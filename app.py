import streamlit as st
import pandas as pd
from fpdf import FPDF
from streamlit_js_eval import get_geolocation
from PIL import Image
import os

# 1. Configuração da página
st.set_page_config(page_title="Radar de Expansão", layout="centered")

# 2. Estilização personalizada
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; color: #ffffff !important; }
    .score-sub-box {
        background-color: #1e2130;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #4a5568;
        text-align: center;
        margin-bottom: 10px;
    }
    .score-total-box {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin-top: 20px;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES AUXILIARES ---
def formatar_br(valor, casas=2):
    try:
        if pd.isna(valor): return "0"
        return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except: return str(valor)

def exportar_pdf(dados_cidade, endereco, lat_lon, obs, scores, detalhes_ponto, foto_arquivo):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, txt="Relatório de Expansão - Análise de Ponto", ln=True, align='C')
    
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(59, 130, 246)
    pdf.cell(0, 10, txt=f"SCORE FINAL: {scores['total']} PONTOS", ln=True, align='C')
    pdf.set_text_color(0, 0, 0)
    
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 8, txt=f"Mercado: {scores['mercado']} pts | Ponto: {scores['ponto']} pts", ln=True, align='C')
    pdf.ln(5)

    # Dados da Cidade
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, txt="1. Dados do Mercado", ln=True)
    pdf.set_font("Arial", "", 10)
    municipio = str(dados_cidade.get('Município', 'N/A')).encode('latin-1', 'ignore').decode('latin-1')
    pdf.cell(0, 6, txt=f"Cidade: {municipio} - {dados_cidade.get('UF', '')}", ln=True)
    pdf.cell(0, 6, txt=f"Populacao: {formatar_br(dados_cidade.get('População', 0), 0)}", ln=True)
    pdf.ln(5)

    # Dados do Ponto
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, txt="2. Localização e Vistoria", ln=True)
    pdf.set_font("Arial", "", 9)
    pdf.multi_cell(0, 5, txt=f"Endereco: {str(endereco).encode('latin-1', 'ignore').decode('latin-1')}")
    pdf.cell(0, 5, txt=f"Coordenadas: {lat_lon}", ln=True)
    pdf.ln(5)

    # Observações
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, txt="3. Observacoes de Campo", ln=True)
    pdf.set_font("Arial", "", 9)
    pdf.multi_cell(0, 5, txt=str(obs).encode('latin-1', 'ignore').decode('latin-1'))

    return pdf.output(dest='S').encode('latin-1', errors='replace')

@st.cache_data
def load_data():
    try:
        file_path = 'Ranking PCA.xlsx'
        if not os.path.exists(file_path): return None
        df_raw = pd.read_excel(file_path, header=None)
        header_idx = 0
        for i, row in df_raw.iterrows():
            if "Município" in [str(val).strip() for val in row.values]:
                header_idx = i
                break
        df = pd.read_excel(file_path, skiprows=header_idx)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except: return None

# --- EXECUÇÃO DO APP ---
df = load_data()

