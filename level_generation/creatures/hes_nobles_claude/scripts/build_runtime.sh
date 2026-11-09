#!/usr/bin/env bash
# Runtime GLBs of one Noble model (not installed: the Hesper stage binds them through integration/actors.yml), after
# the Blender chain (add_sockets, carapace.sh, build_clips, assemble, export_noble) wrote export/<out>_lod0.glb:
# prepare -> colour/shadow LODs -> burn maps baked and embedded (every skinned material) -> tier variants (skin and
# carapace ramps, textures/nb_ramps.json) -> seam glow per tier -> weapons and gear split out per socket
# (scripts/attachments_<out>.json) -> shadows rebuilt from the split body and shrunk -> far LODs (lodrep/) -> emission
# with bloom on the glow materials -> burn maps checked on every variant/LOD -> key times.
# Usage: LOD_REPAIR_PYTHON=<venv python> scripts/build_runtime.sh <out>
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
OUT=${1:?export name}
: "${LOD_REPAIR_PYTHON:?set LOD_REPAIR_PYTHON to a Python with pymeshlab, xatlas, scipy}"
S=../claude_shared
python3 "$repo/tools/prepare_actor_glb.py" export/${OUT}_lod0.glb export/${OUT}_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${OUT}_runtime_lod0.glb" "$here/export/${OUT}_lods.glb" --mesh-node NOBLE 2>&1 | grep "LOD triangles"
# burn maps in each material's UV space (every material of the mesh, weapons too: the baker wants them all): wing rims
# open and fast, ignition at the head, hands and wing tips
MATS=$(python3 -c "import json,struct,sys; r=open(sys.argv[1],'rb').read(); n=struct.unpack_from('<I',r,12)[0]; d=json.loads(r[20:20+n]); print(' '.join(m['name'] for m in d['materials']))" export/${OUT}_lods.glb)
BAKE=(); EMBED=()
for m in $MATS; do lab=$(echo $m | tr 'A-Z' 'a-z'); BAKE+=(--material $m=$lab); EMBED+=($m=work/burn/${OUT}_${lab}_burn.png); done
(cd $S && python3 bake_burn_maps.py "$here/export/${OUT}_lods.glb" "$here/work/burn/${OUT}" --node NOBLE "${BAKE[@]}" \
  --open NB_Body --fast NB_Body=0.6 --ignite B_Head B_L_Hand B_R_Hand B_Wing_L_Lead B_Wing_R_Lead | tail -1)
python3 $S/burn_maps.py export/${OUT}_lods.glb export/${OUT}_burn.glb "${EMBED[@]}"
python3 $S/region_variants.py export/${OUT}_burn.glb export/${OUT}_variants.glb textures/nb_ramps.json \
  --extra NB_Body openyamm_specular=0 --extra NB_Body pbr.metallicFactor=0 \
  --extra NB_Head openyamm_specular=0 --extra NB_Head pbr.metallicFactor=0 \
  --extra NB_Plate openyamm_specular=0.5 --extra NB_Plate pbr.metallicFactor=0
python3 scripts/glow_variants.py export/${OUT}_variants.glb export/${OUT}_glow.glb
python3 scripts/split_attachments.py export/${OUT}_glow.glb --body export/${OUT}_split.glb --items scripts/attachments_${OUT}.json --outdir export
# the rigid attachments do not burn; the split copied the body's burn-map extras without their textures
python3 scripts/strip_attachment_burn.py $(python3 -c "import json; print(' '.join('export/' + i['name'] + '.glb' for i in json.load(open('scripts/attachments_${OUT}.json'))))") | tail -1
python3 scripts/rebuild_shadows.py export/${OUT}_split.glb export/${OUT}_shadows.glb
MESH=NOBLE python3 scripts/shrink_shadow_lods.py export/${OUT}_shadows.glb export/${OUT}_near.glb
python3 lodrep/repair_glb.py export/${OUT}_near.glb work/lodrep_${OUT} export/${OUT}.glb
GLOWC=(--color nb_a=1.0,0.50,0.12 --color nb_b=1.0,0.36,0.06 --strength 1.0)
for v in nb_c nb_ssekh nb_mraal nb_xith nb_gatekeeper; do GLOWC+=(--color $v=1.0,0.86,0.55); done
python3 $S/emission.py export/${OUT}.glb export/${OUT}.glb --material NB_Glow "${GLOWC[@]}" | tail -1
for item in $(python3 -c "import json,sys; print(' '.join(i['name'] for i in json.load(open('scripts/attachments_${OUT}.json'))))"); do
  python3 $S/emission.py export/$item.glb export/$item.glb --material NB_WeaponGlow --color 1.0,0.45,0.10 --strength 1.0 | tail -1 || true
done
python3 scripts/check_burn.py export/${OUT}.glb
python3 scripts/check_key_times.py export/${OUT}.glb
rm -f export/${OUT}_runtime_lod0.glb export/${OUT}_lods.geometry.glb
ls -la export/${OUT}.glb
