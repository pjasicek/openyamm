# Dragon texture quality pass, head set (MM6 `mm6_cdr1`, DragonCover A/B/C), 2026-11-11

Part of the MM6–MM8 audit fixes, texpass stream, phase B, done by texpass-4
([TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md)). Recipe: [TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md)
and the [handoff](../claude_shared/texpass_mm678/HANDOFF.md); toolkit from `mm8_m440_texpass_claude/scripts/`.
Route of the ADragon head set ([mm7_m182_texpass_claude](../mm7_m182_texpass_claude/README.md), same body lineage).

**Head set only** (`DragonHead_A/B/C`, primitive 1 of `mesh`). The body (32.5 %) and wings (38.5 %) sets are
untouched: each is its own 2048 set with already high density (p50 1,670 and 2,889), so merging would lose texels, and
a per-set pass costs a layout and a paint each. They remain candidates for a later pass (10 credits each).
Only UVs, vertex splits and head images changed; mesh, rig, clips, materials, palette-v7 ramps, variants and
`actors.yml` are the installed ones.

- Production projects: [mm6_cdr1_claude](../mm6_cdr1_claude/README.md) (palette v7, user-requested scale grooves,
  ivory teeth patch) and `mm6_cdr1_reduce_claude`.
- Starting point: the installed GLB, backed up as `work/before_texpass/mm6_cdr1.glb` with its `actors.yml` entries.
  Lease `mm6:cdr1`.
- **Meshy: 10 credits**, one 4K retexture of the head upload with the production HD masters.

## Route

- `layout_prims [[mesh, 1]]`, paid layout **`work/uv_cut_s.npz`** (`cut_closed=1 max_stretch=1.8 retry_stretch=3.0
  fine=250 steps=0`); the plain run measured the same. Six zero-area UV triangles are degenerate mesh slivers
  (0.04 mm² against a 62 mm² median), present in both layouts; harmless.
- `compose.py textures/tp 1 0.4`: approved colour to 1 texel, 0.4 of the paint's detail (the m182 values), limiter 1.3.
- `detail_guard [25, 50]` (option from `mm7_m218_texpass_claude`): the paint coloured the ivory horns and teeth red and
  repatterned the scales; its detail is dropped where its toned colour disagrees with the approved (61 % of texels
  damped at least a little; [12, 30] damped 78 % and left almost nothing new).
- `normal_carry.py textures/tp 1.5 0.3`: the approved relief (the user's accepted scale grooves) moved per chart, plus
  0.3 of the 4K normal's fine band.
- LOD1 head projected; LOD2/3 head maps (128/64 px) transferred again.

## Results (`texture_quality.py`, `DragonHead_A`)

| | Before | After |
|---|---|---|
| Atlas | 35.3 % | **62.6 %** |
| Equivalent px | 1,217 | 1,621 |
| Density p10 / p50 / p90 | 954 / 1,075 / 1,150 | 1,359 / 1,416 / 1,460 (×1.32) |
| Islands / fragments | 316 / 9.4 % | 147 / 3.3 % |
| Stretch p90 | 1.49 | 1.15 |

**Tone** (sRGB, approved → pass): r1 hide (199.0, 57.5, 18.4) → (198.9, 57.5, 18.4); r2 (169.7, 135.3, 63.0) → same;
rest (ivory) (224.3, 219.8, 195.2) → same; luminance sd within 0.1.

**Look** ([review/cmp_face.png](review/cmp_face.png), tiers A and B, front and 3/4): eyes, teeth, horns, crest stripe
and tier colours as approved; scale outlines a little crisper. The visible gain is small; the gain is the layout
(fragments, stretch) and density for close cameras.

`lod_check.py` measures the first layout primitive of the body mesh, here the unchanged body set, so its numbers are
unchanged (LOD1 7.1 / 52.8).

## Checks

- `glb_diff`: OK. Winding: 0. Flat shading: 0.00 on all three sets.
- Viewer `review/viewer/` check: 54 loads, no console errors.
- `mm6_mm7_mm8_actor_models_build_every_binding`: PASS. Floor (`DragonCover*`): 3 bindings, 0 problems.

**Sheet:** [review/texpass_sheet_cdr1.png](review/texpass_sheet_cdr1.png).

Installed 2026-11-11 with `tools/install_model.py export/mm6_cdr1.glb --world mm6`. To roll back, install
`work/before_texpass/mm6_cdr1.glb`.
