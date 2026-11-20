# MM8 Necromancer (`m472`, Necromancer A/B/C) reduction (2026-10-18)

User: reduce the Necromancer by the [retopology playbook](../RETOPOLOGY_PLAYBOOK.md) default route, then present a
viewer. No-retexture variant: no part needed rebuilding, so the installed textures, three palette variants and
region ramps stay valid. No Meshy credits. Scripts start from `mm8_m492_reduce_claude/` (coincident-vertex
separation, exact source weights), with per-region budgets added here.

Source: the installed `assets_source/worlds/mm8/models/mm8_m472.glb`, identical to `mm8_m472_claude/export/`
(lining-fix revision, user-accepted), copied to `work/mm8_m472_source_pre_reduce.glb` (rollback source). One
material (`Necromancer_A`, merged head/body 2080x1024 atlas), node `Necromancer`, 8 influences, 128 bones.
No held prop. The project has no shared-gate config, so the gate runner was not run.

## Regions (`make_groups.py`, `review/groups_sheet.png`)

Head texture set = faces with u > 0.505 (5,171). Labels and ratios of the picked ladder:

| label | faces | ratio |
|---|---:|---|
| face skin (head set, Head-dominant, front, below hairline) | 2,372 | 70 % |
| hair and scalp (rest of the head set) | 2,799 | 50 % |
| hands and fingers | 1,536 | 50 % |
| silver cuirass (separate rigid piece on `B_Spine1`) | 1,885 | 60 %, front centre strip kept |
| two skull cords | 676 | kept exactly |
| rest: robe, sleeves, cuffs, slippers, lining | 7,679 | remaining budget |

Kept exactly (`work/keep_f.npy`, 3,614 faces): eyes and ears (head-set pieces up to 250 faces, 646), rune faces
(region mask red at the face centre, 724), the faces around drifted faces from two lock rounds, the cuirass front
centre strip (|x| < 2.5 cm, 133) and both skull cords (676).

## Ladder (limits for the 1.7 m height: p99 5.1 mm, max 25.5 mm)

| config | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| a (face 80, hair 60, hands 60, cuirass 70) | 65 % | 11,009 | 3.43 / 19.6 | 0.996 | 0.996 | pass |
| a | 57 % | 9,823 | 7.34 / 30.6 | 0.989 | 0.990 | fail: group budgets starve the robe |
| b (face 70, hair 50, hands 50, cuirass 60) | 62 % | 10,505 | 3.43 / 17.4 | 0.995 | 0.995 | pass |
| b | 56 % | 9,657 | 4.73 / 29.8 | 0.993 | 0.993 | fail (back-waist vertex in Hit) |
| c (face 60, hair 45, cuirass 55) | 59 / 56 % | 9,995 / 9,487 | 3.73 / 17.4, 4.22 / 20.8 | 0.994 | 0.996 / 0.995 | pass, rejected: lips and mouth lump |
| d = b + one drift lock | 62 % | 10,503 | 4.74 / 22.3 | 0.994 | 0.995 | first pick, superseded |
| e = d + cuirass centre and cords kept | 62 % | 10,503 | 5.54 / 30.6 | 0.992 | 0.993 | fail: the robe starves |
| e | 65 % | 11,011 | 4.02 / 20.8 | 0.994 | 0.995 | pass |
| **f = e + one drift lock** | **65 %** | **11,013** | 4.90 / 22.3 | 0.995 | 0.994 | **picked** |

- **Normals: plain smooth.** The first pick (d) used `REA_NORMALS=transfer` (copy custom normals from the nearest
  source face), on the belief that the source had sculpt normals. It does not. `import_source.py` welds the mesh, and
  Blender stores custom normals relative to the default normals, so the weld scrambled them in `source.blend` into
  fake creases, which the transfer then baked into the candidate. Rendered straight from the GLBs without a weld
  (`scripts/glb_close.py`, `review/glbclose/sheet.png`: installed GLB / transfer build / smooth rebuild), the
  installed face, chest and hands are plainly smooth; the transfer build adds creases on the brow, cheeks and mouth
  corners and warps the chest, and the smooth rebuild matches the installed GLB. The pick uses smooth normals;
  `REA_NORMALS` stays in `reduce_ladder.py` but must not be used with a welded `source.blend`.
