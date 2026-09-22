"""
=============================================================================
  MAIN RUNNER — MICRO-REFORMER ASSIGNMENT
  
  Executes all models and generates the complete report.
  Run this file to reproduce all results.
  
  Author   : [Your Name]
  Course   : [Course Name]
  Institute: [Institute Name]
  Date     : September 2026
=============================================================================
"""

import os, sys, time
import numpy as np
import pandas as pd

# Ensure module path
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 65)
print("  MICRO-REFORMER HYDROGEN PRODUCTION — COMPLETE ANALYSIS")
print("=" * 65)

# ─────────────────────────────────────────────────────────
#  1. KINETICS MODEL
# ─────────────────────────────────────────────────────────
print("\n[1/6] Running Kinetics Model (PFR mole balance)...")
from kinetics_model import run_pfr, equilibrium_constants

# Base case
base = run_pfr(T_K=1073.15, P_bar=1.0, SC_ratio=3.0,
               F_CH4_in=1e-4, W_cat=0.5)
print(f"      Base case (800°C, 1 bar, S/C=3):")
print(f"        CH4 Conversion = {base['X_CH4'][-1]:.2f} %")
print(f"        H2  Yield      = {base['Y_H2'][-1]:.2f} %")

# ─────────────────────────────────────────────────────────
#  2. MASS & ENERGY BALANCE
# ─────────────────────────────────────────────────────────
print("\n[2/6] Computing Mass & Energy Balances...")
from mass_energy_balance import (MicroReformerBalance,
                                  parametric_balance_table)

bal = MicroReformerBalance(T_K=1073.15, P_bar=1.0,
                            SC_ratio=3.0, F_CH4_in=1e-4)
result = bal.run()
bal.print_summary(result)

# Parametric balance table
balance_table = parametric_balance_table(
    temperatures=np.arange(600, 901, 50) + 273.15,
    SC_ratios=[2.0, 3.0, 4.0],
    F_CH4=1e-4
)
print(f"\n      Balance table: {len(balance_table)} conditions computed.")

# ─────────────────────────────────────────────────────────
#  3. PARAMETRIC STUDIES
# ─────────────────────────────────────────────────────────
print("\n[3/6] Running Parametric Studies...")
from parametric_study import (study_temperature, study_pressure,
                               study_sc_ratio, study_ghsv,
                               study_T_SC_map, axial_profile_study)

t0 = time.time()
df_T   = study_temperature(T_range_C=np.arange(500, 951, 25), W_cat=0.5)
df_P   = study_pressure(P_range=np.array([1,2,3,5,7,10,15,20]), W_cat=0.5)
df_SC  = study_sc_ratio(SC_range=np.arange(1.5, 5.5, 0.25), W_cat=0.5)
df_GH  = study_ghsv(GHSV_range=np.logspace(3, 5, 25))
df_map = study_T_SC_map(T_range_C=np.arange(600,901,50),
                         SC_range=np.arange(2, 5.5, 0.5), W_cat=0.5)
axial  = axial_profile_study(T_C=800, P_bar=1.0, SC_ratio=3.0, W_cat=0.8)

print(f"      Parametric studies done in {time.time()-t0:.1f}s")
print(f"        Temperature : {len(df_T)} pts  | Pressure : {len(df_P)} pts")
print(f"        S/C Ratio   : {len(df_SC)} pts  | GHSV     : {len(df_GH)} pts")
print(f"        2D Map      : {len(df_map)} pts")

# Save DataFrames to CSV
outdir = os.path.join(os.path.dirname(__file__), "output_plots")
os.makedirs(outdir, exist_ok=True)
df_T.to_csv(os.path.join(outdir, "study_temperature.csv"), index=False)
df_P.to_csv(os.path.join(outdir, "study_pressure.csv"),    index=False)
df_SC.to_csv(os.path.join(outdir, "study_sc_ratio.csv"),   index=False)
df_GH.to_csv(os.path.join(outdir, "study_ghsv.csv"),       index=False)
df_map.to_csv(os.path.join(outdir, "study_T_SC_map.csv"),  index=False)
print("      CSVs saved to output_plots/")

