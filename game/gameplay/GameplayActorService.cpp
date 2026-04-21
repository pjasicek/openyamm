#include "game/gameplay/GameplayActorService.h"

#include "game/StringUtils.h"
#include "game/party/SpellIds.h"
#include "game/tables/MonsterTable.h"
#include "game/tables/SpellTable.h"

#include <algorithm>
#include <array>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
constexpr float HostilityCloseRange = 1024.0f;
constexpr float HostilityShortRange = 2560.0f;
constexpr float HostilityMediumRange = 5120.0f;
constexpr float HostilityLongRange = 10240.0f;
constexpr float CrowdNoProgressThreshold = 8.0f;
constexpr float CrowdNoProgressStandSeconds = 1.2f;
constexpr float CrowdProbeWindowSeconds = 0.35f;
constexpr float CrowdProbeEdgeDistanceThreshold = 12.0f;
constexpr float Pi = 3.14159265358979323846f;
constexpr float IdleStandSeconds = 1.5f;
constexpr float IdleBoredSeconds = 2.0f;
constexpr uint32_t IdleStandChancePercent = 25u;
constexpr uint32_t InactiveFidgetChancePercent = 5u;

float minutesToSeconds(float minutes)
{
    return minutes * 60.0f;
}

float hoursToSeconds(float hours)
{
    return hours * 3600.0f;
}

bool looksUndeadByName(const std::string &name, const std::string &pictureName)
{
    const std::string normalizedName = toLowerCopy(name + " " + pictureName);
    static const std::array<const char *, 11> UndeadTokens = {{
        "skeleton",
        "zombie",
        "ghost",
        "ghoul",
        "vampire",
        "lich",
        "mummy",
        "wight",
        "spectre",
        "spirit",
        "undead"
    }};

    for (const char *pToken : UndeadTokens)
    {
        if (normalizedName.find(pToken) != std::string::npos)
        {
            return true;
        }
    }

    return false;
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

float normalizeAngleRadians(float angle)
{
    while (angle <= -Pi)
    {
        angle += 2.0f * Pi;
    }

    while (angle > Pi)
    {
        angle -= 2.0f * Pi;
    }

    return angle;
}

float shortestAngleDistanceRadians(float left, float right)
{
    return std::abs(normalizeAngleRadians(left - right));
}

bool attackAbilityIsRanged(
    GameplayActorAttackAbility ability,
    const GameplayActorAttackConstraintState &state)
{
    switch (ability)
    {
        case GameplayActorAttackAbility::Attack1:
            return state.attack1IsRanged;

        case GameplayActorAttackAbility::Attack2:
            return state.attack2IsRanged;

        case GameplayActorAttackAbility::Spell1:
        case GameplayActorAttackAbility::Spell2:
            return true;
    }

    return false;
}

GameplayActorAttackAbility fallbackMeleeAttackAbility(
    GameplayActorAttackAbility chosenAbility,
    const GameplayActorAttackConstraintState &state)
{
    if (chosenAbility == GameplayActorAttackAbility::Attack1 && !state.attack1IsRanged)
    {
        return chosenAbility;
    }

    if (!state.attack1IsRanged)
    {
        return GameplayActorAttackAbility::Attack1;
    }

    if (!state.attack2IsRanged)
    {
        return GameplayActorAttackAbility::Attack2;
    }

    return chosenAbility;
}
}

void GameplayActorService::bindTables(const MonsterTable *pMonsterTable, const SpellTable *pSpellTable)
{
    m_pMonsterTable = pMonsterTable;
    m_pSpellTable = pSpellTable;
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
    return pStats != nullptr && looksUndeadByName(pStats->name, pStats->pictureName);
}

