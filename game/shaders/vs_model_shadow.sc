$input a_position, a_texcoord0, a_indices, a_weight, a_texcoord5, a_texcoord3
$output v_texcoord0

#include "common.sh"
#include "model_skin.sh"

void main()
{
    mat4 skin = u_modelSkin.x > 0.5
        ? modelSkinMatrix(u_modelSkin.z, a_weight, a_indices, a_texcoord3, a_texcoord5) : u_model[0];
    vec3 position = mul(skin, vec4(a_position, 1.0)).xyz;
    gl_Position = mul(u_viewProj, vec4(position, 1.0));
    v_texcoord0 = a_texcoord0;
}
