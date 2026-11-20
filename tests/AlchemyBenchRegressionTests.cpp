#include "doctest/doctest.h"

#include "game/items/AlchemyBenchRuntime.h"
#include "game/items/ItemGenerator.h"
#include "game/events/EventRuntime.h"
#include "game/maps/SaveGame.h"
#include "game/party/Party.h"

#include "tests/RegressionGameData.h"

#include <algorithm>
#include <cstring>
#include <fstream>
#include <iterator>
#include <set>

namespace
{
// The planner's tests mix as an Alchemy Expert of level 4.
OpenYAMM::Game::AlchemistInfo level4Alchemist()
{
    return {std::nullopt, OpenYAMM::Game::SkillMastery::Expert, 4};
}

using namespace OpenYAMM::Game;

constexpr uint32_t BottleItemId = 220;
constexpr uint32_t WidowsweepBerriesItemId = 200;
constexpr uint32_t CureWoundsItemId = 222;
constexpr uint32_t CureWeaknessItemId = 224;
constexpr uint32_t CureDiseaseItemId = 225;
constexpr uint32_t HasteItemId = 228;
constexpr uint32_t CureDiseaseNoteId = 32;
constexpr uint32_t HasteNoteId = 35;

const OpenYAMM::Tests::RegressionGameData &requireRegressionGameData()
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

Character makeMember(const std::string &name)
{
    Character member = {};
    member.name = name;
    member.className = "Knight";
    member.role = "Knight";
    member.portraitTextureName = "PC01-01";
    member.characterDataId = 1;
    member.level = 1;
    member.maxHealth = 40;
    member.health = 40;
    return member;
}

Party makeParty(const OpenYAMM::Tests::RegressionGameData &gameData, size_t memberCount)
{
    PartySeed seed = {};

    for (size_t index = 0; index < memberCount; ++index)
    {
        seed.members.push_back(makeMember("Member" + std::to_string(index)));
    }

    Party party = {};
    party.setItemTable(&gameData.itemTable);
    party.seed(seed);
    return party;
}

void giveAlchemy(Party &party, size_t memberIndex, uint32_t level, SkillMastery mastery)
{
    Character *pMember = party.member(memberIndex);
    REQUIRE(pMember != nullptr);
    pMember->skills["Alchemy"] = {"Alchemy", level, mastery};
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

const AlchemyBookEntry *findEntry(const AlchemyBook &book, uint32_t resultItemId)
{
    const auto found = std::find_if(book.entries.begin(), book.entries.end(),
        [resultItemId](const AlchemyBookEntry &entry)
        {
            return entry.resultItemId == resultItemId;
        });
    return found != book.entries.end() ? &*found : nullptr;
}

AlchemyBenchRuntime::AutonoteLookup unlocked(std::set<uint32_t> autonoteIds)
{
    return [autonoteIds](uint32_t autonoteId)
    {
        return autonoteIds.contains(autonoteId);
    };
}
}

TEST_CASE("alchemy bench gathers ingredients from every pack")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    Party party = makeParty(gameData, 2);
    addItem(party, 0, BottleItemId);
    addItem(party, 1, BottleItemId);
    addItem(party, 0, WidowsweepBerriesItemId);
    addItem(party, 0, CureWoundsItemId, 4);
    addItem(party, 1, CureWoundsItemId, 9);

    const std::vector<AlchemyIngredient> ingredients =
        AlchemyBenchRuntime::collectIngredients(party, benchTables(gameData));

    REQUIRE_EQ(ingredients.size(), 3u);
    CHECK_EQ(ingredients[0].itemId, BottleItemId);
    CHECK_EQ(ingredients[0].kind, AlchemyIngredientKind::Bottle);
    CHECK_EQ(ingredients[0].count, 2u);
    CHECK_EQ(ingredients[1].kind, AlchemyIngredientKind::Reagent);
    CHECK_EQ(ingredients[2].itemId, CureWoundsItemId);
    CHECK_EQ(ingredients[2].count, 2u);
    CHECK_EQ(ingredients[2].bestPower, 9u);
}

TEST_CASE("recharge potion mixes with cure poison in either order")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    constexpr uint32_t CurePoisonItemId = 226;
    constexpr uint32_t RechargeItemId = 233;
    constexpr uint32_t SwiftPotionItemId = 250;

    for (const uint32_t heldItemId : {CurePoisonItemId, RechargeItemId})
    {
        CAPTURE(heldItemId);
        InventoryItem heldItem = {};
        heldItem.objectDescriptionId = heldItemId;
        heldItem.standardEnchantPower = 12;
        InventoryItem targetItem = {};
        targetItem.objectDescriptionId = heldItemId == CurePoisonItemId ? RechargeItemId : CurePoisonItemId;
        targetItem.standardEnchantPower = 8;

        const InventoryItemMixResult result = InventoryItemMixingRuntime::mixItems(
            heldItem, targetItem, SkillMastery::Grandmaster, 10,
            gameData.itemTable, gameData.potionMixingTable,
            gameData.mergedPotionSettingTable, gameData.mergedReagentSettingTable,
            &gameData.potionNoteTable);

        CHECK(result.handled);
        CHECK(result.success);
        CHECK_EQ(result.action, InventoryItemMixAction::PotionMix);
        CHECK(result.heldItemConsumed);
        CHECK(result.returnsBottle);
        CHECK_EQ(targetItem.objectDescriptionId, SwiftPotionItemId);
        CHECK_EQ(targetItem.standardEnchantPower, 10u);
    }
}

TEST_CASE("pure luck mixes stoneskin with luck boost and records its recipe in either order")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    constexpr uint32_t StoneskinItemId = 234;
    constexpr uint32_t LuckBoostItemId = 255;
    constexpr uint32_t PureLuckItemId = 264;
    constexpr uint32_t SwiftPotionItemId = 250;

    for (const uint32_t heldItemId : {StoneskinItemId, LuckBoostItemId})
    {
        const uint32_t targetItemId = heldItemId == StoneskinItemId ? LuckBoostItemId : StoneskinItemId;
        InventoryItem heldItem = {};
        heldItem.objectDescriptionId = heldItemId;
        heldItem.standardEnchantPower = 12;
        InventoryItem targetItem = {};
        targetItem.objectDescriptionId = targetItemId;
        targetItem.standardEnchantPower = 8;
        const InventoryItemMixResult result = InventoryItemMixingRuntime::mixItems(
            heldItem, targetItem, SkillMastery::Grandmaster, 10,
            gameData.itemTable, gameData.potionMixingTable,
            gameData.mergedPotionSettingTable, gameData.mergedReagentSettingTable,
            &gameData.potionNoteTable);

        REQUIRE(result.success);
        CHECK_EQ(targetItem.objectDescriptionId, PureLuckItemId);
        CHECK_EQ(result.unlockedAutonoteId, 79u);
    }

    for (const uint32_t heldItemId : {StoneskinItemId, SwiftPotionItemId})
    {
        const uint32_t targetItemId = heldItemId == StoneskinItemId ? SwiftPotionItemId : StoneskinItemId;
        const auto combination = gameData.potionMixingTable.potionCombination(heldItemId, targetItemId);
        REQUIRE(combination.has_value());
        CHECK_NE(combination->resultItemId, PureLuckItemId);
        CHECK_FALSE(gameData.potionNoteTable.autonoteIdForMix(targetItemId, heldItemId).has_value());
    }
}

