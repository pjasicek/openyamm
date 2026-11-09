# Goblin skirt and belt reconstruction test — 2026-09-24

Requested: rebuild skirt/belt on a copy of the existing goblin and show a baked comparison.

## Review

- [Front comparison](comparison_front.jpg): original 200K source, rebuilt geometry, same rebuilt geometry with normal map.
- [Front / quarter / back comparison](comparison.jpg).
- [Whole-character context](full_baked.png).
- [Actual GLB reimport render](export_front.png).
- [Editable Blender scene](skirt_rebuild.blend).
- [Standalone skirt and belt](skirt_belt_1392.glb).
- [Whole-character review GLB](goblin_skirt_rebuild_review.glb).

## What changed

The original body, clothing and pouch were one connected mesh. The garment was rebuilt as 17 pointed,
thin hanging strips and a closed belt, **1,392 triangles total**. Explicit UV islands and fixed triangulation
support a 2K tangent-space normal map baked from the preserved dense repaired master. Rivets, stitching,
shallow trim and buckle relief are in that map, not individual high-density geometry.

Source strip directions and lengths were measured from a cylindrical surface study. Smooth cross-sections
were fitted to strip centers, excluding the pouch, so vertex placement does not fall into gaps or onto rivets.
Outer/inner normals were separated at thin edges before baking. A radial cage controls projection.

To insert the garment, the fused waist region was cut from a **copy** of the 200K intermediate. Covered waist
and upper-thigh surfaces were rebuilt and joined to the actual cut rings. Thus this test also changes the
anatomy immediately underneath the clothing; it is not a clothes-only swap with every body vertex unchanged.
The pouch exterior was clipped into a separate object and its hidden cut surfaces closed. Original back plates
and rivets were retained. Head, arms and other geometry outside the local cut region retain their source shapes.
All original GLBs, repaired master and prior candidates remain unchanged.

## Counts and limits

- New skirt + belt: **1,392 triangles**, including thickness/back faces, one UV layout, 2K normal map.
- Retained body plus fitted covered anatomy: 143,409 triangles.
- Preserved pouch: 6,980 triangles.
- Retained back hardware: 1,268 triangles.
- Whole-character review export: **153,049 triangles**, verified by reimport.

The whole-character file is a component test with source-density surroundings, **not a runtime LOD**.
The new clothing has no final color/roughness textures, rig, weight painting or animation clearance test.
Some projected borders and the belt fit still need refinement. The torso/thigh replacement is a fitted
underlayer for this comparison, not accepted deformation topology. Normal-map appearance requires renderer
normal-map support; it was evaluated in Blender, not OpenYAMM.

This demonstrates that the characteristic strip forms and mapped relief can survive with inexpensive clothing
geometry. It does not establish that the full goblin is finished, fits the 8–12K target or deforms correctly.
No paid Meshy operation was performed and no new reference images were generated.

## Reproduction and saved state

`skirt_rebuild.blend` is the saved editable scene with packed normal map. The Blender UI is left in
`Goblin - Rebuilt Skirt and Belt v2` with the new garment selected. Session authoring scripts are under `scripts/`;
they depend on the named reference scenes from the existing goblin checkpoints. Measurements and export hashes
are in the JSON reports. Earlier intermediate study files are not accepted production alternatives.

Next: refine clothing fit/projection where visible, preserve this separated part for low-mesh assembly, and
apply the same deliberate geometry/bake division to the remaining body/equipment before rig tests.
