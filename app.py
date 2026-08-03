import streamlit as st
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
from modules.solver import MotorCalculo3D
from modules.checker import VerificadorNBR8800, CATALOGO_CHAPA_DOBRADA, CATALOGO_COMPLETO, PROPRIEDADES_ACO

st.set_page_config(page_title="Dimensionador Metálico 3D", page_icon="🏗️", layout="wide")

def desenhar_diagrama(res, tipo_diagrama):
    """Gera um gráfico 3D Plotly com os diagramas de esforços aplicados sobre a estrutura"""
    fig = go.Figure()
    nos, barras, esforcos = res["nos"], res["barras"], res["esforcos"]
    
    # 1. Desenha a estrutura base em linhas finas
    for n1, n2 in barras:
        x1, y1, z1 = nos[n1]
        x2, y2, z2 = nos[n2]
        fig.add_trace(go.Scatter3d(
            x=[x1, x2], y=[y1, y2], z=[z1, z2],
            mode='lines', line=dict(color='lightgrey', width=2), showlegend=False
        ))
        
    # 2. Plota os resultados
    if tipo_diagrama == "Reações de Apoio":
        rx, ry, rz, texts = [], [], [], []
        for no_idx, reac in res["reacoes"].items():
            x, y, z = nos[no_idx]
            Fx, Fy, Fz = reac[0], reac[1], reac[2]
            rx.append(x); ry.append(y); rz.append(z)
            texts.append(f"Fz: {Fz:.1f}kN<br>Fx: {Fx:.1f}kN<br>Fy: {Fy:.1f}kN")
        
        fig.add_trace(go.Scatter3d(
            x=rx, y=ry, z=rz, mode='markers+text',
            marker=dict(size=8, color='purple', symbol='diamond'),
            text=texts, textposition="top center", textfont=dict(size=12, color='purple'), showlegend=False
        ))
        
    else:
        # Descobrir máximo global para normalizar a escala do desenho
        max_val = 1e-5
        for esf in esforcos:
            v1, v2 = (esf["N"] if "Normal" in tipo_diagrama else (esf["Vz"] if "Cortante" in tipo_diagrama else esf["My"]))
            max_val = max(max_val, abs(v1), abs(v2))
            
        escala = 1.2 / max_val # O diagrama terá no máximo 1.2m visuais de tamanho
        
        for i, esf in enumerate(esforcos):
            n1, n2 = esf["n1"], esf["n2"]
            x1, y1, z1 = nos[n1]
            x2, y2, z2 = nos[n2]
            dx, dy, dz = x2 - x1, y2 - y1, z2 - z1
            L = np.sqrt(dx**2 + dy**2 + dz**2)
            if L == 0: continue
            
            if "Normal" in tipo_diagrama:
                v1, v2 = esf["N"]
                cor = 'royalblue' if (v1+v2) > 0 else 'crimson'
            elif "Cortante" in tipo_diagrama:
                v1, v2 = esf["Vz"]
                cor = 'seagreen'
            else:
                v1, v2 = esf["My"]
                cor = 'darkorange'
                
            # Identifica direção normal para jogar o desenho
            if abs(dz)/L > 0.95: nx, ny, nz = 1, 0, 0
            else: nx, ny, nz = 0, 0, 1
                
            ox1, oy1, oz1 = x1 + nx*v1*escala, y1 + ny*v1*escala, z1 + nz*v1*escala
            ox2, oy2, oz2 = x2 + nx*v2*escala, y2 + ny*v2*escala, z2 + nz*v2*escala
            
            # Linha de contorno do diagrama
            fig.add_trace(go.Scatter3d(
                x=[x1, ox1, ox2, x2], y=[y1, oy1, oy2, y2], z=[z1, oz1, oz2, z2],
                mode='lines', line=dict(color=cor, width=3), showlegend=False
            ))
            
            # Hachuras (linhas de preenchimento)
            hx, hy, hz = [], [], []
            for step in range(1, 5):
                f = step / 5.0
                px, py, pz = x1 + f*dx, y1 + f*dy, z1 + f*dz
                val = v1 + f*(v2 - v1)
                hx.extend([px, px + nx*val*escala, None])
                hy.extend([py, py + ny*val*escala, None])
                hz.extend([pz, pz + nz*val*escala, None])
                
            fig.add_trace(go.Scatter3d(x=hx, y=hy, z=hz, mode='lines', line=dict(color=cor, width=1), showlegend=False))

    fig.update_layout(scene=dict(xaxis_title='X (m)', yaxis_title='Y (m)', zaxis_title='Z (m)', aspectmode='data'), margin=dict(l=0, r=0, b=0, t=0), height=650)
    return fig