TEST_CASE("alchemy bench book lists reagent recipes and only noted potion recipes")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    Party party = makeParty(gameData, 1);
    addItem(party, 0, BottleItemId);
    addItem(party, 0, WidowsweepBerriesItemId);
    addItem(party, 0, CureWoundsItemId);
    addItem(party, 0, CureDiseaseItemId);
    const AlchemyBenchTables tables = benchTables(gameData);
    const std::vector<AlchemyIngredient> ingredients = AlchemyBenchRuntime::collectIngredients(party, tables);

    const AlchemyBook unknownBook =
        AlchemyBenchRuntime::buildBook(tables, ingredients, SkillMastery::Expert, unlocked({}));
    const AlchemyBookEntry *pRedPotion = findEntry(unknownBook, CureWoundsItemId);
    REQUIRE(pRedPotion != nullptr);
    CHECK(pRedPotion->reagentRecipe);
    CHECK_EQ(pRedPotion->brewableCount, 1u);
    CHECK(findEntry(unknownBook, HasteItemId) == nullptr);
    CHECK_GT(unknownBook.totalResultCount, 60u);

    const AlchemyBook book =
        AlchemyBenchRuntime::buildBook(tables, ingredients, SkillMastery::Normal, unlocked({HasteNoteId}));
    const AlchemyBookEntry *pHaste = findEntry(book, HasteItemId);
    REQUIRE(pHaste != nullptr);
    CHECK_FALSE(pHaste->reagentRecipe);
    CHECK_EQ(pHaste->requiredMastery, 2u);
    CHECK_FALSE(pHaste->masteryAllows);
    CHECK_EQ(pHaste->brewableCount, 1u);
    REQUIRE_EQ(pHaste->recipes.size(), 1u);
    const std::set<uint32_t> inputs = {pHaste->recipes[0].targetItemId, pHaste->recipes[0].heldItemId};
    CHECK_EQ(inputs, std::set<uint32_t>{CureWoundsItemId, CureDiseaseItemId});
}

TEST_CASE("alchemy bench preview hides untried mixes and blocks recipes beyond the alchemist")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    Party party = makeParty(gameData, 2);
    giveAlchemy(party, 1, 4, SkillMastery::Normal);
    addItem(party, 0, CureWoundsItemId, 8);
    addItem(party, 0, CureDiseaseItemId, 6);
    const AlchemyBenchTables tables = benchTables(gameData);
    const AlchemyRecipe haste = {CureWoundsItemId, CureDiseaseItemId};

    const AlchemyPreview untried = AlchemyBenchRuntime::preview(party, haste, tables, unlocked({}));
    CHECK_EQ(untried.outcome, AlchemyPreviewOutcome::Unknown);
    CHECK_EQ(untried.resultItemId, 0u);

    const AlchemyPreview tooHard = AlchemyBenchRuntime::preview(party, haste, tables, unlocked({HasteNoteId}));
    CHECK_EQ(tooHard.outcome, AlchemyPreviewOutcome::TooDifficult);
    CHECK_EQ(tooHard.resultItemId, HasteItemId);
    CHECK_EQ(tooHard.requiredMastery, 2u);

    giveAlchemy(party, 1, 4, SkillMastery::Expert);
    const AlchemyPreview known = AlchemyBenchRuntime::preview(party, haste, tables, unlocked({HasteNoteId}));
    CHECK_EQ(known.outcome, AlchemyPreviewOutcome::Known);
    CHECK_EQ(known.resultItemId, HasteItemId);
    CHECK_EQ(known.resultPower, 7u);
    CHECK(known.returnsBottle);

    const AlchemyPreview missing =
        AlchemyBenchRuntime::preview(party, {CureWoundsItemId, CureWoundsItemId}, tables, unlocked({}));
    CHECK_EQ(missing.outcome, AlchemyPreviewOutcome::MissingIngredient);

    const AlchemyPreview reagent =
        AlchemyBenchRuntime::preview(party, {BottleItemId, WidowsweepBerriesItemId}, tables, unlocked({}));
    CHECK_EQ(reagent.outcome, AlchemyPreviewOutcome::MissingIngredient);
}

TEST_CASE("alchemy bench mixes potions held by different party members")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    Party party = makeParty(gameData, 2);
    giveAlchemy(party, 0, 4, SkillMastery::Expert);
    addItem(party, 0, CureWoundsItemId, 2);
    addItem(party, 0, CureWoundsItemId, 8);
    addItem(party, 1, CureDiseaseItemId, 6);
    const AlchemyBenchTables tables = benchTables(gameData);

    const AlchemyMixOutcome outcome = AlchemyBenchRuntime::mix(party, {CureWoundsItemId, CureDiseaseItemId}, tables);

    REQUIRE(outcome.result.handled);
    CHECK(outcome.result.success);
    CHECK_EQ(outcome.result.unlockedAutonoteId, HasteNoteId);
    CHECK_FALSE(outcome.overflowItem.has_value());
    CHECK_EQ(party.inventoryItemCount(CureDiseaseItemId), 0);
    CHECK_EQ(party.inventoryItemCount(CureWoundsItemId), 1);
    CHECK_EQ(party.inventoryItemCount(BottleItemId), 1);

    const std::vector<AlchemyIngredient> ingredients = AlchemyBenchRuntime::collectIngredients(party, tables);
    const AlchemyIngredient *pHaste = AlchemyBenchRuntime::findIngredient(ingredients, HasteItemId);
    REQUIRE(pHaste != nullptr);
    // The strongest Cure Wounds was used: (8 + 6) / 2.
    CHECK_EQ(pHaste->bestPower, 7u);
    const AlchemyIngredient *pCureWounds = AlchemyBenchRuntime::findIngredient(ingredients, CureWoundsItemId);
    REQUIRE(pCureWounds != nullptr);
    CHECK_EQ(pCureWounds->bestPower, 2u);
}

