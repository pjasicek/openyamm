// Blended ground materials (OutdoorTerrainMaterials, IndoorTerrainMaterials): the library layers in two texture
// arrays, their per-layer parameters, and the blend of the two strongest layers at a point. Shared by the outdoor
// terrain (outdoor_terrain_materials.sh) and the terrain faces of open-air BLVs (fs_indoor_textured_lit,
// INDOOR_TERRAIN).

SAMPLER2DARRAY(s_terrainAlbedoHeight, 8);
SAMPLER2DARRAY(s_terrainNormalAoRough, 9);
// Ground layer weights: array layer 0 holds layers 0-3, layer 1 layers 4-7 (stage 11 is the light grid's).
SAMPLER2DARRAY(s_terrainWeights, 10);
// Tileable cloudy noise over 16384 world units: R ~4000-unit, G ~1000-unit, B ~2500-unit (tint), A ~250-unit.
SAMPLER2D(s_terrainMacro, 14);

// Per layer: x = 1 / repeat in world units, y = height blend contrast, z = normal strength, w = cavity: how much
// the material height darkens its albedo (photoscans are delit; the native tiles carry their shading).
uniform vec4 u_terrainLayerParams[8];
// rgb = tint, w = strength of the meadow tint (u_terrainMeadow) on this layer.
uniform vec4 u_terrainLayerTint[8];
// Per ground layer: rgb = the slope layer's tint where that layer dominates (cliffs take the colour of their ground),
// w = the material's rain-wet sheen share in quarters (integer part, 0..4; grass takes a quarter) plus its ground
// highlight strength (fraction; library.yml specular: rock, gravel, flagstones; 0 for soil and grass).
uniform vec4 u_terrainLayerCliff[8];
uniform vec4 u_terrainLayerMacro[8];
// Per layer: x = layer of its variant material (mixed in patches for mid-scale variety), y = variant coverage,
// z = scale of the edge fringe noise where it meets another layer, w = 1 when its smoothest texels are standing
// water (swamp pools).
uniform vec4 u_terrainLayerVariant[8];
// Per layer: rgb = glow colour of its emissive texels (0 for every material without library emissive), w = the albedo
// warmth (red minus blue, untinted) where the glow starts: lava and creep veins glow whatever the light.
uniform vec4 u_terrainLayerEmissive[8];
// x = weighted layer count, y = slope layer (negative: none), z/w = slope start/end as 1 - normal.z.
uniform vec4 u_terrainMaterialControl;
// x = fringe strength, y = 1 / world size of the fringe noise repeat, z = 1 for second projections (anti-tiling,
// blended cliff sides), w = specular strength (0: off; video.terrain_specular).
uniform vec4 u_terrainMaterialMisc;
// Colour multipliers of the driest ([0].rgb) and lushest ([1].rgb) ground (OutdoorMeadowField, v_texcoord0.y).
uniform vec4 u_terrainMeadow[2];

// smoothstep that is zero for an empty range (outdoor_lighting.sh's safeSmoothstep; this file is also included
// without it).
float terrainSmoothstep(float edge0, float edge1, float value)
{
    if (edge0 == edge1)
    {
        return 0.0;
    }

    float t = clamp((value - edge0) / (edge1 - edge0), 0.0, 1.0);
    return t * t * (3.0 - 2.0 * t);
}

// Macro variation (UE-style): per layer, rgb = tint of the cloudy patches, a = broad brightness variation. Then the
// meadow: dry crests and slopes, lush hollows and shores (meadow -1 lush .. +1 dry), scaled by the layer's strength.
vec3 macroVaried(vec3 albedo, float layer, vec4 macroSample, float meadow)
{
    vec4 macro = u_terrainLayerMacro[int(layer + 0.5)];
    float broad = macroSample.r * 0.6 + macroSample.g * 0.4;
    albedo *= 1.0 + (broad - 0.5) * 2.0 * macro.a;
    albedo *= mix(vec3_splat(1.0), macro.rgb, smoothstep(0.35, 0.75, macroSample.b));
    vec3 meadowTint = meadow > 0.0 ? u_terrainMeadow[0].rgb : u_terrainMeadow[1].rgb;
    return albedo * mix(vec3_splat(1.0), meadowTint, min(abs(meadow) * u_terrainLayerTint[int(layer + 0.5)].w, 1.0));
}

