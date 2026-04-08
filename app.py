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
def exportar_pdf(dados_cidade, endereco, lat_lon, obs, foto_arquivo):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    
    pdf.cell(200, 10, txt="Relatorio de Expansao - Analise de Ponto", ln=True, align='C')
    pdf.ln(10)
    
    # 1. Mercado
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, txt="1. Mercado da Cidade", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(200, 8, txt=f"Municipio: {dados_cidade['Município']}", ln=True)
    pdf.cell(200, 8, txt=f"Populacao: {formatar_br(dados_cidade.get('População', 0), 0)}", ln=True)
    pdf.cell(200, 8, txt=f"Share: {formatar_br(dados_cidade.get('%Share', 0), 2)}%", ln=True)
    pdf.cell(200, 8, txt=f"Demanda: {formatar_br(dados_cidade.get('Demanda', 0), 2)}", ln=True)
    
    reg_imediata = dados_cidade.get('REGIÃO GEOGRÁFICA IMEDIATA', 'N/A')
    reg_inter = dados_cidade.get('REGIÃO GEOGRÁFICA INTERMEDIÁRIA', 'N/A')
    pdf.cell(200, 8, txt=f"Regiao Imediata: {reg_imediata}", ln=True)
    pdf.cell(200, 8, txt=f"Regiao Intermediaria: {reg_inter}", ln=True)
    pdf.ln(5)
    
    # 2. Dados do Ponto
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, txt="2. Dados do Ponto", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(200, 8, txt=f"Endereco/Link: {endereco}", ln=True)
    pdf.cell(200, 8, txt=f"Coordenadas GPS: {lat_lon}", ln=True)
    
    if foto_arquivo:
        try:
            img = Image.open(foto_arquivo)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            img_path = "temp_foto.jpg"
            img.save(img_path)
            pdf.ln(5)
            pdf.image(img_path, w=100)
            pdf.ln(5)
            if os.path.exists(img_path): os.remove(img_path)
        except Exception as e:
            pdf.cell(200, 8, txt=f"Erro ao carregar imagem: {e}", ln=True)

    # 3. Observações da Vistoria
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(