TEST_CASE("alchemy bench boosts the copy of a potion that the catalyst raises most")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    Party party = makeParty(gameData, 1);
    giveAlchemy(party, 0, 4, SkillMastery::Expert);
    const AlchemyBenchTables tables = benchTables(gameData);
    const uint32_t catalystItemId = tables.potionSettingTable.catalystPotionItemId();
    REQUIRE_NE(catalystItemId, 0u);
    addItem(party, 0, CureWoundsItemId, 30);
    addItem(party, 0, CureWoundsItemId, 2);
    addItem(party, 0, catalystItemId, 20);

    // Standard's catalyst gives the potion its own power: the strongest copy would lose power, the weak one gains.
    const AlchemyPreview preview =
        AlchemyBenchRuntime::preview(party, {CureWoundsItemId, catalystItemId}, tables, unlocked({}));
    CHECK_EQ(preview.outcome, AlchemyPreviewOutcome::Known);
    CHECK_EQ(preview.targetPower, 2u);
    CHECK_EQ(preview.resultPower, 20u);

    const AlchemyMixOutcome outcome = AlchemyBenchRuntime::mix(party, {CureWoundsItemId, catalystItemId}, tables);
    REQUIRE(outcome.result.success);
    std::multiset<uint16_t> powers;

    for (const InventoryItem &item : party.member(0)->inventory)
    {
        if (item.objectDescriptionId == CureWoundsItemId)
        {
            powers.insert(item.standardEnchantPower);
        }
    }

    CHECK_EQ(powers, std::multiset<uint16_t>{20, 30});
}

TEST_CASE("alchemy bench fills bottles and leaves non-reacting items in place")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    Party party = makeParty(gameData, 1);
    giveAlchemy(party, 0, 2, SkillMastery::Normal);
    addItem(party, 0, BottleItemId);
    addItem(party, 0, WidowsweepBerriesItemId);
    addItem(party, 0, CureWeaknessItemId, 5);
    const AlchemyBenchTables tables = benchTables(gameData);

    const AlchemyMixOutcome noReaction = AlchemyBenchRuntime::mix(party, {CureWeaknessItemId, BottleItemId}, tables);
    CHECK_FALSE(noReaction.result.handled);
    CHECK_EQ(party.inventoryItemCount(BottleItemId), 1);
    CHECK_EQ(party.inventoryItemCount(CureWeaknessItemId), 1);

    const AlchemyMixOutcome filled =
        AlchemyBenchRuntime::mix(party, {BottleItemId, WidowsweepBerriesItemId}, tables);
    REQUIRE(filled.result.handled);
    CHECK(filled.result.success);
    CHECK_EQ(filled.result.action, InventoryItemMixAction::ReagentBottleMix);
    CHECK_EQ(party.inventoryItemCount(BottleItemId), 0);
    CHECK_EQ(party.inventoryItemCount(WidowsweepBerriesItemId), 0);
    CHECK_EQ(party.inventoryItemCount(CureWoundsItemId), 1);

    const AlchemyBook book = AlchemyBenchRuntime::buildBook(tables,
        AlchemyBenchRuntime::collectIngredients(party, tables), SkillMastery::Normal, unlocked({CureDiseaseNoteId}));
    const AlchemyBookEntry *pCureDisease = findEntry(book, CureDiseaseItemId);
    REQUIRE(pCureDisease != nullptr);
    CHECK_EQ(pCureDisease->brewableCount, 1u);
    CHECK(pCureDisease->masteryAllows);
}

TEST_CASE("Clanker's Amulet adds 15 potion power without changing alchemy mastery")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    const AlchemyBenchTables tables = benchTables(gameData);
    Party party = makeParty(gameData, 1);
    giveAlchemy(party, 0, 2, SkillMastery::Normal);

    const AlchemyRecipe recipe = {BottleItemId, WidowsweepBerriesItemId};
    InventoryItem bottle = InventoryItemMixingRuntime::makeBottleItem(tables.itemTable, BottleItemId);
    REQUIRE(party.member(0)->addInventoryItemAt(bottle, 0, 0));
    addItem(party, 0, WidowsweepBerriesItemId);
    const AlchemyPreview withoutAmulet = AlchemyBenchRuntime::preview(party, recipe, tables, unlocked({}));
    REQUIRE(withoutAmulet.outcome == AlchemyPreviewOutcome::Known);

    InventoryItem amulet = ItemGenerator::makeInventoryItem(gameData.itemTable, 1339);
    REQUIRE_NE(amulet.standardEnchantId, 0u);
    CHECK_EQ(amulet.standardEnchantPower, 15u);
    amulet.identified = true;
    std::optional<InventoryItem> heldReplacement;
    REQUIRE(party.tryEquipItemOnMember(0, EquipmentSlot::Amulet, amulet, std::nullopt, false, heldReplacement));
    const AlchemistInfo alchemist = AlchemyBenchRuntime::resolveAlchemist(party);
    CHECK_EQ(alchemist.level, 17u);
    CHECK(alchemist.mastery == SkillMastery::Normal);
    const uint16_t boostedPower = withoutAmulet.resultPower + 15;

    SUBCASE("bench preview and brew")
    {
        CHECK_EQ(AlchemyBenchRuntime::preview(party, recipe, tables, unlocked({})).resultPower, boostedPower);
        const AlchemyMixOutcome outcome = AlchemyBenchRuntime::mix(party, recipe, tables);
        REQUIRE(outcome.result.success);
        CHECK_EQ(outcome.resultItem.standardEnchantPower, boostedPower);
    }

    SUBCASE("inventory brew")
    {
        InventoryItem reagent = {};
        reagent.objectDescriptionId = WidowsweepBerriesItemId;
        const InventoryItemMixResult outcome = InventoryItemMixingRuntime::tryApplyHeldItemToInventoryItem(
            party, 0, reagent, 0, 0, tables.itemTable, tables.potionMixingTable,
            tables.potionSettingTable, tables.reagentSettingTable, &tables.potionNoteTable);
        REQUIRE(outcome.success);
        const InventoryItem *pPotion = party.member(0)->inventoryItemAt(0, 0);
        REQUIRE(pPotion != nullptr);
        CHECK_EQ(pPotion->standardEnchantPower, boostedPower);
    }

    REQUIRE(party.takeEquippedItemFromMember(0, EquipmentSlot::Amulet, amulet));
    CHECK_EQ(AlchemyBenchRuntime::resolveAlchemist(party).level, 2u);
}

