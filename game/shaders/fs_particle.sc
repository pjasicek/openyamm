$input v_texcoord0, v_color0

#include "common.sh"

SAMPLER2D(s_texColor, 0);

void main()
{
    vec4 textureColor = texture2D(s_texColor, v_texcoord0);
    gl_FragColor = vec4(textureColor.rgb * v_color0.rgb, textureColor.a * v_color0.a);
}
