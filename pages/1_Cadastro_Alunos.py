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


@st.cache_data(show_spinner=False)
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


# --- Carregar dados (vai rodar apenas uma vez) ---
df_alunos_bruto, df_pagamentos = get_data_from_excel()
df_alunos = atualizar_status_pagamento(df_alunos_bruto, df_pagamentos)

# --- Título da Página ---
st.title("👨‍💻 Cadastro de Alunos")

# --- Verificação de Sucesso de Cadastro ---
if 'cadastro_sucesso' in st.session_state and st.session_state['cadastro_sucesso']:
    st.success(f"Aluno {st.session_state['nome_aluno_cadastrado']} cadastrado com sucesso!")
    del st.session_state['cadastro_sucesso']
    del st.session_state['nome_aluno_cadastrado']

# --- Formulário de Cadastro ---
with st.form("form_novo_aluno", clear_on_submit=True):
    nome_aluno = st.text_input("Nome do Aluno")
    cpf = st.text_input("CPF")
    celular = st.text_input("Celular")
    data_matricula = st.date_input("Data de Matrícula")
    mensalidade = st.number_input("Valor da Mensalidade", min_value=0.0, format="%.2f")

    col1, col2 = st.columns(2)
    with col1:
        submit_button = st.form_submit_button("Cadastrar Aluno")
    with col2:
        cancel_button = st.form_submit_button("Cancelar")

    if submit_button:
        if not nome_aluno:
            st.error("Por favor, preencha o nome do aluno.")
        else:
            novo_aluno = pd.DataFrame([{
                'Nome do Aluno': nome_aluno,
                'CPF': cpf,
                'Celular': celular,
                'Data de Matrícula': data_matricula,
                'Mensalidade': mensalidade,
                'Status Pagamento': 'Novo'
            }])

            try:
                df_alunos_existente = pd.read_excel(
                    "alunos.xlsx", sheet_name="Alunos", engine="openpyxl", dtype={'CPF': str}
                )
                df_atualizado = pd.concat(
                    [df_alunos_existente, novo_aluno], ignore_index=True
                )

                with pd.ExcelWriter("alunos.xlsx", mode="w", engine="openpyxl") as writer:
                    df_atualizado.to_excel(writer, sheet_name="Alunos", index=False)
                    df_pagamentos.to_excel(writer, sheet_name="Pagamentos", index=False)

                st.session_state['cadastro_sucesso'] = True
                st.session_state['nome_aluno_cadastrado'] = nome_aluno
                st.rerun()

            except Exception as e:
                st.error(f"Erro ao salvar o aluno: {e}")

st.subheader("Lista de Alunos Cadastrados")
df_display = df_alunos.copy()
# Converte a coluna para o tipo datetime para que .dt funcione
df_display['Data de Matrícula'] = pd.to_datetime(df_display['Data de Matrícula'])
df_display['Data de Matrícula'] = df_display['Data de Matrícula'].dt.strftime('%d/%m/%Y')
st.dataframe(df_display, width='stretch')
