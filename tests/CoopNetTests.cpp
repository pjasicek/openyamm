#include "doctest/doctest.h"

#include "engine/net/ByteStream.h"
#include "engine/net/EnetTransport.h"
#include "engine/net/LanDiscovery.h"
#include "engine/net/LoopbackTransport.h"
#include "engine/net/RendezvousClient.h"
#include "engine/net/RendezvousServer.h"
#include "game/coop/CoopInvitation.h"
#include "game/coop/CharacterFile.h"
#include "game/coop/CoopBodies.h"
#include "game/coop/CoopCharacter.h"
#include "game/coop/CoopCodec.h"
#include "game/gameplay/TravelRuntime.h"
#include "game/maps/SaveSections.h"

#include <algorithm>
#include <array>
#include <cstdint>
#include <filesystem>
#include <functional>
#include <memory>
#include <random>
#include <span>
#include <string>
#include <vector>

using namespace OpenYAMM;
using namespace OpenYAMM::Game;

namespace
{
Party::Snapshot oneCharacter(int health, int gold)
{
    Party::Snapshot party;
    Character member;
    member.name = "Ariel";
    member.maxHealth = 100;
    member.health = health;
    member.spellPoints = 20;
    party.members.push_back(member);
    party.gold = gold;
    party.food = 7;
    return party;
}

InventoryItem itemOf(uint32_t objectDescriptionId)
{
    InventoryItem item;
    item.objectDescriptionId = objectDescriptionId;
    return item;
}
}

TEST_CASE("co-op net: a message reads back field by field, and a short one fails as a whole")
{
    Engine::ByteWriter writer;
    writer.u8(7);
    writer.u16(65000);
    writer.u32(4000000000u);
    writer.u64(0x1122334455667788ull);
    writer.i16(-1234);
    writer.i32(-123456789);
    writer.f32(1.5f);
    writer.boolean(true);
    writer.text("Dagger Wound");
    writer.block(std::vector<uint8_t>{1, 2, 3});

    Engine::ByteReader reader(writer.bytes());
    CHECK(reader.u8() == 7);
    CHECK(reader.u16() == 65000);
    CHECK(reader.u32() == 4000000000u);
    CHECK(reader.u64() == 0x1122334455667788ull);
    CHECK(reader.i16() == -1234);
    CHECK(reader.i32() == -123456789);
    CHECK(reader.f32() == doctest::Approx(1.5f));
    CHECK(reader.boolean());
    CHECK(reader.text() == "Dagger Wound");
    CHECK(reader.block(16) == std::vector<uint8_t>{1, 2, 3});
    CHECK(reader.ok());
    CHECK(reader.remaining() == 0);

    // One byte short: the last field cannot be read, and the reader says so.
    std::vector<uint8_t> shortBytes = writer.bytes();
    shortBytes.pop_back();
    Engine::ByteReader shortReader(shortBytes);
    shortReader.u8();
    shortReader.u16();
    shortReader.u32();
    shortReader.u64();
    shortReader.i16();
    shortReader.i32();
    shortReader.f32();
    shortReader.boolean();
    shortReader.text();
    shortReader.block(16);
    CHECK_FALSE(shortReader.ok());

    // A text longer than the reader allows fails it too.
    Engine::ByteReader strictReader(writer.bytes());
    strictReader.u8();
    strictReader.u16();
    strictReader.u32();
    strictReader.u64();
    strictReader.i16();
    strictReader.i32();
    strictReader.f32();
    strictReader.boolean();
    strictReader.text(4);
    CHECK_FALSE(strictReader.ok());
}

TEST_CASE("co-op net: two games in one process exchange messages and learn of each other's leaving")
{
    Engine::LoopbackTransport host;
    Engine::LoopbackTransport guest;
    host.accept(guest);
    host.service(0);
    guest.service(0);

    Engine::NetEvent event;
    REQUIRE(host.pollEvent(event));
    CHECK(event.type == Engine::NetEvent::Type::Connected);
    const Engine::NetPeerId guestPeer = event.peer;
    REQUIRE(guest.pollEvent(event));
    CHECK(event.type == Engine::NetEvent::Type::Connected);
    const Engine::NetPeerId hostPeer = event.peer;

    const std::vector<uint8_t> hello = {1, 2, 3};
    const std::vector<uint8_t> welcome = {9};
    CHECK(guest.send(hostPeer, 0, Engine::NetDelivery::Reliable, hello));
    CHECK(host.send(guestPeer, 1, Engine::NetDelivery::Reliable, welcome));

    // Nothing arrives before the receiving end's next service.
    CHECK_FALSE(host.pollEvent(event));
    host.service(0);
    guest.service(0);
    REQUIRE(host.pollEvent(event));
    CHECK(event.type == Engine::NetEvent::Type::Message);
    CHECK(event.peer == guestPeer);
    CHECK(event.channel == 0);
    CHECK(event.payload == hello);
    REQUIRE(guest.pollEvent(event));
    CHECK(event.channel == 1);
    CHECK(event.payload == welcome);

    guest.disconnect(hostPeer);
    host.service(0);
    REQUIRE(host.pollEvent(event));
    CHECK(event.type == Engine::NetEvent::Type::Disconnected);
    CHECK(event.peer == guestPeer);
    CHECK_FALSE(host.send(guestPeer, 0, Engine::NetDelivery::Reliable, welcome));
}

TEST_CASE("co-op net: the world's change to a guest's character goes on top of what the guest's game did")
{
    // The guest's game drank a potion (+10) and spent 30 gold while the host's monster hit for 25 and a reward
    // paid 100.
    const Party::Snapshot base = oneCharacter(60, 500);
    Party::Snapshot host = base;
    host.members[0].health = 35;
    host.gold = 600;
    Party::Snapshot put = base;
    put.members[0].health = 70;
    put.gold = 470;
    put.members[0].name = "Ariel the Bold";

    const Party::Snapshot merged = mergeGuestCharacter(base, host, put);
    REQUIRE(merged.members.size() == 1);
    CHECK(merged.members[0].health == 45);
    CHECK(merged.gold == 570);
    // What only the guest changed is the guest's.
    CHECK(merged.members[0].name == "Ariel the Bold");
    CHECK(merged.food == 7);
}

TEST_CASE("co-op net: what the host put into a guest's bags is kept; what only the guest moved is the guest's")
{
    Party::Snapshot base = oneCharacter(60, 0);
    base.members[0].inventory.push_back(itemOf(1));

    SUBCASE("the host gave loot")
    {
        Party::Snapshot host = base;
        host.members[0].inventory.push_back(itemOf(2));
        Party::Snapshot put = base;
        put.members[0].inventory.clear();

        const Party::Snapshot merged = mergeGuestCharacter(base, host, put);
        REQUIRE(merged.members[0].inventory.size() == 2);
        CHECK(merged.members[0].inventory[1].objectDescriptionId == 2);
    }

    SUBCASE("only the guest changed its bags")
    {
        Party::Snapshot put = base;
        put.members[0].inventory.push_back(itemOf(3));

        const Party::Snapshot merged = mergeGuestCharacter(base, base, put);
        REQUIRE(merged.members[0].inventory.size() == 2);
        CHECK(merged.members[0].inventory[1].objectDescriptionId == 3);
    }
}

TEST_CASE("co-op net: a party's ruleset state travels with it; the host's change of its auras holds")
{
    Party::Snapshot base = oneCharacter(60, 0);
    base.rulesetState.auraHolders[5] = 0;
    base.rulesetState.heldFood = 3;

    SUBCASE("it goes over the wire with the character")
    {
        base.rulesetState.fixedAuraMaps[17] = "out01.odm";
        base.rulesetState.fixedAuraEndMinutes[17] = 1234.5;
        base.rulesetState.madnessDeaths = 2;
        Party::Snapshot decoded;
        REQUIRE(SaveSections::decodeCharacters(SaveSections::encodeCharacters(base), decoded));
        CHECK(decoded.rulesetState == base.rulesetState);
    }

    SUBCASE("the host gave an aura while the guest's game ended another")
    {
        Party::Snapshot host = base;
        host.rulesetState.auraHolders[38] = PartyRulesetState::FixedAuraHolder;
        host.rulesetState.fixedAuraMaps[38] = "";
        Party::Snapshot put = base;
        put.rulesetState.auraHolders.clear();
        put.rulesetState.heldFood = 9;

        const Party::Snapshot merged = mergeGuestCharacter(base, host, put);
        CHECK(merged.rulesetState.auraHolders == host.rulesetState.auraHolders);
        CHECK(merged.rulesetState.fixedAuraMaps == host.rulesetState.fixedAuraMaps);
        // The held food is the guest's game's to count.
        CHECK(merged.rulesetState.heldFood == 9);
    }

    SUBCASE("only the guest's game changed its auras")
    {
        Party::Snapshot put = base;
        put.rulesetState.auraHolders.clear();

        const Party::Snapshot merged = mergeGuestCharacter(base, base, put);
        CHECK(merged.rulesetState.auraHolders.empty());
    }
}

TEST_CASE("co-op net: a trip is paid by every party, each its own fare and food")
{
    Party buyer;
    buyer.restoreSnapshot(oneCharacter(60, 500));
    Party other;
    other.restoreSnapshot(oneCharacter(40, 30));
    other.addFood(-5);
    TravelCost cost;
    cost.fareGold = 50;
    cost.travelDays = 2;
    cost.travelFood = 5;
    cost.rideByBoat = false;
    Party *pOther = &other;

    REQUIRE(applyTravelCost(buyer, std::span<Party *const>(&pOther, 1), nullptr, cost));
    CHECK(buyer.gold() == 450);
    CHECK(buyer.food() == 2);
    // A party short of the fare pays what it has; one short of the road's food arrives weak.
    CHECK(other.gold() == 0);
    CHECK(other.food() == 0);
    CHECK(other.member(0)->conditions.test(size_t(CharacterCondition::Weak)));
    CHECK_FALSE(buyer.member(0)->conditions.test(size_t(CharacterCondition::Weak)));
    // Both rested on the way.
    CHECK(buyer.member(0)->health == buyer.member(0)->maxHealth);

    // Nothing to pay is nothing done.
    CHECK_FALSE(applyTravelCost(buyer, {}, nullptr, TravelCost{}));
    CHECK(buyer.gold() == 450);
}

