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
            dtype={'CPF': str}
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
st.title("💸 Controle de Pagamentos")

# --- Seção de Controle de Pagamentos
st.markdown("## Registro de Pagamentos")

opcoes_alunos = df_alunos['Nome do Aluno'].unique().tolist()
opcoes_alunos.insert(0, "Selecione um aluno...")

with st.form("form_pagamento", clear_on_submit=True):
    aluno_selecionado = st.selectbox(
        "Aluno",
        options=opcoes_alunos
    )

    data_pagamento = st.date_input("Data do Pagamento")
    valor = st.number_input("Valor", min_value=0.0, format="%.2f")

    submit_button_pagamento = st.form_submit_button("Registrar Pagamento")

    if submit_button_pagamento:
        if aluno_selecionado == "Selecione um aluno...":
            st.error("Por favor, selecione um aluno.")
        else:
            cpf_aluno_selecionado = df_alunos[df_alunos['Nome do Aluno'] == aluno_selecionado]['CPF'].iloc[0]

            novo_pagamento = pd.DataFrame([{
                'CPF do Aluno': cpf_aluno_selecionado,
                'Data do Pagamento': data_pagamento,
                'Valor': valor,
                'Mês de Referência': data_pagamento.strftime('%B/%Y')
            }])

            try:
                df_pagamentos_atualizado = pd.concat([df_pagamentos, novo_pagamento], ignore_index=True)

                with pd.ExcelWriter("alunos.xlsx", mode="w", engine="openpyxl") as writer:
                    df_alunos.to_excel(writer, sheet_name="Alunos", index=False)
                    df_pagamentos_atualizado.to_excel(writer, sheet_name="Pagamentos", index=False)

                st.success(f"Pagamento de {aluno_selecionado} no valor de R${valor} registrado com sucesso!")
                st.rerun()

            except Exception as e:
                st.error(f"Erro ao salvar o pagamento: {e}")

st.subheader("Histórico de Pagamentos")
df_pagamentos_display = df_pagamentos.copy()
# Converte a coluna para o tipo datetime antes de formatar
if not df_pagamentos_display.empty:
    df_pagamentos_display['Data do Pagamento'] = pd.to_datetime(df_pagamentos_display['Data do Pagamento']).dt.strftime(
        '%d/%m/%Y')
st.dataframe(df_pagamentos_display, width='stretch')
