import streamlit as st
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import tempfile
import os

try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

from modules.solver import MotorCalculo3D
from modules.checker import VerificadorNBR8800, CATALOGO_CHAPA_DOBRADA, CATALOGO_COMPLETO, PROPRIEDADES_ACO

st.set_page_config(page_title="Dimensionador Metálico 3D", page_icon="🏗️", layout="wide")

def desenhar_diagrama(res, tipo_diagrama):
    fig = go.Figure()
    nos, barras, esforcos = res["nos"], res["barras"], res["esforcos"]
    
    if tipo_diagrama == "Deslocamentos (Deformada)":
        for n1, n2 in barras:
            x1, y1, z1 = nos[n1]
            x2, y2, z2 = nos[n2]
            fig.add_trace(go.Scatter3d(x=[x1, x2], y=[y1, y2], z=[z1, z2], mode='lines', line=dict(color='lightgrey', width=1, dash='dash'), showlegend=False))
            
        U = res.get("deslocamentos_nodais", [])
        if U:
            U_arr = np.array(U)
            max_disp = np.max(np.abs(U_arr))
            coords_arr = np.array(nos)
            scale = 0.0
            if max_disp > 1e-6:
                dim_max = max(np.max(coords_arr[:, 0]), np.max(coords_arr[:, 1]), np.max(coords_arr[:, 2]))
                scale = (dim_max * 0.1) / max_disp 

            for n1, n2 in barras:
                x1 = nos[n1][0] + U[n1*6] * scale
                y1 = nos[n1][1] + U[n1*6+1] * scale
                z1 = nos[n1][2] + U[n1*6+2] * scale
                
                x2 = nos[n2][0] + U[n2*6] * scale
                y2 = nos[n2][1] + U[n2*6+1] * scale
                z2 = nos[n2][2] + U[n2*6+2] * scale
                
                fig.add_trace(go.Scatter3d(x=[x1, x2], y=[y1, y2], z=[z1, z2], mode='lines', line=dict(color='red', width=5), showlegend=False))

    elif tipo_diagrama == "Reações de Apoio":
        for n1, n2 in barras:
            x1, y1, z1 = nos[n1]
            x2, y2, z2 = nos[n2]
            fig.add_trace(go.Scatter3d(x=[x1, x2], y=[y1, y2], z=[z1, z2], mode='lines', line=dict(color='lightgrey', width=2), showlegend=False))
            
        rx, ry, rz, texts = [], [], [], []
        for no_idx, reac in res["reacoes"].items():
            x, y, z = nos[no_idx]
            Fx, Fy, Fz = reac[0], reac[1], reac[2]
            rx.append(x); ry.append(y); rz.append(z)
            texts.append(f"Fz: {Fz:.1f}kN<br>Fx: {Fx:.1f}kN<br>Fy: {Fy:.1f}kN")
        fig.add_trace(go.Scatter3d(x=rx, y=ry, z=rz, mode='markers+text', marker=dict(size=8, color='purple', symbol='diamond'), text=texts, textposition="top center", textfont=dict(size=11, color='purple'), showlegend=False))
    
    else:
        for n1, n2 in barras:
            x1, y1, z1 = nos[n1]
            x2, y2, z2 = nos[n2]
            fig.add_trace(go.Scatter3d(x=[x1, x2], y=[y1, y2], z=[z1, z2], mode='lines', line=dict(color='lightgrey', width=2), showlegend=False))

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
            
            if "Normal" in tipo_diagrama: cor = 'royalblue' if (esf["N"][0]+esf["N"][1]) > 0 else 'crimson'
            elif "Cortante" in tipo_diagrama: cor = 'seagreen'
            else: cor = 'darkorange'
                
            v1, v2 = (esf["N"] if "Normal" in tipo_diagrama else (esf["Vz"] if "Cortante" in tipo_diagrama else esf["My"]))
            nx, ny, nz = (1, 0, 0) if abs(dz)/L > 0.95 else (0, 0, 1)
            ox1, oy1, oz1 = x1 + nx*v1*escala, y1 + ny*v1*escala, z1 + nz*v1*escala
            ox2, oy2, oz2 = x2 + nx*v2*escala, y2 + ny*v2*escala, z2 + nz*v2*escala
            
            fig.add_trace(go.Scatter3d(x=[x1, ox1, ox2, x2], y=[y1, oy1, oy2, y2], z=[z1, oz1, oz2, z2], mode='lines', line=dict(color=cor, width=3), showlegend=False))

    fig.update_layout(scene=dict(xaxis_title='X (m)', yaxis_title='Y (m)', zaxis_title='Z (m)', aspectmode='data'), margin=dict(l=0, r=0, b=0, t=0), height=600)
    return fig

