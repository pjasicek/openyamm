// Packed facade mask sampling for opaque face materials (BModel and indoor). Include this
// file after material_lighting.sh in face-family shaders only; terrain variants own slot 4
// for the material LUT. The mask shares the diffuse texture's UV and repeat behavior and is
// sampled as single-level linear channel data (never sprite-alpha filtered, no mip chain).
// u_materialWetness.w carries the per-material presence flag: unmasked draws bypass the
// sample entirely, and the neutral mask (0, 1, 1, 1) keeps every term unchanged.
SAMPLER2D(s_texMaterialMask, 4);

vec4 sampleMaterialMask(vec2 diffuseTexcoord)
{
    if (u_materialWetness.w < 0.5)
    {
        return vec4(0.0, 1.0, 1.0, 1.0);
    }

    return texture2D(s_texMaterialMask, diffuseTexcoord);
}
