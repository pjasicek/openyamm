#include "game/gameplay/GameplayActionController.h"

#include "game/audio/GameAudioSystem.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/gameplay/GameplaySpellService.h"
#include "game/items/ItemEnchantRuntime.h"
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
        .z = actor.position.z + std::max(48.0f, static_cast<float>(actor.height) * 0.6f),
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

CharacterAttackMode choosePartyAttackMode(
    const CharacterAttackProfile &profile,
    bool targetInMeleeRange)
{
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
    attack.spellId = profile.wandSpellId;
    attack.attackSoundHook =
        mode == CharacterAttackMode::Bow
            ? "bow_shot"
            : (mode == CharacterAttackMode::Blaster ? "blaster_shot" : "wand_cast");
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

    if (!actor || actor->isDead || actor->isInvisible)
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
        .isDead = actor->isDead,
        .isInvisible = actor->isInvisible,
        .hostileToParty = actor->hostileToParty,
        .visibleForFallback = actor->visibleForFallback,
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
        if (actor.isDead || actor.isInvisible || !actor.hostileToParty || !actor.visibleForFallback)
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
            .isDead = actor.isDead,
            .isInvisible = actor.isInvisible,
            .hostileToParty = actor.hostileToParty,
            .visibleForFallback = actor.visibleForFallback,
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
    const CharacterAttackResult &attack)
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
            pStats->name,
            pStats->pictureName);
    appliedDamage *= multiplier;
    return appliedDamage;
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

        if (attackCastResult.castStarted && !attackCastResult.followupUiActive)
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
    const CharacterAttackProfile attackProfile =
        GameMechanics::buildCharacterAttackProfile(*pAttacker, config.pItemTable, config.pSpellTable);
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
    bool actionPerformed = false;
    bool attacked = false;
    bool killed = false;
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
            const int appliedDamage = resolveMeleeAppliedDamage(config, *pAttacker, *target, attack);
            const int beforeHp = target->currentHp;
            attacked = config.pWorldRuntime->applyPartyAttackMeleeDamage(
                target->actorIndex,
                appliedDamage,
                toRuntimeWorldPoint(config.partyPosition));

            if (attacked)
            {
                const std::optional<PartyAttackActorFacts> afterTarget =
                    resolveUsableActorTarget(config, target->actorIndex);
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

        if (attack.mode == CharacterAttackMode::Wand
            && attack.spellId > 0
            && config.pWorldRuntime != nullptr)
        {
            attacked = config.pWorldRuntime->castPartyAttackSpell(
                GameplayPartyAttackSpellRequest{
                    .sourcePartyMemberIndex = actingMemberIndex,
                    .spellId = static_cast<uint32_t>(attack.spellId),
                    .skillLevel = attack.skillLevel,
                    .skillMastery = attack.skillMastery,
                    .damage = attack.damage,
                    .attackBonus = attack.attackBonus,
                    .useActorHitChance = true,
                    .source = toRuntimeWorldPoint(config.rangedSource),
                    .target = toRuntimeWorldPoint(rangedTarget),
                });
        }
        else if (config.pWorldRuntime != nullptr)
        {
            attacked = config.pWorldRuntime->spawnPartyAttackProjectile(
                GameplayPartyAttackProjectileRequest{
                    .sourcePartyMemberIndex = actingMemberIndex,
                    .objectId =
                        attack.mode == CharacterAttackMode::Blaster
                            ? config.blasterProjectileObjectId
                            : config.arrowProjectileObjectId,
                    .damage = attack.damage,
                    .attackBonus = attack.attackBonus,
                    .useActorHitChance = true,
                    .source = toRuntimeWorldPoint(config.rangedSource),
                    .target = toRuntimeWorldPoint(rangedTarget),
                });
        }

        actionPerformed = attacked;
    }

    if (actionPerformed)
    {
        playPartyAttackSound(config, *pAttacker, attack);
        party.applyRecoveryToActiveMember(attack.recoverySeconds);
        party.switchToNextReadyMember();
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
