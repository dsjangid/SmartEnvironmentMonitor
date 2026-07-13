# Smart Environment Monitoring — Dashboard

Frontend dashboard for an ESP32 + DHT22 environmental monitoring pipeline
(ESP32 → MQTT broker → Flask API → this dashboard).

## Structure

```
Dashboard/
├── index.html          # markup
├── style.css           # responsive instrumentation-panel theme
├── config.js           # API URL, poll interval, alert thresholds
├── app.js              # polling, rendering, Chart.js, alert logic
├── server_example.py    # optional minimal Flask backend for local testing
└── README.md
```

## Run it

1. Serve the dashboard folder with any static server (not `file://`, so
   `fetch()` behaves correctly), e.g.:
   ```
   cd Dashboard
   python3 -m http.server 8080
   ```
2. Point it at your real backend, or spin up the bundled test backend:
   ```
   pip install flask flask-cors
   python3 server_example.py
   ```
3. Open `http://localhost:8080`. If the API is on a different origin, set
   `API_BASE_URL` in `config.js` (e.g. `"http://localhost:5000"`).

## Expected API response

`GET /api/latest`
```json
{
  "temperature": 24.6,
  "humidity": 51.2,
  "timestamp": "2026-07-13T10:30:00+00:00",
  "status": "ok"
}
```

`GET /api/history`
```json
{
  "history": [
    {
      "timestamp": "2026-07-13T10:30:00+00:00",
      "temperature": 24.6,
      "humidity": 51.2
    }
  ]
}
```

## Extending

- **Configurable alerts** — `CONFIG.THRESHOLDS` in `config.js` is the only
  place alert ranges live; swap it for a fetched `/api/thresholds` if rules
  need to change without redeploying the frontend.
- **Auth** — add an `Authorization` header in `fetchLatest()` once the API
  requires it.
