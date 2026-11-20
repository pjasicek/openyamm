#!/bin/bash
# Fre rebuild from the paid inputs (project folder; run under the 12G memory cap): head paint (sym -> fixes) -> finish (body grade, ORM,
# uv_tex) -> positions chain (geo_chain_fre.sh: the same deterministic chain the uploads were made from) -> rig + MM9 clips -> runtime ->
# viewer. Usage: scripts/rebuild_fre.sh <viewer rev> [--install]
# Never regenerated here: work/asm_frozen.npz (add_parts_fre.py + sleeve_rings_pf4.py), work/uv.npz (uv_fre.py: the paid layout),
# textures/pf_*_raw|normal|rough (compose_pf.py), the AO bakes (texpass_bake_ao.py + pad_ao.py on the uploads).
set -e
G=../claude_shared/gltf_venv/bin/python; export PYTHONPATH=/usr/lib/python3/dist-packages
python3 scripts/sleeve_red_fre.py textures/pf_body_raw_meshy.png textures/pf_body_raw.png | tail -1
python3 scripts/collar_feather_fre.py textures/pf_body_raw.png textures/pf_body_raw.png | tail -1
python3 scripts/pad_set_pf4.py 0 textures/pf_body_raw.png textures/pf_body_raw.png > /dev/null
# head set from Meshy's 4K with island-aware padding (the cheek seam line)
python3 scripts/compose_islands_fre.py meshy/fre_head_tex_4k/texture_urls_0_base_color.png textures/pf_head_raw.png 1024 | tail -1
python3 scripts/compose_islands_fre.py meshy/fre_head_tex_4k/texture_urls_0_normal.png textures/pf_head_normal.png 1024 | tail -1
# no sym_paint: on Fre's head it copied gutter texels across the mirror into a dotted line on one cheek (r9 base-colour render)
cp textures/pf_head_raw.png textures/pf_head_b_face.png
[ -f scripts/head_fix_fre.sh ] && bash scripts/head_fix_fre.sh
cp textures/pf_head_b_face.png textures/pf_head_b_final.png
[ -f textures/fre_hair_base.png ] && python3 scripts/hair_tex_fre.py | tail -1      # pass 4: PeasantF2's hair set
python3 scripts/finish_pf.py > /dev/null
[ -f scripts/ao_lift_fre.py ] && python3 scripts/ao_lift_fre.py textures/pf_head_orm.png textures/pf_head_orm.png | tail -1      # pass 4: the old bob's AO off the jaw sides and nape
[ -f work/temple_w.npz ] && python3 scripts/temple_skin_fre.py orm textures/pf_head_orm.png textures/pf_head_orm.png | tail -1
scripts/geo_chain_fre.sh work/uv_tex.npz work/uv_tex2.npz > /dev/null
# collapsed slivers across head UV islands sample one texel each (F3 pass 5)
[ -z "${NOSLIVERFIX:-}" ] && python3 scripts/uv_sliver_fix_pf3.py work/uv_tex2.npz work/uv_tex2.npz textures/pf_head_b_face.png | tail -1
[ -z "${NOSLIVERFIX:-}" ] && NOMOVE=1 python3 scripts/sliver_texel_fre.py work/uv_tex2.npz textures/pf_head_b_face.png textures/pf_head_b_face.png | tail -1
MM9F4=work/mm9_fre.npz CAP_RINGS=${CAP_RINGS:-3,0} BRAID_EASE=${BRAID_EASE:-0.03,0.75} scripts/rig_fre.sh work/uv_tex2.npz 2>&1 | grep -E "Error|Trace" || true
scripts/build_runtime_fre.sh $2 2>&1 | grep -E "WINDING|winding|Error|Trace|install|LOD" || true
scripts/viewer_update.sh $1 > /dev/null
echo REBUILT $1
