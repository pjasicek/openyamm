$input v_texcoord0, v_color0

#include "common.sh"

SAMPLER2D(s_texColor, 0);
uniform vec4 u_particleParams;

void main()
{
    vec4 textureColor = texture2D(s_texColor, v_texcoord0);
    float alpha = textureColor.a * v_color0.a;
    vec3 color = textureColor.rgb * v_color0.rgb;

    // x: additive light, weighted by its opacity. y: MM9's additive sprites, as LithTech's ONE/ONE blend with the
    // default MODULATE texture stage: texture colour times vertex colour, weighted by neither the texture's alpha
    // (its glow textures are already dark where transparent) nor the vertex opacity.
    if (u_particleParams.x > 0.5 && u_particleParams.y < 0.5)
    {
        color *= alpha;
    }

    gl_FragColor = vec4(color, alpha);
}
