#include "doctest/doctest.h"

#include "game/gameplay/GenericActorDialog.h"
#include "game/gameplay/HouseInteraction.h"
#include "game/gameplay/HouseServiceRuntime.h"
#include "game/items/PriceCalculator.h"
#include "game/party/SpellIds.h"

#include "tests/HouseDialogueTestHarness.h"
#include "tests/RegressionGameData.h"

#include <algorithm>
#include <optional>
#include <string>
#include <utility>
#include <vector>

namespace
{
constexpr uint32_t TempleHouseId = 74;
constexpr uint32_t ElementalGuildHouseId = 139;
constexpr uint32_t TrainingHallHouseId = 91;
constexpr uint32_t BankHouseId = 128;
constexpr uint32_t AdventurersInnHouseId = 185;
constexpr uint32_t BrekishHallHouseId = 173;
constexpr uint32_t FredrickHouseId = 237;
constexpr uint32_t HissHouseId = 224;
constexpr uint32_t MasterIdentifyItemTeacherNpcId = 388;
constexpr uint32_t SandroNpcId = 9;
constexpr uint32_t DysonNpcId = 11;
constexpr uint32_t LongTailNpcId = 279;
constexpr uint32_t FredrickNpcId = 32;
constexpr uint32_t DysonDirectNpcId = 483;
constexpr uint32_t RohaniNpcId = 455;
constexpr uint32_t StephenNpcId = 72;

const OpenYAMM::Game::Character *findPartyMemberByRosterId(
    const OpenYAMM::Game::Party &party,
    uint32_t rosterId)
{
    for (const OpenYAMM::Game::Character &member : party.members())
    {
        if (member.rosterId == rosterId)
        {
            return &member;
        }
    }

    return nullptr;
}

bool innEquipmentItemIdentified(
    const OpenYAMM::Game::EquippedItemRuntimeState &runtimeState,
    uint32_t equippedItemId)
{
    return equippedItemId == 0 || runtimeState.identified;
}

const OpenYAMM::Tests::RegressionGameData &requireRegressionGameData()
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());
    return OpenYAMM::Tests::regressionGameData();
}

bool dialogContainsText(const OpenYAMM::Game::EventDialogContent &dialog, const std::string &text)
{
    for (const std::string &line : dialog.lines)
    {
        if (line.find(text) != std::string::npos)
        {
            return true;
        }
    }

    return false;
}

bool dialogHasActionLabel(const OpenYAMM::Game::EventDialogContent &dialog, const std::string &label)
{
    for (const OpenYAMM::Game::EventDialogAction &action : dialog.actions)
    {
        if (action.label == label)
        {
            return true;
        }
    }

    return false;
}

std::optional<size_t> findActionIndexByLabel(
    const OpenYAMM::Game::EventDialogContent &dialog,
    const std::string &label)
{
    for (size_t actionIndex = 0; actionIndex < dialog.actions.size(); ++actionIndex)
    {
        if (dialog.actions[actionIndex].label == label)
        {
            return actionIndex;
        }
    }

    return std::nullopt;
}

bool houseActionsContainDestination(
    const std::vector<OpenYAMM::Game::HouseActionOption> &actions,
    const std::string &destination)
{
    for (const OpenYAMM::Game::HouseActionOption &action : actions)
    {
        if (action.label.find(destination) != std::string::npos)
        {
            return true;
        }
    }

    return false;
}

std::optional<OpenYAMM::Game::HouseActionOption> findHouseActionById(
    const std::vector<OpenYAMM::Game::HouseActionOption> &actions,
    OpenYAMM::Game::HouseActionId actionId)
{
    for (const OpenYAMM::Game::HouseActionOption &action : actions)
    {
        if (action.id == actionId)
        {
            return action;
        }
    }

    return std::nullopt;
}

std::optional<size_t> findActionIndexByLabelPrefix(
    const OpenYAMM::Game::EventDialogContent &dialog,
    const std::string &labelPrefix)
{
    for (size_t actionIndex = 0; actionIndex < dialog.actions.size(); ++actionIndex)
    {
        if (dialog.actions[actionIndex].label.rfind(labelPrefix, 0) == 0)
        {
            return actionIndex;
        }
    }

    return std::nullopt;
}

std::vector<std::string> collectActionLabels(const OpenYAMM::Game::EventDialogContent &dialog)
{
    std::vector<std::string> labels;

    for (const OpenYAMM::Game::EventDialogAction &action : dialog.actions)
    {
        labels.push_back(action.label);
    }

    return labels;
}

int firstTreasureLevelForItem(const OpenYAMM::Game::ItemDefinition &itemDefinition)
{
    for (size_t tierIndex = 0; tierIndex < itemDefinition.randomTreasureWeights.size(); ++tierIndex)
    {
        if (itemDefinition.randomTreasureWeights[tierIndex] > 0)
        {
            return static_cast<int>(tierIndex) + 1;
        }
    }

    return 0;
}

bool itemHasTreasureWeightAtOrAboveTier(const OpenYAMM::Game::ItemDefinition &itemDefinition, int tier)
{
    const int startTier = std::clamp(tier, 1, static_cast<int>(itemDefinition.randomTreasureWeights.size())) - 1;

    for (size_t tierIndex = static_cast<size_t>(startTier); tierIndex < itemDefinition.randomTreasureWeights.size();
         ++tierIndex)
    {
        if (itemDefinition.randomTreasureWeights[tierIndex] > 0)
        {
            return true;
        }
    }

    return false;
}

OpenYAMM::Game::CharacterSkill *setCharacterSkill(
    OpenYAMM::Game::Character &character,
    const std::string &skillName,
    uint32_t level,
    OpenYAMM::Game::SkillMastery mastery)
{
    character.skills[skillName] = {skillName, level, mastery};
    return character.findSkill(skillName);
}

OpenYAMM::Game::EventRuntimeState::DialogueOfferState makeRosterJoinOffer(
    uint32_t npcId,
    uint32_t rosterId,
    uint32_t messageTextId,
    uint32_t partyFullTextId)
{
    OpenYAMM::Game::EventRuntimeState::DialogueOfferState invite = {};
    invite.kind = OpenYAMM::Game::DialogueOfferKind::RosterJoin;
    invite.npcId = npcId;
    invite.rosterId = rosterId;
    invite.messageTextId = messageTextId;
    invite.partyFullTextId = partyFullTextId;
    return invite;
}

void advanceBrekishQuest(OpenYAMM::Tests::HouseDialogueTestHarness &harness)
{
    const OpenYAMM::Game::EventDialogContent &hallDialog = harness.openHouseDialog(BrekishHallHouseId);
    const std::optional<size_t> brekishIndex = findActionIndexByLabel(hallDialog, "Brekish Onefang");

    REQUIRE(brekishIndex.has_value());
    const OpenYAMM::Game::EventDialogContent &brekishDialog = harness.executeAndPresent(*brekishIndex);
    const std::optional<size_t> portalsIndex = findActionIndexByLabel(brekishDialog, "Portals of Stone");

    REQUIRE(portalsIndex.has_value());
    const OpenYAMM::Game::EventDialogContent &portalsDialog = harness.executeAndPresent(*portalsIndex);
    const std::optional<size_t> questIndex = findActionIndexByLabel(portalsDialog, "Quest");

    REQUIRE(questIndex.has_value());
    harness.executeAndPresent(*questIndex);
}
}

TEST_CASE("generic actor dialog resolves lizardman portraits")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    const OpenYAMM::Game::EventRuntimeState runtimeState = {};

    const std::optional<OpenYAMM::Game::GenericActorDialogResolution> villagerResolution =
        OpenYAMM::Game::resolveGenericActorDialog(
            "out01.odm",
            "Lizardman Villager",
            1,
            runtimeState,
            gameData.npcDialogTable);
    REQUIRE(villagerResolution.has_value());
    CHECK_EQ(villagerResolution->npcId, 516u);

    const std::optional<OpenYAMM::Game::GenericActorDialogResolution> soldierResolution =
        OpenYAMM::Game::resolveGenericActorDialog(
            "out01.odm",
            "Lizardman Soldier",
            2,
            runtimeState,
            gameData.npcDialogTable);
    REQUIRE(soldierResolution.has_value());
    CHECK_EQ(soldierResolution->npcId, 517u);

    const std::optional<OpenYAMM::Game::GenericActorDialogResolution> guardResolution =
        OpenYAMM::Game::resolveGenericActorDialog(
            "out01.odm",
            "Guard",
            9,
            runtimeState,
            gameData.npcDialogTable);
    REQUIRE(guardResolution.has_value());
    CHECK_EQ(guardResolution->npcId, 517u);
}

TEST_CASE("dwi actor peasant news")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const std::optional<OpenYAMM::Game::GenericActorDialogResolution> resolution =
        OpenYAMM::Game::resolveGenericActorDialog(
            "out01.odm",
            "Lizardman Peasant",
            1,
            harness.eventRuntimeState(),
            gameData.npcDialogTable);
    REQUIRE(resolution.has_value());

    const OpenYAMM::Game::NpcEntry *pNpc = gameData.npcDialogTable.getNpc(resolution->npcId);
    REQUIRE(pNpc != nullptr);
    const std::optional<std::string> newsText = gameData.npcDialogTable.getNewsText(resolution->newsId);
    REQUIRE(newsText.has_value());

    const OpenYAMM::Game::EventDialogContent &dialog =
        harness.openNpcNews(resolution->npcId, resolution->newsId, "Lizardman Peasant", *newsText);

    CHECK_EQ(dialog.title, "Lizardman Peasant");
    CHECK_EQ(dialog.participantPictureId, 800u);
    CHECK(dialogContainsText(dialog, "If the pirates make it through our warriors"));
}

TEST_CASE("dwi actor lookout news")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const std::optional<OpenYAMM::Game::GenericActorDialogResolution> resolution =
        OpenYAMM::Game::resolveGenericActorDialog(
            "out01.odm",
            "Lizardman Lookout",
            9,
            harness.eventRuntimeState(),
            gameData.npcDialogTable);
    REQUIRE(resolution.has_value());

    const OpenYAMM::Game::NpcEntry *pNpc = gameData.npcDialogTable.getNpc(resolution->npcId);
    REQUIRE(pNpc != nullptr);
    const std::optional<std::string> newsText = gameData.npcDialogTable.getNewsText(resolution->newsId);
    REQUIRE(newsText.has_value());

    const OpenYAMM::Game::EventDialogContent &dialog =
        harness.openNpcNews(resolution->npcId, resolution->newsId, "Lizardman Lookout", *newsText);

    CHECK(dialogContainsText(dialog, "Would you like to fire the cannons"));
}

