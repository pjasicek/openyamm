# MM8 Pirate Warrior (`m412`, Pirate A/B/C and Wimpy Pirate A/B/C) reduction (2026-10-19)

User: "OK go ahead" (MM8 triangle-reduction batch of openyamm-f6: m536, m616, m568, m628, m412). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture variant: no part needed rebuilding, so the installed
textures, three palette variants (`KHR_materials_variants`) and region ramps stay valid. No Meshy credits.

Source: the installed `assets_source/worlds/mm8/models/mm8_m412.glb`, byte-identical to
`../mm8_m412_claude/export/mm8_m412.glb` (knee-correction revision of 2026-10-15; the `assets_dev` runtime copy was
cooked from it at the same time, 2026-10-18 10:53, eight clips), copied to `work/mm8_m412_source_pre_reduce.glb`
(rollback source). One material per tier (`Pirate_A/B/C`, merged 2080x1024 head/body atlas, head set u > 0.5), node
`Pirate`, 42 bones, 4 influences. The cutlass (`mm8_m412_cutlass.glb`, 900 triangles) is unchanged and not part of
this build. Scripts start from `../mm8_m624_reduce_claude/scripts/` (parent-before-transform fix) with the per-region
helpers of `../mm8_m472_reduce_claude/`.

## Keep sets and regions (`make_groups.py`, `review/groups_sheet.png`)

Weld 6,676 -> 448 open edges; 2 coincident vertices with other weights (no split seam).

| label | faces | ratio |
|---|---:|---|
| face skin (head set, `B_Head`, front, below the bandanna; beard and lips) | 1,189 | 70 % |
| neck, ears, chest skin and scalp (rest of the head-set skin piece) | 874 | 50 % |
| bandanna and its tails | 1,109 | 55 % |
| left hook and socket | 500 | 45 % |
| rest: shirt, trousers, boots, sash, belt | 8,205 (3,296 decimated) | remaining budget |

Kept exactly (`work/keep_d.npy`, 4,944 faces):
- the sword fist (`B_R_Hand` / `B_R_Finger*` dominant faces, 1,704), so the fitted cutlass grip does not change;
- small pieces of up to 180 faces (1,455): eyes, eyepatch and strap, earrings, belt buckle, sash knots and tails,
  both cuffs;
- the soles (faces below 6 cm, 306; foot-yaw and sole gates);
- one drift-lock round (35 faces, from ladder a at 70 %);
- **the knee bend zone** (`work/knee_faces.npy`, 1,408 faces: thigh/calf faces with > 95 % leg weight between 0.42 and
  0.74 m). The user found a dislocated-looking right knee in Running on 2026-10-15; the creature's repair added bend
  rows across the knees and `../mm8_m412_claude/scripts/check_knees.py` guards them (skinned chord error of the knee
  edges, every clip, 120 Hz; limits 8 / 16 / 24 / 40 mm per LOD). Every uniform step removed those rows: the 70 %
  candidate of ladder b had a 13.6 cm edge across the right knee and a 22.0 mm chord error (installed 5.49 mm).
  Planar cuts after the reduction (`knee_cuts.py lod0`) also restored it (5.68 mm) but cost 1,010 faces and add
  slivers; keeping the zone costs less;
- a 4 cm hip patch on both sides (36 faces, `patch_keep.py`): with the knees kept, the left hip/sash vertex at rest
  (0.156, 0.035, 0.980) failed every step at `Running:3` (54.5 mm).

## Ladder (limits for the 1.689 m height: p99 5.07 mm, max 25.3 mm)

