$input a_position, a_normal, a_texcoord1
$output v_worldPosition, v_worldNormal, v_texcoord1

#define TERRAIN_VARYING v_texcoord1
#define TERRAIN_ATTRIBUTE a_texcoord1
#include "outdoor_terrain_vertex.sh"
