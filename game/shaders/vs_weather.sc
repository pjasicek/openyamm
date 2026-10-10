$input a_position, a_texcoord0, a_color0
$output v_texcoord0, v_texcoord1, v_color0

// Rain streaks, snow flakes (WEATHER_SNOW), the distant rain curtain (WEATHER_CURTAIN) and ground splashes
// (WEATHER_SPLASH), positioned entirely here.
// Drops and flakes carry a fixed random seed (a_position, a_color0) and wrap through a box that moves with the
// camera, so the volume always surrounds the party without any CPU simulation.

#include "common.sh"
#include "sky_common.sh"

// [0] box centre xyz, time in seconds (wrapped)
// [1] box size xyz, near fade distance; the curtain uses x/y as its bottom and top relative to the centre, splashes
//     x as their spawn radius
// [2] wrapped fall offset xyz, base size; the curtain uses y scroll phase, z columns, w repeats
// [3] velocity relative to the camera xyz, streak seconds; the curtain uses xy as wind over fall speed
// [4] lit colour rgb, alpha
// [5] sway amplitude, sway rate, curtain radius, world size of one pixel at unit view distance
// Snow uses the base size as the flake radius; rain as the streak half-width.
uniform vec4 u_weather[6];
uniform vec4 u_fogColor;
uniform vec4 u_fogDensities;
uniform vec4 u_fogDistances;

float weatherSmoothstep(float edge0, float edge1, float value)
{
    if (edge0 == edge1)
    {
        return 0.0;
    }

    float t = clamp((value - edge0) / (edge1 - edge0), 0.0, 1.0);
    return t * t * (3.0 - 2.0 * t);
}

float weatherFogRatio(float distance)
{
    if (u_fogDensities.w > 0.5)
    {
        return clamp((distance - u_fogDistances.x) / max(u_fogDistances.y - u_fogDistances.x, 1.0), 0.0, 1.0);
    }

    return u_fogDensities.x
        + (u_fogDensities.y - u_fogDensities.x) * weatherSmoothstep(u_fogDistances.x, u_fogDistances.y, distance)
        + (1.0 - u_fogDensities.y) * weatherSmoothstep(u_fogDistances.y, u_fogDistances.z, distance);
}

// Rain and snow fade into the fog with distance like the world behind them.
vec4 weatherFoggedColor(vec3 worldPosition, float alpha)
{
    float distance = length(worldPosition - skyCameraPosition());
    float fogRatio = skyFogRatio(weatherFogRatio(distance), worldPosition, distance, u_fogDistances.z);
    vec3 fogColor = skyFogDisplayColor(fogRatio, u_fogColor.rgb, worldPosition);
    return vec4(mix(u_weather[4].rgb, fogColor, fogRatio), alpha * (1.0 - 0.7 * fogRatio));
}

