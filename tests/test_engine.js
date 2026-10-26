const assert = require('assert');
const { PchipInterpolator, FluidProperties, HydraulicsEngine } = require('../js/pump-engine.js');

console.log("=== INICIANDO SUITE DE PRUEBAS PARA PUMP-ENGINE ===");

// TEST 1: PCHIP Interpolation
console.log("Test 1: PCHIP Interpolación y Monotonía");
const xs = [0, 50, 100, 150, 200];
const ys = [45, 43, 39, 32, 20]; // Curva de bomba decreciente
const interp = new PchipInterpolator(xs, ys);

// Verifica nodos exactos
for (let i = 0; i < xs.length; i++) {
  assert.strictEqual(Math.round(interp.evaluate(xs[i])), ys[i], `Nodo ${xs[i]} debe coincidir exactamente`);
}
// Verifica monotonía decreciente
let prev = interp.evaluate(0);
for (let q = 10; q <= 200; q += 10) {
  const current = interp.evaluate(q);
  assert.ok(current <= prev + 1e-6, `Curva debe ser monótona decreciente en q=${q}`);
  prev = current;
}
console.log("  -> OK: Interpolación monótona PCHIP verificada.");

// TEST 2: Propiedades del Agua
console.log("Test 2: Termo-propiedades del Agua (20°C y 80°C)");
const water20 = FluidProperties.waterProperties(20);
assert.ok(water20.density >= 997 && water20.density <= 999, `Densidad a 20°C debe rondar 998 kg/m3 (obtenido ${water20.density})`);
assert.ok(water20.vaporPressure >= 2300 && water20.vaporPressure <= 2400, `Presión de vapor a 20°C debe rondar 2340 Pa (obtenido ${water20.vaporPressure})`);

const water80 = FluidProperties.waterProperties(80);
assert.ok(water80.density < water20.density, "Densidad a 80°C debe ser menor que a 20°C");
assert.ok(water80.vaporPressure > 45000 && water80.vaporPressure < 50000, `Presión de vapor a 80°C debe rondar 47.3 kPa (obtenido ${water80.vaporPressure})`);
console.log("  -> OK: Propiedades térmicas y de vapor validadas.");

// TEST 3: Darcy-Weisbach & Swamee-Jain
console.log("Test 3: Hidráulica y Factor de Fricción");
// Laminar Re = 1000 -> f = 64 / 1000 = 0.064
const fLam = HydraulicsEngine.frictionFactor(1000, 0.000045, 0.1);
assert.strictEqual(Math.round(fLam * 1000) / 1000, 0.064, "Régimen laminar f=64/Re");

// Turbulento Re = 100,000, Acero comercial e=0.045mm, D=100mm (e/D = 0.00045)
const fTurb = HydraulicsEngine.frictionFactor(100000, 0.000045, 0.1);
assert.ok(fTurb >= 0.018 && fTurb <= 0.022, `Factor turbulento debe estar entre 0.018 y 0.022 (obtenido ${fTurb})`);
console.log("  -> OK: Factores de fricción verificados.");

// TEST 4: Solver del Punto de Operación
console.log("Test 4: Solver de Punto de Operación (H_pump = H_sys)");
// Sistema: H_sys = 15 + 0.0006 * Q^2
const sysFn = (q) => 15 + 0.0006 * Math.pow(q, 2);
const sol = HydraulicsEngine.solveOperatingPoint(interp, sysFn, 0, 200);
assert.ok(sol.solved, "Debe resolver el punto de operación");
assert.ok(sol.q_op > 100 && sol.q_op < 160, `Caudal de operación esperado ~135 m3/h (obtenido ${sol.q_op})`);
const hPumpOp = interp.evaluate(sol.q_op);
const hSysOp = sysFn(sol.q_op);
assert.ok(Math.abs(hPumpOp - hSysOp) < 0.01, `H_pump (${hPumpOp}) debe igualar H_sys (${hSysOp})`);
console.log(`  -> OK: Punto de operación resuelto en Q=${sol.q_op.toFixed(2)} m³/h, H=${sol.h_op.toFixed(2)} m.`);

// TEST 5: Análisis de NPSH y Cavitación
console.log("Test 5: Análisis de Cavitación NPSHa vs NPSHr");
// Presión atmosférica 1.013 bar abs, depósito 2 m sobre bomba (en carga), pérdidas succión 0.5 m, agua 20°C
const npsha = HydraulicsEngine.calculateNPSHa(1.013, 2.0, 0.5, water20);
// Head atmosférico = 101300 / (998.2 * 9.80665) = 10.35 m
// Head vapor = 2338 / (998.2 * 9.80665) = 0.239 m
// NPSHa = 10.35 + 2.0 - 0.5 - 0.24 = 11.61 m
assert.ok(Math.abs(npsha - 11.61) < 0.2, `NPSHa esperado ~11.6 m (obtenido ${npsha.toFixed(2)} m)`);
console.log(`  -> OK: NPSHa calculado con precisión: ${npsha.toFixed(2)} m.`);

// TEST 6: Leyes de Afinidad (VFD)
console.log("Test 6: Leyes de Afinidad por Velocidad Variable");
const affinity = HydraulicsEngine.applyAffinity([100], [40], [75], [15], [3], 0.8, 1.0);
assert.strictEqual(affinity.q[0], 80, "Q debe escalar proporcional a N (100 * 0.8 = 80)");
assert.strictEqual(Math.round(affinity.h[0] * 100) / 100, 25.6, "H debe escalar con N^2 (40 * 0.64 = 25.6)");
assert.strictEqual(Math.round(affinity.power[0] * 100) / 100, 7.68, "P debe escalar con N^3 (15 * 0.512 = 7.68)");
console.log("  -> OK: Leyes de afinidad VFD verificadas.");

// TEST 7: Potencia y LCC
console.log("Test 7: Potencia al Freno y Auditoría Energética");
const pwr = HydraulicsEngine.calculatePower(120, 35, 78, water20, 0.94);
assert.ok(pwr.p_shaft_kw > 14 && pwr.p_shaft_kw < 16, `Potencia al eje esperada ~14.6 kW (obtenida ${pwr.p_shaft_kw})`);
const lcc = HydraulicsEngine.calculateLCC(pwr.p_electrical_kw, 8000, 0.12);
assert.ok(lcc.annual_cost_usd > 10000, `Costo anual OPEX esperado > $10,000 USD (obtenido $${lcc.annual_cost_usd})`);
console.log(`  -> OK: Potencia=${pwr.p_shaft_kw} kW, Costo Anual=$${lcc.annual_cost_usd} USD.`);

console.log("\n==========================================");
console.log(" TODOS LOS TESTS DE PUMP-ENGINE PASARON (7/7)");
console.log("==========================================");
