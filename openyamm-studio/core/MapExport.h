#pragma once

#include "core/Json.h"

#include <array>
#include <cstdint>
#include <filesystem>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
enum class MapKind
{
    Unknown,
    Outdoor,
    Indoor,
};

struct MapExportOptions
{
    // Counts, bounds and names only: no vertex, face, height or tile data.
    bool summaryOnly = false;
    // An outdoor map's void (its scene's terrain.void rectangles), written as terrain.void.
    std::vector<std::array<int, 4>> voidRects;
};

// The terrain.void rectangles [x0, y0, x1, y1] of an outdoor scene's text; empty without any or on a bad scene.
std::vector<std::array<int, 4>> sceneVoidRectangles(const std::string &sceneText);

MapKind mapKindFromPath(const std::filesystem::path &path);
bool readFileBytes(const std::filesystem::path &path, std::vector<uint8_t> &bytes, std::string &errorMessage);

// Writes one map (an .odm or .blv file's bytes) as a JSON object: the supported reader for scripts
// (`oymap export`, PLAN.md section 7). Field names follow the engine's structs in snake case.
bool exportMapJson(
    MapKind kind,
    const std::vector<uint8_t> &bytes,
    const MapExportOptions &options,
    JsonWriter &writer,
    std::string &errorMessage);
}
