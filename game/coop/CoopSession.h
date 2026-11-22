#pragma once

#include "engine/net/EnetTransport.h"
#include "engine/net/LanDiscovery.h"
#include "engine/net/NetTransport.h"
#include "engine/net/RendezvousClient.h"
#include "game/coop/CharacterFile.h"
#include "game/coop/CoopCharacter.h"
#include "game/coop/CoopProtocol.h"
#include "game/coop/LobbyLookup.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/gameplay/PlayerCommands.h"
#include "game/gameplay/PlayerId.h"
#include "game/maps/SaveGame.h"
#include "game/rules/LentAura.h"

#include <future>
#include <array>
#include <cstdint>
#include <deque>
#include <filesystem>
#include <memory>
#include <optional>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Engine
{
class ByteReader;
class ByteWriter;
}

namespace OpenYAMM::Game
{
class GameApplication;
class GameSession;
struct HeldSkinRules;

// A co-op session between games (devdocs/plans/MULTIPLAYER_LISTEN_SERVER_ARCHITECTURE.md, "The replica as built").
// One game hosts: it runs the world for everyone, takes each other game's character as a guest player
// (GameSession::GuestPlayer) and sends every guest's game what it needs to show the world. A game that joined is a
// replica (GameSession::coopReplica): it loads the map from the state the host sends, shows what the host tells it
// and sends what its player does as commands.
//
// The games talk through an INetTransport, so the same code serves two games in one process (LoopbackTransport, the
// scenario runner) and two games on a network (EnetTransport).
class CoopSession : public IPlayerCommandRemote
{
public:
    explicit CoopSession(GameApplication &application);
    ~CoopSession() override;

    CoopSession(const CoopSession &) = delete;
    CoopSession &operator=(const CoopSession &) = delete;

    // Hosts the game in progress on a UDP port; false with the reason when the port cannot be opened. Games on the
    // local network find it by a scan, and anyone who is given the address can join. With a lobby's address
    // ("host:port") the session is also registered there under `name`: it is listed, gets a code to join by, and
    // games behind routers reach it through the lobby (hostCode).
    bool host(uint16_t port, std::string &error, const std::string &name = {}, const std::string &lobbyAddress = {});
    // The name the session goes by, the port it hosts on, the code the lobby gave it (empty until the lobby
    // answered, and without a lobby) and this machine's address towards the lobby or the local network.
    const std::string &hostName() const;
    uint16_t hostPort() const;
    std::string hostCode() const;
    bool hostAsksLobby() const;
    // Joins the session a lobby knows by `code`: the lobby tells both games where the other is, they open a path
    // through their routers, and where none opens the lobby relays. The answer comes with update().
    // `relayOnly` skips the search for a direct path (a test of the relay).
    bool joinByCode(const std::string &lobbyAddress, const std::string &code, std::string &error,
        bool relayOnly = false);
    // Hosts on a transport that is already open (the scenario runner's in-process one).
    void hostOn(std::unique_ptr<Engine::INetTransport> pTransport);
    // Joins the session at "host:port" with the character of the game in progress. The answer comes with update().
    bool join(const std::string &address, std::string &error);
    // Joins over a transport whose connection to the host is being made or made; hostPeer names it.
    void joinOn(std::unique_ptr<Engine::INetTransport> pTransport, Engine::NetPeerId hostPeer);
    // Right after join or joinOn: the character to join with is this file's and not the game in progress's. It is
    // written back to `path` every few minutes and on leaving, and the game in progress comes back as it was.
    void setJoinCharacter(CharacterFile file, std::filesystem::path path);
    // Writes the character file of a guest that joined with one, now. False with the reason when it cannot.
    bool writeJoinCharacter(std::string &error);
    // The file a guest joined with, else null.
    const std::filesystem::path *joinCharacterPath() const;
    // A guest that joined with the character of its own game: writes that game, with the character as the session
    // has it now, into the game's Autosave file, so that what the character gained outlives this game closing.
    // False with the reason when there is nothing to write or it cannot be written.
    bool writeGuestOwnGame(std::string &error);
    // A guest asks the host for its whole world, to keep as a save of its own named `name` (saves/<name>.oysav): the
    // host's quests and maps as they are now, with this guest's character in the party. The old game of this guest
    // is not touched. The save is written when the host's answer arrives; a save of that name is kept unless
    // `replace` says otherwise. False with the reason when it cannot ask.
    bool keepWorldCopy(const std::string &name, bool replace, std::string &error);
    // Ends hosting, or leaves the host: a guest's game goes back to the game it had before it joined, with its
    // character as the session left it.
    void leave();

