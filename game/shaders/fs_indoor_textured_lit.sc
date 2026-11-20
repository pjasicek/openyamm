// INDOOR_TRANSLUCENT: a translucent face (devdocs/INDOOR_TRANSLUCENT_FACES.md), alpha-blended after the opaque
// scene: its lit colour times the tint, at the texture's alpha times the opacity.
// INDOOR_BAKED: a face of a map with baked lighting (devdocs/INDOOR_BAKED_LIGHTING.md) takes its static light from
// its lightmap page instead of the vertex bake and room ambient; the dynamic lights add on top as before.
// INDOOR_FOG: a map with scene fog (devdocs/INDOOR_FOG.md): the finished colour fades into the fog colour between two
// distances from the eye; sky faces stay clear. Only those maps load these programs. u_indoorFogMode selects MM9's
// fog (scene `model: lithtech`): the distance is the view depth, and the texture and the light fade separately.
// u_indoorDaylight: the scene daylight (devdocs/INDOOR_OPEN_SKY.md), taken by the faces whose v_faceInfo.z is 1
// (a face in a sector open to the sky); zero on every other map, where it adds nothing. A lightmapped face takes it
// from its lightmap's daylight page instead (INDOOR_BAKED, u_indoorBakedDaylight).
// v_gradientU, v_gradientV: the face's texture gradients for surface materials (SURFACE_MATERIALS,
// surface_material.sh); the vertex shaders always pass them, and bgfx links only matching varyings.
// INDOOR_TERRAIN: the terrain faces of an open-air BLV (IndoorTerrainMaterials, devdocs/INDOOR_OPEN_SKY.md "Terrain"):
// blended library ground materials (terrain_material_layers.sh) by world position instead of the face texture, lit
// with the smooth ground normal the vertices carry in a_tangent (v_gradientU); v_texcoord0 = (steepness, meadow).
// INDOOR_DEPTH_ONLY: the terrain's depth pre-pass, which writes no colour.
// v_lightmapUv: read only by INDOOR_BAKED, but declared by every variant: shaderc keeps the $input lines of both
// branches of an #if and takes the last, so Metal and SPIR-V lost it; vs_indoor_textured_lit passes zero.
$input v_texcoord0, v_worldPosition, v_texcoord1, v_screenspace, v_flowInfo, v_color0, v_lightmapUv, v_gradientU, v_gradientV, v_faceInfo

#include "common.sh"
#include "world_clip.sh"
#include "light_grid.sh"
#include "sky_common.sh"
#if SURFACE_MATERIALS
#include "surface_material.sh"
#endif
#if INDOOR_TERRAIN
#include "terrain_material_layers.sh"
// The terrain grass's colour (TerrainDecorationRenderer::foliageMap, as the outdoor terrain's stage 1).
SAMPLER2D(s_terrainFoliage, 12);
#endif

SAMPLER2D(s_texColor, 0);
#if INDOOR_BAKED
// RGBM4 lighting in the renderer's units (the texture colour's multiplier).
SAMPLER2D(s_texLightmap, 1);
// A version 2 bake's daylight share of the same page (devdocs/INDOOR_BAKED_LIGHTING.md "Daylight pages").
SAMPLER2D(s_texDaylightmap, 2);
// [0].rgb: the bake's ambient level, w = 1 when s_texDaylightmap holds the page's daylight; [1].rgb, [2].rgb: the
// scales of its ambient and sun shares this hour (1 at noon) on faces open to the sky (indoorBakedDaylightScale).
uniform vec4 u_indoorBakedDaylight[3];
#endif

