#include "doctest/doctest.h"

#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "game/data/GameDataLoader.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayDialogController.h"
#include "game/gameplay/HouseServiceRuntime.h"
#include "game/gameplay/JournalQuestRuntime.h"
#include "game/items/ItemGenerator.h"
#include "game/items/ItemRuntime.h"
#include "game/maps/IndoorSceneYml.h"
#include "game/maps/OutdoorSceneYml.h"
#include "game/maps/MapDeltaData.h"
#include "game/maps/SaveGame.h"
#include "game/mm9/Mm9RudeDialogue.h"
#include "game/mm9/Mm9SkillTrainer.h"
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

TEST_CASE("MM9 promotions open second-tier quests and name the promoters' standing topics")
{
    // dialogue/promotions.yml (the user, 2026-11-08): Fridleif's Gladiator labours no longer need the Mercenary
    // promotion (key 127), and once the labours are done (key 221) he keeps a Gladiator promotion topic.
    OpenYAMM::Game::Mm9RudeDialogueTable table;
    REQUIRE(table.loadDialogueText(
        "NPC61.rude",
        rudeRow(61, 13, 1, "We have Gladiators.", "Three labours.", 14, 127)
            + rudeRow(61, 61, 1, "News?", "None.", -1)));
    OpenYAMM::Game::Party party;
    CHECK(table.visibleRows(61, 13, party).empty());
    REQUIRE(table.loadPromotionsText(
        "promotions.yml",
        "format_version: 1\n"
        "promotions:\n"
        "  - {promotion: Gladiator, rude: 61, done_key: 221}\n"
        "waived_required_keys:\n"
        "  - {rude: 61, key: 127}\n"
        "added_rows:\n"
        "  - '61,61,5,\"Labours done.\",\"Promoted.\",999,218,0,219,0,220,0,0,0,0,26,0,0,0,0,26,0,0,0,0,0,0,0,0,0'\n"));
    CHECK(table.visibleRows(61, 13, party).size() == 1);
    // The added row: on his first page once the three hand-ins are done, gone once it is (key 26).
    CHECK(table.visibleRows(61, 61, party).size() == 1);
    party.setQuestBit(90218, true);
    party.setQuestBit(90219, true);
    party.setQuestBit(90220, true);
    REQUIRE(table.visibleRows(61, 61, party).size() == 2);
    CHECK(table.visibleRows(61, 61, party)[1]->prompt == "Labours done.");
    party.setQuestBit(90026, true);
    CHECK(table.visibleRows(61, 61, party).size() == 1);
    const OpenYAMM::Game::Mm9PromotionService *pService = table.promotionService(61);
    REQUIRE(pService != nullptr);
    CHECK(pService->promotion == "Gladiator");
    CHECK(pService->doneRawKey == 221);
    CHECK(table.promotionService(88) == nullptr);

    // A promoter without dialogue and a waiver no row needs are errors (stale data, not silently ignored).
    OpenYAMM::Game::Mm9RudeDialogueTable stale;
    REQUIRE(stale.loadDialogueText("NPC61.rude", rudeRow(61, 61, 1, "News?", "None.", -1)));
    CHECK_FALSE(stale.loadPromotionsText(
        "promotions.yml",
        "format_version: 1\n"
        "promotions:\n"
        "  - {promotion: Mage, rude: 4, done_key: 294}\n"
        "waived_required_keys:\n"
        "  - {rude: 61, key: 127}\n"));
    CHECK(stale.errors().size() == 2);
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

TEST_CASE("MM9 RUDE trainer topics list each skill, then a lesson row per party member")
{
    using OpenYAMM::Game::EventDialogActionKind;
    using OpenYAMM::Game::EventDialogChoiceMark;
    using OpenYAMM::Game::SkillMastery;

    OpenYAMM::Game::Mm9RudeDialogueTable table;
    REQUIRE(table.loadDialogueText(
        "NPC80.rude",
        rudeRowWithFields(80, 80, 1, "Expert Blade", "Are you ready?", -4, {{16, 2006}})
            + rudeRowWithFields(80, 80, 2, "Expert Spear", "Hold it so.", -4, {{16, 2007}})));
    OpenYAMM::Game::Mm9SkillTrainerTable trainerTable;
    REQUIRE(trainerTable.loadFromRows({
        {
            "CanonicalId", "RudeId", "RudeRowIndex", "SourceLine", "ChoiceSlot", "RawTrainerId", "Mm9Skill",
            "SharedSkills", "TargetMastery", "RequiredSkillRank", "RequiredGold", "RequiredRawKeys",
            "ForbiddenRawKeys", "ExpectedRegion", "SourceDisplayNames", "Npc998Hint", "ActorOwnership",
            "ActorSources", "SourceRude", "Provenance",
        },
        {
            "mm9:trainer/80/1", "80", "0", "1", "1", "2006", "Blade", "Sword|Dagger|Axe", "Expert", "4", "0", "",
            "", "Sturmford", "Katrina Vianni", "Katrina Vianni of Sturmford teaches Blade.", "static",
            "sturmfordcity.scene.yml", "NPC80.rude", "test",
        },
        {
            "mm9:trainer/80/2", "80", "1", "2", "2", "2007", "Spear", "Spear", "Expert", "4", "0", "",
            "", "Sturmford", "Katrina Vianni", "Katrina Vianni of Sturmford teaches Spear.", "static",
            "sturmfordcity.scene.yml", "NPC80.rude", "test",
        },
    }, table));

    OpenYAMM::Game::ClassSkillTable classSkillTable;
    REQUIRE(classSkillTable.loadCapsFromRows({
        {"", "Test Class"},
        {"Dagger", "G"},
        {"Sword", "G"},
        {"Axe", "B"},
        {"Spear", "G"},
    }));
    OpenYAMM::Game::NpcDialogTable npcDialogTable;

    OpenYAMM::Game::Character first = {};
    first.name = "Ari";
    first.className = "Test Class";
    first.maxHealth = 10;
    first.health = 10;
    first.skills["Dagger"] = {"Dagger", 4, SkillMastery::Normal};
    first.skills["Axe"] = {"Axe", 4, SkillMastery::Normal};
    OpenYAMM::Game::Character second = first;
    second.name = "Bryn";
    second.skills.clear();
    second.skills["Dagger"] = {"Dagger", 4, SkillMastery::Normal};
    second.skills["Spear"] = {"Spear", 4, SkillMastery::Normal};

    OpenYAMM::Game::PartySeed seed = {};
    seed.gold = 5000;
    seed.members.push_back(first);
    seed.members.push_back(second);
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
        .pMm9SkillTrainerTable = &trainerTable,
    };
    const OpenYAMM::Game::GameplayDialogController controller;
    controller.openMm9RudeDialogue(context, 80);

    REQUIRE(dialog.actions.size() == 2);
    CHECK(dialog.actions[0].label == "Expert Blade");

    // The skills, each with how many members can take it now: nobody knows Sword, both Dagger, Axe is capped.
    selectionIndex = 0;
    controller.executeActiveDialogAction(context);
    REQUIRE(dialog.actions.size() == 4);
    CHECK(dialog.echo == "Expert Blade");
    CHECK(dialog.actions[0].kind == EventDialogActionKind::Mm9RudeSkillTrainerSkill);
    CHECK(dialog.actions[0].label == "Expert Sword");
    CHECK(dialog.actions[0].choiceMark == EventDialogChoiceMark::Locked);
    CHECK(dialog.actions[1].label == "Expert Dagger");
    CHECK(dialog.actions[1].choiceTag == "2 of 2 can learn");
    CHECK(dialog.actions[2].choiceMark == EventDialogChoiceMark::Locked);
    CHECK(dialog.actions[3].kind == EventDialogActionKind::Mm9RudeSkillTrainerBack);

    // Axe: one row per member, each saying why it cannot be taken; Back returns to the skills.
    selectionIndex = 2;
    controller.executeActiveDialogAction(context);
    REQUIRE(dialog.actions.size() == 3);
    CHECK(dialog.actions[0].label == "Ari: This skill level can not be learned by the Test Class class.");
    CHECK(dialog.actions[0].choiceMark == EventDialogChoiceMark::Locked);
    CHECK(dialog.actions[1].memberIndex == 1);
    CHECK(dialog.actions[2].kind == EventDialogActionKind::Mm9RudeSkillTrainerOffer);
    CHECK(dialog.actions[2].choiceMark == EventDialogChoiceMark::Exit);

    selectionIndex = 0;
    controller.executeActiveDialogAction(context);
    CHECK(party.member(0)->findSkill("Axe")->mastery == SkillMastery::Normal);
    CHECK(party.gold() == 5000);

    selectionIndex = 2;
    controller.executeActiveDialogAction(context);
    REQUIRE(dialog.actions.size() == 4);

    // Dagger: both members can; the second is trained without being the active member, and the page stays.
    selectionIndex = 1;
    controller.executeActiveDialogAction(context);
    REQUIRE(dialog.actions.size() == 3);
    CHECK(dialog.actions[0].label == "Ari: Become Expert in Dagger for 2000 gold");
    CHECK(dialog.actions[1].label == "Bryn: Become Expert in Dagger for 2000 gold");
    CHECK(dialog.actions[1].choiceTag == "Train \xC2\xB7 Expert");
    REQUIRE(party.activeMemberIndex() == 0);

    selectionIndex = 1;
    controller.executeActiveDialogAction(context);
    CHECK(party.member(1)->findSkill("Dagger")->mastery == SkillMastery::Expert);
    CHECK(party.member(0)->findSkill("Dagger")->mastery == SkillMastery::Normal);
    CHECK(party.gold() == 3000);
    CHECK(uiController.statusBar().eventText == "Bryn is now a Expert in Dagger.");
    REQUIRE(dialog.actions.size() == 3);
    REQUIRE(dialog.lines.size() == 1);
    CHECK(dialog.lines[0] == "Bryn is now a Expert in Dagger.");
    CHECK(dialog.actions[1].choiceMark == EventDialogChoiceMark::Locked);
    CHECK(selectionIndex == 0);

    // Back to the skills, then to the talk; a single-skill trainer lists the members at once.
    selectionIndex = 2;
    controller.executeActiveDialogAction(context);
    selectionIndex = 3;
    controller.executeActiveDialogAction(context);
    REQUIRE(dialog.actions.size() == 2);

    selectionIndex = 1;
    controller.executeActiveDialogAction(context);
    REQUIRE(dialog.actions.size() == 3);
    CHECK(dialog.actions[0].choiceMark == EventDialogChoiceMark::Locked);
    CHECK(dialog.actions[1].label == "Bryn: Become Expert in Spear for 2000 gold");
    CHECK(dialog.actions[2].kind == EventDialogActionKind::Mm9RudeSkillTrainerBack);
    CHECK(selectionIndex == 1);
}

