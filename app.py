import streamlit as st
import traceback

# 1. Configuração da página
st.set_page_config(page_title="Dimensionador Metálico 3D", page_icon="🏗️", layout="wide")

st.title("Diagnóstico do Motor 3D 🕵️‍♂️")

st.write("O sistema instalou o pacote, mas está travando ao tentar chamá-lo. Vamos testar as possibilidades:")

# Teste 1: Importação padrão
try:
    from PyNite import FEModel3D
    st.success("✅ Teste 1 Funcionou: 'from PyNite import FEModel3D'")
except Exception as e:
    st.error(f"❌ Teste 1 Falhou. Erro real:")
    st.code(traceback.format_exc())

# Teste 2: Letra minúscula
try:
    from pynite import FEModel3D
    st.success("✅ Teste 2 Funcionou: 'from pynite import FEModel3D'")
except Exception as e:
    st.error(f"❌ Teste 2 Falhou: {e}")

# Teste 3: Nome completo do pacote
try:
    from PyNiteFEA import FEModel3D
    st.success("✅ Teste 3 Funcionou: 'from PyNiteFEA import FEModel3D'")
except Exception as e:
    st.error(f"❌ Teste 3 Falhou: {e}")

st.stop() # Para o aplicativo aqui para não gerar mais loops
