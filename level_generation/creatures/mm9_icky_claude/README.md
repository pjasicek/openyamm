# MM9 Icky family (mm9_icky) — 3D model, 2026-10-30

The MM9 Flying Icky (a small green bat-winged worm with a round lamprey mouth, two horn ears, spine spikes, two thin
hind legs and a whip tail with a spade tip; `mm9/extracted/MODELS/MODELS/FLYINGICKY.abc`, 62 joints, 445 tris, 19
clips) for the MM9 world: Airborne Icky (9087, `MM9 Icky A`, L7), Flying Icky (9088, `MM9 Icky B`, L11), Astral Icky
(9089, `MM9 Icky C`, L18, casts Poison Spray). Built on the route of `../mm9_dfly_claude/` and `../mm9_lobber_claude/`
(MM9 rig reuse: a new HD Meshy mesh weighted to the original MM9 skeleton, the MM9 clips played with only the listed
fixes). Progress, hashes and receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_icky.glb` (installed; cooked copy in `assets_dev`), one skin |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`: Icky A scale 50, B 100, C 200 (MONSTERS.txt `Scale` 0.5 / 1 / 2) |
| Triangles LOD0/1/2/3 | 5,445 / 2,721 / 970 / 313 (LOD0: body 4,320 incl. 9 teeth 162; wings 1,104 + wrist claws 24) |
| Skeleton | the MM9 one, 62 joints, names unchanged (`Xcenter`, `XbackA/C`, neck, `Xheadpiv`, `Xhead`, six mouth petals `Xjawpiv*`/`Xjaw*`, ears, wing arms, legs with toes, tail chain) + `Socket_Mouth` on `Xhead` |
| Clips (30 fps) | Standing 0.5 (StandAir), Walking 0.5 (Flap), Running 0.33 (Flap x1.5), Fidget 1.2 (fidgetair1), AttackMelee 0.8 (Hattackair1), AttackRanged 0.9 (startattackair2), Cast 1.2 (taunt), Hit 0.7 (winceair1), Death 2.1 (DieAir1 + fall1 + FallDown1), Dead 1.0 |
| Events | melee bite 0.293 s (MM9 `bite`, Hattackair1), second bite 0.675 s (MM9 `bite`, startattackair2), cast 0.6 s released from `Socket_Mouth` (the taunt's widest gape; MM9 has no cast event) |
| Floor | flier rule: hover +0.7187 baked in the living clips, eased out over Death; corpse grounded (+0.5493); `floor_audit.py --world mm9` 17/17 ok |
| Meshy credits | **25 / 35** (Smart Topology 5, retexture 10, 4K retexture v2 10 for the texture pass; backup account; no retries) |

## Decisions

- **One skin, tiers by size.** All three MONSTERS.txt rows use `flyingicky.abc` with the single skin
  `flyingicky.dtx`; they differ only in level, stats and `Scale` (0.5 / 1 / 2). So there are no region ramps: every
  descriptor uses the same material, and the bindings carry the MM9 scales (50 / 100 / 200, as the Lobber's Scale-2
  rows did). The descriptors' `TintColor` values (B `0x00b4ffff`, C `0x00ff78b4`) belonged to the archived MM6 sprite
  stand-ins and are not used by 3D models.
- **Roles.** The Icky is melee only (no missile); its attack 2 plays MM9's `startattackair2` (the lunge that opens
  the latch-on bite, ending with the mouth open). The Astral Icky's spell plays the `taunt` (two wing beats and a
  screech, head dipping), released at its widest gape (0.6 s). The ceiling-roost clips (`hang`, `hangfidget`,
  `launch`, `ickysetup`) and `attackair2`, `winceair2`, `dieair2`/`fall2`/`FallDown2` are not exported (one clip per
  role; our actors do not roost on ceilings).
- **The bite flares the mouth as in MM9.** The six petal bones splay the lamprey ring into a wide red hexagonal funnel
  (about 40 degrees); the Meshy snout front follows them (`work/head_r2.png` against `work/head_mm9.png`). The large
  edge stretch in the attack clips (gates below) is that flare.
- **Symmetry.** The primary master shows one leg, so Meshy built one full leg and a stub. The fit keeps the creature's
  right half (the full leg) and mirrors it (the MM9 body is symmetric), which also centres the off-axis Meshy body.

## Route

