# MM7 Wight (m430) — Claude rig-first project

Batch D, model 2 ([batch file](../mm7_batches/BATCH_D.md)). Descriptors 421 Wight (palette 111, brown robe), 422 Wraith
(112, white robe) and 423 Barrow Wight (113, red robe). **Installed 2026-10-20** in `assets_source/worlds/mm7/models/` and `assets_dev/worlds/mm7/models/` (bindings in its `actors.yml`). Status: technically
complete, pending user review.

[Review viewer](review/viewer/index.html) (served at
`http://127.0.0.1:8912/level_generation/creatures/mm7_m430_claude/review/viewer/`) ·
[clip sheets](review/clips_three_quarter.png) · [death](review/clips_death.png) ·
[HD masters](references_hd/selected_views_review.png) · [head masters](references_head/selected_views_review.png)

| Item | Value |
|---|---|
| Exports | `export/mm7_m430.glb` (body, LODs, 3 tier variants, head merged), `export/mm7_m430_dagger.glb` (attachment on `Dagger`); editable master `work/rig_v6.blend` |
| Triangles | body LOD0/1/2/3 7,199 / 3,595 / 1,298 / 459 (incl. the 230-triangle dagger before the split) (was 9,738 / 4,864 / 1,754 / 612). Second cut on the textured master (user review 2026-10-20, `reduce_textured.py`, targets per garment in `scripts/reduce2.json`; protected: Finger, Thumb bones, the head/body texture boundary, head region weight 0.4); both texture sets get new UVs and are baked garment by garment from the unreduced copy `work/rig_v6_full.blend` (`rebake_uv.py` -> `texturing/rebake_v2/`, read by the compose script) |
| Mesh | Smart Topology of the HD three-quarter master: one closed robe + head + hair piece, separate hands, cord strands and inner hem. Head shape kept (the head retexture paints the skull-like face with black sockets) |
| Rig | 52 `B_*` bones cloned from the humanoid set + twist bones + 8 skirt bones; spine and arms from Meshy's auto-rig (wrists ~9 cm inside the long hand pieces), the hidden legs rebuilt straight under the hips (Meshy leaned them 20 cm forward with the ankles off the floor) |
| Weights | `weights_fix.py`: sleeves and their torn strips found by GEODESIC distance over the robe (a strip hangs from its sleeve; the skirt flank beside it is reached from the trunk) and limited to their arm; upper robe on the spine/clavicles; skirt a dress (pelvis at the hips -> 45 % legs at the hem, one smooth left/right mix); hands on their own arm; cord and inner hem copy the robe; shoulder band smoothed 15 passes. `skirt_bones.py`: the skirt's pelvis share moves onto 8 skirt bones that stay at rest except in Death |
| Clips (30 fps) | Standing Mixamo Standard Idle (3.0 s); Walking Mixamo Walk (1.0 s, 1.366 m stride); Running Mixamo Standard Run fit (0.73 s); Attack Mixamo Sword And Shield Slash planted with IK steps and a ready pause (1.5 s, blow 0.75 s; native: dagger raised over the shoulder, cut down and across); Hit set Unarmed get-hit F1; Death Mixamo Standing React Death Backward, travel halved, skirt folded around the legs (3.63 s); Dead; Fidget Mixamo Annoyed Head Shake planted |
| Textures | body 1K + head 1K (Meshy retextures from the HD masters / head turnaround), AO graded, ORM red = per-class specular mask; one region (robe and inner hem); ramps keep the texture's luminance with each tier's native chroma and brightness (white tier gain 7.1) |
| Meshy credits | **30 of 100**: Smart Topology 5, auto-rig 5, body retexture 10, head retexture 10 |

