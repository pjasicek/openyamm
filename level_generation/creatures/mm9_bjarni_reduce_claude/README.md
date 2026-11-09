# MM9 Bjarni Thorvaldssen (`mm9_bjarni`, unique NPC, ledger row 78) reduction: candidate b r60 ready for review (2026-11-05; lease released)

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) /
[REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio 3; user 2026-11-05 "do all": uniques
reduced too, face exact), row 78 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:bjarni` (owner bjarni-reduce-20261105);
the creature's own `mm9:bjarni` lease was free (empty lock, no lease file). Source: the installed `assets_source/worlds/mm9/models/mm9_bjarni.glb`
(sha256 e51870d1339e, identical to `../mm9_bjarni_claude/export/mm9_bj.glb`), copied to `before/` (rollback). No Meshy, no credits, no repaint,
**no linings added** (open user decision). **Not installed.** `../mm9_bjarni_claude/` was only read (its arm/hand, sleeve poke, jitter, shading,
mirror and shrink_shadow_lods scripts and `work/mm9_bj_clips.glb` run in place). Scripts are copies of `../mm9_markel_reduce_claude/` (same build
route: Meshy body + MPFB hands + one head set, one skin), the see-through gate from `../mm9_tryggva_reduce_claude/`, renamed to `Bjarni` /
`BjarniHead`.

| | LOD0 | body prim `Bjarni` | head prim `BjarniHead` | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|
| installed | 8,089 | 4,569 | 3,520 | 4,036 | 1,444 | 475 |
| **b r60 (`export/mm9_bjarni.glb` = `export/mm9_bjarni_b60.glb`, sha256 ef96e332ec88)** | **6,841 (-15.4 %)** | 3,849 | 2,992 | 3,413 | 1,219 | 399 |

Per group (free faces cut): MPFB hands 827 -> 527 (0.6; fingertips exact), scalp hair 676 -> 448 (guard-limited), trousers 1,219 -> 801,
boots 281 -> 183, tunic + yoke 1,080 -> 882 (6 mm distance guard), skirt 61 -> 55. Every vertex of the candidate is an installed vertex (only
index buffers changed); clips (18), skin, nodes, materials and all 6 images identical (`review/gates_b60/same_clips.txt`). Exact
(`scripts/exact_head.py`: 0 missing of 3,945 kept): the face / beard / sideburn part of the head shell (1,010), scalp hairline ring, 30 necklace
beads with the painted tusks + medallion + buckle + trouser studs (1,185, whole), neck pieces (67), cuffs, hand graft, collar contact, soles,
skirt rims, fingertips, the trouser side strips.

## Measured first: protected share
Bjarni's face, beard and hair are **one** Meshy shell (2,055 faces); `scripts/head_classes_bj.py` splits it by texture colour and position into
face/beard/sideburns (kept, 1,010) and scalp hair above the brows / behind the ears (1,045, cuttable; `review/head_classes_bj.png`). No linings
(`twins.py`: 0 pairs). Set a0 (no fingertips/contact): 44.5 % protected; set a 46.4 %; set b 48.8 % (3,945 kept, 4,144 free; 15 % of LOD0 = 29 %
of the free part), so the run went ahead. Hand-vs-hand contact (`hand_contact_mk.py`, 1.2-2 cm) covers 934-1,096 of the 1,398 hand faces
(clasped hands in several clips): keeping it would mean exact hands and no useful gain, so the hands were cut with fingertips exact and the
Applause clap checked by the gates instead.

## Route
Pose-aware half-edge collapse (`scripts/mpqem.py`, Markel's copy) with the chart guard (`MP_CHART=1`), the audit's chart test inside each
collapse (`MP_AUDIT=1`), shading-normal guard (`MP_NRM=1`), shoulder-dominant vertices locked (`MP_LOCK_DOM=Clavicle,UpperArm`, the jitter
gate's sample), texture guard, texture weight 4, seam slides on the hands, scored over all 18 clips; distance guards 4 mm (hands, scalp),
6 mm tunic/yoke, 7 mm trousers and boots, 5 mm skirt.

## Ladders (limits for 1.80 m: p99 <= 5.4 mm, max <= 27 mm, IoU >= .98, SSIM >= .93)
| ladder | change | LOD0 | p99 / max mm | IoU / SSIM | result |
|---|---|---:|---|---|---|
| a | set a; hands .6, trousers .55, boots .55, scalp .65, skirt .6, tunic r60 (= r50, guard stops it) | 6,771 (-16.3 %) | 4.57 / 10.7 (Death:12) | .993 / .9963 | pass; built a60: **black wedge beside the R trouser strip** (`review/crop_h1_strip_a60.png`) and **detached 0 -> 2** (two 4-face trouser studs floating 5 mm over the cut thigh) |
| **b** | **a + trouser side strips and studs exact (`scripts/strip_keep_bj.py`, 195 faces, `review/strip_keep.png`); trousers/boots .5, scalp .6** | **6,841 (-15.4 %)** | **4.43 / 10.7 (Death:12)** | **.995 / .9969** | **PASS, picked** (both a60 faults gone) |

Two ladders; `export/mm9_bjarni_a60.glb` is **rejected** (strip wedge, detached studs).

## Gates, installed -> b r60 (`scripts/gates.sh`, the creature's gate set; `review/gates_before/`, `review/gates_b60/`)
- **UV audit** (`review/uv_audit_b60.json`): **0 escaping LOD0 faces in both primitives**. LOD1-3 (the LOD tool's decimate) body/head 147/139,
  107/143, 62/91 against the installed file's own 142/119, 121/131, 80/107.
- Jitter vs MM9's clips (unmirrored): **identical report**, 0 fails. Sleeve poke: identical (0 everywhere except the installed ArgumentShot1A R
  28.5 mm, 2 vertices). Bones: the same two thigh notes. Detached: 0 both (root-lift/shallow notes the same pieces). Flat shading 0.0/0.1 % both;
  winding 0. Texture quality: body 59.9 % both, stretch p90 1.09 -> 1.11; head set 44.7 % both, fragments 1.5 -> 1.6 %.
- Arm and hand (48 fps): equal except **Applause R hand 2.0 -> 2.1 cm** (28 -> 26 frames over 1 cm; the clapping hands meet as installed).
  Second opinion `scripts/arm_inside_check.py` (parity rays, every frame): Applause R 1.9 cm on 12 vertices -> 2.0 cm on 2 vertices; L 1.9 cm on
  7 -> 1.8 cm on 3. Fidget R 2.9 -> 2.8, Applause L forearm 1.5 -> 1.1; finger stretch maxima equal, minima within -0.07.
- **See-through** (`scripts/see_through.sh`, step 9, 16 views, every clip; `python3 scripts/st_compare.py before a60 b60`): sum of zone maxima
  **71,319 -> 70,970 (-0.5 %)**. Collar lower in 16 of 18 clips, sleeves equal (+/- 8 px), torso lower in 12 clips and higher in 6 (+15..+63 px on
  ~1,000-4,700: ArgumentShake 1,105 -> 1,168, Speak9 1,260 -> 1,296, Fidget/Hit/Running/Death +9..+23), boots/head/trousers +1..+7 px in a few
  clips. The torso worst frames re-rendered (`review/gates_{before,b60}/st_torso_*`, `review/st_torso_speak9_cmp_b60.png`) show the installed
  opening behind the yoke's back panel with a marginally different outline, no new hole.
- LODs (`scripts/lod_check.py`, every frame of every clip; `work/lod_check_{installed,b60}.json`; `scripts/build_lods.py` 0.5/0.18/0.06, 4
  influences, 29 of 29 protected points snapped): height 1.799 m at LOD0-2, 1.8014 at LOD3 (installed 1.7998/1.7983/1.8051); LOD0 lowest point per
  clip identical to installed; LOD1-3 within 0.8 mm of LOD0 in every clip (installed LOD2 8.8 mm, LOD3 15.6 mm); 0 stretched faces at every LOD.

## Review
Viewer (installed and b r60, one skin, all 18 clips): http://127.0.0.1:8912/level_generation/creatures/mm9_bjarni_reduce_claude/review/viewer/
(`run_creature_review.py check` per model: 36 switches, 0 failed, no console errors, `review/viewer_check_{inst_a,red_a}.txt`). The 8912 server
was not running during this job; shots and checks used a temporary `python3 -m http.server 8937` started and stopped by this agent.
Sheets read at full size (installed left/above): `review/sheet_face_b60.png` + `review/sheet_face_diff_b60.png` (front close-up, 3/4, profile, low
3/4, party: face, beard, eyes and ears black in all five diffs; only the scalp hair facets and the yoke edge behind the beads differ),
`review/crop_hair_profile_a60.png` (same scalp cut as b), `review/sheet_body_b60_a.png` (Standing front/3-4/back, Walking, Talk, Death),
`review/close_b60_{1,2,3}.png` (arms, belt/skirt front and back, Running skirt, boots and laces, Talk arms, yoke from behind, Hit, skirt sides, R
bracer knotwork, hair from behind above, belt buckle), `review/close_b60_hands.png`, `review/crop_h1_strip_b60.png` (trouser strip: no wedge).
Look at: the back/top of the hair (0.6: slightly flatter facets on the silhouette), the backs of the hands (0.6), the yoke's back panel edge.

## Build (project folder)
```sh
BL="flock work/blender.lock scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
(repo root) REA_GLB=level_generation/creatures/mm9_bjarni_reduce_claude/before/mm9_bjarni.glb REA_NODE=Bjarni $BL -P .../scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/twins.py; $G scripts/tex_extract.py; $G scripts/head_classes_bj.py
R=0.02 FPS=16 $G scripts/hand_contact_mk.py work/hand_contact_bj20.npy   # split into _body/_hands/_scalp masks (inline, see work/)
MOUTH_Y=1.63 HRING=1 TIPS=1 EXTRA=work/hand_contact_bj20_body.npy $G scripts/make_sets_bj.py a; $G scripts/strip_keep_bj.py a
MOUTH_Y=1.63 HRING=1 TIPS=1 EXTRA=work/hand_contact_bj20_body.npy,work/strip_keep.npy $G scripts/make_sets_bj.py b
work/run_b.sh        # mpqem + reduce_ladder + compare_ladder (env in the file)
work/queue_b60.sh    # build_mp.sh mp_b_r60 -> UV audit -> exact_head -> gates.sh -> see_through.sh step=9
$G scripts/viewer_tiers.py export/mm9_bjarni_b60.glb red; $G scripts/make_viewer_manifest.py b60 "inst_a=..." "red_a=..."
PORT=8912 scripts/shots.sh; scripts/close_shots.sh; scripts/hand_shots.sh; $G scripts/shot_sheets.py b60; $G scripts/face_diff_sheet.py b60
```
Install (orchestrator, on the OK): `install_reduced.sh bjarni mm9_bjarni export/mm9_bjarni.glb level_generation/creatures/mm9_bjarni_claude`
(or `check_winding.py` + `tools/install_model.py export/mm9_bjarni.glb --world mm9 --name mm9_bjarni.glb`), the binding regression, and the
"LOD0 reduced post-install" line in `../mm9_bjarni_claude/README.md`. Rollback: `before/mm9_bjarni.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (stills, gates, viewer check only);
the seated/argument clips by eye (numbers only); LOD1-3 and shadow meshes by eye (numbers only); the beard gate is Markel's copy (painted beard vs
chest; identical text installed vs b60).
