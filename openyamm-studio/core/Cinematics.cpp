#include "core/Cinematics.h"

#include "core/CanonicalYaml.h"
#include "core/Json.h"
#include "core/SketchRead.h"

#include "game/gameplay/CinematicLibrary.h"

#include <yaml-cpp/yaml.h>

#include <array>
#include <cmath>
#include <map>
#include <optional>
#include <set>

namespace OpenYAMM::Studio
{
namespace
{
// The party's eye over its feet (the game's indoor camera height): where a room's centre is looked at from.
constexpr double EyeHeight = 160.0;

double numberIn(const YAML::Node &node, const char *pKey, double fallback)
{
    const YAML::Node value = childOf(node, pKey);

    if (!value.IsDefined() || !value.IsScalar())
    {
        return fallback;
    }

    try
    {
        return value.as<double>();
    }
    catch (const std::exception &)
    {
        return fallback;
    }
}

YAML::Node numberNode(double value)
{
    const double rounded = std::round(value * 1000.0) / 1000.0;

    if (rounded == std::floor(rounded))
    {
        return YAML::Node(static_cast<long long>(rounded));
    }

    return YAML::Node(rounded);
}

YAML::Node point(const std::array<double, 3> &value)
{
    YAML::Node sequence(YAML::NodeType::Sequence);

    for (const double coordinate : value)
    {
        sequence.push_back(numberNode(coordinate));
    }

    sequence.SetStyle(YAML::EmitterStyle::Flow);
    return sequence;
}

// What a place word names: a point, an object the build placed, a placed monster (an actor), the start or a room.
struct Place
{
    std::array<double, 3> position = {};
    std::optional<size_t> actor;
};

class CinematicsWriter
{
public:
    CinematicsWriter(const Project &project, const LoweredIndoorMap &lowered, std::vector<ProjectIssue> &issues)
        : m_project(project)
        , m_lowered(lowered)
        , m_issues(issues)
    {
    }

    bool run(std::string &text)
    {
        const size_t before = m_issues.size();
        const YAML::Node list = childOf(m_project.document("wiring.yml"), "cinematics");
        text.clear();

        if (!list.IsDefined() || !list.IsSequence() || list.size() == 0)
        {
            return true;
        }

        YAML::Node document(YAML::NodeType::Map);
        document["format_version"] = 1;
        document["kind"] = "openyamm_cinematics";
        document["source"] = "Written by oymap build from the Map Studio project \""
            + textOf(m_project.document("project.yml"), "id", "") + "\" (wiring.yml cinematics). Change the project, "
            "not this file.";
        size_t index = 0;
        std::set<std::string> names;

        for (const YAML::Node &cinematic : list)
        {
            const std::string path = "cinematics[" + std::to_string(index++) + "]";
            const std::string name = cinematicName(textOf(cinematic, "id", ""));

            if (!names.insert(name).second)
            {
                issue(path + ".id", "two cinematics are named " + name);
                continue;
            }

            YAML::Node out(YAML::NodeType::Map);

            for (const char *pFlag : {"skippable", "letterbox"})
            {
                if (childOf(cinematic, pFlag).IsDefined())
                {
                    out[pFlag] = textOf(cinematic, pFlag, "true") != "false";
                }
            }

            if (childOf(cinematic, "letterbox_seconds").IsDefined())
            {
                out["letterbox_seconds"] = numberNode(numberIn(cinematic, "letterbox_seconds", 0.5));
            }

            size_t shotIndex = 0;

            for (const YAML::Node &shot : childOf(cinematic, "shots"))
            {
                YAML::Node written;

                if (writeShot(shot, path + ".shots[" + std::to_string(shotIndex++) + "]", written))
                {
                    out["shots"].push_back(written);
                }
            }

            size_t cueIndex = 0;

            for (const YAML::Node &cue : childOf(cinematic, "cues"))
            {
                YAML::Node written;

                if (writeCue(cue, path + ".cues[" + std::to_string(cueIndex++) + "]", written))
                {
                    out["cues"].push_back(written);
                }
            }

            if (childOf(cinematic, "notes").IsDefined())
            {
                out["note"] = textOf(cinematic, "notes", "");
            }

            document["cinematics"][name] = out;
        }

        if (m_issues.size() != before)
        {
            return false;
        }

        text = writeCanonicalYaml(document);
        // The game's own parser (game/gameplay/CinematicLibrary.h, G4) reads the file as the game will.
        std::string parseError;

        if (!Game::parseCinematicLibrary(text, parseError))
        {
            issue("cinematics", "the game refuses the cinematics file: " + parseError);
            text.clear();
            return false;
        }

        return true;
    }

private:
    void issue(const std::string &path, const std::string &message)
    {
        m_issues.push_back({"wiring.yml", path, message, "cinematic"});
    }

