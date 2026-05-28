#include "doctest/doctest.h"

#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "game/mm9/Mm9DialoguePackage.h"
#include "game/mm9/Mm9DialogueRuntime.h"
#include "game/party/Party.h"
#include "tools/Mm9RudeTranscode.h"

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <map>
#include <optional>
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
    int32_t next)
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
    columns[6] = "44";
    return OpenYAMM::Game::serializeMm9RudeCsvLine(columns) + "\n";
}

std::filesystem::path makeFixtureRoot(const std::string &name)
{
    const std::filesystem::path root = std::filesystem::temp_directory_path() / name;
    std::error_code error;
    std::filesystem::remove_all(root, error);

    const std::filesystem::path rudeDirectory = root / "extracted/RUDE/RUDE";
    writeTextFile(rudeDirectory / "NPC1.rude", rudeRow(1, 1, 1, "Hello", "Hi", -1));
    writeTextFile(rudeDirectory / "NPCNAME.rude", "1,Test NPC\n");
    writeTextFile(rudeDirectory / "TOPBLURB.rude", "1,Test NPC,Test blurb\n");
    writeTextFile(rudeDirectory / "NPC997.rude", rudeRow(997, 1, 1, "Quest", "Quest text", 0));
    writeTextFile(rudeDirectory / "NPC998.rude", rudeRow(998, 1, 1, "Note", "Note text", 0));
    writeTextFile(rudeDirectory / "NPC999.rude", rudeRow(999, 1, 1, "Award", "Award text", 0));

    const std::filesystem::path scriptsDirectory = root / "extracted/SCRIPTS/SCRIPTS";
    writeTextFile(scriptsDirectory / "globals.inc", "#number TEST_KEY = 44\n");
    writeTextFile(
        scriptsDirectory / "DORUDE.scr",
        "#include globals.inc\n"
        ":OnUse\n"
        "HasKey TEST_KEY\n"
        "DoRude 1\n"
        "OnRudeExit OnRude\n"
        ":OnRude\n"
        "GiveKey 44\n");

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
        "        value_json: \"\\\"\\\"\"\n"
        "      - name: GreetingSound\n"
        "        code: 0\n"
        "        flags: 0\n"
        "        decoded: false\n"
        "        raw_hex: \"0000\"\n"
        "        value_json: \"\"\n");

    writeTextFile(
        root / "assets_dev/worlds/mm9/world.yml",
        "id: mm9\n"
        "name: MM9\n"
        "sourceGame: mm9\n");

    const OpenYAMM::Game::Mm9DialoguePipelineResult generated =
        OpenYAMM::Game::generateMm9DialoguePipelineFiles(
            root / "extracted",
            root / "source_maps");
    REQUIRE(generated.errors.empty());

    const OpenYAMM::Game::Mm9DialoguePipelineWriteResult writeResult =
        OpenYAMM::Game::writeMm9DialoguePipelineFiles(
            root / "assets_dev/worlds/mm9",
            generated.files,
            false);
    REQUIRE(writeResult.errors.empty());

    return root;
}

