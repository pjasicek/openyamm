// A map's mist (scene `mist`, devdocs/MIST.md; packed by game/render/Mist.h): layers lying on a height and soft
// local volumes, each integrated along the view ray, so the mist has depth without a pass of its own. Included by
// sky_common.sh; its values follow the sky's own in u_skyFog:
// [8] layer count, volume count; [9] the volumes' patches: 1 / patch size, drift x, y;
// per layer from [10]: colour (display space), most it covers; base height, 1 / falloff height, density per unit,
// noise; 1 / depth (0: the mist stays dense below the base), 1 / patch size, drift x, y;
// per volume from [22]: centre, density per unit; 1 / radius, most it covers; colour, noise.
#define MIST_COUNTS 8
#define MIST_VOLUME_PATCHES 9
#define MIST_FIRST_LAYER 10
#define MIST_MAX_LAYERS 4
#define MIST_FIRST_VOLUME 22
#define MIST_MAX_VOLUMES 6

float mistHash(vec2 cell)
{
    return fract(sin(dot(cell, vec2(127.1, 311.7))) * 43758.5453);
}

float mistValueNoise(vec2 position)
{
    vec2 cell = floor(position);
    vec2 blend = fract(position);
    blend = blend * blend * (3.0 - 2.0 * blend);
    return mix(mix(mistHash(cell), mistHash(cell + vec2(1.0, 0.0)), blend.x),
        mix(mistHash(cell + vec2(0.0, 1.0)), mistHash(cell + vec2(1.0, 1.0)), blend.x), blend.y);
}

// Drifting patches, -1..1: two sizes moving apart, so the pattern changes as it travels. scaleDrift: 1 / patch size
// and the drift offset.
float mistPatches(vec3 position, vec3 scaleDrift)
{
    // The height shears the pattern a little, or walls would show it as vertical stripes.
    vec2 base = (position.xy + position.z * vec2(0.6, 0.35)) * scaleDrift.x;
    vec2 drift = scaleDrift.yz;
    float value = mistValueNoise(base + drift) * 0.65 + mistValueNoise(base * 2.7 - drift.yx * 1.9) * 0.35;
    return value * 2.0 - 1.0;
}

// The mean of exp(-u) between two values of u.
float mistMeanDensity(float from, float to)
{
    float span = to - from;
    return abs(span) > 0.001 ? (exp(-from) - exp(-to)) / span : exp(-from);
}

// One layer's optical depth from the eye over `toPoint`: densest at the base, falling off above it and (with a depth)
// below it. shape: base height, 1 / falloff height, density per unit; downRate: 1 / depth, 0 without one.
float mistLayerDepth(vec3 eye, vec3 toPoint, float distance, vec4 shape, float downRate)
{
    float eyeHeight = eye.z - shape.x;
    float pointHeight = eyeHeight + toPoint.z;
    float eyeScaled = eyeHeight >= 0.0 ? eyeHeight * shape.y : -eyeHeight * downRate;
    float pointScaled = pointHeight >= 0.0 ? pointHeight * shape.y : -pointHeight * downRate;
    float average;

    if (eyeHeight * pointHeight >= 0.0)
    {
        average = mistMeanDensity(eyeScaled, pointScaled);
    }
    else
    {
        // The way crosses the base: the part on the eye's side, then the part on the point's.
        float crossing = eyeHeight / (eyeHeight - pointHeight);
        average = crossing * mistMeanDensity(eyeScaled, 0.0) + (1.0 - crossing) * mistMeanDensity(0.0, pointScaled);
    }

    return shape.z * distance * average;
}

// One volume's optical depth: an ellipsoid whose density falls from the centre to nothing at its surface.
float mistVolumeDepth(vec3 eye, vec3 toPoint, float distance, vec4 centre, vec3 inverseRadius)
{
    vec3 origin = (eye - centre.xyz) * inverseRadius;
    vec3 along = toPoint * inverseRadius;
    float a = dot(along, along);
    float b = 2.0 * dot(origin, along);
    float c = dot(origin, origin) - 1.0;
    float discriminant = b * b - 4.0 * a * c;

    if (a < 1.0e-12 || discriminant <= 0.0)
    {
        return 0.0;
    }

    float root = sqrt(discriminant);
    float enter = max((-b - root) / (2.0 * a), 0.0);
    float leave = min((-b + root) / (2.0 * a), 1.0);

    if (leave <= enter)
    {
        return 0.0;
    }

    // The density is 1 - r^2 of the unit sphere, -(a t^2 + b t + c) along the ray.
    float inside = -(a * (leave * leave * leave - enter * enter * enter) / 3.0
        + b * (leave * leave - enter * enter) * 0.5 + c * (leave - enter));
    return centre.w * distance * inside;
}

