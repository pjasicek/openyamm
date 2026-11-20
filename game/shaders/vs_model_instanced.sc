$input a_position, a_normal, a_texcoord0, a_color0, i_data0, i_data1, i_data2, i_data3, i_data4
$output v_texcoord0, v_worldNormal, v_worldPosition, v_color0, v_texcoord1, v_flowInfo, v_sector

#include "common.sh"
#include "model_static.sh"

uniform vec4 u_modelCamera;
uniform vec4 u_modelOutline;

void main()
{
    mat4 model = modelStaticMatrix(i_data0, i_data1, i_data2);
    vec3 position = u_modelStatic[2].y > 0.0
        ? modelStaticFlutter(a_position, a_normal, a_texcoord0, a_color0.a, model) : a_position;
    v_worldPosition = modelStaticPosition(position, u_modelCamera.xyz, model);
    gl_Position = mul(u_viewProj, vec4(v_worldPosition, 1.0));
    v_texcoord0 = modelStaticTexcoord(a_texcoord0, model);
    v_worldNormal = modelStaticNormal(a_normal, u_modelCamera.xyz, model);
    if (u_modelOutline.w > 0.5 && u_modelOutline.w < 1.5)
    {
        // Hover outline shell (1), as in vs_model; 2 is the depth prepass, unchanged: about 2-3 pixels at any distance.
        float thickness = clamp(length(v_worldPosition - u_modelCamera.xyz) * 0.005, 0.5, 24.0);
        v_worldPosition += normalize(v_worldNormal) * thickness;
        gl_Position = mul(u_viewProj, vec4(v_worldPosition, 1.0));
    }
    v_color0 = i_data3;
    // i_data4.w packs the LOD crossfade (0..2) with the indoor sector: crossfade + 4 x (sector + 1). The varying
    // packs the crossfade with the leaves' sun-shadow lift for fs_model.sc instead: crossfade + 4 x lift, the lift in
    // whole world units (u_modelStatic[3].w: a share of the model's height, scaled by the placement; at most 32).
    float placementScale = length(mul(model, vec4(1.0, 0.0, 0.0, 0.0)).xyz);
    float shadowLift = floor(min(u_modelStatic[3].w * placementScale, 32.0) + 0.5);
    v_texcoord1 = vec4(i_data4.xyz, mod(i_data4.w, 4.0) + 4.0 * shadowLift);
    v_sector = floor(i_data4.w * 0.25) - 1.0;
    // Alpha (the flutter weight here) carries the emission scale to the fragment shader.
    v_flowInfo = vec4(a_color0.rgb, modelStaticPulse(model));
}