TEST_CASE("a ruleset's rows on MM9 people: the Hag's MAW topics and a Jarl's bounty office for his region")
{
    using OpenYAMM::Game::EventDialogActionKind;
    using OpenYAMM::Game::EventDialogChoiceMark;

    OpenYAMM::Game::Mm9RudeDialogueTable table;
    REQUIRE(table.loadDialogueText("NPC132.rude", rudeRow(132, 132, 1, "Not today.", "Goodbye.", -1)));
    REQUIRE(table.loadDialogueText(
        "NPC45.rude",
        rudeRow(45, 45, 1, "News?", "None.", 2) + rudeRow(45, 45, 2, "Not today.", "Goodbye.", -1)
            + rudeRow(45, 2, 1, "Thanks.", "Goodbye.", -1)));
    REQUIRE(table.loadRulesetRowsText(
        "dialogue.yml",
        "format_version: 1\n"
        "topics:\n"
        "  - {npc: 132, event: 10010, label: Skill reset}\n"
        "  - {npc: 132, event: 10040, label: Dimensional Maps}\n"
        "bounties:\n"
        "  - {npc: 45, map: sturmford.blv}\n"));

    OpenYAMM::Game::Party party;
    party.seed({});
    OpenYAMM::Game::GameplayUiController uiController;
    OpenYAMM::Game::EventRuntimeState eventRuntimeState;
    OpenYAMM::Game::EventDialogContent dialog = {};
    size_t selectionIndex = 0;
    OpenYAMM::Tests::PartySpellTestWorldRuntime world = {};
    world.bindParty(&party);
    world.bindEventRuntimeState(&eventRuntimeState);
    std::vector<std::string> monsterRow(38);
    monsterRow[0] = "195";
    monsterRow[1] = "Human Mercenary C";
    monsterRow[2] = "Human Mercenary C";
    monsterRow[3] = "10";
    monsterRow[4] = "100";
    monsterRow[10] = "Short";
    monsterRow[11] = "Normal";
    monsterRow[17] = "Phys";
    monsterRow[18] = "1d6";
    OpenYAMM::Game::MonsterTable monsterTable;
    REQUIRE(monsterTable.loadStatsFromRows({monsterRow}));
    world.bindMonsterTable(&monsterTable);
    world.setMapName("Sturmford City");
    OpenYAMM::Game::MapStatsEntry region = {};
    region.name = "Sturmford";
    region.fileName = "sturmford.blv";
    const std::vector<OpenYAMM::Game::MapStatsEntry> maps = {region};
    OpenYAMM::Game::GameplayDialogController::Context context = {
        .uiController = uiController,
        .eventRuntimeState = eventRuntimeState,
        .activeEventDialog = dialog,
        .selectionIndex = selectionIndex,
        .pParty = &party,
        .pWorldRuntime = &world,
        .pMm9RudeDialogueTable = &table,
        .pMapEntries = &maps,
    };
    const OpenYAMM::Game::GameplayDialogController controller;

    // The Hag: both topics on her first page, before the row that ends the talk.
    controller.openMm9RudeDialogue(context, 132);
    REQUIRE(dialog.actions.size() == 3);
    CHECK(dialog.actions[0].kind == EventDialogActionKind::Mm9RudeRulesetEvent);
    CHECK(dialog.actions[0].id == 10010);
    CHECK(dialog.actions[0].label == "Skill reset");
    CHECK(dialog.actions[1].id == 10040);
    CHECK(dialog.actions[2].choiceMark == EventDialogChoiceMark::Exit);

    // The Jarl: the bounty office on his first page only; it posts the region's hunt, its target placed later.
    controller.openMm9RudeDialogue(context, 45);
    REQUIRE(dialog.actions.size() == 3);
    CHECK(dialog.actions[1].kind == EventDialogActionKind::Mm9RudeBountyOffice);
    CHECK(dialog.actions[1].argument == "sturmford.blv");
    selectionIndex = 1;
    controller.executeActiveDialogAction(context);
    REQUIRE(dialog.lines.size() == 1);
    CHECK(dialog.actions.size() == 3);
    CHECK(eventRuntimeState.namedGlobalVars.contains("MMerge.BountyHunt.Sturmford.Month"));
    CHECK(eventRuntimeState.namedGlobalVars["MMerge.BountyHunt.Sturmford.Pending"] == 1);
    CHECK(world.hostileSummonRequests().empty());
    selectionIndex = 0;
    controller.executeActiveDialogAction(context);
    CHECK(table.rulesetRows(45).size() == 1);

    // A row for someone without dialogue, or without its event, map or label, is an error.
    OpenYAMM::Game::Mm9RudeDialogueTable stale;
    REQUIRE(stale.loadDialogueText("NPC132.rude", rudeRow(132, 132, 1, "Not today.", "Goodbye.", -1)));
    CHECK_FALSE(stale.loadRulesetRowsText(
        "dialogue.yml", "format_version: 1\ntopics:\n  - {npc: 7, event: 10010, label: Skill reset}\n"));
    CHECK_FALSE(stale.loadRulesetRowsText("dialogue.yml", "format_version: 1\nbounties:\n  - {npc: 132}\n"));
    stale.clearRulesetRows();
    CHECK(stale.rulesetRows(132).empty());
}

