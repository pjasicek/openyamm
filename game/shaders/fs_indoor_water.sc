$input v_worldPosition, v_worldNormal, v_texcoord0, v_texcoord1, v_color0

#include "common.sh"
#include "water_surface.sh"
#include "world_clip.sh"

uniform vec4 u_indoorLightPositions[12];
uniform vec4 u_indoorLightColors[12];
uniform vec4 u_indoorLightParams;

void main()
{
    clipWorldPosition(v_worldPosition);
    vec3 baseNormal = normalize(v_worldNormal);
    // Project waves onto the face itself, including vertical flowing water.
    vec3 tangent = abs(baseNormal.z) > 0.99 ? vec3(1.0, 0.0, 0.0)
        : normalize(cross(vec3(0.0, 0.0, 1.0), baseNormal));
    vec3 bitangent = cross(baseNormal, tangent);
    vec2 uv = vec2(dot(v_worldPosition, tangent), dot(v_worldPosition, bitangent)) / 768.0;
    uv += v_texcoord0 * u_waterParams.x;
    float falling = dot(v_texcoord0, v_texcoord0) > 0.000001 ? 1.0 - abs(baseNormal.z) : 0.0;
    if (falling > 0.01)
    {
        uv *= vec2(4.0, 0.5);
    }
    else if (abs(baseNormal.z) < 0.99)
    {
        uv *= 3.0;
    }
    vec3 normal = waterWaveNormal(uv, baseNormal, tangent, bitangent, 0.95);
#if WATER_MOVEMENT_RIPPLES
    float movementSheen;
    normal = waterMovementNormal(v_worldPosition, normal, baseNormal, movementSheen);
#endif
    float waveScatter = clamp(length(normal - baseNormal) * 4.0, 0.0, 1.0);
    vec3 viewDirection = normalize(u_cameraPosition.xyz - v_worldPosition);
    if (dot(normal, viewDirection) < 0.0)
    {
        normal = -normal;
    }
    vec3 lighting = u_indoorLightParams.yzw;
    vec3 highlights = vec3_splat(0.0);
    for (int i = 0; i < 12; ++i)
    {
        if (float(i) >= u_indoorLightParams.x)
        {
            break;
        }
        vec3 toLight = u_indoorLightPositions[i].xyz - v_worldPosition;
        float distanceSquared = max(dot(toLight, toLight), 0.0001);
        float radius = max(u_indoorLightPositions[i].w, 1.0);
        float attenuation = 1.0 - clamp(distanceSquared / (radius * radius), 0.0, 1.0);
        attenuation *= attenuation;
        vec3 radiance = u_indoorLightColors[i].rgb * (u_indoorLightColors[i].w * attenuation);
        vec3 lightDirection = toLight * inversesqrt(distanceSquared);
        float incidence = max(dot(normal, lightDirection), 0.0);
        // Retain soft scattered light while allowing ripples to break up broad light patches.
        lighting += radiance * (0.35 + 0.65 * incidence);
        vec3 halfDirection = lightDirection + viewDirection;
        float halfLength = dot(halfDirection, halfDirection);
        if (halfLength > 0.0001)
        {
            float highlight = pow(max(dot(normal, halfDirection * inversesqrt(halfLength)), 0.0), 96.0);
            highlights += radiance * highlight * incidence;
        }
    }
    vec3 tint = v_color0.rgb;
    if (u_waterParams.y < 0.5)
    {
        // Waves still scatter room light on walls and pools without a planar reflection.
        tint = mix(tint, vec3(0.35, 0.55, 0.65), waveScatter);
    }
    vec3 illumination = clamp(lighting, vec3_splat(0.0), vec3_splat(2.0));
    vec3 waterColor = tint * illumination;
    // A dungeon has no daylight sky response; unreflected pools retain their room illumination.
    // Stronger pond ripples still fit the existing reflection guard band and scissor budget.
    vec2 distortion = clamp(normal.xy * 0.05, vec2_splat(-0.014), vec2_splat(0.014));
    vec3 reflected = waterReflection(v_worldPosition, distortion, waterColor);
    vec3 color = mix(waterColor, reflected, waterFresnel(normal, viewDirection)) + highlights;
    if (falling > 0.01)
    {
        color = mix(color, vec3(0.85, 0.92, 1.0) * illumination, waterFlowFoam(uv, falling));
    }
#if WATER_MOVEMENT_RIPPLES
    color += vec3(0.85, 0.92, 1.0) * movementSheen;
#endif
    gl_FragColor = vec4(color, 1.0);
}
