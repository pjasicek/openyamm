$input v_texcoord0
#include "common.sh"

SAMPLER2D(s_gradeScene, 0);
SAMPLER3D(s_gradeLut, 1);
uniform vec4 u_gradeParams;

void main()
{
    vec4 original = texture2D(s_gradeScene, v_texcoord0);
    vec3 uvw = clamp(original.rgb, 0.0, 1.0) * u_gradeParams.y + u_gradeParams.z;
    vec3 graded = texture3D(s_gradeLut, uvw).rgb;
    gl_FragColor = vec4(mix(original.rgb, graded, u_gradeParams.x), original.a);
}