TEST_CASE("co-op net: a character file keeps the character, what its ruleset holds for it, and its last copy")
{
    const std::filesystem::path folder = std::filesystem::temp_directory_path()
        / ("oyamm_character_" + std::to_string(std::random_device{}()));
    const std::filesystem::path path = folder / "ariel.oychar";
    Party::Snapshot party = oneCharacter(60, 345);
    party.members.push_back(party.members.front());
    party.rulesetState.auraHolders[5] = 0;
    party.rulesetState.heldFood = 4;
    party.campaign.questPouch.push_back(itemOf(9));
    RulesetSelection ruleset;
    ruleset.id = "maw";

    CharacterFile file = makeCharacterFile(party, ruleset);
    // One character, and nothing of the world it came from.
    REQUIRE(file.character.members.size() == 1);
    CHECK(file.character.campaign.questPouch.empty());
    std::string error;
    REQUIRE_MESSAGE(writeCharacterFile(path, file, error), error);
    CHECK(file.revision == 1);

    std::optional<CharacterFile> read = readCharacterFile(path, error);
    REQUIRE_MESSAGE(read.has_value(), error);
    CHECK(read->id == file.id);
    CHECK(read->revision == 1);
    CHECK(read->ruleset.id == "maw");
    REQUIRE(read->character.members.size() == 1);
    CHECK(read->character.members[0].name == "Ariel");
    CHECK(read->character.gold == 345);
    CHECK(read->character.rulesetState == party.rulesetState);

    // Written again, the copy before stays beside it.
    file.character.gold = 999;
    REQUIRE_MESSAGE(writeCharacterFile(path, file, error), error);
    read = readCharacterFile(path, error);
    REQUIRE(read.has_value());
    CHECK(read->revision == 2);
    CHECK(read->character.gold == 999);
    std::filesystem::path previous = path;
    previous += ".bak";
    const std::optional<CharacterFile> before = readCharacterFile(previous, error);
    REQUIRE(before.has_value());
    CHECK(before->character.gold == 345);

    // Something else is refused by name.
    CHECK_FALSE(readCharacterFile(folder / "missing.oychar", error).has_value());
    std::error_code fileError;
    std::filesystem::remove_all(folder, fileError);
}

TEST_CASE("co-op net: a joining game is told the first thing its content differs in")
{
    const std::vector<std::string> host = {"package engine schema 4", "mod a 1.0", "mod b 2.0", "ruleset maw"};
    CHECK_FALSE(coopContentDifference(host, host).has_value());

    std::vector<std::string> guest = host;
    guest.back() = "ruleset mmerge";
    REQUIRE(coopContentDifference(host, guest).has_value());
    // Other rules are said in words of their own, naming both games' rules.
    CHECK(coopContentDifference(host, guest)->find("\"maw\"") != std::string::npos);
    CHECK(coopContentDifference(host, guest)->find("\"mmerge\"") != std::string::npos);

    // A guest plays by the host's difficulty: another one the game may change is no difference.
    std::vector<std::string> hard = host;
    hard.back() = "ruleset maw hard";
    guest.back() = "ruleset maw maw";
    CHECK_FALSE(coopContentDifference(hard, guest).has_value());
    CHECK_FALSE(coopRulesRefusal("maw hard solo", "maw easy solo").has_value());
    CHECK_FALSE(coopRulesRefusal("mmerge", "mmerge").has_value());

    // Nightmare and the challenge modes are no exception: the guest plays by the host's.
    CHECK_FALSE(coopRulesRefusal("maw nightmare", "maw hard").has_value());
    CHECK_FALSE(coopRulesRefusal("maw hard", "maw nightmare").has_value());

    // The kind must match under a ruleset.
    CHECK(coopRulesRefusal("maw hard", "maw hard solo").has_value());
    guest.back() = "ruleset maw nightmare solo";
    REQUIRE(coopContentDifference(hard, guest).has_value());
    CHECK(coopContentDifference(hard, guest)->find("maw nightmare solo") != std::string::npos);

    guest = host;
    guest.push_back("mod c 1.0");
    REQUIRE(coopContentDifference(host, guest).has_value());
    CHECK(coopContentDifference(host, guest)->find("mod c 1.0") != std::string::npos);

    // The same mods in another order mount differently.
    guest = host;
    std::swap(guest[1], guest[2]);
    CHECK(coopContentDifference(host, guest).has_value());
}

TEST_CASE("co-op net: a scan of the local network asks, and a host's answer says what its session is")
{
    const std::vector<uint8_t> question = Engine::encodeLanProbe(4711);
    REQUIRE(Engine::decodeLanProbe(question).has_value());
    CHECK(*Engine::decodeLanProbe(question) == 4711u);
    Engine::LanSessionInfo info;
    info.name = "Ariel's world";
    info.world = "mm8";
    info.ruleset = "maw";
    info.protocol = 5;
    info.players = 2;
    info.maxPlayers = 4;
    info.sessionId = 0xC0FFEEu;
    const std::vector<uint8_t> answer = Engine::encodeLanAnswer(4711, info);
    const std::optional<Engine::LanSessionInfo> read = Engine::decodeLanAnswer(answer, 4711);
    CHECK(read.has_value());
    CHECK((read ? read->sessionId : 0u) == 0xC0FFEEu);
    REQUIRE(read.has_value());
    CHECK(read->name == "Ariel's world");
    CHECK(read->world == "mm8");
    CHECK(read->ruleset == "maw");
    CHECK(read->players == 2);
    // An answer to another question, a question taken for an answer, and anything else are none of them.
    CHECK_FALSE(Engine::decodeLanAnswer(answer, 4712).has_value());
    CHECK_FALSE(Engine::decodeLanAnswer(question, 4711).has_value());
    CHECK_FALSE(Engine::decodeLanProbe(answer).has_value());
    CHECK_FALSE(Engine::decodeLanProbe(std::vector<uint8_t>{1, 2, 3}).has_value());
}

TEST_CASE("co-op net: a lobby lists a host's session and finds a joining game a path to it by its code")
{
    // The lobby and two games' sockets, all on this machine over real UDP.
    Engine::NetLibrary library;
    Engine::RendezvousServerConfig config;
    config.port = 0;
    config.relayPortCount = 2;
    config.verbose = false;
    Engine::RendezvousServer server;
    REQUIRE(server.start(config));
    const std::optional<Engine::NetAddress> lobby =
        Engine::parseNetAddress("127.0.0.1:" + std::to_string(server.port()));
    REQUIRE(lobby.has_value());

    Engine::EnetTransport hostSocket;
    Engine::EnetTransport guestSocket;
    REQUIRE(hostSocket.open(0, 3));
    REQUIRE(guestSocket.open(0, 1));
    const auto clientOn = [&lobby](Engine::EnetTransport &socket)
    {
        return std::make_unique<Engine::RendezvousClient>(
            [&socket](const Engine::NetAddress &to, std::span<const uint8_t> datagram)
            {
                socket.sendDatagram(to, datagram);
            },
            *lobby);
    };
    std::unique_ptr<Engine::RendezvousClient> pHost = clientOn(hostSocket);
    std::unique_ptr<Engine::RendezvousClient> pGuest = clientOn(guestSocket);
    hostSocket.setDatagramHandler([&pHost](const Engine::NetAddress &from, std::span<const uint8_t> datagram)
    {
        return pHost->handleDatagram(from, datagram, Engine::netNowMilliseconds());
    });
    guestSocket.setDatagramHandler([&pGuest](const Engine::NetAddress &from, std::span<const uint8_t> datagram)
    {
        return pGuest->handleDatagram(from, datagram, Engine::netNowMilliseconds());
    });
    const auto run = [&](const std::function<bool()> &done)
    {
        for (int step = 0; step < 400 && !done(); ++step)
        {
            server.service(5);
            hostSocket.service(0);
            guestSocket.service(0);
            pHost->update(Engine::netNowMilliseconds());
            pGuest->update(Engine::netNowMilliseconds());
        }

        return done();
    };

    Engine::SessionInfo info;
    info.name = "The test world";
    info.world = "mm8";
    info.ruleset = "mmerge";
    Engine::NetAddress hostLocal = *Engine::parseNetAddress("127.0.0.1:1");
    hostLocal.port = hostSocket.localPort();
    pHost->startHosting(info, hostLocal);
    REQUIRE(run([&pHost]() { return pHost->registered(); }));
    const std::string code = pHost->sessionCode();
    CHECK(code.size() == Engine::SessionCodeLength);

    pGuest->requestList();
    REQUIRE(run([&pGuest]() { return pGuest->sessionList().has_value(); }));
    REQUIRE(pGuest->sessionList()->size() == 1);
    CHECK(pGuest->sessionList()->front().info.name == "The test world");
    CHECK(Engine::toString(pGuest->sessionList()->front().code) == code);

    Engine::NetAddress guestLocal = *Engine::parseNetAddress("127.0.0.1:1");
    guestLocal.port = guestSocket.localPort();
    pGuest->startJoin(*Engine::parseSessionCode(code), guestLocal, false);
    REQUIRE(run([&pGuest]()
    {
        return pGuest->joinState() == Engine::JoinState::Ready || pGuest->joinState() == Engine::JoinState::Failed;
    }));
    CHECK((pGuest->joinState() == Engine::JoinState::Ready));
    CHECK(pGuest->joinAddress().port == hostSocket.localPort());

    // A code the lobby does not know is said to be none.
    std::unique_ptr<Engine::RendezvousClient> pStranger = clientOn(guestSocket);
    pGuest = std::move(pStranger);
    pGuest->startJoin(*Engine::parseSessionCode("ZZZZZZ"), guestLocal, false);
    REQUIRE(run([&pGuest]() { return pGuest->joinState() == Engine::JoinState::Failed; }));
    CHECK((pGuest->joinFailure() == Engine::JoinFailure::NoSuchSession));
}

TEST_CASE("co-op net: a character's vitals travel alone and go back into the same character")
{
    Party::Snapshot party = oneCharacter(60, 500);
    party.members[0].recoverySecondsRemaining = 1.25f;
    const CharacterVitals vitals = takeCharacterVitals(party);
    REQUIRE(vitals.members.size() == 1);
    CHECK(vitals.members[0].health == 60);
    CHECK(vitals.members[0].spellPoints == 20);
    CHECK(vitals.members[0].recoverySecondsRemaining == doctest::Approx(1.25f));

    // Two characters that differ in vitals alone are the same without them.
    Party::Snapshot hurt = party;
    hurt.members[0].health = 10;
    hurt.members[0].recoverySecondsRemaining = 0.0f;
    CHECK(SaveSections::encodeCharacters(withoutCharacterVitals(party))
        == SaveSections::encodeCharacters(withoutCharacterVitals(hurt)));

    CHECK(applyCharacterVitals(hurt, vitals));
    CHECK(hurt.members[0].health == 60);
    CHECK(hurt.members[0].recoverySecondsRemaining == doctest::Approx(1.25f));

    // Vitals of a party of another shape are refused.
    Party::Snapshot two = party;
    two.members.push_back(two.members[0]);
    CHECK_FALSE(applyCharacterVitals(two, vitals));
}

