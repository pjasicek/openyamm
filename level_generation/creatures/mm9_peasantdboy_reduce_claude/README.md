# MM9 Dwarf boy (`mm9_peasantdboy`, PeasantDboy1, rows 67/68) reduction: candidate e r50 ready for review (2026-11-05)

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) /
[REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-2 townsfolk: relaxed keep set,
face exact), ledger row 31 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:peasantdboy` (owner
peasantdboy-reduce-20261104); the creature's own `mm9:peasantdboy` lease was free. Source: the installed
`assets_source/worlds/mm9/models/mm9_peasantdboy.glb` (sha256 ab3ec78feaac, identical to `../mm9_peasantdboy_claude/export/mm9_pdboy.glb`),
copied to `before/` (the rollback source). No Meshy, no credits, no repaint. **Not installed.** `../mm9_peasantdboy_claude/` was only read.

| | LOD0 | body prim (tunic, legs, buttons, linings) | head prim (head, hair + linings, hands) | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|
| installed | 12,983 | 4,606 | 8,377 | 6,490 | 2,336 | 776 |
| **e r50 (`export/mm9_peasantdboy.glb`, sha256 67e6695b3080)** | **10,585 (-18.5 %)** | 4,168 | 6,417 | 5,291 | 1,905 | 633 |

Per group (free faces cut): hands 1,350 -> 810 (0.6, every finger kept), hair shells 1,776 -> 1,066 (0.6) and their linings
1,842 -> 1,132, trousers/boots 773 -> 559, tunic 790 -> 642 (the guards stop it), body linings 996 -> 920. Head part (face skin,
ears, eyes, neck cap, mouth fill; 3,229) exact. Every vertex of the candidate is an installed vertex (positions, normals, UVs,
joints, weights are the installed bytes; only index buffers changed). Clips (9), skin, nodes, materials, region ramps,
`KHR_materials_variants`, all 9 images: identical (`same_clips.py`; `scripts/restore_materials.py` puts back the installed
material JSON that the LOD tool's writer re-serialises).

## Measured first: protected share
Parts by welded connected component (`scripts/analyze.py`): body prim = tunic with forearms and collar (3,018 incl. 882 linings),
two legs (1,090), buttons and detached sleeve-twin patches (498); head prim = head (3,229, one piece), three bob shells each with a
flipped inner twin (3,748), two MPFB hands (1,400). Linings (`../mm9_peasantdboy_claude/scripts/linings_dboy.sh`: hair twins 1.5 mm,
rim and sleeve twins 0.5-3 mm, one dark texel) are found by `scripts/twins.py`: back-to-back faces with identical weights and
opposite normals; 996 body + 1,842 hair pairs, all mutual, none ambiguous. Protected in set e (kept faces + the linings of kept
faces): 6,212 (47.8 %).

Keep set (`scripts/make_sets_dboy.py`, set e = `SHOULDER=1`): head part; small pieces (buttons); collar (tunic faces within 1 cm
of the head); graft junction (body/hand faces within 1.5 cm of each other: the painted wrist band); soles (1.2 cm); rim strips (faces
joining a rim to its lining), the 405 one-texel faces without a twin (clamped rim-lining offsets) and outer faces within 6 mm of
them; lining pairs that both carry UVs (inner-layer twins); set e adds tunic faces on any clavicle/upper-arm vertex (see jitter).
Paired linings are not cut: `scripts/mpqem.py` re-emits them from the surviving lined faces (the installed lining face where the
lined face is unchanged, otherwise the reversed corner map outer vertex -> lining vertex; vertices without a unique twin locked).

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`, PeasantF3's copy)
Chart guard `MP_CHART=1` (12 samples), texture guard over both tiers' baked body colours, head images and the region mask
(`scripts/tex_extract.py`), texture weight 4, seam slides on the hands, scored over every clip at 10 Hz. Added here: a distance
guard `MP_DMAX_MM` (every removed vertex, and every vertex removed earlier into either end, stays within DMAX of the new fan at
rest and in every 4th pose): the area-weighted quadric let 10-27 mm losses through on the tunic and trousers (ladders a/b).

