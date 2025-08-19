# PLANEJAMENTO_DE_OBRA.py (Versão Completa com Controle de Acesso)
import streamlit as st
import json
import os
from datetime import datetime, date, timedelta
import pandas as pd
import plotly.express as px
import uuid

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Gestor de Obras Pro+",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CAMINHOS E CONSTANTES ---
TASKS_FILE = "datatasks.json"
ACTIVITIES_FILE = "data_activities.json"
CONFIG_FILE = "dataconfig.json"
PEOPLE_FILE = "data_people.json"
BACKUP_DIR = "backup_tasks"

# --- CLASSES PARA GERENCIAMENTO DE DADOS ---
class DataManager:
    """Classe centralizada para carregar e salvar dados em arquivos JSON."""
    @staticmethod
    def load(file_path, default=None):
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return default if default is not None else {}
        return default if default is not None else {}

    @staticmethod
    def save(file_path, data):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def backup_tasks():
        os.makedirs(BACKUP_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        tasks = st.session_state.get('tasks', [])
        if tasks:
            backup_file_path = os.path.join(BACKUP_DIR, f"backup_tasks_{timestamp}.json")
            DataManager.save(backup_file_path, tasks)
            st.toast("Backup das tarefas criado com sucesso!", icon="💾")


# --- FUNÇÃO DE AUTENTICAÇÃO ---
def check_authentication():
    """Exibe um formulário de login e retorna o status de autenticação."""
    if 'user_role' not in st.session_state:
        st.session_state['user_role'] = None

    if st.session_state['user_role'] is None:
        st.title("🏗️ Gestor de Obras Pro+")
        st.header("Controle de Acesso")

        placeholder = st.empty()
        with placeholder.form("login_form"):
            st.markdown("Para editar os dados, por favor, insira a chave de acesso.")
            access_key = st.text_input("Chave de Acesso", type="password")

            col1, col2 = st.columns([1, 1.3])

            if col1.form_submit_button("🔑 Entrar como Admin", use_container_width=True):
                if access_key == st.secrets.get("ACCESS_KEY"):
                    st.session_state['user_role'] = 'admin'
                    placeholder.empty()
                    st.rerun()
                else:
                    st.error("Chave de acesso inválida.")

            if col2.form_submit_button("👁️ Continuar em modo de visualização", use_container_width=True):
                st.session_state['user_role'] = 'viewer'
                placeholder.empty()
                st.rerun()
        return False # Bloqueia a execução do resto do app

    return True # Permite a execução do resto do app


# --- FUNÇÕES DE LÓGICA DE NEGÓCIO E UI ---
def get_task_status(task):
    """Retorna o status de uma tarefa com base no seu progresso."""
    progress = task.get('progress', 0)
    if progress == 100:
        return 'Concluída'
    elif progress > 0:
        return 'Em Andamento'
    else:
        return 'Planejada'

def add_activity(icon_type, title, desc):
    """Adiciona uma nova atividade ao log."""
    activity_map = {"new": "➕", "update": "🔄", "delete": "🗑️", "user": "👤", "config": "⚙️", "complete": "✅"}
    icon = activity_map.get(icon_type, "ℹ️")
    new_activity = {
        "type": icon, "title": title, "desc": desc, "time": datetime.now().strftime("%d/%m %H:%M")
    }
    st.session_state.activities.insert(0, new_activity)
    DataManager.save(ACTIVITIES_FILE, st.session_state.activities)

def save_tasks_state():
    """Salva o estado das tarefas e cria um backup."""
    DataManager.save(TASKS_FILE, st.session_state.tasks)
    DataManager.backup_tasks()

def get_team_members_info(team_name):
    """Retorna uma string formatada com nomes e funções dos membros de uma equipe."""
    employees = st.session_state.people.get("employees", [])
    team_members = [e for e in employees if e.get("team") == team_name]
    if team_members:
        return ", ".join([f"{m['name']} ({m['role']})" for m in team_members])
    return "Nenhum colaborador"

def initialize_state():
    """Carrega todos os dados para o estado da sessão na inicialização."""
    if 'initialized' not in st.session_state:
        st.session_state.config = DataManager.load(CONFIG_FILE, {"sectors": [], "teams": []})
        st.session_state.people = DataManager.load(PEOPLE_FILE, {"employees": []})
        st.session_state.tasks = DataManager.load(TASKS_FILE, [])
        st.session_state.activities = DataManager.load(ACTIVITIES_FILE, [])

        # Normaliza nomes de equipes e setores para remover espaços extras
        for team in st.session_state.config.get("teams", []):
            team['name'] = team['name'].strip()
        for sector in st.session_state.config.get("sectors", []):
            sector['name'] = sector['name'].strip()

        # Garante que cada tarefa tenha um ID único e status atualizado
        for task in st.session_state.tasks:
            if 'id' not in task:
                task['id'] = str(uuid.uuid4())
            task['status'] = get_task_status(task)

        st.session_state.initialized = True


# --- INICIALIZAÇÃO DA APLICAÇÃO ---
if not check_authentication():
    st.stop()

initialize_state()
is_admin = st.session_state.get('user_role') == 'admin'


# =================================================================================
# --- SIDEBAR (BARRA LATERAL) ---
# =================================================================================
with st.sidebar:
    st.title("🏗️ Gestor de Obras Pro+")
    if is_admin:
        st.success("Modo de Edição (Admin)")
    else:
        st.warning("Modo de Visualização")

    st.markdown("---")
    st.header("Feed de Atividades")
    for activity in st.session_state.activities[:5]:
        st.info(f"**{activity['type']} {activity['title']}**\n\n_{activity['desc']}_\n\n`{activity['time']}`")
    st.markdown("---")
    with st.expander("👥 Equipes e Funcionários", expanded=False):
        employees = st.session_state.people.get('employees', [])
        if not employees:
            st.warning("Nenhum funcionário cadastrado.")
        else:
            team_names = [t['name'] for t in st.session_state.config.get("teams", [])]
            selected_team = st.selectbox("Filtrar por Equipe", ["Todas"] + team_names, key="sb_team_filter")

            df_emp = pd.DataFrame(employees)
            if selected_team != "Todas":
                df_emp = df_emp[df_emp['team'] == selected_team]

            st.dataframe(df_emp, use_container_width=True, hide_index=True)


# =================================================================================
# --- PÁGINA PRINCIPAL ---
# =================================================================================
st.header("Painel de Acompanhamento de Obra")
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "📋 Gestão de Tarefas", "👷 Gestão de Pessoal", "⚙️ Gestão de Configurações", "📈 Relatórios Detalhados"])

