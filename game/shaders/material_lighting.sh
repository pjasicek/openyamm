// Shared surface-material sheen math. Constants are artistic tuning values, not a PBR contract.
// Zero specular and zero emissive strength must keep the shaded color bit-for-bit unchanged.
// u_materialShading: x roughness, y specular, z fresnel strength, w emissive strength.
// u_materialEmissiveColor: rgb emissive color in the path's working color domain.
// u_materialSunDirection: xyz unit material sun direction, w directional enable.
// u_materialSunColor: rgb material sun tint * intensity.
uniform vec4 u_materialShading;
uniform vec4 u_materialEmissiveColor;
uniform vec4 u_materialSunDirection;
uniform vec4 u_materialSunColor;

bool materialSurfaceEnabled(vec3 normal, vec3 viewDirection)
{
    // Zero normals mark excluded geometry; a degenerate view vector cannot produce sheen.
    return dot(normal, normal) > 0.25 && dot(viewDirection, viewDirection) > 0.000001;
}

vec3 materialUnitViewDirection(vec3 viewDirection)
{
    return viewDirection * inversesqrt(dot(viewDirection, viewDirection));
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
    float fresnelBase = 1.0 - clamp(dot(normal, unitViewDirection), 0.0, 1.0);
    float fresnel = fresnelBase * fresnelBase * fresnelBase * fresnelBase * fresnelBase;
    float normalDotHalf = max(dot(normal, halfDirection), 0.0);
    float response = normalDotLight * pow(normalDotHalf, exponent)
        * specular * (1.0 + fresnelStrength * fresnel);
    return lightColor * response;
}

vec3 materialDirectionalSunResponse(
    vec3 normal,
    vec3 unitViewDirection,
    vec3 directionalAttenuation)
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
        u_materialShading.x,
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
    vec3 directionalAttenuation)
{
    vec3 viewDirection = u_cameraPosition.xyz - worldPosition;

    if (!materialSurfaceEnabled(worldNormal, viewDirection))
    {
        return vec3_splat(0.0);
    }

    vec3 unitViewDirection = materialUnitViewDirection(viewDirection);
    vec3 response = materialDirectionalSunResponse(
        worldNormal,
        unitViewDirection,
        directionalAttenuation);

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
                u_materialShading.x,
                u_materialShading.z);
        }
    }

    return response + materialEmissiveResponse();
}
#endif

#if MATERIAL_INDOOR_RESPONSE
// Requires u_cameraPosition and the u_indoorLight* uniforms declared by the including shader.
// Indoor directional material light is always zero; sheen follows the draw's first selected
// live light with the exact diffuse attenuation, plus emissive.
vec3 indoorMaterialFaceResponse(vec3 worldPosition, vec3 worldNormal)
{
    vec3 viewDirection = u_cameraPosition.xyz - worldPosition;

    if (!materialSurfaceEnabled(worldNormal, viewDirection))
    {
        return vec3_splat(0.0);
    }

    vec3 unitViewDirection = materialUnitViewDirection(viewDirection);
    vec3 response = vec3_splat(0.0);

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
                u_materialShading.x,
                u_materialShading.z);
        }
    }

    return response + materialEmissiveResponse();
}
#endif
