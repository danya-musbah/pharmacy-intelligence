const CHART_COLORS = {
  primary: "#0b5d52",
  secondary: "#1f5673",
  success: "#2e7d5b",
  warning: "#b8791a",
  danger: "#b23a3a",
  grid: "#e2e6e3",
  text: "#5b655f",
};

const chartRegistry = {};

function destroyChart(canvasId) {
  if (chartRegistry[canvasId]) {
    chartRegistry[canvasId].destroy();
    delete chartRegistry[canvasId];
  }
}

function baseOptions(extra) {
  return Object.assign({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: { rtl: true, titleFont: { family: "IBM Plex Sans Arabic" }, bodyFont: { family: "IBM Plex Sans Arabic" } },
    },
    scales: {
      x: { grid: { display: false }, ticks: { color: CHART_COLORS.text, font: { size: 11 } } },
      y: { grid: { color: CHART_COLORS.grid }, ticks: { color: CHART_COLORS.text, font: { size: 11 } } },
    },
  }, extra || {});
}

function renderLineChart(canvasId, labels, series, opts = {}) {
  destroyChart(canvasId);
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  chartRegistry[canvasId] = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: series.map((s) => ({
        label: s.label,
        data: s.data,
        borderColor: s.color || CHART_COLORS.primary,
        backgroundColor: (s.color || CHART_COLORS.primary) + "22",
        fill: s.fill !== false,
        tension: 0.3,
        pointRadius: 0,
        borderWidth: 2,
      })),
    },
    options: baseOptions(opts),
  });
}

function renderBarChart(canvasId, labels, data, opts = {}) {
  destroyChart(canvasId);
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  chartRegistry[canvasId] = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: opts.color || CHART_COLORS.primary,
        borderRadius: 4,
        maxBarThickness: 34,
      }],
    },
    options: baseOptions(opts),
  });
}

function renderForecastChart(canvasId, history, forecast) {
  destroyChart(canvasId);
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  const labels = [...history.map((h) => h.date), ...forecast.map((f) => f.date)];
  const actual = [...history.map((h) => h.actual), ...forecast.map(() => null)];
  const fc = [...history.map(() => null), ...forecast.map((f) => f.forecast)];
  const high = [...history.map(() => null), ...forecast.map((f) => f.high)];
  const low = [...history.map(() => null), ...forecast.map((f) => f.low)];

  chartRegistry[canvasId] = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        { label: "high", data: high, borderColor: "transparent", backgroundColor: CHART_COLORS.primary + "18", fill: "+1", pointRadius: 0 },
        { label: "low", data: low, borderColor: "transparent", pointRadius: 0, fill: false },
        { label: "actual", data: actual, borderColor: CHART_COLORS.secondary, backgroundColor: "transparent", pointRadius: 0, borderWidth: 2, tension: 0.25 },
        { label: "forecast", data: fc, borderColor: CHART_COLORS.primary, borderDash: [5, 4], backgroundColor: "transparent", pointRadius: 0, borderWidth: 2, tension: 0.25 },
      ],
    },
    options: baseOptions({ plugins: { legend: { display: false } } }),
  });
}
