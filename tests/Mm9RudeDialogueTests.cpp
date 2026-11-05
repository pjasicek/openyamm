#include "doctest/doctest.h"

#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "game/data/GameDataLoader.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayDialogController.h"
#include "game/gameplay/HouseServiceRuntime.h"
#include "game/gameplay/JournalQuestRuntime.h"
#include "game/items/ItemRuntime.h"
#include "game/maps/OutdoorSceneYml.h"
#include "game/maps/MapDeltaData.h"
#include "game/maps/SaveGame.h"
#include "game/mm9/Mm9RudeDialogue.h"
#include "game/party/Party.h"
#include "game/ui/GameplayUiController.h"
#include "game/ui/GameplayOverlayTypes.h"
#include "tests/PartySpellTestHarness.h"

#include <algorithm>
#include <array>
#include <fstream>
#include <initializer_list>
#include <string>
#include <filesystem>
#include <sstream>
#include <unordered_set>
#include <utility>
#include <vector>

namespace
{
std::string rudeRow(
    int32_t rudeId,
    int32_t nodeId,
    int32_t choiceSlot,
    const std::string &prompt,
    const std::string &response,
    int32_t next,
    int32_t requiredKey = 0)
{
    std::vector<std::string> columns(30, "0");
    columns[0] = std::to_string(rudeId);
    columns[1] = std::to_string(nodeId);
    columns[2] = std::to_string(choiceSlot);
    columns[3] = '"' + prompt + '"';
    columns[4] = '"' + response + '"';
    columns[5] = std::to_string(next);
    columns[6] = std::to_string(requiredKey);

    std::string text;
    for (size_t index = 0; index < columns.size(); ++index)
    {
        if (index != 0)
        {
            text += ',';
        }
        text += columns[index];
    }
    return text + '\n';
}

std::string rudeRowWithFields(
    int32_t rudeId,
    int32_t nodeId,
    int32_t choiceSlot,
    const std::string &prompt,
    const std::string &response,
    int32_t next,
    std::initializer_list<std::pair<size_t, int32_t>> fields)
{
    std::vector<std::string> columns(30, "0");
    columns[0] = std::to_string(rudeId);
    columns[1] = std::to_string(nodeId);
    columns[2] = std::to_string(choiceSlot);
    columns[3] = '"' + prompt + '"';
    columns[4] = '"' + response + '"';
    columns[5] = std::to_string(next);

    for (const std::pair<size_t, int32_t> &field : fields)
    {
        columns.at(field.first - 1) = std::to_string(field.second);
    }

    std::string text;
    for (size_t index = 0; index < columns.size(); ++index)
    {
        if (index != 0)
        {
            text += ',';
        }
        text += columns[index];
    }
    return text + '\n';
}

const OpenYAMM::Game::Mm9RudeRow *findVisibleRow(
    const OpenYAMM::Game::Mm9RudeDialogueTable &table,
    uint32_t rudeId,
    int32_t nodeId,
    const OpenYAMM::Game::Party &party,
    const std::string &prompt)
{
    const std::vector<const OpenYAMM::Game::Mm9RudeRow *> rows = table.visibleRows(rudeId, nodeId, party);
    const auto iterator = std::find_if(
        rows.begin(),
        rows.end(),
        [&prompt](const OpenYAMM::Game::Mm9RudeRow *pRow)
        {
            return pRow->prompt == prompt;
        });
    return iterator != rows.end() ? *iterator : nullptr;
}

class Mm9RudeExitTestWorldRuntime : public OpenYAMM::Tests::PartySpellTestWorldRuntime
{
public:
    bool executeMapEvent(
        uint16_t eventId,
        size_t &previousMessageCount,
        std::optional<uint8_t> continueStep = std::nullopt) override
    {
        (void)previousMessageCount;
        (void)continueStep;
        ++executeCount;
        lastEventId = eventId;
        return true;
    }

    const OpenYAMM::Game::MapDeltaData *mapDeltaData() const override
    {
        return &mapDelta;
    }

    OpenYAMM::Game::MapDeltaData *mapDeltaData() override
    {
        return &mapDelta;
    }

    OpenYAMM::Game::MapDeltaData mapDelta = {};
    size_t executeCount = 0;
    uint16_t lastEventId = 0;
};

std::string loadSourceText(const std::filesystem::path &relativePath)
{
    const std::filesystem::path path = std::filesystem::path(OPENYAMM_SOURCE_DIR) / relativePath;
    std::ifstream input(path);
    std::ostringstream stream;
    stream << input.rdbuf();
    return stream.str();
}
}

TEST_CASE("MM9 raw quest keys map into the reserved 90000 QBit namespace")
{
    CHECK_FALSE(OpenYAMM::Game::mm9QBitForRawQuestKey(0).has_value());
    CHECK(OpenYAMM::Game::mm9QBitForRawQuestKey(1) == 90001u);
    CHECK(OpenYAMM::Game::mm9QBitForRawQuestKey(9516) == 99516u);
    CHECK(OpenYAMM::Game::mm9QBitForRawQuestKey(9999) == 99999u);
    CHECK_FALSE(OpenYAMM::Game::mm9QBitForRawQuestKey(10000).has_value());

    CHECK_FALSE(OpenYAMM::Game::mm9RawQuestKeyForQBit(90000).has_value());
    CHECK(OpenYAMM::Game::mm9RawQuestKeyForQBit(90001) == 1);
    CHECK(OpenYAMM::Game::mm9RawQuestKeyForQBit(99516) == 9516);
    CHECK(OpenYAMM::Game::mm9RawQuestKeyForQBit(99999) == 9999);
}

TEST_CASE("MM9 RUDE exit callbacks use a source-object-specific event range")
{
    CHECK(OpenYAMM::Game::mm9RudeExitEventIdForSourceObject(0) == 50000u);
    CHECK(OpenYAMM::Game::mm9RudeExitEventIdForSourceObject(207) == 50207u);
    CHECK(OpenYAMM::Game::mm9RudeExitEventIdForSourceObject(2999) == 52999u);
    CHECK_FALSE(OpenYAMM::Game::mm9RudeExitEventIdForSourceObject(3000).has_value());
}

TEST_CASE("MM9 RUDE entry callbacks use source-object-specific event ranges")
{
    CHECK(OpenYAMM::Game::mm9RudeUseEventIdForSourceObject(207) == 53207u);
    CHECK(OpenYAMM::Game::mm9RudeFoundPlayerEventIdForSourceObject(207) == 56207u);
    CHECK_FALSE(OpenYAMM::Game::mm9RudeUseEventIdForSourceObject(3000).has_value());
    CHECK_FALSE(OpenYAMM::Game::mm9RudeFoundPlayerEventIdForSourceObject(3000).has_value());
}

TEST_CASE("MM9 RUDE and live-gameplay vendor presentations select their intended HUD layouts")
{
    OpenYAMM::Game::EventDialogContent dialog = {};
    CHECK_FALSE(OpenYAMM::Game::activeEventDialogPreservesGameplayHud(dialog));

    dialog.isActive = true;
    CHECK_FALSE(OpenYAMM::Game::activeEventDialogPreservesGameplayHud(dialog));

    dialog.presentation = OpenYAMM::Game::EventDialogPresentation::Mm9Rude;
    CHECK(OpenYAMM::Game::activeEventDialogPreservesGameplayHud(dialog));

    dialog.presentation = OpenYAMM::Game::EventDialogPresentation::Standard;
    dialog.isHouseDialog = true;
    dialog.scenePolicy = OpenYAMM::Game::DialogueScenePolicy::LiveGameplay;
    CHECK_FALSE(OpenYAMM::Game::activeEventDialogPreservesGameplayHud(dialog));
    CHECK_FALSE(OpenYAMM::Game::gameplayHudScreenFullyOccludesWorld(
        OpenYAMM::Game::GameplayHudScreenState::Dialogue,
        dialog));
    CHECK_FALSE(OpenYAMM::Game::activeEventDialogShowsVideoArea(dialog, true));
    CHECK_FALSE(OpenYAMM::Game::activeEventDialogAllowsHouseVideoPlayback(dialog));

    dialog.scenePolicy = OpenYAMM::Game::DialogueScenePolicy::HouseVideo;
    CHECK(OpenYAMM::Game::activeEventDialogShowsVideoArea(dialog, true));
    CHECK(OpenYAMM::Game::activeEventDialogAllowsHouseVideoPlayback(dialog));
}

TEST_CASE("MM9 RUDE topics retain source ordering and use mapped QBit conditions")
{
    OpenYAMM::Game::Mm9RudeDialogueTable table;
    const std::string text =
        rudeRow(436, 436, 2, "Locked, topic", "Locked response", -1, 474)
        + rudeRow(436, 436, 1, "Open topic", "Open response", 3)
        + rudeRow(436, 3, 1, "Finish", "blank", -1);
    REQUIRE(table.loadDialogueText("NPC436.rude", text));
    REQUIRE(table.loadNpcNamesText("NPCNAME.rude", "436,Grandpa\n"));
    REQUIRE(table.loadTopBlurbsText("TOPBLURB.rude", "436,436,Welcome.\n"));

    OpenYAMM::Game::Party party;
    std::vector<const OpenYAMM::Game::Mm9RudeRow *> topics = table.visibleRows(436, 436, party);
    REQUIRE(topics.size() == 1);
    CHECK(topics[0]->prompt == "Open topic");
    CHECK(table.npcName(436) == "Grandpa");
    CHECK(table.topBlurb(436) == "Welcome.");

    party.setQuestBit(90474, true);
    topics = table.visibleRows(436, 436, party);
    REQUIRE(topics.size() == 2);
    CHECK(topics[0]->choiceSlot == 1);
    CHECK(topics[1]->choiceSlot == 2);

    const OpenYAMM::Game::Mm9RudeSelection gotoSelection = OpenYAMM::Game::selectMm9RudeRow(*topics[0]);
    CHECK(gotoSelection.kind == OpenYAMM::Game::Mm9RudeSelectionKind::GotoNode);
    CHECK(gotoSelection.next == 3);

    const std::vector<const OpenYAMM::Game::Mm9RudeRow *> finishTopics = table.visibleRows(436, 3, party);
    REQUIRE(finishTopics.size() == 1);
    const OpenYAMM::Game::Mm9RudeSelection closeSelection =
        OpenYAMM::Game::selectMm9RudeRow(*finishTopics[0]);
    CHECK(closeSelection.kind == OpenYAMM::Game::Mm9RudeSelectionKind::Close);
    CHECK(closeSelection.response.empty());
}

TEST_CASE("MM9 RUDE quest handoff rows close dialogue")
{
    OpenYAMM::Game::Mm9RudeDialogueTable table;
    REQUIRE(table.loadDialogueText(
        "NPC89.rude",
        rudeRow(89, 998, 1, "Goodbye", "blank", -14)));

    OpenYAMM::Game::Party party;
    const OpenYAMM::Game::Mm9RudeRow *pGoodbye = findVisibleRow(table, 89, 998, party, "Goodbye");
    REQUIRE(pGoodbye != nullptr);

    const OpenYAMM::Game::Mm9RudeSelection selection = OpenYAMM::Game::selectMm9RudeRow(*pGoodbye);
    CHECK(selection.kind == OpenYAMM::Game::Mm9RudeSelectionKind::Close);
    CHECK(selection.response.empty());
}

TEST_CASE("MM9 Keith Bloodaxe quest acceptance grants the Yobboe quest key before handoff close")
{
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assetFileSystem.initialize(
        sourceRoot,
        sourceRoot / "assets_dev",
        OpenYAMM::Engine::AssetScaleTier::X1,
        "mm9"));

    OpenYAMM::Game::Mm9RudeDialogueTable table;
    REQUIRE(table.load(assetFileSystem));
    OpenYAMM::Game::Party party;

    const OpenYAMM::Game::Mm9RudeRow *pAccept =
        findVisibleRow(table, 89, 3, party, "We will accept this task.");
    REQUIRE(pAccept != nullptr);
    OpenYAMM::Game::applyMm9RudeRowActions(*pAccept, party);
    CHECK(party.hasQuestBit(90128));

    const OpenYAMM::Game::Mm9RudeRow *pGoodbye = findVisibleRow(table, 89, 998, party, "Goodbye");
    REQUIRE(pGoodbye != nullptr);
    CHECK(OpenYAMM::Game::selectMm9RudeRow(*pGoodbye).kind == OpenYAMM::Game::Mm9RudeSelectionKind::Close);
}