# =================================================================================
# --- ABA 1: DASHBOARD ---
# =================================================================================
with tab1:
    st.subheader("Visão Geral do Projeto")
    if not st.session_state.tasks:
        st.warning("Nenhuma tarefa cadastrada. Adicione tarefas para visualizar os relatórios.")
    else:
        df_tasks = pd.DataFrame(st.session_state.tasks)
        df_tasks['due_date'] = pd.to_datetime(df_tasks['due_date'], errors='coerce')

        # --- MÉTRICAS PRINCIPAIS ---
        total_tasks = len(df_tasks)
        completed_tasks = len(df_tasks[df_tasks['status'] == 'Concluída'])
        pending_tasks = total_tasks - completed_tasks
        overall_progress = df_tasks['progress'].mean() if not df_tasks.empty else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Progresso Geral", f"{overall_progress:.1f}%", help="Média de progresso de todas as tarefas.")
        col2.metric("Total de Tarefas", total_tasks)
        col3.metric("Tarefas Concluídas", completed_tasks)
        col4.metric("Tarefas Pendentes", pending_tasks)
        st.markdown("<hr>", unsafe_allow_html=True)

        # --- GRÁFICOS DE DESEMPENHO ---
        st.subheader("Relatórios de Desempenho")
        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            st.markdown("##### **Distribuição por Status**")
            status_counts = df_tasks['status'].value_counts().reset_index()
            status_counts.columns = ['status', 'count']
            fig_status = px.pie(status_counts, names='status', values='count', hole=.4,
                                color='status', color_discrete_map={'Concluída':'#2ca02c', 'Em Andamento':'#ff7f0e', 'Planejada':'#1f77b4'})
            fig_status.update_traces(textinfo='percent+label+value', textfont_size=14, pull=[0.05, 0, 0])
            fig_status.update_layout(showlegend=False, margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig_status, use_container_width=True)

        with col_chart2:
            st.markdown("##### **Progresso Médio por Setor**")
            progress_by_sector = df_tasks.groupby('sector')['progress'].mean().sort_values(ascending=True).reset_index()
            fig_sector = px.bar(progress_by_sector, x='progress', y='sector', orientation='h', text='progress')
            fig_sector.update_traces(texttemplate='%{text:.2s}%', textposition='outside')
            fig_sector.update_layout(yaxis_title=None, xaxis_title="Progresso Médio", margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig_sector, use_container_width=True)

        col_chart3, col_chart4 = st.columns(2)
        with col_chart3:
            st.markdown("##### **Carga de Trabalho por Equipe**")
            tasks_by_team_status = df_tasks.groupby(['team', 'status']).size().reset_index(name='count')
            fig_teams = px.bar(tasks_by_team_status, x='team', y='count', color='status',
                               labels={'team': 'Equipe', 'count': 'Nº de Tarefas'},
                               color_discrete_map={'Concluída':'#2ca02c', 'Em Andamento':'#ff7f0e', 'Planejada':'#1f77b4'},
                               text_auto=True)
            fig_teams.update_layout(xaxis={'categoryorder':'total descending'}, yaxis_title="Nº de Tarefas")
            st.plotly_chart(fig_teams, use_container_width=True)

        with col_chart4:
            st.markdown("##### **Análise de Prazos das Tarefas**")
            today = pd.to_datetime(date.today())
            df_tasks_pending = df_tasks[df_tasks['status'] != 'Concluída'].copy()

            def get_due_category(due_date):
                if pd.isna(due_date): return "Sem Prazo"
                delta = (due_date - today).days
                if delta < 0: return "Atrasada"
                if delta <= 7: return "Vence em 7 dias"
                return "Em Dia"

            df_tasks_pending['due_category'] = df_tasks_pending['due_date'].apply(get_due_category)
            due_counts = df_tasks_pending['due_category'].value_counts().reset_index()
            due_counts.columns = ['category', 'count']

            category_order = ["Atrasada", "Vence em 7 dias", "Em Dia", "Sem Prazo"]
            fig_due_date = px.bar(due_counts, x='category', y='count', color='category', text_auto=True,
                                  labels={'category': 'Status do Prazo', 'count': 'Nº de Tarefas'},
                                  color_discrete_map={'Atrasada': '#d62728', 'Vence em 7 dias': '#ff7f0e', 'Em Dia': '#2ca02c', 'Sem Prazo': '#7f7f7f'},
                                  category_orders={"category": category_order})
            fig_due_date.update_layout(xaxis_title=None, showlegend=False)
            st.plotly_chart(fig_due_date, use_container_width=True)

        st.markdown("<hr>", unsafe_allow_html=True)
        st.subheader("Cronograma da Obra (Gráfico de Gantt)")
        if not st.session_state.tasks:
            st.info("Nenhuma tarefa para exibir no cronograma.")
        else:
            gantt_data = [dict(Task=t.get("name"), Start=t.get("created_at"), Finish=t.get("due_date"), Resource=t.get("team")) for t in st.session_state.tasks]
            df_gantt = pd.DataFrame(gantt_data)

            if not df_gantt['Start'].isnull().all() and not df_gantt['Finish'].isnull().all():
                fig_gantt = px.timeline(df_gantt, x_start="Start", x_end="Finish", y="Task", color="Resource", title="Linha do Tempo das Tarefas")
                fig_gantt.update_yaxes(autorange="reversed")
                st.plotly_chart(fig_gantt, use_container_width=True)
            else:
                st.warning("Datas de início/fim inválidas para gerar o cronograma.")

