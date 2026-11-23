$input v_texcoord1

#include "common.sh"
#include "sky_common.sh"

SAMPLER2D(s_skyCloud0, 0);
SAMPLER2D(s_skyCloud1, 1);
SAMPLER2D(s_skyCloud2, 2);
SAMPLER2D(s_skyCloud3, 3);
SAMPLER2D(s_skyRing, 4);
SAMPLER2D(s_skyStars, 5);
SAMPLER2D(s_skyMoon, 6);
// The map's void cells (terrain.void): R8, one texel per terrain cell, 1 = void; a blank texture without void.
SAMPLER2D(s_skyVoid, 7);

// Clip position to a world-space view ray: inverse of (translation-free view * projection).
uniform mat4 u_skyRay;
// [0] sun disc colour, cos(sun radius); [1] moon direction, cos(moon radius);
// [2] moon phase, moon visibility, star visibility, star rotation;
// [3] cloud lit colour, below-horizon mode (0 fog, 1 sky, 2 flat); [4] cloud shadow colour, sun disc visibility;
// [5] horizon ring opacity, ring height, star brightness, star density; [6] flat fog colour (display), fog haze;
// [7] celestial pole direction, unused.
uniform vec4 u_skyParams[8];
// Per layer: (scale, coverage, softness, opacity), (offset x, offset y, curvature, colour layer flag).
uniform vec4 u_skyClouds[8];
// The orbit ring (game/render/SkyRenderer.cpp, packSkyOrbitUniform): [0] moon angle, ring height; [1] colour,
// opacity; [2] half width, fragments, light count, light radius (radians); [3] light colour, brightness; [4..11] lights.
// All zero, and skipped, unless a preset has an orbit_ring.
uniform vec4 u_skyOrbit[12];
// The theme's rim glow (packSkyRimUniform): [0] horizon direction of its middle (x, y), half width, height (radians);
// [1] colour times strength, depth below the horizon (radians). Zero colour: none.
uniform vec4 u_skyRim[2];
// The void below the horizon (SkyRenderer::render): x 1 when the map has void, y star brightness there, z the
// camera's height above the void floor. All zero on a map without void.
uniform vec4 u_skyVoid;

#define SKY_PI 3.14159265

float skyHash13(vec3 p)
{
    p = fract(p * 0.1031);
    p += dot(p, p.zyx + 31.32);
    return fract((p.x + p.y) * p.z);
}

vec3 skyHash33(vec3 p)
{
    p = fract(p * vec3(0.1031, 0.1030, 0.0973));
    p += dot(p, p.yxz + 33.33);
    return fract((p.xxy + p.yxx) * p.zyx);
}

vec3 rotateAroundAxis(vec3 v, vec3 axis, float angle)
{
    float c = cos(angle);
    float s = sin(angle);
    return v * c + cross(axis, v) * s + axis * dot(axis, v) * (1.0 - c);
}

vec2 cloudUv(vec4 shape, vec4 motion, vec3 direction)
{
    return direction.xy / (max(direction.z, 0.0) + motion.z) * shape.x + motion.xy;
}

