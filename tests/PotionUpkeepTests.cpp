#include "doctest/doctest.h"

#include "game/items/AlchemyBenchRuntime.h"
#include "game/items/InventoryItemUseRuntime.h"
#include "game/items/PotionUpkeep.h"
#include "game/party/Party.h"
#include "game/tables/MergedBaseTables.h"
#include "game/tables/PotionEffectTable.h"

#include "tests/RegressionGameData.h"

#include <algorithm>
#include <set>

namespace
{
using namespace OpenYAMM::Game;

constexpr uint32_t BottleItemId = 220;
constexpr uint32_t WidowsweepBerriesItemId = 200;
constexpr uint32_t PoppyPodItemId = 210;
constexpr uint32_t CureWoundsItemId = 222;
constexpr uint32_t CureDiseaseItemId = 225;
constexpr uint32_t HasteItemId = 228;
constexpr uint32_t CureDiseaseNoteId = 32;
constexpr uint32_t HasteNoteId = 35;
constexpr float Minute = 60.0f;

const OpenYAMM::Tests::RegressionGameData &requireGameData()
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());
    return OpenYAMM::Tests::regressionGameData();
}

AlchemyBenchTables benchTables(const OpenYAMM::Tests::RegressionGameData &gameData)
{
    return {
        gameData.itemTable,
        gameData.potionMixingTable,
        gameData.potionNoteTable,
        gameData.mergedPotionSettingTable,
        gameData.mergedReagentSettingTable};
}

Party makeParty(const OpenYAMM::Tests::RegressionGameData &gameData, size_t memberCount)
{
    PartySeed seed = {};

    for (size_t index = 0; index < memberCount; ++index)
    {
        Character member = {};
        member.name = "Member" + std::to_string(index);
        member.className = "Knight";
        member.role = "Knight";
        member.portraitTextureName = "PC01-01";
        member.characterDataId = 1;
        member.level = 1;
        member.maxHealth = 40;
        member.health = 40;
        seed.members.push_back(member);
    }

    Party party = {};
    party.setItemTable(&gameData.itemTable);
    party.seed(seed);
    return party;
}

void addItem(Party &party, size_t memberIndex, uint32_t itemId, uint16_t power = 0)
{
    InventoryItem item = {};
    item.objectDescriptionId = itemId;
    item.standardEnchantPower = power;

    if (const ItemDefinition *pDefinition = OpenYAMM::Tests::regressionGameData().itemTable.get(itemId))
    {
        item.width = std::max<uint8_t>(1, pDefinition->inventoryWidth);
        item.height = std::max<uint8_t>(1, pDefinition->inventoryHeight);
    }

    REQUIRE(party.tryAutoPlaceItemInMemberInventory(memberIndex, item));
}

BattleOrder potionOrder(uint32_t itemId, uint8_t stockDrinks, std::optional<uint16_t> brewPower = std::nullopt)
{
    BattleOrder order;
    order.kind = BattleOrderKind::Potion;
    order.potionItemId = itemId;
    order.stockDrinks = stockDrinks;
    order.brewPower = brewPower;
    order.renewBelowMinutes = UpkeepRenewDefaultMinutes;
    return order;
}

AlchemyBenchRuntime::AutonoteLookup unlocked(std::set<uint32_t> autonoteIds)
{
    return [autonoteIds](uint32_t autonoteId)
    {
        return autonoteIds.contains(autonoteId);
    };
}
}

TEST_CASE("potion upkeep takes potions with a timed effect only")
{
    const PotionEffectTable &effects = requireGameData().mergedPotionSettingTable.effects();
    REQUIRE(effects.find(HasteItemId) != nullptr);
    REQUIRE(effects.find(CureWoundsItemId) != nullptr);

    CHECK(PotionUpkeep::isUpkeepPotion(*effects.find(HasteItemId)));
    CHECK_FALSE(PotionUpkeep::isUpkeepPotion(*effects.find(CureWoundsItemId)));
    CHECK_FALSE(PotionUpkeep::isUpkeepPotion(*effects.find(CureDiseaseItemId)));
}

