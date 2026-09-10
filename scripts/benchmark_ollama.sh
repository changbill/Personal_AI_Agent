#!/bin/sh
# Phase 0-B Ollama CPU benchmark.
# Usage: sh scripts/benchmark_ollama.sh <explicit-model-tag> [iterations]
# Requires: curl, python3, Docker (only for container resource snapshots).

set -eu

model=${1:?Usage: sh scripts/benchmark_ollama.sh <explicit-model-tag> [iterations]}
iterations=${2:-3}
base_url=${OLLAMA_BASE_URL:-http://127.0.0.1:11434}
container_name=${OLLAMA_CONTAINER_NAME:-personal-ai-agent-ollama-benchmark}
output_file=${BENCHMARK_OUTPUT:-}
prompt='한국어로 개인 비서가 사용자의 일정을 도울 때 지켜야 할 원칙을 세 문장으로 설명해 주세요.'


if [ -n "$output_file" ]; then
  exec >"$output_file" 2>&1
fi
case "$model" in
  *:*) ;;
  *) echo "ERROR: 모델 태그를 명시하세요 (예: qwen2.5:3b)." >&2; exit 2 ;;
esac

case "$iterations" in
  *[!0-9]*|'') echo "ERROR: iterations는 양의 정수여야 합니다." >&2; exit 2 ;;
esac

request_file=$(mktemp)
response_file=$(mktemp)
trap 'rm -f "$request_file" "$response_file"' EXIT HUP INT TERM

python3 - "$model" "$prompt" >"$request_file" <<'PY'
import json
import sys

print(json.dumps({
    "model": sys.argv[1],
    "prompt": sys.argv[2],
    "stream": False,
    "think": False,
    "keep_alive": "10m",
    "options": {"num_ctx": 2048, "num_predict": 96, "temperature": 0},
}, ensure_ascii=False))
PY

printf 'model=%s iterations=%s num_ctx=2048 think=false\n' "$model" "$iterations"
curl --fail --silent --show-error "$base_url/api/version" >/dev/null

run=1
while [ "$run" -le "$iterations" ]; do
  curl --fail --silent --show-error \
    --header 'Content-Type: application/json' \
    --data @"$request_file" \
    "$base_url/api/generate" >"$response_file"

  python3 - "$run" "$response_file" <<'PY'
import json
import sys

with open(sys.argv[2], encoding="utf-8") as response_file:
    data = json.load(response_file)
eval_duration = data.get("eval_duration", 0)
eval_count = data.get("eval_count", 0)
tokens_per_second = eval_count / (eval_duration / 1_000_000_000) if eval_duration else 0
print(
    "run={run} load_s={load:.3f} total_s={total:.3f} output_tokens={tokens} tok_s={tok_s:.2f}".format(
        run=sys.argv[1],
        load=data.get("load_duration", 0) / 1_000_000_000,
        total=data.get("total_duration", 0) / 1_000_000_000,
        tokens=eval_count,
        tok_s=tokens_per_second,
    )
)
print("response=" + data.get("response", "").replace("\n", " "))
PY

  if docker inspect "$container_name" >/dev/null 2>&1; then
    docker stats --no-stream --format 'container_cpu={{.CPUPerc}} container_mem={{.MemUsage}}' "$container_name"
  fi
  run=$((run + 1))
done

printf 'loaded_models:\n'
curl --fail --silent --show-error "$base_url/api/ps"
