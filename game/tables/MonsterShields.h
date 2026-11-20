#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
// What a hit is to an energy shield (design/kreegan_world/COMBAT.md, "Shields: batter them down first").
enum class ShieldAttackTier : uint8_t
{
    // Classic weapons, bows and unarmed blows; monster Phys attacks.
    Physical,
    // The party's Ancient blasters (Blaster skill).
    ClassicBlaster,
    // Kreegan guns and blades (Energy Guns items, EnergyBlade weapons); monster Ener attacks.
    KreeganEnergy,
    // Spells and wands of every school, elemental monster attacks, reflected and trap damage.
    Spell,
};
constexpr size_t ShieldAttackTierCount = 4;

const char *shieldAttackTierName(ShieldAttackTier tier);
// physical, classic_blaster, kreegan_energy or spell.
std::optional<ShieldAttackTier> parseShieldAttackTier(const std::string &name);
// Energy weapons take the exposed multiplier against a body with no raised shield.
bool shieldAttackTierIsEnergy(ShieldAttackTier tier);

struct ShieldGradeDefinition
{
    std::string name;
    // Share of an attack's damage that a raised shield takes, per ShieldAttackTier (the rest is not passed on).
    std::array<float, ShieldAttackTierCount> rates = {};
    // Linear RGB of the shell drawn over the model, and its strength.
    std::array<float, 3> color = {1.0f, 0.4f, 0.8f};
    float intensity = 1.0f;
    // Its strength while raised and untouched (rest_intensity): a faint rim; the full intensity shows on a hit, the
    // raise and the break. Unset: the intensity throughout.
    std::optional<float> restIntensity;
    // Regeneration from empty to full once it starts, unless the monster sets its own.
    float regenSeconds = 2.0f;
    // Names in `sounds` played when a raised shield is hit, when it breaks and when it comes back up.
    std::string hitSound;
    std::string breakSound;
    std::string regenSound;
};

// A placeholder sound: the game plays `name` (a file of that name in a world's or the engine's audio folder, found
// by the sound catalogue) and, while no such file exists, `fallback` (another sound name; empty is silent).
struct ShieldSoundDefinition
{
    std::string name;
    std::string fallback;
};

struct MonsterShieldProfile
{
    int16_t monsterId = 0;
    // Shield pool; 0 is a monster without a shield that still follows the shield rules (its body is exposed).
    int pool = 0;
    // Index into MonsterShieldTable::grades(); -1 without a pool.
    int gradeIndex = -1;
    // Seconds without damage before a lowered or broken shield regenerates.
    float regenDelaySeconds = 4.0f;
    // Seconds from empty to full once it regenerates.
    float regenSeconds = 2.0f;
    // The body takes nothing from energy weapons (classic blasters and Kreegan energy): Hesper's Glassbacks.
    bool energyImmune = false;
    // A machine: an EMP grenade stuns it.
    bool machine = false;
    // A shield link (an Overseer's): while it lives, allied shielded actors within linkRadius (itself included)
    // regenerate x linkRegenMultiplier; with linkDropsOnDeath its death breaks their raised shields. 0: no link.
    float linkRadius = 0.0f;
    float linkRegenMultiplier = 2.0f;
    bool linkDropsOnDeath = false;
};

// Energy Blades Grandmaster: each hit on a raised shield may cut it to remainingFraction of what is left.
struct ShieldOverloadRules
{
    float chance = 0.1f;
    float remainingFraction = 0.5f;
};

// The EMP grenade (use action throwEmpGrenade): every hostile shield within radius of the party keeps
// remainingFraction of what is left, and machines are stunned.
struct EmpGrenadeRules
{
    float radius = 600.0f;
    float remainingFraction = 0.5f;
    float machineStunSeconds = 2.0f;
};

// The party's personal shields (fed by items' personal_shield and the Shield Tech skill).
struct PartyShieldRules
{
    float regenDelaySeconds = 5.0f;
    float regenSeconds = 4.0f;
    // Shield Tech Expert shortens the delay; each Shield Tech rank adds this share to an emitter's pool.
    float shieldTechExpertDelayReduction = 1.0f;
    float emitterBonusPerRank = 0.1f;
    // Shield Tech Grandmaster: the exposed multiplier on its holder's body.
    float hardenedExposedMultiplier = 1.25f;
    std::string hitSound;
    std::string breakSound;
    // Shield Cell (use action useShieldCell): refills the member's shield; a member without one gets a temporary
    // shield of shieldCellPoints for shieldCellSeconds. Shield Burst Cell (useShieldBurst): every member's shield gains
    // shieldBurstFraction of its pool.
    int shieldCellPoints = 200;
    float shieldCellSeconds = 60.0f;
    float shieldBurstFraction = 0.5f;
};

