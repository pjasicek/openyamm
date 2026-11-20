# MM8 Ratman (`m448`, Ratman / Wererat / Greater Wererat) reduction (2026-10-18)

User: "OK do those 5" (MM8 reduction batch: ratman, m436, m584, wolf, m540). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture variant: UVs are kept, so the merged head atlas,
the three trouser variants and region ramps stay valid. No Meshy credits. Scripts copied from
[mm8_m560_reduce_claude](../mm8_m560_reduce_claude/README.md) (coincident-vertex separation, exact source weights).
The sword (`mm8_ratman_sword.glb`, 136 triangles) is unchanged.

Source: installed `assets_source/worlds/mm8/models/mm8_ratman.glb`, identical (SHA-256) to
`mm8_m448_claude/export/mm8_ratman.glb`; copied to `work/mm8_ratman_source_pre_reduce.glb` (rollback source).
One material `Ratman_A` (B/C are variants) on a 2080x1024 body+head atlas, mesh node `Ratman`, 4 influences.
The production project has no shared gate-runner config (its motion gates are project scripts), so no gate rerun.

## Regions

Weld 9,663 -> 2,076 open edges (unchanged by every step; ragged shirt, fur tufts, whiskers), no coincident vertices
with other weights, no split seam. The head set (right half of the atlas) is 8,259 of the 14,623 triangles: the
production kept the Meshy head surface whole and had already cut the body. Face groups (`scripts/ratman_groups.py`):

| group | faces | treatment |
|---|---:|---|
| small pieces (<= 80 faces: incisors, eyes, whiskers, fur tufts) | 1,703 | kept exactly |
| ragged shirt (one 799-face piece) | 799 | kept exactly |
| head set (main head surface, ears) | 7,141 | ladder cut |
| hands and fingers (hand+finger weight > 0.5) | 2,418 | 40 % |
| rest of the body (legs, feet, arms, tail, pouch) | 2,562 | 65 % |

The shirt in the shared cut (75 % and also on its own at 85 %) lost the back flaps: 25.4 mm in Running at every
step (large faces across the back pick up the wrong thigh weights). Kept exactly, the error fell to 16.9 mm.

## Ladder

Limits scaled to the 1.47 m standing height (p99 4.41 mm, max 22.05 mm).

| ladder | head | triangles | p99 / max mm | worst | IoU min | SSIM | |
|---|---:|---:|---|---|---|---|---|
| g1 (shirt in rest 75 %, hands 50 %) | 45 % | 8,639 | 2.71 / 25.44 | Running:6 shirt back | 0.996 | 0.997 | fail |
| g2 (shirt 85 %) | 45 % | 8,723 | 2.65 / 25.44 | Running:6 shirt back | 0.996 | 0.997 | fail |
| g3 (shirt kept, hands 50 %, rest 75 %) | 55 % | 9,557 | 2.30 / 16.92 | Death:6 right foot | 0.997 | 0.998 | pass |
| g3 | 45 % | 8,843 | 2.38 / 16.92 | | 0.997 | 0.997 | pass |
| g3 | 35 % | 8,129 | 2.61 / 16.92 | | 0.997 | 0.997 | pass, ears break up |
| **g4 (shirt kept, hands 40 %, rest 65 %)** | **45 %** | **8,345** | 2.92 / 16.92 | Death:6 right foot | 0.995 | 0.997 | **picked** |
| g4 | 40 % | 7,989 | 2.96 / 16.92 | | 0.995 | 0.997 | pass, cheek lumps |

