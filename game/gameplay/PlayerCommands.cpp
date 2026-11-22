#include "game/gameplay/PlayerCommands.h"

#include "game/app/GameSession.h"
#include "game/audio/GameAudioSystem.h"
#include "game/coop/ReplicaWorldCalls.h"
#include "game/gameplay/GameplayHeldItemController.h"
#include "game/events/EventDialogContent.h"
#include "game/gameplay/GameplayItemService.h"
#include "game/gameplay/GameplayOverlayInputController.h"
#include "game/gameplay/GameplayScreenRuntime.h"
#include "game/gameplay/GameplaySpellService.h"
#include "game/gameplay/HouseServiceRuntime.h"

namespace OpenYAMM::Game
{
PlayerCommands::PlayerCommands(GameSession &session)
    : m_session(session)
{
}

namespace
{
// While a command of another player runs, the world's party is that player's: the handlers and the world code
// they call take the acting party from the world. The session's screens are that player's too (the host keeps a set
// for every guest), the map's event state holds that player's conversation and requests, and nothing is played to
// the host's own player. The local player's command needs no change.
class ActingPartyScope
{
public:
    ActingPartyScope(GameSession &session, PlayerId player, Party *pParty)
        : m_session(session)
        , m_player(player)
        , m_pWorldRuntime(player != LocalPlayer ? session.activeWorldRuntime() : nullptr)
    {
        if (m_pWorldRuntime == nullptr)
        {
            return;
        }

        m_pPrevious = m_pWorldRuntime->swapActingParty(pParty);
        // What is recorded of a fight while the command runs (a spell's hit on a monster) and the missiles it
        // sends flying are this player's.
        m_session.gameplayCombatController().setRecordingPlayer(player);
        m_session.gameplayProjectileService().setSpawningPlayer(player);
        // The ruleset's own values of a party (MAW's auras in effect) are the acting party's meanwhile.
        m_session.setRulesPartyInPlay(player);
        // The session still answers for the local player's party with the local player's.
        m_session.setLocalPartyBehindActingParty(m_pPrevious);
        m_pGuest = m_session.guestPlayer(player);
        EventRuntimeState *pEventRuntimeState = m_pWorldRuntime->eventRuntimeState();

        if (m_pGuest == nullptr || pEventRuntimeState == nullptr || m_session.actingGuestPlayer() != nullptr)
        {
            m_pGuest = nullptr;
            return;
        }

        swapTransientEventRuntimeState(*pEventRuntimeState, m_pGuest->eventTransients);
        m_session.setActingGuestPlayer(m_pGuest);

        if (GameAudioSystem *pAudioSystem = m_session.gameplayScreenRuntime().audioSystem())
        {
            m_audioWasHeld = pAudioSystem->playbackHeld();
            pAudioSystem->setPlaybackHeld(true);
        }
    }

    ~ActingPartyScope()
    {
        if (m_pWorldRuntime == nullptr)
        {
            return;
        }

        m_session.gameplayCombatController().setRecordingPlayer(LocalPlayer);
        m_session.gameplayProjectileService().setSpawningPlayer(LocalPlayer);

        if (m_pGuest != nullptr)
        {
            finishGuestAction();
        }

        // Where what the player did put its party (a teleport) is where it now stands for the host.
        const std::optional<GameplayPlayerBody> order = m_pWorldRuntime->takeActingBodyOrder();
        m_pWorldRuntime->swapActingParty(m_pPrevious);
        m_session.setRulesPartyInPlay(LocalPlayer);
        m_session.setLocalPartyBehindActingParty(nullptr);

        if (GameSession::GuestPlayer *pGuest = order ? m_session.guestPlayer(m_player) : nullptr)
        {
            pGuest->body = *order;
            ++pGuest->bodyOrderSerial;
        }
    }