TEST_CASE("co-op net: a sound reaches another game with all that playing it needs")
{
    EventRuntimeState::PendingSound loop;
    loop.kind = EventRuntimeState::PendingSound::Kind::PlayLoopingKeyed;
    loop.soundScope = SoundScope::World;
    loop.soundId = 4321;
    loop.soundName = "forge_loop";
    loop.key = 0x100000002ull;
    loop.actorIndex = 17;
    loop.pitch = 1.1f;
    loop.x = -300;
    loop.y = 4000;
    loop.z = 96;
    loop.positional = true;
    loop.hasExplicitZ = true;
    EventRuntimeState::PendingSound chime;
    chime.soundId = 206;

    Engine::ByteWriter writer;
    CoopCodec::writeSounds(writer, {loop, chime});
    Engine::ByteReader reader(writer.bytes());
    std::vector<EventRuntimeState::PendingSound> read;
    REQUIRE(CoopCodec::readSounds(reader, read));
    REQUIRE(read.size() == 2);
    CHECK(read[0].kind == EventRuntimeState::PendingSound::Kind::PlayLoopingKeyed);
    CHECK(read[0].soundScope == SoundScope::World);
    CHECK(read[0].soundId == 4321);
    CHECK(read[0].soundName == "forge_loop");
    CHECK(read[0].key == 0x100000002ull);
    REQUIRE(read[0].actorIndex.has_value());
    CHECK(*read[0].actorIndex == 17);
    CHECK(read[0].pitch == doctest::Approx(1.1f));
    CHECK(read[0].x == -300);
    CHECK(read[0].y == 4000);
    CHECK(read[0].z == 96);
    CHECK(read[0].positional);
    CHECK(read[0].hasExplicitZ);
    CHECK(read[1].soundId == 206);
    CHECK_FALSE(read[1].actorIndex.has_value());
    CHECK_FALSE(read[1].positional);

    // A kind no game knows fails the whole list.
    std::vector<uint8_t> bad = writer.bytes();
    bad[1] = 200;
    Engine::ByteReader badReader(bad);
    std::vector<EventRuntimeState::PendingSound> none;
    CHECK_FALSE(CoopCodec::readSounds(badReader, none));
}

TEST_CASE("co-op net: another player's body is a model of its race, then of its class, that the worlds have")
{
    constexpr uint32_t Human = 0;
    constexpr uint32_t Minotaur = 3;
    constexpr uint32_t Troll = 4;
    constexpr uint32_t Undead = 6;
    constexpr uint32_t Dwarf = 9;
    constexpr uint32_t Male = 0;
    constexpr uint32_t Female = 1;
    const auto mm8 = [](const std::string &descriptor)
    {
        return descriptor == "Human Mercenary A" || descriptor == "Cleric (human male) A"
            || descriptor == "Minotaur A" || descriptor == "Necromancer (monster) A";
    };
    CHECK(coopBodyDescriptor(Human, Male, "Knight", mm8) == "Human Mercenary A");
    CHECK(coopBodyDescriptor(Human, Male, "Cleric", mm8) == "Cleric (human male) A");
    CHECK(coopBodyDescriptor(Human, Male, "Priest of Light", mm8) == "Cleric (human male) A");
    // The race before the class: a minotaur who is a mage is a minotaur.
    CHECK(coopBodyDescriptor(Minotaur, Male, "Sorcerer", mm8) == "Minotaur A");
    CHECK(coopBodyDescriptor(Undead, Male, "Knight", mm8) == "Necromancer (monster) A");
    // A race the mounted worlds have no model of stands by its class, and as a fighter where that has none.
    CHECK(coopBodyDescriptor(Troll, Male, "Cleric", mm8) == "Cleric (human male) A");
    CHECK(coopBodyDescriptor(Troll, Male, "Troll", mm8) == "Human Mercenary A");
    CHECK(coopBodyDescriptor(Human, Male, "Sorcerer", mm8) == "Necromancer (monster) A");
    // No woman's model mounted: the men's of the class.
    CHECK(coopBodyDescriptor(Human, Female, "Cleric", mm8) == "Cleric (human male) A");

    const auto mm6 = [](const std::string &descriptor)
    {
        return descriptor == "KnightPlate A" || descriptor == "Cleric A" || descriptor == "BArcher A"
            || descriptor == "BDwarf A" || descriptor == "Druidess A" || descriptor == "PeasantF3 A";
    };
    CHECK(coopBodyDescriptor(Human, Male, "Cleric", mm6) == "Cleric A");
    CHECK(coopBodyDescriptor(Human, Male, "Archer", mm6) == "BArcher A");
    CHECK(coopBodyDescriptor(Human, Male, "Paladin", mm6) == "KnightPlate A");
    CHECK(coopBodyDescriptor(Dwarf, Female, "Cleric", mm6) == "BDwarf A");
    // A woman by a woman's model: one that casts for a class that casts.
    CHECK(coopBodyDescriptor(Human, Female, "Sorcerer", mm6) == "Druidess A");
    CHECK(coopBodyDescriptor(Human, Female, "Knight", mm6) == "PeasantF3 A");

    const auto nothing = [](const std::string &)
    {
        return false;
    };
    CHECK(coopBodyDescriptor(Human, Male, "Knight", nothing).empty());
}

TEST_CASE("co-op net: with every world mounted another player's body is the chosen model of its race, sex and class")
{
    constexpr uint32_t Human = 0;
    constexpr uint32_t Vampire = 1;
    constexpr uint32_t Minotaur = 3;
    constexpr uint32_t Undead = 6;
    constexpr uint32_t Elf = 7;
    constexpr uint32_t Male = 0;
    constexpr uint32_t Female = 1;
    const std::vector<std::string> mounted = {"Fighter Plate A", "Swordsman A", "Fighter Chain A", "Sorcerer A",
        "Mage A", "Cleric A", "Cleric (human male) A", "Druidess A", "Warlock A", "Necromancer A", "Minotaur A",
        "BMinotaur A", "Vampire A", "Vampire (monster) A", "Lich A", "BLich A", "Archer A", "BArcher A",
        "Elf Archer A", "Elf Spearman A", "Monk A", "BThief A", "KnightPlate A", "Human Mercenary A",
        "Pirate Crossbowman (Female) A"};
    const auto all = [&mounted](const std::string &descriptor)
    {
        return std::find(mounted.begin(), mounted.end(), descriptor) != mounted.end();
    };
    // A class and its promotions share a body.
    CHECK(coopBodyDescriptor(Human, Male, "Knight", all) == "Fighter Plate A");
    CHECK(coopBodyDescriptor(Human, Male, "Champion", all) == "Fighter Plate A");
    CHECK(coopBodyDescriptor(Human, Male, "Paladin", all) == "Fighter Plate A");
    CHECK(coopBodyDescriptor(Human, Female, "Knight", all) == "Fighter Chain A");
    CHECK(coopBodyDescriptor(Human, Male, "Sorcerer", all) == "Sorcerer A");
    CHECK(coopBodyDescriptor(Human, Male, "Necromancer", all) == "Sorcerer A");
    CHECK(coopBodyDescriptor(Human, Male, "Cleric", all) == "Cleric A");
    CHECK(coopBodyDescriptor(Human, Male, "Arch Druid", all) == "Cleric A");
    CHECK(coopBodyDescriptor(Human, Female, "Cleric", all) == "Druidess A");
    CHECK(coopBodyDescriptor(Human, Female, "Druid", all) == "Druidess A");
    CHECK(coopBodyDescriptor(Human, Female, "Sorcerer", all) == "Warlock A");
    CHECK(coopBodyDescriptor(Human, Female, "Necromancer", all) == "Necromancer A");
    CHECK(coopBodyDescriptor(Human, Male, "Archer", all) == "Archer A");
    CHECK(coopBodyDescriptor(Human, Female, "Ranger Lord", all) == "BArcher A");
    CHECK(coopBodyDescriptor(Human, Female, "Thief", all) == "Pirate Crossbowman (Female) A");
    // A name inside another name: a Death Knight is no Knight, a Warrior Mage no Mage, and only a Master is a monk.
    CHECK(coopBodyDescriptor(Human, Male, "Death Knight", all) == "KnightPlate A");
    CHECK(coopBodyDescriptor(Human, Male, "Warrior Mage", all) == "Archer A");
    CHECK(coopBodyDescriptor(Human, Male, "Master Archer", all) == "Archer A");
    CHECK(coopBodyDescriptor(Human, Male, "Master", all) == "Monk A");
    // A hooded model serves a woman too.
    CHECK(coopBodyDescriptor(Human, Female, "Monk", all) == "Monk A");
    // One model for a race, whatever the class and the sex.
    CHECK(coopBodyDescriptor(Minotaur, Male, "Sorcerer", all) == "Minotaur A");
    CHECK(coopBodyDescriptor(Vampire, Female, "Vampire", all) == "Vampire A");
    CHECK(coopBodyDescriptor(Undead, Female, "Lich", all) == "Lich A");
    // An elf in a closed helm is the human's model; otherwise an elf's.
    CHECK(coopBodyDescriptor(Elf, Male, "Knight", all) == "Fighter Plate A");
    CHECK(coopBodyDescriptor(Elf, Male, "Sorcerer", all) == "Elf Spearman A");
    CHECK(coopBodyDescriptor(Elf, Female, "Archer", all) == "Elf Archer A");
}

TEST_CASE("co-op net: a body is drawn at the height of its race and sex, not at its monster's size")
{
    constexpr uint32_t Human = 0;
    constexpr uint32_t Minotaur = 3;
    constexpr uint32_t Troll = 4;
    constexpr uint32_t Dragon = 5;
    constexpr uint32_t Elf = 7;
    constexpr uint32_t Dwarf = 9;
    CHECK(coopBodyHeight(Human, 0) == doctest::Approx(190.0f));
    CHECK(coopBodyHeight(Human, 1) == doctest::Approx(180.0f));
    CHECK(coopBodyHeight(Elf, 1) == doctest::Approx(180.0f));
    CHECK(coopBodyHeight(Dwarf, 0) == doctest::Approx(140.0f));
    CHECK(coopBodyHeight(Dwarf, 1) == doctest::Approx(130.0f));
    CHECK(coopBodyHeight(Minotaur, 0) == doctest::Approx(235.0f));
    CHECK(coopBodyHeight(Troll, 0) == doctest::Approx(235.0f));
    // To its wing tips: its head is then about a man's height.
    CHECK(coopBodyHeight(Dragon, 0) == doctest::Approx(370.0f));
    // A race nobody knows is drawn as a human.
    CHECK(coopBodyHeight(77, 0) == doctest::Approx(190.0f));
}

TEST_CASE("co-op net: a body's glow goes by the average tier of what is worn")
{
    CHECK(coopGearTier(std::span<const uint8_t>()) == 0);
    const std::array<uint8_t, 1> one = {4};
    CHECK(coopGearTier(one) == 4);
    // A club, leather and a cap: plain gear, no glow (below 2).
    const std::array<uint8_t, 3> plain = {1, 1, 1};
    CHECK(coopGearTier(plain) == 1);
    // Halves round up: 2.5 is 3.
    const std::array<uint8_t, 4> mixed = {2, 3, 2, 3};
    CHECK(coopGearTier(mixed) == 3);
    // One artifact among plain pieces does not make the whole body legendary: 12 over 5 is 2.4.
    const std::array<uint8_t, 5> oneArtifact = {4, 2, 2, 2, 2};
    CHECK(coopGearTier(oneArtifact) == 2);
}

