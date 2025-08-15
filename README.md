Gestor de Obras Pro 🏗️
Gestor de Obras Pro é uma aplicação web interativa desenvolvida com Streamlit para o gerenciamento e acompanhamento de projetos de construção civil. A ferramenta centraliza o controle de tarefas, equipes e setores, oferecendo um dashboard visual para análise de progresso e desempenho.

## 📋 Índice

Funcionalidades Principais

Como Executar o Projeto

Estrutura de Arquivos

Tecnologias Utilizadas

Como Contribuir

Licença

✨ Funcionalidades Principais
Dashboard Interativo: Métricas e gráficos dinâmicos (rosca, barras, Gantt) para uma visão geral do progresso da obra, status das tarefas, carga de trabalho por equipe e análise de prazos.

Gestão de Tarefas Completa: Crie, edite e exclua tarefas, atribuindo-as a equipes e setores específicos. Acompanhe o progresso individual de cada tarefa.

Gerenciamento de Pessoal: Cadastre funcionários, aloque-os em equipes e mantenha um registro centralizado da sua força de trabalho.

Configuração Flexível do Projeto: Adicione, edite e remova setores da obra e equipes de trabalho de acordo com as necessidades do seu projeto.

Feed de Atividades: Um log em tempo real que registra as ações mais importantes realizadas na aplicação, como criação ou exclusão de tarefas.

Persistência de Dados: Todas as informações são salvas localmente em arquivos JSON, garantindo que seus dados não sejam perdidos ao fechar a aplicação.

Backup Automático: O sistema cria backups automáticos do arquivo de tarefas para prevenir perda de dados.

🚀 Como Executar o Projeto
Siga os passos abaixo para executar o Gestor de Obras Pro em sua máquina local.

Pré-requisitos
Python 3.7 ou superior

Pip (gerenciador de pacotes do Python)

Instalação
Clone o repositório:

Bash

git clone https://github.com/seu-usuario/gestor-de-obras-pro.git
cd gestor-de-obras-pro
Crie e ative um ambiente virtual (recomendado):

Bash

# Para Windows
python -m venv venv
venv\Scripts\activate

# Para macOS/Linux
python3 -m venv venv
source venv/bin/activate
Instale as dependências:
Crie um arquivo requirements.txt com o seguinte conteúdo:

Plaintext

streamlit
pandas
plotly
E então instale as bibliotecas:

Bash

pip install -r requirements.txt
Executando a Aplicação
Com as dependências instaladas, inicie o servidor do Streamlit com o comando:

Bash

streamlit run PLANEJAMENTO_DE_OBRA.py
A aplicação será aberta automaticamente no seu navegador padrão.

📂 Estrutura de Arquivos
O projeto utiliza uma estrutura simples para armazenar os dados e o código-fonte:

.
├── PLANEJAMENTO_DE_OBRA.py     # Arquivo principal da aplicação Streamlit
├── datatasks.json              # Armazena os dados das tarefas
├── data_activities.json        # Armazena o log de atividades recentes
├── dataconfig.json             # Armazena as configurações de setores e equipes
├── data_people.json            # Armazena os dados dos funcionários
├── backup_tasks/               # Diretório para backups automáticos das tarefas
│   └── backup_tasks_*.json
└── README.md                   # Este arquivo
datatasks.json: Salva a lista de todas as tarefas do projeto.

data_activities.json: Mantém um histórico das últimas atividades realizadas.

dataconfig.json: Guarda as listas de setores e equipes que podem ser usados no projeto.

data_people.json: Contém as informações dos funcionários cadastrados.

backup_tasks/: Diretório onde os backups do arquivo de tarefas são armazenados com data e hora.

🛠️ Tecnologias Utilizadas
Streamlit: Framework principal para a criação da interface web interativa.

Pandas: Utilizado para manipulação e análise dos dados das tarefas.

Plotly Express: Para a geração dos gráficos e visualizações de dados no dashboard.

🤝 Como Contribuir
Contribuições são bem-vindas! Se você tem ideias para novas funcionalidades ou encontrou algum problema, sinta-se à vontade para:

Fazer um Fork do projeto.

Criar uma Branch para sua modificação (git checkout -b feature/sua-feature).

Fazer o Commit de suas mudanças (git commit -am 'Adiciona nova feature').

Fazer o Push para a Branch (git push origin feature/sua-feature).

Abrir um Pull Request.

📄 Licença
Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.