    ActingPartyScope(const ActingPartyScope &) = delete;
    ActingPartyScope &operator=(const ActingPartyScope &) = delete;

private:
    void finishGuestAction()
    {
        // What an event gave this player while the command ran goes to its hand or bags now, whatever the command
        // was (a click indoors, a place stepped on, a dialogue closed, a spell): some paths hand it over
        // themselves, the others left it waiting for this player's next dialogue choice.
        if (const ItemTable *pItemTable = m_session.gameplayScreenRuntime().itemTable())
        {
            GameplayHeldItemController::applyGrantedEventItemsToHeldInventory(
                m_session.gameplayScreenRuntime(), *m_pWorldRuntime->eventRuntimeState(), *pItemTable);
        }

        if (GameAudioSystem *pAudioSystem = m_session.gameplayScreenRuntime().audioSystem())
        {
            pAudioSystem->setPlaybackHeld(m_audioWasHeld);
        }

        m_session.setActingGuestPlayer(nullptr);
        EventRuntimeState &eventState = *m_pWorldRuntime->eventRuntimeState();
        GameSession::GuestPlayer::Outcome &outcome = m_pGuest->outcome;
        // The chest and corpse the player has open now (the world's are the acting player's).
        const GameplayChestViewState *pChestView = m_pWorldRuntime->activeChestView();
        const GameplayCorpseViewState *pCorpseView = m_pWorldRuntime->activeCorpseView();
        m_pGuest->chestView = pChestView != nullptr ? std::optional<GameplayChestViewState>(*pChestView) : std::nullopt;
        m_pGuest->corpseView =
            pCorpseView != nullptr ? std::optional<GameplayCorpseViewState>(*pCorpseView) : std::nullopt;

        // What the player's game has to show of it: the status lines, and the sounds of what was done.
        for (size_t index = 0; index < eventState.statusMessages.size(); ++index)
        {
            outcome.statusTexts.emplace_back(eventState.statusMessages[index], statusMessageSeconds(eventState, index));
        }

        eventState.statusMessages.clear();
        eventState.statusMessageSeconds.clear();
        GameplayUiController::StatusBarState &statusBar = m_pGuest->ui.statusBar();

        if (!statusBar.eventText.empty())
        {
            outcome.statusTexts.emplace_back(statusBar.eventText, statusBar.eventRemainingSeconds);
            statusBar.eventText.clear();
            statusBar.eventRemainingSeconds = 0.0f;
        }

        // What an event asked of the whole game stays with the map's state: a move to another map (the players'
        // vote), a movie, a cinematic. So do the sounds placed in the world, which every player hears from where it
        // stands; the others are this player's alone (a quest's chime, a shop's greeting).
        std::optional<EventRuntimeState::PendingMapMove> mapMove = std::move(eventState.pendingMapMove);
        std::optional<EventRuntimeState::PendingMovie> movie = std::move(eventState.pendingMovie);
        std::optional<EventRuntimeState::PendingCinematic> cinematic = std::move(eventState.pendingCinematic);
        std::vector<EventRuntimeState::PendingSound> sounds;

        for (EventRuntimeState::PendingSound &sound : eventState.pendingSounds)
        {
            const bool ofTheWorld =
                sound.positional || sound.kind != EventRuntimeState::PendingSound::Kind::PlayOneShot;
            (ofTheWorld ? sounds : outcome.sounds).push_back(std::move(sound));
        }

        eventState.pendingMapMove.reset();
        eventState.pendingMovie.reset();
        eventState.pendingCinematic.reset();
        eventState.pendingSounds.clear();
        swapTransientEventRuntimeState(eventState, m_pGuest->eventTransients);

        if (mapMove && !eventState.pendingMapMove)
        {
            eventState.pendingMapMove = std::move(mapMove);
            m_session.notePendingMoveProposer(m_player);
        }

        if (movie && !eventState.pendingMovie)
        {
            eventState.pendingMovie = std::move(movie);
        }

        if (cinematic && !eventState.pendingCinematic)
        {
            eventState.pendingCinematic = std::move(cinematic);
        }

        eventState.pendingSounds.insert(eventState.pendingSounds.end(), sounds.begin(), sounds.end());
    }

