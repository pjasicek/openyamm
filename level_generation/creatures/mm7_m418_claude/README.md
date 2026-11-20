# MM7 Troglodyte (m418) — Claude rig-first project

Batch D, model 5 ([batch file](../mm7_batches/BATCH_D.md)). Descriptors 412 Troglodyte Drone (palette 95, green
markings), 413 Troglodyte Soldier (96, grey markings) and 414 Troglodyte Queen (97, cyan markings: the native frames'
own palette). **Installed 2026-10-20** in `assets_source/worlds/mm7/models/` and `assets_dev/worlds/mm7/models/` (bindings in its `actors.yml`). Status: technically complete, pending user review.

[Review viewer](review/viewer/index.html) (served at
`http://127.0.0.1:8912/level_generation/creatures/mm7_m418_claude/review/viewer/`) ·
[HD masters](references_hd/selected_views_review.png) · [head masters](references_head/selected_views_review.png)

| Item | Value |
|---|---|
| Exports | `export/mm7_m418.glb` (body, LODs, 3 tier variants, head merged; unarmed); editable master `work/rig_v6.blend` |
| Triangles | LOD0/1/2/3 6,729 / 3,363 / 1,190 / 380 (was 9,288 / 4,643 / 1,661 / 533). Second cut on the textured master (user review 2026-10-20, `reduce_textured.py`, targets per garment in `scripts/reduce2.json`; protected: Hand bones, the head/body texture boundary, creases, head region weight 1.0); both texture sets get new UVs and are baked garment by garment from the unreduced copy `work/rig_v6_full.blend` (`rebake_uv.py` -> `texturing/rebake_v2/`, read by the compose script) |
| Mesh | Smart Topology of the HD three-quarter master (Codex v2: clearer arm and tail gaps): one closed skin body (hood, dorsal spines, arms with three claws, legs, tail curving to its left) plus 25 separate teeth and 4 tail spines |
| Rig | 52 `B_*` bones with cloned source frames + a 7-bone tail chain `B_Tail0..6`. Meshy's auto-rig put the left hand on the tail and the knees 0.5 m apart in depth, so every joint is measured on the mesh (`limb_profiles.py`: geodesic rings from each claw, toe and the tail tip; leg axes from horizontal slices; `fit_joints.py`) |
| Weights | bone heat on our joints (`build_rig.py WEIGHTS=auto`), then `weights_fix.py`: claws rigid on the hand bones; no leg weight on the arms and no arm weight on the legs; arm weight fading out where the torso/hood axis is nearer (hood rim, hump, dorsal spines: they stretched into shards); the hood rigid on `B_Head`, blended over the rim groove; teeth rigid on the head; tail spines from the skin under them |
| Clips (30 fps) | Mixamo "Mutant" set with `KEEP_REST`: the limbs copy the source's world rotations, the pelvis/spine/neck/head/clavicles keep our forward hunch and take the source's motion relative to Standing frame 0 (the world rule stood the torso upright). Standing Mutant Breathing Idle, arms out 8 deg (4.0 s); Walking Mutant Walking in place (2.377 m of source travel per 1.433 s cycle removed), arms out 22 deg, per-frame floor pass; Running Mutant Run (in place, not fitted: tier speeds 220/240/260 stay under the run threshold); **Attack** Mutant Swiping planted, from its second swipe (source frame 28): rears up with the arm raised, slashes down (blow 0.45 s), cut 0.35 s after the slash and eased to Standing (1.17 s); Hit Zombie Reaction Hit cut at its flinch (0.87 s); Death **authored** (`author_death.py`: rears back, rolls 118 deg onto its back, bounces, lies belly up like m418d; floor pass every frame); Dead; Fidget Mutant Roaring, arms out 22 deg (5.4 s). The tail sways procedurally in every clip (`tail_bones.py`) and lifts in the attack |
| Textures | body 1K + head 1K (hood and teeth; Meshy retextures from the HD masters / head turnaround), AO graded, ORM red = per-class specular mask; one region, the cyan markings, in both sets with the same ramps; ramps: a square-root luminance curve through each tier's native median, chroma by luminance rank, tier C (the native palette) keeping the texture's chroma |
| Meshy credits | **30 of 100**: Smart Topology 5, auto-rig 5 (unused), body retexture 10, head retexture 10 |

## Installed 2026-10-20 (user request; commands as run)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m418_claude/export/mm7_m418.glb --world mm7
```

[actors_m418_binding.yml](actors_m418_binding.yml) is added to `assets_dev/worlds/mm7/models/actors.yml` (scale 78.6 =
native stand 146 px x 1.0 over the 1.858 m Standing pose; stride 2.377 m; blow 0.45 s; head look 30/20 deg).
`run_stride_length` 2.4 is nominal: Running is never reached at the tier speeds.

## Replay

`scripts/rebuild.sh` (`STAGE=rig`, then `STAGE=anim`), texture chain once (`export_uploads.py`, Meshy `retexture_v1`
and `head_retexture_v1`, `transfer_uv.py -- work/rig_v5h.blend meshy/retexture_v1 work/rig_v6.blend`), then
`scripts/build_runtime.sh`, `viewer_tiers.py`, `update_viewer_manifest.py`.

## Gates (final export)

- G4: arm stretch p99 <= 1.42, max 2.18 (left forearm in the attack's raise).
- G6 (closed skin, inside test): Standing, Running and Hit 0; Walking forearm <= 4.2 cm; Attack <= 7.2 cm (the
  slashing hand crosses in front of the hood and belly in the follow-through; a wider arm abduction made the raise
  worse); Fidget <= 7.3 cm (the claws on the knees during the roar's crouch); Death hands <= 4.8 cm while rolling.
  Arm abduction (`arm_abduct.py`) took the walk from 8.2 cm and the hit from 7.8 cm.
- Feet: grounded soles -0.6 cm standing, -0.9..+1.3 cm walking (the Mutant walk sank 5.5 cm before the floor pass).
- Viewer: 3 tiers x 8 clips, no console errors; textured EEVEE frames in `work/r_glb/`. Not checked in game.

## Known limits

- The claws do not articulate (rigid hands); the hood has no jaw (the maw does not open).
- The tail motion is procedural (sway and lift), not physics; in the death it is carried by the roll.
- Arm/claw contacts of up to ~7 cm remain in the attack follow-through and the roar (see G6).
- The rest pose keeps the HD master's tail curve to the creature's left; every clip shows it.

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: Fidget sinks to -27.1.
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m418.glb export/mm7_m418.glb --lift-joints Fidget --lift-only B_Tail* --raise Fidget`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m418.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).

## Gait rollout (2026-10-31)

Package h08 of [the gait rollout](../gait_rollout_20261031/README.md) appended `Lope` (the Mixamo Mutant Run planted,
0.867 s, stride 2.5003; bound as the walking clip: the wander speed is a run pace for this body), `Jog` (humanoid set
Unarmed-Run-Forward, 0.72 s, 4.1344) and `Sprint` (Unarmed-Sprint, 0.60 s, 4.9948) to the installed `mm7_m418.glb`
(existing clips byte-identical) and installed it. Bindings for the coordinator: `walking: Lope`, `stride_length:
2.5003`, `run: Jog`, `run_stride_length: 4.1344`, `sprint: Sprint`, `sprint_stride_length: 4.9948`
(`../gait_rollout_20261031/h08/bindings.yml`). Rebuild: `../gait_rollout_20261031/h08/scripts/rebuild.sh m418`;
details and gates in [the package README](../gait_rollout_20261031/h08/README.md). A far-LOD repair rerun or any
re-export of this model must re-graft these clips (rerun that rebuild on the new source).
