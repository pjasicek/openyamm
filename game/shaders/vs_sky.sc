$input a_position
$output v_texcoord1

#include "common.sh"

void main()
{
    gl_Position = vec4(a_position, 1.0);
    v_texcoord1 = vec4(a_position.xy, 0.0, 0.0);
}
