import streamlit as st
import pandas as pd
import plotly.express as px
import openai

# --- Configuração da Página ---
st.set_page_config(page_title="Diagnóstico com IA", layout="wide")



def identificar_colunas(df):
    """Tenta mapear automaticamente as colunas padrões."""
    colunas = df.columns.str.lower()
    mapeamento = {}

    # Colunas comuns para identificação
    colunas_padrao = {
        'id_tarefa': ['id', 'task id', 'processoid'],
        'nome_tarefa': ['tarefa', 'descrição', 'descricao', 'task name'],
        'cliente': ['cliente', 'nomecliente', 'client name'],
        'responsavel': ['executor', 'assignee', 'responsável'],
        'data_prevista_conclusao': ['due date', 'prazofatal', 'data prevista', 'prazo'],
        'data_real_conclusao': ['completion date', 'datafinalizacao', 'data de conclusão']
    }

    for padrao, possiveis_nomes in colunas_padrao.items():
        for nome in possiveis_nomes:
            for col in df.columns:
                if nome.strip().lower() in col.strip().lower():
                    mapeamento[padrao] = col
                    break
            if padrao in mapeamento:
                break

    if len(mapeamento) < len(colunas_padrao):
        st.warning("⚠️ Algumas colunas esperadas não foram encontradas. Verifique sua planilha.")
        st.write("Colunas encontradas:", df.columns.tolist())
        st.write("Mapeamento parcial:", mapeamento)

    return df.rename(columns=mapeamento)


# Upload
st.title("🔍 Diagnóstico Inteligente")
arquivo = st.file_uploader("Envie uma planilha CSV ou Excel")

if arquivo:
    df = pd.read_excel(arquivo) if arquivo.name.endswith(".xlsx") else pd.read_csv(arquivo)
    df = identificar_colunas(df)

    if 'data_prevista_conclusao' in df.columns and 'data_real_conclusao' in df.columns:
        st.success("Colunas mapeadas com sucesso!")
        st.dataframe(df.head())
    else:
        st.error("Colunas essenciais não encontradas.")
