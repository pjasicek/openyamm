$input v_worldPosition, v_worldNormal, v_texcoord1

#define TERRAIN_VARYING v_texcoord1
#define BAKED_SOURCES 1
#define CONTINUOUS_BANK_PROJECTION 1
#include "outdoor_terrain_materials.sh"
