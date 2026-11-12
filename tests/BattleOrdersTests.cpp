#include "game/maps/SaveGame.h"
#include "game/party/BattleOrders.h"
#include "game/party/Party.h"

#include <doctest/doctest.h>

#include <chrono>
#include <filesystem>
#include <optional>
#include <string>

using namespace OpenYAMM::Game;

TEST_CASE("battle orders: melee reach and beyond meet exactly at the blow's reach")
{
    const BattleOrderDistance inReach = {0, BattleOrderMeleeReach};
    const BattleOrderDistance beyond = {BattleOrderMeleeReach, BattleOrderMaximumDistance};
    CHECK(battleOrderDistanceHolds(inReach, 0.0f));
    CHECK(battleOrderDistanceHolds(inReach, 407.2f));
    CHECK_FALSE(battleOrderDistanceHolds(inReach, 407.3f));
    CHECK_FALSE(battleOrderDistanceHolds(beyond, 407.2f));
    CHECK(battleOrderDistanceHolds(beyond, 407.3f));
    // The maximum distance means no limit.
    CHECK(battleOrderDistanceHolds(beyond, 9000.0f));
    CHECK(battleOrderDistanceHolds({0, 600}, 600.0f));
    CHECK_FALSE(battleOrderDistanceHolds({0, 600}, 601.0f));
    // Without a target a distance never holds.
    CHECK_FALSE(battleOrderDistanceHolds(inReach, std::nullopt));
}

TEST_CASE("battle orders: an ally's HP and the SP a cast keeps")
{
    BattleOrderSituation situation;
    situation.lowestAllyHealthShare = 0.4f;
    situation.spellPoints = 40;
    situation.maximumSpellPoints = 100;

    BattleOrder heal;
    heal.spellName = "Heal";
    heal.allyHealthBelowPercent = 50;
    CHECK(battleOrderConditionsHold(heal, situation, 5));
    heal.allyHealthBelowPercent = 40;
    CHECK_FALSE(battleOrderConditionsHold(heal, situation, 5));

    BattleOrder bolt;
    bolt.spellName = "Light Bolt";
    bolt.keepSpellPointsPercent = 30;
    // 40 - 10 leaves 30, the 30 % kept.
    CHECK(battleOrderConditionsHold(bolt, situation, 10));
    CHECK_FALSE(battleOrderConditionsHold(bolt, situation, 11));
    // Unconditional orders always hold; a weapon order ignores the SP it would keep.
    CHECK(battleOrderConditionsHold(BattleOrder{}, situation, 0));
    BattleOrder melee;
    melee.kind = BattleOrderKind::Melee;
    melee.keepSpellPointsPercent = 90;
    CHECK(battleOrderConditionsHold(melee, situation));
}

TEST_CASE("battle orders: an order for one place holds only there")
{
    BattleOrderSituation situation;
    BattleOrder sparks;
    sparks.spellName = "Sparks";
    situation.indoors = true;
    CHECK(battleOrderConditionsHold(sparks, situation));
    sparks.place = BattleOrderPlace::Indoors;
    CHECK(battleOrderConditionsHold(sparks, situation));
    sparks.place = BattleOrderPlace::Outdoors;
    CHECK_FALSE(battleOrderConditionsHold(sparks, situation));
    situation.indoors = false;
    CHECK(battleOrderConditionsHold(sparks, situation));
    sparks.place = BattleOrderPlace::Indoors;
    CHECK_FALSE(battleOrderConditionsHold(sparks, situation));
    // The weapon orders take a place too.
    BattleOrder shoot;
    shoot.kind = BattleOrderKind::Shoot;
    shoot.place = BattleOrderPlace::Outdoors;
    CHECK(battleOrderConditionsHold(shoot, situation));
    situation.indoors = true;
    CHECK_FALSE(battleOrderConditionsHold(shoot, situation));
}

TEST_CASE("upkeep: a buff is due when gone, or under its renew time and half of what a cast gives")
{
    const float hour = 3600.0f;
    // Without a renew time, only once it is gone.
    CHECK(upkeepBuffDue(0.0f, 5 * hour, std::nullopt));
    CHECK_FALSE(upkeepBuffDue(60.0f, 5 * hour, std::nullopt));
    // Renewed under 30 minutes left.
    CHECK(upkeepBuffDue(0.0f, 5 * hour, uint16_t(30)));
    CHECK(upkeepBuffDue(29 * 60.0f, 5 * hour, uint16_t(30)));
    CHECK_FALSE(upkeepBuffDue(30 * 60.0f, 5 * hour, uint16_t(30)));
    // A ten-minute buff is not cast again at every press: only once under half of it is left.
    CHECK_FALSE(upkeepBuffDue(10 * 60.0f, 10 * 60.0f, uint16_t(30)));
    CHECK_FALSE(upkeepBuffDue(5 * 60.0f, 10 * 60.0f, uint16_t(30)));
    CHECK(upkeepBuffDue(4 * 60.0f, 10 * 60.0f, uint16_t(30)));
}

