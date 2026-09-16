uniform vec4 u_outdoorSunlight;

float outdoorSunlight(vec3 normal)
{
    // Zero normals identify overlays and other geometry without surface lighting.
    float enabled = step(0.5, dot(normal, normal));
    float facing = clamp(dot(normal, u_outdoorSunlight.xyz), 0.0, 1.0);
    // Cap only the base illumination; point lights are added later. Excluded worlds carry neutral ambient=1.
    float base = min(u_outdoorSunlight.w + facing, max(0.85, u_outdoorSunlight.w));
    return mix(1.0, base, enabled);
}
