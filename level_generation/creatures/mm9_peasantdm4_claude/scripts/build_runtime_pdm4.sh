#!/usr/bin/env bash
# Runtime GLB for mm9_peasantdm4 (PeasantDM2's chain on the dwarf male skeleton): rigged master -> textured export -> MM9 clips
# (+ finger aliases) -> hand rest (scripts/hand_rest_pdm4.txt) -> prepare -> LODs -> shadow fix -> material extras (one skin, row 10:
# no tiers, no region mask, as mm9_markel_claude) -> floor fix -> winding check [-> install --world mm9].
# Usage (from the repo root): TOKEN=<lease> [BLEND=work/eyes_trim.blend] level_generation/creatures/mm9_peasantdm4_claude/scripts/build_runtime_pdm4.sh [--install]
set -euo pipefail
# memory cap on every Blender/heavy job (VARIANTS_BRIEF "Memory", 2026-11-02)
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
: "${TOKEN:?set TOKEN}"
V=../claude_shared/gltf_venv/bin/python
rel="level_generation/creatures/$(basename "$here")"
n=pdm4; N=PeasantDM4
B() { local out log; out=$(cd "$repo" && systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 tools/run_creature_blender.sh --token "$TOKEN" "$@" 2>&1) || true
      log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
      if grep -q "Error: script failed\|Traceback" "$log"; then grep -A12 Traceback "$log" | tail -14; echo "STEP FAILED: $1"; exit 1; fi
      grep -E "EXPORTED|LIFT|HEADFIX|LOD triangles" "$log" | cut -c1-200 || true; }
mkdir -p export work
[[ -n "${SKIP_EXPORT:-}" ]] || B "$rel/scripts/build_export_v2.py" "$here/${BLEND:-work/rigid_v3n.blend}" "$here/work/${n}_body_tex.glb" "$N" pdm4_tp pdm4 pdm4_tp
"$V" scripts/clips_mm9.py work/${n}_body_tex.glb work/mm9_${n}_clips.glb scripts/roles_pdm4.json work/clips_v1.json 2>/dev/null | cut -c1-240
# relaxed five-finger hands following MM9's mitten curl (mm9_kira_claude's finger_pose.py; the dwarf mitten has two
# segments, Finger1/Finger11, so the distal direction is Finger11's own axis)
"$V" scripts/finger_pose.py work/mm9_${n}_clips.glb work/mm9_${n}_fp.glb 2>/dev/null | grep -c FINGERPOSE | sed 's/^/FINGERPOSE clips /'
mv work/mm9_${n}_fp.glb work/mm9_${n}_clips.glb
# PeasantDM4 (fuller body and beard than MM9's): the left forearm entered the chest side in RubBeard (5 cm), the skirt
# ring in Running (2.5 cm), the tunic in Talk, the belt-level sleeve flare in AttackMelee (3.3 cm) and Fidget (1.6 cm): arm_clear.py turns the upper arm the least (smoothed over the keys)
# arm_clear.py's own neighbour falloff jumped between keys with different correction axes (jitter gate 20-37 deg/f): the
# corrections are Gaussian-smoothed over the keys (--smooth-keys, added to this project's copy), per clip so that short
# contacts keep their peak: Talk 4; RubBeard and Fidget 14; Running and AttackMelee 8 with a 7 cm margin.
AC() { python3 scripts/arm_clear.py "$1" "$2" --side "L= L " --side "R= R " --test arm --outer-only --exact "${@:3}" | grep ARMCLEAR | cut -c1-200; }
AC work/mm9_${n}_clips.glb work/mm9_${n}_clear1.glb --clips Talk --margin 0.03 --smooth-keys 4
AC work/mm9_${n}_clear1.glb work/mm9_${n}_clear2.glb --clips RubBeard,Fidget --margin 0.03 --smooth-keys 14
AC work/mm9_${n}_clear2.glb work/mm9_${n}_clear.glb --clips Running,AttackMelee --margin 0.07 --max-deg 40 --smooth-keys 8
cur=work/mm9_${n}_clear.glb; k=0
while IFS= read -r line; do
  [[ -z "$line" || "$line" == \#* ]] && continue
  k=$((k + 1)); nxt=work/mm9_${n}_rest${k}.glb
  eval "python3 scripts/hand_rest.py $cur $nxt $line" | grep HANDREST | cut -c1-240
  cur=$nxt
done < scripts/hand_rest_${n}.txt
cp "$cur" export/mm9_${n}_lod0.glb
python3 "$repo/tools/prepare_actor_glb.py" export/mm9_${n}_lod0.glb export/mm9_${n}_runtime_lod0.glb
systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 /snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm9_${n}_runtime_lod0.glb" \
  "$here/export/mm9_${n}_lods.glb" --mesh-node "$N" --max-influences 4 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/mm9_${n}_lods.glb export/mm9_${n}_lods_shadowfix.glb "$N"
python3 scripts/set_material_extras.py export/mm9_${n}_lods_shadowfix.glb export/mm9_${n}_extras.glb openyamm_specular=0 pbr.metallicFactor=0
python3 ../claude_shared/floor/floor_fix.py export/mm9_${n}_extras.glb work/mm9_${n}_floor.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead | tail -3
# true handedness (mirror_glb.py, as mm9_peasantdm1_claude on the same skeleton): convert_abc_model.py keeps LithTech's
# left-handed numbers, so the unmirrored build (work/mm9_pdm4_floor.glb) is the game's actor in a mirror
$V scripts/mirror_glb.py work/mm9_${n}_floor.glb export/mm9_${n}.glb | tail -1
rm -f export/mm9_pdm4_lods.geometry.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/mm9_${n}.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/mm9_${n}.glb --world mm9
fi
ls -la export/mm9_${n}.glb