## Ladders (limits for 1.014 m: p99 <= 3.04 mm, max <= 15.2 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_<label>.png`)
| ladder | change | LOD0 | p99 / max mm (worst) | IoU / SSIM | result |
|---|---|---:|---|---|---|
| a | set a, hands .6, hair .7, legs .6 | 10,517 | 3.46 / 26.8 (Death:6) | .989 / .988 | fail (tunic/trousers lost 10-27 mm) |
| b | + cost cap (wrong units: no effect on the misses) | 10,543 | 3.25 / 17.2 (AttackMelee:9) | .994 / .991 | fail |
| c | + distance guard 2.0 mm | 11,199 (-13.7 %) | 1.15 / 5.4 | .999 / .996 | pass, under 15 % |
| d | guard 3.5 mm, hair .6, legs .5 | 10,527 (-18.9 %) | 2.02 / 9.9 (Death:9) | .996 / .994 | pass; built: jitter Running R shoulder skin 1.58 -> 2.92 mm/f2 (FAIL) |
| **e** | **d + shoulders kept (set e)** | **10,585 (-18.5 %)** | **1.97 / 9.9 (Death:9)** | **.997 / .995** | **PASS, picked; every gate equal** |

d's jitter fail was the gate's statistic (p95 over the clavicle/upper-arm vertices; every remaining vertex moves exactly as
installed), but the brief says keep a failing part exact rather than iterate: e keeps the shoulders (+58 faces).

## Gates, installed -> e r50 (`scripts/gates.sh`: the creature's own gate scripts; `review/gates_before/`, `review/gates_e50/`)
- **UV audit** (`../claude_shared/reduction_uv_audit.py`, `review/uv_audit_e50.json`): **0 escaping LOD0 faces in both primitives**.
  LOD1-3 escapes come from the LOD tool's decimate, at the installed file's level (LOD1 142/227 vs installed 130/187, LOD2 125/208
  vs 133/199, LOD3 33/133 vs 40/163).
- Arm and hand (`--outer-only`): 0 frames > 1 cm, both hands, every clip, both; finger stretch maxima equal, minima +0.05.
- Jitter vs MM9's untouched clips: 0 fails both (Running R shoulder skin 1.58 both; largest change AttackMelee 0.03 -> 0.69 mm/f2,
  under the 2.0 limit).
