# MM9 PeasantM7 human townsman (mm9_peasantm7) — 3D actor, 2026-11-01

Townsfolk batch (`devdocs/mm9_rework/overnight/TOWNSFOLK_BRIEF.md`). MM9 `MONSTERS.txt` rows naming `PeasantM7.abc`:
**51 Commoner** "Peasant Human2 MaleA B", skin PEASANTM7B, DAT class `CommonerHuman2MaleB` (20 placed objects), and
**53 Town** "Peasant Human2 MaleB B", skin PEASANTM7A, DAT class `TownHuman2MaleB` (4). Skins PEASANTM7C/D belong to the
other model `PeasantM7d.abc` (rows 25, 27) and are not this body. Built on the Annud/PeasantM1 route: Meshy body fitted to
the original MM9 PeasantM7/PeasantMale skeleton, MM9's own PeasantMale clips, MPFB five-finger hands, separate head set.
Progress, hashes and Meshy receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_peasantm7.glb` (installed with `tools/install_model.py --world mm9 --name mm9_peasantm7.glb` from `export/mm9_pm7.glb`; cooked copy in `assets_dev`, 4.7 MB) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_peasantm7_claude`: `MM9 51 Commoner` (skin `pm7_b`) and `MM9 53 Town` (skin `pm7_a`), scale 100, `yaw_offset -1.570796327`, stride walk 1.1 / run 2.8, look `Bip01 Neck, Bip01 Head`, impact 0.533 s (hattack2 Rattack) |
| Descriptors | rows 51 (legacy stand-in 368) and 53 (371) appended to `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv`, tables regenerated (`generate_mm9_monster_tables.py`: 9051 `MM9 51 Commoner`, 9053 `MM9 53 Town`) |
| Triangles LOD0/1/2/3 | 7,313 / 3,656 / 1,313 / 437 (from Smart Topology 15,100; head and neck 2,305, two MPFB hands 1,398) |
| Skeleton | PeasantM7 = PeasantMale, 45 joints, rest rotations unchanged, joints translated onto the HD body; + 15 finger bones per side driven from MM9's mitten curl (`finger_alias`); whole model mirrored to MM9's true handedness (`mirror_glb.py`) |
| Clips (30 fps, PeasantMale library `source/mm9_lib/pmale.glb`) | Standing stand1, Walking walk3, Running run, Fidget fidget4, Talk conv2, AttackMelee hattack2, Hit wince1, Death die1, Dead; script clips Cower cower, Conv1 conv1, Conv4 conv4, Conv5 conv5 (22.2 s) |
| Textures | body 2K colour + 1K normal + 1K ORM (R AO); head + hands set 2K colour + 1K normal/ORM; region masks 1K (body R tunic, G collar/placket/hem band, B breeches; head R hair); `openyamm_specular 0`, metallic 0 |
| Meshy credits | **25** (Smart Topology 5, body retexture 4K 10, head retexture 4K 10; backup account, 3700 -> 3570 shared balance over the session) |

## Wrist and hand fix (2026-11-01 evening, user review: "peasantm7 - hands sticking through the sleeves") - current

`review/user_notes/wrist_pokethrough.png`: skin wedges through both sleeves just above the cuffs, blotchy red/purple hands,
dark grey/black-tipped nails. Three causes, each fixed where it starts; mesh face counts, UVs, clips and binding unchanged.

- **Grafted stub through the cloth** (geometry): `graft_hands.py` conformed the MPFB forearm stub to the cuff OPENING; above the
  cuff the Meshy sleeve narrows and the stub poked out on the inner/back side (rest pose 9.4 mm left, 5.3 mm right).
  `scripts/sleeve_tuck.py` (Blender, `work/texpass_head.blend` -> `work/texpass_head_tuck.blend`, frac 0.75, gap 3 mm): every hand
  vertex is pulled inside the sleeve along the ray from the forearm axis to 75 % of the OUTERMOST sleeve wall (the old forearm
  skin Meshy left under the sleeve is hit first, 1-2 mm from the axis, and hid the outer wall in the first try), L 25 / R 25
  vertices moved up to 20 mm; stub vertices more than 1 cm up the sleeve take the nearest sleeve vertex's weights (2 cm blend),
  so the stub moves with the cloth over it. The build now uses `BLEND=work/texpass_head_tuck.blend`.
