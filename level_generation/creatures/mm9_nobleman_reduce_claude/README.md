# MM9 Nobleman (`mm9_nobleman`, Baron / Viscount / Count) reduction: candidate d52 ready for review (2026-11-04)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-1 relaxed keep set),
ledger row 53 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:nobleman` (owner nobleman-reduce-20261104); the
creature's own `mm9:nobleman` lease was free. Source: the installed `assets_source/worlds/mm9/models/mm9_nobleman.glb` (sha256
f820e51d08fc, identical to `../mm9_nobleman_claude/export/mm9_nobleman.glb`), copied to `before/` (the rollback source). No Meshy, no
credits, no repaint. **Not installed.** `../mm9_nobleman_claude/` was only read.

| | LOD0 | limbs (Nobleman_A) | torso (NbTorso) | head (NbHead) | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|---:|
| installed | 10,727 | 2,869 | 4,106 | 3,752 | 5,361 | 1,926 | 659 |
| **d52 (`export/mm9_nobleman.glb`, sha256 1de5c768cc56)** | **8,119 (-24.3 %)** | 1,955 | 3,072 | 3,092 | 4,058 | 1,457 | 541 |

Every vertex of the candidate is an installed vertex: positions, normals, UVs, joints and weights are the installed bytes (only
index buffers changed). Clips (17), skin, nodes, materials, region ramps, `KHR_materials_variants`, all 18 images: byte-identical
(`same_clips.py`). Face skin, neck and eyes are the installed triangles: every tier's face renders pixel-identical
(`review/sheet_face_diff_d52.png`: face and neck black in all five views of all three tiers; only hair, mantle and doublet differ).

## Measured first: protected share
The Meshy head is one shell for face and hair (master part 20), so `scripts/head_split.py` splits it per face: hair = no skin paint
in any tier (tier A blond by hue < 25 deg, B white and C brown by RGB distance to each tier's cheek colour), cleaned by connectivity
(skin flecks in the hair, hair flecks in the face), the front of the face below the brow always skin (painted beards on jaw and
chin), and only the main hair mass (`review/head_split.png`: 2,230 hair of 3,592 head faces). Kept exactly in set a (21.8 %): face
skin with the neck and its seam (1,362), eyes (160), the belt (212, thin painted trims), soles (68), the hand-graft junction (191),
the hairline (345 hair faces within 8 mm of face skin). Set d (final, 40.8 %) adds:
- **shoulder skin** (1,044: faces with a vertex dominated by a Clavicle or UpperArm, the jitter gate's shoulder term; a55 moved
  its 95th percentile, AttackMelee2 R 3.84 -> 4.27 mm/f2) and **hand contact** (523: faces within 3 cm of the other hand in
  Fidget, mirrored; a55 R hand into the clasped L hand 1.6 -> 1.9 cm) (`scripts/gate_keeps.py`);
- the **neck seam** ring (166 body faces within 1.5 cm of the head set), the **mantle rim** (310 faces within two rings of the fur
  mantle's open border: b55 put a light wedge on its lower front edge) and the **throat** centre seam under the collar V (50: the
  grey notch grew at c55) (`scripts/seam_keeps.py`, `THROAT=1`).
Groups: hands 0.65 (every finger kept), hair 0.65, skirt 0.7 (MM9's six hinges), shoes above the soles 0.6; doublet, legs and mantle
take the ladder ratio. No linings and no weapon on this body (finish_nb only plugs the mouth), so the lining rebuild is inert.

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`, the Highwayman's copy)
Scored over 300 poses (every clip at 10 Hz) plus a position+UV rest quadric; only removes vertices; texture guard on all three
tiers (limbs: the shared image, torso and head: each tier's own colour; refuse at > 100 any sample / > 45 mean).

## Ladder (height 1.834 m: p99 <= 5.50 mm, max <= 27.5 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_{a,b,c,d}.png`)
| set | change | step | LOD0 | p99 / max mm (worst) | IoU / SSIM | |
|---|---|---|---:|---|---|---|
| a | base keep set | r55 / r50 / r45 | 7,329 / 7,101 / 6,871 | 4.41/22.2 (Hit2), 5.53/22.2, 7.28/21.3 | .994/.996 | pass / fail / fail |
| b | a + shoulder skin + Fidget hand contact | r55 / r50 | 7,991 / 7,819 | 4.48/22.2, 5.84/22.6 | .995/.996 | pass / fail |
| c | b + neck seam + mantle rim | r55 / r50 | 8,189 / 8,039 | 4.26/22.2, 5.67/22.6 | .995/.996 | pass / fail |
| **d** | c + throat seam | r55 / **r52** | 8,209 / **8,119** | 4.32/22.2, **4.99/22.2 (Hit2)** | **.993/.996** | pass / **PASS, picked** |

a55 (-31.7 %) passed the ladder but moved the jitter shoulder term and the Fidget hand contact above the installed values and showed
the close-up shading marks above; b, c and d bring those back for about 800 triangles.

## Gates, installed -> d52 (the Nobleman's own scripts, `scripts/gates.sh`; `review/gates_before/`, `review/gates_d52/`, `review/gates_compare_d52.txt`)
- Collapse face-frames 27,909 -> 25,206, lower or equal in every clip; worst-frame region counts mostly lower (Death2 shoulder R
  76 -> 65, AttackMelee groin 25 -> 16, Cower torso 16 -> 10); up: elbow_L AttackMelee 0 -> 1, AttackMelee2 3 -> 4, Cower 9 -> 10;
  hip 0 -> 1 in Running, AttackMelee2, Cower; hip_R Hit2 2 -> 3; **torso in Death 3 -> 6**.
- Skirt gate: identical in every clip (0 frames everywhere).
- Arm/hand (outer and skin-only): Hit2 R 3.7 -> 3.5 cm, Death2 R forearm 0.5 -> 0.4 cm; **Fidget R hand 1.6 cm both, frames over
  1 cm 13 -> 14**; finger stretch p99 +0.01 in Standing L, Fidget2/Taunt L and R, AttackMelee2 L, maxima equal or lower.
- Jitter vs MM9's untouched clips: output identical, 7 fails both (the installed model's own: arm_const/arm_bump offsets).
- Bone lengths 0 stretching. Winding 0. Flat shading 0.00. Detached parts 0 (8 components; R hand root lift p90 1.29 -> 1.35 cm).
  Texture quality: limbs stretch p90 1.54 -> 1.55, torso/head density p90 +1-5 px, otherwise unchanged.
