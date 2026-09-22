"""
=============================================================================
  MICRO-REFORMER KINETICS MODEL
  Steam Methane Reforming (SMR) + Water-Gas Shift (WGS)
  
  Reactions:
    R1: CH4 + H2O  <-> CO  + 3H2   ΔH°298 = +206.1 kJ/mol  (endothermic)
    R2: CO  + H2O  <-> CO2 + H2    ΔH°298 = -41.2  kJ/mol  (exothermic)
    R3: CH4 + 2H2O <-> CO2 + 4H2   ΔH°298 = +165.0 kJ/mol  (endothermic)
  
  Kinetics: Langmuir-Hinshelwood (Xu & Froment, 1989) — Ni/Al2O3 catalyst
=============================================================================
"""

import numpy as np
from scipy.integrate import solve_ivp
import warnings
warnings.filterwarnings("ignore")


# ─────────────────────────────────────────────
#  THERMODYNAMIC CONSTANTS
# ─────────────────────────────────────────────
R_GAS = 8.314          # J/(mol·K)
R_kJ  = 8.314e-3       # kJ/(mol·K)

# Standard enthalpies of formation at 298 K (kJ/mol)
DH_f = {
    "CH4":  -74.81,
    "H2O": -241.82,
    "CO":  -110.53,
    "CO2": -393.51,
    "H2":    0.00,
    "N2":    0.00,
}

# Reaction enthalpies (kJ/mol) — at 298 K
DH_R1 = +206.1     # SMR
DH_R2 =  -41.2     # WGS
DH_R3 = +165.0     # DR (combined)


# ─────────────────────────────────────────────
#  SHOMATE EQUATION — Cp (J/mol·K)
#  Source: NIST WebBook
# ─────────────────────────────────────────────
SHOMATE = {
    #      A        B         C          D         E         F          G         H
    "CH4": [  -0.703029, 108.4773, -42.52157,  5.862788, 0.678565,-76.84376, 158.7163, -74.87310],
    "H2O": [ 30.09200,   6.832514, 6.793435, -2.534480, 0.082139,-250.8810, 223.3967,-241.8264],
    "CO":  [ 25.56759,   6.096130, 4.054656, -2.671301, 0.131021,-118.0089, 227.3665,-110.5271],
    "CO2": [ 24.99735,  55.18696, -33.69137,  7.948387,-0.136638,-403.6075, 228.2431,-393.5224],
    "H2":  [ 33.066178,-11.363417, 11.432816, -2.772874,-0.158558,-9.980797, 172.7080,   0.0],
}

def cp_shomate(species: str, T_K: float) -> float:
    """Molar heat capacity [J/(mol·K)] via Shomate equation."""
    c = SHOMATE[species]
    t = T_K / 1000.0
    return c[0] + c[1]*t + c[2]*t**2 + c[3]*t**3 + c[4]/t**2


def enthalpy_reaction_T(reaction: int, T_K: float) -> float:
    """
    Temperature-corrected enthalpy of reaction [kJ/mol]
    using Kirchhoff's law: ΔH(T) = ΔH°298 + ∫Cp dT
    """
    T_ref = 298.15
    dT    = T_K - T_ref

    if reaction == 1:         # CH4 + H2O → CO + 3H2
        delta_cp = (cp_shomate("CO",  T_K) + 3*cp_shomate("H2", T_K)
                    - cp_shomate("CH4", T_K) - cp_shomate("H2O", T_K))
        return DH_R1 + delta_cp * dT / 1000.0

    elif reaction == 2:       # CO + H2O → CO2 + H2
        delta_cp = (cp_shomate("CO2", T_K) + cp_shomate("H2", T_K)
                    - cp_shomate("CO",  T_K) - cp_shomate("H2O", T_K))
        return DH_R2 + delta_cp * dT / 1000.0

    elif reaction == 3:       # CH4 + 2H2O → CO2 + 4H2
        delta_cp = (cp_shomate("CO2", T_K) + 4*cp_shomate("H2", T_K)
                    - cp_shomate("CH4", T_K) - 2*cp_shomate("H2O", T_K))
        return DH_R3 + delta_cp * dT / 1000.0


