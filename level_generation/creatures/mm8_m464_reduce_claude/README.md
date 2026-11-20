# MM8 Vampire female peasant (`m464`, Vampire Female Peasant A/B/C) reduction (2026-10-19)

User: "pick 5 more to do" (next batch after the Troll, Dark Elf peasant, Unicorn, Thunderbird and Ether Knight).
Default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), including its MM8 batch lessons. No retexture,
no Meshy credits. Not installed; awaiting user review.

Source: the installed `assets_source/worlds/mm8/models/mm8_m464.glb`, identical to `mm8_m464_claude/export/`
(v2-arms), copied to `work/mm8_m464_source_pre_reduce.glb` (rollback source). One body node `Body`, three
material variants (`VampirePeasant_A/B/C`), merged head/body 2080x1024 atlas with region mask, 57 joints,
4 influences, seven clips. No attachments. Scripts start from `mm8_m424_reduce_claude/` (parent-transform fix,
exact source weights, coincident-vertex handling); `lod_check.py` comes from `mm8_m604_reduce_claude/` and
`err_lock.py` from the Troll.

## Regions (`make_groups.py`)

Weld 6,421 -> 543 open edges, no coincident vertices with other weights. Height 1.655 m: limits p99 4.97 mm, max
24.8 mm.

| label | piece | faces | picked ratio |
|---|---|---:|---|
| 1 | face, ears and neck skin (head atlas) | 2,020 | 80 % |
| 2 | hair (separate head-atlas piece) | 1,244 | 70 % |
| 3 / 4 | left / right hand | 612 / 608 | 70 % each |
| 0 | jacket, shirt, sleeves (3,435), trousers and boots (3,751) | 7,186 | remaining budget |

Kept exactly (`work/keep_k.npy`, 2,745 faces):
- eyes and teeth (pieces of up to 250 faces, 49);
- the white lace of the jacket panels and the trouser side stripes (`trim_faces.py`, no ring), and the gold boot
  studs with one ring;
- faces around the leg points that missed the source by over 14 mm in Walking/Running/Death (`err_lock.py`,
  13 vertices at the knees and upper thighs);
- one round of light and dark fleck locks (`dark_slivers.py`, now with `REA_LIGHT=1` for light flecks);
- the green/black waistband boundary with one ring (`boundary_faces.py`, z 0.82-1.05 m);
- two spot locks (`spot_lock.py`): a dark slash on the left neck skin at a head-atlas chart border, and a pink fleck
  at the left collar tip. Neither averaged check found them; close-ups did.

## Ladder

| config | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| a: hands kept, face/hair 70 % | 70 / 62 / 55 % | 8,203 / 7,265 / 6,445 | 2.84 / 25.1 ... 4.73 / 25.8 | 0.992-0.984 | 0.998-0.994 | fail: max at knees and thighs; boot studs cut at 62 % |
| c = a + studs + error lock | 70 / 65 / 62 / 57 % | 8,203 ... 6,797 | 3.04 / 13.7 ... 5.17 / 17.3 | 0.992-0.983 | | 70-62 % pass; the lace panels lose shape, skin fleck on the black shirt |
| d = c + lace | 70 / 66 / 62 % | 8,203 / 7,733 / 7,265 | 3.53 / 15.8, 4.6 / 18.3, 6.26 / 25.4 | | | 70 / 66 % pass; shirt fleck remains |
| f = d + fleck locks, hands 70 % | 70 / 68 / 66 % | 8,199 / 7,965 / 7,731 | 3.57 / 15.8, 4.1 / 16.1, 4.83 / 18.3 | 0.989-0.985 | 0.997-0.996 | pass; waistband blocks chopped, eyes slightly narrower |
| g = f + waistband, face 80 % | 72 / 70 / 68 % | 8,433 / 8,199 / 7,965 | 3.93 / 16.1, 4.71 / 18.3, 5.65 / 25.4 | | | 72 / 70 % pass; neck slash and collar fleck |
| **k = g + two spot locks** | **72 %** | **8,433** | **4.07 / 16.1** | **0.988** | **0.997** | **picked** |

- **Pick 72 %:** at 70 % p99 is 4.76 mm against the 4.97 mm limit, and the leg error rises to 21.7 mm in Death.
  The kept lace, studs and waistband take about a fifth of the mesh, so the remaining clothing runs out of budget
  quickly below 72 %.
- **Lace and studs:** thin painted line work and dots. Under the collapse the jacket lace changed shape and the boot
  studs were cut in half (`review/close/sheet_a_trims.png`, `sheet_c_trims.png`); kept, they match
  (`sheet_d_tex.png`, `sheet_f_b.png`). The trouser stripes survived either way and are kept with the lace rule.
- **Face at 80 %:** at 70 % the eyelids and lower lid make-up narrowed a little (`sheet_f_a.png`); 80 % matches
  (`sheet_g_tex.png`, `sheet_i_a.png`).
- **Hands at 70 %** (612 / 608 faces, already light): fingers, the hand-on-hip pose and the Fidget hand match
  (`sheet_f_a.png`).
- **Hair at 70 %:** this short hair is a solid cap, not strand cards, and stays closed (`head_back` in every sheet).
- **A chest box lock was tried and dropped** (`sheet_j.png`): keeping a block of shirt faces exactly made ridges
  where the kept and reduced faces meet. The source's small lapel fold at the chest is reproduced slightly
  differently (`sheet_k.png`).
