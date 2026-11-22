#!/bin/bash
# Runs every two-game co-op scenario (tests/scenarios/coop/net_*.yml) over a bad line: a copy of each gets a
# coop_network step after its coop_guest step. Their waits are written for a good line, so a line worse than about
# 100 ms each way fails them for being late, not for being wrong.
#
#   tools/coop_bad_line/run.sh [delay_ms] [jitter_ms] [loss_permille]      (default: 100 40 100)
#
# Output: output/coop_bad_line/<scenario>.log, and one line per scenario here.
set -u
cd "$(dirname "$0")/../.." || exit 1
DELAY=${1:-100}
JITTER=${2:-40}
LOSS=${3:-100}
OUT="$PWD/output/coop_bad_line"
mkdir -p "$OUT/scenarios" "$OUT/user_data"
failed=0
for scenario in tests/scenarios/coop/net_*.yml; do
    name=$(basename "$scenario" .yml)
    copy="$OUT/scenarios/$name.yml"
    if grep -q '^  - coop_network:' "$scenario"; then
        cp "$scenario" "$copy"
    else
        sed "s/^  - coop_guest: {}\$/  - coop_guest: {}\n  - coop_network: {delay_ms: $DELAY, jitter_ms: $JITTER, loss_permille: $LOSS}/" \
            "$scenario" > "$copy"
    fi
    SDL_AUDIODRIVER=dummy timeout 600 ./build/game/openyamm --user-data "$OUT/user_data" \
        --headless-run-scenario "$copy" --scenario-no-color > "$OUT/$name.log" 2>&1
    rc=$?
    if [ $rc -eq 0 ]; then
        echo "pass  $name"
    else
        failed=$((failed + 1))
        echo "FAIL  $name  $(grep -m1 '^Scenario failure' "$OUT/$name.log" | sed 's/^Scenario failure: [^ ]* //' | cut -c1-160)"
    fi
done
echo "bad line ${DELAY} ms + ${JITTER} ms, loss ${LOSS}/1000: $failed failed"
exit $((failed > 0))
