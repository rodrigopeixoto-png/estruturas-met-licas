import streamlit as st
import plotly.graph_objects as go

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
    st.sidebar.subheader("📐 Geometria")
    vao_x = st.sidebar.number_input("Vão (Eixo X) [m]", min_value=2.0, max_value=50.0, value=12.0, step=1.0)
    comp_y = st.sidebar.number_input("Comprimento (Eixo Y) [m]", min_value=2.0, max_value=100.0, value=20.0, step=1.0)
    altura_z = st.sidebar.number_input("Pé-direito (Eixo Z) [m]", min_value=2.0, max_value=20.0, value=6.0, step=0.5)

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
        
        # --- LÓGICA DO PLOTLY 3D ---
        fig = go.Figure()
        
        # Coordenadas dos nós (Pórtico Retangular Básico)
        x_nodes = [0, vao_x, vao_x, 0, 0, vao_x, vao_x, 0]
        y_nodes = [0, 0, comp_y, comp_y, 0, 0, comp_y, comp_y]
        z_nodes = [0, 0, 0, 0, altura_z, altura_z, altura_z, altura_z]
        
        # Adiciona os nós (pontos vermelhos)
        fig.add_trace(go.Scatter3d(
            x=x_nodes, y=y_nodes, z=z_nodes,
            mode='markers',
            marker=dict(size=6, color='red'),
            name='Nós'
        ))
        
        # Definição das barras (conexões entre os nós)
        # 0-3: Base, 4-7: Topo
        edges = [
            (0, 4), (1, 5), (2, 6), (3, 7), # Pilares
            (4, 5), (5, 6), (6, 7), (7, 4)  # Vigas de cobertura perimetrais
        ]
        
        # Adiciona as linhas (barras azuis)
        for edge in edges:
            fig.add_trace(go.Scatter3d(
                x=[x_nodes[edge[0]], x_nodes[edge[1]]],
                y=[y_nodes[edge[0]], y_nodes[edge[1]]],
                z=[z_nodes[edge[0]], z_nodes[edge[1]]],
                mode='lines',
                line=dict(color='blue', width=5),
                showlegend=False
            ))

        # Configuração do layout do gráfico
        fig.update_layout(
            scene=dict(
                xaxis_title='Vão X (m)',
                yaxis_title='Comprimento Y (m)',
                zaxis_title='Altura Z (m)',
                aspectmode='data' # Mantém a proporção visual exata
            ),
            margin=dict(l=0, r=0, b=0, t=0),
            height=600
        )
        
        # Exibe o gráfico no Streamlit
        st.plotly_chart(fig, use_container_width=True)

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
