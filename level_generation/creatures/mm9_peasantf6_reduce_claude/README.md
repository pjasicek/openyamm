# MM9 PeasantF6 (`mm9_peasantf6`, the elf townswoman with a braid) reduction: candidate f r62 ready for review (2026-11-04)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-2 townsfolk: the
relaxed prio-1 keep set, face exact), ledger row 12 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:peasantf6`
(owner peasantf6-reduce-20261104); the creature's own `mm9:peasantf6` lease was free. Source: the installed
`assets_source/worlds/mm9/models/mm9_peasantf6.glb` (sha256 cd1219701140, identical to `../mm9_peasantf6_claude/export/`), copied
to `before/` (the rollback source). No Meshy, no credits, no repaint. **Not installed.** `../mm9_peasantf6_claude/` was only read.
Starting point: `../mm9_peasantf3_reduce_claude/scripts/` (copied and renamed; PeasantF6 is PeasantF5's body + new hair, braid, ears).

| | LOD0 | head (face, neck, scalp, eyes, teeth) | ears | hair | braid | dress | skirt | lining | legs | arms | hands | bracelets | buckle | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| installed | 14,620 | 4,130 | 588 | 900 | 800 | 2,334 | 924 | 990 | 640 | 940 | 1,500 | 768 | 106 | 7,278 | 2,619 | 872 |
| **f r62 (`export/mm9_peasantf6.glb`, sha256 395702565681)** | **12,022 (-17.8 %)** | 4,130 | 588 | 704 | 504 | 1,748 | 710 | 990 | 526 | 610 | 944 | 460 | 106 | 5,979 | 2,152 | 810 |

Every vertex of the candidate is an installed vertex (positions, normals, UVs, joints, weights are the installed bytes; only index
buffers changed). Clips (11), skin, nodes, materials, region ramps/mask, `KHR_materials_variants`, all 8 images: byte-identical
(`same_clips.py`). Head part and both ears: every installed triangle present exactly (4,130/4,130 and 588/588 by position + UV + normal),
so the face renders pixel-identical in both tiers (`review/sheet_face_diff_f62.png`: face black in all five views of pf6_a and pf6_b;
only the hair crown shading, the braid, the shoulders and the bodice below the neckline differ).

## Measured first: protected share
Part labels from the creature's last pre-GLB mesh (`../mm9_peasantf6_claude/work/uv_lined.npz`, 14,620 faces = LOD0;
`scripts/glb_parts.py`, the head primitive by welded connected component because the braid moved up to 9 mm after that file).
Head + ears + buckle + skirt lining + all other lining/rim faces = 6,252 (43 %) are kept by rule; the final set f keeps 7,761 (53 %).

Keep set (`scripts/make_sets_pf6.py`, set f = `ARMC=1 HEM=0.1 WAIST=0.03 STUB=0.02 BRACELET=cut`): the whole head part (face skin, neck
seam, scalp, eyes, teeth, mouth backing), both elf ears, the buckle, the skirt lining (F5's, 4 mm inside, not a twin of the skirt) and
every other `inner` face (collar-band lining, rim strips of the arm tops and hand stubs); the collar band's 278 lined outer dress faces;
hair within 3.5 mm of the skull (tucked lower edge + rim strip), within 1 cm of an ear and 1.5 cm of the braid; the braid root (1 cm of
the hair); dress within 1 cm of the head (collar), 1.2 cm of an arm (sleeve ends), 2.5 cm of the braid; soles; pieces up to 40 faces;
the hand's forearm stub and the painted forearm sleeve within 2 cm of it (set d); the skirt's hem band (lowest 10 cm) and waist band
(top 3 cm) (set e); dress/skirt faces within 1.5 cm of an arm/hand/bracelet vertex in any clip at 10 Hz (`scripts/arm_contact.py`, set f).
Groups: hands + fingers 0.6 (seam slides; every finger kept), arm skin 0.45, hair 0.7, skirt 0.7, shoes 0.7, hidden calves 0.85,
braid 0.6, bracelets 0.6, dress at the ladder ratio.

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`, F3's copy)
Texture guard over each tier's baked body colour (tone x region ramps), each tier's head image and the region mask
(`scripts/tex_extract.py`; refuse > 100 any sample / > 45 mean), the Mummy's chart guard (`MP_CHART=1`, 12 samples), texture weight 4
(`MP_W5`), seam slides on the hands. Scored over 291 poses (every clip at 10 Hz) plus a position+UV rest quadric.

