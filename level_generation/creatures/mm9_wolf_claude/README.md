# MM9 wolf family (mm9_wolf) — 3D model, 2026-10-30

The MM9 wolf (`mm9/extracted/MODELS/MODELS/WOLF.abc`, 31 joints, 558 tris, 17 clips) for the MM9 world: Grey Wolf
(9114, skin WOLF), Red Wolf (9115, WOLFRED), Black Wolf (9116, WOLFBLACK). Built on the MM9 rig-reuse route of
`../mm9_dfly_claude/` and `../mm9_lobber_claude/`: a new HD Meshy mesh weighted to the original MM9 skeleton, the
MM9 clips played with only the listed fixes. Progress, hashes and receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_wolf.glb` (cooked copy in `assets_dev`), skins `wolf_a/b/c` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_wolf_claude`: MM9 Wolf A/B/C, scale 40/50/50 (100 x MONSTERS.txt `Scale` 0.4/0.5/0.5) |
| Triangles LOD0/1/2/3 | 5,185 / 2,587 / 910 / 287 (LOD0 body 4,588, teeth/claws/eyes 597) |
| Skeleton | the MM9 one, names unchanged: `Bone33` hips, `Bone35`/`Bone32` spine/chest, `Bone26` neck, `Bone27` skull, `Bone28` muzzle, `Bone30` jaw, `Bone37/39` ears, legs `Bone11-12-13-19` (front left), `Bone16-17-18-05`, `Bone01-02-03-09` (hind left), `Bone06-07-08-42`, tail `Bone34-21-22-23-24` |
| Clips (30 fps) | Standing 2.0 (stand), Walking 0.9 (walk), Running 0.4 (run, cross-faded loop), Fidget 3.0 (fidget1), AttackMelee 1.0 (Hattack1), AttackRanged 1.0 (Hattack2), Hit 0.87 (wince1), Death 1.47 (die1), Dead 1.0 |
| Events | bite 0.414 s (MM9 `bite` of Hattack1 and the first bite of Hattack2); wolves cast nothing, `cast: AttackMelee` |
| Gait | stride 1.96 (walk), 4.18 (run) model units per cycle, from the paws' planted backward speed (`scripts/gait_measure.py`) |
| Floor | ground rule; the tail chain bends above the floor first (`--lift-joints`, tail joints only); `floor_audit.py --world mm9` ok |
| Meshy credits | **25 / 35** (backup account): Smart Topology 5, retexture 10, second retexture 10 (on the cleaned mesh) |

## Decisions

- **Clean body before fitting.** The Smart Topology return had a hidden inner shell (24 % of its faces, a third of
  its area) and overlapping fur layers on the chest and neck. After reduction they showed as shards and dark AO
  stains (`work/raw_close_sheet.png`, `review/` shots of revision 2). The main body is voxel-remeshed
  (`scripts/clean_meshy.py`, 3.5 mm in Meshy units, light smooth, `CLEAN_MODE=none`: uniform voxel quads, no
  decimation, since a decimated voxel surface has slivers that flip under the fit) and fitted, weighted and only then
  reduced. Teeth, claws and eyes are kept as returned. A second retexture was made on the clean mesh.
- **Limb fit = a transient skinning pose** (`scripts/fit_quad.py`): global ICP, head ICP, then every leg and the tail
  is estimated on the Meshy limb (centreline joints at the MM9 arc fractions) and posed into the MM9 bind with soft
  capsule weights, so no seam opens at a region border. Segment stretch is capped to 0.85-1.2 and rotations over
  50 degrees are dropped (the tail tip estimate turned 131 degrees).
- **Teeth** follow the upper muzzle or the jaw by the least-squares plane between the MM9 `Bone28` and `Bone30`
  vertices (`scripts/rig_body.py`).
- **Run loop.** MM9's `run` is no clean loop (54 degrees on `Bone08` last-to-first; LithTech blends between loops),
  so it is cross-faded over 0.1 s into a 0.4 s cycle (`clips_mm9.py` `xfade`). Walk/stand seams are closed as before.
- **Tiers.** Regions R fur, G mouth (head texels with a red hue), B eyes (eye pieces), A teeth/claws (identity). Tier A
  keeps the HD look; B/C take hue from their MM9 skin by luminance percentile, MM9 chroma not boosted (our grey wolf
  says nothing about red saturation), brightness by the MM9 tier/A ratio, partly restoring MM9's absolute level.
  MM9 has no amber eye texels the classifier finds: the eyes keep tier A colour in every tier.

## Rebuild

