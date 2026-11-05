#include "doctest/doctest.h"

#include "game/items/AlchemyBenchRuntime.h"
#include "game/party/Party.h"

#include "tests/RegressionGameData.h"

#include <algorithm>
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
