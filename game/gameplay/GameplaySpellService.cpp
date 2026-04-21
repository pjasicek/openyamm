#include "game/gameplay/GameplaySpellService.h"

#include "game/app/GameSession.h"
#include "game/audio/GameAudioSystem.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/party/SpellIds.h"

namespace OpenYAMM::Game
{
namespace
{
bool isUtilitySelectionRequest(const PartySpellCastRequest &request)
{
    return request.utilityAction != PartySpellUtilityActionKind::None
        || request.targetInventoryGridX.has_value()
        || request.targetEquipmentSlot.has_value();
}

bool isFollowupSpellUiActive(
    const GameplayScreenState &screenState,
    const GameplayScreenRuntime &runtime)
{
    return screenState.pendingSpellTarget().active || runtime.utilitySpellOverlayReadOnly().active;
}
}

GameplaySpellService::GameplaySpellService(GameSession &session)
    : m_session(session)
{
}

GameplaySpellService::QuickSpellStartResolution GameplaySpellService::tryStartQuickSpellCast(
    GameplayScreenRuntime &runtime,
    const std::function<bool(
        PartySpellCastRequest &,
        const PartySpellDescriptor &)> &worldTargetResolver)
{
    QuickSpellStartResolution resolution = {};

    if (m_session.gameplayScreenState().pendingSpellTarget().active)
    {
        showPendingTargetSelectionPrompt(runtime);
        return resolution;
    }

    IGameplayWorldRuntime *pWorldRuntime = runtime.worldRuntime();
    const bool hasActiveLootView =
        pWorldRuntime != nullptr
        && (pWorldRuntime->activeChestView() != nullptr || pWorldRuntime->activeCorpseView() != nullptr);

    if (runtime.heldInventoryItem().active
        || runtime.characterScreenReadOnly().open
        || runtime.spellbookReadOnly().active
        || runtime.controlsScreenState().active
        || runtime.keyboardScreenState().active
        || runtime.menuScreenState().active
        || runtime.saveGameScreenState().active
        || runtime.loadGameScreenState().active
        || runtime.activeEventDialog().isActive
        || hasActiveLootView)
    {
        runtime.setStatusBarEvent("Finish current action");
        return resolution;
    }

    Party *pParty = runtime.party();

    if (pParty == nullptr)
    {
        return resolution;
    }

    const Character *pCaster = pParty->activeMember();

    if (pCaster == nullptr || !GameMechanics::canSelectInGameplay(*pCaster))
    {
        runtime.setStatusBarEvent("Nobody is in condition");
        return resolution;
    }

    if (pCaster->quickSpellName.empty())
    {
        resolution.disposition = QuickSpellStartDisposition::AttackFallback;
        return resolution;
    }

    const SpellTable *pSpellTable = runtime.spellTable();

    if (pSpellTable == nullptr)
    {
        return resolution;
    }

    const SpellEntry *pSpellEntry = pSpellTable->findByName(pCaster->quickSpellName);

    if (pSpellEntry == nullptr)
    {
        runtime.setStatusBarEvent("Unknown quick spell");
        return resolution;
    }

    if (tryCastSpellFromMember(
            runtime,
            pParty->activeMemberIndex(),
            uint32_t(pSpellEntry->id),
            pSpellEntry->name,
            true,
            worldTargetResolver))
    {
        resolution.disposition = QuickSpellStartDisposition::CastStarted;
    }

    return resolution;
}

GameplaySpellService::MemberSpellCastResolution GameplaySpellService::castSpellFromMember(
    GameplayScreenRuntime &runtime,
    size_t casterMemberIndex,
    uint32_t spellId,
    const std::string &spellName,
    bool quickCast,
    const std::function<bool(PartySpellCastRequest &, const PartySpellDescriptor &)> &worldTargetResolver)
{
    MemberSpellCastResolution resolution = {};
    Party *pParty = runtime.party();

    if (pParty != nullptr)
    {
        const Character *pCaster = pParty->member(casterMemberIndex);

        if (pCaster == nullptr || !pCaster->knowsSpell(spellId))
        {
            runtime.setStatusBarEvent("Spell not learned");
            return resolution;
        }
    }

    PartySpellCastRequest request = {};
    request.casterMemberIndex = casterMemberIndex;
    request.spellId = spellId;

    if (quickCast
        && worldTargetResolver
        && !tryPrepareQuickCastRequest(runtime, request, spellName, worldTargetResolver))
    {
        return resolution;
    }

    resolution.castStarted = runtime.tryCastSpellRequest(request, spellName);
    resolution.followupUiActive =
        resolution.castStarted && isFollowupSpellUiActive(m_session.gameplayScreenState(), runtime);
    return resolution;
}

bool GameplaySpellService::tryCastSpellFromMember(
    GameplayScreenRuntime &runtime,
    size_t casterMemberIndex,
    uint32_t spellId,
    const std::string &spellName,
    bool quickCast,
    const std::function<bool(PartySpellCastRequest &, const PartySpellDescriptor &)> &worldTargetResolver)
{
    return castSpellFromMember(
        runtime,
        casterMemberIndex,
        spellId,
        spellName,
        quickCast,
        worldTargetResolver).castStarted;
}

bool GameplaySpellService::tryPrepareQuickCastRequest(
    GameplayScreenRuntime &runtime,
    PartySpellCastRequest &request,
    const std::string &spellName,
    const std::function<bool(PartySpellCastRequest &, const PartySpellDescriptor &)> &worldTargetResolver) const
{
    const std::optional<PartySpellDescriptor> descriptor = PartySpellSystem::describeSpell(request.spellId);

    if (!descriptor || !isQuickCastable(*descriptor))
    {
        return true;
    }

    request.quickCast = true;

    if (worldTargetResolver(request, *descriptor))
    {
        return true;
    }

    runtime.setStatusBarEvent("No target for " + spellName, 3.0f);
    return false;
}

GameplaySpellService::SpellRequestResolution GameplaySpellService::resolveSpellRequest(
    GameplayScreenRuntime &runtime,
    const PartySpellCastRequest &request,
    const std::string &spellName)
{
    SpellRequestResolution resolution = {};

    if (!tryValidateCasterForGameplayCast(runtime, request.casterMemberIndex))
    {
        return resolution;
    }

    resolution.castResult = castSpell(runtime, request);

    if (resolution.castResult.succeeded())
    {
        applySuccessFeedback(runtime, request, spellName, resolution.castResult);
        resolution.disposition = SpellRequestDisposition::CastSucceeded;
        return resolution;
    }

    if (tryOpenSelectionUi(runtime, request, spellName, resolution.castResult))
    {
        Party *pParty = runtime.party();

        if (pParty != nullptr)
        {
            pParty->setActiveMemberIndex(request.casterMemberIndex);
        }

        resolution.disposition = SpellRequestDisposition::OpenedSelectionUi;
        return resolution;
    }

    if (requiresTargetSelection(resolution.castResult))
    {
        resolution.disposition = SpellRequestDisposition::NeedsTargetSelection;
        return resolution;
    }

    applyFailureFeedback(runtime, request, resolution.castResult);
    return resolution;
}

void GameplaySpellService::armPendingTargetSelection(
    GameplayScreenRuntime &runtime,
    const PartySpellCastRequest &request,
    PartySpellCastTargetKind targetKind,
    const std::string &spellName) const
{
    GameplayScreenState::PendingSpellTargetState &pendingTargetState =
        m_session.gameplayScreenState().pendingSpellTarget();
    pendingTargetState.clear();
    pendingTargetState.active = true;
    pendingTargetState.casterMemberIndex = request.casterMemberIndex;
    pendingTargetState.spellId = request.spellId;
    pendingTargetState.skillLevelOverride = request.skillLevelOverride;
    pendingTargetState.skillMasteryOverride = request.skillMasteryOverride;
    pendingTargetState.spendMana = request.spendMana;
    pendingTargetState.applyRecovery = request.applyRecovery;
    pendingTargetState.targetKind = targetKind;
    pendingTargetState.spellName = spellName;
    showPendingTargetSelectionPrompt(runtime);
}

void GameplaySpellService::clearPendingTargetSelection(
    GameplayScreenRuntime &runtime,
    const std::string &statusText) const
{
    m_session.gameplayScreenState().pendingSpellTarget().clear();

    if (!statusText.empty())
    {
        runtime.setStatusBarEvent(statusText);
    }
}

PartySpellCastRequest GameplaySpellService::makePendingTargetSelectionRequest() const
{
    const GameplayScreenState::PendingSpellTargetState &pendingTargetState =
        m_session.gameplayScreenState().pendingSpellTarget();

    PartySpellCastRequest request = {};
    request.casterMemberIndex = pendingTargetState.casterMemberIndex;
    request.spellId = pendingTargetState.spellId;
    request.skillLevelOverride = pendingTargetState.skillLevelOverride;
    request.skillMasteryOverride = pendingTargetState.skillMasteryOverride;
    request.spendMana = pendingTargetState.spendMana;
    request.applyRecovery = pendingTargetState.applyRecovery;
    return request;
}

std::string GameplaySpellService::pendingTargetSelectionPromptText(bool includeControls) const
{
    const GameplayScreenState::PendingSpellTargetState &pendingTargetState =
        m_session.gameplayScreenState().pendingSpellTarget();

    std::string prompt =
        pendingTargetState.targetKind == PartySpellCastTargetKind::Actor
            ? "Select actor for "
            : pendingTargetState.targetKind == PartySpellCastTargetKind::Character
            ? "Select character for "
            : pendingTargetState.targetKind == PartySpellCastTargetKind::GroundPoint
            ? "Select ground point for "
            : "Select target for ";
    prompt += pendingTargetState.spellName;

    if (includeControls)
    {
        prompt += "  LMB cast  Esc cancel";
    }

    return prompt;
}

void GameplaySpellService::showPendingTargetSelectionPrompt(
    GameplayScreenRuntime &runtime,
    bool includeControls,
    float durationSeconds) const
{
    const GameplayScreenState::PendingSpellTargetState &pendingTargetState =
        m_session.gameplayScreenState().pendingSpellTarget();

    if (!pendingTargetState.active)
    {
        return;
    }

    runtime.setStatusBarEvent(pendingTargetSelectionPromptText(includeControls), durationSeconds);
}

bool GameplaySpellService::validatePendingTargetSelectionRequest(
    GameplayScreenRuntime &runtime,
    const PartySpellCastRequest &request) const
{
    const GameplayScreenState::PendingSpellTargetState &pendingTargetState =
        m_session.gameplayScreenState().pendingSpellTarget();

    bool targetResolved = true;

    switch (pendingTargetState.targetKind)
    {
        case PartySpellCastTargetKind::Actor:
            targetResolved = request.targetActorIndex.has_value();
            break;

        case PartySpellCastTargetKind::Character:
            targetResolved = request.targetCharacterIndex.has_value();
            break;

        case PartySpellCastTargetKind::ActorOrCharacter:
            targetResolved = request.targetActorIndex.has_value() || request.targetCharacterIndex.has_value();
            break;

        case PartySpellCastTargetKind::GroundPoint:
            targetResolved = request.hasTargetPoint;
            break;

        default:
            break;
    }

    if (targetResolved)
    {
        return true;
    }

    showPendingTargetSelectionPrompt(runtime);
    return false;
}

GameplaySpellService::PendingTargetResolution GameplaySpellService::resolvePendingTargetSelectionCast(
    GameplayScreenRuntime &runtime,
    const PartySpellCastRequest &request) const
{
    PendingTargetResolution resolution = {};
    resolution.castResult = castSpell(runtime, request);

    if (resolution.castResult.succeeded())
    {
        const std::string spellName = m_session.gameplayScreenState().pendingSpellTarget().spellName;
        applySuccessFeedback(runtime, request, spellName, resolution.castResult);
        resolution.disposition = PendingTargetResolutionDisposition::CastSucceeded;
        return resolution;
    }

    if (requiresTargetSelection(resolution.castResult))
    {
        showPendingTargetSelectionPrompt(runtime);
        resolution.disposition = PendingTargetResolutionDisposition::NeedsTargetSelection;
        return resolution;
    }

    applyFailureFeedback(runtime, request, resolution.castResult);
    clearPendingTargetSelection(runtime);
    return resolution;
}

bool GameplaySpellService::tryValidateCasterForGameplayCast(GameplayScreenRuntime &runtime, size_t casterMemberIndex)
{
    Party *pParty = runtime.party();

    if (pParty == nullptr)
    {
        return false;
    }

    const Character *pCaster = pParty->member(casterMemberIndex);

    if (pCaster == nullptr || !GameMechanics::canSelectInGameplay(*pCaster))
    {
        runtime.setStatusBarEvent("Nobody is in condition");
        return false;
    }

    return true;
}

PartySpellCastResult GameplaySpellService::castSpell(
    GameplayScreenRuntime &runtime,
    const PartySpellCastRequest &request) const
{
    Party *pParty = runtime.party();
    IGameplayWorldRuntime *pWorldRuntime = runtime.worldRuntime();
    const SpellTable *pSpellTable = runtime.spellTable();

    if (pParty == nullptr || pWorldRuntime == nullptr || pSpellTable == nullptr)
    {
        return {};
    }

    return PartySpellSystem::castSpell(*pParty, *pWorldRuntime, *pSpellTable, request);
}

bool GameplaySpellService::isQuickCastable(const PartySpellDescriptor &descriptor)
{
    if (spellIdFromValue(descriptor.spellId) == SpellId::MeteorShower
        || spellIdFromValue(descriptor.spellId) == SpellId::Starburst)
    {
        return false;
    }

    if (descriptor.targetKind == PartySpellCastTargetKind::None)
    {
        return true;
    }

    if (descriptor.targetKind == PartySpellCastTargetKind::Actor)
    {
        return descriptor.effectKind == PartySpellCastEffectKind::Projectile
            || descriptor.effectKind == PartySpellCastEffectKind::ActorEffect;
    }

    if (descriptor.targetKind == PartySpellCastTargetKind::GroundPoint)
    {
        return descriptor.effectKind == PartySpellCastEffectKind::Projectile
            || descriptor.effectKind == PartySpellCastEffectKind::MultiProjectile
            || descriptor.effectKind == PartySpellCastEffectKind::AreaEffect;
    }

    return false;
}

bool GameplaySpellService::requiresTargetSelection(const PartySpellCastResult &result)
{
    return result.status == PartySpellCastStatus::NeedActorTarget
        || result.status == PartySpellCastStatus::NeedCharacterTarget
        || result.status == PartySpellCastStatus::NeedActorOrCharacterTarget
        || result.status == PartySpellCastStatus::NeedGroundPoint;
}

bool GameplaySpellService::tryOpenSelectionUi(
    GameplayScreenRuntime &runtime,
    const PartySpellCastRequest &request,
    const std::string &spellName,
    const PartySpellCastResult &result)
{
    if (result.status == PartySpellCastStatus::NeedInventoryItemTarget)
    {
        runtime.closeSpellbookOverlay();
        runtime.characterScreen().open = true;
        runtime.characterScreen().dollJewelryOverlayOpen = false;
        runtime.characterScreen().adventurersInnRosterOverlayOpen = false;
        runtime.characterScreen().source = GameplayUiController::CharacterScreenSource::Party;
        runtime.characterScreen().sourceIndex = request.casterMemberIndex;
        runtime.characterScreen().page = GameplayUiController::CharacterPage::Inventory;
        runtime.openUtilitySpellOverlay(
            GameplayUiController::UtilitySpellOverlayMode::InventoryTarget,
            request.spellId,
            request.casterMemberIndex);
        runtime.setStatusBarEvent("Select item for " + spellName, 4.0f);
        return true;
    }

    if (result.status != PartySpellCastStatus::NeedUtilityUi)
    {
        return false;
    }

    runtime.closeSpellbookOverlay();

    if (isSpellId(request.spellId, SpellId::TownPortal))
    {
        if (!runtime.ensureTownPortalDestinationsLoaded())
        {
            runtime.setStatusBarEvent("Town Portal data missing");
            return true;
        }

        runtime.openUtilitySpellOverlay(
            GameplayUiController::UtilitySpellOverlayMode::TownPortal,
            request.spellId,
            request.casterMemberIndex);
        runtime.resetUtilitySpellOverlayInteractionState();
        runtime.setStatusBarEvent("Choose Town Portal destination", 4.0f);
        return true;
    }

    if (isSpellId(request.spellId, SpellId::LloydsBeacon))
    {
        runtime.openUtilitySpellOverlay(
            GameplayUiController::UtilitySpellOverlayMode::LloydsBeacon,
            request.spellId,
            request.casterMemberIndex,
            false);
        runtime.resetUtilitySpellOverlayInteractionState();
        runtime.setStatusBarEvent("Set or recall beacon", 4.0f);
        return true;
    }

    return false;
}

void GameplaySpellService::applySuccessFeedback(
    GameplayScreenRuntime &runtime,
    const PartySpellCastRequest &request,
    const std::string &spellName,
    const PartySpellCastResult &result) const
{
    if (isUtilitySelectionRequest(request))
    {
        runtime.closeUtilitySpellOverlayAfterSpellResolution(request.spellId);
    }

    runtime.triggerPortraitFaceAnimation(request.casterMemberIndex, FaceAnimationId::CastSpell);
    runtime.playSpeechReaction(request.casterMemberIndex, SpeechId::CastSpell, false);
    m_session.gameplayFxService().triggerPortraitSpellFx(result);
    if (result.screenOverlayRequest.has_value())
    {
        m_session.gameplayFxService().triggerGameplayScreenOverlay(*result.screenOverlayRequest);
    }

    if (runtime.audioSystem() != nullptr && runtime.spellTable() != nullptr)
    {
        const SpellEntry *pSpellEntry = runtime.spellTable()->findById(request.spellId);

        if (result.effectKind == PartySpellCastEffectKind::CharacterRestore
            || result.effectKind == PartySpellCastEffectKind::PartyRestore)
        {
            runtime.audioSystem()->playCommonSound(SoundId::Heal, GameAudioSystem::PlaybackGroup::Ui);
        }
        else if (pSpellEntry != nullptr
            && pSpellEntry->effectSoundId > 0
            && result.effectKind != PartySpellCastEffectKind::Projectile
            && result.effectKind != PartySpellCastEffectKind::MultiProjectile)
        {
            runtime.audioSystem()->playSound(
                pSpellEntry->effectSoundId,
                GameAudioSystem::PlaybackGroup::Ui);
        }
    }

    if (!spellName.empty())
    {
        runtime.setStatusBarEvent("Cast " + spellName);
    }
}

void GameplaySpellService::applyFailureFeedback(
    GameplayScreenRuntime &runtime,
    const PartySpellCastRequest &request,
    const PartySpellCastResult &result) const
{
    if (isUtilitySelectionRequest(request))
    {
        runtime.closeUtilitySpellOverlayAfterSpellResolution(request.spellId);
    }

    runtime.triggerSpellFailureFeedback(request.casterMemberIndex, result.statusText);
}
}
