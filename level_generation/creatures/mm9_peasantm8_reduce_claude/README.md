# MM9 PeasantM8 (`mm9_peasantm8`, the balding shopkeeper, row 93) reduction: candidate d r55 ready for review (2026-11-05; lease released)

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) /
[REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-2 townsfolk: relaxed keep
set, face exact), ledger row 93 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:peasantm8` (owner
peasantm8-reduce-20261105); the creature's own `mm9:peasantm8` lease was free (no lease file). Source: the installed
`assets_source/worlds/mm9/models/mm9_peasantm8.glb` (sha256 d4cf7649b69d, identical to `../mm9_peasantm8_claude/v2/export/mm9_pm8.glb`),
copied to `before/` (the rollback source). No Meshy, no credits, no repaint. **Not installed.** `../mm9_peasantm8_claude/` was only read
(its `v2/scripts/arm_hand_gate.py`, `jitter_gate.py`, `shrink_shadow_lods.py` and `v2/work/mm9_pm8_clips.glb` run in place).
Scripts copied from `../mm9_peasantm8d_reduce_claude/scripts/` (same Forad body) with the names changed; `../mm9_peasantm8d_reduce_claude/`
and `../mm9_peasantm4_reduce_claude/` (another agent's, running) were only read.

**Family note:** PeasantM8 is Forad Darre's body less the ponytail, its ties and the necklace, with its own paint. The body primitive
(3,677 faces) is the same welded piece as PeasantM8d's; the head primitive is the same 2,093-face shell plus the two MPFB hands (699 / 699).
PeasantM8d's set cs and route were re-run here on PeasantM8's own GLB and paint (its cut is not copied: the texture guard is per paint).

| | LOD0 | body prim | head prim (shell + hands) | LOD1 | LOD2 | LOD3 | shadow LOD0 |
|---|---:|---:|---:|---:|---:|---:|---:|
| installed | 7,168 | 3,677 | 3,491 | 3,582 | 1,288 | 427 | 7,168 |
| **d r55 (`export/mm9_peasantm8.glb` = `export/mm9_peasantm8_d55.glb`, sha256 b223eb8cbd06)** | **6,050 (-15.6 %)** | 3,155 | 2,895 | 3,022 | 1,087 | 360 | 6,050 |

Per group (free faces cut): hands 1,201 -> 731 (0.6, every finger kept; graft faces exact), back/side scalp hair 314 -> 188 (0.6),
breeches/boots 1,210 -> 826 (0.6, 5 mm guard), tunic free 647 -> 509 (the 4 mm guard stops it); linings 104 -> 104 (103 installed, 1
re-emitted). Every vertex of the candidate is an installed vertex (only index buffers changed). Clips (12), skin, nodes, materials, all 6
images identical (`same_clips.py`). Exact head shell (1,779 faces: face skin, the bald scalp, ears, neck, brows, the hairline ring, the
collar band in the head material) and every kept face present exactly (`scripts/exact_head.py`).

## Measured first: protected share
`scripts/analyze.py`, `scripts/head_classes.py` (changed for this paint: the blond hair is saturated gold, so hair = hue 30-70 deg with
saturation > 0.35; PeasantM8d's "light, unsaturated" test found 6 hair faces; `HUE_MIN=30`: 383 hair, 1,541 skin, 169 collar band).
Set a (head shell exact, hands/cuffs/graft/soles/rims/hand contact): 2,777 protected (38.7 %), free 4,391. Set cs (+ shoulder cloth 768,
tunic front panel 279, fold faces 21, as PeasantM8d's picked set): 3,796 protected (53.0 %), free 3,372: 15 % of LOD0 (1,075) is 32 % of the
free part, under the 40 % stop line, so the run went ahead. The ponytail (530 free faces on PeasantM8d) is missing here, and the bald scalp is
skin (exact), so PeasantM8d's own settings only reach -14.2 % on this model (ladder c).

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`, PeasantM8d's copy)
Chart guard `MP_CHART=1`, texture guard on the single tier (`scripts/tex_extract.py`), texture weight 4, seam slides on the hands, scored over
every clip at 10 Hz, distance guard 4 mm (5 mm on the legs in d), linings re-emitted from `work/twins.npz`.

## Ladders (limits for 1.758 m: p99 <= 5.27 mm, max <= 26.4 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_<label>.png`)
| ladder | change | LOD0 | p99 / max mm (worst) | IoU / SSIM | result |
|---|---|---:|---|---|---|
| c | PeasantM8d's picked settings: set cs, hands .6, scalp .7, legs .65, tunic r60 (= r50), 4 mm guard | 6,150 (-14.2 %) | 3.02 / 10.6 (Fidget:57) | .997 / .995 | pass, but under the ~15 % line |
| **d** | **c with legs .6 under a 5 mm guard, scalp hair .6** | **6,050 (-15.6 %)** | **3.36 / 10.6 (Fidget:57)** | **.996 / .995** | **PASS, picked; every gate equal** |

## Gates, installed -> d r55 (`scripts/gates.sh`, `scripts/see_through.sh`; `review/gates_before/`, `review/gates_d55/`)
- **UV audit** (`../claude_shared/reduction_uv_audit.py`, `review/uv_audit_d55.json`): **0 escaping LOD0 faces in both primitives**.
  LOD1-3 escapes come from the LOD tool's decimate, near the installed file's own (body/head LOD1 158/116, LOD2 127/124, LOD3 62/81;
  installed LOD1 130/103, LOD2 148/122, LOD3 64/80).
- Arm and hand (`--outer-only --exact`, 48 fps): hand and forearm intrusion equal in every clip (Talk L 3.3 cm 40 frames, MM9's hand on
  the heart, as installed; Fidget R forearm 1.2 cm as installed); finger stretch maxima equal, minima within +0.11; wrists equal.