- **Skin paint on the sleeve** (body texture): the 4K retexture painted skin-coloured wedges onto the cloth above both cuffs.
  `scripts/sleeve_paint_fix.py export/mm9_pm7.glb`: body texels within 12 cm of a hand joint (bind pose) that are skin-coloured
  take the nearest cloth texel (5,420 texels; graded original kept as `work/pm7_tp_basecolor_graded_orig.png`). Run after the grade.
- **Blotchy hands, dark nails** (head set): `compose_headhand.py` graded the MakeHuman hand bake per channel to the spread of
  the face paint (stubble, brows, lips): 2-3x contrast per channel turned its veins red/purple and its pale nails blue-grey.
  `scripts/hand_clean.py` (after `fringe_fix.py`): the hand squares take one clean face-skin colour (201/133/95, the face's
  cheeks and forehead x 0.95) times the bake's luminance detail only (^0.6, +-15 %) and the baked AO; the bake's island rims
  (blended into its black background, dark seam lines in the first try) are padded from 2 px inside.
- **New gate** `scripts/sleeve_poke_gate.py <glb> <json>`: per hand/stub vertex, a ray from the posed forearm axis through it;
  where it meets that arm's sleeve the vertex must lie inside the outermost wall (every clip, 48 fps). Before: left 9.3-16 mm,
  right 5.1-10.8 mm in every clip (all frames). After: **0 mm, 0 frames, in all 13 clips, both sides**
  (`review/gates_v2/sleeve_poke.json`; tier-independent: the tiers only change colours).

Sheets read: `review/sheet_wrist_before_after_L.png`, `review/sheet_wrist_before_after_R.png` (Blender, same cameras, v1.11 vs
v2.2: Standing, Talk 100, Conv1 103, Death 60; front, back, both sides, below), `review/wrist_parts_{L,R}_after.png` (hand
material red: nothing red through the sleeves), `review/sheet_wrists_viewer_after.png` (viewer, both tiers, Standing four sides,
Talk, Conv1, Fidget, Walking, Cower, Death), `review/sheet_hands_closeup_viewer.png` (viewer close-up, both hands front and back).
Rollback of the v1.11 install: `work/rollback_v1/` (source GLB, export, head colour, ramps).

Gates after (v2.2, `review/gates_v2/`): arm and hand gate unchanged (Fidget R 1.9 cm; Conv1 L 5.9 cm, Conv5 L 5.6 cm; Conv1 L
forearm 1.6 -> 1.1 cm); jitter the same 2 known fails (Conv1 L 1.41 deg/f, Conv5 L 1.19); winding 0; detached 0; flat 0.00;
bones as before (MM9's hip slide); texture body unchanged (55.7 %), head set 41.2 %, spread 2.88, fragments 2.6 %; viewer check
26 switches, 0 failed; floor audit both bindings ok; regression `actors --world mm9` passed 192, failed 1 (the known out05), `mm9_actor_models_build_every_binding` PASS (170 descriptors on 70 models, 0 failed). Meshy: 0 credits.

## Clips the MM9 scripts play

DAT objects of the two classes (`scripts/dat_objects.py`): 15 without a script (row default NPCbase.scr -> npcBase.inc ->
BaseRun.inc `LoopAnim Cower`), NPC110.scr (conv2, conv5, conv4, `stand`; basemelee.inc), NPC213.scr and Ralof.scr (conv1,
conv2, `stand`), knutspeech.scr, NPC245.scr (none), NPC161/198/199/240.scr (animation from ScriptParams, empty on these
objects). `stand` is not in the library: bound to Standing (stand1), as Annud and PeasantF8. No map marker names an animation.

## Route (scripts/)

0. **HD masters** (`references_hd/`, Codex through `codex_slot.sh`, brief `CODEX_BRIEF.md`, two runs, records
   `generation_runs.json`): inputs renders of the MM9 model with skin B (`mm9_views_b.png`, `mm9_head_views_b.png`,
   `mm9_skin_x4_b.png`; `ref_renders.py`), bind pose, 1536x1024. Codex's soft halo removed by `clean_alpha.py` (raw returns in
   `references_hd/raw_codex/`). Head turnaround `references_head/` (four views, 1254x1254, `codex_head.sh`).
