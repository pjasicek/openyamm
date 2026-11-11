#include "game/gameplay/GameplayActorService.h"

#include "game/gameplay/PartyHostileAlert.h"
#include "game/party/SpellIds.h"
#include "game/tables/MonsterTable.h"
#include "game/tables/SpellTable.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
constexpr float HostilityCloseRange = 1024.0f;
constexpr float HostilityShortRange = 2560.0f;
constexpr float HostilityMediumRange = 5120.0f;
constexpr float HostilityLongRange = GameplayActorService::MaximumPartyEngagementRange;

float minutesToSeconds(float minutes)
{
    return minutes * 60.0f;
}

float hoursToSeconds(float hours)
{
    return hours * 3600.0f;
}

float hostilityRangeForRelation(int relation)
{
    switch (relation)
    {
        case 1:
            return HostilityCloseRange;
        case 2:
            return HostilityShortRange;
        case 3:
            return HostilityMediumRange;
        case 4:
            return HostilityLongRange;
        default:
            return 0.0f;
    }
}

bool actorCanEngageActorTarget(
    const MonsterTable *pMonsterTable,
    const GameplayActorTargetPolicyState &actor,
    const GameplayActorTargetPolicyState &target)
{
    if (pMonsterTable == nullptr)
    {
        return false;
    }

    const MonsterTable::MonsterStatsEntry *pStats = pMonsterTable->findStatsById(actor.monsterId);

    if (pStats == nullptr)
    {
        return false;
    }

    const bool hasRangedCapability =
        pStats->canFly
        || pStats->attack1HasMissile
        || pStats->attack2HasMissile
        || pStats->hasSpell1
        || pStats->hasSpell2;

    if (hasRangedCapability)
    {
        return true;
    }

    const float verticalReach =
        static_cast<float>(std::max<uint16_t>(std::max(actor.height, target.height), 160u));
    return target.preciseZ <= actor.preciseZ + verticalReach;
}

bool canApplyMmergeStatusSpell(uint32_t skillLevel, SkillMastery skillMastery, int spellResistance)
{
    if (spellResistance >= 200)
    {
        return false;
    }

    const double masteryBonus = static_cast<double>(std::max(0, static_cast<int>(skillMastery))) * 2.5;
    return 100.0 + static_cast<double>(skillLevel) + masteryBonus > static_cast<double>(spellResistance);
}

uint32_t mixActorDecisionSeed(uint32_t actorId, uint32_t counter, uint32_t salt)
{
    return static_cast<uint32_t>(actorId + 1) * 1103515245u
        + counter * 2654435761u
        + salt;
}

float actorDecisionUnitFloat(uint32_t actorId, uint32_t counter, uint32_t salt)
{
    const uint32_t seed = mixActorDecisionSeed(actorId, counter, salt);
    return static_cast<float>(seed & 0xffffu) / 65535.0f;
}

float actorDecisionRange(
    uint32_t actorId,
    uint32_t counter,
    uint32_t salt,
    float minimumValue,
    float maximumValue)
{
    return minimumValue + (maximumValue - minimumValue) * actorDecisionUnitFloat(actorId, counter, salt);
}

}

void GameplayActorService::bindTables(const MonsterTable *pMonsterTable, const SpellTable *pSpellTable)
{
    m_pMonsterTable = pMonsterTable;
    m_pSpellTable = pSpellTable;
}

void GameplayActorService::setPartyEngagementRange(float range)
{
    m_partyEngagementRange = range;
}

float GameplayActorService::configuredPartyEngagementRange() const
{
    return m_partyEngagementRange;
}

void GameplayActorService::setWorldPartyHitReach(std::optional<float> reach)
{
    m_worldPartyHitReach = reach;
}

float GameplayActorService::partyHitReach() const
{
    return std::min(PartyYellowAlertDistance, m_worldPartyHitReach.value_or(PartyYellowAlertDistance));
}

void GameplayActorService::setMm9PartyAwareness(const Mm9PartyAwareness &awareness)
{
    m_mm9PartyAwareness = awareness;
}

const Mm9PartyAwareness &GameplayActorService::mm9PartyAwareness() const
{
    return m_mm9PartyAwareness;
}

void GameplayActorService::setMeleeVerticalReach(float share)
{
    m_meleeVerticalReach = share;
}

void GameplayActorService::setLevelRadiusLimit(float limit)
{
    m_levelRadiusLimit = limit;
}

void GameplayActorService::setFriendlyActorsBlockParty(bool enabled)
{
    m_friendlyActorsBlockParty = enabled;
}

bool GameplayActorService::actorBlocksPartyMovement(
    bool hostileToParty,
    GameplayActorControlMode controlMode) const
{
    if (hostileToParty)
    {
        return true;
    }

    return m_friendlyActorsBlockParty && !isPartyControlledActor(controlMode);
}

bool GameplayActorService::meleeReachesVertically(float share, float attackerFootZ, float attackerHeight,
    float targetFootZ, float targetHeight)
{
    if (share <= 0.0f)
    {
        return true;
    }

    const float lowerHeight = targetFootZ >= attackerFootZ ? attackerHeight : targetHeight;
    return std::abs(targetFootZ - attackerFootZ) <= std::max(MinimumMeleeVerticalReach, share * lowerHeight);
}

bool GameplayActorService::isBound() const
{
    return m_pMonsterTable != nullptr && m_pSpellTable != nullptr;
}

