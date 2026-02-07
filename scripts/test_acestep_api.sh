#!/usr/bin/env bash
set -euo pipefail

API="${API:-http://localhost:8001}"
OUT="${OUT:-output.mp3}"
DURATION="${DURATION:-20}"
POLL_SEC="${POLL_SEC:-2}"
TIMEOUT_SEC="${TIMEOUT_SEC:-600}"

if ! command -v jq >/dev/null; then
  echo "jq is required" >&2
  exit 1
fi

echo "API=$API"

TASK_ID=$(
  curl -s -X POST "$API/release_task" \
    -H 'Content-Type: application/json' \
    -d "{\"prompt\":\"calm piano music\",\"lyrics\":\"[Instrumental]\",\"thinking\":true,\"audio_duration\":$DURATION,\"batch_size\":1,\"audio_format\":\"mp3\"}" \
  | jq -r '.data.task_id'
)

if [[ -z "$TASK_ID" || "$TASK_ID" == "null" ]]; then
  echo "Failed to create task" >&2
  exit 1
fi

echo "TASK_ID=$TASK_ID"

deadline=$(( $(date +%s) + TIMEOUT_SEC ))

while :; do
  now=$(date +%s)
  if (( now > deadline )); then
    echo "Timeout waiting for completion (>${TIMEOUT_SEC}s)" >&2
    exit 1
  fi

  RES=$(curl -s -X POST "$API/query_result" -H 'Content-Type: application/json' -d "{\"task_id_list\":[\"$TASK_ID\"]}")

  # Some server builds return data: [] while running.
  has_item=$(echo "$RES" | jq -r '(.data | length) > 0')
  if [[ "$has_item" != "true" ]]; then
    echo "running... (no data yet)"
    sleep "$POLL_SEC"
    continue
  fi

  STATUS=$(echo "$RES" | jq -r '.data[0].status')
  if [[ "$STATUS" == "0" ]]; then
    echo "running... (status=0)"
    sleep "$POLL_SEC"
    continue
  fi
  if [[ "$STATUS" == "2" ]]; then
    echo "failed (status=2)" >&2
    echo "$RES" | jq . >&2
    exit 1
  fi
  if [[ "$STATUS" != "1" ]]; then
    echo "running... (status=$STATUS)"
    sleep "$POLL_SEC"
    continue
  fi

  FILE=$(echo "$RES" | jq -r '.data[0].result | fromjson[0].file // empty')
  if [[ -z "$FILE" ]]; then
    echo "Succeeded but no audio file path found yet; retrying..." >&2
    sleep "$POLL_SEC"
    continue
  fi

  curl -s -L "$API$FILE" -o "$OUT"
  echo "Saved: $OUT"
  ls -lh "$OUT"
  break
done
