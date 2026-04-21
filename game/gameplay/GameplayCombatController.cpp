#include "game/gameplay/GameplayCombatController.h"

#include <algorithm>
#include <cmath>
#include <iostream>
#include <limits>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t KillSpeechChancePercent = 20;

std::optional<GameplayCombatController::ActorCombatInfo> resolveActor(
    const GameplayCombatController::PendingCombatEventContext &context,
    uint32_t actorId)
{
    if (!context.resolveActorById)
    {
        return std::nullopt;
    }

    return context.resolveActorById(actorId);
}

void triggerPortraitFaceAnimation(
    const GameplayCombatController::PresentationCallbacks &presentation,
    size_t memberIndex,
    FaceAnimationId animationId)
{
    if (presentation.triggerPortraitFaceAnimation)
    {
        presentation.triggerPortraitFaceAnimation(memberIndex, animationId);
    }
}

void triggerPortraitFaceAnimationForAllLivingMembers(
    const GameplayCombatController::PresentationCallbacks &presentation,
    FaceAnimationId animationId)
{
    if (presentation.triggerPortraitFaceAnimationForAllLivingMembers)
    {
        presentation.triggerPortraitFaceAnimationForAllLivingMembers(animationId);
    }
}

void playSpeechReaction(
    const GameplayCombatController::PresentationCallbacks &presentation,
    size_t memberIndex,
    SpeechId speechId,
    bool triggerFaceAnimation)
{
    if (presentation.playSpeechReaction)
    {
        presentation.playSpeechReaction(memberIndex, speechId, triggerFaceAnimation);
    }
}

void showCombatStatus(
    const GameplayCombatController::PresentationCallbacks &presentation,
    const std::string &status)
{
    if (presentation.showCombatStatus)
    {
        presentation.showCombatStatus(status);
    }
}

uint32_t animationTicks(const GameplayCombatController::PresentationCallbacks &presentation)
{
    if (presentation.animationTicks)
    {
        return presentation.animationTicks();
    }

    return 0;
}

} // namespace

std::string GameplayCombatController::formatPartyAttackStatusText(
    const std::string &attackerName,
    const std::string &targetName,
    const CharacterAttackResult &attack,
    bool killed)
{
    if (!attack.canAttack)
    {
        return "Target is out of range";
    }

    if (attack.resolvesOnImpact)
    {
        if (!targetName.empty())
        {
            return attackerName + " shoots " + targetName;
        }

        return attack.mode == CharacterAttackMode::Melee ? attackerName + " swings" : attackerName + " shoots";
    }

    if (targetName.empty())
    {
        return attackerName + " swings";
    }

    if (!attack.hit)
    {
        return attackerName + " misses " + targetName;
    }

    if (killed)
    {
        return attackerName + " inflicts " + std::to_string(attack.damage) + " points killing " + targetName;
    }

    if (attack.mode == CharacterAttackMode::Bow
        || attack.mode == CharacterAttackMode::Wand
        || attack.mode == CharacterAttackMode::Blaster)
    {
        return attackerName + " shoots " + targetName + " for " + std::to_string(attack.damage) + " points";
    }

    return attackerName + " hits " + targetName + " for " + std::to_string(attack.damage) + " damage";
}

void GameplayCombatController::handlePartyAttackPresentation(
    const PresentationCallbacks &presentation,
    const PartyAttackPresentation &attack)
{
    if (attack.actionPerformed)
    {
        if (attack.attack.mode == CharacterAttackMode::Melee)
        {
            if (attack.hadMeleeTarget)
            {
                SpeechId speechId =
                    attack.attacked && attack.attack.hit ? SpeechId::AttackHit : SpeechId::AttackMiss;

                if (attack.killed)
                {
                    speechId = attack.targetStrongEnemy ? SpeechId::KillStrongEnemy : SpeechId::KillWeakEnemy;
                }

                triggerPortraitFaceAnimation(
                    presentation,
                    attack.memberIndex,
                    attack.attacked && attack.attack.hit ? FaceAnimationId::AttackHit : FaceAnimationId::AttackMiss);
                playSpeechReaction(presentation, attack.memberIndex, speechId, false);
            }
        }
        else
        {
            triggerPortraitFaceAnimation(presentation, attack.memberIndex, FaceAnimationId::Shoot);
            playSpeechReaction(presentation, attack.memberIndex, SpeechId::Shoot, false);
        }
    }

    showCombatStatus(
        presentation,
        formatPartyAttackStatusText(
            attack.attackerName,
            attack.targetName,
            attack.attack,
            attack.killed));
}

