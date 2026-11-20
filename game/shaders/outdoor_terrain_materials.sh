// The outdoor terrain: blended ground materials on the smoothed terrain mesh (OutdoorTerrainMaterials).
// Weights cover the 128x128 cell map; the two strongest layers blend by height, each sampled twice with a rotated
// second projection to hide its repeat. The liquid renderer draws the liquid cells; liquid edge cells keep the
// ground only where their native coverage mask leaves some.
// TERRAIN_DEPTH_ONLY: the main view's depth pre-pass (OutdoorRenderer::submitTerrainMaterials): no colour, and it
// leaves out exactly the pixels the shaded programs cut, so the shaded pass after it runs once per pixel.
#include "common.sh"
#include "world_clip.sh"
#include "terrain_material_layers.sh"

// The seabed's caustics: layer 0 the main Voronoi web, layer 1 a finer faint one (tools/terrain_materials.py
// caustics).
SAMPLER2DARRAY(s_terrainCaustics, 0);
// The liquid edge coverage masks (WaterRenderer), one layer per raw tile id: 1 where the liquid shows.
SAMPLER2DARRAY(s_texWaterCoverage, 4);
SAMPLER2D(s_terrainCells, 12);
// Native triangle normals at the terrain lightmap texels, filtered like the bake.
SAMPLER2D(s_terrainBakedNormals, 13);
// Signed distance to the waterline: 128 + distance / range * 127, positive on land.
SAMPLER2D(s_terrainShore, 15);
// The grass decorations' colour (encodeTerrainFoliageMap): rgb = average tuft colour, a = optical depth of the
// grass cards / 4.
SAMPLER2D(s_terrainFoliage, 1);

// xyz = direction toward the baked sun, w = 1 when the bake's direct-only sun page is bound at stage 5.
uniform vec4 u_terrainMaterialLight;
// x = waterline distance range, y = 1 when shores have a seabed under depth-faded water, z = waterline distance
// under the water past which the seabed is plain (one sample of layer w, no detail normals or relighting).
uniform vec4 u_terrainShore;

#if BAKED_SOURCES
SAMPLER2D(s_texLightmap, 2);
uniform vec4 u_bakedTerrainBounds;
#include "outdoor_baked_lighting.sh"
#if !SUN_SHADOWS
SAMPLER2D(s_texBakedSunDirect, 5);
#endif
#elif SUN_SHADOWS
#include "sun_shadows.sh"
#endif

#include "outdoor_sunlight.sh"

uniform vec4 u_cameraPosition;
uniform vec4 u_secretPulseParams;

// Dynamic lights from the view's light grid (stage 11).
#define OUTDOOR_LIGHT_GRID 1
#include "outdoor_lighting.sh"
#include "sky_common.sh"
#include "weather_wetness.sh"

// Restrained specular (lighting plan, phase 6): the GGX highlight of one light for a dielectric surface (F0 0.04),
// N.L included. Rough materials (grass, dirt) barely show it; smooth rock and wet ground glint.
float terrainSpecular(vec3 normal, vec3 toCamera, vec3 toLight, float roughness)
{
    float nl = dot(normal, toLight);
    if (nl <= 0.0)
    {
        return 0.0;
    }
    vec3 halfVector = normalize(toCamera + toLight);
    float nh = max(dot(normal, halfVector), 0.0);
    float nv = max(dot(normal, toCamera), 0.001);
    float vh = max(dot(toCamera, halfVector), 0.0);
    float alpha = max(roughness * roughness, 0.02);
    float alpha2 = alpha * alpha;
    float denominator = nh * nh * (alpha2 - 1.0) + 1.0;
    float distribution = alpha2 / (3.14159265 * denominator * denominator);
    float k = alpha * 0.5;
    float visibility = 0.25 / ((nl * (1.0 - k) + k) * (nv * (1.0 - k) + k));
    // max(): pow() of a negative base is NaN on some GPUs, and vh rounds above 1 with the light at the camera.
    float fresnel = 0.04 + 0.96 * pow(max(1.0 - vh, 0.0), 5.0);
    return distribution * visibility * fresnel * nl;
}

