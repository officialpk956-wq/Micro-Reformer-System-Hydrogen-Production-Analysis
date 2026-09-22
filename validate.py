"""Quick science validity check script."""
import sys, os
sys.path.insert(0, r'd:\sroy\micro_reformer')
from kinetics_model import equilibrium_constants, run_pfr
from mass_energy_balance import MicroReformerBalance

print('='*60)
print('  SCIENCE VALIDITY CHECK')
print('='*60)

# 1. K1 (SMR, endothermic) must increase with T
K600 = equilibrium_constants(873.15)['K1']
K800 = equilibrium_constants(1073.15)['K1']
K900 = equilibrium_constants(1173.15)['K1']
assert K600 < K800 < K900
print(f"  [PASS] K1 increases with T: {K600:.4f} -> {K800:.2f} -> {K900:.1f} bar2")

# 2. K2 (WGS, exothermic) must decrease with T
K2_600 = equilibrium_constants(873.15)['K2']
K2_800 = equilibrium_constants(1073.15)['K2']
assert K2_600 > K2_800
print(f"  [PASS] K2 decreases with T: {K2_600:.4f} -> {K2_800:.4f}")

# 3. Higher T -> higher conversion
r_low  = run_pfr(T_K=873.15,  P_bar=1.0, SC_ratio=3.0, W_cat=0.5)
r_high = run_pfr(T_K=1073.15, P_bar=1.0, SC_ratio=3.0, W_cat=0.5)
x_low  = r_low['X_CH4'][-1]
x_high = r_high['X_CH4'][-1]
assert x_high > x_low
print(f"  [PASS] X_CH4: 600C={x_low:.2f}% < 800C={x_high:.2f}%")

# 4. Higher S/C -> higher conversion
r_sc2 = run_pfr(T_K=1073.15, P_bar=1.0, SC_ratio=2.0, W_cat=0.5)
r_sc4 = run_pfr(T_K=1073.15, P_bar=1.0, SC_ratio=4.0, W_cat=0.5)
x_sc2 = r_sc2['X_CH4'][-1]
x_sc4 = r_sc4['X_CH4'][-1]
assert x_sc4 >= x_sc2
print(f"  [PASS] X_CH4: S/C=2={x_sc2:.2f}% <= S/C=4={x_sc4:.2f}%")

# 5. Higher P -> lower H2 yield (Le Chatelier)
r_p1  = run_pfr(T_K=1073.15, P_bar=1.0,  SC_ratio=3.0, W_cat=0.5)
r_p10 = run_pfr(T_K=1073.15, P_bar=10.0, SC_ratio=3.0, W_cat=0.5)
y_p1  = r_p1['Y_H2'][-1]
y_p10 = r_p10['Y_H2'][-1]
assert y_p1 > y_p10
print(f"  [PASS] Y_H2: P=1bar={y_p1:.2f}% > P=10bar={y_p10:.2f}% (Le Chatelier OK)")

# 6. Atom balance
bal = MicroReformerBalance(T_K=1073.15, P_bar=1.0, SC_ratio=3.0, F_CH4_in=1e-4)
result = bal.run()
atm = bal.atom_balance_check(result)
assert atm['C_err_%'] < 0.01 and atm['H_err_%'] < 0.01 and atm['O_err_%'] < 0.01
print(f"  [PASS] Atom balance C={atm['C_err_%']:.6f}% H={atm['H_err_%']:.6f}% O={atm['O_err_%']:.6f}%")

# 7. Yield and efficiency in physical range
assert 0 <= result.Y_H2 <= 100
assert 0 < result.eta_thermal < 100
print(f"  [PASS] Y_H2={result.Y_H2:.2f}%, eta={result.eta_thermal:.2f}% (in physical range)")

# 8. HTML report size
html_size = os.path.getsize(r'd:\sroy\micro_reformer\output_plots\micro_reformer_report.html')
assert html_size > 1_000_000
print(f"  [PASS] HTML report: {html_size/1e6:.2f} MB (images embedded)")

# 9. All 12 PNGs exist
import glob
pngs = glob.glob(r'd:\sroy\micro_reformer\output_plots\fig*.png')
assert len(pngs) == 12, f"Expected 12 PNGs, found {len(pngs)}"
print(f"  [PASS] All 12 figure PNGs present")

# 10. All 5 CSVs exist
csvs = glob.glob(r'd:\sroy\micro_reformer\output_plots\study_*.csv')
assert len(csvs) == 5
print(f"  [PASS] All 5 parametric study CSVs present")

print()
print("  ALL 10 SCIENCE & FILE CHECKS PASSED!")
print('='*60)
