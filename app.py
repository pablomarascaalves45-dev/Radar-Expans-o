import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime
from PIL import Image
import io
import os
import plotly.express as px

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Radar de Expansão & Analytics", layout="wide")

# --- SISTEMA DE LOGIN ---
USUARIOS_AUTORIZADOS = {
    "Pablo": "55997260245",
    "Lucas": "257030",
    "Eduardo": "5499865084",
    "Eduardo Pedroso": "5496733252",
    "Estevam": "5496964416",    
    "Laércio": "5492130467",
    "Rocha": "4491332648",
    "Gabriel": "5497114483",
    "Juliano": "5481345155",
    "Laerti": "5492371861",
    "Luan": "5496001432",
    "Naudal": "5181285090",
}

if 'logado' not in st.session_state:
    st.session_state.logado = False

def tela_login():
    st.markdown("""
        <style>
        .login-box {
            padding: 2.5rem;
            border-radius: 10px;
            border: 1px solid #4a5568;
            background-color: rgba(157, 165, 177, 0.1);
            margin-top: 50px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.title("🔐 Acesso Restrito")
        st.subheader("Radar de Expansão")
        
        nome_input = st.text_input("Nome Completo")
        celular_input = st.text_input("Número de Celular (com DDD)", placeholder="Ex: 519XXXXXXXX")
        
        if st.button("ENTRAR"):
            if nome_input in USUARIOS_AUTORIZADOS and USUARIOS_AUTORIZADOS[nome_input] == celular_input:
                st.session_state.logado = True
                st.session_state.usuario_nome = nome_input
                st.rerun()
            else:
                st.error("Usuário não cadastrado ou dados incorretos.")
        st.markdown('</div>', unsafe_allow_html=True)

if not st.session_state.logado:
    tela_login()
else:
    # Barra Lateral
    st.sidebar.write(f"👤 Usuário: **{st.session_state.usuario_nome}**")
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    # --- FUNÇÕES DE APOIO ---
    def formatar_br(valor, casas=2):
        try:
            if pd.isna(valor): return "0"
            return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except: return str(valor)

    def exportar_pdf(dados_cidade, endereco, obs, avaliacoes, concorrencia, polos, caracteristicas, foto_arquivo, perc_final, p_merc_txt, p_ponto_txt):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_margins(10, 10, 10)
        
        def clean(txt):
            if txt is None: return ""
            t = str(txt).replace('\u2013', '-').replace('\u2014', '-').replace('\u2022', '*')
            return t.encode('windows-1252', 'replace').decode('windows-1252')

        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 6, txt=clean("Relatório de Expansão - Análise de Ponto"), ln=True, align='C')
        
        pdf.set_fill_color(30, 33, 48)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 8, txt=clean(f"ADERÊNCIA TOTAL: {perc_final}"), ln=True, align='C', fill=True)
        
        pdf.set_fill_color(240, 240, 240)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(0, 6, txt=clean(f"Mercado: {p_merc_txt} | Ponto: {p_ponto_txt}"), ln=True, align='C', fill=True)
        
        pdf.set_text_color(0, 0, 0)
        pdf.ln(5)

        # 1. Mercado
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 5, txt="1. DADOS DO MERCADO", ln=True)
        pdf.set_font("Arial", "", 9)
        pdf.cell(0, 5, txt=clean(f"Cidade: {dados_cidade.get('Município', 'N/A')} - {dados_cidade.get('UF', '')}"), ln=True)
        
        # 2. Localização
        pdf.ln(2)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 5, txt="2. LOCALIZAÇÃO", ln=True)
        pdf.set_font("Arial", "", 8)
        pdf.multi_cell(0, 4, txt=clean(f"Endereço: {endereco}"))
        
        # 3. Análise Técnica
        pdf.ln(2)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 5, txt="3. ANÁLISE TÉCNICA", ln=True)
        y_tec = pdf.get_y()
        pdf.set_font("Arial", "", 8)
        for k, v in avaliacoes.items(): pdf.cell(60, 4, txt=clean(f"- {k}: {v}"), ln=True)
        pdf.set_y(y_tec)
        pdf.set_x(100)
        for k, v in caracteristicas.items():
            pdf.set_x(100)
            pdf.cell(80, 4, txt=clean(f"- {k}: {v}"), ln=True)

        pdf.ln(5)
        pdf.set_font("Arial", "B", 9)
        pdf.cell(0, 5, txt="OBSERVAÇÕES:", ln=True)
        pdf.set_font("Arial", "", 8)
        pdf.multi_cell(0, 4, txt=clean(obs))

        if foto_arquivo:
            try:
                img = Image.open(foto_arquivo)
                if img.mode in ("RGBA", "P"): img = img.convert("RGB")
                img_path = "temp_pdf_foto.jpg"
                img.save(img_path, quality=85)
                pdf.image(img_path, x=10, y=pdf.get_y()+5, w=90)
                os.remove(img_path)
            except: pass
            
        return pdf.output(dest='S').encode('latin-1', errors='replace')

    # --- ABAS ---
    tab_radar, tab_analytics = st.tabs(["🎯 Radar de Expansão", "📊 Analytics de Performance"])

    with tab_radar:
        @st.cache_data
        def load_ranking():
            try:
                # Procura a linha onde começa o cabeçalho real
                df_raw = pd.read_excel('Ranking PCA.xlsx', header=None)
                header_idx = 0
                for i, row in df_raw.iterrows():
                    if "Município" in [str(val).strip() for val in row.values]:
                        header_idx = i
                        break
                df = pd.read_excel('Ranking PCA.xlsx', skiprows=header_idx)
                df.columns = [str(c).strip() for c in df.columns]
                return df
            except: return None

        df_pca = load_ranking()
        if df_pca is not None:
            cidades = sorted(df_pca['Município'].dropna().unique())
            cidade_sel = st.selectbox("Selecione o município:", cidades, index=None)
            
            if cidade_sel:
                dados = df_pca[df_pca['Município'] == cidade_sel].iloc[0]
                uf = dados.get('UF', '')
                
                # Exibição de Métricas de Mercado
                c1, c2, c3 = st.columns(3)
                c1.metric("População", formatar_br(dados.get('População', 0), 0))
                c2.metric("Lojas Cabem", formatar_br(dados.get('Lojas Cabem', 0), 0))
                c3.metric("Demanda", formatar_br(dados.get('Demanda', 0), 2))

                st.markdown("---")
                # Coleta de dados do Ponto
                col_end, col_foto = st.columns(2)
                end_ponto = col_end.text_input("📍 Endereço/Link do Ponto:")
                foto_ponto = col_foto.file_uploader("📸 Foto:", type=['jpg','png','jpeg'])

                # Sliders de Avaliação
                st.subheader("Avaliação do Ponto")
                opcoes = ["Baixo", "Médio", "Alto"]
                
                s1, s2, s3 = st.columns(3)
                f_pess = s1.select_slider("Fluxo Pessoas", options=opcoes, value="Médio")
                f_veic = s2.select_slider("Fluxo Veículos", options=opcoes, value="Médio")
                c_rend = s3.select_slider("Renda Local", options=["Baixa", "Média", "Alta"], value="Média")

                st.subheader("Características")
                cp1, cp2, cp3 = st.columns(3)
                posicao = cp1.selectbox("Posição", ["Esquina +", "Esquina -", "Meio de quadra > 20m", "Meio de quadra < 20m", "Rótula"])
                vagas = cp2.selectbox("Vagas", [">10", "6 á 10", "1 á 5", "Não"])
                visib = cp3.selectbox("Visibilidade", ["Boa", "Ruim"])

                obs_vistoria = st.text_area("Observações da Vistoria:")

                # LÓGICA DE CÁLCULO (Score Mercado 30% + Ponto 70%)
                score_mercado = 0
                if dados.get('Lojas Cabem', 0) > 0: score_mercado += 15
                if dados.get('%Share', 0) <= 0.30: score_mercado += 15
                
                # Lógica Regional
                if uf == "RS":
                    if dados.get('População', 0) > 6000: score_mercado += 5
                else:
                    if dados.get('População', 0) > 15000: score_mercado += 5

                # Score Ponto (Simplificado para o exemplo, mas funcional)
                score_ponto = 35 # Base
                if f_pess == "Alto": score_ponto += 15
                if posicao == "Esquina +": score_ponto += 10
                if vagas == ">10": score_ponto += 10
                
                perc_total = min(100, score_mercado + score_ponto)

                if st.button("📊 GERAR RELATÓRIO PDF"):
                    aval = {"Fluxo Pessoas": f_pess, "Fluxo Veículos": f_veic, "Renda": c_rend}
                    carac = {"Posição": posicao, "Vagas": vagas, "Visibilidade": visib}
                    
                    p_merc_txt = f"{score_mercado}/30"
                    p_ponto_txt = f"{score_ponto}/70"
                    
                    pdf_bytes = exportar_pdf(dados, end_ponto, obs_vistoria, aval, {}, {}, carac, foto_ponto, f"{perc_total}%", p_merc_txt, p_ponto_txt)
                    
                    st.download_button("🚀 Baixar PDF", data=pdf_bytes, file_name=f"Relatorio_{cidade_sel}.pdf", mime="application/pdf")
        else:
            st.error("Arquivo 'Ranking PCA.xlsx' não encontrado.")

    with tab_analytics:
        # Mantém sua lógica de Analytics aqui...
        st.write("Módulo Analytics Ativo")