GameplayActorService::SharedSpellEffectResult GameplayActorService::tryApplySharedSpellEffect(
    uint32_t spellId,
    uint32_t skillLevel,
    SkillMastery skillMastery,
    bool actorLooksUndead,
    bool defaultHostileToParty,
    GameplayActorSpellEffectState &state) const
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

    if (spellName == "stun")
    {
        state.stunRemainingSeconds = std::max(state.stunRemainingSeconds, 0.5f + 0.35f * skillLevel);
        result.disposition = SharedSpellDisposition::Applied;
        result.effectKind = SharedSpellEffectKind::Stun;
        return result;
    }

    if (spellName == "slow")
    {
        state.slowRemainingSeconds = std::max(
            state.slowRemainingSeconds,
            skillMastery == SkillMastery::Grandmaster
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
        state.slowRecoveryMultiplier =
            skillMastery == SkillMastery::Grandmaster
                ? 8.0f
                : skillMastery == SkillMastery::Master
                ? 4.0f
                : 2.0f;
        result.disposition = SharedSpellDisposition::Applied;
        result.effectKind = SharedSpellEffectKind::Slow;
        return result;
    }

    if (spellName == "paralyze")
    {
        state.paralyzeRemainingSeconds = std::max(state.paralyzeRemainingSeconds, minutesToSeconds(3.0f * skillLevel));
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
        state.fearRemainingSeconds = std::max(state.fearRemainingSeconds, durationSeconds);
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

        state.controlRemainingSeconds = std::max(
            state.controlRemainingSeconds,
            spellName == "charm"
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
        state.hostileToParty = false;
        state.hasDetectedParty = false;
        result.disposition = SharedSpellDisposition::Applied;
        result.effectKind = SharedSpellEffectKind::Control;
        return result;
    }

    if (spellName == "shrinking ray")
    {
        state.shrinkRemainingSeconds = std::max(
            state.shrinkRemainingSeconds,
            minutesToSeconds(5.0f * std::max<uint32_t>(1, skillLevel)));
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
            skillMastery == SkillMastery::Grandmaster
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
    state.darkGraspRemainingSeconds = std::max(0.0f, state.darkGraspRemainingSeconds - deltaSeconds);

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

bool GameplayActorService::monsterIdsAreFriendly(int16_t leftMonsterId, int16_t rightMonsterId) const
{
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

    if (actor.hostileToParty)
    {
        return HostilityLongRange;
    }

    return hostilityRangeForRelation(m_pMonsterTable->getRelationToParty(actor.monsterId));
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

GameplayActorService::FriendlyTargetEngagementResult GameplayActorService::resolveFriendlyTargetEngagement(
    const GameplayActorTargetPolicyState &actor,
    uint8_t hostilityType,
    int relationToTarget,
    float targetDistanceSquared) const
{
    FriendlyTargetEngagementResult result = {};

    if (hostilityType != 0 || isPartyControlledActor(actor.controlMode))
    {
        return result;
    }

    result.promotionRange = hostilityPromotionRangeForFriendlyActor(relationToTarget);
    result.shouldPromoteHostility =
        relationToTarget == 1
        || (result.promotionRange >= 0.0f
            && targetDistanceSquared <= result.promotionRange * result.promotionRange);
    result.shouldEngageTarget = result.shouldPromoteHostility;
    return result;
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

GameplayActorAttackChoiceResult GameplayActorService::chooseAttackAbility(
    uint32_t actorId,
    uint32_t attackDecisionCount,
    bool hasSpell1,
    int spell1UseChance,
    bool hasSpell2,
    int spell2UseChance,
    int attack2Chance) const
{
    GameplayActorAttackChoiceResult result = {};
    result.nextDecisionCount = attackDecisionCount + 1;

    const uint32_t baseSeed = mixActorDecisionSeed(actorId, attackDecisionCount, 0x7f4a7c15u);

    auto passesChance =
        [&](int chance, uint32_t salt)
        {
            if (chance <= 0)
            {
                return false;
            }

            return ((baseSeed ^ salt) % 100u) < static_cast<uint32_t>(chance);
        };

    if (hasSpell1 && passesChance(spell1UseChance, 0x13579bdfu))
    {
        result.ability = GameplayActorAttackAbility::Spell1;
        return result;
    }

    if (hasSpell2 && passesChance(spell2UseChance, 0x2468ace0u))
    {
        result.ability = GameplayActorAttackAbility::Spell2;
        return result;
    }

    if (passesChance(attack2Chance, 0x55aa55aau))
    {
        result.ability = GameplayActorAttackAbility::Attack2;
        return result;
    }

    result.ability = GameplayActorAttackAbility::Attack1;
    return result;
}

GameplayActorAttackAbility GameplayActorService::resolveAttackAbilityConstraints(
    GameplayActorAttackAbility chosenAbility,
    const GameplayActorAttackConstraintState &state) const
{
    if (!attackAbilityIsRanged(chosenAbility, state))
    {
        return chosenAbility;
    }

    if (state.blindActive || state.darkGraspActive || !state.rangedCommitAllowed)
    {
        return fallbackMeleeAttackAbility(chosenAbility, state);
    }

    return chosenAbility;
}

GameplayActorService::CrowdSteeringResult GameplayActorService::resolveCrowdSteering(
    uint32_t actorId,
    uint32_t pursueDecisionCount,
    float targetEdgeDistance,
    float deltaSeconds,
    const CrowdSteeringState &state) const
{
    CrowdSteeringResult result = {};
    result.state = state;
    result.nextDecisionCount = pursueDecisionCount;
    result.sideSign = result.state.sideSign == 0 ? 1 : result.state.sideSign;
    result.state.probeElapsedSeconds += std::max(0.0f, deltaSeconds);

    const float progressTowardTarget =
        result.state.lastEdgeDistance > 0.0f
        ? (result.state.lastEdgeDistance - targetEdgeDistance)
        : 0.0f;
    const float crowdProbeEdgeProgress =
        result.state.probeEdgeDistance > 0.0f
        ? (result.state.probeEdgeDistance - targetEdgeDistance)
        : 0.0f;

    if (result.state.sideSign == 0)
    {
        const uint32_t decisionSeed = mixActorDecisionSeed(actorId, result.nextDecisionCount, 0x4f1bbcd3u);
        ++result.nextDecisionCount;
        result.sideSign = (decisionSeed & 1u) == 0u ? 1 : -1;
        result.state.sideSign = result.sideSign;

        if (result.state.lastEdgeDistance <= 0.0f)
        {
            result.state.lastEdgeDistance = targetEdgeDistance;
        }

        result.action = CrowdSteeringAction::SideStep;
        return result;
    }

    if (progressTowardTarget > CrowdNoProgressThreshold)
    {
        result.state.noProgressSeconds = 0.0f;
        result.state.lastEdgeDistance = targetEdgeDistance;
        result.state.escapeAttempts = 0;
    }
    else
    {
        result.state.noProgressSeconds += std::max(0.0f, deltaSeconds);
    }

    const bool crowdProbeStalled =
        result.state.probeElapsedSeconds >= CrowdProbeWindowSeconds
        && crowdProbeEdgeProgress <= CrowdProbeEdgeDistanceThreshold;

    if (crowdProbeStalled && result.state.retreatRemainingSeconds <= 0.0f)
    {
        ++result.state.escapeAttempts;

        const uint32_t decisionSeed = mixActorDecisionSeed(actorId, result.nextDecisionCount, 0x7a5f18c3u);
        ++result.nextDecisionCount;
        const bool shouldStandAfterRetries =
            result.state.escapeAttempts >= 3
            && ((decisionSeed % 100u) < 45u
                || result.state.noProgressSeconds >= CrowdNoProgressStandSeconds);

        if (shouldStandAfterRetries)
        {
            result.action = CrowdSteeringAction::Stand;
            result.standSeconds = actorDecisionRange(
                actorId,
                result.nextDecisionCount,
                0x5b1d8e73u,
                0.9f,
                1.4f);
            result.bored = (decisionSeed % 100u) < 35u;
            result.state.noProgressSeconds = 0.0f;
            result.state.lastEdgeDistance = 0.0f;
            result.state.retreatRemainingSeconds = 0.0f;
            result.state.standRemainingSeconds = result.standSeconds;
            result.state.probeEdgeDistance = 0.0f;
            result.state.probeElapsedSeconds = 0.0f;
            result.state.escapeAttempts = 0;
            result.state.sideSign = 0;
            return result;
        }

        result.action = CrowdSteeringAction::Retreat;
        result.retreatSeconds = actorDecisionRange(
            actorId,
            result.nextDecisionCount,
            0x6d2c4a91u,
            0.18f,
            0.32f);
        result.state.retreatRemainingSeconds = result.retreatSeconds;
        result.state.noProgressSeconds = 0.0f;
        result.state.probeEdgeDistance = targetEdgeDistance;
        result.state.probeElapsedSeconds = 0.0f;
        return result;
    }

    if (result.state.retreatRemainingSeconds > 0.0f)
    {
        result.action = CrowdSteeringAction::Retreat;
        result.retreatSeconds = result.state.retreatRemainingSeconds;
        result.state.noProgressSeconds = 0.0f;
    }
    else
    {
        result.action = CrowdSteeringAction::SideStep;
    }

    if (result.state.probeElapsedSeconds >= CrowdProbeWindowSeconds
        && crowdProbeEdgeProgress > CrowdProbeEdgeDistanceThreshold)
    {
        result.state.probeEdgeDistance = targetEdgeDistance;
        result.state.probeElapsedSeconds = 0.0f;
    }

    return result;
}

GameplayActorService::IdleBehaviorResult GameplayActorService::idleStandBehavior(bool bored) const
{
    IdleBehaviorResult result = {};
    result.action = IdleBehaviorAction::Stand;
    result.bored = bored;
    result.actionSeconds = bored ? IdleBoredSeconds : IdleStandSeconds;
    result.idleDecisionSeconds = result.actionSeconds;
    return result;
}

GameplayActorService::InactiveFidgetResult GameplayActorService::resolveInactiveFidget(
    uint32_t actorId,
    uint32_t idleDecisionCount) const
{
    InactiveFidgetResult result = {};
    result.nextDecisionCount = idleDecisionCount + 1;

    const uint32_t decisionSeed = mixActorDecisionSeed(actorId, idleDecisionCount, 0x7f4a7c15u);
    result.shouldFidget = (decisionSeed % 100u) < InactiveFidgetChancePercent;
    return result;
}

GameplayActorService::IdleBehaviorResult GameplayActorService::resolveIdleBehavior(
    uint32_t actorId,
    uint32_t idleDecisionCount,
    float preciseX,
    float preciseY,
    float homePreciseX,
    float homePreciseY,
    float currentYawRadians,
    bool currentlyWalking,
    float wanderRadius,
    float moveSpeed) const
{
    IdleBehaviorResult result = idleStandBehavior(false);
    result.nextDecisionCount = idleDecisionCount + 1;

    const uint32_t decisionSeed = mixActorDecisionSeed(actorId, idleDecisionCount, 12345u);

    if ((decisionSeed % 100u) < IdleStandChancePercent)
    {
        return result;
    }

    const float deltaHomeX = homePreciseX - preciseX;
    const float deltaHomeY = homePreciseY - preciseY;
    float homeAngle = std::atan2(deltaHomeY, deltaHomeX);

    if (std::abs(deltaHomeX) <= 0.01f && std::abs(deltaHomeY) <= 0.01f)
    {
        homeAngle = currentYawRadians;
    }

    const float randomAngleOffset =
        ((static_cast<int>(decisionSeed % 257u) - 128) / 256.0f) * (Pi / 4.0f);
    const float proposedYaw = normalizeAngleRadians(homeAngle + randomAngleOffset);

    if (shortestAngleDistanceRadians(proposedYaw, currentYawRadians) > (Pi / 4.0f) && !currentlyWalking)
    {
        result.updateYaw = true;
        result.yawRadians = proposedYaw;
        return result;
    }

    result.action = IdleBehaviorAction::Wander;
    result.updateYaw = true;
    result.yawRadians = proposedYaw;
    result.moveDirectionX = std::cos(proposedYaw);
    result.moveDirectionY = std::sin(proposedYaw);
    const float weightedDistance = std::max(std::abs(deltaHomeX), std::abs(deltaHomeY))
        + 0.5f * std::min(std::abs(deltaHomeX), std::abs(deltaHomeY))
        + static_cast<float>(decisionSeed % 16u) * (wanderRadius / 16.0f);
    result.actionSeconds = moveSpeed > 0.0f ? std::max(0.25f, weightedDistance / (4.0f * moveSpeed)) : 0.0f;
    result.idleDecisionSeconds = 0.0f;

    if (result.actionSeconds <= 0.0f)
    {
        result = idleStandBehavior(false);
        result.nextDecisionCount = idleDecisionCount + 1;
        result.updateYaw = true;
        result.yawRadians = proposedYaw;
    }

    return result;
}

GameplayActorTargetPolicyResult GameplayActorService::resolveActorTargetPolicy(
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
    const int factionRelation =
        m_pMonsterTable != nullptr ? m_pMonsterTable->getRelationBetweenMonsters(actor.monsterId, target.monsterId) : 0;
    const bool hostileByFaction = factionRelation > 0;

    if (!hostileByFaction && !hostileToSummon)
    {
        return result;
    }

    if (hostileToSummon)
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
        || state.darkGraspRemainingSeconds > 0.0f
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
    state.darkGraspRemainingSeconds = 0.0f;
    state.hostileToParty = defaultHostileToParty;
    state.hasDetectedParty = false;
    return hadEffect;
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

    return std::max(0, armorClass);
}
}
