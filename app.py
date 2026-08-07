import streamlit as st
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
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
        fig.add_trace(go.Scatter3d(x=rx, y=ry, z=rz, mode='markers+text', marker=dict(size=8, color='purple', symbol='diamond'), text=texts, textposition="top center", textfont=dict(size=11, color='purple'), showlegend=False))
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
    fy_kncm2 = aco['fy'] / 10.0
    
    relatorio = f"=========================================================\n"
    relatorio += f"      MEMÓRIA DE CÁLCULO ESTRUTURAL DETALHADA\n"
    relatorio += f"=========================================================\n"
    relatorio += f"Data: {data_atual} | Status: {status_global}\n\n"

    for v in resultados_comp:
        perf = CATALOGO_COMPLETO[v['perfil']]
        status_comp = "APROVADO" if v['aprovado'] else "REPROVADO"

        relatorio += f"[{v['componente'].upper()}]\n"
        relatorio += f"  Perfil Selecionado: {v['perfil']}\n"
        relatorio += f"  A. ESFORÇOS SOLICITANTES (Sd)\n"
        relatorio += f"     N_Sd = {v['N_sd']:.2f} kN | V_Sd = {v['V_sd']:.2f} kN | M_Sd = {v['M_sd']:.2f} kNm\n\n"
        relatorio += f"  B. RESISTÊNCIAS DE PROJETO (Rd)\n"
        relatorio += f"     N_Rd = {v['N_rd']:.2f} kN (Taxa: {v['ratio_N']:.1f}%)\n"
        relatorio += f"     V_Rd = {v['V_rd']:.2f} kN (Taxa: {v['ratio_V']:.1f}%)\n"
        relatorio += f"     M_Rd = {v['M_rd']:.2f} kNm (Taxa: {v['ratio_M']:.1f}%)\n\n"
        relatorio += f"  C. VERIFICAÇÃO DE FLECHA (ELS)\n"
        relatorio += f"     δ_limite = {v['delta_lim_mm']:.1f} mm | δ_real = {v['D_sd']:.1f} mm (Taxa: {v['ratio_delta']:.1f}%)\n\n"
        relatorio += f"  >> STATUS DA PEÇA: {status_comp} (Taxa Máxima: {v['taxa_maxima']:.1f}%)\n"
        relatorio += ".........................................................\n\n"
    return relatorio

def gerar_relatorio_pdf(texto_memoria):
    if FPDF is None: return None
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Courier", size=9) 
    for linha in texto_memoria.split('\n'):
        pdf.multi_cell(0, 5, txt=linha.encode('latin-1', 'replace').decode('latin-1'))
    out = pdf.output(dest='S')
    return out.encode('latin-1') if isinstance(out, str) else bytes(out)

