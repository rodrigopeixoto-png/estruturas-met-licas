import streamlit as st
import plotly.graph_objects as go
import numpy as np

# Configuração inicial da página
st.set_page_config(page_title="Dimensionador Metálico 3D", page_icon="🏗️", layout="wide")

def main():
    st.title("🏗️ Dimensionamento de Estruturas Metálicas 3D")
    st.caption("Conformidade: NBR 8800 | NBR 6120 | NBR 6123")

    # ==========================================
    # BARRA LATERAL (MENU DE CONFIGURAÇÕES)
    # ==========================================
    st.sidebar.title("Configurações Gerais")
    
    st.sidebar.subheader("📐 Geometria e Sistema Estrutural")
    sistema_principal = st.sidebar.selectbox(
        "Sistema Principal", 
        ["Pórtico Alma Cheia", "Tesoura Plana (Treliçada)", "Arco"]
    )
    
    forma_cobertura = st.sidebar.selectbox(
        "Forma da Cobertura", 
        ["2 Águas", "1 Água"]
    )
    
    vao_x = st.sidebar.number_input("Vão Transversal (Eixo X) [m]", min_value=2.0, max_value=60.0, value=15.0, step=1.0)
    comp_y = st.sidebar.number_input("Comprimento Longitudinal (Eixo Y) [m]", min_value=2.0, max_value=120.0, value=30.0, step=1.0)
    altura_z = st.sidebar.number_input("Pé-direito (Eixo Z) [m]", min_value=2.0, max_value=20.0, value=6.0, step=0.5)
    
    espacamento = st.sidebar.number_input("Espaçamento entre Pórticos [m]", min_value=2.0, max_value=12.0, value=5.0, step=0.5)
    inclinacao = st.sidebar.number_input("Inclinação do Telhado [%]", min_value=1.0, max_value=100.0, value=10.0, step=1.0)

    st.sidebar.markdown("---")
    st.sidebar.subheader("🌪️ Cargas e Vento (NBR 6120 / 6123)")
    tipo_telha = st.sidebar.selectbox("Tipo de Cobertura", ["Trapezoidal (0.05 kN/m²)", "Termoacústica (0.15 kN/m²)", "Fibrocimento (0.18 kN/m²)"])
    sobrecarga = st.sidebar.number_input("Sobrecarga [kN/m²]", min_value=0.0, value=0.25, step=0.05)
    v0 = st.sidebar.number_input("Velocidade Básica V0 [m/s]", min_value=30.0, max_value=60.0, value=40.0, step=1.0)

    # ==========================================
    # PAINEL PRINCIPAL (ABAS DE NAVEGAÇÃO)
    # ==========================================
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📐 Geometria e 3D", "🌪️ Cargas e Vento", "⚙️ Análise (PyNite)", "✅ Verificação", "📦 Exportação (BIM)"
    ])

    with tab1:
        st.subheader(f"Visualização da Estrutura: {sistema_principal} - {forma_cobertura}")
        
        # LÓGICA PARAMÉTRICA DE GERAÇÃO DA MALHA
        fig = go.Figure()
        
        # Definindo a posição de cada pórtico no eixo Y
        y_coords = np.arange(0, comp_y + espacamento, espacamento)
        if y_coords[-1] != comp_y: # Garante que o último pórtico feche no limite exato
            y_coords[-1] = comp_y
            
        all_x, all_y, all_z = [], [], []
        edges = []
        node_offset = 0
        
        # Pontos de conexão para as terças (longitudinais)
        topos_esq, topos_dir, cumeeiras = [], [], []
        
        for y in y_coords:
            if forma_cobertura == "2 Águas":
                # Cálculo da altura da cumeeira (triângulo retângulo)
                h_cum = altura_z + (vao_x / 2.0) * (inclinacao / 100.0)
                
                # Coordenadas dos nós deste pórtico
                x_pts = [0, vao_x, 0, vao_x, vao_x/2]
                y_pts = [y, y, y, y, y]
                z_pts = [0, 0, altura_z, altura_z, h_cum]
                
                # Conexões: Pilar Esq(0-2), Pilar Dir(1-3), Viga Esq(2-4), Viga Dir(4-3)
                local_edges = [(0,2), (1,3), (2,4), (4,3)]
                
                # Guardando nós para ligar as terças longitudinais depois
                topos_esq.append(node_offset + 2)
                topos_dir.append(node_offset + 3)
                cumeeiras.append(node_offset + 4)
                
            else: # 1 Água
                h_cum = altura_z + vao_x * (inclinacao / 100.0)
                
                x_pts = [0, vao_x, 0, vao_x]
                y_pts = [y, y, y, y]
                z_pts = [0, 0, altura_z, h_cum]
                
                # Conexões: Pilar Esq(0-2), Pilar Dir(1-3), Viga(2-3)
                local_edges = [(0,2), (1,3), (2,3)]
                
                topos_esq.append(node_offset + 2)
                topos_dir.append(node_offset + 3)

            all_x.extend(x_pts)
            all_y.extend(y_pts)
            all_z.extend(z_pts)
            
            for edge in local_edges:
                edges.append((edge[0] + node_offset, edge[1] + node_offset))
                
            node_offset += len(x_pts)
            
        # Adicionando linhas longitudinais (Terças/Travamentos)
        for i in range(len(topos_esq) - 1):
            edges.append((topos_esq[i], topos_esq[i+1]))
            edges.append((topos_dir[i], topos_dir[i+1]))
            if forma_cobertura == "2 Águas":
                edges.append((cumeeiras[i], cumeeiras[i+1]))

        # PLOTAGEM
        # Desenha os nós
        fig.add_trace(go.Scatter3d(x=all_x, y=all_y, z=all_z, mode='markers', marker=dict(size=4, color='red'), name='Nós'))
        
        # Desenha as barras
        for edge in edges:
            fig.add_trace(go.Scatter3d(
                x=[all_x[edge[0]], all_x[edge[1]]], y=[all_y[edge[0]], all_y[edge[1]]], z=[all_z[edge[0]], all_z[edge[1]]],
                mode='lines', line=dict(color='blue', width=4), showlegend=False
            ))

        fig.update_layout(
            scene=dict(xaxis_title='X (m)', yaxis_title='Y (m)', zaxis_title='Z (m)', aspectmode='data'),
            margin=dict(l=0, r=0, b=0, t=0), height=600
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.write("Módulo de cargas (já programado anteriormente).")
    with tab3:
        st.write("Aguardando motor de Análise.")
    with tab4:
        st.write("Aguardando Verificações NBR 8800.")
    with tab5:
        st.write("Aguardando Exportação IFC.")

if __name__ == "__main__":
    main()
