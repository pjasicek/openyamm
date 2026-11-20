#pragma once

#include "core/Json.h"

#include <filesystem>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// The world view (S5_BROWSER_EDITOR.md 6.3, deferred to S6: "the project list per map in S5, a world view later";
// S6_PLAN.md 2.9): the projects of a host's folders grouped by world, each a map of that world, linked where the map
// card's `neighbours` lead (exits, map edges, boats, falls ...) to another project's map or to a shipped map. A rebuild
// (map_stats.reference) or an overlay (base) stands for its original: a link to the original's file reaches it.
//
// Read from the map cards and the files that use a neighbour (objects.yml exits, sketch.yml, wiring.yml), without a
// build; the shipped maps are named from the asset root's map_stats when there is one.
struct WorldMapNode
{
    std::string world;
    // The map's file (a project's own: <id>.blv|.odm; an overlay's: its base; a shipped map: as the links name it).
    std::string map;
    // indoor, outdoor, or unknown (a map code without an extension).
    std::string kind;
    // new, rebuild, overlay, or shipped.
    std::string role;
    std::string name;
    // The project's index in the request; -1 for a shipped map.
    int project = -1;
    // A rebuild's original or an overlay's base.
    std::string standsFor;
};

struct WorldLink
{
    size_t from = 0;
    size_t to = 0;
    // The neighbour's id, its kind (edge, door, boat ...), side (map edges) and days.
    std::string id;
    std::string kind;
    std::string side;
    std::optional<int> days;
    // The map the card names.
    std::string target;
    // The link reaches a project that stands for the map it names (a rebuild or an overlay of it).
    bool viaOriginal = false;
    // The objects that use the neighbour (an exit, a door, a building's way out).
    std::vector<std::string> exits;
};

struct WorldGraph
{
    std::vector<WorldMapNode> maps;
    std::vector<WorldLink> links;
    // Projects left out: their index and why.
    std::vector<std::pair<int, std::string>> skipped;
};

// The graph of `projects` (folders), only of `world` when it is not empty. `assetRoot` (optional) names the shipped
// maps.
WorldGraph readWorldGraph(const std::vector<std::filesystem::path> &projects, const std::string &world,
    const std::filesystem::path &assetRoot);

// world.view's result members: {worlds: [{world, maps, links}], skipped}.
void writeWorldGraph(const WorldGraph &graph, JsonWriter &writer);
}
