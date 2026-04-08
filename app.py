import streamlit as st
import pandas as pd
from streamlit_js_eval import get_geolocation # Necessário adicionar streamlit-js-eval no requirements.txt

# 1. Configuração da página
st.set_page_config(page_title="Radar de Expansão", layout="centered")

# 2. Estilização personalizada
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; color: #ffffff !important; }
    [data-testid="stMetricLabel"] { font-size: 0.9rem !important; color: #9da5b1 !important; }
    .section-title { color: #ff4b4b; font-weight: bold; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÃO DE CARREGAMENTO ---
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

# =========================================================
# SEÇÃO 1: MERCADO DA CIDADE
# =========================================================
st.title("🎯 Radar de Expansão")
st.subheader("1. Mercado da Cidade")

if df is not None:
    cidades = sorted(df['Município'].unique())
    cidade_selecionada = st.selectbox("Selecione o município para análise:", options=cidades)

    if cidade_selecionada:
        dados = df[df['Município'] == cidade_selecionada].iloc[0]
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            pop_val = dados.get('População', 0)
            if isinstance(pop_val, str): pop_val = int(pop_val.replace('.', '').replace(',', ''))
            st.metric(label="👥 População", value=f"{int(pop_val):,}".replace(',', '.'))
            
            share_val = dados.get('%Share', 0)
            if isinstance(share_val, (float, int)):
                val = share_val * 100 if share_val < 1 else share_val
                share_txt = f"{val:.2f}".replace('.', ',')
            else:
                share_txt = str(share_val).replace('%', '').strip().replace('.', ',')
            st.metric(label="📊 Share da Cidade", value=f"{share_txt}%")

        with col2:
            lojas = dados.get('N° FSJ', 0)
            st.metric(label="🏠 Lojas Atuais (FSJ)", value=int(lojas) if pd.notnull(lojas) else 0)
            
            demanda = dados.get('Demanda', 'N/A')
            if isinstance(demanda, (int, float)): demanda_display = f"{int(demanda):,}".replace(',', '.')
            else: demanda_display = demanda
            st.metric(label="📈 Demanda", value=demanda_display)

        with col3:
            renda = dados.get('Renda Média Domiciliar (SM)', 0)
            renda_txt = f"{renda:.2f}".replace('.', ',') if isinstance(renda, (int, float)) else str(renda)
            st.metric(label="💰 Renda Média (SM)", value=renda_txt)

            cabem = dados.get('Lojas Cabem', 0)
            st.metric(label="🏗️ Lojas Cabem", value=int(cabem) if pd.notnull(cabem) else 0)

        reg_imediata = dados.get('REGIÃO GEOGRÁFICA IMEDIATA', 'N/A')
        reg_intermediaria = dados.get('REGIÃO GEOGRÁFICA INTERMEDIÁRIA', 'N/A')
        st.caption(f"**Região Imediata:** {reg_imediata} | **Região Intermediária:** {reg_intermediaria}")

# =========================================================
# SEÇÃO 2: ANÁLISE DO PONTO
# =========================================================
st.markdown("---")
st.subheader("2. Análise do Ponto")

# Opção 1: Colar link do Maps
endereco_maps = st.text_input("📍 Cole o link do Google Maps ou Endereço:", placeholder="https://www.google.com/maps/...")

# Opção 2: Pegar localização atual
st.write("Ou use sua localização atual (GPS):")
loc = get_geolocation()

if loc:
    lat = loc['coords']['latitude']
    lon = loc['coords']['longitude']
    st.success(f"Localização capturada: Lat {lat:.5f}, Lon {lon:.5f}")
    
    # Botão para abrir no Maps com a localização capturada
    maps_url = f"https://www.google.com/maps?q={lat},{lon}"
    st.markdown(f"[📍 Abrir no Google Maps]({maps_url})")
else:
    st.info("Clique no botão que aparecerá no navegador para permitir o acesso à localização.")

# Espaço para observações do ponto
obs = st.text_area("📝 Observações sobre o Ponto Comercial:", placeholder="Ex: Próximo a supermercado, fluxo alto de pedestres...")
