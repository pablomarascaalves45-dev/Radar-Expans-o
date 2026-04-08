import streamlit as st
import pandas as pd
from fpdf import FPDF
from streamlit_js_eval import get_geolocation
import datetime
from PIL import Image
import io
import os

# 1. Configuração da página
st.set_page_config(page_title="Radar de Expansão", layout="centered")

# 2. Estilização personalizada
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; color: #ffffff !important; }
    [data-testid="stMetricLabel"] { font-size: 0.9rem !important; color: #9da5b1 !important; }
    /* Ajuste para diminuir o espaço entre labels do slider */
    .stSelectSlider label { font-size: 0.8rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÃO AUXILIAR DE FORMATAÇÃO ---
def formatar_br(valor, casas=2):
    try:
        if pd.isna(valor): return "0"
        return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return str(valor)

# --- FUNÇÃO PARA GERAR PDF ---
def exportar_pdf(dados_cidade, endereco, lat_lon, obs, avaliacoes, foto_arquivo):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    
    pdf.cell(200, 10, txt="Relatorio de Expansao - Analise de Ponto", ln=True, align='C')
    pdf.ln(10)
    
    # 1. Mercado
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, txt="1. Mercado da Cidade", ln=True)
    pdf.set_font("Arial", "", 10)
    municipio = str(dados_cidade['Município']).encode('latin-1', 'ignore').decode('latin-1')
    pdf.cell(200, 8, txt=f"Municipio: {municipio}", ln=True)
    pdf.cell(200, 8, txt=f"Populacao: {formatar_br(dados_cidade.get('População', 0), 0)}", ln=True)
    pdf.ln(5)
    
    # 2. Dados do Ponto
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, txt="2. Dados do Ponto", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(200, 8, txt=f"Endereco: {str(endereco).encode('latin-1', 'ignore').decode('latin-1')}", ln=True)
    pdf.cell(200, 8, txt=f"GPS: {lat_lon}", ln=True)
    
    if foto_arquivo:
        try:
            img = Image.open(foto_arquivo)
            if img.mode in ("RGBA", "P"): img = img.convert("RGB")
            img_path = "temp_foto.jpg"
            img.save(img_path)
            pdf.ln(5)
            pdf.image(img_path, w=80)
            pdf.ln(5)
            if os.path.exists(img_path): os.remove(img_path)
        except: pass

    # 3. Análise do Consultor
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, txt="3. Analise de Campo", ln=True)
    pdf.set_font("Arial", "", 10)
    
    # Adicionando as 4 métricas de fluxo/renda
    for chave, valor in avaliacoes.items():
        pdf.cell(200, 7, txt=f"{chave}: {valor}", ln=True)
    
    pdf.ln(3)
    txt_obs = str(obs).encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 8, txt=f"Observacoes: {txt_obs}")
    
    return pdf.output(dest='S').encode('latin-1', errors='replace')

# --- CARREGAMENTO DE DADOS ---
@st.cache_data
def load_data():
    try:
        file_path = 'Ranking PCA.xlsx'
        df = pd.read_excel(file_path, skiprows=1) # Ajuste simples para o cabeçalho
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except: return None

df = load_data()

# =========================================================
# INTERFACE
# =========================================================
st.title("🎯 Radar de Expansão")

if df is not None:
    # SEÇÃO 1 e 2 omitidas para brevidade, mantendo lógica anterior...
    cidades = sorted(df['Município'].unique())
    cidade_selecionada = st.selectbox("Selecione o município:", options=cidades)
    dados = df[df['Município'] == cidade_selecionada].iloc[0]
    
    # (Campos de Endereço e Foto aqui...)
    endereco = st.text_input("📍 Link ou Endereço do Ponto:")
    foto = st.file_uploader("📸 Foto do Imóvel:", type=['jpg', 'jpeg', 'png'])
    
    loc = get_geolocation()
    lat_lon_str = f"{loc['coords']['latitude']}, {loc['coords']['longitude']}" if loc else "Não capturado"

    st.markdown("---")

    # SEÇÃO 3 - DADOS DO PONTO (ORDEM AJUSTADA)
    st.subheader("3. Dados do Ponto")

    # Layout em Colunas para as Perguntas (Pequeno e Lado a Lado)
    col_a, col_b = st.columns(2)
    col_c, col_d = st.columns(2)

    with col_a:
        f_pess = st.select_slider("1° Fluxo de pessoas", options=["Baixo", "Médio", "Alto"], value="Médio")
    with col_b:
        f_veic = st.select_slider("2° Fluxo de veículos", options=["Baixo", "Médio", "Alto"], value="Médio")
    with col_c:
        c_rend = st.select_slider("3° Classe de renda", options=["Baixa", "Média", "Alta"], value="Média")
    with col_d:
        c_popu = st.select_slider("4° Conc. populacional", options=["Baixo", "Médio", "Alto"], value="Médio")

    st.write("") # Espaçador
    observacoes = st.text_area("📝 Observações da Vistoria:", height=100)

    # Dicionário para enviar ao PDF
    avaliacoes = {
        "Fluxo de Pessoas": f_pess,
        "Fluxo de Veículos": f_veic,
        "Classificação de Renda": c_rend,
        "Concentração Populacional": c_popu
    }

    if st.button("🚀 Preparar PDF"):
        pdf_bytes = exportar_pdf(dados, endereco, lat_lon_str, observacoes, avaliacoes, foto)
        st.download_button(label="⬇️ Baixar PDF", data=pdf_bytes, file_name=f"Analise_{cidade_selecionada}.pdf")
