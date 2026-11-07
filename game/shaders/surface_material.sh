// Surface materials of BLV and BModel face textures (devdocs/SURFACE_MATERIALS_PLAN.md). Two cooked maps lie beside
// a face's colour texture: the normal map (r, g: tangent-space x and y, +x along +u and +y up the image; b: glow) and
// the detail map (r: ambient occlusion, g: roughness, b: metal, a: height, 1 at the face plane). Outdoor arrays read
// them at the layer v_texcoord1.z of the colour texture's size group; a negative layer is a texture without maps.
// The tangent frame is the face's texture gradients per world unit (v_gradientU, v_gradientV from the vertices:
// game/render/SurfaceTextureGradients.h). Needs light_grid.sh.
#if BMODEL_TEXTURE_ARRAY
SAMPLER2DARRAY(s_surfaceNormal, 7);
SAMPLER2DARRAY(s_surfaceDetail, 8);
#define surfaceMap(_sampler, _uv, _layer) texture2DArray(_sampler, vec3(_uv, _layer))
#else
SAMPLER2D(s_surfaceNormal, 7);
SAMPLER2D(s_surfaceDetail, 8);
#define surfaceMap(_sampler, _uv, _layer) texture2D(_sampler, _uv)
#endif

// x = distance where parallax has faded out (0: off), y = night glow (0 by day, 1 at night: windows lit from inside),
// z = highlight strength (sun and point lights), w = sky or room reflection strength.
uniform vec4 u_surfaceMaterial;

// Screen-space reflections (video.surface_reflections): the previous frame's finished world at half resolution, its
// colour and its positions relative to the camera it was seen from (CinematicGrading::ReflectionHistory).
SAMPLER2D(s_reflectionColor, 9);
SAMPLER2D(s_reflectionPosition, 10);
uniform mat4 u_reflectionViewProjection;
// xyz: that camera, w: the sign of texture v along clip y.
uniform vec4 u_reflectionCamera;
// x: 1 when this draw traces reflections (the main view with a history), 0 otherwise.
uniform vec4 u_surfaceReflection;

#define SURFACE_REFLECTION_STEPS 24
#define SURFACE_REFLECTION_FIRST_STEP 12.0
#define SURFACE_REFLECTION_STEP_GROWTH 1.3
#define SURFACE_REFLECTION_DISTANCE 12000.0

// The deepest recess the height channel encodes, in world units (one unit is about a centimetre); the cook scales
// every texture's own depth into it (tools/surface_materials.py, MAX_DEPTH).
#define SURFACE_MAX_DEPTH 8.0
#define SURFACE_GLOW_SCALE 0.8
#define SURFACE_PARALLAX_STEPS 10.0
// Painted metal keeps part of its diffuse colour: the art already shows how the metal looks, and a fully specular
// metal turns black without a detailed environment to reflect.
#define SURFACE_METAL_DIFFUSE_LOSS 0.5
#define SURFACE_PI 3.14159265

struct SurfacePoint
{
    vec3 normal;
    float occlusion;
    float roughness;
    float metal;
    // Glow strength now (the night factor applied); the glow colour is the albedo.
    float glow;
    float height;
};

// The face's world-space normal from the position derivatives, turned toward the camera (BModel and BLV faces are
// flat).
vec3 surfaceFlatNormal(vec3 position, vec3 toCamera)
{
    vec3 normal = cross(dFdx(position), dFdy(position));
    normal *= inversesqrt(max(dot(normal, normal), 0.000001));
    return dot(normal, toCamera) < 0.0 ? -normal : normal;
}

