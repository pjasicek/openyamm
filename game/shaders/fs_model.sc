$input v_texcoord0, v_worldNormal, v_worldPosition, v_color0, v_texcoord1, v_flowInfo, v_sector

#include "common.sh"
#include "sky_common.sh"
#include "world_clip.sh"
#include "sun_shadows.sh"
#include "light_grid.sh"

#ifndef MODEL_PREPASSED
#define MODEL_PREPASSED 0
#endif
// ALPHA_TO_COVERAGE: the depth prepass of alpha-tested foliage into a multisampled world target. Instead of
// discarding below the cutoff it outputs coverage for alpha to coverage, sharpened to about a pixel around the cutoff:
// the leaf edge then covers a fraction of each pixel's samples instead of stair-stepping (and crawling as the camera
// moves). The shaded pass after it (equal depth, per sample) colours exactly those samples.
#ifndef ALPHA_TO_COVERAGE
#define ALPHA_TO_COVERAGE 0
#endif

SAMPLER2D(s_modelTexture, 0);
SAMPLER2D(s_modelNormal, 1);
SAMPLER2D(s_modelMetallicRoughness, 2);
SAMPLERCUBE(s_modelEnvironment, 3);
SAMPLER2D(s_modelEnvironmentBrdf, 4);
SAMPLER2D(s_modelRegionMask, 8);
SAMPLER2D(s_modelRegionRamp, 9);
SAMPLER2D(s_modelBurn, 10);
uniform vec4 u_modelEnvironment;
uniform vec4 u_modelSurface;
uniform vec4 u_modelPbr;
uniform vec4 u_modelMaterial[2];
uniform vec4 u_modelRegion[3];
uniform vec4 u_modelLighting[4];
uniform vec4 u_modelPointPositions[12];
uniform vec4 u_modelPointColors[12];
uniform vec4 u_modelFog[3];
uniform vec4 u_modelCamera;
uniform vec4 u_modelOutline;
// Bloom glow pass: x = 1 to output only the glow, y = a card's glow weight (0: the emission).
uniform vec4 u_modelGlow;
uniform vec4 u_modelEdge;
// Burning creature (ModelBurn): [0] front, char, edge and fire widths in burn-map units; [1] emission colour (linear,
// brightness included) and clock in seconds; [2].x pass: 0 none, 1 the burning surface, 2 the fire over its burnt part.
uniform vec4 u_modelBurn[3];

vec3 modelNormalize(vec3 value)
{
    return value * inversesqrt(max(dot(value, value), 0.000001));
}

vec3 modelEncodeSrgb(vec3 value)
{
    value = max(value, vec3_splat(0.0));
    return mix(value * 12.92, 1.055 * pow(value, vec3_splat(1.0 / 2.4)) - 0.055,
        step(vec3_splat(0.0031308), value));
}

// The specular lobe alone (specularScale > 0), in the units of modelBrdf.
vec3 modelSpecular(vec3 normal, vec3 view, vec3 light, vec3 base, float metallic, float roughness, float specularScale)
{
    float nl = max(dot(normal, light), 0.0);
    vec3 f0 = mix(vec3_splat(0.04), base, metallic);
    float nv = max(dot(normal, view), 0.0001);
    vec3 halfDirection = modelNormalize(light + view);
    float nh = max(dot(normal, halfDirection), 0.0);
    float vh = max(dot(view, halfDirection), 0.0);
    float alpha = roughness * roughness;
    float alphaSquared = alpha * alpha;
    float denominator = nh * nh * (alphaSquared - 1.0) + 1.0;
    float distribution = alphaSquared / max(3.14159265 * denominator * denominator, 0.0000001);
    float k = (roughness + 1.0) * (roughness + 1.0) / 8.0;
    float geometry = (nl / max(nl * (1.0 - k) + k, 0.0001))
        * (nv / max(nv * (1.0 - k) + k, 0.0001));
    // pow() of a negative base is undefined (NaN on some GPUs): with the light at the camera (the party light), vh
    // rounds to just above 1 and scattered pixels turn black.
    vec3 fresnel = f0 + (1.0 - f0) * pow(max(1.0 - vh, 0.0), 5.0);
    // Existing light intensities use unit diffuse irradiance, rather than radiance divided by pi.
    return distribution * geometry * fresnel / max(4.0 * nl * nv, 0.0001) * specularScale * (nl * 3.14159265);
}

