$input v_worldPosition, v_worldNormal, v_texcoord0, v_texcoord1, v_color0

// A silvered mirror (liquids.yml kind: mirror; Xeen's travel mirrors): the planar reflection about the face's own
// plane, tinted by the liquid's colour and a little darker, with a slow, faint magical sheen. No waves, no flow.
// MIRROR_INDOOR: the indoor variant (room light, scene fog with INDOOR_FOG); otherwise the outdoor sky light and fog.

#include "common.sh"
#if !MIRROR_INDOOR || INDOOR_FOG
#include "sky_common.sh"
#endif
#include "water_surface.sh"
#include "world_clip.sh"

#if MIRROR_INDOOR
uniform vec4 u_indoorLightParams;
#if INDOOR_FOG
uniform vec4 u_fogColor;
uniform vec4 u_fogDistances;
#endif
#else
uniform vec4 u_waterSkyColor;
uniform vec4 u_fogColor;
uniform vec4 u_fogDensities;
uniform vec4 u_fogDistances;
#endif

// WaterRenderer.cpp's MirrorReflectionDistance: no capture beyond it, so the reflection fades out before it.
#define MIRROR_FADE_START 3072.0
#define MIRROR_FADE_END 4000.0

float mirrorStep(float start, float end, float value)
{
    if (start == end)
    {
        return 0.0;
    }
    float t = clamp((value - start) / (end - start), 0.0, 1.0);
    return t * t * (3.0 - 2.0 * t);
}

void main()
{
    clipWorldPosition(v_worldPosition);
    vec3 normal = normalize(v_worldNormal);
    vec3 toCamera = u_cameraPosition.xyz - v_worldPosition;
    // One-sided: seen from behind it is not drawn (a portal's membrane has a face for each side, each its own mirror).
    if (dot(normal, toCamera) <= 0.0)
    {
        discard;
    }
    float distanceToCamera = length(toCamera);
    vec3 tangent = abs(normal.z) > 0.99 ? vec3(1.0, 0.0, 0.0) : normalize(cross(vec3(0.0, 0.0, 1.0), normal));
    vec3 bitangent = cross(normal, tangent);
    vec2 faceXy = vec2(dot(v_worldPosition, tangent), dot(v_worldPosition, bitangent));
    float time = u_waterParams.x;

#if MIRROR_INDOOR
    float light = clamp(max(max(u_indoorLightParams.y, u_indoorLightParams.z), u_indoorLightParams.w), 0.2, 1.0);
#else
    float light = clamp(u_waterSkyColor.w, 0.2, 1.0);
#endif
    // Without a capture (far, or reflections off): dull silver, lit by the place.
    vec3 silver = v_color0.rgb * 0.42 * light;

    // The magic: the glass swims very slowly and faintly (the wave normals, drifting, at a fraction of a pixel's sway).
    vec2 swim = texture2D(s_waterNormal, faceXy / 900.0 + vec2(time * 0.004, -time * 0.003)).rg * 2.0 - 1.0;
    vec3 reflected = waterReflection(v_worldPosition, swim * 0.0025, silver);
    reflected = mix(reflected, silver, mirrorStep(MIRROR_FADE_START, MIRROR_FADE_END, distanceToCamera));
    // Silvered glass: the reflected scene tinted by the liquid's colour and a little darker.
    vec3 color = reflected * v_color0.rgb * 0.86;

    // A faint band of pale blue light drifts across the glass, and a few soft glimmers come and go.
    float band = dot(faceXy, vec2(0.0026, 0.0017)) - time * 0.045;
    float sheen = pow(0.5 + 0.5 * sin(band * 6.2831853), 24.0) * 0.07;
    vec2 glint = texture2D(s_waterNormal, faceXy / 300.0 + vec2(-time * 0.009, time * 0.006)).rg * 2.0 - 1.0;
    float glimmer = smoothstep(0.55, 0.9, length(glint)) * (0.5 + 0.5 * sin(time * 0.7 + faceXy.x * 0.01)) * 0.05;
    // The edge of the glass catches more light at a glancing view.
    float grazing = 1.0 - clamp(dot(normal, toCamera / max(distanceToCamera, 0.001)), 0.0, 1.0);
    color += vec3(0.62, 0.74, 1.0) * ((sheen + glimmer) * light + grazing * grazing * grazing * 0.08 * light);

#if MIRROR_INDOOR
#if INDOOR_FOG
    color = mix(color, u_fogColor.rgb, clamp((distanceToCamera - u_fogDistances.x)
        / max(u_fogDistances.y - u_fogDistances.x, 1.0), 0.0, 1.0));
    color = mistApply(color, v_worldPosition);
#endif
    gl_FragColor = vec4(color, 1.0);
#else
    // The outdoor fog, as on the water (fs_water.sc).
    color = mix(color, u_fogColor.rgb, u_fogDensities.z);
    float fogRatio;
    float alpha = 1.0;
    if (u_fogDensities.w > 0.5)
    {
        fogRatio = clamp((distanceToCamera - u_fogDistances.x) / max(u_fogDistances.y - u_fogDistances.x, 1.0),
            0.0, 1.0);
    }
    else
    {
        fogRatio = u_fogDensities.x
            + (u_fogDensities.y - u_fogDensities.x) * mirrorStep(u_fogDistances.x, u_fogDistances.y, distanceToCamera)
            + (1.0 - u_fogDensities.y) * mirrorStep(u_fogDistances.y, u_fogDistances.z, distanceToCamera);
        alpha = 1.0 - mirrorStep(u_fogDistances.y, u_fogDistances.z, distanceToCamera);
    }
    fogRatio = skyWaterFogRatio(fogRatio, v_worldPosition, distanceToCamera, u_fogDistances.z);
    vec3 fogColor = skyFogDisplayColor(fogRatio, u_fogColor.rgb, v_worldPosition);
    gl_FragColor = mix(vec4(color, 1.0), vec4(fogColor, alpha), fogRatio);
    gl_FragColor.rgb = mistApply(gl_FragColor.rgb, v_worldPosition);
#endif
}
