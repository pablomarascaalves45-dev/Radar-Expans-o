import streamlit as st
import pandas as pd

# 1. Configuração da página
st.set_page_config(page_title="Radar de Expansão", layout="centered")

# 2. Estilização para modo Dark e alinhamento das métricas
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #ffffff !important; }
    [data-testid="stMetricLabel"] { font-size: 1rem !important; color: #9da5b1 !important; }
    .stSelectbox label { display: none; } /* Esconde o label para ficar igual ao print */
    </style>
    """, unsafe_allow_html=True)

# 3. Título do App
st.title("🎯 Radar de Expansão")
st.subheader("1. Mercado da Cidade")

@st.cache_data
def load_data():
    try:
        # Carrega pulando a primeira linha de título preto
        df = pd.read_excel('Ranking PCA Cidades.xlsx', skiprows=1)
        # Limpa nomes de colunas
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Erro ao carregar planilha: {e}")
        return None

df = load_data()

if df is not None:
    coluna_cidade = 'Município'
    
    if coluna_cidade in df.columns:
        # Cria a barra de busca/seleção
        cidades = sorted(df[coluna_cidade].unique())
        cidade_selecionada = st.selectbox("Busque o Município:", options=cidades, index=0)

        if cidade_selecionada:
            # Puxa a linha da cidade selecionada
            dados = df[df[coluna_cidade] == cidade_selecionada].iloc[0]

            st.write("---")

            # Layout de 2 colunas para as métricas
            col1, col2 = st.columns(2)

            with col1:
                # Métrica de População
                pop = dados.get('População', 0)
                if isinstance(pop, str): pop = pop.replace('.', '')
                st.metric(label="👥 População", value=f"{int(float(pop)):,}".replace(',', '.'))
                
                # Métrica de Share da Cidade
                share = dados.get('%Share', 0)
                if isinstance(share, (float, int)):
                    share_txt = f"{share * 100:.2f}".replace('.', ',')
                else:
                    share_txt = str(share).replace('.', ',').replace('%', '')
                st.metric(label="📊 Share da Cidade", value=f"{share_txt}%")

            with col2:
                # Métrica de Lojas Atuais
                lojas = dados.get('Nº FSJ', 0)
                st.metric(label="🏠 Lojas Atuais (FSJ)", value=int(lojas) if pd.notnull(lojas) else 0)
                
                # Métrica de Porte
                porte = dados.get('Porte da cidade', 'N/D')
                st.metric(label="📍 Porte", value=porte)

            st.write("---")

            # Rodapé dinâmico igual ao print
            regiao = dados.get('REGIÃO GEOGRÁFICA IMEDIATA', 'N/A')
            st.markdown(f"**Município:** {cidade_selecionada} | **Região:** {regiao}")
    else:
        st.error(f"A coluna '{coluna_cidade}' não foi encontrada na planilha.")
