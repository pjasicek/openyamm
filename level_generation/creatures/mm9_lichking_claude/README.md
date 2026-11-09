# MM9 Lich King (mm9_lichking) — 3D actor, 2026-10-31

Monster row 209 Lich King L65 (`MONSTERS.txt`, descriptor `MM9 209 Lich King`), `LICHKING.abc` with skin `LICHKING1.dtx` and its
staff piece `staff2` on `LICHSTAFF.dtx`. Built on the MM9 humanoid route ([brief](../claude_shared/MM9_HUMANOID_BRIEF.md)): MM9 skeleton and
MM9 clips, never Mixamo. **`LICHKING.abc` does not share the Lich's skeleton or clips** (36 nodes against the Lich's 49, its own 19 clips,
no left `Hand` bone, four toe bones per foot, a staff bone), so the Lich's rig, clips and cloth scripts do not apply; its skull, look and
eye glow do (below). The route and most scripts come from `mm9_evilsorcerer_claude` (raw ABC space, numpy rig, A-pose bind).

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_lichking.glb` (`tools/install_model.py --world mm9`; cooked copy in `assets_dev`) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, block `mm9_lichking_claude` (`scripts/bind_actors.py` under the flock): `scale: 135` (100 x MONSTERS Scale 1.35), `yaw_offset: -1.570796327`, stride 0.65 / run 1.55, `skin: lichking` |
| Triangles LOD0/1/2/3 | 14,861 / 7,428 / 2,671 / 889. LOD0: torso shell with coat 2,794, boots 1,568, hands 1,500, skull 3,000, crown 716, pants 832, upper arms 796, tabard 668, buckle 380, bracers 340, medallions 918, collar wings 240, collar 178, staff 260 + staff skull 439, crown cap 84, tube caps 148 |
| Skeleton | 36 MM9 nodes (rest rotations least-turned onto our bones, clips are MM9's local rotations) + 30 finger bones + 4 tabard links `XPanelF1-4` + 14 coat hinges `XCoat{SFR,SR,BR,B,BL,SL,SFL}{1,2}` + 9 half-joint helpers; sockets `LHand1`, `RHand1`, `u1` |
| Clips (30 fps) | all 19 MM9 clips carried. Standing `stand`, Walking `walk`, Running `run`, Fidget `fidget1`, AttackMelee `Hattack1`, AttackRanged `Rattack1`, Hit `wince1`, Death `die1`, Dead; script clips Fidget2 `fidget2`, Search `search`, Aware `aware`, Taunt, ResurrectSpell, Resurrect `resurrect`, Hit2 `wince2`, Death2 `die2`, Dead2, Death3 `die1_OLD`, Backpedal, BackpedalRun `Backpedalrun`. Left out: `static_model` (the bind pose, 2 keys) |
| Events (MM9's) | `attack_melee` impact 0.479 s (Hattack1 `Rattack`); `attack_ranged` and `cast` impact 0.474 s (Rattack1 `Rangeattack`), glow `palm_left` + `staff_head`, release `palm_left` (MM9's `RangeAttack` socket is on the left hand, `Lhand1`) |
| Sockets | `palm_left: LHand1`, `palm_right: RHand1` (as the Lich's binding), `staff_head: u1` (MM9's staff socket `u1` on Bone01, at our staff skull) |
| Textures | body 2048 colour + 1024 normal + 1024 ORM + 1024 region mask (one set, one tier); head set = the Lich's skull set (2048 colour cooled to MM9's blue-grey bone, 1024 normal, ORM, eye emission mask); staff 256x1024 procedural wood (colour, ORM) |
| Meshy credits | **15 of 30**: body Smart Topology 5, body retexture 10 (4K, four Codex paint views), backup account, no retries; second pass 0 |
| Viewer | http://127.0.0.1:8912/level_generation/creatures/mm9_lichking_claude/review/viewer/ revision `r19-20261101` (staff-in-palm fix; installed r19); the model menu also holds `lichking_r13` (the r13 before the fix) for comparison |

## Route (`scripts/`)

0. **Sources**: `convert_abc_model.py --scale 0.0256` (`source/lk`, and `source/lk2` with the staff texture bound); `probe_src.py` (which bones
   move: toes never, Bone01 never against R Hand, L Finger0 up to 134 deg and 3.5 cm).
1. **Masters**: Codex five views (`references_hd/`) from MM9 renders without the staff (`ref_renders.py`, `codex_masters.sh`).
2. **Meshy Smart Topology** (5): 22 parts. `step1_clean.py` -> `assemble_lk.py`: Meshy's head, strings and duplicate hand dropped, the
   figure's right (-x) parts kept and mirrored, midline parts bisected, per-part budgets; **the approved Lich's skull** (`extract_skull.py`, its
   vertex order and UVs kept) placed in the crown. `flatten_medals.py` (domes to low reliefs about the torso surface), `move_skull.py` and
   `squash_skull_back.py` (r2/r5 skull placement inside the crown ring and under the cap).
3. **Rig**: `fit_rig_lk.py` (spine heights MM9's, legs by sections, arms by tube axes, fingers by geodesic merge levels), `refine.py`
   (rings at knees, elbows, tabard rows), `coat_hinges.py`, `grip_frame.py` (staff axis in the fist, MM9's staff axis carried by a 28.5 deg
   roll of the R Hand bind frame), `make_staff.py` (shaft, brass bands, the Lich's skull small on top, crown cap, tube caps), `heat_weights.py`,
   `weights_lk.py`, `build_glb_lk.py`.
4. **UVs**: `uv_lk.py` (body atlas, `uv_atlas.py`, frozen: `work/uv_body_v1.npz`, never re-run) and `uv_assemble.py` (skulls on the Lich's
   head set, staff, caps on a dark steel strip of the staff texture); `tuck_band.py` (r9) moves the crown's brow-band front arc 2.5 cm back inside
   the skull instead of dropping it, so its atlas charts stay filled.
5. **Paint**: `body_clay.py` -> Codex paints on our exact clay (`references_paint/`, `codex_paint.sh`) -> `make_upload.py` -> Meshy retexture
   4K (10) -> `compose_lk.py` (pad inside charts at 4K, coat lining plain dark navy, downsample once) -> AO bake (`texpass_bake_ao.py`) ->
   `finish_lk.py` (gentle grade, ORM, head set, procedural staff) -> `tone_lk.py` (region mask cloth / armour / gems + ramps).
6. **Clips**: `rig_stage.sh`: `clips_lk.py` (roles `roles_lk.json`, soft joint-offset line on the hips at 0.45 and the left wrist at 0.5) ->
   `arm_out.py` (R 8 deg, L 5 deg constant) -> `grip_keys.py` (right fist closed on the shaft in every clip; since r19 solved on the skin by `grip_solve.py`) -> `staff_lean.py` (r9: right
   hand turned 6 deg so the shaft matches MM9's in Standing) -> `half_keys.py` -> `floor.sh` -> `coat_keys.py` (tabard and coat solved per key)
   -> `head_duck.py` (r12: AttackMelee head ducks off the left hand's path; r19: Hit head turns 20 deg off the staff skull) -> `arm_stage.sh` (`arm_clear.py` + `arm_soft.py`, loops wrap;
   AttackMelee not corrected) -> `floor.sh`.
7. **Runtime**: `build_runtime.sh [--install]`: rig stage -> prepare -> LODs -> shadow fix -> region ramps -> eye emission -> winding fix ->
   sockets -> **`mirror_glb.py`** -> winding check. `viewer_update.sh`, `gates.sh`, `closeups.sh`, `strips.sh`, `tube_gate.py` review it.

## Decisions and deviations

- **Handedness**: built in raw ABC space (L at -x) and mirrored last with the Lich's `mirror_glb.py`; the staff is in the true right hand,
  the cast socket on the true left as in MM9's data (inferred from the coordinate system and names, as on the other bodies).
- **Left wrist**: MM9 has no `Bip01 L Hand`; `Bip01 L Finger0` carries the left palm in MM9 and is our left wrist bone (fingers hang under it,
  curl from `L Finger01` at 0.45/0.35/0.25). The shared gates were patched to accept it.
- **Head**: the approved Lich's skull and its paint (one paint source, no projection), cooled towards MM9's blue-grey bone, eyes red with the
  Lich's pulse. MM9's green mouth glow is not carried. A crown cap closes the open Meshy crown (MM9's is closed). MM9's two hanging side bands
  were left out (strips stand off as shards in lying poses; the crown's cheek plates read in their place).
- **Staff**: built procedurally (MM9's is a 274-triangle prop with a 128 px texture): MM9's lengths and its exact orientation in the hand (the
  roll above), shaft of dark red wood with brass bands, the Lich's skull small on top (MM9's skull is yellow-green with a hook and a feather
  tuft). r9: the staff skull keeps the head set's images but has its own material `LichKingStaffSkull` with a yellow-green ramp
  (`lk_ramps.json`) and a green eye glow; r9 `staff_lean.py` turns the right hand 6 deg so the shaft matches MM9's in Standing within
  0.6 deg (it leaned about 13 deg further across the body in r8). The R arm turns 8 deg out to bring the hand to MM9's (0.23 m from the pelvis).
- **Fist**: r1-r13 solved the finger joints 2.3-3.3 cm from the shaft axis; since r19 (2026-11-01) the staff sits in the palm and the fist is
  solved on the hand's skin (`grip_solve.py`, see the staff-in-palm section).
- **Coat and tabard**: open coat on seven hinge sectors (two links each) and a four-link tabard, solved per key against legs (gravity base,
  lying poses keep the bind shape along the body, floor clamp), smoothed on the clip's keys. Coat lining painted plain dark navy.
- **Tube ends**: upper-arm tubes, trousers and gauntlet wrists are closed by dark caps (`make_staff.py`), so a rim that leaves its cover
  shows a dark end, not a hollow.
- **One tier**: MM9 has one skin; region mask + ramps anyway (the shared-set rule), used to tone the armour to MM9's dark blue-steel.
- **Arms**: constant 8 deg (R) and 5 deg (L) outward; MM9's thin arms swing into our wider coat.
- **Texture spread** 2.6 by design (lining 0.4x, hands 1.5x, crown 1.35x, skull occluder 0.15x).

## Checks (final GLB, r7 clips; r8 changed only the crown's brow band)

| Gate | Result |
|---|---|
| `bone_length_audit.py` | 0 of 19 limb joints stretching (was 4: MM9's 6.1 cm hip slide at full strength, 12 %) |
| `check_winding.py` | 0 inverted closed parts |
| `flat_shading_check.py` | 0.02 body, 0.01 head, 0.01 staff (r8) |
| `texture_quality.py` | body atlas 54.9 % (55.3 % before r8 dropped the crown band's front arc; its charts stay empty; target 55), stretch p90 1.09, fragments 0.0 %, spread 2.61 (by design); head 66.1 % (two skulls share it), fragments 5.6 % (decimated staff skull) |
| `grip_gate.py` | every clip: finger joints 2.3 cm from the shaft axis (shaft radius 1.65), 0 inside, wrap 154 deg |
| `floor_audit.py` | stand 0, walk -0.8..+1.4, living -2.4, dead 0: ok |
| `jitter_gate.py` (corrected vs uncorrected clips) | 0 fails: arm joints, hand and shoulder skin within the uncorrected clip's own motion in every clip |
| `mm9_actor_models_build_every_binding` (`--world mm9 --headless-run-regression-suite actors`, r8 installed) | PASS, 152 descriptors on 62 models, 0 failed (`review/gates/regression_r8.txt`) |
| `run_creature_review.py check` | 21 switches, 0 failed, 0 console errors |

### Arm and hand (`arm_hand_gate.py --outer-only`, 48 fps, r7)

Hand depth into the body (coat included) 0 in Standing, Walking, Running, Backpedal, BackpedalRun, Fidget2, Search, Taunt, AttackRanged,
ResurrectSpell, Dead, Dead2 (r4: L 6.0 cm in Walking and Backpedal, R 3.8-5.9 cm). Open: Death and Death3 L forearm 3.3-3.4 cm, R forearm
3.0-4.2 cm, hands 1.6-2.4 cm (2-5 frames, the fall); Death2 hands 1.7 cm (8 and 4 frames); Resurrect R 2.5 cm (1 frame); AttackMelee L 1.6 cm
(3 frames); Fidget L 1.5 cm (1 frame). Finger stretch: left 2.53 in AttackMelee (MM9's 87 deg finger curl; 3.13 before the curl was cut to
0.45/0.35/0.25), right fist 1.82 constant.

### Coat and tabard (`cloth_gate2.py`, rays from each leg vertex towards the body, 30 fps, r7)

Legs (thighs and shins) through the coat: 0 frames in Standing, Walking, Backpedal, BackpedalRun, Aware, AttackRanged, Hit2, Dead, Dead2;
Fidget 1/43 (3.1 cm, 1 vertex), AttackMelee 6/31 (2.1 cm), Resurrect 6/55 (5.2 cm, 2 vertices), Hit 15/52 (4.1 cm). **Failed: Running
16/21 frames, up to 7.7 cm (24 vertices); tabard in Running 13/21, 7.7 cm (18 vertices)** (the raised thigh passes the swung tabard and the
front coat sectors; a solver change that counts thighs at hinge height cleared Walking but not Running). Fidget2/Search 31/91 (5.9 cm,
4 vertices), Taunt and ResurrectSpell 27-31 frames (3.9 cm, 4 vertices), Death/Death3 17/34 (7.9 cm) and Death2 47/64 (8.0 cm, 49 vertices)
in the falls. Torso against the coat: 2.2-3.1 cm, 2-17 vertices, most clips (the coat's top band at the hips; bind already 45 vertices).

### Collapse (`collapse_gate.py`, every LOD0 primitive, 30 fps, worst single frame per region, r7)

| Clip | face-frames | knee L/R | hip L/R | ankle L/R | elbow L | shoulder L/R | groin | torso | strip | finger |
|---|---|---|---|---|---|---|---|---|---|---|
| Standing | 972 | 0/0 | 0/0 | 0/0 | 0 | 0/0 | 0 | 10 | 0 | 1 |
| Walking | 770 | 0/0 | 5/3 | 1/1 | 0 | 2/3 | 1 | 17 | 0 | 1 |
| Running | 610 | 3/2 | 14/14 | 3/4 | 7 | 0/2 | 4 | 10 | 2 | 1 |
| Fidget2, Search | 1662 | 0/1 | 7/4 | 1/3 | 0 | 2/6 | 1 | 19 | 3 | 1 |
| Taunt | 1832 | 0/1 | 7/2 | 0/2 | 0 | 2/8 | 1 | 43 | 0 | 1 |
| AttackMelee | 1304 | 0/0 | 5/4 | 0/1 | 1 | 22/4 | 2 | 55 | 1 | 3 |
| AttackRanged | 585 | 0/1 | 0/3 | 0/3 | 0 | 4/0 | 4 | 14 | 0 | 1 |
| ResurrectSpell | 2035 | 0/1 | 7/2 | 0/2 | 0 | 2/7 | 1 | 44 | 0 | 1 |
| Resurrect | 1631 | 0/1 | 9/7 | 0/3 | 0 | 14/8 | 4 | 30 | 4 | 1 |
| Hit / Hit2 | 1056 / 663 | 0/1 | 6/2 | 0/3 | 0 | 3/3 | 6 | 21 | 0 | 1 |
| Death, Death3 | 1070 | 1/0 | 7/14 | 1/3 | 0 | 12/6 | 2 | 32 | 4 | 1 |
| Death2 | 3839 | 8/1 | 9/11 | 3/1 | 0 | 4/6 | 4 | 21 | 85 | 1 |
| Dead / Dead2 | 217 / 1209 | 0/1 | 5/4 | 1/1 | 0 | 4/4 | 2 | 15 | 0 | 1 |

The grip's 21 folded faces in every clip went to 1 when the finger curl was capped at 85 deg (r7). Largest left: the torso shell under the
shoulder plates with the arms raised (AttackMelee 55, Taunt 43, ResurrectSpell 44) and the face-down Death2 coat (85).

### Tube ends (`tube_gate.py`, r6 clips; rims are capped since r5)

Rim vertices that no cover meets within 6 cm (beyond the bind's own: upper arms 10, gauntlets 13): upper-arm rims 15-22 of 70 in every clip,
trouser rims 0-22 of 72 (Running 19, Death 22), gauntlet rims 3-18 of 49 (AttackMelee 18). The rims are closed by dark caps, so an exposed
rim shows a dark end; read by eye on the armpit close-ups, not everywhere.

### Detached parts (`detached_parts_audit.py`, r7 clips; r13 count in the second-pass section)

The audit's summary line was cut by the gate script's `tail -30` (the run takes about 30 minutes; not rerun); the 30 lines kept are all
warnings: 21 shallow roots (0.2-0.8 cm) and 9 root lifts, the largest 26.6 cm for the left trouser half off Spine3 in AttackMelee frame 10
and 3.2 cm for the tabard in Death. The trousers at that frame were read close up from three sides (`review/sheet_attackmelee_hips.png`):
covered by the belt, coat and tabard, nothing hangs free.

## Second pass (r9-r13, coordinator's six items; 0 new credits; r13 installed)

Earlier sections keep the first-pass (r7/r8) numbers. Gate outputs: `review/gates/r13`, `tube_r13.txt`, `floor_r13.txt`,
`regression_r13.txt`; the r7 clips re-measured with the corrected cloth gate in `review/gates/r7/cloth_newgate.txt`.

- **Cloth gate corrected (r9)**: `cloth_gate2.py` counted hits on the coat's inner surface and on lifted flaps. It now counts only rays that
  meet a cloth face from its outer side, on outer-surface triangles, for legs below the belt. Every r7/r13 comparison below uses the
  corrected gate.
- **Running cloth (item 1)**: coat 16/21 frames at 7.7 cm (16 vertices) -> **7/21 at 4.9 cm (5 vertices)**; tabard 2/21 at 0.9 cm -> **0/21**.
  The tabard and front sectors now ride the raised thigh (thigh rule: links along a thigh take its angle + 6 deg; leg points above the hinge
  count). **Goal not met**: the remaining hits are the back coat on the kicked-back heel. Other clips: Fidget2/Search 21/91 -> 0,
  Taunt 4/55 -> 0, ResurrectSpell 3/61 -> 0, Resurrect 6/55 -> 0, Fidget 1/43 -> 0, Hit 12/52 (4.1 cm) -> 11/52 (3.7 cm), AttackMelee
  4/31 (2.1 cm) -> 5/31 (2.8 cm), AttackRanged 0 -> 5/31 (2.5 cm), BackpedalRun 0 -> 1/22 (0.1 cm).
- **Face-down coat (item 2)**: lying poses lay the cloth along the legs: thigh line for the upper links, shin line for the lower, 25 deg in
  onto the legs only for sectors facing up (r13), leg and seat obstacles, swing capped at 60 deg. Dead2 coat 0/31 (was 0) and the
  corpse's coat now lies on the legs (`review/sheet_shoulders_r13.png`, Dead2 side and feet). Death2 coat 40/64 at 8.0 cm -> **15/64 at
  7.7 cm**; Death/Death3 coat 17/34 -> 5/34 (7.9 cm, 2 vertices), tabard 7/34 -> 9/34 (7.9 cm). **Not fixed**: the Death2 mid-fall tent
  (1.6-1.9 s, the shins kick up under the back coat; strip at 1.75 s in `review/strips_r13_run_death2.png`).
- **Staff lean (item 3)**: `staff_lean.py`, 6.0 deg on the right hand, shaft within 0.6 deg of MM9's in Standing. Grip gate unchanged:
  2.30 cm joint-to-axis, 0 inside, wrap 154 deg in every clip.
- **Staff skull (item 4)**: yellow-green via its own ramp material and green eye glow (see Decisions).
- **Shoulder collapse (item 5)**: `weights_lk.py` moves the front chest's Clavicle/UpperArm shares (torso shell, collar, collar wings;
  |x| < 16 cm) to Spine3, smoothed. Torso region AttackMelee 55 -> **51**, Taunt 43 -> **25**, ResurrectSpell 44 -> **25**; shoulder_L
  in AttackMelee 22 -> **8**. AttackMelee's torso faces barely moved (the shell under the raised left plate).
- **Atlas (item 6)**: the brow band is tucked instead of dropped: body atlas **55.3 %** (54.9 % in r8), stretch p90 1.09, fragments 0.0 %; head 66.1 %.
- **AttackMelee head duck (r12)**: the new arm correction failed the jitter gate (forearm 6.3 deg/frame over MM9). The left hand sweeps over
  our taller crown. The head now ducks 30 deg sideways off the hand's path (Gaussian, 0.12 s) and the arm is not corrected. Jitter 0 fails;
  AttackMelee L hand 1.6 cm (2 frames), forearm 2.1 cm (r7: 1.6 cm, 3 frames; forearm 1.2 cm). Read in `review/sheet_attackmelee_duck_r12.png`.
- **Coat folds (r13)**: r9-r12 raised the coat-strip collapse (back coat hung inside its bind shape; heel kick sheared B2 from BL2).
  Upright links no longer swing inside their bind angle, and back sectors stay within 30 deg of each other (raising the lower one).

Collapse, r7 -> r13 (worst frame; regions not listed are unchanged or within 1-2 faces):

| Clip | torso | shoulder L/R | strip |
|---|---|---|---|
| Running | 10 -> 6 | 0/2 -> 0/2 | 2 -> 3 |
| Fidget2, Search | 19 -> 14 | 2/6 -> 0/6 | 3 -> 0 |
| Taunt | 43 -> 25 | 2/8 -> 0/11 | 0 -> 0 |
| AttackMelee | 55 -> 51 | 22/4 -> 8/3 | 1 -> 3 |
| ResurrectSpell | 44 -> 25 | 2/7 -> 0/11 | 0 -> 0 |
| Resurrect | 30 -> 18 | 14/8 -> 12/10 | 4 -> 0 |
| Death, Death3 | 32 -> 20 | 12/6 -> 10/9 | 4 -> 20 |
| Death2 | 21 -> 14 | 4/6 -> 16/7 | 85 -> 113 |
| Dead / Dead2 | 15 / 15 -> 2 / 1 | 4/4 -> 0/0, 4/4 | 0 / 0 -> 0 / 16 |

Other gates on r13: bone length 0 of 19 stretching; winding 0; flat 0.02 / 0.00 / 0.01 / staff skull 0.05; jitter 0 fails; tube rims as r6
(upper arms 15-22, trousers 0-22, gauntlets 3-18); floor stand 0, walk -0.8..+1.4, living -2.4, dead 0: ok; regression `mm9_actor_models_build_every_binding` PASS, 158 descriptors on 65 models, 0 failed (suite 192 passed, 1 failed:
`out05_event_clearance_completes_from_monster_killed_hook`, could not load gameplay data, not this model);
detached parts (full output now kept, `review/gates/r13/detached.txt`): 91 components, **8 detached in some pose**, worst 1.33 cm:
skull and crown pieces 0.9-1.3 cm apart (Resurrect, Fidget, Backpedal), three staff pieces on Bone01 (one of 32 triangles 1.27 cm from
the body cluster even in bind), the right hand 0.86 cm in Death, the tabard 0.71 cm in Fidget2; 20 shallow-root warnings (under 0.75 cm) and 15 root lifts, the largest the trouser halves off Spine3 in Death3
(30.1 and 27.6 cm, under the coat; read as covered on the r7 AttackMelee hips sheet, not re-read for Death3).
The staff pieces were not read close up.

## Staff in the palm (r14-r19, 2026-11-01; user review; 0 credits; r19 installed)

The user's review of r13 (Standing, front): "the staff placement needs maybe to be put better to the palm?" The fingers curled beside the
staff and the shaft ran down past the fingertips, outside the hand.

- **Cause**: `grip_frame.py` placed the shaft by the nearest hand vertex (any side of the hand) and the finger knuckle points, and
  `grip_keys.py` solved only the finger JOINT points (bone centre lines) to 2.3-3.3 cm from the axis. Our Meshy hand is a claw (fingers bent
  about 90 deg at the knuckles in the bind), so the shaft stood 4.8 cm off the knuckle line on the palm side, the palm skin 2.1 cm off its
  surface; the solve opened the knuckles 18-28 deg, left the middle joints straight and curled only the tips, which hung beside the shaft
  (thumb on the palm's side). `grip_gate.py` measured joints only, so it passed (2.30 cm, 0 inside, wrap 154 deg). The flaw the Giant had
  (a joint stopped by the base vertices of the next phalanx) was not the one here: the r13 solve looked at no vertices at all.
- **Staff into the hand, not the hand onto the staff**: the staff is translated 2.15 cm in the hand's frame (`grip_solve.py seat`; its
  direction, MM9's lean from `staff_lean.py` and every clip's hand motion are unchanged). Moving the hand instead would have changed the arm
  in every clip (arm_out, arm_clear, jitter) for the same contact. The seat searched positions along the finger direction, each lifted until
  the palm skin (R Hand skin plus the skin within 20 % of each knuckle) is 2.5 mm off the shaft, and kept the one whose solved fist scored
  best (pads on the wood, nothing inside). It moved the staff and staff-skull vertices in `work/asm4.npz`, `uv_v1.npz`, `uv_tex.npz`
  (originals in `work/*_pre_seat.npz`, `work/rig_pre_seat.json`; `rig.json` grip keeps `point_r13`).
- **Fist on the skin** (`grip_solve.py`, called by `grip_keys.py`): per joint, knuckle to tip, the largest curl reached from the extended
  side before the phalanx's own skin (beyond the 20 % next to its joint) or the later phalanges (beyond 30 % of theirs) come within 2.5 mm of
  the shaft; a joint never swings through the shaft; knuckles may open to -50 deg where the claw already crosses it; no curl over 85 deg
  (r7's cap; a 100 deg index tip folded a face in r14-r17). Thumb: solved the same way from the other side (index and middle skin as
  obstacles), then turned 30 deg about the finger direction with the same curls, so it crosses the shaft's front with its pads on the wood:
  curled round the far side it went 3.1 cm into the front coat sector (`XCoatSFR1`, which lies against the shaft) in Aware (r13 2.2 cm).
  Turning the thumb across the shaft first (0-60 deg) gained 15 deg round it but lifted its short last phalanx; not used.
- **Hit head turn**: with the staff 2 cm deeper in the hand, its skull met the head in Hit 2.1 cm deep (2 frames; r13 1.2 cm). The head turns
  20 deg off the staff skull at 0.156 s (Gaussian, 0.06 s; `head_duck.py ... Hit 7.5 20 0.06 staff`): 0.5 cm. A change to MM9's motion,
  like the r12 AttackMelee duck (`review/sheet_hit_headturn_r19.png`).
- **New gates**: `grip_gate.py --mirrored` adds the palm gap (palm-side R Hand skin between wrist and knuckles to the shaft surface), the pad
  gap per finger and phalanx (distal half of each phalanx), the thumb and fingertip angles round the axis from where the palm meets the
  shaft, and hand skin inside the shaft (no tolerance). `staff_gate.py` (staff vertices behind the body skin within 1.5 cm, by counts; the
  open coat makes a depth meaningless; lowest point) and `head_gate.py` (staff inside the head skull's hull) are in `gates.sh`.

| Gate (every clip; worst) | r13 | r19 |
|---|---|---|
| Palm gap, min / p10 | 2.06 / 2.38 cm | **0.44 / 0.54 cm** |
| Pad gap phalanx 1/2/3, Index | 0.65 / 0.22 / 0.39 | 0.12 / 0.22 / 0.43 |
| Middle | 0.75 / 0.26 / 0.40 | 0.11 / 0.39 / 0.64 |
| Ring | 0.51 / 0.18 / 0.28 | 0.12 / 0.25 / 0.17 |
| Pinky | 1.22 / 0.63 / 0.56 | 0.27 / 0.16 / 0.11 |
| Thumb | 1.59 / 0.48 / 0.73 | 0.82 / 0.20 / 0.23 |
| Fingertips round the shaft from the palm contact | 72 deg | **129 deg** |
| Thumb round the shaft from the palm contact | 37 deg (palm side) | 45 deg (across the shaft's front) |
| Hand skin inside the shaft | 0 | 0 |
| Old joint check (bone centre lines; obsolete: a wrapped fist hugs the shaft) | 2.30 cm, wrap 154 deg | 1.76 cm, wrap 203 deg |
| Collapse, finger / wrist_R region | 1 (AttackMelee 3) / 1 | **0 (AttackMelee 2) / 0**; every other region unchanged |
| Arm/hand R hand into body | Aware 2.2, Taunt 1.6, AttackRanged 1.5, ResurrectSpell 1.5, Fidget 1.2, Hit 1.0, Death3 5.8 cm | Aware 0, Taunt 1.3, AttackRanged 1.1, ResurrectSpell 1.1, Fidget 0.7, Hit 0.3, Death3 2.4 cm; Death 4 -> 5 frames over 1 cm (2.5 cm both) |
| Arm/hand L side | Death2 hand 1.5 cm (8 frames), forearm 0.5 cm | hand 1.6 cm (6 frames), forearm 1.2 cm (the left forearm against the moved staff in the fall); AttackMelee hand 1.6 -> 1.3 |
| Finger stretch R | 1.53 / 1.82 | 1.45 / 1.74 |
| Staff in the head hull | Hit 1.2 cm, AttackRanged 2.2 cm (2 frames each) | Hit 0.5 cm, AttackRanged 2.1 cm |
| Staff behind body skin (frames with any) | Fidget2/Search 19, Death 4, Death3 5; most others more | Fidget2/Search 23, Death 5, Death3 7; others fewer (Standing 38, Fidget 16, Hit 3) |
| Staff lowest point, floor audit | Death3 0.0 cm; stand 0, walk -0.8..+1.4, living -2.4, dead 0 | same |
| Jitter, bone length, winding, cloth | 0 fails, 0 of 19, 0, (r13 numbers) | 0 fails, 0 of 19, 0, identical to r13 |

Fidget2 at 1.73 s (the kneel) had the staff through the right shin in r13; in r19 it lies along the front of the shin, more of it visible
(`review/sheet_staff_legs_r19.png`; read, not cleared). AttackRanged keeps MM9's staff in front of the face (2.1 cm into the skull hull, as r13).

Sheets (read by me): `review/sheet_grip_r13_before.png` and `review/sheet_grip_r19_after.png` (right hand from the front, below, outside
and the palm side at Standing 0, 1.33 s, the 2.67 s loop seam and AttackMelee 0.479 s), `review/sheet_hit_headturn_r19.png`,
`review/sheet_staff_contacts_r15.png` (staff skull at the head in Hit and AttackRanged, r13 against the same seat as r19),
`review/sheet_staff_legs_r19.png`. Gate outputs: `review/gates/r13_palm` (r13 re-measured with the new gates), `review/gates/r19`,
`floor_r19.txt`, `regression_r19.txt`.

## Sheets (viewer shots, read by me)

`review/sheet_mm9_vs_ours.png` (MM9 bind and four clip poses against ours), `review/sheet_head.png` (full-size head, front, both quarters,
above), `review/sheet_joints_a.png`, `review/sheet_joints_b.png` (knees, groin, armpits, elbows, neck, head and mouth in kneeling, running,
raised-arm, death and corpse poses), `review/strips_1.png`-`strips_3.png` (every clip, seven frames; r6), `review/sheet_ingame.png`
(in game, bootcamp.odm, spawned rows). Gate outputs: `review/gates/r6`, `r7`, `tube_r6.json`.
Second pass (r13, read by me): `review/sheet_mm9_vs_ours.png` (reshot), `review/strips_r13_run_death2.png` (Running, Death2,
Dead2, Fidget), `review/sheet_shoulders_r13.png` (AttackMelee 0.5 s and Taunt 0.37 s shoulders and chest, Dead2 side and feet, Running
back at 0.2 s), `review/sheet_head_r13.png`, `review/sheet_attackmelee_duck_r12.png`. The in-game sheet was not retaken.

## Open points and what was not checked

- Staff in the palm (r19): the thumb lies across the shaft's front at 45 deg from the palm contact, not round its far side (that side is
  against the front coat); the middle finger's last two pads are 0.4-0.6 cm off the wood (r13 0.3-0.4) and the thumb's base 0.8 cm.
  The Hit head turn (20 deg, 0.1 s) and the hand were read in stills only, not at speed; not looked at in game.
- Coat in **Running** (7/21 frames, 4.9 cm: the heel kicked into the back coat), Hit (feet into the hem), the falls of Death/Death3 and
  the Death2 mid-fall tent; Death2 coat-strip collapse 113 and Death/Death3 20 (r7: 85 and 4); Dead2 16 (r7: 0). Script clips Death3 (`die1_OLD`) holds the staff upright off the floor in its corpse.
- Torso collapse under the raised left shoulder plate in AttackMelee (51); Taunt and ResurrectSpell 25.
- AttackMelee's 30 deg head duck is a deliberate change to MM9's motion (seen in stills, not at speed).
- Motion at normal speed was not watched (agents cannot watch video); strips are seven frames per clip.
- In game: only spawned rows on bootcamp.odm (mostly seen from behind), not Isle of Ashes, where the row is placed; the cast glow at
  `palm_left` / `staff_head`, the corpse, LOD1-3 and shadows were not looked at.
- MM9's FX (`DoFX 1`, `DoFX 0` on ResurrectSpell, `DoResurrection`) are not carried; no engine hook.
- Sounds, footsteps.
- User artistic acceptance: not recorded.


**LOD0 reduced post-install on 2026-11-05 by `level_generation/creatures/mm9_lichking_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_lichking_reduce_claude/before/`.
