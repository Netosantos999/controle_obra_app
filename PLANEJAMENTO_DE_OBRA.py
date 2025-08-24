# PLANEJAMENTO_DE_OBRA.py (Versão Otimizada)
import streamlit as st
import json
import os
from datetime import datetime, date, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
        """Carrega dados de um arquivo JSON. Retorna um valor padrão se o arquivo não existir ou estiver corrompido."""
        default_value = default if default is not None else {}
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return default_value
        return default_value

    @staticmethod
    def save(file_path, data):
        """Salva dados em um arquivo JSON."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def backup_tasks():
        """Cria um backup do arquivo de tarefas com timestamp."""
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
        return False

    return True


# --- FUNÇÕES DE LÓGICA DE NEGÓCIO E UI ---

def get_due_category(due_date, today=pd.to_datetime(date.today())):
    """Classifica uma tarefa pendente com base na sua data de vencimento."""
    if pd.isna(due_date):
        return "Sem Prazo"
    delta = (due_date - today).days
    if delta < 0:
        return "Atrasada"
    if delta <= 7:
        return "Vence em 7 dias"
    return "Em Dia"

def generate_report_html(filtered_df, project_goals, filters):
    """Gera um relatório HTML completo e estilizado a partir dos dados filtrados."""
    
    # --- Métricas ---
    total_tasks = len(filtered_df)
    completed_tasks = len(filtered_df[filtered_df['status'] == 'Concluída'])
    progress = filtered_df['progress'].mean() if total_tasks > 0 else 0
    overdue_tasks = len(filtered_df[(filtered_df['due_date'] < pd.to_datetime(datetime.now())) & (filtered_df['status'] != 'Concluída')])
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    # --- Gráficos (convertidos para HTML) ---
    # Gráfico de Status
    status_counts = filtered_df['status'].value_counts().reset_index()
    status_counts.columns = ['status', 'count']
    fig_status = px.pie(status_counts, names='status', values='count', hole=.4,
                        title="Distribuição por Status",
                        color='status', color_discrete_map={'Concluída':'#2ca02c', 'Em Andamento':'#ff7f0e', 'Planejada':'#1f77b4'})
    fig_status.update_layout(legend_title_text='Status', margin=dict(t=40, b=20, l=20, r=20))
    status_chart_html = fig_status.to_html(full_html=False, include_plotlyjs='cdn')

    # Gráfico de Prazos
    today = pd.to_datetime(date.today())
    df_pending = filtered_df[filtered_df['status'] != 'Concluída'].copy()
    due_chart_html = ""
    if not df_pending.empty:
        df_pending['due_category'] = df_pending['due_date'].apply(get_due_category)
        due_counts = df_pending['due_category'].value_counts().reset_index()
        due_counts.columns = ['category', 'count']
        category_order = ["Atrasada", "Vence em 7 dias", "Em Dia", "Sem Prazo"]
        fig_due = px.bar(due_counts, x='category', y='count', color='category', text_auto=True,
                         title="Análise de Prazos (Tarefas Pendentes)",
                         labels={'category': 'Status do Prazo', 'count': 'Nº de Tarefas'},
                         color_discrete_map={'Atrasada': '#d62728', 'Vence em 7 dias': '#ff7f0e', 'Em Dia': '#2ca02c', 'Sem Prazo': '#7f7f7f'},
                         category_orders={"category": category_order})
        fig_due.update_layout(xaxis_title=None, yaxis_title="Nº de Tarefas", showlegend=False)
        due_chart_html = fig_due.to_html(full_html=False, include_plotlyjs='cdn')

    # --- Tabela de Tarefas (convertida para HTML) ---
    df_display = filtered_df[['name', 'team', 'sector', 'status', 'progress', 'created_at', 'due_date']].copy()
    df_display.rename(columns={'name': 'Tarefa', 'team': 'Equipe', 'sector': 'Setor', 'status': 'Status', 'progress': 'Progresso (%)', 'created_at': 'Início', 'due_date': 'Vencimento'}, inplace=True)
    df_display['Início'] = df_display['Início'].dt.strftime('%d/%m/%Y')
    df_display['Vencimento'] = df_display['Vencimento'].dt.strftime('%d/%m/%Y')
    tasks_table_html = df_display.to_html(index=False, border=0, classes='dataframe')

    # --- Template HTML ---
    html_template = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Relatório de Andamento da Obra</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f9f9f9; margin: 0; padding: 0; }}
            .container {{ max-width: 1100px; margin: 20px auto; padding: 20px; background-color: #fff; border: 1px solid #ddd; box-shadow: 0 0 10px rgba(0,0,0,0.05); }}
            header {{ text-align: center; border-bottom: 2px solid #eee; padding-bottom: 20px; margin-bottom: 30px; }}
            header h1 {{ margin: 0; color: #1f77b4; }}
            header p {{ margin: 5px 0 0; color: #777; }}
            .section {{ margin-bottom: 40px; }}
            .section h2 {{ color: #333; border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 20px; }}
            .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; text-align: center; }}
            .metric {{ background-color: #f9f9f9; padding: 20px; border-radius: 8px; border: 1px solid #e0e0e0; }}
            .metric .value {{ font-size: 2.5em; font-weight: bold; color: #1f77b4; }}
            .metric .label {{ font-size: 1em; color: #666; margin-top: 5px; }}
            .dataframe {{ width: 100%; border-collapse: collapse; }}
            .dataframe th, .dataframe td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; }}
            .dataframe th {{ background-color: #f2f2f2; font-weight: bold; }}
            .dataframe tbody tr:hover {{ background-color: #f5f5f5; }}
            .charts-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
            .chart {{ border: 1px solid #ddd; padding: 10px; border-radius: 8px; }}
            .goals {{ background-color: #e7f3ff; border-left: 4px solid #1f77b4; padding: 15px; margin-bottom: 20px; white-space: pre-wrap; }}
            @media print {{
                body {{ background-color: #fff; }}
                .container {{ box-shadow: none; border: none; margin: 0; max-width: 100%; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>Relatório de Andamento da Obra</h1>
                <p><strong>Data de Emissão:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                <p><strong>Filtros:</strong> Equipe: {filters['team']}, Setor: {filters['sector']}, Status: {filters['status']}</p>
            </header>

            <div class="section">
                <h2>1. Resumo Executivo e Metas</h2>
                <div class="goals"><strong>Metas do Projeto:</strong><br>{project_goals if project_goals else "Nenhuma meta definida."}</div>
                <div class="metrics-grid">
                    <div class="metric"><div class="value">{total_tasks}</div><div class="label">Total de Tarefas</div></div>
                    <div class="metric"><div class="value">{progress:.1f}%</div><div class="label">Progresso Médio</div></div>
                    <div class="metric"><div class="value">{completion_rate:.1f}%</div><div class="label">Taxa de Conclusão</div></div>
                    <div class="metric"><div class="value" style="color: #d62728;">{overdue_tasks}</div><div class="label">Tarefas Atrasadas</div></div>
                </div>
            </div>

            <div class="section">
                <h2>2. Análise Gráfica</h2>
                <div class="charts-grid">
                    <div class="chart">{status_chart_html}</div>
                    <div class="chart">{due_chart_html if due_chart_html else "<p>Nenhuma tarefa pendente para análise.</p>"}</div>
                </div>
            </div>

            <div class="section">
                <h2>3. Detalhamento das Atividades</h2>
                {tasks_table_html}
            </div>
        </div>
    </body>
    </html>
    """
    return html_template

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

