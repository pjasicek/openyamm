# MM7 Archer (`m154`, Archer / Bowman / Elite Archer) reduction (2026-10-20)

User: "reduce tris on all 5" (the five MM7 batch-A humanoids; this project is the Archer). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: the textures, merged body+head atlas, three
tier variants (`KHR_materials_variants`) and region ramps stay valid. No Meshy credits. **Nothing installed.**

Source: the accepted exports of [`../mm7_m154_claude/`](../mm7_m154_claude/README.md) (not installed, rebuilt today),
copied as the rollback sources `work/mm7_m154_source_pre_reduce.glb`, `work/mm7_m154_bow_source_pre_reduce.glb`,
`work/mm7_m154_arrow_source_pre_reduce.glb`. Body node `M154`, one primitive `M154_A` (body and head merged by
`merge_head_material.py`; variants `M154_B`/`M154_C`), 60 joints, 4 influences at LOD0. The bowstring is a skinned
6-sided tube in the body mesh (`Bow` ends, `StringNock` middle). Bow on node `Bow`, arrow on node `Arrow` (separate
attachment GLBs from `split_attachment.py`). Scripts copied from `../mm8_m432_reduce_claude/scripts/` (per-region
groups, keep sets, parent-before-transform ladder, `grip_check.py`), the bow gate from `../mm6_lzd_reduce_claude/`.

[Review viewer](review/viewer/index.html) ·
<http://127.0.0.1:8912/level_generation/creatures/mm7_m154_reduce_claude/review/viewer/index.html>

## Result

| | source | reduced |
|---|---:|---:|
| body LOD0 / 1 / 2 / 3 | 10,253 / 5,124 / 1,838 / 605 | **8,383** / 4,191 / 1,838 / 705 |
| bow LOD0 / 1 / 2 / 3 | 988 / 494 / 176 / 58 | **524** / 284 / 84 / 44 |
| arrow LOD0 / 1 / 2 / 3 | 342 / 171 / 61 / 24 | **210** / 138 / 61 / 24 |
| LOD0 total (body + bow + arrow) | 11,583 | **9,117** (-21 %) |

`export/mm7_m154.glb` (7.4 MB; source 7.6), `export/mm7_m154_bow.glb`, `export/mm7_m154_arrow.glb`: same nodes,
skins, clips (8), sockets (`Socket_Arrow_Release`, `StringNock`, `Bow`, `Arrow`), materials, images (byte-identical),
variants and mesh names as the source; variants on all 8 body colour/shadow primitives and on every bow/arrow LOD.
Winding check: 0 inverted closed parts in all three files.

## Where the triangles are

Weld 6,449 -> 344 open edges, no coincident vertices with other weights, no two-sided sheets (10,253 in and out).
Pieces (`scripts/pieces.py`, `work/piece.npy`):

| piece | faces | treatment |
|---|---:|---|
| head skin (face, neck, scalp) | 2,012 | front of the face (y < -7 cm, z > 1.33 m: 1,453) **kept**; the rest 40 % (under coif and helmet) |
| tunic shell (gorget, pauldrons, sleeves) | 1,784 | ladder budget (label 0); white emblem faces and hem band (z < 0.8 m) kept |
| legs and boots | 1,308 | ladder budget; soles (faces below 6 cm) kept; 3 cm round both knees kept (error lock) |
| two gloves with fingers | 2 x 1,102 | **kept** (bow grip and draw pinch are fitted) |
| fur quiver (two pieces) | 636 | 50 % |
| mail coif | 406 | 85 % |
| helmet | 384 | rim band (z < 1.52 m) kept, dome 65 % |
| diagonal strap | 324 | 50 % |
| mail arms | 291 | kept (75 %: p99 8 mm in poses) |
| bowstring tube | 192 | **kept** |
| horns | 182 | kept |
| buckle | 132 | kept |
| small pieces (<= 80 faces: seven quiver arrows, quiver cap, eyes, helmet spike) | 398 | kept |

Kept exactly: 5,496 faces (`work/keep_f.npy`); groups `work/groups_f.npy`.

## Ladder

Limits for the 1.70 m bind height: p99 5.1 mm, max 25.5 mm (`compare_ladder.py`, every 3rd frame of every clip).

