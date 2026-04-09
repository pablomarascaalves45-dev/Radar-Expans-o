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
        font-size: 2.8rem;
        color: #00ffcc;
        font-weight: bold;
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
    
    polos_str = ", ".join([k for k, v in polos.items() if v == "Sim"])
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

        # --- SCORE MERCADO ---
        score_mercado = 0
        if lojas_cabem_valor > 0:
            score_mercado += 15
            if share_valor_original <= 0.30: score_mercado += 15
        if estado_cidade in ["SC", "PR"]:
            if demanda_cidade < 2000000: score_mercado -= 15 
            if populacao_cidade < 15000: score_mercado -= 15 
        elif estado_cidade == "RS":
            if demanda_cidade < 1200000: score_mercado -= 15
            if populacao_cidade < 6000: score_mercado -= 15
        score_mercado = max(-30, min(30, score_mercado))

        st.markdown("---")
        st.subheader("2. Mídia e Localização")
        endereco = st.text_input("📍 Link ou Endereço do Ponto:")
        loc = get_geolocation()
        lat_lon_str = f"{loc['coords']['latitude']}, {loc['coords']['longitude']}" if loc else "Não capturado"
        foto = st.file_uploader("📸 Foto do Imóvel:", type=['jpg', 'jpeg', 'png'])
        
        st.markdown("---")
        st.subheader("3. Dados do Ponto")
        
        opcoes_padrao = ["Selecionar", "Baixo", "Médio", "Alto"]
        opcoes_renda = ["Selecionar", "Baixa", "Média", "Alta"]
        opcoes_sim_nao = ["Selecionar", "Sim", "Não"]
        opcoes_boa_ruim = ["Selecionar", "Boa", "Ruim"]

        peso_fluxo_pessoas = {"Selecionar": 0, "Baixo": 5, "Médio": 10, "Alto": 15}
        peso_padrao = {"Selecionar": 0, "Baixo": 1, "Médio": 3, "Alto": 5}
        peso_renda = {"Selecionar": 0, "Baixa": 1, "Média": 5, "Alta": 3}
        peso_concorrencia = {"Selecionar": 0, "Baixo": 5, "Médio": 2, "Alto": -5} 
        peso_canibalizacao = {"Selecionar": 0, "Baixo": 5, "Médio": -3, "Alto": -10}
        
        col_a, col_b = st.columns(2)
        col_c, col_d = st.columns(2)
        with col_a: f_pess = st.select_slider("Fluxo de pessoas", options=opcoes_padrao, value="Selecionar")
        with col_b: f_veic = st.select_slider("Fluxo de veículos", options=opcoes_padrao, value="Selecionar")
        with col_c: c_rend = st.select_slider("Classificação de renda", options=opcoes_renda, value="Selecionar")
        with col_d: c_popu = st.select_slider("Concentração populacional", options=opcoes_padrao, value="Selecionar")

        st.markdown("<h3 style='text-align: center;'>Características do Ponto</h3>", unsafe_allow_html=True)
        col_cp1, col_cp2, col_cp3 = st.columns(3)
        with col_cp1: char_local = st.selectbox("Local", options=["Selecionar", "Centro", "Bairro", "Interligação", "Intrabairro"])
        with col_cp2: char_posicao = st.selectbox("Posição", options=["Selecionar", "Esquina", "Rótula", "Meio de quadra"])
        with col_cp3: char_visib = st.selectbox("Visibilidade", options=opcoes_boa_ruim)
        
        col_cp4, col_cp5, col_cp6 = st.columns(3)
        with col_cp4: char_acess = st.selectbox("Acessibilidade", options=opcoes_boa_ruim)
        with col_cp5: char_vagas = st.selectbox("Vagas", options=opcoes_sim_nao)
        with col_cp6: char_solar = st.selectbox("Posição Solar", options=opcoes_boa_ruim)

        st.markdown("<h3 style='text-align: center;'>Concorrência</h3>", unsafe_allow_html=True)
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1: conc_redes = st.select_slider("Redes", options=opcoes_padrao, value="Selecionar")
        with col_c2: conc_indep = st.select_slider("Independentes", options=opcoes_padrao, value="Selecionar")
        with col_c3: conc_canib = st.select_slider("Canibalização", options=opcoes_padrao, value="Selecionar")

        st.markdown("<h3 style='text-align: center;'>Polos geradores de tráfego</h3>", unsafe_allow_html=True)
        p1, p2, p3 = st.columns(3)
        with p1: polo_super = st.checkbox("Supermercado")
        with p2: polo_pada = st.checkbox("Padaria")
        with p3: polo_hosp = st.checkbox("Hospital/UPA")
        p4, p5, p6 = st.columns(3)
        with p4: polo_banc = st.checkbox("Bancos/Lotéricas")
        with p5: polo_pet = st.checkbox("PetShop")
        with p6: polo_fem = st.checkbox("Lojas público feminino")

        observacoes = st.text_area("📝 Observações da Vistoria:", height=80)

        # --- CÁLCULO SCORE PONTO ---
        score_ponto_calc = peso_fluxo_pessoas[f_pess] + peso_padrao[f_veic] + peso_renda[c_rend] + peso_padrao[c_popu]
        score_ponto_calc += peso_concorrencia[conc_redes] + peso_concorrencia[conc_indep] + peso_canibalizacao[conc_canib]
        score_ponto_calc += (5 if polo_super else 0) + (4 if polo_pada else 0) + (3 if polo_hosp else 0)
        score_ponto_calc += (3 if polo_banc else 0) + (2 if polo_pet else 0) + (3 if polo_fem else 0)
        
        if char_posicao == "Esquina":
            score_ponto_calc += 5
        elif char_posicao == "Rótula":
            score_ponto_calc += 3
        elif char_posicao == "Meio de quadra":
            if estado_cidade == "RS": score_ponto_calc += 3
            elif estado_cidade == "SC": score_ponto_calc -= 3
            elif estado_cidade == "PR": score_ponto_calc += 3

        if char_acess == "Boa": score_ponto_calc += 3
        elif char_acess == "Ruim": score_ponto_calc -= 5
        if char_vagas == "Sim": score_ponto_calc += 3
        elif char_vagas == "Não": score_ponto_calc -= 5
        if char_visib == "Boa": score_ponto_calc += 3
        elif char_visib == "Ruim": score_ponto_calc -= 3
        if char_solar == "Boa": score_ponto_calc += 2

        # Ajuste de limite do score do ponto (0 a 70)
        score_ponto = max(0, min(70, score_ponto_calc))

        # --- CÁLCULO DA PORCENTAGEM PONDERADA ---
        aproveitamento_mercado = max(0, score_mercado) / 30
        aproveitamento_ponto = score_ponto / 70
        porcentagem_final = (aproveitamento_mercado * 30) + (aproveitamento_ponto * 70)

        if st.button("📊 AVALIAR"):
            # Formatação simplificada conforme pedido
            perc_mercado_str = f"<b>{(aproveitamento_mercado*100):.2f}%</b>"
            perc_ponto_str = f"<b>{(aproveitamento_ponto*100):.2f}%</b>"

            st.markdown(f"""
                <div class="score-container">
                    <div class="sub-score-text">Mercado da Cidade: {perc_mercado_str}</div>
                    <div class="sub-score-text">Dados do Ponto: {perc_ponto_str}</div>
                    <hr style="border: 0.5px solid #4a5568;">
                    <div class="sub-score-text" style="color: #9da5b1; font-size: 0.9rem;">ADERÊNCIA TOTAL AO MODELO</div>
                    <div class="total-score-text">{porcentagem_final:.2f}%</div>
                </div>
            """, unsafe_allow_html=True)

            aval = {"Fluxo Pessoas": f_pess, "Fluxo Veiculos": f_veic, "Renda": c_rend, "Concentracao": c_popu}
            conc = {"Redes": conc_redes, "Independentes": conc_indep, "Canibalizacao": conc_canib}
            pol = {"Supermercado": "Sim" if polo_super else "Nao", "Padaria": "Sim" if polo_pada else "Nao", "Hospital": "Sim" if polo_hosp else "Nao", "Bancos": "Sim" if polo_banc else "Nao", "Pet": "Sim" if polo_pet else "Nao", "Feminino": "Sim" if polo_fem else "Nao"}
            caract = {"Local": char_local, "Posicao": char_posicao, "Visibilidade": char_visib, "Acessibilidade": char_acess, "Vagas": char_vagas, "Sol": char_solar}

            pdf_bytes = exportar_pdf(dados, endereco, lat_lon_str, observacoes, aval, conc, pol, caract, foto, f"{porcentagem_final:.2f}%", score_mercado, score_ponto)
            st.download_button(label="🚀 Baixar Relatório PDF", data=pdf_bytes, file_name=f"Relatorio_{cidade_selecionada}.pdf", mime="application/pdf")
    else:
        st.info("Por favor, selecione um município.")
else:
    st.error("Arquivo 'Ranking PCA.xlsx' não encontrado.")