Every step passes the numbers; the pick is visual. Head at 35 % breaks the ear rims and lumps the cheek
(`review/close/sheet_g3_head.png`: source / 55 / 45 / 35 % head); 45 % matches the source in texture and silhouette.
Hands at 40 % and the rest at 65 % keep the claws, the sword grip curl, the three toes and their claws
(`review/close/sheet_g4.png`, `sheet_feet.png`). The 16.9 mm maximum is the right heel in the Death fall (the
source's sharper heel bump is softer); toes and claws are unchanged. Texture drift: 2 faces over 40, 0.4 cm2 in
total; no lock. Stretch check: the same 8 neck faces stretch over 20x in the source and the candidate (pre-existing).

Shading checked on GLBs imported directly with their own normals (`scripts/glb_close.py`,
`review/glbclose/sheet.png`, `head_pair.png`); clay renders of `work/source.blend` show weld-scrambled normals.

## Head and shoulder fix (user review 1)

User, on the Attack/ready pose from the right: "fix his head - it is like WAY too much in front? should be a bit
more back and up? and fix his right arm?". Both problems are in the installed model too (`review/head_fix/
installed_sheet.png`, `installed_right.png`); the reduction moved no bones. Causes, by layer:

- **Weights (rig).** The head set had no `B_Neck` weight at all; the back half of the skull, throat and mane carried
  `B_R_Clavicle` / `B_L_Clavicle` (mean 0.2, up to 0.78), `B_Spine1` and the upper-arm twist bones
  (`review/head_fix/w_sheet.png`). Raising the sword arm dragged the cheek and skull, the right shoulder shared its
  surface with the head, and 2-5 neck faces stretched over 20x in every clip.
- **Clips.** The ready pose shared by Standing, Attack, Hit, Fidget and the start of Death points the neck 15 degrees
  below horizontal (rest 24 above) on an 18-degree forward lean: the head joint sits 10 cm below the shoulder joints
  and the skull hangs in front of the chest (Running: -22 degrees). The native sprites carry it on the shoulders.
- **Shoulder rhythm (clips).** The shoulder caps are 0.7-0.9 on the clavicles and the clavicles barely move, so the
  sword arm held about 60 degrees forward bends at a boxy corner under the head.

Fixes, applied to the reduced full-detail file before the LOD build (`work/r57_lod0.glb` -> `work/r57fix_lod0.glb`):

1. `scripts/reweight_head.py`: no clavicle, arm or spine weights left on the head; since review 2 one harmonic weight
   field over the head shell and the body's neck socket (see "Neck hole fix" below). Small separate pieces within
   45 cm of the neck (fur tufts, whiskers, teeth, eyes; 141) become rigid on the skin under their root; since review 3
   the vest's fur collar and the tufts near the skull also ride the head (see "Mane fix" below). Geometry is
   unchanged.
2. `scripts/lift_neck_clips.py`: per key, `B_Neck` is pitched up by (30 degrees - its world pitch), clamped to 0..45,
   and `B_Head` by the opposite, so the head keeps its orientation and rises onto the shoulders. Ready pose and
   Running get 32-45, Walking 13, Fidget's look-up 0; Death fades it out by 0.45 s, Dead is untouched.
3. `scripts/shoulder_follow.py`: per key, each clavicle takes 30 % of its upper arm's swing from rest (at most 20
   degrees) and the upper arm is counter-rotated, so the arm's direction is exactly as authored and only the shoulder
   point follows (sword arm in the ready pose: 20 degrees, a few cm forward). Both arms, all clips, per key, so Dead
   still equals the last Death frame.
4. `scripts/compact_glb.py` drops the replaced accessors.

A first try that moved the head in the rest pose (pitching the rest neck up, "apply pose as rest") also raised the
mane into upright spikes and lifted Walking and Fidget the same amount (`review/head_fix/angle_sheet.png`); the
per-key lift replaced it.

Results: `review/head_fix/before_after_Attack0.png`, `before_after_Attack14.png`, `before_after_Attack27.png`
(installed / reduced / fixed; right side, left side, three-quarter, right shoulder), every clip in
`allclips_{rside,q34,neck_low,neck_back}.png`, the neck seam from below and behind in `check_neck.png`. The throat is
a continuous stretched-fur surface from chin to collar; no gap opens. The mane still fans up a little behind the
raised head in the ready pose.

## Neck hole fix (user review 2)

User, on a front three-quarter close-up of the fixed ready pose: "hole in his neck". Under the chin, torn flat
fur and skin shards stood at odd angles with a dark surface between them (`review/neck_fix/a0.png`: installed /
reduced / head-fixed, Attack frame 0, front, front clay, below, three-quarter).

Cause: the head is a separate open shell plugged into a dark neck socket of the body (the body's neck opening and
the shell's rim loops; `review/neck_fix/nohead.png` shows the socket with the head hidden). The first reweight gave
the shell a neck/head ramp by position and glued its rim to the torso with the rim's old weights, but left the socket
on the torso. Lifting the neck pulled the shell's throat away from the socket and stretched the rim band unevenly
between glued and ramped vertices, so the throat folded into shards and the dark socket showed between them. The
reduction is not involved: the same fix chain on the unreduced installed source gives the same throat
(`review/neck_fix/cull.png`, left column), and the ladder kept every open edge of the source.

Fix (`scripts/reweight_head.py`, rewritten): one harmonic weight field (graph Laplacian over the mesh edges plus the
8 nearest rest-pose neighbours of either layer) over the head shell and the body's neck zone (body vertices with
t > -0.4 within 13 cm of the neck segment; 109 at full detail). Fixed values: the skull (head set from 75 % of the way
to the head joint) is `B_Head` 1, body vertices outside the neck zone keep their own weights (a head share there
moves to `B_Spine2`). Overlapping shell and socket vertices get the same weights and move together, and the throat
stretches evenly from chin to collar. The clip lift and the shoulder rhythm are unchanged.

Results (`review/neck_fix/`): `a0_nf.png` (Attack 0: installed / head-fixed / neck-fixed), `nf_big.png`,
`nf_others.png` (Attack 14 and 27, Standing 24, Running 9, front and three-quarter), `cull.png` (back faces culled
as in the engine: no background shows through the throat; unreduced source with the same fix on the left),
`skull.png` (skull shape unchanged; the mane now lies flatter). The throat is a continuous fur surface, darker than
the chin where the shell's underside texture is stretched; a few mane flaps still stand off the side of the neck.

The ready pose is taller than the installed one: Standing frame 0 measures 1.525 m (LOD3 1.533 m) instead of 1.469 m
(1.465 m), because the head top replaced the mane hump as the highest point, as in the native sprite. The actor
regression checks the 158-unit standing height on the posed coarsest LOD, so the three bindings need scale 103.07
instead of 107.540462 (158 / 1.533) when this is installed; the body becomes about 4 % smaller and the head top
matches the native 158.

## Mane fix (user review 3)

User: "e.g. idle frame 63 - there is some geometry leaking into the head?" (Standing, frame 63 at 48 fps, 1.3125 s).
Flat brown flaps cut across the brow, cheek and ear; in Fidget a whole fur sheet lay over the side of the head
(`review/mane_fix/before_after.png`, top row).

Cause: the mane is the brown fur collar of the vest (a separate 799-face body-set piece that also holds the grey
cloth) plus loose tufts. It lies behind and above the skull, mostly 11-16 cm from the neck axis, just outside the
13 cm neck zone, so it kept its production weights (`B_Spine2` and the clavicles) while the skull is `B_Head` only.
The clip lift moves the head up and back, as asked in review 1, and the skull rose through the collar. A test that
counts body-set vertices more than 4 mm inside the rigid skull (excluding those already inside at rest; scratch
script, Blender BVH against the skull faces) found up to 55 per frame in Standing and 133 in Fidget; the installed
model has none outside Running.

Fix (`scripts/reweight_head.py`): fur of the collar outside the neck zone takes a `B_Head` share by its distance to the
skull, 1 within 4 cm and smoothstepped to 0 at 12 cm (`MANE_FALLOFF=0.04,0.12`), mixed with its own weights. The share
is multiplied by a fur mask from the base colour (grey cloth 0, smoothed over six rings of edges so the sheet does not
tear at the cloth border). Loose tufts take the same share by their nearest point to the skull, on top of the weights
of their root. Tried and rejected (`review/mane_fix/variants_Standing63.png`, `variants_Fidget63.png`: neck-fixed,
4-12, 6-18, 8-24 cm): wider falloffs lift more of the collar into a crest and pull white vest strips onto the neck;
measuring the distance to the whole head shell instead of the skull put shoulder and throat tufts on the head; pinning
the collar as fixed values inside the harmonic solve pulled the whole head shell onto `B_Head`.

Results: face, cheek and ear are clear in Standing and Fidget (`before_after.png`, bottom row); the collar now rides
behind and above the raised head, as the installed hump does from the front. Inside-the-skull counts drop to 29
(Standing), 47 (Fidget), 42 (Attack); what remains sits under the jaw at about 1.2 m, where side-of-neck flaps on the
clavicles meet the jaw underside, not on the face. No face of any LOD stretches over 20x in any clip
(`work/lod_check_r57m.json`, `glb_stretch.py`: 0), floor contact unchanged. The neck-fixed export is kept as
`work/mm8_ratman_neckfix.glb`, its LOD0 as `work/r57nf_lod0.glb`.

The collar flaps above the head are now the highest point: Standing frame 0 measures 1.614 m (LOD3 1.604 m), against
1.525 m (1.533 m) after the neck fix and 1.469 m (1.465 m) installed. For the regression's 158-unit standing height
on the posed coarsest LOD the bindings would need scale 98.5 (158 / 1.604), about 8 % smaller than installed, with
the head top below the native 158; scale 103.07 keeps the head top at 158 and the collar reaches about 165 units.
Superseded by the crest removal in review 4, which makes the head top the highest point again.

## Attack and crest (user review 4)

User: "attack ratman - first 40 frames is just angling of the right hand, then abrupt swing, it should be like in the
first 40 frames also blended like the leg/hip movement ... and also the swing maybe should be blended in there so the
swing itself isnt only 20 frames?" and, on a close-up of the head with fur strips standing above it: "like there is
on top of his head behind these fur strips ... we can just remove them if it causes this black area and a hole".

**Attack.** The production clip held the body still for 40 frames (48 fps) while only the arms moved from the guard
to the slash's start; then the left foot stepped and the pelvis dropped 12 cm in 3 frames (30 degrees of pelvis turn
between two keys), the over-the-shoulder wind-up took 4 frames before a hold, and the strike 2.4 frames (51.2-53.6).
`scripts/retime_attack.py` plays the slash on a monotone time warp: the step and wind-up take frames 0-32, the held
top 32-44, the strike about 10 frames (hand up to 42 cm per frame instead of 73), and the follow-through keeps its
speed. The arms' difference from the guard fades out as an offset over the first 24 frames, so pelvis and legs play
the source step unchanged: the left toe lifts 7 cm and lands by frame 22, no toe sinks below its rest height. Clip
length (1.633 s) and impact (1.116667 s, frame 53.6) are unchanged, so is the impact pose (hand within 3 mm, the
sword's direction there) and `actors.yml`. `review/attack_v2/strip_front.png`, `strip_q34.png`: previous (top) /
new (bottom) at the same frames.

**Crest.** The fur strips are the upper part of the vest's fur collar and loose tufts that the source model wraps up
around the back of the skull, with a dark gap between them and the skull; the installed ready pose hid it because
the head hung forward out of it, and the rest pose shows it in the installed file too. Since the head lift and the
mane fix the strips ride the head and stand above it in every clip. `scripts/drop_crest.py` (after
`reweight_head.py`) deletes the faces of those pieces (body texture set, not the body skin) whose centroid lies above
1.5 m at rest or that ride the head (mean `B_Head` weight over 0.5): 514 faces in 56 pieces. The back of the head
shows the head shell's own fur; no gap or socket shows (`review/crest/heads.png`: mane-fixed / new, nine clip frames,
front-right, front-left, back and top, back faces culled). Narrower cuts (only the head-riding faces, or only those
above 1.55 m) left flaps on top or at the back.

LOD0 is now 7,831 triangles (LODs 3,871 / 1,910 / 930). The head top is the highest point again: Standing frame 0
measures 1.525 m (LOD3 1.533 m), so the bindings need scale 103.07 (158 / 1.533) for the regression's 158-unit
standing height, with the head top at the native 158. No face of any LOD stretches over 20x in any clip
(`work/lod_check_r57c.json`, `glb_stretch.py`: 0); floor contact as before (Attack -1.8 cm, as in the source).
The mane-fixed export is kept as `work/mm8_ratman_manefix.glb`, its LOD0 as `work/r57m_lod0.glb`.

## Trouser streaks (user review 5)

User, on the green tier: "what are the streaks on his trousers?" (near-black triangles and streaks on bright green).
Not from the reduction: the installed model shows the same. The engine recolours the trousers per tier
(`game/shaders/fs_model.sc`): each base-colour texel's luminance, normalised to the region's range (0.028-0.068
linear, a 2.4x window; ramps in the material extras), picks one of 16 native palette stops from near black to bright
green. The shared texture's UV islands differ in brightness and carry baked fold/occlusion blotches (p5-p95
luminance 0.029-0.066, i.e. the whole ramp), so the ramp turned mild dark-green patches into near-black ones.

`scripts/level_trousers.py` (on the finished export; geometry and the other maps unchanged): per UV island of the
trouser mask, the log luminance is split into a 12-texel Gaussian low-frequency part (normalised to the island) and
the detail around it; the low part becomes the mean trouser luminance (0.0449) and the detail is kept at 0.6
strength, blended by the soft mask. p5-p95 is now 0.037-0.051 (the middle third of the ramp): even mid-green, blue
and maroon with the cloth grain and the shading of the normal map. `review/trousers/tiers.png` (each tier before /
after) and `legs.png` (green before, green and maroon after; front, back, side). The export before this step is
`work/mm8_ratman_crest.glb`. Other creatures recoloured with ramps may have the same blotches; not checked.

## Build

`export_cand.py` (`REA_CAND=Cand_57 REA_NODE=Ratman`, `work/ladder.blend` = g4) -> `swap_lod0.py ... Ratman`
(`work/r57_lod0.glb`) -> head, shoulder, neck, crest and attack fix above (`work/r57fix_lod0.glb`) -> `build_lods.py` (as the m448
project: 0.5 / 0.25 / 0.125, 4 influences) -> `shrink_shadow_lods.py` (copied from m448: shadow LOD1-3 tucked
2/4/7 mm inside) -> `carry_variants.py` -> `compact_glb.py` -> `level_trousers.py` -> `compact_glb.py`: `export/mm8_ratman.glb`, 5.8 MB (installed 6.7 MB).
Materials, variants, images (byte-identical), node names and the eight clip names match the installed file.
`work/mm8_ratman_r57_prefix.glb` is the reduced export before the fixes, `work/mm8_ratman_headfix1.glb` the one
reviewed in review 2.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 14,623 | 7,287 | 3,584 | 1,753 |
| reduced | 8,345 | 4,106 | 2,013 | 969 |
| reduced, crest removed | 7,831 | 3,871 | 1,910 | 930 |

`work/lod_check_{src,r57,r57nf,r57m,r57c}.json`: every LOD keeps the source rest bounds (1.698 m, tail tip; LOD3 tail
0.72 m like the installed LOD3; 1.673 m with the crest removed) and the same floor contact per clip (Death dips 0.168 m below in the source as well). With
the fixes no face of any LOD stretches over 20x in any clip; `scripts/glb_stretch.py` (stretch_check on the exported
GLBs, every frame of every clip, full detail): installed 8 faces, reduced 8 (the same neck faces), head-fixed 0,
neck-fixed 0, mane-fixed 0, crest removed 0. `review/lods/sheet.png`: LOD3 (969) turns the extended
right hand into a stub at the attack release and slightly dulls the muzzle; the installed LOD3 kept the fingers.

Viewer: `review/viewer_trousers/` (revision `reduce-6-trousers`: installed vs reduced with the head, shoulder, neck,
mane, crest, attack and trouser fix for each tier, trouser ramps baked by `VIEWER_DIR=review/viewer_trousers
VIEWER_REVISION=reduce-6-trousers scripts/viewer_tiers.py` from the GLB's own atlas, LOD0 only, no sword; the manifest's sha256 and `?v=` are rewritten
on every build and `review.js` loads the manifest with `cache: 'no-store'`). `node
level_generation/creatures/claude_shared/check_viewer.mjs <viewer_trousers URL>` (`tools/run_creature_review.py`
only opens `review/viewer/`): 48 model/clip switches, no console errors. Superseded: `review/viewer_crest/` (review 5,
`reduce-5-crest`), `review/viewer_mane/` (review 4,
`reduce-4-mane`), `review/viewer_neckfix/` (review 3, `reduce-3-neckfix`) and `review/viewer/` (review 2, `reduce-2-headfix`).

## Status

Installed 2026-10-19 (user: "ok good accept") with `python3 tools/install_model.py
level_generation/creatures/mm8_ratman_reduce_claude/export/mm8_ratman.glb --world mm8` after `check_winding.py`
(0 inverted closed parts). The three `mm8_ratman.glb` bindings in `assets_dev/worlds/mm8/models/actors.yml` (and
`mm8_m448_claude/actors_ratman_binding.yml`) use scale 103.0679 (158 / 1.53297, the posed LOD3 standing height);
`OPENYAMM_REGRESSION_FILTER=mm8_ratman_actor_models ./build/game/openyamm --headless-run-regression-suite actors`:
`mm8_ratman_actor_models_keep_native_roles` passes. Recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).
Rollback: install `work/mm8_ratman_source_pre_reduce.glb` the same way and restore scale 107.540462.

Reproduce: `import_source.py` (`REA_NODE=Ratman REA_GLB=<rollback source>`) -> `REA_PROTECT=B_Head dump_mesh.py` ->
`small_pieces.py`, `dump_regions.py`, `ratman_groups.py` -> `REA_KEEP_FACES=work/keep_small_shirt.npy
REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=2:0.4,3:0.65 run_ladder.sh g4 0.5709,0.5465` -> `stretch_check.py`,
`close_ladder.py`, `close_sheet.py`, `texture_drift.py r57` -> `export_cand.py`, `swap_lod0.py` ->
`reweight_head.py work/r57_lod0.glb a.glb`, `CREST_Y=1.5 CREST_HEAD=0.5 drop_crest.py a.glb a2.glb`,
`retime_attack.py a2.glb a3.glb`, `lift_neck_clips.py a3.glb b.glb`, `shoulder_follow.py b.glb c.glb 0.3`,
`compact_glb.py c.glb work/r57fix_lod0.glb` -> build as above -> `REA_NODE=Ratman lod_check.py`, `glb_stretch.py`,
`lod_views.py`, `glb_close.py`, `pose_shots.py` (clip-frame shots straight from GLBs; `POSE_CULL=1` culls back faces, `POSE_FPS=48` counts frames
as the viewer does),
`VIEWER_DIR=review/viewer_trousers VIEWER_REVISION=reduce-6-trousers viewer_tiers.py <installed> r100
export/mm8_ratman.glb r57t`. The LOD build runs in Blender: `blender -b -P scripts/build_lods.py`.


## Gait rollout (2026-10-31)

Package [h21](../gait_rollout_20261031/h21/README.md) appended new in-place locomotion clips to the installed source
`assets_source/worlds/mm8/models/mm8_ratman.glb` (existing clips, meshes, skins and materials byte-identical): `Sprint` (humanoid set Unarmed-Sprint, 0.58 s, sprint_stride_length 4.3509) for MAW's chase; walk and run unchanged.
Bindings are in `../gait_rollout_20261031/h21/bindings.yml` (applied by the rollout coordinator). Rebuild:
`level_generation/creatures/gait_rollout_20261031/h21/scripts/rebuild.sh ratman` (from `h21/work/mm8_ratman_pre_gait.glb`,
the pre-gait source), then `python3 tools/install_model.py
level_generation/creatures/gait_rollout_20261031/h21/export/mm8_ratman.glb --world mm8 --name mm8_ratman.glb`. A far-LOD repair,
head-bob or reduction rerun on this model must re-graft these clips: copy its new source over the pre-gait copy and
rerun the rebuild (or graft them with `claude_shared/graft_clips.py`).
