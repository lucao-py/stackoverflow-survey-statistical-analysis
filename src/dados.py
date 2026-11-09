
import pandas as pd
import streamlit as st

URL_DADOS = (
    "https://media.githubusercontent.com/media/"
    "StackExchange/Survey/main/packages/archive/2025/results.csv"
)


@st.cache_data(show_spinner="Carregando dados...")
def carregar_dados():
    return pd.read_csv(URL_DADOS, low_memory=False)
