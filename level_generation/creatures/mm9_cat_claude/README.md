# MM9 cat (mm9_cat) — 3D model, 2026-10-30

The MM9 town cat (`mm9/extracted/MODELS/MODELS/CAT.abc`, 40 joints, 274 tris, 10 clips; MONSTERS.txt row 294, `cat.dtx`,
`cat.scr`, Scale 2.5, Hostility 2) on the MM9 rig-reuse route of `../mm9_dfly_claude/` and `../mm9_wolf_claude/`: a new HD
Meshy mesh weighted to the original skeleton, the MM9 clips played with only the listed changes. Unlike the dog, the rest
pose is a new standing pose and the hind legs are solved per frame, because MM9's cat crouches on long folded hind legs.
Progress, hashes and receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_cat.glb` (cooked copy in `assets_dev`); one skin, no tiers |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_cat_claude`: `MM9 294 cat`, scale 250 (100 x MONSTERS.txt `Scale` 2.5) |
| Descriptor | `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv`: row 294, fallback visual legacy Cat A (463); monster id 9294 |
| Triangles LOD0/1/2/3 | 6,968 / 3,484 / 1,254 / 418 |
| Skeleton | 46 joints: the MM9 40 plus 6 helpers (`Xblegpiv_h`, `Xbleg_h`, `Xbankle_h`, and with 01; see "Hind knee fix"); MM9 names unchanged (`XCENTER`, `XbackA/B/C`, `Bone01`, `Xfrontleg`, `Xbackleg`, legs `Xflegpiv-Xfankle-Xffoot` and `Xblegpiv-Xbleg-Xblegmid-Xbankle-Xbfoot` (+01), neck `Xneckbase`, `XneckA/B/C`, `Xhead`, ears `Xearpiv-Xear` (+01), tail `Xtailpiv`, `XtailA` to `F`) |
| Clips (30 fps) | Standing 1.7 (stand1), Walking 0.4 (walk), Running 0.2 (run), Fidget 3.0 (fidget1), AttackMelee 0.67 (authored swipe, also ranged and cast), Hit 0.47 and Death 1.3 (authored: MM9 has neither), Dead 1.0 |
| Events | attack impact 0.26 s (the swipe's strike key) |
| Gait | stride 0.28 (walk), 0.32 (run) model units per cycle (`scripts/gait_measure.py`) |
| Floor | ground rule, rest shift 3.12 cm (`FLOOR_SHIFT` in `build_export.py`); `floor_audit.py --world mm9` ok |
| Meshy credits | **35 / 35** (backup account): Smart Topology v1 5, v2 5, head 5, 4K body retexture 10, 4K head retexture 10 |

## Route

0. **HD masters** (`references_hd/`, Codex): five views from renders of the MM9 model and skin. The first set (`superseded_v1/`)
   was mid-stride with a turned head: symmetrising it gave six legs and a hippo face. The final masters stand square.
   **Head turnaround** (`references_head/`): masters for a head-only Meshy model, because the body model's head was wrong.
1. **Meshy** Smart Topology 15k: `cat_smart_v2` (body), `cat_head_smart_v1` (head only). `cat_smart_v1` is the discarded
   first attempt.
2. **Clean** (`clean_meshy.py`): raw holes fan-filled (an open shell voxelises as a double wall: the speckled legs of the
   first pass), voxel 3.5 mm in Meshy units.
3. **Fit** (`fit_quad.py`): ICP on the torso with the paw midline (a global fit is pulled by MM9's bind pose), head turned to
   mirror symmetry, legs aimed at MM9's hind joints from `HIND_JOINTS`, tail spaced along the mesh tail.
4. **Symmetry** (`symmetrize.py`, right half mirrored), then **head graft** (`graft_head.py`, voxel union of the head-only
   model at scale 1.2, cut behind the jaw).
5. **Rest pose** (`rig_body.py`, `REST_FROM_POSE=1`): the rest is the reference pose and clip keys are converted by a
   rotation-only offset. Tail bones are rotations only (`NOLOC`): MM9's bind `XtailA` is 17 cm against 2.6 cm in the clips.
6. **Weights** (`rig_body.py`, `refine_weights.py`): nearest posed label + diffusion; an ear rule keeps the ear flick off the
   skull, a tail tube keeps the rump from shredding, capsule labels hold the hind legs.
7. **Reduce** (`reduce_body.py`, head denser) and mirror again (`sym_rigged.py`).
8. **UVs** (`uv_atlas_run.py`): xatlas, head charts x2.5, two uploads on one layout: whole body, and the head islands alone.
9. **Paint** (`compose_cat.py`): 4K retextures downsampled once to 2K; head paint merged over the head with a geometric neck
   fade and a mild gain; head texels on body islands take the blurred head colour plus the body paint's fur grain (a nearest
   copy gave stair steps); chart seams on the head and neck tone-levelled across the seam; the outer 3 px of each island (Meshy
   paints a pale rim there) refilled with the fur mirrored from just inside; the one-texel white line Meshy painted across the left hip replaced by the fur
   beside it; procedural eyes with a slit pupil. Gentle grade.
10. **Clips** (`clips_mm9.py`, `clips_keys.py`, `hind_ik.py`, `fore_stance.py`, `knee_helpers.py`): MM9 key poses as PCHIP curves, loop seams closed. The hind legs
    are a per-frame two-bone IK onto MM9's ankle and foot, as neither stretching the chain (tore the hips) nor scaling its
    joints (trailed the legs) held up. Swipe, Hit and Death are key poses. `fore_stance.py` then corrects the forelegs: see
    "Foreleg stance fix".
11. **Runtime** (`build_runtime.sh`): prepare, LODs, shadow shrink, specular 0, floor pass, winding.

## Rebuild

```sh
T=<lease token>; B="tools/run_creature_blender.sh --token $T"; P=level_generation/creatures/mm9_cat_claude
V=level_generation/props/mm9_isleofashes_claude/work/venv/bin/python
$V tools/mm9_import_discovery/convert_abc_model.py mm9/extracted/MODELS/MODELS/CAT.abc $P/source/cat --id cat \
  --texture 0=mm9/extracted/SKINS/SKINS/CAT.dtx --scale 0.0256
$B $P/scripts/mm9_rig_source.py $P/source/cat/cat.glb $P/work/mm9_cat_rig.blend 0 0.1819
KEEP_PIECES=0 CLEAN_MODE=none $B $P/scripts/clean_meshy.py $P/meshy/cat_smart_v2/model_urls_glb.glb $P/work/cat_clean_v2.glb 0.0035 0
HIND_JOINTS=0.105,0.185,0.077,0.128,0.099,0.08 GLOBAL_PAWS=-0.265 AIM_IK=1 AIM_VERTICAL=1 STRETCH_MAX=1.5 \
  REGION_GEO=0.095,0.13,0.15,0.0,0.145 GLOBAL_TORSO=-0.06,0.27 HEAD_ROT=sym HEAD_DIFFUSE=300 TIP=extreme AIM_LEGS=1 \
  AIM_MIRROR=1 AIM_TAIL=1 $B $P/scripts/fit_quad.py $P/work/mm9_cat_rig.blend $P/work/cat_clean_v2.glb $P/work/fit_v3.blend $P/work/fit_v3.json
KEEP=neg MID_BAND=0.012 MID_ITERS=15 $B $P/scripts/symmetrize.py $P/work/fit_v3.blend $P/work/sym_v3.blend $P/work/sym_v3.json
SCALE=1.2 CUT=0.45 TAPER=0.05 $B $P/scripts/graft_head.py $P/work/sym_v3.blend $P/meshy/cat_head_smart_v1/model_urls_glb.glb \
  $P/work/graft_v1.blend $P/work/graft_v1.json
REST_FROM_POSE=1 RIG_DIFFUSE=120 RIG_HINGE=20 $B $P/scripts/rig_body.py $P/work/graft_v1.blend $P/work/rig_v3.blend $P/work/rig_v3.json
$B $P/scripts/reduce_body.py $P/work/rig_v3.blend $P/work/reduced_v3.blend $P/work/reduced_v3.json 0.012 0.5 0.026
$B $P/scripts/sym_rigged.py $P/work/reduced_v3.blend $P/work/reduced_v3s.blend $P/work/reduced_v3s.json
$B $P/scripts/refine_weights.py $P/work/reduced_v3s.blend $P/work/refined_v1.blend $P/work/refined_v1.json
$B $P/scripts/uv_atlas_run.py $P/work/refined_v1.blend $P/work/uv_v1.blend $P/texturing/cat_body_upload.glb \
  $P/texturing/cat_head_upload.glb $P/work/uv_v1.json Xhead,XneckC,Xearpiv,Xear,Xearpiv01,Xear01 2.5
# xatlas packs differently per run: never re-run the UV step once the uploads went to Meshy (cat_retexture_v1, cat_head_retexture_v1)
$P/work/build_cat.sh <revision> --install      # dump, AO, compose, grade, export, runtime, viewer manifest
flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock \
  python3 $P/scripts/bind_actors.py mm9_cat_claude $P/work/actors_block.yml
```

`work/` and `work/tools/` hold the wrappers (`bl.sh`, `rig_cat.sh`, `rig_cat2.sh`) used for these steps; they are not sources.

## Checks (2026-10-30)

- Viewer `review/viewer/` (r18, MM9 original as second model): `tools/run_creature_review.py check` 8 clips, 16 switches, 0
  console errors. Acceptance from viewer shots, each looked at: `review/sheet_mm9_vs_ours.png` (MM9 left, ours right: rest
  and clip extremes), `review/sheet_a.png` (all angles, swipe, Hit, Death, Dead), `review/sheet_texture_closeup.png`
  (face, ears, flank). Single-skin model, so there are no tier sheets.
- Winding `check_winding.py`: 0 inverted. Smooth shading `flat_shading_check.py`: flat 0.00. Detached
  `detached_parts_audit.py`: 0 detached of 3 components.
- Texture `texture_quality.py`: atlas 55.4%, density spread 2.58 (the denser head, deliberate), fragments 0.5%, stretch p90 1.2.
- Gates `scripts/gates.py` (`review/gates.json`): loop seams 0; edge ratio p1 0.50-0.74, p99 1.40-1.97; largest single edge 23 (Death and Dead).
- Fold measure `scripts/fold_measure.py`, worst faces in one frame: Standing 41, Running 15, Fidget 54, AttackMelee 49, Hit 40,
  Death 125, Dead 121. These counts were the knee fold of "Hind knee fix" (Standing 50, Death 136 before it); read them with
  the collapse gate there, which reports by joint.
- Orientation `scripts/orientation_gate.py` at 48 fps: head 3.3 deg or less. Paws: Walking 11.1 / 4.6 (fore / hind), Running
  46.0 / 21.8, Fidget 31.2 / 0. These peaks fall between keys: MM9 interpolates its sparse keys linearly and ours are PCHIP,
  and the run swings a paw through a large arc in 0.2 s. Measured on our own 30 fps frames instead: Running 5.0 / 5.1, Walking
  9.5 / 7.4; in Fidget 0.1 at MM9's keys, up to 27.8 in the fast moves into and out of the lick. The poses match in the sheet.
- Floor audit `floor_audit.py --world mm9`: cat ok (stand 0, walk -1.0 to +1.4, living -2.4, dead 0). Hind IK shortfall 0.
- Regression `mm9_actor_models_build_every_binding` (`--world mm9`): 66 descriptors on 32 models, 0 failed; `mm9_` filter
  passed=4 failed=0.
- Not run: an in-game check (optional in the brief).

## Foreleg stance fix (2026-10-30)

User: the front legs look crooked in Standing's front view; each curves inward in an S and they pinch at the wrists.

Cause: MM9's stance, not the mesh or weights. MM9 keys the shoulders about 2.4 cm and the ankles 1.5 cm off the midline, which
fits its narrow chest. Our rest legs are straight at 3 cm under a wider chest, so the keys pulled the wrists together (gap 0.8
mm against 40 mm at rest). MM9's shoulder rotation also did not point our rest leg at the keyed ankle, which bowed the mid-leg.

Fix (`scripts/fore_stance.py`, in `build_export.py` after `hind_ik.py`): one constant sideways offset per side in the chest
frame, so Standing lands on shoulders at 3.0 cm and ankles at 2.7 cm, and the shoulder aimed down the rest segment at the
corrected ankle. The walk and run keep MM9's wider stance and take the aim only. In Fidget and AttackMelee a raised paw fades
back to MM9's line with its height, so it still reaches the mouth. Paw height, fore-aft path and ankle and paw orientation are
unchanged, and the mirror offsets make Standing symmetric at the joints.

| Mid-leg gap (mesh, h 0.05-0.07) | Before | After |
|---|---|---|
| Standing | 0.8 mm | 31-35 mm |
| Hit | 0.8-0.8 mm | 31-35 mm |
| Walking | 21-30 mm | 34-39 mm |
| Running | 10-18 mm | 26-32 mm |

Foreleg jitter at 48 fps (RMS second difference, `work/jitter_fore.py`), after / before / MM9: Standing 0.002 / 0.002 / 0.004,
Walking 4.53 / 4.49 / 4.67, Running 22.6 / 22.6 / 26.8, Fidget 0.46 / 0.43 / 0.66, AttackMelee 3.73 / 3.62, Hit 1.23 / 1.23,
Death 0.77 / 0.76. Orientation gate numbers are unchanged. Leg centres differ left to right by about 2 mm in the mesh; the
joints are exact. Before and after, from viewer shots: `review/sheet_foreleg_before_after.png`.

## Hind knee fix (2026-10-30)

User: the hind knee collapses in the sitting pose, with a sharp fold, a pointed flap, stretched shiny texture and a slot of
background beside the belly, plus a stretched strip down the outside of the foreleg.

Cause: mainly the IK folding past what the mesh can do. MM9's paw targets left our hock 5.6 cm off the floor and 3 cm from the
hip, so the knee closed to 19 degrees. Linear skinning cannot hold that. Weights added to it: back-of-knee skin sat half on the
spine, which stays with the pitched pelvis, and half on the shin. The foreleg strip was not a fold: the earlier rim repair left
a smooth band about 7 mm wide along every chart seam.

Fix:
- `hind_ik.py`: where the knee would close past 45 degrees the tarsus turns back about the ankle towards lying flat, as a sitting
  cat's does. The turn is found per frame and low-passed over the clip (wrapped on loops). The knee aims forward in the sagittal
  plane with a slight splay, because the sitting pelvis is pitched past vertical. Paw and ankle positions and orientation stay.
- `knee_helpers.py`: half-rotation helpers on hip, knee and ankle (6 bones), keyed as a pure function of the child's curve.
  Back-of-knee and groin skin sorted by two smooth ramps. On the concave side of knee and hock the blend is sharp, so each side
  stays rigid and presses against the other. The hock has no helper.
- `compose_cat.py`: seam rims refilled with mirrored fur. Mesh, triangle counts and UV layout are unchanged; LODs rebuilt.

Tried and dropped: moving shin skin to the thigh by threshold (cut a hard edge and made a flat slab on the hock), a 36 degree
knee target (stretched the knee front), a sharper crease (more flips).

`scripts/collapse_gate.py` counts faces whose area falls below 0.2 of rest or whose normal flips against rest carried by the
face's own skin rotation, per clip and joint region, and which of the worst frame's faces any of 42 rays can see (exposed).
Reports: `review/collapse_before.json`, `review/collapse_after.json`.

| Clip | Face-frames | Knee L/R, worst frame | Knee L/R, exposed | Hip L/R | Fore L/R | Body |
|---|---|---|---|---|---|---|
| Standing | 4564 > 2652 | 21/22 > 17/19 | 10/12 > 8/12 | 2/4 > 2/3 | 0/0 > 0/0 | 39 > 10 |
| Hit | 1320 > 765 | 21/22 > 17/19 | 10/12 > 8/12 | 2/4 > 2/3 | 0/0 > 0/0 | 39 > 10 |
| Fidget | 9277 > 6021 | 21/22 > 17/19 | 10/11 > 7/12 | 2/4 > 2/3 | 13/0 > 13/0 | 50 > 21 |
| AttackMelee | 1905 > 1128 | 21/22 > 17/19 | 10/12 > 8/12 | 2/4 > 2/3 | 9/0 > 9/0 | 46 > 17 |
| Death | 7062 > 5194 | 28/24 > 20/20 | 19/1 > 8/4 | 9/9 > 12/11 | 26/25 > 26/25 | 91 > 52 |
| Dead | 6417 > 4774 | 28/23 > 16/14 | 19/1 > 9/4 | 8/8 > 12/11 | 26/23 > 26/23 | 91 > 52 |
| Walking | 210 > 284 | 3/3 > 8/7 | 0/1 > 0/2 | 0/0 > 2/2 | 7/5 > 7/5 | 13 > 12 |
| Running | 141 > 144 | 5/5 > 7/6 | 4/2 > 0/1 | 2/1 > 2/2 | 8/8 > 8/8 | 17 > 10 |

The target of about 0 at the knees in Standing is **not met**: 17/19 remain. In the last list taken (one build before the ankle
helpers, left leg) those exposed were five on the inner hock and three where the shin tucks under the thigh, 0.45-2.1 of rest
area: the faces bridging a real fold reverse, and a few at the ends of the crease can be seen through the gap between the legs.
Sharper creases raised the count. Removing them needs a pose that folds less or a mesh edit. Walking's counts rose a little
(helpers and sharp crease), Death's and Dead's hips too, and the Death and Dead forelegs were not improved.

Still rough: the inner side of the hind paw and hock in sitting clips. The ankle helpers removed the worst crumple, but close up
through the gap between the forelegs it stays angular, with a few flecks of white at the fold (`review/knee_after/st_inner.png`).

Held: foreleg gap 31-35 mm, paw orientation numbers unchanged. Jitter at 48 fps, RMS second difference of 14 leg joints, after /
before / MM9: Standing 0.004 / 0.002 / 0.003, Walking 4.45 / 4.45 / 4.54, Running 26.2 / 26.2 / 28.3, Fidget 0.30 / 0.30 / 0.44,
AttackMelee 2.54 / 2.54, Hit 0.90 / 0.90, Death 0.66 / 0.63. Before and after from viewer shots at the user's framing, each
clip's camera following its own knees: `review/sheet_knee_standing.png`, `review/sheet_knee_clips.png`.

## Deviations and open points

- **Size**: the model is 0.30 m tall at Scale 1, so MONSTERS.txt's Scale 2.5 makes a 0.75 m cat next to a 0.94 m dog. It is
  large for a cat, but this is the MM9 table value and it was kept.
- MM9's hind joints above the ankle are not followed in sitting clips: flat tarsus and forward knee (`hind_ik.py`). Six helper bones added.
- The foreleg joint positions differ from MM9's keys (`fore_stance.py`); paw height and paw and ankle orientation do not.
- MM9's `stand1` is a sitting idle on folded hind legs; the rest pose of this model is standing, and the clip's hind legs come
  from `hind_ik.py`, so the feet land where MM9's do, with different knee angles.
- MM9 has no attack, Hit or Death clip for the cat: AttackMelee (a swipe), Hit and Death are authored key poses, not MM9
  motion. The attack exists because the generator makes the row `Aggress` and the engine requires attack clips.
- The row is `Stationary` in the generated table (its MM9 Move column is 0).
- Unused MM9 clips: fidget2, down, up, standdown, fidgetdown1, fidgetdown2.
- The tail bones are rotations only, so the tail keeps its mesh length rather than MM9's bind lengths.
- The texture is denser on the head on purpose (density spread 2.58), which misses the usual uniform spread.
- The coat is the masters' brown tabby with white chest and paws, not a copy of the 128 px skin.
- User artistic acceptance: not recorded.
