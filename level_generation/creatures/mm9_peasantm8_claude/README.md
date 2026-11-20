# MM9 PeasantM8, the balding shopkeeper (mm9_peasantm8) — 3D actor variant, 2026-11-02

MM9 `PEASANTM8.abc` + `PEASANTM8A.dtx`, the only `MONSTERS.txt` row naming it: **55 Shopkeeper** "Peasant Human2 MaleC B"
(NPCbase.scr, PeasantMale library). DAT class `ShopkeeperHuman2MaleB`, 30 placements (Arslegard, Drangheim, Frosgard,
Guberland, Lindisfarne, Sturmford, Thjorgard and Thronheim cities, one in Guberland). Skins `PEASANTM8B/C.dtx` exist but no
row uses them: not built. Batch: `devdocs/mm9_rework/overnight/VARIANTS_BRIEF.md` (shared-mesh variants; no new body). Owner
peasantm8-agent. Progress, master hashes and Meshy receipts: `creature_3d_progress.json`.

**Same mesh as ForadDarre.** `meshcmp.py peasantm8:foraddarre` (re-run): head p90 1.0 cm (max 1.5), torso 0.8 (max 3.4 at the
back of the belt), arms 1.4 (max 3.1, the hands: ours are grafted MPFB hands anyway), legs p90 2.5 (max 2.7). Per vertex
(`references_hd/` renders, scratch `disp.py`): the leg difference is the boot: MM9's sole sits 2.6 cm further back (heel
longer, toe shorter); the trouser legs themselves are within +0.5 cm radially (knees up to 2 cm on single vertices). Both MM9
meshes are 329/340-vertex single pieces with the same silhouette (`references_hd/mm9_pm8_vs_forad.png`, `_head.png`): no reshape
needed. So this model is **Forad's approved v3.4 body, MM9 skeleton, weights and clip choice** (`../mm9_forad_claude/`, never
written to) with its ponytail and necklace removed and its own paint: a different man (balding, short blond side/back hair,
clean-shaven, pale) in different clothes (brown wool tunic with laced V neck, cream linen sleeves, belt with pewter buckle,
ribbed brown trousers torn at the knees, cuffed boots).

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_peasantm8.glb` (`tools/install_model.py --world mm9 --name mm9_peasantm8.glb`), identical to `v2/export/mm9_pm8.glb` (sha256 d4cf7649...) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` `MM9 55 Shopkeeper` (block `scripts/binding.yml`, `scripts/bind_under_lock.sh` under the flock): Forad's values (scale 100, yaw -1.5708, stride 1.05 / 3.8, look Neck/Head, impact 0.5 s = hattack1 Rattack); script clips `talk`/`conv1` Talk, `conv2` Conv2, `conv3` Conv3, `stand` Standing, `cower` Cower |
| Descriptor | row 55 added to `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` (fallback 374, the stand-in `mm9_npc_legacy_replacements.tsv` gives row 55), tables regenerated (202 rows) |
| Triangles LOD0/1/2/3 | 7,168 / 3,582 / 1,288 / 427 (Forad 8,397: ponytail, 39 necklace beads and the two eyeball cups gone) |
| Clips (30 fps, PeasantMale `source/mm9_lib/pmale.glb`, soft offset line) | Standing stand1, Walking walk3, Running run, Fidget fidget1, Talk conv1 (Forad's hand rest), AttackMelee hattack1, Hit wince1, Death die1, Dead, Cower cower (NPCBase.inc -> BaseRun.inc), **Conv2 conv2, Conv3 conv3** (Narrator.scr, Guberland City: `Loopanim conv1/conv2/conv3/stand`). The other scripts on these objects (NPCbase, Shopkeeper/shopkeeper, BankOrb, NPC378 + basedoor.inc, NPC184, NPC133) play no animation |
| Textures | body 2K colour + 1K normal + 1K ORM on Forad's texture-pass UVs (repainted); head + hands set 2K colour + 1K normal/ORM on new head UVs (ponytail gone, nape smoothed) |
| Meshy credits | **20 / 20**: body retexture 4K 10, head retexture 4K 10 (backup account: 3015 before the first job, 3005 before the second, 2985 after) |
| Viewer | http://127.0.0.1:8912/level_generation/creatures/mm9_peasantm8_claude/review/viewer/ revision `v1-20261102` |

## Route (project folder unless noted; nothing written into mm9_forad_claude)
0. Sources `source/mm9/pm8.glb`, `source/mm9_forad/forad.glb`, `source/mm9_other_skins/{B,C}` (`convert_abc_model.py --scale
   0.0256`, gltf venv + system packages). MM9 renders `scripts/ref_sheets.sh <P> pm8 PEASANTM8A 0.80` -> `references_hd/mm9_*.png`.
1. **HD masters** (Codex via `codex_slot.sh`): `SHAPE=mm9_forad_claude scripts/codex_masters.sh <P> 1|2` (brief
   `references_hd/CODEX_BRIEF.md`: design from MM9, pose/silhouette from Forad's masters, no ponytail), head turnaround
   `scripts/codex_head.sh` (`references_head/CODEX_BRIEF.md`: one brow, no lid crescents, one lip pair, plain bald scalp, calm warm
   face). `scripts/clean_alpha.py` -> `*_clean.png` (the Meshy inputs). Gate read: `references_hd/selected_views_review.png`,
   `references_head/selected_views_review.png`.
2. **Geometry** `scripts/strip_parts.py master ../mm9_forad_claude/v2/work/sleeves_v2.blend work/master_v1.blend`: deletes the
   loose ponytail (3 parts, 339 vertices), 39 necklace beads and Meshy's 2 eyeball cups; no other vertex moves. Then
   `scripts/nape_smooth.py work/master_v1.blend work/master_v1n.blend work/nape_smooth.json -0.017 0.11 0.725 0.05 0.06 0.04 40`:
   Forad's ponytail root knot at the nape smoothed (51 vertices, max 1.8 cm). Body upload: `scripts/strip_upload.py` removes the
   same 1,644 faces from Forad's texture-pass upload (matched by face centre, 0.0 mm) -> `v2/texturing/pm8_body_upload.glb`.
3. **Head UVs** `v2/scripts/texpass_head_uv.py work/master_v1n.blend v2/work/head_uv.blend v2/texturing/pm8_head_upload.glb`
   (uv_atlas 62.7 %). **Never re-run**: the paid head paint belongs to it. Body keeps Forad's texture-pass UVs.
4. **Weights** (no geometry): `scripts/face_rigid_pm8.py` (Kira's rigid-face lesson: the chin's underside carried 20-45 % Neck;
   Head share raised in front of the jaw angle only, 27 vertices, chin min Head 1.0) -> `v2/work/face_rigid.blend`;
   `scripts/sleeve_tuck.py` (PeasantM7's, 0.82 / 2 mm) -> `v2/work/tuck.blend`; `scripts/cuff_follow.py` (new: the 3 cm of
   Forad's rigid bracer past the wrist joint gives up to 50 % of its Forearm weight to the Hand, so a hard wrist bend no longer
   drives the back of the hand through the ring) -> `v2/work/cuff.blend`.
5. **Paint**: `v2/requests/retexture_body.json`, `retexture_head.json` (4K, meshy-7, our UVs); AO `v2/scripts/bake_ao_texpass.py`
   on `v2/work/face_rigid.blend`; `compose_texpass.py pm8 meshy/body_retexture_pm8 v2/texturing/pm8_body_upload.glb
   textures/pm8_ao_2k.png`; `grade_basecolor.py --fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.15`;
   `compose_head_texpass.py forad_tp pm8 meshy/head_retexture_pm8` (Forad's hand texels kept); then, in this order (each keeps
   its own backup as input): `scripts/hand_tone.py pm8 1.0 work/texpos_head.npz -0.017` (hands to the new pale face; texel
   positions `scripts/dump_mesh.py` + `scripts/texel_pos.py`), `scripts/collar_match.py pm8 work/dump_master.npz
   work/texpos_head.npz` (new: the head set's tunic collar painted a lighter orange-brown than the body tunic, a jagged band at
   the seam; local colour gain toward the body paint within 3 cm), `scripts/lip_sym.py` and `scripts/philtrum_lift.py` (new: the
   upper lip read as a moustache shadow in profile under the close-up light; lifted toward the cheek tone, lips excluded).
6. **Lining texel** `scripts/lining_texel.py v2/work/cuff.blend v2/work/master_v2.blend textures/pm8_basecolor_graded.png`
   (PeasantM8d's: Forad's black bracer-lining texel -> the cream cuff's). **`v2/work/master_v2.blend` is the master.**
7. **Runtime**: `PYGLTF_PYTHON=../claude_shared/gltf_venv/bin/python TOKEN=<lease> HEADTEX=pm8 BODYTEX=pm8
   BLEND=v2/work/master_v2.blend v2/scripts/build_runtime_pm8.sh pm8 PeasantM8 v2/scripts/roles_pm8.json` = Forad's
   `build_runtime_v2.sh` plus `scripts/finger_pose.py` after the hand rest (Kira's relaxed-hand script, extended here for the
   two-segment PeasantMale mitten: PIP from Finger11's own +X axis, bend axis from the MPFB palm normal, since the nearly
   straight bind mitten leaves Kira's MCP-plane axis undefined). `v2/scripts/hand_rest_pm8.txt` = Forad's Talk line + Conv2
   (MM9's conv2 sank the left hand 6 cm into Forad's deeper trunk; Annud's Conv1 settings). `scripts/floor_ops.txt` adds
   Conv2/Conv3. Then `check_winding.py`, `install_model.py`, binding under the flock, viewer `v2/scripts/make_viewer_v2.py
   v1-20261102 pm8 ... v2/viewer_prov.json`.

## Checks (installed GLB = `v2/work/r4.glb`)

| Gate | Result |
|---|---|
| Arm and hand (`arm_hand_gate.py --outer-only --exact`, 48 fps, `v2/review/gates/arm.txt`) | hands 0 in every clip except **Talk L 3.3 cm, 40 frames** (MM9's hand on the heart: Forad's accepted Talk is 3.5 cm / 40 frames); Conv2 0 (6.0 cm before its hand rest); Fidget R forearm 1.2 cm (Forad's); finger stretch max 3.2 (Death/Dead R, finger_pose's curl; Forad 2.91); 19 chains per hand |
| Jitter (`jitter_gate.py` vs MM9's untouched clips, `v2/review/gates/jitter.txt`) | 5 fails, the same clips and numbers as Forad's accepted ones (Walking and Death shoulder-skin p95, Talk L upper arm 9.07 deg/f); Conv2 (upper arm 0.89 deg/f over MM9) and Conv3 pass |
| Sleeve poke (`sleeve_poke_gate.py`, every clip, `v2/review/gates/sleeve_poke.txt`) | rest 0. Where MM9 bends the wrist hard the hand still meets the cuff: Talk L 16.4 mm, Hit R 24.3, Death L 10.8, Conv2 L 8.0, Running L 7.8, Fidget L 3.3, Death/Dead R 2.7/3.0 (Forad's installed GLB: Death/Dead R 24.1/24.2, Fidget L 6.7; cuff_follow.py took those down). **Not 0**: Forad's bracer reaches 3.2 cm past the wrist joint, so a 90-127 deg wrist bend crosses it; close-ups `review/r4/hands.png` (bind, Standing, Talk 48, Death 70, Hit 15): the hand leaves the cuff, cream cloth, no skin showing through the sleeve |
| See-through (`scripts/see_through_gate.py` step 3, 8 azimuths x 0/20 deg, every clip, `v2/review/gates/see_through_r4/`) | head 0, torso 0, boots 0, trousers 0, collar 0. Sleeves: thin slivers at Forad's bracer/cuff rim when the wrist turns: R worst 22 px Conv2 frame 12 (5 frames), Conv3 17 px (9 frames), Running 12 px (1), AttackMelee 9 px (3); L 4 px Talk (2). Images read (`report_sleeve*.png`): a one-pixel line along the cuff edge. The same without cuff_follow.py (`see_through_nocuff/`), so it is Forad's rim, not the soft cuff; PeasantM8d reported R 10 px on clips without Conv2/Conv3. Kira's `wrist_fill.py` rim cap was tried and does not run on Forad's lined rims (its ring walk breaks where the lining strip joins the rim); not fixed |
| Full actors suite (`--world mm9 --headless-run-regression-suite actors`) | passed 192, failed 1, the known `out05_event_clearance_completes_from_monster_killed_hook` ("could not load gameplay data"; `review/regression_actors.log`) |
| Rigid head | chin/jaw underside Head 1.0 (`v2/work/face_rigid.json`) |
| Floor (`floor_audit.py --world mm9 --match 'MM9 55 *'`) | ok: stand 0, walk -0.0..+0.0, living 0, dead 0 (Forad's row the same) |
| Detached (`detached_parts_audit.py`) | 0 detached (3 components) |
| Winding | 0 inverted closed parts |
| `texture_quality.py` | body atlas 53.3 % (Forad 53.5 %, same layout less the beads; under the 55 % target as Forad's was accepted), density p10/p50/p90 1502/1553/1598, spread 1.06, fragments 0.0 %, stretch p90 1.09; head set atlas 44.0 % (Forad 43.9 %), fragments 2.7 %, stretch p90 1.24 |
| Viewer `run_creature_review.py check` | 12 switches, 0 failed, 0 console errors |
| Regression `mm9_actor_models_build_every_binding` (`--world mm9`) | PASS, 202 descriptors on 89 models (`review/regression_binding.log`) |

Sheets (read): `review/sheet_mm9_vs_ours_r1.png` (MM9 PeasantM8a vs ours, five views), `references_hd/mm9_head_views.png` (MM9's
face) against `review/r4/head.png` (bind and Talk 60: front, profiles, 3/4, eyes, mouth, both neck sides; r1 had the collar band,
r2/r3 the upper-lip shade), `review/r4/ears.png` (both ears, tight, 3/4 backs, from below, jaw-neck lines, party view),
`review/r4/hands.png`, `review/sheet_viewer_shots.png` (viewer: Standing, face, Talk, Conv2, Conv3, Cower, Walking, AttackMelee).

## Approved model untouched
`mm9_forad_claude/` was only read. sha256 of all 972 files of the project plus `assets_source` and `assets_dev`
`mm9_forad.glb`, before and after: `review/forad_sha256_before.txt` = `review/forad_sha256_after.txt` (identical). The
`MM9 252 Forad Darre` binding was not edited. `mm9_peasantm8d_claude/` (another agent's) was only read (scripts copied).

## Open points / not checked
- Forad's open-vest geometry (standing lapels) is painted as a closed tunic with a laced slit, as PeasantM8d; the cap sleeves
  are paint on the vest shoulders; the cuff rim keeps Forad's small jagged bracer teeth (now cream).
- The hand texture keeps Forad's faint zig-zag graft seam on the back of each hand.
- The viewer's level face shot reads the eyes as looking up (stand1 bows the head), as PeasantM8d's on the same head.
- Skins PEASANTM8B/C (no MONSTERS.txt row) not built.
- No in-game run; LOD1-3 and shadow meshes not looked at; normal-speed playback of Conv2/Conv3 not watched (stills and gates only).
- Map placement (row 55 still placed as legacy 374) is the orchestrator's (see `../mm9_peasantm1d_claude/README.md`, "Binding plan").

User artistic acceptance: not recorded.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_peasantm8_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_peasantm8_reduce_claude/before/`.
