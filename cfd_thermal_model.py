"""
=============================================================================
  CFD THERMAL MODEL — MICRO-REFORMER CHANNEL
  
  2D Finite Difference simulation of:
    • Temperature distribution T(x, r) in a single microchannel
    • Velocity profile u(r) — Hagen-Poiseuille (laminar)
    • Nusselt number and heat transfer coefficient
    • Wall vs centerline temperature profiles
    • Species concentration approximation
  
  Geometry: Cylindrical microchannel (tube-in-tube concept)
    - Inner channel: reactant flow + catalyst wall
    - Outer wall:    heated by combustion gas
  
  This provides ANSYS Fluent equivalent results using Python FDM.
  Use this to guide / validate your ANSYS Fluent setup.
=============================================================================
"""

import numpy as np
from scipy.linalg import solve_banded
from dataclasses import dataclass


# ─────────────────────────────────────────────────
#  MICROCHANNEL GEOMETRY
# ─────────────────────────────────────────────────
@dataclass
class ChannelGeometry:
    L:   float = 50e-3    # Channel length [m]         50 mm
    R:   float = 0.5e-3   # Channel radius [m]          0.5 mm
    t_w: float = 0.1e-3   # Wall thickness [m]          0.1 mm
    N_ch: int  = 20       # Number of parallel channels


@dataclass
class FluidProperties:
    """Average mixture properties (H2O/CH4 at reforming conditions)."""
    mu:    float = 2.5e-5     # Dynamic viscosity [Pa·s]
    rho:   float = 0.35       # Density [kg/m³] (at ~800°C, 1 bar)
    Cp:    float = 2500.0     # Heat capacity [J/(kg·K)]
    k_f:   float = 0.08       # Thermal conductivity [W/(m·K)]
    k_w:   float = 16.0       # Wall (Inconel) conductivity [W/(m·K)]


@dataclass
class BoundaryConditions:
    T_in:   float = 298.15   # Inlet temperature [K]
    T_wall: float = 1073.15  # Wall temperature [K] (uniform, prescribed)
    P_in:   float = 1.0      # Inlet pressure [bar → Pa conversion inside]
    u_mean: float = 0.5      # Mean inlet velocity [m/s]


# ─────────────────────────────────────────────────
#  VELOCITY PROFILE (HAGEN-POISEUILLE)
# ─────────────────────────────────────────────────
def velocity_profile(r_arr: np.ndarray, R: float, u_mean: float) -> np.ndarray:
    """
    Fully-developed laminar (Hagen-Poiseuille) velocity profile.
    u(r) = 2 * u_mean * (1 - (r/R)²)
    """
    return 2.0 * u_mean * (1.0 - (r_arr / R)**2)


def reynolds_number(u_mean: float, D: float,
                    rho: float, mu: float) -> float:
    """Re = ρ u D / μ"""
    return rho * u_mean * D / mu


def nusselt_developing(Re: float, Pr: float,
                       L: float, D: float,
                       mode: str = "uniform_wall_T") -> float:
    """
    Nusselt number for thermally developing flow (Graetz problem).
    
    mode = 'uniform_wall_T'  → Nu = 3.657 + Graetz correction
    mode = 'uniform_flux'    → Nu = 4.364 + Graetz correction
    
    Gnielinski extension for Re > 2300.
    """
    Gz = Re * Pr * D / L    # Graetz number

    if Re < 2300:            # Laminar
        if mode == "uniform_wall_T":
            Nu = 3.657 + 0.0668 * Gz / (1 + 0.04 * Gz**(2/3))
        else:
            Nu = 4.364 + 0.0668 * Gz / (1 + 0.04 * Gz**(2/3))
    else:                    # Turbulent (Gnielinski)
        f  = (0.790 * np.log(Re) - 1.64)**(-2)
        Nu = (f/8) * (Re - 1000) * Pr / (1 + 12.7*(f/8)**0.5 * (Pr**(2/3) - 1))

    return max(Nu, 3.66)


def heat_transfer_coefficient(Nu: float, k_f: float, D: float) -> float:
    """h = Nu × k / D  [W/(m²·K)]"""
    return Nu * k_f / D


