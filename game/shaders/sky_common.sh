// Enhanced sky colour shared by the sky pass and every outdoor fog blend. u_skyFog colours are linear RGB:
// [0] zenith, horizon exponent; [1] horizon, sky share of the fog colour (0 = flat fog, Classic);
// [2] sun glow colour * strength, glow exponent; [3] sun direction, lightning flash;
// [4] map half size (0 = no edge fade), map centre x, y, aerial haze at the far distance;
// [5] lit water colour of the open sea past the map edge (display space), sea visibility (0 in dense fog);
// [6] camera height above the sea, distance at which the sea's haze reaches 63%, camera x, y from the map centre;
// [7] sea past the west (-X), east (+X), south (-Y) and north (+Y) edges (0 = land, 1 = open sea);
// [8] onward: the map's mist (mist.sh, included below), all zero on a map without any;
// [40] the void past the west, east, south and north edges (terrain.void; 0 = none);
// [41] empty space's colour (linear), the air limb's depth below the horizon (radians; 0 = the map has no void).
uniform vec4 u_skyFog[42];
#define SKY_VOID_SIDES 40
#define SKY_VOID_LOOK 41

// Strongest share of the preset's aerial haze that distance alone adds before the view-distance fade.
#define AerialHazeDepth 0.35
// Share of the view distance at which geometry starts fading completely into the sky before it is clipped.
#define ViewEndFadeStart 0.55

vec3 skyLinearToDisplay(vec3 color)
{
    return pow(max(color, vec3_splat(0.0)), vec3_splat(1.0 / 2.2));
}

vec3 skyGradientLinear(vec3 direction)
{
    float up = clamp(direction.z, 0.0, 1.0);
    float towardHorizon = pow(1.0 - up, u_skyFog[0].w);
    vec3 color = mix(u_skyFog[0].rgb, u_skyFog[1].rgb, towardHorizon);
    float sunAmount = max(dot(direction, u_skyFog[3].xyz), 0.0);
    // The glow lobe is strongest close to the horizon, where the light crosses the most air.
    color += u_skyFog[2].rgb * pow(sunAmount, u_skyFog[2].w) * (0.35 + 0.65 * towardHorizon);
    color += vec3(0.55, 0.6, 0.75) * u_skyFog[3].w * 0.5;
    return color;
}

vec3 skyCameraPosition()
{
    return mul(u_invView, vec4(0.0, 0.0, 0.0, 1.0)).xyz;
}

#include "mist.sh"

// Extra fog that reaches full strength where the view leaves the map, so terrain and water meet the fogged
// horizon without a visible edge. Only with the Enhanced sky; visibility inside the map is unchanged.
float skyMapEdgeFog(vec3 worldPosition)
{
    float halfSize = u_skyFog[4].x;

    if (u_skyFog[1].w <= 0.0 || halfSize <= 0.0)
    {
        return 0.0;
    }

    vec3 cameraPosition = skyCameraPosition();
    vec2 local = cameraPosition.xy - u_skyFog[4].yz;

    if (abs(local.x) >= halfSize || abs(local.y) >= halfSize)
    {
        return 0.0;
    }

    vec2 offset = worldPosition.xy - cameraPosition.xy;
    float horizontalDistance = length(offset);

    // The fade starts no nearer than it would toward the closest edge (the start grows with edge distance).
    float nearestEdge = halfSize - max(abs(local.x), abs(local.y));
    if (horizontalDistance < nearestEdge - clamp(nearestEdge * 0.35, 1024.0, 8192.0))
    {
        return 0.0;
    }

    vec2 direction = offset / max(horizontalDistance, 0.001);
    vec2 side = vec2(direction.x >= 0.0 ? 1.0 : -1.0, direction.y >= 0.0 ? 1.0 : -1.0);
    vec2 exitDistance = (side * halfSize - local) / max(abs(direction), vec2_splat(0.0001)) * side;
    float edgeDistance = min(exitDistance.x, exitDistance.y);
    float fadeWidth = clamp(edgeDistance * 0.35, 1024.0, 8192.0);
    return smoothstep(edgeDistance - fadeWidth, edgeDistance, horizontalDistance);
}