    // How a guest's game reached its host, for joining it again.
    struct JoinRoute
    {
        enum class Kind : uint8_t
        {
            // Over a transport someone else made (a test's): this game cannot make it again by itself.
            Other,
            Address,
            Code,
        };

        Kind kind = Kind::Other;
        std::string address;
        std::string lobbyAddress;
        std::string code;
        bool relayOnly = false;
    };
    // The session a guest's game stepped out of: who hosts it, the key of the seat kept there and the way back.
    struct AwayFrom
    {
        std::string hostName;
        uint64_t seatKey = 0;
        JoinRoute route;
        std::string password;
    };
    // A guest's player leaves for its own game for now: the host keeps its seat (the others see it greyed, "away"),
    // the connection ends and this game is its own again, as after leave(). With `move` the own game then travels
    // there: the player went where it wanted to without the others. The game leaves when the host has answered.
    // False with the reason when this game cannot.
    bool stepOut(std::optional<EventRuntimeState::PendingMapMove> move, std::string &error);
    // The session this game stepped out of, until it joins a session again or the player forgets it.
    const std::optional<AwayFrom> &awayFrom() const;
    void forgetAwaySession();
    // Joins the session this game stepped out of again, the way it joined it. Any other join of that host (the
    // Multiplayer screen's, a test's) takes the kept seat as well: the key goes with every Hello.
    bool stepBack(std::string &error);
    // A host's game: the players who stepped out and whose seats are kept.
    size_t awaySeatCount() const;
    // A guest's game, for testing: asks the host to put this player beside it (GameApplication::coopSyncPlayers).
    void askTestSync();

    // Every frame: receives, applies and sends. deltaSeconds is real time.
    void update(float deltaSeconds);

    bool hosting() const;
    bool joined() const;
    // A guest between its Hello and the first map it has loaded.
    bool joining() const;
    // The player this game's character is in the host's session; LocalPlayer in the host's game.
    PlayerId ownPlayer() const override;
    // A guest's game: its player's commands for the host (IPlayerCommandRemote).
    void castSpell(const PartySpellCastRequest &request, std::optional<PlayerId> targetPlayer) override;
    void activateWorldHit(const GameplayWorldHit &hit) override;
    void dialogueAction(size_t selectionIndex, const EventDialogAction &action, bool overrideAction) override;
    void dialogueClose() override;
    void houseStockAction(HouseStockAction action, HouseStockMode stockMode, size_t slotIndex) override;
    void travelVote(bool accept) override;
    void proposeRest(bool heal, float minutes) override;
    void restVote(bool accept) override;
    void returnDowned() override;
    void takeWorldItem(uint32_t itemKey) override;
    void proposeTravel(const EventRuntimeState::PendingMapMove &move) override;
    void houseBankAmount(uint32_t amount) override;
    void stepOutToTravel(const EventRuntimeState::PendingMapMove &move) override;
    void stepOutOfSession() override;
    // A host's game: tells the guests that the agreed travel begins, before the map load holds this game.
    void hostTravelDeparting();
    // Whether a host is ending its session: the guests are being sent its world, and it closes when they have it.
    bool hostStopping() const;
    // A guest's game: everyone agreed and the host is loading the map; until this game's own load starts.
    bool guestDeparting() const;

    // The password the next hosting asks of who joins (empty: none), and the one the next joining gives.
    void setHostPassword(const std::string &password);
    void setJoinPassword(const std::string &password);

