/**
 * app.js - Lógica de interfaz y visualización para pump-system-analyzer
 */

const PRESETS = {
  cooling_water: {
    name: "Agua de Proceso / Enfriamiento (Circuito Cerrado)",
    pumpName: "KSB Etanorm 100-250 (1450 RPM)",
    speedRpm: 1450,
    impellerNominalMm: 250,
    speedRatio: 1.0,
    diamRatio: 1.0,
    points: [
      { q: 0, h: 42.0, eff: 0, power: 8.5, npsh: 1.8 },
      { q: 50, h: 40.5, eff: 52, power: 10.8, npsh: 2.1 },
      { q: 100, h: 37.8, eff: 74, power: 13.9, npsh: 2.6 },
      { q: 150, h: 33.5, eff: 82, power: 16.8, npsh: 3.4 },
      { q: 200, h: 27.2, eff: 79, power: 19.1, npsh: 4.8 },
      { q: 240, h: 20.0, eff: 68, power: 20.2, npsh: 6.5 }
    ],
    fluidTempC: 25,
    suction: {
      lengthM: 6.0,
      diameterMm: 150,
      roughnessMm: 0.045, // Acero comercial
      sumK: 1.5, // 1 válvula mariposa + 1 codo 90
      pSurfaceBarAbs: 1.013,
      liquidLevelM: 2.5, // 2.5 m sobre bomba (en carga)
      pumpCenterlineM: 0.0
    },
    discharge: {
      lengthM: 85.0,
      diameterMm: 125,
      roughnessMm: 0.045,
      sumK: 4.8, // Válvula de retención + compuerta + 4 codos
      pDischargeBarAbs: 1.013,
      dischargeLevelM: 14.5
    },
    valve: {
      enabled: false,
      openingPct: 100,
      cv: 350
    },
    staging: "single", // "single", "parallel", "series"
    energy: {
      hoursPerYear: 8000,
      tariffUsdPerKwh: 0.12,
      motorEffPct: 94
    }
  },

  hot_water_cavitation: {
    name: "Aspiración en Pozo / Agua Caliente (Riesgo Cavitación)",
    pumpName: "Bomba Centrífuga Sanitaria / Industrial",
    speedRpm: 2900,
    impellerNominalMm: 180,
    speedRatio: 1.0,
    diamRatio: 1.0,
    points: [
      { q: 0, h: 55.0, eff: 0, power: 5.2, npsh: 2.2 },
      { q: 25, h: 52.0, eff: 58, power: 7.0, npsh: 2.5 },
      { q: 50, h: 47.0, eff: 76, power: 9.1, npsh: 3.1 },
      { q: 75, h: 39.5, eff: 79, power: 10.8, npsh: 4.2 },
      { q: 100, h: 28.0, eff: 65, power: 12.0, npsh: 6.8 }
    ],
    fluidTempC: 65, // 65°C aumenta fuertemente P_vapor
    suction: {
      lengthM: 12.0,
      diameterMm: 80,
      roughnessMm: 0.045,
      sumK: 3.5, // Válvula de pie con canasto + codos
      pSurfaceBarAbs: 1.013,
      liquidLevelM: -2.2, // Depósito 2.2 m por debajo de la bomba
      pumpCenterlineM: 0.0
    },
    discharge: {
      lengthM: 45.0,
      diameterMm: 65,
      roughnessMm: 0.045,
      sumK: 3.2,
      pDischargeBarAbs: 1.013,
      dischargeLevelM: 18.0
    },
    valve: {
      enabled: false,
      openingPct: 100,
      cv: 180
    },
    staging: "single",
    energy: {
      hoursPerYear: 6000,
      tariffUsdPerKwh: 0.14,
      motorEffPct: 92
    }
  },

  high_pressure_boiler: {
    name: "Alimentación de Caldera de Alta Presión (Multietapa)",
    pumpName: "Multietapa Vertical (e.g. Grundfos CR 45)",
    speedRpm: 2950,
    impellerNominalMm: 160,
    speedRatio: 1.0,
    diamRatio: 1.0,
    points: [
      { q: 0, h: 140.0, eff: 0, power: 9.5, npsh: 1.5 },
      { q: 15, h: 135.0, eff: 55, power: 12.5, npsh: 1.9 },
      { q: 30, h: 124.0, eff: 72, power: 16.2, npsh: 2.5 },
      { q: 45, h: 108.0, eff: 77, power: 19.8, npsh: 3.4 },
      { q: 60, h: 85.0, eff: 68, power: 22.1, npsh: 5.1 }
    ],
    fluidTempC: 85,
    suction: {
      lengthM: 4.0,
      diameterMm: 100,
      roughnessMm: 0.015, // Inoxidable
      sumK: 1.2,
      pSurfaceBarAbs: 1.5, // Desaireador presurizado a 1.5 bar abs
      liquidLevelM: 4.0, // Tanque nodriza elevado 4 m
      pumpCenterlineM: 0.0
    },
    discharge: {
      lengthM: 60.0,
      diameterMm: 65,
      roughnessMm: 0.015,
      sumK: 6.5,
      pDischargeBarAbs: 8.5, // Caldera a 8.5 bar abs
      dischargeLevelM: 8.0
    },
    valve: {
      enabled: false,
      openingPct: 100,
      cv: 90
    },
    staging: "single",
    energy: {
      hoursPerYear: 8400,
      tariffUsdPerKwh: 0.11,
      motorEffPct: 95
    }
  }
};

