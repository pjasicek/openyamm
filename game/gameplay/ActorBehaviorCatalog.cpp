#include "game/gameplay/ActorBehaviorCatalog.h"

#include "engine/AssetFileSystem.h"
#include "game/tables/MonsterModifiers.h"

#include <yaml-cpp/yaml.h>

#include <cmath>
#include <exception>
#include <numbers>
#include <optional>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr const char *CatalogSchema = "openyamm.actorBehaviors.v1";
constexpr float DegreesToRadians = std::numbers::pi_v<float> / 180.0f;
// Without fire_within_degrees a traversing actor fires once it is this close to facing its target.
constexpr float DefaultFireToleranceDegrees = 6.0f;
constexpr float MaximumTacticDistance = 10240.0f;

// A turret's idle `scan`: {half_width_degrees, degrees_per_second, pause_seconds: [min, max], pitch_degrees,
// hold_seconds}; half_width_degrees and degrees_per_second are required.
bool parseTurretScan(const YAML::Node &node, TurretScanSettings &scan, std::string &error)
{
    if (!node.IsMap() || !node["half_width_degrees"] || !node["degrees_per_second"])
    {
        error = "tactic scan needs half_width_degrees and degrees_per_second";
        return false;
    }

    for (const auto &option : node)
    {
        const std::string key = option.first.as<std::string>();

        if (key != "half_width_degrees" && key != "degrees_per_second" && key != "pause_seconds"
            && key != "pitch_degrees" && key != "hold_seconds")
        {
            error = "unknown tactic scan option " + key;
            return false;
        }
    }

    const float halfWidth = node["half_width_degrees"].as<float>();
    const float rate = node["degrees_per_second"].as<float>();
    const std::vector<float> pause = node["pause_seconds"]
        ? node["pause_seconds"].as<std::vector<float>>() : std::vector<float>{0.8f, 2.4f};
    const float pitch = node["pitch_degrees"].as<float>(0.0f);
    const float hold = node["hold_seconds"].as<float>(3.0f);
    const auto finiteIn = [](float value, float low, float high)
    {
        return std::isfinite(value) && value >= low && value <= high;
    };

    if (!finiteIn(halfWidth, 0.0f, 180.0f) || !finiteIn(rate, 1.0f, 360.0f) || pause.size() != 2
        || !finiteIn(pause[0], 0.0f, 60.0f) || !finiteIn(pause[1], pause[0], 60.0f) || !finiteIn(pitch, 0.0f, 45.0f)
        || !finiteIn(hold, 0.0f, 60.0f))
    {
        error = "tactic scan: half_width_degrees 0-180, degrees_per_second 1-360, pause_seconds [min, max] 0-60, "
            "pitch_degrees 0-45, hold_seconds 0-60";
        return false;
    }

    scan.halfWidthRadians = halfWidth * DegreesToRadians;
    scan.radiansPerSecond = rate * DegreesToRadians;
    scan.pauseMinSeconds = pause[0];
    scan.pauseMaxSeconds = pause[1];
    scan.pitchRadians = pitch * DegreesToRadians;
    scan.holdSeconds = hold;
    return true;
}

