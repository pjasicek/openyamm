# MM9 PeasantDM2 old dwarf (`mm9_peasantdm2`, row 47) reduction: candidate c3 r50 ready for review (2026-11-05; lease released)

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) /
[REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-2 townsfolk: relaxed keep set,
face exact), ledger row 47 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:peasantdm2` (owner
peasantdm2-reduce-20261105); the creature's own `mm9:peasantdm2` lease was free. Source: the installed
`assets_source/worlds/mm9/models/mm9_peasantdm2.glb` (sha256 dec7348e99ad, identical to `../mm9_peasantdm2_claude/export/mm9_pdm2.glb`, r7),
copied to `before/` (the rollback source). No Meshy, no credits, no repaint. **Not installed.** `../mm9_peasantdm2_claude/` was only read.
PeasantDM4 (`../mm9_peasantdm4_reduce_claude/`) is its own body (the DM4 README: own mesh, same skeleton); only its beard gate
was copied (`scripts/beard_gate.py`), nothing was written there.

| | LOD0 | body prim (tunic, legs, buttons, linings) | head prim (head shell + beard, hair, ears, plates, hands) | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|
| installed | 11,935 | 6,330 | 5,605 | 5,967 | 2,144 | 713 |
| **c3 r50 (`export/mm9_peasantdm2.glb` = `export/mm9_peasantdm2_c350.glb`, sha256 26ef672b8d1d)** | **10,107 (-15.3 %)** | 5,650 | 4,457 | 5,052 | 1,816 | 604 |

Shadow meshes 8,918 -> 7,414 (LOD0). Per group (free faces cut): hands 1,265 -> 791 (0.6, every finger kept), hair shell 1,186 -> 770
(0.65), scalp and back-of-head skin under the hair 662 -> 462 (0.7), beard sheet 243 -> 185 (0.7; the rest of the beard is kept,
below), trousers/boots 1,151 -> 861, tunic 970 -> 904 (the guards stop it), body linings 2,321 -> 1,997 (re-emitted from the cut
outer faces). Every vertex of the candidate is an installed vertex (positions, normals, UVs, joints, weights are the installed
bytes; only index buffers changed). Clips (15), skin, nodes, materials, region ramps, `KHR_materials_variants`, all 9 images:
identical (`same_clips.py`).

## Measured first: protected share
Parts (`scripts/analyze.py`, `scripts/head_parts.py` -> `review/head_parts.png`): body prim = upper tunic with sleeves (2,397),
lower tunic (907), trousers (994), two boots (984 / 980), three buttons (68); 2,980 of its 6,330 faces are one-texel linings,
rim strips or inner-layer twins (the creature's `linings.sh`). Head prim = one head shell (2,734: face, bald scalp, neck, beard
sheet, cheek patches), the hair shell (1,210), two MPFB hands (1,399), ears (89 / 79) and backing plates (76 / 18).
Keep set c3 (`scripts/make_sets_dm2.py c3` with `TW2=1 HALO_STRIP=0 HANDS=hand_contact_0.04.npy`): 4,930 faces (41.3 %) exact:
- face: the shell faces in the window |x| < 7.5 cm, 0.985 < y < 1.13 m, z > 3 cm plus one ring (1,475: eyes, lids, brows, nose,
  cheeks, moustache, mouth, forehead), every zero-UV head face (the cheek patch islands), the ears and backing plates, and the shell
  within 2 cm of the body (162: neck seam and the beard's contact with the chest);
- hand contact (`scripts/hand_contact_dm2.py`): every non-hand face whose posed centroid comes within 4 cm of a hand vertex in
  any clip at 24 Hz (318 more: the beard under RubBeard/Talk, the hips): c2 (the same cut without it) failed the arm and hand gate in
  Death (L hand 3.7 cm into the cut surface for one frame; installed 0);
- body: collar (tunic within 1 cm of the head prim), graft junction and cuffs (tunic within 4 cm of a hand vertex), soles, buttons,
  rim strips, unmapped loose linings with a 6 mm halo of outer faces, the inner-layer twin pairs (both carry UVs).

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`, the Dwarf boy's copy of PeasantF3's)
Chart guard `MP_CHART=1`, texture guard over both tiers and the region mask (`scripts/tex_extract.py`), texture weight 4, seam
slides on the hands, scored over every clip at 10 Hz, distance guard 3.5 mm (5 mm on tunic and legs, `MP_DMAX_GROUPS=0:5,3:5`).
Added here:
- **Loose linings re-emitted** (`scripts/twins.py` second pass): 464 one-texel lining faces had no face twin (the lining quad split on
  the other diagonal; rim-smoothed normals failed the back-to-back test), so the reference keep set held them exact with a 6 mm
  halo (1,464 tunic/leg faces). Same-weight vertex twins within 3.5 mm map 324 of them (`lining2`) to 324 outer faces (`lined2`);
  those linings are re-emitted from the cut outer faces like the paired ones, and the halo only covers the 302 still unmapped.