    // The host's game began a cinematic or a movie (Coop::PresentationCinematic, PresentationMovie): its guests'
    // games play it too.
    void hostPresentation(uint8_t kind, const std::string &name);

    // A guest's player asks the host to save; false when this game is no guest's or asked a moment ago.
    bool askHostToSave();
    // The host's game was saved: the guests are told, and each keeps what its character has now.
    void hostSaved();
    // The last thing that went wrong (a refusal, a lost connection), for the console and the status bar.
    const std::string &lastNotice() const;

    // Another player as this game shows it: on the host its guests, in a guest's game the host and the other guests.
    // What a player's character last began to do that its body shows: a blow, a shot or a cast. `serial` counts
    // them, so that whoever draws the body tells a new one; `seconds` is the recovery it began with, which the
    // body's swing is fitted to.
    struct PlayerAction
    {
        enum class Kind : uint8_t
        {
            Melee,
            Shot,
            Cast,
        };

        uint8_t serial = 0;
        Kind kind = Kind::Melee;
        float seconds = 0.0f;
    };

    struct OtherPlayer
    {
        PlayerId id = LocalPlayer;
        // The member of its party that stands for the player (the first unless the player chose another): its
        // place in the party, and below what is shown of it. Its body in the world and its face in the players
        // panel are this member's.
        uint8_t avatarMember = 0;
        std::string name;
        std::string className;
        // The character's race and sex (Character::raceId, sexId), for the body that stands for it.
        uint32_t raceId = 0;
        uint32_t sexId = 0;
        // How good what the whole party wears is (coopPartyGearTier), for the glow of its body. The host works it
        // out for everyone.
        uint8_t gearTier = 0;
        PlayerAction action;
        uint32_t portraitPictureId = 0;
        // The character's own portrait art (Character::portraitTextureName); empty where its number names it.
        std::string portraitTextureName;
        uint32_t level = 0;
        int32_t health = 0;
        int32_t maxHealth = 0;
        int32_t spellPoints = 0;
        int32_t maxSpellPoints = 0;
        // What ails it (GameMechanics::displayedCondition), one more than the condition's number; 0 when nothing.
        uint8_t condition = 0;
        bool down = false;
        // Not on the map yet (its game is loading it): it is not drawn and nothing targets it.
        bool loadingMap = false;
        // Stepped out into its own game for now, its seat kept (stepOut): shown greyed, and not on the map.
        bool away = false;
        // The party's other members in the party's order, without the one that stands for it (whom the fields
        // above describe): a player may bring a party.
        struct Mate
        {
            uint32_t portraitPictureId = 0;
            std::string portraitTextureName;
            int32_t health = 0;
            int32_t maxHealth = 0;
            uint8_t condition = 0;
        };
        std::vector<Mate> mates;
        GameplayPlayerBody body = {};
        // How fast the body moves over the ground, for its gait.
        float speed = 0.0f;
    };
    const std::vector<OtherPlayer> &otherPlayers() const;

    // What the players say to each other, oldest first and the last ChatHistory of them, and a count of every line
    // there ever was, by which whoever shows them tells a new one.
    struct ChatLine
    {
        PlayerId player = LocalPlayer;
        std::string name;
        std::string text;
    };
    static constexpr size_t ChatHistory = 64;
    const std::deque<ChatLine> &chatLines() const;
    uint32_t chatSerial() const;
    // Says a line to every player: it shows here at once and goes to the others. False outside a session and for
    // a line of nothing.
    bool sayChat(const std::string &text);
    // Which member of this game's party stands for its player in the others' games: its body in the world and its
    // face in their players panel (GameSettings::coopAvatarMember, the first by default; a party without such a
    // member shows its first). tellOwnAvatar tells a host this game has joined, after the player chose another.
    size_t ownAvatarMember() const;
    void tellOwnAvatar();

    // A place a player points the others at: on their maps and in the world for PingSeconds.
    struct Ping
    {
        PlayerId player = LocalPlayer;
        std::string name;
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        float ageSeconds = 0.0f;
    };
    static constexpr float PingSeconds = 8.0f;
    const std::vector<Ping> &pings() const;
    // Points every player, this one too, at a place on the map everyone is on. False outside a session.
    bool sendPing(float x, float y, float z);
    // A player's name as the others see it: its character's.
    std::string playerName(PlayerId player) const;

