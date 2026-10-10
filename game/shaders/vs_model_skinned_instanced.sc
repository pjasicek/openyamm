$input a_position, a_normal, a_texcoord0, a_indices, a_weight, a_texcoord5, a_texcoord3, i_data0, i_data1
$output v_texcoord0, v_worldNormal, v_worldPosition, v_color0, v_texcoord1, v_flowInfo

#include "common.sh"
#include "model_skin.sh"

// Instanced skinned creatures: one draw per primitive and material for every creature that shares them.
// i_data0: ambient light (rgb) and sun visibility (a), as on static placements; i_data1.w: the creature's first row
// in the shared joint palette. The palette is already in world space, so there is no model matrix.
void main()
{
    mat4 skin = modelSkinMatrix(i_data1.w);
    v_worldPosition = mul(skin, vec4(a_position, 1.0)).xyz;
    gl_Position = mul(u_viewProj, vec4(v_worldPosition, 1.0));
    v_texcoord0 = a_texcoord0;
    v_worldNormal = normalize(mul(skin, vec4(a_normal, 0.0)).xyz);
    v_color0 = i_data0;
    v_texcoord1 = vec4(0.0, 0.0, 0.0, 0.0);
    v_flowInfo = vec4(1.0, 1.0, 1.0, 1.0);
}