TEST_CASE("potion upkeep is due when the buff is gone or running out, never while it would not take")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireGameData();
    const PotionEffectTable &effects = gameData.mergedPotionSettingTable.effects();
    const PotionDefinition &haste = *effects.find(HasteItemId);
    Party party = makeParty(gameData, 1);
    const float drinkSeconds = InventoryItemUseRuntime::potionDurationSeconds(party, effects, 10);
    REQUIRE_GT(drinkSeconds, 120 * Minute);

    CHECK(PotionUpkeep::potionDue(party, 0, haste, 10, drinkSeconds, UpkeepRenewDefaultMinutes));

    party.applyCharacterBuff(0, CharacterBuffId::Haste, 3 * 60 * Minute, 5, 0, 0, SkillMastery::Master, 0);
    CHECK_FALSE(PotionUpkeep::potionDue(party, 0, haste, 10, drinkSeconds, UpkeepRenewDefaultMinutes));
    // Without a renew time, only once it is gone.
    CHECK_FALSE(PotionUpkeep::potionDue(party, 0, haste, 10, drinkSeconds, std::nullopt));

    Party low = makeParty(gameData, 1);
    low.applyCharacterBuff(0, CharacterBuffId::Haste, 20 * Minute, 5, 0, 0, SkillMastery::Master, 0);
    CHECK(PotionUpkeep::potionDue(low, 0, haste, 10, drinkSeconds, UpkeepRenewDefaultMinutes));
    CHECK_FALSE(PotionUpkeep::potionDue(low, 0, haste, 10, drinkSeconds, std::nullopt));

    // A buff stronger than the drink gives is kept.
    Party strong = makeParty(gameData, 1);
    strong.applyCharacterBuff(0, CharacterBuffId::Haste, 20 * Minute, 50, 0, 0, SkillMastery::Master, 0);
    CHECK_FALSE(PotionUpkeep::potionDue(strong, 0, haste, 10, drinkSeconds, UpkeepRenewDefaultMinutes));

    // Haste does not take while weak, so it is never due then.
    Party weak = makeParty(gameData, 1);
    weak.member(0)->conditions.set(size_t(CharacterCondition::Weak));
    CHECK_FALSE(PotionUpkeep::potionDue(weak, 0, haste, 10, drinkSeconds, UpkeepRenewDefaultMinutes));
}

TEST_CASE("potion upkeep counts the drinks carried at the stock's power")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireGameData();
    const PotionEffectTable &effects = gameData.mergedPotionSettingTable.effects();
    const PotionDefinition &haste = *effects.find(HasteItemId);
    Party party = makeParty(gameData, 2);
    addItem(party, 0, HasteItemId, 5);
    addItem(party, 1, HasteItemId, 20);
    addItem(party, 1, CureWoundsItemId, 20);

    CHECK_EQ(PotionUpkeep::carriedDrinks(party, haste, effects, std::nullopt),
        2u * PotionUpkeep::bottleDrinks(haste, {}));
    CHECK_EQ(PotionUpkeep::carriedDrinks(party, haste, effects, uint16_t(10)), PotionUpkeep::bottleDrinks(haste, {}));
    CHECK_EQ(PotionUpkeep::carriedDrinks(party, haste, effects, uint16_t(30)), 0u);
}

TEST_CASE("potion upkeep stock adds the members' drinks and takes the highest power")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireGameData();
    Party party = makeParty(gameData, 2);
    party.member(0)->upkeepOrders = {potionOrder(HasteItemId, 2, uint16_t(10)), potionOrder(CureWoundsItemId, 0)};
    party.member(1)->upkeepOrders = {potionOrder(HasteItemId, 3, uint16_t(30)), potionOrder(CureDiseaseItemId, 1)};
    BattleOrder off = potionOrder(BottleItemId, 4);
    off.enabled = false;
    party.member(1)->upkeepOrders.push_back(off);

    const std::vector<PotionUpkeep::StockTarget> targets = PotionUpkeep::stockTargets(party);

    REQUIRE_EQ(targets.size(), 2u);
    CHECK_EQ(targets[0].itemId, HasteItemId);
    CHECK_EQ(targets[0].drinks, 5u);
    CHECK_EQ(targets[0].power, std::optional<uint16_t>(30));
    CHECK_EQ(targets[1].itemId, CureDiseaseItemId);
    CHECK_EQ(targets[1].power, std::nullopt);
}