TEST_CASE("MM9 RUDE ordinary rows apply all key groups while service payloads remain untouched")
{
    OpenYAMM::Game::Mm9RudeDialogueTable table;
    const std::string text = rudeRowWithFields(
        200,
        200,
        1,
        "Advance",
        "Done",
        201,
        {
            {7, 10},
            {9, 11},
            {15, 12},
            {16, 20},
            {17, 21},
            {18, 50},
            {21, 30},
            {22, 31},
            {26, 40},
            {27, 41},
            {28, 50},
        })
        + rudeRowWithFields(200, 200, 2, "Train", "Certainly", -4, {{16, 2073}});
    REQUIRE(table.loadDialogueText("NPC200.rude", text));

    OpenYAMM::Game::Party party;
    party.setQuestBit(90010, true);
    party.setQuestBit(90011, true);
    party.setQuestBit(90012, true);
    party.setQuestBit(90040, true);
    party.setQuestBit(90041, true);

    std::vector<const OpenYAMM::Game::Mm9RudeRow *> rows = table.visibleRows(200, 200, party);
    REQUIRE(rows.size() == 2);
    const OpenYAMM::Game::Mm9RudeRow *pAdvance = findVisibleRow(table, 200, 200, party, "Advance");
    REQUIRE(pAdvance != nullptr);
    OpenYAMM::Game::applyMm9RudeRowActions(*pAdvance, party);
    CHECK(party.hasQuestBit(90020));
    CHECK(party.hasQuestBit(90021));
    CHECK_FALSE(party.hasQuestBit(90040));
    CHECK_FALSE(party.hasQuestBit(90041));
    CHECK_FALSE(party.hasQuestBit(90050));

    party.setQuestBit(90030, true);
    CHECK(findVisibleRow(table, 200, 200, party, "Advance") == nullptr);

    const OpenYAMM::Game::Mm9RudeRow *pService = findVisibleRow(table, 200, 200, party, "Train");
    REQUIRE(pService != nullptr);
    OpenYAMM::Game::applyMm9RudeRowActions(*pService, party);
    CHECK_FALSE(party.hasQuestBit(92073));
}

TEST_CASE("MM9 RUDE hire and dismiss rows apply their quest key columns")
{
    // NPC2.rude line 13 (Forad's "Welcome Aboard.") hires with c16-c17 = 29, 371; a dismissal removes its hire key.
    OpenYAMM::Game::Mm9RudeDialogueTable table;
    const std::string text = rudeRowWithFields(2, 2, 1, "Welcome Aboard.", "asdf", -10, {{16, 29}, {17, 371}})
        + rudeRowWithFields(2, 2, 2, "You're fired.", "Fine", -11, {{7, 455}, {26, 455}})
        + rudeRowWithFields(2, 2, 3, "Passage", "Alright!", -5, {{16, 5017}});
    REQUIRE(table.loadDialogueText("NPC2.rude", text));

    OpenYAMM::Game::Party party;
    const OpenYAMM::Game::Mm9RudeRow *pHire = findVisibleRow(table, 2, 2, party, "Welcome Aboard.");
    REQUIRE(pHire != nullptr);
    OpenYAMM::Game::applyMm9RudeRowActions(*pHire, party);
    CHECK(party.hasQuestBit(90029));
    CHECK(party.hasQuestBit(90371));

    party.setQuestBit(90455, true);
    const OpenYAMM::Game::Mm9RudeRow *pDismiss = findVisibleRow(table, 2, 2, party, "You're fired.");
    REQUIRE(pDismiss != nullptr);
    OpenYAMM::Game::applyMm9RudeRowActions(*pDismiss, party);
    CHECK_FALSE(party.hasQuestBit(90455));

    const OpenYAMM::Game::Mm9RudeRow *pTravel = findVisibleRow(table, 2, 2, party, "Passage");
    REQUIRE(pTravel != nullptr);
    OpenYAMM::Game::applyMm9RudeRowActions(*pTravel, party);
    CHECK_FALSE(party.hasQuestBit(95017));
}

TEST_CASE("MM9 RUDE skill trainer payloads map ranks and expand composite core skills")
{
    OpenYAMM::Game::Mm9RudeDialogueTable table;
    const std::string text =
        rudeRowWithFields(80, 80, 1, "Expert Blade", "Ready?", -4, {{16, 2006}})
        + rudeRowWithFields(80, 80, 2, "Master Blade", "Ready?", -4, {{16, 2006}})
        + rudeRowWithFields(80, 80, 3, "Grandmaster Armor", "Ready?", -4, {{16, 2029}})
        + rudeRowWithFields(80, 80, 4, "Grandmaster Spear", "Ready?", -4, {{16, 2014}})
        + rudeRowWithFields(80, 80, 5, "Grandmaster Elemental", "Ready?", -4, {{16, 2038}});
    REQUIRE(table.loadDialogueText("NPC80.rude", text));

    const OpenYAMM::Game::Mm9RudeRow *pExpertBladeRow = table.rowByIndex(80, 0);
    REQUIRE(pExpertBladeRow != nullptr);
    const std::optional<OpenYAMM::Game::Mm9RudeSkillTrainerTopic> expertBladeTopic =
        OpenYAMM::Game::resolveMm9RudeSkillTrainerTopic(*pExpertBladeRow);
    REQUIRE(expertBladeTopic.has_value());
    const OpenYAMM::Game::Mm9RudeSkillTrainerTopic &expertBlade = *expertBladeTopic;
    CHECK(expertBlade.targetMastery == OpenYAMM::Game::SkillMastery::Expert);
    CHECK((expertBlade.skillNames == std::vector<std::string>{"Sword", "Dagger"}));

    const OpenYAMM::Game::Mm9RudeRow *pMasterBladeRow = table.rowByIndex(80, 1);
    REQUIRE(pMasterBladeRow != nullptr);
    const std::optional<OpenYAMM::Game::Mm9RudeSkillTrainerTopic> masterBladeTopic =
        OpenYAMM::Game::resolveMm9RudeSkillTrainerTopic(*pMasterBladeRow);
    REQUIRE(masterBladeTopic.has_value());
    const OpenYAMM::Game::Mm9RudeSkillTrainerTopic &masterBlade = *masterBladeTopic;
    CHECK(masterBlade.targetMastery == OpenYAMM::Game::SkillMastery::Master);

    const OpenYAMM::Game::Mm9RudeRow *pGrandmasterArmorRow = table.rowByIndex(80, 2);
    REQUIRE(pGrandmasterArmorRow != nullptr);
    const std::optional<OpenYAMM::Game::Mm9RudeSkillTrainerTopic> grandmasterArmorTopic =
        OpenYAMM::Game::resolveMm9RudeSkillTrainerTopic(*pGrandmasterArmorRow);
    REQUIRE(grandmasterArmorTopic.has_value());
    const OpenYAMM::Game::Mm9RudeSkillTrainerTopic &grandmasterArmor = *grandmasterArmorTopic;
    CHECK(grandmasterArmor.targetMastery == OpenYAMM::Game::SkillMastery::Grandmaster);
    CHECK((grandmasterArmor.skillNames
        == std::vector<std::string>{"LeatherArmor", "ChainArmor", "PlateArmor"}));

    const OpenYAMM::Game::Mm9RudeRow *pGrandmasterSpearRow = table.rowByIndex(80, 3);
    REQUIRE(pGrandmasterSpearRow != nullptr);
    const std::optional<OpenYAMM::Game::Mm9RudeSkillTrainerTopic> grandmasterSpearTopic =
        OpenYAMM::Game::resolveMm9RudeSkillTrainerTopic(*pGrandmasterSpearRow);
    REQUIRE(grandmasterSpearTopic.has_value());
    const OpenYAMM::Game::Mm9RudeSkillTrainerTopic &grandmasterSpear = *grandmasterSpearTopic;
    CHECK((grandmasterSpear.skillNames == std::vector<std::string>{"Spear"}));

    const OpenYAMM::Game::Mm9RudeRow *pGrandmasterElementalRow = table.rowByIndex(80, 4);
    REQUIRE(pGrandmasterElementalRow != nullptr);
    const std::optional<OpenYAMM::Game::Mm9RudeSkillTrainerTopic> grandmasterElementalTopic =
        OpenYAMM::Game::resolveMm9RudeSkillTrainerTopic(*pGrandmasterElementalRow);
    REQUIRE(grandmasterElementalTopic.has_value());
    const OpenYAMM::Game::Mm9RudeSkillTrainerTopic &grandmasterElemental = *grandmasterElementalTopic;
    CHECK((grandmasterElemental.skillNames
        == std::vector<std::string>{"FireMagic", "AirMagic", "WaterMagic", "EarthMagic"}));
}

TEST_CASE("MM9 RUDE composite trainer topics use one atomic mastery transaction")
{
    OpenYAMM::Game::Mm9RudeDialogueTable table;
    REQUIRE(table.loadDialogueText(
        "NPC80.rude",
        rudeRowWithFields(80, 80, 1, "Expert Blade", "Are you ready?", -4, {{16, 2006}})));

    OpenYAMM::Game::ClassSkillTable classSkillTable;
    REQUIRE(classSkillTable.loadCapsFromRows({
        {"", "Test Class"},
        {"Dagger", "G"},
        {"Sword", "G"},
        {"Axe", "B"},
    }));
    OpenYAMM::Game::NpcDialogTable npcDialogTable;

    OpenYAMM::Game::Character member = {};
    member.name = "Trainer Test";
    member.className = "Test Class";
    member.maxHealth = 10;
    member.health = 10;
    member.skills["Dagger"] = {"Dagger", 4, OpenYAMM::Game::SkillMastery::Normal};
    member.skills["Sword"] = {"Sword", 4, OpenYAMM::Game::SkillMastery::Normal};
    member.skills["Axe"] = {"Axe", 4, OpenYAMM::Game::SkillMastery::Normal};

    OpenYAMM::Game::PartySeed seed = {};
    seed.gold = 5000;
    seed.members.push_back(member);
    OpenYAMM::Game::Party party;
    party.seed(seed);

    OpenYAMM::Game::GameplayUiController uiController;
    OpenYAMM::Game::EventRuntimeState eventRuntimeState;
    OpenYAMM::Game::EventDialogContent dialog = {};
    size_t selectionIndex = 0;
    OpenYAMM::Game::GameplayDialogController::Context context = {
        .uiController = uiController,
        .eventRuntimeState = eventRuntimeState,
        .activeEventDialog = dialog,
        .selectionIndex = selectionIndex,
        .pParty = &party,
        .pClassSkillTable = &classSkillTable,
        .pNpcDialogTable = &npcDialogTable,
        .pMm9RudeDialogueTable = &table,
    };
    const OpenYAMM::Game::GameplayDialogController controller;
    controller.openMm9RudeDialogue(context, 80);

    REQUIRE(dialog.actions.size() == 1);
    CHECK(dialog.actions[0].label == "Expert Blade");

    selectionIndex = 0;
    controller.executeActiveDialogAction(context);
    REQUIRE(dialog.actions.size() == 2);
    CHECK(dialog.actions[0].label == "Become Expert in Blade for 2000 gold");
    CHECK(dialog.actions[1].kind == OpenYAMM::Game::EventDialogActionKind::Mm9RudeSkillTrainerBack);

    selectionIndex = 1;
    controller.executeActiveDialogAction(context);
    REQUIRE(dialog.actions.size() == 1);

    selectionIndex = 0;
    controller.executeActiveDialogAction(context);
    REQUIRE(dialog.actions.size() == 2);

    selectionIndex = 0;
    controller.executeActiveDialogAction(context);
    REQUIRE(party.activeMember() != nullptr);
    CHECK(party.activeMember()->findSkill("Dagger")->mastery == OpenYAMM::Game::SkillMastery::Expert);
    CHECK(party.activeMember()->findSkill("Sword")->mastery == OpenYAMM::Game::SkillMastery::Expert);
    CHECK(party.activeMember()->findSkill("Axe")->mastery == OpenYAMM::Game::SkillMastery::Normal);
    CHECK(party.gold() == 3000);
    CHECK(uiController.statusBar().eventText == "Trainer Test is now a Expert in Blade.");
}

TEST_CASE("MM9 actor activation opens the RUDE dialogue with the actor as its source")
{
    OpenYAMM::Game::Mm9RudeDialogueTable table;
    REQUIRE(table.loadDialogueText("NPC90.rude", rudeRow(90, 90, 1, "Hello", "Well met.", -1)));

    OpenYAMM::Game::Character member = {};
    member.name = "Dialogue Test";
    member.maxHealth = 10;
    member.health = 10;
    OpenYAMM::Game::PartySeed seed = {};
    seed.members.push_back(member);
    OpenYAMM::Game::Party party;
    party.seed(seed);
    OpenYAMM::Game::GameplayUiController uiController;
    OpenYAMM::Game::EventRuntimeState eventRuntimeState;
    OpenYAMM::Game::EventDialogContent dialog = {};
    size_t selectionIndex = 0;
    OpenYAMM::Game::GameplayDialogController::Context context = {
        .uiController = uiController,
        .eventRuntimeState = eventRuntimeState,
        .activeEventDialog = dialog,
        .selectionIndex = selectionIndex,
        .pParty = &party,
        .pMm9RudeDialogueTable = &table,
    };
    const OpenYAMM::Game::GameplayDialogController controller;
    int presented = 0;
    OpenYAMM::Game::GameplayDialogController::Mm9ActorDialogueActivation activation = {};
    activation.rudeId = 90;
    activation.actorIndex = 7;
    activation.sourceObjectIndex = 68;

    CHECK(controller.activateMm9ActorDialogue(
        context,
        activation,
        [](size_t) { FAIL("no SCR entry event ran"); },
        [&presented]() { ++presented; }));
    CHECK(presented == 1);
    CHECK(dialog.isActive);
    CHECK(dialog.presentation == OpenYAMM::Game::EventDialogPresentation::Mm9Rude);
    CHECK(dialog.sourceActorIndex == std::optional<uint32_t>(7));
    CHECK(eventRuntimeState.lastActivationResult == "MM9 RUDE 90 engaged");

    dialog = {};
    activation.rudeId = 91;
    CHECK_FALSE(controller.activateMm9ActorDialogue(context, activation, [](size_t) {}, [&presented]() { ++presented; }));
    CHECK_FALSE(dialog.isActive);
    CHECK(eventRuntimeState.lastActivationResult == "MM9 RUDE 91 failed");
}

