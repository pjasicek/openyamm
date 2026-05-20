$input v_texcoord0, v_depth, v_worldPosition, v_texcoord1, v_flowInfo

#include "common.sh"

SAMPLER2D(s_texColor, 0);

uniform vec4 u_fogColor;
uniform vec4 u_fogDensities;
uniform vec4 u_fogDistances;
uniform vec4 u_fxLightPositions[8];
uniform vec4 u_fxLightColors[8];
uniform vec4 u_fxLightParams;
uniform vec4 u_secretPulseParams;
uniform vec4 u_outdoorFaceAlphaParams;

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
    return
        u_fogDensities.x
        + (u_fogDensities.y - u_fogDensities.x) * safeSmoothstep(u_fogDistances.x, u_fogDistances.y, dist)
        + (1.0 - u_fogDensities.y) * safeSmoothstep(u_fogDistances.y, u_fogDistances.z, dist);
}

float getFogAlpha(float dist)
{
    return 1.0 - safeSmoothstep(u_fogDistances.y, u_fogDistances.z, dist);
}

vec3 getFxLighting(vec3 worldPosition)
{
    vec3 lighting = vec3(u_fxLightParams.y, u_fxLightParams.y, u_fxLightParams.y);

    for (int i = 0; i < 8; ++i)
    {
        if (float(i) >= u_fxLightParams.x)
        {
            continue;
        }

        vec3 toLight = u_fxLightPositions[i].xyz - worldPosition;
        float radius = max(u_fxLightPositions[i].w, 1.0);
        float dist = length(toLight);
        float attenuation = 1.0 - safeSmoothstep(0.0, radius, dist);
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
        vec2 atlasMin = v_flowInfo.xy;
        vec2 atlasMax = v_flowInfo.zw;
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
    else
    {
        texcoord.xy += v_flowInfo.xy * u_secretPulseParams.y;

        if (v_flowInfo.z > 0.5)
        {
            float lavaPhase = sin(mod(u_secretPulseParams.y, 8.0) * 6.2831853 / 8.0);
            texcoord.y += lavaPhase;
        }
    }

    vec4 textureColor = texture2D(s_texColor, texcoord);
    textureColor.rgb = mix(textureColor.rgb, u_fogColor.rgb, u_fogDensities.z);
    vec4 litTextureColor = vec4(
        textureColor.rgb * getFxLighting(v_worldPosition),
        textureColor.a * u_outdoorFaceAlphaParams.x);

    if (v_texcoord1.x > 0.5 && u_secretPulseParams.x > 0.5)
    {
        float pulse = 0.5 + 0.5 * sin(u_secretPulseParams.y * 4.0);
        litTextureColor.rgb *= vec3(1.0, pulse, pulse);
    }

    float fogRatio = getFogRatio(v_depth);
    float fogAlpha = getFogAlpha(v_depth);
    vec4 fogColor = vec4(u_fogColor.rgb, fogAlpha);
    gl_FragColor = mix(litTextureColor, fogColor, fogRatio);
}
