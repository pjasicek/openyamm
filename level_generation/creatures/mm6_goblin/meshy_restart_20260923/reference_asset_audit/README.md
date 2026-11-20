# Dark Knight reference audit — 2026-09-24

User supplied `/home/pjasicek/Downloads/the-dark-knight-infinity-blade` as a counterexample to our goblin triangle budgets.
Inspected actual GLB and textures, imported into isolated Blender scene, rendered with/without maps.
Original files untouched. This is a visual/structural reference, not an asset installed into OpenYAMM.

## Measured asset

- **7,834 triangles**, one mesh primitive and one material, including character, sword and shield.
- 23,210 exported vertices: this file contains extensive split vertex data. Triangle count alone does not describe all costs.
- One 2,048 x 2,048 color texture and one 1,024 x 1,024 tangent normal texture.
- 27 skin joints, eight animation entries; animation quality/timing was not evaluated.
- No metallic/roughness texture bindings in this GLB. Metallic factor is 0; material uses specular/IOR extensions.
- Blender importer bone-widget Icosphere excluded from measurements and hidden in renders.

[Comparison](comparison.jpg): geometry only, color only, color plus normal map, same pose/camera/lighting.
Fine armor engraving, rivets, panel lines and much cloth detail are represented by the maps.
The color texture already contains substantial painted/baked shading. The mesh retains large plate shapes,
helmet outline, limbs, sword and shield silhouette. These renders inspect the supplied export, not original-game lighting.

## Correction to our goblin evaluation

Our prior clay-only comparisons were insufficient to judge final detail quality or establish a 20–30K requirement.
Missing shallow detail should be evaluated with a bake and color before declaring it a geometry failure.
Confirmed silhouette/strip distortions and deformation problems remain geometry concerns.

A local [goblin normal-bake proof](../bake_probe_30k/comparison.jpg) demonstrates recovered torso,
armor and skirt relief on unchanged geometry. This quick bake has projection artifacts (notably armor/chest),
temporary auto UVs and no color textures; it is evidence of the mechanism, not an accepted asset.

Proposed next production experiment: a deliberately budgeted roughly 8–12K-triangle goblin including sword,
with UVs and dense-source normal baking early enough to judge final appearance. This is a test target,
not a demonstrated result. Do not use 30K as an assumed minimum or select it simply because its untextured
surface resembles the sculpt more closely. Preserve all source and reduction candidates for comparison.
Normal-map rendering and skeletal support are still required in OpenYAMM; Blender appearance is not engine acceptance.
