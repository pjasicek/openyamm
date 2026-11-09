# MM9 Skeleton body (mm9_skeleton) — 3D actor, 2026-10-30

MM9 `SKELETON.abc` (40 joints, 16 clips), rows 135 Skeleton L16 (descriptor `MM9 Skeleton C`), 192 Skeleton L40 (`MM9 192 Skeleton`), 184 Bone Thrasher L3 (`MM9 Skeleton B`), all skin SKELETON2, and 183 Skeletoid L3 (`MM9 Skeleton A`), 185 Skull Thrower L2 (`MM9 185 Skull Thrower`), skin SKELETONRED, all with SKELETONDAGGER. Built by the approved route of `../mm9_skeletonwarrior_claude/` (MM9 skeleton, MM9 clips, rigid pieces, separate skull, true handedness at the source), with `../mm9_cat_claude/`'s collapse gate.
Progress, hashes and receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_skeleton.glb` (`tools/install_model.py --world mm9`), skins `skel_a` (SKELETON2), `skel_r` (SKELETONRED) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, block `mm9_skeleton_claude`: scale 100 rows 135, 192; 50 (MONSTERS `Scale` 0.5) rows 183, 184, 185. `yaw_offset` -1.570796327, stride walk 2.25 / run 3.4, melee impact 0.4 s (`Rattack`), ranged impact 0.38 s (`RangeAttack`), release socket `throw_hand` = `Bip01 R Hand` (MM9 hangs RangeAttack on the right hand), look `Bip01 Neck, Bip01 Head` |
| Triangles LOD0/1/2 | 12,438 / 5,925 / 2,071 (LOD0: body 8,822 including 575 dark lining faces, head set 3,316, dagger 300). LOD3 (587) is left out of the chain: it lost the legs (`review/sheet_lod.png` shows why it went) |
| Skeleton | MM9's 40 joints, names and rest rotations unchanged, joints translated onto the pieces, + 14 finger bones per side (`Bip01 <S> Thumb1,2`, `Index,Middle,Ring,Pinky 1..3`). MM9's mitten fingers stay as empty bones |
| Clips (30 fps) | Standing `stand` 1.8, Walking `walk` 1.33, Running `run` 0.67, Fidget `fidget1` 2.03, AttackMelee `Hattack1` 0.8, AttackRanged `RAttack1` 0.8, Hit `wince1` 1.0, Death `die1` 1.4, Dead; script clips `attack2` (Hattack2), `hit2` (wince3), `fidget2`, `fidget3`, `taunt`, `resurrect` (6.5 s, climbs out of the ground). Backpedal and BackpedalRun not carried |
| Textures | body 2K colour (mirrored limbs share texels), head set 2K colour (skull, jaw, teeth, eyes, neck), normal and ORM 1K each, dagger 1536x1024 from the Codex master |
| Meshy credits | **40 / 40**: body Smart Topology 5, skull Smart Topology 5, body retexture 10, head retexture 10, second body retexture 10 (backup account; the first request with `target_polycount` 30000 was rejected, 0 credits) |

## Route

0. **Source** (`scripts/mirror_source.py`, from the Skeleton Warrior): `source/skel/skel2_true.glb`, `source/red/skelred_true.glb`. MM9's conversions are mirrored; here the toes have no twins (four on one foot, a chain on the other) and MM9 never keys them, so they keep their rest. Convert at `--scale 0.0256`. Reference images are the raw renders flipped, so they show the true figure (green eye on the figure's right, dagger in its right hand). `review/mm9_vs_ours.png` confirms pose and handedness against the true source in the viewer.
1. **HD masters** (`references_hd/`, Codex): five views. Smart Topology of `00_three_quarter.png` (15,000) gave 152 clean loose parts: every rib group, vertebra, phalanx, tarsal, cuff, strap and vest panel.
2. **Skull** (`references_head/`, Codex): a skull-only Smart Topology gave cranium, mandible, 20 teeth and an inner shell (dropped). The bust views paint it. Excellent from the first try: MM9's swept-back high cranium, real sockets.
3. **Parts** (`scripts/sym_skel.py`): Meshy unit x 1.85 (hip height and skull top as MM9's), reduced per part, right-side parts mirrored over the left. Smart Topology gave a **sixth digit** on each hand, a fork off the little finger: removed. Sockets deepened; eye spheres; a **back panel** (ray-cast onto ribs and spine, torn hem) and a **rope collar** added: the masters and MM9 have them, Meshy gave only the two flanks.
4. **Fit** (`scripts/fit_skel.py`): joints at the pieces' centres, rigid pieces, one smooth field Spine2 -> Spine3 over ribcage, vest and strap (MM9's torso flexes up to 19 deg there), column and neck blended; each piece then turned onto the MM9 bone direction (arms 27-30 deg, legs 9, torso 5.7, hand 36.7). The HD pose stays in `fitco`.
5. **UVs** (`scripts/uv_skel.py`): `work/uv_final.blend`. Never re-run: the paint belongs to this layout. `margin_px=1`: atlas 57.1 % with it, 52.5 % at the default 2.
6. **Paint**: the first body retexture from the masters read as **reptile skin** with an orange woven vest and a black strap with white blobs: the masters' mottled surface. The skull paint stayed. Second pass `references_hd/v2/`: Codex painted **clay renders of the real mesh** (`scripts/hd_clay.py`), bone authority the skull busts, leather authority the MM9 skin. Far better, and it lines up with the geometry. `compose_texpass.py`, gentle grade, then `scripts/tone_skel.py`: bone blobs off leather, leather and grey strap off ribs, rope to tan, bone to the skull's ochre, eye colours.
7. **Finish** (`scripts/finish_skel.py`, shares texels): linings, back panel turned the right way, two closed slivers Meshy returned inside out, two toe bones with zero-area UVs given texels of a neighbour, eyes moved forward (on the socket floor they broke through the temple), hip strips rigid on the thigh, joints closed by a few mm, dagger on `Bone01` (`scripts/dagger_mesh.py`), fist solved round the grip.
8. **Clips** (`scripts/clips_mm9.py`, `roles_skel.json`, `finger_keys.py`, `arm_clear.py`): MM9 local rotations, `root_lift` 1.1123 (the floor under MM9's bind), `thin_keys`. Right fist grips, left hand relaxed, both held: MM9's mittens carry a fixed curl. `arm_clear.py` gained `--solids` (only the closed bones count) and a closest-triangle inside test.
9. **Runtime** (`scripts/build_runtime.sh`): prepare, LODs, shadow fix, `fix_lod_winding.py`, region variants, `drop_tier_ramps.py`, floor, eye emission per tier, winding.

Rebuild after the paid steps: `TOKEN=<lease> scripts/rebuild.sh uv_final.blend`, `scripts/build_runtime.sh --install`, or `scripts/cycle.sh <revision> [--install]` (edit the token in it). Gates: `scripts/final_gates.sh`. Binding: `scripts/bind_actors.py 2.25 3.4` under the flock. PYTHON: `claude_shared/gltf_venv/bin/python` by that path.

## Tiers and MM9 visual properties

- **skel_a** = the paint itself (no ramps), green right eye, dead left eye (MM9's left socket is empty with a crack; the crack is painted).
- **skel_r**: region mask + ramps (`scripts/tier_ramps.py`): body R vest leather, G leg leather and hip strips, B bone; head R eyes, G bone. Colours are the SKELETONRED skin at the matching tiles, by luminance rank. Both eyes red.
- Skins are opaque (`Transparent 0`). Eyes emit, per tier by its own mask (`scripts/tone_skel.py`), pulse 0.12 over 3.1 s: a gain, MM9 paints them.
- `Resurrect 1` (rows 183-185): the clip is bound as a script clip; no behaviour drives it.

## Checks (final GLB, viewer `t20`, 2026-10-31)

| Gate | Result |
|---|---|
| Collapse gate per clip and joint region (`scripts/collapse_gate.py`, adapted from the cat, regions hip_knee, shin_ankle, foot, upper_arm, forearm, hand, fingers, pelvis_scraps, waist, ribs_vest, neck, head, dagger, both primitives) | Body **0** face-frames in all 15 clips (`review/collapse_body.txt`). Head set 0 except Resurrect, neck 1 face, 11 frames, exposed, while the head turns 146 deg underground at the clip's start (`review/collapse_head.txt`). The bones are rigid; the first build folded 2-26 faces on the hip strips, which is why they are rigid on the thigh |
| Thigh through skirt/tabard (`scripts/scrap_gate.py`: cloth points inside the closed femur mesh in the thigh's rest frame, 48 fps) | Walking **0/65**, Running **0/33**, all bound clips 0. Resurrect 6/313 frames, 2.0 cm, femur into the vest panel. The body has no skirt: only short hip strips, rigid on the thigh |
| Hands and forearms inside closed bones (`scripts/hand_bone_gate.py`, 48 fps) | 0 frames over 1 cm in every clip except Hit L hand 2.0 cm, 1 frame. Under 1 cm: AttackMelee/Ranged R hand 0.7, Fidget2 and Taunt L hand 0.5, Resurrect 0.8. Before `arm_clear.py`: Fidget3 R 2.1 cm, 6 frames, AttackMelee L 2.5. Corrections at most 9.3 deg (Resurrect), 7 deg in AttackMelee |
| `arm_hand_gate.py --outer-only --exact` | Its depth figures are noise here: it counts open vest and strip sheets (viewer shots show air). Kept in `review/arm_hand_gate.txt`; finger stretch 1.0 everywhere (rigid phalanges), 18 hand bones per side including MM9's four empty mitten bones |
| `jitter_gate.py` against raw MM9 keys | Hand acceleration at or under MM9's except AttackMelee/Ranged R 224 against 187 mm/f2, Hit L 279 against 243, Death L 140 against 121, Standing R 2.4 against 1.5, Taunt L 47 against 45. The gate reports FAIL on its per-frame shoulder excess in most clips, as on the Skeleton Warrior: dropping held keys (`thin_keys`) moves motion between frames, so a frame-by-frame compare with the raw keys fails by design. Running shoulder skin excess 20 mm/f2 is the largest (`review/jitter_gate.txt`). Not a clean pass |
| `detached_parts_audit.py` (24 fps) | 173 components, **4 flagged** (`review/detached_audit.md`): L talus 10.1 mm root parted, 31 of 608 poses (Walking, the ankle gap); mandible 6.4 mm, 5 poses (rigid with the cranium, against its neck holder); one carpal 4.3 mm, 1 pose (Resurrect); scrap 124 4.1 mm, 17 poses. Bones are separate by design: 68 parts "only just attached". 26 flagged before the joints were closed by 4-9 mm and the dagger rebuilt |
| `check_winding.py` | 0 inverted closed parts |
| `flat_shading_check.py` | 0.00 on body, head and dagger |
| `texture_quality.py` | body atlas 61.1 % (57.1 % unique), fragments **3.1 %** (target 3), stretch 1.24, spread 1.49 (hands 1.3x and linings by design); head atlas 68.6 %, fragments 2.1 %, stretch 1.17, spread 1.08 |
| `floor_audit.py` | all five descriptors ok: stand 0, walk -0.7..+1.2 (scale 100), -0.3..+0.6 (scale 50), living -0.8, dead 0 world units |
| Handedness | Dagger in the true right hand, throw from it. `review/mm9_vs_ours.png` top rows: same pose as the true MM9 source in the same viewer in four poses; MM9's front view has the dagger on image left, ours too |
| Regression `mm9_actor_models_build_every_binding` (`--world mm9`), `--headless-validate-actor-models` | PASS, 95 descriptors on 42 models, 0 failed, 0 refused |
| `run_creature_review.py check` | 60 switches, 0 console errors, 0 failed (four tiers: `skel_a`, `skel_r`, `lod1_a`, `lod2_a`) |
| In game (`--assets output/mm9_rework/assets_dev`, `beethoven.blv`, `review/ingame/`) | Skeleton row 135 stands, bar and name correct, green eye glows; Bone Thrasher at half size attacks the party. Dungeon is dark there: the eye reads, the leather less |

Sheets (viewer shots, all looked at): `review/mm9_vs_ours.png`, `review/sheet_tier_skel_a.png`, `review/sheet_tier_skel_r.png`, `review/sheet_closeups_a.png`, `review/sheet_closeups_r.png` (texture close-ups), `review/sheet_closeups_poses.png` (knees and groin in Running, Death, armpits and neck in AttackMelee2 and Hit, elbows, mouth), `review/sheet_lod.png`, `review/strips_a/strip_<clip>.png` and `review/strips_r/` (8 frames, side and 3/4, every clip), `review/sheet_strips_all_clips_a.png`, `review/ingame/skeleton_crop.png`.

## Deviations and open points

- **Rows 183, 184, 185 keep the row height** of the sprite stand-ins (185 and 166 units) with a half-size model: the health bar floats a body above a Bone Thrasher and the collision column is too tall. Changing the rows means rebuilding the maps (placed actors keep their height), so I left it.
- **Head set is 2K colour**, as the Skeleton Warrior ships, not the brief's 1K.
- **Hands**: Meshy's five bone fingers, not grafted MPFB hands. Three rigid phalanges, two for the thumb. They hold poses; MM9's curl is one fixed clench, so nothing to drive except `wince1`.
- **Hip strips rigid on the thigh**, not hanging from the rope: their tops slide against the rope belt when the thigh swings. Any blend folded them or let the femur through.
- **Strap** has no buckle or studs in geometry or paint after the clean-up; a plain dark band, plus a thin grey band on the upper ribs from the second master that the rib pass did not fully remove. MM9 paints studs and a buckle.
- **Vest**: flank panels and back panel are stiff sheets. In Death and Dead it reads as boards from some angles.
- **Bone texel density** is lower than the skull's (2,135 against 3,200 px/m at the same image size), so bones read softer than the skull up close.
- **Tier R** rope stays tan (MM9's is too); its vest colour is bright against MM9's dull red, darkened by one gain only.
- Eyes are modelled spheres, a gain over MM9's paint; the left is a dark ball rather than an empty hole.
- Walking stride 2.25 is the p90 backward foot speed x clip length; MM9's velocity gives 2.56. Running 3.4 is MM9's. Foot slide in game not measured.
- `Resurrect` starts 1.3 m under the floor and stays out of the floor pass; it is a script clip and no behaviour plays it.
- Unused MM9 clips: Backpedal, BackpedalRun, static_model.
- `SKELETON1.dtx` is not used by any row and is not a tier.

## Not checked

- Normal-speed playback by eye: frames and numbers only.
- Skeletoid and Skull Thrower in game (not placed in Beethoven or Chasm); red tier only in the viewer. Chasm of the Dead in game. Skeleton L40 (row 192) is not placed there either.
- Thrown axe and skull at the release socket in game, melee impact timing in game, Bone Thrasher's corpse.
- Ragdoll of cuffs, ankle bands from below in every clip; Fidget2/3, Taunt, Resurrect close-ups (strips only).
- LOD2 close up, shadows at distance, MM9 lighting match in other maps. FPS with 37 Bone Thrashers: not measured, and LOD2 is the coarsest level at 2,071 triangles each.
- Binding values of `script_clips`: no behaviour reads them.

## Dropped-clip pass, 2026-10-31 (run 2, 0 credits)

`scripts/roles_skel_extra.json`: Backpedal and BackpedalRun through finger_keys, arm_clear and the floor pass (Backpedal grounded like Walking, BackpedalRun raised with 0.04 s loop smoothing), grafted with `claude_shared/graft_clips.py`. Bound `backpedal`, `backpedal_run`. Floor -1.0..+1.8 cm, hands in bones 0, thigh length within 4.6 %. Numbers, strips: `review/clips_restore/`; summary `devdocs/mm9_rework/overnight/status/clips_groupA.md`.

User artistic acceptance: "skeleton OK" (2026-10-31)


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_skeleton_reduce_claude/`** (user-approved; ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `mm9_skeleton_reduce_claude/before/`.


**2026-11-04 later: the reduction was rolled back** (installed source = `mm9_skeleton_reduce_claude/before/`): the UV audit (`claude_shared/reduction_uv_audit.py`) found reduced faces whose UVs left the painted charts, visible in close-up. A fixed reduction may be reinstalled later; see the ledger.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_skeleton_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_skeleton_reduce_claude/before/`.
