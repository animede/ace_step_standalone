#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# Activate local venv if present (recommended)
if [[ -f "$ROOT_DIR/.venv/bin/activate" ]]; then
	# shellcheck disable=SC1091
	source "$ROOT_DIR/.venv/bin/activate"
fi

# -----------------------------------------------------------------------------
# Multi-model setup:
# - Primary (default): turbo
# - Secondary: base (selectable per request via {"model":"acestep-v15-base"})
# -----------------------------------------------------------------------------

export ACESTEP_CONFIG_PATH="${ACESTEP_CONFIG_PATH:-acestep-v15-turbo}"
export ACESTEP_CONFIG_PATH2="${ACESTEP_CONFIG_PATH2:-acestep-v15-base}"
# Optional third model slot (leave empty unless you want it)
export ACESTEP_CONFIG_PATH3="${ACESTEP_CONFIG_PATH3:-}"

# LLM (server-side) for thinking/format/sample. For best quality on 24GB VRAM.
export ACESTEP_LM_MODEL_PATH="${ACESTEP_LM_MODEL_PATH:-acestep-5Hz-lm-4B}"
export ACESTEP_LM_BACKEND="${ACESTEP_LM_BACKEND:-vllm}"
export ACESTEP_DEVICE="${ACESTEP_DEVICE:-auto}"

# NOTE: api_server uses an in-memory queue/job store -> keep workers=1.
export ACESTEP_API_WORKERS="${ACESTEP_API_WORKERS:-1}"

HOST="${ACESTEP_API_HOST:-0.0.0.0}"
PORT="${ACESTEP_API_PORT:-8001}"
LOG_LEVEL="${ACESTEP_API_LOG_LEVEL:-debug}"

# Optional CLI overrides (kept minimal on purpose)
# Accept common variants:
#   --host 0.0.0.0
#   --port 8001
#   --log-level info
# And a compatibility alias some users type:
#   --server-name 0.0.0.0 / -server-name 0.0.0.0  (treated as host)
while [[ $# -gt 0 ]]; do
	case "$1" in
		--host|--server-name|-server-name)
			HOST="${2:-}"
			shift 2
			;;
		--port)
			PORT="${2:-}"
			shift 2
			;;
		--log-level)
			LOG_LEVEL="${2:-}"
			shift 2
			;;
		*)
			echo "[WARN] Unknown arg ignored: $1" >&2
			shift
			;;
	esac
done

exec python -m uvicorn acestep.api_server:app \
	--host "$HOST" \
	--port "$PORT" \
	--workers 1 \
	--log-level "$LOG_LEVEL"
