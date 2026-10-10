// Rain-wet terrain and buildings. u_wetness.x is 0 (dry) to 1 (soaked); the shading normal comes from screen
// derivatives, so any outdoor surface shader can use it. Needs u_cameraPosition and u_fogColor.
uniform vec4 u_wetness;

vec3 applyWetness(vec3 color, vec3 worldPosition)
{
    if (u_wetness.x <= 0.0)
    {
        return color;
    }

    vec3 normal = cross(dFdx(worldPosition), dFdy(worldPosition));
    normal *= inversesqrt(max(dot(normal, normal), 0.000001));
    float up = abs(normal.z);
    // Water fills the pores and darkens the surface; walls shed water and stay drier than the ground.
    float wet = u_wetness.x * mix(0.4, 1.0, up);
    color *= 1.0 - 0.3 * wet;
    // Level wet surfaces mirror a little of the sky at grazing angles.
    vec3 toCamera = normalize(u_cameraPosition.xyz - worldPosition);
    float grazing = 1.0 - clamp(abs(dot(normal, toCamera)), 0.0, 1.0);
    float grazing2 = grazing * grazing;
    float sheen = wet * up * up * grazing2 * grazing2 * 0.35;
    return mix(color, u_fogColor.rgb, sheen);
}
