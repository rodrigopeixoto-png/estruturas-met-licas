import numpy as np

# Catálogo de Perfis Laminados (Linha W Gerdau)
CATALOGO_LAMINADOS = {
    "W 150 x 13.0": {"familia": "Laminado W", "d": 148, "bf": 100, "tw": 4.3, "tf": 4.9, "A": 16.6, "Ix": 634, "Iy": 82, "Wx": 85.7, "Wy": 16.4},
    "W 150 x 18.0": {"familia": "Laminado W", "d": 153, "bf": 102, "tw": 5.8, "tf": 7.1, "A": 23.0, "Ix": 923, "Iy": 126, "Wx": 120.7, "Wy": 24.7},
    "W 200 x 15.0": {"familia": "Laminado W", "d": 200, "bf": 100, "tw": 4.3, "tf": 5.2, "A": 19.1, "Ix": 1305, "Iy": 87, "Wx": 130.5, "Wy": 17.4},
    "W 200 x 22.5": {"familia": "Laminado W", "d": 206, "bf": 102, "tw": 6.2, "tf": 8.0, "A": 28.6, "Ix": 2029, "Iy": 142, "Wx": 197.0, "Wy": 27.9},
    "W 250 x 25.3": {"familia": "Laminado W", "d": 257, "bf": 102, "tw": 6.1, "tf": 8.4, "A": 32.2, "Ix": 3415, "Iy": 149, "Wx": 265.8, "Wy": 29.3},
    "W 310 x 32.7": {"familia": "Laminado W", "d": 308, "bf": 102, "tw": 6.6, "tf": 10.8, "A": 41.7, "Ix": 6524, "Iy": 192, "Wx": 423.6, "Wy": 37.7},
    "W 360 x 44.0": {"familia": "Laminado W", "d": 352, "bf": 171, "tw": 6.9, "tf": 9.8, "A": 56.1, "Ix": 12185, "Iy": 816, "Wx": 692.3, "Wy": 95.5},
}

