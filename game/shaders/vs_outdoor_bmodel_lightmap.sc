$input a_position, a_color0, a_texcoord0, a_texcoord1, a_texcoord3, a_texcoord4, a_tangent, a_bitangent
$output v_texcoord0, v_depth, v_worldPosition, v_texcoord1, v_flowInfo, v_lightmapUv, v_color0, v_gradientU, v_gradientV

#include "common.sh"

void main()
{
    vec4 worldPosition = vec4(a_position, 1.0);
    vec4 viewPosition = mul(u_modelView, worldPosition);
    gl_Position = mul(u_modelViewProj, worldPosition);
    v_texcoord0 = a_texcoord0;
    v_depth = abs(viewPosition.z);
    v_worldPosition = worldPosition.xyz;
    v_texcoord1 = a_texcoord1;
    v_flowInfo = a_texcoord3;
    v_lightmapUv = a_texcoord4;
    v_color0 = a_color0;
    // The face's texture gradients (surface materials).
    v_gradientU = a_tangent;
    v_gradientV = a_bitangent;
}
