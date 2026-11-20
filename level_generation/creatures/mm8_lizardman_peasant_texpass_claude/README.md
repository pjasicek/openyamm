# MM8 Lizardman Peasant texture quality pass (`mm8_lizardman_peasant`), 2026-11-12

The user compared the 2026-11-11 rebuild with the original and decided: "lizardman definitely the older animations...
just need new retexture pass". The rebuild was reverted (see
[the rebuild README, follow-up 2026-11-12](../mm8_lizardman_peasant_rebuild_claude/README.md)) and this pass was run on
the reinstalled original: Meshy auto-rig, original clips, `Lizardman_A/B/C` with the 2026-10-19 garment/trim ramps
([tiers](../mm8_lizardman_peasant_tiers_claude/README.md)). Only UVs (with the vertex splits they need) and images
changed; mesh, rig, weights, clips, materials, variants, ramps and `actors.yml` are the installed ones
(`scripts/glb_diff.py`: "OK: only UVs, vertex splits and images differ").

Agent fix-lizardman-anim, lease `mm8:lizardman_peasant` (token in `work/LEASE.txt`). Recipe:
[TEXTURE_QUALITY_PASS.md section 0](../claude_shared/TEXTURE_QUALITY_PASS.md#0-default-pipeline-since-2026-11-12-uv-study)
and the [MM6-MM8 handoff](../claude_shared/texpass_mm678/HANDOFF.md). Toolkit: texpass-2's config-driven scripts
(copied from `mm6_wwf_texpass_claude/scripts`, compose with `detail_guard` from `mm7_m218_texpass_claude`), `texpass.json`.

**Meshy: 10 credits** (one 4K body retexture, `meshy/body_retexture_v2`, backup account; 455 before the job). Masters: the
gated 2026-10-06 Codex masters made from the native m400 bitmaps (`../mm8_m400/3d_20261006/references/`, the ones the
original model was built from), as the alpha-matted copies in `references_hd/`. No head-only paint (see Face).

## Cause

The installed body used a 2080x1024 body | head atlas laid out by Smart UV: 2,654 islands, 49.4 % of the surface on
fragments (islands under 8 triangles), stretch p90 2.63, density spread 3.2.

## Route

1. `dump.py` (head = the faces in the old atlas's head half, u > 0.5; 1,147 faces), weld 1e-4.
2. `uv.py` (Blender) -> `claude_shared/uv_atlas.py` with the 2026-11-12 defaults (PartUV charts, seam pass, sparrow
   packing), head x1.8, hands x1.3. **The paid layout is `work/uv_v4.npz`; never re-run it.** Defaults alone (uv_v1)
   gave 70.1 % atlas but 9.2 % fragments: 150 merged charts were reverted for the 1.25 stretch limit, and the remaining
   fragments sit on Meshy's folds (334 edges shared by three or more faces; 503 of their incidences are on fragment
   triangles; splitting those edges did not help). Final options: `cut_closed=1 max_stretch=2.0 max_edge_stretch=6
   max_density_ratio=4 merge_below=60 partuv_threshold=2.5` (trials `work/try_a..f`, fast packs; full sparrow 5 x 60 s
   for v4).
3. `resample.py` (approved maps on the layout), `bake_ao.py` (reach 0.035 m), Meshy 4K retexture on
   `texturing/uv_v4_body_upload.glb` (the return reports the same layout).
4. `compose.py`: 4K -> 2K once, gentle grade, tone per class (garment, trim, rest) onto the approved colours, then
   the approved colour below 4 texels plus the paint's luminance detail x0.9, detail limiter 1.3, `detail_guard`
   [12, 30] (the paint's detail fades where its local colour disagrees with the approved: 68 % of texels damped, so the
   outfit pattern, apron checks and scale plates stay the original's), head islands `head_sigma` 1, `head_detail` 0.5.
   Normal from the paint, +y converted, tilt scaled to the approved p90 (x0.41); mask and metal/roughness approved.
   A variant without the guard (`textures/tp_ng_*`, `work/apply_tp_ng.glb`) drew Meshy's own smaller scales over the
   face and read busier; not used (`review/close_sheet1.png`, rows: installed, no guard, guard).
5. `claude_shared/gutter_fill.py` on all four maps (last step), `apply.py` (LOD0 and its shadow get the layout; LOD1 and
   shadow projected per chart; the lod_repair far LODs LOD2/3 keep their UVs and get the maps transferred at 512/256),
   `finish.sh --install`.

## Results (`texture_quality.py`, LOD0 base colour)

| | Before | After |
|---|---|---|
| Image | 2080 x 1024 (body \| head) | 2048 x 2048 |
| Atlas | 44.6 % | **67.6 %** (gate 65 %) |
| Equivalent px | 1,389 | 1,684 |
| Density p10 / p50 / p90 | 349 / 500 / 1,114 | 1,167 / 1,230 / 1,609 |
| Spread | 3.2 | 1.38 (head x1.8 by design) |
| Islands / fragments | 2,654 / 49.4 % | 537 / **4.8 %** |
| Stretch p90 | 2.63 | 1.31 |
| LOD1 colour vs LOD0 (mean / p95 levels) | 10.1 / 39.0 | 7.8 / 35.9 |

Tone (`textures/tp_tone.json`, area-weighted sRGB means, approved -> pass): garment (44.2, 115.3, 56.9) -> (44.8,
115.1, 56.9); trim (128.6, 84.8, 38.1) -> (126.9, 85.7, 39.1); rest (81.8, 105.0, 105.0) -> (81.9, 104.9, 104.7).
Tiers B (tan / purple) and C (crimson / pale grey) come from the unchanged ramps on the new mask.

**Face:** the approved face and eyes are kept (head colour at 1 texel, half the paint's detail, the guard); the
close-ups match the original, and the old chart seams across the snout are gone (`review/cmp_face.png`, every tier
front and three-quarter; head density p50 1,900 -> 2,163, stretch p90 1.72 -> 1.33). At extreme magnification the
snout's fine noise is a touch softer than the original's (head colour resampled at 1 texel).

## Checks (installed 2026-11-12)

- `glb_diff.py`: only UVs, vertex splits (LOD0 13,079 -> 15,188, LOD1 7,768 -> 8,770, and their shadows) and the four
  LOD0 images; winding 0 inverted closed parts; flat shading 0.00; `detached_parts_audit.py`: 0 detached.
- Floor audit (A/B/C): 0 problems. No clip changed, so no gait/stride check and no arm and hand gate are needed
  (clips, skin and weights byte-identical per `glb_diff.py`).
- `mm6_mm7_mm8_actor_models_build_every_binding`: PASS (647 descriptors, 0 failed). Whole actors suite: 191 passed,
  2 failed, neither this model: `every_map_loads_and_builds_its_actor_models` (42 problems, all MM9 BLV maps without
  models) and `out05_event_clearance_completes_from_monster_killed_hook` (fails alone too; uncommitted `game/events`
  work in the tree). `mm8_lizardman_peasant_actor_model_keeps_native_roles` passes.
- Review viewer (`tools/run_creature_review.py --project ... check`): 48 switches, 0 console errors.
- Compare viewer (`../audit_mm678_20261111/compare_viewer/`, manifest rebuilt with its `build.py` after the install):
  `review/compare_sheet.png` (tier A front, A head, B three-quarter, C head; left the original, right the pass) and
  `review/compare/t{0,1,2}_{front,three-quarter,head_close-up}.png`.
- Sheets: `review/texpass_sheet_m400.png` (every tier, installed | pass, identical cameras), `review/close_sheet1.png`
  (chest, arm, apron, shin fringe, head front and three-quarter), `review/paint_vs_approved.png` (atlases).

Revert: `python3 tools/install_model.py level_generation/creatures/mm8_lizardman_peasant_texpass_claude/work/before_texpass/mm8_lizardman_peasant.glb --world mm8`
(the original as reinstalled, sha256 77a5986a...; `actors.yml` was not touched).