TEST_CASE("co-op net: an invitation is read out of the message a host sends, or from a bare code or address")
{
    using namespace OpenYAMM::Game;

    // What the host's Copy Invitation makes, and what Paste Invitation reads back.
    CHECK(Coop::invitationMark({.code = "HS4CHN"}) == "[oyamm:HS4CHN]");
    CHECK(Coop::invitationMark({.code = "HS4CHN", .lobby = "192.168.1.128"}) == "[oyamm:HS4CHN@192.168.1.128]");
    CHECK(Coop::invitationMark({.address = "192.168.1.130"}) == "[oyamm:192.168.1.130]");

    const std::optional<Coop::Invitation> byCode = Coop::readInvitation(
        "Join my OpenYAMM game \"Ariel's world\": copy this message, then ... Paste Invitation. [oyamm:HS4CHN]");
    REQUIRE(byCode.has_value());
    CHECK(byCode->code == "HS4CHN");
    CHECK(byCode->lobby.empty());
    CHECK(byCode->address.empty());

    const std::optional<Coop::Invitation> byLobby = Coop::readInvitation("hey [oyamm:hs4chn@lobby.example:27910] !");
    REQUIRE(byLobby.has_value());
    CHECK(byLobby->code == "HS4CHN");
    CHECK(byLobby->lobby == "lobby.example:27910");

    const std::optional<Coop::Invitation> byAddress = Coop::readInvitation("[oyamm:192.168.1.130:27951]");
    REQUIRE(byAddress.has_value());
    CHECK(byAddress->address == "192.168.1.130:27951");
    CHECK(byAddress->code.empty());

    // A session's password rides with it.
    CHECK(Coop::invitationMark({.code = "HS4CHN", .password = "tea"}) == "[oyamm:HS4CHN#tea]");
    const std::optional<Coop::Invitation> locked = Coop::readInvitation("[oyamm:HS4CHN@192.168.1.128#tea]");
    REQUIRE(locked.has_value());
    CHECK(locked->code == "HS4CHN");
    CHECK(locked->lobby == "192.168.1.128");
    CHECK(locked->password == "tea");
    const std::optional<Coop::Invitation> lockedAddress = Coop::readInvitation("[oyamm:192.168.1.130#tea]");
    REQUIRE(lockedAddress.has_value());
    CHECK(lockedAddress->address == "192.168.1.130");
    CHECK(lockedAddress->password == "tea");

    // A code or an address copied by itself.
    const std::optional<Coop::Invitation> bareCode = Coop::readInvitation("  hs4chn\n");
    REQUIRE(bareCode.has_value());
    CHECK(bareCode->code == "HS4CHN");
    const std::optional<Coop::Invitation> bareAddress = Coop::readInvitation("192.168.1.130");
    REQUIRE(bareAddress.has_value());
    CHECK(bareAddress->address == "192.168.1.130");

    // Anything else on the clipboard is no invitation.
    CHECK_FALSE(Coop::readInvitation("").has_value());
    CHECK_FALSE(Coop::readInvitation("see you at eight").has_value());
    CHECK_FALSE(Coop::readInvitation("[oyamm:HS4CHN").has_value());
    CHECK_FALSE(Coop::readInvitation("[oyamm:]").has_value());
    CHECK_FALSE(Coop::readInvitation("[oyamm:HS4CHN@]").has_value());
}

TEST_CASE("co-op net: a lobby does not answer an address that asks too much")
{
    // Three requests at once and one a second after that; the address asks once (which also gets it the lobby's
    // cookie: only requests that carry it are counted and answered), then sends twelve in one go.
    Engine::NetLibrary library;
    Engine::RendezvousServerConfig config;
    config.port = 0;
    config.relayPortCount = 1;
    config.verbose = false;
    config.requestsPerSecond = 1;
    config.requestBurst = 3;
    Engine::RendezvousServer server;
    REQUIRE(server.start(config));
    const std::optional<Engine::NetAddress> lobby =
        Engine::parseNetAddress("127.0.0.1:" + std::to_string(server.port()));
    REQUIRE(lobby.has_value());
    Engine::EnetTransport socket;
    REQUIRE(socket.open(0, 1));
    Engine::RendezvousClient client(
        [&socket](const Engine::NetAddress &to, std::span<const uint8_t> datagram)
        {
            socket.sendDatagram(to, datagram);
        },
        *lobby);
    socket.setDatagramHandler([&client](const Engine::NetAddress &from, std::span<const uint8_t> datagram)
    {
        return client.handleDatagram(from, datagram, Engine::netNowMilliseconds());
    });
    client.requestList();

    for (int turn = 0; turn < 400 && !client.sessionList().has_value(); ++turn)
    {
        server.service(2);
        socket.service(0);
    }

    REQUIRE(client.sessionList().has_value());
    CHECK(server.stats().refusedRequests == 0);

    for (int request = 0; request < 12; ++request)
    {
        client.requestList();
    }

    for (int turn = 0; turn < 10; ++turn)
    {
        socket.service(5);
        server.service(5);
    }

    // Two were left of the three.
    CHECK(server.stats().refusedRequests == 10);
}

// The lobby against games that do not play fair (forged sender addresses, guessed keys, requests without end).
namespace
{
// A bare socket that speaks the lobby's datagrams itself: what a game's own client never sends, and a look at the
// answers as they arrive.
struct LobbyTalker
{
    Engine::EnetTransport socket;
    std::vector<std::vector<uint8_t>> received;
    // The lobby's stamp on this socket's address, once askLobby was given one.
    uint64_t cookie = 0;

    LobbyTalker()
    {
        REQUIRE(socket.open(0, 1));
        socket.setDatagramHandler([this](const Engine::NetAddress &, std::span<const uint8_t> datagram)
        {
            received.emplace_back(datagram.begin(), datagram.end());
            return true;
        });
    }

    // The last datagram of one kind that arrived, if any.
    template <typename Message>
    std::optional<Message> last() const
    {
        for (size_t index = received.size(); index > 0; --index)
        {
            Message message;

            if (Engine::decode(received[index - 1], message))
            {
                return message;
            }
        }

        return std::nullopt;
    }

    template <typename Message>
    size_t count() const
    {
        return size_t(std::count_if(received.begin(), received.end(), [](const std::vector<uint8_t> &datagram)
        {
            Message message;
            return Engine::decode(datagram, message);
        }));
    }
};

// A lobby on this machine, over real UDP, and the talkers served with it.
struct TestLobby
{
    Engine::NetLibrary library;
    Engine::RendezvousServer server;
    Engine::NetAddress address;

    explicit TestLobby(Engine::RendezvousServerConfig config)
    {
        config.port = 0;
        config.verbose = false;
        REQUIRE(server.start(config));
        const std::optional<Engine::NetAddress> parsed =
            Engine::parseNetAddress("127.0.0.1:" + std::to_string(server.port()));
        REQUIRE(parsed.has_value());
        address = *parsed;
    }

    void turn(std::initializer_list<LobbyTalker *> talkers)
    {
        server.service(2);

        for (LobbyTalker *pTalker : talkers)
        {
            pTalker->socket.service(0);
        }
    }

    bool run(std::initializer_list<LobbyTalker *> talkers, const std::function<bool()> &done)
    {
        for (int step = 0; step < 400 && !done(); ++step)
        {
            turn(talkers);
        }

        return done();
    }

    // Some time, for what must not be answered, or must lapse.
    void runFor(std::initializer_list<LobbyTalker *> talkers, uint32_t milliseconds)
    {
        const uint32_t startedMs = Engine::netNowMilliseconds();

        while (Engine::netNowMilliseconds() - startedMs < milliseconds)
        {
            turn(talkers);
        }
    }
};

Engine::NetAddress addressOf(const std::string &text)
{
    const std::optional<Engine::NetAddress> address = Engine::parseNetAddress(text);
    REQUIRE(address.has_value());
    return *address;
}

// Sends a request as a game does: with the lobby's cookie for this socket, and once more with the cookie the lobby
// answers a request without a good one. The answer, or none when the lobby gives none.
template <typename Request, typename Reply>
std::optional<Reply> askLobby(
    TestLobby &lobby,
    LobbyTalker &talker,
    Request request,
    const Engine::NetAddress &lobbyAddress)
{
    for (int attempt = 0; attempt < 2; ++attempt)
    {
        request.cookie = talker.cookie;
        talker.received.clear();
        talker.socket.sendDatagram(lobbyAddress, Engine::encode(request));
        const bool answered = lobby.run({&talker}, [&talker]()
        {
            return talker.last<Reply>().has_value() || talker.last<Engine::AddressCookieMessage>().has_value();
        });

        if (!answered || talker.last<Reply>().has_value())
        {
            break;
        }

        talker.cookie = talker.last<Engine::AddressCookieMessage>()->cookie;
    }

    return talker.last<Reply>();
}

Engine::HostRegisterMessage registration(
    uint32_t nonce,
    const std::string &name,
    uint64_t sessionKey = 0,
    const Engine::NetAddress &localAddress = {})
{
    Engine::HostRegisterMessage message;
    message.nonce = nonce;
    message.sessionKey = sessionKey;
    message.localAddress = localAddress;
    message.info.name = name;
    message.info.world = "mm8";
    message.info.ruleset = "mmerge";
    return message;
}

// Registers (no key) or heartbeats (the session's key) and returns the lobby's answer.
Engine::HostRegisteredMessage registerSession(
    TestLobby &lobby,
    LobbyTalker &host,
    uint32_t nonce,
    const std::string &name,
    uint64_t sessionKey = 0,
    const Engine::NetAddress &localAddress = {})
{
    const std::optional<Engine::HostRegisteredMessage> reply = askLobby<Engine::HostRegisterMessage,
        Engine::HostRegisteredMessage>(lobby, host, registration(nonce, name, sessionKey, localAddress), lobby.address);
    REQUIRE(reply.has_value());
    CHECK(reply->nonce == nonce);
    return *reply;
}

std::vector<Engine::SessionListEntry> listSessions(TestLobby &lobby, LobbyTalker &asker)
{
    Engine::ListRequestMessage message;
    message.nonce = 9000;
    const std::optional<Engine::ListReplyMessage> reply =
        askLobby<Engine::ListRequestMessage, Engine::ListReplyMessage>(lobby, asker, message, lobby.address);
    REQUIRE(reply.has_value());
    return reply->entries;
}

std::string nameOfSession(const std::vector<Engine::SessionListEntry> &sessions, const Engine::SessionCode &code)
{
    for (const Engine::SessionListEntry &entry : sessions)
    {
        if (entry.code == code)
        {
            return entry.info.name;
        }
    }

    return "(not listed)";
}

// A join request and the lobby's answer to it.
Engine::JoinReplyMessage askToJoin(
    TestLobby &lobby,
    LobbyTalker &guest,
    const Engine::SessionCode &code,
    uint32_t nonce,
    bool wantRelay,
    const Engine::NetAddress &localAddress = {})
{
    Engine::JoinRequestMessage message;
    message.nonce = nonce;
    message.code = code;
    message.localAddress = localAddress;
    message.wantRelay = wantRelay;
    const std::optional<Engine::JoinReplyMessage> reply =
        askLobby<Engine::JoinRequestMessage, Engine::JoinReplyMessage>(lobby, guest, message, lobby.address);
    REQUIRE(reply.has_value());
    CHECK(reply->nonce == nonce);
    return *reply;
}

// Both sides bind to the relay port of a join, as two games do; true when the lobby answered both.
bool bindRelay(
    TestLobby &lobby,
    LobbyTalker &host,
    LobbyTalker &guest,
    const Engine::JoinReplyMessage &reply,
    const Engine::PeerIntroMessage &intro)
{
    const Engine::NetAddress relay{lobby.address.host, reply.relayPort};
    Engine::RelayBindMessage hostBind;
    hostBind.token = intro.relayToken;
    Engine::RelayBindMessage guestBind;
    guestBind.token = reply.relayToken;
    host.received.clear();
    guest.received.clear();
    host.socket.sendDatagram(relay, Engine::encode(hostBind, Engine::RendezvousMessage::RelayBind));
    guest.socket.sendDatagram(relay, Engine::encode(guestBind, Engine::RendezvousMessage::RelayBind));
    return lobby.run({&host, &guest}, [&host, &guest]()
    {
        return host.last<Engine::RelayBindMessage>().has_value() && guest.last<Engine::RelayBindMessage>().has_value();
    });
}

// The introduction the lobby sent a host for the join request it was just asked.
Engine::PeerIntroMessage introductionTo(TestLobby &lobby, LobbyTalker &host)
{
    REQUIRE(lobby.run({&host}, [&host]() { return host.last<Engine::PeerIntroMessage>().has_value(); }));
    return *host.last<Engine::PeerIntroMessage>();
}

// What a game's lobby client sent, kept instead of going out on a socket.
struct SentDatagrams
{
    std::vector<std::pair<Engine::NetAddress, std::vector<uint8_t>>> datagrams;

