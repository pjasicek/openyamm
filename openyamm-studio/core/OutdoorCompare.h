#pragma once

#include "core/Json.h"
#include "core/Preview.h"

#include "game/maps/TerrainTileData.h"
#include "game/outdoor/OutdoorMapData.h"

#include <array>
#include <cstdint>
#include <map>
#include <set>
#include <string>
#include <utility>
#include <vector>

namespace OpenYAMM::Studio
{
// How alike two outdoor maps are, layer by layer, on the terrain's own grid: the measure a rebuild of a shipped
// ODM is corrected by (`oymap compare` on outdoor maps). No game is run. The method is told at the top of
// OutdoorCompare.cpp; every part is 1 for two maps that are the same and counts only what the maps hold, so an
// empty layer in both maps is a part that agrees.

// One map as the comparison reads it.
struct OutdoorCompareSide
{
    std::string name;
    const Game::OutdoorMapData *pMap = nullptr;
    // The map's 256 local tiles as the game resolves them (Game::loadTerrainTileDescriptors). Empty: every cell is
    // read as plain ground of one kind, and the ground, water and road parts compare nothing.
    std::vector<Game::TerrainTileDescriptor> tiles;
    // What an event leads to, by event number: "house 12", "map d05.blv" (from the event flow). An event that is
    // not listed is compared as a plain event.
    std::map<int, std::string> eventTargets;
    // The events whose handler has no title and does nothing on any path (from the event flow): an event number on
    // faces or decorations that is no thing to click, not compared (Ravenshore's 478, 479, 491 to 493). An event the
    // flow does not list may still be a name the map's texts give, and is compared.
    std::set<int> emptyEvents;
    // When the map's script was read (`eventsRead`): the events it gives a handler (`handledEvents`, those the flow
    // lists) or a name (`namedEvents`: a title or hint, as Ravenshore's "The Dauntless", registered without a
    // handler). An event on faces or decorations with neither is no thing either (Harmondale's event 1,
    // `RegisterEvent(1, nil, nil)`, on the gate sign; an event number no script registers).
    bool eventsRead = false;
    std::set<int> handledEvents;
    std::set<int> namedEvents;
};

// The events an event flow (core/EventFlow's JSON) lists, with a handler.
std::set<int> outdoorFlowEvents(const std::string &eventFlowJson);

// How the comparison reads the maps.
struct OutdoorCompareOptions
{
    // The rim (the land beyond the square the party walks, nodes 19 to 109) is judged by its skyline seen from the
    // square's edge, and heights, relief and cliffs count only the square. False: the reading before 2026-11-13,
    // every node and cell node by node and no skyline in the score (it is still reported, with no weight).
    bool rimBySkyline = true;
};

struct OutdoorComparePart
{
    // heights, relief, cliffs, water, ground, roads, buildings, decorations, spawns, events, rim.
    std::string id;
    std::string title;
    // Share of the overall score, the weights of all parts adding up to 1.
    double weight = 0.0;
    double score = 1.0;
    // What the part counted, in one sentence.
    std::string detail;
};

// A building of one map with the building of the other map it was matched to.
struct OutdoorCompareBuilding
{
    // Index in the original (-1: only the rebuild has it) and in the rebuild (-1: only the original has it).
    int original = -1;
    int rebuilt = -1;
    std::string name;
    // The middle of its footprint, world units, and the footprint's area in square cells.
    double x = 0.0;
    double y = 0.0;
    double area = 0.0;
    // Of a matched pair: the share of the two footprints' union they both cover, and rebuilt minus original for
    // the height (top minus bottom) and the base (the bottom).
    double overlap = 0.0;
    double heightDelta = 0.0;
    double baseDelta = 0.0;
    // A building that one map or both cut into several models (a ring of four walls, a castle of sixteen models, a
    // ship of ten): every model of it in each map, by index; `original` and `rebuilt` are the largest of them.
    std::vector<int> originalModels;
    std::vector<int> rebuiltModels;
    std::vector<std::string> originalNames;
    std::vector<std::string> rebuiltNames;
};

// A thing at a place: a spawn point, an event's faces, a decoration with an event.
struct OutdoorComparePlace
{
    // What it is: "spawn 3", "house 12", "map d05.blv", "event".
    std::string what;
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
};

// A block of 16 x 16 cells.
struct OutdoorCompareRegion
{
    // 0 to 7 from the west and from the north; the name is the column's letter and the row's number ("C5").
    int column = 0;
    int row = 0;
    std::string name;
    double score = 1.0;
    // By part, in the order of OutdoorCompareResult::parts; -1 where neither map has anything of that part here.
    std::vector<double> partScores;
    // The differences, largest first, and the first three as one sentence.
    std::vector<std::string> differences;
    std::string sentence;
    // Rebuilt minus original over the block's nodes.
    double meanHeightDelta = 0.0;
    double meanAbsHeightDelta = 0.0;
    // The sight lines from the square's edge whose horizon in the original lies in this block, and the mean height
    // of that horizon above the eye, degrees, in each map.
    size_t skylineRays = 0;
    double originalSkyline = 0.0;
    double rebuiltSkyline = 0.0;
};

struct OutdoorCompareResult
{
    std::string originalName;
    std::string rebuiltName;
    double score = 0.0;
    std::vector<OutdoorComparePart> parts;