// Composites one density layer. Coverage turns the same density field into scattered, broken or overcast cloud;
// thin edges catch the light, thick cores fall into shadow, and rims toward the sun glow.
vec3 applyCloud(vec3 color, vec4 shape, vec4 motion, vec4 texel, vec3 direction, float cloudFade, float sunScatter)
{
    if (motion.w > 0.5)
    {
        // A painted (original) sky: its own colours under the time-of-day light, hazed toward the horizon.
        vec3 painted = pow(texel.rgb, vec3_splat(2.2)) * u_skyParams[3].rgb;
        painted += vec3(0.6, 0.65, 0.8) * u_skyFog[3].w * 0.8;
        painted = mix(painted, u_skyFog[1].rgb, (1.0 - smoothstep(0.0, 0.3, direction.z)) * 0.55);
        // Fog weather washes the painting toward the hazed horizon, as the original fogged sky did.
        painted = mix(painted, u_skyFog[1].rgb, u_skyParams[6].w * 0.8);
        return mix(color, painted, texel.a * shape.w * cloudFade);
    }

    float threshold = 1.0 - shape.y;
    float cover = smoothstep(threshold, threshold + shape.z, texel.r) * shape.w;
    float lightAmount = clamp(1.0 - texel.g * cover * 0.85, 0.0, 1.0);
    vec3 cloudColor = mix(u_skyParams[4].rgb, u_skyParams[3].rgb, lightAmount);
    cloudColor += u_skyFog[2].rgb * sunScatter * (1.0 - cover) * 1.5;
    cloudColor += vec3(0.6, 0.65, 0.8) * u_skyFog[3].w * 1.2;
    // Far clouds take on the haze of the horizon.
    cloudColor = mix(cloudColor, u_skyFog[1].rgb, (1.0 - smoothstep(0.0, 0.35, direction.z)) * 0.55);
    return mix(color, cloudColor, cover * cloudFade);
}

// bandShare: the weight of the painted band (the milky way) against the point stars; brightness and density: the
// preset's (u_skyParams[5].zw), or the void's own.
vec3 starField(vec3 direction, float bandShare, float brightness, float density)
{
    vec3 pole = u_skyParams[7].xyz;
    vec3 rotated = rotateAroundAxis(direction, pole, u_skyParams[2].w);
    float u = atan2(rotated.y, rotated.x) / (2.0 * SKY_PI) + 0.5;
    float v = acos(clamp(rotated.z, -1.0, 1.0)) / SKY_PI;
    vec3 band = texture2D(s_skyStars, vec2(u, v)).rgb;

    vec3 p = rotated * 160.0;
    vec3 cell = floor(p);
    float pick = skyHash13(cell);
    float star = 0.0;

    if (pick > 1.0 - density * 0.08)
    {
        vec3 center = cell + 0.25 + 0.5 * skyHash33(cell);
        float distanceToStar = length(p - center);
        float size = mix(0.14, 0.3, skyHash13(cell + 17.0));
        star = (1.0 - smoothstep(0.0, size, distanceToStar)) * mix(0.35, 1.0, skyHash13(cell + 5.0));
    }

    vec3 tint = mix(vec3(0.75, 0.82, 1.0), vec3(1.0, 0.9, 0.78), skyHash13(cell + 9.0));
    return (band * bandShare + tint * star * star * 3.0) * brightness;
}

vec3 moonDisc(vec3 direction, out float coverage, out float lit)
{
    vec3 moonDirection = u_skyParams[1].xyz;
    float cosRadius = u_skyParams[1].w;
    coverage = 0.0;
    lit = 0.0;
    float facing = dot(direction, moonDirection);

    if (facing < cosRadius)
    {
        // A faint halo around the disc.
        return vec3_splat(pow(max(facing, 0.0), 600.0) * 0.06);
    }

    vec3 right = normalize(cross(moonDirection, vec3(0.0, 0.0, 1.0)) + vec3(0.0001, 0.0, 0.0));
    vec3 up = cross(right, moonDirection);
    float sinRadius = sqrt(max(1.0 - cosRadius * cosRadius, 0.000001));
    vec2 local = vec2(dot(direction, right), dot(direction, up)) / sinRadius;
    float radial = dot(local, local);
    vec3 normal = vec3(local, sqrt(max(1.0 - radial, 0.0)));
    float phaseAngle = u_skyParams[2].x * 2.0 * SKY_PI;
    vec3 light = vec3(sin(phaseAngle), 0.0, -cos(phaseAngle));
    lit = smoothstep(-0.04, 0.12, dot(normal, light));
    vec4 surface = texture2D(s_skyMoon, local * 0.5 + 0.5);
    coverage = (1.0 - smoothstep(0.85, 1.0, radial)) * surface.a;
    // Where a moon's texture is transparent inside the disc (a broken moon), the halo continues as outside it.
    vec3 halo = vec3_splat(pow(max(facing, 0.0), 600.0) * 0.06) * (1.0 - surface.a);
    return vec3(0.92, 0.94, 1.0) * surface.rgb * lit + halo;
}