TEST_CASE("single resident auto open")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const OpenYAMM::Game::EventDialogContent &dialog = harness.openHouseDialog(237);

    CHECK_EQ(dialog.title, "Fredrick Talimere");
    CHECK(dialogHasActionLabel(dialog, "Portals of Stone"));
    CHECK(dialogHasActionLabel(dialog, "Cataclysm"));
}

TEST_CASE("fredrick initial topics exact")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const OpenYAMM::Game::EventDialogContent &dialog = harness.openHouseDialog(237);
    const std::vector<std::string> expectedLabels = {
        "Portals of Stone",
        "Cataclysm",
    };

    CHECK(collectActionLabels(dialog) == expectedLabels);
}

TEST_CASE("multi resident house selection")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const OpenYAMM::Game::EventDialogContent &dialog = harness.openHouseDialog(173);

    CHECK_EQ(dialog.title, "Clan Leader's Hall");
    CHECK(dialogHasActionLabel(dialog, "Brekish Onefang"));
    CHECK(dialogHasActionLabel(dialog, "Dadeross"));
}

TEST_CASE("brekish topic mutation")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const OpenYAMM::Game::EventDialogContent &hallDialog = harness.openHouseDialog(BrekishHallHouseId);
    const std::optional<size_t> brekishIndex = findActionIndexByLabel(hallDialog, "Brekish Onefang");

    REQUIRE(brekishIndex.has_value());
    const OpenYAMM::Game::EventDialogContent &brekishDialog = harness.executeAndPresent(*brekishIndex);
    const std::optional<size_t> portalsIndex = findActionIndexByLabel(brekishDialog, "Portals of Stone");

    REQUIRE(portalsIndex.has_value());
    const OpenYAMM::Game::EventDialogContent &updatedDialog = harness.executeAndPresent(*portalsIndex);

    CHECK(dialogHasActionLabel(updatedDialog, "Quest"));
}

TEST_CASE("fredrick topics after brekish quest")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    advanceBrekishQuest(harness);

    const OpenYAMM::Game::EventDialogContent &dialog = harness.openHouseDialog(FredrickHouseId);

    CHECK(dialogHasActionLabel(dialog, "Power Stone"));
    CHECK(dialogHasActionLabel(dialog, "Abandoned Temple"));
}

TEST_CASE("fredrick topics exact after brekish quest")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    advanceBrekishQuest(harness);

    const OpenYAMM::Game::EventDialogContent &dialog = harness.openHouseDialog(FredrickHouseId);
    const std::vector<std::string> expectedLabels = {
        "Portals of Stone",
        "Cataclysm",
        "Power Stone",
        "Abandoned Temple",
    };

    CHECK(collectActionLabels(dialog) == expectedLabels);
}

TEST_CASE("award gated topic stephen")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    OpenYAMM::Game::EventDialogContent dialog = harness.openNpcDialogue(StephenNpcId);
    CHECK(dialogHasActionLabel(dialog, "Clues"));

    harness.party().addAward(30);
    dialog = harness.openNpcDialogue(StephenNpcId);
    CHECK_FALSE(dialogHasActionLabel(dialog, "Clues"));

    harness.party().removeAward(30);
    harness.party().addAward(31);
    dialog = harness.openNpcDialogue(StephenNpcId);
    CHECK_FALSE(dialogHasActionLabel(dialog, "Clues"));

    harness.party().removeAward(31);
    dialog = harness.openNpcDialogue(StephenNpcId);
    CHECK(dialogHasActionLabel(dialog, "Clues"));
}

TEST_CASE("hiss quest followup persists across reentry")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const OpenYAMM::Game::EventDialogContent &dialog = harness.openHouseDialog(HissHouseId);
    const std::optional<size_t> questIndex = findActionIndexByLabel(dialog, "Quest");

    REQUIRE(questIndex.has_value());
    harness.executeAndPresent(*questIndex);

    harness.uiController().clearEventDialog();
    harness.eventRuntimeState().pendingDialogueContext.reset();
    harness.eventRuntimeState().dialogueState = {};
    harness.eventRuntimeState().messages.clear();

    const OpenYAMM::Game::EventDialogContent &reenteredDialog = harness.openHouseDialog(HissHouseId);
    const std::optional<size_t> idolIndex = findActionIndexByLabel(reenteredDialog, "Do you have the Idol?");

    REQUIRE(idolIndex.has_value());
    const OpenYAMM::Game::EventDialogContent &followupDialog = harness.executeAndPresent(*idolIndex);

    CHECK(dialogContainsText(followupDialog, "Where is the Idol?  Do not waste my time unless you have it!"));
}

TEST_CASE("dwi shop service menu structure")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const OpenYAMM::Game::EventDialogContent &rootDialog = harness.openHouseDialog(1);

    CHECK(dialogHasActionLabel(rootDialog, "Buy Standard"));
    CHECK(dialogHasActionLabel(rootDialog, "Buy Special"));
    CHECK(dialogHasActionLabel(rootDialog, "Display Equipment"));
    CHECK(dialogHasActionLabel(rootDialog, "Learn Skills"));

    const std::optional<size_t> equipmentIndex = findActionIndexByLabel(rootDialog, "Display Equipment");
    REQUIRE(equipmentIndex.has_value());

    const OpenYAMM::Game::EventDialogContent &equipmentDialog = harness.executeAndPresent(*equipmentIndex);

    CHECK(dialogHasActionLabel(equipmentDialog, "Sell"));
    CHECK(dialogHasActionLabel(equipmentDialog, "Identify"));
    CHECK(dialogHasActionLabel(equipmentDialog, "Repair"));

    const std::optional<size_t> sellIndex = findActionIndexByLabel(equipmentDialog, "Sell");
    const std::optional<size_t> identifyIndex = findActionIndexByLabel(equipmentDialog, "Identify");
    const std::optional<size_t> repairIndex = findActionIndexByLabel(equipmentDialog, "Repair");

    REQUIRE(sellIndex.has_value());
    REQUIRE(identifyIndex.has_value());
    REQUIRE(repairIndex.has_value());
    CHECK(equipmentDialog.actions[*sellIndex].enabled);
    CHECK(equipmentDialog.actions[*identifyIndex].enabled);
    CHECK(equipmentDialog.actions[*repairIndex].enabled);
}

TEST_CASE("house service shop standard stock generates and buys")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::HouseEntry *pHouseEntry = gameData.houseTable.get(1);
    REQUIRE(pHouseEntry != nullptr);

    harness.party().addGold(50000);
    const std::vector<OpenYAMM::Game::InventoryItem> &stock = OpenYAMM::Game::HouseServiceRuntime::ensureStock(
        harness.party(),
        gameData.itemTable,
        gameData.standardItemEnchantTable,
        gameData.specialItemEnchantTable,
        *pHouseEntry,
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::HouseStockMode::ShopStandard);
    const auto stockIt =
        std::find_if(stock.begin(), stock.end(), [](const OpenYAMM::Game::InventoryItem &item)
    {
        return item.objectDescriptionId != 0;
    });

    REQUIRE(stockIt != stock.end());
    const size_t slotIndex = static_cast<size_t>(std::distance(stock.begin(), stockIt));
    const int initialGold = harness.party().gold();
    const size_t initialInventoryCount = harness.party().inventoryItemCount();
    std::string statusText;

    REQUIRE(OpenYAMM::Game::HouseServiceRuntime::tryBuyStockItem(
        harness.party(),
        gameData.itemTable,
        gameData.standardItemEnchantTable,
        gameData.specialItemEnchantTable,
        *pHouseEntry,
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::HouseStockMode::ShopStandard,
        slotIndex,
        statusText));
    CHECK_LT(harness.party().gold(), initialGold);
    CHECK_GT(harness.party().inventoryItemCount(), initialInventoryCount);
}

TEST_CASE("house service shop stock uses house data tiers")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::HouseEntry *pHouseEntry = gameData.houseTable.get(1);
    REQUIRE(pHouseEntry != nullptr);

    CHECK_EQ(pHouseEntry->standardStockTier, 1);
    CHECK_EQ(pHouseEntry->specialStockTier, 2);

    const std::vector<OpenYAMM::Game::InventoryItem> &standardStock = OpenYAMM::Game::HouseServiceRuntime::ensureStock(
        harness.party(),
        gameData.itemTable,
        gameData.standardItemEnchantTable,
        gameData.specialItemEnchantTable,
        *pHouseEntry,
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::HouseStockMode::ShopStandard);
    const std::vector<OpenYAMM::Game::InventoryItem> &specialStock = OpenYAMM::Game::HouseServiceRuntime::ensureStock(
        harness.party(),
        gameData.itemTable,
        gameData.standardItemEnchantTable,
        gameData.specialItemEnchantTable,
        *pHouseEntry,
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::HouseStockMode::ShopSpecial);

    for (const OpenYAMM::Game::InventoryItem &item : standardStock)
    {
        if (item.objectDescriptionId == 0)
        {
            continue;
        }

        const OpenYAMM::Game::ItemDefinition *pItemDefinition = gameData.itemTable.get(item.objectDescriptionId);
        REQUIRE(pItemDefinition != nullptr);
        CHECK_LE(firstTreasureLevelForItem(*pItemDefinition), pHouseEntry->standardStockTier);
    }

    for (const OpenYAMM::Game::InventoryItem &item : specialStock)
    {
        if (item.objectDescriptionId == 0)
        {
            continue;
        }

        const OpenYAMM::Game::ItemDefinition *pItemDefinition = gameData.itemTable.get(item.objectDescriptionId);
        REQUIRE(pItemDefinition != nullptr);
        CHECK(itemHasTreasureWeightAtOrAboveTier(*pItemDefinition, pHouseEntry->specialStockTier));
    }
}

