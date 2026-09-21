#!/usr/bin/env bash
# Starts each language implementation in turn, points the black-box
# contract-tests suite at it, runs the full suite, tears the server down,
# and moves to the next. Prints a pass/fail summary for all three at the
# end. See README.md.
set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONTRACT_TESTS_DIR="$REPO_ROOT/contract-tests"

SERVER_PID=""

cleanup() {
  if [ -n "$SERVER_PID" ] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID" 2>/dev/null
    wait "$SERVER_PID" 2>/dev/null
  fi
  SERVER_PID=""
}
trap cleanup EXIT

wait_for_server() {
  local url="$1"
  for _ in $(seq 1 60); do
    if curl -s -o /dev/null "$url/api/v1/urls/aaaaaaa"; then
      return 0
    fi
    sleep 0.5
  done
  echo "Server at $url did not come up in time" >&2
  return 1
}

run_suite_against() {
  local target_url="$1"
  (
    cd "$CONTRACT_TESTS_DIR" || exit 1
    TARGET_URL="$target_url" uv run pytest -q
  )
}

# Plain variables instead of an associative array — the default /bin/bash
# on macOS is 3.2, which doesn't support `declare -A`.
RESULT_PYTHON="FAIL"
RESULT_TYPESCRIPT="FAIL"
RESULT_RUST="FAIL"

echo "== Python (FastAPI) on :8001 =="
(
  cd "$REPO_ROOT/python" || exit 1
  BASE_URL="http://127.0.0.1:8001" uv run uvicorn url_shortener.main:app \
    --host 127.0.0.1 --port 8001 >/tmp/contract-tests-python.log 2>&1 &
  echo $! > /tmp/contract-tests-python.pid
)
SERVER_PID="$(cat /tmp/contract-tests-python.pid)"
if wait_for_server "http://127.0.0.1:8001" && run_suite_against "http://127.0.0.1:8001"; then
  RESULT_PYTHON="PASS"
fi
cleanup

echo
echo "== TypeScript (Fastify) on :8002 =="
(
  cd "$REPO_ROOT/typescript" || exit 1
  if [ ! -d node_modules ]; then npm install --silent; fi
  BASE_URL="http://127.0.0.1:8002" PORT=8002 npm start >/tmp/contract-tests-typescript.log 2>&1 &
  echo $! > /tmp/contract-tests-typescript.pid
)
SERVER_PID="$(cat /tmp/contract-tests-typescript.pid)"
if wait_for_server "http://127.0.0.1:8002" && run_suite_against "http://127.0.0.1:8002"; then
  RESULT_TYPESCRIPT="PASS"
fi
cleanup

echo
echo "== Rust (Axum) on :8003 =="
(
  cd "$REPO_ROOT/rust" || exit 1
  cargo build --quiet
  BASE_URL="http://127.0.0.1:8003" PORT=8003 cargo run --quiet >/tmp/contract-tests-rust.log 2>&1 &
  echo $! > /tmp/contract-tests-rust.pid
)
SERVER_PID="$(cat /tmp/contract-tests-rust.pid)"
if wait_for_server "http://127.0.0.1:8003" && run_suite_against "http://127.0.0.1:8003"; then
  RESULT_RUST="PASS"
fi
cleanup

echo
echo "== Summary =="
overall=0
printf "%-12s %s\n" "python" "$RESULT_PYTHON"
printf "%-12s %s\n" "typescript" "$RESULT_TYPESCRIPT"
printf "%-12s %s\n" "rust" "$RESULT_RUST"
[ "$RESULT_PYTHON" = "PASS" ] || overall=1
[ "$RESULT_TYPESCRIPT" = "PASS" ] || overall=1
[ "$RESULT_RUST" = "PASS" ] || overall=1

exit $overall
