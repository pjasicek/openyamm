#include "doctest/doctest.h"

#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "game/mm9/Mm9DialoguePackage.h"
#include "game/mm9/Mm9InteractionRouting.h"
#include "game/mm9/Mm9JournalContent.h"
#include "game/mm9/Mm9DialogueRuntime.h"
#include "game/mm9/Mm9DialogueUi.h"
#include "game/mm9/Mm9ServiceRuntime.h"
#include "game/mm9/Mm9ScriptRuntime.h"
#include "game/events/EventRuntime.h"
#include "game/gameplay/GameplayDialogController.h"
#include "game/maps/OutdoorSceneYml.h"
#include "game/maps/SaveGame.h"
#include "game/party/Party.h"
#include "game/ui/GameplayUiController.h"
#include "tools/Mm9RudeTranscode.h"
#include "tests/PartySpellTestHarness.h"

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <map>
#include <string>
#include <system_error>
#include <vector>

namespace
{
void writeTextFile(const std::filesystem::path &path, const std::string &contents)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream stream(path, std::ios::binary);
    REQUIRE(stream.good());
    stream << contents;
}

std::string rudeRow(
    int32_t rudeId,
    int32_t nodeId,
    int32_t choiceSlot,
    const std::string &prompt,
    const std::string &response,
    int32_t next,
    int32_t requiredKey)
{
    std::vector<std::string> columns = {
        std::to_string(rudeId),
        std::to_string(nodeId),
        std::to_string(choiceSlot),
        prompt,
        response,
        std::to_string(next),
    };
    while (columns.size() < 30)
    {
        columns.push_back("0");
    }
    columns[6] = std::to_string(requiredKey);
    return OpenYAMM::Game::serializeMm9RudeCsvLine(columns) + "\n";
}

std::string serviceRows()
{
    struct ServiceRow
    {
        int32_t choiceSlot = 0;
        std::string prompt;
        int32_t opcode = 0;
    };

    const std::vector<ServiceRow> rows = {
        {1, "Shop", -2},
        {2, "Training", -3},
        {3, "Skill training", -4},
        {4, "Travel", -5},
        {5, "Bank", -6},
        {6, "Inn", -7},
        {7, "Healer", -8},
        {8, "Hire", -10},
        {9, "Dismiss", -11},
        {10, "Item combine", -13},
        {11, "Quest handoff", -14},
        {12, "Town portal", -15},
        {13, "Donation", -16},
    };

    std::string text;
    for (const ServiceRow &row : rows)
    {
        text += rudeRow(2, 2, row.choiceSlot, row.prompt, row.prompt + " response", row.opcode, 0);
    }

    return text;
}

class Mm9DialogRoutingWorldRuntime : public OpenYAMM::Tests::PartySpellTestWorldRuntime
{
public:
    bool executeNpcTopicEvent(
        uint16_t eventId,
        size_t &previousMessageCount,
        std::optional<uint8_t> continueStep = std::nullopt) override
    {
        ++executedNpcTopicCount;
        capturedNpcTopicEventId = eventId;
        capturedPreviousMessageCount = previousMessageCount;
        capturedContinueStep = continueStep;
        return true;
    }

    bool executeMm9DialogueAction(
        const OpenYAMM::Game::EventDialogAction &action,
        OpenYAMM::Game::EventDialogContent &content) override
    {
        ++executedActionCount;
        capturedAction = action;
        content = nextContent;
        return true;
    }

    size_t executedActionCount = 0;
    size_t executedNpcTopicCount = 0;
    uint16_t capturedNpcTopicEventId = 0;
    size_t capturedPreviousMessageCount = 0;
    std::optional<uint8_t> capturedContinueStep;
    OpenYAMM::Game::EventDialogAction capturedAction = {};
    OpenYAMM::Game::EventDialogContent nextContent = {};
};

class Mm9DialogCallbackWorldRuntime : public OpenYAMM::Tests::PartySpellTestWorldRuntime
{
public:
    Mm9DialogCallbackWorldRuntime(
        OpenYAMM::Game::Mm9DialogueRuntime &dialogueRuntime,
        OpenYAMM::Game::Mm9ScriptRuntime &scriptRuntime)
        : m_dialogueRuntime(dialogueRuntime)
        , m_scriptRuntime(scriptRuntime)
    {
    }

    bool executeMm9DialogueAction(
        const OpenYAMM::Game::EventDialogAction &action,
        OpenYAMM::Game::EventDialogContent &content) override
    {
        ++executedActionCount;
        const OpenYAMM::Game::Mm9DialogueUiActionResult result =
            OpenYAMM::Game::executeMm9DialogueAction(m_dialogueRuntime, action);
        if (!result.handled)
        {
            return false;
        }

        if (result.selection.kind == OpenYAMM::Game::Mm9DialogueSelectionKind::Close
            && !result.selection.onRudeExitLabel.empty()
            && !result.selection.owner.scriptName.empty())
        {
            ++executedCloseCallbackCount;
            callbackScript = result.selection.owner.scriptName;
            callbackLabel = result.selection.onRudeExitLabel;
            std::optional<std::string> error;
            const bool callbackRan =
                m_scriptRuntime.runLabel(callbackScript, callbackLabel, error);
            CHECK(callbackRan);
            CHECK_FALSE(error.has_value());
        }

        content = result.content;
        return true;
    }

    size_t executedActionCount = 0;
    size_t executedCloseCallbackCount = 0;
    std::string callbackScript;
    std::string callbackLabel;

private:
    OpenYAMM::Game::Mm9DialogueRuntime &m_dialogueRuntime;
    OpenYAMM::Game::Mm9ScriptRuntime &m_scriptRuntime;
};

std::filesystem::path makeFixtureRoot()
{
    const int64_t suffix = std::chrono::steady_clock::now().time_since_epoch().count();
    const std::filesystem::path root =
        std::filesystem::temp_directory_path() / ("openyamm_mm9_dialogue_runtime_fixture_"
            + std::to_string(suffix));
    std::error_code error;
    std::filesystem::remove_all(root, error);

    const std::filesystem::path rudeDirectory = root / "extracted/RUDE/RUDE";
    writeTextFile(
        rudeDirectory / "NPC1.rude",
        rudeRow(1, 1, 2, "Locked", "QBit-gated response", -1, 44) +
            rudeRow(1, 1, 1, "Continue", "Go to service node", 2, 0) +
            rudeRow(1, 1, 3, "Bye", "Goodbye", -1, 0) +
            rudeRow(1, 2, 1, "Bank", "Open bank", -6, 0));
    writeTextFile(rudeDirectory / "NPC2.rude", serviceRows());
    writeTextFile(
        rudeDirectory / "NPC3.rude",
        rudeRow(3, 3, 1, "Go to node 999", "Node 999 response", 999, 0) +
            rudeRow(3, 3, 2, "Zero next", "Zero response", 0, 0) +
            rudeRow(3, 999, 1, "Finish", "Finish response", -1, 0));
    writeTextFile(rudeDirectory / "NPCNAME.rude", "1,Test NPC\n");
    writeTextFile(rudeDirectory / "TOPBLURB.rude", "1,Test NPC,Test blurb\n");
    writeTextFile(rudeDirectory / "NPC997.rude", rudeRow(997, 997, 1, "Quest", "Quest text", 0, 0));
    writeTextFile(rudeDirectory / "NPC998.rude", rudeRow(998, 998, 1, "Note", "Note text", 0, 0));
    writeTextFile(rudeDirectory / "NPC999.rude", rudeRow(999, 999, 1, "Award", "Award text", 0, 0));

    const std::filesystem::path scriptsDirectory = root / "extracted/SCRIPTS/SCRIPTS";
    writeTextFile(scriptsDirectory / "globals.inc", "#number TEST_KEY = 44\n");
    writeTextFile(
        scriptsDirectory / "DORUDE.scr",
        "#include globals.inc\n"
        ":OnUse\n"
        "HasKey TEST_KEY\n"
        "DoRude 1\n"
        "OnRudeExit OnRude\n"
        "SetConsoleNumVar SCORE, 7\n"
        "SetConsoleStrVar GREETING, \"hello\"\n"
        "GetConsoleNumVar SCORE, SCORE_OUT\n"
        "GetConsoleStrVar GREETING, GREETING_OUT\n"
        "MysteryOp 7\n"
        ":OnRude\n"
        "GiveKey 44\n"
        ":Rewards\n"
        "GiveGold 50\n"
        "GiveExp 80\n"
        "GiveItem 197\n"
        "HasItem 197\n"
        "TakeItem 197\n"
        "HasItem 197\n"
        ":ObjectState\n"
        "GetParam 0, npc_id\n"
        "GetParam 1, target_name\n"
        "SetPropNumber NeedsTick, 12\n"
        "GetObjectHandleByRudeId npc_id, npc_object\n"
        "AddTrigger Use, OnUse\n"
        "Trigger npc_object, GoToLoc\n"
        "Trigger hMe, Use\n"
        ":ScheduleWait\n"
        "Wait 2, 2, WaitDone\n"
        ":WaitDone\n"
        "SetConsoleNumVar WAIT_DONE, 1\n");

    writeTextFile(
        root / "source_maps/testmap.raw_objects.yml",
        "format_version: 1\n"
        "kind: mm9_raw_world_objects\n"
        "objects:\n"
        "  - object_index: 7\n"
        "    name: ShopkeeperHuman2MaleA\n"
        "    properties:\n"
        "      - name: Name\n"
        "        code: 0\n"
        "        flags: 0\n"
        "        decoded: true\n"
        "        raw_hex: \"\"\n"
        "        value_json: \"\\\"Fixture NPC\\\"\"\n"
        "      - name: DoRude\n"
        "        code: 5\n"
        "        flags: 0\n"
        "        decoded: true\n"
        "        raw_hex: \"01\"\n"
        "        value_json: \"1\"\n"
        "      - name: NPCNbr\n"
        "        code: 0\n"
        "        flags: 0\n"
        "        decoded: false\n"
        "        raw_hex: \"0000803f\"\n"
        "        value_json: \"\"\n"
        "      - name: ScriptName\n"
        "        code: 0\n"
        "        flags: 0\n"
        "        decoded: true\n"
        "        raw_hex: \"\"\n"
        "        value_json: \"\\\"DORUDE.scr\\\"\"\n"
        "      - name: ScriptParams\n"
        "        code: 0\n"
        "        flags: 0\n"
        "        decoded: true\n"
        "        raw_hex: \"\"\n"
        "        value_json: \"\\\"1 FixtureTarget\\\"\"\n"
        "      - name: GreetingSound\n"
        "        code: 0\n"
        "        flags: 0\n"
        "        decoded: true\n"
        "        raw_hex: \"\"\n"
        "        value_json: \"\\\"greeting.wav\\\"\"\n"
        "  - object_index: 8\n"
        "    name: BankerHumanFemaleA\n"
        "    properties:\n"
        "      - name: Name\n"
        "        code: 0\n"
        "        flags: 0\n"
        "        decoded: true\n"
        "        raw_hex: \"\"\n"
        "        value_json: \"\\\"Direct Bank NPC\\\"\"\n"
        "      - name: DoRude\n"
        "        code: 5\n"
        "        flags: 0\n"
        "        decoded: true\n"
        "        raw_hex: \"01\"\n"
        "        value_json: \"1\"\n"
        "      - name: NPCNbr\n"
        "        code: 0\n"
        "        flags: 0\n"
        "        decoded: false\n"
        "        raw_hex: \"00000040\"\n"
        "        value_json: \"\"\n"
        "  - object_index: 10\n"
        "    name: ShopkeeperHumanMaleA\n"
        "    properties:\n"
        "      - name: Name\n"
        "        code: 0\n"
        "        flags: 0\n"
        "        decoded: true\n"
        "        raw_hex: \"\"\n"
        "        value_json: \"\\\"Direct Shop NPC\\\"\"\n"
        "      - name: DoRude\n"
        "        code: 5\n"
        "        flags: 0\n"
        "        decoded: true\n"
        "        raw_hex: \"01\"\n"
        "        value_json: \"1\"\n"
        "      - name: NPCNbr\n"
        "        code: 0\n"
        "        flags: 0\n"
        "        decoded: false\n"
        "        raw_hex: \"00000040\"\n"
        "        value_json: \"\"\n"
        "  - object_index: 11\n"
        "    name: TrainerHumanMaleA\n"
        "    properties:\n"
        "      - name: Name\n"
        "        code: 0\n"
        "        flags: 0\n"
        "        decoded: true\n"
        "        raw_hex: \"\"\n"
        "        value_json: \"\\\"Direct Training NPC\\\"\"\n"
        "      - name: DoRude\n"
        "        code: 5\n"
        "        flags: 0\n"
        "        decoded: true\n"
        "        raw_hex: \"01\"\n"
        "        value_json: \"1\"\n"
        "      - name: NPCNbr\n"
        "        code: 0\n"
        "        flags: 0\n"
        "        decoded: false\n"
        "        raw_hex: \"00000040\"\n"
        "        value_json: \"\"\n"
        "  - object_index: 12\n"
        "    name: SkillTrainerHumanFemaleA\n"
        "    properties:\n"
        "      - name: Name\n"
        "        code: 0\n"
        "        flags: 0\n"
        "        decoded: true\n"
        "        raw_hex: \"\"\n"
        "        value_json: \"\\\"Direct Skill Training NPC\\\"\"\n"
        "      - name: DoRude\n"
        "        code: 5\n"
        "        flags: 0\n"
        "        decoded: true\n"
        "        raw_hex: \"01\"\n"
        "        value_json: \"1\"\n"
        "      - name: NPCNbr\n"
        "        code: 0\n"
        "        flags: 0\n"
        "        decoded: false\n"
        "        raw_hex: \"00000040\"\n"
        "        value_json: \"\"\n"
        "  - object_index: 13\n"
        "    name: TravelGuideHumanMaleA\n"
        "    properties:\n"
        "      - name: Name\n"
        "        code: 0\n"
        "        flags: 0\n"
        "        decoded: true\n"
        "        raw_hex: \"\"\n"
        "        value_json: \"\\\"Direct Travel NPC\\\"\"\n"
        "      - name: DoRude\n"
        "        code: 5\n"
        "        flags: 0\n"
        "        decoded: true\n"
        "        raw_hex: \"01\"\n"
        "        value_json: \"1\"\n"
        "      - name: NPCNbr\n"
        "        code: 0\n"
        "        flags: 0\n"
        "        decoded: false\n"
        "        raw_hex: \"00000040\"\n"
        "        value_json: \"\"\n"
        "  - object_index: 14\n"
        "    name: InnkeeperHumanFemaleA\n"
        "    properties:\n"
        "      - name: Name\n"
        "        code: 0\n"
        "        flags: 0\n"
        "        decoded: true\n"
        "        raw_hex: \"\"\n"
        "        value_json: \"\\\"Direct Inn NPC\\\"\"\n"
        "      - name: DoRude\n"
        "        code: 5\n"
        "        flags: 0\n"
        "        decoded: true\n"
        "        raw_hex: \"01\"\n"
        "        value_json: \"1\"\n"
        "      - name: NPCNbr\n"
        "        code: 0\n"
        "        flags: 0\n"
        "        decoded: false\n"
        "        raw_hex: \"00000040\"\n"
        "        value_json: \"\"\n"
        "  - object_index: 15\n"
        "    name: HealerHumanFemaleA\n"
        "    properties:\n"
        "      - name: Name\n"
        "        code: 0\n"
        "        flags: 0\n"
        "        decoded: true\n"
        "        raw_hex: \"\"\n"
        "        value_json: \"\\\"Direct Healer NPC\\\"\"\n"
        "      - name: DoRude\n"
        "        code: 5\n"
        "        flags: 0\n"
        "        decoded: true\n"
        "        raw_hex: \"01\"\n"
        "        value_json: \"1\"\n"
        "      - name: NPCNbr\n"
        "        code: 0\n"
        "        flags: 0\n"
        "        decoded: false\n"
        "        raw_hex: \"00000040\"\n"
        "        value_json: \"\"\n"
        "  - object_index: 16\n"
        "    name: HirelingHumanMaleA\n"
        "    properties:\n"
        "      - name: Name\n"
        "        code: 0\n"
        "        flags: 0\n"
        "        decoded: true\n"
        "        raw_hex: \"\"\n"
        "        value_json: \"\\\"Direct Hire NPC\\\"\"\n"
        "      - name: DoRude\n"
        "        code: 5\n"
        "        flags: 0\n"
        "        decoded: true\n"
        "        raw_hex: \"01\"\n"
        "        value_json: \"1\"\n"
        "      - name: NPCNbr\n"
        "        code: 0\n"
        "        flags: 0\n"
        "        decoded: false\n"
        "        raw_hex: \"00000040\"\n"
        "        value_json: \"\"\n"
        "  - object_index: 9\n"
        "    name: BrokenDialogueObject\n"
        "    properties:\n"
        "      - name: Name\n"
        "        code: 0\n"
        "        flags: 0\n"
        "        decoded: true\n"
        "        raw_hex: \"\"\n"
        "        value_json: \"\\\"Broken NPC\\\"\"\n"
        "      - name: DoRude\n"
        "        code: 5\n"
        "        flags: 0\n"
        "        decoded: true\n"
        "        raw_hex: \"01\"\n"
        "        value_json: \"1\"\n"
        "      - name: NPCNbr\n"
        "        code: 0\n"
        "        flags: 0\n"
        "        decoded: false\n"
        "        raw_hex: \"0000f041\"\n"
        "        value_json: \"\"\n");

    writeTextFile(
        root / "assets_dev/worlds/mm9/world.yml",
        "id: mm9\n"
        "name: MM9\n"
        "sourceGame: mm9\n");

    const OpenYAMM::Game::Mm9DialoguePipelineResult generated =
        OpenYAMM::Game::generateMm9DialoguePipelineFiles(root / "extracted", root / "source_maps");
    REQUIRE(generated.errors.empty());

    const OpenYAMM::Game::Mm9DialoguePipelineWriteResult writeResult =
        OpenYAMM::Game::writeMm9DialoguePipelineFiles(root / "assets_dev/worlds/mm9", generated.files, false);
    REQUIRE(writeResult.errors.empty());

    return root;
}