## Installed 2026-10-20 (user request; commands as run)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m430_claude/export/mm7_m430.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m430_claude/export/mm7_m430_dagger.glb --world mm7
```

[actors_m430_binding.yml](actors_m430_binding.yml) is added to `assets_dev/worlds/mm7/models/actors.yml` (scale 111.3 =
native stand 197 px x 1.0 over the 1.770 m Standing pose, same for all tiers; stride 1.366 m; blow 0.75 s; head look;
dagger attachment). Tier speeds 180/200/220 stay under the run threshold (267), so Running is a spare clip.

## Replay

`scripts/rebuild.sh` (`STAGE=rig`, then `STAGE=anim`; the first anim pass skips the dagger clearance until
`work/grip_pose.json` exists), texture chain once (`export_uploads.py`, Meshy `retexture_v1` and `head_retexture_v1`,
`transfer_uv.py -- work/rig_v5h.blend meshy/retexture_v1 work/rig_v6.blend`), `make_props.py`, then
`scripts/build_runtime.sh`, `viewer_tiers.py`, `update_viewer_manifest.py`.

## Gates (final export)

- G4: arm-region stretch p99 <= 2.2; the robe's armpit stretches up to 8x on a few edges when the arm goes overhead
  (attack, hit) - a cloth limit of a skinned robe; widening the shoulder blend to 25 cm lowered p99 from 2.47.
  Gap check: no leg weight off the skirt; sleeves, strips and hands carry only their own arm.
- G5: hand stretch <= 4.1x (left hand in the death), 1.5-2.6x elsewhere; dagger fist clearance 1.5-1.7 cm.
- G6: the robe is open (hem, cuffs), so contacts are proximity only; `sword_clear.py` turns the dagger hand <= 33
  degrees where the blade would enter the robe.
- Blade: edge-first share attack 0.77, walk 0.96, hit 0.88 at roll 105 degrees (`blade_edge_gate.py` needed a
  `BLADE_T` range for the short blade: its default 0.3-0.6 m sampled only the dagger's tip).
- Death: the skirt bones aim the hem at the ankles as the body tilts; the corpse lies flat (the first build stood on
  a 0.75 m skirt bell and the floor pass propped it up into a bow).
- Viewer: 3 tiers x 8 clips, no console errors; textured EEVEE frames in `work/r_glb/`. Not checked in game.

## Known limits

- The robe is skinned, not simulated: the hem follows the legs at 45 % and does not swing on its own.
- The face keeps Meshy's human shape (nose, lips) under the painted skull-like texture.
- The hair is a sheet on the head bone down to the shoulders, then on the spine (no separate strands).
- The robe holes of the native hem are painted, not cut.

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: Attack sinks to -9.1; Hit sinks to -2.6; Running sinks to -11.1; Standing sinks to -3.6; Walking sinks to -18.3; dying sinks to -6.0; standing at -3.6; walking sinks to -18.3.
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m430.glb export/mm7_m430.glb --lift-joints Attack Dead Death Hit Running Standing Walking --lift-only 'B_Skirt*,Robe_*,…' --ground-loop Running --ground-loop Standing --ground-loop Walking --raise Attack --raise Hit --ground-death Death Dead`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m430.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).

## Gait rollout (2026-10-31, package h09)

New clips appended to the installed source: `Jog` (Unarmed-Run-Forward, 0.70 s, stride 2.399) and `Sprint` (Unarmed-Sprint, 0.56 s, 3.795), the hidden legs planted on virtual soles (no foot geometry) and the body lifted only where the hem would sink. The installed `Walking` is rebound at its foot-joint stride 1.82 (was 1.366, which the stride gate rejects). `Running` stays, unbound.

Rebuild: `level_generation/creatures/gait_rollout_20261031/h09/scripts/rebuild.sh m430` (composes from the pre-gait copy
`h09/work/mm7_m430_pre_gait.glb` and `h09/jobs/`, runs `gait_gate.py` and `check_winding.py`), then
`python3 tools/install_model.py level_generation/creatures/gait_rollout_20261031/h09/export/mm7_m430.glb --world mm7 --name
mm7_m430.glb`. Bindings: `h09/bindings.yml` (applied by the rollout coordinator). A far-LOD repair, head-bob, floor or
reduction rerun on this model must re-graft these clips: copy the new installed source over the pre-gait copy and
rebuild. Details, gates and doubts: [h09 README](../gait_rollout_20261031/h09/README.md).

## Anim fix (2026-11-11, MM6–MM8 audit)

Walking's robe sheets (cloth 41.6 % bad) came from the 2026-10-21 floor fix bending the skirt bones; Walking's skirt
bones are back at rest and the clip is grounded with `--ground-loop` alone (cloth 7.5 %). Details, numbers and the
rebuild commands: [mm7_m430_animfix_claude](../mm7_m430_animfix_claude/README.md). A future floor fix must not use
`--lift-joints Walking` here.
