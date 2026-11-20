#!/usr/bin/env bash
# Runtime GLB of PeasantHOF1 (rows 61/62 tier phof1_a, row 63 tier phof1_b): master blend -> textured export -> MM9 clips
# (soft offsets) -> relaxed fingers -> hand rest -> prepare -> LODs -> shadow fix -> tiers (body region mask + ramps; tier B's
# own head colour + normal, tier_head.py) -> material extras -> floor fix -> true handedness (mirror) -> winding check
# [-> install --world mm9 as mm9_peasanthof1.glb].
# MODEL=2 builds mm9_peasanthof2.glb (row 64, the HOF2 variant mesh, tier phof2_c) the same way.
# Usage (repo root): [MODEL=1|2] [BLEND=...] level_generation/creatures/mm9_peasanthof_claude/scripts/build_runtime_phof.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
M=${MODEL:-1}; N=PeasantHOF
if [[ $M == 1 ]]; then n=phof1; BODY=phofa_tp; HEADCFG=phof; HEADTEX=phofa_tp; RAMPS=a_ramps.json; DEFBLEND=work/master_v9e.blend; F3GD=0.8
else n=phof2; BODY=phofc_tp; HEADCFG=phof2; HEADTEX=phofc_tp; RAMPS=c_ramps.json; DEFBLEND=work/hof2/master_v23.blend; F3GD=1.0; fi
V=../claude_shared/gltf_venv/bin/python
CAP="systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0"
mkdir -p export work
(cd "$repo" && level_generation/creatures/mm9_peasanthof_claude/scripts/bld.sh "EXPORTED|Error|Trace" \
  level_generation/creatures/mm9_peasanthof_claude/scripts/build_export_v2.py "$here/${BLEND:-$DEFBLEND}" \
  "$here/work/${n}_body_tex.glb" $N $BODY $HEADCFG $HEADTEX | cut -c1-120)
$CAP $V scripts/clips_mm9.py work/${n}_body_tex.glb work/mm9_${n}_clips.glb scripts/roles_phof.json work/clips_${n}.json 2>/dev/null | cut -c1-160
# HOF2 (2026-11-04): MM9's thigh offsets on the refitted rest stretched the left thigh 11 % (bone_length_audit); keep rest lengths
if [[ $M == 2 ]]; then python3 scripts/thigh_length_fix.py work/mm9_${n}_clips.glb work/mm9_${n}_clips_tl.glb && mv work/mm9_${n}_clips_tl.glb work/mm9_${n}_clips.glb; fi
$CAP python3 scripts/finger_pose.py work/mm9_${n}_clips.glb work/mm9_${n}_fp.glb --mcp-extra 0 --pip-extra 0 --thumb-ip 6 --thumb-in 3 | grep -c FINGERPOSE >/dev/null
cur=work/mm9_${n}_fp.glb; i=0
# Fidget (fidget1, the left forearm across the bust looking at the wrist): arm_clear.py turns the upper arm out of the
# fuller body, smooth_correction.py spreads that turn over time (HOM1's route for the same library clip)
$CAP python3 scripts/arm_clear.py $cur work/mm9_${n}_ac.glb --side "L= L " --side "R= R " --clips Fidget,Fidget3 --outer-only | grep -E "ARMCLEAR|ARM_CLEAR" | cut -c1-200 || true
# Fidget (left forearm over the bust) and Fidget3 (hands smoothing the apron): arm_clear turns, spread over time; Fidget3 passes
# the jitter gate only at hold 0.15 s, sigma 0.12 s (HOF1 with 80 % of its 18 deg turn: the linings made it deeper)
$CAP $V scripts/smooth_correction.py $cur work/mm9_${n}_ac.glb work/mm9_${n}_sc0.glb --clip Fidget --joint "Bip01 L UpperArm" --joint "Bip01 R UpperArm" --hold 0.15 --sigma 0.08 2>/dev/null | grep SMOOTH | cut -c1-200
$CAP $V scripts/smooth_correction.py $cur work/mm9_${n}_sc0.glb work/mm9_${n}_sc.glb --clip Fidget3 --joint "Bip01 L UpperArm" --joint "Bip01 R UpperArm" --hold ${F3H:-0.15} --sigma ${F3S:-0.12} --gain ${F3G:-$F3GD} 2>/dev/null | grep SMOOTH | cut -c1-200
cur=work/mm9_${n}_sc.glb
if [[ -f scripts/hand_rest_phof.txt ]]; then
  while IFS= read -r line; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    i=$((i + 1)); nxt=work/mm9_${n}_rest${i}.glb
    eval "$CAP python3 scripts/hand_rest.py $cur $nxt $line" | grep HANDREST | cut -c1-200
    cur=$nxt
  done < scripts/hand_rest_phof.txt
