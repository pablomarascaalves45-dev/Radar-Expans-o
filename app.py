import streamlit as st
import pandas as pd

st.set_page_config(page_title="Score Expansão Farmácia", layout="wide")

st.title("📊 Radar de Expansão - Score de Pontos")

# Upload da planilha
file = st.file_uploader("📂 Envie sua planilha Excel", type=["xlsx"])

if file:
    df = pd.read_excel(file)

    st.subheader("📋 Dados carregados")
    st.dataframe(df)

    # --- MAPEAMENTOS ---
    mapa_fluxo = {"Alto": 5, "Médio": 3, "Baixo": 1}
    mapa_padrao = {"Alto": 5, "Médio": 3, "Baixo": 1}

    # --- POTENCIAL ---
    df["Fluxo_score"] = df["Fluxo"].map(mapa_fluxo)
    df["Populacao_score"] = df["Populacao"].map(mapa_padrao)
    df["Renda_score"] = df["Renda"].map(mapa_padrao)
    df["Veiculos_score"] = df["Veiculos"].map(mapa_padrao)

    df["Potencial"] = (
        df["Fluxo_score"] * 0.4 +
        df["Populacao_score"] * 0.3 +
        df["Renda_score"] * 0.2 +
        df["Veiculos_score"] * 0.1
    )

    # --- CONCORRÊNCIA (PENALIDADE) ---
    def score_concorrencia(row):
        score = 0
        
        # Redes
        if row["Concorrentes_Rede"] > 3:
            score -= 4
        elif row["Concorrentes_Rede"] >= 1:
            score -= 2
        
        # Próprias (FSJ)
        if row["FSJ"] > 3:
            score -= 5
        elif row["FSJ"] >= 1:
            score -= 3
        
        # Independentes
        if row["Independentes"] > 10:
            score -= 2
        elif row["Independentes"] >= 5:
            score -= 1
        
        return score

    df["Concorrencia"] = df.apply(score_concorrencia, axis=1)

    # --- QUALIDADE DO PONTO ---
    df["Visibilidade_score"] = df["Visibilidade"].map(mapa_padrao)
    df["Acesso_score"] = df["Acesso"].map(mapa_padrao)
    df["Regiao_score"] = df["Regiao"].map(mapa_padrao)

    df["Qualidade"] = (
        df["Visibilidade_score"] * 0.5 +
        df["Acesso_score"] * 0.3 +
        df["Regiao_score"] * 0.2
    )

    # --- SCORE FINAL ---
    df["Score_Final"] = (
        df["Potencial"] * 0.5 +
        df["Concorrencia"] * 0.3 +
        df["Qualidade"] * 0.2
    )

    # --- CLASSIFICAÇÃO ---
    def classificar(score):
        if score >= 4:
            return "🟢 Expansão"
        elif score >= 3:
            return "🟡 Avaliar"
        elif score >= 2:
            return "🔴 Risco"
        else:
            return "❌ Descartar"

    df["Decisao"] = df["Score_Final"].apply(classificar)

    # --- RESULTADO ---
    st.subheader("🏆 Ranking de Pontos")
    df = df.sort_values(by="Score_Final", ascending=False)
    st.dataframe(df)

    # --- GRÁFICO ---
    st.subheader("📈 Distribuição de Score")
    st.bar_chart(df["Score_Final"])
