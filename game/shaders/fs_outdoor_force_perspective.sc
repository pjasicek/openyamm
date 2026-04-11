$input v_color0, v_texcoord1, v_screenspace

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

void main()
{
    vec4 fragmentColor = texture2DProj(s_texColor, v_texcoord1) * v_color0;
    float fogRatio = getFogRatio(v_screenspace);

    if (fragmentColor.a < 0.004)
    {
        fogRatio = 0.0;
    }

    gl_FragColor = mix(fragmentColor, vec4(u_fogColor.rgb, 1.0), fogRatio);
}
