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
    int actorCurrentHp,
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

    if (resolvedSpellId == SpellId::Implosion || resolvedSpellId == SpellId::Blades)
    {
        result.disposition = DirectSpellImpactDisposition::ApplyDamage;
        result.damage = std::max(1, baseDamage);

        if (resolvedSpellId == SpellId::Implosion)
        {
            result.visualKind = DirectSpellImpactVisualKind::ActorCenter;
            result.centerVisual = true;
        }

        return result;
    }

    if (resolvedSpellId == SpellId::SpiritLash
        || resolvedSpellId == SpellId::PrismaticLight
        || resolvedSpellId == SpellId::SoulDrinker)
    {
        result.disposition = DirectSpellImpactDisposition::ApplyDamage;
        result.visualKind = DirectSpellImpactVisualKind::ActorUpperBody;
        result.damage = std::max(1, baseDamage);
        return result;
    }

    if (spellName == "mass distortion")
    {
        result.disposition = DirectSpellImpactDisposition::ApplyDamage;
        result.damage = std::max(
            1,
            static_cast<int>(std::round(static_cast<float>(actorCurrentHp) * (0.25f + 0.02f * skillLevel))));
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

    const int16_t actorRelationMonsterId = actor.relationMonsterId > 0 ? actor.relationMonsterId : actor.monsterId;
    return hostilityRangeForRelation(m_pMonsterTable->getRelationToParty(actorRelationMonsterId));
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
    bool attackingState) const
{
    return !isActorUnavailableForCombat(invisible, dead, hpDepleted, dyingState, deadState)
        && !stunnedState
        && !attackingState;
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
    const int16_t actorRelationMonsterId = actor.relationMonsterId > 0 ? actor.relationMonsterId : actor.monsterId;
    const int16_t targetRelationMonsterId = target.relationMonsterId > 0 ? target.relationMonsterId : target.monsterId;

    if (actor.group != 0 && actor.group == target.group)
    {
        return result;
    }

    const int factionRelation = m_pMonsterTable != nullptr
        ? m_pMonsterTable->getRelationBetweenMonsters(actorRelationMonsterId, targetRelationMonsterId)
        : 0;
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
