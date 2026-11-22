#include "core/SceneOverlay.h"

#include "core/CanonicalYaml.h"
#include "core/IndoorBuild.h"
#include "core/MapLoad.h"
#include "core/SketchRead.h"

#include "game/gameplay/CinematicLibrary.h"
#include "game/indoor/IndoorGeometryUtils.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <map>
#include <optional>
#include <set>

namespace OpenYAMM::Studio
{
namespace
{
// Numbers of the overlay's own things: above anything MM9's converters give (DAT indices, 40000 + index for lights).
constexpr int FirstOverlayLightKey = 49001;
constexpr int FirstOverlayKey = 60001;

// The sound a destructible breaks with when it names none, by material (the MM9 converter's most common ones).
const char *materialSound(const std::string &material)
{
    if (material == "wood")
    {
        return "Events/shatterwood02.wav";
    }

    if (material == "glass")
    {
        return "Events/glass_smash.wav";
    }

    if (material == "metal")
    {
        return "Events/metalbreak03.wav";
    }

    return "Events/stonecrumble.wav";
}

std::string idSafe(const std::string &text)
{
    std::string result;

    for (const char character : text)
    {
        const char lower = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
        result.push_back((lower >= 'a' && lower <= 'z') || (lower >= '0' && lower <= '9') ? lower : '_');
    }

    return result.empty() ? "volume" : result;
}

std::string toLower(std::string text)
{
    std::transform(text.begin(), text.end(), text.begin(), [](unsigned char character)
    {
        return static_cast<char>(std::tolower(character));
    });
    return text;
}

// The name after the kind: `light:beacon` -> `beacon`.
std::string nameOf(const std::string &id)
{
    const size_t colon = id.find(':');
    return colon == std::string::npos ? id : id.substr(colon + 1);
}

std::string kindOf(const std::string &id)
{
    const size_t colon = id.find(':');
    return colon == std::string::npos ? std::string() : id.substr(0, colon);
}

YAML::Node numberNode(double value)
{
    if (value == std::floor(value) && std::fabs(value) < 1.0e9)
    {
        return YAML::Node(static_cast<long long>(value));
    }

    return YAML::Node(value);
}

YAML::Node numbers(std::initializer_list<double> values)
{
    YAML::Node sequence(YAML::NodeType::Sequence);

    for (const double value : values)
    {
        sequence.push_back(numberNode(value));
    }

    sequence.SetStyle(YAML::EmitterStyle::Flow);
    return sequence;
}

double scalarNumber(const YAML::Node &node, double fallback)
{
    if (!node.IsDefined() || !node.IsScalar())
    {
        return fallback;
    }

    try
    {
        return node.as<double>();
    }
    catch (const std::exception &)
    {
        return fallback;
    }
}

bool boolOf(const YAML::Node &node, const char *pKey, bool fallback)
{
    const YAML::Node value = childOf(node, pKey);

    if (!value.IsDefined() || !value.IsScalar())
    {
        return fallback;
    }

    return value.Scalar() == "true";
}

// The words of a change that each kind of base thing takes (objects.schema.json `scene.changes`).
const std::map<std::string, std::set<std::string>> &changeWordsByKind()
{
    static const std::map<std::string, std::set<std::string>> words = {
        {"light", {"color", "intensity", "radius", "frequency", "radius_frequency", "phase", "on"}},
        {"sound", {"sound", "sound_radius", "inner_radius", "volume", "loop", "wait", "on", "pan"}},
        {"destructible", {"hp", "damage", "trigger_only", "sound", "destroyed_event", "damaged_event"}},
        {"water", {"tint", "current", "fog"}},
        {"ladder", {"offset", "facing", "width", "reach", "exit", "grab_at_top", "grab_in_air"}},
    };
    return words;
}

// The lock table a base thing's id is kept in, by the scene list it stands in.
const std::map<std::string, int> *lockTableOf(const IdsLock &lock, const std::string &kind)
{
    if (kind == "light")
    {
        return &lock.lights;
    }

    if (kind == "sound")
    {
        return &lock.sounds;
    }

    if (kind == "destructible")
    {
        return &lock.destructibles;
    }

    if (kind == "water")
    {
        return &lock.water;
    }

    if (kind == "spawn")
    {
        return &lock.spawns;
    }

    if (kind == "ladder")
    {
        return &lock.ladders;
    }

    return nullptr;
}

// The faces of each cog in the base map as the scene leaves them (its face overrides may give a face a cog).
std::map<int, std::vector<size_t>> facesByCog(const Game::IndoorMapData &map, const YAML::Node &baseScene)
{
    std::vector<int> cogs(map.faces.size(), 0);

    for (size_t index = 0; index < map.faces.size(); ++index)
    {
        cogs[index] = map.faces[index].cogNumber;
    }

    const YAML::Node overrides = childOf(childOf(baseScene, "initial_state"), "face_attribute_overrides");

    if (overrides.IsDefined() && overrides.IsSequence())
    {
        for (const YAML::Node &entry : overrides)
        {
            const YAML::Node cog = childOf(entry, "cog_number");
            const double face = scalarNumber(childOf(entry, "face_index"), -1.0);

            if (cog.IsDefined() && face >= 0.0 && face < static_cast<double>(cogs.size()))
            {
                cogs[static_cast<size_t>(face)] = static_cast<int>(scalarNumber(cog, 0.0));
            }
        }
    }

    std::map<int, std::vector<size_t>> result;

    for (size_t index = 0; index < cogs.size(); ++index)
    {
        if (cogs[index] != 0)
        {
            result[cogs[index]].push_back(index);
        }
    }

    return result;
}

class OverlayWriter
{
public:
    OverlayWriter(const Project &project, const LoweredIndoorMap &lowered, IdsLock &lock,
        std::vector<ProjectIssue> &issues, std::vector<std::string> &warnings)
        : m_project(project)
        , m_lowered(lowered)
        , m_lock(lock)
        , m_issues(issues)
        , m_warnings(warnings)
        , m_scene(childOf(project.document("objects.yml"), "scene"))
    {
    }

    bool run(const std::string &baseSceneText, const Game::IndoorMapData &baseMap, SceneOverlayText &result)
    {
        const size_t issuesBefore = m_issues.size();

        try
        {
            m_base = YAML::Load(baseSceneText);
        }
        catch (const std::exception &exception)
        {
            issue("project.yml", "base", std::string("the base map's scene does not parse: ") + exception.what(),
                "reference");
            return false;
        }

        m_cogFaces = facesByCog(baseMap, m_base);
        m_baseMap = &baseMap;
        const std::string baseFile = textOf(m_project.document("project.yml"), "base", "");
        YAML::Node overlay(YAML::NodeType::Map);
        overlay["format_version"] = 1;
        overlay["kind"] = "indoor_scene_overlay";
        overlay["source"]["geometry_file"] = baseFile;
        overlay["source"]["notes"] = "Written by oymap build from the Map Studio project \""
            + textOf(m_project.document("project.yml"), "id", "") + "\". Change the project, not this file.";

        collectRemovalsAndChanges();
        spawns(overlay, result);
        list(overlay, "pulsing_lights", "light", "key", result, [this](YAML::Node &target) { addLights(target); });
        list(overlay, "ambient_sounds", "sound", "key", result, [this](YAML::Node &target) { addSounds(target); });
        list(overlay, "destructibles", "destructible", "id", result,
            [this](YAML::Node &target) { addDestructibles(target); });
        list(overlay, "water_volumes", "water", "", result, [this](YAML::Node &target) { addWater(target); });
        list(overlay, "ladders", "ladder", "", result, [this](YAML::Node &target) { addLadders(target); });
        actorsAndItems(overlay, result);
        atmosphereBlocks(overlay);

        for (const std::pair<const std::string, Use> &use : m_uses)
        {
            if (!use.second.used)
            {
                issue("objects.yml", use.second.path, use.first + " is not among the base map's "
                    + listOf(kindOf(use.first)) + " (ids.lock.yml lists what `oymap import` found)", "reference");
            }
        }

        for (YAML::const_iterator entry = overlay.begin(); entry != overlay.end(); ++entry)
        {
            const std::string key = entry->first.Scalar();

            if (key != "format_version" && key != "kind" && key != "source")
            {
                result.keys.push_back(key);
            }
        }

        result.text = writeCanonicalYaml(overlay);
        return m_issues.size() == issuesBefore;
    }

private:
    struct Use
    {
        std::string path;
        bool removed = false;
        bool changed = false;
        YAML::Node change;
        bool used = false;
    };