def obter_propriedades(nome_perfil):
    p = CATALOGO_COMPLETO[nome_perfil]
    return {
        "A": p["A"] * 1e-4,          # cm2 -> m2
        "Iy": p["Iy"] * 1e-8,        # Inércia eixo menor -> m4
        "Iz": p["Ix"] * 1e-8,        # Inércia eixo maior (Ix no catálogo) -> m4
        "J": (p["Iy"] * 1e-8) / 2.0  # Simplificação de torção p/ estabilidade
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

    n_paineis, espacamento_vigota, forma_cobertura = 6, 1.0, "2 Águas"
    if sistema_principal == "Mezanino / Passarela Metálica":
        espacamento_vigota = st.sidebar.number_input("Espaçamento Vigotas Transversais [m]", min_value=0.40, max_value=3.00, value=1.00, step=0.10)
    elif sistema_principal != "Arco":
        forma_cobertura = st.sidebar.selectbox("Forma da Cobertura", ["2 Águas", "1 Água"])
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
        
        mapa_perfis = {
            "Pilares Metálicos": perf_pil,
            "Vigas Principais (Longitudinais)": perf_v_prin,
            "Vigas Secundárias (Transversais)": perf_v_sec
        }
    else:
        perf_pil = st.sidebar.selectbox("Pilares", lista_perfis, index=lista_perfis.index("W 250 x 25.3")) if tipo_pilar == "Pilar Metálico" else None
        perf_terca = st.sidebar.selectbox("Terças de Cobertura", lista_chapa, index=lista_chapa.index("U 100 x 40 x 2.25"))
        perf_bz_sup = st.sidebar.selectbox("Banzo Superior", lista_perfis, index=lista_perfis.index("U 150 x 50 x 3.00"))
        perf_bz_inf = st.sidebar.selectbox("Banzo Inferior", lista_perfis, index=lista_perfis.index("U 150 x 50 x 3.00"))
        perf_diag = st.sidebar.selectbox("Diagonais", lista_perfis, index=lista_perfis.index('2x L 2" x 3/16" (Dupla)'))
        perf_mont = st.sidebar.selectbox("Montantes", lista_perfis, index=lista_perfis.index("UE 100 x 50 x 17 x 2.25"))

        mapa_perfis = {
            "Pilares Metálicos": perf_pil, "Terças de Cobertura": perf_terca,
            "Banzo Superior": perf_bz_sup, "Banzo Inferior": perf_bz_inf,
            "Diagonais": perf_diag, "Montantes": perf_mont
        }

    st.sidebar.markdown("---")
    apoios_base = st.sidebar.selectbox("Vínculos na Base", ["Engastado (Trava Translações e Rotações)", "Articulado (Trava apenas Translações)"])
    q_elu = 5.0  # Carga simplificada de projeto (ELU genérico para focar no cálculo)

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📐 Geometria", "🌪️ Cargas", "⚙️ Análise", "✅ Verificação", "📊 Diagramas", "📦 BIM"])

    # GERADOR DE MALHA COM ATRIBUIÇÃO DE GRUPO
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

    if sistema_principal == "Mezanino / Passarela Metálica":
        y_vigotas = np.arange(0, comp_y + espacamento_vigota, espacamento_vigota)
        if y_vigotas[-1] != comp_y: y_vigotas[-1] = comp_y
        
        for y_v in y_vigotas:
            edges_raw.append({"n1": add_no(0, y_v, altura_z), "n2": add_no(vao_x, y_v, altura_z), "grupo": "Vigas Secundárias (Transversais)"})
        for i in range(len(y_vigotas) - 1):
            edges_raw.append({"n1": add_no(0, y_vigotas[i], altura_z), "n2": add_no(0, y_vigotas[i+1], altura_z), "grupo": "Vigas Principais (Longitudinais)"})
            edges_raw.append({"n1": add_no(vao_x, y_vigotas[i], altura_z), "n2": add_no(vao_x, y_vigotas[i+1], altura_z), "grupo": "Vigas Principais (Longitudinais)"})
        
        if has_pillar:
            for i_y, y_p in enumerate(y_coords):
                if distribuicao_pilares == "Apenas nos 4 cantos extremos" and i_y != 0 and i_y != (len(y_coords) - 1): continue
                edges_raw.append({"n1": add_no(0, y_p, 0), "n2": add_no(0, y_p, altura_z), "grupo": "Pilares Metálicos"})
                edges_raw.append({"n1": add_no(vao_x, y_p, 0), "n2": add_no(vao_x, y_p, altura_z), "grupo": "Pilares Metálicos"})

    else:
        # Lógica simplificada de pórtico
        for i_y, y in enumerate(y_coords):
            has_pillar_local = has_pillar and (distribuicao_pilares == "Em todos os pórticos" or i_y == 0 or i_y == len(y_coords) - 1)
            h_cum = altura_z + vao_x * (inclinacao / 100.0)
            
            n_bE, n_tE = add_no(0, y, 0), add_no(0, y, altura_z)
            n_bD, n_tD = add_no(vao_x, y, 0), add_no(vao_x, y, altura_z)
            n_cum = add_no(vao_x/2, y, h_cum)

            if has_pillar_local:
                edges_raw.append({"n1": n_bE, "n2": n_tE, "grupo": "Pilares Metálicos"})
                edges_raw.append({"n1": n_bD, "n2": n_tD, "grupo": "Pilares Metálicos"})
                
            edges_raw.append({"n1": n_tE, "n2": n_cum, "grupo": "Banzo Superior"})
            edges_raw.append({"n1": n_cum, "n2": n_tD, "grupo": "Banzo Superior"})
            edges_raw.append({"n1": n_tE, "n2": n_tD, "grupo": "Banzo Inferior"})
            
        # Terças de Cobertura conectando pórticos
        for i in range(len(y_coords) - 1):
            edges_raw.append({"n1": add_no(0, y_coords[i], altura_z), "n2": add_no(0, y_coords[i+1], altura_z), "grupo": "Terças de Cobertura"})
            edges_raw.append({"n1": add_no(vao_x, y_coords[i], altura_z), "n2": add_no(vao_x, y_coords[i+1], altura_z), "grupo": "Terças de Cobertura"})

    # ATRIBUIÇÃO FÍSICA PARA MATRIZ
    barras_prontas = []
    for edge in edges_raw:
        grp = edge["grupo"]
        nome_perf = mapa_perfis.get(grp)
        if nome_perf is None: continue # Ex: Pilares de concreto não entram no solver metálico
        
        props = obter_propriedades(nome_perf)
        barras_prontas.append({
            "n1": edge["n1"], "n2": edge["n2"], "grupo": grp,
            "A": props["A"], "Iy": props["Iy"], "Iz": props["Iz"], "J": props["J"]
        })

    with tab1:
        fig = go.Figure()
        for b in barras_prontas:
            x1, y1, z1 = all_x[b["n1"]], all_y[b["n1"]], all_z[b["n1"]]
            x2, y2, z2 = all_x[b["n2"]], all_y[b["n2"]], all_z[b["n2"]]
            fig.add_trace(go.Scatter3d(x=[x1, x2], y=[y1, y2], z=[z1, z2], mode='lines', line=dict(color='blue', width=4), showlegend=False))
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("⚙️ Análise Estrutural Matricial 3D")
        if st.button("🚀 Executar Análise com Matriz Específica", type="primary"):
            with st.spinner("Montando matriz global de rigidez ponderada..."):
                motor = MotorCalculo3D()
                motor.construir_malha(all_x, all_y, all_z, barras_prontas, apoios_base)
                espacamento_calc = espacamento_vigota if sistema_principal == "Mezanino / Passarela Metálica" else espacamento
                motor.aplicar_carga_distribuida(q_elu, vao_x, espacamento_calc)
                st.session_state.res_analise = motor.resolver()

        if st.session_state.res_analise and st.session_state.res_analise.get("sucesso"):
            st.success("✅ Análise Concluída com sucesso!")

    with tab4:
        st.subheader("✅ Verificação Exata (NBR 8800)")
        if not st.session_state.res_analise: 
            st.warning("Execute a Análise.")
        else:
            res = st.session_state.res_analise
            verificador = VerificadorNBR8800(tipo_aco)
            
            resultados_comp = []
            tudo_aprovado = True

            for grupo, esf_grp in res["esforcos_grupos"].items():
                nome_perfil = mapa_perfis[grupo]
                v = verificador.verificar_elemento(
                    nome_perfil, 
                    esf_grp["n_max"], esf_grp["v_max"], esf_grp["m_max"], esf_grp["d_max"], 
                    vao_x, 1.0 # Fator removido, pois o solver agora isola o esforço real do grupo
                )
                v["componente"] = grupo
                v["N_sd"] = esf_grp["n_max"]
                v["V_sd"] = esf_grp["v_max"]
                v["M_sd"] = esf_grp["m_max"]
                v["D_sd"] = esf_grp["d_max"]
                
                resultados_comp.append(v)
                if not v["aprovado"]: tudo_aprovado = False

            if tudo_aprovado: st.success("### 🎉 TODOS OS PERFIS FORAM APROVADOS!")
            else: st.error("### ❌ HÁ PERFIS REPROVADOS!")
            
            st.markdown("---")
            dados_r = {"sistema_principal": sistema_principal, "tipo_pilar": tipo_pilar, "vao_x": vao_x, "comp_y": comp_y, "altura_z": altura_z, "espacamento": espacamento, "g_total": 0, "q_sobre": 0, "q_elu": q_elu, "tipo_aco": tipo_aco, "q_vento_liquido": 0}
            texto_memoria = gerar_relatorio_txt(dados_r, res, resultados_comp, tudo_aprovado)
            
            col_d1, col_d2 = st.columns(2)
            with col_d1: st.download_button("📄 Baixar TXT", data=texto_memoria, file_name="Calculo.txt")
            with col_d2:
                if FPDF is not None:
                    st.download_button("📥 Baixar PDF", data=gerar_relatorio_pdf(texto_memoria), file_name="Calculo.pdf", mime="application/pdf", type="primary")

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
        if st.session_state.res_analise:
            st.plotly_chart(desenhar_diagrama(st.session_state.res_analise, "Momento Fletor (My)"), use_container_width=True)

if __name__ == "__main__":
    main()