// One `tactics` entry: traverse_degrees_per_second, fire_within_degrees, lead_seconds, scan: {...},
// ranged_band: [min, max], post: {leash} and shield_break: {react: fall_back | stagger | climb, max_seconds} (a blink
// on the break is the blink modifier's on_shield_break).
bool parseTactics(const YAML::Node &node, ActorTacticsFacts &tactics, std::string &error)
{
    if (!node.IsMap())
    {
        error = "expected a map of tactic options";
        return false;
    }

    for (const auto &option : node)
    {
        const std::string key = option.first.as<std::string>();

        if (key != "traverse_degrees_per_second" && key != "fire_within_degrees" && key != "ranged_band"
            && key != "post" && key != "scan" && key != "lead_seconds" && key != "shield_break")
        {
            error = "unknown tactic option " + key;
            return false;
        }
    }

    const auto finiteIn = [](float value, float low, float high)
    {
        return std::isfinite(value) && value >= low && value <= high;
    };

    if (node["traverse_degrees_per_second"])
    {
        const float degrees = node["traverse_degrees_per_second"].as<float>();
        const float tolerance = node["fire_within_degrees"].as<float>(DefaultFireToleranceDegrees);

        if (!finiteIn(degrees, 1.0f, 3600.0f) || !finiteIn(tolerance, 0.0f, 180.0f))
        {
            error = "traverse_degrees_per_second must be 1-3600 and fire_within_degrees 0-180";
            return false;
        }

        tactics.traverseRadiansPerSecond = degrees * DegreesToRadians;
        tactics.fireToleranceRadians = tolerance * DegreesToRadians;
    }
    else if (node["fire_within_degrees"] || node["scan"] || node["lead_seconds"])
    {
        error = "fire_within_degrees, scan and lead_seconds require traverse_degrees_per_second";
        return false;
    }

    if (node["scan"] && !parseTurretScan(node["scan"], tactics.scan, error))
    {
        return false;
    }

    if (node["lead_seconds"])
    {
        tactics.leadSeconds = node["lead_seconds"].as<float>();

        if (!finiteIn(tactics.leadSeconds, 0.0f, 2.0f))
        {
            error = "tactic lead_seconds must be 0-2";
            return false;
        }
    }

    if (node["ranged_band"])
    {
        const std::vector<float> band = node["ranged_band"].as<std::vector<float>>();

        if (band.size() != 2 || !finiteIn(band[0], 0.0f, MaximumTacticDistance)
            || !finiteIn(band[1], band[0] + 1.0f, MaximumTacticDistance))
        {
            error = "ranged_band must be [min, max] edge distances with 0 <= min < max";
            return false;
        }

        tactics.rangedMinDistance = band[0];
        tactics.rangedMaxDistance = band[1];
    }

    if (const YAML::Node post = node["post"])
    {
        if (!post.IsMap() || (post.size() > 0 && (post.size() != 1 || !post["leash"])))
        {
            error = "post takes only leash";
            return false;
        }

        tactics.holdPost = true;
        tactics.postLeashRadius = post["leash"].as<float>(0.0f);

        if (!finiteIn(tactics.postLeashRadius, 0.0f, MaximumTacticDistance))
        {
            error = "post leash must be 0-10240";
            return false;
        }
    }

    if (const YAML::Node shieldBreak = node["shield_break"])
    {
        const std::string react = shieldBreak.IsMap() ? shieldBreak["react"].as<std::string>("") : "";

        if (!shieldBreak.IsMap() || (react != "fall_back" && react != "stagger" && react != "climb")
            || (shieldBreak.size() > 1 && (shieldBreak.size() != 2 || !shieldBreak["max_seconds"])))
        {
            error = "shield_break takes react: fall_back, stagger or climb, and max_seconds";
            return false;
        }

        tactics.shieldBreakReaction = react == "stagger" ? ActorShieldBreakReaction::Stagger
            : react == "climb" ? ActorShieldBreakReaction::Climb
            : ActorShieldBreakReaction::FallBack;
        tactics.shieldBreakSeconds = shieldBreak["max_seconds"].as<float>(8.0f);

        if (!finiteIn(tactics.shieldBreakSeconds, 0.1f, 120.0f))
        {
            error = "shield_break max_seconds must be 0.1-120";
            return false;
        }
    }

    return true;
}
}

