$input v_texcoord1

#include "common.sh"

// Upscales the reduced-resolution Enhanced sky into the main sky view.
SAMPLER2D(s_skyImage, 0);

// x: 1 when render targets have a bottom-left origin (OpenGL), 0 otherwise.
uniform vec4 u_skyUpscale;

void main()
{
    vec2 uv = v_texcoord1.xy * 0.5 + 0.5;
    uv.y = u_skyUpscale.x > 0.5 ? uv.y : 1.0 - uv.y;
    gl_FragColor = vec4(texture2D(s_skyImage, uv).rgb, 1.0);
}