OpenYAMM::Game::Mm9DialoguePackage loadFixturePackage(const std::filesystem::path &fixtureRoot)
{
    OpenYAMM::Engine::AssetFileSystem assetFileSystem = {};
    REQUIRE(assetFileSystem.initialize(
        fixtureRoot,
        fixtureRoot / "assets_dev",
        OpenYAMM::Engine::AssetScaleTier::X1,
        "mm9"));

    OpenYAMM::Game::Mm9DialoguePackage package = {};
    const bool loaded = OpenYAMM::Game::loadMm9DialoguePackage(assetFileSystem, package);
    if (!loaded)
    {
        for (const OpenYAMM::Game::Mm9DialoguePackageError &error : package.errors)
        {
            MESSAGE(error.virtualPath << ": " << error.message);
        }
    }
    REQUIRE(loaded);
    REQUIRE(package.errors.empty());
    return package;
}

void writeExtendedVisibilityDialogueFixture(const std::filesystem::path &fixtureRoot)
{
    writeTextFile(
        fixtureRoot / "assets_dev/worlds/mm9/dialogue/npcs/4.yml",
        "format_version: 1\n"
        "source_file: NPC4.rude\n"
        "rows:\n"
        "  - source: { file: NPC4.rude, row: 1 }\n"
        "    raw_columns: [4, 4, 1, Always, Always response, -1]\n"
        "    decoded: { npc_id: 4, node_id: 4, choice_slot: 1, prompt: Always, response: Always response, next: -1 }\n"
        "    semantic: { action: { kind: close } }\n"
        "  - source: { file: NPC4.rude, row: 2 }\n"
        "    raw_columns: [4, 4, 2, Item gate, Item response, -1, 0, 197]\n"
        "    decoded: { npc_id: 4, node_id: 4, choice_slot: 2, prompt: Item gate, response: Item response, next: -1 }\n"
        "    semantic:\n"
        "      action: { kind: close }\n"
        "      conditions:\n"
        "        required_items:\n"
        "          - { column: c08, item_id: 197, state_id: mm9.inventory.197 }\n"
        "  - source: { file: NPC4.rude, row: 3 }\n"
        "    raw_columns: [4, 4, 3, Console num gate, Console num response, -1]\n"
        "    decoded:\n"
        "      npc_id: 4\n"
        "      node_id: 4\n"
        "      choice_slot: 3\n"
        "      prompt: Console num gate\n"
        "      response: Console num response\n"
        "      next: -1\n"
        "    semantic:\n"
        "      action: { kind: close }\n"
        "      conditions:\n"
        "        required_console_num_equals:\n"
        "          - { variable: SCORE, value: 7, state_id: mm9.console_num.SCORE }\n"
        "  - source: { file: NPC4.rude, row: 4 }\n"
        "    raw_columns: [4, 4, 4, Console str gate, Console str response, -1]\n"
        "    decoded:\n"
        "      npc_id: 4\n"
        "      node_id: 4\n"
        "      choice_slot: 4\n"
        "      prompt: Console str gate\n"
        "      response: Console str response\n"
        "      next: -1\n"
        "    semantic:\n"
        "      action: { kind: close }\n"
        "      conditions:\n"
        "        required_console_str_equals:\n"
        "          - { variable: GREETING, value: hello, state_id: mm9.console_str.GREETING }\n"
        "  - source: { file: NPC4.rude, row: 5 }\n"
        "    raw_columns: [4, 4, 5, Combined gate, Combined response, -1, 0, 197]\n"
        "    decoded:\n"
        "      npc_id: 4\n"
        "      node_id: 4\n"
        "      choice_slot: 5\n"
        "      prompt: Combined gate\n"
        "      response: Combined response\n"
        "      next: -1\n"
        "    semantic:\n"
        "      action: { kind: close }\n"
        "      conditions:\n"
        "        required_items:\n"
        "          - { column: c08, item_id: 197, state_id: mm9.inventory.197 }\n"
        "        required_console_num_equals:\n"
        "          - { variable: SCORE, value: 7, state_id: mm9.console_num.SCORE }\n"
        "        required_console_str_equals:\n"
        "          - { variable: GREETING, value: hello, state_id: mm9.console_str.GREETING }\n");
}

std::vector<std::string> visibleTopicPrompts(const OpenYAMM::Game::Mm9DialogueRuntime &runtime)
{
    std::vector<std::string> prompts;
    const std::vector<OpenYAMM::Game::Mm9DialogueTopic> topics = runtime.visibleTopics();
    for (const OpenYAMM::Game::Mm9DialogueTopic &topic : topics)
    {
        prompts.push_back(topic.prompt);
    }
    return prompts;
}

OpenYAMM::Game::Character makeRuntimePartyMember(const std::string &name)
{
    OpenYAMM::Game::Character member = {};
    member.name = name;
    member.className = "Knight";
    member.role = "Knight";
    member.level = 1;
    member.experience = 0;
    member.health = 40;
    member.maxHealth = 40;
    member.spellPoints = 20;
    member.maxSpellPoints = 20;
    return member;
}

OpenYAMM::Game::Party makeRuntimeParty()
{
    OpenYAMM::Game::PartySeed seed = {};
    seed.gold = 10;
    seed.members.push_back(makeRuntimePartyMember("Ariel"));
    seed.members.push_back(makeRuntimePartyMember("Brom"));
    seed.members.push_back(makeRuntimePartyMember("Cedric"));
    seed.members.push_back(makeRuntimePartyMember("Daria"));

    OpenYAMM::Game::Party party = {};
    party.seed(seed);
    return party;
}

bool pathIsWithin(const std::filesystem::path &root, const std::filesystem::path &path)
{
    const std::filesystem::path relativePath = path.lexically_relative(root);
    if (relativePath.empty())
    {
        return path == root;
    }

    const std::filesystem::path firstElement = *relativePath.begin();
    return firstElement != "..";
}

bool pathHasSegment(const std::filesystem::path &path, const std::string &segment)
{
    for (const std::filesystem::path &pathSegment : path)
    {
        if (pathSegment == segment)
        {
            return true;
        }
    }
    return false;
}

bool isGeneratedMm9ArtifactPath(const std::filesystem::path &path)
{
    const std::string filename = path.filename().string();
    if (filename == "dialogue_bindings.yml" || filename == "script_index.yml")
    {
        return true;
    }

    if (path.extension() == ".lua" && pathHasSegment(path, "scripts"))
    {
        return true;
    }

    return path.extension() == ".yml"
        && (pathHasSegment(path, "dialogue") || pathHasSegment(path, "state"));
}

