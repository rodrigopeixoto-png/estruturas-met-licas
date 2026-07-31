import numpy as np

# Catálogo completo de Perfis Laminados (Linha W Gerdau)
CATALOGO_LAMINADOS = {
    "W 150 x 13.0": {"familia": "Laminado W", "d": 148, "bf": 100, "tw": 4.3, "tf": 4.9, "A": 16.6, "Ix": 634, "Iy": 82, "Wx": 85.7, "Wy": 16.4},
    "W 150 x 18.0": {"familia": "Laminado W", "d": 153, "bf": 102, "tw": 5.8, "tf": 7.1, "A": 23.0, "Ix": 923, "Iy": 126, "Wx": 120.7, "Wy": 24.7},
    "W 200 x 15.0": {"familia": "Laminado W", "d": 200, "bf": 100, "tw": 4.3, "tf": 5.2, "A": 19.1, "Ix": 1305, "Iy": 87, "Wx": 130.5, "Wy": 17.4},
    "W 200 x 22.5": {"familia": "Laminado W", "d": 206, "bf": 102, "tw": 6.2, "tf": 8.0, "A": 28.6, "Ix": 2029, "Iy": 142, "Wx": 197.0, "Wy": 27.9},
    "W 250 x 25.3": {"familia": "Laminado W", "d": 257, "bf": 102, "tw": 6.1, "tf": 8.4, "A": 32.2, "Ix": 3415, "Iy": 149, "Wx": 265.8, "Wy": 29.3},
    "W 310 x 32.7": {"familia": "Laminado W", "d": 308, "bf": 102, "tw": 6.6, "tf": 10.8, "A": 41.7, "Ix": 6524, "Iy": 192, "Wx": 423.6, "Wy": 37.7},
    "W 360 x 44.0": {"familia": "Laminado W", "d": 352, "bf": 171, "tw": 6.9, "tf": 9.8, "A": 56.1, "Ix": 12185, "Iy": 816, "Wx": 692.3, "Wy": 95.5},
}

# Catálogo completo de Perfis de Chapa Dobrada (U Simples, U Enrijecido e Cantoneiras)
CATALOGO_CHAPA_DOBRADA = {
    "U 75 x 40 x 2.25": {"familia": "Chapa Dobrada U", "d": 75, "bf": 40, "tw": 2.25, "tf": 2.25, "A": 3.31, "Ix": 28.3, "Iy": 5.0, "Wx": 7.55, "Wy": 1.76},
    "U 100 x 40 x 2.25": {"familia": "Chapa Dobrada U", "d": 100, "bf": 40, "tw": 2.25, "tf": 2.25, "A": 3.87, "Ix": 58.2, "Iy": 5.8, "Wx": 11.64, "Wy": 1.98},
    "U 127 x 50 x 3.00": {"familia": "Chapa Dobrada U", "d": 127, "bf": 50, "tw": 3.00, "tf": 3.00, "A": 6.51, "Ix": 160.2, "Iy": 15.2, "Wx": 25.23, "Wy": 4.31},
    "U 150 x 50 x 3.00": {"familia": "Chapa Dobrada U", "d": 150, "bf": 50, "tw": 3.00, "tf": 3.00, "A": 7.20, "Ix": 248.5, "Iy": 16.4, "Wx": 33.13, "Wy": 4.50},
    "UE 100 x 50 x 17 x 2.25": {"familia": "U Enrijecido", "d": 100, "bf": 50, "tw": 2.25, "tf": 2.25, "A": 4.88, "Ix": 78.4, "Iy": 15.1, "Wx": 15.68, "Wy": 4.25},
    "UE 127 x 50 x 17 x 2.65": {"familia": "U Enrijecido", "d": 127, "bf": 50, "tw": 2.65, "tf": 2.65, "A": 6.46, "Ix": 161.0, "Iy": 18.2, "Wx": 25.35, "Wy": 4.98},
    "UE 150 x 60 x 20 x 3.00": {"familia": "U Enrijecido", "d": 150, "bf": 60, "tw": 3.00, "tf": 3.00, "A": 8.70, "Ix": 308.2, "Iy": 35.8, "Wx": 41.09, "Wy": 8.32},
    "2x L 2\" x 3/16\" (Dupla)": {"familia": "Cantoneira Dupla", "d": 50.8, "bf": 50.8, "tw": 4.76, "tf": 4.76, "A": 9.16, "Ix": 21.8, "Iy": 44.2, "Wx": 6.0, "Wy": 10.2},
    "2x L 2.1/2\" x 1/4\" (Dupla)": {"familia": "Cantoneira Dupla", "d": 63.5, "bf": 63.5, "tw": 6.35, "tf": 6.35, "A": 14.8, "Ix": 54.8, "Iy": 112.0, "Wx": 12.1, "Wy": 21.5},
}

