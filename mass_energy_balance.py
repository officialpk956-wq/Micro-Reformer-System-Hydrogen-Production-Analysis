"""
=============================================================================
  MASS & ENERGY BALANCE — MICRO-REFORMER SYSTEM
  
  Performs:
  1. Elemental (mass) balance — C, H, O atoms
  2. Mole balance — species in/out
  3. Energy balance — heat duty, thermal requirements
  4. H2 production rate and thermal efficiency
=============================================================================
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List
from kinetics_model import (cp_shomate, enthalpy_reaction_T,
                             equilibrium_constants, R_kJ)


# ─────────────────────────────────────────────────
#  DATA CLASSES
# ─────────────────────────────────────────────────
@dataclass
class StreamData:
    name: str
    T_K: float               # Temperature [K]
    P_bar: float             # Pressure [bar]
    F: Dict[str, float]      # Molar flows [mol/s]

    @property
    def F_total(self) -> float:
        return sum(self.F.values())

    @property
    def composition(self) -> Dict[str, float]:
        total = max(self.F_total, 1e-15)
        return {sp: f / total for sp, f in self.F.items()}

    def mass_flow(self) -> float:
        """Total mass flow [g/s]"""
        MW = {"CH4": 16.04, "H2O": 18.02, "CO": 28.01,
              "CO2": 44.01, "H2":  2.016, "N2": 28.01}
        return sum(f * MW.get(sp, 28) for sp, f in self.F.items())


@dataclass
class MassEnergyResult:
    """Stores all balance outputs."""
    inlet: StreamData
    outlet: StreamData
    Q_duty: float            # Heat duty [W]
    eta_thermal: float       # Thermal efficiency [%]
    X_CH4: float             # CH4 conversion [%]
    Y_H2: float              # H2 yield [%]
    H2_production: float     # H2 production [mol/s]
    notes: List[str] = field(default_factory=list)


# ─────────────────────────────────────────────────
#  ENTHALPY CALCULATIONS
# ─────────────────────────────────────────────────
SPECIES_LIST = ["CH4", "H2O", "CO", "CO2", "H2"]

# Standard enthalpy of formation at 298.15 K [kJ/mol]
H_f298 = {
    "CH4": -74.81, "H2O": -241.82, "CO": -110.53,
    "CO2": -393.51, "H2":   0.00,  "N2":    0.00,
}

def enthalpy_stream(stream: StreamData, T_ref: float = 298.15) -> float:
    """
    Total stream enthalpy H = Σ Fi × [H_f,i° + ∫Cp dT]  [kW]
    Numerical integration from T_ref to T_stream.
    """
    total_H = 0.0
    for sp, F_i in stream.F.items():
        if F_i <= 0 or sp not in SHOMATE_SPECIES:
            continue
        # Numerical integration of Cp
        T_points = np.linspace(T_ref, stream.T_K, 100)
        Cp_vals  = [cp_shomate(sp, T) for T in T_points]
        integral = np.trapezoid(Cp_vals, T_points)        # J/mol
        H_i = H_f298.get(sp, 0) * 1000 + integral       # J/mol
        total_H += F_i * H_i                              # J/s = W

    return total_H / 1000.0   # kW

SHOMATE_SPECIES = set(["CH4", "H2O", "CO", "CO2", "H2"])


def heat_duty_reactor(T_K: float, F_CH4_reacted: float,
                      F_CO_prod: float, F_CO2_prod: float) -> float:
    """
    Net heat duty [kW] from reaction enthalpies at temperature T.
    Positive = heat INPUT needed (endothermic net).
    """
    # Extent of each reaction (from stoichiometry)
    xi3    = F_CO2_prod - 0.0              # rough estimate
    xi1    = F_CO_prod
    xi2    = F_CO2_prod - xi3
    xi_tot = xi1 + xi3   # ≈ F_CH4_reacted for checking

    dH1 = enthalpy_reaction_T(1, T_K) * 1000   # J/mol
    dH2 = enthalpy_reaction_T(2, T_K) * 1000
    dH3 = enthalpy_reaction_T(3, T_K) * 1000

    Q = xi1 * dH1 + xi2 * dH2 + xi3 * dH3     # J/s = W
    return Q / 1000.0                            # kW


# ─────────────────────────────────────────────────
#  MAIN BALANCE CLASS
# ─────────────────────────────────────────────────
class MicroReformerBalance:
    """
    Complete mass & energy balance for a micro-reformer channel.
    """

    def __init__(self, T_K: float = 1073.15, P_bar: float = 1.0,
                 SC_ratio: float = 3.0, F_CH4_in: float = 1e-4,
                 X_CH4_target: float = None):
        """
        Parameters
        ----------
        T_K          : Reactor temperature [K]
        P_bar        : Reactor pressure [bar]
        SC_ratio     : Steam-to-carbon molar ratio
        F_CH4_in     : CH4 inlet molar flow [mol/s]
        X_CH4_target : If given, use this conversion; else compute from kinetics
        """
        self.T_K      = T_K
        self.P_bar    = P_bar
        self.SC_ratio = SC_ratio
        self.F_CH4_in = F_CH4_in

        # Use equilibrium conversion as upper bound
        if X_CH4_target is None:
            self.X_CH4 = self._equilibrium_conversion() / 100.0
        else:
            self.X_CH4 = X_CH4_target / 100.0

    def _equilibrium_conversion(self) -> float:
        """
        Estimate equilibrium CH4 conversion using K1 and K3.
        Simple iterative Newton approach.
        """
        K = equilibrium_constants(self.T_K)
        K1, K2 = K["K1"], K["K2"]
        SC     = self.SC_ratio
        P      = self.P_bar

        # Initial guess
        xi = 0.8
        for _ in range(200):
            y_CH4 = max(1 - xi,          1e-9)
            y_H2O = max(SC - xi - xi,    1e-9)
            y_CO  = max(xi,              1e-9)
            y_H2  = max(3*xi,            1e-9)
            N     = y_CH4 + y_H2O + y_CO + y_H2
            # Mole fractions (normalize)
            y_CH4 /= N; y_H2O /= N; y_CO /= N; y_H2 /= N

            Qp = (y_CO * y_H2**3) / (y_CH4 * y_H2O) * P**2
            f  = Qp - K1
            dfdxi = 0.01
            xi = min(max(xi - f * 0.001, 0.01), 0.98)

        return xi * 100.0

    # --------------------------------------------------
    def run(self) -> MassEnergyResult:
        """Perform complete mass & energy balance."""
        F0   = self.F_CH4_in
        SC   = self.SC_ratio
        X    = self.X_CH4

        # ── INLET STREAM ──
        F_CH4_0 = F0
        F_H2O_0 = SC * F0
        inlet = StreamData(
            name="Inlet Feed", T_K=298.15, P_bar=self.P_bar,
            F={"CH4": F_CH4_0, "H2O": F_H2O_0,
               "CO": 0.0, "CO2": 0.0, "H2": 0.0}
        )

        # ── REACTION EXTENTS (simplified: assume R1 and R2 dominant) ──
        # CH4 reacted
        dF_CH4 = X * F0

        # From equilibrium selectivity: fraction going via R1 vs R3
        K      = equilibrium_constants(self.T_K)
        # alpha = fraction of reacted CH4 going via R1
        alpha  = K["K1"] / (K["K1"] + K["K3"] + 1e-30)
        alpha  = np.clip(alpha, 0.3, 0.7)

        xi1    = alpha * dF_CH4          # extent of R1
        xi3    = (1 - alpha) * dF_CH4   # extent of R3

        # WGS — fraction of CO shifted
        K2     = K["K2"]
        f_wgs  = K2 / (1 + K2)          # equilibrium fraction shifted
        xi2    = f_wgs * xi1             # extent of R2

        # ── OUTLET MOLAR FLOWS ──
        F_CH4_out = F0 - xi1 - xi3
        F_H2O_out = F_H2O_0 - xi1 - xi2 - 2*xi3
        F_CO_out  = xi1 - xi2
        F_CO2_out = xi2 + xi3
        F_H2_out  = 3*xi1 + xi2 + 4*xi3

        # Clip negatives
        F_CH4_out = max(F_CH4_out, 0)
        F_H2O_out = max(F_H2O_out, 0)
        F_CO_out  = max(F_CO_out,  0)
        F_CO2_out = max(F_CO2_out, 0)

        outlet = StreamData(
            name="Outlet Product", T_K=self.T_K, P_bar=self.P_bar,
            F={"CH4": F_CH4_out, "H2O": F_H2O_out,
               "CO":  F_CO_out,  "CO2": F_CO2_out, "H2": F_H2_out}
        )

        # ── PERFORMANCE METRICS ──
        X_CH4_pct = (F0 - F_CH4_out) / F0 * 100.0
        Y_H2_pct  = F_H2_out / (4 * F0) * 100.0

        # ── ENERGY BALANCE ──
        # Sensible heat to bring feed from 298 K to T_K
        Q_sensible = enthalpy_stream(
            StreamData("feed_hot", T_K=self.T_K, P_bar=self.P_bar,
                       F=inlet.F), T_ref=298.15
        ) - enthalpy_stream(inlet, T_ref=298.15)

        # Reaction heat (net, at T)
        dH_net = (xi1 * enthalpy_reaction_T(1, self.T_K)
                + xi2 * enthalpy_reaction_T(2, self.T_K)
                + xi3 * enthalpy_reaction_T(3, self.T_K))   # kJ/s = kW

        Q_rxn  = dH_net            # kW (positive = endothermic need)
        Q_duty = Q_sensible + Q_rxn

        # Thermal efficiency: H2 energy out / total heat in
        LHV_H2    = 241.82    # kJ/mol (LHV of H2)
        E_H2_out  = F_H2_out * LHV_H2   # kW
        E_CH4_in  = F0 * 802.3          # kW (LHV of CH4 = 802.3 kJ/mol)
        eta       = E_H2_out / (E_CH4_in + max(Q_duty, 0)) * 100.0

        return MassEnergyResult(
            inlet=inlet, outlet=outlet,
            Q_duty=Q_duty, eta_thermal=eta,
            X_CH4=X_CH4_pct, Y_H2=Y_H2_pct,
            H2_production=F_H2_out,
            notes=[
                f"SMR extent xi1 = {xi1*1e6:.2f} μmol/s",
                f"WGS extent xi2 = {xi2*1e6:.2f} μmol/s",
                f"DR  extent xi3 = {xi3*1e6:.2f} μmol/s",
            ]
        )

    # --------------------------------------------------
    def atom_balance_check(self, result: MassEnergyResult) -> Dict:
        """
        Elemental balance: verify C, H, O atoms are conserved.
        Returns % error for each element.
        """
        inp  = result.inlet.F
        out  = result.outlet.F

        C_in  = inp.get("CH4", 0)
        C_out = out.get("CH4", 0) + out.get("CO", 0) + out.get("CO2", 0)

        H_in  = 4*inp.get("CH4", 0) + 2*inp.get("H2O", 0)
        H_out = (4*out.get("CH4", 0) + 2*out.get("H2O", 0)
                + 2*out.get("H2", 0))

        O_in  = inp.get("H2O", 0)
        O_out = (out.get("H2O", 0) + out.get("CO", 0)
                + 2*out.get("CO2", 0))

        def pct_err(a, b):
            return abs(a - b) / max(abs(a), 1e-15) * 100

        return {
            "C_in":  C_in,  "C_out": C_out,  "C_err_%": pct_err(C_in, C_out),
            "H_in":  H_in,  "H_out": H_out,  "H_err_%": pct_err(H_in, H_out),
            "O_in":  O_in,  "O_out": O_out,  "O_err_%": pct_err(O_in, O_out),
        }

    def print_summary(self, result: MassEnergyResult):
        """Pretty-print balance results."""
        print("\n" + "="*60)
        print("  MICRO-REFORMER MASS & ENERGY BALANCE")
        print("="*60)
        print(f"  Operating Conditions:")
        print(f"    Temperature   : {self.T_K - 273.15:.0f} °C")
        print(f"    Pressure      : {self.P_bar:.1f} bar")
        print(f"    S/C Ratio     : {self.SC_ratio:.1f}")
        print(f"    CH4 Feed Flow : {self.F_CH4_in*1e6:.2f} μmol/s")
        print("-"*60)
        print(f"\n  INLET (Feed Stream):")
        for sp, F in result.inlet.F.items():
            if F > 1e-12:
                print(f"    {sp:<6}: {F*1e6:>10.4f} μmol/s")
        print(f"    {'Total':<6}: {result.inlet.F_total*1e6:>10.4f} μmol/s")
        print(f"\n  OUTLET (Product Stream):")
        for sp, F in result.outlet.F.items():
            if F > 1e-12:
                print(f"    {sp:<6}: {F*1e6:>10.4f} μmol/s")
        print(f"    {'Total':<6}: {result.outlet.F_total*1e6:>10.4f} μmol/s")
        print("\n  REACTION NOTES:")
        for note in result.notes:
            print(f"    • {note}")
        print("\n  PERFORMANCE METRICS:")
        print(f"    CH4 Conversion     : {result.X_CH4:>8.2f} %")
        print(f"    H2 Yield           : {result.Y_H2:>8.2f} %")
        print(f"    H2 Production      : {result.H2_production*1e6:>8.4f} μmol/s")
        print(f"    Net Heat Duty      : {result.Q_duty*1000:>8.4f} W")
        print(f"    Thermal Efficiency : {result.eta_thermal:>8.2f} %")

        atm = self.atom_balance_check(result)
        print("\n  ATOM BALANCE CHECK:")
        print(f"    Carbon   error : {atm['C_err_%']:.4f} %")
        print(f"    Hydrogen error : {atm['H_err_%']:.4f} %")
        print(f"    Oxygen   error : {atm['O_err_%']:.4f} %")
        print("="*60)


# ─────────────────────────────────────────────────
#  PARAMETRIC MASS BALANCE TABLE
# ─────────────────────────────────────────────────
def parametric_balance_table(temperatures: np.ndarray = None,
                             SC_ratios: np.ndarray = None,
                             F_CH4: float = 1e-4) -> list:
    """
    Run balance at multiple conditions and return table of results.
    """
    if temperatures is None:
        temperatures = np.arange(600, 901, 50) + 273.15
    if SC_ratios is None:
        SC_ratios = [2.0, 3.0, 4.0]

    rows = []
    for T in temperatures:
        for SC in SC_ratios:
            bal = MicroReformerBalance(T_K=T, P_bar=1.0,
                                       SC_ratio=SC, F_CH4_in=F_CH4)
            res = bal.run()
            rows.append({
                "T_C":    T - 273.15,
                "SC":     SC,
                "X_CH4":  res.X_CH4,
                "Y_H2":   res.Y_H2,
                "F_H2_umol_s": res.H2_production * 1e6,
                "Q_duty_W":    res.Q_duty * 1000,
                "eta_%":       res.eta_thermal,
            })
    return rows


if __name__ == "__main__":
    bal = MicroReformerBalance(T_K=1073.15, P_bar=1.0,
                               SC_ratio=3.0, F_CH4_in=1e-4)
    result = bal.run()
    bal.print_summary(result)