bool GameplayActorService::actorLooksUndead(int16_t monsterId) const
{
    if (m_pMonsterTable == nullptr)
    {
        return false;
    }

    const MonsterTable::MonsterStatsEntry *pStats = m_pMonsterTable->findStatsById(monsterId);
    return pStats != nullptr && pStats->hasKind(MonsterKind::Undead);
}

int16_t GameplayActorService::relationMonsterId(int16_t monsterId, uint32_t allyMonsterType) const
{
    if (allyMonsterType == 0)
    {
        return monsterId;
    }

    const uint32_t representativeMonsterId = (allyMonsterType - 1u) * 3u + 1u;

    if (representativeMonsterId > 0x7fffu)
    {
        return monsterId;
    }

    return int16_t(representativeMonsterId);
}

GameplayActorService::DirectSpellImpactResult GameplayActorService::resolveDirectSpellImpact(
    uint32_t spellId,
    uint32_t skillLevel,
    int baseDamage,
    bool actorLooksUndead) const
{
    DirectSpellImpactResult result = {};

    if (m_pSpellTable == nullptr)
    {
        return result;
    }

    const SpellEntry *pSpellEntry = m_pSpellTable->findById(static_cast<int>(spellId));

    if (pSpellEntry == nullptr)
    {
        return result;
    }

    const SpellId resolvedSpellId = spellIdFromValue(spellId);
    const std::string &spellName = pSpellEntry->normalizedName;

    if (resolvedSpellId == SpellId::Implosion
        || resolvedSpellId == SpellId::Blades
        || resolvedSpellId == SpellId::Sunray)
    {
        result.disposition = DirectSpellImpactDisposition::ApplyDamage;
        result.damage = std::max(1, baseDamage);

        if (resolvedSpellId == SpellId::Implosion)
        {
            result.visualKind = DirectSpellImpactVisualKind::ActorCenter;
            result.centerVisual = true;
        }
        else if (resolvedSpellId == SpellId::Sunray)
        {
            result.visualKind = DirectSpellImpactVisualKind::ActorUpperBody;
        }

        return result;
    }

    if (resolvedSpellId == SpellId::SpiritLash
        || resolvedSpellId == SpellId::PrismaticLight
        || resolvedSpellId == SpellId::SoulDrinker
        || resolvedSpellId == SpellId::Lifedrain)
    {
        result.disposition = DirectSpellImpactDisposition::ApplyDamage;
        result.visualKind = DirectSpellImpactVisualKind::ActorUpperBody;
        result.damage = std::max(1, baseDamage);
        return result;
    }

    if (resolvedSpellId == SpellId::Inferno)
    {
        result.disposition = DirectSpellImpactDisposition::ApplyDamage;
        result.visualKind = DirectSpellImpactVisualKind::ActorUpperBody;
        result.damage = std::max(1, baseDamage);
        result.preferImpactObject = false;
        return result;
    }

    // The share of the target's hit points comes from the rules (CombatRules::spellDamageOnTarget) as baseDamage.
    if (spellName == "mass distortion")
    {
        result.disposition = DirectSpellImpactDisposition::ApplyDamage;
        result.visualKind = DirectSpellImpactVisualKind::ActorCenter;
        result.damage = std::max(1, baseDamage);
        return result;
    }

    if (spellName == "destroy undead")
    {
        if (!actorLooksUndead)
        {
            result.disposition = DirectSpellImpactDisposition::Rejected;
            return result;
        }

        result.disposition = DirectSpellImpactDisposition::ApplyDamage;
        result.damage = std::max(1, baseDamage);
        return result;
    }

    if (spellName == "light bolt")
    {
        result.disposition = DirectSpellImpactDisposition::ApplyDamage;
        result.damage = std::max(1, baseDamage);

        if (actorLooksUndead)
        {
            result.damage *= 2;
        }

        return result;
    }

    return result;
}

std::optional<bx::Vec3> GameplayActorService::spellPushVelocity(
    uint32_t spellId,
    uint32_t skillLevel,
    float actorX,
    float actorY,
    float sourceX,
    float sourceY)
{
    const SpellId resolvedSpellId = spellIdFromValue(spellId);

    if (resolvedSpellId != SpellId::Fear && resolvedSpellId != SpellId::WingBuffet)
    {
        return std::nullopt;
    }

    const float deltaX = actorX - sourceX;
    const float deltaY = actorY - sourceY;
    const float horizontalLength = std::sqrt(deltaX * deltaX + deltaY * deltaY);

    if (horizontalLength <= 0.01f)
    {
        return std::nullopt;
    }

    const float pushStrength =
        resolvedSpellId == SpellId::WingBuffet
            ? 320.0f + 24.0f * static_cast<float>(skillLevel)
            : 160.0f + 8.0f * static_cast<float>(skillLevel);

    return bx::Vec3{
        (deltaX / horizontalLength) * pushStrength,
        (deltaY / horizontalLength) * pushStrength,
        0.0f};
}