TEST_CASE("MM9 RUDE quest-key actions queue shared quest presentation when an overlay row appears")
{
    OpenYAMM::Game::Mm9RudeDialogueTable dialogueTable;
    REQUIRE(dialogueTable.loadDialogueText(
        "NPC436.rude",
        rudeRowWithFields(436, 436, 1, "Continue", "Go explore.", -1, {{16, 473}})));

    OpenYAMM::Game::JournalQuestTable questTable = {};
    REQUIRE(questTable.loadFromRows({
        {"90001", "Complete training.", "", "MM9", "", "90473"},
        {"90002", "Search the island.", "", "MM9", "90473", "90480"},
    }));

    OpenYAMM::Game::Party party = {};
    party.seed(OpenYAMM::Tests::createSpellRegressionPartySeed());
    party.setJournalQuestTable(&questTable);
    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    const OpenYAMM::Game::Mm9RudeRow *pRow = dialogueTable.rowByIndex(436, 0);
    REQUIRE(pRow != nullptr);

    OpenYAMM::Game::applyMm9RudeRowActions(*pRow, party, &runtimeState);
    CHECK(party.hasQuestBit(90473));
    REQUIRE_EQ(runtimeState.portraitFxRequests.size(), 1u);
    CHECK_EQ(runtimeState.portraitFxRequests.front().kind, OpenYAMM::Game::PortraitFxEventKind::QuestComplete);
    REQUIRE_EQ(runtimeState.pendingSounds.size(), 1u);
    CHECK_EQ(runtimeState.pendingSounds.front().soundId, static_cast<uint32_t>(OpenYAMM::Game::SoundId::Quest));
}

TEST_CASE("MM9 Old Man RUDE progression exposes departure and records its completion keys")
{
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assetFileSystem.initialize(
        sourceRoot,
        sourceRoot / "assets_dev",
        OpenYAMM::Engine::AssetScaleTier::X1,
        "mm9"));

    OpenYAMM::Game::Mm9RudeDialogueTable table;
    REQUIRE(table.load(assetFileSystem));
    OpenYAMM::Game::Party party;

    CHECK(findVisibleRow(table, 436, 436, party, "We're ready to leave.") == nullptr);
    REQUIRE(findVisibleRow(table, 436, 436, party, "We'd like to start our training.") != nullptr);

    const OpenYAMM::Game::Mm9RudeRow *pTrainingComplete =
        findVisibleRow(table, 436, 4, party, "Why?");
    REQUIRE(pTrainingComplete != nullptr);
    OpenYAMM::Game::applyMm9RudeRowActions(*pTrainingComplete, party);
    CHECK(party.hasQuestBit(90474));
    CHECK(findVisibleRow(table, 436, 436, party, "We'd like to start our training.") == nullptr);

    const OpenYAMM::Game::Mm9RudeRow *pReady =
        findVisibleRow(table, 436, 436, party, "We're ready to leave.");
    REQUIRE(pReady != nullptr);
    const OpenYAMM::Game::Mm9RudeRow *pDepartureComplete =
        findVisibleRow(table, 436, 5, party, "Why?");
    REQUIRE(pDepartureComplete != nullptr);
    OpenYAMM::Game::applyMm9RudeRowActions(*pDepartureComplete, party);
    CHECK(party.hasQuestBit(90475));
}

TEST_CASE("MM9 Old Man exit callback grants canonically mapped reward items")
{
    const std::string supportLua = loadSourceText("assets_dev/engine/scripts/common/event_support.lua");
    const std::string commonLua = loadSourceText("assets_dev/worlds/mm9/events/common/mm9_common.lua");
    const std::string worldLua = loadSourceText("assets_dev/worlds/mm9/events/common/world_common.lua");
    const std::string bootcampLua = loadSourceText("assets_dev/worlds/mm9/events/maps/bootcamp.lua");
    REQUIRE_FALSE(supportLua.empty());
    REQUIRE_FALSE(commonLua.empty());
    REQUIRE_FALSE(worldLua.empty());
    REQUIRE_FALSE(bootcampLua.empty());
    CHECK(worldLua.find("[197] = 10197") != std::string::npos);
    CHECK(worldLua.find("[253] = 222") != std::string::npos);
    CHECK(worldLua.find("[347] = 419") != std::string::npos);

    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> program =
        OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
            supportLua + "\n\n" + commonLua + "\n\n" + worldLua + "\n\n" + bootcampLua,
            "@events/maps/bootcamp.lua",
            OpenYAMM::Game::ScriptedEventScope::Map,
            error);
    REQUIRE_MESSAGE(program.has_value(), error.c_str());
    REQUIRE(program->hasEvent(50207));

    OpenYAMM::Game::Party party;
    party.setQuestBit(90475, true);
    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    runtimeState.mapFileName = "bootcamp.odm";
    const OpenYAMM::Game::EventRuntime eventRuntime;
    REQUIRE(eventRuntime.executeEventById(program, std::nullopt, 50207, runtimeState, &party));

    CHECK(party.hasQuestBit(90496));
    CHECK(runtimeState.statusMessages.empty());
    const auto grantedItemId = [&runtimeState](uint32_t itemId)
    {
        return std::any_of(
            runtimeState.grantedItems.begin(),
            runtimeState.grantedItems.end(),
            [itemId](const OpenYAMM::Game::InventoryItem &item)
            {
                return item.objectDescriptionId == itemId;
            });
    };
    CHECK(grantedItemId(10589));
    CHECK(grantedItemId(10298));
    CHECK(grantedItemId(10302));
}

TEST_CASE("MM9 hire dialogue swaps hire and dismiss topics through ordinary RUDE key conditions")
{
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assetFileSystem.initialize(
        sourceRoot,
        sourceRoot / "assets_dev",
        OpenYAMM::Engine::AssetScaleTier::X1,
        "mm9"));

    OpenYAMM::Game::Mm9RudeDialogueTable table;
    REQUIRE(table.load(assetFileSystem));
    OpenYAMM::Game::Party party;

    REQUIRE(findVisibleRow(table, 43, 43, party, "What do you mean?") != nullptr);
    CHECK(findVisibleRow(table, 43, 43, party, "We will no longer be needing your services.") == nullptr);

    party.setQuestBit(90451, true);
    CHECK(findVisibleRow(table, 43, 43, party, "What do you mean?") == nullptr);
    REQUIRE(findVisibleRow(table, 43, 43, party, "We will no longer be needing your services.") != nullptr);
}

TEST_CASE("MM9 RUDE exit callbacks execute only once across explicit and fallback close paths")
{
    OpenYAMM::Game::Mm9RudeDialogueTable table;
    REQUIRE(table.loadDialogueText(
        "NPC436.rude",
        rudeRow(436, 436, 1, "Goodbye, Grandpa.", "blank", -14)));

    OpenYAMM::Game::Party party;
    OpenYAMM::Game::GameplayUiController uiController;
    OpenYAMM::Game::EventRuntimeState eventRuntimeState;
    OpenYAMM::Game::EventDialogContent dialog = {};
    dialog.isActive = true;
    dialog.sourceId = 436;
    dialog.dialogueNodeId = 436;
    dialog.sourceActorIndex = 0;
    dialog.presentation = OpenYAMM::Game::EventDialogPresentation::Mm9Rude;
    dialog.actions.push_back({
        .kind = OpenYAMM::Game::EventDialogActionKind::Mm9RudeTopic,
        .id = 0,
        .label = "Goodbye, Grandpa.",
    });
    size_t selectionIndex = 0;
    Mm9RudeExitTestWorldRuntime worldRuntime;
    worldRuntime.bindParty(&party);
    OpenYAMM::Game::MapDeltaActor actor = {};
    actor.mm9SourceObjectIndex = 207;
    worldRuntime.mapDelta.actors.push_back(actor);
    OpenYAMM::Game::GameplayDialogController::Context context = {
        .uiController = uiController,
        .eventRuntimeState = eventRuntimeState,
        .activeEventDialog = dialog,
        .selectionIndex = selectionIndex,
        .pParty = &party,
        .pWorldRuntime = &worldRuntime,
        .pMm9RudeDialogueTable = &table,
    };

    const OpenYAMM::Game::GameplayDialogController controller;
    const OpenYAMM::Game::GameplayDialogController::Result selectionResult =
        controller.executeActiveDialogAction(context);
    CHECK(selectionResult.shouldCloseActiveDialog);
    CHECK(worldRuntime.executeCount == 1);
    CHECK(worldRuntime.lastEventId == 50207);
    CHECK(dialog.mm9RudeExitCallbackExecuted);

    const OpenYAMM::Game::GameplayDialogController::CloseDialogRequestResult closeResult =
        controller.handleDialogueCloseRequest(context);
    CHECK(closeResult.shouldCloseActiveDialog);
    CHECK(worldRuntime.executeCount == 1);
}

TEST_CASE("MM9 RUDE shop suspension opens a mounted live-gameplay vendor and restores RUDE")
{
    OpenYAMM::Game::Mm9RudeDialogueTable rudeTable;
    REQUIRE(rudeTable.loadDialogueText(
        "NPC53.rude",
        rudeRow(53, 53, 1, "Show us what you have.", "Certainly.", -2)
            + rudeRow(53, 53, 2, "Goodbye.", "blank", -1)));

    std::vector<std::string> vendorRow(25);
    vendorRow[0] = "30053";
    vendorRow[1] = "mm9";
    vendorRow[2] = "53";
    vendorRow[3] = "mm9:vendor/53";
    vendorRow[4] = "Ketil's Swords";
    vendorRow[5] = "Sturmford";
    vendorRow[6] = "Weapon";
    vendorRow[8] = "Weapon";
    vendorRow[11] = "1.2";
    vendorRow[13] = "1";
    vendorRow[16] = "1";
    vendorRow[18] = "14";
    vendorRow[19] = "1";
    vendorRow[20] = "1";
    vendorRow[21] = "1";
    vendorRow[22] = "LiveGameplay";
    std::vector<std::vector<std::string>> stockRows;
    for (uint32_t slotIndex = 0; slotIndex < 6; ++slotIndex)
    {
        stockRows.push_back({
            "30053", "standard", "0", std::to_string(slotIndex), "1", "1", "1", "0", "0", "0", "1",
        });
        stockRows.push_back({
            "30053", "special", "0", std::to_string(slotIndex), "1", "1", "1", "0", "0", "0", "1",
        });
    }
    OpenYAMM::Game::HouseTable houseTable;
    std::string vendorError;
    REQUIRE(houseTable.appendVendorRows(
        {vendorRow},
        {{"30053", "mm9", "53", "14"}},
        stockRows,
        vendorError));

    OpenYAMM::Game::Party party;
    OpenYAMM::Game::GameplayUiController uiController;
    OpenYAMM::Game::EventRuntimeState eventRuntimeState;
    OpenYAMM::Game::EventDialogContent dialog = {};
    size_t selectionIndex = 0;
    Mm9RudeExitTestWorldRuntime worldRuntime;
    worldRuntime.bindParty(&party);
    OpenYAMM::Game::MapDeltaActor actor = {};
    actor.mm9SourceObjectIndex = 53;
    worldRuntime.mapDelta.actors.push_back(actor);
    OpenYAMM::Game::GameplayDialogController::Context context = {
        .uiController = uiController,
        .eventRuntimeState = eventRuntimeState,
        .activeEventDialog = dialog,
        .selectionIndex = selectionIndex,
        .pParty = &party,
        .pWorldRuntime = &worldRuntime,
        .pHouseTable = &houseTable,
        .pMm9RudeDialogueTable = &rudeTable,
        .dialogueHudActive = true,
    };
    const OpenYAMM::Game::GameplayDialogController controller;
    controller.openMm9RudeDialogue(context, 53, 0);
    REQUIRE_EQ(dialog.actions.size(), 2);

    const OpenYAMM::Game::GameplayDialogController::Result openResult =
        controller.executeActiveDialogAction(context);
    CHECK(openResult.shouldOpenPendingEventDialog);
    REQUIRE(eventRuntimeState.pendingDialogueContext.has_value());
    CHECK(eventRuntimeState.pendingDialogueContext->kind == OpenYAMM::Game::DialogueContextKind::HouseService);
    CHECK_EQ(eventRuntimeState.pendingDialogueContext->sourceId, 30053);
    REQUIRE(eventRuntimeState.dialogueState.suspendedMm9RudeDialogue.has_value());
    CHECK_EQ(worldRuntime.executeCount, 0);

    dialog = {};
    dialog.isActive = true;
    dialog.isHouseDialog = true;
    dialog.sourceId = 30053;
    dialog.scenePolicy = OpenYAMM::Game::DialogueScenePolicy::LiveGameplay;
    eventRuntimeState.pendingDialogueContext.reset();
    eventRuntimeState.dialogueState.menuStack.push_back(
        OpenYAMM::Game::DialogueMenuId::ShopEquipment);
    uiController.openInventoryNestedOverlay(
        OpenYAMM::Game::GameplayUiController::InventoryNestedOverlayMode::ShopSell,
        30053);
    const OpenYAMM::Game::GameplayDialogController::CloseDialogRequestResult sellCloseResult =
        controller.handleDialogueCloseRequest(context);
    CHECK_FALSE(sellCloseResult.shouldCloseActiveDialog);
    CHECK_FALSE(sellCloseResult.shouldOpenPendingEventDialog);
    CHECK(uiController.inventoryNestedOverlay().mode
        == OpenYAMM::Game::GameplayUiController::InventoryNestedOverlayMode::ShopDisplay);
    CHECK(dialog.isHouseDialog);

    const OpenYAMM::Game::GameplayDialogController::CloseDialogRequestResult equipmentCloseResult =
        controller.handleDialogueCloseRequest(context);
    CHECK_FALSE(equipmentCloseResult.shouldCloseActiveDialog);
    CHECK(equipmentCloseResult.shouldOpenPendingEventDialog);
    CHECK(eventRuntimeState.dialogueState.menuStack.empty());
    CHECK(dialog.isHouseDialog);
    eventRuntimeState.pendingDialogueContext.reset();

    const OpenYAMM::Game::GameplayDialogController::CloseDialogRequestResult vendorCloseResult =
        controller.handleDialogueCloseRequest(context);
    CHECK_FALSE(vendorCloseResult.shouldCloseActiveDialog);
    CHECK_FALSE(vendorCloseResult.shouldOpenPendingEventDialog);
    CHECK(dialog.presentation == OpenYAMM::Game::EventDialogPresentation::Mm9Rude);
    CHECK_EQ(dialog.sourceId, 53);
    CHECK(dialog.sourceActorIndex == 0);
    CHECK_EQ(worldRuntime.executeCount, 0);

    const OpenYAMM::Game::GameplayDialogController::CloseDialogRequestResult rudeCloseResult =
        controller.handleDialogueCloseRequest(context);
    CHECK(rudeCloseResult.shouldCloseActiveDialog);
    CHECK_EQ(worldRuntime.executeCount, 1);
    CHECK_EQ(worldRuntime.lastEventId, 50053);
}

