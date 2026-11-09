# MM9 Skraelos (mm9_skraelos) — 3D actor, 2026-11-04

Finish brief job 5 (`devdocs/mm9_rework/overnight/FINISH_BRIEF_20261104.md`). MM9 `MONSTERS.txt` row **257 "Skraelos"** (`Skraelos.abc`,
skin `skraelos.dtx`, NPCbase.scr, BaseName PeasantMale, Scale 1); the only row naming the model, one skin, no tiers. The Afterworld's
confessor: a hooded figure with a bare skull for a face, skeletal hands, a black tooled robe under an open rust tabard with a ragged,
blood-stained hem, a bone-fang necklace with a skull pendant, a long bone staff in the right hand and a skull held in the left.
Progress, hashes and Meshy receipts: `creature_3d_progress.json`. Status: `devdocs/mm9_rework/overnight/status/townsfolk_skraelos.md`.

## Why a new body
`claude_shared/mm9_meshcmp.py skraelos:<every MM9 ABC>` (`work/meshcmp_all.txt`): nothing shares the mesh. Closest after a rigid shift:
Colloidal Warrior (head 7.5 / torso 9.2 / arms 11.2 cm p90, other skeleton), Guard, Banshee, Scholar; the Wyrdes have the same 73 joint
names but the bind differs by 16 cm and the body by 6-39 cm. SKRAELOS.abc is MM9's human-female `FHP` skeleton (73 joints, eight skirt
chains, Ponytail/xpony chains, **no thighs**: Calf hangs from the Pelvis) with one finger chain per hand (Finger0 + Finger1); 603 faces;
1.71 m. The staff (37 vertices, 1.44 m) is skinned to `FHP R Finger1`, the held skull (15 vertices) to `FHP L Finger1`.

## What MM9 does with him (DAT objects and scripts)
`mm9_peasantf5_claude/scripts/dat_objects.py Skraelos`: Afterworld `Skraelos` and Hall of the Gods `Skraelos` (NPC336.scr: voice, the
confession / absolution quest, teleports; no clip calls), and a cutscene object (WG_NPC336.scr: `Loopanim stand`, visibility flags).
NPCbase looks up `Cower` (SKRAELOS.abc has none, so MM9 never cowers him: not carried). SKRAELOS.abc's own clips: `static`, `stand`, `walk`,
`conv1`, `fidget1`, `ResurrectSpell` (events playanimsound 0.5 s, DoResurrection 2.5 s), `statue` (bind). No run, hit, death or attack.

## Clips (30 fps)
| Role | Source |
|---|---|
| Standing / Walking / Fidget / Talk / ResurrectSpell | own `stand`, `walk` (MM9 keys no foot motion: a glide under the robe), `fidget1`, `conv1`, `ResurrectSpell` |
| Running / Hit / Death / Dead | PeasantFemale library `run`, `Wince2`, `Die1` (+ held end pose): the FHP library, joint names identical to SKRAELOS.abc's. BaseName PeasantMale names a Bip01 library that cannot drive FHP joints (Sigmund retargeted it; here the matching library needs no retarget) |
| attacks | Fidget (no attack clip; as the Wyrdes) |

Skirt chains damped toward Standing (`roles_sk.json` damp): Running 0.6, Death 0.6, Hit 0.7 (with the right arm: Wince2 drove the staff
hand into the face). Fingers keep the baked grip in every clip (no finger aliases): the props ride on the Hand bones.

## Route (`scripts/`, repo root via `scripts/bl.sh` for Blender, otherwise the project folder)
0. Sources `convert_sources.sh`; `mm9_dump.py`; reference renders `ref_renders.py` -> `review/mm9/`, input sheets `references_hd/mm9_*.png`.
1. Codex (`codex_slot.sh`): `codex_masters.sh 1|2` (brief `references_hd/CODEX_BRIEF.md`: calm, solemn skull, closed jaw, no props),
   `clean_alpha.py`; skull turnaround `codex_heads.sh 1|2` (`references_head/`). Sheets `review/masters_vs_mm9.png`, `review/head_masters.png`.
