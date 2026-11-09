# MM9 Dagrell family (mm9_dagrell) — 3D model, 2026-10-30

The MM9 Dagrell (`mm9/extracted/MODELS/MODELS/DAGRELL.abc`: 67 joints, 45 rigid pieces, 18 clips) is a gaunt, spiked
**bone beast that stands and walks on four limbs** (three-clawed hands, three-toed feet, ribcage, dorsal spikes, a
long tail with a blade); its bind pose is a tight crouch and its `HAttack1` rears on the hind legs. It is not a
humanoid: the MM9 rig-reuse route of `../mm9_dfly_claude/` and `../mm9_lobber_claude/` applies. Dagrell (9147, skin
DAGRELL1), Venomous Dagrell (9148, DAGRELL2), Spectre Dagrell (9149, DAGRELL3). Progress, hashes and receipts:
`creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_dagrell.glb` (cooked copy in `assets_dev`), skins `dagrell_a/b/c` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, descriptors `MM9 Dagrell A/B/C`, scale 100 (MONSTERS.txt `Scale` 1) |
| Triangles LOD0/1/2/3 | 7,518 / 3,727 / 1,294 / 334 (about 140 separate bone, rib, spike, claw and tooth pieces) |
| Skeleton | the MM9 one (names, rest orientations and clips unchanged; joint pivots moved onto Meshy's joints, see "Joint fix"), + `Socket_Mouth` (lower jaw centre, on `Xheadpiv`) |
| Clips (30 fps) | Standing 1.8 (Stand), Walking 1.0 (Walk), Running 0.5 (Run), Fidget 1.8 (Fidget1), AttackMelee 1.0 (HAttack1), AttackRanged 1.2 (RAttack1, also the cast), Hit 1.3 (Wince1), Death 3.63 (Wince2 + returntocrouch + roll onto its right side), Dead 1.0 |
| Events | melee impact 0.5 s (MM9 `lattack`), ranged/cast 0.666 s (MM9 `RangeAttack`), released from `Socket_Mouth` |
| Gait | stride 0.6 m walk (ankle/wrist fore-aft travel 0.59), run 1.1 m (sweep 0.80 plus the gallop's flight), `gait_rate [0.6, 2.5]` (`scripts/gait_dagrell.py`; 0.85 / 1.6 before the joint fix) |
| Meshy credits | **45 / 45** (Smart Topology 5, retexture 10, retexture retry 10 after the skull cut changed the topology, texture pass 20; backup account) |

## Route

0. **HD masters** (`references_hd/`, Codex via `claude_shared/codex_slot.sh`, two runs) from renders of the MM9 model
   in its **Stand pose** (`scripts/ref_renders.py` with `POSE=Stand@0`): the crouched bind pose folds every limb against
   the body. Brief `CODEX_BRIEF.md`; records `generation_runs.json`, `selected_views_review.png`. Gate: 00-04 accepted
   (ribcage, dorsal spikes, three claws per hand and three toes per foot, bladed tail, red eyes, sides correct).
1. **Meshy** Smart Topology 15k from `00_three_quarter.png`: ~130 separate rigid pieces in roughly the Stand pose.
2. **Align** (`scripts/align_stand.py`): similarity ICP onto the MM9 mesh posed at Stand frame 0.
3. **Fit, weights, unpose** (`scripts/fit_dagrell.py`): bones do not bend, so the Meshy geometry is not warped; the
   MM9 skeleton is posed onto it instead (per-bone rigid ICP of each bone's subtree skin about its head, parents first,
   a step kept only when it lowers the distance). A thin thread Meshy grew from the jaw to the left hand is cut. The
   skull is cut along its head/jaw label boundary so Meshy's fused lower jaw becomes a separate mandible on `Xjawpiv`
   (the MM9 bite opens it about the hinge instead of stretching the mouth corners). Pieces under 250 vertices are
   rigid to their majority bone; claws and toes ride their digit's pivot (`X*piv`: MM9's fingers are long, Meshy's
   claws start at the wrist); the few long bones spanning a joint (shin+foot, spine) split by nearest bone segment
   along one chain, limb bones only. Every vertex is unposed to the MM9 bind by its blended fitted-pose matrices
   (action `FitPose` kept for the upload and the gate).
4. **Reduce** (`reduce_body.py 0.45 0.6 0.55`; teeth and small spikes as piece 2), **UV** (`uv_export.py dagrell`:
   the upload is exported in the FitPose, matching the HD views), **retexture v2** from 01/03/02/04.
5. **Left arm** (`scripts/reweight_uv.py`, `scripts/mirror_left_arm.py`): Meshy's left front limb reached forward and
   its MM9 fit stayed poor, so the right arm pieces (well fitted) are mirrored onto the left bones (UVs carried) and
   the old left arm removed; weights from the last fit are carried onto the UV'd mesh piece by piece (no new UVs).
6. **Clips** (`clips_mm9.py` `DAGRELL`, `build_export.py dagrell`): MM9 keys as PCHIP curves at 30 fps; loop seams
   closed (Stand popped 3.1 deg at `XtailF`, Walk 1.2, Run 0.2); MM9 has **no Dagrell death clip**: Death = Wince2
   spasm + returntocrouch (it lies down) + a roll onto its right side (gravity ease-in, bounce, settle).
7. **Textures** (`scripts/compose_dagrell.py`): albedo x0.7 (the retexture came back lighter than the MM9 charcoal and
   the HD masters), 2K graded base, 1K normal, 1K ORM. Regions by 3D transfer to the MM9 skin: R bone, G spikes (red-
   orange in the tier-2 skin: Venomous and Spectre spikes and the tail blade). Tier A identity, B green, C blue steel.
8. **Runtime** (`scripts/build_runtime.sh dagrell [--install]`): prepare -> LODs -> shadow shrink -> region variants
   -> floor pass (ground loops stand/walk/fidget, raise run/attacks/hit, corpse grounded) -> winding (0 inverted).

## Rebuild

```sh
T=<lease token>; B="tools/run_creature_blender.sh --token $T"; P=level_generation/creatures/mm9_dagrell_claude
V=level_generation/props/mm9_isleofashes_claude/work/venv/bin/python
for t in 1 2 3; do $V tools/mm9_import_discovery/convert_abc_model.py mm9/extracted/MODELS/MODELS/DAGRELL.abc \
  $P/source/tier$t --id dagrell$t --texture 0=mm9/extracted/SKINS/SKINS/DAGRELL$t.dtx --scale 0.0256; done
$B $P/scripts/mm9_rig_source.py $P/source/tier1/dagrell1.glb $P/work/mm9_dagrell_ground.blend 0 0.7584
$B $P/scripts/align_stand.py $P/work/mm9_dagrell_ground.blend $P/meshy/dagrell_smart_v1/model_urls_glb.glb $P/work/align_v1.blend $PWD/$P/work/align_v1 $P/work/align_v1.json
$B $P/scripts/fit_dagrell.py $P/work/align_v1.blend $P/work/rig_v4.blend $P/work/rig_v4.json
# work/uv_v2.blend (kept) is the retexture v2 topology: it was reduced/unwrapped from an earlier fit (rig_v1) whose
# head weights steered the decimation, so it is reused as is, not rebuilt. uv_v2 -> uv_v5 only for the mesh and rig:
# the maps come from retexture v4 on uv_v8 (see "Texture quality pass"), kept: xatlas packs differently per run
$B $P/scripts/reweight_uv.py $P/work/uv_v2.blend $P/work/rig_v4.blend $P/work/uv_v4.blend $P/work/reweight_v4.json
$B $P/scripts/mirror_left_arm.py $P/work/uv_v4.blend $P/work/uv_v5.blend $P/work/mirror_v5.json
$B $P/scripts/repivot_dagrell.py $P/work/uv_v5.blend $P/work/uv_v6.blend $P/work/repivot_v6.json
# layout of retexture v4 (kept, never re-run): options in "Texture quality pass"
# $B $P/scripts/uv_texpass.py $P/work/uv_v6.blend $P/work/uv_v8.blend $P/texturing/dagrell_body_upload_v4.glb $P/work/uv_v8.json \
#   cut_closed=1 max_edge_stretch=5.0 max_density_ratio=5.0 max_stretch=1.8 retry_stretch=3.0
$B $P/scripts/texpass_uv3d.py $P/work/uv_v5.blend $P/work/uv_v6.blend $P/work/uv_v8.blend $PWD/$P/work/uv3d_dagrell_v8.npz
$B $P/scripts/texpass_bake_ao.py $PWD/$P/texturing/dagrell_body_upload_v4.glb $PWD/$P/textures/dagrell_ao_2k.png 0.02 2048
# compose, gentle grade, grain, compose, ramp match, export, runtime (shadow_opaque.py included), viewer
$P/scripts/texpass_finish.sh $T --install   # the tone pins read work/before_texpass/textures and work/uv3d_dagrell_v6uv.npz (old UVs, kept)
```

`work/uv3d_mm9_dagrell.npz` is `dump_uv3d.py` of `work/mm9_dagrell_ground.blend` with every MM9 piece as part 1.

## Joint fix (2026-10-30)

User: "limbs not connected to the rest, also the 'tail', and rest when animating (e.g. attack)": in the viewer the
head, legs, feet and tail blade flew up to 60 cm apart in the attack.

**MM9 itself** keeps the body together: its pieces are skinned across the joints (BACK01 runs from the pelvis to the
tail tip, ARM, LOWRLEG and FINGR pieces span two to five bones) and its clips are rotations (translation keys only on
XCENTER, XtailA and, sub-millimetre, the fingers). Joined pieces open by at most 2.0 cm in any clip
(`review/joints/gaps_mm9.json`; the jaw: 2.5 cm).

**Cause.** `fit_dagrell.py` only rotated the MM9 skeleton onto Meshy's pieces; the bones kept MM9's lengths, so their
pivots sat 3-32 cm from where Meshy's pieces meet (`work/repivot_v6.json`, "moved"; Meshy's neck is short, its limbs
and tail proportioned differently). A rigid piece turns about its own bone's pivot, so each MM9 joint rotation (40-130
degrees away from the fitted pose) swung a piece end away from its neighbour by about offset x angle. Some pieces also
rode the wrong bone: the right humerus on XbackB (so the shoulder never bent; the left arm had no humerus at all), the
pelvis on XtailA, a throat piece and the jaw hinge 11 cm behind the mandible, two claws on one digit.

