#include "game/coop/CoopSession.h"

#include "engine/Localization.h"
#include "engine/net/ByteStream.h"
#include "engine/net/EnetTransport.h"
#include "engine/net/NetCompression.h"
#include "game/app/GameApplication.h"
#include "game/app/GameSession.h"
#include "game/coop/CoopBodies.h"
#include "game/coop/CoopCharacter.h"
#include "game/coop/CoopCodec.h"
#include "game/coop/ReplicaWorldCalls.h"
#include "game/events/EventDialogContent.h"
#include "game/events/EventRuntime.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayInteractionController.h"
#include "game/gameplay/HouseServiceRuntime.h"
#include "game/maps/SaveSections.h"
#include "game/party/PlaythroughStatistics.h"
#include "game/render/HeldWeapons.h"

#include <chrono>
#include <random>
#include <cctype>
#include <iostream>
#include <algorithm>
#include <cmath>
#include <sstream>

namespace OpenYAMM::Game
{
namespace
{
using CoopCodec::finiteBody;
using CoopCodec::finitePose;
using CoopCodec::readBody;
using CoopCodec::readPose;
using CoopCodec::writeBody;
using CoopCodec::writePose;

// How often the host sends where everything is, and how often it looks for state that changed.
constexpr float StreamIntervalSeconds = 1.0f / 20.0f;
constexpr float StateIntervalSeconds = 1.0f / 10.0f;
// How often a guest sends where it stands.
constexpr float PositionIntervalSeconds = 1.0f / 20.0f;
// How long a guest waits for the host's answer before it gives up.
constexpr float ConnectTimeoutSeconds = 10.0f;
// A guest whose game has not loaded the map it was sent after this long is dropped; the others play on.
constexpr float MapLoadTimeoutSeconds = 120.0f;
// The farthest a guest's place may move: this fast, and this much besides for a blink or a shove. A place farther
// off than that is not taken, and the guest's game is put back where the host has its character. Above anything a
// character does on foot or in the air, far below a jump across the map.
constexpr float MaxGuestUnitsPerSecond = 6000.0f;
constexpr float GuestPositionSlack = 1024.0f;
// How often a guest that joined with a character file writes it while it plays.
constexpr float CharacterFileWriteSeconds = 120.0f;
// A game is told that the other side is silent after this long without a message from it, and again this often.
constexpr float SilenceToldAfterSeconds = 4.0f;
constexpr float SilenceToldEverySeconds = 4.0f;
// A guest's player may ask the host to save this often.
constexpr float AskSaveEverySeconds = 10.0f;
// A copy of the whole world is sent to one game no more often than this.
constexpr float WorldCopyEverySeconds = 10.0f;
// What may wait for a game that is loading the map; and the mark of a peer that was let go for more than that.
constexpr size_t MaxWaitingMapBytes = 32u * 1024u * 1024u;
constexpr uint16_t UnreadyForGood = 0xffff;
// No party is lent more auras than there are aura spells; a message that names more is not the host's.
constexpr size_t MaxLentAuras = 64;
// The campaign is compared and sent on every this many state ticks (ten a second).
constexpr uint32_t CampaignEveryStateTicks = 5;
// A connection that has not said an accepted Hello after this long is ended, and what it may send packed until then.
constexpr float UnadmittedSeconds = 15.0f;
constexpr size_t MaxUnadmittedBytes = 4u * 1024u * 1024u;
// How far from where the host has a guest a lying item may be for the guest to take it: a player's reach, and as
// much again for the steps the host has not heard of yet.
constexpr float TakeReach = 1024.0f;
// A guest appears this far beside the host, and each further guest as far again.
constexpr float GuestArrivalSpacing = 96.0f;
// What a WorldCopy is: the one a guest's player asked for by a name, the one kept without asking when the host
// saved, and the last one of a host that is ending its session.
constexpr uint8_t WorldCopyAsked = 0;
constexpr uint8_t WorldCopyKept = 1;
constexpr uint8_t WorldCopyLast = 2;
// How long a host that ends its session waits for its guests to have its world.
constexpr float HostStopSeconds = 20.0f;
// A pose that changed goes out this many times: the stream may lose one.
constexpr uint8_t PoseResendCount = 3;
// Monsters whose pose goes out each time whether it changed or not.
constexpr size_t PoseRefreshPerTick = 6;
// Monsters within this of a guest have their place sent every time; the others every FarPoseTicks times.
constexpr float NearPoseDistance = 2560.0f;
constexpr uint32_t FarPoseTicks = 4;
// As many poses as fit one datagram, and as many records as make a message of a reasonable size.
constexpr size_t PosesPerMessage = 24;
constexpr size_t ActorRecordsPerMessage = 32;
// How many of the states sent to a guest the host keeps to measure the guest's changes against.
constexpr size_t SentPartyHistory = 32;
// What a guest's dialogue command asks for.
constexpr uint8_t DialogueOperationSelect = 0;
constexpr uint8_t DialogueOperationOverride = 1;
constexpr uint8_t DialogueOperationClose = 2;
// What a guest's rest command says, and the longest rest or wait a player may ask for (a week).
constexpr uint8_t RestOperationPropose = 0;
constexpr uint8_t RestOperationVote = 1;
constexpr float MaxRestMinutes = 7.0f * 24.0f * 60.0f;

// What a guest's house command says besides the HouseStockAction values.
constexpr uint8_t HouseOperationCloseStock = 16;
constexpr uint8_t HouseOperationCloseService = 17;
// The amount the guest's player typed at the bank, in the place of the slot's number.
constexpr uint8_t HouseOperationBankAmount = 18;

// The screens of a shop that work on the player's own things.
bool isShopServiceMode(GameplayUiController::InventoryNestedOverlayMode mode)
{
    return mode == GameplayUiController::InventoryNestedOverlayMode::ShopSell
        || mode == GameplayUiController::InventoryNestedOverlayMode::ShopIdentify
        || mode == GameplayUiController::InventoryNestedOverlayMode::ShopRepair;
}

// What the host's missile message tells of.
constexpr uint8_t ProjectileEventSpawn = 0;
constexpr uint8_t ProjectileEventEnd = 1;
constexpr uint8_t ProjectileEventImpact = 2;
// As many missiles as have their place sent each time, and how fast a missile's own clock runs.
constexpr uint16_t MaxProjectilePoses = 48;
constexpr float ProjectileTicksPerSecond = 128.0f;
// More sounds than this waiting to go out are of no use to anyone: the oldest are let go.
constexpr size_t MaxQueuedSounds = 128;

// What a guest's chest command says.
constexpr uint8_t LootOperationPutChest = 0;
constexpr uint8_t LootOperationPutCorpse = 1;
constexpr uint8_t LootOperationClose = 2;

// Whether a monster's pose is news for a game that has `sent`. A running animation's clock and a running action's
// time are not: each game runs them itself.
bool poseDiffers(const ReplicaActorPose &pose, const ReplicaActorPose &sent)
{
    return pose.x != sent.x || pose.y != sent.y || pose.z != sent.z || pose.yawRadians != sent.yawRadians
        || pose.velocityX != sent.velocityX || pose.velocityY != sent.velocityY || pose.velocityZ != sent.velocityZ
        || pose.intendedSpeed != sent.intendedSpeed || pose.hp != sent.hp || pose.animation != sent.animation
        || pose.aiState != sent.aiState || pose.attackAbility != sent.attackAbility
        || pose.skirmishPhase != sent.skirmishPhase || pose.flags != sent.flags
        || pose.animationTimeTicks < sent.animationTimeTicks;
}

// What tells a mover's state apart for a game that moves it itself between the host's messages: a move's progress
// and a spin's angle do not.
uint64_t mechanismsKey(const std::unordered_map<uint32_t, RuntimeMechanismState> &mechanisms)
{
    uint64_t key = mechanisms.size();

    for (const auto &[id, mechanism] : mechanisms)
    {
        uint64_t one = 1469598103934665603ull;
        const auto mix = [&one](uint64_t value)
        {
            one = (one ^ value) * 1099511628211ull;
        };
        mix(id);
        mix(mechanism.state);
        mix(uint64_t(mechanism.rotationDirection + 2));
        mix(mechanism.isMoving ? 1 : 0);
        mix(mechanism.spinOn ? 1 : 0);
        mix(uint64_t(mechanism.spinDirection + 2));
        mix(mechanism.spinSet ? 1 : 0);
        // Summed: the map's order is not the same in two games.
        key += one;
    }

    return key;
}

// The event state a guest is sent: without what is one game's own, and without the movers, which travel apart.
std::vector<uint8_t> encodeSharedEventState(const EventRuntimeState &eventState)
{
    EventRuntimeState shared = eventState;
    clearTransientEventRuntimeState(shared);
    shared.mechanisms.clear();
    shared.coopParties.clear();
    return SaveSections::encode(shared);
}

void writeHeldItem(Engine::ByteWriter &writer, const std::optional<InventoryItem> &heldItem)
{
    writer.boolean(heldItem.has_value());

    if (heldItem)
    {
        writer.block(SaveSections::encode(*heldItem));
    }
}

bool readHeldItem(Engine::ByteReader &reader, std::optional<InventoryItem> &heldItem)
{
    heldItem.reset();

    if (!reader.boolean())
    {
        return reader.ok();
    }

    InventoryItem item;

    if (!SaveSections::decode(reader.block(Coop::MaxBlockBytes), item))
    {
        reader.fail();
        return false;
    }

    heldItem = item;
    return reader.ok();
}

void writeVitals(Engine::ByteWriter &writer, const CharacterVitals &vitals)
{
    writer.u8(uint8_t(vitals.members.size()));

    for (const CharacterVitals::Member &member : vitals.members)
    {
        writer.i32(member.health);
        writer.i32(member.spellPoints);
        writer.f32(member.recoverySecondsRemaining);
    }

    for (float seconds : vitals.partyBuffSeconds)
    {
        writer.f32(seconds);
    }

    writer.u16(uint16_t(vitals.characterBuffSeconds.size()));

    for (float seconds : vitals.characterBuffSeconds)
    {
        writer.f32(seconds);
    }

    writer.f32(vitals.itemEffectElapsedGameSeconds);
}

CharacterVitals readVitals(Engine::ByteReader &reader)
{
    CharacterVitals vitals;
    const size_t memberCount = reader.u8();

    for (size_t member = 0; member < memberCount && reader.ok(); ++member)
    {
        CharacterVitals::Member one;
        one.health = reader.i32();
        one.spellPoints = reader.i32();
        one.recoverySecondsRemaining = reader.f32();
        vitals.members.push_back(one);
    }

    for (float &seconds : vitals.partyBuffSeconds)
    {
        seconds = reader.f32();
    }

    const size_t characterBuffCount = reader.u16();

    for (size_t buff = 0; buff < characterBuffCount && reader.ok(); ++buff)
    {
        vitals.characterBuffSeconds.push_back(reader.f32());
    }

    vitals.itemEffectElapsedGameSeconds = reader.f32();
    return vitals;
}

Engine::ByteWriter beginMessage(Coop::Message message)
{
    Engine::ByteWriter writer;
    writer.u8(uint8_t(message));
    return writer;
}

void writeAction(Engine::ByteWriter &message, const CoopSession::PlayerAction &action)
{
    message.u8(action.serial);
    message.u8(uint8_t(action.kind));
    message.f32(action.seconds);
}

CoopSession::PlayerAction readAction(Engine::ByteReader &reader)
{
    CoopSession::PlayerAction action;
    action.serial = reader.u8();
    const uint8_t kind = reader.u8();
    action.kind = kind <= uint8_t(CoopSession::PlayerAction::Kind::Cast) ? CoopSession::PlayerAction::Kind(kind)
        : CoopSession::PlayerAction::Kind::Melee;
    const float seconds = reader.f32();
    action.seconds = std::isfinite(seconds) ? std::clamp(seconds, 0.0f, 10.0f) : 0.0f;
    return action;
}

// `avatarMember`: the member that stands for the player; the first where the party has no such member.
void fillOtherPlayerFromParty(CoopSession::OtherPlayer &player, const Party &party, size_t avatarMember)
{
    const size_t avatar = avatarMember < party.members().size() ? avatarMember : 0;
    const Character *pMember = party.member(avatar);

    if (pMember == nullptr)
    {
        return;
    }

    player.avatarMember = uint8_t(avatar);
    player.name = pMember->name;
    player.className = pMember->className;
    player.raceId = pMember->raceId;
    player.sexId = pMember->sexId;
    player.portraitPictureId = pMember->portraitPictureId;
    player.portraitTextureName = pMember->portraitTextureName;
    player.level = pMember->level;
    player.health = pMember->health;
    player.maxHealth = pMember->maxHealth;
    player.spellPoints = pMember->spellPoints;
    player.maxSpellPoints = pMember->maxSpellPoints;
    const std::optional<CharacterCondition> condition = GameMechanics::displayedCondition(*pMember);
    player.condition = condition ? uint8_t(uint8_t(*condition) + 1) : uint8_t(0);
    player.down = !party.hasActableMember();
    player.mates.clear();

    for (size_t index = 0; index < party.members().size() && player.mates.size() < Coop::MaxPartyMates; ++index)
    {
        if (index == avatar)
        {
            continue;
        }

        const Character &member = party.members()[index];
        const std::optional<CharacterCondition> ails = GameMechanics::displayedCondition(member);
        player.mates.push_back(CoopSession::OtherPlayer::Mate{member.portraitPictureId, member.portraitTextureName,
            member.health, member.maxHealth, ails ? uint8_t(uint8_t(*ails) + 1) : uint8_t(0)});
    }
}
}

CoopSession::CoopSession(GameApplication &application)
    : m_application(application)
    , m_session(application.m_gameSession)
{
}

CoopSession::~CoopSession() = default;

bool CoopSession::host(uint16_t port, std::string &error, const std::string &name, const std::string &lobbyAddress)
{
    if (m_role != Role::None)
    {
        error = "a co-op session is already running";
        return false;
    }

    if (m_session.activeWorldRuntime() == nullptr)
    {
        error = "there is no game to host";
        return false;
    }

    std::unique_ptr<Engine::EnetTransport> pTransport = std::make_unique<Engine::EnetTransport>();

    if (!pTransport->open(port, Coop::MaxGuests))
    {
        error = "could not open UDP port " + std::to_string(port);
        return false;
    }

    Engine::EnetTransport *pEnet = pTransport.get();
    hostOn(std::move(pTransport));
    m_pEnet = pEnet;
    m_hostName = name.empty() ? Engine::tr("{name}'s world", {{"name", playerName(LocalPlayer)}}) : name;
    m_hostSessionId = std::max<uint32_t>(1u, std::random_device{}());

    // The game is hosted for the local network at once. The lobby's name is looked up beside the game (that can
    // take seconds, or fail without a network), and the game registers there when its address is known
    // (updateHost); an address written in numbers is known now.
    m_hostLobbyAsked = !lobbyAddress.empty();

    if (m_hostLobbyAsked)
    {
        m_hostLobbyLookup.start(lobbyAddress, Coop::DefaultLobbyPort);

        if (const std::optional<Engine::NetAddress> lobby = m_hostLobbyLookup.address())
        {
            m_hostLobbyAsked = false;
            hostRegisterWithLobby(*lobby);
        }
    }

    // The socket's other callers besides the connection: a game that scans the local network, and the lobby.
    m_pEnet->setDatagramHandler([this](const Engine::NetAddress &from, std::span<const uint8_t> datagram)
    {
        if (const std::optional<uint32_t> question = Engine::decodeLanProbe(datagram))
        {
            m_pEnet->sendDatagram(from, Engine::encodeLanAnswer(*question, sessionInfoForScan()));
            return true;
        }

        return m_pLobby != nullptr && m_pLobby->handleDatagram(from, datagram, Engine::netNowMilliseconds());
    });
    return true;
}

void CoopSession::hostRegisterWithLobby(const Engine::NetAddress &lobby)
{
    startLobbyClient(lobby);
    Engine::NetAddress local = Engine::localAddressTowards(lobby);
    local.port = m_pEnet->localPort();
    m_pLobby->startHosting(sessionInfoForLobby(), local);
}

void CoopSession::startLobbyClient(const Engine::NetAddress &lobby)
{
    m_pLobby = std::make_unique<Engine::RendezvousClient>(
        [this](const Engine::NetAddress &to, std::span<const uint8_t> datagram)
        {
            if (m_pEnet != nullptr)
            {
                m_pEnet->sendDatagram(to, datagram);
            }
        },
        lobby);
}

Engine::LanSessionInfo CoopSession::sessionInfoForScan() const
{
    Engine::LanSessionInfo info;
    info.name = m_hostName;
    info.world = m_application.m_activeWorldManifest.id;
    // With its difficulty and kind where a ruleset has them: what a game must match to join.
    info.ruleset = coopRulesText(m_session.ruleset());
    info.protocol = Coop::ProtocolVersion;
    info.players = uint8_t(1 + m_session.guestPlayers().size());
    info.maxPlayers = uint8_t(1 + Coop::MaxGuests);
    info.sessionId = m_hostSessionId;
    info.locked = !m_hostPassword.empty();
    return info;
}

Engine::SessionInfo CoopSession::sessionInfoForLobby() const
{
    const Engine::LanSessionInfo scan = sessionInfoForScan();
    Engine::SessionInfo info;
    info.name = scan.name;
    info.world = scan.world;
    info.ruleset = scan.ruleset;
    info.protocolBuild = scan.protocol;
    info.players = scan.players;
    info.maxPlayers = scan.maxPlayers;
    info.flags = uint8_t(Engine::SessionFlagListed | (scan.locked ? Engine::SessionFlagPassword : 0));
    return info;
}

const std::string &CoopSession::hostName() const
{
    return m_hostName;
}

uint16_t CoopSession::hostPort() const
{
    return m_role == Role::Host && m_pEnet != nullptr ? m_pEnet->localPort() : 0;
}

std::string CoopSession::hostCode() const
{
    return m_role == Role::Host && m_pLobby != nullptr && m_pLobby->registered() ? m_pLobby->sessionCode()
        : std::string();
}

bool CoopSession::hostAsksLobby() const
{
    return m_role == Role::Host && (m_pLobby != nullptr || m_hostLobbyAsked);
}

bool CoopSession::joinByCode(
    const std::string &lobbyAddress,
    const std::string &code,
    std::string &error,
    bool relayOnly)
{
    if (m_role != Role::None)
    {
        error = "a co-op session is already running";
        return false;
    }

    if (m_session.partyOfPlayer(LocalPlayer) == nullptr)
    {
        error = "there is no character to join with: start or load a game first";
        return false;
    }

    const std::optional<Engine::NetAddress> lobby = Engine::parseNetAddress(
        lobbyAddress.find(':') == std::string::npos ? lobbyAddress + ":" + std::to_string(Coop::DefaultLobbyPort)
                                                    : lobbyAddress);
    const std::optional<Engine::SessionCode> sessionCode = Engine::parseSessionCode(code);

    if (!lobby)
    {
        error = "could not resolve the lobby at " + lobbyAddress;
        return false;
    }

    if (!sessionCode)
    {
        error = "that is no session code";
        return false;
    }

    std::unique_ptr<Engine::EnetTransport> pTransport = std::make_unique<Engine::EnetTransport>();

    if (!pTransport->open(0, 1))
    {
        error = "could not open a UDP socket";
        return false;
    }

    Engine::EnetTransport *pEnet = pTransport.get();
    joinOn(std::move(pTransport), Engine::InvalidNetPeer);
    m_guestJoinRoute = JoinRoute{JoinRoute::Kind::Code, {}, lobbyAddress, code, relayOnly};
    m_pEnet = pEnet;
    startLobbyClient(*lobby);
    m_pEnet->setDatagramHandler([this](const Engine::NetAddress &from, std::span<const uint8_t> datagram)
    {
        return m_pLobby != nullptr && m_pLobby->handleDatagram(from, datagram, Engine::netNowMilliseconds());
    });
    Engine::NetAddress local = Engine::localAddressTowards(*lobby);
    local.port = m_pEnet->localPort();
    m_pLobby->startJoin(*sessionCode, local, relayOnly);
    m_guestFindingPath = true;
    return true;
}

void CoopSession::hostOn(std::unique_ptr<Engine::INetTransport> pTransport)
{
    close();
    m_pTransport = std::move(pTransport);
    m_role = Role::Host;
    m_mapRevision = 1;
    m_pHostSentWorldRuntime = m_session.activeWorldRuntime();
    m_hostMapLoadSerial = m_application.m_mapLoadSerial;
    m_session.setCoopSession(true);
    m_session.setCoopRole(GameSession::CoopRole::Host);
    m_lastNotice.clear();
    hostPrimeMapBaselines();
}

bool CoopSession::join(const std::string &address, std::string &error)
{
    if (m_role != Role::None)
    {
        error = "a co-op session is already running";
        return false;
    }

    if (m_session.partyOfPlayer(LocalPlayer) == nullptr)
    {
        error = "there is no character to join with: start or load a game first";
        return false;
    }

    const std::string withPort =
        address.find(':') == std::string::npos ? address + ":" + std::to_string(Coop::DefaultPort) : address;
    const std::optional<Engine::NetAddress> hostAddress = Engine::parseNetAddress(withPort);

    if (!hostAddress)
    {
        error = "could not resolve " + withPort;
        return false;
    }

    std::unique_ptr<Engine::EnetTransport> pTransport = std::make_unique<Engine::EnetTransport>();

    if (!pTransport->open(0, 1))
    {
        error = "could not open a UDP socket";
        return false;
    }

    const Engine::NetPeerId hostPeer = pTransport->connect(*hostAddress);

    if (hostPeer == Engine::InvalidNetPeer)
    {
        error = "could not start the connection to " + withPort;
        return false;
    }

    joinOn(std::move(pTransport), hostPeer);
    m_guestJoinRoute = JoinRoute{JoinRoute::Kind::Address, address, {}, {}, false};
    return true;
}

void CoopSession::joinOn(std::unique_ptr<Engine::INetTransport> pTransport, Engine::NetPeerId hostPeer)
{
    // A join begins its count of the character's changes anew: the host's record of this game is new, and a
    // state it sends is taken only when it answers this game's last change by its number. Left from an earlier
    // join in the same run, the numbers never met again and the character stood still in both games.
    m_guestPutSerial = 0;
    m_guestPartyRevision = 0;
    m_guestCommandEpoch = 0;
    m_guestCommandSerial = 0;
    m_guestBodyOrderSerial = 0;
    m_guestHasPartyState = false;
    close();
    m_guestJoinRoute = {};
    m_guestKeptWorld.reset();
    m_pTransport = std::move(pTransport);
    m_role = Role::Guest;
    m_guestHostPeer = hostPeer;
    m_guestConnected = false;
    m_guestWelcomed = false;
    m_guestMapLoaded = false;
    m_guestOwnPlayer = LocalPlayer;
    m_guestConnectSeconds = 0.0f;
    m_lastNotice.clear();
    // This game's own quest items stay with its own world: they leave the character's bags before it is sent.
    m_session.setQuestPouchShared(true);
}

void CoopSession::close()
{

    if (m_role == Role::Host)
    {
        // The guests' parties leave the world with their games.
        for (const HostPeer &peer : m_hostPeers)
        {
            if (peer.player != LocalPlayer)
            {
                m_session.removeGuestPlayer(peer.player);
            }
        }
    }

    if (m_role == Role::Host && m_pLobby != nullptr)
    {
        // The lobby drops the session now, not when it stops hearing of it.
        m_pLobby->stopHosting();
    }

    if (m_role == Role::Host)
    {
        m_hostAwaySeats.clear();
    }

    m_guestSteppingOut.reset();
    m_guestDepartingSeconds = 0.0f;
    m_hostLobbyAsked = false;
    m_hostStopSeconds = 0.0f;
    m_hostPeers.clear();
    m_otherPlayers.clear();
    m_hostSentPlayersBytes.clear();
    m_pLobby.reset();
    m_pEnet = nullptr;
    m_guestFindingPath = false;
    m_hostName.clear();
    m_pTransport.reset();
    m_session.playerCommands().setRemote(nullptr);

    if (m_role != Role::None)
    {
        // What the players were asked goes with the session: a vote left standing would pass in the game that
        // remains, with nobody else to answer it, and take it to that map alone.
        m_session.setReplicaTravelProposal(std::nullopt);
        m_session.setReplicaRestProposal(std::nullopt);

        // What the other players' parties lent this one stays with the session (a host's game clears its own:
        // GameSession::updateLentAuras).
        if (Party *pParty = m_role == Role::Guest ? m_session.partyOfPlayer(LocalPlayer) : nullptr)
        {
            pParty->rules().spells.setLentAuras({});
        }

        // The vote's window too: its serial left standing would refuse every dialogue's close in the game after.
        m_session.setTravelPromptSerial(0, {});
        m_session.setCoopRole(GameSession::CoopRole::None);
        m_session.setCoopSession(false);
    }

    m_role = Role::None;
    m_guestHostPeer = Engine::InvalidNetPeer;
    m_guestConnected = false;
    m_guestWelcomed = false;
    m_guestMapLoaded = false;
    m_guestOwnPlayer = LocalPlayer;
    m_guestCharacterFile.reset();
    m_guestCharacterPath.clear();
    m_guestCharacterWriteSeconds = 0.0f;
    // A world copy asked of this host is not the next host's to fill.
    m_guestWorldCopyPath.clear();
    m_guestWorldCopyName.clear();
    m_guestGoodbye.clear();
    m_hostSentCampaignBytes.clear();
    m_hostSentTravelBytes.clear();
    m_hostSentRulesBytes.clear();
    m_guestHeldGameNews.clear();
    m_guestHostQuestPouch.clear();
    m_chatLines.clear();
    m_pings.clear();
}

bool CoopSession::keepWorldCopy(const std::string &name, bool replace, std::string &error)
{
    if (m_role != Role::Guest || !m_guestMapLoaded)
    {
        error = "only a guest in a host's world can keep a copy of it";
        return false;
    }

    std::string fileName;

    for (const char character : name)
    {
        const unsigned char value = static_cast<unsigned char>(character);
        fileName.push_back(std::isalnum(value) != 0 || character == '-' || character == '_' ? character : '_');
    }

    if (fileName.empty())
    {
        error = "the copy needs a name";
        return false;
    }

    const std::filesystem::path path = std::filesystem::path("saves") / (fileName + ".oysav");
    std::error_code fileError;

    if (!replace && std::filesystem::exists(path, fileError))
    {
        error = path.string() + " is there already: choose another name, or say replace";
        return false;
    }

    m_guestWorldCopyPath = path;
    m_guestWorldCopyName = name;
    Engine::ByteWriter request = beginMessage(Coop::Message::WorldCopyRequest);
    send(m_guestHostPeer, Coop::ChannelControl, Engine::NetDelivery::Reliable, request);
    return true;
}

void CoopSession::guestHandleWorldCopy(Engine::ByteReader &reader)
{
    const uint8_t kind = reader.u8();
    const std::vector<uint8_t> bytes = reader.block(Coop::MaxBlockBytes);
    std::string error;
    std::optional<GameSaveData> world = reader.ok() ? SaveSections::decodeGame(bytes, error) : std::nullopt;

    // The copy nobody asked for (the host saved, or is ending its session): kept in one file of this join, named
    // after the host, renewed in place.
    if (kind != WorldCopyAsked)
    {
        if (!world)
        {
            return;
        }

        if (!m_guestKeptWorld)
        {
            const std::string host = playerName(LocalPlayer);
            KeptWorld kept;
            kept.name = host.empty() ? Engine::tr("The host's world") : Engine::tr("{name}'s world", {{"name", host}});
            std::string fileName = "coop_world_";

            // Named by the host's character and its game, so that two hosts of one name keep two files.
            for (const char character : host + "_" + world->playthroughId.substr(0, 8))
            {
                const unsigned char value = static_cast<unsigned char>(character);
                fileName.push_back(std::isalnum(value) != 0 ? character : '_');
            }

            kept.path = std::filesystem::path("saves") / (fileName + ".oysav");
            kept.playthroughId = PlaythroughStatistics::newPlaythroughId();
            m_guestKeptWorld = std::move(kept);
        }

        world->playthroughId = m_guestKeptWorld->playthroughId;
        world->playthroughTimeline.clear();
        world->playthroughPlayedSeconds = 0.0;
        world->saveName = m_guestKeptWorld->name;
        world->previewBmp.clear();

        if (!saveGameDataToPath(m_guestKeptWorld->path, *world, error))
        {
            m_guestKeptWorld.reset();
            return;
        }

        if (kind == WorldCopyLast)
        {
            // The connection ends next: this is what the player is told then.
            m_guestGoodbye = Engine::tr("The host ended the game. Its world is kept as {name}, under Load Game.",
                {{"name", m_guestKeptWorld->name}});
            m_lastNotice = m_guestGoodbye;
        }
        else if (!m_guestKeptWorld->told)
        {
            m_guestKeptWorld->told = true;
            m_session.gameplayScreenRuntime().setStatusBarEvent(
                Engine::tr("This world is kept for you as {name}, renewed when the host saves",
                    {{"name", m_guestKeptWorld->name}}),
                6.0f);
        }

        return;
    }

    const std::filesystem::path path = std::move(m_guestWorldCopyPath);
    const std::string name = std::move(m_guestWorldCopyName);
    m_guestWorldCopyPath.clear();
    m_guestWorldCopyName.clear();

    if (path.empty() || !world)
    {
        return;
    }

    // A game of its own from here on: another playthrough than the host's, with no history yet.
    world->playthroughId = PlaythroughStatistics::newPlaythroughId();
    world->playthroughTimeline.clear();
    world->playthroughPlayedSeconds = 0.0;
    world->saveName = name;
    world->previewBmp.clear();

    if (!saveGameDataToPath(path, *world, error))
    {
        m_lastNotice = error;
        m_session.gameplayScreenRuntime().setStatusBarEvent(
            Engine::tr("The copy of this world could not be saved"), 6.0f);
        return;
    }

    m_lastNotice =
        Engine::tr("A copy of the host's world was saved as {name}", {{"name", path.filename().string()}});
    m_session.gameplayScreenRuntime().setStatusBarEvent(
        Engine::tr("A copy of this world was saved as {name}", {{"name", name}}), 6.0f);
}

namespace
{
// The guest's own game with its party as the host has it now. That game's own quests and journal stay, and its inn
// roster, which did not travel. A solo host took the party's first character alone: the others waited at home and are
// back in their places behind it.
void putCharacterIntoOwnGame(GameSaveData &game, const Party &party)
{
    Party::Snapshot character = party.snapshot();
    character.campaign = std::move(game.party.campaign);
    character.adventurersInnMembers = std::move(game.party.adventurersInnMembers);

    for (size_t index = character.members.size(); index < game.party.members.size(); ++index)
    {
        character.members.push_back(game.party.members[index]);
    }

    game.party = std::move(character);
}
}

bool CoopSession::writeGuestOwnGame(std::string &error)
{
    const Party *pParty = m_guestMapLoaded ? m_session.partyOfPlayer(LocalPlayer) : nullptr;

    // A game without a playthrough has no Autosave of its own: the one file such games share is not this game's
    // to take.
    if (!m_guestOwnGame || m_guestCharacterFile || pParty == nullptr || m_guestOwnGame->playthroughId.empty())
    {
        error = "this game has no Autosave of its own to write";
        return false;
    }

    // The game as it was left, with the character as the host has it now and that game's own quests and journal.
    GameSaveData game = *m_guestOwnGame;
    putCharacterIntoOwnGame(game, *pParty);
    m_guestCharacterWriteSeconds = 0.0f;

    // Encoding a whole save and writing it would hold a frame every two minutes: it is done beside the game, one
    // write at a time (a round that finds the last one still going is left to the next), into a file of its own
    // that takes the save's place when it is whole, so that nothing ever reads half a save.
    if (m_guestOwnGameWrite.valid()
        && m_guestOwnGameWrite.wait_for(std::chrono::seconds(0)) != std::future_status::ready)
    {
        return true;
    }

    m_guestOwnGameWrite = std::async(std::launch::async,
        [path = autosavePath(game.playthroughId), game = std::move(game)]()
        {
            std::filesystem::path partPath = path;
            partPath += ".part";
            std::string writeError;
            std::error_code renameError;

            if (saveGameDataToPath(partPath, game, writeError))
            {
                std::filesystem::rename(partPath, path, renameError);
            }

            if (!writeError.empty() || renameError)
            {
                std::cerr << "CoopSession: this game's own save was not written: "
                          << (writeError.empty() ? renameError.message() : writeError) << '\n';
            }
        });
    return true;
}

void CoopSession::waitForOwnGameWrite()
{
    if (m_guestOwnGameWrite.valid())
    {
        m_guestOwnGameWrite.wait();
    }
}

void CoopSession::setJoinCharacter(CharacterFile file, std::filesystem::path path)
{
    m_guestCharacterFile = std::move(file);
    m_guestCharacterPath = std::move(path);
    m_guestCharacterWriteSeconds = 0.0f;
}

const std::filesystem::path *CoopSession::joinCharacterPath() const
{
    return m_guestCharacterFile ? &m_guestCharacterPath : nullptr;
}

bool CoopSession::writeJoinCharacter(std::string &error)
{
    if (!m_guestCharacterFile)
    {
        error = "this game did not join with a character file";
        return false;
    }

    // The character as the host has it: this game's party is its mirror once the host's map is loaded.
    if (const Party *pParty = m_guestMapLoaded ? m_session.partyOfPlayer(LocalPlayer) : nullptr)
    {
        m_guestCharacterFile->character = characterForWire(pParty->snapshot());
    }

    m_guestCharacterWriteSeconds = 0.0f;
    return writeCharacterFile(m_guestCharacterPath, *m_guestCharacterFile, error);
}

void CoopSession::leave()
{
    if (m_role == Role::Guest)
    {
        guestReturnToOwnGame(std::string());
        return;
    }

    // A host with guests ends its session in two steps: each guest is sent the world as it now is and is let go
    // once it has it (the transport closes a connection when what was sent is through); then the session closes.
    // A second leave, or guests that do not take it in time, close at once.
    const bool guests = std::any_of(m_hostPeers.begin(), m_hostPeers.end(),
        [](const HostPeer &peer) { return peer.player != LocalPlayer; });

    if (m_role == Role::Host && guests && m_hostStopSeconds <= 0.0f && m_pTransport != nullptr)
    {
        for (HostPeer &peer : m_hostPeers)
        {
            hostSendWorldCopy(peer, WorldCopyLast);
            m_pTransport->disconnect(peer.peer);
        }

        m_hostStopSeconds = HostStopSeconds;
        m_lastNotice = Engine::tr("Ending the game: the other players are sent this world to keep ...");
        m_session.gameplayScreenRuntime().setStatusBarEvent(m_lastNotice, HostStopSeconds);
        return;
    }

    close();
}

bool CoopSession::stepOut(std::optional<EventRuntimeState::PendingMapMove> move, std::string &error)
{
    if (m_role != Role::Guest || !m_guestMapLoaded)
    {
        error = "only a guest in a host's game can step out of it";
        return false;
    }

    if (m_guestCharacterFile)
    {
        error = "a character joined from a file cannot step out: leave and join again";
        return false;
    }

    if (m_guestSteppingOut)
    {
        return true;
    }

    std::random_device device;
    uint64_t key = (uint64_t(device()) << 32) | uint64_t(device());
    key = key != 0 ? key : 1;
    m_guestSteppingOut = PendingStepOut{key, std::move(move)};
    Engine::ByteWriter message = beginMessage(Coop::Message::StepOut);
    message.u64(key);
    send(m_guestHostPeer, Coop::ChannelControl, Engine::NetDelivery::Reliable, message);
    return true;
}

void CoopSession::stepOutToTravel(const EventRuntimeState::PendingMapMove &move)
{
    std::string error;

    if (!stepOut(move, error))
    {
        m_session.gameplayScreenRuntime().setStatusBarEvent(error, 4.0f);
    }
}

void CoopSession::stepOutOfSession()
{
    std::string error;

    if (!stepOut(std::nullopt, error))
    {
        m_session.gameplayScreenRuntime().setStatusBarEvent(error, 4.0f);
    }
}

void CoopSession::hostTravelDeparting()
{
    if (m_role != Role::Host || m_pTransport == nullptr || m_hostPeers.empty())
    {
        return;
    }

    sendToAll(Coop::ChannelControl, Engine::NetDelivery::Reliable, beginMessage(Coop::Message::TravelDeparting));
    // Out now: the map load that follows holds this game for seconds.
    m_pTransport->service(0);
}

bool CoopSession::guestDeparting() const
{
    return m_role == Role::Guest && m_guestMapLoaded && m_guestDepartingSeconds > 0.0f;
}

void CoopSession::guestFinishStepOut()
{
    if (!m_guestSteppingOut)
    {
        return;
    }

    PendingStepOut pending = std::move(*m_guestSteppingOut);
    m_guestSteppingOut.reset();
    AwayFrom away;
    // The host's character is player 0 in every game of the session but its own.
    away.hostName = playerName(LocalPlayer);
    away.seatKey = pending.key;
    away.route = m_guestJoinRoute;
    away.password = m_joinPassword;
    const std::string notice = away.hostName.empty()
        ? Engine::tr("You left the game for now. Return from the Multiplayer menu.")
        : Engine::tr("You left {name}'s game for now. Return from the Multiplayer menu.",
              {{"name", away.hostName}});
    guestReturnToOwnGame(notice);
    m_guestAwayFrom = std::move(away);

    // Where the player wanted to go: its own game travels there now, as after an exit taken alone.
    if (pending.move)
    {
        IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();

        if (EventRuntimeState *pEventRuntimeState =
                pWorldRuntime != nullptr ? pWorldRuntime->eventRuntimeState() : nullptr)
        {
            pEventRuntimeState->pendingMapMove = std::move(*pending.move);
        }
    }
}

const std::optional<CoopSession::AwayFrom> &CoopSession::awayFrom() const
{
    return m_guestAwayFrom;
}

void CoopSession::forgetAwaySession()
{
    m_guestAwayFrom.reset();
}

bool CoopSession::stepBack(std::string &error)
{
    if (!m_guestAwayFrom)
    {
        error = "this game has stepped out of no session";
        return false;
    }

    const AwayFrom away = *m_guestAwayFrom;
    m_joinPassword = away.password;

    switch (away.route.kind)
    {
        case JoinRoute::Kind::Address:
            return join(away.route.address, error);

        case JoinRoute::Kind::Code:
            return joinByCode(away.route.lobbyAddress, away.route.code, error, away.route.relayOnly);

        case JoinRoute::Kind::Other:
            break;
    }

    error = "join that game again the way you joined it";
    return false;
}

void CoopSession::askTestSync()
{
    if (m_role == Role::Guest && m_guestMapLoaded)
    {
        send(m_guestHostPeer, Coop::ChannelControl, Engine::NetDelivery::Reliable,
            beginMessage(Coop::Message::TestSync));
    }
}

size_t CoopSession::awaySeatCount() const
{
    return m_hostAwaySeats.size();
}

bool CoopSession::hosting() const
{
    return m_role == Role::Host;
}

bool CoopSession::joined() const
{
    return m_role == Role::Guest && m_guestMapLoaded;
}

bool CoopSession::joining() const
{
    return m_role == Role::Guest && !m_guestMapLoaded;
}

PlayerId CoopSession::ownPlayer() const
{
    return m_role == Role::Guest ? m_guestOwnPlayer : LocalPlayer;
}

const std::string &CoopSession::lastNotice() const
{
    return m_lastNotice;
}

const std::vector<CoopSession::OtherPlayer> &CoopSession::otherPlayers() const
{
    return m_otherPlayers;
}

const CoopSession::Traffic &CoopSession::traffic() const
{
    return m_traffic;
}

std::string CoopSession::describe() const
{
    std::ostringstream out;

    switch (m_role)
    {
        case Role::None:
            out << "no network session";
            break;

        case Role::Host:
            out << "hosting, map revision " << m_mapRevision << ", " << m_hostPeers.size() << " connection(s)";

            if (m_pLobby != nullptr)
            {
                out << (m_pLobby->registered() ? ", lobby code " + m_pLobby->sessionCode()
                                               : std::string(", the lobby has not answered"));
            }

            break;

        case Role::Guest:
            out << (m_guestMapLoaded ? "joined" : m_guestWelcomed ? "joining: loading the map" : "joining: connecting")
                << " as player " << int(m_guestOwnPlayer) << ", map revision " << m_mapRevision;
            break;
    }

    for (const OtherPlayer &player : m_otherPlayers)
    {
        out << "\nplayer " << int(player.id) << " " << player.name << " (" << player.className << " "
            << player.level << ") hp " << player.health << "/" << player.maxHealth
            << (player.down ? " down" : "") << (player.away ? " away" : player.loadingMap ? " loading" : "")
            << " at " << std::lround(player.body.x) << " " << std::lround(player.body.y) << " "
            << std::lround(player.body.footZ)
            // Which member of its party stands for it, and how good what the party wears is.
            << " member " << int(player.avatarMember) + 1 << " gear " << int(player.gearTier);

        // What its body last showed doing, and how many actions that makes.
        if (player.action.serial != 0)
        {
            out << " action " << int(player.action.serial) << " "
                << (player.action.kind == PlayerAction::Kind::Cast ? "cast"
                    : player.action.kind == PlayerAction::Kind::Shot ? "shot" : "melee");
        }
    }

    // The line as the transport measures it, to each guest or to the host.
    const auto describeLine = [this, &out](const std::string &toWhom, Engine::NetPeerId peer)
    {
        const Engine::NetPeerStats stats = m_pTransport->peerStats(peer);
        out << "\nline to " << toWhom << ": " << stats.roundTripMs << " ms there and back, "
            << stats.lossPermille / 10 << "." << stats.lossPermille % 10 << " % lost, send window "
            << stats.sendWindowPercent << " %";
    };

    if (m_pTransport != nullptr && m_role == Role::Host)
    {
        for (const HostPeer &peer : m_hostPeers)
        {
            describeLine("player " + std::to_string(int(peer.player)), peer.peer);
        }
    }
    else if (m_pTransport != nullptr && m_role == Role::Guest && m_guestHostPeer != Engine::InvalidNetPeer)
    {
        describeLine("the host", m_guestHostPeer);
    }

    out << "\nsent " << m_traffic.messagesSent << " messages, " << m_traffic.bytesSent << " bytes; received "
        << m_traffic.messagesReceived << " messages, " << m_traffic.bytesReceived << " bytes";
    out << "\n  sent before packing: " << m_traffic.bytesSentUnpacked << " bytes";

    if (m_role == Role::Host)
    {
        out << "\n  map sections sent: event state " << m_traffic.sectionsSent[size_t(Coop::MapSection::EventState)]
            << ", mechanisms " << m_traffic.sectionsSent[size_t(Coop::MapSection::Mechanisms)]
            << ", ground items " << m_traffic.sectionsSent[size_t(Coop::MapSection::WorldItems)];
    }

    for (size_t kind = 0; kind < m_traffic.bytesSentByKind.size(); ++kind)
    {
        if (m_traffic.messagesSentByKind[kind] != 0)
        {
            out << "\n  sent kind " << kind << ": " << m_traffic.messagesSentByKind[kind] << " messages, "
                << m_traffic.bytesSentByKind[kind] << " bytes";
        }
    }

    if (!m_lastNotice.empty())
    {
        out << "\n" << m_lastNotice;
    }

    return out.str();
}

void CoopSession::send(
    Engine::NetPeerId peer,
    uint8_t channel,
    Engine::NetDelivery delivery,
    const Engine::ByteWriter &message)
{
    sendBytes(peer, channel, delivery, message.bytes());
}

bool CoopSession::sendBytes(
    Engine::NetPeerId peer,
    uint8_t channel,
    Engine::NetDelivery delivery,
    const std::vector<uint8_t> &bytes)
{
    if (m_pTransport == nullptr || bytes.empty())
    {
        return false;
    }

    const uint8_t kind = bytes[0];
    const bool admission = kind == uint8_t(Coop::Message::Hello) || kind == uint8_t(Coop::Message::Welcome)
        || kind == uint8_t(Coop::Message::Refused);
    std::vector<uint8_t> packed;

    if (bytes.size() >= Coop::PackFromBytes && !admission)
    {
        packed = Engine::packBytes(std::span<const uint8_t>(bytes).subspan(1));
        packed.insert(packed.begin(), uint8_t(kind | Coop::PackedFlag));
    }

    // A packed message that came out no smaller goes as it is.
    const std::vector<uint8_t> &wire = packed.size() > 1 && packed.size() < bytes.size() ? packed : bytes;

    if (!m_pTransport->send(peer, channel, delivery, wire))
    {
        return false;
    }

    ++m_traffic.messagesSent;
    m_traffic.bytesSent += wire.size();
    m_traffic.bytesSentUnpacked += bytes.size();

    if (kind < m_traffic.bytesSentByKind.size())
    {
        ++m_traffic.messagesSentByKind[kind];
        m_traffic.bytesSentByKind[kind] += wire.size();
    }

    return true;
}

std::optional<std::vector<uint8_t>> CoopSession::unpackedMessage(const std::vector<uint8_t> &payload, size_t maxBytes)
{
    if (payload.empty() || (payload[0] & Coop::PackedFlag) == 0)
    {
        return payload;
    }

    std::optional<std::vector<uint8_t>> message =
        Engine::unpackBytes(std::span<const uint8_t>(payload).subspan(1), maxBytes);

    if (message)
    {
        message->insert(message->begin(), uint8_t(payload[0] & ~Coop::PackedFlag));
    }

    return message;
}

void CoopSession::sendToAll(uint8_t channel, Engine::NetDelivery delivery, const Engine::ByteWriter &message)
{
    for (const HostPeer &peer : m_hostPeers)
    {
        if (peer.player != LocalPlayer)
        {
            send(peer.peer, channel, delivery, message);
        }
    }
}

const std::deque<CoopSession::ChatLine> &CoopSession::chatLines() const
{
    return m_chatLines;
}

uint32_t CoopSession::chatSerial() const
{
    return m_chatSerial;
}

const std::vector<CoopSession::Ping> &CoopSession::pings() const
{
    return m_pings;
}

std::string CoopSession::playerName(PlayerId player) const
{
    if (player == ownPlayer())
    {
        // As the others name this player: after the member that stands for its party.
        const Party *pParty = m_session.partyOfPlayer(LocalPlayer);
        const size_t avatar =
            pParty != nullptr && ownAvatarMember() < pParty->members().size() ? ownAvatarMember() : 0;
        const Character *pMember = pParty != nullptr ? pParty->member(avatar) : nullptr;
        return pMember != nullptr ? pMember->name : std::string();
    }

    for (const OtherPlayer &other : m_otherPlayers)
    {
        if (other.id == player)
        {
            return other.name;
        }
    }

    return {};
}

void CoopSession::addChatLine(PlayerId player, const std::string &text)
{
    m_chatLines.push_back(ChatLine{player, playerName(player), text});
    ++m_chatSerial;

    while (m_chatLines.size() > ChatHistory)
    {
        m_chatLines.pop_front();
    }
}

void CoopSession::addPing(PlayerId player, float x, float y, float z)
{
    // One place a player: a new one takes the old one's.
    std::erase_if(m_pings, [player](const Ping &ping) { return ping.player == player; });
    m_pings.push_back(Ping{player, playerName(player), x, y, z, 0.0f});
}

bool CoopSession::sayChat(const std::string &text)
{
    // What a player types, without what is no text.
    std::string line;

    for (const char character : text)
    {
        if (static_cast<unsigned char>(character) >= 0x20 && line.size() < Coop::MaxChatLength)
        {
            line.push_back(character);
        }
    }

    if (m_role == Role::None || m_pTransport == nullptr || line.find_first_not_of(' ') == std::string::npos)
    {
        return false;
    }

    addChatLine(ownPlayer(), line);

    if (m_role == Role::Host)
    {
        Engine::ByteWriter message = beginMessage(Coop::Message::Chat);
        message.u8(LocalPlayer);
        message.text(line, Coop::MaxChatLength);
        sendToAll(Coop::ChannelControl, Engine::NetDelivery::Reliable, message);
    }
    else
    {
        Engine::ByteWriter message = beginMessage(Coop::Message::Say);
        message.text(line, Coop::MaxChatLength);
        send(m_guestHostPeer, Coop::ChannelControl, Engine::NetDelivery::Reliable, message);
    }

    return true;
}

bool CoopSession::sendPing(float x, float y, float z)
{
    if (m_role == Role::None || m_pTransport == nullptr || !std::isfinite(x) || !std::isfinite(y) || !std::isfinite(z))
    {
        return false;
    }

    addPing(ownPlayer(), x, y, z);
    Engine::ByteWriter message = beginMessage(m_role == Role::Host ? Coop::Message::Ping : Coop::Message::Point);

    if (m_role == Role::Host)
    {
        message.u8(LocalPlayer);
    }

    message.u16(m_mapRevision);
    message.f32(x);
    message.f32(y);
    message.f32(z);

    if (m_role == Role::Host)
    {
        sendToAll(Coop::ChannelControl, Engine::NetDelivery::Reliable, message);
    }
    else
    {
        send(m_guestHostPeer, Coop::ChannelControl, Engine::NetDelivery::Reliable, message);
    }

    return true;
}

void CoopSession::updateOwnAction()
{
    // The first-person arms count what the character begins: a swing or a waited cast, an action that showed no
    // swing, a talent. The other games' bodies of this character show the same.
    GameplayScreenRuntime::ViewModelLink &link = m_session.gameplayScreenRuntime().viewModelLink();
    const bool swing = link.swingSerial != m_ownActionSeenSwings;
    const bool action = link.actionSerial != m_ownActionSeenActions;
    const bool talent = link.talentSerial != m_ownActionSeenTalents;
    // A spell cast with nothing else to show for it: a party's member casting (no arms, so no swing or action
    // was counted), from the spellbook, a quick key, an Attack order or the Upkeep key (seen missing by the user on
    // 2026-11-21: a lich's Fire Bolt left its body standing still). Not a cast the arms just showed, which counts
    // as a swing at the press and leaves the hand a moment later.
    constexpr uint32_t ShownCastMs = 1500;
    const uint32_t nowMs = Engine::netNowMilliseconds();
    const bool cast = link.castSerial != m_ownActionSeenCasts && !swing && !action && !talent
        && (m_ownAction.kind != PlayerAction::Kind::Cast || nowMs - m_ownActionAtMs > ShownCastMs);
    m_ownActionSeenSwings = link.swingSerial;
    m_ownActionSeenActions = link.actionSerial;
    m_ownActionSeenTalents = link.talentSerial;
    m_ownActionSeenCasts = link.castSerial;

    if (!swing && !action && !talent && !cast)
    {
        return;
    }

    m_ownActionAtMs = nowMs;

    const Party *pParty = m_session.partyOfPlayer(LocalPlayer);
    const Character *pMember = pParty != nullptr ? pParty->member(pParty->activeMemberIndex()) : nullptr;
    ++m_ownAction.serial;
    m_ownAction.kind = (cast || (swing && link.waitIsCast)) ? PlayerAction::Kind::Cast
        : swing ? (link.bowSelected ? PlayerAction::Kind::Shot : PlayerAction::Kind::Melee)
        : action ? (link.action == GameplayScreenRuntime::ViewModelAction::Cast ? PlayerAction::Kind::Cast
                : link.action == GameplayScreenRuntime::ViewModelAction::Shot ? PlayerAction::Kind::Shot
                : PlayerAction::Kind::Melee)
        : PlayerAction::Kind::Melee;
    // The recovery it began with: the swing's own when it is a swing, else what the character now waits.
    m_ownAction.seconds = swing && link.swingRecoverySeconds > 0.0f ? link.swingRecoverySeconds
        : pMember != nullptr ? pMember->recoverySecondsRemaining : 0.0f;
}

void CoopSession::update(float deltaSeconds)
{
    if (m_role != Role::None)
    {
        updateOwnAction();
    }

    for (Ping &ping : m_pings)
    {
        ping.ageSeconds += deltaSeconds;
    }

    std::erase_if(m_pings, [](const Ping &ping) { return ping.ageSeconds >= PingSeconds; });

    switch (m_role)
    {
        case Role::None:
            break;

        case Role::Host:
            updateHost(deltaSeconds);
            break;

        case Role::Guest:
            updateGuest(deltaSeconds);
            break;
    }
}

// ---------------------------------------------------------------------------------------------------------------
// The host's side.

CoopSession::HostPeer *CoopSession::hostPeerOf(Engine::NetPeerId peer)
{
    for (HostPeer &hostPeer : m_hostPeers)
    {
        if (hostPeer.peer == peer)
        {
            return &hostPeer;
        }
    }

    return nullptr;
}

CoopSession::HostPeer *CoopSession::hostPeerOfPlayer(PlayerId player)
{
    for (HostPeer &hostPeer : m_hostPeers)
    {
        if (hostPeer.player == player && player != LocalPlayer)
        {
            return &hostPeer;
        }
    }

    return nullptr;
}

void CoopSession::updateHost(float deltaSeconds)
{
    // Ending the session: closed once every guest has gone with the world it was sent, or when the wait is over.
    if (m_hostStopSeconds > 0.0f)
    {
        m_hostStopSeconds -= deltaSeconds;
        const bool guestsLeft = std::any_of(m_hostPeers.begin(), m_hostPeers.end(),
            [](const HostPeer &peer) { return peer.player != LocalPlayer; });

        if (!guestsLeft || m_hostStopSeconds <= 0.0f)
        {
            close();
            m_lastNotice = Engine::tr("The game is no longer hosted");
            m_session.gameplayScreenRuntime().setStatusBarEvent(m_lastNotice, 4.0f);
            return;
        }
    }

    // A guest that sends nothing for some seconds is told to the host's player: its line stands, or its game does.
    // A guest loading the map is silent by rights.
    for (HostPeer &peer : m_hostPeers)
    {
        const GameSession::GuestPlayer *pSilent = m_session.guestPlayer(peer.player);
        peer.sinceAskedSaveSeconds += deltaSeconds;
        peer.sinceAskedWorldCopySeconds += deltaSeconds;

        // A connection that does not say Hello holds one of the few places for nothing: it is ended.
        if (peer.player == LocalPlayer)
        {
            peer.unadmittedSeconds += deltaSeconds;

            if (peer.unadmittedSeconds >= UnadmittedSeconds)
            {
                peer.unadmittedSeconds = -1000.0f;
                m_pTransport->disconnect(peer.peer);
            }
        }

        if (peer.player == LocalPlayer || pSilent == nullptr || pSilent->loadingMap)
        {
            peer.silentSeconds = 0.0f;
            continue;
        }

        peer.silentSeconds += deltaSeconds;
        peer.silenceToldSeconds += deltaSeconds;

        if (peer.silentSeconds >= SilenceToldAfterSeconds && peer.silenceToldSeconds >= SilenceToldEverySeconds)
        {
            peer.silenceToldSeconds = 0.0f;
            m_session.gameplayScreenRuntime().setStatusBarEvent(
                Engine::tr("No word from {name} for {seconds} seconds",
                    {{"name", playerName(peer.player)}, {"seconds", int64_t(peer.silentSeconds)}}),
                SilenceToldEverySeconds);
        }
    }

    m_pTransport->service(0);
    Engine::NetEvent event;

    while (m_pTransport != nullptr && m_pTransport->pollEvent(event))
    {
        hostHandleEvent(event);
    }

    if (m_pTransport == nullptr)
    {
        return;
    }

    // Another map (travel, a defeat's respawn, a load): every guest gets its state and loads it.
    if (m_hostMapLoadSerial != m_application.m_mapLoadSerial
        || m_pHostSentWorldRuntime != m_session.activeWorldRuntime())
    {
        m_hostMapLoadSerial = m_application.m_mapLoadSerial;
        m_pHostSentWorldRuntime = m_session.activeWorldRuntime();
        ++m_mapRevision;

        for (HostPeer &peer : m_hostPeers)
        {
            if (peer.player != LocalPlayer)
            {
                hostSendWorldState(peer);
            }
        }

        hostPrimeMapBaselines();
    }

    for (HostPeer &peer : m_hostPeers)
    {
        const GameSession::GuestPlayer *pGuest =
            peer.player != LocalPlayer ? m_session.guestPlayer(peer.player) : nullptr;

        if (pGuest == nullptr)
        {
            continue;
        }

        peer.secondsSincePosition += deltaSeconds;
        peer.loadingSeconds = pGuest->loadingMap ? peer.loadingSeconds + deltaSeconds : 0.0f;

        // A game that does not get the map loaded is let go; its player may join again.
        if (peer.loadingSeconds > MapLoadTimeoutSeconds)
        {
            peer.loadingSeconds = 0.0f;
            hostRefuse(peer, Engine::tr("the map took too long to load"));
        }
    }

    m_hostStreamSeconds += deltaSeconds;
    m_hostStateSeconds += deltaSeconds;
    const bool stateTick = m_hostStateSeconds >= StateIntervalSeconds;

    // The lobby's address was found, or not: the game goes on for the local network either way.
    if (m_hostLobbyAsked && !m_hostLobbyLookup.pending())
    {
        m_hostLobbyAsked = false;

        if (const std::optional<Engine::NetAddress> lobby = m_hostLobbyLookup.address(); lobby && m_pEnet != nullptr)
        {
            hostRegisterWithLobby(*lobby);
        }
        else
        {
            m_lastNotice = Engine::tr("The lobby server {address} was not found: this game is open to your network "
                                      "only.", {{"address", m_hostLobbyLookup.text()}});
            m_session.gameplayScreenRuntime().setStatusBarEvent(m_lastNotice, 6.0f);
        }
    }

    // The lobby is told how many play, and kept hearing of the session.
    if (m_pLobby != nullptr)
    {
        if (stateTick)
        {
            m_pLobby->updateSessionInfo(sessionInfoForLobby());
        }

        m_pLobby->update(Engine::netNowMilliseconds());
    }

    hostRefreshOtherPlayers(stateTick);

    const bool hasGuests = !m_session.guestPlayers().empty();

    if (stateTick)
    {
        m_hostStateSeconds = std::fmod(m_hostStateSeconds, StateIntervalSeconds);
        ++m_hostStateTick;
        hostSendPlayers();

        if (hasGuests)
        {
            // Before the poses: a monster's pose means nothing to a game that has not its record.
            hostSendActorRecords();
            hostSendMapSections();

            // The campaign (quest bits, notes, every shop's stock) is large to compare and changes seldom: twice a
            // second, and at once after a guest's command (hostSendOutcome).
            if (m_hostCampaignDue || m_hostStateTick % CampaignEveryStateTicks == 0)
            {
                m_hostCampaignDue = false;
                hostSendCampaign();
            }

            hostSendPartyStates();
            hostSendTravelProposal();
            hostSendRulesState();
            hostSendLentAuras();
        }
    }

    if (m_hostStreamSeconds >= StreamIntervalSeconds)
    {
        m_hostStreamSeconds = std::fmod(m_hostStreamSeconds, StreamIntervalSeconds);

        if (hasGuests)
        {
            hostSendMoveOrders();
            hostSendBodies();
            hostSendActorPoses();
            hostSendProjectiles();
            hostSendSounds();

            for (HostPeer &peer : m_hostPeers)
            {
                hostSendOutcome(peer);
                hostSendLootViews(peer);
                hostSendHouseScreens(peer);
            }
        }
    }

    if (m_pTransport != nullptr)
    {
        m_pTransport->service(0);
    }
}

void CoopSession::hostHandleEvent(const Engine::NetEvent &event)
{
    switch (event.type)
    {
        case Engine::NetEvent::Type::Connected:
            m_hostPeers.push_back(HostPeer{.peer = event.peer});
            break;

        case Engine::NetEvent::Type::Disconnected:
            hostDropPeer(event.peer);
            break;

        case Engine::NetEvent::Type::Message:
            ++m_traffic.messagesReceived;
            m_traffic.bytesReceived += event.payload.size();

            if (HostPeer *pPeer = hostPeerOf(event.peer))
            {
                pPeer->silentSeconds = 0.0f;
                pPeer->silenceToldSeconds = 0.0f;

                // A game that was not admitted yet may send its Hello and no more than that is worth unpacking.
                const size_t maxBytes = pPeer->player == LocalPlayer ? MaxUnadmittedBytes : Coop::MaxBlockBytes;

                if (const std::optional<std::vector<uint8_t>> message = unpackedMessage(event.payload, maxBytes))
                {
                    hostHandleMessage(*pPeer, event.channel, *message);
                }
            }

            break;
    }
}

void CoopSession::hostDropPeer(Engine::NetPeerId peer)
{
    const HostPeer *pPeer = hostPeerOf(peer);

    if (pPeer == nullptr)
    {
        return;
    }

    if (pPeer->player != LocalPlayer)
    {
        const GameSession::GuestPlayer *pGuest = m_session.guestPlayer(pPeer->player);

        // A player who asked to step out keeps its seat: the others see it greyed until it is back.
        if (pPeer->stepOutKey != 0 && pGuest != nullptr)
        {
            AwaySeat seat;
            seat.key = pPeer->stepOutKey;
            seat.shown.id = pPeer->player;
            fillOtherPlayer(seat.shown, pGuest->party, pPeer->avatarMember);

            if (seat.shown.name.empty())
            {
                seat.shown.name = pPeer->name;
            }

            seat.shown.away = true;
            seat.shown.loadingMap = true;
            m_hostAwaySeats.push_back(std::move(seat));
        }

        m_lastNotice = pPeer->stepOutKey != 0 ? Engine::tr("{name} stepped out for now", {{"name", pPeer->name}})
            : Engine::tr("{name} left the game", {{"name", pPeer->name}});
        m_session.gameplayScreenRuntime().setStatusBarEvent(m_lastNotice, 4.0f);
        // What it had asked of the others is over with its leaving.
        m_session.dropProposalsOf(pPeer->player);
        m_session.removeGuestPlayer(pPeer->player);
    }

    std::erase_if(m_hostPeers, [peer](const HostPeer &hostPeer) { return hostPeer.peer == peer; });
}

void CoopSession::hostRefuse(HostPeer &peer, const std::string &reason)
{
    Engine::ByteWriter message = beginMessage(Coop::Message::Refused);
    message.text(reason);
    send(peer.peer, Coop::ChannelControl, Engine::NetDelivery::Reliable, message);
    m_pTransport->disconnect(peer.peer);
}

void CoopSession::hostHandleMessage(HostPeer &peer, uint8_t, const std::vector<uint8_t> &payload)
{
    Engine::ByteReader reader(payload);
    const Coop::Message message = Coop::Message(reader.u8());

    if (!reader.ok())
    {
        return;
    }

    if (message == Coop::Message::Hello)
    {
        hostHandleHello(peer, reader);
        return;
    }

    // Everything else is a player's: a game that was not admitted has no say.
    if (peer.player == LocalPlayer)
    {
        return;
    }

    switch (message)
    {
        case Coop::Message::Position:
            hostHandlePosition(peer, reader);
            break;

        case Coop::Message::TestSync:
        {
            std::string message;

            if (peer.player != LocalPlayer && m_application.coopTestCommandsAllowed())
            {
                m_application.coopSyncPlayers(LocalPlayer, peer.player, message);
            }

            break;
        }

        case Coop::Message::StepOut:
        {
            const uint64_t key = reader.u64();

            // The seat is kept from the moment the peer's game goes (hostDropPeer); it goes when it has this answer.
            if (reader.ok() && key != 0 && peer.player != LocalPlayer)
            {
                peer.stepOutKey = key;
                m_session.dropProposalsOf(peer.player);
                send(peer.peer, Coop::ChannelControl, Engine::NetDelivery::Reliable,
                    beginMessage(Coop::Message::SteppedOut));
            }

            break;
        }

        case Coop::Message::AskSave:
        {
            // Told to the host's player, who saves or does not; not oftener than a guest's game may ask.
            if (peer.player != LocalPlayer && peer.sinceAskedSaveSeconds >= AskSaveEverySeconds)
            {
                peer.sinceAskedSaveSeconds = 0.0f;
                const std::string asking =
                    Engine::tr("{name} asks you to save the game", {{"name", playerName(peer.player)}});
                m_lastNotice = asking;
                m_session.gameplayScreenRuntime().setStatusBarEvent(asking, 6.0f);
            }

            break;
        }

        case Coop::Message::Avatar:
        {
            const uint8_t member = reader.u8();

            // The players list is made again every update: the others are told with the next one.
            if (reader.ok() && peer.player != LocalPlayer)
            {
                peer.avatarMember = member;
            }

            break;
        }

        case Coop::Message::Say:
        {
            const std::string text = reader.text(Coop::MaxChatLength);

            // A player of the game says it: here, and to everyone else.
            if (reader.ok() && peer.player != LocalPlayer && !text.empty())
            {
                addChatLine(peer.player, text);
                Engine::ByteWriter relayed = beginMessage(Coop::Message::Chat);
                relayed.u8(peer.player);
                relayed.text(text, Coop::MaxChatLength);

                for (const HostPeer &other : m_hostPeers)
                {
                    if (other.player != LocalPlayer && other.peer != peer.peer)
                    {
                        send(other.peer, Coop::ChannelControl, Engine::NetDelivery::Reliable, relayed);
                    }
                }
            }

            break;
        }

        case Coop::Message::Point:
        {
            const uint16_t mapRevision = reader.u16();
            const float x = reader.f32();
            const float y = reader.f32();
            const float z = reader.f32();

            if (reader.ok() && peer.player != LocalPlayer && mapRevision == m_mapRevision && std::isfinite(x)
                && std::isfinite(y) && std::isfinite(z))
            {
                addPing(peer.player, x, y, z);
                Engine::ByteWriter relayed = beginMessage(Coop::Message::Ping);
                relayed.u8(peer.player);
                relayed.u16(m_mapRevision);
                relayed.f32(x);
                relayed.f32(y);
                relayed.f32(z);

                for (const HostPeer &other : m_hostPeers)
                {
                    if (other.player != LocalPlayer && other.peer != peer.peer)
                    {
                        send(other.peer, Coop::ChannelControl, Engine::NetDelivery::Reliable, relayed);
                    }
                }
            }

            break;
        }

        case Coop::Message::WorldCopyRequest:
        {
            // The whole save, packed: not as often as a game cares to ask.
            if (peer.sinceAskedWorldCopySeconds >= WorldCopyEverySeconds)
            {
                peer.sinceAskedWorldCopySeconds = 0.0f;
                hostSendWorldCopy(peer, WorldCopyAsked);
            }

            break;
        }

        case Coop::Message::CharacterPut:
            hostHandleCharacterPut(peer, reader);
            break;

        case Coop::Message::Command:
            hostHandleCommand(peer, reader);
            break;

        case Coop::Message::MapReady:
        {
            const uint16_t mapRevision = reader.u16();

            if (reader.ok() && mapRevision == m_mapRevision)
            {
                peer.readyMapRevision = mapRevision;

                if (GameSession::GuestPlayer *pGuest = m_session.guestPlayer(peer.player))
                {
                    pGuest->loadingMap = false;
                }

                // What changed while its game loaded, then every monster's pose anew.
                for (const std::vector<uint8_t> &waiting : peer.waitingMapMessages)
                {
                    sendBytes(peer.peer, Coop::ChannelControl, Engine::NetDelivery::Reliable, waiting);
                }

                peer.waitingMapMessages.clear();
                peer.waitingMapBytes = 0;
                // Its party is in the map from this moment, for a command of its that came with this message too
                // (without its body the world would act for the host's party).
                m_session.publishGuestBodies();

                for (HostActorStream &stream : m_hostActorStreams)
                {
                    stream.resend = PoseResendCount;
                }
            }

            break;
        }

        default:
            break;
    }
}

void CoopSession::hostHandleHello(HostPeer &peer, Engine::ByteReader &reader)
{
    if (peer.player != LocalPlayer)
    {
        return;
    }

    const uint32_t protocolVersion = reader.u32();
    const uint32_t saveVersion = reader.u32();

    // A game of another version says so before anything it may lay out differently.
    if (!reader.ok() || protocolVersion != Coop::ProtocolVersion || saveVersion != SaveSections::saveVersion())
    {
        hostRefuse(peer, Engine::tr("the two games are different versions of OpenYAMM"));
        return;
    }

    const std::string name = reader.text(Coop::MaxNameLength);
    const std::vector<uint8_t> characterBytes = reader.block(Coop::MaxBlockBytes);
    const size_t identityLineCount = reader.u16();
    std::vector<std::string> identity;

    for (size_t line = 0; line < identityLineCount && line < Coop::MaxIdentityLines && reader.ok(); ++line)
    {
        identity.push_back(reader.text(Coop::MaxIdentityLineLength));
    }

    const std::string password = reader.text(Coop::MaxPasswordLength);
    // The key of the seat this game stepped out of, when it did (of this host's or of another's; 0 for none).
    const uint64_t seatKey = reader.u64();

    if (!reader.ok() || identityLineCount > Coop::MaxIdentityLines)
    {
        hostRefuse(peer, Engine::tr("the join request could not be read"));
        return;
    }

    if (m_hostStopSeconds > 0.0f)
    {
        hostRefuse(peer, Engine::tr("the host is ending the game"));
        return;
    }

    // The same content on both sides: packages, mods and their order, the ruleset the character is of.
    if (const std::optional<std::string> difference =
            coopContentDifference(m_application.coopContentIdentity(), identity))
    {
        hostRefuse(peer, *difference);
        return;
    }

    IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();

    if (pWorldRuntime == nullptr)
    {
        hostRefuse(peer, Engine::tr("the host is not in a game"));
        return;
    }

    if (!m_hostPassword.empty() && password != m_hostPassword)
    {
        hostRefuse(peer, password.empty() ? Engine::tr("this game asks for a password")
                                          : Engine::tr("the password is wrong"));
        return;
    }

    if (m_session.guestPlayers().size() >= Coop::MaxGuests)
    {
        hostRefuse(peer, Engine::tr("the session is full"));
        return;
    }

    Party::Snapshot character;

    if (!SaveSections::decodeCharacters(characterBytes, character) || character.members.empty()
        || character.members.size() > Party::MaxMembers)
    {
        hostRefuse(peer, Engine::tr("the character could not be read"));
        return;
    }

    // A player brings its party (since 2026-11-21). A solo run is one character's: there the first of a party that
    // came with more. The roster of its own world's inn stays at home.
    if (m_session.ruleset().options.soloRun)
    {
        character.members.resize(1);
    }

    character.adventurersInnMembers.clear();
    character.activeMemberIndex =
        character.activeMemberIndex < character.members.size() ? character.activeMemberIndex : 0;

    // A player who stepped out is back in its seat, as the player it was. Anyone else takes a free place: a seat
    // kept for someone away never keeps a present player out, the longest away gives its seat up.
    PlayerId wantedId = LocalPlayer;
    const auto ownSeat = std::find_if(m_hostAwaySeats.begin(), m_hostAwaySeats.end(),
        [seatKey](const AwaySeat &seat) { return seatKey != 0 && seat.key == seatKey; });
    const bool returning = ownSeat != m_hostAwaySeats.end();

    if (returning)
    {
        wantedId = ownSeat->shown.id;
        m_hostAwaySeats.erase(ownSeat);
    }
    else if (m_session.guestPlayers().size() + m_hostAwaySeats.size() >= Coop::MaxGuests
        && !m_hostAwaySeats.empty())
    {
        m_hostAwaySeats.erase(m_hostAwaySeats.begin());
    }

    std::vector<PlayerId> keptIds;

    for (const AwaySeat &seat : m_hostAwaySeats)
    {
        keptIds.push_back(seat.shown.id);
    }

    // Beside the host, each guest a step further.
    GameplayPlayerBody body = {pWorldRuntime->partyX(), pWorldRuntime->partyY(), pWorldRuntime->partyFootZ(), 0.0f};
    body.x += GuestArrivalSpacing * float(m_session.guestPlayers().size() + 1);
    peer.player = m_session.addGuestPlayer(character, body, wantedId, keptIds);
    peer.name = name;

    Engine::ByteWriter welcome = beginMessage(Coop::Message::Welcome);
    welcome.u8(peer.player);
    send(peer.peer, Coop::ChannelControl, Engine::NetDelivery::Reliable, welcome);

    // An open vote goes out again: a game admitted during one would otherwise never be asked, and the vote waits
    // for it. The campaign is looked at on the next state tick, not up to half a second later.
    m_hostSentTravelBytes.clear();
    m_hostCampaignDue = true;

    if (!hostSendWorldState(peer))
    {
        m_session.removeGuestPlayer(peer.player);
        peer.player = LocalPlayer;
        hostRefuse(peer, Engine::tr("the host could not gather the map's state"));
        return;
    }

    m_lastNotice = returning ? Engine::tr("{name} is back", {{"name", name}})
        : Engine::tr("{name} joined the game", {{"name", name}});
    m_session.gameplayScreenRuntime().setStatusBarEvent(m_lastNotice, 4.0f);
}

bool CoopSession::hostSendWorldState(HostPeer &peer)
{
    GameSession::GuestPlayer *pGuest = m_session.guestPlayer(peer.player);

    if (pGuest == nullptr)
    {
        return false;
    }

    std::optional<GameSaveData> worldState = m_application.buildCoopWorldState(peer.player);

    if (!worldState)
    {
        return false;
    }

    // Until its game says the map is loaded, the guest is not in the map for monsters and missiles.
    pGuest->loadingMap = true;
    peer.readyMapRevision = 0;
    peer.sentPartyBytes.clear();
    peer.waitingMapMessages.clear();
    peer.waitingMapBytes = 0;
    // What the player had open on the map it leaves is gone with that map, as in its own game: its conversation,
    // its chest and corpse, its shop and bank screens. What its cursor holds stays.
    pGuest->eventTransients = EventRuntimeState();
    pGuest->chestView.reset();
    pGuest->corpseView.reset();
    pGuest->ui.houseShopOverlay() = {};
    pGuest->ui.inventoryNestedOverlay() = {};
    pGuest->ui.houseBankState() = {};
    peer.sentLootViews.clear();
    peer.sentHouseScreens.clear();
    Engine::ByteWriter message = beginMessage(Coop::Message::WorldState);
    message.u16(m_mapRevision);
    writeBody(message, pGuest->body);
    message.u32(pGuest->bodyOrderSerial);
    message.block(SaveSections::encodeGame(*worldState));
    peer.sentBodyOrderSerial = pGuest->bodyOrderSerial;
    send(peer.peer, Coop::ChannelWorld, Engine::NetDelivery::Reliable, message);
    return true;
}

void CoopSession::hostHandlePosition(HostPeer &peer, Engine::ByteReader &reader)
{
    const uint16_t mapRevision = reader.u16();
    const uint32_t bodyOrderSerial = reader.u32();
    const GameplayPlayerBody body = readBody(reader);
    const PlayerAction action = readAction(reader);
    GameSession::GuestPlayer *pGuest = m_session.guestPlayer(peer.player);

    // What its character does shows wherever the host has it standing.
    if (reader.ok())
    {
        peer.action = action;
    }

    // A position from the map the players have left is dropped ("Old packets"), and so is one sent before the
    // guest's game knew where the host last put its party.
    if (!reader.ok() || mapRevision != m_mapRevision || pGuest == nullptr || pGuest->loadingMap || !finiteBody(body)
        || bodyOrderSerial != pGuest->bodyOrderSerial)
    {
        return;
    }

    // A place a character cannot have reached since the last one is not taken ("a position that jumps across the
    // map"): the host orders the guest's game back to where it has the character. Moves the world makes (an
    // event's teleport, an arrival) are the host's own orders and never come this way.
    const float allowed = MaxGuestUnitsPerSecond * std::max(peer.secondsSincePosition, PositionIntervalSeconds)
        + GuestPositionSlack;

    if (std::hypot(body.x - pGuest->body.x, body.y - pGuest->body.y) > allowed)
    {
        ++pGuest->bodyOrderSerial;
        peer.secondsSincePosition = 0.0f;
        return;
    }

    peer.secondsSincePosition = 0.0f;
    pGuest->body = body;
}

void CoopSession::fillOtherPlayer(OtherPlayer &player, const Party &party, size_t avatarMember)
{
    fillOtherPlayerFromParty(player, party, avatarMember);

    if (!m_pGearRules)
    {
        m_pGearRules = std::make_unique<HeldSkinRules>();
        std::string error;

        if (m_application.m_pAssetFileSystem == nullptr
            || !loadHeldSkinRules(*m_application.m_pAssetFileSystem, "engine/world_items/held_tiers.yml",
                *m_pGearRules, error))
        {
            std::cerr << "Co-op: the gear tiers were not read: " << error << '\n';
            *m_pGearRules = HeldSkinRules{};
            m_pGearRules->tierCount = 0;
        }
    }

    player.gearTier = coopPartyGearTier(party.members(), m_session.data().itemTable(), *m_pGearRules);
}

size_t CoopSession::ownAvatarMember() const
{
    return size_t(std::max(m_application.m_settings.coopAvatarMember, 0));
}

void CoopSession::tellOwnAvatar()
{
    if (m_role == Role::Guest && m_guestWelcomed && m_pTransport != nullptr)
    {
        Engine::ByteWriter message = beginMessage(Coop::Message::Avatar);
        message.u8(uint8_t(std::min<size_t>(ownAvatarMember(), 255)));
        send(m_guestHostPeer, Coop::ChannelControl, Engine::NetDelivery::Reliable, message);
    }
}

void CoopSession::hostRefreshOtherPlayers(bool whole)
{
    const std::vector<std::unique_ptr<GameSession::GuestPlayer>> &guests = m_session.guestPlayers();
    bool samePlayers = m_otherPlayers.size() == guests.size() + m_hostAwaySeats.size();

    for (size_t index = 0; samePlayers && index < guests.size(); ++index)
    {
        samePlayers = m_otherPlayers[index].id == guests[index]->id && !m_otherPlayers[index].away;
    }

    if (!whole && samePlayers)
    {
        for (size_t index = 0; index < guests.size(); ++index)
        {
            OtherPlayer &player = m_otherPlayers[index];
            player.loadingMap = guests[index]->loadingMap;
            player.body = guests[index]->body;

            if (const HostPeer *pPeer = hostPeerOfPlayer(player.id))
            {
                player.action = pPeer->action;
            }
        }

        return;
    }

    m_otherPlayers.clear();

    for (const std::unique_ptr<GameSession::GuestPlayer> &pGuest : m_session.guestPlayers())
    {
        OtherPlayer player;
        player.id = pGuest->id;
        const HostPeer *pShownPeer = hostPeerOfPlayer(pGuest->id);
        fillOtherPlayer(player, pGuest->party, pShownPeer != nullptr ? pShownPeer->avatarMember : 0);

        if (const HostPeer *pPeer = pShownPeer)
        {
            player.action = pPeer->action;

            // The player is named as the member that stands for it; as its game named it only without one.
            if (player.name.empty())
            {
                player.name = pPeer->name;
            }
        }

        player.loadingMap = pGuest->loadingMap;
        player.body = pGuest->body;
        m_otherPlayers.push_back(std::move(player));
    }

    // Those who stepped out, as they were when they went.
    for (const AwaySeat &seat : m_hostAwaySeats)
    {
        m_otherPlayers.push_back(seat.shown);
    }
}

void CoopSession::hostSendPlayers()
{
    // Everyone, the host's own character first; each game leaves its own out.
    Engine::ByteWriter message = beginMessage(Coop::Message::Players);
    std::vector<OtherPlayer> players;

    if (const Party *pLocalParty = m_session.partyOfPlayer(LocalPlayer))
    {
        OtherPlayer local;
        local.id = LocalPlayer;
        fillOtherPlayer(local, *pLocalParty, ownAvatarMember());
        players.push_back(std::move(local));
    }

    players.insert(players.end(), m_otherPlayers.begin(), m_otherPlayers.end());
    message.u8(uint8_t(players.size()));

    for (const OtherPlayer &player : players)
    {
        message.u8(player.id);
        message.text(player.name, Coop::MaxNameLength);
        message.text(player.className, Coop::MaxNameLength);
        message.u8(uint8_t(player.raceId));
        message.u8(uint8_t(player.sexId));
        message.u8(player.gearTier);
        message.u8(player.avatarMember);
        message.u32(player.portraitPictureId);
        message.text(player.portraitTextureName, Coop::MaxNameLength);
        message.u32(player.level);
        message.i32(player.health);
        message.i32(player.maxHealth);
        message.i32(player.spellPoints);
        message.i32(player.maxSpellPoints);
        message.u8(player.condition);
        message.boolean(player.down);
        message.boolean(player.loadingMap);
        message.boolean(player.away);
        message.u8(uint8_t(std::min(player.mates.size(), Coop::MaxPartyMates)));

        for (size_t index = 0; index < player.mates.size() && index < Coop::MaxPartyMates; ++index)
        {
            const OtherPlayer::Mate &mate = player.mates[index];
            message.u32(mate.portraitPictureId);
            message.text(mate.portraitTextureName, Coop::MaxNameLength);
            message.i32(mate.health);
            message.i32(mate.maxHealth);
            message.u8(mate.condition);
        }
    }

    if (message.bytes() == m_hostSentPlayersBytes)
    {
        return;
    }

    m_hostSentPlayersBytes = message.bytes();
    sendToAll(Coop::ChannelControl, Engine::NetDelivery::Reliable, message);
}

void CoopSession::hostSendBodies()
{
    IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();

    if (pWorldRuntime == nullptr || m_session.guestPlayers().empty())
    {
        return;
    }

    Engine::ByteWriter message = beginMessage(Coop::Message::Bodies);
    message.u16(m_mapRevision);
    message.f32(pWorldRuntime->gameMinutes());
    message.u8(uint8_t(1 + m_session.guestPlayers().size()));
    message.u8(LocalPlayer);
    writeBody(message, GameplayPlayerBody{pWorldRuntime->partyX(), pWorldRuntime->partyY(),
        pWorldRuntime->partyFootZ(), pWorldRuntime->gameplayCameraYawRadians(),
        pWorldRuntime->partyIsFlyingForEventChecks()});
    writeAction(message, m_ownAction);

    for (const std::unique_ptr<GameSession::GuestPlayer> &pGuest : m_session.guestPlayers())
    {
        const HostPeer *pPeer = hostPeerOfPlayer(pGuest->id);
        message.u8(pGuest->id);
        writeBody(message, pGuest->body);
        writeAction(message, pPeer != nullptr ? pPeer->action : PlayerAction{});
    }

    sendToAll(Coop::ChannelStream, Engine::NetDelivery::UnreliableNewest, message);
}

void CoopSession::hostSendTravelProposal()
{
    const std::optional<GameSession::TravelProposal> &proposal = m_session.travelProposal();
    Engine::ByteWriter state;
    state.boolean(proposal.has_value());

    if (proposal)
    {
        state.u32(proposal->serial);
        state.u8(proposal->proposer);
        state.boolean(proposal->open);
        state.u8(uint8_t(proposal->accepted.size()));

        for (PlayerId player : proposal->accepted)
        {
            state.u8(player);
        }

        // The move travels as a map's event state holds one.
        EventRuntimeState carrier;
        carrier.pendingMapMove = proposal->move;
        state.block(SaveSections::encode(carrier));
        // What the trip will cost everyone, for the other players' prompt (a save holds no unpaid trip).
        const TravelCost cost = proposal->move.unpaidCost.value_or(TravelCost{});
        state.i32(cost.fareGold);
        state.i32(cost.waitDays);
        state.i32(cost.waitFood);
        state.i32(cost.travelDays);
        state.i32(cost.travelFood);
    }

    const std::optional<GameSession::RestProposal> &rest = m_session.restProposal();
    state.boolean(rest.has_value());

    if (rest)
    {
        state.u32(rest->serial);
        state.u8(rest->proposer);
        state.boolean(rest->heal);
        state.f32(rest->minutes);
        state.u8(uint8_t(rest->accepted.size()));

        for (PlayerId player : rest->accepted)
        {
            state.u8(player);
        }
    }

    if (state.bytes() == m_hostSentTravelBytes)
    {
        return;
    }

    m_hostSentTravelBytes = state.bytes();
    Engine::ByteWriter message = beginMessage(Coop::Message::TravelVote);
    message.raw(state.bytes());
    sendToAll(Coop::ChannelControl, Engine::NetDelivery::Reliable, message);
}

void CoopSession::hostSendRulesState()
{
    const MawRules *pRules = m_session.mawRules();

    if (pRules == nullptr)
    {
        return;
    }

    // The game's part: what is a party's own (its auras, held food, deaths) travels with each player's character.
    std::vector<uint8_t> bytes = SaveSections::encode(pRules->state());

    if (bytes == m_hostSentRulesBytes)
    {
        return;
    }

    Engine::ByteWriter message = beginMessage(Coop::Message::RulesState);
    message.block(bytes);
    m_hostSentRulesBytes = std::move(bytes);
    sendToAll(Coop::ChannelControl, Engine::NetDelivery::Reliable, message);
}

void CoopSession::hostSendLentAuras()
{
    for (HostPeer &peer : m_hostPeers)
    {
        const GameSession::GuestPlayer *pGuest =
            peer.player != LocalPlayer ? m_session.guestPlayer(peer.player) : nullptr;

        if (pGuest == nullptr || peer.readyMapRevision != m_mapRevision
            || (peer.sentLentAuras && peer.sentLentAuras->first == m_mapRevision
                && peer.sentLentAuras->second == pGuest->lentAuras)
            || (!peer.sentLentAuras && pGuest->lentAuras.empty()))
        {
            continue;
        }

        peer.sentLentAuras = std::pair<uint16_t, std::vector<LentAura>>(m_mapRevision, pGuest->lentAuras);
        Engine::ByteWriter message = beginMessage(Coop::Message::LentAuras);
        message.u8(uint8_t(std::min<size_t>(pGuest->lentAuras.size(), MaxLentAuras)));

        for (size_t index = 0; index < pGuest->lentAuras.size() && index < MaxLentAuras; ++index)
        {
            const LentAura &aura = pGuest->lentAuras[index];
            message.u32(aura.spellId);
            message.f32(aura.skill);
            message.u8(aura.mastery);
            message.f32(aura.level);
        }

        send(peer.peer, Coop::ChannelControl, Engine::NetDelivery::Reliable, message);
    }
}

void CoopSession::hostSendCampaign()
{
    std::vector<uint8_t> campaign = SaveSections::encodeCampaign(m_session.campaign().snapshot());

    if (campaign == m_hostSentCampaignBytes)
    {
        return;
    }

    Engine::ByteWriter message = beginMessage(Coop::Message::CampaignState);
    message.block(campaign);
    m_hostSentCampaignBytes = std::move(campaign);

    // Whatever map a guest's game has or is loading: the campaign is the game's, not a map's.
    sendToAll(Coop::ChannelControl, Engine::NetDelivery::Reliable, message);
}

void CoopSession::hostSendPartyStates()
{
    for (HostPeer &peer : m_hostPeers)
    {
        GameSession::GuestPlayer *pGuest = peer.player != LocalPlayer ? m_session.guestPlayer(peer.player) : nullptr;

        if (pGuest == nullptr || peer.readyMapRevision != m_mapRevision)
        {
            continue;
        }

        Party::Snapshot party = characterForWire(pGuest->party.characterSnapshot());
        // The whole character goes out when something of it changed besides its vitals; else the vitals alone.
        Engine::ByteWriter stable;
        const GameplayUiController::HeldInventoryItemState &held = pGuest->ui.heldInventoryItem();
        const std::optional<InventoryItem> heldItem =
            held.active ? std::optional<InventoryItem>(held.item) : std::nullopt;
        writeHeldItem(stable, heldItem);
        stable.block(SaveSections::encodeCharacters(withoutCharacterVitals(party)));
        const CharacterVitals vitals = takeCharacterVitals(party);
        const bool whole = peer.partyStateOwed || stable.bytes() != peer.sentPartyBytes;

        if (!whole && vitals == peer.sentVitals)
        {
            continue;
        }

        peer.partyStateOwed = false;
        peer.sentPartyBytes = stable.bytes();
        peer.sentVitals = vitals;
        ++peer.partyRevision;
        Engine::ByteWriter message = beginMessage(whole ? Coop::Message::PartyState : Coop::Message::PartyVitals);
        message.u32(peer.partyRevision);
        message.u32(peer.commandEpoch);
        message.u32(peer.putSerial);

        if (whole)
        {
            writeHeldItem(message, heldItem);
            message.block(SaveSections::encodeCharacters(party));
        }
        else
        {
            writeVitals(message, vitals);
        }

        peer.sentParties.emplace_back(peer.partyRevision, std::move(party));

        while (peer.sentParties.size() > SentPartyHistory)
        {
            peer.sentParties.pop_front();
        }

        send(peer.peer, Coop::ChannelControl, Engine::NetDelivery::Reliable, message);
    }
}

void CoopSession::hostHandleCharacterPut(HostPeer &peer, Engine::ByteReader &reader)
{
    const uint32_t serial = reader.u32();
    const uint32_t baseRevision = reader.u32();
    const uint32_t commandEpoch = reader.u32();
    std::optional<InventoryItem> heldItem;
    Party::Snapshot put;
    GameSession::GuestPlayer *pGuest = m_session.guestPlayer(peer.player);

    if (!readHeldItem(reader, heldItem) || pGuest == nullptr
        || !SaveSections::decodeCharacters(reader.block(Coop::MaxBlockBytes), put) || !reader.ok()
        || put.members.empty() || put.members.size() > Party::MaxMembers)
    {
        return;
    }

    // Whatever comes of it, the next state says the change was seen.
    peer.putSerial = serial;
    peer.partyStateOwed = true;
    const auto base = std::find_if(peer.sentParties.begin(), peer.sentParties.end(),
        [baseRevision](const std::pair<uint32_t, Party::Snapshot> &sent) { return sent.first == baseRevision; });

    // A change made before the peer's game knew what its last command did, or measured against a state too old to
    // be kept, is dropped: the state that follows puts its game right.
    if (commandEpoch != peer.commandEpoch || base == peer.sentParties.end())
    {
        return;
    }

    peer.acceptedPutSerial = serial;
    pGuest->party.applyMirror(
        mergeGuestCharacter(base->second, characterForWire(pGuest->party.characterSnapshot()), put));
    pGuest->ui.heldInventoryItem() = {};

    if (heldItem)
    {
        pGuest->ui.heldInventoryItem().active = true;
        pGuest->ui.heldInventoryItem().item = *heldItem;
    }
}

void CoopSession::hostHandleCommand(HostPeer &peer, Engine::ByteReader &reader)
{
    const uint32_t commandSerial = reader.u32();
    const uint16_t mapRevision = reader.u16();
    const Coop::Command command = Coop::Command(reader.u8());
    const uint32_t characterChange = reader.u32();
    GameSession::GuestPlayer *pGuest = m_session.guestPlayer(peer.player);

    // A command for the map the players have left is dropped ("Old packets").
    if (!reader.ok() || pGuest == nullptr || mapRevision != m_mapRevision || pGuest->loadingMap)
    {
        return;
    }

    // The world's half of a change of the character the host dropped is dropped with it: an item out of a chest
    // would otherwise be gone from the chest and not in the bags, one dropped from the cursor on the ground and still
    // on the cursor. The state the host owes the peer's game puts the character right; the chest is sent anew.
    if (characterChange != 0 && characterChange != peer.acceptedPutSerial)
    {
        peer.sentLootViews.assign(1, 0xff);
        return;
    }

    static_cast<void>(commandSerial);
    PlayerCommands &commands = m_session.playerCommands();

    switch (command)
    {
        case Coop::Command::WorldCall:
        {
            const std::vector<uint8_t> call = reader.block(Coop::MaxBlockBytes);

            if (reader.ok())
            {
                commands.runReplicaWorldCall(peer.player, call);
            }

            break;
        }

        case Coop::Command::PositionTrigger:
        {
            ReplicaPositionTrigger trigger;
            const uint8_t kind = reader.u8();
            trigger.first = reader.u32();
            trigger.second = reader.u32();

            if (reader.ok() && kind <= uint8_t(ReplicaPositionTrigger::Kind::IndoorTouchFace))
            {
                trigger.kind = ReplicaPositionTrigger::Kind(kind);
                ++peer.commandEpoch;
                commands.touchPositionTrigger(peer.player, trigger);
            }

            break;
        }

        case Coop::Command::CastSpell:
        {
            std::optional<PlayerId> targetPlayer;
            const PartySpellCastRequest request = CoopCodec::readSpellCastRequest(reader, targetPlayer);

            if (reader.ok() && request.casterMemberIndex < pGuest->party.members().size())
            {
                ++peer.commandEpoch;
                commands.castSpellDirect(peer.player, m_session.data().spellTable(), request, targetPlayer);
            }

            break;
        }

        case Coop::Command::ActivateWorldHit:
        {
            const GameplayWorldHit hit = CoopCodec::readWorldHit(reader);

            if (reader.ok())
            {
                ++peer.commandEpoch;
                commands.activateWorldHit(peer.player, hit);
            }

            break;
        }

        case Coop::Command::ProposeTravel:
        {
            EventRuntimeState carrier;

            // Another map, named: the others are asked, as for an exit the host's own player took.
            if (SaveSections::decode(reader.block(Coop::MaxBlockBytes), carrier) && reader.ok()
                && carrier.pendingMapMove && carrier.pendingMapMove->mapName
                && !carrier.pendingMapMove->mapName->empty() && !m_session.travelProposal())
            {
                m_session.proposeTravel(std::move(*carrier.pendingMapMove), peer.player);
            }

            break;
        }

        case Coop::Command::TakeWorldItem:
        {
            // The item the guest meant, if it still lies in this world: out of it, and to the guest's game. An
            // item another player took a moment ago is gone, and the guest is given nothing.
            const uint32_t itemKey = reader.u32();
            IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();
            const std::optional<size_t> itemIndex = reader.ok() && pWorldRuntime != nullptr
                ? pWorldRuntime->worldItemIndexOfKey(itemKey)
                : std::nullopt;
            GameplayWorldItemInspectState taken;
            // Within a player's reach of where the host has the guest, and something over for the guest's last
            // steps the host has not heard of.
            bool withinReach = false;

            if (itemIndex && pGuest != nullptr)
            {
                std::vector<GameplayWorldItemPresentationState> lying;
                pWorldRuntime->collectWorldItemPresentationStates(lying);

                for (const GameplayWorldItemPresentationState &item : lying)
                {
                    if (item.key == itemKey)
                    {
                        const float eyeZ = pGuest->body.footZ + 160.0f;
                        withinReach = std::hypot(item.x - pGuest->body.x, item.y - pGuest->body.y, item.z - eyeZ)
                            <= TakeReach;
                        break;
                    }
                }
            }

            if (itemIndex && withinReach && !pWorldRuntime->hasCustomWorldItemActivation(*itemIndex)
                && commands.takeWorldItem(peer.player, *itemIndex, taken))
            {
                Engine::ByteWriter message = beginMessage(Coop::Message::TakenWorldItem);
                message.block(SaveSections::encode(taken.item));
                message.u32(taken.goldAmount);
                message.boolean(taken.isGold);
                send(peer.peer, Coop::ChannelControl, Engine::NetDelivery::Reliable, message);
            }

            break;
        }

        case Coop::Command::Chest:
        {
            const uint8_t operation = reader.u8();

            if (operation == LootOperationClose)
            {
                if (reader.ok())
                {
                    commands.closeOpenChestAndCorpse(peer.player);
                }

                break;
            }

            const std::vector<uint8_t> viewBytes = reader.block(Coop::MaxBlockBytes);
            GameplayChestViewState chestView;
            GameplayCorpseViewState corpseView;

            if (!reader.ok())
            {
                break;
            }

            if (operation == LootOperationPutChest && SaveSections::decode(viewBytes, chestView))
            {
                commands.putOpenChest(peer.player, chestView);
            }
            else if (operation == LootOperationPutCorpse && SaveSections::decode(viewBytes, corpseView))
            {
                commands.putOpenCorpse(peer.player, corpseView);
            }

            // What the host now has is what the guest's game has: nothing of it is sent back.
            peer.sentLootViews.clear();
            {
                Engine::ByteWriter views;
                views.boolean(pGuest->chestView.has_value());

                if (pGuest->chestView)
                {
                    views.block(SaveSections::encode(*pGuest->chestView));
                }

                views.boolean(pGuest->corpseView.has_value());

                if (pGuest->corpseView)
                {
                    views.block(SaveSections::encode(*pGuest->corpseView));
                }

                peer.sentLootViews = views.bytes();
            }

            break;
        }

        case Coop::Command::TravelVote:
        {
            const bool accept = reader.boolean();

            if (reader.ok())
            {
                m_session.answerTravelProposal(peer.player, accept);
            }

            break;
        }

        case Coop::Command::Rest:
        {
            const uint8_t operation = reader.u8();
            const bool flag = reader.boolean();
            const float minutes = reader.f32();

            if (!reader.ok())
            {
                break;
            }

            if (operation == RestOperationVote)
            {
                m_session.answerRestProposal(peer.player, flag);
            }
            else if (operation == RestOperationPropose && std::isfinite(minutes) && minutes > 0.0f
                && minutes <= MaxRestMinutes && !m_session.restProposal())
            {
                m_session.proposeRest(flag, minutes, peer.player);
            }

            break;
        }

        case Coop::Command::QuestItem:
        {
            InventoryItem item;

            // The world's from now on: every player's party has it, and the campaign's next state says so.
            if (SaveSections::decode(reader.block(Coop::MaxBlockBytes), item) && reader.ok()
                && pGuest->party.pouchFor(item) == ItemPouch::Quest)
            {
                pGuest->party.addToPouch(ItemPouch::Quest, item);
            }

            break;
        }

        case Coop::Command::ReturnDowned:
        {
            std::string message;

            if (m_application.returnDownedPlayer(peer.player, message))
            {
                ++peer.commandEpoch;
            }

            break;
        }

        case Coop::Command::House:
        {
            const uint8_t operation = reader.u8();
            const uint8_t stockMode = reader.u8();
            const size_t slotIndex = reader.u32();

            if (!reader.ok() || stockMode > uint8_t(HouseStockMode::GuildSpellbooks))
            {
                break;
            }

            if (operation <= uint8_t(HouseStockAction::Reroll))
            {
                ++peer.commandEpoch;
                commands.houseStockAction(
                    peer.player, HouseStockAction(operation), HouseStockMode(stockMode), slotIndex);
            }
            else if (operation == HouseOperationCloseStock || operation == HouseOperationCloseService)
            {
                commands.houseScreenClose(peer.player, operation == HouseOperationCloseStock);
            }
            else if (operation == HouseOperationBankAmount)
            {
                ++peer.commandEpoch;
                commands.houseBankAmount(peer.player, uint32_t(slotIndex));
            }

            break;
        }

        case Coop::Command::Dialogue:
        {
            const uint8_t operation = reader.u8();
            const size_t selectionIndex = reader.u32();
            EventDialogAction action;
            const uint8_t kind = reader.u8();
            action.id = reader.u32();
            action.secondaryId = reader.u32();
            action.memberIndex = reader.u32();
            action.argument = reader.text(Coop::MaxNameLength);

            if (!reader.ok() || kind > uint8_t(EventDialogActionKind::EventChoice)
                || operation > DialogueOperationClose)
            {
                break;
            }

            action.kind = EventDialogActionKind(kind);
            ++peer.commandEpoch;

            if (operation == DialogueOperationClose)
            {
                commands.dialogueClose(peer.player);
            }
            else
            {
                commands.dialogueAction(peer.player, selectionIndex, action, operation == DialogueOperationOverride);
            }

            break;
        }

        default:
            break;
    }

    hostSendOutcome(peer);
    hostSendLootViews(peer);
    hostSendHouseScreens(peer);
}

void CoopSession::hostSendOutcome(HostPeer &peer)
{
    GameSession::GuestPlayer *pGuest = peer.player != LocalPlayer ? m_session.guestPlayer(peer.player) : nullptr;

    if (pGuest == nullptr || !pGuest->outcome.any() || peer.readyMapRevision != m_mapRevision)
    {
        return;
    }

    // What the guest's game shows next is of the world as it now stands: a dialogue reads the NPC's state, the
    // quests and the character, so those go first, on the same channel.
    hostSendActorRecords();
    hostSendMapSections();
    hostSendCampaign();
    hostSendPartyStates();
    GameSession::GuestPlayer::Outcome outcome = std::move(pGuest->outcome);
    pGuest->outcome = {};
    // The conversation travels as a map's event state holds it.
    EventRuntimeState carrier;

    if (outcome.dialogue)
    {
        carrier.pendingDialogueContext = std::move(outcome.dialogue->context);
        carrier.dialogueState = std::move(outcome.dialogue->dialogueState);
        carrier.messages = std::move(outcome.dialogue->messages);
    }

    Engine::ByteWriter message = beginMessage(Coop::Message::Outcome);
    message.u16(m_mapRevision);
    message.boolean(outcome.dialogue.has_value());
    message.boolean(outcome.dialogueClosed);
    message.u32(outcome.dialogue ? uint32_t(outcome.dialogue->previousMessageCount) : 0);
    message.boolean(outcome.dialogue ? outcome.dialogue->allowNpcFallbackContent : true);
    message.block(SaveSections::encode(carrier));
    CoopCodec::writeSounds(message, outcome.sounds);
    message.u8(uint8_t(std::min<size_t>(outcome.statusTexts.size(), 255)));

    for (size_t index = 0; index < outcome.statusTexts.size() && index < 255; ++index)
    {
        message.text(outcome.statusTexts[index].first, 1024);
        message.f32(outcome.statusTexts[index].second);
    }

    send(peer.peer, Coop::ChannelControl, Engine::NetDelivery::Reliable, message);
}

void CoopSession::hostSendHouseScreens(HostPeer &peer)
{
    const GameSession::GuestPlayer *pGuest = peer.player != LocalPlayer ? m_session.guestPlayer(peer.player) : nullptr;

    if (pGuest == nullptr || peer.readyMapRevision != m_mapRevision)
    {
        return;
    }

    const GameplayUiController::HouseShopOverlayState &stock = pGuest->ui.houseShopOverlay();
    const GameplayUiController::InventoryNestedOverlayState &service = pGuest->ui.inventoryNestedOverlay();
    const bool serviceOpen = service.active && isShopServiceMode(service.mode);
    Engine::ByteWriter screens;
    screens.boolean(stock.active);
    screens.u32(stock.houseId);
    screens.u8(uint8_t(stock.mode));
    screens.u32(stock.spellbookShelf);
    screens.boolean(serviceOpen);
    screens.u8(serviceOpen ? uint8_t(service.mode) : 0);
    screens.u32(serviceOpen ? service.houseId : 0);
    // The bank asking this player for an amount to deposit or withdraw.
    screens.u8(uint8_t(pGuest->ui.houseBankState().inputMode));
    screens.u32(pGuest->ui.houseBankState().houseId);

    if (screens.bytes() == peer.sentHouseScreens)
    {
        return;
    }

    peer.sentHouseScreens = screens.bytes();
    Engine::ByteWriter message = beginMessage(Coop::Message::HouseScreens);
    message.raw(screens.bytes());
    send(peer.peer, Coop::ChannelControl, Engine::NetDelivery::Reliable, message);
}

void CoopSession::hostSendLootViews(HostPeer &peer)
{
    const GameSession::GuestPlayer *pGuest = peer.player != LocalPlayer ? m_session.guestPlayer(peer.player) : nullptr;

    if (pGuest == nullptr || peer.readyMapRevision != m_mapRevision)
    {
        return;
    }

    Engine::ByteWriter views;
    views.boolean(pGuest->chestView.has_value());

    if (pGuest->chestView)
    {
        views.block(SaveSections::encode(*pGuest->chestView));
    }

    views.boolean(pGuest->corpseView.has_value());

    if (pGuest->corpseView)
    {
        views.block(SaveSections::encode(*pGuest->corpseView));
    }

    if (views.bytes() == peer.sentLootViews)
    {
        return;
    }

    peer.sentLootViews = views.bytes();
    Engine::ByteWriter message = beginMessage(Coop::Message::LootViews);
    message.u16(m_mapRevision);
    message.raw(views.bytes());
    send(peer.peer, Coop::ChannelControl, Engine::NetDelivery::Reliable, message);
}

void CoopSession::hostSendMoveOrders()
{
    for (HostPeer &peer : m_hostPeers)
    {
        const GameSession::GuestPlayer *pGuest =
            peer.player != LocalPlayer ? m_session.guestPlayer(peer.player) : nullptr;

        if (pGuest == nullptr || peer.readyMapRevision != m_mapRevision
            || peer.sentBodyOrderSerial == pGuest->bodyOrderSerial)
        {
            continue;
        }

        peer.sentBodyOrderSerial = pGuest->bodyOrderSerial;
        Engine::ByteWriter message = beginMessage(Coop::Message::MoveOrder);
        message.u16(m_mapRevision);
        message.u32(pGuest->bodyOrderSerial);
        writeBody(message, pGuest->body);
        send(peer.peer, Coop::ChannelControl, Engine::NetDelivery::Reliable, message);
    }
}

void CoopSession::hostSendMapMessage(const Engine::ByteWriter &message)
{
    for (HostPeer &peer : m_hostPeers)
    {
        if (peer.player == LocalPlayer)
        {
            continue;
        }

        if (peer.readyMapRevision == m_mapRevision)
        {
            send(peer.peer, Coop::ChannelControl, Engine::NetDelivery::Reliable, message);
        }
        else if (peer.readyMapRevision != UnreadyForGood)
        {
            peer.waitingMapMessages.push_back(message.bytes());
            peer.waitingMapBytes += message.bytes().size();

            // A game that loads for so long that this much piled up for it is not coming: it is let go.
            if (peer.waitingMapBytes > MaxWaitingMapBytes)
            {
                peer.waitingMapMessages.clear();
                peer.waitingMapBytes = 0;
                peer.readyMapRevision = UnreadyForGood;
                hostRefuse(peer, Engine::tr("the map took too long to load"));
            }
        }
    }
}

void CoopSession::hostPrimeMapBaselines()
{
    m_hostActorSignatures.clear();
    m_hostActorStreams.clear();
    m_hostActorRefreshCursor = 0;
    m_hostSentEventState.clear();
    m_hostSentWorldItems.clear();
    m_hostSentMechanismsKey = 0;
    m_hostSentProjectiles.clear();
    m_hostSentImpacts.clear();
    const IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();

    // The missiles in flight and the impacts showing are in the state the guests load.
    const GameplayProjectileService &projectileService = m_session.gameplayProjectileService();

    for (const GameplayProjectileService::ProjectileState &projectile : projectileService.projectiles())
    {
        m_hostSentProjectiles[projectile.projectileId] = {projectile.x, projectile.y, projectile.z};
    }

    for (const GameplayProjectileService::ProjectileImpactState &impact : projectileService.projectileImpacts())
    {
        m_hostSentImpacts.insert(impact.effectId);
    }

    if (pWorldRuntime == nullptr)
    {
        return;
    }

    const size_t actorCount = pWorldRuntime->mapActorCount();
    m_hostActorSignatures.resize(actorCount);
    m_hostActorStreams.resize(actorCount);

    for (size_t actorIndex = 0; actorIndex < actorCount; ++actorIndex)
    {
        m_hostActorSignatures[actorIndex] = pWorldRuntime->replicaActorSignature(actorIndex);
        m_hostActorStreams[actorIndex].known =
            pWorldRuntime->captureReplicaActorPose(actorIndex, m_hostActorStreams[actorIndex].sent);
    }

    m_hostSentWorldItems = pWorldRuntime->encodeReplicaWorldItems();

    if (const EventRuntimeState *pEventState = pWorldRuntime->eventRuntimeState())
    {
        m_hostSentEventState = encodeSharedEventState(*pEventState);
        m_hostSentMechanismsKey = mechanismsKey(pEventState->mechanisms);
    }
}

void CoopSession::hostSendActorRecords()
{
    const IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();

    if (pWorldRuntime == nullptr)
    {
        return;
    }

    const size_t actorCount = std::min<size_t>(pWorldRuntime->mapActorCount(), 0xFFFF);
    std::vector<size_t> changed;

    for (size_t actorIndex = 0; actorIndex < actorCount; ++actorIndex)
    {
        const uint64_t signature = pWorldRuntime->replicaActorSignature(actorIndex);

        if (actorIndex >= m_hostActorSignatures.size())
        {
            m_hostActorSignatures.push_back(signature);
            changed.push_back(actorIndex);
        }
        else if (m_hostActorSignatures[actorIndex] != signature)
        {
            m_hostActorSignatures[actorIndex] = signature;
            changed.push_back(actorIndex);
        }
    }

    // In batches: a wave of new monsters is many records.
    for (size_t first = 0; first < changed.size(); first += ActorRecordsPerMessage)
    {
        const size_t count = std::min(ActorRecordsPerMessage, changed.size() - first);
        Engine::ByteWriter message = beginMessage(Coop::Message::ActorRecords);
        message.u16(m_mapRevision);
        message.u16(uint16_t(count));

        for (size_t index = first; index < first + count; ++index)
        {
            message.u16(uint16_t(changed[index]));
            message.block(pWorldRuntime->encodeReplicaActor(changed[index]));
        }

        hostSendMapMessage(message);
    }
}

void CoopSession::hostSendActorPoses()
{
    const IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();

    if (pWorldRuntime == nullptr)
    {
        return;
    }

    // Only the monsters whose records the guests have: a new one's pose follows its record.
    const size_t actorCount = std::min(pWorldRuntime->mapActorCount(), m_hostActorSignatures.size());
    m_hostActorStreams.resize(actorCount);
    std::vector<ReplicaActorPose> poses;

    // A few monsters go out each time whether they changed or not, so that every game is put right in time
    // whatever was lost.
    for (size_t refreshed = 0; refreshed < PoseRefreshPerTick && actorCount != 0; ++refreshed)
    {
        m_hostActorRefreshCursor = (m_hostActorRefreshCursor + 1) % actorCount;
        m_hostActorStreams[m_hostActorRefreshCursor].resend =
            std::max<uint8_t>(m_hostActorStreams[m_hostActorRefreshCursor].resend, 1);
    }

    ++m_hostPoseTick;
    std::vector<GameplayPlayerBody> guestBodies;

    for (const std::unique_ptr<GameSession::GuestPlayer> &pGuest : m_session.guestPlayers())
    {
        if (!pGuest->loadingMap)
        {
            guestBodies.push_back(pGuest->body);
        }
    }

    for (size_t actorIndex = 0; actorIndex < actorCount; ++actorIndex)
    {
        HostActorStream &stream = m_hostActorStreams[actorIndex];
        ReplicaActorPose pose;

        if (!pWorldRuntime->captureReplicaActorPose(actorIndex, pose))
        {
            continue;
        }

        // A monster far from every guest is looked at every fourth time: each game moves it on by its speed between.
        const bool near = std::any_of(guestBodies.begin(), guestBodies.end(),
            [&pose](const GameplayPlayerBody &body)
            {
                const float deltaX = pose.x - body.x;
                const float deltaY = pose.y - body.y;
                return deltaX * deltaX + deltaY * deltaY < NearPoseDistance * NearPoseDistance;
            });

        if (!near && stream.known && stream.resend == 0 && (m_hostPoseTick + actorIndex) % FarPoseTicks != 0)
        {
            continue;
        }

        if (!stream.known || poseDiffers(pose, stream.sent))
        {
            stream.resend = near ? PoseResendCount : 1;
        }

        if (stream.resend == 0)
        {
            continue;
        }

        --stream.resend;
        stream.known = true;
        stream.sent = pose;
        poses.push_back(pose);
    }

    // Each message fits one datagram.
    for (size_t first = 0; first < poses.size() || first == 0; first += PosesPerMessage)
    {
        const size_t count = std::min(PosesPerMessage, poses.size() - first);
        Engine::ByteWriter message = beginMessage(Coop::Message::ActorPoses);
        message.u16(m_mapRevision);
        message.f32(pWorldRuntime->gameMinutes());
        message.u8(uint8_t(count));

        for (size_t index = first; index < first + count; ++index)
        {
            writePose(message, poses[index]);
        }

        for (const HostPeer &peer : m_hostPeers)
        {
            if (peer.player != LocalPlayer && peer.readyMapRevision == m_mapRevision)
            {
                send(peer.peer, Coop::ChannelStream, Engine::NetDelivery::UnreliableNewest, message);
            }
        }

        if (poses.empty())
        {
            break;
        }
    }
}

void CoopSession::hostSendProjectiles()
{
    const GameplayProjectileService &service = m_session.gameplayProjectileService();
    Engine::ByteWriter events = beginMessage(Coop::Message::Projectiles);
    events.u16(m_mapRevision);
    Engine::ByteWriter body;
    uint16_t eventCount = 0;
    std::unordered_map<uint32_t, GameplayWorldPoint> flying;
    Engine::ByteWriter poses = beginMessage(Coop::Message::ProjectilePoses);
    poses.u16(m_mapRevision);
    uint16_t poseCount = 0;
    Engine::ByteWriter poseBody;

    for (const GameplayProjectileService::ProjectileState &projectile : service.projectiles())
    {
        if (projectile.isExpired)
        {
            continue;
        }

        flying[projectile.projectileId] = {projectile.x, projectile.y, projectile.z};

        if (!m_hostSentProjectiles.contains(projectile.projectileId))
        {
            body.u8(ProjectileEventSpawn);
            body.block(SaveSections::encode(projectile));
            ++eventCount;
        }

        if (poseCount < MaxProjectilePoses)
        {
            poseBody.u32(projectile.projectileId);
            poseBody.f32(projectile.x);
            poseBody.f32(projectile.y);
            poseBody.f32(projectile.z);
            poseBody.f32(projectile.velocityX);
            poseBody.f32(projectile.velocityY);
            poseBody.f32(projectile.velocityZ);
            ++poseCount;
        }
    }

    // A missile that is gone ended where it last was seen.
    for (const auto &[projectileId, point] : m_hostSentProjectiles)
    {
        if (!flying.contains(projectileId))
        {
            body.u8(ProjectileEventEnd);
            body.u32(projectileId);
            body.f32(point.x);
            body.f32(point.y);
            body.f32(point.z);
            ++eventCount;
        }
    }

    m_hostSentProjectiles = std::move(flying);
    std::unordered_set<uint32_t> impacts;

    for (const GameplayProjectileService::ProjectileImpactState &impact : service.projectileImpacts())
    {
        impacts.insert(impact.effectId);

        if (!m_hostSentImpacts.contains(impact.effectId))
        {
            body.u8(ProjectileEventImpact);
            body.block(SaveSections::encode(impact));
            ++eventCount;
        }
    }

    m_hostSentImpacts = std::move(impacts);

    if (eventCount != 0)
    {
        events.u16(eventCount);
        events.raw(body.bytes());
        hostSendMapMessage(events);
    }

    if (poseCount != 0)
    {
        poses.u16(poseCount);
        poses.raw(poseBody.bytes());

        for (const HostPeer &peer : m_hostPeers)
        {
            if (peer.player != LocalPlayer && peer.readyMapRevision == m_mapRevision)
            {
                send(peer.peer, Coop::ChannelStream, Engine::NetDelivery::UnreliableNewest, poses);
            }
        }
    }
}

void CoopSession::collectFrameSounds()
{
    IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();

    if (m_role != Role::Host || m_session.guestPlayers().empty() || pWorldRuntime == nullptr)
    {
        m_hostCollectedOutdoorSounds = 0;
        return;
    }

    // Sounds placed in the world: every player hears them from where it stands.
    if (const EventRuntimeState *pEventState = pWorldRuntime->eventRuntimeState())
    {
        for (const EventRuntimeState::PendingSound &sound : pEventState->pendingSounds)
        {
            if (sound.positional || sound.kind != EventRuntimeState::PendingSound::Kind::PlayOneShot)
            {
                m_hostSoundOutbox.push_back(sound);
            }
        }
    }

    if (m_application.m_pOutdoorWorldRuntime != nullptr && m_session.currentSceneKind() == SceneKind::Outdoor)
    {
        // The outdoor map's own list is emptied when the view plays it, which may be later than this.
        const std::vector<OutdoorWorldRuntime::AudioEvent> &events =
            m_application.m_pOutdoorWorldRuntime->pendingAudioEvents();

        if (events.size() < m_hostCollectedOutdoorSounds)
        {
            m_hostCollectedOutdoorSounds = 0;
        }

        for (size_t index = m_hostCollectedOutdoorSounds; index < events.size(); ++index)
        {
            const OutdoorWorldRuntime::AudioEvent &event = events[index];
            EventRuntimeState::PendingSound sound;
            sound.soundScope = event.soundScope;
            sound.soundId = event.soundId;
            sound.actorIndex = event.actorIndex;
            sound.pitch = event.pitch;
            sound.x = int32_t(std::lround(event.x));
            sound.y = int32_t(std::lround(event.y));
            sound.z = int32_t(std::lround(event.z));
            sound.positional = event.positional;
            sound.hasExplicitZ = true;
            m_hostSoundOutbox.push_back(std::move(sound));
        }

        m_hostCollectedOutdoorSounds = events.size();
    }

    if (m_hostSoundOutbox.size() > MaxQueuedSounds)
    {
        m_hostSoundOutbox.erase(m_hostSoundOutbox.begin(), m_hostSoundOutbox.end() - ptrdiff_t(MaxQueuedSounds));
    }
}

void CoopSession::hostSendSounds()
{
    if (!m_hostSoundOutbox.empty())
    {
        Engine::ByteWriter message = beginMessage(Coop::Message::Sounds);
        message.u16(m_mapRevision);
        CoopCodec::writeSounds(message, m_hostSoundOutbox);
        m_hostSoundOutbox.clear();

        for (const HostPeer &peer : m_hostPeers)
        {
            if (peer.player != LocalPlayer && peer.readyMapRevision == m_mapRevision)
            {
                send(peer.peer, Coop::ChannelControl, Engine::NetDelivery::Reliable, message);
            }
        }
    }

    // What each guest's own character would say or sound like here is for that guest's game.
    for (const HostPeer &peer : m_hostPeers)
    {
        GameSession::GuestPlayer *pGuest = peer.player != LocalPlayer ? m_session.guestPlayer(peer.player) : nullptr;

        if (pGuest == nullptr || pGuest->party.pendingAudioRequests().empty())
        {
            continue;
        }

        if (peer.readyMapRevision == m_mapRevision)
        {
            Engine::ByteWriter message = beginMessage(Coop::Message::PartyAudio);
            const std::vector<Party::PendingAudioRequest> &requests = pGuest->party.pendingAudioRequests();
            message.u8(uint8_t(std::min<size_t>(requests.size(), 255)));

            for (size_t index = 0; index < requests.size() && index < 255; ++index)
            {
                message.u8(uint8_t(requests[index].kind));
                message.u32(uint32_t(requests[index].soundId));
                message.u8(uint8_t(requests[index].scope));
                message.u32(uint32_t(requests[index].speechId));
                message.u32(uint32_t(requests[index].memberIndex));
            }

            send(peer.peer, Coop::ChannelControl, Engine::NetDelivery::Reliable, message);
        }

        pGuest->party.clearPendingAudioRequests();
    }
}

void CoopSession::hostSendMapSections()
{
    const IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();

    if (pWorldRuntime == nullptr)
    {
        return;
    }

    const auto sendSection = [this](Coop::MapSection section, const std::vector<uint8_t> &bytes)
    {
        Engine::ByteWriter message = beginMessage(Coop::Message::MapSection);
        message.u16(m_mapRevision);
        message.u8(uint8_t(section));
        message.block(bytes);
        hostSendMapMessage(message);
        ++m_traffic.sectionsSent[size_t(section) % m_traffic.sectionsSent.size()];
    };

    if (const EventRuntimeState *pEventState = pWorldRuntime->eventRuntimeState())
    {
        std::vector<uint8_t> eventState = encodeSharedEventState(*pEventState);

        if (eventState != m_hostSentEventState)
        {
            sendSection(Coop::MapSection::EventState, eventState);
            m_hostSentEventState = std::move(eventState);
        }

        const uint64_t key = mechanismsKey(pEventState->mechanisms);

        if (key != m_hostSentMechanismsKey)
        {
            m_hostSentMechanismsKey = key;
            sendSection(Coop::MapSection::Mechanisms, SaveSections::encode(pEventState->mechanisms));
        }
    }

    std::vector<uint8_t> worldItems = pWorldRuntime->encodeReplicaWorldItems();

    if (worldItems != m_hostSentWorldItems)
    {
        sendSection(Coop::MapSection::WorldItems, worldItems);
        m_hostSentWorldItems = std::move(worldItems);
    }
}

// ---------------------------------------------------------------------------------------------------------------
// A guest's side.

void CoopSession::updateGuest(float deltaSeconds)
{
    // What this game did with the character since the last frame goes out before the host's news comes in, and
    // with it what its player did to the map.
    if (m_guestMapLoaded && m_guestHasPartyState)
    {
        m_guestFramePutSerial = 0;
        guestSendCharacterPut();
        guestSendWorldRequests();
        guestSendLootChanges();
        guestSendHouseScreenChanges();
        guestSendQuestPouchAdditions();
        m_guestCharacterWriteSeconds += deltaSeconds;

        // What the character gains must outlive this game closing: a character from a file is kept there, and one
        // of this game's own goes into that game's Autosave.
        if (m_guestCharacterWriteSeconds >= CharacterFileWriteSeconds)
        {
            std::string error;

            const bool hasOwnAutosave = m_guestOwnGame && !m_guestOwnGame->playthroughId.empty();

            if (m_guestCharacterFile ? !writeJoinCharacter(error) : (hasOwnAutosave && !writeGuestOwnGame(error)))
            {
                m_lastNotice = error;
            }

            m_guestCharacterWriteSeconds = 0.0f;
        }
    }

    m_pTransport->service(0);
    Engine::NetEvent event;

    while (m_role == Role::Guest && m_pTransport != nullptr && m_pTransport->pollEvent(event))
    {
        guestHandleEvent(event);
    }

    // The host's news comes many times a second. A few seconds of none is told to the player, who would otherwise
    // stand in a still world wondering; the transport itself waits much longer before it gives the host up.
    m_guestSinceAskedSaveSeconds += deltaSeconds;
    m_guestDepartingSeconds = std::max(0.0f, m_guestDepartingSeconds - deltaSeconds);

    if (m_role == Role::Guest && m_guestMapLoaded)
    {
        m_guestSilentSeconds += deltaSeconds;
        m_guestSilenceToldSeconds += deltaSeconds;

        if (m_guestSilentSeconds >= SilenceToldAfterSeconds && m_guestSilenceToldSeconds >= SilenceToldEverySeconds)
        {
            m_guestSilenceToldSeconds = 0.0f;
            m_session.gameplayScreenRuntime().setStatusBarEvent(
                Engine::tr("No word from the host for {seconds} seconds. Waiting ...",
                    {{"seconds", int64_t(m_guestSilentSeconds)}}),
                SilenceToldEverySeconds);
        }
    }

    if (m_role != Role::Guest || m_pTransport == nullptr)
    {
        return;
    }

    // Through a lobby: the path to the host is found first, and the connection made over it.
    if (m_guestFindingPath && m_pLobby != nullptr && m_pEnet != nullptr)
    {
        m_pLobby->update(Engine::netNowMilliseconds());

        if (m_pLobby->joinState() == Engine::JoinState::Ready)
        {
            m_guestFindingPath = false;
            m_guestConnectSeconds = 0.0f;
            m_guestHostPeer = m_pEnet->connect(m_pLobby->joinAddress());
            m_lastNotice = m_pLobby->joinPath() == Engine::JoinPath::Relay
                ? Engine::tr("Connected to the host through the lobby server")
                : Engine::tr("Connected to the host directly");
        }
        else if (m_pLobby->joinState() == Engine::JoinState::Failed)
        {
            const Engine::JoinFailure failure = m_pLobby->joinFailure();
            guestReturnToOwnGame(failure == Engine::JoinFailure::NoSuchSession
                    ? Engine::tr("The lobby knows no session by that code")
                : failure == Engine::JoinFailure::ServerSilent ? Engine::tr("The lobby did not answer")
                : Engine::tr("No path to the host could be opened"));
        }

        return;
    }

    if (!m_guestMapLoaded)
    {
        m_guestConnectSeconds += deltaSeconds;

        if (!m_guestWelcomed && m_guestConnectSeconds > ConnectTimeoutSeconds)
        {
            guestReturnToOwnGame(Engine::tr("The host did not answer"));
        }

        return;
    }

    guestAdvanceProjectiles(deltaSeconds);
    m_guestPositionSeconds += deltaSeconds;

    if (m_guestPositionSeconds >= PositionIntervalSeconds)
    {
        m_guestPositionSeconds = std::fmod(m_guestPositionSeconds, PositionIntervalSeconds);
        guestSendPosition();
    }

    m_pTransport->service(0);
}

void CoopSession::guestHandleEvent(const Engine::NetEvent &event)
{
    if (event.peer != m_guestHostPeer)
    {
        return;
    }

    switch (event.type)
    {
        case Engine::NetEvent::Type::Connected:
            m_guestConnected = true;
            guestSendHello();
            break;

        case Engine::NetEvent::Type::Disconnected:
            // With the host gone unsaid, the world this game was sent at the host's last save is what is left.
            guestReturnToOwnGame(
                !m_guestGoodbye.empty() ? m_guestGoodbye
                    : m_guestKeptWorld ? Engine::tr("The connection to the host was lost. Its world as of its last"
                                                    " save is kept as {name}, under Load Game.",
                                             {{"name", m_guestKeptWorld->name}})
                                       : Engine::tr("The connection to the host was lost"));
            break;

        case Engine::NetEvent::Type::Message:
            ++m_traffic.messagesReceived;
            m_traffic.bytesReceived += event.payload.size();
            m_guestSilentSeconds = 0.0f;
            m_guestSilenceToldSeconds = 0.0f;

            if (const std::optional<std::vector<uint8_t>> message = unpackedMessage(event.payload))
            {
                guestHandleMessage(event.channel, *message);
            }

            break;
    }
}

void CoopSession::guestSendHello()
{
    const Party *pParty = m_session.partyOfPlayer(LocalPlayer);

    if (pParty == nullptr)
    {
        guestReturnToOwnGame(Engine::tr("There is no character to join with"));
        return;
    }

    // The character of the file this game joined with, else the game in progress's.
    const Party::Snapshot character = m_guestCharacterFile ? m_guestCharacterFile->character : pParty->snapshot();
    const Character *pMember = m_guestCharacterFile
        ? (character.members.empty() ? nullptr : &character.members.front())
        : pParty->member(pParty->activeMemberIndex());
    Engine::ByteWriter message = beginMessage(Coop::Message::Hello);
    message.u32(Coop::ProtocolVersion);
    message.u32(SaveSections::saveVersion());
    message.text(pMember != nullptr ? pMember->name : std::string(), Coop::MaxNameLength);
    message.block(SaveSections::encodeCharacters(character));
    std::vector<std::string> identity = m_application.coopContentIdentity();

    // The ruleset that counts is the one the character was made under.
    if (m_guestCharacterFile && !identity.empty())
    {
        identity.back() = "ruleset " + coopRulesText(m_guestCharacterFile->ruleset);
    }

    message.u16(uint16_t(std::min(identity.size(), Coop::MaxIdentityLines)));

    for (size_t line = 0; line < identity.size() && line < Coop::MaxIdentityLines; ++line)
    {
        message.text(identity[line], Coop::MaxIdentityLineLength);
    }

    message.text(m_joinPassword, Coop::MaxPasswordLength);
    message.u64(m_guestAwayFrom ? m_guestAwayFrom->seatKey : 0);
    m_guestOwnRulesText = identity.empty() || !identity.back().starts_with("ruleset ") ? std::string()
        : identity.back().substr(8);
    send(m_guestHostPeer, Coop::ChannelControl, Engine::NetDelivery::Reliable, message);
}

void CoopSession::guestHandleMessage(uint8_t, const std::vector<uint8_t> &payload)
{
    Engine::ByteReader reader(payload);
    const Coop::Message message = Coop::Message(reader.u8());

    if (!reader.ok())
    {
        return;
    }

    // The channels do not wait for each other: the host's quests or its ruleset's state may arrive before its
    // world, which is the larger message. Until that world is loaded this game is still the guest's own, and
    // putting the host's quests into it would make them the guest's own game's.
    if (!m_guestMapLoaded
        && (message == Coop::Message::CampaignState || message == Coop::Message::RulesState
            || message == Coop::Message::TravelVote))
    {
        m_guestHeldGameNews[uint8_t(message)] = payload;
        return;
    }

    switch (message)
    {
        case Coop::Message::Welcome:
            m_guestOwnPlayer = reader.u8();
            m_guestWelcomed = reader.ok();
            // In a session again: the one this game had stepped out of is this one, or is behind it.
            m_guestAwayFrom.reset();
            // Who of the party stands for this player, where it is not the first.
            if (ownAvatarMember() != 0)
            {
                tellOwnAvatar();
            }
            break;

        case Coop::Message::SteppedOut:
            guestFinishStepOut();
            break;

        case Coop::Message::TravelDeparting:
            // The vote is over; what remains is the wait for the host's map (a while at the most).
            m_guestDepartingSeconds = 45.0f;
            m_session.setReplicaTravelProposal(std::nullopt);
            break;

        case Coop::Message::Refused:
            m_guestGoodbye = Engine::tr("The host refused: {reason}", {{"reason", reader.text()}});
            m_lastNotice = m_guestGoodbye;
            break;

        case Coop::Message::WorldCopy:
            guestHandleWorldCopy(reader);
            break;

        case Coop::Message::Chat:
        {
            const PlayerId player = reader.u8();
            const std::string text = reader.text(Coop::MaxChatLength);

            if (reader.ok() && !text.empty())
            {
                addChatLine(player, text);
            }

            break;
        }

        case Coop::Message::Presentation:
        {
            const uint16_t mapRevision = reader.u16();
            const uint8_t kind = reader.u8();
            const std::string name = reader.text(Coop::MaxNameLength);

            if (!reader.ok() || mapRevision != m_mapRevision || !m_guestMapLoaded)
            {
                break;
            }

            // Shown here as in the host's game; what follows it in the story is the host's events' to do.
            if (kind == Coop::PresentationCinematic)
            {
                m_session.playCinematic(name, 0);
            }
            else if (kind == Coop::PresentationMovie)
            {
                IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();

                if (EventRuntimeState *pState = pWorldRuntime != nullptr ? pWorldRuntime->eventRuntimeState() : nullptr)
                {
                    pState->pendingMovie = EventRuntimeState::PendingMovie{name, false};
                }
            }

            break;
        }

        case Coop::Message::HostSaved:
        {
            // What the character has now is kept as the host's game is: in its file, or in this game's own.
            std::string error;
            const bool hasOwnAutosave = m_guestOwnGame && !m_guestOwnGame->playthroughId.empty();

            if (m_guestMapLoaded && m_guestHasPartyState
                && (m_guestCharacterFile ? !writeJoinCharacter(error) : (hasOwnAutosave && !writeGuestOwnGame(error))))
            {
                m_lastNotice = error;
            }

            m_guestCharacterWriteSeconds = 0.0f;
            m_session.gameplayScreenRuntime().setStatusBarEvent(Engine::tr("The host saved the game"), 3.0f);
            break;
        }

        case Coop::Message::TakenWorldItem:
        {
            GameplayWorldItemInspectState taken;
            const bool itemRead = SaveSections::decode(reader.block(Coop::MaxBlockBytes), taken.item);
            taken.goldAmount = reader.u32();
            taken.isGold = reader.boolean();

            if (itemRead && reader.ok() && m_guestMapLoaded)
            {
                GameplayInteractionController::receiveTakenWorldItem(m_session.gameplayScreenRuntime(), taken);
                // Sent at once: a whole state of the host's that is already on its way acknowledges the last
                // change sent, and would otherwise be taken as newer than the item just received and wipe it.
                guestSendCharacterPut();
            }

            break;
        }

        case Coop::Message::Ping:
        {
            const PlayerId player = reader.u8();
            const uint16_t mapRevision = reader.u16();
            const float x = reader.f32();
            const float y = reader.f32();
            const float z = reader.f32();

            if (reader.ok() && mapRevision == m_mapRevision && std::isfinite(x) && std::isfinite(y)
                && std::isfinite(z))
            {
                addPing(player, x, y, z);
            }

            break;
        }

        case Coop::Message::WorldState:
            guestHandleWorldState(reader);
            break;

        case Coop::Message::Players:
            guestHandlePlayers(reader);
            break;

        case Coop::Message::Bodies:
            guestHandleBodies(reader);
            break;

        case Coop::Message::ActorRecords:
            guestHandleActorRecords(reader);
            break;

        case Coop::Message::ActorPoses:
            guestHandleActorPoses(reader);
            break;

        case Coop::Message::MapSection:
            guestHandleMapSection(reader);
            break;

        case Coop::Message::Projectiles:
            guestHandleProjectiles(reader);
            break;

        case Coop::Message::ProjectilePoses:
            guestHandleProjectilePoses(reader);
            break;

        case Coop::Message::Sounds:
            guestHandleSounds(reader);
            break;

        case Coop::Message::HouseScreens:
            guestHandleHouseScreens(reader);
            break;

        case Coop::Message::PartyAudio:
            guestHandlePartyAudio(reader);
            break;

        case Coop::Message::PartyState:
            guestHandlePartyState(reader);
            break;

        case Coop::Message::PartyVitals:
            guestHandlePartyVitals(reader);
            break;

        case Coop::Message::Outcome:
            guestHandleOutcome(reader);
            break;

        case Coop::Message::MoveOrder:
            guestHandleMoveOrder(reader);
            break;

        case Coop::Message::LootViews:
            guestHandleLootViews(reader);
            break;

        case Coop::Message::CampaignState:
            guestHandleCampaign(reader);
            break;

        case Coop::Message::TravelVote:
            guestHandleTravelProposal(reader);
            break;

        case Coop::Message::RulesState:
            guestHandleRulesState(reader);
            break;

        case Coop::Message::LentAuras:
            guestHandleLentAuras(reader);
            break;

        default:
            break;
    }
}

void CoopSession::guestHandleWorldState(Engine::ByteReader &reader)
{
    // The wait for the host's map is over: this game loads it now.
    m_guestDepartingSeconds = 0.0f;

    const uint16_t mapRevision = reader.u16();
    const GameplayPlayerBody body = readBody(reader);
    const uint32_t bodyOrderSerial = reader.u32();
    const std::vector<uint8_t> gameBytes = reader.block(Coop::MaxBlockBytes);
    std::string error;
    std::optional<GameSaveData> worldState =
        reader.ok() ? SaveSections::decodeGame(gameBytes, error) : std::nullopt;

    if (!worldState || !finiteBody(body))
    {
        guestReturnToOwnGame(Engine::tr("The host's map state could not be read"));
        return;
    }

    // The first state of a session: this game's own is kept for the way back.
    if (!m_guestOwnGame)
    {
        m_application.captureCurrentSceneState();
        m_guestOwnGame = m_session.buildSaveData();
        m_guestOwnSavePath = m_session.currentSavePath();

        // It may be written to a file while the session lasts (writeGuestOwnGame), as a save is.
        if (m_guestOwnGame)
        {
            m_guestOwnGame->requiredContentPackages = collectRequiredContentPackages(
                *m_guestOwnGame,
                m_application.m_gameDataLoader.getItemTable(),
                m_application.m_gameDataLoader.getHouseTable(),
                m_application.m_gameDataLoader.getLoadedContentPackageSchemas());
        }
    }

    m_guestMapLoaded = false;
    m_guestHasPartyState = false;
    m_guestActorPoses.clear();
    m_mapRevision = mapRevision;
    m_session.setCoopSession(true);
    m_session.setCoopRole(GameSession::CoopRole::Guest);

    if (!m_application.loadSaveData(*worldState, true, nullptr))
    {
        guestReturnToOwnGame(Engine::tr("The host's map could not be loaded"));
        return;
    }

    // This game's party plays in the campaign the host's news is put into.
    m_session.bindLoadedPartyToCampaign();

    // The host's state of the map was laid out for the host's copy of it: with another copy here, this game would
    // show another map than the host plays (devdocs/SAVED_MAP_STATE_IDENTITY.md).
    if (m_application.lastMapLoadResetState())
    {
        guestReturnToOwnGame(Engine::tr("This game's copy of the host's map is not the host's"));
        return;
    }

    guestPlaceParty(body);
    m_guestBodyOrderSerial = bodyOrderSerial;

    // The character here is a mirror of the one the host keeps, and what its player does that the host has to do
    // goes to the host.
    if (Party *pParty = m_session.partyOfPlayer(LocalPlayer))
    {
        pParty->setMirror(true);
    }

    m_session.playerCommands().setRemote(this);

    if (m_session.partyState())
    {
        m_session.partyState()->setMirror(true);
    }

    m_guestMapLoaded = true;
    m_guestPositionSeconds = 0.0f;

    // The world is the host's, and so are its difficulty and progression while this game is in it: said once.
    if (const std::string hostRules = coopRulesText(m_session.ruleset());
        !m_guestOwnRulesText.empty() && hostRules != m_guestOwnRulesText)
    {
        m_session.gameplayScreenRuntime().setStatusBarEvent(
            Engine::tr("You play by the host's rules here: {rules}", {{"rules", hostRules}}), 8.0f);
    }

    m_guestOwnRulesText.clear();
    // What the host said of the whole game while its world was on the way is newer than that world.
    const std::unordered_map<uint8_t, std::vector<uint8_t>> heldNews = std::move(m_guestHeldGameNews);
    m_guestHeldGameNews.clear();

    for (const auto &[kind, news] : heldNews)
    {
        guestHandleMessage(Coop::ChannelControl, news);
    }

    Engine::ByteWriter ready = beginMessage(Coop::Message::MapReady);
    ready.u16(m_mapRevision);
    send(m_guestHostPeer, Coop::ChannelControl, Engine::NetDelivery::Reliable, ready);
}

void CoopSession::guestHandlePlayers(Engine::ByteReader &reader)
{
    const size_t count = reader.u8();
    std::vector<OtherPlayer> players;

    for (size_t index = 0; index < count && reader.ok(); ++index)
    {
        OtherPlayer player;
        player.id = reader.u8();
        player.name = reader.text(Coop::MaxNameLength);
        player.className = reader.text(Coop::MaxNameLength);
        player.raceId = reader.u8();
        player.sexId = reader.u8();
        player.gearTier = reader.u8();
        player.avatarMember = reader.u8();
        player.portraitPictureId = reader.u32();
        player.portraitTextureName = reader.text(Coop::MaxNameLength);
        player.level = reader.u32();
        player.health = reader.i32();
        player.maxHealth = reader.i32();
        player.spellPoints = reader.i32();
        player.maxSpellPoints = reader.i32();
        player.condition = reader.u8();
        player.down = reader.boolean();
        player.loadingMap = reader.boolean();
        player.away = reader.boolean();
        const size_t mateCount = std::min<size_t>(reader.u8(), Coop::MaxPartyMates);

        for (size_t mate = 0; mate < mateCount && reader.ok(); ++mate)
        {
            OtherPlayer::Mate read;
            read.portraitPictureId = reader.u32();
            read.portraitTextureName = reader.text(Coop::MaxNameLength);
            read.health = reader.i32();
            read.maxHealth = reader.i32();
            read.condition = reader.u8();
            player.mates.push_back(std::move(read));
        }

        if (player.id == m_guestOwnPlayer)
        {
            continue;
        }

        // Where it stands comes with the bodies; what is known of it stays.
        for (const OtherPlayer &known : m_otherPlayers)
        {
            if (known.id == player.id)
            {
                player.body = known.body;
                player.speed = known.speed;
                player.action = known.action;
            }
        }

        players.push_back(std::move(player));
    }

    if (reader.ok())
    {
        m_otherPlayers = std::move(players);
    }
}

void CoopSession::guestHandleBodies(Engine::ByteReader &reader)
{
    const uint16_t mapRevision = reader.u16();
    const float gameMinutes = reader.f32();
    const size_t count = reader.u8();

    if (!reader.ok() || mapRevision != m_mapRevision || !m_guestMapLoaded)
    {
        return;
    }

    if (IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();
        pWorldRuntime != nullptr && std::isfinite(gameMinutes))
    {
        pWorldRuntime->setReplicaGameMinutes(gameMinutes);
    }

    for (size_t index = 0; index < count && reader.ok(); ++index)
    {
        const PlayerId id = reader.u8();
        const GameplayPlayerBody body = readBody(reader);
        const PlayerAction action = readAction(reader);

        if (!reader.ok() || !finiteBody(body))
        {
            return;
        }

        for (OtherPlayer &player : m_otherPlayers)
        {
            if (player.id == id)
            {
                const float deltaX = body.x - player.body.x;
                const float deltaY = body.y - player.body.y;
                player.speed = std::sqrt(deltaX * deltaX + deltaY * deltaY) / StreamIntervalSeconds;
                player.body = body;
                player.action = action;
            }
        }
    }
}

void CoopSession::guestHandleActorRecords(Engine::ByteReader &reader)
{
    const uint16_t mapRevision = reader.u16();
    const size_t count = reader.u16();
    IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();

    if (!reader.ok() || mapRevision != m_mapRevision || !m_guestMapLoaded || pWorldRuntime == nullptr)
    {
        return;
    }

    for (size_t index = 0; index < count; ++index)
    {
        const size_t actorIndex = reader.u16();
        const std::vector<uint8_t> record = reader.block(Coop::MaxBlockBytes);

        if (!reader.ok())
        {
            return;
        }

        pWorldRuntime->applyReplicaActor(actorIndex, record);

        // The record brought the monster's state of its moment; its last pose is newer.
        if (actorIndex < m_guestActorPoses.size() && m_guestActorPoses[actorIndex])
        {
            pWorldRuntime->applyReplicaActorPose(*m_guestActorPoses[actorIndex]);
        }
    }
}

void CoopSession::guestHandleActorPoses(Engine::ByteReader &reader)
{
    const uint16_t mapRevision = reader.u16();
    const float gameMinutes = reader.f32();
    const size_t count = reader.u8();
    IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();

    if (!reader.ok() || mapRevision != m_mapRevision || !m_guestMapLoaded || pWorldRuntime == nullptr)
    {
        return;
    }

    if (std::isfinite(gameMinutes))
    {
        pWorldRuntime->setReplicaGameMinutes(gameMinutes);
    }

    for (size_t index = 0; index < count; ++index)
    {
        const ReplicaActorPose pose = readPose(reader);

        if (!reader.ok() || !finitePose(pose))
        {
            return;
        }

        if (pose.actorIndex >= pWorldRuntime->mapActorCount())
        {
            continue;
        }

        if (m_guestActorPoses.size() <= pose.actorIndex)
        {
            m_guestActorPoses.resize(size_t(pose.actorIndex) + 1);
        }

        m_guestActorPoses[pose.actorIndex] = pose;
        pWorldRuntime->applyReplicaActorPose(pose);
    }
}

void CoopSession::guestHandleProjectiles(Engine::ByteReader &reader)
{
    const uint16_t mapRevision = reader.u16();
    const size_t eventCount = reader.u16();

    if (!reader.ok() || mapRevision != m_mapRevision || !m_guestMapLoaded)
    {
        return;
    }

    GameplayProjectileService &service = m_session.gameplayProjectileService();

    for (size_t index = 0; index < eventCount && reader.ok(); ++index)
    {
        const uint8_t kind = reader.u8();

        if (kind == ProjectileEventSpawn)
        {
            GameplayProjectileService::ProjectileState projectile;

            if (!SaveSections::decode(reader.block(Coop::MaxBlockBytes), projectile))
            {
                return;
            }

            const auto known = std::find_if(service.projectiles().begin(), service.projectiles().end(),
                [&projectile](const GameplayProjectileService::ProjectileState &other)
                {
                    return other.projectileId == projectile.projectileId;
                });

            if (known == service.projectiles().end())
            {
                service.projectiles().push_back(std::move(projectile));
            }
        }
        else if (kind == ProjectileEventEnd)
        {
            const uint32_t projectileId = reader.u32();
            GameplayWorldPoint point;
            point.x = reader.f32();
            point.y = reader.f32();
            point.z = reader.f32();

            if (!reader.ok() || !std::isfinite(point.x) || !std::isfinite(point.y) || !std::isfinite(point.z))
            {
                return;
            }

            for (GameplayProjectileService::ProjectileState &projectile : service.projectiles())
            {
                if (projectile.projectileId == projectileId)
                {
                    service.expireProjectile(projectile, point);
                }
            }
        }
        else if (kind == ProjectileEventImpact)
        {
            GameplayProjectileService::ProjectileImpactState impact;

            if (!SaveSections::decode(reader.block(Coop::MaxBlockBytes), impact))
            {
                return;
            }

            service.projectileImpacts().push_back(std::move(impact));
        }
        else
        {
            return;
        }
    }

    service.eraseExpiredProjectiles();
}

void CoopSession::guestHandleProjectilePoses(Engine::ByteReader &reader)
{
    const uint16_t mapRevision = reader.u16();
    const size_t poseCount = reader.u16();

    if (!reader.ok() || mapRevision != m_mapRevision || !m_guestMapLoaded)
    {
        return;
    }

    GameplayProjectileService &service = m_session.gameplayProjectileService();

    for (size_t index = 0; index < poseCount; ++index)
    {
        const uint32_t projectileId = reader.u32();
        const float x = reader.f32();
        const float y = reader.f32();
        const float z = reader.f32();
        const float velocityX = reader.f32();
        const float velocityY = reader.f32();
        const float velocityZ = reader.f32();

        if (!reader.ok() || !std::isfinite(x) || !std::isfinite(y) || !std::isfinite(z) || !std::isfinite(velocityX)
            || !std::isfinite(velocityY) || !std::isfinite(velocityZ))
        {
            return;
        }

        for (GameplayProjectileService::ProjectileState &projectile : service.projectiles())
        {
            if (projectile.projectileId == projectileId)
            {
                projectile.x = x;
                projectile.y = y;
                projectile.z = z;
                projectile.velocityX = velocityX;
                projectile.velocityY = velocityY;
                projectile.velocityZ = velocityZ;
            }
        }
    }
}

void CoopSession::houseStockAction(HouseStockAction action, HouseStockMode stockMode, size_t slotIndex)
{
    Engine::ByteWriter payload;
    payload.u8(uint8_t(action));
    payload.u8(uint8_t(stockMode));
    payload.u32(uint32_t(std::min<size_t>(slotIndex, UINT32_MAX)));
    guestSendCommand(Coop::Command::House, payload);
}

void CoopSession::guestHandleHouseScreens(Engine::ByteReader &reader)
{
    const bool stockOpen = reader.boolean();
    const uint32_t stockHouseId = reader.u32();
    const uint8_t stockMode = reader.u8();
    const uint32_t spellbookShelf = reader.u32();
    const bool serviceOpen = reader.boolean();
    const uint8_t serviceMode = reader.u8();
    const uint32_t serviceHouseId = reader.u32();
    const uint8_t bankInputMode = reader.u8();
    const uint32_t bankHouseId = reader.u32();

    if (!reader.ok() || !m_guestMapLoaded || stockMode > uint8_t(GameplayUiController::HouseShopMode::BuySpellbooks)
        || bankInputMode > uint8_t(GameplayUiController::HouseBankInputMode::Withdraw)
        || (serviceOpen && !isShopServiceMode(GameplayUiController::InventoryNestedOverlayMode(serviceMode))))
    {
        return;
    }

    GameplayUiController &ui = m_session.gameplayUiController();
    m_guestHostStockScreen = stockOpen;
    m_guestHostServiceScreen = serviceOpen;

    // The bank's question for an amount opens and closes here as the host has it; what is typed is this game's.
    GameplayUiController::HouseBankState &bank = ui.houseBankState();

    if (bank.inputMode != GameplayUiController::HouseBankInputMode(bankInputMode))
    {
        const bool wasAsking = bank.inputActive();
        bank.inputMode = GameplayUiController::HouseBankInputMode(bankInputMode);
        bank.houseId = bankHouseId != 0 ? bankHouseId : bank.houseId;
        bank.inputText.clear();

        // The host is done with the amount: back to the bank's own choices, as after an amount typed alone.
        if (wasAsking && !bank.inputActive())
        {
            m_session.gameplayScreenRuntime().returnToHouseBankMainDialogShared();
        }
    }

    if (stockOpen)
    {
        ui.openHouseShopOverlay(stockHouseId, GameplayUiController::HouseShopMode(stockMode), spellbookShelf);
    }
    else if (ui.houseShopOverlay().active)
    {
        ui.closeHouseShopOverlay();
    }

    if (serviceOpen)
    {
        ui.openInventoryNestedOverlay(GameplayUiController::InventoryNestedOverlayMode(serviceMode), serviceHouseId);
    }
    else if (ui.inventoryNestedOverlay().active && isShopServiceMode(ui.inventoryNestedOverlay().mode))
    {
        ui.closeInventoryNestedOverlay();
    }
}

void CoopSession::guestSendHouseScreenChanges()
{
    const GameplayUiController &ui = m_session.gameplayUiController();

    if (m_guestHostStockScreen && !ui.houseShopOverlay().active)
    {
        m_guestHostStockScreen = false;
        Engine::ByteWriter payload;
        payload.u8(HouseOperationCloseStock);
        payload.u8(0);
        payload.u32(0);
        guestSendCommand(Coop::Command::House, payload);
    }

    if (m_guestHostServiceScreen
        && !(ui.inventoryNestedOverlay().active && isShopServiceMode(ui.inventoryNestedOverlay().mode)))
    {
        m_guestHostServiceScreen = false;
        Engine::ByteWriter payload;
        payload.u8(HouseOperationCloseService);
        payload.u8(0);
        payload.u32(0);
        guestSendCommand(Coop::Command::House, payload);
    }
}

void CoopSession::guestHandleSounds(Engine::ByteReader &reader)
{
    const uint16_t mapRevision = reader.u16();
    std::vector<EventRuntimeState::PendingSound> sounds;
    const bool read = CoopCodec::readSounds(reader, sounds);
    IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();
    EventRuntimeState *pEventState = pWorldRuntime != nullptr ? pWorldRuntime->eventRuntimeState() : nullptr;

    if (!read || mapRevision != m_mapRevision || !m_guestMapLoaded || pEventState == nullptr)
    {
        return;
    }

    pEventState->pendingSounds.insert(pEventState->pendingSounds.end(), sounds.begin(), sounds.end());
}

void CoopSession::guestHandlePartyAudio(Engine::ByteReader &reader)
{
    const size_t count = reader.u8();
    std::vector<Party::PendingAudioRequest> requests;

    for (size_t index = 0; index < count && reader.ok(); ++index)
    {
        Party::PendingAudioRequest request;
        const uint8_t kind = reader.u8();
        request.soundId = SoundId(reader.u32());
        const uint8_t scope = reader.u8();
        request.speechId = SpeechId(reader.u32());
        request.memberIndex = reader.u32();

        if (kind > uint8_t(Party::PendingAudioRequest::Kind::Speech) || scope > uint8_t(SoundScope::World))
        {
            return;
        }

        request.scope = SoundScope(scope);

        request.kind = Party::PendingAudioRequest::Kind(kind);
        requests.push_back(request);
    }

    Party *pParty = m_session.partyOfPlayer(LocalPlayer);

    if (reader.ok() && m_guestMapLoaded && pParty != nullptr)
    {
        pParty->addPendingAudioRequests(requests);
    }
}

void CoopSession::guestAdvanceProjectiles(float deltaSeconds)
{
    for (GameplayProjectileService::ProjectileState &projectile : m_session.gameplayProjectileService().projectiles())
    {
        if (projectile.isExpired || projectile.isSettled)
        {
            continue;
        }

        projectile.x += projectile.velocityX * deltaSeconds;
        projectile.y += projectile.velocityY * deltaSeconds;
        projectile.z += projectile.velocityZ * deltaSeconds;
        projectile.lifetimeTickAccumulator += deltaSeconds * ProjectileTicksPerSecond;
        const uint32_t ticks = uint32_t(projectile.lifetimeTickAccumulator);
        projectile.timeSinceCreatedTicks += ticks;
        projectile.lifetimeTickAccumulator -= float(ticks);
    }
}

void CoopSession::guestHandleMapSection(Engine::ByteReader &reader)
{
    const uint16_t mapRevision = reader.u16();
    const Coop::MapSection section = Coop::MapSection(reader.u8());
    const std::vector<uint8_t> bytes = reader.block(Coop::MaxBlockBytes);
    IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();

    if (!reader.ok() || mapRevision != m_mapRevision || !m_guestMapLoaded || pWorldRuntime == nullptr)
    {
        return;
    }

    EventRuntimeState *pEventState = pWorldRuntime->eventRuntimeState();

    switch (section)
    {
        case Coop::MapSection::EventState:
        {
            if (pEventState == nullptr)
            {
                return;
            }

            // Read over a copy of this game's state: what the host's state holds replaces it, and what a save does
            // not hold stays. This game's own conversation and requests, and its movers, are put back.
            EventRuntimeState next = *pEventState;

            if (!SaveSections::decode(bytes, next))
            {
                return;
            }

            keepTransientEventRuntimeState(next, *pEventState);
            next.mechanisms = pEventState->mechanisms;
            *pEventState = std::move(next);
            pWorldRuntime->applyEventRuntimeState(true);

            // Applying the event state touches the monsters too (who is hidden, who is hostile); the host's poses
            // say how they are.
            for (const std::optional<ReplicaActorPose> &pose : m_guestActorPoses)
            {
                if (pose)
                {
                    pWorldRuntime->applyReplicaActorPose(*pose);
                }
            }

            break;
        }

        case Coop::MapSection::Mechanisms:
        {
            std::unordered_map<uint32_t, RuntimeMechanismState> mechanisms;

            if (pEventState == nullptr || !SaveSections::decode(bytes, mechanisms))
            {
                return;
            }

            for (auto &[id, mechanism] : mechanisms)
            {
                // A spin goes on from this game's angle.
                if (const auto shown = pEventState->mechanisms.find(id);
                    shown != pEventState->mechanisms.end() && mechanism.spinOn && shown->second.spinOn)
                {
                    mechanism.spinDegrees = shown->second.spinDegrees;
                    mechanism.spinRate = shown->second.spinRate;
                }
            }

            pEventState->mechanisms = std::move(mechanisms);
            break;
        }

        case Coop::MapSection::WorldItems:
            pWorldRuntime->applyReplicaWorldItems(bytes);
            break;
    }
}

uint32_t CoopSession::guestSendCommand(
    Coop::Command command, const Engine::ByteWriter &payload, bool withCharacterChange)
{
    ++m_guestCommandSerial;
    Engine::ByteWriter message = beginMessage(Coop::Message::Command);
    message.u32(m_guestCommandSerial);
    message.u16(m_mapRevision);
    message.u8(uint8_t(command));
    message.u32(withCharacterChange ? m_guestFramePutSerial : 0);
    message.raw(payload.bytes());
    send(m_guestHostPeer, Coop::ChannelControl, Engine::NetDelivery::Reliable, message);
    return m_guestCommandSerial;
}

void CoopSession::guestSendWorldRequests()
{
    IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();

    if (pWorldRuntime == nullptr)
    {
        return;
    }

    for (const std::vector<uint8_t> &call : pWorldRuntime->takeReplicaWorldCalls())
    {
        Engine::ByteWriter payload;
        payload.block(call);
        guestSendCommand(Coop::Command::WorldCall, payload, ReplicaWorldCalls::goesWithCharacterChange(call));
    }

    for (const ReplicaPositionTrigger &trigger : pWorldRuntime->takeReplicaPositionTriggers())
    {
        Engine::ByteWriter payload;
        payload.u8(uint8_t(trigger.kind));
        payload.u32(trigger.first);
        payload.u32(trigger.second);
        guestSendCommand(Coop::Command::PositionTrigger, payload);
    }
}

std::vector<uint8_t> CoopSession::guestCharacterBytes() const
{
    const Party *pParty = m_session.partyOfPlayer(LocalPlayer);

    if (pParty == nullptr)
    {
        return {};
    }

    const GameplayUiController::HeldInventoryItemState &held = m_session.gameplayUiController().heldInventoryItem();
    Engine::ByteWriter bytes;
    writeHeldItem(bytes, held.active ? std::optional<InventoryItem>(held.item) : std::nullopt);
    bytes.block(SaveSections::encodeCharacters(characterForWire(pParty->characterSnapshot())));
    return bytes.bytes();
}

void CoopSession::guestSendCharacterPut()
{
    std::vector<uint8_t> character = guestCharacterBytes();

    if (character.empty() || character == m_guestCharacterBytes)
    {
        return;
    }

    ++m_guestPutSerial;
    m_guestFramePutSerial = m_guestPutSerial;
    Engine::ByteWriter message = beginMessage(Coop::Message::CharacterPut);
    message.u32(m_guestPutSerial);
    message.u32(m_guestPartyRevision);
    message.u32(m_guestCommandEpoch);
    message.raw(character);
    send(m_guestHostPeer, Coop::ChannelControl, Engine::NetDelivery::Reliable, message);
    m_guestCharacterBytes = std::move(character);
}

void CoopSession::guestHandlePartyState(Engine::ByteReader &reader)
{
    const uint32_t revision = reader.u32();
    const uint32_t commandEpoch = reader.u32();
    const uint32_t ackedPutSerial = reader.u32();
    std::optional<InventoryItem> heldItem;
    Party::Snapshot character;

    if (!readHeldItem(reader, heldItem)
        || !SaveSections::decodeCharacters(reader.block(Coop::MaxBlockBytes), character) || !reader.ok()
        || character.members.empty() || character.members.size() > Party::MaxMembers)
    {
        return;
    }

    // A state from before the host saw this game's last change would undo it for a moment: the one that follows
    // holds it.
    if (!m_guestMapLoaded || ackedPutSerial != m_guestPutSerial)
    {
        return;
    }

    IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();
    Party *pParty = m_session.partyOfPlayer(LocalPlayer);

    if (pWorldRuntime == nullptr || pParty == nullptr)
    {
        return;
    }

    pParty->applyMirror(character);
    GameplayUiController::HeldInventoryItemState &held = m_session.gameplayUiController().heldInventoryItem();

    if (heldItem && (!held.active || !(held.item == *heldItem)))
    {
        held = {};
        held.active = true;
        held.item = *heldItem;
        pParty->setHeldItemForQueries(*heldItem);
    }
    else if (!heldItem && held.active)
    {
        held = {};
        pParty->clearHeldItemForQueries();
    }

    // Fly, Water Walk and Feather Fall follow the buffs the host gave or ended.
    pWorldRuntime->syncSpellMovementStatesFromPartyBuffs();
    m_guestHasPartyState = true;
    guestNotePartyState(revision, commandEpoch);
}

void CoopSession::guestNotePartyState(uint32_t revision, uint32_t commandEpoch)
{
    m_guestPartyRevision = revision;
    m_guestCommandEpoch = commandEpoch;
    m_guestCharacterBytes = guestCharacterBytes();
}

void CoopSession::guestHandlePartyVitals(Engine::ByteReader &reader)
{
    const uint32_t revision = reader.u32();
    const uint32_t commandEpoch = reader.u32();
    const uint32_t ackedPutSerial = reader.u32();
    const CharacterVitals vitals = readVitals(reader);
    Party *pParty = m_session.partyOfPlayer(LocalPlayer);

    // As for a whole state: not before the host saw this game's last change.
    if (!reader.ok() || !m_guestMapLoaded || !m_guestHasPartyState || ackedPutSerial != m_guestPutSerial
        || pParty == nullptr)
    {
        return;
    }

    Party::Snapshot character = characterForWire(pParty->snapshot());

    if (!applyCharacterVitals(character, vitals))
    {
        return;
    }

    pParty->applyMirror(character);
    // The hit points came alone: a member they struck down is down here at once, not only when the whole
    // character arrives (until then it walked about with no hit points, 2026-11-21).
    pParty->refreshIncapacitatedConditions();
    guestNotePartyState(revision, commandEpoch);
}

void CoopSession::castSpell(const PartySpellCastRequest &request, std::optional<PlayerId> targetPlayer)
{
    Engine::ByteWriter payload;
    CoopCodec::writeSpellCastRequest(payload, request, targetPlayer);
    guestSendCommand(Coop::Command::CastSpell, payload);
}

void CoopSession::activateWorldHit(const GameplayWorldHit &hit)
{
    Engine::ByteWriter payload;
    CoopCodec::writeWorldHit(payload, hit);
    guestSendCommand(Coop::Command::ActivateWorldHit, payload);
}

void CoopSession::setHostPassword(const std::string &password)
{
    m_hostPassword = password.substr(0, Coop::MaxPasswordLength);
}

void CoopSession::setJoinPassword(const std::string &password)
{
    m_joinPassword = password.substr(0, Coop::MaxPasswordLength);
}

void CoopSession::hostPresentation(uint8_t kind, const std::string &name)
{
    if (m_role != Role::Host)
    {
        return;
    }

    Engine::ByteWriter message = beginMessage(Coop::Message::Presentation);
    message.u16(m_mapRevision);
    message.u8(kind);
    message.text(name, Coop::MaxNameLength);

    for (const HostPeer &peer : m_hostPeers)
    {
        if (peer.player != LocalPlayer && peer.readyMapRevision == m_mapRevision)
        {
            send(peer.peer, Coop::ChannelControl, Engine::NetDelivery::Reliable, message);
        }
    }
}

bool CoopSession::askHostToSave()
{
    if (m_role != Role::Guest || !m_guestMapLoaded || m_guestSinceAskedSaveSeconds < AskSaveEverySeconds)
    {
        return false;
    }

    m_guestSinceAskedSaveSeconds = 0.0f;
    send(m_guestHostPeer, Coop::ChannelControl, Engine::NetDelivery::Reliable, beginMessage(Coop::Message::AskSave));
    return true;
}

void CoopSession::hostSaved()
{
    if (m_role != Role::Host)
    {
        return;
    }

    sendToAll(Coop::ChannelControl, Engine::NetDelivery::Reliable, beginMessage(Coop::Message::HostSaved));

    // And the world as it now is, for each guest to keep: whatever ends the session, it has the host's last save.
    for (HostPeer &peer : m_hostPeers)
    {
        hostSendWorldCopy(peer, WorldCopyKept);
    }
}

void CoopSession::hostSendWorldCopy(HostPeer &peer, uint8_t kind)
{
    // The whole world, with that player's party in the party's place.
    std::optional<GameSaveData> world =
        peer.player != LocalPlayer ? m_application.buildCoopWorldState(peer.player, true) : std::nullopt;

    if (world)
    {
        Engine::ByteWriter copy = beginMessage(Coop::Message::WorldCopy);
        copy.u8(kind);
        copy.block(SaveSections::encodeGame(*world));
        send(peer.peer, Coop::ChannelWorld, Engine::NetDelivery::Reliable, copy);
    }
}

bool CoopSession::hostStopping() const
{
    return m_role == Role::Host && m_hostStopSeconds > 0.0f;
}

void CoopSession::houseBankAmount(uint32_t amount)
{
    Engine::ByteWriter payload;
    payload.u8(HouseOperationBankAmount);
    payload.u8(0);
    payload.u32(amount);
    guestSendCommand(Coop::Command::House, payload);
}

void CoopSession::proposeTravel(const EventRuntimeState::PendingMapMove &move)
{
    // The move travels as it does in the host's own proposal to its guests.
    EventRuntimeState carrier;
    carrier.pendingMapMove = move;
    Engine::ByteWriter payload;
    payload.block(SaveSections::encode(carrier));
    guestSendCommand(Coop::Command::ProposeTravel, payload);
}

void CoopSession::takeWorldItem(uint32_t itemKey)
{
    Engine::ByteWriter payload;
    payload.u32(itemKey);
    guestSendCommand(Coop::Command::TakeWorldItem, payload);
}

void CoopSession::dialogueAction(size_t selectionIndex, const EventDialogAction &action, bool overrideAction)
{
    Engine::ByteWriter payload;
    payload.u8(overrideAction ? DialogueOperationOverride : DialogueOperationSelect);
    payload.u32(uint32_t(selectionIndex));
    payload.u8(uint8_t(action.kind));
    payload.u32(action.id);
    payload.u32(action.secondaryId);
    payload.u32(uint32_t(action.memberIndex));
    payload.text(action.argument, Coop::MaxNameLength);
    guestSendCommand(Coop::Command::Dialogue, payload);
}

void CoopSession::dialogueClose()
{
    Engine::ByteWriter payload;
    payload.u8(DialogueOperationClose);
    payload.u32(0);
    payload.u8(0);
    payload.u32(0);
    payload.u32(0);
    payload.u32(0);
    payload.text(std::string(), Coop::MaxNameLength);
    guestSendCommand(Coop::Command::Dialogue, payload);
}

void CoopSession::guestHandleOutcome(Engine::ByteReader &reader)
{
    const uint16_t mapRevision = reader.u16();
    const bool hasDialogue = reader.boolean();
    const bool dialogueClosed = reader.boolean();
    const size_t previousMessageCount = reader.u32();
    const bool allowNpcFallbackContent = reader.boolean();
    EventRuntimeState carrier;
    const bool carrierRead = SaveSections::decode(reader.block(Coop::MaxBlockBytes), carrier);
    std::vector<EventRuntimeState::PendingSound> sounds;
    const bool soundsRead = CoopCodec::readSounds(reader, sounds);
    const size_t statusCount = reader.u8();
    std::vector<std::pair<std::string, float>> statusTexts;

    for (size_t index = 0; index < statusCount && reader.ok(); ++index)
    {
        std::string text = reader.text(1024);
        const float seconds = reader.f32();
        statusTexts.emplace_back(std::move(text), std::isfinite(seconds) ? seconds : 0.0f);
    }

    IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();
    EventRuntimeState *pEventState = pWorldRuntime != nullptr ? pWorldRuntime->eventRuntimeState() : nullptr;

    if (!reader.ok() || !carrierRead || !soundsRead || mapRevision != m_mapRevision || !m_guestMapLoaded
        || pEventState == nullptr)
    {
        return;
    }

    GameplayScreenRuntime &screenRuntime = m_session.gameplayScreenRuntime();

    for (const std::pair<std::string, float> &status : statusTexts)
    {
        screenRuntime.setStatusBarEvent(status.first, status.second > 0.0f ? status.second : 2.0f);
    }

    pEventState->pendingSounds.insert(pEventState->pendingSounds.end(), sounds.begin(), sounds.end());

    if (dialogueClosed && screenRuntime.activeEventDialog().isActive)
    {
        screenRuntime.closeActiveEventDialog();
    }

    if (hasDialogue && carrier.pendingDialogueContext)
    {
        // The conversation as the host has it, presented here the way the host presented it for this player.
        pEventState->dialogueState = std::move(carrier.dialogueState);
        pEventState->messages = std::move(carrier.messages);
        pEventState->pendingDialogueContext = std::move(carrier.pendingDialogueContext);
        screenRuntime.presentPendingEventDialog(previousMessageCount, allowNpcFallbackContent);
    }
}

std::vector<uint8_t> CoopSession::guestChestBytes() const
{
    const IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();
    const GameplayChestViewState *pChestView = pWorldRuntime != nullptr ? pWorldRuntime->activeChestView() : nullptr;
    return pChestView != nullptr ? SaveSections::encode(*pChestView) : std::vector<uint8_t>();
}

std::vector<uint8_t> CoopSession::guestCorpseBytes() const
{
    const IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();
    const GameplayCorpseViewState *pCorpseView =
        pWorldRuntime != nullptr ? pWorldRuntime->activeCorpseView() : nullptr;
    return pCorpseView != nullptr ? SaveSections::encode(*pCorpseView) : std::vector<uint8_t>();
}

void CoopSession::guestHandleLootViews(Engine::ByteReader &reader)
{
    const uint16_t mapRevision = reader.u16();
    std::optional<GameplayChestViewState> chestView;
    std::optional<GameplayCorpseViewState> corpseView;

    if (reader.boolean())
    {
        chestView.emplace();

        if (!SaveSections::decode(reader.block(Coop::MaxBlockBytes), *chestView))
        {
            return;
        }
    }

    if (reader.boolean())
    {
        corpseView.emplace();

        if (!SaveSections::decode(reader.block(Coop::MaxBlockBytes), *corpseView))
        {
            return;
        }
    }

    IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();

    if (!reader.ok() || mapRevision != m_mapRevision || !m_guestMapLoaded || pWorldRuntime == nullptr)
    {
        return;
    }

    pWorldRuntime->setReplicaLootViews(std::move(chestView), std::move(corpseView));
    m_guestChestBytes = guestChestBytes();
    m_guestCorpseBytes = guestCorpseBytes();
}

void CoopSession::travelVote(bool accept)
{
    Engine::ByteWriter payload;
    payload.boolean(accept);
    guestSendCommand(Coop::Command::TravelVote, payload);
}

void CoopSession::returnDowned()
{
    guestSendCommand(Coop::Command::ReturnDowned, Engine::ByteWriter());
}

void CoopSession::guestHandleTravelProposal(Engine::ByteReader &reader)
{
    std::optional<GameSession::TravelProposal> travel;

    if (reader.boolean())
    {
        travel.emplace();
        travel->serial = reader.u32();
        travel->proposer = reader.u8();
        travel->open = reader.boolean();
        const size_t acceptedCount = reader.u8();

        for (size_t index = 0; index < acceptedCount && reader.ok(); ++index)
        {
            travel->accepted.push_back(reader.u8());
        }

        EventRuntimeState carrier;

        if (!SaveSections::decode(reader.block(Coop::MaxBlockBytes), carrier) || !carrier.pendingMapMove)
        {
            return;
        }

        travel->move = std::move(*carrier.pendingMapMove);
        TravelCost cost;
        cost.fareGold = reader.i32();
        cost.waitDays = reader.i32();
        cost.waitFood = reader.i32();
        cost.travelDays = reader.i32();
        cost.travelFood = reader.i32();
        travel->move.unpaidCost = cost.any() ? std::optional<TravelCost>(cost) : std::nullopt;
    }

    std::optional<GameSession::RestProposal> rest;

    if (reader.boolean())
    {
        rest.emplace();
        rest->serial = reader.u32();
        rest->proposer = reader.u8();
        rest->heal = reader.boolean();
        rest->minutes = reader.f32();
        const size_t acceptedCount = reader.u8();

        for (size_t index = 0; index < acceptedCount && reader.ok(); ++index)
        {
            rest->accepted.push_back(reader.u8());
        }
    }

    if (!reader.ok())
    {
        return;
    }

    m_session.setReplicaTravelProposal(std::move(travel));
    m_session.setReplicaRestProposal(std::move(rest));
}

void CoopSession::proposeRest(bool heal, float minutes)
{
    Engine::ByteWriter payload;
    payload.u8(RestOperationPropose);
    payload.boolean(heal);
    payload.f32(minutes);
    guestSendCommand(Coop::Command::Rest, payload);
}

void CoopSession::restVote(bool accept)
{
    Engine::ByteWriter payload;
    payload.u8(RestOperationVote);
    payload.boolean(accept);
    payload.f32(0.0f);
    guestSendCommand(Coop::Command::Rest, payload);
}

void CoopSession::guestHandleRulesState(Engine::ByteReader &reader)
{
    MawGameState state;
    MawRules *pRules = m_session.mawRules();

    if (!SaveSections::decode(reader.block(Coop::MaxBlockBytes), state) || !reader.ok() || pRules == nullptr)
    {
        return;
    }

    pRules->setState(state);
}

void CoopSession::guestHandleLentAuras(Engine::ByteReader &reader)
{
    const size_t count = reader.u8();
    std::vector<LentAura> auras;

    for (size_t index = 0; index < count && index < MaxLentAuras && reader.ok(); ++index)
    {
        LentAura aura;
        aura.spellId = reader.u32();
        aura.skill = reader.f32();
        aura.mastery = reader.u8();
        aura.level = reader.f32();

        if (std::isfinite(aura.skill) && std::isfinite(aura.level))
        {
            auras.push_back(aura);
        }
    }

    Party *pParty = m_session.partyOfPlayer(LocalPlayer);

    if (reader.ok() && count <= MaxLentAuras && pParty != nullptr)
    {
        pParty->rules().spells.setLentAuras(auras);
    }
}

void CoopSession::guestHandleCampaign(Engine::ByteReader &reader)
{
    CampaignState::Snapshot campaign;

    if (!SaveSections::decodeCampaign(reader.block(Coop::MaxBlockBytes), campaign) || !reader.ok())
    {
        return;
    }

    // The host's quests, journal and shop stock are this game's while it is a guest.
    m_guestHostQuestPouch = campaign.questPouch;
    m_session.campaign().restoreSnapshot(campaign);
}

void CoopSession::guestSendQuestPouchAdditions()
{
    // A quest item this game's player took (out of a chest or a corpse, which a guest's game loots itself) went into
    // this game's copy of the world's quest pouch. The host is told of each, so that the world has it.
    const std::vector<InventoryItem> &pouch = m_session.campaign().questPouch();

    if (pouch.size() <= m_guestHostQuestPouch.size())
    {
        return;
    }

    std::vector<InventoryItem> known = m_guestHostQuestPouch;

    for (const InventoryItem &item : pouch)
    {
        const auto found = std::find(known.begin(), known.end(), item);

        if (found != known.end())
        {
            known.erase(found);
            continue;
        }

        Engine::ByteWriter payload;
        payload.block(SaveSections::encode(item));
        guestSendCommand(Coop::Command::QuestItem, payload);
        m_guestHostQuestPouch.push_back(item);
    }
}

void CoopSession::guestSendLootChanges()
{
    std::vector<uint8_t> chest = guestChestBytes();
    std::vector<uint8_t> corpse = guestCorpseBytes();

    if (chest == m_guestChestBytes && corpse == m_guestCorpseBytes)
    {
        return;
    }

    // Closed here: the host closes its side, and both go.
    if ((chest.empty() && !m_guestChestBytes.empty()) || (corpse.empty() && !m_guestCorpseBytes.empty()))
    {
        Engine::ByteWriter payload;
        payload.u8(LootOperationClose);
        guestSendCommand(Coop::Command::Chest, payload);
    }
    else
    {
        if (chest != m_guestChestBytes)
        {
            Engine::ByteWriter payload;
            payload.u8(LootOperationPutChest);
            payload.block(chest);
            guestSendCommand(Coop::Command::Chest, payload, true);
        }

        if (corpse != m_guestCorpseBytes)
        {
            Engine::ByteWriter payload;
            payload.u8(LootOperationPutCorpse);
            payload.block(corpse);
            guestSendCommand(Coop::Command::Chest, payload, true);
        }
    }

    m_guestChestBytes = std::move(chest);
    m_guestCorpseBytes = std::move(corpse);
}

void CoopSession::guestHandleMoveOrder(Engine::ByteReader &reader)
{
    const uint16_t mapRevision = reader.u16();
    const uint32_t bodyOrderSerial = reader.u32();
    const GameplayPlayerBody body = readBody(reader);

    if (!reader.ok() || mapRevision != m_mapRevision || !m_guestMapLoaded || !finiteBody(body))
    {
        return;
    }

    guestPlaceParty(body);
    m_guestBodyOrderSerial = bodyOrderSerial;
}

void CoopSession::guestPlaceParty(const GameplayPlayerBody &body)
{
    IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();

    if (pWorldRuntime == nullptr)
    {
        return;
    }

    pWorldRuntime->teleportParty(body.x, body.y, body.footZ);

    if (m_session.currentSceneKind() == SceneKind::Outdoor)
    {
        m_application.m_outdoorGameView.setCameraAngles(
            body.yawRadians, m_application.m_outdoorGameView.cameraPitchRadians());
    }
    else
    {
        m_application.m_indoorRenderer.setCameraAngles(
            body.yawRadians, m_application.m_indoorRenderer.cameraPitchRadians());
    }
}

void CoopSession::guestSendPosition()
{
    const IGameplayWorldRuntime *pWorldRuntime = m_session.activeWorldRuntime();

    if (pWorldRuntime == nullptr)
    {
        return;
    }

    Engine::ByteWriter message = beginMessage(Coop::Message::Position);
    message.u16(m_mapRevision);
    message.u32(m_guestBodyOrderSerial);
    writeBody(message, GameplayPlayerBody{pWorldRuntime->partyX(), pWorldRuntime->partyY(),
        pWorldRuntime->partyFootZ(), pWorldRuntime->gameplayCameraYawRadians(),
        pWorldRuntime->partyIsFlyingForEventChecks()});
    writeAction(message, m_ownAction);
    send(m_guestHostPeer, Coop::ChannelPosition, Engine::NetDelivery::UnreliableNewest, message);
}

void CoopSession::guestReturnToOwnGame(const std::string &notice)
{
    // The save written below is the same file.
    waitForOwnGameWrite();

    // The character goes home as the session left it, into the world it came from.
    std::optional<GameSaveData> ownGame = std::move(m_guestOwnGame);
    const std::optional<std::filesystem::path> ownSavePath = std::move(m_guestOwnSavePath);
    m_guestOwnGame.reset();
    m_guestOwnSavePath.reset();

    if (m_guestCharacterFile)
    {
        // A character from a file goes back into its file, and the game in progress comes back as it was.
        std::string error;

        if (m_guestMapLoaded && !writeJoinCharacter(error))
        {
            std::cerr << "CoopSession: " << error << '\n';
        }
    }
    else if (ownGame && m_guestMapLoaded)
    {
        if (const Party *pParty = m_session.partyOfPlayer(LocalPlayer))
        {
            putCharacterIntoOwnGame(*ownGame, *pParty);
            // Into its Autosave as well, when it has one of its own: the game below comes back in memory only.
            std::string error;

            if (!ownGame->playthroughId.empty()
                && !saveGameDataToPath(autosavePath(ownGame->playthroughId), *ownGame, error))
            {
                std::cerr << "CoopSession: " << error << '\n';
            }
        }
    }

    close();
    m_lastNotice = notice;

    if (ownGame)
    {
        m_application.loadSaveData(*ownGame, true, nullptr);

        if (ownSavePath)
        {
            m_session.setCurrentSavePath(*ownSavePath);
        }

        // Its own world's quest items, kept aside for the session, are the character's to carry again where the
        // ruleset has no pouch for them (and the Party pouches setting is off).
        if (Party *pParty = m_session.partyOfPlayer(LocalPlayer))
        {
            pParty->sortPouchItems();
        }
    }

    if (!notice.empty())
    {
        m_session.gameplayScreenRuntime().setStatusBarEvent(notice, 6.0f);
    }
}
}