    // A place word: [x, y, z], or an id (with `offset` added).
    std::optional<Place> placeOf(const YAML::Node &node, const YAML::Node &offset, const std::string &path)
    {
        Place place;

        if (node.IsSequence() && node.size() == 3)
        {
            for (size_t axis = 0; axis < 3; ++axis)
            {
                try
                {
                    place.position[axis] = node[axis].as<double>();
                }
                catch (const std::exception &)
                {
                    issue(path, "a point is three numbers [x, y, z]");
                    return std::nullopt;
                }
            }
        }
        else if (node.IsScalar())
        {
            const std::string id = node.Scalar();
            bool found = false;

            for (const LoweredPlaced &placed : m_lowered.placed)
            {
                if (placed.id == id)
                {
                    place.position = placed.position;
                    found = true;
                }
            }

            for (size_t actor = 0; actor < m_lowered.monsters.size() && !found; ++actor)
            {
                if (m_lowered.monsters[actor].id == id)
                {
                    place.position = m_lowered.monsters[actor].position;
                    // Its number among the map's actors (an overlay's stand after the base map's).
                    place.actor = m_lowered.firstActor + actor;
                    found = true;
                }
            }

            if (!found && (id == "start" || id == "party_start") && m_lowered.start)
            {
                place.position = m_lowered.start->position;
                found = true;
            }

            for (const LoweredRoom &room : m_lowered.rooms)
            {
                if (!found && room.id == id && !room.outline.empty())
                {
                    double x = 0.0;
                    double y = 0.0;

                    for (const std::array<double, 2> &corner : room.outline)
                    {
                        x += corner[0];
                        y += corner[1];
                    }

                    place.position = {x / double(room.outline.size()), y / double(room.outline.size()),
                        room.floor + EyeHeight};
                    found = true;
                }
            }

            if (!found)
            {
                issue(path, id + " is no point and nothing the map placed (a decoration, light, spawn, switch, exit, "
                    "placed monster, room or `start`)");
                return std::nullopt;
            }
        }
        else
        {
            issue(path, "a place is [x, y, z] or an object's id");
            return std::nullopt;
        }

        if (offset.IsDefined() && offset.IsSequence() && offset.size() == 3)
        {
            for (size_t axis = 0; axis < 3; ++axis)
            {
                place.position[axis] += offset[axis].as<double>();
            }
        }

        return place;
    }

    // A camera key: position and one aim, the shot's field of view.
    bool writeKey(const YAML::Node &node, const std::string &path, const YAML::Node &fov, YAML::Node &out)
    {
        const std::optional<Place> at = placeOf(childOf(node, "at"), childOf(node, "offset"), path + ".at");

        if (!at)
        {
            return false;
        }

        out["position"] = point(at->position);
        const bool hasLook = childOf(node, "look_at").IsDefined();
        const bool hasAngles = childOf(node, "yaw").IsDefined() || childOf(node, "pitch").IsDefined();

        if (hasLook == hasAngles)
        {
            issue(path, "a camera looks at one thing: `look_at` (a point or an object), or `yaw` with `pitch`");
            return false;
        }

        if (hasLook)
        {
            const std::optional<Place> target = placeOf(childOf(node, "look_at"), YAML::Node(), path + ".look_at");

            if (!target)
            {
                return false;
            }

            if (target->actor)
            {
                out["look_at_actor"] = static_cast<int>(*target->actor);
            }
            else
            {
                out["look_at"] = point(target->position);
            }
        }
        else
        {
            const double pitch = numberIn(node, "pitch", 0.0);

            if (pitch < -89.0 || pitch > 89.0)
            {
                issue(path + ".pitch", "pitch is -89 to 89 degrees");
                return false;
            }

            out["yaw"] = numberNode(numberIn(node, "yaw", 0.0));
            out["pitch"] = numberNode(pitch);
        }

        if (fov.IsDefined())
        {
            out["fov"] = numberNode(fov.as<double>());
        }

        return true;
    }