uniform vec4 u_indoorLightPositions[12];
uniform vec4 u_indoorLightColors[12];
uniform vec4 u_indoorLightParams;
// x = 1 when the faces take their dynamic lights from the light grid (only for the sectors those reach:
// v_faceInfo.xy, the face's sector and back sector, -1 for none).
uniform vec4 u_indoorFaceGrid;
uniform vec4 u_secretPulseParams;
uniform vec4 u_indoorSkyParams;
uniform vec4 u_indoorSkyProjectionParams;
// [0].rgb: the sky's ambient, [0].w: the open air's lights' scale on the vertex light (1: as baked), [1].rgb: the sun,
// [2].xyz: toward the sun, [2].w: how steeply faces take it.
uniform vec4 u_indoorDaylight[3];
#if INDOOR_TRANSLUCENT
// rgb: tint, a: opacity.
uniform vec4 u_indoorTranslucency;
#endif
#if INDOOR_FOG
// rgb: fog colour; x, y: near and far distance.
uniform vec4 u_fogColor;
uniform vec4 u_fogDistances;
// x = 1: the distance is the view depth; y = 1: the light fades into u_indoorFogLight.rgb apart from the texture.
// u_skyFog (sky_common.sh): zero (flat fog, unchanged) except with an open sky's outdoor view
// (devdocs/INDOOR_OPEN_SKY.md "Outdoor view"), where the sky's haze and its colour in each direction are added as on
// an outdoor map's faces.
uniform vec4 u_indoorFogMode;
uniform vec4 u_indoorFogLight;
#endif

// The dynamic lights' response to the face's angle. Faces turned toward the light keep their old (angle-free) light;
// grazing faces lose only a little (a torch-lit frame is at most about 5 % darker than without N.L), and the
// response fades out just before the face turns away, so the far side of a wall takes none. Static lights are in the
// vertex bake.
float indoorFaceFacing(vec3 normal, vec3 toLight)
{
    float facing = clamp(dot(normal, toLight) * inversesqrt(max(dot(toLight, toLight), 0.0001)), 0.0, 1.0);
    return smoothstep(0.0, 0.08, facing) * (0.86 + 0.14 * sqrt(facing));
}

// The vertex bake of the static lights: rgb, of which 1 - a is the open air's lights' share (MM9's lights over its
// regions, devdocs/INDOOR_OPEN_SKY.md "Daylight"), which follows the hour; a is 1 on every other map.
vec3 indoorVertexLight(vec4 color)
{
    return color.rgb * (1.0 - (1.0 - color.a) * (1.0 - u_indoorDaylight[0].w));
}

// The static light: the room ambient plus the vertex bake of the static lights, or the face's lightmap (with its
// daylight page: as baked, or by the hour on a face open to the sky, daylit 1). The helpers take the varyings from
// main: Metal and HLSL see them only there.
vec3 indoorStaticLight(vec3 vertexLighting, vec2 lightmapUv, float daylit)
{
#if INDOOR_BAKED
    vec4 baked = texture2D(s_texLightmap, lightmapUv);
    vec3 light = baked.rgb * (baked.a * 4.0);
    if (u_indoorBakedDaylight[0].w > 0.5)
    {
        vec4 day = texture2D(s_texDaylightmap, lightmapUv);
        vec3 daylight = day.rgb * (day.a * 4.0);
        vec3 sky = min(daylight, u_indoorBakedDaylight[0].rgb);
        vec3 scaled = sky * u_indoorBakedDaylight[1].rgb + (daylight - sky) * u_indoorBakedDaylight[2].rgb;
        light += mix(daylight, scaled, daylit);
    }
    return light;
#else
    return u_indoorLightParams.yzw + vertexLighting * 2.0;
#endif
}

// The daylight on a face of a sector open to the sky: the sky's ambient and the sun by the face's angle (its gain
// steepens the response), at most 1 (as MM9's lightmaps clamp it).
vec3 indoorDaylight(vec3 normal, float daylit)
{
#if INDOOR_BAKED
    // A lightmapped face's daylight is in its lightmap (indoorStaticLight).
    return vec3_splat(0.0);
#else
    float facing = clamp(dot(normal, u_indoorDaylight[2].xyz) * u_indoorDaylight[2].w, 0.0, 1.0);
    return min(u_indoorDaylight[0].rgb + u_indoorDaylight[1].rgb * facing, vec3_splat(1.0)) * daylit;
#endif
}

