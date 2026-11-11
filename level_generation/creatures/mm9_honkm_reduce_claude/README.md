# MM9 Honk male (`mm9_honkm`, Honk / Elder Honk / Honk Seer) reduction: candidate n r60 ready for install (2026-11-04)

**Final candidate n r60 (orchestrator pre-screen, 2026-11-04): l r60 with the medallion kept exact** ("the rosette visibly warps in
close-up; ~120 tris is worth it"). `export/mm9_honkm.glb` sha256 5b865cbd82c5: LOD0 **6,986 (-13.1 %)**, body set 2,989, head+hands
3,997; LOD1-3 3,491 / 1,257 / 417. Ladder p99 3.09 / max 14.5 mm, IoU .999, SSIM .994. `reduction_uv_audit.py`: 0 escaping faces
at LOD0 (`review/uv_audit_n60.json`; LOD1-3 escape counts at the level of the installed LODs, same LOD builder). Exact faces 0
missing, medallion 216/216. Gates (`review/gates_compare_n60.txt`) identical to l r60 below except the medallion piece count and
flat shading 0.02 (= installed); LOD heights 1.799 m and floor equal to LOD0 at every LOD (`review/lod_summary_n60.txt`).
Sheets read: `review/crop_medallion_n60_a.png` (identical), `review/close_n60_a_hands.png`, `review/sheet_face_diff_n60.png`.
Viewer revision r3-n60-20261104, `run_creature_review.py check` 132 switches, 0 failed. Rebuild: `scripts/reproduce.sh`.
The rest of this file describes l r60, the reviewed step before the medallion change.

## Candidate l r60 (superseded by n r60)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-1 relaxed keep set),
ledger row 81 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:honkm` (owner honkm-reduce-20261104).
Source: the installed `assets_source/worlds/mm9/models/mm9_honkm.glb` (sha256 4a5c84880d03, identical to
`../mm9_honkmale_claude/v2/export/mm9_honkm.glb`), copied to `before/` (the rollback source). No Meshy, no credits, no
repaint. **Not installed.** `../mm9_honkmale_claude/` was only read. The hats (`mm9_honkhat.glb`, `mm9_elderhonkhat.glb`) are
separate GLBs on `Bip01 Head` and were not touched; the head socket is the unchanged bone.

| | LOD0 | body set (`HonkM_A`) | head + hands set (`HonkMHead`) | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|
| installed | 8,038 | 3,087 | 4,951 | 4,018 | 1,445 | 480 |
| **l r60 (`export/mm9_honkm.glb`, sha256 12f5b54b16e4)** | **6,864 (-14.6 %)** | 2,867 | 3,997 | 3,430 | 1,235 | 410 |

Every vertex of the candidate is an installed vertex (positions, normals, UVs, joints, weights are the installed bytes; only
index buffers changed). Clips, skin, nodes, materials, `KHR_materials_variants`, images: byte-identical (`same_clips.py`:
identical). Face skin (with beard, moustache, ears, neck), eyes and mouth pieces, collar chain, buckle, linings and lined
faces: the installed triangles (`review/face_exact_l60.txt`: 0 missing). Faces leaving the source UV charts: **0**
(`review/uv_escape_l60.txt`, the orchestrator's chart check; the first build d r60 had 55 on the hands, see below).

## Where the cut is
Protected share first (brief): face skin 1,753 + eyes/mouth 405 + linings/lined 1,011 + collar 156 + soles, junctions and
hairline make about 58 % of the mesh exact, so ~15 % is close to the limit for this body. The body set was already lean
(sleeves and robe at 2-6 cm triangles).

| region | installed | candidate | ratio |
|---|---:|---:|---|
| hands + forearm stubs (every finger, the hand-graft junction 3.5 cm round the wrist exact) | 1,672 | 1,074 | 0.6 of the free faces, seam slides with a chart guard |
| hair shell (tier A brown paint behind the face box; hairline 8 mm exact) | 1,121 | 655 | 0.6 |
| medallion (rigid Spine3 disc) | 216 | 94 | 0.35 |
| sleeves (robe on the arms) | 410 free | 348 | 0.85 (0.75 failed the jitter gate) |
| robe torso (outside the paint edges, neck zone, hand contact) | 124 free | 88 | 0.6 |
| robe tube, boots, collar, linings, face, eyes | exact | | the tube is the boots' holder in the detached audit |

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`, Highwayman/Lesser Demon copy, sister of `../mm9_honkf_reduce_claude/`)
Scores each collapse over 22 clips at 10 Hz, only removes vertices, texture guard on the body base colour + region mask and on
all three head tiers (100 / 45), seam slides on the hands (`MP_SEAM_GROUPS=1`). Added here: a **chart guard** (`chart_ok`,
`MP_CHART=1`): a collapse is refused when a new face's UV triangle leaves the source primitive's rasterised UV coverage
(2048 px, dilated 2 texels; the same test as `scripts/uv_escape.py`, adapted from the Mummy's). Same count with the guard.
Sets: `scripts/make_sets.py` (male classes from welded pieces, weights and paint; hat seat rule `HATR`), extra keeps
`neck_zone.py`, `paint_edges.py` (RING=0), `honk_contact.py` (body faces under the hands in every clip, medallion excluded),
`extra_keeps.py` (robe tube). LODs: `scripts/build_lods.py` (tools/build_actor_lods.py with floor contact, crown and corpse
contact snapped to the import), the Honk's own `shrink_shadow_lods.py`, `carry_variants.py`.

## Ladder (stop rule for 1.80 m: p99 <= 5.4 mm, max <= 27 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_<label>.png`)
| set | change | LOD0 | p99 / max mm (worst) | IoU / SSIM | result |
|---|---|---:|---|---|---|
| b | hands/hair .6/.65, boots .55, robe .6 | 6,928 | 6.18 / 45.8 (Fidget R sleeve) | .996/.992 | fail |
| d | sleeves own group .8, forearm with hands | 6,852 | 3.83 / 25.9 | .997/.993 | pass; built: jitter Cast L shoulder skin 2.14 FAIL, right boot bind gap 0 -> 3.1 cm, 55 hand faces off the UV charts |
| g | d + chart guard | 6,852 | 4.73 / 25.9 | .997/.993 | pass, 0 off-chart; same jitter/boot findings |
| h-j | shoulder vertices locked / sleeves kept / boots kept + tube kept | 6,954-7,108 | | | lock failed (44 mm); boots must stay whole for the detached audit |
| **l** | tube, boots kept; sleeves .85, medallion .35 (contact released on it), hat seat released | **6,864** | **3.11 / 14.5 (Running)** | **.999/.994** | **PASS, picked** |
| m | l + sleeves .75, medallion front kept | 6,946 | 3.35 / 15.0 | .997/.993 | pass; jitter 2 fails |

## Gates, installed -> l r60 (`scripts/gates.sh`: the Honk male's own gates; `review/gates_before/`, `review/gates_l60/`, `review/gates_compare_l60.txt`)
- Collapse face-frames 41,097 -> 38,694, lower in every clip; single-region worst counts up by one face only at hand_R 2 -> 3
  (AttackRanged, Cast, Hit).
- Robe gate (boots through the robe): identical in every clip. Forearm poke: identical. Detached: identical (both boots flagged
  as installed, by design). Winding 0, bone lengths identical, flat 0.02/0.00 -> 0.00/0.00. Jitter 0 -> 0 fails (shoulder skin
  max 1.38 -> 1.81 mm/f2, limit 2.0 over MM9).
- Arm/hand (`--outer-only --exact`): better in Fidget L (5.4 -> 4.9 cm, 20 -> 17 frames), Hit L, Death R, Fidget2, Cower,
  CowerStart/End; **worse in one field: Hit R forearm in body 2.5 -> 2.9 cm**. Finger stretch p99 rises in every clip
  (e.g. Standing L 1.40 -> 1.92; larger finger triangles), the maxima are unchanged.
- Sleeve see-through: changes of 1 px or 1 frame both ways (CowerEnd L 68 -> 60 px, Hit2 L above34 0 -> 1 px).
- Texture quality: atlas and density unchanged; head-set fragments 4.9 -> 5.7 % (hand islands with fewer faces; texture unchanged).
- LODs (`review/lod_summary_l60.txt`, every frame of every clip): height 1.799 m at every LOD (installed LOD3 1.7905); lowest
  point equal to LOD0 in every clip at every LOD (installed LOD2/3 floated up to +1.5 cm in Dead2); stretched faces equal or fewer.
- Hat seat (`review/hat_seat_l60.txt`, bind): hat-to-head clearance min/median goose hat 8.99/17.69 -> 8.99/17.74 mm, elder hat
  1.50/17.41 -> 2.11/17.41 mm; largest gap increase 2.1 mm. Nothing moves outwards into a hat.
- Viewer `run_creature_review.py check`: 132 switches, 0 failed, no console errors.

## Review
Viewer (installed and reduced, all three tiers, all 22 clips; hats not shown):
http://127.0.0.1:8912/level_generation/creatures/mm9_honkm_reduce_claude/review/viewer/
Sheets read: `review/sheet_face_diff_l60.png` (face front, 3/4, profile, low 3/4, party; every tier: face skin black in the
difference, only hair shading and the medallion differ), `review/sheet_body_l60_b.png` (Standing front/3-4/back, Walking, AttackMelee, Death), `review/sheet_body_d60_a.png`,
`review/sheet_body_d60_c.png` (the first build), `review/close_l60_c.png`, `review/close_d60_a_1.png`, `review/close_d60_a_2.png` (hands, cuffs, belt, back of the
head), `review/crop_medallion_l60_a.png`, `work/crop_l60_f2_a.png`, `work/crop_l60_f4_a.png`, `work/crop_l60_b1.png`,
`review/ladder_sheet_d.png`, `review/paint_head.png`, `review/sets_a_head.png`.
**Look at:** the chest medallion in close-ups (`review/crop_medallion_l60_a.png`: the gold rosette reads slightly different on
the flatter 94-face disc; identical at the standard 3/4 and party views). If that is not acceptable, set `6:1.0` and
`KEEP_EXTRA=...,contact` in `scripts/reproduce.sh`: about 6,986 (-13.1 %). Also the hair at the crown and nape (60 %), fingers
in raised poses.

## Build
`scripts/reproduce.sh` (import, sets, extra keeps, mpqem l r60, build, UV-chart and exact-face checks); gates
`scripts/gates.sh export/mm9_honkm.glb <tag>`, `python3 scripts/gate_compare.py <tag>`; LODs `scripts/blender_queue.sh 0
"<tag>:export/mm9_honkm.glb:lod"`; viewer `scripts/viewer_tiers.py`, `scripts/make_viewer_manifest.py`, `scripts/shots.sh`,
`scripts/close_shots.sh`, `scripts/shot_sheets.py`, `scripts/face_diff_sheet.py`.
Install (on the user's OK only): `check_winding.py export/mm9_honkm.glb` (0), `tools/install_model.py
export/mm9_honkm.glb --world mm9`, the `mm9_actor_models_build_every_binding` regression, and add to
`../mm9_honkmale_claude/README.md`: "LOD0 reduced post-install on <date> by `mm9_honkm_reduce_claude`; a rebuild from this
project must re-run that reduction". Rollback: `before/mm9_honkm.glb`.

## Not checked
In game; motion at normal speed (frames, gates and viewer stills only); LOD1-3 and shadow meshes by eye (numbers only); hats in
the viewer (clearance by numbers at bind only, not per clip); close shots of tier B after the final build (its face and body
sheets only); body sheets of tiers A and C of the final build were made (`review/sheet_body_l60_{a,c}.png`) but read only on the first build; the boots in close-up (hidden under the robe; the close shot aimed at the right foot shows only the robe).

## MM9 sockets (2026-11-10)

The installed model carries MM9's attach points as `Socket_<name>` nodes for held items (scene `held_items`, MM9's AttachProp), added after this project's install by [`mm9_held_items_claude/scripts/add_sockets.py`](../../props/mm9_held_items_claude/scripts/add_sockets.py) (`Socket_pamphlet`). A rebuild installed from here drops them: run that script again and install its export (`tools/install_model.py --world mm9`).
