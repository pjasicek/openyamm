#include "game/gameplay/CinematicLibrary.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cmath>
#include <exception>
#include <initializer_list>
#include <numbers>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
constexpr int CinematicFormatVersion = 1;
constexpr const char *CinematicFileKind = "openyamm_cinematics";
constexpr float MinFovDegrees = 10.0f;
constexpr float MaxFovDegrees = 120.0f;

// Reads one cinematic's YAML with the context its error messages need.
class Reader
{
public:
    explicit Reader(std::string &error)
        : m_error(error)
    {
    }

    bool fail(const std::string &where, const std::string &message)
    {
        m_error = where + ": " + message;
        return false;
    }

    bool onlyKeys(const YAML::Node &node, const std::string &where, std::initializer_list<const char *> keys)
    {
        for (const auto &entry : node)
        {
            const std::string key = entry.first.as<std::string>();
            bool known = false;

            for (const char *pKey : keys)
            {
                known = known || key == pKey;
            }

            if (!known)
            {
                std::string list;

                for (const char *pKey : keys)
                {
                    list += list.empty() ? pKey : std::string(", ") + pKey;
                }

                return fail(where, "unknown key '" + key + "' (known: " + list + ")");
            }
        }

        return true;
    }

    bool number(const YAML::Node &node, const std::string &where, float minimum, float maximum, float &value)
    {
        double parsed = 0.0;

        try
        {
            if (!node.IsScalar())
            {
                return fail(where, "must be a number");
            }

            parsed = node.as<double>();
        }
        catch (const std::exception &)
        {
            return fail(where, "must be a number");
        }

        if (!std::isfinite(parsed) || parsed < minimum || parsed > maximum)
        {
            return fail(where, "must be a number in [" + std::to_string(minimum) + ", " + std::to_string(maximum) + "]");
        }

        value = float(parsed);
        return true;
    }

    bool integer(const YAML::Node &node, const std::string &where, int64_t minimum, int64_t maximum, int64_t &value)
    {
        try
        {
            if (!node.IsScalar())
            {
                return fail(where, "must be an integer");
            }

            value = node.as<int64_t>();
        }
        catch (const std::exception &)
        {
            return fail(where, "must be an integer");
        }

        if (value < minimum || value > maximum)
        {
            return fail(where, "must be an integer in [" + std::to_string(minimum) + ", " + std::to_string(maximum)
                + "]");
        }

        return true;
    }

    bool boolean(const YAML::Node &node, const std::string &where, bool &value)
    {
        try
        {
            value = node.as<bool>();
            return true;
        }
        catch (const std::exception &)
        {
            return fail(where, "must be true or false");
        }
    }

    bool text(const YAML::Node &node, const std::string &where, std::string &value)
    {
        if (!node.IsScalar())
        {
            return fail(where, "must be text");
        }

        value = node.as<std::string>();
        return true;
    }

    bool point(const YAML::Node &node, const std::string &where, GameplayWorldPoint &value)
    {
        if (!node.IsSequence() || node.size() != 3)
        {
            return fail(where, "must be [x, y, z]");
        }

        constexpr float Limit = 1.0e7f;
        return number(node[0], where + "[0]", -Limit, Limit, value.x)
            && number(node[1], where + "[1]", -Limit, Limit, value.y)
            && number(node[2], where + "[2]", -Limit, Limit, value.z);
    }