CATALOGO_COMPLETO = {**CATALOGO_LAMINADOS, **CATALOGO_CHAPA_DOBRADA}

PROPRIEDADES_ACO = {
    "ASTM A36": {"fy": 250, "fu": 400},
    "ASTM A572 Gr 50": {"fy": 345, "fu": 450},
    "USI CIVIL 300": {"fy": 300, "fu": 410}
}

class VerificadorNBR8800:
    def __init__(self, tipo_aco="ASTM A572 Gr 50"):
        self.aco = PROPRIEDADES_ACO.get(tipo_aco, PROPRIEDADES_ACO["ASTM A572 Gr 50"])
        self.gamma_a1 = 1.10

    def verificar_elemento(self, nome_perfil, N_sd, V_sd, M_sd, delta_sd_mm, vao_m, fator_esforso=1.0):
        """Verifica um grupo de barras específico para a NBR 8800."""
        perfil = CATALOGO_COMPLETO.get(nome_perfil, CATALOGO_LAMINADOS["W 200 x 22.5"])
        fy = self.aco["fy"] / 10.0 # Converte MPa para kN/cm²
        A = perfil["A"] # cm²
        Wx = perfil["Wx"] # cm³
        d = perfil["d"] / 10.0 # cm
        tw = perfil["tw"] / 10.0 # cm

        # Esforços minorados/ponderados por elemento
        N_sd_e = abs(N_sd) * fator_esforso
        V_sd_e = abs(V_sd) * fator_esforso
        M_sd_e = abs(M_sd) * fator_esforso

        # 1. Momento Resistente (kNm)
        M_rd = (Wx * fy) / (100.0 * self.gamma_a1)

        # 2. Esforço Cortante Resistente (kN)
        Av = d * tw
        V_rd = (0.60 * Av * fy) / self.gamma_a1

        # 3. Compressão/Tração Resistente (kN)
        N_rd = (A * fy) / self.gamma_a1

        # Ratios de utilização
        ratio_N = N_sd_e / N_rd if N_rd > 0 else 0
        ratio_V = V_sd_e / V_rd if V_rd > 0 else 0
        ratio_M = M_sd_e / M_rd if M_rd > 0 else 0

        # Limite de Flecha ELS
        delta_lim_mm = (vao_m * 1000.0) / 250.0
        ratio_delta = delta_sd_mm / delta_lim_mm if delta_lim_mm > 0 else 0

        taxa_maxima = max(ratio_N, ratio_V, ratio_M, ratio_delta)

        return {
            "perfil": nome_perfil,
            "familia": perfil["familia"],
            "aprovado": taxa_maxima <= 1.0,
            "taxa_maxima": taxa_maxima * 100.0,
            "ratio_N": ratio_N * 100.0,
            "ratio_V": ratio_V * 100.0,
            "ratio_M": ratio_M * 100.0,
            "ratio_delta": ratio_delta * 100.0,
            "M_rd": M_rd,
            "V_rd": V_rd,
            "N_rd": N_rd,
            "delta_lim_mm": delta_lim_mm
        }