- Jitter vs MM9's untouched clips: identical text (the creature's accepted fails: Walking L/R, Talk L, Death shoulder skin).
- Sleeve poke: identical per clip (candidate vertices L 89 -> 88). Linings (`lining_gate.py`): identical per clip.
- See-through (creature's gate, every 3rd 30 fps frame, 16 views): head, torso, boots, trousers, collar 0 both; sleeves at the cuff rim equal or within one pixel in a single frame (`review/see_through_compare_d55.txt`: R Conv2 22 -> 21 px, Conv3 17, Running 12, AttackMelee 9 equal; L Talk 4 -> 2 px; new single-pixel single-frame hits Death L 1 px frame 42 and Fidget R 1 px frame 9, not visible in `review/gates_d55/see_through_sleeveL_Death_42_az315_el20.png`).
- Detached parts 0 both (3 components); flat shading 0.00 both; winding 0; bone lengths 12 checked, 0 stretching. Texture quality:
  body atlas 53.3 % both, stretch p90 1.09 -> 1.10; head 44.0 % both, stretch 1.24 -> 1.23, fragments 2.7 -> 4.0 %.
- LODs (`scripts/lod_check.py`, every frame of every clip; `scripts/build_lods.py`: ratios 0.5/0.18/0.06, 4 influences, 36 of 36
  protected points mapped): height 1.7872 m at every LOD; lowest point at LOD1-3 equal to LOD0 in every clip (installed LOD2 floated up to 1.05 cm, LOD3 1.3 cm); 0 stretched faces at every LOD, both. Logs `work/lod_check_{installed,d55}.{log,json}`.

## Review
Viewer (installed and reduced, the one tier, all 12 clips; `run_creature_review.py check`: 24 switches, 0 failed, no console errors,
`review/viewer_check.txt`): http://127.0.0.1:8912/level_generation/creatures/mm9_peasantm8_reduce_claude/review/viewer/
Sheets read (installed left/above, d55 right/below): `review/sheet_face_d55.png`, `review/sheet_face_diff_d55.png` (front close-up, 3/4,
profile, low 3/4, party: face skin, bald scalp, ears and neck black in all five diffs; only the back/side hair facets and a sliver of its
outline differ), `review/crop_hair_profile_d55.png` (profile hair full size), `review/sheet_body_d55_a.png` (Standing front/3-4/back, Walking,
Fidget, Death), `review/close_d55_{1,2,3,4}.png` (arms, tunic front/back, Running, boots, Talk arms, shoulders and hair from behind, Hit, L/R
hands and cuffs, hair from behind above, sleeve, lacing, lapels and belt buckle, boot cuffs), `review/ladder_sheet_{c,d}.png`,
`review/sets_cs_{head,body,hands}.png`.
Look at: the back of the hair in profile (0.6: strands at slightly different angles, the outline behind the ear a little more angular),
the hand backs (0.6), the R boot cuff's top rim in `close_d55_2.png` c4 (a slightly different corner shading).

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_peasantm8_reduce_claude/before/mm9_peasantm8.glb REA_NODE=PeasantM8 $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/twins.py; $G scripts/tex_extract.py; HUE_MIN=30 $G scripts/head_classes.py
$G scripts/hand_contact_dm2.py; cp work/hand_contact.npy work/hand_contact_0.04.npy
SHOULDER=1 PANEL=1 DEV=75 DEV_RING=0 FRONT_Z=0.05 BACK_Z=-0.02 BACK_Y=1.66 HANDS=hand_contact_0.04.npy $G scripts/make_sets_m8d.py cs
REA_HEIGHT_M=1.758 MP_DMAX_MM=4 MP_DMAX_GROUPS=3:5 MP_CHART=1 MP_W5=4 MP_SEAM_GROUPS=1 SETS=cs MP_GROUPS=1:0.6,3:0.6,6:0.6 scripts/run_mp.sh d 0.55
scripts/build_mp.sh mp_d_r55 export/mm9_peasantm8_d55.glb   # swap_mp -> build_lods -> creature's shrink_shadow_lods -> carry_variants (none) -> fix_winding -> restore_materials
$G ../claude_shared/reduction_uv_audit.py export/mm9_peasantm8_d55.glb before/mm9_peasantm8.glb --json review/uv_audit_d55.json
$G scripts/exact_head.py export/mm9_peasantm8_d55.glb cs
work/queue_d55.sh   # gates.sh, see_through.sh (installed and d55), lod_check.py (installed and d55); python3 scripts/see_through_compare.py d55
python3 scripts/make_viewer_manifest.py d55 "inst_a=installed 7,168=before/mm9_peasantm8.glb" "red_a=reduced d r55 6,050=export/mm9_peasantm8_d55.glb"
HEADUP=0,0.08,0.05 scripts/shots.sh "inst_a red_a"; scripts/close_shots.sh "inst_a red_a"; $G scripts/shot_sheets.py d55; $G scripts/face_diff_sheet.py d55
$G scripts/close_sheet.py d55 a c0,c1,c2,c3 review/close_d55_1.png   # ... _2 .. _4
```
Install (orchestrator, on the OK): `check_winding.py export/mm9_peasantm8.glb` (0), `tools/install_model.py export/mm9_peasantm8.glb
--world mm9 --name mm9_peasantm8.glb`, the `mm9_actor_models_build_every_binding` regression, and add to
`../mm9_peasantm8_claude/README.md`: "LOD0 reduced post-install on <date> by `mm9_peasantm8_reduce_claude`; a rebuild from this
project must re-run that reduction". Rollback: `before/mm9_peasantm8.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (frames, gates and
viewer stills only); LOD1-3 and shadow meshes by eye (numbers only); Conv2/Conv3 in the viewer by eye (gates only).
