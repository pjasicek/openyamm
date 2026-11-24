#include "core/IndoorBuild.h"
#include "core/View.h"

#include "core/CoreMath.h"
#include "core/Cinematics.h"
#include "core/CanonicalYaml.h"
#include "core/Coplanar.h"
#include "core/EyeSector.h"
#include "core/GlbWriter.h"
#include "core/GroundTerrain.h"
#include "core/IndoorLowering.h"
#include "core/Kinds.h"
#include "core/EventFlow.h"
#include "core/Json.h"
#include "core/MapLoad.h"
#include "core/Ops.h"
#include "core/OutdoorBuild.h"
#include "core/SceneOverlay.h"
#include "core/Schema.h"
#include "core/Sketch.h"
#include "core/Walk.h"

#include "core/compile/IndoorSourceGeometryCompiler.h"
#include "game/FaceEnums.h"
#include "game/indoor/IndoorGeometryUtils.h"
#include "game/indoor/IndoorMapData.h"
#include "game/maps/IndoorSceneYml.h"
#include "game/maps/MapDeltaData.h"

#include <algorithm>
#include <functional>
#include <charconv>
#include <cmath>
#include <limits>
#include <set>
#include <sstream>

namespace OpenYAMM::Studio
{
namespace
{
YAML::Node childOf(const YAML::Node &node, const char *pKey)
{
    return node.IsDefined() && node.IsMap() ? node[pKey] : YAML::Node(YAML::NodeType::Undefined);
}

std::string textOf(const YAML::Node &node, const char *pKey, const std::string &fallback)
{
    const YAML::Node value = childOf(node, pKey);
    return value.IsDefined() && value.IsScalar() ? value.Scalar() : fallback;
}

template <typename Number>
YAML::Node sequenceOf(const std::vector<Number> &values)
{
    YAML::Node sequence(YAML::NodeType::Sequence);

    for (const Number value : values)
    {
        sequence.push_back(static_cast<int>(value));
    }

    return sequence;
}

// A scalar that is text whatever it looks like (an empty name, a string of digits): the tag marks it as quoted, so
// the writer does not turn it into null or a number.
YAML::Node textNode(const std::string &text)
{
    YAML::Node node(text);
    node.SetTag("!");
    return node;
}

YAML::Node position(double x, double y, double z)
{
    YAML::Node node(YAML::NodeType::Map);
    node["x"] = static_cast<int>(std::lround(x));
    node["y"] = static_cast<int>(std::lround(y));
    node["z"] = static_cast<int>(std::lround(z));
    return node;
}

// A list of numbers as the scene's readers take them: whole numbers as integers.
YAML::Node sceneNumbers(const std::vector<double> &values)
{
    YAML::Node sequence(YAML::NodeType::Sequence);

    for (const double value : values)
    {
        if (value == std::floor(value))
        {
            sequence.push_back(static_cast<int>(value));
        }
        else
        {
            sequence.push_back(value);
        }
    }

    return sequence;
}

// The texture axes the engine lays a face out by (one texel per unit): walls along the wall and down, floors and
// ceilings along x and against y, a sloping face by its steepness.
bool faceTextureAxes(
    const Game::IndoorFace &face,
    const std::array<double, 3> &normal,
    std::array<double, 3> &axisU,
    std::array<double, 3> &axisV)
{
    const double horizontal = oy::hypot(normal[0], normal[1]);
    const bool asWall = face.facetType == 1
        || ((face.facetType == 4 || face.facetType == 6) && std::abs(normal[2]) < 0.70863342285);
    const bool asFloor = face.facetType == 3 || face.facetType == 5 || face.facetType == 4 || face.facetType == 6;

    if (asWall && horizontal > 1.0e-6)
    {
        axisU = {0.0 - normal[1] / horizontal, normal[0] / horizontal, 0.0};
        axisV = {0.0, 0.0, -1.0};
    }
    else if (asFloor && !asWall)
    {
        axisU = {1.0, 0.0, 0.0};
        axisV = {0.0, -1.0, 0.0};
    }
    else
    {
        return false;
    }

    if (Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::FlipNormalU))
    {
        axisU = {0.0 - axisU[0], 0.0 - axisU[1], 0.0 - axisU[2]};
    }

    if (Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::FlipNormalV))
    {
        axisV = {0.0 - axisV[0], 0.0 - axisV[1], 0.0 - axisV[2]};
    }

    return true;
}

// Sets the face bits of surfaces (`liquid`, `flow`: GlbFace::attributes) on the compiled faces they became, found by
// texture and corners (the compiler keeps each polygon as one face and has no word for these bits). Then the check of
// liquids: a face of a texture the game draws as a liquid (engine/liquids/liquids.yml) or that the project lays as a
// liquid elsewhere, without the fluid bit, is said once per texture (the shipped liquid floors carry it, and it
// makes the picture of a liquid that is no shader's ripple).
// The engine's flow bits (down, up, left, right): a face whose picture flows is a liquid running down a wall or
// along a channel, with or without the fluid bit.
constexpr uint32_t FlowBits = 0x00000004 | 0x00000020 | 0x00000040 | 0x00000800;

void applySurfaceFaceBits(
    const std::vector<GlbNode> &nodes,
    Game::IndoorMapData &map,
    const LiquidTextures &liquids,
    std::vector<std::string> &warnings)
{
    const auto lower = [](std::string text)
    {
        std::transform(text.begin(), text.end(), text.begin(), [](unsigned char letter)
        {
            return static_cast<char>(std::tolower(letter));
        });
        return text;
    };
    using Corners = std::vector<std::array<long, 3>>;
    std::map<std::pair<std::string, Corners>, uint32_t> wanted;

    for (const GlbNode &node : nodes)
    {
        // A decoration's, light's or spawn's marker becomes an entity, not faces: its quad takes the floor's surface
        // (a liquid floor's bits too) and is never in the compiled map.
        if (node.name.starts_with("DECOR_") || node.name.starts_with("LIGHT_") || node.name.starts_with("SPAWN_"))
        {
            continue;
        }

        for (const GlbFace &face : node.faces)
        {
            if (face.attributes == 0)
            {
                continue;
            }

            Corners corners;

            for (const std::array<float, 3> &position : face.positions)
            {
                corners.push_back({std::lround(position[0]), std::lround(position[1]), std::lround(position[2])});
            }

            std::sort(corners.begin(), corners.end());
            wanted[{lower(face.material), corners}] |= face.attributes;
        }
    }

    std::set<std::pair<std::string, Corners>> found;
    std::set<std::string> laidAsLiquid;

    for (Game::IndoorFace &face : map.faces)
    {
        if (!wanted.empty())
        {
            Corners corners;

            for (const uint16_t vertex : face.vertexIndices)
            {
                const Game::IndoorVertex &point = map.vertices[vertex];
                corners.push_back({point.x, point.y, point.z});
            }

            std::sort(corners.begin(), corners.end());
            const auto entry = wanted.find({lower(face.textureName), corners});

            if (entry != wanted.end())
            {
                face.attributes |= entry->second;
                found.insert(entry->first);
            }
        }

        if (!face.isPortal && Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::Fluid))
        {
            laidAsLiquid.insert(lower(face.textureName));
        }
    }

    if (found.size() < wanted.size())
    {
        warnings.push_back("liquid and flow: " + std::to_string(wanted.size() - found.size()) + " of "
            + std::to_string(wanted.size()) + " faces with `liquid` or `flow` on their surface were not found in the "
            "compiled map and do not flow");
    }

    // Faces without the fluid bit, by texture.
    std::map<std::string, size_t> still;

    for (const Game::IndoorFace &face : map.faces)
    {
        const std::string texture = lower(face.textureName);

        if (!face.isPortal && !Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::Fluid)
            && !Game::hasFaceAttribute(face.attributes, Game::FaceAttribute::Invisible)
            && (face.attributes & FlowBits) == 0 && (liquids.matches(texture) || laidAsLiquid.contains(texture)))
        {
            ++still[texture];
        }
    }

    for (const std::pair<const std::string, size_t> &texture : still)
    {
        warnings.push_back("the liquid " + texture.first + " lies on " + std::to_string(texture.second) + " face(s) "
            "without the fluid bit (" + (liquids.matches(texture.first)
                ? std::string("a liquid of the game's shader, whose shipped faces carry the bit")
                : std::string("the project lays it as a liquid elsewhere, where its picture ripples"))
            + "): give that surface `liquid` (water, liquid or lava), or a floor a `floors` entry; a wall the "
            "liquid only runs down (a fall) takes `flow: down` alone");
    }
}

// The compiled faces of surfaces laid `translucent` (GlbFace::translucency), found by texture and corners as the face
// bits above, grouped by their translucency: the scene's `translucent_faces`.
std::map<GlbFaceTranslucency, std::vector<uint16_t>> findTranslucentFaces(
    const std::vector<GlbNode> &nodes,
    const Game::IndoorMapData &map,
    std::vector<std::string> &warnings)
{
    using Corners = std::vector<std::array<long, 3>>;
    const auto lower = [](std::string text)
    {
        std::transform(text.begin(), text.end(), text.begin(), [](unsigned char letter)
        {
            return static_cast<char>(std::tolower(letter));
        });
        return text;
    };
    std::map<std::pair<std::string, Corners>, GlbFaceTranslucency> wanted;

    for (const GlbNode &node : nodes)
    {
        for (const GlbFace &face : node.faces)
        {
            if (!face.translucency)
            {
                continue;
            }

            Corners corners;

            for (const std::array<float, 3> &position : face.positions)
            {
                corners.push_back({std::lround(position[0]), std::lround(position[1]), std::lround(position[2])});
            }

            std::sort(corners.begin(), corners.end());
            wanted[{lower(face.material), corners}] = *face.translucency;
        }
    }

    std::map<GlbFaceTranslucency, std::vector<uint16_t>> groups;
    std::set<std::pair<std::string, Corners>> found;

    for (size_t faceIndex = 0; faceIndex < map.faces.size() && !wanted.empty(); ++faceIndex)
    {
        const Game::IndoorFace &face = map.faces[faceIndex];
        Corners corners;

        for (const uint16_t vertex : face.vertexIndices)
        {
            const Game::IndoorVertex &point = map.vertices[vertex];
            corners.push_back({point.x, point.y, point.z});
        }

        std::sort(corners.begin(), corners.end());
        const auto entry = wanted.find({lower(face.textureName), corners});

        if (entry != wanted.end() && !face.isPortal)
        {
            groups[entry->second].push_back(static_cast<uint16_t>(faceIndex));
            found.insert(entry->first);
        }
    }

    if (found.size() < wanted.size())
    {
        warnings.push_back("translucent: " + std::to_string(wanted.size() - found.size()) + " of "
            + std::to_string(wanted.size()) + " faces with `translucent` on their surface were not found in the "
            "compiled map and draw opaque");
    }

    return groups;
}

// Makes the texture of every sliding part ride with it, where the project put it. The engine draws a face that
// moves with a door from the face's place in the world, one texel per unit, and not from its stored texels (the
// rule of the original maps; a face whose texels are scaled or turned is the exception and already rides). Drawn
// so, the texture stays in the world and slides across the moving face. With TextureMoveByDoor the engine takes
// the place the face has while the door is open and adds the face's texture delta. So each such face gets the
// flag, and its texels are split into that layout and the delta that brings the texture to where the project has
// it; texels plus delta, which is what the map stores for the face at rest, stay as they were. A face that
// stretches (a growing bridge) rides with its moving end.
void anchorMovingFaceTextures(Editor::IndoorSourceGeometryCompileResult &compiled)
{
    Game::IndoorMapData &map = compiled.indoorGeometry;

    for (Game::IndoorSceneDoor &sceneDoor : compiled.generatedDoors)
    {
        Game::MapDeltaDoor &door = sceneDoor.door;

        // A hinged leaf has no direction: the engine turns its stored texels with it.
        if (door.vertexIds.empty() || door.xOffsets.size() != door.vertexIds.size()
            || (door.directionX == 0 && door.directionY == 0 && door.directionZ == 0))
        {
            continue;
        }

        // From the open pose (the door's offsets) to the pose the map is drawn in: the same for every moving vertex.
        const Game::IndoorVertex &drawn = map.vertices[door.vertexIds.front()];
        const std::array<double, 3> fromOpen = {
            double(drawn.x) - door.xOffsets.front(), double(drawn.y) - door.yOffsets.front(),
            double(drawn.z) - door.zOffsets.front()};

        for (size_t faceOffset = 0; faceOffset < door.faceIds.size(); ++faceOffset)
        {
            Game::IndoorFace &face = map.faces[door.faceIds[faceOffset]];
            const size_t count = face.vertexIndices.size();

            if (count < 3 || face.textureUs.size() < count || face.textureVs.size() < count)
            {
                continue;
            }

            std::array<double, 3> normal = {0.0, 0.0, 0.0};

            for (size_t index = 0; index < count; ++index)
            {
                const Game::IndoorVertex &current = map.vertices[face.vertexIndices[index]];
                const Game::IndoorVertex &next = map.vertices[face.vertexIndices[(index + 1) % count]];
                normal[0] += (double(current.y) - next.y) * (double(current.z) + next.z);
                normal[1] += (double(current.z) - next.z) * (double(current.x) + next.x);
                normal[2] += (double(current.x) - next.x) * (double(current.y) + next.y);
            }

            const double length = std::sqrt(normal[0] * normal[0] + normal[1] * normal[1] + normal[2] * normal[2]);
            std::array<double, 3> axisU = {0.0, 0.0, 0.0};
            std::array<double, 3> axisV = {0.0, 0.0, 0.0};

            if (length < 1.0e-6)
            {
                continue;
            }

            normal = {normal[0] / length, normal[1] / length, normal[2] / length};

            if (!faceTextureAxes(face, normal, axisU, axisV))
            {
                continue;
            }

            std::vector<Game::IndoorProjectedFacePoint> geometryTexels;
            std::vector<Game::IndoorProjectedFacePoint> storedTexels;
            double offsetU = 0.0;
            double offsetV = 0.0;

            for (size_t index = 0; index < count; ++index)
            {
                const Game::IndoorVertex &vertex = map.vertices[face.vertexIndices[index]];
                const double u = vertex.x * axisU[0] + vertex.y * axisU[1] + vertex.z * axisU[2];
                const double v = vertex.x * axisV[0] + vertex.y * axisV[1] + vertex.z * axisV[2];
                geometryTexels.push_back({static_cast<float>(u), static_cast<float>(v)});
                storedTexels.push_back({static_cast<float>(face.textureDeltaU + face.textureUs[index]),
                    static_cast<float>(face.textureDeltaV + face.textureVs[index])});
                offsetU += (storedTexels.back().x - u) / double(count);
                offsetV += (storedTexels.back().y - v) / double(count);
            }

            // Scaled or turned texels: a face that moves whole keeps them in the engine; one that stretches cannot.
            if (Game::indoorMoverFaceKeepsStoredTexels(geometryTexels, storedTexels))
            {
                continue;
            }

            const long deltaU = std::lround(
                offsetU + fromOpen[0] * axisU[0] + fromOpen[1] * axisU[1] + fromOpen[2] * axisU[2]);
            const long deltaV = std::lround(
                offsetV + fromOpen[0] * axisV[0] + fromOpen[1] * axisV[1] + fromOpen[2] * axisV[2]);
            std::vector<int16_t> us;
            std::vector<int16_t> vs;
            bool inRange = std::abs(deltaU) <= std::numeric_limits<int16_t>::max()
                && std::abs(deltaV) <= std::numeric_limits<int16_t>::max();

            for (size_t index = 0; index < count && inRange; ++index)
            {
                const long u = face.textureDeltaU + face.textureUs[index] - deltaU;
                const long v = face.textureDeltaV + face.textureVs[index] - deltaV;
                inRange = std::abs(u) <= std::numeric_limits<int16_t>::max()
                    && std::abs(v) <= std::numeric_limits<int16_t>::max();
                us.push_back(static_cast<int16_t>(u));
                vs.push_back(static_cast<int16_t>(v));
            }

            if (!inRange)
            {
                continue;
            }

            std::copy(us.begin(), us.end(), face.textureUs.begin());
            std::copy(vs.begin(), vs.end(), face.textureVs.begin());
            face.textureDeltaU = static_cast<int16_t>(deltaU);
            face.textureDeltaV = static_cast<int16_t>(deltaV);
            face.attributes |= static_cast<uint32_t>(Game::FaceAttribute::TextureMoveByDoor);

            if (faceOffset < door.deltaUs.size() && faceOffset < door.deltaVs.size())
            {
                door.deltaUs[faceOffset] = face.textureDeltaU;
                door.deltaVs[faceOffset] = face.textureDeltaV;
            }
        }
    }
}