// The per-side weight (west, east, south, north) of the side where a view ray in this horizontal direction leaves
// the terrain square, blended across the corners.
float skyExitSideWeight(vec2 direction, vec4 sides)
{
    float halfSize = u_skyFog[4].x;
    vec2 local = clamp(u_skyFog[6].zw, vec2_splat(-halfSize), vec2_splat(halfSize));
    vec2 side = vec2(direction.x >= 0.0 ? 1.0 : -1.0, direction.y >= 0.0 ? 1.0 : -1.0);
    vec2 exitDistance = (side * halfSize - local) / max(abs(direction), vec2_splat(0.0001)) * side;
    float sideX = direction.x >= 0.0 ? sides.y : sides.x;
    float sideY = direction.y >= 0.0 ? sides.w : sides.z;
    // Blend across the corner where the exit moves from an X side to a Y side.
    float towardY = smoothstep(-0.6, 0.6,
        (exitDistance.x - exitDistance.y) / max(min(exitDistance.x, exitDistance.y), 1.0));
    return mix(sideX, sideY, towardY);
}

// How much open sea lies past the map edge where a view ray in this horizontal direction leaves the terrain square.
float skySeaWeight(vec2 direction)
{
    if (u_skyFog[4].x <= 0.0 || u_skyFog[5].w <= 0.0)
    {
        return 0.0;
    }

    return skyExitSideWeight(direction, u_skyFog[7]) * u_skyFog[5].w;
}

// How much of the void (the world's end, terrain.void) lies past the map edge in this horizontal direction; 0 on a
// map without void. The side weights come with what dense fog leaves of the void (SkyRenderer: haze does not grey it).
float skyVoidSideWeight(vec2 direction)
{
    if (u_skyFog[SKY_VOID_LOOK].w <= 0.0 || u_skyFog[4].x <= 0.0)
    {
        return 0.0;
    }

    return skyExitSideWeight(direction, u_skyFog[SKY_VOID_SIDES]);
}

// Empty space below the horizon in `direction`: the horizon's haze over the first degrees down (the air's limb,
// glowing at the world's edge), then the space colour.
vec3 skyVoidDisplay(vec3 direction, vec3 horizonDisplay)
{
    float depth = asin(clamp(-direction.z, 0.0, 1.0));
    float limb = smoothstep(0.0, u_skyFog[SKY_VOID_LOOK].w, depth);
    return mix(horizonDisplay, skyLinearToDisplay(u_skyFog[SKY_VOID_LOOK].rgb), limb);
}

// The open sea past the map edge, below the horizon in `direction`: the water colour turning into the sky's
// reflection at grazing angles (as fs_water does), hazed toward the horizon colour with distance along the view.
vec3 skyDistantSeaDisplay(vec3 direction, vec3 horizonDisplay)
{
    float down = max(-direction.z, 0.00001);
    float distance = u_skyFog[6].x / down;
    float grazing = 1.0 - down;
    float fresnel = 0.02 + 0.98 * grazing * grazing * grazing * grazing * grazing;
    vec3 reflected = skyLinearToDisplay(skyGradientLinear(vec3(direction.xy, down)));
    vec3 sea = mix(u_skyFog[5].rgb, reflected, fresnel);
    return mix(sea, horizonDisplay, 1.0 - exp(-distance / u_skyFog[6].y));
}

// On a map with void (terrain.void), geometry below the void's floor (z 0: the hull's deck and underside, falls pouring
// off the rim) fades into empty space with its depth, so nothing ends in a hard edge in space.
float skyVoidDepthFog(vec3 worldPosition)
{
    if (u_skyFog[SKY_VOID_LOOK].w <= 0.0)
    {
        return 0.0;
    }

    return smoothstep(200.0, 2600.0, -worldPosition.z);
}

