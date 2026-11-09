# MM9 PeasantDM4 (`mm9_peasantdm4`, dwarf townsman with skullcap and red beard) reduction: candidate h45 ready for review (2026-11-05)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) and
[REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) (prio-2 townsfolk, face exact),
ledger row 32 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:peasantdm4` (owner peasantdm4-reduce-20261104);
the creature's own `mm9:peasantdm4` lease was free. Source: the installed `assets_source/worlds/mm9/models/mm9_peasantdm4.glb`
(sha256 d07208ac9f2e, identical to `../mm9_peasantdm4_claude/export/mm9_pdm4.glb`), copied to `before/` (the rollback source).
No Meshy, no credits, no repaint. **Not installed.** `../mm9_peasantdm4_claude/` was only read.

**Family:** DM4 is its own body (the creature README: own Smart Topology mesh, not a variant). DM1 and DM2 share its skeleton only;
DM3 is a variant of DM1's body. Nothing here is shared with the other dwarf-men rows.

| | LOD0 | LOD1 | LOD2 | LOD3 | height (all LODs) |
|---|---:|---:|---:|---:|---:|
| installed | 12,933 | 6,442 | 2,315 | 768 | 1.238 / 1.238 / 1.240 / 1.235 m |
| **h45 (`export/mm9_peasantdm4.glb`, sha256 49829f6a9f72)** | **10,851 (-16.1 %)** | 5,402 | 1,939 | 642 | 1.238 m every LOD |

Per part (LOD0): body primitive 7,905 -> 7,061 (2,103 faces exact: rim strips, unmatched linings, soles, collar under the beard,
small pieces, one arm-gate lock; cloth 3,026 -> 2,596; linings 2,776 -> 2,362, re-emitted); head primitive 5,028 -> 3,790 (face
skin window, neck-cap twins, beard contact with the chest, forearm stubs and the beard-tip lock exact = 1,631; MPFB hands 1,276 ->
766 with every finger; hair and beard 997 -> 605; cap 590 -> 414 plus its lining 532 -> 372, re-emitted).
Every output vertex is an installed vertex (positions, normals, UVs, joints, weights are the installed bytes; only index buffers
changed). Clips (13), skin, nodes, materials, all 6 images: byte-identical (`same_clips.py`). One skin, no tiers.

## Linings (the part that needed new code)
The creature lined most of its cloth (`linings.sh`: rim_lining.py bands, 3 mm or 0.5 mm behind, clipped near other cloth; the
cap lining; twin patches), then `body_reweight.py` changed weights on the chest, so twins are near-equal, not identical, and band
borders overlap. `scripts/twins_dm4.py` pairs every lining face with its outer face (painted copies by identical UV, one-texel
linings by nearest opposite-facing vertex with weights within L1 0.35; triangle pairs, quads as fallback), splits the linings into
bands (connected, one-texel and painted never mixed) and writes a per-band corner map whose lining corner is the band's own GLB
vertex with the nearest UV. Check: every pair's mapped corners land exactly on its own lining face (residual 0.00 mm). `mpqem.py`
cuts each (group x band) subset on its own (band borders locked) and re-emits the lining as the reversed band twins of the
surviving outer faces. Unpaired one-texel faces (rim strips 650+, 260 unmatched) and painted faces within 6 mm of them stay exact.
First tries without the per-band map put mixed-texel or wrong-seam corners on re-emitted faces (UV audit 207 + 192 escaping), fixed.

## Ladders (limits for 1.234 m: p99 <= 3.70 mm, max <= 18.5 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_<label>.png`)
| ladder | change | LOD0 | p99 / max mm | result |
|---|---|---:|---|---|
| a | ratio only (r50/r40), hands .6, hair .75, cap .75, legs .6 | 9,991 | 8.37 / 30.1 (RubBeard) | fail: narrow lining bands forced 5-15 mm collapses |
| b-f | error cap per collapse (`MP_MAXRMS`) 1.2 / 0.9 / 1.0 mm; hair, cap .65-.6 | 10,687-11,017 | 4.0 fail; 3.30-3.76 | f (cap 1.0, hair .6, cap .65): 10,789, 3.61, pass |
| g/h | f + error locks: beard tip (stretch +0.05 in X), one torso lining face (arm gate) | **10,851** | **3.59 / 15.5 (Running:3)** | **PASS, picked** (IoU .9975, SSIM .9925) |

