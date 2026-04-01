$ErrorActionPreference = "Stop"

docker compose up --build -d
Write-Host "Project Management MVP is starting at http://127.0.0.1:8000"