// Enhanced fog ratio: the world's distance fog, aerial haze that grows toward the far distance, the map-edge fade and
// the void's depth. Classic (no sky share) keeps the world fog ratio unchanged.
float skyFogRatio(float fogRatio, vec3 worldPosition, float distance, float farDistance)
{
    if (u_skyFog[1].w <= 0.0)
    {
        return fogRatio;
    }

    // A gentle depth cue through the middle distance (towns a few thousand units away stay clear), then a steep fade
    // that reaches the sky completely at the view distance. The world fog's own fade spans only the last few
    // percent, which from the air shows as a hard cut where the terrain ends.
    float haze = max(u_skyFog[4].w * AerialHazeDepth * smoothstep(farDistance * 0.3, farDistance * 0.9, distance),
        smoothstep(farDistance * ViewEndFadeStart, farDistance, distance));
    return max(max(max(fogRatio, haze), skyMapEdgeFog(worldPosition)), skyVoidDepthFog(worldPosition));
}

// Water fog ratio: on a sea-facing view the water fades into the open sea past the map edge over the whole far
// distance (as the original aerial haze did), so its end at the view distance cannot be seen. Land, coast and
// buildings keep the gentle haze of skyFogRatio(); water facing land (rivers, lakes) is unchanged.
float skyWaterFogRatio(float fogRatio, vec3 worldPosition, float distance, float farDistance)
{
    float ratio = skyFogRatio(fogRatio, worldPosition, distance, farDistance);
    vec3 toFragment = worldPosition - skyCameraPosition();

    if (u_skyFog[1].w <= 0.0 || toFragment.z >= 0.0)
    {
        return ratio;
    }

    float sea = skySeaWeight(toFragment.xy);
    return max(ratio, sea * smoothstep(farDistance * 0.4, farDistance * 0.97, distance));
}

// The colour distant geometry fades into: the sky colour behind it, mixed with the flat fog colour (display space).
// Fragments whose fog cannot change their 8-bit colour (most nearby geometry) skip the sky evaluation.
vec3 skyFogDisplayColor(float fogRatio, vec3 flatDisplayColor, vec3 worldPosition)
{
    if (u_skyFog[1].w <= 0.0 || fogRatio < 1.0 / 255.0)
    {
        return flatDisplayColor;
    }

    vec3 toFragment = worldPosition - skyCameraPosition();
    vec3 direction = normalize(vec3(toFragment.xy, max(toFragment.z, 0.0)) + vec3(0.0, 0.0, 0.0001));
    vec3 color = mix(flatDisplayColor, skyLinearToDisplay(skyGradientLinear(direction)), u_skyFog[1].w);

    // Below the horizon on a sea-facing view, what lies behind distant geometry is the sea that continues past the
    // map edge (the sky pass draws it there), so fogged water, coast and ships fade into it rather than into a band
    // of horizon haze.
    float sea = toFragment.z < 0.0 ? skySeaWeight(direction.xy) : 0.0;
    color = sea > 0.0 ? mix(color, skyDistantSeaDisplay(normalize(toFragment), color), sea) : color;

    // Below the horizon toward the void (terrain.void), what lies behind is empty space: the hull, the cliffs and
    // the falls fade into it rather than into the horizon haze; shallow views keep the haze (the air's limb).
    // Under the void's floor every view looks into it.
    float voidWeight = toFragment.z < 0.0 ? skyVoidSideWeight(direction.xy) : 0.0;
    voidWeight = u_skyFog[SKY_VOID_LOOK].w > 0.0 && worldPosition.z < 0.0 ? 1.0 : voidWeight;
    return voidWeight > 0.0 ? mix(color, skyVoidDisplay(normalize(toFragment), color), voidWeight) : color;
}