TEST_CASE("MM9 RUDE unresolved vendor remains visible with source-specific feedback")
{
    OpenYAMM::Game::Mm9RudeDialogueTable rudeTable;
    REQUIRE(rudeTable.loadDialogueText(
        "NPC53.rude",
        rudeRow(53, 53, 1, "Show us what you have.", "Certainly.", -2)
            + rudeRow(53, 53, 2, "Goodbye.", "blank", -1)));

    OpenYAMM::Game::Party party;
    OpenYAMM::Game::GameplayUiController uiController;
    OpenYAMM::Game::EventRuntimeState eventRuntimeState;
    OpenYAMM::Game::EventDialogContent dialog = {};
    size_t selectionIndex = 0;
    OpenYAMM::Game::HouseTable houseTable;
    OpenYAMM::Game::GameplayDialogController::Context context = {
        .uiController = uiController,
        .eventRuntimeState = eventRuntimeState,
        .activeEventDialog = dialog,
        .selectionIndex = selectionIndex,
        .pParty = &party,
        .pHouseTable = &houseTable,
        .pMm9RudeDialogueTable = &rudeTable,
        .dialogueHudActive = true,
    };
    const OpenYAMM::Game::GameplayDialogController controller;
    controller.openMm9RudeDialogue(context, 53, 0);
    REQUIRE_EQ(dialog.actions.size(), 2);

    const OpenYAMM::Game::GameplayDialogController::Result result =
        controller.executeActiveDialogAction(context);
    CHECK_FALSE(result.shouldCloseActiveDialog);
    CHECK_FALSE(result.shouldOpenPendingEventDialog);
    CHECK_FALSE(eventRuntimeState.dialogueState.suspendedMm9RudeDialogue.has_value());
    CHECK(dialog.presentation == OpenYAMM::Game::EventDialogPresentation::Mm9Rude);
    CHECK_EQ(dialog.sourceId, 53);
    CHECK_EQ(uiController.statusBar().eventText, "MM9 shop 53 has no mounted service definition.");
}

TEST_CASE("MM9 RUDE temple and training services open shared house venues and restore RUDE")
{
    struct ServiceCase
    {
        int32_t opcode = 0;
        uint32_t sourceId = 0;
        const char *pType = nullptr;
        bool canHeal = false;
        bool canDonate = false;
    };
    const std::array<ServiceCase, 3> serviceCases = {{
        {.opcode = -3, .sourceId = 62, .pType = "Training"},
        {.opcode = -8, .sourceId = 58, .pType = "Temple", .canHeal = true, .canDonate = true},
        {.opcode = -16, .sourceId = 58, .pType = "Temple", .canHeal = true, .canDonate = true},
    }};

    for (const ServiceCase &serviceCase : serviceCases)
    {
        CAPTURE(serviceCase.opcode);
        OpenYAMM::Game::Mm9RudeDialogueTable rudeTable;
        REQUIRE(rudeTable.loadDialogueText(
            "NPC" + std::to_string(serviceCase.sourceId) + ".rude",
            rudeRow(
                serviceCase.sourceId,
                serviceCase.sourceId,
                1,
                "Use the service.",
                "Certainly.",
                serviceCase.opcode)
                + rudeRow(
                    serviceCase.sourceId,
                    serviceCase.sourceId,
                    2,
                    "Goodbye.",
                    "blank",
                    -1)));

        std::vector<std::string> venueRow(16);
        venueRow[0] = std::to_string(30000 + serviceCase.sourceId);
        venueRow[1] = "mm9";
        venueRow[2] = std::to_string(serviceCase.sourceId);
        venueRow[3] = "mm9:service/" + std::to_string(serviceCase.sourceId);
        venueRow[4] = serviceCase.pType;
        venueRow[5] = "Sturmford";
        venueRow[6] = serviceCase.pType;
        venueRow[7] = "1.2";
        venueRow[8] = "0";
        venueRow[9] = "0";
        venueRow[10] = serviceCase.canHeal ? "1" : "0";
        venueRow[11] = serviceCase.canDonate ? "1" : "0";
        venueRow[12] = "0";
        venueRow[13] = "LiveGameplay";
        venueRow[14] = "RudeQuestKey";
        venueRow[15] = "1";
        OpenYAMM::Game::HouseTable houseTable;
        std::string serviceError;
        REQUIRE(houseTable.appendServiceVenueRows(
            {venueRow},
            {{venueRow[0], "mm9", venueRow[2], "1"}},
            serviceError));

        OpenYAMM::Game::Party party;
        OpenYAMM::Game::GameplayUiController uiController;
        OpenYAMM::Game::EventRuntimeState eventRuntimeState;
        OpenYAMM::Game::EventDialogContent dialog = {};
        size_t selectionIndex = 0;
        Mm9RudeExitTestWorldRuntime worldRuntime;
        worldRuntime.bindParty(&party);
        OpenYAMM::Game::MapDeltaActor actor = {};
        actor.mm9SourceObjectIndex = serviceCase.sourceId;
        worldRuntime.mapDelta.actors.push_back(actor);
        OpenYAMM::Game::GameplayDialogController::Context context = {
            .uiController = uiController,
            .eventRuntimeState = eventRuntimeState,
            .activeEventDialog = dialog,
            .selectionIndex = selectionIndex,
            .pParty = &party,
            .pWorldRuntime = &worldRuntime,
            .pHouseTable = &houseTable,
            .pMm9RudeDialogueTable = &rudeTable,
            .dialogueHudActive = true,
        };
        const OpenYAMM::Game::GameplayDialogController controller;
        controller.openMm9RudeDialogue(context, serviceCase.sourceId, 0);
        const OpenYAMM::Game::GameplayDialogController::Result openResult =
            controller.executeActiveDialogAction(context);
        CHECK(openResult.shouldOpenPendingEventDialog);
        REQUIRE(eventRuntimeState.pendingDialogueContext.has_value());
        CHECK_EQ(eventRuntimeState.pendingDialogueContext->sourceId, 30000 + serviceCase.sourceId);
        REQUIRE(eventRuntimeState.dialogueState.suspendedMm9RudeDialogue.has_value());

        dialog = {};
        dialog.isActive = true;
        dialog.isHouseDialog = true;
        dialog.sourceId = 30000 + serviceCase.sourceId;
        dialog.scenePolicy = OpenYAMM::Game::DialogueScenePolicy::LiveGameplay;
        eventRuntimeState.pendingDialogueContext.reset();
        const OpenYAMM::Game::GameplayDialogController::CloseDialogRequestResult closeResult =
            controller.handleDialogueCloseRequest(context);
        CHECK_FALSE(closeResult.shouldCloseActiveDialog);
        CHECK(dialog.presentation == OpenYAMM::Game::EventDialogPresentation::Mm9Rude);
        CHECK_EQ(dialog.sourceId, serviceCase.sourceId);
    }
}

TEST_CASE("MM9 RUDE terminal topics close without displaying placeholder responses")
{
    OpenYAMM::Game::Mm9RudeDialogueTable table;
    REQUIRE(table.loadDialogueText(
        "NPC436.rude",
        rudeRow(436, 436, 1, "Goodbye, Grandpa.", "asdf", -1)));

    OpenYAMM::Game::Party party;
    OpenYAMM::Game::GameplayUiController uiController;
    OpenYAMM::Game::EventRuntimeState eventRuntimeState;
    OpenYAMM::Game::EventDialogContent dialog = {};
    dialog.isActive = true;
    dialog.sourceId = 436;
    dialog.dialogueNodeId = 436;
    dialog.presentation = OpenYAMM::Game::EventDialogPresentation::Mm9Rude;
    dialog.actions.push_back({
        .kind = OpenYAMM::Game::EventDialogActionKind::Mm9RudeTopic,
        .id = 0,
        .label = "Goodbye, Grandpa.",
    });
    size_t selectionIndex = 0;
    OpenYAMM::Game::GameplayDialogController::Context context = {
        .uiController = uiController,
        .eventRuntimeState = eventRuntimeState,
        .activeEventDialog = dialog,
        .selectionIndex = selectionIndex,
        .pParty = &party,
        .pMm9RudeDialogueTable = &table,
    };

    const OpenYAMM::Game::GameplayDialogController controller;
    const OpenYAMM::Game::GameplayDialogController::Result result =
        controller.executeActiveDialogAction(context);

    CHECK(result.shouldCloseActiveDialog);
    CHECK(dialog.lines.empty());
}

TEST_CASE("MM9 RUDE node zero remains a source-directed node transition")
{
    OpenYAMM::Game::Mm9RudeDialogueTable table;
    REQUIRE(table.loadDialogueText(
        "NPC402.rude",
        rudeRow(402, 401, 1, "We'd like to become Experts in Learning.", "If qualified.", 0)));

    OpenYAMM::Game::Party party;
    const std::vector<const OpenYAMM::Game::Mm9RudeRow *> rows = table.visibleRows(402, 401, party);
    REQUIRE(rows.size() == 1);
    const OpenYAMM::Game::Mm9RudeSelection selection = OpenYAMM::Game::selectMm9RudeRow(*rows[0]);
    CHECK(selection.kind == OpenYAMM::Game::Mm9RudeSelectionKind::GotoNode);
    CHECK(selection.next == 0);
}

TEST_CASE("MM9 RUDE rejects keys outside its declared namespace")
{
    OpenYAMM::Game::Mm9RudeDialogueTable table;
    CHECK_FALSE(table.loadDialogueText(
        "NPC1.rude",
        rudeRow(1, 1, 1, "Invalid", "Invalid", -1, 10000)));
    CHECK_FALSE(table.errors().empty());
}

TEST_CASE("MM9 world RUDE assets load as one validated package")
{
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assetFileSystem.initialize(
        sourceRoot,
        sourceRoot / "assets_dev",
        OpenYAMM::Engine::AssetScaleTier::X1,
        "mm9"));

    OpenYAMM::Game::Mm9RudeDialogueTable table;
    REQUIRE(table.load(assetFileSystem));
    CHECK(table.errors().empty());
    CHECK(table.hasDialogue(436));
    CHECK(table.hasDialogue(101));
    CHECK(table.hasDialogue(204));
    CHECK(table.hasDialogue(206));
    CHECK(table.npcName(436) == "Old Man");
}

TEST_CASE("Every source MM9 RUDE skill-training row has a core trainer mapping")
{
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assetFileSystem.initialize(
        sourceRoot,
        sourceRoot / "assets_dev",
        OpenYAMM::Engine::AssetScaleTier::X1,
        "mm9"));

    OpenYAMM::Game::Mm9RudeDialogueTable table;
    REQUIRE(table.load(assetFileSystem));

    size_t trainerRowCount = 0;
    for (uint32_t rudeId = 1; rudeId <= 999; ++rudeId)
    {
        for (const OpenYAMM::Game::Mm9RudeRow &row : table.rows(rudeId))
        {
            if (row.next != -4)
            {
                continue;
            }

            ++trainerRowCount;
            CHECK_MESSAGE(
                OpenYAMM::Game::resolveMm9RudeSkillTrainerTopic(row).has_value(),
                "Missing trainer mapping for RUDE ", rudeId, " source line ", row.sourceLine);
        }
    }
    CHECK(trainerRowCount == 115);
}

