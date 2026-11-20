$input v_texcoord0
#include "common.sh"
#include "ambient_occlusion.sh"

// Screen-space reflections of surface materials (surface_material.sh): the world position of every half-resolution
// pixel relative to the camera it was seen from (half floats keep their precision near the camera), a = 0 for the sky.
uniform mat4 u_reflectionInverseView;
// xyz: the camera position.
uniform vec4 u_reflectionHistoryCamera;

void main()
{
    float depth = aoDepth(v_texcoord0);
    if (depth >= 0.999999)
    {
        gl_FragColor = vec4(0.0, 0.0, 0.0, 0.0);
        return;
    }
    vec3 world = mul(u_reflectionInverseView, vec4(aoViewPosition(v_texcoord0, depth), 1.0)).xyz;
    gl_FragColor = vec4(world - u_reflectionHistoryCamera.xyz, 1.0);
}
