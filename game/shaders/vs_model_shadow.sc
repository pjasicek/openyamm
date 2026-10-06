$input a_position, a_texcoord0, a_indices, a_weight, a_texcoord5, a_texcoord3
$output v_texcoord0

#include "common.sh"
#include "model_skin.sh"

void main()
{
    vec3 position = u_modelSkin.x > 0.5 ? modelSkinnedPosition(a_position)
        : mul(u_model[0], vec4(a_position, 1.0)).xyz;
    gl_Position = mul(u_viewProj, vec4(position, 1.0));
    v_texcoord0 = a_texcoord0;
}