```sh
T=<lease token>; B="tools/run_creature_blender.sh --token $T"; P=level_generation/creatures/mm9_wolf_claude
V=level_generation/props/mm9_isleofashes_claude/work/venv/bin/python   # any python with pygltflib
M=mm9/extracted/MODELS/MODELS; S=mm9/extracted/SKINS/SKINS; C=tools/mm9_import_discovery/convert_abc_model.py
$V $C $M/WOLF.abc $P/source/wolf --id wolf --texture 0=$S/WOLF.dtx --scale 0.0256   # also wolfred, wolfblack
$B $P/scripts/mm9_rig_source.py $P/source/wolf/wolf.glb $P/work/mm9_wolf_rig.blend 0 0.1272
CLEAN_MODE=none $B $P/scripts/clean_meshy.py $P/meshy/wolf_smart_v1/model_urls_glb.glb $P/work/wolf_clean_v3.glb 0.0035 0
$B $P/scripts/fit_quad.py $P/work/mm9_wolf_rig.blend $P/work/wolf_clean_v3.glb $P/work/fit_v3.blend $P/work/fit_v3.json
RIG_DIFFUSE=120 RIG_HINGE=20 $B $P/scripts/rig_body.py $P/work/fit_v3.blend $P/work/rig_v3.blend $P/work/rig_v3.json
$B $P/scripts/reduce_body.py $P/work/rig_v3.blend $P/work/reduced_v3.blend $P/work/reduced_v3.json 0.025 0.25 0.05
$B $P/scripts/uv_export.py $P/work/reduced_v3.blend wolf $P/work/uv_v3.blend $P/texturing/wolf_body_upload_v2.glb
# (retexture_v2 was made on this upload)
$B $P/scripts/remove_inverted.py $P/work/uv_v3.blend $P/work/uv_v3b.blend   # voxel bubbles and stray chips
# keel/pocket rebuild + untangle (system python, scipy), then torso weights and teeth (2026-10-30, "Shoulder fold fix")
$B $P/scripts/dump_weights.py $P/work/uv_v3b.blend $P/work/uv_v3b_dump.npz
python3 $P/scripts/armpit_rebuild.py $P/work/uv_v3b_dump.npz $P/work/armpit_v3.npz $P/work/armpit_v3.json
$B $P/scripts/refine_weights.py $P/work/uv_v3b.blend $P/work/uv_v3c.blend $P/work/refine_v3c.json $P/work/armpit_v3.npz
export HEAD_GROUPS=Bone27,Bone28,Bone30,Bone37,Bone39 JAW_GROUPS=Bone30
$B $P/scripts/dump_uv3d.py $P/work/uv_v3c.blend $P/work/uv3d_wolf.npz Body
$B $P/scripts/dump_uv3d.py $P/source/wolf/wolf.glb $P/work/uv3d_mm9_wolf.npz wolf.mesh:1
$B $P/scripts/bake_ao.py $P/work/uv_v3c.blend Body $PWD/$P/textures/wolf_ao_2k.png 0.1 2048
python3 $P/scripts/compose_wolf.py && python3 $P/../claude_shared/grade_basecolor.py --ao $P/textures/wolf_ao_2k.png \
  $P/textures/wolf_basecolor.png && python3 $P/scripts/compose_wolf.py
$B $P/scripts/build_export.py $P/work/uv_v3c.blend $P/work/anim_v3.blend $P/export/mm9_wolf_lod0.glb $P/work/clips_v3.json
python3 tools/creature_workspace.py run --project $P --token $T -- $P/scripts/build_runtime.sh --install
flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock \
  python3 $P/scripts/bind_actors.py mm9_wolf_claude $P/work/actors_block.yml
(cd $P && python3 scripts/viewer_tiers.py && python3 scripts/make_viewer_manifest.py r5_wolf_20261030 \
  "wolf_a=Grey Wolf (Wolf A)=review/viewer/wolf_a.glb" "wolf_b=Red Wolf (Wolf B)=review/viewer/wolf_b.glb" \
  "wolf_c=Black Wolf (Wolf C)=review/viewer/wolf_c.glb")
```

## Checks (2026-10-30)

- Viewer `review/viewer/` (own title, three.js from `mm6_goblin/review_20261006/vendor/`):
  `tools/run_creature_review.py check` 3 tiers x 9 clips, 0 console errors; shots `review/viewer_shots_sheet.png`.
- Gates (`scripts/gates.py`, `review/gates.json`): loop seams 0 (Standing, Walking, Running); edge ratio p1/p99 per
  clip 0.52-0.75 / 1.54-3.00 since the shoulder fold fix (was 0.51-0.73 / 1.31-2.22: the wider blends spread the
  stretch over more edges instead of folding it into a flap); largest single edge 2.6-6.0 (was 2.9-12.5).
