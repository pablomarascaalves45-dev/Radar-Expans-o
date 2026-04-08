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
    .stSelectSlider label { font-size: 0.85rem !important; font-weight: bold; }
    .region-text { font-size: 0.8rem; color: #9da5b1; margin-top: -10px; }
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
def exportar_pdf(dados_cidade, endereco, lat_lon, obs, avaliacoes, concorrencia, polos, caracteristicas, foto_arquivo):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    
    pdf.cell(200, 10, txt="Relatorio de Expansao - Analise de Ponto", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, txt="1. Mercado da Cidade", ln=True)
    pdf.set_font("Arial", "", 10)
    municipio = str(dados_cidade.get('Município', 'N/A')).encode('latin-1', 'ignore').decode('latin-1')
    uf = str(dados_cidade.get('UF', 'N/A'))
    pdf.cell(200, 8, txt=f"Municipio: {municipio} - {uf}", ln=True)
    pdf.cell(200, 8, txt=f"Populacao: {formatar_br(dados_cidade.get('População', 0), 0)}", ln=True)
    
    reg_imediata = str(dados_cidade.get('REGIÃO GEOGRÁFICA IMEDIATA', 'N/A')).encode('latin-1', 'ignore').decode('latin-1')
    reg_interm = str(dados_cidade.get('REGIÃO GEOGRÁFICA INTERMEDIÁRIA', 'N/A')).encode('latin-1', 'ignore').decode('latin-1')
    pdf.cell(200, 8, txt=f"Regiao Imediata: {reg_imediata}", ln=True)
    pdf.cell(200, 8, txt=f"Regiao Intermediaria: {reg_interm}", ln=True)
    
    pdf.ln(5)
    
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

    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, txt="3. Analise de Campo", ln=True)
    
    secoes = [
        ("Atributos de Fluxo/Renda", avaliacoes),
        ("Caracteristicas do Ponto", caracteristicas),
        ("Concorrencia", concorrencia),
        ("Polos Geradores de Trafego", polos)
    ]

    for titulo, dados_dict in secoes:
        pdf.ln(2)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(200, 7, txt=f"{titulo}:", ln=True)
        pdf.set_font("Arial", "", 10)
        for chave, valor in dados_dict.items():
            pdf.cell(200, 7, txt=f"{chave}: {valor}", ln=True)

    pdf.ln(3)
    txt_obs = str(obs).encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 8, txt=f"Observacoes: {txt_obs}")
    
    return pdf.output(dest='S').encode('latin-1', errors='replace')

# --- CARREGAMENTO DE DADOS ---
@st.cache_data
def load_data():
    try:
