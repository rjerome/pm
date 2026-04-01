#!/usr/bin/env bash

set -euo pipefail

docker compose up --build -d
echo "Project Management MVP is starting at http://127.0.0.1:8000"
