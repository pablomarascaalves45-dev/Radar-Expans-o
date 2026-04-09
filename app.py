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
    .score-container {
        background-color: #1e2130;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #4a5568;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-score-text {
        font-size: 1.1rem;
        color: #9da5b1;
        margin: 5px 0;
    }
    .total-score-text {
        font-size: 3.5rem;
        font-weight: bold;
        margin-top: -10px;
    }
    .classificacao-text {
        font-size: 1.4rem;
        font-weight: bold;
        margin-top: 10px;
        text-transform: uppercase;
    }
    .recomendacao-text {
        font-size: 0.95rem;
        color: #bdc3c7;
        margin-bottom: 15px;
        font-style: italic;
        line-height: 1.2;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES AUXILIARES ---
def formatar_br(valor, casas=2):
    try:
        if pd.isna(valor): return "0"
        return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except: return str(valor)

def exportar_pdf(dados_cidade, endereco, lat_lon, obs, avaliacoes, concorrencia, polos, caracteristicas, foto_arquivo, perc_final, score_mercado, score_ponto):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(10, 10, 10)
    pdf.set_auto_page_break(False)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 6, txt="Relatorio de Expansao - Analise de Ponto", ln=True, align='C')
    
    pdf.set_fill_color(30, 33, 48)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 8, txt=f"ADERENCIA TOTAL: {perc_final}", ln=True, align='C', fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    # 1. DADOS DO MERCADO
    pdf.set_font("Arial", "B", 9)
    pdf.cell(0, 5, txt="1. DADOS DO MERCADO", ln=True)
    pdf.set_font("Arial", "", 8)
    municipio = str(dados_cidade.get('Município', 'N/A')).encode('latin-1', 'ignore').decode('latin-1')
    pdf.cell(0, 5, txt=f"Cidade: {municipio} - {dados_cidade.get('UF', '')}", ln=True)
    
    pdf.set_font("Arial", "B", 8)
    col_w = 63
    pdf.cell(col_w, 5, txt=f"Populacao: {formatar_br(dados_cidade.get('População', 0), 0)}", ln=0)
    pdf.cell(col_w, 5, txt=f"Lojas Atuais: {formatar_br(dados_cidade.get('N° FSJ', 0), 0)}", ln=0)
    pdf.cell(col_w, 5, txt=f"Renda Media: {formatar_br(dados_cidade.get('Renda Média Domiciliar (SM)', 0), 2)}", ln=1)
    pdf.cell(col_w, 5, txt=f"Share: {formatar_br(dados_cidade.get('%Share', 0) * 100, 2)}%", ln=0)
    pdf.cell(col_w, 5, txt=f"Demanda: {formatar_br(dados_cidade.get('Demanda', 0), 2)}", ln=0)
    pdf.cell(col_w, 5, txt=f"Lojas Cabem: {formatar_br(dados_cidade.get('Lojas Cabem', 0), 0)}", ln=1)
    pdf.ln(2)

    # 2. LOCALIZACAO
    pdf.set_font("Arial", "B", 9)
    pdf.cell(0, 5, txt="2. LOCALIZACAO", ln=True)
    pdf.set_font("Arial", "", 8)
    pdf.multi_cell(0, 4, txt=f"Endereco: {str(endereco).encode('latin-1', 'ignore').decode('latin-1')}")
    pdf.cell(0, 4, txt=f"Coordenadas GPS: {lat_lon}", ln=True)
    pdf.ln(2)

    # 3. ANALISE TECNICA
    pdf.set_font("Arial", "B", 9)
    pdf.cell(0, 5, txt="3. ANALISE TECNICA DO PONTO", ln=True)
    y_antes = pdf.get_y()
    pdf.set_font("Arial", "B", 7)
    pdf.cell(95, 4, txt="FLUXOS E CONCORRENCIA", ln=True)
    pdf.set_font("Arial", "", 7)
    for k, v in avaliacoes.items():
        pdf.cell(95, 3.5, txt=f"- {k}: {v}", ln=True)
    for k, v in concorrencia.items():
        pdf.cell(95, 3.5, txt=f"- {k}: {v}", ln=True)
    
    pdf.set_y(y_antes)
    pdf.set_x(105)
    pdf.set_font("Arial", "B", 7)
    pdf.cell(95, 4, txt="CARACTERISTICAS E POLOS", ln=True)
    pdf.set_font("Arial", "", 7)
    for k, v in caracteristicas.items():
        pdf.set_x(105)
        pdf.cell(95, 3.5, txt=f"- {k}: {v}", ln=True)
    
    polos_str = ", ".join([k for k, v in polos.items() if v == "Sim" or v is True])
    pdf.set_x(105)
    pdf.multi_cell(95, 3.5, txt=f"- Polos: {polos_str if polos_str else 'Nenhum'}")
    
    pdf.ln(2)
    pdf.set_font("Arial", "B", 8)
    pdf.cell(0, 4, txt="OBSERVACOES DA VISTORIA:", ln=True)
    pdf.set_font("Arial", "", 7)
    pdf.multi_cell(0, 3.5, txt=str(obs).encode('latin-1', 'ignore').decode('latin-1'))

    if foto_arquivo:
        try:
            img = Image.open(foto_arquivo)
            if img.mode in ("RGBA", "P"): img = img.convert("RGB")
            w_orig, h_orig = img.size
            aspect_ratio = w_orig / h_orig
            y_atual = pdf.get_y()
            altura_disponivel = 297 - y_atual - 15
            largura_disponivel = 190
            nova_w = largura_disponivel
            nova_h = nova_w / aspect_ratio
            if nova_h > altura_disponivel:
                nova_h = altura_disponivel
                nova_w = nova_h * aspect_ratio
            x_cent = (210 - nova_w) / 2
            img_path = "temp_pdf_foto.jpg"
            img.save(img_path, quality=90)
            pdf.image(img_path, x=x_cent, y=y_atual + 5, w=nova_w, h=nova_h)
            os.remove(img_path)
        except: pass

    return pdf.output(dest='S').encode('latin-1', errors='replace')

# --- CARREGAMENTO DE DADOS ---
@st.cache_data
def load_data():
    try:
        file_path = 'Ranking PCA.xlsx'
        if not os.path.exists(file_path): return None
        df_raw = pd.read_excel(file_path, header=None)
        header_idx = 0