bool ActorBehaviorCatalog::load(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &worldId,
    std::string &error)
{
    clear();
    m_worldId = worldId;

    if (!loadDocument(assetFileSystem, "engine/behaviors/behaviors.yml", true, error))
    {
        return false;
    }

    if (!worldId.empty() && !loadDocument(assetFileSystem, "worlds/" + worldId + "/behaviors.yml", false, error))
    {
        return false;
    }

    for (const auto &[monsterId, behaviorId] : m_monsterDefaults)
    {
        if (!m_behaviors.contains(behaviorId))
        {
            error = "monster " + std::to_string(monsterId) + " uses unknown actor behaviour: " + behaviorId;
            return false;
        }
    }

    return true;
}

bool ActorBehaviorCatalog::loadDocument(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &virtualPath,
    bool required,
    std::string &error)
{
    const std::optional<std::string> text = assetFileSystem.readTextFile(virtualPath);

    if (!text)
    {
        if (required)
        {
            error = "missing actor behaviour catalogue: " + virtualPath;
            return false;
        }

        return true;
    }

    try
    {
        const YAML::Node root = YAML::Load(*text);

        if (root["schema"].as<std::string>("") != CatalogSchema)
        {
            error = virtualPath + ": expected schema " + CatalogSchema;
            return false;
        }

        const auto readSource =
            [&](const std::string &sourcePath, std::string &source)
            {
                const std::optional<std::string> sourceText = assetFileSystem.readTextFile(sourcePath);

                if (!sourceText)
                {
                    error = virtualPath + ": missing behaviour script " + sourcePath;
                    return false;
                }

                source = *sourceText;
                return true;
            };

        if (root["library"])
        {
            const std::string sourcePath = root["library"].as<std::string>();
            std::string source;

            if (!readSource(sourcePath, source))
            {
                return false;
            }

            setLibrary(sourcePath, source);
        }

        for (const auto &entry : root["behaviors"])
        {
            const std::string id = entry.first.as<std::string>();
            const std::string sourcePath = entry.second.as<std::string>();
            std::string source;

            if (id.empty() || !readSource(sourcePath, source))
            {
                if (error.empty())
                {
                    error = virtualPath + ": behaviour ids must not be empty";
                }

                return false;
            }

            addBehavior(id, sourcePath, source);
        }

        for (const auto &entry : root["monsters"])
        {
            const int monsterId = entry.first.as<int>();

            if (monsterId <= 0 || monsterId > 32767)
            {
                error = virtualPath + ": invalid monster id " + std::to_string(monsterId);
                return false;
            }

            setMonsterDefault(static_cast<int16_t>(monsterId), entry.second.as<std::string>());
        }

        for (const auto &entry : root["tactics"])
        {
            const int monsterId = entry.first.as<int>();
            ActorTacticsFacts tactics = {};
            std::string tacticsError;

            if (monsterId <= 0 || monsterId > 32767)
            {
                error = virtualPath + ": invalid tactics monster id " + std::to_string(monsterId);
                return false;
            }

            if (!parseTactics(entry.second, tactics, tacticsError))
            {
                error = virtualPath + ": tactics of monster " + std::to_string(monsterId) + ": " + tacticsError;
                return false;
            }

            setMonsterTactics(static_cast<int16_t>(monsterId), tactics);
        }
    }
    catch (const std::exception &exception)
    {
        error = virtualPath + ": " + exception.what();
        return false;
    }

    return true;
}

void ActorBehaviorCatalog::clear()
{
    m_worldId.clear();
    m_librarySourcePath.clear();
    m_librarySource.clear();
    m_behaviors.clear();
    m_monsterDefaults.clear();
    m_monsterTactics.clear();
    m_monsterMm9AiProfiles.clear();
}

void ActorBehaviorCatalog::setLibrary(const std::string &sourcePath, const std::string &source)
{
    m_librarySourcePath = sourcePath;
    m_librarySource = source;
}

void ActorBehaviorCatalog::addBehavior(const std::string &id, const std::string &sourcePath, const std::string &source)
{
    m_behaviors[id] = ActorBehaviorDefinition{id, sourcePath, source};
}