// The specular light (linear) of the grid's dynamic lights at the point.
vec3 terrainPointSpecular(vec3 position, vec3 normal, vec3 toCamera, float roughness)
{
    vec3 specular = vec3_splat(0.0);
    if (lightGridMode() < 0.5)
    {
        return specular;
    }
    vec2 range = lightGridCellRange(position);
    int first = int(range.x + 0.5);
    int count = int(range.y + 0.5);
    for (int i = 0; i < LIGHT_GRID_MAX_CELL_LIGHTS; ++i)
    {
        if (i >= count)
        {
            break;
        }
        int index = lightGridLightIndex(first + i);
        if (lightGridLightSource(index).y < 0.5)
        {
            break;
        }
        vec4 positionRadius;
        vec4 colorIntensity;
        lightGridLight(index, positionRadius, colorIntensity);
        vec3 toLight = positionRadius.xyz - position;
        specular += colorIntensity.rgb * (colorIntensity.a * lightGridAttenuation(positionRadius, position)
            * terrainSpecular(normal, toCamera, normalize(toLight), roughness));
    }
    return specular;
}

// Wet sand along the waterline and caustics in the shallows; shore is the signed waterline distance.
vec3 shoreAlbedo(vec3 albedo, vec3 position, float shore)
{
    // Damp sand along the waterline, darker and cooler under the water.
    albedo *= mix(vec3_splat(1.0), vec3(0.72, 0.74, 0.78), 1.0 - smoothstep(0.0, 60.0, shore));
    // Caustics: a web of light whose lines bend and drift with the waves, over a faint finer web drifting the
    // other way. Only in the shallows: everywhere else (all the land) skips the two samples; the branch edges sit
    // where the caustics have faded to nothing, so their mip selection cannot show.
    float shallows = clamp(-shore / 30.0, 0.0, 1.0) * (1.0 - clamp((-shore - 60.0) / 260.0, 0.0, 1.0));
    if (shallows <= 0.0)
    {
        return albedo;
    }
    float time = u_secretPulseParams.y;
    vec2 world = position.xy;
    vec2 wobble = vec2(sin(world.y / 23.0 + time * 1.3) + 0.6 * sin(world.y / 41.0 - time * 0.8),
        cos(world.x / 27.0 + time * 1.1) + 0.6 * cos(world.x / 37.0 - time * 0.9)) * 2.2;
    vec3 web = texture2DArray(s_terrainCaustics,
        vec3((world + wobble) / 380.0 + vec2(time * 0.006, time * 0.004), 0.0)).rgb;
    vec3 fine = texture2DArray(s_terrainCaustics,
        vec3((world - wobble * 0.6) / 290.0 - vec2(time * 0.008, time * 0.005), 1.0)).rgb;
    return albedo * (1.0 + max(web, fine * 0.45) * 1.5 * shallows);
}

// Liquid edge tiles without a seabed: the liquid alone where the native overlay was fully transparent. The coverage
// masks have no mip levels.
bool terrainLiquidEdgeCut(float waterKind, bool seabed, vec2 local, float tileLayer)
{
    return waterKind > 1.5 && !seabed && texture2DArray(s_texWaterCoverage, vec3(local, tileLayer)).r >= 0.999;
}