TEST_CASE("MM9 world data loads transitions trainers and source monster gameplay")
{
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assetFileSystem.initialize(
        sourceRoot,
        sourceRoot / "assets_dev",
        OpenYAMM::Engine::AssetScaleTier::X1,
        "mm9"));

    OpenYAMM::Game::GameDataLoader dataLoader = {};
    REQUIRE(dataLoader.loadCommonForGameplay(assetFileSystem));

    const OpenYAMM::Game::HouseTable &houseTable = dataLoader.getHouseTable();
    size_t reachableShopRowCount = 0;
    std::unordered_set<uint32_t> reachableShopIds;
    for (uint32_t rudeId = 1; rudeId <= 999; ++rudeId)
    {
        for (const OpenYAMM::Game::Mm9RudeRow &row : dataLoader.getMm9RudeDialogueTable().rows(rudeId))
        {
            if (row.next != -2)
            {
                continue;
            }
            ++reachableShopRowCount;
            reachableShopIds.insert(rudeId);
            CHECK_MESSAGE(
                houseTable.resolvePackageSourceVendorId("mm9", rudeId) != nullptr,
                "Missing MM9 vendor alias for RUDE ", rudeId, " source line ", row.sourceLine);
        }
    }
    CHECK_EQ(reachableShopRowCount, 48);
    CHECK_EQ(reachableShopIds.size(), 47);
    size_t reachableTrainingRowCount = 0;
    size_t reachableHealingRowCount = 0;
    size_t reachableDonationRowCount = 0;
    std::unordered_set<uint32_t> reachableServiceIds;
    for (uint32_t rudeId = 1; rudeId <= 999; ++rudeId)
    {
        for (const OpenYAMM::Game::Mm9RudeRow &row : dataLoader.getMm9RudeDialogueTable().rows(rudeId))
        {
            if (row.next != -3 && row.next != -8 && row.next != -16)
            {
                continue;
            }
            reachableTrainingRowCount += row.next == -3 ? 1 : 0;
            reachableHealingRowCount += row.next == -8 ? 1 : 0;
            reachableDonationRowCount += row.next == -16 ? 1 : 0;
            reachableServiceIds.insert(rudeId);
            CHECK_MESSAGE(
                houseTable.resolvePackageSourceServiceId("mm9", rudeId) != nullptr,
                "Missing MM9 service venue alias for RUDE ", rudeId, " source line ", row.sourceLine);
        }
    }
    CHECK_EQ(reachableTrainingRowCount, 8);
    CHECK_EQ(reachableHealingRowCount, 8);
    CHECK_EQ(reachableDonationRowCount, 7);
    CHECK_EQ(reachableServiceIds.size(), 16);
    size_t mm9VendorCount = 0;
    size_t mm9VendorStockRowCount = 0;
    std::unordered_set<uint32_t> stockItemIdsWithoutMountedIcons;
    for (const auto &[houseId, houseEntry] : houseTable.entries())
    {
        (void)houseId;
        if (houseEntry.vendorStockProfile != OpenYAMM::Game::VendorStockProfile::None)
        {
            ++mm9VendorCount;

            const auto inspectPages = [&](const std::vector<OpenYAMM::Game::HouseEntry::DeterministicStockPage> &pages)
            {
                for (const OpenYAMM::Game::HouseEntry::DeterministicStockPage &page : pages)
                {
                    for (const OpenYAMM::Game::HouseEntry::DeterministicStockItem &stockItem : page.items)
                    {
                        ++mm9VendorStockRowCount;
                        const OpenYAMM::Game::ItemDefinition *pItem = dataLoader.getItemTable().get(stockItem.itemId);
                        if (pItem == nullptr || pItem->iconVirtualPath.empty())
                        {
                            stockItemIdsWithoutMountedIcons.insert(stockItem.itemId);
                        }
                    }
                }
            };
            inspectPages(houseEntry.deterministicStandardStockPages);
            inspectPages(houseEntry.deterministicSpecialStockPages);
        }
    }
    CHECK_EQ(mm9VendorCount, 48);
    CHECK_EQ(mm9VendorStockRowCount, 3816);
    CHECK(stockItemIdsWithoutMountedIcons.empty());
    const OpenYAMM::Game::HouseEntry *pSturmfordWeaponVendor =
        houseTable.resolvePackageSourceVendorId("mm9", 53);
    REQUIRE(pSturmfordWeaponVendor != nullptr);
    CHECK_EQ(pSturmfordWeaponVendor->id, 30053);
    CHECK(pSturmfordWeaponVendor->dialogueScenePolicy == OpenYAMM::Game::DialogueScenePolicy::LiveGameplay);
    CHECK(pSturmfordWeaponVendor->videoName.empty());
    CHECK_EQ(pSturmfordWeaponVendor->roomSoundId, 0);
    CHECK_EQ(pSturmfordWeaponVendor->houseSoundBaseId, 0);
    CHECK(pSturmfordWeaponVendor->vendorStockProfile == OpenYAMM::Game::VendorStockProfile::Weapon);
    const std::vector<OpenYAMM::Game::HouseActionOption> vendorRootActions =
        OpenYAMM::Game::buildHouseActionOptions(
            *pSturmfordWeaponVendor,
            nullptr,
            nullptr,
            nullptr,
            0.0f,
            OpenYAMM::Game::DialogueMenuId::None);
    REQUIRE_EQ(vendorRootActions.size(), 3);
    CHECK_EQ(vendorRootActions[0].label, "Buy Standard");
    CHECK_EQ(vendorRootActions[1].label, "Buy Special");
    CHECK_EQ(vendorRootActions[2].label, "Display Equipment");
    CHECK_EQ(pSturmfordWeaponVendor->deterministicStockGenerationVersion, 1);

    const OpenYAMM::Game::HouseEntry *pSturmfordTraining =
        houseTable.resolvePackageSourceServiceId("mm9", 62);
    REQUIRE(pSturmfordTraining != nullptr);
    CHECK(OpenYAMM::Game::resolveHouseServiceType(*pSturmfordTraining)
        == OpenYAMM::Game::HouseServiceType::TrainingHall);
    CHECK_EQ(pSturmfordTraining->trainingMaxLevel, 0);
    CHECK_EQ(pSturmfordTraining->priceMultiplier, doctest::Approx(1.0f));
    CHECK_FALSE(pSturmfordTraining->serviceCanLearnSkills);
    const std::vector<OpenYAMM::Game::HouseActionOption> trainingActions =
        OpenYAMM::Game::buildHouseActionOptions(
            *pSturmfordTraining,
            nullptr,
            nullptr,
            nullptr,
            0.0f,
            OpenYAMM::Game::DialogueMenuId::None);
    REQUIRE_EQ(trainingActions.size(), 1);
    CHECK_EQ(trainingActions[0].id, OpenYAMM::Game::HouseActionId::TrainingTrainActiveMember);

    const OpenYAMM::Game::HouseEntry *pSturmfordTemple =
        houseTable.resolvePackageSourceServiceId("mm9", 58);
    REQUIRE(pSturmfordTemple != nullptr);
    CHECK(OpenYAMM::Game::resolveHouseServiceType(*pSturmfordTemple)
        == OpenYAMM::Game::HouseServiceType::Temple);
    CHECK_EQ(pSturmfordTemple->priceMultiplier, doctest::Approx(1.2f));
    CHECK_EQ(pSturmfordTemple->templeHealingTier, doctest::Approx(0.0f));
    CHECK(pSturmfordTemple->templeCanHeal);
    CHECK(pSturmfordTemple->templeCanDonate);
    CHECK_FALSE(pSturmfordTemple->serviceCanLearnSkills);
    const std::vector<OpenYAMM::Game::HouseActionOption> templeActions =
        OpenYAMM::Game::buildHouseActionOptions(
            *pSturmfordTemple,
            nullptr,
            nullptr,
            nullptr,
            0.0f,
            OpenYAMM::Game::DialogueMenuId::None);
    REQUIRE_EQ(templeActions.size(), 2);
    CHECK_EQ(templeActions[0].id, OpenYAMM::Game::HouseActionId::TempleHeal);
    CHECK_EQ(templeActions[1].id, OpenYAMM::Game::HouseActionId::TempleDonate);

    const OpenYAMM::Game::HouseEntry *pMidwife =
        houseTable.resolvePackageSourceServiceId("mm9", 241);
    REQUIRE(pMidwife != nullptr);
    CHECK(pMidwife->templeCanHeal);
    CHECK_FALSE(pMidwife->templeCanDonate);
    const std::vector<OpenYAMM::Game::HouseActionOption> midwifeActions =
        OpenYAMM::Game::buildHouseActionOptions(
            *pMidwife,
            nullptr,
            nullptr,
            nullptr,
            0.0f,
            OpenYAMM::Game::DialogueMenuId::None);
    REQUIRE_EQ(midwifeActions.size(), 1);
    CHECK_EQ(midwifeActions[0].id, OpenYAMM::Game::HouseActionId::TempleHeal);

    const auto libraryIt = std::find_if(
        houseTable.entries().begin(),
        houseTable.entries().end(),
        [](const std::pair<const uint32_t, OpenYAMM::Game::HouseEntry> &entry)
        {
            return entry.second.vendorStockProfile == OpenYAMM::Game::VendorStockProfile::Mm9Library;
        });
    REQUIRE(libraryIt != houseTable.entries().end());
    const std::vector<OpenYAMM::Game::HouseActionOption> libraryEquipmentActions =
        OpenYAMM::Game::buildHouseActionOptions(
            libraryIt->second,
            nullptr,
            nullptr,
            nullptr,
            0.0f,
            OpenYAMM::Game::DialogueMenuId::ShopEquipment);
    REQUIRE_EQ(libraryEquipmentActions.size(), 1);
    CHECK_EQ(libraryEquipmentActions[0].label, "Sell");
    CHECK_FALSE(OpenYAMM::Game::HouseServiceRuntime::supportsIdentify(libraryIt->second));

    OpenYAMM::Game::Party vendorParty;
    const std::vector<OpenYAMM::Game::InventoryItem> firstStock =
        OpenYAMM::Game::HouseServiceRuntime::ensureStock(
            vendorParty,
            dataLoader.getItemTable(),
            dataLoader.getStandardItemEnchantTable(),
            dataLoader.getSpecialItemEnchantTable(),
            *pSturmfordWeaponVendor,
            0.0f,
            OpenYAMM::Game::HouseStockMode::ShopStandard);
    REQUIRE_EQ(firstStock.size(), 6);
    CHECK(std::all_of(
        firstStock.begin(),
        firstStock.end(),
        [](const OpenYAMM::Game::InventoryItem &item)
        {
            return item.objectDescriptionId != 0;
        }));
    const std::vector<OpenYAMM::Game::InventoryItem> firstSpecialStock =
        OpenYAMM::Game::HouseServiceRuntime::ensureStock(
            vendorParty,
            dataLoader.getItemTable(),
            dataLoader.getStandardItemEnchantTable(),
            dataLoader.getSpecialItemEnchantTable(),
            *pSturmfordWeaponVendor,
            0.0f,
            OpenYAMM::Game::HouseStockMode::ShopSpecial);
    REQUIRE_EQ(firstSpecialStock.size(), 6);
    REQUIRE_FALSE(pSturmfordWeaponVendor->deterministicSpecialStockPages.empty());
    for (size_t slotIndex = 0; slotIndex < firstSpecialStock.size(); ++slotIndex)
    {
        const OpenYAMM::Game::HouseEntry::DeterministicStockItem &authored =
            pSturmfordWeaponVendor->deterministicSpecialStockPages[0].items[slotIndex];
        CHECK_EQ(firstSpecialStock[slotIndex].objectDescriptionId, authored.itemId);
        CHECK_EQ(firstSpecialStock[slotIndex].standardEnchantId, authored.standardEnchantId);
        CHECK_EQ(firstSpecialStock[slotIndex].specialEnchantId, authored.specialEnchantId);
    }
    CHECK(OpenYAMM::Game::HouseServiceRuntime::canSellItemToHouse(
        dataLoader.getItemTable(),
        *pSturmfordWeaponVendor,
        firstStock[0]));
    OpenYAMM::Game::Party libraryParty;
    const std::vector<OpenYAMM::Game::InventoryItem> libraryStock =
        OpenYAMM::Game::HouseServiceRuntime::ensureStock(
            libraryParty,
            dataLoader.getItemTable(),
            dataLoader.getStandardItemEnchantTable(),
            dataLoader.getSpecialItemEnchantTable(),
            libraryIt->second,
            0.0f,
            OpenYAMM::Game::HouseStockMode::ShopStandard);
    REQUIRE_EQ(libraryStock.size(), 12);
    CHECK(OpenYAMM::Game::HouseServiceRuntime::canSellItemToHouse(
        dataLoader.getItemTable(),
        libraryIt->second,
        libraryStock[0]));
    CHECK_FALSE(OpenYAMM::Game::HouseServiceRuntime::canSellItemToHouse(
        dataLoader.getItemTable(),
        *pSturmfordWeaponVendor,
        libraryStock[0]));

    OpenYAMM::Game::Party migrationParty;
    OpenYAMM::Game::HouseServiceRuntime::ensureStock(
        migrationParty,
        dataLoader.getItemTable(),
        dataLoader.getStandardItemEnchantTable(),
        dataLoader.getSpecialItemEnchantTable(),
        *pSturmfordWeaponVendor,
        0.0f,
        OpenYAMM::Game::HouseStockMode::ShopStandard);
    OpenYAMM::Game::Party::HouseStockState *pMigrationState = migrationParty.houseStockState(30053);
    REQUIRE(pMigrationState != nullptr);
    pMigrationState->generationVersion = 99;
    pMigrationState->nextRefreshGameMinutes = 100.0f;
    OpenYAMM::Game::HouseServiceRuntime::ensureStock(
        migrationParty,
        dataLoader.getItemTable(),
        dataLoader.getStandardItemEnchantTable(),
        dataLoader.getSpecialItemEnchantTable(),
        *pSturmfordWeaponVendor,
        99.0f,
        OpenYAMM::Game::HouseStockMode::ShopStandard);
    CHECK_EQ(pMigrationState->generationVersion, 99);
    OpenYAMM::Game::HouseServiceRuntime::ensureStock(
        migrationParty,
        dataLoader.getItemTable(),
        dataLoader.getStandardItemEnchantTable(),
        dataLoader.getSpecialItemEnchantTable(),
        *pSturmfordWeaponVendor,
        100.0f,
        OpenYAMM::Game::HouseStockMode::ShopStandard);
    CHECK_EQ(pMigrationState->generationVersion, 1);
    const std::vector<OpenYAMM::Game::InventoryItem> unchangedStock =
        OpenYAMM::Game::HouseServiceRuntime::ensureStock(
            vendorParty,
            dataLoader.getItemTable(),
            dataLoader.getStandardItemEnchantTable(),
            dataLoader.getSpecialItemEnchantTable(),
            *pSturmfordWeaponVendor,
            14.0f * 24.0f * 60.0f - 1.0f,
            OpenYAMM::Game::HouseStockMode::ShopStandard);
    REQUIRE_EQ(unchangedStock.size(), firstStock.size());
    for (size_t index = 0; index < firstStock.size(); ++index)
    {
        CHECK_EQ(unchangedStock[index].objectDescriptionId, firstStock[index].objectDescriptionId);
        CHECK_EQ(unchangedStock[index].specialEnchantId, firstStock[index].specialEnchantId);
    }
    const std::vector<OpenYAMM::Game::InventoryItem> secondStock =
        OpenYAMM::Game::HouseServiceRuntime::ensureStock(
            vendorParty,
            dataLoader.getItemTable(),
            dataLoader.getStandardItemEnchantTable(),
            dataLoader.getSpecialItemEnchantTable(),
            *pSturmfordWeaponVendor,
            14.0f * 24.0f * 60.0f,
            OpenYAMM::Game::HouseStockMode::ShopStandard);
    REQUIRE_EQ(secondStock.size(), firstStock.size());
    CHECK(std::any_of(
        secondStock.begin(),
        secondStock.end(),
        [&firstStock](const OpenYAMM::Game::InventoryItem &item)
        {
            return std::none_of(
                firstStock.begin(),
                firstStock.end(),
                [&item](const OpenYAMM::Game::InventoryItem &firstItem)
                {
                    return firstItem.objectDescriptionId == item.objectDescriptionId
                        && firstItem.specialEnchantId == item.specialEnchantId;
                });
        }));

    const OpenYAMM::Game::HouseEntry *pFrosgardWeaponVendor =
        houseTable.resolvePackageSourceVendorId("mm9", 200);
    REQUIRE(pFrosgardWeaponVendor != nullptr);
    CHECK_EQ(pFrosgardWeaponVendor->stockRefreshDays, 56);
    OpenYAMM::Game::Party frosgardParty;
    OpenYAMM::Game::HouseServiceRuntime::ensureStock(
        frosgardParty,
        dataLoader.getItemTable(),
        dataLoader.getStandardItemEnchantTable(),
        dataLoader.getSpecialItemEnchantTable(),
        *pFrosgardWeaponVendor,
        0.0f,
        OpenYAMM::Game::HouseStockMode::ShopStandard);
    OpenYAMM::Game::Party::HouseStockState *pFrosgardStockState = frosgardParty.houseStockState(30200);
    REQUIRE(pFrosgardStockState != nullptr);
    CHECK_EQ(pFrosgardStockState->refreshSequence, 1);
    OpenYAMM::Game::HouseServiceRuntime::ensureStock(
        frosgardParty,
        dataLoader.getItemTable(),
        dataLoader.getStandardItemEnchantTable(),
        dataLoader.getSpecialItemEnchantTable(),
        *pFrosgardWeaponVendor,
        55.0f * 24.0f * 60.0f,
        OpenYAMM::Game::HouseStockMode::ShopStandard);
    CHECK_EQ(pFrosgardStockState->refreshSequence, 1);
    OpenYAMM::Game::HouseServiceRuntime::ensureStock(
        frosgardParty,
        dataLoader.getItemTable(),
        dataLoader.getStandardItemEnchantTable(),
        dataLoader.getSpecialItemEnchantTable(),
        *pFrosgardWeaponVendor,
        56.0f * 24.0f * 60.0f,
        OpenYAMM::Game::HouseStockMode::ShopStandard);
    CHECK_EQ(pFrosgardStockState->refreshSequence, 2);

    OpenYAMM::Game::PartySeed buyerSeed = OpenYAMM::Tests::createSpellRegressionPartySeed();
    buyerSeed.gold = 1000000;
    OpenYAMM::Game::Party buyerParty;
    buyerParty.seed(buyerSeed);
    const std::vector<OpenYAMM::Game::InventoryItem> &buyerStock =
        OpenYAMM::Game::HouseServiceRuntime::ensureStock(
            buyerParty,
            dataLoader.getItemTable(),
            dataLoader.getStandardItemEnchantTable(),
            dataLoader.getSpecialItemEnchantTable(),
            *pSturmfordWeaponVendor,
            0.0f,
            OpenYAMM::Game::HouseStockMode::ShopStandard);
    REQUIRE_EQ(buyerStock.size(), 6);
    const uint32_t boughtItemId = buyerStock[0].objectDescriptionId;
    std::string buyStatus;
    OpenYAMM::Game::HouseServiceRuntime::ShopItemServiceResult buyResult =
        OpenYAMM::Game::HouseServiceRuntime::ShopItemServiceResult::None;
    REQUIRE(OpenYAMM::Game::HouseServiceRuntime::tryBuyStockItem(
        buyerParty,
        dataLoader.getItemTable(),
        dataLoader.getStandardItemEnchantTable(),
        dataLoader.getSpecialItemEnchantTable(),
        *pSturmfordWeaponVendor,
        0.0f,
        OpenYAMM::Game::HouseStockMode::ShopStandard,
        0,
        buyStatus,
        &buyResult));
    CHECK(buyResult == OpenYAMM::Game::HouseServiceRuntime::ShopItemServiceResult::Success);
    const OpenYAMM::Game::Party::HouseStockState *pBuyerStockState = buyerParty.houseStockState(30053);
    REQUIRE(pBuyerStockState != nullptr);
    CHECK_EQ(pBuyerStockState->standardStock[0].objectDescriptionId, 0);
    const std::vector<OpenYAMM::Game::InventoryItem> &soldOutStock =
        OpenYAMM::Game::HouseServiceRuntime::ensureStock(
            buyerParty,
            dataLoader.getItemTable(),
            dataLoader.getStandardItemEnchantTable(),
            dataLoader.getSpecialItemEnchantTable(),
            *pSturmfordWeaponVendor,
            14.0f * 24.0f * 60.0f - 1.0f,
            OpenYAMM::Game::HouseStockMode::ShopStandard);
    CHECK_EQ(soldOutStock[0].objectDescriptionId, 0);
    const std::vector<OpenYAMM::Game::InventoryItem> &restockedBuyerStock =
        OpenYAMM::Game::HouseServiceRuntime::ensureStock(
            buyerParty,
            dataLoader.getItemTable(),
            dataLoader.getStandardItemEnchantTable(),
            dataLoader.getSpecialItemEnchantTable(),
            *pSturmfordWeaponVendor,
            14.0f * 24.0f * 60.0f,
            OpenYAMM::Game::HouseStockMode::ShopStandard);
    CHECK_NE(restockedBuyerStock[0].objectDescriptionId, 0);
    REQUIRE(buyerParty.activeMember() != nullptr);
    CHECK(std::any_of(
        buyerParty.activeMember()->inventory.begin(),
        buyerParty.activeMember()->inventory.end(),
        [boughtItemId](const OpenYAMM::Game::InventoryItem &item)
        {
            return item.objectDescriptionId == boughtItemId;
        }));

    const std::string runtimeStockTable = loadSourceText(
        "assets_dev/worlds/mm9/data_tables/vendor_stock.txt");
    CHECK(runtimeStockTable.find("quality") == std::string::npos);
    CHECK(runtimeStockTable.find("source_q") == std::string::npos);

    OpenYAMM::Game::GameSaveData vendorSave = {};
    vendorSave.party = vendorParty.snapshot();
    vendorSave.hasOutdoorRuntimeState = true;
    vendorSave.outdoorWorld.eventRuntimeState = OpenYAMM::Game::EventRuntimeState{};
    vendorSave.outdoorWorld.eventRuntimeState->dialogueState.suspendedMm9RudeDialogue =
        OpenYAMM::Game::EventRuntimeState::SuspendedMm9RudeDialogue{
            .rudeId = 53,
            .nodeId = 53,
            .sourceActorIndex = 9,
            .response = "Certainly.",
            .selectionIndex = 1,
        };
    vendorSave.requiredContentPackages = OpenYAMM::Game::collectRequiredContentPackages(
        vendorSave,
        dataLoader.getItemTable(),
        dataLoader.getHouseTable(),
        dataLoader.getLoadedContentPackageSchemas());
    REQUIRE(vendorSave.requiredContentPackages.contains("mm9"));
    std::string vendorPackageError;
    CHECK(OpenYAMM::Game::validateRequiredContentPackages(
        vendorSave,
        dataLoader.getItemTable(),
        dataLoader.getHouseTable(),
        dataLoader.getLoadedContentPackageSchemas(),
        vendorPackageError));
    OpenYAMM::Game::HouseTable missingVendorHouseTable;
    CHECK_FALSE(OpenYAMM::Game::validateRequiredContentPackages(
        vendorSave,
        dataLoader.getItemTable(),
        missingVendorHouseTable,
        dataLoader.getLoadedContentPackageSchemas(),
        vendorPackageError));
    CHECK(vendorPackageError.find("missing vendor definition 30053") != std::string::npos);
    const std::filesystem::path vendorSavePath =
        std::filesystem::temp_directory_path() / "openyamm_mm9_vendor_roundtrip.oysav";
    std::string vendorSaveError;
    REQUIRE(OpenYAMM::Game::saveGameDataToPath(vendorSavePath, vendorSave, vendorSaveError));
    const std::optional<OpenYAMM::Game::GameSaveData> loadedVendorSave =
        OpenYAMM::Game::loadGameDataFromPath(vendorSavePath, vendorSaveError);
    std::filesystem::remove(vendorSavePath);
    REQUIRE(loadedVendorSave.has_value());
    const auto loadedStockIt = std::find_if(
        loadedVendorSave->party.houseStockStates.begin(),
        loadedVendorSave->party.houseStockStates.end(),
        [](const OpenYAMM::Game::Party::HouseStockState &state)
        {
            return state.houseId == 30053;
        });
    REQUIRE(loadedStockIt != loadedVendorSave->party.houseStockStates.end());
    CHECK_EQ(loadedStockIt->generationVersion, 1);
    REQUIRE_EQ(loadedStockIt->standardStock.size(), secondStock.size());
    CHECK_EQ(loadedStockIt->standardStock[0].objectDescriptionId, secondStock[0].objectDescriptionId);
    CHECK_EQ(loadedStockIt->standardStock[0].specialEnchantId, secondStock[0].specialEnchantId);
    REQUIRE(loadedVendorSave->outdoorWorld.eventRuntimeState.has_value());
    REQUIRE(loadedVendorSave->outdoorWorld.eventRuntimeState->dialogueState.suspendedMm9RudeDialogue.has_value());
    const OpenYAMM::Game::EventRuntimeState::SuspendedMm9RudeDialogue &loadedSuspended =
        *loadedVendorSave->outdoorWorld.eventRuntimeState->dialogueState.suspendedMm9RudeDialogue;
    CHECK_EQ(loadedSuspended.rudeId, 53);
    CHECK_EQ(loadedSuspended.sourceActorIndex, 9);
    CHECK_EQ(loadedSuspended.response, "Certainly.");

    const OpenYAMM::Game::Mm9MapTransitionTable &transitionTable =
        dataLoader.getMm9MapTransitionTable();
    CHECK_EQ(transitionTable.entries().size(), 104);
    const OpenYAMM::Game::Mm9MapTransition *pDarkPassageTransition =
        transitionTable.findByCanonicalId("mm9:transition/arslegardcity/147");
    REQUIRE(pDarkPassageTransition != nullptr);
    CHECK_EQ(pDarkPassageTransition->sourceStartPointName, "StartPoint0");
    CHECK_EQ(pDarkPassageTransition->resolvedStartPointName, "StartPoint");
    CHECK_EQ(pDarkPassageTransition->travelDays, -1);
    CHECK(pDarkPassageTransition->sourceDefaultTravelDays);
    CHECK(transitionTable.findByCanonicalId("mm9:transition/arslegardcity/638") == nullptr);

    const OpenYAMM::Game::Mm9SkillTrainerTable &trainerTable = dataLoader.getMm9SkillTrainerTable();
    CHECK_EQ(trainerTable.entries().size(), 115);
    const OpenYAMM::Game::Mm9SkillTrainerService *pArmsmasterExpert = trainerTable.find(390, 1);
    REQUIRE(pArmsmasterExpert != nullptr);
    CHECK(pArmsmasterExpert->mm9Skill == "Armsmaster");
    CHECK(pArmsmasterExpert->expectedRegion == "Sturmford");
    CHECK(pArmsmasterExpert->actorOwnership == "static");
    const OpenYAMM::Game::Mm9SkillTrainerService *pArmsmasterGrandmaster = trainerTable.find(39, 0);
    REQUIRE(pArmsmasterGrandmaster != nullptr);
    CHECK((pArmsmasterGrandmaster->sourceDisplayNames
        == std::vector<std::string>{"Chera Papan", "Cihu'aton Pa'pan"}));
    const OpenYAMM::Game::Mm9SkillTrainerService *pBodybuildingGrandmaster = trainerTable.find(412, 1);
    REQUIRE(pBodybuildingGrandmaster != nullptr);
    CHECK(pBodybuildingGrandmaster->expectedRegion == "Yorwick");
    CHECK(pBodybuildingGrandmaster->actorOwnership == "scheduled");

    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pTroglodyte =
        dataLoader.getMonsterTable().findStatsById(9097);
    REQUIRE(pTroglodyte != nullptr);
    CHECK_EQ(pTroglodyte->name, "Troglodyte Wren");
    CHECK_EQ(pTroglodyte->hitPoints, 95);
    CHECK_EQ(pTroglodyte->armorClass, 15);
    CHECK_EQ(pTroglodyte->experience, 689);
    // Half its MM9 RunVel (150 x 2.56): the shared AI's doubled pursuit runs at MM9's speed.
    CHECK_EQ(pTroglodyte->speed, 192);
    // Recovery 30 MM9 game seconds of 33 ms: 0.99 s (59 ticks of 1/60 s).
    CHECK_EQ(pTroglodyte->recovery, 59);
    CHECK_EQ(pTroglodyte->fireResistance, 10);
    CHECK_EQ(pTroglodyte->airResistance, 10);
    CHECK_EQ(pTroglodyte->waterResistance, 10);
    CHECK_EQ(pTroglodyte->earthResistance, 10);
    CHECK_EQ(pTroglodyte->mindResistance, 20);
    CHECK_EQ(pTroglodyte->spiritResistance, 20);
    CHECK_EQ(pTroglodyte->bodyResistance, 20);
    CHECK_EQ(pTroglodyte->spell1Name, "poison spray");

    const OpenYAMM::Game::MonsterEntry *pPresentation =
        dataLoader.getMonsterTable().findById(9097);
    REQUIRE(pPresentation != nullptr);
    CHECK_EQ(pPresentation->internalName, "MM9 Troglodyte B");

    const OpenYAMM::Game::MonsterProjectileEntry *pAxe =
        dataLoader.getMonsterProjectileTable().findByToken("MM9Axe");
    REQUIRE(pAxe != nullptr);
    CHECK_EQ(pAxe->objectId, 309);

    const OpenYAMM::Game::MonsterProjectileEntry *pSkull =
        dataLoader.getMonsterProjectileTable().findByToken("MM9Skull");
    REQUIRE(pSkull != nullptr);
    CHECK_EQ(pSkull->objectId, 6030);
    CHECK_EQ(pSkull->impactObjectId, 6031);

    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pSkullThrower =
        dataLoader.getMonsterTable().findStatsById(9185);
    REQUIRE(pSkullThrower != nullptr);
    CHECK_EQ(pSkullThrower->name, "Skull Thrower");
    CHECK_EQ(pSkullThrower->attack1MissileType, "MM9Skull");
    CHECK(pSkullThrower->attack1HasMissile);
    CHECK(pSkullThrower->attackStyle == OpenYAMM::Game::MonsterTable::MonsterAttackStyle::Ranged);

    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pLegacyTroglodyte =
        dataLoader.getMonsterTable().findStatsById(413);
    REQUIRE(pLegacyTroglodyte != nullptr);
    CHECK_EQ(pLegacyTroglodyte->name, "Troglodyte Soldier");
}

