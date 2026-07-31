from PyNite import FEModel3D

class MotorCalculo3D:
    def __init__(self):
        self.modelo = FEModel3D()
        self.configurar_material_base()

    def configurar_material_base(self):
        self.modelo.add_material('Aco', 200e6, 77e6, 0.3, 78.5)
        self.modelo.add_section('Secao_Generica', 0.005, 0.0001, 0.0001, 0.00005)

    def construir_malha(self, nos_x, nos_y, nos_z, barras, tipo_apoio_base):
        """
        Recebe os nós e aplica as condições de contorno de acordo com a escolha do usuário.
        """
        # Adiciona os Nós
        for i in range(len(nos_x)):
            nome_no = f"N{i}"
            self.modelo.add_node(nome_no, nos_x[i], nos_y[i], nos_z[i])
            
            # Condição de contorno na base (Z == 0)
            if nos_z[i] == 0:
                if "Engastado" in tipo_apoio_base:
                    # Trava DX, DY, DZ, RX, RY, RZ
                    self.modelo.def_support(nome_no, True, True, True, True, True, True)
                else:
                    # Articulado: Trava DX, DY, DZ. Libera as rotações RX, RY, RZ.
                    self.modelo.def_support(nome_no, True, True, True, False, False, False)

        # Adiciona as Barras
        for i, (no_inicio, no_fim) in enumerate(barras):
            self.modelo.add_member(f"B{i}", f"N{no_inicio}", f"N{no_fim}", 'Aco', 'Secao_Generica')

    def aplicar_carga_distribuida(self, q_kNm2, vao_x, espacamento):
        q_linear = q_kNm2 * espacamento
        for nome_barra, barra in self.modelo.Members.items():
            z_medio = (barra.i_node.Z + barra.j_node.Z) / 2
            if z_medio > 0.1:
                self.modelo.add_member_dist_load(nome_barra, Direction='FZ', w1=-q_linear, w2=-q_linear)

    def resolver(self):
        try:
            self.modelo.analyze(check_stability=True)
            return True
        except Exception as e:
            return str(e)
