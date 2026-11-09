# MM8 Troll — native m476

> **Installed model reduced (2026-10-18):** the installed body and club are now the reduction from [`../mm8_m476_reduce_claude/`](../mm8_m476_reduce_claude/README.md) (LOD0 11,738 + 3,087 -> 8,802 + 1,575), with black hair specks fixed and planted feet levelled. This project's exports and master remain the unreduced production; rollback sources are in `../mm8_m476_reduce_claude/work/`.


Rigged Clubman, Warrior and Chieftain, made with the shared Claude humanoid playbook. The fitted source-frame rig keeps the forward head, short bowed legs and long arms. The horned ram-skull club is held in the anatomical **left hand**, as in the original.

## Selected assets and review

- [Interactive reviewer](review/viewer/index.html): three tiers, eight clips, native references, orbit/scrub controls and exact-frame feedback.
- [Editable textured master](work/troll_master.blend); [fitted rig and transferred UVs](work/rig_v6.blend).
- [Portable assembled LOD0](export/mm8_m476_prepared.glb); the reviewer bakes each tier's palette for three.js.
- Runtime body: [mm8_m476.glb](export/mm8_m476.glb). Rigid attachment: [mm8_m476_club.glb](export/mm8_m476_club.glb).
- Authoritative generation receipts, selected hashes, validation and acceptance state: [creature_3d_progress.json](creature_3d_progress.json).
- All clips at normal and half speed: [recordings and sampled frames](review/playback/). These recordings precede the final palette/iron colour correction; geometry and animation are the same.
- Native comparisons and action captures: [review/ingame](review/ingame/).

Technical and agent visual completion are distinct from user artistic approval. No user artistic acceptance is implied.

## Native identity and scale

The bitmap family is **m476**, but its three runtime sprite groups are **m477, m478 and m479**, using palettes **477, 478 and 479**. The merged descriptors/monster ids are **Troll A/B/C, 58/59/60**. `m476.yml` is not this Troll's runtime group. Source BMPs require their explicit ACT palettes; their embedded palettes are not the appearance authority.

[Native inventory](source/native_inventory.json) records 160 original BMP hashes, palettes and all SFT slots, including Death's two initial hit frames. [Native RGBA references](source/native/) are decoded originals. The native standing frame is 148 px at scale 1.699997: **251.599556 game units**. Each tier has the same native scale, so the bindings explicitly use **148.041018286 units/metre**, calibrated from the model's **1.699525975 m** standing height. An unnecessary `scale_reference` dependency was removed after the real-game check exposed an unloaded-sprite dependency during debug summons.

## Production

The selected full-body and separate skull-club references are in `references_hd/`; dedicated head views are in `references_head/`. Reference prompts, generation returns and hashes are retained there. Some historical prompt entries summarize the request; they are not labelled exact transcripts. The body was generated unarmed so the left hand could be fitted around the separately generated handle.

| Meshy job | Task | Credits |
|---|---|---:|
| Body, Smart Topology | `01a14dd4-6adf-7191-b954-31228240f297` | 5 |
| Skull club, Smart Topology + texture | `01a14dd5-7f60-7120-bfb5-0f6ecd3a73f4` | 15 |
| Joint estimate/auto-rig | `01a14dd6-cca0-7642-815e-4377c593c4ea` | 5 |
| Body retexture | `01a14dee-58b7-765c-98cb-6c59816d6960` | 10 |
| Head retexture | `01a14dee-8fb0-7519-99d3-885d7b43c368` | 10 |

**45 credits total**, all successful, no pending jobs. No paid animation jobs; [motion selection](review/motion/selection.json) records the local source clips and hashes. Native source references were inspected before generation; the candidate mace clips were previewed before modelling.

The source-frame rig uses Meshy's joint estimates plus measured ankle/wrist rings, symmetric limb placement, connectivity-fitted fingers and forearm/upper-arm twist bones. Corrections retain the crouch rather than stretching the body to a mannequin: fitted leg rotations, grounded/level boots, a small idle leg IK correction, arm clearance, a curved thumb web and local arm-weight smoothing. The final rig has **57 bones including Club** and at most **eight normalized influences**. Pruning retained at least **98.71%** of each pre-pruned weight sum. The closed hair shells have outward winding; a small five-edge neck hole was closed with three triangles and adjacent UVs preserved.

