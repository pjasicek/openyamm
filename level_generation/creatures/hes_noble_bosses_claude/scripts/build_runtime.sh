#!/usr/bin/env bash
# Runtime GLBs of one Noble boss from work/<boss>/shell_tex.blend (shell, add-ons) and the weapon relief:
#   assemble (body + shell + add-ons, Weapon_R/Socket_Tip/palm joints, Noble_* clips) -> skin variant -> prepare
#   -> colour/shadow LODs -> shadow LODs tucked inside -> burn maps -> emission (shell seams by mask, add-on glow)
#   -> key times, winding; the weapon attachment (grip sleeve, Weapon_R frame) with its glow.
# Usage (repository root): TOK=<lease> scripts/build_runtime.sh <boss> <skin A|B|C> <tip m> <shell glow r,g,b>
#        <addon glow r,g,b|-> [weapon name painting grip sleeve tris weapon_glow r,g,b] [--open-right]
set -euo pipefail
P=level_generation/creatures/hes_noble_bosses_claude
boss=$1 skin=$2 tip=$3 shellglow=$4 addglow=$5; shift 5
open=""; weapon=()
for a in "$@"; do [ "$a" = --open-right ] && open=--open-right || weapon+=("$a"); done
W=$P/work/$boss; E=$P/export
B=$(python3 -c "print('$boss'.title().replace('_',''))")
tools/run_creature_blender.sh --token "$TOK" $P/scripts/assemble.py $boss --tip $tip $open ${EXTRA:-} >/dev/null
python3 $P/scripts/set_skin.py $E/${boss}_lod0.glb $W/skin.glb $skin ${SKIN_HEX:+--skin $SKIN_HEX --shell-mask $W/shell_skin_mask.png}
python3 tools/prepare_actor_glb.py $W/skin.glb $W/runtime_lod0.glb | tail -1
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python $P/scripts/lods.py -- $(realpath $W/runtime_lod0.glb) $(realpath $W)/lods.glb Noble ${LOD_RATIOS:-0.55,0.3,0.15} 2>&1 | grep "LOD triangles"
MESH=Noble python3 $P/scripts/shrink_shadow_lods.py $W/lods.glb $W/near.glb >/dev/null
mats=(--material Noble_Body=body --material Noble_Head=head --material ${B}_Shell=shell)
burn=(Noble_Body=$W/burn_body_burn.png Noble_Head=$W/burn_head_burn.png ${B}_Shell=$W/burn_shell_burn.png)
if python3 -c "import json,struct,sys; r=open('$W/near.glb','rb').read(); n=struct.unpack_from('<I',r,12)[0]; d=json.loads(r[20:20+n]); sys.exit(0 if any(m['name']=='${B}_AddOn' for m in d['materials']) else 1)"; then
  mats+=(--material ${B}_AddOn=addon --material ${B}_AddGlow=addglow)
  burn+=(${B}_AddOn=$W/burn_addon_burn.png ${B}_AddGlow=$W/burn_addglow_burn.png)
fi
$P/work/venv/bin/python $P/../claude_shared/bake_burn_maps.py $W/near.glb $W/burn --node Noble "${mats[@]}" \
  --open Noble_Body --fast Noble_Body=0.6 --ignite B_Wing_L_Lead B_Wing_R_Lead B_Wing_L_Finger3 B_Wing_R_Finger3 >/dev/null
PYTHONPATH=$P/../claude_shared python3 $P/../claude_shared/burn_maps.py $W/near.glb $W/burned.glb "${burn[@]}"
$P/work/venv/bin/python $P/scripts/glow_mask.py $P/textures/${boss}_shell_base.png $P/textures/${boss}_shell_glow.png orange 0.55
python3 $P/../claude_shared/emission.py $W/burned.glb $E/hes_${boss}.glb --material ${B}_Shell \
  --mask $P/textures/${boss}_shell_glow.png --color $shellglow --strength 1.0 | tail -1
if [ "$addglow" != "-" ]; then
  python3 $P/../claude_shared/emission.py $E/hes_${boss}.glb $E/hes_${boss}.glb --material ${B}_AddGlow --color $addglow --strength 1.0 | tail -1
fi
python3 $P/scripts/check_key_times.py $E/hes_${boss}.glb | tail -1
python3 level_generation/decorations/mm8_3d/animated/scripts/check_winding.py $E/hes_${boss}.glb | tail -1
if [ ${#weapon[@]} -ge 7 ]; then
  wn=${weapon[0]} wp=${weapon[1]} grip=${weapon[2]} sleeve=${weapon[3]} wt=${weapon[4]} wglow=${weapon[5]} wlen=${weapon[6]}
  WB=$(python3 -c "print(''.join(x.title() for x in '$wn'.split('_')))")
  $P/work/venv/bin/python $P/scripts/weapon_relief.py $P/references_hd/weapons/$wp.png $P/work/weapons/$wp.npz --length $wlen --step 6 --glow-val 0.7 --glow-sat 0.5 | tail -1
  tools/run_creature_blender.sh --token "$TOK" $P/scripts/make_attachment.py $P/work/weapons/$wp.npz $P/references_hd/weapons/$wp.png \
    $E/${wn}_raw.glb $WB --grip $grip --sleeve $sleeve --tris $wt >/dev/null
  tools/run_creature_blender.sh --token "$TOK" $P/scripts/attachment_lods.py $E/${wn}_raw.glb $W/${wn}_lods.glb >/dev/null
  python3 tools/link_static_model_lods.py $W/${wn}_lods.glb $W/${wn}_linked.glb | tail -1
  python3 $P/../claude_shared/emission.py $W/${wn}_linked.glb $E/hes_${wn}.glb --material ${WB}_Glow --color $wglow --strength 1.0 | tail -1
  python3 level_generation/decorations/mm8_3d/animated/scripts/check_winding.py $E/hes_${wn}.glb | tail -1
fi
ls -la $E/hes_${boss}*.glb
