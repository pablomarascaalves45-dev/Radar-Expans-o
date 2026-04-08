import streamlit as st
import pandas as pd

# Configuração da página para o modo mobile/dark
st.set_page_config(page_title="Radar de Expansão", layout="centered")

# Estilização para ficar parecido com o print original
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 2rem; color: #ffffff; }
    label[data-testid="stMetricLabel"] { font-size: 1.1rem; color: #9da5b1; }
    </style>
    """, unsafe_allow_html=True)

# Título do App
st.title("🎯 Radar de Expansão")
st.subheader("1. Mercado da Cidade")

# Função para carregar os dados
@st.cache_data
def load_data():
    # Substitua 'planilha.csv' pelo nome exato do seu arquivo no GitHub
    df = pd.read_csv('planilha.csv', sep=',') 
    # Limpeza básica: remover espaços extras nos nomes das colunas
    df.columns = df.columns.str.strip()
    return df

try:
    df = load_data()

    # Barra de busca por cidade
    cidade_selecionada = st.selectbox(
        "Buscar Município:",
        options=sorted(df['municipio'].unique()),
        index=0
    )

    # Filtrar dados da cidade escolhida
    dados = df[df['municipio'] == cidade_selecionada].iloc[0]

    st.write("---")

    # Exibição das métricas em colunas
    col1, col2 = st.columns(2)

    with col1:
        st.metric(label="População", value=f"{int(dados['populacao']):,}".replace(',', '.'))
        st.metric(label="Share da Cidade", value=f"{dados['share']}%")

    with col2:
        # Aqui você pode exibir o valor direto da planilha ou fazer um cálculo
        # Exemplo: se na sua planilha a coluna se chama 'lojas_potencial'
        st.metric(label="Quantas lojas cabem", value=f"{int(dados['vagas_lojas'])}")
    
    st.write("---")
    
    # Rodapé informativo
    st.caption(f"Dados atualizados para a região de {cidade_selecionada}")

except Exception as e:
    st.error(f"Erro ao carregar os dados. Verifique se os nomes das colunas na planilha estão corretos. Erro: {e}")