    // The host's frame, after the world moved and before its sounds are played: what the guests hear of it is taken
    // down here, since playing them empties the lists.
    void collectFrameSounds();

    // One line per fact, for the console's `coop net`.
    std::string describe() const;

    // Counts of what was sent and received, for the console and for tests.
    struct Traffic
    {
        uint64_t messagesSent = 0;
        uint64_t bytesSent = 0;
        uint64_t messagesReceived = 0;
        uint64_t bytesReceived = 0;
        // What the sent messages were before packing (Coop::PackedFlag); bytesSent is what went out.
        uint64_t bytesSentUnpacked = 0;
        // By the message's kind (Coop::Message).
        std::array<uint64_t, 64> messagesSentByKind = {};
        std::array<uint64_t, 64> bytesSentByKind = {};
        // Map sections sent, by Coop::MapSection.
        std::array<uint64_t, 8> sectionsSent = {};
    };
    const Traffic &traffic() const;

private:
    enum class Role : uint8_t
    {
        None,
        Host,
        Guest,
    };

    // A game connected to this host.
    struct HostPeer
    {
        Engine::NetPeerId peer = Engine::InvalidNetPeer;
        // LocalPlayer until its Hello was accepted.
        PlayerId player = LocalPlayer;
        std::string name;
        // The map revision the peer said it has loaded.
        uint16_t readyMapRevision = 0;
        // The peer's character as it was sent: the bytes of the last state, its number, and the last states by
        // number, which a change the peer's game sends is measured against (CoopCharacter.h).
        std::vector<uint8_t> sentPartyBytes;
        CharacterVitals sentVitals;
        uint32_t partyRevision = 0;
        std::deque<std::pair<uint32_t, Party::Snapshot>> sentParties;
        // Counts what the host did for the peer's player on its command (a cast, an event, a purchase): a change the
        // peer's game made before it knew of that is dropped.
        uint32_t commandEpoch = 0;
        // How long nothing came from the peer, and how long since the host's player was last told so.
        float silentSeconds = 0.0f;
        float silenceToldSeconds = 0.0f;
        // How long since the peer's player last asked for a save.
        float sinceAskedSaveSeconds = 1000.0f;
        // How long since the peer's game last asked for a copy of the world (the whole save, packed: not on every
        // asking), and for how long the peer has been connected without an accepted Hello.
        float sinceAskedWorldCopySeconds = 1000.0f;
        float unadmittedSeconds = 0.0f;
        // The last change of its character the peer's game sent, which the next state acknowledges.
        uint32_t putSerial = 0;
        // The last such change the host took (a change that came before the peer's game knew of a command's result
        // is dropped): what the peer's game did to the world with a dropped change is dropped too.
        uint32_t acceptedPutSerial = 0;
        bool partyStateOwed = false;
        // The last place the host put the peer's party at that its game was told (GuestPlayer::bodyOrderSerial).
        uint32_t sentBodyOrderSerial = 0;
        // The chest and the corpse the peer's player has open, as its game was last told.
        std::vector<uint8_t> sentLootViews;
        std::vector<uint8_t> sentHouseScreens;
        // The lent auras its game was last told, and the map it was told them on (its game's rules start anew
        // with each map it loads).
        std::optional<std::pair<uint16_t, std::vector<LentAura>>> sentLentAuras;
        // What changed on the map while the peer's game was loading it, in order, for when it is ready.
        std::vector<std::vector<uint8_t>> waitingMapMessages;
        size_t waitingMapBytes = 0;
        // How long the peer's game has been loading the map it was sent, and the time since its last place was taken.
        float loadingSeconds = 0.0f;
        float secondsSincePosition = 0.0f;
        // What the peer's character last began to do, as its game said with its place.
        PlayerAction action;
        // Which member of its party stands for the peer's player (Message::Avatar), the first until it says.
        uint8_t avatarMember = 0;
        // The key of the seat to keep when the peer goes: its game asked to step out (0 when it did not).
        uint64_t stepOutKey = 0;
    };
    // A player who stepped out: the key its game names when it is back, and what the others are shown of it.
    struct AwaySeat
    {
        uint64_t key = 0;
        OtherPlayer shown;
    };
    std::vector<AwaySeat> m_hostAwaySeats;
    // A guest's game: how it joined, the step out it asked the host for, and the session it stepped out of.
    struct PendingStepOut
    {
        uint64_t key = 0;
        std::optional<EventRuntimeState::PendingMapMove> move;
    };
    JoinRoute m_guestJoinRoute;
    std::optional<PendingStepOut> m_guestSteppingOut;
    std::optional<AwayFrom> m_guestAwayFrom;
    float m_guestDepartingSeconds = 0.0f;
    // The host's world as this game keeps it without asking: sent when the host saves and when it stops hosting,
    // so that a guest has it whenever the session ends. One file per join, renewed in place.
    struct KeptWorld
    {
        std::string name;
        std::filesystem::path path;
        std::string playthroughId;
        bool told = false;
    };
    std::optional<KeptWorld> m_guestKeptWorld;
    // The rules of the game this guest joined with, to say so once when the host's are others.
    std::string m_guestOwnRulesText;
    // A host ending its session: how long it still waits for the guests to have its world.
    float m_hostStopSeconds = 0.0f;
    void hostSendWorldCopy(HostPeer &peer, uint8_t kind);
    void guestFinishStepOut();