    Engine::RendezvousClient::SendFunction sender()
    {
        return [this](const Engine::NetAddress &to, std::span<const uint8_t> datagram)
        {
            datagrams.emplace_back(to, std::vector<uint8_t>(datagram.begin(), datagram.end()));
        };
    }

    // The punches among them, to one host or (0) to anyone.
    size_t punches(uint32_t host = 0) const
    {
        size_t count = 0;

        for (const std::pair<Engine::NetAddress, std::vector<uint8_t>> &sent : datagrams)
        {
            Engine::PunchMessage punch;

            if (Engine::decode(sent.second, punch) && (host == 0 || sent.first.host == host))
            {
                ++count;
            }
        }

        return count;
    }
};
}

TEST_CASE("co-op net: a lobby's keys, codes and relay tokens are drawn anew each time, none following another")
{
    Engine::RendezvousServerConfig config;
    config.relayPortCount = 2;
    config.requestsPerSecond = 0;
    TestLobby first(config);
    TestLobby second(config);
    std::vector<uint64_t> keys;
    std::vector<std::string> codes;
    Engine::SessionCode lastCode = {};
    LobbyTalker hosts[6];

    for (size_t index = 0; index < 6; ++index)
    {
        TestLobby &lobby = index < 3 ? first : second;
        const Engine::HostRegisteredMessage registered =
            registerSession(lobby, hosts[index], uint32_t(index + 1), "A session");
        keys.push_back(registered.sessionKey);
        codes.push_back(Engine::toString(registered.code));
        lastCode = registered.code;
    }

    for (size_t index = 0; index < keys.size(); ++index)
    {
        CHECK(keys[index] != 0);

        // No key is another's, in one lobby or across two, and none is the one before it counted on.
        for (size_t other = index + 1; other < keys.size(); ++other)
        {
            CHECK(keys[index] != keys[other]);
            CHECK(codes[index] != codes[other]);
        }

        if (index > 0)
        {
            CHECK(keys[index] - keys[index - 1] != 1);
        }
    }

    // The two sides of a relay port have tokens of their own.
    LobbyTalker guest;
    const Engine::JoinReplyMessage reply = askToJoin(second, guest, lastCode, 1, true);
    REQUIRE(second.run({&hosts[5]}, [&hosts]() { return hosts[5].last<Engine::PeerIntroMessage>().has_value(); }));
    const Engine::PeerIntroMessage intro = *hosts[5].last<Engine::PeerIntroMessage>();
    CHECK(reply.relayPort != 0);
    CHECK(reply.relayPort == intro.relayPort);
    CHECK(reply.relayToken != 0);
    CHECK(intro.relayToken != 0);
    CHECK(reply.relayToken != intro.relayToken);
    // The host is shown its own key with the introduction, the proof that the lobby sent it.
    CHECK(intro.sessionKey == keys[5]);
}

TEST_CASE("co-op net: a registration without the key from a host's address opens another session, not the host's")
{
    Engine::RendezvousServerConfig config;
    config.requestsPerSecond = 0;
    TestLobby lobby(config);
    LobbyTalker host;
    LobbyTalker guest;
    const Engine::NetAddress ownLocal = addressOf("192.168.1.10:27900");
    const Engine::NetAddress otherLocal = addressOf("192.168.66.6:6666");
    const Engine::HostRegisteredMessage mine = registerSession(lobby, host, 11, "Mine", 0, ownLocal);

    // From the same address and port, with another number and no key: all that one who forges the host's address
    // can send.
    const Engine::HostRegisteredMessage theirs = registerSession(lobby, host, 12, "Theirs", 0, otherLocal);
    CHECK(theirs.sessionKey != mine.sessionKey);
    CHECK((theirs.code != mine.code));
    CHECK(lobby.server.stats().sessions == 2);
    CHECK(nameOfSession(listSessions(lobby, guest), mine.code) == "Mine");
    CHECK((askToJoin(lobby, guest, mine.code, 1, false).hostLocalAddress == ownLocal));

    // The repeat of the host's own registration (its answer was lost) gets the same answer and changes nothing.
    const Engine::HostRegisteredMessage again = registerSession(lobby, host, 11, "Changed", 0, otherLocal);
    CHECK(again.sessionKey == mine.sessionKey);
    CHECK((again.code == mine.code));
    CHECK(lobby.server.stats().sessions == 2);
    CHECK(nameOfSession(listSessions(lobby, guest), mine.code) == "Mine");
    CHECK((askToJoin(lobby, guest, mine.code, 2, false).hostLocalAddress == ownLocal));

    // With its key the host renames and moves its session.
    const Engine::HostRegisteredMessage renamed =
        registerSession(lobby, host, 13, "Renamed", mine.sessionKey, otherLocal);
    CHECK((renamed.code == mine.code));
    CHECK(nameOfSession(listSessions(lobby, guest), mine.code) == "Renamed");
    CHECK((askToJoin(lobby, guest, mine.code, 3, false).hostLocalAddress == otherLocal));
}

TEST_CASE("co-op net: a lobby passes on a game's own-network address only when it is one")
{
    Engine::RendezvousServerConfig config;
    config.requestsPerSecond = 0;
    TestLobby lobby(config);
    LobbyTalker host;
    LobbyTalker guest;
    uint32_t nonce = 0;
    const Engine::HostRegisteredMessage registered = registerSession(lobby, host, 1, "A session");
    // Whether the host is told the address a joining game says it has on its own network.
    const auto introduced = [&](const std::string &claimed)
    {
        const Engine::NetAddress local = addressOf(claimed);
        host.received.clear();
        askToJoin(lobby, guest, registered.code, ++nonce, false, local);
        REQUIRE(lobby.run({&host}, [&host]() { return host.last<Engine::PeerIntroMessage>().has_value(); }));
        const Engine::PeerIntroMessage intro = *host.last<Engine::PeerIntroMessage>();
        CHECK(intro.clientPublicAddress.port == guest.socket.localPort());
        return intro.clientLocalAddress == local;
    };

    // Anybody's address on the internet is not passed on: the host would send it datagrams.
    CHECK_FALSE(introduced("8.8.8.8:53"));
    CHECK_FALSE(introduced("172.32.0.1:4000"));
    CHECK_FALSE(introduced("192.169.0.1:4000"));
    CHECK_FALSE(introduced("11.0.0.1:4000"));
    // The private and link-local ranges are, and this machine for a game that asked from it.
    CHECK(introduced("10.1.2.3:4000"));
    CHECK(introduced("172.16.0.1:4000"));
    CHECK(introduced("172.31.255.1:4000"));
    CHECK(introduced("192.168.1.20:4000"));
    CHECK(introduced("169.254.7.7:4000"));
    CHECK(introduced("127.0.0.1:4000"));

    // The same for the address a host gives for itself, which every joining game sends datagrams to.
    LobbyTalker otherHost;
    const Engine::HostRegisteredMessage abroad =
        registerSession(lobby, otherHost, 5, "Abroad", 0, addressOf("8.8.4.4:9"));
    CHECK_FALSE(askToJoin(lobby, guest, abroad.code, ++nonce, false).hostLocalAddress.valid());
    registerSession(lobby, otherHost, 6, "At home", abroad.sessionKey, addressOf("192.168.1.10:27900"));
    CHECK((askToJoin(lobby, guest, abroad.code, ++nonce, false).hostLocalAddress == addressOf("192.168.1.10:27900")));
    registerSession(lobby, otherHost, 7, "Abroad again", abroad.sessionKey, addressOf("1.1.1.1:53"));
    CHECK_FALSE(askToJoin(lobby, guest, abroad.code, ++nonce, false).hostLocalAddress.valid());
}