def gerar_relatorio_txt(dados, res_analise, resultados_comp, tudo_aprovado):
    data_atual = datetime.now().strftime("%d/%m/%Y às %H:%M")
    status_global = "APROVADA" if tudo_aprovado else "REPROVADA (Requer revisão de perfis)"
    
    relatorio = f"""=========================================================
      MEMÓRIA DE CÁLCULO ESTRUTURAL - DIMENSIONADOR 3D
=========================================================
Data de Geração: {data_atual}
Status Global da Estrutura: {status_global}

1. DADOS GEOMÉTRICOS E DE CONTORNO
---------------------------------------------------------
- Sistema Principal: {dados['sistema_principal']}
- Forma da Cobertura: {dados['forma_cobertura']}
- Tipo de Pilar: {dados['tipo_pilar']}
- Vão Transversal (X): {dados['vao_x']:.2f} m
- Comprimento Longitudinal (Y): {dados['comp_y']:.2f} m
- Pé-direito (Z): {dados['altura_z']:.2f} m
- Espaçamento entre Pórticos: {dados['espacamento']:.2f} m

2. CARGAS DE PROJETO (ELU)
---------------------------------------------------------
- Carga de Vento Líquida na Cobertura: {dados['q_vento_liquido']:.3f} kN/m²
>> CARGA DE PROJETO COMBINADA (ELU): {dados['q_elu']:.2f} kN/m²

3. ESFORÇOS SOLICITANTES MÁXIMOS
---------------------------------------------------------
- Esforço Normal Máximo (N_sd): {res_analise['n_max_kn']:.2f} kN
- Esforço Cortante Máximo (V_sd): {res_analise['v_max_kn']:.2f} kN
- Momento Fletor Máximo (M_sd): {res_analise['m_max_knm']:.2f} kNm

4. VERIFICAÇÃO NBR 8800
---------------------------------------------------------\n"""
    for v in resultados_comp:
        status_comp = "APROVADO" if v['aprovado'] else "REPROVADO"
        relatorio += f"[{v['componente'].upper()}]\n  Perfil: {v['perfil']} ({v['familia']})\n  Status: {status_comp} (Taxa: {v['taxa_maxima']:.1f}%)\n\n"
    return relatorio


