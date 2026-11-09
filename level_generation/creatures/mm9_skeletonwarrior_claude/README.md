# MM9 Skeleton Warrior body (mm9_skelwar) — 3D actor, 2026-10-30

## Dropped MM9 clips (2026-10-31, run2-clips-groupD) - current

The user lifted the hold on this approved project for clip grafting only. Missing 8: search, fidget2, Hattack1OLD, RAttack1OLD,
wince2, die2, BackPedal, BackPedalRun; all carried. `scripts/extra_clips.sh` (header lists the steps) grafts 8 clips onto the
installed export (`work/pre_clips_export.glb` kept); byte check OK, 22.70 -> 23.86 MB. New files: `roles_skelwar_extra.json`,
`floor_ops_extra.txt`, `rename_clip.py`, `skirt_keys_extra.py` and `skirt_floor_extra.py` (copies of the accepted scripts for
the new clip names; the accepted ones are unchanged). Bound on Skeleton Warrior A/B: search Search, fidget2 ResurrectSpell (MM9's
fidget2 carries its keys), attack_melee_old AttackMeleeOld, attack_ranged_old AttackRangedOld (throw hand, release 0.600 s),
hit2 Hit2, death2 Death2, dead2 Dead2, backpedal Backpedal, backpedal_run BackpedalRun.
Gates (`review/clips_restore_D/`): skirt Backpedal 0 frames through, BackpedalRun 4/33 frames 3.9 cm (front plates at the 62 deg
cap), AttackMeleeOld 14/37 4.1 cm (accepted AttackMelee 16/44 7.6), Death2 11/101 0.9; hands over 1 cm: Death2 L 25 / R 10 frames
(kneeling, both hands on the hilt: the hands meet each other and the blade, `clay_death2.png`), AttackMeleeOld L 4 / R 2, Search R 5
(the fist on the scimitar), as the accepted AttackMelee/Death; L Thigh offset 0.111-0.135 m in AttackMeleeOld (the mirror_source
hip slide the accepted clips have, R Thigh 0.101-0.149); floor living -0.9..+0.8 (BackpedalRun airborne to 18.9, as Running),
corpse 0; jitter arm joints 0 excess, shoulder skin from the floor root Death2 17-18, BackpedalRun 11 mm/f2 (accepted Death 20-25,
Running 39-45). Strips `strip_new_*.png`, `clay_death2.png` read. Not looked at in the viewer or in game.
Edits to approved files (opt-in, defaults unchanged; the patched `clips_mm9.py` rebuilds the accepted clips byte for byte): `clips_mm9.py` gained roles-json `soft_offsets` (the soft joint-offset line) and a per-role `hold`; `scripts/bind_actors.py` carries the new script clips.

