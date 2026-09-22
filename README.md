# 🔬 Compact Micro-Reformer for Hydrogen Production

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![JavaScript](https://img.shields.io/badge/JavaScript-Vanilla-yellow.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Complete-success.svg)

> **Mathematical modeling and simulation of a highly compact micro-reformer for on-demand hydrogen production via Steam Methane Reforming (SMR).**

This repository contains the numerical models and thermal analysis required to simulate the kinetics, thermodynamics, and conjugate heat transfer inside a micro-channel reformer. 

## ✨ Key Features

- **PFR Reaction Kinetics:** Solves the core reaction chemistry using the rigorous **Xu and Froment kinetic model** via a 4th-Order Runge-Kutta (RK4) integration scheme.
- **Thermodynamic Balances:** Enforces strict mass and atom conservation while dynamically computing specific heat capacities and required thermal duty using Kirchhoff's Law and Shomate equations.
- **Conjugate Heat Transfer (CHT):** Utilizes a 1D Finite Difference Method (FDM) to simulate the convective and conductive heat transfer across the solid steel walls separating the combustion and reforming channels.
- **Interactive Visualization:** The Python mathematical logic has been meticulously ported into a Vanilla JavaScript single-page application, allowing for real-time parametric sweeps and 3D domain visualization right in the browser.

---

## 🏗️ Technical Architecture

The simulation is built upon three interconnected pillars of chemical engineering physics:

### 1. Reaction Kinetics (Plug Flow Reactor)
Models the primary reactions taking place over the Ni/MgAl₂O₄ catalyst:
* **Steam Methane Reforming (SMR):** $\text{CH}_4 + \text{H}_2\text{O} \rightleftharpoons \text{CO} + 3\text{H}_2 \quad (\Delta H > 0)$
* **Water-Gas Shift (WGS):** $\text{CO} + \text{H}_2\text{O} \rightleftharpoons \text{CO}_2 + \text{H}_2 \quad (\Delta H < 0)$
* **Dry Reforming:** $\text{CH}_4 + 2\text{H}_2\text{O} \rightleftharpoons \text{CO}_2 + 4\text{H}_2 \quad (\Delta H > 0)$

### 2. Mass & Energy Balances
Tracks every single atom (C, H, O) through the system to guarantee a $<0.01\%$ mass balance error. Dynamically recalculates the highly endothermic reaction enthalpies based on the operating temperature.

### 3. Thermal & CFD Analysis
Models the micro-channels (0.5 mm height) to optimize the temperature gradient. Proves that a counter-current flow arrangement provides a superior temperature distribution, preventing the catalyst-degrading hotspots often found in co-current configurations.

---

## 📈 Parametric Findings

Based on Le Chatelier's Principle, our parametric sweeps demonstrate:
- **Temperature:** Methane conversion approaches ~100% at temperatures $> 800^\circ\text{C}$.
- **Pressure:** SMR performs best at lower pressures (e.g., 1 bar). High pressures suppress the forward reaction.
- **S/C Ratio:** A Steam-to-Carbon ratio $> 2.5$ is critical to maximize $\text{H}_2$ yield and suppress solid carbon (coke) deposition.
- **Space Velocity (GHSV):** Must be carefully balanced (optimal: $10,000 - 30,000\text{ h}^{-1}$) to ensure adequate residence time for the gases to reach equilibrium.

---

## 📂 Project Structure

```text
micro_reformer/
├── kinetics_model.py         # ODE solver & Xu-Froment reaction rates
├── mass_energy_balance.py    # Atom tracking & thermodynamic calculations
├── cfd_thermal_model.py      # 1D FDM heat transfer & CHT logic
├── parametric_study.py       # Parametric sweep simulations
├── report_generator.py       # Report creation pipeline
├── main.py                   # Main execution script
└── output_plots/
    └── micro_reformer_report.html # Final interactive JS visualization dashboard
```

---

## 🚀 Getting Started

### Prerequisites
Make sure you have Python 3.8+ installed. You can install the required numerical libraries using:
```bash
pip install -r requirements.txt
```

### Running the Python Models
To execute the mathematical models and generate the thermodynamic data:
```bash
python main.py
```

### Viewing the Interactive Dashboard
The parametric study and visualizations have been ported to a self-contained web app. Simply open the generated HTML file in any modern browser—no server required!
```bash
# On Windows
start output_plots/micro_reformer_report.html
```

---

## 🤝 Contributing
Contributions, issues, and feature requests are welcome!
