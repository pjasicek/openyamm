# MM9 Markel the Great (mm9_markel) — 3D actor, 2026-11-02

Townsfolk batch, wave 3 unique (`devdocs/mm9_rework/overnight/TOWNSFOLK_BRIEF.md`). MM9 `MONSTERS.txt` row **248 "Markel the Great"**
(MARKEL.abc, skin MARKEL.dtx, NPCbase.scr, BaseName PeasantMale, Scale 1); the only row naming the model, one skin, no tiers.
Built on the Bjarni/PeasantM7 route: Meshy body fitted to MARKEL.abc's own skeleton (the 45-joint PeasantMale biped), MM9's
PeasantMale library clips plus Markel's own clips, MPFB five-finger hands, separate head set. Receipts and hashes:
`creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_markel.glb` (sha256 be0bcbda7dd0..., hair reshape r3; `tools/install_model.py --world mm9 --name mm9_markel.glb` from `export/mm9_mk.glb`) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_markel_claude`: `MM9 248 Markel the Great`, scale 100, `yaw_offset -1.570796327`, stride walk 1.1 / run 2.8, look `Bip01 Neck, Bip01 Head`, impact 0.5 s (hattack1 Rattack); script clips below |
| Descriptor | row 248 appended to `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` (fallback legacy 579 "Merchant C", the existing stand-in of `mm9_npc_legacy_replacements.tsv`), tables regenerated: 9248 `MM9 248 Markel the Great` |
| Triangles LOD0/1/2/3 | 8,169 LOD0 after the hair reshape (was 8,292 / 4,140 / 1,483 / 488; body 3,594, head set 4,575 incl. hands 1,398) |
| Skeleton | MARKEL.abc = PeasantMale, 45 joints (names identical to `source/mm9_lib/pmale.glb`), rest rotations unchanged, joints translated onto the HD body (moves <= 6.4 cm); + 15 MPFB finger bones per side driven from MM9's mitten curl (`finger_alias`); whole model mirrored to MM9's true handedness (`mirror_glb.py`) |
| Textures | body 2K colour + 1K normal + 1K ORM; head + hands set 2K colour + 1K normal/ORM; no region mask (one skin); `openyamm_specular 0`, metallic 0 |
| Meshy credits | **25** (Smart Topology 5, body 4K retexture 10, head 4K retexture 10; backup account 3350 -> 3325 before the retextures, no retries) |

## Hair reshape r3 (2026-11-02, orchestrator review: "the back hair is a big bulbous mass sticking out behind the head and down the upper back") - current

Smart Topology's hair shell hung 13-15 cm behind the neck down to the shoulder blades (`scripts/hair_probe.py`: hair back extent
+0.20..+0.23 m against the skull's +0.05..+0.10 m). MM9's Markel has nape-length hair hugging the skull. 0 Meshy credits.
- **Geometry** `scripts/hair_reshape.py work/final_v1.blend work/hair_v1.blend` (positions, deleted faces and weights only; UVs of the
  kept faces unchanged): hair faces wholly below z 0.665 (Blender; the nape, inside the raised fur collar) deleted (136 faces); every
  other hair vertex further than T from the skull/neck shells moved radially onto that offset (T 1.5 cm above the ears easing to
  0.8 cm at the nape; the sunk bald crown untouched), 4 Laplacian passes; every hair vertex takes the nearest skull/neck vertex's
  weights (the old tail carried Spine2/Neck weights). Hair back extent now +0.06..+0.11 m (1-1.5 cm off the skull).
- **Paint**: the fur mantle behind the neck carried Meshy's paint of the hanging hair and its shadow (a brown/grey dome,
  `review/hair_r1.png`): `scripts/mantle_fix.py` (after `sleeve_paint_fix.py`) finds the body texels within 2.2 cm of the old tail
  (from the rollback GLB) and refills them by reflecting the fur above in the same column (a luminance-ramp recolour came out flat
  grey-beige, `review/hair_r2.png`). The light U-shaped band across the back of the head was neck-skin paint on the hair shell
  (Meshy's nape) plus a hard zone edge: `back_hair.py` now also recolours pinkish skin texels of the back hair and uses soft zone
  edges; `scripts/pad_head.py` re-pads the head set's gutters from the islands themselves (run last). The band is gone (`review/hair_r6.png`).
- Chain now: `sleeve_paint_fix.py` -> `mantle_fix.py`; `bald_crown.py` -> `back_hair.py` -> `spot_fix.py` -> `hand_clean.py` -> `pad_head.py`;
  `BLEND=work/hair_v1.blend scripts/build.sh --install`. Rollback of the r2 install: `work/rollback_r2/` (installed GLB, export, head
  colour and normal, final_v1.blend, viewer GLB).
- Collar check (Blender, back and both sides): Sit, Applause, Sc2_MARKEL02/04, Sc2_Markel13/15, Talk, Death, Sc2_markel21, StaticDie -
  the hair ends inside the fur collar, nothing pokes through (`review/hair_clips.png`, read as `hair_clips_1.png` / `hair_clips_2.png`).
- Gates (`review/gates_hair/`): arm/hand identical to gates_final; sleeve poke 0 mm in all 20 clips; jitter 0 fails; detached 0;
  winding 0; flat 0.0 %; floor ok (stand 0, walk -0.2..+1.8, dead 0); bones as before (MM9 hip slide); texture body unchanged
  (59.3 %), head set 39.1 % (was 43.8 %: the tail's charts are gone), stretch p90 1.63 (was 1.30: the hair charts are now on a
  smaller surface, so denser and somewhat anisotropic - above the 1.5 target, not repainted). Viewer r3-hair-20261102 check 20 / 0
  failed. Binding regression `mm9_actor_models_build_every_binding` **PASS** (187 descriptors on 80 models).
- Sheets read: `review/sheet_hair_head_before_after.png` (MM9 / before / after: 3/4, left, back, right head close), 
  `review/sheet_hair_body_before_after.png` (same, full body), `review/sheet_hair_viewer.png` (viewer: back, left, 3/4 Standing, Sit back,
  Sc2_MARKEL02 left, Sc2_Markel13 right, Walking rear, StaticDie), `review/collar_back.png`, `review/hair_r6.png`.
- Left: a small gold facet on the back of the collar at the neck (a chart of the torc's paint, previously under the hair); faint
  mirrored-fur repeats in the refilled mantle patch at close range.

## What MM9 does with him (DAT objects and scripts)

`scripts/dat_objects.py`-style survey of `assets_dev/worlds/mm9/maps/*.raw_objects.yml` (every object naming Markel):
- Guberland City `MarkeltheGreat0` (NPC127.scr: `loopanim Sit`, vanishes on keys 40/108);
- Afterworld `MarkeltheGreat0` (no script -> NPCbase.scr -> BaseRun.inc `LoopAnim Cower`; hidden);
- Thronheim City `Markel` (ARG_Markel.scr, the Argument cutscene; its Filename property says Kira.abc, the class gives the body):
  `loopanim Sit`; Applause (Clap keys); Sc2_MARKEL02/04/08/10/13/15 on Scene2/Speak4/8/11/13/15, each back to Sit; `walkto`
  (Walking) on Move; Sc2_markel21 on Kill, then `loopanim static_die2`; `PlayAnim Agree` (no Agree clip exists in MARKEL.abc or
  the PeasantMale library: left unbound);
- Thronheim props `MarkeProp` (PropAnim Sit) and `MarkeProp0` (PropAnim static_die2).
No `Attach` call, no socket and no separate .abc: the book in the Argument scene is its own prop (Prop8). Nothing is held.

## Clips (30 fps)

Library (`source/mm9_lib/pmale.glb`, copied from mm9_peasantm7_claude): Standing stand1, Walking walk3, Running run, Fidget
fidget4, Talk conv2, AttackMelee hattack1, Hit wince1, Death die1, Dead (die1 end pose), Cower cower. Own (`source/mm9/markel.glb`):
Sit, Applause, Sc2_MARKEL02, Sc2_MARKEL04, Sc2_Markel08, Sc2_Markel10, Sc2_Markel13, Sc2_Markel15, Sc2_markel21, StaticDie
(static_die2). `script_clips` keys are the lowercased MM9 names (`sc2_markel08` for the script's `Sc2_MARKEL08`, clip `SC2_Markel08`).
Seated clips are grounded like Sit (`floor_fix --seat-like Sit`, as Bjarni); Sc2_markel21 and StaticDie share one offset that grounds
the corpse (MARKEL.abc's death clips sit 0.76 m above its standing origin).

## Route (scripts/, one project folder; most scripts copied from mm9_bjarni_claude / mm9_sven_claude)

0. Sources `convert_abc_model.py --scale 0.0256` -> `source/mm9/markel.glb`; renders `ref_renders.py` -> `references_hd/mm9_views.png`,
   `mm9_head_views.png`, `mm9_skin_x4.png`. HD masters by Codex (`codex_masters.sh 1|2`, brief `references_hd/CODEX_BRIEF.md`, halo
   removed by `clean_alpha.py`, raw returns `references_hd/raw_codex/`); head turnaround `codex_head.sh` -> `references_head/`.
1. Smart Topology 15k from `00_three_quarter.png`; `fit_rig.py` (`fit_config.json`, no `centre_span`), X-ray `review/xray_v1.png`;
   `reduce_uv.py` -> `work/rig_v1.blend`; `graft_hands.py graft_mk.json`; `head_split.py head_mk.json` (parts 1, 2, 6, 10, 11 = face shell,
   hair shell, neck, eyes; the collar tie parts 15/31 stay in the body set; no level cut through the body shell); `fix_flips.py` (2);
   `sleeve_tuck.py` -> `work/head_tuck.blend`.
2. UVs `texpass_uv.py` (body 59.5 %) and `texpass_head_uv.py` (62.3 % of the head square) -> `work/texpass_head.blend`. Never re-run.
3. Retextures 4K (`requests/retexture_body_tp.json`, `retexture_head_tp.json`); `bake_ao_texpass.py`, `compose_texpass.py`, gentle grade,
   `bake_hands.py` (middleage caucasian male), `compose_headhand.py --ref-head --hand-gain 1.12`, then the head-paint chain below and
   `sleeve_paint_fix.py export/mm9_mk.glb` (11,288 skin texels near the cuffs).
4. Geometry after the paint (positions/weights only, UVs unchanged): `crown_shrink.py` (crown_v3, gap -3 mm), `cuff_trim.py -0.022`,
   `bracer_rigid.py`, `TUCK_DEEP=0.014 sleeve_tuck.py`, `accessory_weights.py`, `drop_micro_parts.py` -> **`work/final_v1.blend`**.
5. Runtime `BLEND=work/final_v1.blend scripts/build.sh [--install]` (wraps `build_runtime_v2.sh mk Markel scripts/roles_mk.json`):
   export, `clips_mm9.py` (soft offsets), `hand_rest.py` per `hand_rest_mk.txt`, `clap_spread.py` per `spread_mk.txt` (new hook in the
   build script), prepare, LODs, shadow fix, extras, `floor_fix.py` (`floor_ops.txt`), `mirror_glb.py`, winding.
6. Binding (repo root): `flock level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock bash -c 'python3
   level_generation/creatures/mm9_markel_claude/scripts/bind_actors.py && python3 tools/mm9_import_discovery/generate_mm9_monster_tables.py'`,
   then `level_generation/projects/mm9r_common/review_root.py`. Viewer `scripts/make_viewer_mk.py <rev>`. Gates `scripts/gates.sh <dir>`.

## Face (the batch's failure point) — head-paint chain

Order: `bald_crown.py` -> `back_hair.py` -> `spot_fix.py` -> `hand_clean.py` (each on `textures/mk_tp_head_basecolor.png`; bald_crown
restarts from `work/mk_tp_head_basecolor_composed.png`, so run the whole chain after any change).
- **Bald crown.** MM9's Markel is bald on the crown with a high receding hairline. Smart Topology modelled a full hair cap and Meshy
  painted hair over it with a jagged bald streak (the rejected "pale jagged fringe"). `bald_crown.py`: head-set texels inside a top-view
  ellipse over the crown take the forehead's skin (median x 0.93, a 3D-sinusoid mottle so no chart-seam steps, the forehead's grain),
  feathered into the hair with elongated strand noise; normal map flattened there; gutters padded. `crown_shrink.py` sinks the hair
  shell's crown 3 mm under the face shell (the cap's front edge stood as a wavy step across the forehead). Sheets
  `review/sheet_face_mm9_vs_ours_r1.png` (before), `review/brow_r1.png` .. `brow_r4.png`.
- **Back hair.** The hair shell's tail behind the neck was painted cream fur with a hard edge (a pale patch from behind,
  `review/back_r1.png`). `back_hair.py` recolours those texels by luminance quantile to the hair's own colours (the strand detail
  stays); a 3D strand copy was tried first and came out as a patchwork (`review/back_r2.png`). A soft tonal band remains where the old
  edge was (`review/back_r5.png`).
- **Speck under the right eye.** Face 5653 (an 8 mm triangle) maps onto a 10 px UV sliver of the lower lid's lash line, so it rendered
  as a dark triangle. `spot_fix.py` refills its texels from the 3D-nearest skin texels of the faces round it (a flat colour stayed
  visible, r6-r7); a faint edge remains in tight close-ups. A lighter triangle beside the nose was tried the same way, came out darker,
  and keeps Meshy's paint. The generic part of `spot_fix.py` also clears beard-brown specks at the lower lids (4,506 texels).
- Eyes open, light blue irises visible from party height, one relaxed brow per side, closed mouth with a mild smile, no pout, no red
  rims, no dark nostril triangles, no head/body seam (the beard meets the fur collar; the neck is in the head set). Hands: one clean
  skin colour (`hand_clean.py`).

## Hands, wrists, arms

- **Wrists:** the stub's toothed cuff rim showed as skin wedges through the leather cuffs (`review/wrist_R_r1.png`; sleeve gate 9-27 mm
  on one side in every clip). `cuff_trim.py -0.022` cuts the cuff 2.2 cm above the hand joint to a clean ring, `bracer_rigid.py` makes
  the cuff follow the forearm rigidly, `sleeve_tuck.py` (TUCK_DEEP 1.4 cm) re-tucks and reweights the stub: **0 mm in every clip, both
  sides**. Sheets `review/wrists_final_R.png`, `review/wrists_final_L.png`.
- **Hand rest / jitter** (trials with `/tmp`-style scratch runs of hand_rest.py + jitter_gate.py per clip): default filters for Fidget,
  Applause, Sc2_Markel08/10/13; Talk L `--sigma-dir 0.25` (0 cm, jitter pass); Talk R one eased 9 deg abduction (`clap_spread.py`, as
  Sven); Sc2_MARKEL04 L (MM9's hand at the chin, 17 cm into our fur collar/beard) capped at 5 cm (`--max-push 0.05 --sigma-dir 0.3
  --sigma-time 0.15`): full pushes cleared it but jittered 2.2-6.0 deg/f over MM9; Sc2_markel21 R (hand on the stab wound) capped at 10 cm.

## Checks (final, `review/gates_final/`)

| Gate | Result |
|---|---|
| Arm and hand (`arm_hand_gate.py`, every clip, 48 fps) | hands 0 frames > 1 cm except **Fidget R 1.4 cm (4 f)**, **Applause L 2.3 / R 2.2 cm (59/64 f: hand against hand at the claps)**, **Sc2_MARKEL04 L 3.7 cm (48 of 578 f, the capped chin gesture)**, **Sc2_Markel08 L 2.4 cm (9 f)**, **Sc2_markel21 R 2.4 cm (7 f)**; forearms up to 5.7 cm (Sc2_Markel13 R), 5.0 (Sc2_MARKEL02 L); finger stretch p99 <= 1.6, max 2.91; wrist max 119 deg (MM9's limp death hand); 19 joints per hand |
| Sleeve/wrist poke (`sleeve_poke_gate.py`) | **0 mm, 0 frames, all 20 clips, both sides** (was 9-27 mm) |
| Jitter (`jitter_gate.py` vs MM9's clips) | **0 fails** (r1: 4, r2: 3) |
| Floor (`floor_audit.py --match 'MM9 248*'`) | ok: stand 0, walk -0.2..+1.8, living -0.2, dead 0.0 (walk smoothing 0.04 s; 0.12 s lifted every foot 3.3 units) |
| Winding | 0 inverted closed parts |
| Bones (`bone_length_audit.py`) | R Thigh 11.0-12.3 % (Sc2_markel21, Sc2_Markel13): MM9's own hip slide, as the PeasantMale siblings |
| Detached (`detached_parts_audit.py`) | **0 detached** in any pose (was 7: belt/trim pieces, fixed by `accessory_weights.py`) |
| Flat shading | 0.0 % both materials |
| Texture quality | body atlas **59.3 %**, density 1362/1409/1450 (spread 1.06), fragments 0.1 %, stretch p90 1.09; head set 43.8 % of the 2K image (head square + hand squares), spread 2.07 (hands half density by design), fragments 1.4 %, stretch 1.30 |
| Viewer (`run_creature_review.py check`) | 20 clip switches, 0 failed, 0 console errors (r2-20261102) |
| Regression `--world mm9 --headless-run-regression-suite actors` (final install) | passed 192, failed 1 (the known out05 "could not load gameplay data"); `mm9_actor_models_build_every_binding` **PASS**; log `review/gates_final/regression_actors_final.log` |

Sheets read: `review/sheet_mm9_vs_ours.png` (MM9 vs ours, five views), `review/sheet_face_mm9_vs_ours.png` (MM9 vs ours front, 3/4,
side, party view 22 deg, eyes, neck both sides), `review/sheet_face_viewer.png` (viewer head four views), `review/sheet_body_viewer.png`,
`review/sheet_wrists_viewer.png`, `review/sheet_clips_1.png` + `review/sheet_clips_2.png` (every clip at 15/50/85 %, 3/4 and front),
`review/wrists_final_R.png`, `review/wrists_final_L.png`, `review/back_r5.png`, `review/eyes_r8.png`.
Viewer: `http://127.0.0.1:8912/level_generation/creatures/mm9_markel_claude/review/viewer/index.html`.

## Binding plan (map placement)

The rebuilt maps place `MarkeltheGreat` objects with the legacy stand-in (579) through `transcode_mm9_dat_to_odm.py`, so descriptor
9248 does not show in game yet. Per the brief this switch is the orchestrator's (one change for every row after the batch); the
Thronheim `MarkeProp`/`MarkeProp0` PropAnim props and the ARG cutscene clips need the same descriptor plus script-clip playback.

## Deviations and open points

- **Rings:** MM9's skin gives him gold rings; the grafted MPFB hands are plain skin (no rings painted).
- **Hair volume:** reshaped to nape length hugging the skull (r3 above); no braid modelled (MM9's short braid at the nape is in the paint only).
  The bald crown is shaped by the face shell (the hair cap sunk under it).
- **Agree** (ARG_Markel.scr) has no source clip; left unbound.
- Sc2_MARKEL04 left hand stays 3.7 cm into the fur collar at the chin in 48 frames (jitter vs penetration trade-off above).
- Handedness: `references_hd/mm9_*` renders are of the raw conversion (the mirror image); the installed model is mirrored to MM9's true
  handedness, so left/right details in the MM9-vs-ours sheets appear swapped.
- Not looked at in game (no map spawns the descriptor yet); motion judged on strips and gates, not watched at speed; LOD1-3 and shadow
  meshes not looked at; the Afterworld/Thronheim script behaviour itself not exercised.
- User artistic acceptance: not recorded.


**LOD0 reduced post-install on 2026-11-05 by `level_generation/creatures/mm9_markel_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_markel_reduce_claude/before/`.
