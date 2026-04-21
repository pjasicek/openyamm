#pragma once

#include "game/gameplay/GameplaySpellService.h"
#include "game/gameplay/GameplayScreenState.h"
#include "game/gameplay/GameplayWorldInteraction.h"
#include "game/party/PartySpellSystem.h"

#include <functional>
#include <optional>
#include <string>

#include <bx/math.h>

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;

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

    struct TargetQueries
    {
        bool useCrosshairTarget = false;
        float cursorX = 0.0f;
        float cursorY = 0.0f;
        float screenWidth = 0.0f;
        float screenHeight = 0.0f;
        std::function<std::optional<size_t>()> resolveHoveredActorIndex;
        std::function<std::optional<size_t>()> resolveClosestVisibleHostileActorIndex;
        std::function<std::optional<bx::Vec3>(size_t actorIndex)> resolveActorTargetPoint;
        std::function<std::optional<bx::Vec3>(float screenX, float screenY)> resolveGroundTargetPoint;
    };

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

    static bool tryResolveQuickCastRequest(
        PartySpellCastRequest &request,
        const PartySpellDescriptor &descriptor,
        const TargetQueries &targetQueries);

    static PendingTargetSelectionResult updatePendingTargetSelection(
        GameplayScreenState &screenState,
        GameplayScreenRuntime &runtime,
        GameplaySpellService &spellService,
        const PendingTargetSelectionInput &input);

    static std::optional<bx::Vec3> resolveGroundTargetPointForWorldHit(
        const GameplayWorldHit &worldHit,
        const TargetQueries &targetQueries,
        const std::optional<bx::Vec3> &fallbackGroundTargetPoint = std::nullopt);

private:
    static std::optional<bx::Vec3> resolveCursorTargetPoint(const TargetQueries &targetQueries);
    static bool resolvePendingActorTarget(
        PartySpellCastRequest &request,
        const GameplayWorldHit &worldHit,
        const TargetQueries &targetQueries);
    static bool resolvePendingCharacterTarget(
        PartySpellCastRequest &request,
        const std::optional<size_t> &portraitMemberIndex);
    static bool resolvePendingGroundTarget(
        PartySpellCastRequest &request,
        const GameplayWorldHit &worldHit,
        const TargetQueries &targetQueries,
        const std::optional<bx::Vec3> &fallbackGroundTargetPoint);
};
} // namespace OpenYAMM::Game
