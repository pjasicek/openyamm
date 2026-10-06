SAMPLER2D(s_sunShadowNear, 6);
SAMPLER2D(s_sunShadowFar, 7);
uniform mat4 u_sunShadowMatrices[2];
uniform vec4 u_sunShadowParams[4];

float sunShadowDepth(vec3 encoded)
{
    return dot(encoded, vec3(1.0, 1.0 / 255.0, 1.0 / 65025.0));
}

bool sunShadowCovered(vec3 projected)
{
    float border = u_sunShadowParams[0].y * 2.0;
    return projected.x > border && projected.x < 1.0 - border
        && projected.y > border && projected.y < 1.0 - border && projected.z > 0.0 && projected.z < 1.0;
}

float sunShadowFiltered(vec3 projected, bool nearCascade)
{
    if (u_sunShadowParams[2].z > 0.5)
    {
        vec3 encoded = nearCascade ? texture2D(s_sunShadowNear, projected.xy).rgb
                                   : texture2D(s_sunShadowFar, projected.xy).rgb;
        return step(projected.z - u_sunShadowParams[0].z, sunShadowDepth(encoded));
    }
    float visibility = 0.0;
    for (int y = -1; y <= 1; ++y)
    {
        for (int x = -1; x <= 1; ++x)
        {
            vec2 uv = projected.xy + vec2(float(x), float(y)) * u_sunShadowParams[0].y;
            vec3 encoded = nearCascade ? texture2D(s_sunShadowNear, uv).rgb : texture2D(s_sunShadowFar, uv).rgb;
            visibility += step(projected.z - u_sunShadowParams[0].z, sunShadowDepth(encoded));
        }
    }
    return visibility / 9.0;
}

float sunShadowVisibility(vec3 position, vec3 normal)
{
    if (u_sunShadowParams[0].x < 0.5)
    {
        return 1.0;
    }
    float distance = length(position - u_sunShadowParams[1].xyz);
    if (distance >= u_sunShadowParams[1].w)
    {
        return 1.0;
    }
    float grazing = 1.0 - abs(dot(normal, u_sunShadowParams[3].xyz));
    vec3 nearPosition = position + normal * (u_sunShadowParams[0].w + u_sunShadowParams[2].x * grazing);
    vec3 farPosition = position + normal * (u_sunShadowParams[0].w + u_sunShadowParams[2].y * grazing);
    vec3 nearProjected = mul(u_sunShadowMatrices[0], vec4(nearPosition, 1.0)).xyz;
    vec3 farProjected = mul(u_sunShadowMatrices[1], vec4(farPosition, 1.0)).xyz;
    float farVisibility = sunShadowCovered(farProjected) ? sunShadowFiltered(farProjected, false) : 1.0;
    float visibility = farVisibility;
    if (sunShadowCovered(nearProjected))
    {
        float edge = max(abs(nearProjected.x - 0.5), abs(nearProjected.y - 0.5)) * 2.0;
        float blend = smoothstep(0.80, 0.96, edge);
        visibility = mix(sunShadowFiltered(nearProjected, true), farVisibility, blend);
    }
    return mix(visibility, 1.0, smoothstep(u_sunShadowParams[1].w * 0.85, u_sunShadowParams[1].w, distance));
}