void main()
{
    vec3 centre = u_weather[0].xyz;
    vec4 random = a_color0;
    v_texcoord1 = vec4(0.0, 0.0, 0.0, 0.0);

#if WEATHER_CURTAIN
    vec3 world = vec3(centre.xy + a_position.xy * u_weather[5].z,
        centre.z + mix(u_weather[1].x, u_weather[1].y, a_position.z));
    gl_Position = mul(u_viewProj, vec4(world, 1.0));
    // Streaks lean with the wind blowing along the curtain at this angle ([3].xy is wind over fall speed).
    float angle = a_texcoord0.x * 6.2831853;
    float lean = dot(u_weather[3].xy, vec2(-sin(angle), cos(angle)))
        * (u_weather[1].y - u_weather[1].x) / (6.2831853 * u_weather[5].z);
    v_texcoord0 = vec2(a_texcoord0.x + a_position.z * lean, a_texcoord0.y);
    // Thin out toward the curtain's top and bottom so it never shows an edge.
    float edge = weatherSmoothstep(0.0, 0.25, a_position.z) * (1.0 - weatherSmoothstep(0.6, 1.0, a_position.z));
    v_color0 = weatherFoggedColor(world, u_weather[4].w * edge);
#elif WEATHER_SPLASH
    // a_position is the splash point; corners span x -1..1 and y 0..1 above it. Age and variation arrive in
    // the colour bytes.
    vec3 viewCentre = mul(u_view, vec4(a_position, 1.0)).xyz;
    float size = u_weather[2].w * (0.7 + 0.6 * random.y);
    gl_Position = mul(u_proj, vec4(viewCentre + vec3(a_texcoord0.x * size, a_texcoord0.y * size, 0.0), 1.0));
    v_texcoord0 = a_texcoord0;
    v_texcoord1 = vec4(random.x, random.y, 0.0, 0.0);
    // Splashes thin out toward their spawn radius ([1].x) instead of ending in a visible ring.
    float splashDistance = length(a_position.xy - skyCameraPosition().xy);
    v_color0 = weatherFoggedColor(a_position,
        u_weather[4].w * (1.0 - weatherSmoothstep(0.3 * u_weather[1].x, u_weather[1].x, splashDistance)));
#else
    vec3 box = u_weather[1].xyz;
    vec3 local = mod(a_position * box + u_weather[2].xyz - centre, box) - 0.5 * box;
    vec3 world = centre + local;
    vec3 edge = abs(local) / (0.5 * box);
    // A long horizontal fade lets the near and far rain boxes overlap without a visible edge.
    float fade = (1.0 - weatherSmoothstep(0.5, 1.0, max(edge.x, edge.y)))
        * (1.0 - weatherSmoothstep(0.75, 1.0, edge.z));

#if WEATHER_SNOW
    // Flakes sway on their way down.
    float phase = random.y * 6.2831853;
    float swayTime = u_weather[0].w * u_weather[5].y * (0.6 + 0.8 * random.x) + phase;
    world.xy += vec2(sin(swayTime), cos(swayTime * 0.77)) * u_weather[5].x * (0.4 + random.z);
#endif

    // Each drop or flake is drawn along its motion over the streak time: long thin streaks for rain, flakes leaning
    // slightly into the wind for snow.
    vec3 tail = world - u_weather[3].xyz * u_weather[3].w * (0.8 + 0.4 * random.y);
    vec3 viewHead = mul(u_view, vec4(world, 1.0)).xyz;
    vec3 viewTail = mul(u_view, vec4(tail, 1.0)).xyz;
    vec3 axis = viewHead - viewTail;
    float axisLength = length(axis);
    vec3 direction = axisLength > 0.0001 ? axis / axisLength : vec3(0.0, 1.0, 0.0);
    vec3 middle = 0.5 * (viewHead + viewTail);
    vec3 side = cross(direction, middle);
    float sideLength = length(side);
    side = sideLength > 0.0001 ? side / sideLength : vec3(1.0, 0.0, 0.0);
    float distance = length(middle);
    float physicalWidth = u_weather[2].w * (0.7 + 0.6 * random.x);
    // Never thinner than a pixel; thinner drops fade instead, keeping their brightness.
    float width = max(physicalWidth, distance * u_weather[5].w);
    fade *= min(1.0, physicalWidth / width);
#if WEATHER_SNOW
    // Flakes stay flakes: wind and camera motion lean them at most about one flake width, never into streaks.
    float stretch = min(axisLength, width * 0.8);
    viewTail = viewHead - direction * stretch;
    // The quad extends one width past both ends; the fragment shader draws a soft, rotated six-lobed flake.
    viewTail -= direction * width;
    viewHead += direction * width;
    v_texcoord1 = vec4(stretch / width, random.z * 6.2831853, 0.0, 0.0);
#endif
    vec3 viewPosition = mix(viewTail, viewHead, a_texcoord0.x) + side * (a_texcoord0.y * width);
    gl_Position = mul(u_proj, vec4(viewPosition, 1.0));

    // Nothing pops up right in front of the lens.
    fade *= weatherSmoothstep(u_weather[1].w * 0.4, u_weather[1].w, distance);
    v_texcoord0 = a_texcoord0;
    v_color0 = weatherFoggedColor(world, u_weather[4].w * fade * (0.55 + 0.45 * random.w));
#endif
}
