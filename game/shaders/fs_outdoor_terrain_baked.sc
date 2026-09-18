$input v_texcoord0, v_depth, v_worldPosition, v_worldNormal, v_texcoord1, v_flowInfo, v_sunlight

#define TERRAIN_TEXTURE_ARRAY 1
#define BAKED_SOURCES 1
#include "outdoor_textured_fog.sh"