void initializeAssetFileSystem(
    OpenYAMM::Engine::AssetFileSystem &assetFileSystem,
    const std::filesystem::path &fixtureRoot)
{
    REQUIRE(assetFileSystem.initialize(
        fixtureRoot,
        fixtureRoot / "assets_dev",
        OpenYAMM::Engine::AssetScaleTier::X1,
        "mm9"));
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

struct GeneratedServicePath
{
    int32_t rudeId = 0;
    int32_t opcode = 0;
    std::vector<size_t> sourceRows;
};

std::optional<GeneratedServicePath> findGeneratedServicePath(
    const OpenYAMM::Game::Mm9GeneratedRudeDialogue &dialogue,
    int32_t rudeId,
    int32_t opcode)
{
    struct SearchNode
    {
        int32_t nodeId = 0;
        std::vector<size_t> sourceRows;
    };

    std::vector<SearchNode> queue = {{rudeId, {}}};
    std::vector<int32_t> visitedNodes;

    for (size_t queueIndex = 0; queueIndex < queue.size(); ++queueIndex)
    {
        const SearchNode searchNode = queue[queueIndex];
        if (std::find(visitedNodes.begin(), visitedNodes.end(), searchNode.nodeId) != visitedNodes.end())
        {
            continue;
        }
        visitedNodes.push_back(searchNode.nodeId);

        for (const OpenYAMM::Game::Mm9GeneratedRudeRow &row : dialogue.rows)
        {
            if (row.npcId != rudeId || row.nodeId != searchNode.nodeId)
            {
                continue;
            }

            std::vector<size_t> path = searchNode.sourceRows;
            path.push_back(row.source.row);
            if (row.next == opcode)
            {
                return GeneratedServicePath{rudeId, opcode, path};
            }

            if (row.next > 0)
            {
                queue.push_back({row.next, path});
            }
        }
    }

    return std::nullopt;
}

const OpenYAMM::Game::Mm9GeneratedObjectDialogueBinding *findGeneratedBindingForRudeId(
    const OpenYAMM::Game::Mm9DialoguePackage &package,
    int32_t rudeId)
{
    const std::vector<OpenYAMM::Game::Mm9GeneratedObjectDialogueBinding>::const_iterator bindingIterator =
        std::find_if(
            package.objectBindings.begin(),
            package.objectBindings.end(),
            [rudeId](const OpenYAMM::Game::Mm9GeneratedObjectDialogueBinding &binding)
            {
                return binding.rudeId && *binding.rudeId == rudeId;
            });

    return bindingIterator != package.objectBindings.end() ? &*bindingIterator : nullptr;
}

OpenYAMM::Game::Mm9DialogueOwnerContext ownerContextForGeneratedServicePath(
    const OpenYAMM::Game::Mm9DialoguePackage &package,
    int32_t rudeId)
{
    OpenYAMM::Game::Mm9DialogueOwnerContext owner = {};
    const OpenYAMM::Game::Mm9GeneratedObjectDialogueBinding *pBinding =
        findGeneratedBindingForRudeId(package, rudeId);
    if (pBinding == nullptr)
    {
        return owner;
    }

    owner.mapId = pBinding->mapId;
    owner.objectIndex = pBinding->objectIndex;
    owner.objectName = pBinding->objectName;
    owner.scriptName = pBinding->scriptName;
    owner.scriptParams = pBinding->scriptParams;
    owner.greetingSound = pBinding->greetingSound;
    return owner;
}

OpenYAMM::Game::Mm9DialogueSelectionResult replayGeneratedServicePath(
    OpenYAMM::Game::Mm9DialogueRuntime &runtime,
    const GeneratedServicePath &path)
{
    OpenYAMM::Game::Mm9DialogueSelectionResult result = {};

    for (size_t sourceRow : path.sourceRows)
    {
        const std::vector<OpenYAMM::Game::Mm9DialogueTopic> topics = runtime.visibleTopics();
        const std::vector<OpenYAMM::Game::Mm9DialogueTopic>::const_iterator topicIterator =
            std::find_if(
                topics.begin(),
                topics.end(),
                [sourceRow](const OpenYAMM::Game::Mm9DialogueTopic &topic)
                {
                    return topic.sourceRow == sourceRow;
                });

        REQUIRE(topicIterator != topics.end());
        result = runtime.selectTopic(static_cast<size_t>(topicIterator - topics.begin()));
    }

    return result;
}
}

TEST_CASE("MM9 dialogue package loader reads generated world-mounted pipeline outputs")
{
    const std::filesystem::path fixtureRoot = makeFixtureRoot("openyamm_mm9_dialogue_package_fixture");
    OpenYAMM::Engine::AssetFileSystem assetFileSystem = {};
    initializeAssetFileSystem(assetFileSystem, fixtureRoot);

    OpenYAMM::Game::Mm9DialoguePackage package = {};
    REQUIRE(OpenYAMM::Game::loadMm9DialoguePackage(assetFileSystem, package));
    CHECK(package.errors.empty());

    REQUIRE(package.npcDialogues.count(1) == 1);
    REQUIRE(package.npcDialogues.at(1).rows.size() == 1);
    CHECK(package.npcDialogues.at(1).rows[0].prompt == "Hello");
    CHECK(package.npcDialogues.at(1).rows[0].response == "Hi");
    CHECK(package.npcDialogues.at(1).rows[0].next == -1);
    CHECK(package.npcDialogues.at(1).rows[0].source.file == "NPC1.rude");
    CHECK(package.npcDialogues.at(1).rows[0].rawColumns.size() == 30);

    CHECK(package.npcNames.at(1) == "Test NPC");
    CHECK(package.topBlurbs.at(1) == "Test blurb");
    CHECK(package.journalQuestRows.size() == 1);
    CHECK(package.journalNoteRows.size() == 1);
    CHECK(package.awardRows.size() == 1);

    REQUIRE(package.services.count(-1) == 1);
    CHECK(package.services.at(-1).name == "close");
    REQUIRE(package.keys.count(44) == 1);
    CHECK(package.keys.at(44).qbitId == 9044);

    REQUIRE(package.scripts.count("DORUDE.scr") == 1);
    CHECK(package.scripts.at("DORUDE.scr").luaPath == "scripts/DORUDE.lua");
    CHECK(package.scripts.at("DORUDE.scr").luaText.find("ctx:doRude(1") != std::string::npos);
    REQUIRE(package.scripts.count("globals.inc") == 1);
    CHECK(package.scripts.at("globals.inc").luaPath == "scripts/includes/globals.lua");

    REQUIRE(package.objectBindings.size() == 1);
    CHECK(package.objectBindings[0].mapId == "testmap");
    CHECK(package.objectBindings[0].objectIndex == 7);
    CHECK(package.objectBindings[0].doRude);
    REQUIRE(package.objectBindings[0].rudeId.has_value());
    CHECK(*package.objectBindings[0].rudeId == 1);
    CHECK(package.objectBindings[0].scriptName == "DORUDE.scr");
    CHECK(package.objectBindings[0].scriptSourceExists);

    std::error_code error;
    std::filesystem::remove_all(fixtureRoot, error);
}