2. Meshy Smart Topology 15k of the body (`requests/smart_topology_v1.json`) and of the skull alone (`skull_topology_v1.json`);
   `step1_clean.py` (1.707 m) -> `work/raw.npz`, `work/skull_raw.npz`; `skull_prep.py` (cranium and jaw mirrored, teeth pieces kept,
   Meshy's eyeballs shrunk into small embers set back in the sockets, reduced) -> `work/skull.npz`.
3. `assemble_sk.py` (MM9 origin, pelvis 0, soles -0.885): robe+tabard shell and hood mirrored from +x, the hood's long back point
   compressed toward MM9's (y > 0 x 0.45), sleeves turned 11 deg and scaled onto MM9's arm; the skull on the Meshy face's eye line (14 cm
   wide); Meshy's face, eyes and bead necklace dropped; a dark neck tube from the foramen into the collar; procedural bone-fang necklace
   on a cord over robe and hood; an inner cap disc at -0.30 m; the +x skeletal hand (palm + 31 bone pieces, four digits) + a fifth digit
   copied from the outer finger, moved with the sleeve, mirrored -> `work/asm1.npz`.
4. Rig `rig_sk.sh` = `fit_rig_sk.py` (MM9 joints; arms on the sleeve axis; wrist before the finger bases; head pivot at the skull base;
   fingers from the bone-piece chains: first piece a metacarpal on Hand, the rest split 45/30/25 % by length, joints in the gaps),
   `weights_sk.py` (robe on the skirt chains and spine, hood rigid on Head above the jaw plane, skull rigid, every bone piece rigid on
   its bone), `build_glb_sk.py`, `clips_pf.py roles_sk.json` (soft offset line), arm jobs (`arm_jobs_sk.txt`: arm_clear + arm_soft),
   `arm_out_clip.py arm_clip_sk.txt`. `scripts/final_clip_pass.sh` reruns rig -> runtime -> install -> arm, prop and jitter gates.
5. `staff_place.py` (MM9's staff axis/length in R Finger1's frame, modelled as a long bone) -> `work/asm2.npz`; **`uv_sk.py` (never re-run:
   the paid paints belong to `work/uv.npz`)**: body 2K (hands 1.4x, cap 0.3x), head set (skull + staff 0.35x).
6. Paint: `make_upload_sk.py` (body; head = skull only), retextures 4K (`retexture_body_v1`, `retexture_head_v1`), `compose_sk.py`,
   AO `texpass_bake_ao.py` + `pad_ao.py`, `paint_fix_sk.py` (cap/neck near-black; the masters' necklace painted on the collar inside
   the hood -> black cloth; the rust tabard toned toward MM9's darker brown; the staff's charts as aged bone from the skull's cranium
   texels; the ember eye glow mask), `finish_sk.py` (gentle grade, ORM).
7. After the UVs `scripts/rebuild.sh <rev> [--install]`: `grip_sk.py` (staff on the right Hand at MM9's Standing Finger1 turn, moved to
   the palm side of the proximal phalanges; held skull on the left Hand, upright and facing forward in Standing, its crown in the
   curled fingers; per digit and joint the least turn into contact, opening first where a digit was inside), `copies_sk.py` (held skull
   and pendant as reduced copies of the painted skull with its UVs), `drop_degenerate.py`, `orient_parts.py` / `orient_comps.py`
   (necklace and cap winding), `reduce_parts.py` (hands, held skull, pendant, UVs kept), no linings (the cloth material is made
   doubleSided by `double_body.py`; `linings_wy.py` was used up to r5), paint fixes, grade, rig, `build_runtime_sk.sh` (prepare, LODs, shadow fix, specular 0 / metallic 0, winding,
   robe strips lifted, floor (+ a second `--raise Death` pass), doubleSided cloth, eye emission, mirror to true handedness), `viewer_update.sh`.
8. Binding (repo root): `flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock
   level_generation/creatures/mm9_skraelos_claude/scripts/bind_under_lock.sh`.

