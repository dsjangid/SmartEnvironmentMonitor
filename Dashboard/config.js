/**
 * config.js
 * Central place to tune the dashboard without touching app logic.
 * Change API_BASE_URL when the Flask backend runs on a different host/port.
 */
const CONFIG = {
  // Flask backend base URL. Same-origin by default — override for local dev,
  // e.g. "http://localhost:5000" if the dashboard is served separately from the API.
  API_BASE_URL: "",
  ENDPOINT: "/api/latest",
  HISTORY_ENDPOINT: "/api/history",
  EXPORT_ENDPOINT: "/api/export/csv",

  // How often to poll the backend, in milliseconds.
  POLL_INTERVAL_MS: 5000,

  // Consecutive failed polls before the UI switches to the offline state.
  OFFLINE_AFTER_FAILURES: 2,

  // Maximum number of samples kept in memory for the trend charts / sparklines.
  MAX_HISTORY_POINTS: 60,

  // Comfort / safe-operating thresholds used to flag alerts.
  THRESHOLDS: {
    temperature: { min: 10, max: 35, unit: "\u00B0C" },
    humidity:    { min: 20, max: 70, unit: "%RH" },
  },

  // -------------------------------------------------------------------
  // Extension points (left intentionally simple to wire up later):
  //   - CSV export: serialize `history` (see app.js) to a Blob and trigger download.
  //   - Persistent history: point ENDPOINT at a paginated /api/history route
  //     backed by SQLite instead of relying only on in-memory samples.
  //   - Alert rules: replace THRESHOLDS with rules fetched from the backend
  //     so limits can be changed without redeploying the dashboard.
  // -------------------------------------------------------------------
};