vec3 modelBrdf(vec3 normal, vec3 view, vec3 light, vec3 base, float metallic, float roughness, float specularScale)
{
    float nl = max(dot(normal, light), 0.0);
    vec3 f0 = mix(vec3_splat(0.04), base, metallic);
    if (specularScale <= 0.0)
    {
        // Diffuse only (foliage cards): no half-vector, distribution or geometry terms.
        return (1.0 - f0) * (1.0 - metallic) * base * nl;
    }
    float vh = max(dot(view, modelNormalize(light + view)), 0.0);
    vec3 fresnel = f0 + (1.0 - f0) * pow(max(1.0 - vh, 0.0), 5.0);
    vec3 diffuse = (1.0 - fresnel) * (1.0 - metallic) * base;
    return diffuse * nl + modelSpecular(normal, view, light, base, metallic, roughness, specularScale);
}

// One point light ((1 - d^2/r^2)^2 falloff, as the bakes): GGX diffuse and specular into shaded and the light level,
// or, specularOnly, only its specular lobe into highlights.
void modelPointLight(vec4 positionRadius, vec4 colorIntensity, vec3 worldPosition, vec3 normal, vec3 view,
    vec3 base, float metallic, float roughness, float specularScale, bool specularOnly,
    inout vec3 shaded, inout vec3 lightLevel, inout vec3 highlights)
{
    vec3 delta = positionRadius.xyz - worldPosition;
    float radius = max(positionRadius.w, 0.0001);
    float attenuation = max(1.0 - dot(delta, delta) / (radius * radius), 0.0);
    // "point" is a reserved word in the HLSL front end the Metal shader build goes through.
    vec3 pointLight = colorIntensity.rgb * colorIntensity.w * attenuation * attenuation;
    if (specularOnly)
    {
        if (specularScale > 0.0)
        {
            highlights += modelSpecular(normal, view, modelNormalize(delta), base, metallic, roughness, specularScale)
                * pointLight;
        }
        return;
    }
    shaded += modelBrdf(normal, view, modelNormalize(delta), base, metallic, roughness, specularScale) * pointLight;
    lightLevel += pointLight;
}

// Ordered 4x4 dither threshold in [0, 1) for screen-door LOD crossfades.
float modelDither(vec2 pixel)
{
    vec2 cell = floor(pixel);
    vec2 coarse = floor(cell * 0.5);
    float fine = fract(dot(cell, vec2(0.5, cell.y * 0.75)));
    float wide = fract(dot(coarse, vec2(0.5, coarse.y * 0.75)));
    return fine + wide * 0.25 + 0.03125;
}

// Smooth value noise in [0, 1], for the flicker of burning surfaces and their fire.
float modelBurnHash(vec3 cell)
{
    return fract(sin(dot(cell, vec3(127.1, 311.7, 74.7))) * 43758.5453);
}

float modelBurnNoise(vec3 position)
{
    vec3 cell = floor(position);
    vec3 f = fract(position);
    f = f * f * (3.0 - 2.0 * f);
    float x00 = mix(modelBurnHash(cell), modelBurnHash(cell + vec3(1.0, 0.0, 0.0)), f.x);
    float x10 = mix(modelBurnHash(cell + vec3(0.0, 1.0, 0.0)), modelBurnHash(cell + vec3(1.0, 1.0, 0.0)), f.x);
    float x01 = mix(modelBurnHash(cell + vec3(0.0, 0.0, 1.0)), modelBurnHash(cell + vec3(1.0, 0.0, 1.0)), f.x);
    float x11 = mix(modelBurnHash(cell + vec3(0.0, 1.0, 1.0)), modelBurnHash(cell + vec3(1.0, 1.0, 1.0)), f.x);
    return mix(mix(x00, x10, f.y), mix(x01, x11, f.y), f.z);
}

float modelSmoothstep(float low, float high, float value)
{
    float amount = clamp((value - low) / max(high - low, 1.0), 0.0, 1.0);
    return amount * amount * (3.0 - 2.0 * amount);
}

