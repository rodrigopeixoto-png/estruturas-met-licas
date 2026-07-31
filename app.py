import streamlit as st
import plotly.graph_objects as go
import numpy as np
from modules.solver import MotorCalculo3D
from modules.checker import VerificadorNBR8800, CATALOGO_W, PROPRIEDADES_ACO

st.set_page_config(page_title="Dimensionador Metálico 3D", page_icon="🏗️", layout="wide")

def main():
    st.title("🏗️ Dimensionamento de Estruturas Metálicas 3D")
    st.caption("Conformidade: NBR 8800 | NBR 6120 | NBR 6123")

    if "res_analise" not in st.session_state:
        st.session_state.res_analise = None

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
    st.sidebar.subheader("⚙️ Perfis e Material (NBR 8800)")
    tipo_aco = st.sidebar.selectbox("Aço Estrutural", list(PROPRIEDADES_ACO.keys()))
    perfil_selecionado = st.sidebar.selectbox("Perfil de Projeto (Linha W)", list(CATALOGO_W.keys()), index=2)

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
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📐 Geometria 3D", "🌪️ Cargas", "⚙️ Análise", "✅ Verificação NBR 8800", "📦 BIM"])

    # LÓGICA PARAMÉTRICA DE GEOMETRIA
    y_coords = np.arange(0, comp_y + espacamento, espacamento)
    if y_coords[-1] != comp_y: y_coords[-1] = comp_y
        
    all_x, all_y, all_z = [], [], []
    edges = []
    node_offset = 0
    topos_esq, topos_dir, cumeeiras = [], [], []

    for y in y_coords:
        if sistema_principal == "Arco":
            x_pts = [0] + list(np.linspace(0, vao_x, 9)) + [vao_x]
            y_pts = [y] * 11
            z_pts = [0] + [altura_z + flecha_arco * (1 - (2*(x-vao_x/2)/vao_x)**2) for x in x_pts[1:-1]] + [0]
            local_edges = [(0, 1), (9, 10)]
            for i in range(1, 9): local_edges.append((i, i+1))
            topos_esq.append(node_offset + 1)
            topos_dir.append(node_offset + 9)
            cumeeiras.append(node_offset + 5)

        elif sistema_principal == "Tesoura Plana (Treliçada)":
            if forma_cobertura == "1 Água":
                # Treliça 1 Água dividida em 8 painéis
                n_paineis = 8
                x_sub = np.linspace(0, vao_x, n_paineis + 1)
                h_max = vao_x * (inclinacao / 100.0)
                
                # Nós: Bases dos pilares (0 e 1), Banzos Inf (2 a 10), Banzos Sup (11 a 19)
                x_pts = [0, vao_x] + list(x_sub) + list(x_sub)
                y_pts = [y] * len(x_pts)
                z_pts = [0, 0] + [altura_z] * (n_paineis + 1) + list(altura_z + (vao_x - x_sub) * (inclinacao / 100.0))
                
                local_edges = [
                    (0, 2), (1, 2 + n_paineis) # Pilares
                ]
                
                # Conexões da Treliça (Banzos, Montantes e Diagonais)
                idx_inf = 2
                idx_sup = 2 + (n_paineis + 1)
                
                for i in range(n_paineis):
                    # Banzo Inferior
                    local_edges.append((idx_inf + i, idx_inf + i + 1))
                    # Banzo Superior
                    local_edges.append((idx_sup + i, idx_sup + i + 1))
                    # Montantes
                    local_edges.append((idx_inf + i, idx_sup + i))
                    # Diagonais
                    local_edges.append((idx_inf + i, idx_sup + i + 1))
                
                # Último montante
                local_edges.append((idx_inf + n_paineis, idx_sup + n_paineis))

                topos_esq.append(node_offset + idx_sup)
                topos_dir.append(node_offset + idx_sup + n_paineis)

            else: # 2 Águas
                h_cum = altura_z + (vao_x / 2.0) * (inclinacao / 100.0)
                x_pts = [0, vao_x, 0, vao_x, vao_x/2, vao_x/4, 3*vao_x/4, vao_x/2]
                y_pts = [y] * 8
                z_pts = [0, 0, altura_z, altura_z, altura_z, altura_z + (h_cum-altura_z)/2, altura_z + (h_cum-altura_z)/2, h_cum]
                local_edges = [
                    (0,2), (1,3), 
                    (2,4), (4,3), 
                    (2,5), (5,7), (7,6), (6,3), 
                    (4,7), (4,5), (4,6), (2,7), (3,7) 
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
        if (forma_cobertura == "2 Águas" or sistema_principal == "Arco") and len(cumeeiras) > i:
            edges.append((cumeeiras[i], cumeeiras[i+1]))

    # CARGAS
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
        fig.update_layout(scene=dict(xaxis_title='X (m)', yaxis_title='Y (m)', zaxis_title='Z (m)', aspectmode='data'), margin=dict(l=0, r=0, b=0, t=0), height=550)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Carga Permanente (G)", f"{peso_telha:.2f} kN/m²")
        col2.metric("Sobrecarga (Q)", f"{sobrecarga:.2f} kN/m²")
        col3.metric("Vel. Característica (Vk)", f"{vk:.1f} m/s")
        col4.metric("Pressão do Vento (W)", f"{q_vento:.3f} kN/m²")
        st.success(f"**Carga Distribuída de Projeto (q_Sd):** {q_elu:.2f} kN/m²")

    with tab3:
        st.subheader("⚙️ Análise Estrutural Matricial 3D")
        if st.button("🚀 Executar Análise Estrutural", type="primary"):
            with st.spinner("Calculando esforços solicitantes..."):
                motor = MotorCalculo3D()
                motor.construir_malha(all_x, all_y, all_z, edges, apoios_base)
                motor.aplicar_carga_distribuida(q_elu, vao_x, espacamento)
                st.session_state.res_analise = motor.resolver()

        if st.session_state.res_analise and st.session_state.res_analise.get("sucesso"):
            res = st.session_state.res_analise
            st.success("✅ Análise Matricial Concluída!")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Normal Máx (N_sd)", f"{res['n_max_kn']:.2f} kN")
            c2.metric("Cortante Máx (V_sd)", f"{res['v_max_kn']:.2f} kN")
            c3.metric("Momento Máx (M_sd)", f"{res['m_max_knm']:.2f} kNm")
            c4.metric("Deslocamento Máx", f"{res['desloc_max_mm']:.2f} mm")

    with tab4:
        st.subheader("✅ Verificação de Segurança (NBR 8800)")
        if not st.session_state.res_analise:
            st.warning("⚠️ Por favor, execute a Análise Estrutural na Aba 3 primeiro.")
        else:
            res = st.session_state.res_analise
            verificador = VerificadorNBR8800(perfil_selecionado, tipo_aco)
            ver = verificador.verificar_estrutura(
                res["n_max_kn"], res["v_max_kn"], res["m_max_knm"], res["desloc_max_mm"], vao_x
            )

            if ver["aprovado"]:
                st.success(f"### 🎉 PERFIL APROVADO! (Taxa de Utilização Máxima: {ver['taxa_maxima']:.1f}%)")
            else:
                st.error(f"### ❌ PERFIL REPROVADO! (Taxa de Utilização Máxima: {ver['taxa_maxima']:.1f}%)")

            st.markdown("---")
            col_a, col_b, col_c, col_d = st.columns(4)
            col_a.metric("Flexão (M_sd / M_rd)", f"{ver['ratio_M']:.1f}%", help=f"M_sd: {res['m_max_knm']:.1f} kNm | M_rd: {ver['M_rd']:.1f} kNm")
            col_b.metric("Cisalhamento (V_sd / V_rd)", f"{ver['ratio_V']:.1f}%", help=f"V_sd: {res['v_max_kn']:.1f} kN | V_rd: {ver['V_rd']:.1f} kN")
            col_c.metric("Compressão (N_sd / N_rd)", f"{ver['ratio_N']:.1f}%", help=f"N_sd: {res['n_max_kn']:.1f} kN | N_rd: {ver['N_rd']:.1f} kN")
            col_d.metric("Deformação ELS (δ_sd / δ_lim)", f"{ver['ratio_delta']:.1f}%", help=f"δ_sd: {res['desloc_max_mm']:.1f} mm | Limit: {ver['delta_lim_mm']:.1f} mm")

            st.progress(min(int(ver['taxa_maxima']), 100))

    with tab5: st.write("Aguardando Exportação IFC.")

if __name__ == "__main__":
    main()