    static std::string listOf(const std::string &kind)
    {
        return kind == "light" ? "pulsing lights" : kind == "sound" ? "ambient sounds" : kind == "destructible"
            ? "destructibles" : kind == "water" ? "water volumes" : kind == "ladder" ? "ladders" : "spawn points";
    }

    void issue(const std::string &file, const std::string &path, const std::string &message, const std::string &code)
    {
        m_issues.push_back({file, path, message, code});
    }

    // The base things the project removes or changes, by their lock ids.
    void collectRemovalsAndChanges()
    {
        const YAML::Node removals = childOf(m_scene, "removals");
        size_t index = 0;

        if (removals.IsDefined() && removals.IsSequence())
        {
            for (const YAML::Node &removal : removals)
            {
                const std::string path = "scene.removals[" + std::to_string(index++) + "]";
                Use &use = m_uses[removal.Scalar()];
                use.path = path;
                use.removed = true;
            }
        }

        const YAML::Node changes = childOf(m_scene, "changes");
        index = 0;

        if (changes.IsDefined() && changes.IsSequence())
        {
            for (const YAML::Node &change : changes)
            {
                const std::string path = "scene.changes[" + std::to_string(index++) + "]";
                Use &use = m_uses[textOf(change, "of", "")];
                use.path = path;
                use.change = change;
                use.changed = true;
            }
        }
    }

    // Whether the project touches a list of the scene: changes or removes a base thing of its kind, or adds one.
    bool touches(const std::string &kind, const char *pAdditions) const
    {
        const YAML::Node additions = childOf(m_scene, pAdditions);

        if (additions.IsDefined() && additions.IsSequence() && additions.size() > 0)
        {
            return true;
        }

        return std::any_of(m_uses.begin(), m_uses.end(), [&kind](const std::pair<const std::string, Use> &use)
        {
            return kindOf(use.first) == kind;
        });
    }

    const char *additionsKey(const std::string &kind) const
    {
        return kind == "light" ? "lights" : kind == "sound" ? "sounds" : kind == "destructible" ? "destructibles"
            : kind == "ladder" ? "ladders" : "water";
    }

    // The scene list `sceneKey` as the base has it, with the changes and removals of the base things of `kind`
    // (found by the entry's `numberKey`, or by place when it is empty) and the additions.
    template <typename Add>
    void list(YAML::Node &overlay, const char *pSceneKey, const std::string &kind, const std::string &numberKey,
        SceneOverlayText &result, Add add)
    {
        if (!touches(kind, additionsKey(kind)))
        {
            return;
        }

        const YAML::Node baseList = childOf(m_base, pSceneKey);
        const std::map<std::string, int> &table = *lockTableOf(m_lock, kind);
        YAML::Node target(YAML::NodeType::Sequence);
        size_t place = 0;

        for (const YAML::Node &entry : baseList.IsDefined() && baseList.IsSequence() ? baseList : YAML::Node())
        {
            const int number = numberKey.empty() ? static_cast<int>(place)
                : static_cast<int>(scalarNumber(childOf(entry, numberKey.c_str()), -1.0));
            ++place;
            std::string id;

            for (const std::pair<const std::string, int> &locked : table)
            {
                if (locked.second == number && kindOf(locked.first) == kind && m_uses.contains(locked.first))
                {
                    id = locked.first;
                }
            }

            YAML::Node copy = YAML::Clone(entry);

            if (!id.empty())
            {
                Use &use = m_uses.at(id);
                use.used = true;

                if (use.removed)
                {
                    ++result.removed;
                    continue;
                }

                applyChange(kind, use, copy);
                ++result.changed;
            }

            target.push_back(copy);
        }

        const size_t before = target.size();
        add(target);
        result.added += target.size() - before;
        overlay[pSceneKey] = target;
    }

    void applyChange(const std::string &kind, const Use &use, YAML::Node &entry)
    {
        if (!use.changed)
        {
            return;
        }

        const YAML::Node &change = use.change;

        if (kind == "light")
        {
            YAML::Node intensity = entry["intensity"];
            YAML::Node radius = entry["radius"];

            if (const YAML::Node color = childOf(change, "color"); color.IsDefined())
            {
                entry["color"] = YAML::Clone(color);
                entry["color"].SetStyle(YAML::EmitterStyle::Flow);
            }

            if (const YAML::Node range = childOf(change, "intensity"); range.IsDefined() && range.size() == 2)
            {
                intensity[0] = numberNode(scalarNumber(range[0], 1.0));
                intensity[1] = numberNode(scalarNumber(range[1], 1.0));
            }

            if (const YAML::Node range = childOf(change, "radius"); range.IsDefined() && range.size() == 2)
            {
                radius[0] = numberNode(scalarNumber(range[0], 512.0));
                radius[1] = numberNode(scalarNumber(range[1], 512.0));
            }

            if (const YAML::Node frequency = childOf(change, "frequency"); frequency.IsDefined())
            {
                intensity[2] = numberNode(scalarNumber(frequency, 1.0));

                if (!childOf(change, "radius_frequency").IsDefined())
                {
                    radius[2] = numberNode(scalarNumber(frequency, 1.0));
                }
            }

            if (const YAML::Node frequency = childOf(change, "radius_frequency"); frequency.IsDefined())
            {
                radius[2] = numberNode(scalarNumber(frequency, 1.0));
            }

            if (const YAML::Node phase = childOf(change, "phase"); phase.IsDefined())
            {
                intensity[3] = numberNode(scalarNumber(phase, 0.0));
                radius[3] = numberNode(scalarNumber(phase, 0.0));
            }

            if (childOf(change, "on").IsDefined())
            {
                entry["start_on"] = boolOf(change, "on", true);
            }
        }
        else if (kind == "sound")
        {
            if (childOf(change, "sound").IsDefined())
            {
                entry["sound"] = textOf(change, "sound", "");
            }

            if (const YAML::Node value = childOf(change, "sound_radius"); value.IsDefined())
            {
                entry["outer_radius"] = numberNode(scalarNumber(value, 0.0));
            }

            if (const YAML::Node value = childOf(change, "inner_radius"); value.IsDefined())
            {
                entry["inner_radius"] = numberNode(scalarNumber(value, 0.0));
            }

            if (const YAML::Node value = childOf(change, "volume"); value.IsDefined())
            {
                entry["volume"] = numberNode(scalarNumber(value, 1.0));
            }

            if (childOf(change, "loop").IsDefined())
            {
                entry["loop"] = boolOf(change, "loop", true);
            }

            if (childOf(change, "pan").IsDefined())
            {
                entry["pan"] = boolOf(change, "pan", true);
            }

            if (const YAML::Node wait = childOf(change, "wait"); wait.IsDefined() && wait.size() == 2)
            {
                entry["wait"] = numbers({scalarNumber(wait[0], 0.0), scalarNumber(wait[1], 0.0)});
            }

            if (childOf(change, "on").IsDefined())
            {
                entry["start_on"] = boolOf(change, "on", true);
            }
        }
        else if (kind == "destructible")
        {
            if (const YAML::Node value = childOf(change, "hp"); value.IsDefined())
            {
                entry["hp"] = numberNode(scalarNumber(value, 1.0));
            }

            if (childOf(change, "damage").IsDefined())
            {
                entry["damage_enabled"] = boolOf(change, "damage", true);
            }

            if (childOf(change, "trigger_only").IsDefined())
            {
                entry["trigger_destroy_only"] = boolOf(change, "trigger_only", false);
            }

            if (childOf(change, "sound").IsDefined())
            {
                entry["sound"] = textOf(change, "sound", "");
            }

            for (const char *pWord : {"destroyed_event", "damaged_event"})
            {
                if (childOf(change, pWord).IsDefined())
                {
                    entry[pWord] = eventNumber(change, pWord, use.path);
                }
            }
        }
        else if (kind == "water")
        {
            for (const char *pWord : {"tint", "current"})
            {
                if (const YAML::Node value = childOf(change, pWord); value.IsDefined() && value.size() == 3)
                {
                    entry[pWord] = numbers({scalarNumber(value[0], 0.0), scalarNumber(value[1], 0.0),
                        scalarNumber(value[2], 0.0)});
                }
            }

            // The volume's own fog under water (the scene block as given; the game's parser reads it back).
            if (const YAML::Node fog = childOf(change, "fog"); fog.IsDefined() && fog.IsMap())
            {
                entry["fog"] = YAML::Clone(fog);
            }
        }
        else if (kind == "ladder")
        {
            applyLadderChange(use, entry);
        }
    }

