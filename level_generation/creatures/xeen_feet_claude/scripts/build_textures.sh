#!/usr/bin/env bash
# Texture set on the v2 layout: v1 4K Meshy maps gutter-filled on their own layout -> transfer onto v2 -> AO gutter ->
# compose (2K colour, 1K normal/ORM/mask, classes) -> gentle grade -> gutter fill last on every map.
# Needs work/uv_v2.npz, texturing/foot_v2_layout.glb, textures/feet_ao_2k.png (scripts/bake_ao.py).
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p work/v1_filled
for m in base_color normal roughness metallic; do cp meshy/foot_retexture_v1/texture_urls_0_$m.png work/v1_filled/; done
python3 ../claude_shared/gutter_fill.py texturing/foot_upload.glb work/v1_filled/texture_urls_0_{base_color,normal,roughness,metallic}.png --in-place
python3 scripts/transfer_paint.py
python3 ../claude_shared/gutter_fill.py texturing/foot_v2_layout.glb textures/feet_ao_2k.png textures/v2_basecolor.png --in-place
python3 scripts/compose_feet.py
python3 ../claude_shared/grade_basecolor.py --ao textures/feet_ao_2k.png --fine 1.0 --local 0.0 --ao-strength 0.5 \
  --contrast 1.06 --saturation 1.15 textures/feet_basecolor.png
python3 ../claude_shared/gutter_fill.py texturing/foot_v2_layout.glb textures/feet_basecolor_graded.png \
  textures/feet_region_mask.png textures/feet_normal_1k.png textures/feet_mr_1k.png --in-place
