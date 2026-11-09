# MM9 Annud Redeye (`mm9_annud`, row 54 Shopkeeper, PeasantM6 body) reduction: candidate b r60 ready for review (2026-11-05; lease released)

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) /
[REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (relaxed keep set, face exact; prio-3
unique, user 2026-11-05 "do all"), ledger row 70 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:annud` (owner
annud-reduce-20261105); the creature's own `mm9:annud` / `mm9:annud_redeye` leases were free (no lease file). Source: the installed
`assets_source/worlds/mm9/models/mm9_annud.glb` (sha256 2091b0bd0fcd), copied to `before/` (the rollback source). No Meshy, no
credits, no repaint. **Not installed.** `../mm9_annud_claude/` was only read (its `v2/scripts/arm_hand_gate.py`, `jitter_gate.py`,
`shrink_shadow_lods.py` and `v2/work/mm9_annud_clips.glb` run in place).

**Family note (Hanndl).** `mm9_hanndl.glb` (row 58) is Annud's body with narrowed sleeves, his own paint and added linings (10,060
faces; face arrays not index-compatible with Annud's 8,560). It is being reduced by another agent in `../mm9_hanndl_reduce_claude/`;
that project was **only read** (its scripts copied into `scripts/` at 08:49 and renamed; nothing written there). Annud is cut on his
own GLB and paint, since the texture guard is per paint and the meshes differ.

| | LOD0 | body prim (tunic, trousers, boots, collar/laces) | head prim (shell, hair, hands) | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|
| installed | 8,560 | 3,538 | 5,022 | 4,279 | 1,537 | 509 |
| **b r60 (`export/mm9_annud_b60.glb`, sha256 76a8aea0b20b)** | **7,068 (-17.4 %)** | 2,864 | 4,204 | 3,532 | 1,266 | 419 |

Shadow LODs follow (7,068 / 3,532 / 1,266 / 419). Per group (free faces): hands 1,247 -> 915 (0.65, every finger, fingertips exact),
hair shell 1,007 -> 603 (0.6, hairline exact), scalp under the hair 173 -> 91 (0.5), boots 817 -> 517 (0.5), tunic + trouser tops
1,539 -> 1,165 (the 7 mm distance guard stops it before the ratio). Every vertex of the candidate is an installed vertex (only index
buffers changed); clips (15), skin, nodes, materials, variants (`pm6_a`, carried to every LOD and shadow primitive) and all 8 images are
identical (`same_clips.py`). Exact (`scripts/exact_head.py`, 0 missing): the open head shell (face, ears, beard, neck, the hairline
ring; 1,854 kept faces of 2,027) and every kept face of the set.

## Measured first: protected share
`scripts/analyze.py`, `scripts/head_survey.py` (`review/head_survey.png`), `scripts/make_sets_annud.py a` (`review/sets_a_*.png`):
body = tunic (1,610 incl. sleeves), trousers + boots (1,398), collar trims and lace pieces (530, kept whole); head = shell (2,027,
488 under the hair), hair bob (1,255), two MPFB hands (870 each). No linings (`twins.py`: 0 pairs; Annud's sleeves have Meshy's own
inner layer, part of the tunic piece). Set a keeps the shell except the scalp under the hair, hairline (hair within 12 mm of its rim or
of open skin), collar/neck seam, graft junction, soles, shoulder cloth (Clavicle/UpperArm-dominated, the jitter gate's term), faces the
hands come within 2 cm of in any 48 fps frame (`hand_contact_dm2.py`), fingertips (any distal-finger corner): **3,777 protected
(44.1 %)**, 4,783 free; 15 % of LOD0 = 27 % of the free part, so the ladder ran.

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`, Hanndl's copy)
Chart guard `MP_CHART=1` (12 subdivisions), the audit's own chart test `MP_AUDIT=1`, texture weight `MP_W5=4`, seam slides on the
hands, texture guard over **both looks and the region mask** (`MP_TIERS=ABM`, `scripts/tex_extract.py`: A default colour, B the pm6_a
ramps applied by `tier_textures.apply`, M the tunic mask), scored over every clip at 10 Hz plus a position+UV rest quadric.

## Ladders (limits for 1.78 m: p99 <= 5.34 mm, max <= 26.7 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_<label>.png`)
| ladder | change | LOD0 | p99 / max mm (worst) | IoU / SSIM | result |
|---|---|---:|---|---|---|
| a | set a; hands .65, hair .7, boots .6, scalp .6; 4 mm guard (5 mm boots) | 7,484 (-12.6 %) | 2.76 / 8.06 (PlayGetUp:18) | .9965 / .9966 | pass, under the ~15 % line (r60 = r50: the guard stops the tunic at 1,363 of 1,539; `work/mp_diag.log`: 1,854 distance refusals) |
| **b** | **a with a 7 mm guard, hair .6, boots .5, scalp .5** | **7,068 (-17.4 %)** | **4.55 / 11.41 (PlayGetUp:27)** | **.9947 / .9954** | **PASS, picked** (r60 = r50) |

## Gates, installed -> b r60 (`scripts/gates.sh`, `scripts/see_through.sh`; `review/gates_before/`, `review/gates_b60/`)
- **UV audit** (`../claude_shared/reduction_uv_audit.py`, `review/uv_audit_b60.json`): **0 escaping LOD0 faces in both primitives**.
  LOD1-3 (the LOD tool's decimate): body 113 / 95 / 48, head 212 / 189 / 110 against the installed file's 99 / 93 / 46, 190 / 170 / 112.
- Arm and hand (`--outer-only --exact`, 48 fps): equal or better in every clip (Conv1 R 2.1 -> 1.9 cm, Bow R 3.6 -> 3.1 cm 13 -> 12 f,
  Conv1 L 33 -> 32 f; forearm Standing L 1.0 -> 0.1, AttackMelee L 1.8 -> 0.9, Hit/Death/PlayDeath L 1.4-1.6 -> 0, Conv3 L 3.0 -> 0);
  finger stretch maxima equal or lower, minima within -0.06; wrists equal.
- Jitter vs MM9's untouched clips (`v2/work/mm9_annud_clips.glb`): identical text (7 accepted fails as installed).
- Sleeve poke (`sleeve_poke_gate.py`): 0 in every clip, both. Detached parts: the same three shallow lace/collar pieces. Flat shading
  0.00 both. Winding 0. Bone lengths: the same 2 thigh notes. Texture quality: body atlas 59.4 % both, stretch p90 1.09 -> 1.11; head
  set atlas 40.9 % both.
- See-through (PeasantDM2's/Hanndl's `see_through_gate.py`, step 4, 16 views; not one of Annud's own gates, run on both for comparison;
  `review/see_through_compare_b60.txt`): head, trousers, boots unchanged or lower; torso/collar within one pixel or one frame (Fidget
  collar 2 px 11 -> 14 frames, Conv3 torso 6 -> 7 px; Bow, Hit, Standing, Walking, PlayGetUp collar fewer); **sleeve L +1-2 px** in six
  clips (Running 10 -> 12, AttackMelee 13 -> 14, Bow/Conv3/Hit/Standing +1; Conv1 13 -> 12). That zone is a pre-existing sliver at the
  left cuff rim seen edge-on, present in every installed frame; the re-rendered worst frames (`review/see_through_sleeveL_b60_compare.png`,
  `review/see_sleeveL_{before,b60}/`) show the same few-pixel rim sliver, nothing new through the cloth.
- LODs (`scripts/lod_check.py`, every frame of every clip; `work/lod_check_{installed,b60}.json`), built by `scripts/build_lods.py`
  (tool defaults 0.5/0.18/0.06, 4 influences; soles, crown and the Death/Dead floor contact protected, 42 of 42 points snapped): height
  1.7965 m at every LOD; Standing and Dead lowest point 0.0 at every LOD (installed LOD2 floated 0.5 cm standing, LOD3 0.8 cm standing and
  1.5 cm in Dead); 0 stretched faces at every LOD, both.

## Review
Viewer (installed and reduced, both looks, all 15 clips; `run_creature_review.py check`: 60 switches, 0 failed, no console errors,
`review/viewer_check.txt`): http://127.0.0.1:8912/level_generation/creatures/mm9_annud_reduce_claude/review/viewer/
Sheets read (full size; installed left/above, b60 right/below): `review/sheet_face_b60.png` and `review/sheet_face_diff_b60.png` (front
close-up, 3/4, profile, low 3/4, party, both looks: face, beard, ears and neck black in every diff; only the hair shell facets and the
collar edge differ), `review/sheet_body_b60_{a,b}.png` (Standing front/3-4/back, Walking, Fidget, Death), `review/close_b60_{a,b}_{1..4}.png`
(arms, tunic hem front/back, Running hem, boots, Fidget, shoulders and hair from behind, AttackMelee, both wrists and cuffs, hair from
above, Death, Talk, belt knot, boots front, collar), `review/close_b60_fingers_{1,2}.png` (both hands outside/front/behind: every finger,
nails unchanged), `review/ladder_sheet_{a,b}.png`, `review/sets_a_{body,head,hands}.png`.
Look at: the back of the hair (0.6: facets at slightly different angles), the backs of the hands (0.65: a little smoother shading over the
knuckles), the inside of the wide cuffs.

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G="../claude_shared/gltf_venv/bin/python -W ignore"
REA_GLB=level_generation/creatures/mm9_annud_reduce_claude/before/mm9_annud.glb REA_NODE=Annud $BL -P scripts/import_source.py   # from the repo root
$BL -P scripts/dump_mesh.py; $G scripts/tex_extract.py; $G scripts/twins.py; $G scripts/head_survey.py
R=0.02 FPS=48 $G scripts/hand_contact_dm2.py; cp work/hand_contact.npy work/hand_contact_0.02.npy
SHOULDER=1 TIPS=1 CUFF_HAND=1 HANDS=hand_contact_0.02.npy $G scripts/make_sets_annud.py a
work/run_b.sh        # REA_HEIGHT_M=1.78 MP_TIERS=ABM MP_AUDIT=1 MP_CHART=1 MP_W5=4 MP_SEAM_GROUPS=1 MP_DMAX_MM=7 MP_DMAX_GROUPS=3:7 SETS=a MP_GROUPS=1:0.65,2:0.6,3:0.5,6:0.5 run_mp.sh b 0.6,0.5
scripts/build_mp.sh mp_b_r60 export/mm9_annud_b60.glb   # swap_mp -> build_lods (protected, snapped) -> creature's shrink_shadow_lods -> carry_variants -> fix_winding -> restore_materials
$G ../claude_shared/reduction_uv_audit.py export/mm9_annud_b60.glb before/mm9_annud.glb --json review/uv_audit_b60.json
$G scripts/exact_head.py export/mm9_annud_b60.glb a; work/queue_b60.sh; python3 scripts/see_through_compare.py b60
$G scripts/viewer_tiers_annud.py <glb> work/v_<inst|red>_a.glb work/v_<inst|red>_b.glb; python3 scripts/make_viewer_manifest.py b60 "inst_a=..." ...
scripts/shots.sh "inst_a red_a inst_b red_b"; scripts/close_shots_annud.sh "inst_a red_a inst_b red_b"; scripts/finger_shots.sh
$G scripts/shot_sheets.py b60; $G scripts/face_diff_sheet.py b60; $G scripts/close_sheet.py b60 <tier> <shots> <out>
```
Install (orchestrator, on the OK): `check_winding.py export/mm9_annud_b60.glb` (0), `tools/install_model.py export/mm9_annud_b60.glb
--world mm9 --name mm9_annud.glb`, the `mm9_actor_models_build_every_binding` regression, and add to `../mm9_annud_claude/README.md`:
"LOD0 reduced post-install on <date> by `mm9_annud_reduce_claude`; a rebuild from this project must re-run that reduction". Rollback:
`before/mm9_annud.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (stills, gates and viewer
only); LOD1-3 and shadow meshes by eye (numbers only); Annud's own Blender `sleeve_gate.py` (the shared `sleeve_poke_gate.py` and the
see-through gate ran instead); the pm6_a look in the engine's ramp shader (viewer copies bake the ramps with the engine rule).