- Floor audit `floor_audit.py --world mm9`: Wolf A/B/C ok (49/49 bindings ok). Regression
  `mm9_actor_models_build_every_binding` (`--world mm9`): 49 descriptors on 20 models, 0 failed. Winding: 0 inverted.
- In game (Ravensford `bootcamp.odm`, `tools/run_game.sh` minimized, private `--user-data` folder whose settings.ini has
  `[startup] start_in_main_menu=false`, `start_map_file=bootcamp.odm`, `immortal=true` and the one-shot
  `menu_input_tour_path`; tour `review/wolf_tour.yml`, `exit: true`): `review/ingame_sheet.png` — spawned Grey, Red and
  Black Wolf as 3D actors walking in and biting the party, the Black Wolf's death to its corpse and loot satchel. The
  static-model part of the tour (`model spawn` at the Lobber's coordinates) fell outside the camera.

## Shoulder fold fix (2026-10-30)

User: "wolf - attack (e.g. frame 17) - texture stretching?" In AttackMelee ~17 (48 fps) the wolf rears; between the
raised right foreleg and the brisket the skin folded into a flap with a hard crease, a smaller crease on the other
side and a horizontal crease across the upper chest.

Cause (three parts, measured with a per-frame fold-over count: body faces whose posed normal points against the
smoothed normal of their neighbourhood, every clip at 48 fps):
1. Rest-mesh fold-overs: 90 faces were already folded in the bind mesh where the elbow meets the chest and at the
   tail base (the limb fit pushed the leg top into the chest, plus fused fur layers) - torn sawtooth slits even in
   Standing, and the pockets opened into flaps when the leg swung.
2. MM9's rigid skin gives the leg roots (Bone11/Bone16, Bone01/Bone06) the chest and hip sides; the left and right
   roots met directly under the brisket and in the groin (70 shared vertices at the brisket), the tail root met both
   hind roots on the rump.
3. Surface diffusion gave the two sides of each pocket different bones and left narrow leg/chest borders.
MM9's own wolf at the same frame has the same pose (47 degrees on Bone16 against 9 on Bone11) and folds there too,
with hard low-poly creases; the pose is not extreme, so the clip is unchanged.

Fix (`scripts/refine_weights.py` + `scripts/weight_refine.py`, between `remove_inverted.py` and `dump_uv3d.py`;
UVs, topology and clips unchanged, AO rebaked and textures recomposed because the pockets moved):
- untangle: Laplacian relax around the folded rest faces until none is left or ten passes bring no gain
  (90 -> 8 faces, 564 vertices moved, mean 0.015, max 0.096 model units);
- torso weights: Gaussian spatial smoothing (sigma 0.1, Euclidean, never across two limb chains) so both sides of
  a pocket move together and every leg/chest border is wide; lower legs below elbow/knee, tail past its base,
  muzzle, jaw, ears and rigid pieces keep their weights (fade over 4 rings);
- midline: leg weights fade to Bone32 (front) / Bone33 (back) towards |x| = 0 (smoothstep 0-0.22), after smoothing.
- Tried and dropped: harmonic (Laplace) weights along the surface (worse: keeps the pocket split), Taubin relax of
  every sharp ridge (no gain), half-rotation helper joints for the fore-leg roots (no measurable gain).

Fold-over face-frames (all clips, 48 fps), before -> after: total 54,897 -> 10,508; shoulders 28,142 -> 8,064,
hips/tail 18,838 -> 1,956, neck 2,468 -> 223, head 1,426 -> 234, lower legs 4,023 -> 31. Worst frame per clip:
AttackMelee 108 -> 45, AttackRanged 109 -> 33, Running 112 -> 37, Walking 106 -> 30, Death 127 -> 56, Fidget 121 -> 37,
Hit 123 -> 34, Dead 112 -> 25, Standing 90 -> 9. Front box (brisket/shoulders): 28,212 -> 7,123.
Open: at the raised leg's inner side a soft armpit crease remains at AttackMelee 15-22 and Death 25-35 (it reads as
a fold of skin, no flap); a thin slit stays behind the elbow in the brisket pocket.
Sheets: `review/fold_20261030/sheet_user_frame.png` (the user's framing, close and three-quarter),
`sheet_worst_frames.png` (AttackRanged 11, Running 13, Death 28, Fidget 37, tail base, standing armpit/underside),
`sheet_tiers.png` (Red and Black Wolf). Measure: `scripts/fold_measure.py <glb> [json] [--box=x0,x1,y0,y1,z0,z1]` (OVER line); renders: `scripts/fold_views.py`; sheets: `scripts/fold_sheet.py`.
Checks: winding 0 inverted, flat-shading 0.00, floor audit Wolf A/B/C ok (49 bindings, 0 problems),
`run_creature_review.py check` 3 tiers x 9 clips, 0 console errors. No Meshy credits.

### Second pass (2026-10-30, r5): brisket keel, armpit pockets, fangs

User on r4: a loose sheet with background gaps behind the raised elbow (AttackMelee ~17) and at the elbow in the walk,
plus a hard crease across the chest.
- Rest audit (`scripts/mesh_audit.py`, `scripts/thin_audit.py`): the skin is one closed manifold (0 boundary, 0
  non-manifold edges, 3 self-intersecting face pairs, no stray piece in the torso); no separate fur sheet exists.
  What exists: a thin keel of chest fur hanging between the forelegs (down to z 0.84), joined to the inner legs by
  pinched webs at the front, with narrow slots and pockets behind the elbows. The "sheet" is those walls folding
  over in the pose (back faces culled: the gaps).
- Fix (`scripts/armpit_rebuild.py`, before `refine_weights.py`): the skin's volume on a 5 mm grid, the keel removed
  per z slice below 0.95 (only the parts holding a foreleg axis stay), notches and pockets closed (ball 0.06), a
  smoothed signed distance as target; the 292 region vertices relax onto it (Laplacian + Newton projection,
  untangle before and after). Topology and UVs unchanged, so the texture carries over with no seam; AO rebaked.
- Fangs (detached-parts audit: two lower fangs on the upper jaw, 4.6 cm off the gums in the bite):
  `weight_refine.seat_teeth()` makes each fang rigid on the jaw owning most of its 8 nearest gum vertices; the two
  pieces moved to Bone30. `detached_parts_audit.py`: 0 detached in any pose.
- Tried and dropped: cutting the keel/pockets out and refilling each hole with a fan membrane (clean manifold, but
  spiky shading and more folds), subdividing the armpit (more folds per area), half-rotation helper joints for the
  leg roots (simulated: no change, the folds are the leg sweeping into the chest, not the blend angle), narrower or
  no midline fade, wider smoothing.
- Numbers (fold-over face-frames, all clips at 48 fps): r3 54,897 -> r4 10,508 -> r5 9,903; front box (brisket
  and shoulders) r4 7,008 -> r5 6,025; worst frame AttackMelee 45 -> 42, Walking 30 -> 27, Running 37 -> 30.
  Rest folded faces 8 (brisket front web). Winding 0, flat-shading 0.00, floor audit ok, viewer check 0 errors.
- Sheets: `review/fold_20261030b/sheet_framings.png` (rearing ~17 close and full, walking front 20/30),
  `sheet_legs.png` (both forelegs from the side, from below, in the walk), r4 before / r5 after.
- Still open: in the rearing bite a soft fold remains where the raised leg's inner side meets the brisket (the
  leg sweeps into the chest; linear blend skinning cannot slide skin), and a shallow crease at the walk's elbow.

