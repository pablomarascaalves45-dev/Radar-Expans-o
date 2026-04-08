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
def exportar_pdf(dados_cidade, endereco, lat_lon, obs, avaliacoes, concorrencia, foto_arquivo):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    
    pdf.cell(200, 10, txt="Relatorio de Expansao - Analise de Ponto", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, txt="1. Mercado da Cidade", ln=True)
    pdf.set_font("Arial", "", 10)
    municipio = str(dados_cidade.get('Município', 'N/A')).encode('latin-1', 'ignore').decode('latin-1')
    pdf.cell(200, 8, txt=f"Municipio: {municipio}", ln=True)
    pdf.cell(200, 8, txt=f"Populacao: {formatar_br(dados_cidade.get('População', 0), 0)}", ln=True)
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
    pdf.set_font("Arial", "", 10)
    
    # Seção Dados do Ponto
    for chave, valor in avaliacoes.items():
        pdf.cell(200, 7, txt=f"{chave}: {valor}", ln=True)
    
    pdf.ln(2)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(200, 7, txt="Concorrencia:", ln=True)
    pdf.set_font("Arial", "", 10)
    # Seção Concorrência
    for chave, valor in concorrencia.items():
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
        if not os.path.exists(file_path):
            st.error("Arquivo 'Ranking PCA.xlsx' não encontrado!")
            return None
        
        df_raw = pd.read_excel(file_path, header=None)
        header_idx = 0
        for i, row in df_raw.iterrows():
            if "Município" in [str(val).strip() for val in row.values]:
                header_idx = i
                break
        
        df = pd.read_excel(file_path, skiprows=header_idx)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Erro ao carregar Excel: {e}")
        return None

df = load_data()

# =========================================================
# INTERFACE
# =========================================================
st.title("🎯 Radar de Expansão")

if df is not None:
    # 1. MERCADO
    st.subheader("1. Mercado da Cidade")
    if 'Município' in df.columns:
        cidades = sorted(df['Município'].dropna().unique())
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
    else:
        st.error("A coluna 'Município' não foi detectada. Verifique o cabeçalho do Excel.")

    st.markdown("---")
    
    # 2. LOCALIZAÇÃO
    st.subheader("2. Mídia e Localização")
    endereco = st.text_input("📍 Link ou Endereço do Ponto:")
    foto = st.file_uploader("📸 Foto do Imóvel:", type=['jpg', 'jpeg', 'png'])
    if foto: st.image(foto, use_container_width=True)
    
    loc = get_geolocation()
    lat_lon_str = f"{loc['coords']['latitude']}, {loc['coords']['longitude']}" if loc else "Não capturado"

    st.markdown("---")

    # 3. DADOS DO PONTO
    st.subheader("3. Dados do Ponto")

    col_a, col_b = st.columns(2)
    col_c, col_d = st.columns(2)

    with col_a:
        f_pess = st.select_slider("Fluxo de pessoas", options=["Baixo", "Médio", "Alto"], value="Médio")
    with col_b:
        f_veic = st.select_slider("Fluxo de veículos", options=["Baixo", "Médio", "Alto"], value="Médio")
    with col_c:
        c_rend = st.select_slider("Classificação de renda", options=["Baixa", "Média", "Alta"], value="Média")
    with col_d:
        c_popu = st.select_slider("Concentração populacional", options=["Baixo", "Médio", "Alto"], value="Médio")

    # --- NOVA SEÇÃO: CONCORRÊNCIA ---
    st.write("")
    st.markdown("### Concorrência")
    
    col_e, col_f = st.columns(2)
    col_g, _ = st.columns(2) # Usando _ para manter o alinhamento das colunas

    with col_e:
        conc_redes = st.select_slider("Redes", options=["Baixo", "Médio", "Alto"], value="Médio")
    with col_f:
        conc_indep = st.select_slider("Independentes", options=["Baixo", "Médio", "Alto"], value="Médio")
    with col_g:
        conc_canib = st.select_slider("Canibalização", options=["Baixo", "Médio", "Alto"], value="Médio")

    st.write("") 
    observacoes = st.text_area("📝 Observações da Vistoria:", height=100)

    # Dicionários de dados para o PDF
    avaliacoes = {
        "Fluxo de Pessoas": f_pess,
        "Fluxo de Veículos": f_veic,
        "Classificação de Renda": c_rend,
        "Concentração Populacional": c_popu
    }
    
    dados_concorrencia = {
        "Redes": conc_redes,
        "Independentes": conc_indep,
        "Canibalizacao": conc_canib
    }

    st.markdown("---")
    if st.button("🚀 Preparar PDF"):
        try:
            pdf_bytes = exportar_pdf(dados, endereco, lat_lon_str, observacoes, avaliacoes, dados_concorrencia, foto)
            st.download_button(
                label="⬇️ Baixar Relatório PDF",
                data=pdf_bytes,
                file_name=f"Relatorio_{cidade_selecionada}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Erro ao gerar PDF: {e}")