    // A base ladder moved as a whole (`offset`), turned (`facing`), its strip or its exit changed.
    void applyLadderChange(const Use &use, YAML::Node &entry)
    {
        const YAML::Node &change = use.change;

        if (const YAML::Node offset = childOf(change, "offset"); offset.IsDefined() && offset.size() == 3)
        {
            for (const char *pPoint : {"bottom", "top", "top_exit"})
            {
                YAML::Node point = entry[pPoint];

                for (size_t axis = 0; axis < 3; ++axis)
                {
                    point[axis] = numberNode(scalarNumber(point[axis], 0.0) + scalarNumber(offset[axis], 0.0));
                }
            }
        }

        if (const YAML::Node facing = childOf(change, "facing"); facing.IsDefined())
        {
            const std::optional<double> degrees = facingWordDegrees(facing);

            if (!degrees)
            {
                issue("objects.yml", use.path + ".facing", "a facing is a compass side (n, ne, e ...) or degrees",
                    "schema");
                return;
            }

            entry["facing_degrees"] = numberNode(*degrees);
        }

        for (const char *pWord : {"width", "reach"})
        {
            if (const YAML::Node value = childOf(change, pWord); value.IsDefined())
            {
                entry[pWord] = numberNode(scalarNumber(value, 0.0));
            }
        }

        if (const YAML::Node exit = childOf(change, "exit"); exit.IsDefined() && exit.size() == 2)
        {
            entry["top_exit"] = numbers({scalarNumber(exit[0], 0.0), scalarNumber(exit[1], 0.0),
                scalarNumber(entry["top"][2], 0.0)});
        }

        for (const char *pWord : {"grab_at_top", "grab_in_air"})
        {
            if (childOf(change, pWord).IsDefined())
            {
                entry[pWord] = boolOf(change, pWord, false);
            }
        }
    }

    // A base map event an id names (evt:e<number> in the lock).
    int eventNumber(const YAML::Node &node, const char *pWord, const std::string &path)
    {
        const std::string id = textOf(node, pWord, "");
        const std::map<std::string, int>::const_iterator found = m_lock.events.find(id);

        if (found == m_lock.events.end())
        {
            issue("objects.yml", path + "." + pWord, id + " is not one of the base map's events (evt:e<number> in "
                "ids.lock.yml)", "reference");
            return 0;
        }

        return found->second;
    }

    static YAML::Node point3(const YAML::Node &node)
    {
        return numbers({scalarNumber(node[0], 0.0), scalarNumber(node[1], 0.0), scalarNumber(node[2], 0.0)});
    }

    template <typename Each>
    void eachAddition(const char *pKey, Each each)
    {
        const YAML::Node additions = childOf(m_scene, pKey);
        size_t index = 0;

        if (!additions.IsDefined() || !additions.IsSequence())
        {
            return;
        }

        for (const YAML::Node &node : additions)
        {
            each(node, "scene." + std::string(pKey) + "[" + std::to_string(index++) + "]");
        }
    }

    void addLights(YAML::Node &target)
    {
        eachAddition("lights", [&](const YAML::Node &node, const std::string &)
        {
            YAML::Node entry(YAML::NodeType::Map);
            const std::string id = textOf(node, "id", "");
            entry["key"] = IdsLock::number(m_lock.lights, id, FirstOverlayLightKey);
            entry["position"] = point3(node["position"]);
            const YAML::Node color = childOf(node, "color");
            entry["color"] = color.IsDefined() && color.size() == 3
                ? numbers({scalarNumber(color[0], 255.0), scalarNumber(color[1], 255.0), scalarNumber(color[2], 255.0)})
                : numbers({255, 255, 255});
            const YAML::Node intensity = childOf(node, "intensity");
            const YAML::Node radius = childOf(node, "radius");
            const double frequency = scalarNumber(childOf(node, "frequency"), 1.0);
            const double radiusFrequency = scalarNumber(childOf(node, "radius_frequency"), frequency);
            const double phase = scalarNumber(childOf(node, "phase"), 0.0);
            const bool hasIntensity = intensity.IsDefined() && intensity.size() == 2;
            const bool hasRadius = radius.IsDefined() && radius.size() == 2;
            entry["intensity"] = numbers({hasIntensity ? scalarNumber(intensity[0], 1.0) : 1.0,
                hasIntensity ? scalarNumber(intensity[1], 1.0) : 1.0, frequency, phase});
            entry["radius"] = numbers({hasRadius ? scalarNumber(radius[0], 512.0) : 512.0,
                hasRadius ? scalarNumber(radius[1], 512.0) : 512.0, radiusFrequency, phase});
            entry["start_on"] = boolOf(node, "on", true);
            target.push_back(entry);
        });
    }

    void addSounds(YAML::Node &target)
    {
        eachAddition("sounds", [&](const YAML::Node &node, const std::string &)
        {
            YAML::Node entry(YAML::NodeType::Map);
            const std::string id = textOf(node, "id", "");
            const double radius = scalarNumber(childOf(node, "radius"), 1024.0);
            entry["key"] = IdsLock::number(m_lock.sounds, id, FirstOverlayKey);
            entry["sound"] = textOf(node, "sound", "");
            entry["position"] = point3(node["position"]);
            entry["inner_radius"] = numberNode(scalarNumber(childOf(node, "inner_radius"), radius / 4.0));
            entry["outer_radius"] = numberNode(radius);
            entry["volume"] = numberNode(scalarNumber(childOf(node, "volume"), 1.0));
            entry["loop"] = boolOf(node, "loop", true);

            if (const YAML::Node wait = childOf(node, "wait"); wait.IsDefined() && wait.size() == 2)
            {
                entry["wait"] = numbers({scalarNumber(wait[0], 0.0), scalarNumber(wait[1], 0.0)});
            }

            for (const char *pWord : {"day_only", "night_only"})
            {
                if (boolOf(node, pWord, false))
                {
                    entry[pWord] = true;
                }
            }

            if (!boolOf(node, "pan", true))
            {
                entry["pan"] = false;
            }

            entry["start_on"] = boolOf(node, "on", true);
            target.push_back(entry);
        });
    }

