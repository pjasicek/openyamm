$input a_position, a_normal, a_texcoord0
$output v_worldPosition, v_worldNormal, v_texcoord0

#include "common.sh"

// The terrain loses depth ties to building faces. The smoothed terrain reaches but never crosses the height of a cell's
// highest vertex, where many building floors lie (Ravenshore's crystal plaza): without the offset the two z-fight, and
// the baked light of the terrain under the floor shows through in dark stripes. About 16 steps of a 24-bit depth
// buffer: a fraction of a unit within 2000 units of the camera.
#define TERRAIN_DEPTH_OFFSET 0.000002

void main()
{
    vec4 worldPosition = vec4(a_position, 1.0);
    gl_Position = mul(u_modelViewProj, worldPosition);
    // Clamped to the far plane, so the offset never clips distant terrain.
    gl_Position.z = min(gl_Position.z + TERRAIN_DEPTH_OFFSET * gl_Position.w, gl_Position.w);
    v_worldPosition = a_position;
    v_worldNormal = a_normal;
    v_texcoord0 = a_texcoord0;
}