// BLV faces are flat: the normal from the position derivatives, turned toward the camera.
vec3 indoorFlatNormal(vec3 worldPosition)
{
    vec3 normal = cross(dFdx(worldPosition), dFdy(worldPosition));
    normal *= inversesqrt(max(dot(normal, normal), 0.000001));
    if (dot(normal, mul(u_invView, vec4(0.0, 0.0, 0.0, 1.0)).xyz - worldPosition) < 0.0)
    {
        normal = -normal;
    }
    return normal;
}

vec3 getIndoorLighting(vec3 worldPosition, vec3 normal, vec3 vertexLighting, vec2 lightmapUv, vec3 faceInfo)
{
    vec3 lighting = indoorStaticLight(vertexLighting, lightmapUv, faceInfo.z);
    lighting += indoorDaylight(normal, faceInfo.z);

    if (u_indoorFaceGrid.x > 0.5)
    {
        // The view's light grid: the dynamic lights that reach the face's sectors through portals.
        vec2 range = lightGridCellRange(worldPosition);
        int first = int(range.x + 0.5);
        int count = int(range.y + 0.5);
        for (int i = 0; i < LIGHT_GRID_MAX_CELL_LIGHTS; ++i)
        {
            if (i >= count)
            {
                break;
            }
            int index = lightGridLightIndex(first + i);
            vec3 source = lightGridLightSource(index);
            // Dynamic lights are binned first, so the first static one ends them.
            if (source.y < 0.5)
            {
                break;
            }
            if (!lightGridReaches(index, source, faceInfo.xy))
            {
                continue;
            }
            vec4 positionRadius;
            vec4 colorIntensity;
            lightGridLight(index, positionRadius, colorIntensity);
            lighting += colorIntensity.rgb * (colorIntensity.a * lightGridAttenuation(positionRadius, worldPosition)
                * indoorFaceFacing(normal, positionRadius.xyz - worldPosition));
        }
    }
    else
    {
        // The draw's own list (water reflections, blood splats).
        for (int i = 0; i < 12; ++i)
        {
            if (float(i) >= u_indoorLightParams.x)
            {
                break;
            }
            lighting += u_indoorLightColors[i].rgb * (u_indoorLightColors[i].w
                * lightGridAttenuation(u_indoorLightPositions[i], worldPosition)
                * indoorFaceFacing(normal, u_indoorLightPositions[i].xyz - worldPosition));
        }
    }

    return clamp(lighting, vec3(0.0, 0.0, 0.0), vec3(2.0, 2.0, 2.0));
}