// Parallax occlusion: the texture coordinate where the view ray meets the height field below the face plane. Fades
// out by distance and at grazing angles; no silhouette. weight: 0 turns it off (a face without maps).
// Fixed steps without branches: the maps are read with implicit derivatives, which need uniform control flow
// (bgfx's desktop GL path has no explicit-level array reads).
vec2 surfaceParallax(vec2 uv, float layer, float weight, vec3 toCamera, float distance, vec3 normal, vec3 gradientU,
    vec3 gradientV)
{
    // Off for the whole draw (video.surface_parallax, reflections and other views): a uniform branch, so the loop
    // below costs nothing then and the implicit derivatives stay valid.
    if (u_surfaceMaterial.x <= 0.0)
    {
        return uv;
    }
    vec3 view = -toCamera / max(distance, 0.001);
    float facing = max(-dot(normal, view), 0.0);
    float fade = u_surfaceMaterial.x > 0.0
        ? 1.0 - smoothstep(u_surfaceMaterial.x * 0.65, u_surfaceMaterial.x, distance) : 0.0;
    // Toward grazing views the ray would cross whole stones per step and smear the recesses: the depth fades out,
    // and the offset per unit of depth is capped.
    float depthRange = SURFACE_MAX_DEPTH * fade * weight * smoothstep(0.2, 0.55, facing);
    // Texture coordinates per world unit of depth along the view ray.
    vec2 uvPerDepth = vec2(dot(gradientU, view), dot(gradientV, view)) / max(facing, 0.35);
    float stepDepth = depthRange / SURFACE_PARALLAX_STEPS;
    float previousDepth = 0.0;
    float previousSurface = (1.0 - surfaceMap(s_surfaceDetail, uv, layer).a) * depthRange;
    float hitDepth = depthRange;
    float found = 0.0;
    for (int i = 1; i <= int(SURFACE_PARALLAX_STEPS); ++i)
    {
        float rayDepth = float(i) * stepDepth;
        float surfaceDepth = (1.0 - surfaceMap(s_surfaceDetail, uv + uvPerDepth * rayDepth, layer).a) * depthRange;
        // The first step below the surface: where the ray crosses it between the two samples.
        float crossed = step(surfaceDepth, rayDepth) * (1.0 - found);
        float before = previousSurface - previousDepth;
        float after = rayDepth - surfaceDepth;
        float crossing = mix(previousDepth, rayDepth, clamp(before / max(before + after, 0.0001), 0.0, 1.0));
        hitDepth = mix(hitDepth, crossing, crossed);
        found = max(found, crossed);
        previousDepth = rayDepth;
        previousSurface = surfaceDepth;
    }
    return uv + uvPerDepth * hitDepth;
}

// The material at a texture coordinate; nightGlow is the night factor of night-glowing texels.
SurfacePoint surfacePoint(vec4 normalSample, vec4 detailSample, vec3 normal, vec3 gradientU, vec3 gradientV,
    float nightGlow)
{
    SurfacePoint material;
    vec2 slopes = normalSample.xy * 2.0 - 1.0;
    vec3 tangent = gradientU * inversesqrt(max(dot(gradientU, gradientU), 1.0e-12));
    // +y of the normal map is up the image, against +v.
    vec3 bitangent = -gradientV * inversesqrt(max(dot(gradientV, gradientV), 1.0e-12));
    vec3 detailed = tangent * slopes.x + bitangent * slopes.y
        + normal * sqrt(max(1.0 - dot(slopes, slopes), 0.0));
    material.normal = normalize(detailed);
    material.occlusion = detailSample.r;
    material.metal = detailSample.b;
    material.height = detailSample.a;
    // Specular anti-aliasing: the normal's variation across the pixel widens the highlight instead of sparkling.
    vec3 dndx = dFdx(material.normal);
    vec3 dndy = dFdy(material.normal);
    float variance = 0.25 * (dot(dndx, dndx) + dot(dndy, dndy));
    float roughness = max(detailSample.g, 0.04);
    material.roughness = sqrt(clamp(roughness * roughness + min(2.0 * variance, 0.18), 0.0, 1.0));
    // b in (0, 0.45]: glows at night; [0.55, 1]: always glows. The gap keeps block compression from moving a full
    // night glow across the boundary.
    float glow = normalSample.b;
    float nightStrength = glow < 0.5 ? clamp(glow / 0.45, 0.0, 1.0) : 0.0;
    float alwaysStrength = glow >= 0.5 ? clamp((glow - 0.55) / 0.45, 0.0, 1.0) : 0.0;
    material.glow = nightStrength * nightGlow + alwaysStrength;
    return material;
}

