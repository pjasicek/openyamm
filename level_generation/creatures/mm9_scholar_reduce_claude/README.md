# MM9 Bembridge Scholars (`mm9_scholar`, tiers sc_a / sc_b) LOD0 reduction (2026-11-05)

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) and
[REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md); ledger row 19 of "MM9 reduction"
in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md) (prio 3 unique; user 2026-11-05 "do all": uniques reduced too, faces exact).
Lease `mm9reduce:scholar` (scholar-reduce-20261105); the creature's own `mm9:scholar` lease was free. No Meshy, no credits.
**Status: candidate b r55 ready for review, not installed.** The creature project `../mm9_scholar_claude/` was only read.

Source: the installed `assets_source/worlds/mm9/models/mm9_scholar.glb` (r22, sha256 176c7de25696, = the creature's
`export/mm9_scholar.glb`), copied to `before/mm9_scholar.glb` (the rollback source). Candidate: `export/mm9_scholar.glb`
(= `work/cand_b55.glb`, sha256 1bd81f870a73). Fallback with more error margin: `work/cand_b58.glb` (10,908).

| | LOD0 | Scholar_A (body) | ScholarHead | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|
| installed | 13,782 | 8,054 | 5,728 | 6,882 | 2,462 | 806 |
| **b r55** | **10,794 (-21.7 %)** | 5,640 | 5,154 | 5,387 | 1,925 | 627 |