    // Heights over the 128 x 128 nodes, rebuilt minus original, map units.
    double heightCorrelation = 0.0;
    double meanHeightDelta = 0.0;
    double meanAbsHeightDelta = 0.0;
    double rmsHeightDelta = 0.0;
    // Share of nodes within 64, 128, 256 and 512 units.
    std::array<double, 4> heightWithin = {};
    // Mean of the cells' relief (highest corner minus lowest), original and rebuilt.
    double originalRelief = 0.0;
    double rebuiltRelief = 0.0;
    // Cells too steep to walk (relief over 512), and walkable in one map and not in the other (steep or water).
    size_t originalSteepCells = 0;
    size_t rebuiltSteepCells = 0;
    size_t walkableOnlyInOriginal = 0;
    size_t walkableOnlyInRebuilt = 0;
    // Water, in quarter cells (a shore tile holds water on some of its corners).
    size_t originalWaterQuarters = 0;
    size_t rebuiltWaterQuarters = 0;
    size_t sharedWaterQuarters = 0;
    // Ground kinds by name: quarter cells in the original, in the rebuild and in both at the same place.
    std::vector<std::string> groundKinds;
    std::vector<std::array<size_t, 3>> groundQuarters;
    size_t originalRoadCells = 0;
    size_t rebuiltRoadCells = 0;
    size_t sharedRoadCells = 0;
    size_t sameRoadTileCells = 0;
    // Buildings: matched pairs first, then the original's without a partner, then the rebuild's.
    std::vector<OutdoorCompareBuilding> buildings;
    size_t originalBuildings = 0;
    size_t rebuiltBuildings = 0;
    size_t matchedBuildings = 0;
    double footprintOverlap = 0.0;
    // Over the area under buildings in either map: how alike the buildings' tops are (0 where only one has one).
    double buildingForm = 0.0;
    // Models with area of their own, and those at least half under buildings of the other map.
    size_t originalModelsWithArea = 0;
    size_t rebuiltModelsWithArea = 0;
    size_t originalModelsFound = 0;
    size_t rebuiltModelsFound = 0;
    // Decorations by kind (the entity's name): count in the original and in the rebuild.
    std::vector<std::pair<std::string, std::array<size_t, 2>>> decorationKinds;
    size_t originalDecorations = 0;
    size_t rebuiltDecorations = 0;
    // Decorations without a partner of their kind within reach, in each map.
    std::vector<OutdoorComparePlace> unpairedOriginalDecorations;
    std::vector<OutdoorComparePlace> unpairedRebuiltDecorations;
    // What one map has and the other has not within reach.
    std::vector<OutdoorComparePlace> missingSpawns;
    std::vector<OutdoorComparePlace> extraSpawns;
    size_t originalSpawns = 0;
    size_t rebuiltSpawns = 0;
    std::vector<OutdoorComparePlace> missingEvents;
    std::vector<OutdoorComparePlace> extraEvents;
    size_t originalEvents = 0;
    size_t rebuiltEvents = 0;
    // The 64 regions, row by row from the north-west, and their indices from the worst up.
    std::vector<OutdoorCompareRegion> regions;
    std::vector<size_t> worstRegions;

