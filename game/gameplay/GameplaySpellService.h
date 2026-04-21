#pragma once

#include "game/party/PartySpellSystem.h"

#include <optional>
#include <string>

#include <bx/math.h>

namespace OpenYAMM::Game
{
class GameSession;
class GameplayScreenRuntime;
class IGameplayWorldRuntime;

class GameplaySpellService
{
public:
    struct TargetQueries
    {
        bool useCrosshairTarget = false;
        float cursorX = 0.0f;
        float cursorY = 0.0f;
        float screenWidth = 0.0f;
        float screenHeight = 0.0f;
    };

    enum class QuickSpellStartDisposition
    {
        Failed,
        AttackFallback,
        CastStarted
    };

    struct QuickSpellStartResolution
    {
        QuickSpellStartDisposition disposition = QuickSpellStartDisposition::Failed;
    };

    struct MemberSpellCastResolution
    {
        bool castStarted = false;
        bool followupUiActive = false;
    };

    enum class SpellRequestDisposition
    {
        Failed,
        CastSucceeded,
        OpenedSelectionUi,
        NeedsTargetSelection
    };

    struct SpellRequestResolution
    {
        SpellRequestDisposition disposition = SpellRequestDisposition::Failed;
        PartySpellCastResult castResult = {};
    };

    explicit GameplaySpellService(GameSession &session);

    QuickSpellStartResolution tryStartQuickSpellCast(
        GameplayScreenRuntime &runtime,
        const TargetQueries &targetQueries);

    MemberSpellCastResolution castSpellFromMember(
        GameplayScreenRuntime &runtime,
        size_t casterMemberIndex,
        uint32_t spellId,
        const std::string &spellName,
        bool quickCast = false,
        const TargetQueries *pTargetQueries = nullptr);

    bool tryCastSpellFromMember(
        GameplayScreenRuntime &runtime,
        size_t casterMemberIndex,
        uint32_t spellId,
        const std::string &spellName,
        bool quickCast = false,
        const TargetQueries *pTargetQueries = nullptr);

    bool tryPrepareQuickCastRequest(
        GameplayScreenRuntime &runtime,
        PartySpellCastRequest &request,
        const std::string &spellName,
        const TargetQueries &targetQueries) const;

    SpellRequestResolution resolveSpellRequest(
        GameplayScreenRuntime &runtime,
        const PartySpellCastRequest &request,
        const std::string &spellName);

    enum class PendingTargetResolutionDisposition
    {
        Failed,
        CastSucceeded,
        NeedsTargetSelection
    };

    struct PendingTargetResolution
    {
        PendingTargetResolutionDisposition disposition = PendingTargetResolutionDisposition::Failed;
        PartySpellCastResult castResult = {};
    };

    void armPendingTargetSelection(
        GameplayScreenRuntime &runtime,
        const PartySpellCastRequest &request,
        PartySpellCastTargetKind targetKind,
        const std::string &spellName) const;

    void clearPendingTargetSelection(
        GameplayScreenRuntime &runtime,
        const std::string &statusText = {}) const;

    PartySpellCastRequest makePendingTargetSelectionRequest() const;

    std::string pendingTargetSelectionPromptText(bool includeControls = false) const;

    void showPendingTargetSelectionPrompt(
        GameplayScreenRuntime &runtime,
        bool includeControls = false,
        float durationSeconds = 4.0f) const;

    bool validatePendingTargetSelectionRequest(
        GameplayScreenRuntime &runtime,
        const PartySpellCastRequest &request) const;

    PendingTargetResolution resolvePendingTargetSelectionCast(
        GameplayScreenRuntime &runtime,
        const PartySpellCastRequest &request) const;

    PartySpellCastResult castSpell(
        GameplayScreenRuntime &runtime,
        const PartySpellCastRequest &request) const;

    void applySuccessFeedback(
        GameplayScreenRuntime &runtime,
        const PartySpellCastRequest &request,
        const std::string &spellName,
        const PartySpellCastResult &result) const;

    void applyFailureFeedback(
        GameplayScreenRuntime &runtime,
        const PartySpellCastRequest &request,
        const PartySpellCastResult &result) const;

private:
    static bool tryResolveQuickCastRequest(
        GameplayScreenRuntime &runtime,
        PartySpellCastRequest &request,
        const PartySpellDescriptor &descriptor,
        const TargetQueries &targetQueries);
    static std::optional<bx::Vec3> resolveCursorTargetPoint(
        const TargetQueries &targetQueries,
        const IGameplayWorldRuntime *pWorldRuntime);
    static bool tryValidateCasterForGameplayCast(GameplayScreenRuntime &runtime, size_t casterMemberIndex);
    static bool isQuickCastable(const PartySpellDescriptor &descriptor);
    static bool requiresTargetSelection(const PartySpellCastResult &result);
    static bool tryOpenSelectionUi(
        GameplayScreenRuntime &runtime,
        const PartySpellCastRequest &request,
        const std::string &spellName,
        const PartySpellCastResult &result);

    GameSession &m_session;
};
}