let currentConfig = JSON.parse(JSON.stringify(PRESETS.cooling_water));
let mainChart = null;
let npshChart = null;

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initPresetSelector();
  populateInputsFromConfig();
  attachEventListeners();
  initCharts();
  recalculateAll();
});

function initTabs() {
  const tabs = document.querySelectorAll('.nav-tab-btn');
  tabs.forEach(btn => {
    btn.addEventListener('click', () => {
      tabs.forEach(t => {
        t.classList.remove('active-tab');
        t.classList.add('inactive-tab');
      });
      btn.classList.add('active-tab');
      btn.classList.remove('inactive-tab');

      const targetId = btn.getAttribute('data-tab');
      document.querySelectorAll('.tab-content').forEach(sec => {
        sec.classList.add('hidden');
      });
      const activeSection = document.getElementById(`tab-${targetId}`);
      if (activeSection) activeSection.classList.remove('hidden');

      if (mainChart) mainChart.resize();
      if (npshChart) npshChart.resize();
    });
  });
}

function initPresetSelector() {
  const sel = document.getElementById('preset-selector');
  if (!sel) return;
  sel.innerHTML = Object.keys(PRESETS).map(key => `
    <option value="${key}">${PRESETS[key].name}</option>
  `).join('');

  sel.addEventListener('change', (e) => {
    const key = e.target.value;
    if (PRESETS[key]) {
      currentConfig = JSON.parse(JSON.stringify(PRESETS[key]));
      populateInputsFromConfig();
      recalculateAll();
    }
  });
}

function populateInputsFromConfig() {
  document.getElementById('pump-name').value = currentConfig.pumpName;
  document.getElementById('speed-rpm').value = currentConfig.speedRpm;
  document.getElementById('vfd-speed-slider').value = Math.round(currentConfig.speedRatio * 100);
  document.getElementById('vfd-speed-val').textContent = `${Math.round(currentConfig.speedRatio * 100)} %`;
  document.getElementById('impeller-trim-slider').value = Math.round(currentConfig.diamRatio * 100);
  document.getElementById('impeller-trim-val').textContent = `${Math.round(currentConfig.diamRatio * 100)} %`;

  document.getElementById('fluid-temp').value = currentConfig.fluidTempC;
  document.getElementById('suct-len').value = currentConfig.suction.lengthM;
  document.getElementById('suct-diam').value = currentConfig.suction.diameterMm;
  document.getElementById('suct-rough').value = currentConfig.suction.roughnessMm;
  document.getElementById('suct-k').value = currentConfig.suction.sumK;
  document.getElementById('suct-p-abs').value = currentConfig.suction.pSurfaceBarAbs;
  document.getElementById('suct-z').value = currentConfig.suction.liquidLevelM;

  document.getElementById('disch-len').value = currentConfig.discharge.lengthM;
  document.getElementById('disch-diam').value = currentConfig.discharge.diameterMm;
  document.getElementById('disch-rough').value = currentConfig.discharge.roughnessMm;
  document.getElementById('disch-k').value = currentConfig.discharge.sumK;
  document.getElementById('disch-p-abs').value = currentConfig.discharge.pDischargeBarAbs;
  document.getElementById('disch-z').value = currentConfig.discharge.dischargeLevelM;

  document.getElementById('staging-mode').value = currentConfig.staging || "single";
  document.getElementById('energy-hours').value = currentConfig.energy.hoursPerYear;
  document.getElementById('energy-tariff').value = currentConfig.energy.tariffUsdPerKwh;
  document.getElementById('motor-eff').value = currentConfig.energy.motorEffPct;

  renderPointsTable();
}