# ─────────────────────────────────────────────────────────
#  4. CFD THERMAL MODEL
# ─────────────────────────────────────────────────────────
print("\n[4/6] Running 2D CFD Thermal Model...")
from cfd_thermal_model import (ChannelGeometry, FluidProperties,
                                BoundaryConditions, MicrochannelThermal2D,
                                pressure_drop)

geom  = ChannelGeometry()
fluid = FluidProperties()
bc    = BoundaryConditions(T_wall=1073.15, u_mean=0.5)

solver     = MicrochannelThermal2D(geom, fluid, bc, Nx=150, Nr=25)
cfd_result = solver.solve()
dp         = pressure_drop(geom, fluid, bc)

print(f"      Re = {cfd_result['Re']:.1f}  "
      f"({'Laminar' if cfd_result['Re']<2300 else 'Turbulent'})")
print(f"      Pr = {cfd_result['Pr']:.3f}")
print(f"      Nu_avg = {cfd_result['Nu_avg']:.2f}")
print(f"      h_avg  = {cfd_result['h_avg']:.1f} W/(m²·K)")
print(f"      T_cl outlet = {cfd_result['T_cl'][-1]-273.15:.1f} °C")
print(f"      Q_total = {cfd_result['Q_total_W']:.2f} W")
print(f"      ΔP = {dp['dP_total']:.2f} Pa ({dp['dP_bar']*1000:.3f} mbar)")

# ─────────────────────────────────────────────────────────
#  5. PERFORMANCE SUMMARY & RADAR DATA
# ─────────────────────────────────────────────────────────
print("\n[5/6] Computing Performance Summary...")

# Radar chart data: 5 metrics normalized to 0-100
def make_radar(df_T_local, T_C, label):
    row = df_T_local[abs(df_T_local["T_C"] - T_C) < 15].iloc[0]
    x_ch4 = row["X_CH4"]
    y_h2  = row["Y_H2"]
    h2co  = min(row["H2_CO_ratio"] / 10 * 100, 100)
    eta   = 75.0 - (T_C - 700) * 0.05       # rough efficiency estimate
    co_inv= 100 - row["S_CO"]               # lower CO selectivity = better
    return [x_ch4, y_h2, h2co, eta, co_inv]

radar_data = {
    "T = 600 °C": make_radar(df_T, 600, "600"),
    "T = 750 °C": make_radar(df_T, 750, "750"),
    "T = 900 °C": make_radar(df_T, 900, "900"),
}

print("      Radar data prepared for 3 temperature conditions.")

# ─────────────────────────────────────────────────────────
#  6. GENERATE ALL PLOTS
# ─────────────────────────────────────────────────────────
print("\n[6/6] Generating all plots and figures...")
from visualizer import generate_all_plots

all_data = {
    "axial_profile": axial,
    "df_T":          df_T,
    "df_P":          df_P,
    "df_SC":         df_SC,
    "df_GH":         df_GH,
    "df_map":        df_map,
    "cfd_result":    cfd_result,
    "geom":          geom,
    "balance_table": balance_table,
    "radar_data":    radar_data,
}

plot_paths = generate_all_plots(all_data)

# ─────────────────────────────────────────────────────────
#  FINAL SUMMARY TABLE
# ─────────────────────────────────────────────────────────
print("\n" + "="*65)
print("  FINAL RESULTS SUMMARY")
print("="*65)
print(f"\n  {'Condition':<30} {'X_CH4 %':>10} {'Y_H2 %':>10} {'H2 μmol/s':>12}")
print("  " + "-"*62)
for row in balance_table:
    cond = f"T={row['T_C']:.0f}°C, S/C={row['SC']}"
    print(f"  {cond:<30} {row['X_CH4']:>10.2f} {row['Y_H2']:>10.2f} "
          f"{row['F_H2_umol_s']:>12.4f}")

print("\n" + "="*65)
print(f"  ✓ {len(plot_paths)} figures generated in micro_reformer/output_plots/")
print("  ✓ Parametric data saved as CSVs")
print("  ✓ Analysis complete!")
print("="*65)
