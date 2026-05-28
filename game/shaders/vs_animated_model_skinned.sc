$input a_position, a_normal, a_texcoord0, a_indices, a_weight
$output v_texcoord0, v_worldPosition, v_normal, v_depth

#include "common.sh"

uniform mat4 u_boneMatrices[128];

void main()
{
    mat4 skinMatrix =
        u_boneMatrices[int(a_indices.x)] * a_weight.x
        + u_boneMatrices[int(a_indices.y)] * a_weight.y
        + u_boneMatrices[int(a_indices.z)] * a_weight.z
        + u_boneMatrices[int(a_indices.w)] * a_weight.w;

    vec4 skinnedPosition = mul(skinMatrix, vec4(a_position, 1.0));
    vec3 skinnedNormal = mul(skinMatrix, vec4(a_normal, 0.0)).xyz;
    vec4 viewPosition = mul(u_modelView, skinnedPosition);
    gl_Position = mul(u_modelViewProj, skinnedPosition);
    v_texcoord0 = a_texcoord0;
    v_worldPosition = mul(u_model[0], skinnedPosition).xyz;
    v_normal = normalize(mul(u_model[0], vec4(skinnedNormal, 0.0)).xyz);
    v_depth = abs(viewPosition.z);
}
