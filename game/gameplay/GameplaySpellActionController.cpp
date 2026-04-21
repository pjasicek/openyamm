#include "game/gameplay/GameplaySpellActionController.h"

#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/tables/SpellTable.h"

namespace OpenYAMM::Game
{
GameplaySpellActionController::SpellActionResult GameplaySpellActionController::tryBeginQuickSpellCast(
    GameplayScreenRuntime &runtime,
    GameplaySpellService &spellService,
    const TargetQueries &targetQueries)
{
    const GameplaySpellService::QuickSpellStartResolution resolution =
        spellService.tryStartQuickSpellCast(runtime, targetQueries);

    if (resolution.disposition == GameplaySpellService::QuickSpellStartDisposition::AttackFallback)
    {
        return SpellActionResult::AttackFallback;
    }

    if (resolution.disposition == GameplaySpellService::QuickSpellStartDisposition::CastStarted)
    {
        return SpellActionResult::CastStarted;
    }

    return SpellActionResult::Failed;
}

GameplaySpellActionController::AttackCastResult GameplaySpellActionController::tryBeginAttackCast(
    GameplayScreenRuntime &runtime,
    GameplaySpellService &spellService,
    size_t casterMemberIndex,
    const std::string &attackSpellName,
    const TargetQueries &targetQueries)
{
    if (attackSpellName.empty())
    {
        return {};
    }

    const SpellTable *pSpellTable = runtime.spellTable();
    const SpellEntry *pAttackSpellEntry =
        pSpellTable != nullptr ? pSpellTable->findByName(attackSpellName) : nullptr;

    if (pAttackSpellEntry == nullptr)
    {
        runtime.setStatusBarEvent("Unknown attack spell");
        return {
            .disposition = AttackCastDisposition::Failed,
            .followupUiActive = false,
        };
    }

    const GameplaySpellService::MemberSpellCastResolution castResolution =
        spellService.castSpellFromMember(
            runtime,
            casterMemberIndex,
            uint32_t(pAttackSpellEntry->id),
            pAttackSpellEntry->name,
            true,
            &targetQueries);

    if (!castResolution.castStarted)
    {
        return {
            .disposition = AttackCastDisposition::Failed,
            .followupUiActive = castResolution.followupUiActive,
        };
    }

    return {
        .disposition = AttackCastDisposition::CastStarted,
        .followupUiActive = castResolution.followupUiActive,
    };
}

GameplaySpellActionController::PendingTargetSelectionResult
GameplaySpellActionController::updatePendingTargetSelection(
    GameplayScreenState &screenState,
    GameplayScreenRuntime &runtime,
    GameplaySpellService &spellService,
    const PendingTargetSelectionInput &input)
{
    PendingTargetSelectionResult result = {};
    GameplayScreenState::PendingSpellTargetState &pendingTargetState = screenState.pendingSpellTarget();

    if (!pendingTargetState.active)
    {
        return result;
    }

    if (input.cancelPressed)
    {
        if (!pendingTargetState.cancelLatch)
        {
            spellService.clearPendingTargetSelection(runtime, "Spell canceled");
            result.targetSelectionConsumed = true;
        }

        pendingTargetState.cancelLatch = true;
        return result;
    }

    pendingTargetState.cancelLatch = false;

    if (!input.confirmPressed)
    {
        pendingTargetState.clickLatch = false;
        return result;
    }

    if (pendingTargetState.clickLatch)
    {
        return result;
    }

    pendingTargetState.clickLatch = true;

    PartySpellCastRequest request = spellService.makePendingTargetSelectionRequest();
    const bool actorTargetAllowed =
        pendingTargetState.targetKind == PartySpellCastTargetKind::Actor
        || pendingTargetState.targetKind == PartySpellCastTargetKind::ActorOrCharacter;
    const bool characterTargetAllowed =
        pendingTargetState.targetKind == PartySpellCastTargetKind::Character
        || pendingTargetState.targetKind == PartySpellCastTargetKind::ActorOrCharacter;

    if (actorTargetAllowed)
    {
        resolvePendingActorTarget(request, input.worldHit, runtime.worldRuntime());
    }

    if (characterTargetAllowed)
    {
        resolvePendingCharacterTarget(request, input.portraitMemberIndex);
    }

    if (pendingTargetState.targetKind == PartySpellCastTargetKind::GroundPoint)
    {
        resolvePendingGroundTarget(
            request,
            input.worldHit,
            runtime.worldRuntime(),
            input.fallbackGroundTargetPoint);
    }

    if (!spellService.validatePendingTargetSelectionRequest(runtime, request))
    {
        return result;
    }

    const GameplaySpellService::PendingTargetResolution resolution =
        spellService.resolvePendingTargetSelectionCast(runtime, request);
    result.castResult = resolution.castResult;

    if (resolution.disposition != GameplaySpellService::PendingTargetResolutionDisposition::CastSucceeded)
    {
        return result;
    }

    spellService.clearPendingTargetSelection(runtime);
    result.castSucceeded = true;
    result.targetSelectionConsumed = true;
    return result;
}

std::optional<bx::Vec3> GameplaySpellActionController::resolveGroundTargetPointForWorldHit(
    const GameplayWorldHit &worldHit,
    const IGameplayWorldRuntime *pWorldRuntime,
    const std::optional<bx::Vec3> &fallbackGroundTargetPoint)
{
    if (!worldHit.hasHit)
    {
        return fallbackGroundTargetPoint;
    }

    if (worldHit.kind == GameplayWorldHitKind::Actor && worldHit.actor)
    {
        const size_t actorIndex = worldHit.actor->actorIndex;

        if (actorIndex != GameplayInvalidWorldIndex && pWorldRuntime != nullptr)
        {
            const std::optional<bx::Vec3> actorTargetPoint = pWorldRuntime->spellActionActorTargetPoint(actorIndex);

            if (actorTargetPoint)
            {
                return actorTargetPoint;
            }
        }

        return worldHit.actor->hitPoint;
    }

    if (worldHit.kind == GameplayWorldHitKind::Ground && worldHit.ground && worldHit.ground->isValid)
    {
        return worldHit.ground->worldPoint;
    }

    if (worldHit.worldItem)
    {
        return worldHit.worldItem->hitPoint;
    }

    if (worldHit.container)
    {
        return fallbackGroundTargetPoint;
    }

    if (worldHit.eventTarget)
    {
        return worldHit.eventTarget->hitPoint;
    }

    if (worldHit.object)
    {
        return worldHit.object->hitPoint;
    }

    return fallbackGroundTargetPoint;
}

bool GameplaySpellActionController::resolvePendingActorTarget(
    PartySpellCastRequest &request,
    const GameplayWorldHit &worldHit,
    const IGameplayWorldRuntime *pWorldRuntime)
{
    if (!worldHit.hasHit
        || worldHit.kind != GameplayWorldHitKind::Actor
        || !worldHit.actor
        || worldHit.actor->actorIndex == GameplayInvalidWorldIndex)
    {
        return false;
    }

    if (pWorldRuntime != nullptr
        && !pWorldRuntime->spellActionActorTargetPoint(worldHit.actor->actorIndex))
    {
        return false;
    }

    request.targetActorIndex = worldHit.actor->actorIndex;
    return true;
}

bool GameplaySpellActionController::resolvePendingCharacterTarget(
    PartySpellCastRequest &request,
    const std::optional<size_t> &portraitMemberIndex)
{
    if (!portraitMemberIndex)
    {
        return false;
    }

    request.targetCharacterIndex = *portraitMemberIndex;
    return true;
}

bool GameplaySpellActionController::resolvePendingGroundTarget(
    PartySpellCastRequest &request,
    const GameplayWorldHit &worldHit,
    const IGameplayWorldRuntime *pWorldRuntime,
    const std::optional<bx::Vec3> &fallbackGroundTargetPoint)
{
    const std::optional<bx::Vec3> groundTargetPoint =
        resolveGroundTargetPointForWorldHit(worldHit, pWorldRuntime, fallbackGroundTargetPoint);

    if (!groundTargetPoint)
    {
        return false;
    }

    request.hasTargetPoint = true;
    request.targetX = groundTargetPoint->x;
    request.targetY = groundTargetPoint->y;
    request.targetZ = groundTargetPoint->z;
    return true;
}
} // namespace OpenYAMM::Game
