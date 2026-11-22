#pragma once

#include <array>
#include <compare>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// A surface's `translucent` (the scene's `translucent_faces`, devdocs/INDOOR_TRANSLUCENT_FACES.md): drawn blended
// over what lies behind, still a solid face.
struct GlbFaceTranslucency
{
    double opacity = 1.0;
    std::array<double, 3> tint = {1.0, 1.0, 1.0};
    bool twoSided = false;

    auto operator<=>(const GlbFaceTranslucency &) const = default;
};

// One polygon of a mesh node: its corners in order (the winding gives the front) and their texture coordinates.
struct GlbFace
{
    std::string material;
    std::vector<std::array<float, 3>> positions;
    std::vector<std::array<float, 2>> uvs;
    // Engine face attribute bits the build sets on the compiled face (a surface's `liquid` and `flow`); not written
    // into the file.
    uint32_t attributes = 0;
    // Drawn translucent (a surface's `translucent`); not written into the file.
    std::optional<GlbFaceTranslucency> translucency;
    // The project object the face was lowered from (S5_BROWSER_EDITOR.md 2.9, provenance): a top-level id, with the
    // wall where the lowering knows it (room:hall/walls/3); empty where it is not stamped yet. Not written into the
    // file; the view mesh carries it.
    std::string owner;
};

struct GlbNode
{
    std::string name;
    std::vector<GlbFace> faces;
};

// A binary glTF file for the indoor compiler: one node and mesh per GlbNode, one triangle-fan primitive per face (the
// compiler keeps a fan as one polygon when triangulate_ngons is off), positions as given (Z up, map units), one
// material per name. The bytes depend only on the input.
std::vector<uint8_t> writeGlb(const std::vector<GlbNode> &nodes, const std::string &generator);
}