## Result (r10, installed 2026-11-04)

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_skraelos.glb` (`tools/install_model.py --world mm9`), = `export/mm9_skraelos.glb` (sha256 ccc1466b84cf...) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_skraelos_claude` (`scripts/bind_actors_sk.py` via `scripts/bind_under_lock.sh` under the flock): `MM9 257 Skraelos`, scale 100, yaw_offset -1.570796327, stride walk 1.4 (his walk keys no foot motion: a glide, so the stride only sets the playback rate) / run 1.1 (`stride.py`: PeasantFemale run 0.99-1.20 m), look Neck + Head, attacks play Fidget; script clips talk/conv1 -> Talk, stand, walk, fidget1, resurrectspell |
| Descriptor | row 257 in `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` (fallback 568 Lich A, the stand-in of `mm9_npc_legacy_replacements.tsv`); `mm9_monster_bodies.py --write-overrides` + tables: id 9257, height 174, radius 31 |
| Triangles LOD0/1/2/3 | 13,012 / 6,502 / 2,282 / 763 (robe+tabard 3,878, hood 1,038, skull 3,096, held skull 750 with its socket fills, pendant 179, staff 736, bone hands 2,300, necklace 975, neck tube and cap 72) |
| Skeleton | 108 joints: SKRAELOS.abc's 73 (rest rotations unchanged, translated onto the mesh) + 30 finger bones + 5 half-joint helpers |
| Textures | body (cloth, necklace, bone hands) colour 2K, normal + ORM 1K, **doubleSided** (no linings); head set (skull, teeth, ember eyes, staff; the held skull and pendant reuse the skull's UVs) colour 1K, normal + ORM 1K, emission mask on the ember eyes (red-orange, gentle pulse 0.15 / 2.5 s); one skin, no ramps; specular 0, metallic 0 |
| Meshy credits | **30 / 60**: body Smart Topology 5 (backup 2370 before), skull Smart Topology 5 (2350 before), body 4K retexture 10 (2345 before), head 4K retexture 10 (2335 before); no retries. Backup 2230 at the end (shared account) |
| Viewer | http://127.0.0.1:8912/level_generation/creatures/mm9_skraelos_claude/review/viewer/ revision `r10-20261104` |

## Gates (`review/gates_final/`; first build's numbers in `review/gates/`)

| Gate | Result |
|---|---|
| `arm_hand_gate.py --outer-only --exact` (48 fps) | **0 frames > 1 cm in every clip, both hands, except Death R 1.0 cm in 1 frame** (first build: ResurrectSpell L 6.0 cm / 24 f, Hit L 5.9 / 7 f + R 2.4 / 23 f, Death L 3.3 / 4 f, Cower R 1.9 / 42 f); forearms 0; finger stretch p99 <= 1.68 |
| `prop_gate.py` (new: staff / held skull vs the outer cloth, > 1 cm behind it within 6 cm, 24 fps) | held skull 0 in every clip; **staff FAILS: Fidget 2.5 cm (18 of 65 frames), Death 4.3 cm (15 of 45), Running 1.5 (2 of 19), Talk 1.8 (1 of 217)**: the staff section beside the grip goes into the sleeve cuff / robe front when the wrist bends (first build: Cower 5.1, Death 5.4, Hit 3.5, ResurrectSpell 2.8, Fidget 2.4) |
| `jitter_gate.py` (arm corrections vs the uncorrected clips) | **3 fails**: ResurrectSpell L upper arm 2.27 deg/f excess, shoulder skin 2.27 mm/f2; Death L shoulder skin 2.85 mm/f2, Death R 1.95 mm/f2 (round 1: 4, incl. Running R). Without the arm_clear jobs the hands went 5.6-5.7 cm into the body (ResurrectSpell L, Death R), so the jitter was kept |
| `floor_audit.py --world mm9 --match 'MM9 257*'` | ok: stand -0.1..+0.1, walk -0.1..0.0, living -2.1, dead 0.0 (before: dying sank -5.4, the staff tip mid-fall; fixed by a second `--raise Death` floor pass) |
| `check_winding.py` / `flat_shading_check.py` | 0 inverted closed parts / 0.00 body, 0.00 head |
| `detached_parts_audit.py` | 1: a 24-triangle robe piece on `xbk_rt_a3`, 0.83 cm off in 1 of 856 poses (Death); "root lift" lines are the separate bone pieces of the hands (by design) |
| `bone_length_audit.py` | FHP L Calf 0.42-0.47 m in Running and Hit: the PeasantFemale library's calf translation keys; there is no leg mesh under the robe |
| `texture_quality.py` | body atlas 64.2 %, spread 1.06, fragments 1.4 %, stretch p90 1.05; head set atlas 64.6 %, spread 3.86 (the staff at 0.35x by design), **fragments 6.0 %** (each tooth an island; target 3 %), stretch p90 1.37 |
| See-through (`see_through_gate.py double=1`: doubleSided materials drawn from both sides as the engine does; every 6th 30 fps frame, 8 azimuths x 0/20 deg, 3 mm px) | **torso <= 1 px, sleeve L <= 3 px, head 0, collar/sleeve R 0 in every clip** (`review/gates_final/see_through/`). r5 (one-sided cloth with linings): torso 10,452 px in Death / 7,370 Dead / ~200-250 standing clips, collar <= 117, sleeves <= 98; r9: sleeve L 22 px through the held skull's empty eye sockets (fixed by the socket fills) |
| Viewer `run_creature_review.py check` | 9 clips, 0 failed, 0 console errors |
| Regression `mm9_actor_models_build_every_binding` | **PASS**: 252 descriptors on 114 models, 0 failed (`review/gates_final/regression_binding.log`) |

## Sheets (read)
`review/masters_vs_mm9.png`, `review/head_masters.png`, `review/raw/sheet_parts.png` (Meshy parts), `review/raw/sheet_skull.png`,
`review/raw/sheet_grip.png` + `sheet_gripL.png` (grip at rest), `review/face_r8_sheet.png` (MM9 front + profile; front close-up, both
3/4, true profile, low 3/4, under the jaw, party view, party at 128 px; earlier `face_r1_sheet.png`, `face_r6_sheet.png`),
`review/sheet_body_vs_mm9_r8.png` (MM9 mirrored to true handedness vs ours, five views), `review/sheet_clips_r9.png` (every clip),
`review/sheet_hands_r10.png` (held skull; both hands: front, both 3/4, low), `review/fidget_r6/wide.png`, `review/clay/c1_sheet.png` ..
`c5_sheet.png` (clay clips, Cower and Wince1/Wince2 trials).

## Decisions and open points
- **Clips**: PeasantFemale library (FHP names) for run / hit / death instead of retargeting the PeasantMale (Bip01) library MONSTERS.txt
  names; Hit = Wince2 with both arms and the skirt damped 0.7 (Wince1 and undamped Wince2 drove the staff through the face); Cower
  dropped (MM9 has none for him). Attacks play Fidget.
- **Bone hands**: Meshy's separate phalanx pieces (four digits; a fifth copied from the outer finger), rigid per bone, reduced 45 %:
  faceted "bead" bones up close. The grip is baked (fingers do not follow MM9's mitten curl); props ride on the Hand bones with MM9's
  Standing Finger1 turn baked in, so in Fidget / ResurrectSpell the held skull is ~25-30 deg off MM9's.
- **Held skull** hangs from the fingertips on its crown (the claw could not close round it without entering the cuff); its empty eye
  sockets are backed by small spheres on the paint's darkest socket texel (the see-through gate saw the background through them).
- **Cloth doubleSided** instead of linings (as PeasantF7's head set): the robe's inside under the hem, the hood and the sleeves show the
  outer paint lit from the camera side.
- **Ember eyes**: Meshy's eyeballs shrunk and set back; up close they read as glowing orange balls rather than deep sparks.
- **Paint fixes**: the masters' fang collar painted on the collar and shoulders was refilled with cloth (the necklace is geometry);
  the tabard toned toward MM9's darker brown; the staff painted procedurally from the skull's bone.
- **Map placement not switched** (the orchestrator's): descriptor 9257 is ready; the maps still place the stand-in 568.

## Not checked
In game (no map places 9257); motion at normal speed in the viewer by eye (strips, clay and gates only); LOD1-3 and shadow meshes by eye;
the ResurrectSpell events (playanimsound, DoResurrection) are not bound to anything.

## Motion pass r11 (orchestrator pre-screen 2026-11-04; 0 credits) - current
Installed `mm9_skraelos.glb` sha256 ae3e9d438d6e... (rollback: the r10 numbers above). Gates in `review/gates_motion/`.
- **Staff in the fist on its own bone** `FHP R Staff` (child of the right Hand at the grip, `build_glb_sk.py`; the staff's weights moved to it,
  `weights_sk.py`). `scripts/staff_fix.py` (new, in `rig_sk.sh`): per clip, on the 30 fps keys, the least turn of the staff about the grip
  (searched over directions perpendicular to the shaft, 1 deg steps, cap 25) that keeps it out of the outer cloth, widened by a running
  maximum (0.2 s), Gaussian-smoothed (0.1 s), eased in/out over 0.3 s on one-shots. After the cuff change below it turns only Talk (2 deg) and
  Death (6 deg, a few keys).
- **Cuff rim follows the wrist a little** (`weights_sk.py`, CUFF_HAND 0.35 at the rim fading out over 6 cm, both sleeves): the shaft beside
  the grip had run into the cuff lip whenever the wrist bent (Fidget, Death); positions/UVs unchanged.
- **Arm corrections re-solved as smooth offsets** (`arm_clip_sk.txt`, `arm_out_clip.py`): the arm_clear jobs are off
  (`arm_jobs_sk.txt.off`); ResurrectSpell L 12 deg (constant from the start, eased out 0.5-1.1 s) + 12 deg eased in 4.8-5.3 s to the end,
  R 8 deg (constant, out 0.4-1.0 s); Death L 8 / R 10 deg (constant from the start, out 0.25-0.7 s); Fidget R 8 deg (in 0.1-0.5, out
  2.2-2.6 s); Running R 5 deg constant. Offsets held into Death's fast fall (or constant through it) failed the jitter gate (1.26 deg/f),
  so they end before it.

| Gate | r10 | r11 |
|---|---|---|
| prop_gate staff | Fidget 2.5 cm (18/65 f), Death 4.3 (15/45), Running 1.5 (2/19), Talk 1.8 (1/217) | **0 in every clip except Death 3.6 cm in 1 of 45 frames** (t 1.0 s, the staff's far tip against the robe lifted by the floor pass) |
| prop_gate held skull | 0 | 0 |
| arm_hand_gate | 0 frames > 1 cm except Death R 1.0 cm (1 f) | **0 frames > 1 cm in every clip** (worst Death L 0.4 cm) |
| jitter_gate | 3 fails | **0 fails** |
| floor_audit | ok | ok (stand -0.1..+0.1, walk -0.1..0, living -2.1, dead 0) |
| winding / regression | 0 / PASS | 0 / PASS (252 descriptors on 114 models) |
| see-through (double=1, step 6) | torso <= 1 px, sleeve L <= 3 | torso <= 1 px, sleeve L <= 3, head 0 (unchanged) |
Sheet (read): `review/sheet_motion_r11.png` (right hand and staff at the formerly failing frames: Fidget 0.6/0.92/2.12 s, Talk 3 s, Death
0.42/0.96 s, ResurrectSpell 0.1/5.6 s, both 3/4; Death and Fidget wide). Viewer revision `r11-motion-20261104`.

## Held skull: a real hold, r14 (user review 2026-11-04 "not holding the skull?"; 0 credits) - current
Installed `mm9_skraelos.glb` sha256 d001ce5546bc... (rollback r11: `work/rollback_r11_mm9_skraelos.glb`). Gates in `review/gates_hold/`.
- `grip_sk.py SKULL_MODE=hold` (`rebuild.sh`: SKULL_ALONG 0.13, SKULL_GAP 0.03): the skull (upright and facing forward in Standing, as
  before) sits 13 cm along the fingers from the knuckles and 3 cm to the palm side, so its crown is under the fingers and 5.8 cm clear of
  the cuff; `hold_fingers()` then sets each left digit joint (base to tip) to the flexion angle (fingers: across the finger toward the palm
  side; thumb: toward the skull's centre) that brings the rest of the digit closest to the skull without entering it (signed by the
  skull's own normals). The grip is baked into the rest pose; the skull stays rigid on `FHP L Hand`; the fingers keep the grip in every clip.
- `hold_eval.py` (rest): every digit in contact (min signed distance thumb 0.34, index 0.41, middle 0.12, ring -0.13, pinky 0.32 cm), no
  cloth inside the skull, cuff gap 5.8 cm. Grid of placements tried in `work/` (ALONG 0.03-0.13, GAP 0.03-0.08): the first pick (0.07 /
  0.04) put the crown into the cuff in every clip (prop gate 1.7-4.0 cm), so the skull went 6 cm further out.
- Death: the left wrist is damped 0.6 toward Standing with the skirt chains (the cuff folded onto the skull's jaw in the fall, 1.6 cm).
- Gates: held skull vs cloth **0 in every clip**; see-through torso <= 1 px, sleeve L <= 2, head 0; staff 0 except Death 3.6 cm in 1 of 45 frames (unchanged); arm/hand 0 frames > 1 cm;
  jitter 0 fails; floor ok; winding 0; regression PASS (252 / 114).
- Sheets (read): `review/hold_before_sheet.png` (r11) and `review/hold_after_sheet.png` (r14): left hand and skull in Standing, Walking,
  Fidget, Talk, ResurrectSpell, Running, Hit and Death, front / 3/4 / low, plus the user's angle (`user_party`).
- Left: the fingers lie over the crown and down the sides like MM9's mitten; in the front view the index runs across the crown with a few
  millimetres of air along its middle (the tip touches), and the bone hand is still the faceted "bead" bones.


**LOD0 reduced post-install on 2026-11-05 by `level_generation/creatures/mm9_skraelos_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_skraelos_reduce_claude/before/`.