void ActorBehaviorCatalog::setMonsterDefault(int16_t monsterId, const std::string &behaviorId)
{
    m_monsterDefaults[monsterId] = behaviorId;
}

const std::string &ActorBehaviorCatalog::worldId() const
{
    return m_worldId;
}

const std::string &ActorBehaviorCatalog::librarySourcePath() const
{
    return m_librarySourcePath;
}

const std::string &ActorBehaviorCatalog::librarySource() const
{
    return m_librarySource;
}

const ActorBehaviorDefinition *ActorBehaviorCatalog::findBehavior(const std::string &id) const
{
    const auto iterator = m_behaviors.find(id);
    return iterator != m_behaviors.end() ? &iterator->second : nullptr;
}

const std::string *ActorBehaviorCatalog::defaultBehaviorForMonster(int16_t monsterId) const
{
    const auto iterator = m_monsterDefaults.find(monsterId);
    return iterator != m_monsterDefaults.end() ? &iterator->second : nullptr;
}

bool ActorBehaviorCatalog::empty() const
{
    return m_behaviors.empty();
}

bool ActorBehaviorCatalog::hasMonsterDefaults() const
{
    return !m_monsterDefaults.empty();
}

void ActorBehaviorCatalog::setMonsterTactics(int16_t monsterId, const ActorTacticsFacts &tactics)
{
    m_monsterTactics[monsterId] = tactics;
}

bool ActorBehaviorCatalog::applyMonsterModifiers(const MonsterModifierTable &modifiers, std::string &error)
{
    for (const auto &[monsterId, set] : modifiers.sets())
    {
        // Kept apart from the tactics: an MM9 profile alone must not give its monster tactics (their turret aim and
        // presentation), so MM9 monsters behave as before until the AI reads it.
        if (set.mm9Ai)
        {
            m_monsterMm9AiProfiles[monsterId] = *set.mm9Ai;
        }

        if (set.skirmisher)
        {
            ActorTacticsFacts &tactics = m_monsterTactics[monsterId];
            tactics.skirmish = true;
            tactics.strafeAttackChance = set.skirmisher->strafeAttackChance;
            tactics.evadeChance = set.skirmisher->evadeChance;
            tactics.evadeSeconds = set.skirmisher->evadeSeconds;
            tactics.backOffSeconds = set.skirmisher->backOffSeconds;
            tactics.tauntChance = set.skirmisher->tauntChance;
            tactics.tauntSeconds = set.skirmisher->tauntSeconds;
        }

        if (set.reposition)
        {
            m_monsterTactics[monsterId].reposition = *set.reposition;
        }

        if (!set.kitesParty)
        {
            continue;
        }

        ActorTacticsFacts &tactics = m_monsterTactics[monsterId];

        if (tactics.keepsRangedBand())
        {
            error = "monster " + std::to_string(monsterId)
                + " has both the kites_party modifier and a tactics ranged_band; keep one";
            return false;
        }

        tactics.rangedMinDistance = set.kitesParty->minDistance;
        tactics.rangedMaxDistance = set.kitesParty->maxDistance;
    }

    return true;
}

const ActorTacticsFacts *ActorBehaviorCatalog::tacticsForMonster(int16_t monsterId) const
{
    const auto iterator = m_monsterTactics.find(monsterId);
    return iterator != m_monsterTactics.end() ? &iterator->second : nullptr;
}

bool ActorBehaviorCatalog::hasTactics() const
{
    return !m_monsterTactics.empty();
}

const Mm9AiProfile *ActorBehaviorCatalog::mm9AiProfileForMonster(int16_t monsterId) const
{
    const auto iterator = m_monsterMm9AiProfiles.find(monsterId);
    return iterator != m_monsterMm9AiProfiles.end() ? &iterator->second : nullptr;
}

bool ActorBehaviorCatalog::hasMm9AiProfiles() const
{
    return !m_monsterMm9AiProfiles.empty();
}
}