# --- ABA 2: GESTÃO DE TAREFAS ---
with tab2:
    with st.expander("Adicionar Nova Tarefa", expanded=True):
        with st.form("task_form", clear_on_submit=True):
            task_name = st.text_input("Nome da Tarefa", placeholder="Ex: Instalação Elétrica do Bloco A", disabled=not is_admin)
            
            col1, col2 = st.columns(2)
            available_teams = [t['name'] for t in st.session_state.config.get("teams", [])]
            task_team = col1.selectbox("Equipe Responsável", available_teams, index=None, placeholder="Selecione a equipe", disabled=not is_admin)
            available_sectors = [s['name'] for s in st.session_state.config.get("sectors", [])]
            task_sector = col2.selectbox("Setor da Obra", available_sectors, index=None, placeholder="Selecione o setor", disabled=not is_admin)
            
            col3, col4 = st.columns(2)
            task_created_at = col3.date_input("Data de Início", date.today(), disabled=not is_admin)
            task_due_date = col4.date_input("Data de Vencimento", date.today() + timedelta(days=7), disabled=not is_admin)

            if st.form_submit_button("➕ Adicionar Tarefa", use_container_width=True, disabled=not is_admin):
                if all([task_name, task_team, task_sector]):
                    if task_created_at > task_due_date:
                        st.error("A data de início não pode ser posterior à data de vencimento.")
                    else:
                        new_task = {
                            "id": str(uuid.uuid4()), "name": task_name, "team": task_team, "sector": task_sector,
                            "progress": 0, "created_at": task_created_at.strftime("%Y-%m-%d"),
                            "due_date": task_due_date.strftime("%Y-%m-%d"), "status": "Planejada"
                        }
                        st.session_state.tasks.append(new_task)
                        save_tasks_state()
                        add_activity("new", "Nova Tarefa Criada", f"'{task_name}' atribuída à {task_team}.")
                        st.success(f"Tarefa '{task_name}' adicionada!")
                        st.rerun()
                else:
                    st.error("Todos os campos são obrigatórios.")

    st.markdown("---")
    st.subheader("Lista de Tarefas")

    # Filtros e Busca
    col_filter1, col_filter2, col_filter3 = st.columns(3)
    filter_team = col_filter1.multiselect("Filtrar por Equipe", available_teams, placeholder="Todas as equipes")
    filter_sector = col_filter2.multiselect("Filtrar por Setor", available_sectors, placeholder="Todos os setores")
    filter_status = col_filter3.multiselect("Filtrar por Status", ["Planejada", "Em Andamento", "Concluída"], placeholder="Todos os status")

    search_query = st.text_input("🔍 Buscar tarefa por nome", placeholder="Digite o nome da tarefa...")

    filtered_tasks = st.session_state.tasks
    if filter_team:
        filtered_tasks = [t for t in filtered_tasks if t.get('team') in filter_team]
    if filter_sector:
        filtered_tasks = [t for t in filtered_tasks if t.get('sector') in filter_sector]
    if filter_status:
        filtered_tasks = [t for t in filtered_tasks if t.get('status') in filter_status]
    if search_query:
        filtered_tasks = [t for t in filtered_tasks if search_query.lower() in t.get('name', '').lower()]

    if not filtered_tasks:
        st.info("Nenhuma tarefa encontrada com os filtros atuais.")
    else:
        for index, task in enumerate(filtered_tasks):
            with st.expander(f"**{task.get('name', 'Tarefa sem nome')}** | `{task.get('team', 'Sem equipe')}` | `{task.get('sector', 'Sem setor')}`", expanded=False):
                original_task = task.copy()

                team_name = task.get("team", "")
                employees = st.session_state.people.get("employees", [])
                team_members = [e for e in employees if e.get("team") == team_name]

                if team_members:
                    st.markdown("##### 👥 Colaboradores da Equipe")
                    df_team = pd.DataFrame(team_members)[["name", "role"]]
                    st.dataframe(df_team, use_container_width=True, hide_index=True, key=f"df_team_{task['id']}")
                else:
                    st.info("Nenhum colaborador cadastrado nesta equipe.")

                col1, col2, col3, col4 = st.columns([3, 2, 2, 3])
                
                new_name = col1.text_input("Nome", value=task.get('name', ''), key=f"name_{task['id']}", disabled=not is_admin)
                
                team_name = task.get('team')
                current_team_index = available_teams.index(team_name) if team_name in available_teams else None
                new_team = col2.selectbox("Equipe", available_teams, index=current_team_index, key=f"team_{task['id']}", disabled=not is_admin)
                
                sector_name = task.get('sector')
                current_sector_index = available_sectors.index(sector_name) if sector_name in available_sectors else None
                new_sector = col3.selectbox("Setor", available_sectors, index=current_sector_index, key=f"sector_{task['id']}", disabled=not is_admin)
                
                due_date_val = datetime.strptime(task.get('due_date', str(date.today())), "%Y-%m-%d").date()
                new_due_date = col4.date_input("Vencimento", value=due_date_val, key=f"due_date_{task['id']}", disabled=not is_admin)

                new_progress = st.slider("Progresso (%)", 0, 100, task.get('progress', 0), key=f"progress_{task['id']}", disabled=not is_admin)
                
                if st.button("💾 Salvar", key=f"save_{task['id']}", use_container_width=True, disabled=not is_admin):
                    task_index = next((i for i, t in enumerate(st.session_state.tasks) if t['id'] == task['id']), None)
                    if task_index is not None:
                        st.session_state.tasks[task_index].update({
                            'name': new_name, 'team': new_team, 'sector': new_sector,
                            'due_date': new_due_date.strftime("%Y-%m-%d"), 'progress': new_progress,
                            'status': get_task_status({'progress': new_progress})
                        })
                        save_tasks_state()
                        add_activity("update", "Tarefa Atualizada", f"A tarefa '{original_task.get('name', '')}' foi atualizada.")
                        st.success(f"Tarefa '{new_name}' atualizada!")
                        st.rerun()

                if st.button("🗑️ Excluir", key=f"delete_{task['id']}", use_container_width=True, disabled=not is_admin):
                    st.session_state.confirm_delete = task['id']

                if st.session_state.get('confirm_delete') == task['id']:
                    st.warning(f"**Tem certeza que deseja excluir a tarefa '{task.get('name', '')}'?**")
                    c1, c2 = st.columns(2)
                    if c1.button("Sim, excluir", key=f"confirm_del_{task['id']}", use_container_width=True):
                        task_index = next((i for i, t in enumerate(st.session_state.tasks) if t['id'] == task['id']), None)
                        if task_index is not None:
                            deleted_task_name = st.session_state.tasks.pop(task_index).get('name', 'Sem nome')
                            save_tasks_state()
                            add_activity("delete", "Tarefa Excluída", f"A tarefa '{deleted_task_name}' foi removida.")
                            st.warning(f"Tarefa '{deleted_task_name}' excluída.")
                            del st.session_state['confirm_delete']
                            st.rerun()
                    if c2.button("Cancelar", key=f"cancel_del_{task['id']}", use_container_width=True):
                        del st.session_state['confirm_delete']
                        st.rerun()