std::vector<std::string> generatedMm9ArtifactsOutsideWorldTree(const std::filesystem::path &fixtureRoot)
{
    std::vector<std::string> paths;
    const std::filesystem::path mm9WorldRoot = fixtureRoot / "assets_dev/worlds/mm9";

    for (const std::filesystem::directory_entry &entry :
        std::filesystem::recursive_directory_iterator(fixtureRoot))
    {
        if (!entry.is_regular_file())
        {
            continue;
        }

        const std::filesystem::path path = entry.path();
        if (pathIsWithin(mm9WorldRoot, path) || !isGeneratedMm9ArtifactPath(path))
        {
            continue;
        }

        paths.push_back(path.lexically_relative(fixtureRoot).generic_string());
    }

    std::sort(paths.begin(), paths.end());
    return paths;
}

class RecordingServiceHandler : public OpenYAMM::Game::Mm9DialogueServiceHandler
{
public:
    void openService(const OpenYAMM::Game::Mm9DialogueServiceRequest &request) override
    {
        requests.push_back(request);
    }

    std::vector<OpenYAMM::Game::Mm9DialogueServiceRequest> requests;
};

class RecordingServiceRuntime : public OpenYAMM::Game::Mm9ServiceRuntime
{
public:
    void openService(const OpenYAMM::Game::Mm9DialogueServiceRequest &request) override
    {
        Mm9ServiceRuntime::openService(request);
        requests.push_back(request);
    }

    std::vector<OpenYAMM::Game::Mm9DialogueServiceRequest> requests;
};

void assertObjectDispatchesMm9Service(
    const OpenYAMM::Game::Mm9DialoguePackage &package,
    int32_t objectIndex,
    const std::string &objectName,
    const std::string &topicLabel,
    int32_t opcode,
    OpenYAMM::Game::Mm9ServiceKind serviceKind)
{
    OpenYAMM::Game::Party party = makeRuntimeParty();
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    CAPTURE(objectIndex);
    CAPTURE(objectName);
    CAPTURE(topicLabel);

    const OpenYAMM::Game::Mm9ObjectActivationResult activation =
        scriptRuntime.activateObject("testmap", objectIndex);
    REQUIRE(activation.activated);
    REQUIRE(activation.openedDialogue);
    CHECK(activation.directDialogue);
    CHECK(dialogueRuntime.owner().objectName == objectName);

    const OpenYAMM::Game::EventDialogContent content =
        OpenYAMM::Game::buildMm9DialogueContent(dialogueRuntime);
    const std::vector<OpenYAMM::Game::EventDialogAction>::const_iterator serviceAction =
        std::find_if(
            content.actions.begin(),
            content.actions.end(),
            [&](const OpenYAMM::Game::EventDialogAction &action)
            {
                return action.kind == OpenYAMM::Game::EventDialogActionKind::Mm9Topic
                    && action.label == topicLabel;
            });
    REQUIRE(serviceAction != content.actions.end());

    RecordingServiceRuntime handler = {};
    const OpenYAMM::Game::Mm9DialogueUiActionResult actionResult =
        OpenYAMM::Game::executeMm9DialogueAction(dialogueRuntime, *serviceAction, &handler);
    REQUIRE(actionResult.handled);
    REQUIRE(actionResult.selection.kind == OpenYAMM::Game::Mm9DialogueSelectionKind::Service);
    REQUIRE(actionResult.selection.serviceRequest.has_value());
    CHECK(actionResult.selection.serviceOpcode == opcode);
    CHECK(actionResult.selection.serviceRequest->opcode == opcode);
    CHECK(actionResult.selection.serviceRequest->kind == serviceKind);
    CHECK(actionResult.selection.serviceRequest->owner.mapId == "testmap");
    CHECK(actionResult.selection.serviceRequest->owner.objectIndex == objectIndex);
    CHECK(actionResult.selection.serviceRequest->owner.objectName == objectName);
    REQUIRE(handler.requests.size() == 1);
    CHECK(handler.requests[0].opcode == opcode);
    CHECK(handler.requests[0].kind == serviceKind);
    REQUIRE(handler.activeSession().has_value());
    CHECK(handler.activeSession()->active);
    CHECK(handler.activeSession()->status == OpenYAMM::Game::Mm9ServiceSessionStatus::OpenGeneratedContext);
    CHECK(handler.activeSession()->request.opcode == opcode);
    CHECK(handler.activeSession()->request.kind == serviceKind);
    CHECK(handler.activeSession()->request.rawColumns == handler.requests[0].rawColumns);
}
}

TEST_CASE("MM9 dialogue runtime evaluates RUDE key gates through mapped party qbits")
{
    const std::filesystem::path fixtureRoot = makeFixtureRoot();
    const OpenYAMM::Game::Mm9DialoguePackage package = loadFixturePackage(fixtureRoot);
    OpenYAMM::Game::Party party = {};
    OpenYAMM::Game::Mm9DialogueRuntime runtime(package, party);

    CHECK(OpenYAMM::Game::mm9KeyQbitIdForRawKey(44) == 9044);
    CHECK_FALSE(runtime.hasKey(44));
    CHECK_FALSE(party.hasQuestBit(9044));

    std::string error;
    REQUIRE(runtime.enterObject("testmap", 7, &error));
    CHECK(error.empty());
    CHECK(runtime.currentRudeId() == 1);
    CHECK(runtime.currentNodeId() == 1);
    CHECK(runtime.owner().mapId == "testmap");
    CHECK(runtime.owner().objectIndex == 7);
    CHECK(runtime.owner().scriptName == "DORUDE.scr");
    CHECK(runtime.owner().onRudeExitLabel == "OnRude");
    REQUIRE(runtime.owner().scriptParams.size() == 2);
    CHECK(runtime.owner().scriptParams[0] == "1");
    CHECK(runtime.owner().scriptParams[1] == "FixtureTarget");
    CHECK(runtime.owner().greetingSound == "greeting.wav");

    std::vector<OpenYAMM::Game::Mm9DialogueTopic> topics = runtime.visibleTopics();
    REQUIRE(topics.size() == 2);
    CHECK(topics[0].prompt == "Continue");
    CHECK(topics[1].prompt == "Bye");

    runtime.giveKey(44);
    CHECK(runtime.hasKey(44));
    CHECK(party.hasQuestBit(9044));

    topics = runtime.visibleTopics();
    REQUIRE(topics.size() == 3);
    CHECK(topics[0].prompt == "Continue");
    CHECK(topics[1].prompt == "Locked");
    CHECK(topics[2].prompt == "Bye");
    REQUIRE(topics[1].requiredKeys.size() == 1);
    CHECK(topics[1].requiredKeys[0].column == 7);
    CHECK(topics[1].requiredKeys[0].rawId == 44);
    CHECK(topics[1].requiredKeys[0].qbitId == 9044);
    CHECK(topics[1].requiredKeys[0].stateId == "mm9.keys.44");

    runtime.takeKey(44);
    CHECK_FALSE(runtime.hasKey(44));
    CHECK_FALSE(party.hasQuestBit(9044));

    std::error_code cleanupError;
    std::filesystem::remove_all(fixtureRoot, cleanupError);
}

TEST_CASE("MM9 dialogue visibility recomputes item and console variable conditions")
{
    const std::filesystem::path fixtureRoot = makeFixtureRoot();
    writeExtendedVisibilityDialogueFixture(fixtureRoot);

    const OpenYAMM::Game::Mm9DialoguePackage package = loadFixturePackage(fixtureRoot);
    REQUIRE(package.npcDialogues.count(4) == 1);
    const OpenYAMM::Game::Mm9GeneratedRudeDialogue &dialogue = package.npcDialogues.at(4);
    REQUIRE(dialogue.rows.size() == 5);
    REQUIRE(dialogue.rows[1].requiredItems.size() == 1);
    CHECK(dialogue.rows[1].requiredItems[0].column == 8);
    CHECK(dialogue.rows[1].requiredItems[0].itemId == 197);
    REQUIRE(dialogue.rows[2].requiredConsoleNumEquals.size() == 1);
    CHECK(dialogue.rows[2].requiredConsoleNumEquals[0].variable == "SCORE");
    CHECK(dialogue.rows[2].requiredConsoleNumEquals[0].value == 7);
    REQUIRE(dialogue.rows[3].requiredConsoleStrEquals.size() == 1);
    CHECK(dialogue.rows[3].requiredConsoleStrEquals[0].variable == "GREETING");
    CHECK(dialogue.rows[3].requiredConsoleStrEquals[0].value == "hello");

    OpenYAMM::Game::Party party = makeRuntimeParty();
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);
    REQUIRE(dialogueRuntime.enterRudeId(4));

    CHECK(visibleTopicPrompts(dialogueRuntime) == std::vector<std::string>{"Always"});

    REQUIRE(party.tryGrantItem(197));
    CHECK(visibleTopicPrompts(dialogueRuntime) == std::vector<std::string>{"Always", "Item gate"});

    scriptRuntime.setConsoleNumVar("SCORE", 6);
    CHECK(visibleTopicPrompts(dialogueRuntime) == std::vector<std::string>{"Always", "Item gate"});

    scriptRuntime.setConsoleNumVar("SCORE", 7);
    CHECK(visibleTopicPrompts(dialogueRuntime)
        == std::vector<std::string>{"Always", "Item gate", "Console num gate"});

    scriptRuntime.setConsoleStrVar("GREETING", "hello");
    CHECK(visibleTopicPrompts(dialogueRuntime)
        == std::vector<std::string>{
            "Always",
            "Item gate",
            "Console num gate",
            "Console str gate",
            "Combined gate"});

    scriptRuntime.setConsoleStrVar("GREETING", "bye");
    CHECK(visibleTopicPrompts(dialogueRuntime)
        == std::vector<std::string>{"Always", "Item gate", "Console num gate"});

    std::error_code cleanupError;
    std::filesystem::remove_all(fixtureRoot, cleanupError);
}

TEST_CASE("MM9 qbit reverse mapping covers full core key range")
{
    CHECK(OpenYAMM::Game::mm9KeyQbitIdForRawKey(44) == 9044);
    CHECK(OpenYAMM::Game::mm9RawKeyIdForQbit(9044) == 44);
    CHECK(OpenYAMM::Game::mm9QbitIdIsKeyMapping(9044));

    CHECK(OpenYAMM::Game::mm9KeyQbitIdForRawKey(5017) == 14017);
    CHECK(OpenYAMM::Game::mm9RawKeyIdForQbit(14017) == 5017);
    CHECK(OpenYAMM::Game::mm9QbitIdIsKeyMapping(14017));

    CHECK(OpenYAMM::Game::mm9KeyQbitIdForRawKey(0) == 0);
    CHECK(OpenYAMM::Game::mm9RawKeyIdForQbit(9000) == 0);
    CHECK_FALSE(OpenYAMM::Game::mm9QbitIdIsKeyMapping(9000));
}

TEST_CASE("MM9 scripted object hits preserve authored binding metadata through the interaction router")
{
    OpenYAMM::Game::Mm9InteractionObjectBinding binding = {};
    binding.mapId = "guberland";
    binding.objectId = "mm9:guberland:object:12";
    binding.sourceObjectIndex = 12;
    binding.sourceClass = "Guard";
    binding.sourceName = "DockGuard";
    binding.visualId = "mm9_guard";
    binding.scriptName = "guard.scr";
    binding.scriptParams = "patrol=1";
    binding.routerTargetIndex = 4;
    binding.hitPoint = {1.0f, 2.0f, 3.0f};
    binding.distance = 42.0f;

    const OpenYAMM::Game::GameplayWorldHit hit =
        OpenYAMM::Game::buildMm9ScriptedObjectWorldHit(binding);
    REQUIRE(hit.hasHit);
    REQUIRE(hit.kind == OpenYAMM::Game::GameplayWorldHitKind::EventTarget);
    REQUIRE(hit.eventTarget.has_value());
    CHECK(hit.eventTarget->targetKind == OpenYAMM::Game::GameplayWorldEventTargetKind::Object);
    CHECK(hit.eventTarget->targetIndex == 4);
    REQUIRE(hit.eventTarget->contextActionMetadata.has_value());
    CHECK(hit.eventTarget->contextActionMetadata->kind == "mm9_scripted_object");
    REQUIRE(hit.eventTarget->contextActionMetadata->targetMap.has_value());
    REQUIRE(hit.eventTarget->contextActionMetadata->mm9SourceObjectIndex.has_value());
    REQUIRE(hit.eventTarget->contextActionMetadata->mm9ScriptName.has_value());
    CHECK(*hit.eventTarget->contextActionMetadata->targetMap == "guberland");
    CHECK(*hit.eventTarget->contextActionMetadata->mm9SourceObjectIndex == 12);
    CHECK(*hit.eventTarget->contextActionMetadata->mm9ScriptName == "guard.scr");

    const std::optional<OpenYAMM::Game::Mm9InteractionObjectBinding> roundTripped =
        OpenYAMM::Game::mm9InteractionObjectBindingFromWorldHit(hit);
    REQUIRE(roundTripped.has_value());
    CHECK(roundTripped->mapId == binding.mapId);
    CHECK(roundTripped->objectId == binding.objectId);
    CHECK(roundTripped->sourceObjectIndex == binding.sourceObjectIndex);
    CHECK(roundTripped->sourceClass == binding.sourceClass);
    CHECK(roundTripped->sourceName == binding.sourceName);
    CHECK(roundTripped->visualId == binding.visualId);
    CHECK(roundTripped->scriptName == binding.scriptName);
    CHECK(roundTripped->scriptParams == binding.scriptParams);
    CHECK(roundTripped->routerTargetIndex == binding.routerTargetIndex);
    CHECK(roundTripped->hitPoint.x == doctest::Approx(binding.hitPoint.x));
    CHECK(roundTripped->distance == doctest::Approx(binding.distance));
}