| config | step | tris | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| a: face 75 %, mail arms 75 %, gold trims a group | r81 | 8,363 | 4.44 / 26.03 | 0.994 | 0.9945 | fail (mail arm max; trims stall at 218 faces with 10 mm) |
| b: face 60 %, mail kept, hem kept, coif 60 %, helmet 75 % | r77 | 7,989 | 4.33 / 24.67 | 0.9942 | 0.9948 | passes; **face changes** (lips, eye sockets), notch under the helmet rim |
| c2: b with face 80 % | r79 | 8,145 | 4.62 / 20.94 | 0.9933 | 0.9944 | passes; face still changes in clay |
| c1: face kept | r81 | 8,365 | 4.62 / 20.94 | 0.9932 | 0.9944 | passes; notch under the back helmet rim |
| e: helmet 97 % | r83 | 8,551 | 4.29 / 19.03 | 0.9947 | 0.995 | notch gone (it was the helmet rim) |
| **f: face, horns, helmet rim kept; dome 65 %, coif 85 %** | **r81** | **8,383** | **4.76 / 20.94** | **0.9934** | **0.9942** | **pick** (lowest passing step, auto) |
| f | r79 (body 60 %) | - | | | | (g: quiver/strap 40 %: 8,171, p99 5.21 fail) |
| h: f + 3.5 cm locks at the back and armpit worst points, body 60 % | r80 | 8,237 | 5.35 / 20.94 | 0.9914 | 0.9933 | fail: the tunic and legs cannot go below ~65 % |
| i: f + one drift-lock round | r84 | 8,653 | 4.97 / 20.94 | 0.9934 | 0.9942 | not needed (see drift) |

The body cut is set by the tunic and legs (`scripts/piece_error.py`: both reach p99 ~9 mm at 55 %); the max at the
pick is the left knee in Running (error-locked, under the limit). Of the 8,383 triangles, 3,849 are the face, the
gloves and the string, which the brief keeps exactly, so the requested ~8,000 was not reachable without cutting the
face or the hands (b/c2 do: visible changes in the clay face).

Texture drift (`texture_drift.py r81`): 54 faces over 40, 179 cm2, p99 32 - almost all on the mail coif, whose
high-contrast chain pattern makes the sampled-colour check noisy; the textured close-ups of all three tiers show no
change, so no drift-lock round (config i costs 270 triangles).

Close-ups straight from the GLBs (viewer GLBs with the attachments, `glb_close.py`): `review/sheet_head.png`,
`review/sheet_body.png`, `review/sheet_bow.png` (grip standing and at full draw, draw pinch, whole bow, nocked arrow),
`review/sheet_tiers.png` (tiers B and C). Face, helmet, horns, coif, hands, emblem, quiver and boots match the source.

## Bow and arrow

The bow is a stack of 62 octagon rings along +Y (`make_bow.py`), one connected part. A quadric collapse kinks such
limbs, so `scripts/bow_rings.py` drops whole rings: greedily the ring whose vertices lie closest to the straight bridge
between its neighbours; kept segments copy the source triangles, every vertex keeps its source position, normal and
UV. Fixed at LOD0: the fist band (every ring within 2 cm of the right-hand vertices that come within 4 cm of the bow in
any clip, `grip_gate_bow.py`: y -5.5 ... +9.3 cm, 9 rings) and three rings at each tip (string ends). LOD0 33 rings,
max deviation 2.7 mm; LOD1 18 rings (11.6 mm); LOD2/3 the inscribed diamond of each kept ring (stays inside the
octagon, so inside the fist) at 11 / 6 rings.

Grip gate (`work/grip_export.json`, final body + bow, every 2nd frame of every clip): right-hand vertices inside the
bow per clip are identical to the source (Standing 999 vertex-frames, deepest 7.2 mm; Attack 584 / 7.4 mm; ...): the
source fist already sits up to 7-8 mm inside the grip octagon (fitted with `R_HANDLE=0.016`); nothing new. Left hand:
0 inside in every clip.

The arrow's shaft is a straight 6-sided tube of 24 rings with constant radius and linear UVs; `scripts/arrow_rings.py`
keeps every 2nd ring (LOD0) and every 4th (LOD1), head and vanes unchanged: the shape and texture mapping are exactly
the source's. LOD2/3 are the source's.

## LODs

`build_lods.py`: `tools/build_actor_lods.py` with ratios 0.5 / 0.22 / 0.085 and 8 influence slots (as the source
build), protected points: Death/Dead floor contact (1.5 mm), the top 1 mm, the top 1 mm of each horn, the outer 1 mm on
each side and end, and the bowstring's nock ring and end rings. Then `shrink_shadow_lods.py` (copied from the source
project) and `carry_variants.py`.

- `lod_check.py` (`work/lod_check_{src,f81}.json`): every LOD keeps the LOD0 bounds (top 1.7001 m; source LOD2/3
  1.703) and the LOD0 lowest point in every clip (source LOD3 floated 1.8 cm in Dead, reduced 0.6 mm); no face
  stretches over 20x in any frame of any clip at any LOD.
