import os
import pandas as pd
from datetime import datetime
import uuid

BASE_DIR = "data"

if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)

CONTRATOS = {
    "movimentacoes.csv": [
        "id",
        "data",
        "tipo",
        "categoria",
        "descricao",
        "valor",
        "forma_pagamento"
    ],
    "contas_futuras.csv": [
        "id",
        "descricao",
        "valor_parcela",
        "total_parcelas",
        "parcelas_pagas",
        "data_inicio",
        "status"
    ],
    "receitas_futuras.csv": [
        "id",
        "descricao",
        "valor",
        "data_prevista",
        "status"
    ],
    "investimentos.csv": [
        "id",
        "tipo",
        "categoria",
        "objetivo",
        "valor",
        "data"
    ]
}


def _caminho_csv(nome_arquivo: str) -> str:
    return os.path.join(BASE_DIR, nome_arquivo)


def carregar_csv_seguro(nome_arquivo: str) -> pd.DataFrame:
    caminho = _caminho_csv(nome_arquivo)
    colunas = CONTRATOS[nome_arquivo]

    if not os.path.exists(caminho):
        df = pd.DataFrame(columns=colunas)
        df.to_csv(caminho, index=False)
        return df

    try:
        df = pd.read_csv(caminho)

        if df.empty and len(df.columns) == 0:
            df = pd.DataFrame(columns=colunas)

        for col in colunas:
            if col not in df.columns:
                df[col] = None

        df = df[colunas]

        df = df.fillna("")

        for c in ["valor", "valor_parcela", "total_parcelas", "parcelas_pagas"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

        return df

    except Exception:
        df = pd.DataFrame(columns=colunas)
        df.to_csv(caminho, index=False)
        return df


def salvar_csv_seguro(df: pd.DataFrame, nome_arquivo: str):
    caminho = _caminho_csv(nome_arquivo)
    colunas = CONTRATOS[nome_arquivo]

    if df is None or df.empty:
        df = pd.DataFrame(columns=colunas)
    else:
        df = df[colunas]

    if "id" in df.columns:
        df = df.drop_duplicates(subset="id", keep="first")

    df.reset_index(drop=True, inplace=True)
    df.to_csv(caminho, index=False)


def gerar_id() -> str:
    return str(uuid.uuid4())


def excluir_linha_seguro(df: pd.DataFrame, nome_arquivo: str, id_linha: str) -> pd.DataFrame:
    if df.empty:
        return df

    df = df[df["id"] != id_linha]
    salvar_csv_seguro(df, nome_arquivo)
    return df


def somar_coluna(df: pd.DataFrame, coluna: str) -> float:
    if df.empty or coluna not in df.columns:
        return 0.0
    return float(pd.to_numeric(df[coluna], errors="coerce").fillna(0).sum())


def media_coluna(df: pd.DataFrame, coluna: str) -> float:
    if df.empty or coluna not in df.columns:
        return 0.0
    valores = pd.to_numeric(df[coluna], errors="coerce").dropna()
    if valores.empty:
        return 0.0
    return float(valores.mean())


def hoje_str() -> str:
    return datetime.today().strftime("%Y-%m-%d")


# filtro de período na própria página (não sidebar)

import streamlit as st


def inicializar_filtro():
    if "data_inicio" not in st.session_state:
        st.session_state.data_inicio = datetime.today().replace(day=1)
    if "data_fim" not in st.session_state:
        st.session_state.data_fim = datetime.today()


def mostrar_filtro():
    inicializar_filtro()
    st.subheader("Filtrar por período")

    col1, col2 = st.columns(2)

    with col1:
        st.session_state.data_inicio = st.date_input(
            "De",
            value=st.session_state.data_inicio,
            key="filtro_inicio"
        )

    with col2:
        st.session_state.data_fim = st.date_input(
            "Até",
            value=st.session_state.data_fim,
            key="filtro_fim"
        )


def aplicar_filtro(df: pd.DataFrame, coluna_data: str) -> pd.DataFrame:
    if df.empty or coluna_data not in df.columns:
        return df

    inicio = pd.to_datetime(st.session_state.data_inicio)
    fim = pd.to_datetime(st.session_state.data_fim)

    datas = pd.to_datetime(df[coluna_data], errors="coerce")

    return df[(datas >= inicio) & (datas <= fim)]

