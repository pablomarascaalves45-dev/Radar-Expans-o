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

    # (Lógica de PDF omitida por brevidade, permanece a mesma do seu original)
    # ... código do PDF ...
    return pdf.output(dest='S').encode('latin-1', errors='replace')

# --- CARREGAMENTO DE DADOS ---
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
    st.subheader("1. Mercado da Cidade")
    cidades = sorted(df['Município'].dropna().unique())
    col_cidade, col_uf = st.columns([4, 1])
    
    with col_cidade:
        cidade_selecionada = st.selectbox("Selecione o município:", options=cidades, index=None, placeholder="Escolha uma cidade...")
    
    if cidade_selecionada:
        dados = df[df['Município'] == cidade_selecionada].iloc[0]
        estado_cidade = dados.get('UF', '')
        with col_uf:
            st.text_input("Estado:", value=estado_cidade, disabled=True)
        
        populacao_cidade = dados.get('População', 0)
        lojas_atuais = dados.get('N° FSJ', 0)
        lojas_cabem_valor = dados.get('Lojas Cabem', 0)
        share_valor_original = dados.get('%Share', 0)
        demanda_cidade = dados.get('Demanda', 0)
        renda_media = dados.get('Renda Média Domiciliar (SM)', 0)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("👥 População", formatar_br(populacao_cidade, 0))
            st.metric("📊 Share", f"{formatar_br(share_valor_original * 100, 2)}%")
        with col2:
            st.metric("🏠 Lojas Atuais", formatar_br(lojas_atuais, 0))
            st.metric("📈 Demanda", formatar_br(demanda_cidade, 2))
        with col3:
            st.metric("💰 Renda Média", formatar_br(renda_media, 2))
            st.metric("🏗️ Lojas Cabem", formatar_br(lojas_cabem_valor, 0))

        # --- SCORE MERCADO (MANTIDO) ---
        score_mercado = 0
        if lojas_cabem_valor > 0: score_mercado += 15
        if share_valor_original <= 0.30: score_mercado += 15

        # ... Lógica regional de bônus RS/SC/PR ...
        # (Omitida aqui para focar na classificação final solicitada)

        st.markdown("---")
        st.subheader("2. Mídia e Localização")
        endereco = st.text_input("📍 Link ou Endereço do Ponto:")
        loc = get_geolocation()
        lat_lon_str = f"{loc['coords']['latitude']}, {loc['coords']['longitude']}" if loc else "Não capturado"
        foto = st.file_uploader("📸 Foto do Imóvel:", type=['jpg', 'jpeg', 'png'])
        
        st.markdown("---")
        st.subheader("3. Dados do Ponto")
        
        # ... Sliders e Selectboxes (Padrão) ...
        # [Cálculo de score_ponto_calc simplificado para o exemplo]
        score_ponto = 50 # Exemplo de valor calculado

        # CÁLCULO FINAL DE PORCENTAGEM
        # (Ajuste conforme sua regra: Score Mercado (30) + Score Ponto (70) = 100%)
        porcentagem_final = score_mercado + score_ponto 

        # --- LÓGICA DE CLASSIFICAÇÃO (TABELA NOVA) ---
        if porcentagem_final > 90:
            label_class = "Premium"
            txt_recomenda = "Ponto de altíssima prioridade; solicitar estudo."
            cor_destaque = "#00ffcc"
        elif porcentagem_final >= 70:
            label_class = "Favorável"
            txt_recomenda = "Ponto sólido; ajustes menores em negociação de aluguel."
            cor_destaque = "#f1c40f"
        elif porcentagem_final >= 60:
            label_class = "Médio Risco"
            txt_recomenda = "Requer análise interna; olhar atento às características e dados de geomarketing."
            cor_destaque = "#e67e22"
        else:
            label_class = "Inviável"
            txt_recomenda = "Reprovado tecnicamente; alto risco de ROI negativo."
            cor_destaque = "#ff4b4b"

        if st.button("📊 AVALIAR"):
            st.markdown(f"""
                <div class="score-container">
                    <div class="sub-score-text">Resultado da Análise Técnica</div>
                    <hr style="border: 0.5px solid #4a5568; margin: 15px 0;">
                    <div class="classificacao-text" style="color: {cor_destaque};">{label_class}</div>
                    <div class="recomendacao-text">{txt_recomenda}</div>
                    <div class="total-score-text" style="color: {cor_destaque};">{porcentagem_final:.1f}%</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Botão de download (lógica do PDF deve receber os novos textos)
            # st.download_button(...)