TEST_CASE("house service shop stock excludes rare items")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::HouseEntry *pHouseEntry = gameData.houseTable.get(1);
    REQUIRE(pHouseEntry != nullptr);

    const auto validateStock =
        [&](const std::vector<OpenYAMM::Game::InventoryItem> &stock)
    {
        for (const OpenYAMM::Game::InventoryItem &item : stock)
        {
            if (item.objectDescriptionId == 0)
            {
                continue;
            }

            const OpenYAMM::Game::ItemDefinition *pItemDefinition = gameData.itemTable.get(item.objectDescriptionId);
            REQUIRE(pItemDefinition != nullptr);
            CHECK(pItemDefinition->rarity == OpenYAMM::Game::ItemRarity::Common);
        }
    };

    const std::vector<OpenYAMM::Game::InventoryItem> &standardStock = OpenYAMM::Game::HouseServiceRuntime::ensureStock(
        harness.party(),
        gameData.itemTable,
        gameData.standardItemEnchantTable,
        gameData.specialItemEnchantTable,
        *pHouseEntry,
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::HouseStockMode::ShopStandard);
    const std::vector<OpenYAMM::Game::InventoryItem> &specialStock = OpenYAMM::Game::HouseServiceRuntime::ensureStock(
        harness.party(),
        gameData.itemTable,
        gameData.standardItemEnchantTable,
        gameData.specialItemEnchantTable,
        *pHouseEntry,
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::HouseStockMode::ShopSpecial);

    validateStock(standardStock);
    validateStock(specialStock);
}

TEST_CASE("house service guild spellbook stock generates and buys")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::HouseEntry *pHouseEntry = gameData.houseTable.get(139);
    REQUIRE(pHouseEntry != nullptr);

    harness.party().addGold(50000);
    const std::vector<OpenYAMM::Game::InventoryItem> &stock = OpenYAMM::Game::HouseServiceRuntime::ensureStock(
        harness.party(),
        gameData.itemTable,
        gameData.standardItemEnchantTable,
        gameData.specialItemEnchantTable,
        *pHouseEntry,
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::HouseStockMode::GuildSpellbooks);
    const auto stockIt =
        std::find_if(stock.begin(), stock.end(), [](const OpenYAMM::Game::InventoryItem &item)
    {
        return item.objectDescriptionId != 0;
    });

    REQUIRE(stockIt != stock.end());
    const OpenYAMM::Game::ItemDefinition *pSpellbook = gameData.itemTable.get(stockIt->objectDescriptionId);
    REQUIRE(pSpellbook != nullptr);
    CHECK_EQ(pSpellbook->equipStat, "Book");

    const size_t slotIndex = static_cast<size_t>(std::distance(stock.begin(), stockIt));
    const size_t initialInventoryCount = harness.party().inventoryItemCount();
    std::string statusText;

    REQUIRE(OpenYAMM::Game::HouseServiceRuntime::tryBuyStockItem(
        harness.party(),
        gameData.itemTable,
        gameData.standardItemEnchantTable,
        gameData.specialItemEnchantTable,
        *pHouseEntry,
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::HouseStockMode::GuildSpellbooks,
        slotIndex,
        statusText));
    CHECK_GT(harness.party().inventoryItemCount(), initialInventoryCount);
}

TEST_CASE("house service shop sell accepts matching item")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::HouseEntry *pHouseEntry = gameData.houseTable.get(1);
    REQUIRE(pHouseEntry != nullptr);

    std::optional<uint32_t> sellableItemId;

    for (const OpenYAMM::Game::ItemDefinition &itemDefinition : gameData.itemTable.entries())
    {
        if (itemDefinition.itemId == 0)
        {
            continue;
        }

        OpenYAMM::Game::InventoryItem candidate = {};
        candidate.objectDescriptionId = itemDefinition.itemId;
        candidate.quantity = 1;
        candidate.width = itemDefinition.inventoryWidth;
        candidate.height = itemDefinition.inventoryHeight;

        if (OpenYAMM::Game::HouseServiceRuntime::canSellItemToHouse(gameData.itemTable, *pHouseEntry, candidate))
        {
            sellableItemId = itemDefinition.itemId;
            break;
        }
    }

    REQUIRE(sellableItemId.has_value());
    REQUIRE(harness.party().grantItemToMember(harness.party().activeMemberIndex(), *sellableItemId, 1));

    const OpenYAMM::Game::Character *pMember = harness.party().activeMember();
    REQUIRE(pMember != nullptr);

    std::optional<std::pair<uint8_t, uint8_t>> matchingCell;

    for (const OpenYAMM::Game::InventoryItem &item : pMember->inventory)
    {
        if (item.objectDescriptionId == *sellableItemId)
        {
            matchingCell = std::pair<uint8_t, uint8_t>(item.gridX, item.gridY);
            break;
        }
    }

    REQUIRE(matchingCell.has_value());
    const int initialGold = harness.party().gold();
    const size_t initialInventoryCount = harness.party().inventoryItemCount();
    std::string statusText;

    REQUIRE(OpenYAMM::Game::HouseServiceRuntime::trySellInventoryItem(
        harness.party(),
        gameData.itemTable,
        gameData.standardItemEnchantTable,
        gameData.specialItemEnchantTable,
        *pHouseEntry,
        harness.party().activeMemberIndex(),
        matchingCell->first,
        matchingCell->second,
        statusText));
    CHECK_GT(harness.party().gold(), initialGold);
    CHECK_LT(harness.party().inventoryItemCount(), initialInventoryCount);
}

TEST_CASE("dwi temple service participant identity")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const OpenYAMM::Game::EventDialogContent &dialog = harness.openHouseDialog(TempleHouseId);

    CHECK_EQ(dialog.houseTitle, "Mystic Medicine");
    CHECK_EQ(dialog.title, "Pish, Healer");
    CHECK_EQ(dialog.participantPictureId, 2108u);
}

TEST_CASE("dwi temple skill learning")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    REQUIRE(harness.party().setActiveMemberIndex(1));
    harness.party().addGold(2000);
    const int initialGold = harness.party().gold();

    const OpenYAMM::Game::EventDialogContent &rootDialog = harness.openHouseDialog(TempleHouseId);
    const std::optional<size_t> learnSkillsIndex = findActionIndexByLabel(rootDialog, "Learn Skills");

    REQUIRE(learnSkillsIndex.has_value());
    const OpenYAMM::Game::EventDialogContent &skillDialog = harness.executeAndPresent(*learnSkillsIndex);
    const std::optional<size_t> merchantIndex = findActionIndexByLabelPrefix(skillDialog, "Learn Merchant ");

    REQUIRE(merchantIndex.has_value());
    harness.executeAndPresent(*merchantIndex);

    const OpenYAMM::Game::Character *pCleric = harness.party().member(1);
    REQUIRE(pCleric != nullptr);
    CHECK(pCleric->hasSkill("Merchant"));
    CHECK_LT(harness.party().gold(), initialGold);
}

TEST_CASE("dwi guild skill learning")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    REQUIRE(harness.party().setActiveMemberIndex(3));
    harness.party().addGold(2000);

    const OpenYAMM::Game::EventDialogContent &rootDialog = harness.openHouseDialog(ElementalGuildHouseId);

    CHECK(dialogHasActionLabel(rootDialog, "Buy Spellbooks"));
    CHECK(dialogHasActionLabel(rootDialog, "Learn Skills"));

    const std::optional<size_t> learnSkillsIndex = findActionIndexByLabel(rootDialog, "Learn Skills");
    REQUIRE(learnSkillsIndex.has_value());

    const OpenYAMM::Game::EventDialogContent &skillDialog = harness.executeAndPresent(*learnSkillsIndex);
    const std::optional<size_t> airMagicIndex = findActionIndexByLabelPrefix(skillDialog, "Learn Air Magic ");

    REQUIRE(airMagicIndex.has_value());
    harness.executeAndPresent(*airMagicIndex);

    const OpenYAMM::Game::Character *pSorcerer = harness.party().member(3);
    REQUIRE(pSorcerer != nullptr);
    CHECK(pSorcerer->hasSkill("AirMagic"));
}

TEST_CASE("dwi training service uses active member")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    OpenYAMM::Game::Character *pActiveMember = harness.party().activeMember();
    REQUIRE(pActiveMember != nullptr);
    pActiveMember->experience = 50000;

    const OpenYAMM::Game::EventDialogContent &initialDialog = harness.openHouseDialog(TrainingHallHouseId);
    CHECK(findActionIndexByLabelPrefix(initialDialog, "Train to level ").has_value());

    REQUIRE(harness.party().setActiveMemberIndex(1));
    OpenYAMM::Game::Character *pCleric = harness.party().activeMember();
    REQUIRE(pCleric != nullptr);
    pCleric->experience = 50000;

    const OpenYAMM::Game::EventDialogContent &refreshedDialog = harness.refreshCurrentHouseDialog();
    CHECK(findActionIndexByLabelPrefix(refreshedDialog, "Train to level ").has_value());
}

TEST_CASE("dwi training service stays open after success")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    OpenYAMM::Game::Character *pMember = harness.party().activeMember();
    REQUIRE(pMember != nullptr);
    pMember->experience = 50000;
    harness.party().addGold(1000);

    const uint32_t expectedLevel = pMember->level + 1;
    const uint32_t expectedSkillPoints = 5 + expectedLevel / 10;

    const OpenYAMM::Game::EventDialogContent &dialog = harness.openHouseDialog(TrainingHallHouseId);
    const std::optional<size_t> trainIndex = findActionIndexByLabelPrefix(dialog, "Train to level ");

    REQUIRE(trainIndex.has_value());
    CHECK(dialog.actions[*trainIndex].enabled);
    const OpenYAMM::Game::EventDialogContent &resultDialog = harness.executeAndPresent(*trainIndex);

    CHECK(resultDialog.isActive);
    CHECK_EQ(pMember->level, expectedLevel);
    CHECK_GE(pMember->skillPoints, expectedSkillPoints);
}

TEST_CASE("dwi tavern arcomage submenu")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const OpenYAMM::Game::EventDialogContent &rootDialog = harness.openHouseDialog(107);
    const std::optional<size_t> arcomageIndex = findActionIndexByLabel(rootDialog, "Play Arcomage");

    REQUIRE(arcomageIndex.has_value());
    const OpenYAMM::Game::EventDialogContent &submenuDialog = harness.executeAndPresent(*arcomageIndex);

    CHECK(dialogHasActionLabel(submenuDialog, "Rules"));
    CHECK(dialogHasActionLabel(submenuDialog, "Victory Conditions"));
    CHECK(dialogHasActionLabel(submenuDialog, "Play"));

    const std::optional<size_t> rulesIndex = findActionIndexByLabel(submenuDialog, "Rules");
    REQUIRE(rulesIndex.has_value());

    const OpenYAMM::Game::EventDialogContent &rulesDialog = harness.executeAndPresent(*rulesIndex);

    CHECK(dialogHasActionLabel(rulesDialog, "Rules"));
    CHECK(dialogHasActionLabel(rulesDialog, "Victory Conditions"));
    CHECK(dialogHasActionLabel(rulesDialog, "Play"));
}