float skyNoise1(float x)
{
    float cell = floor(x);
    float t = fract(x);
    return mix(skyHash13(vec3(cell, 7.0, 3.0)), skyHash13(vec3(cell + 1.0, 7.0, 3.0)), t * t * (3.0 - 2.0 * t));
}

// A planetary debris ring along the moon's path: banded across its width, clumped along it, and densest in the
// fragments trailing from the moon.
vec3 orbitRing(vec3 direction)
{
    float across = (asin(clamp(direction.y, -1.0, 1.0)) - asin(u_skyOrbit[0].y)) / u_skyOrbit[2].x;
    float edge = abs(across);

    if (edge >= 1.0)
    {
        return vec3_splat(0.0);
    }

    float along = atan2(direction.z, direction.x);
    float profile = 1.0 - smoothstep(0.35, 1.0, edge);
    // A few soft bands and gaps across the width, as in a planetary ring.
    float bands = 0.7 + 0.3 * sin(across * 9.0 + 2.0 * sin(across * 4.0));
    float clumps = 0.45 + 0.55 * skyNoise1(along * 40.0) * (0.6 + 0.4 * skyNoise1(along * 170.0 + 11.0));
    // Scattered bright specks of debris, about a twelfth of a degree each.
    vec3 grainCell = floor(vec3(along * 700.0, across * u_skyOrbit[2].x * 700.0, 1.0));
    float grain = step(0.965, skyHash13(grainCell)) * 1.5;
    // Signed distance round the ring from the moon: the fragments trail far behind it and barely lead it.
    float fromMoon = mod(along - u_skyOrbit[0].x + SKY_PI, 2.0 * SKY_PI) - SKY_PI;
    float trail = exp(-max(fromMoon, 0.0) * 2.2 - max(-fromMoon, 0.0) * 9.0);
    float density = profile * bands * clumps * (1.0 + u_skyOrbit[2].y * trail) + profile * grain * (0.3 + trail);
    return u_skyOrbit[1].rgb * u_skyOrbit[1].w * density;
}

// Small lights crossing the sky in the ring (orbital platforms): a sharp point with a little glow.
vec3 orbitLights(vec3 direction)
{
    float glow = 0.0;
    float radius = u_skyOrbit[2].w;

    for (int light = 0; light < 8; ++light)
    {
        if (float(light) < u_skyOrbit[2].z)
        {
            // The chord to the light, which equals the angle at these sizes and keeps float precision.
            float distanceToLight = length(direction - u_skyOrbit[4 + light].xyz);
            glow += 1.0 - smoothstep(radius * 0.4, radius, distanceToLight);
            glow += exp(-distanceToLight / (radius * 3.0)) * 0.25;
        }
    }

    return u_skyOrbit[3].rgb * u_skyOrbit[3].w * glow;
}

// A glow along part of the horizon, fixed in world direction: brightest at the horizon in its middle, fading up to
// its height, along to its edges and a little below the horizon (over the void, where nothing covers it).
vec3 rimGlow(vec3 direction)
{
    vec2 level = direction.xy / max(length(direction.xy), 0.0001);
    float along = acos(clamp(dot(level, u_skyRim[0].xy), -1.0, 1.0)) / u_skyRim[0].z;

    if (along >= 1.0)
    {
        return vec3_splat(0.0);
    }

    float elevation = asin(clamp(direction.z, -1.0, 1.0));
    float rise = elevation >= 0.0 ? elevation / u_skyRim[0].w : -elevation / max(u_skyRim[1].w, 0.0001);

    if (rise >= 1.0)
    {
        return vec3_splat(0.0);
    }

    float across = 1.0 - smoothstep(0.0, 1.0, along);
    float upward = 1.0 - smoothstep(0.0, 1.0, rise);
    return u_skyRim[1].rgb * across * upward * upward;
}