if df is not None:
    st.title("🎯 Radar de Expansão")
    
    # ---------------------------------------------------------
    # BLOCO 1: MERCADO DA CIDADE
    # ---------------------------------------------------------
    st.header("1. Mercado da Cidade")
    cidades = sorted(df['Município'].dropna().unique())
    col_cid, col_uf_exib = st.columns([3, 1])
    
    with col_cid:
        cidade_selecionada = st.selectbox("Selecione o município:", options=cidades, index=None)
    
    if cidade_selecionada:
        dados = df[df['Município'] == cidade_selecionada].iloc[0]
        uf = dados.get('UF', '')
        col_uf_exib.text_input("UF", value=uf, disabled=True)
        
        # Variáveis de cálculo
        pop = dados.get('População', 0)
        demanda = dados.get('Demanda', 0)
        cabem = dados.get('Lojas Cabem', 0)
        share = dados.get('%Share', 0)
        
        # Exibição de métricas
        m1, m2, m3 = st.columns(3)
        m1.metric("População", formatar_br(pop, 0))
        m2.metric("Demanda", formatar_br(demanda, 0))
        m3.metric("Lojas Cabem", formatar_br(cabem, 0))

        # Lógica Score Mercado
        score_mercado = 0
        if cabem > 0:
            score_mercado += 15
            if share <= 0.30:
                score_mercado += 15

        # Penalidades Específicas
        if uf in ["SC", "PR"]:
            if demanda < 2000000: score_mercado -= 25
            if pop < 15000: score_mercado -= 20
        elif uf == "RS":
            if demanda < 1200000: score_mercado -= 20
            if pop < 6000: score_mercado -= 20

        st.markdown(f"<div class='score-sub-box'><b>Score Bloco Mercado:</b> {score_mercado} pts</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.header("2. Mídia e Localização")
        endereco = st.text_input("📍 Link ou Endereço do Ponto:")
        loc = get_geolocation()
        lat_lon_str = f"{loc['coords']['latitude']}, {loc['coords']['longitude']}" if loc else "Não capturado"
        foto = st.file_uploader("📸 Foto do Imóvel:", type=['jpg', 'jpeg', 'png'])

        # ---------------------------------------------------------
        # BLOCO 2: DADOS DO PONTO
        # ---------------------------------------------------------
        st.markdown("---")
        st.header("3. Dados do Ponto")
        
        opcoes_padrao = ["Selecionar", "Baixo", "Médio", "Alto"]
        peso_padrao = {"Selecionar": 0, "Baixo": 5, "Médio": 10, "Alto": 15}
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            f_pess = st.select_slider("Fluxo de pessoas", options=opcoes_padrao)
            f_veic = st.select_slider("Fluxo de veículos", options=opcoes_padrao)
        with col_p2:
            c_rend = st.select_slider("Classificação de renda", options=["Selecionar", "Baixa", "Média", "Alta"])
            c_popu = st.select_slider("Concentração populacional", options=opcoes_padrao)

        st.subheader("Características do Imóvel")
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            char_visib = st.selectbox("Visibilidade", ["Selecionar", "Boa", "Ruim"])
            char_vagas = st.selectbox("Vagas", ["Selecionar", "Sim", "Não"])
        with col_c2:
            char_acess = st.selectbox("Acessibilidade", ["Selecionar", "Boa", "Ruim"])
            char_solar = st.selectbox("Posição Solar", ["Selecionar", "Boa", "Ruim"])
        with col_c3:
            char_posicao = st.selectbox("Posição", ["Selecionar", "Esquina", "Rótula", "Meio de quadra"])
            char_local = st.selectbox("Tipo de Local", ["Selecionar", "Centro", "Bairro", "Interligação"])

        st.subheader("Polos Geradores")
        p1, p2, p3 = st.columns(3)
        polo_super = p1.checkbox("Supermercado (+7)")
        polo_pada = p2.checkbox("Padaria (+6)")
        polo_hosp = p3.checkbox("Hospital/UPA (+5)")
        
        # Cálculo Score Ponto
        score_ponto = peso_padrao[f_pess] + peso_padrao[f_veic] + peso_padrao[c_popu]
        score_ponto += {"Selecionar": 0, "Baixa": 5, "Média": 15, "Alta": 10}[c_rend]
        
        # Bônus/Ônus Características
        if char_visib == "Boa": score_ponto += 5
        elif char_visib == "Ruim": score_ponto -= 5
        if char_vagas == "Sim": score_ponto += 5
        elif char_vagas == "Não": score_ponto -= 10
        
        score_ponto += (7 if polo_super else 0) + (6 if polo_pada else 0) + (5 if polo_hosp else 0)

        st.markdown(f"<div class='score-sub-box'><b>Score Bloco Ponto:</b> {score_ponto} pts</div>", unsafe_allow_html=True)

        # ---------------------------------------------------------
        # SCORE FINAL
        # ---------------------------------------------------------
        total = score_mercado + score_ponto
        
        st.markdown(f"""
            <div class='score-total-box'>
                <h1 style='color: white; margin:0;'>SCORE FINAL: {total} pts</h1>
                <p style='margin:0;'>Mercado ({score_mercado}) + Vistoria ({score_ponto})</p>
            </div>
        """, unsafe_allow_html=True)

        observacoes = st.text_area("📝 Observações da Vistoria:", height=100)

        if st.button("🚀 Gerar e Baixar Relatório PDF"):
            scores_resumo = {"mercado": score_mercado, "ponto": score_ponto, "total": total}
            pdf_bytes = exportar_pdf(dados, endereco, lat_lon_str, observacoes, scores_resumo, {}, foto)
            st.download_button(label="⬇️ Clique aqui para Baixar", data=pdf_bytes, file_name=f"Relatorio_{cidade_selecionada}.pdf", mime="application/pdf")

    else:
        st.info("Selecione um município para iniciar a análise.")
else:
    st.error("Arquivo 'Ranking PCA.xlsx' não encontrado no diretório.")
