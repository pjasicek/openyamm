$input v_worldPosition, v_worldNormal, v_texcoord0, v_texcoord1, v_color0

#include "common.sh"
#include "sky_common.sh"

#include "water_surface.sh"
#include "liquid_surface.sh"
#include "world_clip.sh"
SAMPLER2DARRAY(s_texWaterCoverage, 3);
SAMPLER2D(s_waterSprite, 0);
// Rendered terrain heights under shore water (shoreline 2 vertices).
SAMPLER2D(s_waterSeabed, 4);
// World-to-texture mapping of the seabed heights: west x, north y, scale, offset. Zero scale: no seabed.
uniform vec4 u_waterSeabed;
// x: depth over the seabed at which the water turns opaque (only shallower seabed is drawn).
uniform vec4 u_waterSeabedDepth;

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
    if (v_texcoord1.y > 0.5 && v_texcoord1.y < 1.5)
    {
        coverage = texture2DArray(s_texWaterCoverage, vec3(v_texcoord0, v_texcoord1.x)).r;
        if (coverage <= 0.001)
        {
            discard;
        }
    }
    bool lava = v_texcoord1.z > 1.5;
    bool tar = !lava && v_texcoord1.z > 0.5;
    if (lava || tar)
    {
        // Opaque liquids end in a crisp, anti-aliased line along the edge art instead of a translucent staircase of
        // its 128-texel mask.
        float edge = max(fwidth(coverage), 0.02);
        coverage = smoothstep(0.5 - edge, 0.5 + edge, coverage);
    }
    // Shore water: its depth over the rendered seabed decides how see-through it is and where the surf foams.
    bool shoreWater = !lava && !tar && v_texcoord1.y > 1.5 && u_waterSeabed.z > 0.0;
    float depth = 1000.0;
    if (shoreWater)
    {
        vec2 seabedUv = vec2(v_worldPosition.x - u_waterSeabed.x, u_waterSeabed.y - v_worldPosition.y)
            * u_waterSeabed.z + u_waterSeabed.w;
        depth = v_worldPosition.z - texture2D(s_waterSeabed, seabedUv).r;
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
    vec3 color;
    float shallowAlpha = 1.0;
    if (lava)
    {
        // A flowing face's flow (water uv units per second) carries the lava.
        vec2 lavaUv = (flowingFace
            ? vec2(dot(v_worldPosition, tangent), dot(v_worldPosition, bitangent)) : v_worldPosition.xy) / 1200.0;
        vec2 flowOffset = flowingFace ? v_texcoord0 * (0.64 * u_waterSunDirection.w) : vec2_splat(0.0);
        if (falling > 0.01)
        {
            lavaUv *= vec2(1.5, 0.5);
        }
        float heat = lavaHeat(lavaUv, flowOffset, v_worldPosition.xy, !flowingFace, u_waterParams.x);
        if (v_texcoord1.y > 0.5 && v_texcoord1.y < 1.5)
        {
            // An edge tile: lava runs hotter beside the land.
            float spread = 0.035;
            float land = 1.0 - min(
                min(texture2DArray(s_texWaterCoverage, vec3(v_texcoord0 + vec2(spread, 0.0), v_texcoord1.x)).r,
                    texture2DArray(s_texWaterCoverage, vec3(v_texcoord0 - vec2(spread, 0.0), v_texcoord1.x)).r),
                min(texture2DArray(s_texWaterCoverage, vec3(v_texcoord0 + vec2(0.0, spread), v_texcoord1.x)).r,
                    texture2DArray(s_texWaterCoverage, vec3(v_texcoord0 - vec2(0.0, spread), v_texcoord1.x)).r));
            heat = max(heat, land * 0.85);
        }
        color = lavaColor(heat, v_color0.rgb);
    }
    else
    {
        if (falling > 0.01)
        {
            // Stretch turbulence along gravity into flowing strands rather than pool-like round wavelets.
            uv *= vec2(4.0, 0.5);
        }
        // Tar heaves in broad, slow, low swells.
        if (tar && !flowingFace)
        {
            uv *= 0.5;
        }
        // Rain roughens the waves and, on still water near the camera, rings where drops land.
        vec3 normal = waterWaveNormal(uv, baseNormal, tangent, bitangent,
            (tar ? 0.26 : flowingFace ? 0.95 : 0.35) + u_waterParams.w * (tar ? 0.3 : 0.6));
        float bubbleSkin = 0.0;
        float tarGloss = 1.0;
        if (tar && !flowingFace)
        {
            vec3 bubble = tarBubble(v_worldPosition.xy, u_waterParams.x);
            normal = normalize(normal - (tangent * bubble.x + bitangent * bubble.y));
            bubbleSkin = bubble.z;
            // Dull, dusty patches break up the gloss; a bubble's stretched skin is clean and glossy.
            tarGloss = mix(smoothstep(0.25, 0.65, texture2D(s_liquidPattern, v_worldPosition.xy / 3000.0).g)
                * 0.55 + 0.45, 1.0, bubbleSkin);
        }
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
        if (tar)
        {
            // Glossy tar reflects a little more of the sky head-on than water does.
            fresnel = (0.07 + 0.93 * fresnel) * tarGloss;
        }
        vec3 reflected = waterReflection(v_worldPosition, normal.xy * 0.014, u_waterSkyColor.rgb);

        // The material tint retains native colour without its repeating animated pattern.
        // Ambient light still dims the water body at night; waves come from the normal map.
        vec3 waterColor = v_color0.rgb * u_waterSkyColor.w;
        color = mix(waterColor, reflected, fresnel);
        if (falling > 0.01 && !tar)
        {
            color = mix(color, vec3(0.85, 0.92, 1.0) * u_waterSkyColor.w, waterFlowFoam(uv, falling));
        }
        vec3 halfDirection = u_waterSunDirection.xyz + viewDirection;
        float halfLength = dot(halfDirection, halfDirection);
        if (halfLength > 0.0001)
        {
            halfDirection *= inversesqrt(halfLength);
            // Tar's glossy skin gives a tighter, brighter glint.
            float highlight = tar ? pow(max(dot(normal, halfDirection), 0.0), 220.0) * 1.4 * tarGloss
                : pow(max(dot(normal, halfDirection), 0.0), 96.0);
            highlight *= max(dot(normal, u_waterSunDirection.xyz), 0.0);
            color += u_waterSunColor.rgb * highlight;
        }

#if WATER_MOVEMENT_RIPPLES
        color += vec3(0.85, 0.92, 1.0) * movementSheen * max(u_waterSkyColor.w, 0.2);
#endif
        if (shoreWater)
        {
            float time = u_waterParams.x;
            // Swash: the foam band creeps up the beach and back.
            float swash = 0.5 + 0.5 * sin(time * 0.9 + dot(v_worldPosition.xy, vec2(0.0021, 0.0013)));
            // Low wave lines roll in from the deeper water toward the shore.
            float travel = fract(time * 0.12 + dot(v_worldPosition.xy, vec2(0.00031, 0.00023)));
            float opaqueDepth = u_waterSeabedDepth.x;
            float waveDepth = (1.0 - travel) * opaqueDepth;
            // Lacy foam: two drifting samples of the wave normals break bands into bubbles and gaps.
            float lace = texture2D(s_waterNormal, v_worldPosition.xy / 190.0 + vec2(time * 0.017, time * 0.009)).r
                * texture2D(s_waterNormal, v_worldPosition.xy / 113.0 - vec2(time * 0.011, time * 0.014)).g;
            lace = smoothstep(0.18, 0.42, lace);
            float bandCentre = 3.0 + swash * 10.0;
            float edgeFoam = (1.0 - smoothstep(0.0, 5.0, abs(depth - bandCentre))) * lace;
            float waveFoam = (1.0 - smoothstep(0.0, 5.0, abs(depth - waveDepth))) * travel * 0.6 * lace;
            float foam = clamp(edgeFoam + waveFoam, 0.0, 1.0);
            // See-through shallows: the seabed shows near the shore and fades out over deeper water; the surface
            // still reflects at grazing angles.
            float body = smoothstep(0.0, opaqueDepth, depth);
            shallowAlpha = max(mix(0.08, 1.0, body), fresnel);
            color = mix(color, color * vec3(0.85, 1.05, 1.0), 1.0 - body);
            color = mix(color, vec3(0.95, 0.97, 1.0) * max(u_waterSkyColor.w, 0.35), foam * 0.8);
            shallowAlpha = max(shallowAlpha, foam * 0.75);
            // The water thins to nothing at the waterline instead of ending in a hard line.
            shallowAlpha *= smoothstep(0.0, 4.0, depth);
        }
    }
    // Lava's own light cuts through half of the constant haze; distance fog still applies.
    color = mix(color, u_fogColor.rgb, u_fogDensities.z * (lava ? 0.5 : 1.0));
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
    gl_FragColor.rgb = mistApply(gl_FragColor.rgb, v_worldPosition);
    gl_FragColor.a *= coverage * shallowAlpha;
    if (flowingSprite)
    {
        gl_FragColor.a *= texture2D(s_waterSprite, v_texcoord0).a * v_color0.a;
    }
}
