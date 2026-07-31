import numpy as np
from PyNite import FEModel3D


class MotorCalculo3D:
    def __init__(self):
        """Inicializa o modelo tridimensional de Elementos Finitos."""
        self.modelo = FEModel3D()
        self.configurar_material_base()

    def configurar_material_base(self):
        """Configura propriedade do aço e seção genérica inicial (unidades: kN e m)."""
        E = 200e6      # Módulo de Elasticidade (200 GPa = 200.000.000 kN/m²)
        G = 77e6       # Módulo de Cisalhamento (77 GPa = 77.000.000 kN/m²)
        nu = 0.3       # Coeficiente de Poisson
        rho = 78.5     # Peso específico do aço (kN/m³)
        
        self.modelo.add_material('Aco', E, G, nu, rho)
        self.modelo.add_section('Secao_Generica', 0.005, 0.0001, 0.0001, 0.00005)

    def construir_malha(self, nos_x, nos_y, nos_z, barras, tipo_apoio_base):
        """
        Gera os Nós, aplica as Condições de Contorno da Base e cria os Elementos de Barra.
        """
        for i in range(len(nos_x)):
            nome_no = f"N{i}"
            self.modelo.add_node(nome_no, nos_x[i], nos_y[i], nos_z[i])
            
            if nos_z[i] == 0:
                if "Engastado" in tipo_apoio_base:
                    self.modelo.def_support(nome_no, True, True, True, True, True, True)
                else:
                    self.modelo.def_support(nome_no, True, True, True, False, False, False)

        for i, (no_inicio, no_fim) in enumerate(barras):
            nome_barra = f"B{i}"
            self.modelo.add_member(nome_barra, f"N{no_inicio}", f"N{no_fim}", 'Aco', 'Secao_Generica')

    def aplicar_carga_distribuida(self, q_kNm2, vao_x, espacamento):
        """
        Aplica a carga linear tributária (kN/m) nas barras de cobertura.
        """
        q_linear = q_kNm2 * espacamento
        
        for nome_barra, barra in self.modelo.Members.items():
            z_medio = (barra.i_node.Z + barra.j_node.Z) / 2.0
            if z_medio > 0.1:
                self.modelo.add_member_dist_load(nome_barra, Direction='FZ', w1=-q_linear, w2=-q_linear)

    def resolver(self):
        """
        Executa a análise matricial e extrai o resumo dos esforços solicitantes máximos.
        """
        try:
            self.modelo.analyze(check_stability=True)
            
            resultados = {
                "sucesso": True,
                "num_nos": len(self.modelo.Nodes),
                "num_barras": len(self.modelo.Members),
                "n_max_kn": 0.0,
                "v_max_kn": 0.0,
                "m_max_knm": 0.0,
                "desloc_max_mm": 0.0
            }

            for barra in self.modelo.Members.values():
                try:
                    n_local = max(abs(barra.max_axial()), abs(barra.min_axial()))
                    v_local = max(abs(barra.max_shear('Fy')), abs(barra.min_shear('Fy')),
                                  abs(barra.max_shear('Fz')), abs(barra.min_shear('Fz')))
                    m_local = max(abs(barra.max_moment('My')), abs(barra.min_moment('My')),
                                  abs(barra.max_moment('Mz')), abs(barra.min_moment('Mz')))
                    
                    resultados["n_max_kn"] = max(resultados["n_max_kn"], n_local)
                    resultados["v_max_kn"] = max(resultados["v_max_kn"], v_local)
                    resultados["m_max_knm"] = max(resultados["m_max_knm"], m_local)
                except Exception:
                    pass

            for no in self.modelo.Nodes.values():
                try:
                    dx = getattr(no, 'DX', {}).get('Combo 1', 0.0) or 0.0
                    dy = getattr(no, 'DY', {}).get('Combo 1', 0.0) or 0.0
                    dz = getattr(no, 'DZ', {}).get('Combo 1', 0.0) or 0.0
                    
                    desloc_total_m = np.sqrt(dx**2 + dy**2 + dz**2)
                    desloc_total_mm = desloc_total_m * 1000.0
                    
                    resultados["desloc_max_mm"] = max(resultados["desloc_max_mm"], desloc_total_mm)
                except Exception:
                    pass

            return resultados

        except Exception as e:
            return {
                "sucesso": False,
                "erro": str(e)
            }
