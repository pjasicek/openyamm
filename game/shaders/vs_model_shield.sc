$input a_position, a_normal, a_texcoord0, a_indices, a_weight, a_texcoord5, a_texcoord3
$output v_worldPosition, v_worldNormal

#include "common.sh"
#include "model_skin.sh"

// Energy shield shell over a creature (ModelShieldShell, fs_model_shield): the posed surface pushed out along its
// normals, swelling as it shatters.
uniform mat4 u_modelNormalMatrix;
// 0: colour rgb, strength; 1: seconds, break age, raise age, pool fraction; 2: foot z, body height, glow weight,
// thickness; 3: camera xyz; 4-7: hits (world xyz, age).
uniform vec4 u_shieldShell[8];

void main()
{
    bool skinned = u_modelSkin.x > 0.5;
    mat4 skin = skinned ? modelSkinMatrix(u_modelSkin.z, a_weight, a_indices, a_texcoord3, a_texcoord5) : u_model[0];
    vec3 worldPosition = mul(skin, vec4(a_position, 1.0)).xyz;
    vec3 worldNormal = skinned ? normalize(mul(skin, vec4(a_normal, 0.0)).xyz)
        : normalize(mul(u_modelNormalMatrix, vec4(a_normal, 0.0)).xyz);
    float breakAge = u_shieldShell[1].y;
    float thickness = u_shieldShell[2].w;
    float swell = breakAge >= 0.0 ? smoothstep(0.0, 0.7, breakAge) * thickness * 5.0 : 0.0;
    v_worldPosition = worldPosition + worldNormal * (thickness + swell);
    v_worldNormal = worldNormal;
    gl_Position = mul(u_viewProj, vec4(v_worldPosition, 1.0));
}
