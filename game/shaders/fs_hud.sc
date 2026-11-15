$input v_texcoord0, v_color0, v_screenspace

#include "common.sh"

SAMPLER2D(s_texColor, 0);

// The texture times the vertex colour. v_screenspace is the alpha cut: texels at or below it are dropped (0.1 for
// untinted images, as the textured program the HUD used before; negative for none).
void main()
{
    vec4 textureColor = texture2D(s_texColor, v_texcoord0);
    if (textureColor.a <= v_screenspace)
    {
        discard;
    }

    gl_FragColor = textureColor * v_color0;
}