1. **Meshy** Smart Topology 15k from `00_three_quarter.png` (`requests/smart_topology_v1.json`).
2. **Fit + weights** `fit_rig.py` + `fit_config.json` (copied from mm9_peasantm1_claude). New option `centre_interp`: PeasantM7's
   MM9 mesh has only front vertices in the Spine3 band, which moved Spine3 14.8 cm backwards; it now takes the mean move of
   its centre-chain neighbours (0). X-ray `review/xray_v1.png`.
3. **Reduce** `reduce_uv.py` (`reduce_config.json`; its Smart UV upload is unused) -> `work/rig_v1.blend`; **hands**
   `graft_hands.py graft_pm7.json` -> `work/hands_v1.blend`; **head split** `head_split.py head_pm7.json` (neck cut 0.62,
   radius 0.105: the neck only, the collar stays in the body set) -> `work/head_v1.blend`, `review/head_split.png`.
4. **UVs** `texpass_uv.py` (uv_atlas; body atlas 55.7 %) -> `work/texpass_uv.blend`, upload `texturing/pm7_body_upload_tp.glb`;
   `texpass_head_uv.py` -> `work/texpass_head.blend`, `texturing/pm7_head_upload_tp.glb`. Never re-run: the paid textures
   belong to these layouts.
5. **Retextures** 4K: `requests/retexture_body_tp.json` (01/03/02/04), `requests/retexture_head_tp.json` (head views).
6. **Maps** `bake_ao_texpass.py` -> `textures/pm7_tp_ao_2k.png`; `compose_texpass.py pm7_tp meshy/body_retexture_tp
   texturing/pm7_body_upload_tp.glb textures/pm7_tp_ao_2k.png`; gentle grade (`grade_basecolor.py --fine 1.0 --local 0.3
   --ao-strength 0.5 --contrast 1.06 --saturation 1.15`); `bake_hands.py work/texpass_head.blend
   young_caucasian_male/young_lightskinned_male_diffuse.png`; `compose_headhand.py pm7_tp meshy/head_retexture_tp
   textures/pm7_tp_basecolor_graded.png textures/pm7_tp_material_classes.png textures/pm7_tp_metal_rough_1k.png --ref-head
   --hand-gain 1.12` (the hands read darker and redder than the face at 1.0); **`fringe_fix.py`** (below); since v2.2
   `sleeve_paint_fix.py export/mm9_pm7.glb` (after the grade) and `hand_clean.py` (after `fringe_fix.py`), and the master is
   `work/texpass_head_tuck.blend` (`sleeve_tuck.py work/texpass_head.blend work/texpass_head_tuck.blend 0.75 0.003`).
7. **Runtime** `scripts/build_runtime_v2.sh pm7 PeasantM7 scripts/roles_pm7.json` (env `PYGLTF_PYTHON`, `TOKEN`,
   `HEADTEX=pm7_tp BODYTEX=pm7_tp BLEND=work/texpass_head_tuck.blend`, `PYTHONPATH=/usr/lib/python3/dist-packages`): textured export
   (`export_fix` in `head_pm7.json` fills a 5-edge hole in the right elbow sleeve; `build_export_v2.py` gained a fallback cap
   for loops `holes_fill` leaves open) -> `clips_mm9.py` (soft offsets) -> `hand_rest.py` per `hand_rest_pm7.txt` -> prepare
   -> LODs -> shadow fix -> extras -> `region_variants.py` (tiers) -> `floor_fix.py` (`floor_ops.txt`) -> `mirror_glb.py` ->
   winding. Then `tier_pm7.py export/mm9_pm7.glb` (ramps from the new paint) and `retier.sh` (variants -> floor -> mirror ->
   winding from the same build), install, `viewer_tiers.py`, `make_viewer_pm7.py <rev>`.