TEST_CASE("alchemy bench fills the bottle even when the reagent was picked first")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    Party party = makeParty(gameData, 1);
    giveAlchemy(party, 0, 2, SkillMastery::Normal);
    addItem(party, 0, WidowsweepBerriesItemId);
    addItem(party, 0, BottleItemId);
    const AlchemyBenchTables tables = benchTables(gameData);

    const AlchemyMixOutcome filled =
        AlchemyBenchRuntime::mix(party, {WidowsweepBerriesItemId, BottleItemId}, tables);
    REQUIRE(filled.result.handled);
    CHECK(filled.result.success);
    CHECK_EQ(party.inventoryItemCount(BottleItemId), 0);
    CHECK_EQ(party.inventoryItemCount(WidowsweepBerriesItemId), 0);
    CHECK_EQ(party.inventoryItemCount(CureWoundsItemId), 1);

    // The potion keeps the bottle's two cells, not the reagent's one.
    const Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);
    const auto potionIt = std::find_if(pMember->inventory.begin(), pMember->inventory.end(),
        [](const InventoryItem &item) { return item.objectDescriptionId == CureWoundsItemId; });
    REQUIRE(potionIt != pMember->inventory.end());
    CHECK_EQ(potionIt->width, 1u);
    CHECK_EQ(potionIt->height, 2u);
}

TEST_CASE("alchemy bench counts pairs of the same item")
{
    const std::vector<AlchemyIngredient> ingredients = {{CureWoundsItemId, AlchemyIngredientKind::Potion, 5, 0}};
    CHECK_EQ(AlchemyBenchRuntime::brewableCount({CureWoundsItemId, CureWoundsItemId}, ingredients), 2u);
    CHECK_EQ(AlchemyBenchRuntime::brewableCount({CureWoundsItemId, HasteItemId}, ingredients), 0u);
}

TEST_CASE("alchemy bench remembers mixtures that exploded and warns before the next attempt")
{
    constexpr uint32_t MagicPotionItemId = 223;
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    Party party = makeParty(gameData, 1);
    giveAlchemy(party, 0, 10, SkillMastery::Grandmaster);
    addItem(party, 0, HasteItemId);
    addItem(party, 0, MagicPotionItemId);
    addItem(party, 0, HasteItemId);
    addItem(party, 0, MagicPotionItemId);
    const AlchemyBenchTables tables = benchTables(gameData);
    const AlchemyRecipe clash = {HasteItemId, MagicPotionItemId};

    CHECK_EQ(AlchemyBenchRuntime::preview(party, clash, tables, unlocked({})).outcome, AlchemyPreviewOutcome::Unknown);

    const AlchemyMixOutcome boom = AlchemyBenchRuntime::mix(party, clash, tables);
    REQUIRE(boom.result.handled);
    CHECK_FALSE(boom.result.success);
    CHECK_NE(boom.result.failureDamageLevel, 0u);
    CHECK(party.isExplosiveMixKnown(HasteItemId, MagicPotionItemId));
    CHECK_FALSE(party.isExplosiveMixKnown(MagicPotionItemId, HasteItemId));
    CHECK_EQ(AlchemyBenchRuntime::preview(party, clash, tables, unlocked({})).outcome,
        AlchemyPreviewOutcome::KnownExplosive);

    Party restored = makeParty(gameData, 1);
    restored.restoreSnapshot(party.snapshot());
    CHECK(restored.isExplosiveMixKnown(HasteItemId, MagicPotionItemId));
}

TEST_CASE("alchemy bench recipe search ignores case and matches inside names")
{
    CHECK(AlchemyBenchRuntime::matchesSearch("Cure Poison", ""));
    CHECK(AlchemyBenchRuntime::matchesSearch("Cure Poison", "pois"));
    CHECK(AlchemyBenchRuntime::matchesSearch("Cure Poison", "CURE p"));
    CHECK_FALSE(AlchemyBenchRuntime::matchesSearch("Cure Poison", "haste"));
}

TEST_CASE("potion recipe scrolls teach every noted mix of their potion")
{
    constexpr uint32_t DivineRestorationRecipeItemId = 722;
    constexpr uint32_t StoneToFleshRecipeItemId = 1551;
    constexpr uint32_t DivineRestorationItemId = 252;
    constexpr uint32_t StoneToFleshItemId = 262;

    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    const AlchemyBenchTables tables = benchTables(gameData);

    CHECK(AlchemyBenchRuntime::recipeScrollPotionItemId(DivineRestorationRecipeItemId, tables)
        == DivineRestorationItemId);
    // "Stone To Flesh Recipe" names the potion, not the spell scroll or book of the same name.
    CHECK(AlchemyBenchRuntime::recipeScrollPotionItemId(StoneToFleshRecipeItemId, tables) == StoneToFleshItemId);
    CHECK_FALSE(AlchemyBenchRuntime::recipeScrollPotionItemId(HasteItemId, tables).has_value());

    // Every recipe scroll resolves to a potion whose mixes the bench can learn.
    for (const ItemDefinition &definition : gameData.itemTable.entries())
    {
        if (definition.equipStat == "Mscroll" && definition.name.ends_with(" Recipe"))
        {
            CAPTURE(definition.itemId);
            const std::optional<uint32_t> potionItemId =
                AlchemyBenchRuntime::recipeScrollPotionItemId(definition.itemId, tables);
            REQUIRE(potionItemId.has_value());
            CHECK_FALSE(AlchemyBenchRuntime::potionNoteIds(*potionItemId, tables).empty());
        }
    }

    std::vector<uint32_t> noteIds = AlchemyBenchRuntime::potionNoteIds(DivineRestorationItemId, tables);
    std::sort(noteIds.begin(), noteIds.end());
    CHECK(noteIds == std::vector<uint32_t>{65, 66, 67});

    const AlchemyBook book = AlchemyBenchRuntime::buildBook(
        tables, {}, SkillMastery::Grandmaster, unlocked({noteIds.begin(), noteIds.end()}));
    const auto found = std::find_if(book.entries.begin(), book.entries.end(),
        [](const AlchemyBookEntry &entry)
        {
            return entry.resultItemId == DivineRestorationItemId;
        });
    REQUIRE(found != book.entries.end());
    CHECK(found->recipes.size() == 3);
}

namespace
{
constexpr uint32_t PoppyPodItemId = 210;

AlchemyBook knownBook(const Party &party, const AlchemyBenchTables &tables, std::set<uint32_t> notes)
{
    return AlchemyBenchRuntime::buildBook(tables, AlchemyBenchRuntime::collectIngredients(party, tables),
        AlchemyBenchRuntime::resolveAlchemist(party).mastery, unlocked(std::move(notes)));
}

uint32_t countOf(const std::vector<AlchemyItemCount> &counts, uint32_t itemId)
{
    const auto found = std::find_if(counts.begin(), counts.end(),
        [itemId](const AlchemyItemCount &count)
        {
            return count.itemId == itemId;
        });
    return found != counts.end() ? found->count : 0;
}
}