## Ladders (limits for 1.774 m: p99 <= 5.32 mm, max <= 26.6 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_<label>.png`)
| ladder | set / change | step | LOD0 | p99 / max mm (worst) | result |
|---|---|---|---:|---|---|
| a | a: first set, bracelets kept, collar band free | r55 / r45 | 11,818 / 11,800 | 5.41/29.6 (Conv1, puff-sleeve tops), 6.41/34.5 | fail |
| c | b (collar band kept) + bracelets 0.6 | r70 / r65 / r60 | 11,842 / 11,760 / 11,678 | 3.43/16.7, 3.74/16.7, 4.18/18.5 | pass; c60 built: 2 hand-stub vertices per side came through the cut sleeve at rest (dark wedges above both cuffs in `review/crop_cuffs_c60_a.png`), skirt lining 23 mm out of the skirt hem in Running (installed 4.1), R thumb flagged 5.2 cm in Walking (artifact, below) |
| d | c + wrist (stub and sleeve over it) | r60 / r55 | 11,886 / 11,804 | (not laddered, superseded) | stub covered at rest again (`work/d60_skin_poke.json`) |
| e | d + skirt hem/waist bands | r61 / r55 | 11,952 / 11,854 | 3.34/16.7, 4.83/29.6 | pass / fail; e61 built: lining max equal to installed except Death 5.5 -> 6.1 mm, Cower R forearm 1.0 -> 1.4 cm into the chest at frame 0 |
| **f** | **e + arm-contact cloth** | **r62** / r58 | **12,022** / 11,962 | **3.38 / 16.7 (Hit:39)**, 4.02/25.4 (Dead:0, L puff sleeve) | **PASS, picked** (IoU .998, SSIM .9956) / pass, not picked (25 mm on the puff sleeve in the corpse, near the limit, for 60 triangles) |

## Gates, installed -> f r62 (PeasantF6's own scripts, `scripts/gates.sh`; `review/gates_before/`, `review/gates_f62/`)
- **UV chart audit** (`../claude_shared/reduction_uv_audit.py`, `review/uv_audit.json`): **LOD0 0 escaping faces in both nodes**.
  LODs (Blender decimate): body 180 / 137 / 22 at LOD1-3 (installed 123 / 197 / 79), head 20 / 59 / 37 (installed 20 / 56 / 32).
  `scripts/uv_escape.py`: 11 body faces flagged, the same 11 as in the installed file (zero-area centre-seam slivers), 0 new.
- Collapse face-frames lower in every clip (total 21,115 -> 16,970; Cower 2,294 -> 1,295, Conv3 3,567 -> 2,516).
- Robe (legs through skirt): 0 in every clip, both. Skin poke (`skin_poke_gate.py --mirrored`, stub and sleeve): 0.0 mm every clip, both;
  every installed covered candidate still covered at rest (`scripts/skin_poke_rest.py`, 46/46 stub per side; sleeve 31 -> 30 = one
  removed vertex).
- Arm/hand (`--outer-only --exact`, 48 fps): hand 0 frames > 1 cm in every clip, both; Cower forearm L 0.4 -> 0.0, R 1.0 -> 0.0 cm
  (better); finger stretch maxima equal. **One flag:** Conv3 L forearm 6.0 cm @ frame 187 (installed 0.2). It is a measurement artifact:
  that forearm vertex (0.247, 1.016, -0.024) is 5.6 cm (installed) / 6.0 cm (f62) **outside** the skirt (nearest cloth face, lining
  included, on its outer side; a +x ray from it hits nothing in both; `scripts/point_probe.py`); the gate's 6 cm cap picked a tied
  edge face with the opposite normal. Same kind for the Walking R thumb 5.2 cm in c60/e61 (5.5 cm outside the skirt).