fi
cp "$cur" export/mm9_${n}_lod0.glb
python3 "$repo/tools/prepare_actor_glb.py" export/mm9_${n}_lod0.glb export/mm9_${n}_runtime_lod0.glb
$CAP /snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm9_${n}_runtime_lod0.glb" \
  "$here/export/mm9_${n}_lods.glb" --mesh-node "$N" --max-influences 4 2>&1 | grep "LOD triangles"
$CAP python3 scripts/shrink_shadow_lods.py export/mm9_${n}_lods.glb export/mm9_${n}_lods_shadowfix.glb "$N" | tail -1 | cut -c1-160
$CAP $V ../claude_shared/region_variants.py export/mm9_${n}_lods_shadowfix.glb work/mm9_${n}_rv.glb textures/$RAMPS 2>/dev/null | tail -1 | cut -c1-200
if [[ $M == 1 ]]; then $CAP $V scripts/tier_head.py work/mm9_${n}_rv.glb work/mm9_${n}_th.glb ${N}Head phof1_b=phofb_tp 2>/dev/null | tail -1 | cut -c1-200
else cp work/mm9_${n}_rv.glb work/mm9_${n}_th.glb; fi
python3 scripts/set_material_extras.py work/mm9_${n}_th.glb export/mm9_${n}_extras.glb openyamm_specular=0 pbr.metallicFactor=0
FLOORIN=export/mm9_${n}_extras.glb
if [[ $M == 2 ]]; then
  # HOF2 floor-length dress (coordinator pre-screen of r6, 2026-11-04): skirt joints damped toward Standing (Running flap, Death flare),
  # shins/shoes pulled toward the knee when the knee bends (Walking, Running, Cower, Hit), and hidden in the fall (legs_hide.py, as the
  # robed bodies mm9_wyrdold / mm9_scholar)
  $V scripts/dress_clips.py $FLOORIN work/mm9_${n}_dress.glb ${DRESS_DAMP:---damp Running=0.85,Death=0.6,Dead=0.6} ${DRESS_TUCK:---tuck Walking=0.35,Running=0.2,Cower=0.4,Hit=0.5 --a0 8 --a1 35 --tuck-thigh Walking=0.7,Running=0.35@0:1,Cower=0.7 --t0 12 --t1 35} 2>/dev/null | grep -c DRESSCLIPS >/dev/null
  FLOORIN=work/mm9_${n}_dress.glb
fi
python3 ../claude_shared/floor/floor_fix.py $FLOORIN work/mm9_${n}_floor.glb $(cat ${FLOOR_OPS:-scripts/floor_ops.txt}) --ground-death Death Dead | tail -3
# second pass: the skirt strips bent up wherever the falling dress still dips under the floor after the root pass
python3 ../claude_shared/floor/floor_fix.py work/mm9_${n}_floor.glb work/mm9_${n}_floor2.glb --lift-joints Death Dead --lift-only 'x*,XCOM*' | tail -2 | cut -c1-160
MIRRORIN=work/mm9_${n}_floor2.glb
if [[ $M == 2 ]]; then
  # legs_hide AFTER the floor passes: shrinking the calves before them moved the corpse's lowest point and the ground-death root
  # offsets jerked (Death shoulder-skin jitter 6-10 mm/f2); after them the root motion is the legs-intact solution
  $V scripts/legs_hide.py work/mm9_${n}_floor2.glb work/mm9_${n}_legs.glb ${LEGSHIDE:-Death:0.05:0.35:0.05 Dead:0:0:0.05} 2>/dev/null | tail -1
  MIRRORIN=work/mm9_${n}_legs.glb
fi
$V scripts/mirror_glb.py $MIRRORIN work/mm9_${n}_mirror.glb | tail -1
python3 scripts/fix_winding.py work/mm9_${n}_mirror.glb work/mm9_${n}_wind.glb | tail -1
# 2026-11-04 (user review r7: light lines down the cheek and chin with the normal map flat; a dark wedge under the chin): head vertex
# normals averaged across UV seams and the neck seam, under-chin normals turned up/forward with a smooth Gaussian falloff
$V scripts/normal_seams.py work/mm9_${n}_wind.glb export/mm9_peasanthof${M}.glb $([[ $M == 2 ]] && echo --nose-s 0.012) 2>/dev/null | cut -c1-200
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/mm9_peasanthof${M}.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/mm9_peasanthof${M}.glb --world mm9
fi
ls -la export/mm9_peasanthof${M}.glb