def initialize_state():
    """Carrega todos os dados para o estado da sessão na inicialização."""
    if 'initialized' not in st.session_state:
        st.session_state.config = DataManager.load(CONFIG_FILE, {"sectors": [], "teams": [], "project_goals": ""})
        st.session_state.people = DataManager.load(PEOPLE_FILE, {"employees": []})
        tasks_data = DataManager.load(TASKS_FILE, [])
        st.session_state.activities = DataManager.load(ACTIVITIES_FILE, [])

        # Pré-processamento e sanitização dos dados
        for team in st.session_state.config.get("teams", []):
            team['name'] = team['name'].strip()
        for sector in st.session_state.config.get("sectors", []):
            sector['name'] = sector['name'].strip()

        for task in tasks_data:
            if 'id' not in task:
                task['id'] = str(uuid.uuid4())
            task['status'] = get_task_status(task)
        
        # Converte os dados de tarefas em um DataFrame do Pandas
        df_tasks = pd.DataFrame(tasks_data)
        if not df_tasks.empty:
            # Converte colunas de data para datetime, tratando erros
            df_tasks['created_at'] = pd.to_datetime(df_tasks['created_at'], errors='coerce')
            df_tasks['due_date'] = pd.to_datetime(df_tasks['due_date'], errors='coerce')
        
        st.session_state.tasks_df = df_tasks
        st.session_state.tasks = tasks_data # Mantém a lista original para salvar em JSON
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

    st.divider()

    with st.expander("🎯 Metas da Obra", expanded=True):
        if is_admin:
            goals = st.text_area(
                "Descreva as metas principais do projeto:",
                value=st.session_state.config.get("project_goals", ""),
                height=150,
                key="project_goals_text",
                help="Defina os objetivos gerais que guiarão todas as atividades da obra."
            )
            if st.button("Salvar Metas", use_container_width=True):
                st.session_state.config["project_goals"] = goals
                DataManager.save(CONFIG_FILE, st.session_state.config)
                add_activity("config", "Metas Atualizadas", "As metas gerais da obra foram definidas/atualizadas.")
                st.toast("Metas salvas com sucesso!")
                st.rerun()
        else:
            goals = st.session_state.config.get("project_goals", "Nenhuma meta definida.")
            st.markdown(goals if goals else "Nenhuma meta definida.")

    st.header("Feed de Atividades")
    for activity in st.session_state.activities[:5]:
        st.info(f"**{activity['type']} {activity['title']}**\n\n_{activity['desc']}_\n\n`{activity['time']}`")
    st.divider()
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
# Abas da aplicação
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard",
    "📋 Gestão de Tarefas",
    "👷 Gestão de Pessoal",
    "⚙️ Gestão de Configurações",
    "📈 Relatórios Detalhados"
])