    // A camera key's position and aim: position plus one of look_at, look_at_actor, look_at_party, direction or
    // yaw/pitch (degrees), and an optional fov.
    bool cameraKey(const YAML::Node &node, const std::string &where, CinematicCameraKey &key)
    {
        if (!node["position"] || !point(node["position"], where + " position", key.position))
        {
            return node["position"] ? false : fail(where, "needs position: [x, y, z]");
        }

        int aims = 0;

        if (const YAML::Node lookAt = node["look_at"])
        {
            ++aims;
            key.aim = CinematicAim::Point;

            if (!point(lookAt, where + " look_at", key.aimVector))
            {
                return false;
            }
        }

        if (const YAML::Node actor = node["look_at_actor"])
        {
            ++aims;
            key.aim = CinematicAim::Actor;
            int64_t index = 0;

            if (!integer(actor, where + " look_at_actor", 0, 65535, index))
            {
                return false;
            }

            key.actorIndex = size_t(index);
        }

        if (const YAML::Node party = node["look_at_party"])
        {
            ++aims;
            key.aim = CinematicAim::Party;
            bool value = false;

            if (!boolean(party, where + " look_at_party", value))
            {
                return false;
            }

            if (!value)
            {
                return fail(where, "look_at_party must be true when given");
            }
        }

        if (const YAML::Node direction = node["direction"])
        {
            ++aims;
            key.aim = CinematicAim::Direction;

            if (!point(direction, where + " direction", key.aimVector))
            {
                return false;
            }

            const float length = std::sqrt(key.aimVector.x * key.aimVector.x + key.aimVector.y * key.aimVector.y
                + key.aimVector.z * key.aimVector.z);

            if (length < 1.0e-4f)
            {
                return fail(where, "direction must not be zero");
            }

            key.aimVector = {key.aimVector.x / length, key.aimVector.y / length, key.aimVector.z / length};
        }

        if (node["yaw"] || node["pitch"])
        {
            ++aims;
            float yawDegrees = 0.0f;
            float pitchDegrees = 0.0f;

            if (!node["yaw"] || !number(node["yaw"], where + " yaw", -720.0f, 720.0f, yawDegrees))
            {
                return node["yaw"] ? false : fail(where, "yaw and pitch go together (degrees)");
            }

            if (!node["pitch"] || !number(node["pitch"], where + " pitch", -89.0f, 89.0f, pitchDegrees))
            {
                return node["pitch"] ? false : fail(where, "yaw and pitch go together (degrees)");
            }

            const float yaw = yawDegrees * std::numbers::pi_v<float> / 180.0f;
            const float pitch = pitchDegrees * std::numbers::pi_v<float> / 180.0f;
            key.aim = CinematicAim::Direction;
            key.aimVector = {std::cos(yaw) * std::cos(pitch), std::sin(yaw) * std::cos(pitch), std::sin(pitch)};
        }

        if (aims != 1)
        {
            return fail(where, "needs exactly one aim: look_at, look_at_actor, look_at_party, direction or yaw/pitch");
        }

        if (const YAML::Node fov = node["fov"])
        {
            float degrees = 0.0f;

            if (!number(fov, where + " fov", MinFovDegrees, MaxFovDegrees, degrees))
            {
                return false;
            }

            key.verticalFovDegrees = degrees;
        }

        return true;
    }

