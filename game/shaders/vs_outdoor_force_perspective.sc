$input a_position, a_texcoord1, a_texcoord2, a_color0
$output v_color0, v_texcoord1, v_screenspace

#include "common.sh"

void main()
{
    float reciprocalW = a_texcoord2;
    vec4 forcePosition = vec4(
        a_position.x * reciprocalW,
        a_position.y * reciprocalW,
        a_position.z * reciprocalW - 0.000001,
        reciprocalW);
    gl_Position = mul(u_modelViewProj, forcePosition);
    v_color0 = a_color0;
    v_texcoord1 = vec4(a_texcoord1.xy * a_texcoord1.z, 0.0, a_texcoord1.z);
    v_screenspace = a_texcoord1.w;
}