# =================================================================================
# --- ABA 1: DASHBOARD ---
# =================================================================================
with tab1:
    st.subheader("Visão Geral do Projeto")
    if st.session_state.tasks_df.empty:
        st.warning("Nenhuma tarefa cadastrada. Adicione tarefas para visualizar os relatórios.")
    else:
        df_tasks = st.session_state.tasks_df
        
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
        st.divider()

        # --- GRÁFICOS DE DESEMPENHO ---
        st.subheader("Indicadores de Desempenho")
        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            st.markdown("##### **Status das Tarefas**", help="Distribuição percentual das tarefas por status.")
            status_counts = df_tasks['status'].value_counts().reset_index()
            status_counts.columns = ['status', 'count']
            fig_status = px.pie(status_counts, names='status', values='count', hole=.4,
                                title="Distribuição por Status",
                                color='status', color_discrete_map={'Concluída':'#2ca02c', 'Em Andamento':'#ff7f0e', 'Planejada':'#1f77b4'})
            fig_status.update_traces(textinfo='percent+value', textfont_size=14, pull=[0.05, 0, 0])
            fig_status.update_layout(legend_title_text='Status', margin=dict(t=40, b=20, l=20, r=20))
            st.plotly_chart(fig_status, use_container_width=True)

        with col_chart2:
            st.markdown("##### **Progresso por Setor**", help="Média de conclusão das tarefas em cada setor da obra.")
            progress_by_sector = df_tasks.groupby('sector')['progress'].mean().sort_values(ascending=False).reset_index()
            fig_sector = px.bar(progress_by_sector, x='sector', y='progress', text='progress',
                                title="Progresso Médio por Setor",
                                color='progress', color_continuous_scale=px.colors.sequential.Greens)
            fig_sector.update_traces(texttemplate='%{text:.2s}%', textposition='outside')
            fig_sector.update_layout(xaxis_title="Setor", yaxis_title="Progresso Médio (%)", coloraxis_showscale=False)
            st.plotly_chart(fig_sector, use_container_width=True)

        col_chart3, col_chart4 = st.columns(2)
        with col_chart3:
            st.markdown("##### **Carga de Trabalho por Equipe**", help="Número de tarefas (concluídas, em andamento, planejadas) por equipe.")
            tasks_by_team_status = df_tasks.groupby(['team', 'status']).size().reset_index(name='count')
            fig_teams = px.bar(tasks_by_team_status, x='team', y='count', color='status',
                               title="Tarefas por Equipe e Status",
                               labels={'team': 'Equipe', 'count': 'Nº de Tarefas', 'status': 'Status'},
                               color_discrete_map={'Concluída':'#2ca02c', 'Em Andamento':'#ff7f0e', 'Planejada':'#1f77b4'},
                               text_auto=True)
            fig_teams.update_layout(xaxis={'categoryorder':'total descending'}, yaxis_title="Nº de Tarefas", xaxis_title=None)
            st.plotly_chart(fig_teams, use_container_width=True)

        with col_chart4:
            st.markdown("##### **Situação dos Prazos**", help="Classificação de tarefas pendentes por prazo de vencimento.")
            today = pd.to_datetime(date.today())
            df_tasks_pending = df_tasks[df_tasks['status'] != 'Concluída'].copy()

            if not df_tasks_pending.empty:
                df_tasks_pending['due_category'] = df_tasks_pending['due_date'].apply(get_due_category)
                due_counts = df_tasks_pending['due_category'].value_counts().reset_index()
                due_counts.columns = ['category', 'count']

                category_order = ["Atrasada", "Vence em 7 dias", "Em Dia", "Sem Prazo"]
                fig_due_date = px.bar(due_counts, x='category', y='count', color='category', text_auto=True,
                                      title="Análise de Prazos das Tarefas Pendentes",
                                      labels={'category': 'Status do Prazo', 'count': 'Nº de Tarefas'},
                                      color_discrete_map={'Atrasada': '#d62728', 'Vence em 7 dias': '#ff7f0e', 'Em Dia': '#2ca02c', 'Sem Prazo': '#7f7f7f'},
                                      category_orders={"category": category_order})
                fig_due_date.update_layout(xaxis_title=None, yaxis_title="Nº de Tarefas", showlegend=False)
                st.plotly_chart(fig_due_date, use_container_width=True)
            else:
                st.info("Nenhuma tarefa pendente.")

        st.divider()
        st.subheader("Cronograma da Obra (Gráfico de Gantt)")
        if df_tasks.empty:
            st.info("Nenhuma tarefa para exibir no cronograma.")
        else:
            df_gantt = df_tasks[['name', 'created_at', 'due_date', 'team']].copy()
            df_gantt.rename(columns={'name': 'Task', 'created_at': 'Start', 'due_date': 'Finish', 'team': 'Resource'}, inplace=True)
            df_gantt.dropna(subset=['Start', 'Finish'], inplace=True)

            if not df_gantt.empty:
                fig_gantt = px.timeline(df_gantt, x_start="Start", x_end="Finish", y="Task", color="Resource",
                                        title="Linha do Tempo das Tarefas por Equipe")
                fig_gantt.update_yaxes(autorange="reversed", title=None)
                fig_gantt.update_xaxes(title="Linha do Tempo")
                
                # Adiciona linha vertical para o dia de hoje
                fig_gantt.add_shape(type='line',
                                  x0=datetime.now(), y0=0,
                                  x1=datetime.now(), y1=1,
                                  yref='paper',
                                  line=dict(color='red', width=2, dash='dash'))
                fig_gantt.add_annotation(x=datetime.now(), y=1.05, yref='paper',
                                       showarrow=False, text="Hoje",
                                       font=dict(color="red"))
                st.plotly_chart(fig_gantt, use_container_width=True)
            else:
                st.warning("Nenhuma tarefa com datas válidas para gerar o cronograma.")

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

    st.divider()
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

                col1, col2, col3 = st.columns(3)

                new_name = col1.text_input("Nome", value=task.get('name', ''), key=f"name_{task['id']}", disabled=not is_admin)

                team_name = task.get('team')
                current_team_index = available_teams.index(team_name) if team_name in available_teams else None
                new_team = col2.selectbox("Equipe", available_teams, index=current_team_index, key=f"team_{task['id']}", disabled=not is_admin)

                sector_name = task.get('sector')
                current_sector_index = available_sectors.index(sector_name) if sector_name in available_sectors else None
                new_sector = col3.selectbox("Setor", available_sectors, index=current_sector_index, key=f"sector_{task['id']}", disabled=not is_admin)

                col_date1, col_date2 = st.columns(2)
                start_date_val = datetime.strptime(task.get('created_at', str(date.today())), "%Y-%m-%d").date()
                new_start_date = col_date1.date_input("Início", value=start_date_val, key=f"start_date_{task['id']}", disabled=not is_admin)

                due_date_val = datetime.strptime(task.get('due_date', str(date.today())), "%Y-%m-%d").date()
                new_due_date = col_date2.date_input("Vencimento", value=due_date_val, key=f"due_date_{task['id']}", disabled=not is_admin)

                new_progress = st.slider("Progresso (%)", 0, 100, task.get('progress', 0), key=f"progress_{task['id']}", disabled=not is_admin)

                if st.button("💾 Salvar", key=f"save_{task['id']}", use_container_width=True, disabled=not is_admin):
                    if new_start_date > new_due_date:
                        st.error("A data de início não pode ser posterior à data de vencimento.", icon="🚨")
                    else:
                        task_index = next((i for i, t in enumerate(st.session_state.tasks) if t['id'] == task['id']), None)
                        if task_index is not None:
                            st.session_state.tasks[task_index].update({
                                'name': new_name, 'team': new_team, 'sector': new_sector,
                                'created_at': new_start_date.strftime("%Y-%m-%d"),
                                'due_date': new_due_date.strftime("%Y-%m-%d"), 'progress': new_progress,
                                'status': get_task_status({'progress': new_progress})
                            })
                            save_tasks_state()
                            add_activity("update", "Tarefa Atualizada", f"A tarefa '{original_task.get('name', '')}' foi atualizada.")
                            st.success(f"Tarefa '{new_name}' atualizada!")
                            st.rerun()

                if st.button("🗑️ Excluir", key=f"delete_{task['id']}", use_container_width=True, disabled=not is_admin):
                    st.session_state.confirm_delete = task['id']
                    st.rerun()

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

    st.divider()
    st.subheader("Funcionários Cadastrados")
    employees = st.session_state.people.get('employees', [])
    if not employees:
        st.info("Nenhum funcionário cadastrado.")
    else:
        df_people = pd.DataFrame(employees)

        dataframe_args = {
            "use_container_width": True,
            "hide_index": True,
            "key": "employee_selector"
        }

        if is_admin:
            dataframe_args["on_select"] = "rerun"
            dataframe_args["selection_mode"] = "single-row"

        st.dataframe(df_people, **dataframe_args)

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
                        deleted_sector_name = st.session_state.config["sectors"].pop(i)['name']
                        DataManager.save(CONFIG_FILE, st.session_state.config)
                        add_activity("delete", "Setor Removido", f"O setor '{deleted_sector_name}' foi removido.")
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
                            # Atualiza em cascata
                            for task in st.session_state.tasks:
                                if task.get('team') == old_name:
                                    task['team'] = new_name
                            save_tasks_state()
                            for emp in st.session_state.people.get('employees', []):
                                if emp.get('team') == old_name:
                                    emp['team'] = new_name
                            DataManager.save(PEOPLE_FILE, st.session_state.people)
                            add_activity("update", "Equipe Atualizada", f"Equipe '{old_name}' atualizada para '{new_name}'.")
                            st.rerun()
                        else:
                            st.error("Nome inválido ou já existente.")

                    if col_btn2.form_submit_button("❌", disabled=not is_admin or is_in_use, help="Excluir equipe (só se não estiver em uso)"):
                        deleted_team_name = st.session_state.config["teams"].pop(i)['name']
                        DataManager.save(CONFIG_FILE, st.session_state.config)
                        add_activity("delete", "Equipe Removida", f"A equipe '{deleted_team_name}' foi removida.")
                        st.rerun()

