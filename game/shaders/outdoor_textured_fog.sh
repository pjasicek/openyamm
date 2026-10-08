
#include "common.sh"
#include "world_clip.sh"

#if TERRAIN_TEXTURE_ARRAY
SAMPLER2DARRAY(s_texColor, 0);
SAMPLER2DARRAY(s_texTerrainWater, 1);
SAMPLER2DARRAY(s_texWaterCoverage, 4);
#elif TERRAIN_DECORATION
SAMPLER2DARRAY(s_texColor, 0);
#else
SAMPLER2D(s_texColor, 0);
#endif

#if BAKED_SOURCES
SAMPLER2D(s_texLightmap, 2);
uniform vec4 u_bakedTerrainBounds;
#include "outdoor_baked_lighting.sh"
#else
#if SUN_SHADOWS
#include "sun_shadows.sh"
#endif
uniform vec4 u_outdoorSunlight;
#endif

uniform vec4 u_cameraPosition;
uniform vec4 u_secretPulseParams;
uniform vec4 u_waterSurfaceControl;

#include "outdoor_lighting.sh"

void main()
{
    clipWorldPosition(v_worldPosition);
    vec2 texcoord = v_texcoord0;
    bool terrainWater = v_texcoord1.x < -0.5;

#if TERRAIN_TEXTURE_ARRAY
    if (terrainWater && v_flowInfo.y > 0.5
        && (u_waterSurfaceControl.x > 0.5 || abs(u_worldClipPlane.z) > 0.5))
    {
        float coverage = v_texcoord1.x < -1.5
            ? texture2DArray(s_texWaterCoverage, vec3(texcoord, v_flowInfo.x)).r : 1.0;
        if (coverage >= 0.999)
        {
            discard;
        }
    }
#endif

    if (terrainWater && v_texcoord1.x > -1.5)
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
    if (terrainWater && v_texcoord1.x > -1.5)
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
#if !SUN_SHADOWS
    // Lit per vertex (vs_terrain_decoration); decorations are never secret faces.
    textureColor.rgb = mix(textureColor.rgb, u_fogColor.rgb, u_fogDensities.z) * v_flowInfo.yzw;
    float decorationFogDistance = length(v_worldPosition - u_cameraPosition.xyz);
    gl_FragColor = mix(textureColor, vec4(u_fogColor.rgb, getFogAlpha(decorationFogDistance)),
        getFogRatio(decorationFogDistance));
    return;
#endif
#endif
    if (textureColor.a <= 0.1)
    {
        discard;
    }

    textureColor.rgb = mix(textureColor.rgb, u_fogColor.rgb, u_fogDensities.z);
#if BAKED_SOURCES
    vec2 bakedUv = (v_worldPosition.xy - u_bakedTerrainBounds.xy) / u_bakedTerrainBounds.zw;
    vec3 baked = bakedShadowedSourceLighting(texture2D(s_texLightmap, bakedUv),
        texture2D(s_texBakedSky, bakedUv), bakedUv, v_worldPosition);
    vec4 litTextureColor = vec4(bakedSurfaceColor(textureColor.rgb,
        baked + getFxLighting(v_worldPosition, 0.0)), textureColor.a);
#else
    vec4 litTextureColor = vec4(textureColor.rgb * getFxLighting(v_worldPosition, v_sunlight), textureColor.a);
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
