# Raven Man texture quality pass (MM8 `mm8_m584`), 2026-11-11

Texpass stream of the MM6–MM8 audit fixes, agent texpass-3 ([TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md)),
after the [recipe](../claude_shared/TEXTURE_QUALITY_PASS.md) and the [handoff](../claude_shared/texpass_mm678/HANDOFF.md).
Only UVs, vertex splits and images change; mesh, rig, the 6 clips, ramps, materials, variants, the polearm attachment
and `actors.yml` stay.

Production project: [mm8_m584_claude](../mm8_m584_claude/README.md). Starting point: the installed GLB, backed up as
`work/before_texpass/mm8_m584.glb` with `actors_entries.yml`. Lease `mm8:m584`. Kit: the `tp_*.py` scripts from
[mm6_natm_texpass_claude](../mm6_natm_texpass_claude/README.md), config `texpass.json`.

## Cause

A 2080 x 1024 body | head atlas. The wings are 83 % of the surface, so the whole body set (wings, torso, legs) had
158 texels per metre (torso 243) on 1,121 islands, 37.6 % of the surface on fragments, stretch p90 2.66; the head set
(beak and face, 1.5 % of the surface) 1,359.

## Route

1. `tp_dump.py`: head set = old atlas u > 0.5, x3.0 (keeps its density); hands x1.3; **wings x0.6** (`Wing|Feather`
   joints; dark feathers, 83 % of the surface).
2. `tp_uv.py`: `uv_fine` and `uv_v2` (head x2, wings x1: 51.9 %, face 654 texels per metre, too low), then
   **`uv_w06`** (fast packer, `fine=250 steps=0`): 54.5 %, 0 % fragments, stretch 1.04. **The paid layout; never
   re-run it.** Texels per metre, installed -> pass: face 1,359 -> 1,334, torso and legs 243 -> 447, wings 149 -> 269.
3. One retexture with the production masters (`references_hd/` 01-04), meshy-7, 4K, our UVs: `body_retexture_v1`,
   **10 credits**. No head paint (the face keeps its approved density; `head_sigma` 1.2 keeps its approved colour).
4. `tp_resample.py`, `tp_bake_ao.py` (0.03), `tp_compose.py`, `tp_apply.py`.

Changes on this model:
- **`tp_apply.py`**: this GLB's LOD2 and LOD3 sample the LOD0 images (no own far-LOD maps), so they are now projected
  per chart like LOD1, with their shadow meshes; before, the far-LOD refill would have overwritten the LOD0 atlas.
  `tp_lod1_check.py` takes `TP_LOD=2/3`.
- The metal parts (`work/metal_faces.npy`, 1,019 faces with approved metallic > 0.5: chest discs, rivets, knee
  plates) keep the approved colour and normal, and within 1-2.5 cm the result fades to the approved colour: the paint
  drew a second, offset rim around the right chest disc.

## Results (`texture_quality.py`, LOD0 `Raven_A`)

| | Before | After |
|---|---|---|
| Image | 2080 x 1024 | 2048² |
| Atlas | 54.2 % | **54.5 %** |
| Equivalent px | 1,531 | 1,512 |
| Density p10 / p50 / p90 | 399 / 594 / 935 | 1,000 / 1,006 / 1,670 |
| Islands / fragments | 1,121 / 37.6 % | 522 / 0.0 % |
| Stretch p90 | 2.66 | 1.04 |

Atlas use is unchanged, but it is now one even layout (the old body set packed everything except the face into one
1K half). Tiers (`tp_tier_tone.py`): loincloth A/B/C within 0.3 sRGB levels, the rest identical (64.3/59.1/56.5);
luminance sd 36.9 -> 38.3. Colour error against LOD0, mean / p99, before -> after: LOD1 1.4 / 24.3 -> 1.0 / 17.5,
LOD2 2.7 / 54.6 -> 2.0 / 37.7, LOD3 4.2 / 90.9 -> 3.2 / 67.3.

## Checks

- `tp_diff.py` OK; winding 0; flat shading 0.00; viewer `check` 0 console errors (36 switches).
- `mm6_mm7_mm8_actor_models_build_every_binding` PASS after install; floor audit Raven Man A/B/C 0 problems; motion
  audit re-run (`audit_after/`, clips identical).
- Sheets: [review/texpass_head_sheet.png](review/texpass_head_sheet.png) (head front and 3/4, whole front),
  [review/texpass_body_sheet.png](review/texpass_body_sheet.png). Beak, eyes and chest discs match the installed
  ones; feathers on the head and wings, leg scales, harness leather and loincloth are crisper.

Installed 2026-11-11 (MM8). Rollback: install `work/before_texpass/mm8_m584.glb`.
