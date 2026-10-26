/**
 * pump-engine.js - Motor de cálculo termo-hidráulico de alta precisión
 * Implementa Darcy-Weisbach, Colebrook-White, PCHIP, leyes de afinidad, NPSH y LCC.
 */

class PchipInterpolator {
  constructor(xs, ys) {
    if (xs.length !== ys.length || xs.length < 2) {
      throw new Error("PchipInterpolator requiere al menos 2 puntos ordenados.");
    }
    // Ordenar puntos por x creciente
    const pts = xs.map((x, i) => ({ x: Number(x), y: Number(ys[i]) }))
                  .sort((a, b) => a.x - b.x);
    this.xs = pts.map(p => p.x);
    this.ys = pts.map(p => p.y);
    this.n = this.xs.length;

    // Calcular pendientes y derivadas secantes
    this.h = [];
    this.delta = [];
    for (let i = 0; i < this.n - 1; i++) {
      const h_i = this.xs[i + 1] - this.xs[i];
      if (h_i <= 0) throw new Error("Puntos x duplicados o no crecientes.");
      this.h.push(h_i);
      this.delta.push((this.ys[i + 1] - this.ys[i]) / h_i);
    }

    // Derivadas en los nodos d_k (algoritmo estándar PCHIP de Fritsch-Carlson)
    this.d = new Array(this.n).fill(0);
    for (let i = 1; i < this.n - 1; i++) {
      if (this.delta[i - 1] * this.delta[i] > 0) {
        const w1 = 2 * this.h[i] + this.h[i - 1];
        const w2 = this.h[i] + 2 * this.h[i - 1];
        this.d[i] = (w1 + w2) / (w1 / this.delta[i - 1] + w2 / this.delta[i]);
      } else {
        this.d[i] = 0;
      }
    }

    // Extremos (condición de frontera con corrección monótona)
    this.d[0] = this._endpointDerivative(this.h[0], this.h[1] || this.h[0], this.delta[0], this.delta[1] || this.delta[0]);
    this.d[this.n - 1] = this._endpointDerivative(
      this.h[this.n - 2], 
      this.h[this.n - 3] || this.h[this.n - 2], 
      this.delta[this.n - 2], 
      this.delta[this.n - 3] || this.delta[this.n - 2]
    );
  }

  _endpointDerivative(h1, h2, del1, del2) {
    let d = ((2 * h1 + h2) * del1 - h1 * del2) / (h1 + h2);
    if (d * del1 <= 0) d = 0;
    else if (del1 * del2 < 0 && Math.abs(d) > 3 * Math.abs(del1)) d = 3 * del1;
    return d;
  }

  evaluate(x) {
    if (x <= this.xs[0]) {
      // Extrapolación lineal suave en extremo izquierdo
      return this.ys[0] + this.d[0] * (x - this.xs[0]);
    }
    if (x >= this.xs[this.n - 1]) {
      // Extrapolación lineal en extremo derecho
      const last = this.n - 1;
      return this.ys[last] + this.d[last] * (x - this.xs[last]);
    }

    // Búsqueda binaria del intervalo
    let low = 0, high = this.n - 1;
    while (low <= high) {
      const mid = Math.floor((low + high) / 2);
      if (this.xs[mid] <= x && x <= this.xs[mid + 1]) {
        low = mid;
        break;
      }
      if (this.xs[mid] < x) low = mid + 1;
      else high = mid - 1;
    }
    const i = Math.min(low, this.n - 2);
    const h = this.h[i];
    const s = (x - this.xs[i]) / h;
    const s2 = s * s;
    const s3 = s2 * s;

    // Polinomios base de Hermite cúbico
    const h00 = 2 * s3 - 3 * s2 + 1;
    const h10 = s3 - 2 * s2 + s;
    const h01 = -2 * s3 + 3 * s2;
    const h11 = s3 - s2;

    return h00 * this.ys[i] + h10 * h * this.d[i] + h01 * this.ys[i + 1] + h11 * h * this.d[i + 1];
  }
}

class FluidProperties {
  /**
   * Propiedades del agua en función de la temperatura (°C)
   */
  static waterProperties(tempC = 20) {
    const T = Math.max(0, Math.min(130, Number(tempC)));
    // Densidad kg/m³ (IAPWS aproximación cuadrática)
    const density = 1000 * (1 - ((T + 288.9414) / (508929.2 * (T + 68.12963))) * Math.pow(T - 3.9863, 2));
    
    // Viscosidad dinámica Pa.s (Vogel-Fulcher-Tammann)
    const T_k = T + 273.15;
    const viscosity = 0.00002414 * Math.pow(10, 247.8 / (T_k - 140));
    
    // Presión de vapor Pa (Ecuación de Antoine para agua)
    // log10(P_mmHg) = A - B / (C + T)
    const A = 8.07131, B = 1730.63, C = 233.426;
    const p_mmHg = Math.pow(10, A - B / (C + T));
    const vaporPressure = p_mmHg * 133.322; // Pa

    return {
      name: `Agua (${T.toFixed(1)} °C)`,
      temperatureC: T,
      density: Math.round(density * 100) / 100, // kg/m³
      viscosity: viscosity, // Pa.s
      kinematicViscosity: viscosity / density, // m²/s
      vaporPressure: Math.round(vaporPressure) // Pa
    };
  }