    // What the pictures are drawn from. Per node (index y * 128 + x): heights in map units. Per cell: the ground
    // kind on its four corners (north-west, north-east, south-west, south-east; an index into `groundKinds`, the
    // water's among them), a road tile or none, and the building over each quarter cell squared again (a grid of
    // 1024 x 1024, 0 none, else the building's index + 1).
    std::vector<double> originalHeights;
    std::vector<double> rebuiltHeights;
    std::vector<std::array<uint8_t, 4>> originalGround;
    std::vector<std::array<uint8_t, 4>> rebuiltGround;
    std::vector<uint8_t> originalRoads;
    std::vector<uint8_t> rebuiltRoads;
    std::vector<uint16_t> originalFootprints;
    std::vector<uint16_t> rebuiltFootprints;
    std::vector<OutdoorComparePlace> originalDecorationPlaces;
    std::vector<OutdoorComparePlace> rebuiltDecorationPlaces;
    std::vector<OutdoorComparePlace> originalSpawnPlaces;
    std::vector<OutdoorComparePlace> rebuiltSpawnPlaces;
    std::vector<OutdoorComparePlace> originalEventPlaces;
    std::vector<OutdoorComparePlace> rebuiltEventPlaces;
    int waterKind = -1;
    // How the rim was judged (OutdoorCompareOptions::rimBySkyline).
    bool rimBySkyline = true;
    // The skyline over all sight lines: their number and the mean height of the horizon above the eye, degrees.
    size_t skylineRays = 0;
    double originalSkyline = 0.0;
    double rebuiltSkyline = 0.0;
};

// False with a message when a side is not an outdoor map with terrain.
bool compareOutdoorMaps(
    const OutdoorCompareSide &original,
    const OutdoorCompareSide &rebuilt,
    OutdoorCompareResult &result,
    std::string &errorMessage,
    const OutdoorCompareOptions &options = {});

// The report: the score with its parts, the totals of every layer, the regions and the worst of them.
void writeOutdoorCompareJson(const OutdoorCompareResult &result, JsonWriter &writer);

// Every difference: by region all that differs there, every building with its partner or without one, every spawn
// point and event one map has and the other has not, every decoration kind with its two counts.
void writeOutdoorDifferencesJson(const OutdoorCompareResult &result, JsonWriter &writer);

// The pictures, each with the file name it is written under (heights.png, ground.png, objects.png, regions.png):
// the original, the rebuild and their difference side by side, north up.
std::vector<std::pair<std::string, Image>> outdoorComparePictures(const OutdoorCompareResult &result);

// A shots file for calibration/outdoor_ingame.py: the twelve worst regions, each seen from its south edge.
std::string outdoorCompareShotsYaml(const OutdoorCompareResult &result);

// What the events of a map lead to, read from the event flow's JSON (core/EventFlow): "house <n>" for an event
// that enters a house, "map <file>" for one that moves the party to another map.
std::map<int, std::string> outdoorEventTargets(const std::string &eventFlowJson);

// The events of the flow whose handler has no title and no effect on any path.
std::set<int> outdoorEmptyEvents(const std::string &eventFlowJson);
}
