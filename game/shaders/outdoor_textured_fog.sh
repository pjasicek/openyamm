
#include "common.sh"

#if TERRAIN_TEXTURE_ARRAY
SAMPLER2DARRAY(s_texColor, 0);
SAMPLER2DARRAY(s_texTerrainWater, 1);
#elif TERRAIN_DECORATION
SAMPLER2DARRAY(s_texColor, 0);
#else
SAMPLER2D(s_texColor, 0);
#endif

#if BAKED_SOURCES
SAMPLER2D(s_texLightmap, 2);
uniform vec4 u_bakedTerrainBounds;
#include "outdoor_baked_lighting.sh"
#endif

uniform vec4 u_fogColor;
uniform vec4 u_fogDensities;
uniform vec4 u_fogDistances;
uniform vec4 u_cameraPosition;
uniform vec4 u_fxLightPositions[8];
uniform vec4 u_fxLightColors[8];
uniform vec4 u_fxLightParams;
uniform vec4 u_secretPulseParams;

#if !TERRAIN_TEXTURE_ARRAY && !TERRAIN_DECORATION
#define MATERIAL_OUTDOOR_RESPONSE 1
#include "material_lighting.sh"
#endif

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

float getFogAlpha(float dist)
{
    if (u_fogDensities.w > 0.5)
    {
        return 1.0;
    }

    return 1.0 - safeSmoothstep(u_fogDistances.y, u_fogDistances.z, dist);
}

vec3 getFxLighting(vec3 worldPosition, float sunlight)
{
    // Only base illumination receives sunlight; local spell/torch contributions retain their full strength.
#if BAKED_SOURCES
    float base = 0.0;
#else
    float base = u_fxLightParams.y * sunlight;
#endif
    vec3 lighting = vec3(base, base, base);

    for (int i = 0; i < 8; ++i)
    {
        if (float(i) >= u_fxLightParams.x)
        {
            continue;
        }

        vec3 toLight = u_fxLightPositions[i].xyz - worldPosition;
        float radius = max(u_fxLightPositions[i].w, 1.0);
        float distanceSquared = dot(toLight, toLight);
        float inverseRadiusSquared = 1.0 / (radius * radius);
        float attenuation = 1.0 - clamp(distanceSquared * inverseRadiusSquared, 0.0, 1.0);
        attenuation *= attenuation;
        lighting += u_fxLightColors[i].rgb * (u_fxLightColors[i].w * attenuation * u_fxLightParams.z);
    }

    return clamp(lighting, vec3(0.0, 0.0, 0.0), vec3(2.0, 2.0, 2.0));
}

