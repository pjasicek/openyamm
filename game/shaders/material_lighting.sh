// Shared surface-material sheen math. Constants are artistic tuning values, not a PBR contract.
// Zero specular and zero emissive strength must keep the shaded color bit-for-bit unchanged.
// u_materialShading: x roughness, y specular, z fresnel strength, w emissive strength.
// u_materialEmissiveColor: rgb emissive color in the path's working color domain.
// u_materialSunDirection: xyz unit material sun direction, w directional enable.
// u_materialSunColor: rgb material sun tint * intensity.
// u_materialEnvironment: x global exterior wetness in [0, 1]; the CPU sends zero for indoor,
//   underwater and enclosed scenes so no value can leak across a map switch.
// u_materialWetness: x effective wetness response, y wet roughness, z wet darkening.
uniform vec4 u_materialShading;
uniform vec4 u_materialEmissiveColor;
uniform vec4 u_materialSunDirection;
uniform vec4 u_materialSunColor;
uniform vec4 u_materialEnvironment;
uniform vec4 u_materialWetness;

bool materialSurfaceEnabled(vec3 normal, vec3 viewDirection)
{
    // Zero normals mark excluded geometry; a degenerate view vector cannot produce sheen.
    return dot(normal, normal) > 0.25 && dot(viewDirection, viewDirection) > 0.000001;
}

vec3 materialUnitViewDirection(vec3 viewDirection)
{
    return viewDirection * inversesqrt(dot(viewDirection, viewDirection));
}

float materialWetnessFactor(vec3 normal)
{
    // Match the material response's normal gate so excluded geometry stays dry.
    if (!(dot(normal, normal) > 0.25))
    {
        return 0.0;
    }

    float wetness = clamp(u_materialEnvironment.x * u_materialWetness.x, 0.0, 1.0);
    float upward = smoothstep(0.25, 0.90, max(normal.z, 0.0));
    // Vertical exterior walls can still be partially wet.
    return wetness * mix(0.5, 1.0, upward);
}

float materialWetRoughness(vec3 normal)
{
    return mix(u_materialShading.x, u_materialWetness.y, materialWetnessFactor(normal));
}

// Multiplies the albedo term of the calling path; 1.0 when dry.
float materialWetnessAlbedoScale(vec3 normal)
{
    return 1.0 - materialWetnessFactor(normal) * u_materialWetness.z;
}

// Packed facade mask application. The neutral mask (0, 1, 1, 1) leaves every term
// bit-for-bit unchanged: R mixes roughness toward min(roughness, 0.10), G multiplies the
// wetness response, B multiplies the emissive contribution; A is reserved. Face paths only.
float materialMaskedWetnessFactor(vec3 normal, vec4 materialMask)
{
    return materialWetnessFactor(normal) * materialMask.y;
}

float materialMaskedRoughness(vec3 normal, vec4 materialMask)
{
    float roughness = mix(u_materialShading.x, u_materialWetness.y, materialMaskedWetnessFactor(normal, materialMask));
    return mix(roughness, min(roughness, 0.10), materialMask.x);
}

float materialMaskedWetnessAlbedoScale(vec3 normal, vec4 materialMask)
{
    return 1.0 - materialMaskedWetnessFactor(normal, materialMask) * u_materialWetness.z;
}

vec3 materialMaskedEmissiveResponse(vec4 materialMask)
{
    return u_materialEmissiveColor.rgb * (u_materialShading.w * materialMask.z);
}

vec3 materialSpecularForLight(
    vec3 normal,
    vec3 unitViewDirection,
    vec3 unitLightDirection,
    vec3 lightColor,
    float specular,
    float roughness,
    float fresnelStrength)
{
    vec3 halfDirection = unitLightDirection + unitViewDirection;
    float halfLengthSquared = dot(halfDirection, halfDirection);

    if (halfLengthSquared < 0.000001)
    {
        return vec3_splat(0.0);
    }

    halfDirection *= inversesqrt(halfLengthSquared);
    float normalDotLight = max(dot(normal, unitLightDirection), 0.0);
    float exponent = mix(4.0, 192.0, 1.0 - roughness);
    // Energy-normalized lobe: the peak grows as the surface smooths instead of the response
    // shrinking to a sub-pixel needle. The divisor keeps the default 0.9-roughness response
    // at its established strength, so already-authored matte values do not shift.
    float normalizedPeak = (exponent + 2.0) / 24.0;
    float fresnelBase = 1.0 - clamp(dot(normal, unitViewDirection), 0.0, 1.0);
    float fresnel = fresnelBase * fresnelBase * fresnelBase * fresnelBase * fresnelBase;
    float normalDotHalf = max(dot(normal, halfDirection), 0.0);
    float response = normalDotLight * pow(normalDotHalf, exponent)
        * specular * normalizedPeak * (1.0 + fresnelStrength * fresnel);
    return lightColor * response;
}

// In-shade response: sky light (outdoor baked pages) or ambient (indoor) reflected at
// grazing angles. Smooth, reflective materials keep a visible response where the direct
// lobes miss; rough or zero-specular surfaces keep the established look. The environment
// color reaches the calling path from the same source as its diffuse sky/ambient term, so
// baked shadows and sector ambience carry over unchanged.
vec3 materialEnvironmentSpecular(
    vec3 normal,
    vec3 unitViewDirection,
    vec3 environmentColor,
    float specularStrength,
    float roughness,
    float fresnelStrength)
{
    float fresnelBase = 1.0 - clamp(dot(normal, unitViewDirection), 0.0, 1.0);
    float fresnel = fresnelBase * fresnelBase * fresnelBase * fresnelBase * fresnelBase;
    // Hemispheric: the mirror direction selects sky above the horizon and a dim ground
    // bounce below it, so a flat wall varies vertically (sky over ground) instead of
    // washing uniformly — the directionless constant read as a smudge on oblique walls.
    vec3 mirrorDirection = reflect(-unitViewDirection, normal);
    float skyAmount = smoothstep(-0.2, 0.25, mirrorDirection.z);
    vec3 hemisphericColor = environmentColor * mix(0.3, 1.0, skyAmount);
    // Squared smoothness keeps matte surfaces (plaster, weathered wood) essentially clean
    // while glass and polished stone keep most of the response.
    float smoothness = clamp(1.0 - roughness, 0.0, 1.0);
    return hemisphericColor * (specularStrength * smoothness * smoothness * (0.35 + fresnelStrength * fresnel) * 1.4);
}