    void addDestructibles(YAML::Node &target)
    {
        eachAddition("destructibles", [&](const YAML::Node &node, const std::string &path)
        {
            YAML::Node entry(YAML::NodeType::Map);
            const std::string id = textOf(node, "id", "");
            const int cog = static_cast<int>(scalarNumber(childOf(node, "cog"), 0.0));
            const int decorationCog = static_cast<int>(scalarNumber(childOf(node, "decoration_cog"), 0.0));
            const std::string material = textOf(node, "material", "stone");
            std::optional<std::array<double, 3>> centre;

            if (cog == 0 && decorationCog == 0)
            {
                issue("objects.yml", path, "a destructible is made of the base map's faces (`cog`) or decorations "
                    "(`decoration_cog`)", "schema");
                return;
            }

            if (cog != 0)
            {
                const std::map<int, std::vector<size_t>>::const_iterator faces = m_cogFaces.find(cog);

                if (faces == m_cogFaces.end())
                {
                    issue("objects.yml", path + ".cog", "no face of the base map has cog " + std::to_string(cog),
                        "reference");
                    return;
                }

                centre = facesCentre(faces->second);
            }

            if (decorationCog != 0)
            {
                std::array<double, 3> sum = {0.0, 0.0, 0.0};
                int count = 0;

                for (const Game::IndoorEntity &decoration : m_baseMap->entities)
                {
                    if (decoration.eventIdPrimary == decorationCog)
                    {
                        sum[0] += decoration.x;
                        sum[1] += decoration.y;
                        sum[2] += decoration.z;
                        ++count;
                    }
                }

                if (count == 0)
                {
                    issue("objects.yml", path + ".decoration_cog", "no decoration of the base map has the sprite key "
                        + std::to_string(decorationCog), "reference");
                    return;
                }

                if (!centre)
                {
                    centre = std::array<double, 3>{sum[0] / count, sum[1] / count, sum[2] / count + 48.0};
                }
            }

            entry["id"] = IdsLock::number(m_lock.destructibles, id, FirstOverlayKey);
            entry["name"] = nameOf(id);
            entry["hp"] = numberNode(scalarNumber(childOf(node, "hp"), 1.0));
            entry["damage_enabled"] = boolOf(node, "damage", true);
            entry["trigger_destroy_only"] = boolOf(node, "trigger_only", false);
            entry["sound"] = textOf(node, "sound", materialSound(material));
            entry["effect"] = "openyamm:fx/destructible/" + material;
            entry["effect_scale"] = numberNode(scalarNumber(childOf(node, "effect_scale"), 1.0));
            const YAML::Node given = childOf(node, "center");
            entry["center"] = given.IsDefined() ? point3(given)
                : numbers({std::round((*centre)[0]), std::round((*centre)[1]), std::round((*centre)[2])});

            if (cog != 0)
            {
                entry["cog"] = cog;
            }

            if (decorationCog != 0)
            {
                entry["decoration_cog"] = decorationCog;
            }

            for (const char *pWord : {"destroyed_event", "damaged_event"})
            {
                if (childOf(node, pWord).IsDefined())
                {
                    entry[pWord] = eventNumber(node, pWord, path);
                }
            }

            target.push_back(entry);
        });

        // The game refuses two entries of one id.
        std::set<int> ids;

        for (const YAML::Node &entry : target)
        {
            if (!ids.insert(static_cast<int>(scalarNumber(entry["id"], 0.0))).second)
            {
                issue("objects.yml", "scene.destructibles", "destructible id "
                    + std::to_string(static_cast<int>(scalarNumber(entry["id"], 0.0))) + " appears twice", "reference");
            }
        }
    }

    std::array<double, 3> facesCentre(const std::vector<size_t> &faces) const
    {
        std::array<double, 3> low = {1.0e12, 1.0e12, 1.0e12};
        std::array<double, 3> high = {-1.0e12, -1.0e12, -1.0e12};

        for (const size_t faceIndex : faces)
        {
            for (const uint16_t vertexIndex : m_baseMap->faces[faceIndex].vertexIndices)
            {
                if (vertexIndex >= m_baseMap->vertices.size())
                {
                    continue;
                }

                const Game::IndoorVertex &vertex = m_baseMap->vertices[vertexIndex];
                const std::array<double, 3> point = {double(vertex.x), double(vertex.y), double(vertex.z)};

                for (size_t axis = 0; axis < 3; ++axis)
                {
                    low[axis] = std::min(low[axis], point[axis]);
                    high[axis] = std::max(high[axis], point[axis]);
                }
            }
        }

        return {(low[0] + high[0]) / 2.0, (low[1] + high[1]) / 2.0, (low[2] + high[2]) / 2.0};
    }

    void addWater(YAML::Node &target)
    {
        eachAddition("water", [&](const YAML::Node &node, const std::string &path)
        {
            YAML::Node entry(YAML::NodeType::Map);
            entry["id"] = idSafe(nameOf(textOf(node, "id", "")));
            entry["liquid"] = textOf(node, "liquid", "water");
            YAML::Node pieces(YAML::NodeType::Sequence);
            size_t index = 0;

            for (const YAML::Node &piece : childOf(node, "pieces"))
            {
                const double bottom = scalarNumber(childOf(piece, "bottom"), 0.0);
                const double top = scalarNumber(childOf(piece, "top"), 0.0);

                if (!(top > bottom))
                {
                    issue("objects.yml", path + ".pieces[" + std::to_string(index) + "]", "a piece's top must lie "
                        "above its bottom", "geometry");
                }

                YAML::Node out(YAML::NodeType::Map);
                YAML::Node polygon(YAML::NodeType::Sequence);

                for (const YAML::Node &point : childOf(piece, "polygon"))
                {
                    polygon.push_back(numbers({scalarNumber(point[0], 0.0), scalarNumber(point[1], 0.0)}));
                }

                out["polygon"] = polygon;
                out["bottom"] = numberNode(bottom);
                out["top"] = numberNode(top);
                pieces.push_back(out);
                ++index;
            }

            entry["pieces"] = pieces;

            for (const char *pWord : {"tint", "current"})
            {
                if (const YAML::Node value = childOf(node, pWord); value.IsDefined() && value.size() == 3)
                {
                    entry[pWord] = numbers({scalarNumber(value[0], 0.0), scalarNumber(value[1], 0.0),
                        scalarNumber(value[2], 0.0)});
                }
            }

            if (const YAML::Node fog = childOf(node, "fog"); fog.IsDefined() && fog.IsMap())
            {
                entry["fog"] = YAML::Clone(fog);
            }

            target.push_back(entry);
        });
    }

    // Spawn points: additions as the overlay's authored content (appended after the base's), removals by place.
    void spawns(YAML::Node &overlay, SceneOverlayText &result)
    {
        eachAddition("spawns", [&](const YAML::Node &node, const std::string &)
        {
            YAML::Node entry(YAML::NodeType::Map);
            const bool item = textOf(node, "kind", "monster") == "item";
            const std::string tier = textOf(node, "tier", "");
            int index = static_cast<int>(scalarNumber(childOf(node, "slot"), 1.0));

            if (item)
            {
                index = static_cast<int>(scalarNumber(childOf(node, "treasure_level"), 1.0));
            }
            else if (!tier.empty())
            {
                index = 4 + 3 * (tier[0] - 'a') + (index - 1);
            }

            entry["radius"] = numberNode(item ? 32.0 : scalarNumber(childOf(node, "radius"), 128.0));
            entry["type_id"] = item ? 2 : 3;
            entry["index"] = index;
            entry["attributes"] = 0;
            entry["group"] = numberNode(scalarNumber(childOf(node, "group"), 0.0));
            const YAML::Node position = node["position"];
            YAML::Node place(YAML::NodeType::Map);
            place["x"] = static_cast<long long>(std::lround(scalarNumber(position[0], 0.0)));
            place["y"] = static_cast<long long>(std::lround(scalarNumber(position[1], 0.0)));
            place["z"] = static_cast<long long>(std::lround(scalarNumber(position[2], 0.0)));
            place.SetStyle(YAML::EmitterStyle::Flow);
            entry["position"] = place;
            overlay["authored_content"]["spawns"].push_back(entry);
            ++result.added;
        });

        const YAML::Node baseSpawns = childOf(m_base, "spawns");

        for (std::pair<const std::string, Use> &use : m_uses)
        {
            if (kindOf(use.first) != "spawn")
            {
                continue;
            }

            if (use.second.changed)
            {
                issue("objects.yml", use.second.path, "a spawn point is not changed by an overlay: remove it and add "
                    "another", "schema");
            }

            const std::map<std::string, int>::const_iterator number = m_lock.spawns.find(use.first);

            if (number == m_lock.spawns.end() || !use.second.removed || !baseSpawns.IsDefined())
            {
                continue;
            }

            for (const YAML::Node &spawn : baseSpawns)
            {
                if (static_cast<int>(scalarNumber(childOf(spawn, "spawn_index"), -1.0)) != number->second)
                {
                    continue;
                }

                const YAML::Node position = childOf(spawn, "position");
                YAML::Node removal(YAML::NodeType::Map);
                removal["position"] = position.IsMap()
                    ? numbers({scalarNumber(position["x"], 0.0), scalarNumber(position["y"], 0.0),
                        scalarNumber(position["z"], 0.0)})
                    : point3(position);
                removal["index"] = numberNode(scalarNumber(childOf(spawn, "index"), 0.0));
                overlay["removals"]["spawns"].push_back(removal);
                use.second.used = true;
                ++result.removed;
            }
        }
    }

