$input a_position, a_texcoord0, a_texcoord1, a_texcoord3
$output v_texcoord0, v_depth, v_worldPosition, v_texcoord1, v_flowInfo

#include "common.sh"

void main()
{
    vec4 worldPosition = vec4(a_position, 1.0);
    vec4 viewPosition = mul(u_modelView, worldPosition);
    gl_Position = mul(u_modelViewProj, worldPosition);
    v_texcoord0 = a_texcoord0;
    v_depth = length(viewPosition.xyz);
    v_worldPosition = worldPosition.xyz;
    v_texcoord1 = a_texcoord1;
    v_flowInfo = a_texcoord3;
}
