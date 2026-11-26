#include "game/tables/WebOfWorldsTable.h"
#include "game/party/CampaignState.h"

#include <doctest/doctest.h>

#include <set>
#include <string>

using namespace OpenYAMM::Game;

namespace
{
const char *const HesperFixture = R"(
unlock_qbits: [784, 783, 228]
locked_hint: The gate web is silent.
open_hint: Travel between worlds.
known_worlds:
  - {name: Enroth, subtitle: "Enroth · Antagarich · Jadame", position: [130, 280], radius: 13,
     continents: [TPEnroth, Antagrich, townport]}
  - {name: Xeen, position: [75, 195], continents: [TPCloudside, TPDarkside]}
planets:
  - key: hesper
    world: Hesper
    name: Hesper
    icon: HH_Web_Planet
    cleared_icon: HH_Cleansed
    position: [275, 195]
    threat: 4
    cleared_qbit: 60099
    counters:
      - {label: Regions purged, qbits: [60001, 60002, 60003, 60004]}
      - {label: Directives, qbits: [60010, 60011]}
    beacons:
      - {name: Gate Mesa, map: HH_Cinder.odm, position: [100, 200, 300], direction: 90}
      - {name: Creepmire beacon, map: hh_creep.odm, lit_qbit: 60001}
      - {name: The Crown, map: hh_crown.odm, lit_qbit: 60004}
    signals:
      - {name: Signal II, icon: HH_Signal, cleared_name: "Signal II · a frozen moon", position: [335, 325], radius: 8}
)";

WebOfWorldsQBitQuery partyWith(const std::set<uint32_t> &qbits)
{
    return [qbits](uint32_t qbit) { return qbits.count(qbit) != 0; };
}

WebOfWorldsTable loaded(const char *pText)
{
    WebOfWorldsTable table;
    std::string error;
    REQUIRE_MESSAGE(table.appendFromYaml(pText, error), error);
    return table;
}
}

TEST_CASE("web of worlds: an empty table offers nothing")
{
    const WebOfWorldsTable table;
    CHECK(table.empty());
    CHECK_FALSE(table.isUnlocked(partyWith({784}), false));
}

TEST_CASE("web of worlds: the table reads planets, beacons and known worlds")
{
    const WebOfWorldsTable table = loaded(HesperFixture);
    REQUIRE(table.planets().size() == 1);
    const WebOfWorldsPlanet &planet = table.planets().front();
    CHECK(planet.worldId == "hesper");
    CHECK(planet.icon == "hh_web_planet");
    CHECK(planet.clearedIcon == "hh_cleansed");
    CHECK(planet.signals.at(0).icon == "hh_signal");
    CHECK(planet.beacons.size() == 3);
    CHECK(planet.beacons[0].mapFileName == "hh_cinder.odm");
    REQUIRE(planet.beacons[0].position.has_value());
    CHECK((*planet.beacons[0].position)[2] == 300);
    CHECK(planet.beacons[0].directionDegrees == 90);
    CHECK_FALSE(planet.beacons[1].position.has_value());
    CHECK(table.knownWorlds().size() == 2);
    CHECK(table.knownWorlds()[0].continents.size() == 3);
    CHECK(table.findPlanetByWorld("HESPER") == &planet);
    CHECK(table.findPlanetByWorld("mm6") == nullptr);
}

TEST_CASE("web of worlds: any campaign ending unlocks the tab, and a party on a planet always has it")
{
    const WebOfWorldsTable table = loaded(HesperFixture);
    CHECK_FALSE(table.isUnlocked(partyWith({}), false));
    CHECK_FALSE(table.isUnlocked(partyWith({785, 60001}), false));
    CHECK(table.isUnlocked(partyWith({784}), false));
    CHECK(table.isUnlocked(partyWith({783}), false));
    CHECK(table.isUnlocked(partyWith({228}), false));
    CHECK(table.isUnlocked(partyWith({}), true));
}

