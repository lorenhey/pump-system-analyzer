# pump-system-analyzer (v2.0.0)

[![GitHub Pages Deployment](https://img.shields.io/badge/GitHub%20Pages-Live%20v2.0.0-emerald)](https://lorenhey.github.io/pump-system-analyzer/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Standards: API 610 / HI 9.6.1](https://img.shields.io/badge/Standards-API%20610%20%7C%20HI%209.6.1-amber.svg)](https://lorenhey.github.io/pump-system-analyzer/)

> **Simulador Termo-Hidráulico de Redes de Cañerías, Curvas de Bomba, Punto de Operación & Auditor de Cavitación NPSH.**  
> Una herramienta de ingeniería de planta para superar la aproximación nominal y calcular con rigor termodinámico e hidrodinámico el comportamiento real de sistemas de bombeo centrífugo.

🔗 **Aplicación Web Interactiva:** [https://lorenhey.github.io/pump-system-analyzer/](https://lorenhey.github.io/pump-system-analyzer/)

---

## ⚙️ Capacidades Principales (v2.0.0)

1. **Curva de Bomba e Interpolación PCHIP Monótona:**
   * Interpolación Hermítica Cúbica a Trozos (*Piecewise Cubic Hermite Interpolating Polynomial*) para curvas de Altura ($H$-$Q$), Rendimiento ($\eta$-$Q$), Potencia ($P$-$Q$) y $NPSH_r$-$Q$.
   * Elimina oscilaciones numéricas espurias (fenómeno de Runge) preservando la concavidad física del catálogo del fabricante.

2. **Cálculo de Curva de Sistema & Pérdidas por Fricción:**
   * Formulación exacta de **Darcy-Weisbach**:
     $$h_f = f \cdot \frac{L}{D} \cdot \frac{v^2}{2g}$$
   * Factor de fricción $f$ de **Colebrook-White** resuelto mediante la formulación explícita de **Swamee-Jain** para régimen laminar ($Re < 2300$) y turbulento con rugosidad absoluta ($\varepsilon$).
   * Pérdidas secundarias en accesorios ($\sum K$) y estrangulamiento en válvulas de control ($C_v / K_v$).

3. **Solver del Punto de Operación:**
   * Algoritmo numérico de bisección/Brent que encuentra la raíz exacta:
     $$H_{\text{pump}}(Q) - H_{\text{sys}}(Q) = 0$$
   * Determinación de $Q_{op}$, $H_{op}$, $\eta_{op}$, Potencia Hidráulica y Potencia al Freno en el eje ($P_{\text{shaft}}$).
   * Identificación del Punto de Máximo Rendimiento (BEP: *Best Efficiency Point*) y clasificación de la región de trabajo (POR: 80%–110% BEP vs AOR: 70%–120% BEP).

4. **Auditoría Forense de Cavitación & NPSH:**
   * Cálculo riguroso del NPSH Disponible ($NPSH_a$):
     $$\text{NPSH}_a = \frac{P_{\text{suct,abs}} - P_v(T)}{\rho \cdot g} + (Z_s - Z_p) - h_{f,\text{suction}}$$
   * Propiedades del agua dependientes de la temperatura ($0^\circ\text{C}$ a $130^\circ\text{C}$) mediante ecuaciones de vapor de Antoine y densidades IAPWS.
   * Diagnóstico automático bajo normas **HI 9.6.1** y **API 610**:
     * **Seguro:** $\Delta \text{NPSH} \ge 1.0\text{ m}$ y Ratio $\ge 1.20$.
     * **Marginal:** Requiere monitoreo de vibración.
     * **Peligro:** Cavitación inminente / erosión acústica e hidráulica.

5. **Leyes de Afinidad (Variadores VFD & Recorte de Impulsor):**
   * Predicción precisa al variar velocidad ($N$) o diámetro de impulsor ($D$):
     $$\frac{Q_2}{Q_1} = \frac{N_2}{N_1}, \quad \frac{H_2}{H_1} = \left(\frac{N_2}{N_1}\right)^2, \quad \frac{P_2}{P_1} = \left(\frac{N_2}{N_1}\right)^3$$

6. **Arreglos Hidráulicos:**
   * Bombas en Paralelo ($Q_{\text{eq}} = \sum Q_i$ a igual $H$) y Serie ($H_{\text{eq}} = \sum H_i$ a igual $Q$).

7. **Auditoría Energética & OPEX (LCC):**
   * Consumo eléctrico anual en $\text{MWh/año}$ y costo operativo (\$ USD/año).
   * Demostración empírica de ahorro energético: control por VFD vs estrangulamiento de válvula.

---

## 🧪 Validación y Pruebas Unitarias

El motor incluye suites de prueba automatizadas tanto en Python (`pytest`) como en JavaScript (`node`):

```bash
# Tests del motor JavaScript / Web
node tests/test_engine.js

# Tests del motor Python
pytest
```

---

## 📄 Licencia

Código abierto bajo licencia [MIT](LICENSE). Desarrollado por **Lorenzo Perez** ([@lorenhey](https://github.com/lorenhey)).
