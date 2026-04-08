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
    
    # 2. Ponto e Foto
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, txt="2. Analise do Ponto", ln=True)
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

    # 3. Observações
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, txt="3. Observacoes", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 8, txt=obs)
    
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
        st.metric("👥 População", formatar_br(dados.get('População', 0), 0))
        st.metric("📊 Share", f"{formatar_br(dados.get('%Share', 0), 2)}%")
    with col2:
        st.metric("🏠 Lojas Atuais", formatar_br(dados.get('N° FSJ', 0), 0))
        st.metric("📈 Demanda", formatar_br(dados.get('Demanda', 0), 2))
    with col3:
        st.metric("💰 Renda Média", formatar_br(dados.get('Renda Média Domiciliar (SM)', 0), 2))
        st.metric("🏗️ Lojas Cabem", formatar_br(dados.get('Lojas Cabem', 0), 0))

    reg_imediata = dados.get('REGIÃO GEOGRÁFICA IMEDIATA', 'Não encontrada')
    reg_inter = dados.get('REGIÃO GEOGRÁFICA INTERMEDIÁRIA', 'Não encontrada')
    
    st.markdown(f"""
        <div style="font-size: 0.85rem; color: #9da5b1; margin-top: -10px; padding-bottom: 20px;">
            <strong>REGIÃO IMEDIATA:</strong> {reg_imediata} | 
            <strong>REGIÃO INTERMEDIÁRIA:</strong> {reg_inter}
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("2. Análise do Ponto")
    
    endereco = st.text_input("📍 Link ou Endereço do Ponto:")
    
    foto = st.file_uploader("📸 Foto do Imóvel (Câmera ou Galeria):", type=['jpg', 'jpeg', 'png'])
    if foto:
        st.image(foto, caption="Prévia da Foto Selecionada", use_container_width=True)
    
    # --- AJUSTE NAS COORDENADAS GPS ---
    loc = get_geolocation()
    lat_lon_str = "Não capturado"
    if loc:
        # Extrai apenas os números e separa por vírgula
        lat_lon_str = f"{loc['coords']['latitude']}, {loc['coords']['longitude']}"
        st.success(f"📍 GPS Ativo: {lat_lon_str}")
    
    observacoes = st.text_area("📝 Observações da Vistoria:")

    st.markdown("---")
    if st.button("🚀 Preparar PDF"):
        pdf_bytes = exportar_pdf(dados, endereco, lat_lon_str, observacoes, foto)
        st.download_button(
            label="⬇️ Baixar Relatório PDF",
            data=pdf_bytes,
            file_name=f"Relatorio_{cidade_selecionada}.pdf",
            mime="application/pdf"
        )