    // The overlay's own ladders (objects.yml scene.ladders, lowered by lowerOverlayProject).
    void addLadders(YAML::Node &target)
    {
        for (const LoweredLadder &ladder : m_lowered.ladders)
        {
            target.push_back(sceneLadderNode(ladder));
        }

        // The game climbs a ladder by its id: two of one id would be one.
        std::set<std::string> ids;

        for (const YAML::Node &entry : target)
        {
            if (!ids.insert(textOf(entry, "id", "")).second)
            {
                issue("objects.yml", "scene.ladders", "ladder id " + textOf(entry, "id", "") + " appears twice in the "
                    "scene's ladders (the base map's and the overlay's)", "reference");
            }
        }
    }

    // The base map's sector at a place an overlay adds a monster or an item (its feet, a little above the floor).
    std::optional<int> sectorAt(const std::array<double, 3> &point, const std::string &path)
    {
        const std::optional<int16_t> sector = Game::findIndoorSectorForPoint(*m_baseMap, m_baseMap->vertices,
            {float(point[0]), float(point[1]), float(point[2]) + 16.0f});

        if (!sector)
        {
            issue("objects.yml", path + ".position", "[" + formatNumber(point[0]) + ", " + formatNumber(point[1])
                + ", " + formatNumber(point[2]) + "] is in no sector of the base map", "geometry");
            return std::nullopt;
        }

        return *sector;
    }

    // Monsters and floor items the overlay adds: the game appends them after the base scene's (and earlier
    // overlays'), whose numbers stay.
    void actorsAndItems(YAML::Node &overlay, SceneOverlayText &result)
    {
        size_t index = 0;

        for (const LoweredMonster &lowered : m_lowered.monsters)
        {
            LoweredMonster monster = lowered;
            const std::optional<int> sector = sectorAt(monster.position, "scene.monsters[" + std::to_string(index++)
                + "]");

            if (sector)
            {
                monster.sector = *sector;
                overlay["authored_content"]["actors"].push_back(sceneActorNode(monster, -1));
                ++result.added;
            }
        }

        index = 0;

        for (const LoweredItem &lowered : m_lowered.items)
        {
            LoweredItem item = lowered;
            const std::optional<int> sector = sectorAt(item.position, "scene.items[" + std::to_string(index++) + "]");

            if (sector)
            {
                item.sector = *sector;
                overlay["authored_content"]["sprite_objects"].push_back(sceneSpriteObjectNode(item, -1));
                ++result.added;
            }
        }
    }

    // atmosphere.yml's scene blocks, each replacing the base scene's.
    void atmosphereBlocks(YAML::Node &overlay)
    {
        const YAML::Node atmosphere = m_project.document("atmosphere.yml");

        for (const std::pair<const char *, const char *> &block : {std::pair<const char *, const char *>{"open_sky",
                 "sky"}, {"scene_fog", "fog"}, {"daylight", "daylight"}, {"terrain", "terrain"}, {"mist", "mist"}})
        {
            if (const YAML::Node node = childOf(atmosphere, block.first); node.IsDefined())
            {
                overlay[block.second] = YAML::Clone(node);
            }
        }
    }

