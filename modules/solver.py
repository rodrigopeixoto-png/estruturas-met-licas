import numpy as np

class MotorCalculo3D:
    def __init__(self):
        """Motor de Análise Matricial 3D de Estruturas (Método da Rigidez Direta com FEF)"""
        self.E = 200e6      
        self.G = 77e6       
        self.A = 0.005      
        self.Iy = 0.0001    
        self.Iz = 0.0001    
        self.J = 0.00005    
        
        self.nos = []
        self.barras = []
        self.apoios = []
        self.cargas_nodais = []
        self.fef_local = {}

    def construir_malha(self, nos_x, nos_y, nos_z, barras, tipo_apoio_base):
        self.nos = list(zip(nos_x, nos_y, nos_z))
        self.barras = barras
        self.apoios = []
        
        for i, (x, y, z) in enumerate(self.nos):
            if z == 0:
                if "Engastado" in tipo_apoio_base:
                    self.apoios.extend([i*6 + dof for dof in range(6)])
                else:
                    self.apoios.extend([i*6 + dof for dof in range(3)])

    def _get_T(self, dx, dy, dz, L):
        cx, cy, cz = dx/L, dy/L, dz/L
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
        return T, r3x3

    def _matriz_elemento_3d(self, no1, no2):
        x1, y1, z1 = self.nos[no1]
        x2, y2, z2 = self.nos[no2]
        dx, dy, dz = x2 - x1, y2 - y1, z2 - z1
        L = np.sqrt(dx**2 + dy**2 + dz**2)
        if L == 0: L = 1e-6
        
        k_loc = np.zeros((12, 12))
        EA_L = (self.E * self.A) / L
        k_loc[0, 0] = k_loc[6, 6] = EA_L
        k_loc[0, 6] = k_loc[6, 0] = -EA_L
        
        GJ_L = (self.G * self.J) / L
        k_loc[3, 3] = k_loc[9, 9] = GJ_L
        k_loc[3, 9] = k_loc[9, 3] = -GJ_L
        
        k12_Iz, k6_Iz, k4_Iz, k2_Iz = (12*self.E*self.Iz)/(L**3), (6*self.E*self.Iz)/(L**2), (4*self.E*self.Iz)/L, (2*self.E*self.Iz)/L
        k_loc[1, 1] = k_loc[7, 7] = k12_Iz
        k_loc[1, 7] = k_loc[7, 1] = -k12_Iz
        k_loc[1, 5] = k_loc[5, 1] = k_loc[1, 11] = k_loc[11, 1] = k6_Iz
        k_loc[5, 7] = k_loc[7, 5] = -k6_Iz
        k_loc[7, 11] = k_loc[11, 7] = -k6_Iz
        k_loc[5, 5] = k_loc[11, 11] = k4_Iz
        k_loc[5, 11] = k_loc[11, 5] = k2_Iz

        k12_Iy, k6_Iy, k4_Iy, k2_Iy = (12*self.E*self.Iy)/(L**3), (6*self.E*self.Iy)/(L**2), (4*self.E*self.Iy)/L, (2*self.E*self.Iy)/L
        k_loc[2, 2] = k_loc[8, 8] = k12_Iy
        k_loc[2, 8] = k_loc[8, 2] = -k12_Iy
        k_loc[2, 4] = k_loc[4, 2] = k_loc[2, 10] = k_loc[10, 2] = -k6_Iy
        k_loc[4, 8] = k_loc[8, 4] = k6_Iy
        k_loc[8, 10] = k_loc[10, 8] = k6_Iy
        k_loc[4, 4] = k_loc[10, 10] = k4_Iy
        k_loc[4, 10] = k_loc[10, 4] = k2_Iy

        T, R = self._get_T(dx, dy, dz, L)
        k_glob = T.T @ k_loc @ T
        return k_glob, k_loc, T, R, L

    def aplicar_carga_distribuida(self, q_kNm2, vao_x, espacamento):
        q_linear = q_kNm2 * espacamento
        num_dofs = len(self.nos) * 6
        self.cargas_nodais = np.zeros(num_dofs)
        self.fef_local = {}

        for i, (n1, n2) in enumerate(self.barras):
            z_medio = (self.nos[n1][2] + self.nos[n2][2]) / 2.0
            if z_medio > 0.1:
                x1, y1, z1 = self.nos[n1]
                x2, y2, z2 = self.nos[n2]
                L = np.sqrt((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)
                
                T, R = self._get_T(x2-x1, y2-y1, z2-z1, L)
                
                # Carga -q em Z global transposta para eixos locais
                q_glob = np.array([0, 0, -q_linear])
                q_loc = R.T @ q_glob
                qx, qy, qz = q_loc
                
                # Fixed End Forces (Forças de Engastamento Perfeito) em eixo Local
                fef_loc = np.zeros(12)
                fef_loc[0], fef_loc[6] = -qx*L/2, -qx*L/2
                fef_loc[1], fef_loc[7] = -qy*L/2, -qy*L/2
                fef_loc[5], fef_loc[11] = -qy*(L**2)/12, qy*(L**2)/12
                fef_loc[2], fef_loc[8] = -qz*L/2, -qz*L/2
                fef_loc[4], fef_loc[10] = qz*(L**2)/12, -qz*(L**2)/12
                
                self.fef_local[i] = fef_loc
                fef_glob = T.T @ fef_loc
                
                # Aplica as reações invertidas aos nós da malha
                self.cargas_nodais[n1*6:n1*6+6] -= fef_glob[0:6]
                self.cargas_nodais[n2*6:n2*6+6] -= fef_glob[6:12]

    def resolver(self):
        try:
            num_dofs = len(self.nos) * 6
            K_global = np.zeros((num_dofs, num_dofs))
            k_locs, Ts = {}, {}
            
            for i, (n1, n2) in enumerate(self.barras):
                k_glob, k_loc, T, _, _ = self._matriz_elemento_3d(n1, n2)
                k_locs[i], Ts[i] = k_loc, T
                dofs = [n1*6 + d for d in range(6)] + [n2*6 + d for d in range(6)]
                for r in range(12):
                    for c in range(12):
                        K_global[dofs[r], dofs[c]] += k_glob[r, c]

            dofs_livres = [d for d in range(num_dofs) if d not in self.apoios]
            K_livre = K_global[np.ix_(dofs_livres, dofs_livres)]
            F_livre = self.cargas_nodais[dofs_livres]

            U_livre = np.linalg.solve(K_livre, F_livre)
            U_completo = np.zeros(num_dofs)
            U_completo[dofs_livres] = U_livre

            n_max, v_max, m_max = 0.0, 0.0, 0.0
            esforcos = []

            for i, (n1, n2) in enumerate(self.barras):
                dofs = [n1*6 + d for d in range(6)] + [n2*6 + d for d in range(6)]
                u_elem = U_completo[dofs]
                
                f_loc = k_locs[i] @ Ts[i] @ u_elem
                if i in self.fef_local:
                    f_loc += self.fef_local[i]
                    
                N1, N2 = -f_loc[0], f_loc[6]
                Vy1, Vy2 = f_loc[1], -f_loc[7]
                Vz1, Vz2 = f_loc[2], -f_loc[8]
                T1, T2 = -f_loc[3], f_loc[9]
                My1, My2 = -f_loc[4], f_loc[10]
                Mz1, Mz2 = -f_loc[5], f_loc[11]

                esforcos.append({
                    "n1": n1, "n2": n2,
                    "N": (N1, N2), "Vy": (Vy1, Vy2), "Vz": (Vz1, Vz2),
                    "My": (My1, My2), "Mz": (Mz1, Mz2)
                })

                n_max = max(n_max, abs(N1), abs(N2))
                v_max = max(v_max, abs(Vy1), abs(Vy2), abs(Vz1), abs(Vz2))
                m_max = max(m_max, abs(My1), abs(My2), abs(Mz1), abs(Mz2))

            F_total = K_global @ U_completo
            reacoes = {}
            for dof in self.apoios:
                no = dof // 6
                eixo = dof % 6
                if no not in reacoes: reacoes[no] = [0.0]*6
                reacoes[no][eixo] = float(F_total[dof] - self.cargas_nodais[dof])

            desloc_max_mm = float(np.max(np.abs(U_completo)) * 1000.0)

            return {
                "sucesso": True, "num_nos": len(self.nos), "num_barras": len(self.barras),
                "n_max_kn": float(n_max), "v_max_kn": float(v_max), "m_max_knm": float(m_max),
                "desloc_max_mm": desloc_max_mm,
                "esforcos": esforcos, "reacoes": reacoes, "nos": self.nos, "barras": self.barras
            }
        except Exception as e:
            return {"sucesso": False, "erro": str(e)}