TEST_CASE("MM9 racial trainers offer each member their racial ability up to the trainer's mastery")
{
    using OpenYAMM::Game::EventDialogActionKind;
    using OpenYAMM::Game::EventDialogChoiceMark;
    using OpenYAMM::Game::SkillMastery;

    // dialogue/racial_trainers.yml (the user, 2026-11-09): a training hall's keeper teaches up to Master, Arslegard's
    // and a Yorwick grandmaster up to Grandmaster.
    OpenYAMM::Game::Mm9RudeDialogueTable table;
    REQUIRE(table.loadDialogueText(
        "NPC21.rude",
        rudeRow(21, 21, 1, "Yes.", "Very well.", -3)
            + rudeRow(21, 21, 2, "News?", "None.", 2)
            + rudeRow(21, 21, 3, "Not today.", "Goodbye.", -1)
            + rudeRow(21, 2, 1, "Thanks.", "Goodbye.", -1)));
    REQUIRE(table.loadDialogueText("NPC351.rude", rudeRow(351, 351, 1, "Not today.", "Goodbye.", -1)));
    REQUIRE(table.loadRacialTrainersText(
        "racial_trainers.yml",
        "format_version: 1\n"
        "skills: [DarkElfAbility, VampireAbility, DragonAbility]\n"
        "trainers:\n"
        "  - {rude: 21, mastery: Master}\n"
        "  - {rude: 351, mastery: Grandmaster}\n"));
    REQUIRE(table.racialTrainer(21) != nullptr);
    CHECK(table.racialTrainer(21)->maxMastery == SkillMastery::Master);
    CHECK(table.racialTrainer(22) == nullptr);

    OpenYAMM::Game::ClassSkillTable classSkillTable;
    REQUIRE(classSkillTable.loadCapsFromRows({
        {"", "Vampire", "Knight"},
        {"VampireAbility", "G", "-"},
        {"DarkElfAbility", "-", "E"},
    }));
    OpenYAMM::Game::NpcDialogTable npcDialogTable;

    OpenYAMM::Game::Character vampire = {};
    vampire.name = "Ari";
    vampire.className = "Vampire";
    vampire.maxHealth = 10;
    vampire.health = 10;
    vampire.skills["VampireAbility"] = {"VampireAbility", 10, SkillMastery::Expert};
    OpenYAMM::Game::Character darkElfKnight = vampire;
    darkElfKnight.name = "Bryn";
    darkElfKnight.className = "Knight";
    darkElfKnight.skills.clear();
    darkElfKnight.skills["DarkElfAbility"] = {"DarkElfAbility", 7, SkillMastery::Expert};
    OpenYAMM::Game::Character human = darkElfKnight;
    human.name = "Cai";
    human.skills.clear();

    OpenYAMM::Game::PartySeed seed = {};
    seed.gold = 50000;
    seed.members = {vampire, darkElfKnight, human};
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
    controller.openMm9RudeDialogue(context, 21);

    // The topic stands on the first page before the row that ends the talk, and only there.
    REQUIRE(dialog.actions.size() == 4);
    CHECK(dialog.actions[2].kind == EventDialogActionKind::Mm9RudeRacialTrainerOffer);
    CHECK(dialog.actions[2].label == "We want to train our racial abilities.");
    CHECK(dialog.actions[3].choiceMark == EventDialogChoiceMark::Exit);

    // A row per member: the vampire's lesson; the knight's class stops at Expert; the human has none.
    selectionIndex = 2;
    controller.executeActiveDialogAction(context);
    REQUIRE(dialog.actions.size() == 4);
    CHECK(dialog.actions[0].kind == EventDialogActionKind::Mm9RudeRacialTrainerLearn);
    CHECK(dialog.actions[0].label == "Ari: Become Master in Vampire Ability for 2500 gold");
    CHECK(dialog.actions[0].choiceTag == "Train \xC2\xB7 Master");
    CHECK(dialog.actions[1].label == "Bryn: This skill level can not be learned by the Knight class.");
    CHECK(dialog.actions[1].choiceMark == EventDialogChoiceMark::Locked);
    CHECK(dialog.actions[2].label == "Cai: No racial ability to train.");
    CHECK(dialog.actions[2].choiceMark == EventDialogChoiceMark::Locked);
    CHECK(dialog.actions[3].kind == EventDialogActionKind::Mm9RudeSkillTrainerBack);
    CHECK(selectionIndex == 0);

    // Trained to Master; this hall teaches no further, so the vampire is sent to a grandmaster.
    controller.executeActiveDialogAction(context);
    CHECK(party.member(0)->findSkill("VampireAbility")->mastery == SkillMastery::Master);
    CHECK(party.gold() == 47500);
    REQUIRE(dialog.lines.size() == 1);
    CHECK(dialog.lines[0] == "Ari is now a Master in Vampire Ability.");
    CHECK(dialog.actions[0].label == "Ari: Seek a grandmaster to go further in Vampire Ability.");
    CHECK(dialog.actions[0].choiceMark == EventDialogChoiceMark::Locked);

    // A refused row trains nobody; Back returns to the talk.
    selectionIndex = 1;
    controller.executeActiveDialogAction(context);
    CHECK(party.member(1)->findSkill("DarkElfAbility")->mastery == SkillMastery::Expert);
    selectionIndex = 3;
    controller.executeActiveDialogAction(context);
    REQUIRE(dialog.actions.size() == 4);
    CHECK(dialog.actions[2].kind == EventDialogActionKind::Mm9RudeRacialTrainerOffer);

    // Arslegard's keeper teaches Grandmaster.
    controller.openMm9RudeDialogue(context, 351);
    REQUIRE(dialog.actions.size() == 2);
    selectionIndex = 0;
    controller.executeActiveDialogAction(context);
    REQUIRE(dialog.actions.size() == 4);
    CHECK(dialog.actions[0].choiceMark == EventDialogChoiceMark::None);
    selectionIndex = 0;
    controller.executeActiveDialogAction(context);
    CHECK(party.member(0)->findSkill("VampireAbility")->mastery == SkillMastery::Grandmaster);

    // A trainer without dialogue or a mastery, and an unknown skill, are errors.
    OpenYAMM::Game::Mm9RudeDialogueTable stale;
    REQUIRE(stale.loadDialogueText("NPC21.rude", rudeRow(21, 21, 1, "News?", "None.", -1)));
    CHECK_FALSE(stale.loadRacialTrainersText(
        "racial_trainers.yml",
        "format_version: 1\n"
        "skills: [VampireAbility, Vampirism]\n"
        "trainers:\n"
        "  - {rude: 21, mastery: Normal}\n"
        "  - {rude: 4, mastery: Master}\n"));
    CHECK(stale.errors().size() == 3);
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

TEST_CASE("MM9 quest experience goes to every member and leaves the current-member selection")
{
    const std::string supportLua = loadSourceText("assets_dev/engine/scripts/common/event_support.lua");
    const std::string commonLua = loadSourceText("assets_dev/worlds/mm9/events/common/mm9_common.lua");
    REQUIRE_FALSE(supportLua.empty());
    REQUIRE_FALSE(commonLua.empty());

    std::string error;
    const std::optional<OpenYAMM::Game::ScriptedEventProgram> program =
        OpenYAMM::Game::ScriptedEventProgram::loadFromLuaText(
            supportLua + "\n\n" + commonLua + R"lua(
RegisterEvent(1, "Quest reward", function()
    MM9.giveExperience(2000)
    AddValue(Experience, 7)
end)
)lua",
            "@tests/mm9_quest_experience.lua",
            OpenYAMM::Game::ScriptedEventScope::Map,
            error);
    REQUIRE_MESSAGE(program.has_value(), error.c_str());

    OpenYAMM::Game::Character member = {};
    member.maxHealth = 10;
    member.health = 10;
    OpenYAMM::Game::PartySeed seed = {};
    seed.members.resize(5, member);
    OpenYAMM::Game::Party party;
    party.seed(seed);
    party.setActiveMemberIndex(2);

    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    const OpenYAMM::Game::EventRuntime eventRuntime;
    REQUIRE(eventRuntime.executeEventById(program, std::nullopt, 1, runtimeState, &party));

    for (size_t index = 0; index < party.members().size(); ++index)
    {
        CHECK_EQ(party.members()[index].experience, index == 2 ? 2007 : 2000);
    }
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

TEST_CASE("MM9 RUDE temple, training, inn and bank services open shared house venues and restore RUDE")
{
    struct ServiceCase
    {
        int32_t opcode = 0;
        uint32_t sourceId = 0;
        const char *pType = nullptr;
        bool canHeal = false;
        bool canDonate = false;
    };
    const std::array<ServiceCase, 5> serviceCases = {{
        {.opcode = -3, .sourceId = 62, .pType = "Training"},
        {.opcode = -6, .sourceId = 56, .pType = "Bank"},
        {.opcode = -7, .sourceId = 57, .pType = "Tavern"},
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
    CHECK_EQ(mm9VendorStockRowCount, 5934);
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
    // One merchant list, as in MM9: a single Buy
    REQUIRE_EQ(vendorRootActions.size(), 3);
    CHECK_EQ(vendorRootActions[0].id, OpenYAMM::Game::HouseActionId::ShopBuyStandard);
    CHECK_EQ(vendorRootActions[0].label, "Buy");
    CHECK_EQ(vendorRootActions[1].label, "Display Equipment");
    // MM9's venues teach at Normal (learn_skills): a weapon shop the split weapon skills
    CHECK_EQ(vendorRootActions[2].id, OpenYAMM::Game::HouseActionId::OpenLearnSkillsMenu);
    CHECK(std::find(pSturmfordWeaponVendor->offeredSkills.begin(), pSturmfordWeaponVendor->offeredSkills.end(), "Axe")
        != pSturmfordWeaponVendor->offeredSkills.end());
    // 5: MM7's shop treasure levels at the same stage, no forced special enchant, tier 5 weighted toward levels 5-6
    // (generate_mm9_vendors.py STOCK_GENERATION_VERSION; devdocs/mm9_rework/BALANCE_PLAN.md 3.5).
    CHECK_EQ(pSturmfordWeaponVendor->deterministicStockGenerationVersion, 6);

    const OpenYAMM::Game::HouseEntry *pSturmfordTraining =
        houseTable.resolvePackageSourceServiceId("mm9", 62);
    REQUIRE(pSturmfordTraining != nullptr);
    CHECK(OpenYAMM::Game::resolveHouseServiceType(*pSturmfordTraining)
        == OpenYAMM::Game::HouseServiceType::TrainingHall);
    CHECK_EQ(pSturmfordTraining->trainingMaxLevel, 0);
    CHECK_EQ(pSturmfordTraining->priceMultiplier, doctest::Approx(1.0f));
    CHECK(pSturmfordTraining->serviceCanLearnSkills);
    const std::vector<OpenYAMM::Game::HouseActionOption> trainingActions =
        OpenYAMM::Game::buildHouseActionOptions(
            *pSturmfordTraining,
            nullptr,
            nullptr,
            nullptr,
            0.0f,
            OpenYAMM::Game::DialogueMenuId::None);
    REQUIRE_EQ(trainingActions.size(), 2);
    CHECK_EQ(trainingActions[0].id, OpenYAMM::Game::HouseActionId::TrainingTrainActiveMember);
    CHECK_EQ(trainingActions[1].id, OpenYAMM::Game::HouseActionId::OpenLearnSkillsMenu);

    const OpenYAMM::Game::HouseEntry *pSturmfordTemple =
        houseTable.resolvePackageSourceServiceId("mm9", 58);
    REQUIRE(pSturmfordTemple != nullptr);
    CHECK(OpenYAMM::Game::resolveHouseServiceType(*pSturmfordTemple)
        == OpenYAMM::Game::HouseServiceType::Temple);
    CHECK_EQ(pSturmfordTemple->priceMultiplier, doctest::Approx(1.2f));
    CHECK_EQ(pSturmfordTemple->templeHealingTier, doctest::Approx(0.0f));
    CHECK(pSturmfordTemple->templeCanHeal);
    CHECK(pSturmfordTemple->templeCanDonate);
    CHECK(pSturmfordTemple->serviceCanLearnSkills);
    const std::vector<OpenYAMM::Game::HouseActionOption> templeActions =
        OpenYAMM::Game::buildHouseActionOptions(
            *pSturmfordTemple,
            nullptr,
            nullptr,
            nullptr,
            0.0f,
            OpenYAMM::Game::DialogueMenuId::None);
    REQUIRE_EQ(templeActions.size(), 3);
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
    REQUIRE_EQ(midwifeActions.size(), 2);
    CHECK_EQ(midwifeActions[0].id, OpenYAMM::Game::HouseActionId::TempleHeal);
    CHECK_EQ(midwifeActions[1].id, OpenYAMM::Game::HouseActionId::OpenLearnSkillsMenu);

    // MM9's inns are MM6-MM8 taverns (rent a room, fill the packs, learn skills): Sturmford's value 12 is its merchant
    // base 1.2 times ten, its skills keep the merchant base. The banks are the shared bank.
    const OpenYAMM::Game::HouseEntry *pSturmfordInn = houseTable.resolvePackageSourceServiceId("mm9", 57);
    REQUIRE(pSturmfordInn != nullptr);
    CHECK(OpenYAMM::Game::resolveHouseServiceType(*pSturmfordInn) == OpenYAMM::Game::HouseServiceType::Tavern);
    CHECK_EQ(pSturmfordInn->priceMultiplier, doctest::Approx(12.0f));
    CHECK_EQ(pSturmfordInn->skillPriceMultiplier, doctest::Approx(1.2f));
    const std::vector<OpenYAMM::Game::HouseActionOption> innActions =
        OpenYAMM::Game::buildHouseActionOptions(
            *pSturmfordInn,
            nullptr,
            nullptr,
            nullptr,
            0.0f,
            OpenYAMM::Game::DialogueMenuId::None);
    REQUIRE_GE(innActions.size(), 3);
    CHECK_EQ(innActions[0].id, OpenYAMM::Game::HouseActionId::TavernRentRoom);
    CHECK_EQ(innActions[0].label, "Rent room for 14 gold");
    CHECK_EQ(innActions[1].id, OpenYAMM::Game::HouseActionId::TavernBuyFood);
    CHECK_EQ(innActions[1].label, "Fill packs to 12 days for 17 gold");
    CHECK_EQ(innActions[2].id, OpenYAMM::Game::HouseActionId::OpenLearnSkillsMenu);
    CHECK(std::find(pSturmfordInn->offeredSkills.begin(), pSturmfordInn->offeredSkills.end(), "Stealing")
        != pSturmfordInn->offeredSkills.end());
    const OpenYAMM::Game::HouseEntry *pSturmfordBank = houseTable.resolvePackageSourceServiceId("mm9", 56);
    REQUIRE(pSturmfordBank != nullptr);
    CHECK(OpenYAMM::Game::resolveHouseServiceType(*pSturmfordBank) == OpenYAMM::Game::HouseServiceType::Bank);
    // The Stumbling Hero's innkeeper is NPC339 (MMIXSHOPS names the shop 338)
    REQUIRE(houseTable.resolvePackageSourceServiceId("mm9", 339) != nullptr);
    CHECK(OpenYAMM::Game::resolveHouseServiceType(*houseTable.resolvePackageSourceServiceId("mm9", 339))
        == OpenYAMM::Game::HouseServiceType::Tavern);

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
    // A restock is MM9's 15 rolls from each treasure range
    REQUIRE_EQ(firstStock.size(), 30);
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
    CHECK(firstSpecialStock.empty());
    CHECK(pSturmfordWeaponVendor->deterministicSpecialStockPages.empty());
    for (size_t slotIndex = 0; slotIndex < firstStock.size(); ++slotIndex)
    {
        const OpenYAMM::Game::HouseEntry::DeterministicStockItem &authored =
            pSturmfordWeaponVendor->deterministicStandardStockPages[0].items[slotIndex];
        CHECK_EQ(firstStock[slotIndex].objectDescriptionId, authored.itemId);
        CHECK_EQ(firstStock[slotIndex].standardEnchantId, authored.standardEnchantId);
        CHECK_EQ(firstStock[slotIndex].specialEnchantId, authored.specialEnchantId);
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
    REQUIRE_EQ(libraryStock.size(), 30);
    CHECK(OpenYAMM::Game::HouseServiceRuntime::canSellItemToHouse(
        dataLoader.getItemTable(),
        libraryIt->second,
        libraryStock[0]));
    CHECK(OpenYAMM::Game::HouseServiceRuntime::canSellItemToHouse(
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
    CHECK_EQ(pMigrationState->generationVersion, 6);
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
    REQUIRE_EQ(buyerStock.size(), 30);
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
    CHECK_EQ(loadedStockIt->generationVersion, 6);
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
    CHECK_EQ(transitionTable.entries().size(), 105);
    const OpenYAMM::Game::Mm9MapTransition *pDarkPassageTransition =
        transitionTable.findByCanonicalId("mm9:transition/arslegardcity/147");
    REQUIRE(pDarkPassageTransition != nullptr);
    CHECK_EQ(pDarkPassageTransition->sourceStartPointName, "StartPoint0");
    CHECK_EQ(pDarkPassageTransition->resolvedStartPointName, "StartPoint");
    CHECK_EQ(pDarkPassageTransition->travelDays, -1);
    CHECK(pDarkPassageTransition->sourceDefaultTravelDays);
    // Arslegard City's chasm catch volume (DAT ExitTrigger3), a row the rebuilt city adds.
    const OpenYAMM::Game::Mm9MapTransition *pChasmTransition =
        transitionTable.findByCanonicalId("mm9:transition/arslegardcity/638");
    REQUIRE(pChasmTransition != nullptr);
    CHECK_EQ(pChasmTransition->sourceMapFileName, "arslegardcity.blv");
    CHECK_EQ(pChasmTransition->destinationMapFileName, "thjorgard.blv");

    const OpenYAMM::Game::Mm9SkillTrainerTable &trainerTable = dataLoader.getMm9SkillTrainerTable();
    CHECK_EQ(trainerTable.entries().size(), 115);
    size_t trainerRowCount = 0;
    for (uint32_t rudeId = 1; rudeId <= 999; ++rudeId)
    {
        for (const OpenYAMM::Game::Mm9RudeRow &row : dataLoader.getMm9RudeDialogueTable().rows(rudeId))
        {
            if (row.next != -4)
            {
                continue;
            }
            ++trainerRowCount;
            CHECK_MESSAGE(
                trainerTable.find(rudeId, row.rowIndex) != nullptr,
                "Missing trainer service for RUDE ", rudeId, " source line ", row.sourceLine);
        }
    }
    CHECK_EQ(trainerRowCount, 115);
    const OpenYAMM::Game::Mm9SkillTrainerService *pBladeExpert = trainerTable.find(80, 0);
    REQUIRE(pBladeExpert != nullptr);
    CHECK((pBladeExpert->topic.skillNames == std::vector<std::string>{"Sword", "Dagger", "Axe"}));
    const OpenYAMM::Game::Mm9SkillTrainerService *pCudgelGrandmaster = trainerTable.find(37, 0);
    REQUIRE(pCudgelGrandmaster != nullptr);
    CHECK((pCudgelGrandmaster->topic.skillNames == std::vector<std::string>{"Mace", "Staff"}));
    const OpenYAMM::Game::Mm9SkillTrainerService *pSpiritGrandmaster = trainerTable.findByCanonicalId(
        "mm9:trainer/407/2");
    REQUIRE(pSpiritGrandmaster != nullptr);
    CHECK(pSpiritGrandmaster->topic.targetMastery == OpenYAMM::Game::SkillMastery::Grandmaster);
    CHECK((pSpiritGrandmaster->topic.skillNames
        == std::vector<std::string>{"SpiritMagic", "MindMagic", "BodyMagic"}));
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
    // MM9's Recovery 30 is 0.99 s (59 ticks of 1/60 s); the balance gives levels 1-20 75 ticks (1.25 s,
    // mm9_monster_balance.py, devdocs/mm9_rework/BALANCE_PLAN.md section 3.2).
    CHECK_EQ(pTroglodyte->recovery, 75);
    // Fighting people: no immunity, the level 11-20 base of 5 in every school.
    CHECK_EQ(pTroglodyte->fireResistance, 5);
    CHECK_EQ(pTroglodyte->airResistance, 5);
    CHECK_EQ(pTroglodyte->waterResistance, 5);
    CHECK_EQ(pTroglodyte->earthResistance, 5);
    CHECK_EQ(pTroglodyte->mindResistance, 5);
    CHECK_EQ(pTroglodyte->spiritResistance, 5);
    CHECK_EQ(pTroglodyte->bodyResistance, 5);
    CHECK_EQ(pTroglodyte->spell1Name, "poison spray");
    // Spell use: MM9's 50% x 0.4.
    CHECK_EQ(pTroglodyte->spell1UseChance, 20);

    const OpenYAMM::Game::MonsterEntry *pPresentation =
        dataLoader.getMonsterTable().findById(9097);
    REQUIRE(pPresentation != nullptr);
    CHECK_EQ(pPresentation->internalName, "MM9 Troglodyte B");

    const OpenYAMM::Game::MonsterProjectileEntry *pAxe =
        dataLoader.getMonsterProjectileTable().findByToken("MM9Axe");
    REQUIRE(pAxe != nullptr);
    // Its own missile object (MM9's 100 ft/s for 5 s, no gravity), not the party's thrown-axe item object 309.
    CHECK_EQ(pAxe->objectId, 19011);

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
    // The house registry is global: MM9's shops and services are there in another world too (a game started in MM7
    // that loads an MM9 save trades in Chedian), in MM9's own id range, and the legacy houses keep their rows.
    CHECK(dataLoader.getHouseTable().resolvePackageSourceVendorId("mm9", 53) != nullptr);
    CHECK(dataLoader.getHouseTable().resolvePackageSourceServiceId("mm9", 58) != nullptr);
    CHECK(std::all_of(
        dataLoader.getHouseTable().entries().begin(),
        dataLoader.getHouseTable().entries().end(),
        [](const std::pair<const uint32_t, OpenYAMM::Game::HouseEntry> &entry)
        {
            return entry.second.vendorStockProfile == OpenYAMM::Game::VendorStockProfile::None
                || entry.second.packageId == "mm9";
        }));
    // The quest journal is global too: MM9's quest notes are there in another world, beside the base quests.
    CHECK(dataLoader.getJournalQuestTable().hasQuestText(3));
    CHECK(dataLoader.getJournalQuestTable().hasQuestText(90001));

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
    CHECK_EQ(pPoorSword->value, 40);
    CHECK_EQ(pPoorSword->inventoryWidth, 1);
    CHECK_EQ(pPoorSword->inventoryHeight, 5);
    CHECK_EQ(pPoorSword->equipX, 14);
    CHECK_EQ(pPoorSword->equipY, 136);
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
    OpenYAMM::Game::IndoorSceneYmlLoader loader = {};
    std::string errorMessage;
    const std::optional<OpenYAMM::Game::IndoorSceneData> loadedScene = loader.loadFromText(
        loadSourceText("assets_dev/worlds/mm9/maps/bootcamp.scene.yml"),
        errorMessage);
    REQUIRE_MESSAGE(loadedScene.has_value(), errorMessage.c_str());
    const OpenYAMM::Game::IndoorSceneData &scene = *loadedScene;

    struct ExpectedBinding
    {
        int32_t rudeId;
        uint32_t sourceObjectIndex;
        uint16_t yawUnits;
        const char *pName;
    };
    constexpr std::array<ExpectedBinding, 4> ExpectedBindings = {{
        {436, 207, 512, "Old Man"},
        {101, 209, 1023, "Thorkatla the Indiscreet"},
        {204, 210, 6, "Dearbhorgaill A'Washadi"},
        {206, 211, 1533, "Fiachna A'Lanth"},
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
    }
}

TEST_CASE("MM9 black chests roll MM9's own artifacts and level-6 drops mix every world's equipment")
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
    const OpenYAMM::Game::ItemTable &itemTable = dataLoader.getItemTable();
    std::unordered_set<uint32_t> artifacts;
    int equipment = 0;
    int mm9Equipment = 0;
    int artifactDrops = 0;
    constexpr uint32_t Rolls = 400;

    for (uint32_t seed = 1; seed <= Rolls; ++seed)
    {
        // A black chest's level-7 slot (ChestRuntime.cpp): an artifact or relic of MM9's own, the only world its
        // World:mm9 flag allows (devdocs/LOOT_POOL.md, BALANCE_PLAN.md 3.8).
        std::mt19937 chestRng(seed);
        const std::optional<OpenYAMM::Game::InventoryItem> chestItem =
            OpenYAMM::Game::ItemGenerator::generateRandomInventoryItem(
                itemTable,
                dataLoader.getStandardItemEnchantTable(),
                dataLoader.getSpecialItemEnchantTable(),
                OpenYAMM::Game::ItemGenerationRequest{
                    .treasureLevel = 6,
                    .mode = OpenYAMM::Game::ItemGenerationMode::ChestLoot,
                    .allowRareItems = true,
                    .rareItemsOnly = true,
                    .worldId = "mm9",
                },
                nullptr,
                chestRng);
        REQUIRE(chestItem.has_value());
        const OpenYAMM::Game::ItemDefinition *pChestItem = itemTable.get(chestItem->objectDescriptionId);
        REQUIRE(pChestItem != nullptr);
        CHECK(OpenYAMM::Game::ItemRuntime::isArtifact(*pChestItem));
        CHECK_FALSE(pChestItem->hasContentFlag("NoRandom"));
        artifacts.insert(pChestItem->itemId);
        CHECK_EQ(pChestItem->packageId, "mm9");

        // An untyped level-6 monster drop: no artifact (world.yml chestArtifactsOnly); equipment about four times in
        // five, MM9's weighing like MM6-MM8's items of its family and tier (mm9_item_balance.py), a fifth of it.
        std::mt19937 dropRng(seed);
        const std::optional<OpenYAMM::Game::InventoryItem> drop =
            OpenYAMM::Game::ItemGenerator::generateRandomInventoryItem(
                itemTable,
                dataLoader.getStandardItemEnchantTable(),
                dataLoader.getSpecialItemEnchantTable(),
                OpenYAMM::Game::ItemGenerationRequest{
                    .treasureLevel = 6,
                    .mode = OpenYAMM::Game::ItemGenerationMode::MonsterLoot,
                    .worldId = "mm9",
                },
                nullptr,
                dropRng);
        REQUIRE(drop.has_value());
        const OpenYAMM::Game::ItemDefinition *pDrop = itemTable.get(drop->objectDescriptionId);
        REQUIRE(pDrop != nullptr);
        artifactDrops += OpenYAMM::Game::ItemRuntime::isArtifact(*pDrop) ? 1 : 0;
        static const std::unordered_set<std::string> EquipmentStats = {
            "Weapon", "Weapon2", "Weapon1or2", "Missile", "Armor", "Shield", "Helm", "Belt", "Cloak", "Gauntlets",
            "Boots", "Ring", "Amulet"};
        const bool isEquipment = EquipmentStats.contains(pDrop->equipStat);
        equipment += isEquipment ? 1 : 0;
        mm9Equipment += isEquipment && pDrop->packageId == "mm9" ? 1 : 0;
    }

    // The hand-placed and quest artifacts (Black's Heart, Everstrike, Gungnir, Spencer's Obedience, The Green Man)
    // never roll, so a chest cannot give a second copy.
    for (const uint32_t fixedItemId : {10180u, 10184u, 10189u, 10198u, 10213u})
    {
        CHECK_FALSE(artifacts.contains(fixedItemId));
    }

    CHECK_GT(artifacts.size(), 20);
    CHECK_EQ(artifactDrops, 0);
    CHECK_GT(equipment, int(Rolls) * 70 / 100);
    CHECK_LT(equipment, int(Rolls) * 90 / 100);
    CHECK_GT(mm9Equipment, equipment * 8 / 100);
    CHECK_LT(mm9Equipment, equipment * 35 / 100);
}
