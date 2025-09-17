import streamlit as st
import pandas as pd
import datetime
import io


# --- Funções de Lógica ---
def atualizar_status_pagamento(df_alunos, df_pagamentos):
    hoje = datetime.date.today()

    alunos_cpf = df_alunos['CPF'].tolist()

    for cpf in alunos_cpf:
        pagamentos_aluno = df_pagamentos[df_pagamentos['CPF do Aluno'] == cpf]

        if pagamentos_aluno.empty:
            df_alunos.loc[df_alunos['CPF'] == cpf, 'Status Pagamento'] = 'Atrasado'
            continue

        ultimo_pagamento = pd.to_datetime(pagamentos_aluno['Data do Pagamento']).max().date()

        diferenca = (hoje.year - ultimo_pagamento.year) * 12 + (hoje.month - ultimo_pagamento.month)

        if diferenca <= 1:
            df_alunos.loc[df_alunos['CPF'] == cpf, 'Status Pagamento'] = 'Em dia'
        else:
            df_alunos.loc[df_alunos['CPF'] == cpf, 'Status Pagamento'] = 'Atrasado'

    return df_alunos


# Removido o cache para que os dados sempre sejam lidos do arquivo Excel.
def get_data_from_excel():
    try:
        df_alunos = pd.read_excel(
            io="alunos.xlsx",
            engine="openpyxl",
            sheet_name="Alunos",
            dtype={'CPF': str, 'Mensalidade': float}
        )
        df_pagamentos = pd.read_excel(
            io="alunos.xlsx",
            engine="openpyxl",
            sheet_name="Pagamentos",
            dtype={'CPF do Aluno': str}
        )
        return df_alunos, df_pagamentos
    except FileNotFoundError:
        return (
            pd.DataFrame(
                columns=['Nome do Aluno', 'CPF', 'Celular', 'Data de Matrícula', 'Mensalidade', 'Status Pagamento']),
            pd.DataFrame(columns=['CPF do Aluno', 'Data do Pagamento', 'Valor', 'Mês de Referência'])
        )


# --- Carregar dados (vai rodar a cada interação para manter os dados atualizados) ---
df_alunos_bruto, df_pagamentos = get_data_from_excel()
df_alunos = atualizar_status_pagamento(df_alunos_bruto, df_pagamentos)

# --- Título da Página ---
st.title("📊 Dashboard e Análise")

# --- Métricas Principais (KPIs) ---
total_alunos = df_alunos.shape[0]
total_faturamento_geral = df_pagamentos['Valor'].sum()
faturamento_potencial = df_alunos['Mensalidade'].sum()
alunos_atrasados = df_alunos[df_alunos['Status Pagamento'] == 'Atrasado'].shape[0]
valor_atrasados = df_alunos[df_alunos['Status Pagamento'] == 'Atrasado']['Mensalidade'].sum()

# Calcula a entrada do mês atual
hoje = datetime.date.today()
pagamentos_mes_atual = df_pagamentos[
    pd.to_datetime(df_pagamentos['Data do Pagamento']).dt.month == hoje.month
    ]
entrada_mes_atual = pagamentos_mes_atual['Valor'].sum()

col1, col2, col3, col4, col5, col6 = st.columns(6)
with col1:
    st.metric(label="Total de Alunos", value=total_alunos)
with col2:
    st.metric(label="Faturamento Potencial", value=f"R$ {faturamento_potencial:,.2f}")
with col3:
    st.metric(label="Entrada do Mês", value=f"R$ {entrada_mes_atual:,.2f}")
with col4:
    st.metric(label="Valor Total de Atrasados", value=f"R$ {valor_atrasados:,.2f}")
with col5:
    st.metric(label="Alunos Atrasados", value=alunos_atrasados)
with col6:
    st.metric(label="Faturamento Geral", value=f"R$ {total_faturamento_geral:,.2f}")

# --- Gráfico: Status de Pagamento dos Alunos ---
st.markdown("### Visão Geral do Status de Pagamento")

df_contagem_status = df_alunos['Status Pagamento'].value_counts().reset_index()
df_contagem_status.columns = ['Status', 'Quantidade']
st.bar_chart(df_contagem_status, x='Status', y='Quantidade', color="#008080")

# --- Status de Pagamento dos Alunos ---
st.markdown("### Lista de Alunos e Status de Pagamento")

df_status = df_alunos[['Nome do Aluno', 'Mensalidade', 'Status Pagamento']].copy()
df_status.loc[df_status['Status Pagamento'] == 'Em dia', 'Status Pagamento'] = '🟢 Em dia'
df_status.loc[df_status['Status Pagamento'] == 'Atrasado', 'Status Pagamento'] = '🔴 Atrasado'
df_status.loc[df_status['Status Pagamento'] == 'Novo', 'Status Pagamento'] = '🔵 Novo'

st.dataframe(df_status, width='stretch')

# --- Histórico de Faturamento por Mês ---
st.markdown("### Faturamento por Mês")
if not df_pagamentos.empty:
    df_pagamentos['Data do Pagamento'] = pd.to_datetime(df_pagamentos['Data do Pagamento'])
    df_faturamento_mensal = df_pagamentos.groupby(
        'Mês de Referência'
    )['Valor'].sum().reset_index()
    st.bar_chart(df_faturamento_mensal, x='Mês de Referência', y='Valor')
else:
    st.info("Nenhum dado de pagamento para exibir o gráfico.")

# --- Exportar Dados dos Alunos

csv = df_alunos.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Baixar dados de alunos",
    data=csv,
    file_name='lista_alunos.csv',
    mime='text/csv',
)
