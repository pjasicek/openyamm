#pragma once

#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// `oymap ground`: the ground rasteriser (core/GroundTerrain.h) on a built BLV and a `ground` block, outside a project
// (the parity run against an MM9 region's terrain_blend.py output).
int runGround(const std::vector<std::string> &arguments);
}
