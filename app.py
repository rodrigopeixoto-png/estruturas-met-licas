import streamlit as st
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
from modules.solver import MotorCalculo3D
from modules.checker import VerificadorNBR8800, CATALOGO_CHAPA_DOBRADA, CATALOGO_COMPLETO, PROPRIEDADES_ACO

st.set_page_config(page_title="Dimensionador Metálico 3D", page_icon="🏗️", layout="wide")

def desenhar_diagrama(res, tipo_diagrama):
    fig = go.Figure()
    nos, barras, esforcos = res["nos"], res["barras"], res["esforcos"]
    
    for n1, n2 in barras:
        x1, y1, z1 = nos[n1]
        x2, y2, z2 = nos[n2]
        fig.add_trace(go.Scatter3d(
            x=[x1, x2], y=[y1, y2], z=[z1, z2],
            mode='lines', line=dict(color='lightgrey', width=2), showlegend=False
        ))
        
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
            text=texts, textposition="top center", textfont=dict(size=11, color='purple'), showlegend=False
        ))
    else:
        max_val = 1e-5
        for esf in esforcos:
            v1, v2 = (esf["N"] if "Normal" in tipo_diagrama else (esf["Vz"] if "Cortante" in tipo_diagrama else esf["My"]))
            max_val = max(max_val, abs(v1), abs(v2))
            
        escala = 1.2 / max_val
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
                
            nx, ny, nz = (1, 0, 0) if abs(dz)/L > 0.95 else (0, 0, 1)
            ox1, oy1, oz1 = x1 + nx*v1*escala, y1 + ny*v1*escala, z1 + nz*v1*escala
            ox2, oy2, oz2 = x2 + nx*v2*escala, y2 + ny*v2*escala, z2 + nz*v2*escala
            
            fig.add_trace(go.Scatter3d(
                x=[x1, ox1, ox2, x2], y=[y1, oy1, oy2, y2], z=[z1, oz1, oz2, z2],
                mode='lines', line=dict(color=cor, width=3), showlegend=False
            ))

    fig.update_layout(scene=dict(xaxis_title='X (m)', yaxis_title='Y (m)', zaxis_title='Z (m)', aspectmode='data'), margin=dict(l=0, r=0, b=0, t=0), height=600)
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
- Tipo de Pilar: {dados['tipo_pilar']}
- Distribuição dos Pilares: {dados.get('distribuicao_pilares', 'N/A')}
- Vão Transversal (X): {dados['vao_x']:.2f} m
- Comprimento Longitudinal (Y): {dados['comp_y']:.2f} m
- Altura (Z): {dados['altura_z']:.2f} m
- Espaçamento entre Pórticos Principais: {dados['espacamento']:.2f} m
"""
    if dados['sistema_principal'] == "Mezanino / Passarela Metálica":
        relatorio += f"- Espaçamento entre Vigotas Transversais: {dados['espacamento_vigota']:.2f} m\n"
        relatorio += f"- Tipo de Piso: {dados['tipo_piso']}\n"

    relatorio += f"""
2. CARGAS DE PROJETO (ELU - NBR 6120 / NBR 8800)
---------------------------------------------------------
- Carga Permanente Total (G): {dados['g_total']:.2f} kN/m²
- Sobrecarga Normativa de Uso (Q): {dados['q_sobre']:.2f} kN/m²
>> CARGA DE PROJETO COMBINADA (ELU): {dados['q_elu']:.2f} kN/m²