TEST_CASE("co-op net: a lobby remembers the allowance of a bounded number of addresses, the busy ones longest")
{
    // One request a second, two at once, four addresses remembered.
    Engine::RequestLimiter limiter;
    limiter.configure(1, 2, 4);
    bool firstRefusal = false;
    CHECK(limiter.allow(1, 1000, firstRefusal));
    CHECK(limiter.allow(1, 1000, firstRefusal));
    CHECK_FALSE(limiter.allow(1, 1000, firstRefusal));
    CHECK(firstRefusal);
    CHECK_FALSE(limiter.allow(1, 1000, firstRefusal));
    CHECK_FALSE(firstRefusal);
    // What it did not use comes back with time.
    CHECK(limiter.allow(1, 2100, firstRefusal));
    CHECK_FALSE(limiter.allow(1, 2100, firstRefusal));

    // A thousand other addresses, as a flood with forged ones brings: four stay remembered.
    bool allAnswered = true;

    for (uint32_t host = 100; host < 1100; ++host)
    {
        allAnswered = limiter.allow(host, 2101, firstRefusal) && allAnswered;
    }

    CHECK(allAnswered);
    CHECK(limiter.size() == 4);

    // An address that keeps asking is not the one forgotten: it stays refused while three new ones come.
    CHECK(limiter.allow(7, 2102, firstRefusal));
    CHECK(limiter.allow(7, 2102, firstRefusal));
    CHECK_FALSE(limiter.allow(7, 2102, firstRefusal));
    CHECK(limiter.allow(2000, 2102, firstRefusal));
    CHECK(limiter.allow(2001, 2102, firstRefusal));
    CHECK(limiter.allow(2002, 2102, firstRefusal));
    CHECK_FALSE(limiter.allow(7, 2103, firstRefusal));
    CHECK(limiter.size() == 4);
    // Four new ones after it was last heard from push it out; all it gains is a whole allowance.
    CHECK(limiter.allow(2010, 2103, firstRefusal));
    CHECK(limiter.allow(2011, 2103, firstRefusal));
    CHECK(limiter.allow(2012, 2103, firstRefusal));
    CHECK(limiter.allow(2013, 2103, firstRefusal));
    CHECK(limiter.allow(7, 2104, firstRefusal));
    CHECK(limiter.size() == 4);

    // Addresses not heard from for the idle time are forgotten.
    limiter.expire(2104 + 30000, 60000);
    CHECK(limiter.size() == 4);
    limiter.expire(2104 + 60001, 60000);
    CHECK(limiter.size() == 0);

    // Without a limit nothing is remembered.
    limiter.configure(0, 0, 4);
    CHECK(limiter.allow(1, 1000, firstRefusal));
    CHECK(limiter.size() == 0);
}

TEST_CASE("co-op net: a host's heartbeats are answered while its address has asked too much")
{
    // Three requests at once and one a second after that, for an address and for a session's key each.
    Engine::RendezvousServerConfig config;
    config.requestsPerSecond = 1;
    config.requestBurst = 3;
    TestLobby lobby(config);
    LobbyTalker host;
    LobbyTalker flood;
    LobbyTalker newcomer;
    const Engine::HostRegisteredMessage mine = registerSession(lobby, host, 1, "Mine");

    // Another game at the host's address (behind the same router) asks for the list far too often.
    listSessions(lobby, flood);

    for (uint32_t request = 0; request < 10; ++request)
    {
        Engine::ListRequestMessage again;
        again.nonce = 100 + request;
        again.cookie = flood.cookie;
        flood.socket.sendDatagram(lobby.address, Engine::encode(again));
    }

    lobby.runFor({&flood}, 30);
    CHECK(lobby.server.stats().refusedRequests >= 8);
    CHECK(lobby.server.stats().sessions == 1);

    // The address has nothing left: a first registration from it gets the cookie, and with the cookie nothing.
    CHECK_FALSE((askLobby<Engine::HostRegisterMessage, Engine::HostRegisteredMessage>(
        lobby, newcomer, registration(50, "Late"), lobby.address).has_value()));
    CHECK(newcomer.cookie != 0);
    lobby.runFor({&newcomer}, 30);
    CHECK_FALSE(newcomer.last<Engine::HostRegisteredMessage>().has_value());
    CHECK(lobby.server.stats().sessions == 1);

    // The heartbeat carries the session's key and is counted against the session: answered.
    const Engine::HostRegisteredMessage beat = registerSession(lobby, host, 2, "Mine", mine.sessionKey);
    CHECK(beat.sessionKey == mine.sessionKey);

    // The key's own allowance is bounded as well: of six more at once, two are left to be answered.
    host.received.clear();

    for (uint32_t request = 0; request < 6; ++request)
    {
        Engine::HostRegisterMessage heartbeat;
        heartbeat.nonce = 10 + request;
        heartbeat.sessionKey = mine.sessionKey;
        host.socket.sendDatagram(lobby.address, Engine::encode(heartbeat));
    }

    lobby.runFor({&host}, 30);
    CHECK(host.count<Engine::HostRegisteredMessage>() == 2);
}

TEST_CASE("co-op net: an address holds one relay port, and a session's joiners their share, not all of them")
{
    // As the service runs: sixteen ports, one for an address, four for a session.
    Engine::RendezvousServerConfig config;
    CHECK(config.relayPortCount == 16);
    CHECK(config.maxRelaysPerAddress == 1);
    CHECK(config.maxRelaysPerSession == 4);
    config.requestsPerSecond = 0;
    TestLobby lobby(config);
    LobbyTalker hostA;
    LobbyTalker hostB;
    LobbyTalker guest;
    const Engine::HostRegisteredMessage sessionA = registerSession(lobby, hostA, 1, "A");
    const Engine::HostRegisteredMessage sessionB = registerSession(lobby, hostB, 2, "B");

    // Ten requests from one address (every socket of this test is at one), to two sessions: one port in use.
    for (uint32_t nonce = 1; nonce <= 10; ++nonce)
    {
        const Engine::SessionCode &code = nonce % 2 == 0 ? sessionA.code : sessionB.code;
        const Engine::JoinReplyMessage reply = askToJoin(lobby, guest, code, nonce, true);
        CHECK((reply.status == Engine::JoinStatus::Ok));
        CHECK(reply.relayPort != 0);
        CHECK(lobby.server.stats().relaysInUse == 1);
    }

    // The repeat of the newest request is given the port it has; an older request's port is gone.
    const Engine::JoinReplyMessage newest = askToJoin(lobby, guest, sessionA.code, 10, true);
    CHECK(newest.relayPort != 0);
    CHECK(askToJoin(lobby, guest, sessionB.code, 9, true).relayPort == 0);
    CHECK(lobby.server.stats().relaysInUse == 1);

    // Once both sides have bound to the port it carries a game, and the address's next request does not take it
    // away: that one is told there is no port for it.
    hostA.received.clear();
    const Engine::JoinReplyMessage carried = askToJoin(lobby, guest, sessionA.code, 11, true);
    REQUIRE(bindRelay(lobby, hostA, guest, carried, introductionTo(lobby, hostA)));
    CHECK((askToJoin(lobby, guest, sessionB.code, 12, true).status == Engine::JoinStatus::RelayUnavailable));
    CHECK(lobby.server.stats().relaysInUse == 1);
    // A join that asks for no relay port is not held up by any of this.
    CHECK((askToJoin(lobby, guest, sessionB.code, 13, false).status == Engine::JoinStatus::Ok));
}

TEST_CASE("co-op net: the joiners of one session hold so many relay ports and no more")
{
    Engine::RendezvousServerConfig config;
    config.relayPortCount = 4;
    config.requestsPerSecond = 0;
    config.maxRelaysPerSession = 2;
    config.maxRelaysPerAddress = 4;
    TestLobby lobby(config);
    LobbyTalker hostA;
    LobbyTalker hostB;
    LobbyTalker guest;
    const Engine::HostRegisteredMessage sessionA = registerSession(lobby, hostA, 1, "A");
    const Engine::HostRegisteredMessage sessionB = registerSession(lobby, hostB, 2, "B");

    // Two joiners of A, each with both sides bound: ports that carry games.
    for (uint32_t nonce = 1; nonce <= 2; ++nonce)
    {
        hostA.received.clear();
        const Engine::JoinReplyMessage reply = askToJoin(lobby, guest, sessionA.code, nonce, true);
        REQUIRE(reply.relayPort != 0);
        REQUIRE(bindRelay(lobby, hostA, guest, reply, introductionTo(lobby, hostA)));
    }

    CHECK(lobby.server.stats().relaysInUse == 2);
    // The session has its two; another session still gets one.
    CHECK((askToJoin(lobby, guest, sessionA.code, 3, true).status == Engine::JoinStatus::RelayUnavailable));
    CHECK((askToJoin(lobby, guest, sessionB.code, 4, true).status == Engine::JoinStatus::Ok));
    CHECK(lobby.server.stats().relaysInUse == 3);
}

TEST_CASE("co-op net: a relay port that both sides did not bind to is taken back in a few seconds")
{
    Engine::RendezvousServerConfig config;
    config.relayPortCount = 2;
    config.requestsPerSecond = 0;
    config.relayBindTimeoutMs = 400;
    // Two for the one address every socket of this test is at.
    config.maxRelaysPerAddress = 2;
    TestLobby lobby(config);
    LobbyTalker host;
    LobbyTalker guest;
    const Engine::HostRegisteredMessage session = registerSession(lobby, host, 1, "A session");

    // One port that both sides bind to, as two games do.
    host.received.clear();
    const Engine::JoinReplyMessage bound = askToJoin(lobby, guest, session.code, 1, true);
    REQUIRE(bound.relayPort != 0);
    REQUIRE(bindRelay(lobby, host, guest, bound, introductionTo(lobby, host)));

    // And one that only the lobby knows of: asked for and never bound, as by a game that gave up.
    const Engine::JoinReplyMessage unbound = askToJoin(lobby, guest, session.code, 2, true);
    CHECK(unbound.relayPort != 0);
    CHECK(unbound.relayPort != bound.relayPort);
    CHECK(lobby.server.stats().relaysInUse == 2);

    lobby.runFor({&host, &guest}, 900);
    CHECK(lobby.server.stats().relaysInUse == 1);

    // The port taken back is given out again; the repeat of the request that lost it is not told another's.
    const Engine::JoinReplyMessage next = askToJoin(lobby, guest, session.code, 3, true);
    CHECK(next.relayPort == unbound.relayPort);
    CHECK(next.relayToken != unbound.relayToken);
    const Engine::JoinReplyMessage late = askToJoin(lobby, guest, session.code, 2, true);
    CHECK(late.relayPort == 0);
    CHECK(late.relayToken == 0);
}

TEST_CASE("co-op net: an address has a share of a lobby's sessions")
{
    Engine::RendezvousServerConfig config;
    config.requestsPerSecond = 0;
    config.maxSessionsPerAddress = 2;
    TestLobby lobby(config);
    LobbyTalker hosts[3];
    LobbyTalker asker;
    const Engine::HostRegisteredMessage sessionA = registerSession(lobby, hosts[0], 1, "A");
    const Engine::HostRegisteredMessage sessionB = registerSession(lobby, hosts[1], 2, "B");
    CHECK(lobby.server.stats().sessions == 2);

    // The address is full: a third registration gets the cookie and, with it, no session.
    CHECK_FALSE((askLobby<Engine::HostRegisterMessage, Engine::HostRegisteredMessage>(
        lobby, hosts[2], registration(3, "C"), lobby.address).has_value()));
    CHECK(hosts[2].cookie != 0);
    CHECK(lobby.server.stats().sessions == 2);
    const std::vector<Engine::SessionListEntry> listed = listSessions(lobby, asker);
    CHECK(listed.size() == 2);
    CHECK(nameOfSession(listed, sessionA.code) == "A");
    CHECK(nameOfSession(listed, sessionB.code) == "B");

    // A goodbye with the key ends a session only from where the session is.
    Engine::HostUnregisterMessage goodbye;
    goodbye.sessionKey = sessionB.sessionKey;
    hosts[2].socket.sendDatagram(lobby.address, Engine::encode(goodbye));
    lobby.runFor({&hosts[2]}, 30);
    CHECK(lobby.server.stats().sessions == 2);
    hosts[1].socket.sendDatagram(lobby.address, Engine::encode(goodbye));
    lobby.runFor({&hosts[1]}, 30);
    CHECK(lobby.server.stats().sessions == 1);

    // And there is a place again.
    registerSession(lobby, hosts[2], 3, "C");
    CHECK(lobby.server.stats().sessions == 2);
}