TEST_CASE("MM9 generated Lua script runtime keeps object and trigger state distinct")
{
    const std::filesystem::path fixtureRoot = makeFixtureRoot();
    const OpenYAMM::Game::Mm9DialoguePackage package = loadFixturePackage(fixtureRoot);
    OpenYAMM::Game::Party party = {};
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    REQUIRE(dialogueRuntime.enterObject("testmap", 7));

    std::optional<std::string> error;
    REQUIRE(scriptRuntime.runLabel("DORUDE.scr", "ObjectState", error));
    CHECK_FALSE(error.has_value());

    CHECK(scriptRuntime.getScriptNumVar("npc_id") == 1);
    CHECK(scriptRuntime.getScriptStrVar("npc_id") == "1");
    CHECK(scriptRuntime.getScriptStrVar("target_name") == "FixtureTarget");
    CHECK(scriptRuntime.getObjectHandleVar("npc_object") == "mm9:testmap:object:7");
    CHECK(scriptRuntime.getObjectNumberProperty("testmap:7:NeedsTick") == 12);
    REQUIRE(scriptRuntime.state().objectNumberProperties.size() == 1);
    REQUIRE(scriptRuntime.state().objectHandleVars.size() == 1);
    REQUIRE(scriptRuntime.state().triggers.size() == 1);
    REQUIRE(scriptRuntime.state().triggerDispatches.size() == 2);
    CHECK(scriptRuntime.state().triggers[0].scriptSource == "DORUDE.scr");
    CHECK(scriptRuntime.state().triggers[0].mapId == "testmap");
    CHECK(scriptRuntime.state().triggers[0].objectIndex == 7);
    CHECK(scriptRuntime.state().triggers[0].triggerName == "Use");
    CHECK(scriptRuntime.state().triggers[0].label == "OnUse");
    CHECK(scriptRuntime.state().triggerDispatches[0].scriptSource == "DORUDE.scr");
    CHECK(scriptRuntime.state().triggerDispatches[0].mapId == "testmap");
    CHECK(scriptRuntime.state().triggerDispatches[0].objectIndex == 7);
    CHECK(scriptRuntime.state().triggerDispatches[0].targetHandle == "mm9:testmap:object:7");
    CHECK(scriptRuntime.state().triggerDispatches[0].message == "GoToLoc");
    CHECK(scriptRuntime.state().triggerDispatches[1].targetHandle == "mm9:testmap:object:7");
    CHECK(scriptRuntime.state().triggerDispatches[1].message == "Use");
    CHECK(scriptRuntime.getConsoleNumVar("SCORE", 0) == 7);
    CHECK(scriptRuntime.getScriptNumVar("SCORE_OUT", 0) == 7);
    CHECK(scriptRuntime.getConsoleStrVar("GREETING") == "hello");
    CHECK(scriptRuntime.getScriptStrVar("GREETING_OUT") == "hello");
    REQUIRE(scriptRuntime.keyAccesses().size() == 1);
    CHECK(scriptRuntime.keyAccesses()[0].operation == "hasKey");
    CHECK(scriptRuntime.keyAccesses()[0].rawKeyId == 44);
    CHECK(scriptRuntime.partyAccesses().empty());
    REQUIRE(scriptRuntime.unimplementedCommands().size() == 1);
    CHECK(scriptRuntime.unimplementedCommands()[0].command == "mysteryop");
    CHECK(dialogueRuntime.owner().objectIndex == 7);

    std::error_code cleanupError;
    std::filesystem::remove_all(fixtureRoot, cleanupError);
}

TEST_CASE("MM9 object activation runs linked scripts and preserves dialogue owner context")
{
    const std::filesystem::path fixtureRoot = makeFixtureRoot();
    const OpenYAMM::Game::Mm9DialoguePackage package = loadFixturePackage(fixtureRoot);
    OpenYAMM::Game::Party party = {};
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    const OpenYAMM::Game::Mm9ObjectActivationResult result = scriptRuntime.activateObject("testmap", 7);
    CHECK(result.activated);
    CHECK(result.ranScript);
    CHECK(result.openedDialogue);
    CHECK_FALSE(result.directDialogue);
    CHECK(result.queuedGreetingSound);
    CHECK(result.error.empty());
    REQUIRE(result.audioRequest.has_value());
    CHECK(result.audioRequest->mapId == "testmap");
    CHECK(result.audioRequest->objectIndex == 7);
    CHECK(result.audioRequest->objectName == "Fixture NPC");
    CHECK(result.audioRequest->scriptSource == "DORUDE.scr");
    CHECK(result.audioRequest->soundName == "greeting.wav");
    REQUIRE(scriptRuntime.audioRequests().size() == 1);
    CHECK(scriptRuntime.audioRequests()[0].soundName == "greeting.wav");

    CHECK(dialogueRuntime.currentRudeId() == 1);
    CHECK(dialogueRuntime.currentNodeId() == 1);
    CHECK(dialogueRuntime.owner().mapId == "testmap");
    CHECK(dialogueRuntime.owner().objectIndex == 7);
    CHECK(dialogueRuntime.owner().objectName == "Fixture NPC");
    CHECK(dialogueRuntime.owner().scriptName == "DORUDE.scr");
    CHECK(dialogueRuntime.owner().greetingSound == "greeting.wav");
    CHECK(dialogueRuntime.owner().onRudeExitLabel == "OnRude");
    REQUIRE(dialogueRuntime.owner().scriptParams.size() == 2);
    CHECK(dialogueRuntime.owner().scriptParams[0] == "1");
    CHECK(dialogueRuntime.owner().scriptParams[1] == "FixtureTarget");

    REQUIRE(scriptRuntime.keyAccesses().size() == 1);
    CHECK(scriptRuntime.keyAccesses()[0].operation == "hasKey");
    CHECK(scriptRuntime.keyAccesses()[0].rawKeyId == 44);
    CHECK(scriptRuntime.keyAccesses()[0].qbitId == 9044);
    CHECK_FALSE(scriptRuntime.keyAccesses()[0].result);
    CHECK(scriptRuntime.getConsoleNumVar("SCORE") == 7);
    CHECK(scriptRuntime.getConsoleStrVar("GREETING") == "hello");
    REQUIRE(scriptRuntime.unimplementedCommands().size() == 1);
    CHECK(scriptRuntime.unimplementedCommands()[0].scriptSource == "DORUDE.scr");
    CHECK(scriptRuntime.unimplementedCommands()[0].command == "mysteryop");

    const std::vector<OpenYAMM::Game::Mm9DialogueTopic> topics = dialogueRuntime.visibleTopics();
    REQUIRE(topics.size() == 2);
    CHECK(topics[0].prompt == "Continue");
    CHECK(topics[1].prompt == "Bye");

    std::error_code cleanupError;
    std::filesystem::remove_all(fixtureRoot, cleanupError);
}

TEST_CASE("MM9 selected world hit resolves to generated object binding and opens dialogue")
{
    const std::filesystem::path fixtureRoot = makeFixtureRoot();
    const OpenYAMM::Game::Mm9DialoguePackage package = loadFixturePackage(fixtureRoot);
    OpenYAMM::Game::Party party = {};
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    OpenYAMM::Game::Mm9InteractionObjectBinding binding = {};
    binding.mapId = "testmap";
    binding.objectId = "mm9:testmap:object:7";
    binding.sourceObjectIndex = 7;
    binding.sourceClass = "NPC";
    binding.sourceName = "Fixture NPC";
    binding.visualId = "fixture_npc";
    binding.scriptName = "DORUDE.scr";
    binding.scriptParams = "1 FixtureTarget";
    binding.routerTargetIndex = 0;
    binding.hitPoint = {10.0f, 20.0f, 30.0f};
    binding.distance = 64.0f;

    const OpenYAMM::Game::GameplayWorldHit hit =
        OpenYAMM::Game::buildMm9ScriptedObjectWorldHit(binding);
    const OpenYAMM::Game::Mm9ObjectActivationResult result = scriptRuntime.activateObject(hit);

    CHECK(result.activated);
    CHECK(result.ranScript);
    CHECK(result.openedDialogue);
    CHECK(result.error.empty());
    CHECK(dialogueRuntime.currentRudeId() == 1);
    CHECK(dialogueRuntime.owner().mapId == "testmap");
    CHECK(dialogueRuntime.owner().objectIndex == 7);
    CHECK(dialogueRuntime.owner().objectName == "Fixture NPC");
    CHECK(dialogueRuntime.owner().scriptName == "DORUDE.scr");

    const std::vector<OpenYAMM::Game::Mm9DialogueTopic> topics = dialogueRuntime.visibleTopics();
    REQUIRE(topics.size() == 2);
    CHECK(topics[0].prompt == "Continue");
    CHECK(topics[1].prompt == "Bye");

    OpenYAMM::Game::GameplayWorldHit nonMm9Hit = {};
    nonMm9Hit.hasHit = true;
    nonMm9Hit.kind = OpenYAMM::Game::GameplayWorldHitKind::Ground;
    const OpenYAMM::Game::Mm9ObjectActivationResult rejected = scriptRuntime.activateObject(nonMm9Hit);
    CHECK_FALSE(rejected.activated);
    CHECK(rejected.error == "selected world hit is not an MM9 dialogue-capable object");

    std::error_code cleanupError;
    std::filesystem::remove_all(fixtureRoot, cleanupError);
}

TEST_CASE("MM9 object activation falls back to direct RUDE and reports unresolved bindings")
{
    const std::filesystem::path fixtureRoot = makeFixtureRoot();
    const OpenYAMM::Game::Mm9DialoguePackage package = loadFixturePackage(fixtureRoot);
    OpenYAMM::Game::Party party = {};
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    OpenYAMM::Game::Mm9ObjectActivationResult result = scriptRuntime.activateObject("testmap", 8);
    CHECK(result.activated);
    CHECK_FALSE(result.ranScript);
    CHECK(result.openedDialogue);
    CHECK(result.directDialogue);
    CHECK_FALSE(result.queuedGreetingSound);
    CHECK(result.error.empty());
    CHECK(dialogueRuntime.currentRudeId() == 2);
    CHECK(dialogueRuntime.currentNodeId() == 2);
    CHECK(dialogueRuntime.owner().mapId == "testmap");
    CHECK(dialogueRuntime.owner().objectIndex == 8);
    CHECK(dialogueRuntime.owner().objectName == "Direct Bank NPC");
    CHECK(dialogueRuntime.owner().scriptName.empty());
    REQUIRE(dialogueRuntime.visibleTopics().size() == 13);

    result = scriptRuntime.activateObject("testmap", 9);
    CHECK(result.activated);
    CHECK_FALSE(result.ranScript);
    CHECK_FALSE(result.openedDialogue);
    CHECK_FALSE(result.directDialogue);
    CHECK(result.error == "MM9 dialogue binding has no resolved RUDE id");
    CHECK(dialogueRuntime.owner().objectIndex == 8);

    result = scriptRuntime.activateObject("testmap", 404);
    CHECK_FALSE(result.activated);
    CHECK(result.error == "MM9 dialogue binding was not found for selected object");

    std::error_code cleanupError;
    std::filesystem::remove_all(fixtureRoot, cleanupError);
}

