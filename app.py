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
def exportar_pdf(dados_cidade, endereco, lat_lon, obs, fluxo, foto_arquivo):
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
    pdf.cell(200, 8, txt=f"Share: {formatar_br(dados_cidade.get('%Share', 0), 2)}%", ln=True)
    pdf.cell(200, 8, txt=f"Demanda: {formatar_br(dados_cidade.get('Demanda', 0), 2)}", ln=True)
    
    reg_imediata = str(dados_cidade.get('REGIÃO GEOGRÁFICA IMEDIATA', 'N/A')).encode('latin-1', 'ignore').decode('latin-1')
    pdf.cell(200, 8, txt=f"Regiao Imediata: {reg_imediata}", ln=True)
    pdf.ln(5)
    
    # 2. Dados do Ponto
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, txt="2. Dados do Ponto", ln=True)
    pdf.set_font("Arial", "", 10)
    
    txt_end = str(endereco).encode('latin-1', 'ignore').decode('latin-1')
    pdf.cell(200, 8, txt=f"Endereco: {txt_end}", ln=True)
    pdf.cell(200, 8, txt=f"GPS: {lat_lon}", ln=True)
    
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
        except:
            pdf.cell(200, 8, txt="Nao foi possivel processar a imagem.", ln=True)

    # 3. Observações e Avaliação
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, txt="3. Analise Tecnica", ln=True)
    pdf.set_font("Arial", "", 10)
    
    # Adicionando o Fluxo no PDF
    pdf.cell(200, 8, txt=f"Fluxo de pessoas: {fluxo}", ln=True)
    pdf.ln(2)
    
    txt_obs = str(obs).encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 8, txt=f"Observacoes: {txt_obs}")
    
    pdf.ln(10)
    data_hoje = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf.cell(200, 10, txt=f"Gerado em: {data_hoje}", ln=True, align='R')
    
    return pdf.output(dest='S').encode('latin-1', errors='replace')

# --- CARREGAMENTO DE DADOS ---
@st.cache_data
def load_data():
    try:
        file_path = 'Ranking PCA.xlsx'
        if not os.path.exists(file_path):
            return None
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
    # SEÇÃO 1
    st.subheader("1. Mercado da Cidade")
    cidades = sorted(df['Município'].unique())
    cidade_selecionada = st.selectbox("Selecione o município:", options=cidades)
    dados = df[df['Município'] == cidade_selecionada].iloc[0]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("👥 População", formatar_br(dados.get('População', 0), 0))
        st.metric("📊 Share", f"{formatar_br(dados.get('%Share', 0), 2)}%")
    with col2:
        st.metric("🏠 Lojas Atuais", formatar_br(dados.get('N° FSJ', 0), 0))
        st.metric("📈 Demanda", formatar_br(dados.get('Demanda', 0), 2))
    with col3:
        st.metric("💰 Renda Média", formatar_br(dados.get('Renda Média Domiciliar (SM)', 0), 2))
        st.metric("🏗️ Lojas Cabem", formatar_br(dados.get('Lojas Cabem', 0), 0))

    st.markdown("---")
    
    # SEÇÃO 2
    st.subheader("2. Mídia e Localização")
    endereco = st.text_input("📍 Link ou Endereço do Ponto:")
    foto = st.file_uploader("📸 Foto do Imóvel:", type=['jpg', 'jpeg', 'png'])
    if foto:
        st.image(foto, caption="Prévia", use_container_width=True)
    
    loc = get_geolocation()
    lat_lon_str = "Não capturado"
    if loc:
        lat_lon_str = f"{loc['coords']['latitude']}, {loc['coords']['longitude']}"
        st.success(f"📍 GPS Ativo: {lat_lon_str}")
    
    st.markdown("---")

    # SEÇÃO 3
    st.subheader("3. Dados do Ponto")
    observacoes = st.text_area("📝 Observações da Vistoria:", height=100)
    
    # --- NOVO CAMPO: FLUXO DE PESSOAS (SELECT SLIDER) ---
    st.write("---")
    st.markdown("**1° Fluxo de pessoas**")
    fluxo_pessoa = st.select_slider(
        "Arraste para selecionar a intensidade do fluxo:",
        options=["Baixo", "Médio", "Alto"],
        value="Médio"
    )

    st.markdown("---")
    if st.button("🚀 Preparar PDF"):
        try:
            pdf_bytes = exportar_pdf(dados, endereco, lat_lon_str, observacoes, fluxo_pessoa, foto)
            st.download_button(
                label="⬇️ Baixar Relatório PDF",
                data=pdf_bytes,
                file_name=f"Relatorio_{cidade_selecionada}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Erro ao gerar PDF: {e}")
