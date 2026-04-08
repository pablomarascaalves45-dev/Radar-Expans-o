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
    .score-box { 
        background-color: #1e2130; 
        padding: 20px; 
        border-radius: 10px; 
        border: 1px solid #3e4455;
        text-align: center;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÃO AUXILIAR DE FORMATAÇÃO ---
def formatar_br(valor, casas=2):
    try:
        if pd.isna(valor): return "0"
        return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return str(valor)

# --- FUNÇÃO PARA GERAR PDF (Adicionado Score no parâmetro) ---
def exportar_pdf(dados_cidade, endereco, lat_lon, obs, avaliacoes, concorrencia, polos, caracteristicas, foto_arquivo, score_total):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    
    pdf.cell(200, 10, txt="Relatorio de Expansao - Analise de Ponto", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, txt=f"SCORE TOTAL: {score_total} PTS", ln=True, align='C')
    pdf.ln(5)
    
    # ... (Restante do código do PDF permanece igual)
    # Adicionei apenas a chamada do Score no topo para o relatório
    
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
            pdf.image(img_path, w=80)
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
        col_cidade, col_uf = st.columns([4, 1])
        
        with col_cidade:
            cidade_selecionada = st.selectbox("Selecione o município:", options=cidades)
            dados = df[df['Município'] == cidade_selecionada].iloc[0]
            
        with col_uf:
            st.text_input("Estado:", value=dados.get('UF', ''), disabled=True)
        
        col1, col2, col3 = st.columns(3)
        # Extração de dados para o Score
        lojas_cabem = dados.get('Lojas Cabem', 0)
        share_original = dados.get('%Share', 0) # Assumindo que vem como 0.35 para 35%
        
        with col1:
            st.metric("👥 População", formatar_br(dados.get('População', 0), 0))
            st.metric("📊 Share", f"{formatar_br(share_original * 100, 2)}%")
        with col2:
            st.metric("🏠 Lojas Atuais", formatar_br(dados.get('N° FSJ', 0), 0))
            st.metric("📈 Demanda", formatar_br(dados.get('Demanda', 0), 2))
        with col3:
            st.metric("💰 Renda Média", formatar_br(dados.get('Renda Média Domiciliar (SM)', 0), 2))
            st.metric("🏗️ Lojas Cabem", formatar_br(lojas_cabem, 0))

    # --- LÓGICA DO SCORE DE MERCADO ---
    nota_mercado = 0
    condicao_lojas = lojas_cabem > 0
    condicao_share = share_original <= 0.30 # 30%

    if condicao_lojas and condicao_share:
        nota_mercado = 30
    elif condicao_lojas or condicao_share:
        nota_mercado = 15
    else:
        nota_mercado = 0

    st.markdown("---")
    
    # 2. LOCALIZAÇÃO E DADOS DO PONTO (Criação dos sliders igual ao original)
    st.subheader("2. Dados da Vistoria")
    # ... (Seu código de sliders aqui)
    col_a, col_b = st.columns(2)
    with col_a: f_pess = st.select_slider("Fluxo de pessoas", options=["Baixo", "Médio", "Alto"])
    with col_b: f_veic = st.select_slider("Fluxo de veículos", options=["Baixo", "Médio", "Alto"])
    
    # Exemplo de como você pode dar pesos para os sliders (ajuste conforme sua necessidade)
    mapa_pesos = {"Baixo": 0, "Médio": 5, "Alto": 10, "Não": 0, "Sim": 5, "Boa": 5, "Ruim": 0}
    
    # ... (Restante dos inputs: caracteristicas, concorrencia, polos)
    # [Para brevidade, assumindo que os outros sliders estão aqui conforme seu código original]
    
    # Sugestão: adicione aqui os outros blocos de UI (Características, Concorrência, Polos)
    # que você já tinha no seu script original.

    st.markdown("---")
    
    # CÁLCULO FINAL DO SCORE
    # Por enquanto somando apenas a Nota de Mercado. Você pode adicionar as outras aqui.
    score_total = nota_mercado 
    
    st.markdown(f"""
        <div class='score-box'>
            <span style='color: #9da5b1; font-size: 1rem;'>SCORE PRELIMINAR DO PONTO</span><br>
            <span style='color: #ffffff; font-size: 2.5rem; font-weight: bold;'>{score_total}</span>
            <span style='color: #ffffff; font-size: 1.2rem;'> pts</span>
        </div>
    """, unsafe_allow_html=True)

    if st.button("🚀 Preparar PDF"):
        try:
            # Capturando todos os dados dos dicionários (ajuste conforme os sliders que você definir)
            avaliacoes = {"Fluxo Pessoas": f_pess, "Fluxo Veículos": f_veic} # etc...
            dados_concorrencia = {} # Preencha com os valores dos sliders
            dados_polos = {} # Preencha com os valores dos sliders
            dados_caract = {} # Preencha com os valores dos sliders
            
            pdf_bytes = exportar_pdf(dados, "Endereço Exemplo", "0,0", "Obs", avaliacoes, {}, {}, {}, None, score_total)
            st.download_button(label="⬇️ Baixar Relatório PDF", data=pdf_bytes, file_name=f"Relatorio_{cidade_selecionada}.pdf", mime="application/pdf")
        except Exception as e:
            st.error(f"Erro ao gerar PDF: {e}")
