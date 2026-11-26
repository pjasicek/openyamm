#pragma once

#include <cstdint>
#include <string_view>

namespace OpenYAMM::Game::Coop
{
// What two games of a co-op session say to each other (devdocs/plans/MULTIPLAYER_LISTEN_SERVER_ARCHITECTURE.md, "What
// travels over the network"). Every message starts with its Message byte; the fields follow one by one
// (Engine::ByteWriter). Larger pieces of state travel as blocks in the save's own encoding (SaveSections.h), which is
// why both games must be the same build: the admission compares ProtocolVersion and the save version.
constexpr uint32_t ProtocolVersion = 22;

// A message of PackFromBytes or more is sent packed when that makes it smaller: its kind's byte with PackedFlag set,
// then the rest of it packed (Engine::packBytes). The three messages of the admission are never packed, so that a
// game of another version is refused in words it can read.
constexpr uint8_t PackedFlag = 0x80;
constexpr size_t PackFromBytes = 256;
constexpr uint16_t DefaultPort = 27950;
// The lobby service's port (tools/lobby_server_main.cpp); its relay ports follow it.
constexpr uint16_t DefaultLobbyPort = 27910;
// The lobby every game asks unless its player names another or plays on the local network only (the Multiplayer
// screen). A name, so that the lobby can move to another machine without a new build.
constexpr std::string_view DefaultLobbyAddress = "oylobby.jasicek.net";
constexpr size_t MaxGuests = 3;
// A party's members after its first, as the players list names them.
constexpr size_t MaxPartyMates = 4;

// The transport's channels: order is kept within one, so a large state does not hold up play on another.
constexpr uint8_t ChannelControl = 0;  // Reliable: commands, their results, state that changed.
constexpr uint8_t ChannelStream = 1;   // Newest wins: where monsters, missiles and players are.
constexpr uint8_t ChannelWorld = 2;    // Reliable: a map's whole state, at joining and at every map change.
constexpr uint8_t ChannelPosition = 3; // Newest wins: where the sending guest stands.

enum class Message : uint8_t
{
    // A guest's game to the host's.
    Hello = 1,
    Position = 2,
    MapReady = 3,
    Command = 4,
    // What the guest's game did with its character (CoopCharacter.h).
    CharacterPut = 5,
    // The guest's player wants a copy of the host's whole world to keep (WorldCopy answers).
    WorldCopyRequest = 6,
    // A line the guest's player says to the others, and a place it points them at. The host passes both on.
    Say = 7,
    Point = 8,
    // The guest's player asks the host to save the game (a guest's own save key).
    AskSave = 9,
    // The guest's player leaves for its own game for now and wants its seat kept: the key it will name when it
    // comes back. The host answers SteppedOut, and the guest's game leaves then.
    StepOut = 10,
    // A test launcher's game (tools/coop_local): bring this guest to the host. A host carries it out only with its
    // own test commands on ([coop] test_commands).
    TestSync = 11,
    // Which member of the guest's party stands for its player in the others' games (its body, its face in their
    // players panel): the member's place in the party.
    Avatar = 12,