// The scene file of a new indoor map: every key game/maps/IndoorSceneYml.cpp requires, the doors the compiler
// generated, the party start and the chests.
// Door records that bear one door number are one door. What rides a moving part (a chest on a lift, a switch on a
// mover) is compiled as a record of its own beside its carrier's, because the indoor compiler makes a record of
// each node and a rider keeps a node for its own event; here the later records' vertices and faces join the first
// record of their number, and the records behind move up. A map without riders is left as it is.
void joinDoorRecords(Editor::IndoorSourceGeometryCompileResult &compiled)
{
    std::vector<Game::IndoorSceneDoor> joined;

    for (const Game::IndoorSceneDoor &sceneDoor : compiled.generatedDoors)
    {
        Game::IndoorSceneDoor *pFirst = nullptr;

        for (Game::IndoorSceneDoor &candidate : joined)
        {
            if (candidate.door.doorId == sceneDoor.door.doorId)
            {
                pFirst = &candidate;
            }
        }

        if (pFirst == nullptr)
        {
            joined.push_back(sceneDoor);
            continue;
        }

        Game::MapDeltaDoor &door = pFirst->door;
        const Game::MapDeltaDoor &rider = sceneDoor.door;
        door.vertexIds.insert(door.vertexIds.end(), rider.vertexIds.begin(), rider.vertexIds.end());
        door.faceIds.insert(door.faceIds.end(), rider.faceIds.begin(), rider.faceIds.end());
        door.deltaUs.insert(door.deltaUs.end(), rider.deltaUs.begin(), rider.deltaUs.end());
        door.deltaVs.insert(door.deltaVs.end(), rider.deltaVs.begin(), rider.deltaVs.end());
        door.xOffsets.insert(door.xOffsets.end(), rider.xOffsets.begin(), rider.xOffsets.end());
        door.yOffsets.insert(door.yOffsets.end(), rider.yOffsets.begin(), rider.yOffsets.end());
        door.zOffsets.insert(door.zOffsets.end(), rider.zOffsets.begin(), rider.zOffsets.end());

        for (const uint16_t sectorId : rider.sectorIds)
        {
            if (std::find(door.sectorIds.begin(), door.sectorIds.end(), sectorId) == door.sectorIds.end())
            {
                door.sectorIds.push_back(sectorId);
            }
        }
    }

    if (joined.size() == compiled.generatedDoors.size())
    {
        return;
    }

    for (size_t index = 0; index < joined.size(); ++index)
    {
        Game::MapDeltaDoor &door = joined[index].door;
        joined[index].doorIndex = index;
        door.slotIndex = static_cast<uint32_t>(index);
        door.numVertices = static_cast<uint16_t>(door.vertexIds.size());
        door.numFaces = static_cast<uint16_t>(door.faceIds.size());
        door.numSectors = static_cast<uint16_t>(door.sectorIds.size());
        door.numOffsets = static_cast<uint16_t>(door.xOffsets.size());
    }

    compiled.generatedDoors = joined;
    compiled.indoorGeometry.doorCount = static_cast<uint32_t>(joined.size());
}

