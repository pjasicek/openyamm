# Kira the Cold (`mm9_kira.glb`) reduction: candidate c2 r45 ready for review (2026-11-05)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) and
[REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) (relaxed keep set, face exact;
uniques reduced on the user's "do all", 2026-11-05), ledger row 1 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease
`mm9reduce:kira` (owner kira-reduce-20261105); the creature's own `mm9:kira` lease was free. Source: the installed
`assets_source/worlds/mm9/models/mm9_kira.glb` (sha256 0afc4ec2a1e9, identical to `before/mm9_kira.glb`, the rollback source).
No Meshy, no credits, no repaint. **Not installed.** `../mm9_kira_claude/` was only read (labels, gate scripts, shadow-LOD and winding
helpers). Scripts are copies of `../mm9_peasantm1_reduce_claude/` (pose-aware `mpqem.py` with the chart guard and the audit's chart test),
adapted to Kira. The 2026-11-04 MeshLab attempt (hands kept whole, b r80 12,926, never gated) is in `scripts/meshlab_20261104/` and
`export/mm9_kira_meshlab_b80_20261104.glb` (superseded, do not install).

| | LOD0 | body prim `Kira` | head prim `KiraHead` | hands + fingers | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|---:|
| installed | 16,160 | 11,210 | 4,950 | 4,954 | 8,079 | 2,907 | 968 |
| **c2 r45 (`export/mm9_kira.glb` = `export/mm9_kira_c245.glb`, sha256 7db0f255ce4f)** | **12,724 (-21.3 %)** | 8,264 | 4,460 | 3,637 | 6,361 | 2,288 | 760 |

Every vertex of the candidate is an installed vertex (only index buffers changed). Clips (21), skin, nodes, materials, all 6 images:
byte-identical (`same_clips.py`). Face and neck skin (2,378), eyes (320) and every other kept face present exactly (`scripts/exact_parts.py`:
0 missing); the five-view face diff is black on the face (only the hair cap's shading and the armour differ).

## Protected share and keep set (`scripts/glb_parts.py`, `scripts/make_sets_kira.py`, set c2)
Parts come from Kira's final master (`work/master_labels.npz`, `mm9_kira_claude/work/uv_v6.blend`), matched 1:1 to the GLB triangles
(0.011 mm). Face + eyes = 16.7 % of LOD0. Set c2 keeps 33.5 %: face and eyes whole; hairline (hair within 8 mm of the skin), braid
root; collar (1.2 cm of the face skin); armour within 2 cm of hair or braid; vambraces within 4 cm of the hands (rim caps, inner wall:
r8 wrist fix and sleeve gate); hand-graft junction (glove stub + glove within 1.2 cm of the armour); fingertips (6 mm round each of the
10 tips); armour/belt/tasset/skirt/legs within 3 cm of a hand in 11 clips (hands on hips, seated hands); soles; pieces of up to 80
faces; leg faces within 6 cm of the knee cops, the knee cops, the tasset and the skirt-hinged armour band (added in c/c2, see ladders).
Groups: hands + fingers 0.7 (seam slides), hair 0.8, braid 0.7, mail skirt kept (1.0), plates (belt, medallion, lames) 0.7, legs 0.7,
armour shell at the ladder ratio. No effect sockets, glow parts, crown or held items on this model (no shield or sword; see the creature
README), so no prop rebuild. No linings exist; none were added.

## Ladders (limits for 1.814 m: p99 <= 5.44 mm, max <= 27.2 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_{a,b,c,c2}.png`)
| ladder | change | step | LOD0 | p99 / max mm | result |
|---|---|---|---:|---|---|
| a | hands .65, hair .7, skirt .75, legs .6 | r60 / r50 / r40 | 12,124 / 11,946 / 11,814 | 2.89/12.2, 3.59/15.5, 5.66/24.3 | pass / pass / fail; a50 built: hair profile slightly angular at the crown; skirt gate flagged a knee 17 cm in front of the cut hem |
| b | hands .7, hair .8, skirt kept | r50 / r45 | 12,376 / 12,288 | 3.56/15.5, 4.25/18.5 | pass; b45 built: hair as installed; in Sc2_KIRA16b the bent knee showed a sliver of the greave through the cut thigh (`review/close_b45_skirtflag.png`) |
| c | b + leg faces near the knee cops and the knee cops kept, legs .7 | r45 | 12,678 | 3.87/18.5 | pass; knee fixed; skirt gate still flagged knees in front of the cut tasset (Sc2_Kira9b 46 f, Sc2_KIRA16b 13 f at 17-19 cm) |
| **c2** | **c + tasset and skirt-hinged armour band kept** (the failing part kept exact; same step, not a new ladder) | **r45** | **12,724** | **4.00 / 18.47 (Sc2_KIRA5:150)** | **PASS, picked** (IoU .9946, SSIM .9943) |

## Gates, installed -> c2 r45 (`scripts/gates.sh`; `review/gates_before/`, `review/gates_c245/`)
- **UV audit** (`../claude_shared/reduction_uv_audit.py`, `review/uv_audit_c245.json` / `.txt`): **0 LOD0 escaping faces** (Kira 8,264,
  KiraHead 4,460). LOD1-3 (Blender decimate, as installed): body 124/224/149, head 76/93/77 vs installed 88/206/163, 73/91/67.
- Arm/hand (`arm_hand_gate.py --outer-only --exact`): hand and forearm depths identical in every clip (0 frames > 1 cm; worst 0.9 cm
  Fidget R and Sc2_Kira19 R as installed). Finger stretch maxima rise in some clips (Running L 1.76 -> 2.19, AttackMelee L 1.46 -> 1.85;
  overall max 2.11 -> 2.19): fewer finger vertices, longer edges across the knuckles; not visible in the hand close-ups.
- Skirt (legs through the mail skirt): identical to installed in every clip (Sc2_Kira9b 37 f 0.4 cm, Sc2_KIRA12 10 f 0.3, Sc2_KIRA14
  6 f 0.2, Sc2_KIRA20_23 8 f 1.2 cm).
- Jitter vs `mm9_kira_claude/work/kira_clips0.glb`: 4 fails = 4 (Running and Death shoulder skin, the installed's own; Death L 5.25 ->
  5.26 mm/f2); other shoulder-skin values move by sampling (several lower, a few up to +0.4 mm/f2, all far under the limit).
- Sleeve poke (inside, `--past 0`, and the default 3 cm): identical to installed in every clip (worst 0.2 mm AttackMelee R, Sc2_Kira7 L).
- Collapse face-frames lower in every clip (sum 67,392 -> 57,465); detached parts: same 2 flags (tasset 4.0 cm Sc2_KIRA12, armour 1.8 cm Running, by design);
  flat 0.00 both; bones 0 stretching of 12; winding 0; texture quality equal (body stretch p90 1.12 -> 1.13, head 1.08 -> 1.08).
- Fingers (`scripts/finger_dihedral.py`): dihedral p50 / p90 11.1 / 26.5 -> 13.3 / 29.8 deg (r7 before the user's finger fix: 20 / 45);
  every fingertip at full reach (identical tip distances).
- LODs (`scripts/lod_check.py`, every frame of every clip), built by `scripts/build_lods.py` (tool defaults 0.5/0.18/0.06, 4 influences;
  soles, crown and corpse contact of Death/Dead/StaticDie protected and snapped): height 1.8089 m at every LOD; every LOD's lowest point
  equal to LOD0 in every clip (installed LOD3 floated +0.9 cm in Standing); stretched faces 0/0/0/1 (installed 0/0/0/1).

## Review
Viewer (installed and reduced side by side, all 21 clips; `run_creature_review.py check`: 42 switches, 0 failed, no console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_kira_reduce_claude/review/viewer/
Sheets read (c245, full size): `review/sheet_face_c245.png` (front close-up, 3/4, true profile, low 3/4, party), `review/sheet_face_diff_c245.png`,
`review/sheet_body_c245_a.png` (Standing front/3-4/back, Walking, Fidget, Death), `review/close_c245_hands.png` (both hands, both wrist
rims, the AttackMelee fist), `review/close_c245_1.png` (arms, skirt front/back, Running, greaves/boots), `review/close_c245_2.png`
(Fidget arms, hair and shoulders from behind, Hit, hair top, Sit), `review/close_c245_3.png` (medallion, belt + tasset, knee cop,
pauldron lames, braid front), `review/close_c245_knees.png` (seated knees in Sc2_KIRA16b, Sit, Sc2_Kira9b), plus the profile shot
`review/shots/red_a/f2.png`. No visible difference found. Earlier steps' sheets: `review/*_a50*`, `*_b45*`, `*_c45*`.
Look at: the hair cap's crown in profile (shading only), the finger silhouettes of the curled right hand (very slightly more angular),
the seated knees in the cutscene clips.

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_kira_reduce_claude/before/mm9_kira.glb REA_NODE=Kira $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/glb_parts.py; $G scripts/tex_extract.py
$G -c "import numpy as np; g=np.load('work/glb_parts.npz'); np.save('work/keep_kneecops.npy', g['part']==11); np.save('work/keep_tasset.npy', g['part']==13)"
# work/keep_skirtband.npy: armour-shell faces whose corners all carry skirt-hinge (Bone*) weight (10 faces)
EXTRA=work/keep_kneecops.npy,work/keep_tasset.npy,work/keep_skirtband.npy KNEE=0.06 HAIRSKIN=0.008 CONTACT=0.03 HW=0.02 $G scripts/make_sets_kira.py c2
MP_AUDIT=1 MP_CHART=1 MP_W5=4 MP_SEAM_GROUPS=1 SETS=c2 MP_GROUPS=1:0.7,2:0.8,3:0.7,4:1.0,5:0.7,6:0.7 scripts/run_mp.sh c2 0.45
scripts/build_mp.sh mp_c2_r45 export/mm9_kira_c245.glb   # swap_mp -> build_lods (protected, snapped) -> Kira's shrink_shadow_lods -> fix_winding
$G ../claude_shared/reduction_uv_audit.py export/mm9_kira_c245.glb before/mm9_kira.glb --json review/uv_audit_c245.json
$G scripts/exact_parts.py export/mm9_kira_c245.glb c2; $G scripts/finger_dihedral.py before/mm9_kira.glb export/mm9_kira_c245.glb
scripts/gates.sh export/mm9_kira_c245.glb c245; REA_NODE=Kira $BL -P scripts/lod_check.py -- $PWD/export/mm9_kira_c245.glb c245
$G scripts/make_viewer_manifest.py c245-20261105 "inst_a=Kira installed (16,160)=before/mm9_kira.glb" "red_a=Kira reduced c2 r45 (12,724)=export/mm9_kira.glb"
scripts/shots.sh; scripts/close_shots.sh; $G scripts/shot_sheets.py c245; $G scripts/face_diff_sheet.py c245; $G scripts/close_sheet.py ...
```
Install (orchestrator, on the OK): `check_winding.py export/mm9_kira.glb` (0), `tools/install_model.py export/mm9_kira.glb --world mm9`,
the `mm9_actor_models_build_every_binding` regression, and add to `../mm9_kira_claude/README.md`: "LOD0 reduced post-install on <date> by
`mm9_kira_reduce_claude`; a rebuild from this project must re-run that reduction". Rollback: `before/mm9_kira.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (gates and viewer stills
only); LOD1-3 and shadow meshes by eye (numbers only); see-through gate (Kira's project has none; her armour is closed and no
linings exist); the cutscene clips beyond the seated-knee frames and the stills listed above.

The installed model carries `Socket_Sheath` and `Socket_RHand1` (her sword in the Argument, 2026-11-11), added after
this reduction by [`mm9_held_items_claude/scripts/add_sockets.py mm9_kira`](../../props/mm9_held_items_claude/scripts/add_sockets.py).
Rerunning this reduction drops them: run that script again and install its export (`tools/install_model.py --world mm9`).

Her seated Argument clips (Sit, Applause, Sc2_KIRA5 ... Sc2_KIRA14, and Sc2_KIRA16b as she stands) are lowered onto her
chair after install (2026-11-11) by [`mm9_kira_claude/scripts/seat_clips.py`](../mm9_kira_claude/scripts/seat_clips.py):
KIRA.abc keeps her standing hips while seated, so she hovered in front of her chair in the council cinematic. A
rebuild or reduction installed from here drops it: run `add_sockets.py mm9_kira`, install, then `seat_clips.py` and
install its export (`--name mm9_kira.glb`).
