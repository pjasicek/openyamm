$input v_texcoord0, v_worldNormal, v_worldPosition, v_color0, v_texcoord1, v_flowInfo

#include "common.sh"
#include "sky_common.sh"
#include "world_clip.sh"
#include "sun_shadows.sh"

SAMPLER2D(s_modelTexture, 0);
SAMPLER2D(s_modelNormal, 1);
SAMPLER2D(s_modelMetallicRoughness, 2);
SAMPLERCUBE(s_modelEnvironment, 3);
SAMPLER2D(s_modelEnvironmentBrdf, 4);
SAMPLER2D(s_modelRegionMask, 8);
SAMPLER2D(s_modelRegionRamp, 9);
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

vec3 modelBrdf(vec3 normal, vec3 view, vec3 light, vec3 base, float metallic, float roughness, float specularScale)
{
    float nl = max(dot(normal, light), 0.0);
    vec3 f0 = mix(vec3_splat(0.04), base, metallic);
    if (specularScale <= 0.0)
    {
        // Diffuse only (foliage cards): no half-vector, distribution or geometry terms.
        return (1.0 - f0) * (1.0 - metallic) * base * nl;
    }
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
    vec3 fresnel = f0 + (1.0 - f0) * pow(1.0 - vh, 5.0);
    vec3 diffuse = (1.0 - fresnel) * (1.0 - metallic) * base / 3.14159265;
    vec3 specular = distribution * geometry * fresnel / max(4.0 * nl * nv, 0.0001) * specularScale;
    // Existing light intensities use unit diffuse irradiance, rather than radiance divided by pi.
    return (diffuse + specular) * (nl * 3.14159265);
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

float modelSmoothstep(float low, float high, float value)
{
    float amount = clamp((value - low) / max(high - low, 1.0), 0.0, 1.0);
    return amount * amount * (3.0 - 2.0 * amount);
}

void main()
{
    // Base textures are sRGB; the sampler decodes RGB, while factors and alpha stay linear.
    // v_flowInfo.rgb: glTF vertex colour (canopy occlusion on foliage), white on creatures.
    vec4 color = texture2D(s_modelTexture, v_texcoord0) * u_modelMaterial[0] * vec4(v_flowInfo.rgb, 1.0);
#if !MODEL_PREPASSED
    // Water reflections keep only what is above the water plane (zero plane elsewhere).
    clipWorldPosition(v_worldPosition);
    // MODEL_PREPASSED: the shaded pass after a depth prepass. Its equal-depth test already holds the alpha test and the
    // crossfade dither, and a shader without discard keeps the GPU's early depth rejection.
    if (u_modelMaterial[1].y > 0.5 && color.a < u_modelMaterial[1].x)
    {
        discard;
    }
    // Static LOD crossfade (v_texcoord1.w): (0, 1) = the new level appearing, (1, 2) = the old one leaving, with
    // complementary dither so the two always cover each pixel exactly once.
    if (v_texcoord1.w > 0.0)
    {
        float threshold = modelDither(gl_FragCoord.xy);
        bool leaving = v_texcoord1.w > 1.0;
        float progress = leaving ? v_texcoord1.w - 1.0 : v_texcoord1.w;
        if (leaving ? threshold < progress : threshold >= progress)
        {
            discard;
        }
    }
#endif
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
    if (u_modelOutline.w > 0.5)
    {
        gl_FragColor = vec4(u_modelOutline.rgb, 1.0);
        return;
    }
    vec3 shaded = color.rgb;
    if (u_modelMaterial[1].z < 0.5)
    {
        vec3 normal = modelNormalize(v_worldNormal);
        if (u_modelSurface.w >= 0.0)
        {
            vec3 dp1 = dFdx(v_worldPosition);
            vec3 dp2 = dFdy(v_worldPosition);
            vec2 duv1 = dFdx(v_texcoord0);
            vec2 duv2 = dFdy(v_texcoord0);
            vec3 p1 = cross(normal, dp1);
            vec3 p2 = cross(dp2, normal);
            vec3 tangent = p2 * duv1.x + p1 * duv2.x;
            vec3 bitangent = p2 * duv1.y + p1 * duv2.y;
            float inverseLength = inversesqrt(max(max(dot(tangent, tangent), dot(bitangent, bitangent)), 0.000001));
            // z is rebuilt from x and y: cooked normal maps are two-channel (BC5, EAC RG).
            vec2 mappedXy = texture2D(s_modelNormal, v_texcoord0).xy * 2.0 - 1.0;
            vec3 mapped = vec3(mappedXy * u_modelSurface.w, sqrt(max(1.0 - dot(mappedXy, mappedXy), 0.0)));
            normal = modelNormalize(tangent * inverseLength * mapped.x
                + bitangent * inverseLength * mapped.y + normal * mapped.z);
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
        vec3 fresnel = f0 + (max(vec3_splat(1.0 - roughness), f0) - f0) * pow(1.0 - nv, 5.0);
        // ponytail: upward probe fill uses a hemisphere; directional indirect probes if this loses needed contrast.
        // v_color0: per-placement ambient (rgb) and sun (a) scales; v_texcoord1: undirected point light.
        vec3 lightLevel = u_modelLighting[2].rgb * u_modelLighting[2].w * v_color0.rgb;
        // Key light (indoors): u_modelLighting[3].xyz = direction * fraction. That fraction of the ambient arrives
        // from one direction instead, so form and normal-map detail show in rooms lit almost only by ambient (sprites
        // carry painted shading). Gain 2.2 brings a surface facing the camera back to about 1x the ambient, as on a
        // sprite (the flat term alone leaves vertical surfaces at 0.65x); lightLevel E is unchanged.
        float keyFraction = min(length(u_modelLighting[3].xyz), 0.9);
        shaded = color.rgb * (1.0 - metallic) * (1.0 - fresnel) * lightLevel * (1.0 - keyFraction)
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
        if (specularScale > 0.0)
        {
            vec3 reflected = textureCubeLod(s_modelEnvironment, reflect(-view, normal),
                roughness * u_modelEnvironment.w).rgb;
            vec2 integrated = texture2D(s_modelEnvironmentBrdf, vec2(nv, roughness)).rg;
            shaded += reflected * u_modelEnvironment.rgb * v_color0.rgb * (f0 * integrated.x + integrated.y)
                * specularScale;
        }
        shaded += color.rgb * (1.0 - metallic) * v_texcoord1.rgb;
        lightLevel += v_texcoord1.rgb;
        vec3 sunDirection = modelNormalize(u_modelLighting[0].xyz);
        vec3 sun = u_modelLighting[1].rgb * u_modelLighting[0].w * v_color0.a
            * sunShadowVisibility(v_worldPosition, modelNormalize(v_worldNormal));
        shaded += modelBrdf(normal, view, sunDirection, color.rgb, metallic, roughness, specularScale) * sun;
        if (u_modelPbr.z > 0.0)
        {
            // Light through thin leaves: some on the side facing away from the sun, most when looking into it.
            float into = max(dot(-view, sunDirection), 0.0);
            float through = u_modelPbr.z * (0.3 * (1.0 - max(dot(normal, sunDirection), 0.0)) + into * into * into * into);
            shaded += color.rgb * (1.0 - metallic) * sun * through;
        }
        lightLevel += sun;
        for (int i = 0; i < 12; ++i)
        {
            if (i >= int(u_modelLighting[3].w))
            {
                break;
            }
            vec3 delta = u_modelPointPositions[i].xyz - v_worldPosition;
            float radius = max(u_modelPointPositions[i].w, 0.0001);
            float attenuation = max(1.0 - dot(delta, delta) / (radius * radius), 0.0);
            vec3 point = u_modelPointColors[i].rgb * u_modelPointColors[i].w * attenuation * attenuation;
            shaded += modelBrdf(normal, view, modelNormalize(delta), color.rgb, metallic, roughness, specularScale) * point;
            lightLevel += point;
        }
        if (u_modelLighting[1].w > 0.5)
        {
            // World faces and sprites multiply the sRGB texel by the unshaded light level E; linear shading of
            // albedo * E displays as about texel * E^(1/2.2), so scale by E^1.2 to match them in dim light.
            // Above E = 1 the linear response is kept: creature albedos are tuned for it in lit rooms.
            shaded *= pow(clamp(lightLevel, 0.0, 1.0), vec3_splat(1.2));
        }
    }
    // v_flowInfo.a scales the emission: a static material's pulse, 1 otherwise.
    shaded += u_modelSurface.xyz * v_flowInfo.a;
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
    gl_FragColor = vec4(mix(modelEncodeSrgb(shaded), fogColor, fog), color.a);
}