GameplayActorService::SharedSpellEffectResult GameplayActorService::tryApplySharedSpellEffect(
    uint32_t spellId,
    uint32_t skillLevel,
    SkillMastery skillMastery,
    bool actorLooksUndead,
    bool defaultHostileToParty,
    int spellResistance,
    GameplayActorSpellEffectState &state,
    std::optional<float> rulesetSeconds) const
{
    SharedSpellEffectResult result = {};

    if (m_pSpellTable == nullptr)
    {
        return result;
    }

    const SpellEntry *pSpellEntry = m_pSpellTable->findById(static_cast<int>(spellId));

    if (pSpellEntry == nullptr)
    {
        return result;
    }

    const std::string &spellName = pSpellEntry->normalizedName;
    const CombatDamageType damageType = GameMechanics::parseCombatDamageType(pSpellEntry->schoolName);

    // Fate cast on a monster is a buff for it, so its resistances do not apply.
    if (spellName == "fate")
    {
        const int powerPerLevel = skillMastery == SkillMastery::Grandmaster
            ? 6
            : skillMastery == SkillMastery::Master
            ? 4
            : skillMastery == SkillMastery::Expert
            ? 2
            : 1;
        state.fateRemainingSeconds = minutesToSeconds(5.0f);
        state.fatePower = powerPerLevel * static_cast<int>(skillLevel);
        result.disposition = SharedSpellDisposition::Applied;
        return result;
    }

    // A ruleset's crowd control (MAW) lands without the resistance roll and lasts what its rules say; 0 is no effect.
    if (rulesetSeconds && *rulesetSeconds <= 0.0f)
    {
        result.disposition = SharedSpellDisposition::Rejected;
        return result;
    }

    if (!rulesetSeconds && damageType != CombatDamageType::Irresistible && spellResistance >= 200)
    {
        result.disposition = SharedSpellDisposition::Rejected;
        return result;
    }

    if (spellName == "stun")
    {
        if (!rulesetSeconds && !canApplyMmergeStatusSpell(skillLevel, skillMastery, spellResistance))
        {
            result.disposition = SharedSpellDisposition::Rejected;
            return result;
        }

        state.stunRemainingSeconds = std::max(state.stunRemainingSeconds, 0.5f + 0.35f * skillLevel);
        state.paralyzeRemainingSeconds = std::max(
            state.paralyzeRemainingSeconds,
            rulesetSeconds.value_or(
                60.0f + static_cast<float>(skillLevel * std::max(1, static_cast<int>(skillMastery)))));
        result.disposition = SharedSpellDisposition::Applied;
        result.effectKind = SharedSpellEffectKind::Stun;
        return result;
    }

    if (spellName == "slow")
    {
        if (!rulesetSeconds && !canApplyMmergeStatusSpell(skillLevel, skillMastery, spellResistance))
        {
            result.disposition = SharedSpellDisposition::Rejected;
            return result;
        }

        state.slowRemainingSeconds = std::max(
            state.slowRemainingSeconds,
            rulesetSeconds ? *rulesetSeconds
            : skillMastery == SkillMastery::Grandmaster
                ? minutesToSeconds(5.0f * skillLevel)
                : skillMastery == SkillMastery::Master
                ? minutesToSeconds(5.0f * skillLevel)
                : skillMastery == SkillMastery::Expert
                ? minutesToSeconds(5.0f * skillLevel)
                : minutesToSeconds(3.0f * skillLevel));
        state.slowMoveMultiplier =
            skillMastery == SkillMastery::Grandmaster
                ? 0.125f
                : skillMastery == SkillMastery::Master
                ? 0.25f
                : 0.5f;
        // Mastery deepens the walking slowdown only; recovery is always doubled.
        state.slowRecoveryMultiplier = 2.0f;
        result.disposition = SharedSpellDisposition::Applied;
        result.effectKind = SharedSpellEffectKind::Slow;
        return result;
    }

    if (spellName == "paralyze")
    {
        state.paralyzeRemainingSeconds = std::max(
            state.paralyzeRemainingSeconds, rulesetSeconds.value_or(minutesToSeconds(3.0f * skillLevel)));
        result.disposition = SharedSpellDisposition::Applied;
        result.effectKind = SharedSpellEffectKind::Paralyze;
        return result;
    }

    if (spellName == "turn undead")
    {
        if (!actorLooksUndead)
        {
            result.disposition = SharedSpellDisposition::Rejected;
            return result;
        }

        float durationSeconds = minutesToSeconds(3.0f + static_cast<float>(skillLevel));

        if (skillMastery == SkillMastery::Expert)
        {
            durationSeconds = minutesToSeconds(3.0f + 3.0f * static_cast<float>(skillLevel));
        }
        else if (skillMastery == SkillMastery::Master)
        {
            durationSeconds = minutesToSeconds(3.0f + 5.0f * static_cast<float>(skillLevel));
        }

        durationSeconds = rulesetSeconds.value_or(durationSeconds);

        state.fearRemainingSeconds = std::max(state.fearRemainingSeconds, durationSeconds);
        state.hasDetectedParty = false;
        result.disposition = SharedSpellDisposition::Applied;
        result.effectKind = SharedSpellEffectKind::Fear;
        return result;
    }

    if (spellName == "mass fear" || spellName == "fear")
    {
        const float durationSeconds =
            spellName == "mass fear"
                ? (skillMastery == SkillMastery::Grandmaster
                    ? minutesToSeconds(5.0f * skillLevel)
                    : minutesToSeconds(3.0f + 5.0f * static_cast<float>(skillLevel)))
                : (skillMastery == SkillMastery::Expert
                    ? minutesToSeconds(5.0f + static_cast<float>(skillLevel))
                    : minutesToSeconds(3.0f + static_cast<float>(skillLevel)));
        state.fearRemainingSeconds = std::max(state.fearRemainingSeconds, rulesetSeconds.value_or(durationSeconds));
        state.hasDetectedParty = false;
        result.disposition = SharedSpellDisposition::Applied;
        result.effectKind = SharedSpellEffectKind::Fear;
        return result;
    }

    if (spellName == "blind")
    {
        if (skillMastery < SkillMastery::Master)
        {
            result.disposition = SharedSpellDisposition::Rejected;
            return result;
        }

        state.blindRemainingSeconds = std::max(
            state.blindRemainingSeconds,
            skillMastery == SkillMastery::Grandmaster
                ? minutesToSeconds(10.0f * std::max<uint32_t>(1, skillLevel))
                : minutesToSeconds(5.0f * std::max<uint32_t>(1, skillLevel)));
        state.hostileToParty = false;
        state.hasDetectedParty = false;
        result.disposition = SharedSpellDisposition::Applied;
        result.effectKind = SharedSpellEffectKind::Blind;
        return result;
    }

    if (spellName == "charm"
        || spellName == "berserk"
        || spellName == "enslave"
        || spellName == "control undead"
        || spellName == "vampire charm")
    {
        if ((spellName == "control undead" || spellName == "vampire charm") && !actorLooksUndead)
        {
            result.disposition = SharedSpellDisposition::Rejected;
            return result;
        }

        if (!rulesetSeconds
            && spellName == "control undead"
            && spellResistance > static_cast<int>(skillLevel) * std::max(1, static_cast<int>(skillMastery)))
        {
            result.disposition = SharedSpellDisposition::Rejected;
            return result;
        }

        state.controlRemainingSeconds = std::max(
            state.controlRemainingSeconds,
            rulesetSeconds ? *rulesetSeconds
            : spellName == "charm"
                ? (skillMastery == SkillMastery::Grandmaster
                    ? hoursToSeconds(24.0f)
                    : skillMastery == SkillMastery::Master
                    ? minutesToSeconds(10.0f * skillLevel)
                    : minutesToSeconds(5.0f * skillLevel))
                : spellName == "berserk"
                ? (skillMastery == SkillMastery::Grandmaster
                    ? hoursToSeconds(1.0f * skillLevel)
                    : skillMastery == SkillMastery::Master
                    ? minutesToSeconds(10.0f * skillLevel)
                    : minutesToSeconds(5.0f * skillLevel))
                : spellName == "enslave"
                ? minutesToSeconds(10.0f * skillLevel)
                : spellName == "vampire charm"
                ? minutesToSeconds(10.0f * skillLevel)
                : (skillMastery == SkillMastery::Grandmaster
                    ? hoursToSeconds(24.0f)
                    : skillMastery == SkillMastery::Master
                    ? minutesToSeconds(5.0f * skillLevel)
                    : minutesToSeconds(3.0f * skillLevel)));
        state.controlMode =
            spellName == "charm"
                ? GameplayActorControlMode::Charm
                : spellName == "berserk"
                ? GameplayActorControlMode::Berserk
                : spellName == "enslave"
                ? GameplayActorControlMode::Enslaved
                : GameplayActorControlMode::ControlUndead;
        // A berserk monster stays hostile to the party too: it attacks whoever is nearest.
        state.hostileToParty = spellName == "berserk";
        state.hasDetectedParty = false;
        result.disposition = SharedSpellDisposition::Applied;
        result.effectKind = SharedSpellEffectKind::Control;
        return result;
    }

    if (spellName == "shrinking ray")
    {
        state.shrinkRemainingSeconds = std::max(
            state.shrinkRemainingSeconds,
            rulesetSeconds.value_or(minutesToSeconds(5.0f * std::max<uint32_t>(1, skillLevel))));
        state.shrinkDamageMultiplier =
            skillMastery == SkillMastery::Grandmaster
                ? 0.25f
                : skillMastery == SkillMastery::Master
                ? 0.25f
                : skillMastery == SkillMastery::Expert
                ? (1.0f / 3.0f)
                : 0.5f;
        state.shrinkArmorClassMultiplier = state.shrinkDamageMultiplier;
        result.disposition = SharedSpellDisposition::Applied;
        result.effectKind = SharedSpellEffectKind::Shrink;
        return result;
    }

    if (spellName == "dark grasp")
    {
        state.darkGraspRemainingSeconds = std::max(
            state.darkGraspRemainingSeconds,
            rulesetSeconds ? *rulesetSeconds
            : skillMastery == SkillMastery::Grandmaster
                ? minutesToSeconds(10.0f * std::max<uint32_t>(1, skillLevel))
                : minutesToSeconds(5.0f * std::max<uint32_t>(1, skillLevel)));
        state.slowRemainingSeconds = std::max(state.slowRemainingSeconds, state.darkGraspRemainingSeconds);
        state.slowMoveMultiplier = std::min(state.slowMoveMultiplier, 0.5f);
        state.slowRecoveryMultiplier = std::max(state.slowRecoveryMultiplier, 2.0f);
        result.disposition = SharedSpellDisposition::Applied;
        result.effectKind = SharedSpellEffectKind::DarkGrasp;
        return result;
    }

    if (isSpellId(spellId, SpellId::DispelMagic))
    {
        clearSpellEffects(state, defaultHostileToParty);
        result.disposition = SharedSpellDisposition::Applied;
        result.effectKind = SharedSpellEffectKind::DispelMagic;
        return result;
    }

    return result;
}