function renderPointsTable() {
  const tbody = document.getElementById('points-tbody');
  if (!tbody) return;
  tbody.innerHTML = '';

  currentConfig.points.forEach((pt, idx) => {
    const tr = document.createElement('tr');
    tr.className = "border-b border-slate-800 text-xs hover:bg-slate-800/40";
    tr.innerHTML = `
      <td class="p-2"><input type="number" step="1" value="${pt.q}" class="w-20 px-2 py-1 table-pt-input" data-idx="${idx}" data-field="q"></td>
      <td class="p-2"><input type="number" step="0.1" value="${pt.h}" class="w-20 px-2 py-1 table-pt-input" data-idx="${idx}" data-field="h"></td>
      <td class="p-2"><input type="number" step="0.5" value="${pt.eff}" class="w-20 px-2 py-1 table-pt-input" data-idx="${idx}" data-field="eff"></td>
      <td class="p-2"><input type="number" step="0.1" value="${pt.power}" class="w-20 px-2 py-1 table-pt-input" data-idx="${idx}" data-field="power"></td>
      <td class="p-2"><input type="number" step="0.1" value="${pt.npsh}" class="w-20 px-2 py-1 table-pt-input" data-idx="${idx}" data-field="npsh"></td>
      <td class="p-2 text-center">
        <button class="text-rose-400 hover:text-rose-300 delete-pt-btn" data-idx="${idx}"><i class="fa-solid fa-trash"></i></button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  tbody.querySelectorAll('.table-pt-input').forEach(inp => {
    inp.addEventListener('change', (e) => {
      const idx = Number(e.target.dataset.idx);
      const field = e.target.dataset.field;
      currentConfig.points[idx][field] = Number(e.target.value);
      recalculateAll();
    });
  });

  tbody.querySelectorAll('.delete-pt-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const idx = Number(btn.closest('button').dataset.idx);
      if (currentConfig.points.length > 2) {
        currentConfig.points.splice(idx, 1);
        renderPointsTable();
        recalculateAll();
      } else {
        alert("Se requieren al menos 2 puntos para definir la curva de la bomba.");
      }
    });
  });
}

function attachEventListeners() {
  document.getElementById('add-point-btn')?.addEventListener('click', () => {
    const last = currentConfig.points[currentConfig.points.length - 1];
    currentConfig.points.push({
      q: last ? last.q + 30 : 50,
      h: last ? Math.max(0, last.h - 5) : 30,
      eff: 70,
      power: last ? last.power + 2 : 10,
      npsh: last ? last.npsh + 1 : 3
    });
    renderPointsTable();
    recalculateAll();
  });

  document.getElementById('vfd-speed-slider')?.addEventListener('input', (e) => {
    const val = Number(e.target.value);
    currentConfig.speedRatio = val / 100;
    document.getElementById('vfd-speed-val').textContent = `${val} %`;
    recalculateAll();
  });

  document.getElementById('impeller-trim-slider')?.addEventListener('input', (e) => {
    const val = Number(e.target.value);
    currentConfig.diamRatio = val / 100;
    document.getElementById('impeller-trim-val').textContent = `${val} %`;
    recalculateAll();
  });

  const boundInputs = [
    'fluid-temp', 'suct-len', 'suct-diam', 'suct-rough', 'suct-k', 'suct-p-abs', 'suct-z',
    'disch-len', 'disch-diam', 'disch-rough', 'disch-k', 'disch-p-abs', 'disch-z',
    'staging-mode', 'energy-hours', 'energy-tariff', 'motor-eff'
  ];

  boundInputs.forEach(id => {
    document.getElementById(id)?.addEventListener('input', () => {
      syncConfigFromInputs();
      recalculateAll();
    });
  });

  // Export Buttons
  document.getElementById('export-json-btn')?.addEventListener('click', exportJsonProject);
  document.getElementById('export-csv-btn')?.addEventListener('click', exportCsvData);
  document.getElementById('print-report-btn')?.addEventListener('click', () => window.print());
}

function syncConfigFromInputs() {
  currentConfig.fluidTempC = Number(document.getElementById('fluid-temp').value);
  currentConfig.suction.lengthM = Number(document.getElementById('suct-len').value);
  currentConfig.suction.diameterMm = Number(document.getElementById('suct-diam').value);
  currentConfig.suction.roughnessMm = Number(document.getElementById('suct-rough').value);
  currentConfig.suction.sumK = Number(document.getElementById('suct-k').value);
  currentConfig.suction.pSurfaceBarAbs = Number(document.getElementById('suct-p-abs').value);
  currentConfig.suction.liquidLevelM = Number(document.getElementById('suct-z').value);

  currentConfig.discharge.lengthM = Number(document.getElementById('disch-len').value);
  currentConfig.discharge.diameterMm = Number(document.getElementById('disch-diam').value);
  currentConfig.discharge.roughnessMm = Number(document.getElementById('disch-rough').value);
  currentConfig.discharge.sumK = Number(document.getElementById('disch-k').value);
  currentConfig.discharge.pDischargeBarAbs = Number(document.getElementById('disch-p-abs').value);
  currentConfig.discharge.dischargeLevelM = Number(document.getElementById('disch-z').value);

  currentConfig.staging = document.getElementById('staging-mode').value;
  currentConfig.energy.hoursPerYear = Number(document.getElementById('energy-hours').value);
  currentConfig.energy.tariffUsdPerKwh = Number(document.getElementById('energy-tariff').value);
  currentConfig.energy.motorEffPct = Number(document.getElementById('motor-eff').value);
}

function recalculateAll() {
  const fluid = FluidProperties.waterProperties(currentConfig.fluidTempC);
  document.getElementById('fluid-density-val').textContent = `${fluid.density} kg/m³`;
  document.getElementById('fluid-vapor-val').textContent = `${(fluid.vaporPressure / 1000).toFixed(2)} kPa`;
  document.getElementById('fluid-visc-val').textContent = `${(fluid.viscosity * 1000).toFixed(2)} mPa.s`;

  // Curvas de catálogo
  const ptsQ = currentConfig.points.map(p => p.q);
  const ptsH = currentConfig.points.map(p => p.h);
  const ptsEff = currentConfig.points.map(p => p.eff);
  const ptsPwr = currentConfig.points.map(p => p.power);
  const ptsNpsh = currentConfig.points.map(p => p.npsh);

  // Aplicar leyes de afinidad
  const scaled = HydraulicsEngine.applyAffinity(
    ptsQ, ptsH, ptsEff, ptsPwr, ptsNpsh, 
    currentConfig.speedRatio, currentConfig.diamRatio
  );

  // Staging: Serie / Paralelo
  let effectiveQ = scaled.q;
  let effectiveH = scaled.h;
  if (currentConfig.staging === "parallel") {
    effectiveQ = scaled.q.map(q => q * 2);
  } else if (currentConfig.staging === "series") {
    effectiveH = scaled.h.map(h => h * 2);
  }

  const pumpInterp = new PchipInterpolator(effectiveQ, effectiveH);
  const effInterp = new PchipInterpolator(effectiveQ, scaled.eff);
  const npshInterp = new PchipInterpolator(effectiveQ, scaled.npshr);

  // Altura estática del sistema: delta_p / (rho*g) + delta_z
  const deltaPBar = currentConfig.discharge.pDischargeBarAbs - currentConfig.suction.pSurfaceBarAbs;
  const deltaPPa = deltaPBar * 100000;
  const hStaticP = deltaPPa / (fluid.density * HydraulicsEngine.G);
  const deltaZ = currentConfig.discharge.dischargeLevelM - currentConfig.suction.liquidLevelM;
  const totalStaticHead = hStaticP + deltaZ;

  // Parámetros de cañería
  const suctParams = {
    lengthM: currentConfig.suction.lengthM,
    diameterM: currentConfig.suction.diameterMm / 1000,
    roughnessM: currentConfig.suction.roughnessMm / 1000,
    sumK: currentConfig.suction.sumK
  };
  const dischParams = {
    lengthM: currentConfig.discharge.lengthM,
    diameterM: currentConfig.discharge.diameterMm / 1000,
    roughnessM: currentConfig.discharge.roughnessMm / 1000,
    sumK: currentConfig.discharge.sumK
  };

  const systemEvalFn = (q) => HydraulicsEngine.systemHead(q, totalStaticHead, suctParams, dischParams, fluid, 0);

  // Resolver punto de operación
  const qMaxSearch = Math.max(...effectiveQ) * 1.2;
  const solverRes = HydraulicsEngine.solveOperatingPoint(pumpInterp, systemEvalFn, 0, qMaxSearch);

  updateResultsDOM(solverRes, pumpInterp, effInterp, npshInterp, fluid, suctParams, dischParams, totalStaticHead);
  updateCharts(effectiveQ, pumpInterp, effInterp, npshInterp, systemEvalFn, solverRes, fluid, suctParams);
}

function updateResultsDOM(solverRes, pumpInterp, effInterp, npshInterp, fluid, suctParams, dischParams, staticHead) {
  if (!solverRes.solved) {
    document.getElementById('op-q').textContent = "--";
    document.getElementById('op-h').textContent = "--";
    document.getElementById('op-eff').textContent = "--";
    document.getElementById('op-power').textContent = "--";
    document.getElementById('op-npsh-margin').textContent = "Sin flujo";
    document.getElementById('npsh-status-badge').className = "px-2 py-0.5 rounded text-xs badge-danger";
    document.getElementById('npsh-status-badge').textContent = "NO OPERA";
    document.getElementById('diag-msg').textContent = solverRes.reason;
    return;
  }

  const q = solverRes.q_op;
  const h = solverRes.h_op;
  const eff = Math.max(0, effInterp.evaluate(q));
  const npshr = Math.max(0, npshInterp.evaluate(q));

  // Velocidades en cañerías
  const q_m3s = q / 3600;
  const vSuct = q_m3s / ((Math.PI * Math.pow(suctParams.diameterM, 2)) / 4);
  const vDisch = q_m3s / ((Math.PI * Math.pow(dischParams.diameterM, 2)) / 4);

  // Pérdidas en succión para NPSHa
  const suctLoss = HydraulicsEngine.pipeFrictionLoss(q, suctParams.lengthM, suctParams.diameterM, suctParams.roughnessM, fluid);
  const suctMinor = HydraulicsEngine.minorLosses(q, suctParams.diameterM, suctParams.sumK);
  const hfSuction = suctLoss.hf + suctMinor;

  const npsha = HydraulicsEngine.calculateNPSHa(
    currentConfig.suction.pSurfaceBarAbs,
    currentConfig.suction.liquidLevelM,
    hfSuction,
    fluid
  );

  const deltaNpsh = npsha - npshr;
  const npshRatio = npshr > 0 ? npsha / npshr : 99;

  // Potencias y LCC
  const power = HydraulicsEngine.calculatePower(q, h, eff, fluid, currentConfig.energy.motorEffPct / 100);
  const lcc = HydraulicsEngine.calculateLCC(power.p_electrical_kw, currentConfig.energy.hoursPerYear, currentConfig.energy.tariffUsdPerKwh);

  // Actualizar DOM
  document.getElementById('op-q').textContent = `${q.toFixed(1)} m³/h`;
  document.getElementById('op-h').textContent = `${h.toFixed(1)} m`;
  document.getElementById('op-eff').textContent = `${eff.toFixed(1)} %`;
  document.getElementById('op-power').textContent = `${power.p_shaft_kw.toFixed(1)} kW`;
  document.getElementById('op-electrical').textContent = `${power.p_electrical_kw.toFixed(1)} kW`;

  document.getElementById('res-npsha').textContent = `${npsha.toFixed(2)} m`;
  document.getElementById('res-npshr').textContent = `${npshr.toFixed(2)} m`;
  document.getElementById('res-delta-npsh').textContent = `${deltaNpsh.toFixed(2)} m`;
  document.getElementById('res-npsh-ratio').textContent = `${npshRatio.toFixed(2)}`;

  // Badge NPSH
  const badge = document.getElementById('npsh-status-badge');
  if (deltaNpsh >= 1.0 && npshRatio >= 1.2) {
    badge.className = "px-2.5 py-1 rounded text-xs font-bold badge-safe";
    badge.textContent = "SEGURO (Sin cavitación)";
  } else if (deltaNpsh >= 0.3 && npshRatio >= 1.05) {
    badge.className = "px-2.5 py-1 rounded text-xs font-bold badge-warning";
    badge.textContent = "MARGINAL (Vigilancia requerida)";
  } else {
    badge.className = "px-2.5 py-1 rounded text-xs font-bold badge-danger";
    badge.textContent = "PELIGRO DE CAVITACIÓN";
  }

  // Costo Operativo
  document.getElementById('op-annual-kwh').textContent = `${Math.round(lcc.annual_kwh).toLocaleString()} kWh/año`;
  document.getElementById('op-annual-cost').textContent = `$ ${Math.round(lcc.annual_cost_usd).toLocaleString()} USD/año`;
  document.getElementById('res-spec-energy').textContent = `${(power.p_electrical_kw / q).toFixed(3)} kWh/m³`;

  // Velocidades en tuberías
  document.getElementById('v-suct').textContent = `${vSuct.toFixed(2)} m/s`;
  document.getElementById('v-disch').textContent = `${vDisch.toFixed(2)} m/s`;

  // Diagnóstico
  let diagText = [];
  if (vSuct > 2.0) diagText.push(`⚠️ Velocidad en succión elevada (${vSuct.toFixed(2)} m/s > 2.0 m/s estándar). Aumente el diámetro de aspiración.`);
  if (vDisch > 3.5) diagText.push(`⚠️ Velocidad en impulsión elevada (${vDisch.toFixed(2)} m/s > 3.5 m/s). Riesgo de golpe de ariete y pérdidas excesivas.`);
  if (deltaNpsh < 0.5) diagText.push(`🚨 Margen NPSH insuficiente (${deltaNpsh.toFixed(2)} m < 0.5 m). Cavitación inminente: aumente la altura de carga o reduzca pérdidas.`);
  if (eff < 60) diagText.push(`ℹ️ La bomba está operando fuera de su zona óptima (BEP) con rendimiento bajo (${eff.toFixed(1)}%). Evalúe recortar impulsor o variar RPM.`);
  if (diagText.length === 0) diagText.push("✅ Sistema operando dentro de parámetros hidrodinámicos normativos recomendados (HI / API).");

  document.getElementById('diag-msg').innerHTML = diagText.join("<br>");
}

function initCharts() {
  const ctx1 = document.getElementById('mainCurveChart')?.getContext('2d');
  const ctx2 = document.getElementById('npshPowerChart')?.getContext('2d');

  if (ctx1) {
    mainChart = new Chart(ctx1, {
      type: 'line',
      data: {
        datasets: [
          {
            label: 'Curva de Bomba H-Q (m)',
            borderColor: '#38bdf8',
            backgroundColor: 'rgba(56, 189, 248, 0.1)',
            borderWidth: 3,
            data: [],
            yAxisID: 'y'
          },
          {
            label: 'Curva del Sistema H_sys (m)',
            borderColor: '#f59e0b',
            borderDash: [6, 4],
            borderWidth: 2.5,
            data: [],
            yAxisID: 'y'
          },
          {
            label: 'Punto de Operación',
            borderColor: '#ef4444',
            backgroundColor: '#ef4444',
            pointRadius: 8,
            pointHoverRadius: 10,
            showLine: false,
            data: [],
            yAxisID: 'y'
          },
          {
            label: 'Rendimiento η (%)',
            borderColor: '#10b981',
            borderWidth: 1.5,
            borderDash: [2, 2],
            data: [],
            yAxisID: 'y1'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { labels: { color: '#cbd5e1', font: { family: 'Consolas' } } },
          tooltip: { backgroundColor: '#0f172a', borderColor: '#334155', borderWidth: 1 }
        },
        scales: {
          x: {
            title: { display: true, text: 'Caudal Q (m³/h)', color: '#94a3b8' },
            grid: { color: '#1e293b' },
            ticks: { color: '#94a3b8' }
          },
          y: {
            title: { display: true, text: 'Altura Manométrica H (m)', color: '#38bdf8' },
            grid: { color: '#1e293b' },
            ticks: { color: '#38bdf8' },
            position: 'left'
          },
          y1: {
            title: { display: true, text: 'Rendimiento η (%)', color: '#10b981' },
            grid: { drawOnChartArea: false },
            ticks: { color: '#10b981' },
            position: 'right',
            min: 0,
            max: 100
          }
        }
      }
    });
  }

  if (ctx2) {
    npshChart = new Chart(ctx2, {
      type: 'line',
      data: {
        datasets: [
          {
            label: 'NPSH Requerido (m)',
            borderColor: '#ec4899',
            borderWidth: 2.5,
            data: [],
            yAxisID: 'y'
          },
          {
            label: 'NPSH Disponible (m)',
            borderColor: '#06b6d4',
            borderWidth: 2,
            borderDash: [4, 4],
            data: [],
            yAxisID: 'y'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: '#cbd5e1' } }
        },
        scales: {
          x: {
            title: { display: true, text: 'Caudal Q (m³/h)', color: '#94a3b8' },
            grid: { color: '#1e293b' },
            ticks: { color: '#94a3b8' }
          },
          y: {
            title: { display: true, text: 'NPSH (m)', color: '#ec4899' },
            grid: { color: '#1e293b' },
            ticks: { color: '#ec4899' },
            min: 0
          }
        }
      }
    });
  }
}

function updateCharts(effectiveQ, pumpInterp, effInterp, npshInterp, systemEvalFn, solverRes, fluid, suctParams) {
  if (!mainChart || !npshChart) return;

  const qMax = Math.max(...effectiveQ) * 1.15;
  const numPts = 60;
  const step = qMax / numPts;

  const dataPumpH = [];
  const dataSysH = [];
  const dataEff = [];
  const dataNpshr = [];
  const dataNpsha = [];

  for (let q = 0; q <= qMax; q += step) {
    const hP = Math.max(0, pumpInterp.evaluate(q));
    const hS = systemEvalFn(q);
    const eff = Math.max(0, effInterp.evaluate(q));
    const nr = Math.max(0, npshInterp.evaluate(q));

    // NPSHa variable con Q
    const suctLoss = HydraulicsEngine.pipeFrictionLoss(q, suctParams.lengthM, suctParams.diameterM, suctParams.roughnessM, fluid);
    const suctMinor = HydraulicsEngine.minorLosses(q, suctParams.diameterM, suctParams.sumK);
    const na = HydraulicsEngine.calculateNPSHa(
      currentConfig.suction.pSurfaceBarAbs,
      currentConfig.suction.liquidLevelM,
      suctLoss.hf + suctMinor,
      fluid
    );

    dataPumpH.push({ x: Number(q.toFixed(1)), y: Number(hP.toFixed(2)) });
    dataSysH.push({ x: Number(q.toFixed(1)), y: Number(hS.toFixed(2)) });
    dataEff.push({ x: Number(q.toFixed(1)), y: Number(eff.toFixed(1)) });
    dataNpshr.push({ x: Number(q.toFixed(1)), y: Number(nr.toFixed(2)) });
    dataNpsha.push({ x: Number(q.toFixed(1)), y: Number(na.toFixed(2)) });
  }

  mainChart.data.datasets[0].data = dataPumpH;
  mainChart.data.datasets[1].data = dataSysH;
  mainChart.data.datasets[2].data = solverRes.solved ? [{ x: Number(solverRes.q_op.toFixed(1)), y: Number(solverRes.h_op.toFixed(2)) }] : [];
  mainChart.data.datasets[3].data = dataEff;
  mainChart.update();

  npshChart.data.datasets[0].data = dataNpshr;
  npshChart.data.datasets[1].data = dataNpsha;
  npshChart.update();
}

function exportJsonProject() {
  const jsonStr = JSON.stringify(currentConfig, null, 2);
  const blob = new Blob([jsonStr], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `pump_analysis_${currentConfig.pumpName.replace(/\s+/g, '_')}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

function exportCsvData() {
  let csv = "Caudal_m3h,Altura_Bomba_m,Rendimiento_pct,Potencia_kW,NPSHr_m\n";
  currentConfig.points.forEach(p => {
    csv += `${p.q},${p.h},${p.eff},${p.power},${p.npsh}\n`;
  });
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = "curva_bomba.csv";
  a.click();
  URL.revokeObjectURL(url);
}