  static customFluid(name, density, viscosityPaS, vaporPressurePa, tempC = 20) {
    return {
      name: name || "Fluido Personalizado",
      temperatureC: Number(tempC),
      density: Number(density),
      viscosity: Number(viscosityPaS),
      kinematicViscosity: Number(viscosityPaS) / Number(density),
      vaporPressure: Number(vaporPressurePa)
    };
  }
}

class HydraulicsEngine {
  static G = 9.80665; // m/s²

  /**
   * Factor de fricción de Darcy-Weisbach
   * Colebrook-White resuelto por Swamee-Jain (precisión < 1% en régimen turbulento)
   */
  static frictionFactor(Re, roughnessM, diameterM) {
    if (Re <= 0) return 0;
    if (Re < 2300) {
      // Laminar
      return 64 / Re;
    }
    // Transición / Turbulento
    const relRoughness = roughnessM / diameterM;
    const term = (relRoughness / 3.7) + (5.74 / Math.pow(Re, 0.9));
    const f = 0.25 / Math.pow(Math.log10(term), 2);
    return Math.max(0.008, Math.min(0.1, f));
  }

  /**
   * Pérdida de carga en cañería recta Darcy-Weisbach (m de columna de líquido)
   * Q en m³/h, L en m, D en m
   */
  static pipeFrictionLoss(q_m3h, lengthM, diameterM, roughnessM, fluid) {
    if (q_m3h <= 0 || lengthM <= 0 || diameterM <= 0) return 0;
    const q_m3s = q_m3h / 3600;
    const area = (Math.PI * Math.pow(diameterM, 2)) / 4;
    const velocity = q_m3s / area;
    const Re = (velocity * diameterM) / fluid.kinematicViscosity;
    const f = this.frictionFactor(Re, roughnessM, diameterM);
    
    const hf = f * (lengthM / diameterM) * (Math.pow(velocity, 2) / (2 * this.G));
    return { hf, velocity, Re, f };
  }

  /**
   * Pérdidas secundarias en accesorios: h_minor = sum(K) * v² / (2g)
   */
  static minorLosses(q_m3h, diameterM, sumK) {
    if (q_m3h <= 0 || diameterM <= 0 || sumK <= 0) return 0;
    const q_m3s = q_m3h / 3600;
    const area = (Math.PI * Math.pow(diameterM, 2)) / 4;
    const velocity = q_m3s / area;
    return sumK * (Math.pow(velocity, 2) / (2 * this.G));
  }

  /**
   * Altura de sistema H_sys(Q)
   * H_sys = H_static + K_total * Q²
   */
  static systemHead(q_m3h, staticHeadM, suctionParams, dischargeParams, fluid, valveDeltaH = 0) {
    if (q_m3h <= 0) return staticHeadM;
    
    let totalFriction = 0;
    if (suctionParams && suctionParams.lengthM > 0) {
      const suct = this.pipeFrictionLoss(q_m3h, suctionParams.lengthM, suctionParams.diameterM, suctionParams.roughnessM, fluid);
      const minor = this.minorLosses(q_m3h, suctionParams.diameterM, suctionParams.sumK);
      totalFriction += suct.hf + minor;
    }
    if (dischargeParams && dischargeParams.lengthM > 0) {
      const disch = this.pipeFrictionLoss(q_m3h, dischargeParams.lengthM, dischargeParams.diameterM, dischargeParams.roughnessM, fluid);
      const minor = this.minorLosses(q_m3h, dischargeParams.diameterM, dischargeParams.sumK);
      totalFriction += disch.hf + minor;
    }

    return staticHeadM + totalFriction + valveDeltaH;
  }

  /**
   * Leyes de afinidad para variación de velocidad (VFD) y recorte de impulsor
   */
  static applyAffinity(ptsQ, ptsH, ptsEff, ptsPower, ptsNpsh, speedRatio = 1.0, diamRatio = 1.0) {
    const s = Number(speedRatio);
    const d = Number(diamRatio);
    
    const scaleQ = s * d;
    const scaleH = Math.pow(s, 2) * Math.pow(d, 2);
    const scaleP = Math.pow(s, 3) * Math.pow(d, 3);
    const scaleNpsh = Math.pow(s, 2); // NPSHr varía aprox con N²

    const q_scaled = ptsQ.map(q => q * scaleQ);
    const h_scaled = ptsH.map(h => h * scaleH);
    const eff_scaled = ptsEff.map(eff => eff); // La eficiencia se preserva en primera aproximación
    const power_scaled = ptsPower ? ptsPower.map(p => p * scaleP) : null;
    const npsh_scaled = ptsNpsh ? ptsNpsh.map(n => n * scaleNpsh) : null;

    return {
      q: q_scaled,
      h: h_scaled,
      eff: eff_scaled,
      power: power_scaled,
      npshr: npsh_scaled
    };
  }