bool GameplayActorService::hasRunningSpellEffectTimer(const GameplayActorSpellEffectState &state)
{
    return state.slowRemainingSeconds > 0.0f
        || state.stunRemainingSeconds > 0.0f
        || state.paralyzeRemainingSeconds > 0.0f
        || state.fearRemainingSeconds > 0.0f
        || state.blindRemainingSeconds > 0.0f
        || state.controlRemainingSeconds > 0.0f
        || state.shrinkRemainingSeconds > 0.0f
        || state.darkGraspRemainingSeconds > 0.0f
        || state.dayOfProtectionRemainingSeconds > 0.0f
        || state.hourOfPowerRemainingSeconds > 0.0f
        || state.painReflectionRemainingSeconds > 0.0f
        || state.hammerhandsRemainingSeconds > 0.0f
        || state.hasteRemainingSeconds > 0.0f
        || state.shieldRemainingSeconds > 0.0f
        || state.stoneskinRemainingSeconds > 0.0f
        || state.blessRemainingSeconds > 0.0f
        || state.fateRemainingSeconds > 0.0f
        || state.heroismRemainingSeconds > 0.0f;
}

void GameplayActorService::updateSpellEffectTimers(
    GameplayActorSpellEffectState &state,
    float deltaSeconds,
    bool defaultHostileToParty) const
{
    if (deltaSeconds <= 0.0f)
    {
        return;
    }

    state.slowRemainingSeconds = std::max(0.0f, state.slowRemainingSeconds - deltaSeconds);
    state.stunRemainingSeconds = std::max(0.0f, state.stunRemainingSeconds - deltaSeconds);
    state.paralyzeRemainingSeconds = std::max(0.0f, state.paralyzeRemainingSeconds - deltaSeconds);
    state.fearRemainingSeconds = std::max(0.0f, state.fearRemainingSeconds - deltaSeconds);
    state.blindRemainingSeconds = std::max(0.0f, state.blindRemainingSeconds - deltaSeconds);
    state.controlRemainingSeconds = std::max(0.0f, state.controlRemainingSeconds - deltaSeconds);
    state.shrinkRemainingSeconds = std::max(0.0f, state.shrinkRemainingSeconds - deltaSeconds);
    state.armorClassHalvedRemainingSeconds =
        std::max(0.0f, state.armorClassHalvedRemainingSeconds - deltaSeconds);
    state.darkGraspRemainingSeconds = std::max(0.0f, state.darkGraspRemainingSeconds - deltaSeconds);
    state.dayOfProtectionRemainingSeconds = std::max(0.0f, state.dayOfProtectionRemainingSeconds - deltaSeconds);
    state.hourOfPowerRemainingSeconds = std::max(0.0f, state.hourOfPowerRemainingSeconds - deltaSeconds);
    state.painReflectionRemainingSeconds = std::max(0.0f, state.painReflectionRemainingSeconds - deltaSeconds);
    state.hammerhandsRemainingSeconds = std::max(0.0f, state.hammerhandsRemainingSeconds - deltaSeconds);
    state.hasteRemainingSeconds = std::max(0.0f, state.hasteRemainingSeconds - deltaSeconds);
    state.shieldRemainingSeconds = std::max(0.0f, state.shieldRemainingSeconds - deltaSeconds);
    state.stoneskinRemainingSeconds = std::max(0.0f, state.stoneskinRemainingSeconds - deltaSeconds);
    state.blessRemainingSeconds = std::max(0.0f, state.blessRemainingSeconds - deltaSeconds);
    state.fateRemainingSeconds = std::max(0.0f, state.fateRemainingSeconds - deltaSeconds);
    state.heroismRemainingSeconds = std::max(0.0f, state.heroismRemainingSeconds - deltaSeconds);

    if (state.slowRemainingSeconds <= 0.0f)
    {
        state.slowMoveMultiplier = 1.0f;
        state.slowRecoveryMultiplier = 1.0f;
    }

    if (state.controlRemainingSeconds <= 0.0f && state.controlMode != GameplayActorControlMode::None)
    {
        state.controlMode = GameplayActorControlMode::None;
        state.hostileToParty = defaultHostileToParty;
        state.hasDetectedParty = false;
    }

    if (state.shrinkRemainingSeconds <= 0.0f)
    {
        state.shrinkDamageMultiplier = 1.0f;
        state.shrinkArmorClassMultiplier = 1.0f;
    }

    if (state.dayOfProtectionRemainingSeconds <= 0.0f)
    {
        state.dayOfProtectionPower = 0;
    }

    if (state.hourOfPowerRemainingSeconds <= 0.0f)
    {
        state.hourOfPowerPower = 0;
    }

    if (state.hammerhandsRemainingSeconds <= 0.0f)
    {
        state.hammerhandsPower = 0;
    }

    if (state.stoneskinRemainingSeconds <= 0.0f)
    {
        state.stoneskinPower = 0;
    }

    if (state.blessRemainingSeconds <= 0.0f)
    {
        state.blessPower = 0;
    }

    if (state.fateRemainingSeconds <= 0.0f)
    {
        state.fatePower = 0;
    }

    if (state.heroismRemainingSeconds <= 0.0f)
    {
        state.heroismPower = 0;
    }
}