8. **Binding** (repo root, under the flock): `flock level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock bash -c
   'python3 level_generation/creatures/mm9_peasantm7_claude/scripts/bind_actors.py && python3
   tools/mm9_import_discovery/generate_mm9_monster_tables.py'`, then `level_generation/projects/mm9r_common/review_root.py`.

## Tiers (`tier_pm7.py`)

Shared paint = skin B (row 51, 20 of 24 placed objects). Tier A (row 53) by ramps only. Region texels from hue/value classes
of the graded paint (cleaned by a close/open, limited by height on the bind pose); tier A target per texel = MM9 skin A's
colour at the texel's luminance quantile inside the region x our luminance / MM9 skin B's at that quantile, measured on the
same skin rectangles (both skins share one layout; per-tier hue filters keep each rectangle to its cloth). Fit on the class
texels only (gutters and the cream lacing had stretched the first fit to luminance 0.8 and read grey). Fit error (8-bit,
mean / p95): tunic A 0.15/0.32, B 1.23/3.72; collar A 0.94/2.39, B 2.27/8.07; breeches A 0.14/0.36, B 1.56/4.15; hair A
0.80/1.79, B 1.80/5.40. The hair mask fades out above the hair's own luminance (no pale rim on the forehead) and reaches the
nape behind the head. Sheets: `review/sheet_mm9_vs_ours.png`, `review/sheet_tiers.png`, `review/sheet_heads.png`.

## Fringe and hairline (`fringe_fix.py`, orchestrator lesson 2026-11-01)

Meshy painted a dark-grey receding hairline with hair wisps on the face shell's forehead under the hair shell's zigzag edge:
a grey jagged band on tier B and a pale ginger rim on tier A. `fringe_fix.py` (on the composed head colour, kept as
`work/pm7_tp_head_basecolor_composed.png`): skin-coloured texels on the hair shell's rim take the nearest hair colour (17,618
texels); on the face shell's front above the brows every non-skin texel (dilated 6 texels to swallow the wisps and Meshy's pale
rim; 38,400 texels) takes the surrounding forehead skin by normalised convolution plus that skin's grain, feathered over 6
texels. Before/after: `review/sheet_fringe_tiers.png` (`fringe_views.py`, both tiers, front/above/both three-quarters; the
earlier states are described in the status file). A dark 2-3 px notch remains at the right temple where the hair shell's edge
meets the face island border.

## Checks (v1.11-fringe-20261101; v2.2 numbers in the wrist section above)

