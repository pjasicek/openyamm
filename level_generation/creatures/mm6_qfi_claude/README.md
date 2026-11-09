# MM6 Demon Queen (qfi) — 3D model

Accepted by the user on 2026-10-13 (revision 3). Installed as `assets_dev/worlds/mm6/models/mm6_qfi.glb` (source
`assets_source/worlds/mm6/models/`), binding `zDemonQueen` in `assets_dev/worlds/mm6/models/actors.yml`.
Native study and plan: [ANIMATION_STUDY.md](ANIMATION_STUDY.md).

## What it is

One actor GLB with two parts, as the native sprite has the rock in the creature image:
- **Queen**: Meshy Smart Topology from Codex HD masters (`references_hd/`), with a head-only Smart Topology from a
  Codex head turnaround (`references_head/`) grafted on (the body return's face was soft and its horns lopsided).
  12,200 triangles (head 5,000), LODs 6,092 / 2,189 / 728. Body and head texture sets 1K each, merged into one
  material (`tools/merge_head_material.py`).
- **Rock alcove**: Meshy multi-image-to-3D from Codex rock masters (`references_rock/`, niche empty, no baked
  shadow), seam-welded and decimated to 4,000 triangles, rigid on its own `Rock` bone; flattened to 45 % depth (its
  back is against the room's end wall) and 1.1x so its apparent size matches the sprite from the room.
- Meshy: 60 credits (queen 5, head 5, rock 30, body and head textures 10 + 10).

## Rig and clips

Source-frame upper body (humanoid-set frames, bar1 rule) on a six-bone abdomen from the tip in the niche to the
waist; mesh-fitted hands and five finger chains (connectivity cut); forearm/upper-arm twist bones; palm sockets.
Weights: geodesic labels from visible bone seeds, the axial share redistributed along the abdomen-spine-neck chain,
finger pieces wholly on their chains, the graft's two neck surfaces on one Neck -> Head blend, upper-arm weight faded
out medially. Clips (local Mixamo, retargeted by world rotation; spine motion kept at 65 % because her pelvis is
planted on the abdomen):

| Clip | Source | Notes |
|---|---|---|
| Standing (also walk, fidget) | Breathing Idle | abdomen sway layer |
| Attack | Standing Melee Attack Downward | 0.25 s lead-in; blow at 1.05 s (`events.attack_melee`) |
| Cast (Incinerate) | Standing 1H Magic Attack 01 | release at 1.02 s from `Socket_Palm_R` |
| Hit | Standing React Large From Front | neck/head at 60 % (long neck) |
| Death / Dead | authored from qdea0-qdee0 | arms out, raised in a V, rock collapses to 66 % height while she sinks |

Gate (`scripts/clip_gate.py`): edge stretch p99 1.83-2.77, no arm penetration of the torso, armour stretch 1.0.
Revision 3 (user review: the steel cups deformed in the attack, Hit started with hunched shoulders): the breastplate
cups, studs and chest strap (`scripts/rigid_mask.py`, from the metal map and the black strap colour) are rigid on
B_Spine2 with a 3 cm skin feather; the straps over the shoulder tops blend into the clavicle only. Hit is applied as
its change from its own first frame on Standing. The Attack keeps 50 % of the source's spine, 55 % of its neck/head
and 60 % of its clavicle motion, so the downward strike no longer folds the head and shoulder over the chest.
Rock clearance (revision 2, user review: attack/hit went into the boulder): the rock sits 25 cm further behind her
and `scripts/clearance_fix.py` tips the abdomen chain forward on the frames that would enter the rock (smallest angle
that clears, smoothed; Attack up to 11 deg, Cast 25, Hit 24). `scripts/rock_gate.py`: head, arms and upper body
clear of the rock in every clip; only the abdomen tip rests 11-17 cm into the niche lip, as the native tucks it.
Single-edge maxima of 11-22x remain at a few spine/shoulder slivers left by decimation.

## Engine change

`actors.yml fixed_yaw_degrees` (`game/fx/WorldFxSystem.cpp/.h`): the model keeps that world facing instead of turning
with the actor, so the rock stays against the wall; a `look` block (spine, neck, head; 60 deg) turns her toward the
party. Regression `mm6_qfi_actor_model_keeps_rock_facing_and_native_size`.

## Rebuild

Claim `mm6:qfi` with `tools/creature_workspace.py`, then (Blender scripts via `tools/run_creature_blender.sh`):
`rock_load` -> `compose_check` -> (`rigid_mask` on the textured master) -> `build_rig` -> `retarget_mixamo` -> `author_clips` -> `twist_bones` -> `carry_uv`
(UVs from the textured master; `export_uploads` + `transfer_uv` only for a new paid texture) -> `clearance_fix` ->
`rock_gate` -> `clip_gate`, then
`python3 scripts/compose_qfi.py` and `scripts/build_runtime.sh <token> --install`. Editable master: `export/mm6_qfi.blend`.

## Review evidence

Viewer: http://127.0.0.1:8901/level_generation/creatures/mm6_qfi_claude/review/viewer/ (`review/viewer/`, the runtime GLB;
verified with `claude_shared/check_viewer.mjs`, all six clips). It has no floor: in Death/Dead the sunken abdomen shows
below the rock's base, which the game floor hides.
`review/ingame/` (Hive room, same camera: sprite vs model front and at an angle, live sequence of cast, attack, hit and
death), `review/death_vs_native.png`, `review/clips/`, `review/stress_sheet.png`, `review/joint_xray_sheet.png`.

## Known limits

- The model is lit by the room and reads brighter than the sprite, whose rock carries a baked blue-black shadow.
- After death the engine's corpse-satchel handling removes the body (sprite and model alike); the collapsed-rock
  corpse is visible only until then.
- Single-edge stretch spikes at decimated slivers (see Gate); not visible in the captures.
