$input v_texcoord0, v_color0

#include "common.sh"

SAMPLER2D(s_texColor, 0);
uniform vec4 u_particleParams;

void main()
{
    vec4 textureColor = texture2D(s_texColor, v_texcoord0);
    float alpha = textureColor.a * v_color0.a;
    vec3 color = textureColor.rgb * v_color0.rgb;

    if (u_particleParams.x > 0.5)
    {
        color *= textureColor.a;
    }

    gl_FragColor = vec4(color, alpha);
}
