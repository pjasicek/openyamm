# MM6 Thief (thf) rebuild on the MM9 HIGHWAYMAN skeleton — 2026-11-11 (stream `rebuild`, audit mm678 2026-11-11)

Thief / Burglar / Rogue, monsters 637/638/639 (`BThief A/B/C`, palettes 825 green / 826 purple / 827 brown). Replaces the installed model of
`../mm6_thf_claude/` + `../mm6_thf_reduce_claude/` + the gait package h01 (Meshy auto-rig, mitten hands, verlet cloak chains that tore in
Sprint: cloth 27 % bad, body atlas 15.6 %). Route: the approved MM9 humanoid "Yrsa route" with `../mm9_highwayman_claude/` as the skeleton and
clip donor (HIGHWAYMAN.abc + its FIGHTERBASE child clips, `source/true/highwayman1_true.glb`), the Guard pilot's helpers
(`../mm6_gua_rebuild_claude/`) and the PeasantF1 worker's lessons (`../mm6_pfem_rebuild_claude/`).

| Item | Value |
|---|---|
| Installed | `assets_source/worlds/mm6/models/mm6_thf.glb` (sha256 f33397f84d556f40…, 15.7 MB source, 5.0 MB cooked), `tools/install_model.py --world mm6`, 2026-11-11 |
| Revert | `mkdir -p /tmp/thf_revert && cp work/before_rebuild/mm6_thf.glb /tmp/thf_revert/ && python3 tools/install_model.py /tmp/thf_revert/mm6_thf.glb --world mm6`, then put the three BThief blocks of `work/before_rebuild/actors_thf_entries.yml` back into `assets_dev/worlds/mm6/models/actors.yml` (whole file at claim: `work/before_rebuild/actors_full_at_claim.yml`) |
| Geometry | the old project's gated HD masters (`references_hd/`, `references_head/`, copied) and its cleaned Smart Topology (`../mm6_thf_claude/work/step1_v1.blend`, 9,266 tris, part labels): no new geometry credits. Scaled to MM9's shoulder height (x1.1664), not mirrored (pouch right, sheath left, strap across) |
| Skeleton | MM9 HIGHWAYMAN (32 nodes, rest frames turned onto our limbs by the least rotation: `fit_thf.py`, from `fit_hw.py`) + 30 finger bones (MPFB) + 8 jerkin-skirt hinges + 10 half-joint helpers + 48 cloak chain bones (10 main columns x 4, 4 front-mantle columns x 2) = 128 joints |
| Hands | MPFB male hands grafted at the bracers (`graft_hands.py`, frame `rig`, palm toward the thigh, 0.19 m), 15 finger bones per side; relaxed MPFB curl in every clip but the dagger clips, where the fists close round the grips (`finish_thf.py` per-finger solve, thumb over; `finger_keys_thf.py` eases them in 0.12 s and out 0.16 s) |
| Daggers | the approved 2026-10-14 daggers (126 tris each, `extract_daggers.py`) x1.1664, rigid on `Ybasesword` (true right) / `Ybasedagger` (true left), placed on the solved grips, blade along MM9's sword / dagger axes; shown only in Attack, Attack2, AttackRanged (scale 0.001 otherwise); their old painted column is turned into the body atlas's top strip |
| Cloak | one shell (hood, mantle, long cloak) on `Cloak_<k>_<j>` chains (`rig_thf.py`, bilinear weights in angle and height; hood on the head, neck ring and shoulder caps on the torso, a long Head->Neck->Spine3 ramp at the collar by `smooth_band.py`), keyed per frame by `cloak_keys.py` (see "Cloak") |
| Textures | body 2K colour + 1K normal/ORM (uv_atlas, top strip v 0.93..1 left for the daggers), head set 1K (face, side hair, neck skin above the collar); 4K Meshy paints downsampled once, gentle grade; hands toned to the face's skin (Meshy painted them near white); tiers = one cloth region (cloak, hood, green undershirt) + the installed ramps (palettes 825/826/827), range refitted |
| Meshy credits | 20 of 85 (body retexture 4K 10, head retexture 4K 10; backup account) |
| Binding | `actors.yml` BThief A/B/C (`scripts/bind_actors.py`): scale 93.26 (old 108.68 x 1.5799 / 1.8411 standing heights), walking `Walk2` stride 1.9178, run `Jog` 2.666, sprint `Running` 3.21, look `Bip01 Neck, Bip01 Head`, upper body `Bip01 Spine1`, melee impact 0.375 s, ranged impact 0.417 s released from socket `dagger` = `Ybasedagger`, `script_clips: attack2: Attack2` |
| Triangles LOD0/1/2/3 | 9,638 / 4,817 / 1,730 / 572 (installed 4,991 / 2,495 / 1,497 / 798). LOD0: hands 2 x 799 (MPFB), daggers 2 x 126, cloak + hood 2,589, face/hair under the hood ~600 (398 hidden skull faces pruned) |
| Clips (MM9 HIGHWAYMAN + FIGHTERBASE) | Standing `stand`, Walking `walk`, Running `run` (bound as the sprint), Fidget `fidget1`, Attack `Hattack3` x1.2 = 0.73 s (native 0.75 s; contact 0.45 -> 0.375 s), Attack2 `Hattack2`, AttackRanged `Rattack1` x1.2 (release 0.5 -> 0.417 s, the left dagger drawn at 0.19 s, gone at the release), Hit `wince1` x1.2, Death `die1`, Dead; Walk2 = `walk` legs x1.45, rate 1.35 (0.87 s); Jog = `run` legs x0.83, rate 0.8 (0.5 s) (`clips_mm9.py` role option `gain`) |