| config | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| source | | 11,877 | | | | |
| a: fist, small, soles kept; face 75, skin 60, bandanna 60, hook 50 | 75 % | 8,907 | 3.10 / 22.7 | 0.993 | 0.995 | pass |
| a | 70 % | 8,313 | 4.21 / 23.4 | 0.991 | 0.993 | pass, knee rows lost |
| a | 65 % | 7,719 | 6.39 / 52.8 | 0.988 | 0.989 | fail; collar notch, boots blobby |
| b = a + one drift lock | 70 % | 8,311 | 4.31 / 23.4 | 0.990 | 0.993 | pass, knee chord 22.0 mm (limit 8) |
| c = b + knee zone kept | 78 % | 9,263 | 4.17 / 23.4 | 0.991 | 0.993 | pass, knee 5.49 mm |
| c | 75 % | 8,905 | 5.78 / 54.5 | 0.990 | 0.990 | fail (hip point) |
| d = c + hip patch | 76 % | 9,025 | 5.39 / 29.5 | 0.990 | 0.991 | fail: region budgets starve the rest |
| e = d; face 70, skin 50, bandanna 55, hook 45 | 78 % | 9,261 | 3.61 / 22.5 | 0.990 | 0.994 | pass |
| **e** | **76 %** | **9,023** | 4.35 / 22.5 | 0.990 | 0.993 | **pick**, knee 5.49 mm |
| e | 74 % | 8,785 | 5.50 / 29.5 | 0.989 | 0.991 | fail (p99) |

Texture drift at the pick (`texture_drift.py r76`): 7 faces over 40 (8.1 cm2), all under 3 cm2 (beard edge under the
chin and the hook socket rim); not visible in the close-ups. No second lock round.

