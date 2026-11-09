# MM9 elf townsman PeasantM1d (mm9_pm1d) — 3D actor, 2026-11-01

MM9 `PEASANTM1D.abc` (45 joints, the PeasantM6/PeasantMale skeleton, identical joint list to `mm9_annud_claude`), the only
`MONSTERS.txt` rows naming it: **22 Commoner** "Peasant Elf MaleA A" (skin PeasantM1c: blond, orange suede tunic, plum
breeches; DAT class `CommonerElfMaleA`, 24 placements found in the rebuilt maps' raw objects) and **28 Prisoner** "Peasant
Elf MaleD A" (skin PeasantM1d: green wool jacket open over a cream shirt, red-brown breeches, dark hair; no DAT placement
found). Townsfolk batch, `devdocs/mm9_rework/overnight/TOWNSFOLK_BRIEF.md`. Built on the approved MM9 humanoid route
(MM9 skeleton and PeasantMale clips, never Mixamo; grafted five-finger hands; separate head set), with Annud's and the
Honk male's v2 scripts. Progress, hashes and Meshy receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_pm1d.glb` (`tools/install_model.py --world mm9`), identical to `v2/export/mm9_pm1d.glb`, sha256 `9e4828dd48e16b85...` (neck hole filled 2026-11-02; before `c75b7898b02face4...`, rollback `work/installed_preear.glb`) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, block `scripts/binding.yml` (`scripts/bind_under_lock.sh` under the flock): `MM9 22 Commoner` skin `pm1d_c`, `MM9 28 Prisoner` skin `pm1d_d`; scale 100, `yaw_offset -1.570796327`, stride 1.2 / 3.0 (`scripts/stride.py`: walk 1.14-1.26 m, run 2.7-3.5 m), look Neck/Head, melee impact 0.533 s (hattack2 `Rattack`, as Annud) |
| Descriptors | rows 22 and 28 added to `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` (fallback visuals 340 / 342, the stand-ins the maps use), tables regenerated: 9022 / 9028 |
| Triangles LOD0/1/2/3 | 7,995 / 3,997 / 1,437 / 478 (Smart Topology 14,165; head 3,772 kept at 0.75, hands 2 x 700 MPFB) |
| Clips (30 fps, PeasantMale library `source/mm9_lib/pmale.glb`) | Standing `stand1`, Walking `walk3`, Running `run`, Fidget `fidget1`, Talk `conv2`, AttackMelee `hattack2`, Hit `wince1`, Death `die1`, Dead; script clips Cower `cower` (NPCbase/retainer/ThronheimCity_Actor via BaseRun.inc), Conv1 `conv1` (NPC151.scr), Conv4 / Conv5 `conv4` / `conv5` (NPC150.scr). `npc4.scr` plays none; no marker `AnimationName` in the maps |
| Textures | body 2K colour + 1K normal + 1K ORM + 1K region mask (4 regions); head + hands set 2K colour + 1K normal + 1K ORM + 1K mask (2 regions); one set for both tiers |
| Meshy credits | **25** (Smart Topology 5, 4K body retexture 10, 4K head retexture 10; backup account, balance 3740 before the first job), no retries |
| Viewer | http://127.0.0.1:8912/level_generation/creatures/mm9_peasantm1d_claude/review/viewer/ revision `v8-20261102`, tiers `pm1d_c`, `pm1d_d` |

## Route (all from this project; commands in the scripts' headers)

0. **Sources** `scripts/convert_sources.sh` (both skins). **HD masters** from renders of the MM9 model with skin C
   (`scripts/ref_renders.py` -> `references_hd/mm9_views_c.png`, `mm9_head_views_c.png`, `mm9_skin_x4_c.png`), Codex
   (`scripts/codex_masters.sh 1|2`, brief `references_hd/CODEX_BRIEF.md`), 1536x1024; Codex's soft alpha halo removed by
   `scripts/clean_alpha.py` (raw returns in `references_hd/raw/`). Head turnaround `v2/references_head/` (`scripts/codex_head.sh`).