# ─────────────────────────────────────────────
#  EQUILIBRIUM CONSTANTS
#  ln K = -ΔG°/RT  (van't Hoff integration)
# ─────────────────────────────────────────────
def equilibrium_constants(T_K: float) -> dict:
    """
    Equilibrium constants for the three reforming reactions.
    Correlations from Xu & Froment (1989), valid 500–1300 K.
    """
    # K1 (SMR)  [bar²]
    K1 = np.exp(-26830/T_K + 30.114)

    # K2 (WGS)  [dimensionless]
    K2 = np.exp(4400/T_K - 4.036)

    # K3 = K1 * K2  [bar²]
    K3 = K1 * K2

    return {"K1": K1, "K2": K2, "K3": K3}


# ─────────────────────────────────────────────
#  LANGMUIR-HINSHELWOOD RATE EXPRESSIONS
#  Xu & Froment (1989) — Ni/MgAl2O4 catalyst
#  Units: mol/(kg_cat · s)
# ─────────────────────────────────────────────

# Pre-exponential factors [mol/(kg·s·bar^n)]
A_k1  = 4.225e15     # SMR rate constant pre-exp
A_k2  = 1.955e6      # WGS rate constant pre-exp
A_k3  = 1.020e15     # DR  rate constant pre-exp

# Activation energies [kJ/mol]
Ea_1  = 240.1
Ea_2  = 67.13
Ea_3  = 243.9

# Adsorption pre-exponentials [bar⁻¹]
A_KCH4 = 6.65e-4
A_KH2O = 1.77e5
A_KCO  = 8.23e-5
A_KH2  = 6.12e-9

# Adsorption enthalpies [kJ/mol]
dH_CH4 = -38.28
dH_H2O =  88.68
dH_CO  = -70.65
dH_H2  = -82.90


def adsorption_terms(T_K: float, P_CH4: float, P_H2O: float,
                     P_CO: float, P_H2: float) -> float:
    """
    Denominator term (DEN)² for L-H rate expressions.
    Partial pressures in [bar].
    """
    K_CH4 = A_KCH4 * np.exp(-dH_CH4 * 1000 / (R_GAS * T_K))
    K_H2O = A_KH2O * np.exp(-dH_H2O * 1000 / (R_GAS * T_K))
    K_CO  = A_KCO  * np.exp(-dH_CO  * 1000 / (R_GAS * T_K))
    K_H2  = A_KH2  * np.exp(-dH_H2  * 1000 / (R_GAS * T_K))

    DEN = (1 + K_CO * P_CO + K_H2 * P_H2 + K_CH4 * P_CH4
           + K_H2O * P_H2O / P_H2)
    return DEN


def reaction_rates(T_K: float, P_total: float, y: np.ndarray) -> np.ndarray:
    """
    Intrinsic reaction rates r1, r2, r3 [mol/(kg_cat·s)]
    
    Parameters
    ----------
    T_K    : Temperature [K]
    P_total: Total pressure [bar]
    y      : Mole fractions [y_CH4, y_H2O, y_CO, y_CO2, y_H2]
    
    Returns
    -------
    rates  : array [r1, r2, r3]
    """
    y_CH4, y_H2O, y_CO, y_CO2, y_H2 = y

    # Partial pressures [bar]
    P_CH4 = max(y_CH4 * P_total, 1e-10)
    P_H2O = max(y_H2O * P_total, 1e-10)
    P_CO  = max(y_CO  * P_total, 1e-10)
    P_CO2 = max(y_CO2 * P_total, 1e-10)
    P_H2  = max(y_H2  * P_total, 1e-10)

    # Equilibrium constants
    K = equilibrium_constants(T_K)
    K1, K2, K3 = K["K1"], K["K2"], K["K3"]

    # Rate constants (Arrhenius)
    k1 = A_k1 * np.exp(-Ea_1 * 1000 / (R_GAS * T_K))
    k2 = A_k2 * np.exp(-Ea_2 * 1000 / (R_GAS * T_K))
    k3 = A_k3 * np.exp(-Ea_3 * 1000 / (R_GAS * T_K))

    # Adsorption denominator
    DEN = adsorption_terms(T_K, P_CH4, P_H2O, P_CO, P_H2)

    # Reaction driving forces
    RF1 = (P_CH4 * P_H2O / P_H2**2.5) - (P_CO * P_H2**0.5 / K1)
    RF2 = (P_CO * P_H2O / P_H2) - (P_CO2 / K2)
    RF3 = (P_CH4 * P_H2O**2 / P_H2**3.5) - (P_CO2 * P_H2**0.5 / K3)

    r1 = k1 * RF1 / DEN**2
    r2 = k2 * RF2 / DEN**2
    r3 = k3 * RF3 / DEN**2

    return np.array([r1, r2, r3])