TEST_CASE("dwi bank deposit withdraw roundtrip")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const OpenYAMM::Game::EventDialogContent &rootDialog = harness.openHouseDialog(BankHouseId);
    const std::optional<size_t> depositIndex = findActionIndexByLabel(rootDialog, "Deposit");

    REQUIRE(depositIndex.has_value());
    const int initialCarriedGold = harness.party().gold();

    harness.executeAndPresent(*depositIndex);
    harness.confirmHouseBankInput(std::to_string(initialCarriedGold));

    CHECK_EQ(harness.party().gold(), 0);
    CHECK_EQ(harness.party().bankGold(), initialCarriedGold);

    const OpenYAMM::Game::EventDialogContent &bankDialog = harness.activeDialog();
    const std::optional<size_t> withdrawIndex = findActionIndexByLabel(bankDialog, "Withdraw");

    REQUIRE(withdrawIndex.has_value());
    const int bankGold = harness.party().bankGold();

    harness.executeAndPresent(*withdrawIndex);
    harness.confirmHouseBankInput(std::to_string(bankGold));

    CHECK_EQ(harness.party().bankGold(), 0);
    CHECK_EQ(harness.party().gold(), initialCarriedGold);
}

TEST_CASE("transport routes filter by weekday and qbit")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    const OpenYAMM::Game::HouseEntry *pSmugglerHouse = gameData.houseTable.get(65);
    const OpenYAMM::Game::HouseEntry *pQBitHouse = gameData.houseTable.get(69);

    REQUIRE(pSmugglerHouse != nullptr);
    REQUIRE(pQBitHouse != nullptr);

    const std::vector<OpenYAMM::Game::HouseActionOption> mondayActions = OpenYAMM::Game::buildHouseActionOptions(
        *pSmugglerHouse,
        nullptr,
        nullptr,
        nullptr,
        0.0f,
        OpenYAMM::Game::DialogueMenuId::None);
    const std::vector<OpenYAMM::Game::HouseActionOption> tuesdayActions = OpenYAMM::Game::buildHouseActionOptions(
        *pSmugglerHouse,
        nullptr,
        nullptr,
        nullptr,
        24.0f * 60.0f,
        OpenYAMM::Game::DialogueMenuId::None);

    CHECK(houseActionsContainDestination(mondayActions, "Ravage Roaming"));
    CHECK_FALSE(houseActionsContainDestination(mondayActions, "Shadowspire"));
    CHECK(houseActionsContainDestination(tuesdayActions, "Shadowspire"));
    CHECK_FALSE(houseActionsContainDestination(tuesdayActions, "Ravage Roaming"));

    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const std::vector<OpenYAMM::Game::HouseActionOption> lockedActions = OpenYAMM::Game::buildHouseActionOptions(
        *pQBitHouse,
        &harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime(),
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::DialogueMenuId::None);

    REQUIRE_EQ(lockedActions.size(), 1u);
    CHECK_EQ(lockedActions.front().label, "Sorry, come back another day");
    CHECK_FALSE(lockedActions.front().enabled);

    harness.party().setQuestBit(900, true);

    const std::vector<OpenYAMM::Game::HouseActionOption> unlockedActions = OpenYAMM::Game::buildHouseActionOptions(
        *pQBitHouse,
        &harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime(),
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::DialogueMenuId::None);

    REQUIRE_EQ(unlockedActions.size(), 1u);
    CHECK(houseActionsContainDestination(unlockedActions, "Ravenshore"));
}

TEST_CASE("mastery teacher not enough gold")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    REQUIRE(harness.party().setActiveMemberIndex(3));
    OpenYAMM::Game::Character *pCharacter = harness.party().activeMember();
    REQUIRE(pCharacter != nullptr);
    REQUIRE(setCharacterSkill(
        *pCharacter,
        "IdentifyItem",
        7,
        OpenYAMM::Game::SkillMastery::Expert) != nullptr);

    harness.party().addGold(-harness.party().gold());

    const OpenYAMM::Game::EventDialogContent &dialog =
        harness.openMasteryTeacherOffer(MasterIdentifyItemTeacherNpcId, "Master Identify Item");

    REQUIRE_FALSE(dialog.actions.empty());
    CHECK_EQ(dialog.actions.front().label, "You don't have enough gold!");
}

TEST_CASE("mastery teacher missing skill")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    REQUIRE(harness.party().setActiveMemberIndex(3));
    OpenYAMM::Game::Character *pCharacter = harness.party().activeMember();
    REQUIRE(pCharacter != nullptr);
    pCharacter->skills.erase("IdentifyItem");

    const OpenYAMM::Game::EventDialogContent &dialog =
        harness.openMasteryTeacherOffer(MasterIdentifyItemTeacherNpcId, "Master Identify Item");

    REQUIRE_FALSE(dialog.actions.empty());
    CHECK_EQ(
        dialog.actions.front().label,
        "You must know the skill before you can become an expert in it!");
}

TEST_CASE("mastery teacher insufficient skill level")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    REQUIRE(harness.party().setActiveMemberIndex(3));
    OpenYAMM::Game::Character *pCharacter = harness.party().activeMember();
    REQUIRE(pCharacter != nullptr);
    REQUIRE(setCharacterSkill(
        *pCharacter,
        "IdentifyItem",
        6,
        OpenYAMM::Game::SkillMastery::Expert) != nullptr);

    harness.party().addGold(5000);

    const OpenYAMM::Game::EventDialogContent &dialog =
        harness.openMasteryTeacherOffer(MasterIdentifyItemTeacherNpcId, "Master Identify Item");

    REQUIRE_FALSE(dialog.actions.empty());
    CHECK_EQ(
        dialog.actions.front().label,
        "You don't meet the requirements, and cannot be taught until you do.");
}

TEST_CASE("mastery teacher wrong class")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    REQUIRE(harness.party().setActiveMemberIndex(0));
    OpenYAMM::Game::Character *pCharacter = harness.party().activeMember();
    REQUIRE(pCharacter != nullptr);
    REQUIRE(setCharacterSkill(
        *pCharacter,
        "IdentifyItem",
        7,
        OpenYAMM::Game::SkillMastery::Expert) != nullptr);

    harness.party().addGold(5000);

    const OpenYAMM::Game::EventDialogContent &dialog =
        harness.openMasteryTeacherOffer(MasterIdentifyItemTeacherNpcId, "Master Identify Item");

    REQUIRE_FALSE(dialog.actions.empty());
    CHECK_EQ(dialog.actions.front().label, "This skill level can not be learned by the Knight class.");
}

TEST_CASE("mastery teacher character switch changes logic")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    REQUIRE(harness.party().setActiveMemberIndex(0));
    OpenYAMM::Game::Character *pKnight = harness.party().activeMember();
    REQUIRE(pKnight != nullptr);
    REQUIRE(setCharacterSkill(
        *pKnight,
        "IdentifyItem",
        7,
        OpenYAMM::Game::SkillMastery::Expert) != nullptr);

    harness.party().addGold(5000);

    const OpenYAMM::Game::EventDialogContent &knightDialog =
        harness.openMasteryTeacherOffer(MasterIdentifyItemTeacherNpcId, "Master Identify Item");

    REQUIRE_FALSE(knightDialog.actions.empty());
    CHECK_EQ(knightDialog.actions.front().label, "This skill level can not be learned by the Knight class.");

    REQUIRE(harness.party().setActiveMemberIndex(3));
    OpenYAMM::Game::Character *pSorcerer = harness.party().activeMember();
    REQUIRE(pSorcerer != nullptr);
    REQUIRE(setCharacterSkill(
        *pSorcerer,
        "IdentifyItem",
        7,
        OpenYAMM::Game::SkillMastery::Expert) != nullptr);

    const OpenYAMM::Game::EventDialogContent &sorcererDialog = harness.refreshCurrentNpcDialog();

    REQUIRE_FALSE(sorcererDialog.actions.empty());
    CHECK_EQ(sorcererDialog.actions.front().label, "Become Master in Identify Item for 2500 gold");
}

TEST_CASE("mastery teacher offer and learn")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    REQUIRE(harness.party().setActiveMemberIndex(3));
    OpenYAMM::Game::Character *pCharacter = harness.party().activeMember();
    REQUIRE(pCharacter != nullptr);
    REQUIRE(setCharacterSkill(
        *pCharacter,
        "IdentifyItem",
        7,
        OpenYAMM::Game::SkillMastery::Expert) != nullptr);

    const int initialGold = harness.party().gold();
    harness.party().addGold(5000);

    const OpenYAMM::Game::EventDialogContent &offerDialog =
        harness.openMasteryTeacherOffer(MasterIdentifyItemTeacherNpcId, "Master Identify Item");

    REQUIRE_FALSE(offerDialog.actions.empty());
    CHECK_EQ(offerDialog.actions.front().label, "Become Master in Identify Item for 2500 gold");

    const OpenYAMM::Game::EventDialogContent &resultDialog = harness.executeAndPresent(0);

    const OpenYAMM::Game::Character *pUpdatedCharacter = harness.party().activeMember();
    REQUIRE(pUpdatedCharacter != nullptr);
    const OpenYAMM::Game::CharacterSkill *pUpdatedSkill = pUpdatedCharacter->findSkill("IdentifyItem");
    REQUIRE(pUpdatedSkill != nullptr);

    CHECK_EQ(pUpdatedSkill->mastery, OpenYAMM::Game::SkillMastery::Master);
    CHECK_EQ(harness.party().gold(), initialGold + 5000 - 2500);

    REQUIRE_FALSE(resultDialog.actions.empty());
    CHECK_EQ(resultDialog.actions.front().label, "You are already a master in this skill.");
    CHECK(dialogContainsText(resultDialog, "With Mastery of the Identify Items skill"));
}

TEST_CASE("actual roster join rohani")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const OpenYAMM::Game::EventDialogContent &dialog = harness.openNpcDialogue(RohaniNpcId);
    const std::optional<size_t> joinIndex = findActionIndexByLabel(dialog, "Join");

    REQUIRE(joinIndex.has_value());
    const OpenYAMM::Game::EventDialogContent &offerDialog = harness.executeAndPresent(*joinIndex);
    CHECK(dialogContainsText(offerDialog, "Will you have Rohani Oscleton the Dark Elf join you?"));

    const std::optional<size_t> yesIndex = findActionIndexByLabel(offerDialog, "Yes");
    REQUIRE(yesIndex.has_value());
    const OpenYAMM::Game::EventDialogContent &resultDialog = harness.executeAndPresent(*yesIndex);

    CHECK(harness.party().hasRosterMember(6));
    CHECK(harness.eventRuntimeState().unavailableNpcIds.contains(RohaniNpcId));
    CHECK(dialogContainsText(resultDialog, "joined the party"));
}