TEST_CASE("MM9 generated world package loads complete authored dialogue pipeline outputs")
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
    CHECK(package.errors.empty());

    CHECK(package.npcDialogues.size() == 436);
    CHECK(package.npcNames.size() == 439);
    CHECK(package.topBlurbs.size() == 439);
    CHECK(package.journalQuestRows.size() == 143);
    CHECK(package.journalNoteRows.size() == 91);
    CHECK(package.awardRows.size() == 55);
    CHECK(package.scripts.size() == 802);
    CHECK(package.objectBindings.size() == 26207);
    CHECK(package.keys.size() == 684);

    const std::map<int32_t, std::string> expectedServices = {
        {-16, "donation"},
        {-15, "town_portal"},
        {-14, "quest_handoff"},
        {-13, "item_combine"},
        {-11, "dismiss"},
        {-10, "hire"},
        {-8, "healer"},
        {-7, "inn"},
        {-6, "bank"},
        {-5, "travel"},
        {-4, "skill_training"},
        {-3, "training"},
        {-2, "shop"},
        {-1, "close"},
    };
    REQUIRE(package.services.size() == expectedServices.size());
    for (const auto &[opcode, serviceName] : expectedServices)
    {
        REQUIRE(package.services.count(opcode) == 1);
        CHECK(package.services.at(opcode).name == serviceName);
        CHECK(package.services.at(opcode).observedCount > 0);
    }

    size_t dialogueCapableBindings = 0;
    size_t scriptBackedDialogueBindings = 0;
    for (const OpenYAMM::Game::Mm9GeneratedObjectDialogueBinding &binding : package.objectBindings)
    {
        if (!binding.dialogueCapable)
        {
            continue;
        }

        ++dialogueCapableBindings;
        if (!binding.scriptName.empty() && binding.scriptSourceExists)
        {
            ++scriptBackedDialogueBindings;
        }
    }

    CHECK(dialogueCapableBindings == 458);
    CHECK(scriptBackedDialogueBindings > 0);
}