// The light a glowing texel gives: its hue with the darkness of its paint compressed, as stained glass lit from behind
// shows its colours even where they are dark (glowing at the paint's own brightness left dark cells black).
vec3 surfaceGlowColor(vec3 albedo)
{
    float peak = max(max(albedo.r, albedo.g), albedo.b);
    return albedo / max(peak, 0.002) * (0.35 + 0.65 * sqrt(peak));
}

// The history texel a world point (relative to the history camera) falls on; xy: texture coordinate, z: whether it
// lies inside the view.
vec3 surfaceReflectionTexel(vec3 rayPoint)
{
    vec4 clip = mul(u_reflectionViewProjection, vec4(rayPoint + u_reflectionCamera.xyz, 1.0));
    vec2 ndc = clip.xy / max(clip.w, 0.0001);
    float inside = clip.w > 1.0 && abs(ndc.x) < 1.0 && abs(ndc.y) < 1.0 ? 1.0 : 0.0;
    return vec3(ndc.x * 0.5 + 0.5, ndc.y * (0.5 * u_reflectionCamera.w) + 0.5, inside);
}

// Screen-space reflection: marches the reflected ray through the previous frame's positions until it passes behind
// what was seen there, refines the crossing and returns that frame's colour (linear rgb) with a confidence (a; 0: none
// found, the caller keeps its sky or room). Fades at the screen edges, far away and for rays coming back toward the
// camera, whose targets the frame cannot have seen.
vec4 surfaceScreenReflection(vec3 position, vec3 direction, vec3 faceNormal)
{
    vec3 origin = position + faceNormal * 2.0 - u_reflectionCamera.xyz;
    float toward = dot(direction, -normalize(origin));
    float facing = 1.0 - smoothstep(0.2, 0.7, toward);
    if (facing <= 0.0)
    {
        return vec4_splat(0.0);
    }
    float travelled = 0.0;
    float stepLength = SURFACE_REFLECTION_FIRST_STEP;
    for (int i = 0; i < SURFACE_REFLECTION_STEPS; ++i)
    {
        float next = travelled + stepLength;
        vec3 rayPoint = origin + direction * next;
        vec3 texel = surfaceReflectionTexel(rayPoint);
        if (texel.z < 0.5 || next > SURFACE_REFLECTION_DISTANCE)
        {
            break;
        }
        vec4 scene = texture2DLod(s_reflectionPosition, texel.xy, 0.0);
        float behind = length(rayPoint) - length(scene.xyz);
        if (scene.a > 0.5 && behind > 0.0 && behind < max(stepLength * 2.0, 24.0))
        {
            float low = travelled;
            float high = next;
            for (int j = 0; j < 4; ++j)
            {
                float middle = (low + high) * 0.5;
                vec3 probe = origin + direction * middle;
                vec4 probeScene = texture2DLod(s_reflectionPosition, surfaceReflectionTexel(probe).xy, 0.0);
                if (probeScene.a > 0.5 && length(probe) > length(probeScene.xyz))
                {
                    high = middle;
                }
                else
                {
                    low = middle;
                }
            }
            vec2 uv = surfaceReflectionTexel(origin + direction * high).xy;
            vec2 edge = 1.0 - smoothstep(vec2_splat(0.8), vec2_splat(1.0), abs(uv * 2.0 - 1.0));
            float confidence = edge.x * edge.y * facing
                * (1.0 - smoothstep(SURFACE_REFLECTION_DISTANCE * 0.6, SURFACE_REFLECTION_DISTANCE, high));
            vec3 color = texture2DLod(s_reflectionColor, uv, 0.0).rgb;
            return vec4(pow(max(color, vec3_splat(0.0)), vec3_splat(2.2)), confidence);
        }
        travelled = next;
        stepLength *= SURFACE_REFLECTION_STEP_GROWTH;
    }
    return vec4_splat(0.0);
}

// The sky or room radiance a smooth surface reflects, replaced where the screen holds what lies in that direction.
// Only smooth surfaces trace (rough ones blur the reflection away).
vec3 surfaceTracedReflection(vec3 environment, vec3 position, vec3 direction, vec3 faceNormal, float roughness,
    float reflection)
{
    if (u_surfaceReflection.x < 0.5 || reflection < 0.05 || roughness > 0.6)
    {
        return environment;
    }
    vec4 traced = surfaceScreenReflection(position, direction, faceNormal);
    return mix(environment, traced.rgb, traced.a * (1.0 - smoothstep(0.3, 0.6, roughness)));
}

