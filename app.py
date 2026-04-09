if df is not None:
    st.title("🎯 Radar de Expansão")
    
    st.subheader("1. Mercado da Cidade")
    cidades = sorted(df['Município'].dropna().unique())
    col_cidade, col_uf = st.columns([4, 1])
    
    with col_cidade:
        # A variável aqui é cidade_selecionada
        cidade_selecionada = st.selectbox("Selecione o município:", options=cidades)
        # Ajustado de 'ciudad' para 'cidade' para corrigir o NameError
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

    # --- LÓGICA DE SCORE DE MERCADO COM AS PENALIZAÇÕES ---
    score_mercado = (15 if lojas_cabem_valor > 0 else 0) + (15 if share_valor_original <= 0.30 else 0)

    # Penalizações SC e PR
    if estado_cidade in ["SC", "PR"]:
        if demanda_cidade < 2000000:
            score_mercado -= 15
        if populacao_cidade < 15000:
            score_mercado -= 15

    # Penalizações RS
    elif estado_cidade == "RS":
        if demanda_cidade < 1200000:
            score_mercado -= 20
        if populacao_cidade < 6000:
            score_mercado -= 20
