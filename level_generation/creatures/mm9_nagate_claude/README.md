# MM9 Nagate family (mm9_nagate) — 3D model, 2026-10-30

The MM9 Nagate is a giant six-legged **beetle** (`mm9/extracted/MODELS/MODELS/NAGATE.abc`: 53 joints, 14 pieces, 13
clips), not a snake. Nagate Hatchling (9081, skin NAGATE1), Nagate (9082, NAGATE2), Nagate Elder (9083, NAGATE3).
Built on the MM9 rig-reuse route of `../mm9_dfly_claude/` and `../mm9_lobber_claude/` (new HD Meshy mesh weighted to
the original MM9 skeleton, the MM9 clips played with only the listed fixes). Progress, hashes and receipts:
`creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_nagate.glb` (cooked copy in `assets_dev`), skins `nagate_a/b/c` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, descriptors `MM9 Nagate A/B/C`, scale 100 / 150 / 300 (MONSTERS.txt `Scale` 1 / 1.5 / 3, read as a model size multiplier as for the Lobber pods) |
| Triangles LOD0/1/2/3 | 5,415 / 2,707 / 973 / 319 |
| Skeleton | the MM9 one, names unchanged, + `Socket_Mouth` (between the mandibles, on `Xhead`) |
| Clips (30 fps) | Standing 2.0 (stand), Walking 0.6 (walk), Running 0.4 (run at half rate: MM9 has 10 keys in 0.2 s), Fidget 2.5 (fidget1), AttackMelee 0.5 (Hattack1), AttackRanged 0.5 (Rattack1, also the cast), Hit 0.6 (wince1), Death 1.8 (die1: flips onto its back), Dead 1.0 |
| Events | melee impact 0.333 s (MM9 `Rattack; Lattack`), ranged/cast 0.25 s (MM9 `RangeAttack`, the Elder's Redline), released from `Socket_Mouth` |
| Gait | stride 0.30 m (walk and run, toe fore-aft travel, `scripts/gait_nagate.py`), `gait_rate [0.6, 2.5]` |
| Meshy credits | **25 / 35** (Smart Topology 5, retexture 10, texture pass retexture 10; backup account) |

## Route

0. **HD masters** (`references_hd/`, Codex via `claude_shared/codex_slot.sh`, two runs): renders of the MM9 model with
   its tier-1 skin (`mm9_views_tier1.png`, `mm9_top_tier1.png`, skin x4), brief `CODEX_BRIEF.md`, records
   `generation_runs.json`, `selected_views_review.png`. Gate: 00 accepted (six legs, the middle left hidden by the body
   at three-quarter; a faint low-alpha halo only), 01-04 accepted (same beetle, sides face the right way).
1. **Meshy** Smart Topology 15k from `00_three_quarter.png`: shell and underbody (with the head) as two pieces, four
   legs per side, each an upper piece plus a separate claw piece, two stubs, eyes, mandibles, antennae.
2. **Fit** (`scripts/fit_nagate.py`, on `work/mm9_nagate_ground.blend` from `mm9_rig_source.py`, lift 0.2023): neck =
   narrowest underbody slice behind the widest head slice; per-axis affine maps body -> MM9 body.mesh (front at
   `Xneck`) and head -> MM9 head.mesh, blended over the neck (Meshy's beetle was longer and narrower: body scale
   1.26 / 1.03 / 1.23). Claw pieces join their upper piece by virtual edges; the stubs and one leg pair are dropped by
   exact assignment of the remaining legs to the six MM9 chains (hip and tip distances); every leg is mapped onto its
   chain from `X*basepiv` to the toe tip with the upper/claw junction landmarked on the MM9 knee (`X*mid`) and its
   cross-section widened x1.5 (MM9 legs are 1.5-2x longer). Antennae and mandibles fitted onto their chains.
3. **Weights** (`scripts/rig_body.py nagate`), **reduce** (`reduce_body.py 0.4 0.4 0.55`), **UV** (`uv_export.py
   nagate`), **retexture** from 01/03/02/04 on our UVs (`requests/retexture_v1.json`).
4. **Clips** (`scripts/clips_mm9.py` `NAGATE`, run by `build_export.py nagate`): MM9 keys as PCHIP curves at 30 fps;
   the MM9 loops are seamless (0 pop); Running at half rate.
5. **Textures** (`scripts/compose_nagate.py`): 2K graded base, 1K normal, 1K ORM. The tiers differ in pattern
   (Nagate's orange bands), so regions come partly from MM9: each body texel is carried in 3D to the nearest MM9
   surface point and its skin UV. R wing cases (the skin's elytra panels), A bands (where the tier-2 skin is orange),
   B gold claws and mandibles (hue), G chitin; eyes keep the base colour. Tier A identity, B/C chroma by luminance
   percentile from their skins. `review/nagate_texture_classes_tiers.png`.
6. **Runtime** (`scripts/build_runtime.sh nagate [--install]`): prepare -> LODs -> shadow shrink (separate parts under
   8 cm left in place: the eyes inverted at 3 cm) -> `region_variants.py` -> floor pass (ground loops for
   stand/walk/run/fidget, raise attacks/hit, corpse on the floor) -> winding check (0 inverted).

## Rebuild

```sh
T=<lease token>; B="tools/run_creature_blender.sh --token $T"; P=level_generation/creatures/mm9_nagate_claude
V=level_generation/props/mm9_isleofashes_claude/work/venv/bin/python
for t in 1 2 3; do $V tools/mm9_import_discovery/convert_abc_model.py mm9/extracted/MODELS/MODELS/NAGATE.abc \
  $P/source/tier$t --id nagate$t --texture 0=mm9/extracted/SKINS/SKINS/NAGATE$t.dtx --scale 0.0256; done
$B $P/scripts/mm9_rig_source.py $P/source/tier1/nagate1.glb $P/work/mm9_nagate_ground.blend 0 0.2023
$B $P/scripts/fit_nagate.py $P/work/mm9_nagate_ground.blend $P/meshy/nagate_smart_v1/model_urls_glb.glb $P/work/fit_v1.blend $P/work/fit_v1.json
$B $P/scripts/rig_body.py $P/work/fit_v1.blend nagate $P/work/rig_v1.blend $P/work/rig_v1.json
$B $P/scripts/reduce_body.py $P/work/rig_v1.blend $P/work/reduced_v1.blend $P/work/reduced_v1.json 0.4 0.4 0.55
$B $P/scripts/uv_export.py $P/work/reduced_v1.blend nagate $P/work/uv_v1.blend $P/texturing/nagate_body_upload.glb
# work/uv_v2.blend (kept) is the texture pass layout of nagate_retexture_v2: xatlas packs differently per run, never re-run
# $B $P/scripts/uv_atlas_v2.py $P/work/uv_v1.blend $P/work/uv_v2.blend $P/texturing/nagate_body_upload_v2.glb $P/work/uv_v2.json
$B $P/scripts/dump_uv3d.py $P/work/uv_v1.blend $P/work/uv3d_nagate.npz Body   # approved layout, for the tone pins
$B $P/scripts/dump_uv3d.py $P/work/uv_v2.blend $P/work/uv3d_nagate_v2.npz Body
$B $P/scripts/dump_uv3d.py $P/work/mm9_nagate_ground.blend $P/work/uv3d_mm9_nagate.npz body.mesh:1 head.mesh:2 \
  eye.mesh:3 eye01.mesh:3 legfront.mesh:4 legfront01.mesh:4 legmiddle.mesh:4 legmiddle01.mesh:4 legback.mesh:4 \
  legback01.mesh:4 pincer.mesh:5 pincer01.mesh:5 antennae.mesh:6 antennae01.mesh:6
$B $P/scripts/bake_ao.py $P/work/uv_v2.blend Body $PWD/$P/textures/nagate_ao_2k.png 0.03 2048
# compose, gentle grade, grain and eye pin, compose, ramp match, export, runtime, viewer (see "Texture quality pass")
$P/scripts/texpass_finish.sh $T --install
```

The tone pins read the approved set in `work/before_texpass/textures/`.

## Texture quality pass (2026-10-30)

`../claude_shared/TEXTURE_QUALITY_PASS.md`. Mesh shape, rig, weights, clips, sockets and binding unchanged; only UVs, the
paint and the maps. **10 Meshy credits** (backup account).

| Measure (`texture_quality.py`, LOD0) | Before | After |
|---|---|---|
| Atlas use (2K) | 39.1 % | **66.5 %** |
| Equivalent fully used square | 1,281 px | 1,671 px |
| Texels per creature size p10 / p50 / p90 | 890 / 989 / 1,051 | **1,213 / 1,249 / 1,308** (+26 % linear) |
| Density spread p90/p10 | 1.18 | 1.08 |
| Islands / surface on fragments | 801 / 9.0 % | 220 / 1.7 % |
| UV stretch p90 (rest pose) | 1.41 | 1.11 |
| Meshy source | 2K on 39 % | 4K on 66.5 % (3,341 px equivalent) |

- **UVs** `scripts/uv_atlas_v2.py` (`claude_shared/uv_atlas.py`, head x1.8 as before) -> `work/uv_v2.blend`; **retexture
  v2** (`requests/retexture_v2.json`): same four HD masters, `meshy-7`, 4K, our UVs; returned GLB reports the same layout.
- **Maps** colour 4K -> 2K Lanczos once, normal and roughness 4K -> 1K, AO re-baked on the new UVs, gentle grade.
- **Drift and pins.** The fresh paint kept the means but came back grainier: a pale stipple on head, legs and wing cases
  (surface luminance sd chitin 41.6 -> 58.0, p95 134 -> 179; wing cases 37 -> 45). Two steps, no Meshy job:
  `scripts/nagate_grain.py` scales the log-luminance detail finer than 6 texels to 1.25x the approved amplitude at the
  same surface scale (wing cases and bands x0.84, chitin x0.71) and gives the eyes, which have no ramp, the approved mean
  colour; `claude_shared/ramp_match.py` fits the wing, chitin and band ramps of every tier by quantile matching to the
  approved texels at the same surface points (`claude_shared/texpass_tone.py`, `work/tone_v2.json`).
  Mean sRGB and luminance sd, approved -> now: tier A wing cases 53/29/20 sd 37.1 -> 53/29/21 sd 37.0, chitin 74/53/38 sd
  41.5 -> 75/53/38 sd 40.7; tier B bands 104/63/3 sd 61.5 -> 103/62/6 sd 60.7; tier C chitin 85/60/39 sd 46.5 -> 85/60/39
  sd 45.3. Tier A ramp errors: wings 7.7, chitin 3.5, gold 6.0, bands 9.9 levels before the match.
- **Tier B bands kept**: the region still comes from the MM9 tier-2 skin by the 3D transfer, on the same wing-case areas;
  the edges are the same patches, now on the sharper scale pattern (`review/texpass/`, tier B wing and head).
- **Gold** (claws, mandibles): hue-picked as before, now only on limbs, because the 4K paint speckles the belly with gold.
  It reads a little brighter than the approved gold (tier A 103/75/42 -> 133/99/35), left as painted.
- **Shadow LOD** `scripts/shrink_shadow_lods.py`: the new UV seams changed the decimation and one 8-triangle part of shadow
  LOD 2 turned inside out under the shrink; a part whose signed volume would flip now stays in place.
```

## Checks (2026-10-30)

- After the texture pass (same day): `run_creature_review.py check` 0 errors, 27 switches; `check_winding.py` 0 inverted; flat
  shading 0.00; floor audit Nagate A/B/C ok; detached-parts audit unchanged (1 of 20 parts, 9 mm in one AttackMelee pose, as
  approved); regression `mm9_actor_models_build_every_binding` PASS (65 descriptors, 0 failed); clips unchanged. Sheet (review
  viewer, identical cameras, three tiers): `review/texpass_before_after_sheet.png`; shots `review/texpass/before`,
  `review/texpass/after2`, cameras `review/texpass_shots.txt`; before state `work/before_texpass/`. No in-game run.
- Viewer `review/viewer/` (3 tiers x 9 clips): `tools/run_creature_review.py check` 0 errors, 27 switches; shots
  `review/shots/`, `review/viewer_shots_sheet.png`.
- Gates (`scripts/gates.py`, `review/gates.json`): loop seams 0; edge ratio p1/p99 per clip 0.66-0.97 / 1.02-1.55
  (extremes at the antenna and claw tips in the death flip).
- Deformation against MM9: `work/pose_ov_sheet.png` (walk, run, Hattack1, die1 over the MM9 mesh).
- Floor audit `floor_audit.py --world mm9`: Nagate A/B/C ok (49/49 in the world on 2026-10-30).
- Regression `--world mm9 --headless-run-regression-suite actors`: `mm9_actor_models_build_every_binding` PASS (the
  two failing MM8 cases of that suite do not apply under `--world mm9`).
- In game (remade Anskram Keep, `output/mm9_rework/assets_dev` review mirror, `tools/run_game.sh --isolated`,
  minimized, tour `review/anskram_tour.yml`): `review/ingame_sheet.png` — the map's own Nagate Hatchlings as 3D
  actors coming at the party, spawned Nagate and Nagate Elder (scale 3), the Elder's death on its back.

## Deviations and open points

- Meshy made four legs per side and two stubs; the stubs and the pair nearest no MM9 leg (hips at y -0.09) are dropped.
- Legs are Meshy's thin jointed legs stretched 1.5-2x along the MM9 chains and widened x1.5; MM9's are flat blades.
- Tier B's bands come from the MM9 tier-2 skin via the 3D transfer; they read as yellow-orange patches on the violet
  wing cases rather than MM9's crisp stripes. Eyes keep tier A's red in every tier.
- Unused MM9 clips (aware, taunt, fidget2, Hattack2 `bite`, wince2) are not exported. The MM9 `lunge` events are not
  reproduced (clips are in place).
- User artistic acceptance: accepted 2026-10-30 ("nagate - good").
