#!/usr/bin/env bash
# Hesper Kreegan runtime GLBs, NOT installed (the Hesper stage integrates them), both from the gated chain
# (work/rig_v3t.blend) on the same skeleton with the same Carbine_* and Demon_* clips:
# - export/hes_kreegan.glb: the bare Kreegan body (Drudges and later castes with rigid add-ons): export MODE=base ->
#   prepare -> LODs -> skin colour variants -> shrunk shadow LODs -> far LODs repaired (lodrep/) -> key times;
# - export/hes_kreegan_trooper.glb (Trooper A/B/C, 10010-10012): the body with the skinned armour shell (the skin under
#   it removed) -> prepare -> LODs -> colour variants (skin, shell) -> glow variants -> the rigid small parts split out
#   per node (export/hes_kreegan_<part>.glb: pauldron caps, spikes, carapace caps, crest, buckler, tasset, carbine) ->
#   shadow LODs rebuilt from the split body and shrunk -> far LODs repaired -> carbine drop -> key times.
# Usage: TOK=<lease token> LOD_REPAIR_PYTHON=<venv python> scripts/build_runtime_hkr.sh
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
: "${LOD_REPAIR_PYTHON:?set LOD_REPAIR_PYTHON to a Python with pymeshlab, xatlas, scipy}"
lods() {   # $1 = export name: prepare + colour/shadow LODs
  python3 "$repo/tools/prepare_actor_glb.py" export/$1_lod0.glb export/$1_runtime_lod0.glb
  /snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
    --python "$repo/tools/build_actor_lods.py" -- "$here/export/$1_runtime_lod0.glb" "$here/export/$1_lods.glb" --mesh-node HKR 2>&1 | grep "LOD triangles"
}
SKIN=(--extra HKR openyamm_specular=0 --extra HKR pbr.metallicFactor=0
      --extra Demon_White_Claws openyamm_specular=0.3 --extra Demon_White_Claws pbr.metallicFactor=0)
# ---------------------------------------------------------------- bare base
OUT=hes_kreegan
MODE=base DEMON=1 OUT=$OUT scripts/step.sh export_hkr.py
lods $OUT
python3 -c "import json; d = json.load(open('textures/hkr_ramps.json')); d['materials'] = [m for m in d['materials'] if m['base'] != 'HKR_Plate']; json.dump(d, open('textures/hkr_ramps_base.json', 'w'), indent=1)"
python3 ../claude_shared/region_variants.py export/${OUT}_lods.glb export/${OUT}_variants.glb textures/hkr_ramps_base.json "${SKIN[@]}"
MESH=HKR python3 scripts/shrink_shadow_lods.py export/${OUT}_variants.glb export/${OUT}_near.glb
python3 lodrep/repair_glb.py export/${OUT}_near.glb work/lodrep_base export/${OUT}.glb
python3 scripts/check_key_times.py export/${OUT}.glb
# ---------------------------------------------------------------- Trooper caste (skinned shell)
OUT=hes_kreegan_trooper
MODE=trooper DEMON=1 OUT=$OUT scripts/step.sh export_hkr.py
lods $OUT
python3 ../claude_shared/region_variants.py export/${OUT}_lods.glb export/${OUT}_variants.glb textures/hkr_ramps.json "${SKIN[@]}" \
  --extra HKR_Plate openyamm_specular=0.5 --extra HKR_Plate openyamm_specular_mask=true \
  --extra Rifle_A openyamm_specular=0.4 --extra Rifle_A openyamm_specular_mask=true --extra Rifle_A pbr.metallicFactor=0
python3 scripts/glow_variants.py export/${OUT}_variants.glb export/${OUT}_glow.glb
python3 scripts/split_attachments_hkr.py export/${OUT}_glow.glb --body export/${OUT}_split.glb --items scripts/attachments_trooper.json --outdir export
python3 scripts/rebuild_shadows_hkr.py export/${OUT}_split.glb export/${OUT}_shadows.glb
MESH=HKR python3 scripts/shrink_shadow_lods.py export/${OUT}_shadows.glb export/${OUT}_near.glb
# far LODs (LOD2, LOD3 + shadows) by the lod_repair_claude route (lodrep/ = its scripts, via hes_guard_reduce_claude):
# own UVs and 512/256 px far textures filled from LOD0 (region mask RGBA kept), first ladder step passing the gate
# the bulky shell keeps its plate outlines at LOD2 only at ~42 % (the default ladder ties LOD2 and LOD3: r40_25 failed)
LODREP_LADDER=0.42:0.2,0.46:0.2 python3 lodrep/repair_glb.py export/${OUT}_near.glb work/lodrep export/${OUT}_far.glb
# the carbine leaves the hands in the death and lies on the floor (Death, Dead)
python3 scripts/death_carbine_floor.py export/${OUT}_far.glb export/${OUT}.glb export/hes_kreegan_carbine.glb
# seams, studs and the carbine's core glow as emission with bloom (CLAUDE_CREATURE_TEXTURES.md "Emission"): the colour
# per tier in the factor (orange A/B, white-gold C), the separate glow materials emit as a whole
GLOWC=(--color hkr_a=1.0,0.42,0.08 --color hkr_b=1.0,0.36,0.06 --color hkr_c=1.0,0.86,0.55 --strength 1.0)   # >1 clips the colour
for f in export/${OUT}.glb export/hes_kreegan_*.glb; do
  case "$f" in export/hes_kreegan_trooper_*) continue;; esac
  for m in HKR_Glow Rifle_Glow; do
    if python3 -c "import json,struct,sys; r=open(sys.argv[1],'rb').read(); n=struct.unpack_from('<I',r,12)[0]; d=json.loads(r[20:20+n]); sys.exit(0 if any(x.get('name','').startswith(sys.argv[2]) for x in d.get('materials',[])) else 1)" "$f" $m; then
      python3 ../claude_shared/emission.py "$f" "$f" --material $m "${GLOWC[@]}" | tail -1
    fi
  done
done
python3 scripts/check_key_times.py export/${OUT}.glb
rm -f export/*_lods.geometry.glb
ls -la export/hes_kreegan.glb export/${OUT}.glb
