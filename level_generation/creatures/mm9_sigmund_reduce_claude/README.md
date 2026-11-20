# MM9 Sigmund the Stressed (`mm9_sigmund`, unique NPC) reduction: candidate d r75 ready for review (2026-11-05)

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) and
[REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (relaxed keep set, face exact; prio-3
unique reduced on the user's 2026-11-05 "do all"), ledger row 27 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease
`mm9reduce:sigmund` (owner sigmund-reduce-20261105); the creature's own `mm9:sigmund` lease was free. Source: the installed
`assets_source/worlds/mm9/models/mm9_sigmund.glb` (sha256 4846e11dce17, = `../mm9_sigmund_claude/export/mm9_sig.glb`), copied to
`before/` (the rollback source). No Meshy, no credits, no repaint. **Not installed.** `../mm9_sigmund_claude/` was only read (its
masters `work/geo_v3.blend` and `work/linings_v1.blend` opened read-only for labels; its gate scripts run in place).

| | LOD0 | body prim `Sigmund` (hauberk, collar, belt, arms, trousers, boots, rim linings) | head prim `SigmundHead` (face + hair shell, eyes, hair twin, MPFB hands) | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|
| installed | 13,236 | 6,834 | 6,402 | 6,618 | 2,380 | 789 |
| **d r75 (`export/mm9_sigmund.glb`, sha256 e92db6bc73b0)** | **10,876 (-17.8 %)** | 5,684 | 5,192 | 5,438 | 1,956 | 647 |

Every vertex of the candidate is an installed vertex (positions, normals, UVs, joints, weights are the installed bytes; only index
buffers changed). Clips (15), skin, nodes, materials (specular 0 extras), all 6 images: identical (`same_clips.py`). Shadow meshes
rebuilt by the creature's own `shrink_shadow_lods.py` (one-texel linings dropped), LOD slivers by its `drop_lod_slivers.py`.

## Measured first: what is cuttable
Labels from the creature's masters (`scripts/dump_master_parts.py`: `head`/`hand` face attributes; `added` = faces of
`linings_v1.blend` not in `geo_v3.blend`, i.e. everything `linings_sig.sh` added), matched to the GLB by rest centroid through
`mirror_glb.py`'s x flip (`scripts/glb_parts_sig.py`, 6e-8 m). The linings are 35 % of LOD0: 2,304 rim-lining faces (3 mm / 0.5 mm
reversed copies of the cloth bands), 554 rim strips and the 1,746-face hair twin (1.5 mm), each lining face paired with the outer face
it copies. rim_lining.py lines every band once with its own dark texel, so where two bands meet an outer vertex has two twins:
twins are kept per (lining band, outer vertex) and band-border vertices are locked (the first build, b60, re-emitted 15 lining faces
that mixed two bands' texels and failed the UV audit).

## Kept exactly (`scripts/make_sets_sig.py c`, `RIM=0`; 29.7 % of LOD0 + their linings = 38.6 %)
Checked face by face against the installed file (`scripts/kept_check.py export/mm9_sigmund.glb c`: 0 missing): skin 1,762 (every
head-shell UV island that is skin by paint, whole: the face chart with eyes, brows, mouth and forehead, both ears, neck and nape, plus
painted skin grown 3 rings into the hair islands), hairline 169 (hair within 12 mm of skin), gold collar and neck seam 721 (gold paint
above 1.30 m and its ring, body within 12 mm of the head shell), belt with buckle and studs 326, soles 140, fingertips 80 (distal
segment within 6 mm of each tip), hand-graft junction 123 (Forearm-dominated hand faces), small pieces 52, rim strips 560.
Cut (pose-aware half-edge collapse): hauberk/torso cloth at the ladder ratio 0.75, hands 0.65 with seam slides (every finger kept),
hair shell 0.7 with its twin re-emitted, boots 0.75, arm skin + bracers 0.75, trousers 0.7; every cut band's lining re-emitted from
the installed twins (body 2,304 -> 1,874, hair twin 1,746 -> 1,350).

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`, PeasantM2d's copy)
Scored over 422 poses (every clip at 10 Hz) + position/UV rest quadric; texture guard over each primitive's base colour (one skin, no
tiers; `scripts/tex_extract.py`), Mummy chart guard `MP_CHART=1`, the audit's own chart test per collapse `MP_AUDIT=1`, texture weight
`MP_W5=4`. Sigmund changes: per-band lining twins (`twinb*`, `band` in the sets) and `lockpos` (ambiguous and band-border vertices).

## Ladders (limits for 1.74 m: p99 <= 5.22 mm, max <= 26.1 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_{a,b,d}.png`)
| ladder | groups (hands, hair, boots, arms, trousers) | step (torso) | LOD0 | p99 / max mm (worst) | result |
|---|---|---|---:|---|---|
| a | .65 .7 .6 .6 .55 | r60 / r50 | 10,346 / 10,346 | 7.07 / 25.5 (Sc2_Sigmund1c) | fail (calves, thighs, forearms; torso saturates at 485) |
| b (= c) | .65 .7 .75 .75 .7 | r60 | 10,764 | 4.36 / 25.5 | pass. b60: 15 LOD0 UV-audit faces (mixed lining texels) -> c60 with per-band twins: audit 0, but the torso's last collapses (28.7 mm rms) flattened the hauberk's front hem: arm/hand gate L hand 0 -> 6.0 cm in 99 Standing frames (hand inside the flattened hem), StaticDie both hands 5.9 / 5.3 cm (`review/close_c60_*.png`) |
| **d** | same | **r75** / r70 / r65 | **10,876** / 10,830 / 10,786 | **3.33 / 16.7 (Death:12)**, IoU .9942, SSIM .9955 / 3.57 / 19.0 / 4.03 / 19.0 | all pass; **r75 picked**: `scripts/hand_probe.py` L hand > 1 cm below the hem faces 5 vertices (= installed, a bracer face) at r75, 51 at r70, 190 at r65 |