TEST_CASE("MM9 monster overlay leaves legacy monster rows unchanged")
{
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assetFileSystem.initialize(
        sourceRoot,
        sourceRoot / "assets_dev",
        OpenYAMM::Engine::AssetScaleTier::X1));

    OpenYAMM::Game::GameDataLoader dataLoader = {};
    REQUIRE(dataLoader.loadCommonForGameplay(assetFileSystem));
    CHECK(dataLoader.getMm9MapTransitionTable().entries().empty());
    CHECK(dataLoader.getMm9SkillTrainerTable().entries().empty());
    CHECK(dataLoader.getHouseTable().resolvePackageSourceVendorId("mm9", 53) == nullptr);
    CHECK(dataLoader.getHouseTable().resolvePackageSourceServiceId("mm9", 58) == nullptr);
    CHECK(std::none_of(
        dataLoader.getHouseTable().entries().begin(),
        dataLoader.getHouseTable().entries().end(),
        [](const std::pair<const uint32_t, OpenYAMM::Game::HouseEntry> &entry)
        {
            return entry.second.vendorStockProfile != OpenYAMM::Game::VendorStockProfile::None;
        }));

    const OpenYAMM::Game::MonsterTable::MonsterStatsEntry *pLegacyTroglodyte =
        dataLoader.getMonsterTable().findStatsById(413);
    REQUIRE(pLegacyTroglodyte != nullptr);
    CHECK_EQ(pLegacyTroglodyte->name, "Troglodyte Soldier");
}

