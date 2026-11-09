# MM9 Sigmund the Stressed (mm9_sigmund) — 3D actor, 2026-11-02

Overnight batch (`devdocs/mm9_rework/overnight/TOWNSFOLK_BRIEF.md`, `VARIANTS_BRIEF.md`): MM9 `MONSTERS.txt` row **247
"Sigmund the Stressed"** (L80, `sigmund.abc`, skin `sigmund.dtx`, NPCbase.scr, BaseName PeasantMale, Scale 1, Hostility 1); the only
row naming the model, one skin, no tiers. Route: the approved MM9 humanoid route (MM9 skeleton and MM9 clips, Meshy Smart Topology
+ 4K retextures on our UVs, MPFB five-finger hands, separate head set). Progress, hashes and Meshy receipts:
`creature_3d_progress.json`.

## Why a new body
`mm9_meshcmp.py` (orchestrator): 3-6 cm from PeasantM1/M1d with a different skeleton. SIGMUND.abc is not on the PeasantMale biped:
its 49 joints are an `FHP` (female-human-peasant naming) biped with a pelvis root, thighs under `FHP Spine`, one finger chain of
two bones on the left hand and a single `FHP R Finger11` on the right, a three-joint ponytail plus `XCOM_Hair`, and a mail-skirt
ring (`XCOM_skirt`, `x*`) under the pelvis. 1.74 m.

## SIGMUND_CHILD.abc
SIGMUND.abc's LithTech `ChildModels` list names `sigmund_child.ABC` (bytes in the ABC; no script or DAT object names it): MM9
loads it as the animation donor of SIGMUND.abc. It is the same skeleton and mesh with three clips, **stand, fidget, walk**, which
are Sigmund's Standing, Fidget and Walking here (included, not a separate model).

