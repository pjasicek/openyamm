
#include "common.sh"

SAMPLER2D(s_texColor, 0);
#if SPRITE_ATLAS
SAMPLER2D(s_spriteMask, 1);
SAMPLER2D(s_spriteLookup, 2);
uniform vec4 u_spriteAtlasRect;
uniform vec4 u_spriteAtlasTexel;
uniform vec4 u_spriteChroma;
uniform vec4 u_spriteSecondChroma;
uniform vec4 u_spriteThirdChroma;
uniform vec4 u_spriteFourthChroma;

vec3 spriteRgbLookup(vec3 index)
{
    return texture2DLod(s_spriteLookup, vec2((index.y * 33.0 + index.z + 0.5) / 1089.0,
        (index.x + 0.5) / 33.0), 0.0).rgb;
}

vec3 spriteRgbDisplacement(vec3 color)
{
    vec3 position = clamp(color, 0.0, 1.0) * 32.0;
    vec3 lo = floor(position);
    vec3 hi = min(lo + 1.0, vec3(32.0, 32.0, 32.0));
    vec3 f = position - lo;
    vec3 a = mix(spriteRgbLookup(lo), spriteRgbLookup(vec3(lo.x, lo.y, hi.z)), f.z);
    vec3 b = mix(spriteRgbLookup(vec3(lo.x, hi.y, lo.z)), spriteRgbLookup(vec3(lo.x, hi.y, hi.z)), f.z);
    vec3 c = mix(spriteRgbLookup(vec3(hi.x, lo.y, lo.z)), spriteRgbLookup(vec3(hi.x, lo.y, hi.z)), f.z);
    vec3 d = mix(spriteRgbLookup(vec3(hi.x, hi.y, lo.z)), spriteRgbLookup(hi), f.z);
    return mix(mix(a, b, f.y), mix(c, d, f.y), f.x);
}
#endif

vec2 billboardTextureUv(vec2 uv)
{
#if SPRITE_ATLAS
    return clamp(u_spriteAtlasRect.xy + uv * u_spriteAtlasRect.zw,
        u_spriteAtlasRect.xy + u_spriteAtlasTexel.xy * 0.5,
        u_spriteAtlasRect.xy + u_spriteAtlasRect.zw - u_spriteAtlasTexel.xy * 0.5);
#else
    return uv;
#endif
}

uniform vec4 u_billboardAmbient;
uniform vec4 u_billboardOverrideColor;
uniform vec4 u_billboardOutlineParams;
uniform vec4 u_fogColor;
uniform vec4 u_fogDensities;
uniform vec4 u_fogDistances;

float safeSmoothstep(float edge0, float edge1, float value)
{
    if (edge0 == edge1)
    {
        return 0.0;
    }

    float t = clamp((value - edge0) / (edge1 - edge0), 0.0, 1.0);
    return t * t * (3.0 - 2.0 * t);
}

float getFogRatio(float dist)
{
    if (u_fogDensities.w > 0.5)
    {
        return clamp((dist - u_fogDistances.x) / max(u_fogDistances.y - u_fogDistances.x, 1.0), 0.0, 1.0);
    }

    return
        u_fogDensities.x
        + (u_fogDensities.y - u_fogDensities.x) * safeSmoothstep(u_fogDistances.x, u_fogDistances.y, dist)
        + (1.0 - u_fogDensities.y) * safeSmoothstep(u_fogDistances.y, u_fogDistances.z, dist);
}

float sampleBillboardAlpha(vec2 uv, float vertexAlpha, float atlasLod)
{
    if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0)
    {
        return 0.0;
    }

#if SPRITE_ATLAS
    return texture2DLod(s_texColor, billboardTextureUv(uv), atlasLod).a * vertexAlpha;
#else
    return texture2D(s_texColor, billboardTextureUv(uv)).a * vertexAlpha;
#endif
}