bool GameplayActorService::isPartyControlledActor(GameplayActorControlMode controlMode) const
{
    switch (controlMode)
    {
        case GameplayActorControlMode::Charm:
        case GameplayActorControlMode::Enslaved:
        case GameplayActorControlMode::ControlUndead:
        case GameplayActorControlMode::Reanimated:
            return true;

        default:
            return false;
    }
}

bool GameplayActorService::monsterIdsAreFriendly(
    int16_t leftMonsterId,
    int16_t rightMonsterId,
    const std::unordered_map<uint32_t, int32_t> *pRelationOverrides) const
{
    if (pRelationOverrides != nullptr && !pRelationOverrides->empty())
    {
        const auto overrideIterator =
            pRelationOverrides->find(relationOverrideKey(uint32_t(leftMonsterId), uint32_t(rightMonsterId)));

        if (overrideIterator != pRelationOverrides->end())
        {
            return overrideIterator->second <= 0;
        }
    }

    return m_pMonsterTable != nullptr
        && m_pMonsterTable->getRelationBetweenMonsters(leftMonsterId, rightMonsterId) <= 0;
}

bool GameplayActorService::monsterIdsAreHostile(int16_t leftMonsterId, int16_t rightMonsterId) const
{
    return m_pMonsterTable != nullptr
        && m_pMonsterTable->getRelationBetweenMonsters(leftMonsterId, rightMonsterId) > 0;
}