TEST_CASE("MM9 direct bank object activation opens dialogue and dispatches bank service")
{
    const std::filesystem::path fixtureRoot = makeFixtureRoot();
    const OpenYAMM::Game::Mm9DialoguePackage package = loadFixturePackage(fixtureRoot);

    assertObjectDispatchesMm9Service(
        package,
        8,
        "Direct Bank NPC",
        "Bank",
        -6,
        OpenYAMM::Game::Mm9ServiceKind::Bank);

    std::error_code cleanupError;
    std::filesystem::remove_all(fixtureRoot, cleanupError);
}

TEST_CASE("MM9 direct service object activation opens generated service contexts")
{
    const std::filesystem::path fixtureRoot = makeFixtureRoot();
    const OpenYAMM::Game::Mm9DialoguePackage package = loadFixturePackage(fixtureRoot);

    assertObjectDispatchesMm9Service(
        package,
        10,
        "Direct Shop NPC",
        "Shop",
        -2,
        OpenYAMM::Game::Mm9ServiceKind::Shop);
    assertObjectDispatchesMm9Service(
        package,
        11,
        "Direct Training NPC",
        "Training",
        -3,
        OpenYAMM::Game::Mm9ServiceKind::Training);
    assertObjectDispatchesMm9Service(
        package,
        12,
        "Direct Skill Training NPC",
        "Skill training",
        -4,
        OpenYAMM::Game::Mm9ServiceKind::SkillTraining);
    assertObjectDispatchesMm9Service(
        package,
        13,
        "Direct Travel NPC",
        "Travel",
        -5,
        OpenYAMM::Game::Mm9ServiceKind::Travel);
    assertObjectDispatchesMm9Service(
        package,
        14,
        "Direct Inn NPC",
        "Inn",
        -7,
        OpenYAMM::Game::Mm9ServiceKind::Inn);
    assertObjectDispatchesMm9Service(
        package,
        15,
        "Direct Healer NPC",
        "Healer",
        -8,
        OpenYAMM::Game::Mm9ServiceKind::Healer);
    assertObjectDispatchesMm9Service(
        package,
        16,
        "Direct Hire NPC",
        "Hire",
        -10,
        OpenYAMM::Game::Mm9ServiceKind::Hire);
    assertObjectDispatchesMm9Service(
        package,
        16,
        "Direct Hire NPC",
        "Dismiss",
        -11,
        OpenYAMM::Game::Mm9ServiceKind::Dismiss);
    assertObjectDispatchesMm9Service(
        package,
        10,
        "Direct Shop NPC",
        "Item combine",
        -13,
        OpenYAMM::Game::Mm9ServiceKind::ItemCombine);
    assertObjectDispatchesMm9Service(
        package,
        10,
        "Direct Shop NPC",
        "Town portal",
        -15,
        OpenYAMM::Game::Mm9ServiceKind::TownPortal);
    assertObjectDispatchesMm9Service(
        package,
        10,
        "Direct Shop NPC",
        "Donation",
        -16,
        OpenYAMM::Game::Mm9ServiceKind::Donation);

    std::error_code cleanupError;
    std::filesystem::remove_all(fixtureRoot, cleanupError);
}

TEST_CASE("MM9 quest handoff service remains preserved as an explicitly pending opcode")
{
    const std::filesystem::path fixtureRoot = makeFixtureRoot();
    const OpenYAMM::Game::Mm9DialoguePackage package = loadFixturePackage(fixtureRoot);

    OpenYAMM::Game::Party party = {};
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    REQUIRE(scriptRuntime.activateObject("testmap", 10).openedDialogue);
    const OpenYAMM::Game::EventDialogContent content =
        OpenYAMM::Game::buildMm9DialogueContent(dialogueRuntime);
    const std::vector<OpenYAMM::Game::EventDialogAction>::const_iterator handoffAction =
        std::find_if(
            content.actions.begin(),
            content.actions.end(),
            [](const OpenYAMM::Game::EventDialogAction &action)
            {
                return action.kind == OpenYAMM::Game::EventDialogActionKind::Mm9Topic
                    && action.label == "Quest handoff";
            });
    REQUIRE(handoffAction != content.actions.end());

    RecordingServiceRuntime handler = {};
    const OpenYAMM::Game::Mm9DialogueUiActionResult actionResult =
        OpenYAMM::Game::executeMm9DialogueAction(dialogueRuntime, *handoffAction, &handler);
    REQUIRE(actionResult.handled);
    REQUIRE(actionResult.selection.kind == OpenYAMM::Game::Mm9DialogueSelectionKind::Service);
    REQUIRE(actionResult.selection.serviceRequest.has_value());
    CHECK(actionResult.selection.serviceOpcode == -14);
    CHECK(actionResult.selection.serviceRequest->opcode == -14);
    CHECK(actionResult.selection.serviceRequest->kind == OpenYAMM::Game::Mm9ServiceKind::QuestHandoff);
    CHECK(actionResult.selection.serviceRequest->name == "quest_handoff");
    CHECK(actionResult.selection.serviceRequest->rawColumns.size() == 30);
    REQUIRE(handler.requests.size() == 1);
    CHECK(handler.requests[0].opcode == -14);
    CHECK(handler.requests[0].kind == OpenYAMM::Game::Mm9ServiceKind::QuestHandoff);
    REQUIRE(handler.activeSession().has_value());
    CHECK(handler.activeSession()->status == OpenYAMM::Game::Mm9ServiceSessionStatus::PendingExactRuntimeSemantics);

    std::error_code cleanupError;
    std::filesystem::remove_all(fixtureRoot, cleanupError);
}

TEST_CASE("MM9 generated world package opens authored quest NPC from scene object activation")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    OpenYAMM::Engine::AssetFileSystem assetFileSystem = {};
    REQUIRE(assetFileSystem.initialize(
        sourceRoot,
        sourceRoot / "assets_dev",
        OpenYAMM::Engine::AssetScaleTier::X1,
        "mm9"));

    const std::optional<std::string> sceneText =
        assetFileSystem.readTextFile("worlds/mm9/maps/afterworld.scene.yml");
    REQUIRE(sceneText.has_value());

    std::string sceneError;
    OpenYAMM::Game::OutdoorSceneYmlLoader sceneLoader = {};
    const std::optional<OpenYAMM::Game::OutdoorSceneData> sceneData =
        sceneLoader.loadFromText(*sceneText, sceneError);
    REQUIRE_MESSAGE(sceneData.has_value(), sceneError);

    const OpenYAMM::Game::OutdoorSceneModelInstance *pTryggvaInstance = nullptr;
    for (const OpenYAMM::Game::OutdoorSceneModelInstance &modelInstance : sceneData->modelInstances)
    {
        if (modelInstance.sourceObjectIndex == 96)
        {
            pTryggvaInstance = &modelInstance;
            break;
        }
    }
    REQUIRE(pTryggvaInstance != nullptr);
    CHECK(pTryggvaInstance->instanceId == "mm9:afterworld:object:96");
    CHECK(pTryggvaInstance->sourceClass == "TryggvaRavenlocks");
    CHECK(pTryggvaInstance->sourceName == "TryggvaRavenlocks0");

    OpenYAMM::Game::Mm9DialoguePackage package = {};
    REQUIRE(OpenYAMM::Game::loadMm9DialoguePackage(assetFileSystem, package));
    REQUIRE(package.errors.empty());

    const OpenYAMM::Game::Mm9GeneratedObjectDialogueBinding *pBinding = nullptr;
    for (const OpenYAMM::Game::Mm9GeneratedObjectDialogueBinding &binding : package.objectBindings)
    {
        if (binding.mapId == "afterworld" && binding.objectIndex == 96)
        {
            pBinding = &binding;
            break;
        }
    }
    REQUIRE(pBinding != nullptr);
    CHECK(pBinding->dialogueCapable);
    REQUIRE(pBinding->rudeId.has_value());
    CHECK(*pBinding->rudeId == 180);
    CHECK(pBinding->objectName == pTryggvaInstance->sourceName);

    OpenYAMM::Game::Party party = {};
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    const OpenYAMM::Game::Mm9ObjectActivationResult activation =
        scriptRuntime.activateObject("afterworld", static_cast<int32_t>(pTryggvaInstance->sourceObjectIndex));
    REQUIRE(activation.activated);
    REQUIRE(activation.openedDialogue);
    CHECK(activation.directDialogue);
    CHECK(dialogueRuntime.currentRudeId() == 180);
    CHECK(dialogueRuntime.currentNodeId() == 180);
    CHECK(dialogueRuntime.owner().mapId == "afterworld");
    CHECK(dialogueRuntime.owner().objectIndex == 96);
    CHECK(dialogueRuntime.owner().objectName == "TryggvaRavenlocks0");

    const OpenYAMM::Game::EventDialogContent content =
        OpenYAMM::Game::buildMm9DialogueContent(dialogueRuntime);
    CHECK(content.isActive);
    CHECK(content.sourceId == 180);
    CHECK(content.title == "TryggvaRavenlocks0");
    CHECK_FALSE(content.actions.empty());
}

TEST_CASE("MM9 generated journal render models surface quests notes and awards")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    OpenYAMM::Engine::AssetFileSystem assetFileSystem = {};
    REQUIRE(assetFileSystem.initialize(
        sourceRoot,
        sourceRoot / "assets_dev",
        OpenYAMM::Engine::AssetScaleTier::X1,
        "mm9"));

    OpenYAMM::Game::Mm9DialoguePackage package = {};
    REQUIRE(OpenYAMM::Game::loadMm9DialoguePackage(assetFileSystem, package));
    REQUIRE(package.errors.empty());

    OpenYAMM::Game::Party party = makeRuntimeParty();
    std::vector<OpenYAMM::Game::Mm9JournalRenderEntry> quests =
        OpenYAMM::Game::buildMm9QuestRenderEntries(package, party);
    std::vector<OpenYAMM::Game::Mm9JournalRenderEntry> notes =
        OpenYAMM::Game::buildMm9NoteRenderEntries(package, party);
    REQUIRE(quests.size() == 143);
    REQUIRE(notes.size() == 91);

    CHECK(quests[0].source.file == "NPC997.rude");
    CHECK(quests[0].source.row == 1);
    CHECK(quests[0].entryId == 1);
    CHECK(quests[0].title == "Complete your training.");
    CHECK(quests[0].text.find("The Old Man believes you are finally ready") != std::string::npos);
    REQUIRE(quests[0].stateRefs.size() == 1);
    CHECK(quests[0].stateRefs[0].rawId == 473);
    CHECK(quests[0].stateRefs[0].qbitId == OpenYAMM::Game::mm9KeyQbitIdForRawKey(473));
    CHECK_FALSE(quests[0].visible);

    CHECK(notes[0].source.file == "NPC998.rude");
    CHECK(notes[0].title == "Red Barrels increase Might.");
    CHECK(notes[0].text.empty());
    REQUIRE(notes[0].stateRefs.size() == 1);
    CHECK(notes[0].stateRefs[0].rawId == 2000);
    CHECK_FALSE(notes[0].visible);

    party.setQuestBit(OpenYAMM::Game::mm9KeyQbitIdForRawKey(473), true);
    party.setQuestBit(OpenYAMM::Game::mm9KeyQbitIdForRawKey(2000), true);
    quests = OpenYAMM::Game::buildMm9QuestRenderEntries(package, party);
    notes = OpenYAMM::Game::buildMm9NoteRenderEntries(package, party);
    CHECK(quests[0].visible);
    CHECK(notes[0].visible);

    party.addAward(0, 27);
    const std::vector<OpenYAMM::Game::Mm9AwardRenderEntry> awards =
        OpenYAMM::Game::buildMm9AwardRenderEntries(package, party, 0);
    const std::vector<OpenYAMM::Game::Mm9AwardRenderEntry>::const_iterator dragonflyAward =
        std::find_if(
            awards.begin(),
            awards.end(),
            [](const OpenYAMM::Game::Mm9AwardRenderEntry &entry)
            {
                return entry.awardId == 27;
            });
    REQUIRE(dragonflyAward != awards.end());
    CHECK(dragonflyAward->source.file == "NPC999.rude");
    CHECK(dragonflyAward->text == "Killed the Dragonflies.");
    CHECK(dragonflyAward->visible);
}