Chart guard on (`MP_CHART=1`, 12 subdivisions), texture guard (100 / 45), texture weight `MP_W5=4`, hands with seam slides.

## UV chart audit (hard gate)
`review/uv_audit_mm9_peasantdm4.json`: **0 escaping LOD0 faces** in both primitives. LOD1-3 (Blender decimate) 174/204, 167/160,
44/78 vs the installed 159/169, 180/161, 56/102.

## Gates, installed -> h45 (`scripts/gates.sh`: the creature's own scripts; `review/gates_before/`, `review/gates_h45/`)
- Arm/hand (`--outer-only --exact`, 48 fps): 0 frames > 1 cm in every clip, both sides; Running L forearm 1.0 cm both, RubBeard
  0.8 both; new 0.2 cm single hand contacts in Walking L (AttackMelee L 0.2 as installed); finger stretch maxima equal, p99 up to
  +0.05 (hands at 0.6). (f45 had Running R forearm 5.6 cm: a re-emitted lining face read as the surface, the probe
  `scripts/arm_probe_dm4.py` NO_TEXEL=1 showed 0 without linings; locked in h.)
- Jitter vs the mirrored MM9 clips: 0 fails both. Sleeve poke: rest 0 both; Death R 27.4 -> 27.5 mm (the same 1 vertex, 9 frames).
- See-through (creature's settings, every 2nd frame + Running 12/15, 16 views; worst px): sleeve R 10 -> 9, sleeve L 17 -> 17,
  boot L 11 -> 12, boot R 12 -> 12, head 16 -> 17 (cap silhouette slivers), torso 10 -> 11 (frames 54 -> 64), collar 8 -> 8,
  trousers 0. Within a pixel everywhere.
- Beard (`scripts/beard_gate_dm4.py`, new): edge stretch per clip equal to the installed in every clip (h; f45 had X 1.851 -> 1.905,
  Cower 1.531 -> 1.555, fixed by the lock); beard-chest contact gap and approach equal (Standing +1.20 -> +1.21 cm).
- Chest shear p95 (`chest_shear.py`): Talk 2.15 -> 2.55, Hit 2.00 -> 2.26, Cower 1.61 -> 1.73, AttackMelee 6.39 -> 6.48 cm, others
  equal or lower. Every surviving vertex is an installed vertex with its installed weights, so each vertex shears exactly as before;
  the p95 is taken over fewer vertices (758 -> 740s). Not a motion change; noted for the reviewer.
- Lining through cloth (`scripts/lining_gate.py`, new): most lining vertices out per frame lower in every clip; max outward distance
  mixed (Standing 5.2 -> 6.2, Hit 6.1 -> 7.4, Fidget 11.0 -> 6.2, RubBeard 10.8 -> 7.8 mm); the installed already reads 5 mm at rest
  (nearest face of another layer), so this is a relative check; the see-through gate shows no new holes.
- Detached: same single part (L hand) worst 1.06 -> 1.09 cm, detached poses 166 -> 60; three new "concealed" 9-10-face small pieces (calf, skirt ring)
  (hidden from every direction). Flat shading 0.00 both. Bones 12 checked, 0 stretching. Winding 0. Texture quality: body 54.6 %
  as installed, head 40.9 -> 40.8 %, head stretch p90 1.32 -> 1.35.
- LODs (`scripts/lod_check.py`; built by `scripts/build_lods.py`, soles within 3 cm, crown and corpse contact protected, snapped):
  LOD1-2 lowest point per clip within 1 mm of LOD0; LOD3 Walking -0.66 cm (installed -0.05), Death -0.27 (installed -0.39), others
  within 1 mm. Stretched faces: LOD0 as installed (3-6), LOD1-3 0-2.

## Review
Viewer (installed and reduced, every clip; `run_creature_review.py check`: 26 switches, 0 failed, no console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_peasantdm4_reduce_claude/review/viewer/
Sheets read: `review/sheet_face_h45.png` (front close-up, 3/4, true profile, low 3/4, party), `review/sheet_face_diff_h45.png`
(face skin black in all five; cap, hair and beard shading differ), `review/pair_face_f2_f45.png` (profile at full size),
`review/close_h45_{1,3,4}.png` (Running, boots, Talk, both hands outside/front, cuffs, cap from behind above, beard from below,
sleeve band), `review/close_f45_{0,1,2,3,4}.png` (same shots on f45, which differs only by the two lock areas),
`review/sheet_body_f45_a.png`, `review/sets_a_{head,body,hands}.png` (keep/group maps). Not opened: `review/close_h45_{0,2}.png`,
`review/sheet_body_h45_a.png`.
Look at: the fingertips (hands at 0.6), the back of the hair and the beard's lower edge in profile, the cap crown.

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G="../claude_shared/gltf_venv/bin/python -W ignore"
REA_GLB=level_generation/creatures/mm9_peasantdm4_reduce_claude/before/mm9_peasantdm4.glb REA_NODE=PeasantDM4 $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; scripts/cap.sh /snap/bin/blender -b --factory-startup -P scripts/dump_blend_parts.py -- $PWD/../mm9_peasantdm4_claude/work/rigid_v3n.blend
$G scripts/glb_parts_dm4.py; $G scripts/twins_dm4.py; $G scripts/tex_extract.py
LOCKS=work/beard_culprits_f45.npy BLOCKS=work/arm_lock_f45.npy $G scripts/make_sets_dm4.py c
MP_MAXRMS=1.0 MP_CHART=1 MP_W5=4 MP_SEAM_GROUPS=1 SETS=c MP_GROUPS=1:0.6,2:0.6,3:0.65,4:0.5 scripts/run_mp.sh h 0.45
SOLE=0.03 scripts/build_mp.sh mp_h_r45 export/mm9_peasantdm4.glb   # swap_mp -> build_lods -> shrink_shadow_lods (creature's) -> fix_winding
$G ../claude_shared/reduction_uv_audit.py export/mm9_peasantdm4.glb before/mm9_peasantdm4.glb --json review/uv_audit_mm9_peasantdm4.json
scripts/gates.sh export/mm9_peasantdm4.glb h45; scripts/see_through.sh export/mm9_peasantdm4.glb h45
REA_NODE=PeasantDM4 $BL -P scripts/lod_check.py -- $PWD/export/mm9_peasantdm4.glb h45
scripts/shots.sh; scripts/close_shots.sh; $G scripts/shot_sheets.py h45; $G scripts/face_diff_sheet.py h45
```
(`work/beard_culprits_f45.npy` from `scripts/beard_culprits.py` on f45; `work/arm_lock_f45.npy` = the torso lining face found by
`scripts/arm_probe_dm4.py`.) Install (orchestrator, on the OK): `check_winding.py export/mm9_peasantdm4.glb` (0),
`tools/install_model.py export/mm9_peasantdm4.glb --world mm9`, the `mm9_actor_models_build_every_binding` regression, floor audit,
and add to `../mm9_peasantdm4_claude/README.md`: "LOD0 reduced post-install on <date> by `mm9_peasantdm4_reduce_claude`; a
rebuild from this project must re-run that reduction". Rollback: `before/mm9_peasantdm4.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (stills and gates
only); LOD1-3 and shadow meshes by eye (numbers only); the eye/mouth close-ups at the user's zoom (face triangles are the installed
ones and the five-view diff is black).
