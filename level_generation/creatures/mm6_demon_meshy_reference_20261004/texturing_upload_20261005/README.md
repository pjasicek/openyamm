# MM6 demon — Meshy texturing handoff

[Open the upload and UV review](index.html).

Upload **mm6_demon_meshy_upload.glb** to Meshy's Retexture / AI Texturing workflow.
It contains the revision 7 demon only: 16474 triangles, one mesh, a shared UV atlas,
and the existing three simple materials. It is static in the original bind pose.
The death plume, ash, skeleton and animations are excluded from this upload.

The separate **mm6_demon_uv_master.blend** retains the original rig, all nine clips,
death effect and ash. Geometry, indexed triangles, weights, bind matrices, vertex normals
and animation curves match revision 7; UVs and seam flags are the authoring changes.
Keep this file as the animated source for applying returned textures.

## Meshy settings

- Enable **Use Original UV** / preserve existing UVs.
- Enable **PBR**, including base colour, normal, roughness and metallic maps.
- Use **4K** when available: small charts need enough texels and padding for clean seams.
- Use **references/native_front.png** as the main appearance reference. The native profile,
  three-quarter and back are included as additional guidance where supported.
- Use **meshy_prompt.txt** for text-guided texturing. The suggested palette is charcoal skin,
  green leather harness, ivory spikes/claws/teeth/skull, and pink-red eyes.

Meshy supports preserving uploaded UVs and generating PBR maps; see the
[Retexture documentation](https://docs.meshy.ai/en/api/retexture).
No Meshy generation or upload has been performed by this preparation step.
The references are original native pixels cropped and enlarged with nearest-neighbour sampling.

## UVs and checks

The atlas allocates separate regions to the body, head, each hand, feet and skull attachment.
Smart projection initializes the charts, minimum-stretch unwrap relaxes them, local seam cuts
resolve folded charts, and concave packing reduces wasted space. The final UVs stay in 0–1,
with no overlapping charts or degenerate UV triangles. Per-corner UV/geometry correspondence
is checked after importing the actual exported GLB.

[validation.json](validation.json) records exact preservation checks and one representative
pose from every clip. Numbered checker renders use the actual static GLB.
UV coordinates remain attached to the undeformed mesh under animation.

Return the generated GLB and its texture maps. Apply the maps to **Meshy_Atlas** in the UV master;
retain the original rig and effects. If Meshy returns several material texture sets, assign each
to its matching material slot. Check seams, face/skull detail and moving poses before final export.

## Reproduction

In Blender MCP, import **prepare_uv.py** and call **apply()** in the revision 7 scene.
Then run:

```sh
tools/run_creature_blender.sh level_generation/creatures/mm6_demon_meshy_reference_20261004/texturing_upload_20261005/check_and_render.py
python3 level_generation/creatures/mm6_demon_meshy_reference_20261004/texturing_upload_20261005/build_bundle.py
```

The checker image and four reference PNGs are preparation assets already included here.
Previous revision exports are preserved. Runtime integration is separate work.
