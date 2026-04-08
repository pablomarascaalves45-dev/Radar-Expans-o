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
    .stSelectbox label { color: #ffffff !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# Título do App
st.title("🎯 Radar de Expansão")
st.subheader("1. Mercado da Cidade")

# Função para carregar os dados corrigida para Excel
@st.cache_data
def load_data():
    try:
        # Ajustado para ler Excel (.xlsx) e o nome correto do arquivo
        # Nota: Certifique-se de que 'openpyxl' está no seu requirements.txt
        df = pd.read_excel('Ranking PCA Cidades.xlsx') 
        df.columns = df.columns.str.strip() # Remove espaços nos nomes das colunas
        return df
    except FileNotFoundError:
        st.error("Arquivo 'Ranking PCA Cidades.xlsx' não encontrado no diretório do GitHub.")
        return None
    except Exception as e:
        st.error(f"Erro ao ler a planilha: {e}")
        return None

df = load_data()

if df is not None:
    # Barra de busca por município
    # Certifique-se que a coluna na planilha se chama exatamente 'Município'
    coluna_cidade = 'Município' 
    
    if coluna_cidade in df.columns:
        cidades_disponiveis = sorted(df[coluna_cidade].unique())
        
        cidade_selecionada = st.selectbox(
            "Selecione ou digite o nome do município:",
            options=cidades_disponiveis,
            help="Digite o nome da cidade para filtrar."
        )

        if cidade_selecionada:
            dados = df[df[coluna_cidade] == cidade_selecionada].iloc[0]

            st.divider()

            col1, col2 = st.columns(2)

            with col1:
                # População
                pop_val = dados.get('populacao', 0)
                st.metric(label="👥 População", value=f"{int(pop_val):,}".replace(',', '.'))
                
                # Share
                share_val = str(dados.get('share', '0')).replace('.', ',')
                st.metric(label="📊 Share da Cidade", value=f"{share_val}%")

            with col2:
                # Vagas
                vagas_val = int(dados.get('vagas_lojas', 0))
                st.metric(label="🏠 Quantas lojas cabem", value=vagas_val)
                
                # Status
                if 'status' in df.columns:
                    st.metric(label="📍 Status", value=dados['status'])

            st.divider()
            st.caption(f"Exibindo dados de: **{cidade_selecionada}**")
    else:
        st.error(f"Coluna '{coluna_cidade}' não encontrada. Verifique os nomes das colunas na planilha.")
else:
    st.info("Aguardando carregamento da base de dados...")
