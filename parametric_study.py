"""
=============================================================================
  PARAMETRIC STUDY — MICRO-REFORMER PERFORMANCE
  
  Studies the effect of:
    1. Temperature          (600 – 900 °C)
    2. Pressure             (1 – 10 bar)
    3. Steam-to-Carbon (S/C) ratio  (2 – 5)
    4. GHSV                 (1000 – 50000 h⁻¹)
  
  on:
    • CH4 Conversion (%)
    • H2 Yield (%)
    • CO Selectivity (%)
    • H2 Production Rate (μmol/s)
    • Net Heat Duty (W)
=============================================================================
"""

import numpy as np
import pandas as pd
from kinetics_model import run_pfr, equilibrium_constants


# ─────────────────────────────────────────────────
#  HELPER METRICS FROM PFR RESULT
# ─────────────────────────────────────────────────
def extract_metrics(res: dict) -> dict:
    """Extract key performance metrics from PFR result (outlet values)."""
    F_CH4   = res["F_CH4"][-1]
    F_H2O   = res["F_H2O"][-1]
    F_CO    = res["F_CO"][-1]
    F_CO2   = res["F_CO2"][-1]
    F_H2    = res["F_H2"][-1]
    F_CH4_0 = res["F_CH4"][0]

    X_CH4   = res["X_CH4"][-1]
    Y_H2    = res["Y_H2"][-1]

    # CO selectivity: CO / (CO + CO2)
    denom_co = F_CO + F_CO2
    S_CO     = F_CO / max(denom_co, 1e-20) * 100.0

    # H2/CO ratio (syngas quality)
    h2_co_ratio = F_H2 / max(F_CO, 1e-20)

    return {
        "X_CH4":       X_CH4,
        "Y_H2":        Y_H2,
        "S_CO":        S_CO,
        "H2_CO_ratio": h2_co_ratio,
        "F_H2_umol":   F_H2 * 1e6,
        "F_CO_umol":   F_CO * 1e6,
    }


# ─────────────────────────────────────────────────
#  STUDY 1: EFFECT OF TEMPERATURE
# ─────────────────────────────────────────────────
def study_temperature(T_range_C: np.ndarray = None,
                      P_bar: float = 1.0,
                      SC_ratio: float = 3.0,
                      W_cat: float = 0.5) -> pd.DataFrame:
    """Effect of temperature at fixed P and S/C."""
    if T_range_C is None:
        T_range_C = np.arange(500, 951, 25)

    rows = []
    for T_C in T_range_C:
        T_K = T_C + 273.15
        res = run_pfr(T_K=T_K, P_bar=P_bar, SC_ratio=SC_ratio, W_cat=W_cat)
        m   = extract_metrics(res)

        # Also get equilibrium constants
        K   = equilibrium_constants(T_K)
        m.update({"T_C": T_C, "K1": K["K1"], "K2": K["K2"]})
        rows.append(m)

    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────
#  STUDY 2: EFFECT OF PRESSURE
# ─────────────────────────────────────────────────
def study_pressure(P_range: np.ndarray = None,
                   T_C: float = 800.0,
                   SC_ratio: float = 3.0,
                   W_cat: float = 0.5) -> pd.DataFrame:
    """
    Effect of pressure at fixed T and S/C.
    Le Chatelier: higher P disfavors SMR (moles increase), favors WGS.
    """
    if P_range is None:
        P_range = np.array([1, 2, 3, 5, 7, 10, 15, 20])

    rows = []
    for P in P_range:
        res = run_pfr(T_K=T_C+273.15, P_bar=P, SC_ratio=SC_ratio, W_cat=W_cat)
        m   = extract_metrics(res)
        m["P_bar"] = P
        rows.append(m)

    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────
#  STUDY 3: EFFECT OF STEAM-TO-CARBON RATIO
# ─────────────────────────────────────────────────
def study_sc_ratio(SC_range: np.ndarray = None,
                   T_C: float = 800.0,
                   P_bar: float = 1.0,
                   W_cat: float = 0.5) -> pd.DataFrame:
    """
    Effect of S/C ratio at fixed T and P.
    Higher S/C → more H2O → shifts equilibrium toward H2 production.
    Also mitigates carbon deposition.
    """
    if SC_range is None:
        SC_range = np.arange(1.5, 5.5, 0.25)

    rows = []
    for SC in SC_range:
        res = run_pfr(T_K=T_C+273.15, P_bar=P_bar, SC_ratio=SC, W_cat=W_cat)
        m   = extract_metrics(res)
        m["SC"] = SC
        rows.append(m)

    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────
