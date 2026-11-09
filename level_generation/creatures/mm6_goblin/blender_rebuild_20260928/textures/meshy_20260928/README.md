# First Meshy PBR return

**Historical first-pass record.** The later [eye repair](../eye_repair_20260928/README.md) is complete and the
[current review](../../review/eyes_feet_correction/index.html) includes corrected walking-foot angles.
The raw maps and source GLB in this directory remain unchanged. Descriptions of identical maps/actions below
refer to this first integration, before that authorized correction.

The user supplied `/home/pjasicek/Downloads/Meshy_AI_mm6_goblin_texturing_0928122704_texture.glb` after the local
model/animation pass. [meshy_return.glb](meshy_return.glb) preserves that input unchanged. It contains the parked
sword and an unrigged A-pose. [Input audit](import_audit.json) records source hashes and the comparison.

## What came back

- 12,916 triangles and 10,589 split vertices: triangle connectivity, vertex order and UV coordinates are identical
  to the supplied texturing GLB. Meshy flattened the 26 objects into one mesh/material and applied object transforms.
- Maximum world-position difference after accounting for the parked sword transform is about 0.0001 mm.
  Vertex normals also match within numerical tolerance. No topology reconstruction or weight transfer is needed.
- Three 2048×2048 JPEG images are embedded: [base color](base_color.jpg),
  [metallic/roughness](metallic_roughness.jpg), and [tangent normal](normal.jpg).
  In the packed material map, green is roughness and blue is metallic. Base color uses sRGB; both data maps use
  Non-Color. The material's normal strength and metallic/roughness factors are all 1.

## Integration

Transferred the material onto the authored parts and their existing UVs. Retained the 11 named material regions
so skin, armor, eyes, cloth, sword and accessories remain editable separately; all share the same three images.
The merged returned geometry is not used in the rigged delivery. The 72-joint skeleton and all seven animation
clips are unchanged. [Material assignment](material_assignment.json) records the mapping to the previous slots.

The [textured Blender project](../../delivery/mm6_goblin_textured.blend) and
[textured rigged GLB](../../delivery/mm6_goblin_textured_rigged.glb) are separate from the preserved modeling
baseline. Required images are packed. All three exported map payloads are byte-identical to the user's return;
no image regeneration, recoloring, normal inversion or normal-map combination was performed.

Compared the incoming Meshy normals with the earlier sculpt-normal proof on the same color texture. The old proof
emphasizes different cheek/nose forms. The current delivery uses Meshy's supplied normal map; the earlier proof
and original materials remain available in the Blender project, but do not contribute to the delivered material.

## Visual finding in this first pass

The generated face texture includes a pair of painted eyes **above the actual mesh eye openings**. Those painted
eyes appear together with the modeled eyeballs/irises/pupils, producing a doubled-eye effect. A diagnostic render
using the original eye materials confirms the misplaced eye paint is on the skin. Changing only the eyeball
materials or switching normal maps does not remove it.

The required art correction was localized to the eye region of the existing texture atlas: replace the misplaced eyes
on the skin with continuous brow/eyelid skin, and keep a single aligned eye treatment on the actual eye surfaces.
Recheck corresponding normal/roughness detail in that region. Preserve the UV layout, model and animations.
The rest of this first texture pass is retained for user review; it is not declared artistically final.

See the [visual and motion review](../../review/texturing_20260928/index.html), including the face diagnosis and
normal comparison. Previews render the actual reimported textured GLB. Structural validation verifies bind-surface
and UV parity, unchanged animation channels and inverse bind matrices, and embedded texture identity. A 21-pose
reimport check measures all joints plus skin/sword deformation to within approximately 0.004 mm.

Reproduction uses `authoring/inspect_meshy_return.py`, a Blender GLB import into the isolated inspection scene,
`transfer_meshy_materials.apply()` and `.export()`, then `check_textured.py` and the parameterized
`roundtrip`/`previews` helpers. The original downloaded file is read-only throughout.