- **Checks at 72 %:** texture drift 0 faces over 40; dark flecks 0 and light flecks 1 at the default thresholds
  (0 visible).

## Normals

Plain smooth. Rendered straight from the GLBs (`scripts/glb_close.py`, `review/glbclose/sheet.png`: face, neck,
chest, back, hands, legs, hair), the installed model and the reduction shade the same. `close_human.py` clears the
welded `source.blend`'s custom normals before rendering the source column.

## Build

`export_cand.py` (Cand_72 of `work/ladder_k.blend`, REA_NODE=Body) -> `swap_lod0.py ... Body` -> `build_lods.py`
(the creature's own settings from `mm8_m464_claude/scripts/export_model.py`: 0.5 / 0.25 / 0.125, 4 influences, no
shadow shrink; protected points: LOD0 vertices within 1 cm of the floor in any Death/Dead frame and the top 5 mm of
the crown, 111 points) -> `carry_variants.py`: `export/mm8_m464.glb`, 6.9 MB (installed 7.7 MB). Textures, variants,
clips and node structure are byte-identical to the installed ones; check_winding: 0 inverted closed parts.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 11,719 | 5,859 | 2,929 | 1,463 |
| reduced | 8,433 | 4,216 | 2,107 | 1,054 |

Shadow meshes match the colour LODs, as installed. `lod_check.py` (REA_NODE=Body): every LOD keeps the 1.654 m
height and 0.757 m width; no face stretches in any clip at any LOD. The lowest point in Death/Dead is -1.8 mm at every
LOD; installed LOD3 reached -6.4 mm. Running is -0.3 mm (installed -0.0).

## Retexture check

- **Texture set:** unchanged (base colour, metal-rough, normal, region mask byte-identical); the reduction keeps UVs.
- **Head vs body skin:** skin-coloured texels, linear luminance median 0.39 for the face set, 0.57 / 0.58 for the
  hands. The face texture is warmer and darker than the hands. This is in the installed model and was accepted with
  it (`mm8_m464_claude/review/shots/front.png`), so no unify step was applied. A head unify like the Phoenix's
  (`unify_head.py`) would brighten the face toward the hands if the user wants them matched.
- **Existing faults:** none found that the reduction exposed. The neck slash and collar fleck were reduction faults
  and are fixed by the spot locks. The hairline is a hard edge, as in the source.
- **Verdict:** no retexture for either half and no local texture fix. No credits spent.

## Review

Viewer `review/viewer/` (installed vs reduced for each tier; tiers baked by `viewer_variants.py` because three.js has
no region ramps): http://127.0.0.1:8912/level_generation/creatures/mm8_m464_reduce_claude/review/viewer/.
`tools/run_creature_review.py ... check`: 42 clip switches, no console errors.

## Status

Installed 2026-10-19 (user: "female peasant ok"). `check_winding.py`: 0 inverted closed parts. Installed with
`tools/install_model.py ... --world mm8` (the rollback source matched the installed GLB byte for byte first);
`OPENYAMM_REGRESSION_FILTER=mm8_vampire_female_peasant ./build/game/openyamm --world mm8 --headless-run-regression-suite actors`:
`mm8_vampire_female_peasant_actor_models_keep_native_roles` passes (`review/regression.log`). Recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).
Rollback: install `work/mm8_m464_source_pre_reduce.glb` with `tools/install_model.py --world mm8`.

Reproduce: `import_source.py` (REA_NODE=Body, REA_GLB=the rollback source) -> `dump_mesh.py` -> `dump_faces.py` ->
`REA_KEEP_HANDS=1 make_groups.py` -> first ladder a (`REA_KEEP_FACES=work/keep_base.npy REA_GROUPS=work/groups.npy
REA_GROUP_RATIOS=1:0.7,2:0.7 REA_HEIGHT_M=1.655 run_ladder.sh a 0.70,0.62,0.55`) -> `TRIM_WHITE=0 trim_faces.py
work/keep_base.npy work/keep_b.npy 1` -> `REA_CAND=Cand_62 REA_ERR_MM=14 REA_LOCK_R=0.02 err_lock.py -- work/keep_b.npy
work/keep_c.npy` -> keep_d = keep_c + `trim_faces.py ... 0` (lace and studs, no ring) -> ladder d -> light and dark
`dark_slivers.py` (`REA_DARK_L=80 REA_DARK_N=4`) on r70/r66 + `REA_MIN_AREA=1e-5 REA_LOCK_R=0.015 drift_lock.py` ->
keep_e -> keep_f = keep_e without the hand labels 3/4 -> `boundary_faces.py work/keep_f.npy work/keep_g.npy 0.82 1.05` ->
`spot_lock.py work/keep_g.npy work/keep_i.npy 0.015
0.027,-0.045,1.422 0.011,-0.063,1.427 0.022,-0.051,1.416` -> `spot_lock.py work/keep_i.npy work/keep_k.npy 0.015
0.131,-0.006,1.351 0.144,0.015,1.367` -> `REA_KEEP_FACES=work/keep_k.npy REA_GROUP_RATIOS=1:0.8,2:0.7,3:0.7,4:0.7
run_ladder.sh k 0.72` -> build as above.

## Anim fix (2026-11-11, MM6–MM8 audit)

Running loop seam closed (pop 0.0776 H -> 0) with `loop_close.py`; details: [mm8_m464_animfix_claude](../mm8_m464_animfix_claude/README.md).
