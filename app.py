import streamlit as st
import pandas as pd

# 1. Configuração da página
st.set_page_config(page_title="Radar de Expansão", layout="centered")

# 2. Estilização personalizada
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; color: #ffffff !important; }
    [data-testid="stMetricLabel"] { font-size: 0.9rem !important; color: #9da5b1 !important; }
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
        
        header_row = 0
        for i, row in df_raw.iterrows():
            if "Município" in [str(val).strip() for val in row.values]:
                header_row = i
                break
        
        df = pd.read_excel(file_path, skiprows=header_row)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Erro ao carregar Excel: {e}")
        return None

df = load_data()

if df is not None:
    cidades = sorted(df['Município'].unique())
    cidade_selecionada = st.selectbox("Selecione o município:", options=cidades)

    if cidade_selecionada:
        dados = df[df['Município'] == cidade_selecionada].iloc[0]

        st.markdown("---")
        
        # Ajustado para 3 colunas para acomodar as novas métricas
        col1, col2, col3 = st.columns(3)

        with col1:
            # --- POPULAÇÃO ---
            pop_val = dados.get('População', 0)
            if isinstance(pop_val, str):
                pop_val = int(pop_val.replace('.', '').replace(',', ''))
            st.metric(label="👥 População", value=f"{int(pop_val):,}".replace(',', '.'))
            
            # --- SHARE ---
            share_val = dados.get('%Share', 0)
            if isinstance(share_val, (float, int)):
                val = share_val * 100 if share_val < 1 else share_val
                share_txt = f"{val:.2f}".replace('.', ',')
            else:
                share_txt = str(share_val).replace('%', '').strip().replace('.', ',')
            st.metric(label="📊 Share da Cidade", value=f"{share_txt}%")

        with col2:
            # --- LOJAS ATUAIS ---
            lojas = dados.get('N° FSJ', 0)
            st.metric(label="🏠 Lojas Atuais (FSJ)", value=int(lojas) if pd.notnull(lojas) else 0)
            
            # --- DEMANDA ---
            demanda = dados.get('Demanda', 'N/A')
            if isinstance(demanda, (int, float)):
                demanda_display = f"{int(demanda):,}".replace(',', '.')
            else:
                demanda_display = demanda
            st.metric(label="📈 Demanda", value=demanda_display)

        with col3:
            # --- RENDA MÉDIA DOMICILIAR ---
            # O nome da coluna deve ser exato ao do Excel
            renda = dados.get('Renda Média Domiciliar (SM)', 0)
            if isinstance(renda, (int, float)):
                renda_txt = f"{renda:.2f}".replace('.', ',')
            else:
                renda_txt = str(renda).replace('.', ',')
            st.metric(label="💰 Renda Média (SM)", value=renda_txt)

            # --- LOJAS CABEM ---
            cabem = dados.get('Lojas Cabem', 0)
            st.metric(label="🏗️ Lojas Cabem", value=int(cabem) if pd.notnull(cabem) else 0)

        st.markdown("---")
        
        # --- RODAPÉ ---
        reg_imediata = dados.get('REGIÃO GEOGRÁFICA IMEDIATA', 'N/A')
        reg_intermediaria = dados.get('REGIÃO GEOGRÁFICA INTERMEDIÁRIA', 'N/A')
        
        st.caption(f"**Região Imediata:** {reg_imediata} | **Região Intermediária:** {reg_intermediaria}")