## Gait rollout: Trot (2026-11-06)

`../gait_rollout_20261031/q5/` (README there): a procedural `Trot` (flying trot, front R + hind L at phase 0 as
Walking, 0.3667 s, stride 3.04, authored for 8.29 model units/s) grafted onto the installed source, installed and
bound in all three descriptors as `run: Trot` (3.04) with MM9's `Running` moved to `sprint` (4.18). MM9's AI wanders
the wolves at WalkVel (358 / 384 world units/s), which played Running at x0.86 / x0.73; they now trot at x1.08 / x0.93
and chase on Running as before (x1.78 / x1.47; the Grey Wolf's chase stays above 1.5, open). A rebuild here
(`build_runtime.sh`, `extra_clips.sh`, a far-LOD repair) drops the Trot: re-graft it with that package's
`scripts/finish.sh` (`SRC=<new export>`) before installing, and keep its run/sprint lines in `bind_actors.py`'s block.

## Deviations and open points

- Unused MM9 clips (aware, taunt, fidget2, wince2, die2, backpedal, backpedalrun, RAttack1 `RangeAttack` 1.066 s)
  are not exported. MM9 `lunge` events are not reproduced (clips stay in place).
- The voxel rebuild softens fine Meshy sculpt detail slightly; the folded pockets where fur layers fused (armpits,
  tail base) were relaxed on 2026-10-30, 8 small folded faces remain in the brisket pocket (a thin slit behind the
  elbows at rest).
- The muzzle is paler than MM9's dark mask (HD master choice); the Red Wolf reads saturated red in bright light.
- User artistic acceptance: accepted "wolf - ok" (2026-10-30, r5).