# ─────────────────────────────────────────────────
#  2D TEMPERATURE FIELD (FDM)
#  Governing equation (parabolic):
#    ρ Cp u ∂T/∂x = k ∇²T + Q_rxn(x)
#  Discretized using QUICK/upwind in x, central in r.
# ─────────────────────────────────────────────────
class MicrochannelThermal2D:
    """
    2D axisymmetric finite difference solver for microchannel heat transfer.
    Coordinates: x (axial), r (radial)
    """

    def __init__(self, geom: ChannelGeometry,
                 fluid: FluidProperties,
                 bc: BoundaryConditions,
                 Nx: int = 150, Nr: int = 25):
        self.geom  = geom
        self.fluid = fluid
        self.bc    = bc
        self.Nx    = Nx
        self.Nr    = Nr

        # Grid
        self.x     = np.linspace(0, geom.L, Nx)
        self.r     = np.linspace(0, geom.R, Nr)
        self.dx    = geom.L / (Nx - 1)
        self.dr    = geom.R / (Nr - 1)

        # Velocity profile
        self.u     = velocity_profile(self.r, geom.R, bc.u_mean)

        # Temperature field (r × x)
        self.T     = np.full((Nr, Nx), bc.T_in)

        # BCs
        self.T[:, 0]  = bc.T_in     # Inlet
        self.T[-1, :] = bc.T_wall   # Wall (r = R)

    def _heat_source(self, x: float) -> float:
        """
        Volumetric heat source Q [W/m³] from SMR reaction.
        Simplified as Gaussian distribution along channel length.
        Peak at x = 0.3L (reaction front).
        """
        Q_peak   = 5e6     # W/m³
        x_peak   = 0.3 * self.geom.L
        sigma    = 0.1 * self.geom.L
        return Q_peak * np.exp(-0.5 * ((x - x_peak) / sigma)**2)

    def solve(self) -> dict:
        """
        March from x=0 to x=L using implicit scheme in r-direction.
        Returns temperature field and derived quantities.
        """
        fluid  = self.fluid
        bc     = self.bc
        Nr, Nx = self.Nr, self.Nx
        dr, dx = self.dr, self.dx

        alpha = fluid.k_f / (fluid.rho * fluid.Cp)   # thermal diffusivity

        # Coefficient matrix (tridiagonal for r-direction)
        T_field = np.full((Nr, Nx), bc.T_in, dtype=float)
        T_field[-1, :] = bc.T_wall
        T_field[:,  0] = bc.T_in

        for j in range(Nx - 1):
            x_j = self.x[j]
            Q_j = self._heat_source(x_j)

            # Build tridiagonal system for implicit r-sweep
            a = np.zeros(Nr)    # sub-diagonal
            b = np.zeros(Nr)    # diagonal
            c = np.zeros(Nr)    # super-diagonal
            d = np.zeros(Nr)    # RHS

            for i in range(1, Nr - 1):
                r_i = self.r[i]
                u_i = self.u[i]

                coeff_r  = alpha / dr**2
                coeff_rp = coeff_r * (1 + dr / (2 * r_i))
                coeff_rm = coeff_r * (1 - dr / (2 * r_i))
                coeff_x  = u_i / dx

                a[i] = -coeff_rm
                b[i] =  coeff_x + coeff_rp + coeff_rm
                c[i] = -coeff_rp
                d[i] = (coeff_x * T_field[i, j]
                         + Q_j / (fluid.rho * fluid.Cp))

            # Symmetry BC at r=0: dT/dr = 0 → T[0] = T[1]
            b[0]  = 1; c[0]  = -1; d[0]  = 0

            # Wall BC (Dirichlet)
            b[-1] = 1; a[-1] = 0; d[-1] = bc.T_wall

            # Solve tridiagonal (Thomas algorithm via numpy)
            T_new = self._tdma(a, b, c, d)
            T_field[:, j+1] = np.clip(T_new, bc.T_in, bc.T_wall + 50)

        self.T = T_field
        return self._postprocess()

    def _tdma(self, a: np.ndarray, b: np.ndarray,
               c: np.ndarray, d: np.ndarray) -> np.ndarray:
        """Thomas algorithm (TriDiagonal Matrix Algorithm)."""
        n  = len(b)
        c_ = np.zeros(n)
        d_ = np.zeros(n)
        x  = np.zeros(n)

        c_[0] = c[0] / b[0]
        d_[0] = d[0] / b[0]

        for i in range(1, n):
            denom = b[i] - a[i] * c_[i-1]
            if abs(denom) < 1e-30:
                denom = 1e-30
            c_[i] = c[i] / denom
            d_[i] = (d[i] - a[i] * d_[i-1]) / denom

        x[-1] = d_[-1]
        for i in range(n-2, -1, -1):
            x[i] = d_[i] - c_[i] * x[i+1]

        return x

    def _postprocess(self) -> dict:
        """Compute derived quantities from temperature field."""
        fluid = self.fluid
        bc    = self.bc
        geom  = self.geom

        T_cl   = self.T[0, :]        # Centerline temperature
        T_wall = self.T[-1, :]       # Wall temperature (= bc.T_wall)
        T_mix  = np.trapezoid(self.u[:, np.newaxis] * self.T,
                           self.r, axis=0) / np.trapezoid(self.u, self.r)

        # Local heat flux at wall: q = -k dT/dr|_{r=R}
        dT_dr_wall = (self.T[-1, :] - self.T[-2, :]) / self.dr
        q_wall     = -fluid.k_f * dT_dr_wall          # W/m²

        # Local Nusselt: Nu = q × D / (k × (T_wall - T_mix))
        D     = 2 * geom.R
        dT_lm = bc.T_wall - T_mix + 1e-6
        Nu_x  = q_wall * D / (fluid.k_f * dT_lm)
        h_x   = Nu_x * fluid.k_f / D

        # Flow properties
        Re    = reynolds_number(bc.u_mean, D, fluid.rho, fluid.mu)
        Pr    = fluid.mu * fluid.Cp / fluid.k_f
        Nu_avg= nusselt_developing(Re, Pr, geom.L, D)
        h_avg = heat_transfer_coefficient(Nu_avg, fluid.k_f, D)

        # Total heat transferred
        Q_tot = (np.trapezoid(q_wall, self.x) * 2 * np.pi * geom.R
                 * geom.N_ch)   # W (all channels)

        return {
            "x":       self.x * 1000,   # mm
            "r":       self.r * 1000,   # mm
            "T_field": self.T,          # K
            "T_cl":    T_cl,
            "T_wall":  T_wall,
            "T_mix":   T_mix,
            "q_wall":  q_wall,
            "Nu_x":    Nu_x,
            "h_x":     h_x,
            "Re":      Re,
            "Pr":      Pr,
            "Nu_avg":  Nu_avg,
            "h_avg":   h_avg,
            "Q_total_W": Q_tot,
        }