std::string writeSceneText(
    const Project &project,
    const LoweredIndoorMap &lowered,
    const Editor::IndoorSourceGeometryCompileResult &compiled,
    const std::map<GlbFaceTranslucency, std::vector<uint16_t>> &translucentFaces,
    YAML::Node &sceneOut)
{
    YAML::Node scene(YAML::NodeType::Map);
    scene["format_version"] = 1;
    scene["kind"] = "indoor_scene";
    scene["source"]["geometry_file"] = lowered.mapStem + ".blv";

    YAML::Node environment(YAML::NodeType::Map);
    environment["sky_texture"] = textNode("");
    environment["day_bits_raw"] = 0;
    environment["map_extra_bits_raw"] = 0;
    environment["ceiling"] = lowered.sceneCeiling;

    for (const char *pFlag : {"foggy", "raining", "snowing", "underwater", "no_terrain", "always_dark", "always_light",
             "always_foggy", "red_fog"})
    {
        environment["flags"][pFlag] = false;
    }

    environment["fog"]["weak_distance"] = lowered.fogWeakDistance;
    environment["fog"]["strong_distance"] = lowered.fogStrongDistance;
    scene["environment"] = environment;

    // Faces run by walking into them (wiring `touch: true`): the game runs no touch face without this (MM8's chests
    // carry the bit, which its engine ignored).
    if (lowered.touchFaces)
    {
        scene["party_movement"]["touch_faces"] = "run";
    }

    // project.yml rules.no_spells (S8g): no spell works on the map, as in MM7's Shoals (the scene's
    // runtime_restrictions; the other restrictions keep the game's defaults).
    if (textOf(childOf(project.document("project.yml"), "rules"), "no_spells", "") == "true")
    {
        scene["runtime_restrictions"]["allow_spellcasting"] = false;
    }

    // objects.yml `arena` (XD-20): the scene's `arena` block and the restrictions of MM7's arena (7d05_1.scene.yml):
    // no saving and no Lloyd's Beacon there, and the arena's fights refilled on every visit.
    if (lowered.arena)
    {
        const auto point = [](const std::array<double, 3> &at)
        {
            YAML::Node node(YAML::NodeType::Sequence);
            node.SetStyle(YAML::EmitterStyle::Flow);

            for (const double value : at)
            {
                node.push_back(static_cast<int>(std::lround(value)));
            }

            return node;
        };

        scene["runtime_restrictions"]["allow_save_game"] = false;
        scene["runtime_restrictions"]["allow_lloyds_beacon"] = false;
        scene["runtime_restrictions"]["arena"] = true;
        YAML::Node arena(YAML::NodeType::Map);
        arena["minimum_monster_id"] = lowered.arena->minimumMonsterId;
        arena["maximum_monster_id"] = lowered.arena->maximumMonsterId;
        arena["party_position"] = point(lowered.arena->party.position);
        arena["party_direction_degrees"] = lowered.arena->party.directionDegrees;

        for (const std::array<double, 3> &mark : lowered.arena->marks)
        {
            arena["monster_positions"].push_back(point(mark));
        }

        scene["arena"] = arena;
    }

    // Ground mist and fog volumes as atmosphere.yml gives them, the scene's `mist` block as the game reads it
    // (devdocs/MIST.md; the lowering has checked it with the game's parser).
    if (project.has("atmosphere.yml"))
    {
        if (const YAML::Node mist = childOf(project.document("atmosphere.yml"), "mist"); mist.IsDefined()
            && mist.IsMap())
        {
            scene["mist"] = YAML::Clone(mist);
        }

        // The scene's own blocks of a map open to the sky (S6 item S), as given; the game's parser checks them when
        // the build reads the scene back.
        for (const std::pair<const char *, const char *> &block : {std::pair<const char *, const char *>{"open_sky",
                 "sky"}, {"scene_fog", "fog"}, {"daylight", "daylight"}, {"terrain", "terrain"}})
        {
            if (const YAML::Node node = childOf(project.document("atmosphere.yml"), block.first); node.IsDefined()
                && node.IsMap())
            {
                scene[block.second] = YAML::Clone(node);
            }
        }
    }

    YAML::Node state(YAML::NodeType::Map);
    state["location"]["respawn_count"] = 0;
    state["location"]["last_respawn_day"] = 0;
    state["location"]["reputation"] = 0;
    state["location"]["alert_status"] = 0;
    // 875 bytes of outline visibility, all unseen.
    state["visible_outlines"]["bitset_hex"] = textNode(std::string(1750, '0'));
    state["face_attribute_overrides"] = YAML::Node(YAML::NodeType::Sequence);
    state["decoration_flags"] = YAML::Node(YAML::NodeType::Sequence);

    // Decorations hidden at the start (`hidden: true`): the map state's copy of the BLV entity's flags.
    for (size_t entityIndex = 0; entityIndex < lowered.metadata.entities.size(); ++entityIndex)
    {
        if (const uint16_t flags = lowered.metadata.entities[entityIndex].aiAttributes; flags != 0)
        {
            YAML::Node flag(YAML::NodeType::Map);
            flag["entity_index"] = entityIndex;
            flag["flag"] = flags;
            state["decoration_flags"].push_back(flag);
        }
    }
    YAML::Node actors(YAML::NodeType::Sequence);

    // Placed monsters, as a shipped map's scene holds its actors. The sprites are left to the game, which takes
    // them from the monster's descriptor.
    for (const LoweredMonster &monster : lowered.monsters)
    {
        actors.push_back(sceneActorNode(monster, static_cast<int>(actors.size())));
    }

    state["actors"] = actors;
    YAML::Node spriteObjects(YAML::NodeType::Sequence);

    // Items on the floor, as a shipped map's scene holds its sprite objects: the item's number is the first four of
    // the 36 bytes of the item record the object carries.
    for (const LoweredItem &item : lowered.items)
    {
        spriteObjects.push_back(sceneSpriteObjectNode(item, static_cast<int>(spriteObjects.size())));
    }

    state["sprite_objects"] = spriteObjects;
    // Chests whose rolls have levels of their own (`random_levels`) are the game's own chest records, as a shipped
    // map's scene holds them: 140 item records of 36 bytes, an item's number in the first four (a number below
    // zero: one roll of that treasure level, made on the first opening), and the grid of what lies where, empty
    // until then. A record's place in the list is the chest's number; the places below it that belong to loot
    // containers (further down) stay empty records, which the game replaces.
    YAML::Node chestRecords(YAML::NodeType::Sequence);
    int lastRecord = -1;

    for (const LoweredChest &chest : lowered.chests)
    {
        lastRecord = chest.randomLevels.empty() ? lastRecord : std::max(lastRecord, chest.containerId);
    }

    for (int number = 0; number <= lastRecord; ++number)
    {
        std::vector<int> things;
        bool trapped = false;

        for (const LoweredChest &chest : lowered.chests)
        {
            if (chest.containerId != number || chest.randomLevels.empty())
            {
                continue;
            }

            things = chest.items;
            things.insert(things.end(), static_cast<size_t>(chest.randomItems), 0 - chest.treasureLevel);

            for (const int level : chest.randomLevels)
            {
                things.push_back(0 - level);
            }

            trapped = chest.trapLevel > 0;
        }

        std::string records;

        for (size_t slot = 0; slot < 140; ++slot)
        {
            for (int byte = 0; byte < 36; ++byte)
            {
                static const char *pDigits = "0123456789ABCDEF";
                const unsigned value = slot < things.size() && byte < 4
                    ? (static_cast<uint32_t>(things[slot]) >> (8 * byte)) & 0xffu : 0u;
                records.push_back(pDigits[value >> 4]);
                records.push_back(pDigits[value & 0xfu]);
            }
        }

        YAML::Node node(YAML::NodeType::Map);
        node["chest_index"] = number;
        node["chest_type_id"] = 0;
        node["flags"] = trapped ? 1 : 0;
        node["raw_items_hex"] = textNode(records);
        node["inventory_matrix"] = sequenceOf(std::vector<int>(140, 0));
        chestRecords.push_back(node);
    }

    state["chests"] = chestRecords;
    YAML::Node doors(YAML::NodeType::Sequence);

    for (const Game::IndoorSceneDoor &sceneDoor : compiled.generatedDoors)
    {
        const Game::MapDeltaDoor &door = sceneDoor.door;
        YAML::Node node(YAML::NodeType::Map);
        node["door_index"] = static_cast<int>(sceneDoor.doorIndex);
        node["legacy_attributes"] = door.attributes;
        node["door_id"] = door.doorId;
        node["time_since_triggered_ms"] = door.timeSinceTriggered;
        node["direction"].push_back(door.directionX);
        node["direction"].push_back(door.directionY);
        node["direction"].push_back(door.directionZ);
        node["move_length"] = door.moveLength;
        node["open_speed"] = door.openSpeed;
        node["close_speed"] = door.closeSpeed;
        node["state"] = static_cast<int>(door.state);
        node["vertex_ids"] = sequenceOf(door.vertexIds);
        node["face_ids"] = sequenceOf(door.faceIds);
        node["sector_ids"] = sequenceOf(door.sectorIds);
        node["delta_us"] = sequenceOf(door.deltaUs);
        node["delta_vs"] = sequenceOf(door.deltaVs);
        node["x_offsets"] = sequenceOf(door.xOffsets);
        node["y_offsets"] = sequenceOf(door.yOffsets);
        node["z_offsets"] = sequenceOf(door.zOffsets);

        // The compiler stores a sliding leaf in its open pose (slid away by its travel); a rotating mover's stored
        // pose is the closed one, so the slide is taken back out of the offsets.
        const auto closedPose = [&door](const std::vector<int16_t> &offsets, int32_t direction)
        {
            std::vector<int> closed;

            for (const int16_t offset : offsets)
            {
                closed.push_back(static_cast<int>(
                    std::lround(offset + direction / 65536.0 * static_cast<double>(door.moveLength))));
            }

            return closed;
        };

        // A hinged leaf is the engine's rotating mover (devdocs/INDOOR_ROTATING_MOVERS_AND_LADDERS.md): no slide,
        // the travel in tenths of a degree, and the hinge line.
        for (const LoweredDoor &loweredDoor : lowered.doors)
        {
            // The second leaf of a hinged pair turns about its own jamb.
            const bool secondLeaf = loweredDoor.secondDoorId != 0
                && loweredDoor.secondDoorId == static_cast<int>(door.doorId);

            if (!loweredDoor.hinged || (loweredDoor.doorId != static_cast<int>(door.doorId) && !secondLeaf))
            {
                continue;
            }

            const std::array<double, 3> &pivot = secondLeaf ? loweredDoor.secondPivot : loweredDoor.pivot;
            const double openDegrees = secondLeaf ? loweredDoor.secondOpenDegrees : loweredDoor.openDegrees;
            const int travel = static_cast<int>(std::lround(std::abs(openDegrees) * 10.0));
            const int speed = static_cast<int>(std::lround(loweredDoor.turnSpeed * 10.0));
            node["x_offsets"] = sequenceOf(closedPose(door.xOffsets, door.directionX));
            node["y_offsets"] = sequenceOf(closedPose(door.yOffsets, door.directionY));
            node["z_offsets"] = sequenceOf(closedPose(door.zOffsets, door.directionZ));
            node["direction"] = sequenceOf(std::vector<int>{0, 0, 0});
            node["move_length"] = travel;
            node["open_speed"] = speed;
            node["close_speed"] = speed;
            YAML::Node rotation(YAML::NodeType::Map);
            rotation["pivot"].push_back(pivot[0]);
            rotation["pivot"].push_back(pivot[1]);
            rotation["pivot"].push_back(pivot[2]);
            // A trapdoor turns about its level hinge line, the same way for whoever opens it.
            rotation["axis"].push_back(loweredDoor.axis[0]);
            rotation["axis"].push_back(loweredDoor.axis[1]);
            rotation["axis"].push_back(loweredDoor.axis[2]);
            rotation["open_degrees"] = openDegrees;
            rotation["open_away"] = !loweredDoor.hatch;
            node["mover"]["rotation"] = rotation;
            node["mover"]["easing"] = "sine";
            node["mover"]["bodies"] = "reverse";

            if (loweredDoor.autoCloseSeconds > 0.0)
            {
                node["mover"]["auto_close_seconds"] = loweredDoor.autoCloseSeconds;
            }
        }

        // A sliding door or gate stops for the party and the monsters: closing onto a body it opens again, opening it
        // holds (`bodies: reverse`, as the hinged leaves above and MM9's doors). Without it a gate shut through the
        // party standing in its doorway (F43, XD-02's east-cart gateway, 2026-11-24). Lifts and movers stay as they
        // are: they carry what stands on them.
        for (const LoweredDoor &loweredDoor : lowered.doors)
        {
            if (!loweredDoor.hinged && !node["mover"]
                && (loweredDoor.doorId == static_cast<int>(door.doorId)
                    || loweredDoor.secondDoorId == static_cast<int>(door.doorId)))
            {
                node["mover"]["bodies"] = "reverse";
            }
        }

        // A leaf that folds (`fold: true`): only its free edge moves, as the shipped maps' sliding doors are made.
        // The compiler moves every vertex of a mechanism's node; the free edge is the one farthest in the closing
        // direction in the drawn (shut) pose, and the other vertices leave the record and stay at the jamb.
        for (const LoweredDoor &loweredDoor : lowered.doors)
        {
            if (!loweredDoor.fold || (loweredDoor.doorId != static_cast<int>(door.doorId)
                    && loweredDoor.secondDoorId != static_cast<int>(door.doorId)))
            {
                continue;
            }

            const auto along = [&door, &compiled](uint16_t vertexId)
            {
                const Game::IndoorVertex &vertex = compiled.indoorGeometry.vertices[vertexId];
                return static_cast<int64_t>(vertex.x) * door.directionX
                    + static_cast<int64_t>(vertex.y) * door.directionY
                    + static_cast<int64_t>(vertex.z) * door.directionZ;
            };
            int64_t farthest = std::numeric_limits<int64_t>::min();

            for (const uint16_t vertexId : door.vertexIds)
            {
                farthest = std::max(farthest, along(vertexId));
            }

            std::vector<int> vertexIds;
            std::vector<int> xOffsets;
            std::vector<int> yOffsets;
            std::vector<int> zOffsets;

            for (size_t index = 0; index < door.vertexIds.size(); ++index)
            {
                // Half a unit of slack, in the direction's 16.16 scale.
                if (along(door.vertexIds[index]) >= farthest - 32768)
                {
                    vertexIds.push_back(door.vertexIds[index]);
                    xOffsets.push_back(door.xOffsets[index]);
                    yOffsets.push_back(door.yOffsets[index]);
                    zOffsets.push_back(door.zOffsets[index]);
                }
            }

            node["vertex_ids"] = sequenceOf(vertexIds);
            node["x_offsets"] = sequenceOf(xOffsets);
            node["y_offsets"] = sequenceOf(yOffsets);
            node["z_offsets"] = sequenceOf(zOffsets);
        }

        // A mover of objects.yml (it is among the lifts): one that stretches moves only its end face, and one that
        // returns by itself closes like a door that shuts by itself.
        for (const LoweredLift &mover : lowered.lifts)
        {
            if (!mover.mover || mover.doorId != static_cast<int>(door.doorId))
            {
                continue;
            }

            if (mover.stretch)
            {
                // The compiler moves every vertex of a mechanism's node. The end face is the one farthest along the
                // travel (the direction points from open to closed, against it) in the drawn pose; the other
                // vertices leave the record and stay where the map file has them.
                const auto along = [&door, &compiled](uint16_t vertexId)
                {
                    const Game::IndoorVertex &vertex = compiled.indoorGeometry.vertices[vertexId];
                    return -(static_cast<int64_t>(vertex.x) * door.directionX
                        + static_cast<int64_t>(vertex.y) * door.directionY
                        + static_cast<int64_t>(vertex.z) * door.directionZ);
                };
                int64_t farthest = std::numeric_limits<int64_t>::min();

                for (const uint16_t vertexId : door.vertexIds)
                {
                    farthest = std::max(farthest, along(vertexId));
                }

                std::vector<int> vertexIds;
                std::vector<int> xOffsets;
                std::vector<int> yOffsets;
                std::vector<int> zOffsets;

                for (size_t index = 0; index < door.vertexIds.size(); ++index)
                {
                    // Half a unit of slack, in the direction's 16.16 scale.
                    if (along(door.vertexIds[index]) >= farthest - 32768)
                    {
                        vertexIds.push_back(door.vertexIds[index]);
                        xOffsets.push_back(door.xOffsets[index]);
                        yOffsets.push_back(door.yOffsets[index]);
                        zOffsets.push_back(door.zOffsets[index]);
                    }
                }

                node["vertex_ids"] = sequenceOf(vertexIds);
                node["x_offsets"] = sequenceOf(xOffsets);
                node["y_offsets"] = sequenceOf(yOffsets);
                node["z_offsets"] = sequenceOf(zOffsets);
            }

            if (mover.autoReturnSeconds > 0.0)
            {
                node["mover"]["auto_close_seconds"] = mover.autoReturnSeconds;
            }

            // A mover that turns (`turn`): the rotating mover, its start the closed pose, its end the open one.
            if (mover.turning)
            {
                node["x_offsets"] = sequenceOf(closedPose(door.xOffsets, door.directionX));
                node["y_offsets"] = sequenceOf(closedPose(door.yOffsets, door.directionY));
                node["z_offsets"] = sequenceOf(closedPose(door.zOffsets, door.directionZ));
                node["direction"] = sequenceOf(std::vector<int>{0, 0, 0});
                node["move_length"] = static_cast<int>(std::lround(std::abs(mover.degrees) * 10.0));
                node["open_speed"] = static_cast<int>(std::lround(mover.turnSpeed * 10.0));
                node["close_speed"] = static_cast<int>(std::lround(mover.turnSpeed * 10.0));
                YAML::Node rotation(YAML::NodeType::Map);
                rotation["pivot"] = sequenceOf(std::vector<double>(mover.pivot.begin(), mover.pivot.end()));
                rotation["axis"] = sequenceOf(std::vector<double>(mover.axis.begin(), mover.axis.end()));
                rotation["open_degrees"] = mover.degrees;
                rotation["open_away"] = false;
                node["mover"]["rotation"] = rotation;
                node["mover"]["easing"] = "sine";
            }

            // The game carries what stands on a part that moves up or down. One that slides level carries only
            // when its record asks for it; a block that stretches does not move under what stands on it.
            if (!mover.stretch && !mover.turning && door.directionZ == 0)
            {
                node["mover"]["carry"] = true;
            }
        }

        doors.push_back(node);
    }

    state["doors"] = doors;
    state["variables"]["map"] = sequenceOf(std::vector<int>(75, 0));
    state["variables"]["decor"] = sequenceOf(std::vector<int>(125, 0));
    scene["initial_state"] = state;

    if (lowered.start)
    {
        YAML::Node start(YAML::NodeType::Map);
        start["start_index"] = 0;
        start["source_name"] = "StartPoint0";
        start["position"].push_back(static_cast<int>(std::lround(lowered.start->position[0])));
        start["position"].push_back(static_cast<int>(std::lround(lowered.start->position[1])));
        start["position"].push_back(static_cast<int>(std::lround(lowered.start->position[2])));
        start["direction_degrees"] = lowered.start->directionDegrees;
        scene["party_start_points"].push_back(start);
    }

    const std::string world = textOf(project.document("project.yml"), "world", "world");
    YAML::Node containers(YAML::NodeType::Sequence);

    for (const LoweredChest &chest : lowered.chests)
    {
        // (A chest with rolls of several levels is a chest record of the starting state, above.)
        if (!chest.randomLevels.empty())
        {
            continue;
        }

        YAML::Node node(YAML::NodeType::Map);
        node["source_id"] = world + ":" + lowered.mapStem + ":" + chest.name;
        node["source_object_index"] = chest.containerId;
        node["source_name"] = chest.name;
        node["position"] = position(chest.position[0], chest.position[1], chest.position[2]);
        node["container_id"] = chest.containerId;
        node["kind"] = "chest";
        node["presentation"] = "wooden chest";
        node["random_treasure_level"] = chest.treasureLevel;
        node["treasure_type"] = 0;
        node["gold"] = chest.gold;
        node["gold_only"] = false;
        node["random"] = true;
        node["ai_drop"] = false;
        node["trap_level"] = chest.trapLevel;
        node["should_repopulate"] = true;
        YAML::Node fixedItems(YAML::NodeType::Sequence);
        int slot = 1;

        for (const int itemId : chest.items)
        {
            YAML::Node item(YAML::NodeType::Map);
            item["slot"] = slot++;
            item["raw_mm9_item_id"] = 0;
            item["item_id"] = itemId;
            fixedItems.push_back(item);
        }

        node["fixed_items"] = fixedItems;
        node["remove_when_empty"] = false;
        node["random_records"] = chest.randomItems;
        containers.push_back(node);
    }

    scene["loot_containers"] = containers;
    // A list of numbers as the scene's readers take them.
    const auto numbers = [](const std::vector<double> &values)
    {
        return sceneNumbers(values);
    };

    // Ladders, pulsing lights and placed sounds: scene lists the game reads beside the map (none: no key).
    for (const LoweredLadder &ladder : lowered.ladders)
    {
        scene["ladders"].push_back(sceneLadderNode(ladder));
    }

    for (const LoweredPulsingLight &light : lowered.pulsingLights)
    {
        YAML::Node node(YAML::NodeType::Map);
        node["key"] = light.key;
        node["position"] = numbers({light.position[0], light.position[1], light.position[2]});
        node["color"] = sequenceOf(std::vector<int>{light.color[0], light.color[1], light.color[2]});
        node["intensity"] =
            numbers({light.intensity[0], light.intensity[1], light.intensity[2], light.intensity[3]});
        node["radius"] = numbers({light.radius[0], light.radius[1], light.radius[2], light.radius[3]});
        node["start_on"] = light.startOn;
        scene["pulsing_lights"].push_back(node);
    }

    for (const LoweredAmbientSound &sound : lowered.ambientSounds)
    {
        YAML::Node node(YAML::NodeType::Map);
        node["key"] = sound.key;
        node["sound"] = textNode(sound.sound);
        node["position"] = numbers({sound.position[0], sound.position[1], sound.position[2]});
        node["inner_radius"] = numbers({sound.innerRadius})[0];
        node["outer_radius"] = numbers({sound.outerRadius})[0];
        node["volume"] = numbers({sound.volume})[0];
        node["loop"] = sound.loop;

        if (sound.wait)
        {
            node["wait"] = numbers({(*sound.wait)[0], (*sound.wait)[1]});
        }

        node["start_on"] = sound.startOn;

        if (!sound.pan)
        {
            node["pan"] = false;
        }

        // (Only when set: earlier builds' scenes keep their bytes.)
        for (const std::pair<const char *, bool> &hours : {std::pair<const char *, bool>{"day_only", sound.dayOnly},
                 {"night_only", sound.nightOnly}})
        {
            if (hours.second)
            {
                node[hours.first] = true;
            }
        }

        scene["ambient_sounds"].push_back(node);
    }

    // Destructibles (S6): their faces' cog or their decoration's sprite key, the centre of what breaks.
    for (const LoweredDestructible &destructible : lowered.destructibles)
    {
        std::array<double, 3> low = {1.0e12, 1.0e12, 1.0e12};
        std::array<double, 3> high = {-1.0e12, -1.0e12, -1.0e12};
        const Game::IndoorMapData &geometry = compiled.indoorGeometry;
        const auto take = [&low, &high](double x, double y, double z)
        {
            low = {std::min(low[0], x), std::min(low[1], y), std::min(low[2], z)};
            high = {std::max(high[0], x), std::max(high[1], y), std::max(high[2], z)};
        };

        for (const Game::IndoorFace &face : geometry.faces)
        {
            if (destructible.cog != 0 && face.cogNumber == destructible.cog)
            {
                for (const uint16_t vertex : face.vertexIndices)
                {
                    if (vertex < geometry.vertices.size())
                    {
                        take(geometry.vertices[vertex].x, geometry.vertices[vertex].y, geometry.vertices[vertex].z);
                    }
                }
            }
        }

        for (const Game::IndoorEntity &entity : geometry.entities)
        {
            if (destructible.decorationCog != 0 && entity.eventIdPrimary == destructible.decorationCog)
            {
                take(entity.x, entity.y, entity.z + 48.0);
            }
        }

        YAML::Node node(YAML::NodeType::Map);
        node["id"] = destructible.number;
        node["name"] = textNode(destructible.id.substr(destructible.id.find(':') + 1));
        node["hp"] = destructible.hp;
        node["damage_enabled"] = destructible.damage;
        node["trigger_destroy_only"] = destructible.triggerOnly;
        node["sound"] = textNode(destructible.sound);
        node["effect"] = textNode("openyamm:fx/destructible/" + destructible.material);
        node["effect_scale"] = numbers({destructible.effectScale})[0];
        node["center"] = low[0] <= high[0]
            ? numbers({std::round((low[0] + high[0]) / 2.0), std::round((low[1] + high[1]) / 2.0),
                std::round((low[2] + high[2]) / 2.0)})
            : numbers({0.0, 0.0, 0.0});

        if (destructible.cog != 0)
        {
            node["cog"] = destructible.cog;
        }

        if (destructible.decorationCog != 0)
        {
            node["decoration_cog"] = destructible.decorationCog;
        }

        if (destructible.destroyedEvent != 0)
        {
            node["destroyed_event"] = destructible.destroyedEvent;
        }

        if (destructible.damagedEvent != 0)
        {
            node["damaged_event"] = destructible.damagedEvent;
        }

        scene["destructibles"].push_back(node);
    }

    // Water volumes (S6): one upright piece each.
    for (const LoweredWater &water : lowered.water)
    {
        YAML::Node node(YAML::NodeType::Map);
        node["id"] = textNode(water.id.substr(water.id.find(':') + 1));
        node["liquid"] = textNode(water.liquid);
        YAML::Node piece(YAML::NodeType::Map);

        for (const std::array<double, 2> &point : water.outline)
        {
            piece["polygon"].push_back(numbers({point[0], point[1]}));
        }

        piece["bottom"] = numbers({water.bottom})[0];
        piece["top"] = numbers({water.top})[0];
        node["pieces"].push_back(piece);

        if (water.tint)
        {
            node["tint"] = numbers({(*water.tint)[0], (*water.tint)[1], (*water.tint)[2]});
        }

        if (water.current)
        {
            node["current"] = numbers({(*water.current)[0], (*water.current)[1], (*water.current)[2]});
        }

        if (water.fog.IsDefined() && water.fog.IsMap())
        {
            node["fog"] = YAML::Clone(water.fog);
        }

        scene["water_volumes"].push_back(node);
    }

    YAML::Node solidFaces(YAML::NodeType::Sequence);
    solidFaces.SetStyle(YAML::EmitterStyle::Flow);
    for (const auto &group : compiled.generatedFaceGroups)
    {
        if (lowered.decorationCollisionNodes.contains(group.sourceNodeName))
        {
            for (uint16_t face : group.faceIds)
            {
                solidFaces.push_back(face);
            }
        }
    }
    if (solidFaces.size() > 0)
    {
        scene["decoration_collision_faces"] = solidFaces;
    }

    // Faces laid with a `translucent` surface, one entry per translucency.
    for (const auto &[translucency, faces] : translucentFaces)
    {
        YAML::Node node(YAML::NodeType::Map);
        YAML::Node faceList(YAML::NodeType::Sequence);
        faceList.SetStyle(YAML::EmitterStyle::Flow);

        for (const uint16_t face : faces)
        {
            faceList.push_back(static_cast<int>(face));
        }

        node["faces"] = faceList;
        node["opacity"] = numbers({translucency.opacity})[0];
        node["tint"] = numbers({translucency.tint[0], translucency.tint[1], translucency.tint[2]});
        node["two_sided"] = translucency.twoSided;
        scene["translucent_faces"].push_back(node);
    }

    sceneOut = scene;
    return writeCanonicalYaml(scene);
}