- **Face budget**: 60 % lumps the lips and mouth (`review/close/sheet_c1.png`), as the Leather Fighter note warns;
  70 % holds.
- **Cuirass centre and cords** (found by the retexture check below): at d the painted rope trims kinked at the
  plate's front centre line and a green rune streak appeared (UVs slid across the centre UV seam; the strip's max
  drift 34.8 stayed under the drift threshold), and the cord knot at the lower cuirass edge broke into shards. Keeping
  the centre strip and both cords exactly fixes both (`review/glbclose/sheet_fix.png`: installed / d / e). That
  starves the robe at 62 %, so the step is 65 %.
- **Drift locks**: d's lock round removed black shards on the back plate and lower cuirass edge
  (`review/close/sheet_lock.png`). f's round (on e's drift) removed a light streak on the left wrist cuff trim
  (`review/glbclose/sheet_lock.png`: installed / e / f).
- Cuirass rigidity (`cuirass_rigid.py`): all cuirass vertices of the candidate are 100 % `B_Spine1`, as in the source.

## Build

`export_cand.py` (Cand_65 of `work/ladder_f.blend`, 8 influences, smooth normals) -> `swap_lod0.py`
(`work/f65_lod0.glb`) -> `build_lods.py` (the creature's own ratios 0.5 / 0.25 / 0.125, 8 influences) ->
`carry_variants.py`: `export/mm8_m472.glb`, 0 inverted closed parts (`check_winding.py`).

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 16,947 | 8,471 | 4,236 | 2,117 |
| reduced | 11,013 | 5,505 | 2,753 | 1,375 |

`work/lod_check_{src,r65}.json`: every LOD keeps the height (1.699 m against 1.700) and width; the lowest point
over all clips is -3 mm or higher in every LOD, as in the source. A single tiny face stretches over 20x in five clips
at reduced LOD1, as at source LOD0 and LOD3.

Viewer `review/viewer/` (installed and reduced 65 % for the three tiers; ramps baked by `viewer_variants.py`):
`tools/run_creature_review.py ... check` passes, 54 clip switches, no console errors.

## Retexture check (2026-10-18)

Verdict on the corrected build (f65): **no Meshy retexture for either texture set**. No credits. The one texture
defect the check found (cuirass centre UV slide) came from the reduction and is fixed in the cut (above).

**Texture sets.** One material per tier (`Necromancer_A/B/C`) on a shared 2080x1024 atlas: body set u < 0.505
(1K), head set u > 0.505 (1K: face, hair, scalp, neck down to the collar). Ramps only recolour runes and irises.
Texel density (source / reduced): body 395 / 388 px/m, head 855 / 827 px/m. UVs remain valid: no face crosses the
set boundary. The 47 zero-UV-area and 94 flipped faces of f65 (source 0 and 1) are hidden layers under the cuirass
and robe, which already have collapsed UVs in the source (5,627 cm2 of low-density body faces in the source).

**Drift** (`texture_drift.py r65` on the picked step; per region, drift > 40 of 255):

| region | faces (kept) | drift > 40 | area | p99 |
|---|---:|---:|---:|---:|
| robe and rest | 4,780 (1,421) | 17 | 59.1 cm2 | 18.1 |
| face skin | 1,851 (638) | 0 | 0 | 10.0 |
| hair | 1,547 (287) | 0 | 0 | 18.5 |
| hands | 836 (133) | 1 | 5.7 cm2 | 8.9 |
| cuirass | 1,323 (459) | 8 | 8.7 cm2 | 32.8 |
| cords | 676 (676) | 0 | 0 | 0 |

The remaining drifted faces are hidden (inside the torso and under the cuirass) or invisible in the close-ups.

**Head vs body colour** (base colour, linear luminance p10/50/90; CIE Lab medians): face skin (head set)
0.055 / 0.234 / 0.560, L 55.5, chroma 6.9 at hue -89; neck skin (head set) 0.144 / 0.244 / 0.404, L 56.4, C 8.4;
hands (body set) 0.252 / 0.306 / 0.389, L 62.2, C 9.6. Head and body skin never meet (neck and collar skin are all
head set; the cuirass collar covers the junction), so there is no seam. The hands read slightly lighter and bluer
than the face (`review/retex/sheet_body.png`); an optional local fix is a quantile match of hand-skin luminance to
the neck skin, as in `mm6_drg1_reduce_claude/scripts/unify_head.py`. Not needed for a pass.

**Existing quality** (`review/retex/sheet_face.png` all tiers, `sheet_body.png`, `sheet_cuirass.png`; installed
vs f65):
- Head: clean face, eyes, lips and hair on every tier; identical between installed and reduced. No near-black
  texels on face or hair surfaces. A faint dark smudge on the back hair is in the installed texture too.
- Body: the 1K body set softens the robe runes at hand-camera distance (accepted earlier at this resolution); robe
  and cuirass near-black faces are the black robe and the recessed armhole lining (design).
- The black notch at the back waist (`sheet_cuirass.png`, bottom row) is in the installed model too and sits at a
  hair strand tip over the back plate. It is geometry (lining showing between plate and hair), not texture.

Renders: `scripts/tex_views.py` (14 spots x 3 tiers x installed/reduced), `scripts/retex_sheet.py`;
GLB ground truth: `scripts/glb_close.py`.

## Status

Not installed; awaiting user review. To install: `python3 tools/install_model.py
level_generation/creatures/mm8_m472_reduce_claude/export/mm8_m472.glb --world mm8`, then
`OPENYAMM_REGRESSION_FILTER=mm8_necromancer ./build/game/openyamm --world mm8 --headless-run-regression-suite actors`
(`mm8_necromancer_actor_models_keep_tiers_and_dual_cast`), and add the row to
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Rollback: install `work/mm8_m472_source_pre_reduce.glb`.

Reproduce: `import_source.py` (REA_NODE=Necromancer) -> `dump_mesh.py` -> `dump_faces.py` -> `make_groups.py` ->
`REA_KEEP_FACES=work/keep_a.npy REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=1:0.7,2:0.5,3:0.5,4:0.6,5:0.7
run_ladder.sh b 0.62` -> `texture_drift.py r62` -> `drift_lock.py work/keep_a.npy work/keep_b.npy r62` -> keep_e =
keep_b + cuirass centre strip + cords -> `run_ladder.sh e 0.65` (ratios without group 5) -> `texture_drift.py r65` ->
`drift_lock.py work/keep_e.npy work/keep_f.npy r65` -> `run_ladder.sh f 0.65` -> build as above.

## Installed (2026-10-18)

User accepted the viewer ("ok"). `check_winding.py`: 0 inverted closed parts. Installed with
`tools/install_model.py export/mm8_m472.glb --world mm8`; recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).
Regression: `OPENYAMM_REGRESSION_FILTER=mm8_necromancer ./build/game/openyamm --headless-run-regression-suite actors: mm8_necromancer_actor_models_keep_tiers_and_dual_cast passes`. Rollback: install `work/mm8_m472_source_pre_reduce.glb` the same way.