## What MM9 does with him (DAT objects and scripts)
`dat_objects.py Sigmund` over the rebuilt maps' raw objects:
- Drangheim City `SigmundtheStressed0` (no script -> NPCbase.scr: Converse finds no conv clip, BaseRun's `GetAnimNbr Cower` is -1);
- Afterworld `SigmundtheStressed` (NPC87.scr: Rude, quests, `loopanim Sit` when shown; SIXFIRES.inc toggles its visibility);
- Thronheim City `Sigmund` (ARG_Sigmund.scr, the Argument cutscene: `loopanim Sit` (Init, Idle, Done); `PlayAnim Agree` (Agree
  exists in SIGMUND.abc, unlike Kira's/Markel's); `playAnim Applause` + Clap keys; `Sc2_Sigmund1b` on Shot1A (Sign key);
  `Sc2_Sigmund1c` on Shake; `Sc2_Sigmund3b` on Speak3 (Voice3 key));
- props on `Sigmund.abc` with `PropAnim.scr`: Afterworld and Yorwick `sigmund` (`Static_die1`), Thronheim `SigmundProp` (`Sit`).
SIGMUND.abc and sigmund_child have **no run, attack, hit or death clip**; the engine requires hit/dying/dead/attack. The row's BaseName
is PeasantMale, so **Running, AttackMelee, Hit and Death are the PeasantMale library's run, hattack1 (Rattack 0.5 s), wince1 and die1,
retargeted onto the FHP skeleton** (`scripts/retarget_mm9.py`: world-rotation copy, W_t = W_s W_s,rest^-1 W_t,rest per mapped joint,
the unmapped hair/skirt joints keep their rest local rotation, root translation copied; `scripts/retarget_pmale.json`;
`source/mm9_lib/pmale_on_sigmund.glb`; sheet `review/retarget/sheet_retarget.png` on MM9's own mesh). Not carried: Talk and Cower
(MM9 plays neither on this model), the bind clip `sigmond`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_sigmund.glb` (`tools/install_model.py --world mm9 --name mm9_sigmund.glb` from `export/mm9_sig.glb`, sha256 4846e11dce17...) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_sigmund_claude` (`scripts/bind_actors.py` under the flock): `MM9 247 Sigmund the Stressed`, scale 100, `yaw_offset -1.570796327`, stride walk 1.34 / run 2.8 (`stride.py`: walk 1.32-1.37 m; the retargeted run is planted only 10 % of its cycle, 3.4-4.1 m read; 2.8 as Markel's on the same PeasantMale run), look `FHP Neck, FHP Head`, impact 0.5 s |
| Rows | `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv`: 247 -> 403 (Swordsman A, the stand-in of `mm9_npc_legacy_replacements.tsv`); tables regenerated, descriptor 9247; body override **174 / 31** (MM9's rule; our model 1.74 m) |
| Triangles LOD0/1/2/3 | 13,236 / 6,618 / 2,380 / 789 (Smart Topology 16,135 -> 8,909 reduced + MPFB hands 2 x 700; linings and the hair twin ~4,400, one texel each, out of the shadow meshes) |
| Skeleton | SIGMUND.abc's 49 FHP joints, names and rest rotations unchanged, joints translated onto our body (`fit_rig.py`; `centre_interp` Pelvis/Spine3: MM9's low-poly slices there hold back vertices only), + 15 MPFB finger bones per side (left: Finger1/11 drive each finger's 1/2(/3); right: MM9's single R Finger11 drives the MCPs, the outer joints follow at 0.6/0.35); mirrored to MM9's true handedness (`mirror_glb.py`) |
| Clips (30 fps) | child model `source/mm9/sigmund_child.glb`: Standing stand 2.63, Walking walk 1.37, Fidget fidget 2.37; own `source/mm9/sigmund.glb`: Sit sit 1.7 (loop), Agree 5.2, Applause 3.0, Sc2_Sigmund1b 6.03, Sc2_Sigmund1c 4.03, Sc2_Sigmund3b 7.2, StaticDie static_die1; retargeted PeasantMale: Running run 1.03, AttackMelee hattack1 1.03, Hit wince1 1.03, Death die1 1.47, Dead |
| Textures | body 2K colour + 1K normal/ORM; head + hands set 2K colour + 1K normal/ORM; one skin, no region mask; specular 0, metallic 0 |
| Meshy credits | **25 / 50**: Smart Topology 5, body 4K retexture 10, head 4K retexture 10 (backup 2640 -> 2520 over both models' jobs; shared account) |

## Route (scripts/, repo root unless noted)
0. Sources `convert_abc_model.py --scale 0.0256` (SIGMUND, SIGMUND_CHILD with skin SIGMUND; PEASANTMALE library copied from
   mm9_peasantm7_claude); `ref_renders.py`, `input_sheets.py` -> `references_hd/mm9_*`.
1. Codex via `codex_slot.sh`: `codex_masters.sh 1|2` (brief `references_hd/CODEX_BRIEF.md`; a calm, careworn, worried man, not
   angry), `clean_alpha.py 200`; head turnaround `codex_head.sh a` -> `references_head/` (`review/head_check.png`).
2. Meshy Smart Topology 15k from `00_three_quarter.png`. **`sym_meshy.py` with `HEADF=0.86`** (new: the head is centred on its own
   nose before the mirror and the midline relax band is 2.5 mm on the head: mirroring about the torso plane with the 1.2 % body band
   narrowed the face into a V and flattened nose and lips; `review/face_chain.png`, `review/face_sym2.png`) -> `fit_rig.py` (X-ray
   `review/xray_v1.png`) -> `reduce_uv.py` -> `sym_rigged.py` -> `graft_hands.py graft_sig.json` (per-side `template_R`: the right
   hand has no Finger1) -> `head_split.py head_sig.json` -> `eye_fill.py 8,9` -> `drop_parts.py 8,9` -> `cuff_trim.py -0.02` ->
   `triangulate.py` = `work/eyes_v1.blend`.
3. UVs (never re-run): `texpass_uv.py` (body 65.1 %), `relayout_head_sig.py` (face as one chart, head upload; 55.0 %).
4. Paint: `bake_ao_texpass.py`, `compose_texpass.py sig_tp`, gentle grade, `bake_hands.py` (middle-aged caucasian male skin),
   `compose_headhand.py sig_tp meshy/head_tp ...` (backup `work/sig_tp_head_basecolor_composed.png`), then
   **`scripts/head_paint_sig.sh`** (`MX=0.028`): `face_fix_dboy.py` (closed lips, a little toward the cheek hue), `eye_rims.py`
   (red rims and under-eye darkness toward the cheek), `chin_spot.py` (a dark speck on the chin), `hand_clean.py` (the first hand
   grade had caught the blond hair: yellow hands).
5. Geometry after the paint: `midline_weld.py` -> `mouth_relax.py` (CZ 0.634 RX 0.028 RZ 0.016, 12 iters: the pouting upper lip)
   = `work/geo_v2.blend` -> `TUCK_DEEP=0.014 sleeve_tuck.py 0.75 0.003 1` (the hand stub poked out of the bracer ends; FHP names) =
   `work/geo_v3.blend` -> **`scripts/linings_sig.sh`** (`SRC=geo_v3`: neck cap (none needed), hair twin of the head shell's hair
   faces, rim linings of the mail collar, hauberk hem, boot tops, short sleeves, bracer ends) = **`work/linings_v1.blend`**.
6. Runtime `TOKEN=<lease> scripts/build_runtime_sig.sh [--install]` (memory-capped): export, `clips_mm9.py roles_sig.json`,
   **`arm_const.py`** (`arm_const_sig.txt`: a constant 4-6 deg shoulder abduction on the standing clips, Kira's: the hands hung
   2-4 cm into the fuller mail hips), `arm_clear.py` + `arm_bump.py` (`arm_bumps_sig.txt`: Applause, Sc2_Sigmund1b, Sc2_Sigmund3b),
   prepare, LODs, shadow fix, extras, floor fix (`floor_ops.txt`: seated clips grounded like Sit, Running and StaticDie grounded),
   **`drop_lod_slivers.py`** (a 6-triangle LOD2 sliver of the lining rims read as an inverted closed part), mirror, winding.
   Viewer `python3 scripts/make_viewer_manifest.py <rev> "sig=...=export/mm9_sig.glb"`; binding `flock -x
   level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock bash -c 'python3
   level_generation/creatures/mm9_sigmund_claude/scripts/bind_actors.py && python3 tools/mm9_import_discovery/generate_mm9_monster_tables.py'`.

## Face (the user reviews it close)
The Meshy head (Codex turnaround: a careworn, worried, kind man; MM9's Sigmund is "stressed", not angry) came with a pouting
upper lip (3.8 mm ahead of the philtrum), red lower lids and a dark chin speck, and the hand grade had picked up the blond hair
(yellow hands). Fixed: `mouth_relax.py` (depth only, never forward, corners up 1.2 mm), `face_fix_dboy.py` (closed lips),
`eye_rims.py`, `chin_spot.py`, `hand_clean.py` (cheek skin 199/124/92). The mid-face is the Meshy head symmetrised about its own
nose (`sym_meshy.py HEADF=0.86`); the midline needle pairs welded (`midline_weld.py`: dark X pinches on the forehead and chin).
Sheets read (viewer-like EEVEE light): `review/sheet_faces_r4.png` (MM9 head views; front close-up, 3/4, true profile, low 3/4 from
below, party view, both ears, 128 px simulation; body front/3-4/back), `review/faces/r2_zoom.png` (after the mouth relax; before:
`review/faces/r1_zoom.png`). Left: the brows are heavy and drawn up (worried) as painted; the lips stay a gently downturned
closed line (a stressed man, not a smile).

## Checks (final build, `review/gates/`)
| Gate | Result |
|---|---|
| Arm and hand (`arm_hand_gate.py --outer-only`, 15 clips) | **0 frames over 1 cm, both hands, every clip** (before: Standing R 4.2 / L 1.9 cm, 93/127 frames - the hands hung into the fuller mail hips; Applause 2.2/2.8 cm; Sc2_Sigmund3b R 6.0 cm; Sc2_Sigmund1b L 2.3 cm). Worst left: Applause 0.9 cm (the clapping hands meet) |
| Jitter (`jitter_gate.py` vs the clips before the arm fixes) | **0 fails** (Hit had failed at 2.3-2.9 mm/f2 shoulder skin from the floor pass's per-key grounding: `--ground-loop Hit` dropped; Sc2_Sigmund3b's fade lengthened) |
| See-through (`see_through_gate.py`, all 15 clips every 3rd frame, 3 mm px) | head 10 px (Death, under the hair), sleeve R 4, torso 2, boots 1-2, sleeve L 1, collar 0, trousers 0 (`review/gates/see_through_r1/`) |
| Sleeve poke (`sleeve_poke_gate.py`, FHP names) | 0 mm in every clip; it finds no cuff rim on the bracers (rim vertices 0), so the wrist close-ups were judged too (`review/faces/hands_r3.png` before the tuck: the stub poked out of the bracer; fixed by `sleeve_tuck.py`) |
| Floor (`floor_audit.py --world mm9 --match 'MM9 247 *'`) | stand 0.0, walk -0.2..+1.1, living -0.4, dead 0.0: ok; seated clips grounded like Sit (`floor_ops.txt`) |
| Detached (`detached_parts_audit.py`) | **2 reported**: the two boot shells (with their linings, 689 triangles each) sit up to 4.7 mm off the calf: a boot around the leg, not a floating piece (`review/faces/boots.png`); no other part |
| Winding / bones / flat | 0 inverted (after `drop_lod_slivers.py`: a 6-triangle LOD2 sliver); 12 checked, 0 stretching; flat 0.00 on both materials |
| Texture quality | body atlas **65.1 %**, fragments 0.9 %, stretch p90 1.07 (spread reported infinite: one-texel lining faces); head set **39.2 %** (hands at half density by design; below the 55 % target, as the boy's), fragments 1.5 %, stretch 1.20 |
| LOD0 | 13,236 triangles (< 15k) |
| Viewer (`run_creature_review.py check`) | 15 switches, 0 failed, 0 console errors (revision r2-20261102) |
| Regression `mm9_actor_models_build_every_binding` | **PASS** (246 descriptors on 109 models, 0 failed; `review/gates/regression_binding.log`) |

## Sheets read
`review/sheet_mm9_vs_ours.png` (MM9 front/3-4/back vs ours), `review/sheet_faces_r4.png`, `review/faces/r1_zoom.png`,
`review/faces/r2_zoom.png`, `review/faces/hands_r3.png`, `review/faces/boots.png`, `review/sheet_clips_final.png` (all 14 clips,
front and 3/4), `review/clips_fail.png` (the seated cutscene contacts before the fixes), `review/retarget/sheet_retarget.png`,
`review/face_chain.png`, `review/face_sym2.png`, `review/xray_v1.png`, `review/masters_check.png`, `review/head_check.png`.

## Deviations and open points
- Running, AttackMelee, Hit and Death are retargeted PeasantMale clips (SIGMUND.abc has none); the hair and mail-skirt joints keep
  their rest pose in them (the skirt follows the pelvis and thighs through its weights).
- Seated clips (Sit, Agree, Applause, Sc2_*) sit on an invisible chair, grounded at the feet (the Argument scene's chairs are props).
- The constant shoulder abduction (4-6 deg) on the standing clips holds the hands clear of the hauberk; the clapping and the
  Sc2_Sigmund3b hand-on-arm gestures were eased apart (arm_bump.py) and touch less than MM9's.
- Not looked at in game (placement still uses the legacy stand-in 403: the orchestrator's switch); LOD1-3 and shadow meshes not
  looked at; motion judged on strips and gates, not watched at speed; sounds; Android cook.


**LOD0 reduced post-install on 2026-11-05 by `level_generation/creatures/mm9_sigmund_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_sigmund_reduce_claude/before/`.