- See-through (creature's `see_through_gate.py`, every clip, 16 views; worst px): boots 0/0, collar 0/0, head 4/4, sleeve L 15/15
  (frames 101 -> 105), sleeve R 15/15 (80 -> 79), torso 10/10 (58 -> 50 frames). Equal.
- Linings (`scripts/lining_gate.py`, new: lining vertices outside their primitive's outer surface): body most vertices > 0.5 mm
  equal within noise (Fidget 24/24, Hit 25 -> 21, AttackMelee 25 -> 26), largest Fidget 7.9 -> 10.5 mm, Hit 6.7 -> 10.1 mm (chest
  collar band; the lining faces face inward, so a poke shows nothing from outside); hair 40 -> 36 vertices, largest 3.2 -> 7.0 mm
  (an inner shell's lining past another shell's cut face at the crown; not visible in the hair-from-above close-ups).
- Detached parts: same list (L hand piece 700 -> 430 faces). Flat shading 0.00 both. Winding 0. Bone lengths 12 checked, 0
  stretching. Texture quality: body atlas 57.2 % both, stretch p90 1.09 -> 1.10; head 40.9 -> 40.8 %, stretch 1.20 both.
- LODs (`scripts/lod_check.py`, every frame of every clip; built by `scripts/build_lods.py`: tool ratios 0.5/0.18/0.06, 4
  influences, soles/crown/corpse contact protected and snapped): height 1.013 m at every LOD; lowest point at LOD1 equal to LOD0
  in every clip; LOD3 floats +0.6 cm only in Running (installed LOD3 +0.3..+1.3 cm in every clip); stretched faces 0 except LOD2
  Death 1 (installed 0).
- Sleeve poke: not applicable (bare forearms, the creature's README).

## Review
Viewer (installed and reduced, both tiers, all 9 clips; `run_creature_review.py check`: 36 switches, 0 failed, no console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_peasantdboy_reduce_claude/review/viewer/
Sheets read (installed left/above, e50 right/below): `review/sheet_face_e50.png` and `review/sheet_face_diff_e50.png` (front close-up,
3/4, profile, low 3/4, party; both tiers: face skin black in all ten, only hair and collar shading differ), `review/close_e50_a_2.png`
(boots, hair from behind, hair from above), `review/close_e50_a_4.png` (Running hem, Fidget2 hand at the face, AttackMelee, Hit),
`review/close_e50_b_hands.png`, `review/close_e50_b_3.png` (hem front/back, left sleeve); d50 (same cut minus the shoulders):
`review/sheet_face_d50.png`, `review/sheet_body_d50_a.png`, `review/close_d50_a_{1,2,3,hands}.png`. Generated, not opened:
`review/sheet_body_e50_{a,b}.png`, `review/close_e50_a_{hands,3}.png`, `review/close_e50_b_{2,4}.png`.
Look at: the fingertips (hands at 0.6: slightly more angular tips and knuckles), the white belt buckle (its right edge shades a little
darker: interpolated across a cut face), the hair outline from above (a touch more polygonal).

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_peasantdboy_reduce_claude/before/mm9_peasantdboy.glb REA_NODE=PeasantDBoy $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/twins.py; $G scripts/tex_extract.py; SHOULDER=1 $G scripts/make_sets_dboy.py e
MP_DMAX_MM=3.5 MP_CHART=1 MP_W5=4 MP_SEAM_GROUPS=1 SETS=e MP_GROUPS=1:0.6,2:0.6,3:0.5,5:0.5 scripts/run_mp.sh e 0.5
scripts/build_mp.sh mp_e_r50 export/mm9_peasantdboy.glb   # swap_mp -> build_lods -> creature's shrink_shadow_lods -> carry_variants -> fix_winding -> restore_materials
$G ../claude_shared/reduction_uv_audit.py export/mm9_peasantdboy.glb before/mm9_peasantdboy.glb --json review/uv_audit_e50.json
scripts/gates.sh export/mm9_peasantdboy.glb e50; REA_NODE=PeasantDBoy $BL -P scripts/lod_check.py -- $PWD/export/mm9_peasantdboy.glb e50
scripts/see_through.sh export/mm9_peasantdboy.glb e50
$G scripts/viewer_tiers.py export/mm9_peasantdboy.glb red; python3 scripts/make_viewer_manifest.py e50 inst_a=..=work/viewer_inst_th_a.glb red_a=.. inst_b=.. red_b=..
scripts/shots.sh; scripts/close_shots.sh; scripts/close_shots2.sh; $G scripts/shot_sheets.py e50; $G scripts/face_diff_sheet.py e50
```
Install (orchestrator, on the OK): `check_winding.py export/mm9_peasantdboy.glb` (0), `tools/install_model.py export/mm9_peasantdboy.glb
--world mm9 --name mm9_peasantdboy.glb`, the `mm9_actor_models_build_every_binding` regression, and add to
`../mm9_peasantdboy_claude/README.md`: "LOD0 reduced post-install on <date> by `mm9_peasantdboy_reduce_claude`; a rebuild from this
project must re-run that reduction". Rollback: `before/mm9_peasantdboy.glb`. The d50 build is kept in `work/cand_d50/`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (frames, gates and
viewer stills only); LOD1-3 and shadow meshes by eye (numbers only); the full-body viewer shots frame the 1 m figure small, so the
body was judged from the coordinate close-ups; the viewer's shoulder/rear-shoulder preset shots came out empty for this small figure.
