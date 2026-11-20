# MM9 half-orc townsman PeasantHOM1 + HOM2 (`mm9_phom1.glb`, ledger row 84) reduction: candidate c r50 ready for review (2026-11-05)

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) /
[REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-2 townsfolk: relaxed keep set,
face exact), ledger row 84 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:peasanthom` (owner
peasanthom-reduce-20261105); the creature leases `mm9:peasanthom1` and `mm9:peasanthom2` were free. Source: the installed
`assets_source/worlds/mm9/models/mm9_phom1.glb` (sha256 d79023f04c98), copied to `before/` (the rollback source). No Meshy, no credits,
no repaint. **Not installed.** `../mm9_peasanthom1_claude/` and `../mm9_peasanthom2_claude/` were only read (their gate scripts,
`shrink_shadow_lods.py` and `v2/work/mm9_phom1_clips.glb` run in place).

**Family:** PeasantHOM2 is not its own GLB. `../mm9_peasanthom2_claude/` added tier `phom2_a` (own body and head colour + normal
images) to HOM1's approved `mm9_phom1.glb` (same mesh, same UVs). One cut serves rows 57, 58, 60 (HOM1 `phom1_a`, `phom1_b`) and
59 (HOM2 `phom2_a`); the ledger has no separate HOM2 row. All three tiers were guarded and checked.

| | LOD0 | body prim PHOM1_A | head prim PHOM1Head_A | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|
| installed | 7,853 | 3,536 | 4,317 | 3,926 | 1,412 | 470 |
| **c r50 (`export/mm9_phom1.glb` = `export/mm9_phom1_c50.glb`, sha256 0deb8280a2bb)** | **6,631 (−15.6 %)** | 2,910 | 3,721 | 3,313 | 1,192 | 396 |

Cut per group: hands 1,310 → 790 (0.6, every finger; 88 graft/cuff faces exact), back of the hair bowl 254 → 178 (0.7),
trousers/boots 1,430 → 858 (0.6), shirt/vest 321 → 267 (the guards stop it). Every vertex of the candidate is an installed vertex
(positions, normals, UVs, joints, weights are the installed bytes; only index buffers changed). Clips (12), skin, nodes, materials,
region ramps, `KHR_materials_variants` (3 tiers), all 12 images: identical (`same_clips.py`).

## Measured first: protected share
Parts (`scripts/analyze.py`): body prim = shirt/vest/sleeves 1,568, trousers 671, boots 626/620, chest toggle 19, two cuff-lining
strips 16/16 (no linings otherwise: `twins.py` finds 0 pairs). Head prim = one shell 2,014 (face skin, ears, neck and the painted
bowl hair: no separate hair mesh), horns 208/198, eyes 124/110, mouth/tusk pieces 108/101/56, MPFB hands 699/699.
The shell is split by the head region mask (`scripts/head_probe.py`: about 630 faces fully hair): face skin, ears, neck and two
rings into the hair stay exact; only 254 hair faces (back and top of the bowl) are free. Horns, eyes, mouth/tusks kept whole.
Set a protected 41.6 %; the final set c 52.6 % (4,132 faces); ~15 % was reachable from the hands, legs and hair.

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`, PeasantM7d's copy)
Chart guard `MP_CHART=1`; texture guard over all three tiers (A = phom1_a, B = phom1_b with the region ramps applied by the engine
rule, C = phom2_a's own images) and the region mask (`scripts/tex_extract.py`, `MP_TIERS=ABCM`), texture weight 4, seam slides on
the hands, every clip at 10 Hz, distance guard 6 mm (8.5 mm on shirt and legs; PeasantM7d's 5/7 mm scaled to 2.27 m).

Keep set (`scripts/make_sets_hom.py`): head shell skin by mask + 2 rings, horns, eyes, mouth/tusks; small pieces; collar (1 cm of
the head prim); graft junction and cuffs (1.5 / 4 cm of a hand vertex); soles; hand contact (every face a hand comes within 4 cm of
in any clip, `hand_contact_dm2.py`: 44); shoulder cloth (Clavicle/UpperArm-dominated: the jitter gate's shoulder skin, as
PeasantM7d b); cloth within 1 cm of the chest toggle. Set b adds `PAINT` (`work/paint_keep.npy`: every shirt/vest face with a
vest-border texel, body mask alpha, or a red belt texel of the phom2_a paint: 457). Set c adds `HEM=0.50,0.68` (trousers hem and boot
tops: 406).

## Ladders (limits for 2.27 m: p99 ≤ 6.81 mm, max ≤ 34 mm, IoU ≥ .98, SSIM ≥ .93; `review/ladder_sheet_<label>.png`)
| ladder | change | LOD0 | p99 / max mm | IoU / SSIM | result |
|---|---|---:|---|---|---|
| a | hands .6, legs .6, hair .7, shirt r50/r65 (identical: guards) | 6,317 (−19.6 %) | 6.30 / 18.5 | .992 / .995 | built a50: UV audit 0, numeric gates equal; **rejected**: the right end of HOM2's belt (phom2_a) and of the vest hem border (phom1_a) turned into a dark wedge on the left flank (c13 close-up); see-through trousers R 125 → 139, L 114 → 121 px. Export deleted |
| b | a + painted bands (vest border, belt) exact | 6,487 (−17.4 %) | 6.08 / 18.5 | .992 / .996 | ladder pass; not built (legs as a: same trousers regression) |
| **c** | **b + trousers hem / boot tops exact** | **6,631 (−15.6 %)** | **5.49 / 22.1** | **.993 / .996** | **PASS, picked** |

## Gates, installed → c r50 (`scripts/gates.sh`, `scripts/see_through.sh`; `review/gates_before/`, `review/gates_c50/`)
- **UV audit** (`review/uv_audit_c50.json`): **0 escaping LOD0 faces in both primitives**. LOD1-3 escapes come from the LOD tool's
  decimate, near the installed file's own (body/head: LOD1 180/137 vs 147/119, LOD2 115/150 vs 117/143, LOD3 46/88 vs 63/91).
- Exact parts (`scripts/exact_head.py`, `review/exact_c50.txt`): every kept face present with identical corner bytes; of the head
  part only the 254 free hair faces changed (face skin, ears, neck, eyes, mouth/tusks, horns exact).
- Arm and hand (`--outer-only --exact`, 48 fps): hands 0 frames over 1 cm in every clip (Fidget L 0.8 cm as installed); forearms
  equal (Fidget R 2.1, AttackMelee R 1.4 cm); finger stretch max Fidget R 3.47 → 2.87, others equal or within 0.1.
- Jitter vs MM9's untouched clips: 0 fails both; shoulder skin and arm numbers identical in every clip.
- Sleeve poke: 0 frames over tolerance both (Death L 0.2 mm both).
- See-through (creature's `see_through_gate.py`, every 3rd 30 fps frame, 16 views; worst px installed → c50): sleeve R 24 → 23,
  sleeve L 33 → 33, torso 43 → 44, collar 10 → 10, trousers R 125 → 125, **trousers L 114 → 118** (the same single Running frame 0
  from 20° above at the hem over the boot top; `work/st_trousersL_c50.png`: the same hole, a few edge pixels), boots 0 → 0, unattributed
  1 → 1 px. No lining added (user decision pending on HOM1/HOM2 linings).
- Detached 0 both (15 components). Flat 0.00 both. Winding 0. Bone lengths 12 checked, 0 stretching. Texture quality: body atlas
  60.1 % both, stretch p90 1.12 → 1.13; head 46.8 % both, fragments 2.9 → 3.5 %.
- LODs (`scripts/lod_check.py`, every frame of every clip; `scripts/build_lods.py`: tool ratios 0.5/0.18/0.06, 4 influences, soles,
  crown and corpse contact protected and snapped, 37 of 37 mapped): height 2.269 m at every LOD; lowest point at LOD1-3 equal to LOD0
  in every clip (Standing 0.0, Dead 0.0, Death −2.17 cm as LOD0); the installed LOD3 floated +0.6 cm in Standing and +0.9 cm in Dead.
  0 stretched faces at every LOD, both.

## Review
Viewer (installed and reduced, all three tiers, all 12 clips; `run_creature_review.py check`: 72 switches, 0 failed, no console
errors, `review/viewer_check.txt`): http://127.0.0.1:8912/level_generation/creatures/mm9_peasanthom_reduce_claude/review/viewer/
Sheets read (installed left/above, c50 right/below): `review/sheet_face_c50.png` and `review/sheet_face_diff_c50.png` (front close-up,
3/4, profile, low 3/4, party; all three tiers: face skin, ears, horns black in all 15 diffs, only the back of the hair bowl differs),
`review/sheet_body_c50_{a,b,c}.png` (Standing front/3-4/back, Walking, Fidget, Death), `review/close_c50_a_{1,2,3,4}.png`,
`review/close_c50_c_{1,2,4}.png`, `review/close_c50_b_1.png` (arms, trousers front/back, Running, boots, Talk, back, Hit, both hands
with fingertips, hair from behind above, L cuff, chest toggle/belt buckle, boots front), `review/ladder_sheet_a.png`, `review/sets_a_{body,head}.png`;
for a50: `review/sheet_face_a50.png`, `review/sheet_face_diff_a50.png`, `review/sheet_body_a50_{a,b,c}.png`, `review/close_a50_{a,c}_*.png`,
`work/c13_crop.png` (the belt wedge), `work/st_trousers_cmp.png`. Generated, not opened: `review/close_c50_c_3.png`.
Look at: the hand backs (0.6: a few flatter planes in the shading, outline and fingers the same), the back of the hair bowl (0.7),
the trousers above the knee (0.6).

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_peasanthom_reduce_claude/before/mm9_phom1.glb REA_NODE=PHOM1 $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/twins.py; $G scripts/tex_extract.py; $G scripts/head_probe.py
$G scripts/hand_contact_dm2.py; cp work/hand_contact.npy work/hand_contact_0.04.npy
RING=2 HANDS=hand_contact_0.04.npy SHOULDER=1 SMALLC=0.01 $G scripts/make_sets_hom.py a; $G scripts/paint_keep.py
RING=2 HANDS=hand_contact_0.04.npy SHOULDER=1 SMALLC=0.01 PAINT=paint_keep.npy HEM=0.50,0.68 $G scripts/make_sets_hom.py c
REA_HEIGHT_M=2.27 MP_DMAX_MM=6 MP_DMAX_GROUPS=0:8.5,3:8.5 MP_CHART=1 MP_W5=4 MP_SEAM_GROUPS=1 SETS=c MP_GROUPS=1:0.6,3:0.6,6:0.7 scripts/run_mp.sh c 0.5
scripts/build_mp.sh mp_c_r50 export/mm9_phom1_c50.glb   # swap_mp -> build_lods -> HOM1's shrink_shadow_lods -> carry_variants -> fix_winding -> restore_materials
$G ../claude_shared/reduction_uv_audit.py export/mm9_phom1_c50.glb before/mm9_phom1.glb --json review/uv_audit_c50.json
$G scripts/exact_head.py export/mm9_phom1_c50.glb c; work/queue_c50.sh   # gates.sh, see_through.sh, lod_check.py
for t in a:phom1_a b:phom1_b c:phom2_a; do $G ../mm9_peasantm7d_claude/scripts/viewer_variant.py export/mm9_phom1_c50.glb work/viewer_red_${t%%:*}.glb ${t#*:}; done
$G scripts/make_viewer_manifest.py c50 "inst_a=..=work/viewer_inst_a.glb" "red_a=..=work/viewer_red_a.glb" ... (b, c)
HEADUP=0,0.09,0.12 scripts/shots.sh; scripts/close_shots.sh; $G scripts/shot_sheets.py c50; $G scripts/face_diff_sheet.py c50
$G scripts/close_sheet.py c50 a c0,c1,c2,c3 review/close_c50_a_1.png   # ... _2 .. _4, tier c, tier b
```
`scripts/viewer_shots.mjs` is the m424 shot script with a 3-minute ready timeout (the 33 MB GLBs timed out at 30 s under load).

Install (orchestrator, on the OK): `check_winding.py export/mm9_phom1.glb` (0), `tools/install_model.py export/mm9_phom1.glb --world mm9
--name mm9_phom1.glb`, the `mm9_actor_models_build_every_binding` regression, and add to `../mm9_peasanthom1_claude/README.md` and
`../mm9_peasanthom2_claude/README.md`: "LOD0 reduced post-install on <date> by `mm9_peasanthom_reduce_claude`; a rebuild from this
project must re-run that reduction" (HOM2's `add_tier.py` appends to the installed GLB, so a later HOM2 tier rebuild must start from
the reduced file). Rollback: `before/mm9_phom1.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (frames, gates and
viewer stills only); LOD1-3 and shadow meshes by eye (numbers only); tier b's close-ups beyond hands, boots, chest and hair (tier b
differs from a only in ramp colours, the geometry is shared).