TEST_CASE("co-op net: a lobby does nothing for an address that has not sent its cookie back")
{
    // What a datagram with a forged sender address can do: it never sees the cookie, which goes to that address.
    Engine::RendezvousServerConfig config;
    config.requestsPerSecond = 1;
    config.requestBurst = 3;
    TestLobby lobby(config);
    LobbyTalker host;
    LobbyTalker other;
    LobbyTalker asker;

    // A registration without a cookie, with a wrong one and with another address's: the cookie in answer, and no
    // session, however often.
    other.socket.sendDatagram(lobby.address, Engine::encode(registration(1, "Elsewhere")));
    REQUIRE(lobby.run({&other}, [&other]() { return other.last<Engine::AddressCookieMessage>().has_value(); }));
    const uint64_t othersCookie = other.last<Engine::AddressCookieMessage>()->cookie;
    CHECK(othersCookie != 0);

    for (const uint64_t cookie : {uint64_t(0), uint64_t(12345), othersCookie, othersCookie + 1})
    {
        Engine::HostRegisterMessage message = registration(2, "Forged");
        message.cookie = cookie;

        for (int repeat = 0; repeat < 20; ++repeat)
        {
            host.socket.sendDatagram(lobby.address, Engine::encode(message));
        }

        lobby.runFor({&host}, 20);
        CHECK(lobby.server.stats().sessions == 0);
        CHECK_FALSE(host.last<Engine::HostRegisteredMessage>().has_value());
        REQUIRE(host.last<Engine::AddressCookieMessage>().has_value());
        CHECK(host.last<Engine::AddressCookieMessage>()->nonce == 2);
        // The answer is smaller than any request, and the same every time: nothing is kept for it.
        CHECK(Engine::encode(*host.last<Engine::AddressCookieMessage>()).size() < Engine::encode(message).size());
    }

    CHECK(host.last<Engine::AddressCookieMessage>()->cookie != othersCookie);
    // None of the eighty counted against the address: it has its whole allowance, and nothing was refused.
    CHECK(lobby.server.stats().refusedRequests == 0);
    CHECK(listSessions(lobby, asker).empty());

    // With its own cookie the host has a session at once, listed and to be joined.
    const Engine::HostRegisteredMessage session = registerSession(lobby, host, 2, "Real");
    CHECK(lobby.server.stats().sessions == 1);
    CHECK(nameOfSession(listSessions(lobby, asker), session.code) == "Real");

    // A join request without the cookie: the cookie in answer, nothing told to the host, nothing remembered.
    host.received.clear();
    Engine::JoinRequestMessage join;
    join.nonce = 7;
    join.code = session.code;
    join.wantRelay = true;
    other.received.clear();
    other.socket.sendDatagram(lobby.address, Engine::encode(join));
    lobby.runFor({&other, &host}, 30);
    CHECK(other.last<Engine::AddressCookieMessage>().has_value());
    CHECK_FALSE(other.last<Engine::JoinReplyMessage>().has_value());
    CHECK_FALSE(host.last<Engine::PeerIntroMessage>().has_value());
    CHECK(lobby.server.stats().relaysInUse == 0);

    // The same for the list.
    Engine::ListRequestMessage list;
    list.nonce = 8;
    other.received.clear();
    other.socket.sendDatagram(lobby.address, Engine::encode(list));
    lobby.runFor({&other}, 30);
    CHECK(other.last<Engine::AddressCookieMessage>().has_value());
    CHECK_FALSE(other.last<Engine::ListReplyMessage>().has_value());
    CHECK(lobby.server.stats().refusedRequests == 0);
}

TEST_CASE("co-op net: a session moves only to an address that sent its cookie back")
{
    Engine::RendezvousServerConfig config;
    config.requestsPerSecond = 0;
    TestLobby lobby(config);
    LobbyTalker host;
    LobbyTalker elsewhere;
    LobbyTalker guest;
    const Engine::HostRegisteredMessage session = registerSession(lobby, host, 1, "Mine");
    const uint16_t ownPort = host.socket.localPort();
    CHECK(askToJoin(lobby, guest, session.code, 1, false).hostPublicAddress.port == ownPort);

    // The key from another address, as somebody who has the key sends it with a sender address of his choosing:
    // that address gets its cookie, and the session stays where it is.
    elsewhere.socket.sendDatagram(lobby.address, Engine::encode(registration(2, "Moved", session.sessionKey)));
    REQUIRE(lobby.run({&elsewhere}, [&elsewhere]()
    {
        return elsewhere.last<Engine::AddressCookieMessage>().has_value();
    }));
    lobby.runFor({&elsewhere}, 20);
    CHECK_FALSE(elsewhere.last<Engine::HostRegisteredMessage>().has_value());
    CHECK(askToJoin(lobby, guest, session.code, 2, false).hostPublicAddress.port == ownPort);
    CHECK(nameOfSession(listSessions(lobby, guest), session.code) == "Mine");

    // The host itself at a new address (its router gave it another port) sends the cookie back and has moved.
    const Engine::HostRegisteredMessage moved = registerSession(lobby, elsewhere, 3, "Moved", session.sessionKey);
    CHECK(moved.sessionKey == session.sessionKey);
    CHECK((moved.code == session.code));
    CHECK(askToJoin(lobby, guest, session.code, 3, false).hostPublicAddress.port == elsewhere.socket.localPort());
    CHECK(lobby.server.stats().sessions == 1);
}

TEST_CASE("co-op net: a relay port forwards only between the two addresses that asked for it")
{
    // Needs a second address of this machine: datagrams sent to the lobby at the machine's address on its network
    // come from that address, the others from 127.0.0.1.
    Engine::RendezvousServerConfig config;
    config.relayPortCount = 2;
    config.requestsPerSecond = 0;
    config.maxSessionsPerAddress = 1;
    TestLobby lobby(config);
    LobbyTalker host;
    LobbyTalker guest;
    LobbyTalker stranger;
    const Engine::HostRegisteredMessage session = registerSession(lobby, host, 1, "A session");
    host.received.clear();
    const Engine::JoinReplyMessage reply = askToJoin(lobby, guest, session.code, 1, true);
    const Engine::PeerIntroMessage intro = introductionTo(lobby, host);
    REQUIRE(reply.relayPort != 0);

    Engine::NetAddress lobbyOnNetwork = Engine::localAddressTowards(addressOf("8.8.8.8:53"));
    lobbyOnNetwork.port = lobby.address.port;
    Engine::JoinRequestMessage probe;
    probe.nonce = 50;
    probe.code = *Engine::parseSessionCode("ZZZZZZ");
    const std::optional<Engine::JoinReplyMessage> seen = lobbyOnNetwork.valid()
        ? askLobby<Engine::JoinRequestMessage, Engine::JoinReplyMessage>(lobby, stranger, probe, lobbyOnNetwork)
        : std::nullopt;

    if (!seen || seen->clientPublicAddress.host == lobby.address.host)
    {
        MESSAGE("this machine has no second address: the stranger's part is not checked");
    }
    else
    {
        // The stranger has the joining game's token (as one who asked for the port from a forged address would
        // not even have, but one who was told it might), and binds from its own address: not answered.
        const Engine::NetAddress relayOnNetwork{lobbyOnNetwork.host, reply.relayPort};
        Engine::RelayBindMessage bind;
        bind.token = reply.relayToken;
        stranger.received.clear();
        stranger.socket.sendDatagram(relayOnNetwork, Engine::encode(bind, Engine::RendezvousMessage::RelayBind));
        bind.token = intro.relayToken;
        stranger.socket.sendDatagram(relayOnNetwork, Engine::encode(bind, Engine::RendezvousMessage::RelayBind));
        lobby.runFor({&stranger}, 40);
        CHECK_FALSE(stranger.last<Engine::RelayBindMessage>().has_value());

        // A session of another address does not move onto an address that has its share of sessions: one real
        // address cannot put sessions wherever it likes.
        const std::optional<Engine::HostRegisteredMessage> theirs = askLobby<Engine::HostRegisterMessage,
            Engine::HostRegisteredMessage>(lobby, stranger, registration(60, "Theirs"), lobbyOnNetwork);
        REQUIRE(theirs.has_value());
        CHECK(lobby.server.stats().sessions == 2);
        LobbyTalker mover;
        CHECK_FALSE((askLobby<Engine::HostRegisterMessage, Engine::HostRegisteredMessage>(
            lobby, mover, registration(61, "Theirs", theirs->sessionKey), lobby.address).has_value()));
        CHECK(mover.cookie != 0);
        CHECK(askToJoin(lobby, guest, theirs->code, 2, false).hostPublicAddress.host == lobbyOnNetwork.host);
    }

    // The two that asked bind, and what one sends reaches the other and nobody else.
    REQUIRE(bindRelay(lobby, host, guest, reply, intro));
    const Engine::NetAddress relay{lobby.address.host, reply.relayPort};
    const std::vector<uint8_t> word = {'h', 'e', 'l', 'l', 'o'};
    guest.received.clear();
    host.socket.sendDatagram(relay, word);
    REQUIRE(lobby.run({&guest, &stranger}, [&guest]() { return !guest.received.empty(); }));
    CHECK(guest.received.front() == word);
    lobby.runFor({&stranger}, 20);
    CHECK(std::count(stranger.received.begin(), stranger.received.end(), word) == 0);
    CHECK(lobby.server.stats().relayedDatagrams == 1);
}

TEST_CASE("co-op net: a joining game takes the answer to its punch only from the host the lobby named")
{
    const Engine::NetAddress lobby{0x0A0B0C0Du, 27910};
    const Engine::NetAddress hostPublic{0x04030201u, 5000};
    const Engine::NetAddress hostLocal{0x0A01A8C0u, 5000};
    SentDatagrams sent;
    Engine::RendezvousClient guest(sent.sender(), lobby);
    guest.startJoin(*Engine::parseSessionCode("ABCDEF"), Engine::NetAddress{}, false);
    guest.update(1000);
    REQUIRE(sent.datagrams.size() == 1);
    Engine::JoinRequestMessage request;
    REQUIRE(Engine::decode(sent.datagrams.front().second, request));

    Engine::JoinReplyMessage reply;
    reply.nonce = request.nonce;
    reply.hostPublicAddress = hostPublic;
    reply.hostLocalAddress = hostLocal;
    guest.handleDatagram(lobby, Engine::encode(reply), 1010);
    REQUIRE((guest.joinState() == Engine::JoinState::OpeningPath));
    guest.update(1020);
    CHECK(sent.punches(hostPublic.host) == 1);
    CHECK(sent.punches(hostLocal.host) == 1);

    // The right number from an address the lobby did not name: somebody who learnt or guessed the number.
    Engine::PunchMessage answer;
    answer.id = request.nonce;
    answer.isAck = true;
    guest.handleDatagram(Engine::NetAddress{0x09090909u, 5000}, Engine::encode(answer), 1030);
    CHECK((guest.joinState() == Engine::JoinState::OpeningPath));
    guest.handleDatagram(Engine::NetAddress{hostLocal.host, 5001}, Engine::encode(answer), 1030);
    CHECK((guest.joinState() == Engine::JoinState::OpeningPath));

    // The host's public address, from another port than the lobby saw (a router that gives every destination its
    // own): that is the host, and the path.
    const Engine::NetAddress arrivedFrom{hostPublic.host, 5077};
    guest.handleDatagram(arrivedFrom, Engine::encode(answer), 1040);
    CHECK((guest.joinState() == Engine::JoinState::Ready));
    CHECK((guest.joinPath() == Engine::JoinPath::Direct));
    CHECK((guest.joinAddress() == arrivedFrom));
}

