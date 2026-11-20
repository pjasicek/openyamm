#pragma once

#include "core/Json.h"

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
};

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