def main():
    st.title("🏗️ Dimensionamento de Estruturas Metálicas 3D")
    st.caption("Conformidade: NBR 8800 | NBR 6120 | NBR 6123")

    if "res_analise" not in st.session_state:
        st.session_state.res_analise = None

    # MENU LATERAL
    st.sidebar.title("Configurações Gerais")
    sistema_principal = st.sidebar.selectbox("Sistema Principal", ["Pórtico Alma Cheia", "Tesoura Plana (Treliçada)", "Arco"])
    tipo_pilar = st.sidebar.selectbox("Tipo de Pilar/Suporte", ["Pilar Metálico", "Pilar de Concreto Armado (Apoio Rígido)", "Sem Pilar (Apenas Cobertura)"])

    forma_cobertura = "Não se aplica"
    n_paineis = 6
    if sistema_principal != "Arco":
        forma_cobertura = st.sidebar.selectbox("Forma da Cobertura", ["2 Águas", "1 Água"])
        inclinacao = st.sidebar.number_input("Inclinação do Telhado [%]", min_value=1.0, max_value=100.0, value=10.0, step=1.0)
        if sistema_principal == "Tesoura Plana (Treliçada)":
            n_paineis = st.sidebar.slider("Número Total de Painéis da Treliça", min_value=2, max_value=60, value=6, step=2)
    else:
        flecha_arco = st.sidebar.number_input("Flecha do Arco (m)", min_value=1.0, max_value=20.0, value=3.0, step=0.5)

    vao_x = st.sidebar.number_input("Vão Transversal (X) [m]", min_value=2.0, max_value=60.0, value=15.0, step=1.0)
    comp_y = st.sidebar.number_input("Comprimento Longitudinal (Y) [m]", min_value=2.0, max_value=120.0, value=30.0, step=1.0)
    altura_z = st.sidebar.number_input("Pé-direito (Z) [m]", min_value=0.0 if tipo_pilar == "Sem Pilar" else 2.0, max_value=20.0, value=6.0 if tipo_pilar != "Sem Pilar" else 0.0, step=0.5)
    espacamento = st.sidebar.number_input("Espaçamento entre Pórticos [m]", min_value=2.0, max_value=12.0, value=5.0, step=0.5)

    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Perfis Estruturais (NBR 8800)")
    tipo_aco = st.sidebar.selectbox("Aço Estrutural", list(PROPRIEDADES_ACO.keys()))
    lista_perfis = list(CATALOGO_COMPLETO.keys())
    lista_chapa = list(CATALOGO_CHAPA_DOBRADA.keys())

    perfil_pilares = st.sidebar.selectbox("Pilares", lista_perfis, index=3) if tipo_pilar == "Pilar Metálico" else "N/A"
    perfil_tercas = st.sidebar.selectbox("Terças de Cobertura", lista_chapa, index=1)
    perfil_banzo_sup = st.sidebar.selectbox("Banzo Superior", lista_perfis, index=3)
    perfil_banzo_inf = st.sidebar.selectbox("Banzo Inferior", lista_perfis, index=3 if sistema_principal != "Tesoura Plana (Treliçada)" else 10)
    perfil_diagonais = st.sidebar.selectbox("Diagonais", lista_perfis, index=14 if sistema_principal == "Tesoura Plana (Treliçada)" else 3)
    perfil_montantes = st.sidebar.selectbox("Montantes", lista_perfis, index=11 if sistema_principal == "Tesoura Plana (Treliçada)" else 3)

    st.sidebar.markdown("---")
    st.sidebar.subheader("🔒 Condições de Contorno")
    apoios_base = st.sidebar.selectbox("Vínculos na Base", ["Engastado (Trava Translações e Rotações)", "Articulado (Trava apenas Translações)"])

    st.sidebar.markdown("---")
    st.sidebar.subheader("🌪️ Cargas e Vento (NBR 6120/6123)")
    tipo_telha = st.sidebar.selectbox("Tipo de Cobertura", ["Trapezoidal (0.05 kN/m²)", "Termoacústica (0.15 kN/m²)", "Fibrocimento (0.18 kN/m²)"])
    carga_inst = st.sidebar.number_input("Carga Instalações [kN/m²]", min_value=0.0, value=0.10, step=0.02)
    sobrecarga = st.sidebar.number_input("Sobrecarga [kN/m²]", min_value=0.0, value=0.25, step=0.05)
    
    v0 = st.sidebar.number_input("Velocidade V0 [m/s]", min_value=30.0, max_value=60.0, value=40.0, step=1.0)
    s1 = float(st.sidebar.selectbox("Fator S1", ["Plano (1.00)", "Talude (1.10)", "Vale (0.90)"]).split("(")[1].split(")")[0])
    s2 = st.sidebar.number_input("Fator S2", min_value=0.50, max_value=1.50, value=1.00, step=0.01)
    s3 = float(st.sidebar.selectbox("Fator S3", ["Grupo 1 (1.10)", "Grupo 2 (1.00)"]).split("(")[1].split(")")[0])
    cpe = st.sidebar.number_input("Coef. Pressão Externa (Cpe)", min_value=-2.0, max_value=2.0, value=-0.80, step=0.10)
    cpi = st.sidebar.number_input("Coef. Pressão Interna (Cpi)", min_value=-1.0, max_value=1.0, value=0.20, step=0.10)
    c_arrasto = st.sidebar.number_input("Fator Arrasto (Ca)", min_value=0.5, max_value=2.0, value=1.20, step=0.10)

    # ABAS
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📐 Geometria", "🌪️ Cargas", "⚙️ Análise", "✅ Verificação", "📊 Diagramas", "📦 BIM"])

    # Cargas
    peso_telha = float(tipo_telha.split("(")[1].split(" ")[0])
    g_total = peso_telha + carga_inst 
    q_sobre = sobrecarga 
    vk = v0 * s1 * s2 * s3
    q_dinamica = 0.613 * (vk ** 2) / 1000 
    cp_liquido = cpe - cpi
    q_vento_liquido = q_dinamica * cp_liquido * c_arrasto 
    q_elu = (1.25 * g_total) + (1.50 * q_sobre) + (1.40 * abs(q_vento_liquido))

    # Geometria Paramétrica Simplificada
    y_coords = np.arange(0, comp_y + espacamento, espacamento)
    if y_coords[-1] != comp_y: y_coords[-1] = comp_y
    all_x, all_y, all_z, edges, topos_esq, topos_dir, cumeeiras = [], [], [], [], [], [], []
    node_offset, has_pillar = 0, (tipo_pilar != "Sem Pilar")

    for y in y_coords:
        if sistema_principal == "Arco":
            x_pts = [0] + list(np.linspace(0, vao_x, 9)) + [vao_x]
            y_pts = [y] * 11
            z_pts = ([0] if has_pillar else [altura_z]) + [altura_z + flecha_arco * (1 - (2*(x-vao_x/2)/vao_x)**2) for x in x_pts[1:-1]] + ([0] if has_pillar else [altura_z])
            local_edges = [(0, 1), (9, 10)] if has_pillar else []
            for i in range(1, 9): local_edges.append((i, i+1))
            topos_esq.append(node_offset + (1 if has_pillar else 0))
            topos_dir.append(node_offset + (9 if has_pillar else 10))
            cumeeiras.append(node_offset + 5)

        elif sistema_principal == "Tesoura Plana (Treliçada)":
            if forma_cobertura == "1 Água":
                x_sub = np.linspace(0, vao_x, n_paineis + 1)
                x_pts = ([0, vao_x] if has_pillar else []) + list(x_sub) + list(x_sub)
                y_pts = [y] * len(x_pts)
                z_base = [0, 0] if has_pillar else []
                z_pts = z_base + [altura_z] * (n_paineis + 1) + list(altura_z + (vao_x - x_sub) * (inclinacao / 100.0))
                off = 2 if has_pillar else 0
                local_edges = [(0, off), (1, off + n_paineis)] if has_pillar else []
                idx_inf, idx_sup = off, off + (n_paineis + 1)
                for i in range(n_paineis):
                    local_edges.extend([(idx_inf+i, idx_inf+i+1), (idx_sup+i, idx_sup+i+1), (idx_inf+i, idx_sup+i), (idx_inf+i, idx_sup+i+1)])
                local_edges.append((idx_inf + n_paineis, idx_sup + n_paineis)) 
                topos_esq.append(node_offset + idx_sup)
                topos_dir.append(node_offset + idx_sup + n_paineis)
            else: 
                n_lado = n_paineis // 2
                x_all = np.concatenate([np.linspace(0, vao_x/2, n_lado + 1), np.linspace(vao_x/2, vao_x, n_lado + 1)[1:]])
                z_sup_local = np.where(x_all <= vao_x/2, altura_z + x_all*(inclinacao/100.0), altura_z + (vao_x-x_all)*(inclinacao/100.0))
                x_pts = ([0, vao_x] if has_pillar else []) + list(x_all) + list(x_all)
                y_pts = [y] * len(x_pts)
                z_pts = ([0, 0] if has_pillar else []) + [altura_z] * len(x_all) + list(z_sup_local)
                off = 2 if has_pillar else 0
                local_edges = [(0, off), (1, off + len(x_all) - 1)] if has_pillar else []
                idx_inf, idx_sup, tot_p = off, off + len(x_all), len(x_all) - 1
                for i in range(tot_p):
                    local_edges.extend([(idx_inf+i, idx_inf+i+1), (idx_sup+i, idx_sup+i+1), (idx_inf+i, idx_sup+i)])
                    local_edges.append((idx_inf+i, idx_sup+i+1) if i < tot_p//2 else (idx_inf+i+1, idx_sup+i))
                local_edges.append((idx_inf + tot_p, idx_sup + tot_p))
                topos_esq.append(node_offset + idx_sup)
                topos_dir.append(node_offset + idx_sup + tot_p)
                cumeeiras.append(node_offset + idx_sup + (tot_p // 2))

        else: 
            h_cum = altura_z + (vao_x / 2.0) * (inclinacao / 100.0)
            if forma_cobertura == "2 Águas":
                x_pts = ([0, vao_x] if has_pillar else []) + [0, vao_x, vao_x/2]
                y_pts = [y] * len(x_pts)
                z_pts = ([0, 0] if has_pillar else []) + [altura_z, altura_z, h_cum]
                off = 2 if has_pillar else 0
                local_edges = ([(0, off), (1, off+1)] if has_pillar else []) + [(off, off+2), (off+2, off+1)]
                topos_esq.append(node_offset + off)
                topos_dir.append(node_offset + off + 1)
                cumeeiras.append(node_offset + off + 2)
            else:
                h_cum = altura_z + vao_x * (inclinacao / 100.0)
                x_pts = ([0, vao_x] if has_pillar else []) + [0, vao_x]
                y_pts = [y] * len(x_pts)
                z_pts = ([0, 0] if has_pillar else []) + [altura_z, h_cum]
                off = 2 if has_pillar else 0
                local_edges = ([(0, off), (1, off+1)] if has_pillar else []) + [(off, off+1)]
                topos_esq.append(node_offset + off)
                topos_dir.append(node_offset + off + 1)

        all_x.extend(x_pts); all_y.extend(y_pts); all_z.extend(z_pts)
        for edge in local_edges: edges.append((edge[0] + node_offset, edge[1] + node_offset))
        node_offset += len(x_pts)
        
    for i in range(len(topos_esq) - 1):
        edges.extend([(topos_esq[i], topos_esq[i+1]), (topos_dir[i], topos_dir[i+1])])
        if (forma_cobertura == "2 Águas" or sistema_principal == "Arco") and len(cumeeiras) > i: edges.append((cumeeiras[i], cumeeiras[i+1]))

    with tab1:
        fig = go.Figure()
        fig.add_trace(go.Scatter3d(x=all_x, y=all_y, z=all_z, mode='markers', marker=dict(size=4, color='red'), showlegend=False))
        for edge in edges:
            fig.add_trace(go.Scatter3d(x=[all_x[edge[0]], all_x[edge[1]]], y=[all_y[edge[0]], all_y[edge[1]]], z=[all_z[edge[0]], all_z[edge[1]]], mode='lines', line=dict(color='blue', width=4), showlegend=False))
        fig.update_layout(scene=dict(xaxis_title='X (m)', yaxis_title='Y (m)', zaxis_title='Z (m)', aspectmode='data'), margin=dict(l=0, r=0, b=0, t=0), height=550)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("🌪️ Detalhamento de Cargas e Vento (ELU)")
        st.info(f"**Carga de Projeto Total (q_ELU):** {q_elu:.2f} kN/m²")

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
            c1.metric("Normal Máx", f"{res['n_max_kn']:.2f} kN")
            c2.metric("Cortante Máx", f"{res['v_max_kn']:.2f} kN")
            c3.metric("Momento Máx", f"{res['m_max_knm']:.2f} kNm")
            c4.metric("Deslocamento Máx", f"{res['desloc_max_mm']:.2f} mm")

    with tab4:
        st.subheader("✅ Verificação NBR 8800 e Memória de Cálculo")
        if not st.session_state.res_analise: st.warning("⚠️ Execute a Análise Estrutural na Aba 3 primeiro.")
        else:
            res = st.session_state.res_analise
            verificador = VerificadorNBR8800(tipo_aco)
            componentes = [("Terças de Cobertura", perfil_tercas, 0.30), ("Banzo Superior", perfil_banzo_sup, 0.90), ("Banzo Inferior", perfil_banzo_inf, 0.75), ("Diagonais", perfil_diagonais, 0.50), ("Montantes", perfil_montantes, 0.35)]
            if tipo_pilar == "Pilar Metálico": componentes.insert(0, ("Pilares Metálicos", perfil_pilares, 1.0))

            resultados_comp = []
            tudo_aprovado = True
            for nome_comp, perfil, fator in componentes:
                v = verificador.verificar_elemento(perfil, res["n_max_kn"], res["v_max_kn"], res["m_max_knm"], res["desloc_max_mm"], vao_x, fator)
                v["componente"] = nome_comp
                resultados_comp.append(v)
                if not v["aprovado"]: tudo_aprovado = False

            if tudo_aprovado: st.success("### 🎉 ESTRUTURA APROVADA!")
            else: st.error("### ❌ ESTRUTURA REPROVADA!")
            
            # Botão de Memória de Cálculo
            st.markdown("---")
            dados_relatorio = {"sistema_principal": sistema_principal, "forma_cobertura": forma_cobertura, "tipo_pilar": tipo_pilar, "apoios_base": apoios_base, "vao_x": vao_x, "comp_y": comp_y, "altura_z": altura_z, "espacamento": espacamento, "tipo_telha": tipo_telha, "g_total": g_total, "q_sobre": q_sobre, "v0": v0, "s1": s1, "s2": s2, "s3": s3, "cpe": cpe, "cpi": cpi, "c_arrasto": c_arrasto, "q_dinamica": q_dinamica, "q_vento_liquido": q_vento_liquido, "q_elu": q_elu, "tipo_aco": tipo_aco}
            texto_memoria = gerar_relatorio_txt(dados_relatorio, res, resultados_comp, tudo_aprovado)
            st.download_button(label="📥 Baixar Memória de Cálculo (.txt)", data=texto_memoria, file_name="Memoria_Calculo.txt", mime="text/plain", type="primary")
            st.markdown("---")

            for v in resultados_comp:
                st.write(f"#### 🔹 {v['componente']} — `{v['perfil']}`")
                st.progress(min(int(v['taxa_maxima']), 100))

    with tab5:
        st.subheader("📊 Diagramas de Esforços Internos e Reações")
        if not st.session_state.res_analise:
            st.warning("⚠️ Execute a Análise Estrutural na Aba 3 primeiro para visualizar os diagramas.")
        else:
            tipo_diagrama = st.selectbox(
                "Escolha o que deseja visualizar:",
                ["Esforço Normal (Tração/Compressão)", "Esforço Cortante (Vz)", "Momento Fletor (My)", "Reações de Apoio"]
            )
            fig_diag = desenhar_diagrama(st.session_state.res_analise, tipo_diagrama)
            st.plotly_chart(fig_diag, use_container_width=True)

    with tab6: st.write("Aguardando Exportação IFC.")

if __name__ == "__main__":
    main()
