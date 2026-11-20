# MM9 Kira the Cold (mm9_kira) — 3D actor, 2026-11-02

MM9's Jarl of Thronheim: `MONSTERS.txt` row 251 "Kira the Cold" L110 (`KIRA.abc`, skin `KIRAPLATE`, `NPCbase.scr`, Scale 1, IsMonster 0,
Hostility 1, melee 20D8). One skin, no tiers. Built on the approved MM9 humanoid route (MM9 skeleton and MM9 clips, never Mixamo; grafted
five-finger hands; a separate head set). Progress, hashes and Meshy receipts: `creature_3d_progress.json`. Status:
`devdocs/mm9_rework/overnight/status/townsfolk_kira.md`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_kira.glb` (`tools/install_model.py --world mm9`), identical to `export/mm9_kira.glb` (r8 sha256 0afc4ec2a1e9...; r7 22841603a44f... kept as `work/mm9_kira_r7_rollback.glb`) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_kira_claude` (`scripts/bind_actors.py` under the flock): `MM9 251 Kira the Cold`, scale 100, `yaw_offset` -1.570796327, stride walk 1.05 / run 3.0 (`stride.py`: walk 1.04-1.07 m; run planted only 10 % of MM9's cycle, 2.9-3.2 m), look `Bip01 Neck, Bip01 Head`, melee impact 0.373 s (wattack1 `Rattack`), the ranged slot plays AttackMelee (melee row; the engine requires the key) |
| Descriptor | row 251 appended to `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` (fallback visual 255 = Fighter Chain C, the stand-in `mm9_npc_legacy_replacements.tsv` already uses), tables regenerated: id 9251 `MM9 251 Kira the Cold` |
| Triangles LOD0/1/2/3 | 16,160 / 8,078 / 2,906 / 969 (r8; r7 12,659). LOD0: body set 11,210 (armour shell, legs and boots, mail skirt, pauldrons, belt, medallion, knee cops, tasset, MPFB hands 4,954 of which fingers 4,480 after one smooth cut, two vambrace rim caps 72), head set 4,950 (face and neck skin about 2,485, hair 1,428, braid 704, eyeballs 320) |
| Skeleton | KIRA.abc's 50 nodes (Bip01 biped with Pelvis, two finger chains per hand, MM9's back-hair chain `Yhairbase..YhC`, braid chain `Yponybase..YpC`, fringe `Ybang*`), joints moved onto our mesh with the rest frames turned by the least rotation (`fit_kira.py`), + 30 finger bones (MPFB), + 12 half-joint helpers `*_h`, + 6 skirt hinges `Bone06/14/18/02/10/22` under Bip01 Spine (KIRA.abc has no skirt bones) |
| Clips (30 fps) | Standing `stand`, Walking `walk`, Running `run`, Fidget `fidget1`, AttackMelee `wattack1`, Hit `wince1`, Death (authored, below), Dead. Script clips: Sit `sit`, Applause, Sc2_KIRA5, Sc2_Kira7, Sc2_Kira9b, Sc2_KIRA12, Sc2_KIRA14, Sc2_KIRA16b, Sc2_Kira17, Sc2_KIRA20_23 (`Sc2_KIRA20-23`), Sc2_KIRA22, Sc2_Kira19, StaticDie `static_die1` |
| Textures | body colour 2K + normal 1K + ORM 1K (metal from the class map), head colour 2K + normal 1K + ORM 1K; class maps `textures/kira_{body,head}_material_classes.png` (project only) |
| Meshy credits | **25 / 60**: Smart Topology 5, body retexture 4K 10, head retexture 4K 10 (backup account; balance 3550 before the first job, 3440 after the second; floor 2740), no retries |
| Viewer | http://127.0.0.1:8912/level_generation/creatures/mm9_kira_claude/review/viewer/ revision `r8-20261102` (r7 kept in the viewer as `kira_r7` for comparison) |

## Placements and the clips MM9 plays on her