## Route
The pose-aware half-edge collapse (`scripts/mpqem.py`, a copy of the Wyrdes' 2026-11-05 copy: the Scholar's linings are
`linings_wy.py`'s too) on the installed GLB's own vertices: every output corner is an installed vertex, so positions, UVs,
normals, joints and weights are the installed bytes; only index buffers change. Each collapse is scored over 136 poses (every clip
at 10 Hz) plus a 5-D position/UV quadric (texture weight `MP_W5=4`), and refused when it flips a face at rest or in any pose,
when its UV triangle leaves the source charts (chart guard `MP_CHART=1`) or fails the UV audit's own chart test (`MP_AUDIT=1`:
`reduction_uv_audit.Charts.test`, zero tolerance), or when its new faces sample colours the source lacks there in any tier
(texture guard on both tiers' ramped body colours, the region mask and both tier head images, `tex_extract.py`).
Linings (693 twins + 112 rim faces: 147 on the robe, 540 on the hair/beard shell, 6 head) are cut with their outer cloth: the
lined faces are collapsed in their own groups and the lining re-emitted as the reversed twins of the surviving lined faces
(same UVs, weights, 2 mm offset vertices); rim strips kept.

Sets (`scripts/glb_parts.py` labels from `../mm9_scholar_claude/work/uv_tex.npz`, matched exactly; `scripts/make_sets_sc.py a`
with `HANDC=work/handc_02.npy` from `scripts/hand_contact_sc.py`):
- **Exact:** the whole head part (face shell, lips, ears, eyes, neck: 3,254 faces); the hairline and beard edge (outer hair-shell
  faces on its open boundary + 1 ring, and hair within 12 mm of the face shell: 446); collar (body within 1 cm of the head part);
  forearm stubs; sleeve ends within 2 cm of a hand; the jewellery (chain beads, medallion, buckle: 699) and cloth within 6 mm of it;
  region-mask border faces of the robe (795); robe under the resting hands in any frame (164, mirrored); soles; small pieces; rim
  strips. Protected 6,114 of 13,782 (44 %).
- **Own ratios:** hands 0.6 (MPFB, every finger kept), hair/beard 0.65 (unlined and lined), cap 0.7, shoes 0.7, hidden shins 0.5,
  lined robe 0.6 (stops at 100 of 110).
- **Robe** (3,794 free faces): the ladder ratio.

## Ladders (limits for 1.89 m: p99 <= 5.67 mm, max <= 28.35 mm, IoU >= 0.98, SSIM >= 0.93)
| ladder | groups | step | LOD0 | p99 / max mm (worst) | IoU / SSIM | |
|---|---|---|---:|---|---|---|
| a | hands 0.65, hair 0.7, cap 0.75 | r60 / r50 / r45 | 11,138 / 10,758 / 10,722 | 4.04/15.3, 8.45/35.6 (Walking), 11.2/62.7 | .994/.997 at r60 | r60 pass, r50 r45 fail |
| **b** | hands 0.6, hair 0.65, cap 0.7 | r58 / **r55** / r52 | 10,908 / **10,794** / 10,680 | 4.54/16.4, **5.27/25.0 (Cower:0)**, 6.63/28.3 | **.992 / .996** | r58 pass, **r55 pass, picked (lowest passing)**, r52 fail |

Two ladders; the robe stops near 0.5 (below it the lower robe misses by 35-60 mm in Walking and Running), so a third would not
move the result.

## Checks
- **UV audit** (`review/uv_audit_b55.json`): **LOD0 0 escaping faces** in Scholar_A and ScholarHead. LOD1-3 (Blender decimate as
  installed) Scholar_A 211/156/78, ScholarHead 35/72/53 against the installed LODs' own 146/171/118 and 30/64/54.
- **Face exact** (`scripts/face_exact.py`): all 3,254 head-part faces and all 6,114 kept faces are present byte for byte.
- `same_clips.py`: clips, skin, nodes, materials, variants and images identical to the installed file, so jitter and bone
  lengths are unchanged (bone length re-run: the same two Calf entries).

Gates, installed -> b r55 (`scripts/gates.sh`, the creature's own scripts; `review/gates_before/`, `review/gates_b55/`):

| gate | installed | b r55 |
|---|---|---|
| robe (legs through robe) | 0 except Death 2/32 2.4 cm | 0 except Death 2/32 2.3 cm |
| arm/hand `--outer-only --exact` | 0 frames > 1 cm except Fidget L 24 f 5.5 cm (forearm 5.7) | 0 except **Fidget L 27 f 5.4 cm** (forearm 1.6); the known lining-twin artefact of the creature README (the hand rests on the stole; viewer Fidget 0.6/1.02/1.5 s identical, `review/close_a_fidget_hand_b55.png`). Finger stretch max equal or lower everywhere |
| sleeve poke | 0 except Death L 22.2 mm, 1 v, 2 f | identical |
| lining gate (lining outside its cloth) | max 5.16 mm Cower prim 0, 5.80 prim 1 | 5.16 prim 0, 1.93 prim 1; frames equal or fewer |
| collapse face-frames | Standing 907 .. Dead 24,242 | lower in every clip (Standing 384, Fidget 855, Death 15,112, Dead 19,313) |
| detached parts | concealed XhalfHead 2 tris; root lifts hair/head as installed | the same + a concealed 12-tri Spine3 piece 5 mm in 3 Cower poses (hidden from every direction) |
| see-through (`scripts/see_through.sh`) | torso 132/77 Death, head 115 Death, sleeves L 14 / R 13 px (42 / 38 frames) | torso 132/77, head 115 (equal); sleeves L 12 / R 13 px (48 / 53 frames: a few 3 mm px more often at the cuff openings, R Death 5 -> 10 px in 3 frames, R Dead 1 px); collar 1 px in one Fidget frame (`review/gates_b55/see_through_sleeveR_Death_6_az270_el00.png`) |
| winding / flat | 0 / 0.00, 0.07 | 0 / 0.00, 0.08 |
| texture quality body / head | 64.0 %, stretch p90 1.10 / 60.5 %, 1.12 | 64.0 %, 1.12 / 60.5 %, 1.13 |
| LODs (`scripts/build_lods.py`, soles, cap top and corpse contact protected, snapped) | | every LOD 1.890 m (installed LOD3 1.880); lowest point per clip equal at LOD0/1, LOD2 within 0.5 cm, LOD3 Death -0.62 / Running -0.56 cm below its LOD0 (installed LOD3 AttackMelee +0.53, Walking +0.44); stretched faces LOD0 3 = 3, LOD1 2 -> 1 (`work/lod_check_{inst,b55}.json`, `scripts/lod_summary.py inst b55`) |

## Review
- Viewer (installed and b r55, both tiers, all 9 clips): http://127.0.0.1:8912/level_generation/creatures/mm9_scholar_reduce_claude/review/viewer/
  (`run_creature_review.py check`: 36 switches, 0 failed, 0 console errors).
- Sheets read at full size: `review/sheet_face_b55.png` (front close-up, 3/4, profile, low 3/4, party; both tiers),
  `review/sheet_face_diff_b55.png` (face skin black in every view; differences only on hair/beard shading and the cap),
  `review/face_pair_{a,b}_{f0,f1}_b55.png`, `review/sheet_body_b55_{a,b}.png` (Standing front/3-4/back, Walking, Fidget, Death),
  `review/close_{a,b}_hands_stole_b55.png` (both hands, stole + medallion, stole chain), `review/close_{a,b}_cuffs_hem_cap_b55.png`,
  `review/close_{a,b}_robe_b55.png` (robe front/back, Running, feet and hem, hair from behind, Hit), `review/close_a_fidget_hand_b55.png`,
  `review/ladder_sheet_{a,b}.png`. Seen: the 0.6 hands are a little more faceted at the knuckles in close-up; nothing else visible.

## Build
`REA_GLB=.../before/mm9_scholar.glb REA_NODE=Scholar` `import_source.py` + `dump_mesh.py` (Blender) -> `glb_parts.py` ->
`tex_extract.py` -> `hand_contact_sc.py work/handc_02.npy` -> `HANDC=work/handc_02.npy make_sets_sc.py a` ->
`SETS=a MP_GROUPS=1:0.6,2:0.65,3:0.65,4:0.6,5:0.7,6:0.7,7:0.5 scripts/run_mp.sh b 0.58,0.55,0.52` ->
`scripts/build_mp.sh mp_b_r55 work/cand_b55.glb` (swap_mp -> build_lods -> skeleton warrior's shrink_shadow_lods -> carry_variants
-> the Scholar's fix_winding -> check_winding) -> `reduction_uv_audit.py` -> `face_exact.py` -> `gates.sh` / `see_through.sh` ->
`viewer_tiers.py`, `make_viewer_manifest.py`, `shots.sh`, `close_shots.sh`, `shot_sheets.py`, `face_diff_sheet.py`, `close_sheet.py`.

## Install (not run; on the orchestrator's / user's OK)
`check_winding.py export/mm9_scholar.glb` (0), `tools/install_model.py export/mm9_scholar.glb --world mm9`, the binding regression,
`floor_audit.py --world mm9` rows 274/275, and in `../mm9_scholar_claude/README.md`: "LOD0 reduced post-install on <date> by
`mm9_scholar_reduce_claude`; a rebuild from this project must re-run that reduction". Rollback: `before/mm9_scholar.glb`.

## Not checked
In game; motion at normal speed by eye (frames, gates and viewer stills only); LOD1-3 close up by eye (numbers only); the
binding regression and floor audit (after install).