TEST_CASE("battle orders: an older save's attack spell becomes one order")
{
    std::vector<BattleOrder> orders;
    BattleOrderFallback fallback = BattleOrderFallback::Weapon;
    setAttackSpell("", orders, fallback);
    CHECK(orders.empty());
    CHECK(fallback == BattleOrderFallback::Weapon);

    setAttackSpell("Lifedrain", orders, fallback);
    REQUIRE_EQ(orders.size(), 1);
    CHECK(orders.front().spellName == "Lifedrain");
    CHECK(orders.front().enabled);
    CHECK_FALSE(orders.front().distance.has_value());
    CHECK(fallback == BattleOrderFallback::Weapon);

    // A member spell held when nobody needed it (OY-190): it still holds rather than shoot.
    setAttackSpell("Heal", orders, fallback);
    REQUIRE_EQ(orders.size(), 1);
    CHECK(orders.front().spellName == "Heal");
    CHECK(fallback == BattleOrderFallback::Hold);
}

TEST_CASE("battle orders: the spellbook's attack spell sets, recognises and clears its order")
{
    std::vector<BattleOrder> orders;
    BattleOrderFallback fallback = BattleOrderFallback::Weapon;
    setAttackSpell("Heal", orders, fallback);
    CHECK(isAttackSpell("Heal", orders, fallback));
    CHECK_FALSE(isAttackSpell("Fire Bolt", orders, fallback));
    CHECK_FALSE(isAttackSpell("", orders, fallback));

    // A condition or a second order makes it a plan of the window, no longer the plain attack spell.
    orders.front().allyHealthBelowPercent = 50;
    CHECK_FALSE(isAttackSpell("Heal", orders, fallback));

    setAttackSpell("", orders, fallback);
    CHECK(orders.empty());
    CHECK(fallback == BattleOrderFallback::Weapon);
}

TEST_CASE("battle orders: a save keeps each member's orders, fallback and upkeep list")
{
    GameSaveData save;
    save.mapFileName = "oute3.odm";
    Party party;
    party.seed(Party::createDefaultSeed());
    REQUIRE_FALSE(party.members().empty());
    Character &member = *party.member(0);
    BattleOrder heal;
    heal.spellName = "Heal";
    heal.allyHealthBelowPercent = 60;
    BattleOrder shoot;
    shoot.kind = BattleOrderKind::Shoot;
    shoot.distance = BattleOrderDistance{BattleOrderMeleeReach, BattleOrderMaximumDistance};
    shoot.enabled = false;
    BattleOrder bolt;
    bolt.spellName = "Light Bolt";
    bolt.keepSpellPointsPercent = 30;
    bolt.place = BattleOrderPlace::Indoors;
    member.battleOrders = {heal, shoot, bolt};
    member.battleOrderFallback = BattleOrderFallback::Hold;
    BattleOrder bless;
    bless.spellName = "Bless";
    bless.renewBelowMinutes = 45;
    BattleOrder torch;
    torch.spellName = "Torch Light";
    torch.place = BattleOrderPlace::Indoors;
    torch.enabled = false;
    member.upkeepOrders = {bless, torch, heal};
    save.party = party.snapshot();

    const uint64_t ticks = uint64_t(std::chrono::steady_clock::now().time_since_epoch().count());
    const std::filesystem::path path =
        std::filesystem::temp_directory_path() / ("openyamm_battle_orders_save_" + std::to_string(ticks) + ".oysav");
    std::string error;
    REQUIRE_MESSAGE(saveGameDataToPath(path, save, error), error);
    const std::optional<GameSaveData> loaded = loadGameDataFromPath(path, error);
    std::filesystem::remove(path);
    REQUIRE_MESSAGE(loaded.has_value(), error);
    REQUIRE_FALSE(loaded->party.members.empty());
    CHECK(loaded->party.members.front().battleOrders == member.battleOrders);
    CHECK(loaded->party.members.front().battleOrderFallback == BattleOrderFallback::Hold);
    CHECK(loaded->party.members.front().upkeepOrders == member.upkeepOrders);
}
