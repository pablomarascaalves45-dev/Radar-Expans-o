import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Radar de Expansão", layout="centered")

# Estilização personalizada (CSS)
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #ffffff !important; }
    [data-testid="stMetricLabel"] { font-size: 1rem !important; color: #9da5b1 !important; }
    /* Ajuste para a barra de pesquisa */
    .stSelectbox label { color: #ffffff !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# Título do App
st.title("🎯 Radar de Expansão")
st.subheader("1. Mercado da Cidade")

# Função para carregar os dados
@st.cache_data
def load_data():
    try:
        # Tenta carregar o CSV. Se o erro persistir, verifique se o separador é ',' ou ';'
        df = pd.read_csv('planilha.csv', sep=',') 
        df.columns = df.columns.str.strip() # Remove espaços nos nomes das colunas
        return df
    except FileNotFoundError:
        st.error("Arquivo 'planilha.csv' não encontrado no diretório.")
        return None

df = load_data()

if df is not None:
    # Barra de busca (Selectbox com busca por texto integrada)
    # Dica: O Streamlit já permite digitar dentro do selectbox para filtrar
    cidades_disponiveis = sorted(df['Município'].unique())
    
    cidade_selecionada = st.selectbox(
        "Selecione ou digite o nome do município:",
        options=cidades_disponiveis,
        help="Clique e digite o nome da cidade para filtrar rapidamente."
    )

    if cidade_selecionada:
        # Filtrar dados da cidade escolhida
        dados = df[df['Município'] == cidade_selecionada].iloc[0]

        st.divider() # Linha horizontal moderna

        # Exibição das métricas em colunas
        col1, col2 = st.columns(2)

        with col1:
            # Formatação de número para padrão brasileiro (Ponto no milhar)
            pop = f"{int(dados['populacao']):,}".replace(',', '.')
            st.metric(label="👥 População", value=pop)
            
            # Formatação de percentual
            share = f"{dados['share']}".replace('.', ',')
            st.metric(label="📊 Share da Cidade", value=f"{share}%")

        with col2:
            # Valor de lojas
            vagas = int(dados['vagas_lojas'])
            st.metric(label="🏠 Quantas lojas cabem", value=vagas)
            
            # Status (adicionado para aproveitar a lógica do PCA anterior)
            if 'status' in df.columns:
                st.metric(label="📍 Status", value=dados['status'])

        st.divider()
        
        # Rodapé informativo
        st.caption(f"Exibindo dados de: **{cidade_selecionada}**")
else:
    st.info("Aguardando carregamento da base de dados...")
