#pragma once

#include "game/events/EventRuntime.h"
#include "game/gameplay/GameplayActionController.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/gameplay/PlayerId.h"
#include "game/party/PartySpellSystem.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <optional>
#include <span>
#include <string>

namespace OpenYAMM::Game
{
class GameSession;
class GameplayScreenRuntime;
class ItemTable;
class SpellTable;
class Party;

enum class PlayerCommandKind : uint8_t
{
    Attack,
    CastSpell,
    ActivateWorldHit,
    UseHeldItem,
    Count,
};

struct EventDialogAction;
enum class HouseStockAction : uint8_t;
enum class HouseStockMode : uint8_t;

// A co-op guest's game (GameSession::coopReplica): what its player does that the host has to do is handed over here
// instead of being done in this game. The session between the games implements it (game/coop/CoopSession.h).
class IPlayerCommandRemote
{
public:
    virtual ~IPlayerCommandRemote() = default;

    // The player this game's character is in the host's session.
    virtual PlayerId ownPlayer() const = 0;
    virtual void castSpell(const PartySpellCastRequest &request, std::optional<PlayerId> targetPlayer) = 0;
    virtual void activateWorldHit(const GameplayWorldHit &hit) = 0;
    // The choice the player made in the open dialogue: its place in the list and what it is, or an action a popup
    // over the dialogue offered (overrideAction).
    virtual void dialogueAction(size_t selectionIndex, const EventDialogAction &action, bool overrideAction) = 0;
    virtual void dialogueClose() = 0;
    // A shop's stock is the host's: buying, stealing and rerolling happen there.
    virtual void houseStockAction(HouseStockAction action, HouseStockMode stockMode, size_t slotIndex) = 0;
    // The player's answer to another player's travel proposal, and the downed player's wish to return.
    virtual void travelVote(bool accept) = 0;
    // Asking the others to rest or wait, and agreeing to another player's asking.
    virtual void proposeRest(bool heal, float minutes) = 0;
    virtual void restVote(bool accept) = 0;
    virtual void returnDowned() = 0;
    // A lying item, by its key (IGameplayWorldRuntime::worldItemKey): the host takes it out of its world and this
    // game is given it (GameplayInteractionController::receiveTakenWorldItem).
    virtual void takeWorldItem(uint32_t itemKey) = 0;
    // The player walked into the map's edge and agreed to go where it leads: its proposal to the other players.
    virtual void proposeTravel(const EventRuntimeState::PendingMapMove &move) = 0;
    // The amount the player typed when the bank asked for one: the host deposits or withdraws it for this player.
    virtual void houseBankAmount(uint32_t amount) = 0;
    // The player goes where its own travel proposal leads without the others: it steps out of the session into its
    // own game and travels there (CoopSession::stepOut).
    virtual void stepOutToTravel(const EventRuntimeState::PendingMapMove &move) = 0;
    // The player leaves the session for now without a trip of its own (it does not go where the others travel).
    virtual void stepOutOfSession() = 0;
};

// What a player does to the world: every attack, cast, activation of something in the world and use of a held item
// enters here with the player who does it (devdocs/plans/MULTIPLAYER_LISTEN_SERVER_ARCHITECTURE.md, "Commands").
// The input code decides what the player means and with what target; this is where it is done, by the player's
// party, in the game that runs the world. A second player's commands will arrive here the same way.
class PlayerCommands
{
public:
    explicit PlayerCommands(GameSession &session);

    // Set in a co-op guest's game, null everywhere else.
    void setRemote(IPlayerCommandRemote *pRemote);
    IPlayerCommandRemote *remote() const;

    // The party the player acts with; null for a player the session does not have.
    Party *party(PlayerId player) const;

