import pandas as pd
import streamlit as st
import unicodedata

# Estilo CSS personalizado
st.markdown("""
    <style>
    .main { max-width: 90%; margin: 0 auto; }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Análise de Reclamações Mensais")
st.markdown("Carregue a base de dados CSV e visualize a variação mensal por segmento e natureza.")

uploaded_file = st.file_uploader("📁 Escolha um arquivo CSV", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, delimiter=";", encoding='latin-1')

    # Padroniza nomes de colunas
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.normalize('NFKD')
        .str.encode('ascii', errors='ignore')
        .str.decode('utf-8')
    )

    # Mapeia abreviações de mês para nomes completos
    meses_completos = {
        'jan': 'janeiro', 'fev': 'fevereiro', 'mar': 'março',
        'abr': 'abril', 'mai': 'maio', 'jun': 'junho',
        'jul': 'julho', 'ago': 'agosto', 'set': 'setembro',
        'out': 'outubro', 'nov': 'novembro', 'dez': 'dezembro'
    }

    if 'mes' in df.columns:
        df['mes'] = df['mes'].str.lower().map(meses_completos)

        ordem_meses = list(meses_completos.values())
        df['mes'] = pd.Categorical(df['mes'], categories=ordem_meses, ordered=True)

        # Filtros
        st.sidebar.header("🎯 Filtros")
        ano_atual = st.sidebar.selectbox('Selecione o ano', sorted(df['ano'].unique(), reverse=True))
        mes_atual = st.sidebar.selectbox('Selecione o mês atual', ordem_meses)
        mes_anterior = st.sidebar.selectbox('Selecione o mês anterior', ordem_meses)
        canal_opcao = st.sidebar.radio('Selecione o canal', ['Todos', 'PROCON', 'OUVIDORIA'])

        df_atual = df[(df['mes'] == mes_atual) & (df['ano'] == ano_atual)]
        df_anterior = df[(df['mes'] == mes_anterior) & (df['ano'] == ano_atual)]

        if canal_opcao == 'PROCON':
            df_atual = df_atual[df_atual['ds_canal'] == 'PROCON']
            df_anterior = df_anterior[df_anterior['ds_canal'] == 'PROCON']
        elif canal_opcao == 'OUVIDORIA':
            df_atual = df_atual[df_atual['ds_canal'] != 'PROCON']
            df_anterior = df_anterior[df_anterior['ds_canal'] != 'PROCON']

        total_atual = df_atual.shape[0]
        total_anterior = df_anterior.shape[0]
        variacao = ((total_atual - total_anterior) / total_anterior * 100) if total_anterior else 0

        st.divider()
        col1, col2, col3 = st.columns(3)
        col1.metric("📅 Mês Atual", mes_atual.capitalize())
        col2.metric("Total Reclamações", total_atual)
        col3.metric("Variação (%)", f"{variacao:.2f}%", delta_color="inverse" if variacao < 0 else "normal")

        st.markdown(f"No geral, houve {'um aumento' if variacao > 0 else 'uma redução'} de **{abs(variacao):.2f}%** nas reclamações ao comparar **{mes_anterior.capitalize()}** com **{mes_atual.capitalize()}**.")
        st.divider()

        segmentos = df['segmento'].dropna().unique()
        for segmento in segmentos:
            with st.expander(f"🔍 Segmento: {segmento}", expanded=False):
                meses_ate_atual = ordem_meses[:ordem_meses.index(mes_atual) + 1]

                total_seg_acumulado = df[(df['ano'] == ano_atual) & (df['segmento'] == segmento) & (df['mes'].isin(meses_ate_atual))].shape[0]
                total_geral_acumulado = df[(df['ano'] == ano_atual) & (df['mes'].isin(meses_ate_atual))].shape[0]
                perc_rep = (total_seg_acumulado / total_geral_acumulado) * 100 if total_geral_acumulado else 0

                st.markdown(f"📈 Até **{mes_atual.capitalize()}**, este segmento representa **{perc_rep:.2f}%** do total de reclamações no ano.")

                total_atual_seg = df_atual[df_atual['segmento'] == segmento].shape[0]
                total_anterior_seg = df_anterior[df_anterior['segmento'] == segmento].shape[0]
                variacao_seg = ((total_atual_seg - total_anterior_seg) / total_anterior_seg) * 100 if total_anterior_seg else 0

                st.metric("Variação de Reclamações", f"{variacao_seg:.2f}%", delta_color="inverse" if variacao_seg < 0 else "normal")

                # Naturezas
                nat_atual = df_atual[df_atual['segmento'] == segmento]['natureza'].value_counts()
                nat_anterior = df_anterior[df_anterior['segmento'] == segmento]['natureza'].value_counts()
                df_natureza = pd.DataFrame({'Atual': nat_atual, 'Anterior': nat_anterior}).fillna(0)
                df_natureza['Variação'] = df_natureza['Atual'] - df_natureza['Anterior']
                df_natureza = df_natureza.reindex(df_natureza['Variação'].abs().sort_values(ascending=False).index).head(3)

                for natureza, row in df_natureza.iterrows():
                    total_nat_atual = row['Atual']
                    total_nat_ant = row['Anterior']
                    delta = row['Variação']
                    delta_perc = (delta / total_nat_ant * 100) if total_nat_ant else 100

                    st.markdown(f"**Natureza:** {natureza}")
                    st.write(f"De **{total_nat_ant:.0f}** para **{total_nat_atual:.0f}** reclamações (**{'+' if delta > 0 else ''}{delta:.0f} | {delta_perc:.2f}%**)")

                    # Motivos
                    motivos_atual = df_atual[(df_atual['segmento'] == segmento) & (df_atual['natureza'] == natureza)]['motivo'].value_counts()
                    motivos_anterior = df_anterior[(df_anterior['segmento'] == segmento) & (df_anterior['natureza'] == natureza)]['motivo'].value_counts()
                    df_motivos = pd.DataFrame({'Atual': motivos_atual, 'Anterior': motivos_anterior}).fillna(0)
                    df_motivos['Variação'] = df_motivos['Atual'] - df_motivos['Anterior']
                    df_motivos = df_motivos.reindex(df_motivos['Variação'].abs().sort_values(ascending=False).index).head(3)

                    st.write("🔹 **Motivos mais relevantes:**")
                    for motivo, linha in df_motivos.iterrows():
                        st.markdown(f"- {motivo}: {linha['Anterior']:.0f} → {linha['Atual']:.0f} (**{'+' if linha['Variação'] > 0 else ''}{linha['Variação']:.0f}**)")

        st.divider()
        st.caption("© Gabriel Luis - Análise de Dados | Ouvidoria 2025")