TEST_CASE("alchemy chain planner brews a compound potion from bottles and reagents")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    Party party = makeParty(gameData, 1);
    giveAlchemy(party, 0, 4, SkillMastery::Expert);
    for (int index = 0; index < 3; ++index)
    {
        addItem(party, 0, BottleItemId);
    }
    addItem(party, 0, WidowsweepBerriesItemId);
    addItem(party, 0, WidowsweepBerriesItemId);
    addItem(party, 0, PoppyPodItemId);
    const AlchemyBenchTables tables = benchTables(gameData);
    const AlchemyBook book = knownBook(party, tables, {CureDiseaseNoteId, HasteNoteId});
    const AlchemyChainPlanner planner(party, book, level4Alchemist(), tables);

    const AlchemyChainPlan plan = planner.plan(HasteItemId, 99);

    CHECK_EQ(plan.block, AlchemyChainBlock::None);
    CHECK_EQ(plan.brewCount, 1u);
    // Two Cure Wounds and a Cure Weakness from bottles, Cure Disease from one of them, then Haste.
    CHECK_EQ(plan.steps.size(), 5u);
    CHECK_EQ(plan.steps.back().resultItemId, HasteItemId);
    CHECK_EQ(countOf(plan.brewedFirst, CureWoundsItemId), 2u);
    CHECK_EQ(countOf(plan.brewedFirst, CureDiseaseItemId), 1u);
    // Three bottles filled, two handed back by the potion mixes.
    CHECK_EQ(countOf(plan.used, BottleItemId), 1u);
    CHECK_EQ(countOf(plan.used, WidowsweepBerriesItemId), 2u);

    const AlchemyChainOutcome outcome = AlchemyBenchRuntime::brewChain(party, plan, tables);
    CHECK_EQ(outcome.stepsDone, 5u);
    CHECK_EQ(outcome.brewedCount, 1u);
    CHECK_EQ(party.inventoryItemCount(HasteItemId), 1);
    CHECK_EQ(party.inventoryItemCount(BottleItemId), 2);
    CHECK_EQ(party.inventoryItemCount(WidowsweepBerriesItemId), 0);
    CHECK_EQ(party.inventoryItemCount(PoppyPodItemId), 0);
}

TEST_CASE("alchemy chain planner uses carried potions before brewing replacements")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    Party party = makeParty(gameData, 1);
    giveAlchemy(party, 0, 4, SkillMastery::Expert);
    addItem(party, 0, BottleItemId);
    addItem(party, 0, WidowsweepBerriesItemId);
    addItem(party, 0, CureDiseaseItemId, 9);
    const AlchemyBenchTables tables = benchTables(gameData);
    const AlchemyBook book = knownBook(party, tables, {CureDiseaseNoteId, HasteNoteId});

    const AlchemyChainPlan plan = AlchemyChainPlanner(party, book, level4Alchemist(), tables).plan(HasteItemId, 99);

    CHECK_EQ(plan.brewCount, 1u);
    CHECK_EQ(plan.steps.size(), 2u);
    CHECK_EQ(countOf(plan.used, CureDiseaseItemId), 1u);
    // Cure Wounds from level 4 + Widowsweep 1, averaged with the carried Cure Disease of power 9.
    CHECK_EQ(plan.resultPower, 7u);
}

TEST_CASE("alchemy chain planner names the step that blocks a chain")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    Party party = makeParty(gameData, 1);
    giveAlchemy(party, 0, 4, SkillMastery::Expert);
    addItem(party, 0, BottleItemId);
    addItem(party, 0, BottleItemId);
    addItem(party, 0, WidowsweepBerriesItemId);
    addItem(party, 0, WidowsweepBerriesItemId);
    const AlchemyBenchTables tables = benchTables(gameData);

    const AlchemyChainPlan unknown =
        AlchemyChainPlanner(party, knownBook(party, tables, {HasteNoteId}), level4Alchemist(), tables)
            .plan(HasteItemId, 1);
    CHECK_EQ(unknown.brewCount, 0u);
    CHECK_EQ(unknown.block, AlchemyChainBlock::UnknownRecipe);
    CHECK_EQ(unknown.blockItemId, CureDiseaseItemId);

    const AlchemyChainPlan noReagent = AlchemyChainPlanner(party,
        knownBook(party, tables, {HasteNoteId, CureDiseaseNoteId}), level4Alchemist(), tables)
        .plan(HasteItemId, 1);
    CHECK_EQ(noReagent.block, AlchemyChainBlock::MissingBottle);

    giveAlchemy(party, 0, 4, SkillMastery::Normal);
    const AlchemyChainPlan tooHard = AlchemyChainPlanner(party,
        knownBook(party, tables, {HasteNoteId, CureDiseaseNoteId}), level4Alchemist(), tables)
        .plan(HasteItemId, 1);
    CHECK_EQ(tooHard.block, AlchemyChainBlock::NeedsMastery);
    CHECK_EQ(tooHard.blockItemId, HasteItemId);
}

TEST_CASE("alchemy black potion discoveries survive a fresh map and a save round trip")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    Party party = makeParty(gameData, 1);
    giveAlchemy(party, 0, 10, SkillMastery::Grandmaster);
    const AlchemyBenchTables tables = benchTables(gameData);
    EventRuntimeState mapState = {};
    const std::vector<uint32_t> blackPotions = {266, 267, 268, 270};

    for (uint32_t itemId : blackPotions)
    {
        const std::vector<uint32_t> notes = AlchemyBenchRuntime::potionNoteIds(itemId, tables);
        REQUIRE_FALSE(notes.empty());
        const auto found = std::find_if(gameData.potionNoteTable.entries().begin(),
            gameData.potionNoteTable.entries().end(), [&notes](const PotionNoteTable::Entry &entry)
            {
                return entry.autonoteId == notes.front();
            });
        REQUIRE(found != gameData.potionNoteTable.entries().end());
        addItem(party, 0, found->targetItemId);
        addItem(party, 0, found->heldItemId);
        const AlchemyMixOutcome outcome =
            AlchemyBenchRuntime::mix(party, {found->targetItemId, found->heldItemId}, tables);
        REQUIRE(outcome.result.success);
        CHECK_EQ(outcome.resultItem.objectDescriptionId, itemId);
        REQUIRE_NE(outcome.result.unlockedAutonoteId, 0u);
        EventRuntime::setVariableValue(mapState,
            EventRuntime::decodeVariable((outcome.result.unlockedAutonoteId << 16) | 0x00e1u), 1, &party, {0});
    }

    CHECK(mapState.variables.empty());
    mapState = {};
    for (uint32_t itemId : blackPotions)
    {
        const uint32_t noteId = AlchemyBenchRuntime::potionNoteIds(itemId, tables).front();
        CHECK_NE(EventRuntime::getVariableValue(mapState,
            EventRuntime::decodeVariable((noteId << 16) | 0x00dfu), &party), 0);
    }

    GameSaveData save = {};
    save.party = party.snapshot();
    const std::filesystem::path path =
        std::filesystem::temp_directory_path() / "openyamm_black_potion_discoveries.oysav";
    std::string error;
    REQUIRE(saveGameDataToPath(path, save, error));
    const std::optional<GameSaveData> loaded = loadGameDataFromPath(path, error);
    std::filesystem::remove(path);
    REQUIRE_MESSAGE(loaded.has_value(), error);
    Party restored = makeParty(gameData, 1);
    restored.restoreSnapshot(loaded->party);
    const AlchemyBook book = AlchemyBenchRuntime::buildBook(tables, {}, SkillMastery::Grandmaster,
        [&restored](uint32_t noteId) { return restored.hasAutonote(noteId); });
    for (uint32_t itemId : blackPotions)
    {
        CHECK(findEntry(book, itemId) != nullptr);
    }
}