    bool writeShot(const YAML::Node &shot, const std::string &path, YAML::Node &out)
    {
        const double seconds = numberIn(shot, "seconds", 0.0);
        out = YAML::Node(YAML::NodeType::Map);
        out["duration"] = numberNode(seconds);

        if (!(seconds > 0.0))
        {
            issue(path + ".seconds", "a shot lasts more than 0 seconds");
            return false;
        }

        if (textOf(shot, "party", "false") == "true")
        {
            if (childOf(shot, "at").IsDefined() || childOf(shot, "keys").IsDefined())
            {
                issue(path, "a shot of the party's own view has no camera (`at`, `keys`)");
                return false;
            }

            out["party"] = true;
            return true;
        }

        const YAML::Node fov = childOf(shot, "fov");
        const YAML::Node keys = childOf(shot, "keys");

        if (fov.IsDefined() && (fov.as<double>() < 10.0 || fov.as<double>() > 120.0))
        {
            issue(path + ".fov", "the field of view is 10 to 120 degrees");
            return false;
        }

        if (childOf(shot, "easing").IsDefined())
        {
            out["easing"] = textOf(shot, "easing", "smooth");
        }

        if (!keys.IsDefined() || keys.size() == 0)
        {
            YAML::Node key(YAML::NodeType::Map);

            if (!writeKey(shot, path, fov, key))
            {
                return false;
            }

            for (YAML::const_iterator entry = key.begin(); entry != key.end(); ++entry)
            {
                out[entry->first.Scalar()] = entry->second;
            }

            return true;
        }

        // A moving camera: the shot's own place at 0, then its keys in increasing time within the shot.
        YAML::Node first(YAML::NodeType::Map);
        first["at"] = 0;

        if (!writeKey(shot, path, fov, first))
        {
            return false;
        }

        out["keys"].push_back(first);
        double last = 0.0;
        size_t index = 0;

        for (const YAML::Node &key : keys)
        {
            const std::string keyPath = path + ".keys[" + std::to_string(index++) + "]";
            const double at = numberIn(key, "seconds", -1.0);

            if (!(at > last) || at > seconds + 1.0e-3)
            {
                issue(keyPath + ".seconds", "a key's `seconds` lie after the one before it (" + formatNumber(last)
                    + ") and within the shot (" + formatNumber(seconds) + ")");
                return false;
            }

            YAML::Node written(YAML::NodeType::Map);
            written["at"] = numberNode(at);

            if (!writeKey(key, keyPath, fov, written))
            {
                return false;
            }

            out["keys"].push_back(written);
            last = at;
        }

        return true;
    }

    std::optional<int> eventNumber(const std::string &id, const std::string &path)
    {
        for (const LoweredEvent &event : m_lowered.events)
        {
            if (event.id == id)
            {
                return event.eventId;
            }
        }

        // An overlay's cue may run one of the base map's events, by its id in ids.lock.yml (evt:e<number>).
        if (m_lowered.overlay)
        {
            const std::map<std::string, int>::const_iterator base = m_lowered.ids.events.find(id);

            if (base != m_lowered.ids.events.end())
            {
                return base->second;
            }
        }

        issue(path, id + " is no event of wiring.yml");
        return std::nullopt;
    }