std::string writeLuaText(const Project &project, const LoweredIndoorMap &lowered)
{
    std::ostringstream lua;
    lua << "-- Generated by oymap build from the Map Studio project \""
        << textOf(project.document("project.yml"), "id", lowered.mapStem)
        << "\". Change the project (wiring.yml), not this file.\n";
    lua << "SetMapMetadata({onLoad = {";
    bool first = true;

    // The build's own event that makes the peaceful groups peaceful runs first: the project's load events may change
    // a group (an event that turns one hostile once a quest says so, as D1 does outdoors).
    for (const bool peaceful : {true, false})
    {
        for (const LoweredEvent &event : lowered.events)
        {
            if (event.trigger == "load" && (event.id == "evt:studio_peaceful_groups") == peaceful)
            {
                lua << (first ? "" : ", ") << event.eventId;
                first = false;
            }
        }
    }

    lua << "}, onLeave = {";
    first = true;

    for (const LoweredEvent &event : lowered.events)
    {
        if (event.trigger == "leave")
        {
            lua << (first ? "" : ", ") << event.eventId;
            first = false;
        }
    }

    lua << "}, openedChestIds = {";
    first = true;

    // Every chest an event may show: its chest preset's, and those its effects open (open_chest: a chest opened from
    // a second source, one chest of two), as the game lists them for a clicked thing.
    for (const LoweredEvent &event : lowered.events)
    {
        std::vector<int> containers;

        if (event.opensContainer)
        {
            containers.push_back(*event.opensContainer);
        }

        for (const std::string &line : event.body)
        {
            for (size_t at = line.find("evt.OpenChest("); at != std::string::npos;
                 at = line.find("evt.OpenChest(", at + 1))
            {
                const int container = std::atoi(line.c_str() + at + 14);

                if (std::find(containers.begin(), containers.end(), container) == containers.end())
                {
                    containers.push_back(container);
                }
            }
        }

        if (!containers.empty())
        {
            lua << (first ? "" : ", ") << "[" << event.eventId << "] = {";

            for (size_t index = 0; index < containers.size(); ++index)
            {
                lua << (index == 0 ? "" : ", ") << containers[index];
            }

            lua << "}";
            first = false;
        }
    }

    lua << "}";
    first = true;

    // Timers as the scripts exported from the original maps declare them: an interval counted in half minutes of
    // game time, which is one second of play each.
    for (const LoweredEvent &event : lowered.events)
    {
        if (event.trigger != "timer")
        {
            continue;
        }

        lua << (first ? ", timers = {\n" : "") << "    { eventId = " << event.eventId << ", sourceEventId = "
            << event.eventId << ", triggerStep = 0, origin = \"legacy\", triggerKind = \"timer\", "
            << "scheduleKind = \"interval\", intervalHalfMinutes = " << event.everySeconds << " },\n";
        first = false;
    }

    lua << (first ? "})\n" : "}})\n");

    for (const LoweredEvent &event : lowered.events)
    {
        const std::string title = event.title.empty() ? "nil" : jsonQuote(event.title);
        lua << "\n-- " << event.id << "\n";
        // A handler that continues a question, or whose script reads continueStep (a `lua` effect continuing a
        // dialogue it opened, such as Xeen's mirrors), takes it.
        const bool continues = event.continues || std::any_of(event.body.begin(), event.body.end(),
            [](const std::string &line) { return line.find("continueStep") != std::string::npos; });
        // A damage hook (`trigger: monster_damage`): registered on load as the map's MonsterDamage hook, given the
        // hit as `hook` (evt.GetHookContext()); with `monsters` it acts on those monster ids only.
        const bool damageHook = event.trigger == "monster_damage";

        if (damageHook)
        {
            lua << "RegisterMonsterDamageHook(" << event.eventId << ", " << title << ", function(hook)\n";

            if (!event.hookMonsters.empty())
            {
                lua << "    local monsters = {";

                for (size_t index = 0; index < event.hookMonsters.size(); ++index)
                {
                    lua << (index == 0 ? "" : ", ") << "[" << event.hookMonsters[index] << "] = true";
                }

                lua << "}\n    if not monsters[hook.monsterId] then return end\n";
            }

            if (!event.hookActors.empty())
            {
                lua << "    local actors = {";

                for (size_t index = 0; index < event.hookActors.size(); ++index)
                {
                    lua << (index == 0 ? "" : ", ") << "[" << event.hookActors[index] << "] = true";
                }

                lua << "}\n    if not actors[hook.actorIndex] then return end\n";
            }
        }
        else
        {
            lua << "RegisterEvent(" << event.eventId << ", " << title << ", function("
                << (continues ? "continueStep" : "") << ")\n";
        }

        // A `lua` effect that names eventId gets the handler's own number (Xeen.useMirror(id, eventId, continueStep)).
        if (std::any_of(event.body.begin(), event.body.end(),
                [](const std::string &line) { return line.find("eventId") != std::string::npos; }))
        {
            lua << "    local eventId = " << event.eventId << "\n";
        }

        for (const std::string &line : event.body)
        {
            lua << "    " << line << "\n";
        }

        lua << (damageHook ? std::string("end)\n") : "end, " + title + ")\n");
    }

    return lua.str();
}

}

void writeNamedArrivals(JsonWriter &writer, const std::vector<MapArrival> &arrivals)
{
    writer.key("named_arrivals");
    writer.beginArray();

    for (const MapArrival &arrival : arrivals)
    {
        writer.beginObject();
        writer.field("name", arrival.name);
        writer.key("at");
        writer.beginArray();

        for (const int value : arrival.at)
        {
            writer.value(value);
        }

        writer.endArray();
        writer.field("facing", arrival.facing);
        writer.endObject();
    }

    writer.endArray();
}

namespace
{
void writeBuildJson(JsonWriter &writer, const BuildResult &result)
{
    writer.beginObject();
    writer.field("ok", result.issues.empty());
    writer.field("map", result.mapFile);
    writer.field("source_revision", result.sourceRevision);
    writer.field("lock_hash", result.lockHash);
    writer.key("counts");
    writer.beginObject();

    if (result.overlay)
    {
        writer.field("replaced_events", static_cast<uint64_t>(result.events));

        if (!result.sceneOverlayKeys.empty())
        {
            writer.field("scene_added", static_cast<uint64_t>(result.sceneAdded));
            writer.field("scene_changed", static_cast<uint64_t>(result.sceneChanged));
            writer.field("scene_removed", static_cast<uint64_t>(result.sceneRemoved));
            writer.key("scene_keys");
            writer.beginArray();

            for (const std::string &key : result.sceneOverlayKeys)
            {
                writer.value(key);
            }

            writer.endArray();
        }

        if (result.overlayCinematics)
        {
            writer.field("cinematics_added", static_cast<uint64_t>(result.cinematicsAdded));
            writer.field("cinematics_replaced", static_cast<uint64_t>(result.cinematicsReplaced));
        }
    }
    else
    {
        writer.field("sectors", static_cast<uint64_t>(result.sectors));
        writer.field("vertices", static_cast<uint64_t>(result.vertices));
        writer.field("faces", static_cast<uint64_t>(result.faces));
        writer.field("portals", static_cast<uint64_t>(result.portals));
        writer.field("doors", static_cast<uint64_t>(result.doors));
        writer.field("lights", static_cast<uint64_t>(result.lights));
        writer.field("spawns", static_cast<uint64_t>(result.spawns));
        writer.field("entities", static_cast<uint64_t>(result.entities));
        writer.field("events", static_cast<uint64_t>(result.events));
        writer.field("chests", static_cast<uint64_t>(result.chests));
    }

    writer.endObject();
    writeNamedArrivals(writer, result.arrivals);
    writer.key("warnings");
    writer.beginArray();

    for (const std::string &warning : result.warnings)
    {
        writer.value(warning);
    }

    writer.endArray();
    writer.endObject();
}

bool isIdReference(const YAML::Node &schema)
{
    if (!schema.IsDefined() || !schema.IsMap())
    {
        return false;
    }

    const YAML::Node reference = schema["$ref"];
    return reference.IsDefined() && reference.IsScalar()
        && reference.Scalar().find("#/$defs/id") != std::string::npos;
}

// Every map with an `id` declares that id. Collected over all the project's files: a plan refers to the map card's
// neighbours, rooms to the plan's spaces, wiring to objects.
void collectDeclaredIds(const YAML::Node &node, std::set<std::string> &ids)
{
    if (node.IsMap())
    {
        const YAML::Node id = node["id"];

        if (id.IsDefined() && id.IsScalar() && id.Scalar().find(':') != std::string::npos)
        {
            ids.insert(id.Scalar());
        }

        for (YAML::const_iterator iterator = node.begin(); iterator != node.end(); ++iterator)
        {
            collectDeclaredIds(iterator->second, ids);
        }
    }
    else if (node.IsSequence())
    {
        for (const YAML::Node &item : node)
        {
            collectDeclaredIds(item, ids);
        }
    }
}

// Walks a document beside its schema. A value whose schema is the shared id type, under any key but `id`, is a
// reference and must name something the project declares. Names of quest bits and items in conditions must be in
// the map card's tables.
class ReferenceCheck
{
public:
    // `ids` every id the project declares (its files' and its lock's), `qbits` and `items` the names the map card
    // declares.
    ReferenceCheck(const std::set<std::string> &ids, const std::set<std::string> &qbits,
        const std::set<std::string> &items, std::vector<ProjectIssue> &issues)
        : m_issues(issues)
        , m_ids(ids)
        , m_qbits(qbits)
        , m_items(items)
    {
    }

    // The references of one file (not the lock: its keys are ids the build wrote, not references).
    void run(const ProjectFile &file)
    {
        m_file = file.name;
        walk(file.document, SchemaSet::builtIn().root(file.schema), file.schema, "", "");
    }

    // The lock declares the base map's own things under their stable ids (door:d12, evt:e20, room:s3).
    static std::set<std::string> lockIdsOf(const Project &project)
    {
        std::set<std::string> ids;
        const YAML::Node lock = project.document("ids.lock.yml");

        if (lock.IsDefined() && lock.IsMap())
        {
            for (YAML::const_iterator table = lock.begin(); table != lock.end(); ++table)
            {
                if (!table->second.IsMap())
                {
                    continue;
                }

                for (YAML::const_iterator entry = table->second.begin(); entry != table->second.end(); ++entry)
                {
                    ids.insert(entry->first.Scalar());
                }
            }
        }

        return ids;
    }

    static void collectNames(const YAML::Node &table, std::set<std::string> &names)
    {
        if (!table.IsDefined() || !table.IsMap())
        {
            return;
        }

        for (YAML::const_iterator iterator = table.begin(); iterator != table.end(); ++iterator)
        {
            names.insert(iterator->first.Scalar());
        }
    }

private:
    void checkName(const YAML::Node &value, const std::string &key, const std::string &path)
    {
        if (!value.IsScalar() || classifyScalar(value) != ScalarKind::String)
        {
            return;
        }

        const std::set<std::string> &names = key == "qbit" ? m_qbits : m_items;

        // A list of numbers (item counts, tiers) names nothing.
        if (key == "items" && classifyScalar(value) != ScalarKind::String)
        {
            return;
        }


        if (!names.contains(value.Scalar()))
        {
            m_issues.push_back({m_file, path, "'" + value.Scalar() + "' is not declared in project.yml "
                + (key == "qbit" ? "qbits" : "items"), "reference"});
        }
    }