3. ESFORÇOS SOLICITANTES MÁXIMOS
---------------------------------------------------------
- Esforço Normal Máximo (N_sd): {res_analise['n_max_kn']:.2f} kN
- Esforço Cortante Máximo (V_sd): {res_analise['v_max_kn']:.2f} kN
- Momento Fletor Máximo (M_sd): {res_analise['m_max_knm']:.2f} kNm
- Deslocamento Máximo (Flecha ELS): {res_analise['desloc_max_mm']:.2f} mm

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
    sistema_principal = st.sidebar.selectbox(
        "Sistema Principal", 
        ["Pórtico Alma Cheia", "Tesoura Plana (Treliçada)", "Arco", "Mezanino / Passarela Metálica"]
    )
    
    tipo_pilar = st.sidebar.selectbox(
        "Tipo de Pilar/Suporte", 
        ["Pilar Metálico", "Pilar de Concreto Armado (Apoio Rígido)", "Sem Pilar (Apenas Estrutura Superior)"]
    )
    
    distribuicao_pilares = "Em todos os pórticos"
    if tipo_pilar != "Sem Pilar (Apenas Estrutura Superior)":
        distribuicao_pilares = st.sidebar.selectbox(
            "Distribuição de Pilares", 
            ["Em todos os pórticos", "Apenas nos 4 cantos extremos"]
        )

    forma_cobertura = "Não se aplica"
    n_paineis = 6
    espacamento_vigota = 1.00
    tipo_piso = "N/A"

    if sistema_principal == "Mezanino / Passarela Metálica":
        st.sidebar.markdown("**📐 Parâmetros do Piso/Passarela**")
        tipo_piso = st.sidebar.selectbox(
            "Tipo de Piso", 
            ["Painel Wall / Masterboard (0.30 kN/m²)", "Steel Deck + Concreto (2.00 kN/m²)", "Chapa Xadrez Metálica (0.40 kN/m²)", "Painel OSB / Madeira (0.25 kN/m²)"]
        )
        sobrecarga_opcao = st.sidebar.selectbox(
            "Uso / Sobrecarga (NBR 6120)", 
            [
                "Escritórios / Leve (2.50 kN/m²)", 
                "Residencial (1.50 kN/m²)", 
                "Comercial / Lojas (3.00 kN/m²)", 
                "Depósito Leve (4.00 kN/m²)", 
                "Depósito Pesado (5.00 kN/m²)",
                "Passarela - Manutenção/Sem Público (3.00 kN/m²)",
                "Passarela - Acesso Público (5.00 kN/m²)"
            ]
        )
        sobrecarga = float(sobrecarga_opcao.split("(")[1].split(" ")[0])
        espacamento_vigota = st.sidebar.number_input("Espaçamento Vigotas Transversais [m]", min_value=0.40, max_value=3.00, value=1.00, step=0.10)

    elif sistema_principal != "Arco":
        forma_cobertura = st.sidebar.selectbox("Forma da Cobertura", ["2 Águas", "1 Água"])
        inclinacao = st.sidebar.number_input("Inclinação do Telhado [%]", min_value=1.0, max_value=100.0, value=10.0, step=1.0)
        if sistema_principal == "Tesoura Plana (Treliçada)":
            n_paineis = st.sidebar.slider("Número Total de Painéis da Treliça", min_value=2, max_value=60, value=6, step=2)
    else:
        flecha_arco = st.sidebar.number_input("Flecha do Arco (m)", min_value=1.0, max_value=20.0, value=3.0, step=0.5)

    vao_x = st.sidebar.number_input("Vão Transversal (X) [m]", min_value=1.0, max_value=60.0, value=15.0 if sistema_principal != "Mezanino / Passarela Metálica" else 6.0, step=0.5)
    comp_y = st.sidebar.number_input("Comprimento Longitudinal (Y) [m]", min_value=2.0, max_value=120.0, value=30.0 if sistema_principal != "Mezanino / Passarela Metálica" else 12.0, step=0.5)
    altura_z = st.sidebar.number_input("Pé-direito / Altura (Z) [m]", min_value=0.0 if tipo_pilar == "Sem Pilar (Apenas Estrutura Superior)" else 1.5, max_value=20.0, value=3.0 if sistema_principal == "Mezanino / Passarela Metálica" else 6.0, step=0.5)
    espacamento = st.sidebar.number_input("Espaçamento entre Pórticos/Apoios [m]", min_value=1.5, max_value=12.0, value=3.0 if sistema_principal == "Mezanino / Passarela Metálica" else 5.0, step=0.5)

    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Perfis Estruturais (NBR 8800)")
    tipo_aco = st.sidebar.selectbox("Aço Estrutural", list(PROPRIEDADES_ACO.keys()))
    
    lista_perfis = list(CATALOGO_COMPLETO.keys())
    lista_chapa = list(CATALOGO_CHAPA_DOBRADA.keys())

    if sistema_principal == "Mezanino / Passarela Metálica":
        perfil_pilares = st.sidebar.selectbox("Pilares", lista_perfis, index=lista_perfis.index("W 200 x 22.5") if "W 200 x 22.5" in lista_perfis else 0) if tipo_pilar == "Pilar Metálico" else "N/A"
        perfil_viga_principal = st.sidebar.selectbox("Vigas Principais (Longitudinais)", lista_perfis, index=lista_perfis.index("W 250 x 25.3") if "W 250 x 25.3" in lista_perfis else 0)
        perfil_vigotas = st.sidebar.selectbox("Vigas Secundárias (Transversais)", lista_perfis, index=lista_perfis.index("U 150 x 50 x 3.00") if "U 150 x 50 x 3.00" in lista_perfis else 0)
    else:
        perfil_pilares = st.sidebar.selectbox("Pilares", lista_perfis, index=lista_perfis.index("W 250 x 25.3") if "W 250 x 25.3" in lista_perfis else 0) if tipo_pilar == "Pilar Metálico" else "N/A"
        perfil_tercas = st.sidebar.selectbox("Terças de Cobertura", lista_chapa, index=lista_chapa.index("U 100 x 40 x 2.25") if "U 100 x 40 x 2.25" in lista_chapa else 0)
        perfil_banzo_sup = st.sidebar.selectbox("Banzo Superior", lista_perfis, index=lista_perfis.index("U 150 x 50 x 3.00") if "U 150 x 50 x 3.00" in lista_perfis else 0)
        perfil_banzo_inf = st.sidebar.selectbox("Banzo Inferior", lista_perfis, index=lista_perfis.index("U 150 x 50 x 3.00") if "U 150 x 50 x 3.00" in lista_perfis else 0)
        perfil_diagonais = st.sidebar.selectbox("Diagonais", lista_perfis, index=lista_perfis.index('2x L 2" x 3/16" (Dupla)') if '2x L 2" x 3/16" (Dupla)' in lista_perfis else 0)
        perfil_montantes = st.sidebar.selectbox("Montantes", lista_perfis, index=lista_perfis.index("UE 100 x 50 x 17 x 2.25") if "UE 100 x 50 x 17 x 2.25" in lista_perfis else 0)

    st.sidebar.markdown("---")
    st.sidebar.subheader("🔒 Condições de Contorno")
    apoios_base = st.sidebar.selectbox("Vínculos na Base", ["Engastado (Trava Translações e Rotações)", "Articulado (Trava apenas Translações)"])

    st.sidebar.markdown("---")
    st.sidebar.subheader("🌪️ Cargas / Vento")
    if sistema_principal != "Mezanino / Passarela Metálica":
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

    # CÁLCULOS DE CARGAS
    if sistema_principal == "Mezanino / Passarela Metálica":
        peso_piso = float(tipo_piso.split("(")[1].split(" ")[0])
        carga_inst = 0.15
        g_total = peso_piso + carga_inst
        q_sobre = sobrecarga
        v0 = s1 = s2 = s3 = cpe = cpi = c_arrasto = q_vento_liquido = 0.0
        q_elu = (1.25 * g_total) + (1.50 * q_sobre)
    else:
        peso_telha = float(tipo_telha.split("(")[1].split(" ")[0])
        g_total = peso_telha + carga_inst 
        q_sobre = sobrecarga 
        vk = v0 * s1 * s2 * s3
        q_dinamica = 0.613 * (vk ** 2) / 1000 
        cp_liquido = cpe - cpi
        q_vento_liquido = q_dinamica * cp_liquido * c_arrasto 
        q_elu = (1.25 * g_total) + (1.50 * q_sobre) + (1.40 * abs(q_vento_liquido))

    # GEOMETRIA PARAMÉTRICA 3D
    y_coords = np.arange(0, comp_y + espacamento, espacamento)
    if y_coords[-1] != comp_y: y_coords[-1] = comp_y
    all_x, all_y, all_z, edges = [], [], [], []
    has_pillar = (tipo_pilar != "Sem Pilar (Apenas Estrutura Superior)")

    if sistema_principal == "Mezanino / Passarela Metálica":
        y_vigotas = np.arange(0, comp_y + espacamento_vigota, espacamento_vigota)
        if y_vigotas[-1] != comp_y: y_vigotas[-1] = comp_y
        
        dict_nos = {}
        def add_no(x, y, z):
            pt = (round(x, 3), round(y, 3), round(z, 3))
            if pt not in dict_nos:
                dict_nos[pt] = len(dict_nos)
                all_x.append(pt[0]); all_y.append(pt[1]); all_z.append(pt[2])
            return dict_nos[pt]

        # 1. Vigotas Transversais
        for y_v in y_vigotas:
            n_esq = add_no(0, y_v, altura_z)
            n_dir = add_no(vao_x, y_v, altura_z)
            edges.append((n_esq, n_dir)) 

        # 2. Vigas Principais
        for i in range(len(y_vigotas) - 1):
            n1_esq = add_no(0, y_vigotas[i], altura_z)
            n2_esq = add_no(0, y_vigotas[i+1], altura_z)
            edges.append((n1_esq, n2_esq))

            n1_dir = add_no(vao_x, y_vigotas[i], altura_z)
            n2_dir = add_no(vao_x, y_vigotas[i+1], altura_z)
            edges.append((n1_dir, n2_dir))

        # 3. Pilares (condicionados)
        if has_pillar:
            for i_y, y_p in enumerate(y_coords):
                if distribuicao_pilares == "Apenas nos 4 cantos extremos" and i_y != 0 and i_y != (len(y_coords) - 1):
                    continue
                n_topo_esq = add_no(0, y_p, altura_z)
                n_base_esq = add_no(0, y_p, 0)
                edges.append((n_base_esq, n_topo_esq))

                n_topo_dir = add_no(vao_x, y_p, altura_z)
                n_base_dir = add_no(vao_x, y_p, 0)
                edges.append((n_base_dir, n_topo_dir))

    else:
        cobertura_por_frame = []
        node_offset = 0
        for i_y, y in enumerate(y_coords):
            has_pillar_local = has_pillar and (distribuicao_pilares == "Em todos os pórticos" or i_y == 0 or i_y == len(y_coords) - 1)
            nos_cobertura_local = []
            
            if sistema_principal == "Arco":
                x_arco = list(np.linspace(0, vao_x, 9))
                z_arco = [altura_z + flecha_arco * (1 - (2*(x-vao_x/2)/vao_x)**2) for x in x_arco]
                x_pts = ([0, vao_x] if has_pillar_local else []) + x_arco
                y_pts = [y] * len(x_pts)
                z_pts = ([0, 0] if has_pillar_local else []) + z_arco
                off = 2 if has_pillar_local else 0
                local_edges = [(0, off), (1, off + 8)] if has_pillar_local else []
                for i in range(8): local_edges.append((off + i, off + i + 1))
                nos_cobertura_local = [node_offset + off + i for i in range(9)]

            elif sistema_principal == "Tesoura Plana (Treliçada)":
                if forma_cobertura == "1 Água":
                    x_sub = np.linspace(0, vao_x, n_paineis + 1)
                    x_pts = ([0, vao_x] if has_pillar_local else []) + list(x_sub) + list(x_sub)
                    y_pts = [y] * len(x_pts)
                    z_pts = ([0, 0] if has_pillar_local else []) + [altura_z] * (n_paineis + 1) + list(altura_z + (vao_x - x_sub) * (inclinacao / 100.0))
                    off = 2 if has_pillar_local else 0
                    local_edges = [(0, off), (1, off + n_paineis)] if has_pillar_local else []
                    idx_inf, idx_sup = off, off + (n_paineis + 1)
                    for i in range(n_paineis):
                        local_edges.extend([(idx_inf+i, idx_inf+i+1), (idx_sup+i, idx_sup+i+1), (idx_inf+i, idx_sup+i), (idx_inf+i, idx_sup+i+1)])
                    local_edges.append((idx_inf + n_paineis, idx_sup + n_paineis)) 
                    nos_cobertura_local = [node_offset + idx_sup + p for p in range(n_paineis + 1)]
                else: 
                    n_lado = n_paineis // 2
                    x_all = np.concatenate([np.linspace(0, vao_x/2, n_lado + 1), np.linspace(vao_x/2, vao_x, n_lado + 1)[1:]])
                    z_sup_local = np.where(x_all <= vao_x/2, altura_z + x_all*(inclinacao/100.0), altura_z + (vao_x-x_all)*(inclinacao/100.0))
                    x_pts = ([0, vao_x] if has_pillar_local else []) + list(x_all) + list(x_all)
                    y_pts = [y] * len(x_pts)
                    z_pts = ([0, 0] if has_pillar_local else []) + [altura_z] * len(x_all) + list(z_sup_local)
                    off = 2 if has_pillar_local else 0
                    local_edges = [(0, off), (1, off + len(x_all) - 1)] if has_pillar_local else []
                    idx_inf, idx_sup, tot_p = off, off + len(x_all), len(x_all) - 1
                    for i in range(tot_p):
                        local_edges.extend([(idx_inf+i, idx_inf+i+1), (idx_sup+i, idx_sup+i+1), (idx_inf+i, idx_sup+i)])
                        local_edges.append((idx_inf+i, idx_sup+i+1) if i < tot_p//2 else (idx_inf+i+1, idx_sup+i))
                    local_edges.append((idx_inf + tot_p, idx_sup + tot_p))
                    nos_cobertura_local = [node_offset + idx_sup + p for p in range(len(x_all))]

            else: 
                h_cum = altura_z + (vao_x / 2.0) * (inclinacao / 100.0)
                if forma_cobertura == "2 Águas":
                    x_pts = ([0, vao_x] if has_pillar_local else []) + [0, vao_x, vao_x/2]
                    y_pts = [y] * len(x_pts)
                    z_pts = ([0, 0] if has_pillar_local else []) + [altura_z, altura_z, h_cum]
                    off = 2 if has_pillar_local else 0
                    local_edges = ([(0, off), (1, off+1)] if has_pillar_local else []) + [(off, off+2), (off+2, off+1)]
                    nos_cobertura_local = [node_offset + off, node_offset + off + 2, node_offset + off + 1]
                else:
                    h_cum = altura_z + vao_x * (inclinacao / 100.0)
                    x_pts = ([0, vao_x] if has_pillar_local else []) + [0, vao_x]
                    y_pts = [y] * len(x_pts)
                    z_pts = ([0, 0] if has_pillar_local else []) + [altura_z, h_cum]
                    off = 2 if has_pillar_local else 0
                    local_edges = ([(0, off), (1, off+1)] if has_pillar_local else []) + [(off, off+1)]
                    nos_cobertura_local = [node_offset + off, node_offset + off + 1]

            all_x.extend(x_pts); all_y.extend(y_pts); all_z.extend(z_pts)
            for edge in local_edges: edges.append((edge[0] + node_offset, edge[1] + node_offset))
            cobertura_por_frame.append(nos_cobertura_local)
            node_offset += len(x_pts)
            
        for i in range(len(cobertura_por_frame) - 1):
            for p in range(len(cobertura_por_frame[i])):
                edges.append((cobertura_por_frame[i][p], cobertura_por_frame[i+1][p]))

    with tab1:
        fig = go.Figure()
        fig.add_trace(go.Scatter3d(x=all_x, y=all_y, z=all_z, mode='markers', marker=dict(size=4, color='red'), showlegend=False))
        for edge in edges:
            fig.add_trace(go.Scatter3d(x=[all_x[edge[0]], all_x[edge[1]]], y=[all_y[edge[0]], all_y[edge[1]]], z=[all_z[edge[0]], all_z[edge[1]]], mode='lines', line=dict(color='blue', width=4), showlegend=False))
        fig.update_layout(scene=dict(xaxis_title='X (m)', yaxis_title='Y (m)', zaxis_title='Z (m)', aspectmode='data'), margin=dict(l=0, r=0, b=0, t=0), height=550)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("🌪️ Detalhamento de Cargas (NBR 6120 / NBR 8800)")
        c1, c2 = st.columns(2)
        with c1:
            st.info(f"**Carga Permanente Total (G):** {g_total:.2f} kN/m²")
            st.write(f"* **Sobrecarga de Utilização (Q):** {q_sobre:.2f} kN/m²")
        with c2:
            st.success(f"**Carga de Projeto Combinada (q_ELU):** {q_elu:.2f} kN/m²")

    with tab3:
        st.subheader("⚙️ Análise Estrutural Matricial 3D")
        if st.button("🚀 Executar Análise Estrutural", type="primary"):
            with st.spinner("Calculando matriz de rigidez e esforços..."):
                motor = MotorCalculo3D()
                motor.construir_malha(all_x, all_y, all_z, edges, apoios_base)
                espacamento_calc = espacamento_vigota if sistema_principal == "Mezanino / Passarela Metálica" else espacamento
                motor.aplicar_carga_distribuida(q_elu, vao_x, espacamento_calc)
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
        st.subheader("✅ Verificação de Segurança por Componente (NBR 8800)")
        if not st.session_state.res_analise: 
            st.warning("⚠️ Execute a Análise Estrutural na Aba 3 primeiro.")
        else:
            res = st.session_state.res_analise
            verificador = VerificadorNBR8800(tipo_aco)

            if sistema_principal == "Mezanino / Passarela Metálica":
                componentes = [
                    ("Vigas Secundárias (Transversais)", perfil_vigotas, 0.50),
                    ("Vigas Principais (Longitudinais)", perfil_viga_principal, 1.00)
                ]
            else:
                componentes = [
                    ("Terças de Cobertura", perfil_tercas, 0.30),
                    ("Banzo Superior", perfil_banzo_sup, 0.90),
                    ("Banzo Inferior", perfil_banzo_inf, 0.75),
                    ("Diagonais", perfil_diagonais, 0.50),
                    ("Montantes", perfil_montantes, 0.35)
                ]

            if tipo_pilar == "Pilar Metálico": 
                componentes.insert(0, ("Pilares Metálicos", perfil_pilares, 1.00))

            resultados_comp = []
            tudo_aprovado = True
            for nome_comp, perfil, fator in componentes:
                v = verificador.verificar_elemento(perfil, res["n_max_kn"], res["v_max_kn"], res["m_max_knm"], res["desloc_max_mm"], vao_x, fator)
                v["componente"] = nome_comp
                resultados_comp.append(v)
                if not v["aprovado"]: tudo_aprovado = False

            if tudo_aprovado: 
                st.success("### 🎉 TODOS OS COMPONENTES FORAM APROVADOS!")
            else: 
                st.error("### ❌ ESTRUTURA REPROVADA! (Ajuste a bitola dos perfis)")
            
            st.markdown("---")
            dados_relatorio = {
                "sistema_principal": sistema_principal, "forma_cobertura": forma_cobertura,
                "tipo_pilar": tipo_pilar, "distribuicao_pilares": distribuicao_pilares,
                "apoios_base": apoios_base, "vao_x": vao_x, "comp_y": comp_y,
                "altura_z": altura_z, "espacamento": espacamento, "espacamento_vigota": espacamento_vigota,
                "tipo_piso": tipo_piso, "g_total": g_total, "q_sobre": q_sobre, "q_vento_liquido": q_vento_liquido if sistema_principal != "Mezanino / Passarela Metálica" else 0.0,
                "q_elu": q_elu, "tipo_aco": tipo_aco
            }
            texto_memoria = gerar_relatorio_txt(dados_relatorio, res, resultados_comp, tudo_aprovado)
            st.download_button(label="📥 Baixar Memória de Cálculo (.txt)", data=texto_memoria, file_name="Memoria_Calculo.txt", mime="text/plain", type="primary")
            st.markdown("---")

            for v in resultados_comp:
                st.write(f"#### 🔹 {v['componente']} — `{v['perfil']}` *({v['familia']})*")
                c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 2])
                c1.metric("Status", "✅ Ok" if v['aprovado'] else "❌ Reprovado")
                c2.metric("Taxa Utilização", f"{v['taxa_maxima']:.1f}%")
                c3.metric("Momento (M_sd/M_rd)", f"{v['ratio_M']:.1f}%")
                c4.metric("Normal (N_sd/N_rd)", f"{v['ratio_N']:.1f}%")
                c5.metric("Flecha (δ_sd/δ_lim)", f"{v['ratio_delta']:.1f}%")
                
                prog_val = min(max(int(v['taxa_maxima']), 0), 100)
                st.progress(prog_val)
                st.markdown("---")

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