#if SURFACE_MATERIALS
// A face with material maps: the static (baked vertex) light darkened by occlusion, the dynamic lights relit for the
// detailed normal with their highlights, the room's light reflected by smooth and metal surfaces, and glow (glass is
// lit from outside, so it glows at any hour). Display-space result like getIndoorLighting's product.
vec3 surfaceIndoorColor(vec3 displayColor, SurfacePoint material, vec3 faceNormal, vec3 toCamera, float distance,
    vec3 vertexLighting, vec3 worldPosition, vec2 lightmapUv, vec3 faceInfo)
{
    vec3 view = toCamera / max(distance, 0.001);
    vec3 albedo = pow(max(displayColor, vec3_splat(0.0)), vec3_splat(2.2));
    vec3 f0 = mix(vec3_splat(0.04), albedo, material.metal);
    vec3 room = indoorStaticLight(vertexLighting, lightmapUv, faceInfo.z) + indoorDaylight(material.normal, faceInfo.z);
    vec3 lighting = room * material.occlusion;
    vec3 specular = vec3_splat(0.0);
    if (u_indoorFaceGrid.x > 0.5)
    {
        vec3 diffuse;
        vec3 highlights;
        surfacePointLights(worldPosition, material, faceNormal, view, f0, faceInfo.xy, true, diffuse,
            highlights);
        lighting += diffuse;
        specular += highlights;
    }
    else
    {
        for (int i = 0; i < 12; ++i)
        {
            if (float(i) >= u_indoorLightParams.x)
            {
                break;
            }
            vec3 toLight = u_indoorLightPositions[i].xyz - worldPosition;
            vec3 direction = toLight * inversesqrt(max(dot(toLight, toLight), 0.0001));
            vec3 light = u_indoorLightColors[i].rgb * (u_indoorLightColors[i].w
                * lightGridAttenuation(u_indoorLightPositions[i], worldPosition)
                * indoorFaceFacing(faceNormal, toLight));
            lighting += light * surfaceRelight(material.normal, faceNormal, direction);
            specular += light * surfaceSpecular(material.normal, view, direction, material.roughness, f0);
        }
    }
    vec3 linearLighting = pow(clamp(lighting, vec3_splat(0.0), vec3_splat(2.0)), vec3_splat(2.2));
    vec3 color = albedo * (1.0 - SURFACE_METAL_DIFFUSE_LOSS * material.metal) * linearLighting
        + specular * (SURFACE_PI * u_surfaceMaterial.z * material.occlusion);
    float nv = max(dot(material.normal, view), 0.001);
    float specularOcclusion = clamp(pow(nv + material.occlusion, exp2(-16.0 * material.roughness - 1.0)) - 1.0
        + material.occlusion, 0.0, 1.0);
    // The room as an environment: its own light, dimmer toward the floor.
    vec3 reflected = reflect(-view, material.normal);
    vec3 roomRadiance = pow(clamp(room, vec3_splat(0.0), vec3_splat(2.0)), vec3_splat(2.2))
        * (reflected.z >= 0.0 ? 0.45 : 0.25);
    // Only smooth and metal surfaces show the room: the painted colours already hold rough surfaces' faint sheen.
    float reflection = max(material.metal, 1.0 - smoothstep(0.3, 0.7, material.roughness));
    roomRadiance = surfaceTracedReflection(roomRadiance, worldPosition, reflected, faceNormal, material.roughness,
        reflection);
    color += roomRadiance * surfaceEnvironmentResponse(f0, material.roughness, nv)
        * (specularOcclusion * reflection * u_surfaceMaterial.w);
    color += surfaceGlowColor(albedo) * (material.glow * SURFACE_GLOW_SCALE);
    return pow(max(color, vec3_splat(0.0)), vec3_splat(1.0 / 2.2));
}
#endif

