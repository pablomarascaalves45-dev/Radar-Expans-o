import streamlit as st
import pandas as pd

# 1. Configuração da página
st.set_page_config(page_title="Radar de Expansão", layout="centered")

# 2. Estilização personalizada
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #ffffff !important; }
    [data-testid="stMetricLabel"] { font-size: 1rem !important; color: #9da5b1 !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. Título do App
st.title("🎯 Radar de Expansão")
st.subheader("1. Mercado da Cidade")

@st.cache_data
def load_data():
    try:
        # ATUALIZADO: Nome do arquivo conforme seu GitHub
        # ATUALIZADO: skiprows=1 para ignorar o cabeçalho preto da planilha
        df = pd.read_excel('Ranking PCA.xlsx', skiprows=1)
        
        # Limpa espaços em branco nos nomes das colunas
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Erro ao carregar 'Ranking PCA.xlsx': {e}")
        return None

df = load_data()

if df is not None:
    coluna_cidade = 'Município'
    
    if coluna_cidade in df.columns:
        # Remove linhas vazias e cria a lista de cidades
        df = df.dropna(subset=[coluna_cidade])
        cidades = sorted(df[coluna_cidade].unique())
        
        cidade_selecionada = st.selectbox("Selecione o município:", options=cidades)

        if cidade_selecionada:
            # Filtra os dados da cidade escolhida
            dados = df[df[coluna_cidade] == cidade_selecionada].iloc[0]

            st.markdown("---")

            col1, col2 = st.columns(2)

            with col1:
                # --- POPULAÇÃO ---
                pop = dados.get('População', 0)
                # Garante que seja tratado como número para formatar com ponto
                try:
                    pop_val = int(str(pop).replace('.', '').split(',')[0]) if pd.notnull(pop) else 0
                except:
                    pop_val = 0
                st.metric(label="👥 População", value=f"{pop_val:,}".replace(',', '.'))
                
                # --- SHARE ---
                share = dados.get('%Share', 0)
                if isinstance(share, (float, int)):
                    share_txt = f"{share * 100:.2f}".replace('.', ',')
                else:
                    share_txt = str(share).replace('%', '').replace('.', ',')
                st.metric(label="📊 Share da Cidade", value=f"{share_txt}%")

            with col2:
                # --- LOJAS ATUAIS ---
                lojas = dados.get('Nº FSJ', 0)
                st.metric(label="🏠 Lojas Atuais (FSJ)", value=int(lojas) if pd.notnull(lojas) else 0)
                
                # --- PORTE ---
                porte = dados.get('Porte da cidade', 'N/A')
                st.metric(label="📍 Porte", value=porte)

            st.markdown("---")

            # --- RODAPÉ ---
            regiao = dados.get('REGIÃO GEOGRÁFICA IMEDIATA', 'Não informada')
            st.caption(f"Município: **{cidade_selecionada}** | Região: **{regiao}**")
    else:
        st.error(f"Coluna '{coluna_cidade}' não encontrada. Verifique os títulos na sua planilha.")
