$input v_worldPosition, v_worldNormal, v_texcoord0, v_texcoord1, v_color0

#include "common.sh"
#include "sky_common.sh"

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
// x: rain ring amount (0 = none), y: ring layers (0-2).
uniform vec4 u_waterRain;

float rainHash(vec2 position)
{
    vec3 hash = fract(vec3(position.xyx) * 0.1031);
    hash += dot(hash, hash.yzx + 33.33);
    return fract((hash.x + hash.y) * hash.z);
}

// Raindrop rings: each grid cell may hold one drop per cycle, landing at a random spot and spreading as a ring.
// Returns the surface slope; heavier rain fills more cells.
vec2 rainRingSlope(vec2 worldPosition, float time, float amount, float layers)
{
    vec2 slope = vec2_splat(0.0);

    for (int layer = 0; layer < 2; ++layer)
    {
        if (float(layer) < layers)
        {
            vec2 grid = worldPosition / 90.0 + float(layer) * vec2(0.37, 0.71);
            vec2 cell = floor(grid);
            float seed = rainHash(cell + float(layer) * 19.7);
            float cycle = time * 1.15 + seed * 7.0;
            float age = fract(cycle);
            vec2 drop = cell + floor(cycle) * vec2(1.37, 2.11);

            if (rainHash(drop + 0.5) < amount)
            {
                vec2 offset = fract(grid) - (vec2(rainHash(drop + 3.1), rainHash(drop + 5.7)) * 0.5 + 0.25);
                float distance = length(offset);
                float profile = (distance - age * 0.3) * 28.0;
                float crest = profile * exp(-profile * profile) * (1.0 - age) * (1.0 - age);
                slope += offset / max(distance, 0.001) * crest;
            }
        }
    }

    return slope;
}

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
    // Rain roughens the waves and, on still water near the camera, rings where drops land.
    vec3 normal = waterWaveNormal(uv, baseNormal, tangent, bitangent,
        (flowingFace ? 0.95 : 0.35) + u_waterParams.w * 0.6);
    if (u_waterRain.x > 0.0 && falling <= 0.01)
    {
        float ringFade = 1.0 - safeSmoothstep(1500.0, 3200.0, length(v_worldPosition - u_cameraPosition.xyz));
        if (ringFade > 0.0)
        {
            vec2 slope = rainRingSlope(v_worldPosition.xy, u_waterParams.x, u_waterRain.x, u_waterRain.y);
            normal = normalize(normal - (tangent * slope.x + bitangent * slope.y) * (0.9 * ringFade));
        }
    }
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
    fogRatio = skyWaterFogRatio(fogRatio, v_worldPosition, distanceToCamera, u_fogDistances.z);
    vec3 fogColor = skyFogDisplayColor(fogRatio, u_fogColor.rgb, v_worldPosition);
    gl_FragColor = mix(vec4(color, 1.0), vec4(fogColor, alpha), fogRatio);
    gl_FragColor.a *= coverage;
    if (flowingSprite)
    {
        gl_FragColor.a *= texture2D(s_waterSprite, v_texcoord0).a * v_color0.a;
    }
}
