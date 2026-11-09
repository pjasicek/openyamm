# MM9 Troglodyte body (mm9_troglodyte) — 3D actor, 2026-10-31

MM9 `TROGLODYTE.abc` (58 nodes, 18 clips), rows 96 Troglodyte L10 (`MM9 Troglodyte A`, TROGLODYTE1), 97 Troglodyte Wren L17 (`B`, TROGLODYTE2), 98 Troglodyte Gnoll L24 (`C`, TROGLODYTE3). 57 placed in MM9's mines and caves.
Humanoid route: the ABC is a Bip biped with two arms and two legs. Meshy body and open-mouth head on MM9's skeleton, MM9's own clips. Progress and Meshy receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_troglodyte.glb` (`tools/install_model.py --world mm9`), variants `trog_a/b/c` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, block "MM9 Troglodyte body". `scale` 80 / 100 / 125 (MONSTERS `Scale` 0.8, 1, 1.25), `yaw_offset` -1.570796327, stride walk 1.57 / run 1.23 (planted foot), `cast: AttackRanged`, melee impact 0.35 s (`Rattack`), ranged and cast 0.396 s released at `throw_hand` = `Bip02 R Finger21` (MM9's RangeAttack node), upper body `Bip01 Spine1`, no `look` block: MONSTERS `HeadTurn` is 0 |
| Triangles LOD0/1/2/3 | 12,050 / 6,014 / 2,164 / 995. LOD0: body 6,162, spines 90, head skin 4,478, upper teeth 420, lower teeth 600, eyes 300 |
| Skeleton | MM9's nodes, names and local rotations unchanged (Bip01/Bip02 mixed names as in the ABC), + 12 half-rotation helpers `XhalfUpperArm`, `XhalfForearm`, `XhalfThigh`, `XhalfCalf` per side, `XhalfBox01-03` (tail), `XhalfJaw` |
| Clips (30 fps) | Standing `stand`, Walking `walk`, Running `run`, Fidget `fidget1`, AttackMelee `hattack1`, AttackRanged `Rattack1`, Hit `wince1`, Death `die1`, Dead; script clips AttackMelee2 `hattack2`, Fidget2, Aware, Search, Taunt, Hit2 `wince2`, Death2 `die2`. backpedal and backpedalRun not carried |
| Textures | shared body colour 2K, head colour 2K, normal and ORM 1K each, region masks 1K; tier C adds body colour 2K, head colour 2K, two normals 1K. 22.9 MB cooked |
| Meshy credits | **40 / 40**: body Smart Topology 5, head Smart Topology 5, body retexture B 10, head retexture B 10, tier C retexture 10 (backup account, no retries) |

## Fix after the user's review (2026-10-31, 0 credits, viewer `r13`)

User, Hit frame 27 (`review/user_feedback_chest_20261031.png`): a pale spike out of the chest, and a torn jaw edge beside it.
- **Spike:** my neck blend chose vertices by the side of the neck plane, and the chest under the jaw lies in front of that plane, so it took full Head weight and left with the head. `join.py` now blends by distance from the ring (0.13 m). The chest stays on the spine bones.
- **Jaw rim:** decimated triangles span the bisecting band, so the jaw weight stepped across them and the rear rim frayed. `head_build.py` smooths it along the skin behind the hinge. This moves the closed pose a little; topology and UVs unchanged.
- Rows below are bind-reference counts of the earlier table, before -> after. The Hit, Hit2, Taunt, Death and Dead rows of that table and the other gates there are the older build; only the binding regression was rerun: 140 descriptors on 57 models, 3 failed, all `MM9 Guard A/B/C` (a missing `.oytex`, another body's install); all three Troglodyte bindings build.

| Clip | face-frames | neck, head | mouth | body | seen |
|---|---|---|---|---|---|
| Standing | 896 -> 1449 | 1 -> 6 | 0 -> 0 | 0 -> 2 | 6 -> 9 |
| Hit | 4341 -> 3373 | 96 -> 96 | 98 -> 24 | 23 -> 32 | 135 -> 124 |
| Hit2 | 4218 -> 3343 | 57 -> 53 | 72 -> 20 | 32 -> 33 | 100 -> 16 |
| Taunt | 5880 -> 4494 | 91 -> 95 | 114 -> 26 | 22 -> 47 | 149 -> 150 |
| Death | 5169 -> 4023 | 73 -> 71 | 98 -> 24 | 32 -> 36 | 119 -> 109 |
| Dead | 2945 -> 2821 | 34 -> 33 | 0 -> 0 | 24 -> 23 | 52 -> 39 |

The neck count did not fall, so the spike was not what that count measured; about 96 faces remain, the ring band with the head thrown back. Standing and the body column went up a little (Taunt 22 -> 47), the price of the softer band. `review/sheet_chest_fix.png`: chest and jaw rim on all three tiers at frame 27. A small nub remains on the jaw's rear rim. Arm, jitter, pierce gates, strips and the in-game check were not rerun.

## What MM9's model taught

- **Three fingers, no thumb.** The skeleton has four finger chains, but `Finger0` has no vertices and is never keyed. My first brief to Codex said thumb plus three; the mesh says three long clawed fingers. Hands are MM9's design: 9 finger bones per side on `Finger1/11/12`, `Finger2/21/22`, `Finger3/31/32` with MM9's keyed curl. No MPFB graft. `Finger0` chains stay as empty bones.
- **The bind is a stride.** MM9's node rest is its bind and it is asymmetric (left foot back, right hand forward).
- **The mouth is the character.** `Box05` opens up to 63 degrees and translates 8 cm, showing a red palate disc as wide as the head. A closed-mouth paint would have had nothing there, so the head is its own model, generated and painted with the mouth open.

## Route (`scripts/`)

0. **Source**: `convert_abc_model.py` per skin, `mirror_glb.py` on the source: `source/true/trog*_true.glb`, true handedness from the start, so no later mirror.
1. **Masters** (Codex, `codex_masters.sh`, brief `references_hd/CODEX_BRIEF.md`): five views tier B (`references_hd/`), four of tier C with its leather (`tierC/`), four of tier A with its ribs (`tierA/`), five open-mouth head views (`references_head/`).
2. **Body** (`step1_clean.py`, `reduce_mesh.py`, `step1b_mirror.py`): Smart Topology gave a very clean figure, but each arm as torso -> tube -> forearm plus a blind tube from the cheek that ended at the elbow. MM9's shoulder is at that blind tube's root, so the torso tube is deleted and capped, and the blind tube is bridged into the forearm by a swept tube along a Bezier (the elbow). Left half mirrored, spine crease faired, torso stayed denser in the reduction.
3. **Fit** (`mm9_joints.py`, `fit_body.py`): symmetric bind from the mean of MM9's left and right directions, with MM9's exact bone lengths: each limb segment maps its joints onto them (rotation, stretch, radial profile). The torso's outline goes onto MM9's sagittal outline by a polar map. Tail on MM9's Box chain. Upper arm 0.99, forearm 0.76, thigh 1.13, calf 1.16.
4. **Head** (`head_prep.py`, `head_build.py`): the head-only Smart Topology has a real palate, throat pit, tongue and lips. Threads between the jaws deleted, half mirrored, cut by a plane at the neck, reduced. Meshy's 40 peg teeth (7,000 triangles) replaced by procedural teeth on the same sites: pointed upper, blunt lower. The mesh is closed from Meshy's 46 degree gape to MM9's rest gape of about 12 by an arc about the hinge per vertex, so the open pose stays the paint's pose and the closed pose is the bind.
5. **Join** (`join.py`, `clip.py`): body and head clipped exactly on one plane; the ring meets half way (head rim tapers, body fills out), a strip of head material closes it, normals shared over the join. Calf spines are small procedural cones. The part cut off the body stays in the paint upload as an occluder.
6. **Rig** (`rig_bones.py`, `fingers.py`, `heat.py`, `weights.py`, `build_glb.py`): bone heat on the body, mirrored, smoothed, fingers by connectivity and geodesics, head rigid over a neck band, jaw by a blend across the mouth's mid plane. Each bone's bind frame is MM9's rest frame turned by the least rotation onto our bone, so MM9's local rotations give MM9's poses. Knee and elbow pivots at the outside of the bend.
7. **UVs** (`uv_trog.py`, `repack_body.py`): `uv_atlas.py`. The body's star-shaped hands and L-shaped limbs packed at 45 %; charts cut at limb joints and finger roots, no new flattening, 56.9 %. **Never re-run: the paints belong to this layout** (`work/uv_frozen.npz`).
8. **Paint** (`uploads.py`): uploads in Meshy's own pose, so the masters line up. Tier C's upload carries body and cut-off head in one 4K atlas (0.62 + 0.38).
9. **Textures** (`tex_pipeline.py`, `tex_tiers.py`, `project_master.py`, `rast.py`): gentle grade, seam harmonised on both sides of the neck, smeared skin at the neck rebuilt with detail from a clean patch.
10. **Clips** (`clips_mm9.py`, `roles_trog.json`, `arm_bump.py`, `half_keys.py`): root motion exact (k = 1). `arm_bump.py` (from the Zombie, forearm added, an amplitude cap per job, `bumps.txt`) lifts hands and forearms out of the body with one raised-cosine window per contact.
11. **Runtime** (`rebuild.sh`): prepare, LODs, shadow fix, `region_variants.py`, `tier_c.py`, floor with smoothed offsets, winding, `tone.py`.

Rebuild: `scripts/cycle.sh <revision> [--install]` after a mesh change (heat again), `scripts/cycle2.sh <revision> [--install]` after a clip or weight change (with the gates). `scripts/quick_skins.sh <revision>` after a texture change that is not the shared base. `scripts/deliver.sh` = sheets, close-ups, strips. Binding: `scripts/bind_actors.py 1.57 1.23` under the flock.

## Tiers

- **B, Wren**: the paint, `baseColorFactor` .80/.86/.76 toward MM9's darker green (colour only).
- **A, Troglodyte**: shared set, region mask + ramps. R hide, G ribs, B claws (body); R hide, G ribs and eyes, B mouth lining, A teeth (head). MM9's A is a different pattern: pale ribs over violet. The ribs are a mask: Codex masters of the purple figure, projected on the atlas with a depth test (free), high-passed, small specks removed. Blind as in MM9: the eye takes the rib colour, a milky patch; the lid's shape stays.
- **C, Gnoll, deviation against "one shared set"**: own body colour, head colour and two normals. Reason: stitched leather over the back, shoulders, chest, shins and crown; a ramp cannot make that. Cost about 10.7 MB cooked of the model's 22.9 MB. ORM shared. Head: leather transferred from the cut-off piece of the C paint, the hide a rank onto the C body's hide, red-brown lining, green tongue, steel eyes, as MM9. The C hide was darkened toward MM9's.
- Binding per tier checked: `mm9_vs_ours_*.png`, `ingame_sheet.png` (all three drawn in one frame, scale 0.8/1/1.25 visible). LOD1-3 primitives carry the same variant mapping (region_variants).

## Handedness

Built from the true source. `Bip02 R Hand` at x < 0 on a figure facing +Z: the anatomical right. MM9's RangeAttack socket on the right hand is bound as `throw_hand`.

## Checks (viewer `r11`, before the fix above)

**Collapse gate** per clip and joint region (`scripts/collapse_gate.py`, 30 fps, worst single frame per region, faces collapsed below 20 % or flipped; `review/gates/collapse_bindref.txt`, `collapse.txt`).

| Clip | face-frames | knee L/R | groin L/R | armpit L/R | elbow L/R | wrist L/R | ankle L/R | tail root | neck, head | mouth (bind ref) | mouth (open ref) | body | seen at worst frame |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Standing | 896 | 5/4 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 1 | 1 | 0 | 78 | 0 | 6 (neck 1, mouth 0) |
| Walking | 906 | 6/7 | 0/0 | 3/3 | 0/0 | 0/0 | 0/0 | 5 | 4 | 0 | 78 | 11 | 20 (neck 2, mouth 0) |
| Running | 779 | 8/7 | 1/0 | 3/6 | 0/0 | 0/0 | 0/0 | 11 | 12 | 0 | 78 | 15 | 34 (neck 5, mouth 0) |
| Fidget | 1829 | 5/5 | 0/1 | 12/1 | 2/0 | 0/0 | 0/0 | 2 | 22 | 8 | 82 | 21 | 57 (neck 13, mouth 6) |
| Fidget2 | 4160 | 6/4 | 0/0 | 15/16 | 0/0 | 0/0 | 0/0 | 3 | 58 | 52 | 78 | 15 | 98 (neck 43, mouth 28) |
| Aware | 1203 | 6/4 | 0/0 | 9/8 | 0/0 | 0/0 | 0/0 | 1 | 15 | 0 | 78 | 7 | 21 (neck 4, mouth 0) |
| Search | 748 | 5/4 | 0/0 | 1/2 | 0/0 | 0/0 | 0/0 | 1 | 16 | 0 | 78 | 0 | 26 (neck 16, mouth 0) |
| Taunt | 5880 | 8/7 | 0/2 | 10/6 | 0/0 | 0/0 | 0/0 | 2 | 91 | 114 | 78 | 22 | 149 (neck 56, mouth 72) |
| AttackMelee | 1545 | 6/6 | 0/2 | 4/11 | 0/0 | 0/1 | 0/0 | 3 | 75 | 80 | 78 | 15 | 122 (neck 49, mouth 48) |
| AttackMelee2 | 2919 | 8/8 | 1/0 | 10/14 | 0/0 | 0/0 | 0/0 | 3 | 92 | 110 | 78 | 19 | 139 (neck 47, mouth 70) |
| AttackRanged | 1428 | 8/8 | 0/0 | 21/12 | 0/0 | 0/17 | 0/0 | 4 | 41 | 0 | 78 | 26 | 40 (neck 16, mouth 0) |
| Hit | 4341 | 8/8 | 0/1 | 12/31 | 0/0 | 0/0 | 0/0 | 1 | 96 | 98 | 86 | 23 | 135 (neck 42, mouth 64) |
| Hit2 | 4218 | 8/11 | 0/2 | 14/13 | 0/0 | 0/0 | 0/0 | 4 | 57 | 72 | 78 | 32 | 100 (neck 37, mouth 40) |
| Death | 5169 | 8/8 | 0/1 | 15/15 | 0/0 | 0/0 | 0/0 | 5 | 73 | 98 | 78 | 32 | 119 (neck 37, mouth 63) |
| Death2 | 3136 | 5/4 | 0/1 | 3/3 | 0/0 | 0/0 | 4/1 | 15 | 73 | 106 | 98 | 25 | 131 (neck 42, mouth 68) |
| Dead | 2945 | 0/0 | 0/1 | 14/15 | 0/0 | 0/0 | 0/0 | 5 | 34 | 0 | 78 | 24 | 52 (neck 11, mouth 0) |

Reading the mouth: the bind has the jaw closed, so the mouth's faces are folded in the bind. "bind ref" counts faces against that fold. "open ref" (`scripts/head_ref.py`, `HEADREF=`) counts against Meshy's open surface, each face turned by its own jaw angle: 78 is the closed cheek and cavity (present in every clip, 10-15 of them seen, the lips' corners), and it does not rise when the mouth opens, up to 86 in Hit and 98 in Death2. The half-rotation jaw helper took the open reference from up to 186 (104 seen) to that. In the same reference neck and head rise to 126, 62 seen, in Hit: I read those as the cheek band; the close-ups show a clean cheek, which is not proof.
Knees before the pivots and helpers were 0-3 in the first rig with a static helper, 9-12 with keyed helpers on the joint, 8-11 after moving the pivots to the outside of the bend. Knees did not reach the first rig's numbers; at most 4 are seen. Worst seen armpit: Hit right, 31 faces, 18 seen, the arm thrown back; not fixed.

| Gate | Result |
|---|---|
| Arm and hand (`arm_hand_gate.py --outer-only --exact`, `review/gates/arm.txt`, 48 fps) | **0 frames over 1 cm** in Standing, Walking, Running, Fidget, Fidget2, Aware, Search, Taunt, Hit, Hit2, Death, Death2, Dead. **AttackMelee**: L hand 2.2 cm 1 f, R hand 1.2 cm 1 f, R forearm 2.4 cm. **AttackMelee2**: L hand 3.1 cm 1 f, L forearm 3.3 cm. **AttackRanged**: R forearm 2.0 cm. Before `arm_bump.py`: up to 11 cm with the helpers unkeyed, 4-7 cm real. Bumps capped at 15 deg on AttackMelee2 L, or jitter fails by 4 deg/f. Finger stretch max 1.54; 9 skinned chains' bones per hand, `Finger0` empty |
| Jitter against MM9's raw keys (`jitter_gate.py`, `review/gates/jitter.txt`) | **1 clip flagged**: Death, left shoulder skin 10.1 mm/f2, the whole-body corpse raise, with arm joints at 0 excess. Hand acceleration within 3 % of MM9 except Death L 62.6 against 56.0. First build: 14 flagged |
| Nothing through cloth | The body has no cloth geometry: the leather is paint. Measured instead for what can pierce (`pierce_gate.py`, `review/gates/pierce.txt`, Walking and Running every 48 fps frame): tail in legs 0 frames in Walking and Running. Legs in tail: Walking 22/65 frames, 4.0 cm, Running 12/39, 4.8 cm: 1-3 vertices of the thigh's top at the tail root, listed frame by frame in a probe; MM9's own coarse mesh reads 0. Dead 25 f 3.2 cm, same place. Death2 tail in leg 3 f 3.7 cm |
| Head and jaw against the torso | Jaw 0 in Standing, Walking, Running, Taunt; AttackRanged 1 f 1.2 cm, Hit2 2 f 4.6 cm, Death 3 f 2.0 cm. Head skin AttackRanged 8 f 5.0 cm, Hit2 3 f 4.9 cm, Hit 9 f 3.5 cm: MM9's clips bend a much smaller head into the chest. Not corrected |
| Detached parts (`detached_parts_audit.py`, 24 fps) | **0 detached**, 43 components; 3 spines "shallow" 6-8 mm in the corpses, one root lift 8 mm in Death2 |
| Handedness | true source; `Bip02 R Hand` at -x, MM9's RangeAttack on the right hand |
| Orientation | MM9's local rotations unchanged, bone lengths exact, root motion k = 1: head and feet follow MM9 by construction. No per-frame angle gate was run |
| Winding, flat shading | 0 inverted; flat 0.03 body, 0.00 head |
| Texture quality | body atlas 56.9 %, fragments 0.9 %, stretch 1.22, spread **1.47** (over 1.3: hands 1.45x by design); head atlas 66.5 %, fragments 1.8 %, spread 1.52, stretch 2.15 (measured on the closed bind; the head is flattened and painted open, 1.07 there) |
| Floor (`floor_audit.py`) | 3/3 ok: stand -0.1, walk -2.2..+1.1, dead 0 world units at scale 125 |
| Regression `mm9_actor_models_build_every_binding` | PASS, 110 descriptors on 47 models, 0 failed |
| In game (`--assets output/mm9_rework/assets_dev`, `bootcamp.odm`, three tiers spawned) | `review/ingame_sheet.png`: all three draw with their own skin and scale, they attack, 0 load failures |
| Viewer | `run_creature_review.py check`: 48 switches, 0 failed |
| Playback | all 16 clips recorded at normal and half speed, `review/playback/` (32 runs); I read frames and numbers, I cannot watch video |

Sheets, all from viewer shots and looked at: `review/mm9_vs_ours_a.png`, `_b`, `_c` (tier by tier, same clips, MM9 above, ours below), `review/sheet_tiers.png`, `review/sheet_closeups_a.png`, `_b`, `_c` (30 joint-framed close-ups: knees, groin, armpits, elbows, neck, mouth, tail root, ankle, hands, in crouch, attack, death; the camera tracks the joint), `review/sheet_strips_a.png`, `_b`, `_c` (six frames of all 16 clips), `review/sheet_lod.png`, `review/ingame_sheet.png`.
Comparison with MM9, tier by tier: pose and silhouette follow in every clip. A: ribs over violet, teal mouth, blind; lighter and more saturated than MM9's. B: greener and a little yellower than MM9, blotches in place. C: leather over back, chest, shoulders, shins, wrist bands; hide darkened to MM9's; mouth red-brown, tongue green. Ours has a real jaw and teeth where MM9 has a shelf.

## Deviations and open points

- **Tier C images**, above.
- **Bigger chin than MM9**: MM9's jaw is a thin shelf; ours is a real jaw with a throat, so the silhouette is heavier under the head. It is the Codex master's and matches the open-mouth design.
- **Teeth are procedural** (Meshy's pegs were thin and cost 7,000 triangles), painted by the retexture.
- **Forearm shorter than Meshy's** (stretch 0.76) to get MM9's exact reach, with a radial profile.
- **Calf spines**: three per leg, simplified from Meshy's scraps.
- **Tail narrowed** (0.78) so it clears the thighs as MM9's does; root overlap below.
- **No head turn** (`HeadTurn 0`): no `look`.
- **Row height**: rows keep 145 / radius 66 from the sprite tables; at scale 80 the A model stands about 96 units tall, so its health bar floats; C at 125 stands about 150.
- **Spell and missile FX** at `throw_hand` not seen. MM9 hides and shows a weapon in `Rattack1` (`hideweapon`, `ShowWeapon`): the body has none in `Rattack1`; ignored.
- **Symmetry**: mirror residual p99 2 mm, max 17.5 mm at the back of the neck (the ring conform); head, teeth, eyes under 2 mm.

## Not checked

- Motion by eye: the playback videos exist, I judged frames and numbers, not the videos.
- Indoor light: the in-game check is outdoors in `bootcamp.odm`; the mines that place this monster were not visited.
- Spell and missile FX at `throw_hand`, the moment of the throw, sounds and footsteps in game.
- Fidget2, Aware, Search, Taunt, Hit2, Death2 in game: bound as script clips, nothing drives them yet.
- A per-frame orientation gate of head and feet against MM9 (see Checks).
- LOD1-3 in tiers A and C: `review/sheet_lod.png` is tier B. Shadow meshes by eye.
- Loop seams of Walking and Running beyond the jitter gate.
- Android cook (only on request).


## Dropped MM9 clips restored (2026-10-31, run2-clips-groupB)
MM9's TROGLODYTE.abc has 17 clips; `backpedal` and `backpedalRun` were missing. Added as `Backpedal`, `BackpedalRun` (loops, half keys, floor as Walking/Running with smoothing), bound `backpedal`, `backpedal_run`. MM9's two backpedal clips carry the forward walk's keys (BackpedalRun is the walk at 0.8 s), so they step forward as MM9's do. Built with this project's own clip route in `scripts/extra_clips.sh` (soft joint-offset line now in `clips_mm9.py`), floored, then grafted with `claude_shared/graft_clips.py`: meshes, LODs, variants and the accepted clips are byte for byte (checked: old buffer a prefix of the new, old JSON unchanged). Numbers in `review/gates_extra/`, strip `review/gates_extra/strip_new.png` (numpy raster, untextured). Status: `devdocs/mm9_rework/overnight/status/clips_groupB.md`.

User artistic acceptance: "troglodyte - good" (2026-10-31)


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_troglodyte_reduce_claude/`** (user-approved; ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `mm9_troglodyte_reduce_claude/before/`.
