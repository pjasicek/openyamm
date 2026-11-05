#include "game/tables/Mm9MonsterAi.h"

#include <yaml-cpp/yaml.h>

#include <cmath>
#include <exception>

namespace OpenYAMM::Game
{
namespace
{
template <typename Enum, size_t Count>
bool parseName(const std::string &text, const std::array<const char *, Count> &names, Enum &value)
{
    for (size_t index = 0; index < Count; ++index)
    {
        if (text == names[index])
        {
            value = Enum(index);
            return true;
        }
    }

    return false;
}

constexpr std::array<const char *, 8> ArchetypeNames = {
    "crawler", "skirmisher", "ranged_holder", "flier", "swimmer", "turret", "civilian", "guard"};
constexpr std::array<const char *, 3> MovementNames = {"walk", "fly", "swim"};
constexpr std::array<const char *, 3> RangedNames = {"none", "walker", "flier"};
constexpr std::array<const char *, 2> WinceNames = {"low_health", "never"};
constexpr std::array<const char *, 4> DormantUntilNames = {"none", "trigger", "disturbed", "sighted"};
constexpr std::array<const char *, 8> DormantPoseNames = {
    "stand", "lie", "sleep", "hang", "underground", "hidden", "caged", "coffin"};
constexpr std::array<const char *, 3> WanderNames = {"off", "aimless", "path"};
constexpr std::array<const char *, 3> HostilityNames = {"default", "friendly_until_provoked", "hostile_after_event"};
constexpr std::array<const char *, 7> FactionNames = {"none", "monk", "dook", "drangheim", "honk", "training", "guard"};

// The longest distance a placement may give (sight, hearing, leash), in our units.
constexpr float MaximumDistance = 100000.0f;

bool readNumber(const YAML::Node &node, const std::string &key, float minimum, float maximum, float &value,
    std::string &error)
{
    float parsed = 0.0f;

    if (!node.IsScalar() || !YAML::convert<float>::decode(node, parsed) || !std::isfinite(parsed) || parsed < minimum
        || parsed > maximum)
    {
        error = "mm9_ai." + key + " must be a number in " + std::to_string(int(minimum)) + "-"
            + std::to_string(int(maximum));
        return false;
    }

    value = parsed;
    return true;
}

bool readFlag(const YAML::Node &node, const std::string &key, bool &value, std::string &error)
{
    if (!node.IsScalar() || !YAML::convert<bool>::decode(node, value))
    {
        error = "mm9_ai." + key + " must be true or false";
        return false;
    }

    return true;
}

template <typename Enum, size_t Count>
bool readChoice(const YAML::Node &node, const std::string &key, const std::array<const char *, Count> &names,
    Enum &value, std::string &error)
{
    if (node.IsScalar() && parseName(node.as<std::string>(), names, value))
    {
        return true;
    }

    std::string choices;

    for (const char *pName : names)
    {
        choices += choices.empty() ? "" : "|";
        choices += pName;
    }

    error = "mm9_ai." + key + " must be one of " + choices;
    return false;
}

bool readRange(const YAML::Node &node, const std::string &key, float &minimum, float &maximum, std::string &error)
{
    if (!node.IsSequence() || node.size() != 2
        || !readNumber(node[0], key, 0.0f, 3600.0f, minimum, error)
        || !readNumber(node[1], key, 0.0f, 3600.0f, maximum, error)
        || minimum > maximum)
    {
        error = "mm9_ai." + key + " must be [minimum, maximum] seconds";
        return false;
    }

    return true;
}

bool readPoints(const YAML::Node &node, const std::string &key, std::vector<std::array<int32_t, 3>> &points,
    std::string &error)
{
    points.clear();

    if (!node.IsSequence())
    {
        error = "mm9_ai." + key + " must be a list of [x, y, z] points";
        return false;
    }

    for (const YAML::Node &point : node)
    {
        std::array<int32_t, 3> value = {};

        if (!point.IsSequence() || point.size() != 3 || !YAML::convert<int32_t>::decode(point[0], value[0])
            || !YAML::convert<int32_t>::decode(point[1], value[1])
            || !YAML::convert<int32_t>::decode(point[2], value[2]))
        {
            error = "mm9_ai." + key + " must be a list of [x, y, z] points";
            return false;
        }

        points.push_back(value);
    }

    return true;
}

// The placement script's profile fields (scene mm9_ai.profile): the generated fields that differ from its row's.
bool readProfile(const YAML::Node &node, Mm9AiPlacementProfile &profile, std::string &error)
{
    if (!node.IsMap())
    {
        error = "mm9_ai.profile must be a map";
        return false;
    }

    const auto flag = [&](const YAML::Node &value, const std::string &key, std::optional<bool> &field)
    {
        bool parsed = false;

        if (!readFlag(value, "profile." + key, parsed, error))
        {
            return false;
        }

        field = parsed;
        return true;
    };
    const auto seconds = [&](const YAML::Node &value, const std::string &key, std::optional<float> &field)
    {
        float parsed = 0.0f;

        if (!readNumber(value, "profile." + key, 0.0f, 600.0f, parsed, error))
        {
            return false;
        }

        field = parsed;
        return true;
    };

    for (const auto &entry : node)
    {
        const std::string key = entry.first.as<std::string>();
        const YAML::Node &value = entry.second;
        bool ok = true;

        if (key == "archetype")
        {
            Mm9AiArchetype archetype = Mm9AiArchetype::Skirmisher;
            ok = readChoice(value, "profile.archetype", ArchetypeNames, archetype, error);
            profile.archetype = archetype;
        }
        else if (key == "ranged")
        {
            Mm9AiRanged ranged = Mm9AiRanged::None;
            ok = readChoice(value, "profile.ranged", RangedNames, ranged, error);
            profile.ranged = ranged;
        }
        else if (key == "ranged_weapon")
        {
            ok = flag(value, key, profile.rangedWeapon);
        }
        else if (key == "guard_refuge")
        {
            ok = flag(value, key, profile.guardRefuge);
        }
        else if (key == "throttle")
        {
            ok = flag(value, key, profile.throttle);
        }
        else if (key == "always_evade")
        {
            ok = flag(value, key, profile.alwaysEvade);
        }
        else if (key == "evade_min_seconds")
        {
            ok = seconds(value, key, profile.evadeMinSeconds);
        }
        else if (key == "evade_max_seconds")
        {
            ok = seconds(value, key, profile.evadeMaxSeconds);
        }
        else if (key == "melee_window_seconds")
        {
            ok = seconds(value, key, profile.meleeWindowSeconds);
        }
        else if (key == "spawn_in")
        {
            ok = flag(value, key, profile.spawnIn);
        }
        else if (key == "death_spawn")
        {
            float monsterId = 0.0f;
            ok = readNumber(value, "profile.death_spawn", 0.0f, 32767.0f, monsterId, error);
            profile.deathSpawnMonsterId = int16_t(monsterId);
        }
        else if (key == "passive")
        {
            ok = readFlag(value, "profile.passive", profile.passive, error);
        }
        else if (key == "skirmisher")
        {
            Mm9AiFootwork footwork = {};

            if (value.IsMap())
            {
                footwork.enabled = true;

                for (const auto &parameter : value)
                {
                    const std::string name = parameter.first.as<std::string>();
                    float *pValue = name == "strafe_attack_chance" ? &footwork.strafeAttackChance
                        : name == "evade_chance" ? &footwork.evadeChance
                        : name == "taunt_seconds" ? &footwork.tauntSeconds : nullptr;

                    if (pValue == nullptr)
                    {
                        error = "mm9_ai.profile.skirmisher has no key '" + name + "'";
                        return false;
                    }

                    if (!readNumber(parameter.second, "profile.skirmisher." + name, 0.0f,
                            name == "taunt_seconds" ? 10.0f : 1.0f, *pValue, error))
                    {
                        return false;
                    }
                }
            }
            else
            {
                bool enabled = false;
                ok = readFlag(value, "profile.skirmisher", enabled, error) && !enabled;

                if (!ok && error.empty())
                {
                    error = "mm9_ai.profile.skirmisher must be false or {strafe_attack_chance, evade_chance, "
                            "taunt_seconds}";
                }
            }

            profile.footwork = footwork;
        }
        else
        {
            error = "mm9_ai.profile has no key '" + key + "'";
            return false;
        }

        if (!ok)
        {
            return false;
        }
    }

    if (profile.evadeMinSeconds.value_or(0.0f) > profile.evadeMaxSeconds.value_or(600.0f))
    {
        error = "mm9_ai.profile.evade_min_seconds must not exceed evade_max_seconds";
        return false;
    }

    return true;
}
}

bool Mm9AiPlacementRecord::operator==(const Mm9AiPlacementRecord &other) const
{
    const Mm9AiPlacement &a = settings;
    const Mm9AiPlacement &b = other.settings;
    return a.sight == b.sight && a.hearing == b.hearing && a.runawayChance == b.runawayChance
        && a.rangedType == b.rangedType && a.canBeResurrected == b.canBeResurrected && a.wander == b.wander
        && a.wanderLeash == b.wanderLeash && a.wanderWaitMinSeconds == b.wanderWaitMinSeconds
        && a.wanderWaitMaxSeconds == b.wanderWaitMaxSeconds && a.wanderTimeMinSeconds == b.wanderTimeMinSeconds
        && a.wanderTimeMaxSeconds == b.wanderTimeMaxSeconds && a.pathRandom == b.pathRandom
        && a.dormantUntil == b.dormantUntil && a.dormantPose == b.dormantPose && a.hostility == b.hostility
        && a.faction == b.faction && a.summoner == b.summoner && a.startsDead == b.startsDead && a.boss == b.boss
        && a.profile == b.profile
        && pathPoints == other.pathPoints && summonPoints == other.summonPoints && hidingPlaces == other.hidingPlaces
        && summonClass == other.summonClass
        && script == other.script && scriptParams == other.scriptParams;
}

const Mm9AiProfile &mm9StandInCivilianProfile()
{
    // MM9's townsfolk rows (Commoner ... Townsfolk, NPCbase.scr): walk 75 LT/s, run 150 LT/s, AttackRange 36, the
    // default AlertRadius; Always Wince? 1.
    static const Mm9AiProfile profile = []()
    {
        Mm9AiProfile civilian = {};
        civilian.archetype = Mm9AiArchetype::Civilian;
        civilian.wince = Mm9AiWince::Never;
        civilian.attackReach = 108.0f;
        civilian.meleeSweep = 154.0f;
        civilian.walkSpeed = 192.0f;
        civilian.runSpeed = 384.0f;
        civilian.lungeVelocity = 256.0f;
        civilian.guardRefuge = true;
        return civilian;
    }();
    return profile;
}

bool mm9SpawnedWithParam(const Mm9AiPlacementRecord &record)
{
    if (!record.script.empty())
    {
        return false;
    }

    const size_t begin = record.scriptParams.find_first_not_of(' ');
    return begin != std::string::npos && record.scriptParams[begin] == '1'
        && (begin + 1 == record.scriptParams.size() || record.scriptParams[begin + 1] == ' ');
}

Mm9AiProfile placedMm9AiProfile(const Mm9AiProfile &row, const Mm9AiPlacement &placement)
{
    Mm9AiProfile profile = row;
    const Mm9AiPlacementProfile &script = placement.profile;
    profile.archetype = script.archetype.value_or(profile.archetype);
    profile.ranged = script.ranged.value_or(profile.ranged);
    profile.rangedWeapon = script.rangedWeapon.value_or(profile.rangedWeapon);
    profile.guardRefuge = script.guardRefuge.value_or(profile.guardRefuge);
    profile.throttle = script.throttle.value_or(profile.throttle);
    profile.alwaysEvade = script.alwaysEvade.value_or(profile.alwaysEvade);
    profile.evadeMinSeconds = script.evadeMinSeconds.value_or(profile.evadeMinSeconds);
    profile.evadeMaxSeconds = script.evadeMaxSeconds.value_or(profile.evadeMaxSeconds);
    profile.meleeWindowSeconds = script.meleeWindowSeconds.value_or(profile.meleeWindowSeconds);
    profile.spawnIn = script.spawnIn.value_or(profile.spawnIn);
    profile.deathSpawnMonsterId = script.deathSpawnMonsterId.value_or(profile.deathSpawnMonsterId);
    profile.passive = profile.passive || script.passive;

    if (placement.dormantUntil != Mm9AiDormantUntil::None)
    {
        profile.dormantUntil = placement.dormantUntil;
        profile.dormantPose = placement.dormantPose;
    }

    const bool walker = profile.archetype == Mm9AiArchetype::Crawler
        || profile.archetype == Mm9AiArchetype::Skirmisher;

    if (placement.rangedType == 2 && walker && profile.ranged == Mm9AiRanged::Walker)
    {
        profile.archetype = Mm9AiArchetype::RangedHolder;
    }

    return profile;
}

const char *mm9AiArchetypeName(Mm9AiArchetype archetype)
{
    return ArchetypeNames[size_t(archetype)];
}

bool parseMm9AiArchetype(const std::string &text, Mm9AiArchetype &archetype)
{
    return parseName(text, ArchetypeNames, archetype);
}

bool parseMm9AiMovement(const std::string &text, Mm9AiMovement &movement)
{
    return parseName(text, MovementNames, movement);
}

bool parseMm9AiRanged(const std::string &text, Mm9AiRanged &ranged)
{
    return parseName(text, RangedNames, ranged);
}

bool parseMm9AiWince(const std::string &text, Mm9AiWince &wince)
{
    return parseName(text, WinceNames, wince);
}

bool parseMm9AiDormantUntil(const std::string &text, Mm9AiDormantUntil &until)
{
    return parseName(text, DormantUntilNames, until);
}

bool parseMm9AiDormantPose(const std::string &text, Mm9AiDormantPose &pose)
{
    return parseName(text, DormantPoseNames, pose);
}

bool parseMm9AiPlacementNode(const YAML::Node &node, Mm9AiPlacementRecord &record, std::string &error)
{
    record = {};

    if (!node.IsMap())
    {
        error = "mm9_ai must be a map";
        return false;
    }

    Mm9AiPlacement &settings = record.settings;

    try
    {
        for (const auto &entry : node)
        {
            const std::string key = entry.first.as<std::string>();
            const YAML::Node &value = entry.second;
            bool ok = true;

            if (key == "sight")
            {
                ok = readNumber(value, key, 0.0f, MaximumDistance, settings.sight, error);
            }
            else if (key == "hearing")
            {
                ok = readNumber(value, key, 0.0f, MaximumDistance, settings.hearing, error);
            }
            else if (key == "runaway_chance")
            {
                ok = readNumber(value, key, 0.0f, 1.0f, settings.runawayChance, error);
            }
            else if (key == "ranged_type")
            {
                float type = 1.0f;
                ok = readNumber(value, key, 1.0f, 2.0f, type, error) && (type == 1.0f || type == 2.0f);
                settings.rangedType = uint8_t(type);

                if (!ok && error.empty())
                {
                    error = "mm9_ai.ranged_type must be 1 or 2";
                }
            }
            else if (key == "can_be_resurrected")
            {
                ok = readFlag(value, key, settings.canBeResurrected, error);
            }
            else if (key == "wander")
            {
                ok = readChoice(value, key, WanderNames, settings.wander, error);
            }
            else if (key == "wander_leash")
            {
                ok = readNumber(value, key, 0.0f, MaximumDistance, settings.wanderLeash, error);
            }
            else if (key == "wander_wait")
            {
                ok = readRange(value, key, settings.wanderWaitMinSeconds, settings.wanderWaitMaxSeconds, error);
            }
            else if (key == "wander_time")
            {
                ok = readRange(value, key, settings.wanderTimeMinSeconds, settings.wanderTimeMaxSeconds, error);
            }
            else if (key == "hiding_places")
            {
                ok = readPoints(value, key, record.hidingPlaces, error);
            }
            else if (key == "path")
            {
                ok = readPoints(value, key, record.pathPoints, error);
            }
            else if (key == "path_random")
            {
                ok = readFlag(value, key, settings.pathRandom, error);
            }
            else if (key == "dormant")
            {
                ok = value.IsMap() && value["until"]
                    && readChoice(value["until"], "dormant.until", DormantUntilNames, settings.dormantUntil, error)
                    && (!value["pose"]
                        || readChoice(value["pose"], "dormant.pose", DormantPoseNames, settings.dormantPose, error))
                    && settings.dormantUntil != Mm9AiDormantUntil::None;

                if (!ok && error.empty())
                {
                    error = "mm9_ai.dormant must be {until: trigger|disturbed|sighted, pose: ...}";
                }
            }
            else if (key == "hostility")
            {
                ok = readChoice(value, key, HostilityNames, settings.hostility, error);
            }
            else if (key == "faction")
            {
                ok = readChoice(value, key, FactionNames, settings.faction, error);
            }
            else if (key == "summon")
            {
                ok = value.IsMap() && (!value["points"] || readPoints(value["points"], "summon.points",
                    record.summonPoints, error));

                if (ok && value["class"])
                {
                    record.summonClass = value["class"].as<std::string>();
                }

                if (!ok && error.empty())
                {
                    error = "mm9_ai.summon must be {class: <MM9 class>, points: [[x, y, z], ...]}";
                }

                settings.summoner = ok;
            }
            else if (key == "starts_dead")
            {
                ok = readFlag(value, key, settings.startsDead, error);
            }
            else if (key == "boss")
            {
                ok = readFlag(value, key, settings.boss, error);
            }
            else if (key == "profile")
            {
                ok = readProfile(value, settings.profile, error);
            }
            else if (key == "script")
            {
                record.script = value.as<std::string>();
            }
            else if (key == "script_params")
            {
                record.scriptParams = value.as<std::string>();
            }
            else
            {
                error = "mm9_ai has no key '" + key + "'";
                return false;
            }

            if (!ok)
            {
                return false;
            }
        }
    }
    catch (const std::exception &exception)
    {
        error = std::string("mm9_ai: ") + exception.what();
        return false;
    }

    if (settings.wander == Mm9AiWanderMode::Path && record.pathPoints.size() < 2)
    {
        error = "mm9_ai.wander path needs a path of at least two points";
        return false;
    }

    return true;
}
}