    bool shot(const YAML::Node &node, const std::string &where, CinematicShot &shot)
    {
        if (!node.IsMap())
        {
            return fail(where, "must be a map");
        }

        if (!onlyKeys(node, where, {"duration", "party", "keys", "easing", "position", "look_at", "look_at_actor",
                "look_at_party", "direction", "yaw", "pitch", "fov", "note"}))
        {
            return false;
        }

        if (!node["duration"] || !number(node["duration"], where + " duration", 0.001f, MaxCinematicSeconds,
                shot.durationSeconds))
        {
            return node["duration"] ? false : fail(where, "needs duration (seconds)");
        }

        if (const YAML::Node easing = node["easing"])
        {
            std::string name;

            if (!text(easing, where + " easing", name))
            {
                return false;
            }

            if (name == "linear")
            {
                shot.easing = CinematicEasing::Linear;
            }
            else if (name == "smooth")
            {
                shot.easing = CinematicEasing::Smooth;
            }
            else if (name == "spline")
            {
                shot.easing = CinematicEasing::Spline;
            }
            else
            {
                return fail(where, "easing must be linear, smooth or spline");
            }
        }

        bool partyView = false;

        if (const YAML::Node party = node["party"]; party && !boolean(party, where + " party", partyView))
        {
            return false;
        }

        const bool single = bool(node["position"]);
        const bool keyed = bool(node["keys"]);

        if (int(partyView) + int(single) + int(keyed) != 1)
        {
            return fail(where, "needs exactly one of party: true, position (a fixed camera) or keys");
        }

        if (partyView)
        {
            return true;
        }

        if (single)
        {
            CinematicCameraKey key = {};

            if (!cameraKey(node, where, key))
            {
                return false;
            }

            shot.keys.push_back(key);
            return true;
        }

        for (const char *pKey : {"look_at", "look_at_actor", "look_at_party", "direction", "yaw", "pitch", "fov"})
        {
            if (node[pKey])
            {
                return fail(where, std::string("'") + pKey + "' belongs in each of its keys");
            }
        }

        const YAML::Node keys = node["keys"];

        if (!keys.IsSequence() || keys.size() < 2)
        {
            return fail(where, "keys must list at least two camera keys (one: use position)");
        }

        for (size_t index = 0; index < keys.size(); ++index)
        {
            const std::string keyWhere = where + " key " + std::to_string(index + 1);
            const YAML::Node keyNode = keys[index];

            if (!keyNode.IsMap()
                || !onlyKeys(keyNode, keyWhere, {"at", "position", "look_at", "look_at_actor", "look_at_party",
                    "direction", "yaw", "pitch", "fov", "note"}))
            {
                return keyNode.IsMap() ? false : fail(keyWhere, "must be a map");
            }

            CinematicCameraKey key = {};

            // A key may sit at the shot's end (the float duration against the text's exact time: a little slack).
            if (!keyNode["at"]
                || !number(keyNode["at"], keyWhere + " at", 0.0f, shot.durationSeconds + 1.0e-3f, key.atSeconds))
            {
                return keyNode["at"] ? false : fail(keyWhere, "needs at (seconds into the shot)");
            }

            if (index == 0 && key.atSeconds != 0.0f)
            {
                return fail(keyWhere, "the first key must be at 0");
            }

            if (index > 0 && key.atSeconds <= shot.keys.back().atSeconds)
            {
                return fail(keyWhere, "keys must be in increasing time");
            }

            if (!cameraKey(keyNode, keyWhere, key))
            {
                return false;
            }

            shot.keys.push_back(key);
        }

        return true;
    }

