$input v_texcoord0, v_worldPosition, v_normal, v_depth

#include "common.sh"

SAMPLER2D(s_texColor, 0);

uniform vec4 u_animatedModelLightParams;
uniform vec4 u_fogColor;
uniform vec4 u_fogDensities;
uniform vec4 u_fogDistances;

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
    return
        u_fogDensities.x
        + (u_fogDensities.y - u_fogDensities.x) * safeSmoothstep(u_fogDistances.x, u_fogDistances.y, dist)
        + (1.0 - u_fogDensities.y) * safeSmoothstep(u_fogDistances.y, u_fogDistances.z, dist);
}

float getFogAlpha(float dist)
{
    return 1.0 - safeSmoothstep(u_fogDistances.y, u_fogDistances.z, dist);
}

void main()
{
    vec4 textureColor = texture2D(s_texColor, v_texcoord0);
    if (textureColor.a <= 0.001)
    {
        discard;
    }

    vec3 normal = normalize(v_normal);
    vec3 lightDirection = normalize(vec3(-0.35, -0.45, 0.82));
    float diffuse = max(dot(normal, lightDirection), 0.0);
    vec3 lighting = vec3(u_animatedModelLightParams.x, u_animatedModelLightParams.y, u_animatedModelLightParams.z)
        + diffuse * u_animatedModelLightParams.w;
    vec4 litColor = vec4(
        textureColor.rgb * clamp(lighting, vec3(0.0, 0.0, 0.0), vec3(2.0, 2.0, 2.0)),
        textureColor.a);
    litColor.rgb = mix(litColor.rgb, u_fogColor.rgb, u_fogDensities.z);

    float fogRatio = getFogRatio(v_depth);
    float fogAlpha = getFogAlpha(v_depth);
    vec4 fogColor = vec4(u_fogColor.rgb, fogAlpha);
    gl_FragColor = mix(litColor, fogColor, fogRatio);
}