- The string: LOD1-3 keep a two-segment tube (60 triangles) that reaches the nock at full draw. The source LODs had a
  straight 6-triangle string with nock weight 0.01 that never drew; an unprotected collapse gave a 69 % nock weight and
  7 faces stretched over 20x in Attack.
- Protected 5 mm bands (42 points) pulled the LOD3 horns into needles and folded the helmet; 1 mm bands fixed the
  horns, and LOD3 at 0.085 (705, source 605) keeps the helmet a dome (at 0.072 it folded into a peak and the face
  flattened). `review/lods/sheet.png`: source / reduced, LOD0-3.
- `grip_check.py`: all 1,599 hand/finger vertices (weight > 0.5) and all 294 string vertices keep their bind positions
  (< 0.001 mm) and weights.

## Viewer

`review/viewer/`: source (r100) and reduced (r81) for tiers A/B/C, the bow and arrow attached to their joints for
review only (`viewer_attach.py`; separate attachments in game). `python3 tools/run_creature_review.py --project
level_generation/creatures/mm7_m154_reduce_claude --token <lease> check`: 48 switches, no console errors.

## Deviations / for the user

- Body LOD0 8,383 instead of ~8,000 (face, gloves and string kept exactly; the cloth cannot take a deeper cut).
- Body LOD3 705 (source 605) to keep the helmet shape; bow and arrow LOD3 are below the source.
- The source fist already penetrates the bow grip by up to 7-8 mm (unchanged).

## Install later (not run)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m154_reduce_claude/export/mm7_m154.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m154_reduce_claude/export/mm7_m154_bow.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m154_reduce_claude/export/mm7_m154_arrow.glb --world mm7
```

then the staged binding of the source project (`../mm7_m154_claude/integration/actors.yml`). Rollback: the
`work/*_source_pre_reduce.glb` files.

## Reproduce

`REA_GLB=<abs>/work/mm7_m154_source_pre_reduce.glb REA_NODE=M154 bl.sh import_source.py` -> `dump_mesh.py`,
`dump_groups.py`, `extract_basecolor.py <source glb>`, `small_pieces.py`, `pieces.py` ->
`M154_FACE_KEEP=1 M154_EMBLEM_RING=0 M154_HEM_Z=0.8 M154_MAIL_KEEP=1 M154_HORNS_KEEP=1 M154_HELMET_RIM_Z=1.52
M154_LOCK_POINTS='0.146,-0.09,0.457;-0.146,-0.09,0.457' m154_sets.py f` ->
`REA_GROUP_RATIOS=2:0.4,3:0.85,4:0.65,6:0.5,7:0.5 REA_KEEP_FACES=work/keep_f.npy REA_GROUPS=work/groups_f.npy
run_ladder.sh f $(totals.py f 0.75,0.7,0.65)` -> `prop_dump.py` (bow, arrow), `grip_gate_bow.py <source body> <source
bow> src` -> `build_reduced.sh f Cand_81` (reproduces the exports byte for byte) -> checks (`grip_check.py`,
`grip_gate_bow.py`, `lod_check.py`, `string_faces.py`, `lod_views.py`) -> viewer (`viewer_variants.py`,
`viewer_attach.py`, `viewer_manifest.py "MM7 Archer (m154)" r81 10253 8383`). Blender scripts run through
`scripts/bl.sh` (lease token in `TOKEN`); pymeshlab from the shared scratch venv (`run_ladder.sh`).

## Clips updated (2026-10-20)

The source project's walk/run ankle twitch was fixed after this reduction (`../mm7_m154_claude/scripts/foot_level.py`). `scripts/transplant_clips.py` copied the re-exported clips into `export/mm7_m154.glb` and every `review/viewer/*.glb` (geometry, LODs, materials and variants unchanged), and `work/mm7_m154_source_pre_reduce.glb` is now that re-export. After any later re-export of the source, run `python3 scripts/transplant_clips.py ../mm7_m154_claude/export/mm7_m154.glb export/mm7_m154.glb export/mm7_m154.glb`.
The walk bob fix (`walk_bob.py`, same day) was carried over the same way.

**Accepted 2026-10-20**; installed 2026-10-20 from `../mm7_batches/BATCH_A_stage/` (listed in REDUCTION_LEDGER.md).
So was the Hit/Death foot-roll fix (flatness-weighted, smoothed roll; same day); the stage was rebuilt.

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: Attack sinks to -2.7; dying sinks to -9.4.
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m154.glb export/mm7_m154.glb --lift-joints Attack Dead Death --lift-only 'B_Skirt*,Robe_*,…' --raise Attack --ground-death Death Dead`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m154.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).
