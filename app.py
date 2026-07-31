import streamlit as st
import plotly.graph_objects as go
import numpy as np

# Importando o nosso motor de cálculo recém-criado!
from modules.solver import MotorCalculo3D

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
    sistema_principal = st.sidebar.selectbox("Sistema Principal", ["Pórtico Alma Cheia", "Tesoura Plana (Treliçada)", "Arco"])
    forma_cobertura = st.sidebar.selectbox("Forma da Cobertura", ["2 Águas", "1 Água"])
    
    vao_x = st.sidebar.number_input("Vão Transversal (Eixo X) [m]", min_value=2.0, max_value=60.0, value=15.0, step=1.0)
    comp_y = st.sidebar.number_input("Comprimento Longitudinal (Eixo Y) [m]", min_value=2.0, max_value=120.0, value=30.0, step=1.0)
    altura_z = st.sidebar.number_input("Pé-direito (Eixo Z) [m]", min_value=2.0, max_value=20.0, value=6.0, step=0.5)
    
    espacamento = st.sidebar.number_input("Espaçamento entre Pórticos [m]", min_value=2.0, max_value=12.0, value=5.0, step=0.5)
    inclinacao = st.sidebar.number_input("Inclinação do Telhado [%]", min_value=1.0, max_value=100.0, value=10.0, step=1.0)

    st.sidebar.markdown("---")
    st.sidebar.subheader("🌪️ Cargas e Cobertura (NBR 6120)")
    tipo_telha = st.sidebar.selectbox("Tipo de Cobertura", ["Trapezoidal (0.05 kN/m²)", "Termoacústica (0.15 kN/m²)", "Fibrocimento (0.18 kN/m²)"])
    sobrecarga = st.sidebar.number_input("Sobrecarga [kN/m²]", min_value=0.0, value=0.25, step=0.05)
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🌬️ Parâmetros de Vento (NBR 6123)")
    v0 = st.sidebar.number_input("Velocidade Básica V0 [m/s]", min_value=30.0, max_value=60.0, value=40.0, step=1.0)
    
    s1_opcao = st.sidebar.selectbox("Fator Topográfico (S1)", ["Terreno plano ou fracamente acidentado (1.00)", "Taludes e morros (1.10)", "Vales profundos protegidos (0.90)"])
    s1 = float(s1_opcao.split("(")[1].split(")")[0])
    
    s2 = st.sidebar.number_input("Fator de Rugosidade (S2)", min_value=0.50, max_value=1.50, value=1.00, step=0.01)
    
    s3_opcao = st.sidebar.selectbox("Fator Estatístico (S3)", ["Grupo 1: Hospitais, quartéis (1.10)", "Grupo 2: Edifícios residenciais/comerciais (1.00)", "Grupo 3: Galpões e instalações industriais (0.95)", "Grupo 4: Vedações e estruturas temporárias (0.83)"])
    s3 = float(s3_opcao.split("(")[1].split(")")[0])

    # ==========================================
    # PAINEL PRINCIPAL (ABAS DE NAVEGAÇÃO)
    # ==========================================
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📐 Geometria e 3D", "🌪️ Cargas e Vento", "⚙️ Análise (PyNite)", "✅ Verificação", "📦 Exportação (BIM)"
    ])

    with tab1:
        st.subheader(f"Visualização da Estrutura: {sistema_principal} - {forma_cobertura}")
        
        fig = go.Figure()
        
        y_coords = np.arange(0, comp_y + espacamento, espacamento)
        if y_coords[-1] != comp_y:
            y_coords[-1] = comp_y
            
        all_x, all_y, all_z = [], [], []
        edges = []
        node_offset = 0
        
        topos_esq, topos_dir, cumeeiras = [], [], []
        
        for y in y_coords:
            if forma_cobertura == "2 Águas":
                h_cum = altura_z + (vao_x / 2.0) * (inclinacao / 100.0)
                x_pts = [0, vao_x, 0, vao_x, vao_x/2]
                y_pts = [y, y, y, y, y]
                z_pts = [0, 0, altura_z, altura_z, h_cum]
                local_edges = [(0,2), (1,3), (2,4), (4,3)]
                
                topos_esq.append(node_offset + 2)
                topos_dir.append(node_offset + 3)
                cumeeiras.append(node_offset + 4)
            else: # 1 Água
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
            
            for edge in local_edges:
                edges.append((edge[0] + node_offset, edge[1] + node_offset))
                
            node_offset += len(x_pts)
            
        for i in range(len(topos_esq) - 1):
            edges.append((topos_esq[i], topos_esq[i+1]))
            edges.append((topos_dir[i], topos_dir[i+1]))
            if forma_cobertura == "2 Águas":
                edges.append((cumeeiras[i], cumeeiras[i+1]))

        # Desenho da Estrutura
        fig.add_trace(go.Scatter3d(x=all_x, y=all_y, z=all_z, mode='markers', marker=dict(size=4, color='red'), name='Nós'))
        for edge in edges:
            fig.add_trace(go.Scatter3d(
                x=[all_x[edge[0]], all_x[edge[1]]], y=[all_y[edge[0]], all_y[edge[1]]], z=[all_z[edge[0]], all_z[edge[1]]],
                mode='lines', line=dict(color='blue', width=4), showlegend=False
            ))

        fig.update_layout(scene=dict(xaxis_title='X (m)', yaxis_title='Y (m)', zaxis_title='Z (m)', aspectmode='data'), margin=dict(l=0, r=0, b=0, t=0), height=600)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Carregamentos Calculados")
        peso_telha = float(tipo_telha.split("(")[1].split(" ")[0])
        vk = v0 * s1 * s2 * s3
        q_vento = 0.613 * (vk ** 2) / 1000 
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Carga Permanente (G)", f"{peso_telha:.2f} kN/m²")
        col2.metric("Sobrecarga (Q)", f"{sobrecarga:.2f} kN/m²")
        col3.metric("Vel. Característica (Vk)", f"{vk:.1f} m/s")
        col4.metric("Pressão do Vento (W)", f"{q_vento:.3f} kN/m²")
        
        st.markdown("---")
        st.markdown("### Combinações Últimas (ELU) - Coberturas Leves")
        st.latex(r"q_{Sd} = 1.25 \cdot G + 1.40 \cdot W + (1.50 \cdot 0.70) \cdot Q")
        
        q_elu = (1.25 * peso_telha) + (1.40 * q_vento) + (1.50 * 0.70 * sobrecarga)
        st.success(f"**Carga Distribuída de Projeto (q_Sd):** {q_elu:.2f} kN/m²")

    with tab3:
        st.subheader("⚙️ Esforços Internos (Motor de Análise 3D)")
        st.write("Aperte o botão abaixo para enviar a geometria e as cargas para a matriz de cálculo de Elementos Finitos.")
        
        if st.button("🚀 Executar Análise Estrutural", type="primary"):
            with st.spinner("Montando matriz de rigidez e resolvendo o sistema de equações..."):
                try:
                    # 1. Instanciar o motor
                    motor = MotorCalculo3D()
                    
                    # 2. Inserir a geometria (Variáveis all_x, all_y, all_z e edges vêm da Tab 1)
                    motor.construir_malha(all_x, all_y, all_z, edges)
                    
                    # 3. Aplicar as cargas nas vigas de cobertura
                    motor.aplicar_carga_distribuida(q_elu, vao_x, espacamento)
                    
                    # 4. Resolver as equações matriciais
                    status = motor.resolver()
                    
                    if status is True:
                        st.success("✅ Análise Estrutural concluída com sucesso!")
                        
                        # Exibindo um resumo rápido da malha gerada e resolvida
                        col_a, col_b = st.columns(2)
                        col_a.metric("Total de Nós (Graus de Liberdade)", len(motor.modelo.Nodes))
                        col_b.metric("Total de Barras Processadas", len(motor.modelo.Members))
                        
                        st.info("A matriz de rigidez global foi invertida com sucesso. Os esforços de Normal, Cortante, Momento e as Deformações já estão disponíveis na memória para dimensionarmos os perfis na Aba 4.")
                        
                    else:
                        st.error(f"❌ Erro na análise estrutural: {status}")
                except Exception as e:
                    st.error(f"Erro inesperado ao rodar o motor: {e}")

    with tab4:
        st.write("Aguardando Verificações NBR 8800.")
    with tab5:
        st.write("Aguardando Exportação IFC.")

if __name__ == "__main__":
    main()