    bool writeCue(const YAML::Node &cue, const std::string &path, YAML::Node &out)
    {
        out = YAML::Node(YAML::NodeType::Map);
        out["at"] = numberNode(numberIn(cue, "at", 0.0));
        int kinds = 0;

        for (const char *pKind : {"event", "sound", "subtitle", "fade", "letterbox", "shake", "monster"})
        {
            kinds += childOf(cue, pKind).IsDefined() ? 1 : 0;
        }

        if (kinds != 1)
        {
            issue(path, "a cue does one thing: event, sound, subtitle, fade, letterbox, shake or monster");
            return false;
        }

        const YAML::Node seconds = childOf(cue, "seconds");

        if (childOf(cue, "event").IsDefined() || childOf(cue, "sound").IsDefined())
        {
            if (seconds.IsDefined())
            {
                issue(path + ".seconds", "an event or a sound takes no `seconds`");
                return false;
            }

            if (childOf(cue, "sound").IsDefined())
            {
                out["sound"] = textOf(cue, "sound", "");
                return true;
            }

            const std::optional<int> number = eventNumber(textOf(cue, "event", ""), path + ".event");

            if (!number)
            {
                return false;
            }

            out["event"] = *number;
            return true;
        }

        if (childOf(cue, "subtitle").IsDefined())
        {
            if (!seconds.IsDefined() || seconds.as<double>() < 0.1)
            {
                issue(path + ".seconds", "a subtitle stays its `seconds`, at least 0.1");
                return false;
            }

            out["subtitle"] = textOf(cue, "subtitle", "");
        }
        else if (childOf(cue, "fade").IsDefined())
        {
            out["fade"] = textOf(cue, "fade", "in");
        }
        else if (childOf(cue, "letterbox").IsDefined())
        {
            out["letterbox"] = textOf(cue, "letterbox", "true") != "false";
        }
        else if (childOf(cue, "shake").IsDefined())
        {
            out["shake"] = numberNode(numberIn(cue, "shake", 0.5));
        }
        else
        {
            const std::string monster = textOf(cue, "monster", "");
            const std::string action = textOf(cue, "action", "");
            std::optional<size_t> actor;

            for (size_t index = 0; index < m_lowered.monsters.size(); ++index)
            {
                actor = m_lowered.monsters[index].id == monster ? std::optional<size_t>(index) : actor;
            }

            if (!actor)
            {
                issue(path + ".monster", monster + " is no placed monster of objects.yml (`monsters`; in an overlay "
                    "`scene.monsters`)");
                return false;
            }

            if (action.empty())
            {
                issue(path + ".action", "a monster cue says what it does: show, hide, place, move or face");
                return false;
            }

            out["actor"] = static_cast<int>(m_lowered.firstActor + *actor);
            out["action"] = action;

            if (action == "place" || action == "move")
            {
                const std::optional<Place> to = placeOf(childOf(cue, "to"), YAML::Node(), path + ".to");

                if (!to)
                {
                    return false;
                }

                out["to"] = point(to->position);
            }

            if (action == "face")
            {
                const std::optional<Place> target = placeOf(childOf(cue, "look_at"), YAML::Node(), path + ".look_at");

                if (!target)
                {
                    return false;
                }

                if (target->actor)
                {
                    out["look_at_actor"] = static_cast<int>(*target->actor);
                }
                else
                {
                    out["look_at"] = point(target->position);
                }
            }

            if ((action == "move") && !seconds.IsDefined())
            {
                issue(path + ".seconds", "a move takes its `seconds`");
                return false;
            }
        }

        if (seconds.IsDefined())
        {
            out["seconds"] = numberNode(seconds.as<double>());
        }

        return true;
    }

    const Project &m_project;
    const LoweredIndoorMap &m_lowered;
    std::vector<ProjectIssue> &m_issues;
};
}

std::string cinematicName(const std::string &id)
{
    const size_t colon = id.find(':');
    return colon == std::string::npos ? id : id.substr(colon + 1);
}

bool writeCinematicsText(
    const Project &project,
    const LoweredIndoorMap &lowered,
    std::string &text,
    std::vector<ProjectIssue> &issues)
{
    CinematicsWriter writer(project, lowered, issues);
    return writer.run(text);
}
}