    // The attack runs with the player's party, whatever party the request names.
    GameplayActionController::PartyAttackExecutionResult attack(
        PlayerId player,
        GameplayActionController::PartyAttackConfig config);
    // targetPlayer names the player whose character the request's targetCharacterIndex is, when it is not the
    // caster's own: a heal, a cure, a revival or a one-character buff on another player.
    PartySpellCastResult castSpell(
        PlayerId player,
        GameplayScreenRuntime &runtime,
        const PartySpellCastRequest &request,
        std::optional<PlayerId> targetPlayer = std::nullopt);
    // The cast as the rules run it, without the local game's targeting and screen: what a player without a screen
    // here casts with (the scenario runner; a client's cast, once there are clients).
    PartySpellCastResult castSpellDirect(
        PlayerId player,
        const SpellTable &spellTable,
        const PartySpellCastRequest &request,
        std::optional<PlayerId> targetPlayer = std::nullopt);
    // A door, a chest, an NPC, a decoration, a corpse. Picking an item up from the ground is not here yet: it goes
    // through the cursor's held item, which belongs to the game at whose screen it is.
    bool activateWorldHit(PlayerId player, const GameplayWorldHit &hit);
    // Runs an event for the player: its rewards and costs are that party's, and what it opens (a chest) opens for
    // that player. execute gets the party and runs the event; its result is returned.
    bool runEvent(PlayerId player, const std::function<bool(Party &party)> &execute);
    // The chest the player has open: each player has their own, and a chest one player has open is refused to
    // the others until it is closed. takeAllFromOpenChest gives the player's party what fits (found gold goes to
    // every player) and returns the number of things taken.
    std::optional<GameplayChestViewState> openChest(PlayerId player);
    // What a guest's own game made of the chest or corpse its player has open (things taken out, things put in): the
    // host's becomes that. Gold that went out is every other player's too. False when the player has not that chest
    // or corpse open.
    bool putOpenChest(PlayerId player, const GameplayChestViewState &view);
    bool putOpenCorpse(PlayerId player, const GameplayCorpseViewState &view);
    size_t takeAllFromOpenChest(PlayerId player, const ItemTable &itemTable);
    void closeOpenChestAndCorpse(PlayerId player);
    bool useHeldItemOnMember(
        PlayerId player,
        GameplayScreenRuntime &runtime,
        size_t memberIndex,
        bool keepCharacterScreenOpen);

    // A guest's choice in the dialogue the host keeps open for it, and its closing of it. The host does what the
    // choice does for that player's party; what opens or closes then is noted for the player's game
    // (GameSession::GuestPlayer::Outcome).
    bool dialogueAction(PlayerId player, size_t selectionIndex, const EventDialogAction &action, bool overrideAction);
    void dialogueClose(PlayerId player);
    // Another player's buy, theft or reroll in the shop whose stock screen the host keeps open for it.
    bool houseStockAction(PlayerId player, HouseStockAction action, HouseStockMode stockMode, size_t slotIndex);
    // Why this player cannot rest where it stands now (the rest screen's own reasons, and the food of a rest that
    // heals); none when it can.
    std::optional<std::string> restRefusal(PlayerId player, bool heal);
    // Another player left a shop's stock screen, or the screen that sells, identifies or repairs its own things.
    void houseScreenClose(PlayerId player, bool stockScreen);

    // What a guest's own game did to the map with a blow, a shot or a talent it resolved itself
    // (game/coop/ReplicaWorldCalls.h), done here for that player; and the event of a place that player's party
    // stepped on.
    bool runReplicaWorldCall(PlayerId player, std::span<const uint8_t> call);
    // Takes a lying item out of the world for a player (a guest's request): what its taking sets off in the map
    // (a placed pickup's event) is that player's doing.
    bool takeWorldItem(PlayerId player, size_t worldItemIndex, GameplayWorldItemInspectState &taken);
    // The amount a guest typed at the bank, which asked that player for it (its Deposit or Withdraw choice).
    bool houseBankAmount(PlayerId player, uint32_t amount);
    bool touchPositionTrigger(PlayerId player, const ReplicaPositionTrigger &trigger);

    // How many commands of the kind the session has taken, for the console's `commands` and for tests.
    uint64_t count(PlayerCommandKind kind) const;

private:
    void note(PlayerCommandKind kind);
    void noteMapMoveAskedBy(PlayerId player);
    PartySpellCastRequest requestForTarget(
        PlayerId player,
        const PartySpellCastRequest &request,
        std::optional<PlayerId> targetPlayer);

    // A guest's game: the cast is tried here on a copy of the party, to see what it needs and what it shows, and done
    // by the host.
    PartySpellCastResult castSpellAsGuest(
        const SpellTable &spellTable,
        const PartySpellCastRequest &request,
        std::optional<PlayerId> targetPlayer);

    GameSession &m_session;
    IPlayerCommandRemote *m_pRemote = nullptr;
    std::array<uint64_t, size_t(PlayerCommandKind::Count)> m_counts = {};
};
}