    void walk(
        const YAML::Node &value,
        const YAML::Node &unresolvedSchema,
        std::string schemaFile,
        const std::string &path,
        const std::string &key)
    {
        if (!unresolvedSchema.IsDefined())
        {
            return;
        }

        if (isIdReference(unresolvedSchema))
        {
            if (key != "id" && value.IsScalar() && !m_ids.contains(value.Scalar()))
            {
                m_issues.push_back({m_file, path, "nothing in the project has the id " + value.Scalar(), "reference"});
            }

            return;
        }

        const YAML::Node schema = SchemaSet::builtIn().resolve(unresolvedSchema, schemaFile);

        if (!schema.IsDefined() || !schema.IsMap())
        {
            return;
        }

        // A value may take one of several forms: follow each.
        for (const char *pKeyword : {"anyOf", "oneOf"})
        {
            const YAML::Node alternatives = schema[pKeyword];

            if (alternatives.IsDefined())
            {
                for (const YAML::Node &alternative : alternatives)
                {
                    walk(value, alternative, schemaFile, path, key);
                }
            }
        }

        if (value.IsMap())
        {
            const YAML::Node properties = schema["properties"];
            const YAML::Node additional = schema["additionalProperties"];

            for (YAML::const_iterator iterator = value.begin(); iterator != value.end(); ++iterator)
            {
                const std::string childKey = iterator->first.Scalar();
                const std::string childPath = path.empty() ? childKey : path + "." + childKey;

                // Names of quest bits and items, wherever they stand: conditions, treasure, drops, chest contents.
                const bool namesQbit = childKey == "qbit" && isConditionSchema(schema);
                // (An item on the floor, objects.yml `items[n].item`, may also bear its name of items.txt: the
                // lowering looks it up there, with the table.)
                const bool placedItem = childKey == "item" && m_file == "objects.yml" && path.rfind("items[", 0) == 0;
                const bool namesItem = (childKey == "item" && !placedItem) || childKey == "drops"
                    || childKey == "pool" || (childKey == "items" && iterator->second.IsSequence());

                if (namesQbit || namesItem)
                {
                    if (iterator->second.IsSequence())
                    {
                        const YAML::Node names = iterator->second;

                        for (const YAML::Node &name : names)
                        {
                            checkName(name, childKey, childPath);
                        }
                    }
                    else
                    {
                        checkName(iterator->second, childKey, childPath);
                    }
                }

                if (properties.IsDefined() && properties.IsMap() && properties[childKey].IsDefined())
                {
                    walk(iterator->second, properties[childKey], schemaFile, childPath, childKey);
                }
                else if (additional.IsDefined() && additional.IsMap())
                {
                    walk(iterator->second, additional, schemaFile, childPath, childKey);
                }
            }
        }
        else if (value.IsSequence())
        {
            const YAML::Node items = schema["items"];
            size_t index = 0;

            for (const YAML::Node &item : value)
            {
                walk(item, items, schemaFile, path + "[" + std::to_string(index++) + "]", key);
            }
        }
    }

    // A condition is the schema that has both `qbit` and `map_var` among its properties.
    static bool isConditionSchema(const YAML::Node &schema)
    {
        const YAML::Node properties = schema["properties"];
        return properties.IsDefined() && properties.IsMap() && properties["qbit"].IsDefined()
            && properties["map_var"].IsDefined();
    }

    std::vector<ProjectIssue> &m_issues;
    const std::set<std::string> &m_ids;
    const std::set<std::string> &m_qbits;
    const std::set<std::string> &m_items;
    std::string m_file;
};

// The references of every file but the lock, each file's issues apart, with the index they are checked against.
// With `pPrevious` and `pChanged`, a file that did not change keeps its issues when the index is the same.
void checkReferences(const Project &project, const ValidationParts *pPrevious, const std::set<std::string> *pChanged,
    ValidationParts &parts)
{
    const bool incremental = pPrevious != nullptr && pChanged != nullptr && pPrevious->valid;

    for (const std::pair<const std::string, ProjectFile> &entry : project.files)
    {
        std::set<std::string> &ids = parts.declaredIds[entry.first];

        if (incremental && !pChanged->contains(entry.first) && pPrevious->declaredIds.contains(entry.first))
        {
            ids = pPrevious->declaredIds.at(entry.first);
        }
        else
        {
            collectDeclaredIds(entry.second.document, ids);
        }
    }

    parts.lockIds = ReferenceCheck::lockIdsOf(project);
    const YAML::Node card = project.document("project.yml");
    ReferenceCheck::collectNames(childOf(card, "qbits"), parts.qbits);
    ReferenceCheck::collectNames(childOf(card, "items"), parts.items);
    const bool sameIndex = incremental && parts.declaredIds == pPrevious->declaredIds
        && parts.lockIds == pPrevious->lockIds && parts.qbits == pPrevious->qbits && parts.items == pPrevious->items;
    std::set<std::string> all = parts.lockIds;

    for (const std::pair<const std::string, std::set<std::string>> &file : parts.declaredIds)
    {
        all.insert(file.second.begin(), file.second.end());
    }

    for (const std::pair<const std::string, ProjectFile> &entry : project.files)
    {
        // The lock's keys are ids the build wrote, not references.
        if (entry.first == "ids.lock.yml")
        {
            continue;
        }

        std::vector<ProjectIssue> &issues = parts.referenceIssues[entry.first];

        if (sameIndex && !pChanged->contains(entry.first) && pPrevious->referenceIssues.contains(entry.first))
        {
            issues = pPrevious->referenceIssues.at(entry.first);
            continue;
        }

        ReferenceCheck(all, parts.qbits, parts.items, issues).run(entry.second);
    }
}

// The plan's own checks: spaces named once, a diagram that is there, every room realising a space.
void checkPlanSpaces(const Project &project, std::vector<ProjectIssue> &issues)
{
    std::set<std::string> spaces;
    const YAML::Node spaceList = childOf(project.document("plan.yml"), "spaces");

    if (spaceList.IsDefined())
    {
        for (const YAML::Node &space : spaceList)
        {
            if (!spaces.insert(textOf(space, "id", "")).second)
            {
                issues.push_back({"plan.yml", "spaces", "the id " + textOf(space, "id", "") + " is used twice",
                    "reference"});
            }
        }
    }

    // A diagram kept in a file must be there.
    const YAML::Node diagramFile = childOf(childOf(project.document("plan.yml"), "diagram"), "file");

    if (diagramFile.IsDefined() && diagramFile.IsScalar())
    {
        std::error_code error;

        if (!project.root.empty() && !std::filesystem::exists(project.root / diagramFile.Scalar(), error))
        {
            issues.push_back({"plan.yml", "diagram.file", "there is no file " + diagramFile.Scalar()
                + " in the project folder", "reference"});
        }
    }

    const YAML::Node rooms = childOf(project.document("rooms.yml"), "rooms");

    if (rooms.IsDefined() && !spaces.empty())
    {
        size_t index = 0;

        for (const YAML::Node &room : rooms)
        {
            const std::string path = "rooms[" + std::to_string(index++) + "]";
            const std::string space = textOf(room, "space", textOf(room, "id", ""));

            if (!spaces.contains(space))
            {
                issues.push_back({"rooms.yml", path, "the room realises no space of plan.yml (" + space
                    + " is not there); name its space with `space`", "reference"});
            }
        }
    }
}

// The reference issues file by file in the order of the project's files, then the plan's own checks.
void appendReferenceIssues(const Project &project, const ValidationParts &parts, std::vector<ProjectIssue> &issues)
{
    for (const std::pair<const std::string, ProjectFile> &entry : project.files)
    {
        const std::map<std::string, std::vector<ProjectIssue>>::const_iterator found =
            parts.referenceIssues.find(entry.first);

        if (found != parts.referenceIssues.end())
        {
            issues.insert(issues.end(), found->second.begin(), found->second.end());
        }
    }

    checkPlanSpaces(project, issues);
}

// What a project's files refer to must exist in the project (indoor and outdoor alike), and a room must realise a
// space of the plan.
void validatePlanReferences(const Project &project, std::vector<ProjectIssue> &issues)
{
    ValidationParts parts;
    checkReferences(project, nullptr, nullptr, parts);
    appendReferenceIssues(project, parts, issues);
}

std::string dataTable(const BuildOptions &options, const char *pFileName)
{
    std::string text;

    // A mount's own copy of a table stands in front of the asset root's, as in the game.
    if (!options.mountRoot.empty() && readTextFile(options.mountRoot / "engine" / "data_tables" / pFileName, text))
    {
        return text;
    }

    if (!options.assetRoot.empty())
    {
        readTextFile(options.assetRoot / "engine" / "data_tables" / pFileName, text);
    }

    return text;
}

// The tables the lowering looks names up in: the options' kept ones, or read from the asset root (each empty without
// one), with the rows and relations of the project's world (addWorldTableRows).
LoweringOptions loweringOptionsOf(const BuildOptions &options, const std::string &world = {})
{
    if (options.lowering)
    {
        LoweringOptions kept = *options.lowering;
        kept.mountRoot = options.mountRoot;
        return kept;
    }

    LoweringOptions lowering;
    lowering.decorationTableText = dataTable(options, "decoration_data.txt");
    lowering.monsterTableText = dataTable(options, "monster_data.txt");
    lowering.monsterDescriptorTableText = dataTable(options, "monster_descriptors.txt");
    lowering.itemTableText = dataTable(options, "items.txt");
    lowering.objectTableText = dataTable(options, "object_list.txt");
    lowering.assetRoot = options.assetRoot;
    lowering.mountRoot = options.mountRoot;

    if (!options.assetRoot.empty())
    {
        lowering.uniqueNameTableText = dataTable(options, "english/place_mon.txt");
        lowering.relationTableText = dataTable(options, "hostile.txt");
        lowering.mapStatsTableText = dataTable(options, "map_stats.txt");
        readTextFile(options.assetRoot / "engine" / "liquids" / "liquids.yml", lowering.liquidTableText);
        // The 3D models dungeons draw decorations with (their heights, where a hanging one's top is).
        readTextFile(
            options.assetRoot / "engine" / "models" / "indoor_decorations.yml", lowering.indoorModelBindingsText);
        addWorldTableRows(options.assetRoot, world, lowering);
    }

    return lowering;
}
}

