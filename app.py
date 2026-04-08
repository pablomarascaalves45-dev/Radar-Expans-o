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
        file_path = 'Ranking PCA.xlsx'
        df_raw = pd.read_excel(file_path, header=None)
        
        # Procura a linha do cabeçalho
        header_row = 0
        for i, row in df_raw.iterrows():
            if "Município" in [str(val).strip() for val in row.values]:
                header_row = i
                break
        
        df = pd.read_excel(file_path, skiprows=header_row)
        df.columns = [str(c).strip() for c in df.columns]
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        df = df.dropna(subset=['Município'])
        
        return df
    except Exception as e:
        st.error(f"Erro ao processar a planilha: {e}")
        return None

df = load_data()

if df is not None:
    cidades = sorted(df['Município'].unique())
    cidade_selecionada = st.selectbox("Selecione o município:", options=cidades)

    if cidade_selecionada:
        # Puxa os dados da cidade
        dados = df[df['Município'] == cidade_selecionada].iloc[0]

        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            # --- POPULAÇÃO ---
            # Tenta encontrar 'População' ou 'Populacao'
            col_pop = 'População' if 'População' in df.columns else 'Populacao'
            pop_val_raw = dados.get(col_pop, 0)
            
            # Limpeza de números que venham como texto "1.234"
            if isinstance(pop_val_raw, str):
                pop_val = int(pop_val_raw.replace('.', '').replace(',', ''))
            else:
                pop_val = int(pop_val_raw)
            
            st.metric(label="👥 População", value=f"{pop_val:,}".replace(',', '.'))
            
            # --- SHARE ---
            # Tenta encontrar '%Share', '% Share' ou 'Share'
            col_share = next((c for c in df.columns if 'Share' in c), None)
            share_val = dados.get(col_share, 0) if col_share else 0
            
            if isinstance(share_val, (float, int)):
                # Se for decimal (0.05), transforma em (5,00)
                share_num = share_val * 100 if share_val < 1 else share_val
                share_txt = f"{share_num:.2f}".replace('.', ',')
            else:
                share_txt = str(share_val).replace('%', '').strip().replace('.', ',')
            
            st.metric(label="📊 Share da Cidade", value=f"{share_txt}%")

        with col2:
            # --- LOJAS ATUAIS ---
            col_fsj = 'Nº FSJ' if 'Nº FSJ' in df.columns else 'FSJ'
            lojas_val = int(dados.get(col_fsj, 0))
            st.metric(label="🏠 Lojas Atuais (FSJ)", value=lojas_val)
            
            # --- PORTE ---
            porte = dados.get('Porte da cidade', 'N/A')
            st.metric(label="📍 Porte", value=porte)

        st.markdown("---")
        reg_col = 'REGIÃO GEOGRÁFICA IMEDIATA' if 'REGIÃO GEOGRÁFICA IMEDIATA' in df.columns else 'Região'
        regiao = dados.get(reg_col, 'Não informada')
        st.caption(f"Município: **{cidade_selecionada}** | Região: **{regiao}**")