    void send(Engine::NetPeerId peer, uint8_t channel, Engine::NetDelivery delivery, const Engine::ByteWriter &message);
    void sendToAll(uint8_t channel, Engine::NetDelivery delivery, const Engine::ByteWriter &message);
    // Sends a whole message, packed when that pays (Coop::PackedFlag), and counts it.
    bool sendBytes(Engine::NetPeerId peer, uint8_t channel, Engine::NetDelivery delivery,
        const std::vector<uint8_t> &bytes);
    // The message as it was sent, or nothing when a packed one cannot be read.
    static std::optional<std::vector<uint8_t>> unpackedMessage(
        const std::vector<uint8_t> &payload, size_t maxBytes = Coop::MaxBlockBytes);
    void close();

    // --- The host's side.
    void updateHost(float deltaSeconds);
    void hostHandleEvent(const Engine::NetEvent &event);
    void hostHandleMessage(HostPeer &peer, uint8_t channel, const std::vector<uint8_t> &payload);
    void hostHandleHello(HostPeer &peer, Engine::ByteReader &reader);
    void hostHandlePosition(HostPeer &peer, Engine::ByteReader &reader);
    void hostRefuse(HostPeer &peer, const std::string &reason);
    void hostDropPeer(Engine::NetPeerId peer);
    // The map's whole state for the peer's player, sent at joining and whenever the map changed.
    bool hostSendWorldState(HostPeer &peer);
    void hostSendPlayers();
    void hostSendBodies();
    // A reliable message about the map: at once to the games that have the map loaded, and kept for the others.
    void hostSendMapMessage(const Engine::ByteWriter &message);
    // Takes the map as it stands for what the guests have: nothing of it is sent again until it changes.
    void hostPrimeMapBaselines();
    void hostSendActorRecords();
    void hostSendActorPoses();
    void hostSendMapSections();
    void hostSendProjectiles();
    void hostSendSounds();
    void hostSendPartyStates();
    // The campaign (quests, journal, shop stock, what NPCs remember), sent when it changed.
    void hostSendCampaign();
    void hostHandleCharacterPut(HostPeer &peer, Engine::ByteReader &reader);
    void hostHandleCommand(HostPeer &peer, Engine::ByteReader &reader);
    // What the host did for the peer's player that its game has to show, and where the host put its party.
    void hostSendOutcome(HostPeer &peer);
    void hostSendMoveOrders();
    void hostSendLootViews(HostPeer &peer);
    void hostSendHouseScreens(HostPeer &peer);
    // The travel proposal as it stands, sent to every guest when it changed.
    void hostSendTravelProposal();
    // What the ruleset remembers of the game (MAW's banked levels, cleared maps, pity counters), when it changed.
    void hostSendRulesState();
    void hostSendLentAuras();
    // whole: every player's record made anew (ten times a second, and when the players changed); else only where
    // each stands and what it does, which is what changes between.
    void hostRefreshOtherPlayers(bool whole);
    // What the others are shown of a player's party: the member that stands for it (`avatarMember`, the first
    // where the party has no such member), the faces of the rest, and how good what the whole party wears is.
    void fillOtherPlayer(OtherPlayer &player, const Party &party, size_t avatarMember);
    HostPeer *hostPeerOf(Engine::NetPeerId peer);
    HostPeer *hostPeerOfPlayer(PlayerId player);