TEST_CASE("MM9 runtime integration does not emit generated artifacts outside the world tree")
{
    const std::filesystem::path fixtureRoot = makeFixtureRoot();
    CHECK(generatedMm9ArtifactsOutsideWorldTree(fixtureRoot).empty());

    const OpenYAMM::Game::Mm9DialoguePackage package = loadFixturePackage(fixtureRoot);
    OpenYAMM::Game::Party party = makeRuntimeParty();
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    REQUIRE(scriptRuntime.activateObject("testmap", 7).openedDialogue);
    OpenYAMM::Game::EventDialogContent content = OpenYAMM::Game::buildMm9DialogueContent(dialogueRuntime);
    REQUIRE(content.actions.size() == 2);
    OpenYAMM::Game::Mm9DialogueUiActionResult actionResult =
        OpenYAMM::Game::executeMm9DialogueAction(dialogueRuntime, content.actions[0]);
    REQUIRE(actionResult.handled);

    OpenYAMM::Game::GameSaveData saveData = {};
    saveData.mapFileName = "testmap.mm9";
    saveData.party = party.snapshot();
    saveData.mm9ScriptState = scriptRuntime.state();

    std::string saveError;
    REQUIRE(OpenYAMM::Game::saveGameDataToPath(fixtureRoot / "runtime_scope.oysav", saveData, saveError));

    const std::vector<std::string> leakedGeneratedArtifacts =
        generatedMm9ArtifactsOutsideWorldTree(fixtureRoot);
    CHECK(leakedGeneratedArtifacts.empty());

    std::error_code cleanupError;
    std::filesystem::remove_all(fixtureRoot, cleanupError);
}

TEST_CASE("MM9 dialogue UI adapter exposes topics and selected responses through event dialog content")
{
    const std::filesystem::path fixtureRoot = makeFixtureRoot();
    const OpenYAMM::Game::Mm9DialoguePackage package = loadFixturePackage(fixtureRoot);
    OpenYAMM::Game::Party party = {};
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    REQUIRE(scriptRuntime.activateObject("testmap", 7).openedDialogue);

    OpenYAMM::Game::EventDialogContent content = OpenYAMM::Game::buildMm9DialogueContent(dialogueRuntime);
    CHECK(content.isActive);
    CHECK_FALSE(content.isHouseDialog);
    CHECK(content.sourceId == 1);
    CHECK(content.title == "Fixture NPC");
    CHECK(content.lines.empty());
    REQUIRE(content.actions.size() == 2);
    CHECK(content.actions[0].kind == OpenYAMM::Game::EventDialogActionKind::Mm9Topic);
    CHECK(content.actions[0].id == 0);
    CHECK(content.actions[0].secondaryId > 0);
    CHECK(content.actions[0].label == "Continue");
    CHECK(content.actions[0].argument == "choice=1;next=2");
    CHECK(content.actions[1].label == "Bye");

    OpenYAMM::Game::Mm9DialogueUiActionResult actionResult =
        OpenYAMM::Game::executeMm9DialogueAction(dialogueRuntime, content.actions[0]);
    CHECK(actionResult.handled);
    CHECK(actionResult.selection.kind == OpenYAMM::Game::Mm9DialogueSelectionKind::GotoNode);
    CHECK(actionResult.selection.response == "Go to service node");
    CHECK(dialogueRuntime.currentNodeId() == 2);
    CHECK(actionResult.content.isActive);
    REQUIRE(actionResult.content.lines.size() == 1);
    CHECK(actionResult.content.lines[0] == "Go to service node");
    REQUIRE(actionResult.content.actions.size() == 1);
    CHECK(actionResult.content.actions[0].label == "Bank");
    CHECK(actionResult.content.actions[0].argument == "choice=1;next=-6");

    RecordingServiceHandler handler = {};
    actionResult = OpenYAMM::Game::executeMm9DialogueAction(
        dialogueRuntime,
        actionResult.content.actions[0],
        &handler);
    CHECK(actionResult.handled);
    CHECK(actionResult.selection.kind == OpenYAMM::Game::Mm9DialogueSelectionKind::Service);
    CHECK(actionResult.selection.response == "Open bank");
    REQUIRE(actionResult.content.lines.size() == 1);
    CHECK(actionResult.content.lines[0] == "Open bank");
    REQUIRE(handler.requests.size() == 1);
    CHECK(handler.requests[0].kind == OpenYAMM::Game::Mm9ServiceKind::Bank);
    CHECK(handler.requests[0].owner.mapId == "testmap");
    CHECK(handler.requests[0].owner.objectIndex == 7);

    std::error_code cleanupError;
    std::filesystem::remove_all(fixtureRoot, cleanupError);
}

TEST_CASE("MM9 dialogue topic clicks route through the gameplay dialog controller")
{
    OpenYAMM::Game::GameplayUiController uiController = {};
    OpenYAMM::Game::EventRuntimeState eventRuntimeState = {};
    OpenYAMM::Game::EventDialogContent activeDialog = {};
    size_t selectionIndex = 0;
    Mm9DialogRoutingWorldRuntime worldRuntime = {};

    activeDialog.isActive = true;
    activeDialog.title = "Original MM9 dialog";
    activeDialog.actions.push_back({
        .kind = OpenYAMM::Game::EventDialogActionKind::Mm9Topic,
        .id = 17,
        .secondaryId = 123,
        .label = "Ask",
        .argument = "choice=1;next=2",
    });

    worldRuntime.nextContent.isActive = true;
    worldRuntime.nextContent.title = "Updated MM9 dialog";
    worldRuntime.nextContent.lines.push_back("Answer");

    OpenYAMM::Game::GameplayDialogController::Context context = {
        .uiController = uiController,
        .eventRuntimeState = eventRuntimeState,
        .activeEventDialog = activeDialog,
        .selectionIndex = selectionIndex,
        .pWorldRuntime = &worldRuntime,
    };

    const OpenYAMM::Game::GameplayDialogController controller = {};
    const OpenYAMM::Game::GameplayDialogController::Result result =
        controller.executeActiveDialogAction(context);

    CHECK(worldRuntime.executedActionCount == 1);
    CHECK(worldRuntime.capturedAction.kind == OpenYAMM::Game::EventDialogActionKind::Mm9Topic);
    CHECK(worldRuntime.capturedAction.id == 17);
    CHECK(activeDialog.title == "Updated MM9 dialog");
    REQUIRE(activeDialog.lines.size() == 1);
    CHECK(activeDialog.lines[0] == "Answer");
    CHECK_FALSE(result.shouldCloseActiveDialog);
}

TEST_CASE("MM9 dialogue registration leaves legacy NPC topic routing on the normal provider path")
{
    OpenYAMM::Game::GameplayUiController uiController = {};
    OpenYAMM::Game::EventRuntimeState eventRuntimeState = {};
    OpenYAMM::Game::EventDialogContent activeDialog = {};
    size_t selectionIndex = 0;
    Mm9DialogRoutingWorldRuntime worldRuntime = {};

    eventRuntimeState.messages.push_back("previous");
    activeDialog.isActive = true;
    activeDialog.sourceId = 42;
    activeDialog.title = "Legacy NPC dialog";
    activeDialog.actions.push_back({
        .kind = OpenYAMM::Game::EventDialogActionKind::NpcTopic,
        .id = 123,
        .secondaryId = 0,
        .label = "Ask legacy topic",
    });

    OpenYAMM::Game::GameplayDialogController::Context context = {
        .uiController = uiController,
        .eventRuntimeState = eventRuntimeState,
        .activeEventDialog = activeDialog,
        .selectionIndex = selectionIndex,
        .pWorldRuntime = &worldRuntime,
    };

    const OpenYAMM::Game::GameplayDialogController controller = {};
    const OpenYAMM::Game::GameplayDialogController::Result result =
        controller.executeActiveDialogAction(context);

    CHECK(worldRuntime.executedActionCount == 0);
    CHECK(worldRuntime.executedNpcTopicCount == 1);
    CHECK(worldRuntime.capturedNpcTopicEventId == 123);
    CHECK(worldRuntime.capturedPreviousMessageCount == 1);
    CHECK_FALSE(worldRuntime.capturedContinueStep.has_value());
    CHECK(activeDialog.title == "Legacy NPC dialog");
    CHECK(activeDialog.actions[0].kind == OpenYAMM::Game::EventDialogActionKind::NpcTopic);
    CHECK(result.shouldOpenPendingEventDialog);
    CHECK_FALSE(result.shouldCloseActiveDialog);
}

TEST_CASE("MM9 gameplay dialogue close branch runs OnRudeExit and mutates mapped qbits")
{
    const std::filesystem::path fixtureRoot = makeFixtureRoot();
    const OpenYAMM::Game::Mm9DialoguePackage package = loadFixturePackage(fixtureRoot);
    OpenYAMM::Game::Party party = {};
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    REQUIRE(scriptRuntime.activateObject("testmap", 7).openedDialogue);
    CHECK_FALSE(party.hasQuestBit(9044));

    OpenYAMM::Game::GameplayUiController uiController = {};
    OpenYAMM::Game::EventRuntimeState eventRuntimeState = {};
    OpenYAMM::Game::EventDialogContent activeDialog =
        OpenYAMM::Game::buildMm9DialogueContent(dialogueRuntime);
    REQUIRE(activeDialog.actions.size() == 2);
    REQUIRE(activeDialog.actions[1].label == "Bye");

    size_t selectionIndex = 1;
    Mm9DialogCallbackWorldRuntime worldRuntime(dialogueRuntime, scriptRuntime);
    OpenYAMM::Game::GameplayDialogController::Context context = {
        .uiController = uiController,
        .eventRuntimeState = eventRuntimeState,
        .activeEventDialog = activeDialog,
        .selectionIndex = selectionIndex,
        .pWorldRuntime = &worldRuntime,
    };

    const OpenYAMM::Game::GameplayDialogController controller = {};
    const OpenYAMM::Game::GameplayDialogController::Result result =
        controller.executeActiveDialogAction(context);

    CHECK(worldRuntime.executedActionCount == 1);
    CHECK(worldRuntime.executedCloseCallbackCount == 1);
    CHECK(worldRuntime.callbackScript == "DORUDE.scr");
    CHECK(worldRuntime.callbackLabel == "OnRude");
    CHECK(party.hasQuestBit(9044));
    REQUIRE(scriptRuntime.keyAccesses().size() == 2);
    CHECK(scriptRuntime.keyAccesses()[1].operation == "giveKey");
    CHECK(scriptRuntime.keyAccesses()[1].rawKeyId == 44);
    CHECK(scriptRuntime.keyAccesses()[1].qbitId == 9044);
    CHECK(activeDialog.isActive);
    REQUIRE(activeDialog.lines.size() == 1);
    CHECK(activeDialog.lines[0] == "Goodbye");
    CHECK(activeDialog.actions.empty());
    CHECK_FALSE(result.shouldCloseActiveDialog);

    std::error_code cleanupError;
    std::filesystem::remove_all(fixtureRoot, cleanupError);
}

TEST_CASE("MM9 dialogue UI adapter keeps closing response visible without live topics")
{
    const std::filesystem::path fixtureRoot = makeFixtureRoot();
    const OpenYAMM::Game::Mm9DialoguePackage package = loadFixturePackage(fixtureRoot);
    OpenYAMM::Game::Party party = {};
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    REQUIRE(scriptRuntime.activateObject("testmap", 7).openedDialogue);

    OpenYAMM::Game::EventDialogContent content = OpenYAMM::Game::buildMm9DialogueContent(dialogueRuntime);
    REQUIRE(content.actions.size() == 2);
    OpenYAMM::Game::Mm9DialogueUiActionResult actionResult =
        OpenYAMM::Game::executeMm9DialogueAction(dialogueRuntime, content.actions[1]);
    CHECK(actionResult.handled);
    CHECK(actionResult.selection.kind == OpenYAMM::Game::Mm9DialogueSelectionKind::Close);
    CHECK(dialogueRuntime.closed());
    CHECK(actionResult.content.isActive);
    REQUIRE(actionResult.content.lines.size() == 1);
    CHECK(actionResult.content.lines[0] == "Goodbye");
    CHECK(actionResult.content.actions.empty());

    const OpenYAMM::Game::EventDialogContent closedContent =
        OpenYAMM::Game::buildMm9DialogueContent(dialogueRuntime);
    CHECK_FALSE(closedContent.isActive);

    std::error_code cleanupError;
    std::filesystem::remove_all(fixtureRoot, cleanupError);
}