TEST_CASE("actual roster join rohani full party")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::RosterEntry *pExtraMember = gameData.rosterTable.get(3);

    REQUIRE(pExtraMember != nullptr);
    REQUIRE(harness.party().recruitRosterMember(*pExtraMember));

    const OpenYAMM::Game::EventDialogContent &dialog = harness.openNpcDialogue(RohaniNpcId);
    const std::optional<size_t> joinIndex = findActionIndexByLabel(dialog, "Join");

    REQUIRE(joinIndex.has_value());
    const OpenYAMM::Game::EventDialogContent &offerDialog = harness.executeAndPresent(*joinIndex);
    const std::optional<size_t> yesIndex = findActionIndexByLabel(offerDialog, "Yes");

    REQUIRE(yesIndex.has_value());
    const OpenYAMM::Game::EventDialogContent &resultDialog = harness.executeAndPresent(*yesIndex);
    const auto movedHouseIt = harness.eventRuntimeState().npcHouseOverrides.find(RohaniNpcId);

    CHECK(dialogContainsText(resultDialog, "I'm glad you've decided to take me"));
    CHECK_FALSE(harness.eventRuntimeState().unavailableNpcIds.contains(RohaniNpcId));
    REQUIRE(movedHouseIt != harness.eventRuntimeState().npcHouseOverrides.end());
    CHECK_EQ(movedHouseIt->second, AdventurersInnHouseId);
}

TEST_CASE("actual roster join dyson direct")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    const OpenYAMM::Game::EventDialogContent &dialog = harness.openNpcDialogue(DysonDirectNpcId);
    const std::optional<size_t> joinIndex = findActionIndexByLabel(dialog, "Join");

    REQUIRE(joinIndex.has_value());
    const OpenYAMM::Game::EventDialogContent &offerDialog = harness.executeAndPresent(*joinIndex);
    CHECK(dialogContainsText(offerDialog, "I will gladly join you."));

    const std::optional<size_t> yesIndex = findActionIndexByLabel(offerDialog, "Yes");
    REQUIRE(yesIndex.has_value());
    harness.executeAndPresent(*yesIndex);

    CHECK(harness.party().hasRosterMember(34));
}

TEST_CASE("roster join mapping and players can show topic")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    OpenYAMM::Game::EventDialogContent dialog = harness.openNpcDialogue(SandroNpcId);
    CHECK(dialogHasActionLabel(dialog, "Dyson Leland"));

    harness.eventRuntimeState().npcTopicOverrides[DysonNpcId][3] = 634;
    dialog = harness.openNpcDialogue(DysonNpcId);

    const std::optional<size_t> joinIndex = findActionIndexByLabel(dialog, "Join");
    REQUIRE(joinIndex.has_value());
    const OpenYAMM::Game::EventDialogContent &offerDialog = harness.executeAndPresent(*joinIndex);

    CHECK(dialogContainsText(offerDialog, "I will gladly join you."));

    const std::optional<size_t> yesIndex = findActionIndexByLabel(offerDialog, "Yes");
    REQUIRE(yesIndex.has_value());
    harness.executeAndPresent(*yesIndex);

    CHECK(harness.party().hasRosterMember(34));

    dialog = harness.openNpcDialogue(SandroNpcId);
    CHECK_FALSE(dialogHasActionLabel(dialog, "Dyson Leland"));
}

TEST_CASE("synthetic roster join accept")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const std::optional<std::string> inviteText = gameData.npcDialogTable.getText(202);

    if (inviteText.has_value())
    {
        harness.eventRuntimeState().messages.push_back(*inviteText);
    }

    harness.eventRuntimeState().dialogueState.currentOffer = makeRosterJoinOffer(FredrickNpcId, 2, 202, 203);

    OpenYAMM::Game::EventRuntimeState::PendingDialogueContext context = {};
    context.kind = OpenYAMM::Game::DialogueContextKind::NpcTalk;
    context.sourceId = FredrickNpcId;
    harness.eventRuntimeState().pendingDialogueContext = context;

    const OpenYAMM::Game::EventDialogContent &dialog = harness.presentPendingDialog(0, true);
    const std::optional<size_t> yesIndex = findActionIndexByLabel(dialog, "Yes");

    REQUIRE(yesIndex.has_value());
    const OpenYAMM::Game::EventDialogContent &resultDialog = harness.executeAndPresent(*yesIndex);

    CHECK_EQ(harness.party().members().size(), 5u);
    CHECK(harness.eventRuntimeState().unavailableNpcIds.contains(FredrickNpcId));
    CHECK(dialogContainsText(resultDialog, "joined the party"));
}

TEST_CASE("synthetic roster join full party")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::RosterEntry *pExtraMember = gameData.rosterTable.get(3);
    const std::optional<std::string> inviteText = gameData.npcDialogTable.getText(202);

    REQUIRE(pExtraMember != nullptr);
    REQUIRE(harness.party().recruitRosterMember(*pExtraMember));

    if (inviteText.has_value())
    {
        harness.eventRuntimeState().messages.push_back(*inviteText);
    }

    harness.eventRuntimeState().dialogueState.currentOffer = makeRosterJoinOffer(FredrickNpcId, 2, 202, 203);

    OpenYAMM::Game::EventRuntimeState::PendingDialogueContext context = {};
    context.kind = OpenYAMM::Game::DialogueContextKind::NpcTalk;
    context.sourceId = FredrickNpcId;
    harness.eventRuntimeState().pendingDialogueContext = context;

    const OpenYAMM::Game::EventDialogContent &dialog = harness.presentPendingDialog(0, true);
    const std::optional<size_t> yesIndex = findActionIndexByLabel(dialog, "Yes");

    REQUIRE(yesIndex.has_value());
    const OpenYAMM::Game::EventDialogContent &resultDialog = harness.executeAndPresent(*yesIndex);
    const auto movedHouseIt = harness.eventRuntimeState().npcHouseOverrides.find(FredrickNpcId);

    CHECK_EQ(harness.party().members().size(), 5u);
    CHECK_FALSE(harness.eventRuntimeState().unavailableNpcIds.contains(FredrickNpcId));
    REQUIRE(movedHouseIt != harness.eventRuntimeState().npcHouseOverrides.end());
    CHECK_EQ(movedHouseIt->second, AdventurersInnHouseId);
    CHECK(dialogContainsText(resultDialog, "party's all full up"));

    OpenYAMM::Game::EventRuntimeState::PendingDialogueContext innContext = {};
    innContext.kind = OpenYAMM::Game::DialogueContextKind::HouseService;
    innContext.sourceId = AdventurersInnHouseId;
    innContext.hostHouseId = AdventurersInnHouseId;
    harness.eventRuntimeState().pendingDialogueContext = innContext;

    const OpenYAMM::Game::EventDialogContent innDialog = harness.buildPendingDialogContent(0, true);
    const bool showsFredrickTitle = innDialog.title == "Fredrick Talimere";
    const bool showsFredrickAction = dialogHasActionLabel(innDialog, "Fredrick Talimere");
    const bool showsFredrick = showsFredrickTitle || showsFredrickAction;

    CHECK(showsFredrick);
    CHECK_FALSE(dialogHasActionLabel(innDialog, "Rent room for 5 gold"));
    CHECK_FALSE(dialogHasActionLabel(innDialog, "Fill packs to 14 days for 2 gold"));
    CHECK_FALSE(dialogHasActionLabel(innDialog, "Play Arcomage"));
}

TEST_CASE("adventurers inn hire moves character into party")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::RosterEntry *pRosterEntry = gameData.rosterTable.get(3);
    const OpenYAMM::Game::NpcEntry *pNpcEntry =
        pRosterEntry != nullptr ? gameData.npcDialogTable.findNpcByName(pRosterEntry->name) : nullptr;

    REQUIRE(pRosterEntry != nullptr);
    REQUIRE(harness.party().addAdventurersInnMember(*pRosterEntry, pNpcEntry != nullptr ? pNpcEntry->pictureId : 0));

    const size_t initialPartyCount = harness.party().members().size();

    REQUIRE(harness.party().hireAdventurersInnMember(0));
    CHECK_EQ(harness.party().members().size(), initialPartyCount + 1);
    CHECK(harness.party().hasRosterMember(3));
    CHECK(harness.party().adventurersInnMembers().empty());
}

TEST_CASE("adventurers inn hire preserves roster spell knowledge")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::RosterEntry *pRosterEntry = gameData.rosterTable.get(1);

    REQUIRE(pRosterEntry != nullptr);
    REQUIRE(harness.party().addAdventurersInnMember(*pRosterEntry, 0));
    REQUIRE(harness.party().hireAdventurersInnMember(0));

    const OpenYAMM::Game::Character *pHiredMember = findPartyMemberByRosterId(harness.party(), 1);
    REQUIRE(pHiredMember != nullptr);

    CHECK(pHiredMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::TorchLight)));
    CHECK(pHiredMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::FireBolt)));
    CHECK(pHiredMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::WizardEye)));
    CHECK(pHiredMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::FeatherFall)));
    CHECK(pHiredMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::Reanimate)));
    CHECK(pHiredMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::ToxicCloud)));
    CHECK(pHiredMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::VampiricWeapon)));

    CHECK_FALSE(pHiredMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::Inferno)));
    CHECK_FALSE(pHiredMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::Fly)));
    CHECK_FALSE(pHiredMember->knowsSpell(OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::PainReflection)));
}

TEST_CASE("party dismiss moves member to adventurers inn tail")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    REQUIRE_GE(harness.party().members().size(), 3u);

    const size_t dismissedMemberIndex = 1;
    const std::string dismissedName = harness.party().members()[dismissedMemberIndex].name;
    const size_t initialPartyCount = harness.party().members().size();
    const size_t initialInnCount = harness.party().adventurersInnMembers().size();

    CHECK_FALSE(harness.party().dismissMemberToAdventurersInn(0));
    REQUIRE(harness.party().dismissMemberToAdventurersInn(dismissedMemberIndex));

    CHECK_EQ(harness.party().members().size(), initialPartyCount - 1);
    CHECK_EQ(harness.party().adventurersInnMembers().size(), initialInnCount + 1);

    const OpenYAMM::Game::AdventurersInnMember *pDismissedMember =
        harness.party().adventurersInnMember(harness.party().adventurersInnMembers().size() - 1);

    REQUIRE(pDismissedMember != nullptr);
    CHECK_EQ(pDismissedMember->character.name, dismissedName);
    CHECK_EQ(harness.party().lastStatus(), "party member dismissed");
}