**Fix** (`scripts/repivot_dagrell.py`, after `mirror_left_arm.py`, on Meshy's own FitPose geometry):
- structural pieces get their bone: spine split at XbackA / XbackB / Xneckbase (its front is the chest, Xneckbase,
  carrying neck and shoulders as in MM9), neck XneckB, skull/mandible as fitted, tail vertebrae and blade, humerus
  Xarmpiv, forearm Xarm with its hand end Xarmlow, the two separate claws one digit pivot each, femur Xlegpiv, the
  shin+metatarsal+toes piece split Xleg / Xleglow / Xfoot at knee, hock and ankle;
- every other piece (ribs, spikes, pelvis, girdle, spurs, toe claws) takes the skin weights of the host point it grows
  from (the torso when within 3 cm of it);
- each bone's head moves to the interface with its parent's geometry (closest vertex pairs; split pivots on the piece
  axis; the jaw hinge at the mouth corners); rest orientations stay, so the MM9 rotation keys play unchanged;
- the first tail vertebra blends from XCENTER (spine end) to XtailA (far end), as MM9's BACK01 skin does: MM9
  translates XtailA by up to 3.5 cm, which opened a rigid vertebra 2-4 cm in Hit;
- vertices are unposed again (FitPose reproduced to 5e-7 m) and both left limbs are replaced by mirrors of the right
  ones (bones and pieces, about the spine's mid-plane).

**Numbers** (`scripts/joint_gaps.py`: pieces joined in Meshy's FitPose or Standing frame 0, worst opening per clip at
48 fps; mouth pairs apart; `review/joints/gaps_before.json`, `gaps_after.json`):

| Clip | before | after | MM9 (own clip) |
|---|---|---|---|
| Standing | 9.9 cm | 0.7 cm | 0.0 cm |
| Walking | 34 cm | 2.0 cm | 1.0 cm |
| Running | 42 cm | 2.1 cm | 1.8 cm |
| Fidget | 31 cm | 0.9 cm | 1.2 cm |
| AttackMelee | 62 cm | 1.5 cm | 1.7 cm |
| AttackRanged | 63 cm | 1.4 cm | 0.8 cm |
| Hit | 38 cm | 1.5 cm | 2.0 cm |
| Death / Dead | 43 / 37 cm | 4.8 cm (knee cap between femur and shin) | 1.2 / 1.9 cm (Wince2 / returntocrouch) |

Pairs open over 5 cm: 4-18 per clip before, 0 after. `claude_shared/detached_parts_audit.py` (48 fps, all clips,
`review/joints/detached_audit_after.txt`): 0 of 136 parts detached in any pose (before: dozens, up to 33 cm in the
attack alone, the jaw 5.8 cm off in Death, a tail bone in Hit). The mandible stays within 5 mm of the skull at the hinge; the
mouth opens to 16-18 cm at the teeth in the attack and death (MM9 opens its jaw 16-40 degrees). Stride lengths follow
the shorter Meshy legs (above). Sheets (MM9 | before | after, 3/4 and side): `review/joints/dagrell_joints_poses_1.png`
(rest, the attack frame of the user's shot, Standing, Walking, Running, Fidget), `..._poses_2.png` (attacks, Hit,
Death, Dead), `review/joints/dagrell_joints_tiers.png` (three tiers next to MM9's), viewer
`review/joints/dagrell_viewer_tiers_sheet.png`.

**Spectre Dagrell see-through** (user, 2026-10-30). Tiers are `KHR_materials_variants` materials and the engine
resolves the material per draw, so tier C alone is alpha-blended without engine work: `build_runtime.sh` passes
`material.alphaMode="BLEND"`, `baseColorFactor [0.8, 0.92, 1.0, 0.55]` and a faint blue `emissiveFactor` for
`Dagrell_C` (`claude_shared/region_variants.py` `--extra ... material.<key>`). Single-sided; a blended creature
primitive keeps its authored triangle order and writes no depth, so overlapping bone pieces of one Dagrell blend in
triangle order (they share one colour, so the order hardly shows). The engine requires dedicated shadow LODs to be
opaque in every tier ("dedicated shadow LODs require opaque geometry"), so `scripts/shadow_opaque.py` maps the
shadow meshes' Spectre variant onto the opaque tier A material: the Spectre still casts its shadow from the opaque
shadow LODs, and `--headless-validate-actor-models --world mm9` accepts all three bindings.

## Texture quality pass (2026-10-30) - current maps

`../claude_shared/TEXTURE_QUALITY_PASS.md`. Mesh, rig, weights, clips (`clips_v8.json` identical to `clips_v6.json`), sockets
and binding unchanged; only UVs, the paint and the maps. **20 Meshy credits** (backup account): retexture v3 on a first
layout, rejected for stretch, then v4. The joint fix and the see-through Spectre stay: `Dagrell_C` is `BLEND` with its
factors, `scripts/shadow_opaque.py` moves its 4 shadow mappings to opaque, and `--headless-validate-actor-models` accepts it.

| Measure (`texture_quality.py`, LOD0, bind pose) | Before | After |
|---|---|---|
| Atlas use (2K, union) | 12.2 % | **53.0 %** |
| UV sum (mirrored left limbs count twice) | 14.6 % | 62.9 % |
| Equivalent fully used square | 716 px | 1,490 px |
| Texels per creature size p10 / p50 / p90 | 943 / 1,057 / 1,843 | **2,047 / 2,181 / 3,889** (+106 % linear; p90 is the head) |
| Density spread p90/p10 | 1.95 | 1.90 |
| Islands / surface on fragments | 1,448 / 42.5 % | 509 / **8.3 %** (target 3 %, missed) |
| UV stretch p90 | 1.47 | 1.33 (1.27 on the FitPose, over 5x: 0 %) |
| Meshy source | 2K on 12 % | 4K on 53 % (2,981 px equivalent) |

- **Closed bone pieces** are what makes this body hard: xatlas cut them into 754 charts, and 71 of the 175 merged charts
  failed in Blender because a whole closed piece has no boundary. `claude_shared/uv_atlas.py` gained `cut_closed` (a closed or
  holed merged chart is cut into a disc along a shortest path on its underside; what still fails is retried as patches of
  at least 8 triangles) and `max_stretch` / `retry_stretch` (limits on a chart's p90 stretch).
- **Fragments against stretch.** On these pieces the two targets pull apart (`work/uvtry/`, FitPose stretch, unique faces):

  | Trial | Atlas | Fragments | Stretch p90 | Surface over 5x |
  |---|---|---|---|---|
  | D, no stretch limit (retexture v3) | 52.9 % | 0.4 % | 2.97 | 6.6 % (tail blade p90 6.8) |
  | G, limits 2.4 / 4.0 | 51.3 % | 8.6 % | 1.33 | 0 % |
  | **F, limits 1.8 / 3.0 (retexture v4, installed)** | 52.9 % | 9.5 % | 1.27 | 0 % |
  | E, limit 1.8 | 52.5 % | 11.8 % | 1.25 | 0 % |

  D looked good in the viewer but made stretch worse than the approved 1.47, so F was painted. The fragment target is missed
  knowingly: with triangles this large the "fragments" are not specks (under 8 triangles, median about 16 x 16 texels at 2K).
- **Atlas** 53 %, just under the 55 % floor; packing spiky pieces stopped there on every trial.
- **Left limbs** are mirrors of the right ones (`repivot_dagrell.py`) and keep sharing their texels: `scripts/uv_texpass.py`
  lays out the other 6,140 faces on the FitPose shape and copies UVs corner by corner through the old identical UVs. In the
  upload the left limbs collapse to one UV point, so they occlude in Meshy's projection but take no texels.
- **Upload pose** FitPose as before (`texturing/dagrell_body_upload_v4.glb`). AO bakes on that upload too
  (`scripts/texpass_bake_ao.py`), not on the crouched rest pose where folded limbs would darken the body. Spike regions keep
  the approved 3D transfer: `scripts/texpass_uv3d.py` gives the new UVs the uv_v5 positions the MM9 mesh is aligned to.
- **Drift and pins.** Meshy returned stark black and white veining, far from the approved charcoal. `scripts/dagrell_grain.py`
  scales the log-luminance detail finer than 12 texels to 1.25x the approved amplitude at one surface scale (bone x0.61, spikes
  x0.47); `claude_shared/ramp_match.py` then fits both regions' ramps in every tier by quantile matching
  (`work/tone_v8.json`). Mean sRGB and luminance sd, approved -> now: tier A bone 68/66/62 sd 36.2 -> 68/67/62 sd 35.1, B bone
  71/83/42 sd 41.5 -> 71/84/43 sd 40.1, B spikes 98/53/9 -> 97/54/15, C bone 71/71/82 sd 38.8 -> 71/72/83 sd 37.5.
  `compose_dagrell.py` clears the eye class: the approved paint had no eye texels, and the new paint's red ones stayed red in
  every tier, so they now follow the bone ramps. `ALBEDO_SCALE` 0.7 stays.
- **Pattern.** The blotches became the veining and ribbing of the HD masters, so close up the bone reads more detailed than the
  approved smudge; tone and contrast match. Blacks are slightly lifted (tier A p5 5 -> 19 of 255).
- **Neck and tail joints** (coordinator request; `detached_parts_mm9.md` parts 40 `XneckB`, 20 mm, and 71 `XtailB`, 12 mm): not
  real, no change to `repivot_dagrell.py`. Surface samples of the pieces (`scripts/texpass_necktail_surface.py`, every clip at 16
  fps, `work/necktail_surface.txt`) stay 0.7-2.4 mm apart, and viewer shots of AttackRanged 0.63 s and Dead 0 s from four
  sides show no background through either joint (`review/joints_texpass/sheet_before2.png`): the audit's bind contact point
  slides while the piece stays in touch. Parts 66 and 84 follow from the neck flag.

Sheets (review viewer, identical cameras, three tiers): `review/texpass_before_after_sheet.png`; shots `review/texpass/before`,
`review/texpass/after3`, cameras `review/texpass_shots.txt` (`claude_shared/texpass_viewer_shots.py`). Before state:
`work/before_texpass/`.

## Checks (2026-10-30)

- After the texture pass (same day): `run_creature_review.py check` 0 errors, 27 switches; `check_winding.py` 0 inverted; flat
  shading 0.00; floor audit Dagrell A/B/C ok; `--headless-validate-actor-models --world mm9` 66 descriptors, 0 refused (the
  blended Spectre with its opaque shadow LODs included); regression `mm9_actor_models_build_every_binding` PASS (65
  descriptors, 0 failed); `detached_parts_audit.py` identical to the approved model (5 flags, parts 40 and 71 not real, see
  "Texture quality pass"). No in-game run.
- After the joint fix (same day): `run_creature_review.py check` 0 errors, 27 switches; floor audit A/B/C ok;
  `check_winding.py` 0 inverted; flat shading 0.00; detached-parts audit 0 detached; `--headless-validate-actor-models
  --world mm9` 0 refused; regression `mm9_actor_models_build_every_binding` PASS (49 descriptors, 0 failed).
- In game after the fix: `review/ingame_spectre_sheet.png`, `review/ingame_spectre_crop.png` (tour
  `review/spectre_tour.yml`, Isle of Ashes, `tools/run_game.sh --isolated`, minimized; run on a private hard-linked
  copy of the review mirror with only the new GLB swapped in, because the scenario save step failed on the current
  main `assets_dev`): the Spectre reads as a pale blue see-through skeleton beside the opaque A and B, assembled
  while attacking and dying.

- Viewer `review/viewer/` (3 tiers x 9 clips): `tools/run_creature_review.py check` 0 errors, 27 switches; shots
  `review/shots/`, `review/viewer_shots_sheet.png`.
- Gates: `review/gates_fitpose.json` (`scripts/gates_fitpose.py`: edge ratio against the FitPose, i.e. Meshy's own
  shape; the crouched bind pulls joint-spanning pieces apart, so `gates.py` against the bind does not apply):
  p1/p99 per clip 0.85-1.0 / 1.02-1.14, max 1.8-4.5 at Meshy's ankle bends; loop seams 0 (`review/gates.json`).
- Deformation against MM9: `work/pose_final_sheet.png`, `work/pose_v5_sheet.png`, `work/headclose_sheet.png`.
- Floor audit `floor_audit.py --world mm9`: Dagrell A/B/C ok (49/49 in the world).
- Regression `--world mm9 --headless-run-regression-suite actors`: `mm9_actor_models_build_every_binding` PASS.
- In game: `review/ingame_isle_sheet.png` (remade Isle of Ashes, review mirror, `tools/run_game.sh --isolated`,
  minimized, tour `review/isle_tour.yml`: the three tiers spawned in front of the party, attacking, the Spectre's death
  and corpse). Anskram Keep (`review/anskram_tour.yml`) put the camera against a pillar (`review/ingame_sheet.png`).

## Deviations and open points

- No MM9 death clip: Death is Wince2 + returntocrouch + a procedural roll onto the side.
- MM9 draws Dagrells translucent (MONSTERS.txt `Transparent 1`, spectral); only the Spectre (tier C) is see-through
  (user, 2026-10-30), the Dagrell and the Venomous Dagrell are opaque.
- Both left limbs are mirrors of the right ones (Meshy's left limb reached forward); joints open by at most 2 cm
  (5 cm at the knee caps and the tail root) when MM9 bends them; the mandible edge along the skull cut is ragged; Meshy's skull is rounder than MM9's.
- Tier B is lighter green than MM9's (chroma and brightness from the skin's luminance bands); the spike region is small
  (MM9's red-orange texels map onto the tail blade and a few spikes).
- Unused MM9 clips (crouch, CrouchedAware, crouchfidget, returntocrouch except in Death, Walk1, Search, Taunt, Jump,
  HAttack2, Wince2 except in Death, static_model) are not exported; `lunge` events are not reproduced.
- User artistic acceptance: accepted "dagrell - ok" (2026-10-30, after the joint fix).
