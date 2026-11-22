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
        // The actor the attack that casts the spell was aimed at; an actor-targeted quick cast prefers it.
        std::optional<size_t> preferredActorIndex;
        // The member a cast on a member goes to, already chosen (an upkeep cast: PartySpellSystem::upkeepNeed), and
        // the session's player it is a member of when it is another player's character (coopCharacterTarget).
        std::optional<size_t> characterTargetIndex;
        std::optional<PlayerId> characterTargetPlayer;
    };

    // Whom a spell on a character goes to in a co-op session, where every player has one character. Nothing
    // outside one (the callers' own rules stand).
    // - `explicitCast` (the spellbook, a spell's key): the player whose body the view is pointed at within reach;
    //   else whoever within reach needs the spell most, the caster included; else the caster.
    // - otherwise (an Attack order, the Upkeep key): whoever within reach needs it most, the caster included;
    //   nothing when nobody does.
    // Needing it: the dead for the raisings, the stoned for Stone to Flesh, the condition a cure cures, a wound
    // for a heal; among several, the lowest share of hit points. Reach is GameSession::aidReach (5120) with a clear line between the two.
    struct CoopCharacterTarget
    {
        size_t memberIndex = 0;
        // None: the caster's own party.
        std::optional<PlayerId> player;
    };
    std::optional<CoopCharacterTarget> coopCharacterTarget(
        GameplayScreenRuntime &runtime,
        size_t casterMemberIndex,
        uint32_t spellId,
        bool explicitCast) const;
    // The lowest share of hit points among the other players' characters within reach that a heal can still
    // help; 1 when there are none.
    float coopLowestOtherHealthShare() const;

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
        // A quick cast found no target; the caller says so or does something else (an attack swings the weapon).
        bool noTarget = false;
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

    // The active member's quick spell, or with `extraSlot` one of MMMerge's four extra quick spells; an empty slot,
    // like an empty quick spell, attacks instead.
    // `barSpellName`, when not empty, names the spell instead (a solo run's action bar slot), with the same path.
    QuickSpellStartResolution tryStartQuickSpellCast(
        GameplayScreenRuntime &runtime,
        const TargetQueries &targetQueries,
        std::optional<size_t> extraSlot = std::nullopt,
        const std::string &barSpellName = std::string());

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

    // The cast's own report (Telepathy's reveal), or "Cast <spell>"; empty for Telekinesis.
    static std::string successStatusText(const std::string &spellName, const PartySpellCastResult &result);

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
    // The standing destructible under the crosshair (or the cursor), where a missile spell flies with no actor there.
    static std::optional<bx::Vec3> resolveCursorDestructiblePoint(
        const TargetQueries &targetQueries,
        IGameplayWorldRuntime &worldRuntime);
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
