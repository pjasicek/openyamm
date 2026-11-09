# Texture quality pass (Meshy-textured creatures)

**Default for every new 3D model since 2026-10-30, not only a repair pass**: lay new models' UVs, request the paint
and grade by steps 2-5 below from the start, and meet the targets before install. The playbooks point here through
[Sharp textures](../CLAUDE_CREATURE_TEXTURES.md#sharp-textures-layout-paint-resolution-and-grading-default-since-2026-10-30).

Recipe for creatures whose texture reads blotchy or soft up close while the model and animations are fine. Pilot:
MM9 Magreeb, 2026-10-30 (`../mm9_magreeb_claude/README.md`, "Texture quality pass"): atlas 33.7 % -> 54.0 %, median
density +25 %, fine detail 2.4x, fragments 10.3 % -> 2.1 % of the surface, 10 Meshy credits. Mesh shape, rig, clips and
binding stay; only UVs, the paint and the texture maps change.

## 1. Measure

```sh
python3 level_generation/creatures/claude_shared/texture_quality.py <runtime.glb> --by-bone \
  --heatmap <out>/heat --json <out>/quality.json
```

Per base-colour texture (LOD0): **atlas** use (texel-centre union), **equivalent** px (side of a fully used square with
the same detail), texel **density** p10/p50/p90 in texels per creature size and **spread** p90/p10, **islands** and the
share of the surface on **fragments** (islands under 8 triangles), **stretch** p90 (singular-value ratio of the UV map),
per-bone density with `--by-bone`, and UV-space heatmaps (`--reference <median>` puts before and after on one scale).
Render the heatmap on the model by replacing the base-colour image (`../mm9_magreeb_claude/scripts/texpass_views.py
<glb> <prefix> <image-substring>=<heat_density.png>`).

Also look at the Meshy return itself (`meshy/<job>/texture_urls_0_base_color.png`): its size, and whether small
islands are painted as flat specks. Compare the raw and graded base colour on one crop: a 4-16 px band (difference of
Gaussians at 4 and 16 px, inside the islands) much stronger after grading means the grade adds the blotches.

## 2. Targets

| Measure | Target | Magreeb before -> after |
|---|---|---|
| Atlas use | 70 % ideal; 55-60 % is what automatic charts reach on spiky reduced Meshy bodies | 33.7 -> 54.0 % |
| Density spread p90/p10 | <= 1.3 (head islands are meant to be denser) | 1.23 -> 1.12 |
| Fragment surface | <= 3 % | 10.3 -> 2.1 % |
| Stretch p90 | <= 1.5 | 1.52 -> 1.17 |
| Zero-area UV triangles | 0 | 0 -> 12 (fixed in the tool since) |
| Meshy source | 4K on the new UVs, downsampled once | 2K -> 4K |

The creature cook caps colour at 2048 (`tools/cook/model_textures.yml`, user decision), so atlas use and the quality
of the paint are the levers, not a bigger runtime texture.

## 3. Steps

Work under the project lease (`tools/creature_workspace.py claim`), Blender through `tools/run_creature_blender.sh`.

1. **Fix geometry first** if anything else needs it (detached parts: `detached_parts_audit.py`, then a
   `root_limbs.py` like the Magreeb's or the Eye's). New UVs and the retexture come after the last vertex move.
2. **UVs**: `claude_shared/uv_atlas.py` from a project script (template `../mm9_magreeb_claude/scripts/uv_atlas_v8.py`:
   bind pose, head groups and factor, report JSON, neutral static upload GLB). One-time setup:
   `python3 -m venv claude_shared/xatlas_venv && claude_shared/xatlas_venv/bin/pip install xatlas==0.0.11 numpy`.
   Defaults: xatlas charts (max cost 2, roundness 0.5), charts under 12 triangles merged into the neighbour with the
   longest shared border and flattened again by Blender SLIM (reverted to xatlas pieces when they overlap, flip,
   stretch an edge over 3x or collapse a triangle), one density for all charts with the head `head_factor` denser,
   xatlas brute-force packing into a 2048 square with a 2 px margin (about 8 min for 6k triangles).
3. **Retexture** on the new upload with the same HD masters (`requests/retexture_v2.json`: `enable_original_uv`,
   `enable_pbr`, `texture_resolution: "4k"`, `ai_model: meshy-7`; 10 credits like 2K). Check the returned GLB with
   `texture_quality.py`: it must report the same layout as the upload.
4. **Rebuild the maps** from Meshy's maps on our UVs only: colour downsampled 4K -> 2K (Lanczos), normal to 1K,
   roughness, `dump_uv3d.py` and the AO bake on the new UV blend. Never re-bake an earlier bake.
5. **Grade gently**: `grade_basecolor.py --ao <ao> --fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06
   --saturation 1.15` (defaults: fine 0.5, local 0.6, AO 0.7 made the claw blotches). Compare raw / default / gentle on
   one crop before choosing.
6. **Regions and ramps**: re-check the tier-A ramp errors in `<x>_ramps.json`. A richer paint has more hue inside a
   region; split a region whose tier-A error exceeds about 10 levels by hue (Magreeb: olive vs bright green tips) and
   take identity pieces (eyes, teeth) out of the mask rather than giving them a ramp.
7. **Export, LODs, runtime build, winding check, install** as the project's README rebuild; viewer tiers and manifest;
   `tools/run_creature_review.py --project <p> check`; flat-shading check; the project's gates; floor audit; the
   world's `*_actor_models_build_every_binding` regression; `detached_parts_audit.py`.
8. **Sheets** at identical cameras: before/after of the close-up and full body for every tier, density heatmaps on one
   scale, review-viewer presets. Back up the before GLBs and viewer GLBs first (`work/before_texpass/`).

## 4. Pitfalls

- **xatlas packs differently per run.** Never re-run the UV script once its upload went to Meshy; the retexture is
  only valid on that exact layout.
- **xatlas merges islands that overlap in its input** (`add_uv_mesh`): `xatlas_charts.py pack` spreads them on shelves
  first. It also normalises width and height separately; the pack step searches the scale so the result fits one
  square and stays isotropic. Brute-force success is not monotonic in the scale, so it tries every 2 % step.
- **The fast packer is not monotonic either.** `uv_atlas.unwrap(..., fine=250, steps=0)` sweeps it in 0.1 % steps: on the Dragon
  King 55.9 % in 5 minutes, where ten brute-force steps found nothing in 27 (51.8 %). Try it before waiting on brute force.
- **A set with a strip painted by other means** (Dragon King mouth): `height_share=0.8` packs into v 0..0.8 of the square
  without rotation, instead of scaling a whole square into a corner and leaving a column empty.
- **Blender's packer** (concave, any rotation) reached only 44-51 % on these charts, worse than xatlas brute force.
- **SLIM can collapse a strip of a merged chart to a line** (zero UV area). The density check now reverts such charts.
- **Edit-mode round trips reallocate UV layers**: read and write through `me.uv_layers['UVMap']` each time, never a
  stored layer object. Hide unchosen faces in bmesh before `uv.unwrap`; polygon `select` flags alone are not obeyed.
- **Bodies of separate closed pieces** (the Dagrell's 136 bones): merged charts cover whole closed pieces, which Blender
  cannot unwrap. Pass `cut_closed=1`. Check stretch on the shape Meshy paints: opened pieces flatten with long needles (tail
  blade 6.8), so add `max_stretch=1.8 retry_stretch=3.0`. Fragments and stretch then pull apart; prefer stretch, since
  low-poly pieces' "fragments" are not specks (Dagrell README, trial table).
- **A fresh paint can drift a lot**: `claude_shared/texpass_tone.py` compares approved and new at the same surface points per
  tier and region, `claude_shared/ramp_match.py` pins each region's ramps by quantile matching; scale the fine detail first
  (`../mm9_nagate_claude/scripts/nagate_grain.py`). Nagate chitin sd 58 -> 41 (approved 41.6).
- **Bone-segment charts** (one chart per dominant bone, cut into discs on the underside) were tried: spiky segments
  collapse under SLIM and fall back to xatlas pieces; no gain on the Magreeb (50 %).
- **Numpy 2** rejects `np.cross` of 2D vectors; compute UV areas explicitly.
- A scratch file named `inspect.py` next to a Python script shadows the standard library module.
- The tier-A ramp flattens hue variation inside a region by design; the richer the paint, the more regions it needs.

## 5. Other MM9 creatures, ranked by expected gain

`texture_quality.py` on the installed GLBs (`assets_source/worlds/mm9/models/`), 2026-10-30. Atlas = texel-centre
union at 2048 (mirrored or overlapping halves count once; "sum" counts them twice). Gain = linear density at the
Magreeb's 54 % (sqrt(0.54 / atlas)), before the gain from a 4K paint and fewer fragments; the fragment share predicts
how blotchy the current paint is. Do not start these while their projects are being reworked by other agents.

| Rank | Model / material | Atlas (sum) | Equivalent px | Density p50 | Spread | Islands | Fragments | Gain |
|---|---|---|---|---|---|---|---|---|
| 1 | Dagrell `Dagrell_A` | 12.2 % (14.6) | 716 | 1,058 | 1.95 | 1,448 | 42.6 % | x2.10 |
| 2 | Dragonfly wing `DflyWing_A` (1K) | 13.1 % (26.2) | 371 | 891 | 1.43 | 4 | 0 % | x2.03 (repack only) |
| 3 | Greater Demon `GreaterDemon` | 16.7 % | 836 | 544 | 1.20 | 1,408 | 24.8 % | x1.80 |
| 4 | Winged Mutant `Wmut_A` | 24.9 % (37.5) | 1,022 | 1,165 | 1.18 | 1,067 | 12.4 % | x1.47 |
| 5 | Annud body `Annud` | 25.2 % | 1,029 | 891 | 1.19 | 293 | 4.9 % | x1.46 |
| 6 | Forad body `Forad` | 26.4 % | 1,052 | 1,066 | 1.17 | 404 | 4.6 % | x1.43 |
| 7 | Sea Monster `Sea_A` | 29.2 % | 1,107 | 1,614 | 2.07 | 820 | 7.2 % | x1.36 |
| 8 | Yrsa body `Yrsa` | 29.5 % | 1,112 | 748 | 1.16 | 335 | 10.4 % | x1.35 |
| 9 | Forad head `ForadHead` | 30.6 % | 1,132 | 3,352 | 1.95 | 405 | 7.8 % | x1.33 |
| 10 | Yrsa head `YrsaHead` | 33.7 % | 1,188 | 1,901 | 1.22 | 488 | 4.9 % | x1.27 |
| 11 | Basilisk `Basilisk_A` | 35.1 % (35.8) | 1,213 | 1,182 | 2.08 | 895 | 7.6 % | x1.24 |
| 12 | Lobber `Lobber_A` | 38.6 % (39.6) | 1,273 | 959 | 2.26 | 588 | 9.3 % | x1.18 |
| 13 | Annud head `AnnudHead` | 39.1 % | 1,280 | 3,068 | 1.87 | 310 | 6.1 % | x1.18 |
| 14 | Nagate `Nagate_A` | 39.1 % | 1,281 | 989 | 1.18 | 801 | 9.0 % | x1.18 |
| 15 | Terror `Terror_A` | 42.5 % (42.7) | 1,335 | 928 | 1.57 | 534 | 7.1 % | x1.13 |
| 16 | Dragon King `DragonKing` | 42.6 % | 1,336 | 1,132 | 1.06 | 597 | 3.4 % | x1.13 |
| 17 | Icky body `Icky` | 43.4 % | 1,349 | 2,433 | 2.15 | 551 | 13.0 % | x1.12 |
| 18 | Icky wing `Icky_Wing` | 44.1 % (88.4) | 1,360 | 1,907 | 1.01 | 4 | 0 % | x1.11 |
| 19 | Eye `Eye_A` | 44.3 % | 1,364 | 1,557 | 2.05 | 448 | 5.5 % | x1.10 |
| 20 | Jelly `Jelly_A` | 44.9 % | 1,373 | 2,011 | 1.66 | 357 | 4.0 % | x1.10 |
| 21 | Lobber Pod `Pod_A` | 48.3 % | 1,423 | 1,113 | 1.82 | 559 | 9.6 % | x1.06 |
| 22 | Crow `Crow_A` | 52.1 % (52.7) | 1,478 | 1,996 | 1.15 | 479 | 5.3 % | x1.02 |
| 23 | Dragonfly body `Dfly_A` | 54.7 % | 1,515 | 1,545 | 2.63 | 325 | 3.0 % | x0.99 |
| 24 | Wolf `Wolf_A` | 56.9 % | 1,544 | 1,570 | 1.23 | 469 | 4.6 % | x0.97 |

Done since: Annud and Forad, 2026-10-30 (body and head set; body atlas 25.2 -> 59.4 % and 26.4 -> 53.5 %, median
density +57 % and +46 %, 20 credits each; their READMEs, "Texture quality pass"). Their route for a body + head
set and for keeping an approved skin tone (`match_skin.py`) is in `../mm9_annud_claude/v2/scripts/`.

Done since: Nagate and Dagrell, 2026-10-30 (Nagate atlas 39.1 -> 66.5 %, fragments 9.0 -> 1.7 %, 10 credits; Dagrell atlas
12.2 -> 53.0 %, median density x2.06, fragments 42.5 -> 8.3 %, 20 credits; their READMEs, "Texture quality pass").

Dragon King, 2026-10-30 (body and head set; body atlas 35.9 -> 55.9 %, head 30.6 -> 50.9 %, median density +25 % and +31 %,
20 credits; its README, "Texture quality pass").

MM6–MM8: ranking of every installed monster, queue, trial results (Bone Dragon, Water Elemental, Troll, 2026-10-31) and
the MM6–MM8 specifics (installed GLB as the source, far-LOD texture refill, MM7 copies) are in
[texpass_mm678/HANDOFF.md](texpass_mm678/HANDOFF.md).

Below rank 15 the layout gain is small; those are worth the pass only for a 4K paint, a fragment share above about
8 % (Icky, Lobber Pod) or a spread above 2 (Dragonfly body, Icky, Eye, Basilisk, Lobber, Sea Monster), where the
cheaper fix is to even the density without a new paint. Separate head sets (Annud, Forad, Yrsa) are intentionally
denser; measure them against their own body.
- **Hue-picked regions spread on a fresh paint** (Terror, Eye, 2026-10-30): reddish spots in the new paint picked up the flesh ramp as copper
  patches and red flecks. When the mesh is unchanged, limit region masks to where the approved class map had them.
- **A fresh paint can change the creature, not just its sharpness** (Basilisk, Eye, 2026-10-30): tone curves fix the averages but not the
  pattern. Keep the approved look with `../mm9_basilisk_claude/scripts/match_tone.py`: each UV island takes the approved broad colour from the same
  surface points, and only the 4K paint's brightness detail stays on top. Build region masks from the final colours. Compare the hide's
  character in viewer shots: fine detail numbers can rise while a pebbled hide goes smooth.
- **Pattern that exists only in the old paint** (Eye, 2026-10-30): check band energy first. If the new paint's pattern does not correlate with the approved one at
  that scale, tone matching cannot bring it back. `../mm9_eye_claude/scripts/restore_pebbles.py` carries the approved colour down to pattern scale and moves the approved
  normal map too, with XY rotated per chart. Meshy's normal Y points down the image: rotating in Blender's v-up frame flips the relief on some charts, so check the
  normal-to-colour correlation after the transfer.
