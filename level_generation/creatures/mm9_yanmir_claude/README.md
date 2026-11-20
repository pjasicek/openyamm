# MM9 Yanmir body (mm9_yanmir) — 3D actor, 2026-10-31

MM9 `YANMIR.abc` (39 nodes, 20 clips, 798 triangles, pieces staff/head/body on one 512 skin `YANMIR.dtx`): row 206 Yanmir L70
(`MM9 206 Yanmir`), the frost giant king and boss of Yanmir's Fort. One row, one skin: no tiers.
**Humanoid route** (MM9 skeleton, MM9 clips, grafted five-finger hands, head-only Meshy model), with MM9's stride bind taken by
re-resting (as `mm9_highwayman_claude`), a staff built from MM9's stations in the right fist and a procedural ice crown.
Run 2 body, built in one session (overnight-yanmir).

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_yanmir.glb` (`tools/install_model.py --world mm9`) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, block `# >>> mm9_yanmir_claude`: `MM9 206 Yanmir`, scale 333.333 (the model is 0.3 x MM9 size, as `mm9_giant_claude`), `yaw_offset` -1.570796327, stride walk 1.46 / run 1.77 (planted left foot), melee impact 0.603 s (`HAttack1` lkick, a stomp), ranged 0.405 s released at `cast_hand` = `Ystafftop` (MM9's RangeAttack socket node: the staff's head), look Neck + Head, upper body `Bip01 Spine2` |
| Triangles LOD0/1/2/3 | 14,514 (skin 11,772 + staff 1,864 + crown 728 + eyes 150) / 7,238 / 2,603 / 866 |
| Skeleton | MM9's 39 nodes, joints moved onto our mesh, rest frames = MM9's turned by the least rotation onto our limbs (`rig_yan.py`), + 16 half-rotation helpers `*_h` + 30 finger bones |
| Clips (30 fps) | All 20 of YANMIR.abc's clips + Death/Death2 from MM9's Giant + Dead (23). Bound: Standing `stand`, Walking `walk`, Running `run`, Fidget `fidget1`, AttackMelee `HAttack1`, AttackRanged `Rattack1`, Hit `wince1`, Death (Giant `die1`), Dead. `script_clips`: attack2 `Hattack2`, attack3 `StepOn`, ranged2 `rAttack2` (EQAttack), fidget2, taunt, wipe, kick_door `KickDoor`, hit2 `wince2`, death2 (Giant `die2`), start_die `startdie`, fall `fall` (loop), die_standing `Die`, attack_save `Hattack1Save`, ranged_old `rAttack1Old`. None left out |
| Textures | body 2K colour + 1K normal + 1K ORM (Meshy metallic for the silver); head 2K colour + 1K normal + flat ORM; accessories (staff, crown) 1K colour/normal/ORM from one Codex sheet. 9 images |
| Meshy credits | **20 / 30**: body Smart Topology 5, head-only Smart Topology 5, body 4K retexture 10 |

