import streamlit as st

# Configuração inicial da página (deve ser o primeiro comando)
st.set_page_config(
    page_title="Dimensionador Metálico 3D",
    page_icon="🏗️",
    layout="wide"
)

def main():
    st.title("🏗️ Dimensionamento de Estruturas Metálicas 3D")
    st.caption("Conformidade: NBR 8800 | NBR 6120 | NBR 6123")

    # ==========================================
    # BARRA LATERAL (MENU DE CONFIGURAÇÕES)
    # ==========================================
    st.sidebar.title("Configurações Gerais")
    
    tipo_estrutura = st.sidebar.selectbox(
        "Tipo de Estrutura",
        ["Pórtico Espacial", "Treliça de Cobertura"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.info("As configurações de geometria, vento e perfis serão inseridas aqui nos próximos passos.")

    # ==========================================
    # PAINEL PRINCIPAL (ABAS DE NAVEGAÇÃO)
    # ==========================================
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📐 Geometria e 3D", 
        "🌪️ Cargas e Vento", 
        "⚙️ Análise (PyNite)", 
        "✅ Verificação (NBR 8800)",
        "📦 Exportação (IFC/PDF)"
    ])

    with tab1:
        st.subheader("Visualização da Estrutura")
        st.write("Aqui entrará o visualizador 3D feito com Plotly.")

    with tab2:
        st.subheader("Carregamentos (NBR 6120 / NBR 6123)")
        st.write("Aqui calcularemos o peso da telha e as pressões de vento.")

    with tab3:
        st.subheader("Esforços Internos (Motor de Análise)")
        st.write("Aqui conectaremos o PyNite para calcular N, V e M.")

    with tab4:
        st.subheader("Verificações Normativas")
        st.write("Aqui faremos os cálculos de tração, compressão e flexão conforme a NBR 8800.")

    with tab5:
        st.subheader("Relatórios e BIM")
        st.write("Aqui colocaremos os botões para baixar o memorial de cálculo (PDF) e o modelo BIM (IFC).")

if __name__ == "__main__":
    main()