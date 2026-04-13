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

    # --- FUNÇÕES DE AUXÍLIO ---
    def formatar_br(valor, casas=2):
        try:
            if pd.isna(valor): return "0"
            return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except: return str(valor)

    def exportar_pdf(dados_cidade, endereco, obs, avaliacoes, concorrencia, polos, caracteristicas, foto_arquivo, perc_final, score_mercado, score_ponto, p_merc_txt, p_ponto_txt):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_margins(10, 10, 10)
        
        def clean(txt):
            if txt is None: return ""
            return str(txt).encode('windows-1252', 'replace').decode('windows-1252')

        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 6, txt=clean("Relatório de Expansão - Análise de Ponto"), ln=True, align='C')
        
        pdf.set_fill_color(30, 33, 48)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 8, txt=clean(f"ADERÊNCIA TOTAL: {perc_final}"), ln=True, align='C', fill=True)
        
        pdf.set_fill_color(240, 240, 240)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(0, 6, txt=clean(f"Mercado da Cidade: {p_merc_txt}  |  Dados do Ponto: {p_ponto_txt}"), ln=True, align='C', fill=True)
        
        pdf.set_text_color(0, 0, 0)
        pdf.ln(4)

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
        
        y_topo = pdf.get_y()
        pdf.set_font("Arial", "", 8)
        # Resumo das avaliações no PDF
        for k, v in avaliacoes.items(): pdf.cell(60, 4, txt=clean(f"- {k}: {v}"), ln=True)
        
        if foto_arquivo:
            try:
                img = Image.open(foto_arquivo)
                if img.mode in ("RGBA", "P"): img = img.convert("RGB")
                img_path = "temp_pdf_foto.jpg"
                img.save(img_path, quality=85)
                pdf.image(img_path, x=10, y=pdf.get_y()+5, w=100)
                os.remove(img_path)
            except: pass
            
        return pdf.output(dest='S').encode('latin-1', errors='replace')

    # --- ABAS PRINCIPAIS ---
    tab_radar, tab_analytics = st.tabs(["🎯 Radar de Expansão", "📊 Analytics de Performance"])

    with tab_radar:
        @st.cache_data
        def load_ranking_pca():
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

        df_pca = load_ranking_pca()
        if df_pca is not None:
            cidades = sorted(df_pca['Município'].dropna().unique())
            cidade_selecionada = st.selectbox("Selecione o município:", options=cidades, index=None)
            
            if cidade_selecionada:
                dados = df_pca[df_pca['Município'] == cidade_selecionada].iloc[0]
                # Lógica de Score e UI Simplificada aqui (conforme seu código anterior)
                st.success(f"Cidade selecionada: {cidade_selecionada}")
                # [Inserir aqui os sliders e inputs do Radar...]
        else:
            st.error("Arquivo 'Ranking PCA.xlsx' não encontrado.")

    with tab_analytics:
        uploaded_file = st.file_uploader("📂 Suba a base das lojas (Excel)", type=['xlsx'])
        if uploaded_file:
            df_lojas = pd.read_excel(uploaded_file)
            df_lojas.columns = [str(c).strip() for c in df_lojas.columns]

            def localizar_coluna(lista_termos, nome_padrao):
                for col in df_lojas.columns:
                    if any(termo.upper() in col.upper() for termo in lista_termos):
                        return col
                return nome_padrao

            col_fat = localizar_coluna(["FATURAMENTO", "MAR'25"], "MÉDIA FATURAMENTO")
            col_dre = localizar_coluna(["DRE_AC", "FEV/26"], "DRE_AC")
            col_uf = localizar_coluna(["UF"], "UF")
            col_porte = localizar_coluna(["TAMANHO", "CIDADE"], "TAMANHO DA CIDADE")
            col_loja = localizar_coluna(["LOJAS", "NOME"], "LOJAS")

            df_lojas[col_fat] = pd.to_numeric(df_lojas[col_fat], errors='coerce').fillna(0)
            
            # --- KPIs ---
            st.subheader("Indicadores de Resumo")
            k1, k2, k3 = st.columns(3)
            k1.metric("Total Lojas", len(df_lojas))
            k2.metric("Vendas > 400k", len(df_lojas[df_lojas[col_fat] >= 400000]))
            k3.metric("DRE Negativo", len(df_lojas[df_lojas[col_dre] < 0]) if col_dre in df_lojas.columns else 0)

            # --- GRÁFICOS DNA ---
            def classificar(row):
                f = row[col_fat]
                d = row[col_dre] if col_dre in df_lojas.columns else 0
                if f < 400000: return '🔴 Ruim' if d < 0 else '🟡 Baixa'
                return '💎 Alta'

            df_lojas['Performance'] = df_lojas.apply(classificar, axis=1)
            
            analise_alvo = st.selectbox("Analisar DNA por:", [col_porte, "POSIÇÃO DA LOJA"])
            stats = df_lojas.groupby([analise_alvo, 'Performance']).size().reset_index(name='contagem')
            totais = df_lojas.groupby(analise_alvo).size().reset_index(name='total_grupo')
            stats = stats.merge(totais, on=analise_alvo)
            stats['porcentagem'] = (stats['contagem'] / stats['total_grupo'] * 100).round(1)
            stats['texto_barra'] = "Total: " + stats['total_grupo'].astype(str) + "<br>" + stats['Performance'] + ": " + stats['porcentagem'].astype(str) + "%"

            fig = px.bar(stats, x=analise_alvo, y='contagem', color='Performance', barmode='group', text='texto_barra',
                         color_discrete_map={'💎 Alta': '#27ae60', '🟡 Baixa': '#f1c40f', '🔴 Ruim': '#e74c3c'})
            st.plotly_chart(fig, use_container_width=True)
