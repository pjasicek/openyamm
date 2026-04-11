$input v_texcoord0, v_depth

#include "common.sh"

SAMPLER2D(s_texColor, 0);

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
    float fogRatio = getFogRatio(v_depth);
    float fogAlpha = getFogAlpha(v_depth);
    vec4 fogColor = vec4(u_fogColor.rgb, fogAlpha);
    gl_FragColor = mix(textureColor, fogColor, fogRatio);
}
