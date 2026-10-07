#include "game/gameplay/GameplayActionController.h"

#include "game/audio/GameAudioSystem.h"
#include "game/gameplay/GameplayFxService.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/gameplay/GameplaySpellService.h"
#include "game/gameplay/TurnBasedCombatRuntime.h"
#include "game/items/ItemEnchantRuntime.h"
#include "game/party/PartySpellSystem.h"
#include "game/StringUtils.h"
#include "game/tables/ItemTable.h"
#include "game/tables/MonsterTable.h"

#include <algorithm>
#include <cmath>
#include <limits>
#include <random>

namespace OpenYAMM::Game
{
namespace
{
constexpr float CharacterMeleeAttackDistance = 407.2f;
constexpr float CharacterRangedAttackDistance = 5120.0f;
constexpr float DragonBreathSourceHeight = 96.0f;
constexpr float PartyMemberProjectileLateralSpacing = 28.0f;
constexpr float ProjectileRightVectorEpsilon = 0.0001f;
constexpr float MeleeContactNormalEpsilon = 0.0001f;

void resetQuickCastRepeatState(GameplayScreenState::QuickSpellState &quickSpellState)
{
    quickSpellState.castRepeatCooldownSeconds = 0.0f;
    quickSpellState.castLatch = false;
    quickSpellState.readyMemberAvailableWhileHeld = false;
}

float distanceBetween(
    const GameplayActionController::WorldPoint &left,
    const GameplayActionController::WorldPoint &right)
{
    const float deltaX = left.x - right.x;
    const float deltaY = left.y - right.y;
    const float deltaZ = left.z - right.z;
    return std::sqrt(deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ);
}

float actorDistanceFromParty(
    const GameplayActionController::PartyAttackActorFacts &actor,
    const GameplayActionController::WorldPoint &partyPosition)
{
    return std::max(0.0f, distanceBetween(actor.position, partyPosition) - static_cast<float>(actor.radius));
}

GameplayActionController::WorldPoint actorRangedTargetPoint(
    const GameplayActionController::PartyAttackActorFacts &actor)
{
    return GameplayActionController::WorldPoint{
        .x = actor.position.x,
        .y = actor.position.y,
        .z = actor.position.z + GameMechanics::actorTargetHeight(actor.height),
    };
}

GameplayWorldPoint toRuntimeWorldPoint(const GameplayActionController::WorldPoint &point)
{
    return GameplayWorldPoint{
        .x = point.x,
        .y = point.y,
        .z = point.z,
    };
}

void queueMeleeHitBloodEffect(
    const GameplayActionController::PartyAttackConfig &config,
    const GameplayActionController::PartyAttackActorFacts &target)
{
    if (config.pRuntime == nullptr
        || !config.pRuntime->settingsSnapshot().meleeHitBloodEffects
        || config.pMonsterTable == nullptr)
    {
        return;
    }

    const MonsterTable::MonsterStatsEntry *pStats = config.pMonsterTable->findStatsById(target.monsterId);
    if (pStats == nullptr || !pStats->bloodSplatOnDeath)
    {
        return;
    }

    const GameplayActionController::WorldPoint center = {
        .x = target.position.x,
        .y = target.position.y,
        .z = target.position.z + static_cast<float>(target.height) * 0.5f,
    };
    const GameplayActionController::WorldPoint sourceNormal = {
        .x = config.rangedSource.x - center.x,
        .y = config.rangedSource.y - center.y,
        .z = config.rangedSource.z - center.z,
    };
    GameplayActionController::WorldPoint normal = sourceNormal;
    GameplayActionController::WorldPoint contact = center;
    bool resolvedVisualContact = false;
    if (config.directTargetActorIndex == target.actorIndex && config.directTargetHitPoint)
    {
        contact = *config.directTargetHitPoint;
        resolvedVisualContact = true;
    }
    else if (config.pWorldRuntime != nullptr)
    {
        const std::optional<GameplayWorldPoint> fallbackContact =
            config.pWorldRuntime->partyAttackActorContactPoint(target.actorIndex, config.fallbackQuery);
        if (fallbackContact)
        {
            contact = {fallbackContact->x, fallbackContact->y, fallbackContact->z};
            resolvedVisualContact = true;
        }
    }

    if (resolvedVisualContact)
    {
        normal = {
            .x = contact.x - center.x,
            .y = contact.y - center.y,
            .z = contact.z - center.z,
        };
    }

    float normalLength = std::sqrt(normal.x * normal.x + normal.y * normal.y + normal.z * normal.z);
    if (!std::isfinite(normalLength) || normalLength <= MeleeContactNormalEpsilon)
    {
        normal = sourceNormal;
        normalLength = std::sqrt(normal.x * normal.x + normal.y * normal.y + normal.z * normal.z);
    }
    if (!std::isfinite(normalLength) || normalLength <= MeleeContactNormalEpsilon)
    {
        return;
    }
    normal.x /= normalLength;
    normal.y /= normalLength;
    normal.z /= normalLength;

    if (!resolvedVisualContact)
    {
        const float contactRadius = std::max(1.0f, static_cast<float>(target.radius));
        contact.x += normal.x * contactRadius;
        contact.y += normal.y * contactRadius;
        contact.z += normal.z * contactRadius;
    }

    config.pRuntime->fxService().queueMeleeHitBloodEffect(
        {contact.x, contact.y, contact.z},
        {normal.x, normal.y, normal.z});
}

float partyMemberProjectileLateralOffset(size_t memberIndex, size_t memberCount)
{
    if (memberCount <= 1 || memberIndex >= memberCount)
    {
        return 0.0f;
    }

    const float centerIndex = (static_cast<float>(memberCount) - 1.0f) * 0.5f;
    return (centerIndex - static_cast<float>(memberIndex)) * PartyMemberProjectileLateralSpacing;
}

GameplayActionController::WorldPoint offsetPartyProjectileSourceForMember(
    const GameplayActionController::PartyAttackConfig &config,
    const GameplayActionController::WorldPoint &target,
    size_t memberIndex,
    size_t memberCount)
{
    const float lateralOffset = partyMemberProjectileLateralOffset(memberIndex, memberCount);

    if (lateralOffset == 0.0f)
    {
        return config.rangedSource;
    }

    float rightX = config.rangedRight.x;
    float rightY = config.rangedRight.y;
    float rightZ = config.rangedRight.z;
    float rightLength = std::sqrt(rightX * rightX + rightY * rightY + rightZ * rightZ);

    if (rightLength <= ProjectileRightVectorEpsilon)
    {
        const float forwardX = target.x - config.rangedSource.x;
        const float forwardY = target.y - config.rangedSource.y;
        const float forwardLength = std::sqrt(forwardX * forwardX + forwardY * forwardY);

        if (forwardLength <= ProjectileRightVectorEpsilon)
        {
            return config.rangedSource;
        }

        rightX = -forwardY / forwardLength;
        rightY = forwardX / forwardLength;
        rightZ = 0.0f;
        rightLength = 1.0f;
    }

    GameplayActionController::WorldPoint source = config.rangedSource;
    source.x += rightX / rightLength * lateralOffset;
    source.y += rightY / rightLength * lateralOffset;
    source.z += rightZ / rightLength * lateralOffset;
    return source;
}

GameplayActionController::WorldPoint dragonBreathSourcePoint(
    const GameplayActionController::WorldPoint &rangedSource,
    const GameplayActionController::PartyAttackConfig &config)
{
    GameplayActionController::WorldPoint source = rangedSource;
    source.z = std::min(source.z, config.partyPosition.z + DragonBreathSourceHeight);
    return source;
}

CharacterAttackMode choosePartyAttackMode(
    const CharacterAttackProfile &profile,
    bool targetInMeleeRange)
{
    if (profile.hasDragonBreath && profile.rangedAttackBonus.has_value())
    {
        return CharacterAttackMode::DragonBreath;
    }

    if (profile.hasBlaster && profile.rangedAttackBonus.has_value())
    {
        return CharacterAttackMode::Blaster;
    }

    if (profile.hasWand && profile.rangedAttackBonus.has_value())
    {
        return CharacterAttackMode::Wand;
    }

    if (targetInMeleeRange)
    {
        return CharacterAttackMode::Melee;
    }

    if (profile.hasBow && profile.rangedAttackBonus.has_value())
    {
        return CharacterAttackMode::Bow;
    }

    return CharacterAttackMode::Melee;
}

CharacterAttackResult buildUntargetedMeleeAttack(const CharacterAttackProfile &profile)
{
    CharacterAttackResult attack = {};
    attack.mode = CharacterAttackMode::Melee;
    attack.canAttack = true;
    attack.hit = false;
    attack.attackBonus = profile.meleeAttackBonus;
    attack.recoverySeconds = profile.meleeRecoverySeconds;
    attack.attackSoundHook = "melee_swing";
    attack.voiceHook = "attack";
    return attack;
}

CharacterAttackResult buildWorldObjectMeleeAttack(
    const CharacterAttackProfile &profile,
    float targetDistance,
    std::mt19937 &rng)
{
    CharacterAttackResult attack = buildUntargetedMeleeAttack(profile);
    attack.hit = true;
    attack.damageType = CombatDamageType::Physical;
    attack.targetDistance = std::max(0.0f, targetDistance);
    const int minimumDamage = std::max(1, profile.meleeMinDamage);
    const int maximumDamage = std::max(minimumDamage, profile.meleeMaxDamage);
    std::uniform_int_distribution<int> damageDistribution(minimumDamage, maximumDamage);
    attack.damage = damageDistribution(rng);
    return attack;
}

CharacterAttackResult buildRangedReleaseAttack(
    CharacterAttackMode mode,
    const CharacterAttackProfile &profile,
    std::mt19937 &rng)
{
    CharacterAttackResult attack = {};
    attack.mode = mode;
    attack.canAttack = profile.rangedAttackBonus.has_value();
    attack.hit = false;
    attack.resolvesOnImpact = true;
    attack.attackBonus = profile.rangedAttackBonus.value_or(profile.meleeAttackBonus);
    attack.recoverySeconds = profile.rangedRecoverySeconds;
    attack.skillLevel = profile.rangedSkillLevel;
    attack.skillMastery = profile.rangedSkillMastery;
    attack.projectileCount = profile.rangedProjectileCount;
    attack.spellId = profile.rangedSpellId;
    attack.attackSoundHook = "wand_cast";

    if (mode == CharacterAttackMode::Bow)
    {
        attack.attackSoundHook = "bow_shot";
    }
    else if (mode == CharacterAttackMode::Blaster)
    {
        attack.attackSoundHook = "blaster_shot";
        attack.damageType = CombatDamageType::Irresistible;
    }
    else if (mode == CharacterAttackMode::DragonBreath)
    {
        attack.damageType = CombatDamageType::Irresistible;
    }

    attack.voiceHook = "attack";

    if (attack.canAttack)
    {
        const int minimumDamage = profile.rangedMinDamage;
        const int maximumDamage = std::max(profile.rangedMinDamage, profile.rangedMaxDamage);
        attack.damage = std::uniform_int_distribution<int>(minimumDamage, maximumDamage)(rng);
    }

    return attack;
}

std::optional<GameplayActionController::PartyAttackActorFacts> resolveUsableActorTarget(
    const GameplayActionController::PartyAttackConfig &config,
    std::optional<size_t> actorIndex)
{
    if (!actorIndex || config.pWorldRuntime == nullptr)
    {
        return std::nullopt;
    }

    const std::optional<GameplayPartyAttackActorFacts> actor =
        config.pWorldRuntime->partyAttackActorFacts(*actorIndex, false);

    if (!actor || !GameplayActionController::isPartyAttackActorTargetable(*actor) || !actor->lineOfSightToParty)
    {
        return std::nullopt;
    }

    return GameplayActionController::PartyAttackActorFacts{
        .actorIndex = actor->actorIndex,
        .monsterId = actor->monsterId,
        .displayName = actor->displayName,
        .position = {
            .x = actor->position.x,
            .y = actor->position.y,
            .z = actor->position.z,
        },
        .radius = actor->radius,
        .height = actor->height,
        .currentHp = actor->currentHp,
        .maxHp = actor->maxHp,
        .effectiveArmorClass = actor->effectiveArmorClass,
        .hourOfPowerPower = actor->hourOfPowerPower,
        .isDead = actor->isDead,
        .isInvisible = actor->isInvisible,
        .hostileToParty = actor->hostileToParty,
        .visibleForFallback = actor->visibleForFallback,
        .lineOfSightToParty = actor->lineOfSightToParty,
    };
}

std::optional<GameplayActionController::PartyAttackActorFacts> chooseFallbackRangedTarget(
    const GameplayActionController::PartyAttackConfig &config)
{
    if (config.pWorldRuntime == nullptr)
    {
        return std::nullopt;
    }

    const std::vector<GameplayPartyAttackActorFacts> actors =
        config.pWorldRuntime->collectPartyAttackFallbackActors(config.fallbackQuery);
    float bestDistance = std::numeric_limits<float>::max();
    std::optional<GameplayActionController::PartyAttackActorFacts> bestActor;

    for (const GameplayPartyAttackActorFacts &actor : actors)
    {
        if (!GameplayActionController::isPartyAttackFallbackCandidate(actor))
        {
            continue;
        }

        const GameplayActionController::PartyAttackActorFacts actionActor{
            .actorIndex = actor.actorIndex,
            .monsterId = actor.monsterId,
            .displayName = actor.displayName,
            .position = {
                .x = actor.position.x,
                .y = actor.position.y,
                .z = actor.position.z,
            },
            .radius = actor.radius,
            .height = actor.height,
            .currentHp = actor.currentHp,
            .maxHp = actor.maxHp,
            .effectiveArmorClass = actor.effectiveArmorClass,
            .hourOfPowerPower = actor.hourOfPowerPower,
            .isDead = actor.isDead,
            .isInvisible = actor.isInvisible,
            .hostileToParty = actor.hostileToParty,
            .visibleForFallback = actor.visibleForFallback,
            .lineOfSightToParty = actor.lineOfSightToParty,
        };
        const float distance = actorDistanceFromParty(actionActor, config.partyPosition);

        if (distance > CharacterRangedAttackDistance)
        {
            continue;
        }

        if (distance < bestDistance)
        {
            bestDistance = distance;
            bestActor = actionActor;
        }
    }

    return bestActor;
}

void playPartyAttackSound(
    const GameplayActionController::PartyAttackConfig &config,
    const Character &attacker,
    const CharacterAttackResult &attack)
{
    if (config.pRuntime == nullptr)
    {
        return;
    }

    if (attack.attackSoundHook == "wand_cast" && attack.spellId > 0)
    {
        return;
    }

    SoundId soundId = SoundId::SwingBlunt01;

    if (attack.attackSoundHook == "bow_shot")
    {
        soundId = SoundId::ShootBow;
    }
    else if (attack.attackSoundHook == "blaster_shot")
    {
        soundId = SoundId::ShootBlaster;
    }
    else
    {
        soundId = GameMechanics::resolveCharacterAttackSoundId(attacker, config.pItemTable, attack.mode);
    }

    GameAudioSystem *pAudioSystem = config.pRuntime->audioSystem();

    if (pAudioSystem == nullptr)
    {
        return;
    }

    pAudioSystem->playCommonSound(
        soundId,
        GameAudioSystem::PlaybackGroup::World,
        GameAudioSystem::WorldPosition{config.rangedSource.x, config.rangedSource.y, config.rangedSource.z});
}

int resolveMeleeAppliedDamage(
    const GameplayActionController::PartyAttackConfig &config,
    const Character &attacker,
    const GameplayActionController::PartyAttackActorFacts &target,
    const CharacterAttackResult &attack,
    std::mt19937 &rng)
{
    int appliedDamage = attack.damage;

    if (config.pMonsterTable == nullptr)
    {
        return appliedDamage;
    }

    const MonsterTable::MonsterStatsEntry *pStats = config.pMonsterTable->findStatsById(target.monsterId);

    if (pStats == nullptr)
    {
        return appliedDamage;
    }

    const int multiplier =
        ItemEnchantRuntime::characterAttackDamageMultiplierAgainstMonster(
            attacker,
            CharacterAttackMode::Melee,
            config.pItemTable,
            config.pSpecialItemEnchantTable,
            pStats->kindFlags);
    ElementalDamageBonuses additionalDamage = ItemEnchantRuntime::characterAttackElementalDamageBonuses(
        attacker,
        CharacterAttackMode::Melee,
        config.pItemTable,
        config.pSpecialItemEnchantTable);
    additionalDamage.fire *= multiplier;
    additionalDamage.air *= multiplier;
    additionalDamage.water *= multiplier;
    additionalDamage.body *= multiplier;
    additionalDamage.light *= multiplier;
    additionalDamage.dark *= multiplier;

    return GameMechanics::resolveMonsterIncomingWeaponDamage(
        appliedDamage * multiplier,
        attack.damageType,
        additionalDamage,
        MonsterDamageResistances{
            .fire = pStats->fireResistance,
            .air = pStats->airResistance,
            .water = pStats->waterResistance,
            .earth = pStats->earthResistance,
            .spirit = pStats->spiritResistance,
            .mind = pStats->mindResistance,
            .body = pStats->bodyResistance,
            .light = pStats->lightResistance,
            .dark = pStats->darkResistance,
            .physical = pStats->physicalResistance,
        },
        target.hourOfPowerPower,
        rng);
}

std::mt19937 buildPartyAttackRng(
    const GameplayActionController::PartyAttackConfig &config,
    size_t actingMemberIndex,
    std::optional<size_t> targetActorIndex)
{
    const uint32_t seed =
        config.randomSeed
        ^ static_cast<uint32_t>((targetActorIndex.value_or(0) + 1) * 2654435761u)
        ^ static_cast<uint32_t>(actingMemberIndex * 40503u);
    return std::mt19937(seed);
}
} // namespace

void GameplayActionController::updateCooldowns(GameplayScreenState &screenState, float deltaSeconds)
{
    if (deltaSeconds <= 0.0f)
    {
        return;
    }

    GameplayScreenState::AttackActionState &attackActionState = screenState.attackActionState();
    GameplayScreenState::QuickSpellState &quickSpellState = screenState.quickSpellState();

    attackActionState.inspectRepeatCooldownSeconds =
        std::max(0.0f, attackActionState.inspectRepeatCooldownSeconds - deltaSeconds);
    quickSpellState.castRepeatCooldownSeconds =
        std::max(0.0f, quickSpellState.castRepeatCooldownSeconds - deltaSeconds);
}

GameplayActionController::QuickCastActionDecision GameplayActionController::updateQuickCastAction(
    GameplayScreenState::QuickSpellState &quickSpellState,
    const QuickCastActionConfig &config)
{
    if (!config.canRunAction)
    {
        resetQuickCastRepeatState(quickSpellState);
        return {};
    }

    bool readyMemberTransitionWhileHeld = false;

    if (config.quickCastPressed)
    {
        readyMemberTransitionWhileHeld =
            !quickSpellState.readyMemberAvailableWhileHeld && config.hasReadyMember;
        quickSpellState.readyMemberAvailableWhileHeld = config.hasReadyMember;
    }
    else
    {
        quickSpellState.readyMemberAvailableWhileHeld = false;
    }

    const bool pressedThisFrame = config.quickCastPressed && !quickSpellState.castLatch;
    const bool repeatReady =
        config.quickCastPressed
        && quickSpellState.castLatch
        && (quickSpellState.castRepeatCooldownSeconds <= 0.0f || readyMemberTransitionWhileHeld);

    if (pressedThisFrame || repeatReady)
    {
        quickSpellState.attackFallbackRequested = false;
        quickSpellState.castLatch = true;
        quickSpellState.castRepeatCooldownSeconds = HeldActionRepeatDebounceSeconds;
        return QuickCastActionDecision{
            .shouldBeginQuickCast = true,
        };
    }

    if (!config.quickCastPressed)
    {
        resetQuickCastRepeatState(quickSpellState);
    }

    return {};
}

void GameplayActionController::applyQuickCastActionResult(
    GameplayScreenState::QuickSpellState &quickSpellState,
    QuickCastActionResult result)
{
    quickSpellState.attackFallbackRequested = result == QuickCastActionResult::AttackFallback;
}

GameplayActionController::AttackActionDecision GameplayActionController::updateAttackAction(
    GameplayScreenState::AttackActionState &attackActionState,
    GameplayScreenState::QuickSpellState &quickSpellState,
    const AttackActionConfig &config)
{
    if (attackActionState.blocksAttackInput(config.attackPressed))
    {
        quickSpellState.attackFallbackRequested = false;
        return {};
    }

    const bool attackTriggeredByQuickCastFallback = quickSpellState.attackFallbackRequested;
    bool readyMemberTransitionWhileHeld = false;

    if (config.attackPressed)
    {
        readyMemberTransitionWhileHeld =
            !attackActionState.readyMemberAvailableWhileHeld && config.hasReadyMember;
        attackActionState.readyMemberAvailableWhileHeld = config.hasReadyMember;
    }
    else
    {
        attackActionState.readyMemberAvailableWhileHeld = false;
    }

    const bool pressedThisFrame =
        (config.attackPressed || attackTriggeredByQuickCastFallback) && !attackActionState.inspectLatch;
    const bool repeatReady =
        (config.attackPressed || attackTriggeredByQuickCastFallback)
        && attackActionState.inspectLatch
        && (attackActionState.inspectRepeatCooldownSeconds <= 0.0f || readyMemberTransitionWhileHeld);

    quickSpellState.attackFallbackRequested = false;

    if (pressedThisFrame || repeatReady)
    {
        attackActionState.inspectLatch = true;
        attackActionState.inspectRepeatCooldownSeconds = HeldActionRepeatDebounceSeconds;

        return AttackActionDecision{
            .shouldAttemptAttack = true,
            .pressedThisFrame = pressedThisFrame,
        };
    }

    if (!config.attackPressed)
    {
        attackActionState.clear();
    }

    return {};
}

GameplayActionController::PartyAttackExecutionResult GameplayActionController::executePartyAttack(
    const PartyAttackConfig &config)
{
    PartyAttackExecutionResult result = {};

    if (config.pParty == nullptr)
    {
        return result;
    }

    Party &party = *config.pParty;
    Character *pAttacker = party.activeMember();

    if ((pAttacker == nullptr || !GameMechanics::canTakeGameplayAction(*pAttacker))
        && party.switchToNextReadyMember())
    {
        pAttacker = party.activeMember();
    }

    if (pAttacker == nullptr || !GameMechanics::canTakeGameplayAction(*pAttacker))
    {
        return result;
    }

    const size_t actingMemberIndex = party.activeMemberIndex();
    result.attempted = true;
    result.actingMemberIndex = actingMemberIndex;
    if (party.hasPartyBuff(PartyBuffId::Invisibility))
    {
        party.clearPartyBuff(PartyBuffId::Invisibility);
    }

    if (!pAttacker->attackSpellName.empty())
    {
        AttackCastResult attackCastResult = {};

        if (config.pRuntime != nullptr && config.pSpellService != nullptr)
        {
            const GameplaySpellActionController::AttackCastResult spellAttackCastResult =
                GameplaySpellActionController::tryBeginAttackCast(
                    *config.pRuntime,
                    *config.pSpellService,
                    actingMemberIndex,
                    pAttacker->attackSpellName,
                    config.targetQueries);
            attackCastResult.castStarted =
                spellAttackCastResult.disposition
                == GameplaySpellActionController::AttackCastDisposition::CastStarted;
            attackCastResult.followupUiActive = spellAttackCastResult.followupUiActive;
        }

        if (attackCastResult.castStarted
            && !attackCastResult.followupUiActive
            && (config.pRuntime == nullptr || !config.pRuntime->turnBasedCombatRuntime().active()))
        {
            party.switchToNextReadyMember();
        }

        return result;
    }

    std::optional<PartyAttackActorFacts> target = resolveUsableActorTarget(config, config.directTargetActorIndex);

    if (!target)
    {
        target = chooseFallbackRangedTarget(config);
    }

    result.targetActorIndex = target ? std::optional<size_t>(target->actorIndex) : std::nullopt;

    const float targetDistance = target ? actorDistanceFromParty(*target, config.partyPosition) : 0.0f;
    const bool targetInMeleeRange = target.has_value() && targetDistance <= CharacterMeleeAttackDistance;
    const bool worldTargetInMeleeRange = config.pWorldRuntime != nullptr
        && config.directTargetBModelIndex.has_value()
        && config.pWorldRuntime->isPartyAttackMeleeBModelTarget(*config.directTargetBModelIndex)
        && config.directWorldTargetDistance <= CharacterMeleeAttackDistance;
    const CharacterAttackTuning attackTuning = config.pRuntime != nullptr
        ? characterAttackTuningFromSettings(config.pRuntime->settingsSnapshot())
        : CharacterAttackTuning{};
    const CharacterAttackProfile attackProfile =
        GameMechanics::buildCharacterAttackProfile(*pAttacker, config.pItemTable, config.pSpellTable, attackTuning);
    const CharacterAttackMode attackMode = choosePartyAttackMode(attackProfile, targetInMeleeRange);
    std::mt19937 rng = buildPartyAttackRng(config, actingMemberIndex, result.targetActorIndex);
    CharacterAttackResult attack = {};

    if (attackMode == CharacterAttackMode::Melee && target && targetInMeleeRange)
    {
        attack = GameMechanics::resolveCharacterAttackAgainstArmorClass(
            *pAttacker,
            config.pItemTable,
            config.pSpellTable,
            target->effectiveArmorClass,
            targetDistance,
            rng,
            attackTuning);
    }
    else if (attackMode == CharacterAttackMode::Melee && worldTargetInMeleeRange)
    {
        attack = buildWorldObjectMeleeAttack(
            attackProfile,
            config.directWorldTargetDistance,
            rng);
    }
    else if (attackMode == CharacterAttackMode::Melee)
    {
        attack = buildUntargetedMeleeAttack(attackProfile);
    }
    else
    {
        attack = buildRangedReleaseAttack(attackMode, attackProfile, rng);
    }

    result.attack = attack;

    if (attack.canAttack && attack.mode != CharacterAttackMode::Melee
        && pAttacker->conditions.test(static_cast<size_t>(CharacterCondition::Weak)))
    {
        attack.damage /= 2;
        result.attack = attack;
    }

    bool actionPerformed = false;
    bool attacked = false;
    bool killed = false;
    std::optional<int> appliedMeleeDamage;
    const bool hadMeleeTarget = target.has_value() && targetInMeleeRange;

    if (attack.mode == CharacterAttackMode::Melee)
    {
        actionPerformed = attack.canAttack;

        if (target
            && targetInMeleeRange
            && attack.hit
            && attack.damage > 0
            && config.pWorldRuntime != nullptr)
        {
            const int appliedDamage = resolveMeleeAppliedDamage(config, *pAttacker, *target, attack, rng);
            appliedMeleeDamage = appliedDamage;
            const int beforeHp = target->currentHp;
            queueMeleeHitBloodEffect(config, *target);
            attacked = config.pWorldRuntime->applyPartyAttackMeleeDamage(
                target->actorIndex,
                appliedDamage,
                toRuntimeWorldPoint(config.partyPosition));

            if (attacked)
            {
                config.pWorldRuntime->applyPartyAttackMeleeEffects(
                    target->actorIndex,
                    attack,
                    toRuntimeWorldPoint(config.partyPosition));

                const std::optional<GameplayPartyAttackActorFacts> afterTarget =
                    config.pWorldRuntime->partyAttackActorFacts(target->actorIndex, false);
                killed = beforeHp > 0 && afterTarget && afterTarget->currentHp <= 0;

                if (pAttacker->vampiricHealFraction > 0.0f && appliedDamage > 0)
                {
                    party.healMember(
                        actingMemberIndex,
                        std::max(1, static_cast<int>(std::round(
                            static_cast<float>(appliedDamage) * pAttacker->vampiricHealFraction))));
                }

                if (config.pWorldRuntime != nullptr)
                {
                    config.pWorldRuntime->refreshWorldHover(config.worldInspectionRefreshRequest);
                }
            }
        }
        else if (worldTargetInMeleeRange
            && config.directTargetBModelIndex
            && attack.hit
            && attack.damage > 0
            && config.pWorldRuntime != nullptr)
        {
            appliedMeleeDamage = attack.damage;
            attacked = config.pWorldRuntime->applyPartyAttackMeleeBModelDamage(
                *config.directTargetBModelIndex,
                attack.damage);
        }
    }
    else if (attack.canAttack)
    {
        WorldPoint rangedTarget = config.defaultRangedTarget;

        if (target)
        {
            rangedTarget = actorRangedTargetPoint(*target);
        }
        else if (config.hasRayRangedTarget)
        {
            rangedTarget = config.rayRangedTarget;
        }

        const WorldPoint rangedSource = offsetPartyProjectileSourceForMember(
            config,
            rangedTarget,
            actingMemberIndex,
            party.members().size());

        if (attack.mode == CharacterAttackMode::DragonBreath)
        {
            if (attack.spellId > 0 && config.pWorldRuntime != nullptr)
            {
                const WorldPoint source = dragonBreathSourcePoint(rangedSource, config);
                attacked = config.pWorldRuntime->castPartySpellProjectile(
                    GameplayPartySpellProjectileRequest{
                        .casterMemberIndex = static_cast<uint32_t>(actingMemberIndex),
                        .spellId = static_cast<uint32_t>(attack.spellId),
                        .skillLevel = attack.skillLevel,
                        .skillMastery = static_cast<SkillMastery>(attack.skillMastery),
                        .damage = attack.damage,
                        .damageType = GameMechanics::spellCombatDamageType(
                            static_cast<uint32_t>(attack.spellId),
                            config.pSpellTable),
                        .sourceX = source.x,
                        .sourceY = source.y,
                        .sourceZ = source.z,
                        .targetX = rangedTarget.x,
                        .targetY = rangedTarget.y,
                        .targetZ = rangedTarget.z,
                        .effectSoundIdOverride = static_cast<uint32_t>(SoundId::DragonBreath),
                        .impactSoundIdOverride = static_cast<uint32_t>(SoundId::DragonBreathImpact),
                        .turnBasedPendingAction =
                            config.pRuntime != nullptr && config.pRuntime->turnBasedCombatRuntime().active(),
                    });
            }
        }
        else if (attack.mode == CharacterAttackMode::Wand)
        {
            if (attack.spellId > 0 && config.pSpellTable != nullptr && config.pWorldRuntime != nullptr)
            {
                PartySpellCastRequest spellRequest = {};
                spellRequest.casterMemberIndex = actingMemberIndex;
                spellRequest.spellId = static_cast<uint32_t>(attack.spellId);
                spellRequest.quickCast = true;
                spellRequest.targetActorIndex = target ? std::optional<size_t>(target->actorIndex) : std::nullopt;
                spellRequest.hasTargetPoint = true;
                spellRequest.targetX = rangedTarget.x;
                spellRequest.targetY = rangedTarget.y;
                spellRequest.targetZ = rangedTarget.z;
                spellRequest.skillLevelOverride = attack.skillLevel;
                spellRequest.skillMasteryOverride = static_cast<SkillMastery>(attack.skillMastery);
                // Wands cast at fixed wand power; the spell mastery gate is for learned spell casting.
                spellRequest.bypassRequiredMastery = true;
                spellRequest.spendMana = false;
                spellRequest.applyRecovery = false;

                const PartySpellCastResult spellResult =
                    PartySpellSystem::castSpell(party, *config.pWorldRuntime, *config.pSpellTable, spellRequest);
                attacked = spellResult.status == PartySpellCastStatus::Succeeded;

                if (attacked)
                {
                    config.pWorldRuntime->applyPendingSpellCastWorldEffects(spellResult);
                    party.consumeEquippedWandCharge(actingMemberIndex);
                }
            }
        }
        else if (config.pWorldRuntime != nullptr)
        {
            uint32_t projectileObjectId = config.arrowProjectileObjectId;
            const ItemDefinition *pRangedWeapon = config.pItemTable != nullptr
                ? config.pItemTable->get(pAttacker->equipment.bow)
                : nullptr;

            if (pRangedWeapon != nullptr && canonicalSkillName(pRangedWeapon->skillGroup) == "Throwing")
            {
                projectileObjectId = toLowerCopy(pRangedWeapon->unidentifiedName).find("axe") != std::string::npos
                    ? config.throwingAxeProjectileObjectId
                    : config.throwingDaggerProjectileObjectId;
            }

            GameplayPartyAttackProjectileRequest projectileRequest = {
                .sourcePartyMemberIndex = actingMemberIndex,
                .objectId =
                    attack.mode == CharacterAttackMode::Blaster
                        ? config.blasterProjectileObjectId
                        : projectileObjectId,
                .impactObjectId = attack.mode == CharacterAttackMode::Blaster
                    ? config.blasterProjectileObjectId + 1 : 0,
                .damage = attack.damage,
                .attackBonus = attack.attackBonus,
                .useActorHitChance = true,
                .damageType = attack.damageType,
                .source = toRuntimeWorldPoint(rangedSource),
                .target = toRuntimeWorldPoint(rangedTarget),
                .turnBasedPendingAction =
                    config.pRuntime != nullptr && config.pRuntime->turnBasedCombatRuntime().active(),
            };
            attacked = config.pWorldRuntime->spawnPartyAttackProjectile(projectileRequest);

            for (uint8_t projectileIndex = 1; projectileIndex < attack.projectileCount; ++projectileIndex)
            {
                const WorldPoint secondSource = offsetPartyProjectileSourceForMember(
                    config,
                    rangedTarget,
                    actingMemberIndex + projectileIndex,
                    party.members().size() + attack.projectileCount - 1);
                projectileRequest.source = toRuntimeWorldPoint(secondSource);
                attacked = config.pWorldRuntime->spawnPartyAttackProjectile(projectileRequest) || attacked;
            }
        }

        actionPerformed = attacked;
    }

    if (actionPerformed)
    {
        const EquipmentSlot weaponSlot = attack.mode == CharacterAttackMode::Melee
            ? EquipmentSlot::MainHand
            : EquipmentSlot::Bow;
        EquippedItemRuntimeState *pWeaponRuntime = party.equippedItemRuntimeMutable(actingMemberIndex, weaponSlot);
        bool equippedStateChanged = false;

        if (pWeaponRuntime != nullptr
            && !pWeaponRuntime->broken
            && pAttacker->equippedItemEffectFlags.contains("BreakAfterFirstAttack"))
        {
            pWeaponRuntime->broken = true;
            equippedStateChanged = true;
        }

        if (pWeaponRuntime != nullptr
            && !pWeaponRuntime->broken
            && pAttacker->equippedItemEffectFlags.contains("BreakChance2SelfDamage")
            && std::uniform_int_distribution<int>(0, 99)(rng) < 2)
        {
            pWeaponRuntime->broken = true;
            party.applyDamageToMember(
                actingMemberIndex,
                std::max(1, pAttacker->maxHealth / 10),
                "The weapon backfires");
            equippedStateChanged = true;
        }

        if (attack.hit
            && !attack.stunTarget
            && pAttacker->equippedItemEffectFlags.contains("SelfKnockoutOnFailedStun70")
            && std::uniform_int_distribution<int>(0, 99)(rng) < 70)
        {
            party.applyMemberCondition(actingMemberIndex, CharacterCondition::Unconscious);
        }

        if (equippedStateChanged)
        {
            party.refreshDerivedState();
        }

        playPartyAttackSound(config, *pAttacker, attack);

        if (config.pRuntime != nullptr && config.pRuntime->turnBasedCombatRuntime().active())
        {
            config.pRuntime->turnBasedCombatRuntime().storeMemberTurnRecovery(
                actingMemberIndex,
                attack.recoverySeconds);
        }
        else
        {
            party.applyRecoveryToActiveMember(attack.recoverySeconds);
            party.switchToNextReadyMember();
        }
    }

    std::string targetName;

    if (!(attack.mode == CharacterAttackMode::Melee && !targetInMeleeRange) && target)
    {
        targetName = !config.directTargetName.empty() ? config.directTargetName : target->displayName;
    }

    GameplayCombatController::handlePartyAttackPresentation(
        config.pRuntime,
        GameplayCombatController::PartyAttackPresentation{
            .memberIndex = actingMemberIndex,
            .attackerName = pAttacker->name,
            .targetName = targetName,
            .attack = attack,
            .appliedDamage = appliedMeleeDamage,
            .actionPerformed = actionPerformed,
            .attacked = attacked,
            .hadMeleeTarget = hadMeleeTarget,
            .killed = killed,
            .targetStrongEnemy = target.has_value() && target->maxHp >= 100,
        });

    if (config.pWorldRuntime != nullptr)
    {
        config.pWorldRuntime->recordPartyAttackWorldResult(result.targetActorIndex, attacked, actionPerformed);
    }

    result.actionPerformed = actionPerformed;
    result.attacked = attacked;
    result.killed = killed;
    result.attack = attack;
    return result;
}
} // namespace OpenYAMM::Game
