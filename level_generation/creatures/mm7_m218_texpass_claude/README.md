# Elf Spearman texture quality pass (MM7 `mm7_m218`), 2026-11-11

Part of the MM6–MM8 audit fixes, texpass stream, phase B, done by texpass-4
([TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md)). Recipe: [TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md)
and the [handoff](../claude_shared/texpass_mm678/HANDOFF.md); toolkit copied from `mm7_m258_texpass_claude/scripts/`
(via `mm6_bh_texpass_claude`), with one new compose option (`detail_guard`, below).

Only UVs, vertex splits and images changed. Mesh, rig, clips, materials, region ramps, variants `m218_a/b/c` and
`actors.yml` are the installed ones. No clip changed, so the arm and hand gate was not re-run.

- Production projects: [mm7_m218_claude](../mm7_m218_claude/README.md) (HD masters, the painted vine overlay and the
  face's leaf paint from `compose_m218.py`) and [mm7_m218_reduce_claude](../mm7_m218_reduce_claude/README.md).
- Starting point: the installed GLB, backed up as `work/before_texpass/mm7_m218.glb` with its `actors.yml` entries.
  Lease `mm7:m218`.
- **Meshy: 10 credits**, one 4K retexture (`meshy/body_retexture_v2`) with the production HD masters. No head-only
  paint: the face keeps the approved paint (below), so a second paint would add nothing.

## Route

`texpass.json`:
- the 2080×1024 body | head atlas (head half u > 0.51, `head_uv_split`) becomes one 2048 atlas; head ×2.5 so the face
  keeps (here doubles) its density, hands ×1.3, `weld_tol` 0.1 mm;
- paid layout **`work/uv_cut_s.npz`** (`cut_closed=1 max_stretch=1.8 retry_stretch=3.0 fine=250 steps=0`); the plain
  run `work/uv_fine.npz` was the same atlas with 1.2 % fragments;
- region: loincloth; detail limiter 1.3;
- face: `head_sigma 0`, `head_detail 0.35` (the Genie/Manticore rule);
- **`detail_guard [12, 30]`** (new in `scripts/compose.py`): where the tone-matched paint's local colour (opponent
  R−G and yellow−blue, 3-texel blur) differs from the approved one by more than 12 levels, the paint's detail fades
  out (gone at 30), and those texels keep the approved colour unblurred. Reason: the Meshy paint draws its own leaves,
  which do not line up with the designed vine overlay, and its luminance detail drew ghost leaf outlines across the
  skin and soft leaf edges. 51 % of the texels are damped somewhat; the skin grain stays.
- normal: `normal_carry.py textures/tp 1.5 0.3` (approved relief moved per chart plus 0.3 of the 4K normal's fine
  band). The tilt-matched Meshy normal alone added forehead wrinkles and neck veins.

Round 1 (default compose, `head_sigma 1.2`) changed the face: freckles, crow's feet, an older look, ghosted leaves
around the eyes ([review/cmp_face.png](review/cmp_face.png)). Round 2 added the guard and the gentle face
([review/cmp_face_r2.png](review/cmp_face_r2.png)); round 3, installed, keeps guarded texels unblurred
([review/cmp_face_r3.png](review/cmp_face_r3.png), tiers A and C).

## Results (`texture_quality.py`, `Elf_A`)

| | Before (2080×1024) | After (2048²) |
|---|---|---|
| Atlas | 30.3 % | **59.7 %** |
| Equivalent px | 1,146 | 1,583 |
| Density p10 / p50 / p90 | 309 / 551 / 1,811 | 1,333 / 1,402 / 3,421 (body ×2.5, face ×1.9) |
| Islands / fragments | 768 / 7.2 % | 284 / 0.3 % |
| Stretch p90 | 1.78 | 1.14 |

**Tone** (sRGB, approved → pass): loincloth (42.4, 44.9, 113.3) → (42.8, 45.1, 112.8); rest (126.8, 106.5, 77.4) →
(126.7, 106.5, 77.3); luminance sd 41.2 → 40.9.

**LOD colour error** (mean / p99, before → after): LOD1 1.7 / 32.3 → 0.8 / 14.1; LOD2 2.9 / 26.1 → 3.3 / 21.0;
LOD3 6.5 / 47.4 → 6.1 / 35.4.

**Look:** face, eyes, brows and the leaf face paint as approved in every tier; vines, bracers and crown leaves a little
crisper; the skin has a fine grain ([review/cmp_body.png](review/cmp_body.png)). The visible gain is modest: the
designed overlay is the look and stays as painted; the gain is the density for the far LODs and close cameras.

## Checks

- `glb_diff`: OK (only UVs, vertex splits and images; the 2080×1024 maps become 2048²).
- Winding: 0. Flat shading: 0.00.
- Viewer `review/viewer/` check: 66 loads, no console errors.
- `mm6_mm7_mm8_actor_models_build_every_binding`: PASS.
- Floor (`Elf Spearman*`): 3 bindings, 0 problems.

**Sheet:** [review/texpass_sheet_m218.png](review/texpass_sheet_m218.png).

Installed 2026-11-11 with `tools/install_model.py export/mm7_m218.glb --world mm7`. To roll back, install
`work/before_texpass/mm7_m218.glb`.