    // --- A guest's side.
    void updateGuest(float deltaSeconds);
    void guestHandleEvent(const Engine::NetEvent &event);
    void guestHandleMessage(uint8_t channel, const std::vector<uint8_t> &payload);
    void guestSendHello();
    void guestHandleWorldState(Engine::ByteReader &reader);
    void guestHandlePlayers(Engine::ByteReader &reader);
    void guestHandleBodies(Engine::ByteReader &reader);
    void guestHandleActorRecords(Engine::ByteReader &reader);
    void guestHandleActorPoses(Engine::ByteReader &reader);
    void guestHandleMapSection(Engine::ByteReader &reader);
    void guestHandleProjectiles(Engine::ByteReader &reader);
    void guestHandleProjectilePoses(Engine::ByteReader &reader);
    void guestHandleSounds(Engine::ByteReader &reader);
    void guestHandleHouseScreens(Engine::ByteReader &reader);
    // A shop screen the host opened and this game's player left is closed on the host too.
    void guestSendHouseScreenChanges();
    void guestSendQuestPouchAdditions();
    void guestHandleWorldCopy(Engine::ByteReader &reader);
    void guestHandlePartyAudio(Engine::ByteReader &reader);
    // The missiles fly on between the host's messages.
    void guestAdvanceProjectiles(float deltaSeconds);
    void guestHandlePartyState(Engine::ByteReader &reader);
    void guestHandlePartyVitals(Engine::ByteReader &reader);
    void guestHandleOutcome(Engine::ByteReader &reader);
    void guestHandleMoveOrder(Engine::ByteReader &reader);
    void guestHandleLootViews(Engine::ByteReader &reader);
    void guestHandleCampaign(Engine::ByteReader &reader);
    void guestHandleTravelProposal(Engine::ByteReader &reader);
    void guestHandleRulesState(Engine::ByteReader &reader);
    void guestHandleLentAuras(Engine::ByteReader &reader);
    // What this game's player took out of the open chest or corpse or put in, or closed, since the host last knew.
    void guestSendLootChanges();
    std::vector<uint8_t> guestChestBytes() const;
    std::vector<uint8_t> guestCorpseBytes() const;
    // Puts the local party at the place the host gave it, turned as the host turned it.
    void guestPlaceParty(const GameplayPlayerBody &body);
    // Takes the host's numbers of a state it sent and what this game now has as the state the host knows.
    void guestNotePartyState(uint32_t revision, uint32_t commandEpoch);
    // A command for the host: its kind and what it carries. Returns the command's number.
    // withCharacterChange: the command is the world's half of what this frame's change of the character is the
    // other half of (a thing taken from a chest, an item dropped from the cursor): the host does it only when it
    // took that change.
    uint32_t guestSendCommand(
        Coop::Command command, const Engine::ByteWriter &payload, bool withCharacterChange = false);
    // What this game's replica kept for the host since the last frame: its player's blows and the places stepped on.
    void guestSendWorldRequests();
    // Sends what this game did with the character since the host last knew.
    void guestSendCharacterPut();
    // The character and what the cursor holds, as bytes to compare.
    std::vector<uint8_t> guestCharacterBytes() const;
    void guestSendPosition();
    // Back to the game this one had before it joined.
    void guestReturnToOwnGame(const std::string &notice);

