// RGBM4 stores linear incident diffuse lighting, independently of receiver albedo.
SAMPLER2D(s_texBakedSky, 3);
uniform vec4 u_bakedLighting;

vec3 bakedSourceLighting(vec4 sun, vec4 sky)
{
    return sun.rgb * (sun.a * 4.0 * u_bakedLighting.x)
        + sky.rgb * (sky.a * 4.0 * u_bakedLighting.y);
}

vec3 bakedSurfaceColor(vec3 color, vec3 lighting)
{
    // Native bitmap textures and the existing output are display encoded.
    return pow(max(pow(max(color, vec3(0.0)), vec3(2.2)) * lighting, vec3(0.0)), vec3(1.0 / 2.2));
}