    bool cue(const YAML::Node &node, const std::string &where, float defaultLetterboxSeconds, CinematicCue &cue)
    {
        if (!node.IsMap())
        {
            return fail(where, "must be a map");
        }

        if (!onlyKeys(node, where, {"at", "fade", "letterbox", "sound", "subtitle", "event", "actor", "action", "to",
                "look_at", "look_at_actor", "look_at_party", "clip", "loop", "decoration", "offset", "shake", "seconds",
                "color", "note"}))
        {
            return false;
        }

        if (!node["at"] || !number(node["at"], where + " at", 0.0f, MaxCinematicSeconds, cue.atSeconds))
        {
            return node["at"] ? false : fail(where, "needs at (seconds from the start)");
        }

        int kinds = 0;

        for (const char *pKey : {"fade", "letterbox", "sound", "subtitle", "event", "actor", "decoration", "shake"})
        {
            kinds += node[pKey] ? 1 : 0;
        }

        if (kinds != 1)
        {
            return fail(where,
                "needs exactly one of fade, letterbox, sound, subtitle, event, actor, decoration or shake");
        }

        // Keys only some cues take: every other cue refuses them.
        const auto noActorKeys =
            [&]() -> bool
            {
                for (const char *pKey : {"look_at", "look_at_actor", "look_at_party", "clip", "loop", "offset"})
                {
                    if (node[pKey] && !(std::string(pKey) == "offset" && node["decoration"]))
                    {
                        return fail(where, std::string("'") + pKey + "' does not belong to this cue");
                    }
                }

                return true;
            };

        if (!node["actor"] && !noActorKeys())
        {
            return false;
        }

        const YAML::Node secondsNode = node["seconds"];
        const auto seconds =
            [&](float defaultSeconds, float minimum) -> bool
            {
                cue.seconds = defaultSeconds;
                return !secondsNode || number(secondsNode, where + " seconds", minimum, MaxCinematicSeconds, cue.seconds);
            };
        const auto noExtras =
            [&](std::initializer_list<const char *> keys) -> bool
            {
                for (const char *pKey : keys)
                {
                    if (node[pKey])
                    {
                        return fail(where, std::string("'") + pKey + "' does not belong to this cue");
                    }
                }

                return true;
            };

        if (node["color"] && !node["fade"])
        {
            return fail(where, "'color' belongs to a fade cue only");
        }

        if (const YAML::Node fade = node["fade"])
        {
            std::string direction;

            if (!text(fade, where + " fade", direction) || !noExtras({"action", "to"}) || !seconds(1.0f, 0.0f))
            {
                return false;
            }

            if (direction != "in" && direction != "out")
            {
                return fail(where, "fade must be in (from its colour) or out (to its colour)");
            }

            // color: [r, g, b] (0-255) the screen fades to or from; black by default.
            if (const YAML::Node color = node["color"])
            {
                if (!color.IsSequence() || color.size() != 3)
                {
                    return fail(where, "color must be [r, g, b], each 0-255");
                }

                for (size_t channel = 0; channel < 3; ++channel)
                {
                    float value = 0.0f;

                    if (!number(color[channel], where + " color", 0.0f, 255.0f, value))
                    {
                        return false;
                    }

                    cue.colorRgb[channel] = uint8_t(std::lround(value));
                }
            }

            cue.kind = direction == "out" ? CinematicCueKind::FadeOut : CinematicCueKind::FadeIn;
            return true;
        }

        if (const YAML::Node letterbox = node["letterbox"])
        {
            bool on = false;

            if (!boolean(letterbox, where + " letterbox", on) || !noExtras({"action", "to"})
                || !seconds(defaultLetterboxSeconds, 0.0f))
            {
                return false;
            }

            cue.kind = CinematicCueKind::Letterbox;
            cue.amount = on ? 1.0f : 0.0f;
            return true;
        }

        if (const YAML::Node sound = node["sound"])
        {
            cue.kind = CinematicCueKind::Sound;
            return text(sound, where + " sound", cue.text) && noExtras({"action", "to", "seconds"})
                && (!cue.text.empty() || fail(where, "sound needs a name"));
        }

        if (const YAML::Node subtitle = node["subtitle"])
        {
            cue.kind = CinematicCueKind::Subtitle;

            if (!secondsNode)
            {
                return fail(where, "subtitle needs seconds");
            }

            return text(subtitle, where + " subtitle", cue.text) && noExtras({"action", "to"}) && seconds(0.0f, 0.1f);
        }

        if (const YAML::Node event = node["event"])
        {
            int64_t id = 0;
            cue.kind = CinematicCueKind::Event;

            if (!integer(event, where + " event", 1, 65535, id) || !noExtras({"action", "to", "seconds"}))
            {
                return false;
            }

            cue.eventId = uint16_t(id);
            return true;
        }

        if (const YAML::Node decoration = node["decoration"])
        {
            int64_t key = 0;
            cue.kind = CinematicCueKind::DecorationMove;

            if (!integer(decoration, where + " decoration", 1, 0xffffffffll, key) || !noExtras({"action", "to"}))
            {
                return false;
            }

            cue.decorationKey = uint32_t(key);

            if (!node["offset"] || !point(node["offset"], where + " offset", cue.point))
            {
                return node["offset"] ? false : fail(where, "a decoration cue needs offset: [dx, dy, dz]");
            }

            return seconds(0.0f, 0.0f);
        }

        if (const YAML::Node shake = node["shake"])
        {
            cue.kind = CinematicCueKind::Shake;

            if (!secondsNode)
            {
                return fail(where, "shake needs seconds");
            }

            return number(shake, where + " shake", 0.001f, 10.0f, cue.amount) && noExtras({"action", "to"})
                && seconds(0.0f, 0.01f);
        }

        int64_t actor = 0;

        if (!integer(node["actor"], where + " actor", 0, 65535, actor))
        {
            return false;
        }

        cue.actorIndex = size_t(actor);
        std::string action;

        if (!node["action"] || !text(node["action"], where + " action", action))
        {
            return node["action"] ? false : fail(where, "an actor cue needs action: show, hide, place or move");
        }

        const auto noFaceOrClipKeys =
            [&](bool face, bool clip) -> bool
            {
                for (const char *pKey : {"look_at", "look_at_actor", "look_at_party"})
                {
                    if (!face && node[pKey])
                    {
                        return fail(where, std::string("'") + pKey + "' belongs to an actor face cue");
                    }
                }

                for (const char *pKey : {"clip", "loop"})
                {
                    if (!clip && node[pKey])
                    {
                        return fail(where, std::string("'") + pKey + "' belongs to an actor clip cue");
                    }
                }

                return !node["offset"] || fail(where, "'offset' belongs to a decoration cue");
            };

        if (action == "show" || action == "hide")
        {
            cue.kind = action == "show" ? CinematicCueKind::ActorShow : CinematicCueKind::ActorHide;
            return noExtras({"to", "seconds"}) && noFaceOrClipKeys(false, false);
        }

        if (action == "face")
        {
            cue.kind = CinematicCueKind::ActorFace;
            int aims = 0;

            if (const YAML::Node lookAt = node["look_at"])
            {
                ++aims;
                cue.aim = CinematicAim::Point;

                if (!point(lookAt, where + " look_at", cue.point))
                {
                    return false;
                }
            }

            if (const YAML::Node other = node["look_at_actor"])
            {
                ++aims;
                cue.aim = CinematicAim::Actor;
                int64_t index = 0;

                if (!integer(other, where + " look_at_actor", 0, 65535, index))
                {
                    return false;
                }

                cue.aimActorIndex = size_t(index);
            }

            if (const YAML::Node party = node["look_at_party"])
            {
                ++aims;
                cue.aim = CinematicAim::Party;
                bool value = false;

                if (!boolean(party, where + " look_at_party", value) || !value)
                {
                    return value ? false : fail(where, "look_at_party must be true when given");
                }
            }

            if (aims != 1)
            {
                return fail(where, "an actor face cue needs exactly one of look_at, look_at_actor or look_at_party");
            }

            return noExtras({"to"}) && noFaceOrClipKeys(true, false) && seconds(0.0f, 0.0f);
        }

        if (action == "clip")
        {
            cue.kind = CinematicCueKind::ActorClip;

            if (!node["clip"] || !text(node["clip"], where + " clip", cue.text) || cue.text.empty())
            {
                return node["clip"] && !cue.text.empty() ? false : fail(where, "an actor clip cue needs clip: <name>");
            }

            if (const YAML::Node loop = node["loop"]; loop && !boolean(loop, where + " loop", cue.loop))
            {
                return false;
            }

            return noExtras({"to", "seconds"}) && noFaceOrClipKeys(false, true);
        }

        if (action != "place" && action != "move")
        {
            return fail(where, "actor action must be show, hide, place, move, face or clip");
        }

        if (!noFaceOrClipKeys(false, false))
        {
            return false;
        }

        if (!node["to"] || !point(node["to"], where + " to", cue.point))
        {
            return node["to"] ? false : fail(where, "actor " + action + " needs to: [x, y, z] (its feet)");
        }

        if (action == "place")
        {
            cue.kind = CinematicCueKind::ActorPlace;
            return noExtras({"seconds"});
        }

        cue.kind = CinematicCueKind::ActorMove;

        if (!secondsNode)
        {
            return fail(where, "actor move needs seconds");
        }

        return seconds(0.0f, 0.01f);
    }

private:
    std::string &m_error;
};