## Gates, installed -> d r75 (Sigmund's own scripts via `scripts/gates.sh`; `review/gates_before/`, `review/gates_d75/`)
- **UV audit** (`claude_shared/reduction_uv_audit.py`, `review/uv_audit_d75.json`): **LOD0 0 escaping faces** in Sigmund and
  SigmundHead. LOD1-3 (the builder's decimate): body 91 / 117 / 46 (installed 77 / 110 / 40), head 90 / 121 / 61 (90 / 116 / 89).
- Arm/hand (`--outer-only`, the creature's setting): 0 frames over 1 cm in every clip for both hands (as installed); maxima equal
  (Applause 0.9 / 0.9 cm) except Sc2_Sigmund1b L 0.0 -> 0.3 cm; finger stretch p99 maxima equal or lower.
- Jitter (vs `../mm9_sigmund_claude/work/mm9_sig_clips.glb`): **0 fails = 0**. Shoulder-skin excess rises on a thinner vertex sample
  (AttackMelee R 0.36 -> 1.80, Death L 0.90 -> 1.64, Hit R 0.0 -> 0.85 mm/f2; fail line 2.0).
- Sleeve poke: 0 mm in every clip (as installed). Collapse face-frames lower in 13 of 15 clips (Agree 18,508 -> 14,740), Hit 401 -> 412,
  Standing/StaticDie equal; exposed body faces Death 19 -> 33.
- Detached: 2 -> 0 detached (the boot shells now read "concealed", gap 1.1 cm, hidden from every direction); root lifts equal.
- Flat 0.00, winding 0, bones 12 checked 0 stretching, texture quality body stretch p90 1.07 = 1.07, head 1.20 = 1.20 (head
  fragments 1.5 -> 2.2 %: the cut hair islands).
- See-through (`scripts/see_through.sh`, the creature's gate, all 15 clips every 3rd frame, 16 views; hole max px / frames with holes):
  boot L 2 -> 2 px (frames 43 -> 40), boot R 1 -> 1 (21 -> 19), head 10 -> 10 (Death 24, under the hair; 143 -> 139), sleeve L
  1 -> 1, sleeve R 2 -> 2 (19 -> 18), torso 3 -> 2 (4 -> 5 frames), collar / trousers 0 = 0; one new 1-px unattributed hole in one
  Death frame (`python3 scripts/st_summary.py review/gates_before/see_through.json review/gates_d75/see_through.json`).
- LODs (`scripts/lod_check.py`, every frame of every clip; `scripts/lod_summary.py inst d75`, `work/lod_summary_d75.txt`), built by
  `scripts/build_lods.py` (0.5 / 0.18 / 0.06, 4 influences; soles, hair crown and the corpse contact at the end of Death, StaticDie
  and in Dead protected, each point snapped to the imported vertex: 87 of 87): height 1.7437 m at every LOD (installed LOD3 1.7468), 0 stretched faces at every LOD; every clip's lowest
  point at LOD1-3 equal to LOD0 (installed LOD3 sank 5.7 mm in Death and 5.2 mm in Dead, LOD2 floated 3.3 mm in Dead).

## Review
Viewer (installed and reduced, all 15 clips; `run_creature_review.py check`: 30 switches, 0 failed, no console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_sigmund_reduce_claude/review/viewer/
Sheets read at full size: `review/sheet_face_d75.png` (front close-up, 3/4, true profile, low 3/4, party) and
`review/sheet_face_diff_d75.png` (face, ears, collar black; the back hair shell and the mail shoulders differ in shading),
`review/sheet_body_d75.png` (Standing front/3-4/back, Walking, Applause, Death), `review/close_d75_hands.png` (both hands outside and
front), `review/close_d75_torso.png` (hauberk front hem, gold collar and medallion, collar from behind, belt + buckle),
`review/close_d75_legs.png` (both bracers, boot lacing front and back), `review/close_d75_motion.png` (hair from behind above, Running,
Applause hands), the c60 set (`review/close_c60_*.png`, the rejected flat hem) and `review/classes_a/sheet.png` (keep classes).
Look at: the hair shell from behind and in profile (0.7, hairline exact), the fingertips (hands 0.65), the boot tops (0.75).

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_sigmund_reduce_claude/before/mm9_sigmund.glb REA_NODE=Sigmund $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $BL -P scripts/dump_master_parts.py; $G scripts/glb_parts_sig.py; $G scripts/tex_extract.py
RIM=0 $G scripts/make_sets_sig.py c
MP_AUDIT=1 MP_CHART=1 MP_W5=4 MP_SEAM_GROUPS=1 SETS=c MP_GROUPS=1:0.65,2:0.7,3:0.75,4:0.75,5:0.7 scripts/run_mp.sh d 0.75,0.7,0.65
scripts/build_mp.sh mp_d_r75 export/mm9_sigmund.glb   # swap_mp -> build_lods (protected, snapped) -> shrink_shadow_lods -> drop_lod_slivers
$G ../claude_shared/reduction_uv_audit.py export/mm9_sigmund.glb before/mm9_sigmund.glb --json review/uv_audit_d75.json
$G scripts/kept_check.py export/mm9_sigmund.glb c; scripts/gates.sh export/mm9_sigmund.glb d75; scripts/see_through.sh export/mm9_sigmund.glb d75
REA_NODE=Sigmund $BL -P scripts/lod_check.py -- $PWD/export/mm9_sigmund.glb d75; python3 scripts/lod_summary.py inst d75
python3 scripts/make_viewer_manifest.py d75 inst=Installed=before/mm9_sigmund.glb red=Reduced_d75=export/mm9_sigmund.glb
scripts/shots.sh; scripts/close_shots.sh; $G scripts/shot_sheets.py d75; $G scripts/face_diff_sheet.py d75
```
Other files: `export/mm9_sigmund_b60.glb` (UV audit 15) and `export/mm9_sigmund_c60.glb` (flat hem) are rejected intermediates.

Install (orchestrator, on the OK): `check_winding.py export/mm9_sigmund.glb` (0), `tools/install_model.py export/mm9_sigmund.glb --world mm9`,
the `mm9_actor_models_build_every_binding` regression, and add to `../mm9_sigmund_claude/README.md`: "LOD0 reduced post-install on
<date> by `mm9_sigmund_reduce_claude`; a rebuild from this project must re-run that reduction". Rollback: `before/mm9_sigmund.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (gates and viewer stills
only); LOD1-3 and shadow meshes by eye (numbers only); the eye/mouth close-ups at the user's zoom (the face triangles are the installed
ones and the five-view face diff is black there); the seated cutscene clips (Sit, Agree, Sc2_*) only through the gates and the
Applause stills.
