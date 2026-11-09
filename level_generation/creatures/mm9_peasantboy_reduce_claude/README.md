# MM9 peasant boys (`mm9_peasantboy` = Boy1 / Boy2 / Boy1e) reduction: candidate b r60 ready for review (2026-11-05)

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) /
[REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-2 townsfolk: relaxed keep set,
face exact), ledger row 49 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:peasantboy` (owner
peasantboy-reduce-20261105); the creature's own `mm9:peasantboy` lease was free. Source: the installed
`assets_source/worlds/mm9/models/mm9_peasantboy.glb` (sha256 05c721131969, identical to `../mm9_peasantboy_claude/export/mm9_pboy.glb`),
copied to `before/` (the rollback source). No Meshy, no credits, no repaint. **Not installed.** `../mm9_peasantboy_claude/` was only read.

## The family
One body GLB carries all three boys (`KHR_materials_variants` pboy_a / pboy_b / pboy_e: body ramps, boy b's own region mask, three head
images). The only other file, `mm9_peasantboy_elfears.glb` (row 73's elf ears, 672 triangles, a rigid attachment on joint
`Bip01 ElfEars`), is ear geometry: kept exact and **unchanged** (copied to `before/` for reference; no ledger row: the ledger lists the
boys' ear piece among the small attachments it leaves out). So the family is reduced by this one cut; nothing else to re-derive.

| | LOD0 | body prim (cloth, legs, belt/toggles, linings, waist tube) | head prim (head, hair, hands) | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|
| installed | 11,191 | 6,946 | 4,245 | 5,786 | 2,094 | 699 |
| **b r60 (`export/cand_b60/mm9_peasantboy.glb`, sha256 30114c1985b3)** | **8,991 (-19.7 %)** | 5,776 | 3,215 | 4,492 | 1,614 | 534 |

Per group (`work/mp_b.log`): hands 1,279 free -> 767 (0.6, every finger segment keeps faces: smallest L/R Pinky2 21/18 -> 6/6),
hair 794 -> 476 (0.6), scalp under the hair 478 -> 278 (0.5), legs 1,064 -> 684, cloth 640 -> 512 (the guards stop it), waist backstop
tube 1,472 -> 844, paired linings 832 -> 798 (764 installed, 34 re-emitted). Head part (face skin, eyes, brows, nose, mouth, ears' place,
jaw, neck piece: 1,574 faces) exact. Every vertex of the candidate is an installed vertex (positions, normals, UVs, joints, weights are
the installed bytes; only index buffers changed). Clips (10), skin, nodes, materials, region ramps and masks, `KHR_materials_variants`,
all images: identical (`same_clips.py`; `scripts/restore_materials.py` puts back the installed material JSON).

## Measured first: protected share
Parts by welded component (`scripts/analyze.py`, `scripts/make_sets_boy.py`): body prim = cloth (vest, sleeves, vest skirt; 2,226 incl.
275 linings), legs (trousers, lower legs, boots; 2,708 incl. 528 linings), belt + toggle placket + toggles (540), the waist backstop tube
(`waist_backstop.py`: 1,472 one-texel faces inside the trunk); head prim = head shell + neck piece (2,052), hair bob (794), two MPFB hands
(1,399). Linings (`linings.sh`, 3 mm twins, one dark texel) found by `scripts/twins.py` (back-to-back faces, identical weights): 832 pairs.
Protected in set b (kept faces + linings of kept faces): 5,192 (46.4 %). Kept exactly: head part except the scalp under the hair; belt,
placket, toggles; collar (1 cm of the head), graft junction (1.5 cm hand/body), soles (1.2 cm), rim strips, 563 unpaired one-texel linings
(clamped offsets) and the outer faces within HALO (4 mm in set b) of them, lining pairs that carry UVs.

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`, the Dwarf boy's copy of PeasantF3's)
Scored over every clip at 10 Hz; texture weight 4; chart guard (`MP_CHART=1`); the audit's own chart test per new face (`MP_AUDIT=1`,
PeasantM2d's); texture guard over all three tiers' baked body colours, both region masks and the three head images (`scripts/tex_extract.py`);
distance guard 3.5 mm (`MP_DMAX_MM`, the Dwarf boy's); seam slides on the hands. Added here:
- **Re-emitted lining faces on one texel.** Two lining bands with different dark texels meet at the trouser top; a re-emitted lining face
  whose twins sat on both texels spanned the texture between them (a60: 10 LOD0 faces in the UV audit, crotch). A collapse is now refused
  when a new face's corners have twins with no common texel, and each re-emitted face takes the copies on that texel.
- **The waist tube may be cut** (`MP_ZERO_GROUPS=6`: one-texel faces skip the UV-orientation test; every corner stays on the dark texel)
  **under a containment guard** (`MP_ZTOL_MM`): the tube follows the innermost cloth per angle, so its section is not convex and a chord can
  stand outside it. a2 (no guard) put tube chords up to 8.6 mm outside the installed tube and the detached audit then flagged a 26 cm
  "root lift" on the vest. Every new tube face's edge midpoints and centroid must stay within ZTOL of the installed tube surface at rest
  and in every 6th pose.

## Ladders (limits for 1.366 m: p99 <= 4.10 mm, max <= 20.5 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_<label>.png`)
| ladder | change | LOD0 | p99 / max mm (worst) | IoU / SSIM | result |
|---|---|---:|---|---|---|
| a (r60, r50) | set a (halo 6 mm, scalp 0.5), hands .6, hair .65, legs .6, tube .4, no tube guard | 8,857 (r50 = r60: cloth saturates) | 2.75 / 8.9 (AttackMelee:9) | .9953 / .9964 | pass; built a60: UV audit 10 LOD0 escapes (mixed lining texels) |
| a2 | a + lining texel guard | 8,877 | 2.74 / 8.9 | .9953 / .9965 | pass; built: UV audit 0, tube chords 8.6 mm outside the installed tube, vest root-lift flag |
| a3 | a2 + tube guard 0.5 mm | 9,221 (-17.6 %) | 2.69 / 8.9 | .9953 / .9965 | pass; built: every gate equal (fallback, `export/cand_a3/`) |
| **b** | **set b (halo 4 mm), hair .6, legs .55, tube guard 1.5 mm** | **8,991 (-19.7 %)** | **2.74 / 8.9 (AttackMelee:9)** | **.995 / .9964** | **PASS, picked; every gate equal** |

`export/cand_a60/` and `export/cand_a2/` are superseded (kept as records of the two faults above).

## Gates, installed -> b r60 (`scripts/gates.sh`: the creature's own gate scripts; `review/gates_before/`, `review/gates_b60/`)
- **UV audit** (`../claude_shared/reduction_uv_audit.py`, `review/uv_audit_b60.json`): **0 escaping LOD0 faces in both primitives**.
  LOD1-3 (the LOD tool's decimate, not gated): body 124 / 108 / 53 (installed 103 / 123 / 59), head 115 / 141 / 67 (installed 76 / 133 / 100).
- Arm and hand (`--outer-only`): 0 frames > 1 cm, both hands, every clip, both; finger stretch maxima equal or lower (Talk R 2.25 -> 1.96,
  Death R 2.82 -> 2.16), minima +0.0-0.1.
- Jitter vs MM9's untouched clips: 0 fails both; shoulder skin within +-0.05 mm/f2 (Running 0.45 -> 0.38).
- Sleeve poke: 0 mm, 0 frames, both sides, every clip, both.
- See-through (`scripts/see_through.sh`, the creature's gate, every clip every 3rd frame, 16 views; worst px): boots 0/0, collar 7/7,
  head 12 -> 11, sleeve L 4/4 (frames 98 -> 92), sleeve R 7/7 (105 -> 99), torso 19/19 (frames 17 -> 23, the same AttackMelee 12 slit
  the creature README leaves open), trousers L 1/1, trousers R 0/0.
- Linings (`scripts/lining_gate.py`, rewritten here: paired lining vertices against the painted outer cloth): equal in every clip (largest
  2.99 mm Death both; AttackMelee 13 -> 12 vertices). Tube against the installed tube: within 1.2 mm at rest (guard 1.5), up to 3.4 mm in
  Hit, 5.5 mm AttackMelee (the installed tube folds into itself by 5.5 mm there too).
- Tube visibility (`scripts/tube_visible.py`, new: tube points whose ray reaches any of the 16 cameras through back faces only): the tube
  shows through the belt gaps by design; frames with any visible tube point identical in every clip (e.g. Hit 19/19, Talk 25/25).
- Detached parts: 0 detached, the same root-lift / shallow list. Flat shading 0.00 both. Winding 0. Bone lengths: same report. Texture
  quality: body atlas 63.3 % both; head 43.8 -> 43.7 %, fragments 2.1 -> 3.0 %, stretch p90 1.16 -> 1.15.
- LODs (`scripts/lod_check.py`, every frame of every clip; built by `scripts/build_lods.py`: tool ratios 0.5/0.18/0.06, 4 influences,
  soles, crown and corpse contact protected and snapped): height 1.3613 m at every LOD (installed 1.3619, LOD3 1.3515); every clip's
  lowest point at LOD1-3 equal to LOD0 (installed LOD3 floated +0.4..+1.0 cm in most clips); no stretched faces.

## Review
Viewer (installed and reduced, all three tiers, tier e with the unchanged ear attachment on `Bip01 ElfEars` (`scripts/viewer_ears.py`),
all 10 clips; `run_creature_review.py check`: 60 switches, 0 failed, no console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_peasantboy_reduce_claude/review/viewer/  (models `inst_a` / `red_a`, `inst_b` /
`red_b`, `inst_e` / `red_e`).
Sheets read (installed above/left, b60 below/right): `review/sheet_face_b60.png` (front close-up, 3/4, true profile, low 3/4, party; all
three boys: faces identical, hair the same) and `review/sheet_face_diff_b60.png` (face skin black in all 15 views; only the hair shading
facets differ), `review/sheet_body_b60_b.png` (Standing front / 3-4 / back, Walking, Fidget, Death), `review/close_b60_a_hands.png` (both
hands outside, R hand front), `review/close_b60_a_1.png` (vest skirt front / back, sleeve outside, boots and wraps),
`review/close_b60_e_2.png` (Running, Talk, AttackMelee, Hit), `review/close_b60_b_3.png` (hair from above and behind, shoulders, AttackMelee),
`review/ladder_sheet_b.png`. Generated, not opened: `review/sheet_body_b60_{a,e}.png`, `review/close_b60_{b,e}_hands.png`,
`review/close_b60_{b,e}_1.png`, `review/close_b60_{a,b}_2.png`, `review/close_b60_{a,e}_3.png`.
Look at: the fingertips and knuckles (hands at 0.6: slightly more angular tips, every finger kept), the hair outline from above (a touch more
polygonal at the crown's edge).

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_peasantboy_reduce_claude/before/mm9_peasantboy.glb REA_NODE=PeasantBoy $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/twins.py; $G scripts/tex_extract.py; HALO=0.004 SCALP=0.025 $G scripts/make_sets_boy.py b
SCALP=0.025 $G scripts/make_sets_boy.py a      # lining_gate.py / tube_clearance.py read the parts of set a
MP_ZTOL_MM=1.5 MP_DMAX_MM=3.5 MP_CHART=1 MP_AUDIT=1 MP_W5=4 MP_SEAM_GROUPS=1 MP_ZERO_GROUPS=6 SETS=b \
  MP_GROUPS=1:0.6,2:0.6,3:0.55,5:0.5,6:0.4 scripts/run_mp.sh b 0.6
scripts/build_mp.sh mp_b_r60 export/cand_b60/mm9_peasantboy.glb   # swap_mp -> build_lods -> creature's shrink_shadow_lods -> carry_variants -> fix_winding -> restore_materials
$G ../claude_shared/reduction_uv_audit.py export/cand_b60/mm9_peasantboy.glb before/mm9_peasantboy.glb --json review/uv_audit_b60.json
scripts/gates.sh export/cand_b60/mm9_peasantboy.glb b60; $G scripts/lining_gate.py export/cand_b60/mm9_peasantboy.glb review/gates_b60/lining.json
scripts/see_through.sh export/cand_b60/mm9_peasantboy.glb b60; REA_NODE=PeasantBoy $BL -P scripts/lod_check.py -- $PWD/export/cand_b60/mm9_peasantboy.glb b60
$BL -P scripts/tube_visible.py -- $PWD/export/cand_b60/mm9_peasantboy.glb $PWD/review/gates_b60/tube_visible.json
python3 scripts/see_compare.py before b60; python3 scripts/lod_compare.py installed b60
$G scripts/viewer_tiers.py export/cand_b60/mm9_peasantboy.glb red; $G scripts/viewer_ears.py work/viewer_red_th_e.glb   # same for before/ -> inst
python3 scripts/make_viewer_manifest.py b60 inst_a=..=work/viewer_inst_th_a.glb red_a=..=work/viewer_red_th_a.glb ... (b, e)
scripts/shots.sh; scripts/close_shots.sh; scripts/close_shots2.sh; $G scripts/shot_sheets.py b60; $G scripts/face_diff_sheet.py b60
$G scripts/close_sheet.py b60 <tier> c8,c9,c10,c5 review/close_b60_<tier>_hands.png   # and _1 (c12,c13,c14,c4), _2 (c15,c16,c17,c19), _3 (c18,c11,c6,c7)
```
Install (orchestrator, on the OK): `check_winding.py export/cand_b60/mm9_peasantboy.glb` (0), `tools/install_model.py
export/cand_b60/mm9_peasantboy.glb --world mm9 --name mm9_peasantboy.glb` (the ear attachment stays as installed), the
`mm9_actor_models_build_every_binding` regression, and add to `../mm9_peasantboy_claude/README.md`: "LOD0 reduced post-install on <date>
by `mm9_peasantboy_reduce_claude`; a rebuild from this project must re-run that reduction". Rollback: `before/mm9_peasantboy.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (frames, gates and viewer
stills only); LOD1-3 and shadow meshes by eye (numbers only); the eye/mouth close-ups at the user's zoom (the face triangles are the
installed ones and the face diff is black); robe/legs gate (the creature project has none for this body).