TEST_CASE("MM9 world quest overlay augments the shared journal without replacing base quests")
{
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assetFileSystem.initialize(
        sourceRoot,
        sourceRoot / "assets_dev",
        OpenYAMM::Engine::AssetScaleTier::X1,
        "mm9"));

    OpenYAMM::Game::GameDataLoader dataLoader = {};
    REQUIRE(dataLoader.loadCommonForGameplay(assetFileSystem));
    const OpenYAMM::Game::ItemDefinition *pPoorSword = dataLoader.getItemTable().get(10002);
    REQUIRE(pPoorSword != nullptr);
    CHECK_EQ(pPoorSword->packageId, "mm9");
    CHECK_EQ(pPoorSword->canonicalId, "mm9:item/poor_sword");
    CHECK_EQ(pPoorSword->sourceItemId, 2u);
    CHECK_EQ(pPoorSword->value, 43);
    CHECK_EQ(pPoorSword->inventoryWidth, 1);
    CHECK_EQ(pPoorSword->inventoryHeight, 5);
    CHECK_EQ(pPoorSword->equipX, 20);
    CHECK_EQ(pPoorSword->equipY, 139);
    CHECK_EQ(pPoorSword->visualStatus, "generated_equipped_anchor_candidate");
    CHECK_FALSE(pPoorSword->iconVirtualPath.empty());
    const OpenYAMM::Game::ItemDefinition *pArmingDoublet = dataLoader.getItemTable().get(10086u);
    REQUIRE(pArmingDoublet != nullptr);
    CHECK_EQ(pArmingDoublet->visualStatus, "generated_body_variants_reviewed");
    const OpenYAMM::Game::MergedComplexItemPictureEntry *pArmingDoubletPicture =
        dataLoader.getMergedComplexItemPictureTable().get(10086u);
    REQUIRE(pArmingDoubletPicture != nullptr);
    REQUIRE_EQ(pArmingDoubletPicture->points.size(), 6);
    CHECK_EQ(pArmingDoubletPicture->points[0].x, 47);
    CHECK_EQ(pArmingDoubletPicture->points[0].y, 78);
    CHECK_EQ(pArmingDoubletPicture->points[4].x, -2);
    CHECK_EQ(pArmingDoubletPicture->points[4].y, 0);
    CHECK(assetFileSystem.exists("icons/mm9_item_10086v1.png"));
    CHECK(assetFileSystem.exists("icons/mm9_item_10086v5a.png"));
    CHECK_EQ(dataLoader.getItemTable().resolvePackageSourceItemId("mm9", 2), pPoorSword);
    const OpenYAMM::Game::ItemDefinition *pMappedHealthPotion =
        dataLoader.getItemTable().resolvePackageSourceItemId("mm9", 253);
    REQUIRE(pMappedHealthPotion != nullptr);
    CHECK_EQ(pMappedHealthPotion->itemId, 222);

    const OpenYAMM::Game::ItemDefinition *pThrowingDagger = dataLoader.getItemTable().get(10185);
    REQUIRE(pThrowingDagger != nullptr);
    CHECK_EQ(pThrowingDagger->skillGroup, "Throwing");
    CHECK(pThrowingDagger->hasContentFlag("ExtraProjectileAtGrandmaster"));
    CHECK_EQ(pThrowingDagger->contentEffect.maxHealth, 100);
    CHECK(pThrowingDagger->contentEffect.flags == std::vector<std::string>{"TripleProjectile"});

    OpenYAMM::Game::Character thrower = {};
    thrower.speed = 14;
    thrower.accuracy = 14;
    thrower.equipment.bow = pThrowingDagger->itemId;
    thrower.skills["Throwing"] = {"Throwing", 10, OpenYAMM::Game::SkillMastery::Normal};
    const OpenYAMM::Game::CharacterAttackProfile normalThrowingProfile =
        OpenYAMM::Game::GameMechanics::buildCharacterAttackProfile(
            thrower,
            &dataLoader.getItemTable(),
            &dataLoader.getSpellTable());

    thrower.skills["Throwing"].mastery = OpenYAMM::Game::SkillMastery::Expert;
    const OpenYAMM::Game::CharacterAttackProfile expertThrowingProfile =
        OpenYAMM::Game::GameMechanics::buildCharacterAttackProfile(
            thrower,
            &dataLoader.getItemTable(),
            &dataLoader.getSpellTable());

    thrower.skills["Throwing"].mastery = OpenYAMM::Game::SkillMastery::Master;
    const OpenYAMM::Game::CharacterAttackProfile masterThrowingProfile =
        OpenYAMM::Game::GameMechanics::buildCharacterAttackProfile(
            thrower,
            &dataLoader.getItemTable(),
            &dataLoader.getSpellTable());

    thrower.skills["Throwing"].mastery = OpenYAMM::Game::SkillMastery::Grandmaster;
    const OpenYAMM::Game::CharacterAttackProfile grandmasterThrowingProfile =
        OpenYAMM::Game::GameMechanics::buildCharacterAttackProfile(
            thrower,
            &dataLoader.getItemTable(),
            &dataLoader.getSpellTable());

    CHECK_EQ(expertThrowingProfile.rangedMinDamage, normalThrowingProfile.rangedMinDamage + 10);
    CHECK_EQ(masterThrowingProfile.rangedMinDamage, expertThrowingProfile.rangedMinDamage);
    CHECK_EQ(grandmasterThrowingProfile.rangedMinDamage, normalThrowingProfile.rangedMinDamage + 20);
    CHECK(normalThrowingProfile.rangedRecoverySeconds == expertThrowingProfile.rangedRecoverySeconds);
    CHECK(masterThrowingProfile.rangedRecoverySeconds < expertThrowingProfile.rangedRecoverySeconds);
    CHECK(grandmasterThrowingProfile.rangedRecoverySeconds < masterThrowingProfile.rangedRecoverySeconds);
    CHECK_EQ(normalThrowingProfile.rangedProjectileCount, 1);
    CHECK_EQ(grandmasterThrowingProfile.rangedProjectileCount, 2);

    const OpenYAMM::Game::ItemDefinition *pQuestWeapon = dataLoader.getItemTable().get(10197);
    REQUIRE(pQuestWeapon != nullptr);
    CHECK_EQ(pQuestWeapon->value, 0);
    CHECK_EQ(pQuestWeapon->equipStat, "Weapon2");
    CHECK_EQ(pQuestWeapon->skillGroup, "Mace");
    CHECK_EQ(pQuestWeapon->requiredMight, 60);
    CHECK(pQuestWeapon->hasContentFlag("Quest"));
    CHECK(pQuestWeapon->hasContentFlag("NoRandom"));
    CHECK(pQuestWeapon->hasContentFlag("NoShop"));
    CHECK_FALSE(pQuestWeapon->hasContentFlag("NoDrop"));
    CHECK(OpenYAMM::Game::ItemRuntime::canDrop(*pQuestWeapon));

    const OpenYAMM::Game::ItemDefinition *pDisarmTrapSkillBook = dataLoader.getItemTable().get(10298);
    REQUIRE(pDisarmTrapSkillBook != nullptr);
    CHECK_EQ(pDisarmTrapSkillBook->spriteIndex, 78);
    CHECK(OpenYAMM::Game::ItemRuntime::canDrop(*pDisarmTrapSkillBook));

    const OpenYAMM::Game::ItemDefinition *pBladeSkillBook = dataLoader.getItemTable().get(10285);
    REQUIRE(pBladeSkillBook != nullptr);
    CHECK_EQ(pBladeSkillBook->sourceItemId, 285);
    CHECK_EQ(pBladeSkillBook->canonicalId, "mm9:item/blade_skill");
    CHECK_EQ(pBladeSkillBook->useAction, "LearnSkill");
    CHECK_EQ(pBladeSkillBook->useTarget, "Sword|Dagger");

    const OpenYAMM::Game::ItemDefinition *pInterfaceScroll = dataLoader.getItemTable().get(10579);
    REQUIRE(pInterfaceScroll != nullptr);
    CHECK_EQ(pInterfaceScroll->spriteIndex, 20579);
    CHECK(OpenYAMM::Game::ItemRuntime::canDrop(*pInterfaceScroll));

    struct SetClassExpectation
    {
        uint32_t firstItemId = 0;
        const char *pClassRoot = nullptr;
        const char *pAllowedRole = nullptr;
        const char *pRejectedRole = nullptr;
    };

    constexpr std::array<SetClassExpectation, 4> SetClassExpectations = {{
        {10219, "Cavalier", "Champion", "Knight"},
        {10224, "Paladin", "Crusader", "Knight"},
        {10229, "Necromancer", "Lich", "Sorcerer"},
        {10234, "Cleric", "Priest", "Sorcerer"},
    }};

    for (const SetClassExpectation &expectation : SetClassExpectations)
    {
        OpenYAMM::Game::Character allowedCharacter = {};
        allowedCharacter.role = expectation.pAllowedRole;
        OpenYAMM::Game::Character rejectedCharacter = {};
        rejectedCharacter.role = expectation.pRejectedRole;

        for (uint32_t itemId = expectation.firstItemId; itemId < expectation.firstItemId + 5; ++itemId)
        {
            const OpenYAMM::Game::ItemDefinition *pSetItem = dataLoader.getItemTable().get(itemId);
            REQUIRE(pSetItem != nullptr);
            CHECK(pSetItem->allowedClassRoots == std::vector<std::string>{expectation.pClassRoot});
            CHECK(OpenYAMM::Game::ItemRuntime::characterMeetsClassRestriction(allowedCharacter, *pSetItem));
            CHECK_FALSE(OpenYAMM::Game::ItemRuntime::characterMeetsClassRestriction(rejectedCharacter, *pSetItem));
        }
    }

    for (uint32_t rawItemId = 175; rawItemId <= 238; ++rawItemId)
    {
        if (rawItemId == 177)
        {
            continue;
        }
        const OpenYAMM::Game::ItemDefinition *pUniqueItem =
            dataLoader.getItemTable().get(10000 + rawItemId);
        REQUIRE(pUniqueItem != nullptr);
        CHECK_FALSE(pUniqueItem->effectProfile.empty());
    }

    REQUIRE_EQ(dataLoader.getItemTable().setBonuses().size(), 4);
    OpenYAMM::Game::Party setParty = {};
    setParty.setItemTable(&dataLoader.getItemTable());
    setParty.seed(OpenYAMM::Tests::createSpellRegressionPartySeed());
    OpenYAMM::Game::Character &setMember = *setParty.member(0);
    setMember.equipment.mainHand = 10219;
    setMember.equipment.armor = 10220;
    setMember.equipment.helm = 10221;
    setMember.equipment.ring1 = 10222;
    setMember.equipment.offHand = 10223;
    setParty.refreshDerivedState();
    CHECK_EQ(setParty.equippedItemSetPieceCount(0, "mm9:set/prize"), 5);
    CHECK_EQ(setMember.magicalBonuses.might, 14);
    CHECK_EQ(setMember.magicalBonuses.meleeAttack, 40);
    CHECK_EQ(setMember.magicalBonuses.resistances.fire, 10);
    CHECK_EQ(setMember.itemSkillBonuses["Bodybuilding"], 10);
    CHECK_EQ(setMember.itemSkillBonuses["Dodging"], 7);
    setMember.conditions.set(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Dead));
    setParty.refreshDerivedState();
    CHECK_EQ(setParty.equippedItemSetPieceCount(0, "mm9:set/prize"), 5);
    CHECK_EQ(setMember.magicalBonuses.meleeAttack, 40);
    setMember.conditions.reset(static_cast<size_t>(OpenYAMM::Game::CharacterCondition::Dead));

    setMember.equipmentRuntime.mainHand.broken = true;
    setParty.refreshDerivedState();
    CHECK_EQ(setParty.equippedItemSetPieceCount(0, "mm9:set/prize"), 4);
    CHECK_EQ(setMember.magicalBonuses.might, 4);
    CHECK_EQ(setMember.magicalBonuses.meleeAttack, 0);
    CHECK_EQ(setMember.magicalBonuses.resistances.fire, 0);

    OpenYAMM::Game::Party weeklyParty = {};
    weeklyParty.setItemTable(&dataLoader.getItemTable());
    weeklyParty.seed(OpenYAMM::Tests::createSpellRegressionPartySeed());
    OpenYAMM::Game::Character &weeklyMember = *weeklyParty.member(0);
    weeklyMember.equipment.ring1 = 10209;
    weeklyParty.refreshDerivedState();
    const int goldBeforeWeeklyEffect = weeklyParty.gold();
    weeklyParty.advanceTimedStates(7.0f * 24.0f * 60.0f * 60.0f);
    CHECK_EQ(weeklyParty.gold(), goldBeforeWeeklyEffect + 1000);

    setMember.equipmentRuntime.mainHand.broken = false;
    setParty.refreshDerivedState();
    OpenYAMM::Game::GameSaveData contentSave = {};
    contentSave.party = setParty.snapshot();
    contentSave.requiredContentPackages = OpenYAMM::Game::collectRequiredContentPackages(
        contentSave,
        dataLoader.getItemTable(),
        dataLoader.getHouseTable(),
        dataLoader.getLoadedContentPackageSchemas());
    REQUIRE(contentSave.requiredContentPackages.contains("mm9"));
    CHECK_EQ(contentSave.requiredContentPackages.at("mm9"), 1);
    std::string contentError;
    CHECK(OpenYAMM::Game::validateRequiredContentPackages(
        contentSave,
        dataLoader.getItemTable(),
        dataLoader.getHouseTable(),
        dataLoader.getLoadedContentPackageSchemas(),
        contentError));
    CHECK_FALSE(OpenYAMM::Game::validateRequiredContentPackages(
        contentSave,
        dataLoader.getItemTable(),
        dataLoader.getHouseTable(),
        {{"engine", 1}},
        contentError));
    CHECK(contentError.find("missing content package 'mm9'") != std::string::npos);

    const std::filesystem::path contentSavePath =
        std::filesystem::temp_directory_path() / "openyamm_mm9_item_content_roundtrip.oysav";
    REQUIRE(OpenYAMM::Game::saveGameDataToPath(contentSavePath, contentSave, contentError));
    const std::optional<OpenYAMM::Game::GameSaveData> loadedContentSave =
        OpenYAMM::Game::loadGameDataFromPath(contentSavePath, contentError);
    std::filesystem::remove(contentSavePath);
    REQUIRE(loadedContentSave.has_value());
    OpenYAMM::Game::Party loadedSetParty = {};
    loadedSetParty.setItemTable(&dataLoader.getItemTable());
    loadedSetParty.restoreSnapshot(loadedContentSave->party);
    loadedSetParty.refreshDerivedState();
    REQUIRE(loadedSetParty.member(0) != nullptr);
    CHECK_EQ(loadedSetParty.member(0)->equipment.mainHand, 10219);
    CHECK_EQ(loadedSetParty.equippedItemSetPieceCount(0, "mm9:set/prize"), 5);
    CHECK_EQ(loadedSetParty.member(0)->magicalBonuses.meleeAttack, 40);

    OpenYAMM::Game::GameSaveData worldItemSave = {};
    worldItemSave.hasOutdoorRuntimeState = true;
    OpenYAMM::Game::OutdoorWorldRuntime::WorldItemState savedWorldItem = {};
    savedWorldItem.item.objectDescriptionId = 10197;
    worldItemSave.outdoorWorld.worldItems.push_back(savedWorldItem);
    const std::unordered_map<std::string, uint32_t> worldItemPackages =
        OpenYAMM::Game::collectRequiredContentPackages(
            worldItemSave,
            dataLoader.getItemTable(),
            dataLoader.getHouseTable(),
            dataLoader.getLoadedContentPackageSchemas());
    REQUIRE(worldItemPackages.contains("mm9"));
    CHECK_EQ(worldItemPackages.at("mm9"), 1);

    const OpenYAMM::Game::ReadableScrollEntry *pLichInstructions =
        dataLoader.getReadableScrollTable().get(10245);
    REQUIRE(pLichInstructions != nullptr);
    CHECK_EQ(pLichInstructions->location, "On Becoming a Lich");
    CHECK_FALSE(pLichInstructions->text.empty());

    const OpenYAMM::Game::JournalQuestTable &questTable = dataLoader.getJournalQuestTable();
    CHECK(questTable.hasQuestText(3));
    CHECK(questTable.hasQuestText(90001));

    OpenYAMM::Game::Party party = {};
    party.seed(OpenYAMM::Tests::createSpellRegressionPartySeed());
    std::vector<std::string> visibleQuests = OpenYAMM::Game::buildCurrentQuestTexts(questTable, party);
    REQUIRE_FALSE(visibleQuests.empty());
    CHECK(visibleQuests.front().starts_with("Complete your training."));

    party.setQuestBit(90473, true);
    visibleQuests = OpenYAMM::Game::buildCurrentQuestTexts(questTable, party);
    CHECK(std::any_of(
        visibleQuests.begin(),
        visibleQuests.end(),
        [](const std::string &text)
        {
            return text.starts_with("Search for anyone living on this island.");
        }));
}

