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
        # Carrega o arquivo sem pular linhas inicialmente para encontrar o cabeçalho
        file_path = 'Ranking PCA.xlsx'
        df_raw = pd.read_excel(file_path, header=None)
        
        # Procura a linha que contém a palavra "Município"
        header_row = 0
        for i, row in df_raw.iterrows():
            if "Município" in row.values:
                header_row = i
                break
        
        # Recarrega o dataframe usando a linha correta como cabeçalho
        df = pd.read_excel(file_path, skiprows=header_row)
        
        # Limpa nomes de colunas (remove espaços e garante que sejam strings)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Remove colunas e linhas totalmente vazias
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        df = df.dropna(subset=['Município'])
        
        return df
    except Exception as e:
        st.error(f"Erro ao processar a planilha: {e}")
        return None

df = load_data()

if df is not None:
    coluna_cidade = 'Município'
    
    # Lista de cidades
    cidades = sorted(df[coluna_cidade].unique())
    
    cidade_selecionada = st.selectbox("Selecione o município:", options=cidades)

    if cidade_selecionada:
        dados = df[df[coluna_cidade] == cidade_selecionada].iloc[0]

        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            # População
            pop = dados.get('População', 0)
            try:
                # Remove pontos de milhar se existirem e converte para número
                pop_val = int(str(pop).replace('.', '').split(',')[0])
            except:
                pop_val = 0
            st.metric(label="👥 População", value=f"{pop_val:,}".replace(',', '.'))
            
            # %Share
            share = dados.get('%Share', 0)
            if isinstance(share, (float, int)):
                share_txt = f"{share * 100:.2f}".replace('.', ',')
            else:
                share_txt = str(share).replace('%', '').replace('.', ',')
            st.metric(label="📊 Share da Cidade", value=f"{share_txt}%")

        with col2:
            # Lojas Atuais
            lojas = dados.get('Nº FSJ', 0)
            try:
                lojas_val = int(lojas)
            except:
                lojas_val = 0
            st.metric(label="🏠 Lojas Atuais (FSJ)", value=lojas_val)
            
            # Porte
            porte = dados.get('Porte da cidade', 'N/A')
            st.metric(label="📍 Porte", value=porte)

        st.markdown("---")
        # Rodapé
        regiao = dados.get('REGIÃO GEOGRÁFICA IMEDIATA', 'Não informada')
        st.caption(f"Município: **{cidade_selecionada}** | Região: **{regiao}**")
else:
    st.info("Carregando base de dados...")
