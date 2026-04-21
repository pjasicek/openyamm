#include "game/gameplay/GameplayActorService.h"

#include "game/StringUtils.h"
#include "game/party/SpellIds.h"
#include "game/tables/MonsterTable.h"
#include "game/tables/SpellTable.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <limits>

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
constexpr float CrowdReangleEngageRange = 1024.0f;
constexpr float Pi = 3.14159265358979323846f;
constexpr float IdleStandSeconds = 1.5f;
constexpr float IdleBoredSeconds = 2.0f;
constexpr uint32_t IdleStandChancePercent = 25u;
constexpr uint32_t InactiveFidgetChancePercent = 5u;
constexpr float ActorMeleeRange = 307.2f;
constexpr float ActorTicksPerSecond = 128.0f;

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

float length2d(float x, float y)
{
    return std::sqrt(x * x + y * y);
}

float length3d(float x, float y, float z)
{
    return std::sqrt(x * x + y * y + z * z);
}

float lengthSquared3d(float x, float y, float z)
{
    return x * x + y * y + z * z;
}

bool isWithinRange3d(float x, float y, float z, float range)
{
    return lengthSquared3d(x, y, z) <= range * range;
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

bool attackAbilityIsSpell(GameplayActorAttackAbility ability)
{
    return ability == GameplayActorAttackAbility::Spell1 || ability == GameplayActorAttackAbility::Spell2;
}

float meleeRangeForCombatTarget(bool targetIsActor)
{
    return targetIsActor ? ActorMeleeRange * 0.5f : ActorMeleeRange;
}

int averageAttackDamage(const GameplayActorService::AttackDamageProfile &profile)
{
    if (profile.diceRolls <= 0 || profile.diceSides <= 0)
    {
        return std::max(0, profile.bonus);
    }

    return profile.diceRolls * (profile.diceSides + 1) / 2 + profile.bonus;
}

int resolveBaseAttackImpactDamage(const GameplayActorService::AttackImpactInput &input)
{
    const int fallbackAttackDamage = std::max(1, input.monsterLevel / 2);
    const int fallbackSpellDamage = std::max(2, input.monsterLevel);

    switch (input.ability)
    {
        case GameplayActorAttackAbility::Attack2:
        {
            const int damage = averageAttackDamage(input.attack2Damage);
            return std::max(1, damage > 0 ? damage : fallbackAttackDamage);
        }
        case GameplayActorAttackAbility::Spell1:
        case GameplayActorAttackAbility::Spell2:
            return fallbackSpellDamage;
        case GameplayActorAttackAbility::Attack1:
        default:
        {
            const int damage = averageAttackDamage(input.attack1Damage);
            return std::max(1, damage > 0 ? damage : fallbackAttackDamage);
        }
    }
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

    if (resolvedSpellId == SpellId::SpiritLash || resolvedSpellId == SpellId::SoulDrinker)
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

GameplayActorService::ActorInitialTimingResult GameplayActorService::resolveActorInitialTiming(
    const ActorInitialTimingInput &input) const
{
    ActorInitialTimingResult result = {};
    result.attackCooldownSeconds =
        input.recoverySeconds * actorDecisionRange(input.actorId, 0, 0x4d595df4u, 0.25f, 1.0f);
    result.idleDecisionSeconds = actorDecisionRange(input.actorId, 0, 0x1f123bb5u, 0.2f, 1.35f);
    return result;
}

bool GameplayActorService::isActorUnavailableForCombat(const ActorCombatAvailabilityInput &input) const
{
    return input.invisible
        || input.dead
        || input.hpDepleted
        || input.dyingState
        || input.deadState;
}

bool GameplayActorService::canActorEnterHitReaction(const ActorHitReactionInput &input) const
{
    return !isActorUnavailableForCombat(input.availability)
        && !input.stunnedState
        && !input.attackingState;
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

bool GameplayActorService::shouldCommitToRangedAbility(const RangedAbilityCommitInput &input) const
{
    if (!input.abilityIsRanged)
    {
        return false;
    }

    if (input.targetEdgeDistance >= 5120.0f)
    {
        return false;
    }

    if (!input.movementAllowed)
    {
        return true;
    }

    const float meleeRange = meleeRangeForCombatTarget(input.targetIsActor);

    if (input.targetEdgeDistance <= meleeRange * 1.15f)
    {
        return false;
    }

    const float gapBeyondMelee = std::max(0.0f, input.targetEdgeDistance - meleeRange);
    float chancePercent = 0.0f;

    if (gapBeyondMelee < 256.0f)
    {
        chancePercent = 15.0f;
    }
    else if (gapBeyondMelee < 640.0f)
    {
        chancePercent = 30.0f;
    }
    else if (gapBeyondMelee < 1280.0f)
    {
        chancePercent = 50.0f;
    }
    else if (gapBeyondMelee < 2560.0f)
    {
        chancePercent = 72.0f;
    }
    else if (gapBeyondMelee < 4096.0f)
    {
        chancePercent = 84.0f;
    }
    else
    {
        chancePercent = 68.0f;
    }

    if (attackAbilityIsSpell(input.ability))
    {
        chancePercent = std::min(95.0f, chancePercent + 10.0f);
    }

    const uint32_t salt =
        input.ability == GameplayActorAttackAbility::Attack2 ? 0x55aa55aau
        : input.ability == GameplayActorAttackAbility::Spell1 ? 0x13579bdfu
        : input.ability == GameplayActorAttackAbility::Spell2 ? 0x2468ace0u
        : 0x7f4a7c15u;
    const float rollPercent =
        actorDecisionUnitFloat(input.actorId, input.attackDecisionCount, salt ^ 0x31415926u) * 100.0f;
    return rollPercent < chancePercent;
}

GameplayActorService::AttackStartResult GameplayActorService::resolveAttackStart(const AttackStartInput &input) const
{
    AttackStartResult result = {};

    const float attackActionSeconds = std::max(0.1f, input.attackAnimationSeconds);
    result.actionSeconds = attackActionSeconds;
    result.attackCooldownSeconds =
        input.abilityIsRanged
        ? input.recoverySeconds + attackActionSeconds
        : input.recoverySeconds;
    result.attackCooldownSeconds *= actorDecisionRange(
        input.actorId,
        input.attackDecisionCount,
        0x0b91f2a3u,
        0.9f,
        1.2f);
    return result;
}

GameplayActorService::AttackImpactResult GameplayActorService::resolveAttackImpact(
    const AttackImpactInput &input) const
{
    AttackImpactResult result = {};
    result.damage = resolveBaseAttackImpactDamage(input);

    if (input.shrinkActive)
    {
        result.damage = std::max(
            1,
            static_cast<int>(std::round(static_cast<float>(result.damage) * input.shrinkDamageMultiplier)));
    }

    if (input.darkGraspActive && input.abilityIsMelee)
    {
        result.damage = std::max(1, (result.damage + 1) / 2);
    }

    if (input.abilityIsRanged)
    {
        result.action = AttackImpactAction::RangedRelease;
        result.shouldSpawnProjectile = input.hasCombatTarget;
        return result;
    }

    if (input.targetIsParty)
    {
        result.action = AttackImpactAction::PartyMeleeImpact;
    }
    else if (input.targetIsActor)
    {
        result.action = AttackImpactAction::ActorMeleeImpact;
    }

    return result;
}

GameplayActorService::CombatTargetResult GameplayActorService::resolveCombatTarget(
    const CombatTargetInput &input) const
{
    CombatTargetResult target = {};
    float bestPriorityDistanceSquared = std::numeric_limits<float>::max();
    const float partySenseRange = partyEngagementRange(input.actorPolicyState);

    if (partySenseRange > 0.0f)
    {
        const float deltaPartyX = input.partyX - input.actorX;
        const float deltaPartyY = input.partyY - input.actorY;
        const float deltaPartyZ = input.partyTargetZ - input.actorTargetZ;
        const bool canSenseParty =
            std::abs(deltaPartyX) <= partySenseRange
            && std::abs(deltaPartyY) <= partySenseRange
            && std::abs(deltaPartyZ) <= partySenseRange
            && isWithinRange3d(deltaPartyX, deltaPartyY, deltaPartyZ, partySenseRange);

        target.partyCanSense = canSenseParty;

        if (canSenseParty)
        {
            const float horizontalDistanceToParty = length2d(deltaPartyX, deltaPartyY);
            const float distanceToParty = length3d(deltaPartyX, deltaPartyY, deltaPartyZ);
            const float edgeDistanceToParty = std::max(
                0.0f,
                distanceToParty - static_cast<float>(input.actorRadius) - input.partyCollisionRadius);
            target.kind = CombatTargetKind::Party;
            target.targetX = input.partyX;
            target.targetY = input.partyY;
            target.targetZ = input.partyTargetZ;
            target.deltaX = deltaPartyX;
            target.deltaY = deltaPartyY;
            target.deltaZ = deltaPartyZ;
            target.horizontalDistanceToTarget = horizontalDistanceToParty;
            target.distanceToTarget = distanceToParty;
            target.edgeDistance = edgeDistanceToParty;
            target.canSense = true;
            bestPriorityDistanceSquared = distanceToParty * distanceToParty;
        }
    }

    if (input.pActorCandidates == nullptr || m_pMonsterTable == nullptr)
    {
        return target;
    }

    for (const CombatTargetCandidate &candidate : *input.pActorCandidates)
    {
        if (candidate.actorIndex == input.actorIndex || candidate.unavailable || !candidate.hasLineOfSight)
        {
            continue;
        }

        const float deltaX = candidate.preciseX - input.actorX;
        const float deltaY = candidate.preciseY - input.actorY;

        if (std::abs(deltaX) > HostilityLongRange || std::abs(deltaY) > HostilityLongRange)
        {
            continue;
        }

        const GameplayActorTargetPolicyResult targetPolicy =
            resolveActorTargetPolicy(input.actorPolicyState, candidate.policyState);

        if (!targetPolicy.canTarget)
        {
            continue;
        }

        const float deltaZ = candidate.targetZ - input.actorTargetZ;
        const float distanceSquaredToCandidate = lengthSquared3d(deltaX, deltaY, deltaZ);

        if (distanceSquaredToCandidate >= bestPriorityDistanceSquared)
        {
            continue;
        }

        if (!isWithinRange3d(deltaX, deltaY, deltaZ, targetPolicy.engagementRange))
        {
            continue;
        }

        const float horizontalDistanceToCandidate = length2d(deltaX, deltaY);
        const float distanceToCandidate = length3d(deltaX, deltaY, deltaZ);
        const float edgeDistance = std::max(
            0.0f,
            distanceToCandidate - static_cast<float>(input.actorRadius) - static_cast<float>(candidate.radius));
        target.kind = CombatTargetKind::Actor;
        target.actorIndex = candidate.actorIndex;
        target.relationToTarget = targetPolicy.relationToTarget;
        target.targetX = candidate.preciseX;
        target.targetY = candidate.preciseY;
        target.targetZ = candidate.targetZ;
        target.deltaX = deltaX;
        target.deltaY = deltaY;
        target.deltaZ = deltaZ;
        target.horizontalDistanceToTarget = horizontalDistanceToCandidate;
        target.distanceToTarget = distanceToCandidate;
        target.edgeDistance = edgeDistance;
        target.canSense = true;
        bestPriorityDistanceSquared = distanceSquaredToCandidate;
    }

    return target;
}

GameplayActorService::ActorPartyProximityResult GameplayActorService::resolveActorPartyProximity(
    const ActorPartyProximityInput &input) const
{
    ActorPartyProximityResult result = {};
    const float nearDistance = std::max(0.0f, input.actorRadius)
        + std::max(0.0f, input.partyCollisionRadius)
        + 16.0f;
    const float verticalReach = std::max(std::max(0.0f, input.actorHeight), 192.0f);

    result.veryNearParty =
        input.horizontalDistanceToParty <= nearDistance
        && std::abs(input.verticalDistanceToParty) <= verticalReach;
    return result;
}

GameplayActorService::CombatEngagementResult GameplayActorService::resolveCombatEngagement(
    const CombatEngagementInput &input) const
{
    CombatEngagementResult result = {};
    result.hostilityType = input.hostilityType;
    result.hasDetectedParty = input.hasDetectedParty;
    result.hasCombatTarget = input.combatTarget.kind != CombatTargetKind::None;
    result.targetIsParty = input.combatTarget.kind == CombatTargetKind::Party;
    result.targetIsActor = input.combatTarget.kind == CombatTargetKind::Actor;
    result.shouldEngageTarget = result.hasCombatTarget && input.combatTarget.canSense;
    result.inMeleeRange = input.combatTarget.edgeDistance <= meleeRangeForCombatTarget(result.targetIsActor);

    if (result.targetIsActor)
    {
        const FriendlyTargetEngagementResult friendlyTargetEngagement = resolveFriendlyTargetEngagement(
            input.actorPolicyState,
            input.hostilityType,
            input.combatTarget.relationToTarget,
            lengthSquared3d(input.combatTarget.deltaX, input.combatTarget.deltaY, input.combatTarget.deltaZ));
        result.promotionRange = friendlyTargetEngagement.promotionRange;
        result.shouldPromoteHostility = friendlyTargetEngagement.shouldPromoteHostility;

        if (friendlyTargetEngagement.shouldPromoteHostility)
        {
            result.hostilityType = 4;
            result.shouldUpdateHostilityType = result.hostilityType != input.hostilityType;
        }

        if (!friendlyTargetEngagement.shouldEngageTarget)
        {
            result.shouldEngageTarget = false;
        }
    }

    if (result.targetIsParty && !input.hasDetectedParty)
    {
        result.hasDetectedParty = true;
        result.shouldPlayPartyAlert = true;
    }
    else if (!result.targetIsParty || !input.combatTarget.partyCanSense)
    {
        result.hasDetectedParty = false;
    }

    result.shouldFlee =
        result.shouldEngageTarget
        && input.combatTarget.distanceToTarget <= HostilityLongRange
        && shouldFleeForAiType(input.aiType, input.currentHp, input.maxHp);
    result.friendlyNearParty =
        !result.shouldEngageTarget
        && !input.hostileToParty
        && input.partyIsVeryNearActor;
    return result;
}

GameplayActorService::CombatAbilityDecisionResult GameplayActorService::resolveCombatAbilityDecision(
    const CombatAbilityDecisionInput &input) const
{
    CombatAbilityDecisionResult result = {};
    result.nextAttackDecisionCount = input.attackDecisionCount;

    GameplayActorAttackAbility chosenAbility = GameplayActorAttackAbility::Attack1;

    if (input.chooseRandomAbility)
    {
        const GameplayActorAttackChoiceResult attackChoice =
            chooseAttackAbility(
                input.actorId,
                input.attackDecisionCount,
                input.hasSpell1,
                input.spell1UseChance,
                input.hasSpell2,
                input.spell2UseChance,
                input.attack2Chance);
        result.nextAttackDecisionCount = attackChoice.nextDecisionCount;
        chosenAbility = attackChoice.ability;
    }

    GameplayActorAttackConstraintState constraintState = input.constraintState;

    if (attackAbilityIsRanged(chosenAbility, constraintState))
    {
        RangedAbilityCommitInput rangedCommitInput = {};
        rangedCommitInput.actorId = input.actorId;
        rangedCommitInput.attackDecisionCount = result.nextAttackDecisionCount;
        rangedCommitInput.ability = chosenAbility;
        rangedCommitInput.abilityIsRanged = true;
        rangedCommitInput.movementAllowed = input.movementAllowed;
        rangedCommitInput.targetIsActor = input.targetIsActor;
        rangedCommitInput.targetEdgeDistance = input.targetEdgeDistance;

        if (!shouldCommitToRangedAbility(rangedCommitInput))
        {
            constraintState.rangedCommitAllowed = false;
        }
    }

    if (input.applyAbilityConstraints)
    {
        chosenAbility = resolveAttackAbilityConstraints(chosenAbility, constraintState);
    }

    const bool rawAbilityIsRanged = attackAbilityIsRanged(chosenAbility, input.constraintState);
    result.ability = chosenAbility;
    result.abilityIsRanged =
        rawAbilityIsRanged
        && !input.constraintState.darkGraspActive
        && !input.constraintState.blindActive;
    result.abilityIsMelee = !rawAbilityIsRanged;
    result.stationaryOrTooCloseForRangedPursuit = !input.movementAllowed || input.inMeleeRange;
    return result;
}

GameplayActorService::CombatEngageDecisionResult GameplayActorService::resolveCombatEngageDecision(
    const CombatEngageDecisionInput &input) const
{
    CombatEngageDecisionResult result = {};
    const bool currentlyPursuingWithMoveDirection =
        input.currentlyPursuing
        && input.actionSeconds > 0.0f
        && (std::abs(input.currentMoveDirectionX) > 0.001f
            || std::abs(input.currentMoveDirectionY) > 0.001f);

    if (input.abilityIsMelee && input.crowdStandActive)
    {
        result.action = CombatEngageDecisionAction::HoldCrowdStand;
        result.preserveCrowdSteering = true;
        return result;
    }

    if (input.abilityIsRanged)
    {
        if (input.attackCooldownReady)
        {
            result.action = CombatEngageDecisionAction::StartRangedAttack;
            return result;
        }

        if (input.stationaryOrTooCloseForRangedPursuit)
        {
            result.action = CombatEngageDecisionAction::StandForRangedBlock;
            return result;
        }

        if (currentlyPursuingWithMoveDirection)
        {
            result.action = CombatEngageDecisionAction::ContinueRangedPursuit;
            return result;
        }

        result.action = CombatEngageDecisionAction::StartRangedPursuit;
        result.pursueMode = PursueActionMode::OffsetShort;
        result.useRecoveryFloorForPursuit = true;
        return result;
    }

    if (input.abilityIsMelee && input.inMeleeRange)
    {
        if (input.attackCooldownReady)
        {
            result.action = CombatEngageDecisionAction::StartMeleeAttack;
            return result;
        }

        result.action = CombatEngageDecisionAction::StandForMeleeCooldown;
        return result;
    }

    result.meleePursuitActive = input.abilityIsMelee;
    result.preserveCrowdSteering = input.abilityIsMelee;

    if (!input.movementAllowed)
    {
        result.action = CombatEngageDecisionAction::StartMeleePursuitWithoutMovement;
        return result;
    }

    if (currentlyPursuingWithMoveDirection)
    {
        result.action = CombatEngageDecisionAction::ContinueMeleePursuit;
        return result;
    }

    result.action = CombatEngageDecisionAction::StartMeleePursuit;
    result.pursueMode =
        input.targetEdgeDistance >= 1024.0f ? PursueActionMode::OffsetWide : PursueActionMode::Direct;
    return result;
}

GameplayActorService::CombatEngageApplicationResult GameplayActorService::resolveCombatEngageApplication(
    const CombatEngageApplicationInput &input) const
{
    CombatEngageApplicationResult result = {};
    result.pursueMode = input.pursueMode;
    result.minimumPursueActionSeconds =
        input.useRecoveryFloorForPursuit ? std::max(0.0f, input.recoverySeconds) : 0.0f;

    if (input.action == CombatEngageDecisionAction::HoldCrowdStand)
    {
        result.state = CombatEngageApplicationState::Standing;
        result.animation = CombatEngageApplicationAnimation::BoredOrStanding;
        result.clearMoveDirection = true;
        return result;
    }

    if (input.action == CombatEngageDecisionAction::StartRangedAttack
        || input.action == CombatEngageDecisionAction::StartMeleeAttack)
    {
        result.state = CombatEngageApplicationState::Attacking;
        result.animation = CombatEngageApplicationAnimation::AttackAbility;
        result.clearMoveDirection = true;
        result.faceTarget = true;
        result.startAttack = true;
        return result;
    }

    if (input.action == CombatEngageDecisionAction::StandForRangedBlock
        || input.action == CombatEngageDecisionAction::StandForMeleeCooldown)
    {
        result.state = CombatEngageApplicationState::Standing;
        result.animation = CombatEngageApplicationAnimation::Standing;
        result.clearMoveDirection = true;
        result.faceTarget = true;
        return result;
    }

    if (input.action == CombatEngageDecisionAction::ContinueRangedPursuit
        || input.action == CombatEngageDecisionAction::ContinueMeleePursuit)
    {
        result.state = CombatEngageApplicationState::Pursuing;
        result.animation = CombatEngageApplicationAnimation::Walking;
        result.useCurrentMoveAsDesired = true;
        return result;
    }

    if (input.action == CombatEngageDecisionAction::StartMeleePursuitWithoutMovement)
    {
        result.state = CombatEngageApplicationState::Pursuing;
        result.animation = CombatEngageApplicationAnimation::Standing;
        result.clearMoveDirection = true;
        return result;
    }

    result.state = CombatEngageApplicationState::Pursuing;
    result.animation = CombatEngageApplicationAnimation::Walking;
    result.startPursueAction = true;
    return result;
}

GameplayActorService::CombatFlowDecisionResult GameplayActorService::resolveCombatFlowDecision(
    const CombatFlowDecisionInput &input) const
{
    CombatFlowDecisionResult result = {};

    if (input.attackInProgress)
    {
        result.action = CombatFlowAction::ContinueAttack;
        return result;
    }

    if (input.blindActive)
    {
        result.action = CombatFlowAction::BlindWander;
        return result;
    }

    if (input.shouldFlee || input.fearActive)
    {
        result.action = CombatFlowAction::Flee;
        return result;
    }

    if (input.shouldEngageTarget)
    {
        result.action = CombatFlowAction::EngageTarget;
        return result;
    }

    if (input.friendlyNearParty)
    {
        result.action = CombatFlowAction::FriendlyNearParty;
        return result;
    }

    result.action = CombatFlowAction::NonCombat;
    return result;
}

GameplayActorService::CombatFlowApplicationResult GameplayActorService::resolveCombatFlowApplication(
    const CombatFlowApplicationInput &input) const
{
    CombatFlowApplicationResult result = {};
    result.actionSeconds = input.actionSeconds;
    result.idleDecisionSeconds = input.idleDecisionSeconds;

    if (input.action == CombatFlowAction::ContinueAttack)
    {
        result.state = CombatFlowApplicationState::Attacking;
        result.animation = CombatFlowApplicationAnimation::Current;
        result.clearMoveDirection = true;
        return result;
    }

    if (input.action == CombatFlowAction::BlindWander)
    {
        result.state = CombatFlowApplicationState::Wandering;
        result.animation = input.movementAllowed
            ? CombatFlowApplicationAnimation::Walking
            : CombatFlowApplicationAnimation::Standing;

        if (std::abs(input.currentMoveDirectionX) < 0.01f
            && std::abs(input.currentMoveDirectionY) < 0.01f)
        {
            result.updateMoveDirection = true;
            result.moveDirectionX = std::cos(input.currentYawRadians);
            result.moveDirectionY = std::sin(input.currentYawRadians);
        }

        return result;
    }

    if (input.action == CombatFlowAction::Flee)
    {
        result.state = CombatFlowApplicationState::Fleeing;
        result.animation = input.movementAllowed
            ? CombatFlowApplicationAnimation::Walking
            : CombatFlowApplicationAnimation::Standing;

        if (input.targetHorizontalDistance > 0.01f)
        {
            result.updateDesiredMove = true;
            result.desiredMoveX = -input.targetDeltaX / input.targetHorizontalDistance;
            result.desiredMoveY = -input.targetDeltaY / input.targetHorizontalDistance;
            result.updateMoveDirection = true;
            result.moveDirectionX = result.desiredMoveX;
            result.moveDirectionY = result.desiredMoveY;
            result.updateYaw = true;
            result.yawRadians = std::atan2(result.desiredMoveY, result.desiredMoveX);
        }

        return result;
    }

    if (input.action == CombatFlowAction::FriendlyNearParty)
    {
        result.state = CombatFlowApplicationState::Standing;
        result.animation = CombatFlowApplicationAnimation::Standing;
        result.clearMoveDirection = true;
        result.clearVelocity = true;
        result.actionSeconds = std::max(input.actionSeconds, 0.25f);
        result.idleDecisionSeconds = std::max(input.idleDecisionSeconds, 0.25f);
        return result;
    }

    return result;
}

GameplayActorService::ActiveActorUpdateSelectionResult GameplayActorService::selectActiveActorUpdates(
    const ActiveActorUpdateSelectionInput &input) const
{
    ActiveActorUpdateSelectionResult result = {};
    result.activeActorMask.assign(input.actorCount, false);

    if (input.pCandidates == nullptr || input.actorCount == 0 || input.maxActiveActors == 0)
    {
        return result;
    }

    std::vector<std::pair<size_t, float>> activeActorDistances;
    activeActorDistances.reserve(input.pCandidates->size());

    for (const ActiveActorUpdateCandidate &candidate : *input.pCandidates)
    {
        if (!candidate.eligible || candidate.actorIndex >= input.actorCount)
        {
            continue;
        }

        if (candidate.distanceToParty <= input.activeRange)
        {
            activeActorDistances.push_back({candidate.actorIndex, candidate.distanceToParty});
        }
    }

    std::stable_sort(
        activeActorDistances.begin(),
        activeActorDistances.end(),
        [](const std::pair<size_t, float> &left, const std::pair<size_t, float> &right)
        {
            return left.second < right.second;
        });

    for (size_t index = 0; index < activeActorDistances.size() && index < input.maxActiveActors; ++index)
    {
        result.activeActorMask[activeActorDistances[index].first] = true;
    }

    return result;
}

GameplayActorService::ActorFrameRouteResult GameplayActorService::resolveActorFrameRoute(
    const ActorFrameRouteInput &input) const
{
    ActorFrameRouteResult result = {};

    if (!input.hasMonsterStats)
    {
        result.action = ActorFrameRouteAction::MissingStats;
        return result;
    }

    result.action = input.selectedForActiveUpdate
        ? ActorFrameRouteAction::Active
        : ActorFrameRouteAction::Inactive;
    return result;
}

GameplayActorService::ActorFrameTimerResult GameplayActorService::advanceActorFrameTimers(
    const ActorFrameTimerInput &input) const
{
    ActorFrameTimerResult result = {};
    const float deltaSeconds = std::max(0.0f, input.deltaSeconds);
    const float recoveryStepSeconds = deltaSeconds / std::max(1.0f, input.slowRecoveryMultiplier);

    result.idleDecisionSeconds = std::max(0.0f, input.idleDecisionSeconds - deltaSeconds);
    result.attackCooldownSeconds = std::max(0.0f, input.attackCooldownSeconds - recoveryStepSeconds);
    result.actionSeconds = std::max(
        0.0f,
        input.actionSeconds - (input.attacking ? recoveryStepSeconds : deltaSeconds));
    result.crowdSideLockRemainingSeconds = std::max(0.0f, input.crowdSideLockRemainingSeconds - deltaSeconds);
    result.crowdRetreatRemainingSeconds = std::max(0.0f, input.crowdRetreatRemainingSeconds - deltaSeconds);
    result.crowdStandRemainingSeconds = std::max(0.0f, input.crowdStandRemainingSeconds - deltaSeconds);
    return result;
}

GameplayActorService::ActorAnimationTickResult GameplayActorService::advanceActorAnimationTick(
    const ActorAnimationTickInput &input) const
{
    ActorAnimationTickResult result = {};
    float tickScale = 1.0f;

    if (input.walking && input.slowActive)
    {
        tickScale = std::clamp(input.slowMoveMultiplier, 0.125f, 1.0f);
    }

    result.tickDelta = std::max(0.0f, input.baseTickDelta) * tickScale;
    return result;
}

GameplayActorService::ActorMoveSpeedResult GameplayActorService::resolveActorMoveSpeed(
    const ActorMoveSpeedInput &input) const
{
    ActorMoveSpeedResult result = {};
    const int rawMoveSpeed = input.configuredMoveSpeed > 0 ? input.configuredMoveSpeed : input.defaultMoveSpeed;
    const float baseMoveSpeed = std::max(1, rawMoveSpeed);

    result.moveSpeed =
        baseMoveSpeed
        * input.slowMoveMultiplier
        * (input.darkGraspActive ? 0.5f : 1.0f);
    return result;
}

GameplayActorService::ActorMovementBlockResult GameplayActorService::resolveActorMovementBlock(
    const ActorMovementBlockInput &input) const
{
    ActorMovementBlockResult result = {};

    if (!input.movementBlocked)
    {
        return result;
    }

    result.zeroVelocity = true;
    result.actionSeconds = input.actionSeconds;

    if (!input.pursuing)
    {
        result.resetMoveDirection = true;
        result.stand = true;
        result.actionSeconds = std::min(input.actionSeconds, 0.25f);
    }

    return result;
}

GameplayActorService::ActorFrameCommitResult GameplayActorService::resolveActorFrameCommit(
    const ActorFrameCommitInput &input) const
{
    ActorFrameCommitResult result = {};

    result.keepCurrentAnimation = input.attackInProgress;
    result.resetAnimationTime = !result.keepCurrentAnimation && input.proposedAnimationChanged;
    result.resetCrowdSteering = !input.preserveCrowdSteering;
    result.applyMovement =
        input.movementAllowed
        && (std::abs(input.desiredMoveX) > 0.001f || std::abs(input.desiredMoveY) > 0.001f);
    return result;
}

GameplayActorService::ActorAttackFrameResult GameplayActorService::resolveActorAttackFrame(
    const ActorAttackFrameInput &input) const
{
    ActorAttackFrameResult result = {};

    if (!input.attacking)
    {
        return result;
    }

    result.attackInProgress = input.actionSeconds > 0.0f;
    result.attackJustCompleted = !result.attackInProgress && !input.impactTriggered;
    return result;
}

GameplayActorService::ActorStatusFrameResult GameplayActorService::resolveActorStatusFrame(
    const ActorStatusFrameInput &input) const
{
    ActorStatusFrameResult result = {};
    result.actionSeconds = input.actionSeconds;

    if (input.currentlyStunned && !input.paralyzeActive)
    {
        result.actionSeconds = std::max(0.0f, input.actionSeconds - std::max(0.0f, input.deltaSeconds));
        result.action = result.actionSeconds <= 0.0f
            ? ActorStatusFrameAction::RecoverFromStun
            : ActorStatusFrameAction::HoldStun;
        return result;
    }

    if (input.paralyzeActive)
    {
        result.action = ActorStatusFrameAction::HoldParalyze;
        result.actionSeconds = 0.0f;
        return result;
    }

    if (input.stunActive)
    {
        result.action = ActorStatusFrameAction::ForceStun;
        result.actionSeconds = std::max(input.actionSeconds, input.stunRemainingSeconds);
        return result;
    }

    return result;
}

GameplayActorService::ActorDeathFrameResult GameplayActorService::resolveActorDeathFrame(
    const ActorDeathFrameInput &input) const
{
    ActorDeathFrameResult result = {};

    if (input.dead)
    {
        result.action = ActorDeathFrameAction::HoldDead;
        return result;
    }

    if (!input.hpDepleted && !input.dying)
    {
        return result;
    }

    if (!input.dying)
    {
        result.action = ActorDeathFrameAction::MarkDead;
        return result;
    }

    result.action = ActorDeathFrameAction::AdvanceDying;
    result.actionSeconds = std::max(0.0f, input.actionSeconds - std::max(0.0f, input.deltaSeconds));
    result.finishedDying = result.actionSeconds <= 0.0f;
    return result;
}

GameplayActorService::PursueActionResult GameplayActorService::resolvePursueAction(
    const PursueActionInput &input) const
{
    PursueActionResult result = {};
    result.nextDecisionCount = input.pursueDecisionCount + 1;

    if (input.distanceToTarget <= 0.01f || input.moveSpeed <= 0.0f)
    {
        return result;
    }

    const uint32_t decisionSeed =
        mixActorDecisionSeed(input.actorId, input.pursueDecisionCount, 0x9e3779b9u);

    result.started = true;
    result.yawRadians = std::atan2(input.deltaTargetY, input.deltaTargetX);
    result.actionSeconds = input.distanceToTarget / input.moveSpeed;

    if (input.mode == PursueActionMode::OffsetShort)
    {
        const float offset = (decisionSeed & 1u) == 0u ? (Pi / 64.0f) : (-Pi / 64.0f);
        result.yawRadians = normalizeAngleRadians(result.yawRadians + offset);
        result.actionSeconds = 0.5f;
    }
    else if (input.mode == PursueActionMode::Direct)
    {
        result.actionSeconds = std::min(result.actionSeconds, 32.0f / ActorTicksPerSecond);
    }
    else
    {
        const float offset = (decisionSeed & 1u) == 0u ? (Pi / 4.0f) : (-Pi / 4.0f);
        result.yawRadians = normalizeAngleRadians(result.yawRadians + offset);
        result.actionSeconds = std::min(result.actionSeconds, 128.0f / ActorTicksPerSecond);
    }

    result.moveDirectionX = std::cos(result.yawRadians);
    result.moveDirectionY = std::sin(result.yawRadians);
    result.actionSeconds = std::max(std::max(0.05f, result.actionSeconds), input.minimumActionSeconds);
    return result;
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

bool GameplayActorService::shouldApplyCrowdSteering(const CrowdSteeringEligibilityInput &input) const
{
    return input.contactedActorCount > 0
        && input.meleePursuitActive
        && input.pursuing
        && !input.actorCanFly
        && !input.inMeleeRange
        && input.targetEdgeDistance <= CrowdReangleEngageRange;
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

GameplayActorService::InactiveActorBehaviorResult GameplayActorService::resolveInactiveActorBehavior(
    const InactiveActorBehaviorInput &input) const
{
    InactiveActorBehaviorResult result = {};
    result.nextIdleDecisionCount = input.idleDecisionCount;
    result.actionSeconds = std::max(0.0f, input.actionSeconds - std::max(0.0f, input.deltaSeconds));
    result.idleDecisionSeconds =
        std::max(0.0f, input.idleDecisionSeconds - std::max(0.0f, input.deltaSeconds));

    if (input.currentAnimationBored && result.actionSeconds > 0.0f)
    {
        result.keepCurrentAnimation = true;
        return result;
    }

    result.shouldSetStandingAnimation = true;

    if (result.idleDecisionSeconds > 0.0f)
    {
        return result;
    }

    result.idleDecisionSeconds = input.decisionIntervalSeconds;

    if (!input.allowFidget)
    {
        return result;
    }

    const InactiveFidgetResult fidgetDecision =
        resolveInactiveFidget(input.actorId, input.idleDecisionCount);
    result.nextIdleDecisionCount = fidgetDecision.nextDecisionCount;

    if (fidgetDecision.shouldFidget)
    {
        result.shouldApplyIdleBehavior = true;
        result.idleBehavior = idleStandBehavior(true);
    }

    return result;
}

GameplayActorService::NonCombatBehaviorResult GameplayActorService::resolveNonCombatBehavior(
    const NonCombatBehaviorInput &input) const
{
    NonCombatBehaviorResult result = {};

    if (input.hostileToParty || input.wanderRadius <= 0.0f)
    {
        result.action = input.actionSeconds <= 0.0f
            ? NonCombatBehaviorAction::ApplyIdleBehavior
            : NonCombatBehaviorAction::Stand;
        result.idleBehavior = idleStandBehavior(false);
        return result;
    }

    const float deltaHomeX = input.homePreciseX - input.preciseX;
    const float deltaHomeY = input.homePreciseY - input.preciseY;
    const float distanceToHome = length2d(deltaHomeX, deltaHomeY);

    if (distanceToHome > input.wanderRadius)
    {
        result.action = NonCombatBehaviorAction::ReturnHome;

        if (distanceToHome > 0.01f)
        {
            result.moveDirectionX = deltaHomeX / distanceToHome;
            result.moveDirectionY = deltaHomeY / distanceToHome;
            result.updateYaw = true;
            result.yawRadians = std::atan2(result.moveDirectionY, result.moveDirectionX);
        }

        return result;
    }

    const bool hasMoveDirection =
        std::abs(input.moveDirectionX) > 0.001f || std::abs(input.moveDirectionY) > 0.001f;

    if (input.actionSeconds > 0.0f && hasMoveDirection)
    {
        result.action = NonCombatBehaviorAction::ContinueMove;
        result.moveDirectionX = input.moveDirectionX;
        result.moveDirectionY = input.moveDirectionY;
        return result;
    }

    if (input.currentlyWandering)
    {
        result.action = NonCombatBehaviorAction::ApplyIdleBehavior;
        result.idleBehavior = idleStandBehavior(false);
        return result;
    }

    if (input.actionSeconds > 0.0f)
    {
        result.action = NonCombatBehaviorAction::Stand;
        return result;
    }

    result.action = NonCombatBehaviorAction::StartIdleBehavior;

    if (!input.allowIdleWander)
    {
        result.idleBehavior = idleStandBehavior(false);
        result.idleBehavior.nextDecisionCount = input.idleDecisionCount + 1;
        return result;
    }

    result.idleBehavior = resolveIdleBehavior(
        input.actorId,
        input.idleDecisionCount,
        input.preciseX,
        input.preciseY,
        input.homePreciseX,
        input.homePreciseY,
        input.currentYawRadians,
        input.currentlyWalking,
        input.wanderRadius,
        input.moveSpeed);
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
