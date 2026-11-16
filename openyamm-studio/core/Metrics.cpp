#include "core/Metrics.h"

#include "core/CoreMath.h"
#include "core/Reachability.h"

#include "game/FaceEnums.h"

#include <algorithm>
#include <cmath>
#include <map>
#include <regex>
#include <set>
#include <sstream>

namespace OpenYAMM::Studio
{
namespace
{
// BLV face attribute bits (game/FaceEnums.h values, as the census scripts read them).
constexpr uint32_t AttributeSecret = 0x2;
constexpr uint32_t AttributeClickable = 0x02000000;
constexpr uint32_t AttributePressurePlate = 0x04000000;
// A spawn of type 3 is a monster.
constexpr uint16_t SpawnTypeMonster = 3;

struct Spread
{
    double minimum = 0.0;
    double lowerQuartile = 0.0;
    double median = 0.0;
    double upperQuartile = 0.0;
    double maximum = 0.0;
    size_t count = 0;
};

Spread spreadOf(std::vector<double> values)
{
    Spread spread;
    spread.count = values.size();

    if (values.empty())
    {
        return spread;
    }

    std::sort(values.begin(), values.end());
    const auto at = [&values](double share)
    {
        return values[static_cast<size_t>(std::floor(share * static_cast<double>(values.size() - 1) + 0.5))];
    };
    spread.minimum = values.front();
    spread.lowerQuartile = at(0.25);
    spread.median = at(0.5);
    spread.upperQuartile = at(0.75);
    spread.maximum = values.back();
    return spread;
}

void writeSpread(JsonWriter &writer, std::string_view name, const Spread &spread)
{
    writer.key(name);
    writer.beginObject();
    writer.field("count", static_cast<uint64_t>(spread.count));
    writer.field("min", std::round(spread.minimum));
    writer.field("q1", std::round(spread.lowerQuartile));
    writer.field("median", std::round(spread.median));
    writer.field("q3", std::round(spread.upperQuartile));
    writer.field("max", std::round(spread.maximum));
    writer.endObject();
}

std::string lowerCopy(std::string text)
{
    std::transform(text.begin(), text.end(), text.begin(), [](unsigned char character)
    {
        return static_cast<char>(std::tolower(character));
    });
    return text;
}

// The script cut into its handlers: event number to the text from its RegisterEvent line to the next.
std::map<int, std::string> handlerBlocks(const std::string &script)
{
    std::map<int, std::string> blocks;
    const std::regex registration("(^|\\n)Register(?:NoOp)?Event\\((\\d+),");
    std::vector<std::pair<size_t, int>> starts;

    for (std::sregex_iterator match(script.begin(), script.end(), registration); match != std::sregex_iterator();
         ++match)
    {
        starts.emplace_back(static_cast<size_t>(match->position(0)), std::stoi((*match)[2].str()));
    }

    for (size_t index = 0; index < starts.size(); ++index)
    {
        const size_t end = index + 1 < starts.size() ? starts[index + 1].first : script.size();
        blocks[starts[index].second] += script.substr(starts[index].first, end - starts[index].first);
    }

    return blocks;
}

struct EventKinds
{
    size_t door = 0;
    size_t trap = 0;
    size_t localTeleport = 0;
    size_t exit = 0;
    size_t summon = 0;
    size_t chest = 0;
    size_t text = 0;
};

EventKinds classifyBoundEvents(const LoadedMap &map, const std::set<int> &boundEvents)
{
    EventKinds kinds;
    const std::map<int, std::string> blocks = handlerBlocks(map.scriptText);
    const std::regex otherMap("MoveToMap\\([^)]*\"([^\"]+\\.(?:blv|odm))\"", std::regex::icase);

    for (const int eventId : boundEvents)
    {
        const std::map<int, std::string>::const_iterator block = blocks.find(eventId);

        if (block == blocks.end())
        {
            continue;
        }

        const std::string &text = block->second;
        kinds.door += text.find("evt.SetDoorState") != std::string::npos ? 1 : 0;
        kinds.trap += (text.find("evt.DamagePlayer(") != std::string::npos
                          || text.find("evt.CastSpell(") != std::string::npos)
            ? 1 : 0;
        kinds.summon += text.find("SummonMonsters") != std::string::npos ? 1 : 0;
        kinds.chest += text.find("evt.OpenChest(") != std::string::npos ? 1 : 0;
        kinds.text += text.find("evt.StatusText(") != std::string::npos ? 1 : 0;

        if (text.find("evt.MoveToMap(") != std::string::npos)
        {
            std::smatch target;
            const bool namesMap = std::regex_search(text, target, otherMap);

            if (!namesMap || lowerCopy(target[1].str()) == map.fileName)
            {
                ++kinds.localTeleport;
            }
            else
            {
                ++kinds.exit;
            }
        }
    }

    return kinds;
}

void writeTopNames(
    JsonWriter &writer, std::string_view name, const std::map<std::string, double> &weights, size_t limit)
{
    std::vector<std::pair<std::string, double>> ordered(weights.begin(), weights.end());
    std::stable_sort(ordered.begin(), ordered.end(), [](const auto &left, const auto &right)
    {
        return left.second > right.second;
    });
    double total = 0.0;

    for (const std::pair<std::string, double> &entry : ordered)
    {
        total += entry.second;
    }

    writer.key(name);
    writer.beginArray();

    for (size_t index = 0; index < ordered.size() && index < limit; ++index)
    {
        writer.beginObject();
        writer.field("name", ordered[index].first);
        writer.field("share", total > 0.0 ? std::round(ordered[index].second / total * 1000.0) / 1000.0 : 0.0);
        writer.endObject();
    }

    writer.endArray();
}

// How many of the map's decorations carry a light: those whose row of decoration_data.txt (by number, else by
// internal name) has a LightRadius above 0. Rows are tab-separated: number, InternalName, Hint, Type, Radius, Height,
// LightRadius.
size_t lightCarryingDecorations(const Game::IndoorMapData &indoor, const std::string &tableText)
{
    std::map<int, bool> litById;
    std::map<std::string, bool> litByName;
    std::istringstream lines(tableText);

    for (std::string line; std::getline(lines, line);)
    {
        std::vector<std::string> cells;
        std::istringstream cellStream(line);

        for (std::string cell; std::getline(cellStream, cell, '\t');)
        {
            cells.push_back(cell);
        }

        if (cells.size() < 7 || cells[0].empty() || cells[0].find_first_not_of("0123456789") != std::string::npos
            || cells[6].empty() || cells[6].find_first_not_of("0123456789") != std::string::npos)
        {
            continue;
        }

        // (A map names a row by its place in the list, which begins at 0: one less than the table's number.)
        const bool lit = std::stoi(cells[6]) > 0;
        litById[std::stoi(cells[0]) - 1] = lit;
        litByName[lowerCopy(cells[1])] = lit;
    }

    size_t count = 0;

    for (const Game::IndoorEntity &entity : indoor.entities)
    {
        // A shipped map's decoration bears the row's name; a built one its own id and the row's place.
        const std::map<std::string, bool>::const_iterator byName = litByName.find(lowerCopy(entity.name));
        const std::map<int, bool>::const_iterator byId = litById.find(entity.decorationListId);
        count += (byName != litByName.end() ? byName->second : byId != litById.end() && byId->second) ? 1 : 0;
    }

    return count;
}

void writeIndoor(const LoadedMap &map, const MetricsOptions &options, JsonWriter &writer)
{
    const Game::IndoorMapData &indoor = *map.indoor;
    std::set<size_t> occupied;
    std::set<std::pair<size_t, size_t>> links;
    std::vector<double> portalWidths;
    std::vector<double> portalHeights;
    std::map<std::string, double> textureAreas;
    std::map<size_t, double> floorAreaBySector;
    std::vector<double> floorLevels;
    std::set<int> boundEvents;
    size_t secretFaces = 0;
    size_t plates = 0;
    size_t clickable = 0;
    double floorArea = 0.0;

    for (const Game::IndoorFace &face : indoor.faces)
    {
        if (face.roomNumber != 0)
        {
            occupied.insert(face.roomNumber);
        }

        if (face.cogTriggered != 0)
        {
            boundEvents.insert(face.cogTriggered);
        }

        secretFaces += (face.attributes & AttributeSecret) != 0 ? 1 : 0;
        plates += (face.attributes & AttributePressurePlate) != 0 ? 1 : 0;
        clickable += (face.attributes & AttributeClickable) != 0 ? 1 : 0;

        if (face.vertexIndices.size() < 3)
        {
            continue;
        }

        // The face's extent and its area (Newell).
        double minX = 1.0e9;
        double maxX = -1.0e9;
        double minY = 1.0e9;
        double maxY = -1.0e9;
        double minZ = 1.0e9;
        double maxZ = -1.0e9;
        double normalX = 0.0;
        double normalY = 0.0;
        double normalZ = 0.0;

        for (size_t index = 0; index < face.vertexIndices.size(); ++index)
        {
            const Game::IndoorVertex &current = indoor.vertices[face.vertexIndices[index]];
            const Game::IndoorVertex &next =
                indoor.vertices[face.vertexIndices[(index + 1) % face.vertexIndices.size()]];
            minX = std::min(minX, static_cast<double>(current.x));
            maxX = std::max(maxX, static_cast<double>(current.x));
            minY = std::min(minY, static_cast<double>(current.y));
            maxY = std::max(maxY, static_cast<double>(current.y));
            minZ = std::min(minZ, static_cast<double>(current.z));
            maxZ = std::max(maxZ, static_cast<double>(current.z));
            normalX += (static_cast<double>(current.y) - next.y) * (static_cast<double>(current.z) + next.z);
            normalY += (static_cast<double>(current.z) - next.z) * (static_cast<double>(current.x) + next.x);
            normalZ += (static_cast<double>(current.x) - next.x) * (static_cast<double>(current.y) + next.y);
        }

        const double area = std::sqrt(normalX * normalX + normalY * normalY + normalZ * normalZ) / 2.0;

        if (face.isPortal)
        {
            if (face.roomNumber != 0 && face.roomBehindNumber != 0 && face.roomNumber != face.roomBehindNumber)
            {
                links.insert({std::min<size_t>(face.roomNumber, face.roomBehindNumber),
                    std::max<size_t>(face.roomNumber, face.roomBehindNumber)});
            }

            // An upright portal is a doorway: its width along the wall and its height.
            if (maxZ - minZ > 32.0)
            {
                portalWidths.push_back(oy::hypot(maxX - minX, maxY - minY));
                portalHeights.push_back(maxZ - minZ);
            }

            continue;
        }

        textureAreas[lowerCopy(face.textureName)] += area;

        // Floors: facing up.
        if (area > 0.0 && normalZ / (2.0 * area) > 0.7)
        {
            floorArea += std::abs(normalZ) / 2.0;
            floorAreaBySector[face.roomNumber] += std::abs(normalZ) / 2.0;
            floorLevels.push_back(minZ);
        }
    }

    for (const Game::IndoorEntity &entity : indoor.entities)
    {
        if (entity.scriptEventId() != 0)
        {
            boundEvents.insert(entity.scriptEventId());
        }
    }

    // Components and loops of the room graph.
    std::map<size_t, size_t> parent;

    for (const size_t sector : occupied)
    {
        parent[sector] = sector;
    }

    const auto find = [&parent](size_t sector)
    {
        while (parent[sector] != sector)
        {
            parent[sector] = parent[parent[sector]];
            sector = parent[sector];
        }

        return sector;
    };

    for (const std::pair<size_t, size_t> &link : links)
    {
        if (parent.contains(link.first) && parent.contains(link.second))
        {
            parent[find(link.first)] = find(link.second);
        }
    }

    std::set<size_t> roots;

    for (const size_t sector : occupied)
    {
        roots.insert(find(sector));
    }

    std::vector<double> sectorAreas;
    std::vector<double> sectorHeights;

    for (const std::pair<const size_t, double> &entry : floorAreaBySector)
    {
        sectorAreas.push_back(entry.second);

        if (entry.first < indoor.sectors.size())
        {
            sectorHeights.push_back(indoor.sectors[entry.first].maxZ - indoor.sectors[entry.first].minZ);
        }
    }

    size_t monsterSpawns = 0;

    for (const Game::IndoorSpawn &spawn : indoor.spawns)
    {
        monsterSpawns += spawn.typeId == SpawnTypeMonster ? 1 : 0;
    }

    size_t fixedActors = 0;
    size_t uniqueActors = 0;
    size_t doors = 0;

    if (map.state)
    {
        fixedActors = map.state->actors.size();
        doors = map.state->doors.size();

        for (const Game::MapDeltaActor &actor : map.state->actors)
        {
            uniqueActors += actor.uniqueNameIndex != 0 ? 1 : 0;
        }
    }

    const EventKinds kinds = classifyBoundEvents(map, boundEvents);
    const double millionUnits = floorArea / 1.0e6;
    const auto perArea = [millionUnits](size_t count)
    {
        return millionUnits > 0.0 ? std::round(static_cast<double>(count) / millionUnits * 100.0) / 100.0 : 0.0;
    };

    writer.key("structure");
    writer.beginObject();
    writer.field("sectors", static_cast<uint64_t>(occupied.size()));
    writer.field("links", static_cast<uint64_t>(links.size()));
    writer.field("components", static_cast<uint64_t>(roots.size()));
    // Independent rings in the room graph.
    writer.field("loops", static_cast<int64_t>(links.size()) - static_cast<int64_t>(occupied.size())
        + static_cast<int64_t>(roots.size()));
    writer.endObject();

    writer.key("scale");
    writer.beginObject();
    writer.field("floor_area_millions", std::round(millionUnits * 100.0) / 100.0);
    writeSpread(writer, "sector_floor_area", spreadOf(sectorAreas));
    writeSpread(writer, "sector_height", spreadOf(sectorHeights));
    writeSpread(writer, "doorway_width", spreadOf(portalWidths));
    writeSpread(writer, "doorway_height", spreadOf(portalHeights));
    writeSpread(writer, "floor_level", spreadOf(floorLevels));
    writer.endObject();

    writer.key("mechanisms");
    writer.beginObject();
    writer.field("doors", static_cast<uint64_t>(doors));
    writer.field("bound_events", static_cast<uint64_t>(boundEvents.size()));
    writer.field("door_events", static_cast<uint64_t>(kinds.door));
    writer.field("trap_events", static_cast<uint64_t>(kinds.trap));
    writer.field("local_teleports", static_cast<uint64_t>(kinds.localTeleport));
    writer.field("exits", static_cast<uint64_t>(kinds.exit));
    writer.field("summon_events", static_cast<uint64_t>(kinds.summon));
    writer.field("chest_events", static_cast<uint64_t>(kinds.chest));
    writer.field("text_events", static_cast<uint64_t>(kinds.text));
    writer.field("secret_faces", static_cast<uint64_t>(secretFaces));
    writer.field("pressure_plates", static_cast<uint64_t>(plates));
    writer.field("clickable_faces", static_cast<uint64_t>(clickable));
    writer.endObject();

    writer.key("density");
    writer.beginObject();
    writer.field("spawn_points", static_cast<uint64_t>(monsterSpawns));
    writer.field("fixed_actors", static_cast<uint64_t>(fixedActors));
    writer.field("unique_actors", static_cast<uint64_t>(uniqueActors));
    writer.field("lights", static_cast<uint64_t>(indoor.lights.size()));
    writer.field("decorations", static_cast<uint64_t>(indoor.entities.size()));
    // Decorations whose row of the decoration table has a light radius (a wall torch, a brazier): the game lights
    // them without a light record of the map. With the map's own lights they are its light sources.
    const size_t decorationLights = lightCarryingDecorations(indoor, options.decorationTableText);
    writer.field("decoration_lights", static_cast<uint64_t>(decorationLights));
    writer.field("light_sources", static_cast<uint64_t>(indoor.lights.size() + decorationLights));
    // Per million square units of floor.
    writer.field("spawn_points_per_area", perArea(monsterSpawns));
    writer.field("lights_per_area", perArea(indoor.lights.size()));
    writer.field("light_sources_per_area", perArea(indoor.lights.size() + decorationLights));
    writer.field("decorations_per_area", perArea(indoor.entities.size()));
    writer.endObject();

    writer.key("palette");
    writer.beginObject();
    writer.field("textures", static_cast<uint64_t>(textureAreas.size()));
    writeTopNames(writer, "by_area", textureAreas, 12);
    writer.endObject();

    if (options.withReachability)
    {
        const ReachabilityResult reach = checkReachability(map);
        writer.key("play");
        writer.beginObject();
        writer.field("walked", reach.ran);

        if (reach.ran)
        {
            writer.field("sectors_with_floor", static_cast<uint64_t>(reach.sectorsWithFloor));
            writer.field("reached_at_start", static_cast<uint64_t>(reach.reachedAtStart));
            writer.field("reached_doors_clear", static_cast<uint64_t>(reach.reachedDoorsOpen));
            // One flood cell is 32 by 32 units.
            writer.field("walkable_area_millions",
                std::round(static_cast<double>(reach.cellsWalked) * 1024.0 / 1.0e6 * 100.0) / 100.0);
            writer.field("unreached_spawn_points", static_cast<uint64_t>(reach.unreachableSpawns.size()));
        }

        writer.endObject();
    }
}

void writeOutdoor(const LoadedMap &map, JsonWriter &writer)
{
    const Game::OutdoorMapData &outdoor = *map.outdoor;
    std::vector<double> footprints;
    std::vector<double> heights;
    std::vector<std::array<double, 2>> centres;
    std::map<std::string, double> textureFaces;
    std::set<int> boundEvents;
    size_t faces = 0;

    for (const Game::OutdoorBModel &bmodel : outdoor.bmodels)
    {
        if (bmodel.vertices.empty())
        {
            continue;
        }

        double minX = 1.0e9;
        double maxX = -1.0e9;
        double minY = 1.0e9;
        double maxY = -1.0e9;
        double minZ = 1.0e9;
        double maxZ = -1.0e9;

        for (const Game::OutdoorBModelVertex &vertex : bmodel.vertices)
        {
            minX = std::min(minX, static_cast<double>(vertex.x));
            maxX = std::max(maxX, static_cast<double>(vertex.x));
            minY = std::min(minY, static_cast<double>(vertex.y));
            maxY = std::max(maxY, static_cast<double>(vertex.y));
            minZ = std::min(minZ, static_cast<double>(vertex.z));
            maxZ = std::max(maxZ, static_cast<double>(vertex.z));
        }

        footprints.push_back((maxX - minX) * (maxY - minY));
        heights.push_back(maxZ - minZ);
        centres.push_back({(minX + maxX) / 2.0, (minY + maxY) / 2.0});

        for (const Game::OutdoorBModelFace &face : bmodel.faces)
        {
            ++faces;
            textureFaces[lowerCopy(face.textureName)] += 1.0;

            if (face.cogTriggeredNumber != 0)
            {
                boundEvents.insert(face.cogTriggeredNumber);
            }
        }
    }

    // Gap from each building's centre to its nearest neighbour's.
    std::vector<double> gaps;

    for (size_t index = 0; index < centres.size(); ++index)
    {
        double nearest = 1.0e18;

        for (size_t other = 0; other < centres.size(); ++other)
        {
            if (other != index)
            {
                nearest = std::min(nearest, oy::hypot(centres[index][0] - centres[other][0],
                    centres[index][1] - centres[other][1]));
            }
        }

        if (centres.size() > 1)
        {
            gaps.push_back(nearest);
        }
    }

    std::map<std::string, double> decorationNames;

    for (const Game::OutdoorEntity &entity : outdoor.entities)
    {
        decorationNames[lowerCopy(entity.name)] += 1.0;

        if (entity.scriptEventId() != 0)
        {
            boundEvents.insert(entity.scriptEventId());
        }
    }

    size_t monsterSpawns = 0;

    for (const Game::OutdoorSpawn &spawn : outdoor.spawns)
    {
        monsterSpawns += spawn.typeId == SpawnTypeMonster ? 1 : 0;
    }

    std::map<std::string, double> tiles;
    int lowest = 255;
    int highest = 0;

    for (const uint8_t sample : outdoor.heightMap)
    {
        lowest = std::min<int>(lowest, sample);
        highest = std::max<int>(highest, sample);
    }

    for (const uint8_t tile : outdoor.tileMap)
    {
        tiles[std::to_string(tile)] += 1.0;
    }

    const EventKinds kinds = classifyBoundEvents(map, boundEvents);

    writer.key("structure");
    writer.beginObject();
    writer.field("bmodels", static_cast<uint64_t>(footprints.size()));
    writer.field("bmodel_faces", static_cast<uint64_t>(faces));
    writer.field("exits", static_cast<uint64_t>(kinds.exit));
    writer.endObject();

    writer.key("scale");
    writer.beginObject();
    writeSpread(writer, "building_footprint", spreadOf(footprints));
    writeSpread(writer, "building_height", spreadOf(heights));
    writeSpread(writer, "nearest_building_gap", spreadOf(gaps));
    writer.field("relief_range",
        (highest - lowest) * Game::OutdoorMapData::TerrainHeightScale);
    writer.endObject();

    writer.key("mechanisms");
    writer.beginObject();
    writer.field("bound_events", static_cast<uint64_t>(boundEvents.size()));
    writer.field("door_events", static_cast<uint64_t>(kinds.door));
    writer.field("trap_events", static_cast<uint64_t>(kinds.trap));
    writer.field("local_teleports", static_cast<uint64_t>(kinds.localTeleport));
    writer.field("chest_events", static_cast<uint64_t>(kinds.chest));
    writer.field("fixed_actors", static_cast<uint64_t>(map.state ? map.state->actors.size() : 0));
    writer.endObject();

    writer.key("density");
    writer.beginObject();
    writer.field("spawn_points", static_cast<uint64_t>(monsterSpawns));
    writer.field("decorations", static_cast<uint64_t>(outdoor.entities.size()));
    writer.endObject();

    writer.key("palette");
    writer.beginObject();
    writer.field("textures", static_cast<uint64_t>(textureFaces.size()));
    writeTopNames(writer, "textures_by_faces", textureFaces, 12);
    writer.field("decoration_kinds", static_cast<uint64_t>(decorationNames.size()));
    writeTopNames(writer, "decorations_by_count", decorationNames, 12);
    writer.field("tile_kinds", static_cast<uint64_t>(tiles.size()));
    writeTopNames(writer, "tiles_by_cells", tiles, 8);
    writer.endObject();
}
}

void writeMetricsJson(const LoadedMap &map, const MetricsOptions &options, JsonWriter &writer)
{
    writer.beginObject();
    writer.field("map", map.fileName);
    writer.field("world", map.world);
    writer.field("kind", map.indoor ? "indoor" : "outdoor");

    if (map.indoor)
    {
        writeIndoor(map, options, writer);
    }
    else if (map.outdoor)
    {
        writeOutdoor(map, writer);
    }

    writer.endObject();
}
}