// Whiteout blends of a tangent-space detail normal on the vertical planes facing X (right = +Y, up = +Z) and
// facing Y (right = +X, up = +Z).
vec3 facingXNormal(vec3 tangent, vec3 geometric)
{
    vec3 blended = vec3(tangent.xy + geometric.yz, abs(geometric.x) * tangent.z);
    return vec3(sign(geometric.x) * blended.z, blended.x, blended.y);
}

vec3 facingYNormal(vec3 tangent, vec3 geometric)
{
    vec3 blended = vec3(tangent.xy + geometric.xz, abs(geometric.y) * tangent.z);
    return vec3(blended.x, sign(geometric.y) * blended.z, blended.y);
}

vec3 detailTangent(vec4 detail, float strength)
{
    vec2 slopes = detail.xy * 2.0 - 1.0;
    return vec3(slopes * strength, sqrt(max(1.0 - dot(slopes, slopes), 0.0)));
}


// One layer: albedo with height, world-space shading normal, and ambient occlusion with roughness. Ground layers
// project from above; the slope layer projects onto the vertical planes so cliffs are not stretched. With
// u_terrainMaterialMisc.z, a second projection (rotated from above, or the other vertical plane) hides the repeat
// and blends cliff sides; detail scales its share (zero on the plain seabed). That branch is uniform, so
// anisotropic filtering keeps its implicit derivatives. faceUp is the triangle's own normal.z.
// The glow of a layer's sample: its untinted albedo where it is warm enough, in the layer's glow colour.
vec3 terrainLayerGlow(vec3 tintedAlbedo, vec3 tint, float layer)
{
    vec4 emissive = u_terrainLayerEmissive[int(layer + 0.5)];
    vec3 albedo = tintedAlbedo / max(tint, vec3_splat(0.02));
    return albedo * emissive.rgb * smoothstep(emissive.w, emissive.w + 0.25, albedo.r - albedo.b);
}

