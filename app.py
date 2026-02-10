import streamlit as st
import pandas as pd
from utils import (
    carregar_csv_seguro,   # enquanto a leitura ainda vem do mesmo lugar
    excluir_linha_seguro,
    gerar_id,
    somar_coluna,
    mostrar_filtro,
    aplicar_filtro,
    salvar_planilha
)

st.set_page_config(page_title="Atlas Financeiro", layout="wide")
st.title("Atlas Financeiro 🗺️")

# =========================
# CARREGAMENTO
# =========================

mov = carregar_csv_seguro("movimentacoes.csv")
contas = carregar_csv_seguro("contas_futuras.csv")
receitas = carregar_csv_seguro("receitas_futuras.csv")
invest = carregar_csv_seguro("investimentos.csv")

mostrar_filtro()

mov = aplicar_filtro(mov, "data")
contas = aplicar_filtro(contas, "data_inicio")
receitas = aplicar_filtro(receitas, "data_prevista")
invest = aplicar_filtro(invest, "data")

# =========================
# SIDEBAR
# =========================

pagina = st.sidebar.radio(
    "Navegação",
    [
        "Dashboard",
        "Movimentações",
        "Contas Futuras",
        "Receitas Futuras",
        "Investimentos"
    ]
)

# =========================
# DASHBOARD
# =========================

if pagina == "Dashboard":

    entradas = mov[mov["tipo"] == "entrada"]
    saidas = mov[mov["tipo"] == "saída"]

    saldo = somar_coluna(entradas, "valor") - somar_coluna(saidas, "valor")
    total_saidas = somar_coluna(saidas, "valor")
    total_contas = somar_coluna(contas, "valor_parcela")
    receitas_pendentes = receitas[receitas["status"] == "pendente"]
    total_receitas_futuras = somar_coluna(receitas_pendentes, "valor")
    total_investido = somar_coluna(invest, "valor")

    col1, col2, col3 = st.columns(3)
    col1.metric("Saldo Atual", f"R$ {saldo:,.2f}")
    col2.metric("Total em Contas", f"R$ {total_contas:,.2f}")
    col3.metric("Total Investido", f"R$ {total_investido:,.2f}")

    col4, col5, col6 = st.columns(3)
    col4.metric("Total em Saídas", f"R$ {total_saidas:,.2f}")
    col5.metric("Receitas Futuras", f"R$ {total_receitas_futuras:,.2f}")

    gasto_medio = total_saidas if total_saidas > 0 else 0
    meses = saldo / gasto_medio if gasto_medio > 0 else 0
    col6.metric("Quanto tempo o dinheiro dura", f"{meses:.1f} meses")

# =========================
# MOVIMENTAÇÕES
# =========================

elif pagina == "Movimentações":

    st.subheader("Nova Movimentação")

    with st.form("nova_mov"):
        tipo = st.selectbox("Tipo", ["entrada", "saída"])
        categoria = st.text_input("Categoria")
        descricao = st.text_input("Descrição")
        valor = st.number_input("Valor", min_value=0.0)
        forma = st.selectbox(
            "Forma de Pagamento",
            ["Pix", "Débito", "Dinheiro", "Crédito Nubank", "Crédito Inter"]
        )
        data = st.date_input("Data")

        if st.form_submit_button("Adicionar"):
            if not descricao.strip() or valor <= 0:
                st.error("Preencha descrição e valor válido.")
                st.stop()

            nova = {
                "id": gerar_id(),
                "data": data.isoformat(),
                "tipo": tipo,
                "categoria": categoria,
                "descricao": descricao,
                "valor": valor,
                "forma_pagamento": forma
            }

            mov = pd.concat([mov, pd.DataFrame([nova])], ignore_index=True)
            salvar_planilha(mov, "movimentacoes")
            st.success("Movimentação adicionada")
            st.experimental_rerun()

    st.divider()
    st.subheader("Histórico")

    if mov.empty:
        st.info("Nenhuma movimentação registrada.")
    else:
        for _, row in mov.iterrows():
            cols = st.columns([4, 2, 2, 1])
            cols[0].write(f"{row['data']} — {row['descricao']}")
            cols[1].write(row["categoria"])
            cols[2].write(f"R$ {float(row['valor']):,.2f}")
            if cols[3].button("Excluir", key=row["id"]):
                mov = mov[mov["id"] != row["id"]]
                salvar_planilha(mov, "movimentacoes")
                st.experimental_rerun()

# =========================
# CONTAS FUTURAS
# =========================

