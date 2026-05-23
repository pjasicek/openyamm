$input v_texcoord0

#include "common.sh"

uniform vec4 u_beamParams;
uniform vec4 u_beamCoreColor;
uniform vec4 u_beamGlowColor;

float safeSmoothstep(float edge0, float edge1, float value)
{
    if (edge0 == edge1)
    {
        return value < edge0 ? 0.0 : 1.0;
    }

    float t = clamp((value - edge0) / (edge1 - edge0), 0.0, 1.0);
    return t * t * (3.0 - 2.0 * t);
}

void main()
{
    float time = u_beamParams.x;
    float intensity = u_beamParams.y;
    float beamLength = max(1.0, u_beamParams.z);
    float along = v_texcoord0.x;
    float across = abs(v_texcoord0.y * 2.0 - 1.0);
    float flow = along * beamLength / 128.0;

    float noiseA = sin(flow * 2.21 - time * 8.7) * 0.055;
    float noiseB = sin(flow * 5.37 + time * 4.9) * 0.030;
    float edgeNoise = noiseA + noiseB;
    float noisyAcross = across + edgeNoise * (0.25 + across * 0.75);

    float core = 1.0 - safeSmoothstep(0.06, 0.23, noisyAcross);
    float innerGlow = 1.0 - safeSmoothstep(0.18, 0.58, noisyAcross);
    float outerGlow = 1.0 - safeSmoothstep(0.46, 1.02, across);
    float filament =
        (0.5 + 0.5 * sin(flow * 8.6 - time * 16.0))
        * (1.0 - safeSmoothstep(0.18, 0.62, across));
    float impactPulse = 0.72 + 0.28 * sin(time * 18.0);
    float impactDistance =
        sqrt((1.0 - along) * (1.0 - along) * 18.0 + across * across * 1.05);
    float impactGlow = (1.0 - safeSmoothstep(0.10, 1.18, impactDistance)) * impactPulse;
    float impactCore = (1.0 - safeSmoothstep(0.02, 0.42, impactDistance)) * impactPulse;
    float endFade =
        safeSmoothstep(0.0, 0.045, along)
        * (1.0 - safeSmoothstep(0.94, 1.0, along));

    float alpha =
        clamp(
            (core * 0.95 + innerGlow * 0.42 + outerGlow * 0.24 + filament * 0.18)
            * endFade
            * intensity
            + (impactGlow * 0.58 + impactCore * 0.95) * intensity,
            0.0,
            1.0);

    if (alpha <= 0.004)
    {
        discard;
    }

    vec3 color =
        u_beamCoreColor.rgb * (core * 1.35 + filament * 0.55)
        + u_beamGlowColor.rgb * (innerGlow * 0.72 + outerGlow * 0.42)
        + u_beamCoreColor.rgb * impactCore * 1.35
        + u_beamGlowColor.rgb * impactGlow * 0.95;
    color *= alpha;
    gl_FragColor = vec4(color, alpha);
}