- Skirt lining through the skirt (`scripts/lining_gate.py`, 10 fps): largest outward distance equal in every clip except Death
  5.47 -> 6.13 mm and Dead 2.32 -> 2.81 mm; lining vertices > 0.5 mm out in the worst frame up (Walking and Running 8 -> 23, Talk/Conv1 6-8 -> 12, Death 65 -> 85; the
  skirt's middle rows are cut while the lining is kept), frames with any vertex out equal in every clip.
  Hit 76.8 mm in both (the installed construction).
- Jitter vs `../mm9_peasantf6_claude/work/ref_half.glb`: 2 fails both (Death shoulder skin 35.9 mm/f2, the installed model's own).
- Detached parts: 21 components and the same 7 detached parts with the same worst distances (feet inside the skirt, forearm lifts
  1.8 cm); the audit's root cluster changed name (xbk3 -> FHP Spine1, body piece 1,914 -> 1,702 tris), so the L forearm moved from
  "shallow" to a "root lift" line; its vertices are installed vertices. Flat shading 0.00 / 0.03 both. Winding 0. Bone lengths 14, 0
  stretching. Texture quality: unchanged (body stretch p90 1.05 -> 1.06, head 1.15 -> 1.16).
- See-through (`scripts/see_through.sh`, every clip, 16 views; hole max px per zone, installed / f62): every zone's maximum equal (torso 57/57 Death from the feet up the open skirt, the installed construction; sleeve L 25/25, sleeve R 27/27, collar 10/10, head 2/2, boots 0/0); per-clip rises of 1-3 px in single clips (torso Walking 12 -> 15, Fidget and Conv3 12 -> 14 px; collar Conv3 2 -> 3; sleeve L Dead 9 -> 10) and equal falls elsewhere (`scripts/see_summary.py`).
- LODs (`scripts/lod_check.py`, every frame of every clip; `work/lod_check_{installed,f62}.json`), built by `scripts/build_lods.py` (tool
  defaults 0.5/0.18/0.06, 4 influences; soles, crown and corpse contact within LIE 3 cm protected, each point snapped to the imported
  vertex; a point shared by coincident vertices with other weights is dropped, the tool refuses it): height 1.770 m at every LOD
  (installed LOD3 1.767); every clip's lowest point at LOD1-3 equal to LOD0 (installed LOD2/3 differed by up to 0.5 cm, Running LOD3
  +0.54 cm); 0 stretched faces. With LIE 1 cm (e61) LOD3 sank 1.5-1.7 cm in Dead/Death.

## Review
Viewer (installed and reduced, both tiers, all 11 clips; `run_creature_review.py check`: 44 switches, 0 failed, no console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_peasantf6_reduce_claude/review/viewer/
Sheets read: `review/sheet_face_f62.png` (front close-up, 3/4, true profile, low 3/4, party; both tiers), `review/sheet_face_diff_f62.png`,
`review/sheet_body_f62_{a,b}.png` (Standing front/3-4/back, Walking, Talk, Death), `review/close_f62_{a,b}_hands.png` (L/R hand
outside, R hand front), `review/close_f62_{a,b}_1.png` (arms, skirt front/back, Running skirt, cuffs), `review/close_f62_a_2.png` (feet,
Talk arms, braid from behind, Hit, hair from behind above), `review/crop_hair_f62.png` (crown at full size), `review/crop_chest_f62.png`
(bodice, lacing and painted necklace at 2x), `review/crop_cuffs_c60_a.png` (the c60 cuff wedges that set d fixed).
Look at: the fingertips in close-up (hands at 0.6: slightly more angular tips), the puff sleeves (a little smoother shading of the folds),
the braid lobes (0.6), the lining at the skirt hem in Running/Death.

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_peasantf6_reduce_claude/before/mm9_peasantf6.glb REA_NODE=PeasantF6 $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/glb_parts.py; $G scripts/tex_extract.py; $G scripts/arm_contact.py 0.015 10
ARMC=1 HEM=0.1 WAIST=0.03 STUB=0.02 BRACELET=cut $G scripts/make_sets_pf6.py f
MP_TEX_MAX=100 MP_TEX_MEAN=45 MP_CHART=1 MP_W5=4 MP_SEAM_GROUPS=1 SETS=f MP_GROUPS=1:0.6,2:0.7,3:0.7,4:0.7,5:0.45,7:0.85,8:0.6,9:0.6 \
  scripts/cap.sh $G scripts/mpqem.py before/mm9_peasantf6.glb 0.62,0.58          # ladder: work/queue_f.sh (reduce_ladder + compare)
LIE=0.03 scripts/build_mp.sh mp_f_r62 export/mm9_peasantf6.glb   # swap_mp -> build_lods (protected, snapped) -> shrink_shadow_lods -> carry_variants -> fix_winding
$G ../claude_shared/reduction_uv_audit.py export/mm9_peasantf6.glb before/mm9_peasantf6.glb --json review/uv_audit.json
scripts/gates.sh export/mm9_peasantf6.glb f62; REA_NODE=PeasantF6 $BL -P scripts/lod_check.py -- $PWD/export/mm9_peasantf6.glb f62
scripts/see_through.sh export/mm9_peasantf6.glb f62; python3 scripts/see_summary.py review/gates_before/see_through.json review/gates_f62/see_through.json
$G scripts/viewer_tiers.py export/mm9_peasantf6.glb red   # installed: viewer_tiers.py before/mm9_peasantf6.glb inst
$G scripts/make_viewer_manifest.py f62 inst_a=..=work/viewer_inst_th_a.glb red_a=..=work/viewer_red_th_a.glb inst_b=.. red_b=..
scripts/shots.sh; scripts/close_shots.sh; $G scripts/shot_sheets.py f62; $G scripts/face_diff_sheet.py f62; $G scripts/close_sheet.py f62 a c8,c9,c10 review/close_f62_a_hands.png 420
```
Install (orchestrator, on the OK): `check_winding.py export/mm9_peasantf6.glb` (0), `tools/install_model.py export/mm9_peasantf6.glb
--world mm9`, the `mm9_actor_models_build_every_binding` regression, and add to `../mm9_peasantf6_claude/README.md`: "LOD0 reduced
post-install on <date> by `mm9_peasantf6_reduce_claude`; a rebuild from this project must re-run that reduction". Rollback:
`before/mm9_peasantf6.glb`. PeasantF5 (ledger row 30) shares this body: its reduction can reuse this keep set (F5 has no hair shell,
braid or elf ears, and has the coif and brooches).

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (frames, gates and
viewer stills only); LOD1-3 and shadow meshes by eye (numbers only); the eye/mouth close-ups at the user's zoom (the face triangles
are the installed ones, and the five-view face diff is black); see-through was not run on the intermediate c60/e61 candidates.
