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
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    tasks_to_backup = st.session_state.get('tasks', [])
    if tasks_to_backup:
        save_json(f"backup_tasks_{timestamp}.json", tasks_to_backup)

# --- INICIALIZAÇÃO E CARREGAMENTO DE DADOS ---
if 'initialized' not in st.session_state:
    st.session_state.config = load_json(CONFIG_FILE, {"sectors": [], "teams": []})
    st.session_state.people = load_json(PEOPLE_FILE, {"employees": []})
    st.session_state.tasks = load_json(TASKS_FILE, [])
    st.session_state.activities = load_json(ACTIVITIES_FILE, [])
    
    # Adiciona o campo 'status' se não existir nas tarefas
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
    activity_map = {
        "new": "➕", "update": "🔄", "delete": "🗑️", "user": "👤", "config": "⚙️"
    }
    icon = activity_map.get(icon_type, "ℹ️")
    
    new_activity = {
        "type": icon,
        "title": title,
        "desc": desc,
        "time": datetime.now().strftime("%d/%m %H:%M")
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

# --- ABA 1: DASHBOARD ---
with tab1:
    st.subheader("Visão Geral do Projeto")
    if not st.session_state.tasks:
        st.warning("Nenhuma tarefa cadastrada. Adicione tarefas para visualizar os relatórios.")
    else:
        df_tasks = pd.DataFrame(st.session_state.tasks)
        total_tasks = len(df_tasks)
        completed_tasks = len(df_tasks[df_tasks['progress'] == 100])
        pending_tasks = total_tasks - completed_tasks
        overall_progress = df_tasks['progress'].mean() / 100 if not df_tasks.empty else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Progresso Geral", f"{overall_progress:.1%}")
        col2.metric("Total de Tarefas", total_tasks)
        col3.metric("Tarefas Concluídas", completed_tasks)
        col4.metric("Tarefas Pendentes", pending_tasks)
        st.markdown("<hr>", unsafe_allow_html=True)

        # --- NOVA SEÇÃO DE RELATÓRIOS GRÁFICOS ---
        st.subheader("Relatórios Gráficos")
        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            # Gráfico 1: Status das Tarefas (Pizza)
            status_counts = df_tasks['status'].value_counts().reset_index()
            status_counts.columns = ['status', 'count']
            fig_status = px.pie(status_counts, names='status', values='count', 
                                title="Distribuição de Tarefas por Status",
                                hole=.3, color_discrete_map={'Concluída':'green', 'Em Andamento':'orange', 'Planejada':'blue'})
            st.plotly_chart(fig_status, use_container_width=True)

            # Gráfico 3: Carga de Trabalho por Equipe (Barras)
            team_counts = df_tasks['team'].value_counts().reset_index()
            team_counts.columns = ['team', 'count']
            fig_teams = px.bar(team_counts, x='team', y='count', 
                               title="Carga de Trabalho por Equipe",
                               labels={'team': 'Equipe', 'count': 'Nº de Tarefas'},
                               color='team')
            st.plotly_chart(fig_teams, use_container_width=True)

        with col_chart2:
            # Gráfico 2: Progresso Médio por Setor (Barras)
            progress_by_sector = df_tasks.groupby('sector')['progress'].mean().reset_index()
            fig_sector = px.bar(progress_by_sector, x='sector', y='progress',
                                title="Progresso Médio por Setor (%)",
                                labels={'sector': 'Setor', 'progress': 'Progresso Médio (%)'},
                                color='sector', text_auto='.2s')
            fig_sector.update_traces(textangle=0, textposition="outside")
            st.plotly_chart(fig_sector, use_container_width=True)
        
        st.markdown("<hr>", unsafe_allow_html=True)
        # --- Gráfico de Gantt ---
        st.subheader("Cronograma da Obra (Gráfico de Gantt)")
        gantt_data = [dict(Task=t.get("name"), Start=t.get("created_at"), Finish=t.get("due_date"), Resource=t.get("team")) for t in st.session_state.tasks]
        df_gantt = pd.DataFrame(gantt_data)
        fig_gantt = px.timeline(df_gantt, x_start="Start", x_end="Finish", y="Task", color="Resource", title="Linha do Tempo das Tarefas por Equipe")
        fig_gantt.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_gantt, use_container_width=True)