0. **HD masters** (`references_hd/`, Codex, two runs): renders of the MM9 model with its skin (`mm9_views_tier1.png`,
   five views; `mm9_head_tier1.png`, head close-ups; `mm9_top_tier1.png`; the skin x4 for material). Brief
   `CODEX_BRIEF.md`; records `generation_runs.json`, `selected_views_review.png`. Bind pose: wings spread flat,
   head hanging forward-down. Canvas 1536x1024. Extra `05_wings_top.png` (top view) builds and textures the wings.
   The faint exterior alpha halo was clipped (alpha < 40 -> 0); the raw returns are kept as `*_raw.png`. Gate: all
   six accepted (identity, mouth ring and teeth, horns, red eyes, spikes, wrist claws, tail barbs and spade, correct
   left/right); 00 shows only one leg (see Symmetry).
1. **Meshy** Smart Topology 15k from `00_three_quarter.png` (`requests/icky_smart_v1.json`): one shell with wings,
   legs, tail and horns, plus eight teeth (`work/meshy_v1_sheet.png`).
2. **Fit** (`scripts/fit_icky.py`, overlays `work/*_sheet.png`): similarity from four landmarks (mouth = teeth
   centroid, tail tip, both wing tips); Meshy's wing membranes cut beyond the flank (|x| > 0.047 inside the wing-root
   span, beyond 0.1 elsewhere; the legs hang below and are kept) and the flank holes filled; rigid ICP of the torso
   onto the MM9 torso, rigid ICP of the head (+ teeth) onto the MM9 head blended into the neck; the tail mapped by
   arc length onto the MM9 tail chain (parallel-transported frames, root blended); the leg is left in place (after
   the torso ICP its foot lies on the MM9 foot; a chain fit dragged the belly in because the MM9 thigh runs inside the
   body); bisect at x = 0, mirror the right half, teeth mirrored likewise.
3. **Wings** (`scripts/prep_wings.py`, `scripts/build_wings.py`): the top view's membrane outline (body column and
   legs excluded, wrist claws split off by their cream/orange colour), outline every 14 px plus a staggered interior
   grid, Delaunay inside the mask, chords split so top and bottom never collapse; mapped onto the MM9 wing by a 2D
   similarity (image root -> middle of the MM9 wing's inner edge, tip -> tip); z, normal and weights from the MM9 wing
   mid-surface under each vertex (the MM9 wing is a two-layer slab: both layers averaged), barycentric weights; closed
   leaves 5 mm thick at the centre tapering to the outline; UVs are the image points. Claws: six-sided cones on the
   leading edge, rigid with the wing weights at their base (`work/wing_mesh2d.png`).
4. **Weights** (`scripts/rig_body.py`): nearest MM9 vertex label (MM9 body, spikes and teeth only for the core; the
   tail and each leg only from their own chain; MM9 wing and foot meshes excluded from the core), diffusion with the
   mouth petals and ears held, teeth rigid with their nearest body vertex, 4 influences.
5. **Reduce** (`scripts/reduce_body.py 0.25 0.5 0.3`: body, teeth, head), **UV** (`scripts/uv_export.py`: Smart UV,
   head islands x2), **retexture** from 01/03/02/04 on our UVs (`requests/icky_retexture_v1.json`).
6. **Clips** (`scripts/clips_mm9.py`, run by `scripts/build_export.py`): MM9 key poses resampled as PCHIP curves at
   30 fps; loop seams 0 before and after; Death stitched (joins 0 degrees); Running = Flap x1.5 (whole frames);
   Dead = Death's last pose (MM9's belly-up corpse).
7. **Textures** (`scripts/compose.py`): body 2K base (gutters padded) graded by `grade_basecolor.py` (AO from
   `bake_ao.py`), 1K normal, 1K ORM (R AO, G roughness: mouth ring 0.4, horns/teeth/spikes 0.5, scales 0.55-0.8,
   B 0); wing material: the HD top-view crop (2048x512), roughness 0.6.
8. **Runtime** (`scripts/build_runtime.sh`): prepare -> LODs -> shadow shrink (wing leaves and parts < 3 cm not
   pushed) -> `material_extras.py` (specular 0, metallic 0; no tier ramps) -> floor pass -> winding check
   (0 inverted).

## Rebuild