TEST_CASE("alchemy chain planner keeps carried mixed potions when asked and brews them fresh")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    Party party = makeParty(gameData, 1);
    giveAlchemy(party, 0, 4, SkillMastery::Expert);
    for (int index = 0; index < 3; ++index)
    {
        addItem(party, 0, BottleItemId);
    }
    addItem(party, 0, WidowsweepBerriesItemId);
    addItem(party, 0, WidowsweepBerriesItemId);
    addItem(party, 0, PoppyPodItemId);
    addItem(party, 0, CureDiseaseItemId, 9);
    const AlchemyBenchTables tables = benchTables(gameData);
    const AlchemyBook book = knownBook(party, tables, {CureDiseaseNoteId, HasteNoteId});
    CHECK(book.isMixedPotion(CureDiseaseItemId));
    CHECK(book.isMixedPotion(HasteItemId));
    CHECK_FALSE(book.isMixedPotion(CureWoundsItemId));
    CHECK_FALSE(book.isMixedPotion(BottleItemId));

    const AlchemyChainPlan plan =
        AlchemyChainPlanner(party, book, level4Alchemist(), tables, true).plan(HasteItemId, 99);

    // As with nothing carried: Cure Disease is brewed first, the carried one is set aside.
    CHECK_EQ(plan.brewCount, 1u);
    CHECK_EQ(plan.steps.size(), 5u);
    CHECK_EQ(countOf(plan.brewedFirst, CureDiseaseItemId), 1u);
    CHECK_EQ(countOf(plan.used, CureDiseaseItemId), 0u);
    REQUIRE_EQ(plan.kept.size(), 1u);
    CHECK_EQ(plan.kept.front().itemId, CureDiseaseItemId);

    const AlchemyChainOutcome outcome = AlchemyBenchRuntime::brewChain(party, plan, tables);
    CHECK_EQ(outcome.brewedCount, 1u);
    CHECK_EQ(party.inventoryItemCount(HasteItemId), 1);
    REQUIRE_EQ(party.inventoryItemCount(CureDiseaseItemId), 1);
    // The very potion carried before, though the one brewed on the way was weaker.
    for (const InventoryItem &item : party.member(0)->inventory)
    {
        if (item.objectDescriptionId == CureDiseaseItemId)
        {
            CHECK_EQ(item.standardEnchantPower, 9);
        }
    }

    // The book's direct counts leave the carried mixed potion out too.
    Party direct = makeParty(gameData, 1);
    giveAlchemy(direct, 0, 4, SkillMastery::Expert);
    addItem(direct, 0, CureWoundsItemId, 5);
    addItem(direct, 0, CureDiseaseItemId, 9);
    const std::vector<AlchemyIngredient> ingredients = AlchemyBenchRuntime::collectIngredients(direct, tables);
    const auto hasteCount = [&](bool keep)
    {
        const AlchemyBook counted = AlchemyBenchRuntime::buildBook(tables, ingredients, SkillMastery::Expert,
            unlocked({CureDiseaseNoteId, HasteNoteId}), keep);
        const auto found = std::find_if(counted.entries.begin(), counted.entries.end(),
            [](const AlchemyBookEntry &entry)
            {
                return entry.resultItemId == HasteItemId;
            });
        return found != counted.entries.end() ? found->brewableCount : 0u;
    };
    CHECK_EQ(hasteCount(false), 1u);
    CHECK_EQ(hasteCount(true), 0u);
}