1. Meshy Smart Topology 15k from `00_three_quarter.png`; `scripts/fit_rig.py` (Annud's fit, `scripts/fit_config.json`;
   X-ray `review/xray_v1_sheet.png`) -> `work/fit_v1.blend`; `scripts/reduce_uv.py` -> `work/uv_v1.blend`;
   `scripts/prelabel.py` (`scripts/prelabel.json`: head = faces above z 0.66 of the one torso/arms/face shell plus every
   head part; four stray 5-vertex lace strips deleted) -> `work/label_v1.blend`.
2. Body UVs `v2/scripts/texpass_uv.py` (uv_atlas) -> `work/uv_tp.blend`, upload `texturing/pm1d_body_upload.glb`; 4K
   retexture `requests/retexture_body.json`; `bake_ao_texpass.py`, `compose_texpass.py` -> `textures/pm1d_*`.
3. Hands `v2/scripts/graft_hands.py` (`graft_pm1d.json`) -> `v2/work/hands_v1.blend`; `head_split.py` (`head_pm1d.json`)
   -> `head_v1.blend`; head UVs `texpass_head_uv.py` -> `v2/work/head_uv.blend`, upload `v2/texturing/pm1d_head_upload.glb`;
   4K head retexture `v2/requests/retexture_head.json`; `bake_hands.py` (young caucasian male skin), `compose_headhand.py
   --ref-head` (the body's "skin" class was mostly orange tunic, so the hands are graded to the face).
4. **Clean-up** `scripts/geo_fix.py` (`geo_fix.json`) -> `v2/work/fix_v1.blend` (the master): two 34 cm slivers from the
   jaw to the right collar deleted, four loose spikes/stubs on the back (Meshy modelled the laces there too) deleted, the
   left armpit fin and two collar folds laid flat by local smoothing (deleting them opened holes: first try). Paint:
   `scripts/tex_fix.py` (laces painted a second time on the back, and the fin's cream paint, refilled from the tunic),
   `grade_basecolor.py` gentle, `scripts/neck_match.py` (body neck skin 255/172/131 -> head neck 222/141/100).
   `scripts/neck_hole.py` fix_v1 -> **`v2/work/fix_v2.blend` (the master since 2026-11-02)**: see "Neck hole".
5. **Tiers** `scripts/tier_ramps.py`: body R tunic, G front panel (|x| < 6 cm, hem to neck: row 28's shirt), B breeches,
   A gold hem trim; head R hair (hair parts whole + painted scalp/forehead), G the collar painted into the head set.
   Tier C ramps fitted to our own paint; tier D quantile-matched to the PeasantM1d skin texels of the same region
   (MM9 skins share one UV layout, so C/D pairs come texel by texel; sampled over the MM9 mesh). Report in
   `textures/pm1d_ramps.json`.
6. **Runtime** `TOKEN=<lease> scripts/rebuild.sh <viewer revision> [--install]` -> `v2/scripts/build_runtime_v2.sh`:
   export, `clips_mm9.py` (`v2/scripts/roles_pm1d.json`, `soft_offsets`), `hand_rest.py` (`hand_rest_pm1d.txt`: Talk,
   Conv1, Conv4, Conv5), prepare, LODs, shadow LODs, `region_variants.py` (body + head), floor pass
   (`scripts/floor_ops.txt`), `mirror_glb.py` (true handedness: L Hand at x -0.62 with the toes toward +z in the
   converted ABC, as the Honks), `scripts/fix_winding.py` (one 6-triangle zero-volume boot-strap remnant in LOD1),
   winding check; viewer GLBs `v2/scripts/viewer_tiers.py` (bakes body and head ramps), manifest `make_viewer_tiers.py`.
   **Never re-run `texpass_uv.py` or `texpass_head_uv.py`**: the paid paints belong to `work/uv_tp.blend` and
   `v2/work/head_uv.blend`.

## Neck hole (2026-11-02, ear sweep)
Ear sweep (`claude_shared/mm9_overview/ear_sweep_20261102.png`, rows 1-2): "a small pale grey triangle under the jaw" on both
tiers. Checked against MM9 (`references_hd/mm9_head_views_c.png`) and the HD masters: no lace or collar there; the grey was the
render background seen through a **see-through hole**: a 6-edge boundary loop (two missing triangles meeting at a point, a
bow-tie, 1.2 cm) in the head set's neck skin under the right jaw (export GLB centre -0.038, 1.578, 0.054), not paint. Left by
`geo_fix.py`, which deleted the two 34 cm slivers from the jaw to the right collar. **Fix** `scripts/neck_hole.py` (Blender, on
`v2/work/fix_v1.blend` -> `fix_v2.blend`; `list` mode prints every boundary loop of up to 8 edges): the loop in the neck box is
filled with 4 triangles, the head material and attributes of its rim, and the rim's HeadUV where a face's corners lie in one UV
island (3 faces; the fourth spans a seam and takes its nearest rim face's mean texel). No vertex moved; clips identical
(`glb_diff.py` vs the previous install: 0.000 mm in every clip, every image the same; LOD0 6,526 -> 6,529 vertices, 7,995 ->
7,999 triangles). Two other small loops stay: a 4-edge one at the face front (0.041, 1.649, 0.105; 3 x 7 mm, an eye corner) and a
5-edge one on the crown under the hair. Sheet `review/sheet_ear_before_after.png` (both tiers, before v7 / after v8: ear-side
close-ups, both profiles, both 3/4 backs, both under-jaw views, party view from 22 deg). Winding 0; viewer v8-20261102 check
26 switches, 0 failed.
Regression after the last ear-sweep install (2026-11-02, `review/regression_actors_earsweep.log`): `--world mm9 actors` passed 192,
failed 1 (the known `out05_event_clearance_completes_from_monster_killed_hook` "could not load gameplay data");
`mm9_actor_models_build_every_binding` **PASS**.

## Checks (final GLB, 2026-11-01)

| Gate | Result |
|---|---|
| Arm and hand (`arm_hand_gate.py --outer-only --exact`, 48 fps, `v2/review/gates/arm_final.txt`) | hands 0 in 11 of 13 clips; **Conv1 L 3.1 cm, 31 frames** (MM9's hand at the chin/throat, as Annud's Conv1 3.0 cm) and **Conv5 L 1.8 cm, 13 frames** (thinker hand on the chin); forearms <= 0.7 cm; finger stretch max 2.34; 19 chains per hand. Raw MM9 clips before the rest: Talk 2.6, Conv1 5.6 / R 2.5, Conv4 2.4, Conv5 5.9 cm; AttackMelee R forearm 6.0 cm went to 0 with the clean-up |
| Jitter (`jitter_gate.py` vs MM9's untouched clips) | 0 fails (arm_clear.py first: Conv1 2.3 and Conv5 5.5 deg/f over MM9, so hand_rest.py) |
| Floor (`floor_audit.py --world mm9 --match 'MM9 2[28] *'`) | both OK: stand 0, walk -0.0..+0.0, living 0, dead 0 |
| Winding | 0 inverted closed parts |
| Bones (`bone_length_audit.py`) | 12 checked, 0 stretching |
| Detached (`detached_parts_audit.py`) | 0 detached (32 components) |
| Flat shading | 0.00 on both materials |
| `texture_quality.py` body | atlas 56.4 %, density p10/p50/p90 1482/1554/1609, spread 1.09, fragments 0.1 %, stretch p90 1.21 |
| `texture_quality.py` head + hands | atlas 43.5 % (62 % on the head upload; hands' squares), spread 1.47 (head denser by design), fragments 1.5 %, stretch p90 1.20 |
| Tier C ramp fit (8-bit mean / p95) | tunic 6.4 / 27, panel 6.2 / 27, breeches 1.9 / 5.5, trim 9.7 / 39, hair 2.7 / 7.4, collar 1.9 / 5.2 |
| Viewer `run_creature_review.py check` | 26 switches, 0 failed, 0 console errors |
| Regression `mm9_actor_models_build_every_binding` (`--world mm9`) | PASS, 168 descriptors on 69 models, 0 failed |

Sheets (viewer shots, read): `review/sheet_ear_before_after.png` (2026-11-02), `review/sheet_mm9_vs_ours.png`, `review/sheet_tiers.png`, `review/sheet_face.png`,
`review/face_closeup.png`, `review/strips_1.png` and `review/strips_2.png` (every clip at four times, tier C),
`review/close_contacts.png` (Conv1/Conv5 chin contacts, Talk and Standing hands).

## Deviations and open points

- **Tier D is a colour tier, not row 28's own face or pattern.** Same young face for both rows (MM9's PeasantM1d face is
  older, jowly and stubbled); the jacket is plain green wool from the suede paint's luminance (MM9: flecked tweed);
  breeches plain red-brown (MM9: checked, torn at the knees); the belt stays (MM9's jacket covers the waist). A real
  row-28 face would need a head retexture per tier (10 credits).
- Small remaining faults seen in the sheets: a jagged pale band at the brows under row 28's dark fringe (forehead paint
  between skin and hair), faint lace grooves on the upper back (Meshy modelled the back laces; paint refilled, relief in
  the normal map and AO stays), a crumpled patch at the right collar where the sliver fold was smoothed, a faint
  vertical UV seam on the front of the neck.
- Hands: MM9's mitten curl drives the five MPFB fingers (`finger_alias`, Annud's). No wrist_fix (the Honk's constant
  hand rotation) was applied.
- Symmetry not measured against MM9's bind.
- `attack_ranged` maps to AttackMelee (the engine requires the key; both rows are civilians).

## Binding plan for the map placements (not done: shared import code)

The rebuilt maps place these NPCs with `monster_id` 340 / 342 (MM6-MM8 "Peasant Elf MaleA A/C" sprites) from
`tools/mm9_import_discovery/mm9_npc_legacy_replacements.tsv` through `transcode_mm9_dat_to_odm.py`
(`build_mm9_npc_actor_lines`); nothing places 9022 / 9028 yet, as with Annud's row 54 (373). To show the 3D model in game:
make the transcoder emit `MM9_MONSTER_ID_BASE + row` for rows listed in `mm9_npc_actor_rows.tsv` (or set rows 22 and 28
to 9022 / 9028 in the replacements table if the transcoder accepts MM9 ids there), then regenerate the MM9 maps
(`tools/mm9_import_discovery/regenerate_mm9_maps.sh`) and the review root. This touches shared import code and every
MM9 map, so it is left to the orchestrator; all townsfolk rows in `mm9_npc_actor_rows.tsv` need the same switch.

## Not checked

Normal-speed playback was not watched (motion judged from strips and the jitter gate); no in-game run; LOD1-3 and shadow
meshes not looked at; foot sliding against the 1.2 / 3.0 strides; tier D clips (only Standing shots: same clips and mesh).

User artistic acceptance: not recorded.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_pm1d_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_pm1d_reduce_claude/before/`.


**See-through linings added post-install on 2026-11-05 by `level_generation/creatures/mm9_pm1d_lining_claude/`** (brief `devdocs/mm9_rework/overnight/LINING_BRIEF_20261105.md`; LOD0 6,623 -> 7,974, appended to the reduced mesh). A rebuild from this project must re-run the reduction and then the lining pass. Rollback source: `level_generation/creatures/mm9_pm1d_lining_claude/before/`.
