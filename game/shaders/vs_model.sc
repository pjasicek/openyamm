$input a_position, a_normal, a_texcoord0, a_indices, a_weight, a_texcoord5, a_texcoord3
$output v_texcoord0, v_worldNormal, v_worldPosition

#include "common.sh"
#include "model_skin.sh"

uniform mat4 u_modelNormalMatrix;
uniform vec4 u_modelOutline;
uniform vec4 u_modelCamera;

void main()
{
    v_worldPosition = u_modelSkin.x > 0.5 ? modelSkinnedPosition(a_position)
        : mul(u_model[0], vec4(a_position, 1.0)).xyz;
    gl_Position = mul(u_viewProj, vec4(v_worldPosition, 1.0));
    v_texcoord0 = a_texcoord0;
    v_worldNormal = u_modelSkin.x > 0.5 ? modelSkinnedNormal(a_normal)
        : mul(u_modelNormalMatrix, vec4(a_normal, 0.0)).xyz;
    if (u_modelOutline.w > 0.5)
    {
        float thickness = clamp(length(v_worldPosition - u_modelCamera.xyz) * 0.0015, 0.15, 8.0);
        vec3 outlined = v_worldPosition + normalize(v_worldNormal) * thickness;
        gl_Position = mul(u_viewProj, vec4(outlined, 1.0));
    }
}
