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

    static SpellActionResult tryBeginQuickSpellCast(
        GameplayScreenRuntime &runtime,
        GameplaySpellService &spellService,
        const TargetQueries &targetQueries);

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
};
} // namespace OpenYAMM::Game
