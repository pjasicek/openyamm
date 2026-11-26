$input a_position, a_normal, a_texcoord0
$output v_worldPosition, v_worldNormal, v_texcoord0

#define TERRAIN_VARYING v_texcoord0
#define TERRAIN_ATTRIBUTE a_texcoord0
#include "outdoor_terrain_vertex.sh"
