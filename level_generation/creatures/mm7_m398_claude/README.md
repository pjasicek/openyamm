# MM7 Skeleton Warrior (m398) — Claude rig-first project

Batch D, model 1 ([batch file](../mm7_batches/BATCH_D.md)). Descriptors 397 Skeleton (palette 399, green breeches),
398 Skeleton Warrior (palette 63, blue-violet) and 399 Skeleton Lord (palette 64, brown-red). **Exported, not
installed** (batch rule: the user decides later). Status: technically complete, pending user review.

[Review viewer](review/viewer/index.html) (served at
`http://127.0.0.1:8912/level_generation/creatures/mm7_m398_claude/review/viewer/`) ·
[clip sheets](review/clips_three_quarter.png) · [HD masters](references_hd/selected_views_review.png) ·
[head masters](references_head/selected_views_review.png)

| Item | Value |
|---|---|
| Exports | `export/mm7_m398.glb` (body, LODs, 3 tier variants, head merged), `export/mm7_m398_sword.glb` (attachment on `Sword`), `export/mm7_m398_arrows.glb` (attachment on `Arrows`); editable master `work/rig_v6.blend` |
| Triangles | body LOD0/1/2/3 8,593 / 4,274 / 1,512 / 499 (incl. sword 314 and arrows 92 before the split) (was 11,507 / 5,737 / 2,043 / 676). Second cut on the textured master (user review 2026-10-20, `reduce_textured.py`, targets per garment in `scripts/reduce2.json`; protected: Finger, Thumb bones, the head/body texture boundary, head region weight 0.4); both texture sets get new UVs and are baked garment by garment from the unreduced copy `work/rig_v6_full.blend` (`rebake_uv.py` -> `texturing/rebake_v2/`, read by the compose script) |
| Mesh | Smart Topology of the HD three-quarter master: 88 separate pieces (bones, cuirass, gauntlets, breeches, boots, studs). The body's skull came back as a flat face with a loose chin, so a head-only Smart Topology (skull with jaw, separate teeth, spiked helmet with rivets) replaces it (`graft_head.py`) |
| Rig | 52 `B_*` bones cloned from the humanoid set + forearm/upper-arm twist; joints from the pieces (elbow knobs, gauntlet wrist rings, femur/tibia centreline at the kneecaps, boot ankle rings) cross-checked with Meshy's auto-rig; mesh-measured gauntlet hands, fingers by connectivity |
| Weights | per piece (`weights_fix.py`): bones rigid on their bone (limb pieces split at the joint with a 2-3 cm ramp), cuirass/ribs/spine on a smooth spine chain, gauntlets/boots limited to their own limb, breeches to pelvis and legs; gap check: 0 vertices with arm or leg weight off their limb's pieces |
| Clips (30 fps) | Standing Mixamo Standard Idle (3.0 s); Walking Mixamo Walk (1.0 s, 1.656 m stride); Running Mixamo Standard Run, high-pelvis fit (0.73 s, 1.8 m); Attack Mixamo Sword And Shield Slash planted, 20 % of its legs with IK steps, ready pause, spine twist limited (1.5 s, blow 0.75 s); Hit set Unarmed get-hit F1 (0.5 s); Death Mixamo Standing React Death Backward, travel halved (3.63 s); Dead; Fidget Mixamo Annoyed Head Shake planted (2.57 s) |
| Textures | body 1K + head 1K (Meshy retextures from the HD masters / head turnaround), AO graded, ORM red = per-class specular mask; one region (breeches); ramps keep the texture's luminance with each tier's native chroma; props atlas 512 px (own paint) |
| Meshy credits | **45 of 100**: Smart Topology 5, auto-rig 5, head Smart Topology 5, body retexture 10 (v1, superseded), body retexture 10 (v2), head retexture 10 |