void main()
{
    clipWorldPosition(v_worldPosition);
    vec3 position = v_worldPosition;
    // The triangle's own normal.z from the screen-space derivatives, taken before any branch.
    vec3 faceNormal = cross(dFdx(position), dFdy(position));
    float faceUp = abs(faceNormal.z) * inversesqrt(max(dot(faceNormal, faceNormal), 1.0e-12));
    vec2 mapUv = vec2(position.x + 32768.0, 32768.0 - position.y) / 65536.0;
    vec2 cellCoord = mapUv * 128.0;
    vec2 cell = clamp(floor(cellCoord), vec2_splat(0.0), vec2_splat(126.0));
    vec2 local = clamp(cellCoord - cell, vec2_splat(0.0), vec2_splat(1.0));
    vec4 info = texture2DLod(s_terrainCells, (cell + 0.5) / 128.0, 0.0);
    if (info.a < 0.5)
    {
        discard;
    }
    float tileLayer = floor(info.r * 255.0 + 0.5);
    float waterKind = floor(info.g * 255.0 + 0.5);
    // info.b: 1 water, 0.5 an opaque liquid (tar, lava), 0 land; liquid cells are drawn by the liquid renderer.
    bool renderedWater = info.b > 0.25;
    // With a seabed, water cells draw the ground under the water renderer's see-through shallows.
    bool seabed = renderedWater && info.b > 0.75 && u_terrainShore.y > 0.5;
    float shore = u_terrainShore.y > 0.5
        ? (texture2D(s_terrainShore, mapUv).r * 255.0 - 128.0) / 127.0 * u_terrainShore.x : 0.0;
    // Deeper seabed, mostly hidden by the water, is plain: the full path fades into it, then a single sample.
    float plain = seabed && u_terrainShore.w >= 0.0
        ? smoothstep(u_terrainShore.z * 0.5, u_terrainShore.z, -shore) : 0.0;
    vec3 geometricNormal = normalize(v_worldNormal);

    vec3 albedo;
    vec3 shadingNormal = geometricNormal;
    float occlusion = 1.0;
    float roughness = 1.0;
    float layerSpecular = 0.0;
    float layerWetSheen = 1.0;
    float pool = 0.0;
    vec3 glow = vec3_splat(0.0);
    // Open liquid without a seabed: the liquid renderer draws the whole cell.
    if (waterKind > 0.5 && waterKind < 1.5 && renderedWater && !seabed)
    {
        discard;
    }
#if TERRAIN_DEPTH_ONLY
    if (plain <= 0.999 && terrainLiquidEdgeCut(waterKind, seabed, local, tileLayer))
    {
        discard;
    }
    gl_FragColor = vec4_splat(0.0);
#else
    if (plain > 0.999)
    {
        float layer = u_terrainShore.w;
        vec4 params = u_terrainLayerParams[int(layer + 0.5)];
        vec4 color = texture2DArray(s_terrainAlbedoHeight, vec3(vec2(position.x, -position.y) * params.x, layer));
        vec3 plainAlbedo = color.rgb * u_terrainLayerTint[int(layer + 0.5)].rgb
            * mix(1.0, 0.45 + 1.1 * color.a, params.w);
        albedo = shoreAlbedo(macroVaried(plainAlbedo, layer, texture2D(s_terrainMacro, position.xy / 16384.0), 0.0),
            position, shore);
    }
    else
    {
        if (terrainLiquidEdgeCut(waterKind, seabed, local, tileLayer))
        {
            discard;
        }
        vec4 weights0 = texture2DArray(s_terrainWeights, vec3(mapUv, 0.0));
        vec4 weights1 = texture2DArray(s_terrainWeights, vec3(mapUv, 1.0));
        vec4 macroSample = texture2D(s_terrainMacro, position.xy / 16384.0);
        // The meadow field is smooth; mid-scale noise frays the borders of its dry and lush patches.
        float meadow = clamp(v_texcoord0.y + (macroSample.g - 0.5) * 0.5 + (macroSample.a - 0.5) * 0.3, -1.0, 1.0);
        blendTerrainMaterial(weights0, weights1, position, geometricNormal, faceUp, v_texcoord0.x, macroSample, meadow,
            plain, u_terrainShore.w, albedo, shadingNormal, occlusion, roughness, layerSpecular, layerWetSheen, glow,
            pool);
        if (u_terrainShore.y > 0.5)
        {
            albedo = shoreAlbedo(albedo, position, shore);
        }
    }

    if (u_terrainFoliage[0].x > 0.0)
    {
        albedo = terrainFoliageAlbedo(albedo, texture2D(s_terrainFoliage, mapUv), position, u_cameraPosition.xyz,
            geometricNormal);
    }
    albedo = mix(albedo, u_fogColor.rgb, u_fogDensities.z);
    // Specular: smooth rock and rain-wet level ground glint; rough grass and dirt barely change. Skipped where the
    // material is too rough to show it.
    // Which ground glints is the material's (library specular: rock, gravel, flagstones), not its roughness map, whose
    // values vary too much between sources (some grass scans read smooth). Rain wets level ground of every material.
    // The texture roughness only varies the lobe across the surface.
    float wet = clamp(u_wetness.x * shadingNormal.z * shadingNormal.z * (1.0 - plain), 0.0, 1.0);
    // Rain leaves a damp sheen, not a mirror: a broad lobe, and grass (wet sheen a quarter) barely takes it.
    float specularRoughness = mix(clamp(0.15 + 0.15 * roughness, 0.18, 0.3), 0.38, wet);
    // A water film smooths the ground's fine relief: wet glints follow the broad surface, not the detail normal
    // (which sparkles as noise at this roughness).
    vec3 specularNormal = normalize(mix(shadingNormal, geometricNormal, 0.75 * wet));
    float specularStrength = u_terrainMaterialMisc.w * max(layerSpecular, 0.13 * wet * layerWetSheen);
    bool glossy = specularStrength > 0.0;
    vec3 toCamera = normalize(u_cameraPosition.xyz - position);
    vec3 specular = vec3_splat(0.0);
    if (glossy)
    {
        specular = terrainPointSpecular(position, specularNormal, toCamera, specularRoughness) * specularStrength;
    }
#if BAKED_SOURCES
    vec2 bakedUv = (position.xy - u_bakedTerrainBounds.xy) / u_bakedTerrainBounds.zw;
    vec4 sunSample = texture2DLod(s_texLightmap, bakedUv, 0.0);
    vec4 skySample = texture2DLod(s_texBakedSky, bakedUv, 0.0);
    vec3 totalSun = sunSample.rgb * (sunSample.a * 4.0);
    vec3 directSun = totalSun;
    if (u_terrainMaterialLight.w > 0.5 && plain < 0.999)
    {
        vec4 directSample = texture2DLod(s_texBakedSunDirect, bakedUv, 0.0);
        directSun = min(directSample.rgb * (directSample.a * 4.0), totalSun);
    }
    // The bake lit the native flat triangles; relight its direct sun for the smooth, detailed normal. The native
    // normal comes filtered exactly like the bake, so the ratio is smooth across native triangle edges. The plain
    // seabed keeps the bake as it is.
    float relight = 1.0;
    float skyFacing = 1.0;
    float visibility = 1.0;
    if (plain < 0.999)
    {
        vec3 facetNormal = texture2DLod(s_terrainBakedNormals, bakedUv, 0.0).xyz * 2.0 - 1.0;
        vec3 toSun = u_terrainMaterialLight.xyz;
        float facetFacing = dot(facetNormal, toSun);
        relight = mix(clamp(max(dot(shadingNormal, toSun), 0.0) / max(facetFacing, 0.15), 0.0, 2.0), 1.0, plain);
        skyFacing = mix((0.65 + 0.35 * shadingNormal.z) / (0.65 + 0.35 * facetNormal.z), 1.0, plain);
#if SUN_SHADOWS
        if (u_sunShadowParams[0].x > 0.5)
        {
            vec3 shadowNormal = dot(geometricNormal, u_sunShadowParams[3].xyz) < 0.0
                ? -geometricNormal : geometricNormal;
            visibility = mix(sunShadowVisibility(position, shadowNormal, 1.0), 1.0, plain);
        }
#endif
    }
    vec3 sunLight = (totalSun - directSun) * occlusion + directSun * relight * visibility;
    vec3 skyLight = skySample.rgb * (skySample.a * 4.0) * occlusion * skyFacing;
    vec3 lighting = sunLight * u_bakedLighting[0].rgb + skyLight * u_bakedLighting[1].rgb;
    vec3 litColor = bakedSurfaceColor(albedo, lighting + getFxLighting(position, 0.0));
    if (glossy)
    {
        // The bake's direct sun on the native facet, as the sun's light with its shadows (so shadowed ground does not
        // glint), relit for the detailed normal by the highlight.
        vec3 toSun = normalize(u_terrainMaterialLight.xyz);
        vec3 facetNormal = texture2DLod(s_terrainBakedNormals, bakedUv, 0.0).xyz * 2.0 - 1.0;
        vec3 sun = directSun * visibility / max(dot(facetNormal, toSun), 0.15) * u_bakedLighting[0].rgb;
        specular += sun * terrainSpecular(specularNormal, toCamera, toSun, specularRoughness) * specularStrength
            * occlusion;
        // Added to the linear light, then encoded like the rest.
        litColor = pow(pow(max(litColor, vec3_splat(0.0)), vec3_splat(2.2)) + specular, vec3_splat(1.0 / 2.2));
    }
#else
    vec3 litColor = albedo * getFxLighting(position, outdoorSunlight(normalize(mix(shadingNormal, geometricNormal,
        plain)))) * occlusion;
    if (glossy)
    {
        // The sun at the ambient level's complement: the unbaked terrain's sun term (outdoorSunlight).
        vec3 toSun = normalize(u_outdoorSunlight.xyz);
        float sun = max(1.0 - u_outdoorSunlight.w, 0.0);
        litColor += (specular + vec3_splat(sun * terrainSpecular(specularNormal, toCamera, toSun, specularRoughness)
            * specularStrength)) * occlusion;
    }
#endif
    if (plain < 0.999 && (waterKind < 0.5 || waterKind > 1.5))
    {
        litColor = mix(applyWetness(litColor, position), litColor, plain);
    }
    if (pool > 0.0)
    {
        // Standing water (level ground only): the dark, murky lit pool under a rippled surface that mirrors the sky
        // at grazing angles and glints.
        float time = u_secretPulseParams.y;
        vec2 ripplePosition = position.xy / 70.0;
        vec2 ripple = vec2(sin(ripplePosition.x * 1.7 + time * 1.9 + sin(ripplePosition.y * 1.3)),
            cos(ripplePosition.y * 1.9 - time * 1.6 + sin(ripplePosition.x * 1.1))) * 0.03;
        vec3 waterNormal = normalize(vec3(ripple, 1.0));
        vec3 toCamera = normalize(u_cameraPosition.xyz - position);
        float facing = clamp(dot(waterNormal, toCamera), 0.0, 1.0);
        float fresnel = 0.03 + 0.97 * pow(1.0 - facing, 5.0);
        vec3 toSun = normalize(u_terrainMaterialLight.xyz);
        float glint = pow(max(dot(reflect(-toCamera, waterNormal), toSun), 0.0), 160.0) * 0.5;
        vec3 water = mix(litColor * 0.65, u_fogColor.rgb * 0.8, min(fresnel, 0.7)) + vec3(1.0, 0.95, 0.85) * glint;
        litColor = mix(litColor, water, pool);
    }

    if (dot(glow, vec3_splat(1.0)) > 0.0)
    {
        // Emissive ground (library emissive): light of its own on top of the lit colour, fogged like the rest.
        litColor += glow;
    }

    float fogDistance = length(position - u_cameraPosition.xyz);
    float fogRatio = skyFogRatio(getFogRatio(fogDistance), position, fogDistance, u_fogDistances.z);
    vec4 fogColor = vec4(skyFogDisplayColor(fogRatio, u_fogColor.rgb, position), getFogAlpha(fogDistance));
    gl_FragColor = mix(vec4(litColor, 1.0), fogColor, fogRatio);
    gl_FragColor.rgb = mistApply(gl_FragColor.rgb, position);
#endif // !TERRAIN_DEPTH_ONLY
}