TEST_CASE("Bootcamp MM9 dialogue actors retain source object and RUDE identities")
{
    OpenYAMM::Game::OutdoorSceneYmlLoader loader = {};
    std::string errorMessage;
    const std::optional<OpenYAMM::Game::OutdoorSceneData> loadedScene = loader.loadFromText(
        loadSourceText("assets_dev/worlds/mm9/maps/bootcamp.scene.yml"),
        errorMessage);
    REQUIRE_MESSAGE(loadedScene.has_value(), errorMessage.c_str());

    OpenYAMM::Game::OutdoorSceneData scene = *loadedScene;
    REQUIRE_MESSAGE(
        loader.applyOverlayFromText(
            scene,
            loadSourceText("assets_dev/worlds/mm9/maps/bootcamp_authored.scene.yml"),
            errorMessage),
        errorMessage.c_str());

    struct ExpectedBinding
    {
        int32_t rudeId;
        uint32_t sourceObjectIndex;
        uint16_t yawUnits;
        const char *pName;
    };
    constexpr std::array<ExpectedBinding, 4> ExpectedBindings = {{
        {436, 207, 0, "Old Man"},
        {101, 209, 511, "Thorkatla the Indiscreet"},
        {204, 210, 1542, "Dearbhorgaill A'Washadi"},
        {206, 211, 1021, "Fiachna A'Lanth"},
    }};

    constexpr std::array<const char *, 4> ExpectedGreetingSounds = {{
        "voices/npc/NPC_249.wav",
        "voices/NPC/NPC_101.wav",
        "voices/NPC/NPC_204.wav",
        "voices/NPC/NPC_206.wav",
    }};

    std::vector<const OpenYAMM::Game::MapDeltaActor *> dialogueActors;
    for (const OpenYAMM::Game::MapDeltaActor &actor : scene.initialState.actors)
    {
        if (actor.mm9RudeId > 0)
        {
            dialogueActors.push_back(&actor);
        }
    }

    REQUIRE(dialogueActors.size() == ExpectedBindings.size());
    for (size_t index = 0; index < ExpectedBindings.size(); ++index)
    {
        const OpenYAMM::Game::MapDeltaActor &actor = *dialogueActors[index];
        const ExpectedBinding &expected = ExpectedBindings[index];
        CHECK(actor.npcId == 0);
        CHECK(actor.mm9RudeId == expected.rudeId);
        CHECK(actor.mm9SourceObjectIndex == expected.sourceObjectIndex);
        CHECK(actor.initialYawUnits == expected.yawUnits);
        CHECK(actor.immobile);
        CHECK(actor.name == expected.pName);

        const auto greeting = std::find_if(
            scene.mm9NpcGreetings.begin(),
            scene.mm9NpcGreetings.end(),
            [&expected](const OpenYAMM::Game::OutdoorMm9NpcGreeting &entry)
            {
                return entry.sourceObjectIndex == expected.sourceObjectIndex;
            });
        REQUIRE(greeting != scene.mm9NpcGreetings.end());
        CHECK(greeting->soundName == ExpectedGreetingSounds[index]);
    }
}