void main()
{
    vec2 texcoord = v_texcoord0;
    bool terrainWater = v_texcoord1.x < -0.5;

    if (terrainWater)
    {
#if TERRAIN_TEXTURE_ARRAY
        vec2 atlasMin = vec2(0.0, 0.0);
        vec2 atlasMax = vec2(1.0, 1.0);
#else
        vec2 atlasMin = v_flowInfo.xy;
        vec2 atlasMax = v_flowInfo.zw;
#endif
        vec2 atlasSpan = max(atlasMax - atlasMin, vec2(0.0001, 0.0001));
        vec2 localCoord = clamp((texcoord - atlasMin) / atlasSpan, vec2(0.0, 0.0), vec2(1.0, 1.0));

        float pongPhase = sin(mod(u_secretPulseParams.y, 10.0) * 6.2831853 / 10.0);
        float swirlPhase = mod(u_secretPulseParams.y, 8.0) * 6.2831853 / 8.0;
        float ripplePhase = mod(u_secretPulseParams.y, 6.0) * 6.2831853 / 6.0;

        vec2 localDelta = vec2(0.0, 0.0);
        localDelta.x += pongPhase * 0.004 * sin(localCoord.x * 6.2831853);
        localDelta.y += pongPhase * 0.004 * sin(localCoord.y * 6.2831853);
        localDelta.x += 0.0025 * sin(swirlPhase + localCoord.y * 6.2831853);
        localDelta.y += 0.0025 * cos(swirlPhase + localCoord.x * 6.2831853);
        localDelta.x -= 0.001 * cos(ripplePhase + (localCoord.y + localDelta.y) * 6.2831853 * 6.0);
        float edgeFade =
            safeSmoothstep(0.04, 0.12, localCoord.x)
            * (1.0 - safeSmoothstep(0.88, 0.96, localCoord.x))
            * safeSmoothstep(0.04, 0.12, localCoord.y)
            * (1.0 - safeSmoothstep(0.88, 0.96, localCoord.y));
        localDelta *= edgeFade;

        texcoord = clamp(texcoord + localDelta * atlasSpan, atlasMin, atlasMax);
    }
#if !TERRAIN_TEXTURE_ARRAY && !TERRAIN_DECORATION
    else
    {
        texcoord.xy += v_flowInfo.xy * u_secretPulseParams.y;

        if (v_flowInfo.z > 0.5)
        {
            float lavaPhase = sin(mod(u_secretPulseParams.y, 8.0) * 6.2831853 / 8.0);
            texcoord.y += lavaPhase;
        }
    }

#endif
#if TERRAIN_TEXTURE_ARRAY
    // Water repeats across cells. Land and shore overlays retain clamped sampling because
    // their opposite edges can contain different materials. Both samplers share one array.
    vec4 textureColor;
    if (terrainWater)
    {
        textureColor = texture2DArray(s_texTerrainWater, vec3(texcoord, v_flowInfo.x));
    }
    else
    {
        textureColor = texture2DArray(s_texColor, vec3(texcoord, v_flowInfo.x));
    }
#elif TERRAIN_DECORATION
    vec4 textureColor = texture2DArray(s_texColor, vec3(texcoord, v_flowInfo.x));
#else
    vec4 textureColor = texture2D(s_texColor, texcoord);
#endif
#if TERRAIN_DECORATION
    if (v_texcoord1.y > 0.5)
    {
        textureColor = vec4(1.0, 1.0, 1.0, 1.0);
    }
    textureColor *= v_color0;
    // Fixed object-space noise, independent of frame/time and screen position. Coverage fades
    // without shrinking the mesh or introducing a screen-space pattern that crawls over it.
    vec2 coverageCell = floor(v_texcoord0 * vec2(128.0, 96.0));
    float coverageNoise = fract(sin(dot(coverageCell, vec2(12.9898, 78.233))
                                   + v_texcoord1.w * 91.7) * 43758.5453);
    if (textureColor.a < 0.4 || v_texcoord1.z <= coverageNoise)
    {
        discard;
    }
#endif
    if (textureColor.a <= 0.1)
    {
        discard;
    }

    textureColor.rgb = mix(textureColor.rgb, u_fogColor.rgb, u_fogDensities.z);
#if BAKED_SOURCES
    vec2 bakedUv = (v_worldPosition.xy - u_bakedTerrainBounds.xy) / u_bakedTerrainBounds.zw;
    vec3 baked = bakedSourceLighting(texture2D(s_texLightmap, bakedUv), texture2D(s_texBakedSky, bakedUv));
    vec4 litTextureColor = vec4(bakedSurfaceColor(textureColor.rgb,
        baked + getFxLighting(v_worldPosition, 0.0)), textureColor.a);
#else
    vec4 litTextureColor = vec4(textureColor.rgb * getFxLighting(v_worldPosition, v_sunlight), textureColor.a);
#endif

#if !TERRAIN_TEXTURE_ARRAY && !TERRAIN_DECORATION
    // Bounded artistic sheen and emissive in the existing display-encoded domain, before the
    // secret tint and outdoor fog. Zero material contribution keeps the color unchanged.
    litTextureColor.rgb += outdoorMaterialFaceResponse(
        v_worldPosition,
        v_worldNormal,
        vec3_splat(1.0));
#endif

    bool classicSecret = v_texcoord1.x > 0.5 && v_texcoord1.x < 1.5;
    bool authoredPerception = v_texcoord1.x >= 1.5;
    bool perceptionDetected = u_secretPulseParams.z >= v_texcoord1.x - 2.0;
    bool secretDetected =
        (classicSecret && u_secretPulseParams.x > 0.5)
        || (authoredPerception && perceptionDetected);

    if (authoredPerception && !perceptionDetected)
    {
        discard;
    }

    if (secretDetected)
    {
        float pulse = 0.5 + 0.5 * sin(u_secretPulseParams.y * 4.0);
        litTextureColor.rgb *= vec3(1.0, pulse, pulse);
    }

    float fogDistance = length(v_worldPosition - u_cameraPosition.xyz);
    float fogRatio = getFogRatio(fogDistance);
    float fogAlpha = getFogAlpha(fogDistance);
    vec4 fogColor = vec4(u_fogColor.rgb, fogAlpha);
    gl_FragColor = mix(litTextureColor, fogColor, fogRatio);
}
