# IPVTL Cluster Web Management

This repository contains a minimal example of an IPVTL cluster management panel. The backend is implemented with FastAPI and the frontend is a simple static page located at `frontend/index.html`.

Main features
- Cluster discovery: load server list from `servers/servers.json`.
- Status polling: the backend `Poller` periodically fetches `/status` from each server and caches the results.
- Status API: endpoints such as `/api/servers` and `/api/servers/{id}/status` expose server information for the frontend or external tools.
- Channel management (restart): `POST /api/servers/{server_id}/channels/{channel_id}/restart` triggers stop/start requests to the target server to restart a channel (`app/services/manager.py`).
- Static admin UI: `frontend/index.html` shows CPU and channel status, supports auto-refresh and restart actions.

Project layout (summary)
- `app/main.py`: application entry point; loads server configuration and creates the `Poller` on startup.
- `app/config.py`: global settings (poll interval, concurrency, timeouts, path to `servers.json`) using Pydantic.
- `app/models.py`: Pydantic models: `Server`, `ServerStatus`, `Channel`.
- `app/api/servers.py`: API routes for listing servers, querying status and restarting channels.
- `app/services/poller.py`: async poller that fetches status from servers and keeps a cached view.
- `app/services/manager.py`: implements stop/start HTTP requests used to restart channels.
- `servers/servers.json`: example server configuration.
- `frontend/index.html`: minimal frontend that calls the API and displays status.

Running (development)
1. Create and activate a virtual environment (optional):

```powershell
python -m venv .venv
.\\.venv\\Scripts\\activate
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Start the app (example with `uvicorn`):

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

4. Open `http://localhost:8000/` in your browser to view the admin page.

Configuration
- Edit `servers/servers.json` to update the server list.
- Override settings via environment variables (see `app/config.py`) such as `POLL_INTERVAL`, `POLL_CONCURRENCY`, etc.

API overview
- `GET /api/servers` — returns the server list.
- `GET /api/servers/{server_id}/status` — returns cached status for the given server (CPU, channels).
- `POST /api/servers/{server_id}/channels/{channel_id}/restart` — restarts a channel (stop then start).

Notes & suggestions
- The code uses `print` statements for debugging; consider switching to `logging` with `LOG_LEVEL`.
- For production, add authentication/authorization and tighten CORS instead of allowing all origins.

Next steps (suggested)
- Add authentication (JWT or API key).
- Convert the frontend to a SPA (React/Vue) for better UX and monitoring.
- Add tests for `Poller`, `manager`, and API routes.