TEST_CASE("alchemy bench mixes the copies of the powers the player chose")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    Party party = makeParty(gameData, 2);
    giveAlchemy(party, 0, 4, SkillMastery::Expert);
    addItem(party, 0, CureWoundsItemId, 2);
    addItem(party, 0, CureWoundsItemId, 8);
    addItem(party, 1, CureWoundsItemId, 2);
    addItem(party, 1, CureDiseaseItemId, 6);
    addItem(party, 1, CureDiseaseItemId, 10);
    const AlchemyBenchTables tables = benchTables(gameData);
    const AlchemyRecipe haste = {CureWoundsItemId, CureDiseaseItemId};

    const std::vector<AlchemyPowerOption> options = AlchemyBenchRuntime::powerOptions(party, CureWoundsItemId, tables);
    REQUIRE_EQ(options.size(), 2u);
    CHECK_EQ(options[0].power, 8u);
    CHECK_EQ(options[0].count, 1u);
    CHECK_EQ(options[1].power, 2u);
    CHECK_EQ(options[1].count, 2u);

    // Left to the bench, both slots take their strongest copy.
    const AlchemyPreview strongest = AlchemyBenchRuntime::preview(party, haste, tables, unlocked({HasteNoteId}));
    CHECK_EQ(strongest.targetPower, 8u);
    CHECK_EQ(strongest.heldPower, 10u);
    CHECK_EQ(strongest.resultPower, 9u);

    const AlchemyPowerChoice weakest = {uint16_t(2), uint16_t(6)};
    const AlchemyPreview chosen = AlchemyBenchRuntime::preview(party, haste, tables, unlocked({HasteNoteId}), weakest);
    CHECK_EQ(chosen.outcome, AlchemyPreviewOutcome::Known);
    CHECK_EQ(chosen.targetPower, 2u);
    CHECK_EQ(chosen.heldPower, 6u);
    CHECK_EQ(chosen.resultPower, 4u);

    // One slot chosen, the other left to the bench.
    const AlchemyPreview mixed =
        AlchemyBenchRuntime::preview(party, haste, tables, unlocked({HasteNoteId}), {uint16_t(2), std::nullopt});
    CHECK_EQ(mixed.targetPower, 2u);
    CHECK_EQ(mixed.heldPower, 10u);

    // Two weak Cure Wounds, one weak Cure Disease.
    CHECK_EQ(AlchemyBenchRuntime::brewableCount(party, haste, weakest, tables), 1u);
    CHECK_EQ(AlchemyBenchRuntime::brewableCount(party, haste, {uint16_t(2), std::nullopt}, tables), 2u);

    const AlchemyMixOutcome outcome = AlchemyBenchRuntime::mix(party, haste, tables, {}, weakest);
    REQUIRE(outcome.result.success);
    CHECK_EQ(outcome.resultItem.objectDescriptionId, HasteItemId);
    CHECK_EQ(outcome.resultItem.standardEnchantPower, 4u);

    // The strong copies are still there, and the used-up power 6 is no longer a choice.
    const std::vector<AlchemyPowerOption> left = AlchemyBenchRuntime::powerOptions(party, CureWoundsItemId, tables);
    REQUIRE_EQ(left.size(), 2u);
    CHECK_EQ(left[0].power, 8u);
    CHECK_EQ(left[1].count, 1u);
    const AlchemyPowerChoice remaining = AlchemyBenchRuntime::availableChoice(party, haste, weakest, tables);
    CHECK_EQ(remaining.targetPower, std::optional<uint16_t>(2));
    CHECK_FALSE(remaining.heldPower.has_value());

    // A chosen power without a copy mixes nothing.
    const AlchemyMixOutcome none = AlchemyBenchRuntime::mix(party, haste, tables, {}, weakest);
    CHECK_FALSE(none.result.handled);
    CHECK_EQ(party.inventoryItemCount(CureDiseaseItemId), 1);
}

TEST_CASE("alchemy bench power choices of one potion in both slots take separate copies")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    Party party = makeParty(gameData, 1);
    giveAlchemy(party, 0, 4, SkillMastery::Expert);
    addItem(party, 0, CureWoundsItemId, 3);
    addItem(party, 0, CureWoundsItemId, 9);
    addItem(party, 0, CureWoundsItemId, 5);
    const AlchemyBenchTables tables = benchTables(gameData);
    const AlchemyRecipe pair = {CureWoundsItemId, CureWoundsItemId};

    // The held slot's chosen copy is found first; the target left to the bench takes the strongest of the rest.
    const AlchemyPreview heldChosen =
        AlchemyBenchRuntime::preview(party, pair, tables, unlocked({}), {std::nullopt, uint16_t(9)});
    CHECK_EQ(heldChosen.heldPower, 9u);
    CHECK_EQ(heldChosen.targetPower, 5u);

    // Only one copy has power 9: both slots cannot choose it.
    const AlchemyPowerChoice both =
        AlchemyBenchRuntime::availableChoice(party, pair, {uint16_t(9), uint16_t(9)}, tables);
    CHECK_EQ(both.targetPower, std::optional<uint16_t>(9));
    CHECK_FALSE(both.heldPower.has_value());

    CHECK_EQ(AlchemyBenchRuntime::brewableCount(party, pair, {uint16_t(3), uint16_t(5)}, tables), 1u);
    CHECK_EQ(AlchemyBenchRuntime::brewableCount(party, pair, {std::nullopt, uint16_t(3)}, tables), 1u);
}

TEST_CASE("alchemy bench catalyst boosts the chosen copy instead of the one it raises most")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    Party party = makeParty(gameData, 1);
    giveAlchemy(party, 0, 4, SkillMastery::Expert);
    const AlchemyBenchTables tables = benchTables(gameData);
    const uint32_t catalystItemId = tables.potionSettingTable.catalystPotionItemId();
    REQUIRE_NE(catalystItemId, 0u);
    addItem(party, 0, CureWoundsItemId, 30);
    addItem(party, 0, CureWoundsItemId, 2);
    addItem(party, 0, CureWoundsItemId, 10);
    addItem(party, 0, catalystItemId, 20);
    addItem(party, 0, catalystItemId, 12);
    const AlchemyRecipe boost = {CureWoundsItemId, catalystItemId};

    const AlchemyPowerChoice choice = {uint16_t(10), uint16_t(12)};
    const AlchemyPreview preview = AlchemyBenchRuntime::preview(party, boost, tables, unlocked({}), choice);
    CHECK_EQ(preview.outcome, AlchemyPreviewOutcome::Known);
    CHECK_EQ(preview.targetPower, 10u);
    CHECK_EQ(preview.heldPower, 12u);
    CHECK_EQ(preview.resultPower, 12u);

    REQUIRE(AlchemyBenchRuntime::mix(party, boost, tables, {}, choice).result.success);
    std::multiset<uint16_t> powers;

    for (const AlchemyPowerOption &option : AlchemyBenchRuntime::powerOptions(party, CureWoundsItemId, tables))
    {
        powers.insert(option.power);
    }

    CHECK_EQ(powers, std::multiset<uint16_t>{2, 12, 30});
    const std::vector<AlchemyPowerOption> catalysts = AlchemyBenchRuntime::powerOptions(party, catalystItemId, tables);
    REQUIRE_EQ(catalysts.size(), 1u);
    CHECK_EQ(catalysts[0].power, 20u);
}

TEST_CASE("alchemy bench tells a swapped bottle and reagent their own slots' powers")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    Party party = makeParty(gameData, 1);
    giveAlchemy(party, 0, 4, SkillMastery::Expert);
    addItem(party, 0, BottleItemId);
    addItem(party, 0, WidowsweepBerriesItemId);
    const AlchemyBenchTables tables = benchTables(gameData);
    const std::vector<AlchemyPowerOption> reagent =
        AlchemyBenchRuntime::powerOptions(party, WidowsweepBerriesItemId, tables);
    REQUIRE_EQ(reagent.size(), 1u);
    REQUIRE_GT(reagent[0].power, 0u);

    // The reagent in the target slot is mixed as the held item, and still reads as the target slot's power.
    const AlchemyPreview preview =
        AlchemyBenchRuntime::preview(party, {WidowsweepBerriesItemId, BottleItemId}, tables, unlocked({}));
    CHECK_EQ(preview.outcome, AlchemyPreviewOutcome::Known);
    CHECK_EQ(preview.targetPower, reagent[0].power);
    CHECK_EQ(preview.heldPower, 0u);
}