MM9 `SKELETONWARRIOR.abc` (33 joints, 21 clips), rows 136 Skeleton Warrior L22 (descriptor `MM9 Skeleton Warrior A`, skin
SKELETONWAR2) and 137 Skeleton Master L33 (`MM9 Skeleton Warrior B`, SKELETONWAR1), both with SKELETONSCIMITAR. The plain
`skeleton` body is a separate job. Built by the approved Yrsa route (MM9 skeleton, MM9 clips, a separate head set) with the MM6
skeleton's rigid-piece rule (`../mm6_ske_claude/`) and the Dagrell's joint lesson (`../mm9_dagrell_claude/`).
Progress, hashes and receipts: `creature_3d_progress.json`. User artistic acceptance: approved "very good" with one fix (the skirt, below); the fixed build is not yet reviewed.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_skelwar.glb` (`tools/install_model.py --world mm9`), skins `skelwar_b` Warrior, `skelwar_c` Master |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, scale 100 (MONSTERS `Scale` 1), `yaw_offset` -1.570796327, stride walk 1.68 / run 3.4, melee impact 0.339 s (`Rattack`), ranged impact 0.402 s (`RangeAttack`), release socket `throw_hand` = `LHand1`, look `Bip01 Neck, Head` |
| Triangles LOD0/1/2/3 | 10,484 / 4,428 / 1,623 / 578 (of LOD0: 1,574 dark lining faces, 266 scimitar, 7,300 painted body and head) |
| Skeleton | MM9's 33 joints, names and rest rotations unchanged, joints translated onto the pieces, + 15 finger bones per side (`Bip01 <S> Thumb1..Pinky3`), + 8 plate hinges (`Skirt_*`) |
| Clips (30 fps) | Standing `stand` 2.0, Walking `walk` 1.1, Running `run` 0.67, Fidget `fidget1` 1.7, AttackMelee `Hattack1` 0.9, AttackRanged `RAttack1` 1.1, Hit `wince1` 0.93, Death `die1` 1.2, Dead; script clips `attack2` (Hattack2), `taunt`, `resurrect_spell`, `resurrect` |
| Textures | body 2K colour (mirrored limbs share texels), head set 2K colour (helmet, skull, neck, eyes), normal and ORM 1K each, scimitar 1536x1024 (from the Codex master) |
| Meshy credits | **30 / 40**: body Smart Topology 5, skull Smart Topology 5, body retexture 10, head retexture 10 (backup account, no retries) |

## Skirt fix (2026-10-30) - current

User approved the model ("very good") with one fix: "when walking and running, the thigh bones go through the skirt". Body and leg clips, mesh, UVs, textures and binding are unchanged:
`scripts/clip_same.py` gives 0 difference on every body channel in all 13 clips (against `work/before_skirt/mm9_skelwar.glb`, the approved build). Meshy: 0 credits.

- **Cause**: the plates were skinned by one smooth field, belt to thighs (`fit_skelwar.py`), so they followed the thighs by at most 80 % and bent; the thigh passed through. `scripts/skirt_gate.py` measures it: femur, knee and
  boot-top points on a plate's outer side with their foot on the plate, 48 fps, LOD0 (zero-UV linings are not plates).
- **Fix**: eight rigid plate groups on small hinge bones `Skirt_<group>` at the belt, children of `Bip01 Spine` (`finish_skelwar.py`, `work/skirt_groups.json`), keyed by `scripts/skirt_keys.py` on the 30 fps keys, in the Spine frame: base = Kabsch fit of each plate to the
  approved skinned plate; plus the least extra turn that clears the leg by 1 cm, front and back plates fore and aft, side plates along their own swing; through a running maximum (0.05 s) and a Gaussian (0.04 s; one-shots twice that), circular on loops
  (seams at most 0.06 deg). A side plate leans 0.45 of its front neighbour's turn. One-shot extras are capped (front 50 deg, side and back 8), AttackMelee scaled 0.75.
- **Rejected on the way**, all with numbers that passed: a radial lift about each plate's top edge (the skirt fanned out like a flower, up to 75 deg, linings showing); the same diagonal axis on `front_R`/`front_L` (they rolled edge-on, like wings);
  uncapped one-shots (a side plate flew out as a black wing in Hit).
- **Death and Dead**: the rigid plates reach lower, so the floor pass lifted the corpse 5 cm. `scripts/skirt_floor.py` restores the approved root keys and turns any plate that would sink a few degrees clear of the floor.

| Clip | Frames through, before | after | Deepest cm, before | after |
|---|---|---|---|---|
| Walking | 53/53 | 0/53 | 6.3 | 0.0 |
| Running | 32/33 | 0/33 | 7.3 | 0.0 |
| Standing | 0/97 | 0/97 | 0.0 | 0.0 |
| Fidget | 44/82 | 0/82 | 3.4 | 0.0 |
| Taunt | 9/44 | 0/44 | 1.0 | 0.0 |
| AttackMelee | 30/44 | 16/44 | 7.7 | 7.6 |
| AttackMelee2 | 34/44 | 29/44 | 8.2 | 4.1 |
| AttackRanged | 17/53 | 11/53 | 5.3 | 1.9 |
| Hit | 33/45 | 19/45 | 9.1 | 2.3 |
| Death | 37/58 | 20/58 | 7.8 | 9.6 |
| Dead | 0/49 | 0/49 | 0.0 | 0.0 |
| ResurrectSpell | 13/66 | 0/66 | 1.0 | 0.0 |
| Resurrect | 86/106 | 44/106 | 12.3 | 19.6 |

Plates against the approved build (`scripts/skirt_plate_gate.py`, `review/skirt/plate_gate.json`): hem acceleration Walking p95 21.5 -> 14.5, max 63.4 -> 28.5 mm/f2; Running 54.2 -> 42.0, max 102.0 -> 56.0: smoother. AttackMelee max 87 -> 221, Hit 17 -> 64, Fidget 6.6 -> 21: worse, still low-passed.
Reversals of the hem per clip Walking 4 -> 6, Running 6 -> 8: one rise per leg per cycle, no flutter in the shots.

**Costs, stated plainly**: rigid plates part where the approved skinned field kept them joined: largest neighbour opening Walking 1.2 -> 19.0 cm, Running 1.3 -> 22.6, up to 26.7 in Hit. The brief asked for no more separation than before; the thigh has to come out somewhere, and in the shots it now shows between plates
instead of through one. The walking silhouette is a little wider and the side plates show more of their dark lining. Arm gate, frames over 1 cm: AttackMelee L 3 -> 6, Hit L 0 -> 2, Death 4/3 -> 8/6 (the raised plates meet the hands; fast clips). Deepest values got worse in two clips: Resurrect 12.3 -> 19.6 cm (script clip, half the frames) and Death 7.8 -> 9.6 (a few frames of the fall, half the frames). In Death the front plate rides up with the raised legs and shows its lining.

Gates on the final build: `check_winding.py` 0 inverted; flat shading 0.01; `floor_audit.py` ok; `run_creature_review.py check` 78 switches, 0 errors; `mm9_actor_models_build_every_binding` PASS, 78 descriptors on 37 models; `--headless-validate-actor-models` 0 refused.
`detached_parts_audit.py` (24 fps, `review/skirt/detached_audit.md`): the 8 helmet false positives as before, plus 3 plate groups new (`Skirt_front` 114 mm, `front_R` 94, `front_L` 92, "base lifted") in 8 of 391 poses, all one-shots (Death, AttackRanged); none in Walking or Running. The plates hinge at the belt, so their tops stay on it; the flag is the base against their bind neighbours.
Viewer `v2h-skirt-20261030` also carries `lod1_c`, `lod1_b` (LOD1 as the main mesh) and `before_c`, `before_b` for comparison. Sheets, viewer shots at identical cameras, front, side and 3/4: `review/skirt/cmp_master_walk.png`, `cmp_master_run.png`, `cmp_warrior_walk.png`, `cmp_warrior_run.png`, `cmp_lod1.png`, `other_clips.png`; numbers `review/skirt/gate_before.txt`, `gate_after.txt`, `plate_gate.txt`.
Rebuild: `TOKEN=<lease> scripts/rebuild.sh --install`; it needs `work/before_skirt/` (the approved GLBs are the reference for the plate fit and the death root). Keep it.

## Handedness (MM9 ABC conversions are mirrored)

Checked, not assumed (`scripts/handedness.py`, `review/handedness.txt`). `convert_abc_model.py` keeps LithTech's left-handed numbers
in right-handed glTF: the raw GLB faces +Z with `Bip01 R Hand` at x +0.377, the figure's anatomical LEFT. MM9 names its bones
anatomically, so the raw conversion holds the scimitar in the left hand and throws with the right. Every other MM9 GLB
shares this; only bodies with a held weapon or shield show it.

`scripts/mirror_source.py` fixes it at the source: `source/war*/skelwar*_true.glb`. World bone motion D(t) = W(t) W(rest)^-1 is
mirrored onto the partner bone (S D S), locals rebuilt, L/R names swapped, weapon bone and scimitar moved across. Rest frames stay
MM9's, so `clips_mm9.py` copies rotations as usual. Final GLB: faces +Z, `Bip01 R Hand` at x -0.343, scimitar under `Bip01 R Hand`, the
throw from `LHand1` at +x. Not the Imp's route (`mm9_imp_claude/scripts/mirror_glb.py` mirrors the finished GLB); same result. Verified
against the mirrored raw clip in `review/mm9/mir/cmp.png`.

## Route

0. **HD masters** (`references_hd/`, Codex via `codex_slot.sh`, two runs) from MM9 model renders without the scimitar: A-pose, five-finger gauntlets.
   Gate: true alpha, three horns, red eyes, open jaw, bare waist, correct sides. `references_head/` (Codex): bare skull plus four helmeted busts.
   `references_prop/`: the flat scimitar.
1. **Smart Topology** gave 66 clean separate parts: bones, armour plates, helmet shell and guards, skirt plates, five-finger gauntlets. As on MM6 it gave a
   human-looking face, so a skull-only Smart Topology (cranium, separate mandible, 29 separate teeth) replaces face and jaw.
2. **Parts** (`scripts/sym_parts.py`): reduced per part to fixed targets, right-side parts mirrored over the left (MM9 is symmetric; Meshy's pairs
   were within 1-3 cm) except the skirt, whose mirrored half left slits. Cranium's hidden crown and back cut and capped. Eye spheres set in the sockets.
3. **Fit** (`scripts/fit_skelwar.py`): joints where the pieces meet (shoulder at the humerus top, elbow in the elbow cap, wrist at the gauntlet, hip at the femur
   head, knee at the condyles, ankle on the shaft line), pieces rigid on one bone. Spine and neck columns blend, boots blend round the ankle, the skirt follows one field of
   height and side (belt to thighs, 0.8 at the hem). Then each piece turns onto the MM9 bone direction about its joint (MM9's legs slant back, its torso forward: torso 9.8 deg,
   legs 7-14, arms 9-12, hand 29 so the knuckle line lies on MM9's handle): left alone, that rest offset stays in every clip. The HD pose stays in `fitco`, for the upload.
   Fingers by connectivity (as `../mm6_gob2_claude/scripts/fit_fingers.py`).
4. **UVs** (`scripts/uv_skelwar.py`, `uv_atlas.py`, on the HD pose): twins share texels; hands 1.4x denser. Never re-run: the paint belongs to this layout.
5. **4K retexture** of body (four HD masters) and head (four busts), AO on the uploads, `compose_texpass.py`, gentle grade with saturation 1.0, then `scripts/tone_skelwar.py`.
6. **Finish** (`scripts/finish_skelwar.py`, shares existing texels, so no new paint): needle vertices the decimation left, eye subdivision, coincident dark lining on open plates (the
   Yrsa sleeve lesson), hip bars (Meshy has no pelvis), scimitar on `Bone01` (`scripts/scimitar_mesh.py`: pillowed plate from the master's alpha, 266 triangles, MM9's handle
   direction and blade plane), fist solved per finger round the handle (`work/hand_poses.json`).
7. **Clips** (`scripts/clips_mm9.py`, `roles_skelwar.json`, `finger_keys.py`): MM9 local rotations. `root_lift` 1.0559: MM9's clips stand on the floor while its bind centres on the pelvis, so without it
   every clip carried the lift twice. `thin_keys`: MM9's keys hold then jump, a stop-start the curves keep, so repeated keys are dropped; `work/skelwar_clips_raw.glb` keeps the untouched timing. Finger bones
   hold poses (grip, relaxed); in AttackRanged the left hand closes and opens at the release.
8. **Runtime** (`scripts/build_runtime.sh`): prepare, LODs, shadow fix, region variants, `drop_tier_ramps.py`, floor, eye emission, winding.

Rebuild after the paid steps: `TOKEN=<lease> scripts/rebuild.sh --install`, then `scripts/viewer_tiers.py`, `scripts/make_viewer_manifest.py`. PYTHON: `claude_shared/gltf_venv/bin/python` by that path.

## Tiers and MM9 visual properties

- **Master** = the paint itself: its materials carry no ramps, because a luminance ramp flattened the lacquer by 15 levels (`work/ramps_report.json`). They share every image with the Warrior.
- **Warrior**: region mask + ramps (`scripts/tier_ramps.py`): R lacquer and insignia, G lacing, B eyes, A horns. Colours are MM9's WAR2 skin at the texels where WAR1 is red or blue, matched by luminance rank.
- Skins are opaque (`Transparent 0`; alpha 255 throughout). Eyes: emission mask from the paint, red / amber, pulse 0.12 over 3.1 s (a gain: MM9 paints them).
- `FX0 bluedots` (Master) and `ResurrectFX`: not wired. The MM9 clips exist as script clips, but no behaviour drives them.

## Checks (final GLB, viewer `v1g-20261030`)

| Gate | Result |
|---|---|
| `run_creature_review.py check` | 26 switches, 0 console errors |
| Regression `mm9_actor_models_build_every_binding`, `--headless-validate-actor-models` | PASS, 73 descriptors on 35 models, 0 failed, 0 refused |
| `check_winding.py` | 0 inverted closed parts |
| `floor_audit.py --match 'MM9 Skeleton Warrior*'` | ok: stand 0, walk +/-0.8, living -0.8, dead 0 world units |
| `flat_shading_check.py` | 0.01 body and head; scimitar 0.27 (flat blade by design) |
| `texture_quality.py` | body atlas 67.3 %, fragments 0.4 %, stretch 1.13; head atlas 64.4 %, fragments 1.2 %, stretch 1.10. Its density spread is meaningless here: lining faces collapse to a texel (real: body 1,157 px/m, hands 1,614, head set 2,620) |
| `arm_hand_gate.py --outer-only --exact` | 0 hand frames over 1 cm except AttackMelee L 5.9 cm (3 frames), Death L 6.0 (4), R 5.8 (3), Resurrect R 6.0 (28, script clip, rising); finger stretch max 1.78, 3.63 in the throw's fist |
| `jitter_gate.py` against raw MM9 keys | hand acceleration and angular velocity at or under MM9's, with a few within 7 % over (AttackMelee2 L, Hit L, Walking L angle). The gate itself reports 22 fails on its per-frame shoulder "excess": the gate compares frame by frame with the raw keys, and dropping held keys moves motion between frames by design. `review/hand_smooth.txt`: hand acceleration p95 Walking 55.7 against 71.2, Fidget 16.2 against 20.9 |
| `detached_parts_audit.py` | see below |

Detached audit (`review/detached_audit.md`, final GLB at 24 fps; 48 fps gave the same parts plus two skirt plates for one frame each in the script-only Resurrect): 8 of 98 parts flagged, all helmet guard plates
or their linings on `Bip01 Head`, "base lifted" up to 156.5 mm. Their base is judged against the cuirass they rest on at bind, which the head then leaves. They are rigid on the same bone as the helmet shell, and
`scripts/helmet_contact.py` puts each within 1.5-9.7 mm (nearest vertices) of a neighbouring helmet piece, a gap no clip changes: false positives. No bone, joint or limb piece is flagged; femurs, humeri and forearms stay rooted (shallowest listed in the report's "only just attached").

Sheets (viewer shots): `review/mm9_vs_ours.png` (MM9 renders against viewer shots, both tiers, seven poses), `review/sheet_tier_master.png`, `review/sheet_tier_warrior.png`, `review/sheet_closeups.png`, `review/sheet_faces.png`, `review/sheet_collar.png`. Reports: `review/arm_hand_gate.txt`, `jitter_gate.txt`, `detached_audit.md`.

## Deviations and open points

- **Head set is 2K colour**, as Yrsa, Forad and Annud ship, not the brief's 1K: 2,620 px/m on the face.
- **Hands**: the design's five-finger gauntlets from Meshy's own mesh, not grafted MPFB hands; 15 bones per side. MM9's hand is a rigid mitten (one thumb key, in die2), so MM9's curl has nothing to drive: they hold poses.
- **Scimitar stays in the body GLB** as a third material, rigid on `Bone01`, not a split attachment. Its texture uses 7.6 % of the master image.
- **Warrior's armour**: MM9 paints plain black mail where the Master has lamellar; here the lamellar pattern stays, dark. Its brow insignia reads silver; MM9 has none. A separate base colour would match better.
- **Ribs**: the master's lowest ribs under the cuirass were not modelled by Meshy; MM9 shows them at the back.
- Skirt: see "Skirt fix". MM9's plates do not move at all.
- Running stride 3.4 m is MM9's `RunVelocity` x clip length, not a planted-foot measure (feet planted 5-7 % of the cycle). Running's root keeps per-key floor raises: pelvis acceleration 48 against 29 mm/f2 without them.
- Unused MM9 clips: search, fidget2, the OLD attacks, wince2, die2, BackPedal, BackPedalRun.
- **Not checked**: in game (`tools/run_game.sh --isolated` fails its save_game preparation on current `assets_dev`, as the Dagrell README records, and I did not build a private mirror); LOD1-3 and shadow meshes by eye; normal-speed playback by eye (frames and numbers only); the fit of thrown projectiles at `LHand1`.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_skelwar_reduce_claude/`** (user-approved; ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `mm9_skelwar_reduce_claude/before/`.
