// RGBM4 stores linear incident diffuse lighting, independently of receiver albedo.
SAMPLER2D(s_texBakedSky, 3);
uniform vec4 u_bakedLighting[2];

vec3 decodeBakedSource(vec4 source)
{
    return source.rgb * (source.a * 4.0);
}

vec3 bakedSourceLighting(vec4 sun, vec4 sky)
{
    return decodeBakedSource(sun) * u_bakedLighting[0].rgb
        + decodeBakedSource(sky) * u_bakedLighting[1].rgb;
}

vec3 bakedSurfaceColor(vec3 color, vec3 lighting)
{
    // Native bitmap textures and the existing output are display encoded.
    return pow(
        max(pow(max(color, vec3_splat(0.0)), vec3_splat(2.2)) * lighting, vec3_splat(0.0)),
        vec3_splat(1.0 / 2.2));
}

vec3 bakedSurfaceColorWithEmission(vec3 color, vec3 lighting, vec3 addedLinear)
{
    // Material specular and emissive join the linear expression before its one display encode;
    // a zero addedLinear term keeps the encoded result unchanged.
    return pow(
        max(pow(max(color, vec3_splat(0.0)), vec3_splat(2.2)) * lighting + addedLinear, vec3_splat(0.0)),
        vec3_splat(1.0 / 2.2));
}