void sampleTerrainLayer(float layer, vec3 tint, vec3 world, vec3 geometric, float faceUp, float variation,
    float detail, out vec4 albedoHeight, out vec3 normal, out vec2 occlusionRoughness)
{
    vec4 params = u_terrainLayerParams[int(layer + 0.5)];
    vec4 variant = u_terrainLayerVariant[int(layer + 0.5)];
    bool slope = abs(layer - u_terrainMaterialControl.y) < 0.5;
    bool detailed = u_terrainMaterialMisc.z > 0.5;
    bool facingX = detailed || abs(geometric.x) >= abs(geometric.y);
    // U follows world X and V world -Y, so an OpenGL normal map's red and green are world X and Y.
    vec2 planar = vec2(world.x, -world.y) * params.x;
    vec2 side = facingX ? vec2(world.y, -world.z) : vec2(world.x, -world.z);
    vec2 uvA = slope ? side * params.x : planar;
    vec4 colorA = texture2DArray(s_terrainAlbedoHeight, vec3(uvA, layer));
    vec4 detailA = texture2DArray(s_terrainNormalAoRough, vec3(uvA, layer));
    vec3 tangentA = detailTangent(detailA, params.z);
    vec3 normalA = slope
        ? (facingX ? facingXNormal(tangentA, geometric) : facingYNormal(tangentA, geometric))
        : vec3(tangentA.xy + geometric.xy, tangentA.z * geometric.z);
    colorA.rgb *= tint;
    albedoHeight = colorA;
    normal = normalize(normalA);
    occlusionRoughness = detailA.zw;
    if (detailed)
    {
        // Ground layers take the second sample from their variant material (or themselves), rotated.
        float layerB = slope ? layer : variant.x;
        vec4 paramsB = u_terrainLayerParams[int(layerB + 0.5)];
        vec2 planarB = vec2(world.x, -world.y) * paramsB.x;
        vec2 rotated = vec2(0.8 * planarB.x - 0.6 * planarB.y, 0.6 * planarB.x + 0.8 * planarB.y) * 0.71
            + vec2(0.37, 0.61);
        vec2 uvB = slope ? vec2(world.x, -world.z) * params.x : rotated;
        vec4 colorB = texture2DArray(s_terrainAlbedoHeight, vec3(uvB, layerB));
        vec4 detailB = texture2DArray(s_terrainNormalAoRough, vec3(uvB, layerB));
        colorB.rgb *= slope ? tint : u_terrainLayerTint[int(layerB + 0.5)].rgb;
        vec3 tangentB = detailTangent(detailB, paramsB.z);
        vec3 normalB;
        float share;
        if (slope)
        {
            normalB = facingYNormal(tangentB, geometric);
            share = smoothstep(-0.15, 0.15, abs(geometric.y) - abs(geometric.x) + (colorB.a - colorA.a) * 0.25);
        }
        else
        {
            // Back from the rotated texture frame (V points down the image) to world X/Y.
            vec2 tangent = vec2(tangentB.x, -tangentB.y);
            vec2 unrotated = vec2(0.8 * tangent.x + 0.6 * tangent.y, -0.6 * tangent.x + 0.8 * tangent.y);
            normalB = vec3(vec2(unrotated.x, -unrotated.y) + geometric.xy, tangentB.z * geometric.z);
            // The variant covers about variant.y of the ground in soft macro-noise patches; within the wide
            // transition the taller sample wins, so edges break up finely instead of averaging the two.
            share = smoothstep(-0.12, 0.12, (variation - 1.0 + variant.y) * 0.9 + (colorB.a - colorA.a) * 0.45);
        }
        share *= detail;
        albedoHeight = mix(colorA, colorB, share);
        normal = normalize(mix(normal, normalize(normalB), share));
        occlusionRoughness = mix(detailA.zw, detailB.zw, share);
    }
    // Ground layers on banks too gentle for the slope layer: the projection from above stretches down the slope, so
    // the steeper part blends to the two vertical planes. The coordinates come before the branch, so their implicit
    // derivatives hold in it; only bank pixels pay for the extra samples. A flat triangle is never a bank: along the
    // foot of an abrupt cliff the smooth normals, taken across the step, tilt the flat strip below it.
    vec2 sideUvX = vec2(world.y, -world.z) * params.x;
    vec2 sideUvY = vec2(world.x, -world.z) * params.x;
    float upward = smoothstep(0.72, 0.92, max(geometric.z, faceUp));
    // The slope layer follows the broadly smoothed terrain, so it also covers the flat strip at a cliff's foot, where
    // its vertical projections would smear into streaks: there it projects from above like the ground layers.
    if (slope && upward > 0.0)
    {
        vec4 colorTop = texture2DArray(s_terrainAlbedoHeight, vec3(planar, layer));
        vec4 detailTop = texture2DArray(s_terrainNormalAoRough, vec3(planar, layer));
        vec3 tangentTop = detailTangent(detailTop, params.z);
        colorTop.rgb *= tint;
        albedoHeight = mix(albedoHeight, colorTop, upward);
        normal = normalize(mix(normal, normalize(vec3(tangentTop.xy + geometric.xy, tangentTop.z * geometric.z)),
            upward));
        occlusionRoughness = mix(occlusionRoughness, detailTop.zw, upward);
    }
    float bank = slope ? 0.0 : 1.0 - upward;
    if (bank > 0.0)
    {
        // The plane the bank faces. Without anti-tiling it is the only one, switching at the diagonal like the slope
        // layer's. With it, both blend where the bank faces within about 10 degrees of a diagonal, so most bank
        // pixels still pay for one plane.
        float facing = (abs(geometric.y) - abs(geometric.x)) / max(length(geometric.xy), 0.0001);
        float weightY = detailed ? smoothstep(-0.25, 0.25, facing) : step(0.0, facing);
        vec4 colorX = vec4_splat(0.0);
        vec4 detailX = vec4(0.5, 0.5, 1.0, 1.0);
        vec4 colorY = vec4_splat(0.0);
        vec4 detailY = vec4(0.5, 0.5, 1.0, 1.0);
        if (!detailed)
        {
            vec2 sideUv = weightY > 0.5 ? sideUvY : sideUvX;
            vec4 color = texture2DArray(s_terrainAlbedoHeight, vec3(sideUv, layer));
            vec4 detailSample = texture2DArray(s_terrainNormalAoRough, vec3(sideUv, layer));
            colorX = color;
            detailX = detailSample;
            colorY = color;
            detailY = detailSample;
        }
        else
        {
            if (weightY < 1.0)
            {
                colorX = texture2DArray(s_terrainAlbedoHeight, vec3(sideUvX, layer));
                detailX = texture2DArray(s_terrainNormalAoRough, vec3(sideUvX, layer));
            }
            if (weightY > 0.0)
            {
                colorY = texture2DArray(s_terrainAlbedoHeight, vec3(sideUvY, layer));
                detailY = texture2DArray(s_terrainNormalAoRough, vec3(sideUvY, layer));
            }
        }
        weightY = clamp(weightY + (colorY.a - colorX.a) * 2.0 * weightY * (1.0 - weightY), 0.0, 1.0);
        float weightX = 1.0 - weightY;
        vec4 sideColor = colorX * weightX + colorY * weightY;
        sideColor.rgb *= tint;
        vec3 sideNormal = facingXNormal(detailTangent(detailX, params.z), geometric) * weightX
            + facingYNormal(detailTangent(detailY, params.z), geometric) * weightY;
        albedoHeight = mix(albedoHeight, sideColor, bank);
        normal = normalize(mix(normal, normalize(sideNormal), bank));
        occlusionRoughness = mix(occlusionRoughness, detailX.zw * weightX + detailY.zw * weightY, bank);
    }
}
// The ground at a point from its layer weights (weights0: layers 0-3, weights1: layers 4-7): the two strongest
// layers, the slope layer where steepness (1 - normal.z of the broadly smoothed ground) passes the slope start, blended
// by height with the fringe noise across their soft band. geometricNormal: the smooth surface normal; faceUp: the
// triangle's own normal.z; macroSample: s_terrainMacro at position.xy / 16384; meadow: -1 lush .. +1 dry; plain and
// shoreLayer: the outdoor seabed's plain share and its layer (0 and -1 elsewhere).
void blendTerrainMaterial(vec4 weights0, vec4 weights1, vec3 position, vec3 geometricNormal, float faceUp,
    float steepness, vec4 macroSample, float meadow, float plain, float shoreLayer, out vec3 albedo,
    out vec3 shadingNormal, out float occlusion, out float roughness, out float layerSpecular, out float layerWetSheen,
    out vec3 glow, out float pool)
{
    glow = vec3_splat(0.0);
    float weights[8];
    weights[0] = weights0.x;
    weights[1] = weights0.y;
    weights[2] = weights0.z;
    weights[3] = weights0.w;
    weights[4] = weights1.x;
    weights[5] = weights1.y;
    weights[6] = weights1.z;
    weights[7] = weights1.w;
    float dominantWeight = -1.0;
    float dominantLayer = 0.0;
    for (int index = 0; index < 8; ++index)
    {
        if (weights[index] > dominantWeight)
        {
            dominantWeight = weights[index];
            dominantLayer = float(index);
        }
    }
    float variation = macroSample.g * 0.65 + macroSample.a * 0.35;
    if (u_terrainMaterialControl.y >= 0.0)
    {
        // steepness: 1 - normal.z of the broadly smoothed terrain; the macro noise roughens the edge. The
        // single-material test (OutdoorTerrainMaterials::createMesh) relies on the noise moving it by 0.1 at most.
        float steep = terrainSmoothstep(u_terrainMaterialControl.z, u_terrainMaterialControl.w,
            steepness + (macroSample.a - 0.5) * 0.12 + (macroSample.g - 0.5) * 0.08);
        for (int index = 0; index < 8; ++index)
        {
            weights[index] = weights[index] * (1.0 - steep)
                + (abs(float(index) - u_terrainMaterialControl.y) < 0.5 ? steep : 0.0);
        }
    }
    float firstWeight = -1.0;
    float secondWeight = -1.0;
    float firstLayer = 0.0;
    float secondLayer = 0.0;
    for (int index = 0; index < 8; ++index)
    {
        float weight = weights[index];
        if (weight > firstWeight)
        {
            secondWeight = firstWeight;
            secondLayer = firstLayer;
            firstWeight = weight;
            firstLayer = float(index);
        }
        else if (weight > secondWeight)
        {
            secondWeight = weight;
            secondLayer = float(index);
        }
    }
    // The two strongest layers take their slots in layer order, not by strength: where they are equally strong,
    // neighbouring pixels then still sample each layer in the same slot. A swap inside a 2x2 pixel quad tore the
    // texture coordinate derivatives (each layer has its own repeat), sampled the smallest mips and drew dotted
    // lines through the middle of every blend.
    if (secondLayer < firstLayer)
    {
        float layer = firstLayer;
        firstLayer = secondLayer;
        secondLayer = layer;
        float weight = firstWeight;
        firstWeight = secondWeight;
        secondWeight = weight;
    }
    vec4 firstColor;
    vec3 firstNormal;
    vec2 firstSurface;
    vec4 secondColor;
    vec3 secondNormal;
    vec2 secondSurface;
    vec3 cliffTint = u_terrainLayerCliff[int(dominantLayer + 0.5)].rgb;
    vec3 firstTint = abs(firstLayer - u_terrainMaterialControl.y) < 0.5
        ? cliffTint : u_terrainLayerTint[int(firstLayer + 0.5)].rgb;
    vec3 secondTint = abs(secondLayer - u_terrainMaterialControl.y) < 0.5
        ? cliffTint : u_terrainLayerTint[int(secondLayer + 0.5)].rgb;
#if SINGLE_MATERIAL
    // This draw holds the triangles whose pixels read one material only (OutdoorTerrainMaterials::createMesh):
    // the stronger slot alone is sampled, and the empty slot copies it with no weight.
    if (firstWeight < secondWeight)
    {
        firstLayer = secondLayer;
        firstWeight = secondWeight;
        firstTint = secondTint;
    }
    secondLayer = firstLayer;
    secondWeight = 0.0;
    sampleTerrainLayer(firstLayer, firstTint, position, geometricNormal, faceUp, variation, 1.0 - plain,
        firstColor, firstNormal, firstSurface);
    secondColor = firstColor;
    secondNormal = firstNormal;
    secondSurface = firstSurface;
#else
    sampleTerrainLayer(firstLayer, firstTint, position, geometricNormal, faceUp, variation, 1.0 - plain,
        firstColor, firstNormal, firstSurface);
    sampleTerrainLayer(secondLayer, secondTint, position, geometricNormal, faceUp, variation, 1.0 - plain,
        secondColor, secondNormal, secondSurface);
#endif
    // Height blend: the taller material shows through first where both are present.
    float total = max(firstWeight + max(secondWeight, 0.0), 0.0001);
    float firstShare = firstWeight / total;
    // Fringe: across the soft band between two layers, fine noise (A ~1/64 and G ~1/16 of its repeat) tips the
    // balance, scattering clumps and islands of the lower-numbered layer into the other and holes back into it.
    vec4 fringeSample = texture2D(s_terrainMacro, position.xy * u_terrainMaterialMisc.y);
    float fringeScale = min(u_terrainLayerVariant[int(firstLayer + 0.5)].z,
        u_terrainLayerVariant[int(secondLayer + 0.5)].z);
    float fringe = (fringeSample.a * 0.55 + fringeSample.g * 0.45 - 0.5) * u_terrainMaterialMisc.x * fringeScale
        * 4.0 * firstShare * (1.0 - firstShare);
    firstShare = clamp(firstShare + fringe, 0.0, 1.0);
    float secondShare = 1.0 - firstShare;
    vec4 firstParams = u_terrainLayerParams[int(firstLayer + 0.5)];
    vec4 secondParams = u_terrainLayerParams[int(secondLayer + 0.5)];
    float depth = mix(firstParams.y, secondParams.y, 0.5);
    float top = max(firstColor.a + firstShare, secondColor.a + secondShare) - depth;
    // A layer fades out with its weight: one without weight never shows through the low spots of the other, so
    // the single-material draw, which skips it, matches the triangles around it.
    float firstAmount = max(firstColor.a + firstShare - top, 0.0) * clamp(firstWeight * 10.0, 0.0, 1.0);
    float secondAmount = max(secondColor.a + secondShare - top, 0.0) * clamp(secondWeight * 10.0, 0.0, 1.0);
    // The plain seabed is the shore layer alone, whichever slot it holds.
    float secondMix = mix(secondAmount / max(firstAmount + secondAmount, 0.0001),
        abs(secondLayer - shoreLayer) < 0.5 ? 1.0 : 0.0, plain);
    vec3 firstAlbedo = firstColor.rgb * mix(1.0, 0.45 + 1.1 * firstColor.a, firstParams.w);
    vec3 secondAlbedo = secondColor.rgb * mix(1.0, 0.45 + 1.1 * secondColor.a, secondParams.w);
    albedo = mix(macroVaried(firstAlbedo, firstLayer, macroSample, meadow),
        macroVaried(secondAlbedo, secondLayer, macroSample, meadow), secondMix);
    shadingNormal = normalize(mix(firstNormal, secondNormal, secondMix));
    occlusion = mix(mix(1.0, mix(firstSurface.x, secondSurface.x, secondMix), 0.85), 1.0, plain);
    roughness = mix(mix(firstSurface.y, secondSurface.y, secondMix), 1.0, plain);
    float firstPacked = u_terrainLayerCliff[int(firstLayer + 0.5)].w;
    float secondPacked = u_terrainLayerCliff[int(secondLayer + 0.5)].w;
    layerSpecular = mix(fract(firstPacked), fract(secondPacked), secondMix) * (1.0 - plain);
    layerWetSheen = mix(floor(firstPacked), floor(secondPacked), secondMix) * 0.25;
    vec3 firstEmissive = u_terrainLayerEmissive[int(firstLayer + 0.5)].rgb;
    vec3 secondEmissive = u_terrainLayerEmissive[int(secondLayer + 0.5)].rgb;
    if (dot(firstEmissive + secondEmissive, vec3_splat(1.0)) > 0.0)
    {
        glow = mix(terrainLayerGlow(firstColor.rgb, firstTint, firstLayer),
            terrainLayerGlow(secondColor.rgb, secondTint, secondLayer), secondMix) * (1.0 - plain);
    }
    pool = mix(u_terrainLayerVariant[int(firstLayer + 0.5)].w * terrainSmoothstep(0.2, 0.12, firstSurface.y),
        u_terrainLayerVariant[int(secondLayer + 0.5)].w * terrainSmoothstep(0.2, 0.12, secondSurface.y), secondMix)
        * (1.0 - plain) * terrainSmoothstep(0.94, 0.985, geometricNormal.z);
}
