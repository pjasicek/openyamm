$input v_texcoord0, v_color0, v_depth, v_worldPosition

#include "common.sh"
#include "sky_common.sh"
#include "world_clip.sh"

SAMPLER2D(s_texColor, 0);
uniform vec4 u_spriteAtlasRect;
uniform vec4 u_spriteAtlasTexel;
uniform vec4 u_billboardOutlineParams;
uniform vec4 u_billboardOverrideColor;
uniform vec4 u_fogColor;
uniform vec4 u_fogDensities;
uniform vec4 u_fogDistances;

float fogTransition(float start, float end, float distance)
{
    if (start == end)
    {
        return 0.0;
    }
    float t = clamp((distance - start) / (end - start), 0.0, 1.0);
    return t * t * (3.0 - 2.0 * t);
}

float fogRatio(float distance)
{
    if (u_fogDensities.w > 0.5)
    {
        return clamp((distance - u_fogDistances.x) / max(u_fogDistances.y - u_fogDistances.x, 1.0), 0.0, 1.0);
    }
    return u_fogDensities.x
        + (u_fogDensities.y - u_fogDensities.x)
            * fogTransition(u_fogDistances.x, u_fogDistances.y, distance)
        + (1.0 - u_fogDensities.y)
            * fogTransition(u_fogDistances.y, u_fogDistances.z, distance);
}

float spriteAlpha(vec2 uv, float lod)
{
    if (any(lessThan(uv, vec2_splat(0.0))) || any(greaterThan(uv, vec2_splat(1.0))))
    {
        return 0.0;
    }
    // Clamp within this pose's cell. Its existing mip gutters isolate it from adjacent poses.
    vec2 halfTexel = 0.5 * exp2(lod) * u_spriteAtlasTexel.xy;
    vec2 atlasUv = clamp(u_spriteAtlasRect.xy + uv * u_spriteAtlasRect.zw,
        u_spriteAtlasRect.xy + halfTexel, u_spriteAtlasRect.xy + u_spriteAtlasRect.zw - halfTexel);
    return texture2DLod(s_texColor, atlasUv, lod).a;
}

float surroundingAlpha(vec2 uv, vec2 dx, vec2 dy, float lod)
{
    vec2 diagonal0 = (dx + dy) * 0.70710678;
    vec2 diagonal1 = (dx - dy) * 0.70710678;
    float alpha = max(spriteAlpha(uv + dx, lod), spriteAlpha(uv - dx, lod));
    alpha = max(alpha, max(spriteAlpha(uv + dy, lod), spriteAlpha(uv - dy, lod)));
    alpha = max(alpha, max(spriteAlpha(uv + diagonal0, lod), spriteAlpha(uv - diagonal0, lod)));
    return max(alpha, max(spriteAlpha(uv + diagonal1, lod), spriteAlpha(uv - diagonal1, lod)));
}

void main()
{
    // Derivatives precede all divergent branches. Offsets follow screen pixels, including mirrored poses.
    vec2 dx = dFdx(v_texcoord0);
    vec2 dy = dFdy(v_texcoord0);
    vec2 pixelsPerUv = u_spriteAtlasRect.zw / u_spriteAtlasTexel.xy;
    vec2 pixelDx = dx * pixelsPerUv;
    vec2 pixelDy = dy * pixelsPerUv;
    float lod = clamp(0.5 * log2(max(max(dot(pixelDx, pixelDx), dot(pixelDy, pixelDy)), 1.0)),
        0.0, u_spriteAtlasTexel.z);
    clipWorldPosition(v_worldPosition);
    float centerAlpha = spriteAlpha(v_texcoord0, lod);
    if (centerAlpha >= 0.999)
    {
        discard;
    }
    float width = u_billboardOutlineParams.z;
    // Both radii retain thin weapons and limbs. Linear alpha filtering provides the antialiased edge.
    float dilatedAlpha = max(surroundingAlpha(v_texcoord0, dx * width, dy * width, lod),
        surroundingAlpha(v_texcoord0, dx * (width * 0.5), dy * (width * 0.5), lod));
    // Blend through soft alpha fringes; a zero-alpha gate would break restored silhouettes.
    // Subtraction also avoids filling the interior of uniformly translucent sprites.
    float coverage = max(dilatedAlpha - centerAlpha, 0.0);
    if (coverage < 0.001)
    {
        discard;
    }
    float outlineFogRatio = clamp(skyFogRatio(fogRatio(v_depth), v_worldPosition, v_depth, u_fogDistances.z), 0.0, 1.0);
    vec3 color = mix(u_billboardOverrideColor.rgb,
        skyFogDisplayColor(outlineFogRatio, u_fogColor.rgb, v_worldPosition), outlineFogRatio);
    gl_FragColor = vec4(color, coverage * v_color0.a * u_billboardOverrideColor.a);
}
