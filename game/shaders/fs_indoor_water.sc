$input v_worldPosition, v_worldNormal, v_texcoord0, v_texcoord1, v_color0

#include "common.sh"
#include "water_surface.sh"
#include "liquid_surface.sh"
#include "world_clip.sh"

uniform vec4 u_indoorLightPositions[12];
uniform vec4 u_indoorLightColors[12];
uniform vec4 u_indoorLightParams;
#if INDOOR_FOG
// A map with scene fog (devdocs/INDOOR_FOG.md). rgb: fog colour; x, y: near and far distance.
uniform vec4 u_fogColor;
uniform vec4 u_fogDistances;
#endif

void main()
{
    clipWorldPosition(v_worldPosition);
    vec3 baseNormal = normalize(v_worldNormal);
    // Project waves onto the face itself, including vertical flowing water.
    vec3 tangent = abs(baseNormal.z) > 0.99 ? vec3(1.0, 0.0, 0.0)
        : normalize(cross(vec3(0.0, 0.0, 1.0), baseNormal));
    vec3 bitangent = cross(baseNormal, tangent);
    vec2 faceXy = vec2(dot(v_worldPosition, tangent), dot(v_worldPosition, bitangent));
    vec2 uv = faceXy / 768.0;
    uv += v_texcoord0 * u_waterParams.x;
    float falling = dot(v_texcoord0, v_texcoord0) > 0.000001 ? 1.0 - abs(baseNormal.z) : 0.0;
    bool lava = v_texcoord1.z > 1.5;
    bool tar = !lava && v_texcoord1.z > 0.5;
    bool floorFace = abs(baseNormal.z) >= 0.99;
    if (falling > 0.01)
    {
        uv *= vec2(4.0, 0.5);
    }
    else if (!floorFace)
    {
        uv *= 3.0;
    }
    else if (tar)
    {
        // Tar heaves in broad, slow, low swells.
        uv *= 0.5;
    }
    vec3 normal = waterWaveNormal(uv, baseNormal, tangent, bitangent, tar ? 0.26 : 0.95);
    if (tar && floorFace)
    {
        vec3 bubble = tarBubble(v_worldPosition.xy, u_waterParams.x);
        normal = normalize(normal - (tangent * bubble.x + bitangent * bubble.y));
    }
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
            float specular = max(dot(normal, halfDirection * inversesqrt(halfLength)), 0.0);
            // Tar's glossy skin gives a tighter, brighter glint.
            float highlight = tar ? pow(specular, 220.0) * 1.4 : pow(specular, 96.0);
            highlights += radiance * highlight * incidence;
        }
    }
    vec3 illumination = clamp(lighting, vec3_splat(0.0), vec3_splat(2.0));
    if (lava)
    {
        // Self-lit whatever the room light. A face's authored flow (water uv units per second) carries the lava.
        // Dungeon pools are small: a finer pattern than outdoor lava fields.
        vec2 lavaUv = faceXy / 900.0;
        if (falling > 0.01)
        {
            lavaUv *= vec2(1.5, 0.5);
        }
        float heat = lavaHeat(lavaUv, v_texcoord0 * (768.0 / 900.0 * u_waterParams.x), v_worldPosition.xy, floorFace,
            u_waterParams.x);
        gl_FragColor = vec4(lavaColor(heat, v_color0.rgb), 1.0);
        return;
    }
    if (!tar && floorFace && dot(baseNormal, u_cameraPosition.xyz - v_worldPosition) < 0.0)
    {
        // A swimmable volume's top seen from below (its faces are two-sided): no planar reflection, which is built
        // for the view from above. Within Snell's window, about 49 degrees round the vertical, the daylight comes
        // through, brighter straight up and rippling with the waves, and the world above shows in it; outside it the
        // surface partly mirrors the water body. With the eye under water the renderer draws every liquid, the opaque deep
        // sea too, after the sky, so there is a world behind the window.
        float window = smoothstep(0.6, 0.74, dot(normal, viewDirection));
        vec3 light = max(illumination, vec3_splat(0.35));
        vec3 under = v_color0.rgb * light + vec3(0.42, 0.6, 0.66) * light * (window * window) + highlights * 0.5;
        // MM9's surface is evenly see-through from below: the mirror outside the window is only partly opaque.
        float underAlpha = mix(0.6, 0.22, window * window);
#if INDOOR_FOG
        under = mix(under, u_fogColor.rgb, clamp((length(v_worldPosition - u_cameraPosition.xyz) - u_fogDistances.x)
            / max(u_fogDistances.y - u_fogDistances.x, 1.0), 0.0, 1.0));
#endif
        gl_FragColor = vec4(under, underAlpha);
        return;
    }
    vec3 tint = v_color0.rgb;
    if (u_waterParams.y < 0.5 && !tar)
    {
        // Waves still scatter room light on walls and pools without a planar reflection.
        tint = mix(tint, vec3(0.35, 0.55, 0.65), waveScatter);
    }
    vec3 waterColor = tint * illumination;
    // A dungeon has no daylight sky response; unreflected pools retain their room illumination.
    // Stronger pond ripples still fit the existing reflection guard band and scissor budget.
    vec2 distortion = clamp(normal.xy * 0.05, vec2_splat(-0.014), vec2_splat(0.014));
    vec3 reflected = waterReflection(v_worldPosition, distortion, waterColor);
    // Glossy tar reflects a little more head-on than water does.
    float fresnel = waterFresnel(normal, viewDirection);
    float reflectance = tar ? 0.07 + 0.93 * fresnel : fresnel;
    vec3 color = mix(waterColor, reflected, reflectance) + highlights;
    // A see-through liquid (liquids.yml opacity, the tint's alpha; opaque ones keep exactly 1) blends over its bed:
    // the body covers it at that opacity, the reflection and the highlights lie over it whole, so the surface turns
    // mirror-like at grazing angles. The colour is divided by the coverage the blend multiplies it with.
    float alpha = 1.0;
    if (v_color0.a < 0.998)
    {
        // Rippled coverage, as MM9's water sprites (their alpha a caustic network over a thin tint): the waves'
        // steep rings draw denser and lighter, the more so the clearer the liquid; the mean stays its opacity. A
        // thin body is lit at least as much as it is clear, as MM9 draws those sprites unlit: in a dark room the bed
        // shows dimly through bright ripples instead of the water vanishing into it.
        float clarity = 1.0 - v_color0.a;
        float ripple = smoothstep(0.2, 0.64, waveScatter);
        float body = min(v_color0.a * mix(1.0, 0.48 + 1.9 * ripple, clarity), 1.0);
        vec3 bodyColor = mix(tint, mix(tint, vec3_splat(1.0), 0.35), ripple * clarity)
            * max(illumination, vec3_splat(clarity));
        alpha = body + (1.0 - body) * reflectance;
        color = (bodyColor * (body * (1.0 - reflectance)) + reflected * reflectance + highlights) / alpha;
    }
    if (falling > 0.01 && !tar)
    {
        float foam = waterFlowFoam(uv, falling);
        color = mix(color, vec3(0.85, 0.92, 1.0) * illumination, foam);
        alpha += (1.0 - alpha) * foam;
    }
#if WATER_MOVEMENT_RIPPLES
    color += vec3(0.85, 0.92, 1.0) * movementSheen / alpha;
#endif
#if INDOOR_FOG
    color = mix(color, u_fogColor.rgb, clamp((length(v_worldPosition - u_cameraPosition.xyz) - u_fogDistances.x)
        / max(u_fogDistances.y - u_fogDistances.x, 1.0), 0.0, 1.0));
#endif
    gl_FragColor = vec4(color, alpha);
}