## Route (`scripts/`)
0. `convert_sources.sh`: `convert_abc_model.py --scale 0.00768` (0.3 x MM9, like the giant) in raw ABC space, `mirror_glb.py` -> `source/true/yanmir_true.glb`. The bind is asymmetric (right leg stepping forward with the heel up, right arm bent round the staff), so no `mirror_source.py`.
1. Masters: `make_refs` renders (`ref_renders.py`, `input_sheets.py`), `codex_masters.sh` 1 and 2 (`references_hd/00-04`, arms 35 deg out of the body), head clay sculpt `codex_head.sh` (`references_head/00_geometry.png`, no crown: the crown is a part).
2. Meshy: body and head-only Smart Topology. The body came back as 28 layered shells (torso, legs, mantle, belt, bracers, plates, sleeves, head pieces).
3. `fit_yan.py` (left half mirrored; x and y x 2.55, z mapped through MM9's left joint heights: MM9's legs are 1.35 x longer against the torso than Meshy's), `head_prep.py`, `face_npz.py` (head placed by the eyes), `combine_shells.py` (Meshy's own head and beard shrunk inside the new head), `wrap_bf.py` at 4 mm with 3-voxel closing, `body_close.py` (remesh, projected back on the shells, 150k): one closed skin, new head included. A Boolean union failed on the voxel body's self-intersections (1,580 multi-face edges), so the head goes in through the wrap.
4. `rig_yan.py` (joints onto the mesh, MM9 frames turned onto our limbs, bone heat; head rigid above a forward-tilted neck plane; the beard on `Ponytail1`, which is where MM9 weights its beard), `step_b.sh` (MPFB hands, 15 finger bones per side, `wrist_weld.py`), `quick.sh` (`weights_fix_yan.py`, `helpers_yan.py`, `reduce_yan.py` with the fingers protected), `q2.sh` (`sym_bf.py`, `mesh_clean.py`, quick clips, collapse).
5. `uv_yan.py` (never re-run: the paint belongs to `work/uv_v1.blend`), Meshy retexture 4K of the body (head faces collapsed), `texpass_bake_ao.py`, `compose_yan.py`, `grade_basecolor.py`, `tone_match.py` (skin toward MM9's value and saturation).
6. Head: `head_clay.py`, `codex_heads.sh` (five views painted on our clay), `project_head.py` (eyes, nose, mouth from the front view alone), `raster_pos.py` + `eyes.py` (eyeballs painted from their own 3D position, pale ice-blue), `tone_match.py`.
7. Staff and crown: `make_staff.py` (MM9's stations: 2.5-unit shaft (8.4 m in game), three silver blades, octahedral gem; 2.2 cm up its axis so the foot meets the floor), `make_crown.py` (band 6 mm proud of the hair, V plate, 12 ice spikes), `compose_acc.py` (Codex sheet `references_acc/acc_sheet.png` re-cut into the atlas the two parts use), `fist_yan.py` (right fist: wrist turn lining the knuckles up with the shaft, each finger's three joints solved to wrap one cylinder of the shaft's radius plus its own thickness, staff shifted onto that axis), `attach_crown.py`, `spikes.py` (wrap notches on the mantle's back), `nape_relax.py`, `tunnel_close.py` (all in `parts_chain.sh`).
8. `scripts/textures_all.sh` (after the AO bake; ends with `seam_blend.py`: body texels within 3.5 cm under the neck cut take the head paint mirrored across it, and the throat behind the beard the beard's paint). `scripts/parts_chain.sh` (fist, crown, spikes, nape, `tunnel_close.py` -> `work/parts_r4.blend`).
9. `REV=rN scripts/rebuild.sh --install`: `export_yan.py`, `head_pivot.py` (6 cm back, 2 cm up), `clips_mm9.py` (soft joint-offset line; roles `roles_yan.json`; sources `source/true/yanmir_plus.glb` = YANMIR + `giant_deaths.py`), `finger_keys_yan.py` (fist held in every clip; the wrist turn taken back out of Ystaff's keys so the staff keeps MM9's frame), `staff_floor.py` (the staff tips over onto the floor in the falls instead of piercing it), `head_twist_cap.py` 28/40 deg, `arm_out.py` 6 deg left arm only, `half_keys.py`, `hand_clear_keys.py`, `half_keys.py`, prepare, LODs, shadow fix, `floor_fix.py`, winding, install, viewer.
10. Binding: from the repo root, `flock level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock python3 level_generation/creatures/mm9_yanmir_claude/scripts/bind_actors.py 1.46 1.77`. Gates: `scripts/gates.sh`. Sheets: `strip_shots.sh` + `strip_sheets.sh`, `closeups.sh`.

## Checks
Final build r4 (installed 2026-10-31). Numbers in `review/gates/`; r4 copies of jitter/collapse/arm also in `work/*_r4.txt`.

| Gate | Result |
|---|---|
| Handedness | raw ABC: R on the anatomical left; source and runtime: right (`review/gates/handedness.txt`); the staff in the true right hand |
| Bones (`bone_length_audit.py`) | runtime 0 of 12 stretching. MM9's raw clips stretch both thigh offsets 0.183-0.247 m natively; `clips_mm9.py` ORBIT keeps ours constant |
| `detached_parts_audit.py` | body (11,772 tris skin, crown, eyes): **0 detached**. Flagged: the staff's parts, which are held, not joined: 7.3 cm from the fist in Running (MM9 slides its staff 23 cm through the hand there) and 29 cm in `AttackMeleeSave` (MM9's unused Hattack1Save swings the staff 67 cm out of the hand) |
| `flat_shading_check.py` | 0.00 on all three materials |
| `check_winding.py` | 0 inverted closed parts |
| `texture_quality.py` | body atlas **60.4 %**, spread 1.07, fragments 0.5 %, stretch p90 1.16 (all targets met); head atlas 65.0 %, spread **1.78** (over 1.3: the face is packed 1.7 x denser on purpose), stretch 1.08; accessories: a tiled atlas (wood and silver repeat), not comparable |
| Floor (`floor_audit.py --match 'MM9 206 Yanmir'`) | ok: stand 0, walk 0, living -0.3, dead 0 (tolerance 2.5) |
| Regression `mm9_actor_models_build_every_binding` | **PASS, 150 descriptors on 60 models, 0 failed** (after the r4 install) |
| `run_creature_review.py check` | 23 clips switched, 0 failed, 0 console errors |
| Faces | `review/sheet_heads.png` (front, quarter, side) and `review/sheet_heads_b.png` (other quarter, back), read at full size: one pair of eyes, one nose, one mouth, beard continuous to its tip |
| In game | Yanmir's Fort from the review root (`yanmirsfort.blv`, `--isolated`, immortal): the map's own Yanmir in his doorway and a spawned friendly one, front and back (`review/ingame_sheet.png`, `review/ingame_r2_sheet.png`; frames `review/ingame_r4/`, `review/ingame_r2/`); he fights (ice bolts at the party) |

**Arm and hand (`review/gates/arm_hand_skin.txt`, skin, outer faces, exact): passes in 22 of 23 clips.** Death2 (script clip, the Giant's die2 to the knees) fails: left hand 3.5 cm for 4 frames, right forearm 6.0 cm at its last frame (the arm under the body on the ground). `hand_clear_keys.py` fixed 9 contacts (Fidget2 3.7, Wipe 8.5, AttackMelee/StepOn 13.6, AttackRanged2 13.1, Death L 9.6 / R 12.1 cm -> 0); Death2 L 10.7 and R 6.7 cm have no solution under the speed cap. Finger stretch p99 1.1-1.8, max 3.4-7.1 (left, MM9's finger curl on the MPFB chains) and 4.6 (right fist). Wrist max 82 deg (Death2), MM9's own.

**Held staff (`review/gates/staff.txt`):** the staff against the body: 0 cm in every clip except `AttackMeleeSave` (4.0 cm in the left thigh: MM9's unused swing) and Death 0.6 cm (head). Grip (Standing): finger skin 0.26 cm inside the shaft at most (45 vertex samples), fingers wrap 120-150 deg each, thumb 15 deg (it rests beside the shaft, not over it). r2 had the shaft beside the fist (1.4 cm in, thumb 0); r3's circle fit put it through the proximal phalanges (1.9 cm); r4 solves each finger round the same cylinder (`fist_yan.py`).

**Beard (`review/gates/beard.txt`, Ponytail1 skin against the rest): 5.8-6.0 cm "inside" in every clip, Standing included.** The wrap closed the beard's tip onto the chest and mantle as one surface, so the gate reads the joined skin as inside; not a beard going through the chest in motion. Not fixed.

**Jitter (`review/gates/jitter.txt`, 48 fps, against MM9's clips with the same fist, staff fix and helpers): FAILS as defined, 7 flags, all left arm:** AttackMelee / StepOn upper arm +1.52 deg/f, shoulder skin 5.84 mm/f2; AttackRanged2 +1.79 deg/f, 8.12 mm/f2; AttackMelee2 / KickDoor +0.59 deg/f, 4.09 mm/f2 (the constant 6 deg abduction on MM9's fast frames); Death +1.19 deg/f; Death2 +0.40 deg/f, 2.45 mm/f2. Relative reading (`--rel 0.25`): **1 flag** (Death L). Second attempt (`work/j5_*`): no abduction and the hand-clear speed capped at 0.7 deg/f gave 3 flags (AttackMelee, StepOn, AttackRanged2) but left the hand 9.6 cm in the body in Death and 0.4 cm in Standing, so r4 was kept. r2 had 14 flags (both arms abducted 8 deg).

**Collapse, worst single frame per clip and region** (`review/gates/collapse.txt`, all LOD0 primitives, 30 fps). Not zero:

| Clip | face-frames | worst frame (largest regions) |
|---|---|---|
| Standing | 1872 | finger 23 wrist_R 10 elbow_R 1 shoulder_L 1 |
| Walking | 1462 | finger 24 wrist_R 11 torso 5 shoulder_L 4 hip_L 3 |
| Running | 1248 | finger 33 head 15 wrist_R 10 shoulder_L 8 wrist_L 8 |
| Fidget | 4396 | finger 63 head 16 wrist_L 12 wrist_R 12 shoulder_L 4 |
| Fidget2 | 8336 | head 41 finger 32 wrist_R 11 wrist_L 8 shoulder_R 6 |
| Taunt | 2137 | finger 63 wrist_L 14 wrist_R 12 head 10 torso 6 |
| Wipe | 9777 | finger 72 head 71 neck 39 hip_R 19 hip_L 16 |
| AttackMelee | 2407 | finger 29 head 17 neck 14 hip_L 11 wrist_R 11 |
| AttackMelee2 | 1471 | finger 24 head 19 wrist_R 10 knee_R 5 shoulder_L 5 |
| StepOn | 2407 | finger 29 head 17 neck 14 hip_L 11 wrist_R 11 |
| AttackRanged | 1331 | finger 38 wrist_R 11 wrist_L 10 torso 5 shoulder_L 3 |
| AttackRanged2 | 2625 | finger 29 head 18 neck 14 hip_L 11 wrist_R 11 |
| AttackRangedOld | 2125 | finger 63 head 17 wrist_L 12 wrist_R 12 shoulder_L 4 |
| AttackMeleeSave | 2990 | head 35 finger 23 wrist_R 14 neck 13 body 6 |
| KickDoor | 1471 | finger 24 head 19 wrist_R 10 knee_R 5 shoulder_L 5 |
| Hit | 1678 | finger 23 wrist_R 10 neck 4 shoulder_L 2 hip_L 1 |
| Hit2 | 1421 | finger 23 wrist_R 10 hip_L 2 elbow_R 2 shoulder_L 2 |
| StartDie | 2509 | head 56 finger 23 torso 12 wrist_R 11 shoulder_L 9 |
| Fall | 2539 | head 64 finger 18 torso 13 wrist_R 10 shoulder_L 9 |
| Death | 5613 | head 27 finger 23 wrist_R 12 hip_L 10 hip_R 10 |
| Die | 1421 | finger 23 wrist_R 10 hip_L 2 elbow_R 2 shoulder_L 2 |
| Death2 | 7439 | head 85 hip_L 72 hip_R 36 neck 27 finger 23 |
| Dead | 3038 | head 24 finger 19 wrist_R 11 hip_L 9 knee_L 7 |

Worst: Death2 hips 72/36 and head 85 (the Giant's kneel and head drop: script clip); head 56-71 in StartDie, Fall, Wipe (MM9 throws the head back: the nape under the long hair compresses); finger 63-72 in Fidget, Taunt, Wipe (knuckle faces under MM9's full curl). Changes made for it: head pivot 6 cm back, 2 cm up, twist cap, nape relax: Fidget2 head 107 -> 41, StartDie 103 -> 56, Death 73 -> 27. Hair resting on the back (`hair_rest.py`, tried) made StartDie and Death2 worse and was dropped.

Sheets (r4, viewer, all read): `review/mm9_vs_ours.png` (MM9 bind with staff vs ours Standing, four views), `review/sheet_heads.png`, `review/sheet_heads_b.png`, `review/sheet_hand_staff.png` (fist from three sides, staff head), `review/sheet_closeups.png` (knees, groin, armpits, elbow, neck, head in the crouch `AttackMelee` 0.55 s, the kneel `Death2` 1.0 s, the fall `Death` 1.2 s and `Dead`), `review/sheet_strips_1.png`, `_2`, `_3` (all 23 clips, six frames each), `review/ingame_sheet.png`.

## Decisions and deviations
- **Death:** MM9 has no lying death for Yanmir. His trap death is `startdie` (the floor breaks) -> `fall` (looped in the air) -> the pit, and `Die` ends standing. The engine needs a corpse, so Death/Dead are MM9's own Giant `die1` (falls forward on his face) and Death2 the Giant's `die2` (to his knees), retargeted by world orientation onto YANMIR.abc (`giant_deaths.py`: every bone points where the Giant's does). Yanmir's own three death clips are kept as script clips for a scripted trap.
- **Re-rest instead of posing the mesh:** MM9's bind is a stride with the right arm bent; the mesh stays in Meshy's A-pose and each limb bone takes MM9's frame turned onto our limb, so MM9's local rotations still give MM9's world rotations.
- **Proportions:** MM9's legs are long against the torso. Ours: x/y scaled to MM9's widths, legs stretched in z to MM9's hip, knee and ankle heights (`fit_yan.py`).
- **Staff:** built, not painted by Meshy: MM9's three-bladed head and gem, a round shaft (MM9's is square). Shaft radius 1.95-2.35 cm so the MPFB fist closes round it; the staff is rigid on Ystaff (MM9's Ystafftop/Ystaffbot never move against Ystaff). MM9 plants its foot 2 cm (6.7 game units) into the floor; ours sits 2.2 cm higher up its own axis.
- **Crown:** a separate rigid part on Head with its own texture, so the head paint has a single layer (face, hair, beard) and needs no occlusion between layers.
- **Hair and nape:** the long hair is on Head as in MM9; its lower rim at the back folds when MM9 throws the head back or turns it. Head pivot moved 6 cm back and 2 cm up, head twist capped 28/40 deg (Fidget2 turned 60 deg -> 40), nape weights relaxed: collapse head 107 -> 39 (Fidget2), 103 -> 57 (StartDie), 73 -> 25 (Death).
- **Tone:** the Meshy paint was bluer and darker than MM9 (saturation 0.41 / value 0.58 against MM9's 0.34 / 0.63); `tone_match.py` brought skin texels to 0.35 / 0.62 (head 0.36 / 0.62).
- **Size:** the model is 2.88 units tall at 0.3 x MM9 scale; scale 333.333 gives 961 game units, the descriptor height 957.

## Open points
- Jitter as defined (7 flags, left arm) and Death2's hands, above. Collapse at the nape in head-back clips and the Giant's kneel.
- The beard's tip is joined to the chest skin (the wrap); the beard gate reads it as inside.
- The thumb does not close over the shaft (15 deg wrap); fingers wrap 120-150 deg.
- Neck sides between the hair and the mantle show bare blue skin with a smooth, slightly smeared paint (the throat under the beard was pulled forward to close a see-through tunnel, `tunnel_close.py`).
- The fur mantle's necklace disks are painted by Meshy as black disks with white dots; MM9's are dark silver knotwork. Small slivers at the brown sleeve bands' lower corners.
- MM9's Giant die1 (our Death) has the body leave the floor for a moment at 1.8-1.9 s (the Giant's own stagger, 15 cm at our scale, about 50 game units).
- The staff is round and silver-white; MM9's is a square, mottled pole.

## Not checked
- Playback at normal speed (agents cannot watch video): every clip read in six-frame strips and stills only.
- Orientation gate not run (humanoid head and feet follow MM9 by construction of the re-rest). LOD1-3 by eye. Sounds, the ice-bolt launch point from `Ystafftop` and the melee impact moment in game. The trap death (start_die / fall) driven by a script: nothing plays them yet. Android cook.
- In game only in Yanmir's Fort's first hall at one camera; not seen walking or dying in game, nor from above.


## Follow-up r5 (coordinator's short pass, 2026-10-31, 0 credits)
- **Staff to MM9's:** `make_staff.py` v2: a thick pole (r 3.4-3.8 cm, MM9's square is 7.0-8.4 cm across) in MM9's speckled grey-brown
  (Codex tile `references_acc/v2/pole_tile.png` from MM9's own staff renders `references_acc/v2/mm9_staff_views.png`, via `codex_slot.sh`),
  and a tulip cup of four knotwork petals bound by a silver ring round the green gem, as MM9's head. `compose_acc.py` takes the tile.
- **Thumb over the shaft:** `fist_yan.py` solves each finger round the thick pole with the pole lying in the palm, and the thumb's tip onto
  the index finger's last phalanx: thumb wrap 15 -> 90 deg (Standing), fingers 60-120 deg, finger skin 0 cm inside the pole (r4 0.26).
  Read from the palm side: `review/sheet_fist_palm.png` (the thumb lies across the pole), `review/sheet_hand_staff.png`.
- **Back of the head:** `hair_widen.py` widens the back hair 1.30 x toward its foot (a block to the shoulders, as MM9's) and
  `hair_contrast.py` raises contrast and blue in the head set's own paint behind the ears (one paint source). Read at full size:
  `review/sheet_heads_b.png` (both rear quarters and the back), `review/sheet_heads.png` (front, quarter, side: one pair of eyes, one nose, one mouth).
  Cost: head texture spread 1.78 -> 1.94, stretch p90 1.08 -> **1.64 (target 1.5)**: the widened hair stretches its frozen UVs 1.3 x across.
- **Necklace disks:** `disks_silver.py` (texel mask in the collar band + dark-silver ramp by luminance, ORM metal 0.85, roughness 0.38).
  Visible as dark silver with bright studs; the knotwork itself is not there (Meshy painted dots).
- **Death2 hands:** not fixed. `hand_clear_keys.py` with the speed cap raised to 2.0 deg/f still found no solution for L 10.7 / R 6.7 cm
  (the Giant's kneel puts both arms under the torso); left as is (script clip).
- **Gates r5:** regression PASS 150/60/0; viewer 23 clips 0 failed; floor ok; winding 0; bones 0 stretching; flat 0.00; arm-hand unchanged
  (22/23, Death2 L 3.5 cm, R forearm 6.0 cm); jitter unchanged (7 strict, 1 relative); collapse lower in every clip (Standing 1,872 ->
  1,157 face-frames, Walking 1,462 -> 914; worst Death2 hips 72/36 unchanged); staff vs body 0 except `AttackMeleeSave` 6.0 cm (was 4.0:
  the thicker pole) and Death grip 1.96 cm into the pole while the hand turns; detached: body 0, the gem (8 tris) floats free in the cup by design.
  Sheets r5: `review/mm9_vs_ours.png`, `review/sheet_heads.png`, `review/sheet_heads_b.png`, `review/sheet_hand_staff.png`,
  `review/sheet_fist_palm.png`, `review/sheet_strips_1-3.png` (strips 2 read). Closeups and in-game not redone in r5.

User artistic acceptance: not recorded


**LOD0 reduced post-install on 2026-11-05 by `level_generation/creatures/mm9_yanmir_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_yanmir_reduce_claude/before/`.
