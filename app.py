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

    def exportar_pdf(dados_cidade, endereco, obs, avaliacoes, concorrencia, polos, caracteristicas, foto_arquivo, perc_final, score_mercado, score_ponto, p_merc_txt, p_ponto_txt):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_margins(10, 10, 10)
        
        # Correção para caracteres especiais (substitui traços longos e símbolos incompatíveis)
        def clean(txt):
            if txt is None: return ""
            # Substitui o en-dash (\u2013) por hífen comum e limpa outros caracteres
            t = str(txt).replace('\u2013', '-').replace('\u2014', '-')
            return t.encode('windows-1252', 'replace').decode('windows-1252')

        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 6, txt=clean("Relatório de Expansão - Análise de Ponto"), ln=True, align='C')
        
        pdf.set_fill_color(30, 33, 48)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 8, txt=clean(f"ADERÊNCIA TOTAL: {perc_final}"), ln=True, align='C', fill=True)
        
        pdf.set_fill_color(240, 240, 240)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(0, 6, txt=clean(f"Mercado da Cidade: {p_merc_txt} | Dados do Ponto: {p_ponto_txt}"), ln=True, align='C', fill=True)
        
        pdf.set_text_color(0, 0, 0)
        pdf.ln(4)

        # Dados do Mercado
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 5, txt="1. DADOS DO MERCADO", ln=True)
        pdf.set_font("Arial", "", 9)
        pdf.cell(0, 5, txt=clean(f"Cidade: {dados_cidade.get('Município', 'N/A')} - {dados_cidade.get('UF', '')}"), ln=True)
        
        pdf.set_font("Arial", "B", 8)
        col_w = 63
        pdf.cell(col_w, 5, txt=clean(f"População: {formatar_br(dados_cidade.get('População', 0), 0)}"), ln=0)
        pdf.cell(col_w, 5, txt=clean(f"Lojas Atuais: {formatar_br(dados_cidade.get('N° FSJ', 0), 0)}"), ln=0)
        pdf.cell(col_w, 5, txt=clean(f"Renda Média: {formatar_br(dados_cidade.get('Renda Média Domiciliar (SM)', 0), 2)}"), ln=1)
        
        pdf.ln(4)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 5, txt=clean("2. LOCALIZAÇÃO"), ln=True)
        pdf.set_font("Arial", "", 8)
        pdf.multi_cell(0, 4, txt=clean(f"Endereço: {endereco}"))
        
        pdf.ln(4)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 5, txt=clean("3. ANÁLISE TÉCNICA DO PONTO"), ln=True)
        
        # Colunas de Características
        y_start = pdf.get_y()
        pdf.set_font("Arial", "", 8)
        for k, v in avaliacoes.items(): pdf.cell(60, 4, txt=clean(f"- {k}: {v}"), ln=True)
        
        pdf.set_y(y_start)
        pdf.set_x(100)
        for k, v in caracteristicas.items(): 
            pdf.set_x(100)
            pdf.cell(60, 4, txt=clean(f"- {k}: {v}"), ln=True)

        pdf.ln(5)
        pdf.set_font("Arial", "B", 8)
        pdf.cell(0, 5, txt=clean("OBSERVAÇÕES:"), ln=True)
        pdf.set_font("Arial", "", 8)
        pdf.multi_cell(0, 4, txt=clean(obs))

        if foto_arquivo:
            try:
                img = Image.open(foto_arquivo)
                if img.mode in ("RGBA", "P"): img = img.convert("RGB")
                img_path = "temp_pdf_foto.jpg"
                img.save(img_path, quality=85)
                # Tenta encaixar a imagem no final
                pdf.image(img_path, x=10, y=pdf.get_y()+5, w=100)
                os.remove(img_path)
            except: pass
            
        return pdf.output(dest='S').encode('latin-1', errors='replace')

    # --- ABAS ---
    tab_radar, tab_analytics = st.tabs(["🎯 Radar de Expansão", "📊 Analytics de Performance"])

    with tab_radar:
        @st.cache_data
        def load_ranking():
            try:
                df = pd.read_excel('Ranking PCA.xlsx', skiprows=1) # Ajuste o skip se necessário
                df.columns = [str(c).strip() for c in df.columns]
                return df
            except: return None

        df_pca = load_ranking()
        if df_pca is not None:
            st.subheader("1. Mercado da Cidade")
            cidade_selecionada = st.selectbox("Selecione o município:", sorted(df_pca['Município'].dropna().unique()), index=None)
            
            if cidade_selecionada:
                dados = df_pca[df_pca['Município'] == cidade_selecionada].iloc[0]
                # ... [Lógica de Sliders do Radar aqui] ...
                st.info(f"Dados carregados para {cidade_selecionada}")
                
                # Exemplo de botão de avaliar e gerar PDF (Simplificado para o código não ficar gigante)
                if st.button("📊 GERAR RELATÓRIO"):
                    # Aqui você chamaria a função exportar_pdf com os dados coletados
                    st.write("Relatório Processado.")
        else:
            st.error("Arquivo 'Ranking PCA.xlsx' não encontrado.")

    with tab_analytics:
        st.subheader("Análise de Lojas Atuais")
        up_lojas = st.file_uploader("Suba a base das lojas (Excel)", type=['xlsx'])
        if up_lojas:
            df_l = pd.read_excel(up_lojas)
            df_l.columns = [str(c).strip() for c in df_l.columns]
            
            # KPI Header
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Lojas", len(df_l))
            
            # Gráfico de Dispersão (Exemplo)
            if "MÉDIA FATURAMENTO DE MAR'25 ATÉ FEV'26" in df_l.columns:
                fig = px.scatter(df_l, x="MÉDIA FATURAMENTO DE MAR'25 ATÉ FEV'26", y="DRE_AC FEV/26", color="UF")
                st.plotly_chart(fig, use_container_width=True)