| Gate | Result |
|---|---|
| Arm and hand gate (`arm_hand_gate.py`, every clip, 48 fps; `review/gates/arm_hand_gate.txt`) | hands 0 cm in body in every clip except **Fidget R 1.9 cm, 7 frames** (MM9's beard scratch: the fingers on the chin, as Annud's 2.5 cm), **Conv1 L 5.9 cm, 27 frames** and **Conv5 L 5.6 cm, 44 frames** (MM9's hand on the hip: the fingers go under the flared tunic skirt, cloth over the hand; the trunk cast of `hand_rest.py` reports it clear and `arm_clear.py` on top cleared 7 deg but doubled the jitter). Forearms 0 except Conv1 L 1.6 cm. Finger stretch p99 <= 1.57, max 3.14 (Fidget L). Wrist max 119 deg (Death/Dead: MM9's limp death hand). Five chains per hand (19 joints) |
| Jitter (`jitter_gate.py` vs MM9's clips; `review/gates/jitter_gate.txt`) | 2 fails: **Conv1 L upper arm 1.41 deg/f over MM9 (limit 1.0), shoulder skin 3.27 mm/f2 (limit 2.0)**; **Conv5 L 1.19 deg/f, 1.01 deg/f2, skin 2.44**. Seven `hand_rest.py` filter settings tried (`hand_rest_pm7.txt` comments); Annud's accepted Conv1 had 1.25 / 1.06. Walking and Death (shoulder skin 8-11 mm/f2 from the per-key floor pass) fixed by `--smooth-loop Walking 0.12 --smooth Death 0.1` |
| Floor (`floor_audit.py --world mm9 --match 'MM9 5[13] *'`) | both bindings ok: stand 0, walk -0.1..+2.4, living -0.1, dead -0.0 world units |
| Winding (`check_winding.py`) | 0 inverted closed parts |
| Bones (`bone_length_audit.py`) | Thigh translation 0.112-0.125 (11 %): MM9's own hip slide (the library pmale.glb 0.097-0.129, Annud 0.109-0.126) |
| Detached (`detached_parts_audit.py`) | 0 detached in any pose (21 components) |
| Flat shading | 0.00 on both materials |
| Texture quality (`texture_quality.py`) | body atlas **55.7 %**, density p10/p50/p90 1416/1473/1523 (spread 1.08), fragments 0.0 %, stretch p90 1.15; head set 41.2 % (head square about 58 %), spread 2.92 (hands half density by design, as Annud), fragments 2.7 %, stretch 1.30 |
| Viewer (`run_creature_review.py check`) | 26 tier/clip switches, 0 failed, 0 console errors |
| Regression `--world mm9 --headless-run-regression-suite actors` (final install) | passed 192, failed 1 (the known `out05_event_clearance_completes_from_monster_killed_hook` "could not load gameplay data"); `mm9_actor_models_build_every_binding` **PASS** (647 descriptors on 185 models and 168 on 69, 0 failed); log `review/gates/regression_actors.log` |

Viewer: `http://127.0.0.1:8912/level_generation/creatures/mm9_peasantm7_claude/review/viewer/index.html` (tiers pm7_b, pm7_a;
three.js has no region ramps, so `viewer_tiers.py` bakes each tier's ramps into its own viewer GLB).
Sheets read: `review/sheet_mm9_vs_ours.png`, `review/sheet_tiers.png`, `review/sheet_heads.png`,
`review/sheet_face_closeup.png`, `review/sheet_fringe_tiers.png`, `review/strips_a.png` + `review/strips_b.png` (every clip,
six times, tier B, quarter view), `review/head_v1.png` (bind and Talk close-ups: eyes, mouth, neck), `review/contact_probe.png`.

## Binding plan (map placement)

The rebuilt maps place these townsfolk with the legacy stand-in ids (368 for `CommonerHuman2MaleB`, 371 for
`TownHuman2MaleB`) through `transcode_mm9_dat_to_odm.py`, so the new descriptors do not show in game yet. Per the brief this
switch is the orchestrator's, once for every row after the batch: placements of those two DAT classes should use
9051 / 9053. No transcoder or map change here.

## Deviations and open points

- **Tier A is a recolour of the B man.** Skin A is a different man (smiling, green eyes, ginger stubble) with a gold brocade
  collar and a jewelled necklace; the shared face and the plain collar cloth carry A's colours only (collar gold, hair and
  brows auburn, stubble stays brown). A separate head paint for A would cost a second head retexture (10 credits) and a
  per-tier head image.
- **Conv1/Conv5 left hand on the hip** under the tunic skirt flare and the marginal jitter excess above.
- Hands' skin: one clean face-skin colour with the MakeHuman bake's luminance detail (`hand_clean.py`, v2.2).
- The sleeve of Meshy's mesh had a 5-edge hole at the right elbow (filled at export).
- Not looked at in game; motion judged on viewer strips, not watched at speed; LOD1-3 and shadow meshes not looked at.
- User artistic acceptance: not recorded.


**LOD0 reduced post-install on 2026-11-05 by `level_generation/creatures/mm9_peasantm7_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_peasantm7_reduce_claude/before/`.