Close-ups: `review/close/sheet_a_head.png`, `sheet_a_body.png` (source / 75 / 70 / 65), `sheet_e_head.png`,
`sheet_e_body.png` (source / c78 / e76), `sheet_b_spots.png` (chin, hook end). The clay renders in `review/close/`
come from the welded `source.blend`, whose custom normals the weld scrambles; judge shading from
`review/glbclose/sheet_src_r76.png` (round 1; installed / reduced GLBs, textured then clay, each file's own normals): face,
eyepatch, beard, bandanna knot and tails, sword fist, hook and cuff, sash, back, boots, Attack and Death match.
Normals are plain smooth (no `REA_NORMALS=transfer`).

## Round 2: hole above the right ear (2026-10-19)

User review: "pirate ok, but there is a hole in his head above his right ear" (viewer close-up from his right: the
green bandanna shows through a gap above and in front of the right ear, and a small green sliver at the eye corner).

**Cause: the installed model has the hole; the reduction widened it.** The head skin is open on top under the
bandanna (a 68-edge boundary loop, rim 1.52-1.61 m). At the right temple that rim lies below the bandanna's lower
edge, so the bandanna's inside, and with the bandanna removed the background, shows through a wedge above and in front
of the ear and a sliver at the eye corner. `review/temple/fix_check_g78.png` (top: flat-colour crops from his right,
installed / fixed; bottom: the same views with the bandanna removed, magenta background) shows it on the installed
LOD0; `review/temple/noband_lods.png` shows larger holes on installed LOD1-3. The 76 % cut moved the bandanna rim and
the hairline skin and opened more of it behind the ear (`review/temple/green_diff_r76.png`, magenta = green pixels the
installed model does not show; 1,171 such pixels over a 36-view ring around the head, `scripts/green_ring.py`).
Not a weld or split seam (no new open edges; the two coincident vertices are elsewhere).

**Fix at the source:**
- `patch_scalp.py`: the skin's 68-edge opening gets a fan cap around its rest centroid, wound with the rim faces,
  weights averaged from the rim (all `B_Head`), every corner on one dark hairline texel of the head set (128, 91, 63).
  The cap is hidden under the bandanna except where the wedge was. The 43-edge loop beside it is the bandanna's own
  lower rim and stays open. 68 faces, appended after the source faces so every per-face mask keeps its index
  (`work/source_unpatched.blend`, `mesh_in_unpatched.npz` and `*_unpatched.npy` keep the round-1 inputs).
- Kept exactly: the skin and bandanna faces within 1.2 cm of the other piece (`work/band_border.npy`, 579 faces), so
  the bandanna rim and hairline do not move.
- Ladder g (keep_f = keep_d + border + cap; same region ratios): 79 % 9,433 (p99 4.06) / **78 % 9,313 (p99 4.64,
  max 22.5, IoU 0.990: pick)** / 77.5 % 9,253 (p99 5.07, fail). Texture drift: 8 faces over 40 (11.4 cm2), small.
- Ring check (new green pixels against the installed model): LOD0 45, all on the bandanna tail's silhouette over the
  shirt (`review/temple/green_diff_f78_060.png`), none at either temple. LOD1-3 differences are bandanna-edge
  silhouette changes of the coarser LODs; with the bandanna removed every LOD is closed at both temples
  (`review/temple/noband_lods.png`: installed / fixed, right and left, LOD0-3).
- Temple close-ups from the GLBs, textured, every LOD (`scripts/temple_views.py`): `review/temple/sheet_lods.png`
  (rows LOD0-3; installed right / fixed right / installed left / fixed left).

## Build

`export_cand.py` (Cand_78 of `work/ladder_g.blend`, 4 influences, smooth normals) -> `swap_lod0.py`
(`work/g78_lod0.glb`) -> `build_lods.py` (the creature's builder with LOD1 base 0.42 instead of 0.46, then 0.18 / 0.06)
-> `knee_cuts.py export/mm8_m412.glb lods` (the creature's `refine_knee_lods.py` planes on LOD1-3 colour and shadow)
-> `carry_variants.py` (variants on all 8 colour/shadow primitives) -> `compact_glb.py` (drops the accessors the knee
cuts replaced) -> `check_winding.py` (0 inverted closed parts): `export/mm8_m412.glb`, 7.1 MB (installed 7.6 MB),
8 clips.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 11,877 | 6,323 | 2,573 | 842 |
| round 1 (76 %, superseded) | 9,023 | 4,906 | 2,069 | 679 |
| **round 2 (78 %, temple fix)** | **9,313** | **4,768** | **2,122** | **705** |

The LOD1 base: the restored knee rows add about 850 faces, and the shared gate caps LOD1 at 55 % of LOD0
(`lod_ratio`); the right-arm Attack edge stretch p99 at LOD1 (limit 2.0, installed 1.98) varies with the ratio: round 2
trials 0.45 gave 2.03, 0.43 gave 2.01 (fail), 0.44 1.98 and 0.42 1.91 (pass). 0.42 keeps the margin.

Checks on the export:
- **Shared gates** (`claude_shared/gates/run_gates.sh` with `../mm8_m412_claude/gates.json`, `work/gates_final/`):
  FAIL with 488 FAIL and 136 UNVERIFIED rows, the same counts as the installed model (`work/gates_src/`; source
  motion ranges, the hook's missing palm and distant-LOD fingers, documented in the creature README).
  `gate_diff.py work/gates_src/gates.json work/gates_final/gates.json`: 0 rows that pass on the installed model fail,
  no failing row worse by more than 10 %.
- **Knee curvature** (`check_knees.py`, `work/knee_final.json`): 5.49 / 10.43 / 17.53 / 30.71 mm per LOD against
  the limits 8 / 16 / 24 / 40 (installed 5.49 / 10.43 / 17.53 / 29.80).
- **LODs** (`lod_check.py`, `work/lod_check_{src,g78}.json`): no face stretches over 20x in any frame of any clip;
  lowest point over all clips -1.2 mm or higher in every LOD (installed LOD3 Death: -7.8 mm). Height 1.701 / 1.701 /
  1.703 / 1.689 m (installed 1.700 / 1.700 / 1.700 / 1.699): LOD3 is 1 cm lower at the bandanna top.
  `review/lods/sheet.png` (round 1): installed / reduced, LOD0-3, standing, Attack and the Running knee frame.

Viewer: `review/viewer/` (installed vs reduced 78 % for the three tiers, revision reduce-2; ramps baked by
`viewer_variants.py`; manifest sha256 and `?v=` updated),
<http://127.0.0.1:8912/level_generation/creatures/mm8_m412_reduce_claude/review/viewer/>;
`python3 tools/run_creature_review.py --project level_generation/creatures/mm8_m412_reduce_claude check`: 48 clip
switches, no console errors.

## Round 3: walking height jump (2026-10-19)

User review (round 2 installed by the coordinator, regression passing, ledger row added): "imo there is a big 'jump'
in like height when walking e.g. frames 14-16 the head bobbing" (viewer frames, 48 fps: 0.29-0.33 s).

**Cause: the creature's Walking motion, not the reduction or the knee repair.** All eight clips of the reduced export
are byte-identical to the installed pre-reduction model, and the pre-knee-repair GLB
(`../mm8_m412_claude/review/knee_fix/before_mm8_m412.glb`) has the same jump (`work/walk_before_knee.json`). The viewer
frame is round(time x 48); Walking is 1.0 s with 121 keys at 120 Hz, key 120 = key 0. `scripts/walk_heights.py`
(`work/walk_src.json`): the pelvis (and the head with it) sinks during double support, 0.908-0.917 m, because the legs
cannot reach both planted soles from a higher hip, then shoots up at each toe-off: +2.6 / +3.1 / +1.9 cm at frames
14 / 15 / 16 and +1.8 / +3.9 cm at 37 / 38 (largest 48 fps step 3.9 cm; 11.7 cm range per cycle). Feet do not slide
or jump; only the trunk does.

**Fix** (`scripts/smooth_walk_bob.py <in> <out> 8`, applied to the round-2 export, kept as
`work/mm8_m412_pre_walkfix.glb`): a periodic Gaussian pass (sigma 8 keys = 67 ms) over the pelvis height, lowered by
smooth local dips wherever it would rise above the height from which both ankles are still reachable (99.5 % of leg
length). Both legs are re-solved by analytic two-bone IK in their original knee plane: every ankle keeps its original
world path (error 0.001 mm) and every foot its world rotation, so foot contact, lift and the loop seam are unchanged.
Only B_Pelvis translation and the thigh, calf and foot rotations of Walking change. Result: pelvis 0.909-1.004 m, two
even bobs per cycle, largest 48 fps step 1.25 cm (was 3.94); frames 13-17 now rise 0.9-1.0 cm per frame.
Stronger smoothing evens it further (sigma 14: 5.8 cm range, 0.7 cm step), but the extra knee bend then trips
`walking_knee_max_deg` on LOD2 (61-65 degrees against 60, measured at that LOD's peak-lift frame; LOD0 stays at 49-54),
a new fail against the installed model; sigma 8 is the smoothest without one.

Evidence: `review/walk_bob_plot.png` (head and pelvis per viewer frame; grey installed, blue this build, orange the
rejected sigma 14; lower panel: lowest foot vertex, unchanged), `review/walk/filmstrip_f10_20.png` (side view, frames
10-20, before / after, red line at frame 10's head height).

Checks on the round-3 export (`export/mm8_m412.glb`, 9,313 / 4,768 / 2,122 / 705, 7.0 MB):
- Shared gates (`work/gates_walk/`): 480 FAIL, 136 UNVERIFIED (installed 488 / 136). `gate_diff.py`: 0 new fails,
  0 worse; 8 rows fixed (`walking_knee_min_deg` L/R at LOD0-1 colour and shadow: the swing knee now bends 43-47 degrees
  instead of 31-34).
- Knee curvature unchanged: 5.49 / 10.43 / 17.53 / 30.71 mm (Walking itself 3.4-3.9 mm at LOD0).
- `lod_check.py` (`work/lod_check_walkfix.json`): no stretched faces; Walking lowest point 2.3 mm or higher in
  every LOD; heights unchanged.
- `check_winding.py`: 0 inverted closed parts. Viewer rebuilt (revision reduce-3, sha256 and `?v=` updated), check
  48 clip switches, no console errors.

The creature's own authoring master (`../mm8_m412_claude/work/master_knees.blend`) still has the old Walking: a
re-export from it would bring the jump back unless `smooth_walk_bob.py` is run on its export as well.

## Status

Round 3 (round 2 + smoothed Walk bob) installed 2026-10-19 after user review ("ok accepted") with `tools/install_model.py --world mm8`, replacing round 2 (installed earlier the same day once the right-ear hole was fixed); actor regression `mm8_pirate_actor_models_keep_native_roles` passes (`review/regression.log`). Recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).

Round 3 (walk fix) is staged in `export/mm8_m412.glb`, awaiting user review; not installed. The installed round 2 is
`work/mm8_m412_pre_walkfix.glb` (same geometry and LODs, old Walking).

Install (from the repository root): `python3 tools/install_model.py
level_generation/creatures/mm8_m412_reduce_claude/export/mm8_m412.glb --world mm8`, then
`OPENYAMM_REGRESSION_FILTER=mm8_pirate_actor_models ./build/game/openyamm --headless-run-regression-suite actors`
(`mm8_pirate_actor_models_keep_native_roles`) and add the row to [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).
The cutlass stays as installed.
Rollback: `python3 tools/install_model.py level_generation/creatures/mm8_m412_reduce_claude/work/mm8_m412_source_pre_reduce.glb --world mm8 --name mm8_m412.glb`.

Reproduce: `REA_GLB=<rollback source> REA_NODE=Pirate import_source.py` (then rename `work/source.blend` to
`work/source_unpatched.blend`) -> `patch_scalp.py` -> `dump_mesh.py` -> `dump_faces.py` (on the unpatched blend) ->
`make_groups.py` -> round-1 keep sets as below, each extended with the 68 cap faces (kept, group 0) ->
keep_f = keep_d + `work/band_border.npy` -> `REA_KEEP_FACES=work/keep_f.npy REA_GROUPS=work/groups.npy
REA_GROUP_RATIOS=1:0.7,2:0.5,3:0.55,4:0.45 run_ladder.sh g 0.78` -> build as above -> `check_knees.py`, `lod_check.py`,
gates, `gate_diff.py`, `temple_views.py`, `green_ring.py`, `hide_band.py`, viewer.
Round-1 keep sets: `REA_KEEP_FACES=work/keep_base.npy REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=1:0.75,2:0.6,3:0.6,4:0.5
run_ladder.sh a 0.70` -> `texture_drift.py r70` -> `drift_lock.py work/keep_base.npy work/keep_b.npy r70` -> keep_c =
keep_b + `work/knee_faces.npy` -> `patch_keep.py work/keep_c.npy work/keep_d.npy 0.156,0.0353,0.9795 0.1695,0.0016,0.9587`.

## Walk2 and Jog (2026-10-21)

`export/mm8_m412.glb` now also carries `Walk2` (Mixamo Walk, 1.05 s) and `Jog` (Mixamo Running (5), 0.833 s), appended by
[../mm8_pirates_gait_claude](../mm8_pirates_gait_claude/README.md) so every tier walks and chases inside the gait
window (the old Running is a sprint that crawled in game). Existing clips, meshes, LODs and variants are byte-identical;
the pre-gait export is kept as `work/mm8_m412_pre_gait.glb` (rollback: `tools/install_model.py` it with
`--name mm8_m412.glb --world mm8`). Installed 2026-10-21; bindings not changed here. Gate values for every descriptor:
`walking: Walk2`, `run: Jog`, `stride_length: 1.4998`, `run_stride_length: 2.3583`; PASSED (every tier 0.78–1.41). Playback:
[../mm8_m412_gait_claude](../mm8_m412_gait_claude/README.md).

## Gait rollout (2026-10-31)

The installed source `assets_source/worlds/mm8/models/mm8_m412.glb` now also carries `Sprint` (humanoid set Unarmed-Sprint, 0.62 s, stride 3.5194) for MAW's chase; A and Wimpy B/C now chase on the installed `Jog` (their chase is a run pace at pursuit 2.0), Wimpy A keeps `Walking`.
Appended by [package h17](../gait_rollout_20261031/h17/README.md) on the installed source (existing clips, meshes, LODs
and variants byte-identical); pre-gait copy and rollback: `../gait_rollout_20261031/h17/work/mm8_m412_pre_gait.glb`.
Bindings are in `../gait_rollout_20261031/h17/bindings.yml` (applied by the rollout coordinator). Rebuild:
`../gait_rollout_20261031/h17/scripts/rebuild.sh m412`. A far-LOD repair, head-bob or reduction rerun that rewrites
this source must re-graft these clips (copy the new source over the pre-gait copy and rebuild, or
`claude_shared/graft_clips.py`).