// The world's fog colour at the horizon below this direction (fog mode), or the flat fog colour (flat mode).
vec3 belowHorizonFog(vec3 direction, float belowMode)
{
    if (belowMode > 1.5)
    {
        return u_skyParams[6].rgb;
    }

    vec3 horizonDirection = normalize(vec3(direction.xy, 0.0) + vec3(0.0, 0.0, 0.0001));
    vec3 horizon = mix(u_skyParams[6].rgb, skyLinearToDisplay(skyGradientLinear(horizonDirection)), u_skyFog[1].w);
    // Maps ringed by sea continue it past the terrain square to the horizon.
    float sea = skySeaWeight(direction.xy);
    return sea > 0.0 ? mix(horizon, skyDistantSeaDisplay(direction, horizon), sea) : horizon;
}

// How much of the view below the horizon in this direction looks into the void: where the ray meets the void floor
// inside the terrain square, that cell's void mask (filtered, a soft edge); past the square, the mask's border cell
// where the ray leaves it, so the void runs on to the horizon wherever the map's edge is void and stops nowhere else.
// u_skyVoid.w: how much an open sky's fog cover leaves of it (no weather greys it).
float skyVoidWeight(vec3 direction)
{
    if (u_skyVoid.x < 0.5 || direction.z >= 0.0)
    {
        return 0.0;
    }

    float halfSize = u_skyFog[4].x;
    vec2 start = clamp(u_skyFog[6].zw, vec2_splat(-halfSize), vec2_splat(halfSize));
    vec2 hit = u_skyFog[6].zw + direction.xy * (u_skyVoid.z / max(-direction.z, 0.00001));

    if (max(abs(hit.x), abs(hit.y)) >= halfSize)
    {
        vec2 delta = hit - start;
        vec2 side = vec2(delta.x >= 0.0 ? 1.0 : -1.0, delta.y >= 0.0 ? 1.0 : -1.0);
        vec2 reach = (side * halfSize - start) / max(abs(delta), vec2_splat(0.0001)) * side;
        hit = start + delta * clamp(min(reach.x, reach.y), 0.0, 1.0);
    }

    float halfTexel = 0.5 / 128.0;
    vec2 uv = clamp(vec2(hit.x + halfSize, halfSize - hit.y) / (2.0 * halfSize), vec2_splat(halfTexel),
        vec2_splat(1.0 - halfTexel));
    return texture2DLod(s_skyVoid, uv, 0.0).r * u_skyVoid.w;
}

// The void over the below-horizon colour (display space): the air's limb turning into empty space, with stars by
// day and night (turned a quarter round from the sky's own, so they do not mirror them).
vec3 applyVoid(vec3 below, vec3 direction)
{
    float weight = skyVoidWeight(direction);

    if (weight <= 0.0)
    {
        return below;
    }

    vec3 horizonDirection = normalize(vec3(direction.xy, 0.0) + vec3(0.0, 0.0, 0.0001));
    vec3 horizon = mix(u_skyParams[6].rgb, skyLinearToDisplay(skyGradientLinear(horizonDirection)), u_skyFog[1].w);
    vec3 space = pow(skyVoidDisplay(direction, horizon), vec3_splat(2.2));
    float depth = asin(clamp(-direction.z, 0.0, 1.0));
    float starAmount = u_skyVoid.y * smoothstep(0.0, u_skyFog[SKY_VOID_LOOK].w, depth);

    if (starAmount > 0.001)
    {
        // Point stars of the void's own brightness and density, no painted band: the same by day and by night
        // whatever the preset's stars (D-109: the night void no lighter than the day's), near black between them.
        space += starField(vec3(-direction.y, direction.x, -direction.z), 0.0, 1.0, 1.0) * starAmount;
    }

    return mix(below, skyLinearToDisplay(space), weight);
}

