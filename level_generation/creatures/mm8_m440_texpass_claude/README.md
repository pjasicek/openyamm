# Ogre Warrior texture quality pass (MM8 `mm8_m440`), 2026-11-11

Part of the MM6–MM8 audit fixes, texpass stream, phase B, done by texpass-4
([TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md)). Recipe: [TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md)
and the [handoff](../claude_shared/texpass_mm678/HANDOFF.md); toolkit from `mm7_m218_texpass_claude/scripts/`.

Only UVs, vertex splits and images of the body GLB changed. Mesh, rig, clips, materials, cloth ramps, variants
`m440_a/b/c`, the club (`mm8_m440_club.glb`, untouched) and `actors.yml` are the installed ones. No clip changed.

- Production projects: [mm8_m440_claude](../mm8_m440_claude/README.md) and
  [mm8_m440_reduce_claude](../mm8_m440_reduce_claude/README.md).
- Starting point: the installed GLB, backed up as `work/before_texpass/mm8_m440.glb` with its `actors.yml` entries.
  Lease `mm8:m440`.
- **Meshy: 10 credits**, one 4K retexture (`meshy/body_retexture_v2`) with the production HD masters. No head paint.

## Route

`texpass.json`:
- the 2080×1024 body | head atlas (head from u 0.508, `head_uv_split 0.5`) becomes one 2048 atlas; head ×2.5, hands
  ×1.3, `weld_tol` 0.1 mm;
- paid layout **`work/uv_cut_s.npz`** (`cut_closed=1 max_stretch=1.8 retry_stretch=3.0 fine=250 steps=0`);
- region: cloth; detail limiter 1.3; face `head_sigma 0`, `head_detail 0.35`;
- default normal (Meshy 4K, tilt matched); no `detail_guard` (the paint's straps and plates follow the approved ones).
- Every LOD of this model shares the LOD0 images, so LOD1–3 were all projected per chart (no separate far-LOD maps).
- `scripts/apply.py`: the shadow-copy tolerance now allows the 30 mm inset cap of this model's `finish_runtime.py`
  (same triangles; LOD1–3 shadows are inset 10–30 mm by design).
- Viewer shots aim at the face (`head_offset [0, -0.02, 0.15]`): the hunched chest strap hides the head bone.

## Results (`texture_quality.py`, `M440_A`)

| | Before (2080×1024) | After (2048²) |
|---|---|---|
| Atlas | 31.5 % | **56.2 %** |
| Equivalent px | 1,168 | 1,535 |
| Density p10 / p50 / p90 | 307 / 397 / 1,039 | 786 / 819 / 1,905 (body ×2.1, face ×1.8) |
| Islands / fragments | 813 / 3.1 % | 352 / 0.1 % |
| Stretch p90 | 1.78 | 1.14 |

**Tone** (sRGB, approved → pass): cloth (76.2, 83.1, 49.8) → (76.6, 83.1, 50.1); rest (119.9, 86.7, 63.9) → unchanged.

**LOD colour error** (mean / p99, before → after): LOD1 4.5 / 54.4 → 1.8 / 26.2; LOD2 9.0 / 73.2 → 4.3 / 44.9;
LOD3 12.9 / 86.4 → 6.9 / 64.1.

**Look:** face, eyes, tusks and teeth as approved in every tier ([review/cmp_face.png](review/cmp_face.png), tiers A
and C, front and 3/4); helmet iron, chainmail, studs and plates finer; cloth tiers green/blue/red kept
([review/cmp_body.png](review/cmp_body.png)).

## Checks

- `glb_diff`: OK. Winding: 0. Flat shading: 0.00.
- Viewer `review/viewer/` check: 60 loads, no console errors.
- `mm6_mm7_mm8_actor_models_build_every_binding`: PASS. Floor (`Ogre Warrior*`): 3 bindings, 0 problems.

**Sheet:** [review/texpass_sheet_m440.png](review/texpass_sheet_m440.png).

Installed 2026-11-11 with `tools/install_model.py export/mm8_m440.glb --world mm8`. To roll back, install
`work/before_texpass/mm8_m440.glb`.
