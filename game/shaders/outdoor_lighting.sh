// Fog and point-light lighting of outdoor surfaces, shared by fragment shaders and the grass vertex shader
// (terrain decorations light per vertex). BAKED_SOURCES: baked sunlight comes from the lightmap, not the base term;
// SUN_SHADOWS (fragment only): the base sunlight is shadowed by the mesh sun shadow maps.
uniform vec4 u_fogColor;
uniform vec4 u_fogDensities;
uniform vec4 u_fogDistances;
uniform vec4 u_fxLightPositions[8];
uniform vec4 u_fxLightColors[8];
uniform vec4 u_fxLightParams;

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
#if SUN_SHADOWS
    float direct = max(sunlight - u_outdoorSunlight.w, 0.0);
    if (u_sunShadowParams[0].x > 0.5 && direct > 0.0)
    {
        vec3 normal = cross(dFdx(worldPosition), dFdy(worldPosition));
        normal *= inversesqrt(max(dot(normal, normal), 0.000001));
        if (dot(normal, u_sunShadowParams[3].xyz) < 0.0)
        {
            normal = -normal;
        }
        sunlight -= direct * (1.0 - sunShadowVisibility(worldPosition, normal));
    }
#endif
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