## New walk and run: Walk2, Run2 (gait2, 2026-10-21)

The installed `Walking` shortens the legs 45 % toward Standing, so its feet pivot under the robe with no planted phase
(stride unmeasurable, played 1.9-2.3x wandering); `Running` played 3-3.7x chasing. Two clips were added under new
names; every existing clip is unchanged (the graft re-exports the installed `Walking` from the master and checks it
against this GLB: difference 0). No Meshy credits; Mixamo clips from the local library.

| clip | source | seconds | stride (gait gate) | authored speed | tier rates (A/B/C) |
|---|---|---:|---:|---:|---|
| `Walk2` | Mixamo "Walking (10)" | 0.767 | 1.239 (vertices 1.239, feet 1.257: trusted) | 1.62 | wander 1.10 / 1.20 / 1.31 |
| `Run2` | Mixamo "Running (4)" | 0.700 | 2.12 (vertices 2.121, feet 1.507: robed run, passed explicitly) | 3.03 | chase 1.17 / 1.29 / 1.40 |

Binding the gate passed (`gait_gate.py --world mm8 --model mm8_m472.glb --candidate export/mm8_m472.glb --set
walking=Walk2 --set run=Run2 --set run_stride_length=2.12`): `walking: Walk2`, `run: Run2`, `stride_length: 1.239`,
`run_stride_length: 2.12`. Not bound yet (the orchestrator edits `actors.yml`).

