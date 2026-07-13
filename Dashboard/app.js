/**
 * app.js
 * Smart Environment Monitoring — dashboard client.
 *
 * Responsibilities:
 *   1. Poll the Flask backend (CONFIG.ENDPOINT) on an interval.
 *   2. Render live sensor cards, sparklines, and trend charts.
 *   3. Track connection health and surface a friendly offline state.
 *   4. Flag out-of-range readings via the alert banner.
 *
 * Kept dependency-free aside from Chart.js so it can be dropped into any
 * static host in front of the Flask API.
 */

(function () {
  "use strict";

  // ---------------------------------------------------------------------
  // DOM references
  // ---------------------------------------------------------------------
  const el = {
    connectionPill: document.getElementById("connectionPill"),
    connectionText: document.getElementById("connectionText"),
    lastUpdated: document.getElementById("lastUpdated"),
    exportButton: document.getElementById("exportButton"),

    alertBanner: document.getElementById("alertBanner"),
    alertTitle: document.getElementById("alertTitle"),
    alertDetail: document.getElementById("alertDetail"),

    offlineBanner: document.getElementById("offlineBanner"),
    offlineEndpoint: document.getElementById("offlineEndpoint"),
    footerEndpoint: document.getElementById("footerEndpoint"),
    footerInterval: document.getElementById("footerInterval"),

    tempCard: document.getElementById("tempCard"),
    tempValue: document.getElementById("tempValue"),
    tempTrend: document.getElementById("tempTrend"),
    tempRangeLabel: document.getElementById("tempRangeLabel"),
    tempPoints: document.getElementById("tempPoints"),

    historyBody: document.getElementById("historyBody"),
    historyCount: document.getElementById("historyCount"),

    humCard: document.getElementById("humCard"),
    humValue: document.getElementById("humValue"),
    humTrend: document.getElementById("humTrend"),
    humRangeLabel: document.getElementById("humRangeLabel"),
    humPoints: document.getElementById("humPoints"),
  };

  // ---------------------------------------------------------------------
  // State
  // ---------------------------------------------------------------------
  const state = {
    history: {
      labels: [],
      temperature: [],
      humidity: [],
    },
    consecutiveFailures: 0,
    isOnline: false,
    hasLoadedOnce: false,
    hasHistorySeeded: false,
    lastTemp: null,
    lastHum: null,
  };

  // ---------------------------------------------------------------------
  // Chart.js setup (dark theme matching the CSS token palette)
  // ---------------------------------------------------------------------
  const palette = {
    temp: "#f97316",
    tempFill: "rgba(249, 115, 22, 0.14)",
    hum: "#0ea5e9",
    humFill: "rgba(14, 165, 233, 0.14)",
    grid: "rgba(15, 23, 42, 0.08)",
    text: "#475569",
  };

  const chartsAvailable = typeof Chart !== "undefined";

  if (chartsAvailable) {
    Chart.defaults.font.family = "'JetBrains Mono', monospace";
    Chart.defaults.color = palette.text;
  }

  function baseLineOptions(unit) {
    return {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 300 },
      interaction: { intersect: false, mode: "index" },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#ffffff",
          borderColor: "#e2e8f0",
          borderWidth: 1,
          titleColor: "#0f172a",
          bodyColor: "#0f172a",
          padding: 10,
          callbacks: {
            label: (ctx) => ` ${ctx.formattedValue}${unit}`,
          },
        },
      },
      scales: {
        x: {
          grid: { color: palette.grid },
          ticks: { maxTicksLimit: 6, color: palette.text },
        },
        y: {
          grid: { color: palette.grid },
          ticks: { color: palette.text },
        },
      },
    };
  }

  function createChart(canvasId, config) {
    if (!chartsAvailable) {
      console.warn("[dashboard] Chart.js is not available; telemetry cards will still update.");
      return {
        data: config.data,
        update: () => {},
      };
    }

    return new Chart(document.getElementById(canvasId), config);
  }

  const tempChart = createChart("tempChart", {
    type: "line",
    data: {
      labels: [],
      datasets: [{
        data: [],
        borderColor: palette.temp,
        backgroundColor: palette.tempFill,
        fill: true,
        tension: 0.35,
        pointRadius: 0,
        borderWidth: 2,
      }],
    },
    options: baseLineOptions(CONFIG.THRESHOLDS.temperature.unit),
  });

  const humChart = createChart("humChart", {
    type: "line",
    data: {
      labels: [],
      datasets: [{
        data: [],
        borderColor: palette.hum,
        backgroundColor: palette.humFill,
        fill: true,
        tension: 0.35,
        pointRadius: 0,
        borderWidth: 2,
      }],
    },
    options: baseLineOptions("%"),
  });

  function sparklineOptions() {
    return {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      plugins: { legend: { display: false }, tooltip: { enabled: false } },
      elements: { point: { radius: 0 } },
      scales: {
        x: { display: false },
        y: { display: false },
      },
    };
  }

  const tempSpark = createChart("tempSpark", {
    type: "line",
    data: { labels: [], datasets: [{ data: [], borderColor: palette.temp, borderWidth: 2, fill: false, tension: 0.4 }] },
    options: sparklineOptions(),
  });

  const humSpark = createChart("humSpark", {
    type: "line",
    data: { labels: [], datasets: [{ data: [], borderColor: palette.hum, borderWidth: 2, fill: false, tension: 0.4 }] },
    options: sparklineOptions(),
  });

  // ---------------------------------------------------------------------
  // Rendering helpers
  // ---------------------------------------------------------------------
  function formatClock(date) {
    return date.toLocaleTimeString([], { hour12: false });
  }

  function setConnectionState(stateName, label) {
    el.connectionPill.dataset.state = stateName;
    el.connectionText.textContent = label;
  }

  function setLoadingSkeleton(isLoading) {
    [el.tempValue, el.humValue].forEach((node) => {
      node.classList.toggle("skeleton", isLoading);
    });
  }

  function trendFor(current, previous) {
    if (previous === null || current === previous) return { dir: "flat", arrow: "\u2192", text: "steady" };
    if (current > previous) return { dir: "up", arrow: "\u2191", text: "rising" };
    return { dir: "down", arrow: "\u2193", text: "falling" };
  }

  function renderTrend(node, trend) {
    node.dataset.dir = trend.dir;
    node.querySelector(".trend-arrow").textContent = trend.arrow;
    node.querySelector(".trend-text").textContent = trend.text;
  }

  function updateReadingCards(temperature, humidity) {
    const tempTrend = trendFor(temperature, state.lastTemp);
    const humTrend = trendFor(humidity, state.lastHum);

    el.tempValue.textContent = temperature.toFixed(1);
    el.humValue.textContent = humidity.toFixed(1);

    renderTrend(el.tempTrend, tempTrend);
    renderTrend(el.humTrend, humTrend);

    el.tempCard.classList.remove("is-stale");
    el.humCard.classList.remove("is-stale");

    state.lastTemp = temperature;
    state.lastHum = humidity;
  }

  function updateCharts(label, temperature, humidity) {
    const h = state.history;
    h.labels.push(label);
    h.temperature.push(temperature);
    h.humidity.push(humidity);

    if (h.labels.length > CONFIG.MAX_HISTORY_POINTS) {
      h.labels.shift();
      h.temperature.shift();
      h.humidity.shift();
    }

    tempChart.data.labels = h.labels;
    tempChart.data.datasets[0].data = h.temperature;
    tempChart.update("none");

    humChart.data.labels = h.labels;
    humChart.data.datasets[0].data = h.humidity;
    humChart.update("none");

    // Sparklines show a short recent slice for a cleaner glance-view.
    const sparkSlice = 20;
    const tSlice = h.temperature.slice(-sparkSlice);
    const hSlice = h.humidity.slice(-sparkSlice);

    tempSpark.data.labels = tSlice.map((_, i) => i);
    tempSpark.data.datasets[0].data = tSlice;
    tempSpark.update("none");

    humSpark.data.labels = hSlice.map((_, i) => i);
    humSpark.data.datasets[0].data = hSlice;
    humSpark.update("none");

    el.tempPoints.textContent = `${h.temperature.length} sample${h.temperature.length === 1 ? "" : "s"}`;
    el.humPoints.textContent = `${h.humidity.length} sample${h.humidity.length === 1 ? "" : "s"}`;
  }

  function redrawCharts() {
    const h = state.history;

    tempChart.data.labels = h.labels;
    tempChart.data.datasets[0].data = h.temperature;
    tempChart.update("none");

    humChart.data.labels = h.labels;
    humChart.data.datasets[0].data = h.humidity;
    humChart.update("none");

    const sparkSlice = 20;
    const tSlice = h.temperature.slice(-sparkSlice);
    const hSlice = h.humidity.slice(-sparkSlice);

    tempSpark.data.labels = tSlice.map((_, i) => i);
    tempSpark.data.datasets[0].data = tSlice;
    tempSpark.update("none");

    humSpark.data.labels = hSlice.map((_, i) => i);
    humSpark.data.datasets[0].data = hSlice;
    humSpark.update("none");

    el.tempPoints.textContent = `${h.temperature.length} sample${h.temperature.length === 1 ? "" : "s"}`;
    el.humPoints.textContent = `${h.humidity.length} sample${h.humidity.length === 1 ? "" : "s"}`;
  }

  function seedChartsFromHistory(history) {
    const recent = history.slice(-CONFIG.MAX_HISTORY_POINTS);
    state.history.labels = recent.map((entry) => formatClock(new Date(entry.timestamp)));
    state.history.temperature = recent.map((entry) => Number(entry.temperature));
    state.history.humidity = recent.map((entry) => Number(entry.humidity));
    state.hasHistorySeeded = true;
    redrawCharts();
  }

  function checkAlerts(temperature, humidity) {
    const t = CONFIG.THRESHOLDS.temperature;
    const h = CONFIG.THRESHOLDS.humidity;

    const tempOut = temperature < t.min || temperature > t.max;
    const humOut = humidity < h.min || humidity > h.max;

    el.tempCard.classList.toggle("is-alerting", tempOut);
    el.humCard.classList.toggle("is-alerting", humOut);

    if (!tempOut && !humOut) {
      el.alertBanner.hidden = true;
      return;
    }

    const parts = [];
    if (tempOut) parts.push(`temperature ${temperature.toFixed(1)}${t.unit} (expected ${t.min}\u2013${t.max}${t.unit})`);
    if (humOut) parts.push(`humidity ${humidity.toFixed(1)}% (expected ${h.min}\u2013${h.max}%)`);

    el.alertTitle.textContent = "Reading out of expected range";
    el.alertDetail.textContent = parts.join(" \u00B7 ") + ".";
    el.alertBanner.hidden = false;
  }

  function markStale() {
    el.tempCard.classList.add("is-stale");
    el.humCard.classList.add("is-stale");
  }

  function renderHistory(history) {
    if (!history || history.length === 0) {
      el.historyBody.innerHTML = '<tr><td colspan="3" class="history-empty">No history yet.</td></tr>';
      el.historyCount.textContent = "0 entries";
      return;
    }

    const rows = history.slice(-10).map((entry) => {
      const time = new Date(entry.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
      return `
        <tr>
          <td>${time}</td>
          <td>${Number(entry.temperature).toFixed(1)}°C</td>
          <td>${Number(entry.humidity).toFixed(1)}%</td>
        </tr>
      `;
    }).join("");

    el.historyBody.innerHTML = rows;
    el.historyCount.textContent = `${history.length} entries`;
  }

  async function fetchHistory() {
    try {
      const response = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.HISTORY_ENDPOINT}`, { cache: "no-store" });
      if (!response.ok) throw new Error("History fetch failed");
      const data = await response.json();
      const history = data.history || [];
      renderHistory(history);
      seedChartsFromHistory(history);
    } catch (err) {
      console.warn("History fetch failed", err);
    }
  }

  // ---------------------------------------------------------------------
  // Networking
  // ---------------------------------------------------------------------
  async function fetchLatest() {
    const url = `${CONFIG.API_BASE_URL}${CONFIG.ENDPOINT}`;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 4500);

    try {
      const res = await fetch(url, { signal: controller.signal, cache: "no-store" });
      clearTimeout(timeout);

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();
      handleSuccess(data);
    } catch (err) {
      clearTimeout(timeout);
      handleFailure(err);
    }
  }

  function handleSuccess(data) {
    const temperature = Number(data.temperature);
    const humidity = Number(data.humidity);

    if (Number.isNaN(temperature) || Number.isNaN(humidity)) {
      handleWaitingForSensor();
      return;
    }

    state.consecutiveFailures = 0;
    state.isOnline = true;
    state.hasLoadedOnce = true;

    el.offlineBanner.hidden = true;
    setConnectionState("online", "Live");
    setLoadingSkeleton(false);

    const now = new Date();
    el.lastUpdated.textContent = formatClock(now);

    updateReadingCards(temperature, humidity);
    updateCharts(formatClock(now), temperature, humidity);
    checkAlerts(temperature, humidity);
  }

  function handleWaitingForSensor() {
    state.consecutiveFailures = 0;
    state.isOnline = true;

    el.offlineBanner.hidden = false;
    el.offlineEndpoint.textContent = "Waiting for MQTT sensor data";
    setConnectionState("connecting", "Waiting");
    setLoadingSkeleton(true);
  }

  function handleFailure(err) {
    state.consecutiveFailures += 1;
    console.warn("[dashboard] fetch failed:", err.message);
    el.offlineEndpoint.textContent = CONFIG.ENDPOINT;

    if (state.consecutiveFailures >= CONFIG.OFFLINE_AFTER_FAILURES) {
      state.isOnline = false;
      setConnectionState("offline", "Offline");
      el.offlineBanner.hidden = false;
      if (state.hasLoadedOnce) markStale();
    } else {
      setConnectionState("connecting", "Reconnecting\u2026");
    }
  }

  // ---------------------------------------------------------------------
  // Boot
  // ---------------------------------------------------------------------
  async function exportCsv() {
    try {
      const response = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.EXPORT_ENDPOINT}`, { cache: "no-store" });
      if (!response.ok) throw new Error("Export failed");

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "environment_history.csv";
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.warn("CSV export failed", err);
    }
  }

  function init() {
    el.offlineEndpoint.textContent = CONFIG.ENDPOINT;
    el.footerEndpoint.textContent = CONFIG.ENDPOINT;
    el.footerInterval.textContent = `${Math.round(CONFIG.POLL_INTERVAL_MS / 1000)}s`;
    el.tempRangeLabel.textContent = `${CONFIG.THRESHOLDS.temperature.min}–${CONFIG.THRESHOLDS.temperature.max}${CONFIG.THRESHOLDS.temperature.unit}`;
    el.humRangeLabel.textContent = `${CONFIG.THRESHOLDS.humidity.min}–${CONFIG.THRESHOLDS.humidity.max}%`;

    el.exportButton.addEventListener("click", exportCsv);

    setLoadingSkeleton(true);
    setConnectionState("connecting", "Connecting\u2026");

    fetchLatest();
    fetchHistory();
    setInterval(fetchLatest, CONFIG.POLL_INTERVAL_MS);
    setInterval(fetchHistory, CONFIG.POLL_INTERVAL_MS * 2);
  }

  document.addEventListener("DOMContentLoaded", init);
})();
