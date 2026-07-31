from PyNite import FEModel3D

class MotorCalculo3D:
    def __init__(self):
        """Inicializa o modelo 3D de Elementos Finitos"""
        self.modelo = FEModel3D()
        self.configurar_material_base()

    def configurar_material_base(self):
        """Configura um aço estrutural padrão (unidades em kN e m)"""
        E = 200e6     # Módulo de Elasticidade (200 GPa = 200.000.000 kN/m²)
        G = 77e6      # Módulo de Cisalhamento (77 GPa)
        nu = 0.3      # Coeficiente de Poisson
        rho = 78.5    # Peso específico (kN/m³)
        
        self.modelo.add_material('Aco', E, G, nu, rho)
        
        # Cria uma seção transversal genérica temporária (até colocarmos o catálogo)
        # Área, Iz, Iy, J (em metros)
        self.modelo.add_section('Secao_Generica', 0.005, 0.0001, 0.0001, 0.00005)

    def construir_malha(self, nos_x, nos_y, nos_z, barras):
        """
        Constrói a malha de elementos finitos recebendo as coordenadas do Streamlit.
        """
        # Adiciona os Nós
        for i in range(len(nos_x)):
            nome_no = f"N{i}"
            self.modelo.add_node(nome_no, nos_x[i], nos_y[i], nos_z[i])
            
            # Condição de contorno: Se Z == 0, é a base do pilar (Engaste)
            if nos_z[i] == 0:
                self.modelo.def_support(nome_no, True, True, True, True, True, True)

        # Adiciona as Barras (Elementos)
        for i, (no_inicio, no_fim) in enumerate(barras):
            nome_barra = f"B{i}"
            self.modelo.add_member(nome_barra, f"N{no_inicio}", f"N{no_fim}", 'Aco', 'Secao_Generica')

    def aplicar_carga_distribuida(self, q_kNm2, vao_x, espacamento):
        """
        Aplica a carga nas vigas. 
        Por simplificação inicial, aplica carga gravitacional nos elementos de topo.
        """
        # Carga linear tributária em kN/m (Carga por m² * Largura de influência)
        q_linear = q_kNm2 * espacamento
        
        for nome_barra, barra in self.modelo.Members.items():
            z_medio = (barra.i_node.Z + barra.j_node.Z) / 2
            
            # Se for uma barra de cobertura (Z > 0), aplica a carga distribuída em -Z
            if z_medio > 0.1:
                self.modelo.add_member_dist_load(nome_barra, Direction='FZ', w1=-q_linear, w2=-q_linear)

    def resolver(self):
        """Executa a análise matricial e retorna sucesso ou falha"""
        try:
            self.modelo.analyze(check_stability=True)
            return True
        except Exception as e:
            return str(e)
