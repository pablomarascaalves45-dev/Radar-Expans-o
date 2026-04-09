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
    .score-container {
        background-color: #1e2130;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #4a5568;
        text-align: center;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES AUXILIARES ---
def formatar_br(valor, casas=2):
    try:
        if pd.isna(valor): return "0"
        return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return str(valor)

def exportar_pdf(dados_cidade, endereco, lat_lon, obs, avaliacoes, concorrencia, polos, caracteristicas, foto_arquivo, score_final):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(10, 10, 10)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, txt="Relatorio de Expansao - Analise de Ponto", ln=True, align='C')
    pdf.set_text_color(0, 51, 102)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, txt=f"SCORE FINAL: {score_final} PONTOS", ln=True, align='C')
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, txt="1. Mercado da Cidade", ln=True)
    pdf.set_font("Arial", "", 9)
    municipio = str(dados_cidade.get('Município', 'N/A')).encode('latin-1', 'ignore').decode('latin-1')
    uf = str(dados_cidade.get('UF', 'N/A'))
    pdf.cell(0, 5, txt=f"Municipio: {municipio} - {uf} | Populacao: {formatar_br(dados_cidade.get('População', 0), 0)}", ln=True)
    pdf.ln(2)

    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, txt="2. Dados do Ponto", ln=True)
    pdf.set_font("Arial", "", 8)
    pdf.multi_cell(0, 4, txt=f"Endereco: {str(endereco).encode('latin-1', 'ignore').decode('latin-1')}")
    pdf.cell(0, 4, txt=f"GPS: {lat_lon}", ln=True)
    pdf.ln(2)

    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, txt="3. Analise de Campo", ln=True)
    y_start_analise = pdf.get_y()
    
    def print_dict_compact(titulo, dicionario, x_pos, y_pos):
        pdf.set_xy(x_pos, y_pos)
        pdf.set_font("Arial", "B", 8)
        pdf.cell(45, 5, txt=titulo, ln=True)
        pdf.set_font("Arial", "", 8)
        for chave, valor in dicionario.items():
            pdf.set_x(x_pos)
            pdf.cell(45, 4, txt=f"- {chave}: {valor}", ln=True)
        return pdf.get_y()

    h1 = print_dict_compact("Fluxo/Renda", avaliacoes, 10, y_start_analise)
    h2 = print_dict_compact("Concorrencia", concorrencia, 10, h1 + 2)
    h3 = print_dict_compact("Caracteristicas", caracteristicas, 60, y_start_analise)
    h4 = print_dict_compact("Polos Geradores", polos, 110, y_start_analise)

    final_y = max(h2, h3, h4) + 5
    pdf.set_xy(10, final_y)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(0, 5, txt="Observacoes:", ln=True)
    pdf.set_font("Arial", "", 8)
    pdf.multi_cell(0, 4, txt=str(obs).encode('latin-1', 'ignore').decode('latin-1'))
    
    if foto_arquivo:
        try:
            img = Image.open(foto_arquivo)
            if img.mode in ("RGBA", "P"): img = img.convert("RGB")
            img_path = "temp_pdf_foto.jpg"
            img.save(img_path)
            pdf.image(img_path, x=20, y=pdf.get_y()+5, w=170)
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
        # Adicionado index=None para iniciar vazio
        cidade_selecionada = st.selectbox("Selecione o município:", options=cidades, index=None, placeholder="Escolha uma cidade...")
    
    # Só processa o restante do script se uma cidade for escolhida
    if cidade_selecionada:
        dados = df[df['Município'] == cidade_selecionada].iloc[0]
        
        with col_uf:
            estado_cidade = dados.get('UF', '')
            st.text_input("Estado:", value=estado_cidade, disabled=True)
        
        populacao_cidade = dados.get('População', 0)
        lojas_atuais = dados.get('N° FSJ', 0)
        lojas_cabem_valor = dados.get('Lojas Cabem', 0)
        share_valor_original = dados.get('%Share', 0)
        demanda_cidade = dados.get('Demanda', 0)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("👥 População", formatar_br(populacao_cidade, 0))
            st.metric("📊 Share", f"{formatar_br(share_valor_original * 100, 2)}%")
        with col2:
            st.metric("🏠 Lojas Atuais", formatar_br(lojas_atuais, 0))
            st.metric("📈 Demanda", formatar_br(demanda_cidade, 2))
        with col3:
            st.metric("💰 Renda Média", formatar_br(dados.get('Renda Média Domiciliar (SM)', 0), 2))
            st.metric("🏗️ Lojas Cabem", formatar_br(lojas_cabem_valor, 0))

        # --- LÓGICA DE SCORE DE MERCADO ---
        score_mercado = (15 if lojas_cabem_valor > 0 else 0) + (15 if share_valor_original <= 0.30 else 0)

        if estado_cidade in ["SC", "PR"]:
            if demanda_cidade < 2000000: score_mercado -= 15
            if populacao_cidade < 15000: score_mercado -= 15
        elif estado_cidade == "RS":
            if demanda_cidade < 1200000: score_mercado -= 20
            if populacao_cidade < 6000: score_mercado -= 20

        st.markdown("---")
        st.subheader("2. Mídia e Localização")
        endereco = st.text_input("📍 Link ou Endereço do Ponto:")
        loc = get_geolocation()
        lat_lon_str = f"{loc['coords']['latitude']}, {loc['coords']['longitude']}" if loc else "Não capturado"
        foto = st.file_uploader("📸 Foto do Imóvel:", type=['jpg', 'jpeg', 'png'])
        
        st.markdown("---")
        st.subheader("3. Dados do Ponto")
        
        peso_padrao = {"Baixo": 5, "Médio": 10, "Alto": 15}
        peso_renda = {"Baixa": 5, "Média": 15, "Alta": 10}
        peso_concorrencia = {"Baixo": 10, "Médio": 5, "Alto": -5} 
        peso_canibalizacao = {"Baixo": 10, "Médio": -5, "Alto": -10}
        
        col_a, col_b = st.columns(2)
        col_c, col_d = st.columns(2)
        with col_a: f_pess = st.select_slider("Fluxo de pessoas", options=["Baixo", "Médio", "Alto"])
        with col_b: f_veic = st.select_slider("Fluxo de veículos", options=["Baixo", "Médio", "Alto"])
        with col_c: c_rend = st.select_slider("Classificação de renda", options=["Baixa", "Média", "Alta"])
        with col_d: c_popu = st.select_slider("Concentração populacional", options=["Baixo", "Médio", "Alto"])

        st.markdown("<h3 style='text-align: center;'>Características do Ponto</h3>", unsafe_allow_html=True)
        col_cp1, col_cp2, col_cp3 = st.columns(3)
        with col_cp1: char_local = st.selectbox("Local", options=["Centro", "Bairro", "Interligação", "Intrabairro"])
        with col_cp2: char_posicao = st.selectbox("Posição", options=["Esquina", "Rótula", "Meio de quadra"])
        with col_cp3: char_visib = st.selectbox("Visibilidade", options=["Boa", "Ruim"])
        
        col_cp4, col_cp5, col_cp6 = st.columns(3)
        with col_cp4: char_acess = st.selectbox("Acessibilidade", options=["Boa", "Ruim"])
        with col_cp5: char_vagas = st.selectbox("Vagas", options=["Sim", "Não"])
        with col_cp6: char_solar = st.selectbox("Posição Solar", options=["Boa", "Ruim"])

        # --- LÓGICA DE POSIÇÃO ---
        score_posicao = 0
        if estado_cidade == "RS":
            pesos_pos = {"Esquina": 10, "Meio de quadra": 5, "Rótula": 7}
            score_posicao = pesos_pos.get(char_posicao, 0)
        elif estado_cidade == "PR":
            pesos_pos = {"Esquina": 10, "Meio de quadra": 5 if populacao_cidade < 50000 else -5, "Rótula": 7}
            score_posicao = pesos_pos.get(char_posicao, 0)
        elif estado_cidade == "SC":
            pesos_pos = {"Esquina": 10, "Meio de quadra": -10, "Rótula": 7}
            score_posicao = pesos_pos.get(char_posicao, 0)
        else:
            pesos_pos = {"Esquina": 5, "Meio de quadra": 0, "Rótula": 2}
            score_posicao = pesos_pos.get(char_posicao, 0)

        # Lógica de Localização
        score_local = 0
        if populacao_cidade <= 100000:
            pesos_loc = {"Centro": 15 if lojas_atuais == 0 else 10, "Bairro": -5 if lojas_atuais == 0 else 5, "Interligação": 0 if lojas_atuais == 0 else 5, "Intrabairro": -5 if lojas_atuais == 0 else 0}
        else:
            pesos_loc = {"Centro": 10, "Bairro": 5, "Interligação": 5, "Intrabairro": 5}
        score_local = pesos_loc.get(char_local, 0)

        st.markdown("<h3 style='text-align: center;'>Concorrência</h3>", unsafe_allow_html=True)
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1: conc_redes = st.select_slider("Redes", options=["Baixo", "Médio", "Alto"])
        with col_c2: conc_indep = st.select_slider("Independentes", options=["Baixo", "Médio", "Alto"])
        with col_c3: conc_canib = st.select_slider("Canibalização", options=["Baixo", "Médio", "Alto"])

        st.markdown("<h3 style='text-align: center;'>Polos geradores de tráfego</h3>", unsafe_allow_html=True)
        p1, p2, p3 = st.columns(3)
        with p1: polo_super = st.checkbox("Supermercado")
        with p2: polo_pada = st.checkbox("Padaria")
        with p3: polo_hosp = st.checkbox("Hospital/UPA")
        p4, p5, p6 = st.columns(3)
        with p4: polo_banc = st.checkbox("Bancos/Lotéricas")
        with p5: polo_pet = st.checkbox("PetShop")
        with p6: polo_fem = st.checkbox("Lojas público feminino")

        # Cálculo final
        score_ponto = peso_padrao[f_pess] + peso_padrao[f_veic] + peso_renda[c_rend] + peso_padrao[c_popu]
        score_ponto += peso_concorrencia[conc_redes] + peso_concorrencia[conc_indep] + peso_canibalizacao[conc_canib]
        score_ponto += (7 if polo_super else 0) + (6 if polo_pada else 0) + (5 if polo_hosp else 0)
        score_ponto += (5 if polo_banc else 0) + (2 if polo_pet else 0) + (5 if polo_fem else 0)
        score_ponto += (5 if char_acess == "Boa" else -10) + (5 if char_vagas == "Sim" else -10)
        score_ponto += (5 if char_visib == "Boa" else -5) + (5 if char_solar == "Boa" else 0)
        score_ponto += score_local + score_posicao
        
        score_final = score_mercado + score_ponto
        observacoes = st.text_area("📝 Observações da Vistoria:", height=80)

        st.markdown(f'<div class="score-container"><h1 style="color:white;">{score_final} pts</h1></div>', unsafe_allow_html=True)

        if st.button("🚀 Gerar Relatório"):
            avaliacoes = {"Fluxo Pessoas": f_pess, "Fluxo Veículos": f_veic, "Renda": c_rend, "Concentração": c_popu}
            dados_concorrencia = {"Redes": conc_redes, "Independentes": conc_indep, "Canibalizacao": conc_canib}
            dados_polos = {"Super": "Sim" if polo_super else "Não", "Padaria": "Sim" if polo_pada else "Não", "Saude": "Sim" if polo_hosp else "Não", "Banco": "Sim" if polo_banc else "Não", "Pet": "Sim" if polo_pet else "Não", "Feminino": "Sim" if polo_fem else "Não"}
            dados_caract = {"Local": f"{char_local} (+{score_local})", "Posicao": f"{char_posicao} (+{score_posicao})", "Visib.": char_visib, "Acess.": char_acess, "Vagas": char_vagas, "Sol": char_solar}
            pdf_bytes = exportar_pdf(dados, endereco, lat_lon_str, observacoes, avaliacoes, dados_concorrencia, dados_polos, dados_caract, foto, score_final)
            st.download_button(label="⬇️ Baixar PDF", data=pdf_bytes, file_name=f"Relatorio_{cidade_selecionada}.pdf", mime="application/pdf")
    else:
        st.info("Por favor, selecione um município para iniciar a análise.")
