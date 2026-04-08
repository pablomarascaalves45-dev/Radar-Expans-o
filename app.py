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
        # Carrega o Excel
        df = pd.read_excel('Ranking PCA Cidades.xlsx') 
        # Limpeza: remove espaços extras e garante que os nomes batam com a imagem
        df.columns = df.columns.str.strip() 
        return df
    except Exception as e:
        st.error(f"Erro ao ler a planilha: {e}")
        return None

df = load_data()

if df is not None:
    # Nome da coluna conforme a imagem: 'Município'
    coluna_cidade = 'Município' 
    
    if coluna_cidade in df.columns:
        cidades_disponiveis = sorted(df[coluna_cidade].unique())
        
        cidade_selecionada = st.selectbox(
            "Selecione ou digite o nome do município:",
            options=cidades_disponiveis,
            help="Digite o nome da cidade para filtrar."
        )

        if cidade_selecionada:
            # Filtra a linha da cidade
            dados = df[df[coluna_cidade] == cidade_selecionada].iloc[0]

            st.divider()

            col1, col2 = st.columns(2)

            with col1:
                # 1. População (Nome exato na imagem: 'População')
                # Tratando caso o Excel leia como string com pontos (ex: 1.773.733)
                pop_bruta = dados.get('População', 0)
                if isinstance(pop_bruta, str):
                    pop_val = pop_bruta.replace('.', '')
                else:
                    pop_val = pop_bruta
                
                st.metric(label="👥 População", value=f"{int(pop_val):,}".replace(',', '.'))
                
                # 2. %Share (Nome exato na imagem: '%Share')
                share_val = dados.get('%Share', '0')
                # Se vier como decimal (0.0762), multiplicamos por 100
                if isinstance(share_val, (float, int)):
                    share_display = f"{share_val * 100:.2f}".replace('.', ',')
                else:
                    share_display = str(share_val).replace('.', ',')
                
                st.metric(label="📊 Share da Cidade", value=f"{share_display}%")

            with col2:
                # 3. Nº FSJ (Ajustei para o que aparece na imagem, já que 'vagas_lojas' não é visível)
                fsj_val = int(dados.get('Nº FSJ', 0))
                st.metric(label="🏠 Lojas Atuais (FSJ)", value=fsj_val)
                
                # 4. Porte da cidade (Nome exato na imagem: 'Porte da cidade')
                porte = dados.get('Porte da cidade', 'N/A')
                st.metric(label="📍 Porte", value=porte)

            st.divider()
            
            # Informação extra da Região (Coluna: 'REGIÃO GEOGRÁFICA IMEDIATA')
            regiao = dados.get('REGIÃO GEOGRÁFICA IMEDIATA', 'Não informada')
            st.caption(f"Município: **{cidade_selecionada}** | Região: **{regiao}**")
    else:
        st.error(f"Coluna '{coluna_cidade}' não encontrada. Verifique se o nome na planilha é exatamente 'Município'.")
else:
    st.info("Aguardando carregamento da base de dados...")