float GameplayActorService::partyEngagementRange(const GameplayActorTargetPolicyState &actor) const
{
    if (m_pMonsterTable == nullptr || isPartyControlledActor(actor.controlMode))
    {
        return 0.0f;
    }

    return actor.hostileToParty ? m_partyEngagementRange : 0.0f;
}

float GameplayActorService::hostilityPromotionRangeForFriendlyActor(int relation) const
{
    switch (relation)
    {
        case 1:
            return 0.0f;
        case 2:
            return HostilityCloseRange;
        case 3:
            return HostilityShortRange;
        case 4:
            return HostilityMediumRange;
        default:
            return -1.0f;
    }
}

bool GameplayActorService::shouldFleeForAiType(GameplayActorAiType aiType, int currentHp, int maxHp) const
{
    if (aiType == GameplayActorAiType::Wimp)
    {
        return true;
    }

    if (maxHp <= 0)
    {
        return false;
    }

    if (aiType == GameplayActorAiType::Normal)
    {
        return static_cast<float>(currentHp) < static_cast<float>(maxHp) * 0.2f;
    }

    if (aiType == GameplayActorAiType::Aggressive)
    {
        return static_cast<float>(currentHp) < static_cast<float>(maxHp) * 0.1f;
    }

    return false;
}

float GameplayActorService::initialAttackCooldownSeconds(uint32_t actorId, float recoverySeconds) const
{
    return recoverySeconds * actorDecisionRange(actorId, 0, 0x4d595df4u, 0.25f, 1.0f);
}

float GameplayActorService::initialIdleDecisionSeconds(uint32_t actorId) const
{
    return actorDecisionRange(actorId, 0, 0x1f123bb5u, 0.2f, 1.35f);
}

bool GameplayActorService::isActorUnavailableForCombat(
    bool invisible,
    bool dead,
    bool hpDepleted,
    bool dyingState,
    bool deadState) const
{
    return invisible || dead || hpDepleted || dyingState || deadState;
}

bool GameplayActorService::canActorEnterHitReaction(
    bool invisible,
    bool dead,
    bool hpDepleted,
    bool dyingState,
    bool deadState,
    bool stunnedState,
    bool attackingState,
    bool force) const
{
    return !isActorUnavailableForCombat(invisible, dead, hpDepleted, dyingState, deadState)
        && (force || (!stunnedState && !attackingState));
}

bool GameplayActorService::partyIsVeryNearActor(
    float horizontalDistanceToParty,
    float verticalDistanceToParty,
    float actorRadius,
    float actorHeight,
    float partyCollisionRadius) const
{
    const float nearDistance = std::max(0.0f, actorRadius)
        + std::max(0.0f, partyCollisionRadius)
        + 16.0f;
    const float verticalReach = std::max(std::max(0.0f, actorHeight), 192.0f);

    return horizontalDistanceToParty <= nearDistance
        && std::abs(verticalDistanceToParty) <= verticalReach;
}

float GameplayActorService::effectiveActorMoveSpeed(
    int configuredMoveSpeed,
    int defaultMoveSpeed,
    float slowMoveMultiplier,
    bool darkGraspActive) const
{
    const int rawMoveSpeed = configuredMoveSpeed > 0 ? configuredMoveSpeed : defaultMoveSpeed;
    const float baseMoveSpeed = std::max(1, rawMoveSpeed);

    return baseMoveSpeed * slowMoveMultiplier * (darkGraspActive ? 0.5f : 1.0f);
}

float GameplayActorService::effectiveRecoveryProgressMultiplier(const GameplayActorSpellEffectState &state) const
{
    float multiplier = 1.0f / std::max(1.0f, state.slowRecoveryMultiplier);

    if (state.hasteRemainingSeconds > 0.0f || state.hourOfPowerRemainingSeconds > 0.0f)
    {
        multiplier *= 1.5f;
    }

    return std::max(0.125f, multiplier);
}