# --- ABA 3: GESTÃO DE PESSOAL ---
with tab3:
    with st.expander("Cadastrar Novo Funcionário", expanded=True):
        with st.form("people_form", clear_on_submit=True):
            emp_name = st.text_input("Nome do Funcionário", disabled=not is_admin)
            
            available_teams_personnel = [t['name'] for t in st.session_state.config.get("teams", [])]
            emp_team = st.selectbox("Equipe", available_teams_personnel, index=None, placeholder="Selecione uma equipe", disabled=not is_admin)
            emp_role = st.text_input("Função/Cargo", disabled=not is_admin)

            if st.form_submit_button("➕ Adicionar Funcionário", use_container_width=True, disabled=not is_admin):
                if all([emp_name, emp_role, emp_team]):
                    new_employee = {"id": str(uuid.uuid4()), "name": emp_name, "team": emp_team, "role": emp_role}
                    st.session_state.people.setdefault('employees', []).append(new_employee)
                    DataManager.save(PEOPLE_FILE, st.session_state.people)
                    add_activity("user", "Novo Colaborador", f"{emp_name} adicionado à equipe {emp_team}.")
                    st.success(f"Funcionário {emp_name} cadastrado!")
                    st.rerun()
                else:
                    st.error("Todos os campos são obrigatórios.")

    st.markdown("---")
    st.subheader("Funcionários Cadastrados")
    employees = st.session_state.people.get('employees', [])
    if not employees:
        st.info("Nenhum funcionário cadastrado.")
    else:
        df_people = pd.DataFrame(employees)
        
        # --- CÓDIGO CORRIGIDO ---
        # 1. Define os argumentos base do dataframe
        dataframe_args = {
            "use_container_width": True,
            "hide_index": True,
            "key": "employee_selector"
        }
        
        # 2. Adiciona os argumentos de seleção apenas se for admin
        if is_admin:
            dataframe_args["on_select"] = "rerun"
            dataframe_args["selection_mode"] = "single-row"
            
        # 3. Chama o dataframe desempacotando os argumentos
        st.dataframe(df_people, **dataframe_args)
        # --- FIM DA CORREÇÃO ---
        
        if is_admin:
            selection = st.session_state.get("employee_selector", {}).get("selection", {})
            if selection and selection.get("rows"):
                selected_index = selection["rows"][0]
                if selected_index < len(employees):
                    employee = employees[selected_index]
                    
                    st.markdown("#### Editar/Excluir Funcionário Selecionado")
                    with st.form(key=f"edit_employee_{employee.get('id', selected_index)}"):
                        edited_name = st.text_input("Nome", value=employee['name'])
                        
                        all_teams_edit = [t['name'] for t in st.session_state.config.get("teams", [])]
                        current_team_index = all_teams_edit.index(employee['team']) if employee['team'] in all_teams_edit else 0
                        edited_team = st.selectbox("Equipe", options=all_teams_edit, index=current_team_index)
                        edited_role = st.text_input("Cargo", value=employee['role'])

                        col_btn1, col_btn2 = st.columns(2)
                        if col_btn1.form_submit_button("💾 Salvar Alterações", use_container_width=True):
                            employees[selected_index] = {'id': employee.get('id'), 'name': edited_name, 'team': edited_team, 'role': edited_role}
                            DataManager.save(PEOPLE_FILE, st.session_state.people)
                            add_activity("update", "Dados Atualizados", f"Os dados de '{edited_name}' foram atualizados.")
                            st.success(f"Dados de '{edited_name}' atualizados!")
                            st.rerun()
                        
                        if col_btn2.form_submit_button("🗑️ Excluir Funcionário", type="primary", use_container_width=True):
                            deleted_employee = employees.pop(selected_index)
                            DataManager.save(PEOPLE_FILE, st.session_state.people)
                            add_activity("delete", "Funcionário Removido", f"O funcionário '{deleted_employee['name']}' foi removido.")
                            st.warning(f"Funcionário '{deleted_employee['name']}' removido.")
                            st.rerun()

