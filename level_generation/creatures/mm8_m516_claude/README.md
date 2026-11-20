# MM8 Thunder Lizard / Basilisk — m516

Rigged and integrated using the shared Claude non-humanoid playbook. The three native tiers are Young Basilisk, Basilisk and Elder Basilisk (monster IDs 88–90; descriptors Thunder Lizard A/B/C). Artistic acceptance remains with the user.

[Interactive review](http://127.0.0.1:8901/level_generation/creatures/mm8_m516_claude/review/viewer/) · [Native motion study](ANIMATION_STUDY.md) · [Canonical receipts](creature_3d_progress.json)

![Native sprite/model comparison](review/ingame/comparison.jpg)

## Attack revision 02 — 2026-10-18

The user requested a higher rear, sideways head-back wind-up and forward/right impact. Rechecking native aa–ah in front, profile and rear confirms a one-foot rear, asymmetric head tilt and downward diagonal bite. The new Attack raises the snout by 0.86 m above its ready pose, lifts the left foot 0.36 m while the right stays planted, opens the arm silhouette, then drives the head down/forward toward the creature's right. The impact remains at 1.0 s; the viewer's native anchors now follow the fitted timing.

[Native/model comparison](review/attack_revision_02/comparison.jpg) · [Native combat frames](review/attack_revision_02/native_contact.jpg) · [Preservation checks](review/attack_revision_02/preservation.json)

Normal/half-speed playback, front/profile/quarter anchors, all four LOD floor checks, export parity and the focused native actor regression pass. The revised attack was captured in Agar's Laboratory on NVIDIA/OpenGL. The other seven clips, original mesh, UVs, skin weights, bind and maps are byte-exact to the previous LOD0 export. Earlier outdoor/corpse captures still cover those preserved parts; outdoor and broad regression were not repeated for this clip-only revision. No additional generation credits were used.

## Delivered files

- `export/mm8_m516.blend`: editable 30-bone rig, eight baked actions, retained UV layers and packed A-tier textures.
- `export/mm8_m516_portable_a.glb`, `_b.glb`, `_c.glb`: standalone textured animated GLBs for ordinary glTF viewers.
- `export/mm8_m516.glb`: engine source with three region-palette variants, four colour LODs and four shadow LODs.
- `textures/`: separate 1K body/head base colour, normal, material and region maps; native palette ramps in `m516_ramps.json`. Runtime merges these into four 2080×1024 atlases and one material per tier.
- `references_hd/master_gate.json` and `references_head/master_gate.json`: selected full-body and detailed head references, hashes and review gates. All 170 native source-frame hashes were checked against `../mm8_m516/sources.json`.

The installed source is `assets_source/worlds/mm8/models/mm8_m516.glb`; `tools/install_model.py --world mm8` cooks the runtime copy into `assets_dev/worlds/mm8/models/`. The three entries in that world's `actors.yml` retain native gameplay, original sprites and unrelated bindings. No equipment, projectile or new ability was added.

## Fitting and motion

The long tail was fitted to the native profile, then given eight articulated joints. Measured hip/knee/hock/ankle chains use local two-bone IK and corrected anatomical skin weights. The torso shifts toward the supporting foot; the tail counters hip motion with a delayed tip wave. Hands, feet, jaw and frills retain separate controls.

| Clip | Seconds | Behaviour |
|---|---:|---|
| Standing | 2.0 | Breathing and restrained head/tail movement |
| Walking | 1.0 | Grounded alternating steps, 1.0 m stride |
| Running | 0.75 | Lower balanced torso, short flight phase, 1.8 m stride |
| Attack | 1.25 | Crouch, rear, bite at the native 1.0 s impact, recovery |
| Hit | 0.625 | Native asymmetric recoil and return |
| Death | 1.0 | Recoil, side collapse, relaxed feet and settling tail |
| Dead | 0.25 | Held final corpse pose |
| Fidget | 0.625 | Native head lift and open-mouth gesture |

Standing height is 1.992714 m; runtime scale 79.288852 reproduces the native 158-pixel standing height at frame scale 1.0. Native movement speeds, collision dimensions, attack timing and paralyze/stone effects remain table-owned.

## Geometry and materials

LOD triangles: **12,644 / 6,321 / 3,158 / 1,579**. All vertices have at most four normalized weights; the rig has 30 bones. The 15% bent-pose reduction preserves face, finger/toe and seam detail. Surface error is 2.24 mm at the 99th percentile, with protected vertices unchanged. The existing retexture detail normals are retained on the unchanged UV islands; there is no additional sculpt or retopology pass.

Native palettes 516/518/519 supply the shared scale, underside, frill and iris ramps. Dark pupils remain unmasked; claw masks exclude finger scales. Maps use class-based roughness and AO-modulated specular masks under the current engine PBR contract. The final runtime winding check reports zero inverted closed components. At 290 pixels high, even LOD3 retains over 95% silhouette overlap in front, profile and three-quarter views.

## Verification

`review/checks/` contains source/export pose parity, dense floor/loop sampling, stance velocity, reduction, runtime influence and LOD checks. Exported poses match the authoring mesh within 0.1 mm. Walking/running stance velocity errors are below 0.000014 m/s. Death interpolation has a sub-5 mm floor excursion on the two-metre authoring model; the held corpse clears the floor. Separate corpse-region assertions check body, head and tail support.

The viewer checks all 24 tier/clip combinations. `review/playback/` records every action at normal and half speed; `review/shots/` covers palettes, face, both hands, feet, profile and remains. Native captures use the real NVIDIA/OpenGL desktop renderer at the playbook cameras in New Sorpigal (`oute3.odm`) and Agar's Laboratory (`6d19.blv`), with matched sprite views, LOD checks and a live bite/hit/death sequence. These captures are visual checks, not a performance benchmark.

The ordinary `openyamm` build passed. The Thunder Lizard actor-binding regression passes. The broader MM8 snapshot reports **26 passed, 5 unrelated failures**: missing Triton/Cyclops presentation, Unicorn horn bounds, and Water Elemental/Necromancer standing-height checks. See `review/checks/mm8_regression_final.log`. A transient concurrent Water Elemental material-extension failure was resolved before the retained native captures; production manifests were preserved.

Android was not run. User artistic approval has not been recorded.

## Reproduction and cost

The `scripts/` directory preserves geometry fitting, rigging, animation, UV transfer/packing, AO, texture composition, export auditing, LOD construction and runtime finishing. Use the project lease with `tools/run_creature_blender.sh`; refresh motion before export, prepare the actor GLB, generate LODs, refresh authored maps, prepare viewer tiers, then finish the runtime GLB and install it. `pack_editable.py` packs the native A appearance after portable exports are built. Review with `tools/run_creature_review.py` and the retained native input tours.

Meshy receipts total **25 credits**: 5 for Smart Topology, 10 for body retexture and 10 for head retexture. The rejected initial local-path request consumed zero credits. No humanoid rigging or paid animation job was used.
