"""
=============================================================================
  VISUALIZER — MICRO-REFORMER PLOTS
  Generates all publication-quality figures for the assignment report.
=============================================================================
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.gridspec import GridSpec
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.patches as mpatches
import pandas as pd
import os, warnings
warnings.filterwarnings("ignore")

# ─── STYLE ──────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.dpi":        150,
    "font.family":       "DejaVu Sans",
    "font.size":         11,
    "axes.labelsize":    12,
    "axes.titlesize":    13,
    "axes.titleweight":  "bold",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "legend.framealpha": 0.85,
    "legend.fontsize":   10,
    "lines.linewidth":   2.2,
    "lines.markersize":  6,
    "grid.alpha":        0.35,
    "grid.linestyle":    "--",
})

# Custom colour palette
COLORS = ["#2563EB","#16A34A","#DC2626","#D97706","#7C3AED","#0891B2","#DB2777"]

OUTDIR = os.path.join(os.path.dirname(__file__), "output_plots")
os.makedirs(OUTDIR, exist_ok=True)

def save(fig, name: str):
    path = os.path.join(OUTDIR, name)
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"  ✓ Saved: output_plots/{name}")
    return path


# ──────────────────────────────────────────────────────────────────────────
#  FIG 1: AXIAL SPECIES PROFILES
# ──────────────────────────────────────────────────────────────────────────
def plot_axial_profiles(profile: dict) -> str:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle("Axial Species & Conversion Profiles — PFR Micro-Reformer", y=1.02)

    ax1, ax2 = axes
    W = profile["W"]

    # Species mole fractions
    for sp, col, lbl in [("y_CH4", COLORS[0], "CH₄"),
                          ("y_H2",  COLORS[1], "H₂"),
                          ("y_CO",  COLORS[2], "CO"),
                          ("y_CO2", COLORS[3], "CO₂"),]:
        ax1.plot(W, profile[sp], color=col, label=lbl)

    ax1.set_xlabel("Catalyst Mass W [kg]")
    ax1.set_ylabel("Mole Fraction [%]")
    ax1.set_title("Mole Fraction Profiles")
    ax1.legend(); ax1.grid(True)
    ax1.set_xlim(0, W[-1])

    # Conversion & Yield
    ax2.plot(W, profile["X_CH4"], color=COLORS[0], label="CH₄ Conversion (%)", linewidth=2.5)
    ax2.plot(W, profile["Y_H2"],  color=COLORS[1], label="H₂ Yield (%)",       linewidth=2.5)
    ax2.set_xlabel("Catalyst Mass W [kg]")
    ax2.set_ylabel("Conversion / Yield [%]")
    ax2.set_title("CH₄ Conversion & H₂ Yield")
    ax2.legend(); ax2.grid(True)
    ax2.set_xlim(0, W[-1]); ax2.set_ylim(0, 100)

    plt.tight_layout()
    return save(fig, "fig01_axial_profiles.png")


# ──────────────────────────────────────────────────────────────────────────
#  FIG 2: EFFECT OF TEMPERATURE
# ──────────────────────────────────────────────────────────────────────────
def plot_temperature_study(df: pd.DataFrame) -> str:
    fig = plt.figure(figsize=(14, 10))
    gs  = GridSpec(2, 2, figure=fig, hspace=0.38, wspace=0.35)
    fig.suptitle("Effect of Temperature on Reformer Performance", fontsize=15)

    plots = [
        ("T_C", "X_CH4",    "CH₄ Conversion [%]",    "CH₄ Conversion vs Temperature",   COLORS[0]),
        ("T_C", "Y_H2",     "H₂ Yield [%]",           "H₂ Yield vs Temperature",          COLORS[1]),
        ("T_C", "S_CO",     "CO Selectivity [%]",     "CO Selectivity vs Temperature",    COLORS[2]),
        ("T_C", "F_H2_umol","H₂ Production [μmol/s]", "H₂ Production Rate vs Temperature",COLORS[3]),
    ]

    for idx, (xcol, ycol, ylabel, title, col) in enumerate(plots):
        ax = fig.add_subplot(gs[idx//2, idx%2])
        ax.plot(df[xcol], df[ycol], color=col, marker="o", markersize=4)
        ax.fill_between(df[xcol], df[ycol], alpha=0.12, color=col)
        ax.set_xlabel("Temperature [°C]"); ax.set_ylabel(ylabel)
        ax.set_title(title); ax.grid(True)
        ax.set_xlim(df[xcol].min(), df[xcol].max())

    return save(fig, "fig02_temperature_effect.png")


# ──────────────────────────────────────────────────────────────────────────
#  FIG 3: EFFECT OF PRESSURE
# ──────────────────────────────────────────────────────────────────────────
def plot_pressure_study(df: pd.DataFrame) -> str:
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle("Effect of Pressure on Reformer Performance\n(T = 800 °C, S/C = 3)", fontsize=14)

    for ax, ycol, ylabel, col in zip(axes,
        ["X_CH4",     "Y_H2",    "H2_CO_ratio"],
        ["CH₄ Conversion [%]","H₂ Yield [%]", "H₂/CO Ratio [-]"],
        COLORS[:3]):
        ax.semilogx(df["P_bar"], df[ycol], color=col, marker="s", markersize=6)
        ax.fill_between(df["P_bar"], df[ycol], alpha=0.12, color=col)
        ax.set_xlabel("Pressure [bar]"); ax.set_ylabel(ylabel)
        ax.set_title(ylabel); ax.grid(True, which="both")

    plt.tight_layout()
    return save(fig, "fig03_pressure_effect.png")


# ──────────────────────────────────────────────────────────────────────────
#  FIG 4: EFFECT OF S/C RATIO
# ──────────────────────────────────────────────────────────────────────────
def plot_sc_study(df: pd.DataFrame) -> str:
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle("Effect of Steam-to-Carbon Ratio\n(T = 800 °C, P = 1 bar)", fontsize=14)

    for ax, ycol, ylabel, col in zip(axes,
        ["X_CH4",     "Y_H2",    "S_CO"],
        ["CH₄ Conversion [%]","H₂ Yield [%]","CO Selectivity [%]"],
        COLORS[:3]):
        ax.plot(df["SC"], df[ycol], color=col, marker="^", markersize=6)
        ax.fill_between(df["SC"], df[ycol], alpha=0.12, color=col)
        ax.set_xlabel("S/C Ratio [-]"); ax.set_ylabel(ylabel)
        ax.set_title(ylabel); ax.grid(True)

    plt.tight_layout()
    return save(fig, "fig04_sc_ratio_effect.png")


# ──────────────────────────────────────────────────────────────────────────
#  FIG 5: EFFECT OF GHSV
# ──────────────────────────────────────────────────────────────────────────
def plot_ghsv_study(df: pd.DataFrame) -> str:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle("Effect of GHSV on Reformer Performance\n(T = 800 °C, P = 1 bar, S/C = 3)", fontsize=14)

    ax1, ax2 = axes
    ax1.semilogx(df["GHSV"], df["X_CH4"], color=COLORS[0], label="X_CH₄", marker="o", markersize=4)
    ax1.semilogx(df["GHSV"], df["Y_H2"],  color=COLORS[1], label="Y_H₂",  marker="s", markersize=4)
    ax1.set_xlabel("GHSV [h⁻¹]"); ax1.set_ylabel("Conversion / Yield [%]")
    ax1.set_title("Conversion & Yield vs GHSV"); ax1.legend(); ax1.grid(True, which="both")

    ax2.semilogx(df["GHSV"], df["contact_ms"], color=COLORS[3], marker="^", markersize=4)
    ax2.set_xlabel("GHSV [h⁻¹]"); ax2.set_ylabel("Contact Time [ms]")
    ax2.set_title("Contact Time vs GHSV"); ax2.grid(True, which="both")

    plt.tight_layout()
    return save(fig, "fig05_ghsv_effect.png")


# ──────────────────────────────────────────────────────────────────────────
#  FIG 6: 2D T-SC HEATMAP
# ──────────────────────────────────────────────────────────────────────────
def plot_heatmap_T_SC(df: pd.DataFrame) -> str:
    pivot = df.pivot(index="SC", columns="T_C", values="Y_H2")

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Parametric H₂ Yield Map — Temperature × S/C Ratio", fontsize=14)

    # H2 yield heatmap
    ax = axes[0]
    im = ax.imshow(pivot.values, aspect="auto", origin="lower",
                   extent=[pivot.columns.min(), pivot.columns.max(),
                           pivot.index.min(),   pivot.index.max()],
                   cmap="YlOrRd", vmin=0, vmax=100)
    ax.set_xlabel("Temperature [°C]"); ax.set_ylabel("S/C Ratio [-]")
    ax.set_title("H₂ Yield [%]")
    plt.colorbar(im, ax=ax, label="H₂ Yield [%]")

    # X_CH4 heatmap
    pivot2 = df.pivot(index="SC", columns="T_C", values="X_CH4")
    ax2 = axes[1]
    im2 = ax2.imshow(pivot2.values, aspect="auto", origin="lower",
                     extent=[pivot2.columns.min(), pivot2.columns.max(),
                             pivot2.index.min(),   pivot2.index.max()],
                     cmap="Blues", vmin=0, vmax=100)
    ax2.set_xlabel("Temperature [°C]"); ax2.set_ylabel("S/C Ratio [-]")
    ax2.set_title("CH₄ Conversion [%]")
    plt.colorbar(im2, ax=ax2, label="CH₄ Conversion [%]")

    plt.tight_layout()
    return save(fig, "fig06_heatmap_T_SC.png")


# ──────────────────────────────────────────────────────────────────────────
#  FIG 7: CFD TEMPERATURE FIELD
# ──────────────────────────────────────────────────────────────────────────
def plot_cfd_temperature(cfd_result: dict) -> str:
    fig = plt.figure(figsize=(16, 12))
    gs  = GridSpec(2, 2, figure=fig, hspace=0.40, wspace=0.38)
    fig.suptitle("2D CFD Thermal Analysis — Microchannel Reformer", fontsize=15)

    x_mm  = cfd_result["x"]
    r_mm  = cfd_result["r"]
    T_K   = cfd_result["T_field"]
    T_C   = T_K - 273.15

    # ── Plot 1: 2D contour ──
    ax1 = fig.add_subplot(gs[0, :])
    X, R = np.meshgrid(x_mm, r_mm)
    cf = ax1.contourf(X, R, T_C, levels=40, cmap="inferno")
    plt.colorbar(cf, ax=ax1, label="Temperature [°C]")
    cs = ax1.contour(X, R, T_C, levels=10, colors="white", linewidths=0.5, alpha=0.6)
    ax1.clabel(cs, inline=True, fontsize=8, fmt="%.0f°C")
    ax1.set_xlabel("Axial Position x [mm]"); ax1.set_ylabel("Radial Position r [mm]")
    ax1.set_title("Temperature Distribution T(x,r) — Microchannel Cross-Section")

    # ── Plot 2: Axial profiles ──
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.plot(x_mm, cfd_result["T_cl"]  - 273.15, color=COLORS[0], label="Centerline T")
    ax2.plot(x_mm, cfd_result["T_mix"] - 273.15, color=COLORS[1], label="Bulk-Mean T",  linestyle="--")
    ax2.plot(x_mm, cfd_result["T_wall"]- 273.15, color=COLORS[2], label="Wall T",        linestyle=":")
    ax2.set_xlabel("Axial Position [mm]"); ax2.set_ylabel("Temperature [°C]")
    ax2.set_title("Axial Temperature Profiles"); ax2.legend(); ax2.grid(True)

    # ── Plot 3: Local Nusselt ──
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.plot(x_mm, cfd_result["Nu_x"], color=COLORS[3])
    ax3.axhline(cfd_result["Nu_avg"], color=COLORS[2], linestyle="--",
                label=f"Nu_avg = {cfd_result['Nu_avg']:.2f}")
    ax3.set_xlabel("Axial Position [mm]"); ax3.set_ylabel("Local Nusselt Number Nu(x)")
    ax3.set_title("Local Nusselt Number Distribution"); ax3.legend(); ax3.grid(True)
    ax3.set_ylim(bottom=0)

    return save(fig, "fig07_cfd_temperature.png")


# ──────────────────────────────────────────────────────────────────────────
#  FIG 8: VELOCITY PROFILE + RADIAL TEMPERATURE
# ──────────────────────────────────────────────────────────────────────────
def plot_velocity_radial(cfd_result: dict, geom) -> str:
    from cfd_thermal_model import velocity_profile, BoundaryConditions
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle("Microchannel Flow & Radial Temperature Profiles", fontsize=14)

    r_mm = cfd_result["r"]
    R_mm = r_mm[-1]

    # ── Velocity profile ──
    u_mean = 0.5
    u = 2 * u_mean * (1 - (r_mm / R_mm)**2)
    axes[0].plot(u, r_mm, color=COLORS[0])
    axes[0].fill_betweenx(r_mm, 0, u, alpha=0.2, color=COLORS[0])
    axes[0].set_xlabel("Velocity u(r) [m/s]"); axes[0].set_ylabel("Radial Position r [mm]")
    axes[0].set_title("Hagen-Poiseuille Velocity Profile"); axes[0].grid(True)
    axes[0].axvline(u_mean, color=COLORS[2], linestyle="--", label="u_mean")
    axes[0].legend()

    # ── Radial T at x = L/4, L/2, 3L/4 ──
    T_K    = cfd_result["T_field"]
    Nx     = T_K.shape[1]
    pts    = [(Nx//4, "x=L/4"), (Nx//2, "x=L/2"), (3*Nx//4, "x=3L/4")]
    for (idx, lbl), col in zip(pts, COLORS):
        axes[1].plot(T_K[:, idx] - 273.15, r_mm, color=col, label=lbl)
    axes[1].set_xlabel("Temperature [°C]"); axes[1].set_ylabel("Radial Position r [mm]")
    axes[1].set_title("Radial Temperature at Different Axial Positions")
    axes[1].legend(); axes[1].grid(True)

    # ── Heat flux at wall ──
    axes[2].plot(cfd_result["x"], cfd_result["q_wall"] / 1e3, color=COLORS[2])
    axes[2].set_xlabel("Axial Position [mm]"); axes[2].set_ylabel("Wall Heat Flux [kW/m²]")
    axes[2].set_title("Axial Wall Heat Flux Distribution"); axes[2].grid(True)
    axes[2].fill_between(cfd_result["x"], cfd_result["q_wall"]/1e3, alpha=0.15, color=COLORS[2])

    plt.tight_layout()
    return save(fig, "fig08_velocity_radial.png")


# ──────────────────────────────────────────────────────────────────────────
#  FIG 9: MASS & ENERGY BALANCE SANKEY-STYLE BAR
# ──────────────────────────────────────────────────────────────────────────
def plot_energy_balance(results_table: list) -> str:
    df = pd.DataFrame(results_table)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle("Mass & Energy Balance — Effect of Temperature & S/C Ratio", fontsize=14)

    # Heat duty vs T for each SC
    for sc_val, col in zip([2.0, 3.0, 4.0], COLORS):
        sub = df[df["SC"] == sc_val]
        axes[0].plot(sub["T_C"], sub["Q_duty_W"],
                     color=col, marker="o", markersize=4, label=f"S/C = {sc_val}")
    axes[0].set_xlabel("Temperature [°C]"); axes[0].set_ylabel("Net Heat Duty [W]")
    axes[0].set_title("Heat Duty vs Temperature"); axes[0].legend(); axes[0].grid(True)

    # Thermal efficiency
    for sc_val, col in zip([2.0, 3.0, 4.0], COLORS):
        sub = df[df["SC"] == sc_val]
        axes[1].plot(sub["T_C"], sub["eta_%"],
                     color=col, marker="^", markersize=4, label=f"S/C = {sc_val}")
    axes[1].set_xlabel("Temperature [°C]"); axes[1].set_ylabel("Thermal Efficiency [%]")
    axes[1].set_title("Thermal Efficiency vs Temperature"); axes[1].legend(); axes[1].grid(True)

    plt.tight_layout()
    return save(fig, "fig09_energy_balance.png")


# ──────────────────────────────────────────────────────────────────────────
#  FIG 10: PERFORMANCE SUMMARY RADAR / SPIDER CHART
# ──────────────────────────────────────────────────────────────────────────
def plot_summary_radar(summary_data: dict) -> str:
    """
    Radar chart comparing performance at different operating conditions.
    """
    categories = ["CH₄\nConversion", "H₂\nYield", "H₂/CO\nRatio",
                  "Thermal\nEff. (norm)", "CO\nSelectivity(inv)"]
    N = len(categories)
    angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    ax.set_title("Micro-Reformer Performance Radar\n(Normalized 0-100 scale)",
                 pad=20, fontsize=13, fontweight="bold")

    for (label, vals), col in zip(summary_data.items(), COLORS):
        v = vals + vals[:1]
        ax.plot(angles, v, color=col, linewidth=2, label=label)
        ax.fill(angles, v, alpha=0.10, color=col)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=10)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.grid(True, alpha=0.4)
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.15))

    plt.tight_layout()
    return save(fig, "fig10_radar_chart.png")


# ──────────────────────────────────────────────────────────────────────────
#  FIG 11: EQUILIBRIUM CONSTANTS vs T
# ──────────────────────────────────────────────────────────────────────────
def plot_equilibrium_constants() -> str:
    from kinetics_model import equilibrium_constants
    T_range = np.arange(500, 1001, 10)
    K1_vals = [equilibrium_constants(T+273.15)["K1"] for T in T_range]
    K2_vals = [equilibrium_constants(T+273.15)["K2"] for T in T_range]
    K3_vals = [equilibrium_constants(T+273.15)["K3"] for T in T_range]

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle("Equilibrium Constants vs Temperature", fontsize=14)

    for ax, K, label, col in zip(axes,
        [K1_vals, K2_vals, K3_vals],
        ["K₁ (SMR) [bar²]", "K₂ (WGS) [-]", "K₃ (DR) [bar²]"],
        COLORS[:3]):
        ax.semilogy(T_range, K, color=col)
        ax.fill_between(T_range, K, 1e-20, alpha=0.12, color=col)
        ax.set_xlabel("Temperature [°C]"); ax.set_ylabel(label)
        ax.set_title(label); ax.grid(True, which="both")

    plt.tight_layout()
    return save(fig, "fig11_equilibrium_constants.png")


# ──────────────────────────────────────────────────────────────────────────
#  FIG 12: MICRO-REACTOR SCHEMATIC DIAGRAM
# ──────────────────────────────────────────────────────────────────────────
def plot_reactor_schematic() -> str:
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.set_xlim(0, 14); ax.set_ylim(0, 6)
    ax.axis("off")
    ax.set_title("Micro-Reformer System — Schematic Diagram", fontsize=14, fontweight="bold", pad=15)

    # Outer reactor shell
    outer = mpatches.FancyBboxPatch((1, 1), 10, 4,
        boxstyle="round,pad=0.1", linewidth=2,
        edgecolor="#1E3A5F", facecolor="#EBF5FB")
    ax.add_patch(outer)

    # Catalyst bed region
    cat = mpatches.FancyBboxPatch((2, 1.5), 7, 3,
        boxstyle="round,pad=0.05", linewidth=1.5,
        edgecolor="#6B7280", facecolor="#FEF9C3", alpha=0.7)
    ax.add_patch(cat)
    ax.text(5.5, 3.0, "Ni/Al₂O₃ Catalyst Bed", ha="center", va="center",
            fontsize=11, color="#92400E", fontweight="bold")

    # Heat source (outer annulus)
    for y_pos, label in [(1.1, "Combustion Gas (Heat Source)"), (4.7, "")]:
        ax.text(6, y_pos, label, ha="center", va="center",
                fontsize=9, color="#B91C1C", style="italic")

    # Flow arrows
    ax.annotate("", xy=(2.1, 3), xytext=(0.5, 3),
                arrowprops=dict(arrowstyle="->", color=COLORS[0], lw=2.5))
    ax.text(0.2, 3.3, "Feed\nCH₄ + H₂O", ha="center", fontsize=9, color=COLORS[0])

    ax.annotate("", xy=(12.0, 3), xytext=(9.0, 3),
                arrowprops=dict(arrowstyle="->", color=COLORS[1], lw=2.5))
    ax.text(12.5, 3.3, "Product\nH₂+CO+CO₂", ha="center", fontsize=9, color=COLORS[1])

    # Heat arrows
    for y in [1.6, 2.2, 2.8, 3.4, 4.0, 4.6]:
        ax.annotate("", xy=(2.1, y), xytext=(1.2, y),
                    arrowprops=dict(arrowstyle="->", color=COLORS[2], lw=1, alpha=0.5))

    # Labels
    ax.text(6, 5.5, "T: 600–900 °C  |  P: 1–20 bar  |  S/C: 2–5  |  L = 50 mm",
            ha="center", va="center", fontsize=10,
            bbox=dict(boxstyle="round", facecolor="#DBEAFE", edgecolor="#3B82F6"))

    # Dimensions
    ax.annotate("", xy=(2, 0.6), xytext=(9, 0.6),
                arrowprops=dict(arrowstyle="<->", color="#374151", lw=1.5))
    ax.text(5.5, 0.35, "Reactor Length L = 50 mm", ha="center", fontsize=9, color="#374151")

    plt.tight_layout()
    return save(fig, "fig12_reactor_schematic.png")


# ──────────────────────────────────────────────────────────────────────────
#  GENERATE ALL FIGURES
# ──────────────────────────────────────────────────────────────────────────
def generate_all_plots(data: dict) -> list:
    """Generate all 12 figures. Returns list of file paths."""
    paths = []
    print("\n  Generating plots...")

    paths.append(plot_axial_profiles(data["axial_profile"]))
    paths.append(plot_temperature_study(data["df_T"]))
    paths.append(plot_pressure_study(data["df_P"]))
    paths.append(plot_sc_study(data["df_SC"]))
    paths.append(plot_ghsv_study(data["df_GH"]))
    paths.append(plot_heatmap_T_SC(data["df_map"]))
    paths.append(plot_cfd_temperature(data["cfd_result"]))
    paths.append(plot_velocity_radial(data["cfd_result"], data["geom"]))
    paths.append(plot_energy_balance(data["balance_table"]))
    paths.append(plot_summary_radar(data["radar_data"]))
    paths.append(plot_equilibrium_constants())
    paths.append(plot_reactor_schematic())

    return paths
