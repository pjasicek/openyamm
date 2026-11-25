#include "doctest/doctest.h"

#include "core/OutdoorCompare.h"
#include "core/OutdoorRoofCover.h"

#include <algorithm>
#include <functional>
#include <array>
#include <cmath>
#include <limits>
#include <set>

using namespace OpenYAMM::Studio;
namespace Game = OpenYAMM::Game;

namespace
{
constexpr int Side = 128;

// The sketch schema with its references within the file written out in place (S5b2 moved the building words into
// one $defs: a test that reads a word's description by its path reads it where it is used, as the form does).
YAML::Node inlinedSchemaNode(const YAML::Node &node, const YAML::Node &root, int depth)
{
    if (node.IsSequence())
    {
        YAML::Node copy(YAML::NodeType::Sequence);

        for (const YAML::Node &item : node)
        {
            copy.push_back(inlinedSchemaNode(item, root, depth));
        }

        return copy;
    }

    if (!node.IsMap())
    {
        return YAML::Clone(node);
    }

    YAML::Node copy(YAML::NodeType::Map);
    const YAML::Node reference = node["$ref"];
    const bool inlined = reference.IsDefined() && reference.Scalar().rfind("#/", 0) == 0 && depth < 16;

    if (inlined)
    {
        YAML::Node target = root;
        std::string pointer = reference.Scalar().substr(2);

        while (!pointer.empty())
        {
            const size_t slash = pointer.find('/');
            const std::string part = pointer.substr(0, slash);
            const YAML::Node next = target[part];
            target.reset(next);
            pointer = slash == std::string::npos ? std::string() : pointer.substr(slash + 1);
        }

        copy = inlinedSchemaNode(target, root, depth + 1);
    }

    for (YAML::const_iterator entry = node.begin(); entry != node.end(); ++entry)
    {
        if (!inlined || entry->first.Scalar() != "$ref")
        {
            copy[entry->first.Scalar()] = inlinedSchemaNode(entry->second, root, depth);
        }
    }

    return copy;
}

const YAML::Node &inlinedSketchSchema()
{
    static const YAML::Node inlined = inlinedSchemaNode(SchemaSet::builtIn().root("sketch.schema.json"),
        SchemaSet::builtIn().root("sketch.schema.json"), 0);
    return inlined;
}

// A tile table laid out as the shipped ones: dirt on the tiles 1 to 12, grass from 90, water from 126, rock from
// 162 and roads from 198, each set with its twelve tiles toward dirt at 12 to 23.
std::vector<Game::TerrainTileDescriptor> testTiles()
{
    std::vector<Game::TerrainTileDescriptor> tiles(256);

    for (Game::TerrainTileDescriptor &tile : tiles)
    {
        tile.textureName = "pending";
    }

    for (int tile = 1; tile <= 12; ++tile)
    {
        tiles[tile].textureName = "dirttyl";
        tiles[tile].tileset = 4;
    }

    const char *pNames[4] = {"grastyl", "wtrtyl", "rktyl", "drsrcros"};
    const uint16_t baseFlags[4] = {0, Game::TerrainTileFlagWater, 0, Game::TerrainTileFlagTransition};

    for (int set = 0; set < 4; ++set)
    {
        for (int offset = 0; offset < 36; ++offset)
        {
            Game::TerrainTileDescriptor &tile = tiles[90 + set * 36 + offset];
            tile.textureName = pNames[set];
            tile.tileset = static_cast<uint16_t>(set == 3 ? 10 : set);
            tile.variant = static_cast<uint16_t>(offset);
            tile.flags = offset >= 12 && offset < 24 && set != 3
                ? static_cast<uint16_t>(Game::TerrainTileFlagTransition | (set == 1 ? Game::TerrainTileFlagShore : 0))
                : baseFlags[set];
        }
    }

    return tiles;
}

// Level grass 320 high.
Game::OutdoorMapData testMap()
{
    Game::OutdoorMapData map;
    map.version = 8;
    map.heightMap.assign(Side * Side, 10);
    map.tileMap.assign(Side * Side, 90);
    map.attributeMap.assign(Side * Side, 0);
    return map;
}

// A box of a house: a floor, a roof and four walls, its south wall carrying an event.
Game::OutdoorBModel testHouse(int west, int south, int width, int depth, int base, int height, uint16_t event)
{
    Game::OutdoorBModel house;
    house.name = "house";

    for (int level = 0; level < 2; ++level)
    {
        const int z = base + level * height;
        house.vertices.push_back({west, south, z});
        house.vertices.push_back({west + width, south, z});
        house.vertices.push_back({west + width, south + depth, z});
        house.vertices.push_back({west, south + depth, z});
    }

    const uint16_t quads[6][4] = {{0, 3, 2, 1}, {4, 5, 6, 7}, {0, 1, 5, 4}, {1, 2, 6, 5}, {2, 3, 7, 6}, {3, 0, 4, 7}};

    for (int face = 0; face < 6; ++face)
    {
        Game::OutdoorBModelFace polygon;
        polygon.vertexIndices.assign(quads[face], quads[face] + 4);
        polygon.cogTriggeredNumber = face == 2 ? event : 0;
        house.faces.push_back(polygon);
    }

    return house;
}

Game::OutdoorEntity testDecoration(const std::string &name, int x, int y)
{
    Game::OutdoorEntity entity;
    entity.name = name;
    entity.decorationListId = 100;
    entity.x = x;
    entity.y = y;
    return entity;
}

Game::OutdoorSpawn testSpawn(int x, int y, uint16_t index)
{
    Game::OutdoorSpawn spawn;
    spawn.x = x;
    spawn.y = y;
    spawn.typeId = 3;
    spawn.index = index;
    spawn.radius = 32;
    return spawn;
}

// A map with something of every layer: a hill, a lake with its shore, a rock field, a road, two houses, trees,
// spawn points.
Game::OutdoorMapData testWorld()
{
    Game::OutdoorMapData map = testMap();

    for (int y = 20; y < 40; ++y)
    {
        for (int x = 20; x < 40; ++x)
        {
            const double reach = std::max(std::abs(x - 30), std::abs(y - 30));
            map.heightMap[y * Side + x] = static_cast<uint8_t>(10 + (10 - reach) * 6);
        }
    }

    for (int y = 70; y < 80; ++y)
    {
        for (int x = 70; x < 80; ++x)
        {
            map.tileMap[y * Side + x] = 126;
        }

        // The shore on the lake's west side: dirt along the west of the cell.
        map.tileMap[y * Side + 69] = 126 + 17;
    }

    for (int y = 100; y < 110; ++y)
    {
        for (int x = 10; x < 30; ++x)
        {
            map.tileMap[y * Side + x] = 162;
        }
    }

    for (int x = 40; x < 100; ++x)
    {
        map.tileMap[50 * Side + x] = 198 + 2;
    }

    map.bmodels.push_back(testHouse(1024, 1024, 1024, 768, 320, 512, 171));
    map.bmodels.push_back(testHouse(-9000, 4000, 1536, 1536, 320, 900, 172));

    for (int index = 0; index < 30; ++index)
    {
        map.entities.push_back(testDecoration(index % 3 == 0 ? "rock01" : "tree12", -20000 + index * 700,
            15000 - index * 300));
    }

    map.spawns.push_back(testSpawn(-12000, -12000, 1));
    map.spawns.push_back(testSpawn(18000, 9000, 2));
    map.spawns.push_back(testSpawn(3000, -22000, 3));
    return map;
}

OutdoorCompareSide sideOf(const Game::OutdoorMapData &map, const char *pName)
{
    OutdoorCompareSide side;
    side.name = pName;
    side.pMap = &map;
    side.tiles = testTiles();
    side.eventTargets = {{171, "house 2"}, {172, "map d05.blv"}};
    return side;
}

double partOf(const OutdoorCompareResult &result, const std::string &id)
{
    for (const OutdoorComparePart &part : result.parts)
    {
        if (part.id == id)
        {
            return part.score;
        }
    }

    return -1.0;
}

// `rimBySkyline` false: every node and cell node by node, the reading before 2026-11-13 (`--without rim`).
OutdoorCompareResult compared(const Game::OutdoorMapData &original, const Game::OutdoorMapData &rebuilt,
    bool rimBySkyline = true)
{
    OutdoorCompareResult result;
    std::string errorMessage;
    OutdoorCompareOptions options;
    options.rimBySkyline = rimBySkyline;
    REQUIRE(compareOutdoorMaps(sideOf(original, "original"), sideOf(rebuilt, "rebuilt"), result, errorMessage,
        options));
    return result;
}

// Every part of the score but the named ones is untouched (a part reported with no weight is not in the score).
void checkOnlyTheseDiffer(const OutdoorCompareResult &result, const std::vector<std::string> &ids)
{
    for (const OutdoorComparePart &part : result.parts)
    {
        if (part.weight <= 0.0)
        {
            continue;
        }

        const bool named = std::find(ids.begin(), ids.end(), part.id) != ids.end();
        CAPTURE(part.id);
        CHECK((part.score < 1.0) == named);
    }
}
}

TEST_CASE("two outdoor maps that are the same compare at 100 % in every part and every region")
{
    const Game::OutdoorMapData map = testWorld();
    const OutdoorCompareResult result = compared(map, map);
    CHECK(result.score == doctest::Approx(1.0));
    CHECK(result.parts.size() == 11);

    for (const OutdoorComparePart &part : result.parts)
    {
        CAPTURE(part.id);
        CHECK(part.score == doctest::Approx(1.0));
    }

    for (const OutdoorCompareRegion &region : result.regions)
    {
        CHECK(region.score == doctest::Approx(1.0));
        CHECK(region.differences.empty());
    }

    CHECK(result.matchedBuildings == 2);
    CHECK(result.missingSpawns.empty());
    CHECK(result.missingEvents.empty());
    CHECK(result.heightCorrelation == doctest::Approx(1.0));
    // 100 cells of lake and half of the ten shore cells.
    CHECK(result.originalWaterQuarters == 420);
    CHECK(result.originalRoadCells == 60);
    CHECK(result.originalEvents == 2);
    // The weights of the parts add up to the whole score.
    double weight = 0.0;

    for (const OutdoorComparePart &part : result.parts)
    {
        weight += part.weight;
    }

    CHECK(weight == doctest::Approx(1.0));
}

TEST_CASE("land raised by 256 over one region costs the heights part half of that region and names it")
{
    const Game::OutdoorMapData original = testMap();
    Game::OutdoorMapData rebuilt = original;

    // Region C5: columns 32 to 47, rows 64 to 79. Eight steps of 32 are 256 units.
    for (int y = 64; y < 80; ++y)
    {
        for (int x = 32; x < 48; ++x)
        {
            rebuilt.heightMap[y * Side + x] += 8;
        }
    }

    // Node by node over the whole map (C5 lies inside the playable square, so the skyline judging differs only in
    // counting the square's 91 x 91 nodes: checked at the end).
    const OutdoorCompareResult result = compared(original, rebuilt, false);
    // 256 of the 16384 nodes score a half.
    CHECK(partOf(result, "heights") == doctest::Approx(1.0 - 128.0 / 16384.0));
    CHECK(result.meanHeightDelta == doctest::Approx(256.0 * 256.0 / 16384.0));
    CHECK(result.heightWithin[1] == doctest::Approx(1.0 - 256.0 / 16384.0));
    CHECK(result.heightWithin[2] == doctest::Approx(1.0));
    const OutdoorCompareRegion &worst = result.regions[result.worstRegions[0]];
    CHECK(worst.name == "C5");
    CHECK(worst.partScores[0] == doctest::Approx(0.5));
    CHECK(worst.meanHeightDelta == doctest::Approx(256.0));
    CHECK(worst.sentence.find("256") != std::string::npos);
    CHECK(worst.sentence.find("higher") != std::string::npos);
    // The block's rim is a step of 256 in ground that was level: the relief part sees it, no cell is too steep.
    CHECK(partOf(result, "relief") < 1.0);
    CHECK(result.rebuiltSteepCells == 0);
    checkOnlyTheseDiffer(result, {"heights", "relief"});
    CHECK(result.score < 1.0);
    CHECK(result.score > 0.99);
    const OutdoorCompareResult square = compared(original, rebuilt);
    CHECK(partOf(square, "heights") == doctest::Approx(1.0 - 128.0 / (91.0 * 91.0)));
    CHECK(partOf(square, "rim") == doctest::Approx(1.0));
    checkOnlyTheseDiffer(square, {"heights", "relief"});
}

TEST_CASE("level ground where the original is rough loses the relief part, not the heights")
{
    Game::OutdoorMapData original = testMap();
    Game::OutdoorMapData rebuilt = original;

    // The original rises and falls by 4 steps (128 units) from node to node; the rebuild lies level in between.
    for (int y = 0; y < Side; ++y)
    {
        for (int x = 0; x < Side; ++x)
        {
            original.heightMap[y * Side + x] = static_cast<uint8_t>(((x + y) % 2) == 0 ? 8 : 12);
        }
    }

    const OutdoorCompareResult result = compared(original, rebuilt, false);
    // Every node is 64 off: 1 - 64 / 512.
    CHECK(partOf(result, "heights") == doctest::Approx(0.875));
    // Every cell rises 128 in the original and 0 in the rebuild.
    CHECK(partOf(result, "relief") == doctest::Approx(0.0));
    CHECK(result.originalRelief == doctest::Approx(128.0));
    CHECK(result.rebuiltRelief == doctest::Approx(0.0));
    checkOnlyTheseDiffer(result, {"heights", "relief"});
}

TEST_CASE("a cliff one cell aside still counts as that cliff; a cliff that is gone does not")
{
    Game::OutdoorMapData original = testMap();

    // A wall of 20 steps (640 units) along x = 60.
    for (int y = 0; y < Side; ++y)
    {
        for (int x = 60; x < Side; ++x)
        {
            original.heightMap[y * Side + x] = 30;
        }
    }

    Game::OutdoorMapData moved = testMap();

    for (int y = 0; y < Side; ++y)
    {
        for (int x = 61; x < Side; ++x)
        {
            moved.heightMap[y * Side + x] = 30;
        }
    }

    // Node by node over the whole map: the wall runs on through the rim.
    const OutdoorCompareResult aside = compared(original, moved, false);
    CHECK(aside.originalSteepCells == 127);
    CHECK(aside.rebuiltSteepCells == 127);
    CHECK(partOf(aside, "cliffs") == doctest::Approx(1.0));
    // The cells of the two cliff lines: each can be walked in one map only.
    CHECK(aside.walkableOnlyInOriginal == 127);
    CHECK(aside.walkableOnlyInRebuilt == 127);
    const OutdoorCompareResult gone = compared(original, testMap(), false);
    CHECK(partOf(gone, "cliffs") == doctest::Approx(0.0));
    CHECK(gone.walkableOnlyInRebuilt == 127);
}

TEST_CASE("water, ground kinds and roads are each counted on their own")
{
    const Game::OutdoorMapData original = testWorld();
    Game::OutdoorMapData dry = original;

    // The lake's east half becomes grass.
    for (int y = 70; y < 80; ++y)
    {
        for (int x = 75; x < 80; ++x)
        {
            dry.tileMap[y * Side + x] = 90;
        }
    }

    const OutdoorCompareResult water = compared(original, dry);
    // 220 of 420 quarter cells of water are left.
    CHECK(partOf(water, "water") == doctest::Approx(220.0 / 420.0));
    checkOnlyTheseDiffer(water, {"water", "ground"});

    Game::OutdoorMapData grassy = original;

    for (int y = 100; y < 110; ++y)
    {
        for (int x = 10; x < 30; ++x)
        {
            grassy.tileMap[y * Side + x] = 90;
        }
    }

    const OutdoorCompareResult ground = compared(original, grassy);
    // 200 cells of rock are grass now: of the land's quarters of either map, those do not agree.
    const double land = 128.0 * 128.0 * 4.0 - 420.0;
    CHECK(partOf(ground, "ground") == doctest::Approx((land - 800.0) / (land + 800.0)));
    checkOnlyTheseDiffer(ground, {"ground"});
    bool rockListed = false;

    for (size_t kind = 0; kind < ground.groundKinds.size(); ++kind)
    {
        if (ground.groundKinds[kind] == "rktyl")
        {
            rockListed = true;
            CHECK(ground.groundQuarters[kind][0] == 800);
            CHECK(ground.groundQuarters[kind][1] == 0);
        }
    }

    CHECK(rockListed);

    // The road one row aside is still that road, though no cell is shared; five rows aside it is another road.
    Game::OutdoorMapData beside = original;
    Game::OutdoorMapData far = original;

    for (int x = 40; x < 100; ++x)
    {
        beside.tileMap[50 * Side + x] = 90;
        beside.tileMap[51 * Side + x] = 198 + 2;
        far.tileMap[50 * Side + x] = 90;
        far.tileMap[55 * Side + x] = 198 + 2;
    }

    CHECK(partOf(compared(original, beside), "roads") == doctest::Approx(0.7));
    CHECK(partOf(compared(original, far), "roads") == doctest::Approx(0.0));
    // A road is dirt with a road on it: moving it moves dirt, which the ground part counts.
    checkOnlyTheseDiffer(compared(original, far), {"roads", "ground"});
}

TEST_CASE("a building is matched by its footprint: moved a little it is the same building, far away it is missing")
{
    const Game::OutdoorMapData original = testWorld();
    Game::OutdoorMapData nudged = original;
    nudged.bmodels[0] = testHouse(1024 + 256, 1024, 1024, 768, 320, 512, 171);
    const OutdoorCompareResult near = compared(original, nudged);
    CHECK(near.matchedBuildings == 2);
    CHECK(partOf(near, "buildings") < 1.0);
    CHECK(partOf(near, "buildings") > 0.8);
    // The event on its wall went with it, 256 aside: still paired.
    CHECK(partOf(near, "events") == doctest::Approx(1.0));
    checkOnlyTheseDiffer(near, {"buildings"});

    Game::OutdoorMapData away = original;
    away.bmodels[0] = testHouse(20000, -20000, 1024, 768, 320, 512, 171);
    const OutdoorCompareResult far = compared(original, away);
    CHECK(far.matchedBuildings == 1);
    CHECK(far.buildings.size() == 3);
    CHECK(far.buildings[1].rebuilt == -1);
    CHECK(far.buildings[2].original == -1);
    CHECK(far.missingEvents.size() == 1);
    CHECK(far.missingEvents[0].what == "house 2");
    CHECK(partOf(far, "events") == doctest::Approx(0.5));

    // Twice as high: the footprint agrees, the height does not.
    Game::OutdoorMapData tall = original;
    tall.bmodels[1] = testHouse(-9000, 4000, 1536, 1536, 320, 1800, 172);
    const OutdoorCompareResult higher = compared(original, tall);
    CHECK(higher.footprintOverlap == doctest::Approx(1.0));
    CHECK(higher.buildings[0].heightDelta + higher.buildings[1].heightDelta == doctest::Approx(900.0));
    // The form part (0.4 of the part) loses the taller house's whole area: its top is more than a storey off.
    CHECK(higher.buildingForm < 0.7);
    CHECK(higher.buildingForm > 0.2);
    CHECK(partOf(higher, "buildings") == doctest::Approx(0.6 + 0.4 * higher.buildingForm));
    CHECK(higher.originalModelsFound == 2);

    // A house cut into two models that cover the same ground is the same house: nothing is lost.
    Game::OutdoorMapData cut = original;
    cut.bmodels[0] = testHouse(1024, 1024, 512, 768, 320, 512, 171);
    cut.bmodels.push_back(testHouse(1024 + 512, 1024, 512, 768, 320, 512, 171));
    const OutdoorCompareResult halves = compared(original, cut);
    CHECK(halves.footprintOverlap == doctest::Approx(1.0));
    CHECK(halves.buildingForm == doctest::Approx(1.0));
    CHECK(partOf(halves, "buildings") == doctest::Approx(1.0));

    // The same house with another event behind its door is not the same entrance.
    OutdoorCompareSide relabelled = sideOf(original, "rebuilt");
    relabelled.eventTargets[171] = "house 3";
    OutdoorCompareResult result;
    std::string errorMessage;
    REQUIRE(compareOutdoorMaps(sideOf(original, "original"), relabelled, result, errorMessage));
    CHECK(partOf(result, "events") == doctest::Approx(0.5));
}

TEST_CASE("decorations count by kind and by density, spawn points by place and slot")
{
    const Game::OutdoorMapData original = testWorld();
    Game::OutdoorMapData other = original;

    for (Game::OutdoorEntity &entity : other.entities)
    {
        entity.name = "plant04";
    }

    // As many in every region, none of the same kind: the density half is kept.
    CHECK(partOf(compared(original, other), "decorations") == doctest::Approx(0.5));
    Game::OutdoorMapData bare = original;
    bare.entities.clear();
    const OutdoorCompareResult none = compared(original, bare);
    CHECK(partOf(none, "decorations") == doctest::Approx(0.0));
    CHECK(none.decorationKinds.size() == 2);
    checkOnlyTheseDiffer(none, {"decorations"});

    Game::OutdoorMapData spawns = original;
    // One of another slot at its place, one moved out of reach, one kept.
    spawns.spawns[0].index = 3;
    spawns.spawns[1].x -= 6000;
    const OutdoorCompareResult result = compared(original, spawns);
    CHECK(partOf(result, "spawns") == doctest::Approx(1.5 / 3.0));
    CHECK(result.missingSpawns.size() == 1);
    CHECK(result.extraSpawns.size() == 1);
    checkOnlyTheseDiffer(result, {"spawns"});
}

TEST_CASE("the report and the pictures of an outdoor comparison are written, the same every time")
{
    const Game::OutdoorMapData original = testWorld();
    Game::OutdoorMapData rebuilt = testMap();
    const OutdoorCompareResult result = compared(original, rebuilt);
    CHECK(result.score < 0.9);
    JsonWriter first(true);
    writeOutdoorCompareJson(result, first);
    JsonWriter second(true);
    writeOutdoorCompareJson(compared(original, rebuilt), second);
    CHECK(first.text() == second.text());
    CHECK(first.text().find("\"worst_regions\"") != std::string::npos);
    JsonWriter differences(true);
    writeOutdoorDifferencesJson(result, differences);
    CHECK(differences.text().find("only in the original") != std::string::npos);
    CHECK(differences.text().find("map d05.blv") != std::string::npos);
    const std::vector<std::pair<std::string, Image>> pictures = outdoorComparePictures(result);
    REQUIRE(pictures.size() == 4);
    CHECK(pictures[0].first == "heights.png");
    CHECK(pictures[0].second.width == 1568);
    CHECK(!encodePng(pictures[1].second).empty());
    const std::string shots = outdoorCompareShotsYaml(result);
    CHECK(shots.find("region-") != std::string::npos);
    CHECK(outdoorEventTargets("[{\"event\":7,\"paths\":[{\"effects\":[\"EnterHouse(12)\"]}]},\n{\"event\":9,"
        "\"paths\":[{\"effects\":[\"leave to D05.blv at 1, 2, 3 (x)\"]}]},{\"event\":10,\"paths\":[]}]")
        == std::map<int, std::string>{{7, "house 12"}, {9, "map d05.blv"}});
}

// ---- The land, the ground and the roads of an outdoor project (core/OutdoorLowering, core/OutdoorGround) ----

#include "core/OutdoorBuild.h"
#include "core/OutdoorGround.h"
#include "core/OutdoorLowering.h"
#include "core/Schema.h"
#include "core/Sketch.h"

namespace
{
Project outdoorProject(const std::string &sketch, const char *pWorld = "mm8")
{
    const std::vector<std::pair<std::string, std::string>> files = {
        {"project.yml", std::string("format: 0\nid: groundtest\nworld: ") + pWorld + "\nkind: outdoor\n"},
        {"plan.yml", "format: 0\nentrances:\n  - {id: entrance:north, kind: arrival, facing: s}\n"
            "height_bands:\n  - {id: band:low, range: [576, 704]}\n  - {id: band:high, range: [2496, 2624]}\n"},
        {"sketch.yml", "format: 0\npoints:\n  - {id: entrance:north, at: [100, 50], facing: s}\n" + sketch},
    };
    Project project;

    for (const std::pair<std::string, std::string> &entry : files)
    {
        ProjectFile file;
        file.name = entry.first;
        file.text = entry.second;
        file.document = YAML::Load(entry.second);

        for (const ProjectFileKind &kind : projectFileKinds())
        {
            if (file.name == kind.pName)
            {
                file.schema = kind.pSchema;
            }
        }

        project.files[file.name] = file;
    }

    return project;
}

// Level land 640 high: one band over the whole map.
const char *LevelLand =
    "heights:\n  bands:\n    - {band: band:low, polygon: [[0, 0], [128, 0], [128, 128], [0, 128]]}\n";

LoweredOutdoorMap loweredOf(const std::string &sketch, const char *pWorld = "mm8")
{
    LoweredOutdoorMap lowered;
    std::vector<ProjectIssue> issues;
    const bool ok = lowerOutdoorProject(outdoorProject(sketch, pWorld), lowered, issues);

    for (const ProjectIssue &issue : issues)
    {
        MESSAGE(issue.file << ": " << issue.path << ": " << issue.message);
    }

    REQUIRE(ok);
    return lowered;
}

std::vector<ProjectIssue> refusedWith(const std::string &sketch, const char *pWorld = "mm8")
{
    LoweredOutdoorMap lowered;
    std::vector<ProjectIssue> issues;
    CHECK_FALSE(lowerOutdoorProject(outdoorProject(sketch, pWorld), lowered, issues));
    return issues;
}

bool anyIssue(const std::vector<ProjectIssue> &issues, const std::string &fragment)
{
    return std::any_of(issues.begin(), issues.end(), [&fragment](const ProjectIssue &issue)
    {
        return issue.message.find(fragment) != std::string::npos;
    });
}

int tileAt(const LoweredOutdoorMap &lowered, int x, int y)
{
    return lowered.tiles[static_cast<size_t>(y) * Side + x];
}

int sampleAt(const LoweredOutdoorMap &lowered, int x, int y)
{
    return lowered.samples[static_cast<size_t>(y) * Side + x];
}

// A grid of step 8 with every sample `value` (in units of 64) but one.
std::string gridText(int value, int column, int row, int other)
{
    std::string text = "  grid:\n    step: 8\n    unit: 64\n    rows:\n";

    for (int y = 0; y < 16; ++y)
    {
        text += "      - [";

        for (int x = 0; x < 16; ++x)
        {
            text += (x == 0 ? "" : ", ") + std::to_string(x == column && y == row ? other : value);
        }

        text += "]\n";
    }

    return text;
}
}

TEST_CASE("a height grid holds spot heights: the land runs rounded through them and never beyond them")
{
    // Every sample 640 but the one at the node [68, 68], which is 1280.
    const LoweredOutdoorMap lowered = loweredOf("heights:\n" + gridText(10, 8, 8, 20));
    CHECK(sampleAt(lowered, 68, 68) == 1280 / 32);
    CHECK(sampleAt(lowered, 60, 68) == 640 / 32);
    CHECK(sampleAt(lowered, 76, 68) == 640 / 32);
    CHECK(sampleAt(lowered, 68, 60) == 640 / 32);
    // Half way to the next sample the hill is about half way down, and it falls on every step from its top.
    CHECK(sampleAt(lowered, 64, 68) >= 928 / 32);
    CHECK(sampleAt(lowered, 64, 68) <= 1024 / 32);

    for (int x = 61; x <= 68; ++x)
    {
        CHECK(sampleAt(lowered, x, 68) >= sampleAt(lowered, x - 1, 68));
    }

    // No node lies above the highest sample or below the lowest: the curve grows no hill the grid does not have.
    CHECK(*std::max_element(lowered.samples.begin(), lowered.samples.end()) == 1280 / 32);
    CHECK(*std::min_element(lowered.samples.begin(), lowered.samples.end()) == 640 / 32);
}

TEST_CASE("over a grid a height point corrects the land where it stands, and water pulls nothing")
{
    const LoweredOutdoorMap lowered = loweredOf("heights:\n  points:\n    - {at: [20, 20], h: 1600}\n"
        + gridText(10, 99, 99, 10) + "water:\n  bodies:\n"
        "    - {id: water:lake, kind: lake, level: 0, polygon: [[70, 20], [80, 20], [80, 30], [70, 30]]}\n");
    CHECK(sampleAt(lowered, 20, 20) == 1600 / 32);
    // The point fades over one step of the grid (8 cells) and is gone there.
    CHECK(sampleAt(lowered, 24, 20) > 640 / 32);
    CHECK(sampleAt(lowered, 24, 20) < 1120 / 32);
    CHECK(sampleAt(lowered, 28, 20) == 640 / 32);
    CHECK(sampleAt(lowered, 20, 29) == 640 / 32);
    // The lake's corners and the ring of shore corners round them lie at the water's level; the next node is the
    // grid's land again: the bank is the grid's to draw.
    CHECK(sampleAt(lowered, 75, 25) == 0);
    CHECK(sampleAt(lowered, 81, 25) == 0);
    CHECK(sampleAt(lowered, 69, 25) == 0);
    CHECK(sampleAt(lowered, 82, 25) == 640 / 32);
    CHECK(sampleAt(lowered, 68, 25) == 640 / 32);
}

TEST_CASE("water lies on the corners of cells: open water inside the outline, the shore tiles round it")
{
    const LoweredOutdoorMap lowered = loweredOf(std::string(LevelLand) + "water:\n  bodies:\n"
        "    - {id: water:lake, kind: lake, level: 320, polygon: [[70, 20], [80, 20], [80, 30], [70, 30]]}\n");
    CHECK(lowered.waterCells == 100);
    CHECK(lowered.shoreCells == 44);
    // Open water: the plain water tile or one of its variants.
    CHECK(tileAt(lowered, 75, 25) >= 126);
    CHECK(tileAt(lowered, 75, 25) < 138);
    CHECK(lowered.waterCorners[25 * Side + 75] == 15);
    // West of the lake: water on the east corners, dirt along the west side.
    CHECK(lowered.waterCorners[25 * Side + 69] == (2 | 8));
    CHECK(tileAt(lowered, 69, 25) == 126 + 17);
    CHECK(tileAt(lowered, 80, 25) == 126 + 16);
    CHECK(tileAt(lowered, 75, 19) == 126 + 18);
    CHECK(tileAt(lowered, 75, 30) == 126 + 19);
    // The corner cells keep water on one corner only: dirt on the other three.
    CHECK(tileAt(lowered, 69, 19) == 126 + 14);
    CHECK(tileAt(lowered, 80, 19) == 126 + 12);
    CHECK(tileAt(lowered, 69, 30) == 126 + 15);
    CHECK(tileAt(lowered, 80, 30) == 126 + 13);
    // Land never touches water: the corners round the lake are dirt, and grass leads over to them.
    CHECK(tileAt(lowered, 68, 25) == 90 + 16);
    CHECK(tileAt(lowered, 81, 25) == 90 + 17);
    CHECK(tileAt(lowered, 67, 25) < 102);
    // The shore cells lie at the water's level, like the shipped maps' beaches.
    CHECK(sampleAt(lowered, 69, 25) == 320 / 32);
    CHECK(sampleAt(lowered, 81, 31) == 320 / 32);
    CHECK(lowered.tileSets == std::array<uint16_t, 4>{90, 126, 342, 414});
    CHECK(lowered.masterTile == 0);
}

TEST_CASE("the void (U-12) lies at 0 and dry, its outline at the land's height, its cells have four corners in it, "
    "and no water may overlap it")
{
    const std::string rim = "void:\n  - {id: void:rim, polygon: [[105, 0], [128, 0], [128, 128], [105, 128]]}\n";
    const LoweredOutdoorMap lowered = loweredOf(std::string(LevelLand) + rim);
    REQUIRE(lowered.voidCells.size() == static_cast<size_t>(Side) * Side);
    CHECK(lowered.voidCells[10 * Side + 105] == 1);
    CHECK(lowered.voidCells[127 * Side + 127] == 1);
    // The cell west of the outline has its east corners on it only: the land's last cell, level to the edge (D-109:
    // the outline keeps the land's height, so the drop lies in the first void cell, which is never drawn).
    CHECK(lowered.voidCells[10 * Side + 104] == 0);
    CHECK(sampleAt(lowered, 104, 10) > 0);
    CHECK(sampleAt(lowered, 105, 10) == sampleAt(lowered, 104, 10));
    CHECK(sampleAt(lowered, 106, 10) == 0);
    CHECK(sampleAt(lowered, 120, 60) == 0);
    CHECK(lowered.waterCells == 0);
    CHECK(outdoorVoidRectangles(lowered.voidCells) == std::vector<std::array<int, 4>>{{105, 0, 127, 127}});
    CHECK(loweredOf(LevelLand).voidCells.empty());

    // A notch: the runs of each row stack into rectangles while their span repeats.
    std::vector<uint8_t> cells(static_cast<size_t>(Side) * Side, 0);

    for (int y = 0; y < Side; ++y)
    {
        for (int x = y >= 40 && y < 50 ? 100 : 110; x < Side; ++x)
        {
            cells[static_cast<size_t>(y) * Side + x] = 1;
        }
    }

    CHECK(outdoorVoidRectangles(cells)
        == std::vector<std::array<int, 4>>{{110, 0, 127, 39}, {100, 40, 127, 49}, {110, 50, 127, 127}});

    const std::vector<ProjectIssue> issues = refusedWith(std::string(LevelLand) + rim + "water:\n  bodies:\n"
        "    - {id: water:sea, kind: sea, level: 0, polygon: [[100, 0], [128, 0], [128, 128], [100, 128]]}\n");
    CHECK(anyIssue(issues, "lie in the void"));
}

TEST_CASE("a river is at least one open cell wide with a shore on each side")
{
    const LoweredOutdoorMap lowered = loweredOf(std::string(LevelLand) + "water:\n  rivers:\n"
        "    - {id: water:brook, line: [[20, 10], [20, 60]], width_cells: 1, level: 320}\n");
    CHECK(std::any_of(lowered.warnings.begin(), lowered.warnings.end(), [](const std::string &warning)
    {
        return warning.find("narrower than 2 cells") != std::string::npos;
    }));
    // Corners 19 to 21 are water: two cells of open water, the shores at 18 and 21.
    CHECK(lowered.water[30 * Side + 19] == 1);
    CHECK(lowered.water[30 * Side + 20] == 1);
    CHECK(tileAt(lowered, 18, 30) == 126 + 17);
    CHECK(tileAt(lowered, 21, 30) == 126 + 16);
}

TEST_CASE("ground kinds: the later zone lies over the earlier, a line of dirt between two kinds")
{
    const LoweredOutdoorMap lowered = loweredOf(std::string(LevelLand) + "ground:\n"
        "  - {material: grass_meadow, polygon: [[0, 0], [128, 0], [128, 128], [0, 128]]}\n"
        "  - {material: rock, polygon: [[10, 10], [30, 10], [30, 30], [10, 30]]}\n"
        "  - {material: soil, polygon: [[60, 60], [70, 60], [70, 70], [60, 70]]}\n");
    CHECK(lowered.groundKinds == std::vector<std::string>{"grass", "rock"});
    CHECK(lowered.tileSets[0] == 90);
    CHECK(lowered.tileSets[2] == 342);
    // Rock inside its zone: the second ground set's plain tile or a variant.
    CHECK(tileAt(lowered, 20, 20) >= 162);
    CHECK(tileAt(lowered, 20, 20) < 174);
    // Its east edge: rock toward dirt, then grass toward dirt, then grass.
    CHECK(tileAt(lowered, 29, 20) == 162 + 16);
    CHECK(tileAt(lowered, 30, 20) == 90 + 17);
    CHECK(tileAt(lowered, 32, 20) < 102);
    // Dirt drawn over grass: the dirt tiles, grass leading over to them.
    CHECK(tileAt(lowered, 65, 65) >= 1);
    CHECK(tileAt(lowered, 65, 65) <= 12);
    CHECK(tileAt(lowered, 59, 65) == 90 + 16);

    // Every cell's tile is one the sets have: never a hole in a set.
    for (const uint8_t tile : lowered.tiles)
    {
        const int offset = tile >= 90 ? (tile - 90) % 36 : 0;
        CHECK(tile != 0);
        CHECK(offset < 24);
    }
}

TEST_CASE("a third kind of land and a kind the world lacks are refused, with what to change")
{
    const std::string whole = "polygon: [[0, 0], [128, 0], [128, 128], [0, 128]]}\n";
    CHECK(anyIssue(refusedWith(std::string(LevelLand) + "ground:\n  - {material: grass, " + whole
        + "  - {material: rock, polygon: [[10, 10], [30, 10], [30, 30], [10, 30]]}\n"
        "  - {material: volcanic, polygon: [[40, 40], [60, 40], [60, 60], [40, 60]]}\n"),
        "the sketch draws 3: grass (1 zone), rock (1 zone), volcanic (1 zone)"));
    const std::vector<ProjectIssue> issues = refusedWith(std::string(LevelLand) + "ground:\n  - {material: snow, "
        + whole);
    CHECK(anyIssue(issues, "the world mm8 has no ground of the kind `snow`"));
    CHECK(anyIssue(issues, "grass, rock, volcanic"));
    // Harmondale's world has snow, and lays it in its second set.
    const LoweredOutdoorMap snowy = loweredOf(std::string(LevelLand) + "ground:\n  - {material: grass, " + whole
        + "  - {material: snow, polygon: [[10, 10], [30, 10], [30, 30], [10, 30]]}\n", "mm7");
    CHECK(snowy.tileSets == std::array<uint16_t, 4>{90, 126, 342, 414});
    CHECK(snowy.masterTile == 1);
    CHECK(tileAt(snowy, 20, 20) >= 162);
}

TEST_CASE("a ground zone with steeper_than lies on the steep ground of its outline only")
{
    // Low ground in the north, high in the south, a cliff of 1920 along y = 64.
    const LoweredOutdoorMap lowered = loweredOf("heights:\n  bands:\n"
        "    - {band: band:low, polygon: [[0, 0], [128, 0], [128, 64], [0, 64]]}\n"
        "    - {band: band:high, polygon: [[0, 64], [128, 64], [128, 128], [0, 128]]}\n"
        "  cliffs:\n    - {line: [[0, 64], [128, 64]], drop: 1900, down: left}\n"
        "ground:\n  - {material: grass, polygon: [[0, 0], [128, 0], [128, 128], [0, 128]]}\n"
        "  - {material: rock, steeper_than: 512, polygon: [[0, 0], [128, 0], [128, 128], [0, 128]]}\n");
    // The cliff's face is rock, the land above and below is grass, with the tiles toward dirt between.
    CHECK(tileAt(lowered, 60, 63) >= 162);
    CHECK(tileAt(lowered, 60, 63) < 174);
    CHECK(tileAt(lowered, 60, 62) == 162 + 18);
    CHECK(tileAt(lowered, 60, 64) == 162 + 19);
    CHECK(tileAt(lowered, 60, 61) == 90 + 19);
    CHECK(tileAt(lowered, 60, 65) == 90 + 18);
    CHECK(tileAt(lowered, 60, 40) < 102);
    CHECK(tileAt(lowered, 60, 90) < 102);
}

TEST_CASE("a road is one cell wide in a bed of dirt, with the classic bends, ends and diagonal steps")
{
    const LoweredOutdoorMap lowered = loweredOf(std::string(LevelLand) + "roads:\n"
        "  - {link: road:a, line: [[10.5, 10.5], [20.5, 10.5], [20.5, 20.5]], surface: pebbles}\n"
        "  - {link: road:b, line: [[40.5, 40.5], [50.5, 50.5]]}\n"
        "  - {link: road:c, line: [[15.5, 10.5], [15.5, 4.5]], surface: road_pebbles}\n"
        "  - {link: road:path, line: [[80.5, 80.5], [90.5, 80.5]], surface: dirt}\n"
        "  - {link: road:lawn, line: [[80.5, 90.5], [90.5, 90.5]], surface: grass}\n"
        "  - {link: road:deck, line: [[80.5, 95.5], [90.5, 95.5]], bridge: true}\n");
    const int road = 198;
    // East-west and north-south runs, the bend between them, the two ends, the T where road:c leaves.
    CHECK(tileAt(lowered, 12, 10) == road + 2);
    CHECK(tileAt(lowered, 20, 15) == road + 1);
    CHECK(tileAt(lowered, 20, 10) == road + 6);
    CHECK(tileAt(lowered, 10, 10) == road + 14);
    CHECK(tileAt(lowered, 20, 20) == road + 13);
    CHECK(tileAt(lowered, 15, 10) == road + 9);
    CHECK(tileAt(lowered, 15, 4) == road + 11);
    // Grass leads over to the road's dirt on both sides.
    CHECK(tileAt(lowered, 12, 9) == 90 + 19);
    CHECK(tileAt(lowered, 12, 11) == 90 + 18);
    // The diagonal road is a staircase of the two diagonal pieces, one cell wide: 21 cells for 10 cells each way.
    size_t steps = 0;

    for (int y = 40; y <= 50; ++y)
    {
        for (int x = 40; x <= 50; ++x)
        {
            const int tile = tileAt(lowered, x, y);

            if (tile >= road && tile < road + 36 && !(x == 40 && y == 40) && !(x == 50 && y == 50))
            {
                CAPTURE(x);
                CAPTURE(y);
                CHECK((tile == road + 19 || tile == road + 20));
                ++steps;
            }
        }
    }

    CHECK(steps == 19);
    // A dirt path is bare dirt; grass and a bridge lay nothing, and the build says so.
    CHECK(tileAt(lowered, 85, 80) <= 12);
    CHECK(tileAt(lowered, 85, 79) == 90 + 19);
    CHECK(tileAt(lowered, 85, 90) < 102);
    CHECK(tileAt(lowered, 85, 95) < 102);
    CHECK(lowered.roads.size() == 4);
    CHECK(std::any_of(lowered.warnings.begin(), lowered.warnings.end(), [](const std::string &warning)
    {
        return warning.find("road:lawn (grass)") != std::string::npos;
    }));
    CHECK(std::any_of(lowered.warnings.begin(), lowered.warnings.end(), [](const std::string &warning)
    {
        return warning.find("1 bridges") != std::string::npos;
    }));
}

TEST_CASE("the road pieces by which neighbours are road, as the shipped maps choose them")
{
    // Offsets in the road set: crossing 0, north-south 1, east-west 2, bends 3 to 6, T pieces 7 to 10, ends 11 to
    // 14, diagonal steps 19 to 22. Measured on Ravenshore (509 of 511 road cells) and Harmondale (341 of 342).
    CHECK(outdoorRoadTileOffset(true, true, true, true, false) == 0);
    CHECK(outdoorRoadTileOffset(true, false, true, false, false) == 1);
    CHECK(outdoorRoadTileOffset(false, true, false, true, false) == 2);
    CHECK(outdoorRoadTileOffset(true, true, false, false, false) == 3);
    CHECK(outdoorRoadTileOffset(true, false, false, true, false) == 4);
    CHECK(outdoorRoadTileOffset(false, true, true, false, false) == 5);
    CHECK(outdoorRoadTileOffset(false, false, true, true, false) == 6);
    CHECK(outdoorRoadTileOffset(true, true, true, false, false) == 7);
    CHECK(outdoorRoadTileOffset(true, false, true, true, false) == 8);
    CHECK(outdoorRoadTileOffset(true, true, false, true, false) == 9);
    CHECK(outdoorRoadTileOffset(false, true, true, true, false) == 10);
    CHECK(outdoorRoadTileOffset(false, false, true, false, false) == 11);
    CHECK(outdoorRoadTileOffset(false, false, false, true, false) == 12);
    CHECK(outdoorRoadTileOffset(true, false, false, false, false) == 13);
    CHECK(outdoorRoadTileOffset(false, true, false, false, false) == 14);
    CHECK(outdoorRoadTileOffset(false, false, true, true, true) == 19);
    CHECK(outdoorRoadTileOffset(true, true, false, false, true) == 20);
    CHECK(outdoorRoadTileOffset(false, true, true, false, true) == 21);
    CHECK(outdoorRoadTileOffset(true, false, false, true, true) == 22);
    // The tiles toward dirt by which corners hold dirt (north-west, north-east, south-west, south-east).
    CHECK(outdoorGroundTileOffset(false, false, false, false) == 0);
    CHECK(outdoorGroundTileOffset(true, true, false, false) == 18);
    CHECK(outdoorGroundTileOffset(false, true, false, true) == 16);
    CHECK(outdoorGroundTileOffset(true, true, false, true) == 12);
    CHECK(outdoorGroundTileOffset(false, true, false, false) == 20);
    CHECK(outdoorGroundTileOffset(true, false, false, true) == -1);
    CHECK(outdoorGroundTileOffset(false, true, true, false) == -1);
}

TEST_CASE("a road lies level across its width: its bed follows the land along it, or the sketch's bed")
{
    // Land that rises to the south: 64 a cell in the grid's reading.
    std::string grid = "heights:\n  grid:\n    step: 8\n    unit: 64\n    rows:\n";

    for (int y = 0; y < 16; ++y)
    {
        grid += "      - [";

        for (int x = 0; x < 16; ++x)
        {
            grid += (x == 0 ? "" : ", ") + std::to_string(4 + y * 8);
        }

        grid += "]\n";
    }

    const auto reliefOf = [](const LoweredOutdoorMap &lowered, int x, int y)
    {
        const int corners[4] = {sampleAt(lowered, x, y), sampleAt(lowered, x + 1, y), sampleAt(lowered, x, y + 1),
            sampleAt(lowered, x + 1, y + 1)};
        return (*std::max_element(corners, corners + 4) - *std::min_element(corners, corners + 4)) * 32;
    };
    const LoweredOutdoorMap bare = loweredOf(grid);
    CHECK(reliefOf(bare, 60, 40) == 64);
    const LoweredOutdoorMap graded = loweredOf(grid + "roads:\n"
        "  - {link: road:across, line: [[30.5, 40.5], [90.5, 40.5]]}\n"
        "  - {link: road:cut, line: [[30.5, 80.5], [90.5, 80.5]], bed: [640, 640]}\n");
    // Across the slope the road's cells are level, at the land's height along its middle.
    CHECK(reliefOf(graded, 60, 40) == 0);
    CHECK(sampleAt(graded, 60, 40) == sampleAt(graded, 60, 41));
    CHECK(std::abs(sampleAt(graded, 60, 40) * 32 - (sampleAt(bare, 60, 40) + sampleAt(bare, 60, 41)) * 16) <= 32);
    // The cells beside it are the slope's again.
    CHECK(sampleAt(graded, 60, 43) == sampleAt(bare, 60, 43));
    // The road with a bed is cut down to it.
    CHECK(sampleAt(graded, 60, 80) == 640 / 32);
    CHECK(sampleAt(graded, 60, 81) == 640 / 32);
    CHECK(sampleAt(bare, 60, 80) > 640 / 32 + 30);
    // P4 (X3's Newcastle mirror): a bed that lowers the land by more than two steps beside a fixture is told; a road
    // whose bed keeps to the land is not.
    const LoweredOutdoorMap beside = loweredOf(grid + "roads:\n"
        "  - {link: road:across, line: [[30.5, 40.5], [90.5, 40.5]]}\n"
        "  - {link: road:cut, line: [[30.5, 80.5], [90.5, 80.5]], bed: [640, 640]}\n"
        "structures:\n  - {id: thing:mirror, kind: portal, at: [60, 79.6], radius: 112}\n"
        "  - {id: thing:well, kind: well, at: [60, 39.6]}\n");
    const auto told = [&beside](const std::string &fragment)
    {
        return std::count_if(beside.warnings.begin(), beside.warnings.end(), [&fragment](const std::string &warning)
        {
            return warning.find(fragment) != std::string::npos;
        });
    };
    CHECK(told("the bed of road:cut lowers the land") == 1);
    CHECK(told("within a cell of thing:mirror") == 1);
    CHECK(told("thing:well") == 0);
    // A bed with the wrong number of heights is refused.
    CHECK(anyIssue(refusedWith(grid + "roads:\n  - {link: road:x, line: [[30.5, 80.5], [90.5, 80.5]], "
        "bed: [640]}\n"), "one height for each of the 2 points"));
}

TEST_CASE("a road through water carries no road there, and the build says which")
{
    const LoweredOutdoorMap lowered = loweredOf(std::string(LevelLand) + "water:\n  bodies:\n"
        "    - {id: water:lake, kind: lake, level: 320, polygon: [[70, 20], [80, 20], [80, 30], [70, 30]]}\n"
        "roads:\n  - {link: road:ford, line: [[60.5, 25.5], [90.5, 25.5]]}\n");
    CHECK(tileAt(lowered, 65, 25) == 198 + 2);
    CHECK(tileAt(lowered, 75, 25) < 138);
    CHECK(tileAt(lowered, 75, 25) >= 126);
    // The road ends at the shore on each side: 60 to 68 and 81 to 90.
    CHECK(lowered.roadCells == 19);
    CHECK(std::any_of(lowered.warnings.begin(), lowered.warnings.end(), [](const std::string &warning)
    {
        return warning.find("12 cells of road lie in water") != std::string::npos
            && warning.find("road:ford (12)") != std::string::npos
            && warning.find("bridge: true") != std::string::npos;
    }));
}

TEST_CASE("what the tiles cannot show is cleared from a ground mask")
{
    std::vector<uint8_t> mask(129 * 129, 0);
    const auto set = [&mask](int x, int y)
    {
        mask[y * 129 + x] = 1;
    };
    // A lone corner, a line of corners one wide, and a block of 3 x 3 corners.
    set(5, 5);

    for (int x = 20; x < 30; ++x)
    {
        set(x, 10);
    }

    for (int y = 40; y < 43; ++y)
    {
        for (int x = 40; x < 43; ++x)
        {
            set(x, y);
        }
    }

    // Two blocks of 2 x 2 that touch at one corner only: the cell between them would hold the kind on two
    // opposite corners.
    set(60, 60);
    set(61, 60);
    set(60, 61);
    set(61, 61);
    set(62, 62);
    set(63, 62);
    set(62, 63);
    set(63, 63);
    set(61, 62);
    set(61, 63);
    set(60, 62);
    set(60, 63);
    settleOutdoorGroundMask(mask);
    CHECK(mask[5 * 129 + 5] == 0);
    CHECK(mask[10 * 129 + 25] == 0);
    CHECK(mask[41 * 129 + 41] == 1);
    CHECK(mask[40 * 129 + 40] == 1);

    for (int y = 0; y + 1 < 129; ++y)
    {
        for (int x = 0; x + 1 < 129; ++x)
        {
            const bool northWest = mask[y * 129 + x] != 0;
            const bool northEast = mask[y * 129 + x + 1] != 0;
            const bool southWest = mask[(y + 1) * 129 + x] != 0;
            const bool southEast = mask[(y + 1) * 129 + x + 1] != 0;
            CHECK_FALSE((northWest && southEast && !northEast && !southWest));
            CHECK_FALSE((northEast && southWest && !northWest && !southEast));
        }
    }
}

TEST_CASE("cliff lines that end short of each other are told; the two walls of a pass are not")
{
    const auto cliffIssues = [](const std::string &cliffs)
    {
        std::vector<ProjectIssue> issues;
        validateSketch(outdoorProject(std::string(LevelLand) + "  cliffs:\n" + cliffs), issues);
        std::vector<std::string> found;

        for (const ProjectIssue &issue : issues)
        {
            if (issue.message.find("cells short of") != std::string::npos)
            {
                CHECK(issue.code == "heights");
                found.push_back(issue.path + ": " + issue.message);
            }
        }

        return found;
    };
    // A face that stops two cells before the wall it should meet: both ends are told.
    const std::vector<std::string> gap = cliffIssues("    - {line: [[30, 10], [30, 38]], drop: 800}\n"
        "    - {line: [[10, 40], [32, 40]], drop: 800}\n");
    REQUIRE(gap.size() == 2);
    CHECK(gap[0].find("heights.cliffs[0].line") == 0);
    CHECK(gap[0].find("ends at [30, 38], 2 cells short of heights.cliffs[1]") != std::string::npos);
    CHECK(gap[0].find("share a point") != std::string::npos);
    // Joined at a point, or far apart: nothing.
    CHECK(cliffIssues("    - {line: [[30, 10], [30, 40]], drop: 800}\n"
        "    - {line: [[10, 40], [30, 40]], drop: 800}\n").empty());
    CHECK(cliffIssues("    - {line: [[30, 10], [30, 30]], drop: 800}\n"
        "    - {line: [[10, 40], [32, 40]], drop: 800}\n").empty());
    // The two walls of a pass run side by side two cells apart and end together.
    CHECK(cliffIssues("    - {line: [[10, 40], [50, 40]], drop: 800}\n"
        "    - {line: [[10, 42], [50, 42]], drop: 800}\n").empty());
}

TEST_CASE("the cells of an outdoor map by what their tiles are: land, shore, open water, road")
{
    Game::OutdoorMapData map = testMap();
    map.tileMap[0] = 126;
    map.tileMap[1] = 126 + 17;
    map.tileMap[2] = 198 + 2;
    map.tileMap[3] = 1;
    map.tileMap[4] = 162 + 16;
    const std::vector<uint8_t> kinds = outdoorCellKinds(map, testTiles());
    CHECK(kinds[0] == 2);
    CHECK(kinds[1] == 1);
    CHECK(kinds[2] == 3);
    CHECK(kinds[3] == 0);
    CHECK(kinds[4] == 0);
    CHECK(kinds[5] == 0);
}

namespace
{
// Every property under a schema node says what it is: a description of its own, or a reference to a definition.
void checkDescribed(const YAML::Node &schema, const std::string &path, size_t &fields)
{
    if (!schema.IsDefined() || !schema.IsMap())
    {
        return;
    }

    const YAML::Node properties = schema["properties"];

    for (YAML::const_iterator property = properties.begin();
         properties.IsDefined() && properties.IsMap() && property != properties.end(); ++property)
    {
        const std::string name = path + "." + property->first.Scalar();
        CAPTURE(name);
        CHECK((property->second["description"].IsDefined() || property->second["$ref"].IsDefined()
            || property->second["const"].IsDefined()));
        ++fields;
        checkDescribed(property->second, name, fields);
    }

    checkDescribed(schema["items"], path + "[]", fields);
}
}

TEST_CASE("the sketch's schema describes every field it has")
{
    const YAML::Node root = inlinedSketchSchema();
    REQUIRE(root.IsMap());
    size_t fields = 0;
    checkDescribed(root, "sketch", fields);
    CHECK(fields > 60);
    // The fields of S4's second and third parts.
    const std::string &text = SchemaSet::builtIn().text("sketch.schema.json");
    CHECK(text.find("\"steeper_than\"") != std::string::npos);
    CHECK(text.find("\"bed\"") != std::string::npos);
    CHECK(text.find("a spot height") != std::string::npos);
}

// ---- Buildings, spawn points and scattered decorations (core/OutdoorBuildings, core/OutdoorPlaces) ----

#include "core/OutdoorBuildings.h"
#include "core/OutdoorModel.h"
#include "core/OutdoorPlaces.h"

#include "game/FaceEnums.h"

namespace
{
// A project with one building of 2 x 1.5 cells in the plan and what the test adds to the sketch.
Project buildingProject(const std::string &plots, const std::string &more = {})
{
    Project project = outdoorProject(std::string(LevelLand) + "districts:\n  - space: town:t\n"
        "    polygon: [[30, 30], [60, 30], [60, 60], [30, 60]]\n    plots:\n" + plots + more);
    ProjectFile &plan = project.files["plan.yml"];
    plan.text = "format: 0\nentrances:\n  - {id: entrance:north, kind: arrival, facing: s}\n"
        "height_bands:\n  - {id: band:low, range: [576, 704]}\n"
        "spaces:\n  - id: town:t\n    kind: town\n    buildings:\n"
        "      - {id: building:home, type: house, footprint_cells: [2, 1.5]}\n"
        "      - {id: building:shed, type: shed, footprint_cells: [0.25, 1]}\n"
        "    population:\n      - {id: pop:wolves, actor: Dire Wolf}\n";
    plan.document = YAML::Load(plan.text);
    ProjectFile &card = project.files["project.yml"];
    card.text = "format: 0\nid: groundtest\nworld: mm8\nkind: outdoor\nmap_stats:\n  id: 9900\n  slots:\n"
        "    - {monster: Centaur}\n    - {monster: Dire Wolf}\n";
    card.document = YAML::Load(card.text);
    return project;
}

LoweredOutdoorMap loweredBuildings(const std::string &plots, const std::string &more = {})
{
    LoweredOutdoorMap lowered;
    std::vector<ProjectIssue> issues;
    const bool ok = lowerOutdoorProject(buildingProject(plots, more), lowered, issues);

    for (const ProjectIssue &issue : issues)
    {
        MESSAGE(issue.path << ": " << issue.message);
    }

    REQUIRE(ok);
    return lowered;
}

// The outward normal of a face from its points, and whether it is flat.
std::array<double, 3> faceNormal(const Game::OutdoorBModel &model, const Game::OutdoorBModelFace &face)
{
    std::array<double, 3> normal = {0.0, 0.0, 0.0};

    for (size_t index = 0; index < face.vertexIndices.size(); ++index)
    {
        const Game::OutdoorBModelVertex &from = model.vertices[face.vertexIndices[index]];
        const Game::OutdoorBModelVertex &to = model.vertices[face.vertexIndices[(index + 1)
            % face.vertexIndices.size()]];
        normal[0] += (from.y - to.y) * static_cast<double>(from.z + to.z);
        normal[1] += (from.z - to.z) * static_cast<double>(from.x + to.x);
        normal[2] += (from.x - to.x) * static_cast<double>(from.y + to.y);
    }

    const double length = std::sqrt(normal[0] * normal[0] + normal[1] * normal[1] + normal[2] * normal[2]);
    return {normal[0] / length, normal[1] / length, normal[2] / length};
}
}

TEST_CASE("a plot that says nothing more is the world's ordinary house: bays of panels, a door, eaves and a hip roof")
{
    LoweredOutdoorMap lowered = loweredBuildings("      - {building: building:home, at: [40, 40], facing: s, "
        "house: 904, title: Lott's Family Home, foundation: 0}\n");
    REQUIRE(lowered.buildings.size() == 1);
    OutdoorBuildingPlan &plan = lowered.buildings[0];
    CHECK(plan.base == doctest::Approx(640.0));
    REQUIRE(plan.doors.size() == 1);
    CHECK(plan.doors[0].house == 904);
    plan.doors[0].event = 7;
    plan.nameEvent = 8;
    const Game::OutdoorBModel house = raiseOutdoorBuilding(plan);
    // The walls stand on cells 40 to 42 east and 40 to 41.5 south; Ravenshore's eaves reach 16 further out. One
    // storey of 256, a fascia of 32, the roof 96 and half the ridge beam of 32 over it.
    CHECK(house.minX == (40 - 64) * 512 - 16);
    CHECK(house.maxX == (42 - 64) * 512 + 16);
    CHECK(house.maxY == (64 - 40) * 512 + 16);
    CHECK(house.minY == (64 - 41.5) * 512 - 16);
    CHECK(house.minZ == 640);
    CHECK(house.maxZ == 640 + 256 + 32 + 96 + 16);
    CHECK(house.bspNodes.empty());
    // The south wall: eight bays of 128. Posts at its ends, the door in bay 3, a window on each side of it.
    REQUIRE(plan.parts.size() == 1);
    CHECK(plan.parts[0].bays[0] == std::vector<std::string>{"post_left", "wall", "window", "door", "window", "wall",
        "window", "post_right"});
    CHECK(plan.doors[0].bay == 3);
    REQUIRE(plan.doors[0].face >= 0);
    const Game::OutdoorBModelFace &door = house.faces[plan.doors[0].face];
    CHECK(door.textureName == "t14a03");
    CHECK(door.cogTriggeredNumber == 7);
    CHECK((door.attributes & Game::faceAttributeBit(Game::FaceAttribute::Clickable)) != 0);
    CHECK(door.polygonType == 1);
    int low[3] = {1 << 30, 1 << 30, 1 << 30};
    int high[3] = {-(1 << 30), -(1 << 30), -(1 << 30)};

    for (const uint16_t index : door.vertexIndices)
    {
        const Game::OutdoorBModelVertex &vertex = house.vertices[index];
        low[0] = std::min(low[0], vertex.x);
        low[1] = std::min(low[1], vertex.y);
        low[2] = std::min(low[2], vertex.z);
        high[0] = std::max(high[0], vertex.x);
        high[1] = std::max(high[1], vertex.y);
        high[2] = std::max(high[2], vertex.z);
    }

    // 128 by 256 on the floor in the south wall, its texture fitted once; the build's place for it agrees.
    CHECK(high[0] - low[0] == 128);
    CHECK(low[0] == (40 - 64) * 512 + 3 * 128);
    CHECK(low[1] == (64 - 41.5) * 512);
    CHECK(high[1] == low[1]);
    CHECK(low[2] == 640);
    CHECK(high[2] == 640 + 256);
    CHECK(faceNormal(house, door)[1] == doctest::Approx(-1.0));
    CHECK(*std::min_element(door.textureUs.begin(), door.textureUs.end()) == 0);
    CHECK(*std::max_element(door.textureUs.begin(), door.textureUs.end()) == 128);
    CHECK(*std::max_element(door.textureVs.begin(), door.textureVs.end()) == 256);
    CHECK(plan.doors[0].x == doctest::Approx((low[0] + high[0]) * 0.5));
    CHECK(plan.doors[0].normalY == doctest::Approx(-1.0));
    std::map<std::string, size_t> textures;

    for (const Game::OutdoorBModelFace &face : house.faces)
    {
        // Every face is flat and stores its plane as the game's maps do; every face but the door says the name.
        const std::array<double, 3> normal = faceNormal(house, face);
        const Game::OutdoorBModelVertex &first = house.vertices[face.vertexIndices[0]];
        CHECK(face.planeNormalZ == std::lround(normal[2] * 65536.0));
        CHECK(std::abs(face.planeDistance + std::lround((normal[0] * first.x + normal[1] * first.y
            + normal[2] * first.z) * 65536.0)) <= 2);
        CHECK(face.cogTriggeredNumber == (&face == &door ? 7 : 8));

        for (const uint16_t index : face.vertexIndices)
        {
            const Game::OutdoorBModelVertex &vertex = house.vertices[index];
            CHECK(std::fabs(normal[0] * (vertex.x - first.x) + normal[1] * (vertex.y - first.y)
                + normal[2] * (vertex.z - first.z)) < 1.0);
        }

        if (face.polygonType == 1 && first.z < 640 + 256 && face.textureName != "t14a05b")
        {
            // A wall looks away from the middle of the house.
            const double outX = (first.x + house.vertices[face.vertexIndices[1]].x) * 0.5 - house.positionX;
            const double outY = (first.y + house.vertices[face.vertexIndices[1]].y) * 0.5 - house.positionY;
            CHECK(normal[0] * outX + normal[1] * outY > 0.0);
        }

        ++textures[face.textureName];
    }

    // The kit's panels: two posts to a wall, the door, the roof's four slopes, the soffit and fascia in the trim,
    // the ridge beam's five faces.
    CHECK(textures["t14a07"] == 4);
    CHECK(textures["t14a06"] == 4);
    CHECK(textures["t14a03"] == 1);
    CHECK(textures["t14a05"] == 4);
    CHECK(textures["t14a05b"] == 8);
    CHECK(textures["t14abcd11"] == 5);
    CHECK(textures["t14a04a"] > 4);
}

TEST_CASE("roofs: flat can be stood on, lean-to rises to the back, a gable's ends run up to the ridge, a cone tips")
{
    const auto raised = [](const std::string &fields, const char *pWorld = "mm8")
    {
        Project project = buildingProject("      - {building: building:home, at: [40, 40], facing: s" + fields + "}\n");
        project.files["project.yml"].text.replace(project.files["project.yml"].text.find("mm8"), 3, pWorld);
        project.files["project.yml"].document = YAML::Load(project.files["project.yml"].text);
        LoweredOutdoorMap lowered;
        std::vector<ProjectIssue> issues;
        REQUIRE(lowerOutdoorProject(project, lowered, issues));
        return raiseOutdoorBuilding(lowered.buildings[0]);
    };
    const auto count = [](const Game::OutdoorBModel &model, int polygonType)
    {
        return std::count_if(model.faces.begin(), model.faces.end(), [polygonType](const Game::OutdoorBModelFace &face)
        {
            return face.polygonType == polygonType;
        });
    };
    const Game::OutdoorBModel flat = raised(", roof: flat, wall_height: 512, eaves: 0, fascia: 0");
    CHECK(flat.maxZ == 640 + 512);
    CHECK(count(flat, 3) == 1);
    // Two rows of panels: the upper row has a window where the lower has the door.
    CHECK(std::count_if(flat.faces.begin(), flat.faces.end(), [](const Game::OutdoorBModelFace &face)
    {
        return face.textureName == "t14a03";
    }) == 1);
    const Game::OutdoorBModel lean = raised(", roof: lean_to, roof_height: 256, fascia: 0");
    CHECK(lean.maxZ == 640 + 256 + 256);

    // The back wall (north) reaches the top; the front's eaves stay at the wall height.
    for (const Game::OutdoorBModelVertex &vertex : lean.vertices)
    {
        CHECK((vertex.z <= 640 + 256 || vertex.y == lean.maxY));
    }

    const Game::OutdoorBModel gable = raised(", roof: gable, roof_height: 200, eaves: 0, fascia: 0, textures: {wall: "
        "wallx, window: wallx, door: doorx, post_left: wallx, post_right: wallx, roof: roofx, gable: gablex}");
    CHECK(gable.maxZ == 640 + 256 + 200);
    size_t gableEnds = 0;

    for (const Game::OutdoorBModelFace &face : gable.faces)
    {
        CHECK((face.textureName == "wallx" || face.textureName == "roofx" || face.textureName == "doorx"
            || face.textureName == "gablex"));
        gableEnds += face.textureName == "gablex" ? 1 : 0;
    }

    // The ridge runs east-west (the longer side): the east and west walls carry the gable ends, in their own
    // texture.
    CHECK(gableEnds == 2);
    // A verge: the slopes run on 48 past each gable end (the ridge east-west, the house 1024 along it), a barge board
    // 24 high under the roof's edge at each end, two per end; the gable faces stay in the end walls' planes.
    const Game::OutdoorBModel verged = raised(", roof: gable, roof_height: 200, eaves: 0, fascia: 0, verge: 48, "
        "textures: {wall: wallx, window: wallx, door: doorx, post_left: wallx, post_right: wallx, roof: roofx, "
        "gable: gablex, trim: trimx}");
    CHECK(verged.maxX - verged.minX == 1024 + 2 * 48);
    CHECK(verged.maxZ == 640 + 256 + 200);
    size_t boards = 0;

    for (const Game::OutdoorBModelFace &face : verged.faces)
    {
        boards += face.textureName == "trimx" ? 1 : 0;

        if (face.textureName == "gablex")
        {
            for (const uint16_t index : face.vertexIndices)
            {
                CHECK((verged.vertices[index].x == verged.minX + 48 || verged.vertices[index].x == verged.maxX - 48));
            }
        }

        if (face.textureName == "trimx")
        {
            // Out at the verge, upright, facing away from the house.
            CHECK((verged.vertices[face.vertexIndices[0]].x == verged.minX
                || verged.vertices[face.vertexIndices[0]].x == verged.maxX));
            CHECK(face.polygonType == 1);
        }
    }

    CHECK(boards == 4);
    // `verge_walls: [e]`: only the east end runs on (a shed against the west end): two boards, the west end flush.
    const Game::OutdoorBModel eastOnly = raised(", roof: gable, roof_height: 200, eaves: 0, fascia: 0, verge: 48, "
        "verge_walls: [e], textures: {roof: roofx, gable: gablex, trim: trimx}");
    CHECK(eastOnly.maxX - eastOnly.minX == 1024 + 48);
    CHECK(std::count_if(eastOnly.faces.begin(), eastOnly.faces.end(), [](const Game::OutdoorBModelFace &face)
    {
        return face.textureName == "trimx";
    }) == 2);
    // Refused off a gable: a hip has no gable ends.
    {
        Project project = buildingProject("      - {building: building:home, at: [40, 40], facing: s, roof: hip, "
            "verge: 48}\n");
        LoweredOutdoorMap lowered;
        std::vector<ProjectIssue> issues;
        lowerOutdoorProject(project, lowered, issues);
        CHECK(std::any_of(issues.begin(), issues.end(), [](const ProjectIssue &issue)
        {
            return issue.message.find("verge runs a box's gable") != std::string::npos;
        }));
    }
    // Harmondale's ordinary roof is a gable at 50 degrees: over a depth of 768 it rises tan(50) * 384.
    const Game::OutdoorBModel harmondale = raised("", "mm7");
    CHECK(harmondale.maxZ == 640 + 256 + std::lround(384.0 * std::tan(50.0 * 3.14159265358979323846 / 180.0)));
    // New Sorpigal's: a hip rising 128, no eaves.
    const Game::OutdoorBModel sorpigal = raised("", "mm6");
    CHECK(sorpigal.maxZ == 640 + 256 + 128);
    CHECK(sorpigal.maxX - sorpigal.minX == 1024);
    const Game::OutdoorBModel cone = raised(", roof: cone, roof_pitch: 45, eaves: 0, fascia: 0");
    CHECK(cone.maxZ == 640 + 256 + 384);
    CHECK(count(cone, 4) == 4);
}

TEST_CASE("a building of parts: a body, a wing with its own roof, a round tower with a cone, a hanging upper storey")
{
    LoweredOutdoorMap lowered = loweredBuildings("      - building: building:home\n        at: [40, 40]\n"
        "        facing: s\n        house: 77\n        title: Needful Things\n        turn: 0\n"
        "        door: {part: wing, wall: e, bay: 1}\n        parts:\n"
        "          - {id: body, at: [0, 0], size: [640, 512], roof: gable, roof_height: 128, ridge_along: ew}\n"
        "          - {id: wing, at: [640, 128], size: [256, 384], wall_height: 512, roof: flat, parapet: 64, "
        "battlements: true, walls: {e: [window, door, t14c01b]}}\n"
        "          - {id: tower, shape: round, at: [0, 0], radius: 160, sides: 8, wall_height: 768, kit: tower, "
        "roof: cone, roof_height: 400, eaves: 0, fascia: 0}\n"
        "          - {id: upper, at: [64, 64], size: [256, 256], bottom: 384, wall_height: 256, roof: none}\n");
    REQUIRE(lowered.buildings.size() == 1);
    OutdoorBuildingPlan &plan = lowered.buildings[0];
    REQUIRE(plan.parts.size() == 4);
    CHECK(plan.parts[2].shape == "round");
    CHECK(plan.parts[2].outline.size() == 8);
    CHECK(plan.parts[2].textures.at("wall") == "t14c01b");
    // The door is where the plot says: the wing's east wall, the bay written `door`.
    REQUIRE(plan.doors.size() == 1);
    CHECK(plan.doors[0].part == 1);
    CHECK(plan.doors[0].wall == 1);
    CHECK(plan.doors[0].bay == 1);
    plan.doors[0].event = 3;
    const Game::OutdoorBModel model = raiseOutdoorBuilding(plan);
    // The tower's tip is the highest point; the tower stands round the plot's north-west corner.
    CHECK(model.maxZ == 640 + 768 + 400);
    CHECK(model.minX == (40 - 64) * 512 - std::lround(160.0 * std::cos(3.14159265358979323846 / 8.0)));
    const Game::OutdoorBModelFace &door = model.faces[plan.doors[0].face];
    CHECK(faceNormal(model, door)[0] == doctest::Approx(1.0));
    CHECK(door.cogTriggeredNumber == 3);
    // A bay may name a texture itself; the upper storey that hangs has an underside.
    CHECK(std::any_of(model.faces.begin(), model.faces.end(), [](const Game::OutdoorBModelFace &face)
    {
        return face.textureName == "t14c01b" && face.polygonType == 1;
    }));
    CHECK(std::any_of(model.faces.begin(), model.faces.end(), [](const Game::OutdoorBModelFace &face)
    {
        return face.polygonType == 5 && face.planeDistance == (640 + 384) * 65536;
    }));
    // Merlons on the wing: blocks whose tops lie 64 over its roof.
    CHECK(std::count_if(model.faces.begin(), model.faces.end(), [&model](const Game::OutdoorBModelFace &face)
    {
        return face.polygonType == 3 && model.vertices[face.vertexIndices[0]].z == 640 + 512 + 64;
    }) >= 6);

    // Turned by 90 degrees the same building looks east where it looked north; its size is the same.
    LoweredOutdoorMap turned = loweredBuildings("      - {building: building:home, at: [40, 40], facing: s, turn: 90, "
        "roof: flat, eaves: 0, fascia: 0, foundation: 0}\n");
    const Game::OutdoorBModel turnedModel = raiseOutdoorBuilding(turned.buildings[0]);
    CHECK(turnedModel.maxX - turnedModel.minX == 768);
    CHECK(turnedModel.maxY - turnedModel.minY == 1024);
    CHECK(turned.buildings[0].doors[0].normalX == doctest::Approx(-1.0));

    const auto refused = [](const std::string &plot)
    {
        LoweredOutdoorMap unused;
        std::vector<ProjectIssue> found;
        CHECK_FALSE(lowerOutdoorProject(buildingProject(plot), unused, found));
        return found;
    };
    const std::string head = "      - building: building:home\n        at: [40, 40]\n        facing: s\n";
    CHECK(anyIssue(refused(head + "        walls: {s: [door, window]}\n"), "list 6 to 10 bays"));
    CHECK(anyIssue(refused(head + "        walls: {s: [wall, wall, wall, wall, wall, wall, windw, wall]}\n"),
        "which is no role of the part; it is so near the role `window`"));
    CHECK(anyIssue(refused(head + "        kit: marble\n"), "its kits are thatch, stone, shingle"));
    // Batch S4R: an outline may bend in, but not cross itself.
    CHECK(anyIssue(refused(head + "        parts:\n          - {shape: outline, outline: [[0, 0], [512, 0], "
        "[0, 512], [512, 512]]}\n"), "must not cross itself"));
    CHECK(anyIssue(refused(head + "        parts:\n          - {shape: round, radius: 128, roof: lean_to}\n"),
        "a lean_to needs a box"));
    CHECK(anyIssue(refused(head + "        parts:\n          - {at: [4096, 0], size: [512, 512]}\n"),
        "more than two cells outside its plot"));
    CHECK(anyIssue(refused(head + "        roof: hip\n        parapet: 64\n"), "stand round a flat roof"));
    CHECK(anyIssue(refused(head + "        door: none\n        house: 3\n"), "do not go together"));
}

TEST_CASE("a texture the world does not have is refused, with the plot that names it; liquids pass")
{
    LoweredOutdoorMap lowered = loweredBuildings("      - {building: building:home, at: [40, 40], facing: s, "
        "textures: {roof: slate99}}\n");
    std::vector<ProjectIssue> issues;
    checkOutdoorBuildingTextures(lowered.buildings, {"t14a01", "t14a04a", "t14a03", "t14a07", "t14a06", "t14a05b",
        "t14abcd11"}, "mm8", issues);
    REQUIRE(issues.size() == 1);
    CHECK(issues[0].message.find("the world mm8 has no texture slate99 (roof), named by building:home")
        != std::string::npos);
    CHECK(issues[0].message.find("oymap assets") != std::string::npos);
    // No list of textures at hand (no asset root): nothing is checked.
    issues.clear();
    checkOutdoorBuildingTextures(lowered.buildings, {}, "mm8", issues);
    CHECK(issues.empty());
    Game::OutdoorBModel model;
    model.name = "thing:well";
    Game::OutdoorBModelFace face;
    face.textureName = "WtrTyl";
    model.faces.push_back(face);
    face.textureName = "nosuch";
    model.faces.push_back(face);
    checkOutdoorModelTextures({model}, {"wtrtyl", "t06b01"}, "mm8", issues);
    REQUIRE(issues.size() == 1);
    CHECK(issues[0].message.find("`nosuch`, named by thing:well") != std::string::npos);
}

TEST_CASE("the ground under a plot is level at the building's floor; plots that cannot be houses are refused")
{
    // Land that rises to the south under the plot: a grid whose rows climb.
    std::string grid = "heights:\n  grid:\n    step: 8\n    unit: 64\n    rows:\n";

    for (int y = 0; y < 16; ++y)
    {
        grid += "      - [";

        for (int x = 0; x < 16; ++x)
        {
            grid += (x == 0 ? "" : ", ") + std::to_string(4 + y * 8);
        }

        grid += "]\n";
    }

    Project project = buildingProject("      - {building: building:home, at: [40, 40], facing: s}\n");
    ProjectFile &sketch = project.files["sketch.yml"];
    sketch.text.replace(sketch.text.find(LevelLand), std::string(LevelLand).size(), grid);
    sketch.document = YAML::Load(sketch.text);
    LoweredOutdoorMap lowered;
    std::vector<ProjectIssue> issues;
    REQUIRE(lowerOutdoorProject(project, lowered, issues));
    const int floor = static_cast<int>(lowered.buildings[0].base);
    CHECK(floor % 32 == 0);

    // The six nodes under the plot (x 40 to 42, y 40 and 41) lie at the floor; the slope goes on beside them.
    for (int x = 40; x <= 42; ++x)
    {
        CHECK(sampleAt(lowered, x, 40) * 32 == floor);
        CHECK(sampleAt(lowered, x, 41) * 32 == floor);
    }

    CHECK(sampleAt(lowered, 41, 44) * 32 > floor);
    CHECK(sampleAt(lowered, 41, 37) * 32 < floor);

    const auto refused = [](const std::string &plot)
    {
        LoweredOutdoorMap unused;
        std::vector<ProjectIssue> found;
        CHECK_FALSE(lowerOutdoorProject(buildingProject(plot), unused, found));
        return found;
    };
    CHECK(anyIssue(refused("      - {building: building:home, at: [40, 40], facing: s, parts: [{size: [64, 512]}]}\n"),
        "a door is 128 wide (a bay of at least 96)"));
    CHECK(anyIssue(refused("      - {building: building:home, at: [40, 40], facing: s, roof: onion}\n"),
        "the roof of a box part is flat, hip, gable, lean_to, cone, dome, none"));
    CHECK(anyIssue(refused("      - {building: building:home, at: [40, 40], facing: s, house: 3, "
        "into: {map: d07.blv}}\n"), "not both"));
    // The same shed with `form: none` is left out, and said.
    const LoweredOutdoorMap none = loweredBuildings("      - {building: building:shed, at: [40, 40], facing: s, "
        "form: none}\n");
    CHECK(none.buildings.empty());
    CHECK(std::any_of(none.warnings.begin(), none.warnings.end(), [](const std::string &warning)
    {
        return warning.find("1 plots with `form: none` raise nothing") != std::string::npos;
    }));
}

TEST_CASE("spawn points and scattered decorations stand on free land, the same places every time")
{
    const std::string more = "water:\n  bodies:\n"
        "    - {id: water:lake, kind: lake, level: 320, polygon: [[70, 20], [80, 20], [80, 30], [70, 30]]}\n"
        "roads:\n  - {link: road:a, line: [[30.5, 50.5], [60.5, 50.5]]}\n"
        "areas:\n  - {id: pop:wolves, count: 5, polygon: [[30, 44], [60, 44], [60, 56], [30, 56]]}\n"
        "  - {id: pop:wolves, slot: 3, circle: {at: [100, 100], r: 2}}\n"
        "  - {id: pop:wolves, kind: keep_clear, circle: {at: [20, 100], r: 2}}\n"
        "  - {id: pop:wolves, count: 3, polygon: [[72, 22], [78, 22], [78, 28], [72, 28]]}\n"
        "scatter:\n  - {decoration: Tree12, count: 40, polygon: [[36, 36], [48, 36], [48, 56], [36, 56]]}\n"
        "  - {decoration: rock17, count: 3, circle: {at: [100, 20], r: 3}, spacing: 2}\n";
    const Project project = buildingProject("      - {building: building:home, at: [40, 40], facing: s}\n", more);
    LoweredOutdoorMap lowered;
    std::vector<ProjectIssue> issues;
    REQUIRE(lowerOutdoorProject(project, lowered, issues));
    const std::string table = "#\tInternalName\tHint\n1\tnothing\t\n377\trock17\trock\n464\ttree12\ttree\n";
    OutdoorPlaces places;
    std::vector<std::string> warnings;
    REQUIRE(placeOutdoorThings(project, lowered, table, places, issues, warnings));
    // Five markers of the wolves' slot (the second of the map's slots), one of slot 3, none for the keep-clear
    // area, none in the lake.
    REQUIRE(places.spawns.size() == 6);
    CHECK(places.spawns[0].slot == 2);
    CHECK(places.spawns[5].slot == 3);
    CHECK(std::any_of(warnings.begin(), warnings.end(), [](const std::string &warning)
    {
        return warning.find("3 spawn points found no place") != std::string::npos;
    }));
    REQUIRE(places.decorations.size() == 43);
    CHECK(places.decorations[0].name == "tree12");
    CHECK(places.decorations[0].listId == 463);
    CHECK(places.decorations[42].listId == 376);
    const auto cellOf = [](int x, int y)
    {
        return std::array<double, 2>{x / 512.0 + 64.0, 64.0 - y / 512.0};
    };

    for (const OutdoorPlacedDecoration &decoration : places.decorations)
    {
        const std::array<double, 2> cell = cellOf(decoration.x, decoration.y);
        // Not on the road's cells (row 50), not within a quarter cell of the house (40 to 42, 40 to 41.5).
        CHECK(static_cast<int>(cell[1]) != 50);
        CHECK_FALSE((cell[0] > 39.75 && cell[0] < 42.25 && cell[1] > 39.75 && cell[1] < 41.75));
        CHECK(decoration.z == 640);
    }

    for (const OutdoorPlacedSpawn &spawn : places.spawns)
    {
        CHECK(static_cast<int>(cellOf(spawn.x, spawn.y)[1]) != 50);
    }

    // The three rocks keep their distance of two cells.
    for (size_t first = 40; first < 43; ++first)
    {
        for (size_t second = first + 1; second < 43; ++second)
        {
            CHECK(std::hypot(places.decorations[first].x - places.decorations[second].x,
                places.decorations[first].y - places.decorations[second].y) >= 1024.0);
        }
    }

    OutdoorPlaces again;
    std::vector<std::string> unused;
    REQUIRE(placeOutdoorThings(project, lowered, table, again, issues, unused));
    REQUIRE(again.decorations.size() == places.decorations.size());

    for (size_t index = 0; index < again.decorations.size(); ++index)
    {
        CHECK(again.decorations[index].x == places.decorations[index].x);
        CHECK(again.decorations[index].y == places.decorations[index].y);
    }

    // A decoration the table does not have is refused; without the table the scatter is left out and said.
    Project unknown = buildingProject("      - {building: building:home, at: [40, 40], facing: s}\n",
        "scatter:\n  - {decoration: palm99, count: 1, circle: {at: [100, 20], r: 3}}\n");
    std::vector<ProjectIssue> found;
    CHECK_FALSE(placeOutdoorThings(unknown, lowered, table, again, found, unused));
    CHECK(anyIssue(found, "there is no decoration named palm99"));
    std::vector<std::string> said;
    REQUIRE(placeOutdoorThings(project, lowered, "", again, issues, said));
    CHECK(again.decorations.empty());
    CHECK(std::any_of(said.begin(), said.end(), [](const std::string &warning)
    {
        return warning.find("needs an asset root") != std::string::npos;
    }));
}

// ---- Structures, their events, travel and the rest of the second batch (core/OutdoorThings, OutdoorInstall) ----

#include "core/ChestKinds.h"
#include "core/Coplanar.h"
#include "core/OutdoorBuild.h"
#include "core/OutdoorThings.h"
#include "game/maps/OutdoorSceneYml.h"

#include <fstream>

namespace
{
// The things of a project with the house of `buildingProject` and what the test adds to the sketch.
OutdoorThings thingsOf(const std::string &more, std::vector<ProjectIssue> &issues, IdsLock &ids,
    std::vector<std::string> *pWarnings = nullptr, const OutdoorDoorPictures *pDoorPictures = nullptr)
{
    const Project project = buildingProject("      - {building: building:home, at: [40, 40], facing: s}\n", more);
    LoweredOutdoorMap lowered;
    std::vector<ProjectIssue> lowering;
    REQUIRE(lowerOutdoorProject(project, lowered, lowering, nullptr, {}, pDoorPictures));
    OutdoorThings things;
    std::vector<std::string> warnings;
    OutdoorEventWords words(project, {}, ids, issues);
    raiseOutdoorThings(project, lowered, {}, ids, words, things, issues,
        pWarnings != nullptr ? *pWarnings : warnings);
    return things;
}

const OutdoorEventPlan *eventOf(const OutdoorThings &things, const std::string &id)
{
    for (const OutdoorEventPlan &event : things.events)
    {
        if (event.id == id)
        {
            return &event;
        }
    }

    return nullptr;
}
}

TEST_CASE("chests outdoors: the shipped chest of a kind (7out01 chest_N), a box of its own textures with a warning")
{
    // The kind's faces: MM7's chest is 19 faces (a 4, b 10, c 2, e 1, g 2).
    const std::optional<ChestKind> kind = chestKindOf("7gt002");
    REQUIRE(kind);
    const std::vector<ChestFace> faces = chestKindFaces(*kind, kind->size, 0.0, 80.0);
    std::map<std::string, int> letters;

    for (const ChestFace &face : faces)
    {
        ++letters[face.texture];
    }

    CHECK(faces.size() == 19);
    CHECK(letters == std::map<std::string, int>{{"7gt002a", 4}, {"7gt002b", 10}, {"7gt002c", 2}, {"7gt002e", 1},
        {"7gt002g", 2}});
    CHECK(defaultChestKind("mm8") == "gt002");
    CHECK(defaultChestKind("mm7") == "7gt002");
    CHECK(defaultChestKind("mm6") == "ch1");

    std::vector<ProjectIssue> issues;
    std::vector<std::string> warnings;
    IdsLock ids;
    const OutdoorThings things = thingsOf("structures:\n"
        "  - {id: thing:chest, kind: chest, at: [52.25, 50], chest_kind: 7gt002}\n"
        "  - {id: thing:plain, kind: chest, at: [54.25, 50]}\n"
        "  - {id: thing:own, kind: chest, at: [56.25, 50], textures: {wall: 7gt002a, top: 7gt002b}}\n", issues, ids,
        &warnings);
    REQUIRE(issues.empty());
    REQUIRE(things.models.size() == 3);
    const Game::OutdoorBModel &chest = things.models[0];
    CHECK(chest.faces.size() == 19);
    CHECK(chest.maxX - chest.minX == 96);
    CHECK(chest.maxY - chest.minY == 64);
    CHECK(chest.maxZ - chest.minZ == 80);

    for (const Game::OutdoorBModelFace &face : chest.faces)
    {
        const auto [lowU, highU] = std::minmax_element(face.textureUs.begin(), face.textureUs.end());
        const auto [lowV, highV] = std::minmax_element(face.textureVs.begin(), face.textureVs.end());

        // chest_N's: the front slope's own picture looks north; the middles 64 across, the end pieces 16, the
        // short ends 64 across the chest's depth.
        if (face.textureName == "7gt002e")
        {
            CHECK(face.planeNormalY > 40000);
            CHECK(face.planeNormalZ > 40000);
            CHECK(*highV - *lowV == 16);
        }
        else if (face.textureName == "7gt002a")
        {
            CHECK(*highU - *lowU == 64);
        }
        else if (face.textureName == "7gt002b")
        {
            CHECK(*highU - *lowU == 16);
            CHECK((*lowU == 0 || *lowU == 48));
        }
        else if (face.textureName == "7gt002c")
        {
            CHECK(*highU - *lowU == 64);
            CHECK(*highV - *lowV == 64);
            CHECK(std::abs(face.planeNormalX) == 65536);
        }
    }

    // The world's own (mm8: gt002) without a word; a box of its own textures keeps the 9 faces, with a warning.
    CHECK(things.models[1].faces.size() == 19);
    CHECK(std::all_of(things.models[1].faces.begin(), things.models[1].faces.end(),
        [](const Game::OutdoorBModelFace &face)
    {
        return face.textureName.starts_with("gt002");
    }));
    CHECK(things.models[2].faces.size() == 9);
    CHECK(std::any_of(warnings.begin(), warnings.end(), [](const std::string &warning)
    {
        return warning.find("not a shipped chest") != std::string::npos;
    }));
    std::vector<ProjectIssue> unknown;
    IdsLock unknownIds;
    thingsOf("structures:\n  - {id: thing:a, kind: chest, at: [50, 50], chest_kind: ch9}\n", unknown, unknownIds);
    CHECK(anyIssue(unknown, "no chest kind"));
}

TEST_CASE("the ground things stand on: the game's two triangles per cell, split north-west to south-east")
{
    LoweredOutdoorMap lowered;
    lowered.samples.assign(static_cast<size_t>(OutdoorNodeCount) * OutdoorNodeCount, 0);
    // A cell (10, 20) with corners north-west 0, north-east 8, south-west 2, south-east 4 (steps of 32).
    lowered.samples[20 * OutdoorNodeCount + 10] = 0;
    lowered.samples[20 * OutdoorNodeCount + 11] = 8;
    lowered.samples[21 * OutdoorNodeCount + 10] = 2;
    lowered.samples[21 * OutdoorNodeCount + 11] = 4;
    CHECK(lowered.groundHeightAt(10.0, 20.0) == doctest::Approx(0.0));
    CHECK(lowered.groundHeightAt(11.0, 20.0) == doctest::Approx(256.0));
    CHECK(lowered.groundHeightAt(10.0, 21.0) == doctest::Approx(64.0));
    CHECK(lowered.groundHeightAt(11.0, 21.0) == doctest::Approx(128.0));
    // On the diagonal: halfway between north-west and south-east (the bilinear surface says 112 there).
    CHECK(lowered.groundHeightAt(10.5, 20.5) == doctest::Approx(64.0));
    CHECK(lowered.storedHeightAt(10.5, 20.5) == doctest::Approx(112.0));
    // Each triangle is flat: the north-east one through NW, NE and SE, the south-west one through NW, SW and SE.
    CHECK(lowered.groundHeightAt(10.75, 20.25) == doctest::Approx(0.75 * 256.0 + 0.25 * (128.0 - 256.0)));
    CHECK(lowered.groundHeightAt(10.25, 20.75) == doctest::Approx(0.75 * 64.0 + 0.25 * (128.0 - 64.0)));
}

TEST_CASE("structures: a wall with a walkable top, a gate and merlons; a bridge deck on the land; a well; a chest")
{
    std::vector<ProjectIssue> issues;
    IdsLock ids;
    const OutdoorThings things = thingsOf("structures:\n"
        "  - {id: thing:town_wall, kind: wall, line: [[70, 70], [80, 70], [80, 80]], height: 384, thickness: 128, "
        "battlements: true, gates: [{at: [75, 70], width: 384, height: 320}]}\n"
        "  - {id: thing:bridge, kind: bridge, line: [[20, 90], [28, 90]], width: 384, kerb: 64, rise: 128}\n"
        "  - {id: thing:well, kind: well, at: [50.5, 50.5], title: Drink from the well, once: true, "
        "effects: [{add: {var: MightBonus, value: 25}}, {text: Might +25}, {autonote: 210}]}\n"
        "  - {id: thing:chest, kind: chest, at: [52.25, 50], turn: 90, chest: {level: 3, random_items: 4, "
        "items: [501]}}\n"
        "  - {id: thing:cave, kind: doorway, at: [60, 60], turn: 180, title: Enter the Cave, "
        "into: {map: d07.blv, at: [1, 2, 3], facing: 512}}\n"
        "  - {id: thing:post, kind: sign, at: [55, 55], title: To the Harbour}\n", issues, ids);

    for (const ProjectIssue &issue : issues)
    {
        MESSAGE(issue.path << ": " << issue.message);
    }

    REQUIRE(issues.empty());
    REQUIRE(things.models.size() == 6);
    const Game::OutdoorBModel &wall = things.models[0];
    // The top is level, 384 over the land (640), with merlons 64 on it; the wall goes 64 into the ground. Two
    // stretches of 5120, mitred at the corner: the outer side reaches half the thickness further.
    CHECK(wall.name == "thing:town_wall");
    CHECK(wall.maxZ == 640 + 384 + 64);
    CHECK(wall.minZ == 640 - 64);
    CHECK(wall.maxX == (80 - 64) * 512 + 64);
    // A top one can stand on at 1024, and the lintel's underside 320 over the ground in the gate.
    CHECK(std::count_if(wall.faces.begin(), wall.faces.end(), [&wall](const Game::OutdoorBModelFace &face)
    {
        return face.polygonType == 3 && wall.vertices[face.vertexIndices[0]].z == 640 + 384;
    }) >= 3);
    CHECK(std::count_if(wall.faces.begin(), wall.faces.end(), [&wall](const Game::OutdoorBModelFace &face)
    {
        return face.polygonType == 5 && wall.vertices[face.vertexIndices[0]].z == 640 + 320;
    }) == 1);

    // No face of the wall stands in the gate's opening below the lintel.
    for (const Game::OutdoorBModelFace &face : wall.faces)
    {
        double x = 0.0;
        double z = 0.0;

        for (const uint16_t index : face.vertexIndices)
        {
            x += wall.vertices[index].x / static_cast<double>(face.vertexIndices.size());
            z += wall.vertices[index].z / static_cast<double>(face.vertexIndices.size());
        }

        const double gateX = (75 - 64) * 512.0;
        CHECK_FALSE((std::fabs(x - gateX) < 150.0 && z < 640 + 300 && z > 640 && face.polygonType == 1
            && std::abs(face.planeNormalY) > 60000));
    }

    const Game::OutdoorBModel &bridge = things.models[1];
    // The deck rests 16 over the land at both ends and is 128 higher in its middle; kerbs of 64 on it.
    CHECK(bridge.maxZ == 640 + 16 + 128 + 64);
    CHECK(bridge.maxX - bridge.minX == 8 * 512);
    CHECK(bridge.maxY - bridge.minY == 384);
    CHECK(std::count_if(bridge.faces.begin(), bridge.faces.end(), [](const Game::OutdoorBModelFace &face)
    {
        return face.polygonType == 4 || face.polygonType == 3;
    }) >= 4);

    // The well: every face runs its event; the event adds once, by a map variable of its own.
    const Game::OutdoorBModel &well = things.models[2];
    const OutdoorEventPlan *pWell = eventOf(things, "evt:thing:well");
    REQUIRE(pWell != nullptr);
    CHECK(pWell->title == "Drink from the well");
    REQUIRE(pWell->body.size() == 5);
    CHECK(pWell->body[0] == "if IsAtLeast(MapVar(0), 1) then return end");
    CHECK(pWell->body[2] == "AddValue(MightBonus, 25)");
    CHECK(pWell->body[3] == "evt.StatusText(\"Might +25\")");
    CHECK(pWell->body[4] == "SetAutonote(210)");
    CHECK(std::all_of(well.faces.begin(), well.faces.end(), [pWell](const Game::OutdoorBModelFace &face)
    {
        return face.cogTriggeredNumber == pWell->number;
    }));
    CHECK(std::any_of(well.faces.begin(), well.faces.end(), [](const Game::OutdoorBModelFace &face)
    {
        return face.textureName == "wtrtyl" && face.polygonType == 3;
    }));

    // The chest: 64 by 96 when turned, 80 high, and a chest record with what the sketch puts in.
    const Game::OutdoorBModel &chest = things.models[3];
    CHECK(chest.maxX - chest.minX == 64);
    CHECK(chest.maxY - chest.minY == 96);
    CHECK(chest.maxZ - chest.minZ == 80);
    REQUIRE(things.chests.size() == 1);
    CHECK(things.chests[0].level == 3);
    CHECK(things.chests[0].randomItems == 4);
    CHECK(things.chests[0].items == std::vector<int>{501});
    const OutdoorEventPlan *pChest = eventOf(things, "evt:thing:chest");
    REQUIRE(pChest != nullptr);
    CHECK(pChest->title == "Chest");
    CHECK(pChest->body == std::vector<std::string>{"evt.OpenChest(0)"});
    CHECK(things.chestOfEvent.at(pChest->number) == 0);

    // The doorway looks north when turned half round, and leads into the cave.
    const OutdoorEventPlan *pCave = eventOf(things, "evt:thing:cave");
    REQUIRE(pCave != nullptr);
    CHECK(pCave->body == std::vector<std::string>{"evt.MoveToMap(1, 2, 3, 512, 0, 0, 0, 1, \"d07.blv\")"});
    CHECK(std::any_of(things.models[4].faces.begin(), things.models[4].faces.end(),
        [](const Game::OutdoorBModelFace &face)
    {
        return face.textureName == "t14c03" && face.planeNormalY > 60000;
    }));
    // A sign only says its title.
    const OutdoorEventPlan *pSign = eventOf(things, "evt:thing:post");
    REQUIRE(pSign != nullptr);
    CHECK(pSign->body.empty());

    // The numbers stay with their ids: built again with a structure put in front, every old id keeps its number.
    IdsLock again = ids;
    std::vector<ProjectIssue> unused;
    const OutdoorThings more = thingsOf("structures:\n"
        "  - {id: thing:new_sign, kind: sign, at: [56, 56], title: New}\n"
        "  - {id: thing:well, kind: well, at: [50.5, 50.5], title: Drink from the well}\n", unused, again);
    CHECK(eventOf(more, "evt:thing:well")->number == pWell->number);
    CHECK(eventOf(more, "evt:thing:new_sign")->number > pSign->number);
}

TEST_CASE("structures that cannot be built are refused, with what to change")
{
    const auto refused = [](const std::string &structure)
    {
        std::vector<ProjectIssue> issues;
        IdsLock ids;
        thingsOf("structures:\n" + structure, issues, ids);
        return issues;
    };
    CHECK(anyIssue(refused("  - {id: thing:a, kind: ship, at: [50, 50]}\n"), "needs a model of its own"));
    CHECK(anyIssue(refused("  - {id: thing:a, kind: well, at: [50, 50]}\n"
        "  - {id: thing:a, kind: well, at: [52, 50]}\n"), "two structures have the id thing:a"));
    CHECK(anyIssue(refused("  - {id: thing:a, kind: wall, line: [[50, 50]]}\n"), "two or more points"));
    CHECK(anyIssue(refused("  - {id: thing:a, kind: wall, line: [[50, 50], [60, 50]], gates: [{at: [50, 50]}]}\n"),
        "too near a corner of the wall"));
    CHECK(anyIssue(refused("  - {id: thing:a, kind: chest, at: [50, 50], house: 3}\n"), "one of them"));
    CHECK(anyIssue(refused("  - {id: thing:a, kind: well, at: [50, 50], effects: [{explode: 3}]}\n"),
        "is not one an outdoor structure has"));
    CHECK(anyIssue(refused("  - {id: thing:a, kind: obelisk, at: [50, 50], width: 512, height: 100}\n"),
        "at least as high as wide"));
    // Naming a decoration or a monster needs the tables of an asset root: left out and said, not refused.
    std::vector<ProjectIssue> issues;
    std::vector<std::string> warnings;
    IdsLock ids;
    const OutdoorThings things = thingsOf("structures:\n  - {id: thing:tree, kind: decoration, decoration: tree12, "
        "at: [50, 50]}\nactors:\n  - {monster: Peasant, at: [51, 51], count: 3}\n", issues, ids, &warnings);
    CHECK(issues.empty());
    CHECK(things.decorations.empty());
    CHECK(things.actors.empty());
    CHECK(warnings.size() == 2);
}

TEST_CASE("an outdoor map's edges become its row of the travel table, and its neighbours lead back to it")
{
    Project project = buildingProject("      - {building: building:home, at: [40, 40], facing: s}\n");
    ProjectFile &card = project.files["project.yml"];
    card.text += "name: Test Vale\nneighbours:\n"
        "  - {id: edge:north, to: out03.odm, kind: edge, side: north, days: 5}\n"
        "  - {id: edge:east, to: out06, kind: edge, side: east, days: 3, arrival_side: north, one_way: true}\n"
        "  - {id: door:cave, to: d07.blv, kind: door}\n"
        "  - {id: edge:south_west, to: out03.odm, kind: edge, side: south, span: [-32768, 0], days: 2,"
        " arrival: [0, 0, 0]}\n";
    card.document = YAML::Load(card.text);
    const std::vector<OutdoorTravelEdge> edges = outdoorTravelEdges(project);
    REQUIRE(edges.size() == 3);
    CHECK(edges[0].arrivalSide == "south");
    CHECK_FALSE(edges[0].span.has_value());
    CHECK(edges[1].map == "out06.odm");
    CHECK(edges[1].oneWay);
    // A span of a side is the world's edge_spans table's, not a travel row (nor a way back).
    CHECK(edges[2].span == std::make_pair(-32768, 0));
    const std::filesystem::path table = std::filesystem::temp_directory_path() / "oymap_travel_test.txt";
    {
        std::ofstream stream(table);
        stream << "Key map\tUp\tSide\tDays\tDown\tSide\tDays\tLeft\tSide\tDays\tRight\tSide\tDays\t"
                  "StraightTravel\tNotes\n"
               << "out03.odm\tout04.odm\tright\t10\tout02.odm\tup\t5\t\t\t\t\t\t\t\tAlvar\n"
               << "out06.odm\tout04.odm\tdown\t5\t\t\t\t\t\t\t\t\t\t\tShadowspire\n";
    }
    std::vector<std::string> changes;
    std::string errorMessage;
    REQUIRE(upsertOutdoorTravelRows(project, table, changes, errorMessage));
    std::ifstream stream(table);
    std::string text((std::istreambuf_iterator<char>(stream)), std::istreambuf_iterator<char>());
    // Its own row: north to Alvar's south side in 5 days, east to Shadowspire's north side in 3, nothing south.
    CHECK(text.find("groundtest.odm\tout03.odm\tdown\t5\t\t\t\t\t\t\tout06.odm\tup\t3\t\tTest Vale")
        != std::string::npos);
    // Alvar's south side leads here now, to this map's north side; Shadowspire's row is as it was (one way).
    CHECK(text.find("out03.odm\tout04.odm\tright\t10\tgroundtest.odm\tup\t5") != std::string::npos);
    CHECK(text.find("out06.odm\tout04.odm\tdown\t5\t\t\t\t\t\t\t\t\t\t\tShadowspire") != std::string::npos);
    CHECK(changes.size() == 3);
    // Written again it is the same table: one row for the map.
    std::vector<std::string> second;
    REQUIRE(upsertOutdoorTravelRows(project, table, second, errorMessage));
    std::ifstream again(table);
    const std::string textAgain((std::istreambuf_iterator<char>(again)), std::istreambuf_iterator<char>());
    CHECK(textAgain == text);
    std::error_code error;
    std::filesystem::remove(table, error);
}

TEST_CASE("an outdoor map's sky and weather: its row of the bolster table, the reference's under its own number")
{
    Project project = buildingProject("      - {building: building:home, at: [40, 40], facing: s}\n");
    ProjectFile &card = project.files["project.yml"];
    card.document = YAML::Load("format: 0\nid: groundtest\nworld: mm8\nkind: outdoor\nname: Test Vale\n"
        "map_stats: {id: 9901, reference: OUT02.odm}\n");
    const std::filesystem::path tables = std::filesystem::temp_directory_path() / "oymap_bolster_test";
    std::error_code error;
    std::filesystem::create_directories(tables, error);
    const auto writeTables = [&tables]()
    {
        std::ofstream stats(tables / "map_stats.txt");
        stats << "#\tName\tFile\n2\tRavenshore\tout02.odm\n63\tHarmondale\t7out02.odm\n";
        std::ofstream bolster(tables / "bolster_maps.txt");
        bolster << "#\tNote\tContinent\tBolster kind\tSpells\tSummons\tWeather\tBolster extra\tProfs max rarity\t"
                   "Custom sky\tRain\tSnow\r\n"
                << "2\tRavenshore\t1\tLowerToEqual\tx\t-\tx\t0\t20\t\r\n"
                << "63\tHarmondale\t2\tLowerToEqual\tx\t-\tx\t0\t20\t\t\tx\r\n";
    };
    const auto tableText = [&tables]()
    {
        std::ifstream stream(tables / "bolster_maps.txt", std::ios::binary);
        return std::string((std::istreambuf_iterator<char>(stream)), std::istreambuf_iterator<char>());
    };
    writeTables();
    std::vector<std::string> changes;
    std::string errorMessage;
    // The reference's row under the project's number and name: Jadame's skies, rain by the world's chances.
    REQUIRE(upsertOutdoorWeatherRow(project, tables, changes, errorMessage));
    std::string text = tableText();
    CHECK(text.find("\r\n9901\tTest Vale\t1\tLowerToEqual\tx\t-\tx\t0\t20\t\r\n") != std::string::npos);
    CHECK(text.find("2\tRavenshore\t1\tLowerToEqual\tx\t-\tx\t0\t20\t\r\n") != std::string::npos);
    REQUIRE(changes.size() == 1);
    CHECK(changes[0].find("continent 1, as out02.odm, rain, no snow") != std::string::npos);
    // Written again it is the same table.
    REQUIRE(upsertOutdoorWeatherRow(project, tables, changes, errorMessage));
    CHECK(tableText() == text);

    // What the project says itself lies over the reference: another continent, snow without rain, one sky.
    card.document = YAML::Load("format: 0\nid: groundtest\nworld: mm8\nkind: outdoor\nname: Test Vale\n"
        "map_stats: {id: 9901, reference: out02.odm, continent: 3}\n");
    ProjectFile &atmosphere = project.files["atmosphere.yml"];
    atmosphere.name = "atmosphere.yml";
    atmosphere.text = "format: 0\nsky: sunsetclouds\nweather: {snow: true}\n";
    atmosphere.document = YAML::Load(atmosphere.text);
    changes.clear();
    REQUIRE(upsertOutdoorWeatherRow(project, tables, changes, errorMessage));
    text = tableText();
    CHECK(text.find("9901\tTest Vale\t3\tLowerToEqual\tx\t-\tx\t0\t20\tsunsetclouds\t-\tx\r\n") != std::string::npos);
    CHECK(changes[0].find("no rain, snow, the sky sunsetclouds") != std::string::npos);

    // Without a reference: a plain row on the world's own continent, monsters as the tables have them, no weather
    // until the project asks for it.
    writeTables();
    card.document = YAML::Load("format: 0\nid: groundtest\nworld: mm7\nkind: outdoor\nname: New Dale\n"
        "map_stats: {id: 9902, slots: []}\n");
    project.files.erase("atmosphere.yml");
    changes.clear();
    REQUIRE(upsertOutdoorWeatherRow(project, tables, changes, errorMessage));
    CHECK(tableText().find("9902\tNew Dale\t2\t0\t-\t-\t-\t0\t\t\r\n") != std::string::npos);
    CHECK(changes[0].find("continent 2, a plain row, no rain, no snow") != std::string::npos);

    // An indoor project, an overlay and a card without a number get no row.
    card.document = YAML::Load("format: 0\nid: groundtest\nworld: mm7\nkind: outdoor\n");
    CHECK(!outdoorWeatherRow(project).written);
    card.document = YAML::Load("format: 0\nid: groundtest\nworld: mm7\nkind: indoor\nmap_stats: {id: 9902}\n");
    CHECK(!outdoorWeatherRow(project).written);
    std::filesystem::remove_all(tables, error);
}

TEST_CASE("a dry build is what validate runs: arrival points, travel, ids and what cannot be placed are checked")
{
    Project project = buildingProject("      - {building: building:home, at: [40, 40], facing: s, house: 904, "
        "title: Home}\n", "areas:\n  - {id: pop:wolves, slot: 5, circle: {at: [100, 100], r: 2}}\n");
    std::vector<ProjectIssue> issues;
    validateOutdoorProject(project, issues);
    // A check the build makes when it places the spawn points: now also validate's.
    CHECK(anyIssue(issues, "a map has three monster slots"));
    const size_t found = issues.size();
    validateOutdoorProject(project, issues);
    CHECK(issues.size() == found);

    Project good = buildingProject("      - {building: building:home, at: [40, 40], facing: s, house: 904, "
        "title: Home}\n", "points:\n  - {id: entrance:north, at: [64, 20], facing: s}\n");
    ProjectFile &card = good.files["project.yml"];
    card.text += "neighbours:\n  - {id: edge:north, to: out03.odm, kind: edge, side: north, days: 5}\n";
    card.document = YAML::Load(card.text);
    ProjectFile &plan = good.files["plan.yml"];
    plan.text.replace(plan.text.find("{id: entrance:north, kind: arrival, facing: s}"), 46,
        "{id: entrance:north, kind: arrival, facing: s, neighbour: edge:north}");
    plan.document = YAML::Load(plan.text);
    ProjectFile air;
    air.name = "atmosphere.yml";
    air.text = "format: 0\nsky: sky05\nprecipitation: rain\nash: 40\ndaily_fog:\n  small: {chance: 20, weak_distance: 4096, "
        "strong_distance: 8192}\n";
    air.document = YAML::Load(air.text);
    good.files[air.name] = air;
    good.root = std::filesystem::temp_directory_path() / "oymap_outdoor_dry";
    BuildOptions options;
    options.outputDirectory = good.root / "build";
    BuildResult result;
    const bool built = buildOutdoorProject(good, options, result);

    for (const ProjectIssue &issue : result.issues)
    {
        MESSAGE(issue.path << ": " << issue.message);
    }

    REQUIRE(built);
    const auto fileText = [&good](const char *pName)
    {
        std::ifstream stream(good.root / "build" / pName);
        return std::string((std::istreambuf_iterator<char>(stream)), std::istreambuf_iterator<char>());
    };
    const std::string scene = fileText("groundtest.scene.yml");
    // The arrival point for those who come from the north, under the name the game looks for; the sky, the rain
    // and the daily fog of the atmosphere.
    CHECK(scene.find("north start") != std::string::npos);
    CHECK(scene.find("sky05") != std::string::npos);
    CHECK(scene.find("precipitation: rain") != std::string::npos);
    CHECK(scene.find("small_chance: 20") != std::string::npos);
    // D-40: the map's ash chance in the scene's weather.
    CHECK(scene.find("ash_chance: 40") != std::string::npos);
    const std::string lua = fileText("groundtest.lua");
    CHECK(lua.find("evt.EnterHouse(904)") != std::string::npos);
    CHECK(lua.find("RegisterEvent(2, \"Home\", nil, \"Home\")") != std::string::npos);
    const std::string json = fileText("build.json");
    CHECK(json.find("\"arrival_side\": \"south\"") != std::string::npos);
    // The lock was written beside the project, with the door's and the name's numbers.
    std::ifstream lockStream(good.root / "ids.lock.yml");
    const std::string lock((std::istreambuf_iterator<char>(lockStream)), std::istreambuf_iterator<char>());
    CHECK(lock.find("evt:door:building:home: 1") != std::string::npos);
    CHECK(lock.find("evt:name:building:home: 2") != std::string::npos);
    std::error_code error;
    std::filesystem::remove_all(good.root, error);
}

TEST_CASE("the measure: an event on houses that stand apart is a thing at each; a ring without a roof has its ring")
{
    // One name event on two houses twenty cells apart, as the shipped maps share one over a street of houses: the
    // rebuild gives each house its own. Two things in both maps, each where its house is.
    Game::OutdoorMapData original = testMap();
    original.bmodels = {testHouse(-8192, 0, 512, 512, 320, 256, 7), testHouse(2048, 0, 512, 512, 320, 256, 7)};
    Game::OutdoorMapData rebuilt = original;
    rebuilt.bmodels[1] = testHouse(2048, 0, 512, 512, 320, 256, 8);
    const OutdoorCompareResult apart = compared(original, rebuilt);
    CHECK(apart.originalEvents == 2);
    CHECK(apart.rebuiltEvents == 2);
    CHECK(partOf(apart, "events") == doctest::Approx(1.0));
    // Models that touch are one thing cut in pieces (a ship): one event on both is one place.
    Game::OutdoorMapData ship = testMap();
    ship.bmodels = {testHouse(0, 0, 512, 512, 320, 256, 7), testHouse(512, 0, 512, 512, 320, 256, 7)};
    CHECK(compared(ship, ship).originalEvents == 1);

    // A ring wall without a roof: four upright faces and nothing that lies. It has its ring as its footprint,
    // and the same ring in the rebuild is the same building.
    Game::OutdoorMapData ring = testMap();
    ring.bmodels = {testHouse(0, 0, 512, 512, 320, 64, 0)};
    ring.bmodels[0].faces.erase(ring.bmodels[0].faces.begin(), ring.bmodels[0].faces.begin() + 2);
    const OutdoorCompareResult rings = compared(ring, ring);
    CHECK(rings.matchedBuildings == 1);
    CHECK(partOf(rings, "buildings") == doctest::Approx(1.0));
    // Against a map without it the ring is missed: it counts.
    CHECK(partOf(compared(ring, testMap()), "buildings") == doctest::Approx(0.0));
}

TEST_CASE("the measure: a clump of decorations across a region's border counts as it stands")
{
    // Ten trees half a cell west of the border between regions A and B (x = 16 cells), and the same clump a cell
    // further east, across the border: the same trees in the same place, to a cell.
    Game::OutdoorMapData original = testMap();
    Game::OutdoorMapData moved = testMap();

    for (int tree = 0; tree < 10; ++tree)
    {
        original.entities.push_back(testDecoration("tree12", (16 - 64) * 512 - 256, (64 - 40 - tree) * 512));
        moved.entities.push_back(testDecoration("tree12", (16 - 64) * 512 + 256, (64 - 40 - tree) * 512));
    }

    CHECK(partOf(compared(original, moved), "decorations") == doctest::Approx(1.0));
    CHECK(partOf(compared(original, original), "decorations") == doctest::Approx(1.0));
    // Trees that stand somewhere else altogether are still missed, and another kind in the same place is half
    // right (the density, not the kind).
    Game::OutdoorMapData far = testMap();
    Game::OutdoorMapData rocks = testMap();

    for (int tree = 0; tree < 10; ++tree)
    {
        far.entities.push_back(testDecoration("tree12", (100 - 64) * 512, (64 - 100) * 512 + tree * 64));
        rocks.entities.push_back(testDecoration("rock17", (16 - 64) * 512 - 256, (64 - 40 - tree) * 512));
    }

    CHECK(partOf(compared(original, far), "decorations") == doctest::Approx(0.0));
    CHECK(partOf(compared(original, rocks), "decorations") == doctest::Approx(0.5));
    // The totals are whole decorations.
    const OutdoorCompareResult result = compared(original, moved);
    REQUIRE(result.decorationKinds.size() == 1);
    CHECK(result.decorationKinds[0].second == std::array<size_t, 2>{10, 10});
}

TEST_CASE("checks: cliff lines that go on from one point are joined; a gap a road runs through is a pass")
{
    const auto short_of = [](const std::string &more)
    {
        std::vector<ProjectIssue> issues;
        validateSketch(outdoorProject(std::string(LevelLand) + more), issues);
        return anyIssue(issues, "cells short of");
    };
    // The second line goes on from the first's last point, at a sharp turn back: joined.
    CHECK_FALSE(short_of("  cliffs:\n    - {line: [[95, 13], [98, 18], [98, 22], [96, 23]], drop: 640, down: left}\n"
        "    - {line: [[96, 23], [94, 24], [92, 27], [96, 31]], drop: 640, down: left}\n"));
    // A line that ends two cells short of another that runs across it: a gap the land runs through.
    const std::string gap = "  cliffs:\n    - {line: [[40, 60], [50, 60]], drop: 640, down: left}\n"
        "    - {line: [[52, 50], [52, 70]], drop: 640, down: left}\n";
    CHECK(short_of(gap));
    // The same gap with a road through it is a pass.
    CHECK_FALSE(short_of(gap + "roads:\n  - {link: road:pass, line: [[51, 40], [51, 80]]}\n"));
}

TEST_CASE("ground drawn to the map's edge reaches its east column and south row; a wall shorter than a bay")
{
    const LoweredOutdoorMap lowered = loweredOf(std::string(LevelLand)
        + "ground:\n  - {material: grass, polygon: [[0, 0], [128, 0], [128, 128], [0, 128]]}\n");
    // Grass all over: every cell is a plain grass tile or one of its variants (the first twelve of the set), none
    // leads over to dirt along the east and south edges.
    size_t toDirt = 0;

    for (int index = 0; index < Side; ++index)
    {
        toDirt += tileAt(lowered, Side - 1, index) >= OutdoorFirstSetTile + 12 ? 1 : 0;
        toDirt += tileAt(lowered, index, Side - 1) >= OutdoorFirstSetTile + 12 ? 1 : 0;
        toDirt += tileAt(lowered, Side - 1, index) == OutdoorDirtTile ? 1 : 0;
    }

    CHECK(toDirt == 0);
    // A wall of 64 takes no list of bays: said as it is.
    LoweredOutdoorMap unused;
    std::vector<ProjectIssue> found;
    CHECK_FALSE(lowerOutdoorProject(buildingProject("      - {building: building:home, at: [40, 40], facing: s, "
        "door: none, parts: [{size: [64, 512], walls: {s: [wall]}}]}\n"), unused, found));
    CHECK(anyIssue(found, "shorter than the narrowest bay"));
    CHECK_FALSE(anyIssue(found, "list 1 bays"));
}

TEST_CASE("a door on a short outline face takes the face's listed bays")
{
    // The Eye of Newt's west face (Castle Ironfist): 160 long, listed as [wall, 16], [door, 128], [wall, 16]: three
    // bays, the door in bay 1 (the length alone holds one).
    const LoweredOutdoorMap lowered = loweredBuildings("      - {building: building:home, at: [40, 40], facing: s, "
        "door: none, doors: [{part: body, wall: '1', bay: 1}], parts: [{id: body, shape: outline, outline: [[0, 0], "
        "[512, 0], [512, 160], [0, 160]], walls: {'1': [[wall, 16], [door, 128], [wall, 16]]}}]}\n");
    REQUIRE(lowered.buildings.size() == 1);
    REQUIRE(lowered.buildings[0].doors.size() == 1);
    CHECK(lowered.buildings[0].doors[0].bay == 1);
    LoweredOutdoorMap unused;
    std::vector<ProjectIssue> found;
    CHECK_FALSE(lowerOutdoorProject(buildingProject("      - {building: building:home, at: [40, 40], facing: s, "
        "door: none, doors: [{part: body, wall: '1', bay: 3}], parts: [{id: body, shape: outline, outline: [[0, 0], "
        "[512, 0], [512, 160], [0, 160]], walls: {'1': [[wall, 16], [door, 128], [wall, 16]]}}]}\n"), unused, found));
    CHECK(anyIssue(found, "has 3 bays"));
    // Unlisted, the same face holds one.
    found.clear();
    CHECK_FALSE(lowerOutdoorProject(buildingProject("      - {building: building:home, at: [40, 40], facing: s, "
        "door: none, doors: [{part: body, wall: '1', bay: 1}], parts: [{id: body, shape: outline, outline: [[0, 0], "
        "[512, 0], [512, 160], [0, 160]]}]}\n"), unused, found));
    CHECK(anyIssue(found, "has 1 bays"));
}

TEST_CASE("forms: hip and gable roofs on a house with cut corners, a part that tapers, a plot's floor")
{
    // A house 512 square with its corners cut by 64: eight walls.
    const std::string cut = "[[64, 0], [448, 0], [512, 64], [512, 448], [448, 512], [64, 512], [0, 448], [0, 64]]";
    const auto raised = [&cut](const std::string &words)
    {
        LoweredOutdoorMap lowered = loweredBuildings("      - {building: building:home, at: [40, 40], facing: s, "
            "door: none, eaves: 0, fascia: 0, parts: [{shape: outline, outline: " + cut + ", " + words + "}]}\n");
        REQUIRE(lowered.buildings.size() == 1);
        return raiseOutdoorBuilding(lowered.buildings[0]);
    };
    const auto facesOf = [](const Game::OutdoorBModel &model, const std::string &texture, int type)
    {
        return std::count_if(model.faces.begin(), model.faces.end(), [&](const Game::OutdoorBModelFace &face)
        {
            return face.textureName == texture && (type == 0 || face.polygonType == type);
        });
    };
    const Game::OutdoorBModel hip = raised("roof: hip, roof_height: 128");
    // One slope over each of the eight walls, all at the same pitch, up 128 where the outline is deepest (256 from
    // the long walls): the roof's foot is the walls' top at 640 + 256.
    CHECK(facesOf(hip, "t14a05", 4) == 8);
    CHECK(hip.maxZ == 640 + 256 + 128);
    int32_t steepness = 0;

    for (const Game::OutdoorBModelFace &face : hip.faces)
    {
        if (face.textureName != "t14a05")
        {
            continue;
        }

        // Flat, and with the same lean as every other slope.
        const std::array<double, 3> normal = faceNormal(hip, face);
        const Game::OutdoorBModelVertex &first = hip.vertices[face.vertexIndices[0]];

        for (const uint16_t index : face.vertexIndices)
        {
            const Game::OutdoorBModelVertex &vertex = hip.vertices[index];
            CHECK(std::fabs((vertex.x - first.x) * normal[0] + (vertex.y - first.y) * normal[1]
                + (vertex.z - first.z) * normal[2]) < 1.5);
        }

        steepness = steepness == 0 ? face.planeNormalZ : steepness;
        CHECK(std::abs(face.planeNormalZ - steepness) < 400);
    }

    // A gable with its ridge east-west: two slopes, and the walls under them closed up to the slopes: the two
    // long end walls (east and west) to the ridge, the four cut corners a little way.
    const Game::OutdoorBModel gable = raised("roof: gable, roof_height: 128, ridge_along: ew, "
        "textures: {gable: t14a01b}");
    CHECK(facesOf(gable, "t14a05", 4) == 2);
    CHECK(facesOf(gable, "t14a01b", 1) == 6);
    CHECK(gable.maxZ == 640 + 256 + 128);
    // By a pitch: 45 degrees over half the width across the ridge (256) is a rise of 256.
    CHECK(raised("roof: gable, roof_pitch: 45, ridge_along: ns").maxZ == 640 + 256 + 256);

    // A spire: the walls lean in to half the foot's width over 512, under a cone.
    LoweredOutdoorMap spireLand = loweredBuildings("      - {building: building:home, at: [40, 40], facing: s, "
        "door: none, eaves: 0, fascia: 0, parts: [{size: [512, 512], taper: 0.5, wall_height: 512, roof: flat}]}\n");
    const Game::OutdoorBModel spire = raiseOutdoorBuilding(spireLand.buildings[0]);
    CHECK(spire.maxX - spire.minX == 512);
    CHECK(spire.maxZ == 640 + 512);
    bool topFound = false;

    for (const Game::OutdoorBModelFace &face : spire.faces)
    {
        if (face.polygonType != 3)
        {
            continue;
        }

        int least = 1 << 30;
        int most = -(1 << 30);

        for (const uint16_t index : face.vertexIndices)
        {
            least = std::min(least, spire.vertices[index].x);
            most = std::max(most, spire.vertices[index].x);
        }

        // The flat top is half as wide as the foot.
        CHECK(most - least == 256);
        topFound = true;
    }

    CHECK(topFound);
    // Its four walls lean: none is upright.
    CHECK(std::count_if(spire.faces.begin(), spire.faces.end(), [](const Game::OutdoorBModelFace &face)
    {
        return face.polygonType == 4 && face.planeNormalZ < 46340;
    }) == 4);

    // A plot's floor as the sketch says it: the ground under the plot is level there, not at the land's mean.
    const LoweredOutdoorMap terrace = loweredBuildings(
        "      - {building: building:home, at: [40, 40], facing: s, floor: 704}\n");
    CHECK(terrace.buildings[0].base == 704);
    CHECK(terrace.storedHeightAt(41, 41) == 704);
    // P4: on a platform a floor off the land's step stands where it is said, the land under it at the step under it
    // (X2's stalls at 1040 on a court topped at 1040: the land rounded up to 1056 rose through the court's paving).
    // On the land the floor keeps the nearest step, the land flush with it (D1's town at 1150 on land at 1152).
    const std::string court = "structures:\n  - {id: thing:court, kind: platform, at: [40.5, 40.5], size: [2048, 2048], "
        "height: 16}\n";

    for (const int floor : {720, 735, 736 + 16})
    {
        const LoweredOutdoorMap offStep = loweredBuildings(
            "      - {building: building:home, at: [40, 40], facing: s, floor: " + std::to_string(floor) + "}\n", court);
        CHECK(offStep.buildings[0].base == floor);
        const LoweredOutdoorMap onLand = loweredBuildings(
            "      - {building: building:home, at: [40, 40], facing: s, floor: " + std::to_string(floor) + "}\n");
        CHECK(onLand.buildings[0].base == std::round(floor / 32.0) * 32.0);
        CHECK(onLand.storedHeightAt(41, 41) == onLand.buildings[0].base);

        for (int y = 40; y <= 41; ++y)
        {
            for (int x = 40; x <= 41; ++x)
            {
                CHECK(offStep.storedHeightAt(x, y) <= floor);
                CHECK(offStep.storedHeightAt(x, y) > floor - 32);
            }
        }
    }

    CHECK(loweredBuildings("      - {building: building:home, at: [40, 40], facing: s}\n").buildings[0].base == 640);
    // Water under the plot: the plot stands at the water's level unless its floor is said lower (Vertigo's falls
    // building at the cliff's foot, whose plot the high stream reached, stood at the stream's level).
    const std::string pond = "water:\n  bodies:\n"
        "    - {id: water:pond, kind: lake, level: 832, polygon: [[38, 38], [41, 38], [41, 41], [38, 41]]}\n";
    CHECK(loweredBuildings("      - {building: building:home, at: [40, 40], facing: s}\n", pond).buildings[0].base
        == 832);
    const LoweredOutdoorMap underWater = loweredBuildings(
        "      - {building: building:home, at: [40, 40], facing: s, floor: 640}\n", pond);
    CHECK(underWater.buildings[0].base == 640);
    CHECK(std::any_of(underWater.warnings.begin(), underWater.warnings.end(), [](const std::string &warning)
    {
        return warning.find("under the water that reaches its plot (at 832)") != std::string::npos;
    }));

    const auto refused = [](const std::string &plot)
    {
        LoweredOutdoorMap unused;
        std::vector<ProjectIssue> found;
        CHECK_FALSE(lowerOutdoorProject(buildingProject(plot), unused, found));
        return found;
    };
    const std::string head = "      - building: building:home\n        at: [40, 40]\n        facing: s\n";
    CHECK(anyIssue(refused(head + "        floor: -5\n"), "floor is the height of the building's floor"));
    CHECK(anyIssue(refused(head + "        parts: [{size: [512, 512], taper: 9}]\n"), "taper is how wide the top"));
    CHECK(anyIssue(refused(head + "        parts: [{size: [512, 512], taper: 0.5}]\n"),
        "is on a part with `taper`"));
    CHECK(anyIssue(refused(head + "        door: none\n        parts: [{shape: outline, outline: " + cut
        + ", roof: hip, ridge: 32}]\n"), "is for a box"));
    // A hip with its ridge drawn in 64 on the same outline: the ridge runs north-south from 64 inside the north
    // wall to 64 inside the south wall, so the roof is at its height 384 long there.
    const Game::OutdoorBModel drawnIn = raised("roof: hip, roof_height: 128, hip: 64, ridge_along: ns");
    int ridgeLeast = 1 << 30;
    int ridgeMost = -(1 << 30);

    for (const Game::OutdoorBModelVertex &vertex : drawnIn.vertices)
    {
        if (vertex.z == 640 + 256 + 128)
        {
            ridgeLeast = std::min(ridgeLeast, vertex.y);
            ridgeMost = std::max(ridgeMost, vertex.y);
        }
    }

    CHECK(ridgeMost - ridgeLeast == 512 - 2 * 64);
}

TEST_CASE("forms: a ramp is one sloping slab; a doorway reaches back into the slope and has a hood")
{
    std::vector<ProjectIssue> issues;
    IdsLock ids;
    const OutdoorThings things = thingsOf("structures:\n"
        "  - {id: thing:ramp, kind: stairs, line: [[50, 50], [52, 50]], rise: 256, width: 256, ramp: true}\n"
        "  - {id: thing:den, kind: doorway, at: [60, 60], width: 256, height: 256, depth: 256, hood: 512, "
        "into: {map: d08.blv}}\n", issues, ids);
    REQUIRE(issues.empty());
    REQUIRE(things.models.size() == 2);
    const Game::OutdoorBModel &ramp = things.models[0];
    // Its top is one face that climbs 256 over 1024, walkable; two cheeks and two ends beside it.
    CHECK(ramp.faces.size() == 5);
    CHECK(ramp.maxZ == 640 + 256);
    CHECK(std::count_if(ramp.faces.begin(), ramp.faces.end(), [](const Game::OutdoorBModelFace &face)
    {
        return face.polygonType == 4 && face.planeNormalZ > 46340;
    }) == 1);
    // D-160 (X4 p11): every face looks out of the slab (the collision is one-sided; cheeks wound inward let the
    // party walk in through them), each side straight out from the middle.
    const double middleX = (ramp.minX + ramp.maxX) * 0.5;
    const double middleY = (ramp.minY + ramp.maxY) * 0.5;
    const double middleZ = (ramp.minZ + ramp.maxZ) * 0.5;
    size_t sides = 0;

    for (const Game::OutdoorBModelFace &face : ramp.faces)
    {
        double x = 0.0;
        double y = 0.0;
        double z = 0.0;

        for (const uint16_t index : face.vertexIndices)
        {
            x += ramp.vertices[index].x;
            y += ramp.vertices[index].y;
            z += ramp.vertices[index].z;
        }

        const double count = static_cast<double>(face.vertexIndices.size());
        CHECK(face.planeNormalX * (x / count - middleX) + face.planeNormalY * (y / count - middleY)
            + face.planeNormalZ * (z / count - middleZ) > 0.0);
        sides += std::abs(face.planeNormalZ) < 64 ? 1 : 0;
    }

    CHECK(sides == 4);
    // The doorway: its frame 256 deep behind the front, its hood 512 before it; the door stays one face.
    const Game::OutdoorBModel &den = things.models[1];
    CHECK(den.maxY - den.minY == 256 + 512);
    CHECK(den.maxX - den.minX == 384);
    CHECK(den.maxZ == 640 + 288);
    // The hood's roof and cheeks have no backs on the frame's front (P3 2026-11-24, X1's Witch Tower door: they lay
    // back to back with it).
    CHECK(findOutdoorBackToBackFaces({den}).empty());
    CHECK(findOutdoorCoplanarFaces({den}).empty());

    // A castle gate of two leaves (X4's, DOORS.md): the door picture once on each half, the right one mirrored; one
    // face more than the gate of one leaf, arched or square.
    for (const char *pArch : {"", ", arch: round"})
    {
        std::vector<ProjectIssue> gateIssues;
        IdsLock gateIds;
        const OutdoorThings gates = thingsOf(std::string("structures:\n"
            "  - {id: thing:one, kind: doorway, at: [60, 60], width: 384, height: 448") + pArch + "}\n"
            "  - {id: thing:two, kind: doorway, at: [70, 60], width: 384, height: 448, leaves: 2" + pArch + "}\n",
            gateIssues, gateIds);
        REQUIRE(gateIssues.empty());
        REQUIRE(gates.models.size() == 2);
        CHECK(gates.models[1].faces.size() == gates.models[0].faces.size() + 1);
        // The two leaves: u from 0 to 128 each, the right one running back.
        size_t spans = 0;

        for (const Game::OutdoorBModelFace &face : gates.models[1].faces)
        {
            const auto [least, most] = std::minmax_element(face.textureUs.begin(), face.textureUs.end());

            if (face.textureName == gates.models[1].faces.back().textureName && *least == 0 && *most == 128)
            {
                ++spans;
            }
        }

        CHECK(spans >= 2);
    }

    const auto refused = [](const std::string &structure)
    {
        std::vector<ProjectIssue> found;
        IdsLock lock;
        thingsOf("structures:\n" + structure, found, lock);
        return found;
    };
    CHECK(anyIssue(refused("  - {id: thing:r, kind: stairs, line: [[50, 50], [50.25, 50]], rise: 512, "
        "ramp: true}\n"), "steeper than 45 degrees"));
    CHECK(anyIssue(refused("  - {id: thing:d, kind: doorway, at: [60, 60], depth: 4}\n"), "16 to 2048 deep"));
}

TEST_CASE("a standalone doorway fits a painting to each leaf in its logical texels")
{
    std::vector<ProjectIssue> issues;
    IdsLock ids;
    const OutdoorDoorPictures pictures = parseOutdoorDoorPictures(
        {"textures:\n  panel: {class: feature, door: single, size: [256, 64]}\n"});
    const OutdoorThings doors = thingsOf("structures:\n"
        "  - {id: thing:plain, kind: doorway, at: [50, 50], width: 192, height: 288, textures: {door: grate}}\n"
        "  - {id: thing:furnace, kind: doorway, at: [60, 60], width: 192, height: 288, "
        "textures: {door: {texture: grate, fit: true, size: [128, 128]}}}\n"
        "  - {id: thing:pair, kind: doorway, at: [70, 70], width: 384, height: 288, leaves: 2, "
        "textures: {door: {texture: panel, fit: true, size: [192, 96]}}}\n"
        "  - {id: thing:classed, kind: doorway, at: [80, 80], width: 192, height: 288, textures: {door: panel}}\n",
        issues, ids, nullptr, &pictures);
    REQUIRE(issues.empty());
    REQUIRE(doors.models.size() == 4);
    const Game::OutdoorBModelFace &plain = doors.models[0].faces.back();
    const Game::OutdoorBModelFace &furnace = doors.models[1].faces.back();
    CHECK(plain.textureUs == std::vector<int16_t>{0, 128, 128, 0});
    CHECK(plain.textureVs == std::vector<int16_t>{256, 256, 0, 0});
    CHECK(furnace.textureUs == plain.textureUs);
    CHECK(furnace.textureVs == std::vector<int16_t>{128, 128, 0, 0});

    const auto &paired = doors.models[2].faces;
    const auto &left = paired.at(paired.size() - 2);
    const auto &right = paired.back();
    CHECK(left.textureUs == std::vector<int16_t>{0, 192, 192, 0});
    CHECK(right.textureUs == std::vector<int16_t>{192, 0, 0, 192});
    CHECK(left.textureVs == std::vector<int16_t>{96, 96, 0, 0});
    CHECK(right.textureVs == left.textureVs);
    const auto &classed = doors.models[3].faces.back();
    CHECK(classed.textureUs == std::vector<int16_t>{0, 256, 256, 0});
    CHECK(classed.textureVs == plain.textureVs);

    for (const char *invalid : {"fit: true", "fit: false, size: [128, 128]", "fit: true, size: [128, 0]"})
    {
        issues.clear();
        thingsOf(std::string("structures:\n  - {id: thing:bad, kind: doorway, at: [60, 60], "
            "textures: {door: {texture: grate, ") + invalid + "}}}\n", issues, ids);
        CHECK(anyIssue(issues, "a fitted door picture"));
    }
}

TEST_CASE("named wall tiles stay in phase across a doorway hood and its jambs")
{
    std::vector<ProjectIssue> issues;
    IdsLock ids;
    const OutdoorThings doors = thingsOf("wall_tiles: {iron: [256, 64]}\nstructures:\n"
        "  - {id: thing:furnace, kind: doorway, at: [27, 25], width: 192, height: 288, depth: 384, hood: 96, "
        "textures: {wall: iron, door: {texture: grate, fit: true, size: [128, 128]}}}\n", issues, ids);
    REQUIRE(issues.empty());
    REQUIRE(doors.models.size() == 1);
    const auto &model = doors.models.front();
    size_t walls = 0;
    for (const auto &face : model.faces)
    {
        if (face.textureName == "iron" && face.polygonType == 1)
        {
            ++walls;
            for (size_t i = 0; i < face.vertexIndices.size(); ++i)
            {
                const auto &point = model.vertices[face.vertexIndices[i]];
                const int u = point.y * (face.planeNormalX / 65536) - point.x * (face.planeNormalY / 65536);
                CHECK((face.textureUs[i] - u) % 256 == 0);
                CHECK((face.textureVs[i] + point.z) % 64 == 0);
            }
        }
    }
    CHECK(walls >= 8);
    CHECK(model.faces.back().textureUs == std::vector<int16_t>{0, 128, 128, 0});
    CHECK(model.faces.back().textureVs == std::vector<int16_t>{128, 128, 0, 0});

    for (const std::string bad : {"[]", "{iron: [256, 0]}", "{iron: [256.25, 64]}"})
    {
        issues.clear();
        LoweredOutdoorMap lowered;
        const Project project = buildingProject("", "wall_tiles: " + bad + "\n");
        CHECK_FALSE(lowerOutdoorProject(project, lowered, issues));
        CHECK(anyIssue(issues, "wall"));
    }
}

namespace
{
// A project built into a folder of its own: the script and the scene it wrote.
struct BuiltOutdoor
{
    bool built = false;
    std::vector<ProjectIssue> issues;
    std::vector<std::string> warnings;
    std::string lua;
    YAML::Node scene;
};

BuiltOutdoor builtOutdoor(Project project, const char *pFolder, const std::filesystem::path &assetRoot = {})
{
    BuiltOutdoor built;
    project.root = std::filesystem::temp_directory_path() / pFolder;
    BuildOptions options;
    options.outputDirectory = project.root / "build";
    // The names an asset root's tables answer for are looked up; nothing is read back through it.
    options.assetRoot = assetRoot;
    options.dryRun = false;
    BuildResult result;
    built.built = buildOutdoorProject(project, options, result);
    built.issues = result.issues;
    built.warnings = result.warnings;

    for (const ProjectIssue &issue : result.issues)
    {
        MESSAGE(issue.path << ": " << issue.message);
    }

    std::ifstream luaStream(project.root / "build" / "groundtest.lua");
    built.lua = std::string((std::istreambuf_iterator<char>(luaStream)), std::istreambuf_iterator<char>());
    std::ifstream sceneStream(project.root / "build" / "groundtest.scene.yml");
    const std::string scene((std::istreambuf_iterator<char>(sceneStream)), std::istreambuf_iterator<char>());
    built.scene = built.built ? YAML::Load(scene) : YAML::Node();
    std::error_code error;
    std::filesystem::remove_all(project.root, error);
    return built;
}

// The number of the event with a title, from the script's registration; 0 when there is none.
int eventNumberOf(const std::string &lua, const std::string &title)
{
    const size_t found = lua.find(", \"" + title + "\", ");
    const size_t begin = found == std::string::npos ? found : lua.rfind("RegisterEvent(", found);
    return begin == std::string::npos ? 0 : std::atoi(lua.c_str() + begin + 14);
}

// How many faces the scene gives an event, and how many of them have a bit of their attributes.
size_t facesOfEvent(const YAML::Node &scene, int event, uint32_t bit = 0)
{
    size_t count = 0;

    for (const YAML::Node &face : scene["bmodel_faces"]["interactive_faces"])
    {
        if (face["cog_triggered_number"].as<int>() == event
            && (bit == 0 || (face["legacy_attributes"].as<uint32_t>() & bit) != 0))
        {
            ++count;
        }
    }

    return count;
}

void addCardTables(Project &project)
{
    ProjectFile &card = project.files["project.yml"];
    card.text += "qbits: {council_hall_open: 59}\nitems: {thorns_key: 661}\n";
    card.document = YAML::Load(card.text);
}
}

TEST_CASE("item spawn points lie in an items area by its level; a chest holds things of several levels")
{
    const BuiltOutdoor built = builtOutdoor(buildingProject(
        "      - {building: building:home, at: [40, 40], facing: s}\n",
        "areas:\n  - {id: pop:wolves, kind: items, level: 3, count: 4, circle: {at: [100, 100], r: 2}}\n"
        "structures:\n  - {id: thing:tree_chest, kind: chest, at: [50, 50], chest: {level: 3, random_items: 0, "
        "random_levels: [7, 3, 3, 3], items: [501]}}\n"), "oymap_outdoor_items");
    REQUIRE(built.built);
    // Four markers of type 2 with the treasure level as their number, at least a quarter cell apart.
    REQUIRE(built.scene["spawns"].size() == 4);

    for (const YAML::Node &spawn : built.scene["spawns"])
    {
        CHECK(spawn["type_id"].as<int>() == 2);
        CHECK(spawn["index"].as<int>() == 3);
    }

    // The chest's records: the certain item, then one thing of level 7 and three of level 3 (a number below zero
    // is a treasure level).
    const std::string records = built.scene["initial_state"]["chests"][0]["raw_items_hex"].as<std::string>();
    CHECK(records.substr(0, 8) == "F5010000");
    CHECK(records.substr(72, 8) == "F9FFFFFF");
    CHECK(records.substr(144, 8) == "FDFFFFFF");
    CHECK(records.substr(288, 8) == "FDFFFFFF");
    CHECK(records.substr(360, 8) == "00000000");
    const auto refused = [](const std::string &more)
    {
        const BuiltOutdoor result = builtOutdoor(buildingProject(
            "      - {building: building:home, at: [40, 40], facing: s}\n", more), "oymap_outdoor_items_bad");
        CHECK_FALSE(result.built);
        return result.issues;
    };
    CHECK(anyIssue(refused("areas:\n  - {id: pop:wolves, kind: items, circle: {at: [100, 100], r: 2}}\n"),
        "an items area has a `level`"));
    CHECK(anyIssue(refused("areas:\n  - {id: pop:wolves, slot: 1, level: 2, circle: {at: [100, 100], r: 2}}\n"),
        "is the treasure level of an items area"));
    CHECK(anyIssue(refused("structures:\n  - {id: thing:c, kind: chest, at: [50, 50], chest: {random_levels: "
        "[9]}}\n"), "random_levels is a list of treasure levels"));
}

TEST_CASE("a model of a shipped map is taken by name to where the sketch says, with the structure's event")
{
    // An asset root with one outdoor map of the world, holding two models named ship and one named cart.
    const std::filesystem::path root = std::filesystem::temp_directory_path() / "oymap_outdoor_import_root";
    std::error_code error;
    std::filesystem::create_directories(root / "worlds" / "mm8" / "maps", error);
    Game::OutdoorMapData source = testMap();
    source.decorationMap.assign(Side * Side, 0);
    source.bmodels = {testHouse(1000, 2000, 512, 256, 100, 300, 44), testHouse(1512, 2000, 512, 256, 100, 200, 45),
        testHouse(-5000, -5000, 128, 128, 0, 64, 0)};
    source.bmodels[0].name = "Ship";
    source.bmodels[1].name = "ship";
    source.bmodels[2].name = "cart";

    for (Game::OutdoorBModel &model : source.bmodels)
    {
        for (Game::OutdoorBModelFace &face : model.faces)
        {
            face.textureName = "t06b01";
            face.textureUs.assign(face.vertexIndices.size(), 0);
            face.textureVs.assign(face.vertexIndices.size(), 0);
            face.planeNormalZ = 65536;
        }
    }

    const std::optional<std::vector<uint8_t>> bytes = Game::OutdoorMapDataWriter().buildBytes(source);
    REQUIRE(bytes);
    std::string writeError;
    REQUIRE(writeBinaryFileAtomically(root / "worlds" / "mm8" / "maps" / "src.odm", *bytes, writeError));
    const auto raised = [&root](const std::string &structures, std::vector<ProjectIssue> &issues,
        std::vector<std::string> *pWarnings = nullptr)
    {
        const Project project = buildingProject("      - {building: building:home, at: [40, 40], facing: s}\n",
            "structures:\n" + structures);
        LoweredOutdoorMap lowered;
        std::vector<ProjectIssue> lowering;
        REQUIRE(lowerOutdoorProject(project, lowered, lowering));
        IdsLock ids;
        OutdoorEventWords words(project, root, ids, issues);
        OutdoorThings things;
        std::vector<std::string> warnings;
        raiseOutdoorThings(project, lowered, pWarnings != nullptr ? std::filesystem::path() : root, ids, words,
            things, issues, pWarnings != nullptr ? *pWarnings : warnings);
        return things;
    };
    std::vector<ProjectIssue> issues;
    const OutdoorThings things = raised(
        "  - {id: thing:ship, kind: model, from: {map: SRC.odm, models: [ship]}, at: [80, 30], raise: 16, "
        "title: The Dauntless, house: 480}\n"
        "  - {id: thing:cart, kind: model, from: {map: src.odm, models: [2]}}\n", issues);
    REQUIRE(issues.empty());
    REQUIRE(things.models.size() == 2);
    // Both models named ship as one thing, 1024 by 256, its middle at the cell [80, 30], 16 higher than it was.
    const Game::OutdoorBModel &ship = things.models[0];
    CHECK(ship.faces.size() == 12);
    CHECK(ship.maxX - ship.minX == 1024);
    CHECK((ship.maxX + ship.minX) / 2 == (80 - 64) * 512);
    CHECK((ship.maxY + ship.minY) / 2 == (64 - 30) * 512);
    CHECK(ship.minZ == 116);
    CHECK(ship.maxZ == 416);
    // Its faces run the structure's event, not the events they had; their planes went with them.
    const OutdoorEventPlan *pShip = eventOf(things, "evt:thing:ship");
    REQUIRE(pShip != nullptr);
    CHECK(pShip->body == std::vector<std::string>{"evt.EnterHouse(480)"});

    for (const Game::OutdoorBModelFace &face : ship.faces)
    {
        CHECK(face.cogTriggeredNumber == pShip->number);
        CHECK(face.textureName == "t06b01");
        CHECK(face.planeDistance == -65536 * ship.vertices[face.vertexIndices[0]].z);
    }

    // Without `at` a model stands where it stood, and without words it says and does nothing.
    const Game::OutdoorBModel &cart = things.models[1];
    CHECK(cart.minX == -5000);
    CHECK(cart.minY == -5000);
    CHECK(cart.faces[0].cogTriggeredNumber == 0);
    // Refused, with what to change; left out and said without an asset root.
    std::vector<ProjectIssue> found;
    raised("  - {id: thing:a, kind: model, from: {map: nowhere.odm, models: [ship]}}\n", found);
    CHECK(anyIssue(found, "there is no outdoor map nowhere.odm"));
    found.clear();
    raised("  - {id: thing:a, kind: model, from: {map: src.odm, models: [galleon]}}\n", found);
    CHECK(anyIssue(found, "src.odm has no model `galleon`: it has 3 models"));
    found.clear();
    raised("  - {id: thing:a, kind: model}\n", found);
    CHECK(anyIssue(found, "a model is taken `from:"));
    found.clear();

    // `from.world`: a map of another world (a Xeen map taking Erathia's ship); without it, only the project's world.
    std::filesystem::create_directories(root / "worlds" / "mm7" / "maps", error);
    REQUIRE(writeBinaryFileAtomically(root / "worlds" / "mm7" / "maps" / "erathia.odm", *bytes, writeError));
    CHECK(raised("  - {id: thing:a, kind: model, from: {world: mm7, map: erathia.odm, models: [ship]}}\n", found)
        .models.size() == 1);
    CHECK(found.empty());
    raised("  - {id: thing:a, kind: model, from: {map: erathia.odm, models: [ship]}}\n", found);
    CHECK(anyIssue(found, "there is no outdoor map erathia.odm in worlds/mm8/maps"));
    found.clear();
    raised("  - {id: thing:a, kind: model, from: {world: mm6, map: erathia.odm, models: [ship]}}\n", found);
    CHECK(anyIssue(found, "there is no outdoor map erathia.odm in worlds/mm6/maps"));
    found.clear();
    std::vector<std::string> said;
    CHECK(raised("  - {id: thing:a, kind: model, from: {map: src.odm, models: [ship]}}\n", found, &said)
        .models.empty());
    CHECK(found.empty());
    CHECK(std::any_of(said.begin(), said.end(), [](const std::string &warning)
    {
        return warning.find("needs an asset root") != std::string::npos;
    }));
    std::filesystem::remove_all(root, error);
}

TEST_CASE("P3: a humped bridge's ends meet land that falls across them within 32 on every side")
{
    // The land rises about 48 a cell to the south over the rows 52 to 68 (a grid 8 cells apart: 256, 640, 1024),
    // across a bridge running east 1024 wide: D4's Snow River bridge (+33 and +43 at a kerb when its ends stood 16
    // over the land's middle).
    std::string grid = "heights:\n  grid:\n    step: 8\n    unit: 64\n    rows:\n";

    for (int y = 0; y < 16; ++y)
    {
        grid += "      - [";

        for (int x = 0; x < 16; ++x)
        {
            grid += (x == 0 ? "" : ", ") + std::to_string(y == 6 ? 4 : y == 8 ? 16 : 10);
        }

        grid += "]\n";
    }

    Project project = buildingProject("      - {building: building:home, at: [40, 40], facing: s}\n",
        "structures:\n  - {id: thing:bridge, kind: bridge, line: [[20, 60], [28, 60]], width: 1024, rise: 32}\n");
    ProjectFile &sketch = project.files["sketch.yml"];
    REQUIRE(sketch.text.find(LevelLand) != std::string::npos);
    sketch.text.replace(sketch.text.find(LevelLand), std::string(LevelLand).size(), grid);
    sketch.document = YAML::Load(sketch.text);
    LoweredOutdoorMap lowered;
    std::vector<ProjectIssue> issues;
    REQUIRE(lowerOutdoorProject(project, lowered, issues));
    IdsLock ids;
    OutdoorEventWords words(project, {}, ids, issues);
    OutdoorThings things;
    std::vector<std::string> warnings;
    raiseOutdoorThings(project, lowered, {}, ids, words, things, issues, warnings);
    REQUIRE(issues.empty());
    REQUIRE(things.models.size() == 1);
    const Game::OutdoorBModel *pBridge = &things.models[0];

    for (const double end : {20.0, 28.0})
    {
        // The deck's top at the end (its highest corner there), and the land 24 beyond it at its middle and a
        // quarter of its width each side, as tools/xeen/town_fit_check.py `bridges.step` reads them.
        const int endX = static_cast<int>(std::lround((end - 64.0) * 512.0));
        int deck = -(1 << 30);

        for (const Game::OutdoorBModelVertex &vertex : pBridge->vertices)
        {
            deck = vertex.x == endX ? std::max(deck, vertex.z) : deck;
        }

        const double beyond = end + (end < 24.0 ? -24.0 : 24.0) / 512.0;
        double lowest = 1.0e9;
        double highest = -1.0e9;

        for (const double across : {-0.5, 0.0, 0.5})
        {
            const double land = lowered.groundHeightAt(beyond, 60.0 + across);
            CAPTURE(end);
            CAPTURE(across);
            CHECK(std::fabs(deck - land) <= 32.0);
            lowest = std::min(lowest, land);
            highest = std::max(highest, land);
        }

        // Steep enough that 16 over the middle would leave more than 32 on the low side.
        CHECK(highest - lowest > 40.0);
    }
}

TEST_CASE("P3: drop_overlaps drops of a taken model's faces lying on each other the smaller of each two")
{
    // A sail laid both ways (front and back on the same corners) with a patch on its front: as MM7's Lady Catherine
    // (Nystor's ship on Xeen's X2), whose hull boards and trim lie back to back and two trims on each other.
    const std::filesystem::path root = std::filesystem::temp_directory_path() / "oymap_outdoor_drop_overlaps_root";
    std::error_code error;
    std::filesystem::create_directories(root / "worlds" / "mm8" / "maps", error);
    Game::OutdoorMapData source = testMap();
    source.decorationMap.assign(Side * Side, 0);
    Game::OutdoorBModel sail;
    sail.name = "sail";
    sail.vertices = {{0, 0, 600}, {256, 0, 600}, {256, 0, 856}, {0, 0, 856}, {64, 0, 664}, {192, 0, 664},
        {192, 0, 792}, {64, 0, 792}};

    for (const std::array<uint16_t, 4> &corners : {std::array<uint16_t, 4>{0, 1, 2, 3},
        std::array<uint16_t, 4>{3, 2, 1, 0}, std::array<uint16_t, 4>{4, 5, 6, 7}})
    {
        Game::OutdoorBModelFace face;
        face.vertexIndices.assign(corners.begin(), corners.end());
        face.textureName = "t06b01";
        face.textureUs.assign(4, 0);
        face.textureVs.assign(4, 0);
        sail.faces.push_back(face);
    }

    source.bmodels = {sail};
    const std::optional<std::vector<uint8_t>> bytes = Game::OutdoorMapDataWriter().buildBytes(source);
    REQUIRE(bytes);
    std::string writeError;
    REQUIRE(writeBinaryFileAtomically(root / "worlds" / "mm8" / "maps" / "src.odm", *bytes, writeError));
    const auto raised = [&root](const std::string &structures, std::vector<ProjectIssue> &issues)
    {
        const Project project = buildingProject("      - {building: building:home, at: [40, 40], facing: s}\n",
            "structures:\n" + structures);
        LoweredOutdoorMap lowered;
        std::vector<ProjectIssue> lowering;
        REQUIRE(lowerOutdoorProject(project, lowered, lowering));
        IdsLock ids;
        OutdoorEventWords words(project, root, ids, issues);
        OutdoorThings things;
        std::vector<std::string> warnings;
        raiseOutdoorThings(project, lowered, root, ids, words, things, issues, warnings);
        return things;
    };
    std::vector<ProjectIssue> issues;
    const OutdoorThings whole = raised("  - {id: thing:s, kind: model, from: {map: src.odm, models: [sail]}}\n",
        issues);
    REQUIRE(issues.empty());
    REQUIRE(whole.models.size() == 1);
    CHECK(whole.models[0].faces.size() == 3);
    CHECK(findOutdoorBackToBackFaces({whole.models[0]}).size() == 2);
    CHECK(findOutdoorCoplanarFaces({whole.models[0]}).size() == 1);
    const OutdoorThings dropped = raised("  - {id: thing:s, kind: model, from: {map: src.odm, models: [sail]}, "
        "drop_overlaps: true}\n", issues);
    REQUIRE(issues.empty());
    REQUIRE(dropped.models.size() == 1);
    // The patch (smaller than the front) and the back (as large as the front, and the later) are dropped.
    REQUIRE(dropped.models[0].faces.size() == 1);
    CHECK(dropped.models[0].faces[0].vertexIndices.size() == 4);
    CHECK(findOutdoorBackToBackFaces({dropped.models[0]}).empty());
    CHECK(findOutdoorCoplanarFaces({dropped.models[0]}).empty());
    raised("  - {id: thing:s, kind: model, from: {map: src.odm, models: [sail]}, drop_overlaps: some}\n", issues);
    CHECK(anyIssue(issues, "`drop_overlaps: true` drops"));
    std::filesystem::remove_all(root, error);
}

TEST_CASE("a door behind a condition; a chest that opens with its key; a part with a name and a click of its own")
{
    Project project = buildingProject(
        "      - building: building:home\n        at: [40, 40]\n        facing: s\n        house: 904\n"
        "        title: Home\n        condition: {not: {qbit: 695}}\n        locked_text: This Door is Locked\n"
        "        else_effects: [{lua: \"evt.FaceAnimation(FaceAnimation.DoorLocked)\"}]\n"
        "        parts:\n          - {id: shop, size: [512, 768], title: The Shop}\n"
        "          - {id: basin, at: [512, 0], size: [512, 768], title: Drink from the Fountain, "
        "effects: [{text: Refreshing}]}\n"
        "        doors:\n          - {part: basin, wall: s, into: {map: d09.blv, at: [320, -1290, 513], "
        "facing: 512}, title: Enter the Hall, condition: {qbit: council_hall_open}, "
        "else_effects: [{lua: \"evt.SpeakNPC(3)\"}]}\n",
        "structures:\n"
        "  - {id: thing:vault, kind: platform, at: [50, 50], size: [256, 256], height: 32, title: The Vault of "
        "Time, hint: Vault, chest: {level: 5, random_items: 3}, condition: {any: [{item: thorns_key}, "
        "{map_var: vault_open}]}, effects: [{take_item: thorns_key}, {set: {var: {map_var: vault_open}, "
        "value: 1}}]}\n");
    addCardTables(project);
    const BuiltOutdoor built = builtOutdoor(project, "oymap_outdoor_click");
    REQUIRE(built.built);
    const std::string &lua = built.lua;
    // The plot's own door: shut while the bit is set, with what happens then; else the house.
    CHECK(lua.find("    if not (not (IsQBitSet(QBit(695)))) then\n"
        "        evt.FaceAnimation(FaceAnimation.DoorLocked)\n"
        "        evt.StatusText(\"This Door is Locked\")\n        return\n    end\n    evt.EnterHouse(904)\n")
        != std::string::npos);
    // The second door: a bit by its name in project.yml, an NPC speaks while it is not set.
    CHECK(lua.find("    if not (IsQBitSet(QBit(59))) then\n        evt.SpeakNPC(3)\n        return\n    end\n"
        "    evt.MoveToMap(320, -1290, 513, 512, 0, 0, 0, 1, \"d09.blv\")\n") != std::string::npos);
    // The vault: the chest only with the key or once opened; then the key is taken and the opening remembered.
    CHECK(lua.find("    if not (((HasItem(661)) or (IsAtLeast(MapVar(0), 1)))) then\n        return\n    end\n"
        "    evt.OpenChest(0)\n    RemoveItem(661)\n    SetValue(MapVar(0), 1)\n") != std::string::npos);
    // The door of a part with a name says that name; a door with a title of its own keeps it.
    const int shop = eventNumberOf(lua, "The Shop");
    const int basin = eventNumberOf(lua, "Drink from the Fountain");
    const int hall = eventNumberOf(lua, "Enter the Hall");
    const int vault = eventNumberOf(lua, "The Vault of Time");
    const int hint = eventNumberOf(lua, "Vault");
    REQUIRE(shop != 0);
    REQUIRE(basin != 0);
    REQUIRE(hall != 0);
    REQUIRE(vault != 0);
    REQUIRE(hint != 0);
    CHECK(lua.find("RegisterEvent(" + std::to_string(basin) + ", \"Drink from the Fountain\", function()\n"
        "    evt.StatusText(\"Refreshing\")\nend") != std::string::npos);
    // Two events say The Shop: the house door in that part (one face, the first) and the part's walls and roof;
    // the basin's faces run its click, but for the one door in it.
    const size_t secondShop = lua.find(", \"The Shop\", ", lua.find(", \"The Shop\", ") + 1);
    REQUIRE(secondShop != std::string::npos);
    const int shopWalls = std::atoi(lua.c_str() + lua.rfind("RegisterEvent(", secondShop) + 14);
    CHECK(lua.find("RegisterEvent(" + std::to_string(shop) + ", \"The Shop\", function()") != std::string::npos);
    CHECK(lua.find("RegisterEvent(" + std::to_string(shopWalls) + ", \"The Shop\", nil") != std::string::npos);
    CHECK(facesOfEvent(built.scene, shop) == 1);
    CHECK(facesOfEvent(built.scene, shopWalls) > 8);
    CHECK(facesOfEvent(built.scene, hall) == 1);
    CHECK(facesOfEvent(built.scene, basin) > 8);
    // The vault's top runs the click, its four sides only say the hint.
    CHECK(facesOfEvent(built.scene, vault) == 1);
    CHECK(facesOfEvent(built.scene, hint) == 4);

    // What cannot be built is refused, with what to change.
    const auto refused = [](const std::string &plot, const std::string &more)
    {
        Project bad = buildingProject(plot, more);
        const BuiltOutdoor result = builtOutdoor(bad, "oymap_outdoor_click_bad");
        CHECK_FALSE(result.built);
        return result.issues;
    };
    const std::string house = "      - {building: building:home, at: [40, 40], facing: s, house: 904}\n";
    CHECK(anyIssue(refused("      - {building: building:home, at: [40, 40], facing: s, "
        "condition: {qbit: 5}}\n", ""), "this door opens nothing"));
    CHECK(anyIssue(refused("      - {building: building:home, at: [40, 40], facing: s, house: 904, "
        "condition: {qbit: council_hall_open}}\n", ""), "is not declared in project.yml `qbits`"));
    CHECK(anyIssue(refused("      - {building: building:home, at: [40, 40], facing: s, house: 904, "
        "locked_text: Shut}\n", ""), "give the condition"));
    CHECK(anyIssue(refused(house, "structures:\n  - {id: thing:c, kind: chest, at: [50, 50], hint: Box}\n"),
        "is used as a whole"));
    CHECK(anyIssue(refused(house, "structures:\n  - {id: thing:w, kind: well, at: [50, 50], "
        "condition: {password: fish}, effects: [{gold: 5}]}\n"), "the build has no test for a `password`"));
    CHECK(anyIssue(refused(house, "structures:\n  - {id: thing:w, kind: well, at: [50, 50], "
        "condition: {item: 5, consume: true, qbit: 3}, locked_text: Dry}\n"), "this structure does nothing"));
}

TEST_CASE("events nobody clicks: on entering, by the clock, a floor stepped on; things events show and repaint")
{
    const std::filesystem::path root = std::filesystem::temp_directory_path() / "oymap_outdoor_event_root";
    std::error_code error;
    std::filesystem::create_directories(root / "engine" / "data_tables", error);
    {
        std::ofstream decorations(root / "engine" / "data_tables" / "decoration_data.txt");
        decorations << "#\tName\n13\tparty start\n101\ttree12\n";
        const auto world = root / "worlds" / "mm8";
        std::filesystem::create_directories(world);
        std::ofstream(world / "world.yml") << "tableContributions: [{table: decorations, mode: append, path: trees.txt}]\n";
        std::ofstream(world / "trees.txt") << "102\ttree37\n";
        // The tile table of the test land is not there: the build reads it with an asset root.
    }
    const std::string house = "      - {building: building:home, at: [40, 40], facing: s, house: 904, hidden: true}\n";
    const std::string more =
        "structures:\n"
        "  - {id: thing:trap, kind: platform, at: [50, 50], size: [512, 512], height: 16, trigger: step, "
        "once: true, condition: {not: {qbit: 760}}, effects: [{qbit: 760}, {cast: {spell: 2, from: [6545, 10984, "
        "4000], to: [6545, 5678, 111], mastery: grandmaster, level: 10}}, {summon: {slot: 1, at: [5232, 1424, 0], "
        "count: 10, group: 51}}, {show: [building:home, thing:tower]}]}\n"
        "  - {id: thing:tower, kind: obelisk, at: [55, 55], hidden: true}\n"
        "  - {id: thing:wall, kind: wall, line: [[70, 70], [80, 70]]}\n"
        "  - {id: thing:post, kind: sign, at: [56, 56], title: Signpost, arms: [{title: West to Erathia, "
        "toward: w}, {title: East, toward: e}]}\n"
        "events:\n"
        "  - {id: evt:enter, trigger: load, effects: [{set_texture: {of: thing:wall, from: T06B01, to: t06b02}}, "
        "{hide: thing:wall}]}\n"
        "  - {id: evt:fort_fire, trigger: timer, every: 5, condition: {not: {qbit: 760}}, "
        "lua: \"evt.CastSpell(6, 10, 3, 7368, 4920, 416, 4903, 7358, 1)\"}\n";
    const BuiltOutdoor built = builtOutdoor(buildingProject(house, more), "oymap_outdoor_events");
    REQUIRE(built.built);
    const std::string &lua = built.lua;
    // The numbers: the house door 1, then the structures and events in the sketch's order.
    CHECK(lua.find("SetMapMetadata({onLoad = {") != std::string::npos);
    CHECK(lua.find("scheduleKind = \"interval\", intervalHalfMinutes = 5 },\n}})") != std::string::npos);
    const size_t loadList = lua.find("onLoad = {") + 10;
    const int enter = std::atoi(lua.c_str() + loadList);
    REQUIRE(enter != 0);
    const size_t timerId = lua.find("{ eventId = ") + 12;
    const int fire = std::atoi(lua.c_str() + timerId);
    CHECK(lua.find("RegisterEvent(" + std::to_string(fire) + ", nil, function()\n"
        "    if not (not (IsQBitSet(QBit(760)))) then\n        return\n    end\n"
        "    evt.CastSpell(6, 10, 3, 7368, 4920, 416, 4903, 7358, 1)\nend)") != std::string::npos);
    // The trap: once, behind its condition; the spell, the monsters, and the two hidden things shown by their
    // faces' numbers.
    CHECK(lua.find("    evt.CastSpell(2, 10, 4, 6545, 10984, 4000, 6545, 5678, 111)\n"
        "    evt.SummonMonsters(1, 1, 10, 5232, 1424, 0, 51, 0)\n") != std::string::npos);
    CHECK(lua.find("FacetBits.Invisible, 0)\n") != std::string::npos);
    CHECK(lua.find("FacetBits.Untouchable, 0)\n") != std::string::npos);
    // The wall is repainted and hidden on entering: its stone faces carry the texture's number, its others the
    // wall's own, and hiding names both.
    const size_t setTexture = lua.find("evt.SetTexture(");
    REQUIRE(setTexture != std::string::npos);
    const int stoneNumber = std::atoi(lua.c_str() + setTexture + 15);
    CHECK(lua.find("evt.SetTexture(" + std::to_string(stoneNumber) + ", \"t06b02\")") != std::string::npos);
    CHECK(lua.find("evt.SetFacetBit(" + std::to_string(stoneNumber) + ", FacetBits.Invisible, 1)")
        != std::string::npos);
    const uint32_t invisible = 0x00002000;
    const uint32_t untouchable = 0x20000000;
    const uint32_t plate = 0x04000000;
    const uint32_t clickable = 0x02000000;
    size_t stone = 0;
    size_t hidden = 0;
    size_t stepped = 0;
    size_t clicked = 0;

    for (const YAML::Node &face : built.scene["bmodel_faces"]["interactive_faces"])
    {
        const uint32_t attributes = face["legacy_attributes"].as<uint32_t>();
        stone += face["cog_number"].as<int>() == stoneNumber ? 1 : 0;
        hidden += (attributes & invisible) != 0 && (attributes & untouchable) != 0 && face["cog_number"].as<int>() != 0
            ? 1 : 0;
        stepped += (attributes & plate) != 0 ? 1 : 0;
        clicked += (attributes & clickable) != 0 ? 1 : 0;
    }

    CHECK(stone >= 5);
    // The house (hidden) and the tower (8 faces) start invisible and without touch, every face with a number.
    CHECK(hidden > 8 + 10);
    // The trap's top is the one face stepped on; nobody clicks its sides.
    CHECK(stepped == 1);
    // The signpost: the post says Signpost, each arm its own title on its six faces.
    CHECK(facesOfEvent(built.scene, eventNumberOf(lua, "West to Erathia")) == 6);
    CHECK(facesOfEvent(built.scene, eventNumberOf(lua, "East")) == 6);
    CHECK(facesOfEvent(built.scene, eventNumberOf(lua, "Signpost")) == 5);
    CHECK(clicked > 17);

    // A decoration that an event changes carries a number of its own; one that starts hidden has the map's flag.
    const std::string trees =
        "structures:\n"
        "  - {id: thing:tree, kind: decoration, decoration: tree12, at: [57, 57], title: Fruit Tree, once: true, "
        "condition: {not: {season: winter}}, effects: [{give_item: 1432}, {text: You received an apple}, "
        "{set_sprite: {of: thing:tree, to: tree37}}]}\n"
        "  - {id: thing:fire, kind: decoration, decoration: tree37, at: [58, 58], hidden: true, title: Fire}\n"
        "  - {id: thing:pit, kind: platform, at: [59, 59], size: [128, 128], title: Signal Fire Pit, "
        "effects: [{show: thing:fire}]}\n"
        "  - {id: thing:plain, kind: decoration, decoration: tree12, at: [60, 60], turn: 90}\n";
    Project withTrees = buildingProject("      - {building: building:home, at: [40, 40], facing: s}\n", trees);
    LoweredOutdoorMap lowered;
    std::vector<ProjectIssue> issues;
    REQUIRE(lowerOutdoorProject(withTrees, lowered, issues));
    IdsLock ids;
    OutdoorEventWords words(withTrees, root, ids, issues);
    OutdoorThings things;
    std::vector<std::string> warnings;
    REQUIRE(raiseOutdoorThings(withTrees, lowered, root, ids, words, things, issues, warnings));
    REQUIRE(things.decorationIds == std::vector<std::string>{"thing:tree", "thing:fire", "thing:plain"});
    CHECK(words.decorationNumber("thing:tree") == 30000);
    CHECK(words.decorationNumber("thing:fire") == 30001);
    CHECK(words.decorationNumber("thing:plain") == 0);
    CHECK(words.targets().at("thing:fire").hidden);
    // A decoration's `turn` (degrees clockwise) is its facing in the map (degrees counter-clockwise); none: 0 (D-35).
    CHECK(things.decorations[2].facing == 270);
    CHECK(things.decorations[0].facing == 0);
    const OutdoorEventPlan *pTree = eventOf(things, "evt:thing:tree");
    REQUIRE(pTree != nullptr);
    CHECK(pTree->body == std::vector<std::string>{"if IsAtLeast(MapVar(0), 1) then return end",
        "if not (not (evt.CheckSeason(Season.Winter))) then", "    return", "end", "SetValue(MapVar(0), 1)",
        "evt.GiveItem(1, 0, 1432)", "evt.StatusText(\"You received an apple\")",
        "evt.SetSprite(30000, 1, \"tree37\")"});
    const OutdoorEventPlan *pPit = eventOf(things, "evt:thing:pit");
    REQUIRE(pPit != nullptr);
    CHECK(pPit->body == std::vector<std::string>{"evt.SetSprite(30001, 1)"});
    std::vector<std::string> said;
    words.finish(said);
    CHECK(said.empty());

    // Refused, with what to change.
    const auto refused = [&root](const std::string &text)
    {
        Project bad = buildingProject("      - {building: building:home, at: [40, 40], facing: s}\n", text);
        LoweredOutdoorMap land;
        std::vector<ProjectIssue> found;
        REQUIRE(lowerOutdoorProject(bad, land, found));
        IdsLock lock;
        OutdoorEventWords badWords(bad, root, lock, found);
        OutdoorThings unused;
        std::vector<std::string> unusedWarnings;
        raiseOutdoorThings(bad, land, root, lock, badWords, unused, found, unusedWarnings);

        for (Game::OutdoorBModel &model : unused.models)
        {
            badWords.applyToModel(model.name, model);
        }

        return found;
    };
    CHECK(anyIssue(refused("events:\n  - {id: evt:a, trigger: click, effects: [{gold: 1}]}\n"),
        "runs on entering the map (trigger: load), on leaving it (trigger: leave), by the clock"));
    CHECK(anyIssue(refused("events:\n  - {id: evt:a, trigger: timer, effects: [{gold: 1}]}\n"),
        "a timer event has `every`"));
    CHECK(anyIssue(refused("events:\n  - {id: evt:a, trigger: load}\n"), "the event does nothing"));
    CHECK(anyIssue(refused("events:\n  - {id: evt:a, trigger: load, effects: [{show: thing:nothing}]}\n"),
        "which the sketch does not draw"));
    CHECK(anyIssue(refused("events:\n  - {id: evt:a, trigger: load, effects: [{show_actors: 7}]}\n"),
        "no entry has group 7"));
    CHECK(anyIssue(refused("structures:\n  - {id: thing:t, kind: decoration, decoration: tree12, at: [50, 50]}\n"
        "events:\n  - {id: evt:a, trigger: load, effects: [{set_sprite: {of: thing:t, to: palm99}}]}\n"),
        "there is no decoration named palm99"));
    CHECK(anyIssue(refused("structures:\n  - {id: thing:w, kind: wall, line: [[70, 70], [80, 70]]}\n"
        "events:\n  - {id: evt:a, trigger: load, effects: [{set_texture: {of: thing:w, from: marble9, "
        "to: t06b02}}]}\n"), "which has no face of that texture; its textures are"));
    CHECK(anyIssue(refused("structures:\n  - {id: thing:o, kind: obelisk, at: [50, 50], trigger: step, "
        "effects: [{gold: 1}]}\n"), "has no face one can stand on"));
    CHECK(anyIssue(refused("structures:\n  - {id: thing:p, kind: platform, at: [50, 50], size: [128, 128], "
        "trigger: step, house: 3}\n"), "is entered by a click"));
    CHECK(anyIssue(refused("structures:\n  - {id: thing:s, kind: sign, at: [50, 50], arms: [{title: A, "
        "toward: n}, {title: B, toward: n}]}\n"), "each way once"));
    CHECK(anyIssue(refused("actors:\n  - {monster: Goblin, at: [50, 50], hidden: true}\n"),
        "give the entry a `group` number of its own"));
    // Nothing shows it: said, not refused.
    Project lonely = buildingProject("      - {building: building:home, at: [40, 40], facing: s}\n",
        "structures:\n  - {id: thing:tower, kind: obelisk, at: [55, 55], hidden: true}\n");
    const BuiltOutdoor alone = builtOutdoor(lonely, "oymap_outdoor_events_alone");
    CHECK(alone.built);
    CHECK(std::any_of(alone.warnings.begin(), alone.warnings.end(), [](const std::string &warning)
    {
        return warning.find("thing:tower starts hidden and no event shows it") != std::string::npos;
    }));
    std::filesystem::remove_all(root, error);
}

TEST_CASE("D5: a translucent structure's faces are listed in the scene's translucent_faces")
{
    const std::string house = "      - {building: building:home, at: [40, 40], facing: s}\n";
    const std::string more =
        "structures:\n"
        "  - {id: thing:curtain, kind: wall, line: [[70, 70], [80, 70]], translucent: true}\n"
        "  - {id: thing:wall, kind: wall, line: [[70, 80], [80, 80]]}\n";
    const BuiltOutdoor built = builtOutdoor(buildingProject(house, more), "oymap_outdoor_translucent");
    INFO(built.warnings.size());
    REQUIRE(built.built);
    const YAML::Node faces = built.scene["bmodel_faces"]["translucent_faces"];
    REQUIRE(faces.IsSequence());
    CHECK(faces.size() >= 5);
    std::set<int> models;

    for (const YAML::Node &face : faces)
    {
        models.insert(face["bmodel_index"].as<int>());
    }

    // One wall's model, not the other's.
    CHECK(models.size() == 1);
    // The game reads the list back (the build checked it applies to the map: built is true).
    std::string error;
    const std::optional<Game::OutdoorSceneData> scene =
        Game::OutdoorSceneYmlLoader().loadFromText(YAML::Dump(built.scene), error);
    REQUIRE_MESSAGE(scene.has_value(), error);
    CHECK(scene->translucentFaces.size() == faces.size());
}

TEST_CASE("an outdoor map's own monster relations are set on entering the map, as an indoor map's")
{
    const std::filesystem::path root = std::filesystem::temp_directory_path() / "oymap_outdoor_relations_root";
    std::error_code error;
    std::filesystem::create_directories(root / "engine" / "data_tables", error);
    {
        std::ofstream monsters(root / "engine" / "data_tables" / "monster_data.txt");
        monsters << "#\tName\tPicture\n202\tArcher\tArcher A\n203\tBowman\tArcher B\n211\tFloating Eye\tBeholder A\n";
    }
    const auto raised = [](const std::string &more, const std::filesystem::path &assets,
        std::vector<ProjectIssue> &issues, std::vector<std::string> &warnings)
    {
        const Project project = buildingProject("      - {building: building:home, at: [40, 40], facing: s}\n", more);
        LoweredOutdoorMap lowered;
        REQUIRE(lowerOutdoorProject(project, lowered, issues));
        IdsLock ids;
        OutdoorEventWords words(project, assets, ids, issues);
        OutdoorThings things;
        raiseOutdoorThings(project, lowered, assets, ids, words, things, issues, warnings);
        return things;
    };
    std::vector<ProjectIssue> issues;
    std::vector<std::string> warnings;
    const OutdoorThings things = raised("relations:\n"
        "  - {of: [Archer A, 203], toward: party, relation: hostile}\n"
        "  - {of: 211, toward: 202, relation: friendly, both_ways: true}\n", root, issues, warnings);
    CHECK(issues.empty());
    const OutdoorEventPlan *pEvent = eventOf(things, "evt:studio_relations");
    REQUIRE(pEvent != nullptr);
    CHECK(pEvent->body == std::vector<std::string>{"evt.SetMonsterRelation(202, 0, 4)",
        "evt.SetMonsterRelation(203, 0, 4)", "evt.SetMonsterRelation(211, 202, 0)",
        "evt.SetMonsterRelation(202, 211, 0)"});
    // Run on entering the map, by an event no face carries; the rows kept for the build's hostility check.
    CHECK(std::find(things.onLoad.begin(), things.onLoad.end(), pEvent->number) != things.onLoad.end());
    CHECK(things.relations.size() == 4);
    // Without relations no such event.
    CHECK(eventOf(raised("", root, issues, warnings), "evt:studio_relations") == nullptr);
    // Refused, in the sketch's words: a kind the table lacks, a name two rows share, the party both ways, the id
    // taken by an event of the sketch.
    const auto refused = [&](const std::string &more)
    {
        std::vector<ProjectIssue> found;
        std::vector<std::string> unused;
        raised(more, root, found, unused);
        return found;
    };
    CHECK(anyIssue(refused("relations:\n  - {of: 99, toward: party, relation: hostile}\n"),
        "there is no monster number 99 in monster_data.txt"));
    CHECK(refused("relations:\n  - {of: 99, toward: party, relation: hostile}\n").front().file == "sketch.yml");
    CHECK(anyIssue(refused("relations:\n  - {of: 202, toward: party, relation: 4, both_ways: true}\n"),
        "drop `both_ways`"));
    CHECK(anyIssue(refused("events:\n  - {id: evt:studio_relations, trigger: load, effects: [{gold: 1}]}\n"
        "relations:\n  - {of: 202, toward: party, relation: hostile}\n"), "is the build's own"));
    // Without an asset root the relations are left out and said, as placed actors are.
    std::vector<std::string> said;
    const OutdoorThings bare = raised("relations:\n  - {of: 202, toward: party, relation: hostile}\n", {}, issues,
        said);
    CHECK(eventOf(bare, "evt:studio_relations") == nullptr);
    CHECK(std::any_of(said.begin(), said.end(), [](const std::string &warning)
    {
        return warning.find("relations: 1 entries are left out") != std::string::npos;
    }));
    CHECK(issues.empty());
    std::filesystem::remove_all(root, error);
}

TEST_CASE("scatter in clumps stands round a few middles; steep ground takes only what says so; roads meet thin")
{
    const std::string table = "#\tInternalName\tHint\n1\tnothing\t\n377\trock17\trock\n464\ttree12\ttree\n";
    const Project project = buildingProject("      - {building: building:home, at: [40, 40], facing: s}\n",
        "scatter:\n  - {decoration: tree12, count: 30, clusters: 2, cluster_radius: 2, spacing: 0.5, "
        "polygon: [[70, 70], [110, 70], [110, 110], [70, 110]]}\n"
        "roads:\n  - {link: road:a, line: [[10.5, 100.5], [30.5, 100.5]]}\n"
        "  - {link: road:b, line: [[20.5, 100.5], [20.5, 110.5]]}\n"
        "  - {link: road:c, line: [[20.5, 100.5], [21.5, 101.5], [30.5, 110.5]]}\n");
    LoweredOutdoorMap lowered;
    std::vector<ProjectIssue> issues;
    REQUIRE(lowerOutdoorProject(project, lowered, issues));
    OutdoorPlaces places;
    std::vector<std::string> warnings;
    REQUIRE(placeOutdoorThings(project, lowered, table, places, issues, warnings, {{84.0, 84.0, 96.0, 96.0}}));
    REQUIRE(places.decorations.size() == 30);
    // Every tree lies within two cells of one of two places, and none on the ground kept off.
    std::vector<std::array<double, 2>> middles;

    for (const OutdoorPlacedDecoration &decoration : places.decorations)
    {
        const double x = decoration.x / 512.0 + 64.0;
        const double y = 64.0 - decoration.y / 512.0;
        CHECK_FALSE((x > 83.75 && x < 96.25 && y > 83.75 && y < 96.25));
        const bool near = std::any_of(middles.begin(), middles.end(), [x, y](const std::array<double, 2> &middle)
        {
            return std::hypot(middle[0] - x, middle[1] - y) <= 4.0;
        });

        if (!near)
        {
            middles.push_back({x, y});
        }
    }

    CHECK(middles.size() == 2);

    // Where three roads meet no four road cells make a square.
    for (int y = 95; y < 115; ++y)
    {
        for (int x = 5; x < 35; ++x)
        {
            const auto road = [&lowered](int cellX, int cellY)
            {
                // The road tiles of the map's fourth set (198 and the 35 after it).
                return tileAt(lowered, cellX, cellY) >= 198 && tileAt(lowered, cellX, cellY) < 198 + 36;
            };
            CHECK_FALSE((road(x, y) && road(x + 1, y) && road(x, y + 1) && road(x + 1, y + 1)));
        }
    }
}

TEST_CASE("the second batch's words are in the schemas, every one described")
{
    const std::string &sketch = SchemaSet::builtIn().text("sketch.schema.json");

    for (const char *pWord : {"\"parts\"", "\"turn\"", "\"kit\"", "\"walls\"", "\"upper_walls\"", "\"windows\"",
             "\"roof_pitch\"", "\"eaves\"", "\"fascia\"", "\"hip\"", "\"ridge\"", "\"ridge_along\"", "\"roof_low\"",
             "\"parapet\"", "\"battlements\"", "\"doors\"", "\"structures\"", "\"gates\"", "\"kerb\"", "\"piers\"",
             "\"roofed\"", "\"effects\"", "\"once\"", "\"actors\"", "\"clusters\"", "\"cluster_radius\"",
             "\"steep\""})
    {
        CHECK_MESSAGE(sketch.find(pWord) != std::string::npos, pWord);
    }

    const YAML::Node air = SchemaSet::builtIn().root("atmosphere.schema.json");
    REQUIRE(air.IsMap());
    size_t fields = 0;
    checkDescribed(air["properties"]["daily_fog"], "atmosphere.daily_fog", fields);
    CHECK(fields >= 9);
    CHECK(air["properties"]["sky"]["description"].IsDefined());
    CHECK(air["properties"]["precipitation"]["description"].IsDefined());
}

// ---- The rim: the land beyond the square the party walks (core/OutdoorRim) and how compare judges it ----

#include "core/OutdoorRim.h"

namespace
{
bool anyWarning(const LoweredOutdoorMap &lowered, const std::string &fragment)
{
    return std::any_of(lowered.warnings.begin(), lowered.warnings.end(), [&fragment](const std::string &warning)
    {
        return warning.find(fragment) != std::string::npos;
    });
}

// A ridge 3008 high on rows 5 to 10 along the north side, beyond the playable square; its height every other
// stretch of `period` cells, starting `shift` cells along.
Game::OutdoorMapData ridgedMap(int period, int shift)
{
    Game::OutdoorMapData map = testMap();

    for (int y = 5; y <= 10; ++y)
    {
        for (int x = 0; x < Side; ++x)
        {
            const bool high = period == 0 || ((x + shift) / period) % 2 == 0;
            map.heightMap[y * Side + x] = static_cast<uint8_t>(high ? 94 : 40);
        }
    }

    return map;
}
}

TEST_CASE("the rim is judged by its skyline from the square's edge, not node by node")
{
    const Game::OutdoorMapData ridged = ridgedMap(0, 0);
    const OutdoorCompareResult self = compared(ridged, ridged);
    CHECK(self.score == doctest::Approx(1.0));
    CHECK(partOf(self, "rim") == doctest::Approx(1.0));
    CHECK(self.skylineRays == 4 * 45 * 51);

    // Level ground where the original has a ridge: only the rim part loses, and the north regions say so.
    const OutdoorCompareResult flat = compared(ridged, testMap());
    checkOnlyTheseDiffer(flat, {"rim"});
    CHECK(partOf(flat, "rim") < 0.8);
    CHECK(partOf(flat, "heights") == doctest::Approx(1.0));
    CHECK(flat.originalSkyline > flat.rebuiltSkyline);
    const OutdoorCompareRegion &worst = flat.regions[flat.worstRegions[0]];
    CHECK(worst.row == 0);
    CHECK(worst.skylineRays > 0);
    CHECK(worst.sentence.find("skyline") != std::string::npos);
    CHECK(worst.sentence.find("lower") != std::string::npos);

    // Node by node (`--without rim`): the heights part loses instead and the rim's skyline has no weight.
    const OutdoorCompareResult nodes = compared(ridged, testMap(), false);
    checkOnlyTheseDiffer(nodes, {"heights", "relief", "cliffs"});
    CHECK(partOf(nodes, "heights") < 1.0);
    CHECK(partOf(nodes, "rim") == doctest::Approx(partOf(flat, "rim")));
    double weight = 0.0;

    for (const OutdoorComparePart &part : nodes.parts)
    {
        weight += part.weight;
        CHECK((part.id == "rim") == (part.weight == 0.0));
    }

    CHECK(weight == doctest::Approx(1.0));

    // Tops two cells along from where the original has them: node by node much is lost, the skyline keeps most.
    const Game::OutdoorMapData tops = ridgedMap(8, 0);
    const Game::OutdoorMapData shifted = ridgedMap(8, 2);
    const OutdoorCompareResult moved = compared(tops, shifted);
    const OutdoorCompareResult movedNodes = compared(tops, shifted, false);
    CHECK(partOf(moved, "rim") > 0.85);
    CHECK(partOf(moved, "rim") > partOf(compared(tops, testMap()), "rim"));
    CHECK(partOf(movedNodes, "heights") < 0.99);
}

TEST_CASE("frame.rim: a ridge beyond the square, a sea, a shelf, the edge row, and a road's valley")
{
    const std::string rim = "frame:\n  rim:\n"
        "    - {side: north, form: ridge, height: [2000, 3000], crest: 12, floor: 640}\n"
        "    - {side: south, form: level, height: 0}\n"
        "    - {side: east, form: level, height: [2000, 2800], meet: 3}\n"
        "  edge: {height: 640, east: 2304}\n"
        "roads:\n  - {link: road:out, line: [[60.5, 60.5], [60.5, 0.5]], bed: [640, 640]}\n";
    const LoweredOutdoorMap plain = loweredOf(std::string(LevelLand) + "roads:\n"
        "  - {link: road:out, line: [[60.5, 60.5], [60.5, 0.5]], bed: [640, 640]}\n");
    const LoweredOutdoorMap shaped = loweredOf(std::string(LevelLand) + rim);

    // Inside the square nothing changes.
    for (int y = OutdoorPlayableFirstNode; y <= OutdoorPlayableLastNode; ++y)
    {
        for (int x = OutdoorPlayableFirstNode; x <= OutdoorPlayableLastNode; ++x)
        {
            CAPTURE(x);
            CAPTURE(y);
            REQUIRE(sampleAt(shaped, x, y) == sampleAt(plain, x, y));
        }
    }

    // The north ridge: tops between its heights near its crest, the floor at the square, the edge row at 640.
    int highest = 0;

    for (int x = 25; x < 50; ++x)
    {
        for (int y = 3; y <= 11; ++y)
        {
            highest = std::max(highest, sampleAt(shaped, x, y) * 32);
        }

        CHECK(sampleAt(shaped, x, 0) * 32 == 640);
        CHECK(sampleAt(shaped, x, 18) * 32 <= 800);
    }

    CHECK(highest >= 2500);
    CHECK(highest <= 3200);
    // The road runs out through a valley at its bed, the ridge standing beside it.
    CHECK(sampleAt(shaped, 60, 7) * 32 == 640);
    CHECK(std::max(sampleAt(shaped, 52, 7), sampleAt(shaped, 68, 7)) * 32 >= 1600);
    // The sea: level at 0 four cells out (the edge row at 640 is the map's edge).
    CHECK(sampleAt(shaped, 60, OutdoorPlayableLastNode + 6) == 0);
    CHECK(sampleAt(shaped, 60, 127) * 32 == 640);
    // The shelf: between its heights, uneven, and its edge column at 2304.
    std::set<int> shelf;

    for (int y = 30; y < 90; ++y)
    {
        const int height = sampleAt(shaped, OutdoorPlayableLastNode + 8, y) * 32;
        CHECK(height >= 1984);
        CHECK(height <= 2816);
        shelf.insert(height);
        CHECK(sampleAt(shaped, 127, y) * 32 == 2304);
    }

    CHECK(shelf.size() > 4);
    // The same words give the same land; another seed another ridge of the same description.
    CHECK(loweredOf(std::string(LevelLand) + rim).samples == shaped.samples);
    std::string seeded = rim;
    seeded.replace(seeded.find("floor: 640}"), 11, "floor: 640, seed: 9}");
    CHECK(loweredOf(std::string(LevelLand) + seeded).samples != shaped.samples);
}

TEST_CASE("frame.rim refuses what cannot be built and says what to change")
{
    const auto refused = [](const std::string &entry, const std::string &fragment)
    {
        CAPTURE(entry);
        CHECK(anyIssue(refusedWith(std::string(LevelLand) + "frame:\n  rim:\n    - " + entry + "\n"), fragment));
    };
    refused("{side: north, form: ridge, height: 3000}", "a ridge needs two heights");
    refused("{side: north, form: ridge, height: [3000, 2000]}", "swap 3000 and 2000");
    refused("{side: north, form: ridge, height: [2000, 3000], crest: 20}", "4 to 15 cells out");
    refused("{side: north, form: ridge, height: [2000, 3000], meet: 3}", "`meet` is level ground's word");
    refused("{side: north, form: ridge, height: [2000, 3000], floor: 2500}", "does not stand above its floor");
    refused("{side: north, form: level, height: 640, crest: 9}", "`floor` and `crest` are a ridge's words");
    refused("{side: north, form: level, height: 640, meet: 20}", "1 to 12");
    refused("{side: north, form: level, height: 9000}", "0 to 8160");
    refused("{side: north, form: level, height: 640, roughness: 600}", "0 to 512");
    refused("{side: north, form: level, height: 640, span: [80, 40]}", "from below to");
    refused("{side: north, form: hill, height: 640}", "`level`");
    refused("{side: north, height: 640}", "no `form`");
    CHECK(anyIssue(refusedWith(std::string(LevelLand) + "frame:\n  rim:\n"
        "    - {side: north, span: [0, 70], form: level, height: 0}\n"
        "    - {side: north, span: [60, 128], form: level, height: 640}\n"), "do not overlap"));
    CHECK(anyIssue(refusedWith(std::string(LevelLand) + "frame:\n  edge: {height: 9000}\n"), "0 to 8160"));
}

TEST_CASE("a rim entry without a form shapes nothing, and the retired depth is warned of")
{
    const LoweredOutdoorMap plain = loweredOf(LevelLand);
    const LoweredOutdoorMap noted = loweredOf(std::string(LevelLand) + "frame:\n  rim:\n"
        "    - {side: west, depth: [20, 33], notes: \"the upland\"}\n");
    CHECK(noted.samples == plain.samples);
    CHECK(anyWarning(noted, "has no `form`, so it shapes nothing"));
    CHECK(anyWarning(noted, "depth is retired"));
    CHECK_FALSE(anyWarning(plain, "rim"));
}

TEST_CASE("the rim's words are in the sketch schema, every one described")
{
    const YAML::Node root = inlinedSketchSchema();
    REQUIRE(root.IsMap());
    const YAML::Node frame = root["properties"]["frame"]["properties"];
    const YAML::Node entry = frame["rim"]["items"]["properties"];

    for (const char *pWord : {"side", "span", "form", "height", "floor", "crest", "meet", "roughness", "seed",
             "space", "depth"})
    {
        CAPTURE(pWord);
        CHECK(entry[pWord]["description"].IsDefined());
    }

    for (const char *pWord : {"height", "north", "east", "south", "west"})
    {
        CAPTURE(pWord);
        CHECK(frame["edge"]["properties"][pWord]["description"].IsDefined());
    }

    CHECK(frame["rim"]["items"]["required"].size() == 1);
}

// ---- Ridges and rough ground inside the square (heights.ridges, heights.rough) ----

TEST_CASE("heights.ridges: a line of nodes at its height, upright or sloping, a channel below the land")
{
    const LoweredOutdoorMap plain = loweredOf(LevelLand);
    const LoweredOutdoorMap ridged = loweredOf(std::string(LevelLand) + "  ridges:\n"
        "    - {line: [[40, 60], [80, 60]], height: 1280}\n"
        "    - {line: [[40, 70], [80, 70]], height: [1280, 2560], slope: 2}\n"
        "    - {line: [[40, 80], [80, 80]], height: 0, width: 3}\n"
        "    - {line: [[40, 90.5], [80, 90.5]], height: 1280}\n");
    // Upright: the line's nodes at 1280, their neighbours as they were.
    CHECK(sampleAt(ridged, 60, 60) * 32 == 1280);
    CHECK(sampleAt(ridged, 60, 59) == sampleAt(plain, 60, 59));
    CHECK(sampleAt(ridged, 60, 61) == sampleAt(plain, 60, 61));
    CHECK(sampleAt(ridged, 39, 60) == sampleAt(plain, 39, 60));
    // Heights along the line run straight between its points; the sides run back over two cells.
    CHECK(sampleAt(ridged, 60, 70) * 32 == 1920);
    CHECK(sampleAt(ridged, 60, 69) * 32 == 640 + (1920 - 640) * 3 / 4);
    CHECK(sampleAt(ridged, 60, 68) * 32 == 640 + (1920 - 640) / 4);
    CHECK(sampleAt(ridged, 60, 67) == sampleAt(plain, 60, 67));
    // A channel three nodes wide.
    for (int y = 79; y <= 81; ++y)
    {
        CHECK(sampleAt(ridged, 60, y) == 0);
    }

    CHECK(sampleAt(ridged, 60, 78) == sampleAt(plain, 60, 78));
    // A line between two rows of nodes: both rows are half a cell from it.
    CHECK(sampleAt(ridged, 60, 90) * 32 == 1280);
    CHECK(sampleAt(ridged, 60, 91) * 32 == 1280);
    // A one-node ridge 640 above the land makes cells too steep to walk on both sides, as the originals' dykes do.
    const auto relief = [&ridged](int x, int y)
    {
        const int corners[4] = {sampleAt(ridged, x, y), sampleAt(ridged, x + 1, y), sampleAt(ridged, x, y + 1),
            sampleAt(ridged, x + 1, y + 1)};
        return (*std::max_element(corners, corners + 4) - *std::min_element(corners, corners + 4)) * 32;
    };
    CHECK(relief(60, 59) > 512);
    CHECK(relief(60, 60) > 512);
    // Water keeps its level and the build says so.
    const LoweredOutdoorMap wet = loweredOf(std::string(LevelLand) + "  ridges:\n"
        "    - {line: [[40, 60], [80, 60]], height: 1280}\n"
        "water:\n  bodies:\n    - {id: water:pond, polygon: [[55, 55], [65, 55], [65, 65], [55, 65]], level: 576}\n");
    CHECK(sampleAt(wet, 60, 60) * 32 == 576);
    CHECK(sampleAt(wet, 45, 60) * 32 == 1280);
    CHECK(std::any_of(wet.warnings.begin(), wet.warnings.end(), [](const std::string &warning)
    {
        return warning.find("heights.ridges") != std::string::npos && warning.find("water") != std::string::npos;
    }));
    // What cannot be built.
    const auto refused = [](const std::string &entry, const std::string &fragment)
    {
        CAPTURE(entry);
        CHECK(anyIssue(refusedWith(std::string(LevelLand) + "  ridges:\n    - " + entry + "\n"), fragment));
    };
    refused("{line: [[40, 60]], height: 640}", "at least two");
    refused("{line: [[40, 60], [80, 60]], height: [640, 700, 800]}", "one number for each of its 2 points");
    refused("{line: [[40, 60], [80, 60]]}", "one number for each");
    refused("{line: [[40, 60], [80, 60]], height: 9000}", "0 to 8160");
    refused("{line: [[40, 60], [80, 60]], height: 640, width: 0.5}", "1 to 8");
    refused("{line: [[40, 60], [80, 60]], height: 640, slope: 20}", "0 (upright, as a dyke) to 16");
}

TEST_CASE("heights.rough: an area's ground moves by about its amount, the rest not at all, the same words alike")
{
    const LoweredOutdoorMap plain = loweredOf(LevelLand);
    const std::string area = "  rough:\n    - {polygon: [[30, 30], [90, 30], [90, 90], [30, 90]], amount: 64}\n";
    const LoweredOutdoorMap rough = loweredOf(std::string(LevelLand) + area);
    double moved = 0.0;
    size_t count = 0;

    for (int y = 0; y < Side; ++y)
    {
        for (int x = 0; x < Side; ++x)
        {
            const int delta = std::abs(sampleAt(rough, x, y) - sampleAt(plain, x, y)) * 32;

            if (x < 30 || x > 90 || y < 30 || y > 90)
            {
                CHECK(delta == 0);
            }
            else if (x >= 33 && x <= 87 && y >= 33 && y <= 87)
            {
                moved += delta;
                ++count;
            }
        }
    }

    CHECK(moved / count > 40.0);
    CHECK(moved / count < 90.0);
    CHECK(loweredOf(std::string(LevelLand) + area).samples == rough.samples);
    std::string seeded = area;
    seeded.replace(seeded.find("amount: 64"), 10, "amount: 64, seed: 7");
    CHECK(loweredOf(std::string(LevelLand) + seeded).samples != rough.samples);
    // Bumps of several cells: neighbours move together.
    const LoweredOutdoorMap bumps = loweredOf(std::string(LevelLand)
        + "  rough:\n    - {polygon: [[30, 30], [90, 30], [90, 90], [30, 90]], amount: 64, scale: 6}\n");
    size_t sameAsNext = 0;

    for (int x = 40; x < 80; ++x)
    {
        sameAsNext += std::abs(sampleAt(bumps, x, 60) - sampleAt(bumps, x + 1, 60)) <= 1 ? 1 : 0;
    }

    CHECK(sameAsNext > 30);
    const auto refused = [](const std::string &entry, const std::string &fragment)
    {
        CAPTURE(entry);
        CHECK(anyIssue(refusedWith(std::string(LevelLand) + "  rough:\n    - " + entry + "\n"), fragment));
    };
    refused("{polygon: [[30, 30], [90, 30], [90, 90], [30, 90]], amount: 0}", "above 0 and at most 256");
    refused("{polygon: [[30, 30], [90, 30], [90, 90], [30, 90]], amount: 300}", "above 0 and at most 256");
    refused("{polygon: [[30, 30], [90, 30], [90, 90], [30, 90]], amount: 20, scale: 9}", "1 (node by node");
    refused("{polygon: [[30, 30], [90, 30]], amount: 20}", "at least three");
}

TEST_CASE("the ridges' and rough areas' words are in the sketch schema, every one described")
{
    const YAML::Node heights = inlinedSketchSchema()["properties"]["heights"]["properties"];

    for (const char *pWord : {"line", "height", "width", "slope"})
    {
        CAPTURE(pWord);
        CHECK(heights["ridges"]["items"]["properties"][pWord]["description"].IsDefined());
    }

    for (const char *pWord : {"polygon", "amount", "scale", "seed"})
    {
        CAPTURE(pWord);
        CHECK(heights["rough"]["items"]["properties"][pWord]["description"].IsDefined());
    }
}

// ---- Decorations in rows and rings (scatter[].line, closed) ----

TEST_CASE("scatter along a line plants a row evenly from end to end, and a ring evenly round, where drawn")
{
    const std::string table = "#\tInternalName\tHint\n1\tnothing\t\n377\trock17\trock\n464\ttree12\ttree\n";
    const auto planted = [&table](const std::string &scatter, std::vector<ProjectIssue> &issues)
    {
        const Project project = buildingProject("      - {building: building:home, at: [40, 40], facing: s}\n",
            "scatter:\n" + scatter);
        LoweredOutdoorMap lowered;
        REQUIRE(lowerOutdoorProject(project, lowered, issues));
        OutdoorPlaces places;
        std::vector<std::string> warnings;
        placeOutdoorThings(project, lowered, table, places, issues, warnings);
        std::vector<std::array<double, 2>> cells;

        for (const OutdoorPlacedDecoration &decoration : places.decorations)
        {
            cells.push_back({decoration.x / 512.0 + 64.0, 64.0 - decoration.y / 512.0});
        }

        return cells;
    };
    std::vector<ProjectIssue> issues;
    // A row of five over four cells, one a cell; it crosses the house's plot and stands there all the same.
    const std::vector<std::array<double, 2>> row = planted("  - {decoration: tree12, count: 5, "
        "line: [[38, 41], [42, 41]]}\n", issues);
    CHECK(issues.empty());
    REQUIRE(row.size() == 5);

    for (size_t index = 0; index < row.size(); ++index)
    {
        CHECK(row[index][0] == doctest::Approx(38.0 + index));
        CHECK(row[index][1] == doctest::Approx(41.0));
    }

    // A ring of eight round a square of side 4: the corners and the middles of the sides.
    const std::vector<std::array<double, 2>> ring = planted("  - {decoration: rock17, count: 8, closed: true, "
        "line: [[70, 70], [74, 70], [74, 74], [70, 74]]}\n", issues);
    CHECK(issues.empty());
    REQUIRE(ring.size() == 8);
    CHECK(ring[0][0] == doctest::Approx(70.0));
    CHECK(ring[1][0] == doctest::Approx(72.0));
    CHECK(ring[2][0] == doctest::Approx(74.0));
    CHECK(ring[3][1] == doctest::Approx(72.0));
    CHECK(ring[7][0] == doctest::Approx(70.0));
    CHECK(ring[7][1] == doctest::Approx(72.0));
    // What cannot be built.
    const auto refused = [&planted](const std::string &entry, const std::string &fragment)
    {
        CAPTURE(entry);
        std::vector<ProjectIssue> found;
        planted("  - " + entry + "\n", found);
        CHECK(anyIssue(found, fragment));
    };
    refused("{decoration: tree12, count: 1, line: [[60, 60], [64, 60]]}", "2 or more along a row");
    refused("{decoration: tree12, count: 4, closed: true, line: [[60, 60], [64, 60]]}", "at least three");
    refused("{decoration: tree12, count: 4, line: [[60, 60], [64, 60]], clusters: 2}", "stands evenly along");
    refused("{decoration: tree12, count: 4, line: [[60, 60], [64, 60]], spacing: 1}", "stands evenly along");
    refused("{decoration: tree12, count: 4, line: [[60, 60], [127.5, 60]]}", "0.5 to 126.5");
    refused("{decoration: tree12, count: 4, line: [[60, 60], [60, 60]]}", "no length");
}

TEST_CASE("the rows' words are in the sketch schema, described")
{
    const YAML::Node scatter = inlinedSketchSchema()["properties"]["scatter"]["items"];
    CHECK(scatter["properties"]["line"]["description"].IsDefined());
    CHECK(scatter["properties"]["closed"]["description"].IsDefined());
    CHECK(scatter["oneOf"].size() == 3);
}

// ---- Buildings: a door up a storey, a hip cut flat, a bridge's arch and railings ----

TEST_CASE("a door in an upper storey stands on its row's sill, and the rows it is not in keep their window")
{
    LoweredOutdoorMap lowered = loweredBuildings("      - {building: building:home, at: [40, 40], facing: s, "
        "foundation: 0, wall_height: 768, door: none, doors: [{wall: s, bay: 2, storey: 2, house: 905}]}\n");
    REQUIRE(lowered.buildings.size() == 1);
    OutdoorBuildingPlan &plan = lowered.buildings[0];
    REQUIRE(plan.doors.size() == 1);
    CHECK(plan.doors[0].storey == 1);
    CHECK(plan.doors[0].bay == 2);
    plan.doors[0].event = 7;
    plan.nameEvent = 8;
    const Game::OutdoorBModel house = raiseOutdoorBuilding(plan);
    REQUIRE(plan.doors[0].face >= 0);
    const Game::OutdoorBModelFace &door = house.faces[plan.doors[0].face];
    CHECK(door.cogTriggeredNumber == 7);
    int low = 1 << 30;
    int high = -(1 << 30);

    for (const uint16_t index : door.vertexIndices)
    {
        low = std::min(low, house.vertices[index].z);
        high = std::max(high, house.vertices[index].z);
    }

    CHECK(low == 640 + 256);
    CHECK(high == 640 + 512);
    CHECK(plan.doors[0].z == doctest::Approx(640.0 + 256.0));
    // One door face: the ground row and the row above the door's show no door there.
    size_t doors = 0;

    for (const Game::OutdoorBModelFace &face : house.faces)
    {
        doors += face.textureName == "t14a03" ? 1 : 0;
    }

    CHECK(doors == 1);
    const auto refused = [](const std::string &plot, const std::string &fragment)
    {
        CAPTURE(plot);
        LoweredOutdoorMap unused;
        std::vector<ProjectIssue> found;
        CHECK_FALSE(lowerOutdoorProject(buildingProject(plot), unused, found));
        CHECK(anyIssue(found, fragment));
    };
    refused("      - {building: building:home, at: [40, 40], facing: s, wall_height: 300, door: none, "
        "doors: [{wall: s, storey: 2, house: 905}]}\n", "Raise `wall_height` to 384");
    refused("      - {building: building:home, at: [40, 40], facing: s, wall_height: 600, door: none, "
        "doors: [{wall: s, storey: 0, house: 905}]}\n", "whole number from 1");
}

TEST_CASE("a hip roof with a cap is cut flat at that height, on an outline part and on a box")
{
    for (const std::string &part : {std::string("{shape: outline, outline: [[0, 128], [128, 0], [896, 0], "
             "[1024, 128], [1024, 640], [896, 768], [128, 768], [0, 640]], roof: hip, roof_height: 384, cap: 256, "
             "eaves: 0, fascia: 0}"),
             std::string("{at: [0, 0], size: [1024, 768], roof: hip, hip: 384, roof_height: 384, cap: 256, "
                 "eaves: 0, fascia: 0}")})
    {
        CAPTURE(part);
        LoweredOutdoorMap lowered = loweredBuildings("      - {building: building:home, at: [40, 40], facing: s, "
            "foundation: 0, wall_height: 256, door: none, parts: [" + part + "]}\n");
        REQUIRE(lowered.buildings.size() == 1);
        const Game::OutdoorBModel house = raiseOutdoorBuilding(lowered.buildings[0]);
        CHECK(house.maxZ == 640 + 256 + 256);
        // The flat top: one level face at the cap, a third of the depth in from every side (slope 384 over 384).
        size_t tops = 0;

        for (const Game::OutdoorBModelFace &face : house.faces)
        {
            bool level = true;
            int width = 0;
            int lowX = 1 << 30;
            int highX = -(1 << 30);

            for (const uint16_t index : face.vertexIndices)
            {
                level = level && house.vertices[index].z == 640 + 512;
                lowX = std::min(lowX, house.vertices[index].x);
                highX = std::max(highX, house.vertices[index].x);
            }

            width = highX - lowX;

            if (level)
            {
                ++tops;
                CHECK(width == doctest::Approx(1024 - 2 * 256).epsilon(0.01));
            }
        }

        CHECK(tops == 1);
    }

    LoweredOutdoorMap unused;
    std::vector<ProjectIssue> found;
    CHECK_FALSE(lowerOutdoorProject(buildingProject("      - {building: building:home, at: [40, 40], facing: s, "
        "roof: gable, cap: 100}\n"), unused, found));
    CHECK(anyIssue(found, "`cap` cuts a hip roof flat"));
}

TEST_CASE("the bridge words: an arch from a height at both ends, railings up to 512")
{
    const auto refused = [](const std::string &bridge)
    {
        std::vector<ProjectIssue> found;
        IdsLock ids;
        thingsOf("structures:\n  - {id: thing:b, kind: bridge, line: [[70, 70], [78, 70]], " + bridge + "}\n", found,
            ids);
        return anyIssue(found, "kerbs of 0 to 512");
    };
    CHECK_FALSE(refused("height: 544, rise: 96, kerb: 352"));
    CHECK(refused("height: 544, rise: 96, kerb: 600"));
    const YAML::Node structure = inlinedSketchSchema()["properties"]["structures"]["items"];
    CHECK(structure["properties"]["kerb"]["maximum"].as<double>() == 512.0);
    CHECK(structure["properties"]["cap"]["description"].IsDefined());
    CHECK(structure["properties"]["doors"]["items"]["properties"]["storey"]["description"].IsDefined());
}

// ---- Events: calendar timers, steps before the house, the screen into a map, a shared switch, a model's click ----

TEST_CASE("calendar timers run by the day or the week, as the originals' refills do; a daily one may keep an hour")
{
    const std::string more = "events:\n"
        "  - {id: evt:well_gold, trigger: weekly, effects: [{set: {var: map_var_1, value: 0}}]}\n"
        "  - {id: evt:well_might, trigger: daily, effects: [{set: {var: map_var_2, value: 0}}]}\n"
        "  - {id: evt:bell, trigger: daily, hour: 1, effects: [{text: Dong}]}\n"
        "  - {id: evt:fire, trigger: timer, every: 5, effects: [{text: Crackle}]}\n";
    const BuiltOutdoor built = builtOutdoor(buildingProject("      - {building: building:home, at: [40, 40], "
        "facing: s}\n", more), "oymap_outdoor_calendar");

    for (const ProjectIssue &issue : built.issues)
    {
        MESSAGE(issue.path << ": " << issue.message);
    }

    REQUIRE(built.built);
    CHECK(built.lua.find("triggerKind = \"long\", scheduleKind = \"weekly\" },") != std::string::npos);
    CHECK(built.lua.find("triggerKind = \"long\", scheduleKind = \"daily\" },") != std::string::npos);
    CHECK(built.lua.find("triggerKind = \"timer\", scheduleKind = \"daily\", startHour = 1, startMinute = 0, "
        "startSecond = 0 },") != std::string::npos);
    CHECK(built.lua.find("scheduleKind = \"interval\", intervalHalfMinutes = 5 },") != std::string::npos);
    // In the order of their event numbers.
    CHECK(built.lua.find("\"weekly\"") < built.lua.find("intervalHalfMinutes = 5"));
    std::vector<ProjectIssue> issues;
    IdsLock ids;
    thingsOf("events:\n  - {id: evt:a, trigger: weekly, hour: 3, effects: [{text: A}]}\n", issues, ids);
    CHECK(anyIssue(issues, "`hour` is for `trigger: daily`"));
    issues.clear();
    thingsOf("events:\n  - {id: evt:a, trigger: daily, hour: 24, effects: [{text: A}]}\n", issues, ids);
    CHECK(anyIssue(issues, "0 to 23"));
    issues.clear();
    thingsOf("events:\n  - {id: evt:a, trigger: daily, every: 5, effects: [{text: A}]}\n", issues, ids);
    CHECK(anyIssue(issues, "a load event has none"));
}

TEST_CASE("lua_before runs after the lock and before the house; into.screen shows the house's question first")
{
    const std::string house = "      - {building: building:home, at: [40, 40], facing: s, house: 899, "
        "condition: {not: {qbit: 57}}, lua_before: \"evt.ShowMovie(\\\"confluxkey\\\", true)\", lua: \"Done()\"}\n";
    const std::string more = "structures:\n"
        "  - {id: thing:crystal, kind: doorway, at: [60, 60], facing: s, title: Enter Escaton's Crystal, "
        "into: {map: d10.blv, at: [-1024, -1626, 0], facing: 520, screen: {house: 355}}}\n"
        "  - {id: thing:cove, kind: doorway, at: [70, 60], facing: s, into: {map: d08.blv, screen: {house: 351, "
        "picture: 2}}}\n";
    const BuiltOutdoor built = builtOutdoor(buildingProject(house, more), "oymap_outdoor_before");

    for (const ProjectIssue &issue : built.issues)
    {
        MESSAGE(issue.path << ": " << issue.message);
    }

    REQUIRE(built.built);
    const size_t lock = built.lua.find("IsQBitSet(QBit(57))");
    const size_t movie = built.lua.find("evt.ShowMovie(\"confluxkey\", true)");
    const size_t enter = built.lua.find("evt.EnterHouse(899)");
    const size_t done = built.lua.find("Done()");
    REQUIRE(lock != std::string::npos);
    REQUIRE(movie != std::string::npos);
    CHECK(lock < movie);
    CHECK(movie < enter);
    CHECK(enter < done);
    CHECK(built.lua.find("evt.MoveToMap(-1024, -1626, 0, 520, 0, 0, 355, 1, \"d10.blv\")") != std::string::npos);
    CHECK(built.lua.find("evt.MoveToMap(0, 0, 0, 0, 0, 0, 351, 2, \"d08.blv\")") != std::string::npos);
    std::vector<ProjectIssue> issues;
    IdsLock ids;
    thingsOf("structures:\n  - {id: thing:c, kind: doorway, at: [60, 60], facing: s, into: {map: d10.blv, "
        "screen: {house: -1}}}\n", issues, ids);
    CHECK(anyIssue(issues, "screen is `none`"));
}

TEST_CASE("F16: a way into a dungeon shows the standard entrance window unless `screen: none`")
{
    // The user (2026-11-21): the MM6-MM8 dungeon entrance window (the map's name, the stairs picture, OK and Close),
    // not a scene's own Yes/No. Left out, `screen` is {text 0, picture 1} into a .blv and nothing into an .odm.
    const std::string more = "structures:\n"
        "  - {id: thing:cave, kind: doorway, at: [60, 60], facing: s, into: {map: d10.blv, at: [1, 2, 3]}}\n"
        "  - {id: thing:hole, kind: doorway, at: [64, 60], facing: s, into: {map: d11.blv, at: [4, 5, 6], "
        "screen: none}}\n"
        "  - {id: thing:vale, kind: doorway, at: [68, 60], facing: s, into: {map: out02.odm, at: [7, 8, 9]}}\n"
        "  - {id: thing:lair, kind: doorway, at: [72, 60], facing: s, into: {map: d12.blv, at: [1, 1, 1], "
        "screen: {text: 5003}}}\n"
        "  - {id: thing:pit, kind: doorway, at: [76, 60], facing: s, into: {map: d12.blv, at: [2, 2, 2], "
        "screen: {house: 0, picture: 6}}}\n";
    const BuiltOutdoor built = builtOutdoor(buildingProject("      - {building: building:home, at: [40, 40], "
        "facing: s}\n", more), "oymap_outdoor_f16");
    REQUIRE(built.built);
    CHECK(built.lua.find("evt.MoveToMap(1, 2, 3, 0, 0, 0, 0, 1, \"d10.blv\")") != std::string::npos);
    CHECK(built.lua.find("evt.MoveToMap(4, 5, 6, 0, 0, 0, 0, 0, \"d11.blv\", {direct = true})")
        != std::string::npos);
    CHECK(built.lua.find("evt.MoveToMap(7, 8, 9, 0, 0, 0, 0, 0, \"out02.odm\")") != std::string::npos);
    CHECK(built.lua.find("evt.MoveToMap(1, 1, 1, 0, 0, 0, 5003, 1, \"d12.blv\")") != std::string::npos);
    CHECK(built.lua.find("evt.MoveToMap(2, 2, 2, 0, 0, 0, 0, 6, \"d12.blv\")") != std::string::npos);

    // A building's door into a dungeon takes the same default.
    const BuiltOutdoor door = builtOutdoor(buildingProject("      - {building: building:home, at: [40, 40], "
        "facing: s, into: {map: d05.blv, at: [10, 20, 30]}}\n"), "oymap_outdoor_f16_door");
    REQUIRE(door.built);
    CHECK(door.lua.find("evt.MoveToMap(10, 20, 30, 0, 0, 0, 0, 1, \"d05.blv\")") != std::string::npos);

    std::vector<ProjectIssue> issues;
    IdsLock ids;
    thingsOf("structures:\n  - {id: thing:c, kind: doorway, at: [60, 60], facing: s, into: {map: d10.blv, "
        "screen: {text: 3, house: 3}}}\n", issues, ids);
    CHECK(anyIssue(issues, "screen is `none`"));
    issues.clear();
    thingsOf("structures:\n  - {id: thing:c, kind: doorway, at: [60, 60], facing: s, into: {map: d10.blv, "
        "screen: {text: 3, movie: 2}}}\n", issues, ids);
    CHECK(anyIssue(issues, "not `movie`"));
}

TEST_CASE("F16: an outdoor actor carries an item into its corpse (`carries`)")
{
    const std::filesystem::path root = std::filesystem::temp_directory_path() / "oymap_outdoor_carries";
    std::filesystem::create_directories(root / "engine" / "data_tables");
    std::vector<std::string> monster(20, "0");
    monster[0] = "7";
    monster[1] = "Robber";
    monster[4] = "30";
    monster[13] = "200";
    std::string monsterLine;

    for (const std::string &cell : monster)
    {
        monsterLine += (monsterLine.empty() ? "" : "\t") + cell;
    }

    std::ofstream(root / "engine" / "data_tables" / "monster_data.txt") << "#\tName\n" << monsterLine << "\n";
    std::ofstream(root / "engine" / "data_tables" / "monster_descriptors.txt") << "#\tName\n7\tRobber\t160\t40\n";

    const auto raised = [&](const std::string &actor, std::vector<ProjectIssue> &issues)
    {
        const Project project = buildingProject("      - {building: building:home, at: [40, 40], facing: s}\n",
            "actors:\n" + actor);
        LoweredOutdoorMap lowered;
        std::vector<ProjectIssue> lowering;
        REQUIRE(lowerOutdoorProject(project, lowered, lowering));
        OutdoorThings things;
        std::vector<std::string> warnings;
        IdsLock ids;
        OutdoorEventWords words(project, {}, ids, issues);
        raiseOutdoorThings(project, lowered, root, ids, words, things, issues, warnings);
        return things;
    };

    std::vector<ProjectIssue> issues;
    const OutdoorThings things = raised("  - {monster: Robber, at: [50, 50], carries: 12152}\n", issues);
    INFO(issues.size());
    REQUIRE_EQ(things.actors.size(), 1u);
    CHECK_EQ(things.actors[0].carriedItem, 12152);
    issues.clear();
    CHECK(raised("  - {monster: Robber, at: [50, 50], carries: ring_of_keys}\n", issues).actors.empty());
    CHECK(anyIssue(issues, "`carries` is the number of the item"));
    std::error_code error;
    std::filesystem::remove_all(root, error);
}

TEST_CASE("D-90: items lie on the ground outdoors (sketch `items`), on the game's ground or `height` above it")
{
    const std::filesystem::path root = std::filesystem::temp_directory_path() / "oymap_outdoor_ground_items";
    std::filesystem::create_directories(root / "engine" / "data_tables");
    // items.txt: number, picture, name, value, equip stat ... sprite index in column 11.
    std::ofstream(root / "engine" / "data_tables" / "items.txt")
        << "Item #\tPic File\tName\tValue\tEquip Stat\n"
        << "601\tkeys2\tWarehouse Key\t0\tN / A\tMisc\t0\t0\t6\t0\tKey\t347\n"
        << "197\tgold1\tSmall pile of gold\t0\tGold\tMisc\t0\t0\t0\t0\tGold\t190\n"
        << "602\tnothing\tShadow\t0\tN / A\tMisc\t0\t0\t6\t0\tShadow\t999\n";
    // object_list.txt: the rows from 0 (the game's numbering), the object number in column 2, the sprite in 7.
    std::ofstream(root / "engine" / "data_tables" / "object_list.txt")
        << "null\tnull\t0\t32\t32\t0\t0\t0\n"
        << "key\t3KEY\t347\t64\t16\t0\t0\t17568\n"
        << "gold\tgold01\t190\t64\t16\t0\t0\t17000\n";

    std::vector<std::string> warnings;
    const auto raised = [&](const std::string &items, std::vector<ProjectIssue> &issues, LoweredOutdoorMap &lowered)
    {
        const Project project = buildingProject("      - {building: building:home, at: [40, 40], facing: s}\n",
            "structures:\n  - {id: thing:crate, kind: crate, at: [60, 60], size: 64}\nitems:\n" + items);
        std::vector<ProjectIssue> lowering;
        REQUIRE(lowerOutdoorProject(project, lowered, lowering));
        OutdoorThings things;
        warnings.clear();
        IdsLock ids;
        OutdoorEventWords words(project, {}, ids, issues);
        raiseOutdoorThings(project, lowered, root, ids, words, things, issues, warnings);
        return things;
    };

    std::vector<ProjectIssue> issues;
    LoweredOutdoorMap lowered;
    const OutdoorThings things = raised("  - {id: item:key, item: Warehouse Key, at: [50.5, 60], height: 72}\n"
        "  - {id: item:coins, item: 197, at: [52, 60], gold: 40}\n"
        "  - {id: item:on_crate, item: 601, at: [60, 60], height: 64}\n", issues, lowered);
    INFO(issues.size());
    REQUIRE(issues.empty());
    REQUIRE_EQ(things.items.size(), 3u);
    // The game lets a resting item down onto the ground or a model's top: the key 72 over bare ground is warned of
    // (a barrel is no floor), the one on the crate's top is not.
    CHECK(std::count_if(warnings.begin(), warnings.end(), [](const std::string &warning)
    {
        return warning.find("no structure's top") != std::string::npos;
    }) == 1);
    CHECK(std::any_of(warnings.begin(), warnings.end(), [](const std::string &warning)
    {
        return warning.find("item:key") != std::string::npos;
    }));
    CHECK_EQ(things.items[0].itemId, 601);
    CHECK_EQ(things.items[0].objectDescriptionId, 1);
    CHECK_EQ(things.items[0].spriteId, 17568);
    CHECK(things.items[0].position[2] == doctest::Approx(std::round(lowered.groundHeightAt(50.5, 60.0) + 72.0)));
    CHECK(things.items[0].position[0] == doctest::Approx(std::round((50.5 - OutdoorNodeCount / 2) * 512.0)));
    CHECK_EQ(things.items[1].gold, 40);
    CHECK_EQ(things.items[1].objectDescriptionId, 2);

    // Refused: an item nothing draws, a heap without its amount, gold on a key, a second id.
    for (const auto &[item, words] : std::vector<std::pair<std::string, std::string>>{
             {"  - {id: item:a, item: 602, at: [50, 50]}\n", "cannot lie on the ground"},
             {"  - {id: item:a, item: 197, at: [50, 50]}\n", "a heap of gold needs `gold`"},
             {"  - {id: item:a, item: 601, at: [50, 50], gold: 5}\n", "is no heap of gold"},
             {"  - {id: item:a, item: 601, at: [50, 50]}\n  - {id: item:a, item: 601, at: [51, 50]}\n", "of its own"}})
    {
        std::vector<ProjectIssue> refused;
        LoweredOutdoorMap land;
        raised(item, refused, land);
        INFO(item);
        CHECK(anyIssue(refused, words));
    }

    std::error_code error;
    std::filesystem::remove_all(root, error);
}

TEST_CASE("a structure follows another's switch; a model's click is on the models named, its hint on the rest")
{
    const std::string more = "structures:\n"
        "  - {id: thing:ship, kind: platform, at: [60, 60], size: [512, 512], height: 64, hidden: true}\n"
        "  - {id: thing:gangway, kind: platform, at: [62, 60], size: [256, 128], height: 32, switch: thing:ship}\n"
        "events:\n  - {id: evt:arrive, trigger: load, condition: {qbit: 10}, effects: [{show: thing:ship}]}\n";
    std::vector<ProjectIssue> issues;
    IdsLock ids;
    // As the build does: the things are raised, then every model takes the numbers events change it by.
    const Project switched = buildingProject("      - {building: building:home, at: [40, 40], facing: s}\n", more);
    LoweredOutdoorMap land;
    std::vector<ProjectIssue> lowering;
    REQUIRE(lowerOutdoorProject(switched, land, lowering));
    OutdoorEventWords switchWords(switched, {}, ids, issues);
    OutdoorThings things;
    std::vector<std::string> unusedWarnings;
    raiseOutdoorThings(switched, land, {}, ids, switchWords, things, issues, unusedWarnings);

    for (Game::OutdoorBModel &model : things.models)
    {
        switchWords.applyToModel(model.name, model);
    }

    CHECK(issues.empty());
    const Game::OutdoorBModel *pShip = nullptr;
    const Game::OutdoorBModel *pGangway = nullptr;

    for (const Game::OutdoorBModel &model : things.models)
    {
        pShip = model.name == "thing:ship" ? &model : pShip;
        pGangway = model.name == "thing:gangway" ? &model : pGangway;
    }

    REQUIRE(pShip != nullptr);
    REQUIRE(pGangway != nullptr);
    const uint32_t hidden = Game::faceAttributeBit(Game::FaceAttribute::Invisible);

    for (const Game::OutdoorBModelFace &face : pGangway->faces)
    {
        CHECK(face.cogNumber == pShip->faces[0].cogNumber);
        CHECK((face.attributes & hidden) != 0);
    }

    CHECK(pShip->faces[0].cogNumber != 0);
    issues.clear();
    thingsOf("structures:\n  - {id: thing:a, kind: platform, at: [60, 60], size: [256, 256], height: 32, "
        "switch: thing:a}\n", issues, ids);
    CHECK(anyIssue(issues, "`switch` names the structure"));
    issues.clear();
    thingsOf("structures:\n  - {id: thing:a, kind: platform, at: [60, 60], size: [256, 256], height: 32, "
        "switch: thing:nothing}\n", issues, ids);
    CHECK(anyIssue(issues, "`switch` names the structure"));

    // A model taken in two pieces: the door runs the click, the hull says the hint.
    const std::filesystem::path root = std::filesystem::temp_directory_path() / "oymap_outdoor_click_root";
    std::error_code error;
    std::filesystem::create_directories(root / "worlds" / "mm8" / "maps", error);
    Game::OutdoorMapData source = testMap();
    source.decorationMap.assign(Side * Side, 0);
    source.bmodels = {testHouse(1000, 2000, 512, 256, 100, 300, 44), testHouse(1512, 2000, 128, 64, 100, 200, 45)};
    source.bmodels[0].name = "Crystal";
    source.bmodels[1].name = "Crystal_Door";

    for (Game::OutdoorBModel &model : source.bmodels)
    {
        for (Game::OutdoorBModelFace &face : model.faces)
        {
            face.textureName = "t06b01";
            face.textureUs.assign(face.vertexIndices.size(), 0);
            face.textureVs.assign(face.vertexIndices.size(), 0);
            face.planeNormalZ = 65536;
        }
    }

    const std::optional<std::vector<uint8_t>> bytes = Game::OutdoorMapDataWriter().buildBytes(source);
    REQUIRE(bytes);
    std::string writeError;
    REQUIRE(writeBinaryFileAtomically(root / "worlds" / "mm8" / "maps" / "src.odm", *bytes, writeError));
    const auto raised = [&root](const std::string &structures, std::vector<ProjectIssue> &found)
    {
        const Project project = buildingProject("      - {building: building:home, at: [40, 40], facing: s}\n",
            "structures:\n" + structures);
        LoweredOutdoorMap lowered;
        std::vector<ProjectIssue> lowering;
        REQUIRE(lowerOutdoorProject(project, lowered, lowering));
        IdsLock lock;
        OutdoorEventWords words(project, root, lock, found);
        OutdoorThings raisedThings;
        std::vector<std::string> warnings;
        raiseOutdoorThings(project, lowered, root, lock, words, raisedThings, found, warnings);
        return raisedThings;
    };
    issues.clear();
    const OutdoorThings crystal = raised("  - {id: thing:crystal, kind: model, from: {map: src.odm, models: [Crystal, "
        "Crystal_Door]}, click: [crystal_door], title: Enter Escaton's Crystal, hint: Escaton's Crystal, "
        "into: {map: d10.blv}}\n", issues);
    CHECK(issues.empty());
    REQUIRE(crystal.models.size() == 1);
    const OutdoorEventPlan *pEnter = eventOf(crystal, "evt:thing:crystal");
    const OutdoorEventPlan *pHint = eventOf(crystal, "evt:hint:thing:crystal");
    REQUIRE(pEnter != nullptr);
    REQUIRE(pHint != nullptr);
    CHECK(pHint->title == "Escaton's Crystal");
    // The hull's six faces first, then the door's six.
    REQUIRE(crystal.models[0].faces.size() == 12);

    for (size_t face = 0; face < 12; ++face)
    {
        CHECK(crystal.models[0].faces[face].cogTriggeredNumber == (face < 6 ? pHint->number : pEnter->number));
    }

    issues.clear();
    raised("  - {id: thing:crystal, kind: model, from: {map: src.odm, models: [Crystal]}, title: A, hint: B}\n",
        issues);
    CHECK(anyIssue(issues, "say which of its models run the click with `click"));
    issues.clear();
    raised("  - {id: thing:crystal, kind: model, from: {map: src.odm, models: [Crystal]}, click: [Crystal_Door], "
        "title: A}\n", issues);
    CHECK(anyIssue(issues, "is none of those taken"));
}

TEST_CASE("the event words of this batch are in the sketch schema, described")
{
    const YAML::Node root = inlinedSketchSchema();
    const YAML::Node structure = root["properties"]["structures"]["items"]["properties"];
    CHECK(structure["click"]["description"].IsDefined());
    CHECK(structure["switch"]["description"].IsDefined());
    CHECK(structure["lua_before"]["description"].IsDefined());
    CHECK(structure["into"]["properties"]["screen"]["description"].IsDefined());
    const YAML::Node events = root["properties"]["events"]["items"]["properties"];
    CHECK(events["hour"]["description"].IsDefined());
    CHECK(events["trigger"]["enum"].size() == 5);
}

// ---- The measure: centres from corners, upright faces' tops where they stand, markers, empty events ----

TEST_CASE("a model with no pixel of its own stands at the middle of its corners, not at the centre it stores")
{
    Game::OutdoorMapData original = testMap();
    // A small box inside a larger one: the larger covers every pixel of the small one.
    original.bmodels.push_back(testHouse(1152, 1152, 256, 256, 320, 256, 0));
    original.bmodels.push_back(testHouse(1024, 1024, 512, 512, 320, 300, 0));
    original.bmodels[0].name = "wagon";
    original.bmodels[0].boundingCenterX = 0;
    original.bmodels[0].boundingCenterY = -5187;
    const OutdoorCompareResult result = compared(original, testMap());
    bool found = false;

    for (const OutdoorCompareBuilding &building : result.buildings)
    {
        if (building.name == "wagon")
        {
            found = true;
            CHECK(building.x == doctest::Approx(1024 + 256));
            CHECK(building.y == doctest::Approx(1024 + 256));
        }
    }

    CHECK(found);
}

TEST_CASE("an upright face is as high as its top edge where it stands: a railing over an arch is not level")
{
    // A wall 8 cells long whose top rises from 400 at its west end to 1200 at its east end, and a wall as long whose
    // top is level at 1200: alike only at the east end.
    const auto wall = [](int eastTop)
    {
        Game::OutdoorMapData map = testMap();
        Game::OutdoorBModel model;
        model.name = "railing";
        model.vertices = {{0, 4096, 320}, {4096, 4096, 320}, {4096, 4096, eastTop}, {0, 4096, 400}};

        if (eastTop == 400)
        {
            model.vertices[3].z = 1200;
            model.vertices[2].z = 1200;
        }

        Game::OutdoorBModelFace face;
        face.vertexIndices = {0, 1, 2, 3};
        face.textureName = "t06b01";
        face.polygonType = 1;
        model.faces.push_back(face);
        map.bmodels.push_back(model);
        return map;
    };
    const Game::OutdoorMapData rising = wall(1200);
    const Game::OutdoorMapData level = wall(400);
    CHECK(partOf(compared(rising, rising), "buildings") == doctest::Approx(1.0));
    // Their footprints are the same line; only the tops differ, and only toward the west.
    const OutdoorCompareResult result = compared(rising, level);
    CHECK(partOf(result, "buildings") < 1.0);
    CHECK(partOf(result, "buildings") > 0.6);
}

TEST_CASE("party starts are markers, not decorations; an empty event is no thing; the unpaired are named")
{
    Game::OutdoorMapData original = testMap();
    Game::OutdoorEntity start = testDecoration("", 1000, 1000);
    start.decorationListId = 13;
    original.entities.push_back(start);
    original.entities.push_back(testDecoration("tree12", 5000, 5000));
    Game::OutdoorMapData rebuilt = testMap();
    rebuilt.entities.push_back(testDecoration("tree12", 5100, 5000));
    rebuilt.entities.push_back(testDecoration("rock01", -9000, -9000));
    const OutdoorCompareResult result = compared(original, rebuilt);
    CHECK(result.originalDecorations == 1);
    REQUIRE(result.unpairedRebuiltDecorations.size() == 1);
    CHECK(result.unpairedRebuiltDecorations[0].what == "rock01");
    CHECK(result.unpairedOriginalDecorations.empty());
    JsonWriter writer(true);
    writeOutdoorDifferencesJson(result, writer);
    CHECK(writer.take().find("\"decorations_only_in_rebuilt\"") != std::string::npos);
    // A model carrying an event whose handler has no title and does nothing.
    Game::OutdoorMapData ship = testMap();
    ship.bmodels.push_back(testHouse(1024, 1024, 512, 512, 320, 256, 184));
    OutdoorCompareSide quiet = sideOf(ship, "ship");
    quiet.emptyEvents = outdoorEmptyEvents("[{\"event\":184,\"title\":\"\",\"paths\":[{\"tests\":[],"
        "\"effects\":[]}],\"truncated\":false},\n{\"event\":171,\"title\":\"\",\"paths\":[{\"tests\":[],"
        "\"effects\":[\"EnterHouse(2)\"]}]}]");
    CHECK(quiet.emptyEvents == std::set<int>{184});
    OutdoorCompareResult counted;
    std::string errorMessage;
    REQUIRE(compareOutdoorMaps(quiet, sideOf(ship, "ship"), counted, errorMessage));
    CHECK(counted.originalEvents == 0);
    CHECK(counted.rebuiltEvents == 1);
}

// ---- Outdoor batch six: the hidden slope over steps ----

namespace
{
const uint32_t InvisibleBit = Game::faceAttributeBit(Game::FaceAttribute::Invisible);
const uint32_t UntouchableBit = Game::faceAttributeBit(Game::FaceAttribute::Untouchable);

// The lowest and highest corner of a face, and its corners' x.
std::array<int, 2> heightsOf(const Game::OutdoorBModel &model, const Game::OutdoorBModelFace &face)
{
    std::array<int, 2> heights = {1 << 30, -(1 << 30)};

    for (const uint16_t index : face.vertexIndices)
    {
        heights = {std::min(heights[0], model.vertices[index].z), std::max(heights[1], model.vertices[index].z)};
    }

    return heights;
}
}

TEST_CASE("a flight of steps has the hidden slope the shipped maps walk up, and its risers let the party through")
{
    std::vector<ProjectIssue> issues;
    IdsLock ids;
    const OutdoorThings things = thingsOf("structures:\n"
        "  - {id: thing:flight, kind: stairs, line: [[50, 50], [52, 50]], rise: 256, tread: 32, width: 256}\n",
        issues, ids);
    REQUIRE(issues.empty());
    REQUIRE(things.models.size() == 1);
    const Game::OutdoorBModel &flight = things.models[0];
    std::vector<const Game::OutdoorBModelFace *> slopes;
    size_t risers = 0;

    for (const Game::OutdoorBModelFace &face : flight.faces)
    {
        if ((face.attributes & InvisibleBit) != 0)
        {
            slopes.push_back(&face);
        }

        if ((face.attributes & UntouchableBit) != 0)
        {
            // Only the risers: upright, looking down the flight (west), the way the party comes.
            ++risers;
            CHECK(face.polygonType == 1);
            CHECK(face.planeNormalX == -65536);
        }
    }

    CHECK(risers == 8);
    REQUIRE(slopes.size() == 1);
    const Game::OutdoorBModelFace &slope = *slopes[0];
    // Between floor and wall, walked on, from the ground at the foot to the top: 256 over 1024.
    CHECK(slope.polygonType == 4);
    CHECK((slope.attributes & UntouchableBit) == 0);
    CHECK(slope.planeNormalZ == std::lround(1024.0 / std::hypot(1024.0, 256.0) * 65536.0));
    CHECK(heightsOf(flight, slope) == std::array<int, 2>{640, 640 + 256});

    // It runs through the foot of every riser: each tread's back edge lies on it.
    int west = 1 << 30;

    for (const uint16_t index : slope.vertexIndices)
    {
        west = std::min(west, flight.vertices[index].x);
    }

    for (const Game::OutdoorBModelFace &face : flight.faces)
    {
        if (face.polygonType == 3)
        {
            int east = -(1 << 30);

            for (const uint16_t index : face.vertexIndices)
            {
                east = std::max(east, flight.vertices[index].x);
            }

            CHECK(heightsOf(flight, face)[0] == doctest::Approx(640.0 + (east - west) * 0.25).epsilon(0.01));
        }
    }

    const auto refused = [](const std::string &structure)
    {
        std::vector<ProjectIssue> found;
        IdsLock lock;
        thingsOf("structures:\n" + structure, found, lock);
        return found;
    };
    // 512 up over 384: the game slides the party down a slope that steep and that high.
    CHECK(anyIssue(refused("  - {id: thing:s, kind: stairs, line: [[50, 50], [50.75, 50]], rise: 512}\n"),
        "the party cannot walk up a flight"));
    // A short flight may be steep: below 128 the game walks any slope (96 up over 64).
    CHECK(refused("  - {id: thing:s, kind: stairs, line: [[50, 50], [50.125, 50]], rise: 96}\n").empty());
    CHECK(outdoorSlopeWalkable(127.0, 1.0));
    CHECK_FALSE(outdoorSlopeWalkable(128.0, 128.0));
    CHECK(outdoorSlopeWalkable(128.0, 129.0));
}

TEST_CASE("a part that is climbed: a dais of two rings gets a slope over every wall, its walls let the party through")
{
    LoweredOutdoorMap lowered = loweredBuildings("      - {building: building:home, at: [40, 40], facing: s, "
        "foundation: 0, door: none, windows: none, eaves: 0, fascia: 0, roof: flat, parts: ["
        "{id: step, shape: round, at: [512, 384], radius: 416, sides: 8, wall_height: 32, climb: 40}, "
        "{id: dais, shape: round, at: [512, 384], radius: 372, sides: 8, wall_height: 64, climb: 40}, "
        "{id: post, at: [480, 352], size: [64, 64], wall_height: 256}]}\n");
    REQUIRE(lowered.buildings.size() == 1);
    REQUIRE(lowered.buildings[0].parts[0].climbFrom.size() == 8);
    // The ring's walls stand on the ground, the dais's on the ring's top; the post's are not climbed.
    CHECK(*lowered.buildings[0].parts[0].climbFrom[3] == 0.0);
    CHECK(*lowered.buildings[0].parts[1].climbFrom[3] == 32.0);
    CHECK(lowered.buildings[0].parts[2].climbFrom.empty());
    const Game::OutdoorBModel dais = raiseOutdoorBuilding(lowered.buildings[0]);
    std::map<std::array<int, 2>, size_t> slopes;
    size_t risers = 0;

    for (const Game::OutdoorBModelFace &face : dais.faces)
    {
        const std::array<int, 2> heights = heightsOf(dais, face);

        if ((face.attributes & InvisibleBit) != 0)
        {
            ++slopes[heights];
            CHECK(face.polygonType == 4);
            // 32 up over 40 in, as Harmondale's fort's flights (normal 51175).
            CHECK(face.planeNormalZ == doctest::Approx(51175).epsilon(0.01));
        }

        // Every wall of the two rings lets the party through; the post's walls (to 896) stop it.
        if (face.polygonType == 1)
        {
            CHECK(((face.attributes & UntouchableBit) != 0) == (heights[1] <= 640 + 64));
            risers += (face.attributes & UntouchableBit) != 0 ? 1 : 0;
        }
    }

    CHECK(slopes == std::map<std::array<int, 2>, size_t>{{{640, 672}, 8}, {{672, 704}, 8}});
    CHECK(risers >= 16);

    const auto refused = [](const std::string &parts)
    {
        LoweredOutdoorMap unused;
        std::vector<ProjectIssue> found;
        lowerOutdoorProject(buildingProject("      - {building: building:home, at: [40, 40], facing: s, "
            "foundation: 0, door: none, eaves: 0, fascia: 0, roof: flat, parts: [" + parts + "]}\n"), unused, found);
        return found;
    };
    CHECK(anyIssue(refused("{wall_height: 32, roof: hip, climb: 40}"), "a flat top to stand on"));
    CHECK(anyIssue(refused("{wall_height: 128, climb: 40}"), "at most 64 high"));
    CHECK(anyIssue(refused("{shape: round, radius: 64, wall_height: 32, climb: 80}"), "past the middle"));
    CHECK(anyIssue(refused("{wall_height: 32, climb: 8}"), "16 to 512"));
    CHECK(anyIssue(refused("{wall_height: 64}, {at: [256, 256], size: [256, 256], wall_height: 32, climb: 40}"),
        "nothing to climb"));
    CHECK(refused("{wall_height: 32, climb: 40}").empty());
}

TEST_CASE("the climbing words are in the sketch schema, described")
{
    const YAML::Node root = inlinedSketchSchema();
    const YAML::Node structure = root["properties"]["structures"]["items"]["properties"];
    CHECK(structure["parts"]["items"]["properties"]["climb"]["description"].IsDefined());
    CHECK(structure["tread"]["description"].as<std::string>().find("hidden slope") != std::string::npos);
    const YAML::Node plot = root["properties"]["districts"]["items"]["properties"]["plots"]["items"]["properties"];
    CHECK(plot["parts"]["items"]["properties"]["climb"]["description"].IsDefined());
}

TEST_CASE("an upper door takes its bay's own texture, stands on the band, and bays may have widths of their own")
{
    // Ravenshore's north-east block: the upper row begins at 288 over a band of 32, and the locked door is t14a03
    // between two panels 64 wide, on a stone house whose kit door is t14c03.
    LoweredOutdoorMap lowered = loweredBuildings("      - {building: building:home, at: [40, 40], facing: s, "
        "foundation: 0, kit: stone, door: none, parts: [{id: p3, size: [1024, 384], wall_height: 544, band: 32, "
        "textures: {band: t14d01}, upper_walls: {s: [t14a07, t14a04a, [t14a01, 64], [t14a03, 128], "
        "[t14a01, 64], t14a04a, t14a04a, t14a04a, t14a06]}}], doors: [{part: p3, wall: s, bay: 3, storey: 2, "
        "house: 905}]}\n");
    REQUIRE(lowered.buildings.size() == 1);
    OutdoorBuildingPlan &plan = lowered.buildings[0];
    REQUIRE(plan.doors.size() == 1);
    CHECK(plan.doors[0].texture == "t14a03");
    plan.doors[0].event = 7;
    const Game::OutdoorBModel house = raiseOutdoorBuilding(plan);
    REQUIRE(plan.doors[0].face >= 0);
    const Game::OutdoorBModelFace &door = house.faces[plan.doors[0].face];
    CHECK(door.textureName == "t14a03");
    CHECK(heightsOf(house, door) == std::array<int, 2>{640 + 288, 640 + 544});
    // 256 in from the wall's west end (two bays of 128 and one of 64), 128 wide.
    int west = 1 << 30;
    int east = -(1 << 30);
    int wallWest = 1 << 30;

    for (const uint16_t index : door.vertexIndices)
    {
        west = std::min(west, house.vertices[index].x);
        east = std::max(east, house.vertices[index].x);
    }

    for (const std::array<double, 2> &corner : plan.parts[0].outline)
    {
        wallWest = std::min(wallWest, static_cast<int>(std::lround(corner[0])));
    }

    CHECK(west - wallWest == 320);
    CHECK(east - west == 128);
    // The band: one face along each wall from 256 to 288, in its own texture.
    size_t bands = 0;

    for (const Game::OutdoorBModelFace &face : house.faces)
    {
        if (face.textureName == "t14d01")
        {
            ++bands;
            CHECK(heightsOf(house, face) == std::array<int, 2>{640 + 256, 640 + 288});
        }
    }

    CHECK(bands == 4);
    const auto refused = [](const std::string &part, const std::string &fragment)
    {
        CAPTURE(part);
        LoweredOutdoorMap unused;
        std::vector<ProjectIssue> found;
        CHECK_FALSE(lowerOutdoorProject(buildingProject("      - {building: building:home, at: [40, 40], facing: s, "
            "door: none, parts: [" + part + "]}\n"), unused, found));
        CHECK(anyIssue(found, fragment));
    };
    refused("{size: [512, 384], walls: {s: [wall, [door, 600], wall]}}", "[word, width]");
    refused("{size: [512, 384], walls: {s: [wall, [door, 128], [wall, 128]]}}", "which leaves 256 to 1 bays");
    refused("{size: [512, 384], walls: {s: [[wall, 128], [door, 128], [wall, 128]]}}", "no bay is left");
    refused("{size: [512, 384], band: 200}", "0 to 128");
}

TEST_CASE("the band and bay widths are in the sketch schema, described")
{
    const YAML::Node root = inlinedSketchSchema();
    const YAML::Node part = root["properties"]["structures"]["items"]["properties"]["parts"]["items"]["properties"];
    CHECK(part["band"]["description"].IsDefined());
    CHECK(part["walls"]["description"].as<std::string>().find("[word, width]") != std::string::npos);
    CHECK(part["upper_walls"]["additionalProperties"]["items"]["oneOf"].IsSequence());
}

TEST_CASE("the measure: a building cut into several models in either map is one building, paired by footprint")
{
    // The fort's ring: one model of four pieces in the original, four walls in the rebuild; and the other way round
    // (a castle of four models against one plot).
    Game::OutdoorBModel ring;
    ring.name = "ring";
    std::vector<Game::OutdoorBModel> walls;

    for (int piece = 0; piece < 4; ++piece)
    {
        Game::OutdoorBModel wall = testHouse(piece * 2048, 0, 1024, 1024, 320, 256, 0);
        wall.name = "wall" + std::to_string(piece);
        const uint16_t offset = static_cast<uint16_t>(ring.vertices.size());
        ring.vertices.insert(ring.vertices.end(), wall.vertices.begin(), wall.vertices.end());

        for (Game::OutdoorBModelFace face : wall.faces)
        {
            for (uint16_t &index : face.vertexIndices)
            {
                index = static_cast<uint16_t>(index + offset);
            }

            ring.faces.push_back(face);
        }

        walls.push_back(wall);
    }

    Game::OutdoorMapData whole = testMap();
    whole.bmodels.push_back(ring);
    Game::OutdoorMapData pieces = testMap();
    pieces.bmodels = walls;
    const OutdoorCompareResult cut = compared(whole, pieces);
    REQUIRE(cut.buildings.size() == 1);
    CHECK(cut.buildings[0].original == 0);
    CHECK(cut.buildings[0].rebuiltModels.size() == 4);
    CHECK(cut.buildings[0].overlap == doctest::Approx(1.0));
    CHECK(cut.matchedBuildings == 1);
    JsonWriter writer(true);
    writeOutdoorDifferencesJson(cut, writer);
    const std::string json = writer.take();
    CHECK(json.find("\"models_rebuilt\"") != std::string::npos);
    CHECK(json.find("only in the rebuild") == std::string::npos);
    const OutdoorCompareResult joined = compared(pieces, whole);
    REQUIRE(joined.buildings.size() == 1);
    CHECK(joined.buildings[0].originalModels.size() == 4);
    CHECK(joined.matchedBuildings == 4);
    // Models that share less than half of the smaller one still pair one to one, as before.
    Game::OutdoorMapData shifted = testMap();
    shifted.bmodels.push_back(testHouse(700, 0, 1024, 1024, 320, 256, 0));
    Game::OutdoorMapData single = testMap();
    single.bmodels.push_back(testHouse(0, 0, 1024, 1024, 320, 256, 0));
    const OutdoorCompareResult loose = compared(single, shifted);
    REQUIRE(loose.buildings.size() == 1);
    CHECK(loose.buildings[0].rebuilt == 0);
    CHECK(loose.buildings[0].overlap < 0.5);
}

TEST_CASE("the rim's eyes stand inside the square: a node beside the edge does not decide every sight line")
{
    // Ravenshore's B5: rebuilt nodes just beyond the square's west edge 400 over the original's, along 20 cells.
    const Game::OutdoorMapData flat = ridgedMap(0, 0);
    Game::OutdoorMapData bump = ridgedMap(0, 0);

    for (int row = 60; row <= 80; ++row)
    {
        bump.heightMap[static_cast<size_t>(row) * Side + 18] = static_cast<uint8_t>(10 + 400 / 32);
    }

    const OutdoorCompareResult bumped = compared(flat, bump);
    checkOnlyTheseDiffer(bumped, {"rim"});
    // Eyes on the edge itself read 0.88 here.
    CHECK(partOf(bumped, "rim") > 0.9);
}

TEST_CASE("ground along a line: a strip of whole cells along a dyke; one node alone the tiles cannot show")
{
    const LoweredOutdoorMap strip = loweredOf(std::string(LevelLand) + "ground:\n"
        "  - {material: grass, line: [[40, 60], [80, 60]], width: 2}\n"
        "  - {material: grass, line: [[40, 40], [60, 60]], width: 3}\n"
        "  - {material: grass, line: [[90, 20], [90, 40]]}\n");
    // Two nodes across, the second on the line's left (north of a line drawn east): one row of grass cells, the
    // rows either side grass toward dirt.
    CHECK(tileAt(strip, 60, 59) >= 90);
    CHECK(tileAt(strip, 60, 59) < 102);
    CHECK(tileAt(strip, 60, 60) >= 102);
    CHECK(tileAt(strip, 60, 60) < 126);
    CHECK(tileAt(strip, 60, 58) >= 102);
    CHECK(tileAt(strip, 60, 58) < 126);
    // Three across a diagonal: whole cells along it.
    CHECK(tileAt(strip, 50, 50) >= 90);
    CHECK(tileAt(strip, 50, 50) < 102);
    // One line of corners alone: no tile shows it, so it is cleared.
    CHECK(tileAt(strip, 90, 30) <= 12);

    const std::string whole = "polygon: [[0, 0], [128, 0], [128, 128], [0, 128]]";
    CHECK(anyIssue(refusedWith(std::string(LevelLand) + "ground:\n  - {material: grass, " + whole
        + ", line: [[1, 1], [2, 2]]}\n"), "one of the two"));
    CHECK(anyIssue(refusedWith(std::string(LevelLand) + "ground:\n  - {material: grass, line: [[1, 1], [9, 1]], "
        "width: 1.5}\n"), "a whole number from 1 to 8"));
    CHECK(anyIssue(refusedWith(std::string(LevelLand) + "ground:\n  - {material: grass, line: [[1, 1]]}\n"),
        "at least two"));
}

TEST_CASE("heights.ridges two nodes wide on a diagonal: the second node across, never the floor beside it")
{
    const LoweredOutdoorMap plain = loweredOf(LevelLand);
    const LoweredOutdoorMap ridged = loweredOf(std::string(LevelLand) + "  ridges:\n"
        "    - {line: [[40, 40], [60, 60]], height: 1280, width: 2}\n"
        "    - {line: [[40, 80], [80, 80]], height: 1280, width: 2}\n");
    // Drawn south-east: its nodes and the node north of each (its left), not the one south.
    CHECK(sampleAt(ridged, 50, 50) * 32 == 1280);
    CHECK(sampleAt(ridged, 50, 49) * 32 == 1280);
    CHECK(sampleAt(ridged, 50, 51) == sampleAt(plain, 50, 51));
    CHECK(sampleAt(ridged, 49, 50) == sampleAt(plain, 49, 50));
    // Drawn east: two rows, the line's and the one north of it.
    CHECK(sampleAt(ridged, 60, 80) * 32 == 1280);
    CHECK(sampleAt(ridged, 60, 79) * 32 == 1280);
    CHECK(sampleAt(ridged, 60, 81) == sampleAt(plain, 60, 81));
    CHECK(sampleAt(ridged, 60, 78) == sampleAt(plain, 60, 78));
    // The ground line of the same width lays the same nodes.
    for (int x = 41; x < 60; ++x)
    {
        for (int y = 38; y <= 62; ++y)
        {
            size_t segment = 0;
            double share = 0.0;
            double beyond = 0.0;
            const std::vector<std::array<double, 2>> line = {{40.0, 40.0}, {60.0, 60.0}};
            CHECK(outdoorNodeOnLine(line, 2.0, x, y, segment, share, beyond)
                == (sampleAt(ridged, x, y) * 32 == 1280));
        }
    }
}

TEST_CASE("the ground line's words are in the sketch schema, described")
{
    const YAML::Node ground = inlinedSketchSchema()["properties"]["ground"]["items"];
    CHECK(ground["properties"]["line"]["description"].IsDefined());
    CHECK(ground["properties"]["width"]["description"].IsDefined());
    CHECK(ground["required"].size() == 1);
}

TEST_CASE("scatter with an id: events change all its decorations at once, as the shipped maps' seasonal forests")
{
    const std::filesystem::path root = std::filesystem::temp_directory_path() / "oymap_outdoor_scatter_id_root";
    std::error_code error;
    std::filesystem::create_directories(root / "engine" / "data_tables", error);
    {
        std::ofstream decorations(root / "engine" / "data_tables" / "decoration_data.txt");
        decorations << "#\tName\n13\tparty start\n101\ttree12\n102\ttree37\n103\tplant32\n";
    }
    const std::string more =
        "structures:\n"
        "  - {id: thing:bell, kind: platform, at: [60, 60], size: [128, 128], title: Bell, "
        "effects: [{set_sprite: {of: scatter:forest, to: tree37}}, {hide: scatter:flowers}]}\n"
        "scatter:\n"
        "  - {id: scatter:forest, decoration: tree12, count: 10, polygon: [[30, 30], [38, 30], [38, 38], [30, 38]]}\n"
        "  - {id: scatter:forest, decoration: tree12, count: 10, polygon: [[70, 30], [78, 30], [78, 38], [70, 38]]}\n"
        "  - {id: scatter:flowers, decoration: plant32, count: 5, circle: {at: [90, 90], r: 3}}\n"
        "  - {decoration: tree12, count: 5, circle: {at: [100, 100], r: 3}}\n";
    const Project project = buildingProject("      - {building: building:home, at: [40, 40], facing: s}\n", more);
    LoweredOutdoorMap lowered;
    std::vector<ProjectIssue> issues;
    REQUIRE(lowerOutdoorProject(project, lowered, issues));
    IdsLock ids;
    OutdoorEventWords words(project, root, ids, issues);
    OutdoorThings things;
    std::vector<std::string> warnings;
    REQUIRE(raiseOutdoorThings(project, lowered, root, ids, words, things, issues, warnings));
    CHECK(issues.empty());
    const int forest = words.decorationNumber("scatter:forest");
    const int flowers = words.decorationNumber("scatter:flowers");
    CHECK(forest >= 30000);
    CHECK(flowers >= 30000);
    CHECK(forest != flowers);
    const OutdoorEventPlan *pBell = eventOf(things, "evt:thing:bell");
    REQUIRE(pBell != nullptr);
    CHECK(pBell->body == std::vector<std::string>{"evt.SetSprite(" + std::to_string(forest) + ", 1, \"tree37\")",
        "evt.SetSprite(" + std::to_string(flowers) + ", 0)"});
    std::string table;
    REQUIRE(readTextFile(root / "engine" / "data_tables" / "decoration_data.txt", table));
    OutdoorPlaces places;
    REQUIRE(placeOutdoorThings(project, lowered, table, places, issues, warnings));
    REQUIRE(places.decorations.size() == 30);
    // Both forest entries carry the one id; the entry without one carries none.
    CHECK(std::count_if(places.decorations.begin(), places.decorations.end(),
        [](const OutdoorPlacedDecoration &decoration)
        {
            return decoration.target == "scatter:forest";
        }) == 20);
    CHECK(places.decorations.back().target.empty());

    // An id that is a structure's is refused.
    const Project clash = buildingProject("      - {building: building:home, at: [40, 40], facing: s}\n",
        "structures:\n  - {id: thing:grove, kind: decoration, decoration: tree12, at: [50, 50]}\n"
        "scatter:\n  - {id: thing:grove, decoration: tree12, count: 3, circle: {at: [90, 90], r: 3}}\n");
    std::vector<ProjectIssue> found;
    IdsLock clashIds;
    OutdoorEventWords clashWords(clash, root, clashIds, found);
    CHECK(anyIssue(found, "is already the id of structures[0]"));
    const YAML::Node scatter = inlinedSketchSchema()["properties"]["scatter"]["items"];
    CHECK(scatter["properties"]["id"]["description"].IsDefined());
}

TEST_CASE("a sign that hangs has no post; a blank thing carries an event with no title and no handler")
{
    std::vector<ProjectIssue> issues;
    IdsLock ids;
    // Harmondale's gate sign: a board 192 by 80 whose top is 592 up, under the arch over the east road.
    const OutdoorThings things = thingsOf("structures:\n"
        "  - {id: thing:gate_sign, kind: sign, at: [60, 60], turn: 90, hang: true, height: 592, board_height: 80, "
        "width: 192, blank: true, textures: {board: hhr1bwall, wall: trim11_32}}\n", issues, ids);
    REQUIRE(issues.empty());
    REQUIRE(things.models.size() == 1);
    const Game::OutdoorBModel &sign = things.models[0];
    CHECK(sign.minZ == 640 + 592 - 80);
    CHECK(sign.maxZ == 640 + 592);
    const int number = IdsLock::number(ids.events, "evt:thing:gate_sign", 1);
    CHECK(number > 0);
    CHECK(std::all_of(sign.faces.begin(), sign.faces.end(), [number](const Game::OutdoorBModelFace &face)
    {
        return face.cogTriggeredNumber == number;
    }));
    // No handler: the event is a number on the faces and nothing more.
    CHECK(std::none_of(things.events.begin(), things.events.end(), [number](const OutdoorEventPlan &event)
    {
        return event.number == number;
    }));

    const auto refused = [](const std::string &structure, const std::string &fragment)
    {
        CAPTURE(structure);
        std::vector<ProjectIssue> found;
        IdsLock lock;
        thingsOf("structures:\n  - {id: thing:s, kind: sign, at: [60, 60], " + structure + "}\n", found, lock);
        CHECK(anyIssue(found, fragment));
    };
    refused("blank: true, title: Harmondale", "has no title and does nothing");
    refused("hang: true, arms: [{toward: n, title: North}]", "without a post");
    refused("board_height: 300", "16 to 256");
    const YAML::Node structure = inlinedSketchSchema()["properties"]["structures"]["items"];
    for (const char *pWord : {"hang", "board_height", "blank"})
    {
        CHECK(structure["properties"][pWord]["description"].IsDefined());
    }
}

TEST_CASE("the measure: an event with neither a handler nor a name is no thing; a name alone is one")
{
    // Harmondale's gate sign carries event 1, `RegisterEvent(1, nil, nil)`; Ravenshore's ship carries 184,
    // `RegisterEvent(184, "The Dauntless", nil, ...)`, a name without a handler.
    Game::OutdoorMapData town = testMap();
    town.bmodels.push_back(testHouse(1024, 1024, 512, 512, 320, 256, 1));
    town.bmodels.push_back(testHouse(8192, 8192, 512, 512, 320, 256, 184));
    OutdoorCompareSide read = sideOf(town, "town");
    read.eventsRead = true;
    read.namedEvents = {184};
    CHECK(outdoorFlowEvents("[{\"event\":3,\"title\":\"\"},\n{\"event\":17,\"title\":\"A\"}]") == std::set<int>{3, 17});
    OutdoorCompareResult counted;
    std::string errorMessage;
    REQUIRE(compareOutdoorMaps(read, read, counted, errorMessage));
    CHECK(counted.originalEvents == 1);
    // Unread (no script at hand): every event on things counts, as before.
    REQUIRE(compareOutdoorMaps(sideOf(town, "town"), sideOf(town, "town"), counted, errorMessage));
    CHECK(counted.originalEvents == 2);
}

#include "core/OutdoorInteractive.h"

TEST_CASE("outdoor batch seven's tool defects: things outdoors, a word of another shape, scatter by its own words")
{
    // `oymap things` on an outdoor map: a house's door enters it, its walls say its name, a chest opens.
    LoadedMap map;
    map.outdoor = testMap();
    map.outdoor->bmodels.push_back(testHouse(1024, 1024, 512, 512, 320, 256, 3));
    map.outdoor->bmodels.back().faces[3].cogTriggeredNumber = 4;
    map.outdoor->bmodels.push_back(testHouse(8192, 8192, 96, 64, 320, 80, 9));
    map.outdoor->bmodels.back().name = "chest";
    std::map<int, std::string> modelNames;
    const std::vector<InteractiveThing> listed = listOutdoorInteractiveThings(map,
        "[{\"event\": 3, \"title\": \"Tempered Steel\", \"paths\": [{\"effects\": [\"EnterHouse(9)\"]}]},"
        "{\"event\": 4, \"title\": \"Tempered Steel\", \"paths\": [{\"effects\": []}]},"
        "{\"event\": 9, \"title\": \"Chest\", \"paths\": [{\"effects\": [\"open chest 2\"]}]}]", modelNames);
    REQUIRE(listed.size() == 3);
    CHECK(listed[0].kind == "house");
    CHECK(listed[0].title == "Tempered Steel");
    CHECK(listed[1].kind == "name");
    CHECK(listed[2].kind == "chest");
    CHECK(modelNames[listed[2].sector] == "chest");
    CHECK(listed[2].faces == std::vector<uint32_t>{65536 + 2});
    // The door looks south (its face's stored normal is unset here: the summed look of the upright faces is 0, so
    // the stand is south of the thing), on the ground at 320.
    CHECK(listed[0].stand[2] == doctest::Approx(320.0));
    CHECK_FALSE(listed[0].safeToUse);

    // An `outline` without `shape: outline` was built as a box over the whole plot without a word.
    LoweredOutdoorMap unused;
    std::vector<ProjectIssue> found;
    CHECK_FALSE(lowerOutdoorProject(buildingProject("      - {building: building:home, at: [40, 40], facing: s, "
        "door: none, parts: [{outline: [[0, 0], [512, 0], [256, 384]]}]}\n"), unused, found));
    CHECK(anyIssue(found, "`outline` belongs to a part of `shape: outline`"));
    found.clear();
    CHECK_FALSE(lowerOutdoorProject(buildingProject("      - {building: building:home, at: [40, 40], facing: s, "
        "door: none, parts: [{shape: outline, size: [64, 64], outline: [[0, 0], [512, 0], [256, 384]]}]}\n"),
        unused, found));
    CHECK(anyIssue(found, "`size` belongs to a part of `shape: box`"));

    // Scatter: an entry places by its own words. Splitting the first entry in two leaves the last one's trees where
    // they were (they moved all over the map when the seed was the entry's place in the list).
    const std::string table = "#\tInternalName\tHint\n1\tnothing\t\n377\trock17\trock\n464\ttree12\ttree\n";
    const auto planted = [&table](const std::string &scatter)
    {
        const Project project = buildingProject("      - {building: building:home, at: [40, 40], facing: s}\n",
            "scatter:\n" + scatter);
        LoweredOutdoorMap lowered;
        std::vector<ProjectIssue> issues;
        REQUIRE(lowerOutdoorProject(project, lowered, issues));
        OutdoorPlaces places;
        std::vector<std::string> warnings;
        placeOutdoorThings(project, lowered, table, places, issues, warnings);
        std::vector<std::array<int, 2>> trees;

        for (const OutdoorPlacedDecoration &decoration : places.decorations)
        {
            if (decoration.name == "tree12")
            {
                trees.push_back({decoration.x, decoration.y});
            }
        }

        return trees;
    };
    const std::string last = "  - {decoration: tree12, count: 20, polygon: [[70, 70], [90, 70], [90, 90], [70, 90]]}\n";
    const std::vector<std::array<int, 2>> whole = planted(
        "  - {decoration: rock17, count: 30, polygon: [[10, 10], [30, 10], [30, 30], [10, 30]]}\n" + last);
    const std::vector<std::array<int, 2>> split = planted(
        "  - {decoration: rock17, count: 15, polygon: [[10, 10], [30, 10], [30, 30], [10, 30]]}\n"
        "  - {decoration: rock17, count: 15, polygon: [[10, 10], [30, 10], [30, 30], [10, 30]], id: x}\n" + last);
    REQUIRE(whole.size() == 20);
    CHECK(whole == split);
    // Two entries written alike do not stand on one another.
    const std::vector<std::array<int, 2>> twice = planted(last + last);
    REQUIRE(twice.size() == 40);
    CHECK(std::vector<std::array<int, 2>>(twice.begin(), twice.begin() + 20)
        != std::vector<std::array<int, 2>>(twice.begin() + 20, twice.end()));
}

TEST_CASE("a height point that raises a node on a cliff line stays there; one at the foot's height goes down")
{
    // The cliff along y 64 says its low side is the north (left, walking east), so a node on the line is the
    // south's: 640. A point of 2500 there raises it (a shelf at the edge); before, it went to the north neighbour,
    // whose base was nearer, and set that node instead.
    const std::string land = "heights:\n  bands:\n"
        "    - {band: band:high, polygon: [[0, 0], [128, 0], [128, 64], [0, 64]]}\n"
        "    - {band: band:low, polygon: [[0, 64], [128, 64], [128, 128], [0, 128]]}\n"
        "  cliffs:\n    - {line: [[0, 64], [128, 64]], drop: 1900, down: left}\n";
    const LoweredOutdoorMap raised = loweredOf(land + "  points:\n    - {at: [60, 64], h: 2500}\n");
    CHECK(sampleAt(raised, 60, 64) * 32 == doctest::Approx(2500).epsilon(0.02));
    // With the low side where the land is low (the south), a node on the line is the north's top; a point there at
    // the foot's height (a cave mouth at the cliff's base) still goes down to the foot's node.
    const std::string south = land.substr(0, land.find("down: left")) + "down: right}\n";
    const LoweredOutdoorMap none = loweredOf(south);
    const LoweredOutdoorMap foot = loweredOf(south + "  points:\n    - {at: [60, 64], h: 600}\n");
    CHECK(sampleAt(foot, 60, 64) == sampleAt(none, 60, 64));
    CHECK(sampleAt(foot, 60, 65) * 32 == doctest::Approx(600).epsilon(0.06));
}

namespace
{
// The faces of a model with a texture, and of those the ones of a polygon type (0: any).
std::vector<const Game::OutdoorBModelFace *> facesWith(const Game::OutdoorBModel &model, const std::string &texture,
    int polygonType = 0)
{
    std::vector<const Game::OutdoorBModelFace *> found;

    for (const Game::OutdoorBModelFace &face : model.faces)
    {
        if (face.textureName == texture && (polygonType == 0 || face.polygonType == polygonType))
        {
            found.push_back(&face);
        }
    }

    return found;
}

std::vector<ProjectIssue> buildingIssues(const std::string &plot)
{
    LoweredOutdoorMap unused;
    std::vector<ProjectIssue> found;
    lowerOutdoorProject(buildingProject("      - {building: building:home, at: [40, 40], facing: s, " + plot
        + "}\n"), unused, found);
    return found;
}
}

TEST_CASE("an open part stands on posts: no walls, a post at each corner and along, low walls, a ceiling")
{
    // A shrine of Harmondale's kind: a square on posts 32 wide, low walls 128 high on three sides, a hip roof.
    LoweredOutdoorMap lowered = loweredBuildings("      - {building: building:home, at: [40, 40], facing: s, "
        "door: none, eaves: 0, fascia: 0, ridge: 0, textures: {post: t14abcd10, sill: t14a01}, parts: [{size: [512, "
        "512], posts: 32, post_every: 256, sill: 128, sill_walls: [e, n, w], roof: hip, roof_height: 128}]}\n");
    REQUIRE(lowered.buildings.size() == 1);
    const Game::OutdoorBModel shrine = raiseOutdoorBuilding(lowered.buildings[0]);
    // No wall panels at all.
    CHECK(facesWith(shrine, "t14a04a").empty());
    CHECK(facesWith(shrine, "t14a07").empty());
    // Eight posts (four corners, one in the middle of each wall) from the foundation to the walls' top.
    const std::vector<const Game::OutdoorBModelFace *> postTops = facesWith(shrine, "t14abcd10", 3);
    CHECK(postTops.size() == 8);

    for (const Game::OutdoorBModelFace *pFace : facesWith(shrine, "t14abcd10", 1))
    {
        CHECK(heightsOf(shrine, *pFace) == std::array<int, 2>{640 - 128, 640 + 256});
    }

    // Low walls on three sides, two pieces each between the posts, 128 high.
    size_t sills = 0;

    for (const Game::OutdoorBModelFace *pFace : facesWith(shrine, "t14a01", 3))
    {
        CHECK(heightsOf(shrine, *pFace)[0] == 640 + 128);
        ++sills;
    }

    CHECK(sills == 6);
    // A ceiling under the roof, looking down at the walls' top.
    const std::vector<const Game::OutdoorBModelFace *> ceilings = facesWith(shrine, "t14a05b", 5);
    REQUIRE(ceilings.size() == 1);
    CHECK(heightsOf(shrine, *ceilings[0]) == std::array<int, 2>{640 + 256, 640 + 256});
    // What cannot be built.
    CHECK(anyIssue(buildingIssues("parts: [{size: [512, 512], posts: 32}]"), "is on an open part"));
    CHECK(anyIssue(buildingIssues("door: none, parts: [{size: [512, 512], post_every: 256}]"),
        "belongs to an open part"));
    CHECK(anyIssue(buildingIssues("door: none, parts: [{size: [512, 512], posts: 32, sill: 240}]"), "8 up to 32"));
    CHECK(anyIssue(buildingIssues("door: none, parts: [{size: [512, 512], posts: 4}]"), "8 to 256"));
}

TEST_CASE("porches: a roof on posts out from a wall, a canopy over a door, a recess with the door at its back")
{
    // A box 1024 wide (eight bays): a porch on posts over bays 0 to 3 of the south wall, a canopy over the door
    // (bay 5), and on the north wall bays 2 to 4 set back 128.
    LoweredOutdoorMap lowered = loweredBuildings("      - {building: building:home, at: [40, 40], facing: s, "
        "eaves: 0, fascia: 0, ridge: 0, roof: flat, textures: {porch: t14b05, post: t14abcd10}, door: {wall: n, "
        "bay: 3, step: {depth: 64, height: 16}}, parts: [{size: [1024, 768], wall_height: 384, porches: ["
        "{wall: s, bays: [0, 3], depth: 192, height: 224, rise: 32, posts: 32, floor: 16}, "
        "{wall: s, bays: [5, 5], depth: 96, height: 272, rise: 24, overhang: 32}, "
        "{wall: n, bays: [2, 4], depth: 128, recess: true}]}]}\n");
    REQUIRE(lowered.buildings.size() == 1);
    OutdoorBuildingPlan &plan = lowered.buildings[0];
    REQUIRE(plan.parts[0].porches.size() == 3);
    plan.doors[0].event = 5;
    const Game::OutdoorBModel house = raiseOutdoorBuilding(plan);
    // Two porch roofs in the porch texture: from 224 + 16 and 272 + 16 at the front up to the wall.
    std::vector<std::array<int, 2>> roofs;

    for (const Game::OutdoorBModelFace *pFace : facesWith(house, "t14b05", 4))
    {
        roofs.push_back(heightsOf(house, *pFace));
    }

    std::sort(roofs.begin(), roofs.end());
    CHECK(roofs == std::vector<std::array<int, 2>>{{640 + 240, 640 + 272}, {640 + 288, 640 + 312}});
    // Two posts at the porch's front corners from its floor to its roof's front edge.
    const std::vector<const Game::OutdoorBModelFace *> postSides = facesWith(house, "t14abcd10", 1);
    CHECK(postSides.size() == 8);

    for (const Game::OutdoorBModelFace *pFace : postSides)
    {
        CHECK(heightsOf(house, *pFace) == std::array<int, 2>{640 + 16, 640 + 224});
    }
    // The door in the recess stands 128 in from the north wall (the plot's north edge is y 12288).
    const OutdoorDoorPlan &door = plan.doors[0];
    REQUIRE(door.face >= 0);
    double north = -1.0e9;

    for (const std::array<double, 2> &corner : plan.parts[0].outline)
    {
        north = std::max(north, corner[1]);
    }

    CHECK(door.y == doctest::Approx(north - 128.0));
    const Game::OutdoorBModelFace &doorFace = house.faces[door.face];

    for (const uint16_t index : doorFace.vertexIndices)
    {
        CHECK(house.vertices[index].y == std::lround(north - 128.0));
    }

    // The step lies before it, at the recess's back, 16 high.
    size_t steps = 0;

    for (const Game::OutdoorBModelFace &face : house.faces)
    {
        if (face.polygonType == 3 && heightsOf(house, face)[0] == 640 + 16)
        {
            int top = -(1 << 30);

            for (const uint16_t index : face.vertexIndices)
            {
                top = std::max(top, house.vertices[index].y);
            }

            steps += top == std::lround(north - 128.0 + 64.0) ? 1 : 0;
        }
    }

    CHECK(steps == 1);
    // What cannot be built.
    CHECK(anyIssue(buildingIssues("door: none, parts: [{size: [1024, 768], porches: [{wall: s, bays: [0, 9]}]}]"),
        "spans `bays: [first, last]`"));
    CHECK(anyIssue(buildingIssues("door: none, parts: [{size: [1024, 768], porches: [{wall: s, height: 300, "
        "rise: 64}]}]"), "must meet the wall"));
    CHECK(anyIssue(buildingIssues("door: none, parts: [{size: [1024, 768], porches: [{wall: s, recess: true, "
        "depth: 760}]}]"), "make it shallower"));
    CHECK(anyIssue(buildingIssues("door: none, parts: [{size: [1024, 768], porches: [{wall: s, bays: [0, 2]}, "
        "{wall: s, bays: [2, 3]}]}]"), "another porch"));
    CHECK(anyIssue(buildingIssues("door: {wall: s, step: {height: 200}}, parts: [{size: [1024, 768]}]"),
        "a door's `step` is"));
    // A stoop (Ravenshore's lanes): from the street 64 under the floor up to the sill, 128 out.
    LoweredOutdoorMap stoop = loweredBuildings("      - {building: building:home, at: [40, 40], facing: s, "
        "door: {wall: s, step: {depth: 128, height: 0, front: -64, overhang: 0}}, parts: [{size: [1024, 768]}]}\n");
    const Game::OutdoorBModel stooped = raiseOutdoorBuilding(stoop.buildings[0]);
    size_t slopes = 0;

    for (const Game::OutdoorBModelFace &face : stooped.faces)
    {
        if (face.polygonType == 4 && heightsOf(stooped, face) == std::array<int, 2>{640 - 64, 640})
        {
            ++slopes;
            CHECK(face.planeNormalZ == std::lround(128.0 / std::hypot(128.0, 64.0) * 65536.0));
        }
    }

    CHECK(slopes == 1);
}

TEST_CASE("a roof in rings: a thatched hall's roof that flattens to a flat top, a hut's to a tip")
{
    // Harmondale's training hall: [[192, 192], [128, 64], [80, 32]] over a round part, a flat top at 288.
    LoweredOutdoorMap lowered = loweredBuildings("      - {building: building:home, at: [40, 40], facing: s, "
        "door: none, eaves: 0, fascia: 0, parts: [{shape: round, at: [512, 384], radius: 512, sides: 12, roof: cone, "
        "tiers: [[192, 192], [128, 64], [80, 32]]}]}\n");
    REQUIRE(lowered.buildings.size() == 1);
    const Game::OutdoorBModel hall = raiseOutdoorBuilding(lowered.buildings[0]);
    std::map<std::array<int, 2>, size_t> rings;
    size_t tops = 0;

    for (const Game::OutdoorBModelFace *pFace : facesWith(hall, "t14a05"))
    {
        const std::array<int, 2> heights = heightsOf(hall, *pFace);
        ++rings[heights];
        tops += pFace->polygonType == 3 ? 1 : 0;
    }

    CHECK(rings == std::map<std::array<int, 2>, size_t>{{{896, 1088}, 12}, {{1088, 1152}, 12}, {{1152, 1184}, 12},
        {{1184, 1184}, 1}});
    CHECK(tops == 1);
    // A hut: the last ring reaches the middle, a tip.
    LoweredOutdoorMap hut = loweredBuildings("      - {building: building:home, at: [40, 40], facing: s, "
        "door: none, eaves: 0, fascia: 0, parts: [{shape: round, at: [512, 384], radius: 256, sides: 12, roof: cone, "
        "wall_height: 128, tiers: [[64, 112], [256, 80]]}]}\n");
    const Game::OutdoorBModel beehive = raiseOutdoorBuilding(hut.buildings[0]);
    size_t triangles = 0;

    for (const Game::OutdoorBModelFace *pFace : facesWith(beehive, "t14a05"))
    {
        triangles += pFace->vertexIndices.size() == 3 ? 1 : 0;
        CHECK(heightsOf(beehive, *pFace)[1] <= 640 + 128 + 192);
    }

    CHECK(triangles == 12);
    CHECK(anyIssue(buildingIssues("door: none, parts: [{shape: round, at: [512, 384], radius: 256, roof: hip, "
        "tiers: [[300, 100]]}]"), "only a cone's last ring"));
    CHECK(anyIssue(buildingIssues("door: none, parts: [{shape: round, at: [512, 384], radius: 256, roof: cone, "
        "roof_height: 96, tiers: [[64, 100]]}]"), "leave out `roof_height`"));
    CHECK(anyIssue(buildingIssues("door: none, parts: [{size: [512, 512], roof: gable, tiers: [[64, 100]]}]"),
        "cone or hip roof"));
}

TEST_CASE("a sign on a wall over a bay, a railing round a flat top, a hole with its pit in a dais")
{
    LoweredOutdoorMap lowered = loweredBuildings("      - {building: building:home, at: [40, 40], facing: s, "
        "door: none, eaves: 0, fascia: 0, roof: flat, textures: {railing: t14abcd11}, parts: [{size: [1024, 768], "
        "wall_height: 384, signs: [{wall: s, bay: 2, texture: sgmagic, size: [64, 64], bottom: 320, out: 8}], "
        "railing: {height: 208, walls: [s]}, holes: [{at: [448, 320], size: [128, 128], depth: 64}]}]}\n");
    REQUIRE(lowered.buildings.size() == 1);
    const OutdoorBuildingPlan &plan = lowered.buildings[0];
    const Game::OutdoorBModel house = raiseOutdoorBuilding(lowered.buildings[0]);
    // The board: its picture 8 out from the south wall over bay 2's middle (320 from the west end), 320 to 384.
    const std::vector<const Game::OutdoorBModelFace *> boards = facesWith(house, "sgmagic");
    REQUIRE(boards.size() == 1);
    CHECK(heightsOf(house, *boards[0]) == std::array<int, 2>{640 + 320, 640 + 384});
    double south = 1.0e9;
    double west = 1.0e9;

    for (const std::array<double, 2> &corner : plan.parts[0].outline)
    {
        south = std::min(south, corner[1]);
        west = std::min(west, corner[0]);
    }

    for (const uint16_t index : boards[0]->vertexIndices)
    {
        CHECK(house.vertices[index].y == std::lround(south - 8.0));
        CHECK(std::abs(house.vertices[index].x - (west + 320.0)) == 32);
    }

    // The railing: its rail's top at 208 over the roof along the south wall, posts every 128 at most.
    size_t posts = 0;

    for (const Game::OutdoorBModelFace *pFace : facesWith(house, "t14abcd11", 3))
    {
        const int top = heightsOf(house, *pFace)[0];
        CHECK((top == 640 + 384 + 192 || top == 640 + 384 + 208));
        posts += top == 640 + 384 + 192 ? 1 : 0;
    }

    CHECK(posts == 9);
    // Between the posts a barrier the party cannot pass, not drawn (both ways).
    size_t barriers = 0;

    for (const Game::OutdoorBModelFace &face : house.faces)
    {
        barriers += (face.attributes & InvisibleBit) != 0 && face.textureName == "t14abcd11" ? 1 : 0;
    }

    CHECK(barriers == 2);
    // The top in pieces round the hole, the pit 64 deep under it with four sides and a floor.
    size_t pieces = 0;

    for (const Game::OutdoorBModelFace *pFace : facesWith(house, "t14a05", 3))
    {
        CHECK(heightsOf(house, *pFace)[0] == 640 + 384);
        ++pieces;
    }

    CHECK(pieces == 4);
    CHECK(facesWith(house, "t14a01", 1).size() >= 4);
    size_t pitFloors = 0;

    for (const Game::OutdoorBModelFace *pFace : facesWith(house, "t14a05b", 3))
    {
        pitFloors += heightsOf(house, *pFace) == std::array<int, 2>{640 + 320, 640 + 320} ? 1 : 0;
    }

    CHECK(pitFloors == 1);
    // What cannot be built.
    CHECK(anyIssue(buildingIssues("door: none, parts: [{size: [1024, 768], signs: [{wall: s, bay: 9, texture: x1}]}]"),
        "a sign on a wall is"));
    CHECK(anyIssue(buildingIssues("door: none, parts: [{size: [1024, 768], wall_height: 256, signs: [{wall: s, "
        "bay: 2, texture: x1, bottom: 240}]}]"), "must lie on the wall"));
    CHECK(anyIssue(buildingIssues("door: none, roof: hip, parts: [{size: [1024, 768], railing: {height: 200}}]"),
        "runs round a flat top"));
    CHECK(anyIssue(buildingIssues("door: none, roof: flat, parts: [{size: [1024, 768], holes: [{at: [0, 0], "
        "size: [128, 128]}]}]"), "within 8 of the part's walls"));
    CHECK(anyIssue(buildingIssues("door: none, roof: hip, parts: [{size: [1024, 768], holes: [{at: [256, 256], "
        "size: [128, 128]}]}]"), "cut in a flat top"));
}

TEST_CASE("outdoor batch seven's building words are in the sketch schema, described")
{
    const YAML::Node root = inlinedSketchSchema();
    const YAML::Node plot = root["properties"]["districts"]["items"]["properties"]["plots"]["items"]["properties"];
    const YAML::Node structure = root["properties"]["structures"]["items"]["properties"];

    for (const YAML::Node &part : {plot["parts"]["items"]["properties"], structure["parts"]["items"]["properties"]})
    {
        for (const char *pWord : {"posts", "post_every", "sill", "sill_walls", "porches", "signs", "railing", "holes",
                 "tiers"})
        {
            CAPTURE(pWord);
            CHECK(part[pWord]["description"].IsDefined());
        }

        for (const char *pWord : {"wall", "bays", "depth", "height", "rise", "thickness", "overhang", "posts", "floor",
                 "recess"})
        {
            CAPTURE(pWord);
            CHECK(part["porches"]["items"]["properties"][pWord]["description"].IsDefined());
        }
    }

    CHECK(plot["tiers"]["description"].IsDefined());
    CHECK(structure["tiers"]["description"].IsDefined());
    CHECK(plot["door"]["oneOf"][1]["properties"]["step"]["description"].IsDefined());
    CHECK(plot["doors"]["items"]["properties"]["step"]["description"].IsDefined());
    CHECK(structure["doors"]["items"]["properties"]["step"]["description"].IsDefined());
}

TEST_CASE("a slender obelisk of eight sides on a plinth, a signpost's arms with their own pictures, a well's post")
{
    std::vector<ProjectIssue> issues;
    IdsLock ids;
    // Harmondale's white obelisk: eight sides 128 across drawing in to 80, a tip 128 high, a plinth 416 by 32.
    const OutdoorThings things = thingsOf("structures:\n"
        "  - {id: thing:obelisk, kind: obelisk, at: [50, 50], width: 128, height: 960, sides: 8, taper: 0.625, "
        "tip: 128, plinth: [416, 32], textures: {wall: t14a01, plinth: t14a05}}\n"
        "  - {id: thing:post, kind: sign, at: [56, 50], height: 272, width: 112, post: 32, board_height: 32, arms: "
        "[{title: West, toward: w, board: s_west}, {title: South, toward: s}], textures: {board: s_south}}\n"
        "  - {id: thing:well, kind: well, at: [60, 50], radius: 112, height: 96, post: 320}\n", issues, ids);
    REQUIRE(issues.empty());
    REQUIRE(things.models.size() == 3);
    const Game::OutdoorBModel &obelisk = things.models[0];
    // Eight sides of the shaft from the plinth's top, eight faces of the tip, the plinth's four sides and top.
    size_t shaft = 0;
    size_t tip = 0;

    for (const Game::OutdoorBModelFace &face : obelisk.faces)
    {
        if (face.textureName == "t14a01")
        {
            const std::array<int, 2> heights = heightsOf(obelisk, face);
            shaft += heights == std::array<int, 2>{640 + 32, 640 + 960 - 128} ? 1 : 0;
            tip += heights == std::array<int, 2>{640 + 960 - 128, 640 + 960} ? 1 : 0;
        }
    }

    CHECK(shaft == 8);
    CHECK(tip == 8);
    CHECK(facesWith(obelisk, "t14a05", 3).size() == 1);
    // The signpost: a post 32 wide, each arm's picture its own (the second takes the sign's board).
    const Game::OutdoorBModel &post = things.models[1];
    CHECK(facesWith(post, "s_west").size() == 2);
    CHECK(facesWith(post, "s_south").size() == 2);
    // The well's post stands from its water up to 320.
    int highest = 0;

    for (const Game::OutdoorBModelVertex &vertex : things.models[2].vertices)
    {
        highest = std::max(highest, vertex.z);
    }

    CHECK(highest == 640 + 320);
    // What cannot be built.
    const auto refused = [](const std::string &structure, const std::string &fragment)
    {
        CAPTURE(structure);
        std::vector<ProjectIssue> found;
        IdsLock lock;
        thingsOf("structures:\n  - " + structure + "\n", found, lock);
        CHECK(anyIssue(found, fragment));
    };
    refused("{id: thing:o, kind: obelisk, at: [50, 50], sides: 6}", "4 or 8 `sides`");
    refused("{id: thing:o, kind: obelisk, at: [50, 50], width: 128, plinth: [64, 32]}", "at least as wide");
    refused("{id: thing:w, kind: well, at: [50, 50], post: 64}", "higher than its wall");
    refused("{id: thing:w, kind: well, at: [50, 50], post: 300, roofed: true}", "not both");
    refused("{id: thing:s, kind: sign, at: [50, 50], post: 200, arms: [{title: W, toward: w}]}", "8 to 128");
}

TEST_CASE("a sign that hangs across a wall: an arm from the wall, the board under it with its picture on both faces")
{
    LoweredOutdoorMap lowered = loweredBuildings("      - {building: building:home, at: [40, 40], facing: s, "
        "door: none, eaves: 0, fascia: 0, roof: flat, parts: [{size: [1024, 768], wall_height: 256, signs: [{wall: s, "
        "bay: 2, texture: sgmagic, size: [64, 64], bottom: 152, out: 56, hang: true}]}]}\n");
    const OutdoorBuildingPlan &plan = lowered.buildings[0];
    const Game::OutdoorBModel house = raiseOutdoorBuilding(lowered.buildings[0]);
    const std::vector<const Game::OutdoorBModelFace *> boards = facesWith(house, "sgmagic");
    REQUIRE(boards.size() == 2);
    double south = 1.0e9;

    for (const std::array<double, 2> &corner : plan.parts[0].outline)
    {
        south = std::min(south, corner[1]);
    }

    for (const Game::OutdoorBModelFace *pBoard : boards)
    {
        CHECK(heightsOf(house, *pBoard) == std::array<int, 2>{640 + 152, 640 + 216});
        // Across the wall: it looks east or west, from 56 to 120 out.
        CHECK(std::abs(pBoard->planeNormalX) == 65536);

        for (const uint16_t index : pBoard->vertexIndices)
        {
            const double out = south - house.vertices[index].y;
            CHECK((std::lround(out) == 56 || std::lround(out) == 120));
        }
    }

    CHECK(anyIssue(buildingIssues("door: none, parts: [{size: [1024, 768], wall_height: 256, signs: [{wall: s, "
        "bay: 2, texture: x1, bottom: 200, hang: true}]}]"), "a sign on a wall is"));
}

TEST_CASE("a roof in rings over an outline whose short sides vanish on the way in covers the outline once")
{
    // Harmondale's training hall: twelve sides of 128 to 286; the short ones shrink to nothing in the second ring.
    // Its rings measured square to its sides: in 144 (114 to 192) up 192, in 128 up 64, in 80 up 32, a flat top.
    LoweredOutdoorMap lowered = loweredBuildings("      - {building: building:home, at: [40, 40], facing: s, "
        "door: none, eaves: 0, fascia: 0, parts: [{shape: outline, outline: [[464, 704], [592, 704], [848, 576], "
        "[976, 448], [976, 192], [848, 64], [592, -64], [464, -64], [208, 64], [80, 192], [80, 448], [208, 576]], "
        "roof: cone, tiers: [[144, 192], [128, 64], [80, 32]]}]}\n");
    REQUIRE(lowered.buildings.size() == 1);
    const OutdoorBuildingPlan &plan = lowered.buildings[0];
    const Game::OutdoorBModel hall = raiseOutdoorBuilding(lowered.buildings[0]);
    double outlineArea = 0.0;
    std::array<double, 4> bounds = {1.0e9, 1.0e9, -1.0e9, -1.0e9};

    for (size_t index = 0; index < plan.parts[0].outline.size(); ++index)
    {
        const std::array<double, 2> &from = plan.parts[0].outline[index];
        const std::array<double, 2> &to = plan.parts[0].outline[(index + 1) % plan.parts[0].outline.size()];
        outlineArea += (from[0] * to[1] - to[0] * from[1]) * 0.5;
        bounds = {std::min(bounds[0], from[0]), std::min(bounds[1], from[1]), std::max(bounds[2], from[0]),
            std::max(bounds[3], from[1])};
    }

    // Every roof face lies over the outline, and together they cover it once (seen from above).
    double roofArea = 0.0;
    size_t tops = 0;

    for (const Game::OutdoorBModelFace *pFace : facesWith(hall, "t14a05"))
    {
        double area = 0.0;

        for (size_t index = 0; index < pFace->vertexIndices.size(); ++index)
        {
            const Game::OutdoorBModelVertex &from = hall.vertices[pFace->vertexIndices[index]];
            const Game::OutdoorBModelVertex &to =
                hall.vertices[pFace->vertexIndices[(index + 1) % pFace->vertexIndices.size()]];
            area += (static_cast<double>(from.x) * to.y - static_cast<double>(to.x) * from.y) * 0.5;
            CHECK(from.x >= bounds[0] - 1.0);
            CHECK(from.x <= bounds[2] + 1.0);
            CHECK(from.y >= bounds[1] - 1.0);
            CHECK(from.y <= bounds[3] + 1.0);
            CHECK(from.z >= 640 + 256);
            CHECK(from.z <= 640 + 256 + 288);
        }

        roofArea += std::fabs(area);
        tops += heightsOf(hall, *pFace) == std::array<int, 2>{640 + 256 + 288, 640 + 256 + 288} ? 1 : 0;
    }

    CHECK(tops == 1);
    CHECK(roofArea == doctest::Approx(outlineArea).epsilon(0.01));
}

TEST_CASE("outdoor batch eight: one event on several things, a sign carrying its shop's door, a board off its bay")
{
    // A step trap of three plates on one event (Harmondale's fort: the four faces round the pit carry event 236).
    std::vector<ProjectIssue> issues;
    IdsLock ids;
    const OutdoorThings things = thingsOf("structures:\n"
        "  - {id: thing:plate_a, kind: platform, at: [50, 50], size: [128, 128], trigger: step, effects: "
        "[{text: Trap}]}\n"
        "  - {id: thing:plate_b, kind: platform, at: [51, 50], size: [128, 128], trigger: step, same_event_as: "
        "thing:plate_a}\n"
        "  - {id: thing:plate_c, kind: platform, at: [52, 50], size: [128, 128], same_event_as: thing:plate_a, "
        "hint: Plate}\n", issues, ids);
    REQUIRE(issues.empty());
    REQUIRE(things.models.size() == 3);
    const int trap = IdsLock::number(ids.events, "evt:thing:plate_a", 1);
    CHECK(ids.events.count("evt:thing:plate_b") == 0);
    // One handler only; the second plate runs it from its top, the third from its clicked faces.
    size_t handlers = 0;

    for (const OutdoorEventPlan &event : things.events)
    {
        handlers += event.number == trap ? 1 : 0;
    }

    CHECK(handlers == 1);

    for (size_t model = 0; model < 3; ++model)
    {
        size_t carrying = 0;

        for (const Game::OutdoorBModelFace &face : things.models[model].faces)
        {
            carrying += face.cogTriggeredNumber == trap ? 1 : 0;
        }

        CAPTURE(model);
        CHECK(carrying >= 1);
    }

    // What cannot be said.
    const auto refused = [](const std::string &structure, const std::string &fragment)
    {
        CAPTURE(structure);
        std::vector<ProjectIssue> found;
        IdsLock lock;
        thingsOf("structures:\n  - {id: thing:a, kind: platform, at: [50, 50], effects: [{text: A}]}\n"
            "  - {id: thing:n, kind: platform, at: [52, 50]}\n  - " + structure + "\n", found, lock);
        CHECK(anyIssue(found, fragment));
    };
    refused("{id: thing:b, kind: platform, at: [51, 50], same_event_as: thing:a, effects: [{text: B}]}",
        "leave out its own");
    refused("{id: thing:b, kind: platform, at: [51, 50], same_event_as: thing:a, once: true}", "belongs to the event");
    refused("{id: thing:b, kind: platform, at: [51, 50], same_event_as: thing:nothing}", "no structure has the id");
    refused("{id: thing:b, kind: platform, at: [51, 50], same_event_as: thing:n}", "carries no event of its own");
    refused("{id: thing:b, kind: platform, at: [51, 50], same_event_as: thing:b}", "its own event");
    refused("{id: thing:b, kind: platform, at: [51, 50], same_event_as: building:home}", "carries no event");
    refused("{id: thing:b, kind: platform, at: [51, 50], same_event_as: {building: building:home, door: 1, part: p}}",
        "one of them");

    // A sign on its post carrying its shop's door (Ravenshore: Caori's Curios' sign, event 196), built whole.
    const BuiltOutdoor built = builtOutdoor(buildingProject("      - {building: building:home, at: [40, 40], "
        "facing: s, house: 5, title: Home, doors: [{wall: n, house: 6, title: Back}]}\n",
        "structures:\n  - {id: thing:sign, kind: sign, at: [50, 50], same_event_as: building:home}\n"
        "  - {id: thing:sign2, kind: sign, at: [52, 50], same_event_as: {building: building:home, door: 1}}\n"),
        "oymap_same_event");
    REQUIRE(built.built);
    const int home = eventNumberOf(built.lua, "Home");
    const int back = eventNumberOf(built.lua, "Back");
    CHECK(home != 0);
    CHECK(back != 0);
    CHECK(built.lua.find("evt.EnterHouse(5)") != std::string::npos);
    // Two handlers of the house, no others named after the signs.
    CHECK(built.lua.find("thing:sign") == std::string::npos);

    // A board 48 east of its bay's middle (Ravenshore's boards stand 32 to 64 off).
    LoweredOutdoorMap lowered = loweredBuildings("      - {building: building:home, at: [40, 40], facing: s, "
        "door: none, eaves: 0, fascia: 0, roof: flat, parts: [{size: [1024, 768], wall_height: 384, signs: [{wall: s, "
        "bay: 2, texture: sgmagic, size: [64, 64], bottom: 320, out: 8, offset: 48}]}]}\n");
    const Game::OutdoorBModel house = raiseOutdoorBuilding(lowered.buildings[0]);
    const std::vector<const Game::OutdoorBModelFace *> boards = facesWith(house, "sgmagic");
    REQUIRE(boards.size() == 1);
    double west = 1.0e9;

    for (const std::array<double, 2> &corner : lowered.buildings[0].parts[0].outline)
    {
        west = std::min(west, corner[0]);
    }

    for (const uint16_t index : boards[0]->vertexIndices)
    {
        CHECK(std::abs(house.vertices[index].x - (west + 320.0 + 48.0)) == 32);
    }

    CHECK(anyIssue(buildingIssues("door: none, parts: [{size: [1024, 768], wall_height: 384, signs: [{wall: s, "
        "bay: 0, texture: x1, offset: -100}]}]"), "must lie on the wall"));
}

TEST_CASE("outdoor batch eight: a house on a base course, a well's windlass frame, a buried thing, bay names")
{
    // A plinth of 64: the land under the plot lies 64 under the floor, the base course shows over it.
    LoweredOutdoorMap plain = loweredBuildings("      - {building: building:home, at: [40, 40], facing: s}\n");
    LoweredOutdoorMap raised = loweredBuildings("      - {building: building:home, at: [40, 40], facing: s, "
        "plinth: 64}\n");
    REQUIRE(raised.buildings.size() == 1);
    CHECK(raised.buildings[0].base == plain.buildings[0].base + 64.0);
    CHECK(raised.storedHeightAt(41.0, 41.0) == plain.storedHeightAt(41.0, 41.0));
    CHECK(anyIssue(buildingIssues("plinth: 48"), "steps of 32"));
    CHECK(anyIssue(buildingIssues("plinth: 128"), "raise `foundation`"));
    CHECK(!anyIssue(buildingIssues("plinth: 128, foundation: 160"), "plinth"));

    // Ravenshore's well: two uprights 64 drawing in to 24 from the ring's top (80) to 184, a beam 32 high on them.
    std::vector<ProjectIssue> issues;
    IdsLock ids;
    const OutdoorThings things = thingsOf("structures:\n"
        "  - {id: thing:well, kind: well, at: [50, 50], radius: 128, height: 80, sides: 8, frame: {height: 184, "
        "posts: [64, 24], beam: 32}, textures: {post: t1cabs, beam: t06c11}}\n"
        "  - {id: thing:well2, kind: well, at: [54, 50], radius: 128, height: 80, frame: {roof: cone}}\n"
        "  - {id: thing:well3, kind: well, at: [58, 50], radius: 88, height: 96, frame: {height: 224, posts: [16, 16], "
        "beam: 0, roof: gable}}\n", issues, ids);
    REQUIRE(issues.empty());
    REQUIRE(things.models.size() == 3);
    const std::vector<const Game::OutdoorBModelFace *> uprights = facesWith(things.models[0], "t1cabs");
    CHECK(uprights.size() == 8);

    for (const Game::OutdoorBModelFace *pFace : uprights)
    {
        CHECK(heightsOf(things.models[0], *pFace) == std::array<int, 2>{640 + 80, 640 + 184});
    }

    int top = 0;

    for (const Game::OutdoorBModelVertex &vertex : things.models[0].vertices)
    {
        top = std::max(top, vertex.z);
    }

    CHECK(top == 640 + 216);
    CHECK(facesWith(things.models[0], "t06c11").size() >= 5);
    int coneTip = 0;

    for (const Game::OutdoorBModelVertex &vertex : things.models[1].vertices)
    {
        coneTip = std::max(coneTip, vertex.z);
    }

    CHECK(coneTip == 640 + 184 + 32 + 96);
    int ridge = 0;

    for (const Game::OutdoorBModelVertex &vertex : things.models[2].vertices)
    {
        ridge = std::max(ridge, vertex.z);
    }

    CHECK(ridge == 640 + 224 + 32);
    const auto refused = [](const std::string &structure, const std::string &fragment)
    {
        CAPTURE(structure);
        std::vector<ProjectIssue> found;
        IdsLock lock;
        thingsOf("structures:\n  - " + structure + "\n", found, lock);
        CHECK(anyIssue(found, fragment));
    };
    refused("{id: thing:w, kind: well, at: [50, 50], frame: {}, post: 300}", "one of them");
    refused("{id: thing:w, kind: well, at: [50, 50], frame: {posts: [24, 64]}}", "no wider");
    refused("{id: thing:w, kind: well, at: [50, 50], height: 96, frame: {height: 100}}", "at least 32 over the ring");
    refused("{id: thing:w, kind: well, at: [50, 50], frame: {roof: hip}}", "cone or gable");

    // A chest under the land is built, with a word.
    std::vector<ProjectIssue> found;
    std::vector<std::string> warnings;
    IdsLock lock;
    thingsOf("structures:\n  - {id: thing:chest, kind: chest, at: [50, 50], raise: -24}\n", found, lock, &warnings);
    CHECK(found.empty());
    bool warned = false;

    for (const std::string &warning : warnings)
    {
        warned = warned || warning.find("thing:chest stands 24 under the land") != std::string::npos;
    }

    CHECK(warned);

    // A bay naming a texture without a digit (Harmondale's window chbw) is a texture's name; one with a space is not.
    CHECK(!anyIssue(buildingIssues("parts: [{size: [512, 384], walls: {s: [wall, chbw, door, chbw]}}]"),
        "a bay names"));
    CHECK(anyIssue(buildingIssues("parts: [{size: [512, 384], walls: {s: [wall, \"ch bw\", door, wall]}}]"),
        "cannot be a texture's name"));
    // A recess to the wall's end is refused for its bays, not its depth.
    const std::vector<ProjectIssue> recess = buildingIssues("parts: [{size: [768, 512], porches: [{wall: s, "
        "bays: [3, 5], depth: 64, recess: true}]}]");
    CHECK(anyIssue(recess, "open at a corner"));
    CHECK(!anyIssue(recess, "make it shallower"));
}

TEST_CASE("outdoor batch eight: spawn markers follow their own area's words, not its place in the list")
{
    const std::string wolves = "  - {id: pop:wolves, count: 3, polygon: [[60, 60], [70, 60], [70, 70], [60, 70]]}\n";
    const std::string more = "  - {id: pop:wolves, count: 2, polygon: [[80, 80], [90, 80], [90, 90], [80, 90]]}\n";
    const auto markers = [](const std::string &areas)
    {
        const Project project = buildingProject("      - {building: building:home, at: [40, 40], facing: s}\n",
            "areas:\n" + areas);
        LoweredOutdoorMap lowered;
        std::vector<ProjectIssue> issues;
        REQUIRE(lowerOutdoorProject(project, lowered, issues));
        OutdoorPlaces places;
        std::vector<std::string> warnings;
        REQUIRE(placeOutdoorThings(project, lowered, {}, places, issues, warnings, {}));
        std::set<std::array<int, 2>> found;

        for (const OutdoorPlacedSpawn &spawn : places.spawns)
        {
            if (spawn.x > (60 - 64) * 512 && spawn.x < (70 - 64) * 512)
            {
                found.insert({spawn.x, spawn.y});
            }
        }

        return found;
    };
    const std::set<std::array<int, 2>> alone = markers(wolves);
    CHECK(alone.size() == 3);
    CHECK(markers(more + wolves) == alone);
}

TEST_CASE("outdoor batch eight's words are in the sketch schema, described")
{
    const YAML::Node root = inlinedSketchSchema();
    const YAML::Node plot = root["properties"]["districts"]["items"]["properties"]["plots"]["items"]["properties"];
    const YAML::Node structure = root["properties"]["structures"]["items"]["properties"];
    CHECK(structure["same_event_as"]["description"].IsDefined());
    CHECK(structure["frame"]["description"].IsDefined());
    CHECK(structure["plinth"]["description"].IsDefined());
    CHECK(plot["plinth"]["description"].IsDefined());
    CHECK(plot["parts"]["items"]["properties"]["signs"]["items"]["properties"]["offset"]["description"].IsDefined());
    CHECK(structure["parts"]["items"]["properties"]["signs"]["items"]["properties"]["offset"]["description"]
        .IsDefined());
}

TEST_CASE("a map's own tile sets: Shadowspire's grey dust, grey stone, tar pools, its water and road rows")
{
    const std::string whole = "polygon: [[0, 0], [128, 0], [128, 128], [0, 128]]}\n";
    const LoweredOutdoorMap lowered = loweredOf(std::string(LevelLand)
        + "tile_sets: {dirt: gdtyl, water: 738, road: gdrdcros}\n"
        "ground:\n  - {material: gstyl, " + whole
        + "  - {material: gdtyl, polygon: [[60, 60], [70, 60], [70, 70], [60, 70]]}\n"
        "water:\n  bodies:\n"
        "    - {id: water:sea, kind: lake, level: 640, polygon: [[100, 20], [110, 20], [110, 30], [100, 30]]}\n"
        "    - {id: water:tar, kind: pond, level: 640, tile_set: tartyl, "
        "polygon: [[20, 20], [30, 20], [30, 30], [20, 30]]}\n");
    // The master tile turns the plain tiles into grey dust; the four sets are Shadowspire's own rows.
    CHECK(lowered.masterTile == 2);
    CHECK(lowered.tileSets == std::array<uint16_t, 4>{702, 738, 666, 774});
    CHECK(lowered.groundKinds == std::vector<std::string>{"gstyl", "tartyl"});
    // The tar pool is the second ground set's plain tile, its edges the tar's tiles toward the dust; the lake is
    // the water set; the dust named by its set is the plain ground.
    CHECK(tileAt(lowered, 25, 25) >= 162);
    CHECK(tileAt(lowered, 25, 25) < 174);
    CHECK(tileAt(lowered, 19, 25) == 162 + 17);
    CHECK(tileAt(lowered, 105, 25) >= 126);
    CHECK(tileAt(lowered, 105, 25) < 138);
    CHECK(tileAt(lowered, 65, 65) >= 1);
    CHECK(tileAt(lowered, 65, 65) <= 12);
    // Grey stone keeps a line of dust from the tar, as from water.
    CHECK(tileAt(lowered, 18, 25) == 90 + 16);

    // Sets the world lacks, or that cannot serve, are refused with the sets it has.
    std::vector<ProjectIssue> issues = refusedWith(std::string(LevelLand) + "tile_sets: {water: gstyl, road: 90}\n");
    CHECK(anyIssue(issues, "has no liquid set `gstyl`"));
    CHECK(anyIssue(issues, "tartyl (666)"));
    CHECK(anyIssue(issues, "has no road set `90`"));
    issues = refusedWith(std::string(LevelLand) + "tile_sets: {dirt: gdtyl}\n", "mm7");
    CHECK(anyIssue(issues, "one of 7dirttyl"));
    issues = refusedWith(std::string(LevelLand) + "water:\n  bodies:\n    - {id: water:x, kind: pond, level: 640, "
        "tile_set: gstyl, polygon: [[20, 20], [30, 20], [30, 30], [20, 30]]}\n");
    CHECK(anyIssue(issues, "is a liquid set of the world mm8"));
    // A set named by its row is that set: the second tar set of the table.
    const LoweredOutdoorMap byRow = loweredOf(std::string(LevelLand) + "ground:\n  - {material: \"846\", " + whole);
    CHECK(byRow.tileSets[0] == 846);
    // D-40: lava on a map of MM7's tiles (Xeen's X7): MM8's lava set in the MM7 table's row 450.
    const LoweredOutdoorMap lava = loweredOf(std::string(LevelLand) + "water:\n  bodies:\n    - {id: water:lava, kind: "
        "pond, level: 640, tile_set: lavtyl, polygon: [[20, 20], [30, 20], [30, 30], [20, 30]]}\n", "mm7");
    CHECK(std::find(lava.tileSets.begin(), lava.tileSets.end(), 450) != lava.tileSets.end());
    CHECK(std::find(lava.groundKinds.begin(), lava.groundKinds.end(), "lavtyl") != lava.groundKinds.end());
}

TEST_CASE("a road jogs with the diagonal pieces of its own set only: an MM6 road with two round bends")
{
    const std::string roads = std::string(LevelLand)
        + "roads:\n  - {link: road:b, line: [[40.5, 40.5], [50.5, 50.5]]}\n";
    const LoweredOutdoorMap mm6 = loweredOf(roads, "mm6");
    const LoweredOutdoorMap mm8 = loweredOf(roads);
    size_t mm6Diagonals = 0;
    size_t mm8Diagonals = 0;

    for (size_t cell = 0; cell < mm6.tiles.size(); ++cell)
    {
        const int road = 90 + 3 * 36;
        mm6Diagonals += mm6.tiles[cell] >= road + 19 && mm6.tiles[cell] <= road + 22 ? 1 : 0;
        mm8Diagonals += mm8.tiles[cell] >= road + 19 && mm8.tiles[cell] <= road + 22 ? 1 : 0;
    }

    CHECK(mm6.tileSets[3] == 774);
    CHECK(mm6Diagonals == 0);
    CHECK(mm8Diagonals > 0);
}

TEST_CASE("over a grid height points that stand close together do not add up")
{
    const LoweredOutdoorMap lowered = loweredOf("heights:\n  points:\n    - {at: [19, 20], h: 1600}\n"
        "    - {at: [21, 20], h: 1600}\n    - {at: [20, 19], h: 1600}\n    - {at: [20, 21], h: 1600}\n"
        + gridText(10, 99, 99, 10));
    CHECK(sampleAt(lowered, 19, 20) == 1600 / 32);
    // Between them the land reaches the points' height, not three times their rise.
    CHECK(sampleAt(lowered, 20, 20) <= 1600 / 32);
    CHECK(sampleAt(lowered, 20, 20) >= 1400 / 32);
}

TEST_CASE("compare: the plain ground is the map's own; tar and lava are kinds of their own, not water")
{
    std::vector<Game::TerrainTileDescriptor> tiles = testTiles();

    for (int tile = 1; tile <= 12; ++tile)
    {
        tiles[tile].textureName = "gdtyl";
        tiles[tile].tileset = 26;
    }

    for (int offset = 0; offset < 36; ++offset)
    {
        tiles[126 + offset].textureName = "tartyl";
    }

    Game::OutdoorMapData map = testWorld();

    for (int y = 0; y < 60; ++y)
    {
        for (int x = 60; x < 128; ++x)
        {
            map.tileMap[y * Side + x] = 1;
        }

        map.tileMap[y * Side + 59] = 90 + 17;
    }

    OutdoorCompareSide side;
    side.name = "original";
    side.pMap = &map;
    side.tiles = tiles;
    OutdoorCompareResult result;
    std::string errorMessage;
    REQUIRE(compareOutdoorMaps(side, side, result, errorMessage, OutdoorCompareOptions()));
    CHECK(result.score == doctest::Approx(1.0));
    bool tar = false;

    for (size_t kind = 0; kind < result.groundKinds.size(); ++kind)
    {
        // The grass tiles toward dirt lead over to grey dust here: no corner is the world's dirt.
        if (result.groundKinds[kind] == "dirt")
        {
            CHECK(result.groundQuarters[kind][0] == 0);
        }

        tar = tar || (result.groundKinds[kind] == "tartyl" && result.groundQuarters[kind][0] > 0);
    }

    CHECK(tar);
}

TEST_CASE("compare: invisible faces are neither a building's top nor its plan")
{
    const Game::OutdoorMapData original = testWorld();
    Game::OutdoorMapData rebuilt = original;
    // An invisible ceiling high over the first house, wider than it (Harmondale's footbridge has one).
    Game::OutdoorBModel &house = rebuilt.bmodels[0];
    const uint16_t first = static_cast<uint16_t>(house.vertices.size());
    house.vertices.push_back({768, 768, 3000});
    house.vertices.push_back({2304, 768, 3000});
    house.vertices.push_back({2304, 2048, 3000});
    house.vertices.push_back({768, 2048, 3000});
    Game::OutdoorBModelFace ceiling;
    ceiling.vertexIndices = {first, static_cast<uint16_t>(first + 1), static_cast<uint16_t>(first + 2),
        static_cast<uint16_t>(first + 3)};
    ceiling.attributes = Game::faceAttributeBit(Game::FaceAttribute::Invisible);
    house.faces.push_back(ceiling);
    CHECK(partOf(compared(original, rebuilt), "buildings") == doctest::Approx(1.0));
    // Seen, the same ceiling is a top.
    rebuilt.bmodels[0].faces.back().attributes = 0;
    CHECK(partOf(compared(original, rebuilt), "buildings") < 1.0);
}

TEST_CASE("the sky theme's row of sky.yml: added to the maps block, an older row replaced, comments kept")
{
    const std::string text = "version: 1\nthemes:\n  necrotic: {saturation: 0.25}\n# the maps\nmaps:\n"
        "  # MM8\n  out06.odm: necrotic\n  mine.odm: lush\n";
    const std::string written = withSkyTheme(text, "mine.odm", "necrotic");
    CHECK(written.find("  mine.odm: necrotic\n") != std::string::npos);
    CHECK(written.find("mine.odm: lush") == std::string::npos);
    CHECK(written.find("  # MM8\n  out06.odm: necrotic\n") != std::string::npos);
    CHECK(written.find("# the maps\n") != std::string::npos);
    // A block that is not the last: the row goes at its end, before the next block.
    const std::string middle = withSkyTheme("maps:\n  a.odm: lush\nother: 1\n", "b.odm", "arid");
    CHECK(middle == "maps:\n  a.odm: lush\n  b.odm: arid\nother: 1\n");
}

TEST_CASE("atmosphere mist and sky theme: the scene's mist block; a mist the game refuses is refused")
{
    Project good = buildingProject("      - {building: building:home, at: [40, 40], facing: s, house: 904}\n",
        "points:\n  - {id: entrance:north, at: [64, 20], facing: s}\n");
    ProjectFile air;
    air.name = "atmosphere.yml";
    air.text = "format: 0\nsky_theme: necrotic\nmist:\n  layer: {color_rgb: [150, 168, 158], base_height: 100, "
        "falloff_height: 80, visibility: 720}\n";
    air.document = YAML::Load(air.text);
    good.files[air.name] = air;
    good.root = std::filesystem::temp_directory_path() / "oymap_outdoor_mist";
    BuildOptions options;
    options.outputDirectory = good.root / "build";
    BuildResult result;
    REQUIRE(buildOutdoorProject(good, options, result));
    std::ifstream stream(good.root / "build" / "groundtest.scene.yml");
    const std::string scene((std::istreambuf_iterator<char>(stream)), std::istreambuf_iterator<char>());
    CHECK(scene.find("mist:") != std::string::npos);
    CHECK(scene.find("base_height: 100") != std::string::npos);
    CHECK(outdoorSkyTheme(good) == "necrotic");
    // A door without a title says nothing (no id as its name).
    std::ifstream luaStream(good.root / "build" / "groundtest.lua");
    const std::string lua((std::istreambuf_iterator<char>(luaStream)), std::istreambuf_iterator<char>());
    CHECK(lua.find("\"building:home\"") == std::string::npos);

    good.files["atmosphere.yml"].text = "format: 0\nmist:\n  layer: {color_rgb: [150, 168, 158], height: 100}\n";
    good.files["atmosphere.yml"].document = YAML::Load(good.files["atmosphere.yml"].text);
    BuildResult refused;
    CHECK_FALSE(buildOutdoorProject(good, options, refused));
    CHECK(anyIssue(refused.issues, "the game refuses this mist"));
    std::error_code error;
    std::filesystem::remove_all(good.root, error);
}

TEST_CASE("a building has no trigger, and its own words need its own door")
{
    Project project = buildingProject("      - {building: building:home, at: [40, 40], facing: s, door: none, "
        "trigger: step, effects: [{text: Hello}]}\n");
    std::vector<ProjectIssue> issues;
    validateOutdoorProject(project, issues);
    CHECK(anyIssue(issues, "a building has no `trigger`"));
    CHECK(anyIssue(issues, "has no door of its own"));
}

#include "core/Coplanar.h"

TEST_CASE("outdoor coplanar: identical parts and parts that run through each other, named by structure and part")
{
    // Two identical boxes, and a third box running into the first along its south wall's plane.
    LoweredOutdoorMap lowered = loweredBuildings("      - {building: building:home, at: [40, 40], facing: s, "
        "door: none, eaves: 0, fascia: 0, roof: flat, parts: [{id: a, at: [0, 0], size: [512, 512]}, {id: b, at: "
        "[0, 0], size: [512, 512]}, {id: c, at: [256, 0], size: [512, 256]}]}\n");
    REQUIRE(lowered.buildings.size() == 1);
    std::vector<Game::OutdoorBModel> models = {raiseOutdoorBuilding(lowered.buildings[0])};
    const std::vector<OutdoorCoplanarPair> pairs = findOutdoorCoplanarFaces(models);
    CHECK(!pairs.empty());
    const std::vector<std::string> said =
        describeOutdoorCoplanarGroups(models, pairs, {lowered.buildings[0].faceParts});
    bool identical = false;
    bool through = false;

    for (const std::string &sentence : said)
    {
        MESSAGE(sentence);
        identical = identical || (sentence.find("part:a and building:home part:b") != std::string::npos
            && sentence.find("identical") != std::string::npos);
        through = through || (sentence.find("part:c") != std::string::npos
            && sentence.find("run through each other") != std::string::npos);
    }

    CHECK(identical);
    CHECK(through);
    // A pair the original has at the same place (the same two textures, plane and place) is the original's.
    std::vector<OutdoorCoplanarPair> marked = pairs;
    CHECK(markOutdoorPairsAsOriginal(models, marked, outdoorCoplanarPlaces(models, pairs)) == pairs.size());
    // One face 1 unit in front of another counts (a picture on a board); 2 units do not.
    for (const double apart : {1.0, 2.0})
    {
        Game::OutdoorBModel board;
        board.name = "thing:board";
        OutdoorModelBuilder builder(board);
        builder.addSurface({{0.0, 0.0, 0.0}, {128.0, 0.0, 0.0}, {128.0, 0.0, 64.0}, {0.0, 0.0, 64.0}}, "a", 0);
        builder.addSurface({{0.0, -apart, 0.0}, {128.0, -apart, 0.0}, {128.0, -apart, 64.0}, {0.0, -apart, 64.0}},
            "b", 0);
        builder.finish();
        CHECK(findOutdoorCoplanarFaces({board}).size() == (apart == 1.0 ? 1u : 0u));
        // Not drawn, it does not count.
        builder.hide(0);
        CHECK(findOutdoorCoplanarFaces({board}).size() == 0u);
    }

    // A board's face in the plane of the picture over it is hidden; one an inch behind is not.
    Game::OutdoorBModel sign;
    OutdoorModelBuilder signBuilder(sign);
    signBuilder.addSurface({{0.0, 0.0, 0.0}, {128.0, 0.0, 0.0}, {128.0, 0.0, 64.0}, {0.0, 0.0, 64.0}}, "a", 0);
    signBuilder.addSurface({{0.0, 4.0, 0.0}, {128.0, 4.0, 0.0}, {128.0, 4.0, 64.0}, {0.0, 4.0, 64.0}}, "a", 0);
    signBuilder.addSurface({{0.0, 0.0, 0.0}, {128.0, 0.0, 0.0}, {128.0, 0.0, 64.0}, {0.0, 0.0, 64.0}}, "p", 0);
    signBuilder.hideUnder(0, 2, 2, 3);
    CHECK((sign.faces[0].attributes & InvisibleBit) != 0);
    CHECK((sign.faces[1].attributes & InvisibleBit) == 0);
}

TEST_CASE("the studio's own z-fighting: railing corners, boards under pictures, gable ridge beams, stall sills")
{
    // A flat top railed on all four walls with a sign board, a gable with eaves 96 and a ridge beam, and an open
    // stall with a sill on one wall: no faces in one plane over each other.
    LoweredOutdoorMap lowered = loweredBuildings("      - {building: building:home, at: [40, 40], facing: s, "
        "door: none, eaves: 0, fascia: 0, roof: flat, textures: {railing: t14abcd11}, parts: [{id: deck, size: [1024, "
        "768], wall_height: 384, signs: [{wall: s, bay: 2, texture: sgmagic, size: [64, 64], bottom: 320, out: 8}, "
        "{wall: e, bay: 1, texture: sgmagic, size: [64, 64], bottom: 152, out: 56, hang: true}], railing: {height: "
        "208}}]}\n"
        "      - {building: building:home, at: [50, 40], facing: s, door: none, roof: gable, eaves: 96, fascia: 16, "
        "ridge: 16, parts: [{size: [512, 768], roof_height: 400}]}\n"
        "      - {building: building:home, at: [60, 40], facing: s, door: none, roof: flat, parts: [{size: [896, 384], "
        "posts: 16, post_every: 256, sill: 128, sill_walls: [n, e]}]}\n");
    REQUIRE(lowered.buildings.size() == 3);
    std::vector<Game::OutdoorBModel> models;

    for (OutdoorBuildingPlan &building : lowered.buildings)
    {
        models.push_back(raiseOutdoorBuilding(building));
    }

    for (const OutdoorCoplanarPair &pair : findOutdoorCoplanarFaces(models))
    {
        FAIL_CHECK(describeOutdoorCoplanarPair(models, pair, {}));
    }

    // A signpost's boards and a free sign's: pictures on boards that reach them, no pairs.
    std::vector<ProjectIssue> issues;
    IdsLock ids;
    const OutdoorThings things = thingsOf("structures:\n"
        "  - {id: thing:post, kind: sign, at: [56, 50], height: 272, width: 112, post: 32, board_height: 32, arms: "
        "[{title: West, toward: w, board: s_west}, {title: South, toward: s}], textures: {board: s_south}}\n"
        "  - {id: thing:sign, kind: sign, at: [58, 50], textures: {board: sgalch}}\n", issues, ids);
    REQUIRE(issues.empty());
    CHECK(findOutdoorCoplanarFaces(things.models).empty());
    CHECK(facesWith(things.models[1], "sgalch").size() == 2);
}

TEST_CASE("stairs without `ramp` lay their treads in `top`, their risers in `wall`")
{
    std::vector<ProjectIssue> issues;
    IdsLock ids;
    const OutdoorThings things = thingsOf("structures:\n"
        "  - {id: thing:steps, kind: stairs, line: [[50, 50], [51, 50]], width: 256, rise: 128, tread: 32, "
        "textures: {wall: t19b10a, top: t19a05a}}\n", issues, ids);
    REQUIRE(issues.empty());
    REQUIRE(things.models.size() == 1);
    CHECK(facesWith(things.models[0], "t19a05a", 3).size() == 4);
    CHECK(facesWith(things.models[0], "t19b10a", 3).empty());
    CHECK(!facesWith(things.models[0], "t19b10a", 1).empty());
}

TEST_CASE("a town wall with battlements: merlons along its outer side, no faces over each other at its corners")
{
    std::vector<ProjectIssue> issues;
    IdsLock ids;
    const OutdoorThings things = thingsOf("structures:\n"
        "  - {id: thing:town_wall, kind: wall, line: [[50, 50], [54, 50], [54, 53], [50, 53]], closed: true, "
        "height: 384, thickness: 128, battlements: true, gates: [{at: [52, 50], width: 256, height: 256}]}\n",
        issues, ids);
    REQUIRE(issues.empty());
    REQUIRE(things.models.size() == 1);
    for (const OutdoorCoplanarPair &pair : findOutdoorCoplanarFaces(things.models))
    {
        FAIL_CHECK(describeOutdoorCoplanarPair(things.models, pair, {}));
    }
}

TEST_CASE("doors[].same_event_as: three doors of one building on one event, as Buccaneers' Lair's")
{
    const BuiltOutdoor built = builtOutdoor(buildingProject("      - {building: building:home, at: [40, 40], "
        "facing: s, house: 191, title: Lair, parts: [{size: [1024, 768]}], doors: [{wall: e, same_event_as: 0}, "
        "{wall: w, same_event_as: building:home}]}\n", "points:\n  - {id: entrance:north, at: [64, 20], facing: s}\n"),
        "oymap_outdoor_same_door");
    REQUIRE(built.built);
    size_t enters = 0;

    for (size_t at = built.lua.find("evt.EnterHouse(191)"); at != std::string::npos;
         at = built.lua.find("evt.EnterHouse(191)", at + 1))
    {
        ++enters;
    }

    CHECK(enters == 1);
    std::map<int, size_t> faces;

    for (const YAML::Node &face : built.scene["bmodel_faces"]["interactive_faces"])
    {
        ++faces[face["cog_triggered_number"].as<int>()];
    }

    bool three = false;

    for (const std::pair<const int, size_t> &entry : faces)
    {
        three = three || (entry.first != 0 && entry.second == 3);
    }

    CHECK(three);
    // A door that carries another's event has no words of its own; the door it names must have an event.
    CHECK(anyIssue(buildingIssues("house: 191, parts: [{size: [1024, 768]}], doors: [{wall: e, same_event_as: 0, "
        "house: 12}]"), "leave out its own `house`"));
    CHECK(anyIssue(buildingIssues("house: 191, parts: [{size: [1024, 768]}], doors: [{wall: e, same_event_as: "
        "[1]}]"), "names the door whose event it carries"));
    const BuiltOutdoor nothing = builtOutdoor(buildingProject("      - {building: building:home, at: [40, 40], "
        "facing: s, door: none, parts: [{size: [1024, 768]}], doors: [{wall: e, same_event_as: 0}]}\n",
        "points:\n  - {id: entrance:north, at: [64, 20], facing: s}\n"), "oymap_outdoor_same_door2");
    CHECK_FALSE(nothing.built);
    CHECK(anyIssue(nothing.issues, "carries no event"));
}

TEST_CASE("a porch floor from the land under a plinth; an open part's posts on chosen walls")
{
    for (const bool fromLand : {false, true})
    {
        LoweredOutdoorMap lowered = loweredBuildings(std::string("      - {building: building:home, at: [40, 40], "
            "facing: s, door: none, plinth: 32, textures: {step: t14a09}, parts: [{size: [1024, 768], porches: "
            "[{wall: s, depth: 128, posts: 16, floor: 32") + (fromLand ? ", floor_from: land" : "") + "}]}]}\n");
        const OutdoorBuildingPlan &plan = lowered.buildings[0];
        const Game::OutdoorBModel house = raiseOutdoorBuilding(lowered.buildings[0]);
        const std::vector<const Game::OutdoorBModelFace *> slabs = facesWith(house, "t14a09", 3);
        REQUIRE(slabs.size() == 1);
        CAPTURE(fromLand);
        CHECK(heightsOf(house, *slabs[0])[0] == std::lround(plan.base + (fromLand ? 0.0 : 32.0)));
    }

    CHECK(anyIssue(buildingIssues("door: none, parts: [{size: [1024, 768], porches: [{wall: s, floor: 32, "
        "floor_from: roof}]}]"), "floor_from is `foot`"));

    // A porch on posts against the house: posts on its south wall only (and that wall's corners).
    LoweredOutdoorMap lowered = loweredBuildings("      - {building: building:home, at: [40, 40], facing: s, "
        "door: none, eaves: 0, fascia: 0, textures: {post: t14abcd10, sill: t14a01}, parts: [{size: [512, 512], "
        "posts: 32, post_every: 256, post_walls: [s], sill: 96, roof: flat}]}\n");
    const Game::OutdoorBModel porch = raiseOutdoorBuilding(lowered.buildings[0]);
    // The south wall's two corners and one between.
    CHECK(facesWith(porch, "t14abcd10", 3).size() == 3);
    // The low wall only between the south wall's posts (two pieces).
    CHECK(facesWith(porch, "t14a01", 3).size() == 2);
    CHECK(anyIssue(buildingIssues("door: none, parts: [{size: [512, 512], posts: 32, post_walls: [s], sill: 96, "
        "sill_walls: [n]}]"), "has none (`post_walls`)"));
    CHECK(anyIssue(buildingIssues("door: none, parts: [{size: [512, 512], post_walls: [s]}]"),
        "belongs to an open part"));
}

TEST_CASE("a fence: posts on the ground along its line, rails between them, a barrier not drawn")
{
    std::vector<ProjectIssue> issues;
    IdsLock ids;
    const OutdoorThings things = thingsOf("structures:\n"
        "  - {id: thing:pen, kind: fence, line: [[50, 50], [52, 50], [52, 51]], every: 192, rails: 2, "
        "textures: {post: t14a07, rail: trim11_32}}\n", issues, ids);
    REQUIRE(issues.empty());
    REQUIRE(things.models.size() == 1);
    const Game::OutdoorBModel &fence = things.models[0];
    // 1024 in 6 gaps and 512 in 3: 9 gaps, 10 posts with their tops 112 over the ground.
    const std::vector<const Game::OutdoorBModelFace *> tops = facesWith(fence, "t14a07", 3);
    CHECK(tops.size() == 10);
    CHECK(heightsOf(fence, *tops[0])[0] == 640 + 112);
    // Two rails between each two posts: their tops.
    CHECK(facesWith(fence, "trim11_32", 3).size() == 18);
    size_t barriers = 0;

    for (const Game::OutdoorBModelFace &face : fence.faces)
    {
        barriers += (face.attributes & InvisibleBit) != 0 ? 1 : 0;
    }

    CHECK(barriers == 18);
    CHECK(findOutdoorCoplanarFaces(things.models).empty());
    std::vector<ProjectIssue> refused;
    IdsLock lock;
    thingsOf("structures:\n  - {id: thing:f, kind: fence, line: [[50, 50], [52, 50]], rails: 9}\n", refused, lock);
    CHECK(anyIssue(refused, "a fence is 32 to 512 high"));
}

TEST_CASE("a waterfall: top water to the lip, a free sheet to the pool, foot water, rock sides, banks and the land cut")
{
    struct Falls
    {
        LoweredOutdoorMap lowered;
        OutdoorThings things;
        std::vector<ProjectIssue> issues;
    };
    const auto falls = [](const std::string &entry)
    {
        Falls result;
        Project project = buildingProject("      - {building: building:home, at: [40, 40], facing: s}\n",
            "structures:\n  - {id: thing:falls, kind: waterfall, " + entry + "}\n");
        // Low land (640) in the north, high (1664) in the south, a cliff along y 64.
        ProjectFile &sketch = project.files["sketch.yml"];
        const std::string bands = "    - {band: band:low, polygon: [[0, 0], [128, 0], [128, 128], [0, 128]]}\n";
        sketch.text.replace(sketch.text.find(bands), bands.size(),
            "    - {band: band:low, polygon: [[0, 0], [128, 0], [128, 64], [0, 64]]}\n"
            "    - {band: band:high, polygon: [[0, 64], [128, 64], [128, 128], [0, 128]]}\n"
            "  cliffs:\n    - {line: [[0, 64], [128, 64]], drop: 1024, down: left}\n");
        sketch.document = YAML::Load(sketch.text);
        ProjectFile &plan = project.files["plan.yml"];
        plan.text.replace(plan.text.find("height_bands:\n"), 14, "height_bands:\n  - {id: band:high, range: "
            "[1600, 1728]}\n");
        plan.document = YAML::Load(plan.text);
        std::vector<ProjectIssue> lowering;

        if (!lowerOutdoorProject(project, result.lowered, result.issues))
        {
            return result;
        }

        std::vector<std::string> warnings;
        IdsLock ids;
        OutdoorEventWords words(project, {}, ids, result.issues);
        raiseOutdoorThings(project, result.lowered, {}, ids, words, result.things, result.issues, warnings);
        return result;
    };
    const auto ground = [](const LoweredOutdoorMap &lowered, int x, int y)
    {
        return lowered.ground[static_cast<size_t>(y) * OutdoorNodeCount + x];
    };
    const Falls upright = falls("line: [[50, 64], [50, 60]], top: 1664, foot: 640, width: 512, rocks: false, "
        "banks: false");
    REQUIRE(upright.issues.empty());
    REQUIRE(upright.things.models.size() == 1);
    const Game::OutdoorBModel &model = upright.things.models[0];
    const uint32_t fluid = Game::faceAttributeBit(Game::FaceAttribute::Fluid);
    const uint32_t flowDown = Game::faceAttributeBit(Game::FaceAttribute::FlowDown);
    const uint32_t passes = Game::faceAttributeBit(Game::FaceAttribute::Untouchable);
    std::set<int> levels;
    std::vector<const Game::OutdoorBModelFace *> sheets;
    std::vector<const Game::OutdoorBModelFace *> ramps;

    for (const Game::OutdoorBModelFace &face : model.faces)
    {
        CHECK(face.textureName == "wtrtyl");
        CHECK((face.attributes & flowDown) != 0);
        const std::array<int, 2> heights = heightsOf(model, face);

        if (heights[1] - heights[0] <= 16)
        {
            // The top water (rising out of the stream, then 2 over it to the lip) and the foot water 2 over the
            // pool: liquid, walked on.
            CHECK((face.attributes & fluid) != 0);
            CHECK((face.attributes & passes) == 0);

            if (heights[0] == heights[1])
            {
                levels.insert(heights[0]);
            }
            else
            {
                ramps.push_back(&face);
            }

            continue;
        }

        sheets.push_back(&face);
        CHECK((face.attributes & passes) != 0);
        CHECK((face.attributes & fluid) == 0);
        // The sheet stands free of the land, from the top water's edge to the pool.
        CHECK(heights == std::array<int, 2>{640, 1666});
    }

    CHECK(levels == std::set<int>{642, 1666});
    REQUIRE(ramps.size() == 1);
    CHECK(heightsOf(model, *ramps[0]) == std::array<int, 2>{1652, 1666});
    // One plane, so the game's water has no seam on it.
    REQUIRE(sheets.size() == 1);
    CHECK(sheets[0]->vertexIndices.size() == 4);
    // The land under the lip is cut to the foot; the land up the stream and beside the cut is not.
    CHECK(ground(upright.lowered, 50, 64) <= 640.0);
    CHECK(ground(upright.lowered, 50, 66) > 1600.0);
    CHECK(ground(upright.lowered, 53, 64) > 1600.0);

    // The flow the game gives each triangle of a water face (game/render/WaterGeometry.h waterFaceFlow, FlowDown
    // over a 128-texel liquid): the same on every triangle of a sheet, or its picture tears along the diagonals.
    const auto flows = [](const Game::OutdoorBModel &of, const Game::OutdoorBModelFace &face)
    {
        std::vector<std::array<double, 2>> found;

        for (size_t corner = 1; corner + 1 < face.vertexIndices.size(); ++corner)
        {
            std::array<std::array<double, 3>, 3> p = {};
            std::array<std::array<double, 2>, 3> t = {};
            const std::array<size_t, 3> at = {0, corner, corner + 1};

            for (size_t index = 0; index < 3; ++index)
            {
                const Game::OutdoorBModelVertex &vertex = of.vertices[face.vertexIndices[at[index]]];
                p[index] = {static_cast<double>(vertex.x), static_cast<double>(vertex.y),
                    static_cast<double>(vertex.z)};
                t[index] = {face.textureUs[at[index]] / 128.0, face.textureVs[at[index]] / 128.0};
            }

            const std::array<double, 3> e1 = {p[1][0] - p[0][0], p[1][1] - p[0][1], p[1][2] - p[0][2]};
            const std::array<double, 3> e2 = {p[2][0] - p[0][0], p[2][1] - p[0][1], p[2][2] - p[0][2]};
            const double u1 = t[1][0] - t[0][0];
            const double v1 = t[1][1] - t[0][1];
            const double u2 = t[2][0] - t[0][0];
            const double v2 = t[2][1] - t[0][1];
            const double determinant = u1 * v2 - v1 * u2;
            REQUIRE(std::fabs(determinant) > 1.0e-6);
            std::array<double, 3> n = {e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2],
                e1[0] * e2[1] - e1[1] * e2[0]};
            const double length = std::sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2]);
            n = {n[0] / length, n[1] / length, n[2] / length};
            std::array<double, 3> across = {1.0, 0.0, 0.0};

            if (std::fabs(n[2]) <= 0.99)
            {
                const double level = std::sqrt(n[0] * n[0] + n[1] * n[1]);
                across = {-n[1] / level, n[0] / level, 0.0};
            }

            const std::array<double, 3> up = {n[1] * across[2] - n[2] * across[1],
                n[2] * across[0] - n[0] * across[2], n[0] * across[1] - n[1] * across[0]};
            std::array<double, 3> velocity = {};

            for (size_t axis = 0; axis < 3; ++axis)
            {
                velocity[axis] = (e2[axis] * u1 - e1[axis] * u2) / determinant;
            }

            found.push_back({velocity[0] * across[0] + velocity[1] * across[1] + velocity[2] * across[2],
                velocity[0] * up[0] + velocity[1] * up[1] + velocity[2] * up[2]});
        }

        return found;
    };
    const std::vector<std::array<double, 2>> sheetFlows = flows(model, *sheets[0]);
    REQUIRE(sheetFlows.size() == 2);
    CHECK(sheetFlows[0][0] == doctest::Approx(sheetFlows[1][0]).epsilon(0.01));
    CHECK(sheetFlows[0][1] == doctest::Approx(sheetFlows[1][1]).epsilon(0.01));

    // Leaning, fanning out, with rock sides and banks: the sheet's foot stands out, the crags in the world's rock,
    // the banks in its dirt tile; still one plane.
    const Falls leaning = falls("line: [[50, 64], [50, 60]], top: 1664, foot: 640, width: 512, lean: 384, "
        "spread: 1.7");
    REQUIRE(leaning.issues.empty());
    REQUIRE(leaning.things.models.size() == 1);
    int dirtFaces = 0;
    int leaningSheets = 0;

    for (const Game::OutdoorBModelFace &face : leaning.things.models[0].faces)
    {
        dirtFaces += face.textureName == "dirttyl" ? 1 : 0;

        if ((face.attributes & passes) != 0)
        {
            ++leaningSheets;
            const std::vector<std::array<double, 2>> leaningFlows = flows(leaning.things.models[0], face);
            CHECK(leaningFlows[0][1] == doctest::Approx(leaningFlows[1][1]).epsilon(0.01));
            CHECK(std::fabs(leaningFlows[0][0] - leaningFlows[1][0]) < 0.01);
        }
    }

    CHECK(leaningSheets == 1);
    // F29: with rock sides only the land under the sheet is cut (beside it a pit lay beyond the crags); with none,
    // every node whose cell the sheet crosses, as the upright fall above.
    CHECK(ground(leaning.lowered, 50, 64) <= 640.0);
    CHECK(ground(leaning.lowered, 51, 64) > 1600.0);
    CHECK(ground(leaning.lowered, 49, 64) > 1600.0);
    CHECK(ground(upright.lowered, 51, 64) <= 640.0);
    CHECK(ground(upright.lowered, 49, 64) <= 640.0);
    // The crags and the two banks (two slopes of triangles every 128 along the top water's 1088, and an end).
    CHECK(dirtFaces > 40 + 2 * (2 * 2 * 9 + 1) - 1);
    CHECK(leaning.things.models[0].faces.size() > model.faces.size());
    CHECK(anyIssue(falls("line: [[50, 64], [50, 60]], top: 1664, foot: 640, width: 512, "
        "textures: {bank: {texture: x}}").issues, "a waterfall's textures are names"));

    // Refused: a fall that does not fall; one away from any river without a width.
    CHECK(anyIssue(falls("line: [[50, 64], [50, 60]], top: 1664, foot: 1640, width: 512").issues,
        "a waterfall falls"));
    CHECK(anyIssue(falls("line: [[50, 64], [50, 60]], top: 1664, foot: 640").issues, "needs a `width`"));

    // A chute before the sheet (a rim fall down the hull's deck, D-112): two planes meeting at the chute's end, the
    // chute from the lip's level down `drop`, the sheet from there to the foot; each plane flows one way.
    const Falls chuted = falls("line: [[50, 64], [50, 60]], top: 1664, foot: 640, width: 512, rocks: false, "
        "banks: false, chute: [600, 300], lean: 100");
    REQUIRE(chuted.issues.empty());
    REQUIRE(chuted.things.models.size() == 1);
    std::vector<std::array<int, 2>> drops;

    for (const Game::OutdoorBModelFace &face : chuted.things.models[0].faces)
    {
        const std::array<int, 2> heights = heightsOf(chuted.things.models[0], face);

        if (heights[1] - heights[0] > 16)
        {
            drops.push_back(heights);
            const std::vector<std::array<double, 2>> chuteFlows = flows(chuted.things.models[0], face);
            REQUIRE(chuteFlows.size() == 2);
            CHECK(chuteFlows[0][1] == doctest::Approx(chuteFlows[1][1]).epsilon(0.01));
        }
    }

    std::sort(drops.begin(), drops.end());
    CHECK(drops == std::vector<std::array<int, 2>>{{640, 1366}, {1366, 1666}});
    CHECK(anyIssue(falls("line: [[50, 64], [50, 60]], top: 1664, foot: 640, width: 512, chute: [600, 2000]").issues,
        "`chute` is [out, drop]"));
}

// ---- Ways in (outdoor code batch O-B): cave mouths, hatches, arched heads, door dressing ----

namespace
{
struct CaveBuild
{
    LoweredOutdoorMap lowered;
    OutdoorThings things;
    std::vector<ProjectIssue> issues;
    std::vector<std::string> warnings;
    bool lowered_ = false;
};

CaveBuild caveBuild(const std::string &structures, const std::string &heights = {})
{
    CaveBuild build;
    Project project = buildingProject("      - {building: building:home, at: [40, 40], facing: s}\n",
        "structures:\n" + structures);

    if (!heights.empty())
    {
        ProjectFile &sketch = project.files["sketch.yml"];
        const std::string bands = "    - {band: band:low, polygon: [[0, 0], [128, 0], [128, 128], [0, 128]]}\n";
        sketch.text.replace(sketch.text.find(bands), bands.size(), bands + heights);
        sketch.document = YAML::Load(sketch.text);
    }

    build.lowered_ = lowerOutdoorProject(project, build.lowered, build.issues);

    if (build.lowered_)
    {
        IdsLock ids;
        OutdoorEventWords words(project, {}, ids, build.issues);
        raiseOutdoorThings(project, build.lowered, {}, ids, words, build.things, build.issues, build.warnings);
    }

    build.warnings.insert(build.warnings.end(), build.lowered.warnings.begin(), build.lowered.warnings.end());
    return build;
}

bool anyWarning(const std::vector<std::string> &warnings, const std::string &fragment)
{
    return std::any_of(warnings.begin(), warnings.end(), [&fragment](const std::string &warning)
    {
        return warning.find(fragment) != std::string::npos;
    });
}

int nodeHeight(const LoweredOutdoorMap &lowered, int x, int y)
{
    return lowered.samples[static_cast<size_t>(y) * 128 + x] * 32;
}

const Game::OutdoorBModel *modelNamed(const OutdoorThings &things, const std::string &name)
{
    for (const Game::OutdoorBModel &model : things.models)
    {
        if (model.name == name)
        {
            return &model;
        }
    }

    return nullptr;
}
}

TEST_CASE("an arch head: round rises half its width, pointed meets at the top, both convex and symmetric")
{
    for (const char *pForm : {"round", "pointed"})
    {
        for (const int sides : {2, 5, 6, 8})
        {
            const std::vector<std::array<double, 2>> head = outdoorArchHead(128.0, 256.0, pForm, sides);
            REQUIRE(head.size() >= 3);
            CHECK(head.front()[0] == doctest::Approx(-64.0));
            CHECK(head.back()[0] == doctest::Approx(64.0));
            double top = 0.0;

            for (size_t index = 0; index < head.size(); ++index)
            {
                CHECK(head[index][0] == doctest::Approx(-head[head.size() - 1 - index][0]));
                CHECK(head[index][1] == doctest::Approx(head[head.size() - 1 - index][1]));
                top = std::max(top, head[index][1]);
            }

            // An odd number of round segments has no point at the very top.
            CHECK(top >= 256.0 * 0.98);
            CHECK(top <= 256.0 + 1.0e-6);
            const double spring = head.front()[1];
            CHECK(spring == doctest::Approx(std::string(pForm) == "round" ? 192.0 : 256.0 - 128.0 * std::sqrt(3.0)
                * 0.5).epsilon(0.001));

            // Convex: every turn along the head goes the same way.
            for (size_t index = 0; index + 2 < head.size(); ++index)
            {
                const double cross = (head[index + 1][0] - head[index][0]) * (head[index + 2][1] - head[index][1])
                    - (head[index + 1][1] - head[index][1]) * (head[index + 2][0] - head[index][0]);
                CHECK(cross <= 1.0e-6);
            }
        }
    }

    // A low opening: the head rises no more than the opening is high.
    const std::vector<std::array<double, 2>> low = outdoorArchHead(512.0, 128.0, "round", 6);
    CHECK(low.front()[1] == doctest::Approx(0.0));
}

TEST_CASE("a cave mouth: a shell without floor or back, a tunnel to one dark face, the land set under it")
{
    // A mouth looking south at the middle of cells 49 to 51; the hill behind it.
    const CaveBuild build = caveBuild("  - {id: thing:cave, kind: cave_mouth, at: [50, 50], size: [1024, 1024], "
        "crest: 736, mouth: {width: 512, height: 384, depth: 256}, title: Enter the Cave, hint: A Cave, "
        "into: {map: d49.blv, at: [0, 0, 0], facing: 0}}\n",
        "  ridges:\n    - {line: [[44, 48], [56, 48]], height: 1440, width: 1}\n");

    for (const ProjectIssue &issue : build.issues)
    {
        MESSAGE(issue.path << ": " << issue.message);
    }

    REQUIRE(build.issues.empty());
    const Game::OutdoorBModel *pCave = modelNamed(build.things, "thing:cave");
    REQUIRE(pCave != nullptr);
    // Measured: Yaardrake's shell and mouth have 104 faces; this one the same order.
    CHECK(pCave->faces.size() >= 60);
    CHECK(pCave->faces.size() <= 160);
    // The floor: the land at the front's middle (640); front row and the shoulder at it, the back row at the crest.
    // F8: the side edges at the shoulder rise to the shell as far as the mouth's floor allows (a step).
    for (int x = 49; x <= 51; ++x)
    {
        CHECK(nodeHeight(build.lowered, x, 51) == 640);
        CHECK(nodeHeight(build.lowered, x, 50) == (x == 50 ? 640 : 672));
        CHECK(nodeHeight(build.lowered, x, 49) == 640 + 736);
    }

    CHECK_FALSE(anyWarning(build.warnings, "lies lower than its crest"));
    size_t doors = 0;
    uint16_t doorEvent = 0;
    std::set<uint16_t> others;

    for (const Game::OutdoorBModelFace &face : pCave->faces)
    {
        if (face.textureName == "solid01")
        {
            ++doors;
            doorEvent = face.cogTriggeredNumber;
        }
        else
        {
            others.insert(face.cogTriggeredNumber);
            CHECK(face.textureName == "dirttyl");
        }
    }

    CHECK(doors == 1);
    CHECK(doorEvent != 0);
    REQUIRE(others.size() == 1);
    CHECK(*others.begin() != doorEvent);
    // Within the footprint, from the floor to the crest; nothing below the floor (no floor face is needed).
    CHECK(pCave->minX >= (49 - 64) * 512 - 1);
    CHECK(pCave->maxX <= (51 - 64) * 512 + 1);
    CHECK(pCave->minZ >= 640 - 1);
    CHECK(pCave->maxZ <= 640 + 736 + 64 + 1);
    // Every face is a triangle but the dark face; no face lies flat on the land.
    for (const Game::OutdoorBModelFace &face : pCave->faces)
    {
        if (face.textureName != "solid01")
        {
            CHECK(face.vertexIndices.size() == 3);
        }

        bool allOnFloor = true;

        for (const uint16_t index : face.vertexIndices)
        {
            allOnFloor = allOnFloor && pCave->vertices[index].z <= 641;
        }

        CHECK_FALSE(allOnFloor);
    }

    CHECK(findOutdoorCoplanarFaces(build.things.models).empty());
}

TEST_CASE("a cave mouth's facets come from its seed, its land warns when the hill behind is lower than its crest")
{
    const auto cave = [](const std::string &more)
    {
        return caveBuild("  - {id: thing:cave, kind: cave_mouth, at: [50, 50], turn: 90, title: In, into: {map: "
            "d49.blv, at: [0, 0, 0], facing: 0}" + more + "}\n");
    };
    const CaveBuild first = cave("");
    const CaveBuild again = cave("");
    const CaveBuild other = cave(", seed: 7");
    const CaveBuild smooth = cave(", roughness: 0");
    REQUIRE(first.issues.empty());
    const Game::OutdoorBModel *pFirst = modelNamed(first.things, "thing:cave");
    const Game::OutdoorBModel *pAgain = modelNamed(again.things, "thing:cave");
    const Game::OutdoorBModel *pOther = modelNamed(other.things, "thing:cave");
    const Game::OutdoorBModel *pSmooth = modelNamed(smooth.things, "thing:cave");
    REQUIRE((pFirst && pAgain && pOther && pSmooth));
    const auto sameVertices = [](const Game::OutdoorBModel &a, const Game::OutdoorBModel &b)
    {
        if (a.vertices.size() != b.vertices.size())
        {
            return false;
        }

        for (size_t index = 0; index < a.vertices.size(); ++index)
        {
            if (a.vertices[index].x != b.vertices[index].x || a.vertices[index].y != b.vertices[index].y
                || a.vertices[index].z != b.vertices[index].z)
            {
                return false;
            }
        }

        return true;
    };
    CHECK(sameVertices(*pFirst, *pAgain));
    CHECK_FALSE(sameVertices(*pFirst, *pOther));
    CHECK_FALSE(sameVertices(*pFirst, *pSmooth));
    // Turned 90: it looks west; the back row (x 51) stands at the crest, the front (x 49) at the floor. F8: the
    // level land behind it rises to the crest one cell back, so no dome stands over it.
    CHECK(nodeHeight(first.lowered, 49, 50) == 640);
    CHECK(nodeHeight(first.lowered, 51, 50) > 640 + 384);
    CHECK(nodeHeight(first.lowered, 52, 50) >= nodeHeight(first.lowered, 51, 50));
    CHECK(nodeHeight(first.lowered, 53, 50) == 640);
    CHECK_FALSE(anyWarning(first.warnings, "lies lower than its crest"));
    CHECK_FALSE(anyWarning(first.warnings, "caves.dome"));
    // The dark face looks west.
    for (const Game::OutdoorBModelFace &face : pFirst->faces)
    {
        if (face.textureName == "solid01")
        {
            CHECK(faceNormal(*pFirst, face)[0] < -0.9);
        }
    }
}

TEST_CASE("a free barrow: closed all round on level land; a mouth with a door slab in a flat front")
{
    const CaveBuild barrow = caveBuild("  - {id: thing:barrow, kind: cave_mouth, at: [50, 50], free: true, "
        "size: [1536, 1536], title: Barrow, into: {map: d26.blv, at: [0, 0, 0], facing: 0}}\n");
    REQUIRE(barrow.issues.empty());
    CHECK_FALSE(anyWarning(barrow.warnings, "lies lower than its crest"));

    for (int y = 48; y <= 52; ++y)
    {
        for (int x = 49; x <= 51; ++x)
        {
            CHECK(nodeHeight(barrow.lowered, x, y) == 640);
        }
    }

    const Game::OutdoorBModel *pBarrow = modelNamed(barrow.things, "thing:barrow");
    REQUIRE(pBarrow != nullptr);
    CHECK(pBarrow->maxZ >= 640 + 384 + 72);
    // Its back is closed: faces look north.
    CHECK(std::any_of(pBarrow->faces.begin(), pBarrow->faces.end(), [&](const Game::OutdoorBModelFace &face)
    {
        return faceNormal(*pBarrow, face)[1] > 0.5;
    }));

    const CaveBuild crypt = caveBuild("  - {id: thing:crypt, kind: cave_mouth, at: [50, 50], mouth: {form: door}, "
        "title: Crypt, hint: A crypt, into: {map: d26.blv, at: [0, 0, 0], facing: 0}}\n");
    REQUIRE(crypt.issues.empty());
    const Game::OutdoorBModel *pCrypt = modelNamed(crypt.things, "thing:crypt");
    REQUIRE(pCrypt != nullptr);
    size_t slabs = 0;

    for (const Game::OutdoorBModelFace &face : pCrypt->faces)
    {
        if (face.textureName == "t14c03")
        {
            ++slabs;
            // A flat head: four corners, 192 x 320.
            CHECK(face.vertexIndices.size() == 4);
        }
    }

    CHECK(slabs == 1);
}

TEST_CASE("hatches: a wedge rising from its dark mouth to its back, a pit's rim round a dark shaft")
{
    const CaveBuild wedge = caveBuild("  - {id: thing:hatch, kind: hatch, at: [50, 50], title: Down, into: {map: "
        "d07.blv, at: [0, 0, 0], facing: 0}}\n");
    REQUIRE(wedge.issues.empty());
    const Game::OutdoorBModel *pWedge = modelNamed(wedge.things, "thing:hatch");
    REQUIRE(pWedge != nullptr);
    // CoFent_S has 24 faces.
    CHECK(pWedge->faces.size() >= 10);
    CHECK(pWedge->faces.size() <= 30);
    CHECK(pWedge->maxZ == 640 + 192);
    // Front row (south, y 50.5 rounds to none: footprint 512 from 49.5 to 50.5) is at the floor where nodes lie.
    CHECK(std::count_if(pWedge->faces.begin(), pWedge->faces.end(), [](const Game::OutdoorBModelFace &face)
    {
        return face.textureName == "solid01";
    }) == 1);
    // Both ends of the front close alike: every face has its mirror across the wedge's middle (the mound's left half
    // splits its quads on the mirrored diagonal; one diagonal everywhere laid a triangle along X1's land edge).
    int minX = std::numeric_limits<int>::max();
    int maxX = std::numeric_limits<int>::min();

    for (const Game::OutdoorBModelVertex &vertex : pWedge->vertices)
    {
        minX = std::min(minX, vertex.x);
        maxX = std::max(maxX, vertex.x);
    }

    const auto cornersOf = [pWedge](const Game::OutdoorBModelFace &face, int mirrorSum)
    {
        std::vector<std::array<int, 3>> corners;

        for (const uint16_t index : face.vertexIndices)
        {
            const Game::OutdoorBModelVertex &vertex = pWedge->vertices[index];
            corners.push_back({mirrorSum == 0 ? vertex.x : mirrorSum - vertex.x, vertex.y, vertex.z});
        }

        std::sort(corners.begin(), corners.end());
        return corners;
    };
    const auto near = [](const std::vector<std::array<int, 3>> &a, const std::vector<std::array<int, 3>> &b)
    {
        if (a.size() != b.size())
        {
            return false;
        }

        for (size_t index = 0; index < a.size(); ++index)
        {
            for (size_t axis = 0; axis < 3; ++axis)
            {
                if (std::abs(a[index][axis] - b[index][axis]) > 1)
                {
                    return false;
                }
            }
        }

        return true;
    };
    size_t unmirrored = 0;

    for (const Game::OutdoorBModelFace &face : pWedge->faces)
    {
        const std::vector<std::array<int, 3>> mirrored = cornersOf(face, minX + maxX);
        const bool found = std::any_of(pWedge->faces.begin(), pWedge->faces.end(),
            [&](const Game::OutdoorBModelFace &other) { return near(mirrored, cornersOf(other, 0)); });
        unmirrored += found ? 0 : 1;
    }

    CHECK(unmirrored == 0);

    const CaveBuild pit = caveBuild("  - {id: thing:pit, kind: hatch, form: pit, at: [50, 50], title: Down, "
        "hint: A pit, into: {map: d24.blv, at: [0, 0, 0], facing: 0}}\n");
    REQUIRE(pit.issues.empty());
    const Game::OutdoorBModel *pPit = modelNamed(pit.things, "thing:pit");
    REQUIRE(pPit != nullptr);
    // d24entranceA: 13 faces, the rim 64 high, the dark face 16 below its top.
    CHECK(pPit->faces.size() == 13);
    CHECK(pPit->maxZ == 640 + 64);
    size_t dark = 0;

    for (const Game::OutdoorBModelFace &face : pPit->faces)
    {
        if (face.textureName == "solid01")
        {
            ++dark;
            CHECK(pPit->vertices[face.vertexIndices[0]].z == 640 + 48);
            CHECK(faceNormal(*pPit, face)[2] > 0.99);
        }
    }

    CHECK(dark == 1);
    CHECK(findOutdoorCoplanarFaces(pit.things.models).empty());
}

TEST_CASE("cave mouths and hatches refuse what cannot be built")
{
    const auto refused = [](const std::string &structure, const std::string &fragment)
    {
        const CaveBuild build = caveBuild("  - " + structure + "\n");
        CHECK_MESSAGE(anyIssue(build.issues, fragment), structure);
    };
    refused("{id: thing:c, kind: cave_mouth, at: [50, 50], crest: 200}", "the crest stands over the mouth");
    refused("{id: thing:c, kind: cave_mouth, at: [50, 50], mouth: {width: 1000}}", "fits the footprint");
    refused("{id: thing:c, kind: cave_mouth, at: [50, 50], mouth: {depth: 900}}", "three quarters");
    refused("{id: thing:c, kind: cave_mouth, at: [50, 50], roughness: 2}", "roughness is 0");
    refused("{id: thing:c, kind: hatch, form: trapdoor, at: [50, 50]}", "a hatch's form is wedge");
    refused("{id: thing:c, kind: hatch, at: [50, 50], free: true}", "`free` is a cave mouth's word");
}

TEST_CASE("arched heads on a doorway and a wall's gate; a gabled portico over a doorway")
{
    std::vector<ProjectIssue> issues;
    IdsLock ids;
    const OutdoorThings things = thingsOf("structures:\n  - {id: thing:door, kind: doorway, at: [50, 50], arch: pointed, "
        "roof: gable, hood: 128, title: In, into: {map: d01.blv, at: [0, 0, 0], facing: 0}}\n"
        "  - {id: thing:plain, kind: doorway, at: [55, 50], title: In, into: {map: d01.blv, at: [0, 0, 0], "
        "facing: 0}}\n"
        "  - {id: thing:wall, kind: wall, line: [[44, 56], [52, 56]], gates: [{at: [48, 56], width: 384, height: 320, "
        "arch: round}]}\n"
        "  - {id: thing:flat, kind: wall, line: [[44, 58], [52, 58]], gates: [{at: [48, 58], width: 384, "
        "height: 320}]}\n", issues, ids);
    REQUIRE(issues.empty());
    const Game::OutdoorBModel *pDoor = modelNamed(things, "thing:door");
    const Game::OutdoorBModel *pPlain = modelNamed(things, "thing:plain");
    REQUIRE((pDoor && pPlain));
    // The door: one face with the head's points (more than four corners), up to the door's height.
    size_t doorCorners = 0;

    for (const Game::OutdoorBModelFace &face : pDoor->faces)
    {
        if (face.textureName == "t14c03")
        {
            doorCorners = face.vertexIndices.size();
        }
    }

    CHECK(doorCorners > 4);
    // The portico: four faces more than the hooded frame alone would have, the ridge 0.35 of the frame's width up.
    CHECK(pDoor->maxZ == pPlain->maxZ + static_cast<int>(std::lround(192.0 * 0.35)));
    const Game::OutdoorBModel *pWall = modelNamed(things, "thing:wall");
    const Game::OutdoorBModel *pFlat = modelNamed(things, "thing:flat");
    REQUIRE((pWall && pFlat));
    // Six segments: spandrels both sides and a soffit each (18), the flat lintel's underside gone.
    CHECK(pWall->faces.size() >= pFlat->faces.size() + 15);
    size_t soffits = 0;

    for (const Game::OutdoorBModelFace &face : pWall->faces)
    {
        soffits += faceNormal(*pWall, face)[2] < -0.1 ? 1 : 0;
    }

    CHECK(soffits >= 4);
    std::vector<ProjectIssue> refused;
    IdsLock lock;
    thingsOf("structures:\n  - {id: thing:w, kind: wall, line: [[44, 56], [52, 56]], gates: [{at: [48, 56], arch: ogee}]}\n",
        refused, lock);
    CHECK(anyIssue(refused, "a gate's `arch` is round, pointed or segment"));
}

TEST_CASE("door dressing: an arched double door, arched windows, a hood, nested frames and a portcullis")
{
    const auto raised = [](const std::string &fields)
    {
        Project project = buildingProject("      - {building: building:home, at: [40, 40], facing: s, title: Home, "
            "foundation: 0" + fields + "}\n");
        LoweredOutdoorMap lowered;
        std::vector<ProjectIssue> issues;
        const bool ok = lowerOutdoorProject(project, lowered, issues);

        for (const ProjectIssue &issue : issues)
        {
            MESSAGE(issue.path << ": " << issue.message);
        }

        REQUIRE(ok);
        lowered.buildings[0].doors[0].event = 7;
        lowered.buildings[0].nameEvent = 8;
        return raiseOutdoorBuilding(lowered.buildings[0]);
    };
    const auto doorFaces = [](const Game::OutdoorBModel &model)
    {
        std::vector<size_t> found;

        for (size_t index = 0; index < model.faces.size(); ++index)
        {
            if (model.faces[index].cogTriggeredNumber == 7)
            {
                found.push_back(model.faces[index].vertexIndices.size());
            }
        }

        return found;
    };
    const Game::OutdoorBModel plain = raised("");
    CHECK(doorFaces(plain) == std::vector<size_t>{4});
    const Game::OutdoorBModel arched = raised(", door: {arch: round}");
    REQUIRE(doorFaces(arched).size() == 1);
    CHECK(doorFaces(arched)[0] == 2 + 7);
    // The corners over the head: six faces of the wall's own texture.
    CHECK(arched.faces.size() == plain.faces.size() + 6);
    const Game::OutdoorBModel pair = raised(", door: {arch: pointed, leaves: 2}");
    CHECK(doorFaces(pair).size() == 2);
    const Game::OutdoorBModel windows = raised(", windows: all, window_arch: round");
    const Game::OutdoorBModel squareWindows = raised(", windows: all");
    CHECK(windows.faces.size() > squareWindows.faces.size());
    const Game::OutdoorBModel hooded = raised(", door: {hood: 96}");
    // Three blocks of five faces (no bottoms).
    CHECK(hooded.faces.size() == plain.faces.size() + 15);
    CHECK(hooded.minY < plain.minY - 64);
    const Game::OutdoorBModel framed = raised(", wall_height: 512, door: {frame: {steps: 2, step: 32, portcullis: "
        "true}}");
    const Game::OutdoorBModel tall = raised(", wall_height: 512");
    // Two rings of three blocks, and bars that carry the door's event.
    CHECK(framed.faces.size() > tall.faces.size() + 30);
    CHECK(doorFaces(framed).size() > 10);
    std::vector<ProjectIssue> issues;
    LoweredOutdoorMap lowered;
    CHECK_FALSE(lowerOutdoorProject(buildingProject("      - {building: building:home, at: [40, 40], facing: s, "
        "door: {leaves: 3}}\n"), lowered, issues));
    CHECK(anyIssue(issues, "`leaves` is 1 or 2"));
}

// ---- Catalog batch O-A: map-wide plumbing (leave, flags, flying, invisible faces, scatter words, terraces) ----

namespace
{
Project withAtmosphere(Project project, const std::string &text)
{
    ProjectFile air;
    air.name = "atmosphere.yml";
    air.text = text;
    air.document = YAML::Load(text);

    for (const ProjectFileKind &kind : projectFileKinds())
    {
        if (air.name == kind.pName)
        {
            air.schema = kind.pSchema;
        }
    }

    project.files[air.name] = air;
    return project;
}

// The building project with a lake in its plan.
Project withLake(Project project)
{
    ProjectFile &plan = project.files["plan.yml"];
    plan.text += "  - id: water:lake\n    kind: water\n";
    plan.document = YAML::Load(plan.text);
    return project;
}

const char *HomePlot = "      - {building: building:home, at: [40, 40], facing: s}\n";
}

TEST_CASE("O-A: an event on leaving the map goes into onLeave; a timer at a flying party into levitateTrapEvents")
{
    const BuiltOutdoor built = builtOutdoor(buildingProject(HomePlot, "events:\n"
        "  - {id: evt:heart, trigger: leave, condition: {qbit: 12}, effects: [{qbit: 13}]}\n"
        "  - {id: evt:anti_fly, trigger: timer, every: 10, when_flying: true, condition: {not: {qbit: 1180}}, "
        "effects: [{cast: {spell: 6, from: [-6152, -9208, 2700], to: [0, 0, 0], mastery: master, level: 5}}]}\n"
        "  - {id: evt:hello, trigger: load, effects: [{text: Hello}]}\n"), "oymap_oa_leave");
    REQUIRE(built.built);
    const std::string &lua = built.lua;
    const size_t leave = lua.find("onLeave = {");
    REQUIRE(leave != std::string::npos);
    const int heart = std::atoi(lua.c_str() + leave + 11);
    CHECK(heart != 0);
    CHECK(lua.find("RegisterEvent(" + std::to_string(heart) + ", nil, function()\n"
        "    if not (IsQBitSet(QBit(12))) then\n        return\n    end\n    SetQBit(QBit(13))") != std::string::npos);
    // The load list keeps only the load event; the flying timer is a timer, listed, and its handler returns at once
    // unless the party flies, before its condition (as the original's event 230 of oute3).
    const size_t traps = lua.find("SetMapMetadata({levitateTrapEvents = {");
    REQUIRE(traps != std::string::npos);
    const int antiFly = std::atoi(lua.c_str() + traps + 38);
    CHECK(antiFly != 0);
    CHECK(lua.find("{ eventId = " + std::to_string(antiFly) + ", sourceEventId = " + std::to_string(antiFly)
        + ", triggerStep = 0, origin = \"legacy\", triggerKind = \"timer\", scheduleKind = \"interval\", "
        "intervalHalfMinutes = 10 }") != std::string::npos);
    CHECK(lua.find("RegisterEvent(" + std::to_string(antiFly) + ", nil, function()\n"
        "    if not IsAtLeast(IsFlying, 0) then return end\n    if not (not (IsQBitSet(QBit(1180)))) then")
        != std::string::npos);
    CHECK(lua.find("evt.CastSpell(6, 5, 3, -6152, -9208, 2700, 0, 0, 0)") != std::string::npos);
    const size_t load = lua.find("onLoad = {");
    CHECK(std::atoi(lua.c_str() + load + 10) != heart);
    CHECK(lua.find("onLoad = {" + std::to_string(antiFly)) == std::string::npos);

    // Without them the metadata is as before: no levitateTrapEvents, an empty onLeave.
    const BuiltOutdoor plain = builtOutdoor(buildingProject(HomePlot), "oymap_oa_leave_plain");
    REQUIRE(plain.built);
    CHECK(plain.lua.find("SetMapMetadata({onLoad = {") != std::string::npos);
    CHECK(plain.lua.find("onLeave = {}") != std::string::npos);

    std::vector<ProjectIssue> issues;
    validateOutdoorProject(buildingProject(HomePlot, "events:\n  - {id: evt:a, trigger: load, when_flying: true, "
        "effects: [{text: x}]}\n"), issues);
    CHECK(anyIssue(issues, "`when_flying` is for `trigger: timer`"));
}

TEST_CASE("O-A: atmosphere flags, the flight ceiling and footsteps per tile go into the scene as the shipped ones")
{
    const BuiltOutdoor water = builtOutdoor(withAtmosphere(buildingProject(HomePlot), "format: 0\nceiling: 2000\n"
        "flags: {underwater: true, always_foggy: true}\nfootsteps:\n  - {tiles: [90, 93], walk: 91, run: 52}\n"
        "  - {tile: 0, walk: 91, run: 0}\n"), "oymap_oa_flags");
    REQUIRE(water.built);
    const YAML::Node environment = water.scene["environment"];
    // As elemw.scene.yml: map_extra_bits_raw 68 (underwater 0x04, always foggy 0x40), ceiling 2000.
    CHECK(environment["map_extra_bits_raw"].as<int>() == 68);
    CHECK(environment["day_bits_raw"].as<int>() == 0);
    CHECK(environment["ceiling"].as<int>() == 2000);
    CHECK(environment["flags"]["underwater"].as<bool>());
    CHECK(environment["flags"]["always_foggy"].as<bool>());
    CHECK_FALSE(environment["flags"]["no_terrain"].as<bool>());
    CHECK_FALSE(environment["flags"]["red_fog"].as<bool>());
    const YAML::Node footsteps = water.scene["terrain"]["footstep_sound_overrides"];
    REQUIRE(footsteps.size() == 5);
    CHECK(footsteps[0]["tile_id"].as<int>() == 90);
    CHECK(footsteps[3]["tile_id"].as<int>() == 93);
    CHECK(footsteps[3]["walk_sound_id"].as<int>() == 91);
    CHECK(footsteps[3]["run_sound_id"].as<int>() == 52);
    CHECK(footsteps[4]["tile_id"].as<int>() == 0);

    // The Plane of Air: no terrain and always light (40); the Plane of Fire: always foggy and red fog (192).
    const BuiltOutdoor air = builtOutdoor(withAtmosphere(buildingProject(HomePlot), "format: 0\n"
        "flags: {no_terrain: true, always_light: true}\n"), "oymap_oa_flags_air");
    REQUIRE(air.built);
    CHECK(air.scene["environment"]["map_extra_bits_raw"].as<int>() == 40);
    const BuiltOutdoor fire = builtOutdoor(withAtmosphere(buildingProject(HomePlot), "format: 0\n"
        "flags: {always_foggy: true, red_fog: true, foggy: true}\n"), "oymap_oa_flags_fire");
    REQUIRE(fire.built);
    CHECK(fire.scene["environment"]["map_extra_bits_raw"].as<int>() == 192);
    CHECK(fire.scene["environment"]["day_bits_raw"].as<int>() == 1);

    // None: every flag false, as before.
    const BuiltOutdoor plain = builtOutdoor(buildingProject(HomePlot), "oymap_oa_flags_plain");
    REQUIRE(plain.built);
    CHECK(plain.scene["environment"]["map_extra_bits_raw"].as<int>() == 0);
    CHECK(plain.scene["environment"]["ceiling"].as<int>() == 0);
    CHECK(plain.scene["terrain"]["footstep_sound_overrides"].size() == 0);

    // The atmosphere schema refuses a flag the scene does not have.
    std::vector<ProjectIssue> issues;
    validateProjectSchemas(withAtmosphere(buildingProject(HomePlot), "format: 0\nflags: {lava: true}\n"), issues);
    CHECK_FALSE(issues.empty());
}

TEST_CASE("O-A: invisible plates and lids, barriers, invisible kerbs and ethereal faces")
{
    const uint32_t invisible = 0x00002000;
    const uint32_t plate = 0x04000000;
    const uint32_t untouchable = 0x20000000;
    std::vector<ProjectIssue> issues;
    IdsLock ids;
    const OutdoorThings things = thingsOf("structures:\n"
        "  - {id: thing:tut_plate, kind: platform, at: [50, 50], size: [512, 512], invisible: true, trigger: step, "
        "effects: [{text: Read the sign}]}\n"
        "  - {id: thing:lid, kind: platform, at: [52, 52], size: [1024, 512], height: 192, invisible: true}\n"
        "  - {id: thing:wall, kind: barrier, line: [[70, 70], [72, 70], [72, 72]], height: 384}\n"
        "  - {id: thing:bridge, kind: bridge, line: [[20, 90], [28, 90]], width: 320, kerb_invisible: 96}\n"
        "  - {id: thing:front, kind: platform, at: [56, 56], size: [256, 256], ethereal: true}\n", issues, ids);

    for (const ProjectIssue &issue : issues)
    {
        MESSAGE(issue.path << ": " << issue.message);
    }

    REQUIRE(issues.empty());
    REQUIRE(things.models.size() == 5);
    // The plate: one level face on the land (640), not drawn, a pressure plate with the event.
    const Game::OutdoorBModel &tut = things.models[0];
    REQUIRE(tut.faces.size() == 1);
    CHECK((tut.faces[0].attributes & invisible) != 0);
    CHECK((tut.faces[0].attributes & plate) != 0);
    CHECK(tut.faces[0].cogTriggeredNumber != 0);
    CHECK(tut.faces[0].planeNormalZ == 65536);
    CHECK(tut.vertices[0].z == 640);
    // The lid: one face 192 over the land, no event.
    const Game::OutdoorBModel &lid = things.models[1];
    REQUIRE(lid.faces.size() == 1);
    CHECK((lid.faces[0].attributes & invisible) != 0);
    CHECK((lid.faces[0].attributes & plate) == 0);
    CHECK(lid.vertices[0].z == 832);
    // The barrier: two stretches, two faces each, all upright and not drawn, from the land to 384 over it.
    const Game::OutdoorBModel &wall = things.models[2];
    REQUIRE(wall.faces.size() == 4);

    for (const Game::OutdoorBModelFace &face : wall.faces)
    {
        CHECK((face.attributes & invisible) != 0);
        CHECK(face.planeNormalZ == 0);
        CHECK(face.cogTriggeredNumber == 0);
    }

    CHECK(wall.maxZ == 640 + 384);
    // The bridge: per deck piece two upright faces not drawn, 96 high, on the deck's edges; nothing else hidden.
    size_t hiddenKerbs = 0;

    for (const Game::OutdoorBModelFace &face : things.models[3].faces)
    {
        hiddenKerbs += (face.attributes & invisible) != 0 ? 1 : 0;
        CHECK(((face.attributes & invisible) == 0 || face.planeNormalZ == 0));
    }

    CHECK(hiddenKerbs == 2);
    // Ethereal: every face drawn and walked through.
    for (const Game::OutdoorBModelFace &face : things.models[4].faces)
    {
        CHECK((face.attributes & untouchable) != 0);
        CHECK((face.attributes & invisible) == 0);
    }

    const auto refused = [](const std::string &structure, const std::string &fragment)
    {
        std::vector<ProjectIssue> found;
        IdsLock lock;
        thingsOf("structures:\n" + structure, found, lock);
        CAPTURE(structure);
        CHECK(anyIssue(found, fragment));
    };
    refused("  - {id: thing:b, kind: barrier, line: [[70, 70], [72, 70]], effects: [{text: x}]}\n",
        "a barrier is never used");
    refused("  - {id: thing:b, kind: barrier, line: [[70, 70], [72, 70]], height: 8}\n", "a barrier stands from");
    refused("  - {id: thing:b, kind: bridge, line: [[20, 90], [28, 90]], kerb_invisible: 2000}\n",
        "invisible kerbs");
    refused("  - {id: thing:p, kind: platform, at: [50, 50], size: [512, 512], height: 0}\n", "a `height` of 8");
}

TEST_CASE("O-A: scatter groups, a click on every decoration, things on water and floating, and a mixed stand")
{
    // The repository's own assets, read only: the decoration table, the tile table, the world for the read back.
    const std::filesystem::path root = OPENYAMM_DEV_ASSETS_DIR;
    const BuiltOutdoor built = builtOutdoor(withLake(buildingProject(HomePlot,
        "water:\n  bodies:\n    - {id: water:lake, kind: lake, level: 320, polygon: [[70, 70], [90, 70], [90, 90], "
        "[70, 90]]}\n"
        "scatter:\n"
        "  - {id: forest_a, group: 5, decoration: tree12, count: 6, polygon: [[10, 10], [25, 10], [25, 25], [10, 25]]}\n"
        "  - {group: 10, decoration: flower01, count: 4, polygon: [[10, 100], [20, 100], [20, 110], [10, 110]], "
        "event: {title: Flowers, effects: [{text: You pick a flower}]}}\n"
        "  - {decoration: bouy0, count: 5, on: water, spacing: 1, polygon: [[70, 70], [90, 70], [90, 90], [70, 90]]}\n"
        "  - {decoration: dec57, count: 8, height: [1100, 1600], polygon: [[100, 10], [120, 10], [120, 30], "
        "[100, 30]]}\n"
        "events:\n  - {id: evt:seasons, trigger: load, condition: {season: winter}, effects: [{set_sprite: {of: "
        "forest_a, to: tree37}}, {hide: group:10}]}\n")), "oymap_oa_scatter", root);
    REQUIRE(built.built);
    size_t trees = 0;
    size_t flowers = 0;
    size_t buoys = 0;
    size_t clouds = 0;
    int flowerEvent = 0;

    for (const YAML::Node &entity : built.scene["entities"])
    {
        const std::string name = entity["name"].as<std::string>();
        const int z = entity["position"]["z"].as<int>();

        if (name == "tree12")
        {
            ++trees;
            CHECK(entity["event_id_primary"].as<int>() == 5);
        }
        else if (name == "flower01")
        {
            ++flowers;
            CHECK(entity["event_id_primary"].as<int>() == 10);
            flowerEvent = entity["event_id_secondary"].as<int>();
            CHECK(flowerEvent != 0);
        }
        else if (name == "bouy0")
        {
            ++buoys;
            // On the lake's surface, inside it.
            CHECK(z == 320);
            CHECK(entity["position"]["x"].as<int>() > (70 - 64) * 512);
        }
        else if (name == "dec57")
        {
            ++clouds;
            CHECK(z >= 640 + 1100);
            CHECK(z <= 640 + 1600);
        }
    }

    CHECK(trees == 6);
    CHECK(flowers == 4);
    CHECK(buoys == 5);
    CHECK(clouds == 8);
    // The season event changes the groups by their numbers, as Harmondale's event 250.
    CHECK(built.lua.find("evt.SetSprite(5, 1, \"tree37\")") != std::string::npos);
    CHECK(built.lua.find("evt.SetSprite(10, 0)") != std::string::npos);
    CHECK(built.lua.find("RegisterEvent(" + std::to_string(flowerEvent) + ", \"Flowers\", function()\n"
        "    evt.StatusText(\"You pick a flower\")") != std::string::npos);

    const auto refused = [](const std::string &more, const std::string &fragment)
    {
        std::vector<ProjectIssue> issues;
        validateOutdoorProject(buildingProject(HomePlot, more), issues);
        CAPTURE(more);
        CHECK(anyIssue(issues, fragment));
    };
    refused("scatter:\n  - {id: a, group: 5, decoration: tree12, count: 1, circle: {at: [10, 10], r: 3}}\n"
        "  - {id: a, group: 6, decoration: tree12, count: 1, circle: {at: [20, 20], r: 3}}\n", "one group");
    refused("scatter:\n  - {id: a, group: 5, decoration: tree12, count: 1, circle: {at: [10, 10], r: 3}}\n"
        "  - {id: b, group: 5, decoration: tree12, count: 1, circle: {at: [20, 20], r: 3}}\n", "already the group");
}

TEST_CASE("a scatter support radius preserves the calibrated sites when the decoration cylinder is removed")
{
    const auto sites = [](int tableRadius, const std::string &support)
    {
        const Project project = buildingProject(HomePlot, "scatter:\n  - {decoration: vase, count: 75, spacing: 0.5, "
            "polygon: [[70, 70], [100, 70], [100, 100], [70, 100]]" + support + "}\n");
        std::vector<ProjectIssue> issues;
        LoweredOutdoorMap ground;
        REQUIRE(lowerOutdoorProject(project, ground, issues));
        // Level shelves separated by slopes. Radius 65 rejects placements that a point can occupy.
        for (int y = 69; y <= 101; ++y)
        {
            for (int x = 69; x <= 101; ++x)
            {
                ground.samples[y * OutdoorNodeCount + x] = x % 8 < 4 ? 20 : 32;
            }
        }
        const std::string table = "1\tnothing\t\n101\tvase\tVase\t0\t" + std::to_string(tableRadius) + "\n";
        OutdoorPlaces places;
        std::vector<std::string> warnings;
        REQUIRE(placeOutdoorThings(project, ground, table, places, issues, warnings));
        std::vector<std::array<int, 2>> points;
        for (const OutdoorPlacedDecoration &decoration : places.decorations)
        {
            points.push_back({decoration.x, decoration.y});
        }
        return points;
    };
    const auto calibrated = sites(65, "");
    REQUIRE(calibrated.size() == 75);
    CHECK(sites(0, "") != calibrated);
    CHECK(sites(0, ", support_radius: 65") == calibrated);
    CHECK(sites(65, ", support_radius: 0") == sites(0, ""));
}

TEST_CASE("O-A: a stand of mixed kinds, spacing across entries, a share closer, a thinned rim; clumps keep a cell")
{
    const std::string table = "#\tInternalName\tHint\n1\tnothing\t\n101\ttree12\ttree\n102\ttree37\ttree\n";
    const auto placed = [&table](const std::string &scatter, std::vector<std::string> *pWarnings = nullptr)
    {
        const Project project = buildingProject(HomePlot, "scatter:\n" + scatter);
        LoweredOutdoorMap lowered;
        std::vector<ProjectIssue> issues;
        REQUIRE(lowerOutdoorProject(project, lowered, issues));
        OutdoorPlaces places;
        std::vector<std::string> warnings;
        CHECK(placeOutdoorThings(project, lowered, table, places, issues, pWarnings != nullptr ? *pWarnings
            : warnings));

        for (const ProjectIssue &issue : issues)
        {
            MESSAGE(issue.path << ": " << issue.message);
        }

        return places.decorations;
    };
    const auto nearestOf = [](const std::vector<OutdoorPlacedDecoration> &all, size_t index)
    {
        double nearest = 1e30;

        for (size_t other = 0; other < all.size(); ++other)
        {
            if (other != index)
            {
                nearest = std::min(nearest, std::hypot(all[other].x - all[index].x, all[other].y - all[index].y)
                    / 512.0);
            }
        }

        return nearest;
    };
    const std::string square = "polygon: [[70, 70], [110, 70], [110, 110], [70, 110]]";

    // kinds: both mixed through one throw, about by weight.
    const std::vector<OutdoorPlacedDecoration> mixed = placed("  - {kinds: {tree12: 3, tree37: 1}, count: 120, "
        "spacing: 1.4, " + square + "}\n");
    REQUIRE(mixed.size() == 120);
    const size_t of37 = static_cast<size_t>(std::count_if(mixed.begin(), mixed.end(),
        [](const OutdoorPlacedDecoration &decoration) { return decoration.name == "tree37"; }));
    CHECK(of37 > 15);
    CHECK(of37 < 50);

    for (size_t index = 0; index < mixed.size(); ++index)
    {
        CHECK(nearestOf(mixed, index) >= 1.4 - 1e-6);
    }

    // spacing_group: two entries over one ground keep their spacing from each other too; without it they do not.
    const std::string two = "  - {decoration: tree12, count: 60, spacing: 1.4, spacing_group: stand, " + square
        + "}\n  - {decoration: tree37, count: 60, spacing: 1.4, spacing_group: stand, " + square + "}\n";
    const std::vector<OutdoorPlacedDecoration> grouped = placed(two);

    for (size_t index = 0; index < grouped.size(); ++index)
    {
        CHECK(nearestOf(grouped, index) >= 1.4 - 1e-6);
    }

    const std::vector<OutdoorPlacedDecoration> apart = placed("  - {decoration: tree12, count: 60, spacing: 1.4, "
        + square + "}\n  - {decoration: tree37, count: 60, spacing: 1.4, " + square + "}\n");
    double least = 1e30;

    for (size_t index = 0; index < apart.size(); ++index)
    {
        least = std::min(least, nearestOf(apart, index));
    }

    CHECK(least < 1.4);

    // close_share: at most a tenth closer than the spacing, none closer than close_spacing.
    const std::vector<OutdoorPlacedDecoration> close = placed("  - {decoration: tree12, count: 200, spacing: 1.4, "
        "close_share: 0.1, close_spacing: 1.0, " + square + "}\n");
    size_t closer = 0;

    for (size_t index = 0; index < close.size(); ++index)
    {
        const double nearest = nearestOf(close, index);
        CHECK(nearest >= 1.0 - 1e-6);
        closer += nearest < 1.4 - 1e-6 ? 1 : 0;
    }

    CHECK(closer > 0);
    // Each close place makes at most two things close to one another.
    CHECK(closer <= 2 * 20);

    // edge_thin: fewer within three cells of the edge than without it, the same count where room is left.
    const std::string sparse = "  - {decoration: tree12, count: 200, spacing: 1.0, " + square;
    const auto rim = [](const std::vector<OutdoorPlacedDecoration> &all)
    {
        size_t near = 0;

        for (const OutdoorPlacedDecoration &decoration : all)
        {
            const double x = decoration.x / 512.0 + 64.0;
            const double y = 64.0 - decoration.y / 512.0;
            near += std::min({x - 70.0, 110.0 - x, y - 70.0, 110.0 - y}) < 3.0 ? 1 : 0;
        }

        return near;
    };
    const std::vector<OutdoorPlacedDecoration> full = placed(sparse + "}\n");
    const std::vector<OutdoorPlacedDecoration> thinned = placed(sparse + ", edge_thin: {width: 3, keep: 0.33}}\n");
    CHECK(thinned.size() == 200);
    CHECK(rim(thinned) * 2 < rim(full));

    // Clumps keep a cell between their things unless `spacing` says otherwise.
    const std::vector<OutdoorPlacedDecoration> clumps = placed("  - {decoration: tree12, count: 20, clusters: 3, "
        "cluster_radius: 4, " + square + "}\n");

    for (size_t index = 0; index < clumps.size(); ++index)
    {
        CHECK(nearestOf(clumps, index) >= 1.0 - 1e-6);
    }

    // The warning names the entries that found no place.
    std::vector<std::string> warnings;
    placed("  - {id: crowd, decoration: tree12, count: 50, spacing: 2, polygon: [[70, 70], [74, 70], [74, 74], "
        "[70, 74]]}\n", &warnings);
    CHECK(std::any_of(warnings.begin(), warnings.end(), [](const std::string &warning)
    {
        return warning.find("(scatter[0] (crowd) ") != std::string::npos && warning.find(" of 50)") != std::string::npos;
    }));

    // Refusals.
    const auto refused = [&table](const std::string &scatter, const std::string &fragment)
    {
        const Project project = buildingProject(HomePlot, "scatter:\n" + scatter);
        LoweredOutdoorMap lowered;
        std::vector<ProjectIssue> issues;
        REQUIRE(lowerOutdoorProject(project, lowered, issues));
        OutdoorPlaces places;
        std::vector<std::string> warnings;
        CHECK_FALSE(placeOutdoorThings(project, lowered, table, places, issues, warnings));
        CAPTURE(scatter);
        CHECK(anyIssue(issues, fragment));
    };
    refused("  - {kinds: {tree12: 0}, count: 1, circle: {at: [80, 80], r: 3}}\n", "`kinds` mixes");
    refused("  - {kinds: {tree99: 1}, count: 1, circle: {at: [80, 80], r: 3}}\n", "no decoration named tree99");
    refused("  - {decoration: tree12, count: 1, close_share: 0.1, circle: {at: [80, 80], r: 3}}\n", "give both");
    refused("  - {decoration: tree12, count: 1, edge_thin: {width: 3}, circle: {at: [80, 80], r: 3}}\n",
        "`edge_thin` is");
    refused("  - {decoration: tree12, count: 1, on: sky, circle: {at: [80, 80], r: 3}}\n", "`on` is land");
    refused("  - {decoration: tree12, count: 1, height: [9, 2], circle: {at: [80, 80], r: 3}}\n", "`height` is");
    refused("  - {decoration: tree12, count: 2, on: water, clusters: 1, circle: {at: [80, 80], r: 3}}\n",
        "spread evenly");
}

TEST_CASE("O-A: a level terrace area holds its nodes at one height; its slope runs back into the land")
{
    const LoweredOutdoorMap lowered = loweredOf(std::string(LevelLand) + "  terraces:\n"
        "    - {polygon: [[40, 40], [50, 40], [50, 46], [40, 46]], height: 288}\n"
        "    - {polygon: [[80, 80], [84, 80], [84, 84], [80, 84]], height: 1280, slope: 4}\n");
    const auto at = [&lowered](int x, int y)
    {
        return lowered.ground[static_cast<size_t>(y) * OutdoorNodeCount + static_cast<size_t>(x)];
    };

    for (int y = 40; y <= 46; ++y)
    {
        for (int x = 40; x <= 50; ++x)
        {
            CHECK(at(x, y) == doctest::Approx(288.0));
        }
    }

    // A step: the node beside the outline keeps the land's 640.
    CHECK(at(39, 43) == doctest::Approx(640.0));
    CHECK(at(51, 43) == doctest::Approx(640.0));
    // The slope: halfway down two cells out, the land at four.
    CHECK(at(84, 82) == doctest::Approx(1280.0));
    CHECK(at(86, 82) == doctest::Approx(640.0 + (1280.0 - 640.0) * 0.5));
    CHECK(at(88, 82) == doctest::Approx(640.0));
    CHECK(anyIssue(refusedWith(std::string(LevelLand) + "  terraces:\n    - {polygon: [[40, 40], [50, 40]], "
        "height: 288}\n"), "a terrace's `polygon`"));
    CHECK(anyIssue(refusedWith(std::string(LevelLand) + "  terraces:\n    - {polygon: [[40, 40], [50, 40], "
        "[50, 46]], height: 9000}\n"), "0 to 8160"));
}

namespace
{
const Game::OutdoorBModel *onlyModel(const OutdoorThings &things, const std::vector<ProjectIssue> &issues)
{
    for (const ProjectIssue &issue : issues)
    {
        MESSAGE(issue.path << ": " << issue.message);
    }

    return issues.empty() && things.models.size() == 1 ? &things.models[0] : nullptr;
}

size_t texturedFaces(const Game::OutdoorBModel &model, const std::string &texture, uint32_t bits = 0)
{
    return static_cast<size_t>(std::count_if(model.faces.begin(), model.faces.end(),
        [&](const Game::OutdoorBModelFace &face)
    {
        return face.textureName == texture && (face.attributes & bits) == bits;
    }));
}
}

TEST_CASE("O-C: a segmental arch head is an arc of a circle flatter than a half circle, convex and symmetric")
{
    const std::vector<std::array<double, 2>> head = outdoorArchHead(400.0, 300.0, "segment", 4);
    REQUIRE(head.size() == 5);
    CHECK(head.front()[0] == doctest::Approx(-200.0));
    CHECK(head.back()[0] == doctest::Approx(200.0));
    // A quarter of the width over its springs, its crown at the top.
    CHECK(head.front()[1] == doctest::Approx(200.0));
    CHECK(head[2][1] == doctest::Approx(300.0));
    // On one circle: radius (200^2 + 100^2) / 200 = 250, its centre 250 under the crown.
    for (const std::array<double, 2> &point : head)
    {
        CHECK(std::hypot(point[0], point[1] - 50.0) == doctest::Approx(250.0));
    }

    // A given rise; never more than a half circle.
    CHECK(outdoorArchHead(400.0, 300.0, "segment", 6, 50.0).front()[1] == doctest::Approx(250.0));
    CHECK(outdoorArchHead(400.0, 300.0, "segment", 6, 900.0).front()[1] == doctest::Approx(100.0));
    std::vector<ProjectIssue> issues;
    IdsLock ids;
    const OutdoorThings things = thingsOf("structures:\n  - {id: thing:door, kind: doorway, at: [50, 50], "
        "arch: segment, title: In, into: {map: d01.blv}}\n", issues, ids);
    CHECK(onlyModel(things, issues) != nullptr);
}

TEST_CASE("O-C: a fountain's basin as an outline: MM6's pointed Heroes' fountain, rim tops, water in convex pieces")
{
    std::vector<ProjectIssue> issues;
    IdsLock ids;
    // HFa1_E as the original's faces give it (outa1, 58 faces: 16 rim walls out and in, 16 rim tops, 6 water).
    const OutdoorThings things = thingsOf("structures:\n  - {id: thing:hf, kind: fountain, at: [50, 50], height: "
        "96, rim: 32, water_below: 32, pillar: 0, outline: [[288, 0], [224, 64], [96, 160], [-64, 192], [-224, 224], "
        "[-192, 128], [-192, 96], [-224, 32], [-288, 0], [-224, -32], [-192, -96], [-192, -128], [-224, -224], "
        "[-64, -192], [96, -160], [224, -64]], textures: {wall: descnr1, water: 6wtrtyl}, title: Drink, hint: "
        "Fountain}\n", issues, ids);
    const Game::OutdoorBModel *pModel = onlyModel(things, issues);
    REQUIRE(pModel != nullptr);
    const uint32_t fluid = 0x10;
    const size_t water = texturedFaces(*pModel, "6wtrtyl", fluid);
    CHECK(water >= 2);
    CHECK(water <= 8);
    CHECK(texturedFaces(*pModel, "descnr1") == 48);
    // The ground 640: rim top 96 over it, water 32 under the rim's top; the outline's own reach.
    CHECK(pModel->maxZ == 640 + 96);
    CHECK(pModel->maxX - pModel->minX == 576);
    CHECK(pModel->maxY - pModel->minY == 448);
    uint16_t drink = 0;
    std::set<uint16_t> rest;

    for (const Game::OutdoorBModelFace &face : pModel->faces)
    {
        if (face.textureName == "6wtrtyl")
        {
            drink = face.cogTriggeredNumber;
            CHECK(face.planeNormalZ == 65536);
            CHECK(pModel->vertices[face.vertexIndices[0]].z == 640 + 64);
        }
        else
        {
            rest.insert(face.cogTriggeredNumber);
        }
    }

    CHECK(drink != 0);
    REQUIRE(rest.size() == 1);
    CHECK(*rest.begin() != drink);
    CHECK(findOutdoorCoplanarFaces(things.models).empty());
}

TEST_CASE("O-C: a rectangular pond, a three-sided basin, a stepped basin and MM8's box pillar with running water")
{
    const uint32_t flowDown = 0x4;
    const uint32_t fluid = 0x10;
    std::vector<ProjectIssue> issues;
    IdsLock ids;
    const OutdoorThings pond = thingsOf("structures:\n  - {id: thing:pond, kind: fountain, at: [50, 50], size: [640, "
        "128], height: 72, rim: 16, water_below: 40, pillar: 0}\n", issues, ids);
    const Game::OutdoorBModel *pPond = onlyModel(pond, issues);
    REQUIRE(pPond != nullptr);
    CHECK(pPond->maxX - pPond->minX == 640);
    CHECK(pPond->maxY - pPond->minY == 128);
    // Four walls out, four tops, four in, one water face (a rectangle is one convex piece), as outd1's pond's 17.
    CHECK(pPond->faces.size() == 13);

    issues.clear();
    const OutdoorThings three = thingsOf("structures:\n  - {id: thing:tri, kind: fountain, at: [50, 50], sides: 3, "
        "radius: 256}\n", issues, ids);
    const Game::OutdoorBModel *pThree = onlyModel(three, issues);
    REQUIRE(pThree != nullptr);
    CHECK(pThree->faces.size() == 3 * 3 + 1 + 3 + 1);

    issues.clear();
    const OutdoorThings stepped = thingsOf("structures:\n  - {id: thing:town, kind: fountain, at: [50, 50], radius: "
        "312, sides: 8, rim: 96, height: 64, water_below: 16, tiers: [[96, 64]], tier_shape: box, "
        "pillar: 448}\n", issues, ids);
    const Game::OutdoorBModel *pStepped = onlyModel(stepped, issues);
    REQUIRE(pStepped != nullptr);
    // The step: a box round the ring 96 out, 64 high; the basin on it, its top at 128 over the ground.
    const double across = 2.0 * (312.0 * std::cos(3.14159265358979 / 8.0) + 96.0);
    CHECK(pStepped->maxX - pStepped->minX == doctest::Approx(across).epsilon(0.01));
    size_t stepTops = 0;

    for (const Game::OutdoorBModelFace &face : pStepped->faces)
    {
        stepTops += face.planeNormalZ == 65536 && pStepped->vertices[face.vertexIndices[0]].z == 640 + 64 ? 1 : 0;
    }

    CHECK(stepTops >= 4);
    CHECK(pStepped->maxZ == 640 + 448);
    CHECK(findOutdoorCoplanarFaces(stepped.models).empty());

    issues.clear();
    const OutdoorThings mm8 = thingsOf("structures:\n  - {id: thing:mm8, kind: fountain, at: [50, 50], radius: 384, "
        "height: 80, pillar: 144, pillar_shape: box, pillar_width: 64, flow: down, textures: {water: wtrtyl}, "
        "title: Drink}\n", issues, ids);
    const Game::OutdoorBModel *pMm8 = onlyModel(mm8, issues);
    REQUIRE(pMm8 != nullptr);
    // The block: four running sides and a top, water; the basin's water liquid.
    CHECK(texturedFaces(*pMm8, "wtrtyl", flowDown) == 5);
    CHECK(texturedFaces(*pMm8, "wtrtyl", fluid) == 1);
    CHECK(pMm8->maxZ == 640 + 144);

    const auto refused = [](const std::string &structure, const std::string &fragment)
    {
        std::vector<ProjectIssue> found;
        IdsLock lock;
        thingsOf("structures:\n" + structure, found, lock);
        CAPTURE(structure);
        CHECK(anyIssue(found, fragment));
    };
    refused("  - {id: thing:f, kind: fountain, at: [50, 50], outline: [[0, 0], [100, 0]]}\n", "3 to 64 points");
    refused("  - {id: thing:f, kind: fountain, at: [50, 50], outline: [[0, 0], [200, 200], [200, 0], [0, 200]]}\n",
        "crossing nowhere");
    refused("  - {id: thing:f, kind: fountain, at: [50, 50], size: [200, 200], outline: [[0, 0], [1, 0], [0, 1]]}\n",
        "not both");
    refused("  - {id: thing:f, kind: fountain, at: [50, 50], size: [128, 128], rim: 64}\n", "leaves no water");
    refused("  - {id: thing:f, kind: fountain, at: [50, 50], pillar_shape: star}\n", "round (the default) or a box");
    refused("  - {id: thing:f, kind: fountain, at: [50, 50], tiers: [[64, 2]]}\n", "8 to 512 high");
}

TEST_CASE("O-C: a bridge on arches: soffits, spandrels and piers to the land, as the sea viaduct; segment arches")
{
    std::vector<ProjectIssue> issues;
    IdsLock ids;
    // Eight cells long (4096), level at 960 over the datum, three arches on piers 256 wide.
    const OutdoorThings things = thingsOf("structures:\n  - {id: thing:viaduct, kind: bridge, line: [[40, 70], [48, "
        "70]], width: 512, height: 1600, thickness: 64, kerb: 80, arches: {count: 3, rise: 352, pier_width: 256}, "
        "textures: {deck: 7t1beds2, side: chb1}}\n", issues, ids);
    const Game::OutdoorBModel *pModel = onlyModel(things, issues);
    REQUIRE(pModel != nullptr);
    size_t soffits = 0;
    double lowestSoffit = 1.0e9;

    for (const Game::OutdoorBModelFace &face : pModel->faces)
    {
        if (face.planeNormalZ < 0)
        {
            ++soffits;

            for (const uint16_t index : face.vertexIndices)
            {
                lowestSoffit = std::min(lowestSoffit, static_cast<double>(pModel->vertices[index].z));
            }
        }
    }

    // Six segments to an arch, no deck underside; the springs 352 under the crowns (1536).
    CHECK(soffits == 18);
    CHECK(lowestSoffit == doctest::Approx(1600.0 - 64.0 - 352.0).epsilon(0.001));
    // Down to the land (640) and below it.
    CHECK(pModel->minZ < 640);
    CHECK(pModel->maxZ == 1600 + 80);
    CHECK(findOutdoorCoplanarFaces(things.models).empty());

    issues.clear();
    const OutdoorThings flat = thingsOf("structures:\n  - {id: thing:span, kind: bridge, line: [[40, 70], [44, 70]], "
        "height: 1200, arches: {count: 1, rise: 256, form: segment}}\n", issues, ids);
    const Game::OutdoorBModel *pFlat = onlyModel(flat, issues);
    REQUIRE(pFlat != nullptr);
    size_t flatSoffits = 0;

    for (const Game::OutdoorBModelFace &face : pFlat->faces)
    {
        flatSoffits += face.planeNormalZ < 0 ? 1 : 0;
    }

    CHECK(flatSoffits == 4);

    const auto refused = [](const std::string &structure, const std::string &fragment)
    {
        std::vector<ProjectIssue> found;
        IdsLock lock;
        thingsOf("structures:\n" + structure, found, lock);
        CAPTURE(structure);
        CHECK(anyIssue(found, fragment));
    };
    refused("  - {id: thing:b, kind: bridge, line: [[40, 70], [44, 70], [44, 74]], arches: {count: 2}}\n",
        "straight `line` of two points");
    refused("  - {id: thing:b, kind: bridge, line: [[40, 70], [41, 70]], arches: {count: 8}}\n", "at least 64 wide");
    refused("  - {id: thing:b, kind: bridge, line: [[40, 70], [44, 70]], piers: 2, arches: {count: 2}}\n",
        "no `piers`");
}

TEST_CASE("an arched bridge beds both ends and its centre pier across a slope while both vaults stay open")
{
    const Project project = buildingProject("", "structures:\n  - {id: thing:bridge, kind: bridge, "
        "line: [[40, 60], [52, 60]], width: 1536, height: 1536, thickness: 64, "
        "arches: {spans: [1024, 1024], rise: 256, pier_width: 1024}}\n");
    LoweredOutdoorMap ground;
    std::vector<ProjectIssue> issues;
    REQUIRE(lowerOutdoorProject(project, ground, issues));
    for (int y = 58; y <= 62; ++y)
    {
        for (int x = 40; x <= 52; ++x)
        {
            ground.samples[y * OutdoorNodeCount + x] = static_cast<uint8_t>(32 - 4 * (y - 58));
        }
    }
    // Two hollows lie inside the supports. The third lies outside the bridge, so the east minimum is exactly
    // halfway down a terrain edge, below every footprint corner and every terrain vertex inside that footing.
    ground.samples[61 * OutdoorNodeCount + 41] = 4;
    ground.samples[61 * OutdoorNodeCount + 46] = 7;
    ground.samples[62 * OutdoorNodeCount + 50] = 4;
    IdsLock ids;
    OutdoorEventWords words(project, {}, ids, issues);
    OutdoorThings things;
    std::vector<std::string> warnings;
    REQUIRE(raiseOutdoorThings(project, ground, {}, ids, words, things, issues, warnings));
    const Game::OutdoorBModel *bridge = onlyModel(things, issues);
    REQUIRE(bridge != nullptr);
    using Vertex = Game::OutdoorBModelVertex;
    const auto range = [&](const Game::OutdoorBModelFace &face, int Vertex::*coordinate)
    {
        const auto [lo, hi] = std::minmax_element(face.vertexIndices.begin(), face.vertexIndices.end(),
            [&](uint16_t a, uint16_t b) { return bridge->vertices[a].*coordinate < bridge->vertices[b].*coordinate; });
        return std::array<int, 2>{bridge->vertices[*lo].*coordinate, bridge->vertices[*hi].*coordinate};
    };
    const auto worldX = [](int cell) { return (cell - 64) * 512; };
    const std::array<int, 2> across = {1280, 2816};
    struct Support { int from, to, bottom; };
    for (const Support &support : {Support{40, 43, 32}, Support{45, 47, 128}, Support{49, 52, 288}})
    {
        CAPTURE(support.from);
        const std::array<int, 2> along = {worldX(support.from), worldX(support.to)};
        int ends = 0, sides = 0;
        for (const auto &face : bridge->faces)
        {
            const auto x = range(face, &Vertex::x), y = range(face, &Vertex::y);
            if (y == across && x[0] == x[1] && (x[0] == along[0] || x[0] == along[1]))
                ++ends;
            else if (x == along && y[0] == y[1] && (y[0] == across[0] || y[0] == across[1])
                     && face.planeNormalZ == 0)
                ++sides;
            else
                continue;
            CHECK(range(face, &Vertex::z)[0] == support.bottom);
            CHECK(std::count_if(face.vertexIndices.begin(), face.vertexIndices.end(),
                [&](uint16_t i) { return bridge->vertices[i].z == support.bottom; }) == 2);
        }
        CHECK(ends == 2);
        CHECK(sides == 2);
    }
    // A vertical ray under each crown still sees the two original soffit panels at deck height minus thickness.
    for (int x : {worldX(44), worldX(48)})
    {
        int hits = 0;
        for (const auto &face : bridge->faces)
        {
            const auto span = range(face, &Vertex::x);
            if (face.planeNormalZ < 0 && span[0] <= x && x <= span[1] && range(face, &Vertex::y) == across)
            {
                const double z = -(double(face.planeNormalX) * x + double(face.planeNormalY) * 2048
                    + face.planeDistance) / face.planeNormalZ;
                CHECK(z == doctest::Approx(1472).epsilon(0.0002));
                ++hits;
            }
        }
        CHECK(hits == 2);
    }
}

TEST_CASE("O-C: a sagging footbridge with rope rails and end towers, as Harmondale's NewOut2Bridge_")
{
    std::vector<ProjectIssue> issues;
    IdsLock ids;
    const OutdoorThings things = thingsOf("structures:\n  - {id: thing:foot, kind: bridge, line: [[40, 70], [47, 70]], "
        "width: 512, height: 1280, rise: -96, piers: 0, railing: rope, towers: [96, 96, 352], textures: {deck: 7trimd, "
        "side: trim2_16a}}\n", issues, ids);
    const Game::OutdoorBModel *pModel = onlyModel(things, issues);
    REQUIRE(pModel != nullptr);
    // The deck's middle 96 under its ends; the towers 352 over the ends; ropes 224 over the deck.
    double middleTop = 1.0e9;

    for (const Game::OutdoorBModelFace &face : pModel->faces)
    {
        if (face.textureName == "7trimd" && face.planeNormalZ > 60000)
        {
            for (const uint16_t index : face.vertexIndices)
            {
                middleTop = std::min(middleTop, static_cast<double>(pModel->vertices[index].z));
            }
        }
    }

    CHECK(middleTop == doctest::Approx(1280.0 - 96.0).epsilon(0.002));
    CHECK(pModel->maxZ == 1280 + 352);
    CHECK(findOutdoorCoplanarFaces(things.models).empty());
    std::vector<ProjectIssue> found;
    thingsOf("structures:\n  - {id: thing:b, kind: bridge, line: [[40, 70], [44, 70]], railing: chain}\n", found,
        ids);
    CHECK(anyIssue(found, "`railing` is rope"));
}

TEST_CASE("O-C: liquid faces on a structure's and a part's textures: lava with its flow")
{
    const uint32_t fluid = 0x10;
    const uint32_t lava = 0x40000000;
    const uint32_t flowDown = 0x4;
    std::vector<ProjectIssue> issues;
    IdsLock ids;
    const OutdoorThings things = thingsOf("structures:\n  - {id: thing:stream, kind: stairs, line: [[50, 50], [51, 50]], "
        "rise: 256, ramp: true, textures: {top: {texture: lavtyl, liquid: lava, flow: down}, wall: chb1}}\n",
        issues, ids);
    const Game::OutdoorBModel *pModel = onlyModel(things, issues);
    REQUIRE(pModel != nullptr);
    // MM8 (the test's world): the burning bit and the flow, no fluid bit, as the Plane of Fire's streams.
    CHECK(texturedFaces(*pModel, "lavtyl", lava | flowDown) >= 1);
    CHECK(texturedFaces(*pModel, "lavtyl") == texturedFaces(*pModel, "lavtyl", lava | flowDown));
    CHECK(texturedFaces(*pModel, "lavtyl", fluid) == 0);
    CHECK(texturedFaces(*pModel, "chb1", fluid) == 0);

    Project project = buildingProject("      - {building: building:home, at: [40, 40], facing: s, foundation: 0, "
        "door: none, parts: [{id: base, at: [0, 0], size: [512, 512], wall_height: 256, roof: flat, textures: {roof: {texture: lavatyl, liquid: "
        "lava}}}]}\n");
    LoweredOutdoorMap lowered;
    std::vector<ProjectIssue> lowering;
    const bool ok = lowerOutdoorProject(project, lowered, lowering);

    for (const ProjectIssue &issue : lowering)
    {
        MESSAGE(issue.path << ": " << issue.message);
    }

    REQUIRE(ok);
    const Game::OutdoorBModel building = raiseOutdoorBuilding(lowered.buildings[0]);
    CHECK(texturedFaces(building, "lavatyl", lava) >= 1);
    CHECK(texturedFaces(building, "lavatyl") == texturedFaces(building, "lavatyl", lava));
    CHECK(outdoorLiquidBits("lava", "", "mm6") == fluid);
    CHECK(outdoorLiquidBits("water", "up", "mm7") == (fluid | 0x20));
    CHECK(outdoorLiquidBits("tar", "", "mm7") == UINT32_MAX);

    std::vector<ProjectIssue> found;
    thingsOf("structures:\n  - {id: thing:s, kind: stairs, line: [[50, 50], [51, 50]], rise: 256, ramp: true, "
        "textures: {top: {texture: x, liquid: tar}}}\n", found, ids);
    CHECK(anyIssue(found, "liquid: water | lava"));
}

TEST_CASE("O-C: a culvert: a headwall round a round mouth, water out of it, one dark face that is clicked")
{
    std::vector<ProjectIssue> issues;
    IdsLock ids;
    const OutdoorThings things = thingsOf("structures:\n  - {id: thing:sewer, kind: culvert, at: [50, 50], turn: 90, "
        "width: 288, height: 456, wall: [576, 552], title: Enter the Sewer, hint: Sewer, into: {map: 7d16.blv}}\n",
        issues, ids);
    const Game::OutdoorBModel *pModel = onlyModel(things, issues);
    REQUIRE(pModel != nullptr);
    size_t dark = 0;
    size_t water = 0;
    uint16_t click = 0;
    std::set<uint16_t> rest;

    for (const Game::OutdoorBModelFace &face : pModel->faces)
    {
        if (face.textureName == "solid01")
        {
            ++dark;
            click = face.cogTriggeredNumber;
            // Turned 90: looks west.
            CHECK(face.planeNormalX < -60000);
            continue;
        }

        rest.insert(face.cogTriggeredNumber);
        water += (face.attributes & 0x30) == 0x30 ? 1 : 0;
    }

    CHECK(dark == 1);
    CHECK(click != 0);
    REQUIRE(rest.size() == 1);
    CHECK(*rest.begin() != click);
    // The pipe's floor and four strips out over the land.
    CHECK(water == 5);
    CHECK(pModel->maxZ == 640 + 552);
    CHECK(findOutdoorCoplanarFaces(things.models).empty());
    std::vector<ProjectIssue> found;
    thingsOf("structures:\n  - {id: thing:c, kind: culvert, at: [50, 50], wall: [200, 600]}\n", found, ids);
    CHECK(anyIssue(found, "a culvert's mouth"));
}

TEST_CASE("O-C: a cave mouth set back behind a ledge: the rim a recess narrowing to it, a ramp up to its foot")
{
    const CaveBuild build = caveBuild("  - {id: thing:cave, kind: cave_mouth, at: [50, 50], size: [1024, 1536], "
        "crest: 900, mouth: {width: 432, height: 512, depth: 256, setback: 384, ledge: 96}, title: In, hint: A Cave, "
        "into: {map: 7d33.blv}}\n", "  ridges:\n    - {line: [[44, 47], [56, 47]], height: 1600, width: 1}\n");

    for (const ProjectIssue &issue : build.issues)
    {
        MESSAGE(issue.path << ": " << issue.message);
    }

    REQUIRE(build.issues.empty());
    const Game::OutdoorBModel *pCave = modelNamed(build.things, "thing:cave");
    REQUIRE(pCave != nullptr);
    // The dark face: 384 + 72 + 256 behind the footprint's front; its foot 96 over the floor.
    double darkFoot = 1.0e9;
    double darkY = 0.0;
    size_t ramps = 0;
    const double front = (64 - 50) * 512.0 - 768.0;

    for (const Game::OutdoorBModelFace &face : pCave->faces)
    {
        if (face.textureName == "solid01")
        {
            for (const uint16_t index : face.vertexIndices)
            {
                darkFoot = std::min(darkFoot, static_cast<double>(pCave->vertices[index].z));
                darkY = pCave->vertices[index].y;
            }
        }

        ramps += face.vertexIndices.size() == 4 && face.textureName == "dirttyl" && face.planeNormalZ > 30000
            && face.planeNormalZ < 65536 ? 1 : 0;
    }

    const double floor = nodeHeight(build.lowered, 50, 51);
    CHECK(darkFoot == doctest::Approx(floor + 96.0));
    CHECK(darkY == doctest::Approx(front + 384.0 + 72.0 + 256.0).epsilon(0.001));
    CHECK(ramps == 1);
    CHECK(pCave->minY == doctest::Approx(front).epsilon(0.001));
    const CaveBuild refused = caveBuild("  - {id: thing:cave, kind: cave_mouth, at: [50, 50], mouth: {ledge: 64}}\n");
    CHECK(anyIssue(refused.issues, "a ledge needs a setback"));
}

TEST_CASE("P4: a rough cave mouth's shell has no two faces on each other, whatever its seed")
{
    // X5's xd10_north: roughness moved two points of one ring past each other where the footprint's side flattens
    // them into one plane, and the quad between them folded onto itself (two faces of the shell on each other).
    // Where the rim reaches the footprint's corner, a shaken ring of the corner's column stood on the rim's jamb; two
    // cuts a unit apart (the front's and the footprint edge's) made sliver faces that folded over their neighbours.
    size_t builds = 0;
    size_t found = 0;

    for (const char *pShape : {"size: [576, 1536], crest: 480, mouth: {width: 448, height: 384, depth: 75, rim: 64}",
             "size: [1536, 1536], crest: 480, mouth: {width: 448, height: 384, depth: 75}",
             "size: [1024, 1024], crest: 736, mouth: {width: 512, height: 384, depth: 256}",
             "size: [1024, 1280], free: true, crest: 400, mouth: {width: 256, height: 256, depth: 128}"})
    {
        for (const char *pRoughness : {"0", "0.4", "0.7", "1"})
        {
            for (int seed = 1; seed <= 60; ++seed)
            {
                const CaveBuild build = caveBuild("  - {id: thing:xd10_north, kind: cave_mouth, at: [50, 50], "
                    + std::string(pShape) + ", roughness: " + pRoughness + ", seed: " + std::to_string(seed)
                    + ", title: In, into: {map: d49.blv}}\n",
                    "  ridges:\n    - {line: [[44, 47], [56, 47]], height: 1600, width: 1}\n");
                REQUIRE(build.issues.empty());
                const Game::OutdoorBModel *pCave = modelNamed(build.things, "thing:xd10_north");
                REQUIRE(pCave != nullptr);
                const size_t pairs = findOutdoorCoplanarFaces({*pCave}).size()
                    + findOutdoorBackToBackFaces({*pCave}).size();

                if (pairs > 0)
                {
                    const std::string what = std::string(pShape) + " roughness " + pRoughness + " seed "
                        + std::to_string(seed) + ": " + std::to_string(pairs);
                    MESSAGE(what);
                }

                found += pairs;
                ++builds;
            }
        }
    }

    CHECK(builds == 960);
    CHECK(found == 0);
}

// ---- Masses and roofs (outdoor code batch O-D): domes, batter and buttresses, roofs to the ground, terraces and
// stairs, ruins, eaves per wall, round and stepped platforms ----

namespace
{
// The faces of a model with a texture whose corners all lie within [low, high] in height.
size_t facesBetween(const Game::OutdoorBModel &model, const std::string &texture, int low, int high)
{
    size_t count = 0;

    for (const Game::OutdoorBModelFace *pFace : facesWith(model, texture))
    {
        const std::array<int, 2> heights = heightsOf(model, *pFace);
        count += heights[0] >= low && heights[1] <= high ? 1 : 0;
    }

    return count;
}

// The bounds [x0, y0, x1, y1] of a model's faces with a texture.
std::array<int, 4> planBounds(const Game::OutdoorBModel &model, const std::string &texture)
{
    std::array<int, 4> bounds = {1 << 30, 1 << 30, -(1 << 30), -(1 << 30)};

    for (const Game::OutdoorBModelFace *pFace : facesWith(model, texture))
    {
        for (const uint16_t index : pFace->vertexIndices)
        {
            const Game::OutdoorBModelVertex &vertex = model.vertices[index];
            bounds = {std::min(bounds[0], vertex.x), std::min(bounds[1], vertex.y), std::max(bounds[2], vertex.x),
                std::max(bounds[3], vertex.y)};
        }
    }

    return bounds;
}

Game::OutdoorBModel raisedPlot(const std::string &plot)
{
    LoweredOutdoorMap lowered = loweredBuildings("      - {building: building:home, at: [40, 40], facing: s, " + plot
        + "}\n");
    REQUIRE(lowered.buildings.size() == 1);
    return raiseOutdoorBuilding(lowered.buildings[0]);
}
}

TEST_CASE("O-D: a dome over a round part in rings to a tip; Ravenshore's mushroom cap wider than its walls")
{
    const Game::OutdoorBModel dome = raisedPlot("door: none, eaves: 0, fascia: 0, parts: [{shape: round, at: [512, "
        "384], radius: 256, sides: 8, wall_height: 256, roof: dome}]");
    // Four rings of eight faces, the last eight triangles to the tip a half sphere's height over the walls.
    CHECK(facesWith(dome, "t14a05").size() == 32);
    size_t triangles = 0;
    int highest = 0;

    for (const Game::OutdoorBModelFace *pFace : facesWith(dome, "t14a05"))
    {
        triangles += pFace->vertexIndices.size() == 3 ? 1 : 0;
        highest = std::max(highest, heightsOf(dome, *pFace)[1]);
        CHECK(faceNormal(dome, *pFace)[2] > 0.0);
    }

    CHECK(triangles == 8);
    CHECK(highest == 640 + 256 + 256);
    // The cap: eaves 96 with their soffit and a fascia, the dome rising from the eaves' ring.
    const Game::OutdoorBModel cap = raisedPlot("door: none, eaves: 96, fascia: 32, parts: [{shape: round, at: [512, "
        "384], radius: 160, sides: 8, wall_height: 384, roof: dome, roof_height: 192, dome_rings: 3}]");
    CHECK(facesWith(cap, "t14a05").size() == 24);
    CHECK(facesBetween(cap, "t14a05b", 640 + 384, 640 + 384) == 8);
    const std::array<int, 4> walls = planBounds(cap, "t14a01");
    const std::array<int, 4> roof = planBounds(cap, "t14a05");
    CHECK(walls[0] - roof[0] >= 90);
    CHECK(highest > 0);
    CHECK(anyIssue(buildingIssues("door: none, parts: [{shape: round, at: [512, 384], radius: 256, roof: dome, "
        "dome_rings: 9}]"), "dome_rings is"));
    CHECK(anyIssue(buildingIssues("door: none, parts: [{size: [512, 512], roof: hip, dome_rings: 3}]"),
        "belongs to `roof: dome`"));
}

TEST_CASE("O-D: a battered part leans in with its bays, its door upright at the foot; a sloping foot; buttresses")
{
    // The Plane of Fire's guard tower: 512 square, drawn in 64 over 768, a flat top 384 square.
    const Game::OutdoorBModel tower = raisedPlot("eaves: 0, fascia: 0, parts: [{size: [512, 512], wall_height: 768, "
        "batter: 64, roof: flat}]");
    const std::array<int, 4> top = planBounds(tower, "t14a05");
    CHECK(top[2] - top[0] == 384);
    CHECK(top[3] - top[1] == 384);
    const std::array<int, 4> foot = planBounds(tower, "t14a01");
    CHECK(foot[2] - foot[0] == 512);
    size_t leaning = 0;

    for (const Game::OutdoorBModelFace *pFace : facesWith(tower, "t14a01"))
    {
        const double z = faceNormal(tower, *pFace)[2];
        leaning += z > 0.05 && z < 0.2 ? 1 : 0;
    }

    CHECK(leaning >= 4);
    // The door upright on the south wall's foot, the wedge's level top over its head.
    const std::vector<const Game::OutdoorBModelFace *> doors = facesWith(tower, "t14a03");
    REQUIRE(doors.size() == 1);
    CHECK(heightsOf(tower, *doors[0]) == std::array<int, 2>{640, 896});
    CHECK(std::fabs(faceNormal(tower, *doors[0])[2]) < 1.0e-6);
    CHECK(facesBetween(tower, "t14a05b", 896, 896) == 1);

    // A sloping foot 256 high, upright above it.
    const Game::OutdoorBModel based = raisedPlot("door: none, eaves: 0, fascia: 0, parts: [{size: [512, 512], "
        "wall_height: 768, batter: 32, batter_height: 256, batter_walls: [s, n], roof: flat}]");
    size_t upright = 0;
    size_t sloped = 0;

    for (const Game::OutdoorBModelFace *pFace : facesWith(based, "t14a01"))
    {
        const double z = faceNormal(based, *pFace)[2];
        (std::fabs(z) < 1.0e-6 ? upright : sloped) += heightsOf(based, *pFace)[0] >= 640 ? 1 : 0;
    }

    CHECK(sloped == 2);
    CHECK(upright >= 4);
    CHECK(planBounds(based, "t14a05")[2] - planBounds(based, "t14a05")[0] == 512);
    CHECK(planBounds(based, "t14a05")[3] - planBounds(based, "t14a05")[1] == 512 - 64);

    // Two buttresses on the south wall: a front, two sides and a sloping top each.
    const Game::OutdoorBModel buttressed = raisedPlot("door: none, textures: {buttress: t06a01}, parts: [{size: "
        "[512, 512], wall_height: 384, buttresses: {count: 2, width: 64, depth: 96, height: 320, walls: [s]}}]");
    CHECK(facesWith(buttressed, "t06a01").size() == 8);
    CHECK(facesBetween(buttressed, "t06a01", 640 + 320 - 96, 640 + 320) == 2);

    CHECK(anyIssue(buildingIssues("door: none, parts: [{size: [512, 512], batter: 64, taper: 0.8}]"),
        "a battered part"));
    CHECK(anyIssue(buildingIssues("door: none, parts: [{size: [512, 512], batter: 300}]"), "past the middle"));
    CHECK(anyIssue(buildingIssues("door: none, parts: [{size: [512, 512], batter: 64, buttresses: {count: 1}}]"),
        "buttresses stand against upright walls"));
}

TEST_CASE("O-D: roofs to the ground: an A-frame's door in its gable, a cone hut's door cut into its slope")
{
    // An A-frame: no walls, the gable roof from the ground, the door in the south gable.
    const Game::OutdoorBModel frame = raisedPlot("eaves: 0, fascia: 0, ridge: 0, parts: [{size: [512, 768], "
        "wall_height: 0, roof: gable, ridge_along: ns, roof_height: 512, door_height: 256}]");
    const std::vector<const Game::OutdoorBModelFace *> doors = facesWith(frame, "t14a03");
    REQUIRE(doors.size() == 1);
    CHECK(heightsOf(frame, *doors[0]) == std::array<int, 2>{640, 896});
    // The south gable in pieces round the door, none over it.
    const std::array<int, 4> foot = planBounds(frame, "t14a05");
    size_t gablePieces = 0;

    for (const Game::OutdoorBModelFace *pFace : facesWith(frame, "t14a01"))
    {
        // Above the foundation's course.
        if (faceNormal(frame, *pFace)[1] < -0.99 && heightsOf(frame, *pFace)[1] > 640)
        {
            ++gablePieces;
        }
    }

    CHECK(gablePieces >= 3);
    CHECK(foot[3] - foot[1] == 768);

    // A cone hut: an eight-sided cone from the ground, the door standing at its foot under a level top.
    const Game::OutdoorBModel hut = raisedPlot("eaves: 0, fascia: 0, parts: [{shape: round, at: [512, 384], "
        "radius: 320, sides: 8, wall_height: 0, roof: cone, roof_height: 672, door_height: 256}]");
    const std::vector<const Game::OutdoorBModelFace *> hutDoors = facesWith(hut, "t14a03");
    REQUIRE(hutDoors.size() == 1);
    CHECK(heightsOf(hut, *hutDoors[0]) == std::array<int, 2>{640, 896});
    CHECK(faceNormal(hut, *hutDoors[0])[1] < -0.99);
    CHECK(facesBetween(hut, "t14a05", 896, 896) == 1);
    // Its cheeks: upright, from the slope to the door's head.
    size_t cheeks = 0;

    for (const Game::OutdoorBModelFace *pFace : facesWith(hut, "t14a05"))
    {
        cheeks += std::fabs(faceNormal(hut, *pFace)[2]) < 1.0e-6 ? 1 : 0;
    }

    CHECK(cheeks == 2);

    // A castle gate higher than its walls (A5's X6 gates, `door_height: 384`): two leaves, the second mirrored, cut
    // into the roof as a single door is.
    const Game::OutdoorBModel gate = raisedPlot("eaves: 0, fascia: 0, door: {leaves: 2}, parts: [{size: [512, 512], "
        "wall_height: 256, roof: flat, door_height: 384}]");
    const std::vector<const Game::OutdoorBModelFace *> gateLeaves = facesWith(gate, "t14a03");
    REQUIRE(gateLeaves.size() == 2);
    CHECK(heightsOf(gate, *gateLeaves[0]) == std::array<int, 2>{640, 1024});
    CHECK(heightsOf(gate, *gateLeaves[1]) == std::array<int, 2>{640, 1024});

    // Each leaf shows its wing once (128 texels across), the second mirrored.
    for (size_t leafIndex = 0; leafIndex < 2; ++leafIndex)
    {
        const std::vector<int16_t> &us = gateLeaves[leafIndex]->textureUs;
        CHECK(*std::max_element(us.begin(), us.end()) - *std::min_element(us.begin(), us.end()) == 128);
    }
    CHECK(anyIssue(buildingIssues("door: none, parts: [{size: [512, 512], wall_height: 0, roof: flat}]"),
        "under a roof that reaches the ground"));
}

TEST_CASE("texture fit words: a window laid once per bay and only in the lowest row, a trim post on its end, a raised wall")
{
    // Three window bays 192 wide on a wall two rows high: each window face shows its 128 x 256 picture once, all in
    // the lowest row (A6: a 192 bay showed the window 1.5 times; the rows above repeated it).
    const Game::OutdoorBModel house = raisedPlot("door: none, eaves: 0, fascia: 0, textures: {window: {texture: "
        "fitwin, fit: true, size: [128, 256]}}, parts: [{size: [576, 512], wall_height: 512, roof: flat, "
        "windows: none, walls: {s: [window, window, window]}}]");
    const std::vector<const Game::OutdoorBModelFace *> windows = facesWith(house, "fitwin");
    REQUIRE(windows.size() == 3);

    for (const Game::OutdoorBModelFace *pFace : windows)
    {
        CHECK(heightsOf(house, *pFace) == std::array<int, 2>{640, 896});
        CHECK(*std::max_element(pFace->textureUs.begin(), pFace->textureUs.end())
            - *std::min_element(pFace->textureUs.begin(), pFace->textureUs.end()) == 128);
        CHECK(*std::max_element(pFace->textureVs.begin(), pFace->textureVs.end())
            - *std::min_element(pFace->textureVs.begin(), pFace->textureVs.end()) == 256);
    }

    CHECK(anyIssue(buildingIssues("door: none, textures: {window: {texture: t14b02, fit: true}}, parts: [{size: "
        "[512, 512]}]"), "a picture laid once per bay"));

    // An open part's posts in the trim: the band runs up the post (its texels across the post's height).
    const Game::OutdoorBModel shed = raisedPlot("door: none, eaves: 0, fascia: 0, textures: {trim: t14a05b}, parts: "
        "[{size: [512, 512], wall_height: 256, posts: 16, roof: flat}]");
    size_t posts = 0;

    for (const Game::OutdoorBModelFace *pFace : facesWith(shed, "t14a05b"))
    {
        const std::array<int, 2> heights = heightsOf(shed, *pFace);

        if (heights[1] - heights[0] >= 200 && std::fabs(faceNormal(shed, *pFace)[2]) < 1.0e-6)
        {
            ++posts;
            CHECK(*std::max_element(pFace->textureUs.begin(), pFace->textureUs.end())
                - *std::min_element(pFace->textureUs.begin(), pFace->textureUs.end()) == heights[1] - heights[0]);
        }
    }

    CHECK(posts == 16);

    // A wall raised 96 stands that much higher, its foot too.
    std::vector<ProjectIssue> issues;
    IdsLock ids;
    const OutdoorThings things = thingsOf("structures:\n"
        "  - {id: thing:low, kind: wall, line: [[70, 70], [80, 70]], height: 256}\n"
        "  - {id: thing:high, kind: wall, line: [[70, 70], [80, 70]], height: 256, raise: 96}\n", issues, ids);
    REQUIRE(issues.empty());
    REQUIRE(things.models.size() == 2);
    CHECK(things.models[1].maxZ == things.models[0].maxZ + 96);
    CHECK(things.models[1].minZ == things.models[0].minZ + 96);
}

TEST_CASE("O-D: a stepped pyramid with a stair cut into it, as Dragonsand's: treads, risers, cheeks")
{
    const Game::OutdoorBModel pyramid = raisedPlot("door: none, eaves: 0, fascia: 0, textures: {stair: t06a01, "
        "cheek: t14c01}, parts: [{size: [768, 768], at: [128, 0], wall_height: 256, steps: [[128, 128], "
        "[128, 128]], roof: flat, stair: {wall: s, width: 128, cheek: [32, 64], rise: 32}}]");
    // 512 to climb in risers of 32: 16 risers the party passes through and 16 treads.
    const std::vector<const Game::OutdoorBModelFace *> steps = facesWith(pyramid, "t06a01");
    CHECK(steps.size() == 32);
    const uint32_t untouchable = Game::faceAttributeBit(Game::FaceAttribute::Untouchable);
    size_t risers = 0;

    for (const Game::OutdoorBModelFace *pFace : steps)
    {
        risers += (pFace->attributes & untouchable) != 0 ? 1 : 0;
    }

    CHECK(risers == 16);
    // The terraces' treads at 896 and 1024, the top at 1152; none left over the stair's span.
    CHECK(facesBetween(pyramid, "t14a05", 640 + 512, 640 + 512) == 1);
    CHECK(facesBetween(pyramid, "t14a05", 640 + 256, 640 + 256) >= 4);
    const std::array<int, 4> stair = planBounds(pyramid, "t06a01");
    CHECK(stair[2] - stair[0] == 128);

    for (const Game::OutdoorBModelFace *pFace : facesWith(pyramid, "t14a05"))
    {
        double x = 0.0;
        double y = 0.0;

        for (const uint16_t index : pFace->vertexIndices)
        {
            x += pyramid.vertices[index].x / static_cast<double>(pFace->vertexIndices.size());
            y += pyramid.vertices[index].y / static_cast<double>(pFace->vertexIndices.size());
        }

        CHECK_FALSE((x > stair[0] - 31 && x < stair[2] + 31 && y < stair[3] - 1));
    }

    CHECK(facesWith(pyramid, "t14c01").size() >= 8);
    CHECK(anyIssue(buildingIssues("door: none, parts: [{size: [512, 512], stair: {wall: s}}]"),
        "a stair climbs a stepped or battered part"));
    CHECK(anyIssue(buildingIssues("door: none, parts: [{size: [512, 512], steps: [[300, 64]]}]"), "steps are"));
}

TEST_CASE("O-D: a ruin: bays to their own heights, some gone, a whole door, wall tops and bare rafters")
{
    const Game::OutdoorBModel ruin = raisedPlot("eaves: 0, fascia: 0, textures: {rafter: t14abcd11, wall_top: "
        "t14c01}, parts: [{size: [1024, 768], wall_height: 512, roof: gable, roof_height: 192, ruin: {height: [128, "
        "384], gaps: 0.3, roof: frame, every: 256, seed: 7}}]");
    // No roof, no gables: ten rafters and a ridge beam of six faces each.
    CHECK(facesWith(ruin, "t14a05").empty());
    CHECK(facesWith(ruin, "t14abcd11").size() == 66);
    std::set<int> tops;

    for (const Game::OutdoorBModelFace *pFace : facesWith(ruin, "t14a01"))
    {
        const std::array<int, 2> heights = heightsOf(ruin, *pFace);
        CHECK(heights[1] <= 640 + 384);
        tops.insert(heights[1]);
    }

    CHECK(tops.size() >= 3);
    const std::vector<const Game::OutdoorBModelFace *> doors = facesWith(ruin, "t14a03");
    REQUIRE(doors.size() == 1);
    CHECK(heightsOf(ruin, *doors[0]) == std::array<int, 2>{640, 896});
    CHECK(!facesWith(ruin, "t14c01").empty());
    CHECK(anyIssue(buildingIssues("door: none, parts: [{size: [512, 512], ruin: {gaps: 1.5}}]"), "a ruin is"));
}

namespace
{
// The edges of a model's drawn faces over `floor` (one end 8 or more over it) that no other face runs along for more
// than 8 units: a closed shell has none (tools/xeen/check_faces.py `shell.open_edge`).
size_t openEdgesOver(const Game::OutdoorBModel &model, int floor)
{
    using Point = std::array<double, 3>;
    struct Edge
    {
        Point from;
        Point to;
        size_t face = 0;
    };
    std::vector<Edge> edges;

    for (size_t face = 0; face < model.faces.size(); ++face)
    {
        const std::vector<uint16_t> &corners = model.faces[face].vertexIndices;

        for (size_t corner = 0; corner < corners.size(); ++corner)
        {
            const Game::OutdoorBModelVertex &a = model.vertices[corners[corner]];
            const Game::OutdoorBModelVertex &b = model.vertices[corners[(corner + 1) % corners.size()]];
            edges.push_back({{static_cast<double>(a.x), static_cast<double>(a.y), static_cast<double>(a.z)},
                {static_cast<double>(b.x), static_cast<double>(b.y), static_cast<double>(b.z)}, face});
        }
    }

    const auto onEdge = [](const Point &point, const Edge &edge)
    {
        const Point along = {edge.to[0] - edge.from[0], edge.to[1] - edge.from[1], edge.to[2] - edge.from[2]};
        const double squared = along[0] * along[0] + along[1] * along[1] + along[2] * along[2];
        double share = squared > 0.0 ? ((point[0] - edge.from[0]) * along[0] + (point[1] - edge.from[1]) * along[1]
            + (point[2] - edge.from[2]) * along[2]) / squared : 0.0;
        share = std::clamp(share, 0.0, 1.0);
        double distance = 0.0;

        for (size_t axis = 0; axis < 3; ++axis)
        {
            const double apart = point[axis] - edge.from[axis] - along[axis] * share;
            distance += apart * apart;
        }

        return distance <= 0.75 * 0.75;
    };
    size_t open = 0;

    for (const Edge &edge : edges)
    {
        if (std::max(edge.from[2], edge.to[2]) < floor + 8.0)
        {
            continue;
        }

        const double length = std::sqrt((edge.to[0] - edge.from[0]) * (edge.to[0] - edge.from[0])
            + (edge.to[1] - edge.from[1]) * (edge.to[1] - edge.from[1])
            + (edge.to[2] - edge.from[2]) * (edge.to[2] - edge.from[2]));
        const int steps = std::max(1, static_cast<int>(std::ceil(length / 2.0)));
        double bare = 0.0;

        for (int step = 0; step < steps; ++step)
        {
            const double share = (step + 0.5) / steps;
            const Point point = {edge.from[0] + (edge.to[0] - edge.from[0]) * share,
                edge.from[1] + (edge.to[1] - edge.from[1]) * share, edge.from[2] + (edge.to[2] - edge.from[2]) * share};
            const bool covered = std::any_of(edges.begin(), edges.end(), [&](const Edge &other)
            {
                return other.face != edge.face && onEdge(point, other);
            });
            bare += covered ? 0.0 : length / steps;
        }

        open += bare > 8.0 ? 1 : 0;
    }

    return open;
}
}

TEST_CASE("F30: a ruin is a closed shell: its corners closed by mitred inner faces and end faces")
{
    // A box with gaps and a door, and round parts of eight and twelve sides (the Ruined watchtower on X1, the Rim
    // Watch on D3): every edge over the floor runs along another face, and no faces lie on each other.
    for (const char *pPlot : {"textures: {wall_top: t14c01}, parts: [{size: [1024, 768], wall_height: 512, roof: "
             "none, ruin: {height: [128, 384], gaps: 0.3, seed: 7}}]",
             "door: none, parts: [{shape: round, at: [410, 410], radius: 320, sides: 8, wall_height: 448, roof: none, "
             "ruin: {height: [128, 448], gaps: 0.3, seed: 3}}]",
             "door: none, parts: [{shape: round, at: [512, 512], radius: 448, sides: 12, wall_height: 384, roof: none, "
             "ruin: {height: [96, 384], gaps: 0.2, thickness: 32, seed: 11}}]"})
    {
        CAPTURE(pPlot);
        const Game::OutdoorBModel ruin = raisedPlot(pPlot);
        CHECK(openEdgesOver(ruin, 640) == 0);
        CHECK(findOutdoorCoplanarFaces({ruin}).empty());
        CHECK(findOutdoorBackToBackFaces({ruin}).empty());
    }
}

TEST_CASE("O-D: eaves on chosen walls only; a recess under a hanging part leaves its underside out")
{
    const Game::OutdoorBModel house = raisedPlot("door: none, eaves: 64, fascia: 0, parts: [{size: [512, 512], "
        "roof: hip, roof_height: 128, eaves_walls: [s]}]");
    const std::array<int, 4> walls = planBounds(house, "t14a01");
    const std::array<int, 4> roof = planBounds(house, "t14a05");
    CHECK(roof[1] == walls[1] - 64);
    CHECK(roof[3] == walls[3]);
    CHECK(roof[0] == walls[0]);
    CHECK(facesBetween(house, "t14a05b", 896, 896) == 1);

    // New Sorpigal's temple: a part on posts of its own height with a recess under it.
    const Game::OutdoorBModel hanging = raisedPlot("door: none, eaves: 0, fascia: 0, parts: [{size: [1024, 768], "
        "bottom: 128, wall_height: 256, roof: flat, porches: [{wall: s, bays: [2, 5], depth: 128, recess: true}]}]");
    // The underside at 768 in pieces round the recess: none reaches into it.
    const std::array<int, 4> all = planBounds(hanging, "t14a01");

    for (const Game::OutdoorBModelFace *pFace : facesWith(hanging, "t14a05b"))
    {
        if (heightsOf(hanging, *pFace) != std::array<int, 2>{768, 768} || faceNormal(hanging, *pFace)[2] > 0.0)
        {
            continue;
        }

        for (const uint16_t index : pFace->vertexIndices)
        {
            const Game::OutdoorBModelVertex &vertex = hanging.vertices[index];
            const bool inRecess = vertex.x > all[0] + 256 + 1 && vertex.x < all[0] + 768 - 1
                && vertex.y < all[1] + 128 - 1;
            CHECK_FALSE(inRecess);
        }
    }
}

TEST_CASE("O-D: a battered town wall, one whose top follows the land, round and stepped platforms")
{
    std::vector<ProjectIssue> issues;
    IdsLock ids;
    const OutdoorThings wall = thingsOf("structures:\n  - {id: thing:wall, kind: wall, line: [[50, 50], [52, 50]], "
        "height: 384, thickness: 128, batter: 32, batter_height: 192, battlements: true}\n", issues, ids);
    const Game::OutdoorBModel *pWall = onlyModel(wall, issues);
    REQUIRE(pWall != nullptr);
    size_t sloped = 0;

    for (const Game::OutdoorBModelFace &face : pWall->faces)
    {
        const double z = faceNormal(*pWall, face)[2];
        sloped += z > 0.05 && z < 0.5 ? 1 : 0;
    }

    CHECK(sloped >= 2);
    CHECK(findOutdoorCoplanarFaces(wall.models).empty());

    std::vector<ProjectIssue> followIssues;
    const OutdoorThings follows = thingsOf("structures:\n  - {id: thing:wall, kind: wall, line: [[50, 50], [53, 50]], "
        "height: 256, thickness: 64, top: follow}\n", followIssues, ids);
    const Game::OutdoorBModel *pFollows = onlyModel(follows, followIssues);
    REQUIRE(pFollows != nullptr);
    int highest = 0;

    for (const Game::OutdoorBModelVertex &vertex : pFollows->vertices)
    {
        highest = std::max(highest, vertex.z);
    }

    CHECK(highest == 640 + 256);

    // An arched gate in a wall whose top follows the land: the lintel over the arch starts at the arch's apex, so
    // nothing stands across the gate under it (it went down into the land: Burlock's village wall, X4, 2026-11-24).
    std::vector<ProjectIssue> gateIssues;
    const OutdoorThings gated = thingsOf("structures:\n  - {id: thing:wall, kind: wall, line: [[50, 50], [56, 50]], "
        "height: 448, thickness: 128, top: follow, gates: [{at: [53, 50], width: 512, height: 384, arch: round}]}\n",
        gateIssues, ids);
    const Game::OutdoorBModel *pGated = onlyModel(gated, gateIssues);
    REQUIRE(pGated != nullptr);
    const int gateX = (53 - 64) * 512;
    size_t across = 0;

    for (const Game::OutdoorBModelFace &face : pGated->faces)
    {
        int minX = 1 << 30;
        int maxX = -(1 << 30);
        int minZ = 1 << 30;
        int maxZ = -(1 << 30);

        for (const uint16_t index : face.vertexIndices)
        {
            minX = std::min(minX, pGated->vertices[index].x);
            maxX = std::max(maxX, pGated->vertices[index].x);
            minZ = std::min(minZ, pGated->vertices[index].z);
            maxZ = std::max(maxZ, pGated->vertices[index].z);
        }

        across += minX < gateX && maxX > gateX && minZ < 640 + 100 && maxZ > 640 + 100 ? 1 : 0;
    }

    CHECK(across == 0);

    std::vector<ProjectIssue> padIssues;
    const OutdoorThings pad = thingsOf("structures:\n  - {id: thing:pad, kind: platform, at: [50, 50], sides: 8, "
        "radius: 256, height: 64, tiers: [[64, 64]], textures: {wall: t14c01, top: t06a01}}\n", padIssues, ids);
    const Game::OutdoorBModel *pPad = onlyModel(pad, padIssues);
    REQUIRE(pPad != nullptr);
    CHECK(facesBetween(*pPad, "t06a01", 640 + 64, 640 + 64) == 8);
    CHECK(facesBetween(*pPad, "t06a01", 640 + 128, 640 + 128) == 1);
    CHECK(facesWith(*pPad, "t14c01").size() == 16);

    std::vector<ProjectIssue> refused;
    thingsOf("structures:\n  - {id: thing:wall, kind: wall, line: [[50, 50], [52, 50]], height: 384, thickness: 128, "
        "batter: 100}\n", refused, ids);
    CHECK(anyIssue(refused, "a wall's `batter`"));
}

// ---- Land (outdoor code batch O-E): spires and peak fields, cuts with ramps, nested terraces, closed ridges,
// buildings against a slope with a ground skirt ----

namespace
{
double groundAt(const LoweredOutdoorMap &lowered, int x, int y)
{
    return lowered.ground[static_cast<size_t>(y) * OutdoorNodeCount + static_cast<size_t>(x)];
}

// The building project with more height words after the level land.
LoweredOutdoorMap loweredOnLand(const std::string &plots, const std::string &land)
{
    Project project = buildingProject(plots);
    ProjectFile &sketch = project.files["sketch.yml"];
    sketch.text.replace(sketch.text.find(LevelLand), std::string(LevelLand).size(), std::string(LevelLand) + land);
    sketch.document = YAML::Load(sketch.text);
    LoweredOutdoorMap lowered;
    std::vector<ProjectIssue> issues;
    const bool ok = lowerOutdoorProject(project, lowered, issues);

    for (const ProjectIssue &issue : issues)
    {
        MESSAGE(issue.path << ": " << issue.message);
    }

    REQUIRE(ok);
    return lowered;
}

}

TEST_CASE("O-E: a spire sets one node or a 2 x 2 column to its height, every neighbour as it was")
{
    const LoweredOutdoorMap lowered = loweredOf(std::string(LevelLand) + "  spires:\n"
        "    - {at: [50, 50], height: 5440}\n"
        "    - {at: [60.5, 60.5], height: 4800, width: 2}\n");

    CHECK(groundAt(lowered, 50, 50) == doctest::Approx(5440.0));

    for (const std::array<int, 2> &near : std::vector<std::array<int, 2>>{{49, 50}, {51, 50}, {50, 49}, {51, 51}})
    {
        CHECK(groundAt(lowered, near[0], near[1]) == doctest::Approx(640.0));
    }

    for (int y = 60; y <= 61; ++y)
    {
        for (int x = 60; x <= 61; ++x)
        {
            CHECK(groundAt(lowered, x, y) == doctest::Approx(4800.0));
        }
    }

    CHECK(groundAt(lowered, 59, 60) == doctest::Approx(640.0));
    CHECK(groundAt(lowered, 62, 61) == doctest::Approx(640.0));
    // The whole rise within one cell: as steep as the format holds.
    CHECK((sampleAt(lowered, 50, 50) - sampleAt(lowered, 51, 50)) * 32 == 5440 - 640);
    const auto refused = [](const std::string &entry, const std::string &fragment)
    {
        CAPTURE(entry);
        CHECK(anyIssue(refusedWith(std::string(LevelLand) + "  spires:\n    - " + entry + "\n"), fragment));
    };
    refused("{at: [50, 50]}", "a spire's `height`");
    refused("{at: [50, 50], height: 9000}", "0 to 8160");
    refused("{at: [50, 50], height: 2000, width: 3}", "1 (the node at `at`) or 2");
    refused("{at: [130, 50], height: 2000}", "a spire's `at`");
}

TEST_CASE("O-E: a peak field puts its count of tops in the area, apart, only raising the land, the same each time")
{
    const std::string field = "  peaks:\n    - {polygon: [[30, 30], [90, 30], [90, 90], [30, 90]], count: 20, "
        "height: [3000, 5000], radius: [2, 3], spacing: 6}\n";
    const LoweredOutdoorMap lowered = loweredOf(std::string(LevelLand) + field);
    std::vector<std::array<int, 2>> tops;

    for (int y = 0; y < Side; ++y)
    {
        for (int x = 0; x < Side; ++x)
        {
            const double height = groundAt(lowered, x, y);
            CHECK(height >= 640.0 - 1.0e-6);

            if (x < 29 || x > 91 || y < 29 || y > 91)
            {
                CHECK(height == doctest::Approx(640.0));
            }

            bool top = height >= 3000.0 - 1.0e-6;

            for (int dy = -1; top && dy <= 1; ++dy)
            {
                for (int dx = -1; dx <= 1; ++dx)
                {
                    top = top && ((dx == 0 && dy == 0) || groundAt(lowered, x + dx, y + dy) < height);
                }
            }

            if (top)
            {
                tops.push_back({x, y});
                CHECK(height <= 5000.0 + 1.0e-6);
                CHECK(x >= 30);
                CHECK(x <= 90);
            }
        }
    }

    CHECK(tops.size() == 20);

    for (size_t first = 0; first < tops.size(); ++first)
    {
        for (size_t second = first + 1; second < tops.size(); ++second)
        {
            CHECK(std::hypot(tops[first][0] - tops[second][0], tops[first][1] - tops[second][1]) >= 6.0);
        }
    }

    // A cone: the node beside a top stands between the top and the land.
    const double beside = groundAt(lowered, tops[0][0] + 1, tops[0][1]);
    CHECK(beside > 640.0);
    CHECK(beside < groundAt(lowered, tops[0][0], tops[0][1]));
    CHECK(loweredOf(std::string(LevelLand) + field).samples == lowered.samples);
    std::string seeded = field;
    seeded.replace(seeded.find("spacing: 6"), 10, "spacing: 6, seed: 9");
    CHECK(loweredOf(std::string(LevelLand) + seeded).samples != lowered.samples);
    // Needles: only the tops change; a field too dense for its spacing says so.
    const LoweredOutdoorMap needles = loweredOf(std::string(LevelLand) + "  peaks:\n    - {polygon: [[40, 40], "
        "[44, 40], [44, 44], [40, 44]], count: 30, rise: 2000, spacing: 2}\n");
    size_t raised = 0;

    for (int y = 38; y <= 46; ++y)
    {
        for (int x = 38; x <= 46; ++x)
        {
            const double height = groundAt(needles, x, y);
            raised += height > 640.0 ? 1 : 0;
            CHECK((height == doctest::Approx(640.0) || height == doctest::Approx(2640.0)));
        }
    }

    CHECK(raised >= 4);
    CHECK(raised <= 9);
    CHECK(anyWarning(needles, "of 30 peaks fit in the area"));
    const auto refused = [](const std::string &entry, const std::string &fragment)
    {
        CAPTURE(entry);
        CHECK(anyIssue(refusedWith(std::string(LevelLand) + "  peaks:\n    - " + entry + "\n"), fragment));
    };
    const std::string area = "polygon: [[30, 30], [90, 30], [90, 90], [30, 90]]";
    refused("{" + area + ", count: 5}", "one of the two");
    refused("{" + area + ", count: 5, height: 2000, rise: 300}", "one of the two");
    refused("{" + area + ", count: 0, height: 2000}", "1 to 2000");
    refused("{" + area + ", count: 5, height: [4000, 2000]}", "[low, high]");
    refused("{" + area + ", count: 5, height: 2000, profile: cone}", "base `radius` above 0");
    refused("{" + area + ", count: 5, height: 2000, profile: spike}", "needle (the top only");
    refused("{" + area + ", count: 5, height: 2000, radius: 20}", "0 to 16");
}

TEST_CASE("O-E: a cut: its floor inside, walls as high as the land on its outline, an open edge that runs out")
{
    // A slot cut into a plateau at 1856: floor 160, open to the south where the land beyond runs down to it.
    const std::string plateau = "  terraces:\n    - {polygon: [[30, 30], [70, 30], [70, 70], [30, 70]], height: "
        "1856}\n";
    const LoweredOutdoorMap lowered = loweredOf(std::string(LevelLand) + plateau + "  cuts:\n"
        "    - {polygon: [[40, 40], [44, 40], [44, 50], [40, 50]], floor: 160, open: [2], slope: 4}\n");

    for (int y = 41; y <= 50; ++y)
    {
        for (int x = 41; x <= 43; ++x)
        {
            CHECK(groundAt(lowered, x, y) == doctest::Approx(160.0));
        }
    }

    // The walls: the outline's nodes keep the plateau, a one-node cliff 1696 high.
    for (int y = 40; y <= 50; ++y)
    {
        CHECK(groundAt(lowered, 40, y) == doctest::Approx(1856.0));
        CHECK(groundAt(lowered, 44, y) == doctest::Approx(1856.0));
    }

    CHECK(groundAt(lowered, 42, 40) == doctest::Approx(1856.0));
    // Beyond the open edge the plateau runs down to the floor over four cells, square in front of it only.
    CHECK(groundAt(lowered, 42, 52) == doctest::Approx(1856.0 + (160.0 - 1856.0) * 0.5));
    CHECK(groundAt(lowered, 42, 54) == doctest::Approx(1856.0));
    CHECK(groundAt(lowered, 39, 51) == doctest::Approx(1856.0));
    CHECK(groundAt(lowered, 45, 51) == doctest::Approx(1856.0));
    // A cut inside a cut steps down from its floor; a ramp left without heights runs from the land at one end to
    // the other.
    const LoweredOutdoorMap nested = loweredOf(std::string(LevelLand) + plateau + "  cuts:\n"
        "    - polygon: [[40, 40], [60, 40], [60, 60], [40, 60]]\n      floor: 1024\n"
        "      ramps:\n        - {line: [[50, 40], [50, 46]]}\n"
        "    - {polygon: [[45, 45], [55, 45], [55, 55], [45, 55]], floor: 0}\n");
    CHECK(groundAt(nested, 50, 50) == doctest::Approx(0.0));
    CHECK(groundAt(nested, 45, 50) == doctest::Approx(1024.0));
    CHECK(groundAt(nested, 42, 50) == doctest::Approx(1024.0));
    CHECK(groundAt(nested, 50, 40) == doctest::Approx(1856.0));
    CHECK(groundAt(nested, 50, 43) == doctest::Approx(1856.0 + (0.0 - 1856.0) * 0.5));
    CHECK(groundAt(nested, 50, 46) == doctest::Approx(0.0));
    CHECK(groundAt(nested, 49, 43) == doctest::Approx(1024.0));
    // A cut whose outline stands no higher than its floor has no walls, and the build says so.
    CHECK(anyWarning(loweredOf(std::string(LevelLand) + "  cuts:\n    - {polygon: [[40, 40], [44, 40], [44, 44], "
        "[40, 44]], floor: 640}\n"), "no wall where they are"));
    const auto refused = [](const std::string &entry, const std::string &fragment)
    {
        CAPTURE(entry);
        CHECK(anyIssue(refusedWith(std::string(LevelLand) + "  cuts:\n    - " + entry + "\n"), fragment));
    };
    const std::string outline = "polygon: [[40, 40], [44, 40], [44, 44], [40, 44]]";
    refused("{polygon: [[40, 40], [44, 40]], floor: 0}", "a cut's `polygon`");
    refused("{" + outline + "}", "a cut's `floor`");
    refused("{" + outline + ", floor: 0, open: [4]}", "0 to 3");
    refused("{" + outline + ", floor: 0, slope: 20}", "a cut's `slope`");
    refused("{" + outline + ", floor: 0, ramps: [{line: [[41, 41], [43, 43]], slope: 2}]}", "a ramp has no sides");
    refused("{" + outline + ", floor: 0, ramps: [{line: [[41, 41], [43, 43]], closed: true}]}", "a ridge's word");
}

TEST_CASE("O-E: nested terraces with sheer steps and ramps across them, as Castle Ironfist's pit")
{
    // The pit's rings: a rim at 1856, then 1248 and 640 two nodes in each, a floor at 0; a ramp from the 640 ring
    // down to the floor and one up the rim's side.
    const LoweredOutdoorMap lowered = loweredOf(std::string(LevelLand) + "  terraces:\n"
        "    - polygon: [[32, 63], [49, 63], [49, 83], [32, 83]]\n      height: 1856\n"
        "      steps: [[2, 1248], [4, 640], [6, 0]]\n"
        "      ramps:\n        - {line: [[36.5, 69], [36.5, 75]], height: [640, 96]}\n"
        "        - {line: [[40, 85], [40, 83]]}\n");
    CHECK(groundAt(lowered, 32, 70) == doctest::Approx(1856.0));
    CHECK(groundAt(lowered, 33, 70) == doctest::Approx(1856.0));
    CHECK(groundAt(lowered, 34, 70) == doctest::Approx(1248.0));
    CHECK(groundAt(lowered, 35, 70) == doctest::Approx(1248.0));
    CHECK(groundAt(lowered, 38, 70) == doctest::Approx(0.0));
    CHECK(groundAt(lowered, 40, 65) == doctest::Approx(1248.0));
    CHECK(groundAt(lowered, 40, 67) == doctest::Approx(640.0));
    CHECK(groundAt(lowered, 40, 75) == doctest::Approx(0.0));
    // Each ring's edge is a sheer step of one node.
    CHECK((sampleAt(lowered, 33, 70) - sampleAt(lowered, 34, 70)) * 32 == 1856 - 1248);
    // The first ramp: both nodes beside its half-cell line, graded from 640 to 96.
    CHECK(groundAt(lowered, 36, 69) == doctest::Approx(640.0));
    CHECK(groundAt(lowered, 37, 72) == doctest::Approx(640.0 + (96.0 - 640.0) * 0.5));
    CHECK(groundAt(lowered, 36, 75) == doctest::Approx(96.0));
    // The second, without heights, from the land at its foot (640) to the rim (1856).
    CHECK(groundAt(lowered, 40, 84) == doctest::Approx(1248.0));
    CHECK(groundAt(lowered, 40, 83) == doctest::Approx(1856.0));
    CHECK(anyIssue(refusedWith(std::string(LevelLand) + "  terraces:\n    - {polygon: [[32, 63], [49, 63], [49, 83]], "
        "height: 1856, steps: [[4, 640], [2, 1248]]}\n"), "nested rings"));
}

TEST_CASE("O-E: a closed ridge runs back to its first point: a crater's rim round a hollow")
{
    const std::string rim = "  ridges:\n    - {line: [[40, 40], [46, 40], [46, 46], [40, 46]], closed: true, "
        "height: 1664}\n";
    const LoweredOutdoorMap open = loweredOf(std::string(LevelLand) + "  ridges:\n    - {line: [[40, 40], [46, 40], "
        "[46, 46], [40, 46]], height: 1664}\n");
    const LoweredOutdoorMap closed = loweredOf(std::string(LevelLand) + rim + "  cuts:\n    - {polygon: [[40, 40], "
        "[46, 40], [46, 46], [40, 46]], floor: 96}\n");
    CHECK(groundAt(open, 40, 43) == doctest::Approx(640.0));
    CHECK(groundAt(closed, 40, 43) == doctest::Approx(1664.0));
    CHECK(groundAt(closed, 43, 40) == doctest::Approx(1664.0));
    CHECK(groundAt(closed, 43, 43) == doctest::Approx(96.0));
    CHECK(groundAt(closed, 39, 43) == doctest::Approx(640.0));
    CHECK(anyIssue(refusedWith(std::string(LevelLand) + "  ridges:\n    - {line: [[40, 40], [46, 40]], closed: true, "
        "height: 900}\n"), "a ring of at least three"));
    CHECK(anyIssue(refusedWith(std::string(LevelLand) + "  ridges:\n    - {line: [[40, 40], [46, 40], [46, 46]], "
        "closed: yes, height: 900}\n"), "`closed` is true"));
}

TEST_CASE("O-E: a building against a slope: no back wall, the hill kept under it, the front row at the floor")
{
    // A hill north of the plot (rows 36 to 40 at 1280); the plot's rows 40 and 41, its front to the south.
    const std::string hill = "  terraces:\n    - {polygon: [[36, 36], [46, 36], [46, 40], [36, 40]], height: 1280}\n";
    const std::string plot = "      - {building: building:home, at: [40, 40], facing: s, door: none, floor: 640, "
        "eaves: 0, fascia: 0, parts: [{size: [1024, 768], wall_height: 384, roof: flat}]";
    const LoweredOutdoorMap against = loweredOnLand(plot + ", against: slope}\n", hill);
    const LoweredOutdoorMap plain = loweredOnLand(plot + "}\n", hill);
    REQUIRE(against.buildings.size() == 1);
    CHECK(against.buildings[0].against);
    CHECK(groundAt(plain, 41, 40) == doctest::Approx(640.0));
    CHECK(groundAt(against, 41, 40) == doctest::Approx(1280.0));
    CHECK(groundAt(against, 41, 41) == doctest::Approx(640.0));
    CHECK_FALSE(anyWarning(against, "its inside shows"));
    OutdoorBuildingPlan againstPlan = against.buildings[0];
    OutdoorBuildingPlan plainPlan = plain.buildings[0];
    const Game::OutdoorBModel withoutBack = raiseOutdoorBuilding(againstPlan);
    const Game::OutdoorBModel withBack = raiseOutdoorBuilding(plainPlan);
    const auto facing = [](const Game::OutdoorBModel &model, int direction)
    {
        size_t count = 0;

        for (const Game::OutdoorBModelFace &face : model.faces)
        {
            const std::array<double, 3> normal = faceNormal(model, face);
            const double length = std::hypot(normal[0], normal[1], normal[2]);
            count += length > 0.0 && normal[1] * direction / length > 0.9 ? 1 : 0;
        }

        return count;
    };
    CHECK(facing(withBack, 1) > 0);
    CHECK(facing(withoutBack, 1) == 0);
    CHECK(facing(withoutBack, -1) == facing(withBack, -1));
    // Land lower than the walls' top behind it: the inside shows, and the build says so.
    CHECK(anyWarning(loweredOnLand(plot + ", against: slope}\n", ""), "its inside shows"));
    CHECK(anyIssue(buildingIssues("against: cliff, parts: [{size: [512, 512]}]"), "against is slope"));
}

TEST_CASE("O-E: a ground skirt carries the walls down below the lowest land round the plot in the ground's texture")
{
    // A plot on a terrace edge: its south half over land 512 lower.
    const std::string edge = "  terraces:\n    - {polygon: [[36, 36], [46, 36], [46, 40.5], [36, 40.5]], height: "
        "1152}\n";
    const std::string plot = "      - {building: building:home, at: [40, 40], facing: s, door: none, floor: 1152, "
        "eaves: 0, fascia: 0, skirt: ground, parts: [{size: [1024, 768], wall_height: 384, roof: flat}]}\n";
    const LoweredOutdoorMap lowered = loweredOnLand(plot, edge);
    REQUIRE(lowered.buildings.size() == 1);
    // The land under the plot is not made level.
    CHECK(groundAt(lowered, 41, 41) == doctest::Approx(640.0));
    CHECK(lowered.buildings[0].foundation == doctest::Approx(1152.0 - 640.0 + 64.0));
    OutdoorBuildingPlan plan = lowered.buildings[0];
    const Game::OutdoorBModel model = raiseOutdoorBuilding(plan);
    CHECK(facesWith(model, "dirttyl").size() == 4);
    CHECK(facesBetween(model, "dirttyl", 640 - 64, 1152) == 4);
    CHECK(loweredOnLand(std::string(plot).replace(plot.find("skirt: ground"), 13, "skirt: 7dirttyl"), edge)
        .buildings[0].skirt == "7dirttyl");
    CHECK(anyIssue(buildingIssues("skirt: ground, foundation: 0, parts: [{size: [512, 512]}]"), "a skirt is"));
}

TEST_CASE("O-E: the land words are in the sketch schema, every one described")
{
    const YAML::Node root = inlinedSketchSchema();
    const YAML::Node heights = root["properties"]["heights"]["properties"];
    const std::map<std::string, std::vector<const char *>> words = {
        {"spires", {"at", "height", "width"}},
        {"peaks", {"polygon", "count", "height", "rise", "radius", "profile", "width", "spacing", "seed"}},
        {"cuts", {"polygon", "floor", "open", "slope", "ramps"}},
        {"terraces", {"steps", "ramps"}},
        {"ridges", {"closed"}},
    };

    for (const auto &[list, names] : words)
    {
        CHECK(heights[list]["description"].IsDefined());

        for (const char *pWord : names)
        {
            CAPTURE(list);
            CAPTURE(pWord);
            CHECK(heights[list]["items"]["properties"][pWord]["description"].IsDefined());
        }
    }

    const YAML::Node plots = root["properties"]["districts"]["items"]["properties"]["plots"]["items"]["properties"];
    const YAML::Node structures = root["properties"]["structures"]["items"]["properties"];

    for (const char *pWord : {"against", "skirt"})
    {
        CAPTURE(pWord);
        CHECK(plots[pWord]["description"].IsDefined());
        CHECK(structures[pWord]["description"].IsDefined());
    }
}

namespace
{
// Batch O-F: the faces of a model whose every corner lies at or above a height.
size_t facesAbove(const Game::OutdoorBModel &model, int low)
{
    size_t count = 0;

    for (const Game::OutdoorBModelFace &face : model.faces)
    {
        bool above = true;

        for (const uint16_t index : face.vertexIndices)
        {
            above = above && model.vertices[index].z >= low;
        }

        count += above ? 1 : 0;
    }

    return count;
}

const Game::OutdoorBModel *builtModel(const std::string &structures, std::vector<ProjectIssue> &issues)
{
    static IdsLock ids;
    static OutdoorThings things;
    things = thingsOf("structures:\n" + structures, issues, ids);

    for (const ProjectIssue &issue : issues)
    {
        MESSAGE(issue.path << ": " << issue.message);
    }

    return issues.empty() && things.models.size() == 1 && findOutdoorCoplanarFaces(things.models).empty()
        ? &things.models[0] : nullptr;
}
}

TEST_CASE("O-F: a portal is a ring round a membrane whose picture moves, on a dais, every face running its event")
{
    std::vector<ProjectIssue> issues;
    const Game::OutdoorBModel *pGate = builtModel("  - {id: thing:gate, kind: portal, at: [50, 50], title: Gate, "
        "into: {map: elemf.odm}, textures: {frame: gn_mtl03, dais: gn_mtl01, membrane: LavTyl}}\n", issues);
    REQUIRE(pGate != nullptr);
    const uint32_t flowRight = Game::faceAttributeBit(Game::FaceAttribute::FlowRight);
    // Both sides of the membrane, the picture moving right as the Planes' gates (0x800).
    CHECK(texturedFaces(*pGate, "LavTyl", flowRight) == 2);
    CHECK(texturedFaces(*pGate, "gn_mtl03", flowRight) == 0);
    std::set<uint16_t> events;

    for (const Game::OutdoorBModelFace &face : pGate->faces)
    {
        events.insert(face.cogTriggeredNumber);
    }

    CHECK(events.size() == 1);
    CHECK(*events.begin() != 0);
    // gw_fire_N's measures: 384 by 256 on a skirt of 64, the ring's foot on the dais 48 up, its top 352 up.
    CHECK(pGate->maxX - pGate->minX == 512);
    CHECK(pGate->maxY - pGate->minY == 384);
    CHECK(pGate->minZ == 640);
    CHECK(pGate->maxZ == 640 + 352);
    // Turned 90 it spans north to south.
    issues.clear();
    const Game::OutdoorBModel *pTurned = builtModel("  - {id: thing:gate, kind: portal, at: [50, 50], turn: 90, "
        "dais: false, radius: 256}\n", issues);
    REQUIRE(pTurned != nullptr);
    CHECK(pTurned->maxY - pTurned->minY == 576);
    CHECK(pTurned->maxX - pTurned->minX == 32);
    CHECK(pTurned->minZ == 640);
    issues.clear();
    builtModel("  - {id: thing:gate, kind: portal, at: [50, 50], sides: 40}\n", issues);
    CHECK(anyIssue(issues, "a portal is a ring"));
}

TEST_CASE("O-F: a free-standing arch, and ribs rising to a hub at the angles given")
{
    std::vector<ProjectIssue> issues;
    const Game::OutdoorBModel *pArch = builtModel("  - {id: thing:arch, kind: arch, line: [[49, 50], [51, 50]], "
        "height: 600, width: 48, depth: 32}\n", issues);
    REQUIRE(pArch != nullptr);
    CHECK(pArch->maxZ == 640 + 600);
    CHECK(pArch->minZ >= 640 - 8);
    // The feet stand half a beam's depth out from the line's ends.
    CHECK(pArch->minX == doctest::Approx(-15.0 * 512 - 16.0).epsilon(0.001));
    CHECK(pArch->maxY - pArch->minY == 48);
    issues.clear();
    const Game::OutdoorBModel *pRibs = builtModel("  - {id: thing:tele, kind: arch, at: [50, 50], angles: [180, 50, "
        "310], radius: 646, height: 360, width: 46, hub: 93, curve: 1.6, segments: 4}\n", issues);
    REQUIRE(pRibs != nullptr);
    CHECK(pRibs->maxZ == 640 + 360);
    // The rib at 180 runs north: its foot 646 north of the middle.
    CHECK(pRibs->maxY == 14 * 512 + 646);
    // Three ribs of four steps (four faces each) and the hub.
    CHECK(pRibs->faces.size() == 3 * 4 * 4 + 6 + 2);
    issues.clear();
    builtModel("  - {id: thing:arch, kind: arch, at: [50, 50], ribs: 2}\n", issues);
    CHECK(anyIssue(issues, "two ribs are one arch"));
}

TEST_CASE("O-F: a stone ring of trilithons round an altar, standing stones, and one trilithon")
{
    std::vector<ProjectIssue> issues;
    const Game::OutdoorBModel *pRing = builtModel("  - {id: thing:henge, kind: stone_ring, at: [50, 50], count: 4, "
        "radius: 400, stone: [128, 96, 256], gap: 160, altar: [160, 160, 112], title: Altar, hint: Stonehenge, "
        "textures: {wall: Cwb1, altar: CWB}}\n", issues);
    REQUIRE(pRing != nullptr);
    // Four trilithons: two uprights without tops (five faces each with a bottom? no: four sides) and a lintel
    // (four sides, top, underside); the altar five faces, the used part.
    CHECK(pRing->faces.size() == 4 * (4 + 4 + 6) + 5);
    CHECK(pRing->maxZ == 640 + 256 + 72);
    CHECK(texturedFaces(*pRing, "CWB") == 5);
    std::set<uint16_t> altar;
    std::set<uint16_t> stones;

    for (const Game::OutdoorBModelFace &face : pRing->faces)
    {
        (face.textureName == "CWB" ? altar : stones).insert(face.cogTriggeredNumber);
    }

    CHECK(altar.size() == 1);
    CHECK(stones.size() == 1);
    CHECK(*altar.begin() != *stones.begin());
    issues.clear();
    const Game::OutdoorBModel *pStones = builtModel("  - {id: thing:circle, kind: stone_ring, at: [50, 50], angles: "
        "[0, 90, 200], lintel: false, seed: 4, stone: [96, 64, 200]}\n", issues);
    REQUIRE(pStones != nullptr);
    CHECK(pStones->faces.size() == 3 * 5);
    issues.clear();
    const Game::OutdoorBModel *pOne = builtModel("  - {id: thing:t, kind: trilithon, at: [50, 50], turn: 90}\n",
        issues);
    REQUIRE(pOne != nullptr);
    // Turned 90 its opening looks west: the uprights stand north and south of each other.
    CHECK(pOne->maxY - pOne->minY > pOne->maxX - pOne->minX);
    issues.clear();
    builtModel("  - {id: thing:t, kind: stone_ring, at: [50, 50], stone: [128, 96]}\n", issues);
    CHECK(anyIssue(issues, "stone ring"));
}

TEST_CASE("O-F: a walkway's deck follows its points' heights, with kerbs, piers to the land and a framed end")
{
    std::vector<ProjectIssue> issues;
    const Game::OutdoorBModel *pWalk = builtModel("  - {id: thing:walk, kind: walkway, line: [[44, 50, 1744], "
        "[47, 50, 1744], [47, 52, 1904]], textures: {top: 7t1beds2, wall: 7gt003a, post: 7t1books1}}\n", issues);
    REQUIRE(pWalk != nullptr);
    // Barrow Downs' measures: the floor 1744, kerbs to 1824, piers 128 over them.
    CHECK(pWalk->maxZ == 1904 + 80 + 128);
    // The floor and underside of the level stretch; of the rising one, which bends at its foot, two triangles each.
    CHECK(texturedFaces(*pWalk, "7t1beds2") == 2 + 4);
    // Piers at the three points (no stretch is longer than 1536), two posts each, eight sides and a top.
    CHECK(texturedFaces(*pWalk, "7t1books1") == 3 * 2 * 9);
    CHECK(pWalk->minZ == 640 - 32);
    issues.clear();
    const Game::OutdoorBModel *pEnd = builtModel("  - {id: thing:walk, kind: walkway, line: [[44, 50, 736], "
        "[46, 50, 736]], piers: 0, ends: [open, frame], frame_height: 352}\n", issues);
    REQUIRE(pEnd != nullptr);
    // The deck 96 over the land at its framed end: three steps down to it, a hidden slope over them, the risers
    // and the deck's end let through.
    size_t hidden = 0;
    size_t through = 0;

    for (const Game::OutdoorBModelFace &face : pEnd->faces)
    {
        hidden += (face.attributes & InvisibleBit) != 0 ? 1 : 0;
        through += (face.attributes & UntouchableBit) != 0 ? 1 : 0;
    }

    CHECK(hidden == 1);
    CHECK(through == 3);
    CHECK(pEnd->maxZ == 736 + 352 + 64);
    issues.clear();
    builtModel("  - {id: thing:walk, kind: walkway, line: [[44, 50, 0], [44.1, 50, 2000]]}\n", issues);
    CHECK(anyIssue(issues, "rising at most 45 degrees"));
}

TEST_CASE("O-F: a deck of an outline that bends in, on posts, and a house standing on it")
{
    const std::string deck = "  - {id: thing:deck, kind: deck, outline: [[44, 44], [48, 44], [48, 46], [46, 46], "
        "[46, 48], [44, 48]], level: 896, posts: 32}\n";
    std::vector<ProjectIssue> issues;
    const Game::OutdoorBModel *pDeck = builtModel(deck, issues);
    REQUIRE(pDeck != nullptr);
    double area = 0.0;

    for (const Game::OutdoorBModelFace &face : pDeck->faces)
    {
        if (face.planeNormalZ > 60000)
        {
            std::vector<Point2> points;

            for (const uint16_t index : face.vertexIndices)
            {
                points.push_back({static_cast<double>(pDeck->vertices[index].x),
                    static_cast<double>(pDeck->vertices[index].y)});
            }

            area += polygonDoubleArea(points) * 0.5;
        }
    }

    // An L of 12 cells.
    CHECK(std::fabs(area) == doctest::Approx(12.0 * 512 * 512));
    CHECK(pDeck->maxZ == 896);
    CHECK(pDeck->minZ == 640 - 32);
    const LoweredOutdoorMap lowered = loweredBuildings("      - {building: building:home, at: [44.5, 44.5], facing: s, "
        "on: thing:deck, door: none, parts: [{size: [512, 512]}]}\n", "structures:\n" + deck);
    REQUIRE(lowered.buildings.size() == 1);
    CHECK(lowered.buildings[0].base == doctest::Approx(896.0));
    CHECK(lowered.buildings[0].foundation == doctest::Approx(32.0));
    // The land under it stays.
    CHECK(groundAt(lowered, 45, 45) == doctest::Approx(640.0));
    CHECK(anyIssue(buildingIssues("on: thing:nothing, door: none"), "`on` names a structure of `kind: deck`"));
    CHECK(anyIssue(buildingIssues("on: thing:deck, floor: 900, door: none"), "a building `on` a deck"));
}

TEST_CASE("O-F: a tent: walls leaning in under a gable, the front open under an awning, and an A-frame")
{
    std::vector<ProjectIssue> issues;
    const Game::OutdoorBModel *pTent = builtModel("  - {id: thing:tent, kind: tent, at: [50, 50], size: [976, 672], "
        "wall_height: 288, lean: 96, height: 400, awning: 192, textures: {canvas: GNecClg2, inner: t06a10, "
        "pole: t06c11}}\n", issues);
    REQUIRE(pTent != nullptr);
    // Two slopes, two side walls and the back wall and gable, each both ways; no front.
    CHECK(texturedFaces(*pTent, "GNecClg2") == 6);
    CHECK(texturedFaces(*pTent, "t06a10") == 6);
    CHECK(pTent->maxZ == 640 + 400);
    // The awning reaches 192 south of the walls' top at the front.
    CHECK(pTent->minY == 14 * 512 - (488 - 96) - 192);
    // F31: the inner side in another picture lies 2 inward of the canvas, so none lies back to back with it.
    CHECK(findOutdoorBackToBackFaces({*pTent}).empty());
    issues.clear();
    const Game::OutdoorBModel *pFrame = builtModel("  - {id: thing:a, kind: tent, at: [50, 50], open: false}\n",
        issues);
    REQUIRE(pFrame != nullptr);
    // Two slopes and two gables, both ways, and two poles.
    CHECK(pFrame->faces.size() == 8 + 2 * 4);
    // F31: in one picture the canvas is drawn once (the game draws outdoor faces from both sides) over a hidden inner
    // face the party still meets.
    CHECK(findOutdoorBackToBackFaces({*pFrame}).empty());
    CHECK(findOutdoorCoplanarFaces({*pFrame}).empty());
    size_t hidden = 0;

    for (const Game::OutdoorBModelFace &face : pFrame->faces)
    {
        hidden += Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::Invisible) ? 1 : 0;
    }

    CHECK(hidden == 4);
    issues.clear();
    builtModel("  - {id: thing:a, kind: tent, at: [50, 50], open: false, awning: 100}\n", issues);
    CHECK(anyIssue(issues, "an awning needs the open front"));
}

TEST_CASE("F31: faces back to back: a sheet laid both ways is found, one 2 apart or hidden is not")
{
    const auto sheet = [](double apart, bool hide)
    {
        Game::OutdoorBModel model;
        OutdoorModelBuilder builder(model);
        builder.addSurface({{0.0, 0.0, 0.0}, {256.0, 0.0, 0.0}, {256.0, 0.0, 256.0}, {0.0, 0.0, 256.0}}, "t14a01", 0);
        const int back = builder.addSurface({{0.0, apart, 256.0}, {256.0, apart, 256.0}, {256.0, apart, 0.0},
            {0.0, apart, 0.0}}, "t14a01", 0);

        if (hide)
        {
            builder.hide(back);
        }

        builder.finish();
        return model;
    };
    const std::vector<OutdoorCoplanarPair> pairs = findOutdoorBackToBackFaces({sheet(0.0, false)});
    REQUIRE(pairs.size() == 1);
    CHECK(pairs[0].area == doctest::Approx(256.0 * 256.0));
    CHECK(findOutdoorCoplanarFaces({sheet(0.0, false)}).empty());
    CHECK(findOutdoorBackToBackFaces({sheet(1.0, false)}).size() == 1);
    CHECK(findOutdoorBackToBackFaces({sheet(2.0, false)}).empty());
    CHECK(findOutdoorBackToBackFaces({sheet(0.0, true)}).empty());
    // Two models, one face each, are compared too.
    Game::OutdoorBModel first = sheet(0.0, false);
    Game::OutdoorBModel second = first;
    first.faces.pop_back();
    second.faces.erase(second.faces.begin());
    CHECK(findOutdoorBackToBackFaces({first, second}).size() == 1);
    CHECK(describeOutdoorCoplanarPair({sheet(0.0, false)}, pairs[0], {}, true).find("back to back")
        != std::string::npos);
}

TEST_CASE("O-F: an arcade: openings under arches between piers, open through, its top walkable")
{
    std::vector<ProjectIssue> issues;
    const Game::OutdoorBModel *pArcade = builtModel("  - {id: thing:arcade, kind: arcade, line: [[48, 50], "
        "[48, 47.5]], height: 512, depth: 96, bays: 3, pier: 128, spring: 256, textures: {wall: Ceb1sa, under: "
        "7t1beds2, top: 7trimd}}\n", issues);
    REQUIRE(pArcade != nullptr);
    // Castle Navan's measures: three openings 256 wide; each two jambs and four soffit steps.
    CHECK(texturedFaces(*pArcade, "7t1beds2") == 3 * (2 + 4));
    CHECK(texturedFaces(*pArcade, "7trimd") == 1);
    CHECK(pArcade->maxZ == 640 + 512);
    // The soffits' crown 128 over the springing.
    CHECK(facesBetween(*pArcade, "7t1beds2", 640 + 256, 640 + 384) == 3 * 4);
    issues.clear();
    const Game::OutdoorBModel *pPointed = builtModel("  - {id: thing:arcade, kind: arcade, line: [[48, 50], "
        "[48, 47.5]], bays: 3, arch: pointed, sides: 6}\n", issues);
    REQUIRE(pPointed != nullptr);
    issues.clear();
    builtModel("  - {id: thing:arcade, kind: arcade, line: [[48, 50], [48, 49.5]], bays: 4}\n", issues);
    CHECK(anyIssue(issues, "an arcade stands"));
}

TEST_CASE("O-F: a portico of round columns under a flat ceiling, its band and a pediment; round posts on an open part")
{
    const std::string plot = "door: none, textures: {post: OrAltMrb, capital: OCap, trim: OCeil}, parts: [{size: "
        "[512, 768], wall_height: 640, roof: flat, porches: [{wall: s, form: portico, depth: 288, height: 320, "
        "thickness: 96, columns: 3, rows: 2, posts: 48, pediment: gable, pediment_height: 128}]}]";
    const Game::OutdoorBModel model = raisedPlot(plot);
    // Six columns: a shaft of eight sides, a base (four sides and a top), a capital (four sides and an underside).
    CHECK(texturedFaces(model, "OrAltMrb") == 6 * 8);
    CHECK(texturedFaces(model, "OCap") == 6 * 10);
    CHECK(findOutdoorCoplanarFaces({model}).empty());
    // The pediment: two slopes rising 128 over the band's top, a triangle over the front.
    LoweredOutdoorMap lowered = loweredBuildings("      - {building: building:home, at: [40, 40], facing: s, " + plot
        + "}\n");
    const double floor = lowered.buildings[0].base;
    CHECK(facesBetween(model, "OCeil", static_cast<int>(floor) + 320 + 96, static_cast<int>(floor) + 320 + 96 + 128)
        >= 1);
    CHECK(anyIssue(buildingIssues("parts: [{size: [512, 512], porches: [{wall: s, columns: 3}]}]"),
        "belong to a portico"));
    const Game::OutdoorBModel open = raisedPlot("door: none, textures: {post: OrAltMrb, capital: OCap}, parts: "
        "[{size: [512, 512], posts: 48, posts_shape: round}]");
    CHECK(texturedFaces(open, "OrAltMrb") == 4 * 8);
    CHECK(texturedFaces(open, "OCap") == 4 * 10);
    CHECK(findOutdoorCoplanarFaces({open}).empty());
    CHECK(anyIssue(buildingIssues("parts: [{size: [512, 512], posts_shape: round}]"), "belongs to an open part"));
}

TEST_CASE("O-F: the landmark words are in the sketch schema, every one described")
{
    const YAML::Node root = inlinedSketchSchema();
    const YAML::Node structures = root["properties"]["structures"]["items"]["properties"];
    bool kinds = true;

    for (const char *pKind : {"portal", "arch", "stone_ring", "trilithon", "walkway", "deck", "tent", "arcade"})
    {
        bool found = false;

        for (const YAML::Node &kind : structures["kind"]["enum"])
        {
            found = found || kind.Scalar() == pKind;
        }

        CAPTURE(pKind);
        CHECK(found);
        kinds = kinds && found;
    }

    for (const char *pWord : {"ring", "dais", "ribs", "hub", "curve", "segments", "angles", "count", "stone", "gap",
             "lintel", "altar", "kerb_width", "pier_every", "pier_radius", "pier_above", "ends", "frame_height",
             "level", "posts", "post_every", "awning", "open", "lean", "bays", "span", "pier", "spring", "on"})
    {
        CAPTURE(pWord);
        CHECK(structures[pWord]["description"].IsDefined());
    }

    const YAML::Node plots = root["properties"]["districts"]["items"]["properties"]["plots"]["items"]["properties"];
    CHECK(plots["on"]["description"].IsDefined());
    const YAML::Node part = plots["parts"]["items"]["properties"];
    CHECK(part["posts_shape"]["description"].IsDefined());

    for (const char *pWord : {"form", "posts_shape", "columns", "rows", "pediment", "pediment_height"})
    {
        CAPTURE(pWord);
        CHECK(part["porches"]["items"]["properties"][pWord]["description"].IsDefined());
    }
}

namespace
{
// Batch S4R: the area a model's faces of a texture cover seen from above, of those looking up (1), down (-1) or
// either (0) with a corner at least `low` high.
double planArea(const Game::OutdoorBModel &model, const std::string &texture, int facing, int low = -(1 << 30))
{
    double area = 0.0;

    for (const Game::OutdoorBModelFace *pFace : facesWith(model, texture))
    {
        const std::array<double, 3> normal = faceNormal(model, *pFace);

        if ((facing > 0 && normal[2] <= 0.1) || (facing < 0 && normal[2] >= -0.1) || heightsOf(model, *pFace)[0] < low)
        {
            continue;
        }

        double twice = 0.0;

        for (size_t index = 0; index < pFace->vertexIndices.size(); ++index)
        {
            const Game::OutdoorBModelVertex &a = model.vertices[pFace->vertexIndices[index]];
            const Game::OutdoorBModelVertex &b
                = model.vertices[pFace->vertexIndices[(index + 1) % pFace->vertexIndices.size()]];
            twice += static_cast<double>(a.x) * b.y - static_cast<double>(b.x) * a.y;
        }

        area += std::fabs(twice) * 0.5;
    }

    return area;
}

double coverArea(const std::vector<RoofCoverFace> &faces)
{
    double area = 0.0;

    for (const RoofCoverFace &face : faces)
    {
        area += polygonDoubleArea(face.points) * 0.5;
    }

    return area;
}
}

TEST_CASE("S4R: the roof cover of an outline that bends in: an L's two wings, a notched front's three pieces")
{
    // An L, counter-clockwise (x east, y north): a bar 768 by 256 and a wing 256 wide up to 768.
    const std::vector<Point2> l = {{0, 0}, {768, 0}, {768, 768}, {512, 768}, {512, 256}, {0, 256}};
    CHECK(outlineBendsIn(l));
    CHECK_FALSE(outlineBendsIn({{0, 0}, {512, 0}, {512, 512}, {0, 512}}));
    const std::vector<std::vector<Point2>> wings = roofCoverPieces(l);
    REQUIRE(wings.size() == 2);
    // Each wing whole: the corner square lies in both.
    CHECK(std::fabs(polygonDoubleArea(wings[0]) + polygonDoubleArea(wings[1]) - 2.0 * (768 * 256 * 2)) < 1.0);
    // A notched front: a block 1024 by 512 cut 256 deep and 256 wide in the middle of its south side.
    const std::vector<Point2> notched = {{0, 0}, {384, 0}, {384, 256}, {640, 256}, {640, 0}, {1024, 0}, {1024, 512},
        {0, 512}};
    CHECK(roofCoverPieces(notched).size() == 3);
    CHECK(convexPartsOf({{0, 0}, {512, 0}, {512, 512}, {0, 512}}).size() == 1);
    double parts = 0.0;

    for (const std::vector<Point2> &part : convexPartsOf(notched))
    {
        parts += polygonDoubleArea(part) * 0.5;
    }

    CHECK(parts == doctest::Approx(1024.0 * 512 - 256 * 256));
    // A hip over the L: the wings meet in a valley from the inner corner; the roof is the straight skeleton's.
    const RoofCover hip(l, false, std::nullopt);
    CHECK(hip.deepest() == doctest::Approx(128.0));
    CHECK(hip.runAt({640, 128}) == doctest::Approx(128.0));
    // Near the inner corner, on the bar's side of the valley: as high as its distance from the bar's inner wall
    // (the wave from the wing's inner wall has not reached it when the bar's does).
    CHECK(hip.runAt({520, 240}) == doctest::Approx(16.0));
    CHECK(hip.runAt({520, 262}) == doctest::Approx(8.0));
    CHECK(hip.runAt({400, 128}) == doctest::Approx(128.0));
    CHECK(hip.runAt({100, 128}) == doctest::Approx(100.0));
    // The slopes cover the L once.
    CHECK(coverArea(hip.faces({})) == doctest::Approx(768.0 * 256 * 2 - 256 * 256).epsilon(0.001));
    CHECK(hip.profiles(l).empty());
    // A gable over the L: each wing's ridge along its length; the wings' far ends and the corner's two outer walls
    // stand as gable ends.
    const RoofCover gable(l, true, std::nullopt);
    CHECK(coverArea(gable.faces({})) == doctest::Approx(768.0 * 256 * 2 - 256 * 256).epsilon(0.001));
    CHECK(gable.profiles(l).size() >= 2);
    // Harmondale's tavern: a wing 832 by 704 with its ridge north-south and a hall 448 deep running into it from the
    // east, its ridge east-west. Both ridges as high; the hall's roof ends at the wing's ridge.
    const std::vector<Point2> tavern = {{0, 0}, {832, 0}, {832, 256}, {2304, 256}, {2304, 704}, {0, 704}};
    const RoofCover cross(tavern, true, std::nullopt);
    REQUIRE(cross.pieces().size() == 2);
    CHECK(cross.runAt({416, 352}) == doctest::Approx(cross.deepest()));
    CHECK(cross.runAt({1500, 480}) == doctest::Approx(cross.deepest()));
    CHECK(cross.runAt({100, 480}) == doctest::Approx(cross.deepest() * 100 / 416));
    CHECK(coverArea(cross.faces({})) == doctest::Approx(832.0 * 704 + 1472 * 448).epsilon(0.001));
    // Gable ends: the wing's two and the hall's east end; none on the wing's west wall from the hall.
    size_t ends = 0;

    for (const RoofProfileFace &face : cross.profiles(tavern))
    {
        ends += 1;
        CHECK_FALSE(std::all_of(face.begin(), face.end(), [](const std::array<double, 3> &point)
        {
            return point[0] < 0.5;
        }));
    }

    CHECK(ends >= 3);
    // One slope for all (a pitch): the hall's ridge lower than the wing's.
    const RoofCover pitched(tavern, true, std::nullopt, 0.0, true);
    CHECK(pitched.runAt({1500, 480}) == doctest::Approx(224.0));
    CHECK(pitched.runAt({416, 352}) == doctest::Approx(416.0));
    // A ridge given for all: one direction.
    const RoofCover along(notched, true, Point2{1.0, 0.0});
    CHECK(coverArea(along.faces({})) == doctest::Approx(1024.0 * 512 - 256 * 256).epsilon(0.001));
    // The space between two outlines: an eaves ring.
    double ring = 0.0;

    for (const std::vector<Point2> &piece : areaBetween({{-64, -64}, {576, -64}, {576, 576}, {-64, 576}},
             {{0, 0}, {512, 0}, {512, 512}, {0, 512}}))
    {
        ring += polygonDoubleArea(piece) * 0.5;
    }

    CHECK(ring == doctest::Approx(640.0 * 640 - 512 * 512));
}

TEST_CASE("S4R: an L-shaped part under one hip or gable roof, a notched plinth with a flat top")
{
    // The L in the plot (y south): a bar along the north and a wing down the east.
    const std::string l = "door: none, eaves: 0, fascia: 0, parts: [{shape: outline, outline: [[0, 0], [768, 0], "
        "[768, 768], [512, 768], [512, 256], [0, 256]], wall_height: 256, roof: ";
    const Game::OutdoorBModel hip = raisedPlot(l + "hip, roof_height: 128}]");
    const double area = 768.0 * 256 * 2 - 256 * 256;
    // Six walls, one roof over the whole: its slopes cover the L once, up to 128 over the walls.
    CHECK(planArea(hip, "t14a05", 1) == doctest::Approx(area).epsilon(0.002));
    int highest = 0;

    for (const Game::OutdoorBModelFace *pFace : facesWith(hip, "t14a05"))
    {
        highest = std::max(highest, heightsOf(hip, *pFace)[1]);
        CHECK(faceNormal(hip, *pFace)[2] > 0.0);
    }

    CHECK(highest == 640 + 256 + 128);
    // No end walls over the walls' top under a hip.
    CHECK(facesBetween(hip, "t14a01", 897, 2000) == 0);
    CHECK(planBounds(hip, "t14a05") == planBounds(hip, "t14a01"));
    // A gable: the same cover, and upright gable ends over the walls.
    const Game::OutdoorBModel gable = raisedPlot(l + "gable, roof_height: 128}]");
    CHECK(planArea(gable, "t14a05", 1) == doctest::Approx(area).epsilon(0.002));
    CHECK(facesBetween(gable, "t14a01", 896, 1024) >= 2);
    // Eaves round the L, none over the wing's inner wall (wall 3): the soffit fills the rest.
    const Game::OutdoorBModel eaves = raisedPlot("door: none, eaves: 64, fascia: 0, parts: [{shape: outline, outline: "
        "[[0, 0], [768, 0], [768, 768], [512, 768], [512, 256], [0, 256]], wall_height: 256, roof: hip, roof_height: "
        "128, eaves_walls: [0, 1, 2, 4, 5]}]");
    const std::array<int, 4> walls = planBounds(eaves, "t14a01");
    const std::array<int, 4> roof = planBounds(eaves, "t14a05");
    CHECK(roof[0] == walls[0] - 64);
    CHECK(roof[2] == walls[2] + 64);
    CHECK(planArea(eaves, "t14a05b", -1) > 64.0 * 768 * 2);
    CHECK(planArea(eaves, "t14a05", 1) == doctest::Approx(area + planArea(eaves, "t14a05b", -1)).epsilon(0.002));
    // Blooded Daggers' plinth: a front notch 128 deep, its top in convex pieces.
    const Game::OutdoorBModel plinth = raisedPlot("door: none, eaves: 0, fascia: 0, parts: [{shape: outline, outline: "
        "[[0, 0], [1024, 0], [1024, 512], [640, 512], [640, 384], [384, 384], [384, 512], [0, 512]], wall_height: 32, "
        "roof: flat}]");
    CHECK(planArea(plinth, "t14a05", 1) == doctest::Approx(1024.0 * 512 - 256 * 128));
    CHECK(facesBetween(plinth, "t14a05", 672, 672) == facesWith(plinth, "t14a05").size());
    CHECK(facesWith(plinth, "t14a05").size() >= 3);
    // What an outline that bends in cannot carry yet.
    CHECK(anyIssue(buildingIssues(l + "cone}]"), "an outline that bends in takes"));
    CHECK(anyIssue(buildingIssues("door: none, parts: [{shape: outline, outline: [[0, 0], [768, 0], [768, 768], "
        "[512, 768], [512, 256], [0, 256]], roof: hip, posts: 32}]"), "not posts"));
}

TEST_CASE("S4R: eaves along part of a wall, from a join onward; a parapet on chosen walls and stretches")
{
    // A box 512 square under a hip with eaves 64 everywhere but the first 256 of its west wall (from its north end).
    const Game::OutdoorBModel house = raisedPlot("door: none, eaves: 64, fascia: 0, parts: [{size: [512, 512], "
        "roof: hip, roof_height: 128, ridge: 0, eaves_walls: [s, e, n, {wall: w, from: 256}]}]");
    const double region = 640.0 * 640 - 64.0 * (256 + 64);
    CHECK(planArea(house, "t14a05", 1) == doctest::Approx(region).epsilon(0.002));
    CHECK(planArea(house, "t14a05b", -1) == doctest::Approx(region - 512.0 * 512).epsilon(0.002));
    // Where the eaves stop the roof's edge stands over the wall: an upright face closes it.
    CHECK(facesBetween(house, "t14a01", 896, 1024) >= 1);
    // Whole walls as before: the same faces as `eaves_walls` of names only.
    const Game::OutdoorBModel whole = raisedPlot("door: none, eaves: 64, fascia: 0, parts: [{size: [512, 512], "
        "roof: hip, roof_height: 128, ridge: 0, eaves_walls: [s, {wall: e}]}]");
    const Game::OutdoorBModel named = raisedPlot("door: none, eaves: 64, fascia: 0, parts: [{size: [512, 512], "
        "roof: hip, roof_height: 128, ridge: 0, eaves_walls: [s, e]}]");
    CHECK(whole.faces.size() == named.faces.size());
    CHECK(planBounds(whole, "t14a05") == planBounds(named, "t14a05"));
    CHECK(anyIssue(buildingIssues("door: none, eaves: 64, parts: [{size: [512, 512], roof: hip, ridge: 0, "
        "eaves_walls: [{wall: w, from: 256, to: 900}]}]"), "must lie on the wall"));
    // A wall's own eaves: 192 over the north wall, 64 over the rest.
    const Game::OutdoorBModel deep = raisedPlot("door: none, eaves: 64, fascia: 0, parts: [{size: [512, 512], "
        "roof: hip, roof_height: 128, ridge: 0, eaves_walls: [s, e, {wall: n, eaves: 192}, w]}]");
    const std::array<int, 4> deepWalls = planBounds(deep, "t14a01");
    const std::array<int, 4> deepRoof = planBounds(deep, "t14a05");
    CHECK(deepRoof[3] == deepWalls[3] + 192);
    CHECK(deepRoof[1] == deepWalls[1] - 64);
    CHECK(anyIssue(buildingIssues("door: none, eaves: 64, parts: [{size: [512, 512], roof: hip, ridge: 0, "
        "eaves_walls: [{wall: n, eaves: 900}]}]"), "how far the roof reaches out over that wall"));
    CHECK(anyIssue(buildingIssues("door: none, eaves: 64, parts: [{size: [512, 512], roof: cone, eaves_walls: "
        "[{wall: w, from: 256}]}]"), "eaves along part of a wall go with"));

    // A parapet on the east wall and the first 128 of the north wall, mitred at their corner, ended square.
    const Game::OutdoorBModel walk = raisedPlot("door: none, eaves: 0, fascia: 0, parts: [{size: [512, 512], "
        "roof: flat, parapet: 64, parapet_walls: [e, {wall: n, to: 128}]}]");
    const std::array<int, 4> walls = planBounds(walk, "t14a01");
    // Two tops, both on the east side.
    size_t tops = 0;

    for (const Game::OutdoorBModelFace *pFace : facesWith(walk, "t14a01"))
    {
        if (heightsOf(walk, *pFace) == std::array<int, 2>{960, 960})
        {
            ++tops;
            CHECK(faceNormal(walk, *pFace)[2] > 0.0);
        }
    }

    CHECK(tops == 2);
    CHECK(planArea(walk, "t14a01", 1, 960) == doctest::Approx(512.0 * 32 + 96.0 * 32));
    CHECK(planBounds(walk, "t14a05")[0] == walls[0]);
    // Each stretch's free end closed: the east one at its south end, the north one at its west end.
    CHECK(facesBetween(walk, "t14a01", 896, 960) == 2 + 2 + 2 + 2);
    CHECK(anyIssue(buildingIssues("door: none, parts: [{size: [512, 512], roof: flat, parapet_walls: [e]}]"),
        "names the walls a parapet stands on"));
    // An L with a parapet round all its walls.
    const Game::OutdoorBModel roofWalk = raisedPlot("door: none, eaves: 0, fascia: 0, parts: [{shape: outline, "
        "outline: [[0, 0], [768, 0], [768, 768], [512, 768], [512, 256], [0, 256]], roof: flat, parapet: 64}]");
    // The parapet's strip round the outline (3072 long, 32 wide), less a square at each of the five corners that
    // bend out and more one at the corner that bends in.
    CHECK(planArea(roofWalk, "t14a01", 1, 960) == doctest::Approx(3072.0 * 32 - 4 * 32 * 32).epsilon(0.001));
}

TEST_CASE("S4R: the words of batch S4R are in the sketch schema, described")
{
    const YAML::Node root = inlinedSketchSchema();
    const YAML::Node plots = root["properties"]["districts"]["items"]["properties"]["plots"]["items"]["properties"];
    const YAML::Node part = plots["parts"]["items"]["properties"];

    for (const char *pWord : {"parapet_walls", "eaves_walls"})
    {
        CAPTURE(pWord);
        CHECK(part[pWord]["description"].IsDefined());
        CHECK(part[pWord]["items"]["oneOf"][1]["properties"]["from"]["description"].IsDefined());
    }

    CHECK(part["shape"]["description"].Scalar().find("bending in") != std::string::npos);
}

// ---- Outdoor code batch O-H (2026-11-14): from the fresh rebuilds of Castle Ironfist and Erathia ----

TEST_CASE("O-H: heights.nodes sets each given node, last of the land's words; `~` keeps the land")
{
    const LoweredOutdoorMap lowered = loweredOf(std::string(LevelLand) + "  ridges:\n"
        "    - {line: [[40, 40], [44, 40]], height: 1600}\n"
        "  nodes:\n"
        "    - {at: [40, 40], rows: [[150, ~, 0], [26, 26]]}\n"
        "    - {at: [70, 70], unit: 64, rows: [[75]]}\n");

    // Over the ridge laid before it.
    CHECK(groundAt(lowered, 40, 40) == doctest::Approx(4800.0));
    CHECK(groundAt(lowered, 41, 40) == doctest::Approx(1600.0));
    CHECK(groundAt(lowered, 42, 40) == doctest::Approx(0.0));
    CHECK(groundAt(lowered, 40, 41) == doctest::Approx(832.0));
    CHECK(groundAt(lowered, 41, 41) == doctest::Approx(832.0));
    CHECK(groundAt(lowered, 42, 41) == doctest::Approx(640.0));
    CHECK(groundAt(lowered, 70, 70) == doctest::Approx(4800.0));
    CHECK(groundAt(lowered, 71, 70) == doctest::Approx(640.0));
    // A sheer fall between two neighbouring nodes.
    CHECK((sampleAt(lowered, 40, 40) - sampleAt(lowered, 40, 41)) * 32 == 4800 - 832);
    const auto refused = [](const std::string &entry, const std::string &fragment)
    {
        CAPTURE(entry);
        CHECK(anyIssue(refusedWith(std::string(LevelLand) + "  nodes:\n    - " + entry + "\n"), fragment));
    };
    refused("{at: [40.5, 40], rows: [[1]]}", "whole nodes");
    refused("{at: [126, 40], rows: [[1, 2, 3]]}", "ends inside the map");
    refused("{at: [40, 127], rows: [[1], [2]]}", "ends inside the map");
    refused("{at: [40, 40], rows: [[300]]}", "0 to 8160");
    refused("{at: [40, 40], rows: []}", "`rows` are lists");
    refused("{at: [40, 40], unit: 0, rows: [[1]]}", "`unit`");
    const YAML::Node heights =
        inlinedSketchSchema()["properties"]["heights"]["properties"];

    for (const char *pWord : {"at", "unit", "rows"})
    {
        CHECK(heights["nodes"]["items"]["properties"][pWord]["description"].IsDefined());
    }
}

TEST_CASE("O-H: a stair inside an upright part runs `run` in from its wall's foot up to the flat roof")
{
    // Castle Ironfist's castle: the King's Library and the towers' doors on the block's top at 576.
    const Game::OutdoorBModel castle = raisedPlot("door: none, eaves: 0, fascia: 0, textures: {stair: t06a01, "
        "cheek: t14c01, wall: t14a03, roof: t14a05}, parts: [{size: [1024, 768], wall_height: 576, roof: flat, "
        "stair: {wall: s, along: 256, width: 256, run: 576, ramp: true, cheek: [32, 64]}}]");
    const std::vector<const Game::OutdoorBModelFace *> ramp = facesWith(castle, "t06a01");
    REQUIRE(ramp.size() == 1);
    const std::array<int, 2> rampHeights = heightsOf(castle, *ramp[0]);
    CHECK(rampHeights[1] - rampHeights[0] == 576);
    const std::array<int, 4> slot = planBounds(castle, "t06a01");
    CHECK(slot[2] - slot[0] == 256);
    CHECK(slot[3] - slot[1] == 576);
    // No roof and no wall left over the flight and its cheeks.
    for (const char *pTexture : {"t14a05", "t14a03"})
    {
        for (const Game::OutdoorBModelFace *pFace : facesWith(castle, pTexture))
        {
            double x = 0.0;
            double y = 0.0;

            for (const uint16_t index : pFace->vertexIndices)
            {
                x += castle.vertices[index].x / static_cast<double>(pFace->vertexIndices.size());
                y += castle.vertices[index].y / static_cast<double>(pFace->vertexIndices.size());
            }

            CAPTURE(pTexture);
            CHECK_FALSE((x > slot[0] - 31 && x < slot[2] + 31 && y > slot[1] + 1 && y < slot[3] - 1));
        }
    }

    // The cut's sides inside the block, the cheeks' tops and faces.
    CHECK(facesWith(castle, "t14c01").size() >= 6);
    CHECK(anyIssue(buildingIssues("door: none, parts: [{size: [512, 512], roof: flat, stair: {wall: s}}]"),
        "give it `run`"));
    CHECK(anyIssue(buildingIssues("door: none, parts: [{size: [512, 512], roof: hip, stair: {wall: s, run: 256}}]"),
        "with a flat roof"));
    CHECK(anyIssue(buildingIssues("door: none, parts: [{size: [512, 512], roof: flat, stair: {wall: s, run: 600}}]"),
        "reaches through the part"));
}

TEST_CASE("O-H: a wall up to 4096 thick, a gate 32 from a free end, a passage along it, a gate under the passage")
{
    std::vector<ProjectIssue> issues;
    IdsLock ids;
    // Castle Ironfist's gate block: 1024 along, 1152 thick, a round arch 768 wide (cheeks of 128).
    // Erathia's fort: a block 1920 thick, the road through it along its line over the river's gate.
    const OutdoorThings things = thingsOf("structures:\n"
        "  - {id: thing:gate, kind: wall, line: [[44, 50], [46, 50]], height: 704, thickness: 1152, "
        "gates: [{at: [45, 50], width: 768, height: 576, arch: round}]}\n"
        "  - {id: thing:fort, kind: wall, line: [[44, 56], [48, 56]], height: 768, thickness: 1920, "
        "passage_along: {floor: 896, width: 512, height: 320}, gates: [{at: [46, 56], width: 512, height: 192}]}\n",
        issues, ids);

    for (const ProjectIssue &issue : issues)
    {
        MESSAGE(issue.path << ": " << issue.message);
    }

    REQUIRE(issues.empty());
    const Game::OutdoorBModel *pGate = modelNamed(things, "thing:gate");
    const Game::OutdoorBModel *pFort = modelNamed(things, "thing:fort");
    REQUIRE((pGate && pFort));
    CHECK(pGate->maxY - pGate->minY == 1152);
    // The passage: its floor (the piece under it, looking up, across the whole thickness) and its ceiling (looking
    // down) along the wall's whole length; its two sides 704 thick each.
    size_t floors = 0;
    size_t ceilings = 0;

    for (const Game::OutdoorBModelFace &face : pFort->faces)
    {
        const std::array<int, 2> heights = heightsOf(*pFort, face);
        const std::array<double, 3> normal = faceNormal(*pFort, face);
        floors += heights[0] == 896 && heights[1] == 896 && normal[2] > 0.9 ? 1 : 0;
        ceilings += heights[0] == 1216 && heights[1] == 1216 && normal[2] < -0.9 ? 1 : 0;
    }

    CHECK(floors >= 2);
    CHECK(ceilings >= 2);
    CHECK(pFort->maxZ == 640 + 768);
    const auto refused = [](const std::string &structure, const std::string &fragment)
    {
        std::vector<ProjectIssue> found;
        IdsLock lock;
        thingsOf("structures:\n" + structure, found, lock);
        CAPTURE(structure);
        CHECK(anyIssue(found, fragment));
    };
    refused("  - {id: thing:a, kind: wall, line: [[44, 56], [48, 56]], thickness: 5000}\n", "32 to 4096 thick");
    refused("  - {id: thing:a, kind: wall, line: [[44, 56], [48, 56]], height: 384, gates: [{at: [46, 56], "
        "height: 400}]}\n", "stands over the wall's top");
    refused("  - {id: thing:a, kind: wall, line: [[44, 56], [48, 56]], height: 768, thickness: 1024, passage_along: "
        "{floor: 896}, gates: [{at: [46, 56], height: 300}]}\n", "stands over the passage along the wall");
    refused("  - {id: thing:a, kind: wall, line: [[44, 56], [48, 56], [48, 60]], height: 768, thickness: 1024, "
        "passage_along: {floor: 896}}\n", "a passage along a wall runs through a straight wall");
    refused("  - {id: thing:a, kind: wall, line: [[44, 56], [48, 56]], height: 768, thickness: 1024, passage_along: "
        "{floor: 896, width: 1000}}\n", "a passage along a wall");
}

TEST_CASE("O-H: a roof round an open court: walls round the court, a hip's ridge ring midway, nothing over the court")
{
    // Erathia's Castle Gryphonheart keep: one roof whose ridge ring falls to the outer walls and into the court.
    const Game::OutdoorBModel keep = raisedPlot("door: none, eaves: 0, fascia: 0, textures: {wall: t14a03, roof: "
        "t14a05}, parts: [{size: [1024, 768], wall_height: 256, roof: hip, roof_height: 192, court: {at: [256, 256], "
        "size: [512, 256]}}]");
    const std::vector<const Game::OutdoorBModelFace *> roof = facesWith(keep, "t14a05");
    CHECK(roof.size() == 8);
    const std::array<int, 2> roofHeights = {keep.minZ, keep.maxZ};
    CHECK(roofHeights[1] - 192 == 640 + 256);
    const std::array<int, 4> bounds = planBounds(keep, "t14a03");
    size_t courtWalls = 0;

    for (const Game::OutdoorBModelFace *pFace : facesWith(keep, "t14a03"))
    {
        double x = 0.0;
        double y = 0.0;

        for (const uint16_t index : pFace->vertexIndices)
        {
            x += keep.vertices[index].x / static_cast<double>(pFace->vertexIndices.size());
            y += keep.vertices[index].y / static_cast<double>(pFace->vertexIndices.size());
        }

        courtWalls += x > bounds[0] + 128 && x < bounds[2] - 128 && y > bounds[1] + 128 && y < bounds[3] - 128 ? 1 : 0;
    }

    CHECK(courtWalls == 4);

    // No roof over the court's middle.
    for (const Game::OutdoorBModelFace *pFace : roof)
    {
        double x = 0.0;
        double y = 0.0;

        for (const uint16_t index : pFace->vertexIndices)
        {
            x += keep.vertices[index].x / static_cast<double>(pFace->vertexIndices.size());
            y += keep.vertices[index].y / static_cast<double>(pFace->vertexIndices.size());
        }

        const double middleX = (bounds[0] + bounds[2]) * 0.5;
        const double middleY = (bounds[1] + bounds[3]) * 0.5;
        CHECK_FALSE((std::fabs(x - middleX) < 200.0 && std::fabs(y - middleY) < 72.0));
    }

    CHECK(anyIssue(buildingIssues("door: none, parts: [{size: [512, 512], roof: gable, court: {at: [128, 128], size: "
        "[256, 256]}}]"), "a court goes through a box part"));
    CHECK(anyIssue(buildingIssues("door: none, parts: [{size: [512, 512], roof: hip, court: {at: [32, 128], size: "
        "[256, 256]}}]"), "within 64 of the part's walls"));
}

TEST_CASE("O-H: one shared hint event on many things; a building's hint on its walls; a hint on a tent")
{
    // Erathia: "House" (event 51) on 22 homes' walls, "Well" (201) on five wells, "Tent" (91) on the healers'.
    const BuiltOutdoor built = builtOutdoor(buildingProject(
        "      - {building: building:home, at: [40, 40], facing: s}\n",
        "structures:\n"
        "  - {id: thing:h1, kind: building, at: [40, 50], size: [1, 1], title: Heartsworn Home, house: 936, "
        "hint: House, hint_shared: true}\n"
        "  - {id: thing:h2, kind: building, at: [44, 50], size: [1, 1], title: Other Home, house: 937, hint: House, "
        "hint_shared: true}\n"
        "  - {id: thing:h3, kind: building, at: [48, 50], size: [1, 1], title: Own Home, house: 938, hint: Cottage}\n"
        "  - {id: thing:well_1, kind: well, at: [50, 50], title: Drink, effects: [{text: Refreshing}], hint: Well, "
        "hint_shared: true}\n"
        "  - {id: thing:well_2, kind: well, at: [54, 50], title: Drink, effects: [{text: Refreshing}], hint: Well, "
        "hint_shared: true}\n"
        "  - {id: thing:well_3, kind: well, at: [58, 50], title: Drink, effects: [{text: Refreshing}], hint: Well}\n"
        "  - {id: thing:tent, kind: tent, at: [60, 56], wall_height: 192, open: false, house: 926, title: Healer, "
        "hint: Tent}\n"), "oymap_outdoor_shared_hint");
    REQUIRE(built.built);
    const auto registrations = [&](const std::string &title)
    {
        size_t count = 0;
        std::istringstream lines(built.lua);
        std::string line;

        while (std::getline(lines, line))
        {
            count += line.rfind("RegisterEvent(", 0) == 0 && line.find(", \"" + title + "\"") != std::string::npos
                ? 1 : 0;
        }

        return count;
    };
    // One "House" for both shared homes, the third home's walls its own hint; two "Well" events (the shared one and
    // the third well's own); the doors keep their titles.
    CHECK(registrations("House") == 1);
    CHECK(registrations("Cottage") == 1);
    CHECK(registrations("Well") == 2);
    CHECK(registrations("Heartsworn Home") == 1);
    const int house = eventNumberOf(built.lua, "House");
    const int well = eventNumberOf(built.lua, "Well");
    REQUIRE((house != 0 && well != 0));
    CHECK(facesOfEvent(built.scene, house) > 8);
    CHECK(facesOfEvent(built.scene, well) > 4);
    // The tent: its canvas says Tent, its front end enters the healer's.
    const int tent = eventNumberOf(built.lua, "Tent");
    const int healer = eventNumberOf(built.lua, "Healer");
    REQUIRE((tent != 0 && healer != 0));
    CHECK(facesOfEvent(built.scene, tent) > facesOfEvent(built.scene, healer));
    CHECK(facesOfEvent(built.scene, healer) >= 2);
    std::vector<ProjectIssue> refused;
    IdsLock lock;
    thingsOf("structures:\n  - {id: thing:w, kind: well, at: [50, 50], hint_shared: true}\n", refused, lock);
    CHECK(anyIssue(refused, "`hint_shared` shares the thing's `hint`"));
}

TEST_CASE("O-H: an arched recess (a soffit under each segment, the wall over the arch); a door's own recess")
{
    // Castle Ironfist's gate passage: a recess 1024 deep under a round head.
    const Game::OutdoorBModel gate = raisedPlot("door: none, eaves: 0, fascia: 0, textures: {soffit: t06a01, "
        "wall: t14a03}, parts: [{size: [1024, 1152], wall_height: 768, roof: flat, walls: {s: [wall, wall, wall, "
        "wall, wall, wall, wall]}, porches: [{wall: s, bays: [1, 5], depth: 1024, recess: true, arch: round, "
        "sides: 6}]}]");
    const std::vector<const Game::OutdoorBModelFace *> soffits = facesWith(gate, "t06a01");
    CHECK(soffits.size() == 6);
    size_t looksDown = 0;

    for (const Game::OutdoorBModelFace *pFace : soffits)
    {
        looksDown += faceNormal(gate, *pFace)[2] < -0.1 ? 1 : 0;
    }

    CHECK(looksDown >= 4);
    CHECK(anyIssue(buildingIssues("door: none, parts: [{size: [512, 512], porches: [{wall: s, arch: round}]}]"),
        "a recess's `arch`"));
    // A door 256 back: the two cheeks of its recess and its ceiling.
    const Game::OutdoorBModel hall = raisedPlot("eaves: 0, fascia: 0, door: {wall: s, bay: 2, recess: 256}, "
        "parts: [{size: [768, 768], wall_height: 384, roof: flat, walls: {s: [wall, wall, door, wall, wall, wall]}}]");
    const Game::OutdoorBModel flat = raisedPlot("eaves: 0, fascia: 0, door: {wall: s, bay: 2}, "
        "parts: [{size: [768, 768], wall_height: 384, roof: flat, walls: {s: [wall, wall, door, wall, wall, wall]}}]");
    CHECK(hall.faces.size() >= flat.faces.size() + 3);
    CHECK(anyIssue(buildingIssues("door: {wall: s, recess: 900}, parts: [{size: [512, 512]}]"),
        "a door's `recess`"));
}

TEST_CASE("O-H: holes in a platform's top: a basin's pit sunk into it, a plate's opening flush with it")
{
    std::vector<ProjectIssue> issues;
    IdsLock ids;
    const OutdoorThings things = thingsOf("structures:\n"
        "  - {id: thing:court, kind: platform, at: [50, 50], size: [1024, 1024], height: 64, textures: {top: t14a05, "
        "wall: t14a03}, holes: [{at: [50, 50], size: [256, 256], depth: 64}]}\n"
        "  - {id: thing:pad, kind: platform, at: [60, 60], size: [640, 640], height: 32, textures: {top: t14a05, wall: t14a03}, "
        "holes: [{at: [60, 60], size: [182, 182], turn: 45, depth: 0}]}\n"
        "  - {id: thing:plate, kind: platform, at: [60, 60], size: [182, 182], turn: 45, height: 32, textures: {top: t06a01}, "
        "trigger: step, effects: [{text: plate}]}\n", issues, ids);
    REQUIRE(issues.empty());
    const Game::OutdoorBModel *pCourt = modelNamed(things, "thing:court");
    const Game::OutdoorBModel *pPad = modelNamed(things, "thing:pad");
    REQUIRE((pCourt && pPad));
    // The basin's floor 64 under the court's top, its four sides looking in.
    CHECK(facesBetween(*pCourt, "t14a05", 640, 640) == 1);
    CHECK(facesBetween(*pCourt, "t14a05", 704, 704) >= 4);
    // No face of the pad's top over the plate's middle.
    for (const Game::OutdoorBModelFace *pFace : facesWith(*pPad, "t14a05"))
    {
        double x = 0.0;
        double y = 0.0;

        for (const uint16_t index : pFace->vertexIndices)
        {
            x += pPad->vertices[index].x / static_cast<double>(pFace->vertexIndices.size());
            y += pPad->vertices[index].y / static_cast<double>(pFace->vertexIndices.size());
        }

        CHECK(std::hypot(x - (pPad->minX + pPad->maxX) * 0.5, y - (pPad->minY + pPad->maxY) * 0.5) > 60.0);
    }

    CHECK(facesBetween(*pPad, "t14a05", 672, 672) >= 4);
    std::vector<ProjectIssue> refused;
    IdsLock lock;
    thingsOf("structures:\n  - {id: thing:p, kind: platform, at: [50, 50], size: [256, 256], holes: [{at: [50, 50], "
        "size: [256, 256]}]}\n", refused, lock);
    CHECK(anyIssue(refused, "within 8 of the platform's edge"));
}

TEST_CASE("O-H: install's way back is the neighbour's side that leads to the original, not the arrival side")
{
    // Erathia (7out03): its east edge says it arrives on Harmondale's east side, but Harmondale's way to Erathia is its
    // left (west) side; the way back arrives on this map's east side, the table's "left" (S8g).
    Project project = buildingProject("      - {building: building:home, at: [40, 40], facing: s}\n");
    ProjectFile &card = project.files["project.yml"];
    card.document = YAML::Load("format: 0\nid: groundtest\nworld: mm7\nkind: outdoor\nname: Test Vale\n"
        "map_stats: {id: 9901, reference: 7out03.odm}\nneighbours:\n"
        "  - {id: edge:east, to: 7out02.odm, kind: edge, side: east, days: 2, arrival_side: east}\n");
    const std::filesystem::path table = std::filesystem::temp_directory_path() / "oymap_travel_back_test.txt";
    {
        std::ofstream stream(table);
        stream << "Key map\tUp\tSide\tDays\tDown\tSide\tDays\tLeft\tSide\tDays\tRight\tSide\tDays\t"
                  "StraightTravel\tNotes\n"
               << "7out02.odm\t\t\t\t\t\t\t7out03.odm\tright\t2\t7out04.odm\tdown\t7\t\tHarmondale\n";
    }
    std::vector<std::string> changes;
    std::string errorMessage;
    REQUIRE(upsertOutdoorTravelRows(project, table, changes, errorMessage));
    std::ifstream stream(table);
    std::string text((std::istreambuf_iterator<char>(stream)), std::istreambuf_iterator<char>());
    CHECK(text.find("7out02.odm\t\t\t\t\t\t\tgroundtest.odm\tleft\t2\t7out04.odm\tdown\t7\t\tHarmondale")
        != std::string::npos);
    std::error_code error;
    std::filesystem::remove(table, error);
}

TEST_CASE("S8g: an east or west arrival is written in MMerge's words, \"left\" for the east start, \"right\" for the west")
{
    // The game (game/tables/MapStats.cpp parseMergedOutdoorTravelSide) enters by the east start on "left" and by the
    // west start on "right": Erathia's shipped row leads left to Tatalia "left" and right to Harmondale "right".
    Project project = buildingProject("      - {building: building:home, at: [40, 40], facing: s}\n");
    ProjectFile &card = project.files["project.yml"];
    card.document = YAML::Load("format: 0\nid: groundtest\nworld: mm7\nkind: outdoor\nname: Test Vale\n"
        "map_stats: {id: 9901, reference: 7out03.odm}\nneighbours:\n"
        "  - {id: edge:west, to: 7out13.odm, kind: edge, side: west, days: 5}\n"
        "  - {id: edge:east, to: 7out02.odm, kind: edge, side: east, days: 4, arrival_side: west}\n"
        "  - {id: edge:north, to: 7out05.odm, kind: edge, side: north, days: 3, one_way: true}\n");
    const std::vector<OutdoorTravelEdge> edges = outdoorTravelEdges(project);
    REQUIRE(edges.size() == 3);
    CHECK(edges[0].arrivalSide == "east");
    const std::filesystem::path table = std::filesystem::temp_directory_path() / "oymap_travel_words_test.txt";
    {
        std::ofstream stream(table);
        stream << "Key map\tUp\tSide\tDays\tDown\tSide\tDays\tLeft\tSide\tDays\tRight\tSide\tDays\t"
                  "StraightTravel\tNotes\n"
               << "7out02.odm\t\t\t\t\t\t\t7out03.odm\tleft\t5\t7out04.odm\tdown\t7\t\tHarmondale\n"
               << "7out13.odm\t\t\t\t\t\t\t\t\t\t7out03.odm\tright\t5\t\tTatalia\n";
    }
    std::vector<std::string> changes;
    std::string errorMessage;
    REQUIRE(upsertOutdoorTravelRows(project, table, changes, errorMessage));
    std::ifstream stream(table);
    const std::string text((std::istreambuf_iterator<char>(stream)), std::istreambuf_iterator<char>());
    // Its own row: north "down" (the south start), west to Tatalia's east start ("left"), east to Harmondale's west
    // start ("right").
    CHECK(text.find("groundtest.odm\t7out05.odm\tdown\t3\t\t\t\t7out13.odm\tleft\t5\t7out02.odm\tright\t4\t\t"
        "Test Vale") != std::string::npos);
    // The ways back arrive on this map's sides: from Harmondale's left onto its east side ("left"), from Tatalia's
    // right onto its west side ("right"), as the shipped rows to Erathia do.
    CHECK(text.find("7out02.odm\t\t\t\t\t\t\tgroundtest.odm\tleft\t4\t7out04.odm\tdown\t7\t\tHarmondale")
        != std::string::npos);
    CHECK(text.find("7out13.odm\t\t\t\t\t\t\t\t\t\tgroundtest.odm\tright\t5\t\tTatalia") != std::string::npos);
    std::error_code error;
    std::filesystem::remove(table, error);
}

// ---- Workstream S8d (2026-11-15): outdoor code list items 19 to 21 (Castle Ironfist's and Erathia's words) ----

#include "core/Audit.h"

namespace
{
// The faces of a model whose corners all lie in a box [x0, y0, x1, y1] seen from above.
size_t facesInside(const Game::OutdoorBModel &model, const std::array<double, 4> &box)
{
    size_t count = 0;

    for (const Game::OutdoorBModelFace &face : model.faces)
    {
        bool inside = !face.vertexIndices.empty();

        for (const uint16_t index : face.vertexIndices)
        {
            const Game::OutdoorBModelVertex &vertex = model.vertices[index];
            inside = inside && vertex.x >= box[0] && vertex.x <= box[2] && vertex.y >= box[1] && vertex.y <= box[3];
        }

        count += inside ? 1 : 0;
    }

    return count;
}

// The lowest and highest corner of the faces of a texture.
std::array<int, 2> heightsWith(const Game::OutdoorBModel &model, const std::string &texture)
{
    std::array<int, 2> range = {1 << 30, -(1 << 30)};

    for (const Game::OutdoorBModelFace *pFace : facesWith(model, texture))
    {
        const std::array<int, 2> heights = heightsOf(model, *pFace);
        range = {std::min(range[0], heights[0]), std::max(range[1], heights[1])};
    }

    return range;
}
}

TEST_CASE("S8d: a vault over a box: tiers from each eaves side with a flat crown, or a half ellipse; its ends closed")
{
    // Castle Ironfist's temples (TempleW): Pxshings falling 256 in five slopes to each end, a crown 864 long.
    const Game::OutdoorBModel temple = raisedPlot("door: none, parts: [{size: [1664, 768], wall_height: 256, "
        "roof: vault, ridge_along: ns, tiers: [[24, 32], [56, 48], [96, 64], [176, 96], [48, 16]], eaves: 0, "
        "fascia: 0, textures: {roof: t14a05, gable: t06a01}}]");
    const std::vector<const Game::OutdoorBModelFace *> slopes = facesWith(temple, "t14a05");
    REQUIRE(slopes.size() == 11);
    std::set<int> leans;
    size_t level = 0;

    for (const Game::OutdoorBModelFace *pFace : slopes)
    {
        const std::array<double, 3> normal = faceNormal(temple, *pFace);
        CHECK(normal[2] > 0.5);
        level += normal[2] > 0.999 ? 1 : 0;
        leans.insert(static_cast<int>(std::lround(std::fabs(normal[0]) * 100.0)));
    }

    // The original's slopes: normals 0.80, 0.65, 0.55, 0.48 and 0.32 across; one level crown.
    CHECK(level == 1);
    CHECK(leans == std::set<int>{0, 32, 48, 55, 65, 80});
    CHECK(heightsWith(temple, "t14a05")[1] - heightsWith(temple, "t14a05")[0] == 256);
    // The two end walls closed up to the section, each one face of the gable texture over the walls' top.
    CHECK(facesWith(temple, "t06a01").size() == 2);
    // Without tiers: a half ellipse, half the span high, four segments to each side.
    const Game::OutdoorBModel barrel = raisedPlot("door: none, parts: [{size: [1024, 512], wall_height: 256, "
        "roof: vault, eaves: 0, fascia: 0, textures: {roof: t14a05}}]");
    CHECK(facesWith(barrel, "t14a05").size() == 8);
    CHECK(heightsWith(barrel, "t14a05")[1] - heightsWith(barrel, "t14a05")[0] == 256);
    CHECK(findOutdoorCoplanarFaces({temple}).empty());
    CHECK(findOutdoorCoplanarFaces({barrel}).empty());
    CHECK(anyIssue(buildingIssues("door: none, parts: [{shape: round, radius: 256, roof: vault}]"),
        "so does a vault"));
    CHECK(anyIssue(buildingIssues("door: none, parts: [{size: [1024, 512], roof: vault, tiers: [[64, 32], "
        "[64, 64]]}]"), "no steeper than the one below"));
    CHECK(anyIssue(buildingIssues("door: none, parts: [{size: [1024, 512], roof: gable, vault_segments: 6}]"),
        "belongs to `roof: vault`"));
}

TEST_CASE("S8d: a recess open at its corners: the walls across stand back by its depth, the roof over all")
{
    // Castle Ironfist's HouseR2S: the wing's whole south front an open porch 256 deep under its gable.
    const std::string wing = "door: {wall: s, bay: 1}, eaves: 0, fascia: 0, parts: [{size: [512, 768], "
        "wall_height: 256, roof: gable, ridge_along: ns, roof_height: 384, porches: [{wall: s, depth: 256, "
        "recess: true, open_corner: true, posts: 32}]}]";
    const Game::OutdoorBModel house = raisedPlot(wing);
    int west = 1 << 30;
    int south = 1 << 30;
    int east = -(1 << 30);

    for (const Game::OutdoorBModelVertex &vertex : house.vertices)
    {
        west = std::min(west, vertex.x);
        east = std::max(east, vertex.x);
        south = std::min(south, vertex.y);
    }

    // Nothing upright stands on the side walls' first 256 from the front corner but the two posts (32 square).
    size_t sideWall = 0;

    for (const Game::OutdoorBModelFace &face : house.faces)
    {
        const std::array<double, 3> normal = faceNormal(house, face);
        bool front = true;
        bool onSide = true;

        for (const uint16_t index : face.vertexIndices)
        {
            const Game::OutdoorBModelVertex &vertex = house.vertices[index];
            front = front && vertex.y < south + 255 && vertex.z < 400;
            onSide = onSide && (vertex.x == west || vertex.x == east);
        }

        sideWall += front && onSide && std::fabs(normal[2]) < 0.1 && std::fabs(normal[0]) > 0.9 ? 1 : 0;
    }

    CHECK(sideWall == 0);
    CHECK(findOutdoorCoplanarFaces({house}).empty());
    // Without the word a recess to the wall's end is refused as before; a door in the open stretch is refused.
    CHECK(anyIssue(buildingIssues("door: none, parts: [{size: [768, 512], porches: [{wall: s, bays: [3, 5], "
        "depth: 64, recess: true}]}]"), "open at a corner"));
    CHECK(anyIssue(buildingIssues("door: {wall: e, bay: 0}, parts: [{size: [768, 512], porches: [{wall: s, "
        "bays: [3, 5], depth: 256, recess: true, open_corner: true}]}]"), "leaves open"));
    CHECK(anyIssue(buildingIssues("door: none, parts: [{size: [768, 512], porches: [{wall: s, bays: [2, 3], "
        "depth: 64, recess: true, open_corner: true}]}]"), "`open_corner: true` opens a recess"));
}

TEST_CASE("S8d: a door on a sill stands a whole door high from it, the wall under it, the row above over it")
{
    // Castle Ironfist's King's Library door: 128 over the forecourt, in walls 384 high.
    const Game::OutdoorBModel keep = raisedPlot("eaves: 0, fascia: 0, textures: {door: t14a03}, door: {wall: s, "
        "bay: 2, sill: 128}, parts: [{size: [768, 512], wall_height: 384, roof: flat, walls: {s: [wall, wall, door, "
        "wall, wall, wall]}}]");
    const Game::OutdoorBModel plain = raisedPlot("eaves: 0, fascia: 0, textures: {door: t14a03}, door: {wall: s, "
        "bay: 2}, parts: [{size: [768, 512], wall_height: 384, roof: flat, walls: {s: [wall, wall, door, wall, "
        "wall, wall]}}]");
    const std::array<int, 2> door = heightsWith(keep, "t14a03");
    const std::array<int, 2> floorDoor = heightsWith(plain, "t14a03");
    CHECK(door[0] == floorDoor[0] + 128);
    CHECK(door[1] == floorDoor[0] + 384);
    CHECK(findOutdoorCoplanarFaces({keep}).empty());
    CHECK(anyIssue(buildingIssues("door: {wall: s, sill: 200}, parts: [{size: [512, 512]}]"), "a door's `sill`"));
    CHECK(anyIssue(buildingIssues("door: {wall: s, sill: 64, hood: 64}, parts: [{size: [512, 512]}]"),
        "a door's `sill`"));
}

TEST_CASE("S8d: a bridge's kerbs of their own width; arches of their own spans")
{
    std::vector<ProjectIssue> issues;
    IdsLock ids;
    // Erathia's viaduct Bridge_E: kerbs 64 wide, openings 384, 576 and 384 on piers 128.
    const OutdoorThings things = thingsOf("structures:\n"
        "  - {id: thing:viaduct, kind: bridge, line: [[50, 60], [50, 54.625]], height: 1328, width: 512, "
        "thickness: 48, kerb: 80, kerb_width: 64, textures: {deck: t14a05, side: t06a01}, arches: {count: 3, "
        "spans: [384, 576, 384], pier_width: 128, rise: 192}}\n"
        "  - {id: thing:plain, kind: bridge, line: [[60, 60], [60, 54.625]], height: 1328, width: 512, "
        "thickness: 48, kerb: 80, textures: {deck: t14a05, side: t06a01}, arches: {count: 3, pier_width: 128}}\n",
        issues, ids);
    REQUIRE(issues.empty());
    const Game::OutdoorBModel *pViaduct = modelNamed(things, "thing:viaduct");
    const Game::OutdoorBModel *pPlain = modelNamed(things, "thing:plain");
    REQUIRE((pViaduct && pPlain));
    // The kerbs' tops: 64 across on the viaduct, 32 on the plain bridge.
    const auto kerbWidth = [](const Game::OutdoorBModel &model)
    {
        int narrowest = 1 << 30;

        for (const Game::OutdoorBModelFace &face : model.faces)
        {
            const std::array<int, 2> heights = heightsOf(model, face);

            if (heights[0] == heights[1] && heights[0] > 1328 && faceNormal(model, face)[2] > 0.99)
            {
                int x0 = 1 << 30;
                int x1 = -(1 << 30);

                for (const uint16_t index : face.vertexIndices)
                {
                    x0 = std::min(x0, model.vertices[index].x);
                    x1 = std::max(x1, model.vertices[index].x);
                }

                narrowest = std::min(narrowest, x1 - x0);
            }
        }

        return narrowest;
    };
    CHECK(kerbWidth(*pViaduct) == 64);
    CHECK(kerbWidth(*pPlain) == 32);
    // The soffits' crowns: the middle opening 576 wide, the others 384 (each soffit's segments looking down).
    // Each soffit segment's stretch along the line; touching stretches are one opening.
    std::vector<std::array<int, 2>> stretches;

    for (const Game::OutdoorBModelFace &face : pViaduct->faces)
    {
        // Sloping and looking down: a soffit's segment (the deck's underside is level).
        if (faceNormal(*pViaduct, face)[2] < -0.1 && heightsOf(*pViaduct, face)[0] < heightsOf(*pViaduct, face)[1])
        {
            std::array<int, 2> stretch = {1 << 30, -(1 << 30)};

            for (const uint16_t index : face.vertexIndices)
            {
                stretch = {std::min(stretch[0], pViaduct->vertices[index].y),
                    std::max(stretch[1], pViaduct->vertices[index].y)};
            }

            stretches.push_back(stretch);
        }
    }

    std::sort(stretches.begin(), stretches.end());
    std::vector<int> widths;

    for (size_t index = 0; index < stretches.size();)
    {
        std::array<int, 2> opening = stretches[index];

        for (++index; index < stretches.size() && stretches[index][0] <= opening[1] + 1; ++index)
        {
            opening[1] = std::max(opening[1], stretches[index][1]);
        }

        widths.push_back(opening[1] - opening[0]);
    }

    CHECK(widths == std::vector<int>{384, 576, 384});
    std::vector<ProjectIssue> refused;
    IdsLock lock;
    thingsOf("structures:\n  - {id: thing:b, kind: bridge, line: [[50, 60], [56, 60]], width: 256, kerb_width: 48}\n",
        refused, lock);
    CHECK(anyIssue(refused, "a bridge's `kerb_width`"));
    std::vector<ProjectIssue> wide;
    IdsLock wideLock;
    thingsOf("structures:\n  - {id: thing:b, kind: bridge, line: [[50, 60], [52, 60]], height: 512, arches: {count: 2, "
        "spans: [512, 512]}}\n", wide, wideLock);
    CHECK(anyIssue(wide, "`spans` is each opening's width"));
}

TEST_CASE("S8d: signpost arms between the compass's ways; diagonal arms, a gable door, chamfered deck posts clear")
{
    std::vector<ProjectIssue> issues;
    IdsLock ids;
    // Castle Ironfist's guild sign GuildsignW: three boards at 90, 205 and 335; Erathia's two-way signs (ne, sw).
    const OutdoorThings things = thingsOf("structures:\n"
        "  - {id: thing:guilds, kind: sign, at: [50, 50], height: 288, width: 64, post: 32, arms: [{title: Spirit, "
        "toward: 205}, {title: Mind, toward: 335}, {title: Body, toward: 90}]}\n"
        "  - {id: thing:two_way, kind: sign, at: [60, 50], height: 272, width: 144, arms: [{title: One, toward: ne}, "
        "{title: Two, toward: sw}]}\n"
        "  - {id: thing:quay, kind: deck, outline: [[41.78, 34.94], [42.0, 34.94], [42.25, 35.31], [44.75, 35.31], "
        "[45.0, 35.19], [45.22, 35.19], [45.22, 36.19], [45.0, 36.19], [44.75, 35.81], [43.75, 35.81], "
        "[43.75, 38.12], [43.25, 38.12], [43.25, 35.81], [42.25, 35.81], [42.0, 35.94], [41.78, 35.94]], "
        "level: 192, thickness: 48, posts: 64, post_every: 512}\n", issues, ids);
    REQUIRE(issues.empty());
    const Game::OutdoorBModel *pGuilds = modelNamed(things, "thing:guilds");
    const Game::OutdoorBModel *pTwoWay = modelNamed(things, "thing:two_way");
    const Game::OutdoorBModel *pQuay = modelNamed(things, "thing:quay");
    REQUIRE((pGuilds && pTwoWay && pQuay));
    // The board toward 205 (south-south-west) reaches out south and a little west of the post.
    int least = 1 << 30;
    int middleX = (pGuilds->minX + pGuilds->maxX) / 2;
    int southmostX = 0;

    for (const Game::OutdoorBModelVertex &vertex : pGuilds->vertices)
    {
        if (vertex.y < least)
        {
            least = vertex.y;
            southmostX = vertex.x;
        }
    }

    CHECK(southmostX < middleX);
    CHECK(findOutdoorCoplanarFaces({*pGuilds}).empty());
    CHECK(findOutdoorCoplanarFaces({*pTwoWay}).empty());
    CHECK(findOutdoorCoplanarFaces({*pQuay}).empty());
    std::vector<ProjectIssue> refused;
    IdsLock lock;
    thingsOf("structures:\n  - {id: thing:s, kind: sign, at: [50, 50], arms: [{title: A, toward: 400}]}\n", refused,
        lock);
    CHECK(anyIssue(refused, "degrees clockwise from north"));
    // Erathia's A-frame: a door cut into the gable end does not lie on the gable.
    const Game::OutdoorBModel frame = raisedPlot("door: {part: p1, wall: n, bay: 1}, parts: [{id: p1, size: [512, "
        "608], wall_height: 128, roof: gable, roof_height: 498, eaves: 16, ridge_along: ns, door_height: 256}]");
    CHECK(findOutdoorCoplanarFaces({frame}).empty());
}

TEST_CASE("S8d: a chamfered platform, a culvert's grating, a tent with a door under a hip, a doorway's turf hood")
{
    std::vector<ProjectIssue> issues;
    IdsLock ids;
    const OutdoorThings things = thingsOf("structures:\n"
        "  - {id: thing:deck, kind: platform, at: [50, 50], size: [768, 768], height: 64, chamfer: 224, "
        "textures: {top: t14a05, wall: t06a01}}\n"
        "  - {id: thing:outfall, kind: culvert, at: [60, 50], width: 488, height: 504, pipe: 48, textures: "
        "{wall: t06a01, grating: t14a07}, grating: {bars: [2, 3], width: 18}, into: {map: d01.blv}}\n"
        "  - {id: thing:healer, kind: tent, at: [70, 50], size: [528, 656], wall_height: 256, lean: 32, height: 384, "
        "open: false, roof: hip, textures: {canvas: t14a01, door: t14a03}, house: 926, hint: Tent}\n"
        "  - {id: thing:bandits, kind: doorway, at: [80, 50], facing: e, hood: 128, roof: gable, "
        "textures: {wall: t06a01, roof: t14a05}, into: {map: d02.blv}}\n"
        "  - {id: thing:turned, kind: doorway, at: [80, 50], turn: -90, hood: 128, roof: gable, "
        "textures: {wall: t06a01, roof: t14a05}, into: {map: d02.blv}}\n", issues, ids);
    REQUIRE(issues.empty());
    const Game::OutdoorBModel *pDeck = modelNamed(things, "thing:deck");
    const Game::OutdoorBModel *pOutfall = modelNamed(things, "thing:outfall");
    const Game::OutdoorBModel *pTent = modelNamed(things, "thing:healer");
    const Game::OutdoorBModel *pBandits = modelNamed(things, "thing:bandits");
    const Game::OutdoorBModel *pTurned = modelNamed(things, "thing:turned");
    REQUIRE((pDeck && pOutfall && pTent && pBandits && pTurned));
    // The deck's top: one face of eight corners.
    REQUIRE(facesWith(*pDeck, "t14a05").size() == 1);
    CHECK(facesWith(*pDeck, "t14a05")[0]->vertexIndices.size() == 8);
    // Five bars, six faces each, carrying the way in (the dark face's event).
    const std::vector<const Game::OutdoorBModelFace *> bars = facesWith(*pOutfall, "t14a07");
    CHECK(bars.size() == 30);
    const std::vector<const Game::OutdoorBModelFace *> dark = facesWith(*pOutfall, "solid01");
    REQUIRE(dark.size() == 1);
    CHECK(bars.front()->cogTriggeredNumber == dark[0]->cogTriggeredNumber);
    CHECK(findOutdoorCoplanarFaces({*pOutfall}).empty());
    // P3 2026-11-24: the upright bars' feet 2 under the water (12 over the floor), not on its plane (X1's outfall).
    CHECK(findOutdoorBackToBackFaces({*pOutfall}).empty());
    int barFoot = 1 << 30;

    for (const Game::OutdoorBModelFace *pBar : bars)
    {
        barFoot = std::min(barFoot, heightsOf(*pOutfall, *pBar)[0]);
    }

    // The dark face stands on the water.
    CHECK(barFoot == heightsOf(*pOutfall, *dark[0])[0] - 2);
    // The tent's door on its closed front carries the house; the canvas says "Tent"; a hip, no gable triangle.
    const std::vector<const Game::OutdoorBModelFace *> door = facesWith(*pTent, "t14a03");
    REQUIRE(door.size() == 1);
    const std::vector<const Game::OutdoorBModelFace *> canvas = facesWith(*pTent, "t14a01");
    REQUIRE(!canvas.empty());
    CHECK(door[0]->cogTriggeredNumber != canvas[0]->cogTriggeredNumber);
    CHECK(findOutdoorCoplanarFaces({*pTent}).empty());
    CHECK(findOutdoorBackToBackFaces({*pTent}).empty());
    // A doorway facing east is one turned -90; its portico in the roof's texture.
    CHECK(pBandits->vertices.size() == pTurned->vertices.size());
    CHECK(pBandits->minX == pTurned->minX);
    CHECK(pBandits->maxY == pTurned->maxY);
    CHECK(facesWith(*pBandits, "t14a05").size() == 3);
    std::vector<ProjectIssue> refused;
    IdsLock lock;
    thingsOf("structures:\n"
        "  - {id: thing:p, kind: platform, at: [50, 50], size: [256, 256], chamfer: 128}\n"
        "  - {id: thing:t, kind: tent, at: [60, 50], wall_height: 256, open: true, textures: {door: t14a03}}\n"
        "  - {id: thing:c, kind: culvert, at: [70, 50], grating: {bars: [0, 0]}}\n"
        "  - {id: thing:d, kind: doorway, at: [80, 50], facing: up}\n", refused, lock);
    CHECK(anyIssue(refused, "a platform's `chamfer`"));
    CHECK(anyIssue(refused, "a tent's door is on its closed front"));
    CHECK(anyIssue(refused, "a culvert's grating"));
    CHECK(anyIssue(refused, "a doorway's `facing` is n, e, s or w"));
}

TEST_CASE("S8d: a half-hipped gable, a pent roof round a storey, walls that flare out")
{
    // Erathia's House 10E/W: hipped at its ends, gabled above, a skirt roof at the first floor.
    const Game::OutdoorBModel house = raisedPlot("door: {wall: s, bay: 2}, eaves: 64, fascia: 0, ridge: 0, "
        "textures: {roof: t14a05, gable: t06a01, pent: t14b05}, parts: [{size: [768, 512], wall_height: 512, "
        "roof: gable, roof_height: 320, half_hip: 192, pent: {height: 256, out: 128, rise: 64}}]");
    // Two eaves slopes and two hips, a small gable over each hip.
    CHECK(facesWith(house, "t14a05").size() == 4);
    CHECK(facesWith(house, "t06a01").size() == 2);

    for (const Game::OutdoorBModelFace *pFace : facesWith(house, "t06a01"))
    {
        CHECK(heightsOf(house, *pFace)[1] - heightsOf(house, *pFace)[0] == 128);
    }

    // The pent: one slope over each of the four walls, from 64 over its edge at the wall.
    CHECK(facesWith(house, "t14b05").size() == 4);
    CHECK(findOutdoorCoplanarFaces({house}).empty());
    CHECK(anyIssue(buildingIssues("parts: [{size: [512, 512], roof: hip, half_hip: 64}]"), "half_hip hips"));
    CHECK(anyIssue(buildingIssues("parts: [{size: [512, 512], wall_height: 256, pent: {height: 224}}]"),
        "a pent is"));
    // Castle Gryphonheart's bailey: walls leaning out 150 over 512, the flat top wider than the foot.
    const Game::OutdoorBModel bailey = raisedPlot("door: none, eaves: 0, fascia: 0, textures: {roof: t14a05}, "
        "parts: [{size: [1536, 1024], wall_height: 512, flare: 150, roof: flat, windows: none}]");
    const Game::OutdoorBModel upright = raisedPlot("door: none, eaves: 0, fascia: 0, textures: {roof: t14a05}, "
        "parts: [{size: [1536, 1024], wall_height: 512, roof: flat, windows: none}]");
    const std::array<int, 4> top = planBounds(bailey, "t14a05");
    const std::array<int, 4> foot = planBounds(upright, "t14a05");
    CHECK(top[2] - top[0] == foot[2] - foot[0] + 300);
    CHECK(anyIssue(buildingIssues("parts: [{size: [512, 512], batter: 32, flare: 32}]"), "not with `batter`"));
}

TEST_CASE("S8d: audit names a solid decoration in a doorway's way, not one beside it or one walked through")
{
    // XD-01's stash keg: smlbarel (radius 30) 68 inside the doorway, 28 off the line through its middle.
    LoadedMap map;
    map.indoor = Game::IndoorMapData();
    Game::IndoorMapData &indoor = *map.indoor;
    indoor.vertices = {{800, 4600, -384}, {800, 4800, -384}, {800, 4800, -128}, {800, 4600, -128}};
    Game::IndoorFace portal;
    portal.isPortal = true;
    portal.vertexIndices = {0, 1, 2, 3};
    portal.roomNumber = 6;
    portal.roomBehindNumber = 9;
    indoor.faces.push_back(portal);
    const auto entity = [](uint16_t listId, int x, int y)
    {
        Game::IndoorEntity placed;
        placed.decorationListId = listId;
        placed.x = x;
        placed.y = y;
        placed.z = -384;
        placed.name = "stash_barrel";
        return placed;
    };
    // In the way; beside the opening; far out; a keg one walks through (MoveThrough).
    indoor.entities = {entity(1, 868, 4672), entity(1, 868, 4790), entity(1, 1100, 4700), entity(2, 868, 4700)};
    const std::string table = "Decoration Data\n#\tInternalName\tHint\tType\tRadius\tHeight\tLightRadius\tLightRed\t"
        "LightGreen\tLightBlue\tSoundId\tFlags\tSpriteId\n"
        "1\tnull\tnull\t0\t8\t8\t0\t0\t0\t0\t0\t0\t0\n"
        "2\tsmlbarel\tKeg\t0\t30\t40\t0\t0\t0\t0\t0\t0\t100\n"
        "3\tmist\tMist\t0\t30\t40\t0\t0\t0\t0\t0\tMoveThrough\t101\n";
    size_t found = 0;

    for (const AuditFinding &finding : auditLooks(map, table, {}))
    {
        if (finding.code == "thing.in_doorway")
        {
            ++found;
            CHECK(finding.message.find("decoration 0 ") != std::string::npos);
        }
    }

    CHECK(found == 1);
}

TEST_CASE("P3: audit names a table across a doorway's way out (XD-14's great hall), not one clear of it or low")
{
    // XD-14's kennels door: a portal 224 wide in the kennels' face of a wall 128 thick (x 1408 to 1536), its jambs
    // through the wall, and the hall's long table 64 high and 64 off the wall running across the opening's width.
    const auto mapWith = [](int tableNorth, int tableHigh, uint32_t attributes)
    {
        LoadedMap map;
        map.world = "xeen";
        map.indoor = Game::IndoorMapData();
        Game::IndoorMapData &indoor = *map.indoor;
        const auto quad = [&indoor](std::array<std::array<int, 3>, 4> corners, bool isPortal, uint32_t bits)
        {
            Game::IndoorFace face;
            face.isPortal = isPortal;
            face.attributes = bits;
            face.roomNumber = 12;
            face.roomBehindNumber = isPortal ? 16 : 12;

            for (const std::array<int, 3> &corner : corners)
            {
                face.vertexIndices.push_back(static_cast<uint16_t>(indoor.vertices.size()));
                indoor.vertices.push_back({corner[0], corner[1], corner[2]});
            }

            indoor.faces.push_back(face);
        };
        quad({{{1536, 944, 0}, {1536, 720, 0}, {1536, 720, 320}, {1536, 944, 320}}}, true, 0);
        quad({{{1408, 720, 0}, {1536, 720, 0}, {1536, 720, 320}, {1408, 720, 320}}}, false, 0);
        quad({{{1536, 944, 0}, {1408, 944, 0}, {1408, 944, 320}, {1536, 944, 320}}}, false, 0);
        quad({{{1344, tableNorth, tableHigh}, {1344, -128, tableHigh}, {1344, -128, 0}, {1344, tableNorth, 0}}}, false,
            attributes);
        return map;
    };
    const auto found = [](const LoadedMap &map)
    {
        size_t count = 0;

        for (const AuditFinding &finding : auditLooks(map, "", {}))
        {
            if (finding.code == "face.in_doorway")
            {
                ++count;
                CHECK(finding.severity == "error");
                CHECK(finding.message.find("face 3 ") != std::string::npos);
            }
        }

        return count;
    };
    // Across the opening: the party's middle gets 155 out, short of the jambs' 128 and its radius.
    CHECK(found(mapWith(896, 64, 0)) == 1);
    // Clear of the opening's width and the party's radius (as rebuilt); low enough to step on; a wall one sees.
    CHECK(found(mapWith(656, 64, 0)) == 0);
    CHECK(found(mapWith(896, 48, 0)) == 0);
    CHECK(found(mapWith(896, 320, 0)) == 0);
    // Not drawn and as high: an invisible wall.
    CHECK(found(mapWith(896, 320, Game::faceAttributeBit(Game::FaceAttribute::Invisible))) == 1);
}

TEST_CASE("Xeen dressing: audit keeps containers off doors, doorways and walking lines, by walls, clumps in storerooms")
{
    // One room 2000 by 1600 (sector 0): a doorway in its west wall (y 700-900), a door in its north wall (x 900-1100).
    LoadedMap map;
    map.indoor = Game::IndoorMapData();
    Game::IndoorMapData &indoor = *map.indoor;
    const auto upright = [&indoor](int x0, int y0, int x1, int y1, bool portal)
    {
        const uint16_t first = static_cast<uint16_t>(indoor.vertices.size());
        indoor.vertices.push_back({x0, y0, 0});
        indoor.vertices.push_back({x1, y1, 0});
        indoor.vertices.push_back({x1, y1, 256});
        indoor.vertices.push_back({x0, y0, 256});
        Game::IndoorFace face;
        face.isPortal = portal;
        face.vertexIndices = {first, uint16_t(first + 1), uint16_t(first + 2), uint16_t(first + 3)};
        face.roomNumber = 0;
        face.roomBehindNumber = portal ? 1 : 0;
        indoor.faces.push_back(face);
        return static_cast<uint16_t>(indoor.faces.size() - 1);
    };
    upright(0, 0, 2000, 0, false);
    upright(2000, 0, 2000, 1600, false);
    upright(2000, 1600, 0, 1600, false);
    upright(0, 1600, 0, 0, false);
    upright(0, 700, 0, 900, true);
    const uint16_t leaf = upright(900, 1600, 1100, 1600, false);
    map.state = Game::MapDeltaData();
    Game::MapDeltaDoor door;
    door.faceIds = {leaf};
    map.state->doors.push_back(door);
    const auto entity = [](uint16_t listId, int x, int y)
    {
        Game::IndoorEntity placed;
        placed.decorationListId = listId;
        placed.x = x;
        placed.y = y;
        placed.name = listId == 0 ? "bigbarel" : "statue";
        return placed;
    };
    // 0 in front of the doorway, 1 by the door, 2 in the open floor, 3 a statue (a set piece) on the line between
    // the openings, 4-6 a clump.
    indoor.entities = {entity(0, 200, 780), entity(0, 1150, 1450), entity(0, 1000, 400), entity(1, 500, 1200),
        entity(0, 1800, 100), entity(0, 1800, 250), entity(0, 1800, 400)};
    indoor.sectors.resize(2);
    indoor.sectors[0].decorationIds = {0, 1, 2, 3, 4, 5, 6};
    const std::string table = "Decoration Data\n#\tInternalName\tHint\tType\tRadius\tHeight\tLightRadius\tLightRed\t"
        "LightGreen\tLightBlue\tSoundId\tFlags\tSpriteId\n"
        "1\tbigbarel\tbarrel\t0\t30\t40\t0\t0\t0\t0\t0\t0\t100\n"
        "2\tstatue\tStatue\t0\t40\t160\t0\t0\t0\t0\t0\t0\t101\n";
    std::map<std::string, std::vector<std::string>> found;

    for (const AuditFinding &finding : auditDressing(map, table, {}))
    {
        found[finding.code].push_back(finding.message.substr(0, finding.message.find(' ', 11)));
    }

    CHECK(found["dressing.doorway"] == std::vector<std::string>{"decoration 0"});
    CHECK(found["dressing.door"] == std::vector<std::string>{"decoration 1"});
    CHECK(found["dressing.wall"] == std::vector<std::string>{"decoration 2"});
    CHECK(found["dressing.walking_line"] == std::vector<std::string>{"decoration 3"});
    REQUIRE(found["dressing.clump"].size() == 1);

    // The statue is a set piece: on the walking line it is a warning, not an error.
    for (const AuditFinding &finding : auditDressing(map, table, {}))
    {
        if (finding.code == "dressing.walking_line")
        {
            CHECK(finding.severity == "warning");
        }
    }

    // Two more barrels make the room a storeroom (8 containers): the clump is allowed, the floor barrel 320 away.
    indoor.entities.push_back(entity(0, 1900, 800));
    indoor.entities.push_back(entity(0, 1900, 1100));
    indoor.sectors[0].decorationIds = {0, 1, 2, 3, 4, 5, 6, 7, 8};
    found.clear();

    for (const AuditFinding &finding : auditDressing(map, table, {}))
    {
        found[finding.code].push_back(finding.message.substr(0, finding.message.find(' ', 11)));
    }

    CHECK(found["dressing.clump"].empty());
    CHECK(found["dressing.wall"] == std::vector<std::string>{"decoration 2"});
}

TEST_CASE("Xeen dressing: doorway band, set pieces, table tops, merged openings, free gap and tagged storerooms")
{
    // One room 2000 by 1600 (sector 0) with a floor at 0: two portals side by side in its west wall (y 700-800 and
    // 800-900: one opening), a doorway in its east wall (y 700-900), and a stretch 200 wide (y 700-900, x 800-1200) on
    // the walking line between them.
    LoadedMap map;
    map.world = "xeen";
    map.indoor = Game::IndoorMapData();
    Game::IndoorMapData &indoor = *map.indoor;
    const auto upright = [&indoor](int x0, int y0, int x1, int y1, bool portal)
    {
        const uint16_t first = static_cast<uint16_t>(indoor.vertices.size());
        indoor.vertices.push_back({x0, y0, 0});
        indoor.vertices.push_back({x1, y1, 0});
        indoor.vertices.push_back({x1, y1, 256});
        indoor.vertices.push_back({x0, y0, 256});
        Game::IndoorFace face;
        face.isPortal = portal;
        face.vertexIndices = {first, uint16_t(first + 1), uint16_t(first + 2), uint16_t(first + 3)};
        face.roomNumber = 0;
        face.roomBehindNumber = portal ? 1 : 0;
        indoor.faces.push_back(face);
        return static_cast<uint16_t>(indoor.faces.size() - 1);
    };
    upright(0, 0, 2000, 0, false);
    upright(2000, 0, 2000, 700, false);
    upright(2000, 900, 2000, 1600, false);
    upright(2000, 1600, 0, 1600, false);
    upright(0, 1600, 0, 900, false);
    upright(0, 700, 0, 0, false);
    const uint16_t westA = upright(0, 700, 0, 800, true);
    const uint16_t westB = upright(0, 800, 0, 900, true);
    const uint16_t east = upright(2000, 700, 2000, 900, true);
    upright(800, 700, 1200, 700, false);
    upright(1200, 900, 800, 900, false);
    {
        const uint16_t first = static_cast<uint16_t>(indoor.vertices.size());
        indoor.vertices.push_back({0, 0, 0});
        indoor.vertices.push_back({2000, 0, 0});
        indoor.vertices.push_back({2000, 1600, 0});
        indoor.vertices.push_back({0, 1600, 0});
        Game::IndoorFace floor;
        floor.vertexIndices = {first, uint16_t(first + 1), uint16_t(first + 2), uint16_t(first + 3)};
        floor.roomNumber = 0;
        indoor.faces.push_back(floor);
    }
    const auto entity = [](uint16_t listId, int x, int y, int z = 0)
    {
        static const char *const Names[] = {"bigbarel", "statue", "goblet", "table"};
        Game::IndoorEntity placed;
        placed.decorationListId = listId;
        placed.x = x;
        placed.y = y;
        placed.z = z;
        placed.name = Names[listId];
        return placed;
    };
    // 0 a barrel beside the east doorway along the wall, 250 past its end (allowed); 1 one 150 past it (an error);
    // 2 a barrel 280 in front of the west opening, clicked (a set piece: no doorway error); 3 a goblet on the line
    // (too small); 4 a barrel on a table on the line (not on the floor); 5 a table in the narrow stretch.
    indoor.entities = {entity(0, 1900, 450), entity(0, 1900, 550), entity(0, 280, 895), entity(2, 500, 800),
        entity(0, 700, 800, 80), entity(3, 1000, 800)};
    indoor.entities[2].eventIdPrimary = 5;
    indoor.sectors.resize(2);
    indoor.sectors[0].decorationIds = {0, 1, 2, 3, 4, 5};
    const std::string table = "Decoration Data\n#\tInternalName\tHint\tType\tRadius\tHeight\tLightRadius\tLightRed\t"
        "LightGreen\tLightBlue\tSoundId\tFlags\tSpriteId\n"
        "1\tbigbarel\tbarrel\t0\t30\t40\t0\t0\t0\t0\t0\t0\t100\n"
        "2\tstatue\tStatue\t0\t40\t160\t0\t0\t0\t0\t0\t0\t101\n"
        "3\tgoblet\tGoblet\t0\t10\t20\t0\t0\t0\t0\t0\t0\t102\n"
        "4\ttable\tTable\t0\t40\t64\t0\t0\t0\t0\t0\t0\t103\n";
    std::map<std::string, std::vector<std::string>> found;
    std::map<std::string, std::vector<std::string>> severities;

    for (const AuditFinding &finding : auditDressing(map, table, {}))
    {
        found[finding.code].push_back(finding.message.substr(0, finding.message.find(' ', 11)));
        severities[finding.code].push_back(finding.severity);
    }

    CHECK(found["dressing.doorway"] == std::vector<std::string>{"decoration 1"});
    // The table on the line (furniture: an error) leaves 60 on each side in the stretch 200 wide (an error too).
    CHECK(found["dressing.walking_line"] == std::vector<std::string>{"decoration 5", "decoration 5"});
    CHECK(severities["dressing.walking_line"] == std::vector<std::string>{"error", "error"});
    CHECK(found["dressing.wall"].empty());

    // The two west portals are one opening: the line runs from its middle to the east doorway's.
    for (const AuditFinding &finding : auditDressing(map, table, {}))
    {
        if (finding.code == "dressing.walking_line")
        {
            CHECK(finding.message.find("faces " + std::to_string(westA) + "+" + std::to_string(westB) + " and "
                      + std::to_string(east))
                != std::string::npos);
        }
    }

    // Three barrels together outside a storeroom: a clump, unless the room is tagged `store: true`.
    indoor.entities.push_back(entity(0, 1800, 1500));
    indoor.entities.push_back(entity(0, 1650, 1500));
    indoor.entities.push_back(entity(0, 1500, 1500));
    indoor.sectors[0].decorationIds = {0, 1, 2, 3, 4, 5, 6, 7, 8};
    size_t clumps = 0;

    for (const AuditFinding &finding : auditDressing(map, table, {}))
    {
        clumps += finding.code == "dressing.clump" ? 1 : 0;
    }

    CHECK(clumps == 1);
    clumps = 0;

    for (const AuditFinding &finding : auditDressing(map, table, {}, {0}))
    {
        clumps += finding.code == "dressing.clump" ? 1 : 0;
    }

    CHECK(clumps == 0);

    // The installed map's <stem>.studio.yml carries the storerooms and hanging decorations back.
    const DressingFacts facts = studioFileDressingFacts(
        YAML::Load("project: \"x\"\nhanging_decorations: [3, 4]\nstorerooms: [6]\n"));
    CHECK(facts.hanging == std::set<int>{3, 4});
    CHECK(facts.storerooms == std::set<int>{6});
}

TEST_CASE("Xeen dressing outdoors: house doors, the walking line between them, house walls, roads and clumps")
{
    // Two houses 512 square across a street: A (y 0-512) with its door north (x 192-320, event 1), B (y 1536-2048)
    // with its door south (event 2); a road along the cells' row 69 (world y -2816) far from both.
    LoadedMap map;
    map.outdoor = Game::OutdoorMapData();
    Game::OutdoorMapData &outdoor = *map.outdoor;
    outdoor.heightMap.assign(128 * 128, 0);
    outdoor.tileMap.assign(128 * 128, 0);
    const auto wall = [](Game::OutdoorBModel &model, int x0, int y0, int x1, int y1, uint16_t event)
    {
        const uint16_t first = static_cast<uint16_t>(model.vertices.size());
        model.vertices.push_back({x0, y0, 0});
        model.vertices.push_back({x1, y1, 0});
        model.vertices.push_back({x1, y1, 256});
        model.vertices.push_back({x0, y0, 256});
        Game::OutdoorBModelFace face;
        face.vertexIndices = {first, uint16_t(first + 1), uint16_t(first + 2), uint16_t(first + 3)};
        face.cogTriggeredNumber = event;
        model.faces.push_back(face);
    };
    const auto house = [&wall](int y0, bool doorNorth, uint16_t event)
    {
        Game::OutdoorBModel model;
        model.minX = 0;
        model.maxX = 512;
        model.minY = y0;
        model.maxY = y0 + 512;
        const int doorY = doorNorth ? y0 + 512 : y0;
        const int otherY = doorNorth ? y0 : y0 + 512;
        wall(model, 0, doorY, 192, doorY, 0);
        wall(model, 192, doorY, 320, doorY, event);
        wall(model, 320, doorY, 512, doorY, 0);
        wall(model, 0, otherY, 512, otherY, 0);
        wall(model, 0, y0, 0, y0 + 512, 0);
        wall(model, 512, y0, 512, y0 + 512, 0);
        return model;
    };
    outdoor.bmodels = {house(0, true, 1), house(1536, false, 2)};
    map.scriptText = "RegisterEvent(1, \"Inn\", function()\n    evt.EnterHouse(5)\nend, \"Inn\")\n"
        "RegisterEvent(2, \"Smithy\", function()\n    evt.EnterHouse(6)\nend, \"Smithy\")\n"
        "RegisterEvent(3, \"Sign\", nil, \"Sign\")\n";
    std::vector<uint8_t> cellKinds(128 * 128, 0);

    for (int x = 66; x <= 72; ++x)
    {
        cellKinds[69 * 128 + x] = 3;
    }

    const auto entity = [](const char *pName, int x, int y)
    {
        Game::OutdoorEntity placed;
        placed.name = pName;
        placed.x = x;
        placed.y = y;
        return placed;
    };
    // 0 a barrel before door A, 1 a tree right before it (a set piece), 2 a rock on the walking line, 3 a barrel by
    // house A but off its wall, 4 a rock on the road, 5 one by it, 6-8 a clump in the open.
    outdoor.entities = {entity("bigbarel", 380, 700), entity("tree", 256, 600), entity("rock", 280, 1024),
        entity("bigbarel", 900, 256), entity("rock", 3000, -2850), entity("rock", 3000, -3100),
        entity("bigbarel", 6000, 6000), entity("bigbarel", 6100, 6000), entity("bigbarel", 6200, 6000)};
    const std::string table = "Decoration Data\n#\tInternalName\tHint\tType\tRadius\tHeight\tLightRadius\tLightRed\t"
        "LightGreen\tLightBlue\tSoundId\tFlags\tSpriteId\n"
        "1\tbigbarel\tbarrel\t0\t30\t40\t0\t0\t0\t0\t0\t0\t100\n"
        "2\ttree\tTree\t0\t40\t400\t0\t0\t0\t0\t0\t0\t101\n"
        "3\trock\tRock\t0\t40\t60\t0\t0\t0\t0\t0\t0\t102\n";
    std::map<std::string, std::vector<std::string>> found;
    std::map<std::string, std::vector<std::string>> levels;

    for (const AuditFinding &finding : auditDressing(map, table, {}, {}, cellKinds))
    {
        found[finding.code].push_back(finding.message.substr(0, finding.message.find(' ', 11)));
        levels[finding.code].push_back(finding.severity);
    }

    CHECK(found["dressing.door"] == std::vector<std::string>{"decoration 0", "decoration 1"});
    CHECK(levels["dressing.door"] == std::vector<std::string>{"error", "warning"});
    CHECK(found["dressing.walking_line"] == std::vector<std::string>{"decoration 1", "decoration 2"});
    // A rock is a set piece (decision D-14): a warning on the line, as the tree.
    CHECK(levels["dressing.walking_line"] == std::vector<std::string>{"warning", "warning"});
    CHECK(found["dressing.wall"] == std::vector<std::string>{"decoration 3"});
    CHECK(found["dressing.road"] == std::vector<std::string>{"decoration 4"});
    CHECK(found["dressing.clump"].size() == 1);
    REQUIRE(found["dressing.outdoor"].size() == 1);

    // Without the doors' script, no house doors: their faces are walls, nothing is in front of a door.
    map.scriptText.clear();
    found.clear();

    for (const AuditFinding &finding : auditDressing(map, table, {}, {}, cellKinds))
    {
        found[finding.code].push_back(finding.message.substr(0, finding.message.find(' ', 11)));
    }

    CHECK(found["dressing.door"].empty());
    CHECK(found["dressing.walking_line"].empty());
}

TEST_CASE("F40 prop overlap: barrels drawn into each other and into a wall, an item inside one, a model's outline")
{
    // A room (floor at 0, x and y 0-1000) with a wall along its north side (y 1000).
    LoadedMap map;
    map.world = "xeen";
    map.fileName = "xeen_test.blv";
    map.indoor = Game::IndoorMapData();
    Game::IndoorMapData &indoor = *map.indoor;
    const auto face = [&indoor](const std::vector<Game::IndoorVertex> &points, const std::array<int32_t, 3> &normal)
    {
        Game::IndoorFace added;

        for (const Game::IndoorVertex &point : points)
        {
            added.vertexIndices.push_back(static_cast<uint16_t>(indoor.vertices.size()));
            indoor.vertices.push_back(point);
        }

        added.textureName = "stone";
        added.planeNormal = normal;
        indoor.faces.push_back(added);
    };
    face({{0, 0, 0}, {1000, 0, 0}, {1000, 1000, 0}, {0, 1000, 0}}, {0, 0, 65536});
    face({{0, 1000, 0}, {0, 1000, 300}, {1000, 1000, 300}, {1000, 1000, 0}}, {0, -65536, 0});
    const auto entity = [](const char *pName, int x, int y)
    {
        Game::IndoorEntity placed;
        placed.name = pName;
        placed.x = x;
        placed.y = y;
        return placed;
    };
    // 0 and 1 drawn 20 into each other; 2 standing 20 in the wall; 3 and 4 kegs 15 apart, whose model is drawn 60
    // round them.
    indoor.entities = {entity("bigbarel", 300, 300), entity("bigbarel", 340, 300), entity("bigbarel", 500, 990),
        entity("keg", 700, 500), entity("keg", 775, 500)};
    // A treasure inside barrel 1.
    Game::IndoorSpawn treasure;
    treasure.x = 355;
    treasure.y = 300;
    treasure.typeId = 2;
    indoor.spawns.push_back(treasure);
    PropOverlapData data;
    data.decorationTableText = "Decoration Data\n#\tInternalName\tHint\tType\tRadius\tHeight\tLightRadius\tLightRed\t"
        "LightGreen\tLightBlue\tSoundId\tFlags\tSpriteId\n"
        "1\tbigbarel\tbarrel\t0\t30\t40\t0\t0\t0\t0\t0\t0\t100\n"
        "2\tkeg\tkeg\t0\t30\t40\t0\t0\t0\t0\t0\t0\t100\n";
    const auto findings = [&map, &data]()
    {
        std::map<std::string, std::vector<std::string>> found;

        for (const AuditFinding &finding : auditPropOverlap(map, data, std::string()))
        {
            found[finding.code + " " + finding.severity].push_back(
                finding.message.substr(0, finding.message.find(' ', 11)));
        }

        return found;
    };
    std::map<std::string, std::vector<std::string>> found = findings();
    CHECK(found["prop.overlap error"] == std::vector<std::string>{"decoration 0"});
    CHECK(found["prop.wall error"] == std::vector<std::string>{"decoration 2"});
    CHECK(found["item.hidden error"] == std::vector<std::string>{"treasure spawn"});
    CHECK(found["prop.squeeze warning"] == std::vector<std::string>{"decoration 3"});

    // The kegs' model (a square 3 across, 1 high, bound 40 high): drawn 60 round each, into each other.
    data.bindingTexts = {"decorations:\n  - {name: keg, model: keg.glb, height: 40}\n"};
    data.readModel = [](const std::string &model) -> std::optional<PropModelShape>
    {
        if (model != "keg.glb")
        {
            return std::nullopt;
        }

        PropModelShape shape;
        shape.height = 1.0;
        shape.outlines.fill({{-1.5, -1.5}, {1.5, -1.5}, {1.5, 1.5}, {-1.5, 1.5}});
        return shape;
    };
    found = findings();
    CHECK(found["prop.overlap error"] == std::vector<std::string>{"decoration 0", "decoration 3"});
    CHECK(found["prop.squeeze warning"].empty());
}

TEST_CASE("Xeen prop support: a barrel over a terrace's edge, one in the air, a chest of the wrong pieces")
{
    // A terrace (floor at 0, x 0-1000) over a lower floor (at -256, x 1000-2000), both y 0-1000.
    LoadedMap map;
    map.world = "xeen";
    map.indoor = Game::IndoorMapData();
    Game::IndoorMapData &indoor = *map.indoor;
    const auto face = [&indoor](const std::vector<Game::IndoorVertex> &points, const char *pTexture, uint16_t event,
                          const std::array<int32_t, 3> &normal)
    {
        Game::IndoorFace added;

        for (const Game::IndoorVertex &point : points)
        {
            added.vertexIndices.push_back(static_cast<uint16_t>(indoor.vertices.size()));
            indoor.vertices.push_back(point);
        }

        added.textureName = pTexture;
        added.cogTriggered = event;
        added.planeNormal = normal;
        indoor.faces.push_back(added);
    };
    const std::array<int32_t, 3> up = {0, 0, 65536};
    face({{0, 0, 0}, {1000, 0, 0}, {1000, 1000, 0}, {0, 1000, 0}}, "floor", 0, up);
    face({{1000, 0, -256}, {2000, 0, -256}, {2000, 1000, -256}, {1000, 1000, -256}}, "floor", 0, up);
    // A chest box (x 200-260, y 700-740, 40 high) of ten clicked faces: six MM6 chest pieces and four planks.
    for (int index = 0; index < 10; ++index)
    {
        const int y = 700 + index * 4;
        face({{200, y, 0}, {260, y, 0}, {260, y, 40}, {200, y, 40}}, index < 6 ? "ch1frle" : "plank", 5,
            {0, -65536, 0});
    }

    const auto entity = [](int x, int y, int z)
    {
        Game::IndoorEntity placed;
        placed.name = "bigbarel";
        placed.x = x;
        placed.y = y;
        placed.z = z;
        return placed;
    };
    // 0 half over the terrace's edge, 1 in the air over the terrace, 2 well on it.
    indoor.entities = {entity(990, 500, 0), entity(500, 500, 200), entity(300, 300, 0)};
    const std::string table = "Decoration Data\n#\tInternalName\tHint\tType\tRadius\tHeight\tLightRadius\tLightRed\t"
        "LightGreen\tLightBlue\tSoundId\tFlags\tSpriteId\n"
        "1\tbigbarel\tbarrel\t0\t30\t40\t0\t0\t0\t0\t0\t0\t100\n";
    std::map<std::string, std::vector<std::string>> found;
    std::map<std::string, std::vector<std::string>> levels;

    for (const AuditFinding &finding : auditPropSupport(map, table, std::string()))
    {
        found[finding.code].push_back(finding.message.substr(0, finding.message.find(' ', 11)));
        levels[finding.code].push_back(finding.severity);
    }

    CHECK(found["support.overhang"] == std::vector<std::string>{"decoration 0"});
    CHECK(levels["support.overhang"] == std::vector<std::string>{"error"});
    CHECK(found["support.floating"] == std::vector<std::string>{"decoration 1"});
    CHECK(found["support.edge"].empty());
    REQUIRE(found["chest.look"].size() == 1);
    CHECK(levels["chest.look"] == std::vector<std::string>{"error"});
    CHECK(found["chest.entrance"].empty());

    // All of MM6's chest pieces: a shipped chest. A barrel said to hang is not judged.
    for (Game::IndoorFace &placed : indoor.faces)
    {
        if (placed.cogTriggered == 5)
        {
            placed.textureName = "ch1frle";
        }
    }

    found.clear();

    for (const AuditFinding &finding : auditPropSupport(map, table, std::string(), {1}))
    {
        found[finding.code].push_back(finding.message.substr(0, finding.message.find(' ', 11)));
    }

    CHECK(found["chest.look"].empty());
    CHECK(found["support.floating"].empty());
    CHECK(found["support.overhang"] == std::vector<std::string>{"decoration 0"});

    // Outdoors on flat land at 0: a barrel 100 over it floats, one on it stands.
    LoadedMap land;
    land.world = "xeen";
    land.outdoor = Game::OutdoorMapData();
    land.outdoor->heightMap.assign(128 * 128, 0);
    land.outdoor->tileMap.assign(128 * 128, 0);
    Game::OutdoorEntity high;
    high.name = "bigbarel";
    high.z = 100;
    Game::OutdoorEntity low;
    low.name = "bigbarel";
    low.x = 1000;
    land.outdoor->entities = {high, low};
    found.clear();

    for (const AuditFinding &finding : auditPropSupport(land, table, std::string()))
    {
        found[finding.code].push_back(finding.message.substr(0, finding.message.find(' ', 11)));
    }

    CHECK(found["support.floating"] == std::vector<std::string>{"decoration 0"});
    CHECK(found["support.overhang"].empty());
    CHECK(found["support.edge"].empty());
}

TEST_CASE("outdoor player bits, a question before the click's work, and things shown from a handler's Lua")
{
    const std::string more = "structures:\n"
        "  - {id: thing:spring, kind: well, at: [50, 50], title: Lifeforce Spring, once: true, "
        "condition: {not: {player_bit: 11280}}, question: {ask: \"Drink (Yes/No)?\", answers: [Yes, Y], "
        "wrong_text: You leave it be., wrong_effects: [{lua: Xeen.leftIt()}]}, effects: [{player_bit: 11280}, {add: {var: BaseEndurance, value: 2}}]}\n"
        "  - {id: thing:coffin, kind: obelisk, at: [60, 60], title: Coffin, "
        "lua: \"if Opens() then HideThing(\\\"thing:lid\\\") ShowThing(\\\"thing:stair\\\") end\"}\n"
        "  - {id: thing:lid, kind: obelisk, at: [62, 60]}\n"
        "  - {id: thing:stair, kind: obelisk, at: [64, 60], hidden: true}\n"
        "  - {id: thing:fence, kind: barrier, line: [[70, 70], [80, 70]], height: 300}\n";
    const std::string house = "      - {building: building:home, at: [40, 40], facing: s, house: 904}\n";
    const BuiltOutdoor built = builtOutdoor(buildingProject(house, more), "oymap_outdoor_question");

    for (const ProjectIssue &issue : built.issues)
    {
        MESSAGE(issue.path << ": " << issue.message);
    }

    REQUIRE(built.built);
    const std::string &lua = built.lua;
    // The bit tested and set for the member who clicks; the question asked after the lock, the work on the answer.
    const size_t lock = lua.find("IsPlayerBitSet(PlayerBit(11280))");
    const size_t right = lua.find("if continueStep == 2 then");
    const size_t ask = lua.find("evt.AskQuestion(eventId, 1, 0, 2, \"Drink (Yes/No)?\", {\"Yes\", \"Y\"})");
    REQUIRE(lock != std::string::npos);
    REQUIRE(right != std::string::npos);
    REQUIRE(ask != std::string::npos);
    CHECK(right < lock);
    CHECK(lock < ask);
    CHECK(lua.find("function(continueStep)") != std::string::npos);
    CHECK(lua.find("local eventId = ") != std::string::npos);
    const size_t set = lua.find("SetPlayerBit(PlayerBit(11280))");
    REQUIRE(set != std::string::npos);
    CHECK(set > right);
    CHECK(set < lock);
    CHECK(lua.find("You leave it be.") != std::string::npos);
    // `wrong_effects` run in the wrong answer's branch, before the question is asked again.
    const size_t wrong = lua.find("Xeen.leftIt()");
    REQUIRE(wrong != std::string::npos);
    CHECK(wrong > lua.find("You leave it be."));
    CHECK(wrong < lock);
    // The Lua's ShowThing and HideThing are the calls {show} and {hide} write, inside the branch.
    CHECK(lua.find("ShowThing") == std::string::npos);
    CHECK(lua.find("HideThing") == std::string::npos);
    CHECK(lua.find("if Opens() then evt.SetFacetBit(") != std::string::npos);
    CHECK(lua.find("FacetBits.Untouchable, 0) end") != std::string::npos);
    // The barrier takes its line and height without a word the schema does not know.
    CHECK(std::none_of(built.warnings.begin(), built.warnings.end(), [](const std::string &warning)
    {
        return warning.find("does not apply") != std::string::npos;
    }));
}

#include "game/maps/OutdoorSceneYml.h"

#include <iterator>
#include <optional>

TEST_CASE("E9: sketch.yml `sounds` are the outdoor scene's ambient sounds, refused without a sound or a radius")
{
    Project project = buildingProject("      - {building: building:home, at: [40, 40], facing: s, house: 904, "
        "title: Home}\n", "sounds:\n"
        "  - {id: sound:surf, at: [64, 64], sound: waves.wav, radius: 6000, inner_radius: 2500, volume: 0.6}\n"
        "  - {id: sound:owls, at: [32, 96], sound: owls.wav, radius: 3000, height: 400, wait: [4, 9], "
        "night_only: true, on: false, pan: false}\n");
    project.root = std::filesystem::temp_directory_path() / "oymap_outdoor_sounds";
    BuildOptions options;
    options.outputDirectory = project.root / "build";
    BuildResult result;
    const bool built = buildOutdoorProject(project, options, result);

    for (const ProjectIssue &issue : result.issues)
    {
        MESSAGE(issue.path << ": " << issue.message);
    }

    REQUIRE(built);
    std::ifstream stream(project.root / "build" / "groundtest.scene.yml");
    const std::string text((std::istreambuf_iterator<char>(stream)), std::istreambuf_iterator<char>());
    std::string error;
    const std::optional<Game::OutdoorSceneData> scene = Game::OutdoorSceneYmlLoader().loadFromText(text, error);
    REQUIRE_MESSAGE(scene.has_value(), error);
    REQUIRE(scene->ambientSounds.size() == 2);
    const Game::WorldAmbientSound &surf = scene->ambientSounds[0];
    const Game::WorldAmbientSound &owls = scene->ambientSounds[1];
    CHECK(surf.sound == "waves.wav");
    CHECK(surf.outerRadius == doctest::Approx(6000.0f));
    CHECK(surf.innerRadius == doctest::Approx(2500.0f));
    CHECK(surf.volume == doctest::Approx(0.6f));
    CHECK(surf.startOn);
    CHECK(surf.key != owls.key);
    // The owls 400 over the ground, by night, silent until a script switches them on.
    CHECK(owls.innerRadius == doctest::Approx(750.0f));
    CHECK(owls.waitMinSeconds == doctest::Approx(4.0f));
    CHECK(owls.nightOnly);
    CHECK_FALSE(owls.startOn);
    // D-48: the owls heard centred, the surf panned.
    CHECK_FALSE(owls.pan);
    CHECK(surf.pan);
    CHECK(owls.position[0] < surf.position[0]);
    CHECK(owls.position[1] < surf.position[1]);

    Project bad = buildingProject("      - {building: building:home, at: [40, 40], facing: s, house: 904, "
        "title: Home}\n", "sounds:\n  - {id: sound:surf, at: [64, 64], sound: waves.wav, radius: 100, "
        "inner_radius: 200}\n");
    bad.root = std::filesystem::temp_directory_path() / "oymap_outdoor_sounds_bad";
    BuildOptions badOptions;
    badOptions.outputDirectory = bad.root / "build";
    BuildResult refused;
    CHECK_FALSE(buildOutdoorProject(bad, badOptions, refused));
    CHECK(std::any_of(refused.issues.begin(), refused.issues.end(),
        [](const ProjectIssue &issue) { return issue.message.find("a sound needs `sound`") != std::string::npos; }));
    std::error_code removeError;
    std::filesystem::remove_all(project.root, removeError);
    std::filesystem::remove_all(bad.root, removeError);
}

TEST_CASE("A6: a named arrival on a structure's top stands on that top, not on the land under it")
{
    // entrance:north is sketched at cell [100, 50]; a platform over it (D6's crust over the lava, 26 high), or beside
    // it.
    const auto arrivalHeight = [](const std::string &at, int height, const char *pFolder, bool &warned)
    {
        Project project = buildingProject("      - {building: building:home, at: [40, 40], facing: s, house: 904, "
            "title: Home}\n", "structures:\n  - {id: thing:crust, kind: platform, at: " + at + ", size: [512, 512], "
            "height: " + std::to_string(height) + "}\n");
        project.root = std::filesystem::temp_directory_path() / pFolder;
        BuildOptions options;
        options.outputDirectory = project.root / "build";
        BuildResult result;
        const bool built = buildOutdoorProject(project, options, result);

        for (const ProjectIssue &issue : result.issues)
        {
            MESSAGE(issue.path << ": " << issue.message);
        }

        std::error_code removeError;
        std::filesystem::remove_all(project.root, removeError);
        REQUIRE(built);
        warned = std::any_of(result.warnings.begin(), result.warnings.end(), [](const std::string &warning)
        {
            return warning.find("entrance:north lies within thing:crust") != std::string::npos;
        });
        const std::vector<MapArrival>::const_iterator north = std::find_if(result.arrivals.begin(),
            result.arrivals.end(), [](const MapArrival &arrival) { return arrival.name == "entrance:north"; });
        REQUIRE(north != result.arrivals.end());
        return north->at[2];
    };
    bool warned = false;
    const int beside = arrivalHeight("[90, 50]", 26, "oymap_outdoor_arrival_beside", warned);
    CHECK_FALSE(warned);
    const int over = arrivalHeight("[100, 50]", 26, "oymap_outdoor_arrival_over", warned);
    CHECK(over == beside + 26);
    CHECK_FALSE(warned);
    // Far over the land (a point in the middle of a mound): on its top, and said.
    const int high = arrivalHeight("[100, 50]", 120, "oymap_outdoor_arrival_high", warned);
    CHECK(high == beside + 120);
    CHECK(warned);
}

// ---- Merge point 41: building doors (F2, D-91 §3) and cave mouths (F8, D-91 §2) ----

namespace
{
// The door faces (event 7) of a building read with `pictures`: per face its width across (x: the door looks south)
// and the texels across it.
struct DoorLeafNumbers
{
    double width = 0.0;
    double texels = 0.0;
    std::string texture;
};

std::vector<DoorLeafNumbers> doorLeaves(const std::string &plot, const OutdoorDoorPictures *pPictures,
    std::vector<std::string> &warnings, OutdoorBuildingPlan *pPlan = nullptr)
{
    std::vector<ProjectIssue> issues;
    std::vector<OutdoorBuildingPlan> buildings = readOutdoorBuildings(buildingProject("      - {building: "
        "building:home, at: [40, 40], facing: s, " + plot + "}\n"), "mm7", issues, warnings, pPictures);

    for (const ProjectIssue &issue : issues)
    {
        MESSAGE(issue.path << ": " << issue.message);
    }

    REQUIRE(issues.empty());
    REQUIRE(buildings.size() == 1);
    buildings[0].doors[0].event = 7;
    buildings[0].nameEvent = 8;
    const Game::OutdoorBModel model = raiseOutdoorBuilding(buildings[0]);
    std::vector<DoorLeafNumbers> leaves;

    for (const Game::OutdoorBModelFace &face : model.faces)
    {
        if (face.cogTriggeredNumber != 7)
        {
            continue;
        }

        double low = 1e9;
        double high = -1e9;

        for (const uint16_t vertex : face.vertexIndices)
        {
            low = std::min(low, double(model.vertices[vertex].x));
            high = std::max(high, double(model.vertices[vertex].x));
        }

        const auto [uLow, uHigh] = std::minmax_element(face.textureUs.begin(), face.textureUs.end());
        leaves.push_back({high - low, double(*uHigh - *uLow), face.textureName});
    }

    if (pPlan != nullptr)
    {
        *pPlan = buildings[0];
    }

    return leaves;
}

const char *DoorPictureClasses = "textures:\n"
    "  wingl: {class: feature, door: wing, size: [128, 256], twin: wingr}\n"
    "  wingr: {class: feature, door: wing, size: [128, 256], twin: wingl}\n"
    "  bigdoor: {class: feature, door: single, size: [256, 256]}\n"
    "  plain: {class: tile, size: [128, 128]}\n";
}

TEST_CASE("F2: a door whose picture is a wing becomes a double door on a bay 256 wide")
{
    const OutdoorDoorPictures pictures = parseOutdoorDoorPictures({DoorPictureClasses});
    REQUIRE(pictures.size() == 3);
    CHECK(pictures.at("wingr").twin == "wingl");
    CHECK(pictures.at("bigdoor").size[0] == 256);
    std::vector<std::string> warnings;
    // Without the texture classes: one leaf, as before.
    CHECK(doorLeaves("textures: {door: wingr}", nullptr, warnings).size() == 1);
    // With them: two leaves of 128 on a bay of 256, the left wing (the first twin by name) on both, one mirrored.
    OutdoorBuildingPlan plan;
    const std::vector<DoorLeafNumbers> pair = doorLeaves("textures: {door: wingr}", &pictures, warnings, &plan);
    REQUIRE(pair.size() == 2);

    for (const DoorLeafNumbers &leaf : pair)
    {
        CHECK(leaf.width == doctest::Approx(128.0).epsilon(0.02));
        CHECK(leaf.texels == doctest::Approx(128.0).epsilon(0.02));
        CHECK(leaf.texture == "wingl");
    }

    CHECK(plan.doors[0].leaves == 2);
    CHECK_FALSE(plan.doors[0].leavesGiven);
    // `leaves: 1` keeps the wing alone; a listed bay of 128 too, with a warning.
    CHECK(doorLeaves("textures: {door: wingr}, door: {leaves: 1}", &pictures, warnings).size() == 1);
    warnings.clear();
    CHECK(doorLeaves("textures: {door: wingl}, walls: {s: [post_left, window, wall, door, wall, window, wall, "
              "post_right]}", &pictures, warnings).size() == 1);
    CHECK(anyWarning(warnings, "is one wing of a double door"));
    // `leaves: 2` on a wall whose bays are not listed: a bay of 256 where the door is (before: one bay's 128).
    const std::vector<DoorLeafNumbers> given = doorLeaves("door: {leaves: 2}", &pictures, warnings);
    REQUIRE(given.size() == 2);
    CHECK(given[0].width == doctest::Approx(128.0).epsilon(0.02));
}

TEST_CASE("D-91: each leaf of a pair shows its picture whole at its own width; a doorway's leaves too")
{
    const OutdoorDoorPictures pictures = parseOutdoorDoorPictures({DoorPictureClasses});
    std::vector<std::string> warnings;
    const std::string gate = "textures: {door: bigdoor}, door: {leaves: 2}, parts: [{size: [1024, 512], "
        "walls: {s: [wall, wall, [door, 512], wall, wall]}}]";
    // Known: 256 texels on each 256 leaf (the whole picture, the right one mirrored); unknown: half of it.
    const std::vector<DoorLeafNumbers> whole = doorLeaves(gate, &pictures, warnings);
    const std::vector<DoorLeafNumbers> half = doorLeaves(gate, nullptr, warnings);
    REQUIRE(whole.size() == 2);
    REQUIRE(half.size() == 2);
    CHECK(whole[0].width == doctest::Approx(256.0).epsilon(0.02));
    CHECK(whole[0].texels == doctest::Approx(256.0).epsilon(0.02));
    CHECK(whole[1].texels == doctest::Approx(256.0).epsilon(0.02));
    CHECK(half[0].texels == doctest::Approx(128.0).epsilon(0.02));
    // A 128 wing on a listed bay of 256 with `leaves: 2` stays as it was (the shipped kits' pairs).
    const std::vector<DoorLeafNumbers> wings = doorLeaves("textures: {door: wingl}, door: {leaves: 2}, parts: "
        "[{size: [1024, 512], walls: {s: [wall, wall, wall, [door, 256], wall, wall, wall]}}]", &pictures, warnings);
    const std::vector<DoorLeafNumbers> wingsBefore = doorLeaves("textures: {door: wingl}, door: {leaves: 2}, parts: "
        "[{size: [1024, 512], walls: {s: [wall, wall, wall, [door, 256], wall, wall, wall]}}]", nullptr, warnings);
    REQUIRE(wings.size() == 2);
    REQUIRE(wingsBefore.size() == 2);
    CHECK(wings[0].texels == wingsBefore[0].texels);
    CHECK(wings[1].width == wingsBefore[1].width);
}

TEST_CASE("F8: a cave mouth into a hill: the land rises round its sides and back; its wings and blind mouth warn")
{
    // The default footprint (1024) round a 512 mouth on level land: the shell's wings stand over the land beside.
    const CaveBuild wide = caveBuild("  - {id: thing:cave, kind: cave_mouth, at: [50, 50], into: {map: d49.blv, "
        "at: [0, 0, 0], facing: 0}}\n");
    REQUIRE(wide.issues.empty());
    CHECK(anyWarning(wide.warnings, "caves.wings"));
    CHECK_FALSE(anyWarning(wide.warnings, "caves.dome"));
    CHECK_FALSE(anyWarning(wide.warnings, "caves.blind_mouth"));
    // The land behind it (two rows back) rises to the crest; the front row stays at the floor.
    CHECK(nodeHeight(wide.lowered, 50, 48) >= nodeHeight(wide.lowered, 50, 49));
    CHECK(nodeHeight(wide.lowered, 50, 51) == 640);
    // As wide as its mouth and rim: no wings.
    const CaveBuild narrow = caveBuild("  - {id: thing:cave, kind: cave_mouth, at: [50, 50], size: [640, 1024], "
        "mouth: {rim: 64}, into: {map: d49.blv, at: [0, 0, 0], facing: 0}}\n");
    REQUIRE(narrow.issues.empty());
    CHECK_FALSE(anyWarning(narrow.warnings, "caves.wings"));
    // No `into`: a blind mouth, unless it is a shelter or blocked.
    const CaveBuild blind = caveBuild("  - {id: thing:den, kind: cave_mouth, at: [50, 50]}\n");
    CHECK(anyWarning(blind.warnings, "caves.blind_mouth"));
}

TEST_CASE("D-91: a cave mouth that leads nowhere is a lit shelter or blocked by rubble")
{
    const auto texturesOf = [](const CaveBuild &build, const std::string &id)
    {
        std::map<std::string, size_t> counts;
        const Game::OutdoorBModel *pModel = modelNamed(build.things, id);
        REQUIRE(pModel != nullptr);

        for (const Game::OutdoorBModelFace &face : pModel->faces)
        {
            ++counts[face.textureName];
        }

        return counts;
    };
    const CaveBuild dark = caveBuild("  - {id: thing:den, kind: cave_mouth, at: [50, 50], title: A den}\n");
    const CaveBuild shelter = caveBuild("  - {id: thing:den, kind: cave_mouth, at: [50, 50], form: shelter, title: A "
        "den}\n");
    const CaveBuild blocked = caveBuild("  - {id: thing:adit, kind: cave_mouth, at: [50, 50], form: blocked, title: "
        "The adit, effects: [{text: The adit has fallen in.}]}\n");
    REQUIRE(dark.issues.empty());
    REQUIRE(shelter.issues.empty());
    REQUIRE(blocked.issues.empty());
    // The dark face is gone: the shelter's back and the rubble are the shell's rock.
    CHECK(texturesOf(dark, "thing:den").contains("solid01"));
    CHECK_FALSE(texturesOf(shelter, "thing:den").contains("solid01"));
    CHECK_FALSE(texturesOf(blocked, "thing:adit").contains("solid01"));
    CHECK_FALSE(anyWarning(shelter.warnings, "caves.blind_mouth"));
    CHECK_FALSE(anyWarning(blocked.warnings, "caves.blind_mouth"));
    // A shelter is shallow: its back stands nearer the front than a tunnel's dark face.
    REQUIRE(shelter.lowered.caves.size() == 1);
    CHECK(shelter.lowered.caves[0].mouthDepth < dark.lowered.caves[0].mouthDepth);
    // The rubble's crown stands out before the mouth: the blocked mouth's model reaches further south (forward).
    CHECK(modelNamed(blocked.things, "thing:adit")->faces.size() > 0);
    // Not with a way in.
    const CaveBuild both = caveBuild("  - {id: thing:den, kind: cave_mouth, at: [50, 50], form: shelter, into: {map: "
        "d49.blv, at: [0, 0, 0], facing: 0}}\n");
    CHECK(anyIssue(both.issues, "a cave mouth's `form` is shelter"));
}

TEST_CASE("F28: a gate or a bridge's head whose road tiles are centred off its middle is said in the build")
{
    // A road east to west along row 50 through a wall standing north to south at x 45, and a road north from a
    // bridge's head at y 49 along column 70.
    const auto warnings = [](const std::string &gateAt, const std::string &bridgeX)
    {
        const Project project = buildingProject("      - {building: building:home, at: [40, 40], facing: s}\n",
            "roads:\n  - {link: road:a, line: [[30.5, 50.5], [60.5, 50.5]]}\n"
            "  - {link: road:b, line: [[70.5, 49.5], [70.5, 60.5]]}\n"
            "structures:\n  - {id: thing:wall, kind: wall, line: [[45, 46], [45, 55]], gates: [{at: " + gateAt
            + ", width: 384}]}\n"
            "  - {id: thing:bridge, kind: bridge, line: [[" + bridgeX + ", 45], [" + bridgeX + ", 49]], width: 384}\n");
        LoweredOutdoorMap lowered;
        std::vector<ProjectIssue> issues;
        REQUIRE(lowerOutdoorProject(project, lowered, issues));
        return outdoorRoadOffWarnings(project, lowered);
    };
    CHECK(warnings("[45, 50.5]", "70.5").empty());
    const std::vector<std::string> off = warnings("[45, 50]", "70");
    REQUIRE(off.size() == 2);
    CHECK(off[0].find("gates.road_off: thing:wall gates[0]") == 0);
    // Half a cell (256, to the sampling's step of 15) to the south of the gate's middle.
    const size_t centred = off[0].find("is centred ");
    REQUIRE(centred != std::string::npos);
    CHECK(std::abs(std::stoi(off[0].substr(centred + 11)) - 256) <= 16);
    CHECK(off[1].find("gates.road_off: thing:bridge (its last head)") == 0);
}

TEST_CASE("a decoration stands on its rotated bearing points on the two native terrain triangles")
{
    LoweredOutdoorMap map;
    std::vector<ProjectIssue> issues;
    const Project layout = buildingProject("", "decoration_feet: {arch: [[128, 0, 8], [-128, 0, 0]]}\n");
    REQUIRE(lowerOutdoorProject(layout, map, issues));
    const auto sample = [](int x, int y) { return y * OutdoorNodeCount + x; };
    std::fill(map.samples.begin(), map.samples.end(), 0);
    map.samples[sample(20, 20)] = 0;
    map.samples[sample(21, 20)] = 20;
    map.samples[sample(20, 21)] = 4;
    map.samples[sample(21, 21)] = 8;
    CHECK(map.decorationGroundAt("other", 20.5, 20.5, 0) == doctest::Approx(128));
    CHECK(map.decorationGroundAt("arch", 20.5, 20.5, 0) == doctest::Approx(96));
    // After the turn the foot of the arch at the lower side still stands above the empty space at its middle.
    CHECK(map.decorationGroundAt("arch", 20.5, 20.5, 90) == doctest::Approx(160));
    CHECK(map.decorationGroundAt("arch", 20.5, 20.5, 180) == doctest::Approx(88));
    std::vector<ProjectIssue> invalidIssues;
    CHECK_FALSE(lowerOutdoorProject(buildingProject("", "decoration_feet: {arch: []}\n"), map, invalidIssues));
    CHECK(anyIssue(invalidIssues, "foot offsets"));
}

TEST_CASE("explicit decoration feet meet the rounded terrain across subdivisions and keep level ground")
{
    LoweredOutdoorMap map;
    map.decorationFeet["stone"] = {{0, 0, 0}};
    map.samples.assign(OutdoorNodeCount * OutdoorNodeCount, 10);
    for (int y = 0; y < OutdoorNodeCount; ++y)
    {
        map.samples[y * OutdoorNodeCount + 21] = 18;
        map.samples[y * OutdoorNodeCount + 22] = 42;
    }
    // The ODM stores x=20.43 at cell 20.4296875. The seven-subdivision triangle sits lowest there in this
    // 0, 0, 256, 1024 rise above the plateau. The continuous curve and the four/eight meshes all differ.
    CHECK(map.decorationGroundAt("other", 20.43, 30.25, 0) == doctest::Approx(430.08));
    CHECK(map.decorationGroundAt("stone", 20.43, 30.25, 0) == doctest::Approx(401.6661).epsilon(0.000003));
    CHECK(map.decorationGroundAt("stone", 40.43, 30.25, 0) == doctest::Approx(320));
    CHECK(map.decorationGroundAt("stone", 128, -1, 0) == doctest::Approx(320));
}

// ---- Collision of decorations drawn as 3D models (`collision: model`, 2026-11-24: Xeen's world hull) ----

#include "core/OutdoorDecorationCollision.h"

namespace
{
// A box from (-1, 0, -0.25) to (1, 1, 0.25) in glTF units as a binary glTF: 8 corners, 12 triangles.
void writeBoxGlb(const std::filesystem::path &path, float height = 1.0f)
{
    std::array<float, 24> corners = {-1, 0, -0.25f, 1, 0, -0.25f, 1, 1, -0.25f, -1, 1, -0.25f,
        -1, 0, 0.25f, 1, 0, 0.25f, 1, 1, 0.25f, -1, 1, 0.25f};
    for (size_t i = 1; i < corners.size(); i += 3)
    {
        corners[i] *= height;
    }
    const std::array<uint16_t, 36> indices = {0, 2, 1, 0, 3, 2, 4, 5, 6, 4, 6, 7, 0, 1, 5, 0, 5, 4,
        3, 7, 6, 3, 6, 2, 0, 4, 7, 0, 7, 3, 1, 2, 6, 1, 6, 5};
    std::string binary(reinterpret_cast<const char *>(corners.data()), sizeof(corners));
    binary.append(reinterpret_cast<const char *>(indices.data()), sizeof(indices));
    std::string json = "{\"asset\":{\"version\":\"2.0\"},\"scene\":0,\"scenes\":[{\"nodes\":[0]}],"
        "\"nodes\":[{\"mesh\":0,\"name\":\"box\"}],\"meshes\":[{\"name\":\"box\",\"primitives\":[{\"attributes\":"
        "{\"POSITION\":0},\"indices\":1}]}],\"buffers\":[{\"byteLength\":" + std::to_string(binary.size()) + "}],"
        "\"bufferViews\":[{\"buffer\":0,\"byteOffset\":0,\"byteLength\":96},{\"buffer\":0,\"byteOffset\":96,"
        "\"byteLength\":72}],\"accessors\":[{\"bufferView\":0,\"componentType\":5126,\"count\":8,\"type\":\"VEC3\","
        "\"min\":[-1,0,-0.25],\"max\":[1,1,0.25]},{\"bufferView\":1,\"componentType\":5123,\"count\":36,"
        "\"type\":\"SCALAR\"}]}";
    json.append((4 - json.size() % 4) % 4, ' ');
    const uint32_t total = 12 + 8 + static_cast<uint32_t>(json.size()) + 8 + static_cast<uint32_t>(binary.size());
    std::ofstream out(path, std::ios::binary);
    const auto word = [&out](uint32_t value)
    {
        out.write(reinterpret_cast<const char *>(&value), 4);
    };
    word(0x46546C67u);
    word(2);
    word(total);
    word(static_cast<uint32_t>(json.size()));
    word(0x4E4F534Au);
    out << json;
    word(static_cast<uint32_t>(binary.size()));
    word(0x004E4942u);
    out << binary;
}
}

TEST_CASE("decoration collision: a `collision: model` binding raises the model's hidden triangles where it is drawn")
{
    const std::filesystem::path root = std::filesystem::temp_directory_path() / "oymap_decoration_collision";
    std::filesystem::remove_all(root);
    std::filesystem::create_directories(root / "engine" / "models");
    std::filesystem::create_directories(root / "worlds" / "w" / "models");
    writeBoxGlb(root / "engine" / "models" / "box.glb");
    {
        std::ofstream engine(root / "engine" / "models" / "decorations.yml");
        engine << "decorations:\n  - {name: plate, model: engine/models/box.glb, height: 100, yaw: facing}\n"
                  "  - {name: crate, model: engine/models/box.glb, height: 100, yaw: facing, collision: model}\n";
        std::ofstream world(root / "worlds" / "w" / "models" / "decorations.yml");
        world << "decorations:\n  - {name: plate, model: engine/models/box.glb, height: 100, yaw: facing, "
                 "collision: model}\n";
    }

    std::vector<OutdoorPlacedDecoration> placed(4);
    placed[0].name = "plate";
    placed[1].name = "crate";
    placed[2].name = "crate";
    placed[3].name = "tree";

    for (OutdoorPlacedDecoration &decoration : placed)
    {
        decoration.x = 1000;
        decoration.y = 2000;
        decoration.z = 500;
        decoration.facing = 90;
    }

    std::vector<std::string> warnings;
    const std::vector<Game::OutdoorBModel> models = raiseDecorationCollision(root, "w", "m",
        placed, {"thing:plate", "thing:crate", "thing:hidden_crate", "thing:tree"}, {false, false, true, false},
        warnings);
    // The world's plate (its entry replaces the engine's) and the shown crate; not the hidden one, not the tree.
    REQUIRE(models.size() == 2);
    CHECK(warnings.empty());
    CHECK(models[0].name == "collision:thing:plate");
    CHECK(models[0].faces.size() == 12);

    for (const Game::OutdoorBModelFace &face : models[0].faces)
    {
        CHECK(Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::Invisible));
    }

    // 100 high (the binding's height over the model's 1), turned by its facing (90): the model's 2-wide x runs
    // along the map's y, its 0.5-deep z along x.
    CHECK(models[0].minZ == 500);
    CHECK(models[0].maxZ == 600);
    CHECK(models[0].maxX - models[0].minX == 50);
    CHECK(models[0].maxY - models[0].minY == 200);
    CHECK(models[0].minY == 1900);
    std::filesystem::remove_all(root);
}

TEST_CASE("static decoration model proxies use the visual scale and opt only permanent scatter into collision")
{
    const auto root = std::filesystem::temp_directory_path() / "oymap_test_collision_proxy";
    std::filesystem::create_directories(root / "worlds/w/models");
    writeBoxGlb(root / "worlds/w/models/show.glb");
    writeBoxGlb(root / "worlds/w/models/body.glb", 0.5f);
    const std::string row = "{name: rock, model: worlds/w/models/show.glb, height: 100, yaw: facing, collision: model, "
        "collision_model: worlds/w/models/body.glb";
    {
        std::ofstream outdoor(root / "worlds/w/models/decorations.yml");
        outdoor << "decorations:\n  - " << row << ", collision_scatter: true}\n"
            "  - {name: plant, model: worlds/w/models/show.glb, height: 100, collision: model}\n";
        std::ofstream indoor(root / "worlds/w/models/indoor_decorations.yml");
        indoor << "decorations:\n  - " << row << ", maps: [room.blv]}\n";
    }
    std::vector<std::string> warnings;
    OutdoorPlacedDecoration rock;
    rock.name = "rock";
    OutdoorPlacedDecoration plant;
    plant.name = "plant";
    const auto models = raiseDecorationCollision(root, "w", "out", {}, {}, {}, warnings, {rock, plant});
    REQUIRE(models.size() == 1);
    CHECK(models[0].maxZ == 50);
    DecorationCollisionModels room(root, "w", "room", true);
    const auto vertices = room.place("rock", 0, 0, 10, 0, false, warnings);
    REQUIRE(vertices.size() == 36);
    CHECK(std::max_element(vertices.begin(), vertices.end(), [](const auto &a, const auto &b)
        { return a[2] < b[2]; })->at(2) == 60);
    DecorationCollisionModels elsewhere(root, "w", "other", true);
    CHECK(elsewhere.place("rock", 0, 0, 0, 0, false, warnings).empty());
    CHECK(warnings.empty());
    std::filesystem::remove_all(root);
}

TEST_CASE("decoration collision: `collision_model: lod` raises the coarsest LOD, placed by the base mesh's height")
{
    const auto root = std::filesystem::temp_directory_path() / "oymap_test_collision_lod";
    std::filesystem::remove_all(root);
    std::filesystem::create_directories(root / "worlds/w/models");
    {
        // Mesh 0 (the node's): the box 1 high, its extras naming LODs 1 and 2; mesh 2 (the coarsest): the lower half
        // of the box's front face, two triangles.
        std::array<float, 24> corners = {-1, 0, -0.25f, 1, 0, -0.25f, 1, 1, -0.25f, -1, 1, -0.25f,
            -1, 0, 0.25f, 1, 0, 0.25f, 1, 1, 0.25f, -1, 1, 0.25f};
        const std::array<float, 12> card = {-1, 0, 0, 1, 0, 0, 1, 0.5f, 0, -1, 0.5f, 0};
        const std::array<uint16_t, 36> indices = {0, 2, 1, 0, 3, 2, 4, 5, 6, 4, 6, 7, 0, 1, 5, 0, 5, 4,
            3, 7, 6, 3, 6, 2, 0, 4, 7, 0, 7, 3, 1, 2, 6, 1, 6, 5};
        std::string binary(reinterpret_cast<const char *>(corners.data()), sizeof(corners));
        binary.append(reinterpret_cast<const char *>(card.data()), sizeof(card));
        binary.append(reinterpret_cast<const char *>(indices.data()), sizeof(indices));
        std::string json = "{\"asset\":{\"version\":\"2.0\"},\"scene\":0,\"scenes\":[{\"nodes\":[0]}],"
            "\"nodes\":[{\"mesh\":0,\"name\":\"rock\"}],\"meshes\":["
            "{\"name\":\"rock\",\"extras\":{\"openyamm_lods\":[1,2]},\"primitives\":[{\"attributes\":"
            "{\"POSITION\":0},\"indices\":2}]},"
            "{\"name\":\"rock_lod1\",\"primitives\":[{\"attributes\":{\"POSITION\":0},\"indices\":2}]},"
            "{\"name\":\"rock_lod2\",\"primitives\":[{\"attributes\":{\"POSITION\":1},\"indices\":3}]}],"
            "\"buffers\":[{\"byteLength\":" + std::to_string(binary.size()) + "}],"
            "\"bufferViews\":[{\"buffer\":0,\"byteOffset\":0,\"byteLength\":96},{\"buffer\":0,\"byteOffset\":96,"
            "\"byteLength\":48},{\"buffer\":0,\"byteOffset\":144,\"byteLength\":72}],"
            "\"accessors\":[{\"bufferView\":0,\"componentType\":5126,\"count\":8,\"type\":\"VEC3\","
            "\"min\":[-1,0,-0.25],\"max\":[1,1,0.25]},{\"bufferView\":1,\"componentType\":5126,\"count\":4,"
            "\"type\":\"VEC3\",\"min\":[-1,0,0],\"max\":[1,0.5,0]},{\"bufferView\":2,\"componentType\":5123,"
            "\"count\":36,\"type\":\"SCALAR\"},{\"bufferView\":2,\"componentType\":5123,\"count\":6,"
            "\"type\":\"SCALAR\"}]}";
        json.append((4 - json.size() % 4) % 4, ' ');
        const uint32_t total = 12 + 8 + uint32_t(json.size()) + 8 + uint32_t(binary.size());
        std::ofstream out(root / "worlds/w/models/rock.glb", std::ios::binary);
        const auto word = [&out](uint32_t value)
        {
            out.write(reinterpret_cast<const char *>(&value), 4);
        };
        word(0x46546C67u);
        word(2);
        word(total);
        word(uint32_t(json.size()));
        word(0x4E4F534Au);
        out << json;
        word(uint32_t(binary.size()));
        word(0x004E4942u);
        out << binary;
    }
    writeBoxGlb(root / "worlds/w/models/hull.glb");
    {
        std::ofstream outdoor(root / "worlds/w/models/decorations.yml");
        outdoor << "decorations:\n"
            "  - {name: rock, model: worlds/w/models/rock.glb, height: 100, yaw: facing, collision: model, "
            "collision_model: lod, collision_scatter: true}\n"
            "  - {name: hull, model: worlds/w/models/hull.glb, height: 100, yaw: facing, collision: model, "
            "collision_model: lod}\n";
    }
    OutdoorPlacedDecoration rock;
    rock.name = "rock";
    rock.z = 10;
    OutdoorPlacedDecoration hull;
    hull.name = "hull";
    std::vector<std::string> warnings;
    // The scattered rock (it asks for collision_scatter) and the hull structure, which has no LODs: its whole box.
    const auto models = raiseDecorationCollision(root, "w", "out", {hull}, {"thing:hull"}, {false}, warnings, {rock});
    CHECK(warnings.empty());
    REQUIRE(models.size() == 2);
    CHECK(models[0].name == "collision:thing:hull");
    CHECK(models[0].faces.size() == 12);
    CHECK(models[0].maxZ == 100);
    CHECK(models[1].name == "collision:scatter_0");
    // The coarsest LOD's two triangles, scaled by the base mesh's height 1 (100 world units per unit): 50 high.
    CHECK(models[1].faces.size() == 2);
    CHECK(models[1].minZ == 10);
    CHECK(models[1].maxZ == 60);
    std::filesystem::remove_all(root);
}

#include "core/MapLoad.h"
#include "game/outdoor/OutdoorGeometryUtils.h"

TEST_CASE("void audit: a hull decoration's hidden collision over the void is no finding, another model is")
{
    LoadedMap map;
    map.outdoor = Game::OutdoorMapData{};
    map.outdoor->voidCells.assign(size_t(Game::OutdoorMapData::TerrainWidth) * Game::OutdoorMapData::TerrainHeight, 0);
    // The cell holding the map's middle is void.
    const int cellX = static_cast<int>(std::floor(Game::outdoorWorldToGridXFloat(0.0f)));
    const int cellY = static_cast<int>(std::floor(Game::outdoorWorldToGridYFloat(0.0f)));
    map.outdoor->voidCells[size_t(cellY) * Game::OutdoorMapData::TerrainWidth + size_t(cellX)] = 1;
    const auto modelAt = [](const std::string &name)
    {
        Game::OutdoorBModel model;
        model.name = name;
        model.minX = -100;
        model.maxX = 100;
        model.minY = -100;
        model.maxY = 100;
        return model;
    };
    map.outdoor->bmodels = {modelAt("collision:thing:hull_001"), modelAt("thing:crate")};
    Game::OutdoorEntity hull;
    hull.name = "xeen_hull4";
    map.outdoor->entities = {hull};
    const std::vector<AuditFinding> findings = auditVoid(map);
    REQUIRE(findings.size() == 1);
    CHECK(findings[0].message.find("thing:crate") != std::string::npos);
}

namespace
{
// D-170: every level upward face of a model stands 4 or more over the land under it or lies 8 or more under it.
size_t facesOnLand(const Game::OutdoorBModel &model, const LoweredOutdoorMap &lowered)
{
    size_t found = 0;

    for (const Game::OutdoorBModelFace &face : model.faces)
    {
        if (face.planeNormalZ < 65470 || face.vertexIndices.size() < 3)
        {
            continue;
        }

        std::vector<std::array<double, 2>> outline;
        double z = 0.0;

        for (const uint16_t index : face.vertexIndices)
        {
            outline.push_back({double(model.vertices[index].x), double(model.vertices[index].y)});
            z += model.vertices[index].z;
        }

        z /= static_cast<double>(face.vertexIndices.size());
        const std::array<double, 2> land = lowered.groundRangeUnder(outline);
        found += land[1] > z - 4.0 + 0.5 && land[0] < z + 8.0 - 0.5 ? 1 : 0;
    }

    return found;
}

// The project of `thingsOf` lowered, its land then changed by `shape`, and its structures raised.
OutdoorThings thingsOnLand(const std::string &more, LoweredOutdoorMap &lowered,
    const std::function<void(LoweredOutdoorMap &)> &shape)
{
    const Project project = buildingProject("      - {building: building:home, at: [40, 40], facing: s}\n", more);
    std::vector<ProjectIssue> issues;
    REQUIRE(lowerOutdoorProject(project, lowered, issues));
    shape(lowered);
    IdsLock ids;
    OutdoorThings things;
    std::vector<std::string> warnings;
    OutdoorEventWords words(project, {}, ids, issues);
    raiseOutdoorThings(project, lowered, {}, ids, words, things, issues, warnings);
    REQUIRE(issues.empty());
    return things;
}
}

TEST_CASE("D-170: the land under a sample range: corners, crossings and nodes inside; the rule over or under it")
{
    LoweredOutdoorMap lowered = loweredOf(LevelLand);
    // A node at (64, 64), world (0, 0), raised 64 over the level 640.
    lowered.samples[static_cast<size_t>(64) * OutdoorNodeCount + 64] += 2;
    const std::array<double, 2> around = lowered.groundRangeUnder({{-256, -256}, {256, -256}, {256, 256}, {-256, 256}});
    CHECK(around[0] == doctest::Approx(640.0));
    CHECK(around[1] == doctest::Approx(704.0));
    // A face at 660 over it is lifted 4 over its highest land; one at 600 under the level land stays.
    CHECK(outdoorClearOfLand(lowered, {{-256, -256}, {256, -256}, {256, 256}, {-256, 256}}, 660.0)
        == doctest::Approx(708.0));
    CHECK(outdoorClearOfLand(lowered, {{-256, -256}, {256, -256}, {256, 256}, {-256, 256}}, 632.0)
        == doctest::Approx(632.0));
    CHECK(outdoorClearOfLand(lowered, {{1024, 1024}, {1280, 1024}, {1280, 1280}}, 648.0) == doctest::Approx(648.0));
    // Kept under a limit, it lies 8 under the lowest land instead.
    CHECK(outdoorClearOfLand(lowered, {{-256, -256}, {256, -256}, {256, 256}, {-256, 256}}, 660.0, 690.0)
        == doctest::Approx(632.0));
}

TEST_CASE("D-170: a porch's slab stands 4 over the land that rises to it beyond the plot")
{
    const Project project = buildingProject("      - {building: building:home, at: [40, 40], facing: s, "
        "parts: [{id: body, at: [64, 64], size: [896, 512], porches: [{wall: s, depth: 128, height: 224, posts: 24, "
        "floor: 16}]}]}\n");
    LoweredOutdoorMap lowered;
    std::vector<ProjectIssue> issues;
    REQUIRE(lowerOutdoorProject(project, lowered, issues));
    REQUIRE(lowered.buildings.size() == 1);
    // The land beyond the levelled plot rises south of it (row 42 at 704): under the porch (rows 41.125 to 41.375)
    // from 648 to 664, through the slab at 656 (the floor 640 and 16).
    for (int x = 36; x <= 44; ++x)
    {
        lowered.samples[static_cast<size_t>(42) * OutdoorNodeCount + x] = 22;
    }

    const Game::OutdoorBModel unclear = raiseOutdoorBuilding(lowered.buildings[0]);
    CHECK(facesOnLand(unclear, lowered) > 0);
    const Game::OutdoorBModel house = raiseOutdoorBuilding(lowered.buildings[0], nullptr, &lowered);
    CHECK(facesOnLand(house, lowered) == 0);
    CHECK(house.faces.size() == unclear.faces.size());
}

TEST_CASE("D-170: a tread the hillside reaches stands 4 over it or lies 8 under it")
{
    LoweredOutdoorMap lowered;
    const OutdoorThings things = thingsOnLand("structures:\n"
        "  - {id: thing:flight, kind: stairs, line: [[50, 50], [52, 50]], rise: 256, tread: 32, width: 256}\n",
        lowered, [](LoweredOutdoorMap &land)
    {
        // The hill climbs with the flight, its top flush with the last tread (896).
        for (int y = 49; y <= 51; ++y)
        {
            land.samples[static_cast<size_t>(y) * OutdoorNodeCount + 51] = 24;
            land.samples[static_cast<size_t>(y) * OutdoorNodeCount + 52] = 28;
            land.samples[static_cast<size_t>(y) * OutdoorNodeCount + 53] = 28;
        }
    });
    REQUIRE(things.models.size() == 1);
    CHECK(facesOnLand(things.models[0], lowered) == 0);
    CHECK(things.models[0].maxZ <= 896 + 32);
}

TEST_CASE("D-170: a gate's leaves make no end faces against the gate's cheeks or each other; a free end keeps one")
{
    LoweredOutdoorMap lowered;
    const OutdoorThings things = thingsOnLand("structures:\n"
        "  - {id: thing:gatehouse, kind: wall, line: [[48, 50], [50.4, 50]], height: 448, thickness: 192, "
        "gates: [{at: [49.2, 50], width: 256, height: 320}]}\n"
        "  - {id: thing:leaf_l, kind: wall, line: [[48.95, 50.1], [49.2, 50.1]], height: 256, thickness: 32}\n"
        "  - {id: thing:leaf_r, kind: wall, line: [[49.2, 50.1], [49.45, 50.1]], height: 256, thickness: 32}\n"
        "  - {id: thing:free, kind: wall, line: [[55, 50], [55.5, 50]], height: 256, thickness: 32}\n",
        lowered, [](LoweredOutdoorMap &) {});
    REQUIRE(things.models.size() == 4);
    const auto ends = [](const Game::OutdoorBModel &model)
    {
        return std::count_if(model.faces.begin(), model.faces.end(), [](const Game::OutdoorBModelFace &face)
        {
            return std::abs(face.planeNormalX) > 65000;
        });
    };
    CHECK(things.models[1].name == "thing:leaf_l");
    CHECK(ends(things.models[1]) == 0);
    CHECK(ends(things.models[2]) == 0);
    CHECK(ends(things.models[3]) == 2);
}