TEST_CASE("MM9 runtime state domains do not alias keys maps console object properties or inventory")
{
    const std::filesystem::path fixtureRoot = makeFixtureRoot();
    const OpenYAMM::Game::Mm9DialoguePackage package = loadFixturePackage(fixtureRoot);
    OpenYAMM::Game::Party party = makeRuntimeParty();
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    REQUIRE(dialogueRuntime.enterObject("testmap", 7));

    scriptRuntime.setConsoleNumVar("SHARED", 10);
    scriptRuntime.setConsoleStrVar("SHARED", "console");
    scriptRuntime.setMapNumVar("testmap", "SHARED", 20);
    scriptRuntime.setMapStrVar("testmap", "SHARED", "map");
    scriptRuntime.setMapNumVar("othermap", "SHARED", 30);
    scriptRuntime.setScriptNumVar("SHARED", 40);
    scriptRuntime.setScriptStrVar("SHARED", "script");
    scriptRuntime.setObjectNumberProperty("SHARED", 50, 0);
    dialogueRuntime.giveKey(44);
    REQUIRE(party.tryGrantItem(197));

    CHECK(scriptRuntime.getConsoleNumVar("SHARED") == 10);
    CHECK(scriptRuntime.getConsoleStrVar("SHARED") == "console");
    CHECK(scriptRuntime.getMapNumVar("testmap", "SHARED") == 20);
    CHECK(scriptRuntime.getMapStrVar("testmap", "SHARED") == "map");
    CHECK(scriptRuntime.getMapNumVar("othermap", "SHARED") == 30);
    CHECK(scriptRuntime.getScriptNumVar("SHARED") == 40);
    CHECK(scriptRuntime.getScriptStrVar("SHARED") == "script");
    CHECK(scriptRuntime.getObjectNumberProperty("testmap:7:SHARED") == 50);
    CHECK(dialogueRuntime.hasKey(44));
    CHECK(party.hasQuestBit(9044));
    CHECK(party.hasItemAnywhere(197));
    CHECK(scriptRuntime.state().consoleNumVars.size() == 1);
    CHECK(scriptRuntime.state().mapNumVars.size() == 2);
    CHECK(scriptRuntime.state().scriptNumVars.size() == 1);
    CHECK(scriptRuntime.state().objectNumberProperties.size() == 1);

    std::error_code cleanupError;
    std::filesystem::remove_all(fixtureRoot, cleanupError);
}

TEST_CASE("MM9 dialogue runtime selects generated responses, services, and close callbacks")
{
    const std::filesystem::path fixtureRoot = makeFixtureRoot();
    const OpenYAMM::Game::Mm9DialoguePackage package = loadFixturePackage(fixtureRoot);
    OpenYAMM::Game::Party party = {};
    OpenYAMM::Game::Mm9DialogueRuntime runtime(package, party);

    REQUIRE(runtime.enterObject("testmap", 7));
    std::vector<OpenYAMM::Game::Mm9DialogueTopic> topics = runtime.visibleTopics();
    REQUIRE(topics.size() == 2);
    CHECK(topics[0].prompt == "Continue");

    OpenYAMM::Game::Mm9DialogueSelectionResult result = runtime.selectTopic(0);
    CHECK(result.kind == OpenYAMM::Game::Mm9DialogueSelectionKind::GotoNode);
    CHECK(result.response == "Go to service node");
    CHECK(runtime.currentNodeId() == 2);

    topics = runtime.visibleTopics();
    REQUIRE(topics.size() == 1);
    CHECK(topics[0].prompt == "Bank");
    result = runtime.selectTopic(0);
    CHECK(result.kind == OpenYAMM::Game::Mm9DialogueSelectionKind::Service);
    CHECK(result.serviceOpcode == -6);
    CHECK(result.serviceName == "bank");
    CHECK(result.response == "Open bank");
    CHECK_FALSE(runtime.closed());

    REQUIRE(runtime.enterObject("testmap", 7));
    runtime.giveKey(44);
    topics = runtime.visibleTopics();
    REQUIRE(topics.size() == 3);
    result = runtime.selectTopic(1);
    CHECK(result.kind == OpenYAMM::Game::Mm9DialogueSelectionKind::Close);
    CHECK(result.response == "QBit-gated response");
    CHECK(result.onRudeExitLabel == "OnRude");
    CHECK(result.owner.mapId == "testmap");
    CHECK(result.owner.objectIndex == 7);
    CHECK(runtime.closed());

    std::error_code cleanupError;
    std::filesystem::remove_all(fixtureRoot, cleanupError);
}

TEST_CASE("MM9 dialogue runtime treats node 999 and next zero explicitly")
{
    const std::filesystem::path fixtureRoot = makeFixtureRoot();
    const OpenYAMM::Game::Mm9DialoguePackage package = loadFixturePackage(fixtureRoot);
    OpenYAMM::Game::Party party = {};
    OpenYAMM::Game::Mm9DialogueRuntime runtime(package, party);

    REQUIRE(runtime.enterRudeId(3));
    CHECK(runtime.currentNodeId() == 3);

    std::vector<OpenYAMM::Game::Mm9DialogueTopic> topics = runtime.visibleTopics();
    REQUIRE(topics.size() == 2);
    CHECK(topics[0].prompt == "Go to node 999");
    CHECK(topics[0].next == 999);
    CHECK(topics[1].prompt == "Zero next");
    CHECK(topics[1].next == 0);

    OpenYAMM::Game::Mm9DialogueSelectionResult result = runtime.selectTopic(0);
    CHECK(result.kind == OpenYAMM::Game::Mm9DialogueSelectionKind::GotoNode);
    CHECK(result.next == 999);
    CHECK(result.response == "Node 999 response");
    CHECK(runtime.currentNodeId() == 999);
    CHECK_FALSE(runtime.closed());

    topics = runtime.visibleTopics();
    REQUIRE(topics.size() == 1);
    CHECK(topics[0].prompt == "Finish");
    result = runtime.selectTopic(0);
    CHECK(result.kind == OpenYAMM::Game::Mm9DialogueSelectionKind::Close);
    CHECK(result.response == "Finish response");
    CHECK(runtime.closed());

    REQUIRE(runtime.enterRudeId(3));
    result = runtime.selectTopic(1);
    CHECK(result.kind == OpenYAMM::Game::Mm9DialogueSelectionKind::UnresolvedZero);
    CHECK(result.next == 0);
    CHECK(result.response == "Zero response");
    CHECK(runtime.currentNodeId() == 3);
    CHECK_FALSE(runtime.closed());

    std::error_code cleanupError;
    std::filesystem::remove_all(fixtureRoot, cleanupError);
}

TEST_CASE("MM9 generated Lua script runtime opens dialogue and routes OnRudeExit through qbit keys")
{
    const std::filesystem::path fixtureRoot = makeFixtureRoot();
    const OpenYAMM::Game::Mm9DialoguePackage package = loadFixturePackage(fixtureRoot);
    OpenYAMM::Game::Party party = {};
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    CHECK(scriptRuntime.resolveRawKeyId("TEST_KEY") == 44);
    CHECK_FALSE(party.hasQuestBit(9044));

    std::optional<std::string> error;
    REQUIRE(scriptRuntime.runLabel("DORUDE.scr", "OnUse", error));
    CHECK_FALSE(error.has_value());

    CHECK(dialogueRuntime.currentRudeId() == 1);
    CHECK(dialogueRuntime.currentNodeId() == 1);
    CHECK(dialogueRuntime.owner().onRudeExitLabel == "OnRude");
    REQUIRE(scriptRuntime.registeredCallbacks().size() == 1);
    CHECK(scriptRuntime.registeredCallbacks()[0].scriptSource == "DORUDE.scr");
    CHECK(scriptRuntime.registeredCallbacks()[0].label == "OnRude");
    REQUIRE(scriptRuntime.state().registeredCallbacks.size() == 1);
    CHECK(scriptRuntime.state().registeredCallbacks[0].label == "OnRude");
    REQUIRE(scriptRuntime.keyAccesses().size() == 1);
    CHECK(scriptRuntime.keyAccesses()[0].operation == "hasKey");
    CHECK(scriptRuntime.keyAccesses()[0].rawKeyId == 44);
    CHECK(scriptRuntime.keyAccesses()[0].qbitId == 9044);
    CHECK_FALSE(scriptRuntime.keyAccesses()[0].result);
    CHECK(scriptRuntime.getConsoleNumVar("SCORE") == 7);
    CHECK(scriptRuntime.getConsoleStrVar("GREETING") == "hello");
    REQUIRE(scriptRuntime.state().consoleNumVars.size() == 1);
    REQUIRE(scriptRuntime.state().consoleStrVars.size() == 1);
    REQUIRE(scriptRuntime.unimplementedCommands().size() == 1);
    CHECK(scriptRuntime.unimplementedCommands()[0].scriptSource == "DORUDE.scr");
    CHECK(scriptRuntime.unimplementedCommands()[0].command == "mysteryop");
    CHECK(scriptRuntime.unimplementedCommands()[0].argumentsText == "7");

    const std::vector<OpenYAMM::Game::Mm9DialogueTopic> topics = dialogueRuntime.visibleTopics();
    REQUIRE(topics.size() == 2);
    REQUIRE(topics[1].prompt == "Bye");
    const OpenYAMM::Game::Mm9DialogueSelectionResult closeResult = dialogueRuntime.selectTopic(1);
    REQUIRE(closeResult.kind == OpenYAMM::Game::Mm9DialogueSelectionKind::Close);
    CHECK(closeResult.onRudeExitLabel == "OnRude");

    const OpenYAMM::Game::Mm9ScriptRuntimeCallback &callback = scriptRuntime.registeredCallbacks()[0];
    REQUIRE(scriptRuntime.runLabel(callback.scriptSource, callback.label, error));
    CHECK(party.hasQuestBit(9044));
    REQUIRE(scriptRuntime.keyAccesses().size() == 2);
    CHECK(scriptRuntime.keyAccesses()[1].operation == "giveKey");
    CHECK(scriptRuntime.keyAccesses()[1].rawKeyId == 44);
    CHECK(scriptRuntime.keyAccesses()[1].qbitId == 9044);

    std::error_code cleanupError;
    std::filesystem::remove_all(fixtureRoot, cleanupError);
}

