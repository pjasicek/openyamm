#!/usr/bin/env bash
# One tier-colour iteration: compose (gains from textures/m422_ramp_gains.json) -> viewer tier GLBs -> the three
# tier_match shots per tier -> tier_match.py. Usage: TOK=<lease> scripts/tier_iter.sh
set -euo pipefail
cd "$(dirname "$0")/.."; REPO=$(cd ../../.. && pwd); NAME=$(basename "$PWD")
python3 scripts/compose_m422.py | grep RAMP
python3 scripts/viewer_tiers.py > /dev/null; python3 scripts/update_viewer_manifest.py > /dev/null
for t in a b c; do
  (cd "$REPO" && timeout 900 python3 tools/run_creature_review.py --project level_generation/creatures/$NAME --token "$TOK" \
     --tier m422_$t shots m422_${t}_tmfront:Standing:0:front:body m422_${t}_tmback:Standing:0:back:body \
     m422_${t}_tmhead:Standing:0:quarter:head > /dev/null)
done
python3 scripts/tier_match.py | sed 's/"native_rgb"/\n     native/' | cut -c1-220
