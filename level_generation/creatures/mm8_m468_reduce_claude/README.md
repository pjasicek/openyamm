# MM8 Vampire (`m468`, Vampire Minion / Vampire / Greater Vampire) reduction (2026-10-19)

User: "OK do those 5" (Lizardman Warrior, Vampire, Smuggler, Gog, Cleric). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), including its MM8 batch lessons. No retexture, no Meshy credits.
Not installed; awaiting user review.

Source: the installed `assets_source/worlds/mm8/models/mm8_m468.glb`, identical to `mm8_m468_claude/export/`,
copied to `work/mm8_m468_source_pre_reduce.glb` (rollback source). One mesh node `M468`, three material variants
(`M468_A/B/C`, only the trousers change colour through the region mask), merged head/body 2080x1024 atlas, 4
influences, nine clips. No attachments. Scripts start from `mm8_m464_reduce_claude/` (the Vampire female peasant:
parent-transform fix, exact source weights, coincident-vertex handling, fleck and spot locks); `region_error.py` and
`lod_views.py` come from `mm8_m604_reduce_claude/`.

## Regions (`make_groups.py`)

Weld 6,330 -> 586 open edges, no coincident vertices with other weights. Height 1.64 m: limits p99 4.92 mm, max
24.6 mm.

| label | piece | faces | picked ratio |
|---|---|---:|---|
| 1 | head, ears and neck skin (head atlas) | 2,080 | 80 % |
| 2 | hands and long clawed fingers | 2,371 | 35 % |
| 3 | bare clawed feet and toes | 1,510 | 35 % |
| 4 / 5 | ragged vest / torn trousers | 1,499 / 900 | remaining budget |
| 0 | body skin (torso, arms, shins) | 539 | remaining budget |

The body skin is already lean; most of the triangles sat in the head, hands and feet.

Kept exactly (`work/keep_h.npy`, 2,260 faces):
- eyes, mouth, fangs and teeth, and the belt with its buckle (pieces of up to 280 faces, 1,369);
- the ragged vest and trouser edges: faces touching an open edge (`rag_edges.py`, 467 + 257). Without them the
  vest's back hem lost its points and pulled skin colour into the hem (`review/close/sheet_b2.png`);
- the leg/foot region border, both sides (`group_border.py`, 119 faces). Decimated separately, the feet and shins
  folded a step into the right ankle front (`sheet_d3.png`);
- nine small spot locks (`spot_lock.py`, R 12 mm) at the faces the drift and fleck checks flagged on the 65 % step:
  a red fleck beside the right claws in Attack, dark flecks at the left hand, light flecks on the vest back.

## Ladder

| config | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| a: head 70 %, hands/feet 55 % | 70 / 62 / 55 % | 7,186 / 6,364 / 5,646 | 3.54 / 20.5, 8.72 / 47.1, 54.9 / 229 | 0.992-0.759 | | 70 % only; the clothing ran out of budget |
| b: head 80 %, hands/feet 45 % | 70 / 66 / 62 % | 7,184 / 6,774 / 6,364 | 3.58 / 17.0, 4.53 / 28.6, 7.02 / 29.3 | 0.993-0.978 | | 66 % fails max at the vest back; hem points lost |
| c = b + ragged edges | 70 / 66 / 63 % | 7,184 ... 6,466 | 3.75 / 20.5, 5.63 / 28.9, 8.33 / 47.1 | | | edges kept but the interiors starve |
| d = c, hands/feet 35 % | 68 / 65 / 62 % | 6,982 / 6,674 / 6,366 | 3.95 / 14.9, 4.44 / 17.0, 5.82 / 28.9 | 0.993-0.982 | | 68 / 65 % pass; right ankle step |
| e = d + leg/foot border | 67 / 65 / 63 % | 6,878 / 6,674 / 6,468 | 4.13 / 17.0, 4.57 / 16.3, 5.62 / 28.9 | 0.992-0.984 | | pass to 65 %; red fleck at the claws |
| f / g = e + a drift-lock round (R 15 mm) | 66 / 65 / 64 % | | 4.69 / 28.6 ... | | | fail: the lock moved the collapse to the back skin under the vest |
| **h = e + nine spot locks** | **66 %** | **6,776** | **4.53 / 20.5** | **0.990** | **0.992** | **picked** (65 %: max 28.6, fail) |

- **Pick 66 %:** the lowest passing step once the visible flecks are locked. A full drift-lock round (f, g) moved
  the error under the vest, as the playbook warns, so only the flagged spots are kept.
- **Hands and feet at 35 %:** the claws, knuckles, toes and toenails match the source in textured and clay close-ups
  at rest and in Attack (`sheet_d1.png`, `sheet_h1.png`).
- **Face at 80 %:** brow ridges, eye sockets, ears, lips and the fang ring match (`sheet_b1.png`, `sheet_e2.png`).
  The ladder a run at 70 % had most of its surface error in the head.
- **Checks at 66 %:** texture drift 0 faces over 40; fleck checks 1 dark and 2 light faces left, all on the vest back
  and front thigh, invisible in close-ups (`sheet_h1.png`, `sheet_h2.png`).

## Normals

Plain smooth. Rendered straight from the GLBs (`scripts/glb_close.py`, `review/glbclose/sheet.png`: face, fangs,
neck, torso front and back, hand, foot), the installed model and the reduction shade the same. Unlike the
Bedraggled Human's head, this source carries no sharper head normals.

## Build

