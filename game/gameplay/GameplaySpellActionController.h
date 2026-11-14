#pragma once

#include "game/gameplay/GameplaySpellService.h"
#include "game/gameplay/GameplayScreenState.h"
#include "game/gameplay/GameplayWorldInteraction.h"
#include "game/party/PartySpellSystem.h"

#include <optional>
#include <string>

#include <bx/math.h>

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;
class IGameplayWorldRuntime;

class GameplaySpellActionController
{
public:
    enum class SpellActionResult
    {
        Failed,
        CastStarted,
        AttackFallback
    };

    enum class AttackCastDisposition
    {
        NotConfigured,
        Failed,
        // No target for the attack spell: the attack swings the weapon instead.
        NoTarget,
        CastStarted
    };

    struct AttackCastResult
    {
        AttackCastDisposition disposition = AttackCastDisposition::NotConfigured;
        bool followupUiActive = false;
    };

    using TargetQueries = GameplaySpellService::TargetQueries;

    struct PendingTargetSelectionInput
    {
        bool cancelPressed = false;
        bool confirmPressed = false;
        std::optional<size_t> portraitMemberIndex;
        GameplayWorldHit worldHit = {};
        std::optional<bx::Vec3> fallbackGroundTargetPoint;
        TargetQueries targetQueries = {};
    };

    struct PendingTargetSelectionResult
    {
        bool castSucceeded = false;
        bool targetSelectionConsumed = false;
        PartySpellCastResult castResult = {};
    };

    // The active member's quick spell, or with `extraSlot` one of MMMerge's four extra quick spells.
    // `barSpellName`: a solo run's action bar spell instead (GameplaySpellService::tryStartQuickSpellCast).
    static SpellActionResult tryBeginQuickSpellCast(
        GameplayScreenRuntime &runtime,
        GameplaySpellService &spellService,
        const TargetQueries &targetQueries,
        std::optional<size_t> extraSlot = std::nullopt,
        const std::string &barSpellName = std::string());

    // A solo run's arms showing a cast of this spell (GameplayScreenRuntime::ViewModelLink): the self or target clip,
    // the school that colours the hand, and the caster's recovery for the spell, which the clip is fitted to. False
    // for a spell the caster cannot name (unknown spell).
    static bool prepareViewModelCast(
        GameplayScreenRuntime &runtime,
        const Character &caster,
        const std::string &spellName);

    static AttackCastResult tryBeginAttackCast(
        GameplayScreenRuntime &runtime,
        GameplaySpellService &spellService,
        size_t casterMemberIndex,
        const std::string &attackSpellName,
        const TargetQueries &targetQueries);

    static PendingTargetSelectionResult updatePendingTargetSelection(
        GameplayScreenState &screenState,
        GameplayScreenRuntime &runtime,
        GameplaySpellService &spellService,
        const PendingTargetSelectionInput &input);

    static std::optional<bx::Vec3> resolveGroundTargetPointForWorldHit(
        const GameplayWorldHit &worldHit,
        const IGameplayWorldRuntime *pWorldRuntime,
        const std::optional<bx::Vec3> &fallbackGroundTargetPoint = std::nullopt);

private:
    static bool resolvePendingActorTarget(
        PartySpellCastRequest &request,
        const GameplayWorldHit &worldHit,
        const IGameplayWorldRuntime *pWorldRuntime);
    static bool resolvePendingCharacterTarget(
        PartySpellCastRequest &request,
        const std::optional<size_t> &portraitMemberIndex);
    static bool resolvePendingGroundTarget(
        PartySpellCastRequest &request,
        const GameplayWorldHit &worldHit,
        const IGameplayWorldRuntime *pWorldRuntime,
        const std::optional<bx::Vec3> &fallbackGroundTargetPoint);
    static bool resolvePendingTelekinesisTarget(
        PartySpellCastRequest &request,
        const GameplayWorldHit &worldHit,
        const IGameplayWorldRuntime *pWorldRuntime);
};
} // namespace OpenYAMM::Game