- LODs (`scripts/lod_check.py`, every frame of every clip; `work/lod_check_{installed,d52}.json`), built by `scripts/build_lods.py`
  (tools/build_actor_lods.py defaults, soles/crown/corpse contact protected): height 1.8339 m at every LOD (installed LOD3 1.8305);
  Standing lowest point -0.01 cm at every LOD (installed LOD3 +1.6 cm, floating); Dead 0 at every LOD; Death -1.37 cm, Death2 -1.64 /
  -1.64 / -1.39 / -1.39 cm (installed -2.04 / -2.04 / -1.23 / -1.31); faces stretched > 20x: LOD0 Hit2 1 (as installed), LOD1-3 0.

## Review
Viewer (installed and reduced, every tier, all 17 clips; `run_creature_review.py check`: 102 switches, 0 failed, no console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_nobleman_reduce_claude/review/viewer/
Sheets read: `review/sheet_face_d52.png` (front close-up, 3/4, profile, low 3/4, party; every tier), `review/sheet_face_diff_d52.png`,
`review/crop_hair_d52.png` (Count's painted headband, Viscount's hair in profile, full size), `review/sheet_body_d52_c.png`
(and a55 `review/sheet_body_a55_a.png`), `review/close_d52_{a,c}_{1,2}.png` (arms, skirt front/back, Running skirt, shoes, AttackMelee2
arms, shoulders from behind, Cower), `review/head_split.png`, `review/ladder_sheet_a.png`; close-up crops of the chest at a55/b55/c55
(`work/chest_a_zoom*.png`). Look at: the fur mantle up close (larger triangles shade the fur a little differently), the shin bands
(band edges slightly softer on one leg), the gold placket hem, the hair (cut to 65 %, no holes or steps found).

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
$BL -P scripts/dump_final_parts.py                    # part labels of ../mm9_nobleman_claude/work/final_v1.blend
REA_GLB=level_generation/creatures/mm9_nobleman_reduce_claude/before/mm9_nobleman.glb REA_NODE=Nobleman $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/glb_parts.py; $G scripts/tex_extract.py; $G scripts/head_split.py
HAIRLINE=0.008 SOLE=0.012 $G scripts/make_sets.py a; $G scripts/glb_sets.py a
$G scripts/gate_keeps.py a b; THROAT=1 $G scripts/seam_keeps.py b d
SETS=d scripts/run_mp.sh d 0.55,0.52                  # mpqem (MP_GROUPS 1:0.65,2:0.65,3:0.7,4:0.6; guard 100/45) -> ladder -> compare
SOLE=0.012 scripts/build_mp.sh mp_d_r52 export/mm9_nobleman.glb   # swap_mp -> build_lods (protected) -> shrink_shadow_lods -> carry_variants -> fix_winding
scripts/gates.sh export/mm9_nobleman.glb d52; $G scripts/gate_compare.py d52
REA_NODE=Nobleman $BL -P scripts/lod_check.py -- $PWD/export/mm9_nobleman.glb d52
$G scripts/viewer_tiers.py export/mm9_nobleman.glb d52   # ramps baked for three.js (the creature's own viewer_tiers rule)
scripts/shots.sh; $G scripts/shot_sheets.py d52; $G scripts/face_diff_sheet.py d52; scripts/close_shots.sh
```
Install (on the user's OK only): `check_winding.py export/mm9_nobleman.glb` (0), `tools/install_model.py export/mm9_nobleman.glb
--world mm9`, the `mm9_actor_models_build_every_binding` regression, and add to `../mm9_nobleman_claude/README.md`: "LOD0 reduced
post-install on <date> by `mm9_nobleman_reduce_claude`; a rebuild from this project must re-run that reduction". Rollback:
`before/mm9_nobleman.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (frames, gates and
viewer stills only); LOD1-3 and shadow meshes by eye (numbers only); the Viscount in close-ups (face and body sheets only); the
Fidget R extra frame over 1 cm (depth unchanged) and the Death torso collapse count 3 -> 6 were not chased further.
