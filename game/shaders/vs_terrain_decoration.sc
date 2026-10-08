$input a_position, a_texcoord0, a_color0, i_data0, i_data1, i_data2, i_data3
$output v_texcoord0, v_texcoord1, v_worldPosition, v_flowInfo, v_depth, v_color0, v_sunlight

#include "common.sh"
#include "outdoor_sunlight.sh"
#include "outdoor_lighting.sh"
#if BAKED_SOURCES
SAMPLER2D(s_texLightmap, 2);
uniform vec4 u_bakedTerrainBounds;
#include "outdoor_baked_lighting.sh"
#endif

uniform vec4 u_cameraPosition;
uniform vec4 u_terrainDecorationParams;
// Card outline per tuft layer: 8 texture coordinates per layer, two per vec4 (TerrainDecorationRenderer).
uniform vec4 u_terrainDecorationCutout[64];

void main()
{
    float distance = length(i_data0.xyz - u_cameraPosition.xyz);
    // Keep silhouettes at their authored size. Stagger the coverage fade in a broad far band;
    // changing the camera must never make grass grow out of the ground.
    float seed = fract(sin(dot(i_data0.xy, vec2(0.0129898, 0.078233))) * 43758.5453);
    float rangeScale = mix(0.8, 1.0, seed);
    float fade = 1.0 - smoothstep(u_terrainDecorationParams.y * rangeScale,
                                u_terrainDecorationParams.z * rangeScale, distance);
    float c = cos(i_data0.w);
    float s = sin(i_data0.w);
    vec3 position = a_position;
    vec2 texcoord = a_texcoord0;
    if (u_terrainDecorationParams.w > 0.5)
    {
        // Grass card: a_position.x = outline slot, a_position.y = which of the two crossed cards.
        float index = floor(i_data3.w + 0.5) * 8.0 + a_position.x;
        vec4 pair = u_terrainDecorationCutout[int(index * 0.5)];
        texcoord = fract(index * 0.5) > 0.25 ? pair.zw : pair.xy;
        position = a_position.y < 0.5 ? vec3(texcoord.x - 0.5, 0.0, 1.0 - texcoord.y)
            : vec3(0.0, texcoord.x - 0.5, 1.0 - texcoord.y);
    }
    vec3 local = position * vec3(i_data1.x, i_data1.x, i_data1.y);
    vec3 world = i_data0.xyz + vec3(c * local.x - s * local.y, s * local.x + c * local.y, local.z);
    world.z -= dot(world.xy - i_data0.xy, i_data3.xy) / max(i_data3.z, 0.5);
    float phase = u_terrainDecorationParams.x * 1.6 + dot(i_data0.xy, vec2(0.003, 0.004));
    world.xy += vec2(sin(phase), cos(phase * 0.7)) * i_data1.z * position.z * position.z;
    gl_Position = mul(u_viewProj, vec4(world, 1.0));
    v_worldPosition = world;
    v_texcoord0 = texcoord;
    v_texcoord1 = vec4(0.0, i_data1.w, fade, seed);
    v_depth = gl_Position.w;
    v_color0 = a_color0 * i_data2;
    v_sunlight = outdoorSunlight(i_data3.xyz);
    // A tuft is small, so its light is evaluated per vertex: v_flowInfo.yzw multiplies the display-space texel.
    // Baked: (texel^2.2 * light)^(1/2.2) = texel * light^(1/2.2). The sun-shadow fragment variants relight per pixel.
#if BAKED_SOURCES
    vec2 bakedUv = (world.xy - u_bakedTerrainBounds.xy) / u_bakedTerrainBounds.zw;
    vec3 light = bakedSourceLighting(texture2DLod(s_texLightmap, bakedUv, 0.0),
        texture2DLod(s_texBakedSky, bakedUv, 0.0)) + getFxLighting(world, 0.0);
    light = pow(max(light, vec3_splat(0.0)), vec3_splat(1.0 / 2.2));
#else
    vec3 light = getFxLighting(world, v_sunlight);
#endif
    v_flowInfo = vec4(i_data3.w, light);
}
