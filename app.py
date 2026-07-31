import streamlit as st
import plotly.graph_objects as go

# Configuração inicial da página
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
    st.sidebar.subheader("📐 Geometria")
    vao_x = st.sidebar.number_input("Vão (Eixo X) [m]", min_value=2.0, max_value=50.0, value=12.0, step=1.0)
    comp_y = st.sidebar.number_input("Comprimento (Eixo Y) [m]", min_value=2.0, max_value=100.0, value=20.0, step=1.0)
    altura_z = st.sidebar.number_input("Pé-direito (Eixo Z) [m]", min_value=2.0, max_value=20.0, value=6.0, step=0.5)

    st.sidebar.markdown("---")
    st.sidebar.subheader("🌪️ Cargas e Vento")
    tipo_telha = st.sidebar.selectbox(
        "Tipo de Cobertura",
        ["Trapezoidal Simples (0.05 kN/m²)", "Termoacústica (0.15 kN/m²)", "Fibrocimento 6mm (0.18 kN/m²)"]
    )
    
    sobrecarga = st.sidebar.number_input("Sobrecarga (NBR 6120) [kN/m²]", min_value=0.0, value=0.25, step=0.05)
    
    v0 = st.sidebar.number_input("Velocidade Básica V0 [m/s]", min_value=30.0, max_value=60.0, value=40.0, step=1.0)
    s1_s2_s3 = st.sidebar.number_input("Fatores Combinados (S1 x S2 x S3)", min_value=0.5, max_value=1.5, value=1.0, step=0.05)

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
        
        fig = go.Figure()
        
        x_nodes = [0, vao_x, vao_x, 0, 0, vao_x, vao_x, 0]
        y_nodes = [0, 0, comp_y, comp_y, 0, 0, comp_y, comp_y]
        z_nodes = [0, 0, 0, 0, altura_z, altura_z, altura_z, altura_z]
        
        fig.add_trace(go.Scatter3d(
            x=x_nodes, y=y_nodes, z=z_nodes,
            mode='markers', marker=dict(size=6, color='red'), name='Nós'
        ))
        
        edges = [(0, 4), (1, 5), (2, 6), (3, 7), (4, 5), (5, 6), (6, 7), (7, 4)]
        
        for edge in edges:
            fig.add_trace(go.Scatter3d(
                x=[x_nodes[edge[0]], x_nodes[edge[1]]],
                y=[y_nodes[edge[0]], y_nodes[edge[1]]],
                z=[z_nodes[edge[0]], z_nodes[edge[1]]],
                mode='lines', line=dict(color='blue', width=5), showlegend=False
            ))

        fig.update_layout(
            scene=dict(xaxis_title='Vão X (m)', yaxis_title='Comprimento Y (m)', zaxis_title='Altura Z (m)', aspectmode='data'),
            margin=dict(l=0, r=0, b=0, t=0), height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Carregamentos Calculados")
        
        # Extração automática do peso numérico da telha a partir do texto
        peso_telha = float(tipo_telha.split("(")[1].split(" ")[0])
        
        # Cálculo da pressão dinâmica do vento
        vk = v0 * s1_s2_s3
        q_vento = 0.613 * (vk ** 2) / 1000 # Convertendo de N/m² para kN/m²
        
        # Exibição em colunas
        col1, col2, col3 = st.columns(3)
        col1.metric(label="Carga Permanente (G)", value=f"{peso_telha:.2f} kN/m²")
        col2.metric(label="Sobrecarga (Q)", value=f"{sobrecarga:.2f} kN/m²")
        col3.metric(label="Pressão do Vento (W)", value=f"{q_vento:.3f} kN/m²")
        
        st.markdown("---")
        st.markdown("### Combinações Últimas (ELU)")
        st.markdown("Conforme a **NBR 8800**, utilizaremos a seguinte combinação (considerando o vento como variável principal para coberturas leves):")
        
        st.latex(r"q_{Sd} = 1.25 \cdot G + 1.50 \cdot Q + 1.40 \cdot W")
        
        # Cálculo da carga combinada
        q_elu = (1.25 * peso_telha) + (1.50 * sobrecarga) + (1.40 * q_vento)
        
        st.success(f"**Carga Total Solicitante (q_Sd):** {q_elu:.2f} kN/m²")
        st.info("💡 Este valor distribuído será aplicado no motor de cálculo 3D para gerar os esforços internos da estrutura.")

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