DAT objects (`scripts` none; found with a search over `assets_dev/worlds/mm9/maps/*.raw_objects.yml`):
- Thronheim City `KiratheCold` "KiraCold" (`NPC239.scr`, her hall: quests, voice; its `loopanim Sit` is commented out) and `KiratheCold` "Kira"
  (`ARG_Kira.scr`, the Argument cutscene); Afterworld `KiratheCold0` (hidden until the Six Fires, `SIXFIRES.inc` toggles it; row default
  `NPCbase.scr`). The other "Filename Kira.abc" objects in the Argument scene (Bjarni, Sigmund, Forad, Tryggva, Markel) are other rows.
- Corpse props `Kira` (Prop, `PropAnim.scr Static_die1`, `Kira.abc` + `KiraPlate.dtx`) in Afterworld and Yorwick: StaticDie is carried for them;
  how Props with an actor model are rendered is not part of this job.
- `NPCbase.scr` plays `Converse` (conv*) and BaseRun's `LoopAnim Cower`: KIRA.abc has neither, so MM9 falls back to its roles.
- `ARG_Kira.scr`: `loopanim Sit`, `playAnim Applause`, `Sc2_KIRA5/7/9b/12/14/16b/17/19`, `Sc2_Kira20-23`, `Sc2_Kira22`, `walkto` (walk);
  `Agree` is played but does not exist in KIRA.abc. `AttachProp kirasword` (Sheath, then RHand1) is the cutscene's sword (not built).
- Left out (not played by any of her scripts): `kirasetup02`, `taunt`, `fidget2`, `walk1`, `stand1`, `wattack2/3`, `block`, `dodgeleft/right/back`,
  `Backpedal`, `Backpedal_run`, `wince2` (only its recoil feeds Death), `Sc2_KIRA24`, `Sc2_KIRA23`, `Sc2_KIRAshot16a`.
- **Death:** KIRA.abc has no death clip (MM9 never kills her in a script); the engine requires `dying`. Death = wince2's first 0.45 s blended
  over 0.85 s into `static_die1` (the corpse pose the PropAnim props use), held 0.9 s; Dead = its last pose. `clips_mm9.py` gained per-clip
  `trims`, a per-role `blend` and `hold` for this.

## No shield, no sword (deviation from the job text)

The job asked for KIRASHIELD as a held attachment. MM9 never attaches it to her: no script or DAT object does; `KIRASHIELD.scr` is the
quest item lying in Thronheim City (item 375 "Kira's Shield ... Wasn't the town clerk of Sturmford asking for this?", already the
decoration `mm9_kirashield`). Her MM9 renders show no shield. Carrying it would contradict the quest, so she has none; the
shield-through-body gate does not apply. The sword (`KIRASWORD`) is attached only inside the Argument cutscene; not built (cutscene work).

## Route (`scripts/`)

