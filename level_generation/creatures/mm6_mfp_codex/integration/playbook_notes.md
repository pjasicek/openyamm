# Production lessons — current after review round 1

- Keep the canonical texture set shared by every LOD. Reload it from disk before export; packed Blender images can silently retain an earlier bake. Body/head atlas merging must preserve the shared cache across LODs.
- A bright forearm triangle can be a real boundary hole plus bad repair UVs. Close the hole with existing vertices and give its cap a separate padded UV patch. A 64 px appended strip preserves the original 1K texel density; do not overlap an occupied skin island.
- Match face and body luminance in linear colour, with the same neck field on both sides of the seam. Preserve facial detail; use smooth common skin illumination rather than projecting clothing shadows into exposed skin.
- Fit fingers using actual mesh fingertip landmarks, not bone display tails. Inspect the palm side and measure all five digits against the real handle at every held time and every LOD.
- Reverse grip needs both a fixed wrist and the correct signed blade edge. Rotate the attachment around its handle axis; choose impact from actual maximum tip speed, then validate signed edge lead.
- Use the shared gate runner unchanged. Supply anatomical elbow/palm axes, garment openings and per-LOD regions in the project config. For the asymmetric skirt, each half has its own moving opening plane.
- Skin/normal appearance should be reviewed in the exported GLB viewer. Auxiliary Blender reimport/splitting can shade differently. Disable stale bind-pose frustum culling in the local review viewer so close-up animated props remain visible.
- Preserve initial-yaw Mixamo rest-delta retargeting during forward falls. Keep Dead identical to the final Death pose. Delete fractional helper keys before rebaking twist and retain all eight Blender actions explicitly.
- Recheck the exported GLB after retiming; use the accessor's actual final sample for viewer duration metadata (the 240 Hz export truncates a fractional end by about 1 ms).

Original production notes, including now-superseded per-LOD map choices, are preserved in `../work/round1/before/integration/playbook_notes.md`.

## Review round 2

- Lit-sprite luminance pasted around cylinders encodes directional skin bands. Keep native pigment/mean and let mesh lighting supply highlights; explicitly distinguish this from historical albedo P90/P95 equality.
- Measure every UV island against surface area. Re-unwrapping at real 4K density fixes stretch; enlarging the old bitmap does not.
- Project each lower-LOD face to its matching source surface piece; keep all corners within one continuous UV island. Old lower-LOD UV layouts were not reliable correspondence.
- Denoise face pigment across UV seams in surface space. Exclude gold and preserve dark features; packed-UV blur mixes unrelated islands and creates patches.
- Derive repeat cloth from the selected HD costume reference and map it in physical units.
- Refresh skin normals after hole repairs; reload authoritative maps at export.
- Preserve the accepted cut/blow, shorten only recovery and verify the requested endpoint with the shared sampler.
