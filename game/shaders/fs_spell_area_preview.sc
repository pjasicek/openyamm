$input v_texcoord0, v_depth, v_worldPosition

#include "common.sh"

uniform vec4 u_fogColor;
uniform vec4 u_fogDensities;
uniform vec4 u_fogDistances;
uniform vec4 u_spellAreaParams0;
uniform vec4 u_spellAreaParams1;
uniform vec4 u_spellAreaColorA;
uniform vec4 u_spellAreaColorB;

float safeSmoothstep(float edge0, float edge1, float value)
{
    if (edge0 == edge1)
    {
        return value < edge0 ? 0.0 : 1.0;
    }

    float t = clamp((value - edge0) / (edge1 - edge0), 0.0, 1.0);
    return t * t * (3.0 - 2.0 * t);
}

float bandMask(float radius, float center, float halfWidth)
{
    float inner = safeSmoothstep(center - halfWidth, center, radius);
    float outer = 1.0 - safeSmoothstep(center, center + halfWidth, radius);
    return inner * outer;
}

float crispBandMask(float radius, float center, float halfWidth, float feather)
{
    float inner = safeSmoothstep(center - halfWidth - feather, center - halfWidth, radius);
    float outer = 1.0 - safeSmoothstep(center + halfWidth, center + halfWidth + feather, radius);
    return inner * outer;
}

float sectorMask(float angle01, float center01, float halfWidth01)
{
    float delta = abs(fract(angle01 - center01 + 0.5) - 0.5);
    return 1.0 - safeSmoothstep(halfWidth01, halfWidth01 + 0.02, delta);
}

float lineRepeatMask(float angle01, float repeatCount, float halfWidth)
{
    float repeated = fract(angle01 * repeatCount);
    float distanceToLine = abs(repeated - 0.5);
    return 1.0 - safeSmoothstep(halfWidth, halfWidth + 0.015, distanceToLine);
}

float crispLineRepeatMask(float angle01, float repeatCount, float halfWidth, float feather)
{
    float repeated = fract(angle01 * repeatCount);
    float distanceToLine = abs(repeated - 0.5);
    return 1.0 - safeSmoothstep(halfWidth, halfWidth + feather, distanceToLine);
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
    const float Pi = 3.14159265358979323846;

    vec2 centeredUv = v_texcoord0 * 2.0 - 1.0;
    float radius = length(centeredUv);

    if (radius > 1.02)
    {
        discard;
    }

    float angle01 = fract(atan2(centeredUv.y, centeredUv.x) / (2.0 * Pi) + 1.0);
    float time = u_spellAreaParams0.x;
    float pulse = 0.5 + 0.5 * sin(time * u_spellAreaParams0.y);
    float slowPulse = 0.5 + 0.5 * sin(time * u_spellAreaParams1.x);

    float outerRing = crispBandMask(radius, 0.92, 0.0165, 0.0035);
    float midRing = crispBandMask(radius, 0.70 + pulse * 0.018, 0.00975, 0.0025);
    float innerRing = crispBandMask(radius, 0.44, 0.0075, 0.0020);
    float centerRing = crispBandMask(radius, 0.18 + slowPulse * 0.012, 0.00675, 0.0020);
    float centerDisk = 1.0 - safeSmoothstep(0.03, 0.11, radius);
    float groundOverlay =
        1.0 - safeSmoothstep(0.93, 0.99, radius);

    float majorTicks = crispLineRepeatMask(angle01, 8.0, 0.0195, 0.0065) * crispBandMask(radius, 0.92, 0.054, 0.008);
    float minorTicks =
        crispLineRepeatMask(angle01 + 0.0625, 16.0, 0.0105, 0.0045) * crispBandMask(radius, 0.70, 0.0285, 0.006);
    float spokes = crispLineRepeatMask(angle01, 4.0, 0.0105, 0.0045) * (1.0 - safeSmoothstep(0.12, 0.78, radius));

    float rotatingArcA =
        sectorMask(angle01, fract(time * u_spellAreaParams1.y), 0.075) * crispBandMask(radius, 0.83, 0.0255, 0.006);
    float rotatingArcB =
        sectorMask(angle01, fract(-time * u_spellAreaParams1.z + 0.33), 0.060) * crispBandMask(radius, 0.58, 0.01875, 0.0045);
    float rotatingArcC =
        sectorMask(angle01, fract(time * (u_spellAreaParams1.y * 0.65) + 0.66), 0.050) * crispBandMask(radius, 0.30, 0.0135, 0.00375);

    float diamond =
        1.0
        - safeSmoothstep(0.06, 0.12, abs(centeredUv.x) + abs(centeredUv.y));
    float crossA = 1.0 - safeSmoothstep(0.010, 0.028, abs(centeredUv.x));
    float crossB = 1.0 - safeSmoothstep(0.010, 0.028, abs(centeredUv.y));
    float centerGlyph = max(diamond * (1.0 - safeSmoothstep(0.16, 0.24, radius)), max(crossA, crossB) * centerDisk);

    float outerGlow = crispBandMask(radius, 0.92, 0.038, 0.016);
    float innerGlow = crispBandMask(radius, 0.52, 0.048, 0.020);

    float baseMask = outerRing + midRing + innerRing + centerRing + majorTicks * 0.85 + minorTicks * 0.55;
    float accentMask = rotatingArcA + rotatingArcB + rotatingArcC + centerGlyph + spokes * 0.35 + centerDisk * 0.45;
    float glowMask = outerGlow * (0.22 + 0.12 * pulse) + innerGlow * (0.14 + 0.10 * slowPulse);

    vec3 overlayColor = mix(u_spellAreaColorA.rgb, u_spellAreaColorB.rgb, 0.18) * groundOverlay * 0.60;
    vec3 baseColor = u_spellAreaColorA.rgb * baseMask;
    vec3 accentColor = u_spellAreaColorB.rgb * accentMask;
    vec3 glowColor = mix(u_spellAreaColorA.rgb, u_spellAreaColorB.rgb, 0.45) * glowMask;
    vec3 color = overlayColor + baseColor + accentColor + glowColor;

    float alpha =
        clamp(
            groundOverlay * 0.40
            + baseMask * 0.42
            + accentMask * 0.78
            + glowMask * 0.18,
            0.0,
            u_spellAreaParams0.z);

    float fogRatio = getFogRatio(v_depth);
    float fogAlpha = getFogAlpha(v_depth);
    vec4 fogColor = vec4(u_fogColor.rgb, fogAlpha);
    vec4 markerColor = vec4(color, alpha);
    gl_FragColor = mix(markerColor, fogColor, fogRatio);
}
