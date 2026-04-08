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
    pdf.cell(200, 8, txt=f"Municipio: {municipio}", ln=True)
    pdf.cell(200, 8, txt=f"Populacao: {formatar_br(dados_cidade.get('População', 0), 0)}", ln=True)
    
    # Adicionando Regiões ao PDF
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

        # AJUSTE 1: Exibição das Regiões abaixo de Share e Demanda
        reg_imediata = dados.get('REGIÃO GEOGRÁFICA IMEDIATA', 'N/A')
        reg_intermediaria = dados.get('REGIÃO GEOGRÁFICA INTERMEDIÁRIA', 'N/A')
        st.markdown(f"""
            <div class='region-text'>
                <b>REGIÃO IMEDIATA:</b> {reg_imediata} | <b>REGIÃO INTERMEDIÁRIA:</b> {reg_intermediaria}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    
    # 2. LOCALIZAÇÃO
    st.subheader("2. Mídia e Localização")
    endereco = st.text_input("📍 Link ou Endereço do Ponto:")
    
    # AJUSTE 2: Captura automática de GPS logo abaixo do endereço
    loc = get_geolocation()
    if loc:
        lat = loc['coords']['latitude']
        lon = loc['coords']['longitude']
        lat_lon_str = f"{lat}, {lon}"
        st.success(f"📍 GPS Ativo: Lat: {lat}, Lon: {lon}")
    else:
        lat_lon_str = "Não capturado"
        st.warning("Aguardando permissão de localização/GPS...")

    foto = st.file_uploader("📸 Foto do Imóvel:", type=['jpg', 'jpeg', 'png'])
    if foto: st.image(foto, use_container_width=True)
    
    st.markdown("---")

    # 3. DADOS DO PONTO
    st.subheader("3. Dados do Ponto")
    col_a, col_b = st.columns(2)
    col_c, col_d = st.columns(2)
    
    with col_a:
        f_pess = st.select_slider("Fluxo de pessoas", options=["Baixo", "Médio", "Alto"])
    with col_b:
        f_veic = st.select_slider("Fluxo de veículos", options=["Baixo", "Médio", "Alto"])
    with col_c:
        c_rend = st.select_slider("Classificação de renda", options=["Baixa", "Média", "Alta"])
    with col_d:
        c_popu = st.select_slider("Concentração populacional", options=["Baixo", "Médio", "Alto"])

    # --- CARACTERÍSTICAS DO PONTO ---
    st.write("")
    st.markdown("<h3 style='text-align: center;'>Características do Ponto</h3>", unsafe_allow_html=True)
    
    col_cp1, col_cp2, col_cp3 = st.columns(3)
    with col_cp1:
        char_local = st.select_slider("Local", options=["Centro", "Bairro", "Interligação", "Intrabairro"])
    with col_cp2:
        char_posicao = st.select_slider("Posição", options=["Esquina", "Rótula", "Meio de quadra"])
    with col_cp3:
        char_visib = st.select_slider("Visibilidade", options=["Boa", "Ruim"])

    col_cp4, col_cp5, col_cp6 = st.columns(3)
    with col_cp4:
        char_acess = st.select_slider("Acessibilidade", options=["Baixa", "Média", "Alta"])
    with col_cp5:
        char_vagas = st.select_slider("Vagas", options=["Não", "Sim"])
    with col_cp6:
        char_solar = st.select_slider("Posição Solar", options=["Boa", "Ruim"])

    # --- SEÇÃO: CONCORRÊNCIA ---
    st.write("")
    st.markdown("<h3 style='text-align: center;'>Concorrência</h3>", unsafe_allow_html=True)
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        conc_redes = st.select_slider("Redes", options=["Baixo", "Médio", "Alto"])
    with col_c2:
        conc_indep = st.select_slider("Independentes", options=["Baixo", "Médio", "Alto"])
    with col_c3:
        conc_canib = st.select_slider("Canibalização", options=["Baixo", "Médio", "Alto"])

    # --- SEÇÃO: POLOS GERADORES DE TRÁFEGO ---
    st.write("")
    st.markdown("<h3 style='text-align: center;'>Polos geradores de tráfego</h3>", unsafe_allow_html=True)
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        polo_super = st.select_slider("Supermercado", options=["Não", "Sim"])
    with col_p2:
        polo_pada = st.select_slider("Padaria", options=["Não", "Sim"])
    with col_p3:
        polo_hosp = st.select_slider("Hospital/UPA", options=["Não", "Sim"])
    col_p4, col_p5, col_p6 = st.columns(3)
    with col_p4:
        polo_banc = st.select_slider("Bancos/Lotéricas", options=["Não", "Sim"])
    with col_p5:
        polo_pet = st.select_slider("PetShop", options=["Não", "Sim"])
    with col_p6:
        polo_fem = st.select_slider("Lojas público feminino", options=["Não", "Sim"])

    st.write("") 
    observacoes = st.text_area("📝 Observações da Vistoria:", height=100)

    # Coleta de dados para exportação
    avaliacoes = {"Fluxo Pessoas": f_pess, "Fluxo Veículos": f_veic, "Renda": c_rend, "Concentração": c_popu}
    dados_concorrencia = {"Redes": conc_redes, "Independentes": conc_indep, "Canibalizacao": conc_canib}
    dados_polos = {"Supermercado": polo_super, "Padaria": polo_pada, "Hospital/UPA": polo_hosp, "Bancos": polo_banc, "PetShop": polo_pet, "Lojas Fem": polo_fem}
    dados_caract = {"Local": char_local, "Posicao": char_posicao, "Visibilidade": char_visib, "Acessibilidade": char_acess, "Vagas": char_vagas, "Sol": char_solar}

    st.markdown("---")
    if st.button("🚀 Preparar PDF"):
        try:
            pdf_bytes = exportar_pdf(dados, endereco, lat_lon_str, observacoes, avaliacoes, dados_concorrencia, dados_polos, dados_caract, foto)
            st.download_button(label="⬇️ Baixar Relatório PDF", data=pdf_bytes, file_name=f"Relatorio_{cidade_selecionada}.pdf", mime="application/pdf")
        except Exception as e:
            st.error(f"Erro ao gerar PDF: {e}")