Why not a full-length stride: the hem reaches only ~0.22 m before and behind the pelvis and its circumference cannot
grow, so the natural 1.86 m (walk) and 2.6 m (run) Mixamo strides hung the trailing slipper 10-30 cm up outside the
robe. The robe fit (`gait2_fit.py`) keeps each ankle on the source's own path relative to the pelvis but scales its
forward travel (walk 0.68, run 0.93), heights above the planted level (0.45 / 0.40) and foot pitch (0.45 / 0.50),
moves the path centre 5 / 7 cm forward, draws an airborne foot in to at most 0.20 m behind the pelvis (smoothed over
time), and solves the legs by two-bone IK with the knee in the source's leg plane. The planted phase is kept (93 % of
walk samples have a planted shoe). Upper body and arms keep the source motion. The game's speeds would want a longer
stride (target authored speeds 1.94 / 3.88); every tier still plays inside the 0.75-1.5 window.

Pipeline (all in `../mm8_m472_claude/scripts/`, one Blender each, about a minute in total):
`gait2_motion.py` (retarget `gait2_retarget_mixamo.py`, exact loop, floor pass, constant foot tilt `gait2_foot_level.py`
:const, `gait2_fit.py`, floor pass, twist bake FA 0.6) -> `gait2_cloth.py` (production `garment_sim.py` on the new
clips, Running's 10 cm hem opening on Run2, `surface_clearance.py` garment correctives, visible floor lift,
`check_deformation.py`) -> `gait2_export.py` (actions appended to `necromancer_master.blend`, armature-only glTF) ->
`gait2_graft.py work/mm8_m472_pre_gait2.glb export/mm8_m472.glb`. `garment_sim.py` and `surface_clearance.py` gained
optional `INPUT_BLEND`/`OUTPUT_BLEND`/`CLIPS`/`LOOPS` init globals (defaults unchanged). Rollback source:
`work/mm8_m472_pre_gait2.glb` (the previous install).

Checks (`../mm8_m472_claude/work/deformation.json`, `gait2_arm_gate.py`):

| | Walking | Walk2 | Running | Run2 |
|---|---:|---:|---:|---:|
| robe edge stretch max / p99 | 4.43 / 1.48 | 9.93 / 2.48 | 5.92 / 2.00 | 12.27 / 2.60 |
| robe vertices inside a shoe (max, depth) | 0 | 4, 10 mm | 0 | 3, 7 mm |
| lowest shoe point range (m) | 0.003-0.011 | 0.003-0.005 | 0.003-0.076 | 0.003-0.029 |
| hand edge stretch max (G5) | 2.45 | 2.27 | 2.45 | 2.23 |
| wrist swing max (deg) | 38 | 43 | 30 | 40 |
| hand twist about the forearm max (deg; twist bone takes 0.6) | 111 | 127 | 110 | 84 |
| hands inside the trunk capsule | 0 | 0 | 0 | 0 |
| hand rotation step per half frame (deg) | 4.6 | 6.5 | 7.2 | 16.4 (source arm pump) |

`check_winding.py`: 0 inverted closed parts. Viewer: `review/viewer/` adds `necromancer_{a,b,c}_gait2` (all clips,
including the old ones for comparison); playback recordings in `review/playback/`.

Open points: from behind, the trailing slipper heel still shows at the back hem for a few frames of each cycle (touching
the floor, no longer floating); the robe stretches more than in the old clips around the advancing knee; Run2's hands
rotate fast (the Mixamo arm pump).
