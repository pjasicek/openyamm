# MM9 PeasantM5 (`mm9_peasantm5`, the stocky bearded townsman, row 67) reduction: candidate c r55 ready for review (2026-11-05; lease released)

## Fix pass c r55 (orchestrator pre-screen of b r55, 2026-11-05) - current candidate
The pre-screen found one brighter strand on the crown from behind (`review/close_b55_3.png` c11): a light streak in the hair. Located by
colour drift first (`scripts/hair_drift_m5.py`): the strand texture is high-frequency, so 214 of 741 hair faces drift > 12 and a keep set
from it would hold nearly all the hair; the coordinator's other option was taken instead: **hair shell 0.6 -> 0.7** (`run_mp.sh c`, all
else as b). LOD0 **7,252 (-16.6 %)**: hair shell 703 -> 491 free (b: 421); body primitive identical to b (3,342); LOD1-3 3,625 / 1,304 /
433. `export/mm9_peasantm5.glb` = `export/mm9_peasantm5_c55.glb` (sha256 below in the ledger); b r55 kept as `export/mm9_peasantm5_b55.glb`.
- Ladder c r55: p99 3.51 / max 12.0 mm (Death:12), IoU .9916, SSIM .9935, PASS (`review/ladder_sheet_c.png`).
- UV audit `review/uv_audit_c55.json`: 0 escaping LOD0 faces in both primitives. `exact_head.py`: face shell, collar, eyes, every kept
  face present byte-exact, every vertex an installed one; winding 0.
- Crown re-rendered both tiers (`scripts/crown_shots.sh`: c11 from behind right above, c14 from behind left above, c6):
  `review/crown_c55.png` (installed | b55 | c55) and `review/crop_crown_c11_a_inst_b55_c55.png` (full size): the streak is gone in c55
  and the crown reads as the installed in both tiers.
