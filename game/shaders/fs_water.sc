$input v_worldPosition, v_worldNormal, v_texcoord0, v_texcoord1, v_color0

#include "common.sh"

#include "water_surface.sh"
#include "world_clip.sh"
SAMPLER2DARRAY(s_texWaterCoverage, 3);
SAMPLER2D(s_waterSprite, 0);

// Time in seconds, reflection present, render-target Y orientation, rain intensity.
uniform vec4 u_waterSunDirection; // xyz: sun direction, w: unwrapped directional-flow time.
uniform vec4 u_waterSunColor;
uniform vec4 u_waterSkyColor;
uniform vec4 u_fogColor;
uniform vec4 u_fogDensities;
uniform vec4 u_fogDistances;

float safeSmoothstep(float start, float end, float value)
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
    float coverage = 1.0;
    if (v_texcoord1.y > 0.5)
    {
        coverage = texture2DArray(s_texWaterCoverage, vec3(v_texcoord0, v_texcoord1.x)).r;
        if (coverage <= 0.001)
        {
            discard;
        }
    }
    // World coordinates keep waves continuous across native terrain cell boundaries.
    vec3 baseNormal = normalize(v_worldNormal);
    vec3 tangent = abs(baseNormal.z) > 0.99 ? vec3(1.0, 0.0, 0.0)
        : normalize(cross(vec3(0.0, 0.0, 1.0), baseNormal));
    vec3 bitangent = cross(baseNormal, tangent);
    bool flowingFace = v_texcoord1.x < 0.0;
    bool flowingSprite = v_texcoord1.x < -1.5;
    vec2 uv = flowingFace
        ? vec2(dot(v_worldPosition, tangent), dot(v_worldPosition, bitangent)) / (flowingSprite ? 96.0 : 768.0)
            + (flowingSprite ? vec2(0.0, 0.8) : v_texcoord0) * u_waterSunDirection.w
        : v_worldPosition.xy / 2048.0;
    float falling = flowingFace && (flowingSprite || dot(v_texcoord0, v_texcoord0) > 0.000001)
        ? 1.0 - abs(baseNormal.z) : 0.0;
    if (falling > 0.01)
    {
        // Stretch turbulence along gravity into flowing strands rather than pool-like round wavelets.
        uv *= vec2(4.0, 0.5);
    }
    vec3 normal = waterWaveNormal(uv, baseNormal, tangent, bitangent,
        (flowingFace ? 0.95 : 0.35) + u_waterParams.w * 0.15);
#if WATER_MOVEMENT_RIPPLES
    float movementSheen;
    normal = waterMovementNormal(v_worldPosition, normal, normalize(v_worldNormal), movementSheen);
#endif
    vec3 viewDirection = normalize(u_cameraPosition.xyz - v_worldPosition);
    if (dot(normal, viewDirection) < 0.0)
    {
        normal = -normal;
    }
    float fresnel = waterFresnel(normal, viewDirection);
    vec3 reflected = waterReflection(v_worldPosition, normal.xy * 0.014, u_waterSkyColor.rgb);

    // The material tint retains native colour without its repeating animated pattern.
    // Ambient light still dims the water body at night; waves come from the normal map.
    vec3 waterColor = v_color0.rgb * u_waterSkyColor.w;
    vec3 color = mix(waterColor, reflected, fresnel);
    if (falling > 0.01)
    {
        color = mix(color, vec3(0.85, 0.92, 1.0) * u_waterSkyColor.w, waterFlowFoam(uv, falling));
    }
    vec3 halfDirection = u_waterSunDirection.xyz + viewDirection;
    float halfLength = dot(halfDirection, halfDirection);
    if (halfLength > 0.0001)
    {
        halfDirection *= inversesqrt(halfLength);
        float highlight = pow(max(dot(normal, halfDirection), 0.0), 96.0);
        highlight *= max(dot(normal, u_waterSunDirection.xyz), 0.0);
        color += u_waterSunColor.rgb * highlight;
    }

#if WATER_MOVEMENT_RIPPLES
    color += vec3(0.85, 0.92, 1.0) * movementSheen * max(u_waterSkyColor.w, 0.2);
#endif
    color = mix(color, u_fogColor.rgb, u_fogDensities.z);
    float distanceToCamera = length(v_worldPosition - u_cameraPosition.xyz);
    float fogRatio;
    float alpha = 1.0;
    if (u_fogDensities.w > 0.5)
    {
        fogRatio = clamp((distanceToCamera - u_fogDistances.x)
            / max(u_fogDistances.y - u_fogDistances.x, 1.0), 0.0, 1.0);
    }
    else
    {
        fogRatio = u_fogDensities.x
            + (u_fogDensities.y - u_fogDensities.x)
                * safeSmoothstep(u_fogDistances.x, u_fogDistances.y, distanceToCamera)
            + (1.0 - u_fogDensities.y)
                * safeSmoothstep(u_fogDistances.y, u_fogDistances.z, distanceToCamera);
        alpha = 1.0 - safeSmoothstep(u_fogDistances.y, u_fogDistances.z, distanceToCamera);
    }
    gl_FragColor = mix(vec4(color, 1.0), vec4(u_fogColor.rgb, alpha), fogRatio);
    gl_FragColor.a *= coverage;
    if (flowingSprite)
    {
        gl_FragColor.a *= texture2D(s_waterSprite, v_texcoord0).a * v_color0.a;
    }
}