int GameplayActorService::effectiveAttackDamageBonus(
    GameplayActorAttackAbility ability,
    const GameplayActorSpellEffectState &state) const
{
    if (ability != GameplayActorAttackAbility::Attack1)
    {
        return 0;
    }

    int bonus = 0;

    if (state.hourOfPowerRemainingSeconds > 0.0f)
    {
        bonus = std::max(bonus, state.hourOfPowerPower);
    }

    if (state.heroismRemainingSeconds > 0.0f)
    {
        bonus = std::max(bonus, state.heroismPower);
    }

    if (state.hammerhandsRemainingSeconds > 0.0f)
    {
        bonus += state.hammerhandsPower;
    }

    return std::max(0, bonus);
}

int GameplayActorService::effectiveAttackHitBonus(const GameplayActorSpellEffectState &state) const
{
    int bonus = 0;

    if (state.hourOfPowerRemainingSeconds > 0.0f)
    {
        bonus = std::max(bonus, state.hourOfPowerPower);
    }

    if (state.blessRemainingSeconds > 0.0f)
    {
        bonus = std::max(bonus, state.blessPower);
    }

    if (state.fateRemainingSeconds > 0.0f)
    {
        bonus += state.fatePower;
    }

    return std::max(0, bonus);
}

bool GameplayActorService::halveIncomingMissileDamage(const GameplayActorSpellEffectState &state) const
{
    return state.shieldRemainingSeconds > 0.0f;
}

bool GameplayActorService::hasPainReflection(const GameplayActorSpellEffectState &state) const
{
    return state.painReflectionRemainingSeconds > 0.0f;
}

GameplayActorTargetPolicyResult GameplayActorService::resolveActorTargetPolicy(
    const GameplayActorTargetPolicyState &actor,
    const GameplayActorTargetPolicyState &target,
    const std::unordered_map<uint32_t, int32_t> *pRelationOverrides) const
{
    GameplayActorTargetPolicyResult result = resolveFactionTargetPolicy(actor, target);

    if (pRelationOverrides == nullptr || pRelationOverrides->empty())
    {
        return result;
    }

    const uint32_t actorRelationMonsterId =
        uint32_t(actor.relationMonsterId > 0 ? actor.relationMonsterId : actor.monsterId);
    const uint32_t targetRelationMonsterId =
        uint32_t(target.relationMonsterId > 0 ? target.relationMonsterId : target.monsterId);
    const auto findRow = [pRelationOverrides](uint32_t left, uint32_t right)
    {
        return pRelationOverrides->find(relationOverrideKey(left, right));
    };
    auto overrideIterator = pRelationOverrides->end();

    if (actor.group != 0)
    {
        overrideIterator = findRow(relationGroupSide(actor.group), targetRelationMonsterId);
    }

    if (overrideIterator == pRelationOverrides->end() && target.group != 0)
    {
        overrideIterator = findRow(actorRelationMonsterId, relationGroupSide(target.group));
    }

    if (overrideIterator == pRelationOverrides->end())
    {
        overrideIterator = findRow(actorRelationMonsterId, targetRelationMonsterId);
    }

    if (overrideIterator == pRelationOverrides->end())
    {
        return result;
    }

    if (!result.canTarget && overrideIterator->second > 0)
    {
        result.canTarget = true;
        result.relationToTarget = overrideIterator->second;
        result.engagementRange = hostilityRangeForRelation(overrideIterator->second);
    }
    else if (result.canTarget && overrideIterator->second <= 0)
    {
        result = {};
    }

    return result;
}

GameplayActorTargetPolicyResult GameplayActorService::resolveFactionTargetPolicy(
    const GameplayActorTargetPolicyState &actor,
    const GameplayActorTargetPolicyState &target) const
{
    GameplayActorTargetPolicyResult result = {};
    const bool actorIsPartyControlled = isPartyControlledActor(actor.controlMode);
    const bool targetIsPartyControlled = isPartyControlledActor(target.controlMode);

    if (actorIsPartyControlled)
    {
        if (!target.hostileToParty || targetIsPartyControlled)
        {
            return result;
        }

        result.canTarget = true;
        result.relationToTarget = 4;
        result.engagementRange = HostilityLongRange;
        return result;
    }

    const bool hostileToSummon = actor.hostileToParty && targetIsPartyControlled;
    const int16_t actorRelationMonsterId = actor.relationMonsterId > 0 ? actor.relationMonsterId : actor.monsterId;
    const int16_t targetRelationMonsterId = target.relationMonsterId > 0 ? target.relationMonsterId : target.monsterId;

    if (!hostileToSummon && actor.group != 0 && actor.group == target.group)
    {
        return result;
    }

    // A berserk monster attacks whatever is nearest, and every monster may fight it back (MM8: "attacking the nearest
    // living creature"; the original makes it hostile at long range to all but its own group).
    const bool berserk = actor.controlMode == GameplayActorControlMode::Berserk
        || target.controlMode == GameplayActorControlMode::Berserk;
    // A monster hit by another fights it back at long range, whatever their factions (MM6-MM8 lastCharacterIdToHit;
    // OE Actor::FindClosestActor): how Evenmorn's gargoyles answer the ghosts.
    const bool strikesBack = actor.lastActorAttackerId && *actor.lastActorAttackerId == target.actorId;

    const int factionRelation = m_pMonsterTable != nullptr
        ? m_pMonsterTable->getRelationBetweenMonsters(actorRelationMonsterId, targetRelationMonsterId)
        : 0;
    const bool hostileByFaction = factionRelation > 0;

    if (!hostileByFaction && !hostileToSummon && !berserk && !strikesBack)
    {
        return result;
    }

    if (hostileToSummon || berserk || strikesBack)
    {
        if (!actorCanEngageActorTarget(m_pMonsterTable, actor, target))
        {
            return result;
        }

        result.canTarget = true;
        result.relationToTarget = 4;
        result.engagementRange = HostilityLongRange;
        return result;
    }

    result.relationToTarget = factionRelation;
    result.engagementRange = hostilityRangeForRelation(result.relationToTarget);
    result.canTarget = result.engagementRange > 0.0f;
    return result;
}