TEST_CASE("web of worlds: beacons light by their QBits, counters and the purge meter count the planet's QBits")
{
    const WebOfWorldsTable table = loaded(HesperFixture);
    const WebOfWorldsPlanet &planet = table.planets().front();

    const WebOfWorldsPlanetProgress fresh = webOfWorldsPlanetProgress(planet, partyWith({}));
    CHECK_FALSE(fresh.cleared);
    CHECK(fresh.purgePercent == 0);
    CHECK(fresh.litBeacons == std::vector<size_t>{0});
    REQUIRE(fresh.counters.size() == 2);
    CHECK(fresh.counters[0].total == 4);
    CHECK(fresh.counters[0].done == 0);

    const WebOfWorldsPlanetProgress mid = webOfWorldsPlanetProgress(planet, partyWith({60001, 60002, 60010}));
    CHECK(mid.litBeacons == std::vector<size_t>{0, 1});
    CHECK(mid.counters[0].done == 2);
    CHECK(mid.counters[1].done == 1);
    CHECK(mid.purgePercent == 50);

    const WebOfWorldsPlanetProgress cleared = webOfWorldsPlanetProgress(planet, partyWith({60004, 60099}));
    CHECK(cleared.cleared);
    CHECK(cleared.purgePercent == 100);
    CHECK(cleared.litBeacons == std::vector<size_t>{0, 2});
}

TEST_CASE("web of worlds: open chart progress updates on QBit changes, restores, and party or planet changes")
{
    const auto table = loaded(HesperFixture);
    const auto &planet = table.planets().front();
    CampaignState party;
    CampaignState otherParty;
    WebOfWorldsProgressReading reading;
    REQUIRE(reading.get(planet, nullptr).litBeacons == std::vector<size_t>{0});
    party.setQuestBit(60001, true);
    otherParty.setQuestBit(60004, true);
    REQUIRE(party.questRevision() == otherParty.questRevision());
    const auto &progress = reading.get(planet, &party);
    const auto saved = party.snapshot();
    REQUIRE(progress.litBeacons == std::vector<size_t>{0, 1});
    REQUIRE(progress.counters.size() == 2);
    CHECK(progress.counters[0].done == 1);
    const auto *pCounters = progress.counters.data();
    party.setQuestBit(60001, true);
    CHECK(reading.get(planet, &party).counters.data() == pCounters); // hovering reuses the same computed rows
    CHECK(reading.get(planet, &otherParty).litBeacons == std::vector<size_t>{0, 2});
    CHECK(reading.get(planet, &party).litBeacons == std::vector<size_t>{0, 1});
    party.setQuestBit(60099, true);
    CHECK(reading.get(planet, &party).purgePercent == 100);
    party.restoreSnapshot(saved);
    CHECK_FALSE(reading.get(planet, &party).cleared);
    party.setQuestBit(60001, false);
    CHECK(reading.get(planet, &party).litBeacons == std::vector<size_t>{0});
    CHECK(reading.get(planet, &otherParty).litBeacons == std::vector<size_t>{0, 2});
    WebOfWorldsPlanet sibling;
    sibling.clearedQBit = 60004;
    CHECK(reading.get(sibling, &otherParty).cleared);
    otherParty.resetForNewParty();
    CHECK_FALSE(reading.get(sibling, &otherParty).cleared);
}

TEST_CASE("web of worlds: contributions append, a planet twice is an error, bad rows are refused")
{
    WebOfWorldsTable table = loaded(HesperFixture);
    std::string error;
    CHECK_FALSE(table.appendFromYaml(HesperFixture, error));
    CHECK(error.find("twice") != std::string::npos);

    WebOfWorldsTable greeting;
    REQUIRE(greeting.appendFromYaml("first_open: {qbit: 60088, message: Wake, sound: seeker}", error));
    CHECK(greeting.firstOpen().qbit == 60088);
    CHECK(greeting.firstOpen().sound == "seeker");
    CHECK_FALSE(greeting.appendFromYaml("first_open: {qbit: 60089, message: Again}", error));

    WebOfWorldsTable other;
    CHECK_FALSE(other.appendFromYaml("planets:\n  - {key: x, world: x, name: X, position: [1, 2]}\n", error));
    CHECK(error.find("beacon") != std::string::npos);
    CHECK_FALSE(other.appendFromYaml("planets:\n  - {key: x, world: x, name: X}\n", error));
    CHECK_FALSE(other.appendFromYaml(
        "planets:\n  - {key: x, world: x, name: X, position: [1, 2],\n"
        "     beacons: [{name: B, map: m.odm, position: [1]}]}\n",
        error));

    WebOfWorldsTable second;
    REQUIRE(second.appendFromYaml(
        "planets:\n  - {key: y, world: y, name: Y, position: [1, 2], purge_qbits: [5, 6], counters: [{label: A, "
        "qbits: [1, 2, 3]}], beacons: [{name: B, map: m.odm}]}\n",
        error));
    CHECK(webOfWorldsPlanetProgress(second.planets()[0], partyWith({1, 2, 5})).purgePercent == 50);
}
