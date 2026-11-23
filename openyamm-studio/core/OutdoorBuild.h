#pragma once

#include "core/IndoorBuild.h"

#include <array>
#include <cstdint>
#include <optional>
#include <utility>
#include <vector>

namespace OpenYAMM::Studio
{
// The build of a new outdoor project (project.yml `kind: outdoor`, without `base`): a classic ODM, the form of the
// outdoor maps of Might and Magic 6 to 8: the land, the ground and the roads (core/OutdoorLowering,
// core/OutdoorGround), the buildings (core/OutdoorBuildings), what else stands on the map with its events
// (core/OutdoorThings), spawn points and scattered decorations (core/OutdoorPlaces), the party start and the
// arrival points of those who come from a neighbour. What the sketch says and the build does not make is named in
// the result's warnings.

// The checks of an outdoor project that need the lowering: what `oymap validate` adds to the schemas and the
// sketch's own checks. Does nothing for a project without a sketch.
void validateOutdoorProject(const Project &project, std::vector<ProjectIssue> &issues);

// The same with an asset root at hand: also the names the build looks up there (decorations, monsters, textures),
// so `oymap validate --assets` refuses what `oymap build --assets` would. Issues already in `issues` are not
// added twice.
void validateOutdoorProject(
    const Project &project,
    const std::filesystem::path &assetRoot,
    std::vector<ProjectIssue> &issues);

// The same with the options of a validation (the asset root, its kept tables, where the view goes): true when the
// dry build got to its end (BuildOptions::pOutdoorView is filled then).
bool validateOutdoorProject(const Project &project, const BuildOptions &options, std::vector<ProjectIssue> &issues);

// Writes <stem>.odm, <stem>.scene.yml, <stem>.lua and build.json into the output directory. The ODM is written by
// the game's own writer (Game::OutdoorMapDataWriter, the one the editor's outdoor build uses) and read back: by the
// game's loaders in memory, and, when the options name an asset root, through core/MapLoad from a mount folder as
// the game would read it. True when the map was built (and, unless dryRun, written) without issues.
bool buildOutdoorProject(const Project &project, const BuildOptions &options, BuildResult &result);

struct LoweredOutdoorMap;

// F28 (tools/xeen/town_fit_check.py `gates.road_off`): the build's warnings for a way through a wall (each `gates`
// entry of a `kind: wall`, its passage `width` along the wall's line at its `at`) or a bridge's head (across each end
// of a `kind: bridge`'s line, its `width` wide) whose road tiles are centred more than 128 off the passage's middle:
// the road runs into the tower beside the arch. Road tiles are whole cells, so a gate or a bridge on a cell line (not
// on x.5) has its road on one side of its middle. Measured on the lowered map's tiles (the road set, local tiles 198
// to 233) along the passage and a cell beyond each end, 0.4 of a cell each side of it.
std::vector<std::string> outdoorRoadOffWarnings(const Project &project, const LoweredOutdoorMap &lowered);

// A way from an outdoor project's map to a neighbour across a side of the map (project.yml `neighbours` with
// `kind: edge` and a `side`).
struct OutdoorTravelEdge
{
    // The neighbour's id in project.yml.
    std::string id;
    // north, south, east or west: the side of this map the party leaves by, and arrives at coming back.
    std::string side;
    // The neighbour's map file.
    std::string map;
    // The side of the neighbour the party enters: `arrival_side`, else the side across.
    std::string arrivalSide;
    int days = 0;
    // The neighbour's own row is left as it is (`one_way`, `listed_only`).
    bool oneWay = false;
    // `span`: the stretch of the side this neighbour covers, [from, to] in units along it (x for north and south, y
    // for east and west). Such a neighbour is no row of the travel table, which has one map per side: the world's
    // edge_spans table holds it (game/tables/MapStats.h MapEdgeSpan), written by the world's own generator.
    std::optional<std::pair<int, int>> span;
};

std::vector<OutdoorTravelEdge> outdoorTravelEdges(const Project &project);

// Writes the project's row of outdoor_travels.txt (the table at `tablePath`, replaced by rename), and points each
// neighbour's row back at the project's map. `changes` says what was written, a line a way. Does nothing for a
// project that is not outdoor or has no edge neighbour. The method is told at the top of OutdoorInstall.cpp.
bool upsertOutdoorTravelRows(
    const Project &project,
    const std::filesystem::path &tablePath,
    std::vector<std::string> &changes,
    std::string &errorMessage);

// What a project says of its map's row in bolster_maps.txt: the continent (its skies, colours and journal), rain and
// snow by the world's chances, and how the map's monsters are strengthened. The method is told in OutdoorInstall.cpp.
struct OutdoorWeatherRow
{
    // False for a project that gets no row: an overlay, without a map_stats id, or an indoor project without
    // map_stats.bolster (S8g: an indoor map's row is opt-in).
    bool written = false;
    // map_stats.bolster, the row's `Bolster kind` as the game reads it (LowerToEqual, AllToEqual, OriginalStats, 0 for
    // none); empty: the reference's, else none.
    std::string bolster;
    // The map's number (project.yml map_stats.id) and name.
    std::string id;
    std::string note;
    // The shipped map whose row is the template (map_stats.reference, lower case); empty for none.
    std::string reference;
    // map_stats.continent, else the world's own; `continentGiven` when the project names it.
    int continent = 0;
    bool continentGiven = false;
    // atmosphere.yml `weather`: rain and snow by the world's chances; `weatherGiven` when the project has it.
    bool weatherGiven = false;
    bool rain = false;
    bool snow = false;
    // atmosphere.yml `sky`: one sky for every weather; empty for the continent's skies.
    std::string sky;
};

OutdoorWeatherRow outdoorWeatherRow(const Project &project);

// Writes the project's row of bolster_maps.txt in `tablesDirectory` (replaced by rename), reading the reference
// map's number from the map_stats.txt beside it. `changes` gets a line that says what the row holds. Does nothing
// for a project that gets no row.
bool upsertOutdoorWeatherRow(
    const Project &project,
    const std::filesystem::path &tablesDirectory,
    std::vector<std::string> &changes,
    std::string &errorMessage);

// The void cells of a lowering (LoweredOutdoorMap::voidCells, 128 x 128) as the scene's terrain.void rectangles
// [x0, y0, x1, y1], inclusive: each row's runs, stacked while a run's span repeats on the next row.
std::vector<std::array<int, 4>> outdoorVoidRectangles(const std::vector<uint8_t> &voidCells);

// atmosphere.yml `sky_theme`, empty when the project names none.
std::string outdoorSkyTheme(const Project &project);

// Points the map at its sky theme in `skyFile` (engine/rendering/sky/sky.yml of a scratch root or a mount): the
// line `  <map>.odm: <theme>` in the file's `maps` block, replacing an older line of the map; the file is
// replaced by rename. Does nothing for a project without `sky_theme`. Pure text in, text out: `withSkyTheme`.
std::string withSkyTheme(const std::string &text, const std::string &mapFile, const std::string &theme);
bool upsertOutdoorSkyTheme(
    const Project &project,
    const std::filesystem::path &skyFile,
    std::vector<std::string> &changes,
    std::string &errorMessage);
}