TEST_CASE("MM9 generated world package dispatches every service opcode from authored dialogue rows")
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

    const std::map<int32_t, OpenYAMM::Game::Mm9ServiceKind> expectedKinds = {
        {-16, OpenYAMM::Game::Mm9ServiceKind::Donation},
        {-15, OpenYAMM::Game::Mm9ServiceKind::TownPortal},
        {-14, OpenYAMM::Game::Mm9ServiceKind::QuestHandoff},
        {-13, OpenYAMM::Game::Mm9ServiceKind::ItemCombine},
        {-11, OpenYAMM::Game::Mm9ServiceKind::Dismiss},
        {-10, OpenYAMM::Game::Mm9ServiceKind::Hire},
        {-8, OpenYAMM::Game::Mm9ServiceKind::Healer},
        {-7, OpenYAMM::Game::Mm9ServiceKind::Inn},
        {-6, OpenYAMM::Game::Mm9ServiceKind::Bank},
        {-5, OpenYAMM::Game::Mm9ServiceKind::Travel},
        {-4, OpenYAMM::Game::Mm9ServiceKind::SkillTraining},
        {-3, OpenYAMM::Game::Mm9ServiceKind::Training},
        {-2, OpenYAMM::Game::Mm9ServiceKind::Shop},
    };

    std::map<int32_t, GeneratedServicePath> pathsByOpcode;
    for (const std::pair<const int32_t, OpenYAMM::Game::Mm9GeneratedRudeDialogue> &dialogueEntry :
        package.npcDialogues)
    {
        for (const std::pair<const int32_t, OpenYAMM::Game::Mm9ServiceKind> &expected : expectedKinds)
        {
            if (pathsByOpcode.count(expected.first) != 0)
            {
                continue;
            }

            const std::optional<GeneratedServicePath> path =
                findGeneratedServicePath(dialogueEntry.second, dialogueEntry.first, expected.first);
            if (path)
            {
                pathsByOpcode[expected.first] = *path;
            }
        }
    }

    REQUIRE(pathsByOpcode.size() == expectedKinds.size());

    OpenYAMM::Game::Party party = {};
    OpenYAMM::Game::Mm9DialogueRuntime runtime(package, party);
    for (const std::pair<const int32_t, OpenYAMM::Game::Mm9GeneratedKey> &keyEntry : package.keys)
    {
        runtime.giveKey(keyEntry.first);
    }

    RecordingServiceHandler handler = {};
    for (const std::pair<const int32_t, OpenYAMM::Game::Mm9ServiceKind> &expected : expectedKinds)
    {
        const GeneratedServicePath &path = pathsByOpcode.at(expected.first);
        const OpenYAMM::Game::Mm9DialogueOwnerContext owner =
            ownerContextForGeneratedServicePath(package, path.rudeId);
        REQUIRE(runtime.enterRudeId(path.rudeId, owner));

        const OpenYAMM::Game::Mm9DialogueSelectionResult result =
            replayGeneratedServicePath(runtime, path);
        REQUIRE(result.kind == OpenYAMM::Game::Mm9DialogueSelectionKind::Service);
        REQUIRE(result.serviceRequest.has_value());
        CHECK(result.serviceOpcode == expected.first);
        CHECK(result.serviceRequest->opcode == expected.first);
        CHECK(result.serviceRequest->kind == expected.second);
        CHECK(result.serviceRequest->rudeId == path.rudeId);
        CHECK(result.serviceRequest->sourceRow == path.sourceRows.back());
        CHECK(result.serviceRequest->rawColumns.size() == 30);
        CHECK(result.serviceRequest->rawColumns[5] == std::to_string(expected.first));
        CHECK(runtime.dispatchServiceSelection(result, handler));
    }

    REQUIRE(handler.requests.size() == expectedKinds.size());
    for (const OpenYAMM::Game::Mm9DialogueServiceRequest &request : handler.requests)
    {
        REQUIRE(expectedKinds.count(request.opcode) == 1);
        CHECK(request.kind == expectedKinds.at(request.opcode));
        CHECK_FALSE(request.name.empty());
        CHECK(request.sourceRow > 0);
        const bool hasGeneratedOwnerContext =
            !request.owner.mapId.empty() || request.owner.objectIndex == -1;
        CHECK(hasGeneratedOwnerContext);
    }
}

TEST_CASE("MM9 dialogue package loader rejects stale or malformed generated package files")
{
    const std::filesystem::path fixtureRoot = makeFixtureRoot("openyamm_mm9_dialogue_package_bad_fixture");
    writeTextFile(
        fixtureRoot / "assets_dev/worlds/mm9/state/keys.yml",
        "format_version: 1\n"
        "state_domain: mm9.keys\n"
        "backend: qbits\n"
        "qbit_base: 9000\n"
        "keys:\n"
        "  - raw_id: 44\n"
        "    qbit_id: 9045\n");

    OpenYAMM::Engine::AssetFileSystem assetFileSystem = {};
    initializeAssetFileSystem(assetFileSystem, fixtureRoot);
    OpenYAMM::Game::Mm9DialoguePackage package = {};
    CHECK(!OpenYAMM::Game::loadMm9DialoguePackage(assetFileSystem, package));

    bool foundKeyError = false;
    for (const OpenYAMM::Game::Mm9DialoguePackageError &error : package.errors)
    {
        if (error.virtualPath == "state/keys.yml" &&
            error.message.find("9000 + raw_id") != std::string::npos)
        {
            foundKeyError = true;
        }
    }
    CHECK(foundKeyError);

    std::error_code error;
    std::filesystem::remove_all(fixtureRoot, error);
}