TEST_CASE("alchemy chain planner aims at a power with the weakest ingredients that reach it")
{
    constexpr uint32_t WolfsEyeItemId = 201;
    constexpr uint32_t GogBloodItemId = 202;
    constexpr uint32_t PhoenixFeatherItemId = 204;
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    Party party = makeParty(gameData, 2);
    giveAlchemy(party, 0, 4, SkillMastery::Expert);

    for (int index = 0; index < 6; ++index)
    {
        addItem(party, 1, BottleItemId);
    }

    // Cure Wounds reagents of four strengths, and two for Cure Weakness.
    addItem(party, 0, WidowsweepBerriesItemId);
    addItem(party, 0, WidowsweepBerriesItemId);
    addItem(party, 0, WolfsEyeItemId);
    addItem(party, 0, GogBloodItemId);
    addItem(party, 0, PhoenixFeatherItemId);
    addItem(party, 0, PoppyPodItemId);
    addItem(party, 0, PoppyPodItemId);
    const AlchemyBenchTables tables = benchTables(gameData);
    const AlchemyBook book = knownBook(party, tables, {CureDiseaseNoteId, HasteNoteId});
    const AlchemyChainPlanner planner(party, book, level4Alchemist(), tables);

    const AlchemyChainPlan strongest = planner.plan(HasteItemId, 1);
    REQUIRE_EQ(strongest.brewCount, 1u);
    // Without an aim the steps leave the copies to the bench.
    CHECK_FALSE(strongest.steps.back().choice.any());

    const std::vector<AlchemyChainPowerOption> options = planner.powerOptions(HasteItemId);
    REQUIRE_GE(options.size(), 3u);
    CHECK_LT(options.front().power, strongest.resultPower);
    CHECK_GE(options.back().power, strongest.resultPower);

    for (size_t index = 0; index < options.size(); ++index)
    {
        // Weakest first, and each aim brews exactly the power it is listed with.
        if (index > 0)
        {
            CHECK_GT(options[index].power, options[index - 1].power);
        }

        const AlchemyChainPlan aimed = planner.plan(HasteItemId, 1, options[index].aim);
        REQUIRE_EQ(aimed.brewCount, 1u);
        CHECK_EQ(aimed.resultPower, options[index].power);
        CHECK(aimed.steps.back().choice.targetPower.has_value());
        CHECK(aimed.steps.back().choice.heldPower.has_value());
        CHECK_EQ(planner.aimForPower(HasteItemId, options[index].power), std::optional<uint16_t>(options[index].aim));
    }

    // Nothing brews past the strongest power.
    CHECK_EQ(planner.plan(HasteItemId, 1, uint16_t(options.back().power + 1)).brewCount, 0u);
    CHECK_FALSE(planner.aimForPower(HasteItemId, uint16_t(options.back().power + 1)).has_value());

    // Brewing follows the plan copy by copy: the weakest potion leaves the Phoenix Feather alone.
    {
        Party weakParty = party;
        const AlchemyChainPlan weakest = planner.plan(HasteItemId, 1, options.front().aim);
        const AlchemyChainOutcome outcome = AlchemyBenchRuntime::brewChain(weakParty, weakest, tables);
        REQUIRE_EQ(outcome.brewedCount, 1u);
        CHECK_EQ(outcome.lastBrewed.standardEnchantPower, options.front().power);
        CHECK_EQ(weakParty.inventoryItemCount(PhoenixFeatherItemId), 1);
        CHECK_EQ(weakParty.inventoryItemCount(WidowsweepBerriesItemId), 0);
    }

    for (const AlchemyChainPowerOption &option : options)
    {
        Party brewingParty = party;
        const AlchemyChainOutcome outcome =
            AlchemyBenchRuntime::brewChain(brewingParty, planner.plan(HasteItemId, 1, option.aim), tables);
        REQUIRE_EQ(outcome.brewedCount, 1u);
        CHECK_EQ(outcome.lastBrewed.standardEnchantPower, option.power);
    }

    // Every potion of a longer plan reaches the aim, and the brewing gives what was planned.
    const AlchemyChainPlan all = planner.plan(HasteItemId, 99, options.front().aim);
    CHECK_EQ(all.brewCount, 2u);
    Party allParty = party;
    const AlchemyChainOutcome brewedAll = AlchemyBenchRuntime::brewChain(allParty, all, tables);
    CHECK_EQ(brewedAll.brewedCount, 2u);
    CHECK_EQ(brewedAll.stepsDone, all.steps.size());

    for (const AlchemyPowerOption &brewed : AlchemyBenchRuntime::powerOptions(allParty, HasteItemId, tables))
    {
        CHECK_GE(brewed.power, options.front().power);
    }
}

TEST_CASE("alchemy chain planner aims with carried potions before brewing stronger ones")
{
    constexpr uint32_t PhoenixFeatherItemId = 204;
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    Party party = makeParty(gameData, 1);
    giveAlchemy(party, 0, 4, SkillMastery::Expert);
    addItem(party, 0, BottleItemId);
    addItem(party, 0, BottleItemId);
    addItem(party, 0, WidowsweepBerriesItemId);
    addItem(party, 0, PhoenixFeatherItemId);
    addItem(party, 0, CureDiseaseItemId, 9);
    addItem(party, 0, CureDiseaseItemId, 40);
    const AlchemyBenchTables tables = benchTables(gameData);
    const AlchemyBook book = knownBook(party, tables, {CureDiseaseNoteId, HasteNoteId});
    const AlchemyChainPlanner planner(party, book, level4Alchemist(), tables);

    // The lowest aim takes the weak Cure Disease and the weak reagent: (5 + 9) / 2.
    const AlchemyChainPlan weakest = planner.plan(HasteItemId, 1, uint16_t(0));
    REQUIRE_EQ(weakest.brewCount, 1u);
    CHECK_EQ(weakest.resultPower, 7u);
    CHECK_EQ(weakest.steps.size(), 2u);

    // One above it, the stronger Cure Disease makes up for the weak reagent.
    const AlchemyChainPlan next = planner.plan(HasteItemId, 1, uint16_t(8));
    REQUIRE_EQ(next.brewCount, 1u);
    CHECK_GE(next.resultPower, 8u);
    CHECK_EQ(countOf(next.used, PhoenixFeatherItemId) + countOf(next.used, WidowsweepBerriesItemId), 1u);

    Party brewingParty = party;
    const AlchemyChainOutcome outcome = AlchemyBenchRuntime::brewChain(brewingParty, next, tables);
    REQUIRE_EQ(outcome.brewedCount, 1u);
    CHECK_EQ(outcome.lastBrewed.standardEnchantPower, next.resultPower);
}
