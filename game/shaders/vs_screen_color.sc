$input a_position, a_color0
$output v_color0

#include "common.sh"

void main()
{
    // Clip-space coordinates keep screen effects independent of camera projection and near clipping.
    gl_Position = vec4(a_position, 1.0);
    v_color0 = a_color0;
}