void main()
{
#if INDOOR_DEPTH_ONLY
    // The terrain's depth pre-pass in the main view (IndoorRenderer::submitMainViewFaces): depth alone, written with
    // the colour masked, so the shaded pass after it runs once per pixel. The main view has no clip plane.
    gl_FragColor = vec4_splat(0.0);
#else
    clipWorldPosition(v_worldPosition);
    // v_texcoord1.x: 1 for a secret face, plus 2 for a face of the scene's `opaque_faces`; rounded first, as the
    // interpolated slot sits a hair off its whole value (an unrounded test speckled opaque faces with the pulse).
    float faceFlags = floor(v_texcoord1.x + 0.5);
#if INDOOR_TERRAIN
    vec3 position = v_worldPosition;
    // The triangle's own normal.z (the ground layers' bank test) from the derivatives, taken before any branch.
    vec3 flatNormal = cross(dFdx(position), dFdy(position));
    float faceUp = abs(flatNormal.z) * inversesqrt(max(dot(flatNormal, flatNormal), 1.0e-12));
    vec3 groundNormal = normalize(v_gradientU);
    // The weights cover the 65 536-unit map frame from its north-west corner, as on an outdoor map.
    vec2 mapUv = vec2(position.x + 32768.0, 32768.0 - position.y) / 65536.0;
    vec4 weights0 = texture2DArray(s_terrainWeights, vec3(mapUv, 0.0));
    vec4 weights1 = texture2DArray(s_terrainWeights, vec3(mapUv, 1.0));
    vec4 macroSample = texture2D(s_terrainMacro, position.xy / 16384.0);
    float meadow = clamp(v_texcoord0.y + (macroSample.g - 0.5) * 0.5 + (macroSample.a - 0.5) * 0.3, -1.0, 1.0);
    vec3 albedo;
    vec3 shadingNormal;
    float occlusion;
    float roughness;
    float layerSpecular;
    float layerWetSheen;
    vec3 glow;
    float pool;
    blendTerrainMaterial(weights0, weights1, position, groundNormal, faceUp, v_texcoord0.x, macroSample, meadow, 0.0,
        -1.0, albedo, shadingNormal, occlusion, roughness, layerSpecular, layerWetSheen, glow, pool);
    if (u_terrainFoliage[0].x > 0.0)
    {
        albedo = terrainFoliageAlbedo(albedo, texture2D(s_terrainFoliage, mapUv), position, skyCameraPosition(),
            groundNormal);
    }
    vec4 textureColor = vec4(albedo, 1.0);
    vec3 faceLighting = getIndoorLighting(v_worldPosition, shadingNormal, indoorVertexLight(v_color0), v_lightmapUv,
        v_faceInfo) * occlusion;
    vec3 color = albedo * faceLighting + glow;
#if INDOOR_FOG
    vec3 fogLight = faceLighting;
#endif
#else
    vec2 texcoord = v_texcoord0;

    if (v_flowInfo.w < -1.5)
    {
        float screenY = u_viewRect.w - gl_FragCoord.y;
        float xDistance = (u_indoorSkyProjectionParams.x - gl_FragCoord.x) * u_indoorSkyProjectionParams.z;
        float yDistance = (u_indoorSkyProjectionParams.y - screenY) * u_indoorSkyProjectionParams.z;
        float cosYaw = cos(u_indoorSkyParams.z);
        float sinYaw = sin(u_indoorSkyParams.z);
        float oePitch = -u_indoorSkyParams.w;
        float cosPitch = cos(oePitch);
        float sinPitch = sin(oePitch);
        float skyLeft = (-sinYaw * xDistance) + (cosYaw * sinPitch * yDistance) + (cosYaw * cosPitch);
        float skyFront = (cosYaw * xDistance) + (sinYaw * sinPitch * yDistance) + (sinYaw * cosPitch);
        float v18x = -sin((-oePitch) + u_indoorSkyProjectionParams.w);
        float v18z = -cos(oePitch + u_indoorSkyProjectionParams.w);
        float topProjection = min(v18x + v18z * yDistance, -0.0000001);
        float skyDepth = -512.0 / topProjection;
        float scrollPixels = (1000.0 / 64.0) * 0.25 * u_secretPulseParams.y;
        texcoord.xy = vec2(
            (scrollPixels + skyLeft * skyDepth / 16.0) * v_flowInfo.x,
            (scrollPixels + skyFront * skyDepth / 16.0) * v_flowInfo.y);
    }
    else
    {
        texcoord.xy += v_flowInfo.xy * u_secretPulseParams.y;

        if (v_flowInfo.w < -0.5)
        {
            texcoord.xy += u_indoorSkyParams.xy;
        }
    }

    if (v_flowInfo.z > 0.5 || v_flowInfo.w > 0.5)
    {
        float pongPhase = sin(mod(u_secretPulseParams.y, 8.0) * 6.2831853 / 8.0);
        float swirlPhase = mod(u_secretPulseParams.y, 5.0) * 6.2831853 / 5.0;
        float ripplePhase = mod(u_secretPulseParams.y, 2.0) * 6.2831853 / 2.0;

        vec2 delta = vec2(0.0, 0.0);
        delta.x += pongPhase * 0.01 * sin(texcoord.x * 6.2831853);
        delta.y += pongPhase * 0.01 * sin(texcoord.y * 6.2831853);
        delta.x += 0.01 * sin(swirlPhase + texcoord.y * 6.2831853);
        delta.y += 0.01 * cos(swirlPhase + texcoord.x * 6.2831853);
        delta.x -= 0.005 * cos(ripplePhase + (texcoord.y + delta.y) * 6.2831853 * 24.0);
        texcoord += delta;
    }

#if SURFACE_MATERIALS
    vec3 toCamera = mul(u_invView, vec4(0.0, 0.0, 0.0, 1.0)).xyz - v_worldPosition;
    float cameraDistance = length(toCamera);
    vec3 faceNormal = surfaceFlatNormal(v_worldPosition, toCamera);
    vec3 gradientU = v_gradientU;
    vec3 gradientV = v_gradientV;
    texcoord = surfaceParallax(texcoord, 0.0, 1.0, toCamera, cameraDistance, faceNormal, gradientU, gradientV);
    SurfacePoint material = surfacePoint(texture2D(s_surfaceNormal, texcoord), texture2D(s_surfaceDetail, texcoord),
        faceNormal, gradientU, gradientV, u_surfaceMaterial.y);
#endif
    vec4 textureColor = texture2D(s_texColor, texcoord);

    // A face of the scene's `opaque_faces`: its texture's alpha is no cut-out (MM9's window glass without its
    // Translucent flag, devdocs/INDOOR_TRANSLUCENT_FACES.md).
    if (faceFlags > 1.5)
    {
        textureColor.a = 1.0;
    }
    else if (textureColor.a <= 0.001)
    {
        discard;
    }

#if SURFACE_MATERIALS
    vec3 color = surfaceIndoorColor(textureColor.rgb, material, faceNormal, toCamera, cameraDistance,
        indoorVertexLight(v_color0), v_worldPosition, v_lightmapUv, v_faceInfo);
#if INDOOR_FOG
    // The light MM9's fog fades apart from the texture: the room's (static and daylight).
    vec3 fogLight = indoorStaticLight(indoorVertexLight(v_color0), v_lightmapUv, v_faceInfo.z)
        + indoorDaylight(faceNormal, v_faceInfo.z);
#endif
#else
    vec3 faceLighting = getIndoorLighting(v_worldPosition, indoorFlatNormal(v_worldPosition),
        indoorVertexLight(v_color0), v_lightmapUv, v_faceInfo);
    vec3 color = textureColor.rgb * faceLighting;
#if INDOOR_FOG
    vec3 fogLight = faceLighting;
#endif
#endif
#endif

    if (mod(faceFlags, 2.0) > 0.5 && u_secretPulseParams.x > 0.5)
    {
        float pulse = 0.5 + 0.5 * sin(u_secretPulseParams.y * 4.0);
        vec3 secretTint = color * vec3(1.0, pulse, pulse);
        color = secretTint;
    }

#if INDOOR_TRANSLUCENT
    color *= u_indoorTranslucency.rgb;
#endif
#if INDOOR_FOG
    if (v_flowInfo.w >= -1.5)
    {
        float fogDistance = u_indoorFogMode.x > 0.5 ? abs(mul(u_view, vec4(v_worldPosition, 1.0)).z)
            : length(mul(u_invView, vec4(0.0, 0.0, 0.0, 1.0)).xyz - v_worldPosition);
        float fogAmount = clamp((fogDistance - u_fogDistances.x) / max(u_fogDistances.y - u_fogDistances.x, 1.0),
            0.0, 1.0);
        if (u_indoorFogMode.y > 0.5)
        {
            // MM9's two passes: the texture fades into the fog colour, its light into the lightmap pass's.
            vec3 fadedLight = max(fogLight, vec3_splat(0.001));
            color = mix(color / fadedLight, u_fogColor.rgb, fogAmount)
                * mix(fadedLight, u_indoorFogLight.rgb, fogAmount);
        }
        else
        {
            fogAmount = skyFogRatio(fogAmount, v_worldPosition, fogDistance, u_fogDistances.y);
            color = mix(color, skyFogDisplayColor(fogAmount, u_fogColor.rgb, v_worldPosition), fogAmount);
        }
        // The map's mist (scene `mist`, mist.sh) lies over the fogged colour.
        color = mistApply(color, v_worldPosition);
    }
#endif

#if INDOOR_TRANSLUCENT
    gl_FragColor = vec4(color, textureColor.a * u_indoorTranslucency.a);
#else
    gl_FragColor = vec4(color, textureColor.a);
#endif
#endif // !INDOOR_DEPTH_ONLY
}
