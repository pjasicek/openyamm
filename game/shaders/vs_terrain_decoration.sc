$input a_position, a_texcoord0, a_color0, i_data0, i_data1, i_data2, i_data3
$output v_texcoord0, v_texcoord1, v_worldPosition, v_flowInfo, v_depth, v_color0, v_sunlight

#include "common.sh"
#include "outdoor_sunlight.sh"

uniform vec4 u_cameraPosition;
uniform vec4 u_terrainDecorationParams;

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
    vec3 local = a_position * vec3(i_data1.x, i_data1.x, i_data1.y);
    vec3 world = i_data0.xyz + vec3(c * local.x - s * local.y, s * local.x + c * local.y, local.z);
    world.z -= dot(world.xy - i_data0.xy, i_data3.xy) / max(i_data3.z, 0.5);
    float phase = u_terrainDecorationParams.x * 1.6 + dot(i_data0.xy, vec2(0.003, 0.004));
    world.xy += vec2(sin(phase), cos(phase * 0.7)) * i_data1.z * a_position.z * a_position.z;
    gl_Position = mul(u_viewProj, vec4(world, 1.0));
    v_worldPosition = world;
    v_texcoord0 = a_texcoord0;
    v_texcoord1 = vec4(0.0, i_data1.w, fade, seed);
    v_flowInfo = vec4(i_data3.w, 0.0, 0.0, 0.0);
    v_depth = gl_Position.w;
    v_color0 = a_color0 * i_data2;
    v_sunlight = outdoorSunlight(i_data3.xyz);
}
