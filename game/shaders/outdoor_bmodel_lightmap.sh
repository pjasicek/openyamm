
#include "common.sh"

SAMPLER2D(s_texColor, 0);
SAMPLER2D(s_texLightmap, 1);
#if BAKED_SOURCES
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

#define MATERIAL_OUTDOOR_RESPONSE 1
#include "material_lighting.sh"
#include "material_mask.sh"

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

vec3 getFxLighting(vec3 worldPosition)
{
#if BAKED_SOURCES
    vec3 lighting = vec3_splat(0.0);
#else
    vec3 lighting = vec3(u_fxLightParams.y, u_fxLightParams.y, u_fxLightParams.y);
#endif

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
    texcoord.xy += v_flowInfo.xy * u_secretPulseParams.y;

    if (v_flowInfo.z > 0.5)
    {
        float lavaPhase = sin(mod(u_secretPulseParams.y, 8.0) * 6.2831853 / 8.0);
        texcoord.y += lavaPhase;
    }

    vec4 textureColor = texture2D(s_texColor, texcoord);
    if (textureColor.a <= 0.1)
    {
        discard;
    }

#if BAKED_SOURCES
    textureColor.rgb = mix(textureColor.rgb, u_fogColor.rgb, u_fogDensities.z);
    vec4 bakedSun = texture2D(s_texLightmap, v_lightmapUv);
    vec4 bakedSky = texture2D(s_texBakedSky, v_lightmapUv);
    vec3 staticLighting = bakedSourceLighting(bakedSun, bakedSky);
    // Material sheen and emissive join the linear expression before its one display encode.
    // Only the directional term receives the baked sun visibility; local sheen and emissive
    // remain independent of that source. Wetness darkens the linear albedo.
    vec4 materialMask = sampleMaterialMask(texcoord);
    vec4 litTextureColor = vec4(bakedSurfaceColorWithEmission(textureColor.rgb,
        staticLighting + getFxLighting(v_worldPosition),
        outdoorMaterialFaceResponse(
            v_worldPosition,
            v_worldNormal,
            decodeBakedSource(bakedSun),
            materialMask,
            u_bakedLighting[1].rgb * decodeBakedSource(bakedSky)),
        materialMaskedWetnessAlbedoScale(v_worldNormal, materialMask)), textureColor.a);
#else
    vec3 staticLighting = texture2D(s_texLightmap, v_lightmapUv).rgb * v_color0.rgb;
    textureColor.rgb = mix(textureColor.rgb, u_fogColor.rgb, u_fogDensities.z);
    // Combined imported lightmaps stay in the legacy domain; the material term is added in it.
    vec4 materialMask = sampleMaterialMask(texcoord);
    vec4 litTextureColor = vec4(
        textureColor.rgb * staticLighting * getFxLighting(v_worldPosition)
            * materialMaskedWetnessAlbedoScale(v_worldNormal, materialMask)
            + outdoorMaterialFaceResponse(
                v_worldPosition,
                v_worldNormal,
                vec3_splat(1.0),
                materialMask,
                vec3_splat(0.0)),
        textureColor.a);
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
