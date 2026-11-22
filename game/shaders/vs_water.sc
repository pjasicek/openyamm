$input a_position, a_normal, a_texcoord0, a_texcoord1, a_texcoord2, a_color0
$output v_worldPosition, v_worldNormal, v_texcoord0, v_texcoord1, v_color0

#include "common.sh"

void main()
{
    // Tar and lava sit a little above the ground and faces they cover: where their edge art blends them into the land
    // (and the materials terrain's smoothed ground meets them), the liquid is drawn over it instead of depth-fighting.
    // A mirror (3) stays on its plane: its reflection is captured about it.
    vec3 position = a_texcoord2 > 0.5 && a_texcoord2 < 2.5 ? a_position + a_normal * 3.0 : a_position;
    gl_Position = mul(u_modelViewProj, vec4(position, 1.0));
    v_worldPosition = position;
    v_worldNormal = a_normal;
    v_texcoord0 = a_texcoord0;
    // x: coverage layer (negative: flowing face or sprite), y: shoreline, z: liquid (0 water, 1 tar, 2 lava, 3 mirror).
    v_texcoord1 = vec4(a_texcoord1.xy, a_texcoord2, 0.0);
    v_color0 = a_color0;
}