float cueEndSeconds(const CinematicCue &cue)
{
    switch (cue.kind)
    {
        case CinematicCueKind::FadeOut:
        case CinematicCueKind::FadeIn:
        case CinematicCueKind::Letterbox:
        case CinematicCueKind::Subtitle:
        case CinematicCueKind::ActorMove:
        case CinematicCueKind::ActorFace:
        case CinematicCueKind::Shake:
            return cue.atSeconds + cue.seconds;
        default:
            return cue.atSeconds;
    }
}

bool parseCinematic(const std::string &id, const YAML::Node &node, CinematicDefinition &definition, std::string &error)
{
    Reader reader(error);
    const std::string where = "cinematic '" + id + "'";

    if (!node.IsMap())
    {
        return reader.fail(where, "must be a map");
    }

    if (!reader.onlyKeys(node, where, {"skippable", "letterbox", "letterbox_seconds", "ambient", "shots", "cues",
            "source", "note"}))
    {
        return false;
    }

    definition.id = id;

    if (const YAML::Node skippable = node["skippable"];
        skippable && !reader.boolean(skippable, where + " skippable", definition.skippable))
    {
        return false;
    }

    if (const YAML::Node ambient = node["ambient"];
        ambient && !reader.boolean(ambient, where + " ambient", definition.ambient))
    {
        return false;
    }

    // An ambient one has no bars unless it asks (and then it may not: it never takes the view).
    definition.letterbox = !definition.ambient;

    if (const YAML::Node letterbox = node["letterbox"];
        letterbox && !reader.boolean(letterbox, where + " letterbox", definition.letterbox))
    {
        return false;
    }

    if (const YAML::Node seconds = node["letterbox_seconds"];
        seconds && !reader.number(seconds, where + " letterbox_seconds", 0.0f, 10.0f, definition.letterboxSeconds))
    {
        return false;
    }

    float shotsEnd = 0.0f;

    if (const YAML::Node shots = node["shots"])
    {
        if (!shots.IsSequence())
        {
            return reader.fail(where, "shots must be a list");
        }

        for (size_t index = 0; index < shots.size(); ++index)
        {
            CinematicShot shot = {};

            if (!reader.shot(shots[index], where + " shot " + std::to_string(index + 1), shot))
            {
                return false;
            }

            shotsEnd += shot.durationSeconds;
            definition.shots.push_back(std::move(shot));
        }
    }

    bool explicitLetterbox = false;

    if (const YAML::Node cues = node["cues"])
    {
        if (!cues.IsSequence())
        {
            return reader.fail(where, "cues must be a list");
        }

        for (size_t index = 0; index < cues.size(); ++index)
        {
            CinematicCue cue = {};

            if (!reader.cue(cues[index], where + " cue " + std::to_string(index + 1), definition.letterboxSeconds,
                    cue))
            {
                return false;
            }

            explicitLetterbox = explicitLetterbox || cue.kind == CinematicCueKind::Letterbox;
            definition.cues.push_back(std::move(cue));
        }
    }

    if (definition.shots.empty() && definition.cues.empty())
    {
        return reader.fail(where, "needs shots or cues");
    }

    if (definition.ambient)
    {
        if (!definition.shots.empty() || definition.letterbox || explicitLetterbox)
        {
            return reader.fail(where, "an ambient cinematic has no shots and no letterbox");
        }

        for (const CinematicCue &cue : definition.cues)
        {
            if (cue.kind == CinematicCueKind::FadeIn || cue.kind == CinematicCueKind::FadeOut)
            {
                return reader.fail(where, "an ambient cinematic has no fades");
            }
        }
    }

    definition.durationSeconds = shotsEnd;

    for (const CinematicCue &cue : definition.cues)
    {
        definition.durationSeconds = std::max(definition.durationSeconds, cueEndSeconds(cue));
    }

    if (definition.durationSeconds > MaxCinematicSeconds)
    {
        return reader.fail(where, "lasts longer than an hour");
    }

    // letterbox: true without letterbox cues: the bars come in at the start and go at the end.
    if (definition.letterbox && !explicitLetterbox)
    {
        const float seconds = std::min(definition.letterboxSeconds, definition.durationSeconds * 0.5f);
        CinematicCue in = {};
        in.kind = CinematicCueKind::Letterbox;
        in.amount = 1.0f;
        in.seconds = seconds;
        CinematicCue out = in;
        out.amount = 0.0f;
        out.atSeconds = definition.durationSeconds - seconds;
        definition.cues.push_back(in);
        definition.cues.push_back(out);
    }

    std::stable_sort(definition.cues.begin(), definition.cues.end(),
        [](const CinematicCue &left, const CinematicCue &right) { return left.atSeconds < right.atSeconds; });
    return true;
}
}

