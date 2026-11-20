# MM6 goblin delivery review — 2026-09-08

This review covers the final top-level model files and their matching sprite set, not the earlier numbered
checkpoints. The last accepted source combines neck 3, surface/detail 2, motion 10, protected-face mesh reduction
and corrected UV interpolation. [Machine-readable integrity results](delivery_audit.json) bind the delivery to its
file hashes and ZIP. No self-assigned artistic score is used.

| Goal criterion | Delivered evidence and review result |
| --- | --- |
| Identity/proportions | [Four-view comparison](review/native_restored_model.png) places native, selected restored and final rendered figures at equal visible height without changing aspect ratio. Lean exposed body, separate plates, pointed head/ears, toothy face and right-hand curved blade remain recognizable. Missing native action views and ambiguous back markings are explicitly interpreted. |
| Model finish | [Actual GLB studio renders](review/export_glb/) cover front, side, rear, oblique, face, rear neck, torso, hand, feet, attack and corpse. Earlier primitive facial masses, separate neck cap, wrist step and stair-like armpit deformation were corrected and re-rendered. Current close-ups show connected skin, separate fingers/claws, modeled attachment thickness and coherent equipment. |
| Materials | Final baked color/normal/ORM were compared with source and reduced geometry, then actual GLB reimport. Last torso pigment patches were fixed by retaining true UV interpolation through reduction. Related skin surfaces share a consistent olive character; iron, brass, leather, teeth and eyes retain intentional differences. Three shared 4K atlases plus optional regions are preserved. |
| Deformation/motion | Seven named clips survive actual GLB import with exact durations. [Perspective playback/contact sheets](review/motion_playback_final_glb/README.md) and [directional contacts](spritesheets/previews/) were inspected, including free-palm orientation, sword grip, toe-off, strike/recoil and collapse. Dense imported Walk/Death samples check ground clearance. Death and Corpse bone matrices match exactly; loop error is only floating-point noise. |
| Practical editable asset | [Packed Blender file](mm6_goblin.blend) reopens as one mesh/one 88-bone rig plus studio camera/lights, with seven Actions and three packed used textures. [Reopen report](export_work/blend_reopen_report.json). GUI delivery scene was appended without deleting other scenes; MCP and viewport capture work. [GLB](mm6_goblin.glb) has one skin, four influences, tangents and seven zero-based clips. [Posing/reset instructions](README.md). |
| Sprite quality | 552 masters at 710×578, 552 RGBA PNGs and 552 shared-palette BMPs at 355×289; seven unlabeled eight-row atlases. Genuine opposite sides preserve weapon handedness. All frames pass nonempty/unclipped and mask/palette checks. All atlas cells match their standalone PNGs. [Native-size PNG/BMP comparison](spritesheets/previews/png_bmp_native_size.png) and selected eight-view action sequences were inspected. |
| Timing | Dense 10/16/12/1 frame counts retain precise display timing independently of continuous model keys. Attack/Death have separate positive-integer 12/10-frame legacy subsets preserving 0.75/0.625 seconds. Standing intentionally extends a static pose to a two-second idle. GIF rounding, endpoint sampling and Corpse hold are documented. |
| Reproducibility | [59-image native manifest](source_manifest.json), [AI reference/prompt index](reference_restoration/README.md), detailed source libraries, authoring/export/render/pack/review scripts, pose manifests and preserved revision checkpoints. All 59 audited original BMP hashes remain unchanged. |
| Handoff | [Model README](README.md), [sprite instructions](spritesheets/README.md), [calibration history](ART_CALIBRATION.md), [generic workflow additions](../SPRITE_TO_3D_WORKFLOW.md), focused validation reports and sprite ZIP. Final status is in [PROGRESS.md](PROGRESS.md). |

## Focused checks

The actual imported GLB has no unweighted vertices, at most four influences, and maximum weight-sum error about
1.45e-7. Its lowest checked Death point is +0.003655 m; Corpse is +0.010019 m. Walk and Death were evaluated at
121 times each to cover the demonstrated toe-off and interpolation risks. These are asset-specific checks, not
a general collision guarantee. The intended in-place walk speed is 0.853333 m/s. Source planted-foot drift with
matching travel was about 0.2 mm. [Imported motion report](export_work/imported_motion_report.json).

`pack_sprites.py` verifies every frame's nonempty interior alpha bounds, BMP mask and shared palette, source model
hash and positive legacy timing. `verify_delivery.py` additionally checks model/import provenance, required GLB
streams, every atlas cell, ZIP inventory/CRC and Python syntax. This work did not require an engine build or map
scenario suite. The source and exact final GLB were opened in Blender; no independent game-engine integration
or runtime performance benchmark is claimed.

## Interpretation and integration limits

This is a detailed stylized reconstruction. The low-resolution originals cannot establish every anatomical groove,
strap, jewelry piece or unseen action view, so AI detail remains a reviewed interpretation. Exposed-back markings
are ambiguous; the model uses the conservative design recorded in calibration. Leather tassets use authored hinge
animation rather than cloth simulation. Blender and GLB highlights can differ because the small Blender skin SSS
contribution is not exported and `KHR_materials_specular` support varies by consumer.

The mesh is 206,722 triangles with 14 material regions and three shared 4K textures. It is a detailed game-mesh
delivery with declared costs; no LOD chain or target-engine performance claim is supplied.
Sprite ground pivot is (177.5,277), 12 pixels above canvas bottom, so future native billboard installation must
account for that offset and consumer scale. Original MM6 variant mappings are unchanged. New runtime IDs, actor
installation and gameplay edits were excluded by the brief. These documented integration steps do not represent
uncompleted sprite/model generation.
