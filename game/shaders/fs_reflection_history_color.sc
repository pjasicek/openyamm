$input v_texcoord0
#include "common.sh"

// Screen-space reflections of surface materials (surface_material.sh): the finished world's colour at half
// resolution, the image the next frame's smooth faces reflect. One bilinear tap averages the 2 x 2 source texels.
SAMPLER2D(s_reflectionScene, 0);

void main()
{
    gl_FragColor = vec4(texture2D(s_reflectionScene, v_texcoord0).rgb, 1.0);
}