    GameApplication &m_application;
    GameSession &m_session;
    Role m_role = Role::None;
    std::unique_ptr<Engine::INetTransport> m_pTransport;
    // The transport again when it is the UDP one, for what only that has (the lobby's datagrams, a port); null on
    // the in-process one.
    Engine::EnetTransport *m_pEnet = nullptr;
    // This game's side of the lobby: a host's registration, or a joining game's search for a path.
    std::unique_ptr<Engine::RendezvousClient> m_pLobby;
    std::string m_hostName;
    // This hosting's number in its answers to a scan of the network (Engine::LanSessionInfo::sessionId).
    uint32_t m_hostSessionId = 0;
    std::string m_hostPassword;
    std::string m_joinPassword;
    // A guest: how long nothing came from the host, how long since its player was told so, and since it asked the
    // host to save.
    float m_guestSilentSeconds = 0.0f;
    float m_guestSilenceToldSeconds = 0.0f;
    float m_guestSinceAskedSaveSeconds = 1000.0f;
    // A joining game that waits for the lobby to find it a path; it connects when there is one.
    bool m_guestFindingPath = false;
    Engine::LanSessionInfo sessionInfoForScan() const;
    Engine::SessionInfo sessionInfoForLobby() const;
    void startLobbyClient(const Engine::NetAddress &lobby);
    Traffic m_traffic;
    std::string m_lastNotice;
    // What the host said before it ended the connection (it refused the join, it ended the game): the reason the
    // player is told when the connection then ends. Not m_lastNotice, which holds whatever was last said.
    std::string m_guestGoodbye;
    // What this game's own character last began to do, read off the first-person arms' counters every frame.
    PlayerAction m_ownAction;
    uint32_t m_ownActionSeenSwings = 0;
    uint32_t m_ownActionSeenActions = 0;
    uint32_t m_ownActionSeenTalents = 0;
    // The spells cast, and when the body was last told of an action (netNowMilliseconds): a cast the arms already
    // showed as a swing is not shown twice.
    uint32_t m_ownActionSeenCasts = 0;
    uint32_t m_ownActionAtMs = 0;
    void updateOwnAction();
    std::deque<ChatLine> m_chatLines;
    uint32_t m_chatSerial = 0;
    std::vector<Ping> m_pings;
    void addChatLine(PlayerId player, const std::string &text);
    void addPing(PlayerId player, float x, float y, float z);
    std::vector<OtherPlayer> m_otherPlayers;
    // Counts up with every map the host has loaded while hosting; what a message says about a map carries it, and one
    // from another map is dropped.
    uint16_t m_mapRevision = 0;

    // Host.
    std::vector<HostPeer> m_hostPeers;
    // The world runtime and map the guests were last sent, so that a change of either sends the state again.
    const IGameplayWorldRuntime *m_pHostSentWorldRuntime = nullptr;
    uint32_t m_hostMapLoadSerial = 0;
    float m_hostStreamSeconds = 0.0f;
    float m_hostStateSeconds = 0.0f;
    // Counts the state ticks: what changes seldom and is costly to compare (the campaign) goes out every few.
    uint32_t m_hostStateTick = 0;
    bool m_hostCampaignDue = false;
    std::vector<uint8_t> m_hostSentPlayersBytes;
    // The tiers a worn item is drawn in (engine/world_items/held_tiers.yml), read with the first player shown; left
    // without tiers where the file cannot be read, and no body glows then.
    std::unique_ptr<HeldSkinRules> m_pGearRules;
    std::vector<uint8_t> m_hostSentCampaignBytes;
    std::vector<uint8_t> m_hostSentTravelBytes;
    std::vector<uint8_t> m_hostSentRulesBytes;
    // What the guests have of the map: each monster's record signature and the pose last sent, and the sections.
    struct HostActorStream
    {
        ReplicaActorPose sent = {};
        // How many more times the pose goes out although it did not change: a pose that was lost is not sent again
        // by itself.
        uint8_t resend = 0;
        bool known = false;
    };
    std::vector<uint64_t> m_hostActorSignatures;
    std::vector<HostActorStream> m_hostActorStreams;
    size_t m_hostActorRefreshCursor = 0;
    uint32_t m_hostPoseTick = 0;
    std::vector<uint8_t> m_hostSentEventState;
    std::vector<uint8_t> m_hostSentWorldItems;
    uint64_t m_hostSentMechanismsKey = 0;
    // The missiles and impact effects the guests know of, each missile with where it last was.
    std::unordered_map<uint32_t, GameplayWorldPoint> m_hostSentProjectiles;
    std::unordered_set<uint32_t> m_hostSentImpacts;
    // The world's sounds since the last send, and how many of the outdoor map's own list are among them.
    std::vector<EventRuntimeState::PendingSound> m_hostSoundOutbox;
    size_t m_hostCollectedOutdoorSounds = 0;

