import numpy as np

# Catálogo básico de perfis W (Gerdau) para dimensionamento
CATALOGO_W = {
    "W 150 x 13.0": {"d": 148, "bf": 100, "tw": 4.3, "tf": 4.9, "A": 16.6, "Ix": 634, "Iy": 82, "Wx": 85.7, "Wy": 16.4},
    "W 200 x 15.0": {"d": 200, "bf": 100, "tw": 4.3, "tf": 5.2, "A": 19.1, "Ix": 1305, "Iy": 87, "Wx": 130.5, "Wy": 17.4},
    "W 200 x 22.5": {"d": 206, "bf": 102, "tw": 6.2, "tf": 8.0, "A": 28.6, "Ix": 2029, "Iy": 142, "Wx": 197.0, "Wy": 27.9},
    "W 250 x 25.3": {"d": 257, "bf": 102, "tw": 6.1, "tf": 8.4, "A": 32.2, "Ix": 3415, "Iy": 149, "Wx": 265.8, "Wy": 29.3},
    "W 310 x 32.7": {"d": 308, "bf": 102, "tw": 6.6, "tf": 10.8, "A": 41.7, "Ix": 6524, "Iy": 192, "Wx": 423.6, "Wy": 37.7},
    "W 360 x 44.0": {"d": 352, "bf": 171, "tw": 6.9, "tf": 9.8, "A": 56.1, "Ix": 12185, "Iy": 816, "Wx": 692.3, "Wy": 95.5},
}

PROPRIEDADES_ACO = {
    "ASTM A36": {"fy": 250, "fu": 400}, # MPa
    "ASTM A572 Gr 50": {"fy": 345, "fu": 450} # MPa
}

class VerificadorNBR8800:
    def __init__(self, nome_perfil, tipo_aco="ASTM A572 Gr 50"):
        self.perfil = CATALOGO_W.get(nome_perfil, CATALOGO_W["W 200 x 22.5"])
        self.aco = PROPRIEDADES_ACO.get(tipo_aco, PROPRIEDADES_ACO["ASTM A572 Gr 50"])
        self.gamma_a1 = 1.10

    def calcular_resistencias(self, L_m):
        """Calcula os esforços resistentes nominais e de projeto conforme a NBR 8800."""
        fy = self.aco["fy"] / 10.0 # Converte MPa para kN/cm²
        A = self.perfil["A"] # cm²
        Wx = self.perfil["Wx"] # cm³
        d = self.perfil["d"] / 10.0 # cm
        tw = self.perfil["tw"] / 10.0 # cm

        # 1. Momento Resistente Plastico/Efetivo (M_Rd em kNm)
        M_rk = (Wx * fy) / 100.0 # kN.m
        M_rd = M_rk / self.gamma_a1

        # 2. Esforço Cortante Resistente (V_Rd em kN)
        # Área da alma Av = d * tw
        Av = d * tw
        V_rk = 0.60 * Av * fy
        V_rd = V_rk / self.gamma_a1

        # 3. Compressão Resistente (N_Rd em kN)
        N_rk = A * fy
        N_rd = N_rk / self.gamma_a1

        return {
            "M_rd": M_rd,
            "V_rd": V_rd,
            "N_rd": N_rd
        }

    def verificar_estrutura(self, N_sd, V_sd, M_sd, delta_sd_mm, vao_m):
        """Compara os esforços atuantes x resistentes e avalia a taxa de utilização."""
        res = self.calcular_resistencias(vao_m)
        
        ratio_N = abs(N_sd) / res["N_rd"] if res["N_rd"] > 0 else 0
        ratio_V = abs(V_sd) / res["V_rd"] if res["V_rd"] > 0 else 0
        ratio_M = abs(M_sd) / res["M_rd"] if res["M_rd"] > 0 else 0
        
        # Limite de Flecha para Coberturas (L / 250)
        delta_lim_mm = (vao_m * 1000.0) / 250.0
        ratio_delta = delta_sd_mm / delta_lim_mm if delta_lim_mm > 0 else 0

        taxa_maxima = max(ratio_N, ratio_V, ratio_M, ratio_delta)
        aprovado = taxa_maxima <= 1.0

        return {
            "aprovado": aprovado,
            "taxa_maxima": taxa_maxima * 100.0, # em %
            "ratio_N": ratio_N * 100.0,
            "ratio_V": ratio_V * 100.0,
            "ratio_M": ratio_M * 100.0,
            "ratio_delta": ratio_delta * 100.0,
            "delta_lim_mm": delta_lim_mm,
            "M_rd": res["M_rd"],
            "V_rd": res["V_rd"],
            "N_rd": res["N_rd"]
        }
