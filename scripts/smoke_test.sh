#!/usr/bin/env bash
# Smoke test for a running QuizHub instance (local, Docker or Render).
#
# Usage:
#   scripts/smoke_test.sh                              # http://localhost:5000
#   BASE_URL=https://<name>.onrender.com scripts/smoke_test.sh
#   scripts/smoke_test.sh https://<name>.onrender.com
#
# Stops with a non-zero exit code on the first failed check.
set -euo pipefail

BASE_URL="${1:-${BASE_URL:-http://localhost:5000}}"
BASE_URL="${BASE_URL%/}"

# A cold Render instance needs about a minute to wake up: allow for it and retry 5xx answers.
CURL=(curl --silent --show-error --max-time 90 --retry 3 --retry-delay 5)

pass() { echo "PASS  $1"; }
fail() { echo "FAIL  $1" >&2; exit 1; }

echo "Smoke test against $BASE_URL"

# 1. /health answers 200 with {"status": "ok"}
body=$("${CURL[@]}" --fail "$BASE_URL/health") || fail "GET /health did not return 200"
echo "$body" | grep -Eq '"status"[[:space:]]*:[[:space:]]*"ok"' || fail "GET /health body is not {\"status\": \"ok\"}: $body"
pass "GET /health -> 200 {\"status\": \"ok\"}"

# 2. The home page loads
"${CURL[@]}" --fail --output /dev/null "$BASE_URL/" || fail "GET / did not return 200"
pass "GET / -> 200"

# 3. The leaderboard is public and returns 200
"${CURL[@]}" --fail --output /dev/null "$BASE_URL/leaderboard" || fail "GET /leaderboard did not return 200"
pass "GET /leaderboard -> 200"

# 4. /topics needs a nickname: without a session it must redirect (curl does not follow redirects)
code=$("${CURL[@]}" --output /dev/null --write-out '%{http_code}' "$BASE_URL/topics") || fail "GET /topics failed"
case "$code" in
  301|302|303|307|308) pass "GET /topics without a session -> $code redirect" ;;
  *) fail "GET /topics without a session returned $code, expected a redirect" ;;
esac

echo "All smoke checks passed."
