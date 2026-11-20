#!/usr/bin/env bash
# meshy_wait.sh <project> <token> <job>: polls until SUCCEEDED/FAILED, then downloads
P=$1; T=$2; J=$3
for i in $(seq 1 200); do
  out=$(python3 tools/creature_meshy.py --project "$P" --token "$T" poll --job "$J" --wait-seconds 45 2>&1 | tail -1)
  echo "$out"
  case "$out" in *"Another creature operation"*) sleep 20; continue;; esac
  case "$out" in *SUCCEEDED*) python3 tools/creature_meshy.py --project "$P" --token "$T" download --job "$J" 2>&1 | tail -2; exit 0;; *FAILED*|*CANCELED*|*EXPIRED*) exit 1;; esac
done
exit 2