const CinematicDefinition *CinematicLibrary::find(const std::string &id) const
{
    for (const CinematicDefinition &definition : cinematics)
    {
        if (definition.id == id)
        {
            return &definition;
        }
    }

    return nullptr;
}

std::optional<CinematicLibrary> parseCinematicLibrary(const std::string &yamlText, std::string &error)
{
    error.clear();
    YAML::Node root;

    try
    {
        root = YAML::Load(yamlText);
    }
    catch (const std::exception &exception)
    {
        error = std::string("not valid YAML: ") + exception.what();
        return std::nullopt;
    }

    Reader reader(error);

    if (!root.IsMap())
    {
        reader.fail("cinematics file", "must be a map");
        return std::nullopt;
    }

    if (!reader.onlyKeys(root, "cinematics file", {"format_version", "kind", "source", "cinematics"}))
    {
        return std::nullopt;
    }

    int64_t version = 0;

    if (!root["format_version"]
        || !reader.integer(root["format_version"], "format_version", CinematicFormatVersion, CinematicFormatVersion,
            version))
    {
        if (!root["format_version"])
        {
            reader.fail("cinematics file", "needs format_version: 1");
        }

        return std::nullopt;
    }

    std::string kind;

    if (!root["kind"] || !reader.text(root["kind"], "kind", kind) || kind != CinematicFileKind)
    {
        reader.fail("cinematics file", std::string("needs kind: ") + CinematicFileKind);
        return std::nullopt;
    }

    const YAML::Node cinematics = root["cinematics"];

    if (!cinematics || !cinematics.IsMap())
    {
        reader.fail("cinematics file", "needs a cinematics map (id: cinematic)");
        return std::nullopt;
    }

    CinematicLibrary library = {};

    for (const auto &entry : cinematics)
    {
        const std::string id = entry.first.as<std::string>();

        if (id.empty() || library.find(id) != nullptr)
        {
            reader.fail("cinematic '" + id + "'", id.empty() ? "needs an id" : "is defined twice");
            return std::nullopt;
        }

        CinematicDefinition definition = {};

        if (!parseCinematic(id, entry.second, definition, error))
        {
            return std::nullopt;
        }

        library.cinematics.push_back(std::move(definition));
    }

    return library;
}

void mergeCinematicLibrary(CinematicLibrary &library, CinematicLibrary &&overlay)
{
    for (CinematicDefinition &definition : overlay.cinematics)
    {
        const auto found = std::find_if(library.cinematics.begin(), library.cinematics.end(),
            [&definition](const CinematicDefinition &existing) { return existing.id == definition.id; });

        if (found != library.cinematics.end())
        {
            *found = std::move(definition);
        }
        else
        {
            library.cinematics.push_back(std::move(definition));
        }
    }
}
}
