#include "core/OutdoorBuild.h"
#include "core/View.h"

#include "core/CanonicalYaml.h"
#include "core/Coplanar.h"
#include "core/Json.h"
#include "core/MapLoad.h"
#include "core/MonsterRelations.h"
#include "core/IndoorLowering.h"
#include "core/Ops.h"
#include "core/OutdoorLowering.h"
#include "core/OutdoorPlaces.h"
#include "core/OutdoorThings.h"
#include "core/Schema.h"
#include "core/Sketch.h"
#include "core/Walk.h"
#include "core/SketchRead.h"

#include "game/FaceEnums.h"
#include "game/maps/MapDeltaData.h"
#include "game/maps/MistYml.h"
#include "game/maps/OutdoorSceneYml.h"
#include "game/maps/TerrainTileData.h"
#include "game/outdoor/OutdoorMapData.h"

#include <physfs.h>

#include <algorithm>
#include <array>
#include <charconv>
#include <cmath>
#include <cstdlib>
#include <sstream>

namespace OpenYAMM::Studio
{
namespace
{
constexpr size_t NodeTotal = static_cast<size_t>(OutdoorNodeCount) * OutdoorNodeCount;
// The party start decoration of the merged decoration table and how the shipped maps place it (Dagger Wound's
// "Party Start"): invisible, flag 2.
constexpr int PartyStartDecorationId = 13;
constexpr int PartyStartAttributes = 2;
// The map's flag of a decoration that is not drawn until an event shows it, and the bits of an actor that is
// hostile whatever its kind and of one that is not there until its group is shown.
constexpr int LevelDecorationInvisible = 0x0020;
constexpr int ActorAggressor = 0x00080000;
constexpr int ActorInvisible = 0x00010000;
const char *PartyStartName = "party start";



size_t countOf(const YAML::Node &node)
{
    return node.IsDefined() && node.IsSequence() ? node.size() : 0;
}

YAML::Node textNode(const std::string &text)
{
    YAML::Node node(text);
    node.SetTag("!");
    return node;
}

YAML::Node zeros(size_t count)
{
    YAML::Node sequence(YAML::NodeType::Sequence);

    for (size_t index = 0; index < count; ++index)
    {
        sequence.push_back(0);
    }

    return sequence;
}

// A door of a built building: the model and the face that carry its event.
struct DoorFace
{
    size_t model = 0;
    size_t face = 0;
    uint32_t attributes = 0;
    uint16_t event = 0;
    // The number events change the face by (its bits, its texture); 0 for none.
    uint16_t cog = 0;
};

// Where the party arrives coming from a neighbour across a side of the map: the game looks for the decoration
// named "<side> start" (core/OutdoorInstall.cpp tells the travel).
struct ArrivalPoint
{
    std::string name;
    std::string entrance;
    int x = 0;
    int y = 0;
    int z = 0;
    int facing = 0;
};

int facingUnitsOf(const std::string &compass)
{
    // The game's angle units: 2048 a turn, 0 east, counter-clockwise.
    static const std::pair<const char *, int> Units[] = {{"e", 0}, {"ne", 256}, {"n", 512}, {"nw", 768}, {"w", 1024},
        {"sw", 1280}, {"s", 1536}, {"se", 1792}};

    for (const std::pair<const char *, int> &entry : Units)
    {
        if (compass == entry.first)
        {
            return entry.second;
        }
    }

    return 0;
}

// Where the party stands at a point of the land: on the land, or, where a structure covers the land there (D6's
// cooled crust over the lava, 26 above it), on that structure's top. From the land upwards: while the first face
// above within the party's height (192) looks up and can be stood on, the point is inside the structure and goes up
// onto that face; a face that looks down (an underside, a roof over a porch seen from below) or none ends it. A
// structure that starts hidden (D6's crust, shown when the lava cools) counts: an arrival named on it is for when it
// stands there; one that is never solid (`solid: false`) does not.
// The height and the structure stood on (empty: the land).
struct StandingPlace
{
    double height = 0.0;
    std::string model;
};

StandingPlace standingPlaceOnModels(const std::vector<Game::OutdoorBModel> &models, double x, double y, double ground)
{
    constexpr double PartyHeight = 192.0;
    // A face one can stand on looks up more than sideways (the game's 45 degrees, 46340 of 65536).
    constexpr int32_t StandableNormal = 46340;
    const uint32_t portal = Game::faceAttributeBit(Game::FaceAttribute::IsPortal);
    const uint32_t invisible = Game::faceAttributeBit(Game::FaceAttribute::Invisible);
    const uint32_t untouchable = Game::faceAttributeBit(Game::FaceAttribute::Untouchable);
    StandingPlace place;
    place.height = ground;

    for (int guard = 0; guard < 16; ++guard)
    {
        std::optional<double> nearest;
        // Of the faces at that height: whether one looks down (a thin roof's underside under its top ends the
        // climb) and whether one can be stood on.
        bool nearestDown = false;
        bool nearestStandable = false;
        std::string nearestModel;

        for (const Game::OutdoorBModel &model : models)
        {
            for (const Game::OutdoorBModelFace &face : model.faces)
            {
                // Upright faces cover no ground; nor do faces nothing ever touches.
                if (std::abs(face.planeNormalZ) < 3277 || (face.attributes & portal) != 0
                    || (face.attributes & (invisible | untouchable)) == untouchable || face.vertexIndices.size() < 3)
                {
                    continue;
                }

                bool inside = false;

                for (size_t index = 0, previous = face.vertexIndices.size() - 1; index < face.vertexIndices.size();
                     previous = index++)
                {
                    const Game::OutdoorBModelVertex &a = model.vertices[face.vertexIndices[index]];
                    const Game::OutdoorBModelVertex &b = model.vertices[face.vertexIndices[previous]];

                    if ((a.y > y) != (b.y > y)
                        && x < a.x + (b.x - a.x) * (y - a.y) / static_cast<double>(b.y - a.y))
                    {
                        inside = !inside;
                    }
                }

                if (!inside)
                {
                    continue;
                }

                // The face's plane over the point, from its first corner (its stored distance may not fit far out).
                const Game::OutdoorBModelVertex &corner = model.vertices[face.vertexIndices[0]];
                const double z = corner.z - (static_cast<double>(face.planeNormalX) * (x - corner.x)
                    + static_cast<double>(face.planeNormalY) * (y - corner.y)) / face.planeNormalZ;

                // (A unit of rounding past the party's height: a thin roof's two faces there go together.)
                if (z <= place.height + 0.5 || z > place.height + PartyHeight + 1.0)
                {
                    continue;
                }

                if (!nearest || z < *nearest - 1.0)
                {
                    nearest = z;
                    nearestDown = false;
                    nearestStandable = false;
                }
                else if (z > *nearest + 1.0)
                {
                    continue;
                }

                nearestDown = nearestDown || face.planeNormalZ < 0;

                if (face.planeNormalZ > StandableNormal && !nearestStandable)
                {
                    nearestStandable = true;
                    nearestModel = model.name;
                }
            }
        }

        if (!nearest || nearestDown || !nearestStandable)
        {
            break;
        }

        place.height = *nearest;
        place.model = nearestModel;
    }

    return place;
}

// An arrival placed on a structure's top far over the land (a point sketched in the middle of a cave mouth's mound,
// not in front of it): said, as the party then stands up there.
void warnHighArrival(
    const std::string &name, double ground, const StandingPlace &place, std::vector<std::string> *pWarnings)
{
    if (pWarnings != nullptr && !place.model.empty() && place.height - ground > 64.0)
    {
        pWarnings->push_back("sketch.yml: " + name + " lies within " + place.model + ", whose top over it is "
            + std::to_string(static_cast<int>(std::lround(place.height - ground))) + " over the land: the party "
            "arrives standing on that top. Move the point off the structure where the party should stand on the "
            "land (in front of a cave mouth or a door, not in its middle)");
    }
}

// The arrival points: for every edge neighbour of the project, the plan entrance that names it (kind arrival or
// both) where the sketch places it. `missing` gets the sides that lead somewhere and have no such entrance.
std::vector<ArrivalPoint> arrivalPoints(
    const Project &project,
    const LoweredOutdoorMap &lowered,
    const std::vector<Game::OutdoorBModel> &models,
    std::vector<std::string> &missing)
{
    std::vector<ArrivalPoint> points;
    const YAML::Node entrances = childOf(project.document("plan.yml"), "entrances");
    const YAML::Node placed = childOf(project.document("sketch.yml"), "points");

    for (const OutdoorTravelEdge &edge : outdoorTravelEdges(project))
    {
        bool found = false;

        for (size_t index = 0; !found && entrances.IsDefined() && entrances.IsSequence() && index < entrances.size();
             ++index)
        {
            const YAML::Node entrance = entrances[index];
            const std::string kind = textOf(entrance, "kind", "");
            bool names = textOf(entrance, "neighbour", "") == edge.id;
            const YAML::Node several = childOf(entrance, "neighbours");

            for (size_t other = 0; several.IsDefined() && several.IsSequence() && other < several.size(); ++other)
            {
                names = names || (several[other].IsScalar() && several[other].Scalar() == edge.id);
            }

            if (!names || (kind != "arrival" && kind != "both"))
            {
                continue;
            }

            for (size_t point = 0; placed.IsDefined() && placed.IsSequence() && point < placed.size(); ++point)
            {
                const YAML::Node node = placed[point];
                const YAML::Node at = childOf(node, "at");

                if (textOf(node, "id", "") != textOf(entrance, "id", "") || !at.IsDefined() || !at.IsSequence()
                    || at.size() != 2)
                {
                    continue;
                }

                const double x = at[0].as<double>(0.0);
                const double y = at[1].as<double>(0.0);
                ArrivalPoint arrival;
                arrival.name = edge.side + " start";
                arrival.entrance = textOf(entrance, "id", "");
                arrival.x = static_cast<int>(std::lround((x - OutdoorNodeCount / 2) * OutdoorCellSize));
                arrival.y = static_cast<int>(std::lround((OutdoorNodeCount / 2 - y) * OutdoorCellSize));
                const StandingPlace place =
                    standingPlaceOnModels(models, arrival.x, arrival.y, lowered.storedHeightAt(x, y));
                arrival.z = static_cast<int>(std::lround(place.height));
                arrival.facing = facingUnitsOf(textOf(node, "facing", textOf(entrance, "facing", "")));
                points.push_back(arrival);
                found = true;
                break;
            }
        }

        if (!found && !edge.oneWay)
        {
            missing.push_back(edge.side + " (from " + edge.map + ")");
        }
    }

    return points;
}

// The named arrivals (D-4): `start`, and every plan entrance of kind arrival or both where the sketch places it,
// standing on the land or on the top of a structure that covers it there, facing as the point (else the entrance)
// says.
std::vector<MapArrival> namedArrivals(
    const Project &project,
    const LoweredOutdoorMap &lowered,
    const std::vector<Game::OutdoorBModel> &models,
    std::vector<std::string> *pWarnings = nullptr)
{
    std::vector<MapArrival> named;

    if (lowered.start)
    {
        MapArrival start;
        start.name = "start";
        start.at[0] = static_cast<int>(std::lround(lowered.start->x));
        start.at[1] = static_cast<int>(std::lround(lowered.start->y));
        start.at[2] = static_cast<int>(std::lround(lowered.start->z));
        start.facing = lowered.start->facing;
        named.push_back(start);
    }

    const YAML::Node entrances = childOf(project.document("plan.yml"), "entrances");
    const YAML::Node placed = childOf(project.document("sketch.yml"), "points");

    for (size_t index = 0; entrances.IsDefined() && entrances.IsSequence() && index < entrances.size(); ++index)
    {
        const YAML::Node entrance = entrances[index];
        const std::string kind = textOf(entrance, "kind", "both");
        const std::string id = textOf(entrance, "id", "");

        for (size_t point = 0; kind != "exit" && !id.empty() && placed.IsDefined() && placed.IsSequence()
             && point < placed.size(); ++point)
        {
            const YAML::Node node = placed[point];
            const YAML::Node at = childOf(node, "at");

            if (textOf(node, "id", "") != id || !at.IsDefined() || !at.IsSequence() || at.size() != 2)
            {
                continue;
            }

            const double x = at[0].as<double>(0.0);
            const double y = at[1].as<double>(0.0);
            MapArrival arrival;
            arrival.name = id;
            arrival.at[0] = static_cast<int>(std::lround((x - OutdoorNodeCount / 2) * OutdoorCellSize));
            arrival.at[1] = static_cast<int>(std::lround((OutdoorNodeCount / 2 - y) * OutdoorCellSize));
            const double ground = lowered.storedHeightAt(x, y);
            const StandingPlace place = standingPlaceOnModels(models, arrival.at[0], arrival.at[1], ground);
            arrival.at[2] = static_cast<int>(std::lround(place.height));
            warnHighArrival(id, ground, place, pWarnings);
            arrival.facing = facingUnitsOf(textOf(node, "facing", textOf(entrance, "facing", "")));
            named.push_back(arrival);
            break;
        }
    }

    return named;
}

std::string hexOf(const std::vector<uint8_t> &bytes)
{
    static const char *pDigits = "0123456789ABCDEF";
    std::string text;

    for (const uint8_t byte : bytes)
    {
        text.push_back(pDigits[byte >> 4]);
        text.push_back(pDigits[byte & 0xfu]);
    }

    return text;
}

std::string writeSceneText(
    const LoweredOutdoorMap &lowered,
    const std::vector<DoorFace> &doors,
    const std::vector<std::pair<size_t, size_t>> &translucentFaces,
    const OutdoorPlaces &places,
    const OutdoorThings &things,
    const std::vector<ArrivalPoint> &arrivals,
    const YAML::Node &atmosphere,
    bool noSpells,
    YAML::Node &sceneOut)
{
    YAML::Node scene(YAML::NodeType::Map);
    scene["format_version"] = 1;
    scene["kind"] = "outdoor_scene";
    scene["source"]["geometry_file"] = lowered.mapStem + ".odm";

    YAML::Node environment(YAML::NodeType::Map);
    // The sky, the fog and the weather from the project's atmosphere.yml; without it the game's own choices.
    environment["sky_texture"] = textNode(textOf(atmosphere, "sky", ""));
    environment["ground_tileset_name"] = textNode("");
    environment["master_tile"] = static_cast<int>(lowered.masterTile);
    YAML::Node tileSets(YAML::NodeType::Sequence);

    for (const uint16_t tileSet : lowered.tileSets)
    {
        tileSets.push_back(static_cast<int>(tileSet));
    }

    environment["tile_set_lookup_indices"] = tileSets;
    // atmosphere.yml `flags`: the scene's environment flags, and the raw bits the shipped scenes keep beside them
    // (the game derives the bits from the flags: game/maps/OutdoorSceneYml.cpp syncEnvironmentRawBits).
    const YAML::Node flags = childOf(atmosphere, "flags");
    uint32_t extraBits = 0;
    const std::array<std::pair<const char *, uint32_t>, 9> flagBits = {{{"foggy", 0}, {"raining", 0x01},
        {"snowing", 0x02}, {"underwater", 0x04}, {"no_terrain", 0x08}, {"always_dark", 0x10}, {"always_light", 0x20},
        {"always_foggy", 0x40}, {"red_fog", 0x80}}};

    const auto flagSet = [&flags](const char *pFlag)
    {
        const YAML::Node value = childOf(flags, pFlag);
        return value.IsDefined() && value.IsScalar() && value.as<bool>(false);
    };

    for (const std::pair<const char *, uint32_t> &flag : flagBits)
    {
        extraBits |= flagSet(flag.first) ? flag.second : 0;
    }

    environment["day_bits_raw"] = flagSet("foggy") ? 1 : 0;
    environment["map_extra_bits_raw"] = static_cast<int>(extraBits);

    for (const std::pair<const char *, uint32_t> &flag : flagBits)
    {
        environment["flags"][flag.first] = flagSet(flag.first);
    }

    const YAML::Node fog = childOf(atmosphere, "fog");
    environment["fog"]["weak_distance"] =
        childOf(fog, "weak_distance").IsDefined() ? fog["weak_distance"].as<int>(0) : 0;
    environment["fog"]["strong_distance"] =
        childOf(fog, "strong_distance").IsDefined() ? fog["strong_distance"].as<int>(0) : 0;
    // The flight ceiling (the Plane of Water's 2000); 0: the game's own.
    environment["ceiling"] = childOf(atmosphere, "ceiling").IsDefined() ? atmosphere["ceiling"].as<int>(0) : 0;
    const std::string precipitation = textOf(atmosphere, "precipitation", "");
    const YAML::Node dailyFog = childOf(atmosphere, "daily_fog");
    const YAML::Node tint = childOf(atmosphere, "fog_tint");
    // D-40: the map's own chance of ash fall (percent of days), read by the game as weather.yml's `ash` for the map.
    const YAML::Node ash = childOf(atmosphere, "ash");

    if (!precipitation.empty() || dailyFog.IsDefined() || tint.IsDefined() || ash.IsDefined())
    {
        YAML::Node weather(YAML::NodeType::Map);
        weather["fog_mode"] = dailyFog.IsDefined() ? "daily_random" : "static";
        weather["precipitation"] = precipitation.empty() ? "none" : precipitation;

        if (ash.IsDefined() && ash.IsScalar())
        {
            weather["ash_chance"] = ash.as<int>(0);
        }

        if (tint.IsDefined() && tint.IsSequence() && tint.size() == 3)
        {
            for (size_t channel = 0; channel < 3; ++channel)
            {
                weather["fog_tint_rgb"].push_back(tint[channel].as<int>(0));
            }
        }

        for (const char *pDensity : {"small", "average", "dense"})
        {
            const YAML::Node density = childOf(dailyFog, pDensity);

            if (!density.IsDefined() || !density.IsMap())
            {
                continue;
            }

            weather["daily_fog"][std::string(pDensity) + "_chance"] = density["chance"].as<int>(0);
            weather["daily_fog"][pDensity]["weak_distance"] = density["weak_distance"].as<int>(0);
            weather["daily_fog"][pDensity]["strong_distance"] = density["strong_distance"].as<int>(0);
        }

        environment["weather"] = weather;
    }

    scene["environment"] = environment;

    // project.yml rules.no_spells (S8g): no spell works on the map (the scene's runtime_restrictions).
    if (noSpells)
    {
        scene["runtime_restrictions"]["allow_spellcasting"] = false;
    }

    // atmosphere.yml `view_distance`: the map's far clip and draw distances scaled (A6's D4: the castle across the
    // lake); the scene's rendering.view_distance_scale, 1 when left out.
    if (const YAML::Node viewDistance = childOf(atmosphere, "view_distance"); viewDistance.IsDefined()
        && viewDistance.IsScalar())
    {
        scene["rendering"]["view_distance_scale"] = viewDistance.as<double>(1.0);
    }

    // Ground mist as atmosphere.yml gives it (checked by the game's parser in checkOutdoorMist).
    if (const YAML::Node mist = childOf(atmosphere, "mist"); mist.IsDefined() && mist.IsMap())
    {
        scene["mist"] = YAML::Clone(mist);
    }

    // sketch.yml `sounds` (E9): the scene's placed ambient sounds, as an indoor build writes them.
    for (const LoweredAmbientSound &sound : things.sounds)
    {
        const auto number = [](double value)
        {
            const double rounded = std::round(value * 1000.0) / 1000.0;
            return rounded == std::round(rounded) ? YAML::Node(static_cast<long long>(std::llround(rounded)))
                                                  : YAML::Node(rounded);
        };
        YAML::Node node(YAML::NodeType::Map);
        node["key"] = sound.key;
        node["sound"] = textNode(sound.sound);
        node["position"].SetStyle(YAML::EmitterStyle::Flow);

        for (const double axis : sound.position)
        {
            node["position"].push_back(number(axis));
        }

        node["inner_radius"] = number(sound.innerRadius);
        node["outer_radius"] = number(sound.outerRadius);
        node["volume"] = number(sound.volume);
        node["loop"] = sound.loop;

        if (sound.wait)
        {
            node["wait"].SetStyle(YAML::EmitterStyle::Flow);
            node["wait"].push_back(number((*sound.wait)[0]));
            node["wait"].push_back(number((*sound.wait)[1]));
        }

        node["start_on"] = sound.startOn;

        if (sound.dayOnly)
        {
            node["day_only"] = true;
        }

        if (sound.nightOnly)
        {
            node["night_only"] = true;
        }

        if (!sound.pan)
        {
            node["pan"] = false;
        }

        scene["ambient_sounds"].push_back(node);
    }

    scene["terrain"]["attribute_overrides"] = YAML::Node(YAML::NodeType::Sequence);
    // atmosphere.yml `footsteps`: the steps' sounds on chosen ground tiles (the ODM's local tile numbers), as the
    // shipped scenes' footstep_sound_overrides (out04's ashes, MM6's lava fields).
    YAML::Node footsteps(YAML::NodeType::Sequence);
    const YAML::Node footstepsNode = childOf(atmosphere, "footsteps");

    for (size_t index = 0; footstepsNode.IsDefined() && footstepsNode.IsSequence() && index < footstepsNode.size();
         ++index)
    {
        const YAML::Node entry = footstepsNode[index];
        int first = 0;
        int last = -1;

        if (const YAML::Node tile = childOf(entry, "tile"); tile.IsDefined())
        {
            first = last = tile.as<int>(0);
        }
        else if (const YAML::Node range = childOf(entry, "tiles"); range.IsDefined() && range.IsSequence()
            && range.size() == 2)
        {
            first = range[0].as<int>(0);
            last = range[1].as<int>(-1);
        }

        for (int tile = std::max(first, 0); tile <= std::min(last, 255); ++tile)
        {
            YAML::Node sound(YAML::NodeType::Map);
            sound["tile_id"] = tile;
            sound["walk_sound_id"] = childOf(entry, "walk").as<int>(0);
            sound["run_sound_id"] = childOf(entry, "run").as<int>(0);
            footsteps.push_back(sound);
        }
    }

    scene["terrain"]["footstep_sound_overrides"] = footsteps;
    // The scene says which faces carry events: the game clears every face's event and sets these.
    YAML::Node interactive(YAML::NodeType::Sequence);

    for (const DoorFace &door : doors)
    {
        YAML::Node face(YAML::NodeType::Map);
        face["bmodel_index"] = static_cast<int>(door.model);
        face["face_index"] = static_cast<int>(door.face);
        face["legacy_attributes"] = door.attributes;
        face["cog_number"] = static_cast<int>(door.cog);
        face["cog_triggered_number"] = static_cast<int>(door.event);
        face["cog_trigger"] = 0;
        interactive.push_back(face);
    }

    scene["bmodel_faces"]["interactive_faces"] = interactive;

    // The faces of structures laid `translucent: true`: drawn blended by their texture's alpha.
    if (!translucentFaces.empty())
    {
        YAML::Node translucent(YAML::NodeType::Sequence);

        for (const auto &[model, face] : translucentFaces)
        {
            YAML::Node entry(YAML::NodeType::Map);
            entry.SetStyle(YAML::EmitterStyle::Flow);
            entry["bmodel_index"] = static_cast<int>(model);
            entry["face_index"] = static_cast<int>(face);
            translucent.push_back(entry);
        }

        scene["bmodel_faces"]["translucent_faces"] = translucent;
    }

    YAML::Node start(YAML::NodeType::Map);
    start["entity_index"] = 0;
    start["name"] = textNode(PartyStartName);
    start["decoration_list_id"] = PartyStartDecorationId;
    start["ai_attributes"] = PartyStartAttributes;
    start["position"]["x"] = static_cast<int>(std::lround(lowered.start->x));
    start["position"]["y"] = static_cast<int>(std::lround(lowered.start->y));
    start["position"]["z"] = static_cast<int>(std::lround(lowered.start->z));
    start["facing"] = lowered.start->facing;
    start["event_id_primary"] = 0;
    start["event_id_secondary"] = 0;
    start["variable_primary"] = 0;
    start["variable_secondary"] = 0;
    start["special_trigger"] = 0;
    start["initial_decoration_flag"] = PartyStartAttributes;
    YAML::Node entities(YAML::NodeType::Sequence);
    entities.push_back(start);

    for (const OutdoorPlacedDecoration &decoration : places.decorations)
    {
        YAML::Node entity(YAML::NodeType::Map);
        entity["entity_index"] = static_cast<int>(entities.size());
        entity["name"] = textNode(decoration.name);
        entity["decoration_list_id"] = decoration.listId;
        entity["ai_attributes"] = 0;
        entity["position"]["x"] = decoration.x;
        entity["position"]["y"] = decoration.y;
        entity["position"]["z"] = decoration.z;
        entity["facing"] = decoration.facing;
        // The number events change its picture by (its scatter entry's `id` or `group`), 0 for none; the event a
        // click on it runs (the entry's `event`).
        entity["event_id_primary"] = decoration.number;
        entity["event_id_secondary"] = decoration.event;
        entity["variable_primary"] = 0;
        entity["variable_secondary"] = 0;
        entity["special_trigger"] = 0;
        entity["initial_decoration_flag"] = 0;
        entities.push_back(entity);
    }

    // Where the party arrives from each neighbour: as the party start, under the name the game looks for.
    for (const ArrivalPoint &arrival : arrivals)
    {
        YAML::Node entity(YAML::NodeType::Map);
        entity["entity_index"] = static_cast<int>(entities.size());
        entity["name"] = textNode(arrival.name);
        entity["decoration_list_id"] = PartyStartDecorationId;
        entity["ai_attributes"] = PartyStartAttributes;
        entity["position"]["x"] = arrival.x;
        entity["position"]["y"] = arrival.y;
        entity["position"]["z"] = arrival.z;
        entity["facing"] = arrival.facing;
        entity["event_id_primary"] = 0;
        entity["event_id_secondary"] = 0;
        entity["variable_primary"] = 0;
        entity["variable_secondary"] = 0;
        entity["special_trigger"] = 0;
        entity["initial_decoration_flag"] = PartyStartAttributes;
        entities.push_back(entity);
    }

    // Single decorations of the sketch's structures, each with the event a click on it runs.
    for (size_t index = 0; index < things.decorations.size(); ++index)
    {
        const OutdoorPlacedDecoration &decoration = things.decorations[index];
        YAML::Node entity(YAML::NodeType::Map);
        entity["entity_index"] = static_cast<int>(entities.size());
        entity["name"] = textNode(decoration.name);
        entity["decoration_list_id"] = decoration.listId;
        entity["ai_attributes"] = 0;
        entity["position"]["x"] = decoration.x;
        entity["position"]["y"] = decoration.y;
        entity["position"]["z"] = decoration.z;
        entity["facing"] = decoration.facing;
        // The number events change its picture by, and the map's flag of a decoration that starts hidden.
        entity["event_id_primary"] = index < things.decorationNumbers.size() ? things.decorationNumbers[index] : 0;
        entity["event_id_secondary"] = static_cast<int>(things.decorationEvents[index]);
        entity["variable_primary"] = 0;
        entity["variable_secondary"] = 0;
        entity["special_trigger"] = 0;
        entity["initial_decoration_flag"] =
            index < things.decorationHidden.size() && things.decorationHidden[index] ? LevelDecorationInvisible : 0;
        entities.push_back(entity);
    }

    scene["entities"] = entities;
    // A spawn point as the shipped maps place them: type 3 (monsters of a slot of the map), radius 32.
    YAML::Node spawns(YAML::NodeType::Sequence);

    for (const OutdoorPlacedSpawn &placed : places.spawns)
    {
        YAML::Node spawn(YAML::NodeType::Map);
        spawn["spawn_index"] = static_cast<int>(spawns.size());
        spawn["position"]["x"] = placed.x;
        spawn["position"]["y"] = placed.y;
        spawn["position"]["z"] = placed.z;
        spawn["radius"] = 32;
        spawn["type_id"] = placed.type;
        spawn["index"] = placed.slot;
        spawn["attributes"] = 0;
        spawn["group"] = 0;
        spawns.push_back(spawn);
    }

    scene["spawns"] = spawns;

    YAML::Node state(YAML::NodeType::Map);
    state["location"]["respawn_count"] = 0;
    state["location"]["last_respawn_day"] = 0;
    state["location"]["reputation"] = 0;
    state["location"]["alert_status"] = 0;
    state["face_attribute_overrides"] = YAML::Node(YAML::NodeType::Sequence);
    // People and creatures that stand on the map from the start, as a shipped map's scene holds its actors. The
    // sprites are left to the game, which takes them from the monster's descriptor.
    YAML::Node actors(YAML::NodeType::Sequence);

    for (const OutdoorActorPlan &actor : things.actors)
    {
        YAML::Node node(YAML::NodeType::Map);
        node["actor_index"] = static_cast<int>(actors.size());
        node["name"] = textNode("");
        node["npc_id"] = actor.npc;
        // The game's Aggressor bit: hostile whatever the monster table says of its kind.
        node["attributes"] = (actor.hostile ? ActorAggressor : 0) | (actor.hidden ? ActorInvisible : 0);
        node["hp"] = actor.hitPoints;
        node["hostility_type"] = 0;
        node["monster_info_id"] = actor.monsterId;
        node["monster_id"] = actor.monsterId;
        node["radius"] = actor.radius;
        node["height"] = actor.height;
        node["move_speed"] = actor.moveSpeed;
        node["position"]["x"] = actor.x;
        node["position"]["y"] = actor.y;
        node["position"]["z"] = actor.z;
        node["sprite_ids"] = zeros(4);
        node["sector_id"] = 0;
        node["current_action_animation"] = 0;
        node["carried_item_id"] = actor.carriedItem;
        node["group"] = actor.group;
        node["ally"] = 0;
        node["unique_name_index"] = 0;
        if (actor.leash > 0)
        {
            node["leash_radius"] = actor.leash;
        }
        actors.push_back(node);
    }

    state["actors"] = actors;
    YAML::Node spriteObjects(YAML::NodeType::Sequence);

    // sketch.yml `items`: items on the ground, as a shipped outdoor map's scene holds its sprite objects (sector 0).
    for (const LoweredItem &item : things.items)
    {
        spriteObjects.push_back(sceneSpriteObjectNode(item, static_cast<int>(spriteObjects.size())));
    }

    state["sprite_objects"] = spriteObjects;
    // Chests as a shipped map's scene holds them: 140 item records of 36 bytes, an item's number in the first
    // four (a number below zero: something of that treasure level, chosen by the game on the first opening), and
    // the grid of what lies where, empty until then.
    YAML::Node chests(YAML::NodeType::Sequence);

    for (const OutdoorChestPlan &chest : things.chests)
    {
        std::vector<uint8_t> records(140 * 36, 0);
        size_t slot = 0;
        const auto put = [&records, &slot](int item)
        {
            const uint32_t value = static_cast<uint32_t>(item);

            for (int byte = 0; byte < 4 && slot < 140; ++byte)
            {
                records[slot * 36 + byte] = static_cast<uint8_t>((value >> (8 * byte)) & 0xffu);
            }

            ++slot;
        };

        for (const int item : chest.items)
        {
            put(item);
        }

        for (int index = 0; index < chest.randomItems; ++index)
        {
            put(-chest.level);
        }

        // Things of other treasure levels, one each (a chest of mixed levels).
        for (const int level : chest.randomLevels)
        {
            put(-level);
        }

        YAML::Node node(YAML::NodeType::Map);
        node["chest_index"] = static_cast<int>(chests.size());
        node["chest_type_id"] = chest.picture;
        node["flags"] = chest.trapped ? 1 : 0;
        node["raw_items_hex"] = textNode(hexOf(records));
        node["inventory_matrix"] = zeros(140);
        chests.push_back(node);
    }

    state["chests"] = chests;
    const Game::MapDeltaPersistentVariables variables;
    state["variables"]["map"] = zeros(variables.mapVars.size());
    state["variables"]["decor"] = zeros(variables.decorVars.size());
    scene["initial_state"] = state;
    sceneOut = scene;
    return writeCanonicalYaml(scene);
}

std::string luaQuoted(const std::string &text)
{
    std::string result = "\"";

    for (const char character : text)
    {
        if (character == '"' || character == '\\')
        {
            result.push_back('\\');
        }

        result.push_back(character == '\n' ? ' ' : character);
    }

    return result + "\"";
}

std::string writeLuaText(
    const Project &project,
    const LoweredOutdoorMap &lowered,
    const std::vector<OutdoorEventPlan> &events,
    const OutdoorThings &things)
{
    std::ostringstream lua;
    lua << "-- Generated by oymap build from the Map Studio project \""
        << textOf(project.document("project.yml"), "id", lowered.mapStem)
        << "\". Change the project, not this file.\n";
    lua << "SetMapMetadata({";

    // Timer events that act only on a flying party, as the exported scripts list them (left out when none, so
    // maps without them keep their bytes).
    if (!things.levitateTraps.empty())
    {
        lua << "levitateTrapEvents = {";

        for (size_t index = 0; index < things.levitateTraps.size(); ++index)
        {
            lua << (index == 0 ? "" : ", ") << things.levitateTraps[index];
        }

        lua << "}, ";
    }

    lua << "onLoad = {";

    for (size_t index = 0; index < things.onLoad.size(); ++index)
    {
        lua << (index == 0 ? "" : ", ") << things.onLoad[index];
    }

    lua << "}, onLeave = {";

    for (size_t index = 0; index < things.onLeave.size(); ++index)
    {
        lua << (index == 0 ? "" : ", ") << things.onLeave[index];
    }

    lua << "}, openedChestIds = {";

    // Which chest each chest event opens: the game marks the chest as opened by it.
    for (const std::pair<const int, int> &chest : things.chestOfEvent)
    {
        lua << "[" << chest.first << "] = {" << chest.second << "}, ";
    }

    lua << "}";
    bool firstTimer = true;

    // Timers as the scripts exported from the original maps declare them: an interval counted in half minutes of
    // game time, which is one second of play each; calendar timers by day or week. In event number order.
    std::map<int, std::string> timerLines;

    for (const std::pair<const int, int> &timer : things.timers)
    {
        timerLines[timer.first] = "triggerKind = \"timer\", scheduleKind = \"interval\", intervalHalfMinutes = "
            + std::to_string(timer.second);
    }

    for (const std::pair<const int, std::string> &timer : things.calendarTimers)
    {
        timerLines[timer.first] = timer.second;
    }

    for (const std::pair<const int, std::string> &timer : timerLines)
    {
        lua << (firstTimer ? ", timers = {\n" : "") << "    { eventId = " << timer.first << ", sourceEventId = "
            << timer.first << ", triggerStep = 0, origin = \"legacy\", " << timer.second << " },\n";
        firstTimer = false;
    }

    lua << (firstTimer ? "})\n" : "}})\n");

    for (const OutdoorEventPlan &event : events)
    {
        lua << "\n-- " << event.id << "\nRegisterEvent(" << event.number << ", "
            << (event.title.empty() ? std::string("nil") : luaQuoted(event.title)) << ", ";

        if (event.body.empty())
        {
            lua << "nil";
        }
        else
        {
            // A handler whose script reads continueStep (a `lua` effect continuing a dialogue the handler opened,
            // such as Xeen's mirrors) takes it.
            const bool continues = std::any_of(event.body.begin(), event.body.end(),
                [](const std::string &line) { return line.find("continueStep") != std::string::npos; });
            lua << (continues ? "function(continueStep)\n" : "function()\n");

            // A `lua` effect that names eventId gets the handler's own number (Xeen.useMirror(id, eventId,
            // continueStep)).
            if (std::any_of(event.body.begin(), event.body.end(),
                    [](const std::string &line) { return line.find("eventId") != std::string::npos; }))
            {
                lua << "    local eventId = " << event.number << "\n";
            }

            for (const std::string &line : event.body)
            {
                lua << "    " << line << "\n";
            }

            lua << "end";
        }

        if (!event.title.empty())
        {
            lua << ", " << luaQuoted(event.title);
        }

        lua << ")\n";
    }

    return lua.str();
}

// What the sketch and the plan say and this slice does not build, by layer and count.
// Where the monster table leaves the map's slot and placed monsters peaceful to the party or sets them on each other
// unsaid (core/MonsterRelations.h): warnings with the fix in sketch.yml `relations`. Nothing without an asset root.
void warnOutdoorMonsterHostility(
    const Project &project,
    const std::filesystem::path &assetRoot,
    const OutdoorThings &things,
    const OutdoorPlaces &places,
    std::vector<std::string> &warnings)
{
    const std::filesystem::path tables = assetRoot / "engine" / "data_tables";
    std::string monsterText;
    std::string relationText;
    std::string mapStatsText;

    const std::string world = textOf(project.document("project.yml"), "world", "");

    if (!readWorldTable(assetRoot, world, "monster_data.txt", "monster_data", monsterText)
        || !readTextFile(tables / "hostile.txt", relationText))
    {
        return;
    }

    readWorldTable(assetRoot, world, "map_stats.txt", "map_stats", mapStatsText);
    MapMonsters monsters;
    readMapSlots(project.document("project.yml"), parseTableRows(mapStatsText), monsters);

    for (const OutdoorPlacedSpawn &spawn : places.spawns)
    {
        if (spawn.type == 3)
        {
            monsters.spawns.push_back({spawn.area, spawn.slot, '\0', 0});
        }
    }

    for (const OutdoorActorPlan &actor : things.actors)
    {
        monsters.placed.push_back({actor.id, actor.monsterId, actor.group,
            actor.hostile ? std::optional<bool>(true) : std::nullopt});
    }

    monsters.peacefulGroups = things.peacefulGroups;
    monsters.relations = things.relations;
    std::string worldRelationsText;

    if (!world.empty() && readTextFile(assetRoot / "worlds" / world / "relations.yml", worldRelationsText))
    {
        monsters.world = readWorldMonsterRelations(worldRelationsText);
    }
    const std::vector<std::string> found =
        monsterHostilityWarnings(monsters, parseTableRows(monsterText), parseTableRows(relationText), "sketch.yml");
    warnings.insert(warnings.end(), found.begin(), found.end());
}

void listNotBuilt(const Project &project, std::vector<std::string> &warnings)
{
    const YAML::Node sketch = project.document("sketch.yml");
    const YAML::Node plan = project.document("plan.yml");
    const YAML::Node card = project.document("project.yml");
    const auto notBuilt = [&warnings](const std::string &layer, size_t count, const std::string &what)
    {
        if (count != 0)
        {
            warnings.push_back("not built yet: " + layer + ": " + std::to_string(count) + " " + what);
        }
    };
    notBuilt("sketch.yml water.shores", countOf(childOf(childOf(sketch, "water"), "shores")),
        "shore stretches by kind (every shore is the classic dirt beach of the shore tiles; a cliff at the water "
        "comes from the heights)");
    notBuilt("sketch.yml views", countOf(childOf(sketch, "views")), "cameras (a review's, not the map's)");
    size_t planEntries = 0;

    for (const char *pKey : {"containers", "points_of_interest", "landmarks", "set_pieces", "mechanisms"})
    {
        planEntries += countOf(childOf(plan, pKey));
    }

    notBuilt("plan.yml", planEntries, "containers, points of interest, landmarks, set pieces and mechanisms: the "
        "plan says what they are, the build raises what sketch.yml draws of them in `structures` and `actors`");
    size_t otherWays = 0;
    const YAML::Node neighbours = childOf(card, "neighbours");

    for (size_t index = 0; neighbours.IsDefined() && neighbours.IsSequence() && index < neighbours.size(); ++index)
    {
        const std::string kind = textOf(neighbours[index], "kind", "");
        otherWays += kind == "edge" || kind == "door" ? 0 : 1;
    }

    notBuilt("project.yml neighbours", otherWays, "ways that are neither a map edge nor a door (boats, stables, "
        "teleports: a house's service or an event of a structure makes them)");

    if (childOf(card, "rules").IsDefined() && !project.has("atmosphere.yml"))
    {
        warnings.push_back("not built yet: project.yml `rules` (weather, home town, respawn): the scene has the "
            "game's own sky and no weather until the project has an atmosphere.yml (sky, fog, precipitation, "
            "daily_fog)");
    }

    warnings.push_back("not built yet: the map's terrain material file (worlds/<world>/terrain_materials/<map>.yml "
        "and its weight images, made by tools/terrain_materials.py weights), which the game needs to draw the "
        "terrain in a window; headless runs and oymap do not need it");
}

// The original a project is matched against: map_stats.reference, else its base; empty for none.
std::string outdoorOriginalOf(const Project &project)
{
    const YAML::Node card = project.document("project.yml");
    const YAML::Node stats = childOf(card, "map_stats");
    const std::string reference = stats.IsMap() ? textOf(stats, "reference", "") : std::string();
    return reference.empty() ? textOf(card, "base", "") : reference;
}

// Faces of the built models in one plane over each other (core/Coplanar.h): one warning for each pair of parts whose
// faces fight, pairs the original has at the same place left out (`original`: the original's file, read when the
// asset root can be opened here), and a summary line.
void warnOutdoorCoplanar(
    const Project &project,
    const BuildOptions &options,
    const LoweredOutdoorMap &lowered,
    const std::vector<Game::OutdoorBModel> &models,
    bool assetsReadable,
    std::vector<std::string> &warnings)
{
    OutdoorFaceParts parts;

    for (const OutdoorBuildingPlan &building : lowered.buildings)
    {
        parts.push_back(building.faceParts);
    }

    std::vector<OutdoorCoplanarPair> pairs = findOutdoorCoplanarFaces(models);
    const std::string original = outdoorOriginalOf(project);
    std::string matched;
    size_t asOriginal = 0;

    if (!pairs.empty() && !original.empty() && !options.assetRoot.empty() && assetsReadable)
    {
        // The original's places, kept by a service (they depend only on the asset root, the world and the map).
        const std::string key = options.assetRoot.string() + "|" + lowered.world + "|" + original;
        const std::vector<CoplanarPlace> *pPlaces = nullptr;
        std::vector<CoplanarPlace> places;

        if (options.pOriginals != nullptr && options.pOriginals->coplanarPlaces.contains(key))
        {
            pPlaces = &options.pOriginals->coplanarPlaces.at(key);
        }
        else
        {
            AssetSession session;
            LoadedMap map;
            std::string errorMessage;

            if (session.open(options.assetRoot, lowered.world, errorMessage) && loadMap(session, original, map,
                    errorMessage) && map.outdoor)
            {
                const std::vector<Game::OutdoorBModel> &originalModels = map.outdoor->bmodels;
                places = outdoorCoplanarPlaces(originalModels, findOutdoorCoplanarFaces(originalModels));
                pPlaces = &places;

                if (options.pOriginals != nullptr)
                {
                    pPlaces = &(options.pOriginals->coplanarPlaces[key] = places);
                }
            }
        }

        if (pPlaces != nullptr)
        {
            asOriginal = markOutdoorPairsAsOriginal(models, pairs, *pPlaces);
            matched = original;
        }
    }

    std::vector<OutdoorCoplanarPair> fresh;

    for (const OutdoorCoplanarPair &pair : pairs)
    {
        if (!pair.asOriginal)
        {
            fresh.push_back(pair);
        }
    }

    for (const std::string &sentence : describeOutdoorCoplanarGroups(models, fresh, parts))
    {
        warnings.push_back("faces in one plane: " + sentence);
    }

    if (!pairs.empty())
    {
        warnings.push_back("faces in one plane: " + std::to_string(pairs.size()) + " pairs, "
            + (matched.empty() ? std::string("no original to match")
                : std::to_string(asOriginal) + " as the original (" + matched + ")")
            + ", " + std::to_string(fresh.size()) + " new (`oymap audit` lists each pair)");
    }
}

void writeBuildJson(
    JsonWriter &writer,
    const BuildResult &result,
    const LoweredOutdoorMap &lowered,
    const std::vector<OutdoorTravelEdge> &travel,
    const std::vector<ArrivalPoint> &arrivals)
{
    int lowest = OutdoorHighestSample;
    int highest = 0;

    for (const uint8_t sample : lowered.samples)
    {
        lowest = std::min(lowest, static_cast<int>(sample));
        highest = std::max(highest, static_cast<int>(sample));
    }

    writer.beginObject();
    writer.field("ok", result.issues.empty());
    writer.field("map", result.mapFile);
    writer.field("source_revision", result.sourceRevision);
    writer.field("lock_hash", result.lockHash);
    writer.key("counts");
    writer.beginObject();
    writer.field("height_samples", static_cast<uint64_t>(lowered.samples.size()));
    writer.field("lowest", static_cast<int>(lowest * OutdoorHeightStep));
    writer.field("highest", static_cast<int>(highest * OutdoorHeightStep));
    writer.field("water_cells", static_cast<uint64_t>(lowered.waterCells));
    writer.field("shore_cells", static_cast<uint64_t>(lowered.shoreCells));
    writer.field("road_cells", static_cast<uint64_t>(lowered.roadCells));
    writer.field("buildings", static_cast<uint64_t>(lowered.buildings.size()));
    writer.field("entities", static_cast<uint64_t>(result.entities));
    writer.endObject();
    // The parts of each building model by their first face, for `oymap audit`'s messages.
    writer.key("face_parts");
    writer.beginObject();

    for (const OutdoorBuildingPlan &building : lowered.buildings)
    {
        writer.key(building.id);
        writer.beginArray();

        for (size_t face = 0; face < building.faceParts.size(); ++face)
        {
            if (face == 0 || building.faceParts[face] != building.faceParts[face - 1])
            {
                writer.beginArray();
                writer.value(static_cast<uint64_t>(face));
                writer.value(building.faceParts[face]);
                writer.endArray();
            }
        }

        writer.endArray();
    }

    writer.endObject();

    if (lowered.start)
    {
        writer.key("start");
        writer.beginObject();
        writer.field("entrance", lowered.start->entrance);
        writer.field("x", static_cast<int>(std::lround(lowered.start->x)));
        writer.field("y", static_cast<int>(std::lround(lowered.start->y)));
        writer.field("z", static_cast<int>(std::lround(lowered.start->z)));
        writer.field("facing", lowered.start->facing);
        writer.endObject();
    }

    // The buildings with where their doors are: the middle of the door at the floor, and the way it looks.
    writer.key("buildings");
    writer.beginArray();

    for (const OutdoorBuildingPlan &building : lowered.buildings)
    {
        if (building.doors.empty())
        {
            continue;
        }

        const OutdoorDoorPlan &door = building.doors[0];
        const char *pLooks = std::fabs(door.normalX) > std::fabs(door.normalY) ? (door.normalX > 0.0 ? "e" : "w")
            : (door.normalY > 0.0 ? "n" : "s");
        writer.beginObject();
        writer.field("id", building.id);
        writer.field("title", door.title);
        writer.field("event", static_cast<int>(door.event));
        writer.field("house", door.house);
        writer.field("floor", static_cast<int>(std::lround(building.base)));
        writer.key("door");
        writer.beginArray();
        writer.value(static_cast<int>(std::lround(door.x)));
        writer.value(static_cast<int>(std::lround(door.y)));
        writer.value(static_cast<int>(std::lround(door.z)));
        writer.endArray();
        // The way the door looks, as a unit vector and as the nearest side.
        writer.key("normal");
        writer.beginArray();
        writer.value(std::round(door.normalX * 1000.0) / 1000.0);
        writer.value(std::round(door.normalY * 1000.0) / 1000.0);
        writer.endArray();
        writer.field("faces", std::string(pLooks));
        writer.endObject();
    }

    writer.endArray();
    // The ways across the map's sides, as `oymap install` writes them into the travel table.
    writer.key("travel");
    writer.beginArray();

    for (const OutdoorTravelEdge &edge : travel)
    {
        writer.beginObject();
        writer.field("side", edge.side);
        writer.field("to", edge.map);
        writer.field("arrival_side", edge.arrivalSide);
        writer.field("days", edge.days);
        writer.field("way_back", !edge.oneWay);

        if (edge.span)
        {
            writer.key("span");
            writer.beginArray();
            writer.value(edge.span->first);
            writer.value(edge.span->second);
            writer.endArray();
        }

        writer.endObject();
    }

    writer.endArray();
    writer.key("arrivals");
    writer.beginArray();

    for (const ArrivalPoint &arrival : arrivals)
    {
        writer.beginObject();
        writer.field("name", arrival.name);
        writer.field("entrance", arrival.entrance);
        writer.key("at");
        writer.beginArray();
        writer.value(arrival.x);
        writer.value(arrival.y);
        writer.value(arrival.z);
        writer.endArray();
        writer.endObject();
    }

    writer.endArray();
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

// The map as some loader read it against what was lowered: heights, water tiles and the party start.
bool sameAsLowered(
    const Game::OutdoorMapData &map,
    const LoweredOutdoorMap &lowered,
    bool withStart,
    std::string &difference)
{
    if (map.heightMap.size() != NodeTotal || map.tileMap.size() != NodeTotal)
    {
        difference = "the map read back has no 128 x 128 terrain";
        return false;
    }

    for (size_t node = 0; node < NodeTotal; ++node)
    {
        if (map.heightMap[node] != lowered.samples[node])
        {
            difference = "the height at [" + std::to_string(node % OutdoorNodeCount) + ", "
                + std::to_string(node / OutdoorNodeCount) + "] reads back as " + std::to_string(map.heightMap[node])
                + " steps, lowered " + std::to_string(lowered.samples[node]);
            return false;
        }

        if (map.tileMap[node] != lowered.tiles[node])
        {
            difference = "the cell [" + std::to_string(node % OutdoorNodeCount) + ", "
                + std::to_string(node / OutdoorNodeCount) + "] reads back with tile "
                + std::to_string(map.tileMap[node]) + ", laid " + std::to_string(lowered.tiles[node]);
            return false;
        }
    }

    if (!withStart)
    {
        return true;
    }

    for (const Game::OutdoorEntity &entity : map.entities)
    {
        if (entity.name == PartyStartName)
        {
            if (entity.x == std::lround(lowered.start->x) && entity.y == std::lround(lowered.start->y)
                && entity.z == std::lround(lowered.start->z))
            {
                return true;
            }

            difference = "the party start reads back at another place";
            return false;
        }
    }

    difference = "the map read back has no party start";
    return false;
}

// The written files read as the game reads a map: from a mount folder in front of the asset root, through
// core/MapLoad. Leaves nothing behind.
bool readBackThroughAssets(
    const BuildOptions &options,
    const std::filesystem::path &outputDirectory,
    const LoweredOutdoorMap &lowered,
    std::string &difference)
{
    const std::string mapFile = lowered.mapStem + ".odm";
    const std::filesystem::path mount = outputDirectory / "readback";
    const std::filesystem::path maps = mount / "worlds" / lowered.world / "maps";
    const std::filesystem::path events = mount / "worlds" / lowered.world / "events" / "maps";
    std::error_code error;
    std::filesystem::remove_all(mount, error);
    std::filesystem::create_directories(maps, error);
    std::filesystem::create_directories(events, error);
    std::filesystem::copy_file(outputDirectory / mapFile, maps / mapFile, error);
    std::filesystem::copy_file(outputDirectory / (lowered.mapStem + ".scene.yml"),
        maps / (lowered.mapStem + ".scene.yml"), error);
    std::filesystem::copy_file(outputDirectory / (lowered.mapStem + ".lua"), events / (lowered.mapStem + ".lua"),
        error);
    bool same = false;

    if (error)
    {
        difference = "could not lay out " + mount.string() + ": " + error.message();
    }
    else
    {
        AssetSession::setExtraMount(mount);
        AssetSession session;
        LoadedMap map;

        if (!session.open(options.assetRoot, lowered.world, difference) || !loadMap(session, mapFile, map, difference))
        {
            same = false;
        }
        else if (!map.outdoor || !map.outdoorScene || !map.state || !map.events)
        {
            difference = "the map does not load whole";

            for (const std::string &warning : map.warnings)
            {
                difference += "; " + warning;
            }
        }
        else
        {
            same = sameAsLowered(*map.outdoor, lowered, true, difference);
        }

        AssetSession::setExtraMount({});
    }

    std::filesystem::remove_all(mount, error);
    return same;
}

// The names of a `key:` block of a YAML text whose entries are indented two spaces (sky.yml `aliases`), lower
// case.
std::set<std::string> blockKeys(const std::string &text, const std::string &block)
{
    std::set<std::string> keys;
    std::istringstream lines(text);
    std::string line;
    bool inside = false;

    while (std::getline(lines, line))
    {
        if (!line.empty() && line[0] != ' ' && line[0] != '#')
        {
            inside = line.rfind(block + ":", 0) == 0;
            continue;
        }

        const size_t colon = line.find(':');

        if (!inside || line.size() < 3 || line[0] != ' ' || line[1] != ' ' || line[2] == ' ' || line[2] == '#'
            || colon == std::string::npos)
        {
            continue;
        }

        std::string key = line.substr(2, colon - 2);
        std::transform(key.begin(), key.end(), key.begin(), [](unsigned char character)
        {
            return static_cast<char>(std::tolower(character));
        });
        keys.insert(key);
    }

    return keys;
}

// The sky and the continent an outdoor project names, against the asset root's tables: a sky the game has no
// preset for and a continent without a row are refused (core/OutdoorInstall tells what they do).
void checkOutdoorAir(const Project &project, const std::filesystem::path &assetRoot, std::vector<ProjectIssue> &issues,
    std::vector<std::string> &warnings)
{
    const OutdoorWeatherRow row = outdoorWeatherRow(project);
    const YAML::Node atmosphere = project.has("atmosphere.yml") ? project.document("atmosphere.yml")
        : YAML::Node(YAML::NodeType::Undefined);
    std::string sky = textOf(atmosphere, "sky", "");
    std::transform(sky.begin(), sky.end(), sky.begin(), [](unsigned char character)
    {
        return static_cast<char>(std::tolower(character));
    });
    std::string text;

    // The engine's sky names and the world's own (worlds/<id>/rendering/sky/sky.yml, composed into the engine's).
    std::string worldSky;
    const std::string skyWorld = textOf(project.document("project.yml"), "world", "");
    const bool hasWorldSky = !skyWorld.empty()
        && readTextFile(assetRoot / "worlds" / skyWorld / "rendering" / "sky" / "sky.yml", worldSky);

    if (!sky.empty() && readTextFile(assetRoot / "engine" / "rendering" / "sky" / "sky.yml", text))
    {
        std::set<std::string> known = blockKeys(text, "aliases");

        if (hasWorldSky)
        {
            known.merge(blockKeys(worldSky, "aliases"));
        }

        if (!known.empty() && !known.contains(sky))
        {
            std::string some;
            size_t count = 0;

            for (const std::string &name : known)
            {
                some += (count == 0 ? "" : ", ") + name;

                if (++count == 12)
                {
                    break;
                }
            }

            issues.push_back({"atmosphere.yml", "sky", "the game has no sky named " + sky + ": the names are the "
                "`aliases` of engine/rendering/sky/sky.yml (" + some + " ...); or leave `sky` out for the "
                "continent's skies by the weather", "atmosphere"});
        }
    }

    const std::string theme = textOf(atmosphere, "sky_theme", "");

    if (!theme.empty() && readTextFile(assetRoot / "engine" / "rendering" / "sky" / "sky.yml", text))
    {
        std::set<std::string> themes = blockKeys(text, "themes");

        if (hasWorldSky)
        {
            themes.merge(blockKeys(worldSky, "themes"));
        }

        if (!themes.contains(theme))
        {
            std::string listed;

            for (const std::string &name : themes)
            {
                listed += (listed.empty() ? "" : ", ") + name;
            }

            issues.push_back({"atmosphere.yml", "sky_theme", "engine/rendering/sky/sky.yml has no theme `" + theme
                + "`; its themes are " + listed, "atmosphere"});
        }
    }

    if (!row.written)
    {
        if (textOf(project.document("project.yml"), "kind", "") == "outdoor")
        {
            warnings.push_back("air: the map has no number (project.yml map_stats.id), so `oymap install` cannot "
                "write its row of bolster_maps.txt: it has no continent, the game's fallback sky, and no rain or "
                "snow");
        }

        return;
    }

    if (row.continent <= 0 && row.reference.empty())
    {
        warnings.push_back("air: the world " + textOf(project.document("project.yml"), "world", "")
            + " has no continent of its own: say project.yml map_stats.continent (a row of engine/data_tables/"
            "continent_settings.txt), or the map is drawn under the game's fallback sky");
    }

    // The engine's continents and the world's own (its continent_settings contribution, Xeen's faces 6 and 7).
    const std::string world = textOf(project.document("project.yml"), "world", "");

    if (row.continentGiven && readWorldTable(assetRoot, world, "continent_settings.txt", "continent_settings", text))
    {
        std::istringstream lines(text);
        std::string line;
        std::string listed;
        bool found = false;

        while (std::getline(lines, line))
        {
            const size_t tab = line.find('\t');
            const std::string number = line.substr(0, tab);
            const size_t nameEnd = tab == std::string::npos ? tab : line.find('\t', tab + 1);

            if (number.empty() || !std::all_of(number.begin(), number.end(), [](unsigned char character)
                {
                    return std::isdigit(character) != 0;
                }))
            {
                continue;
            }

            found = found || number == std::to_string(row.continent);
            listed += (listed.empty() ? "" : ", ") + number + " "
                + (tab == std::string::npos ? std::string() : line.substr(tab + 1, nameEnd - tab - 1));
        }

        if (!found)
        {
            issues.push_back({"project.yml", "map_stats.continent", "there is no continent "
                + std::to_string(row.continent) + " in engine/data_tables/continent_settings.txt or the world's; "
                "they have " + listed,
                "atmosphere"});
        }
    }
}

// The sketch's own checks, sorted: what makes the lowering unsound is an issue, what it copes with is a warning.
void checkSketch(const Project &project, std::vector<ProjectIssue> &issues, std::vector<std::string> *pWarnings)
{
    std::vector<ProjectIssue> found;
    validateSketch(project, found);
    size_t heights = 0;
    size_t coverage = 0;

    // The checks set each finding's severity where they find it (core/Sketch.cpp): errors stop the build, the
    // warnings (heights and coverage findings the lowering copes with) are counted into the build's warnings.
    for (const ProjectIssue &issue : found)
    {
        if (issue.isError())
        {
            issues.push_back(issue);
        }
        else if (issue.code == "heights")
        {
            ++heights;
        }
        else if (issue.code == "coverage")
        {
            ++coverage;
        }
    }

    if (pWarnings != nullptr && heights != 0)
    {
        pWarnings->push_back("sketch checks: " + std::to_string(heights) + " findings on heights (a point outside its "
            "band's range, water above its shore; see oymap validate); the build takes the points and levels as "
            "drawn");
    }

    if (pWarnings != nullptr && coverage != 0)
    {
        pWarnings->push_back("sketch checks: " + std::to_string(coverage) + " plan entries without a place in the "
            "sketch (see oymap validate)");
    }
}
}

void validateOutdoorProject(const Project &project, std::vector<ProjectIssue> &issues)
{
    validateOutdoorProject(project, std::filesystem::path(), issues);
}

void validateOutdoorProject(
    const Project &project,
    const std::filesystem::path &assetRoot,
    std::vector<ProjectIssue> &issues)
{
    BuildOptions options;
    options.assetRoot = assetRoot;
    validateOutdoorProject(project, options, issues);
}

bool validateOutdoorProject(const Project &project, const BuildOptions &givenOptions, std::vector<ProjectIssue> &issues)
{
    if (!project.has("sketch.yml"))
    {
        return false;
    }

    // Everything the build checks, without writing: the lowering, the buildings and structures, the places of
    // spawn points and scattered decorations, and with an asset root the names of decorations and textures.
    BuildOptions options = givenOptions;
    options.dryRun = true;
    options.outputDirectory.clear();
    BuildResult result;
    const bool built = buildOutdoorProject(project, options, result);

    for (const ProjectIssue &issue : result.issues)
    {
        const bool known = std::any_of(issues.begin(), issues.end(), [&issue](const ProjectIssue &other)
        {
            return other.file == issue.file && other.path == issue.path && other.message == issue.message;
        });

        if (!known)
        {
            issues.push_back(issue);
        }
    }

    return built;
}

// What the studio's view draws (core/View.h): the map as read back, and its tiles' textures.
void fillOutdoorView(const Project &project, const BuildOptions &options, const LoweredOutdoorMap &lowered,
    const Game::OutdoorMapData &readBack, const std::string &tileTableText)
{
    if (options.pOutdoorView == nullptr)
    {
        return;
    }

    OutdoorView &view = *options.pOutdoorView;
    view.world = textOf(project.document("project.yml"), "world", "");
    view.map = readBack;
    resolveOutdoorTileTextures(view, tileTableText);
    view.hasStart = lowered.start.has_value();

    if (lowered.start)
    {
        view.start = {lowered.start->x, lowered.start->y, lowered.start->z};
        view.startFacing = lowered.start->facing;
    }
}

bool buildOutdoorProject(const Project &project, const BuildOptions &options, BuildResult &result)
{
    {
        // The sketch's checks read words to check them, not to build: not what the read record is for.
        SketchReadPause pause;
        checkSketch(project, result.issues, &result.warnings);
    }

    if (!result.issues.empty())
    {
        return false;
    }

    LoweredOutdoorMap lowered;
    const std::string styleWorld =
        studioStyleWorld(options.assetRoot, textOf(project.document("project.yml"), "world", ""));

    // The texture classes' door pictures (F2: a wing door becomes a pair, a leaf shows its picture whole).
    const OutdoorDoorPictures doorPictures =
        readOutdoorDoorPictures(options.assetRoot, textOf(project.document("project.yml"), "world", ""));

    if (!lowerOutdoorProject(project, lowered, result.issues, options.pLand, styleWorld, &doorPictures)
        || !result.issues.empty()
        || !lowered.start)
    {
        return false;
    }

    // The buildings: one model each. Event numbers are kept in ids.lock.yml: a number once given to a door stays
    // that door's, whatever is added to the sketch later.
    IdsLock ids = IdsLock::fromDocument(project.document("ids.lock.yml"));
    std::vector<Game::OutdoorBModel> models;
    std::vector<OutdoorEventPlan> events;

    // What the map's events test and do, in the words of the indoor wiring (core/OutdoorEvents).
    OutdoorEventWords words(project, options.assetRoot, ids, result.issues);
    const YAML::Node sketch = project.document("sketch.yml");

    // First every id that has a number, so a new id never takes the number of one that comes later in the sketch.
    for (OutdoorBuildingPlan &building : lowered.buildings)
    {
        for (size_t index = 0; index < building.doors.size(); ++index)
        {
            OutdoorDoorPlan &door = building.doors[index];
            const YAML::Node doorNode = sketchNodeAt(sketch, door.path);
            const bool acts = OutdoorEventWords::hasActions(doorNode);

            // A door that carries another's event gets it once every building's events are known (below).
            if (!door.sameEventAs.empty())
            {
                continue;
            }

            if (door.house == 0 && door.toMap.empty() && !acts)
            {
                for (const char *pKey : {"condition", "locked_text", "else_effects", "once"})
                {
                    if (childOf(doorNode, pKey).IsDefined())
                    {
                        result.issues.push_back({"sketch.yml", door.path + "." + pKey, std::string("`") + pKey
                            + "` belongs to what the door does, and this door opens nothing: give it `house`, "
                            "`into`, `effects` or `lua`, or leave `" + pKey + "` out", "event"});
                    }
                }

                continue;
            }

            const std::string id = "evt:door:" + building.id + (index == 0 ? "" : "." + std::to_string(index + 1));
            door.event = static_cast<uint16_t>(IdsLock::number(ids.events, id, 1));
            std::vector<std::string> body;
            // `once`, then the lock: unless the condition holds, else_effects, locked_text and no more.
            words.lock(doorNode, door.path, "once.door:" + building.id
                + (index == 0 ? "" : "." + std::to_string(index + 1)), body);

            if (door.house != 0)
            {
                body.push_back("evt.EnterHouse(" + std::to_string(door.house) + ")");
            }
            else if (!door.toMap.empty())
            {
                // A named arrival of that map (D-4), from its installed <stem>.studio.yml.
                if (!door.arrivalName.empty())
                {
                    MapArrival found;
                    std::string warning;

                    if (!resolveMapArrival(options.assetRoot, options.mountRoot, lowered.world, door.toMap,
                            door.arrivalName, found, warning))
                    {
                        result.issues.push_back({"sketch.yml", door.path + ".into.arrival", warning, "reference"});
                        continue;
                    }

                    if (!warning.empty())
                    {
                        result.warnings.push_back(door.path + ".into.arrival: " + warning);
                    }

                    std::copy(std::begin(found.at), std::end(found.at), door.arrival);
                    door.arrivalFacing = door.arrivalFacingGiven ? door.arrivalFacing : found.facing;
                }

                body.push_back("evt.MoveToMap(" + std::to_string(door.arrival[0]) + ", "
                    + std::to_string(door.arrival[1]) + ", " + std::to_string(door.arrival[2]) + ", "
                    + std::to_string(door.arrivalFacing) + ", 0, 0, " + std::to_string(door.screen.text) + ", "
                    + std::to_string(door.screen.picture) + ", " + luaQuoted(door.toMap)
                    + moveScreenOptions(door.screen) + ")");
            }

            words.actions(doorNode, door.path, body);
            events.push_back({door.event, id, door.title, body});
        }

        // A building without a door of its own has nothing that runs the plot's words.
        const YAML::Node buildingNode = sketchNodeAt(sketch, building.path);
        const bool ownDoor = !building.doors.empty() && building.doors[0].path == building.path;

        if (!ownDoor && (OutdoorEventWords::hasActions(buildingNode) || childOf(buildingNode, "condition").IsDefined()))
        {
            result.issues.push_back({"sketch.yml", building.path, building.id + " has no door of its own (`door: "
                "none`), so nothing would run its `effects`, `lua` or `condition`: put them on the part that is "
                "clicked (a part with a `title` and `effects` or `lua`), or give the building a door", "event"});
        }

        // A building runs its words from a click on its door or parts; nothing steps on it.
        if (childOf(buildingNode, "trigger").IsDefined())
        {
            result.issues.push_back({"sketch.yml", building.path + ".trigger", "a building has no `trigger`: its "
                "door and parts run their words on a click. What runs when the party steps somewhere is a "
                "structure that is a model (`kind: platform`, `wall`, `stairs`, `bridge`) with `trigger: step`",
                "event"});
        }

        if (building.hintShared)
        {
            // Batch O-H: one event for every thing whose shared hint says the same.
            const std::string id = outdoorSharedHintId(building.hint);
            building.nameEvent = static_cast<uint16_t>(IdsLock::number(ids.events, id, 1));

            if (std::none_of(events.begin(), events.end(), [&](const OutdoorEventPlan &other)
                { return other.id == id; }))
            {
                events.push_back({building.nameEvent, id, building.hint, {}});
            }
        }
        else if (!building.title.empty() || !building.hint.empty())
        {
            const std::string id = "evt:name:" + building.id;
            building.nameEvent = static_cast<uint16_t>(IdsLock::number(ids.events, id, 1));
            events.push_back({building.nameEvent, id, building.hint.empty() ? building.title : building.hint, {}});
        }

        // Batch O-H: boards on a part's wall with an event of their own (a `title`, a `house`).
        for (size_t partIndex = 0; partIndex < building.parts.size(); ++partIndex)
        {
            for (size_t signIndex = 0; signIndex < building.parts[partIndex].signs.size(); ++signIndex)
            {
                OutdoorWallSignPlan &sign = building.parts[partIndex].signs[signIndex];

                if (sign.title.empty())
                {
                    continue;
                }

                const std::string id = "evt:sign:" + building.id + "." + std::to_string(partIndex) + "."
                    + std::to_string(signIndex);
                sign.event = static_cast<uint16_t>(IdsLock::number(ids.events, id, 1));
                std::vector<std::string> body;

                if (sign.house != 0)
                {
                    body.push_back("evt.EnterHouse(" + std::to_string(sign.house) + ")");
                }

                events.push_back({sign.event, id, sign.title, body});
            }
        }

        // A part with a name of its own, or that is clicked itself (a shop of a joined block, a guild's fountain):
        // its faces that are no door carry an event of their own. Parts of one building that say and do the same
        // are one thing (a shop drawn as three boxes): they share the event.
        std::vector<size_t> partEvents;

        for (size_t index = 0; index < building.parts.size(); ++index)
        {
            OutdoorPartPlan &part = building.parts[index];
            const YAML::Node partNode = part.path.empty() ? YAML::Node(YAML::NodeType::Undefined)
                : sketchNodeAt(sketch, part.path);
            // A building without `parts` is one part drawn by the plot itself: the plot's words are its door's.
            const bool ownNode = partNode.IsDefined() && part.path.find(".parts[") != std::string::npos;
            const bool acts = ownNode && OutdoorEventWords::hasActions(partNode);

            if (!ownNode || (part.title.empty() && !acts))
            {
                for (const char *pKey : {"condition", "locked_text", "else_effects", "once"})
                {
                    if (ownNode && childOf(partNode, pKey).IsDefined())
                    {
                        result.issues.push_back({"sketch.yml", part.path + "." + pKey, std::string("`") + pKey
                            + "` belongs to what a click on the part does, and this part does nothing: give it "
                            "`effects` or `lua`, or leave `" + pKey + "` out", "event"});
                    }
                }

                continue;
            }

            const std::string id = "evt:part:" + building.id + "/"
                + (part.id.empty() ? std::to_string(index) : part.id);
            const std::string title = part.title.empty() ? building.title : part.title;
            std::vector<std::string> body;

            if (acts)
            {
                // `once` is one memory for the parts that share the event: kept under the first's name.
                words.lock(partNode, part.path, "once.part:" + building.id + "/" + title, body);
                words.actions(partNode, part.path, body);
            }

            for (const size_t other : partEvents)
            {
                if (events[other].title == title && events[other].body == body)
                {
                    part.event = events[other].number;
                }
            }

            if (part.event != 0)
            {
                continue;
            }

            part.event = static_cast<uint16_t>(IdsLock::number(ids.events, id, 1));
            partEvents.push_back(events.size());
            events.push_back({part.event, id, title, body});
        }
    }

    // What stands on the map beside its houses: the structures' models go after the buildings'. Their handlers
    // are written before any model is raised, so that every model knows what events change of it.
    OutdoorThings things;

    // The buildings' events a structure may carry (`same_event_as`: a sign with its shop's door).
    for (const OutdoorBuildingPlan &building : lowered.buildings)
    {
        const std::string key = "building:" + (building.id.rfind("building:", 0) == 0
            ? building.id.substr(9) : building.id);
        uint16_t own = building.nameEvent;

        for (const OutdoorDoorPlan &door : building.doors)
        {
            const size_t listed = door.path.rfind(".doors[");
            const int number = door.path == building.path ? 0
                : (listed == std::string::npos ? -1 : std::atoi(door.path.c_str() + listed + 7) + 1);

            if (number >= 0 && door.event != 0)
            {
                things.buildingEvents[key + "/door:" + std::to_string(number)] = door.event;
            }

            own = number == 0 && door.event != 0 ? door.event : own;
        }

        things.buildingEvents[key] = own;

        for (size_t index = 0; index < building.parts.size(); ++index)
        {
            const OutdoorPartPlan &part = building.parts[index];

            if (part.event != 0)
            {
                things.buildingEvents[key + "/part:" + (part.id.empty() ? std::to_string(index) : part.id)]
                    = part.event;
            }
        }
    }

    // Doors that carry another door's event (`doors[].same_event_as`).
    for (OutdoorBuildingPlan &building : lowered.buildings)
    {
        for (OutdoorDoorPlan &door : building.doors)
        {
            if (door.sameEventAs.empty())
            {
                continue;
            }

            const std::map<std::string, uint16_t>::const_iterator found = things.buildingEvents.find(door.sameEventAs);

            if (found == things.buildingEvents.end() || found->second == 0)
            {
                result.issues.push_back({"sketch.yml", door.path + ".same_event_as", door.sameEventAs
                    + " carries no event: a door's event is there when the door opens something (`house`, `into`, "
                    "`effects`) and does not itself carry another's; a building's name event when it has a "
                    "`title`", "event"});
                continue;
            }

            door.event = found->second;
        }
    }

    if (!raiseOutdoorThings(project, lowered, options.assetRoot, ids, words, things, result.issues,
            result.warnings, options.mountRoot))
    {
        return false;
    }

    for (OutdoorBuildingPlan &building : lowered.buildings)
    {
        Game::OutdoorBModel model = raiseOutdoorBuilding(building);
        words.applyToModel(building.id, model);
        models.push_back(model);
    }

    for (Game::OutdoorBModel &model : things.models)
    {
        words.applyToModel(model.name, model);
    }

    if (!result.issues.empty())
    {
        return false;
    }

    words.finish(result.warnings);

    for (const std::string &id : things.decorationIds)
    {
        const std::map<std::string, OutdoorEventTarget>::const_iterator target = words.targets().find(id);
        things.decorationNumbers.push_back(words.decorationNumber(id));
        things.decorationHidden.push_back(target != words.targets().end() && target->second.hidden);
    }

    models.insert(models.end(), things.models.begin(), things.models.end());
    // A shared hint said by buildings and structures alike is one event (batch O-H).
    for (const OutdoorEventPlan &event : things.events)
    {
        if (event.id.rfind(outdoorSharedHintId(""), 0) != 0 || std::none_of(events.begin(), events.end(),
                [&](const OutdoorEventPlan &other) { return other.id == event.id; }))
        {
            events.push_back(event);
        }
    }

    if (!options.assetRoot.empty())
    {
        checkOutdoorAir(project, options.assetRoot, result.issues, result.warnings);
        // The world's own textures; a world without kits of its own (Xeen, built in MM7's style) takes any shipped
        // world's, as the game mounts every world's textures for its maps (MM6's royal walls, MM8's water).
        std::set<std::string> known = outdoorTextureNames(options.assetRoot, lowered.world, options.mountRoot);
        std::error_code worldsError;

        for (std::filesystem::directory_iterator other(options.assetRoot / "worlds", worldsError), end;
             lowered.styleWorld != lowered.world && !worldsError && other != end; other.increment(worldsError))
        {
            if (other->is_directory(worldsError))
            {
                known.merge(outdoorTextureNames(options.assetRoot, other->path().filename().string(),
                    options.mountRoot));
            }
        }

        checkOutdoorBuildingTextures(lowered.buildings, known, lowered.world, result.issues);
        checkOutdoorModelTextures(things.models, known, lowered.world, result.issues);

        // The textures events give to faces.
        for (const std::pair<const std::string, std::string> &named : words.namedTextures())
        {
            std::string name = named.first;
            std::transform(name.begin(), name.end(), name.begin(), [](unsigned char character)
            {
                return static_cast<char>(std::tolower(character));
            });

            if (!known.empty() && !known.contains(name))
            {
                result.issues.push_back({"sketch.yml", named.second, "the world " + lowered.world
                    + " has no texture `" + named.first + "`: `oymap assets <text> --kind texture --world "
                    + lowered.world + "` lists the textures it has", "texture"});
            }
        }

        if (!result.issues.empty())
        {
            return false;
        }
    }

    result.warnings.insert(result.warnings.end(), lowered.warnings.begin(), lowered.warnings.end());
    {
        SketchReadPause pause;
        listNotBuilt(project, result.warnings);
    }
    // With an asset root at hand, the tile sets must be what they are taken for in that root's tile table.
    std::string tileTableText;

    if (!options.assetRoot.empty())
    {
        const std::filesystem::path tablePath = options.assetRoot / "engine" / "data_tables" / lowered.tileTable;
        std::string &table = tileTableText;

        if (!readTextFile(tablePath, table))
        {
            result.issues.push_back({"", "", "could not read the tile table engine/data_tables/" + lowered.tileTable
                + " of the asset root", "io"});
            return false;
        }

        const std::string wrong = checkOutdoorTileTable(lowered, table);

        if (!wrong.empty())
        {
            result.issues.push_back({"", "", lowered.tileTable + ": " + wrong, "build"});
            return false;
        }
    }

    const std::string stem = lowered.mapStem;
    result.mapFile = stem + ".odm";
    Game::OutdoorMapData map;
    // The version of a new map, as the editor makes them: the layout of Might and Magic 8.
    map.version = 8;
    map.fileName = result.mapFile;
    map.name = textOf(project.document("project.yml"), "name", stem);
    map.masterTile = lowered.masterTile;
    map.tileSetLookupIndices = lowered.tileSets;
    map.heightMap = lowered.samples;
    map.tileMap = lowered.tiles;
    map.attributeMap.assign(NodeTotal, 0);
    map.decorationMap.assign(NodeTotal, 0);
    map.bmodels = models;

    const std::optional<std::vector<uint8_t>> odm = Game::OutdoorMapDataWriter().buildBytes(map);

    if (!odm)
    {
        result.issues.push_back({"", "", "the built map could not be written as ODM", "build"});
        return false;
    }

    // The game's own readers must accept the map and the scene, apply the one to the other, and give back what was
    // lowered.
    std::optional<Game::OutdoorMapData> readBack = Game::OutdoorMapDataLoader().loadFromBytes(*odm);
    std::string errorMessage;

    if (!readBack || !sameAsLowered(*readBack, lowered, false, errorMessage))
    {
        result.issues.push_back({"", "", "the ODM the build wrote does not read back: "
            + (readBack ? errorMessage : std::string("the game's loader refuses it")), "build"});
        return false;
    }

    OutdoorPlaces places;
    std::string decorationTable;

    // The engine's decorations and the world's own (world.yml `decorations`: Xeen's basalt boulders, A5 on X7).
    if (!options.assetRoot.empty())
    {
        readWorldTable(options.assetRoot, lowered.world, "decoration_data.txt", "decorations", decorationTable);
    }

    if (!placeOutdoorThings(project, lowered, decorationTable, places, result.issues, result.warnings,
            things.covered))
    {
        return false;
    }

    warnOutdoorMonsterHostility(project, options.assetRoot, things, places, result.warnings);

    // The number events change a scatter entry's decorations by: the same for every decoration of one `id`.
    for (OutdoorPlacedDecoration &decoration : places.decorations)
    {
        decoration.number = decoration.target.empty() ? 0 : words.decorationNumber(decoration.target);
    }

    // A scatter entry's `event`: one handler that a click on any of its decorations runs (the words of a click:
    // `title`, `condition`, `locked_text`, `else_effects`, `effects`, `once`, `lua`). Entries of one id share the
    // first one's.
    {
        const YAML::Node scatter = childOf(project.document("sketch.yml"), "scatter");
        std::map<size_t, uint16_t> eventOfEntry;
        std::map<std::string, uint16_t> eventOfId;

        for (size_t index = 0; scatter.IsDefined() && scatter.IsSequence() && index < scatter.size(); ++index)
        {
            const YAML::Node node = childOf(scatter[index], "event");
            const std::string path = "scatter[" + std::to_string(index) + "].event";

            if (!node.IsDefined())
            {
                continue;
            }

            if (!node.IsMap() || (!OutdoorEventWords::hasActions(node) && textOf(node, "title", "").empty()))
            {
                result.issues.push_back({"sketch.yml", path, "a scatter entry's `event` is what a click on any of "
                    "its decorations does, in the words of a click: {title: Flowers, effects: [...], lua: ...}",
                    "event"});
                continue;
            }

            const std::string id = textOf(scatter[index], "id", "").empty() ? "scatter" + std::to_string(index)
                : textOf(scatter[index], "id", "");

            if (const std::map<std::string, uint16_t>::const_iterator known = eventOfId.find(id);
                known != eventOfId.end())
            {
                eventOfEntry[index] = known->second;
                continue;
            }

            OutdoorEventPlan event;
            event.id = "evt:scatter:" + id;
            event.number = static_cast<uint16_t>(IdsLock::number(ids.events, event.id, 1));
            event.title = textOf(node, "title", "");
            words.lock(node, path, "once.scatter:" + id, event.body);
            words.actions(node, path, event.body);
            events.push_back(event);
            eventOfEntry[index] = event.number;
            eventOfId[id] = event.number;
        }

        for (OutdoorPlacedDecoration &decoration : places.decorations)
        {
            const std::map<size_t, uint16_t>::const_iterator found =
                eventOfEntry.find(static_cast<size_t>(decoration.entry));
            decoration.event = decoration.entry >= 0 && found != eventOfEntry.end() ? found->second : 0;
        }

        if (!result.issues.empty())
        {
            return false;
        }
    }

    // Every face that carries an event: the game clears the events of all faces and sets these.
    std::vector<DoorFace> doors;

    for (size_t model = 0; model < models.size(); ++model)
    {
        for (size_t face = 0; face < models[model].faces.size(); ++face)
        {
            const Game::OutdoorBModelFace &modelFace = models[model].faces[face];

            // Also the faces events change (their number) and those that start hidden (their bits).
            if (modelFace.cogTriggeredNumber != 0 || modelFace.cogNumber != 0
                || (modelFace.attributes & Game::faceAttributeBit(Game::FaceAttribute::Invisible)) != 0)
            {
                doors.push_back({model, face, modelFace.attributes, modelFace.cogTriggeredNumber,
                    modelFace.cogNumber});
            }
        }
    }

    // The structures laid `translucent: true` (D5's Barrier curtain): every face of the models named after them.
    std::vector<std::pair<size_t, size_t>> translucentFaces;
    const YAML::Node structureNodes = childOf(project.document("sketch.yml"), "structures");

    for (size_t index = 0; structureNodes.IsDefined() && structureNodes.IsSequence() && index < structureNodes.size();
         ++index)
    {
        const YAML::Node node = structureNodes[index];

        if (textOf(node, "translucent", "false") != "true")
        {
            continue;
        }

        const std::string id = textOf(node, "id", "");
        bool found = false;

        for (size_t model = 0; model < models.size(); ++model)
        {
            if (models[model].name != id)
            {
                continue;
            }

            found = true;

            for (size_t face = 0; face < models[model].faces.size(); ++face)
            {
                translucentFaces.emplace_back(model, face);
            }
        }

        if (!found)
        {
            result.warnings.push_back("structures[" + std::to_string(index) + "].translucent: " + id
                + " built no model of its own, so nothing is drawn see-through");
        }
    }

    std::sort(events.begin(), events.end(), [](const OutdoorEventPlan &left, const OutdoorEventPlan &right)
    {
        return left.number < right.number;
    });
    std::vector<std::string> sidesWithoutArrival;
    const std::vector<ArrivalPoint> arrivals = arrivalPoints(project, lowered, models, sidesWithoutArrival);
    // (Also for a dry build: what validate says.)
    result.arrivals = namedArrivals(project, lowered, models, &result.warnings);

    if (!sidesWithoutArrival.empty())
    {
        std::string sides;

        for (const std::string &side : sidesWithoutArrival)
        {
            sides += (sides.empty() ? "" : ", ") + side;
        }

        result.warnings.push_back("arrivals: no arrival point for the side " + sides + ": a party that comes from "
            "there arrives at the map's party start. Give plan.yml an entrance with `kind: arrival` (or both) and "
            "`neighbour: <the project.yml edge neighbour>`, and sketch.yml a point for it");
    }

    // Ground mist: read as the game reads a scene's `mist`, so the scene is not refused at load.
    if (project.has("atmosphere.yml"))
    {
        const YAML::Node mist = childOf(project.document("atmosphere.yml"), "mist");
        Game::MapMist parsedMist;
        std::string mistError;

        if (mist.IsDefined() && !Game::parseSceneMistNode(mist, parsedMist, mistError))
        {
            result.issues.push_back({"atmosphere.yml", "mist", "the game refuses this mist: " + mistError
                + " (devdocs/MIST.md)", "atmosphere"});
            return false;
        }
    }

    YAML::Node sceneNode;

    if (options.dryRun && options.commitCheck)
    {
        // A commit's check: the scene's write and its reader check are the build's (2.4.3).
        result.entities = 0;
        result.events = events.size();
        result.doors = lowered.buildings.size();

        for (const Game::OutdoorBModel &model : readBack->bmodels)
        {
            result.faces += model.faces.size();
            result.vertices += model.vertices.size();
        }

        fillOutdoorView(project, options, lowered, *readBack, tileTableText);
        return true;
    }

    const std::string sceneText = writeSceneText(lowered, doors, translucentFaces, places, things, arrivals,
        project.has("atmosphere.yml") ? project.document("atmosphere.yml") : YAML::Node(YAML::NodeType::Undefined),
        textOf(childOf(project.document("project.yml"), "rules"), "no_spells", "") == "true", sceneNode);
    const std::optional<Game::OutdoorSceneData> scene =
        Game::OutdoorSceneYmlLoader().loadFromText(sceneText, errorMessage);

    if (!scene)
    {
        result.issues.push_back({"", "", "the scene file the build wrote is not accepted: " + errorMessage, "build"});
        return false;
    }

    Game::MapDeltaData delta;

    if (!Game::buildOutdoorMapStateFromScene(*scene, *readBack, delta, errorMessage))
    {
        result.issues.push_back({"", "", "the scene file does not apply to the built map: " + errorMessage, "build"});
        return false;
    }

    if (!sameAsLowered(*readBack, lowered, true, errorMessage))
    {
        result.issues.push_back({"", "", "the built map with its scene applied is not what was lowered: "
            + errorMessage, "build"});
        return false;
    }

    result.entities = readBack->entities.size();
    result.spawns = readBack->spawns.size();
    // For an outdoor map: `sectors` stays 0, `faces` and `vertices` are the building models', `doors` their doors
    // with an event.
    result.events = events.size();
    result.doors = lowered.buildings.size();

    for (const Game::OutdoorBModel &model : readBack->bmodels)
    {
        result.faces += model.faces.size();
        result.vertices += model.vertices.size();
    }
    const std::filesystem::path outputDirectory =
        options.outputDirectory.empty() ? project.root / "build" : options.outputDirectory;
    // Also under Node: the wasm build passes HOME to PhysicsFS (wasm/node_env.pre.js).
    const bool assetsReadable = PHYSFS_isInit() == 0;
    const bool throughAssets = !options.dryRun && !options.assetRoot.empty() && assetsReadable;
    warnOutdoorCoplanar(project, options, lowered, models, assetsReadable, result.warnings);

    fillOutdoorView(project, options, lowered, *readBack, tileTableText);

    if (!options.dryRun && !throughAssets)
    {
        result.warnings.push_back(options.assetRoot.empty()
            ? "the build was read back by the game's loaders in memory only: name an asset root (--assets) to have it "
              "read from a mount folder as the game reads it"
            : "the build was read back by the game's loaders in memory only: the asset file system cannot be opened "
              "here (it is open already, or this is the WebAssembly core)");
    }

    if (options.dryRun)
    {
        return true;
    }

    const std::string luaText = writeLuaText(project, lowered, events, things);
    const std::string lockText = writeCanonicalYaml(ids.toDocument(), SchemaSet::builtIn(), "ids_lock.schema.json");
    const std::map<std::string, ProjectFile>::const_iterator currentLock = project.files.find("ids.lock.yml");
    result.lockChanged = currentLock == project.files.end() || currentLock->second.text != lockText;
    result.sourceRevision = projectRevision(project);
    result.lockHash = lockHashOfText(&lockText);
    // The lock is a record (S5_BROWSER_EDITOR.md 2.4.1): written under the project lock and logged; an outdoor build
    // never drops an entry.
    bool lockWritten = false;

    if (!writeBinaryFileAtomically(outputDirectory / result.mapFile, *odm, errorMessage)
        || !writeTextFileAtomically(outputDirectory / (stem + ".scene.yml"), sceneText, errorMessage)
        || !writeTextFileAtomically(outputDirectory / (stem + ".lua"), luaText, errorMessage)
        || (result.lockChanged
            && !writeLockRecord(project.root, lockText, result.sourceRevision, "build", lockWritten, errorMessage)))
    {
        result.issues.push_back({"", "", errorMessage, "io"});
        return false;
    }

    if (throughAssets && !readBackThroughAssets(options, outputDirectory, lowered, errorMessage))
    {
        result.issues.push_back({"", "", "the written map, read as the game reads it, is not what was lowered: "
            + errorMessage, "build"});
        return false;
    }

    // The walk's movement state and terrain pack (core/Walk.h), read through the asset root as the game reads the
    // tile tables; without one the walk cannot go outdoors.
    std::vector<std::string> walkFiles;

    if (throughAssets)
    {
        AssetSession session;
        std::vector<uint8_t> terrainPack;

        if (session.open(options.assetRoot, lowered.world, errorMessage))
        {
            terrainPack = writeWalkTerrainPack(session.files(), *readBack);
        }

        WalkStateHeader walkHeader;
        walkHeader.kind = "outdoor";
        walkHeader.world = lowered.world;
        walkHeader.map = result.mapFile;
        walkHeader.party = walkPartyOfWorld(options.assetRoot, lowered.world, true);

        // A map with edges to travel by gets the merged outdoor travel rows' bounds (game/tables/MapStats.cpp,
        // MergedOutdoorBounds*), past which the game asks the party to travel.
        if (!outdoorTravelEdges(project).empty())
        {
            walkHeader.bounds = std::array<int, 4>{-23143, 23143, -23143, 23143};
        }

        if (const std::optional<Game::OutdoorMapData> plain = Game::OutdoorMapDataLoader().loadFromBytes(*odm))
        {
            walkHeader.faceAttributes = walkFaceAttributeChanges(*plain, *readBack);
        }

        if (terrainPack.empty())
        {
            result.warnings.push_back(
                "no terrain pack for walk mode: the tile tables did not load from the asset root");
        }
        else if (!writeBinaryFileAtomically(outputDirectory / (stem + ".walk.terrain"), terrainPack, errorMessage)
            || !writeTextFileAtomically(outputDirectory / (stem + ".walk.yml"),
                writeWalkStateText(walkHeader, sceneNode), errorMessage))
        {
            result.issues.push_back({"", "", errorMessage, "io"});
            return false;
        }
        else
        {
            walkFiles = {stem + ".walk.yml", stem + ".walk.terrain"};
        }
    }

    JsonWriter buildJson(true);
    writeBuildJson(buildJson, result, lowered, outdoorTravelEdges(project), arrivals);
    std::string buildJsonText = buildJson.take();
    buildJsonText.push_back('\n');

    if (!writeTextFileAtomically(outputDirectory / "build.json", buildJsonText, errorMessage))
    {
        result.issues.push_back({"", "", errorMessage, "io"});
        return false;
    }

    result.files = {result.mapFile, stem + ".scene.yml", stem + ".lua", "build.json"};
    result.files.insert(result.files.end(), walkFiles.begin(), walkFiles.end());
    return true;
}
}