# Catálogo de Perfis de Chapa Dobrada (Perfis U Simples da Tabela + U Enrijecidos e Cantoneiras)
CATALOGO_CHAPA_DOBRADA = {
    # Perfis U Simples (Tabela NBR)
    # --- h = 50 mm, B = 25 mm ---
    "U 50 x 25 x 2.00": {"familia": "Chapa Dobrada U", "d": 50, "bf": 25, "tw": 2.00, "tf": 2.00, "A": 1.75, "Ix": 6.66, "Iy": 1.07, "Wx": 2.60, "Wy": 0.60},
    "U 50 x 25 x 2.25": {"familia": "Chapa Dobrada U", "d": 50, "bf": 25, "tw": 2.25, "tf": 2.25, "A": 2.07, "Ix": 7.70, "Iy": 1.26, "Wx": 3.00, "Wy": 0.71},
    "U 50 x 25 x 2.65": {"familia": "Chapa Dobrada U", "d": 50, "bf": 25, "tw": 2.65, "tf": 2.65, "A": 2.38, "Ix": 8.66, "Iy": 1.43, "Wx": 3.40, "Wy": 0.82},
    "U 50 x 25 x 3.00": {"familia": "Chapa Dobrada U", "d": 50, "bf": 25, "tw": 3.00, "tf": 3.00, "A": 2.67, "Ix": 9.55, "Iy": 1.59, "Wx": 3.80, "Wy": 0.92},

    # --- h = 75 mm, B = 38 mm ---
    "U 75 x 38 x 2.00": {"familia": "Chapa Dobrada U", "d": 75, "bf": 38, "tw": 2.00, "tf": 2.00, "A": 2.80, "Ix": 25.10, "Iy": 4.55, "Wx": 6.60, "Wy": 1.58},
    "U 75 x 38 x 2.25": {"familia": "Chapa Dobrada U", "d": 75, "bf": 38, "tw": 2.25, "tf": 2.25, "A": 3.32, "Ix": 29.43, "Iy": 5.37, "Wx": 7.80, "Wy": 1.88},
    "U 75 x 38 x 2.65": {"familia": "Chapa Dobrada U", "d": 75, "bf": 38, "tw": 2.65, "tf": 2.65, "A": 3.84, "Ix": 33.56, "Iy": 6.15, "Wx": 8.90, "Wy": 2.17},
    "U 75 x 38 x 3.00": {"familia": "Chapa Dobrada U", "d": 75, "bf": 38, "tw": 3.00, "tf": 3.00, "A": 4.35, "Ix": 37.49, "Iy": 6.91, "Wx": 9.90, "Wy": 2.45},
    "U 75 x 38 x 4.75": {"familia": "Chapa Dobrada U", "d": 75, "bf": 38, "tw": 4.75, "tf": 4.75, "A": 6.48, "Ix": 52.75, "Iy": 10.00, "Wx": 14.00, "Wy": 3.66},

    # --- h = 100 mm, B = 40 mm ---
    "U 100 x 40 x 2.00": {"familia": "Chapa Dobrada U", "d": 100, "bf": 40, "tw": 2.00, "tf": 2.00, "A": 3.27, "Ix": 49.01, "Iy": 4.99, "Wx": 9.80, "Wy": 1.65},
    "U 100 x 40 x 2.25": {"familia": "Chapa Dobrada U", "d": 100, "bf": 40, "tw": 2.25, "tf": 2.25, "A": 3.89, "Ix": 57.67, "Iy": 5.89, "Wx": 11.50, "Wy": 1.96},
    "U 100 x 40 x 2.65": {"familia": "Chapa Dobrada U", "d": 100, "bf": 40, "tw": 2.65, "tf": 2.65, "A": 4.51, "Ix": 65.99, "Iy": 6.76, "Wx": 13.10, "Wy": 2.26},
    "U 100 x 40 x 3.00": {"familia": "Chapa Dobrada U", "d": 100, "bf": 40, "tw": 3.00, "tf": 3.00, "A": 5.11, "Ix": 73.99, "Iy": 7.61, "Wx": 14.70, "Wy": 2.56},
    "U 100 x 40 x 4.75": {"familia": "Chapa Dobrada U", "d": 100, "bf": 40, "tw": 4.75, "tf": 4.75, "A": 7.67, "Ix": 105.90, "Iy": 11.09, "Wx": 21.10, "Wy": 3.84},

    # --- h = 100 mm, B = 50 mm ---
    "U 100 x 50 x 2.00": {"familia": "Chapa Dobrada U", "d": 100, "bf": 50, "tw": 2.00, "tf": 2.00, "A": 3.65, "Ix": 58.15, "Iy": 9.24, "Wx": 11.60, "Wy": 2.52},
    "U 100 x 50 x 2.25": {"familia": "Chapa Dobrada U", "d": 100, "bf": 50, "tw": 2.25, "tf": 2.25, "A": 4.35, "Ix": 68.55, "Iy": 10.94, "Wx": 13.70, "Wy": 3.00},
    "U 100 x 50 x 2.65": {"familia": "Chapa Dobrada U", "d": 100, "bf": 50, "tw": 2.65, "tf": 2.65, "A": 5.04, "Ix": 78.60, "Iy": 12.59, "Wx": 15.70, "Wy": 3.48},
    "U 100 x 50 x 3.00": {"familia": "Chapa Dobrada U", "d": 100, "bf": 50, "tw": 3.00, "tf": 3.00, "A": 5.71, "Ix": 88.29, "Iy": 14.20, "Wx": 17.60, "Wy": 3.94},
    "U 100 x 50 x 4.75": {"familia": "Chapa Dobrada U", "d": 100, "bf": 50, "tw": 4.75, "tf": 4.75, "A": 8.63, "Ix": 127.50, "Iy": 20.89, "Wx": 25.40, "Wy": 5.84},

    # --- h = 127 mm, B = 50 mm ---
    "U 127 x 50 x 2.00": {"familia": "Chapa Dobrada U", "d": 127, "bf": 50, "tw": 2.00, "tf": 2.00, "A": 4.17, "Ix": 101.30, "Iy": 9.94, "Wx": 15.90, "Wy": 2.61},
    "U 127 x 50 x 2.25": {"familia": "Chapa Dobrada U", "d": 127, "bf": 50, "tw": 2.25, "tf": 2.25, "A": 4.97, "Ix": 119.60, "Iy": 11.78, "Wx": 18.80, "Wy": 3.10},
    "U 127 x 50 x 2.65": {"familia": "Chapa Dobrada U", "d": 127, "bf": 50, "tw": 2.65, "tf": 2.65, "A": 5.76, "Ix": 137.50, "Iy": 13.57, "Wx": 21.60, "Wy": 3.59},
    "U 127 x 50 x 3.00": {"familia": "Chapa Dobrada U", "d": 127, "bf": 50, "tw": 3.00, "tf": 3.00, "A": 6.53, "Ix": 154.80, "Iy": 15.32, "Wx": 24.30, "Wy": 4.08},
    "U 127 x 50 x 4.75": {"familia": "Chapa Dobrada U", "d": 127, "bf": 50, "tw": 4.75, "tf": 4.75, "A": 9.91, "Ix": 225.90, "Iy": 22.66, "Wx": 35.50, "Wy": 6.16},

    # --- h = 150 mm, B = 50 mm ---
    "U 150 x 50 x 2.00": {"familia": "Chapa Dobrada U", "d": 150, "bf": 50, "tw": 2.00, "tf": 2.00, "A": 4.60, "Ix": 149.90, "Iy": 10.42, "Wx": 19.90, "Wy": 2.66},
    "U 150 x 50 x 2.25": {"familia": "Chapa Dobrada U", "d": 150, "bf": 50, "tw": 2.25, "tf": 2.25, "A": 5.49, "Ix": 177.40, "Iy": 12.35, "Wx": 23.60, "Wy": 3.17},
    "U 150 x 50 x 2.65": {"familia": "Chapa Dobrada U", "d": 150, "bf": 50, "tw": 2.65, "tf": 2.65, "A": 6.37, "Ix": 204.10, "Iy": 14.24, "Wx": 27.20, "Wy": 3.67},
    "U 150 x 50 x 3.00": {"familia": "Chapa Dobrada U", "d": 150, "bf": 50, "tw": 3.00, "tf": 3.00, "A": 7.23, "Ix": 230.10, "Iy": 16.08, "Wx": 30.60, "Wy": 4.16},
    "U 150 x 50 x 4.75": {"familia": "Chapa Dobrada U", "d": 150, "bf": 50, "tw": 4.75, "tf": 4.75, "A": 11.01, "Ix": 338.00, "Iy": 23.84, "Wx": 45.00, "Wy": 6.30},

    # --- h = 200 mm, B = 50 mm ---
    "U 200 x 50 x 2.00": {"familia": "Chapa Dobrada U", "d": 200, "bf": 50, "tw": 2.00, "tf": 2.00, "A": 5.55, "Ix": 299.30, "Iy": 11.20, "Wx": 29.90, "Wy": 2.74},
    "U 200 x 50 x 2.25": {"familia": "Chapa Dobrada U", "d": 200, "bf": 50, "tw": 2.25, "tf": 2.25, "A": 6.63, "Ix": 354.90, "Iy": 13.28, "Wx": 35.40, "Wy": 3.26},
    "U 200 x 50 x 2.65": {"familia": "Chapa Dobrada U", "d": 200, "bf": 50, "tw": 2.65, "tf": 2.65, "A": 7.70, "Ix": 409.30, "Iy": 15.32, "Wx": 40.90, "Wy": 3.78},
    "U 200 x 50 x 3.00": {"familia": "Chapa Dobrada U", "d": 200, "bf": 50, "tw": 3.00, "tf": 3.00, "A": 8.75, "Ix": 462.40, "Iy": 17.31, "Wx": 46.20, "Wy": 4.29},
    "U 200 x 50 x 4.75": {"familia": "Chapa Dobrada U", "d": 200, "bf": 50, "tw": 4.75, "tf": 4.75, "A": 13.39, "Ix": 686.20, "Iy": 25.76, "Wx": 68.60, "Wy": 6.51},

    # Perfis U Enrijecidos
    "UE 100 x 50 x 17 x 2.25": {"familia": "U Enrijecido", "d": 100, "bf": 50, "tw": 2.25, "tf": 2.25, "A": 4.88, "Ix": 78.4, "Iy": 15.1, "Wx": 15.68, "Wy": 4.25},
    "UE 127 x 50 x 17 x 2.65": {"familia": "U Enrijecido", "d": 127, "bf": 50, "tw": 2.65, "tf": 2.65, "A": 6.46, "Ix": 161.0, "Iy": 18.2, "Wx": 25.35, "Wy": 4.98},
    "UE 150 x 60 x 20 x 3.00": {"familia": "U Enrijecido", "d": 150, "bf": 60, "tw": 3.00, "tf": 3.00, "A": 8.70, "Ix": 308.2, "Iy": 35.8, "Wx": 41.09, "Wy": 8.32},

    # Cantoneiras
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
        perfil = CATALOGO_COMPLETO.get(nome_perfil, CATALOGO_LAMINADOS["W 200 x 22.5"])
        fy = self.aco["fy"] / 10.0  # MPa -> kN/cm²
        A = perfil["A"]
        Wx = perfil["Wx"]
        d = perfil["d"] / 10.0
        tw = perfil["tw"] / 10.0

        N_sd_e = abs(N_sd) * fator_esforso
        V_sd_e = abs(V_sd) * fator_esforso
        M_sd_e = abs(M_sd) * fator_esforso

        M_rd = (Wx * fy) / (100.0 * self.gamma_a1)
        Av = d * tw
        V_rd = (0.60 * Av * fy) / self.gamma_a1
        N_rd = (A * fy) / self.gamma_a1

        ratio_N = N_sd_e / N_rd if N_rd > 0 else 0
        ratio_V = V_sd_e / V_rd if V_rd > 0 else 0
        ratio_M = M_sd_e / M_rd if M_rd > 0 else 0

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