```sh
T=<lease token>; B="tools/run_creature_blender.sh --token $T"; P=level_generation/creatures/mm9_icky_claude
V=level_generation/props/mm9_isleofashes_claude/work/venv/bin/python   # any python with pygltflib
$V tools/mm9_import_discovery/convert_abc_model.py mm9/extracted/MODELS/MODELS/FLYINGICKY.abc $P/source/icky \
  --id icky --texture 0=mm9/extracted/SKINS/SKINS/FLYINGICKY.dtx --scale 0.0256
$B $P/scripts/mm9_rig_source.py $P/source/icky/icky.glb $P/work/mm9_icky_src.blend 0 0
$B $P/scripts/fit_icky.py $P/work/mm9_icky_src.blend $P/meshy/icky_smart_v1/model_urls_glb.glb $P/work/fit_v2.blend $P/work/fit_v2.json full
python3 $P/scripts/prep_wings.py
$B $P/scripts/build_wings.py $P/work/fit_v2.blend $P/work/wings_v2.blend $P/work/wings_v2.json
$B $P/scripts/rig_body.py $P/work/wings_v2.blend $P/work/rig_v2.blend $P/work/rig_v2.json
$B $P/scripts/reduce_body.py $P/work/rig_v2.blend $P/work/reduced_v2.blend $P/work/reduced_v2.json 0.25 0.5 0.3
$B $P/scripts/uv_export.py $P/work/reduced_v2.blend icky $P/work/uv_v2.blend $P/texturing/icky_body_upload.glb
$B $P/scripts/dump_uv3d.py $P/work/uv_v2.blend $PWD/$P/work/uv3d_icky.npz Body   # the approved UVs, for the tone match
# texture pass (2026-10-30): xatlas UVs on the same mesh, 4K retexture v2 on them, gentle grade, tone match
$B $P/scripts/uv_atlas_texpass.py $P/work/uv_v2.blend $P/work/uv_v3.blend $P/texturing/icky_body_upload_v2.glb $P/work/uv_v3.json
#   xatlas packs differently per run: never re-run this, retexture_v2 is on that upload
python3 tools/creature_meshy.py --project $P --token $T submit --job icky_retexture_v2 --kind retexture \
  --request requests/icky_retexture_v2.json --credits 10      # then poll / download
$B $P/scripts/dump_uv3d.py $P/work/uv_v3.blend $PWD/$P/work/uv3d_icky_v3.npz Body
$B $P/scripts/bake_ao.py $P/work/uv_v3.blend Body $PWD/$P/textures/icky_ao_2k.png 0.03 2048
python3 $P/scripts/compose.py && python3 $P/../claude_shared/grade_basecolor.py --ao $P/textures/icky_ao_2k.png \
  --fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.15 $P/textures/icky_basecolor.png
python3 $P/scripts/tone_match.py $P/work/uv3d_icky.npz $P/work/uv3d_icky_v3.npz $P/work/before_texpass/icky_basecolor_graded.png \
  $P/textures/icky_basecolor_graded.png $P/textures/icky_basecolor_final.png --json $P/work/tone_match.json --push orange=1.25,0.74,0.65
$B $P/scripts/build_export.py $P/work/uv_v3.blend $P/work/anim_v3.blend $P/export/mm9_icky_lod0.glb $P/work/clips_v3.json
python3 tools/creature_workspace.py run --project $P --token $T -- $P/scripts/build_runtime.sh --install
python3 $P/scripts/make_viewer_manifest.py r2_icky_texpass_20261030 "icky=Flying Icky (Airborne / Flying / Astral; one skin)=$P/export/mm9_icky.glb"
```

## Checks (2026-10-30)

- Viewer `review/viewer/` (1 model x 10 clips): `tools/run_creature_review.py ... check` 0 console errors, 10 clips
  switched; shots `review/viewer_shots_sheet.png`; playback `review/playback/` (every clip at 1x and 0.5x).
  (Since the texture pass the viewer's focus presets are tuned to this body; earlier close views were Blender renders,
  `work/final_sheet.png`.)
- Gates (`scripts/gates.py`, `review/gates.json`): loop seams 0; edge ratio p1/p99 Standing/Walking/Running
  0.37 / 1.6, Fidget/Cast 0.36 / 1.9, Death 0.51 / 3.9, Hit 0.33 / 4.8, attacks 0.33-0.39 / 8.3-8.6 (the MM9 mouth
  flare: the petal ring splays into the funnel).
- Floor audit `floor_audit.py --world mm9`: 17/17 ok. Regression `mm9_actor_models_build_every_binding`
  (`OPENYAMM_REGRESSION_FILTER`, `--world mm9`): 17 descriptors on 8 models, 0 failed. Winding: 0 inverted closed
  parts.
- In game (remade Anskram Keep from `output/mm9_rework/assets_dev`, `tools/run_game.sh --isolated`, minimized,
  immortal, tour `review/anskram_tour.yml`, `exit: true`): `review/ingame_sheet.png`, frames in `review/ingame/` -
  the map's Airborne Ickies and spawned Flying / Astral Ickies as textured 3D actors at their three sizes, static
  models playing Standing, AttackMelee, Cast, Hit and Death to the corpse, a fight and deaths with corpses on the
  floor. The mirror's `worlds/mm9/models/` was relinked to the current `assets_dev` files (review_root refresh
  semantics, that folder only) so the new GLB and bindings are in it.