## Installed 2026-10-20 (user request; commands as run)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m398_claude/export/mm7_m398.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m398_claude/export/mm7_m398_sword.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m398_claude/export/mm7_m398_arrows.glb --world mm7
```

[actors_m398_binding.yml](actors_m398_binding.yml) is added to `assets_dev/worlds/mm7/models/actors.yml` (scale 119.5 =
native stand 173 px x 1.2 over the 1.737 m Standing pose; B and C use `scale_reference: Skeleton Warrior A`, so the
engine applies their sprite scales 1.3 / 1.4; stride 1.656 m, run 1.8 m; blow 0.75 s; head look on B_Neck/B_Head;
sword and arrows attachments). The tiers walk at 220/250/280 units/s, under the run threshold (2.4 x scale = 287+),
so Running is a spare clip.

## Replay

`scripts/rebuild.sh` (`STAGE=rig`, then `STAGE=anim`), texture chain once (`export_uploads.py`, Meshy
`retexture_v2` and `head_retexture_v1`, `transfer_uv.py -- work/rig_v5h.blend meshy/retexture_v2 work/rig_v6.blend`),
`make_props.py`, then `scripts/build_runtime.sh` (once on the textured master: `reduce_textured.py`, `rebake_uv.py`) (uv rasters, AO, `compose_m398.py`, export, prepare, LODs, shadow fix,
region variants, sword/arrows split, head merge), `viewer_tiers.py`, `update_viewer_manifest.py`.

## Gates (final export)

- G3: wrists/elbows/ankles within 2-4 cm of Meshy's estimate, mirror differences <= 1.5 cm; Meshy's knees sat 6 cm in
  front of the kneecaps and were replaced by the leg centreline. Hand frames from the fitted knuckle line.
- G4: arm stretch p99 <= 1.32 (attack), max 1.94 (hit, left hand). G5: hand stretch <= 2.18x; sword fist clearance
  1.6-1.75 cm (handle radius 1.5 cm).
- G6: closed shells (bones, boots, skull, helmet) <= 0.5 cm in every clip. The inside test now confirms with ray parity
  (a flat back-rib piece 13 cm from the gauntlet passed the 45-degree cone test at its rim). `sword_clear.py` turns the
  sword hand <= 21 degrees where the blade would enter the body or open shells (idle, walk, run, hit, fidget, death).
- Feet: grounded soles -2.6..+2.2 cm (walk), idle -1.9 cm. Blade: edge-first share 0.74 in the attack (+0.73 cutting
  edge leading), 0.83 in the walk (roll 45 degrees from the knuckle line, bar1 rule).
- Viewer: `tools/run_creature_review.py ... check`: 3 tiers x 8 clips, no console errors. Textured EEVEE frames of the
  exported GLB: `work/r_glb/`.
- Not checked in game (optional for this batch).

## What went wrong and was fixed

- **Reduction collapsed the gauntlets**: with the hands protected, the whole 730-triangle cut fell on the forearm tubes,
  which shrank to small cones; the clay sheets showed it but it was only caught on the first textured render, after
  the first body retexture (10 credits) was painted on that mesh. The gauntlets are no longer reduced; the body was
  retextured again (`retexture_v2`); the head upload was byte-identical, so the head retexture stayed valid.
- **Battlecry fidget** threw the skull far back over the cuirass; replaced by a planted head shake.
- **Tier ramps**: rank-matching the native cloth pixels copied the sprites' baked white highlights into the top of
  the ramp (grey cloth); the ramps now keep the texture's luminance with each tier's native chroma.
- Feet (user review 2026-10-20: feet on their outer edges, ankle twist, head bob): `foot_level.py` from batch C (mm7_m218_claude: sole pitch + roll weighted by sole flatness, capped at 20 deg, smoothed; the run levelled too) and `walk_bob.py` from batch A (mm7_m154_claude: walk pelvis height averaged over both steps and smoothed, legs re-solved onto the same ankle paths) after clip timing. Idle/attack/fidget soles 0.5-1.1 deg from flat (were 9-10 deg on the outer edge); walk mid-stance 0.7-5.6 deg (were 8-30); foot turn per frame unchanged from the source clips (walk/run <= 25.9 deg, hit <= 14.0); walk pelvis second difference 4.79 -> 0.73 cm. Batch A's per-frame roll on the hit made its landing snap (21 deg per frame); batch C's flatness weighting does not.

## Known limits

- The breeches and cuirass are skinned, not simulated; the hands come within 3 mm of the breeches' flare in the idle
  (proximity, no penetration).
- The sword's red streaks are painted procedurally; the blade reads a little pink at a distance.
- Both arrows ride one `Arrows` joint under B_Spine2 (the flank arrow does not follow B_Spine1 separately).
- The run carries the blade across the chest (clear of the body); it is never reached at the tiers' speeds.
- The native death collapses into a heap of bones; the model falls back whole.

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: Attack sinks to -2.6; Attack sinks to -2.8; Attack sinks to -3.0; Standing sinks to -2.7; Walking sinks to -3.4; Walking sinks to -3.6; Walking sinks to -3.9; dying sinks to -2.9; dying sinks to -3.1; dying sinks to -3.3; standing at -2.7; walking sinks to -3.4; walking sinks to -3.6; walking sinks to -3.9.
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m398.glb export/mm7_m398.glb --lift-joints Attack Dead Death Standing Walking --lift-only 'B_Skirt*,Robe_*,…' --ground-loop Standing --ground-loop Walking --raise Attack --ground-death Death Dead`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m398.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).

## Gait rollout (2026-10-31, package h09)

New clips appended to the installed source: `Jog` (humanoid set Unarmed-Run-Forward, 0.74 s, stride 2.7115) for Standard's chase and `Sprint` (Unarmed-Sprint, 0.60 s, 3.7857) for MAW's; bound as `run` / `sprint`. `Running` stays in the GLB, no longer bound. The jog lifts the sword arm 18 deg while the right knee comes through.

Rebuild: `level_generation/creatures/gait_rollout_20261031/h09/scripts/rebuild.sh m398` (composes from the pre-gait copy
`h09/work/mm7_m398_pre_gait.glb` and `h09/jobs/`, runs `gait_gate.py` and `check_winding.py`), then
`python3 tools/install_model.py level_generation/creatures/gait_rollout_20261031/h09/export/mm7_m398.glb --world mm7 --name
mm7_m398.glb`. Bindings: `h09/bindings.yml` (applied by the rollout coordinator). A far-LOD repair, head-bob, floor or
reduction rerun on this model must re-graft these clips: copy the new installed source over the pre-gait copy and
rebuild. Details, gates and doubts: [h09 README](../gait_rollout_20261031/h09/README.md).