# ─────────────────────────────────────────────
#  PFR MOLE BALANCE ODE
# ─────────────────────────────────────────────
def smr_ode(W: float, F: np.ndarray,
            T_K: float, P_bar: float, F_total0: float) -> np.ndarray:
    """
    Mole balance for plug-flow reformer (per unit catalyst mass).
    
    State: F = [F_CH4, F_H2O, F_CO, F_CO2, F_H2]  [mol/s]
    W     : catalyst weight [kg]
    """
    F_CH4, F_H2O, F_CO, F_CO2, F_H2 = F
    F_total = F_CH4 + F_H2O + F_CO + F_CO2 + F_H2
    F_total = max(F_total, 1e-12)

    y = np.array([F_CH4, F_H2O, F_CO, F_CO2, F_H2]) / F_total
    r = reaction_rates(T_K, P_bar, y)

    r1, r2, r3 = r[0], r[1], r[2]

    # Stoichiometry
    dF_CH4 = -(r1 + r3)
    dF_H2O = -(r1 + r2 + 2*r3)
    dF_CO  =  (r1 - r2)
    dF_CO2 =  (r2 + r3)
    dF_H2  =  (3*r1 + r2 + 4*r3)

    return np.array([dF_CH4, dF_H2O, dF_CO, dF_CO2, dF_H2])


def run_pfr(T_K: float = 800+273.15, P_bar: float = 1.0,
            SC_ratio: float = 3.0, F_CH4_in: float = 1e-4,
            W_cat: float = 1.0) -> dict:
    """
    Solve PFR mole balance for given operating conditions.
    
    Returns dict with axial profiles and performance metrics.
    """
    F_H2O_in = SC_ratio * F_CH4_in
    F_in     = np.array([F_CH4_in, F_H2O_in, 0.0, 0.0, 0.0])
    F_total0 = F_in.sum()

    W_span = (0, W_cat)
    W_eval = np.linspace(0, W_cat, 200)

    sol = solve_ivp(
        fun=lambda W, F: smr_ode(W, F, T_K, P_bar, F_total0),
        t_span=W_span, y0=F_in, t_eval=W_eval,
        method="Radau", rtol=1e-6, atol=1e-10
    )

    F_CH4 = sol.y[0]; F_H2O = sol.y[1]
    F_CO  = sol.y[2]; F_CO2 = sol.y[3]; F_H2 = sol.y[4]

    X_CH4 = (F_CH4_in - F_CH4) / F_CH4_in * 100   # % conversion
    Y_H2  = F_H2 / (4 * F_CH4_in) * 100            # % yield (max 4 mol H2/mol CH4)

    return {
        "W":     sol.t,
        "F_CH4": F_CH4,  "F_H2O": F_H2O,
        "F_CO":  F_CO,   "F_CO2": F_CO2, "F_H2": F_H2,
        "X_CH4": X_CH4,  "Y_H2": Y_H2,
        "T_K":   T_K,    "P_bar": P_bar, "SC": SC_ratio,
    }


if __name__ == "__main__":
    result = run_pfr(T_K=1073.15, P_bar=1.0, SC_ratio=3.0)
    print(f"CH4 Conversion  : {result['X_CH4'][-1]:.2f} %")
    print(f"H2 Yield        : {result['Y_H2'][-1]:.2f} %")
    print(f"H2 produced     : {result['F_H2'][-1]*1e6:.4f} μmol/s")