    GameSession &m_session;
    PlayerId m_player = LocalPlayer;
    IGameplayWorldRuntime *m_pWorldRuntime = nullptr;
    Party *m_pPrevious = nullptr;
    GameSession::GuestPlayer *m_pGuest = nullptr;
    bool m_audioWasHeld = false;
};
}

void PlayerCommands::setRemote(IPlayerCommandRemote *pRemote)
{
    m_pRemote = pRemote;
}

IPlayerCommandRemote *PlayerCommands::remote() const
{
    return m_pRemote;
}

Party *PlayerCommands::party(PlayerId player) const
{
    // A guest whose game is still loading the map is not on it: nothing is done for it or to it until it is.
    if (const GameSession::GuestPlayer *pGuest = m_session.guestPlayer(player); pGuest != nullptr && pGuest->loadingMap)
    {
        return nullptr;
    }

    return m_session.partyOfPlayer(player);
}

void PlayerCommands::note(PlayerCommandKind kind)
{
    ++m_counts[size_t(kind)];
}

uint64_t PlayerCommands::count(PlayerCommandKind kind) const
{
    return kind < PlayerCommandKind::Count ? m_counts[size_t(kind)] : 0;
}

GameplayActionController::PartyAttackExecutionResult PlayerCommands::attack(
    PlayerId player,
    GameplayActionController::PartyAttackConfig config)
{
    config.pParty = party(player);

    if (config.pParty == nullptr)
    {
        return {};
    }

    note(PlayerCommandKind::Attack);
    const ActingPartyScope acting(m_session, player, config.pParty);
    return GameplayActionController::executePartyAttack(config);
}

PartySpellCastResult PlayerCommands::castSpell(
    PlayerId player,
    GameplayScreenRuntime &runtime,
    const PartySpellCastRequest &request,
    std::optional<PlayerId> targetPlayer)
{
    Party *pParty = party(player);

    if (pParty == nullptr)
    {
        return {};
    }

    note(PlayerCommandKind::CastSpell);
    // The player the casting game chose with the request, where the caller names none.
    targetPlayer = targetPlayer ? targetPlayer : request.targetPlayer;

    if (m_pRemote != nullptr && player == LocalPlayer && runtime.spellTable() != nullptr)
    {
        return castSpellAsGuest(*runtime.spellTable(), request, targetPlayer);
    }

    // The target's party is looked up before the acting party is swapped in: the world answers for the local
    // player's party with the acting one while the scope lasts.
    const PartySpellCastRequest targeted = requestForTarget(player, request, targetPlayer);
    const ActingPartyScope acting(m_session, player, pParty);
    return m_session.gameplaySpellService().castSpell(runtime, targeted);
}

PartySpellCastResult PlayerCommands::castSpellAsGuest(
    const SpellTable &spellTable,
    const PartySpellCastRequest &request,
    std::optional<PlayerId> targetPlayer)
{
    IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();
    Party *pParty = party(LocalPlayer);

    if (pParty == nullptr || pWorldRuntime == nullptr)
    {
        return {};
    }

    // On copies: the party's is the host's to change, and so is another player's, which a copy of this one stands in
    // for. The map changes nothing while the try lasts.
    Party trial = *pParty;
    trial.setMirror(false);
    Party otherPlayerStandIn = trial;
    PartySpellCastRequest tried = request;
    const bool onAnotherPlayer = targetPlayer && *targetPlayer != m_pRemote->ownPlayer();
    tried.pTargetParty = onAnotherPlayer ? &otherPlayerStandIn : nullptr;

    // The stand-in is as hurt and ails as this game knows that player to be, so that a heal, a cure or a raising
    // is tried on what it is for.
    // The stand-in's first member stands for whichever member of that party the cast names (this party may have
    // fewer); the host is asked with the member's own number.
    if (onAnotherPlayer)
    {
        const size_t named = request.targetCharacterIndex.value_or(0);

        if (tried.targetCharacterIndex)
        {
            tried.targetCharacterIndex = 0;
        }

        for (const CoopAidPlayer &other : m_session.coopAidPlayers())
        {
            Character *pStandIn = other.player == *targetPlayer && named < other.members.size()
                ? otherPlayerStandIn.member(0) : nullptr;

            if (pStandIn != nullptr)
            {
                const CoopAidPlayer::Member &known = other.members[named];
                pStandIn->health = known.health;
                pStandIn->conditions.reset();

                if (known.conditionCode != 0 && known.conditionCode <= uint8_t(CharacterCondition::Count))
                {
                    pStandIn->conditions.set(size_t(known.conditionCode - 1));
                }
            }
        }
    }
    // A spell that takes the party elsewhere (Town Portal, a beacon's recall) asks for the move in the map's event
    // state: the try must leave none behind, or this game would go there alone while the host asks the others.
    EventRuntimeState *pTrialState = pWorldRuntime->eventRuntimeState();
    const std::optional<EventRuntimeState::PendingMapMove> moveBefore =
        pTrialState != nullptr ? pTrialState->pendingMapMove : std::nullopt;
    pWorldRuntime->setReplicaDryRun(true);
    const PartySpellCastResult result = PartySpellSystem::castSpell(trial, *pWorldRuntime, spellTable, tried);
    pWorldRuntime->setReplicaDryRun(false);

    if (pTrialState != nullptr)
    {
        pTrialState->pendingMapMove = moveBefore;
    }

    if (!result.succeeded())
    {
        return result;
    }

    m_pRemote->castSpell(request, onAnotherPlayer ? targetPlayer : std::nullopt);

    // The cost shows at once; the host's state confirms it.
    const Character *pTrialCaster = trial.member(request.casterMemberIndex);

    if (Character *pCaster = pParty->member(request.casterMemberIndex); pCaster != nullptr && pTrialCaster != nullptr)
    {
        pCaster->spellPoints = pTrialCaster->spellPoints;
        pCaster->recoverySecondsRemaining = pTrialCaster->recoverySecondsRemaining;
        pCaster->recoveryTotalSeconds = pTrialCaster->recoveryTotalSeconds;
    }

    return result;
}

PartySpellCastResult PlayerCommands::castSpellDirect(
    PlayerId player,
    const SpellTable &spellTable,
    const PartySpellCastRequest &request,
    std::optional<PlayerId> targetPlayer)
{
    IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();
    Party *pParty = party(player);

    if (pParty == nullptr || pWorldRuntime == nullptr)
    {
        return {};
    }

    note(PlayerCommandKind::CastSpell);

    if (m_pRemote != nullptr && player == LocalPlayer)
    {
        return castSpellAsGuest(spellTable, request, targetPlayer);
    }

    const PartySpellCastRequest targeted = requestForTarget(player, request, targetPlayer);
    const ActingPartyScope acting(m_session, player, pParty);
    const PartySpellCastResult result = PartySpellSystem::castSpell(*pParty, *pWorldRuntime, spellTable, targeted);
    pWorldRuntime->applyPendingSpellCastWorldEffects(result);
    return result;
}

PartySpellCastRequest PlayerCommands::requestForTarget(
    PlayerId player,
    const PartySpellCastRequest &request,
    std::optional<PlayerId> targetPlayer)
{
    PartySpellCastRequest targeted = request;

    if (targetPlayer && *targetPlayer != player)
    {
        // A player who is not in the session, stands too far away or behind a wall leaves the request without its
        // character target: the cast fails for want of one, and never lands on the caster's own member of that
        // number.
        targeted.pTargetParty =
            m_session.playersInAidSight(player, *targetPlayer) ? party(*targetPlayer) : nullptr;

        if (targeted.pTargetParty == nullptr)
        {
            targeted.targetCharacterIndex.reset();
        }
    }

    const auto addAidParty = [&](PlayerId other)
    {
        Party *pOther = other != player ? party(other) : nullptr;

        if (pOther != nullptr && m_session.playersWithinAidRadius(player, other))
        {
            targeted.aidParties.push_back(pOther);
        }
    };

    addAidParty(LocalPlayer);

    for (const std::unique_ptr<GameSession::GuestPlayer> &pGuest : m_session.guestPlayers())
    {
        addAidParty(pGuest->id);
    }

    return targeted;
}

bool PlayerCommands::activateWorldHit(PlayerId player, const GameplayWorldHit &hit)
{
    IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();
    Party *pParty = party(player);

    if (pParty == nullptr || pWorldRuntime == nullptr)
    {
        return false;
    }

    note(PlayerCommandKind::ActivateWorldHit);

    // A guest's game: the host opens the door, the chest or the conversation for this player.
    if (m_pRemote != nullptr && player == LocalPlayer)
    {
        m_pRemote->activateWorldHit(hit);
        return true;
    }

    if (player == LocalPlayer)
    {
        return pWorldRuntime->activateWorldHit(hit);
    }

    // What the click's event asks of the world (a chest to open) is applied while this player acts, so that it
    // is theirs; what the local player's events asked before is applied first, so that it stays the local player's.
    pWorldRuntime->applyEventRuntimeState();
    const ActingPartyScope acting(m_session, player, pParty);
    const bool activated = pWorldRuntime->activateWorldHit(hit);
    pWorldRuntime->applyEventRuntimeState();
    // A dialogue the click asked for opens now, while the screens are this player's.
    m_session.gameplayScreenRuntime().ensurePendingEventDialogPresented(true);
    noteMapMoveAskedBy(player);
    return activated;
}

bool PlayerCommands::runEvent(PlayerId player, const std::function<bool(Party &party)> &execute)
{
    IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();
    Party *pParty = party(player);

    if (pParty == nullptr || pWorldRuntime == nullptr)
    {
        return false;
    }

    if (player == LocalPlayer)
    {
        return execute(*pParty);
    }

    pWorldRuntime->applyEventRuntimeState();
    const ActingPartyScope acting(m_session, player, pParty);
    const bool executed = execute(*pParty);
    pWorldRuntime->applyEventRuntimeState();
    // A dialogue the event asked for opens now, while the screens are this player's.
    m_session.gameplayScreenRuntime().ensurePendingEventDialogPresented(true);
    noteMapMoveAskedBy(player);
    return executed;
}

bool PlayerCommands::dialogueAction(
    PlayerId player,
    size_t selectionIndex,
    const EventDialogAction &action,
    bool overrideAction)
{
    IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();
    Party *pParty = party(player);
    GameSession::GuestPlayer *pGuest = m_session.guestPlayer(player);

    if (pParty == nullptr || pWorldRuntime == nullptr || pGuest == nullptr)
    {
        return false;
    }

    pWorldRuntime->applyEventRuntimeState();
    const ActingPartyScope acting(m_session, player, pParty);
    GameplayScreenRuntime &screenRuntime = m_session.gameplayScreenRuntime();
    const EventDialogContent &dialog = screenRuntime.activeEventDialog();

    if (!dialog.isActive)
    {
        return false;
    }

    if (overrideAction)
    {
        // An action over the dialogue offered is a ship's or coach's departure picked on the timetable, and nothing
        // else: any other kind named by another game (a topic's event, a lesson) is not run.
        const bool scheduledTrip = action.kind == EventDialogActionKind::Mm9RudeTransportRoute
            || (action.kind == EventDialogActionKind::HouseService
                && action.id == uint32_t(HouseActionId::TransportScheduledTrip));

        if (!scheduledTrip)
        {
            return false;
        }

        screenRuntime.executeDialogAction(action);
    }
    else
    {
        // The choice has to be the one the player's game showed at that place.
        if (selectionIndex >= dialog.actions.size() || dialog.actions[selectionIndex].kind != action.kind
            || dialog.actions[selectionIndex].id != action.id || !dialog.actions[selectionIndex].enabled)
        {
            return false;
        }

        screenRuntime.eventDialogSelectionIndex() = selectionIndex;
        screenRuntime.executeActiveDialogAction();
    }

    pWorldRuntime->applyEventRuntimeState();

    // A move to another map the choice asked for (an exit confirmed) is this player's proposal to the others. The
    // dialogue it was confirmed in is this player's and closes now: the local game's stays for its departure frame.
    if (m_session.pendingMapMove().has_value())
    {
        m_session.notePendingMoveProposer(player);
        screenRuntime.closeActiveDialogForMapMove();
    }

    screenRuntime.ensurePendingEventDialogPresented(true);
    return true;
}

bool PlayerCommands::houseStockAction(
    PlayerId player,
    HouseStockAction action,
    HouseStockMode stockMode,
    size_t slotIndex)
{
    IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();
    Party *pParty = party(player);
    GameSession::GuestPlayer *pGuest = m_session.guestPlayer(player);

    if (pParty == nullptr || pWorldRuntime == nullptr || pGuest == nullptr)
    {
        return false;
    }

    const ActingPartyScope acting(m_session, player, pParty);
    GameplayScreenRuntime &screenRuntime = m_session.gameplayScreenRuntime();
    const GameplayUiController::HouseShopOverlayState &overlay = screenRuntime.houseShopOverlay();
    const HouseTable *pHouseTable = overlay.active ? screenRuntime.houseTable() : nullptr;
    const HouseEntry *pHouseEntry = pHouseTable != nullptr ? pHouseTable->get(overlay.houseId) : nullptr;

    // The stock the player's game shows is the one the host opened for it.
    const std::optional<HouseStockMode> openMode =
        overlay.mode == GameplayUiController::HouseShopMode::BuyStandard ? std::optional(HouseStockMode::ShopStandard)
        : overlay.mode == GameplayUiController::HouseShopMode::BuySpecial ? std::optional(HouseStockMode::ShopSpecial)
        : overlay.mode == GameplayUiController::HouseShopMode::BuySpellbooks
            ? std::optional(HouseStockMode::GuildSpellbooks)
        : std::nullopt;

    if (pHouseEntry == nullptr || openMode != stockMode)
    {
        return false;
    }

    GameplayOverlayInputController::performHouseStockAction(screenRuntime, *pHouseEntry, stockMode, slotIndex, action);
    return true;
}

std::optional<std::string> PlayerCommands::restRefusal(PlayerId player, bool heal)
{
    Party *pParty = party(player);

    if (pParty == nullptr)
    {
        return std::nullopt;
    }

    std::optional<ActingPartyScope> acting;

    if (player != LocalPlayer)
    {
        acting.emplace(m_session, player, pParty);
    }

    const GameplayScreenRuntime &screenRuntime = m_session.gameplayScreenRuntime();

    if (std::optional<std::string> restriction = screenRuntime.restRestrictionStatus())
    {
        return restriction;
    }

    if (heal && pParty->food() < screenRuntime.restFoodRequired())
    {
        return Engine::tr("You don't have enough food to rest.");
    }

    return std::nullopt;
}

void PlayerCommands::houseScreenClose(PlayerId player, bool stockScreen)
{
    Party *pParty = party(player);

    if (pParty == nullptr || m_session.guestPlayer(player) == nullptr)
    {
        return;
    }

    const ActingPartyScope acting(m_session, player, pParty);

    if (stockScreen)
    {
        m_session.gameplayScreenRuntime().closeHouseShopOverlay();
    }
    else
    {
        m_session.gameplayScreenRuntime().closeInventoryNestedOverlay();
    }
}

void PlayerCommands::dialogueClose(PlayerId player)
{
    IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();
    Party *pParty = party(player);

    if (pParty == nullptr || pWorldRuntime == nullptr || m_session.guestPlayer(player) == nullptr)
    {
        return;
    }

    const ActingPartyScope acting(m_session, player, pParty);
    m_session.gameplayScreenRuntime().handleDialogueCloseRequest();
    // The player's game closed its own: nothing of this is news for it.
    m_session.guestPlayer(player)->outcome.dialogueClosed = false;
}

namespace
{
uint64_t goldIn(const std::vector<GameplayChestItemState> &items)
{
    uint64_t gold = 0;

    for (const GameplayChestItemState &item : items)
    {
        gold += item.isGold ? item.goldAmount : 0;
    }

    return gold;
}

// What a player took of the gold of a chest or corpse is every other player's too (found gold goes to everyone).
void shareTakenGold(
    GameSession &session,
    const Party &finder,
    uint64_t goldBefore,
    uint64_t goldAfter,
    GoldReason reason)
{
    const IGameplayWorldRuntime *pWorldRuntime = session.activeWorldRuntime();
    const EventRuntimeState *pEventRuntimeState =
        pWorldRuntime != nullptr ? pWorldRuntime->eventRuntimeState() : nullptr;

    if (pEventRuntimeState == nullptr || goldAfter >= goldBefore)
    {
        return;
    }

    for (Party *pOtherParty : pEventRuntimeState->coopParties)
    {
        if (pOtherParty != &finder)
        {
            pOtherParty->addGold(int(std::min<uint64_t>(goldBefore - goldAfter, 0x7FFFFFFF)), reason);
        }
    }
}
}

bool PlayerCommands::putOpenChest(PlayerId player, const GameplayChestViewState &view)
{
    IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();
    Party *pParty = party(player);

    if (pParty == nullptr || pWorldRuntime == nullptr || player == LocalPlayer)
    {
        return false;
    }

    const ActingPartyScope acting(m_session, player, pParty);
    GameplayChestViewState *pChestView = pWorldRuntime->activeChestView();

    // The chest the player has open, and no other.
    if (pChestView == nullptr || pChestView->chestId != view.chestId)
    {
        return false;
    }

    const uint64_t goldBefore = goldIn(pChestView->items) + goldIn(pChestView->hiddenItems);

    // Gold only leaves a chest: a view with more of it is not the chest's (what is taken is shared with the others).
    if (goldIn(view.items) + goldIn(view.hiddenItems) > goldBefore)
    {
        return false;
    }

    pChestView->items = view.items;
    pChestView->hiddenItems = view.hiddenItems;
    pWorldRuntime->commitActiveChestView();
    shareTakenGold(
        m_session, *pParty, goldBefore, goldIn(view.items) + goldIn(view.hiddenItems), GoldReason::LootChest);
    return true;
}

bool PlayerCommands::putOpenCorpse(PlayerId player, const GameplayCorpseViewState &view)
{
    IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();
    Party *pParty = party(player);

    if (pParty == nullptr || pWorldRuntime == nullptr || player == LocalPlayer)
    {
        return false;
    }

    const ActingPartyScope acting(m_session, player, pParty);
    GameplayCorpseViewState *pCorpseView = pWorldRuntime->activeCorpseView();

    if (pCorpseView == nullptr || pCorpseView->sourceIndex != view.sourceIndex
        || pCorpseView->fromSummonedMonster != view.fromSummonedMonster)
    {
        return false;
    }

    const uint64_t goldBefore = goldIn(pCorpseView->items);

    if (goldIn(view.items) > goldBefore)
    {
        return false;
    }

    pCorpseView->items = view.items;
    pWorldRuntime->commitActiveCorpseView();
    shareTakenGold(m_session, *pParty, goldBefore, goldIn(view.items), GoldReason::LootCorpse);
    return true;
}

bool PlayerCommands::houseBankAmount(PlayerId player, uint32_t amount)
{
    IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();
    Party *pParty = party(player);

    if (pParty == nullptr || pWorldRuntime == nullptr || m_session.guestPlayer(player) == nullptr)
    {
        return false;
    }

    const ActingPartyScope acting(m_session, player, pParty);
    GameplayScreenRuntime &screenRuntime = m_session.gameplayScreenRuntime();

    // Only where the bank is asking this player: the amount is what its player typed.
    if (!screenRuntime.houseBankState().inputActive())
    {
        return false;
    }

    screenRuntime.houseBankState().inputText = std::to_string(amount);
    screenRuntime.confirmHouseBankInput();
    return true;
}

bool PlayerCommands::takeWorldItem(PlayerId player, size_t worldItemIndex, GameplayWorldItemInspectState &taken)
{
    IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();
    Party *pParty = party(player);

    if (pParty == nullptr || pWorldRuntime == nullptr)
    {
        return false;
    }

    const ActingPartyScope acting(m_session, player, pParty);
    return pWorldRuntime->takeWorldItemInspectState(worldItemIndex, taken);
}

bool PlayerCommands::runReplicaWorldCall(PlayerId player, std::span<const uint8_t> call)
{
    IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();
    Party *pParty = party(player);

    if (pParty == nullptr || pWorldRuntime == nullptr || player == LocalPlayer)
    {
        return false;
    }

    const ActingPartyScope acting(m_session, player, pParty);
    return ReplicaWorldCalls::execute(*pWorldRuntime, call);
}

bool PlayerCommands::touchPositionTrigger(PlayerId player, const ReplicaPositionTrigger &trigger)
{
    const std::optional<GameplayPlayerBody> body = m_session.bodyOfPlayer(player);

    if (!body)
    {
        return false;
    }

    return runEvent(player, [&](Party &)
    {
        IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();
        return pWorldRuntime != nullptr && pWorldRuntime->executeReplicaPositionTrigger(trigger, *body);
    });
}

void PlayerCommands::noteMapMoveAskedBy(PlayerId player)
{
    // A map move the player's event asked for is that player's proposal to the others (GameSession::proposeTravel).
    const IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();
    const EventRuntimeState *pEventRuntimeState =
        pWorldRuntime != nullptr ? pWorldRuntime->eventRuntimeState() : nullptr;

    if (pEventRuntimeState != nullptr && pEventRuntimeState->pendingMapMove)
    {
        m_session.notePendingMoveProposer(player);
    }
}

std::optional<GameplayChestViewState> PlayerCommands::openChest(PlayerId player)
{
    IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();
    Party *pParty = party(player);

    if (pParty == nullptr || pWorldRuntime == nullptr)
    {
        return std::nullopt;
    }

    // A copy: the world's view is this player's only while the player acts.
    const ActingPartyScope acting(m_session, player, pParty);
    const GameplayChestViewState *pChestView = pWorldRuntime->activeChestView();
    return pChestView != nullptr ? std::optional<GameplayChestViewState>(*pChestView) : std::nullopt;
}

size_t PlayerCommands::takeAllFromOpenChest(PlayerId player, const ItemTable &itemTable)
{
    IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();
    Party *pParty = party(player);

    if (pParty == nullptr || pWorldRuntime == nullptr)
    {
        return 0;
    }

    const ActingPartyScope acting(m_session, player, pParty);

    if (pWorldRuntime->activeChestView() == nullptr)
    {
        return 0;
    }

    return GameplayOverlayInputController::takeAllActiveChestItems(*pWorldRuntime, *pParty, &itemTable, false).taken;
}

void PlayerCommands::closeOpenChestAndCorpse(PlayerId player)
{
    IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();
    Party *pParty = party(player);

    if (pParty == nullptr || pWorldRuntime == nullptr)
    {
        return;
    }

    const ActingPartyScope acting(m_session, player, pParty);
    pWorldRuntime->closeActiveChestView();
    pWorldRuntime->closeActiveCorpseView();
}

bool PlayerCommands::useHeldItemOnMember(
    PlayerId player,
    GameplayScreenRuntime &runtime,
    size_t memberIndex,
    bool keepCharacterScreenOpen)
{
    Party *pParty = party(player);

    if (pParty == nullptr)
    {
        return false;
    }

    note(PlayerCommandKind::UseHeldItem);
    const ActingPartyScope acting(m_session, player, pParty);
    return m_session.gameplayItemService().tryUseHeldItemOnPartyMember(runtime, memberIndex, keepCharacterScreenOpen);
}
}