void main()
{
    float atlasLod = 0.0;
#if SPRITE_ATLAS
    // Derive the footprint before UV clamping or divergent alpha/outline branches.
    vec2 pixelUv = v_texcoord0 * u_spriteAtlasRect.zw / u_spriteAtlasTexel.xy;
    vec2 dx = dFdx(pixelUv);
    vec2 dy = dFdy(pixelUv);
    atlasLod = clamp(0.5 * log2(max(max(dot(dx, dx), dot(dy, dy)), 1.0)), 0.0, u_spriteAtlasTexel.z);
#endif
    vec4 textureColor =
        (v_texcoord0.x < 0.0 || v_texcoord0.x > 1.0 || v_texcoord0.y < 0.0 || v_texcoord0.y > 1.0)
            ? vec4(0.0, 0.0, 0.0, 0.0)
#if SPRITE_ATLAS
            : texture2DLod(s_texColor, billboardTextureUv(v_texcoord0), atlasLod);
#else
            : texture2D(s_texColor, billboardTextureUv(v_texcoord0));
#endif
#if SPRITE_ATLAS
    if (u_spriteChroma.w > 0.5)
    {
        vec4 coverage = texture2DLod(s_spriteMask, billboardTextureUv(v_texcoord0), atlasLod);
        float neutral = min(textureColor.r, textureColor.b);
        float chroma = max(0.0, textureColor.g - neutral);
        vec3 target = vec3(neutral, neutral, neutral) + chroma * u_spriteChroma.rgb;
        if (u_spriteChroma.w > 1.5)
        {
            float luminance = dot(textureColor.rgb, vec3(0.2126, 0.7152, 0.0722));
            target = luminance * u_spriteChroma.rgb;
        }
        if (u_spriteChroma.w > 6.5)
        {
            textureColor.rgb = clamp(textureColor.rgb + coverage.r * spriteRgbDisplacement(textureColor.rgb), 0.0, 1.0);
        }
        else if (u_spriteChroma.w > 4.5)
        {
            float luminance = dot(textureColor.rgb, vec3(0.2126, 0.7152, 0.0722));
            float x = (floor(luminance * 255.0 + 0.5) + 0.5) / 256.0;
            if (u_spriteChroma.w > 5.5)
            {
                vec3 r = texture2DLod(s_spriteLookup, vec2(x, 0.125), 0.0).rgb;
                vec3 g = texture2DLod(s_spriteLookup, vec2(x, 0.375), 0.0).rgb;
                vec3 b = texture2DLod(s_spriteLookup, vec2(x, 0.625), 0.0).rgb;
                vec3 a = texture2DLod(s_spriteLookup, vec2(x, 0.875), 0.0).rgb;
                textureColor.rgb = clamp(textureColor.rgb * (1.0 - coverage.r - coverage.g - coverage.b - coverage.a)
                    + r * coverage.r + g * coverage.g + b * coverage.b + a * coverage.a, 0.0, 1.0);
            }
            else
            {
                vec3 targetLut = texture2DLod(s_spriteLookup, vec2(x, 0.5), 0.0).rgb;
                textureColor.rgb = clamp(mix(textureColor.rgb, targetLut, coverage.r), 0.0, 1.0);
            }
        }
        else if (u_spriteChroma.w > 3.5)
        {
            float luminance = dot(textureColor.rgb, vec3(0.2126, 0.7152, 0.0722));
            textureColor.rgb = clamp(textureColor.rgb * (1.0 - coverage.r - coverage.g - coverage.b - coverage.a)
                + luminance * (coverage.r * u_spriteChroma.rgb + coverage.g * u_spriteSecondChroma.rgb
                    + coverage.b * u_spriteThirdChroma.rgb + coverage.a * u_spriteFourthChroma.rgb), 0.0, 1.0);
        }
        else if (u_spriteChroma.w > 2.5)
        {
            float luminance = dot(textureColor.rgb, vec3(0.2126, 0.7152, 0.0722));
            textureColor.rgb = clamp(textureColor.rgb * (1.0 - coverage.r - coverage.g)
                + luminance * (coverage.r * u_spriteChroma.rgb + coverage.g * u_spriteSecondChroma.rgb), 0.0, 1.0);
        }
        else
        {
            textureColor.rgb = clamp(mix(textureColor.rgb, target, coverage.r), 0.0, 1.0);
        }
    }
#endif
    vec3 litColor = textureColor.rgb * (u_billboardAmbient.rgb + v_color0.rgb);
    litColor = mix(litColor, u_fogColor.rgb, u_fogDensities.z);
    vec4 shadedColor = vec4(litColor, textureColor.a * v_color0.a);
    float baseAlpha = shadedColor.a;
    vec4 fragmentColor = shadedColor;

    if (u_billboardOverrideColor.a > 0.001 && u_billboardOutlineParams.z > 0.001)
    {
        float outlineAlpha = 0.0;
        bool outlineOnly = u_billboardOutlineParams.w > 0.5;
        float enable1 = step(1.0, u_billboardOutlineParams.z + 0.001);
        float enable2 = step(2.0, u_billboardOutlineParams.z + 0.001);
        float enable3 = step(3.0, u_billboardOutlineParams.z + 0.001);
        float enable4 = step(4.0, u_billboardOutlineParams.z + 0.001);
        vec2 texel = u_billboardOutlineParams.xy;

        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(texel.x, 0.0), v_color0.a, atlasLod) * enable1);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(-texel.x, 0.0), v_color0.a, atlasLod) * enable1);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(0.0, texel.y), v_color0.a, atlasLod) * enable1);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(0.0, -texel.y), v_color0.a, atlasLod) * enable1);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(texel.x, texel.y), v_color0.a, atlasLod) * enable1);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(-texel.x, texel.y), v_color0.a, atlasLod) * enable1);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(texel.x, -texel.y), v_color0.a, atlasLod) * enable1);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(-texel.x, -texel.y), v_color0.a, atlasLod) * enable1);

        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(texel.x * 2.0, 0.0), v_color0.a, atlasLod) * enable2);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(-texel.x * 2.0, 0.0), v_color0.a, atlasLod) * enable2);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(0.0, texel.y * 2.0), v_color0.a, atlasLod) * enable2);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(0.0, -texel.y * 2.0), v_color0.a, atlasLod) * enable2);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(texel.x * 2.0, texel.y * 2.0), v_color0.a, atlasLod) * enable2);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(-texel.x * 2.0, texel.y * 2.0), v_color0.a, atlasLod) * enable2);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(texel.x * 2.0, -texel.y * 2.0), v_color0.a, atlasLod) * enable2);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(-texel.x * 2.0, -texel.y * 2.0), v_color0.a, atlasLod) * enable2);

        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(texel.x * 3.0, 0.0), v_color0.a, atlasLod) * enable3);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(-texel.x * 3.0, 0.0), v_color0.a, atlasLod) * enable3);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(0.0, texel.y * 3.0), v_color0.a, atlasLod) * enable3);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(0.0, -texel.y * 3.0), v_color0.a, atlasLod) * enable3);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(texel.x * 3.0, texel.y * 3.0), v_color0.a, atlasLod) * enable3);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(-texel.x * 3.0, texel.y * 3.0), v_color0.a, atlasLod) * enable3);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(texel.x * 3.0, -texel.y * 3.0), v_color0.a, atlasLod) * enable3);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(-texel.x * 3.0, -texel.y * 3.0), v_color0.a, atlasLod) * enable3);

        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(texel.x * 4.0, 0.0), v_color0.a, atlasLod) * enable4);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(-texel.x * 4.0, 0.0), v_color0.a, atlasLod) * enable4);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(0.0, texel.y * 4.0), v_color0.a, atlasLod) * enable4);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(0.0, -texel.y * 4.0), v_color0.a, atlasLod) * enable4);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(texel.x * 4.0, texel.y * 4.0), v_color0.a, atlasLod) * enable4);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(-texel.x * 4.0, texel.y * 4.0), v_color0.a, atlasLod) * enable4);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(texel.x * 4.0, -texel.y * 4.0), v_color0.a, atlasLod) * enable4);
        outlineAlpha = max(outlineAlpha, sampleBillboardAlpha(v_texcoord0 + vec2(-texel.x * 4.0, -texel.y * 4.0), v_color0.a, atlasLod) * enable4);

        if (baseAlpha <= 0.001 && outlineAlpha > 0.001)
        {
            fragmentColor = vec4(u_billboardOverrideColor.rgb, outlineAlpha * u_billboardOverrideColor.a);
        }
        else if (outlineOnly)
        {
            fragmentColor = vec4(0.0, 0.0, 0.0, 0.0);
        }
    }

    if (fragmentColor.a <= 0.001)
    {
        discard;
    }

    float fogRatio = getFogRatio(v_depth);
    vec3 foggedColor = mix(fragmentColor.rgb, u_fogColor.rgb, fogRatio);
    gl_FragColor = vec4(foggedColor, fragmentColor.a);
}