- **One texel per re-emitted lining face**: the corner map mixed two lining bands' texels in one face (c50: 25 LOD0 faces escaping
  the UV charts). Each re-emitted face now takes, at every corner's twin position, the lining copy whose texel all three corners
  share (copies at one position have equal weights and normals), and a collapse that leaves no shared texel is refused.
- `scripts/lining_gate.py` searches 32 nearest outer faces (8 missed the closest of the larger cut faces: false 16 mm "outs" at
  rest); baseline re-run the same way.

## Ladders (limits for 1.216 m: p99 <= 3.65 mm, max <= 18.2 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_<label>.png`)
| ladder | change | LOD0 | p99 / max mm (worst) | IoU / SSIM | result |
|---|---|---:|---|---|---|
| a | set a (reference keep set + face window), hands .6, hair .65, legs .5, scalp/beard .7 | 10,419 (-12.7 %) | 2.27 / 9.3 (Walking:9) | .997 / .996 | pass, under 15 % (tunic 655 free -> 631) |
| b | + loose linings re-emitted, halo only round unmapped linings | 10,211 (-14.4 %) | 2.42 / 9.3 | .996 / .995 | pass, under 15 % |
| c | + 5 mm guard on tunic/legs | 9,989 (-16.3 %) | 2.82 / 9.3 | .996 / .995 | pass; built c50: 25 UV escapes (lining texels), export deleted |
| c2 | c + one texel per re-emitted lining | 9,993 (-16.3 %) | 2.82 / 9.3 | .996 / .995 | UV audit 0; arm/hand FAIL Death L 3.7 cm (1 frame), export deleted |
| **c3** | **c2 + hand-contact faces exact** | **10,107 (-15.3 %)** | **2.77 / 9.3 (Walking:9)** | **.997 / .995** | **PASS, picked; every gate equal** |

c2/c3 are fixes of ladder c (same ratios), not further ladders: the failing part (faces under the hands) was kept exact.

## Gates, installed -> c3 r50 (`scripts/gates.sh` with the creature's own gate scripts; `review/gates_before/`, `review/gates_c350/`)
- **UV audit** (`../claude_shared/reduction_uv_audit.py`, `review/uv_audit_c350.json`): **0 escaping LOD0 faces in both primitives**.
  LOD1-3 escapes come from the LOD tool's decimate, near the installed file's own (body/head: LOD1 160/165 vs installed 141/151,
  LOD2 147/158 vs 128/157, LOD3 49/91 vs 49/108).
- Arm and hand (`--outer-only`, 48 fps): 0 frames > 1 cm, both hands, all 15 clips, both; finger stretch maxima equal or lower,
  minima +0.01..0.03.