## Texture quality pass (2026-10-30)

`../claude_shared/TEXTURE_QUALITY_PASS.md` and `../claude_shared/MM9_TEXTURE_PASS_BRIEF.md`. The body only: the wing leaves
(`Icky_Wing`, our own texture, UV sum 88.4 %) are untouched. Mesh, rig, weights, clips, socket and hover are unchanged
(`work/clips_v3.json` = `clips_v2.json`, LOD triangles 5,445 / 2,721 / 970 / 313); only the body's UVs and maps changed.
**10 Meshy credits** (retexture v2, backup account); creature total **25 / 35**. One skin, so no ramps.

| `texture_quality.py` (LOD0, `Icky`) | Before | After |
|---|---|---|
| Atlas use (2K) | 43.4 % | **57.8 %** |
| Equivalent fully used square | 1,349 px | **1,557 px** |
| Density p10 / p50 / p90 | 2,168 / 2,433 / 4,659 | 2,474 / 2,555 / 5,098 |
| Spread p90/p10 (head x2 on purpose) | 2.15 | 2.06 |
| Islands / surface on fragments | 551 / 13.0 % | 140 / **1.8 %** |
| Stretch p90 | 1.41 | 1.21 |
| Zero-area UV triangles | - | 0 |
| Meshy source | 2K on Smart UV | 4K on the new UVs (3,114 px equivalent) |

Median density rose only 5 %; atlas use and the 4K paint carry the improvement:
fine detail 7.2 -> 15.8 levels RMS (under 1.5 px), the
4-16 px blotch band 24.0 -> 15.5.

- **UVs** `scripts/uv_atlas_texpass.py` on `work/uv_v2.blend` -> `work/uv_v3.blend`, head groups and x2 as in
  `uv_export.py`. Do not re-run it: the paint is bound to this layout.
- **Grade** gentle (`--fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.15`). AO re-baked on the new UVs.
- **Drift and its fix.** The fresh paint came back lighter and higher in contrast (green linear p95 0.29 -> 0.51, sd 37
  -> 52, the whole surface sd 52 -> 63). `scripts/tone_match.py` maps each channel, per hue class of the NEW paint, onto the
  approved paint's distribution at the same surface points (curves only, nothing spatial from the old paint). Whole
  surface approved -> final: mean 53.7/100.9/51.8 -> 53.2/99.5/51.1, sd 52.4 -> 49.2, linear p95 0.533 -> 0.495
  (`scripts/tone_compare.py`, `work/tone_v3.json`). A first version washed the dorsal spike tips pale because the yellow
  belly dominated their class; orange is now a class of its own with a chroma push (`--push orange=1.25,0.74,0.65`).
  Output `textures/icky_basecolor_final.png`, read by `build_export.py`.
- **Reads differently from the approved paint (from the masters, kept):** the small red eyes are now visible on the head
  sides (the HD masters and the MM9 skin have them; the old paint had blurred them into dark smudges), the mouth ring
  is a cleaner red with separate teeth, and the scales read as a crisp cell pattern instead of blotches.

**Checks.** Winding 0 inverted; `run_creature_review.py check` no failures (10 clips, revision
`r2_icky_texpass_20261030`); flat-shading 0.00 on the body, wings 0.98 as before; floor audit Icky A/B/C ok;
`detached_parts_audit.py` 0 detached, output identical to the before GLB; regression
`mm9_actor_models_build_every_binding` (`--world mm9`) 61 descriptors on 28 models, 0 failed; gates loop seams 0
(`review/gates_texpass.json`). No in-game run. Viewer presets in `review/viewer/review.js` are retuned to this body.
Accepted from review-viewer shots at identical cameras (`review/texpass/`): `review/texpass_closeups_sheet.png` (with 1:1
crops) and `review/texpass_body_sheet.png`; density heatmap `work/heat_after_density.png`. Before state: `work/before_texpass/`.

## Deviations and open points

- Wings are our own closed leaves from the HD top view (Meshy's wings dropped), as on the dragonfly; the wrist claws
  are small cones. Their thickness is 5 mm at the centre.
- The left half is the mirrored right half (Meshy's left leg was a stub).
- No tier colours: MM9 uses one skin for all three rows; the rows differ by size only.
- AttackRanged (`startattackair2`) ends with the mouth open, as MM9's latch-on lunge does; the engine blends out of
  it. The Icky has no missile, so it is rarely if ever played.
- MM9 `Velocity` lunges are not reproduced (clips are in place); the corpse is MM9's belly-up FallDown1 pose.
- User artistic acceptance: accepted 2026-10-30 ("flying icky - good").
