#!/usr/bin/env bash
# Rebuild the Dragon Pharaoh from the shipped MM8 Lizardman Warrior (no Blender): skin, nemes, crest fold, clips, book.
set -euo pipefail
cd "$(dirname "$0")/../../../.."
P=level_generation/creatures/xeen_pharaoh_claude
T=level_generation/creatures/xeen_tiers_claude
mkdir -p $P/work $P/export
python3 $T/xeen_tiers.py assets_source/worlds/mm8/models/mm8_m404.glb $P/work/step1.glb $P/specs/spec_pharaoh.json
python3 $T/add_region.py $P/work/step1.glb $P/work/step2.glb $P/specs/body_skin.json
python3 $T/add_region.py $P/work/step2.glb $P/work/step3.glb $P/specs/body_leather.json
python3 $P/scripts/build_nemes.py $P/work/step3.glb $P/specs/nemes.json $P/work/nemes_model.glb \
    $P/export/xeen_pharaoh_nemes.glb --report $P/work/nemes_report.json
python3 $P/scripts/squash_crest.py $P/work/step3.glb $P/work/nemes_model.glb $P/work/step4.glb
python3 $P/scripts/author_clips.py $P/work/step4.glb $P/specs/clips.json $P/work/step5.glb $P/work/book_local.json > $P/work/clip_gates.txt
python3 level_generation/creatures/claude_shared/floor/floor_fix.py $P/work/step5.glb $P/export/xeen_pharaoh.glb --raise Hit
python3 $P/scripts/gate_book.py $P/export/xeen_pharaoh.glb $P/work/book_local.json $P/work/gate_book.json
python3 $P/scripts/build_book.py $P/work/book_local.json $P/export/xeen_pharaoh_book.glb
for m in xeen_pharaoh xeen_pharaoh_nemes xeen_pharaoh_book; do
    python3 level_generation/decorations/mm8_3d/animated/scripts/check_winding.py $P/export/$m.glb
done
