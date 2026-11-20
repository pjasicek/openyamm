#include "game/tables/MonsterShields.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cmath>
#include <exception>

namespace OpenYAMM::Game
{
namespace
{
constexpr const char *ShieldsSchema = "openyamm.shields.v1";
constexpr std::array<const char *, ShieldAttackTierCount> TierNames = {
    "physical", "classic_blaster", "kreegan_energy", "spell"};

bool finiteIn(float value, float minimum, float maximum)
{
    return std::isfinite(value) && value >= minimum && value <= maximum;
}

bool parseColor(const YAML::Node &node, std::array<float, 3> &color, std::string &error)
{
    if (!node.IsSequence() || node.size() != 3)
    {
        error = "color must be [r, g, b] (linear, 0-1)";
        return false;
    }
    for (size_t channel = 0; channel < 3; ++channel)
    {
        color[channel] = node[channel].as<float>();
        if (!finiteIn(color[channel], 0.0f, 4.0f))
        {
            error = "color channels must lie in 0-4";
            return false;
        }
    }
    return true;
}

bool parseGrade(const std::string &name, const YAML::Node &node, ShieldGradeDefinition &grade, std::string &error)
{
    if (!node.IsMap() || !node["rates"].IsMap())
    {
        error = "grade '" + name + "' needs a map with rates: {physical, classic_blaster, kreegan_energy, spell}";
        return false;
    }
    grade.name = name;
    for (const auto &entry : node["rates"])
    {
        const std::string tier = entry.first.as<std::string>();
        const auto found = std::find(TierNames.begin(), TierNames.end(), tier);
        if (found == TierNames.end())
        {
            error = "grade '" + name + "': unknown attack tier '" + tier + "'";
            return false;
        }
        const float rate = entry.second.as<float>();
        if (!finiteIn(rate, 0.0f, 4.0f))
        {
            error = "grade '" + name + "': rate of '" + tier + "' must lie in 0-4";
            return false;
        }
        grade.rates[size_t(found - TierNames.begin())] = rate;
    }
    if (node["color"] && !parseColor(node["color"], grade.color, error))
    {
        error = "grade '" + name + "': " + error;
        return false;
    }
    grade.intensity = node["intensity"].as<float>(1.0f);
    grade.regenSeconds = node["regen_seconds"].as<float>(2.0f);
    if (node["rest_intensity"])
    {
        grade.restIntensity = node["rest_intensity"].as<float>();
    }
    if (!finiteIn(grade.intensity, 0.0f, 8.0f) || !finiteIn(grade.regenSeconds, 0.05f, 600.0f)
        || (grade.restIntensity && !finiteIn(*grade.restIntensity, 0.0f, grade.intensity)))
    {
        error = "grade '" + name + "': intensity must lie in 0-8, rest_intensity in 0-intensity and regen_seconds "
            "in 0.05-600";
        return false;
    }
    grade.hitSound = node["hit_sound"].as<std::string>("");
    grade.breakSound = node["break_sound"].as<std::string>("");
    grade.regenSound = node["regen_sound"].as<std::string>("");
    return true;
}
}

const char *shieldAttackTierName(ShieldAttackTier tier)
{
    return TierNames[std::min(size_t(tier), ShieldAttackTierCount - 1)];
}

std::optional<ShieldAttackTier> parseShieldAttackTier(const std::string &name)
{
    const auto found = std::find(TierNames.begin(), TierNames.end(), name);
    return found != TierNames.end() ? std::optional<ShieldAttackTier>(ShieldAttackTier(found - TierNames.begin()))
        : std::nullopt;
}

bool shieldAttackTierIsEnergy(ShieldAttackTier tier)
{
    return tier == ShieldAttackTier::ClassicBlaster || tier == ShieldAttackTier::KreeganEnergy;
}

bool MonsterShieldTable::loadWorldYaml(const std::string &text, const std::string &packageId, uint32_t idBegin,
    uint32_t idEnd, std::string &error)
{
    const std::string where = "worlds/" + packageId + "/shields.yml: ";
    try
    {
        const YAML::Node root = YAML::Load(text);
        if (!root.IsMap() || root["schema"].as<std::string>("") != ShieldsSchema)
        {
            error = where + "expected schema " + ShieldsSchema;
            return false;
        }

        if (const YAML::Node rules = root["rules"])
        {
            if (m_rulesDeclared)
            {
                error = where + "another world already declares the shield rules";
                return false;
            }
            m_rulesDeclared = true;
            m_exposedEnergyMultiplier = rules["exposed_energy_multiplier"].as<float>(1.5f);
            if (const YAML::Node party = rules["party"])
            {
                m_partyRules.regenDelaySeconds = party["regen_delay_seconds"].as<float>(5.0f);
                m_partyRules.regenSeconds = party["regen_seconds"].as<float>(4.0f);
                m_partyRules.shieldTechExpertDelayReduction =
                    party["shield_tech_expert_delay_reduction"].as<float>(1.0f);
                m_partyRules.emitterBonusPerRank = party["emitter_bonus_per_rank"].as<float>(0.1f);
                m_partyRules.hardenedExposedMultiplier = party["hardened_exposed_multiplier"].as<float>(1.25f);
                m_partyRules.hitSound = party["hit_sound"].as<std::string>("");
                m_partyRules.breakSound = party["break_sound"].as<std::string>("");
                if (const YAML::Node cell = party["shield_cell"])
                {
                    m_partyRules.shieldCellPoints = cell["points"].as<int>(200);
                    m_partyRules.shieldCellSeconds = cell["seconds"].as<float>(60.0f);
                }
                if (const YAML::Node burst = party["shield_burst"])
                {
                    m_partyRules.shieldBurstFraction = burst["refill_fraction"].as<float>(0.5f);
                }
            }
            if (const YAML::Node overload = rules["overload"])
            {
                m_overloadRules.chance = overload["chance"].as<float>(0.1f);
                m_overloadRules.remainingFraction = overload["remaining_fraction"].as<float>(0.5f);
            }
            if (const YAML::Node emp = rules["emp_grenade"])
            {
                m_empGrenadeRules.radius = emp["radius"].as<float>(600.0f);
                m_empGrenadeRules.remainingFraction = emp["remaining_fraction"].as<float>(0.5f);
                m_empGrenadeRules.machineStunSeconds = emp["machine_stun_seconds"].as<float>(2.0f);
            }
            if (!finiteIn(m_exposedEnergyMultiplier, 0.0f, 10.0f)
                || !finiteIn(m_partyRules.regenDelaySeconds, 0.0f, 600.0f)
                || !finiteIn(m_partyRules.regenSeconds, 0.05f, 600.0f)
                || m_partyRules.shieldCellPoints < 0 || m_partyRules.shieldCellPoints > 1000000
                || !finiteIn(m_partyRules.shieldCellSeconds, 0.0f, 3600.0f)
                || !finiteIn(m_partyRules.shieldBurstFraction, 0.0f, 1.0f)
                || !finiteIn(m_overloadRules.chance, 0.0f, 1.0f)
                || !finiteIn(m_overloadRules.remainingFraction, 0.0f, 1.0f)
                || !finiteIn(m_empGrenadeRules.radius, 0.0f, 20000.0f)
                || !finiteIn(m_empGrenadeRules.remainingFraction, 0.0f, 1.0f)
                || !finiteIn(m_empGrenadeRules.machineStunSeconds, 0.0f, 60.0f))
            {
                error = where + "rules out of range";
                return false;
            }
        }

        for (const auto &entry : root["sounds"])
        {
            ShieldSoundDefinition sound;
            sound.name = entry.first.as<std::string>();
            sound.fallback = entry.second.IsMap() ? entry.second["fallback"].as<std::string>("") : "";
            if (findSound(sound.name) != nullptr)
            {
                error = where + "sound '" + sound.name + "' is declared twice";
                return false;
            }
            m_sounds.push_back(sound);
        }

        for (const auto &entry : root["grades"])
        {
            ShieldGradeDefinition grade;
            if (!parseGrade(entry.first.as<std::string>(), entry.second, grade, error))
            {
                error = where + error;
                return false;
            }
            if (std::any_of(m_grades.begin(), m_grades.end(),
                    [&](const ShieldGradeDefinition &other) { return other.name == grade.name; }))
            {
                error = where + "grade '" + grade.name + "' is declared twice";
                return false;
            }
            m_grades.push_back(std::move(grade));
        }

        for (const auto &entry : root["monsters"])
        {
            const int id = entry.first.as<int>();
            const YAML::Node node = entry.second;
            if (id <= 0 || uint32_t(id) < idBegin || uint32_t(id) > idEnd || id > INT16_MAX)
            {
                error = where + "monster " + std::to_string(id) + " lies outside the world's monster id range";
                return false;
            }
            if (m_profiles.contains(int16_t(id)))
            {
                error = where + "monster " + std::to_string(id) + " is listed twice";
                return false;
            }
            MonsterShieldProfile profile;
            profile.monsterId = int16_t(id);
            profile.pool = node.IsMap() ? node["shield"].as<int>(0) : 0;
            const std::string gradeName = node.IsMap() ? node["grade"].as<std::string>("") : "";
            if (profile.pool < 0 || profile.pool > 1000000 || (profile.pool > 0) != !gradeName.empty())
            {
                error = where + "monster " + std::to_string(id) + ": a shield needs a grade and a grade a shield";
                return false;
            }
            if (profile.pool > 0)
            {
                const auto found = std::find_if(m_grades.begin(), m_grades.end(),
                    [&](const ShieldGradeDefinition &grade) { return grade.name == gradeName; });
                if (found == m_grades.end())
                {
                    error = where + "monster " + std::to_string(id) + ": unknown grade '" + gradeName + "'";
                    return false;
                }
                profile.gradeIndex = int(found - m_grades.begin());
                profile.regenDelaySeconds = node["regen_delay_seconds"].as<float>(4.0f);
                profile.regenSeconds = node["regen_seconds"].as<float>(found->regenSeconds);
                if (!finiteIn(profile.regenDelaySeconds, 0.0f, 600.0f)
                    || !finiteIn(profile.regenSeconds, 0.05f, 600.0f))
                {
                    error = where + "monster " + std::to_string(id) + ": regeneration out of range";
                    return false;
                }
            }
            if (node.IsMap())
            {
                profile.energyImmune = node["energy_immune"].as<bool>(false);
                profile.machine = node["machine"].as<bool>(false);
                if (const YAML::Node link = node["link"])
                {
                    profile.linkRadius = link["radius"].as<float>(2560.0f);
                    profile.linkRegenMultiplier = link["regen_multiplier"].as<float>(2.0f);
                    profile.linkDropsOnDeath = link["drop_on_death"].as<bool>(false);
                    if (!finiteIn(profile.linkRadius, 1.0f, 20000.0f)
                        || !finiteIn(profile.linkRegenMultiplier, 0.0f, 20.0f))
                    {
                        error = where + "monster " + std::to_string(id) + ": link radius or multiplier out of range";
                        return false;
                    }
                }
            }
            addProfile(profile);
        }
    }
    catch (const std::exception &exception)
    {
        error = where + exception.what();
        return false;
    }

    for (const ShieldGradeDefinition &grade : m_grades)
    {
        for (const std::string *pSound : {&grade.hitSound, &grade.breakSound, &grade.regenSound})
        {
            if (!pSound->empty() && findSound(*pSound) == nullptr)
            {
                error = where + "grade '" + grade.name + "' names the undeclared sound '" + *pSound + "'";
                return false;
            }
        }
    }
    return true;
}

void MonsterShieldTable::clear()
{
    *this = {};
}

const MonsterShieldProfile *MonsterShieldTable::find(int16_t monsterId) const
{
    if (monsterId < m_minimumMonsterId || monsterId > m_maximumMonsterId)
    {
        return nullptr;
    }
    const auto found = m_profiles.find(monsterId);
    return found != m_profiles.end() ? &found->second : nullptr;
}

const ShieldGradeDefinition *MonsterShieldTable::grade(const MonsterShieldProfile &profile) const
{
    return profile.gradeIndex >= 0 && size_t(profile.gradeIndex) < m_grades.size()
        ? &m_grades[size_t(profile.gradeIndex)] : nullptr;
}

const ShieldSoundDefinition *MonsterShieldTable::findSound(const std::string &name) const
{
    const auto found = std::find_if(m_sounds.begin(), m_sounds.end(),
        [&](const ShieldSoundDefinition &sound) { return sound.name == name; });
    return found != m_sounds.end() ? &*found : nullptr;
}

int MonsterShieldTable::addGrade(const ShieldGradeDefinition &grade)
{
    m_grades.push_back(grade);
    return int(m_grades.size()) - 1;
}

void MonsterShieldTable::addProfile(const MonsterShieldProfile &profile)
{
    m_profiles[profile.monsterId] = profile;
    m_hasLinks = m_hasLinks || profile.linkRadius > 0.0f;
    m_minimumMonsterId = std::min(m_minimumMonsterId, profile.monsterId);
    m_maximumMonsterId = std::max(m_maximumMonsterId, profile.monsterId);
}

ShieldHitResolution resolveMonsterShieldHit(const MonsterShieldTable &table, const MonsterShieldProfile &profile,
    float currentShield, int damage, ShieldAttackTier tier, const ShieldHitModifiers &modifiers)
{
    ShieldHitResolution result;
    const ShieldGradeDefinition *pGrade = table.grade(profile);
    if (damage <= 0)
    {
        return result;
    }
    if (pGrade != nullptr && profile.pool > 0 && currentShield > 0.0f)
    {
        // Nothing passes a raised shield; what it takes beyond its remaining pool is lost, except that a cleaving hit
        // carries half of the damage the broken shield did not need through to the body.
        const float share = std::clamp(modifiers.energyShare, 0.0f, 1.0f);
        const float rate = ((1.0f - share) * pGrade->rates[size_t(tier)]
            + share * pGrade->rates[size_t(ShieldAttackTier::KreeganEnergy)])
            * std::max(0.0f, modifiers.shieldDamageMultiplier);
        const float taken = float(damage) * rate;
        result.absorbed = true;
        result.shieldDamage = std::min(taken, currentShield);
        result.broke = taken >= currentShield;
        if (result.broke && modifiers.cleave && rate > 0.0f && !profile.energyImmune)
        {
            const float leftover = float(damage) - currentShield / rate;
            result.bodyDamage = int(std::lround(std::max(0.0f, leftover) * 0.5f));
            result.cleaved = result.bodyDamage > 0;
            result.absorbed = !result.cleaved;
        }
        return result;
    }
    if (profile.energyImmune && shieldAttackTierIsEnergy(tier))
    {
        return result;
    }
    const float multiplier =
        shieldAttackTierIsEnergy(tier) ? table.exposedEnergyMultiplier() * modifiers.exposedMultiplier : 1.0f;
    result.bodyDamage = int(std::lround(float(damage) * multiplier));
    return result;
}

float regenerateMonsterShield(const MonsterShieldProfile &profile, float currentShield, float secondsSinceDamage,
    float deltaSeconds, float rateMultiplier)
{
    if (profile.pool <= 0 || currentShield >= float(profile.pool) || deltaSeconds <= 0.0f)
    {
        return std::min(currentShield, float(std::max(profile.pool, 0)));
    }
    // Only the part of the step after the delay regenerates.
    const float regenerating = std::min(deltaSeconds, secondsSinceDamage + deltaSeconds - profile.regenDelaySeconds);
    if (regenerating <= 0.0f)
    {
        return currentShield;
    }
    const float rate = float(profile.pool) / std::max(profile.regenSeconds, 0.05f) * std::max(rateMultiplier, 0.0f);
    return std::min(float(profile.pool), currentShield + rate * regenerating);
}
}