  /**
   * Cálculo de NPSHa (Net Positive Suction Head Available)
   * NPSHa = (P_suct_abs - P_v) / (rho * g) + Z_suct - h_f_suct
   */
  static calculateNPSHa(pSuctionBarAbs, zSuctionM, hfSuctionM, fluid) {
    const pAbsPa = Number(pSuctionBarAbs) * 100000;
    const rhoG = fluid.density * this.G;
    const headPressure = (pAbsPa - fluid.vaporPressure) / rhoG;
    const npsha = headPressure + Number(zSuctionM) - Number(hfSuctionM);
    return Math.max(0, npsha);
  }

  /**
   * Solver del Punto de Operación: H_pump(Q) = H_sys(Q)
   * Método numérico de Bisección / Regula Falsi con tolerancia de 0.001 m3/h
   */
  static solveOperatingPoint(pumpInterp, systemEvalFn, qMin = 0, qMax = 500) {
    const f = (q) => pumpInterp.evaluate(q) - systemEvalFn(q);

    // Verificar si en q=0 la bomba supera la altura estática
    const f0 = f(qMin);
    if (f0 < 0) {
      return {
        solved: false,
        reason: "La altura de la bomba a caudal cero (Shutoff Head) es menor que la altura estática del sistema. No hay flujo.",
        q: 0,
        h: pumpInterp.evaluate(0)
      };
    }

    // Buscar intervalo donde cambia de signo
    let a = qMin, b = qMax;
    let step = (b - a) / 50;
    let foundBracket = false;

    for (let q = a; q <= b; q += step) {
      if (f(q) <= 0) {
        b = q;
        a = q - step;
        foundBracket = true;
        break;
      }
    }

    if (!foundBracket) {
      // Probar expandir b
      b = qMax * 1.5;
      if (f(b) <= 0) {
        a = qMax;
        foundBracket = true;
      } else {
        return {
          solved: false,
          reason: "No se encontró punto de intersección dentro del rango admisible de caudales.",
          q: null,
          h: null
        };
      }
    }

    // Bisección refinada
    let iter = 0;
    let mid = (a + b) / 2;
    while ((b - a) > 0.0001 && iter < 100) {
      mid = (a + b) / 2;
      const val = f(mid);
      if (Math.abs(val) < 1e-6) break;
      if (val > 0) a = mid;
      else b = mid;
      iter++;
    }

    const q_op = mid;
    const h_op = pumpInterp.evaluate(q_op);

    return {
      solved: true,
      q_op: q_op,
      h_op: h_op,
      iterations: iter
    };
  }

  /**
   * Cálculo de Potencia y Eficiencia
   */
  static calculatePower(q_m3h, h_m, effPercent, fluid, motorEfficiency = 0.94) {
    if (q_m3h <= 0 || h_m <= 0) {
      return { p_hydraulic_kw: 0, p_shaft_kw: 0, p_electrical_kw: 0 };
    }
    const q_m3s = q_m3h / 3600;
    const pHydraulicKw = (fluid.density * this.G * q_m3s * h_m) / 1000;
    const eff = Math.max(1, Math.min(100, Number(effPercent))) / 100;
    const pShaftKw = pHydraulicKw / eff;
    const pElectricalKw = pShaftKw / (motorEfficiency || 0.94);

    return {
      p_hydraulic_kw: Math.round(pHydraulicKw * 100) / 100,
      p_shaft_kw: Math.round(pShaftKw * 100) / 100,
      p_electrical_kw: Math.round(pElectricalKw * 100) / 100
    };
  }

  /**
   * Cálculo de ciclo de vida / Costo energético anual (OPEX)
   */
  static calculateLCC(pElectricalKw, hoursPerYear = 8000, tariffUsdPerKwh = 0.12) {
    const annualKwh = pElectricalKw * hoursPerYear;
    const annualCost = annualKwh * tariffUsdPerKwh;
    return {
      annual_kwh: Math.round(annualKwh),
      annual_cost_usd: Math.round(annualCost),
      hours: hoursPerYear,
      tariff: tariffUsdPerKwh
    };
  }
}

// Exportación compatible para Node y Browser
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { PchipInterpolator, FluidProperties, HydraulicsEngine };
}
