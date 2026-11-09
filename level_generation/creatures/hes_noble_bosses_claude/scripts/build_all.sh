#!/usr/bin/env bash
# All four Noble bosses' runtime GLBs and weapons (repository root; TOK=<lease>). Shells and add-ons must exist
# (work/<boss>/shell_tex.blend: fit_shell -> shell_finish -> uv_shell -> shell_material -> transfer_tex -> make_addons;
# see the README). Then the review viewer.
set -euo pipefail
P=level_generation/creatures/hes_noble_bosses_claude
# the shells' gold lifted toward the concepts (from the *_raw.png bakes, idempotent)
for b in vhorrax coil_keeper conductor hierarch; do python3 $P/scripts/grade_gold.py $P/textures/${b}_shell_base.png 1.3 1.1; done
# own skins (integrator, 2026-10-24): Vhorrax oxblood, the Coil Keeper storm blue, the Conductor pale lilac; the
# Hierarch keeps the concept plum (ov_c). Region ramps only (set_skin.py --skin), no baked colours.
SKIN_HEX=5a1f1f EXTRA=--wing-spread $P/scripts/build_runtime.sh vhorrax B 0.80 1.0,0.42,0.1 - \
  vhorrax_courtesy vhorrax_courtesy 0.155 0.095,0.205 1400 1.0,0.5,0.15 0.95
SKIN_HEX=2f4a7a EXTRA=--wing-spread $P/scripts/build_runtime.sh coil_keeper A 0.90 1.0,0.42,0.1 0.62,0.3,1.0 \
  coil_spear coil_spear 0.55 0.49,0.61 1100 0.62,0.3,1.0 1.45
SKIN_HEX=a898c0 EXTRA=--wing-spread $P/scripts/build_runtime.sh conductor C 0.85 1.0,0.42,0.1 0.8,0.68,1.0 \
  conductor_baton conductor_baton 0.45 0.39,0.51 1200 0.8,0.68,1.0 1.40
EXTRA="--wing-spread --seated" $P/scripts/build_runtime.sh hierarch C 0.30 1.0,0.42,0.1 1.0,0.42,0.1 --open-right
# the faltering Hierarch (10146): skin hierarch_dark turns the spinal cables' glow off
python3 $P/scripts/add_variants.py $P/export/hes_hierarch.glb $P/work/hierarch/var.glb hierarch hierarch_dark Hierarch_AddGlow
python3 $P/../claude_shared/emission.py $P/work/hierarch/var.glb $P/export/hes_hierarch.glb --material Hierarch_AddGlow \
  --color hierarch=1.0,0.42,0.1 --color hierarch_dark=0.0,0.0,0.0 --strength 1.0
python3 $P/scripts/check_key_times.py $P/export/hes_hierarch.glb | tail -1
# the enthroned Hierarch's throne (10145): fitted under the seated pose, in the Throne joint's frame
tools/run_creature_blender.sh --token "$TOK" $P/scripts/fit_throne.py --tris 3000 >/dev/null
tools/run_creature_blender.sh --token "$TOK" $P/scripts/attachment_lods.py $P/export/hes_hierarch_throne.glb \
  $P/work/hierarch/throne_lods.glb >/dev/null
python3 tools/link_static_model_lods.py $P/work/hierarch/throne_lods.glb $P/work/hierarch/throne_linked.glb | tail -1
$P/work/venv/bin/python $P/scripts/glow_mask.py $P/meshy/throne_v1/texture_urls_0_base_color.png \
  $P/textures/throne_glow.png orange 0.6
python3 $P/../claude_shared/emission.py $P/work/hierarch/throne_linked.glb $P/export/hes_hierarch_throne.glb \
  --material Hierarch_Throne --mask $P/textures/throne_glow.png --color 1.0,0.42,0.1 --strength 1.0 | tail -1
python3 $P/scripts/png_images.py $P/export/hes_hierarch_throne.glb $P/export/hes_hierarch_throne.glb
python3 level_generation/decorations/mm8_3d/animated/scripts/check_winding.py $P/export/hes_hierarch_throne.glb | tail -1
# the same throne as D12's permanent decoration (it stays when 10145 is hidden at phase 2): metres, feet origin
tools/run_creature_blender.sh --token "$TOK" $P/scripts/throne_decoration.py 286 >/dev/null
python3 tools/link_static_model_lods.py $P/work/hierarch/throne_deco_raw.glb $P/work/hierarch/throne_deco_linked.glb | tail -1
python3 $P/../claude_shared/emission.py $P/work/hierarch/throne_deco_linked.glb $P/export/hes_hierarch_throne_deco.glb \
  --material Hierarch_Throne --mask $P/textures/throne_glow.png --color 1.0,0.42,0.1 --strength 1.0 | tail -1
python3 $P/scripts/png_images.py $P/export/hes_hierarch_throne_deco.glb $P/export/hes_hierarch_throne_deco.glb
python3 level_generation/decorations/mm8_3d/animated/scripts/check_winding.py $P/export/hes_hierarch_throne_deco.glb | tail -1
python3 $P/scripts/viewer_build.py