bool GameplayActorService::clearSpellEffects(
    GameplayActorSpellEffectState &state,
    bool defaultHostileToParty) const
{
    const bool hadEffect =
        state.slowRemainingSeconds > 0.0f
        || state.stunRemainingSeconds > 0.0f
        || state.paralyzeRemainingSeconds > 0.0f
        || state.fearRemainingSeconds > 0.0f
        || state.blindRemainingSeconds > 0.0f
        || state.controlRemainingSeconds > 0.0f
        || state.controlMode != GameplayActorControlMode::None
        || state.shrinkRemainingSeconds > 0.0f
        || state.armorClassHalvedRemainingSeconds > 0.0f
        || state.darkGraspRemainingSeconds > 0.0f
        || state.dayOfProtectionRemainingSeconds > 0.0f
        || state.hourOfPowerRemainingSeconds > 0.0f
        || state.painReflectionRemainingSeconds > 0.0f
        || state.hammerhandsRemainingSeconds > 0.0f
        || state.hasteRemainingSeconds > 0.0f
        || state.shieldRemainingSeconds > 0.0f
        || state.stoneskinRemainingSeconds > 0.0f
        || state.blessRemainingSeconds > 0.0f
        || state.fateRemainingSeconds > 0.0f
        || state.heroismRemainingSeconds > 0.0f
        || state.slowMoveMultiplier != 1.0f
        || state.slowRecoveryMultiplier != 1.0f
        || state.shrinkDamageMultiplier != 1.0f
        || state.shrinkArmorClassMultiplier != 1.0f;

    state.slowRemainingSeconds = 0.0f;
    state.slowMoveMultiplier = 1.0f;
    state.slowRecoveryMultiplier = 1.0f;
    state.stunRemainingSeconds = 0.0f;
    state.paralyzeRemainingSeconds = 0.0f;
    state.fearRemainingSeconds = 0.0f;
    state.blindRemainingSeconds = 0.0f;
    state.controlRemainingSeconds = 0.0f;
    state.controlMode = GameplayActorControlMode::None;
    state.shrinkRemainingSeconds = 0.0f;
    state.shrinkDamageMultiplier = 1.0f;
    state.shrinkArmorClassMultiplier = 1.0f;
    state.armorClassHalvedRemainingSeconds = 0.0f;
    state.darkGraspRemainingSeconds = 0.0f;
    state.dayOfProtectionRemainingSeconds = 0.0f;
    state.dayOfProtectionPower = 0;
    state.hourOfPowerRemainingSeconds = 0.0f;
    state.hourOfPowerPower = 0;
    state.painReflectionRemainingSeconds = 0.0f;
    state.hammerhandsRemainingSeconds = 0.0f;
    state.hammerhandsPower = 0;
    state.hasteRemainingSeconds = 0.0f;
    state.shieldRemainingSeconds = 0.0f;
    state.stoneskinRemainingSeconds = 0.0f;
    state.stoneskinPower = 0;
    state.blessRemainingSeconds = 0.0f;
    state.blessPower = 0;
    state.fateRemainingSeconds = 0.0f;
    state.fatePower = 0;
    state.heroismRemainingSeconds = 0.0f;
    state.heroismPower = 0;
    state.hostileToParty = defaultHostileToParty;
    state.hasDetectedParty = false;
    return hadEffect;
}

bool GameplayActorService::breakFearAndControlOnPartyDamage(GameplayActorSpellEffectState &state) const
{
    const bool hadFear = state.fearRemainingSeconds > 0.0f;
    const bool hadControl =
        state.controlRemainingSeconds > 0.0f || state.controlMode != GameplayActorControlMode::None;

    if (!hadFear && !hadControl)
    {
        return false;
    }

    state.fearRemainingSeconds = 0.0f;
    state.controlRemainingSeconds = 0.0f;
    state.controlMode = GameplayActorControlMode::None;
    state.hostileToParty = true;
    state.hasDetectedParty = true;
    return true;
}

int GameplayActorService::effectiveArmorClass(int baseArmorClass, const GameplayActorSpellEffectState &state) const
{
    int armorClass = baseArmorClass;

    if (state.shrinkRemainingSeconds > 0.0f)
    {
        armorClass = static_cast<int>(std::floor(static_cast<float>(armorClass) * state.shrinkArmorClassMultiplier));
    }

    if (state.darkGraspRemainingSeconds > 0.0f)
    {
        armorClass /= 2;
    }

    if (state.armorClassHalvedRemainingSeconds > 0.0f)
    {
        armorClass /= 2;
    }

    int armorBonus = 0;

    if (state.hourOfPowerRemainingSeconds > 0.0f)
    {
        armorBonus = std::max(armorBonus, state.hourOfPowerPower);
    }

    if (state.stoneskinRemainingSeconds > 0.0f)
    {
        armorBonus = std::max(armorBonus, state.stoneskinPower);
    }

    return std::max(0, armorClass + armorBonus);
}
}