# --- ABA 4: GESTÃO DE CONFIGURAÇÕES ---
with tab4:
    st.subheader("Gerenciar Setores e Equipes")
    if not is_admin:
        st.warning("Apenas administradores podem gerenciar setores e equipes.", icon="🔒")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Setores da Obra")
        with st.form("form_add_sector", clear_on_submit=True):
            new_sector_name = st.text_input("Nome do Novo Setor", disabled=not is_admin).strip()
            if st.form_submit_button("➕ Adicionar Setor", disabled=not is_admin):
                if new_sector_name and not any(s['name'].lower() == new_sector_name.lower() for s in st.session_state.config["sectors"]):
                    st.session_state.config["sectors"].append({"name": new_sector_name, "desc": ""})
                    DataManager.save(CONFIG_FILE, st.session_state.config)
                    add_activity("config", "Setor Adicionado", f"O setor '{new_sector_name}' foi criado.")
                    st.rerun()
                elif not new_sector_name:
                    st.error("O nome do setor não pode ser vazio.")
                else:
                    st.error("Este setor já existe.")

        for i, sector in enumerate(st.session_state.config["sectors"]):
            is_in_use = any(task.get('sector') == sector['name'] for task in st.session_state.tasks)
            with st.expander(f"{sector['name']} ({'Em uso' if is_in_use else 'Não utilizado'})"):
                with st.form(key=f"edit_sector_{i}"):
                    old_name = sector['name']
                    new_name = st.text_input("Nome do Setor", value=old_name, disabled=not is_admin).strip()
                    
                    col_btn1, col_btn2 = st.columns([3, 1])
                    if col_btn1.form_submit_button("💾 Salvar", disabled=not is_admin):
                        if new_name and not any(s['name'].lower() == new_name.lower() for s in st.session_state.config["sectors"] if s['name'] != old_name):
                            st.session_state.config["sectors"][i]['name'] = new_name
                            DataManager.save(CONFIG_FILE, st.session_state.config)
                            for task in st.session_state.tasks:
                                if task.get('sector') == old_name:
                                    task['sector'] = new_name
                            save_tasks_state()
                            add_activity("update", "Setor Atualizado", f"Setor '{old_name}' atualizado para '{new_name}'.")
                            st.rerun()
                        else:
                            st.error("Nome inválido ou já existente.")
                    
                    if col_btn2.form_submit_button("❌", disabled=not is_admin or is_in_use, help="Excluir setor (só se não estiver em uso)"):
                        st.session_state.config["sectors"].pop(i)
                        DataManager.save(CONFIG_FILE, st.session_state.config)
                        add_activity("delete", "Setor Removido", f"O setor '{old_name}' foi removido.")
                        st.rerun()

    with col2:
        st.markdown("#### Equipes de Trabalho")
        with st.form("form_add_team", clear_on_submit=True):
            new_team_name = st.text_input("Nome da Nova Equipe", disabled=not is_admin).strip()
            if st.form_submit_button("➕ Adicionar Equipe", disabled=not is_admin):
                if new_team_name and not any(t['name'].lower() == new_team_name.lower() for t in st.session_state.config["teams"]):
                    st.session_state.config["teams"].append({"name": new_team_name})
                    DataManager.save(CONFIG_FILE, st.session_state.config)
                    add_activity("config", "Equipe Adicionada", f"A equipe '{new_team_name}' foi criada.")
                    st.rerun()
                elif not new_team_name:
                    st.error("O nome da equipe não pode ser vazio.")
                else:
                    st.error("Esta equipe já existe.")

        for i, team in enumerate(st.session_state.config["teams"]):
            is_in_use = any(task.get('team') == team['name'] for task in st.session_state.tasks) or \
                        any(emp.get('team') == team['name'] for emp in st.session_state.people.get('employees', []))
            
            with st.expander(f"{team['name']} ({'Em uso' if is_in_use else 'Não utilizada'})"):
                with st.form(key=f"edit_team_{i}"):
                    old_name = team['name']
                    new_name = st.text_input("Nome da Equipe", value=old_name, disabled=not is_admin).strip()
                    
                    col_btn1, col_btn2 = st.columns([3, 1])
                    if col_btn1.form_submit_button("💾 Salvar", disabled=not is_admin):
                        if new_name and not any(t['name'].lower() == new_name.lower() for t in st.session_state.config["teams"] if t['name'] != old_name):
                            st.session_state.config["teams"][i]['name'] = new_name
                            DataManager.save(CONFIG_FILE, st.session_state.config)
                            for task in st.session_state.tasks:
                                if task.get('team') == old_name:
                                    task['team'] = new_name
                            save_tasks_state()
                            for emp in st.session_state.people.get('employees', []):
                                if emp.get('team') == old_name:
                                    emp['team'] = new_name
                            DataManager.save(PEOPLE_FILE, st.session_state.people)
                            add_activity("update", "Equipe Atualizada", f"Equipe '{old_name}' atualizado para '{new_name}'.")
                            st.rerun()
                        else:
                            st.error("Nome inválido ou já existente.")
                    
                    if col_btn2.form_submit_button("❌", disabled=not is_admin or is_in_use, help="Excluir equipe (só se não estiver em uso)"):
                        st.session_state.config["teams"].pop(i)
                        DataManager.save(CONFIG_FILE, st.session_state.config)
                        add_activity("delete", "Equipe Removida", f"A equipe '{old_name}' foi removida.")
                        st.rerun()

