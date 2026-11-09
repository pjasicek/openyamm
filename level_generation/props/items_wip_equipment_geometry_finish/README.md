# Equipment geometry finish — 2026-10-18

**13 of 13 item entries complete and individually installed; 11 of 11 unique geometry sources.** The first six were finished in the initial pass; the seven previously deferred entries were finished afterwards (see [Finishing the deferred seven](#finishing-the-deferred-seven)). Additional Meshy spend: **20 / 200 credits**, four necessary Smart Topology jobs after local attempts failed; no further paid work.

[Handoff](handoff.json) contains every decision, final export/source/runtime hash and proposed bounds. [Ledger](ledger.json) is the per-icon status record. Shared `items.yml`, binding lengths, engine code, settings and the original equipment project were not edited. No builds, global cooks, staging or commits were run.

| Installed entry | Source | Triangles | Result |
|---|---|---:|---|
| Old Leather Boots `6boots1` | own local repair | 3400 | Continuous feet/cuffs, deep leather interiors, physical brass buckles |
| Ultimate `6boots5`, Lucius `6boots6`, Hermes `6boots7` | one shared local repair | 3186 each | Deep open shafts; same source GLB and texture set |
| Moon Cloak `7item348` | preserved painted cloth plus new hardware | 3388 | Real closed gold crescent seated on supporting folds |
| Fancy Hat `7item096` | own local repair and new exact-guide painting | 2800 | Continuous gathered crown and rim, green gem/brass setting |

The three special boots have identical original icon pixels, identical unprocessed/source GLBs and identical cooked geometry/texture references. Only the cooked containers' source-path receipts differ. Their original pair width was restored after separating touching feet; all five original painted views and masks then passed registration against the newly rendered repaired guides. Deep interiors are geometry, not painted caps.

Old Leather Boots use the coordinator's reviewed per-face material-class path. Actual buckle solids are brass; feet, bands, shafts and lining are leather. This corrects shaded green generated mask pixels that otherwise classified the lining as glossy black/gem. The 3400-triangle budget preserves both physical interiors. Moon Cloak retains the prior 3200-triangle cloth body and adds 188 brooch triangles; its original body geometry and UVs are asserted unchanged, so its existing PBR bake is reused without reprojection or resampling. The hardware uses physical constant-gold PBR. These are the two recorded exceptions to the usual 3200 budget.

Accepted PBR scenes are `work/codex_tex/geometryfinish_<canonical icon>_pbr.blend`; unprocessed exports are `geometryfinish_<icon>_export.glb`. The special boots share the `6boots5` scene and guides. Exact final guides live in `codex_tex/equipment_<canonical icon>/`. [Moon body registration proof](receipts/moon_body_registration.json), [shared proportions](receipts/shared_boot_proportions.json), [boot identity](receipts/boot_variant_identity.json) and per-folder `final_view_sources.json` identify the accepted sources. Earlier geometry/painting trials are retained work, not accepted outputs. Use `moon_clasp.py` for the final Moon assembly; earlier voxel-cloth routes are rejected.

## Finishing the deferred seven

| Installed entry | Triangles | What was missing and how it was finished |
|---|---:|---|
| Alvar Cloak `item124` | 3002 | Paintings were 12-36% off the guide size; registered (below). Black crease strokes in the masks reclassified to leather |
| Necromancer Cloak `item125` | 3000 | Registered; gems kept only where set in metal fittings, crease strokes reclassified to leather |
| Wreath Crown `6crown1` | 2998 | Registered (the "+27% left width" was a neighbouring view's fragment in the crop); `unseen_material` corrected to the design's horn class |
| Wizard Cap `6hat3` | 2800 | Registered; masks limited to metal and cloth |
| Shadow's Mask `7item344` | 3200 | Old painting had a different shape (slit eyes, filled plate). New paint-only Codex atlas ([brief](codex_tex/equipment_7item344/CODEX_BRIEF_paint_v2.md), `paint_raw_v2.png`) with oval holes; uniform leather class, no mask views |
| Traveller's Hat `7item095` | 3192 | The tears were 30 self-intersecting faces left by decimation in the gathered fold; exact self-union with touching folds separated (`resolve_self_intersections.py`). Silhouette unchanged, so the registered paintings were reused |
| Cloth Hat `6hat1` | 3498 | The cap body was right; Meshy's paper-thin feather crossed the crown and baked as black streaks. Replaced by a solid tapered feather seated in the cuff (`rebuild_6hat1_feather.py`), new guides and a new Codex atlas ([brief](codex_tex/equipment_6hat1/CODEX_BRIEF_paint_v3.md)). The old raw paintings are in `superseded_old_feather/` |

**Registration instead of size-only repainting.** Imagegen keeps a guide's content but not its exact size, and asking it for size-only corrections did not converge. `scripts/register_views.py <icon>` labels the objects of each raw sheet (3x4 paint+mask or 3x2 paint-only) and assigns them to cells by centroid, fits each view's bounding box to its guide, then applies a bounded, smooth multi-scale demons warp of the painted silhouette onto the guide's. A view passes only with warped IoU >= 0.95 and 95th-percentile displacement <= 4% of the object diagonal, so a painting of a different shape is still rejected (the old 7item344 painting failed at 7-14%). Results and every candidate are in each folder's `registration.json`; raw files stay unchanged. Designs may list `material_classes` (and `gems_in_metal`) in `designs.json` to reclassify crease strokes imagegen draws black in masks.

**Geometry gates added.** Zero exposed back faces (rays from 60 directions whose first hit is a back face) and no corner normals opposing their face, for 6hat1, 6hat3, 7item095, item124, item125, 6crown1 and 7item344's sources. Moon Cloak `7item348` follow-up: its preserved cloth body had 207 faces whose imported normals opposed the face (dark creases). `scripts/moon_normals.py` welds the glTF seam splits (positions and UVs unchanged), makes winding consistent and outward, drops those normals and re-smooths; now 0 inverted, textures and crescent unchanged ([before/after](review/7item348_normals_before_after.png)). Thin slits between its interpenetrating cloth layers remain as before.

[Fourteen outdoor captures](review/native_outdoor_finish_contact.jpg) show the seven at binding scale in the MM7 review save (OpenGL 3.3, NVIDIA `0x10de`, exit code zero; receipts in `receipts/native_outdoor_finish/`). No indoor run was made for these seven.

Fresh candidates, exact guides, original generated PNG bytes, exact built-in imagegen prompts, input/output hashes and rejection reasons are retained for resumption. All new image generation used the built-in tool. The original project remains read-only: 216 of 218 recorded input files still match; its two shared baker/fixture scripts changed during concurrent coordinator work and were preserved. Their UV-domain and reviewed material-class corrections were carried into our local copies.

Validation completed:

- Five actual PBR views per accepted unique geometry, beside the original icon, using explicit Backfacing/Transparent culling. Comparisons: [Old boots](review/6boots1_comparison.png), [shared boots](review/6boots5_comparison.png), [Moon](review/7item348_comparison.png), [Fancy Hat](review/7item096_comparison.png).
- Winding, finite positions/normals/UVs, no degenerate triangles, centered footprint, lowest point zero, triangle budgets and three embedded 512px PBR maps including normals.
- Focused pinched-fan, culling, mixed PBR/GLB roundtrip, physical lining, UV triangle-domain and authored per-face class fixtures passed.
- Thirteen individually scoped desktop installs/cook verifications passed (six in the first pass, seven later); export and source hashes agree. Each later install first confirmed its baseline source/runtime hashes were untouched.
- [Twelve outdoor captures](review/native_outdoor_contact.jpg) show actual settled items in the MM7 review save. [Eight indoor captures](review/native_indoor_contact.jpg) show four unique shared-model instances at actual binding scale on the verified flat `6d19.blv` entrance floor. Native OpenGL 3.3, NVIDIA vendor `0x10de`; both isolated runs completed with exit code zero. Full PNGs and run receipts are retained. No performance claim.

The coordinator should apply the completed rows' proposed bounds from `handoff.json` (now all 13). They preserve each original binding length and use current runtime fitting, `length / max(glTF X extent, glTF Z extent)`, with axes `[x, -z, y]`. No LODs were added for these small props. Android was not cooked or tested; this remains WIP content outside release promotion. The workspace lease is released.