TEST_CASE("MM9 qbit-backed key state survives save load and restores dialogue visibility")
{
    const std::filesystem::path fixtureRoot = makeFixtureRoot();
    const OpenYAMM::Game::Mm9DialoguePackage package = loadFixturePackage(fixtureRoot);
    OpenYAMM::Game::Party party = {};
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    std::optional<std::string> scriptError;
    REQUIRE(scriptRuntime.runLabel("DORUDE.scr", "OnUse", scriptError));
    REQUIRE(scriptRuntime.runLabel("DORUDE.scr", "OnRude", scriptError));
    REQUIRE(dialogueRuntime.enterObject("testmap", 7));
    REQUIRE(scriptRuntime.runLabel("DORUDE.scr", "ObjectState", scriptError));
    REQUIRE(scriptRuntime.runLabel("DORUDE.scr", "ScheduleWait", scriptError));
    scriptRuntime.setMapNumVar("testmap", "PUZZLE_STATE", 12);
    scriptRuntime.setMapStrVar("testmap", "LAST_NPC", "Fixture NPC");
    scriptRuntime.setMapNumVar("othermap", "PUZZLE_STATE", 99);
    CHECK(party.hasQuestBit(9044));

    OpenYAMM::Game::GameSaveData saveData = {};
    saveData.mapFileName = "testmap.mm9";
    saveData.party = party.snapshot();
    saveData.mm9ScriptState = scriptRuntime.state();

    const std::filesystem::path savePath = fixtureRoot / "mm9_dialogue_state.oysav";
    std::string saveError;
    REQUIRE(OpenYAMM::Game::saveGameDataToPath(savePath, saveData, saveError));

    const std::optional<OpenYAMM::Game::GameSaveData> loaded =
        OpenYAMM::Game::loadGameDataFromPath(savePath, saveError);
    REQUIRE(loaded.has_value());

    OpenYAMM::Game::Party restoredParty = {};
    restoredParty.restoreSnapshot(loaded->party);
    CHECK(restoredParty.hasQuestBit(9044));
    REQUIRE(loaded->mm9ScriptState.consoleNumVars.count("SCORE") == 1);
    REQUIRE(loaded->mm9ScriptState.consoleStrVars.count("GREETING") == 1);
    REQUIRE(loaded->mm9ScriptState.mapNumVars.count("testmap") == 1);
    REQUIRE(loaded->mm9ScriptState.mapStrVars.count("testmap") == 1);
    REQUIRE(loaded->mm9ScriptState.scriptNumVars.count("npc_id") == 1);
    REQUIRE(loaded->mm9ScriptState.scriptStrVars.count("target_name") == 1);
    REQUIRE(loaded->mm9ScriptState.objectHandleVars.count("npc_object") == 1);
    REQUIRE(loaded->mm9ScriptState.objectNumberProperties.count("testmap:7:NeedsTick") == 1);
    REQUIRE(loaded->mm9ScriptState.triggers.size() == 1);
    REQUIRE(loaded->mm9ScriptState.triggerDispatches.size() == 2);
    REQUIRE(loaded->mm9ScriptState.scheduledInvocations.size() == 1);
    REQUIRE(loaded->mm9ScriptState.registeredCallbacks.size() == 2);
    CHECK(loaded->mm9ScriptState.consoleNumVars.at("SCORE") == 7);
    CHECK(loaded->mm9ScriptState.consoleStrVars.at("GREETING") == "hello");
    CHECK(loaded->mm9ScriptState.mapNumVars.at("testmap").at("PUZZLE_STATE") == 12);
    CHECK(loaded->mm9ScriptState.mapStrVars.at("testmap").at("LAST_NPC") == "Fixture NPC");
    CHECK(loaded->mm9ScriptState.mapNumVars.at("othermap").at("PUZZLE_STATE") == 99);
    CHECK(loaded->mm9ScriptState.scriptNumVars.at("npc_id") == 1);
    CHECK(loaded->mm9ScriptState.scriptStrVars.at("target_name") == "FixtureTarget");
    CHECK(loaded->mm9ScriptState.objectHandleVars.at("npc_object") == "mm9:testmap:object:7");
    CHECK(loaded->mm9ScriptState.objectNumberProperties.at("testmap:7:NeedsTick") == 12);
    CHECK(loaded->mm9ScriptState.triggers[0].triggerName == "Use");
    CHECK(loaded->mm9ScriptState.triggerDispatches[0].targetHandle == "mm9:testmap:object:7");
    CHECK(loaded->mm9ScriptState.triggerDispatches[0].message == "GoToLoc");
    CHECK(loaded->mm9ScriptState.triggerDispatches[1].targetHandle == "mm9:testmap:object:7");
    CHECK(loaded->mm9ScriptState.triggerDispatches[1].message == "Use");
    CHECK(loaded->mm9ScriptState.scheduledInvocations[0].scriptSource == "DORUDE.scr");
    CHECK(loaded->mm9ScriptState.scheduledInvocations[0].label == "WaitDone");
    CHECK(loaded->mm9ScriptState.scheduledInvocations[0].dueTimeSeconds == 2.0);
    CHECK(loaded->mm9ScriptState.registeredCallbacks[0].label == "OnRude");
    CHECK(loaded->mm9ScriptState.registeredCallbacks[1].label == "OnRude");

    OpenYAMM::Game::Mm9DialogueRuntime restoredRuntime(package, restoredParty);
    OpenYAMM::Game::Mm9ScriptRuntime restoredScriptRuntime(package, restoredRuntime);
    restoredScriptRuntime.restoreState(loaded->mm9ScriptState);
    CHECK(restoredScriptRuntime.getConsoleNumVar("SCORE") == 7);
    CHECK(restoredScriptRuntime.getConsoleStrVar("GREETING") == "hello");
    CHECK(restoredScriptRuntime.getMapNumVar("testmap", "PUZZLE_STATE") == 12);
    CHECK(restoredScriptRuntime.getMapStrVar("testmap", "LAST_NPC") == "Fixture NPC");
    CHECK(restoredScriptRuntime.getMapNumVar("othermap", "PUZZLE_STATE") == 99);
    CHECK(restoredScriptRuntime.getMapNumVar("missing", "PUZZLE_STATE", -1) == -1);
    CHECK(restoredScriptRuntime.getScriptNumVar("npc_id") == 1);
    CHECK(restoredScriptRuntime.getScriptStrVar("target_name") == "FixtureTarget");
    CHECK(restoredScriptRuntime.getObjectHandleVar("npc_object") == "mm9:testmap:object:7");
    CHECK(restoredScriptRuntime.getObjectNumberProperty("testmap:7:NeedsTick") == 12);
    REQUIRE(restoredScriptRuntime.registeredCallbacks().size() == 2);
    CHECK(restoredScriptRuntime.registeredCallbacks()[0].label == "OnRude");
    REQUIRE(restoredScriptRuntime.advanceScriptTime(2.0, scriptError));
    CHECK(restoredScriptRuntime.getConsoleNumVar("WAIT_DONE") == 1);
    CHECK(restoredScriptRuntime.scheduledInvocations().empty());
    REQUIRE(restoredRuntime.enterObject("testmap", 7));
    const std::vector<OpenYAMM::Game::Mm9DialogueTopic> restoredTopics = restoredRuntime.visibleTopics();
    REQUIRE(restoredTopics.size() == 3);
    CHECK(restoredTopics[0].prompt == "Continue");
    CHECK(restoredTopics[1].prompt == "Locked");
    CHECK(restoredTopics[2].prompt == "Bye");

    std::error_code cleanupError;
    std::filesystem::remove_all(fixtureRoot, cleanupError);
}

TEST_CASE("MM9 save load rejects stale dialogue state schema versions")
{
    const std::filesystem::path fixtureRoot = makeFixtureRoot();
    const OpenYAMM::Game::Mm9DialoguePackage package = loadFixturePackage(fixtureRoot);
    OpenYAMM::Game::Party party = makeRuntimeParty();
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    std::optional<std::string> scriptError;
    REQUIRE(scriptRuntime.runLabel("DORUDE.scr", "OnUse", scriptError));
    REQUIRE(scriptRuntime.runLabel("DORUDE.scr", "OnRude", scriptError));

    OpenYAMM::Game::GameSaveData saveData = {};
    saveData.mapFileName = "testmap.mm9";
    saveData.party = party.snapshot();
    saveData.mm9ScriptState = scriptRuntime.state();

    const std::filesystem::path savePath = fixtureRoot / "stale_mm9_dialogue_state.oysav";
    std::string saveError;
    REQUIRE(OpenYAMM::Game::saveGameDataToPath(savePath, saveData, saveError));

    {
        std::fstream stream(savePath, std::ios::binary | std::ios::in | std::ios::out);
        REQUIRE(stream.good());
        constexpr uint32_t StaleVersionBeforeMm9ScriptRuntimeState = 61;
        stream.seekp(8, std::ios::beg);
        stream.write(
            reinterpret_cast<const char *>(&StaleVersionBeforeMm9ScriptRuntimeState),
            sizeof(StaleVersionBeforeMm9ScriptRuntimeState));
        REQUIRE(stream.good());
    }

    std::string loadError;
    const std::optional<OpenYAMM::Game::GameSaveData> loaded =
        OpenYAMM::Game::loadGameDataFromPath(savePath, loadError);
    CHECK_FALSE(loaded.has_value());
    CHECK(loadError == "unsupported save version");

    std::error_code cleanupError;
    std::filesystem::remove_all(fixtureRoot, cleanupError);
}

TEST_CASE("MM9 generated Lua script runtime mutates party inventory gold and experience")
{
    const std::filesystem::path fixtureRoot = makeFixtureRoot();
    const OpenYAMM::Game::Mm9DialoguePackage package = loadFixturePackage(fixtureRoot);
    OpenYAMM::Game::Party party = makeRuntimeParty();
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    std::optional<std::string> error;
    REQUIRE(scriptRuntime.runLabel("DORUDE.scr", "Rewards", error));
    CHECK_FALSE(error.has_value());

    CHECK(party.gold() == 60);
    CHECK_FALSE(party.hasItemAnywhere(197));
    REQUIRE(party.member(0) != nullptr);
    REQUIRE(party.member(1) != nullptr);
    REQUIRE(party.member(2) != nullptr);
    REQUIRE(party.member(3) != nullptr);
    CHECK(party.member(0)->experience == 20);
    CHECK(party.member(1)->experience == 20);
    CHECK(party.member(2)->experience == 20);
    CHECK(party.member(3)->experience == 20);

    const std::vector<OpenYAMM::Game::Mm9ScriptRuntimePartyAccess> &partyAccesses =
        scriptRuntime.partyAccesses();
    REQUIRE(partyAccesses.size() == 6);
    CHECK(partyAccesses[0].operation == "giveGold");
    CHECK(partyAccesses[0].amount == 50);
    CHECK(partyAccesses[1].operation == "giveExp");
    CHECK(partyAccesses[1].amount == 80);
    CHECK(partyAccesses[2].operation == "giveItem");
    CHECK(partyAccesses[2].id == 197);
    CHECK(partyAccesses[2].result);
    CHECK(partyAccesses[3].operation == "hasItem");
    CHECK(partyAccesses[3].result);
    CHECK(partyAccesses[4].operation == "takeItem");
    CHECK(partyAccesses[4].id == 197);
    CHECK(partyAccesses[4].result);
    CHECK(partyAccesses[5].operation == "hasItem");
    CHECK_FALSE(partyAccesses[5].result);

    std::error_code cleanupError;
    std::filesystem::remove_all(fixtureRoot, cleanupError);
}

TEST_CASE("MM9 dialogue runtime dispatches every known service opcode with source context")
{
    const std::filesystem::path fixtureRoot = makeFixtureRoot();
    const OpenYAMM::Game::Mm9DialoguePackage package = loadFixturePackage(fixtureRoot);
    OpenYAMM::Game::Party party = {};
    OpenYAMM::Game::Mm9DialogueRuntime runtime(package, party);

    OpenYAMM::Game::Mm9DialogueOwnerContext owner = {};
    owner.mapId = "testmap";
    owner.objectIndex = 7;
    owner.objectName = "Fixture NPC";
    owner.scriptName = "DORUDE.scr";
    REQUIRE(runtime.enterRudeId(2, owner));

    const std::map<int32_t, OpenYAMM::Game::Mm9ServiceKind> expectedKinds = {
        {-2, OpenYAMM::Game::Mm9ServiceKind::Shop},
        {-3, OpenYAMM::Game::Mm9ServiceKind::Training},
        {-4, OpenYAMM::Game::Mm9ServiceKind::SkillTraining},
        {-5, OpenYAMM::Game::Mm9ServiceKind::Travel},
        {-6, OpenYAMM::Game::Mm9ServiceKind::Bank},
        {-7, OpenYAMM::Game::Mm9ServiceKind::Inn},
        {-8, OpenYAMM::Game::Mm9ServiceKind::Healer},
        {-10, OpenYAMM::Game::Mm9ServiceKind::Hire},
        {-11, OpenYAMM::Game::Mm9ServiceKind::Dismiss},
        {-13, OpenYAMM::Game::Mm9ServiceKind::ItemCombine},
        {-14, OpenYAMM::Game::Mm9ServiceKind::QuestHandoff},
        {-15, OpenYAMM::Game::Mm9ServiceKind::TownPortal},
        {-16, OpenYAMM::Game::Mm9ServiceKind::Donation},
    };

    const std::vector<OpenYAMM::Game::Mm9DialogueTopic> topics = runtime.visibleTopics();
    REQUIRE(topics.size() == expectedKinds.size());

    RecordingServiceHandler handler = {};
    for (size_t topicIndex = 0; topicIndex < topics.size(); ++topicIndex)
    {
        const OpenYAMM::Game::Mm9DialogueSelectionResult result = runtime.selectTopic(topicIndex);
        REQUIRE(result.kind == OpenYAMM::Game::Mm9DialogueSelectionKind::Service);
        REQUIRE(result.serviceRequest.has_value());
        CHECK(runtime.dispatchServiceSelection(result, handler));
    }

    REQUIRE(handler.requests.size() == expectedKinds.size());
    for (const OpenYAMM::Game::Mm9DialogueServiceRequest &request : handler.requests)
    {
        REQUIRE(expectedKinds.count(request.opcode) == 1);
        CHECK(request.kind == expectedKinds.at(request.opcode));
        CHECK(request.rudeId == 2);
        CHECK(request.nodeId == 2);
        CHECK(request.owner.mapId == "testmap");
        CHECK(request.owner.objectIndex == 7);
        CHECK(request.owner.objectName == "Fixture NPC");
        CHECK(request.owner.scriptName == "DORUDE.scr");
        CHECK(request.sourceRow > 0);
        CHECK(request.rawColumns.size() == 30);
        CHECK(request.rawColumns[5] == std::to_string(request.opcode));
    }

    std::error_code cleanupError;
    std::filesystem::remove_all(fixtureRoot, cleanupError);
}