# =================================================================================
# --- ABA 5: RELATÓRIOS DETALHADOS ---
# =================================================================================
with tab5:
    st.subheader("Relatório Detalhado por Atividade")

    if not st.session_state.tasks:
        st.info("Nenhuma tarefa cadastrada para gerar relatórios.")
    else:
        df_tasks = pd.DataFrame(st.session_state.tasks)
        df_tasks['created_at'] = pd.to_datetime(df_tasks['created_at'])
        df_tasks['due_date'] = pd.to_datetime(df_tasks['due_date'])

        all_teams = ["Todas"] + sorted(df_tasks['team'].unique().tolist())
        selected_team_report = st.selectbox("Filtrar por Equipe:", all_teams, key="report_team_filter")

        all_sectors = ["Todos"] + sorted(df_tasks['sector'].unique().tolist())
        selected_sector_report = st.selectbox("Filtrar por Setor:", all_sectors, key="report_sector_filter")

        all_statuses = ["Todos"] + sorted(df_tasks['status'].unique().tolist())
        selected_status_report = st.selectbox("Filtrar por Status:", all_statuses, key="report_status_filter")

        filtered_report_tasks = df_tasks.copy()
        if selected_team_report != "Todas":
            filtered_report_tasks = filtered_report_tasks[filtered_report_tasks['team'] == selected_team_report]
        if selected_sector_report != "Todos":
            filtered_report_tasks = filtered_report_tasks[filtered_report_tasks['sector'] == selected_sector_report]
        if selected_status_report != "Todos":
            filtered_report_tasks = filtered_report_tasks[filtered_report_tasks['status'] == selected_status_report]

        if filtered_report_tasks.empty:
            st.warning("Nenhuma tarefa encontrada com os filtros selecionados.")
        else:
            st.markdown("---")
            st.markdown("### Visão Geral das Tarefas Filtradas")
            col_metrics_report1, col_metrics_report2, col_metrics_report3 = st.columns(3)
            col_metrics_report1.metric("Total de Tarefas", len(filtered_report_tasks))
            col_metrics_report2.metric("Tarefas Concluídas", len(filtered_report_tasks[filtered_report_tasks['status'] == 'Concluída']))
            col_metrics_report3.metric("Progresso Médio", f"{filtered_report_tasks['progress'].mean():.1f}%")

            st.markdown("---")
            st.markdown("### Detalhes das Tarefas")

            for _, row in filtered_report_tasks.iterrows():
                with st.expander(f"📌 {row['name']} | Equipe: {row['team']} | Setor: {row['sector']}"):
                    st.write(f"**Status:** {row['status']} | **Progresso:** {row['progress']}%")
                    st.write(f"**Início:** {row['created_at'].strftime('%d/%m/%Y')} | **Vencimento:** {row['due_date'].strftime('%d/%m/%Y')}")

                    team_name = row['team']
                    all_employees = st.session_state.people.get("employees", [])
                    team_members_list = [emp for emp in all_employees if emp.get("team") == team_name]

                    if team_members_list:
                        st.markdown("👥 **Colaboradores da Equipe:**")
                        df_colab = pd.DataFrame(team_members_list)[['name', 'role']]
                        st.dataframe(df_colab, use_container_width=True, hide_index=True)
                    else:
                        st.info("Nenhum colaborador cadastrado para esta equipe.")

            st.markdown("---")
            st.markdown("### Gráficos do Relatório")

            st.markdown("##### Progresso Médio por Equipe (Filtrado)")
            progress_by_team_report = filtered_report_tasks.groupby('team')['progress'].mean().reset_index()
            fig_progress_team_report = px.bar(progress_by_team_report, x='team', y='progress',
                                               title='Progresso Médio por Equipe',
                                               labels={'team': 'Equipe', 'progress': 'Progresso Médio (%)'})
            st.plotly_chart(fig_progress_team_report, use_container_width=True)

            st.markdown("##### Distribuição de Status por Setor (Filtrado)")
            status_by_sector_report = filtered_report_tasks.groupby(['sector', 'status']).size().reset_index(name='count')
            fig_status_sector_report = px.bar(status_by_sector_report, x='sector', y='count', color='status',
                                              title='Distribuição de Status por Setor',
                                              labels={'sector': 'Setor', 'count': 'Nº de Tarefas'},
                                              color_discrete_map={'Concluída':'#2ca02c', 'Em Andamento':'#ff7f0e', 'Planejada':'#1f77b4'})
            st.plotly_chart(fig_status_sector_report, use_container_width=True)

            st.markdown("##### Cronograma das Tarefas Filtradas")
            gantt_data_report = [
                dict(Task=t.get("name"), Start=t.get("created_at"), Finish=t.get("due_date"), Resource=t.get("team"))
                for t in filtered_report_tasks.to_dict('records')
            ]
            df_gantt_report = pd.DataFrame(gantt_data_report)

            if not df_gantt_report.empty and not df_gantt_report['Start'].isnull().all() and not df_gantt_report['Finish'].isnull().all():
                fig_gantt_report = px.timeline(df_gantt_report, x_start="Start", x_end="Finish", y="Task", color="Resource",
                                               title="Linha do Tempo das Tarefas Filtradas")
                fig_gantt_report.update_yaxes(autorange="reversed")
                st.plotly_chart(fig_gantt_report, use_container_width=True)
            else:
                st.info("Datas de início/fim inválidas ou insuficientes para gerar o cronograma das tarefas filtradas.")
                