    // The host's game to a guest's.
    Welcome = 32,
    Refused = 33,
    WorldState = 34,
    Players = 35,
    Bodies = 36,
    ActorRecords = 37,
    ActorPoses = 38,
    MapSection = 39,
    // Missiles that appeared, missiles that ended and where, and the effects of their impacts.
    Projectiles = 40,
    PartyState = 41,
    CampaignState = 42,
    // What the host's game shows that every game should: a cinematic of the map (PresentationCinematic, its id)
    // or a movie (PresentationMovie, its name). Each guest's game plays it by its own settings.
    Presentation = 43,
    CommandResult = 44,
    // What the host did for the guest's player that its game has to show: a dialogue that opened or closed, status
    // lines, sounds.
    Outcome = 45,
    // The travel proposal that waits for the players' answers, or that none does.
    TravelVote = 46,
    RulesState = 47,
    // A character's hit points, spell points, recovery and buff times alone (CharacterVitals).
    PartyVitals = 48,
    // The host put the guest's party somewhere (a teleport, an arrival): its game moves it there.
    MoveOrder = 49,
    // The chest and the corpse the host has open for the guest's player.
    LootViews = 50,
    // Where the missiles in flight are.
    ProjectilePoses = 51,
    // Sounds of the world, for every guest to hear where they sound.
    Sounds = 52,
    // What the guest's own character says and sounds like (a hit taken, a find, a spell's end).
    PartyAudio = 53,
    // The shop screens the host keeps open for the guest: a stock to buy from, or the guest's own things to sell,
    // identify or repair.
    HouseScreens = 54,
    // The host's whole world as a save, with the asking guest's character in it: the guest's game keeps it as a save
    // of its own.
    WorldCopy = 55,
    // A line another player said, and a place another player points at.
    Chat = 56,
    Ping = 57,
    // The lying item the guest asked for (Command::TakeWorldItem), out of the host's world and now the guest's.
    TakenWorldItem = 58,
    // The host saved its game: a guest's game writes what its character has now (its file, or its own game).
    HostSaved = 59,
    // The host keeps the seat of the guest that asked to step out (Message::StepOut).
    SteppedOut = 60,
    // The travel everyone agreed to begins: the host loads the map now, and the guests' games say so until their
    // own load starts.
    TravelDeparting = 61,
    // The auras the other players' parties near this player's lend it now (LentAura; a ruleset with auras).
    LentAuras = 62,
};

// What a guest's player does that the host has to do (Message::Command). Each carries a number of its own, which the
// host's answer names where the guest's game waits for one.
enum class Command : uint8_t
{
    // What the guest's own game did to the map with a blow, a shot or a talent (ReplicaWorldCalls.h).
    WorldCall = 1,
    // The party stepped on a place that runs an event.
    PositionTrigger = 2,
    CastSpell = 3,
    ActivateWorldHit = 4,
    Chest = 5,
    Dialogue = 6,
    TravelVote = 7,
    ReturnDowned = 8,
    House = 9,
    // Asking the others to rest or wait, or agreeing to it.
    Rest = 10,
    // A quest item the guest's own game put into the world's quest pouch (out of a chest or corpse it looted).
    QuestItem = 11,
    // A lying item the guest's player takes, by its key. The world is the host's: it gives the item
    // (Message::TakenWorldItem) or, the item gone, nothing.
    TakeWorldItem = 12,
    // The guest's player answered OK to its own game's question at the map's edge: the place it leads to, which
    // the host proposes to the others in that player's name.
    ProposeTravel = 13,
};

// A part of a map's state that travels by itself when it changes (Message::MapSection).
enum class MapSection : uint8_t
{
    // What events changed of the map: variables, face and texture changes, lights, NPC changes (EventRuntimeState).
    EventState = 1,
    // Doors and other movers: sent when one starts or ends a move; between that they move in each game.
    Mechanisms = 2,
    // What lies on the ground.
    WorldItems = 3,
};

// The longest block a message may carry: a whole map's state with a long game's campaign fits many times over, and a
// length beyond it is refused before anything is allocated for it.
constexpr size_t MaxBlockBytes = 64u * 1024u * 1024u;
constexpr size_t MaxNameLength = 64;
constexpr uint8_t PresentationCinematic = 1;
constexpr uint8_t PresentationMovie = 2;

// A session's password: the host's game refuses a Hello that does not carry it.
constexpr size_t MaxPasswordLength = 32;
// A line of chat, in bytes.
constexpr size_t MaxChatLength = 240;
// The lines of a game's content identity (GameApplication::coopContentIdentity) in a join request.
constexpr size_t MaxIdentityLines = 512;
constexpr size_t MaxIdentityLineLength = 256;
}