`export_cand.py` (Cand_66 of `work/ladder_h.blend`, REA_NODE=M468) -> `swap_lod0.py ... M468` -> `build_lods.py`
(the creature's own settings from `mm8_m468_claude/scripts/build_lods.py`: 0.5 / 0.25 / 0.125, 4 influences;
protected points: LOD0 vertices within 1 cm of the floor in any Death/Dead frame, the top 5 mm of the crown and the
outer 5 mm on both sides, 229 points) -> `carry_variants.py`: `export/mm8_m468.glb`, 6.2 MB (installed 6.8 MB).
Textures, variants, clips, sockets and node structure are unchanged. check_winding: 0 inverted closed parts.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 10,268 | 5,134 | 2,566 | 1,276 |
| reduced | 6,776 | 3,388 | 1,686 | 839 |

Shadow meshes match the colour LODs, as installed. `lod_check.py` (REA_NODE=M468) on every LOD:
- keeps the 1.70 m height and the 1.24 m claw span;
- no face stretches in any clip;
- the lowest point per clip is the same at every LOD: Death -2.7 mm (as installed), Running -0.5 mm, Hit -0.3 mm,
  Walking -0.1 mm. The soles sit about 2 mm lower than the source, which floated 2.4-3 mm in Standing, Attack, Cast
  and Fidget.

`review/lods/sheet.png` compares all LODs at rest and in Attack. LOD3 at 839 triangles keeps the claws, vest flaps
and toes at least as well as the installed 1,276-triangle LOD3, so the creature's ratios are kept.

## Retexture check

- **Texture set:** unchanged (base colour, metal-rough, normal, region mask); the reduction keeps UVs.
- **Head vs body skin:** skin-coloured texels, linear luminance median 0.36 for the head set and 0.52 for the hands,
  feet and body. The head texture is darker (eye sockets, wrinkles and veins painted into it), and in renders the face
  reads as the same pale blue as the body (`review/glbclose/sheet.png`). This is the installed model the user
  accepted, so no unify step was applied.
- **Existing faults:** none found. The white specks on the vest are painted wear in the source texture.
- **Verdict:** no retexture for either half and no local texture fix. No credits spent.

## Review

Viewer `review/viewer/` (installed vs reduced for each tier; tiers baked by `viewer_variants.py`):
http://127.0.0.1:8912/level_generation/creatures/mm8_m468_reduce_claude/review/viewer/.
`tools/run_creature_review.py --project level_generation/creatures/mm8_m468_reduce_claude check`: 54 clip switches,
no console errors.

## Status

Installed 2026-10-19 (user: "vampire ok"). `check_winding.py`: 0 inverted closed parts. Installed with
`tools/install_model.py ... --world mm8` (the rollback source matched the installed GLB byte for byte first).
`./build/tests/openyamm_unit_tests --test-case='*mm8 Vampire*'` (no headless regression case): 2 test cases, 183 assertions pass (`review/unit_tests.log`). Recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).
Rollback: install `work/mm8_m468_source_pre_reduce.glb` with `tools/install_model.py --world mm8`.

Reproduce: `REA_NODE=M468 REA_GLB=<rollback source> import_source.py` -> `dump_mesh.py` -> `dump_faces.py` ->
`make_groups.py` -> `rag_edges.py work/keep_base.npy work/keep_c.npy` -> `group_border.py work/keep_c.npy
work/keep_e.npy 0 3` -> `REA_KEEP_FACES=work/keep_e.npy REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=1:0.8,2:0.35,3:0.35
REA_HEIGHT_M=1.64 run_ladder.sh e65 0.65` -> `texture_drift.py r65`, `dark_slivers.py r65` (dark and `REA_LIGHT=1`,
`REA_DARK_L=80 REA_DARK_N=4`) -> `spot_lock.py work/keep_e.npy work/keep_h.npy 0.012 -0.378,0.128,1.2
-0.235,0.086,1.443 -0.39,0.128,1.239 0.542,-0.117,0.862 0.591,-0.048,0.87 0.251,0.146,1.241 0.389,0.118,1.251
0.36,0.128,1.215 0.227,-0.101,0.736` -> `REA_KEEP_FACES=work/keep_h.npy ... run_ladder.sh h 0.66,0.65` -> build as
above -> `lod_check.py`, `lod_views.py`, `glb_close.py`, `viewer_variants.py` (source r100, export r66).


## Gait rollout (2026-10-31)

Package [h21](../gait_rollout_20261031/h21/README.md) appended new in-place locomotion clips to the installed source
`assets_source/worlds/mm8/models/mm8_m468.glb` (existing clips, meshes, skins and materials byte-identical): `Walk2` (Mixamo Mutant Walking, 0.90 s, stride 1.7799), `Jog` (Unarmed-Run-Forward, 0.76 s, 3.0055) and `Sprint` (Unarmed-Sprint, 0.60 s, 4.1083); bound as walking / run / sprint (the installed `Walking` and `Running` stay in the GLB).
Bindings are in `../gait_rollout_20261031/h21/bindings.yml` (applied by the rollout coordinator). Rebuild:
`level_generation/creatures/gait_rollout_20261031/h21/scripts/rebuild.sh m468` (from `h21/work/mm8_m468_pre_gait.glb`,
the pre-gait source), then `python3 tools/install_model.py
level_generation/creatures/gait_rollout_20261031/h21/export/mm8_m468.glb --world mm8 --name mm8_m468.glb`. A far-LOD repair,
head-bob or reduction rerun on this model must re-graft these clips: copy its new source over the pre-gait copy and
rerun the rebuild (or graft them with `claude_shared/graft_clips.py`).