void GameplayCombatController::handlePendingCombatEvents(
    PendingCombatEventContext &context,
    const std::vector<CombatEvent> &events)
{
    for (const CombatEvent &event : events)
    {
        if (event.type == CombatEventType::PartyProjectileActorImpact)
        {
            const Character *pSourceMember = context.party.member(event.sourcePartyMemberIndex);
            const std::optional<ActorCombatInfo> targetActor = resolveActor(context, event.targetActorId);
            const std::string sourceName =
                pSourceMember != nullptr && !pSourceMember->name.empty() ? pSourceMember->name : "party";
            const std::string targetName = targetActor ? targetActor->displayName : "monster";

            if (!event.hit)
            {
                triggerPortraitFaceAnimation(
                    context.presentation,
                    event.sourcePartyMemberIndex,
                    FaceAnimationId::AttackMiss);
                playSpeechReaction(context.presentation, event.sourcePartyMemberIndex, SpeechId::AttackMiss, false);
                showCombatStatus(context.presentation, sourceName + " misses " + targetName);
            }
            else if (event.killed)
            {
                triggerPortraitFaceAnimation(
                    context.presentation,
                    event.sourcePartyMemberIndex,
                    FaceAnimationId::AttackHit);
                SpeechId speechId = SpeechId::AttackHit;

                if ((animationTicks(context.presentation) + event.targetActorId) % 100u < KillSpeechChancePercent)
                {
                    speechId = targetActor && targetActor->maxHp >= 100
                        ? SpeechId::KillStrongEnemy
                        : SpeechId::KillWeakEnemy;
                }

                playSpeechReaction(context.presentation, event.sourcePartyMemberIndex, speechId, false);

                if (event.spellId > 0)
                {
                    showCombatStatus(
                        context.presentation,
                        sourceName + " deals " + std::to_string(event.damage) + " damage killing " + targetName);
                }
                else
                {
                    showCombatStatus(
                        context.presentation,
                        sourceName + " inflicts " + std::to_string(event.damage) + " points killing " + targetName);
                }
            }
            else
            {
                triggerPortraitFaceAnimation(
                    context.presentation,
                    event.sourcePartyMemberIndex,
                    FaceAnimationId::AttackHit);
                playSpeechReaction(context.presentation, event.sourcePartyMemberIndex, SpeechId::AttackHit, false);

                if (event.spellId > 0)
                {
                    showCombatStatus(
                        context.presentation,
                        sourceName + " deals " + std::to_string(event.damage) + " damage to " + targetName);
                }
                else
                {
                    showCombatStatus(
                        context.presentation,
                        sourceName + " shoots " + targetName + " for " + std::to_string(event.damage) + " points");
                }
            }

            if (event.hit
                && event.damage > 0
                && event.spellId == 0
                && pSourceMember != nullptr
                && pSourceMember->vampiricHealFraction > 0.0f)
            {
                context.party.healMember(
                    event.sourcePartyMemberIndex,
                    std::max(1, static_cast<int>(
                        std::round(static_cast<float>(event.damage) * pSourceMember->vampiricHealFraction))));
            }

            continue;
        }

        if (event.type != CombatEventType::MonsterMeleeImpact
            && event.type != CombatEventType::PartyProjectileImpact)
        {
            continue;
        }

        std::string sourceName = "monster";
        uint32_t sourceAttackPreferences = 0;

        const std::optional<ActorCombatInfo> sourceActor = resolveActor(context, event.sourceId);
        if (sourceActor)
        {
            sourceName = sourceActor->displayName;
            sourceAttackPreferences = sourceActor->attackPreferences;
        }

        if (event.sourceId == std::numeric_limits<uint32_t>::max())
        {
            sourceName = event.spellId > 0 ? "event spell" : "event";
        }

        const std::string status = event.type == CombatEventType::MonsterMeleeImpact
            ? sourceName + " hit party for " + std::to_string(event.damage)
            : sourceName
                + (event.spellId > 0 ? " spell hit party for " : " projectile hit party for ")
                + std::to_string(event.damage);

        std::optional<size_t> targetMemberIndex = std::nullopt;

        if (!event.affectsAllParty)
        {
            targetMemberIndex = context.party.chooseMonsterAttackTarget(
                sourceAttackPreferences,
                event.sourceId ^ static_cast<uint32_t>(event.damage) ^ static_cast<uint32_t>(event.spellId));
        }

        Character *pTargetMember = targetMemberIndex ? context.party.member(*targetMemberIndex) : nullptr;
        const bool ignorePhysicalDamage =
            pTargetMember != nullptr
            && pTargetMember->physicalDamageImmune
            && (event.type == CombatEventType::MonsterMeleeImpact || event.spellId == 0);

        if (ignorePhysicalDamage)
        {
            showCombatStatus(context.presentation, "Mistform ignores physical damage");
            continue;
        }

        const bool isPhysicalProjectile =
            event.type == CombatEventType::PartyProjectileImpact && event.spellId == 0;
        const auto adjustedDamageForMember =
            [event, isPhysicalProjectile](const Character &member) -> int
            {
                if (isPhysicalProjectile && member.halfMissileDamage)
                {
                    return std::max(1, (event.damage + 1) / 2);
                }

                return event.damage;
            };
        bool damagedParty = false;
        std::vector<size_t> damagedMemberIndices;

        if (event.affectsAllParty)
        {
            bool wroteStatus = false;

            for (size_t memberIndex = 0; memberIndex < context.party.members().size(); ++memberIndex)
            {
                Character *pMember = context.party.member(memberIndex);

                if (pMember == nullptr || pMember->health <= 0)
                {
                    continue;
                }

                if (pMember->physicalDamageImmune
                    && (event.type == CombatEventType::MonsterMeleeImpact || event.spellId == 0))
                {
                    continue;
                }

                const bool applied = context.party.applyDamageToMember(
                    memberIndex,
                    adjustedDamageForMember(*pMember),
                    wroteStatus ? "" : status);
                damagedParty = applied || damagedParty;

                if (applied)
                {
                    damagedMemberIndices.push_back(memberIndex);
                }

                wroteStatus = wroteStatus || damagedParty;
            }
        }
        else
        {
            const int adjustedDamage =
                pTargetMember != nullptr ? adjustedDamageForMember(*pTargetMember) : event.damage;
            damagedParty = targetMemberIndex
                ? context.party.applyDamageToMember(*targetMemberIndex, adjustedDamage, status)
                : false;

            if (damagedParty && targetMemberIndex.has_value())
            {
                damagedMemberIndices.push_back(*targetMemberIndex);
            }
        }

        if (damagedParty)
        {
            // Physical projectiles use the same armor-impact path as melee hits.
            if (event.type == CombatEventType::MonsterMeleeImpact || isPhysicalProjectile)
            {
                for (size_t memberIndex : damagedMemberIndices)
                {
                    context.party.requestDamageImpactSoundForMember(memberIndex);
                }
            }

            if (event.affectsAllParty)
            {
                triggerPortraitFaceAnimationForAllLivingMembers(context.presentation, FaceAnimationId::DamagedParty);
            }
            else
            {
                triggerPortraitFaceAnimation(context.presentation, *targetMemberIndex, FaceAnimationId::Damaged);
            }

            std::cout << "Party damaged source=" << sourceName
                      << " damage=" << event.damage
                      << " kind="
                      << (event.type == CombatEventType::MonsterMeleeImpact
                              ? "melee"
                              : (event.spellId > 0 ? "spell" : "projectile"))
                      << '\n';
        }
    }
}
} // namespace OpenYAMM::Game