TEST_CASE("co-op net: a host punches towards a bounded number of joining games, of one address and in all")
{
    const Engine::NetAddress lobby{0x0A0B0C0Du, 27910};
    const uint32_t victim = 0x04030201u;
    SentDatagrams sent;
    Engine::RendezvousClient host(sent.sender(), lobby);
    host.startHosting(Engine::SessionInfo{}, Engine::NetAddress{});
    host.update(1000);
    REQUIRE(sent.datagrams.size() == 1);
    Engine::HostRegisterMessage registration;
    REQUIRE(Engine::decode(sent.datagrams.front().second, registration));
    Engine::HostRegisteredMessage registered;
    registered.nonce = registration.nonce;
    registered.sessionKey = 77;
    registered.code = *Engine::parseSessionCode("ABCDEF");
    host.handleDatagram(lobby, Engine::encode(registered), 1001);
    REQUIRE(host.registered());

    // Ten games at one address ask to join at once.
    for (uint32_t index = 0; index < 10; ++index)
    {
        Engine::PeerIntroMessage intro;
        intro.sessionKey = 77;
        intro.introId = 100 + index;
        intro.clientPublicAddress = Engine::NetAddress{victim, uint16_t(4000 + index)};
        host.handleDatagram(lobby, Engine::encode(intro), 1100);
    }

    sent.datagrams.clear();
    host.update(1200);
    CHECK(sent.punches(victim) == 3);

    // And from thirty addresses more: twelve games are punched at a time, whoever they are.
    for (uint32_t index = 0; index < 30; ++index)
    {
        Engine::PeerIntroMessage intro;
        intro.sessionKey = 77;
        intro.introId = 200 + index;
        intro.clientPublicAddress = Engine::NetAddress{0x0B000001u + (index << 8), 4000};
        host.handleDatagram(lobby, Engine::encode(intro), 1200);
    }

    sent.datagrams.clear();
    host.update(1400);
    CHECK(sent.punches() == 12);
    CHECK(sent.punches(victim) == 3);

    // A game that asked for a relay port is sent no punches; the host binds to the port at the lobby.
    Engine::PeerIntroMessage relayed;
    relayed.sessionKey = 77;
    relayed.introId = 300;
    relayed.clientPublicAddress = Engine::NetAddress{0x0C000001u, 4000};
    relayed.relayPort = 27911;
    relayed.relayToken = 5;
    host.handleDatagram(lobby, Engine::encode(relayed), 1400);
    sent.datagrams.clear();
    host.update(1600);
    CHECK(sent.punches(0x0C000001u) == 0);
    CHECK(std::any_of(sent.datagrams.begin(), sent.datagrams.end(),
        [&lobby](const std::pair<Engine::NetAddress, std::vector<uint8_t>> &datagram)
        {
            Engine::RelayBindMessage bind;
            return Engine::decode(datagram.second, bind) && bind.token == 5
                && (datagram.first == Engine::NetAddress{lobby.host, 27911});
        }));

    // When the punches' time is over the places are free again.
    host.update(8000);
    Engine::PeerIntroMessage later;
    later.sessionKey = 77;
    later.introId = 400;
    later.clientPublicAddress = Engine::NetAddress{victim, 4000};
    host.handleDatagram(lobby, Engine::encode(later), 8000);
    sent.datagrams.clear();
    host.update(8200);
    CHECK(sent.punches(victim) == 1);
    CHECK(sent.punches() == 1);
}

TEST_CASE("co-op net: a host acts on an introduction only with its session's key, and answers only whom it names")
{
    const Engine::NetAddress lobby{0x0A0B0C0Du, 27910};
    const Engine::NetAddress joiner{0x04030201u, 4000};
    // 192.168.1.20 and 8.8.8.8, as NetAddress keeps a host: the first number in the lowest byte.
    const Engine::NetAddress ownNetwork{0x1401A8C0u, 4000};
    const Engine::NetAddress anybody{0x08080808u, 53};
    SentDatagrams sent;
    Engine::RendezvousClient host(sent.sender(), lobby);
    host.startHosting(Engine::SessionInfo{}, Engine::NetAddress{});
    host.update(1000);
    REQUIRE(sent.datagrams.size() == 1);
    Engine::HostRegisterMessage registration;
    REQUIRE(Engine::decode(sent.datagrams.front().second, registration));
    CHECK(registration.cookie == 0);

    // The lobby's cookie first: the registration is said again at once, with the cookie.
    Engine::AddressCookieMessage cookie;
    cookie.nonce = registration.nonce;
    cookie.cookie = 4242;
    host.handleDatagram(lobby, Engine::encode(cookie), 1001);
    sent.datagrams.clear();
    host.update(1002);
    REQUIRE(sent.datagrams.size() == 1);
    REQUIRE(Engine::decode(sent.datagrams.front().second, registration));
    CHECK(registration.cookie == 4242);
    Engine::HostRegisteredMessage registered;
    registered.nonce = registration.nonce;
    registered.sessionKey = 77;
    registered.code = *Engine::parseSessionCode("ABCDEF");
    host.handleDatagram(lobby, Engine::encode(registered), 1003);
    REQUIRE(host.registered());

    // Introductions with the lobby's address as their sender (which can be forged) and no key, or a wrong one:
    // nothing is sent anywhere, for as long as punches would last.
    for (uint32_t index = 0; index < 12; ++index)
    {
        Engine::PeerIntroMessage forged;
        forged.sessionKey = index % 2 == 0 ? 0 : 78;
        forged.introId = 1000 + index;
        forged.clientPublicAddress = Engine::NetAddress{0x09090909u + (index << 24), 53};
        forged.clientLocalAddress = anybody;
        host.handleDatagram(lobby, Engine::encode(forged), 1100);
    }

    sent.datagrams.clear();

    for (uint32_t nowMs = 1200; nowMs < 4000; nowMs += 100)
    {
        host.update(nowMs);
    }

    CHECK(sent.punches() == 0);

    // A punch from somebody the lobby did not introduce is not answered either.
    Engine::PunchMessage punch;
    punch.id = 5;

    for (int index = 0; index < 100; ++index)
    {
        host.handleDatagram(joiner, Engine::encode(punch), 4000);
    }

    CHECK(sent.punches() == 0);

    // The lobby's own introduction, which says the game's own-network address is anybody's on the internet:
    // punches go to the public address and not there.
    Engine::PeerIntroMessage intro;
    intro.sessionKey = 77;
    intro.introId = 1;
    intro.clientPublicAddress = joiner;
    intro.clientLocalAddress = anybody;
    host.handleDatagram(lobby, Engine::encode(intro), 4000);
    sent.datagrams.clear();
    host.update(4100);
    CHECK(sent.punches(joiner.host) == 1);
    CHECK(sent.punches(anybody.host) == 0);
    CHECK(sent.punches() == 1);

    // An address of its own network is punched as well.
    intro.introId = 2;
    intro.clientPublicAddress = Engine::NetAddress{0x05030201u, 4000};
    intro.clientLocalAddress = ownNetwork;
    host.handleDatagram(lobby, Engine::encode(intro), 4100);
    sent.datagrams.clear();
    host.update(4200);
    CHECK(sent.punches(ownNetwork.host) == 1);
    CHECK(sent.punches() == 3);

    // The introduced game's punches are answered, from whatever port they come, and only so many a second.
    sent.datagrams.clear();

    for (int index = 0; index < 100; ++index)
    {
        host.handleDatagram(Engine::NetAddress{joiner.host, 4999}, Engine::encode(punch), 4250);
    }

    CHECK(sent.punches(joiner.host) == 20);
    host.handleDatagram(anybody, Engine::encode(punch), 4250);
    CHECK(sent.punches(anybody.host) == 0);
    // After the punches' time the game is nobody again.
    sent.datagrams.clear();
    host.handleDatagram(joiner, Engine::encode(punch), 4100 + 6000);
    CHECK(sent.punches() == 0);
}

TEST_CASE("co-op net: a question to the local network is as long as the longest answer to it")
{
    // A host answers only a whole question, so nobody is sent more than whoever asked in his name sent.
    Engine::LanSessionInfo info;
    info.name = std::string(200, 'n');
    info.world = std::string(200, 'w');
    info.ruleset = std::string(200, 'r');
    const std::vector<uint8_t> question = Engine::encodeLanProbe(4711);
    const std::vector<uint8_t> answer = Engine::encodeLanAnswer(4711, info);
    CHECK(question.size() >= answer.size());
    CHECK(Engine::decodeLanProbe(question).has_value());
    CHECK_FALSE(Engine::decodeLanProbe(std::span<const uint8_t>(question.data(), question.size() - 1)).has_value());
    CHECK_FALSE(Engine::decodeLanProbe(std::span<const uint8_t>(question.data(), 10)).has_value());
}

TEST_CASE("co-op net: ending a connection that is still being made is told, and its id is not used again")
{
    Engine::EnetTransport socket;
    REQUIRE(socket.open(0, 1));
    // Nobody answers there, so the connection stays in the making.
    const Engine::NetAddress nobody = addressOf("127.0.0.1:9");
    const Engine::NetPeerId first = socket.connect(nobody);
    REQUIRE(first != Engine::InvalidNetPeer);
    socket.disconnect(first);
    Engine::NetEvent event;
    REQUIRE(socket.pollEvent(event));
    CHECK((event.type == Engine::NetEvent::Type::Disconnected));
    CHECK(event.peer == first);
    CHECK_FALSE(socket.pollEvent(event));

    // The one place is free again, and whoever takes it is another peer.
    const Engine::NetPeerId second = socket.connect(nobody);
    REQUIRE(second != Engine::InvalidNetPeer);
    CHECK(second != first);
    // The old id names nobody: ending it again does nothing to the new connection.
    socket.disconnect(first);
    CHECK_FALSE(socket.pollEvent(event));
    CHECK((socket.peerAddress(second) == nobody));
}