namespace
{
// The Lua overlay of a project that changes a shipped map: each wiring event under the number of the base map's
// event it replaces. The game appends the file to the map's script (events/maps/<base stem>_<project id>.lua).
std::string writeOverlayLuaText(const Project &project, const LoweredIndoorMap &lowered)
{
    const YAML::Node card = project.document("project.yml");
    std::ostringstream lua;
    lua << "-- Generated by oymap build from the Map Studio project \"" << textOf(card, "id", "")
        << "\": an overlay of "
        << textOf(card, "base", "") << ". Change the project (wiring.yml), not this file.\n";
    lua << "do\n";
    // Only the handler is replaced: the event keeps its place in the map's load, leave and timer lists, its chest
    // and context metadata, and (unless the project gives a title) its title and hint. ReplaceMapEvent would drop
    // the event's timers.
    lua << "    local function replaceHandler(eventId, title, handler)\n";
    lua << "        evt.map[eventId] = function(...)\n";
    lua << "            evt._BeginEvent(eventId)\n";
    lua << "            handler(...)\n";
    lua << "        end\n";
    lua << "        if title ~= nil then\n";
    lua << "            evt.meta.map.title[eventId] = title\n";
    lua << "            evt.meta.map.hint[eventId] = title\n";
    lua << "        end\n";
    lua << "    end\n";

    for (const LoweredEvent &event : lowered.events)
    {
        lua << "\n    -- " << event.id << "\n";
        lua << "    replaceHandler(" << event.eventId << ", " << (event.title.empty() ? "nil" : jsonQuote(event.title))
            << ", function()\n";

        for (const std::string &line : event.body)
        {
            lua << "        " << line << "\n";
        }

        lua << "    end)\n";
    }

    lua << "end\n";
    return lua.str();
}

bool buildOverlay(const Project &project, const BuildOptions &options, BuildResult &result)
{
    LoweredIndoorMap lowered;
    checkSceneOverlayWords(project, result.issues);
    const YAML::Node card = project.document("project.yml");
    const std::string stem = std::filesystem::path(textOf(card, "base", "")).stem().string();
    // The base map, read from the asset root when there is one: its script, scene and cinematics, and the numbers the
    // overlay's own monsters take after its actors (S8a).
    std::optional<AssetSession> session;
    LoadedMap map;
    std::optional<std::string> baseScene;
    LoweringOptions loweringOptions = loweringOptionsOf(options, textOf(card, "world", ""));

    if (!options.assetRoot.empty())
    {
        std::string errorMessage;
        session.emplace();

        if (!session->open(options.assetRoot, textOf(card, "world", ""), errorMessage)
            || !loadMap(*session, textOf(card, "base", ""), map, errorMessage))
        {
            result.issues.push_back({"project.yml", "base", errorMessage, "reference"});
            return false;
        }

        baseScene = session->files().readTextFile("Data/games/" + stem + ".scene.yml");

        if (baseScene)
        {
            readOverlayBase(project, *session, map, *baseScene, loweringOptions);
        }
    }

    if (!lowerOverlayProject(project, loweringOptions, lowered, result.issues) || !result.issues.empty())
    {
        return false;
    }

    // What the lowering warns of (an added monster's name the game shows only on its corpse, one that stays hidden).
    result.warnings.insert(result.warnings.end(), lowered.warnings.begin(), lowered.warnings.end());

    const std::string fileName = lowered.mapStem + "_" + textOf(card, "id", "overlay") + ".lua";
    const std::string sceneFileName = lowered.mapStem + "_" + textOf(card, "id", "overlay") + ".scene.yml";
    const std::string cinematicsFileName = lowered.mapStem + "_" + textOf(card, "id", "overlay") + ".cinematics.yml";
    const std::string luaText = writeOverlayLuaText(project, lowered);
    const bool changesScene = projectChangesScene(project);
    // The overlay's cinematics (wiring.yml `cinematics`): the game merges them by name after the map's own (S8a).
    std::string cinematicsText;

    if (!writeCinematicsText(project, lowered, cinematicsText, result.issues))
    {
        return false;
    }

    const bool writesCinematics = !cinematicsText.empty();
    // An overlay that changes only the scene or the cinematics has no script; one that changes nothing writes the
    // script as before.
    const bool writesLua = !lowered.events.empty() || (!changesScene && !writesCinematics);
    result.mapFile = textOf(card, "base", "");
    result.events = lowered.events.size();
    result.overlay = true;
    IdsLock lock = lowered.ids;
    SceneOverlayText scene;

    // With an asset root at hand, the base map's script with the overlay appended must still run, and every
    // replaced event must be one the base map has.
    if (session)
    {
        std::string errorMessage;

        for (const LoweredEvent &event : lowered.events)
        {
            if (map.events && !map.events->hasEvent(static_cast<uint16_t>(event.eventId))
                && !map.events->getHint(static_cast<uint16_t>(event.eventId)))
            {
                result.issues.push_back({"wiring.yml", "", event.id + " replaces event "
                    + std::to_string(event.eventId) + ", which " + result.mapFile + " does not have", "reference"});
            }
        }

        map.fullScriptSource += "\n\n-- map overlay: " + fileName + "\n" + luaText;
        std::string flowJson;

        if (!exploreEventHandlers(map, flowJson, errorMessage))
        {
            result.issues.push_back({"wiring.yml", "", "with the overlay " + errorMessage, "build"});
        }

        // The overlay's own handlers must call the game's functions with usable arguments on every path.
        std::vector<int> replaced;

        for (const LoweredEvent &event : lowered.events)
        {
            replaced.push_back(event.eventId);
        }

        for (const std::string &problem : eventFlowProblems(flowJson, replaced))
        {
            result.issues.push_back({"wiring.yml", "", problem, "script"});
        }

        // The scene overlay (S6_PLAN.md item O): from the base map's own scene, then read by the game's overlay
        // reader over the base scene, as the game will.
        if (changesScene)
        {
            if (!map.indoor || !baseScene)
            {
                result.issues.push_back({"project.yml", "base", result.mapFile + " has no indoor scene an overlay "
                    "could change", "reference"});
                return false;
            }

            if (!buildSceneOverlayText(project, *baseScene, *map.indoor, lowered, lock, scene, result.issues,
                    result.warnings))
            {
                return false;
            }

            const Game::IndoorSceneYmlLoader loader;
            std::string sceneError;
            std::optional<Game::IndoorSceneData> checked = loader.loadFromText(*baseScene, sceneError);

            if (!checked || !loader.applyOverlayFromText(*checked, scene.text, sceneError))
            {
                result.issues.push_back({"objects.yml", "scene", "the game refuses the scene overlay: " + sceneError,
                    "build"});
                return false;
            }

            Game::MapDeltaData state;

            if (!Game::buildIndoorMapStateFromScene(*checked, *map.indoor, state, sceneError))
            {
                result.issues.push_back({"objects.yml", "scene", "the base map with the overlay does not load: "
                    + sceneError, "build"});
                return false;
            }
        }

        // Which of the overlay's cinematics replace the map's own (the same name) and which are new.
        if (writesCinematics)
        {
            const std::vector<std::string> baseNames = baseCinematicNames(*session, stem);
            result.overlayCinematics = true;

            for (const YAML::Node &cinematic : childOf(project.document("wiring.yml"), "cinematics"))
            {
                const std::string name = cinematicName(textOf(cinematic, "id", ""));
                const bool replaces = std::find(baseNames.begin(), baseNames.end(), name) != baseNames.end();
                ++(replaces ? result.cinematicsReplaced : result.cinematicsAdded);
            }
        }

        if (lowered.events.empty() && !changesScene && !writesCinematics)
        {
            result.warnings.push_back("the project replaces no event of " + result.mapFile + ": nothing to build");
        }

        if (!result.issues.empty())
        {
            return false;
        }
    }
    else if (changesScene)
    {
        result.issues.push_back({"objects.yml", "scene", "an overlay that changes the scene is built with the asset "
            "root (--assets): it is written from the base map's scene", "build"});
        return false;
    }
    else
    {
        result.warnings.push_back("built without --assets: the overlay was not run against the base map's script");
    }

    const std::string lockText =
        writeCanonicalYaml(lock.toDocument(), SchemaSet::builtIn(), "ids_lock.schema.json");
    const std::map<std::string, ProjectFile>::const_iterator overlayLock = project.files.find("ids.lock.yml");
    // An overlay's lock keeps every entry: the base map's numbers, and its own things' once given.
    const bool lockChanged = changesScene
        && (overlayLock == project.files.end() || overlayLock->second.text != lockText);
    result.lockChanged = lockChanged;

    if (options.dryRun)
    {
        return true;
    }

    const std::filesystem::path outputDirectory =
        options.outputDirectory.empty() ? project.root / "build" : options.outputDirectory;
    result.sourceRevision = projectRevision(project);
    result.lockHash = lockChanged ? lockHashOfText(&lockText)
        : lockHashOfText(overlayLock == project.files.end() ? nullptr : &overlayLock->second.text);
    result.sceneOverlayKeys = scene.keys;
    result.sceneAdded = scene.added;
    result.sceneChanged = scene.changed;
    result.sceneRemoved = scene.removed;
    JsonWriter buildJson(true);
    writeBuildJson(buildJson, result);
    std::string buildJsonText = buildJson.take();
    buildJsonText.push_back('\n');
    std::string errorMessage;
    std::error_code removeError;
    bool lockWritten = false;
    const bool ownBuild = options.outputDirectory.empty();

    // A file the project no longer makes leaves the build folder, so that install does not copy an old one.
    if (!writesLua)
    {
        std::filesystem::remove(outputDirectory / fileName, removeError);
    }

    if (!changesScene)
    {
        std::filesystem::remove(outputDirectory / sceneFileName, removeError);
    }

    if (!writesCinematics)
    {
        std::filesystem::remove(outputDirectory / cinematicsFileName, removeError);
    }

    if ((writesLua && !writeTextFileAtomically(outputDirectory / fileName, luaText, errorMessage))
        || (changesScene && !writeTextFileAtomically(outputDirectory / sceneFileName, scene.text, errorMessage))
        || (writesCinematics
            && !writeTextFileAtomically(outputDirectory / cinematicsFileName, cinematicsText, errorMessage))
        || !writeTextFileAtomically(outputDirectory / "build.json", buildJsonText, errorMessage)
        || (lockChanged && !writeLockRecord(project.root, lockText, result.sourceRevision, "build", lockWritten,
            errorMessage))
        || (lockChanged && !ownBuild && !writeTextFileAtomically(outputDirectory / "ids.lock.yml", lockText,
            errorMessage)))
    {
        result.issues.push_back({"", "", errorMessage, "io"});
        return false;
    }

    result.files.clear();

    if (writesLua)
    {
        result.files.push_back(fileName);
    }

    if (changesScene)
    {
        result.files.push_back(sceneFileName);
    }

    if (writesCinematics)
    {
        result.files.push_back(cinematicsFileName);
    }

    result.files.push_back("build.json");
    return true;
}
}

std::string missingWorldNote(const Project &project, const std::filesystem::path &assetRoot)
{
    const std::string world = textOf(project.document("project.yml"), "world", "");
    std::error_code error;

    if (assetRoot.empty() || world.empty() || std::filesystem::is_directory(assetRoot / "worlds" / world, error))
    {
        return "";
    }

    return "the asset root has no world '" + world + "' (no worlds/" + world + " folder). "
        "The project's files check and build, but `oymap render`, `solve`, `audit`, `metrics`, `compare` and `export` "
        "of the project, `oymap install` and the game read a map through its world's package and will refuse this "
        "one. Until that world exists, build under a world the root has (`world: mm7` in project.yml, one line to "
        "change back) and note in the project what stands in for what";
}

LoweringOptions readLoweringOptions(const std::filesystem::path &assetRoot)
{
    BuildOptions options;
    options.assetRoot = assetRoot;
    LoweringOptions lowering = loweringOptionsOf(options);
    lowering.tables = parseLoweringTables(lowering);
    return lowering;
}

namespace
{
// --- the lowering that skips (S5_BROWSER_EDITOR.md 2.4.2) ----------------------------------------------------------

// The files whose objects the indoor lowering reads: an object of these with an error is left out of a view build.
// The files the lowering builds from, whose listed objects a view build may leave out (2.4.2): the indoor files,
// and an outdoor project's sketch (its structures, scatter, areas, actors, events: per structure, S5b2).
const char *const LoweredFiles[] = {"rooms.yml", "objects.yml", "wiring.yml", "sketch.yml"};

bool isLoweredFile(const std::string &name)
{
    return std::any_of(std::begin(LoweredFiles), std::end(LoweredFiles),
        [&name](const char *pName) { return name == pName; });
}

// The object an issue's path names ("rooms[3].outline" in rooms.yml: rooms[3]'s id). False for an issue that names no
// object of a lowered file (the file as a whole, the map card, a value outside the lists).
bool objectOfIssue(const Project &project, const ProjectIssue &issue, std::string &id)
{
    if (!isLoweredFile(issue.file) || !project.has(issue.file))
    {
        return false;
    }

    const size_t open = issue.path.find('[');
    const size_t close = issue.path.find(']');

    if (open == std::string::npos || close == std::string::npos || close < open || open == 0
        || issue.path.find('.') < open)
    {
        return false;
    }

    const std::string list = issue.path.substr(0, open);
    const std::string number = issue.path.substr(open + 1, close - open - 1);

    if (number.empty() || !std::all_of(number.begin(), number.end(), [](char letter) { return std::isdigit(letter); }))
    {
        return false;
    }

    const YAML::Node items = childOf(project.document(issue.file), list.c_str());
    const size_t index = static_cast<size_t>(std::stoul(number));

    if (!items.IsDefined() || !items.IsSequence() || index >= items.size())
    {
        return false;
    }

    id = textOf(items[index], "id", "");
    return !id.empty();
}

bool mentionsAny(const YAML::Node &node, const std::set<std::string> &ids)
{
    if (node.IsScalar())
    {
        return ids.contains(node.Scalar());
    }

    if (node.IsMap())
    {
        for (YAML::const_iterator iterator = node.begin(); iterator != node.end(); ++iterator)
        {
            if (mentionsAny(iterator->second, ids))
            {
                return true;
            }
        }
    }
    else if (node.IsSequence())
    {
        for (const YAML::Node &item : node)
        {
            if (mentionsAny(item, ids))
            {
                return true;
            }
        }
    }

    return false;
}

// The project without the objects `left` names, and without every object of the lowered files that names one of them
// (an opening into a room left out, the door in it, the event that opens the door, a light standing in the room).
// `left` grows by those; `because` says why each dependent went.
Project projectWithout(const Project &project, std::set<std::string> &left, std::map<std::string, std::string> &because)
{
    // Dependents, until nothing more goes.
    bool grew = true;

    while (grew)
    {
        grew = false;

        for (const char *pFile : LoweredFiles)
        {
            const YAML::Node document = project.document(pFile);

            if (!document.IsDefined() || !document.IsMap())
            {
                continue;
            }

            for (YAML::const_iterator list = document.begin(); list != document.end(); ++list)
            {
                // A copy of the node: `list->second` lives in a temporary the loop would outlive.
                const YAML::Node items = list->second;

                if (!items.IsSequence())
                {
                    continue;
                }

                for (const YAML::Node &item : items)
                {
                    const std::string id = textOf(item, "id", "");

                    if (id.empty() || left.contains(id) || !mentionsAny(item, left))
                    {
                        continue;
                    }

                    // The first id it names that is left out.
                    for (const std::string &other : left)
                    {
                        if (mentionsAny(item, std::set<std::string>{other}))
                        {
                            because[id] = other;
                            break;
                        }
                    }

                    left.insert(id);
                    grew = true;
                }
            }
        }
    }

    Project reduced = project;

    for (const char *pFile : LoweredFiles)
    {
        const std::map<std::string, ProjectFile>::const_iterator file = project.files.find(pFile);

        if (file == project.files.end() || !file->second.document.IsMap())
        {
            continue;
        }

        // A new tree (the project's own is shared with the caller's).
        YAML::Node document(YAML::NodeType::Map);

        for (YAML::const_iterator entry = file->second.document.begin(); entry != file->second.document.end(); ++entry)
        {
            const YAML::Node value = entry->second;

            if (!value.IsSequence())
            {
                document[entry->first.Scalar()] = YAML::Clone(value);
                continue;
            }

            YAML::Node kept(YAML::NodeType::Sequence);

            for (const YAML::Node &item : value)
            {
                if (!left.contains(textOf(item, "id", "")))
                {
                    kept.push_back(YAML::Clone(item));
                }
            }

            document[entry->first.Scalar()] = kept;
        }

        const ProjectFile replaced{file->second.name, file->second.schema, file->second.text, document};
        reduced.files.erase(pFile);
        reduced.files.emplace(pFile, replaced);
    }

    return reduced;
}

bool sameIssue(const ProjectIssue &left, const ProjectIssue &right)
{
    return left.file == right.file && left.path == right.path && left.message == right.message;
}

// The view build of a project the full lowering refused (2.4.2): the objects the errors name are left out, with
// what depends on them, and the rest is lowered; again while new errors name objects, a few rounds at most. Gives
// the lowered map of the rest (null when an error names no object, or nothing could be lowered), adds the errors the
// rounds found that the full lowering had not reached, and one note per object left out.
// `lower` lowers a reduced project, adding what it finds to its issues; true when it lowered (the caller keeps what
// it made of the last call).
bool skippingRounds(
    const Project &project,
    const std::vector<ProjectIssue> &known,
    size_t firstIssue,
    ValidationViews &views,
    const std::function<bool(const Project &, std::vector<ProjectIssue> &)> &lower)
{
    std::vector<std::string> &skipped = views.skipped;
    // The issues known so far and those the rounds add; what is added goes to the view, not the validation.
    std::vector<ProjectIssue> issues = known;
    const size_t knownCount = issues.size();
    const auto keep = [&issues, &views, knownCount]()
    {
        views.skippedIssues.assign(issues.begin() + static_cast<std::ptrdiff_t>(knownCount), issues.end());
    };

    std::set<std::string> left;
    std::map<std::string, std::string> because;
    // The first error that names each object: what its note says.
    std::map<std::string, std::string> firstError;
    size_t from = firstIssue;

    for (int round = 0; round < 6; ++round)
    {
        bool attributed = false;
        bool unattributed = false;

        for (size_t index = from; index < issues.size(); ++index)
        {
            // The plan is not lowered: its errors do not stop a view.
            if (!issues[index].isError() || issues[index].file == "plan.yml")
            {
                continue;
            }

            std::string id;

            if (objectOfIssue(project, issues[index], id))
            {
                attributed = attributed || left.insert(id).second;
                firstError.emplace(id, issues[index].message);
            }
            else
            {
                unattributed = true;
            }
        }

        if (unattributed || !attributed)
        {
            return false;
        }

        const Project reduced = projectWithout(project, left, because);
        std::vector<ProjectIssue> found;
        const bool clean = lower(reduced, found)
            && std::none_of(found.begin(), found.end(), [](const ProjectIssue &issue) { return issue.isError(); });

        // The rounds' errors that the full lowering did not reach (it stops at its first stage with an error). Their
        // paths are positions in the reduced files: only errors whose object is still there are kept.
        from = issues.size();

        for (const ProjectIssue &issue : found)
        {
            std::string id;

            if (issue.isError() && objectOfIssue(reduced, issue, id))
            {
                // Named by the full project's position of the object.
                ProjectIssue placed = issue;
                const YAML::Node items = childOf(project.document(issue.file),
                    issue.path.substr(0, issue.path.find('[')).c_str());

                for (size_t position = 0; items.IsDefined() && position < items.size(); ++position)
                {
                    if (textOf(items[position], "id", "") == id)
                    {
                        placed.path = issue.path.substr(0, issue.path.find('[')) + "[" + std::to_string(position)
                            + issue.path.substr(issue.path.find(']'));
                    }
                }

                if (std::none_of(issues.begin(), issues.end(),
                        [&placed](const ProjectIssue &known) { return sameIssue(known, placed); }))
                {
                    issues.push_back(placed);
                }
            }
            else if (issue.isError())
            {
                return false;
            }
        }

        if (!clean && from == issues.size())
        {
            return false;
        }

        if (clean)
        {
            for (const std::string &id : left)
            {
                std::string file = "rooms.yml";
                std::string path;

                for (const char *pFile : LoweredFiles)
                {
                    const YAML::Node document = project.document(pFile);

                    for (YAML::const_iterator list = document.begin(); document.IsMap() && list != document.end();
                         ++list)
                    {
                        const YAML::Node items = list->second;

                        for (size_t position = 0; items.IsSequence() && position < items.size(); ++position)
                        {
                            if (textOf(items[position], "id", "") == id)
                            {
                                file = pFile;
                                path = list->first.Scalar() + "[" + std::to_string(position) + "]";
                            }
                        }
                    }
                }

                const std::map<std::string, std::string>::const_iterator reason = because.find(id);
                const std::map<std::string, std::string>::const_iterator error = firstError.find(id);
                issues.push_back({file, path, id + " is left out of the view until "
                    + (reason != because.end() ? "the errors of " + reason->second + " are fixed (it names it)"
                        : error != firstError.end() ? "this is fixed: " + error->second
                        : std::string("its errors are fixed")), "skipped", IssueSeverity::Note});
                skipped.push_back(id);
            }

            keep();
            return true;
        }
    }

    return false;
}

std::shared_ptr<LoweredIndoorMap> lowerSkipping(
    const Project &project,
    const LoweringOptions &options,
    const std::vector<ProjectIssue> &known,
    size_t firstIssue,
    ValidationViews &views)
{
    std::shared_ptr<LoweredIndoorMap> lowered;
    const bool made = skippingRounds(project, known, firstIssue, views,
        [&lowered, &options](const Project &reduced, std::vector<ProjectIssue> &found)
        {
            lowered = std::make_shared<LoweredIndoorMap>();
            return lowerIndoorProject(reduced, options, *lowered, found);
        });
    return made ? lowered : nullptr;
}

// The outdoor view build (2.4.2, per structure): a dry build of the sketch without the objects the errors name.
std::shared_ptr<OutdoorView> outdoorSkipping(
    const Project &project,
    const BuildOptions &options,
    const std::vector<ProjectIssue> &known,
    size_t firstIssue,
    ValidationViews &views)
{
    std::shared_ptr<OutdoorView> view;
    const bool made = skippingRounds(project, known, firstIssue, views,
        [&view, &options](const Project &reduced, std::vector<ProjectIssue> &found)
        {
            view = std::make_shared<OutdoorView>();
            BuildOptions viewOptions = options;
            viewOptions.pOutdoorView = view.get();
            viewOptions.commitCheck = true;
            return validateOutdoorProject(reduced, viewOptions, found);
        });
    return made ? view : nullptr;
}
}