# =================================================================================
# --- ABA 5: RELATÓRIOS DETALHADOS ---
# =================================================================================
with tab5:
    st.subheader("Gerador de Relatórios para Diretoria")

    if 'report_html' not in st.session_state:
        st.session_state.report_html = None

    # --- PAINEL DE FILTROS ---
    st.markdown("Selecione os filtros desejados para gerar um relatório detalhado e profissional.")
    if not st.session_state.tasks:
        st.info("Nenhuma tarefa cadastrada para gerar relatórios.")
    else:
        df_tasks = st.session_state.tasks_df
        with st.container(border=True):
            st.markdown("#### **1. Definir Parâmetros do Relatório**")
            col_filter1, col_filter2, col_filter3 = st.columns(3)
            all_teams = ["Todas"] + sorted(df_tasks['team'].unique().tolist())
            selected_team = col_filter1.selectbox("Filtrar por Equipe:", all_teams, key="report_team_filter")

            all_sectors = ["Todos"] + sorted(df_tasks['sector'].unique().tolist())
            selected_sector = col_filter2.selectbox("Filtrar por Setor:", all_sectors, key="report_sector_filter")

            all_statuses = ["Todos"] + sorted(df_tasks['status'].unique().tolist())
            selected_status = col_filter3.selectbox("Filtrar por Status:", all_statuses, key="report_status_filter")

        if st.button("📄 Gerar Relatório", use_container_width=True, type="primary"):
            # --- LÓGICA DE FILTRAGEM OTIMIZADA ---
            query = []
            if selected_team != "Todas":
                query.append(f"team == '{selected_team}'")
            if selected_sector != "Todos":
                query.append(f"sector == '{selected_sector}'")
            if selected_status != "Todos":
                query.append(f"status == '{selected_status}'")
            
            filtered_report_tasks = df_tasks.query(" and ".join(query)) if query else df_tasks.copy()

            if filtered_report_tasks.empty:
                st.warning("Nenhuma tarefa encontrada com os filtros selecionados.")
                st.session_state.report_html = None
            else:
                filters = {"team": selected_team, "sector": selected_sector, "status": selected_status}
                project_goals = st.session_state.config.get("project_goals", "")
                st.session_state.report_html = generate_report_html(filtered_report_tasks, project_goals, filters)

    # --- EXIBIÇÃO DO RELATÓRIO ---
    if st.session_state.report_html:
        st.divider()
        st.markdown("#### **2. Pré-visualização e Download**")

        # Botão de Download
        st.download_button(
            label="📥 Baixar Relatório em HTML",
            data=st.session_state.report_html,
            file_name=f"relatorio_obra_{datetime.now().strftime('%Y%m%d')}.html",
            mime="text/html",
            use_container_width=True
        )

        # Pré-visualização
        with st.container(height=600, border=True):
            st.components.v1.html(st.session_state.report_html, height=600, scrolling=True)