| Role | Local source / treatment | Duration |
|---|---|---:|
| Standing | ArmedIdle, fitted crouch and planted boots | 2.0 s |
| Walking | ArmedWalk, mirrored to left-hand carry | 0.8 s |
| Running | ArmedRunForward, mirrored | 0.8 s |
| Attack | MaceAttackR1, mirrored; 0.833 s anticipation, original strike/follow-through speed | 1.4 s |
| Hit | ArmedGetHitF1 with short standing transitions | 0.5 s |
| Fidget | ArmedIdleAlert1 with standing transitions | 2.0 s |
| Death | UnarmedDeath1; left arm/club kept outside the body | 1.3 s |
| Dead | Last Death pose held | 1.0 s |

The measured strike event is **0.916666667 s**, within the native 1 s attack's timing tolerance. Walking and running strides are **1.484 m** and **2.937 m**, measured from planted-foot speed. Native Troll speeds do not normally reach the engine's run threshold; Running remains available and verified in the reviewer.

Body and head retextures transferred with **0.0 mm** positional mismatch. Shared 1K maps preserve fine texture detail, unify skin colour and darken the iron to match the native sprites. Only the cloth edging is recoloured, using native green-region indices and corresponding tier palettes. Body/head maps merge into a **2080×1024** atlas; the club keeps a separate 1K set. No full texture duplication per runtime tier. Normal maps are converted to glTF +Y; final checks are positive for body and club. Materials are single-sided and opaque.

Combined body/club LOD0 is approximately **14.8k triangles**. Four colour LODs and smaller shadow geometry are included; exact counts are in the progress record. The higher body count protects the face, shoulder silhouette and open clothing boundaries. Decimating the torso further collapsed the waist, so it is retained at LOD0. This is an explicit silhouette-driven budget choice.

## Validation and reproduction

The selected arm-skin gate, after final eight-weight pruning, measures p99 stretch at **1.72× maximum** at tested extremes. Fingers are measured separately over every frame: **3.03× maximum**, below the playbook's approximate 4.5× limit. Idle soles remain **3 mm** above the floor; walking/attack planted soles stay within approximately **−6 to +13 mm**. Running intentionally has airborne phases; death transitions to body contact.

The half-frame contact scan reports no suspect intersections in seven animated roles. It uses closest-surface normals and proximity because the torso/clothing shells are open, supplemented by front/side/three-quarter visual inspection; it is not a proof for closed-volume containment. Numerical reports and source logs are retained in `work/` and `review/validation/`. The generic ring-size probe is unsuitable for this Troll's thick arms and emits null samples; arm-skin stretch, fitted twist weights and actual visual playback are the applicable evidence.

The stock three.js reviewer uses four influences; its close-up deformation is an approximation of the native renderer's eight-weight skinning. The native indoor/outdoor captures verify the actual cooked assets, materials and attachment. Browser playback and runtime checks are not hardware performance benchmarks.

To rebuild from the selected fitted/UV master without generation or paid jobs, claim the project and run:

```sh
tools/run_creature_blender.sh --token TOKEN level_generation/creatures/mm8_m476_claude/scripts/build_assets.py
```

This runs composition → export → normal-map preparation → colour LODs → shadow LODs → shared palette variants → Club split → head/body atlas merge → winding/normal validation → portable viewer tiers. Refresh viewer hashes after rebuilding. Install both final exports with `tools/install_model.py --world mm8`; it writes authoritative `assets_source` files and cooks the runtime copies. Do not copy runtime models back into the project.

Runtime binding is in `assets_dev/worlds/mm8/models/actors.yml`. The focused regression is `mm8_troll_actor_models_keep_native_tiers_and_club` in `game/outdoor/HeadlessOutdoorDiagnostics.cpp`: three shared-body instances, all native animation roles, unchanged simulation, eight required clips and a club on each Club bone.

```sh
OPENYAMM_REGRESSION_FILTER=mm8_troll ./build/game/openyamm --world mm6 --headless-run-regression-suite actors
python3 tools/run_creature_review.py --project level_generation/creatures/mm8_m476_claude check
```

The development build and focused Troll regression pass. The broader MM6 actor suite reports **62 passed, 2 failed**: Demon tier loading and Ooze glossy material checks. Both failures reproduce identically with all three Troll bindings removed from an isolated asset copy; see [baseline evidence](review/validation/mm6_baseline.json). These unrelated failures remain unresolved. The final browser check switches all 24 tier/clip combinations without console errors.

Native captures use the playbook's New Sorpigal and Agar's Laboratory cameras and genuine hostile summons. The indoor fixture adds distant sprite preload actors in an isolated hard-linked asset tree; its changed scene is unlinked before writing. Production map data remains unchanged. The fixture record includes original/fixture hashes. `review/ingame/validation.json` records final run locations and checks.

No raw animation-library clips were added to runtime assets, no engine behavior was changed, and no changes were staged or committed. Android was not built or visually tested.
