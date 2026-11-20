# MM9 Bigfoot body (mm9_bigfoot) — 3D actor, 2026-10-31

MM9 `BIGFOOT.abc` (28 nodes, 19 clips, 764 triangles, no child model: ChildModels count 1): rows 198 Bigfoot L18 (`MM9 Bigfoot A`, BIGFOOT1), 199 Sasquatch L28 (`B`, BIGFOOT2), 200 Yeti L38 (`C`, BIGFOOT3).
**Humanoid route** (MM9 skeleton, MM9 clips, grafted five-finger hands, head-only Meshy model): a biped with arms and a face. Built under the orchestrator's short-budget order at 91 % of the weekly limit (r6, accepted "bigfoot - ok"); **r7 (run 2, 2026-10-31)** cleared the hands on keys, added MM9's five dropped clips, softened the Sasquatch back panel and the Yeti chest, and reran every gate. **r9 (follow-up, same day)** worked the collapse gate (neck and armpit weights, head pivot, head twist cap) and the neck rim texture (pale collar patches, reddish band).

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_bigfoot.glb` (`tools/install_model.py --world mm9`), variants `bf_a/b/c` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, `MM9 Bigfoot A/B/C`, scale 100 (MONSTERS Scale 1), `yaw_offset` -1.570796327, stride walk 1.56 / run 2.99 (planted foot), melee impact 0.456 s (`Lattack`), ranged 0.566 s released at `cast_hand` = `Bip01 R Hand` (MM9's RangeAttack), look `Bip01 Head`, upper body `Bip01 Spine2` |
| Triangles LOD0/1/2/3 | 9,442 / 4,720 / 1,698 / 565 |
| Skeleton | MM9's 27 joints, rest rotations unchanged, joints translated, + 15 half-rotation helpers + 30 finger bones |
| Clips (30 fps) | All 18 of BIGFOOT.abc's clips (bind pose `static_model` excepted) + Dead. Bound: Standing, Walking, Running, Fidget, AttackMelee `Hattack1`, AttackRanged `Rattack1`, Hit `wince1`, Death `die1`, Dead. `script_clips`: attack2 AttackMelee2 `Hattack2`, fidget2, hit2, taunt, death2, and since r7 walk_fidget `walkfidget`, backpedal, backpedal_run, jumping_down `JumpingDown` (arms raised, MM9's own), lying_down `LyingDown` (lies on its side; MM9 keeps the pelvis at standing height, ours is grounded by `floor_fix.py --ground-loop`). None left out. `walkfidget` turns the head 118 deg |
| Textures | body 2K colour + 1K normal + ORM + mask; head 2K colour + 1K normal + flat ORM + mask; Yeti head 1536 colour (own image, **deviation**: open snarl and blue bands are a design difference; shares A's normal). 9 images |
| Meshy credits | **20 / 40**: body Smart Topology 5, head-only 5, body retexture 10. Run 2: 0 |

## Route (`scripts/`)
0. `convert_abc_model.py --scale 0.0256` in raw ABC space, `mirror_glb.py` (`source/true/`). Bind symmetric (bones 4.5 mm off centre, mesh not): no `mirror_source.py`. `bone_length_audit.py`: 0 stretching on the raw clips and on the GLB, so MM9's own clips slide no limb joint.
1. Masters (Codex, tier A), head clay sculpt.
2. `wrap_all.sh`: `head_prep.py`, `fit_bf.py` (left half mirrored; arms to MM9's bones, legs sheared, feet translated, soles flat), `face_npz.py` + `wrap_bf.py` + `head_close.py` (head shell closed at 2 mm), `union_bf.py` (Boolean union, seam relaxed). **Deviation from the Gezzampt:** its whole-figure voxel wrap erased eyes and lips at 3-4 mm, so only the head is closed and the body keeps Meshy's surface.
3. `rig_bf.py`, `step_b.sh` (posed MPFB hands, widened 1.42 x and thickened 1.5 x, 15 finger bones, MM9's `Finger1` curl through `finger_alias`), `quick.sh`, `sym_bf.py` (exact left-right symmetry after the reduction), `q2.sh`.
4. `uv_bf.py`, never re-run: the paint belongs to `work/uv_v1.blend`. Retexture at 4K, downsampled once.
5. Head: `head_clay.py`, Codex paints five views per tier A and C on our clay, `project_head.py`: eyes, nose and mouth from the front view alone, `eyes.py` paints the eyeballs. Tiers: `tier_ramps.py` (histogram match to MM9's skin read at the same body position; fur from limbs, since Sasquatch's torso panel is speckled). `tier_head_c.py`.
6. `textures_all.sh`, then `REV=<rev> scripts/rebuild.sh --install`, `bind_actors.py` under the flock.
7. Run 2: `rebuild.sh` first runs `neck_shoulder_weights.py` (throat clavicle weight to Spine3, armpit wall to the spine, Head/Head_h split) and `head_pivot.py` (head pivot 8 cm forward) on `work/bf_body.glb`, then builds the clips as `clips_mm9.py` -> `head_twist_cap.py` (50/75 deg) (soft offset line; per-role `ease_out`) -> `arm_out.py` 12 deg -> `half_keys.py` -> `hand_clear_keys.py` (about 10 min, 12 processes) -> `half_keys.py`; `SKIP_CLIPS=1` reuses `work/bf_final_clips.glb` for texture-only rebuilds. Body masks only: `BODY_ONLY=1 PYTHONPATH=scripts tier_ramps.py` (keeps the head ramps that `seam_fix.py` graded against). Neck rim: `PYTHONPATH=scripts neck_rim.py` (last step of `textures_all.sh`; reads its inputs from `work/neck_rim_in/`), and for a texture-only rebuild `swap_image.py work/bf_final_clips.glb BigfootHead textures/bf_head_final.png` before `SKIP_EXPORT=1 SKIP_CLIPS=1 rebuild.sh`. `bind_extra_clips.py` added the five script clips. Gates: `scripts/gates.sh`.

## Checks (r9, final build; r7 in `work/README_r7.md`, r6 in `work/README_r6.md`)
| Gate | Result |
|---|---|
| Handedness | raw ABC: R on the anatomical left; source and runtime: right |
| Bones (`bone_length_audit.py`) | 12 checked, 0 stretching |
| `detached_parts_audit.py` | 3 components, 0 detached (all 19 clips) |
| `flat_shading_check.py` | 0.00 |
| `check_winding.py` | 0 inverted closed parts |
| `texture_quality.py` | unchanged: body atlas **53.9 %** (target 55), spread 1.19; head atlas **49.8 %**, spread 1.77 |
| `floor_audit.py --world mm9 --match 'MM9 Bigfoot*'` | 3 ok: stand 0, walk 0, living 0, dead 0. Script clips measured apart: lowest point 0.0 to -0.003 m in WalkFidget, Backpedal, BackpedalRun, JumpingDown, LyingDown (were -0.13, -0.10, -0.10, -0.20 and +0.70 before `floor_ops.txt` took them) |
| Regression `mm9_actor_models_build_every_binding` | PASS, 147 descriptors on 58 models, 0 failed, on the final install (r9). The whole `actors` suite: 191 passed, 2 failed, neither involving Bigfoot: `mm6_ogr_actor_models_bind_all_tiers` (Ogre Hit blend) and `out05_event_clearance_completes_from_monster_killed_hook` (could not load gameplay data) |
| `run_creature_review.py check` | 57 switched (3 tiers x 19 clips), 0 failed, 0 console errors |
| Faces | faces unchanged; the neck rim below them changed in r9 (`review/sheet_tier_heads_r9.png`, `review/sheet_neck_r9.png`, read at full size): one pair of eyes, one nose, one mouth per tier |
| In game (`bootcamp.odm`, review root, r9 final) | `review/ingame_sheet_r9.png`: three tiers friendly then hostile, walk, overhead smash and fight (the pink and yellow creature near the camera in f01 is another map actor) |

**Arm and hand (PASSES, `review/gates/arm_hand_skin.txt`, skin, outer faces, exact):** 0 frames over 1 cm in all 19 clips. Worst: AttackMelee2/AttackRanged R 0.8 cm, Hit2 R 0.5, Fidget2 L 0.5 / R 0.6, AttackMelee L 0.5, Death2 R 0.5 cm. r6: Fidget2 L 6.0 cm 59 f, Taunt 6.0/5.9, attacks up to 6.0, Hit2 R 6.0, Death2 R 5.9 (all capped at 6 cm; true depth to 15 cm). Wrist max 58.9 deg (AttackMelee, MM9's own), Taunt R 44.8.
How (`scripts/hand_clear_keys.py`, report `work/hand_clear.json`): per contact episode one raised-cosine window (ramps 0.25-0.4 s, zero at both clip ends, flat over the contact), two constant axes chosen at the deepest frame so the deepest point moves along the entered face's mean normal (or out to the side, or between), upper arm and wrist amplitudes from a grid, least added upper-arm speed first. Nothing is smoothed afterwards, so nothing puts a hand back. 11 windows: Fidget R (upper arm 3 deg), Fidget2 L (9 + wrist 35) and R (wrist 5), Taunt L and R (wrist 35 each: the palms lie flat on the chest in the beats), AttackMelee L (6 + 20) and R (3 + 5), AttackMelee2/AttackRanged L (wrist 15), Hit2 R (6 + 35), Death2 R (9 + 30). AttackMelee2 and AttackRanged (same MM9 keys) ease back to the stance over 0.5 s instead of 0.2 s (`ease_out` in `roles_bf.json`, from 0.53 s; at the 0.566 s impact the blend is 1 %): with 0.2 s both hands crossed into the thighs during the return and no window under the jitter cap could clear them. Close-ups of every corrected moment: `review/sheet_hands_r7.png`.

**Jitter (`review/gates/jitter*.txt`, 48 fps). FAILS as defined: 22 flags in 12 clips.** The reference is now MM9's clips with the same half-joint helpers (`work/bf_ref_clips.glb`); r6 compared with clips whose helpers stayed at rest (19 flags in 14 clips, same causes). Three readings:
- strict (the gate as written): 22 flags. All but one are the r6 constant 12 deg abduction (`arm_out.py`, kept: the accepted look, and Standing has hands 6 cm in the thighs without it). A rotation fixed in the clavicle's frame turns MM9's fast frames by a few per cent more: e.g. Death2 L upper arm 20.8 against MM9's 18.4 deg/f where MM9 jumps 1.2 -> 4.4 -> 18.4 deg/f by itself. Worst: Death2 upper arm 3.4-3.5 deg/f, shoulder skin 19.6 mm/f2 (on MM9's 226), Death 2.0 deg/f, 10 mm/f2. Applying the abduction in the upper arm's own frame instead gave 0 upper-arm excess but 2.8-3.4 deg/f forearm excess and a 15 mm/f2 shoulder spike in Taunt, so it was not used.
- relative (`--rel 0.25`, an excess counts only above a quarter of MM9's value at that frame): 9 flags in AttackMelee R, AttackMelee2/AttackRanged L, Hit2, Death, Death2.
- the hand corrections alone, against the abducted clips they start from (`jitter_corrections.txt`): **1 flag**, Death2 R: upper arm +1.71 deg/f, forearm +1.08, shoulder skin +6.2 mm/f2. Its contact starts 0.06 s into the clip, so the window's ramp cannot be longer; splitting the contact into three windows left the first unsolvable. Death2 is a script clip. r9 (new armpit weights): the same 22 / 9 / 1 flags; Death2 R's shoulder skin excess is now 12.1 mm/f2 (the wall it measures now follows the spine).

**Collapse (r9, `review/gates/collapse.txt`, all LOD0 primitives, 30 fps). Not zero; worked in the follow-up.** What the counts measured, read face by face (`scripts/collapse_where.py`, `work/cdiag.py`): head 44 in WalkFidget were the jaw rim and neck side, weighted Head 0.7 + R Clavicle/UpperArm_h 0.3, folding into the shoulder under MM9's 96 deg head twist (the head joint sits 5 cm above the clavicles; no neck bone); Hit2 and AttackMelee2 the same rim plus the throat, which mixed Head with both clavicles; shoulder 24 in AttackMelee was the torso's side wall under the armpit (x 0.33-0.36 m, chest height) carrying UpperArm weight, dragged up with the arm overhead. Real skin folds, not fur-shell or brow faces. The gait counts (finger 21, wrist 10-12) are knuckle and wrist-crease faces of 1.6 cm2 median under MM9's 45-50 deg finger curl, 3-6 seen. Fixes, each measured alone first:
- head twist soft cap (`head_twist_cap.py`, unchanged below 50 deg, never above 75; swing kept): WalkFidget 96 -> 74 deg, Hit2 79 -> 71, AttackMelee2 72 -> 68; WalkFidget head 44 -> 26. A deviation from MM9's motion (it looks less far round), recorded here.
- head pivot 8 cm forward (`head_pivot.py`, at the jaw's side of the bend): WalkFidget head 26 -> 13, Death 36 -> 17, Hit 16 -> 1, Fidget 6 -> 1. 6 cm back, 6 cm up and mixed offsets measured worse.
- throat (`THROAT` in `neck_shoulder_weights.py`): the neck's clavicle weight within 8-18 cm of the midline goes to Spine3, then Head/Head_h split as `helpers_bf.py` does: Hit2 23 -> 19 head.
- armpit wall (`FLANK`): its UpperArm weight to Spine1/Spine2 by height, fading out by the armpit, the arm and the front fold: AttackMelee shoulder 24/12 -> 14/11, Death2 13/10 -> 5/6. A wider wall put folds into Standing and Fidget; kept off the front fold.
- tried and dropped: the coordinator's half-joint helper split with clavicles as Head_h parents, and Laplacian weight smoothing over the neck band: both raised the counts (WalkFidget head 47, Death 45-54).

| Clip | face-frames r7 -> r9 | worst frame r7 | worst frame r9 | exposed r9 |
|---|---|---|---|---|
| Standing | 0 -> 0 | 0 | 0 | 0 |
| Walking | 891 -> 889 | hip_L 3 hip_R 3 wrist_L 10 wrist_R 12 torso 1 finger 21 | hip_L 3 hip_R 3 shoulder_L 1 shoulder_R 1 wrist_L 10 wrist_R 12 torso 1 finger 21 | hip_L 2 shoulder_R 1 wrist_L 3 wrist_R 5 finger 6 |
| Running | 782 -> 792 | knee_L 7 knee_R 4 hip_L 5 hip_R 3 ankle_L 2 ankle_R 2 shoulder_L 1 shoulder_R 1 wrist_L 10 wrist_R 12 torso 1 finger 21 | knee_L 7 knee_R 4 hip_L 5 hip_R 3 ankle_L 2 ankle_R 2 shoulder_L 2 shoulder_R 2 wrist_L 10 wrist_R 12 torso 1 finger 21 | knee_L 5 hip_L 4 hip_R 1 ankle_L 2 wrist_L 3 wrist_R 3 finger 5 |
| Fidget | 366 -> 416 | hip_R 1 shoulder_R 6 torso 1 head 6 | hip_R 1 shoulder_R 7 torso 1 head 1 | shoulder_R 6 torso 1 |
| Fidget2 | 93 -> 73 | hip_R 1 shoulder_L 1 head 1 | hip_R 1 head 1 | hip_R 1 head 1 |
| Taunt | 33 -> 29 | ankle_R 2 shoulder_L 1 torso 1 | ankle_R 2 shoulder_L 1 torso 1 | ankle_R 2 shoulder_L 1 torso 1 |
| AttackMelee | 441 -> 370 | hip_L 4 hip_R 4 ankle_R 4 elbow_R 1 shoulder_L 24 shoulder_R 12 wrist_L 3 wrist_R 3 groin 3 torso 5 | hip_L 4 hip_R 4 ankle_R 4 elbow_R 1 shoulder_L 14 shoulder_R 11 wrist_L 3 wrist_R 3 groin 3 torso 9 | hip_R 3 ankle_R 3 elbow_R 1 shoulder_L 10 shoulder_R 10 wrist_L 3 wrist_R 2 torso 1 |
| AttackMelee2 | 362 -> 228 | hip_L 2 hip_R 2 ankle_L 2 ankle_R 7 shoulder_L 4 shoulder_R 7 groin 2 torso 3 head 25 | hip_L 2 hip_R 2 ankle_L 2 ankle_R 7 shoulder_L 4 shoulder_R 3 groin 2 torso 5 head 20 | hip_L 2 hip_R 2 ankle_L 2 ankle_R 3 groin 2 torso 1 head 14 |
| AttackRanged | 362 -> 228 | hip_L 2 hip_R 2 ankle_L 2 ankle_R 7 shoulder_L 4 shoulder_R 7 groin 2 torso 3 head 25 | hip_L 2 hip_R 2 ankle_L 2 ankle_R 7 shoulder_L 4 shoulder_R 3 groin 2 torso 5 head 20 | hip_L 2 hip_R 2 ankle_L 2 ankle_R 3 groin 2 torso 1 head 14 |
| Hit | 99 -> 122 | ankle_L 2 ankle_R 2 shoulder_L 1 torso 1 head 16 | ankle_L 2 ankle_R 2 shoulder_R 4 torso 1 head 2 | ankle_L 2 ankle_R 2 shoulder_R 4 torso 1 head 2 |
| Hit2 | 510 -> 401 | hip_R 3 ankle_R 1 shoulder_L 3 shoulder_R 5 torso 5 head 42 | hip_R 3 ankle_R 1 shoulder_L 1 shoulder_R 8 torso 3 head 21 | hip_R 3 ankle_R 1 shoulder_L 1 torso 1 head 10 |
| Death | 345 -> 202 | hip_L 6 hip_R 7 ankle_R 6 shoulder_L 2 torso 1 head 36 | hip_L 6 hip_R 7 ankle_R 6 torso 1 head 19 | hip_L 6 hip_R 1 head 11 |
| Death2 | 481 -> 329 | knee_L 3 hip_L 7 hip_R 6 ankle_L 14 ankle_R 6 shoulder_L 13 shoulder_R 10 torso 2 head 15 | knee_L 3 hip_L 5 hip_R 6 ankle_L 14 ankle_R 6 shoulder_L 5 shoulder_R 6 torso 4 head 1 | knee_L 1 hip_L 2 hip_R 4 ankle_L 5 ankle_R 5 shoulder_L 3 shoulder_R 1 |
| WalkFidget | 2932 -> 2104 | hip_L 3 hip_R 3 shoulder_R 5 wrist_L 10 wrist_R 12 torso 2 head 44 finger 21 | hip_L 3 hip_R 3 shoulder_R 2 wrist_L 10 wrist_R 12 torso 2 head 11 finger 21 | hip_L 2 shoulder_R 2 wrist_L 3 wrist_R 5 torso 1 head 9 finger 6 |
| Backpedal | 1083 -> 1079 | hip_L 3 hip_R 3 wrist_L 10 wrist_R 12 torso 1 finger 21 | hip_L 3 hip_R 3 shoulder_L 1 shoulder_R 2 wrist_L 10 wrist_R 12 torso 1 finger 21 | hip_L 2 shoulder_R 2 wrist_L 3 wrist_R 5 finger 7 |
| BackpedalRun | 794 -> 792 | hip_L 3 hip_R 3 wrist_L 10 wrist_R 12 torso 1 finger 21 | hip_L 3 hip_R 3 shoulder_L 1 shoulder_R 2 wrist_L 10 wrist_R 12 torso 1 finger 21 | hip_L 2 shoulder_R 2 wrist_L 3 wrist_R 5 finger 6 |
| JumpingDown | 551 -> 425 | shoulder_L 5 shoulder_R 10 torso 4 | shoulder_L 3 shoulder_R 13 torso 3 | shoulder_L 3 shoulder_R 13 torso 3 |
| LyingDown | 0 -> 61 | 0 | shoulder_R 1 | shoulder_R 1 |
| Dead | 0 -> 0 | 0 | 0 | 0 |

Visible at the worst frames (`review/sheet_collapse_r7_r9.png`, r7 left of r9, full size): in WalkFidget the jaw no longer sinks into the right shoulder and the diagonal crease across the chest is gone; AttackMelee's armpit fold sits under the raised arm in both. Remaining: the jaw rim and throat where MM9 presses the chin into the chest (AttackMelee2 0.6 s, head 20, 14 seen) or turns the head into the shoulder (Hit2, 21, 10 seen); the nape with the head thrown back in Death (19, 11 seen); JumpingDown's raised R shoulder (13); the gait knuckles.

Sheets (r9, viewer): `review/mm9_vs_ours_tiers.png`, `review/sheet_tier_heads_r9.png`, `review/sheet_neck_r9.png` (throat, neck side and nape per tier), `review/sheet_collapse_r7_r9.png`, `review/sheet_hands_r7.png` (every corrected contact), `review/sheet_closeups_a.png`, `_b`, `_c` (knees, groin, armpits, elbow, neck, mouth in crouch `AttackMelee`, `Death`, `Dead`), `review/sheet_strips_{a,b,c}_{1,2,3}.png` (all 19 clips, six frames each), `review/ingame_sheet_r9.png`. Before/after texture shots `review/r7pre/`, `review/neck_r8/` (pale patches before the rim fix). Numbers `review/gates/`.

## Decisions and deviations
- **Hands**: MM9 keys `Finger1` at 45-50 deg in walks and runs, so real finger chains, not rigid fists. Thumb left open, not solved into a fist.
- **Tone**: ramps at about MM9's value (A x 1.05, B x 1.12, C x 0.88): the Gezzampt came out too bright. A is still redder than MM9 in the viewer's light; C whiter.
- **Saddle** (r7): an ellipse over the back and onto the flanks from the body position (`tier_ramps.py`), soft edge broken by the paint's own fur grain, tier B lighter there. r6 was a blurred box with straight sides. Ours stays a little darker and more olive than MM9's grey panel.
- **Yeti chest** (r7): the chest region is an ellipse on the front from the body position with a wide soft edge (r6 picked low-saturation texels and blurred them in UV space: a jagged edge and a pale keyhole on the breastbone). Its top stays under the head set, or the head's white throat reads as a collar. Same region for A and B's tan chest, now soft-edged there too. MM9's patch is a little larger and greyer.
- **Region mask order** (r9): the shader mixes the channels in order, so the body mask's fur channel is now 1 everywhere and chest, hands/feet and saddle mix over it. With fur = 1 - the others (r6/r7) the base paint showed through every soft edge: a red-orange band under the chest on A and B, a warm rim round the Yeti's blue patch, and orange streaks in the Sasquatch's back panel. The fits keep the partition. The back panel now reads as a greyer, lighter olive area with a softer outline, nearer MM9's grey panel.
- **Head twist cap and head pivot** (r9): see Collapse. MM9 turns the head up to 96 deg; ours stops near 74.
- **Clip ends** (r7): AttackMelee2/AttackRanged ease back over 0.5 s (see Arm and hand).
- **Yeti mouth**: painted on the closed-lip geometry; no teeth geometry. Shares A's normal map, so the lips' relief sits under the painted teeth.
- **Sizes**: 256 units at scale 100. Rows keep the sprite stand-in height 163-165, so the health bar sits low and the collision column is shorter than the model.
- **Death**: MM9's `Velocity` events not carried over; `lunge` not either.

## Open points
- Jitter as the gate is written (22 flags) and collapse, above.
- Neck rim (r9): the head's lower rim now carries the body's grain and colour (4th head region, ramps fitted to the body's final colour, 2-3 of 255 off), so the pale grey patches beside the chin are gone on all tiers and the seam band has fur grain. The head UV is stretched there, so the copied grain reads streaky and faceted under the jaw (close-ups `cacr7`, `cadd7`); the hood above the rim keeps the head paint's smooth look.
- Yeti: a thin pale line across the blue chest in the Dead close-up (`ccdd6`), probably a UV seam; seen, not fixed.
- Rock throw: no rock is held; the projectile leaves the right hand.

## Not checked
- Playback at normal speed (agents cannot watch video): the hand windows, the head cap and the new neck and armpit weights were read in stills only.
- r9 sheets I read: the r9 strip sheets of A (all three), B's second and C's first from the clips as installed (before the last mask-only change), B's close-ups, the tier comparison, the tier heads, the neck sheet, the collapse sheet, the belly and back checks and the in-game sheet. The strip and close-up sheets were regenerated once more after that mask change (colour only, same clips); of those I read B's first strip sheet and A's and C's close-ups, and did not read B's third or C's second and third.
- Orientation gate not run. MM9 versus ours in clip poses: no sheet. Melee contact moment, sounds, the rock's release. Maps that place these rows, indoor light, night. LOD1-3 by eye. Android cook. Nothing in the engine plays the five new script clips yet.

User artistic acceptance: "bigfoot - ok" (2026-10-31)


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_bigfoot_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_bigfoot_reduce_claude/before/`.