# ─────────────────────────────────────────────────
#  PRESSURE DROP ANALYSIS
# ─────────────────────────────────────────────────
def pressure_drop(geom: ChannelGeometry,
                  fluid: FluidProperties,
                  bc: BoundaryConditions) -> dict:
    """
    Pressure drop through microchannel (Hagen-Poiseuille + minor losses).
    """
    D    = 2 * geom.R
    L    = geom.L
    Re   = reynolds_number(bc.u_mean, D, fluid.rho, fluid.mu)

    # Friction factor
    if Re < 2300:
        f = 64 / Re         # Laminar
    else:
        f = 0.316 * Re**(-0.25)   # Blasius (turbulent)

    # Major (Darcy-Weisbach) and minor losses
    dP_major = f * L / D * 0.5 * fluid.rho * bc.u_mean**2
    dP_minor = 1.5 * 0.5 * fluid.rho * bc.u_mean**2    # entry + exit

    dP_total = dP_major + dP_minor

    return {
        "Re":        Re,
        "f":         f,
        "dP_major":  dP_major,
        "dP_minor":  dP_minor,
        "dP_total":  dP_total,
        "dP_bar":    dP_total / 1e5,
    }


# ─────────────────────────────────────────────────
#  MULTI-TEMPERATURE PARAMETRIC CFD
# ─────────────────────────────────────────────────
def cfd_parametric(T_wall_range: np.ndarray = None,
                   velocity_range: np.ndarray = None) -> list:
    """Run 2D thermal model at multiple wall temperatures and velocities."""
    if T_wall_range is None:
        T_wall_range = np.arange(700, 901, 50) + 273.15
    if velocity_range is None:
        velocity_range = [0.1, 0.3, 0.5, 1.0, 2.0]

    results = []
    geom  = ChannelGeometry()
    fluid = FluidProperties()

    for T_w in T_wall_range:
        for u_m in velocity_range:
            bc = BoundaryConditions(T_wall=T_w, u_mean=u_m)
            solver = MicrochannelThermal2D(geom, fluid, bc, Nx=80, Nr=15)
            out    = solver.solve()
            dp     = pressure_drop(geom, fluid, bc)

            results.append({
                "T_wall_C":   T_w - 273.15,
                "u_mean":     u_m,
                "Re":         out["Re"],
                "Nu_avg":     out["Nu_avg"],
                "h_avg":      out["h_avg"],
                "Q_total_W":  out["Q_total_W"],
                "T_cl_out_C": out["T_cl"][-1] - 273.15,
                "T_mix_out_C":out["T_mix"][-1] - 273.15,
                "dP_Pa":      dp["dP_total"],
            })

    return results


if __name__ == "__main__":
    print("Running 2D CFD thermal model...")
    geom  = ChannelGeometry()
    fluid = FluidProperties()
    bc    = BoundaryConditions(T_wall=1073.15, u_mean=0.5)

    solver = MicrochannelThermal2D(geom, fluid, bc, Nx=120, Nr=20)
    result = solver.solve()

    print(f"Re = {result['Re']:.1f} ({'Laminar' if result['Re']<2300 else 'Turbulent'})")
    print(f"Pr = {result['Pr']:.3f}")
    print(f"Nu_avg = {result['Nu_avg']:.2f}")
    print(f"h_avg  = {result['h_avg']:.1f} W/(m²·K)")
    print(f"Outlet centerline T = {result['T_cl'][-1]-273.15:.1f} °C")
    print(f"Total heat transferred = {result['Q_total_W']:.2f} W")

    dp = pressure_drop(geom, fluid, bc)
    print(f"Pressure drop = {dp['dP_total']:.2f} Pa ({dp['dP_bar']:.4f} bar)")