    const Project &m_project;
    const LoweredIndoorMap &m_lowered;
    IdsLock &m_lock;
    std::vector<ProjectIssue> &m_issues;
    std::vector<std::string> &m_warnings;
    YAML::Node m_scene;
    YAML::Node m_base;
    const Game::IndoorMapData *m_baseMap = nullptr;
    std::map<int, std::vector<size_t>> m_cogFaces;
    std::map<std::string, Use> m_uses;
};
}

void lockBaseSceneThings(const Game::IndoorSceneData &scene, YAML::Node &lock)
{
    YAML::Node lights(YAML::NodeType::Map);

    for (const Game::IndoorPulsingLight &light : scene.pulsingLights)
    {
        lights["light:k" + std::to_string(light.lightKey)] = static_cast<int>(light.lightKey);
    }

    YAML::Node sounds(YAML::NodeType::Map);

    for (const Game::WorldAmbientSound &sound : scene.ambientSounds)
    {
        sounds["sound:a" + std::to_string(sound.key)] = static_cast<int>(sound.key);
    }

    YAML::Node destructibles(YAML::NodeType::Map);

    for (const Game::IndoorDestructible &destructible : scene.destructibles)
    {
        destructibles["destructible:k" + std::to_string(destructible.id)] = static_cast<int>(destructible.id);
    }

    YAML::Node water(YAML::NodeType::Map);
    std::set<std::string> waterIds;

    for (size_t index = 0; index < scene.waterVolumes.size(); ++index)
    {
        std::string id = "water:" + idSafe(scene.waterVolumes[index].id);

        // Two volumes of one name (MM9 has none) keep apart by their place.
        if (!waterIds.insert(id).second)
        {
            id += "_" + std::to_string(index);
            waterIds.insert(id);
        }

        water[id] = static_cast<int>(index);
    }

    YAML::Node spawns(YAML::NodeType::Map);

    for (const Game::IndoorSceneSpawn &spawn : scene.spawns)
    {
        spawns["spawn:s" + std::to_string(spawn.spawnIndex)] = static_cast<int>(spawn.spawnIndex);
    }

    // Ladders by their place in the list, named by their id (S8a).
    YAML::Node ladders(YAML::NodeType::Map);
    std::set<std::string> ladderIds;

    for (size_t index = 0; index < scene.ladders.size(); ++index)
    {
        std::string id = "ladder:" + idSafe(scene.ladders[index].id);

        if (!ladderIds.insert(id).second)
        {
            id += "_" + std::to_string(index);
            ladderIds.insert(id);
        }

        ladders[id] = static_cast<int>(index);
    }

    for (const std::pair<const char *, YAML::Node> &table : {std::pair<const char *, YAML::Node>{"lights", lights},
             {"sounds", sounds}, {"destructibles", destructibles}, {"water", water}, {"spawns", spawns},
             {"ladders", ladders}})
    {
        if (table.second.size() > 0)
        {
            lock[table.first] = table.second;
        }
    }
}

void lockBaseCinematics(const std::string &cinematicsText, YAML::Node &lock)
{
    std::string error;
    const std::optional<Game::CinematicLibrary> library = Game::parseCinematicLibrary(cinematicsText, error);
    YAML::Node cinematics(YAML::NodeType::Map);

    for (size_t index = 0; library && index < library->cinematics.size(); ++index)
    {
        const std::string &name = library->cinematics[index].id;

        // Only a name an id can carry (a wiring cinematic of the same name replaces it).
        if (!name.empty() && idSafe(name) == name && name[0] >= 'a' && name[0] <= 'z')
        {
            cinematics["cinematic:" + name] = static_cast<int>(index);
        }
    }

    if (cinematics.size() > 0)
    {
        lock["cinematics"] = cinematics;
    }
}

std::vector<std::string> baseCinematicNames(const AssetSession &session, const std::string &stem)
{
    std::vector<std::string> names;
    const std::optional<std::string> text = session.files().readTextFile("Data/games/" + stem + ".cinematics.yml");
    std::string error;
    const std::optional<Game::CinematicLibrary> library =
        text ? Game::parseCinematicLibrary(*text, error) : std::nullopt;

    for (const Game::CinematicDefinition &cinematic : library ? library->cinematics
             : std::vector<Game::CinematicDefinition>())
    {
        names.push_back(cinematic.id);
    }

    return names;
}

void readOverlayBase(
    const Project &project,
    const AssetSession &session,
    const LoadedMap &map,
    const std::string &baseSceneText,
    LoweringOptions &options)
{
    const YAML::Node card = project.document("project.yml");
    const std::string ownName = toLower(std::filesystem::path(textOf(card, "base", "")).stem().string() + "_"
        + textOf(card, "id", "") + ".scene.yml");
    options.overlayFirstActor = 0;
    options.overlayBaseGroups.clear();
    const auto count = [&options](const YAML::Node &actors, const YAML::Node &spawns)
    {
        for (const YAML::Node &actor : actors.IsDefined() && actors.IsSequence() ? actors : YAML::Node())
        {
            ++options.overlayFirstActor;
            options.overlayBaseGroups.insert(static_cast<int>(scalarNumber(childOf(actor, "group"), 0.0)));
        }

        for (const YAML::Node &spawn : spawns.IsDefined() && spawns.IsSequence() ? spawns : YAML::Node())
        {
            options.overlayBaseGroups.insert(static_cast<int>(scalarNumber(childOf(spawn, "group"), 0.0)));
        }
    };

    try
    {
        const YAML::Node base = YAML::Load(baseSceneText);
        count(childOf(childOf(base, "initial_state"), "actors"), childOf(base, "spawns"));

        // The world's overlays the game applies before this one (name order): their actors stand before its own.
        for (const std::string &path : map.sceneOverlayPaths)
        {
            const std::string name = toLower(std::filesystem::path(path).filename().string());

            if (name >= ownName)
            {
                continue;
            }

            const std::optional<std::string> text = session.files().readTextFile(path);
            const YAML::Node overlay = text ? YAML::Load(*text) : YAML::Node();
            const YAML::Node authored = childOf(overlay, "authored_content");
            count(childOf(authored, "actors"), childOf(authored, "spawns"));
        }
    }
    catch (const std::exception &)
    {
        // A scene that does not parse is reported by the build that reads it.
    }

    options.overlayBaseGroups.erase(0);
}

void addWorldTableRows(const std::filesystem::path &assetRoot, const std::string &world, LoweringOptions &options)
{
    std::string manifest;
    bool added = false;

    if (assetRoot.empty() || world.empty() || !readTextFile(assetRoot / "worlds" / world / "world.yml", manifest))
    {
        return;
    }

    try
    {
        const YAML::Node contributions = childOf(YAML::Load(manifest), "tableContributions");

        for (const YAML::Node &contribution : contributions.IsDefined() && contributions.IsSequence() ? contributions
                 : YAML::Node())
        {
            const std::string table = textOf(contribution, "table", "");
            std::string *pText = table == "monster_data" ? &options.monsterTableText
                : table == "decorations" ? &options.decorationTableText
                : table == "monster_descriptors" ? &options.monsterDescriptorTableText
                : table == "items" ? &options.itemTableText
                : table == "map_stats" ? &options.mapStatsTableText
                : table == "place_mon" ? &options.uniqueNameTableText : nullptr;
            std::string rows;

            if (pText != nullptr && textOf(contribution, "mode", "") == "append"
                && readTextFile(assetRoot / "worlds" / world / textOf(contribution, "path", ""), rows))
            {
                pText->append("\n" + rows);
                added = true;
            }
        }
    }
    catch (const std::exception &)
    {
        // A manifest that does not parse adds nothing (the game refuses the world).
    }

    // The world's monster factions and their relations (worlds/<world>/relations.yml), which the game consults before
    // hostile.txt.
    added = readTextFile(assetRoot / "worlds" / world / "relations.yml", options.worldRelationsText) || added;

    if (added)
    {
        options.tables = parseLoweringTables(options);
    }
}

std::string indoorSceneProfile(const Game::IndoorSceneData &scene)
{
    if (scene.openSky.enabled && scene.terrain)
    {
        return "region";
    }

    return scene.openSky.enabled ? "city" : "dungeon";
}

bool projectChangesScene(const Project &project)
{
    const YAML::Node scene = childOf(project.document("objects.yml"), "scene");

    if (scene.IsDefined() && scene.IsMap())
    {
        for (YAML::const_iterator entry = scene.begin(); entry != scene.end(); ++entry)
        {
            if (entry->second.IsSequence() && entry->second.size() > 0)
            {
                return true;
            }
        }
    }

    const YAML::Node atmosphere = project.document("atmosphere.yml");

    for (const char *pBlock : {"open_sky", "scene_fog", "daylight", "terrain", "mist"})
    {
        if (childOf(atmosphere, pBlock).IsDefined())
        {
            return true;
        }
    }

    return false;
}

void checkSceneOverlayWords(const Project &project, std::vector<ProjectIssue> &issues)
{
    const YAML::Node card = project.document("project.yml");
    const YAML::Node scene = childOf(project.document("objects.yml"), "scene");
    const bool overlay = childOf(card, "base").IsDefined();

    if (!overlay)
    {
        if (scene.IsDefined())
        {
            issues.push_back({"objects.yml", "scene", "`scene` is for overlay projects (project.yml `base`): a new map "
                "places its lights, sounds and spawns in rooms (`lights`, `sounds`, `spawns`)", "schema"});
        }

        return;
    }

    if (textOf(card, "kind", "") == "outdoor" && projectChangesScene(project))
    {
        issues.push_back({"objects.yml", "scene", "scene overlays of outdoor maps are not built yet: only indoor "
            "(BLV) maps", "unsupported"});
        return;
    }

    if (!scene.IsDefined() || !scene.IsMap())
    {
        return;
    }

    const IdsLock lock = IdsLock::fromDocument(project.document("ids.lock.yml"));
    std::set<std::string> removed;
    const YAML::Node removals = childOf(scene, "removals");
    size_t index = 0;

    if (removals.IsDefined() && removals.IsSequence())
    {
        for (const YAML::Node &removal : removals)
        {
            const std::string id = removal.Scalar();
            const std::string path = "scene.removals[" + std::to_string(index++) + "]";
            const std::map<std::string, int> *pTable = lockTableOf(lock, kindOf(id));

            if (pTable == nullptr || !pTable->contains(id))
            {
                issues.push_back({"objects.yml", path, id + " is no base thing an overlay removes: a spawn point, "
                    "pulsing light, ambient sound, destructible, water volume or ladder of ids.lock.yml", "reference"});
            }
            else if (!removed.insert(id).second)
            {
                issues.push_back({"objects.yml", path, id + " is removed twice", "reference"});
            }
        }
    }

    const YAML::Node changes = childOf(scene, "changes");
    index = 0;
    std::set<std::string> changed;

    if (changes.IsDefined() && changes.IsSequence())
    {
        for (const YAML::Node &change : changes)
        {
            const std::string id = textOf(change, "of", "");
            const std::string kind = kindOf(id);
            const std::string path = "scene.changes[" + std::to_string(index++) + "]";
            const std::map<std::string, std::set<std::string>>::const_iterator words = changeWordsByKind().find(kind);
            const std::map<std::string, int> *pTable = lockTableOf(lock, kind);

            if (words == changeWordsByKind().end() || pTable == nullptr || !pTable->contains(id))
            {
                issues.push_back({"objects.yml", path + ".of", id + " is no base thing an overlay changes: a pulsing "
                    "light, ambient sound, destructible, water volume or ladder of ids.lock.yml", "reference"});
                continue;
            }

            if (removed.contains(id))
            {
                issues.push_back({"objects.yml", path, id + " is both changed and removed", "reference"});
            }

            if (!changed.insert(id).second)
            {
                issues.push_back({"objects.yml", path, id + " is changed twice: say it in one change", "reference"});
            }

            for (YAML::const_iterator word = change.begin(); word != change.end(); ++word)
            {
                const std::string name = word->first.Scalar();

                if (name != "of" && name != "notes" && !words->second.contains(name))
                {
                    issues.push_back({"objects.yml", path + "." + name, "`" + name + "` does not change a " + kind,
                        "schema"});
                }
            }
        }
    }

    // New things' ids must not be the base map's.
    for (const char *pList : {"lights", "sounds", "spawns", "destructibles", "water", "ladders"})
    {
        const YAML::Node additions = childOf(scene, pList);
        index = 0;

        if (!additions.IsDefined() || !additions.IsSequence())
        {
            continue;
        }

        for (const YAML::Node &addition : additions)
        {
            const std::string id = textOf(addition, "id", "");
            const std::map<std::string, int> *pTable = lockTableOf(lock, kindOf(id));
            const std::string path = "scene." + std::string(pList) + "[" + std::to_string(index++) + "]";
            const bool baseLadder = kindOf(id) == "ladder" && lock.ladders.contains(id);
            const bool baseId = baseLadder || (id.size() > 2 && (id.find(":k") != std::string::npos
                || id.find(":a") != std::string::npos || id.find(":s") != std::string::npos) && pTable != nullptr
                && pTable->contains(id) && pTable->at(id) < (kindOf(id) == "light" ? FirstOverlayLightKey
                    : FirstOverlayKey));

            if (baseId)
            {
                issues.push_back({"objects.yml", path + ".id", id + " is a base thing's id: change it under "
                    "`changes`, or give the new one another id", "reference"});
            }
        }
    }
}

bool buildSceneOverlayText(
    const Project &project,
    const std::string &baseSceneText,
    const Game::IndoorMapData &baseMap,
    const LoweredIndoorMap &lowered,
    IdsLock &lock,
    SceneOverlayText &result,
    std::vector<ProjectIssue> &issues,
    std::vector<std::string> &warnings)
{
    OverlayWriter writer(project, lowered, lock, issues, warnings);
    return writer.run(baseSceneText, baseMap, result);
}

namespace
{
struct DescribedThing
{
    std::string id;
    std::string kind;
    std::string origin;
    std::string state;
    std::array<int64_t, 3> at = {0, 0, 0};
    int64_t radius = 0;
    std::string label;
    std::vector<std::vector<std::array<int64_t, 2>>> polygons;
};

int64_t whole(double value)
{
    return static_cast<int64_t>(std::llround(value));
}

std::map<int, std::string> reverseTable(const std::map<std::string, int> &table)
{
    std::map<int, std::string> result;

    for (const std::pair<const std::string, int> &entry : table)
    {
        result[entry.second] = entry.first;
    }

    return result;
}
}

bool describeSceneOverlay(
    const Project &project,
    const std::filesystem::path &assetRoot,
    JsonWriter &writer,
    std::string &errorKind,
    std::string &errorMessage)
{
    const YAML::Node card = project.document("project.yml");
    const std::string baseFile = textOf(card, "base", "");
    const std::string world = textOf(card, "world", "");

    if (baseFile.empty() || textOf(card, "kind", "") != "indoor")
    {
        errorKind = "bad_request";
        errorMessage = "view.overlay is for overlay projects of indoor maps (project.yml `base` naming a BLV)";
        return false;
    }

    AssetSession session;
    LoadedMap map;

    if (!session.open(assetRoot, world, errorMessage) || !loadMap(session, baseFile, map, errorMessage)
        || !map.indoor)
    {
        errorKind = "no_such_map";
        return false;
    }

    const std::string stem = std::filesystem::path(baseFile).stem().string();
    const std::optional<std::string> baseText = session.files().readTextFile("Data/games/" + stem + ".scene.yml");
    const Game::IndoorSceneYmlLoader loader;
    std::string sceneError;
    std::optional<Game::IndoorSceneData> base =
        baseText ? loader.loadFromText(*baseText, sceneError) : std::nullopt;

    if (!base)
    {
        errorKind = "no_such_map";
        errorMessage = baseFile + " has no scene that reads: " + sceneError;
        return false;
    }

    IdsLock lock = IdsLock::fromDocument(project.document("ids.lock.yml"));
    std::vector<ProjectIssue> issues;
    std::vector<std::string> warnings;
    SceneOverlayText overlay;
    YAML::Node built;
    checkSceneOverlayWords(project, issues);
    // The overlay's own monsters, items and ladders, as the build lowers them (with the asset root's tables).
    LoweringOptions options = readLoweringOptions(assetRoot);
    addWorldTableRows(assetRoot, world, options);
    readOverlayBase(project, session, map, *baseText, options);
    LoweredIndoorMap lowered;
    lowerOverlayProject(project, options, lowered, issues);

    if (issues.empty() && projectChangesScene(project)
        && buildSceneOverlayText(project, *baseText, *map.indoor, lowered, lock, overlay, issues, warnings))
    {
        built = YAML::Load(overlay.text);
    }

    const YAML::Node scene = childOf(project.document("objects.yml"), "scene");
    std::set<std::string> removed;
    std::set<std::string> changed;

    for (const YAML::Node &removal : childOf(scene, "removals").IsDefined() ? childOf(scene, "removals")
             : YAML::Node(YAML::NodeType::Sequence))
    {
        removed.insert(removal.Scalar());
    }

    for (const YAML::Node &change : childOf(scene, "changes").IsDefined() ? childOf(scene, "changes")
             : YAML::Node(YAML::NodeType::Sequence))
    {
        changed.insert(textOf(change, "of", ""));
    }

    std::vector<DescribedThing> things;
    const auto baseThing = [&](const std::string &id, const std::string &kind, double x, double y, double z,
                               double radius, const std::string &label)
    {
        DescribedThing thing;
        thing.id = id;
        thing.kind = kind;
        thing.origin = "base";
        thing.state = removed.contains(id) ? "removed" : changed.contains(id) ? "changed" : "kept";
        thing.at = {whole(x), whole(y), whole(z)};
        thing.radius = whole(radius);
        thing.label = label;
        things.push_back(thing);
        return &things.back();
    };

    const std::map<int, std::string> lights = reverseTable(lock.lights);
    const std::map<int, std::string> sounds = reverseTable(lock.sounds);
    const std::map<int, std::string> destructibles = reverseTable(lock.destructibles);
    const std::map<int, std::string> water = reverseTable(lock.water);
    const std::map<int, std::string> spawns = reverseTable(lock.spawns);
    const auto idOf = [](const std::map<int, std::string> &table, int number, const std::string &fallback)
    {
        const std::map<int, std::string>::const_iterator found = table.find(number);
        return found == table.end() ? fallback : found->second;
    };

    for (const Game::IndoorPulsingLight &light : base->pulsingLights)
    {
        baseThing(idOf(lights, int(light.lightKey), "light:k" + std::to_string(light.lightKey)), "light",
            light.position[0], light.position[1], light.position[2], light.radius[1],
            "pulsing light " + std::to_string(light.lightKey));
    }

    for (const Game::WorldAmbientSound &sound : base->ambientSounds)
    {
        baseThing(idOf(sounds, int(sound.key), "sound:a" + std::to_string(sound.key)), "sound", sound.position[0],
            sound.position[1], sound.position[2], sound.outerRadius, sound.sound);
    }

    for (const Game::IndoorDestructible &destructible : base->destructibles)
    {
        baseThing(idOf(destructibles, int(destructible.id), "destructible:k" + std::to_string(destructible.id)),
            "destructible", destructible.center[0], destructible.center[1], destructible.center[2], 0.0,
            destructible.name.empty() ? "destructible " + std::to_string(destructible.id) : destructible.name);
    }

    for (size_t index = 0; index < base->waterVolumes.size(); ++index)
    {
        const Game::IndoorWaterVolume &volume = base->waterVolumes[index];
        double x = 0.0;
        double y = 0.0;
        double top = 0.0;
        size_t points = 0;

        for (const Game::IndoorWaterPiece &piece : volume.pieces)
        {
            for (const std::array<float, 2> &point : piece.polygon)
            {
                x += point[0];
                y += point[1];
                ++points;
            }

            top = std::max(top, double(piece.top));
        }

        DescribedThing *pThing = baseThing(idOf(water, int(index), "water:" + volume.id), "water",
            points > 0 ? x / double(points) : 0.0, points > 0 ? y / double(points) : 0.0, top, 0.0, volume.id);

        for (const Game::IndoorWaterPiece &piece : volume.pieces)
        {
            std::vector<std::array<int64_t, 2>> polygon;

            for (const std::array<float, 2> &point : piece.polygon)
            {
                polygon.push_back({whole(point[0]), whole(point[1])});
            }

            pThing->polygons.push_back(polygon);
        }
    }

    for (const Game::IndoorSceneSpawn &spawn : base->spawns)
    {
        baseThing(idOf(spawns, int(spawn.spawnIndex), "spawn:s" + std::to_string(spawn.spawnIndex)), "spawn",
            spawn.spawn.x, spawn.spawn.y, spawn.spawn.z, spawn.spawn.radius,
            std::string(spawn.spawn.typeId == 2 ? "item roll " : "monsters ") + std::to_string(spawn.spawn.index));
    }

    const std::map<int, std::string> ladders = reverseTable(lock.ladders);

    for (size_t index = 0; index < base->ladders.size(); ++index)
    {
        const Game::IndoorLadder &ladder = base->ladders[index];
        baseThing(idOf(ladders, int(index), "ladder:" + idSafe(ladder.id)), "ladder", ladder.bottom[0],
            ladder.bottom[1], ladder.bottom[2], 0.0, "ladder " + ladder.id + ", "
                + formatNumber(std::round(ladder.top[2] - ladder.bottom[2])) + " high");
    }

    // The project's additions, where the built overlay put them (a destructible's centre from its faces).
    const auto added = [&](const std::string &id, const std::string &kind, const YAML::Node &place, double radius,
                           const std::string &label)
    {
        DescribedThing thing;
        thing.id = id;
        thing.kind = kind;
        thing.origin = "added";
        thing.state = "added";
        thing.at = {whole(scalarNumber(place[0], 0.0)), whole(scalarNumber(place[1], 0.0)),
            whole(scalarNumber(place[2], 0.0))};
        thing.radius = whole(radius);
        thing.label = label;
        things.push_back(thing);
        return &things.back();
    };

    if (built.IsDefined() && built.IsMap())
    {
        for (const YAML::Node &light : childOf(built, "pulsing_lights"))
        {
            const int key = int(scalarNumber(light["key"], 0.0));

            if (key >= FirstOverlayLightKey)
            {
                added(idOf(lights, key, ""), "light", light["position"], scalarNumber(light["radius"][1], 0.0),
                    "pulsing light " + std::to_string(key));
            }
        }

        for (const YAML::Node &sound : childOf(built, "ambient_sounds"))
        {
            const int key = int(scalarNumber(sound["key"], 0.0));

            if (key >= FirstOverlayKey)
            {
                added(idOf(sounds, key, ""), "sound", sound["position"], scalarNumber(sound["outer_radius"], 0.0),
                    textOf(sound, "sound", ""));
            }
        }

        for (const YAML::Node &destructible : childOf(built, "destructibles"))
        {
            const int id = int(scalarNumber(destructible["id"], 0.0));

            if (id >= FirstOverlayKey)
            {
                added(idOf(destructibles, id, ""), "destructible", destructible["center"], 0.0,
                    textOf(destructible, "name", ""));
            }
        }

        const YAML::Node newWater = childOf(scene, "water");
        size_t index = 0;

        if (newWater.IsDefined() && newWater.IsSequence())
        {
            for (const YAML::Node &volume : newWater)
            {
                double x = 0.0;
                double y = 0.0;
                double top = 0.0;
                size_t points = 0;
                std::vector<std::vector<std::array<int64_t, 2>>> polygons;

                for (const YAML::Node &piece : childOf(volume, "pieces"))
                {
                    std::vector<std::array<int64_t, 2>> polygon;

                    for (const YAML::Node &point : childOf(piece, "polygon"))
                    {
                        x += scalarNumber(point[0], 0.0);
                        y += scalarNumber(point[1], 0.0);
                        ++points;
                        polygon.push_back({whole(scalarNumber(point[0], 0.0)), whole(scalarNumber(point[1], 0.0))});
                    }

                    top = std::max(top, scalarNumber(childOf(piece, "top"), 0.0));
                    polygons.push_back(polygon);
                }

                YAML::Node place = numbers({points > 0 ? x / double(points) : 0.0,
                    points > 0 ? y / double(points) : 0.0, top});
                added(textOf(volume, "id", ""), "water", place, 0.0, nameOf(textOf(volume, "id", "")))->polygons =
                    polygons;
            }
        }

        // Ladders, monsters and items the overlay adds, where the lowering put them.
        for (const LoweredLadder &ladder : lowered.ladders)
        {
            added("ladder:" + ladder.name, "ladder", numbers({ladder.bottom[0], ladder.bottom[1], ladder.bottom[2]}),
                0.0, "ladder " + ladder.name + ", " + formatNumber(std::round(ladder.top[2] - ladder.bottom[2]))
                    + " high");
        }

        for (size_t actor = 0; actor < lowered.monsters.size(); ++actor)
        {
            const LoweredMonster &monster = lowered.monsters[actor];
            added(monster.id, "monster", numbers({monster.position[0], monster.position[1], monster.position[2]}),
                double(monster.radius), "monster " + std::to_string(monster.monsterId) + ", actor "
                    + std::to_string(lowered.firstActor + actor));
        }

        for (const LoweredItem &item : lowered.items)
        {
            added(item.id, "item", numbers({item.position[0], item.position[1], item.position[2]}), 0.0,
                "item " + std::to_string(item.itemId));
        }

        const YAML::Node newSpawns = childOf(scene, "spawns");
        index = 0;

        for (const YAML::Node &spawn : childOf(childOf(built, "authored_content"), "spawns"))
        {
            const std::string id = newSpawns.IsDefined() && index < newSpawns.size()
                ? textOf(newSpawns[index], "id", "") : std::string();
            ++index;
            const YAML::Node position = spawn["position"];
            added(id, "spawn", numbers({scalarNumber(position["x"], 0.0), scalarNumber(position["y"], 0.0),
                scalarNumber(position["z"], 0.0)}), scalarNumber(spawn["radius"], 0.0),
                std::string(int(scalarNumber(spawn["type_id"], 3.0)) == 2 ? "item roll " : "monsters ")
                    + std::to_string(int(scalarNumber(spawn["index"], 0.0))));
        }
    }

    std::array<int64_t, 4> bounds = {0, 0, 0, 0};

    if (!map.indoor->vertices.empty())
    {
        bounds = {INT64_MAX, INT64_MAX, INT64_MIN, INT64_MIN};

        for (const Game::IndoorVertex &vertex : map.indoor->vertices)
        {
            bounds[0] = std::min<int64_t>(bounds[0], vertex.x);
            bounds[1] = std::min<int64_t>(bounds[1], vertex.y);
            bounds[2] = std::max<int64_t>(bounds[2], vertex.x);
            bounds[3] = std::max<int64_t>(bounds[3], vertex.y);
        }
    }

    writer.field("base", baseFile);
    writer.field("world", world);
    writer.field("profile", indoorSceneProfile(*base));
    writer.key("bounds");
    writer.beginArray();

    for (const int64_t value : bounds)
    {
        writer.value(value);
    }

    writer.endArray();
    writer.key("scene_keys");
    writer.beginArray();

    for (const std::string &key : overlay.keys)
    {
        writer.value(key);
    }

    writer.endArray();
    writer.key("things");
    writer.beginArray();

    for (const DescribedThing &thing : things)
    {
        writer.beginObject();
        writer.field("id", thing.id);
        writer.field("kind", thing.kind);
        writer.field("origin", thing.origin);
        writer.field("state", thing.state);
        writer.key("at");
        writer.beginArray();
        writer.value(thing.at[0]);
        writer.value(thing.at[1]);
        writer.value(thing.at[2]);
        writer.endArray();

        if (thing.radius > 0)
        {
            writer.field("radius", thing.radius);
        }

        writer.field("label", thing.label);

        if (!thing.polygons.empty())
        {
            writer.key("polygons");
            writer.beginArray();

            for (const std::vector<std::array<int64_t, 2>> &polygon : thing.polygons)
            {
                writer.beginArray();

                for (const std::array<int64_t, 2> &point : polygon)
                {
                    writer.beginArray();
                    writer.value(point[0]);
                    writer.value(point[1]);
                    writer.endArray();
                }

                writer.endArray();
            }

            writer.endArray();
        }

        writer.endObject();
    }

    writer.endArray();

    // The cinematics (S8a): the base map's, kept or replaced by one of the project's of the same name, and the
    // project's others, added (the game merges the overlay's file by name).
    const std::vector<std::string> baseNames = baseCinematicNames(session, stem);
    std::vector<std::string> ownNames;

    for (const YAML::Node &cinematic : childOf(project.document("wiring.yml"), "cinematics"))
    {
        ownNames.push_back(nameOf(textOf(cinematic, "id", "")));
    }

    if (!baseNames.empty() || !ownNames.empty())
    {
        writer.key("cinematics");
        writer.beginArray();
        const auto entry = [&writer](const std::string &name, const char *pState)
        {
            writer.beginObject();
            writer.field("id", "cinematic:" + name);
            writer.field("state", pState);
            writer.endObject();
        };

        for (const std::string &name : baseNames)
        {
            entry(name, std::find(ownNames.begin(), ownNames.end(), name) != ownNames.end() ? "replaced" : "kept");
        }

        for (const std::string &name : ownNames)
        {
            if (std::find(baseNames.begin(), baseNames.end(), name) == baseNames.end())
            {
                entry(name, "added");
            }
        }

        writer.endArray();
    }

    writer.key("issues");
    writer.beginArray();

    for (const ProjectIssue &issue : issues)
    {
        writer.beginObject();
        writer.field("file", issue.file);
        writer.field("path", issue.path);
        writer.field("message", issue.message);
        writer.endObject();
    }

    writer.endArray();
    return true;
}
}
