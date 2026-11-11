#include "game/gameplay/CinematicRuntime.h"
#include "engine/Localization.h"

#include "game/events/EventRuntime.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cmath>
#include <exception>
#include <initializer_list>
#include <limits>
#include <numbers>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
constexpr int CinematicFormatVersion = 1;
constexpr const char *CinematicFileKind = "openyamm_cinematics";
constexpr float MaxCinematicSeconds = 3600.0f;
constexpr float MinFovDegrees = 10.0f;
constexpr float MaxFovDegrees = 120.0f;
constexpr float MaxPitchRadians = 1.55f;
// Where the camera looks on an actor: three quarters of its height (about the face of a standing figure).
constexpr float ActorAimHeightFraction = 0.75f;
// CameraShake: radians of yaw (pitch: two thirds of it) at intensity 1, at the start of a shake.
constexpr float ShakeRadiansPerIntensity = 0.018f;

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
                "note"}))
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

        if (const YAML::Node fade = node["fade"])
        {
            std::string direction;

            if (!text(fade, where + " fade", direction) || !noExtras({"action", "to"}) || !seconds(1.0f, 0.0f))
            {
                return false;
            }

            if (direction != "in" && direction != "out")
            {
                return fail(where, "fade must be in (from black) or out (to black)");
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

GameplayWorldPoint lerp(const GameplayWorldPoint &from, const GameplayWorldPoint &to, float t)
{
    return {from.x + (to.x - from.x) * t, from.y + (to.y - from.y) * t, from.z + (to.z - from.z) * t};
}

std::optional<GameplayWorldPoint> normalized(const GameplayWorldPoint &vector)
{
    const float length = std::sqrt(vector.x * vector.x + vector.y * vector.y + vector.z * vector.z);

    if (length < 1.0e-4f)
    {
        return std::nullopt;
    }

    return GameplayWorldPoint{vector.x / length, vector.y / length, vector.z / length};
}

// The spline's velocity at a key (units per second): the neighbours' difference over their time span; zero at the
// first and last key and at a key with the same value as a neighbour (a hold).
GameplayWorldPoint splineTangent(const std::vector<GameplayWorldPoint> &values, const std::vector<float> &times,
    size_t index)
{
    const auto same = [&](size_t left, size_t right)
    {
        const GameplayWorldPoint &a = values[left];
        const GameplayWorldPoint &b = values[right];
        return std::abs(a.x - b.x) + std::abs(a.y - b.y) + std::abs(a.z - b.z) < 1.0e-3f;
    };

    if (index == 0 || index + 1 >= values.size() || same(index, index - 1) || same(index, index + 1)
        || times[index + 1] <= times[index - 1])
    {
        return {};
    }

    const float span = times[index + 1] - times[index - 1];
    const GameplayWorldPoint &next = values[index + 1];
    const GameplayWorldPoint &previous = values[index - 1];
    return {(next.x - previous.x) / span, (next.y - previous.y) / span, (next.z - previous.z) / span};
}

// The cubic Hermite between keys from and from + 1 at t (0..1 of the segment).
GameplayWorldPoint splineAt(const std::vector<GameplayWorldPoint> &values, const std::vector<float> &times,
    size_t from, float t)
{
    const size_t to = from + 1;
    const float duration = times[to] - times[from];
    const GameplayWorldPoint startTangent = splineTangent(values, times, from);
    const GameplayWorldPoint endTangent = splineTangent(values, times, to);
    const float t2 = t * t;
    const float t3 = t2 * t;
    const float h00 = 2.0f * t3 - 3.0f * t2 + 1.0f;
    const float h10 = (t3 - 2.0f * t2 + t) * duration;
    const float h01 = -2.0f * t3 + 3.0f * t2;
    const float h11 = (t3 - t2) * duration;
    const GameplayWorldPoint &p0 = values[from];
    const GameplayWorldPoint &p1 = values[to];
    return {h00 * p0.x + h10 * startTangent.x + h01 * p1.x + h11 * endTangent.x,
        h00 * p0.y + h10 * startTangent.y + h01 * p1.y + h11 * endTangent.y,
        h00 * p0.z + h10 * startTangent.z + h01 * p1.z + h11 * endTangent.z};
}

std::optional<GameplayWorldPoint> keyDirection(
    const CinematicCameraKey &key,
    const GameplayWorldPoint &eye,
    const ICinematicWorld &world)
{
    std::optional<GameplayWorldPoint> target;

    switch (key.aim)
    {
        case CinematicAim::Direction:
            return key.aimVector;
        case CinematicAim::Point:
            target = key.aimVector;
            break;
        case CinematicAim::Party:
            target = world.partyEye();
            break;
        case CinematicAim::Actor:
            if (const std::optional<GameplayWorldPoint> feet = world.actorFeet(key.actorIndex))
            {
                target = GameplayWorldPoint{feet->x, feet->y,
                    feet->z + world.actorHeight(key.actorIndex) * ActorAimHeightFraction};
            }
            break;
    }

    return target ? normalized({target->x - eye.x, target->y - eye.y, target->z - eye.z}) : std::nullopt;
}
}

void applyActorPresentation(const EventRuntimeState *pEvents, size_t actorIndex, GameplayRuntimeActorState &state)
{
    if (pEvents == nullptr || pEvents->actorPresentations.empty() || state.isDead)
    {
        return;
    }

    const auto found = pEvents->actorPresentations.find(uint32_t(actorIndex));

    if (found == pEvents->actorPresentations.end())
    {
        return;
    }

    const EventRuntimeState::ActorPresentation &presentation = found->second;

    if (!presentation.clip.empty())
    {
        state.scriptedClip = presentation.clip;
        state.scriptedClipThen = presentation.then;
        state.scriptedClipSeconds = presentation.clipSeconds;
        state.scriptedClipEnd = presentation.hold ? GameplayRuntimeActorState::ScriptedClipEnd::Hold
            : presentation.loop ? GameplayRuntimeActorState::ScriptedClipEnd::Loop
            : GameplayRuntimeActorState::ScriptedClipEnd::Release;
    }

    if (presentation.yawRadians)
    {
        state.yawRadians = *presentation.yawRadians;
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

void CameraShake::start(float intensity, float seconds)
{
    if (!(intensity > 0.0f) || !(seconds > 0.0f))
    {
        return;
    }

    Entry entry = {};
    entry.intensity = std::min(intensity, 10.0f);
    entry.seconds = std::min(seconds, MaxCinematicSeconds);
    // Each shake starts at its own phase, so two at once do not move in step.
    entry.phase = float(m_startCount++) * 2.399963f;
    m_entries.push_back(entry);
}

void CameraShake::update(float deltaSeconds)
{
    m_yawRadians = 0.0f;
    m_pitchRadians = 0.0f;

    for (Entry &entry : m_entries)
    {
        entry.elapsedSeconds += std::max(deltaSeconds, 0.0f);
    }

    std::erase_if(m_entries, [](const Entry &entry) { return entry.elapsedSeconds >= entry.seconds; });

    for (const Entry &entry : m_entries)
    {
        // Fades out over its seconds (quadratically: most of the shaking is early, as a quake's jolt).
        const float remaining = 1.0f - entry.elapsedSeconds / entry.seconds;
        const float amplitude = entry.intensity * ShakeRadiansPerIntensity * remaining * remaining;
        const float t = entry.elapsedSeconds;
        m_yawRadians += amplitude * (0.6f * std::sin(t * 71.0f + entry.phase) + 0.4f * std::sin(t * 117.0f
            + entry.phase * 1.7f));
        m_pitchRadians += amplitude * 0.67f * (0.6f * std::sin(t * 89.0f + entry.phase * 0.6f)
            + 0.4f * std::sin(t * 53.0f + entry.phase * 2.3f));
    }
}

void CameraShake::clear()
{
    m_entries.clear();
    m_yawRadians = 0.0f;
    m_pitchRadians = 0.0f;
}

bool CameraShake::active() const
{
    return !m_entries.empty();
}

float CameraShake::yawRadians() const
{
    return m_yawRadians;
}

float CameraShake::pitchRadians() const
{
    return m_pitchRadians;
}

void CinematicRuntime::start(const CinematicDefinition &definition, uint16_t doneEventId, ICinematicWorld &world)
{
    if (active())
    {
        skip(world, true);
        finish(world);
    }

    m_definition = definition;
    m_doneEventId = doneEventId;
    m_elapsedSeconds = 0.0f;
    m_nextCue = 0;
    m_ending = false;
    m_moves.clear();
    m_fadeFrom = m_fadeTo = m_fadeAmount = 0.0f;
    m_fadeSeconds = 0.0f;
    m_letterboxFrom = m_letterboxTo = m_letterboxAmount = 0.0f;
    m_letterboxSeconds = 0.0f;
    m_subtitle.clear();
    m_cameraView.reset();
    m_shotIndex.reset();
    update(0.0f, world);
}

void CinematicRuntime::update(float deltaSeconds, ICinematicWorld &world)
{
    if (!m_definition)
    {
        return;
    }

    // The last frame showed its end (or a skip): it finishes now, so that frame still drew the cinematic (a map move
    // its last event asks for happens after that frame, with no party view between).
    if (m_ending)
    {
        finish(world);
        return;
    }

    m_elapsedSeconds += std::max(deltaSeconds, 0.0f);

    while (m_definition && m_nextCue < m_definition->cues.size()
        && m_definition->cues[m_nextCue].atSeconds <= m_elapsedSeconds)
    {
        runCue(m_definition->cues[m_nextCue++], world);
    }

    if (!m_definition)
    {
        return;
    }

    advanceMoves(world);
    updatePresentation();
    updateCamera(world);

    m_ending = m_elapsedSeconds >= m_definition->durationSeconds && m_nextCue >= m_definition->cues.size();
}

bool CinematicRuntime::skip(ICinematicWorld &world, bool force)
{
    if (!m_definition || (!m_definition->skippable && !force))
    {
        return false;
    }

    // The rest of the cinematic happens at once: its map events in order, its actors at their last places.
    for (const ActorMove &move : m_moves)
    {
        world.placeActor(move.actorIndex, move.to);
    }

    m_moves.clear();

    while (m_definition && m_nextCue < m_definition->cues.size())
    {
        const CinematicCue &cue = m_definition->cues[m_nextCue++];

        switch (cue.kind)
        {
            case CinematicCueKind::Event:
            case CinematicCueKind::ActorShow:
            case CinematicCueKind::ActorHide:
            case CinematicCueKind::ActorPlace:
                runCue(cue, world);
                break;
            case CinematicCueKind::ActorMove:
                world.placeActor(cue.actorIndex, cue.point);
                break;
            case CinematicCueKind::DecorationMove:
                m_movedDecorations.emplace_back(cue.decorationKey, cue.point);
                break;
            default:
                break;
        }
    }

    // Decorations at their last offsets now (a glide still under way included).
    for (const auto &[key, offset] : m_movedDecorations)
    {
        world.moveDecoration(key, offset, 0.0f);
    }

    m_movedDecorations.clear();

    m_subtitle.clear();
    m_ending = true;
    return true;
}

void CinematicRuntime::stop()
{
    m_definition.reset();
    m_ending = false;
    m_presentedActors.clear();
    m_movedDecorations.clear();
    m_doneEventId = 0;
    m_elapsedSeconds = 0.0f;
    m_nextCue = 0;
    m_moves.clear();
    m_fadeAmount = 0.0f;
    m_letterboxAmount = 0.0f;
    m_subtitle.clear();
    m_cameraView.reset();
    m_shotIndex.reset();
}

bool CinematicRuntime::active() const
{
    return m_definition.has_value();
}

bool CinematicRuntime::skippable() const
{
    return m_definition && m_definition->skippable;
}

bool CinematicRuntime::takesOverView() const
{
    return m_definition && !m_definition->ambient;
}

const std::string &CinematicRuntime::activeId() const
{
    static const std::string None;
    return m_definition ? m_definition->id : None;
}

float CinematicRuntime::elapsedSeconds() const
{
    return m_elapsedSeconds;
}

std::optional<size_t> CinematicRuntime::activeShotIndex() const
{
    return m_cameraView ? m_shotIndex : std::nullopt;
}

const std::optional<CinematicCameraView> &CinematicRuntime::cameraView() const
{
    return m_cameraView;
}

float CinematicRuntime::letterboxAmount() const
{
    return m_letterboxAmount;
}

float CinematicRuntime::fadeAmount() const
{
    return m_fadeAmount;
}

const std::string &CinematicRuntime::subtitle() const
{
    return m_subtitle;
}

CameraShake &CinematicRuntime::shake()
{
    return m_shake;
}

const CameraShake &CinematicRuntime::shake() const
{
    return m_shake;
}

void CinematicRuntime::runCue(const CinematicCue &cue, ICinematicWorld &world)
{
    switch (cue.kind)
    {
        case CinematicCueKind::FadeOut:
        case CinematicCueKind::FadeIn:
            m_fadeFrom = cue.kind == CinematicCueKind::FadeOut ? m_fadeAmount : 1.0f;
            m_fadeTo = cue.kind == CinematicCueKind::FadeOut ? 1.0f : 0.0f;
            m_fadeStartSeconds = cue.atSeconds;
            m_fadeSeconds = cue.seconds;
            break;
        case CinematicCueKind::Letterbox:
            m_letterboxFrom = m_letterboxAmount;
            m_letterboxTo = cue.amount;
            m_letterboxStartSeconds = cue.atSeconds;
            m_letterboxSeconds = cue.seconds;
            break;
        case CinematicCueKind::Sound:
            world.playSound(cue.text);
            break;
        case CinematicCueKind::Subtitle:
            m_subtitle = Engine::localize(cue.text);
            m_subtitleEndSeconds = cue.atSeconds + cue.seconds;
            break;
        case CinematicCueKind::Event:
            world.runEvent(cue.eventId);
            break;
        case CinematicCueKind::ActorShow:
        case CinematicCueKind::ActorHide:
            world.setActorHidden(cue.actorIndex, cue.kind == CinematicCueKind::ActorHide);
            break;
        case CinematicCueKind::ActorPlace:
            std::erase_if(m_moves, [&](const ActorMove &move) { return move.actorIndex == cue.actorIndex; });
            world.placeActor(cue.actorIndex, cue.point);
            break;
        case CinematicCueKind::ActorMove:
            if (const std::optional<GameplayWorldPoint> feet = world.actorFeet(cue.actorIndex))
            {
                std::erase_if(m_moves, [&](const ActorMove &move) { return move.actorIndex == cue.actorIndex; });
                m_moves.push_back({cue.actorIndex, *feet, cue.point, cue.atSeconds, cue.seconds});
            }
            break;
        case CinematicCueKind::ActorFace:
            if (const std::optional<GameplayWorldPoint> feet = world.actorFeet(cue.actorIndex))
            {
                std::optional<GameplayWorldPoint> target;

                if (cue.aim == CinematicAim::Point)
                {
                    target = cue.point;
                }
                else if (cue.aim == CinematicAim::Party)
                {
                    target = world.partyEye();
                }
                else
                {
                    target = world.actorFeet(cue.aimActorIndex);
                }

                if (target && (std::abs(target->x - feet->x) > 0.01f || std::abs(target->y - feet->y) > 0.01f))
                {
                    world.faceActor(cue.actorIndex, std::atan2(target->y - feet->y, target->x - feet->x), cue.seconds);
                    m_presentedActors.push_back(cue.actorIndex);
                }
            }
            break;
        case CinematicCueKind::ActorClip:
            world.playActorClip(cue.actorIndex, cue.text, cue.loop);
            m_presentedActors.push_back(cue.actorIndex);
            break;
        case CinematicCueKind::DecorationMove:
            world.moveDecoration(cue.decorationKey, cue.point, cue.seconds);
            m_movedDecorations.emplace_back(cue.decorationKey, cue.point);
            break;
        case CinematicCueKind::Shake:
            m_shake.start(cue.amount, cue.seconds);
            break;
    }
}

void CinematicRuntime::advanceMoves(ICinematicWorld &world)
{
    for (const ActorMove &move : m_moves)
    {
        const float t = std::clamp((m_elapsedSeconds - move.startSeconds) / move.seconds, 0.0f, 1.0f);
        world.placeActor(move.actorIndex, lerp(move.from, move.to, t));
    }

    std::erase_if(m_moves,
        [&](const ActorMove &move) { return m_elapsedSeconds >= move.startSeconds + move.seconds; });
}

void CinematicRuntime::updatePresentation()
{
    const auto ramp =
        [&](float from, float to, float startSeconds, float seconds)
        {
            const float t = seconds > 0.0f ? std::clamp((m_elapsedSeconds - startSeconds) / seconds, 0.0f, 1.0f) : 1.0f;
            return from + (to - from) * t;
        };

    m_fadeAmount = ramp(m_fadeFrom, m_fadeTo, m_fadeStartSeconds, m_fadeSeconds);
    m_letterboxAmount = ramp(m_letterboxFrom, m_letterboxTo, m_letterboxStartSeconds, m_letterboxSeconds);

    if (!m_subtitle.empty() && m_elapsedSeconds >= m_subtitleEndSeconds)
    {
        m_subtitle.clear();
    }
}

void CinematicRuntime::updateCamera(const ICinematicWorld &world)
{
    float shotStart = 0.0f;
    const CinematicShot *pShot = nullptr;

    for (size_t index = 0; index < m_definition->shots.size(); ++index)
    {
        const CinematicShot &shot = m_definition->shots[index];

        if (m_elapsedSeconds < shotStart + shot.durationSeconds)
        {
            pShot = &shot;
            m_shotIndex = index;
            break;
        }

        shotStart += shot.durationSeconds;
    }

    if (pShot == nullptr || pShot->keys.empty())
    {
        m_cameraView.reset();
        return;
    }

    const float local = m_elapsedSeconds - shotStart;
    size_t from = 0;

    while (from + 1 < pShot->keys.size() && pShot->keys[from + 1].atSeconds <= local)
    {
        ++from;
    }

    const size_t to = std::min(from + 1, pShot->keys.size() - 1);
    const CinematicCameraKey &fromKey = pShot->keys[from];
    const CinematicCameraKey &toKey = pShot->keys[to];
    float t = to == from ? 0.0f
        : std::clamp((local - fromKey.atSeconds) / (toKey.atSeconds - fromKey.atSeconds), 0.0f, 1.0f);

    if (pShot->easing == CinematicEasing::Smooth)
    {
        t = t * t * (3.0f - 2.0f * t);
    }

    CinematicCameraView view = {};
    view.eye = lerp(fromKey.position, toKey.position, t);
    std::vector<float> times;
    const bool spline = pShot->easing == CinematicEasing::Spline && to != from;

    if (spline)
    {
        std::vector<GameplayWorldPoint> positions;

        for (const CinematicCameraKey &key : pShot->keys)
        {
            times.push_back(key.atSeconds);
            positions.push_back(key.position);
        }

        view.eye = splineAt(positions, times, from, t);
    }

    const std::optional<GameplayWorldPoint> fromDirection = keyDirection(fromKey, view.eye, world);
    const std::optional<GameplayWorldPoint> toDirection = keyDirection(toKey, view.eye, world);
    std::optional<GameplayWorldPoint> direction;

    if (fromDirection && toDirection)
    {
        direction = normalized(lerp(*fromDirection, *toDirection, t));
    }

    if (spline && fromDirection && toDirection)
    {
        // The aims along the same curve, each key's direction seen from the current eye.
        std::vector<GameplayWorldPoint> directions;

        for (const CinematicCameraKey &key : pShot->keys)
        {
            const std::optional<GameplayWorldPoint> keyAim = keyDirection(key, view.eye, world);
            directions.push_back(keyAim ? *keyAim : *fromDirection);
        }

        direction = normalized(splineAt(directions, times, from, t));
    }

    direction = direction ? direction : (t < 0.5f ? fromDirection : toDirection);

    if (!direction && m_cameraView)
    {
        // The aim is gone (an actor removed): keep the last view's direction.
        view.yawRadians = m_cameraView->yawRadians;
        view.pitchRadians = m_cameraView->pitchRadians;
    }
    else if (direction)
    {
        view.yawRadians = std::atan2(direction->y, direction->x);
        view.pitchRadians = std::clamp(std::asin(std::clamp(direction->z, -1.0f, 1.0f)), -MaxPitchRadians,
            MaxPitchRadians);
    }

    if (fromKey.verticalFovDegrees && toKey.verticalFovDegrees)
    {
        view.verticalFovDegrees = *fromKey.verticalFovDegrees
            + (*toKey.verticalFovDegrees - *fromKey.verticalFovDegrees) * t;
    }
    else
    {
        view.verticalFovDegrees = fromKey.verticalFovDegrees ? fromKey.verticalFovDegrees : toKey.verticalFovDegrees;
    }

    m_cameraView = view;
}

void CinematicRuntime::finish(ICinematicWorld &world)
{
    const uint16_t doneEventId = m_doneEventId;
    // Its actors return to their own animation and facing.
    std::sort(m_presentedActors.begin(), m_presentedActors.end());
    m_presentedActors.erase(std::unique(m_presentedActors.begin(), m_presentedActors.end()), m_presentedActors.end());

    for (const size_t actorIndex : m_presentedActors)
    {
        world.clearActorPresentation(actorIndex);
    }

    stop();

    if (doneEventId != 0)
    {
        world.runEvent(doneEventId);
    }
}
}