0. **Sources**: `convert_abc_model.py --scale 0.0256` (KIRA, KIRASHIELD, KIRASWORD; gltf_venv site-packages), `mirror_glb.py` ->
   `source/true/` (raw ABC `R Hand` sits on the figure's left). `ref_renders.py`, `src_strips.py` (`review/mm9_refs/`, `review/mm9_strips_a|b.png`).
1. **Masters** (Codex through `codex_slot.sh`): `references_hd/` (`codex_masters.sh` 1, 2; brief `CODEX_BRIEF.md`), `references_head/`
   (`codex_heads.sh`: front, three-quarter, both profiles, back and a close face). `clean_alpha.py` -> `*_clean.png`.
2. **Meshy** Smart Topology 15k from `00_three_quarter_clean.png`.
3. **`clean_kira.py`**: labels on the whole return (armour shell, legs, face, hair, eyes, medallion, belt, knee cops, pauldron lames, tasset,
   gloves by position), Meshy's braid stub dropped, scaled to MM9's height on MM9's floor, face/hair/eyes moved together onto the midline by
   the face's front, the figure's RIGHT half kept (Meshy's face had a lip blob on the left mouth corner) and mirrored, mail skirt split below the belt.
4. **Rig** (`step_rig.sh`): `fit_kira.py` (`fit_kira.json`: centre chain and hair chain translated, limbs least-turned; joints the config does
   not place follow their parent) -> `build_braid.py` (an 8-sided plaited tube from behind the right ear over the front of the shoulder, Yp
   joints moved onto it) -> `rig_kira.py` (structural weights; hair cap on the Head, hanging hair on Yhair..YhC, braid on Yp*, six skirt
   hinges, rigid copies for belt and medallion, per-vertex copies for lames, knee cops and tasset) -> `graft_hands.py` (`graft_kira.json`,
   MPFB female hands, 15 finger bones per side) -> `helpers_kira.py`.
5. **UVs** `uv_kira.py` (**never re-run**: the paid paints belong to `work/uv_v1.blend`): body square 2K (gloves 1.5x), head square (face 1.6x).
   Uploads `texturing/kira_body_upload.glb`, `kira_head_upload.glb` (`head_upload_kira.py`).
6. **Paint**: body retexture 4K (body masters), head retexture 4K (head masters). `dump_uv.py`, `compose_kira.py` (4K -> 2K once, gutters
   padded), AO `texpass_bake_ao.py` (6 cm body, 3 cm head), `part_map.py`, `face_fix.py`, `finish_kira.py` (gentle grade, hair x1.25,
   normal green flipped: Meshy writes Y-down, measured against the paint's relief; face skin normal flat; class maps; ORM).
7. **After the paint, UVs unchanged**: `cuff_weights.py` (vambrace ends past the wrist follow the hand) -> `sleeve_tuck.py 0.6 0.005`
   (from mm9_peasantm7_claude: the grafted stub tucked inside the vambrace, its weights from the vambrace) -> `face_tweak.py` (chin cleft and
   slivers smoothed) = `work/uv_v3.blend`.
7b. **r8 fixes** (`scripts/step_r8.sh`, user review 2026-11-02, below): `face_rigid.py` -> `chin_fold.py` -> `wrist_fill.py` ->
   `subdiv_fingers.py` -> `uv_slivers.py` = `work/uv_v6.blend`; `chin_paint.py` (head paint despeck, reads
   `textures/kira_head_final_r7.png`, writes `kira_head_final.png`). `dump_hand_pos.py work/uv_v6.blend work/hand_pos.npy 0.9027` for the
   sleeve gate. Review helpers: `wrist_close.py` (wrist close-ups in the forearm's frame), `rim_view.py` (rest-pose rim, glove hidden or
   shown), `ba_sheet.py` (labelled grids), `dump_face_w.py`, `probe_blend.py`, `probe_chin.py` (analysis dumps); `shots.sh` now takes
   the viewer model from `M` (default `kira`; it still pointed at `nj_a`).
8. **Runtime** `IN=uv_v6.blend scripts/rebuild.sh [--install]`: `export_kira.py` -> `clips_mm9.py` (`roles_kira.json`, soft offset line) ->
   `arm_const.py` (`arm_const.txt`: L 5 / R 2 deg on the roles that ease to Standing; MM9's hands rest on her hips and our armour is fuller)
   -> `arm_out.py` (`armout_jobs.txt`: Fidget R, Sc2_KIRA5 L forward, Sc2_Kira17 R, Sc2_Kira9b R 4 deg) -> `finger_pose.py` (r8) -> `half_keys.py` -> `skirt_keys.py` (seated clips keep
   their swing at the ends) -> prepare -> LODs -> shadow fix -> `material_classes_to_orm.py` (metal = metallic 1) -> `floor_fix.py`
   (`floor_ops.txt`, ground death) -> winding -> install. Viewer: `make_viewer_manifest.py <rev> kira=Kira the Cold=export/mm9_kira.glb`.
   Gates: `GD=gates_r8 scripts/gates.sh` (r7: `gates_final`).

## r8 fixes (user review 2026-11-02)

Notes: "her left cheek/chin wrong, gets distorted (fidget1 frame 55); her hands posture not sure if correct; the graft has a hole (right
hand)"; with the screenshots `review/user_notes/` (and a dark smudge under the lower lip in two of them). Rollback copy of the r7 runtime
GLB: `work/mm9_kira_r7_rollback.glb` (sha256 22841603a44f...).

- **Jaw shear** (cause): KIRA.abc has no jaw bone and its Head pivot sits at mouth height; `rig_kira.py` split the face skin by a
  chin-nape plane through the chin's front with a +/-3 cm blend, and `helpers_kira.py` relaxed the neck band 10 passes up to z 0.72, so
  the lips, chin and jaw carried 30-100 % `Bip01 Neck` / `Bip01 Head_h`. Every head turn against the neck sheared the lower face: the chin
  up to 50 mm off the head-rigid position in Fidget, 77 mm in Death, 83 mm in Sc2_KIRA20_23. Fix `face_rigid.py`: a boundary that
  follows the jaw (under the chin at the throat corner, rising to the nape and towards the jaw angles; blend 1.8 cm in front, doubled
  and raised behind the jaw angle so the skin under the ears keeps a soft neck share), shared Neck / Head_h / Head as the helpers do.
  Result: the lower face (1,353 vertices in front of the face above the chin) moves **0.00 mm** off the Head in every clip (r7: 4-83 mm).
- **Chin smudge** (cause): three midline sliver triangles under the lower lip (and one on the nose bridge, two at the collar's front) had
  every PartUV corner on the atlas corner, which holds dark hair in the head atlas: the dark stroke r7 took for the lip's shadow
  (`uv_slivers.py` gives them their neighbours' UVs). The chin's lower rim had two doubled fans per side with faces turned into the
  head (specks under any light) and the lower lip's centre an unwelded midline twin pair (a slit): `chin_fold.py` welds the twins
  (0.1 mm), deletes the inverted faces under the triangle that covers them and moves their apex onto its plane, smooths the cleft under
  the lower lip (vertex moves; no UV of any remaining face changes). Meshy's head paint also carries grey, unsaturated triangles just
  under the lower lip on both sides of the chin, mostly in the islands' gutters (bleeding in at the edges): `chin_paint.py` replaces
  texels of the chin and mouth islands and their gutters that are darker and greyer than the local skin with the local skin colour
  (lips, ears and hair untouched; MM9's face and the head masters are clean there). A small V notch at the lower lip's centre remains
  (Meshy's mirrored lip geometry), now without the dark stroke.
- **Hand posture** (cause): `clips_mm9.py`'s `finger_alias` copied Finger1's whole rotation (twist and abduction too) onto every MCP and
  Finger11/12's rotation from MM9's bind onto the distal joints in mismatched frames; MM9's bind mitten is already curled (MCP 28.6,
  PIP 14.5 deg) and the MPFB bind splayed (left index/ring/pinky 19/14/24 deg off the middle finger): stiff splayed claws with hooked
  tips, flat knuckles. Fix `finger_pose.py` (after `arm_out.py`): per key MM9's mitten flexion (MCP, PIP, DIP, thumb IP) drives a
  flexion-only pose of each finger about its own lateral axis, relative to MM9's bind; a relaxed curl mostly at the knuckle (MCP +18,
  PIP +6 deg, ring/pinky cascade) that fades out where MM9 opens the hand (Sc2_KIRA5); spread set to index +3 / ring -3 / pinky -6 deg
  from the middle finger; thumb IP 20 deg and 8 deg towards the index. Standing: left hand hangs relaxed with the fingers together,
  right hand curled on the hip; Fidget both on the hips; AttackMelee fists (MM9's own fists). Sc2_Kira9b's right hand then dug 1.9 cm
  into the seated thigh for 2 frames: `armout_jobs.txt` gained `Sc2_Kira9b:R:3.4:4.4:4`.
- **Wrist hole** (cause): the vambrace ends in two open loops (Meshy's outer wall, 18 vertices, slanted 0.2-3.3 cm past the wrist joint,
  r 1.6-2.4 cm, and its inner layer), and `sleeve_tuck.py 0.6` pulled the glove stub to 60 % of the sleeve radius up to 3 cm past the
  joint: at the rim the glove was a 0.7-1.2 cm stalk in a 1.6-2.4 cm tube, so a bent wrist showed the hollow end. Fix `wrist_fill.py`:
  the glove inside the rim flares to 0.85 x the vambrace's inner wall (0.9 left one vertex 1.3 mm through the vambrace in AttackMelee) (then steps back where a face would pass through the outer wall:
  0 added, 6 per side were through it before and still are, at the slanted rim) and takes the vambrace's weights (glove top, rim and cap
  move together in every clip); one ring of cap faces from the outer rim inward to 0.72 x its radius (deeper, down to 0.3 x, where the glove stays narrower, so the cap edge is inside the glove in all 36 columns), recessed 2 mm, on the rim's own
  texel (a rolled metal edge). Glove radius at the rim now 1.3-2.1 cm in 32 of 36 columns against the rim's 1.6-2.4 (r7: 0.7-1.2; two columns of the right glove stay at 0.7 cm), the rest closed by the cap.
- **Faceted fingers** (cause): `graft_hands.py` decimated each MPFB hand to 760 triangles: 6-sided fingers, dihedrals p50 20 / p90 45 deg
  under smooth normals (the normals were already smooth: no split normals, flat check 0.00). Fix `subdiv_fingers.py`: one smooth cut
  of the finger faces (UVs interpolated inside each face, the paint follows): dihedrals p50 11 / p90 26 deg, +3,436 triangles. The
  **streaked finger texture** is the paint itself: the fingers are thin strip islands in the body atlas with Meshy's leather pattern
  stretched along them; fixing it needs a finger re-paint (the UVs belong to the paid paint), not done.

## Checks (installed build, `review/gates_r8/`; r7 in `review/gates_final/`)

| Gate | Result |
|---|---|
| `arm_hand_gate.py --outer-only --exact` (48 fps, 21 clips) | **0 frames over 1 cm in every clip, both hands**; worst depth 0.9 cm (Sc2_Kira19 R), forearms 0.0, finger stretch max 2.11. r8: the new finger pose put Sc2_Kira9b R 1.9 cm (2 frames) into the seated thigh: `Sc2_Kira9b:R:3.4:4.4:4` in `armout_jobs.txt`. r7 history: Standing L 2.4 cm, Fidget L/R 2.4/2.6, Sc2_KIRA5 L 5.0, Sc2_Kira17 R 4.7 on the first rig, fixed by `arm_const.txt` and `armout_jobs.txt` |
| `jitter_gate.py` against the uncorrected clips | **0 fails** |
| Lower face on the Head (r8 measure: 1,353 face vertices in front above the chin, posed vs head-rigid, 30 fps, every clip) | **0.00 mm in every clip** (r7: Standing 4.5, Fidget 50, AttackMelee 44, Death 77, Sc2_Kira7 61, Sc2_Kira17 71, Sc2_KIRA20_23 83 mm) |
| `sleeve_poke_gate.py --hand-pos` (glove inside the vambrace, `--past 0`; `hand_pos.npy` regenerated from uv_v6, lift 0.9027) | **0 frames over tolerance in every clip**; worst 0.2 mm (AttackMelee R, Sc2_Kira7 L). The default (3 cm past the wrist) reads up to 52 mm in 40 clip-sides as in r7 (50 mm, 40): the cuff bends with the hand there and the perpendicular ray hits the straight vambrace |
| `skirt_gate.py` (legs through the mail skirt) | unchanged: 0 in every role clip; seated cutscene clips Sc2_Kira9b 37/322 frames at 0.4 cm, Sc2_KIRA12 10/165 at 0.3, Sc2_KIRA14 6/170 at 0.2, Sc2_KIRA20_23 8/73 at 1.2 cm |
| Shield through the body | not applicable: no shield (see above) |
| `collapse_gate.py` (face-frames) | Standing 287, Walking 217, Running 821, Fidget 1,235, AttackMelee 882, Hit 1,151, Death 1,441, Dead 1,674; Sc2_Kira7 15,585, Sc2_Kira9b 10,415. Higher than r7 (177 / 206 / 212 / 951 / 380 / 329 / 637 / 1,333) because the fingers have four times the triangles and curl more: the new face-frames are finger and palm faces 5-15 cm past the wrist, inside the curled fingers and fists (at most 16 small exposed faces at a worst frame; `review/handfix/` renders). Neck and head fell: Sc2_Kira7 neck 73 -> 11 and head 61 -> 7 at the worst frame, Sc2_Kira19 head 275 -> 36 and Sc2_Kira9b head 275 -> 3 face-frames; Sc2_KIRA22 neck rose 34 -> 538 face-frames (9 at the worst frame, 3 exposed) |
| `detached_parts_audit.py` (24 fps, all clips) | unchanged: 2 flagged, the tasset 4.0 cm off the skirt in Sc2_KIRA12 and the armour shell 1.8 cm off the legs in Running (by design) |
| `bone_length_audit.py` | 0 stretching of 12 |
| `flat_shading_check.py` | 0.00 body, 0.00 head (rerun after the last cap change) |
| `check_winding.py` | 0 inverted closed parts (rerun after the last cap change; the other rows ran on the build before it, which differed only in the cap's inner ring) |
| `floor_audit.py --world mm9 --match 'MM9 251*'` | ok: stand -0.0..+0.0, walk -0.9..+0.9, living -1.8, dead 0.0 |
| `texture_quality.py` | body atlas 59.6 %, spread 1.13, fragments 0.1 %, stretch p90 1.12; head atlas 56.2 %, spread 1.14, fragments 0.0 %, stretch p90 1.08 |
| Regression `--world mm9 --headless-run-regression-suite actors` (r8 installed) | `mm9_actor_models_build_every_binding` **PASS** (187 descriptors on 80 models, 0 failed); suite 192 passed, 1 failed: `out05_event_clearance_completes_from_monster_killed_hook` "could not load gameplay data" (known, not this body) |
| Viewer `run_creature_review.py check` (r8, models `kira` and `kira_r7`) | 42 switches, 0 failed, 0 console errors |

## Sheets (read by me)

- `review/sheet_mm9_vs_ours.png`: MM9 (stand pose) vs ours (Standing), four views and two head views.
- `review/strips_a.png`, `review/strips_b.png` (every clip, six frames) against `review/mm9_strips_a.png`, `review/mm9_strips_b.png`.
- `review/sheet_head.png` (viewer, front, quarter, both profiles, back), `review/face_zoom_r6.png` (face close-up), `review/clay_face.png`.
- `review/sheet_close.png` (hands on hips, attack hand, boots in the walk, skirt in the run, seated cutscene, corpse, body, head),
  `review/wrist_chk2.png` (wrists in AttackMelee, Hit, Sc2_Kira17), `review/sheet_body_r1.png`.
- r8: `review/sheet_jaw_before_after.png` (Fidget frames 27, 40, 48, 55, 62, 70 and the worst face frame of AttackMelee, Hit, Death,
  Sc2_KIRA5, Sc2_Kira7, Sc2_KIRA12, Sc2_Kira17, Sc2_KIRA20_23, Sc2_Kira19, Sc2_KIRA22; three-quarter from both sides, r7 | r8),
  `review/sheet_hands_before_after.png` (MM9 | r7 | r8, both hands, Standing, Fidget, AttackMelee, Sc2_KIRA5, Sc2_Kira17, front and side),
  `review/sheet_wrist_before_after.png` (both wrists: rest and the worst wrist flexes, Sc2_KIRA20_23 R 68 deg, AttackMelee R 64,
  Sc2_Kira7 L 60, Hit L 49, from above, behind, below, outside, front; then rest-pose rim views with the glove hidden and shown),
  `review/handfix/` (working shots: viewer mouth close-ups `v8_mouth.png`, `chin_zoom_ba.png`, `face_ba.png`, paint before/after
  `chin_paint_all.png`, rim close-ups `rz2.png`, `rim_sheet.png`).
- `review/references_hd/selected_views_review.png` and `references_head/selected_views_review.png` are Codex's own sheets.

## Deviations and open points

- **Face**: Meshy's head paint (eyes open, blue, irises visible, one brow line, lips closed). The fringe is Meshy's: a smooth cap with a
  shallow V at the centre (MM9's is parted near the centre and side-swept); its edge meets the skin cleanly (no pale band). Our face is
  narrower than the Codex face (eyes 4.7 cm apart). r7's "thin shadow line under the lower lip" was UVs on the atlas corner (r8 fix
  above); a small V notch at the lower lip's centre remains. A projection of the Codex close face (`project_face.py`, kept) read paler and
  blurrier than Meshy's own paint and was not used.
- **Braid** is built, not Meshy's (Meshy fused it); its paint is Meshy's head paint: a dark tube with little plait contrast.
- **Hair** stays on MM9's back-hair chain (Yh*), so it swings as MM9's does; the cap round the skull is rigid on the Head.
- **Sleeve gate**: inside the rigid vambrace the stub stays covered; the gate's default 3 cm past the wrist joint reads 2-5 cm in bending
  clips because the cuff bends with the hand there and the perpendicular-ray test hits the straight vambrace (looked at: no poke visible).
- **Tasset** (front plate panel) lifts up to 4 cm off the skirt in Sc2_KIRA12 when the front hinge swings for the seated thighs.
- **Map placement not switched** (orchestrator's step, TOWNSFOLK_BRIEF lesson 1): the rebuilt maps still place the legacy stand-in 255;
  descriptor 9251 is ready for the batch switch.
- **Cutscene** clips are bound as `script_clips`; whether OpenYAMM plays the Argument scene is script work, not checked here.

## What was not checked

- In game (no game run made); the corpse props (`PropAnim Static_die1`) and the Argument cutscene in the engine.
- Motion at normal speed by eye (judged from strips, close-ups and numbers; no playback capture).
- LOD1-3 and shadow meshes by eye.
- r8: the finger texture streaks (paint, not fixed); the corpse pose and Death hands by eye; the rim from every angle in every frame
  (looked at: rest and the four worst wrist flexes); the subdivided fingers' collapse counts are higher (curled fingers, faces inside
  the fists; at most 16 small exposed faces at a worst frame).

User artistic acceptance: not recorded


**LOD0 reduced post-install on 2026-11-05 by `level_generation/creatures/mm9_kira_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_kira_reduce_claude/before/`.

The installed model carries MM9's attach points as `Socket_<name>` nodes for held items (scene `held_items`, MM9's
AttachProp; 2026-11-11: `Socket_Sheath` and `Socket_RHand1` for her sword in the Argument cutscene), added after this
project's install by [`mm9_held_items_claude/scripts/add_sockets.py mm9_kira`](../../props/mm9_held_items_claude/scripts/add_sockets.py).
A rebuild installed from here (or its reduction) drops them: run that script again and install its export
(`tools/install_model.py --world mm9`).

Her seated Argument clips (Sit, Applause, Sc2_KIRA5 ... Sc2_KIRA14, and Sc2_KIRA16b as she stands) are lowered onto her
chair after install (2026-11-11) by [`mm9_kira_claude/scripts/seat_clips.py`](../mm9_kira_claude/scripts/seat_clips.py):
KIRA.abc keeps her standing hips while seated, so she hovered in front of her chair in the council cinematic. A
rebuild or reduction installed from here drops it: run `add_sockets.py mm9_kira`, install, then `seat_clips.py` and
install its export (`--name mm9_kira.glb`).