TEST_CASE("potion upkeep restock brews what is missing without mixing the stocked potions")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireGameData();
    const AlchemyBenchTables tables = benchTables(gameData);
    const PotionEffectTable &effects = gameData.mergedPotionSettingTable.effects();
    Party party = makeParty(gameData, 1);
    party.member(0)->skills["Alchemy"] = {"Alchemy", 4, SkillMastery::Expert};

    for (int index = 0; index < 3; ++index)
    {
        addItem(party, 0, BottleItemId);
    }

    addItem(party, 0, WidowsweepBerriesItemId);
    addItem(party, 0, WidowsweepBerriesItemId);
    addItem(party, 0, PoppyPodItemId);
    // The stocked Cure Disease: Haste would otherwise be mixed from it rather than from a fresh one.
    addItem(party, 0, CureDiseaseItemId, 9);
    party.member(0)->upkeepOrders = {potionOrder(HasteItemId, 1), potionOrder(CureDiseaseItemId, 1)};

    const PotionUpkeep::RestockOutcome outcome =
        PotionUpkeep::restock(party, tables, effects, unlocked({CureDiseaseNoteId, HasteNoteId}), false);

    REQUIRE_EQ(outcome.lines.size(), 1u);
    CHECK_EQ(outcome.lines[0].itemId, HasteItemId);
    CHECK_EQ(outcome.lines[0].brewedBottles, 1u);
    CHECK(outcome.lines[0].complete);
    CHECK(outcome.brewedAny());
    CHECK_EQ(party.inventoryItemCount(HasteItemId), 1);
    CHECK_EQ(party.inventoryItemCount(CureDiseaseItemId), 1);

    // In stock now: nothing more to brew.
    const PotionUpkeep::RestockOutcome again =
        PotionUpkeep::restock(party, tables, effects, unlocked({CureDiseaseNoteId, HasteNoteId}), false);
    CHECK(again.lines.empty());
}

TEST_CASE("potion upkeep restock says why it could not brew")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireGameData();
    const AlchemyBenchTables tables = benchTables(gameData);
    const PotionEffectTable &effects = gameData.mergedPotionSettingTable.effects();
    Party party = makeParty(gameData, 1);
    party.member(0)->skills["Alchemy"] = {"Alchemy", 4, SkillMastery::Expert};
    addItem(party, 0, CureDiseaseItemId, 9);
    party.member(0)->upkeepOrders = {potionOrder(HasteItemId, 1), potionOrder(CureDiseaseItemId, 1)};

    const PotionUpkeep::RestockOutcome outcome =
        PotionUpkeep::restock(party, tables, effects, unlocked({CureDiseaseNoteId, HasteNoteId}), false);

    REQUIRE_EQ(outcome.lines.size(), 1u);
    CHECK_EQ(outcome.lines[0].brewedBottles, 0u);
    CHECK_FALSE(outcome.lines[0].complete);
    CHECK_NE(outcome.lines[0].block, AlchemyChainBlock::None);
    CHECK_FALSE(outcome.brewedAny());
    CHECK_EQ(party.inventoryItemCount(CureDiseaseItemId), 1);
}

TEST_CASE("alchemy chain planner keeps the reserved copies, strongest first")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireGameData();
    const AlchemyBenchTables tables = benchTables(gameData);
    Party party = makeParty(gameData, 1);
    party.member(0)->skills["Alchemy"] = {"Alchemy", 4, SkillMastery::Expert};
    addItem(party, 0, BottleItemId);
    addItem(party, 0, WidowsweepBerriesItemId);
    addItem(party, 0, CureDiseaseItemId, 9);
    addItem(party, 0, CureDiseaseItemId, 3);
    const AlchemyBook book = AlchemyBenchRuntime::buildBook(tables,
        AlchemyBenchRuntime::collectIngredients(party, tables),
        AlchemyBenchRuntime::resolveAlchemist(party).mastery, unlocked({CureDiseaseNoteId, HasteNoteId}));
    const std::vector<AlchemyItemCount> reserved = {{CureDiseaseItemId, 1}};

    const AlchemyChainPlan plan =
        AlchemyChainPlanner(party, book, AlchemyBenchRuntime::resolveAlchemist(party), tables, false, reserved)
            .plan(HasteItemId, 99);

    // The weaker Cure Disease is mixed; the stronger one is kept.
    CHECK_EQ(plan.brewCount, 1u);
    REQUIRE_EQ(plan.kept.size(), 1u);
    CHECK_EQ(plan.kept.front().itemId, CureDiseaseItemId);
    CHECK_EQ(plan.kept.front().power, 9u);

    AlchemyBenchRuntime::brewChain(party, plan, tables);
    CHECK_EQ(party.inventoryItemCount(HasteItemId), 1);
    REQUIRE_EQ(party.inventoryItemCount(CureDiseaseItemId), 1);
}