void validateProject(const Project &project, const BuildOptions &options, std::vector<ProjectIssue> &issues)
{
    ValidationParts parts;
    validateProjectParts(project, options, nullptr, nullptr, parts, issues, nullptr);
}

void validateProjectParts(
    const Project &project,
    const BuildOptions &options,
    const ValidationParts *pPrevious,
    const std::set<std::string> *pChanged,
    ValidationParts &parts,
    std::vector<ProjectIssue> &issues,
    ValidationViews *pViews)
{
    parts = {};
    const size_t issuesBefore = issues.size();
    const bool incremental = pPrevious != nullptr && pChanged != nullptr && pPrevious->valid;

    // The schemas, file by file: a file that did not change keeps its issues.
    for (const std::pair<const std::string, ProjectFile> &entry : project.files)
    {
        std::vector<ProjectIssue> &fileIssues = parts.schemaIssues[entry.first];

        if (incremental && !pChanged->contains(entry.first) && pPrevious->schemaIssues.contains(entry.first))
        {
            fileIssues = pPrevious->schemaIssues.at(entry.first);
        }
        else
        {
            validateFileSchema(entry.second, fileIssues);
        }

        issues.insert(issues.end(), fileIssues.begin(), fileIssues.end());
    }

    if (issues.size() != issuesBefore)
    {
        // Schema issues end the check before the references are read: what was found so far is kept per file. An
        // indoor project whose schema errors all name objects of the lowered files is still lowered for its view,
        // without those objects (2.4.2): a view build, never installed.
        parts.valid = false;
        const YAML::Node card = project.document("project.yml");

        if (pViews != nullptr && textOf(card, "kind", "") == "indoor" && !childOf(card, "base").IsDefined()
            && project.has("rooms.yml"))
        {
            pViews->indoor = lowerSkipping(project, loweringOptionsOf(options, textOf(card, "world", "")), issues,
                issuesBefore, *pViews);
        }
        else if (pViews != nullptr && textOf(card, "kind", "") == "outdoor" && !childOf(card, "base").IsDefined()
            && project.has("sketch.yml"))
        {
            pViews->outdoor = outdoorSkipping(project, options, issues, issuesBefore, *pViews);
        }

        return;
    }

    // Whether an error was found since the start: warnings (the outdoor sketch's) do not stop the lowering.
    const auto errorSinceStart = [&issues, issuesBefore]()
    {
        return std::any_of(issues.begin() + static_cast<std::ptrdiff_t>(issuesBefore), issues.end(),
            [](const ProjectIssue &issue) { return issue.isError(); });
    };

    checkReferences(project, pPrevious, pChanged, parts);
    parts.valid = true;
    appendReferenceIssues(project, parts, issues);

    // Words on the wrong kind: warnings, file by file (a file that did not change keeps its findings).
    for (const std::pair<const std::string, ProjectFile> &entry : project.files)
    {
        if (!isSourceFile(entry.first))
        {
            continue;
        }

        std::vector<ProjectIssue> &fileIssues = parts.kindIssues[entry.first];

        if (incremental && !pChanged->contains(entry.first) && pPrevious->kindIssues.contains(entry.first))
        {
            fileIssues = pPrevious->kindIssues.at(entry.first);
        }
        else
        {
            checkWordKinds(entry.second, fileIssues);
        }

        issues.insert(issues.end(), fileIssues.begin(), fileIssues.end());
    }
    validateSketch(project, issues);
    const std::string kind = textOf(project.document("project.yml"), "kind", "");
    checkSceneOverlayWords(project, issues);

    // rules.no_spells is written into a new map's scene (S8g); an overlay project writes no scene of its map.
    if (childOf(project.document("project.yml"), "base").IsDefined()
        && textOf(childOf(project.document("project.yml"), "rules"), "no_spells", "") == "true")
    {
        issues.push_back({"project.yml", "rules.no_spells", "`no_spells` is written into a new map's scene; an overlay "
            "project does not write its base map's scene restrictions", "schema"});
    }

    if (childOf(project.document("project.yml"), "base").IsDefined())
    {
        // (With the asset root's tables: an overlay may add monsters and items, S8a.)
        LoweredIndoorMap lowered;
        const size_t before = issues.size();
        LoweringOptions overlayOptions =
            loweringOptionsOf(options, textOf(project.document("project.yml"), "world", ""));

        if (lowerOverlayProject(project, overlayOptions, lowered, issues) && issues.size() == before)
        {
            std::string cinematicsText;
            writeCinematicsText(project, lowered, cinematicsText, issues);
        }
    }
    else if (kind == "indoor" && project.has("rooms.yml"))
    {
        std::shared_ptr<LoweredIndoorMap> lowered = std::make_shared<LoweredIndoorMap>();
        const LoweringOptions loweringOptions =
            loweringOptionsOf(options, textOf(project.document("project.yml"), "world", ""));
        const size_t before = issues.size();

        const bool loweredWell = lowerIndoorProject(project, loweringOptions, *lowered, issues)
            && issues.size() == before;

        // The cinematics are checked against the lowered map (their objects' places, events, monsters).
        if (loweredWell)
        {
            std::string cinematicsText;
            writeCinematicsText(project, *lowered, cinematicsText, issues);
        }

        if (loweredWell && issues.size() == before && pViews != nullptr)
        {
            pViews->indoor = lowered;
        }
        else if (pViews != nullptr && issues.size() != before)
        {
            // The lowering stopped at an object it cannot lower: the view is built without it (2.4.2).
            pViews->indoor = lowerSkipping(project, loweringOptions, issues, before, *pViews);
        }
    }
    else if (kind == "outdoor" && !errorSinceStart())
    {
        // With the asset root, as the build: one dry build checks what the build would look up there too.
        std::shared_ptr<OutdoorView> view = pViews != nullptr ? std::make_shared<OutdoorView>() : nullptr;
        BuildOptions outdoorOptions = options;
        outdoorOptions.pOutdoorView = view.get();
        const size_t before = issues.size();

        if (validateOutdoorProject(project, outdoorOptions, issues) && view)
        {
            pViews->outdoor = view;
        }
        else if (pViews != nullptr && errorSinceStart())
        {
            // The dry build stopped at an object it cannot build: the view is built without it (2.4.2).
            pViews->outdoor = outdoorSkipping(project, options, issues, before, *pViews);
        }
    }
    else if (kind == "outdoor" && pViews != nullptr && project.has("sketch.yml"))
    {
        // Errors the reference checks found: a view build without the objects they name.
        pViews->outdoor = outdoorSkipping(project, options, issues, issuesBefore, *pViews);
    }
}