## Chain (`scripts/`)
1. `rebuild_mesh.sh`: `clean_thf.py` (old step1 mesh, scale, labels: 1 torso, 2 face, 4 hand, 5 legs, 6 boot, 7 jerkin skirt, 8 bracer, 9 strap,
   10 pouch, 11 sheath, 12 buckle, 14 cloak) -> `fit_thf.py` (`fit_thf.json`) -> `rig_thf.py` (weights, skirt hinges, cloak chains + `work/rig_v1.blend.cloak.json`)
   -> `graft_hands.py graft_thf.json` (`BLENDER_USER_EXTENSIONS=$HOME/.config/blender/5.2/extensions`) -> `helpers_thf.py` -> `prune_hidden.py`.
2. `uv_thf.py` (frozen: the paints belong to `work/uv_v1.blend`) -> `requests/retexture_{body,head}.json` (Meshy 4K, masters `references_hd/`,
   head turnaround `references_head/`) -> `bake_ao_thf.py` -> `extract_daggers.py` -> `finish_thf.py` (fists, daggers) -> `dump_uv.py work/final_v1.blend`
   -> `compose_thf.py --stage raw` (grade included), `--stage final` (dagger strip, hands toned, hood paint in the head set turned to hair, region mask, ramps).
3. `TOKEN=… scripts/build_runtime.sh [--install]`: `smooth_band.py` (collar ramp) -> `export_thf.py` -> `clips.sh` (`clips_mm9.py roles_thf.json`,
   `finger_keys_thf.py`, `half_keys.py`, `skirt_keys.py`, `foot_clear.py` Running/Jog, `cloak_keys.py`) -> prepare, LODs, shadow fix, `region_variants.py`,
   `floor_fix.py` (`floor_ops.txt`), winding [-> install]. `FROM_CLOAK=1` reruns only the cloak keys.
4. `gates.sh`, viewer (`viewer_thf.py export/mm6_thf.glb rebuild`, `viewer_manifest.py rebuild <rev>`), `ingame.sh`, binding `scripts/bind_actors.py` (repo root,
   env `WALK_STRIDE RUN_STRIDE SPRINT_STRIDE`).

## Cloak (`cloak_keys.py`)
The installed cloak tore because neighbouring verlet chains drifted apart (Sprint cloth 27 % bad). Here each frame is solved on its own on the chain
joints (no simulation state: loops close, one-shots start from the eased Standing pose): the target drape hangs between rigid-with-Spine3 and plumb
(more plumb lower down), trails back in the gaits, then 10-12 rounds of capsule collisions (legs and heels push the cloth along its own outward
normal, also between columns; arms push radially but never beyond the bind-pose clearance, since the chain line runs mid-thickness), a lateral
constraint that keeps neighbouring columns within 0.85-1.22 of their rest spacing (no tears), exact segment lengths; joint paths smoothed in the Spine3
frame. Death: the drape follows the torso as it tilts; while falling the hem may dip 8 cm under the floor and its vertices at most 16 cm under the
body's lowest point, from the landing the cloak lies under the body (vertex-level floor pass). Residual leg contact (chain level): Walk2 2.2 cm,
Jog 2.9 cm, MM9 run 5.4 cm (a toe tip at the hem in a few frames).