def gerar_relatorio_txt(dados, res_analise, resultados_comp, tudo_aprovado):
    data_atual = datetime.now().strftime("%d/%m/%Y às %H:%M")
    status_global = "APROVADA" if tudo_aprovado else "REPROVADA (Requer revisão de perfis)"
    
    aco = PROPRIEDADES_ACO[dados['tipo_aco']]
    fy_mpa = aco['fy']
    fy_kncm2 = fy_mpa / 10.0
    gamma_a1 = 1.10
    
    relatorio = f"""=========================================================
      MEMÓRIA DE CÁLCULO ESTRUTURAL DETALHADA
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

3. ESFORÇOS SOLICITANTES MÁXIMOS GLOBAIS
---------------------------------------------------------
- Esforço Normal Máximo (N_sd): {res_analise.get('n_max_kn', 0.0):.2f} kN
- Esforço Cortante Máximo (V_sd): {res_analise.get('v_max_kn', 0.0):.2f} kN
- Momento Fletor Máximo (M_sd): {res_analise.get('m_max_knm', 0.0):.2f} kNm
- Deslocamento Máximo (Flecha ELS): {res_analise.get('desloc_max_mm', 0.0):.2f} mm

4. TABELA DE ESFORÇOS EXTREMOS (LEGENDAS DOS DIAGRAMAS)
---------------------------------------------------------
"""
    for grp, esf in res_analise.get('esforcos_grupos', {}).items():
        if esf["n_pos"] == -1e9: continue
        relatorio += f"[{grp.upper()}]\n"
        relatorio += f"  Normal (N)   -> Máx (Tração): {esf['n_pos']:.2f} kN | Mín (Comp): {esf['n_neg']:.2f} kN\n"
        relatorio += f"  Cortante (V) -> Máx: {esf['v_pos']:.2f} kN | Mín: {esf['v_neg']:.2f} kN\n"
        relatorio += f"  Momento (M)  -> Máx (+): {esf['m_pos']:.2f} kNm | Mín (-): {esf['m_neg']:.2f} kNm\n"
        relatorio += f"  Flecha Máx   -> {esf['d_max']:.2f} mm\n\n"

    relatorio += f"""
5. VERIFICAÇÃO DETALHADA POR COMPONENTE (NBR 8800)
---------------------------------------------------------
Propriedades do Material: {dados['tipo_aco']} (fy = {fy_mpa} MPa = {fy_kncm2:.1f} kN/cm²)
Coeficiente de Minoração (γ_a1) = {gamma_a1}

"""
    for v in resultados_comp:
        perf = CATALOGO_COMPLETO[v['perfil']]
        A = perf['A']
        Wx = perf['Wx']
        d = perf['d'] / 10.0
        tw = perf['tw'] / 10.0
        Av = d * tw
        status_comp = "APROVADO" if v['aprovado'] else "REPROVADO"

        relatorio += f"[{v['componente'].upper()}]\n  Perfil Selecionado: {v['perfil']} ({v['familia']})\n"
        relatorio += f"  A. ESFORÇOS ATUANTES MÁXIMOS EM MÓDULO ABSOLUTO (Sd)\n     N_Sd = {v['N_sd']:.2f} kN | V_Sd = {v['V_sd']:.2f} kN | M_Sd = {v['M_sd']:.2f} kNm\n\n"
        relatorio += f"  B. PROPRIEDADES GEOMÉTRICAS DA SEÇÃO\n"
        relatorio += f"     Área Bruta (A) = {A:.2f} cm²\n"
        relatorio += f"     Módulo Resistente Elástico (Wx) = {Wx:.2f} cm³\n"
        relatorio += f"     Altura (d) = {d:.2f} cm | Espessura da Alma (tw) = {tw:.2f} cm\n\n"
        relatorio += f"  C. VERIFICAÇÕES DE RESISTÊNCIA E FLECHA\n"
        relatorio += f"     Tração/Compressão (N_Rd = {v['N_rd']:.2f} kN): {v['N_sd']:.2f} / {v['N_rd']:.2f} = {v['ratio_N']:.1f}%\n"
        relatorio += f"     Cisalhamento (V_Rd = {v['V_rd']:.2f} kN): {v['V_sd']:.2f} / {v['V_rd']:.2f} = {v['ratio_V']:.1f}%\n"
        relatorio += f"     Momento Fletor (M_Rd = {v['M_rd']:.2f} kNm): {v['M_sd']:.2f} / {v['M_rd']:.2f} = {v['ratio_M']:.1f}%\n"
        relatorio += f"     Flecha (δ_lim = {v['delta_lim_mm']:.1f} mm): {v['D_sd']:.2f} / {v['delta_lim_mm']:.1f} = {v['ratio_delta']:.1f}%\n\n"
        relatorio += f"  >> STATUS DA PEÇA: {status_comp} (Taxa Máxima: {v['taxa_maxima']:.1f}%)\n.........................................................\n\n"
    return relatorio

