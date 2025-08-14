### INÍCIO DO CÓDIGO MELHORADO
# app.py
import streamlit as st
import json
import os
from datetime import datetime, date, timedelta
import pandas as pd
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Gestor de Obras Pro",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CAMINHOS DOS ARQUIVOS ---
TASKS_FILE = "datatasks.json"
ACTIVITIES_FILE = "data_activities.json"
CONFIG_FILE = "dataconfig.json"
PEOPLE_FILE = "data_people.json"
BACKUP_DIR = "backup_tasks"  # Define o nome do diretório de backup

# --- FUNÇÕES AUXILIARES DE MANIPULAÇÃO DE DADOS ---
def load_json(file_path, default):
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return default
    return default

def save_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def save_backup():
    """Salva um backup das tarefas no diretório de backups."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    tasks_to_backup = st.session_state.get('tasks', [])
    if tasks_to_backup:
        backup_file_path = os.path.join(BACKUP_DIR, f"backup_tasks_{timestamp}.json")
        save_json(backup_file_path, tasks_to_backup)

# --- INICIALIZAÇÃO E CARREGAMENTO DE DADOS ---
if 'initialized' not in st.session_state:
    st.session_state.config = load_json(CONFIG_FILE, {"sectors": [], "teams": []})
    st.session_state.people = load_json(PEOPLE_FILE, {"employees": []})
    st.session_state.tasks = load_json(TASKS_FILE, [])
    st.session_state.activities = load_json(ACTIVITIES_FILE, [])

    for task in st.session_state.tasks:
        if 'status' not in task:
            if task.get('progress', 0) == 100:
                task['status'] = 'Concluída'
            elif task.get('progress', 0) > 0:
                task['status'] = 'Em Andamento'
            else:
                task['status'] = 'Planejada'
    st.session_state.initialized = True

# --- FUNÇÕES DE LÓGICA DE NEGÓCIO ---
def save_all_configs():
    """Salva as configurações de setores e equipes."""
    save_json(CONFIG_FILE, st.session_state.config)

def save_tasks_state():
    """Salva o estado atual das tarefas e faz um backup."""
    save_json(TASKS_FILE, st.session_state.tasks)
    save_backup()

def add_activity(icon_type, title, desc):
    """Adiciona uma nova atividade ao log."""
    activity_map = {"new": "➕", "update": "🔄", "delete": "🗑️", "user": "👤", "config": "⚙️"}
    icon = activity_map.get(icon_type, "ℹ️")
    new_activity = {
        "type": icon, "title": title, "desc": desc, "time": datetime.now().strftime("%d/%m %H:%M")
    }
    st.session_state.activities.insert(0, new_activity)
    save_json(ACTIVITIES_FILE, st.session_state.activities)

# =================================================================================
# --- SIDEBAR (BARRA LATERAL) ---
# =================================================================================
with st.sidebar:
    st.title("🏗️ Gestor de Obras Pro")
    st.markdown("---")
    st.header("Feed de Atividades Recentes")
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
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📋 Gestão de Tarefas", "👷 Gestão de Pessoal", "⚙️ Gestão de Configurações"])

# =================================================================================
# --- ABA 1: DASHBOARD (COM GRÁFICOS MELHORADOS) ---
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
        completed_tasks = len(df_tasks[df_tasks['progress'] == 100])
        pending_tasks = total_tasks - completed_tasks
        overall_progress = df_tasks['progress'].mean() if not df_tasks.empty else 0
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Progresso Geral", f"{overall_progress:.1%}")
        col2.metric("Total de Tarefas", total_tasks)
        col3.metric("Tarefas Concluídas", completed_tasks)
        col4.metric("Tarefas Pendentes", pending_tasks)
        st.markdown("<hr>", unsafe_allow_html=True)

        # --- SEÇÃO DE RELATÓRIOS GRÁFICOS MELHORADA ---
        st.subheader("Relatórios de Desempenho")
        
        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            # Gráfico 1: Distribuição de Tarefas por Status (Rosca)
            st.markdown("##### **Distribuição por Status**")
            status_counts = df_tasks['status'].value_counts().reset_index()
            status_counts.columns = ['status', 'count']
            fig_status = px.pie(
                status_counts, 
                names='status', 
                values='count',
                hole=.4, 
                color='status',
                color_discrete_map={'Concluída':'#2ca02c', 'Em Andamento':'#ff7f0e', 'Planejada':'#1f77b4'}
            )
            fig_status.update_traces(textinfo='percent+label+value', textfont_size=14, pull=[0.05, 0, 0])
            fig_status.update_layout(showlegend=False, margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig_status, use_container_width=True)
            
            # Gráfico 3: Carga de Trabalho por Equipe (Barras Empilhadas)
            st.markdown("##### **Carga de Trabalho por Equipe e Status**")
            tasks_by_team_status = df_tasks.groupby(['team', 'status']).size().reset_index(name='count')
            fig_teams = px.bar(
                tasks_by_team_status, 
                x='team', 
                y='count', 
                color='status',
                title="Nº de Tarefas por Equipe",
                labels={'team': 'Equipe', 'count': 'Nº de Tarefas'},
                color_discrete_map={'Concluída':'#2ca02c', 'Em Andamento':'#ff7f0e', 'Planejada':'#1f77b4'},
                text_auto=True
            )
            fig_teams.update_layout(xaxis={'categoryorder':'total descending'})
            st.plotly_chart(fig_teams, use_container_width=True)

        with col_chart2:
            # Gráfico 2: Progresso Médio por Setor (Barras Horizontais)
            st.markdown("##### **Progresso Médio por Setor**")
            progress_by_sector = df_tasks.groupby('sector')['progress'].mean().sort_values(ascending=True).reset_index()
            fig_sector = px.bar(
                progress_by_sector, 
                x='progress', 
                y='sector', 
                orientation='h',
                labels={'sector': 'Setor', 'progress': 'Progresso Médio (%)'}, 
                text='progress'
            )
            fig_sector.update_traces(texttemplate='%{text:.2s}%', textposition='auto')
            fig_sector.update_layout(yaxis_title=None, xaxis_title=None, margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig_sector, use_container_width=True)

            # Gráfico 4 (NOVO): Análise de Prazos
            st.markdown("##### **Análise de Prazos das Tarefas**")
            today = pd.to_datetime(date.today())
            
            def get_due_category(due_date):
                if pd.isna(due_date):
                    return "Sem Prazo"
                if due_date < today:
                    return "Vencida"
                elif due_date <= today + timedelta(days=7):
                    return "Vence em 7 dias"
                else:
                    return "Em Dia"

            df_tasks['due_category'] = df_tasks['due_date'].apply(get_due_category)
            due_counts = df_tasks['due_category'].value_counts().reset_index()
            due_counts.columns = ['category', 'count']
            
            category_order = ["Vencida", "Vence em 7 dias", "Em Dia", "Sem Prazo"]
            due_counts['category'] = pd.Categorical(due_counts['category'], categories=category_order, ordered=True)
            due_counts = due_counts.sort_values('category')

            fig_due_date = px.bar(
                due_counts, x='category', y='count',
                labels={'category': 'Status do Prazo', 'count': 'Nº de Tarefas'},
                color='category',
                color_discrete_map={
                    'Vencida': '#d62728', 
                    'Vence em 7 dias': '#ff7f0e', 
                    'Em Dia': '#2ca02c',
                    'Sem Prazo': '#7f7f7f'
                },
                text_auto=True
            )
            fig_due_date.update_layout(xaxis_title=None, showlegend=False)
            st.plotly_chart(fig_due_date, use_container_width=True)


        st.markdown("<hr>", unsafe_allow_html=True)
        # --- Gráfico de Gantt ---
        st.subheader("Cronograma da Obra (Gráfico de Gantt)")
        if not st.session_state.tasks:
            st.info("Nenhuma tarefa para exibir no cronograma.")
        else:
            # Ordena as tarefas pela data de início para um Gantt mais lógico
            sorted_tasks = sorted(st.session_state.tasks, key=lambda x: x.get('created_at', '9999-12-31'))
            gantt_data = [
                dict(
                    Task=t.get("name", "Tarefa Sem Nome"), 
                    Start=t.get("created_at"), 
                    Finish=t.get("due_date"), 
                    Resource=t.get("team", "Sem Equipe")
                ) 
                for t in sorted_tasks
            ]
            df_gantt = pd.DataFrame(gantt_data)
            
            # Verifica se as colunas de data não estão vazias
            if not df_gantt['Start'].isnull().all() and not df_gantt['Finish'].isnull().all():
                fig_gantt = px.timeline(
                    df_gantt, 
                    x_start="Start", 
                    x_end="Finish", 
                    y="Task", 
                    color="Resource", 
                    title="Linha do Tempo das Tarefas por Equipe"
                )
                fig_gantt.update_yaxes(autorange="reversed") # Tarefas de cima para baixo em ordem
                st.plotly_chart(fig_gantt, use_container_width=True)
            else:
                st.warning("Não foi possível gerar o cronograma. Verifique as datas de início e vencimento das tarefas.")

# --- ABA 2: GESTÃO DE TAREFAS ---
with tab2:
    st.subheader("Adicionar e Editar Tarefas")
    with st.form("task_form", clear_on_submit=True):
        task_name = st.text_input("Nome da Tarefa")
        col1, col2 = st.columns(2)
        
        available_teams = [t['name'] for t in st.session_state.config.get("teams", [])]
        if not available_teams:
            col1.warning("Cadastre uma equipe primeiro!")
            task_team = None
        else:
            task_team = col1.selectbox("Equipe Responsável", available_teams, key="add_task_team")

        available_sectors = [s['name'] for s in st.session_state.config.get("sectors", [])]
        task_sector = col2.selectbox("Setor da Obra", available_sectors, key="add_task_sector")
        
        task_created_at = col1.date_input("Data de Início", date.today())
        task_due_date = col2.date_input("Data de Vencimento", date.today() + timedelta(days=7))
        
        if st.form_submit_button("➕ Adicionar Tarefa"):
            if task_name and task_team and task_sector:
                new_task = {"name": task_name, "team": task_team, "sector": task_sector, "progress": 0, "created_at": task_created_at.strftime("%Y-%m-%d"), "due_date": task_due_date.strftime("%Y-%m-%d"), "status": "Planejada"}
                st.session_state.tasks.append(new_task)
                save_tasks_state()
                add_activity("new", "Nova Tarefa Criada", f"'{task_name}' atribuída à {task_team}.")
                st.success(f"Tarefa '{task_name}' adicionada!")
                st.rerun()
            else:
                st.error("Nome da tarefa, equipe e setor são obrigatórios.")


    st.markdown("---")
    st.subheader("Lista de Tarefas Atuais")
    if not st.session_state.tasks:
        st.info("Nenhuma tarefa cadastrada.")
    else:
        for index, task in enumerate(st.session_state.tasks):
            with st.expander(f"**{task.get('name')}** (`Equipe: {task.get('team')}` | `Setor: {task.get('sector')}` | `Status: {task.get('status')}` | `Progresso: {task.get('progress', 0)}%`)"):
                with st.form(f"form_edit_{index}"):
                    
                    original_name = task.get('name')
                    
                    c1, c2 = st.columns(2)
                    new_name = c1.text_input("Nome da Tarefa", value=original_name, key=f"name_edit_{index}")
                    
                    all_sectors = [s['name'] for s in st.session_state.config.get("sectors", [])]
                    current_sector_index = all_sectors.index(task.get('sector')) if task.get('sector') in all_sectors else 0
                    new_sector = c2.selectbox("Setor", options=all_sectors, index=current_sector_index, key=f"sector_edit_{index}")

                    c3, c4 = st.columns(2)
                    all_teams = [t['name'] for t in st.session_state.config.get("teams", [])]
                    if not all_teams:
                        c3.warning("Nenhuma equipe disponível para seleção.")
                        new_team = task.get('team')
                    else:
                        current_team_index = all_teams.index(task.get('team')) if task.get('team') in all_teams else 0
                        new_team = c3.selectbox("Nova Equipe", all_teams, index=current_team_index, key=f"team_edit_{index}")
                    
                    due_date_val = datetime.strptime(task.get('due_date'), "%Y-%m-%d").date() if isinstance(task.get('due_date'), str) else date.today()
                    new_due_date = c4.date_input("Novo Vencimento", value=due_date_val, key=f"due_edit_{index}")
                    
                    new_progress = st.slider("Progresso (%)", 0, 100, task.get('progress', 0), key=f"prog_edit_{index}")
                    
                    c1_btn, c2_btn = st.columns([1, 0.2])
                    if c1_btn.form_submit_button("💾 Salvar Alterações"):
                        task['name'] = new_name
                        task['sector'] = new_sector
                        task['team'] = new_team
                        task['due_date'] = new_due_date.strftime("%Y-%m-%d")
                        task['progress'] = new_progress
                        task['status'] = 'Concluída' if new_progress == 100 else ('Em Andamento' if new_progress > 0 else 'Planejada')
                        
                        save_tasks_state()
                        add_activity("update", "Tarefa Atualizada", f"A tarefa '{original_name}' foi atualizada.")
                        st.success(f"Tarefa '{new_name}' atualizada!")
                        st.rerun()
                        
                    if c2_btn.form_submit_button("❌ Excluir"):
                        deleted_task_name = st.session_state.tasks.pop(index).get('name')
                        save_tasks_state()
                        add_activity("delete", "Tarefa Excluída", f"A tarefa '{deleted_task_name}' foi removida.")
                        st.warning(f"Tarefa '{deleted_task_name}' excluída.")
                        st.rerun()

# --- ABA 3: GESTÃO DE PESSOAL ---
with tab3:
    st.subheader("Cadastrar Novo Funcionário")
    with st.form("people_form", clear_on_submit=True):
        emp_name = st.text_input("Nome do Funcionário")
        
        available_teams_personnel = [t['name'] for t in st.session_state.config.get("teams", [])]
        if not available_teams_personnel:
            st.warning("Cadastre uma equipe primeiro para poder adicionar funcionários.")
            emp_team = None
        else:
            emp_team = st.selectbox("Equipe", available_teams_personnel)

        emp_role = st.text_input("Função/Cargo")

        if st.form_submit_button("➕ Adicionar Funcionário"):
            if emp_name and emp_role and emp_team:
                new_employee = {"name": emp_name, "team": emp_team, "role": emp_role}
                st.session_state.people.get('employees', []).append(new_employee)
                save_json(PEOPLE_FILE, st.session_state.people)
                add_activity("user", "Novo Colaborador", f"{emp_name} adicionado à equipe {emp_team}.")
                st.success(f"Funcionário {emp_name} cadastrado!")
                st.rerun()
            elif not emp_team:
                st.error("Não é possível adicionar funcionário. Nenhuma equipe está disponível.")
            else:
                st.error("Nome e Cargo são obrigatórios.")


    st.markdown("---")
    st.subheader("Funcionários Cadastrados")
    if not st.session_state.people.get('employees', []):
        st.info("Nenhum funcionário na base de dados.")
    else:
        for i, employee in enumerate(st.session_state.people['employees']):
            st.markdown("---")
            col1, col2 = st.columns([4, 1])
            with col1:
                st.info(f"**Nome:** {employee['name']} | **Equipe:** {employee['team']} | **Cargo:** {employee['role']}")
            with col2:
                if st.button("🗑️ Excluir", key=f"delete_emp_{i}"):
                    deleted_employee = st.session_state.people['employees'].pop(i)
                    save_json(PEOPLE_FILE, st.session_state.people)
                    add_activity("delete", "Funcionário Removido", f"O funcionário '{deleted_employee['name']}' foi removido.")
                    st.toast(f"Funcionário '{deleted_employee['name']}' removido!", icon="🗑️")
                    st.rerun()

            with st.expander("✏️ Editar Funcionário"):
                with st.form(key=f"edit_employee_{i}"):
                    edited_name = st.text_input("Nome", value=employee['name'], key=f"edit_emp_name_{i}")
                    
                    all_teams_edit = [t['name'] for t in st.session_state.config.get("teams", [])]
                    if not all_teams_edit:
                        st.warning("Nenhuma equipe disponível.")
                        edited_team = employee['team']
                    else:
                        current_team_index_edit = all_teams_edit.index(employee['team']) if employee['team'] in all_teams_edit else 0
                        edited_team = st.selectbox("Equipe", options=all_teams_edit, index=current_team_index_edit, key=f"edit_emp_team_{i}")
                    
                    edited_role = st.text_input("Cargo", value=employee['role'], key=f"edit_emp_role_{i}")

                    if st.form_submit_button("💾 Salvar Alterações"):
                        st.session_state.people['employees'][i]['name'] = edited_name
                        st.session_state.people['employees'][i]['team'] = edited_team
                        st.session_state.people['employees'][i]['role'] = edited_role

                        save_json(PEOPLE_FILE, st.session_state.people)
                        add_activity("update", "Dados Atualizados", f"Os dados de '{edited_name}' foram atualizados.")
                        st.success(f"Dados de '{edited_name}' atualizados com sucesso!")
                        st.rerun()

# --- ABA 4: GESTÃO DE CONFIGURAÇÕES ---
with tab4:
    st.subheader("Gerenciar Setores e Equipes do Projeto")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Setores da Obra")
        with st.form("form_add_sector", clear_on_submit=True):
            new_sector_name = st.text_input("Nome do Novo Setor")
            new_sector_desc = st.text_input("Descrição do Setor")
            if st.form_submit_button("➕ Adicionar Setor"):
                if new_sector_name and not any(s['name'] == new_sector_name for s in st.session_state.config["sectors"]):
                    st.session_state.config["sectors"].append({"name": new_sector_name, "desc": new_sector_desc})
                    save_all_configs()
                    add_activity("config", "Setor Adicionado", f"O setor '{new_sector_name}' foi criado.")
                    st.success(f"Setor '{new_sector_name}' adicionado.")
                    st.rerun()
        st.markdown("---")
        for i, sector in enumerate(st.session_state.config["sectors"]):
            sub_col1, sub_col2 = st.columns([4, 1])
            sub_col1.info(f"**{sector['name']}**: {sector['desc']}")
            
            is_in_use = any(task.get('sector') == sector['name'] for task in st.session_state.tasks)
            if is_in_use:
                sub_col2.warning("Em uso")
            elif sub_col2.button("❌", key=f"del_sector_{i}"):
                deleted_sector = st.session_state.config["sectors"].pop(i)
                save_all_configs()
                add_activity("delete", "Setor Removido", f"O setor '{deleted_sector['name']}' foi removido.")
                st.warning(f"Setor '{deleted_sector['name']}' removido.")
                st.rerun()

            with st.expander("✏️ Editar Setor"):
                with st.form(key=f"edit_sector_{i}"):
                    old_sector_name = sector['name']
                    edited_sector_name = st.text_input("Novo Nome do Setor", value=old_sector_name, key=f"s_name_{i}")
                    edited_sector_desc = st.text_input("Nova Descrição", value=sector.get('desc', ''), key=f"s_desc_{i}")
                    
                    if st.form_submit_button("💾 Salvar"):
                        if edited_sector_name and edited_sector_name != old_sector_name:
                            for task in st.session_state.tasks:
                                if task.get('sector') == old_sector_name:
                                    task['sector'] = edited_sector_name
                            save_tasks_state()
                        
                        st.session_state.config["sectors"][i]['name'] = edited_sector_name
                        st.session_state.config["sectors"][i]['desc'] = edited_sector_desc
                        save_all_configs()
                        add_activity("update", "Setor Atualizado", f"Setor '{old_sector_name}' foi atualizado para '{edited_sector_name}'.")
                        st.success("Setor atualizado com sucesso!")
                        st.rerun()
            
    with col2:
        st.markdown("#### Equipes de Trabalho")
        with st.form("form_add_team", clear_on_submit=True):
            new_team_name = st.text_input("Nome da Nova Equipe")
            if st.form_submit_button("➕ Adicionar Equipe"):
                if new_team_name and not any(t['name'] == new_team_name for t in st.session_state.config["teams"]):
                    st.session_state.config["teams"].append({"name": new_team_name})
                    save_all_configs()
                    add_activity("config", "Equipe Adicionada", f"A equipe '{new_team_name}' foi criada.")
                    st.success(f"Equipe '{new_team_name}' adicionada.")
                    st.rerun()
        st.markdown("---")
        for i, team in enumerate(st.session_state.config["teams"]):
            sub_col1, sub_col2 = st.columns([4, 1])
            sub_col1.success(f"**{team['name']}**")
            
            is_in_use = any(task.get('team') == team['name'] for task in st.session_state.tasks) or \
                        any(emp.get('team') == team['name'] for emp in st.session_state.people.get('employees', []))
            if is_in_use:
                sub_col2.warning("Em uso")
            elif sub_col2.button("❌", key=f"del_team_{i}"):
                deleted_team = st.session_state.config["teams"].pop(i)
                save_all_configs()
                add_activity("delete", "Equipe Removida", f"A equipe '{deleted_team['name']}' foi removida.")
                st.warning(f"Equipe '{deleted_team['name']}' removida.")
                st.rerun()

            with st.expander("✏️ Editar Equipe"):
                with st.form(key=f"edit_team_{i}"):
                    old_team_name = team['name']
                    edited_team_name = st.text_input("Novo Nome da Equipe", value=old_team_name, key=f"t_name_{i}")
                    
                    if st.form_submit_button("💾 Salvar"):
                        if edited_team_name and edited_team_name != old_team_name:
                            for task in st.session_state.tasks:
                                if task.get('team') == old_team_name:
                                    task['team'] = edited_team_name
                            save_tasks_state()
                            
                            for emp in st.session_state.people.get('employees', []):
                                if emp.get('team') == old_team_name:
                                    emp['team'] = edited_team_name
                            save_json(PEOPLE_FILE, st.session_state.people)
                            
                            st.session_state.config["teams"][i]['name'] = edited_team_name
                            save_all_configs()
                            add_activity("update", "Equipe Atualizada", f"Equipe '{old_team_name}' foi atualizada para '{edited_team_name}'.")
                            st.success("Equipe atualizada com sucesso e todas as referências foram migradas!")
                            st.rerun()
