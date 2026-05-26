#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_HOST="${API_HOST:-127.0.0.1}"
API_PORT="${API_PORT:-8000}"
WEB_HOST="${WEB_HOST:-127.0.0.1}"
WEB_PORT="${WEB_PORT:-3000}"

if [ -f "$ROOT_DIR/.env.local" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env.local"
  set +a
fi

API_CORS_ORIGINS="${API_CORS_ORIGINS:-http://localhost:${WEB_PORT},http://127.0.0.1:${WEB_PORT},http://localhost:3001,http://127.0.0.1:3001}"
export API_CORS_ORIGINS

cleanup() {
  trap - INT TERM EXIT
  if [ -n "${API_PID:-}" ] && kill -0 "$API_PID" 2>/dev/null; then
    kill "$API_PID" 2>/dev/null || true
  fi
  if [ -n "${WEB_PID:-}" ] && kill -0 "$WEB_PID" 2>/dev/null; then
    kill "$WEB_PID" 2>/dev/null || true
  fi
  wait 2>/dev/null || true
}

trap cleanup INT TERM EXIT

cd "$ROOT_DIR"

echo "Starting FastAPI on http://${API_HOST}:${API_PORT}"
python3 -m uvicorn app.main:app \
  --app-dir apps/api \
  --reload \
  --host "$API_HOST" \
  --port "$API_PORT" &
API_PID=$!

echo "Starting Next.js on http://${WEB_HOST}:${WEB_PORT}"
npm --workspace apps/web run dev -- --hostname "$WEB_HOST" --port "$WEB_PORT" &
WEB_PID=$!

echo ""
echo "Frontend: http://${WEB_HOST}:${WEB_PORT}"
echo "Backend:  http://${API_HOST}:${API_PORT}"
echo "Press Ctrl-C to stop both servers."
echo ""

wait "$API_PID" "$WEB_PID"
