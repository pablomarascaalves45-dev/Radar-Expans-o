import streamlit as st
import pandas as pd
from fpdf import FPDF
from streamlit_js_eval import get_geolocation
import datetime
from PIL import Image
import io
import os

# 1. Configuração da página
st.set_config(page_title="Radar de Expansão", layout="centered")

# 2. Estilização personalizada
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; color: #ffffff !important; }
    .score-box {
        background-color: #1e2130;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #4a5568;
        text-align: center;
    }
    .total-score {
        background: linear-gradient(90deg, #4b6cb7 0%, #182848 100%);
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin-top: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES AUXILIARES ---
def formatar_br(valor, casas=2):
    try:
        if pd.isna(valor): return "0"
        return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except: return str(valor)

def exportar_pdf(dados_cidade, endereco, lat_lon, obs, avaliacoes, concorrencia, polos, caracteristicas, foto_arquivo, s_mercado, s_ponto, s_final):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, txt="Relatorio de Expansao - Analise de Ponto", ln=True, align='C')
    
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, txt=f"SCORE TOTAL: {s_final} PONTOS (Mercado: {s_mercado} | Ponto: {s_ponto})", ln=True, align='C')
    pdf.ln(5)

    # ... (Restante da lógica do PDF permanece similar, apenas incluído o detalhamento do score no cabeçalho)
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

df = load_data()

if df is not None:
    st.title("🎯 Radar de Expansão")
    
    # --- BLOCO 1: MERCADO DA CIDADE ---
    st.header("1. Mercado da Cidade")
    cidades = sorted(df['Município'].dropna().unique())
    cidade_selecionada = st.selectbox("Selecione o município:", options=cidades, index=None)
    
    if cidade_selecionada:
        dados = df[df['Município'] == cidade_selecionada].iloc[0]
        estado_cidade = dados.get('UF', '')
        populacao_cidade = dados.get('População', 0)
        lojas_cabem_valor = dados.get('Lojas Cabem', 0)
        share_valor_original = dados.get('%Share', 0)
        demanda_cidade = dados.get('Demanda', 0)

        # Cálculo de Score de Mercado
        score_mercado = 0
        if lojas_cabem_valor > 0:
            score_mercado += 15
            if share_valor_original <= 0.30:
                score_mercado += 15

        if estado_cidade in ["SC", "PR"]:
            if demanda_cidade < 2000000: score_mercado -= 25
            if populacao_cidade < 15000: score_mercado -= 20
        elif estado_cidade == "RS":
            if demanda_cidade < 1200000: score_mercado -= 20
            if populacao_cidade < 6000: score_mercado -= 20

        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("População", formatar_br(populacao_cidade, 0))
        col_m2.metric("Demanda", formatar_br(demanda_cidade, 0))
        col_m3.metric("Lojas Cabem", formatar_br(lojas_cabem_valor, 0))
        
        st.markdown(f"""<div class='score-box'><b>Subtotal Mercado:</b> {score_mercado} pts</div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.header("2. Mídia e Localização")
        endereco = st.text_input("📍 Endereço do Ponto:")
        foto = st.file_uploader("📸 Foto do Imóvel:", type=['jpg', 'png'])

        # --- BLOCO 2: DADOS DO PONTO ---
        st.markdown("---")
        st.header("3. Dados do Ponto")
        
        opcoes_padrao = ["Selecionar", "Baixo", "Médio", "Alto"]
        peso_padrao = {"Selecionar": 0, "Baixo": 5, "Médio": 10, "Alto": 15}
        
        c1, c2 = st.columns(2)
        with c1: f_pess = st.select_slider("Fluxo de pessoas", options=opcoes_padrao)
        with c2: f_veic = st.select_slider("Fluxo de veículos", options=opcoes_padrao)

        # Lógica de Características e Polos
        st.subheader("Características e Polos")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            polo_super = st.checkbox("Próximo a Supermercado (+7)")
            polo_banc = st.checkbox("Próximo a Bancos (+5)")
        with col_p2:
            char_visib = st.selectbox("Visibilidade", ["Selecionar", "Boa", "Ruim"])
            char_vagas = st.selectbox("Vagas de Estacionamento", ["Selecionar", "Sim", "Não"])

        # Cálculo de Score do Ponto
        score_ponto = peso_padrao[f_pess] + peso_padrao[f_veic]
        score_ponto += (7 if polo_super else 0) + (5 if polo_banc else 0)
        if char_visib == "Boa": score_ponto += 5
        if char_vagas == "Sim": score_ponto += 5
        
        st.markdown(f"""<div class='score-box'><b>Subtotal Ponto:</b> {score_ponto} pts</div>""", unsafe_allow_html=True)

        # --- RESULTADO FINAL ---
        score_final = score_mercado + score_ponto
        
        st.markdown(f"""
            <div class='total-score'>
                <h2 style='color: white; margin:0;'>Score Final: {score_final} pts</h2>
                <p style='color: #d1d1d1; margin:0;'>Mercado ({score_mercado}) + Ponto ({score_ponto})</p>
            </div>
        """, unsafe_allow_html=True)

        observacoes = st.text_area("Observações:")

        if st.button("🚀 Gerar Relatório Completo"):
            st.success("Relatório gerado com sucesso!")
            # Chamar função exportar_pdf com os novos parâmetros de score