- Jitter vs MM9's untouched clips: 0 fails both.
- Sleeve poke (`sleeve_poke_gate.py`): identical per clip (rest 0 mm both sides; AttackMelee L 48.4 mm 5 f, Death R 36.1, Dump R 27.8,
  Rock R 15.9, Hammer R 13.3, Cower L 4.2, Fidget2 R 3.6: the creature's checked wrist-fold cases).
- Beard (DM4's gate, `scripts/beard_gate.py`: edge stretch and torso contact over every clip at 48 fps): identical in every clip
  (stretch max 8.675, contact gap max +1.43 cm, approach max 1.22 cm; 77 contact vertices both).
- Linings (`scripts/lining_gate.py`, 32 faces): largest outward 3.00 mm both, most vertices > 0.5 mm per clip equal or fewer
  (e.g. AttackMelee 56 -> 52, Fidget2 41 -> 38, Running 40 -> 37).
- See-through (creature's `see_through_gate.py`, every 3rd 30 fps frame, 16 views; worst px, installed -> c3):
  boots 0/0, trousers 0/0, collar 2/2 (frames 3 -> 4), torso 4/4 (14 -> 17 frames), head 9/9 (213 -> 210), sleeve L 4 -> 3 (26 -> 25),
  sleeve R 4 -> 5 (3 frames both; specks on the shoulder edge, `review/gates_c350/see_through_sleeveR_Death_24_az315_el00.png`).
  Equal within single-pixel noise.
- Detached parts: same two boots (lining artifact, the creature's README): R 1.66 -> 1.80 cm (12 -> 11 of 744 poses), L 1.02 -> 0.94 cm
  (4 -> 3). Flat shading 0.00 both. Winding 0. Bone lengths 12 checked, 0 stretching. Texture quality: body atlas 62.4 % both,
  stretch p90 1.07 -> 1.08; head 42.2 % both, stretch 1.34 both.
- LODs (`scripts/lod_check.py`, every frame of every clip; `scripts/build_lods.py`: tool ratios 0.5/0.18/0.06, 4 influences, soles/
  crown/corpse contact protected and snapped):
  height 1.2157 m at every LOD (installed LOD2 1.2172, LOD3 1.2219); lowest point at LOD1-3 equal to LOD0 within 0.6 mm in every clip
  (installed LOD2 floated +0.1..+0.4 cm and LOD3 +0.1..+1.2 cm); stretched faces LOD0 2 per clip (AttackMelee 4) vs installed 3 (5),
  LOD1-3 0 both. Logs `work/lod_check_{installed,c350}.log`.

## Review
Viewer (installed and reduced, both tiers, all 15 clips; `run_creature_review.py check`: 60 switches, 0 failed, no console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_peasantdm2_reduce_claude/review/viewer/
Sheets read (installed left/above, c350 right/below): `review/sheet_face_c350.png` and `review/sheet_face_diff_c350.png` (front
close-up, 3/4, profile, low 3/4, party; both tiers: face skin, beard and moustache black in all ten diffs, only the hair shell, the
tunic shoulders and the lower collar differ), `review/close_c350_a_{1,2,3,4}.png` (arms/torso front and back, Running, boots, hands
outside and front, hair from behind, Death lying, RubBeard hand on the beard, belt, boot cuffs), `review/close_c350_b_4.png`,
`review/sheet_body_c350_b.png` and `review/sheet_body_c250_a.png` (full body front/3-4/back, Walking, Fidget, Death; c250 = c3 without
the hand-contact keep). Generated, not opened: `review/sheet_body_c350_a.png`, `review/close_c350_b_{1,2,3}.png`. `review/head_parts.png`, `review/sets_*` show the keep sets.
Look at: the hair shell silhouette and its shading from the side and behind (0.65: a few more facets in the shading, outline the same),
the knuckles (hands at 0.6), the lower tunic back.

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_peasantdm2_reduce_claude/before/mm9_peasantdm2.glb REA_NODE=PeasantDM2 $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/twins.py; $G scripts/tex_extract.py; $G scripts/head_parts.py
R=0.04 $G scripts/hand_contact_dm2.py; cp work/hand_contact.npy work/hand_contact_0.04.npy
TW2=1 HALO_STRIP=0 HANDS=hand_contact_0.04.npy $G scripts/make_sets_dm2.py c3
REA_HEIGHT_M=1.216 MP_DMAX_MM=3.5 MP_DMAX_GROUPS=0:5,3:5 MP_CHART=1 MP_W5=4 MP_SEAM_GROUPS=1 SETS=c3 \
  MP_GROUPS=1:0.6,2:0.65,3:0.5,6:0.7,7:0.7 scripts/run_mp.sh c3 0.5
scripts/build_mp.sh mp_c3_r50 export/mm9_peasantdm2_c350.glb   # swap_mp -> build_lods -> creature's shrink_shadow_lods -> carry_variants -> fix_winding -> restore_materials
$G ../claude_shared/reduction_uv_audit.py export/mm9_peasantdm2_c350.glb before/mm9_peasantdm2.glb --json review/uv_audit_c350.json
scripts/gates.sh export/mm9_peasantdm2_c350.glb c350; scripts/see_through.sh export/mm9_peasantdm2_c350.glb c350
REA_NODE=PeasantDM2 $BL -P scripts/lod_check.py -- $PWD/export/mm9_peasantdm2_c350.glb c350
$G scripts/viewer_tiers.py export/mm9_peasantdm2_c350.glb red; python3 scripts/make_viewer_manifest.py c350 "inst_a=..=work/viewer_inst_th_a.glb" ...
HEADUP=0,0.08,0.09 scripts/shots.sh; scripts/close_shots_dm2.sh; $G scripts/shot_sheets.py c350; $G scripts/face_diff_sheet.py c350
$G scripts/close_sheet.py c350 a c0,c1,c2,c3 review/close_c350_a_1.png   # ... _2 .. _4, tier b
```
Install (orchestrator, on the OK): `check_winding.py export/mm9_peasantdm2.glb` (0), `tools/install_model.py export/mm9_peasantdm2.glb
--world mm9 --name mm9_peasantdm2.glb`, the `mm9_actor_models_build_every_binding` regression, and add to
`../mm9_peasantdm2_claude/README.md`: "LOD0 reduced post-install on <date> by `mm9_peasantdm2_reduce_claude`; a rebuild from this
project must re-run that reduction". Rollback: `before/mm9_peasantdm2.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (frames, gates and
viewer stills only); LOD1-3 and shadow meshes by eye (numbers only); fingertips at full size (the hand close-ups frame the backs of the
hands); the viewer's shoulders-from-behind preset came out empty for this figure.

## MM9 sockets (2026-11-10)

The installed model carries MM9's attach points as `Socket_<name>` nodes for held items (scene `held_items`, MM9's AttachProp), added after this project's install by [`mm9_held_items_claude/scripts/add_sockets.py`](../../props/mm9_held_items_claude/scripts/add_sockets.py) (`Socket_RHand1`). A rebuild installed from here drops them: run that script again and install its export (`tools/install_model.py --world mm9`).