elif pagina == "Contas Futuras":

    st.subheader("Nova Conta Futura")

    with st.form("nova_conta"):
        descricao = st.text_input("Descrição")
        valor = st.number_input("Valor da Parcela", min_value=0.0)
        total = st.number_input("Total de Parcelas", min_value=1, step=1)
        data = st.date_input("Data de Início")

        if st.form_submit_button("Adicionar"):
            if not descricao or valor <= 0:
                st.error("Dados inválidos.")
                st.stop()

            nova = {
                "id": gerar_id(),
                "descricao": descricao,
                "valor_parcela": valor,
                "total_parcelas": total,
                "parcelas_pagas": 0,
                "data_inicio": data.isoformat(),
                "status": "ativa"
            }

            contas = pd.concat([contas, pd.DataFrame([nova])], ignore_index=True)
            salvar_planilha(contas, "contas_futuras")
            st.success("Conta criada")
            st.experimental_rerun()

    st.divider()

    for _, row in contas.iterrows():
        cols = st.columns([4, 2, 2, 1])
        cols[0].write(row["descricao"])
        cols[1].write(f"{int(row['parcelas_pagas'])}/{int(row['total_parcelas'])}")
        cols[2].write(f"R$ {float(row['valor_parcela']):,.2f}")

        if row["status"] != "concluída":
            if cols[3].button("Pagar", key=row["id"]):

                idx = contas[contas["id"] == row["id"]].index[0]
                contas.at[idx, "parcelas_pagas"] += 1

                if contas.at[idx, "parcelas_pagas"] >= contas.at[idx, "total_parcelas"]:
                    contas.at[idx, "status"] = "concluída"

                salvar_planilha(contas, "contas_futuras")

                nova_saida = {
                    "id": gerar_id(),
                    "data": row["data_inicio"],
                    "tipo": "saída",
                    "categoria": "Conta Futura",
                    "descricao": row["descricao"],
                    "valor": row["valor_parcela"],
                    "forma_pagamento": "Automático"
                }

                mov = pd.concat([mov, pd.DataFrame([nova_saida])], ignore_index=True)
                salvar_planilha(mov, "movimentacoes")

                st.experimental_rerun()
        else:
            cols[3].write("✅")

# =========================
# RECEITAS FUTURAS
# =========================

elif pagina == "Receitas Futuras":

    st.subheader("Nova Receita Futura")

    with st.form("nova_receita"):
        descricao = st.text_input("Descrição")
        valor = st.number_input("Valor", min_value=0.0)
        data = st.date_input("Data Prevista")

        if st.form_submit_button("Adicionar"):
            if not descricao or valor <= 0:
                st.error("Dados inválidos.")
                st.stop()

            nova = {
                "id": gerar_id(),
                "descricao": descricao,
                "valor": valor,
                "data_prevista": data.isoformat(),
                "status": "pendente"
            }

            receitas = pd.concat([receitas, pd.DataFrame([nova])], ignore_index=True)
            salvar_planilha(receitas, "receitas_futuras")
            st.experimental_rerun()

    st.divider()

    for _, row in receitas.iterrows():
        cols = st.columns([4, 2, 1])
        cols[0].write(row["descricao"])
        cols[1].write(f"R$ {float(row['valor']):,.2f}")

        if row["status"] != "recebida":
            if cols[2].button("Receber", key=row["id"]):

                idx = receitas[receitas["id"] == row["id"]].index[0]
                receitas.at[idx, "status"] = "recebida"
                salvar_planilha(receitas, "receitas_futuras")

                nova_entrada = {
                    "id": gerar_id(),
                    "data": row["data_prevista"],
                    "tipo": "entrada",
                    "categoria": "Receita Futura",
                    "descricao": row["descricao"],
                    "valor": row["valor"],
                    "forma_pagamento": "Automático"
                }

                mov = pd.concat([mov, pd.DataFrame([nova_entrada])], ignore_index=True)
                salvar_planilha(mov, "movimentacoes")

                st.experimental_rerun()
        else:
            cols[2].write("✅")

# =========================
# INVESTIMENTOS
# =========================

elif pagina == "Investimentos":

    st.subheader("Novo Investimento / Reserva")

    with st.form("novo_invest"):
        tipo = st.selectbox("Tipo", ["investimento", "reserva"])
        categoria = st.text_input("Categoria")
        objetivo = st.text_input("Objetivo")
        valor = st.number_input("Valor", min_value=0.0)
        data = st.date_input("Data")

        if st.form_submit_button("Adicionar"):
            if not objetivo or valor <= 0:
                st.error("Dados inválidos.")
                st.stop()

            nova = {
                "id": gerar_id(),
                "tipo": tipo,
                "categoria": categoria,
                "objetivo": objetivo,
                "valor": valor,
                "data": data.isoformat()
            }

            invest = pd.concat([invest, pd.DataFrame([nova])], ignore_index=True)
            salvar_planilha(invest, "investimentos")
            st.experimental_rerun()

    st.divider()

    for _, row in invest.iterrows():
        cols = st.columns([4, 2])
        cols[0].write(f"{row['tipo']} — {row['objetivo']}")
        cols[1].write(f"R$ {float(row['valor']):,.2f}")
