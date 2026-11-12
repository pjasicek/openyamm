# Flying Eye texture quality pass (MM6 `mm6_bh`, BBeholder A/B/C), 2026-11-11

Part of the MM6–MM8 audit fixes, texpass stream, phase B, done by texpass-4
([TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md)). Recipe: [TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md)
and the [handoff](../claude_shared/texpass_mm678/HANDOFF.md); toolkit copied from `mm7_m258_texpass_claude/scripts/`.

Only UVs, vertex splits and images changed. Mesh, rig, clips, materials, region ramps, variants `bh_a/b/c` and
`actors.yml` are the installed ones.

- Production projects: [mm6_bh_claude](../mm6_bh_claude/README.md) (HD masters, regions skin / face / iris) and
  [mm6_bh_reduce_claude](../mm6_bh_reduce_claude/README.md) (reduction, fitted teeth, ivory cell, horn repairs).
- Starting point: the installed GLB (with the 2026-10-21 floor fix), backed up as `work/before_texpass/mm6_bh.glb`
  with its `actors.yml` entries. Lease `mm6:bh`.
- **Meshy: 10 credits**, one 4K retexture (`meshy/body_retexture_v2`) with the production HD masters (front, left,
  back, right). No head-only paint: the whole creature is a head and its one face is on the same atlas.

## Route

`texpass.json` settings:
- layout mesh `Eye`; EyeBall bone ×1.5 (217 faces), the rest uniform;
- regions skin, face, iris; detail limiter 1.3;
- **`keep_approved_regions: [iris]`, grow 3**: the iris and the pupil it encloses keep the approved paint exactly
  (eye lesson from the Water Elemental and Genie);
- paid layout **`work/uv_cut.npz`** (`cut_closed=1 max_stretch=1.8 retry_stretch=3.0 fine=250 steps=0`; never
  re-run). The plain fast-packer layout `work/uv_fine.npz` measured the same (53.6 %, 0.2 % fragments) and was not used.
- Default compose (sigma 4, detail 0.9): the approved colour below 4 texels per island, the paint's luminance detail
  above it. The low band carries the approved horn repairs, ivory teeth and native shading; the Meshy paint brings
  only the fine grain. LOD1 projected, LOD2/3 maps transferred again.

## Results (`texture_quality.py`, `Eye_A`)

| | Before | After |
|---|---|---|
| Atlas | 27.6 % | **53.7 %** |
| Equivalent px | 1,075 | 1,501 |
| Density p10 / p50 / p90 | 386 / 485 / 531 | 611 / 644 / 681 (×1.33 median) |
| Islands / fragments | 815 / 9.9 % | 222 / 0.1 % |
| Stretch p90 | 1.88 | 1.23 |

**Tone** (area-weighted sRGB, approved → pass): skin (56.3, 33.1, 25.0) → (57.1, 33.9, 25.7); face (88.0, 79.8, 71.7)
→ (86.8, 78.6, 70.6); iris kept (109.4, 115.3, 18.1). Luminance sd skin 18.1 → 19.2, face 32.3 → 30.7.

**LOD colour error** (mean / p99, before → after): LOD1 7.6 / 67.0 → 6.3 / 48.0; LOD2 6.2 / 43.6 → 6.6 / 33.2;
LOD3 11.0 / 68.8 → 9.6 / 51.5.

**Close-ups** ([review/cmp_eye.png](review/cmp_eye.png), tiers A and B, installed left): the shattered triangles on the
grey face are gone; the brow ridges, pebbled face and back lumps are crisp. Eye unchanged in every tier (the small
jagged notch at the pupil's upper left is in the approved paint and was kept). Teeth stay ivory; horn stripes unchanged.

## Checks

- `glb_diff`: OK (only UVs, vertex splits and images: Eye 8,053 → 9,493, LOD1 4,606 → 6,034 vertices).
- Winding: 0 inverted closed parts. Flat shading: 0.02 (unchanged).
- Clips identical (`glb_diff`), so motion was not re-measured.
- Viewer `review/viewer/` check: 54 loads, no console errors.
- `mm6_mm7_mm8_actor_models_build_every_binding`: PASS (647 descriptors on 185 models).
- Floor (`BBeholder*`): 3 bindings, 0 problems.

**Sheet:** [review/texpass_sheet_bh.png](review/texpass_sheet_bh.png) (head front, head 3/4, top, side, whole body;
tiers A/B/C, installed against pass).

Installed 2026-11-11 with `tools/install_model.py export/mm6_bh.glb --world mm6`. To roll back, install
`work/before_texpass/mm6_bh.glb`.