TEST_CASE("adventurers inn roster members use roster portraits and identified items")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::RosterEntry *pRosterEntry = gameData.rosterTable.get(1);

    REQUIRE(pRosterEntry != nullptr);
    REQUIRE(harness.party().addAdventurersInnMember(*pRosterEntry, 1));

    const OpenYAMM::Game::AdventurersInnMember *pInnMember = harness.party().adventurersInnMember(0);

    REQUIRE(pInnMember != nullptr);
    CHECK_EQ(pInnMember->portraitPictureId, 2909u);

    for (const OpenYAMM::Game::InventoryItem &item : pInnMember->character.inventory)
    {
        CHECK(item.identified);
    }

    CHECK(innEquipmentItemIdentified(
        pInnMember->character.equipmentRuntime.mainHand,
        pInnMember->character.equipment.mainHand));
    CHECK(innEquipmentItemIdentified(
        pInnMember->character.equipmentRuntime.offHand,
        pInnMember->character.equipment.offHand));
    CHECK(innEquipmentItemIdentified(
        pInnMember->character.equipmentRuntime.bow,
        pInnMember->character.equipment.bow));
    CHECK(innEquipmentItemIdentified(
        pInnMember->character.equipmentRuntime.armor,
        pInnMember->character.equipment.armor));
    CHECK(innEquipmentItemIdentified(
        pInnMember->character.equipmentRuntime.helm,
        pInnMember->character.equipment.helm));
    CHECK(innEquipmentItemIdentified(
        pInnMember->character.equipmentRuntime.belt,
        pInnMember->character.equipment.belt));
    CHECK(innEquipmentItemIdentified(
        pInnMember->character.equipmentRuntime.cloak,
        pInnMember->character.equipment.cloak));
    CHECK(innEquipmentItemIdentified(
        pInnMember->character.equipmentRuntime.gauntlets,
        pInnMember->character.equipment.gauntlets));
    CHECK(innEquipmentItemIdentified(
        pInnMember->character.equipmentRuntime.boots,
        pInnMember->character.equipment.boots));
    CHECK(innEquipmentItemIdentified(
        pInnMember->character.equipmentRuntime.amulet,
        pInnMember->character.equipment.amulet));
    CHECK(innEquipmentItemIdentified(
        pInnMember->character.equipmentRuntime.ring1,
        pInnMember->character.equipment.ring1));
    CHECK(innEquipmentItemIdentified(
        pInnMember->character.equipmentRuntime.ring2,
        pInnMember->character.equipment.ring2));
    CHECK(innEquipmentItemIdentified(
        pInnMember->character.equipmentRuntime.ring3,
        pInnMember->character.equipment.ring3));
    CHECK(innEquipmentItemIdentified(
        pInnMember->character.equipmentRuntime.ring4,
        pInnMember->character.equipment.ring4));
    CHECK(innEquipmentItemIdentified(
        pInnMember->character.equipmentRuntime.ring5,
        pInnMember->character.equipment.ring5));
    CHECK(innEquipmentItemIdentified(
        pInnMember->character.equipmentRuntime.ring6,
        pInnMember->character.equipment.ring6));
}

TEST_CASE("transport action spends gold advances time and queues map move")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::HouseEntry *pHouseEntry = gameData.houseTable.get(63);

    REQUIRE(pHouseEntry != nullptr);

    harness.party().addGold(1000);
    const float initialGameMinutes = harness.worldRuntime().gameMinutes();
    const int initialGold = harness.party().gold();
    const OpenYAMM::Game::Character *pMember = harness.party().activeMember();
    REQUIRE(pMember != nullptr);
    const int expectedPrice = OpenYAMM::Game::PriceCalculator::transportPrice(pMember, *pHouseEntry, true);
    OpenYAMM::Game::Character *pActiveMember = harness.party().activeMember();
    REQUIRE(pActiveMember != nullptr);

    harness.party().applyPartyBuff(
        OpenYAMM::Game::PartyBuffId::TorchLight,
        600.0f,
        1,
        0,
        0,
        OpenYAMM::Game::SkillMastery::None,
        0);
    pActiveMember->health = std::max(1, pActiveMember->health - 20);
    pActiveMember->spellPoints = std::max(0, pActiveMember->spellPoints - 5);
    pActiveMember->recoverySecondsRemaining = 3.0f;
    pActiveMember->conditions.set(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Weak));
    pActiveMember->conditions.set(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Fear));

    const std::vector<OpenYAMM::Game::HouseActionOption> actions = OpenYAMM::Game::buildHouseActionOptions(
        *pHouseEntry,
        &harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime(),
        0.0f,
        OpenYAMM::Game::DialogueMenuId::None);
    const std::optional<OpenYAMM::Game::HouseActionOption> action =
        findHouseActionById(actions, OpenYAMM::Game::HouseActionId::TransportRoute);

    REQUIRE(action.has_value());
    const OpenYAMM::Game::HouseActionResult result = OpenYAMM::Game::performHouseAction(
        *action,
        *pHouseEntry,
        harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime());

    CHECK(result.succeeded);
    REQUIRE(result.soundType.has_value());
    CHECK_EQ(*result.soundType, OpenYAMM::Game::HouseSoundType::TransportTravel);
    CHECK_EQ(harness.party().gold(), initialGold - expectedPrice);
    CHECK_EQ(harness.worldRuntime().gameMinutes(), doctest::Approx(initialGameMinutes + 24.0f * 60.0f));

    pActiveMember = harness.party().activeMember();
    REQUIRE(pActiveMember != nullptr);
    CHECK_EQ(pActiveMember->health, pActiveMember->maxHealth);
    CHECK_EQ(pActiveMember->spellPoints, pActiveMember->maxSpellPoints);
    CHECK_FALSE(pActiveMember->conditions.test(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Weak)));
    CHECK_FALSE(pActiveMember->conditions.test(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Fear)));
    CHECK_EQ(pActiveMember->recoverySecondsRemaining, doctest::Approx(0.0f));
    CHECK_FALSE(harness.party().hasPartyBuff(OpenYAMM::Game::PartyBuffId::TorchLight));

    const OpenYAMM::Game::EventRuntimeState *pWorldRuntimeState = harness.worldRuntime().eventRuntimeState();

    REQUIRE(pWorldRuntimeState != nullptr);
    const std::optional<OpenYAMM::Game::EventRuntimeState::PendingMapMove> &pendingMapMove =
        pWorldRuntimeState->pendingMapMove;

    REQUIRE(pendingMapMove.has_value());
    REQUIRE(pendingMapMove->mapName.has_value());
    CHECK_EQ(*pendingMapMove->mapName, "Out02.odm");
    REQUIRE(pendingMapMove->directionDegrees.has_value());
    CHECK_EQ(*pendingMapMove->directionDegrees, 180);
    CHECK(pendingMapMove->useMapStartPosition);
}

TEST_CASE("transport route schedule is driven by transport_schedules table")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::HouseEntry *pHouseEntry = gameData.houseTable.get(67);

    REQUIRE(pHouseEntry != nullptr);

    std::vector<OpenYAMM::Game::HouseActionOption> actions = OpenYAMM::Game::buildHouseActionOptions(
        *pHouseEntry,
        &harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime(),
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::DialogueMenuId::None);

    CHECK(houseActionsContainDestination(actions, "Ravenshore"));
    CHECK_FALSE(houseActionsContainDestination(actions, "Regna"));

    harness.worldRuntime().advanceGameMinutes(5.0f * 24.0f * 60.0f);
    actions = OpenYAMM::Game::buildHouseActionOptions(
        *pHouseEntry,
        &harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime(),
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::DialogueMenuId::None);

    CHECK_FALSE(houseActionsContainDestination(actions, "Ravenshore"));
    CHECK(houseActionsContainDestination(actions, "Regna"));
}

TEST_CASE("transport route quest bit gates show unavailable fallback until unlocked")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::HouseEntry *pHouseEntry = gameData.houseTable.get(69);

    REQUIRE(pHouseEntry != nullptr);

    std::vector<OpenYAMM::Game::HouseActionOption> actions = OpenYAMM::Game::buildHouseActionOptions(
        *pHouseEntry,
        &harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime(),
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::DialogueMenuId::None);

    REQUIRE_EQ(actions.size(), 1);
    CHECK_EQ(actions.front().label, "Sorry, come back another day");
    CHECK_FALSE(actions.front().enabled);

    harness.party().setQuestBit(900, true);
    actions = OpenYAMM::Game::buildHouseActionOptions(
        *pHouseEntry,
        &harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime(),
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::DialogueMenuId::None);

    REQUIRE_EQ(actions.size(), 1);
    CHECK(actions.front().enabled);
    CHECK(houseActionsContainDestination(actions, "Ravenshore"));
}

TEST_CASE("transport route travel time is clamped to at least one day")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    OpenYAMM::Game::HouseEntry houseEntry = {};
    houseEntry.id = 99999;
    houseEntry.type = "Boats";
    houseEntry.priceMultiplier = 1.0f;

    OpenYAMM::Game::HouseEntry::TransportRoute route = {};
    route.routeIndex = 1;
    route.destinationName = "Test Harbor";
    route.mapFileName = "Out02.odm";
    route.travelDays = 0;
    route.useMapStartPosition = true;
    houseEntry.transportRoutes.push_back(route);

    harness.party().addGold(1000);
    const float initialGameMinutes = harness.worldRuntime().gameMinutes();
    const std::vector<OpenYAMM::Game::HouseActionOption> actions = OpenYAMM::Game::buildHouseActionOptions(
        houseEntry,
        &harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime(),
        harness.worldRuntime().gameMinutes(),
        OpenYAMM::Game::DialogueMenuId::None);

    REQUIRE_EQ(actions.size(), 1);
    CHECK(actions.front().label.find("1 day to Test Harbor") != std::string::npos);

    const OpenYAMM::Game::HouseActionResult result = OpenYAMM::Game::performHouseAction(
        actions.front(),
        houseEntry,
        harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime());

    CHECK(result.succeeded);
    CHECK_EQ(harness.worldRuntime().gameMinutes(), doctest::Approx(initialGameMinutes + 24.0f * 60.0f));
    REQUIRE_FALSE(result.messages.empty());
    CHECK_EQ(result.messages.front(), "It will take 1 day to travel to Test Harbor.");
}

