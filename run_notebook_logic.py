import numpy as np
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

from kinetics_model import run_pfr
from mass_energy_balance import MicroReformerBalance

plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({'font.size': 11, 'figure.dpi': 100})

print("="*60)
print("1. RUNNING TEMPERATURE SWEEP (500°C - 900°C)...")
print("="*60)

temps_C = np.linspace(500, 900, 15)
temps_K = temps_C + 273.15
conversions = []
yields = []
selectivities = []

for T in temps_K:
    res = run_pfr(T_K=T, P_bar=1.0, SC_ratio=3.0, W_cat=0.5)
    conversions.append(res['X_CH4'][-1])
    yields.append(res['Y_H2'][-1])

fig, ax1 = plt.subplots(figsize=(8, 5))

# Plot 1: Conversion and Yield
ax1.plot(temps_C, conversions, label='CH$_4$ Conversion (%)', color='#ef4444', marker='o', lw=2)
ax1.plot(temps_C, yields, label='H$_2$ Yield (%)', color='#10b981', marker='s', lw=2)
ax1.set_title('Methane Conversion & Hydrogen Yield vs Temperature')
ax1.set_xlabel('Temperature [°C]')
ax1.set_ylabel('Percentage [%]')
ax1.legend()

plt.tight_layout()
plt.savefig(r'd:\sroy\micro_reformer\notebook_results.png')
print("-> Temperature sweep complete. Saved plot to notebook_results.png")

print("\n" + "="*60)
print("2. RUNNING MASS & ENERGY BALANCE (800°C)...")
print("="*60)

T_opt_K = 800 + 273.15
balance = MicroReformerBalance(T_K=T_opt_K, P_bar=1.0, SC_ratio=3.0, F_CH4_in=1e-4)
result = balance.run()

print(f"Operating Temp: 800 °C")
print(f"Steam/Carbon:   3.0")
print("-" * 40)
print(f"CH4 Conversion: {result.X_CH4:.2f} %")
print(f"H2 Yield:       {result.Y_H2:.2f} %")
print(f"Thermal Duty:   {result.Q_duty*1000:.2f} W  (Endothermic)")
print(f"Thermal Eff:    {result.eta_thermal:.2f} %")
print("-" * 40)

atm = balance.atom_balance_check(result)
print(f"Atom Balance Errors: C: {atm['C_err_%']:.6f}%, H: {atm['H_err_%']:.6f}%, O: {atm['O_err_%']:.6f}%")
if atm['C_err_%'] < 0.01:
    print("✅ Conservation of mass verified.")
