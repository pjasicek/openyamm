$input v_texcoord0, v_color0

#include "common.sh"

SAMPLER2D(s_texColor, 0);

uniform vec4 u_billboardAmbient;

void main()
{
    vec4 textureColor = texture2D(s_texColor, v_texcoord0);
    vec3 litColor = textureColor.rgb * (u_billboardAmbient.rgb + v_color0.rgb);
    gl_FragColor = vec4(litColor, textureColor.a * v_color0.a);
}