void main()
{
    // Burn pass 2: fire where the surface has just burnt away (behind its glowing edge, for the fire width), rising
    // through world-space noise and strongest along the silhouette, so the body briefly remains a shape of flame.
    // Premultiplied over the scene in display space; fog fades it.
    if (u_modelBurn[2].x > 1.5)
    {
        float burnt = u_modelBurn[0].x - texture2D(s_modelBurn, v_texcoord0).r - u_modelBurn[0].z;
        if (burnt <= 0.0 || burnt >= u_modelBurn[0].w)
        {
            discard;
        }
        float life = 1.0 - burnt / u_modelBurn[0].w;
        vec3 view = modelNormalize(u_modelCamera.xyz - v_worldPosition);
        float silhouette = 1.0 - abs(dot(modelNormalize(v_worldNormal), view));
        vec3 rising = v_worldPosition * vec3(0.06, 0.06, 0.025) - vec3(0.0, 0.0, u_modelBurn[1].w * 2.2);
        float flame = modelBurnNoise(rising) * 0.65 + modelBurnNoise(rising * 2.3 + vec3_splat(7.1)) * 0.35;
        float amount = life * (0.35 + 0.65 * silhouette * silhouette) * smoothstep(0.45, 0.85, flame + 0.2 * life);
        float fireDistance = length(v_worldPosition - u_modelCamera.xyz);
        float fireFog = u_modelFog[1].w > 0.5
            ? clamp((fireDistance - u_modelFog[2].x) / max(u_modelFog[2].y - u_modelFog[2].x, 1.0), 0.0, 1.0)
            : modelSmoothstep(u_modelFog[2].y, u_modelFog[2].z, fireDistance);
        // The emission colour's hue at a level below white (additive layers and both faces add up), turning
        // yellow in the hottest tongues.
        float hue = max(max(u_modelBurn[1].r, u_modelBurn[1].g), max(u_modelBurn[1].b, 0.0001));
        float level = clamp(amount * hue * 0.45, 0.0, 0.8);
        vec3 fire = u_modelBurn[1].rgb / hue * level + vec3(0.0, 0.3, 0.06) * level * level;
        float cover = clamp(level * 1.3, 0.0, 0.9) * (1.0 - fireFog);
        gl_FragColor = vec4(modelEncodeSrgb(fire) * (1.0 - fireFog), cover);
        return;
    }
    // Base textures are sRGB; the sampler decodes RGB, while factors and alpha stay linear.
    // v_flowInfo.rgb: glTF vertex colour (canopy occlusion on foliage), white on creatures.
    vec4 color = texture2D(s_modelTexture, v_texcoord0) * u_modelMaterial[0] * vec4(v_flowInfo.rgb, 1.0);
#if !MODEL_PREPASSED
    // Water reflections keep only what is above the water plane (zero plane elsewhere).
    clipWorldPosition(v_worldPosition);
    // MODEL_PREPASSED: the shaded pass after a depth prepass. Its equal-depth test already holds the alpha test and the
    // crossfade dither, and a shader without discard keeps the GPU's early depth rejection.
#if ALPHA_TO_COVERAGE
    float coverage = u_modelMaterial[1].y > 0.5
        ? clamp((color.a - u_modelMaterial[1].x) / max(fwidth(color.a), 0.0001) + 0.5, 0.0, 1.0) : 1.0;
#else
    if (u_modelMaterial[1].y > 0.5 && color.a < u_modelMaterial[1].x)
    {
        discard;
    }
#endif
    // Static LOD crossfade (v_texcoord1.w): (0, 1) = the new level appearing, (1, 2) = the old one leaving, with
    // complementary dither so the two always cover each pixel exactly once.
    // v_texcoord1.w also carries the leaves' sun-shadow lift in multiples of 4 (vs_model_instanced.sc); the rounding
    // keeps an interpolated 4 x lift that lands just below its value from reading as a crossfade near 4.
    // Interpolating that per-instance constant drifts by about 1e-5 (more as the lift grows), so a crossfade starts
    // above a small threshold: a drift read as a level just appearing would discard nearly all of a leaf's pixels.
    float crossfade = v_texcoord1.w - 4.0 * floor((v_texcoord1.w + 1.0) * 0.25);
    if (crossfade > 0.002)
    {
        float threshold = modelDither(gl_FragCoord.xy);
        bool leaving = crossfade > 1.0;
        float progress = leaving ? crossfade - 1.0 : crossfade;
        if (leaving ? threshold < progress : threshold >= progress)
        {
            discard;
        }
    }
#endif
#if ALPHA_TO_COVERAGE
    gl_FragColor = vec4(0.0, 0.0, 0.0, coverage);
    return;
#endif
    // Burn pass 1: the surface the front has passed beyond its glowing edge is gone; ahead of the front it chars, with
    // cracks glowing through (burn map green), and the edge itself glows brightest where the hole begins.
    float burnChar = 0.0;
    vec3 burnGlow = vec3_splat(0.0);
#if !MODEL_PREPASSED
    if (u_modelBurn[2].x > 0.5)
    {
        vec2 burnTexel = texture2D(s_modelBurn, v_texcoord0).rg;
        float past = u_modelBurn[0].x - burnTexel.r;
        if (past > u_modelBurn[0].z)
        {
            discard;
        }
        float flicker = modelBurnNoise(v_worldPosition * 0.06 - vec3(0.0, 0.0, u_modelBurn[1].w * 3.0));
        burnChar = smoothstep(-u_modelBurn[0].y, 0.0, past);
        float edge = smoothstep(-u_modelBurn[0].z, u_modelBurn[0].z, past);
        float cracks = burnChar * burnChar * smoothstep(0.5, 0.85, burnTexel.g + 0.25 * flicker);
        burnGlow = u_modelBurn[1].rgb * (edge * edge * (0.7 + 0.6 * flicker) + 0.45 * cracks);
    }
#endif
    if (u_modelOutline.w > 1.5 && u_modelOutline.w < 2.5)
    {
        // Depth prepass (creatures, static foliage): depth and the alpha test above are all it needs.
        gl_FragColor = vec4_splat(0.0);
        return;
    }
    if (dot(u_modelRegion[2], vec4_splat(1.0)) > 0.5)
    {
        // Colour variant of a shared skin: inside each region-mask channel the colour follows that region's ramp
        // (one row of 16 stops), indexed by the luminance normalised to the region's range.
        vec4 regionMask = texture2D(s_modelRegionMask, v_texcoord0) * u_modelRegion[2];
        float luminance = dot(color.rgb, vec3(0.2126, 0.7152, 0.0722));
        vec4 position = clamp((vec4_splat(luminance) - u_modelRegion[0])
            / max(u_modelRegion[1] - u_modelRegion[0], vec4_splat(0.0001)), 0.0, 1.0);
        vec4 rampU = (position * 15.0 + 0.5) / 16.0;
        color.rgb = mix(color.rgb, texture2D(s_modelRegionRamp, vec2(rampU.x, 0.125)).rgb, regionMask.r);
        color.rgb = mix(color.rgb, texture2D(s_modelRegionRamp, vec2(rampU.y, 0.375)).rgb, regionMask.g);
        color.rgb = mix(color.rgb, texture2D(s_modelRegionRamp, vec2(rampU.z, 0.625)).rgb, regionMask.b);
        color.rgb = mix(color.rgb, texture2D(s_modelRegionRamp, vec2(rampU.w, 0.875)).rgb, regionMask.a);
    }
    color.rgb *= 1.0 - 0.94 * burnChar;
    // Creature contour shell (outline flag 3): the albedo darkened by u_modelOutline.x in the ambient light, then fogged.
    // Unlit and without emission: early depth rejection is off with the alpha test, so this also runs for much of the
    // shell the body hides.
    bool contour = u_modelOutline.w > 2.5;
    if (u_modelOutline.w > 0.5 && !contour)
    {
        gl_FragColor = vec4(u_modelOutline.rgb, 1.0);
        return;
    }
    vec3 shaded = color.rgb;
    if (contour)
    {
        shaded *= u_modelOutline.x * clamp(u_modelLighting[2].rgb * u_modelLighting[2].w * v_color0.rgb, 0.0, 1.0);
    }
    else if (u_modelMaterial[1].z < 0.5)
    {
        vec3 normal = modelNormalize(v_worldNormal);
        // Alpha-tested decoration leaves (MODEL_PREPASSED, shaded after their depth prepass) skip the normal map and,
        // below, the sky reflection: on cards that small their relief and faint sheen do not show, and the leaves cover
        // much of a forest view (out07 dense view: 0.83 -> 0.80 ms GPU per frame, desktop).
        if (u_modelSurface.w >= 0.0 && MODEL_PREPASSED == 0)
        {
            vec3 dp1 = dFdx(v_worldPosition);
            vec3 dp2 = dFdy(v_worldPosition);
            vec2 duv1 = dFdx(v_texcoord0);
            vec2 duv2 = dFdy(v_texcoord0);
            vec3 p1 = cross(normal, dp1);
            vec3 p2 = cross(dp2, normal);
            vec3 tangent = p2 * duv1.x + p1 * duv2.x;
            vec3 bitangent = p2 * duv1.y + p1 * duv2.y;
            // The frame is the texture gradient times the screen determinant, whose sign follows the backend's window
            // y direction (up in OpenGL, down in Vulkan) and the facing: divide it out, so tangent points along +u
            // and bitangent along +v (down the image) on every backend.
            float inverseLength = inversesqrt(max(max(dot(tangent, tangent), dot(bitangent, bitangent)), 0.000001))
                * (dot(dp1, p2) < 0.0 ? -1.0 : 1.0);
            // z is rebuilt from x and y: cooked normal maps are two-channel (BC5, EAC RG). glTF convention: +x along
            // +u, +y up the image (against +v). tools/normal_map_convention.py converts Meshy's +y-down maps.
            vec2 mappedXy = texture2D(s_modelNormal, v_texcoord0).xy * 2.0 - 1.0;
            vec3 mapped = vec3(mappedXy * u_modelSurface.w, sqrt(max(1.0 - dot(mappedXy, mappedXy), 0.0)));
            normal = modelNormalize(tangent * inverseLength * mapped.x
                - bitangent * inverseLength * mapped.y + normal * mapped.z);
        }
        vec3 view = modelNormalize(u_modelCamera.xyz - v_worldPosition);
        if (u_modelMaterial[1].w > 0.5 && dot(normal, view) < 0.0)
        {
            normal = -normal;
        }
        vec4 surface = texture2D(s_modelMetallicRoughness, v_texcoord0);
        float metallic = clamp(surface.b * u_modelPbr.x, 0.0, 1.0);
        float roughness = clamp(surface.g * u_modelPbr.y, 0.045, 1.0);
        float nv = max(dot(normal, view), 0.0001);
        vec3 f0 = mix(vec3_splat(0.04), color.rgb, metallic);
        vec3 fresnel = f0 + (max(vec3_splat(1.0 - roughness), f0) - f0) * pow(max(1.0 - nv, 0.0), 5.0);
        // ponytail: upward probe fill uses a hemisphere; directional indirect probes if this loses needed contrast.
        // v_color0: per-placement ambient (rgb) and sun (a) scales; v_texcoord1: undirected point light.
        vec3 lightLevel = u_modelLighting[2].rgb * u_modelLighting[2].w * v_color0.rgb;
        // Key light (indoors): u_modelLighting[3].xyz = direction * fraction. That fraction of the ambient arrives
        // from one direction instead, so form and normal-map detail show in rooms lit almost only by ambient (sprites
        // carry painted shading). Gain 2.2 brings a surface facing the camera back to about 1x the ambient, as on a
        // sprite (the flat term alone leaves vertical surfaces at 0.65x); lightLevel E is unchanged.
        float keyFraction = min(length(u_modelLighting[3].xyz), 0.9);
        // Display-space rooms (indoors) light models mostly by ambient, which a fully metallic texel would not receive
        // at all: keep a little of it, so metal reads dark rather than black where no light is near.
        float ambientMetallic = u_modelLighting[1].w > 0.5 ? min(metallic, 0.8) : metallic;
        shaded = color.rgb * (1.0 - ambientMetallic) * (1.0 - fresnel) * lightLevel * (1.0 - keyFraction)
            * (0.65 + 0.35 * max(normal.z, 0.0));
        if (keyFraction > 0.0)
        {
            // Diffuse only: a broad specular lobe from a camera-side light lays a pale sheen over the whole lit side.
            shaded += modelBrdf(normal, view, u_modelLighting[3].xyz / length(u_modelLighting[3].xyz), color.rgb,
                metallic, roughness, 0.0) * lightLevel * (keyFraction * 2.2);
        }
        // u_modelPbr.w scales specular: flat leaf cards seen edge-on would otherwise catch a near-white Fresnel sheen.
        // At zero (foliage) the sky reflection and specular lobes are skipped entirely. Negative: a specular mask, the
        // metallic-roughness red channel times -w (a merged head and body material with matte skin).
        float specularScale = u_modelPbr.w >= 0.0 ? u_modelPbr.w : -u_modelPbr.w * surface.r;
        // Specular occlusion (u_modelEdge.z: 1 = metallic-roughness red AO, 2 = COLOR_0 luminance over u_modelEdge.w):
        // creases and cavities keep their sky, sun and point-light specular out, rougher surfaces more so (Lagarde).
        if (u_modelEdge.z > 0.5)
        {
            float occlusion = u_modelEdge.z > 1.5
                ? clamp(dot(v_flowInfo.rgb, vec3(0.2126, 0.7152, 0.0722)) / u_modelEdge.w, 0.0, 1.0) : surface.r;
            specularScale *= clamp(pow(nv + occlusion, exp2(-16.0 * roughness - 1.0)) - 1.0 + occlusion, 0.0, 1.0);
        }
        if (specularScale > 0.0 && MODEL_PREPASSED == 0)
        {
            vec3 reflected = textureCubeLod(s_modelEnvironment, reflect(-view, normal),
                roughness * u_modelEnvironment.w).rgb;
            vec2 integrated = texture2D(s_modelEnvironmentBrdf, vec2(nv, roughness)).rg;
            shaded += reflected * u_modelEnvironment.rgb * v_color0.rgb * (f0 * integrated.x + integrated.y)
                * specularScale;
        }
        shaded += color.rgb * (1.0 - ambientMetallic) * v_texcoord1.rgb;
        lightLevel += v_texcoord1.rgb;
        vec3 sunDirection = modelNormalize(u_modelLighting[0].xyz);
        // Static leaves (translucent) look their shadow up a little toward the sun (4 % of the placed model's height,
        // at most 32 units): a crown's outer cards and its inner shell lie close together, and the sunlit outer layer
        // would shade itself.
        float shadowLift = u_modelPbr.z > 0.0 ? floor((v_texcoord1.w + 1.0) * 0.25) : 0.0;
        vec3 shadowPosition = v_worldPosition + u_sunShadowParams[3].xyz * shadowLift;
        vec3 sun = u_modelLighting[1].rgb * u_modelLighting[0].w * v_color0.a
            * sunShadowVisibility(shadowPosition, modelNormalize(v_worldNormal), 0.0);
        shaded += modelBrdf(normal, view, sunDirection, color.rgb, metallic, roughness, specularScale) * sun;
        if (u_modelPbr.z > 0.0)
        {
            // Light through thin leaves: some on the side facing away from the sun, most when looking into it.
            float into = max(dot(-view, sunDirection), 0.0);
            float through = u_modelPbr.z * (0.3 * (1.0 - max(dot(normal, sunDirection), 0.0)) + into * into * into * into);
            shaded += color.rgb * (1.0 - metallic) * sun * through;
        }
        lightLevel += sun;
        // Point lights: the view's clustered light grid (u_lightGrid mode 1 full, 2 highlights only), else the draw's
        // uniform list (u_modelLighting[3].w: count; negative = highlights only). Highlights only: static
        // decorations, whose placement light already carries the lights' diffuse share.
        // Highlights reflect the light itself, so they skip the display-space scaling by the light level below.
        vec3 highlights = vec3_splat(0.0);
        bool gridSpecularOnly = lightGridMode() > 1.5;
        // A matte surface in highlight-only mode takes nothing from the lights: skip the loop.
        if (lightGridMode() > 0.5 && !(gridSpecularOnly && specularScale <= 0.0))
        {
            vec2 range = lightGridCellRange(v_worldPosition);
            int first = int(range.x + 0.5);
            int count = int(range.y + 0.5);
            for (int i = 0; i < LIGHT_GRID_MAX_CELL_LIGHTS; ++i)
            {
                if (i >= count)
                {
                    break;
                }
                int index = lightGridLightIndex(first + i);
                // Indoors only the lights that reach the model's room through portals (v_sector, -1: any).
                if (!lightGridReaches(index, lightGridLightSource(index), vec2(v_sector, -1.0)))
                {
                    continue;
                }
                vec4 positionRadius;
                vec4 colorIntensity;
                lightGridLight(index, positionRadius, colorIntensity);
                modelPointLight(positionRadius, colorIntensity, v_worldPosition, normal, view, color.rgb, metallic,
                    roughness, specularScale, gridSpecularOnly, shaded, lightLevel, highlights);
            }
        }
        else if (lightGridMode() < 0.5)
        {
            int pointCount = int(abs(u_modelLighting[3].w));
            bool pointSpecularOnly = u_modelLighting[3].w < 0.0;
            for (int i = 0; i < 12; ++i)
            {
                if (i >= pointCount)
                {
                    break;
                }
                modelPointLight(u_modelPointPositions[i], u_modelPointColors[i], v_worldPosition, normal, view,
                    color.rgb, metallic, roughness, specularScale, pointSpecularOnly, shaded, lightLevel, highlights);
            }
        }
        if (u_modelLighting[1].w > 0.5)
        {
            // World faces and sprites multiply the sRGB texel by the unshaded light level E; linear shading of
            // albedo * E displays as about texel * E^(1/2.2), so scale by E^1.2 to match them in dim light.
            // Above E = 1 the linear response is kept: creature albedos are tuned for it in lit rooms.
            shaded *= pow(clamp(lightLevel, 0.0, 1.0), vec3_splat(1.2));
        }
        shaded += highlights;
        if (u_modelEdge.x > 0.0)
        {
            // Edge darkening (creatures): a soft contour like the sprites' dark rim. It follows the interpolated mesh
            // normal, not the normal map, and the band is at least ~1.5 pixels wide so distant creatures keep it.
            float facing = abs(dot(modelNormalize(v_worldNormal), view));
            float band = max(0.55, 1.5 * fwidth(facing));
            shaded *= 1.0 - u_modelEdge.x * (1.0 - smoothstep(0.0, band, facing));
        }
    }
    // v_flowInfo.a scales the emission: a static material's pulse, 1 otherwise.
    shaded += contour ? vec3_splat(0.0) : u_modelSurface.xyz * v_flowInfo.a + burnGlow;
    // An SDR shoulder preserves sub-0.8 values and hue while compressing specular peaks smoothly.
    float peak = max(max(shaded.r, shaded.g), shaded.b);
    float compressed = 0.8 + 0.2 * (1.0 - exp(-max(peak - 0.8, 0.0) / 0.2));
    if (u_modelMaterial[1].z < 0.5 && peak > 0.8)
    {
        shaded *= compressed / peak;
    }
    float distance = length(v_worldPosition - u_modelCamera.xyz);
    float fog = u_modelFog[1].w > 0.5
        ? clamp((distance - u_modelFog[2].x) / max(u_modelFog[2].y - u_modelFog[2].x, 1.0), 0.0, 1.0)
        : u_modelFog[1].x
            + (u_modelFog[1].y - u_modelFog[1].x) * modelSmoothstep(u_modelFog[2].x, u_modelFog[2].y, distance)
            + (1.0 - u_modelFog[1].y) * modelSmoothstep(u_modelFog[2].y, u_modelFog[2].z, distance);
    fog = skyFogRatio(max(fog, u_modelFog[1].z), v_worldPosition, distance, u_modelFog[2].z);
    vec3 fogColor = skyFogDisplayColor(fog, u_modelFog[0].rgb, v_worldPosition);
    vec3 displayColor = modelEncodeSrgb(shaded);
    // Creature hit flash (u_modelEdge.y, gameplay.melee_hit_flash): a brief mix towards warm white in display space,
    // as on sprites; not on the contour shell.
    if (u_modelEdge.y > 0.0 && !contour)
    {
        displayColor = mix(displayColor, vec3(1.0, 0.94, 0.86), u_modelEdge.y);
    }
    if (u_modelGlow.x > 0.0)
    {
        // Bloom glow pass (lighting plan, phase 7; ModelRenderer::setGlowView): what the surface emits, display
        // space, fading with the fog like an additive card. Cards (y = their weight) glow with their whole colour;
        // other surfaces with their emission (the material's, pulsed, and a burn's).
        vec3 emitted = u_modelGlow.y > 0.0 ? displayColor * u_modelGlow.y
            : modelEncodeSrgb(u_modelSurface.xyz * v_flowInfo.a + burnGlow);
        gl_FragColor = vec4(emitted * (1.0 - fog) * u_modelGlow.x, color.a);
        return;
    }
    // Additive glow (outline flag -1, static decorations): the fog fades it out instead of mixing in its colour.
    gl_FragColor = u_modelOutline.w < -0.5 ? vec4(displayColor * (1.0 - fog), color.a)
        : vec4(mix(displayColor, fogColor, fog), color.a);
}