## Checks (final build, installed)
| Check | Result |
|---|---|
| Attack motion ratio vs MM9 biped median | 0.88 -> **1.04** (Hattack3 x1.2: amp p90 0.40, body share 0.84, peak speed 6.43, torso turn 51 deg) |
| Worst region beyond Standing (audit roles) | AttackRanged hand 7.0 % (fist folds); cloth: Sprint 27.0 -> 3.7 %, Hit 19.3 -> 0.5 %, Walk2 5.2 %, Jog 2.9 %, Attack 0.4 %; Death cloth 10.5 %, head 11.2 % (collar), arm 9.0 % (not an audit role; all under 12) |
| Hand inside the body (motion_audit) | 0 % in every bound role (installed 0 %) |
| `arm_hand_gate.py --outer-only --exact` | against skin and jerkin (`NOCLOTH=1`, `review/gates/arm_hand_skin.txt`): 0 cm in every clip but AttackRanged L 0.5 cm and Death/Dead L forearm 4.4-4.9 cm (MM9's die1 left arm over the chest while lying); with the cloak included the hands read 2-6 cm "inside" the cloak shell they hang in (`arm_hand.txt`); 17 finger chains per hand, finger stretch <= 1.55 (Death 2.05) |
| `grip_gate.py` | fingers inside the grip <= 0.1 cm; wrap per finger thumb 127-150, index 120-135, middle 195-210, ring 165-180, pinky 30-60 deg (the short grip ends at the ring finger) |
| `jitter_gate.py` vs the raw MM9 clips | 0 fails |
| gait_gate / floor_audit / gait_audit | **PASSED** (wander Walk2 x1.12-1.21, chase Jog x1.01-1.09, MAW chase Running x1.14-1.16) / 0 problems (stand 0, walk -0.9..+2.4, living -2.5, dead 0) / 0 flagged |
| texture_quality (`audit_after/texq.txt`) | body Thief_A 2048: atlas **58.3 %** (installed 23.9 % at 1K), fragments 0.0 % (8.7), stretch p90 1.09 (2.45), density p50 1,077 px/m (498), spread 1.05; head ThiefHead_A 1024: atlas **54.6 %** (15.6 %), fragments 1.9 % (10.0), stretch 1.09 (1.56); materials 3 -> 2 (cloak no longer its own draw) |
| winding, regression, viewer | 0 inverted (the dagger parts flipped outside out in `finish_thf.py`); `mm6_mm7_mm8_actor_models_build_every_binding` PASS (647 descriptors, 0 failed), `mm6_thief_actor_model_tiers_share_the_native_height` PASS; `run_creature_review.py check` 36 switches, 0 console errors |
| Before/after | `review/sheet_before_after.png` (stand front/quarter/back, walk, jog, sprint from behind, attack, throw, hit, dead; every tier) and `review/sheet_before_after_close.png` (face front and 3/4, both hands in Standing); `review/sheet_fists.png` (fists on the daggers in Attack and AttackRanged, relaxed hand in Standing). The viewer shows model units, so the rebuild (1.84) looks larger than the installed model (1.58); in game both are 171.5 units tall |
| In game | `review/ingame/frozen_sheet.png` (three tiers spawned and frozen: New Sorpigal test spot, Agar's Laboratory), `review/ingame/out_sheet.png`, `in_sheet.png` (hostile thieves approach and attack an immortal party with both daggers, one killed: death and corpse) |

## Deviations / open
- Body from the old cleaned Smart Topology (`step1_v1.blend`), not the installed reduced LOD0: the rebuild needed the unreduced mesh for new UVs and
  hands. Not mirrored (the pouch, sheath and strap are one-sided).
- Daggers are shown only in the dagger clips (as before): they pop in at the clip start and out at the end while the fists ease.
- Death: the falling body is raised up to ~20 cm for a few keys by `floor_fix --ground-death` because the cloak hem dips under the floor while he falls
  (smoothed 0.06 s); the corpse lies 9 cm higher than MM9's die1 puts the pelvis (body 6 cm + the cloak under him).
- Left forearm through the chest in Death/Dead (MM9 die1's arm pose on a thicker body), 4-5 cm.
- A pale jagged ring shows under the bracer rim on close-ups (Meshy's rim paint), and the face mesh is the Smart Topology's coarse face (~400 tris)
  under a 1K head paint.
- Hood inside: Meshy painted the skull under the hood as the hood's cloth; turned to dark hair (as the masters) by hue, so its detail is cloth weave in a
  hair colour.
- Walk2 cloth 5.3 %, Jog 3.0 %: the kicked heel lifts the hem at the back (no tearing); MM9's run (the sprint) still shows a toe tip at the hem.
- Not checked: LOD1-3 by eye beyond the in-game shots; Android.

## Far LODs repaired (2026-11-12, lod-step1)

LOD2/LOD3 and their shadows rebuilt by `lod_repair_claude/scripts/repair.py` from the installed GLB: ladder step
25/12 %, own 512/256 px far maps by UV correspondence; LOD0, LOD1, clips, materials and tiers unchanged
(`verify_far_only.py` OK), winding 0, every_binding PASS. Numbers and captures: `../lod_repair_claude/README.md`
("MM6 rebuilds' far LODs"). Revert: `tools/install_model.py level_generation/creatures/mm6_thf_rebuild_claude/work/before_lodrepair/mm6_thf.glb --world mm6`.
