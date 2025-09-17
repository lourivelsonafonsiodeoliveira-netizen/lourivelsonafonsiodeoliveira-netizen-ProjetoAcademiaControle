import streamlit as st
from PIL import Image

st.set_page_config(
    page_title="Controle de Alunos | Jiu-Jitsu",
    layout="wide",
)

# --- Exibe a Imagem ---
try:
    image = Image.open('jiujitsu.png')
    st.image(image, width=400)
except FileNotFoundError:
    st.warning("Imagem 'jiujitsu.png' não encontrada na pasta do projeto.")

st.title("🥋 Bem-vindo(a) ao seu Painel de Gestão")
st.markdown("Use o menu lateral para navegar entre as seções do aplicativo.")

st.info("👈 Selecione uma opção no menu à esquerda.")