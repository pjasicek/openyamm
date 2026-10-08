$input a_position, a_normal, a_texcoord0, a_color0, i_data0, i_data1, i_data2, i_data3, i_data4
$output v_texcoord0

#include "common.sh"
#include "model_static.sh"

void main()
{
    // Billboards cast no shadow, so no camera position is needed here.
    vec3 position = u_modelStatic[2].y > 0.0 ? modelStaticFlutter(a_position, a_normal, a_texcoord0, a_color0.a)
        : a_position;
    gl_Position = mul(u_viewProj, vec4(modelStaticPosition(position, vec3(0.0, 0.0, 0.0)), 1.0));
    v_texcoord0 = modelStaticTexcoord(a_texcoord0);
}
