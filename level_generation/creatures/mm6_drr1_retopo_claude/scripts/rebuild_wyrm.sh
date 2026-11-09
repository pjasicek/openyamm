#!/usr/bin/env bash
# Rebuild the installed Wyrm from the retopology sources: patch -> dump/AO -> compose -> finalize -> runtime -> install.
# Needs the leases: RETOPO_TOKEN (mm6_drr1_retopo_claude) and WYRM_TOKEN (mm6_drr1_claude).
set -eu
cd "$(dirname "$0")/../../../.."
R=level_generation/creatures/mm6_drr1_retopo_claude; W=level_generation/creatures/mm6_drr1_claude
blend() { tools/run_creature_blender.sh --token "$1" "$2" > /dev/null; L=$(ls -t /tmp/openyamm-creature-blender-*.log | head -1);
          grep -E "Traceback|^Error" -A4 "$L" && exit 1; grep -E "$3" "$L" || true; }
blend "$RETOPO_TOKEN" $R/scripts/patch_v5.py "HOLES|PATCH|PATCHED"
for s in dump ao_body ao_head; do REA_STAGE=$s blend "$RETOPO_TOKEN" $R/scripts/dump_final.py "DUMPED|^AO"; done
python3 $R/scripts/compose_final.py | grep -E "repaired|islands|COMPOSED" | cut -c1-160
blend "$WYRM_TOKEN" $W/scripts/finalize_v4.py "^FINAL"
python3 tools/prepare_actor_glb.py $W/export/mm6_wyrm_lod0.glb $W/export/mm6_wyrm_runtime_lod0.glb > /dev/null
blend "$WYRM_TOKEN" $W/scripts/build_lods.py "LOD triangles"
python3 level_generation/creatures/claude_shared/bake_burn_maps.py $W/export/mm6_wyrm_lods.glb $W/textures/wyrm \
  --node Wyrm --material Wyrm=body --material WyrmHead=head --ignite Head Jaw Tail9 Tail10 > /dev/null
python3 $W/scripts/finish_runtime.py | tail -1
python3 $W/scripts/viewer_tiers.py > /dev/null
for f in mm6_wyrm.glb mm6_wyrm_remains.glb; do python3 tools/install_model.py $W/export/$f --world mm6 | tail -1; done
cp $W/export/mm6_wyrm_remains.glb $W/review/viewer/
