$input a_position, a_texcoord0, a_texcoord1
$output v_texcoord0, v_worldPosition, v_texcoord1

#include "common.sh"

void main()
{
    vec4 worldPosition = vec4(a_position, 1.0);
    gl_Position = mul(u_modelViewProj, worldPosition);
    v_texcoord0 = a_texcoord0;
    v_worldPosition = worldPosition.xyz;
    v_texcoord1 = a_texcoord1;
}
