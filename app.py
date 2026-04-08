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

@st.cache_data
def load_data():
    try:
        # O SEGREDO ESTÁ AQUI: skiprows=1 pula a linha preta de título
        df = pd.read_excel('Ranking PCA Cidades.xlsx', skiprows=1)
        
        # Limpa espaços extras nos nomes das colunas
        df.columns = [str(c).strip() for c in df.columns]
        
        # Remove colunas vazias que o Excel às vezes cria
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        
        return df
    except Exception as e:
        st.error(f"Erro ao ler a planilha: {e}")
        return None

df = load_data()

if df is not None:
    # Nome da coluna conforme a imagem da planilha
    coluna_cidade = 'Município'
    
    if coluna_cidade in df.columns:
        # Remove linhas que possam estar totalmente vazias no fim da planilha
        df = df.dropna(subset=[coluna_cidade])
        
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
                # 1. População
                pop_bruta = dados.get('População', 0)
                # Remove pontos se o Excel leu como texto (ex: 1.773.733 -> 1773733)
                if isinstance(pop_bruta, str):
                    pop_clean = "".join(filter(str.isdigit, pop_bruta))
                    pop_val = int(pop_clean) if pop_clean else 0
                else:
                    pop_val = int(pop_bruta) if pd.notnull(pop_bruta) else 0
                
                st.metric(label="👥 População", value=f"{pop_val:,}".replace(',', '.'))
                
                # 2. %Share
                share_val = dados.get('%Share', 0)
                if isinstance(share_val, (float, int)):
                    share_display = f"{share_val * 100:.2f}".replace('.', ',')
                else:
                    share_display = str(share_val).replace('.', ',').replace('%', '')
                
                st.metric(label="📊 Share da Cidade", value=f"{share_display}%")

            with col2:
                # 3. Nº FSJ
                fsj_val = dados.get('Nº FSJ', 0)
                st.metric(label="🏠 Lojas Atuais (FSJ)", value=int(fsj_val) if pd.notnull(fsj_val) else 0)
                
                # 4. Porte da cidade
                porte = dados.get('Porte da cidade', 'N/A')
                st.metric(label="📍 Porte", value=porte)

            st.divider()
            
            # Rodapé com Região
            regiao = dados.get('REGIÃO GEOGRÁFICA IMEDIATA', 'Não informada')
            st.caption(f"Município: **{cidade_selecionada}** | Região: **{regiao}**")
    else:
        st.error(f"Coluna '{coluna_cidade}' não encontrada.")
        st.write("Colunas lidas:", df.columns.tolist()) # Ajuda a debugar se o nome mudar
else:
    st.info("Aguardando carregamento da base de dados...")
