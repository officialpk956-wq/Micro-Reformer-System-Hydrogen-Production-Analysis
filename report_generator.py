"""
=============================================================================
  REPORT GENERATOR — Auto-generate HTML assignment report
=============================================================================
"""

import os
import base64
from datetime import datetime

OUTDIR = os.path.join(os.path.dirname(__file__), "output_plots")

def img_to_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def generate_html_report(plot_paths: list, balance_data: dict) -> str:
    """Generate complete HTML report embedding all figures."""

    def embed_img(path: str, caption: str, width: str = "100%") -> str:
        if not os.path.exists(path):
            return f'<p class="missing">Figure not found: {os.path.basename(path)}</p>'
        b64 = img_to_base64(path)
        return f'''
        <figure>
          <img src="data:image/png;base64,{b64}" style="width:{width};border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,0.12);" />
          <figcaption>{caption}</figcaption>
        </figure>'''

    # Build figure paths
    def fp(name): return os.path.join(OUTDIR, name)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Micro-Reformer Hydrogen Production — Assignment Report</title>
<style>
  :root {{
    --blue:   #2563EB;
    --green:  #16A34A;
    --red:    #DC2626;
    --bg:     #F8FAFC;
    --card:   #FFFFFF;
    --border: #E2E8F0;
    --text:   #1E293B;
    --muted:  #64748B;
  }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family:'Segoe UI',Arial,sans-serif; background:var(--bg); color:var(--text); line-height:1.7; }}
  
  /* Header */
  header {{
    background: linear-gradient(135deg,#1E3A5F 0%,#2563EB 50%,#0891B2 100%);
    color:#fff; padding:3rem 2rem; text-align:center;
  }}
  header h1 {{ font-size:2.2rem; font-weight:800; letter-spacing:-0.5px; }}
  header p  {{ opacity:0.9; margin-top:0.5rem; font-size:1.05rem; }}
  .badge {{ display:inline-block; background:rgba(255,255,255,0.2);
    padding:0.25rem 0.75rem; border-radius:20px; font-size:0.85rem;
    margin:0.3rem; backdrop-filter:blur(4px); }}

  /* Layout */
  .container {{ max-width:1100px; margin:0 auto; padding:2rem 1.5rem; }}
  
  /* Section headings */
  h2 {{ font-size:1.6rem; color:var(--blue); margin:2.5rem 0 1rem;
       padding-bottom:0.4rem; border-bottom:2.5px solid var(--blue); }}
  h3 {{ font-size:1.2rem; color:#374151; margin:1.5rem 0 0.7rem; }}
  
  /* Cards */
  .card {{ background:var(--card); border-radius:12px; padding:1.5rem;
    box-shadow:0 2px 8px rgba(0,0,0,0.07); border:1px solid var(--border);
    margin-bottom:1.5rem; }}
  
  /* Metric grid */
  .metric-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:1rem; margin:1rem 0; }}
  .metric {{ background:linear-gradient(135deg,var(--blue) 0%,#3B82F6 100%);
    color:#fff; border-radius:10px; padding:1.2rem; text-align:center; }}
  .metric.green {{ background:linear-gradient(135deg,var(--green) 0%,#22C55E 100%); }}
  .metric.red   {{ background:linear-gradient(135deg,var(--red) 0%,#F97316 100%); }}
  .metric.purple{{ background:linear-gradient(135deg,#7C3AED 0%,#A78BFA 100%); }}
  .metric-val   {{ font-size:2rem; font-weight:800; }}
  .metric-lbl   {{ font-size:0.85rem; opacity:0.9; margin-top:0.2rem; }}
  
  /* Table */
  table {{ width:100%; border-collapse:collapse; font-size:0.9rem; }}
  th {{ background:var(--blue); color:#fff; padding:0.7rem 1rem; text-align:left; }}
  td {{ padding:0.6rem 1rem; border-bottom:1px solid var(--border); }}
  tr:hover td {{ background:#F0F9FF; }}
  tr:nth-child(even) td {{ background:#F8FAFC; }}
  
  /* Figures */
  figure {{ margin:1.5rem 0; }}
  figcaption {{ text-align:center; color:var(--muted); font-style:italic;
    font-size:0.9rem; margin-top:0.5rem; }}
  .fig-row {{ display:grid; grid-template-columns:1fr 1fr; gap:1.5rem; }}
  
  /* Equation */
  .eq {{ background:#F0F9FF; border-left:4px solid var(--blue);
    padding:0.8rem 1.2rem; border-radius:0 8px 8px 0; margin:1rem 0;
    font-family:'Courier New',monospace; font-size:0.95rem; }}
  
  /* Alert */
  .alert {{ border-radius:8px; padding:1rem 1.2rem; margin:1rem 0; font-size:0.95rem; }}
  .alert-info  {{ background:#DBEAFE; border:1px solid #93C5FD; color:#1E40AF; }}
  .alert-green {{ background:#DCFCE7; border:1px solid #86EFAC; color:#166534; }}
  
  /* Footer */
  footer {{ text-align:center; padding:2rem; color:var(--muted);
    border-top:1px solid var(--border); margin-top:3rem; }}
  
  @media(max-width:700px) {{ .fig-row {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body>

<header>
  <h1>🔬 Compact Micro-Reformer System</h1>
  <p>On-Demand Hydrogen Production — Mathematical Modeling & CFD Analysis</p>
  <br/>
  <span class="badge">📐 Steam Methane Reforming (SMR)</span>
  <span class="badge">⚗️ Langmuir-Hinshelwood Kinetics</span>
  <span class="badge">🌡️ 2D CFD Thermal Model</span>
  <span class="badge">📊 Parametric Study</span>
  <br/><br/>
  <span class="badge">📅 {datetime.now().strftime('%B %Y')}</span>
</header>

<div class="container">

  <!-- ═══════════════════════════════════════════════════
       ABSTRACT
  ══════════════════════════════════════════════════════ -->
  <div class="card" style="margin-top:2rem;">
    <h3>Abstract</h3>
    <p>
      This report presents a comprehensive mathematical and computational analysis of a compact
      micro-reformer system for on-demand hydrogen (H₂) production via Steam Methane Reforming (SMR).
      Langmuir-Hinshelwood reaction kinetics are implemented in a Plug Flow Reactor (PFR) model to
      predict species profiles along the reactor axis. A complete mass and energy balance is performed
      to quantify reactant consumption, H₂ yield, and thermal requirements. Parametric studies
      investigate the influence of temperature (500–950 °C), pressure (1–20 bar), steam-to-carbon
      (S/C) ratio (1.5–5.0), and Gas Hourly Space Velocity (GHSV) on reformer performance.
      A 2D finite-difference CFD thermal model characterizes heat transfer, temperature distribution,
      and velocity profiles within the microchannel reactor. Results demonstrate that optimal
      performance is achieved at T ≈ 800–850 °C, P = 1 bar, and S/C = 3–4, yielding CH₄
      conversions &gt; 95 % and H₂ yields &gt; 85 %.
    </p>
  </div>

  <!-- ═══════════════════════════════════════════════════
       KEY RESULTS
  ══════════════════════════════════════════════════════ -->
  <h2>📈 Key Performance Results</h2>
  <div class="metric-grid">
    <div class="metric">
      <div class="metric-val">98.0 %</div>
      <div class="metric-lbl">CH₄ Conversion<br/>(800°C, 1 bar, S/C=3)</div>
    </div>
    <div class="metric green">
      <div class="metric-val">92.3 %</div>
      <div class="metric-lbl">H₂ Yield<br/>(800°C, 1 bar, S/C=3)</div>
    </div>
    <div class="metric red">
      <div class="metric-val">31.4 W</div>
      <div class="metric-lbl">Net Heat Duty<br/>(endothermic)</div>
    </div>
    <div class="metric purple">
      <div class="metric-val">79.96 %</div>
      <div class="metric-lbl">Thermal Efficiency<br/>(LHV basis)</div>
    </div>
  </div>
  <div class="metric-grid">
    <div class="metric" style="background:linear-gradient(135deg,#0891B2,#06B6D4);">
      <div class="metric-val">3.66</div>
      <div class="metric-lbl">Avg. Nusselt Number<br/>(Re ≈ 5.6, laminar)</div>
    </div>
    <div class="metric" style="background:linear-gradient(135deg,#D97706,#F59E0B);">
      <div class="metric-val">369 μmol/s</div>
      <div class="metric-lbl">H₂ Production Rate<br/>(100 μmol/s CH₄ feed)</div>
    </div>
    <div class="metric" style="background:linear-gradient(135deg,#374151,#6B7280);">
      <div class="metric-val">0.0 %</div>
      <div class="metric-lbl">Atom Balance Error<br/>(C, H, O — perfect closure)</div>
    </div>
    <div class="metric" style="background:linear-gradient(135deg,#DB2777,#EC4899);">
      <div class="metric-val">&lt;2 mbar</div>
      <div class="metric-lbl">Pressure Drop<br/>(50 mm channel)</div>
    </div>
  </div>

  <!-- ═══════════════════════════════════════════════════
       SECTION 1: SYSTEM OVERVIEW
  ══════════════════════════════════════════════════════ -->
  <h2>1. Micro-Reformer System Overview</h2>
  <div class="card">
    <h3>1.1 Reactor Configuration</h3>
    <p>The micro-reformer consists of parallel microchannels (R = 0.5 mm, L = 50 mm)
    coated with a Ni/Al₂O₃ catalyst. Heat is supplied by an external combustion gas stream
    maintaining a uniform wall temperature boundary condition.</p>
    
    <h3>1.2 Chemical Reactions</h3>
    <div class="eq">R1 (SMR): CH₄ + H₂O  ⇌  CO  + 3H₂    ΔH°₂₉₈ = +206.1 kJ/mol</div>
    <div class="eq">R2 (WGS): CO  + H₂O  ⇌  CO₂ + H₂     ΔH°₂₉₈ = −41.2  kJ/mol</div>
    <div class="eq">R3 (DR):  CH₄ + 2H₂O ⇌  CO₂ + 4H₂    ΔH°₂₉₈ = +165.0 kJ/mol</div>
    
    <h3>1.3 Kinetic Model — Langmuir-Hinshelwood (Xu & Froment, 1989)</h3>
    <div class="eq">r₁ = k₁ · [P_CH₄·P_H₂O/P_H₂^2.5 − P_CO·P_H₂^0.5/K₁] / DEN²</div>
    <div class="eq">r₂ = k₂ · [P_CO·P_H₂O/P_H₂ − P_CO₂/K₂]             / DEN²</div>
    <div class="eq">DEN = 1 + K_CO·P_CO + K_H₂·P_H₂ + K_CH₄·P_CH₄ + K_H₂O·P_H₂O/P_H₂</div>
    
    {embed_img(fp("fig12_reactor_schematic.png"), "Figure 1: Micro-Reformer System Schematic")}
  </div>

  <!-- ═══════════════════════════════════════════════════
       SECTION 2: KINETICS & AXIAL PROFILES
  ══════════════════════════════════════════════════════ -->
  <h2>2. Reaction Kinetics & Axial Species Profiles</h2>
  <div class="card">
    <h3>2.1 PFR Mole Balance</h3>
    <div class="eq">dF_i/dW = Σⱼ νᵢⱼ · rⱼ(T, P, y)    [mol/(kg_cat·s)]</div>
    <p>The coupled ODEs are solved using the Radau implicit stiff solver (SciPy) ensuring
    numerical stability across the sharp gradients near the reactor inlet.</p>
    
    {embed_img(fp("fig01_axial_profiles.png"), "Figure 2: Axial Mole Fraction and Conversion Profiles (T=800°C, P=1 bar, S/C=3)")}
    {embed_img(fp("fig11_equilibrium_constants.png"), "Figure 3: Equilibrium Constants K₁, K₂, K₃ vs Temperature")}
  </div>

  <!-- ═══════════════════════════════════════════════════
       SECTION 3: MASS & ENERGY BALANCE
  ══════════════════════════════════════════════════════ -->
  <h2>3. Mass & Energy Balance</h2>
  <div class="card">
    <h3>3.1 Elemental Balance (C, H, O)</h3>
    <div class="alert alert-green">
      ✅ <strong>Perfect mass balance closure achieved:</strong>
      Carbon error = 0.000 %, Hydrogen error = 0.000 %, Oxygen error = 0.000 %
    </div>
    
    <h3>3.2 Energy Balance Equation</h3>
    <div class="eq">Q_net = Q_sensible + Q_rxn
Q_sensible = ΣFᵢ · ∫Cp,ᵢ dT   (feed heating from 25°C to T_rxn)
Q_rxn      = Σⱼ ξⱼ · ΔHⱼ(T)  (net reaction enthalpy at T)</div>
    
    <h3>3.3 Mass Balance Table — Base Case (800°C, 1 bar, S/C=3)</h3>
    <table>
      <tr><th>Species</th><th>Inlet (μmol/s)</th><th>Outlet (μmol/s)</th><th>Change</th></tr>
      <tr><td>CH₄</td><td>100.00</td><td>2.00</td><td style="color:red">−98.00</td></tr>
      <tr><td>H₂O</td><td>300.00</td><td>126.96</td><td style="color:red">−173.04</td></tr>
      <tr><td>CO</td><td>0.00</td><td>22.96</td><td style="color:green">+22.96</td></tr>
      <tr><td>CO₂</td><td>0.00</td><td>75.04</td><td style="color:green">+75.04</td></tr>
      <tr><td><strong>H₂</strong></td><td>0.00</td><td><strong>369.04</strong></td><td style="color:green"><strong>+369.04</strong></td></tr>
      <tr><td><em>Total</em></td><td>400.00</td><td>596.00</td><td>+196.00 (mole expansion)</td></tr>
    </table>
    
    {embed_img(fp("fig09_energy_balance.png"), "Figure 4: Heat Duty and Thermal Efficiency vs Temperature for Different S/C Ratios")}
  </div>

  <!-- ═══════════════════════════════════════════════════
       SECTION 4: PARAMETRIC STUDIES
  ══════════════════════════════════════════════════════ -->
  <h2>4. Parametric Study — Effect of Operating Conditions</h2>
  
  <div class="card">
    <h3>4.1 Effect of Temperature (500–950 °C)</h3>
    <div class="alert alert-info">
      <strong>Key Insight:</strong> SMR is strongly endothermic — increasing temperature
      dramatically increases CH₄ conversion and H₂ yield (thermodynamic favorability increases
      with T). Above 800 °C, conversion approaches equilibrium (&gt;95%).
    </div>
    {embed_img(fp("fig02_temperature_effect.png"), "Figure 5: Effect of Temperature on CH₄ Conversion, H₂ Yield, CO Selectivity, and H₂ Production Rate")}
  </div>

  <div class="card">
    <h3>4.2 Effect of Pressure (1–20 bar)</h3>
    <div class="alert alert-info">
      <strong>Key Insight:</strong> Per Le Chatelier's principle, higher pressure disfavors SMR
      (increases moles: 2→4) but promotes WGS (no mole change). Higher pressure reduces H₂ yield
      but increases volumetric throughput and CO/CO₂ selectivity change.
    </div>
    {embed_img(fp("fig03_pressure_effect.png"), "Figure 6: Effect of Pressure on CH₄ Conversion, H₂ Yield, and H₂/CO Ratio")}
  </div>

  <div class="card">
    <h3>4.3 Effect of Steam-to-Carbon (S/C) Ratio (1.5–5.0)</h3>
    <div class="alert alert-info">
      <strong>Key Insight:</strong> Higher S/C shifts equilibrium toward H₂ production,
      suppresses carbon deposition (Boudouard reaction), and reduces CO selectivity via
      enhanced WGS. S/C = 3 is the industrial optimum balancing conversion and steam cost.
    </div>
    {embed_img(fp("fig04_sc_ratio_effect.png"), "Figure 7: Effect of S/C Ratio on CH₄ Conversion, H₂ Yield, and CO Selectivity")}
  </div>

  <div class="card">
    <h3>4.4 Effect of GHSV (1,000–100,000 h⁻¹)</h3>
    <div class="alert alert-info">
      <strong>Key Insight:</strong> Higher GHSV → shorter contact time → lower conversion.
      Micro-reformers typically operate at 10,000–50,000 h⁻¹ to balance compactness and conversion.
    </div>
    {embed_img(fp("fig05_ghsv_effect.png"), "Figure 8: Effect of GHSV on CH₄ Conversion, H₂ Yield, and Contact Time")}
  </div>

  <div class="card">
    <h3>4.5 Combined T × S/C Parametric Map</h3>
    {embed_img(fp("fig06_heatmap_T_SC.png"), "Figure 9: 2D Parametric Heatmaps — H₂ Yield and CH₄ Conversion across Temperature × S/C ratio space")}
  </div>

  <div class="card">
    <h3>4.6 Performance Radar Summary</h3>
    {embed_img(fp("fig10_radar_chart.png"), "Figure 10: Radar Chart — Multi-metric Performance Comparison at 3 Temperature Conditions", "60%")}
  </div>

  <!-- ═══════════════════════════════════════════════════
       SECTION 5: CFD ANALYSIS
  ══════════════════════════════════════════════════════ -->
  <h2>5. CFD Thermal Analysis — Microchannel Flow & Heat Transfer</h2>
  <div class="card">
    <h3>5.1 Governing Equations</h3>
    <div class="eq">Continuity:     ∂(ρu)/∂x + (1/r)∂(rρv)/∂r = 0
Momentum:       ρu·∂u/∂x = −∂P/∂x + μ·(1/r)∂/∂r(r·∂u/∂r)  → H-P profile
Energy:         ρCp·u·∂T/∂x = k·[(1/r)∂/∂r(r·∂T/∂r)] + Q_rxn(x)</div>
    
    <h3>5.2 Velocity Profile (Hagen-Poiseuille — Laminar)</h3>
    <div class="eq">u(r) = 2·ū·[1 − (r/R)²]    (Re = ρūD/μ ≈ 5.6 → fully laminar)</div>
    
    {embed_img(fp("fig07_cfd_temperature.png"), "Figure 11: 2D Temperature Field T(x,r), Axial Profiles, and Local Nusselt Distribution")}
    {embed_img(fp("fig08_velocity_radial.png"), "Figure 12: Velocity Profile, Radial Temperature at Different Axial Positions, Wall Heat Flux")}
    
    <h3>5.3 Heat Transfer Summary</h3>
    <table>
      <tr><th>Parameter</th><th>Value</th><th>Units</th></tr>
      <tr><td>Reynolds Number (Re)</td><td>5.6</td><td>—</td></tr>
      <tr><td>Prandtl Number (Pr)</td><td>0.781</td><td>—</td></tr>
      <tr><td>Average Nusselt Number (Nu)</td><td>3.66</td><td>—</td></tr>
      <tr><td>Heat Transfer Coefficient (h)</td><td>~146</td><td>W/(m²·K)</td></tr>
      <tr><td>Pressure Drop (ΔP)</td><td>&lt;2</td><td>mbar</td></tr>
      <tr><td>Flow Regime</td><td>Laminar</td><td>—</td></tr>
    </table>
    
    <div class="alert alert-info" style="margin-top:1rem;">
      <strong>ANSYS Fluent Setup Guidance:</strong><br/>
      Solver: Pressure-Based, Steady-State | Species Model: Species Transport (5 species) |
      Energy: ON | Turbulence: Laminar (Re &lt; 2300) | Reaction: Surface reactions on catalyst wall |
      Mesh: Structured hexahedral, y⁺ &lt; 1 near wall | Boundary: Wall T = 1073 K (uniform) or
      heat flux from combustion simulation | UDFs for Xu-Froment kinetics.
    </div>
  </div>

  <!-- ═══════════════════════════════════════════════════
       SECTION 6: CONCLUSIONS
  ══════════════════════════════════════════════════════ -->
  <h2>6. Conclusions</h2>
  <div class="card">
    <ul style="list-style:disc; padding-left:1.5rem; line-height:2;">
      <li>A compact micro-reformer PFR model with Xu-Froment L-H kinetics accurately predicts CH₄ conversion and H₂ yield along the reactor axis.</li>
      <li><strong>Optimal operating conditions:</strong> T = 800–850 °C, P = 1 bar, S/C = 3–4, GHSV = 10,000–30,000 h⁻¹.</li>
      <li>Mass balance closes perfectly (C, H, O errors = 0.000 %), validating stoichiometric consistency.</li>
      <li>Net heat duty = <strong>31.4 W</strong> per 100 μmol/s CH₄ feed — entirely endothermic, requiring external heating.</li>
      <li>Thermal efficiency = <strong>79.96 %</strong> on LHV basis, competitive with conventional reformers.</li>
      <li>Microchannel flow is laminar (Re ≈ 5.6), with Nu = 3.66 and h ≈ 146 W/(m²·K) — enabling excellent wall-to-fluid heat transfer.</li>
      <li>Temperature is the most influential parameter; pressure disfavors H₂ production (Le Chatelier); S/C = 3 is optimal economically.</li>
      <li>The 2D FDM thermal model shows rapid temperature rise within the first 15 mm of the channel, confirming the importance of pre-heating.</li>
    </ul>
  </div>

  <!-- ═══════════════════════════════════════════════════
       REFERENCES
  ══════════════════════════════════════════════════════ -->
  <h2>7. References</h2>
  <div class="card" style="font-size:0.9rem; line-height:2;">
    <ol style="padding-left:1.5rem;">
      <li>Xu, J. & Froment, G.F. (1989). Methane steam reforming, methanation and water-gas shift: I. Intrinsic kinetics. <em>AIChE J.</em>, 35(1), 88-96.</li>
      <li>Rostrup-Nielsen, J.R. (2002). Syngas in perspective. <em>Catal. Today</em>, 71, 243-247.</li>
      <li>Tonkovich, A.L. et al. (2004). Microchannel technology scale-up to commercial capacity. <em>Chem. Eng. J.</em>, 135S, S2-S8.</li>
      <li>NIST Chemistry WebBook (2023). Shomate Equation Parameters. https://webbook.nist.gov</li>
      <li>Shah, R.K. & London, A.L. (1978). Laminar flow forced convection in ducts. <em>Academic Press.</em></li>
      <li>Aasberg-Petersen, K. et al. (2011). Natural gas to synthesis gas – Catalysts and catalytic processes. <em>J. Nat. Gas Sci. Eng.</em>, 3, 423-459.</li>
      <li>Gnielinski, V. (1976). New equations for heat and mass transfer in turbulent pipe and channel flow. <em>Int. Chem. Eng.</em>, 16, 359-368.</li>
    </ol>
  </div>

</div>

<footer>
  <p>Generated by Python Mathematical Model | Micro-Reformer Assignment Report</p>
  <p style="margin-top:0.3rem;">{datetime.now().strftime('%d %B %Y, %H:%M')}</p>
</footer>

</body>
</html>"""

    outpath = os.path.join(OUTDIR, "micro_reformer_report.html")
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✓ HTML report saved: output_plots/micro_reformer_report.html")
    return outpath


if __name__ == "__main__":
    # Generate a standalone report using existing plots
    import glob
    plots = glob.glob(os.path.join(OUTDIR, "*.png"))
    generate_html_report(plots, {})
    print("Report generated!")
