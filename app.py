import streamlit as st
import pandas as pd

st.set_page_config(page_title="Radar de Expansão", layout="wide")

st.title("📍 Radar de Expansão - Farmácias")

st.write("Faça upload da sua base de dados")

arquivo = st.file_uploader("Escolha um arquivo Excel", type=["xlsx"])

if arquivo:
    df = pd.read_excel(arquivo)

    st.subheader("Dados")
    st.dataframe(df)

    # Exemplo de score
    if "População" in df.columns:
        df["Score"] = df["População"] * 0.5

        st.subheader("Ranking")
        st.dataframe(df.sort_values(by="Score", ascending=False))
