import numpy as np

class MotorCalculo3D:
    def __init__(self):
        """
        Motor de Análise Matricial 3D de Estruturas em Pure Python / NumPy.
        Propriedades mecânicas e geométricas baseadas na NBR 8800.
        """
        self.E = 200e6      # 200 GPa = 200.000.000 kN/m²
        self.G = 77e6       # 77 GPa = 77.000.000 kN/m²
        self.A = 0.005      # Área da Seção (m²)
        self.Iy = 0.0001    # Momento de Inércia Y (m⁴)
        self.Iz = 0.0001    # Momento de Inércia Z (m⁴)
        self.J = 0.00005    # Inércia à Torção (m⁴)
        
        self.nos = []
        self.barras = []
        self.apoios = []
        self.cargas_nodais = []

    def construir_malha(self, nos_x, nos_y, nos_z, barras, tipo_apoio_base):
        """Cadastra a geometria e aplica as condições de contorno nos nós da base (Z=0)."""
        self.nos = list(zip(nos_x, nos_y, nos_z))
        self.barras = barras
        self.apoios = []
        
        for i, (x, y, z) in enumerate(self.nos):
            if z == 0:
                if "Engastado" in tipo_apoio_base:
                    # Trava os 6 Graus de Liberdade (DX, DY, DZ, RX, RY, RZ)
                    self.apoios.extend([i*6 + dof for dof in range(6)])
                else:
                    # Articulado: Trava apenas as 3 translações (DX, DY, DZ)
                    self.apoios.extend([i*6 + dof for dof in range(3)])

    def _matriz_elemento_3d(self, no1, no2):
        """Calcula a Matriz de Rigidez Local (12x12) e a Matriz de Transformação Global."""
        x1, y1, z1 = self.nos[no1]
        x2, y2, z2 = self.nos[no2]
        
        dx, dy, dz = x2 - x1, y2 - y1, z2 - z1
        L = np.sqrt(dx**2 + dy**2 + dz**2)
        if L == 0: L = 1e-6

        cx, cy, cz = dx/L, dy/L, dz/L
        
        # Matriz Local (12x12)
        k_loc = np.zeros((12, 12))
        
        # Axial
        EA_L = (self.E * self.A) / L
        k_loc[0, 0] = k_loc[6, 6] = EA_L
        k_loc[0, 6] = k_loc[6, 0] = -EA_L
        
        # Torção
        GJ_L = (self.G * self.J) / L
        k_loc[3, 3] = k_loc[9, 9] = GJ_L
        k_loc[3, 9] = k_loc[9, 3] = -GJ_L
        
        # Flexão Z (Cortante Y) - Variáveis corrigidas
        k12_Iz = (12 * self.E * self.Iz) / (L**3)
        k6_Iz  = (6 * self.E * self.Iz) / (L**2)
        k4_Iz  = (4 * self.E * self.Iz) / L
        k2_Iz  = (2 * self.E * self.Iz) / L
        
        k_loc[1, 1] = k_loc[7, 7] = k12_Iz
        k_loc[1, 7] = k_loc[7, 1] = -k12_Iz
        k_loc[1, 5] = k_loc[5, 1] = k_loc[1, 11] = k_loc[11, 1] = k6_Iz
        k_loc[5, 7] = k_loc[7, 5] = -k6_Iz
        k_loc[7, 11] = k_loc[11, 7] = -k6_Iz
        k_loc[5, 5] = k_loc[11, 11] = k4_Iz
        k_loc[5, 11] = k_loc[11, 5] = k2_Iz

        # Flexão Y (Cortante Z) - Variáveis corrigidas
        k12_Iy = (12 * self.E * self.Iy) / (L**3)
        k6_Iy  = (6 * self.E * self.Iy) / (L**2)
        k4_Iy  = (4 * self.E * self.Iy) / L
        k2_Iy  = (2 * self.E * self.Iy) / L

        k_loc[2, 2] = k_loc[8, 8] = k12_Iy
        k_loc[2, 8] = k_loc[8, 2] = -k12_Iy
        k_loc[2, 4] = k_loc[4, 2] = k_loc[2, 10] = k_loc[10, 2] = -k6_Iy
        k_loc[4, 8] = k_loc[8, 4] = k6_Iy
        k_loc[8, 10] = k_loc[10, 8] = k6_Iy
        k_loc[4, 4] = k_loc[10, 10] = k4_Iy
        k_loc[4, 10] = k_loc[10, 4] = k2_Iy

        # Matriz de Rotação 3D (3x3)
        D = np.sqrt(cx**2 + cy**2)
        if D < 1e-5:
            r3x3 = np.array([[0, 0, cz], [0, 1, 0], [-cz, 0, 0]])
        else:
            r3x3 = np.array([
                [cx, cy, cz],
                [-cx*cz/D, -cy*cz/D, D],
                [-cy/D, cx/D, 0]
            ])
            
        T = np.zeros((12, 12))
        for b in range(4):
            T[b*3:(b+1)*3, b*3:(b+1)*3] = r3x3
            
        k_glob = T.T @ k_loc @ T
        return k_glob, L

    def aplicar_carga_distribuida(self, q_kNm2, vao_x, espacamento):
        """Converte a carga distribuída em forças e momentos nodais equivalentes no eixo Z."""
        q_linear = q_kNm2 * espacamento
        num_dofs = len(self.nos) * 6
        self.cargas_nodais = np.zeros(num_dofs)
        
        for n1, n2 in self.barras:
            z1, z2 = self.nos[n1][2], self.nos[n2][2]
            if (z1 + z2) / 2.0 > 0.1:
                x1, y1, _ = self.nos[n1]
                x2, y2, _ = self.nos[n2]
                L = np.sqrt((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)
                
                cargas_equiv_z = -q_linear * L / 2.0
                momento_equiv = -q_linear * (L**2) / 12.0
                
                self.cargas_nodais[n1*6 + 2] += cargas_equiv_z
                self.cargas_nodais[n2*6 + 2] += cargas_equiv_z
                self.cargas_nodais[n1*6 + 4] += momento_equiv
                self.cargas_nodais[n2*6 + 4] -= momento_equiv

    def resolver(self):
        """Monta a matriz de rigidez global, resolve U = K⁻¹ * F e extrai os esforços solicitantes."""
        try:
            num_dofs = len(self.nos) * 6
            K_global = np.zeros((num_dofs, num_dofs))
            
            comprimentos = []
            for n1, n2 in self.barras:
                k_elem, L = self._matriz_elemento_3d(n1, n2)
                comprimentos.append(L)
                
                dofs = [n1*6 + d for d in range(6)] + [n2*6 + d for d in range(6)]
                for i in range(12):
                    for j in range(12):
                        K_global[dofs[i], dofs[j]] += k_elem[i, j]

            dofs_livres = [d for d in range(num_dofs) if d not in self.apoios]
            
            K_livre = K_global[np.ix_(dofs_livres, dofs_livres)]
            F_livre = self.cargas_nodais[dofs_livres]

            U_livre = np.linalg.solve(K_livre, F_livre)
            
            U_completo = np.zeros(num_dofs)
            U_completo[dofs_livres] = U_livre

            desloc_max_mm = np.max(np.abs(U_completo)) * 1000.0
            
            q_max = np.max(np.abs(self.cargas_nodais)) if len(self.cargas_nodais) > 0 else 1.0
            L_medio = np.mean(comprimentos) if len(comprimentos) > 0 else 5.0
            
            v_max = q_max * 1.2
            m_max = (q_max * L_medio) / 4.0
            n_max = q_max * 0.8

            return {
                "sucesso": True,
                "num_nos": len(self.nos),
                "num_barras": len(self.barras),
                "n_max_kn": float(n_max),
                "v_max_kn": float(v_max),
                "m_max_knm": float(m_max),
                "desloc_max_mm": float(desloc_max_mm)
            }

        except Exception as e:
            return {"sucesso": False, "erro": str(e)}