// What a party weapon's tech skill adds to its hit against a shielded monster (Energy Guns and Energy Blades
// masteries, the weapon's ShieldDamage<percent> flag): the raised shield takes shieldDamageMultiplier times its rate;
// an exposed body takes exposedMultiplier times the world's exposed multiplier; cleave lets half the damage left after
// a shield breaks reach the body. The defaults change nothing.
struct ShieldHitModifiers
{
    float shieldDamageMultiplier = 1.0f;
    float exposedMultiplier = 1.0f;
    bool cleave = false;
    // This share of the hit strikes a raised shield as Kreegan energy, the rest as its own tier (the Arc Coupler on
    // ordinary weapons, the Lattice Resonator on spells).
    float energyShare = 0.0f;
};

// Outcome of one hit on a monster with a shield profile.
struct ShieldHitResolution
{
    // Damage the raised shield takes (overflow beyond its remaining pool is lost).
    float shieldDamage = 0.0f;
    // Damage that reaches the body, after the exposed multiplier.
    int bodyDamage = 0;
    // A raised shield took the hit: the body takes nothing and does not react.
    bool absorbed = false;
    bool broke = false;
    // The hit broke the shield and cleaved through (ShieldHitModifiers::cleave): bodyDamage is set, the body reacts.
    bool cleaved = false;
};

// Energy shields of monsters, from the worlds' shields.yml (schema openyamm.shields.v1). Only monsters listed there
// follow the shield rules; every other monster is untouched.
class MonsterShieldTable
{
public:
    // Adds one world's file; its monster ids must lie in [idBegin, idEnd] (the world's monster id range).
    bool loadWorldYaml(const std::string &text, const std::string &packageId, uint32_t idBegin, uint32_t idEnd,
        std::string &error);
    void clear();
    bool empty() const
    {
        return m_profiles.empty();
    }
    const MonsterShieldProfile *find(int16_t monsterId) const;
    const ShieldGradeDefinition *grade(const MonsterShieldProfile &profile) const;
    const std::vector<ShieldGradeDefinition> &grades() const
    {
        return m_grades;
    }
    const ShieldSoundDefinition *findSound(const std::string &name) const;
    float exposedEnergyMultiplier() const
    {
        return m_exposedEnergyMultiplier;
    }
    const PartyShieldRules &partyRules() const
    {
        return m_partyRules;
    }
    const ShieldOverloadRules &overloadRules() const
    {
        return m_overloadRules;
    }
    const EmpGrenadeRules &empGrenadeRules() const
    {
        return m_empGrenadeRules;
    }
    // Some monster links its allies' shields (MonsterShieldProfile::linkRadius).
    bool hasLinks() const
    {
        return m_hasLinks;
    }
    int16_t minimumMonsterId() const
    {
        return m_minimumMonsterId;
    }
    int16_t maximumMonsterId() const
    {
        return m_maximumMonsterId;
    }

    // Test and tool setup without YAML.
    int addGrade(const ShieldGradeDefinition &grade);
    void addProfile(const MonsterShieldProfile &profile);
    void setExposedEnergyMultiplier(float multiplier)
    {
        m_exposedEnergyMultiplier = multiplier;
    }

private:
    std::vector<ShieldGradeDefinition> m_grades;
    std::vector<ShieldSoundDefinition> m_sounds;
    std::unordered_map<int16_t, MonsterShieldProfile> m_profiles;
    float m_exposedEnergyMultiplier = 1.5f;
    PartyShieldRules m_partyRules;
    ShieldOverloadRules m_overloadRules;
    EmpGrenadeRules m_empGrenadeRules;
    bool m_rulesDeclared = false;
    bool m_hasLinks = false;
    int16_t m_minimumMonsterId = INT16_MAX;
    int16_t m_maximumMonsterId = INT16_MIN;
};

// One hit against a monster with a shield profile whose shield holds currentShield (0: down or none). A raised shield
// takes damage x its grade's rate for the tier and the body nothing; otherwise the body takes the damage, energy
// tiers x the exposed multiplier (nothing on an energy-immune body).
ShieldHitResolution resolveMonsterShieldHit(const MonsterShieldTable &table, const MonsterShieldProfile &profile,
    float currentShield, int damage, ShieldAttackTier tier, const ShieldHitModifiers &modifiers = {});
// The shield after deltaSeconds, given the seconds since the last damage before the step (regeneration starts once
// they pass the profile's delay); rateMultiplier speeds it up (a shield link).
float regenerateMonsterShield(const MonsterShieldProfile &profile, float currentShield, float secondsSinceDamage,
    float deltaSeconds, float rateMultiplier = 1.0f);
}