#  STUDY 4: EFFECT OF GHSV
# ─────────────────────────────────────────────────
def study_ghsv(GHSV_range: np.ndarray = None,
               T_C: float = 800.0,
               P_bar: float = 1.0,
               SC_ratio: float = 3.0,
               rho_cat: float = 1200.0,     # catalyst density [kg/m³]
               Vol_cat: float = 1e-6) -> pd.DataFrame:       # 1 cm³
    """
    Effect of Gas Hourly Space Velocity (GHSV) [h⁻¹].
    Higher GHSV → shorter contact time → lower conversion.
    
    W_cat [kg] = rho_cat × V_cat  (fixed volume reactor)
    GHSV [h⁻¹] = Q_feed_NTP [m³/h] / V_cat [m³]
    """
    if GHSV_range is None:
        GHSV_range = np.logspace(3, 5, 30)   # 1000 – 100000 h⁻¹

    rows = []
    W_cat = rho_cat * Vol_cat   # [kg]

    for GHSV in GHSV_range:
        # Convert GHSV to molar feed rate
        # Q_feed [m³/s] = GHSV [h⁻¹] × V_cat [m³] / 3600
        Q_feed_NTP = GHSV * Vol_cat / 3600.0         # m³/s at NTP
        F_total_in = Q_feed_NTP / 22.4e-3             # mol/s (ideal gas, 22.4 L/mol)
        F_CH4_in   = F_total_in / (1 + SC_ratio)

        res = run_pfr(T_K=T_C+273.15, P_bar=P_bar, SC_ratio=SC_ratio,
                      F_CH4_in=F_CH4_in, W_cat=W_cat)
        m   = extract_metrics(res)
        m["GHSV"]       = GHSV
        m["contact_ms"]  = 3600 / GHSV * 1000        # ms
        rows.append(m)

    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────
#  COMBINED 2-D PARAMETRIC MAP  (T vs SC)
# ─────────────────────────────────────────────────
def study_T_SC_map(T_range_C: np.ndarray = None,
                   SC_range:  np.ndarray = None,
                   P_bar: float = 1.0,
                   W_cat: float = 0.5) -> pd.DataFrame:
    """2D parametric map: Temperature × S/C → H2 yield heatmap."""
    if T_range_C is None:
        T_range_C = np.arange(600, 901, 50)
    if SC_range is None:
        SC_range  = np.arange(2, 5.5, 0.5)

    rows = []
    for T_C in T_range_C:
        for SC in SC_range:
            res = run_pfr(T_K=T_C+273.15, P_bar=P_bar, SC_ratio=SC, W_cat=W_cat)
            m   = extract_metrics(res)
            m.update({"T_C": T_C, "SC": SC})
            rows.append(m)

    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────
#  AXIAL PROFILE STUDY
# ─────────────────────────────────────────────────
def axial_profile_study(T_C: float = 800,
                         P_bar: float = 1.0,
                         SC_ratio: float = 3.0,
                         W_cat: float = 1.0) -> dict:
    """
    Detailed axial profiles along reactor length for a single condition.
    Returns species flow rates, conversion, and yield vs. W (catalyst mass).
    """
    res = run_pfr(T_K=T_C+273.15, P_bar=P_bar, SC_ratio=SC_ratio, W_cat=W_cat)

    F_total = (res["F_CH4"] + res["F_H2O"] + res["F_CO"]
               + res["F_CO2"] + res["F_H2"])

    return {
        "W":       res["W"],
        "F_CH4":   res["F_CH4"] * 1e6,
        "F_H2O":   res["F_H2O"] * 1e6,
        "F_CO":    res["F_CO"]  * 1e6,
        "F_CO2":   res["F_CO2"] * 1e6,
        "F_H2":    res["F_H2"]  * 1e6,
        "X_CH4":   res["X_CH4"],
        "Y_H2":    res["Y_H2"],
        "y_CH4":   res["F_CH4"] / F_total * 100,
        "y_H2":    res["F_H2"]  / F_total * 100,
        "y_CO":    res["F_CO"]  / F_total * 100,
        "y_CO2":   res["F_CO2"] / F_total * 100,
    }


if __name__ == "__main__":
    print("Running parametric studies...")
    df_T  = study_temperature()
    df_P  = study_pressure()
    df_SC = study_sc_ratio()
    df_GH = study_ghsv()
    print(f"Temperature study  : {len(df_T)} points")
    print(f"Pressure study     : {len(df_P)} points")
    print(f"S/C ratio study    : {len(df_SC)} points")
    print(f"GHSV study         : {len(df_GH)} points")
    print("\nSample at T=800°C, P=1 bar, S/C=3:")
    res = run_pfr(T_K=1073.15, P_bar=1.0, SC_ratio=3.0, W_cat=0.5)
    from kinetics_model import equilibrium_constants
    print(f"  X_CH4 = {res['X_CH4'][-1]:.2f} %")
    print(f"  Y_H2  = {res['Y_H2'][-1]:.2f} %")