def gerar_relatorio_pdf(texto_memoria, res_analise=None):
    if FPDF is None: return None
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Courier", size=9) 
    for linha in texto_memoria.split('\n'):
        pdf.multi_cell(0, 5, txt=linha.encode('latin-1', 'replace').decode('latin-1'))
        
    if res_analise:
        try:
            pdf.add_page()
            pdf.set_font("Courier", 'B', 12)
            pdf.cell(0, 10, "6. ANEXO - DIAGRAMAS 3D", ln=True)
            pdf.set_font("Courier", size=9)
            
            diagramas = ["Deslocamentos (Deformada)", "Momento Fletor (My)", "Reações de Apoio"]
            
            for diag in diagramas:
                fig = desenhar_diagrama(res_analise, diag)
                fig.update_layout(paper_bgcolor='white', plot_bgcolor='white')
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                    fig.write_image(tmp.name, width=800, height=600)
                    pdf.cell(0, 10, f"-> {diag}:", ln=True)
                    pdf.image(tmp.name, x=10, w=190)
                    pdf.ln(5)
                    tmp_path = tmp.name
                
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
        except Exception as e:
            pdf.multi_cell(0, 5, txt=f"\n[Aviso: Não foi possível gerar os diagramas no PDF. Verifique a instalação do 'kaleido'. Detalhe: {e}]")

    out = pdf.output(dest='S')
    return out.encode('latin-1') if isinstance(out, str) else bytes(out)

def obter_propriedades(nome_perfil):
    p = CATALOGO_COMPLETO[nome_perfil]
    return {
        "A": p["A"] * 1e-4,          
        "Iy": p["Ix"] * 1e-8, 
        "Iz": p["Iy"] * 1e-8,  
        "J": (p["Iy"] * 1e-8) / 2.0  
    }

