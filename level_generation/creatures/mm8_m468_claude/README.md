# MM8 Vampire — m468

> **Installed model reduced (2026-10-19):** the installed model is now the reduction from [`../mm8_m468_reduce_claude/`](../mm8_m468_reduce_claude/README.md) (LOD0 10,268 -> 6,776). This project's exports and master remain the unreduced production; the rollback source is in `../mm8_m468_reduce_claude/work/`.

Full Claude-playbook production requested 2026-10-18. Technical review is recorded separately from user artistic acceptance.
Canonical status: `creature_3d_progress.json`. Original 2D assets remain unchanged.

## Identity and likeness

Merged monster IDs 52–54 are `Vampire (monster) A/B/C`: Vampire Minion, Vampire and Greater Vampire.
Sprite groups m469/m470/m471 use native palettes 469/470/471. Only the torn trousers vary: green, purple and red.
The pale bald head, pointed ears, red eyes, fangs, bare clawed feet and short brown vest remain shared.
`references_native/source_inventory.json` preserves all 192 original BMP hashes; `references_native/three_tiers.png`
shows the actual palette distinction. The embedded BMP placeholder palette is not used for production colours.

The Devil supplied the movement benchmark: readable raised claws, wrist roll, facial intent, foot support and recovery.
The Vampire retains its own lean anatomy and five long clawed digits. There is no weapon or full cape.

## Motion and timing

`review/motion_selection.json` records local source clips, hashes and rejected alternatives. No paid animation jobs.
All clips use a fitted source-frame rig with world-rotation retargeting, individual fingers, a jaw hinge and distributed
arm twist. Elbow fitting, continuous wrist weights, collar weights and bare-foot support were checked on exported geometry.

| Clip | Seconds | Source and adaptation |
| --- | ---: | --- |
| Standing | 4.0333 | Mutant breathing idle; supported guard |
| Walking | 1.4333 | Mutant walking; narrow grounded stalk, travel removed |
| Running | 0.7333 | Standard run; restrained body flight and bare-foot toe-off |
| Attack | 2.0000 | Zombie Attack (1); raised right claw, rapid strike, guarded recovery |
| Cast | 1.6667 | Unarmed dual attack cast; continuous gather then both palms present |
| Hit | 0.5000 | Unarmed frontal hit; fits the native 0.625-second hit |
| Fidget | 1.3333 | Alert idle; expressive head/upper-body motion |
| Death | 1.2000 | Forward armed death; eased entry and grounded settling |
| Dead | 1.0000 | Exact final Death pose held |

Melee contact is at 77/60 seconds; cast release at 35/30 seconds. The runtime aligns those moments with the native
1.25-second action and plays the remaining animation at source speed. Native recovery remains 80/70/60 ticks from
action start, so a new action can interrupt the visual recovery. Gameplay tables and sprite timings are unchanged.
Walk/run strides are 1.82103545/2.82296493 metres. Scale is 114.47878993 from the native 187-pixel standing body.
Both palm sockets charge and release spells; two eye sockets are available without an added eye-glow effect.
Head look is limited to 20 degrees yaw and 10 degrees pitch.

## Geometry and textures

The selected Smart Topology body started at 15,299 triangles. The fitted original head is retained; upper outer
canines were lengthened locally. Reduction protects the face, hands and feet. LOD0 has 10,268 triangles; lower levels have 5,134, 2,566 and 1,276.
Body and head texture returns match every uploaded triangle and corner; their geometry never replaces the fitted rig.
A 61-face ear UV overlap was repaired by translating texture patches into padded space, with no normal-tangent rotation.
Final UV checks report zero overlaps, degenerates or out-of-range faces. The head retains its independently painted detail.

Maps use 1K body and head sets, then a padded 2080×1024 runtime atlas and one source material per tier. The standard cooker adds visible back-face triangles. Native palette ramps
recolour only trousers. Roughness and specular masks follow skin, leather, cloth, eyes, mouth, ivory and brass geometry.
Both returned normal maps were measured as -Y and converted once to glTF +Y. AO is baked into colour at low strength;
ORM red stores the runtime specular mask, green roughness, blue metallic.

The lowest LOD follows the playbook's approximate halving budget (12.5% target, 13% gate), rather than the shared
runner's older 10% default. Sole and wrist contact vertices are protected. Shadow meshes are tucked inside the colour
surface, excluding the hands and feet. UV seam duplicates are deduplicated for sole measurements in the shared gate
runner; its focused numeric regressions cover that measurement.

## Delivery and evidence

- `export/mm8_m468.glb`: runtime-ready model with three tiers, nine clips and colour/shadow LODs.
- `work/m468_textured_master.blend`: packed editable model, fitted skeleton and animations.
- `review/viewer/`: shared interactive comparison viewer with all tiers, native anchors and frame feedback.
- `review/final_gates/`, `review/uv_validation.json`: exported geometry and UV checks.
- `review/playback/`: final normal and half-speed recordings; `review/playback_clay/` retains the motion review.
- `review/ingame/`: native indoor/outdoor sprite comparisons, distance levels and motion poses.
- `review/completion.json`: exact installed hashes, counts, tests and review receipts.

Meshy: 30 credits total (body 5, rig 5, body texture 10, head texture 10), within the 100-credit project budget.
Verification: 6,618 deformation checks, 16 gate-runner regressions and 51 MM8 tests (6,400 assertions) pass.
Independent Blender skinning differs by less than 0.001 mm. The broader animation suite has two pre-existing MM6
Devil fixture mismatches (death timing/visibility and LOD counts); this task leaves those assets and expectations alone.

No Android, Vulkan or performance benchmarking is included. Native desktop captures establish visual integration only.


## Motion revision 02 — user frame review

Current viewer revision: **m468_motion_v2**. Cast frames 13–44 (viewer 48 fps) now gather continuously instead of repeating a pose. Attack wind-up has less sideways torso lean and a bent claw arm; the free left elbow follows a lower anatomical recovery path. Strike and spell-release timing are unchanged.

The selected UV master, packed editable master, portable exports, three viewer tiers and installed source/runtime GLBs all include the correction. Geometry, skin weights, UVs, embedded textures and the other seven clips are unchanged.

Validation: all 6,618 export gates pass; 51 focused tests / 6,400 assertions pass. The new casting regression reproduces all 31 frozen steps on the old installed asset and passes on the revision. Agent review covers frontal/side close-ups, normal/half-speed playback and eight affected poses each indoors/outdoors on the desktop GPU. No Android, Vulkan or performance run for this animation-only revision.

[Revision evidence](review/motion_revision_02/review.json), [preservation check](review/motion_revision_02/preservation.json), [final gates](review/final_gates/gates.json), [playback](review/playback/playback.json). Original completion and model/master checkpoints are retained under `review/motion_revision_02/`.

Reproduce the motion edit with `scripts/revise_motion_02.py` through `tools/run_creature_blender.sh`, then `scripts/build_delivery.py`, `scripts/viewer_tiers.py` and the normal `tools/install_model.py` cook. The revision script reads the preserved pre-review UV master and is repeatable.
