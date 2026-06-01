import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta, time
import plotly.express as px

# ============================
# CONFIGURAÇÕES INICIAIS
# ============================
st.set_page_config(
    page_title="Dashboard de Chamados",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Paleta de cores
PRIMARY_BG = "#0F172A"         # Fundo primário
SECONDARY_BG = "#1E293B"       # Fundo secundário
PRIMARY_COLOR = "#F1F5F9"      # Cor do texto
ACCENT_COLOR = "#38BDF8"       # Cor de destaque
ALERT_COLOR = "#EF4444"        # Cor para alertas

# ============================
# CSS CUSTOMIZADO COM MODO ESCURO PADRÃO E ESTILO FUTURISTA
# ============================
st.markdown(f"""
<meta name="color-scheme" content="dark">
<link href="https://fonts.googleapis.com/css2?family=Orbitron&display=swap" rel="stylesheet">
<style>
    /* Configuração global do fundo e fontes */
    body, .stApp {{
        background: linear-gradient(135deg, {PRIMARY_BG}, {SECONDARY_BG});
        color: {PRIMARY_COLOR};
        font-family: 'Roboto', sans-serif;
        min-height: 100vh;
        margin: 0;
    }}
    /* Títulos com estilo futurista */
    h1, h2, h3, h4, h5, h6 {{
        font-family: 'Orbitron', sans-serif;
        color: {ACCENT_COLOR};
        text-shadow: 2px 2px 5px rgba(0, 0, 0, 0.7);
    }}
    /* Botões com efeito hover e sombra */
    .stButton button {{
        background-color: {ACCENT_COLOR};
        color: {PRIMARY_COLOR};
        border-radius: 8px;
        padding: 10px 20px;
        border: none;
        font-size: 16px;
        transition: background-color 0.3s ease, transform 0.2s ease;
        box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
    }}
    .stButton button:hover {{
        background-color: #005f99;
        transform: scale(1.02);
    }}
    /* Inputs com fundo claro para melhor legibilidade */
    .stTextInput input {{
        color: black;
        border-radius: 4px;
        padding: 8px;
    }}
    /* Sidebar customizada */
    .css-1d391kg {{
        background: {SECONDARY_BG};
    }}
    /* Efeito de fade-in para os gráficos */
    .fade-in {{
        animation: fadeInAnimation ease 1.5s;
        animation-iteration-count: 1;
        animation-fill-mode: forwards;
    }}
    @keyframes fadeInAnimation {{
        0%   {{ opacity: 0; transform: translateY(20px); }}
        100% {{ opacity: 1; transform: translateY(0); }}
    }}
    /* Estilo para os "cards" de métricas com efeito hover */
    .card {{
        background: {SECONDARY_BG};
        padding: 20px;
        border-radius: 10px;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.2);
        text-align: center;
        transition: transform 0.3s ease;
    }}
    .card:hover {{
        transform: scale(1.02);
    }}
    .card h3 {{
        margin: 0;
        color: {ACCENT_COLOR};
    }}
    .card p {{
        font-size: 28px;
        margin: 10px 0 0 0;
        font-weight: bold;
    }}
</style>
""", unsafe_allow_html=True)

# ============================
# CONEXÃO COM O BANCO DE DADOS
# ============================
class DatabaseConnector:
    def __init__(self):
        self.config = {
            "host": "172.16.1.189",
            "port": 3306,
            "user": "central_user",
            "password": "evt123456",
            "database": "central",
            "charset": "utf8",
            "use_unicode": True
        }
    
    def __enter__(self):
        try:
            self.conn = mysql.connector.connect(**self.config)
            return self.conn
        except Error as e:
            st.error(f"Erro ao conectar ao banco de dados: {e}")
            return None
    
    def __exit__(self, exc_type, exc_value, traceback):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()

# ============================
# FUNÇÕES DE CONSULTA ATUALIZADAS
# ============================
def consultar_chamados(data_inicio, data_fim, local=None, tipo=None, status=None):
    """Consulta o total de chamados com filtros aplicados"""
    with DatabaseConnector() as conexao:
        if not conexao:
            return None
        try:
            cursor = conexao.cursor()
            query = """SELECT COUNT(*) AS total_chamados 
                       FROM chamados 
                       WHERE data_entrada BETWEEN %s AND %s"""
            params = [data_inicio, data_fim]
            
            if local:
                query += " AND Amb_Solic_Amb_Emp_has_And_Andares_Edificios_nome = %s"
                params.append(local)
                
            if tipo:
                query += " AND idChamado LIKE %s"
                params.append(f"{tipo}%")
                
            if status:
                query += " AND status = %s"
                params.append(status)
                
            cursor.execute(query, tuple(params))
            return cursor.fetchone()[0] or 0
        except Error as e:
            st.error(f"Erro na consulta SQL: {e}")
            return None

def consultar_por_local(data_inicio, data_fim, tipo=None):
    """Consulta chamados agrupados por local com filtro de tipo"""
    with DatabaseConnector() as conexao:
        if not conexao:
            return None
        try:
            cursor = conexao.cursor()
            query = """SELECT Amb_Solic_Amb_Emp_has_And_Andares_Edificios_nome AS Local, 
                               COUNT(*) AS Total
                        FROM chamados
                        WHERE data_entrada BETWEEN %s AND %s"""
            params = [data_inicio, data_fim]
            
            if tipo:
                query += " AND idChamado LIKE %s"
                params.append(f"{tipo}%")
                
            query += """ GROUP BY Local
                         ORDER BY Total DESC
                         LIMIT 13"""
            
            cursor.execute(query, tuple(params))
            return pd.DataFrame(cursor.fetchall(), columns=["Local", "Total"])
        except Error as e:
            st.error(f"Erro na consulta por Local: {e}")
            return None

def consultar_ultimos_solicitantes(data_inicio, data_fim, tipo=None):
    """Consulta os últimos 7 solicitantes"""
    with DatabaseConnector() as conexao:
        if not conexao:
            return None
        try:
            cursor = conexao.cursor()
            query = """SELECT solicitante, MAX(data_entrada) AS Ultima_Solicitacao 
                       FROM chamados
                       WHERE data_entrada BETWEEN %s AND %s"""
            params = [data_inicio, data_fim]
            
            if tipo:
                query += " AND idChamado LIKE %s"
                params.append(f"{tipo}%")
                
            query += """ GROUP BY solicitante
                         ORDER BY Ultima_Solicitacao DESC
                         LIMIT 7"""
            
            cursor.execute(query, tuple(params))
            return pd.DataFrame(cursor.fetchall(), columns=["Solicitante", "Última Solicitação"])
        except Error as e:
            st.error(f"Erro na consulta de solicitantes: {e}")
            return None

def consultar_empresas_externas(data_inicio, data_fim):
    """Consulta empresas com mais chamados externos (OP)"""
    with DatabaseConnector() as conexao:
        if not conexao:
            return None
        try:
            cursor = conexao.cursor()
            query = """SELECT Amb_Solic_Amb_Emp_has_And_Empresas_nome AS Empresa,
                          COUNT(*) AS Total
                        FROM chamados
                        WHERE data_entrada BETWEEN %s AND %s
                          AND idChamado LIKE '%OP%'
                        GROUP BY Empresa
                        ORDER BY Total DESC"""
            
            cursor.execute(query, (data_inicio, data_fim))
            return pd.DataFrame(cursor.fetchall(), columns=["Empresa", "Total"])
        except Error as e:
            st.error(f"Erro na consulta de empresas: {e}")
            return None
def consultar_por_tipo(data_inicio, data_fim):
    """Consulta chamados agrupados por Tipo"""
    with DatabaseConnector() as conexao:
        if not conexao:
            return None
        try:
            cursor = conexao.cursor()
            query = """SELECT SUBSTRING(idChamado, 1, 2) AS Tipo, 
                              COUNT(*) AS Total
                       FROM chamados
                       WHERE data_entrada BETWEEN %s AND %s
                       GROUP BY Tipo
                       ORDER BY Tipo ASC"""
            cursor.execute(query, (data_inicio, data_fim))
            return pd.DataFrame(cursor.fetchall(), columns=["Tipo", "Total"])
        except Error as e:
            st.error(f"Erro na consulta por Tipo: {e}")
            return None


# ==========================================
# FUNÇÕES DE VISUALIZAÇÃO ATUALIZADAS
# ==========================================
def criar_grafico_empresas(df):
    if df.empty:
        st.warning("Nenhum dado disponível para empresas externas")
        return
    
    fig = px.bar(
        df,
        x='Empresa',
        y='Total',
        title='Chamados Externos por Empresa',
        color='Total',
        color_continuous_scale=[SECONDARY_BG, ACCENT_COLOR]
    )
    fig.update_layout(
        template="plotly_dark",
        xaxis_tickangle=-45,
        plot_bgcolor=PRIMARY_BG,
        paper_bgcolor=SECONDARY_BG
    )
    st.plotly_chart(fig, use_container_width=True)

# ============================
# INTERFACE PRINCIPAL ATUALIZADA
# ============================
st.title("🔍 Dashboard de Chamados - Visão Completa")

# Filtros na sidebar
with st.sidebar:
    st.image("https://i.ibb.co/WV0yS2K/EVT-Analytica-3-1.jpg", use_column_width=True)
    st.header("Filtros Avançados")
    
    # Filtro de período com a nova opção "Dia atual (a partir das 6h)"
    opcao_periodo = st.selectbox(
        "Período:",
        ["Últimas 24 horas", "Última semana", "Último mês", "Último ano", "Personalizado"],
        index=0
    )
    
    # Filtros adicionais
    tipo_chamado = st.selectbox(
        "Tipo de Chamado:",
        ["Todos", "OP - Externo", "IN - Interno"],
        index=0
    )
    
    local_filtro = st.text_input("Filtrar por Local:")
    status_filtro = st.text_input("Filtrar por Status:")

# Processamento das datas
hoje = datetime.today()
if opcao_periodo == "Personalizado":
    data_inicio = st.sidebar.date_input("Data Inicial", hoje - timedelta(days=7))
    data_fim = st.sidebar.date_input("Data Final", hoje)
elif opcao_periodo == "Dia atual (a partir das 6h)":
    agora = datetime.now()
    if agora.time() >= time(6, 0):
        data_inicio = datetime.combine(agora.date(), time(6, 0))
        data_fim = datetime.combine(agora.date(), time(23, 59, 59))
    else:
        data_inicio = datetime.combine((agora - timedelta(days=1)).date(), time(6, 0))
        data_fim = datetime.combine(agora.date(), time(5, 59, 59))
else:
    periodos = {
        "Últimas 24 horas": (hoje - timedelta(days=1), hoje),
        "Última semana": (hoje - timedelta(weeks=1), hoje),
        "Último mês": (hoje.replace(day=1), hoje),
        "Último ano": (hoje.replace(year=hoje.year-1), hoje)
    }
    data_inicio, data_fim = periodos[opcao_periodo]

data_inicio_str = data_inicio.strftime('%Y-%m-%d %H:%M:%S')
data_fim_str = data_fim.strftime('%Y-%m-%d %H:%M:%S')

# Conversão do tipo de chamado para filtro
tipo = None
if tipo_chamado == "OP - Externo":
    tipo = "OP"
elif tipo_chamado == "IN - Interno":
    tipo = "IN"

# Execução das consultas
total = consultar_chamados(
    data_inicio_str,
    data_fim_str,
    local=local_filtro or None,
    tipo=tipo or None,
    status=status_filtro or None
)

df_locais = consultar_por_local(data_inicio_str, data_fim_str, tipo)
df_solicitantes = consultar_ultimos_solicitantes(data_inicio_str, data_fim_str, tipo)
df_empresas = consultar_empresas_externas(data_inicio_str, data_fim_str)

# Exibição dos resultados
if total is not None:
    # Cards superiores
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="card"><h3>Total de Chamados</h3><p>{total}</p></div>', unsafe_allow_html=True)
    with col2:
        tipo_exib = tipo_chamado.split(" -")[0] if tipo else "Todos"
        st.markdown(f'<div class="card"><h3>Tipo de Chamado</h3><p>{tipo_exib}</p></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="card"><h3>Período</h3><p>{opcao_periodo}</p></div>', unsafe_allow_html=True)
    
    # Abas principais
    tab1, tab2, tab3, tab4 = st.tabs(["Visão Geral", "Solicitantes", "Empresas Externas", "Tipos"])


    with tab1:
        st.subheader("Distribuição por Local")
        if df_locais is not None and not df_locais.empty:
            col1, col2 = st.columns([3, 2])
            with col1:
                fig = px.pie(
                    df_locais,
                    names='Local',
                    values='Total',
                    title='Distribuição de Chamados',
                    hole=0.3,
                    color_discrete_sequence=['#87C3D4', '#6BAEC3', '#4F98B2', '#3382A1', '#176C90'],
                    labels={'Local': 'Edifício'},
                    hover_data=['Total']
                )

                fig.update_traces(
                    hovertemplate="<br>".join([
                        "<b>%{label}</b>",
                        "Quantidade: %{value}",
                        "Percentual: %{percent}"
                    ]),
                    textinfo='percent+label',
                    textposition='inside',
                    textfont=dict(color='#010101', size=16),
                    marker=dict(
                        line=dict(color=PRIMARY_BG, width=0.5),
                    )
                )

                fig.update_layout(
                    showlegend=False,
                    paper_bgcolor=SECONDARY_BG,
                    plot_bgcolor=PRIMARY_BG,
                    font=dict(color=PRIMARY_COLOR),
                    margin=dict(t=50, b=20, l=20, r=20),
                    title_font=dict(size=20, color=ACCENT_COLOR)
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.dataframe(df_locais.set_index('Local'), height=400)
        else:
            st.warning("Nenhum dado disponível para os filtros selecionados")
    
    with tab3:
        st.subheader("Chamados Externos por Empresa")
        if df_empresas is not None and not df_empresas.empty:
            criar_grafico_empresas(df_empresas)
            st.dataframe(df_empresas.set_index('Empresa'))
        else:
            st.warning("Nenhum dado disponível para empresas externas")
            
      

else:
    st.error("Erro ao carregar dados. Verifique os filtros e conexão.")

    