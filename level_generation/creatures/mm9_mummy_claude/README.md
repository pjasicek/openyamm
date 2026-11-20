# MM9 Mummy body (mm9_mummy) — 3D actor, 2026-10-30

MM9 `MUMMY.abc` (32 joints, 22 clips), rows 144 Canopic Mummy L20 (`MM9 Mummy A`, MUMMY1), 145 Embalmed Mummy L30 (`B`, MUMMY2), 146 Petrified Mummy L40 (`C`, MUMMY3). Placed in Chasm of the Dead.
Built on the approved route (MM9 skeleton, MM9 clips, separate head set), with the differences under "Deviations". Progress and receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_mummy.glb` (`tools/install_model.py --world mm9`), variants `mummy_a/b/c` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, scale 100, `yaw_offset` -1.570796327, stride walk 1.49 / run 2.52 (planted foot), `cast: AttackRanged`, melee and ranged impact 0.333 s, release and glow `cast_hand` = `Bip01 R Hand`, look `Bip01 Neck, Head`, upper body `Bip01 Spine1` |
| Triangles LOD0/1/2/3 | 9,397 / 4,697 / 1,691 / 563; LOD0: body 5,806, head 3,207, strips 384 |
| Skeleton | 95 joints: MM9's 32 + 30 finger bones (15 per side) + 13 band bones + 9 half-joint helpers + spare `XarmStrip`, `XthighStrip` (unweighted) + the rest of MM9's unused strip bones |
| Clips (30 fps) | Standing `stand`, Walking `walk`, Running `run`, Fidget `fidget1`, AttackMelee `Hattack1`, AttackRanged `Rattack1`, Hit `wince1`, Death `die1`, Dead; script clips AttackMelee2, Fidget2, Hit2, Taunt, ResurrectSpell, Resurrect, Coffin, Wakeup, Wakeup2 |
| Textures | 3 body colour 2K, 3 head colour 2K, 3 body normal 1K, 3 head normal 1K, 2 ORM 1K shared by the tiers (14 images) |
| Meshy credits | **40 / 40**: body Smart Topology 5, head Smart Topology 5, body retexture A, B, C 10 each (backup account), no retries |

## Second pass (2026-10-31, 0 credits)

Orchestrator's list after reading the sheets; this is the second serious attempt. Everything here is in `rebuild.sh`. Mesh, UVs and paints unchanged except 10 head triangles removed.

- **Thigh and arm strips lie on the skin** (`assemble.py` `on_skin`): each vertex 5.5 mm off the surface, skinned from the triangle under it, so they bend with the limb in every pose. The thigh strip was the shard the orchestrator found; the arm spike was the same fault (it went through the floor in Dead), so it went too. Lost: both MM9 spikes as silhouette, `Bone01/02/24` are no longer used. The thigh strip's base no longer reads as "inside the thigh": it is on the skin.
- **Half-joint helpers** (`rig_bones.half_pairs`, `weights.py`, `half_keys.py`): 9 bones at shoulders, elbows, hips, knees and the head, each turned half way between parent and child on the keys; where the two overlap, the shared weight moves to the helper.
- **Hinge pivots moved to the outside of the bend** (`build_glb.py`): knee 3 cm back, elbow 1.5 cm back, hip 2.5 cm forward. This took Running's knees from 7/6 to 0/2.
- **Shoulder blend widened** (8 extra smoothing passes within 13 cm of the joint).
- **Band on 13 knots with its own bones** (`Xband01-11`), bending stiffness in the rope, a low-pass along the chain, a chest capsule.
- **Arm correction softened** (`arm_soft.py`): `arm_clear`'s result widened by a running maximum and a Gaussian in seconds, soft-capped, faded at the clip's ends, in the parent's frame. Tried wider envelopes: at 0.14 s and 13 deg the jitter gate nearly passed (1.06 deg/f) but the left hand went back 6 cm into the leg, 11 frames. Hands in the body are the worse fault, so the shipped envelope is cap 22 deg, sigma 0.09 s, fade 0.16 s.
- **Head islands**: two 5-triangle islands removed at assembly.
- **Feet**: the new orientation gate found every sole pitched 10 deg against MM9 in every clip. My bind used the ankle-to-toe direction for the foot, which differs between the two feet shapes. Now yaw only.

### Collapse, first pass -> second pass (`scripts/collapse_gate.py`, 30 fps, worst single frame per region; `review/pass1/`, `review/collapse.txt`)

| Clip | face-frames | knee L/R | hip L/R | groin | neck | shoulder L/R | elbow L/R | strip | seen at worst frame |
|---|---|---|---|---|---|---|---|---|---|
| Standing | 243 -> 72 | 0/0 | 0/0 | 0 | 0 | 1/0 | 0/0 | 2 -> 0 | 3 -> 1 |
| Walking | 236 -> 108 | 3/3 -> 0/0 | 4/4 -> 2/0 | 0 | 0 | 2/1 -> 1/1 | 0/0 | 8 -> 4 | 11 -> 5 |
| Running | 506 -> 153 | 7/6 -> 0/2 | 8/5 -> 0/0 | 0 | 0 | 9/9 -> 5/4 | 0/0 | 12 -> 3 | 10 -> 9 |
| Fidget | 528 -> 205 | 0/0 | 0/0 | 0 | 0 | 8/0 -> 5/0 | 0/0 | 4 -> 2 | 7 -> 4 |
| Fidget2 | 1017 -> 592 | 0/0 | 0/0 | 0 | 0 -> 1 | 12/5 -> 5/3 | 0/0 | 2 | 12 -> 9 |
| Taunt | 1017 -> 592 | 0/0 | 0/0 | 0 | 0 -> 1 | 12/5 -> 5/3 | 0/0 | 2 | 12 -> 9 |
| AttackMelee | 694 -> 393 | 2/2 -> 0/3 | 5/1 -> 1/2 | 2 -> 0 | 7 -> 4 | 22/19 -> 7/16 | 0/3 | 35 -> 6 | 51 -> 20 |
| AttackMelee2 | 535 -> 361 | 2/2 -> 1/3 | 5/0 -> 0/0 | 3 -> 0 | 8 -> 9 | 8/16 -> 6/9 | 0/0 | 33 -> 6 | 58 -> 25 |
| AttackRanged | 694 -> 393 | 2/2 -> 0/3 | 5/1 -> 1/2 | 2 -> 0 | 7 -> 4 | 22/19 -> 7/16 | 0/3 | 35 -> 6 | 51 -> 20 |
| Hit | 126 -> 168 | 0/0 -> 0/2 | 0/3 -> 0/0 | 0 | 2 | 3/2 | 0/0 -> 1/0 | 4 -> 6 | 7 -> 11 |
| Hit2 | 185 -> 211 | 0/0 -> 0/2 | 0/0 | 0 | 5 -> 4 | 4/3 -> 2/5 | 0/0 | 4 | 10 -> 12 |
| Death | 1349 -> 626 | 7/8 -> 0/1 | 13/7 -> 5/5 | 1 -> 0 | 11 -> 9 | 8/6 -> 7/5 | 0/0 | 66 -> 13 | 54 -> 24 |
| ResurrectSpell | 1017 -> 592 | 0/0 | 0/0 | 0 | 0 -> 1 | 12/5 -> 5/3 | 0/0 | 2 | 12 -> 9 |
| Resurrect | 7287 -> 3250 | 12/28 -> 2/19 | 80/14 -> 98/6 | 13 -> 2 | 4 -> 2 | 13/16 -> 7/4 | 8/8 -> 5/7 | 87 -> 26 | 116 -> 71 |
| Coffin | 177 -> 71 | 0/0 | 0/0 | 0 | 0 | 15/20 -> 4/6 | 7/8 -> 4/4 | 12 -> 10 | 45 -> 22 |
| Wakeup | 5695 -> 2667 | 11/16 -> 3/8 | 34/32 -> 19/15 | 8 -> 0 | 1 | 43/27 -> 17/10 | 8/8 -> 4/4 | 38 -> 12 | 65 -> 26 |
| Wakeup2 | 4848 -> 2185 | 11/16 -> 3/8 | 34/32 -> 19/15 | 8 -> 0 | 1 | 43/27 -> 17/10 | 8/8 -> 4/4 | 29 -> 12 | 65 -> 23 |
| Dead | 713 -> 775 | 0/0 | 0/2 -> 2/2 | 0 | 8 -> 6 | 2/2 -> 2/3 | 0/0 | 9 -> 10 | 21 -> 20 |

### Other gates, first pass -> second pass

| Gate | First pass | Second pass |
|---|---|---|
| Thigh strip | stands off the leg, rigid | on the skin in every pose, `review/sheet_closeups2.png` |
| Detached parts | 1 flagged (head island 6.8 mm) | **0 detached**, 8 components |
| Jitter (`review/jitter_gate.txt`) | 5 fails: upper arm excess 3.3, forearm 3.8 deg/f | **still 5 fails**: AttackMelee/Ranged upper arm 1.48, forearm 2.24 deg/f; Death 1.35, 1.1 (threshold 1.0). Hand maxima within 1.5 % of MM9 except Death L acceleration 83 against 79 |
| Arm gate, AttackMelee/Ranged | L 0 frames, R 1 frame 1.0 cm | **worse**: L 2.2 cm 4 frames, R 2.4 cm 2 frames. The price of the softer correction; fingertips at the thigh at the end of the swing |
| Arm gate, Death | 0 | 0 |
| Band through thigh and calf, 48 fps | Walking 0/66, Running 0/44, Standing 0/129 | Walking 0/66, Standing 0/129, Running 2/44 0.3 cm, AttackMelee 2/42 2.7 cm, Hit2 3/49 0.6 cm, Death 2/53 0.4 cm; script: Wakeup 33/210 1.8 cm, Wakeup2 28/129 1.7, Resurrect 5/177 1.1, Coffin 4/4 1.4 |
| Band through torso and hip (new) | not measured | Standing, Walking, Running, Hit, Death 0; **AttackMelee/Ranged 7/42 5.9 cm, AttackMelee2 5/37 9.4 cm**; script Wakeup2 13/129 9.6, Resurrect 4/177 10.0 |
| Foot orientation against MM9 (new) | sole 10 deg off in all clips | sole mean 0.0-2.6 deg, 3.4 deg of yaw is our toe splay. Max in Walking 10.7, Wakeup 24.6 |
| Head orientation against MM9 (new) | - | mean 0.2-6.7 deg; the larger values are one-shots easing from Standing (max 35.8 in AttackMelee2) |
| Floor audit | ok, walk -1.3..+1.6 | ok, stand 0, walk -0.5..+1.0, dead 0 |
| Regression | PASS 87 descriptors | PASS, 95 descriptors on 42 models, 0 failed |
| Winding, flat shading | 0, 0.00 | 0, 0.00 |
| Viewer check | 54 switches, 0 errors | 54 switches, 0 errors |
| Texture quality | atlas 55.8 / 58.7 % | atlas 55.8 / 58.6 %, spread 1.47 / 1.08 |
| In game | 3 tiers | 3 tiers, 0 load failures, `review/ingame_sheet.png` |
| Playback (`run_creature_review.py playback`) | not run | all 18 clips recorded at normal and half speed, `review/playback/*.webm`; timed frames of the moving clips in `review/sheet_playback.png`. I read frames, not motion: I cannot watch the video |

### Still failing or open, with numbers

- **Jitter: 5 fails remain**, excess down from 3.3 to 1.48 deg/f, all in the corrected clips, because the clip gives the correction under 0.4 s to rise and fall. A pass costs a hand in the leg (above). Not solved further: this was the last attempt.
- **Arm gate got worse** in AttackMelee and AttackRanged, as stated: 2.2 and 2.4 cm for 4 and 2 frames.
- **Band through the chest in the attacks**: up to 9.4 cm for 5 frames of 37 in AttackMelee2. Its tip is pinned on the forearm, and the forearm crosses the chest. A final collision pass after the low-pass did not help (5.0 and 9.5 cm) and made Running worse (1.1 cm), so it was taken out.
- **Shoulders**: AttackMelee right 16 faces, the anterior armpit as the arm crosses the chest, a real crease.
- **Hit and Hit2** went slightly up (126 -> 168, 185 -> 211 face-frames), right knee 2: a cost of the moved pivots.
- **Resurrect left hip 80 -> 98**: the moved hip pivot in a crumpled pose half under the floor. Script clip, nothing drives it; left.
- **Wakeup**: hips 19/15, shoulders 17/10, band through thigh 33/210 frames. Script clip; hands in the legs 6 cm in sitting, as before.

## Route (`scripts/`)

0. **Masters** (Codex through `codex_slot.sh`, `references_hd/`, `references_head/`, inputs `mm9_views_t*.png` rendered from MM9 model + skin): five views of tier A, four of B and C (`tierB/`, `tierC/`), four busts per tier, a clean sculpt `00_geometry.png`, and `strip_swatch.png`. Masters leave the loose strips out on purpose.
1. **Body** (`step1_clean.py`, `step2_sym.py`): Smart Topology 15k from the 3/4 master gave a clean body with five separate fingers and a crushed face. Centred, yaw undone, left arm turned to the masters' A pose, left half mirrored (residual max 4 mm).
2. **Head** (`step3_head.py`): head-only Smart Topology from the sculpt. Meshy double-walls the hood and hung a needle off the chin: spike cut, hidden walls deleted by ray visibility (voxel routes mangled the face, `solid_head.py` is the dead end), crown and back of the hood put on an ellipsoid, left half mirrored.
3. **Join** (`step4_join.py`): per-region reduction of the body half, then a neck tube runs up inside the hood; the head is a separate shell lying over it.
4. **Rig** (`fit_rig.py`, `heat_weights.py`, `weights.py`, `build_glb.py`): joints from plane sections, fingers from geodesic merge levels. **Bind is the mesh's A pose, not MM9's T pose**: each bone's bind frame is MM9's rest frame turned by the least rotation onto our bone, inverse binds from that, so MM9's local rotations give MM9's poses with no mesh posing step (the Yrsa route's "joints translated only" could not apply). Heat weights, mirrored, 6 smoothing passes, fingers restricted to their chains, head rigid, neck tube blended.
5. **Paint**: body UVs on the upload (`uv_mummy.py`), 4K retexture per tier. **Runtime layout** (`split_pack.py`, `transfer.py`): the upload's atlas use was 29 % (see Deviations), so the long charts are cut and repacked with a strip rectangle, and all maps are sampled from the 4K paints through the old UVs, normals rotated per chart. No repaint.
6. **Linen** (`linen.py`): Meshy paints the cloth as pebbles, a hide rather than linen. On a mask of the cloth (long dark gaps and flesh excluded) colour and normal are low-passed and a weave from the Codex swatch goes on. Pattern and gaps stay.
7. **Heads** (`head_project.py`, `head_landmarks.json`): no credits left for six paints, so each tier's Codex busts are projected onto the head UVs by hand-read landmarks, four views, depth-tested. Normal from luminance. 25 % of the head set's texels are hidden surfaces with no view; they carry the nearest colour.
8. **Strips** (`strips.py`, `band_sim.py`): ribbons on MM9's strip bones, two-sided. The long band is a rope solve on the 30 fps keys (pinned on the waist and right forearm, gravity, capsules round thighs, calves and torso, loops three cycles with the seam spread, low-passed), with no twist by parallel transport. MM9's own keys left it through the thigh and folded.
9. **Clips** (`clips_mummy.py`, `roles_mummy.json`, `arm_clear.py`): MM9 local rotations, repeated keys thinned, pelvis translation absolute. Arm correction on AttackMelee, AttackMelee2, AttackRanged and Death only (max 19.9 deg, on keys, sigma 2).
10. **Runtime** (`rebuild.sh`): build -> clips -> `arm_clear` on the skin without strips -> `copy_anim` -> `band_sim` -> prepare -> LODs -> shadow fix -> `tier_skins.py` -> floor -> `mirror_glb.py` (last) -> winding -> install. Then `viewer_update.sh <revision>`.

Rebuild: `TOKEN=<lease> scripts/rebuild.sh --install` from the project folder; textures: `work/textures.sh`, then `linen.py`, the grade and `finish_tex.py`. Never re-run `uv_mummy.py`: the paints belong to that layout. `bind_actors.py` writes the binding (the first install used `rebind_cast.py` for the cast clip).

## Handedness

Everything is built in the raw (mirrored) ABC frame and `mirror_glb.py` flips the finished GLB. `scripts/handedness.py`: final figure faces +Z, `R Hand` at x -0.504 (anatomical right), raw at +0.621 (anatomical left). The band and arm strip are on the true right arm. MM9's `RangeAttack` socket is on `R Hand`, bound as `cast_hand`.

## First pass checks (viewer `r7-20261030`, superseded where the second pass lists a newer number)

| Gate | Result |
|---|---|
| `run_creature_review.py check` | 54 switches, 0 console errors |
| Regression `mm9_actor_models_build_every_binding` | PASS, 87 descriptors on 40 models, 0 failed (it failed on the first binding, `spellcasting actor model requires a cast clip`, fixed) |
| In game, `--assets output/mm9_rework/assets_dev`, `bootcamp.odm`, three tiers spawned | `review/ingame_sheet.png`: all three draw with their own skin; 0 load failures in the log |
| `check_winding.py` | 0 inverted closed parts |
| `flat_shading_check.py` | 0.00 body and head |
| `floor_audit.py --match 'MM9 Mummy*'` | 3/3 ok: stand 0, walk -1.3..+1.6, living -1.3, dead 0 world units |
| `texture_quality.py` body / head | atlas 55.8 % / 58.7 %, spread 1.55 / 1.08 (body over the 1.3 target: hands 1.4x and strips denser, by design), fragments 0.1 / 0.3 %, stretch p90 about 1.1 / 1.16 |
| `arm_hand_gate.py --outer-only --exact` (skin, no strips) | hand and forearm 0 frames over 1 cm in Standing, Walking, Running, Fidget, Fidget2, Taunt, Hit, Hit2, Death, Dead; AttackMelee/Ranged R 1 frame 1.0 cm; script clips Coffin R 5.9 cm 4 frames (crossed hands on the chest), Wakeup L 5.4 cm 19 frames, R 5.8 cm 12, Resurrect L 2.5 cm 11; finger stretch max 1.9 (Wakeup), 1.5 elsewhere; 15 chains per side |
| `jitter_gate.py` against the uncorrected clips | hand acceleration and angular velocity at or under MM9 everywhere. 5 fails, all per-frame excess on corrected clips: AttackMelee and AttackRanged upper arm 3.3 deg/f, Death 1.9 deg/f (fast clips) |
| `strip_gate.py` (`review/strip_gate.txt`, 48 fps, strips against thigh and calf skin) | **Band: Walking 0/66, Running 0/44, Standing 0/129**, Fidget 2/167 0.5 cm, AttackMelee/Ranged 1/42 2.2 cm, Death 0, Resurrect 2/177 7.7 cm. Before the rope: Walking 20/66 3.1 cm, Standing 129/129 2.4 cm. Arm strip 0 everywhere. Thigh strip reads 1.2-1.4 cm in every frame: that is its base, rooted in its own thigh, rigid on it; it does not pass through the other leg |
| `detached_parts_audit.py` (24 fps) | 12 components, 1 flagged: a 5-triangle head island, 6.8 mm in 4 of 920 poses, rigid on `Bip01 Head`. Band and arm strip roots clear after moving their pins |
| Symmetry | mirror residual mean 0.01 mm, max 4 mm (MM9's own hands and strips are not symmetric; the body is) |

**Collapse gate, first pass** (`review/pass1/collapse.txt`), worst single frame per region, faces collapsed or flipped, then faces any camera can see at the clip's worst frame:

| Clip | knee L/R | hip L/R | groin | neck | shoulder L/R | strip | seen |
|---|---|---|---|---|---|---|---|
| Standing | 0/0 | 0/0 | 0 | 0 | 1/0 | 2 | 3 |
| Walking | 3/3 | 4/4 | 0 | 0 | 2/1 | 8 | 11 |
| Running | 7/6 | 8/5 | 0 | 0 | 9/9 | 12 | 10 |
| Fidget | 0/0 | 0/0 | 0 | 0 | 8/0 | 4 | 7 |
| AttackMelee, AttackRanged | 2/2 | 5/1 | 2 | 7 | 22/19 | 35 | 51 |
| AttackMelee2 | 2/2 | 5/0 | 3 | 8 | 8/16 | 33 | 58 |
| Hit | 0/0 | 0/3 | 0 | 2 | 3/2 | 4 | 7 |
| Hit2 | 0/0 | 0/0 | 0 | 5 | 4/3 | 4 | 10 |
| Death | 7/8 | 13/7 | 1 | 11 | 8/6 | 66 | 54 |
| Dead | 0/0 | 0/2 | 0 | 8 | 2/2 | 9 | 21 |
| Fidget2, Taunt, ResurrectSpell | 0/0 | 0/0 | 0 | 0 | 12/5 | 2 | 12 |
| Resurrect (script) | 12/28 | 80/14 | 13 | 4 | 13/16 | 87 | 116 |
| Coffin (script) | 0/0 | 0/0 | 0 | 0 | 15/20 | 12 | 45 |
| Wakeup, Wakeup2 (script) | 11/16 | 34/32 | 8 | 1 | 43/27 | 38, 29 | 65 |

These are open numbers, not excused: Most "seen" faces in the attacks and Death are the band folding where the arm throws it, then shoulders under an arm raised above a 40-degree bind. Close-ups of the skin read clean; the cat lesson says that is not proof. Passes 2 -> 6 of weight smoothing took Walking hips and knees from 5/4 to 4/3 and AttackMelee face-frames 1,369 -> 1,137.

Sheets (viewer shots, second pass build): `review/mm9_vs_ours.png` (MM9 mirrored over ours, eight clip frames; the cameras are close, not identical), `review/sheet_tiers.png`, `review/sheet_hide_mm9.png`, `review/sheet_closeups.png` and `review/sheet_closeups2.png` (groin, knees, armpits, elbows, neck, the strips, in sitting, crouching, attack, death; tier B), `review/sheet_strips_a.png`, `sheet_strips_b.png`, `sheet_strips_c.png` (six frames of all 18 clips per tier, looked at small), `review/sheet_playback.png`, `review/ingame_sheet.png`.

## Deviations and open points

- **Per-tier images, against the "one shared set + ramps" rule.** Reason: the skins differ in design, not colour: Canopic is fully wrapped with a bearded man's face, Embalmed is torn open over flesh with a skull, Petrified is criss-crossed strips over dark flesh with a different skull. Ramps cannot move a bandage. The doc's exception is "differs in pattern or detail (markings, a face)". **Extra memory: 23.4 MB cooked over one set** (B and C: 2 body colour, 2 head colour, 2 body normal, 2 head normal; one set is 12.1 MB, total 35.4 MB). Colour-only differences stay out of the images: ORM is shared, the strip swatch is one image in all three, tier tone is `baseColorFactor` per material (A .85/.90, B .95/.90, C .60/.80). Runtime: variants map per primitive in the cooked GLB; `review/ingame_sheet.png` shows all three drawn in one frame. A later tier or recolour on this body is not a ramp edit.
- **Atlas mistake.** I submitted retexture A before reading the UV report: 29 % use. The 4K paint has enough density for the 2K runtime (2,218 equivalent px against 1,530 used), so charts were cut and repacked instead of repainting. B and C used the same layout so all three transfer alike. Cost: chart cuts, no credits.
- **Hands**: five wrapped fingers from Meshy's mesh by connectivity, 15 bones per side, no MPFB graft. MM9 has no finger bones: its right hand is a mitten, its left a thumb and three fingers. Ours are the same on both sides and hold a relaxed curl in every clip.
- **Thigh strip** moved from MM9's inner thigh to the outer thigh, on the skin (second pass). **Arm strip** on the back of the upper arm, on the skin.
- **Band keys are ours**, not MM9's: a rope solve on `XstripRoot`, `Xband01-11`, `XstripTip`. Rope length 0.86 of the bind polyline. `Bone04-08` keep MM9's keys but drive nothing.
- **Short forearm**: Meshy's forearm is 15 cm against MM9's 21; total reach about 7 cm less. Not stretched: the masters were painted on this shape.
- **Heads are projections**, not Meshy paints: sharper than Meshy on the face, but front, side and back views meet in visible seams on the hood, and the back of tier A's hood has a few blotches.
- **Head colour 2K**, as Yrsa and the Skeleton Warrior ship, not the brief's 1K.
- **Neck**: a small fin of the hood sits at the side of the nape; the hood lies over the neck tube rather than joining it.
- **No jaw**: MM9 has no jaw bone, mouths are closed, painted. No cavity built.
- **Eyes** are paint, no emission. MM9 has no glow on these skins.
- **Spell FX**: `cast_hand` socket bound, but what Curse and Paralyze look like at that hand was not seen.
- **Coffin scripts**: `coffin`, `Wakeup`, `Wakeup2` are bound as script clips. No behaviour drives them; `MUMMYAWAKEN.scr` and `COFFINMUMMY.scr` are not implemented. `Resurrect` starts below the floor, as MM9's does (a rise from the ground).
- Unused MM9 clips: die2, BackPedal, BackPedalRun, Coffin2, static_model.

## Not checked

- Chasm of the Dead itself: the in-game check was `bootcamp.odm`, outdoors, with spawned actors. Indoor lighting not seen.
- Melee and cast effects in game, attack sounds, the charge glow at `cast_hand`.
- LOD1-3 and shadow meshes by eye; the skin-laid strips at LOD1+ especially (they may sink into the leg).
- Motion by eye: the playback videos exist, but I judged frames and numbers, not the videos themselves.
- The rope seam on loops was not measured, and band jitter is judged from frames.
- Android cook (only on request).

## Dropped-clip pass, 2026-10-31 (run 2, 0 credits)

`scripts/roles_mummy_extra.json`: Backpedal, BackpedalRun, Coffin2 (lying in the coffin, held pose), Death2 (`die2`), Dead2, through arm_clear (Coffin2 only, 22 deg cap: crossed hands 6.0 -> 0.7 cm), copy_anim, band_sim (Backpedal* loop; Dead2 holds Death2's end; Coffin2's band settles and holds), half_keys, floor (ground-death Death2/Dead2, Coffin2 grounded), mirror, grafted with `claude_shared/graft_clips.py`. Bound `coffin2`, `death2`, `dead2`, `backpedal`, `backpedal_run`. Band through torso: Death2 2.1 cm, 18 of 66 frames. Numbers, strips: `review/clips_restore/`; summary `devdocs/mm9_rework/overnight/status/clips_groupA.md`.

User artistic acceptance: "mummy - ok" (2026-10-31)


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_mummy_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_mummy_reduce_claude/before/`.
