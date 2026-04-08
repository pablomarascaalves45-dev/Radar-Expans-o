import streamlit as st
import pandas as pd
from fpdf import FPDF
from streamlit_js_eval import get_geolocation
import datetime

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

# --- FUNÇÃO PARA GERAR PDF ---
def exportar_pdf(dados_cidade, endereco, lat_lon, obs):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    
    # Título
    pdf.cell(200, 10, txt="Relatório de Expansão - Análise de Ponto", ln=True, align='C')
    pdf.ln(10)
    
    # Dados da Cidade
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, txt="1. Mercado da Cidade", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(200, 8, txt=f"Município: {dados_cidade['Município']}", ln=True)
    pdf.cell(200, 8, txt=f"População: {dados_cidade['População']}", ln=True)
    pdf.cell(200, 8, txt=f"Share: {dados_cidade.get('%Share', 'N/A')}", ln=True)
    pdf.cell(200, 8, txt=f"Demanda: {dados_cidade.get('Demanda', 'N/A')}", ln=True)
    pdf.ln(5)
    
    # Dados do Ponto
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, txt="2. Análise do Ponto", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(200, 8, txt=f"Endereço/Link: {endereco}", ln=True)
    pdf.cell(200, 8, txt=f"Coordenadas GPS: {lat_lon}", ln=True)
    pdf.ln(5)
    
    # Observações
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, txt="3. Observações", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 8, txt=obs)
    
    # Rodapé
    pdf.ln(10)
    data_hoje = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf.cell(200, 10, txt=f"Gerado em: {data_hoje}", ln=True, align='R')
    
    return pdf.output(dest='S').encode('latin-1')

# --- CARREGAMENTO DE DADOS ---
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
    except:
        return None

df = load_data()

# =========================================================
# INTERFACE
# =========================================================
st.title("🎯 Radar de Expansão")

if df is not None:
    st.subheader("1. Mercado da Cidade")
    cidades = sorted(df['Município'].unique())
    cidade_selecionada = st.selectbox("Selecione o município:", options=cidades)
    
    dados = df[df['Município'] == cidade_selecionada].iloc[0]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("👥 População", str(dados.get('População', 0)))
        st.metric("📊 Share", f"{dados.get('%Share', 0)}%")
    with col2:
        st.metric("🏠 Lojas Atuais", str(dados.get('N° FSJ', 0)))
        st.metric("📈 Demanda", str(dados.get('Demanda', 0)))
    with col3:
        st.metric("💰 Renda Média", str(dados.get('Renda Média Domiciliar (SM)', 0)))
        st.metric("🏗️ Lojas Cabem", str(dados.get('Lojas Cabem', 0)))

    st.markdown("---")
    st.subheader("2. Análise do Ponto")
    
    endereco = st.text_input("📍 Link ou Endereço do Ponto:")
    
    loc = get_geolocation()
    lat_lon_str = "Não capturado"
    if loc:
        lat_lon_str = f"Lat: {loc['coords']['latitude']}, Lon: {loc['coords']['longitude']}"
        st.success(f"📍 GPS Ativo: {lat_lon_str}")
    
    observacoes = st.text_area("📝 Observações da Vistoria:")

    # --- BOTÃO PDF ---
    st.markdown("---")
    if st.button("🚀 Preparar PDF"):
        pdf_bytes = exportar_pdf(dados, endereco, lat_lon_str, observacoes)
        
        st.download_button(
            label="⬇️ Baixar Relatório PDF",
            data=pdf_bytes,
            file_name=f"Relatorio_{cidade_selecionada}.pdf",
            mime="application/pdf"
        )