TEST_CASE("tavern rent room defers recovery until rest screen")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::HouseEntry *pTavernHouse = gameData.houseTable.get(107);

    REQUIRE(pTavernHouse != nullptr);

    OpenYAMM::Game::Character *pTavernMember = harness.party().activeMember();
    REQUIRE(pTavernMember != nullptr);

    harness.party().addGold(1000);
    harness.party().applyPartyBuff(
        OpenYAMM::Game::PartyBuffId::WizardEye,
        600.0f,
        1,
        0,
        0,
        OpenYAMM::Game::SkillMastery::None,
        0);
    const int initialHealth = std::max(1, pTavernMember->health - 17);
    const int initialSpellPoints = std::max(0, pTavernMember->spellPoints - 4);
    pTavernMember->health = initialHealth;
    pTavernMember->spellPoints = initialSpellPoints;
    pTavernMember->conditions.set(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Asleep));
    pTavernMember->recoverySecondsRemaining = 2.0f;
    const float initialGameMinutes = harness.worldRuntime().gameMinutes();

    const OpenYAMM::Game::HouseActionResult tavernResult = OpenYAMM::Game::performHouseAction(
        OpenYAMM::Game::HouseActionOption{
            OpenYAMM::Game::HouseActionId::TavernRentRoom,
            "Rent room",
            "",
            true,
            ""},
        *pTavernHouse,
        harness.party(),
        &gameData.classSkillTable,
        &harness.worldRuntime());

    CHECK(tavernResult.succeeded);
    REQUIRE(tavernResult.pendingInnRest.has_value());
    CHECK_EQ(tavernResult.pendingInnRest->houseId, pTavernHouse->id);
    REQUIRE(tavernResult.soundType.has_value());
    CHECK_EQ(*tavernResult.soundType, OpenYAMM::Game::HouseSoundType::TavernRentRoom);
    CHECK_EQ(harness.worldRuntime().gameMinutes(), doctest::Approx(initialGameMinutes));
    CHECK_EQ(pTavernMember->health, initialHealth);
    CHECK_EQ(pTavernMember->spellPoints, initialSpellPoints);
    CHECK_EQ(pTavernMember->recoverySecondsRemaining, doctest::Approx(2.0f));
    CHECK(pTavernMember->conditions.test(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Asleep)));
    CHECK(harness.party().hasPartyBuff(OpenYAMM::Game::PartyBuffId::WizardEye));
}

TEST_CASE("temple donate applies oe reputation gating and buffs")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    const OpenYAMM::Game::HouseEntry *pTempleHouse = gameData.houseTable.get(TempleHouseId);

    REQUIRE(pTempleHouse != nullptr);

    harness.party().addGold(5000);
    harness.worldRuntime().advanceGameMinutes(24.0f * 60.0f);
    harness.worldRuntime().setCurrentLocationReputation(-25);

    OpenYAMM::Game::Character *pWeakMember = harness.party().member(1);
    REQUIRE(pWeakMember != nullptr);

    pWeakMember->conditions.set(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Weak));
    const int donationPrice = std::max(1, static_cast<int>(std::round(pTempleHouse->priceMultiplier)));
    const int initialGold = harness.party().gold();

    for (int donationIndex = 0; donationIndex < 3; ++donationIndex)
    {
        const OpenYAMM::Game::HouseActionResult result = OpenYAMM::Game::performHouseAction(
            OpenYAMM::Game::HouseActionOption{
                OpenYAMM::Game::HouseActionId::TempleDonate,
                "Donate",
                "",
                true,
                ""},
            *pTempleHouse,
            harness.party(),
            &gameData.classSkillTable,
            &harness.worldRuntime());

        CHECK(result.succeeded);
        CHECK(result.messages == std::vector<std::string>{"Thank You"});
    }

    CHECK_EQ(harness.party().gold(), initialGold - donationPrice * 3);
    CHECK_EQ(harness.worldRuntime().currentLocationReputation(), -25);
    CHECK_EQ(
        harness.eventRuntimeState().dialogueState.templeDonationCounters[harness.party().activeMemberIndex()],
        3);

    const OpenYAMM::Game::PartyBuffState *pWizardEye =
        harness.party().partyBuff(OpenYAMM::Game::PartyBuffId::WizardEye);
    const OpenYAMM::Game::PartyBuffState *pFeatherFall =
        harness.party().partyBuff(OpenYAMM::Game::PartyBuffId::FeatherFall);
    const OpenYAMM::Game::PartyBuffState *pProtectionFromMagic =
        harness.party().partyBuff(OpenYAMM::Game::PartyBuffId::ProtectionFromMagic);
    const OpenYAMM::Game::PartyBuffState *pHeroism =
        harness.party().partyBuff(OpenYAMM::Game::PartyBuffId::Heroism);
    const OpenYAMM::Game::PartyBuffState *pShield =
        harness.party().partyBuff(OpenYAMM::Game::PartyBuffId::Shield);
    const OpenYAMM::Game::PartyBuffState *pStoneskin =
        harness.party().partyBuff(OpenYAMM::Game::PartyBuffId::Stoneskin);
    const OpenYAMM::Game::PartyBuffState *pBodyResistance =
        harness.party().partyBuff(OpenYAMM::Game::PartyBuffId::BodyResistance);

    REQUIRE(pFeatherFall != nullptr);
    CHECK(pFeatherFall->active());
    CHECK_EQ(pFeatherFall->remainingSeconds, doctest::Approx(43200.0f));

    REQUIRE(pWizardEye != nullptr);
    CHECK(pWizardEye->active());
    CHECK_EQ(pWizardEye->remainingSeconds, doctest::Approx(43200.0f));
    CHECK_EQ(pWizardEye->power, 0);

    REQUIRE(pProtectionFromMagic != nullptr);
    CHECK(pProtectionFromMagic->active());
    CHECK_EQ(pProtectionFromMagic->remainingSeconds, doctest::Approx(10800.0f));
    CHECK_EQ(pProtectionFromMagic->power, 3);

    REQUIRE(pHeroism != nullptr);
    CHECK(pHeroism->active());
    CHECK_EQ(pHeroism->remainingSeconds, doctest::Approx(14400.0f));
    CHECK_EQ(pHeroism->power, 8);

    REQUIRE(pShield != nullptr);
    CHECK(pShield->active());
    CHECK_EQ(pShield->remainingSeconds, doctest::Approx(14400.0f));

    REQUIRE(pStoneskin != nullptr);
    CHECK(pStoneskin->active());
    CHECK_EQ(pStoneskin->remainingSeconds, doctest::Approx(14400.0f));
    CHECK_EQ(pStoneskin->power, 8);

    REQUIRE(pBodyResistance != nullptr);
    CHECK(pBodyResistance->active());
    CHECK_EQ(pBodyResistance->remainingSeconds, doctest::Approx(43200.0f));
    CHECK_EQ(pBodyResistance->power, 12);

    CHECK_FALSE(harness.party().hasPartyBuff(OpenYAMM::Game::PartyBuffId::Haste));

    for (size_t memberIndex = 0; memberIndex < harness.party().members().size(); ++memberIndex)
    {
        const OpenYAMM::Game::CharacterBuffState *pBless =
            harness.party().characterBuff(memberIndex, OpenYAMM::Game::CharacterBuffId::Bless);
        const OpenYAMM::Game::CharacterBuffState *pPreservation =
            harness.party().characterBuff(memberIndex, OpenYAMM::Game::CharacterBuffId::Preservation);

        REQUIRE(pBless != nullptr);
        CHECK(pBless->active());
        CHECK_EQ(pBless->remainingSeconds, doctest::Approx(14400.0f));
        CHECK_EQ(pBless->power, 8);

        REQUIRE(pPreservation != nullptr);
        CHECK(pPreservation->active());
        CHECK_EQ(pPreservation->remainingSeconds, doctest::Approx(4500.0f));
    }

    REQUIRE_EQ(harness.eventRuntimeState().spellFxRequests.size(), 5u);
    CHECK_EQ(
        harness.eventRuntimeState().spellFxRequests.front().spellId,
        OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::Bless));
}

TEST_CASE("empty house after departure")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    harness.eventRuntimeState().unavailableNpcIds.insert(FredrickNpcId);

    REQUIRE(harness.executeOut01LocalEvent(37));

    const OpenYAMM::Game::EventDialogContent &dialog = harness.presentPendingDialog(0, true);

    CHECK(dialogContainsText(dialog, "The house is empty."));
}

TEST_CASE("event fountain heal and refresh status work")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    OpenYAMM::Game::Character *pMember = harness.party().activeMember();

    REQUIRE(pMember != nullptr);

    pMember->health = std::max(1, pMember->health - 40);
    const int expectedHealedHealth = std::min(pMember->maxHealth, pMember->health + 25);

    REQUIRE(harness.executeOut01LocalEvent(104));
    CHECK_EQ(pMember->health, expectedHealedHealth);
    REQUIRE_FALSE(harness.eventRuntimeState().statusMessages.empty());
    CHECK_EQ(harness.eventRuntimeState().statusMessages.back(), "Your Wounds begin to Heal");

    constexpr uint32_t FountainHealAutoNoteRawId = (248u << 16) | 0x00dfu;

    CHECK(harness.eventRuntimeState().variables.contains(FountainHealAutoNoteRawId));

    harness.eventRuntimeState().statusMessages.clear();
    pMember->health = pMember->maxHealth;

    REQUIRE(harness.executeOut01LocalEvent(104));
    REQUIRE_FALSE(harness.eventRuntimeState().statusMessages.empty());
    CHECK_EQ(harness.eventRuntimeState().statusMessages.back(), "Refreshing");
}

TEST_CASE("event luck fountain grants permanent bonus once")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    OpenYAMM::Game::Character *pMember = harness.party().activeMember();

    REQUIRE(pMember != nullptr);

    pMember->luck = 10;

    REQUIRE(harness.executeOut01LocalEvent(102));
    CHECK_EQ(pMember->luck, 12);
    REQUIRE_FALSE(harness.eventRuntimeState().statusMessages.empty());
    CHECK_EQ(harness.eventRuntimeState().statusMessages.back(), "Luck +2 (Permanent)");

    harness.eventRuntimeState().statusMessages.clear();

    REQUIRE(harness.executeOut01LocalEvent(102));
    REQUIRE(harness.executeOut01LocalEvent(102));
    REQUIRE(harness.executeOut01LocalEvent(102));
    CHECK_EQ(pMember->luck, 16);

    harness.eventRuntimeState().statusMessages.clear();

    REQUIRE(harness.executeOut01LocalEvent(102));
    CHECK_EQ(pMember->luck, 16);
    REQUIRE_FALSE(harness.eventRuntimeState().statusMessages.empty());
    CHECK_EQ(harness.eventRuntimeState().statusMessages.back(), "Refreshing");
}