- Hair stretch (`scripts/hair_stretch_m5.py`, new): every-edge and >= 5 mm maxima identical to the installed in every clip (installed,
  b55 and c55 all equal; the maxima are the installed's own edges). See-through (`review/gates_c55/`): head zone worst pixels equal
  in every clip (frames within +-2), other zones as b55. LODs (`work/lod_check_c55.log`): height 1.7721 m at every LOD (= installed),
  floor per clip equal to LOD0 except LOD2 Walking -0.70 cm (as b55); 0 stretched faces. Viewer (now installed vs c55, both tiers):
  40 switches, 0 failed (`review/viewer_check_c55.txt`).
- Not re-run on c55 (body primitive byte-identical to b55, head change only in the hair shell): arm/hand, jitter, sleeve poke, linings,
  beard (face shell exact), detached, texture quality; the face/body sheets below are b55's.

## First candidate b r55 (superseded by c r55)

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) /
[REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-2 townsfolk: relaxed keep
set, face exact), ledger row 67 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:peasantm5` (owner
peasantm5-reduce-20261105); the creature's own `mm9:peasantm5` lease was free (no lease file). Source: the installed
`assets_source/worlds/mm9/models/mm9_peasantm5.glb` (sha256 a7e5f69a2ed7, identical to `../mm9_peasantm5_claude/export/mm9_pm5.glb`),
copied to `before/` (the rollback source). No Meshy, no credits, no repaint. **Not installed.** `../mm9_peasantm5_claude/` was only read
(its `arm_hand_gate.py`, `jitter_gate.py`, `shrink_shadow_lods.py` and `work/mm9_pm5_clips.glb` run in place; `sleeve_poke_gate.py` and
`see_through_gate.py` copied here). Scripts are copies of `../mm9_peasantm8_reduce_claude/scripts/` (linings, mpqem, LODs) with
`../mm9_peasantm1_reduce_claude/`'s two-tier texture extraction and viewer scripts and DM4's beard gate, adapted to this mesh.

**Family note:** PeasantM5 is a variant of Markel's body (row 76, deferred unique, not reduced). No other GLB shares this mesh, so
nothing else was re-derived.

| | LOD0 | body prim `PeasantM5_A` | head prim `PeasantM5Head` | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|
| installed | 8,698 | 4,060 | 4,638 | 4,347 | 1,563 | 521 |
| **b r55 (`export/mm9_peasantm5.glb` = `export/mm9_peasantm5_b55.glb`, sha256 ce412b362d88)** | **7,182 (-17.4 %)** | 3,342 | 3,840 | 3,589 | 1,292 | 428 |

Per group (free faces cut): MPFB hands 1,289 -> 773 (0.6, every finger; graft faces exact), hair shell 703 -> 421 (0.6; hairline
2 rings + the crown hole rims exact), trousers/boots 1,128 -> 824 (6 mm guard), shirt 1,384 -> 1,090 (5 mm guard stops it), linings
742 -> 622 re-emitted from the cut cloth (`work/twins.npz`, 403 installed + 219 re-emitted). Every vertex of the candidate is an
installed vertex (only index buffers changed); clips (10), skin, nodes, materials, `KHR_materials_variants` (pm5_a, pm5_b), all 9
images identical (`review/gates_b55/same_clips.txt`). Face shell (face, painted beard, ears, neck) 1,820, collar ring 301, eyes 96,
buckle and every kept face present exactly (`scripts/exact_head.py`: 0 missing).

## Measured first: protected share
`scripts/analyze.py`, `scripts/head_survey_m5.py` (`review/head_survey.png`): the beard is painted on the closed face shell (no beard
geometry of its own); the hair shell is a separate cap; the raised collar ring is in the head material. Set a (`scripts/make_sets_m5.py a`):
face shell, collar, eyes, buckle, hairline, cuffs/graft (4 cm / 1.5 cm of a hand vertex), collar band of the body (1 cm), soles, rim strips,
loose linings + halo, and the beard contact (body faces within 3 cm of a beard vertex, 85 faces) exact: 3,608 protected (41.5 %), free
4,504; 15 % of LOD0 (1,305) is 29 % of the free part, under the 40 % line, so the run went ahead.

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`, PeasantM8's copy)
Chart guard `MP_CHART=1`, texture guard over both tiers (`scripts/tex_extract.py`: body tone with each tier's ramps + region mask, head:
each tier's own image), texture weight 4, seam slides on the hands, scored over every clip at 10 Hz, distance guard, linings re-emitted.

## Ladders (limits for 1.759 m: p99 <= 5.28 mm, max <= 26.4 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_{a,b}.png`)
| ladder | change | LOD0 | p99 / max mm (worst) | IoU / SSIM | result |
|---|---|---:|---|---|---|
| a | set a, hands .6, legs .6, hair .65, shirt r60 / r50, 4 mm guard everywhere | 7,428 (-14.6 %) | 2.74 / 11.2 (Death:30) | .994 / .995 | pass, but under ~15 % (guard stopped shirt and legs) |
| **b** | **a with shirt 5 mm / legs 6 mm guard, legs .55, hair .6, r55** | **7,182 (-17.4 %)** | **3.53 / 12.0 (Death:12)** | **.9915 / .9934** | **PASS, picked; gates equal** |

Two ladders (cap three).

## Gates, installed -> b r55 (`scripts/gates.sh`, `scripts/see_through.sh`; `review/gates_before/`, `review/gates_b55/`)
- **UV audit** (`review/uv_audit_b55.json`): **0 escaping LOD0 faces in both primitives**. LOD1-3 (LOD tool's decimate) body/head
  119/130, 68/149, 43/97 vs the installed's own 111/105, 96/138, 47/107.
- Arm and hand (`--outer-only --exact`, 48 fps): hand depths and frames identical in every clip (Fidget R 1.4 cm 4 f, as installed);
  forearms identical (Talk R 4.5, AttackMelee R 4.4 cm as installed); finger stretch maxima equal or lower.
- Jitter vs MM9's clips: 0 fails both; shoulder-skin excess within 0.0-0.83 mm/f2 (installed 0.0-1.52; AttackMelee L 0.18 -> 0.65,
  Hit L 0.11 -> 0.28, limit 2.0): fewer vertices in the sample, each vertex moves as installed.
- **Beard** (`scripts/beard_gate_m5.py`): stretch, contact gap and approach identical in every clip (494 beard faces, 24 contact verts).
- Sleeve poke: 0 mm every clip both (candidate vertices R 78 -> 75). Linings (`lining_gate.py`): max out equal or lower per clip,
  outlying vertices equal or fewer.
- See-through (creature's gate, every 3rd 30 fps frame, 16 views; `python3 scripts/see_through_compare.py b55`): every zone's worst
  pixels equal or lower (Dead torso 6 -> 5, Death sleeve R 1 -> 0); new single-pixel single-frame hits Hit sleeve L 1 px (frame 15) and
  Talk sleeve R 1 px (`review/gates_b55/see_through_sleeveL_Hit_15_az045_el20.png`).
- Detached 0 both; flat shading 0.00 both; winding 0; bone lengths 12 checked, 0 stretching. Texture quality: body 58.5 % both, stretch
  p90 1.30 -> 1.31; head 39.1 -> 39.0 %, stretch 1.72 -> 1.74, fragments 1.7 -> 2.2 %.
- LODs (`scripts/lod_check.py`; `scripts/build_lods.py` 0.5/0.18/0.06, 4 influences, 31 of 31 protected points mapped): height
  1.7716 m at every LOD (installed 1.7721 / 1.7722 / 1.7729 / 1.7704); LOD0 lowest point per clip identical to installed; LOD1-3 equal
  to LOD0 in every clip except LOD2 Walking -0.70 cm (LOD0 -0.18; installed LOD3 floated up to +0.5 cm, LOD2 Running +1.3); 0
  stretched faces at every LOD (installed LOD1 1). Logs `work/lod_check_{installed,b55}.{log,json}`.

## Review
Viewer (installed and reduced, both tiers, all 10 clips; `run_creature_review.py check`: 40 switches, 0 failed, no console errors,
`review/viewer_check.txt`): http://127.0.0.1:8912/level_generation/creatures/mm9_peasantm5_reduce_claude/review/viewer/
Sheets read (installed left/above, b55 right/below): `review/sheet_face_b55.png`, `review/sheet_face_diff_b55.png` (front close-up, 3/4,
profile, low 3/4, party, both tiers: face skin, beard, ears and neck black in all ten diffs; hair shell and the shirt shoulders differ in
shading), `review/crop_hair_profile_b55.png`, `review/sheet_body_b55_{a,b}.png` (Standing front/3-4/back, Walking, Talk, Death),
`review/close_b55_{1,2,3,4}.png` (arms, belt/hem front and back, Running hem, boots, Talk arms, shoulders and hair from behind, Hit,
sleeves and cuffs, crown from behind above, shirt front), `review/close_b55_hands.png` (both hands with fingers), `review/sets_a_{body,head}.png`.
Look at: the hands (0.6: thumb tips slightly more angular), the crown from behind (`close_b55_3.png` c11: one brighter strand streak),
the shirt hem's lower edge from the side (`close_b55_3.png` c9).

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_peasantm5_reduce_claude/before/mm9_peasantm5.glb REA_NODE=PeasantM5 $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/twins.py; $G scripts/tex_extract.py; $G scripts/make_sets_m5.py a
REA_HEIGHT_M=1.759 MP_DMAX_MM=4 MP_DMAX_GROUPS=0:5,3:6 MP_CHART=1 MP_W5=4 MP_SEAM_GROUPS=1 SETS=a MP_GROUPS=1:0.6,3:0.55,6:0.6 scripts/run_mp.sh b 0.55
scripts/build_mp.sh mp_b_r55 export/mm9_peasantm5_b55.glb   # swap_mp -> build_lods -> creature's shrink_shadow_lods -> carry_variants -> fix_winding -> restore_materials
$G ../claude_shared/reduction_uv_audit.py export/mm9_peasantm5_b55.glb before/mm9_peasantm5.glb --json review/uv_audit_b55.json
$G scripts/exact_head.py export/mm9_peasantm5_b55.glb a
work/queue_b55.sh   # gates.sh, see_through.sh (installed and b55), lod_check.py (installed and b55); python3 scripts/see_through_compare.py b55
$G scripts/viewer_tiers.py before/mm9_peasantm5.glb inst; $G scripts/viewer_tiers.py export/mm9_peasantm5_b55.glb red
$G scripts/make_viewer_manifest.py b55 "inst_a=..=work/viewer_inst_th_a.glb" "red_a=..=work/viewer_red_th_a.glb" "inst_b=.." "red_b=.."
HEADUP=0,0.08,0.05 scripts/shots.sh; scripts/close_shots.sh "inst_a red_a"; scripts/hand_shots.sh "inst_a red_a"
$G scripts/shot_sheets.py b55; $G scripts/face_diff_sheet.py b55; $G scripts/close_sheet.py b55 a c0,c1,c2,c3 review/close_b55_1.png   # ...
```
(The viewer shots time out on a model's first load while Blender runs: run each first model twice.)
Install (orchestrator, on the OK): `check_winding.py export/mm9_peasantm5.glb` (0), `tools/install_model.py export/mm9_peasantm5.glb
--world mm9 --name mm9_peasantm5.glb`, the `mm9_actor_models_build_every_binding` regression, and add to
`../mm9_peasantm5_claude/README.md`: "LOD0 reduced post-install on <date> by `mm9_peasantm5_reduce_claude`; a rebuild from this
project must re-run that reduction". Rollback: `before/mm9_peasantm5.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (stills, gates and
viewer check only); LOD1-3 and shadow meshes by eye (numbers only); tier B close-ups (tier B differs only by colour ramps and its
own head image; its face and body sheets were read).
