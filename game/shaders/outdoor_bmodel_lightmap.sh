
#include "common.sh"
#include "sky_common.sh"
#include "world_clip.sh"

#if BMODEL_TEXTURE_ARRAY
// Static materials of one texture size share an array; the layer arrives per vertex (v_texcoord1.y).
SAMPLER2DARRAY(s_texColor, 0);
#else
SAMPLER2D(s_texColor, 0);
#endif
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

#include "weather_wetness.sh"
#include "light_grid.sh"
#if SURFACE_MATERIALS
#include "surface_material.sh"
#if !SUN_SHADOWS
SAMPLER2D(s_texBakedSunDirect, 5);
#endif
// xyz = direction toward the baked sun.
uniform vec4 u_surfaceSun;
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

vec3 getFxLighting(vec3 worldPosition)
{
#if BAKED_SOURCES
    vec3 lighting = vec3_splat(0.0);
#else
    vec3 lighting = vec3(u_fxLightParams.y, u_fxLightParams.y, u_fxLightParams.y);
#endif

    // Dynamic lights from the view's light grid (scaled like the list below), else the draw's own list (water
    // reflections); the active lights come first: stop at the count.
    if (lightGridMode() > 0.5)
    {
        lighting += lightGridDynamicLighting(worldPosition);
    }
    for (int i = 0; i < 8; ++i)
    {
        if (float(i) >= u_fxLightParams.x || lightGridMode() > 0.5)
        {
            break;
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

#if SURFACE_MATERIALS
// The sky seen in a reflection: the sky's gradient (or a flat sky with the Classic sky), dim ground below the
// horizon, scaled to the sky light the bake says reaches the point (radiance), so recesses reflect less.
vec3 surfaceSkyRadiance(vec3 direction, vec3 radiance, float roughness)
{
    float ground = direction.z >= 0.0 ? 1.0 : 0.3;
    if (u_skyFog[1].w <= 0.0)
    {
        return radiance * ground;
    }
    vec3 average = mix(u_skyFog[0].rgb, u_skyFog[1].rgb, 0.6);
    float averageLuminance = max(dot(average, vec3(0.2126, 0.7152, 0.0722)), 0.0001);
    vec3 sky = direction.z >= 0.0 ? skyGradientLinear(direction) : u_skyFog[1].rgb * ground;
    sky = mix(sky, average * ground, roughness);
    return sky * (dot(radiance, vec3(0.2126, 0.7152, 0.0722)) / averageLuminance);
}

// A face with material maps under the bake: the bake's light for the flat face relit for the detailed normal (as the
// terrain does), occlusion, the highlights of the sun and point lights, the sky's reflection and glow. Linear result.
// It takes the varyings from main: Metal and HLSL see them only there.
vec3 surfaceBakedColor(vec3 displayColor, SurfacePoint material, vec3 faceNormal, vec3 toCamera, float distance,
    vec3 worldPosition, vec2 lightmapUv)
{
    vec3 albedo = pow(max(displayColor, vec3_splat(0.0)), vec3_splat(2.2));
    vec3 normal = material.normal;
    float roughness = material.roughness;
    float upward = clamp(faceNormal.z, 0.0, 1.0);
    if (u_wetness.x > 0.0)
    {
        // Rain darkens and smooths the surface (walls shed water); on level faces the recesses fill with water
        // first, so mortar joints and worn hollows hold puddles.
        float wet = u_wetness.x * mix(0.4, 1.0, upward);
        albedo *= 1.0 - 0.3 * wet;
        roughness = mix(roughness, min(roughness, 0.2), wet * 0.7);
        float waterDepth = mix(0.35, 0.02, u_wetness.x);
        float puddle = smoothstep(0.9, 0.97, upward)
            * smoothstep(waterDepth, waterDepth + 0.03, 1.0 - material.height);
        albedo *= 1.0 - 0.3 * puddle;
        roughness = mix(roughness, 0.03, puddle);
        normal = normalize(mix(normal, faceNormal, puddle));
    }
    vec3 view = toCamera / max(distance, 0.001);
    vec3 f0 = mix(vec3_splat(0.04), albedo, material.metal);
    vec3 diffuseAlbedo = albedo * (1.0 - SURFACE_METAL_DIFFUSE_LOSS * material.metal);

    vec4 sunSample = texture2D(s_texLightmap, lightmapUv);
    vec4 skySample = texture2D(s_texBakedSky, lightmapUv);
    vec4 directSample = texture2D(s_texBakedSunDirect, lightmapUv);
    vec3 totalSun = sunSample.rgb * (sunSample.a * 4.0);
    vec3 directSun = min(directSample.rgb * (directSample.a * 4.0), totalSun);
    float visibility = 1.0;
#if SUN_SHADOWS
    if (u_sunShadowParams[0].x > 0.5)
    {
        vec3 shadowNormal = dot(faceNormal, u_sunShadowParams[3].xyz) < 0.0 ? -faceNormal : faceNormal;
        visibility = sunShadowVisibility(worldPosition, shadowNormal, 1.0);
    }
#endif
    vec3 toSun = normalize(u_surfaceSun.xyz);
    float relight = surfaceRelight(normal, faceNormal, toSun);
    // Sky light comes mostly from above: relief tilted up takes more of it, tilted down less.
    float skyFacing = (0.55 + 0.45 * normal.z) / (0.55 + 0.45 * faceNormal.z);
    vec3 sky = skySample.rgb * (skySample.a * 4.0) * u_bakedLighting[1].rgb;
    vec3 irradiance = ((totalSun - directSun) * material.occlusion + directSun * relight * visibility)
        * u_bakedLighting[0].rgb + sky * material.occlusion * skyFacing;

    vec3 pointDiffuse = vec3_splat(0.0);
    vec3 pointSpecular = vec3_splat(0.0);
    if (lightGridMode() > 0.5)
    {
        SurfacePoint lit = material;
        lit.normal = normal;
        lit.roughness = roughness;
        surfacePointLights(worldPosition, lit, faceNormal, view, f0, vec2(-1.0, -1.0), false, pointDiffuse,
            pointSpecular);
    }
    else
    {
        pointDiffuse = getFxLighting(worldPosition);
    }

    vec3 color = diffuseAlbedo * min(irradiance + pointDiffuse, vec3_splat(4.0));
    // The bake's direct sun on the flat face, as the sun's strength at normal incidence (its shadows kept).
    vec3 sunStrength = directSun * visibility / max(dot(faceNormal, toSun), 0.15) * u_bakedLighting[0].rgb;
    vec3 specular = (sunStrength * surfaceSpecular(normal, view, toSun, roughness, f0) + pointSpecular)
        * (SURFACE_PI * u_surfaceMaterial.z * material.occlusion);
    float nv = max(dot(normal, view), 0.001);
    vec3 reflected = reflect(-view, normal);
    // Creases keep the sky out of their reflection, rougher surfaces more so.
    float specularOcclusion = clamp(
        pow(nv + material.occlusion, exp2(-16.0 * roughness - 1.0)) - 1.0 + material.occlusion, 0.0, 1.0);
    // Only smooth and metal surfaces show the sky: the painted colours already hold rough surfaces' faint sheen.
    float reflection = max(material.metal, 1.0 - smoothstep(0.3, 0.7, roughness));
    vec3 environment = surfaceTracedReflection(surfaceSkyRadiance(reflected, sky / (0.55 + 0.45 * faceNormal.z),
        roughness), worldPosition, reflected, faceNormal, roughness, reflection);
    specular += environment * surfaceEnvironmentResponse(f0, roughness, nv)
        * (specularOcclusion * reflection * u_surfaceMaterial.w);
    return color + specular + surfaceGlowColor(albedo) * (material.glow * SURFACE_GLOW_SCALE);
}
#endif

void main()
{
    clipWorldPosition(v_worldPosition);
    vec2 texcoord = v_texcoord0;
    texcoord.xy += v_flowInfo.xy * u_secretPulseParams.y;

    if (v_flowInfo.z > 0.5)
    {
        float lavaPhase = sin(mod(u_secretPulseParams.y, 8.0) * 6.2831853 / 8.0);
        texcoord.y += lavaPhase;
    }

#if SURFACE_MATERIALS
    vec3 toCamera = u_cameraPosition.xyz - v_worldPosition;
    float cameraDistance = length(toCamera);
    vec3 faceNormal = surfaceFlatNormal(v_worldPosition, toCamera);
    vec3 gradientU = v_gradientU;
    vec3 gradientV = v_gradientV;
#if BMODEL_TEXTURE_ARRAY
    // The texture's layer in the group's material arrays; negative: the texture has no maps.
    float materialLayer = v_texcoord1.z;
    bool hasMaterial = materialLayer > -0.5;
#else
    float materialLayer = 0.0;
    bool hasMaterial = true;
#endif
    texcoord = surfaceParallax(texcoord, materialLayer, hasMaterial ? 1.0 : 0.0, toCamera, cameraDistance,
        faceNormal, gradientU, gradientV);
    SurfacePoint material = surfacePoint(surfaceMap(s_surfaceNormal, texcoord, materialLayer),
        surfaceMap(s_surfaceDetail, texcoord, materialLayer), faceNormal, gradientU, gradientV,
        u_surfaceMaterial.y);
#endif

#if BMODEL_TEXTURE_ARRAY
    vec4 textureColor = texture2DArray(s_texColor, vec3(texcoord, v_texcoord1.y));
#else
    vec4 textureColor = texture2D(s_texColor, texcoord);
#endif
    if (textureColor.a <= 0.1)
    {
        discard;
    }

#if BAKED_SOURCES
    textureColor.rgb = mix(textureColor.rgb, u_fogColor.rgb, u_fogDensities.z);
    vec4 litTextureColor;
#if SURFACE_MATERIALS
    if (hasMaterial)
    {
        litTextureColor = vec4(pow(max(surfaceBakedColor(textureColor.rgb, material, faceNormal, toCamera,
            cameraDistance, v_worldPosition, v_lightmapUv), vec3_splat(0.0)), vec3_splat(1.0 / 2.2)), textureColor.a);
    }
    else
#endif
    {
        vec3 staticLighting = bakedShadowedSourceLighting(texture2D(s_texLightmap, v_lightmapUv),
            texture2D(s_texBakedSky, v_lightmapUv), v_lightmapUv, v_worldPosition);
        litTextureColor = vec4(bakedSurfaceColor(textureColor.rgb,
            staticLighting + getFxLighting(v_worldPosition)), textureColor.a);
        litTextureColor.rgb = applyWetness(litTextureColor.rgb, v_worldPosition);
    }
#else
    vec3 staticLighting = texture2D(s_texLightmap, v_lightmapUv).rgb * v_color0.rgb;
    textureColor.rgb = mix(textureColor.rgb, u_fogColor.rgb, u_fogDensities.z);
    vec4 litTextureColor = vec4(
        textureColor.rgb * staticLighting * getFxLighting(v_worldPosition),
        textureColor.a);
    litTextureColor.rgb = applyWetness(litTextureColor.rgb, v_worldPosition);
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
    float fogRatio = skyFogRatio(getFogRatio(fogDistance), v_worldPosition, fogDistance, u_fogDistances.z);
    float fogAlpha = getFogAlpha(fogDistance);
    vec4 fogColor = vec4(skyFogDisplayColor(fogRatio, u_fogColor.rgb, v_worldPosition), fogAlpha);
    gl_FragColor = mix(litTextureColor, fogColor, fogRatio);
    gl_FragColor.rgb = mistApply(gl_FragColor.rgb, v_worldPosition);
}
