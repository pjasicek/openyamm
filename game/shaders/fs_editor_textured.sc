$input v_texcoord0

#include "common.sh"

SAMPLER2D(s_texColor, 0);

void main()
{
    vec4 textureColor = texture2D(s_texColor, v_texcoord0);

    if (textureColor.a <= 0.001)
    {
        discard;
    }

    gl_FragColor = textureColor;
}
