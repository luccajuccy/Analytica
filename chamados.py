import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
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
# CSS CUSTOMIZADO
# ============================
st.markdown(f"""
<meta name="color-scheme" content="dark">
<link href="https://fonts.googleapis.com/css2?family=Orbitron&display=swap" rel="stylesheet">
<style>
    /* ... (mantenha o CSS original) ... */
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
            st.error(f"Erro na conexão: {e}")
            return None
    
    def __exit__(self, exc_type, exc_value, traceback):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()

# ============================
# FUNÇÃO DE CONSULTA (MODIFICADA)
# ============================
def consultar_ops_30_dias():
    data_fim = datetime.today()
    data_inicio = data_fim - timedelta(days=30)
    
    with DatabaseConnector() as conexao:
        if not conexao:
            return None
        try:
            cursor = conexao.cursor()
            query = """
                SELECT 
                    DATE(data_entrada) AS Dia,
                    COUNT(*) AS Total
                FROM chamados
                WHERE 
                    data_entrada BETWEEN %s AND %s
                    AND idChamado LIKE 'OP%%'
                GROUP BY DATE(data_entrada)
                ORDER BY Dia
            """
            cursor.execute(query, (data_inicio, data_fim))
            resultado = cursor.fetchall()
            return pd.DataFrame(resultado, columns=["Dia", "Total"])
        except Error as e:
            st.error(f"Erro na consulta: {e}")
            return None

# ============================
# FUNÇÃO DE GRÁFICO (ATUALIZADA)
# ============================
def criar_grafico_interativo(df):
    st.markdown("### 📈 Análise de OPs por Dia")
    tipo_grafico = st.radio(
        "Selecione o tipo de gráfico:",
        ["Barras", "Linhas"],
        horizontal=True
    )
    
    if tipo_grafico == "Barras":
        fig = px.bar(
            df,
            x="Dia",
            y="Total",
            title="OPs por Dia - Últimos 30 Dias",
            color_discrete_sequence=[ACCENT_COLOR]
        )
    else:
        fig = px.line(
            df,
            x="Dia",
            y="Total",
            title="OPs por Dia - Últimos 30 Dias",
            markers=True,
            color_discrete_sequence=[ACCENT_COLOR]
        )
    
    fig.update_layout(
        plot_bgcolor=PRIMARY_BG,
        paper_bgcolor=SECONDARY_BG,
        font_color=PRIMARY_COLOR,
        xaxis_title="Data",
        yaxis_title="Quantidade de OPs",
        xaxis=dict(type='category')
    )
    
    st.plotly_chart(fig, use_container_width=True)

# ============================
# INTERFACE PRINCIPAL (ATUALIZADA)
# ============================
st.title("🔧 Monitor de Chamados - Últimos 30 Dias")

# Carregar dados
with st.spinner("Carregando dados de produção..."):
    df_ops = consultar_ops_30_dias()

if df_ops is not None:
    if not df_ops.empty:
        # Exibir métricas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de OPs", df_ops["Total"].sum())
        with col2:
            st.metric("Dia com Mais OPs", df_ops["Total"].max())
        with col3:
            st.metric("Média Diária", round(df_ops["Total"].mean(), 1))
        
        # Criar gráfico
        criar_grafico_interativo(df_ops)
        
        # Exibir dados brutos
        st.markdown("### 📋 Detalhamento Diário")
        st.dataframe(df_ops.style.background_gradient(
            cmap="Blues",
            subset=["Total"]
        ), use_container_width=True)
        
        # Botão de download
        csv = df_ops.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Baixar dados como CSV",
            data=csv,
            file_name="ops_ultimos_30_dias.csv",
            mime="text/csv"
        )
    else:
        st.warning("Nenhuma Ordem de Produção registrada nos últimos 30 dias!")
else:
    st.error("Falha ao carregar dados do banco.")

# ============================
# NOTAS TÉCNICAS
# ============================
st.markdown("---")
st.markdown("""
**Filtros Aplicados:**
- Período: Últimos 30 dias
- Tipo de Chamado: Exclusivamente OPs (ID começando com 'OP')
- Exclusão Automática: Todos registros iniciados com 'IN'
""")