    // Guest.
    Engine::NetPeerId m_guestHostPeer = Engine::InvalidNetPeer;
    bool m_guestConnected = false;
    bool m_guestWelcomed = false;
    bool m_guestMapLoaded = false;
    PlayerId m_guestOwnPlayer = LocalPlayer;
    float m_guestPositionSeconds = 0.0f;
    float m_guestConnectSeconds = 0.0f;
    // The pose each monster was last given, to give again after the map's event state was taken.
    std::vector<std::optional<ReplicaActorPose>> m_guestActorPoses;
    // The character as the host last had it here, or as this game last sent it; the host's numbers it came with; and
    // the number of this game's last change.
    std::vector<uint8_t> m_guestCharacterBytes;
    bool m_guestHasPartyState = false;
    uint32_t m_guestPartyRevision = 0;
    uint32_t m_guestCommandEpoch = 0;
    uint32_t m_guestPutSerial = 0;
    // The number of the change of the character sent in this frame; 0 when none was.
    uint32_t m_guestFramePutSerial = 0;
    // The write of this game's own save that is under way off the frame thread (writeGuestOwnGame); waited for
    // before anything else writes that file.
    std::future<void> m_guestOwnGameWrite;
    // The lobby a hosted game registers with, while its address is being looked up (host, updateHost).
    LobbyLookup m_hostLobbyLookup;
    bool m_hostLobbyAsked = false;
    void hostRegisterWithLobby(const Engine::NetAddress &lobby);
    void waitForOwnGameWrite();
    uint32_t m_guestCommandSerial = 0;
    // The last place the host put this game's party at (Message::MoveOrder); positions sent carry it.
    uint32_t m_guestBodyOrderSerial = 0;
    // The open chest and corpse as the host last had them here, or as this game last sent them.
    std::vector<uint8_t> m_guestChestBytes;
    // The shop screens the host has open for this player.
    bool m_guestHostStockScreen = false;
    bool m_guestHostServiceScreen = false;
    std::vector<uint8_t> m_guestCorpseBytes;
    // The game this one had before it joined, and its save file.
    // The character file this game joined with and where it lies (setJoinCharacter); none when it joined with the
    // character of the game in progress.
    std::optional<CharacterFile> m_guestCharacterFile;
    std::filesystem::path m_guestCharacterPath;
    float m_guestCharacterWriteSeconds = 0.0f;
    // The world's quest pouch as the host has it by what this game knows: what the host last sent, and what this
    // game told it of since (guestSendQuestPouchAdditions).
    std::vector<InventoryItem> m_guestHostQuestPouch;
    // The host's news of the whole game (its quests, the ruleset's state, a vote that waits) that came before the
    // host's world was loaded here, the newest of each kind: this game is still the guest's own until then, and
    // they are for the host's world. Applied when the world is loaded.
    std::unordered_map<uint8_t, std::vector<uint8_t>> m_guestHeldGameNews;
    // The save a world copy the host was asked for is written to (keepWorldCopy); empty while none is awaited.
    std::filesystem::path m_guestWorldCopyPath;
    std::string m_guestWorldCopyName;
    std::optional<GameSaveData> m_guestOwnGame;
    std::optional<std::filesystem::path> m_guestOwnSavePath;
};
}
