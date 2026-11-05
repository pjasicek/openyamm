$input a_position, a_texcoord0, a_texcoord1, a_texcoord2, a_texcoord3, a_color0, a_tangent, a_bitangent, a_texcoord6
$output v_texcoord0, v_worldPosition, v_texcoord1, v_screenspace, v_flowInfo, v_color0, v_lightmapUv, v_gradientU, v_gradientV, v_faceInfo

#include "common.sh"

void main()
{
    vec4 worldPosition = vec4(a_position, 1.0);
    gl_Position = mul(u_modelViewProj, worldPosition);
    v_texcoord0 = a_texcoord0;
    v_worldPosition = worldPosition.xyz;
    v_texcoord1 = a_texcoord1;
    v_screenspace = a_texcoord2;
    v_flowInfo = a_texcoord3;
    v_color0 = a_color0;
    // No lightmap: the baked programs use vs_indoor_textured_baked.
    v_lightmapUv = vec2(0.0, 0.0);
    // The face's texture gradients (surface materials).
    v_gradientU = a_tangent;
    v_gradientV = a_bitangent;
    // The face's sector, back sector and daylight (one draw holds the faces of many sectors).
    v_faceInfo = a_texcoord6;
}
