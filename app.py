import streamlit as st
import plotly.graph_objects as go
import numpy as np
from modules.solver import MotorCalculo3D

st.set_page_config(page_title="Dimensionador Metálico 3D", page_icon="🏗️", layout="wide")

def main():
    st.title("🏗️ Dimensionamento de Estruturas Metálicas 3D")
    st.caption("Conformidade: NBR 8800 | NBR 6120 | NBR 6123")

    # ==========================================
    # BARRA LATERAL (MENU DE CONFIGURAÇÕES)
    # ==========================================
    st.sidebar.title("Configurações Gerais")
    
    st.sidebar.subheader("📐 Sistema Estrutural")
    sistema_principal = st.sidebar.selectbox("Sistema Principal", ["Pórtico Alma Cheia", "Tesoura Plana (Treliçada)", "Arco"])
    
    forma_cobertura = "Não se aplica"
    if sistema_principal != "Arco":
        forma_cobertura = st.sidebar.selectbox("Forma da Cobertura", ["2 Águas", "1 Água"])
        inclinacao = st.sidebar.number_input("Inclinação do Telhado [%]", min_value=1.0, max_value=100.0, value=10.0, step=1.0)
    else:
        flecha_arco = st.sidebar.number_input("Flecha do Arco (m)", min_value=1.0, max_value=20.0, value=3.0, step=0.5)

    vao_x = st.sidebar.number_input("Vão Transversal (Eixo X) [m]", min_value=2.0, max_value=60.0, value=15.0, step=1.0)
    comp_y = st.sidebar.number_input("Comprimento Longitudinal (Eixo Y) [m]", min_value=2.0, max_value=120.0, value=30.0, step=1.0)
    altura_z = st.sidebar.number_input("Pé-direito (Eixo Z) [m]", min_value=2.0, max_value=20.0, value=6.0, step=0.5)
    espacamento = st.sidebar.number_input("Espaçamento entre Pórticos [m]", min_value=2.0, max_value=12.0, value=5.0, step=0.5)

    st.sidebar.markdown("---")
    st.sidebar.subheader("🔒 Condições de Contorno")
    apoios_base = st.sidebar.selectbox(
        "Vínculos na Base (Fundação)", 
        ["Engastado (Trava Translações e Rotações)", "Articulado (Trava apenas Translações)"]
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("🌪️ Cargas (NBR 6120 / NBR 6123)")
    tipo_telha = st.sidebar.selectbox("Tipo de Cobertura", ["Trapezoidal (0.05 kN/m²)", "Termoacústica (0.15 kN/m²)", "Fibrocimento (0.18 kN/m²)"])
    sobrecarga = st.sidebar.number_input("Sobrecarga [kN/m²]", min_value=0.0, value=0.25, step=0.05)
    v0 = st.sidebar.number_input("Velocidade Básica V0 [m/s]", min_value=30.0, max_value=60.0, value=40.0, step=1.0)
    s1 = float(st.sidebar.selectbox("Fator S1", ["Plano (1.00)", "Talude (1.10)", "Vale (0.90)"]).split("(")[1].split(")")[0])
    s2 = st.sidebar.number_input("Fator S2", min_value=0.50, max_value=1.50, value=1.00, step=0.01)
    s3 = float(st.sidebar.selectbox("Fator S3", ["Grupo 1 (1.10)", "Grupo 2 (1.00)", "Grupo 3 (0.95)", "Grupo 4 (0.83)"]).split("(")[1].split(")")[0])

    # ==========================================
    # PAINEL PRINCIPAL (ABAS DE NAVEGAÇÃO)
    # ==========================================
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📐 Geometria 3D", "🌪️ Cargas", "⚙️ Análise", "✅ Verificação", "📦 BIM"])

    # LÓGICA PARAMÉTRICA DE GEOMETRIA
    y_coords = np.arange(0, comp_y + espacamento, espacamento)
    if y_coords[-1] != comp_y: y_coords[-1] = comp_y
        
    all_x, all_y, all_z = [], [], []
    edges = []
    node_offset = 0
    topos_esq, topos_dir, cumeeiras = [], [], []

    for y in y_coords:
        if sistema_principal == "Arco":
            # Gera 9 pontos para simular a curva do arco
            x_pts = [0] + list(np.linspace(0, vao_x, 9)) + [vao_x]
            y_pts = [y] * 11
            # Z: Pilares nas pontas, Parábola no meio
            z_pts = [0] + [altura_z + flecha_arco * (1 - (2*(x-vao_x/2)/vao_x)**2) for x in x_pts[1:-1]] + [0]
            
            local_edges = [(0, 1), (9, 10)] # Pilares
            for i in range(1, 9): local_edges.append((i, i+1)) # Curva do Arco
            
            topos_esq.append(node_offset + 1)
            topos_dir.append(node_offset + 9)
            cumeeiras.append(node_offset + 5) # Nó central do arco

        elif sistema_principal == "Tesoura Plana (Treliçada)" and forma_cobertura == "2 Águas":
            h_cum = altura_z + (vao_x / 2.0) * (inclinacao / 100.0)
            # Pilares(0,1), Bases da Treliça(2,3), Meio Banzo Inf(4), Topos(5,6), Cumeeira(7)
            x_pts = [0, vao_x, 0, vao_x, vao_x/2, vao_x/4, 3*vao_x/4, vao_x/2]
            y_pts = [y] * 8
            z_pts = [0, 0, altura_z, altura_z, altura_z, altura_z + (h_cum-altura_z)/2, altura_z + (h_cum-altura_z)/2, h_cum]
            
            local_edges = [
                (0,2), (1,3), # Pilares
                (2,4), (4,3), # Banzo Inferior
                (2,5), (5,7), (7,6), (6,3), # Banzo Superior
                (4,7), (4,5), (4,6), (2,7), (3,7) # Montantes e Diagonais
            ]
            topos_esq.append(node_offset + 2)
            topos_dir.append(node_offset + 3)
            cumeeiras.append(node_offset + 7)

        else: # Alma Cheia
            h_cum = altura_z + (vao_x / 2.0) * (inclinacao / 100.0)
            if forma_cobertura == "2 Águas":
                x_pts = [0, vao_x, 0, vao_x, vao_x/2]
                y_pts = [y, y, y, y, y]
                z_pts = [0, 0, altura_z, altura_z, h_cum]
                local_edges = [(0,2), (1,3), (2,4), (4,3)]
                topos_esq.append(node_offset + 2)
                topos_dir.append(node_offset + 3)
                cumeeiras.append(node_offset + 4)
            else:
                h_cum = altura_z + vao_x * (inclinacao / 100.0)
                x_pts = [0, vao_x, 0, vao_x]
                y_pts = [y, y, y, y]
                z_pts = [0, 0, altura_z, h_cum]
                local_edges = [(0,2), (1,3), (2,3)]
                topos_esq.append(node_offset + 2)
                topos_dir.append(node_offset + 3)

        all_x.extend(x_pts)
        all_y.extend(y_pts)
        all_z.extend(z_pts)
        for edge in local_edges: edges.append((edge[0] + node_offset, edge[1] + node_offset))
        node_offset += len(x_pts)
        
    for i in range(len(topos_esq) - 1):
        edges.append((topos_esq[i], topos_esq[i+1]))
        edges.append((topos_dir[i], topos_dir[i+1]))
        if forma_cobertura == "2 Águas" or sistema_principal == "Arco":
            edges.append((cumeeiras[i], cumeeiras[i+1]))

    # CÁLCULO DE CARGAS (TAB 2)
    peso_telha = float(tipo_telha.split("(")[1].split(" ")[0])
    vk = v0 * s1 * s2 * s3
    q_vento = 0.613 * (vk ** 2) / 1000 
    q_elu = (1.25 * peso_telha) + (1.40 * q_vento) + (1.50 * 0.70 * sobrecarga)

    with tab1:
        fig = go.Figure()
        fig.add_trace(go.Scatter3d(x=all_x, y=all_y, z=all_z, mode='markers', marker=dict(size=4, color='red'), name='Nós'))
        for edge in edges:
            fig.add_trace(go.Scatter3d(
                x=[all_x[edge[0]], all_x[edge[1]]], y=[all_y[edge[0]], all_y[edge[1]]], z=[all_z[edge[0]], all_z[edge[1]]],
                mode='lines', line=dict(color='blue', width=4), showlegend=False
            ))
        fig.update_layout(scene=dict(xaxis_title='X', yaxis_title='Y', zaxis_title='Z', aspectmode='data'), margin=dict(l=0, r=0, b=0, t=0), height=500)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Carga Permanente (G)", f"{peso_telha:.2f} kN/m²")
        col2.metric("Sobrecarga (Q)", f"{sobrecarga:.2f} kN/m²")
        col3.metric("Vel. Característica (Vk)", f"{vk:.1f} m/s")
        col4.metric("Pressão do Vento (W)", f"{q_vento:.3f} kN/m²")
        st.success(f"**Carga Distribuída de Projeto (q_Sd):** {q_elu:.2f} kN/m²")

    with tab3:
        if st.button("🚀 Executar Análise Estrutural", type="primary"):
            with st.spinner("Resolvendo equações matriciais..."):
                try:
                    motor = MotorCalculo3D()
                    # Passando também o tipo de apoio para o motor
                    motor.construir_malha(all_x, all_y, all_z, edges, apoios_base)
                    motor.aplicar_carga_distribuida(q_elu, vao_x, espacamento)
                    status = motor.resolver()
                    if status is True: st.success("✅ Análise concluída! Nós e Elementos processados.")
                    else: st.error(f"Erro: {status}")
                except Exception as e:
                    st.error(f"Erro: {e}")

    with tab4: st.write("Aguardando Verificações NBR 8800.")
    with tab5: st.write("Aguardando Exportação IFC.")

if __name__ == "__main__":
    main()
