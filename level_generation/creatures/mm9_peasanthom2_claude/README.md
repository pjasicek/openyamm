# MM9 half-orc shopkeeper PeasantHOM2 (tier phom2_a of mm9_phom1) — 3D actor, 2026-11-02

Variants batch (`devdocs/mm9_rework/overnight/VARIANTS_BRIEF.md`). MM9 `MONSTERS.txt` row **59 Shopkeeper** "Peasant Half-Orc
Male C" names `PeasantHOM2.ABC` with skin `PeasantHOM2a`. The mesh comparison (`meshcmp.py peasanthom1:peasanthom2`, re-run
2026-11-02) gives head 0.0 cm, torso max 0.1, arms 3 % over 1.5 cm (max 2.0), legs 0: **PeasantHOM2 is PeasantHOM1's mesh**,
so this is a new tier of the approved `mm9_phom1.glb` (`../mm9_peasanthom1_claude/`, rows 57/58/60), not a new body.
Progress and Meshy receipts: `creature_3d_progress.json` (lease identity `mm9:peasanthom2`).

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_phom1.glb` = `export/mm9_phom1.glb`, sha256 `d79023f04c98385b...` (`tools/install_model.py --world mm9`); before: `0692f374972b17f5...` (HOM1's v16 install), rollback `work/rollback/mm9_phom1_installed_before_phom2.glb` (source) and `work/rollback/mm9_phom1_assets_dev_before_phom2.glb` (cooked runtime copy, sha256 `e33dea80...`) |
| Variants | `phom1_a`, `phom1_b` (approved, unchanged), **`phom2_a`** (new) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` (`scripts/binding.yml` via `scripts/bind_under_lock.sh` under the flock): `MM9 59 Shopkeeper`, skin `phom2_a`; HOM1's scale, strides, look, impact and clips |
| Descriptor | row 59 in `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` (fallback visual 445, the stand-in of `mm9_npc_legacy_replacements.tsv`), tables regenerated (197 rows): 9059 |
| Meshy credits | **20** (4K body retexture 10, 4K head retexture 10, on HOM1's own uploads; backup 3265 before the first job, 3245 after the second; other agents spending too) |
| Viewer | http://127.0.0.1:8912/level_generation/creatures/mm9_peasanthom2_claude/review/viewer/ revision `v1-20261102`, tiers phom2_a, phom1_a, phom1_b (HOM1's viewer GLBs) |

## Decision: own paint, not ramps
MM9's HOM2a is a different man in different clothes (`review/mm9/`, `references_hd/mm9_views_h2.png`): a closed charcoal doublet
with plum pinstripe brocade, gold toggle clasps down the front, a wide burgundy belt with a gold heart buckle, dark grey-green
wool trousers, tall brown boots with gold shin ornaments (HOM1: open plum vest over a cream linen shirt, red-brown trousers,
cream leg wraps); dark wavy hair, moustache and goatee, dark purple-brown horns. Ramps cannot paint a belt, clasps or a closed
front, so the tier has **its own body colour + normal and its own head colour + normal** (as PeasantDM1/DM2 tier B), no
region mask or ramps; ORM is HOM1's (specular 0, metallic 0 at runtime).

## Clips the row plays
Row 59's DAT class `ShopkeeperHalfOrcMaleC` has no placement in the rebuilt maps; the one half-orc shopkeeper object is
`ShopKeeperHalfOrcMaleA` (shopkeeper.scr: BaseWander markers, none names an animation). Default NPCbase.scr -> BaseRun.inc
`LoopAnim Cower`. The phom1 GLB already carries all 11 PEASANTHOMALE clips (Cower, CowerStart, CowerStop included): nothing added.

## Route (scripts/, project folder unless noted)
0. `scripts/mm9_refs.sh` (repo root): MM9 renders of PEASANTHOM2 + skin -> `references_hd/mm9_views_h2.png`,
   `mm9_head_views_h2.png`, `mm9_skin_x4_h2.png`.
1. **Codex masters as edits of HOM1's accepted masters** (the mesh exists, so the views must keep its silhouette):
   `scripts/codex_masters.sh` (brief `references_hd/CODEX_BRIEF.md`; HOM1's five clean body masters as edit targets) and
   `scripts/codex_head.sh` (brief `references_head/CODEX_BRIEF.md`; HOM1's four head views). Calm, warm smile asked for.
   Halo removed (`clean_alpha.py`), then **`scripts/align_masters.py`**: an axis-aligned affine per view fitted to HOM1's
   silhouette (IoU body 0.74-0.90 -> 0.87-0.92, head 0.91-0.96 -> 0.91-0.98) -> `references_hd/clean/`, `references_head/clean/`.
   Overlay `review/masters_aligned_overlay.png`.
2. **Retextures** on HOM1's uploads (`texturing/phom1_body_upload.glb`, `phom1_head_upload.glb`: byte copies, same sha256 as
   HOM1's): `requests/retexture_body.json`, `requests/retexture_head.json` (4K). HOM1's UV scripts not re-run.
3. **Maps**: `v2/scripts/compose_texpass.py phom2 ...` (HOM1's AO), gentle `grade_basecolor.py`, `scripts/sleeve_paint_fix_phom2.py`
   (573 skin texels on the cuffs -> cloth), `v2/scripts/compose_headhand.py phom2 ... --ref-head --hand-gain 1.3`,
   `scripts/hand_clean_phom2.py` (from v2/), **`scripts/mouth_line.py`** (the pale teeth line along the closed mouth's slit ->
   dark lip colour, 1,078 texels; mapped from a flat front close-up via a UV-coded render, `scripts/uv_probe.py`).
4. **Tier**: `scripts/build_tier.sh [--install]`: **`scripts/add_tier.py`** appends variant `phom2_a` to the installed approved
   GLB: two new materials (copies of PHOM1_A / PHOM1Head_A with the new colour/normal images, no ramps), four images appended at
   the end of the binary buffer, one more variant mapping on every primitive (12: LOD0-3, shadow meshes). Then
   `scripts/verify_append.py`, winding, `scripts/variant_glb.py` (viewer GLB).

## Approved PeasantHOM1 tiers unchanged (proof)
- `scripts/verify_append.py` (`review/gates/verify_append.txt`): **OK** — all 1,669 old bufferViews byte-identical at the same
  offsets; every old accessor, image, texture, sampler, material, node, skin, animation identical; old variant mappings identical
  and first; variants `phom1_a`, `phom1_b` unchanged. Added: 2 materials, 4 images, 4 bufferViews.
- `v2/scripts/glb_diff.py` (`review/gates/glb_diff_vs_approved.txt`): all 8 HOM1 images "same"; LOD0 6,103 vertices; **0.000 mm
  in every clip** (12 clips).
- Cooked runtime copy (`assets_dev`): the old materials/images/textures JSON entries are identical, the 8 old `.oytex` URIs
  unchanged; 4 new ones.
- No file in `../mm9_peasanthom1_claude/` was written (none newer than this lease).

## Checks
| Gate | Result |
|---|---|
| Arm/hand, jitter, sleeve poke, floor, bones, detached | geometry and clips identical to HOM1's approved install (0.000 mm), so HOM1's numbers stand (its README). Floor audit `MM9 59 Shopkeeper`: stand 0, walk -1.6..+1.5, living -1.6, dead 0: ok |
| Winding | 0 inverted closed parts |
| Flat shading | 0.00 both materials |
| Texture quality (same UVs as HOM1) | body atlas 60.1 %, spread 1.07, fragments 0.5 %; head set 46.8 %, spread 3.09, fragments 2.9 % |
| Viewer check | 36 switches, 0 failed, 0 console errors |
| Binding regression `mm9_actor_models_build_every_binding` | **PASS**, 197 descriptors on 85 models (`review/gates/regression_binding.log`) |
| See-through (`scripts/see_through_gate.py`, PeasantDM2's, every 3rd frame, 16 views; `review/gates/see_through/`) | worst background pixels: sleeve L 33 (Talk 231), sleeve R 24 (Death 36), torso 43 (Cower 0, the hem from behind), collar 10, trousers R 125 / L 114 (Running 9 / 0 only: the knee crease opening from 20 deg above), boots 0. **This is PeasantHOM1's approved mesh** (identical geometry): lining it would change the approved tiers, so it is left and reported |

Sheets read: `review/sheet_mm9_vs_ours.png` (MM9 HOM2a / HOM1a vs ours, front, q34, back), `review/first_body.png`
(Standing, Talk 100, Walking 20; four sides), `review/first_head.png`, `review/face_eyes.png` + `review/face_eyes_h1.png`
(eyes/mouth vs the approved HOM1), `review/face_mouth2.png` (after mouth_line), `review/sheet_ears_first.png` (both ears, backs,
under the jaw, party view; HOM1a above for reference), `review/see_through_worst.png`, `review/masters_aligned_overlay.png`,
`review/body_paint_h1_vs_h2.png`, `review/head_paint_h1_vs_h2.png`.

## Deviations and open points
- The Codex views drift from HOM1's outline (fitted by an affine, IoU >= 0.87); Meshy projected them onto HOM1's exact mesh.
  Small mismatches: the doublet's front clasps sit on HOM1's vest opening; the horns' ring shading.
- The thin line on the left side of the nose bridge is in the approved HOM1 too (geometry/UV seam), not touched.
- The closed mouth shows the inner lip faces from below (as HOM1); a faint pale wisp remains at the slit corners.
- Ears: skin with the hair's sideburn in front of them, as MM9; no foreign texels found (`review/sheet_ears_first.png`).
- See-through holes of HOM1's mesh (above).

## Not checked
No in-game run (map placement is the orchestrator's: the maps still place the stand-in 445); motion at normal speed not watched
(clips are HOM1's approved ones); LOD1-3 not looked at with the new paint; user artistic acceptance not recorded.


**LOD0 reduced post-install on 2026-11-05 by `level_generation/creatures/mm9_peasanthom_reduce_claude/`** (HOM2 is the `phom2_a` tier of `mm9_phom1.glb`; ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction", row 84). `add_tier.py` appends to the installed file, so a tier rebuild must start from the reduced GLB, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_peasanthom_reduce_claude/before/`.
