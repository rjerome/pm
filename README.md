# Project Management MVP

## Run

macOS:

```bash
./scripts/start-mac.sh
```

Linux:

```bash
./scripts/start-linux.sh
```

Windows PowerShell:

```powershell
./scripts/start-windows.ps1
```

The app will be available at `http://127.0.0.1:8000`.

## Stop

macOS:

```bash
./scripts/stop-mac.sh
```

Linux:

```bash
./scripts/stop-linux.sh
```

Windows PowerShell:

```powershell
./scripts/stop-windows.ps1
```

## Backend Tests

```bash
uv run pytest
```

## AI Connectivity Check

The temporary part 8 verification route is `POST /api/ai/connectivity-check`.

- Local backend runs can read `OPENROUTER_API_KEY` from the root `.env`
- Docker passes `OPENROUTER_API_KEY` into the container explicitly through `compose.yaml`
- The route uses the current MVP bearer token: `pm-mvp-user-token`

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/ai/connectivity-check \
  -H "Authorization: Bearer pm-mvp-user-token"
```