bool buildProject(const Project &project, const BuildOptions &options, BuildResult &result)
{
    result = {};
    validateProjectSchemas(project, result.issues);

    if (!result.issues.empty())
    {
        return false;
    }

    validatePlanReferences(project, result.issues);
    checkProjectGround(project, result.issues);
    const YAML::Node card = project.document("project.yml");


    if (childOf(card, "base").IsDefined())
    {
        return buildOverlay(project, options, result);
    }

    if (textOf(card, "kind", "") == "outdoor")
    {
        return !result.issues.empty() ? false : buildOutdoorProject(project, options, result);
    }

    if (textOf(card, "kind", "") != "indoor")
    {
        result.issues.push_back({"project.yml", "kind", "oymap build compiles new indoor and outdoor maps and "
            "overlays of any map", "unsupported"});
        return false;
    }

    LoweredIndoorMap lowered;
    const LoweringOptions loweringOptions = loweringOptionsOf(options, textOf(card, "world", ""));

    if (!lowerIndoorProject(project, loweringOptions, lowered, result.issues) || !result.issues.empty())
    {
        return false;
    }

    const std::filesystem::path outputDirectory =
        options.outputDirectory.empty() ? project.root / "build" : options.outputDirectory;
    const std::string stem = lowered.mapStem;
    result.mapFile = stem + ".blv";
    const std::vector<uint8_t> glb = writeGlb(lowered.nodes, "oymap");
    Editor::normalizeIndoorGeometryMetadata(lowered.metadata, result.mapFile);
    // The metadata is handed to the compiler in memory and not written beside the mesh: its serialiser uses
    // yaml-cpp's Emitter, which leaves a broken exit handler under Emscripten (PLAN.md section 13, "Toolchain").
    // The compiler reads its mesh from a file. A dry run uses a scratch name beside the output and removes it.
    const std::filesystem::path sourceDirectory = outputDirectory / "source";
    const std::filesystem::path glbPath = sourceDirectory / (stem + ".glb");
    std::string errorMessage;

    if (!writeBinaryFileAtomically(glbPath, glb, errorMessage))
    {
        result.issues.push_back({"", "", errorMessage, "io"});
        return false;
    }

    Editor::IndoorSourceGeometryCompileResult compiled;

    if (!Editor::compileIndoorSourceGeometry(glbPath, lowered.metadata, compiled, errorMessage))
    {
        result.issues.push_back({"rooms.yml", "", "the indoor compiler refused the lowered map: " + errorMessage,
            "compile"});
        return false;
    }

    joinDoorRecords(compiled);
    anchorMovingFaceTextures(compiled);
    std::vector<std::string> liquidWarnings;
    applySurfaceFaceBits(lowered.nodes, compiled.indoorGeometry,
        readLiquidTextures(loweringOptions.liquidTableText, textOf(card, "world", "")), liquidWarnings);
    const std::map<GlbFaceTranslucency, std::vector<uint16_t>> translucentFaces =
        findTranslucentFaces(lowered.nodes, compiled.indoorGeometry, liquidWarnings);

    // Lights that start dark (objects.yml lights[].on: false): the map holds them switched off (the engine's
    // "disabled" bit of a BLV light, 0x08) until evt.SetLight names them by their id. The compiler has no word
    // for it, so it is set on its result.
    for (Game::IndoorLight &light : compiled.indoorGeometry.lights)
    {
        if (std::find(lowered.darkLights.begin(), lowered.darkLights.end(), light.id) != lowered.darkLights.end())
        {
            light.attributes = static_cast<int16_t>(light.attributes | 0x08);
        }
    }

    result.warnings = compiled.warnings;

    for (const std::string &placeholder : lowered.placeholders)
    {
        result.warnings.push_back("placeholder not built: " + placeholder);
    }

    result.warnings.insert(result.warnings.end(), lowered.warnings.begin(), lowered.warnings.end());
    result.warnings.insert(result.warnings.end(), liquidWarnings.begin(), liquidWarnings.end());

    if (const std::string note = missingWorldNote(project, options.assetRoot); !note.empty())
    {
        result.warnings.push_back(note);
    }

    const Game::IndoorMapData &map = compiled.indoorGeometry;
    result.sectors = map.sectors.size();
    result.vertices = map.vertices.size();
    result.faces = map.faces.size();
    result.doors = compiled.generatedDoors.size();
    result.lights = map.lights.size();
    result.spawns = map.spawns.size();
    result.entities = map.entities.size();
    result.events = lowered.events.size();
    result.chests = lowered.chests.size();

    // The named arrivals in the game's units (a facing of 2048 a turn).
    const auto arrivalOf = [](const std::string &name, const LoweredStart &start)
    {
        MapArrival arrival;
        arrival.name = name;

        for (size_t axis = 0; axis < 3; ++axis)
        {
            arrival.at[axis] = static_cast<int>(std::lround(start.position[axis]));
        }

        arrival.facing = static_cast<int>(std::lround(start.directionDegrees * 2048.0 / 360.0)) % 2048;
        arrival.facing += arrival.facing < 0 ? 2048 : 0;
        return arrival;
    };

    result.arrivals.clear();

    if (lowered.start)
    {
        result.arrivals.push_back(arrivalOf("start", *lowered.start));
    }

    for (const std::pair<std::string, LoweredStart> &arrival : lowered.arrivals)
    {
        result.arrivals.push_back(arrivalOf(arrival.first, arrival.second));
    }

    // The build must have produced what the project describes.
    std::set<int> boundEvents;

    for (const Game::IndoorFace &face : map.faces)
    {
        result.portals += face.isPortal ? 1 : 0;

        if (face.cogTriggered != 0)
        {
            boundEvents.insert(face.cogTriggered);
        }
    }

    // A decoration that is clicked carries its event itself.
    for (const Game::IndoorEntity &entity : map.entities)
    {
        if (entity.scriptEventId() != 0)
        {
            boundEvents.insert(entity.scriptEventId());
        }
    }

    for (const LoweredEvent &event : lowered.events)
    {
        if (event.trigger != "timer" && event.trigger != "load" && event.trigger != "leave" && event.trigger != "call"
            && event.trigger != "monster_damage"
            && !boundEvents.contains(event.eventId))
        {
            result.issues.push_back({"wiring.yml", "",
                "the event " + event.id + " is bound to no face of the built map",
                "build"});
        }
    }

    if (result.sectors != lowered.rooms.size() + 1)
    {
        result.issues.push_back({"rooms.yml", "", "the built map has " + std::to_string(result.sectors)
            + " sectors for " + std::to_string(lowered.rooms.size()) + " rooms (expected one each and the reserved "
            "sector 0)", "build"});
    }

    if (result.portals != lowered.openings.size())
    {
        result.issues.push_back({"rooms.yml", "", "the built map has " + std::to_string(result.portals)
            + " portal faces for " + std::to_string(lowered.openings.size()) + " openings", "build"});
    }

    size_t secondLeaves = 0;

    for (const LoweredDoor &door : lowered.doors)
    {
        secondLeaves += door.secondDoorId > 0 ? 1 : 0;
    }

    if (result.doors != lowered.doors.size() + secondLeaves + lowered.lifts.size())
    {
        result.issues.push_back({"objects.yml", "", "the built map has " + std::to_string(result.doors)
            + " moving parts for " + std::to_string(lowered.doors.size()) + " doors (" + std::to_string(secondLeaves)
            + " of two leaves) and " + std::to_string(lowered.lifts.size()) + " lifts and movers in the project",
            "build"});
    }

    const std::optional<std::vector<uint8_t>> blv = Game::IndoorMapDataWriter().buildBytes(map);

    if (!blv)
    {
        result.issues.push_back({"", "", "the built map could not be written as BLV", "build"});
        return false;
    }

    // Ground drawn as terrain on a map open to the sky (atmosphere.yml `ground`, core/GroundTerrain.h): its weights
    // and material file from the built faces, and the scene's `terrain` block.
    std::optional<GroundTerrain> ground;

    if (!buildProjectGround(project, map, options.assetRoot, stem, ground, result.issues))
    {
        return false;
    }

    YAML::Node sceneNode;
    std::string sceneText = writeSceneText(project, lowered, compiled, translucentFaces, sceneNode);

    if (ground)
    {
        sceneNode["terrain"] = ground->sceneTerrain;
        sceneText = writeCanonicalYaml(sceneNode);
        result.warnings.insert(result.warnings.end(), ground->warnings.begin(), ground->warnings.end());
    }

    // The game's own reader must accept the scene and apply it to the map.
    const std::optional<Game::IndoorSceneData> scene =
        Game::IndoorSceneYmlLoader().loadFromText(sceneText, errorMessage);

    if (!scene)
    {
        result.issues.push_back({"", "", "the scene file the build wrote is not accepted: " + errorMessage, "build"});
        return false;
    }

    Game::IndoorMapData checkedMap = map;
    Game::MapDeltaData delta;

    if (!Game::buildIndoorMapStateFromScene(*scene, checkedMap, delta, errorMessage))
    {
        result.issues.push_back({"", "", "the scene file does not apply to the built map: " + errorMessage, "build"});
        return false;
    }

    // Faces in one plane over each other, as the map starts and with its moving parts moved (core/Coplanar.h):
    // said by the project's ids.
    {
        CoplanarNames names;

        for (const std::pair<const std::string, int> &sector : lowered.ids.sectors)
        {
            names.sectors[sector.second] = sector.first;
        }

        for (const std::pair<const std::string, int> &door : lowered.ids.doors)
        {
            names.doors[door.second] = door.first;
        }

        for (const std::pair<const std::string, int> &event : lowered.ids.events)
        {
            names.events[event.second] = event.first;
        }

        for (const CoplanarPair &pair : findCoplanarFaces(checkedMap, &delta))
        {
            result.warnings.push_back("faces in one plane: " + describeCoplanarPair(checkedMap, &delta, pair, names));
        }

        // Walkable tops where the party's eye is in another sector's space than the game draws from
        // (core/EyeSector.h).
        for (const EyeSectorFinding &finding : findEyeOutsideSector(checkedMap, &delta))
        {
            result.warnings.push_back("eye outside its sector: " + describeEyeSectorFinding(checkedMap, &delta, finding,
                names));
        }
    }

    if (!result.issues.empty())
    {
        return false;
    }

    const std::string luaText = writeLuaText(project, lowered);
    // The map's cinematics (S6 item C): beside the map, none when the project has none.
    std::string cinematicsText;

    if (!writeCinematicsText(project, lowered, cinematicsText, result.issues))
    {
        return false;
    }

    const YAML::Node lockDocument = lowered.ids.toDocument();
    const std::string lockText = writeCanonicalYaml(lockDocument, SchemaSet::builtIn(), "ids_lock.schema.json");
    const std::map<std::string, ProjectFile>::const_iterator currentLock = project.files.find("ids.lock.yml");
    result.lockChanged = currentLock == project.files.end() || currentLock->second.text != lockText;

    if (options.dryRun)
    {
        std::error_code error;
        std::filesystem::remove(glbPath, error);
        std::filesystem::remove(sourceDirectory, error);
        std::filesystem::remove(outputDirectory, error);
        return true;
    }

    result.sourceRevision = projectRevision(project);
    result.lockHash = lockHashOfText(&lockText);
    JsonWriter buildJson(true);
    writeBuildJson(buildJson, result);
    std::string buildJsonText = buildJson.take();
    buildJsonText.push_back('\n');

    // Every build keeps the project's lock up to date (new ids added, removed ones dropped), so that a number once
    // given (an event a playtest clicks, a door) stays: `--out` too (from the ninth merge to batch ten it wrote the
    // lock only beside its map, and new events renumbered between builds: XD-03's second pass). A build elsewhere
    // also writes a copy beside its map. The private builds of `export`, `compare`, `audit` and the rest on a
    // project build a copy of it (cli openTarget), so they never touch the project's own lock.
    const bool ownBuild = options.outputDirectory.empty();
    // The lock is a record (S5_BROWSER_EDITOR.md 2.4.1): written under the project lock, each change logged in
    // .oymap/lock.log, never a history entry. It keeps the numbers of removed ids until `oymap lock prune`.
    bool lockWritten = false;

    // The walk's movement state (core/Walk.h): the doors by project id, the rooms by sector.
    WalkStateHeader walkHeader;
    walkHeader.kind = "indoor";
    walkHeader.world = textOf(project.document("project.yml"), "world", "");
    walkHeader.map = result.mapFile;
    walkHeader.party = walkPartyOfWorld(options.assetRoot, walkHeader.world, false);

    for (const LoweredDoor &door : lowered.doors)
    {
        WalkDoor walkDoor;
        walkDoor.id = door.id;
        walkDoor.mechanisms.push_back(uint32_t(door.doorId));

        if (door.secondDoorId != 0)
        {
            walkDoor.mechanisms.push_back(uint32_t(door.secondDoorId));
        }

        walkHeader.doors.push_back(walkDoor);
    }

    for (const LoweredLift &lift : lowered.lifts)
    {
        walkHeader.doors.push_back(WalkDoor{lift.id, {uint32_t(lift.doorId)}, false});
    }

    for (const std::pair<const std::string, int> &sector : lowered.ids.sectors)
    {
        walkHeader.rooms.emplace_back(sector.second, sector.first);
    }

    std::sort(walkHeader.rooms.begin(), walkHeader.rooms.end());
    const std::string walkText = writeWalkStateText(walkHeader, sceneNode);

    if (!writeBinaryFileAtomically(outputDirectory / result.mapFile, *blv, errorMessage)
        || !writeTextFileAtomically(outputDirectory / (stem + ".scene.yml"), sceneText, errorMessage)
        || !writeTextFileAtomically(outputDirectory / (stem + ".walk.yml"), walkText, errorMessage)
        || !writeTextFileAtomically(outputDirectory / (stem + ".lua"), luaText, errorMessage)
        || (!cinematicsText.empty()
            && !writeTextFileAtomically(outputDirectory / (stem + ".cinematics.yml"), cinematicsText, errorMessage))
        || !writeTextFileAtomically(outputDirectory / "build.json", buildJsonText, errorMessage)
        || (result.lockChanged
            && !writeLockRecord(project.root, lockText, result.sourceRevision, "build", lockWritten, errorMessage))
        || (!ownBuild && !writeTextFileAtomically(outputDirectory / "ids.lock.yml", lockText, errorMessage)))
    {
        result.issues.push_back({"", "", errorMessage, "io"});
        return false;
    }

    result.files = {
        result.mapFile, stem + ".scene.yml", stem + ".walk.yml", stem + ".lua", "build.json",
        "source/" + stem + ".glb"};

    if (!cinematicsText.empty())
    {
        result.files.push_back(stem + ".cinematics.yml");
    }
    else
    {
        std::error_code staleError;
        std::filesystem::remove(outputDirectory / (stem + ".cinematics.yml"), staleError);
    }

    if (!writeGroundFiles(ground, outputDirectory, stem, result.files, errorMessage))
    {
        result.issues.push_back({"", "", errorMessage, "io"});
        return false;
    }

    if (!ownBuild)
    {
        result.files.push_back("ids.lock.yml");
    }

    return true;
}

YAML::Node sceneActorNode(const LoweredMonster &monster, int actorIndex)
{
    YAML::Node node(YAML::NodeType::Map);

    if (actorIndex >= 0)
    {
        node["actor_index"] = actorIndex;
    }

    node["name"] = textNode(monster.displayName);
    node["npc_id"] = monster.npc;
    node["attributes"] = monster.attributes;
    node["hp"] = monster.hitPoints;
    node["hostility_type"] = 0;
    node["monster_info_id"] = monster.monsterId;
    // The legacy actor record exposes the low 16 bits of experience as a signed word.
    node["monster_id"] = static_cast<int16_t>(monster.experience);
    node["radius"] = monster.radius;
    node["height"] = monster.height;
    node["move_speed"] = monster.moveSpeed;
    node["position"] = position(monster.position[0], monster.position[1], monster.position[2]);
    node["initial_yaw_units"] = monster.yawUnits;

    if (monster.immobile)
    {
        node["immobile"] = true;
    }

    if (monster.leash > 0)
    {
        node["leash_radius"] = monster.leash;
    }

    node["sprite_ids"] = sequenceOf(std::vector<int>{0, 0, 0, 0});
    node["sector_id"] = monster.sector;
    node["current_action_animation"] = 0;
    node["carried_item_id"] = monster.carriedItemId;
    node["group"] = monster.group;
    node["ally"] = 0;
    node["unique_name_index"] = monster.uniqueNameIndex;
    return node;
}

YAML::Node sceneSpriteObjectNode(const LoweredItem &item, int index)
{
    YAML::Node node(YAML::NodeType::Map);

    if (index >= 0)
    {
        node["sprite_object_index"] = index;
    }

    node["sprite_id"] = item.spriteId;
    node["object_description_id"] = item.objectDescriptionId;
    node["position"] = position(item.position[0], item.position[1], item.position[2]);
    node["velocity"] = position(0.0, 0.0, 0.0);
    node["yaw_angle"] = 0;
    node["sound_id"] = 0;
    node["attributes"] = 0;
    node["sector_id"] = item.sector;

    for (const char *pField : {"time_since_created", "temporary_lifetime", "glow_radius_multiplier", "spell_id",
             "spell_level", "spell_skill", "field54", "spell_caster_pid", "spell_target_pid", "lod_distance",
             "spell_caster_ability"})
    {
        node[pField] = 0;
    }

    node["initial_position"] = position(item.position[0], item.position[1], item.position[2]);
    std::string record;

    for (int byte = 0; byte < 36; ++byte)
    {
        static const char *pDigits = "0123456789ABCDEF";
        // The item's number in the first word; a heap of gold's amount in the fourth.
        const unsigned value = byte < 4 ? (static_cast<unsigned>(item.itemId) >> (8 * byte)) & 0xffu
            : byte >= 12 && byte < 16 ? (static_cast<unsigned>(item.gold) >> (8 * (byte - 12))) & 0xffu : 0u;
        record.push_back(pDigits[value >> 4]);
        record.push_back(pDigits[value & 0xfu]);
    }

    node["raw_containing_item_hex"] = textNode(record);
    return node;
}

YAML::Node sceneLadderNode(const LoweredLadder &ladder)
{
    YAML::Node node(YAML::NodeType::Map);
    node["id"] = textNode(ladder.name);
    node["bottom"] = sceneNumbers({ladder.bottom[0], ladder.bottom[1], ladder.bottom[2]});
    node["top"] = sceneNumbers({ladder.top[0], ladder.top[1], ladder.top[2]});
    node["facing_degrees"] = sceneNumbers({ladder.facingDegrees})[0];
    node["width"] = sceneNumbers({ladder.width})[0];
    node["reach"] = sceneNumbers({ladder.reach})[0];
    node["top_exit"] = sceneNumbers({ladder.topExit[0], ladder.topExit[1], ladder.topExit[2]});
    node["grab_at_top"] = ladder.grabAtTop;

    if (ladder.grabInAir)
    {
        node["grab_in_air"] = true;
    }

    return node;
}
}
