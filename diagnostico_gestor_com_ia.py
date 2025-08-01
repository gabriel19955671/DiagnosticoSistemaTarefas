import streamlit as st
import pandas as pd
import plotly.express as px
import openai

# --- Configuração da Página ---
st.set_page_config(page_title="Diagnóstico com IA", layout="wide")

# --- Função para identificar colunas automaticamente ---
def identificar_colunas(df):
    colunas = df.columns.str.lower()
    mapeamento = {}

    colunas_padrao = {
        'id_tarefa': ['id', 'task id', 'processoid', 'tarefa - id', 'tarefa - desconsiderada para sempre?'],
        'nome_tarefa': ['tarefa', 'descrição', 'descricao', 'task name', 'tarefa - nome', 'tarefa - data de vencimento.mês'],
        'cliente': ['cliente', 'nomecliente', 'client name', 'cliente - nome'],
        'responsavel': ['executor', 'assignee', 'responsável', 'tarefa - responsável', 'responsável - papel'],
        'data_prevista_conclusao': [
            'due date', 'prazofatal', 'data prevista', 'prazo',
            'tarefa - data de vencimento (completa)', 'tarefa - data de vencimento',
            'tarefa - no prazo?'
        ],
        'data_real_conclusao': [
            'completion date', 'datafinalizacao', 'data de conclusão',
            'tarefa - data de conclusão (completa)', 'tarefa - data de conclusão'
        ]
    }

    for padrao, possiveis_nomes in colunas_padrao.items():
        for nome in possiveis_nomes:
            for col in df.columns:
                if nome.strip().lower() in col.strip().lower():
                    mapeamento[padrao] = col
                    break
            if padrao in mapeamento:
                break

    if 'data_prevista_conclusao' not in mapeamento and 'tarefa - data de vencimento.ano' in df.columns and 'tarefa - data de vencimento.dia' in df.columns:
        df['data_prevista_conclusao'] = pd.to_datetime(df['tarefa - data de vencimento.ano'].astype(str) + '-' + df['tarefa - data de vencimento.mês'].astype(str) + '-' + df['tarefa - data de vencimento.dia'].astype(str), errors='coerce')
        mapeamento['data_prevista_conclusao'] = 'data_prevista_conclusao'

    if 'data_real_conclusao' not in mapeamento and 'tarefa - data de conclusão.ano' in df.columns and 'tarefa - data de conclusão.dia' in df.columns:
        df['data_real_conclusao'] = pd.to_datetime(df['tarefa - data de conclusão.ano'].astype(str) + '-' + df['tarefa - data de conclusão.mês'].astype(str) + '-' + df['tarefa - data de conclusão.dia'].astype(str), errors='coerce')
        mapeamento['data_real_conclusao'] = 'data_real_conclusao'

    st.subheader("🔍 Log de mapeamento de colunas")
    st.write("Colunas encontradas na planilha:", df.columns.tolist())
    st.write("Colunas mapeadas:", mapeamento)

    return df.rename(columns=mapeamento), mapeamento

# --- Funções Auxiliares ---
def categorizar_tarefa(nome_tarefa):
    nome_tarefa = str(nome_tarefa).lower()
    if any(keyword in nome_tarefa for keyword in ['dctf', 'sped', 'fiscal', 'imposto', 'das']):
        return 'Fiscal'
    elif any(keyword in nome_tarefa for keyword in ['balancete', 'contábil', 'conciliação']):
        return 'Contábil'
    elif any(keyword in nome_tarefa for keyword in ['folha', 'admissão', 'rescisão', 'esocial']):
        return 'Depto. Pessoal'
    else:
        return 'Outros'

def calcular_metricas(df):
    if 'data_prevista_conclusao' in df.columns:
        df['data_prevista_conclusao'] = pd.to_datetime(df['data_prevista_conclusao'], errors='coerce')
    if 'data_real_conclusao' in df.columns:
        df['data_real_conclusao'] = pd.to_datetime(df['data_real_conclusao'], errors='coerce')
    df['status_prazo'] = 'No Prazo'
    if 'data_real_conclusao' in df.columns and 'data_prevista_conclusao' in df.columns:
        df.loc[df['data_real_conclusao'] > df['data_prevista_conclusao'], 'status_prazo'] = 'Em Atraso'
        df.loc[df['data_real_conclusao'].isna(), 'status_prazo'] = 'Pendente'
        df['dias_de_atraso'] = (df['data_real_conclusao'] - df['data_prevista_conclusao']).dt.days
        df.loc[df['dias_de_atraso'] < 0, 'dias_de_atraso'] = 0
    else:
        df['dias_de_atraso'] = 0
    if 'nome_tarefa' in df.columns:
        df['tipo_tarefa'] = df['nome_tarefa'].apply(categorizar_tarefa)
    else:
        df['tipo_tarefa'] = 'Indefinido'
    if 'data_real_conclusao' in df.columns:
        df['mes_conclusao'] = df['data_real_conclusao'].dt.to_period('M').astype(str)
    else:
        df['mes_conclusao'] = 'Indefinido'
    return df

# --- Início da Interface ---
st.title("📊 Diagnóstico Inteligente com IA")

arquivo = st.file_uploader("Envie uma planilha CSV ou Excel")

if arquivo:
    df_bruto = pd.read_excel(arquivo) if arquivo.name.endswith(".xlsx") else pd.read_csv(arquivo)
    df_bruto, mapeamento = identificar_colunas(df_bruto)

    df_analise = calcular_metricas(df_bruto)
    st.success("✅ Dados processados com sucesso!")
    st.dataframe(df_analise.head())

    # Diagnóstico com IA
    st.markdown("---")
    st.subheader("📌 Diagnóstico Automático com IA")

    if st.button("Gerar Diagnóstico com IA"):
        with st.spinner("Gerando análise com inteligência artificial..."):
            colunas_para_resumo = [col for col in ['cliente', 'responsavel', 'status_prazo', 'tipo_tarefa', 'dias_de_atraso'] if col in df_analise.columns]
            resumo = df_analise[colunas_para_resumo].head(50).to_csv(index=False)
            prompt = f"""Você é um analista contábil. Avalie os dados a seguir e gere um diagnóstico sobre gargalos, atrasos e oportunidades de melhoria:\n{resumo}"""
            try:
                client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                resposta = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Você é um analista contábil especialista em produtividade."},
                        {"role": "user", "content": prompt}
                    ]
                )
                st.success("✅ Diagnóstico gerado com sucesso!")
                st.markdown(resposta.choices[0].message.content)
            except Exception as e:
                st.error(f"Erro ao gerar diagnóstico com IA: {e}")