# --- ABA 2: GESTÃO DE TAREFAS ---
with tab2:
    st.subheader("Adicionar e Editar Tarefas")
    with st.form("task_form", clear_on_submit=True):
        task_name = st.text_input("Nome da Tarefa")
        col1, col2 = st.columns(2)
        task_team = col1.selectbox("Equipe Responsável", [t['name'] for t in st.session_state.config.get("teams", [])])
        task_sector = col2.selectbox("Setor da Obra", [s['name'] for s in st.session_state.config.get("sectors", [])])
        task_created_at = col1.date_input("Data de Início", date.today())
        task_due_date = col2.date_input("Data de Vencimento", date.today() + timedelta(days=7))
        if st.form_submit_button("➕ Adicionar Tarefa"):
            if task_name:
                new_task = {"name": task_name, "team": task_team, "sector": task_sector, "progress": 0, "created_at": task_created_at.strftime("%Y-%m-%d"), "due_date": task_due_date.strftime("%Y-%m-%d"), "status": "Planejada"}
                st.session_state.tasks.append(new_task)
                save_tasks_state()
                add_activity("new", "Nova Tarefa Criada", f"'{task_name}' atribuída à {task_team}.")
                st.success(f"Tarefa '{task_name}' adicionada!")
                st.rerun()

    st.markdown("---")
    st.subheader("Lista de Tarefas Atuais")
    if not st.session_state.tasks:
        st.info("Nenhuma tarefa cadastrada.")
    else:
        for index, task in enumerate(st.session_state.tasks):
            with st.expander(f"**{task.get('name')}** (`Equipe: {task.get('team')}` | `Status: {task.get('status')}` | `Progresso: {task.get('progress', 0)}%`)"):
                with st.form(f"form_edit_{index}"):
                    new_progress = st.slider("Progresso (%)", 0, 100, task.get('progress', 0), key=f"prog_{index}")
                    c1, c2 = st.columns(2)
                    new_due_date = c1.date_input("Novo Vencimento", value=datetime.strptime(task.get('due_date'), "%Y-%m-%d").date(), key=f"due_{index}")
                    all_teams = [t['name'] for t in st.session_state.config.get("teams", [])]
                    current_team_index = all_teams.index(task.get('team')) if task.get('team') in all_teams else 0
                    new_team = c2.selectbox("Nova Equipe", all_teams, index=current_team_index, key=f"team_{index}")
                    c1_btn, c2_btn = st.columns([1, 0.2])
                    if c1_btn.form_submit_button("💾 Salvar Alterações"):
                        task['progress'] = new_progress
                        task['due_date'] = new_due_date.strftime("%Y-%m-%d")
                        task['team'] = new_team
                        task['status'] = 'Concluída' if new_progress == 100 else ('Em Andamento' if new_progress > 0 else 'Planejada')
                        save_tasks_state()
                        add_activity("update", "Tarefa Atualizada", f"Progresso de '{task['name']}' atualizado.")
                        st.success(f"Tarefa '{task['name']}' atualizada!")
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
        emp_team = st.selectbox("Equipe", [t['name'] for t in st.session_state.config.get("teams", [])])
        emp_role = st.text_input("Função/Cargo")
        if st.form_submit_button("➕ Adicionar Funcionário"):
            if emp_name and emp_role:
                new_employee = {"name": emp_name, "team": emp_team, "role": emp_role}
                st.session_state.people.get('employees', []).append(new_employee)
                save_json(PEOPLE_FILE, st.session_state.people)
                add_activity("user", "Novo Colaborador", f"{emp_name} adicionado à equipe {emp_team}.")
                st.success(f"Funcionário {emp_name} cadastrado!")
                st.rerun()
    st.markdown("---")
    st.subheader("Funcionários Cadastrados")
    if not st.session_state.people.get('employees', []):
        st.info("Nenhum funcionário na base de dados.")
    else:
        st.dataframe(pd.DataFrame(st.session_state.people.get('employees', [])), use_container_width=True, hide_index=True)

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