vec3 materialDirectionalSunResponse(
    vec3 normal,
    vec3 unitViewDirection,
    vec3 directionalAttenuation,
    float roughness)
{
    if (u_materialSunDirection.w < 0.5)
    {
        return vec3_splat(0.0);
    }

    return materialSpecularForLight(
        normal,
        unitViewDirection,
        u_materialSunDirection.xyz,
        u_materialSunColor.rgb * directionalAttenuation,
        u_materialShading.y,
        roughness,
        u_materialShading.z);
}

vec3 materialEmissiveResponse()
{
    return u_materialEmissiveColor.rgb * u_materialShading.w;
}

#if MATERIAL_OUTDOOR_RESPONSE
// Requires u_cameraPosition and the u_fxLight* uniforms declared by the including shader.
// Uses the first entry of the draw's ranked local light selection, with the exact diffuse
// attenuation, without adding its diffuse contribution again.
vec3 outdoorMaterialFaceResponse(
    vec3 worldPosition,
    vec3 worldNormal,
    vec3 directionalAttenuation,
    vec4 materialMask,
    vec3 environmentColor)
{
    vec3 viewDirection = u_cameraPosition.xyz - worldPosition;

    if (!materialSurfaceEnabled(worldNormal, viewDirection))
    {
        return vec3_splat(0.0);
    }

    // Wetness tightens the sheen lobe; emissive stays independent of wetness.
    // The facade mask splits roughness and emissive within one diffuse texture.
    float roughness = materialMaskedRoughness(worldNormal, materialMask);
    vec3 unitViewDirection = materialUnitViewDirection(viewDirection);
    vec3 response = materialDirectionalSunResponse(
        worldNormal,
        unitViewDirection,
        directionalAttenuation,
        roughness);
    response += materialEnvironmentSpecular(
        worldNormal,
        unitViewDirection,
        environmentColor,
        u_materialShading.y,
        roughness,
        u_materialShading.z);

    if (u_materialShading.y > 0.0 && u_fxLightParams.x > 0.0)
    {
        vec3 toLight = u_fxLightPositions[0].xyz - worldPosition;
        float toLightLengthSquared = dot(toLight, toLight);

        if (toLightLengthSquared > 0.000001)
        {
            float radius = max(u_fxLightPositions[0].w, 1.0);
            float attenuation = 1.0 - clamp(toLightLengthSquared / (radius * radius), 0.0, 1.0);
            attenuation *= attenuation;
            vec3 lightColor = u_fxLightColors[0].rgb * (u_fxLightColors[0].w * attenuation * u_fxLightParams.z);
            response += materialSpecularForLight(
                worldNormal,
                unitViewDirection,
                toLight * inversesqrt(toLightLengthSquared),
                lightColor,
                u_materialShading.y,
                roughness,
                u_materialShading.z);
        }
    }

    return response + materialMaskedEmissiveResponse(materialMask);
}
#endif

#if MATERIAL_INDOOR_RESPONSE
// Requires u_cameraPosition and the u_indoorLight* uniforms declared by the including shader.
// Indoor directional material light is always zero; sheen follows the draw's first selected
// live light with the exact diffuse attenuation, plus emissive. Indoor wetness is always zero
// (the CPU binds a zero material environment), so the wetness helpers resolve to dry values.
vec3 indoorMaterialFaceResponse(vec3 worldPosition, vec3 worldNormal, vec4 materialMask)
{
    vec3 viewDirection = u_cameraPosition.xyz - worldPosition;

    if (!materialSurfaceEnabled(worldNormal, viewDirection))
    {
        return vec3_splat(0.0);
    }

    float roughness = materialMaskedRoughness(worldNormal, materialMask);
    vec3 unitViewDirection = materialUnitViewDirection(viewDirection);
    // Sector ambient light carries a grazing specular response so polished indoor
    // surfaces read in shade; it shares the diffuse ambient term exactly.
    vec3 response = materialEnvironmentSpecular(
        worldNormal,
        unitViewDirection,
        u_indoorLightParams.yzw,
        u_materialShading.y,
        roughness,
        u_materialShading.z);

    if (u_materialShading.y > 0.0 && u_indoorLightParams.x > 0.0)
    {
        vec3 toLight = u_indoorLightPositions[0].xyz - worldPosition;
        float toLightLengthSquared = dot(toLight, toLight);

        if (toLightLengthSquared > 0.000001)
        {
            float radius = max(u_indoorLightPositions[0].w, 1.0);
            float attenuation = 1.0 - clamp(toLightLengthSquared / (radius * radius), 0.0, 1.0);
            attenuation *= attenuation;
            vec3 lightColor = u_indoorLightColors[0].rgb * u_indoorLightColors[0].w * attenuation;
            response += materialSpecularForLight(
                worldNormal,
                unitViewDirection,
                toLight * inversesqrt(toLightLengthSquared),
                lightColor,
                u_materialShading.y,
                roughness,
                u_materialShading.z);
        }
    }

    return response + materialMaskedEmissiveResponse(materialMask);
}
#endif
