# MM9 Colloidal Warrior body (mm9_colloidalwarrior) — 3D actor, 2026-10-31 (second pass r9, 2026-11-01)

MM9 `COLLOIDALWARRIOR.abc` (56 nodes; one skinned piece `Box06`, 660 triangles, plus hidden Biped bone boxes; 16 clips incl. the bind
pose; no child model): rows 9234 Colloidal Soldier L50 (`MM9 Colloidal A`, COLLOIDAL1, MONSTERS Scale 1.5), 9235 Colloidal Warrior L60
(`B`, COLLOIDAL2, 1.75), 9236 Colloidal Guardian L70 (`C`, COLLOIDAL3, 2.0).
**Humanoid route** (MM9 skeleton and clips, grafted five-finger MPFB hands, head-only Meshy model, separate head set), as `mm9_bigfoot_claude`.
Opaque body: MM9's three skins have alpha 255 and no fullbright flag, so no blending (the engine's blended-sort limits do not apply);
the slime reads through a glossy material (roughness 0.28-0.6, specular kept on), not see-through.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_colloidalwarrior.glb` (`tools/install_model.py --world mm9`), variants `cw_a/b/c` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, `MM9 Colloidal A/B/C`, **scale 150 / 175 / 200** (100 x MONSTERS Scale; descriptor heights 307/358/410 already match), `yaw_offset` -1.570796327, stride walk 1.30 / run 2.6 (model metres), melee impact 0.489 s (`Rattack` in Hattack1), ranged impact 1.333 s released at `cast_hand` = `Bip01 R Hand` (MM9's RangeAttack hand), look `Bip01 Head` (50/30 deg), upper body `Bip01 Spine2` |
| Triangles LOD0/1/2/3 | 12,520 / 6,258 / 2,251 / 749 (body set 7,994, head set 4,526; hands about 3,600) |
| Skeleton | MM9's 56 nodes (true-handed by `mirror_glb.py`), rest rotations MM9's, joints translated to the fit, + 30 finger bones (each takes MM9's own finger bone's rest frame) + 16 half-rotation helpers (`*_h`, incl. Neck and Head). Head pivot moved 14 cm toward the face (deviation, see Collapse) |
| Clips (30 fps) | All 15 MM9 clips + Dead (`static_model`, the bind pose, not carried). Bound: Standing `stand`, Walking `walk`, Running `run`, Fidget `fidget1`, AttackMelee `Hattack1`, AttackRanged `Rattack1`, Hit `wince1`, Death `die1`, Dead. `script_clips`: attack2 `Hattack2`, fidget2, hit2 `wince2`, taunt `Taunt`, death2 `die2`, backpedal `BackPedal`, backpedal_run `BackPedalRun`. None left out |
| Fingers | MM9 animates five real finger chains (Finger0-42, curls to 65-82 deg), so each MPFB finger bone copies its MM9 bone's local rotation (`finger_alias` "copy", factor 1); MPFB grafted straight (curl 0) like MM9's bind |
| Textures | body 2K colour + 1K normal + 1K ORM + 1K region mask; head 2K colour + 1K normal + flat ORM + 1K mask. One shared set for all tiers, ramps only. 8 images, 17.9 MB GLB buffer |
| Meshy credits | **20 / 30** (second pass 0): body Smart Topology 5 (`cw_smart_v1`), head-only Smart Topology 5 (`cw_head_smart_v1`), body 4K retexture 10 (`cw_retex_v1`). Backup balance 3,900 at the end |

## Second pass (r9, 2026-11-01, coordinator's review; 0 credits)
Installed r9; everything below the r4 sections that this pass changed is restated here.
1. **Tone.** Measured under the same viewer light with MM9's own model and skins loaded in a copy of the viewer
   (`review/viewer_cmp/`, `scripts/tone_cmp.sh`, `scripts/tone_measure.py`, sheet `review/tone_cmp.png`): our tiers were 12-14 %
   more saturated than MM9's, and already darker (MM9's Blender renders in the first tier sheet are much darker than the same
   skins in the viewer: that sheet misled the first comparison). Now: saturation x0.88 for B and C in `tier_ramps_cw.py`
   (median S ours/MM9: B 0.63/0.61, C 0.69/0.66); value ours/MM9 B 0.49/0.54, C 0.45/0.51. I did not darken further, because they
   are already below MM9 in value. In game the Soldier read pale grey-mauve (`review/ingame_r6/`), so its ramps went to value 0.80 and
   saturation 1.0 (viewer: V 0.51 / S 0.56 vs MM9 0.69 / 0.48) and the specular went from 1.0 to 0.4 on all materials
   (`openyamm_specular` extra in `rebuild.sh`). In game r8/r9 (`review/ingame_sheet.png`, `review/ingame_r8/`): clay-brown Soldier,
   olive Warrior, dark red-brown Guardian. The viewer does not apply `openyamm_specular`, so the viewer highlights are stronger than in game.
2. **Armpit notch.** Bigfoot's FLANK rule (`neck_shoulder_weights.py`, armpit wall to Spine2/Spine3, 5 rings, 16 passes):
   AttackMelee R shoulder 70 -> 55 face-frames at the worst frame (exposed 65 -> 53). The torn black notch with streaks is now a closed crease
   with a small dark slit (`review/sheet_armpit.png`, all tiers). Cost: Standing shoulders 5/3 -> 11/8, Walking 17/14 -> 23/19,
   Fidget 12/7 -> 18/16 (small, mostly hidden: exposed sums per clip within +-7 except Fidget2/Taunt +7). Shoulder pivots moved
   5 cm up / back / out were measured and not kept (no gain).
3. **Collapse, head.** `head_cap.py`: MM9's head rotation (swing and twist) soft-capped at 35/50 deg (Fidget 61 -> 49, Hit2 67 -> 50,
   Death2 69 -> 50 deg): **Death2 head 116 -> 93, Hit2 89 -> 41**, Fidget 49 -> 26, AttackMelee 53 -> 29, Hit 37 -> 39 (worst-frame faces).
   A deviation from MM9's motion: the head turns less far. Death2's remaining folds are the throat rolls under the R shoulder as the
   head drops onto it (`work/insp/d2h.png`).
4. **cbde5.** Not a texture fault: the close-up camera stood 10 cm from the left hand's fingertips (nearest vertices on Index3/Middle3/
   Ring3), so the finger filled the frame, magnified past the texel density. The Death left-forearm close-up now frames from 1.4 m.
5. **Script clips.** BackpedalRun L hand 5.8 cm -> **0** (0.25 s ramps; 0.4 s found no solution). **Death2 R stays 6.0 cm (7 frames)**:
   no solution with grids up to 80 deg upper arm / 60 deg wrist, nor with a window that holds the correction to the clip end
   (`HC_HOLD_END`, the hand lies in the chest until the corpse settles). Recorded as failed.
6. **Bulk** (`bulk.py`, measured, not kept): arms x1.12/x1.25 thicker sank the forearms into the belly (Walking R unclearable at 1.25);
   the head 7 cm lower into the shoulders raised Death2 head folds 93 -> 119 and Standing shoulders 11/8 -> 16/9. **Deviation:** ours stays
   a smaller toad-man with a visible throat and thinner arms than MM9's slab.

| Gate (r9) | Result |
|---|---|
| Bones / detached / flat / winding | 0 stretching / 0 / 0.00 / 0 |
| Floor | 3 ok |
| Regression | **PASS, 158 descriptors on 65 models, 0 failed** |
| Viewer check | 48 switches, 0 errors |
| Arm and hand | 0 frames over 1 cm in every clip except **Death2 R 6.0 cm (7 frames)** |
| Jitter | **FAILS: 5 clips strict** (AttackRanged R skin 10.8 mm/f2, Hit R 0.93 deg/f, Death L 0.96-1.26 deg/f and 7.3 mm/f2, Death2 L 0.72 deg/f, BackpedalRun L 2.2 mm/f2), **2 relative** (AttackRanged, Death). r4 had 3 / 1: the new BackpedalRun and Death2 L hand windows add two |
| Texture quality | unchanged: atlas 51.4 / 52.1 % |

## Route (`scripts/`)
0. `convert_abc_model.py --scale 0.0256` per skin (`source/t1-3`), `mirror_glb.py` (`source/true/`). Bind symmetric. `handedness.py`: raw R on the anatomical left; true and runtime right. `bone_length_audit.py`: 0 stretching (raw and runtime). The moving root is `Bip01` (MM9 keys it at floor height): `root_lift` Bip01 1.016.
1. Codex masters (`references_hd/CODEX_BRIEF.md`, tier B green, 00-04) from MM9 renders (`ref_renders.py`, `input_sheets.py`); head clay sculpt (`references_head/CODEX_BRIEF.md`, `00_geometry.png`).
2. `scripts/build_body.sh`: `fit_cw.py` (figure's right half mirrored, scaled to MM9's 2.014 m, trunk widened x1.15 to MM9's bulk, legs sheared 13 cm out to MM9's stance, arm segments onto MM9's bones), `head_prep.py` (head-only shell, loops capped, mirrored; Meshy's bead teeth and lid scraps dropped: the grin is painted on the closed lips), `head_fix.py` (centroid fans for the last holes; the eye pieces dropped: the almond recesses are the eyes, painted), `face_place.py` (head at S 0.8 so top and eye width match MM9, back half pressed into the hunch, 14k triangles, despiked; no voxel wrap: its 2.5 mm closure frayed the creases between the throat rolls), `union_cw.py` (old head and throat shrunk, Boolean union, seam relaxed off the face), `sculpt_fix.py` (Meshy's knee lumps and crotch spike smoothed; the star-shaped feet, with toes all round the ankle, pulled into MM9's forward fin: reach behind the ankle x0.28), `rig_cw.py` (bone heat, face rigid down to the chin), `step_b.sh` (MPFB hands 0.50 m, x1.30/1.40 thick, `graft_cw.json`), `quick.sh` (`weights_fix_cw.py`, `helpers_cw.py`, `reduce_cw.py` flat 6000 / joints 4000 / head 3800 / hands 2000), `q2.sh` (`sym_cw.py`, quick clips, collapse, bones).
3. `uv_cw.py` on `work/piv_v1.blend` -> `work/uv_v1.blend`, **never re-run** (the Meshy paint belongs to it); `texturing/cw_body_upload_v1.glb` (head faces on one point). Meshy retexture at 4K with the four masters.
4. `scripts/textures_all.sh`: `compose_cw.py` (2K colour once from 4K, normal 1K, ORM 1K with Meshy's roughness kept low), `grade_basecolor.py` (gentle), `project_head.py b` (Codex paint of tier B on our own head clay `references_head/b_*`, eyes, nose and mouth from the front view alone), `tier_ramps_cw.py`, `neck_rim_cw.py`.
5. `REV=rN scripts/rebuild.sh [--install]`: `export_cw.py`, `head_band.py`, `neck_shoulder_weights.py` (UpperArm helper mix, smoothed), `head_pivot.py` (+14 cm), `clips_mm9.py` (soft joint-offset line), `half_keys.py`, `clip_fix.sh` (`hand_clear_keys.py`, then a second pass with a larger grid for AttackRanged R), LODs, shadow fix, `region_variants.py`, `floor_fix.py`, winding, install, viewer.
6. Binding `scripts/bind_actors.py 1.30 2.6` under the flock, then the table generator under the flock (rows 9234-9236 unchanged). Gates `scripts/gates.sh`; sheets `strips.py`, `strip_sheets.sh`, `closeups.sh`, `cmp_sheet.py`; in game `scripts/ingame_tour.yml`.

## Tiers (one shared set + region mask + ramps)
Body: R slime (1 everywhere, gutters included), G arms and hands. Head: R slime (fitted to MM9's torso samples, so head and body draw the same tone), G eyes (B orange as painted; A and C red, as MM9's), B mouth gap and teeth (kept as painted on every tier), A the rim where the head set meets the body (takes the body's grain and colour; 0.5-0.7 of 255 off the body per tier). Ramps by histogram match to MM9's skin read at the same body position (MM9's face texels excluded). Tier A at 0.85 of MM9's value: at 1.0 it read pale pink in game. Compared with MM9 tier by tier in `review/mm9_vs_ours_tiers.png`: A tan-brown mud, B yellow-olive slime with dark moss blotches, C rust. MM9 renders there are darker (Blender light); the skins themselves are as light as ours.

## Checks (r4; superseded where the second pass says so)
| Gate | Result |
|---|---|
| Handedness | raw R on the anatomical left; source and runtime right |
| Bones (`bone_length_audit.py`) | 12 checked, 0 stretching (raw and runtime) |
| `detached_parts_audit.py` | 1 component, 0 detached |
| `flat_shading_check.py` | body 0.00, head 0.00 |
| `check_winding.py` | 0 inverted closed parts |
| `texture_quality.py` | body atlas **51.4 %** (target 55), spread 1.09, fragments 0.1 %, stretch p90 1.15; head atlas **52.1 %**, spread 1.79 (face denser by design), stretch 1.10 |
| `floor_audit.py --world mm9` | 3 bindings ok (stand 0, walk 0, living 0, dead 0) |
| Regression `mm9_actor_models_build_every_binding` (`--world mm9`) | **PASS, 155 descriptors on 63 models, 0 failed** (after the last install) |
| `run_creature_review.py check` | 48 switches (3 tiers x 16 clips), 0 failed, 0 console errors |
| Faces | `review/sheet_heads.png` (front, quarter, side per tier, read at full size): one pair of slit eyes, one beak nose, one grin with one row of teeth per jaw, per tier |

**Arm and hand (`review/gates/arm_hand_skin.txt`, skin, outer faces, exact, 48 fps):** 0 frames over 1 cm in every bound clip. Worst
under 1 cm: Running L 0.9, Walking L forearm 0.8, Death L forearm 0.9, AttackRanged R 0.6 cm. **Fails in two script clips:** Death2 R hand
6.0 cm (7 frames, forearm 5.8; capped, MM9 throws the right hand into the chest as it falls), BackpedalRun L hand 5.8 cm (5 frames).
`hand_clear_keys.py` found no solution for either, also with the larger grid (48 deg upper arm, 60 deg wrist). Wrist max 98 deg
(AttackMelee R, MM9's own punch). Before the corrections: Walking L 6.0 cm (9 frames), AttackRanged R 15 cm+ (the hand scooping slime
went into the chest; now it lies on the belly), Hit R 7.8, Death L 11.8, Backpedal L 6.2, AttackMelee2 L 5.3.

**Jitter (`review/gates/jitter*.txt`, against MM9's clips with the same helpers and weights). FAILS as defined: 3 clips strict, 1 relative.**
Strict: AttackRanged R shoulder skin 9.6 mm/f2 over MM9 (the 20 deg upper-arm / 50 deg wrist window that lifts the hand out of the chest:
it starts 0.25 s into the clip, so the in-ramp cannot be longer), Hit R upper arm and forearm 0.93 deg/f (9 deg window), Death L upper
arm 0.63, forearm 0.91 deg/f, skin 5.4 mm/f2 (12 deg window from 0.15 s). Relative (`--rel 0.25`): AttackRanged only. All other clips 0.

**Collapse (r9, `review/gates/collapse.txt`, all LOD0 primitives, 30 fps). Not zero.** face-frames per clip; worst frame per region; how many of
the worst frame's faces a camera can see:

| Clip | face-frames | worst frame | exposed |
|---|---|---|---|
| Standing | 2596 | hip_L=5 hip_R=1 ankle_L=1 ankle_R=1 toe_L=1 toe_R=1 shoulder_L=11 shoulder_R=8 torso=1 head=10 finger=5 | hip_L=5 hip_R=1 ankle_L=1 ankle_R=1 toe_L=1 toe_R=1 shoulder_L=3 torso=1 head=9 finger=4 |
| Walking | 2026 | hip_L=9 hip_R=7 ankle_L=2 ankle_R=3 toe_L=2 toe_R=5 shoulder_L=23 shoulder_R=19 groin=5 torso=1 head=8 finger=7 | hip_L=9 hip_R=7 ankle_L=2 ankle_R=3 toe_L=1 toe_R=5 shoulder_L=6 groin=4 torso=1 head=6 finger=4 |
| Running | 1876 | knee_R=37 hip_L=6 hip_R=30 ankle_L=52 ankle_R=55 toe_L=2 toe_R=4 shoulder_L=11 shoulder_R=22 groin=5 torso=3 head=15 finger=7 | hip_L=3 hip_R=9 ankle_L=20 ankle_R=2 toe_R=3 shoulder_R=5 groin=3 head=2 finger=5 |
| Fidget | 5735 | hip_L=12 hip_R=4 ankle_L=1 ankle_R=2 toe_L=1 toe_R=2 shoulder_L=18 shoulder_R=16 torso=2 head=26 finger=5 | hip_L=7 hip_R=1 ankle_L=1 ankle_R=2 toe_R=2 shoulder_L=6 shoulder_R=3 torso=2 head=24 finger=4 |
| Fidget2 | 3382 | hip_L=6 hip_R=1 ankle_L=3 ankle_R=2 toe_L=1 toe_R=1 shoulder_L=19 shoulder_R=29 groin=2 torso=2 head=43 finger=5 | hip_L=3 hip_R=1 ankle_L=2 ankle_R=2 toe_R=1 shoulder_L=4 shoulder_R=7 groin=2 torso=1 head=31 finger=4 |
| Taunt | 1809 | hip_L=6 hip_R=1 ankle_L=3 ankle_R=2 toe_L=1 toe_R=1 shoulder_L=19 shoulder_R=29 groin=2 torso=2 head=43 finger=5 | hip_L=3 ankle_L=3 ankle_R=2 toe_R=1 shoulder_L=6 shoulder_R=7 groin=2 torso=1 head=29 finger=4 |
| AttackMelee | 1901 | hip_L=6 hip_R=11 ankle_L=3 ankle_R=2 toe_L=3 toe_R=2 elbow_R=1 shoulder_L=13 shoulder_R=55 wrist_R=4 groin=5 torso=2 head=29 finger=5 | hip_R=3 ankle_L=2 ankle_R=2 toe_L=3 toe_R=1 elbow_R=1 shoulder_L=3 shoulder_R=50 wrist_R=1 groin=1 torso=2 head=22 finger=2 |
| AttackMelee2 | 2582 | hip_L=23 hip_R=14 ankle_L=1 ankle_R=2 toe_L=1 toe_R=2 elbow_R=1 shoulder_L=43 shoulder_R=54 wrist_R=1 groin=3 torso=1 head=55 finger=5 | hip_L=21 hip_R=11 ankle_L=1 ankle_R=2 toe_R=2 elbow_R=1 shoulder_L=26 shoulder_R=22 wrist_R=1 groin=1 torso=1 head=40 |
| AttackRanged | 3673 | hip_L=14 hip_R=9 ankle_L=9 ankle_R=2 toe_L=2 toe_R=2 elbow_R=2 shoulder_L=12 shoulder_R=39 wrist_R=11 groin=5 torso=5 head=17 finger=20 | hip_L=2 hip_R=1 ankle_L=4 ankle_R=2 toe_L=2 toe_R=1 shoulder_R=26 wrist_R=7 groin=2 head=5 finger=16 |
| Hit | 2769 | hip_L=25 hip_R=6 ankle_L=2 ankle_R=2 toe_L=2 toe_R=1 elbow_L=1 shoulder_L=26 shoulder_R=27 wrist_L=1 groin=6 torso=2 head=39 finger=5 | hip_L=8 hip_R=3 ankle_L=2 ankle_R=2 toe_L=2 toe_R=1 shoulder_L=8 shoulder_R=2 wrist_L=1 groin=4 head=25 |
| Hit2 | 2410 | knee_R=4 hip_L=10 hip_R=3 ankle_L=1 ankle_R=7 toe_L=2 toe_R=3 shoulder_L=31 shoulder_R=39 torso=2 head=41 finger=5 | hip_L=1 hip_R=3 ankle_R=3 toe_L=2 toe_R=3 shoulder_L=1 shoulder_R=5 head=38 |
| Death | 7759 | knee_R=46 hip_L=20 hip_R=34 ankle_L=110 ankle_R=5 toe_L=2 toe_R=3 elbow_R=1 shoulder_L=17 shoulder_R=46 wrist_R=8 groin=5 torso=3 head=28 finger=7 | hip_L=1 hip_R=13 ankle_L=58 ankle_R=3 toe_L=2 toe_R=3 elbow_R=1 shoulder_L=3 shoulder_R=25 wrist_R=7 groin=3 torso=1 head=11 finger=5 |
| Death2 | 9061 | knee_R=7 hip_L=23 hip_R=19 ankle_L=107 ankle_R=70 toe_L=2 toe_R=3 shoulder_L=52 shoulder_R=48 groin=7 torso=2 head=93 finger=5 | hip_L=15 hip_R=14 ankle_L=25 ankle_R=2 toe_L=2 toe_R=2 shoulder_L=36 shoulder_R=3 groin=5 torso=2 head=40 finger=4 |
| Backpedal | 1933 | hip_L=9 hip_R=8 ankle_L=2 ankle_R=3 toe_L=2 toe_R=5 shoulder_L=20 shoulder_R=19 groin=4 torso=1 head=7 finger=7 | hip_L=9 hip_R=6 ankle_L=2 ankle_R=3 toe_L=1 toe_R=3 shoulder_L=7 groin=4 torso=1 head=6 finger=4 |
| BackpedalRun | 1320 | hip_L=9 hip_R=8 ankle_L=2 ankle_R=3 toe_L=2 toe_R=5 shoulder_L=20 shoulder_R=19 groin=4 torso=1 head=7 finger=7 | hip_L=9 hip_R=6 ankle_L=2 ankle_R=3 toe_L=1 toe_R=4 shoulder_L=8 groin=4 torso=1 head=5 finger=4 |
| Dead | 7440 | knee_R=43 hip_R=21 ankle_L=110 ankle_R=2 toe_L=2 toe_R=3 shoulder_L=5 shoulder_R=38 wrist_R=4 groin=2 head=3 finger=7 | hip_R=21 ankle_L=63 ankle_R=2 toe_L=2 toe_R=3 shoulder_R=30 wrist_R=4 groin=2 head=1 finger=7 |

Worked on the first rig and after, each measured alone (numbers: head / shoulder faces at the worst frame):
- head band (`head_band.py`): MM9 turns this neckless head 30 deg in its idle and up to 69 deg (mostly a twist about the spine). The rig's
  9 cm band: Fidget head 109, Hit2 173, Death2 219. A narrow band (|x| 0.18-0.30) doubled them (Fidget 209). A tall wide band (|x| 0.40-0.70)
  halved them (Fidget 15) but webbed the hood to a raised arm (AttackRanged); kept |x| 0.30-0.48 over hh -0.35..0.08 (Fidget 102).
- armpit (`neck_shoulder_weights.py`, UpperArm through its helper, smoothed 3 rings 8 passes): AttackMelee R shoulder 73 -> 63, Death2 70 -> 55.
  The bigfoot FLANK rule (armpit wall to Spine2/Spine3) was tried at two sizes: AttackMelee R 57/50 but Standing, Fidget, Hit and Backpedal
  shoulders rose; not kept.
- head pivot (`head_pivot.py`): back 8 cm worse (Fidget 139); forward 8 / 14 / 20 cm: Fidget 72 / 49 / 49, Hit2 57 / 89 / 134, Death2 156 / 116 / 82;
  14 cm kept (a deviation: the face turns about a point nearer itself, the back of the dome swings more).
Remaining, seen in close-ups: the front armpit in AttackMelee as the right arm crosses the chest (`review/sheet_closeups_b.png` cbcr3,
a dark notch); the throat rolls when the head is thrown back (Fidget, Death2); the ankle folds of the flipper feet in Death and Dead
(ankle_L 110, mostly hidden under the corpse: 58 seen); the knee in Running and Death.

**Hood stretch (measured, not a gate):** the head's 30 deg idle twist stretches the hood skin: Standing edge stretch p90 1.28, p99 1.67,
max 4.1; Fidget p90 1.64, max 7.7; Walking p90 1.07. It shows as brushed streaks on the trapezius in the viewer at Standing.

Sheets (viewer): `review/mm9_vs_ours_tiers.png`, `review/sheet_heads.png`, `review/sheet_tex.png`, `review/sheet_closeups_{a,b,c}.png`
(knees, groin, armpits, elbow, neck, mouth in the AttackMelee crouch, Death and Dead), `review/sheet_strips_{a,b,c}_{1,2,3}.png` (all 16
clips, six frames each), `review/sheet_lods.png` (LOD0-3, clay), `review/ingame_sheet.png`. Numbers `review/gates/`.
Viewer: http://127.0.0.1:8912/level_generation/creatures/mm9_colloidalwarrior_claude/review/viewer/

## In game
`isleofashes.odm` (open grass at -12000, 0; bootcamp's canyon is too narrow), review root, isolated (`scripts/ingame_tour.yml`): all three
rows spawn friendly, then a Warrior and a Guardian hostile; they walk, fight and throw (the party dies after about 8 s and the tour ends on
the game-over screen). `review/ingame/f03_hostile.png` is the full-body frame (the Warrior walking, the Soldier from behind on the slope);
f05/f06 the Guardian and a Warrior's reaching hand. At 1.5-2.0 x scale they stand 3-4 m tall, as MM9's.

## Decisions and deviations
- **Opaque, glossy:** MM9's skins are opaque; the gel look is roughness and specular. No blended material.
- **Width:** the master's body was narrower than MM9's blob: trunk x1.15 between the knees and the head, legs 13 cm wider apart, arms MM9's length.
- **Head:** head-only Meshy model from a Codex clay sculpt, unioned; Meshy's bead teeth and eyeballs dropped; eyes and teeth painted
  (one paint source per feature) on the shell's almond recesses and closed lips.
- **Feet:** Meshy gave toes all round the ankle; the ones behind it are pulled into a short heel (`sculpt_fix.py`), MM9's fin points forward.
- **Head pivot +14 cm forward** and the head band, above. MM9's head twist itself is kept (no cap).
- **AttackRanged R:** the hand scooping slime from the belly lies on the belly instead of 15 cm inside it (20 deg upper arm, 50 deg wrist window).
- **Sizes:** 150/175/200 world units per model metre, so 3.0 / 3.5 / 4.0 m: MONSTERS Scale 1.5/1.75/2.
- **Run stride 2.6** is an estimate: in MM9's run a foot is planted only 2-7 % of the cycle, so `stride.py` cannot measure it (walk: 1.23-1.37 m measured).
- **Not carried:** MM9 `ColloidalWarrior -> Shockwave` model swap (a script event), `lunge` and `Velocity`-type events, the COLLOIDALGOO prop (no goo blob is held; the projectile leaves the right hand).

## Open points
- Jitter (3 strict, 1 relative) and collapse above; Death2 R and BackpedalRun L hands in the body (script clips).
- LOD2/LOD3 from `build_actor_lods.py` defaults: LOD3 (749) shows shards at the throat rolls and spiky fingers in `review/sheet_lods.png`.
  `level_generation/creatures/lod_repair_claude/scripts/repair.py mm9_colloidalwarrior` would rebuild them; not run (it writes into that project).
- UV atlas 51-52 % against the 55 % target (bigfoot 53.9 / 49.8 was kept).
- Upper back: the Meshy paint has a small navel-like dimple between the shoulder blades (`review/sheet_tex.png`, back).

## Not checked
- Playback at normal speed of r9 (none recorded for r9; `review/playback/` is r4). Corrections read in stills only.
- r9 sheets read: `sheet_heads.png`, `sheet_armpit.png`, `sheet_closeups_b.png`, `sheet_strips_a_2`, `_b_3`, `_c_1`, `tone_cmp.png`,
  `ingame_sheet.png`. Not read: the other strip sheets, closeups A and C, `sheet_tex.png`, `mm9_vs_ours_tiers.png` of r9.
- LOD1-3 in game, LOD2/3 not repaired (lod_repair_claude not run), maps that place these rows, indoor light, night, sounds, melee
  contact, ranged release, Android. Orientation gate not run.

User artistic acceptance: not recorded


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_colloidalwarrior_reduce_claude/`** (user-approved; ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `mm9_colloidalwarrior_reduce_claude/before/`.
