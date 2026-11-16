#pragma once

#include <array>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// How a flat face lays its picture: the texels per map unit along the picture's width (u) and along its height (v),
// from its corners and their texture coordinates (the three corners that span the most area). Nothing for a face
// without area or whose coordinates do not change one way (a marker, a portal). A picture at its own size has 1 and
// 1; one squashed one way has two rates far apart (the user's walk through XD-01: a desk stretching a cabinet's
// four drawers over a front 224 wide and 72 high, 0.57 and 3.6).
std::optional<std::array<double, 2>> texelRates(
    const std::vector<std::array<double, 3>> &points, const std::vector<std::array<double, 2>> &texels);

// Whether a decoration hangs (from a chain, a hook, a wall or a ceiling) or floats by its nature, by its hint in
// decoration_data.txt (`chandelier`, `lantern`, `sconce`, `torch`, `cage`, `flag`, `stalagtite`, `buoy`, ...): such
// a thing needs nothing under it.
bool decorationHangs(const std::string &hint);
}
