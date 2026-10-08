#pragma once

#include <string>
#include <unordered_map>
#include <utility>

namespace OpenYAMM::Game
{
constexpr const char *DefaultWorldId = "mm8";

std::string normalizeWorldId(const std::string &worldId);
std::string normalizeMapFileStem(const std::string &fileName);
std::string inferWorldIdFromMapFileName(const std::string &fileName, const std::string &fallbackWorldId);
std::string buildCanonicalMapId(const std::string &worldId, const std::string &fileName);

// Save migration: moves a map state stored under a canonical id the map no longer has. An existing entry under the
// current id wins.
template <typename State>
void migrateMapStateKey(
    std::unordered_map<std::string, State> &states,
    const std::string &legacyCanonicalId,
    const std::string &canonicalId)
{
    if (states.contains(canonicalId))
    {
        return;
    }

    auto node = states.extract(legacyCanonicalId);

    if (!node.empty())
    {
        node.key() = canonicalId;
        states.insert(std::move(node));
    }
}
}