// GGX highlight of one light (N.L included), with Schlick Fresnel from f0.
vec3 surfaceSpecular(vec3 normal, vec3 toCamera, vec3 toLight, float roughness, vec3 f0)
{
    float nl = dot(normal, toLight);
    if (nl <= 0.0)
    {
        return vec3_splat(0.0);
    }
    vec3 halfVector = normalize(toCamera + toLight);
    float nh = max(dot(normal, halfVector), 0.0);
    float nv = max(dot(normal, toCamera), 0.001);
    float vh = max(dot(toCamera, halfVector), 0.0);
    float alpha = max(roughness * roughness, 0.002);
    float alpha2 = alpha * alpha;
    float denominator = nh * nh * (alpha2 - 1.0) + 1.0;
    float distribution = alpha2 / (SURFACE_PI * denominator * denominator);
    float k = alpha * 0.5;
    float visibility = 0.25 / ((nl * (1.0 - k) + k) * (nv * (1.0 - k) + k));
    // pow() of a negative base is undefined (NaN on some GPUs, e.g. D3D): with the light at the camera (the party
    // torch), vh rounds to just above 1 and scattered pixels turn black.
    vec3 fresnel = f0 + (vec3_splat(1.0) - f0) * pow(max(1.0 - vh, 0.0), 5.0);
    return fresnel * (distribution * visibility * nl);
}

// Split-sum environment response for the sky reflection (Karis's analytic fit of the integrated BRDF).
vec3 surfaceEnvironmentResponse(vec3 f0, float roughness, float nv)
{
    vec4 c0 = vec4(-1.0, -0.0275, -0.572, 0.022);
    vec4 c1 = vec4(1.0, 0.0425, 1.04, -0.04);
    vec4 r = roughness * c0 + c1;
    float a004 = min(r.x * r.x, exp2(-9.28 * nv)) * r.x + r.y;
    vec2 ab = vec2(-1.04, 1.04) * a004 + r.zw;
    return f0 * ab.x + vec3_splat(ab.y);
}

// How much brighter a light is on the detailed normal than on the flat face the light was computed for.
float surfaceRelight(vec3 detailed, vec3 faceNormal, vec3 toLight)
{
    return clamp(max(dot(detailed, toLight), 0.0) / max(dot(faceNormal, toLight), 0.15), 0.0, 2.0);
}

// Diffuse (relit for the detailed normal) and highlights of the light grid's dynamic lights at a point. facing: the
// indoor flat-face response (outdoor point lights are undirected). Static lights are baked, so the first one ends
// the list. sectors: the face's sectors indoors (light reach), (-1, -1) outdoors.
void surfacePointLights(vec3 position, SurfacePoint material, vec3 faceNormal, vec3 toCamera, vec3 f0, vec2 sectors,
    bool facing, out vec3 diffuse, out vec3 specular)
{
    diffuse = vec3_splat(0.0);
    specular = vec3_splat(0.0);
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
        vec3 source = lightGridLightSource(index);
        if (source.y < 0.5)
        {
            break;
        }
        if (!lightGridReaches(index, source, sectors))
        {
            continue;
        }
        vec4 positionRadius;
        vec4 colorIntensity;
        lightGridLight(index, positionRadius, colorIntensity);
        vec3 toLight = positionRadius.xyz - position;
        vec3 direction = toLight * inversesqrt(max(dot(toLight, toLight), 0.0001));
        vec3 light = colorIntensity.rgb * (colorIntensity.a * lightGridAttenuation(positionRadius, position));
        float flatResponse = 1.0;
        if (facing)
        {
            // indoorFaceFacing: nearly angle-free toward the light, none on the far side.
            float flatFacing = clamp(dot(faceNormal, direction), 0.0, 1.0);
            flatResponse = smoothstep(0.0, 0.08, flatFacing) * (0.86 + 0.14 * sqrt(flatFacing));
        }
        diffuse += light * flatResponse * surfaceRelight(material.normal, faceNormal, direction);
        specular += light * flatResponse
            * surfaceSpecular(material.normal, toCamera, direction, material.roughness, f0);
    }
}
