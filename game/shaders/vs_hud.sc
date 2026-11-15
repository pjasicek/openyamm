$input a_position, a_texcoord0, a_color0
$output v_texcoord0, v_color0, v_screenspace

#include "common.sh"

// The HUD draw list's one program (devdocs/HUD_RENDERING.md): screen pixels in a_position.xy, the vertex's alpha
// cut in a_position.z.
void main()
{
    gl_Position = mul(u_viewProj, vec4(a_position.xy, 0.0, 1.0));
    v_texcoord0 = a_texcoord0;
    v_color0 = a_color0;
    v_screenspace = a_position.z;
}
