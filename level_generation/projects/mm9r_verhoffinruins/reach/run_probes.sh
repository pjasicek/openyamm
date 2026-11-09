#!/usr/bin/env bash
# Runs the probes given (default: all) and prints each probe's actor positions over time (ACTOR report lines).
cd "$(dirname "$0")/../../../.." || exit 1
files=("$@")
[ ${#files[@]} -eq 0 ] && files=(level_generation/projects/mm9r_verhoffinruins/reach/probe_*.yml)
for g in "${files[@]}"; do
  echo "== $g"
  ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" --headless-run-scenario "$g" --scenario-no-color 2>&1 \
    | grep -E "^ACTOR|Scenario (failure|passed)" | sed -E 's/.*(position=[^ ]+).*(targeting_party=[a-z]+).*/\1 \2/' | uniq | tr '\n' ' '
  echo
done