// The pixel position is a parameter: the Metal shader build sees gl_FragCoord only inside main().
float skyDither(vec2 pixel)
{
    // Breaks up 8-bit banding in the smooth gradient.
    return (fract(sin(dot(pixel, vec2(12.9898, 78.233))) * 43758.5453) - 0.5) / 255.0;
}

void main()
{
    vec4 farPoint = mul(u_skyRay, vec4(v_texcoord1.xy, 0.5, 1.0));
    vec3 direction = normalize(farPoint.xyz / farPoint.w);
    float belowMode = u_skyParams[3].w;
    bool fogBelowHorizon = belowMode < 0.5 || belowMode > 1.5;

    // Well below the horizon only the fog colour remains (the blend below is complete there), and most of these
    // pixels are covered by terrain anyway: skip the sky layers.
    bool rimLit = max(u_skyRim[1].r, max(u_skyRim[1].g, u_skyRim[1].b)) > 0.0001;

    if (fogBelowHorizon && direction.z <= -0.012)
    {
        // The void over the hazed and misted fog colour: empty space keeps its dark and its stars by night too.
        vec3 below = applyVoid(mistApplySky(belowHorizonFog(direction, belowMode), direction), direction);

        if (rimLit)
        {
            below = skyLinearToDisplay(pow(below, vec3_splat(2.2)) + rimGlow(direction));
        }

        gl_FragColor = vec4(below + skyDither(gl_FragCoord.xy), 1.0);
        return;
    }

    vec3 skyDirection = belowMode > 0.5 && belowMode < 1.5 ? vec3(direction.xy, abs(direction.z)) : direction;
    vec3 color = skyGradientLinear(skyDirection);
    vec3 gradient = color;

    float starVisibility = u_skyParams[2].z * smoothstep(0.0, 0.15, skyDirection.z);

    if (starVisibility > 0.001)
    {
        color += starField(skyDirection, 0.6, u_skyParams[5].z, u_skyParams[5].w) * starVisibility;
    }

    float orbitHorizon = smoothstep(0.0, 0.15, skyDirection.z);

    if (u_skyOrbit[1].w > 0.001 && orbitHorizon > 0.0)
    {
        color += orbitRing(skyDirection) * orbitHorizon;
    }

    float moonVisibility = u_skyParams[2].y * smoothstep(-0.02, 0.04, skyDirection.z);

    if (moonVisibility > 0.001)
    {
        float moonCoverage;
        float moonLit;
        vec3 moon = moonDisc(skyDirection, moonCoverage, moonLit);
        // The unlit side hides the stars behind it but stays close to the sky's own colour.
        vec3 behindMoon = mix(color, gradient * 0.92, moonCoverage * moonVisibility);
        color = mix(behindMoon, moon, moonCoverage * moonVisibility * moonLit);
        color += moon * (1.0 - moonCoverage) * moonVisibility;
    }

    // The lights pass in front of the moon: they orbit far closer.
    if (u_skyOrbit[2].z > 0.5 && u_skyOrbit[3].w > 0.001 && skyDirection.z > 0.0)
    {
        color += orbitLights(skyDirection) * smoothstep(0.0, 0.05, skyDirection.z);
    }

    float sunFacing = dot(skyDirection, u_skyFog[3].xyz);
    float sunVisibility = u_skyParams[4].w * smoothstep(-0.03, 0.02, skyDirection.z);
    // Squared so a sun dimmed by overcast or fog fades to a pale smudge rather than a bright dot.
    float sunStrength = sunVisibility * sunVisibility;
    float sunDisc = smoothstep(u_skyParams[0].w - 0.00004, u_skyParams[0].w + 0.00002, sunFacing);
    if (sunStrength > 0.0001 && sunFacing > 0.99)
    {
        color += u_skyParams[0].rgb * sunStrength * (sunDisc * 6.0 + pow(sunFacing, 1800.0) * 0.6);
    }

    // The rim glow sits behind the cloud banks and clouds.
    vec3 rim = rimLit && direction.z >= 0.0 ? rimGlow(direction) : vec3_splat(0.0);
    color += rim;

    // Distant cloud banks around the horizon; luminance shapes the cloud, alpha its coverage.
    float ringHeight = max(u_skyParams[5].y, 0.001);

    if (u_skyParams[5].x > 0.001 && skyDirection.z < ringHeight)
    {
        float ringU = atan2(skyDirection.y, skyDirection.x) / (2.0 * SKY_PI) + 0.5;
        float ringV = 1.0 - clamp(skyDirection.z / ringHeight, 0.0, 1.0);
        vec4 ring = texture2D(s_skyRing, vec2(ringU, ringV));
        vec3 ringColor = mix(u_skyParams[4].rgb, u_skyParams[3].rgb, ring.r);
        // The lowest banks sit in the horizon haze.
        ringColor = mix(ringColor, u_skyFog[1].rgb, 0.2 + 0.6 * ringV * ringV * ringV);
        // The glow behind them lights the banks, so its base is not cut off from its part below the horizon.
        ringColor += rim;
        color = mix(color, ringColor, ring.a * u_skyParams[5].x);
    }

    // Clouds continue down to the horizon, crowding together in perspective and dissolving into its haze (see
    // applyCloud); only the last degree fades, where the layer's texels compress beyond filtering.
    float cloudFade = smoothstep(0.0, 0.02, skyDirection.z);

    // Layers 2 and 3 only carry weather cross-fades; each layer is skipped when transparent.
    if (cloudFade > 0.0)
    {
        float sunScatter = pow(max(sunFacing, 0.0), 6.0);

        if (u_skyClouds[0].w > 0.001)
        {
            vec4 texel = texture2D(s_skyCloud0, cloudUv(u_skyClouds[0], u_skyClouds[1], skyDirection));
            color = applyCloud(color, u_skyClouds[0], u_skyClouds[1], texel, skyDirection, cloudFade, sunScatter);
        }

        if (u_skyClouds[2].w > 0.001)
        {
            vec4 texel = texture2D(s_skyCloud1, cloudUv(u_skyClouds[2], u_skyClouds[3], skyDirection));
            color = applyCloud(color, u_skyClouds[2], u_skyClouds[3], texel, skyDirection, cloudFade, sunScatter);
        }

        if (u_skyClouds[4].w > 0.001)
        {
            vec4 texel = texture2D(s_skyCloud2, cloudUv(u_skyClouds[4], u_skyClouds[5], skyDirection));
            color = applyCloud(color, u_skyClouds[4], u_skyClouds[5], texel, skyDirection, cloudFade, sunScatter);
        }

        if (u_skyClouds[6].w > 0.001)
        {
            vec4 texel = texture2D(s_skyCloud3, cloudUv(u_skyClouds[6], u_skyClouds[7], skyDirection));
            color = applyCloud(color, u_skyClouds[6], u_skyClouds[7], texel, skyDirection, cloudFade, sunScatter);
        }
    }

    vec3 display = skyLinearToDisplay(color);

    // Below the horizon the sky continues as the world's fog colour, so distant terrain meets it seamlessly.
    if (fogBelowHorizon && direction.z < 0.004)
    {
        display = mix(display, belowHorizonFog(direction, belowMode), 1.0 - smoothstep(-0.012, 0.004, direction.z));
    }

    display = mistApplySky(display, direction);

    // The void after the mist (as in the early exit above); its limb starts from the horizon colour, so it joins.
    if (fogBelowHorizon && direction.z < 0.0)
    {
        display = applyVoid(display, direction);
    }

    // Below the horizon the glow shows over the fog colour (the void beyond the land's edge).
    if (rimLit && direction.z < 0.0)
    {
        display = skyLinearToDisplay(pow(display, vec3_splat(2.2)) + rimGlow(direction));
    }

    gl_FragColor = vec4(display + skyDither(gl_FragCoord.xy), 1.0);
}
