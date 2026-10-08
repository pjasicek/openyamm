$input a_position, a_normal, a_texcoord0, a_color0, i_data0, i_data1, i_data2, i_data3, i_data4
$output v_texcoord0, v_worldNormal, v_worldPosition, v_color0, v_texcoord1, v_flowInfo

#include "common.sh"
#include "model_static.sh"

uniform vec4 u_modelCamera;
uniform vec4 u_modelOutline;

void main()
{
    vec3 position = u_modelStatic[2].y > 0.0 ? modelStaticFlutter(a_position, a_normal, a_texcoord0, a_color0.a)
        : a_position;
    v_worldPosition = modelStaticPosition(position, u_modelCamera.xyz);
    gl_Position = mul(u_viewProj, vec4(v_worldPosition, 1.0));
    v_texcoord0 = modelStaticTexcoord(a_texcoord0);
    v_worldNormal = modelStaticNormal(a_normal, u_modelCamera.xyz);
    if (u_modelOutline.w > 1.5)
    {
        // Hover outline shell (1 = the depth prepass, unchanged): about 2-3 pixels at any distance.
        float thickness = clamp(length(v_worldPosition - u_modelCamera.xyz) * 0.005, 0.5, 24.0);
        v_worldPosition += normalize(v_worldNormal) * thickness;
        gl_Position = mul(u_viewProj, vec4(v_worldPosition, 1.0));
    }
    v_color0 = i_data3;
    v_texcoord1 = i_data4;
    v_flowInfo = a_color0;
}