TEST_CASE("event hidden well uses bank gold gate and mapvar progress")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness blockedHarness(gameData);
    OpenYAMM::Game::Character *pBlockedMember = blockedHarness.party().activeMember();

    REQUIRE(pBlockedMember != nullptr);

    pBlockedMember->luck = 14;
    blockedHarness.party().addGold(150);
    blockedHarness.party().depositGoldToBank(100);
    blockedHarness.party().addGold(-blockedHarness.party().gold());

    REQUIRE(blockedHarness.executeOut01LocalEvent(103));
    REQUIRE_FALSE(blockedHarness.eventRuntimeState().statusMessages.empty());
    CHECK_EQ(blockedHarness.eventRuntimeState().statusMessages.back(), "Refreshing");

    OpenYAMM::Tests::HouseDialogueTestHarness rewardHarness(gameData);
    OpenYAMM::Game::Character *pRewardMember = rewardHarness.party().activeMember();

    REQUIRE(pRewardMember != nullptr);

    pRewardMember->luck = 14;
    rewardHarness.party().addGold(-rewardHarness.party().gold());

    REQUIRE(rewardHarness.executeOut01LocalEvent(103));
    CHECK_EQ(rewardHarness.party().gold(), 1000);
    CHECK_EQ(rewardHarness.eventRuntimeState().mapVars[29], 1);

    constexpr uint32_t HiddenWellAutoNoteRawId = (247u << 16) | 0x00dfu;

    CHECK(rewardHarness.eventRuntimeState().variables.contains(HiddenWellAutoNoteRawId));
}

TEST_CASE("event beacon actual stat checks include temporary bonuses")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    OpenYAMM::Game::Character *pMember = harness.party().activeMember();

    REQUIRE(pMember != nullptr);

    pMember->endurance = 20;
    pMember->permanentBonuses.endurance = 0;
    pMember->magicalBonuses.endurance = 5;

    REQUIRE(harness.executeGlobalEvent(544));
    REQUIRE_FALSE(harness.eventRuntimeState().statusMessages.empty());
    CHECK_EQ(harness.eventRuntimeState().statusMessages.back(), "You win!  +3 Skill Points");
}

TEST_CASE("event beacon actual stat checks include equipped item bonuses")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);
    OpenYAMM::Game::Character *pMember = harness.party().activeMember();

    REQUIRE(pMember != nullptr);

    pMember->endurance = 20;
    pMember->permanentBonuses.endurance = 0;
    pMember->magicalBonuses.endurance = 0;
    pMember->equipment.mainHand = 503;

    REQUIRE(harness.executeGlobalEvent(544));
    REQUIRE_FALSE(harness.eventRuntimeState().statusMessages.empty());
    CHECK_EQ(harness.eventRuntimeState().statusMessages.back(), "You win!  +3 Skill Points");
}

TEST_CASE("promotion champion event primary knight")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    harness.party().grantItem(539);

    REQUIRE(harness.executeGlobalEvent(58));

    const OpenYAMM::Game::Character *pMember0 = harness.party().member(0);
    const OpenYAMM::Game::Character *pMember1 = harness.party().member(1);

    REQUIRE(pMember0 != nullptr);
    REQUIRE(pMember1 != nullptr);
    CHECK_EQ(pMember0->className, "Champion");
    CHECK_EQ(pMember1->className, "Cleric");
    CHECK(harness.party().hasAward(0, 23));
    CHECK_FALSE(harness.party().hasAward(1, 23));
    CHECK_EQ(harness.party().inventoryItemCount(539), 0u);
}

TEST_CASE("promotion champion event multiple member indices")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    REQUIRE(harness.party().setMemberClassName(0, "Cleric"));
    REQUIRE(harness.party().setMemberClassName(1, "Knight"));
    REQUIRE(harness.party().setMemberClassName(2, "Knight"));
    REQUIRE(harness.party().grantItemToMember(1, 539));
    REQUIRE(harness.party().grantItemToMember(2, 539));

    REQUIRE(harness.executeGlobalEvent(58));

    const OpenYAMM::Game::Character *pMember0 = harness.party().member(0);
    const OpenYAMM::Game::Character *pMember1 = harness.party().member(1);
    const OpenYAMM::Game::Character *pMember2 = harness.party().member(2);
    const OpenYAMM::Game::Character *pMember3 = harness.party().member(3);

    REQUIRE(pMember0 != nullptr);
    REQUIRE(pMember1 != nullptr);
    REQUIRE(pMember2 != nullptr);
    REQUIRE(pMember3 != nullptr);
    CHECK_EQ(pMember0->className, "Cleric");
    CHECK_EQ(pMember1->className, "Champion");
    CHECK_EQ(pMember2->className, "Champion");
    CHECK_NE(pMember3->className, "Champion");
    CHECK(harness.party().hasAward(1, 23));
    CHECK(harness.party().hasAward(2, 23));
    CHECK_FALSE(harness.party().hasAward(0, 23));
    CHECK_FALSE(harness.party().hasAward(3, 23));
    CHECK_EQ(harness.party().inventoryItemCount(539), 0u);
}

TEST_CASE("event buoys grant skill points")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness northHarness(gameData);
    OpenYAMM::Game::Character *pNorthMember = northHarness.party().activeMember();

    REQUIRE(pNorthMember != nullptr);

    pNorthMember->luck = 13;
    pNorthMember->skillPoints = 0;

    REQUIRE(northHarness.executeOut01LocalEvent(497));
    CHECK_EQ(pNorthMember->skillPoints, 2);

    OpenYAMM::Tests::HouseDialogueTestHarness southHarness(gameData);
    OpenYAMM::Game::Character *pSouthMember = southHarness.party().activeMember();

    REQUIRE(pSouthMember != nullptr);

    pSouthMember->luck = 20;
    pSouthMember->skillPoints = 0;

    REQUIRE(southHarness.executeOut01LocalEvent(498));
    CHECK_EQ(pSouthMember->skillPoints, 5);
}

TEST_CASE("event palm tree requires perception skill")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness blockedHarness(gameData);
    OpenYAMM::Game::Character *pBlockedMember = blockedHarness.party().activeMember();

    REQUIRE(pBlockedMember != nullptr);
    REQUIRE(setCharacterSkill(
        *pBlockedMember,
        "Perception",
        2,
        OpenYAMM::Game::SkillMastery::Normal) != nullptr);

    REQUIRE(blockedHarness.executeOut01LocalEvent(494));
    CHECK_FALSE(blockedHarness.party().hasQuestBit(270));

    OpenYAMM::Tests::HouseDialogueTestHarness rewardHarness(gameData);
    OpenYAMM::Game::Character *pRewardMember = rewardHarness.party().activeMember();

    REQUIRE(pRewardMember != nullptr);
    REQUIRE(setCharacterSkill(
        *pRewardMember,
        "Perception",
        3,
        OpenYAMM::Game::SkillMastery::Normal) != nullptr);

    REQUIRE(rewardHarness.executeOut01LocalEvent(494));
    CHECK(rewardHarness.party().hasQuestBit(270));
}

TEST_CASE("long tail tobersk buy topic remains available after purchase")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    harness.party().addGold(1000);

    OpenYAMM::Game::EventDialogContent dialog = harness.openNpcDialogue(LongTailNpcId);
    CHECK(dialogHasActionLabel(dialog, "Buy Tobersk Fruit for 200 gold"));

    const std::optional<size_t> buyTopicIndex =
        findActionIndexByLabel(dialog, "Buy Tobersk Fruit for 200 gold");

    REQUIRE(buyTopicIndex.has_value());
    harness.executeAndPresent(*buyTopicIndex);

    dialog = harness.openNpcDialogue(LongTailNpcId);
    CHECK(dialogHasActionLabel(dialog, "Buy Tobersk Fruit for 200 gold"));
}

TEST_CASE("event tobersk buy and sell update gold items and weekday price")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    harness.party().addGold(1000);
    const int goldBeforeBuy = harness.party().gold();

    REQUIRE(harness.executeGlobalEvent(250));
    CHECK_EQ(harness.party().gold(), goldBeforeBuy - 200);
    CHECK_EQ(harness.party().inventoryItemCount(643), 1);

    REQUIRE(harness.party().grantItemToMember(2, 645));

    harness.worldRuntime().advanceGameMinutes(-harness.worldRuntime().gameMinutes());
    const int goldBeforeSale = harness.party().gold();

    REQUIRE(harness.executeGlobalEvent(251));
    CHECK_EQ(harness.party().inventoryItemCount(645), 0);
    CHECK_EQ(harness.party().gold(), goldBeforeSale + 557);
}

TEST_CASE("event teacher hint sets autonote and note fx")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    OpenYAMM::Tests::HouseDialogueTestHarness harness(gameData);

    REQUIRE(harness.executeGlobalEvent(430));

    constexpr uint32_t SpearMasterAutoNoteRawId = (141u << 16) | 0x00e1u;
    const auto noteIt = harness.eventRuntimeState().variables.find(SpearMasterAutoNoteRawId);

    REQUIRE(noteIt != harness.eventRuntimeState().variables.end());
    CHECK_NE(noteIt->second, 0);

    bool sawAutoNoteFx = false;

    for (const OpenYAMM::Game::EventRuntimeState::PortraitFxRequest &request :
         harness.eventRuntimeState().portraitFxRequests)
    {
        if (request.kind == OpenYAMM::Game::PortraitFxEventKind::AutoNote
            && std::find(
                   request.memberIndices.begin(),
                   request.memberIndices.end(),
                   harness.party().activeMemberIndex()) != request.memberIndices.end())
        {
            sawAutoNoteFx = true;
            break;
        }
    }

    CHECK(sawAutoNoteFx);
    REQUIRE_FALSE(harness.eventRuntimeState().messages.empty());
    CHECK_NE(
        harness.eventRuntimeState().messages.front().find("Ashandra Withersmythe"),
        std::string::npos);
}