def main():
    st.title("🏗️ Dimensionamento de Estruturas Metálicas 3D")
    st.caption("Conformidade: NBR 8800 | NBR 6120 | NBR 6123")

    if "res_analise" not in st.session_state:
        st.session_state.res_analise = None

    st.sidebar.title("Configurações Gerais")
    sistema_principal = st.sidebar.selectbox("Sistema Principal", ["Pórtico Alma Cheia", "Tesoura Plana (Treliçada)", "Arco", "Mezanino / Passarela Metálica"])
    tipo_pilar = st.sidebar.selectbox("Tipo de Pilar/Suporte", ["Pilar Metálico", "Pilar de Concreto Armado", "Sem Pilar"])
    
    distribuicao_pilares = "Em todos os pórticos"
    if tipo_pilar != "Sem Pilar":
        distribuicao_pilares = st.sidebar.selectbox("Distribuição de Pilares", ["Em todos os pórticos", "Apenas nos 4 cantos extremos"])

    n_paineis = 6
    espacamento_vigota = 1.0
    forma_cobertura = "2 Águas"
    inclinacao = 10.0
    flecha_arco = 3.0

    if sistema_principal == "Mezanino / Passarela Metálica":
        st.sidebar.markdown("**📐 Parâmetros do Piso/Passarela**")
        espacamento_vigota = st.sidebar.number_input("Espaçamento Vigotas Transversais [m]", min_value=0.40, max_value=3.00, value=1.00, step=0.10)
    elif sistema_principal != "Arco":
        forma_cobertura = st.sidebar.selectbox("Forma da Cobertura", ["2 Águas", "1 Água"])
        inclinacao = st.sidebar.number_input("Inclinação do Telhado [%]", min_value=1.0, max_value=100.0, value=10.0, step=1.0)
        if sistema_principal == "Tesoura Plana (Treliçada)":
            n_paineis = st.sidebar.slider("Número de Painéis da Treliça", min_value=2, max_value=60, value=6, step=2)
    else:
        flecha_arco = st.sidebar.number_input("Flecha do Arco (m)", min_value=1.0, max_value=20.0, value=3.0, step=0.5)

    vao_x = st.sidebar.number_input("Vão Transversal (X) [m]", value=15.0 if sistema_principal != "Mezanino / Passarela Metálica" else 6.0)
    comp_y = st.sidebar.number_input("Comprimento Longitudinal (Y) [m]", value=30.0 if sistema_principal != "Mezanino / Passarela Metálica" else 12.0)
    altura_z = st.sidebar.number_input("Pé-direito / Altura (Z) [m]", value=6.0 if sistema_principal != "Mezanino / Passarela Metálica" else 3.0)
    espacamento = st.sidebar.number_input("Espaçamento entre Pórticos [m]", value=5.0 if sistema_principal != "Mezanino / Passarela Metálica" else 3.0)

    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Perfis Estruturais")
    tipo_aco = st.sidebar.selectbox("Aço Estrutural", list(PROPRIEDADES_ACO.keys()))
    
    lista_perfis = list(CATALOGO_COMPLETO.keys())
    lista_chapa = list(CATALOGO_CHAPA_DOBRADA.keys())

    if sistema_principal == "Mezanino / Passarela Metálica":
        perf_pil = st.sidebar.selectbox("Pilares", lista_perfis, index=lista_perfis.index("W 200 x 22.5")) if tipo_pilar == "Pilar Metálico" else None
        perf_v_prin = st.sidebar.selectbox("Vigas Principais (Longitudinais)", lista_perfis, index=lista_perfis.index("W 360 x 122 (Remontado)"))
        perf_v_sec = st.sidebar.selectbox("Vigas Secundárias (Transversais)", lista_perfis, index=lista_perfis.index("W 150 x 18.0"))
        mapa_perfis = {"Pilares Metálicos": perf_pil, "Vigas Principais (Longitudinais)": perf_v_prin, "Vigas Secundárias (Transversais)": perf_v_sec}
    else:
        perf_pil = st.sidebar.selectbox("Pilares", lista_perfis, index=lista_perfis.index("W 250 x 25.3")) if tipo_pilar == "Pilar Metálico" else None
        perf_terca = st.sidebar.selectbox("Terças de Cobertura", lista_chapa, index=lista_chapa.index("U 100 x 40 x 2.25"))
        perf_bz_sup = st.sidebar.selectbox("Banzo Superior", lista_perfis, index=lista_perfis.index("U 150 x 50 x 3.00"))
        perf_bz_inf = st.sidebar.selectbox("Banzo Inferior", lista_perfis, index=lista_perfis.index("U 150 x 50 x 3.00"))
        perf_diag = st.sidebar.selectbox("Diagonais", lista_perfis, index=lista_perfis.index('2x L 2" x 3/16" (Dupla)'))
        perf_mont = st.sidebar.selectbox("Montantes", lista_perfis, index=lista_perfis.index("UE 100 x 50 x 17 x 2.25"))
        mapa_perfis = {"Pilares Metálicos": perf_pil, "Terças de Cobertura": perf_terca, "Banzo Superior": perf_bz_sup, "Banzo Inferior": perf_bz_inf, "Diagonais": perf_diag, "Montantes": perf_mont}

    st.sidebar.markdown("---")
    apoios_base = st.sidebar.selectbox("Vínculos na Base / Apoios", ["Engastado (Trava Translações e Rotações)", "Articulado (Trava apenas Translações)"])
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🌪️ Cargas / Vento")
    if sistema_principal == "Mezanino / Passarela Metálica":
        tipo_piso = st.sidebar.selectbox("Tipo de Piso", ["Painel Wall / Masterboard (0.30 kN/m²)", "Steel Deck + Concreto (2.00 kN/m²)", "Chapa Xadrez Metálica (0.40 kN/m²)", "Painel OSB / Madeira (0.25 kN/m²)"])
        sobrecarga_opcao = st.sidebar.selectbox(
            "Uso / Sobrecarga", 
            [
                "Escritórios / Leve (2.50 kN/m²)", "Residencial (1.50 kN/m²)", "Comercial / Lojas (3.00 kN/m²)", 
                "Depósito Leve (4.00 kN/m²)", "Depósito Pesado (5.00 kN/m²)", "Passarela - Manutenção/Sem Público (3.00 kN/m²)", 
                "Passarela - Acesso Público (5.00 kN/m²)", "Academias / Ginástica (5.00 kN/m²)" 
            ]
        )
        peso_piso = float(tipo_piso.split("(")[1].split(" ")[0])
        carga_inst = 0.15
        g_total = peso_piso + carga_inst
        q_sobre = float(sobrecarga_opcao.split("(")[1].split(" ")[0])
        q_vento_liquido = 0.0
        q_elu = (1.25 * g_total) + (1.50 * q_sobre)
    else:
        tipo_telha = st.sidebar.selectbox("Tipo de Cobertura", ["Trapezoidal (0.05 kN/m²)", "Termoacústica (0.15 kN/m²)", "Fibrocimento (0.18 kN/m²)"])
        carga_inst = st.sidebar.number_input("Carga Instalações [kN/m²]", min_value=0.0, value=0.10, step=0.02)
        q_sobre = st.sidebar.number_input("Sobrecarga [kN/m²]", min_value=0.0, value=0.25, step=0.05)
        v0 = st.sidebar.number_input("Velocidade V0 [m/s]", min_value=30.0, max_value=60.0, value=40.0, step=1.0)
        cpe = st.sidebar.number_input("Coef. Pressão Externa (Cpe)", min_value=-2.0, max_value=2.0, value=-0.80, step=0.10)
        cpi = st.sidebar.number_input("Coef. Pressão Interna (Cpi)", min_value=-1.0, max_value=1.0, value=0.20, step=0.10)
        
        peso_telha = float(tipo_telha.split("(")[1].split(" ")[0])
        g_total = peso_telha + carga_inst 
        q_vento_liquido = (0.613 * (v0 ** 2) / 1000) * (cpe - cpi) * 1.20
        q_elu = (1.25 * g_total) + (1.50 * q_sobre) + (1.40 * abs(q_vento_liquido))

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📐 Geometria", "🌪️ Cargas", "⚙️ Análise", "✅ Verificação", "📊 Diagramas", "📦 BIM"])

    # GERADOR DE MALHA 
    y_coords = np.arange(0, comp_y + espacamento, espacamento)
    if y_coords[-1] != comp_y: y_coords[-1] = comp_y
    all_x, all_y, all_z, edges_raw = [], [], [], []
    has_pillar = (tipo_pilar != "Sem Pilar")
    
    dict_nos = {}
    def add_no(x, y, z):
        pt = (round(x, 3), round(y, 3), round(z, 3))
        if pt not in dict_nos:
            dict_nos[pt] = len(dict_nos)
            all_x.append(pt[0]); all_y.append(pt[1]); all_z.append(pt[2])
        return dict_nos[pt]

    apoios_idx = set()

    if sistema_principal == "Mezanino / Passarela Metálica":
        y_vigotas = np.arange(0, comp_y + espacamento_vigota, espacamento_vigota)
        if y_vigotas[-1] != comp_y: y_vigotas[-1] = comp_y
        
        for y_v in y_vigotas:
            edges_raw.append({"n1": add_no(0, y_v, altura_z), "n2": add_no(vao_x, y_v, altura_z), "grupo": "Vigas Secundárias (Transversais)"})
        for i in range(len(y_vigotas) - 1):
            edges_raw.append({"n1": add_no(0, y_vigotas[i], altura_z), "n2": add_no(0, y_vigotas[i+1], altura_z), "grupo": "Vigas Principais (Longitudinais)"})
            edges_raw.append({"n1": add_no(vao_x, y_vigotas[i], altura_z), "n2": add_no(vao_x, y_vigotas[i+1], altura_z), "grupo": "Vigas Principais (Longitudinais)"})
        
        for i_y, y_p in enumerate(y_coords):
            is_supported_frame = (distribuicao_pilares == "Em todos os pórticos" or i_y == 0 or i_y == (len(y_coords) - 1))
            if is_supported_frame:
                n_tE = add_no(0, y_p, altura_z)
                n_tD = add_no(vao_x, y_p, altura_z)
                if has_pillar:
                    n_bE = add_no(0, y_p, 0)
                    n_bD = add_no(vao_x, y_p, 0)
                    grp_pilar = "Pilares Metálicos" if tipo_pilar == "Pilar Metálico" else "Pilares Concreto"
                    edges_raw.append({"n1": n_bE, "n2": n_tE, "grupo": grp_pilar})
                    edges_raw.append({"n1": n_bD, "n2": n_tD, "grupo": grp_pilar})
                    apoios_idx.update([n_bE, n_bD])
                else:
                    apoios_idx.update([n_tE, n_tD])

    else:
        cobertura_por_frame = []
        for i_y, y in enumerate(y_coords):
            is_supported_frame = (distribuicao_pilares == "Em todos os pórticos" or i_y == 0 or i_y == (len(y_coords) - 1))
            
            if sistema_principal == "Arco":
                x_arco = list(np.linspace(0, vao_x, 9))
                z_arco = [altura_z + flecha_arco * (1 - (2*(x-vao_x/2)/vao_x)**2) for x in x_arco]
                n_arco_ids = [add_no(x, y, z) for x, z in zip(x_arco, z_arco)]
                
                for i in range(8):
                    edges_raw.append({"n1": n_arco_ids[i], "n2": n_arco_ids[i+1], "grupo": "Banzo Superior"})
                
                if is_supported_frame:
                    n_tE, n_tD = n_arco_ids[0], n_arco_ids[-1]
                    if has_pillar:
                        n_bE, n_bD = add_no(0, y, 0), add_no(vao_x, y, 0)
                        grp_pilar = "Pilares Metálicos" if tipo_pilar == "Pilar Metálico" else "Pilares Concreto"
                        edges_raw.append({"n1": n_bE, "n2": n_tE, "grupo": grp_pilar})
                        edges_raw.append({"n1": n_bD, "n2": n_tD, "grupo": grp_pilar})
                        apoios_idx.update([n_bE, n_bD])
                    else:
                        apoios_idx.update([n_tE, n_tD])
                cobertura_por_frame.append(n_arco_ids)

            elif sistema_principal == "Tesoura Plana (Treliçada)":
                if forma_cobertura == "1 Água":
                    x_sub = np.linspace(0, vao_x, n_paineis + 1)
                    x_pts = list(x_sub) + list(x_sub)
                    z_pts = [altura_z] * (n_paineis + 1) + list(altura_z + (vao_x - x_sub) * (inclinacao / 100.0))
                else:
                    n_lado = n_paineis // 2
                    x_all = np.concatenate([np.linspace(0, vao_x/2, n_lado + 1), np.linspace(vao_x/2, vao_x, n_lado + 1)[1:]])
                    z_sup_local = np.where(x_all <= vao_x/2, altura_z + x_all*(inclinacao/100.0), altura_z + (vao_x-x_all)*(inclinacao/100.0))
                    x_pts = list(x_all) + list(x_all)
                    z_pts = [altura_z] * len(x_all) + list(z_sup_local)
                
                n_trel_ids = [add_no(x, y, z) for x, z in zip(x_pts, z_pts)]
                meio = len(n_trel_ids) // 2
                idx_inf = n_trel_ids[:meio]
                idx_sup = n_trel_ids[meio:]
                
                for i in range(len(idx_inf)-1):
                    edges_raw.append({"n1": idx_inf[i], "n2": idx_inf[i+1], "grupo": "Banzo Inferior"})
                    edges_raw.append({"n1": idx_sup[i], "n2": idx_sup[i+1], "grupo": "Banzo Superior"})
                    edges_raw.append({"n1": idx_inf[i], "n2": idx_sup[i], "grupo": "Montantes"})
                    if forma_cobertura == "1 Água" or i < (len(idx_inf)-1)//2:
                        edges_raw.append({"n1": idx_inf[i], "n2": idx_sup[i+1], "grupo": "Diagonais"})
                    else:
                        edges_raw.append({"n1": idx_inf[i+1], "n2": idx_sup[i], "grupo": "Diagonais"})
                edges_raw.append({"n1": idx_inf[-1], "n2": idx_sup[-1], "grupo": "Montantes"})
                
                if is_supported_frame:
                    n_tE, n_tD = idx_inf[0], idx_inf[-1]
                    if has_pillar:
                        n_bE, n_bD = add_no(0, y, 0), add_no(vao_x, y, 0)
                        grp_pilar = "Pilares Metálicos" if tipo_pilar == "Pilar Metálico" else "Pilares Concreto"
                        edges_raw.append({"n1": n_bE, "n2": n_tE, "grupo": grp_pilar})
                        edges_raw.append({"n1": n_bD, "n2": n_tD, "grupo": grp_pilar})
                        apoios_idx.update([n_bE, n_bD])
                    else:
                        apoios_idx.update([n_tE, n_tD])
                cobertura_por_frame.append(idx_sup)

            else: 
                n_tE = add_no(0, y, altura_z)
                n_tD = add_no(vao_x, y, altura_z)
                
                if forma_cobertura == "2 Águas":
                    h_cum = altura_z + (vao_x / 2.0) * (inclinacao / 100.0)
                    n_cum = add_no(vao_x/2, y, h_cum)
                    edges_raw.append({"n1": n_tE, "n2": n_cum, "grupo": "Banzo Superior"})
                    edges_raw.append({"n1": n_cum, "n2": n_tD, "grupo": "Banzo Superior"})
                    cobertura_por_frame.append([n_tE, n_cum, n_tD])
                else:
                    h_cum = altura_z + vao_x * (inclinacao / 100.0)
                    n_cum = add_no(vao_x, y, h_cum)
                    edges_raw.append({"n1": n_tE, "n2": n_cum, "grupo": "Banzo Superior"})
                    cobertura_por_frame.append([n_tE, n_cum])

                edges_raw.append({"n1": n_tE, "n2": n_tD, "grupo": "Banzo Inferior"})
                
                if is_supported_frame:
                    if has_pillar:
                        n_bE, n_bD = add_no(0, y, 0), add_no(vao_x, y, 0)
                        grp_pilar = "Pilares Metálicos" if tipo_pilar == "Pilar Metálico" else "Pilares Concreto"
                        edges_raw.append({"n1": n_bE, "n2": n_tE, "grupo": grp_pilar})
                        edges_raw.append({"n1": n_bD, "n2": n_tD, "grupo": grp_pilar})
                        apoios_idx.update([n_bE, n_bD])
                    else:
                        apoios_idx.update([n_tE, n_tD])
            
        for i in range(len(cobertura_por_frame) - 1):
            for p in range(len(cobertura_por_frame[i])):
                if p < len(cobertura_por_frame[i+1]):
                    edges_raw.append({"n1": cobertura_por_frame[i][p], "n2": cobertura_por_frame[i+1][p], "grupo": "Terças de Cobertura"})

    barras_prontas = []
    barras_visualizacao = []
    
    for edge in edges_raw:
        grp = edge["grupo"]
        barras_visualizacao.append({"n1": edge["n1"], "n2": edge["n2"], "grupo": grp})
        
        if grp == "Pilares Concreto":
            barras_prontas.append({"n1": edge["n1"], "n2": edge["n2"], "grupo": grp, "A": 0.16, "Iy": 0.002, "Iz": 0.002, "J": 0.002})
            continue

        nome_perf = mapa_perfis.get(grp)
        if nome_perf is None: continue 
        
        props = obter_propriedades(nome_perf)
        barras_prontas.append({"n1": edge["n1"], "n2": edge["n2"], "grupo": grp, "A": props["A"], "Iy": props["Iy"], "Iz": props["Iz"], "J": props["J"]})

    with tab1:
        fig = go.Figure()
        for b in barras_visualizacao:
            x1, y1, z1 = all_x[b["n1"]], all_y[b["n1"]], all_z[b["n1"]]
            x2, y2, z2 = all_x[b["n2"]], all_y[b["n2"]], all_z[b["n2"]]
            
            line_color = 'gray' if b["grupo"] == "Pilares Concreto" else 'blue'
            line_width = 8 if b["grupo"] == "Pilares Concreto" else 4
            fig.add_trace(go.Scatter3d(x=[x1, x2], y=[y1, y2], z=[z1, z2], mode='lines', line=dict(color=line_color, width=line_width), showlegend=False))
            
        fig.update_layout(scene=dict(xaxis_title='X (m)', yaxis_title='Y (m)', zaxis_title='Z (m)', aspectmode='data'), margin=dict(l=0, r=0, b=0, t=0), height=550)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("🌪️ Detalhamento de Cargas (ELU)")
        st.info(f"**Carga de Projeto Total (q_ELU):** {q_elu:.2f} kN/m²")

    with tab3:
        st.subheader("⚙️ Análise Estrutural Matricial 3D")
        if st.button("🚀 Executar Análise com Matriz Específica", type="primary"):
            with st.spinner("Montando matriz global de rigidez ponderada..."):
                motor = MotorCalculo3D()
                motor.construir_malha(all_x, all_y, all_z, barras_prontas, list(apoios_idx), apoios_base)
                espacamento_calc = espacamento_vigota if sistema_principal == "Mezanino / Passarela Metálica" else espacamento
                motor.aplicar_carga_distribuida(q_elu, vao_x, espacamento_calc)
                st.session_state.res_analise = motor.resolver()

        if st.session_state.res_analise:
            if st.session_state.res_analise.get("sucesso"):
                st.success("✅ Análise Concluída com sucesso!")
            else:
                st.error(f"❌ Erro na análise: {st.session_state.res_analise.get('erro')}")

    with tab4:
        st.subheader("✅ Verificação Exata (NBR 8800)")
        if not st.session_state.res_analise: 
            st.warning("Execute a Análise na Aba 3.")
        elif not st.session_state.res_analise.get("sucesso"):
             st.error("A análise falhou. Não é possível realizar a verificação.")
        else:
            res = st.session_state.res_analise
            verificador = VerificadorNBR8800(tipo_aco)
            
            resultados_comp = []
            tudo_aprovado = True

            for grupo, esf_grp in res.get("esforcos_grupos", {}).items():
                nome_perfil = mapa_perfis.get(grupo)
                if nome_perfil is None: continue 
                
                v = verificador.verificar_elemento(
                    nome_perfil, 
                    esf_grp["n_max"], esf_grp["v_max"], esf_grp["m_max"], esf_grp["d_max"], 
                    vao_x, 1.0 
                )
                v["componente"] = grupo
                v["N_sd"] = esf_grp["n_max"]
                v["V_sd"] = esf_grp["v_max"]
                v["M_sd"] = esf_grp["m_max"]
                v["D_sd"] = esf_grp["d_max"]
                v["fator"] = 1.0
                
                resultados_comp.append(v)
                if not v["aprovado"]: tudo_aprovado = False

            if tudo_aprovado: st.success("### 🎉 TODOS OS PERFIS FORAM APROVADOS!")
            elif len(resultados_comp) > 0: st.error("### ❌ HÁ PERFIS REPROVADOS!")
            
            if len(resultados_comp) > 0:
                st.markdown("---")
                dados_r = {
                    "sistema_principal": sistema_principal, "tipo_pilar": tipo_pilar, 
                    "distribuicao_pilares": distribuicao_pilares, "vao_x": vao_x, "comp_y": comp_y, 
                    "altura_z": altura_z, "espacamento": espacamento, "espacamento_vigota": espacamento_vigota,
                    "g_total": g_total, "q_sobre": q_sobre, "q_elu": q_elu, "tipo_aco": tipo_aco, 
                    "q_vento_liquido": q_vento_liquido, "tipo_piso": tipo_piso if sistema_principal == "Mezanino / Passarela Metálica" else "N/A"
                }
                texto_memoria = gerar_relatorio_txt(dados_r, res, resultados_comp, tudo_aprovado)
                
                col_d1, col_d2 = st.columns(2)
                with col_d1: st.download_button("📄 Baixar TXT", data=texto_memoria, file_name="Calculo.txt", use_container_width=True)
                with col_d2:
                    if FPDF is not None:
                        # Quando o botão é clicado, tenta embutir os diagramas
                        st.download_button("📥 Baixar PDF com Anexos 3D", data=gerar_relatorio_pdf(texto_memoria, res), file_name="Calculo_Detalhado.pdf", mime="application/pdf", type="primary", use_container_width=True)

                st.markdown("---")
                for v in resultados_comp:
                    st.write(f"#### 🔹 {v['componente']} — `{v['perfil']}`")
                    c1, c2, c3, c4, c5 = st.columns(5)
                    c1.metric("Status", "✅ Ok" if v['aprovado'] else "❌ Reprovado")
                    c2.metric("Taxa", f"{v['taxa_maxima']:.1f}%")
                    c3.metric("Momento (Msd/Mrd)", f"{v['ratio_M']:.1f}%")
                    c4.metric("Normal (Nsd/Nrd)", f"{v['ratio_N']:.1f}%")
                    c5.metric("Flecha", f"{v['ratio_delta']:.1f}%")
                    st.progress(min(max(int(v['taxa_maxima']), 0), 100))
                    st.markdown("---")

    with tab5:
        if st.session_state.res_analise and st.session_state.res_analise.get("sucesso"):
            tipo_diagrama = st.selectbox("Visualizar:", ["Deslocamentos (Deformada)", "Esforço Normal (Tração/Compressão)", "Esforço Cortante (Vz)", "Momento Fletor (My)", "Reações de Apoio"])
            st.plotly_chart(desenhar_diagrama(st.session_state.res_analise, tipo_diagrama), use_container_width=True)

if __name__ == "__main__":
    main()