bool mistEnabled()
{
    return u_skyFog[MIST_COUNTS].x + u_skyFog[MIST_COUNTS].y > 0.5;
}

// The mist between the eye and a point `toPoint` away: its colour (display space) and how much of the pixel it covers.
// patchScale 0 leaves the drifting patches out (the sky, whose far end has no place for them).
vec4 mistAlong(vec3 eye, vec3 toPoint, float patchScale)
{
    float distance = length(toPoint);
    vec3 endPoint = eye + toPoint;
    float clear = 1.0;
    vec3 color = vec3_splat(0.0);
    float weight = 0.0;

    for (int band = 0; band < MIST_MAX_LAYERS; ++band)
    {
        if (float(band) >= u_skyFog[MIST_COUNTS].x)
        {
            break;
        }

        vec4 tint = u_skyFog[MIST_FIRST_LAYER + band * 3];
        vec4 shape = u_skyFog[MIST_FIRST_LAYER + band * 3 + 1];
        vec4 extent = u_skyFog[MIST_FIRST_LAYER + band * 3 + 2];
        float depth = mistLayerDepth(eye, toPoint, distance, shape, extent.x);

        if (depth <= 0.0)
        {
            continue;
        }

        if (shape.w * patchScale > 0.0 && depth > 0.004)
        {
            // Seen from above, the patches lie where the view enters the mist, so they keep their place as the eye
            // moves; from inside they lie on what is seen.
            float top = shape.x + 1.0 / shape.y;
            float above = clamp((eye.z - top) * shape.y, 0.0, 1.0);
            vec3 patchPoint = endPoint;
            if (above > 0.0 && endPoint.z < top)
            {
                patchPoint = mix(endPoint, eye + toPoint * ((top - eye.z) / min(toPoint.z, -0.001)), above);
            }
            depth *= 1.0 + shape.w * mistPatches(patchPoint, extent.yzw);
        }

        float cover = min(1.0 - exp(-depth), tint.w);
        clear *= 1.0 - cover;
        color += tint.rgb * cover;
        weight += cover;
    }

    for (int index = 0; index < MIST_MAX_VOLUMES; ++index)
    {
        if (float(index) >= u_skyFog[MIST_COUNTS].y)
        {
            break;
        }

        vec4 centre = u_skyFog[MIST_FIRST_VOLUME + index * 3];
        vec4 shape = u_skyFog[MIST_FIRST_VOLUME + index * 3 + 1];
        vec4 tint = u_skyFog[MIST_FIRST_VOLUME + index * 3 + 2];
        float depth = mistVolumeDepth(eye, toPoint, distance, centre, shape.xyz);

        if (depth <= 0.0)
        {
            continue;
        }

        if (tint.w * patchScale > 0.0)
        {
            depth *= 1.0 + tint.w * mistPatches(endPoint, u_skyFog[MIST_VOLUME_PATCHES].xyz);
        }

        float cover = min(1.0 - exp(-depth), shape.w);
        clear *= 1.0 - cover;
        color += tint.rgb * cover;
        weight += cover;
    }

    return vec4(color / max(weight, 0.0001), 1.0 - clear);
}

// A finished display colour seen through the map's mist; unchanged on a map without any.
vec3 mistApply(vec3 displayColor, vec3 worldPosition)
{
    if (!mistEnabled())
    {
        return displayColor;
    }

    vec3 eye = skyCameraPosition();
    vec4 mist = mistAlong(eye, worldPosition - eye, 1.0);
    return mix(displayColor, mist.rgb, mist.a);
}

// How much of a pixel stays clear of the mist: glows and other additive light fade by it instead of taking its colour.
float mistClear(vec3 worldPosition)
{
    if (!mistEnabled())
    {
        return 1.0;
    }

    vec3 eye = skyCameraPosition();
    return 1.0 - mistAlong(eye, worldPosition - eye, 1.0).a;
}

// The sky seen through the mist in a direction: the view runs on to where the layers have thinned to nothing.
vec3 mistApplySky(vec3 displayColor, vec3 direction)
{
    if (!mistEnabled())
    {
        return displayColor;
    }

    vec4 mist = mistAlong(skyCameraPosition(), direction * 200000.0, 0.0);
    return mix(displayColor, mist.rgb, mist.a);
}
