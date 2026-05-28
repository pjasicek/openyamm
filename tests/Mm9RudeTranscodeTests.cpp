#include "doctest/doctest.h"

#include "engine/scripting/LuaStateOwner.h"
#include "tools/Mm9RudeTranscode.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cctype>
#include <fstream>
#include <filesystem>
#include <optional>
#include <set>
#include <string>
#include <vector>

namespace
{
std::filesystem::path mm9ExtractedRoot()
{
    return std::filesystem::path(OPENYAMM_SOURCE_DIR) / "mm9/extracted";
}

std::filesystem::path sourceRoot()
{
    return std::filesystem::path(OPENYAMM_SOURCE_DIR);
}

std::filesystem::path rudePath(const std::string &fileName)
{
    return mm9ExtractedRoot() / "RUDE/RUDE" / fileName;
}

std::filesystem::path scriptPath(const std::string &fileName)
{
    return mm9ExtractedRoot() / "SCRIPTS/SCRIPTS" / fileName;
}

OpenYAMM::Game::Mm9RudeFile requireRudeFile(const std::string &fileName)
{
    const OpenYAMM::Game::Mm9RudeFile file = OpenYAMM::Game::parseMm9RudeFile(rudePath(fileName));
    REQUIRE_MESSAGE(file.errors.empty(), fileName.c_str());
    REQUIRE_MESSAGE(!file.rows.empty(), fileName.c_str());
    return file;
}

void checkAllRowsHaveColumns(const OpenYAMM::Game::Mm9RudeFile &file, size_t expectedColumns)
{
    for (const OpenYAMM::Game::Mm9RudeRow &row : file.rows)
    {
        INFO(row.sourcePath.string());
        INFO(row.rowNumber);
        CHECK(row.columns.size() == expectedColumns);
    }
}

OpenYAMM::Game::Mm9ScriptFile requireScriptFile(const std::string &fileName)
{
    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(scriptPath(fileName));
    REQUIRE_MESSAGE(file.errors.empty(), fileName.c_str());
    REQUIRE_MESSAGE(!file.lines.empty(), fileName.c_str());
    return file;
}

std::vector<std::filesystem::path> mm9ScriptSourceFiles()
{
    const std::filesystem::path scriptDirectory = mm9ExtractedRoot() / "SCRIPTS/SCRIPTS";
    std::vector<std::filesystem::path> paths;
    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(scriptDirectory))
    {
        if (entry.is_regular_file() && (entry.path().extension() == ".scr" || entry.path().extension() == ".inc"))
        {
            paths.push_back(entry.path());
        }
    }
    std::sort(paths.begin(), paths.end());
    return paths;
}

std::set<int32_t> mm9RudeIds()
{
    std::set<int32_t> ids;
    const std::filesystem::path rudeDirectory = mm9ExtractedRoot() / "RUDE/RUDE";
    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(rudeDirectory))
    {
        if (!entry.is_regular_file() || entry.path().extension() != ".rude" ||
            entry.path().filename() == "NPCNAME.rude" || entry.path().filename() == "TOPBLURB.rude")
        {
            continue;
        }

        const OpenYAMM::Game::Mm9RudeFile file = OpenYAMM::Game::parseMm9RudeFile(entry.path());
        REQUIRE(file.errors.empty());
        for (const OpenYAMM::Game::Mm9RudeRow &row : file.rows)
        {
            REQUIRE(!row.columns.empty());
            const std::optional<int32_t> id = OpenYAMM::Game::parseMm9RudeInt(row.columns[0]);
            REQUIRE(id.has_value());
            ids.insert(*id);
        }
    }
    return ids;
}

std::set<int32_t> rudeIdSetFromTwoOrThreeColumnFile(const std::string &fileName)
{
    std::set<int32_t> ids;
    const OpenYAMM::Game::Mm9RudeFile file = requireRudeFile(fileName);
    for (const OpenYAMM::Game::Mm9RudeRow &row : file.rows)
    {
        REQUIRE(!row.columns.empty());
        const std::optional<int32_t> id = OpenYAMM::Game::parseMm9RudeInt(row.columns[0]);
        REQUIRE(id.has_value());
        ids.insert(*id);
    }
    return ids;
}

std::set<int32_t> broadMm9KeyState()
{
    std::set<int32_t> keys;
    for (int32_t key = 1; key <= 10000; ++key)
    {
        keys.insert(key);
    }
    return keys;
}

std::set<int32_t> questQbitIdsFromFile(const std::filesystem::path &path)
{
    std::ifstream stream(path);
    REQUIRE(stream.good());

    std::set<int32_t> qbitIds;
    std::string line;
    while (std::getline(stream, line))
    {
        const size_t firstTab = line.find('\t');
        const std::string idText = firstTab == std::string::npos ? line : line.substr(0, firstTab);
        const std::optional<int32_t> qbitId = OpenYAMM::Game::parseMm9RudeInt(idText);
        if (qbitId && *qbitId > 0)
        {
            qbitIds.insert(*qbitId);
        }
    }

    return qbitIds;
}

std::set<int32_t> authoredMm6Mm7Mm8QuestQbits()
{
    std::set<int32_t> qbitIds = questQbitIdsFromFile(
        sourceRoot() / "assets_dev/engine/data_tables/english/quests.txt");
    const std::set<int32_t> mm6LegacyQbits = questQbitIdsFromFile(
        sourceRoot() / "assets_dev/worlds/mm6/_legacy/tables/Quests.txt");
    qbitIds.insert(mm6LegacyQbits.begin(), mm6LegacyQbits.end());
    return qbitIds;
}

void checkProviderServiceFixture(
    const std::string &fileName,
    int32_t rudeId,
    int32_t nodeId,
    int32_t opcode,
    const std::string &serviceName)
{
    OpenYAMM::Game::Mm9RudeDialogueProvider provider = {};
    REQUIRE(provider.loadFromFile(requireRudeFile(fileName)));
    provider.setKeyState(broadMm9KeyState());
    REQUIRE(provider.enterNode(rudeId, nodeId));

    const std::vector<OpenYAMM::Game::Mm9RudeTopic> topics = provider.visibleTopics();
    const auto serviceTopic = std::find_if(
        topics.begin(),
        topics.end(),
        [opcode](const OpenYAMM::Game::Mm9RudeTopic &topic)
        {
            return topic.next == opcode;
        });
    REQUIRE(serviceTopic != topics.end());

    const OpenYAMM::Game::Mm9RudeSelectionResult result =
        provider.selectTopic(static_cast<size_t>(serviceTopic - topics.begin()));
    CHECK(result.kind == OpenYAMM::Game::Mm9RudeSelectionKind::Service);
    CHECK(result.next == opcode);
    CHECK(result.serviceName == serviceName);
}

void writeTextFileForTest(const std::filesystem::path &path, const std::string &contents)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream stream(path, std::ios::binary);
    REQUIRE(stream.good());
    stream << contents;
}

std::string fixedWidthRudeRowForTest(
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

std::filesystem::path createPipelineFixtureRoot(const std::string &name)
{
    const std::filesystem::path root = std::filesystem::temp_directory_path() / name;
    std::error_code error;
    std::filesystem::remove_all(root, error);

    const std::filesystem::path rudeDirectory = root / "extracted/RUDE/RUDE";
    writeTextFileForTest(rudeDirectory / "NPC1.rude", fixedWidthRudeRowForTest(1, 1, 1, "Hello", "Hi", -1));
    writeTextFileForTest(rudeDirectory / "NPCNAME.rude", "1,Test NPC\n");
    writeTextFileForTest(rudeDirectory / "TOPBLURB.rude", "1,Test NPC,Test blurb\n");
    writeTextFileForTest(rudeDirectory / "NPC997.rude", fixedWidthRudeRowForTest(997, 1, 1, "Quest", "Quest text", 0));
    writeTextFileForTest(rudeDirectory / "NPC998.rude", fixedWidthRudeRowForTest(998, 1, 1, "Note", "Note text", 0));
    writeTextFileForTest(rudeDirectory / "NPC999.rude", fixedWidthRudeRowForTest(999, 1, 1, "Award", "Award text", 0));

    const std::filesystem::path scriptsDirectory = root / "extracted/SCRIPTS/SCRIPTS";
    writeTextFileForTest(scriptsDirectory / "globals.inc", "#number TEST_KEY = 44\n");
    writeTextFileForTest(
        scriptsDirectory / "DORUDE.scr",
        ";fixture\n#include globals.inc\n:OnUse\nHasKey TEST_KEY\nDoRude 1\nOnRudeExit OnRude\n:OnRude\nGiveKey 44\n");
    std::filesystem::create_directories(root / "maps");
    return root;
}
}

TEST_CASE("MM9 RUDE source inventory matches researched baseline")
{
    const OpenYAMM::Game::Mm9RudeSourceInventory inventory =
        OpenYAMM::Game::scanMm9RudeSourceInventory(mm9ExtractedRoot());

    for (const OpenYAMM::Game::Mm9RudeParseError &error : inventory.errors)
    {
        INFO(error.sourcePath.string());
        INFO(error.rowNumber);
        INFO(error.message);
        CHECK(false);
    }

    CHECK(inventory.numberedRudeFileCount == 439);
    CHECK(inventory.numberedRudeRowCount == 4504);
    CHECK(inventory.numberedNpcIdCount == 439);
    CHECK(inventory.numberedNodePairCount == 1869);
    CHECK(inventory.normalDialogueFileCount == 436);
    CHECK(inventory.normalDialogueRowCount == 4215);
    CHECK(inventory.normalNpcIdCount == 436);
    CHECK(inventory.normalNodePairCount == 1864);
    CHECK(inventory.npcNameRowCount == 439);
    CHECK(inventory.topBlurbRowCount == 439);
    CHECK(inventory.npc997RowCount == 143);
    CHECK(inventory.npc998RowCount == 91);
    CHECK(inventory.npc999RowCount == 55);
    CHECK(inventory.scriptFileCount == 715);
    CHECK(inventory.includeFileCount == 87);
}

TEST_CASE("MM9 RUDE parser preserves expected column shapes")
{
    checkAllRowsHaveColumns(requireRudeFile("NPC1.rude"), 30);
    checkAllRowsHaveColumns(requireRudeFile("NPC100.rude"), 30);
    checkAllRowsHaveColumns(requireRudeFile("NPC997.rude"), 30);
    checkAllRowsHaveColumns(requireRudeFile("NPC998.rude"), 30);
    checkAllRowsHaveColumns(requireRudeFile("NPC999.rude"), 30);
    checkAllRowsHaveColumns(requireRudeFile("NPCNAME.rude"), 2);
    checkAllRowsHaveColumns(requireRudeFile("TOPBLURB.rude"), 3);
}

TEST_CASE("MM9 RUDE CSV parser keeps quoted punctuation and empty fields")
{
    std::string error;
    const std::optional<std::vector<std::string>> columns =
        OpenYAMM::Game::parseMm9RudeCsvLine("1,2,3,\"A, quoted \"\"topic\"\"\",blank,-1,0,,0", error);

    REQUIRE(columns.has_value());
    REQUIRE(columns->size() == 9);
    CHECK((*columns)[0] == "1");
    CHECK((*columns)[3] == "A, quoted \"topic\"");
    CHECK((*columns)[4] == "blank");
    CHECK((*columns)[7].empty());
}

TEST_CASE("MM9 RUDE CSV parser round-trips all source rows and rejects malformed rows")
{
    const std::filesystem::path rudeDirectory = mm9ExtractedRoot() / "RUDE/RUDE";
    size_t rowCount = 0;
    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(rudeDirectory))
    {
        if (!entry.is_regular_file() || entry.path().extension() != ".rude")
        {
            continue;
        }

        const OpenYAMM::Game::Mm9RudeFile file = OpenYAMM::Game::parseMm9RudeFile(entry.path());
        REQUIRE(file.errors.empty());
        for (const OpenYAMM::Game::Mm9RudeRow &row : file.rows)
        {
            std::string error;
            const std::optional<std::vector<std::string>> reparsed =
                OpenYAMM::Game::parseMm9RudeCsvLine(OpenYAMM::Game::serializeMm9RudeCsvLine(row.columns), error);
            REQUIRE(reparsed.has_value());
            CHECK(*reparsed == row.columns);
            ++rowCount;
        }
    }

    CHECK(rowCount == 5382);

    std::string error;
    CHECK(!OpenYAMM::Game::parseMm9RudeCsvLine("1,\"unterminated", error).has_value());
    CHECK(!error.empty());
}

TEST_CASE("MM9 RUDE YAML generation is deterministic and lossless for raw columns")
{
    const OpenYAMM::Game::Mm9RudeFile file = requireRudeFile("NPC1.rude");

    const std::string firstYaml = OpenYAMM::Game::generateMm9RudeYaml(file);
    const std::string secondYaml = OpenYAMM::Game::generateMm9RudeYaml(file);
    CHECK(firstYaml == secondYaml);

    const YAML::Node root = YAML::Load(firstYaml);
    REQUIRE(root["rows"]);
    REQUIRE(root["rows"].IsSequence());
    REQUIRE(root["rows"].size() == file.rows.size());

    for (size_t rowIndex = 0; rowIndex < file.rows.size(); ++rowIndex)
    {
        const YAML::Node yamlRow = root["rows"][rowIndex];
        const YAML::Node rawColumns = yamlRow["raw_columns"];
        REQUIRE(rawColumns);
        REQUIRE(rawColumns.IsSequence());
        REQUIRE(rawColumns.size() == file.rows[rowIndex].columns.size());

        for (size_t columnIndex = 0; columnIndex < file.rows[rowIndex].columns.size(); ++columnIndex)
        {
            CHECK(rawColumns[columnIndex].as<std::string>() == file.rows[rowIndex].columns[columnIndex]);
        }

        CHECK(yamlRow["source"]["file"].as<std::string>() == "NPC1.rude");
        CHECK(yamlRow["source"]["row"].as<size_t>() == file.rows[rowIndex].rowNumber);
    }
}

TEST_CASE("MM9 RUDE YAML exposes decoded normal row fields without dropping raw tail fields")
{
    const OpenYAMM::Game::Mm9RudeFile file = requireRudeFile("NPC1.rude");
    const YAML::Node root = YAML::Load(OpenYAMM::Game::generateMm9RudeYaml(file));
    const YAML::Node firstRow = root["rows"][0];

    CHECK(firstRow["decoded"]["npc_id"].as<std::string>() == file.rows[0].columns[0]);
    CHECK(firstRow["decoded"]["node_id"].as<std::string>() == file.rows[0].columns[1]);
    CHECK(firstRow["decoded"]["choice_slot"].as<std::string>() == file.rows[0].columns[2]);
    CHECK(firstRow["decoded"]["prompt"].as<std::string>() == file.rows[0].columns[3]);
    CHECK(firstRow["decoded"]["response"].as<std::string>() == file.rows[0].columns[4]);
    CHECK(firstRow["decoded"]["next"].as<std::string>() == file.rows[0].columns[5]);

    for (size_t columnIndex = 6; columnIndex < file.rows[0].columns.size(); ++columnIndex)
    {
        std::string key = "c";
        if (columnIndex + 1 < 10)
        {
            key += "0";
        }
        key += std::to_string(columnIndex + 1);
        CHECK(firstRow["decoded"]["raw_fields"][key].as<std::string>() == file.rows[0].columns[columnIndex]);
    }
}

TEST_CASE("MM9 RUDE YAML emits semantic and unresolved blocks only for validated row meanings")
{
    const OpenYAMM::Game::Mm9RudeFile serviceFile = requireRudeFile("NPC100.rude");
    const YAML::Node serviceRoot = YAML::Load(OpenYAMM::Game::generateMm9RudeYaml(serviceFile));
    YAML::Node serviceRow;
    for (const YAML::Node &row : serviceRoot["rows"])
    {
        const YAML::Node action = row["semantic"]["action"];
        if (action
            && action["kind"].as<std::string>() == "service"
            && action["opcode"].as<int32_t>() == -6)
        {
            serviceRow = row;
            break;
        }
    }
    REQUIRE(serviceRow);
    CHECK(serviceRow["semantic"]["action"]["opcode"].as<int32_t>() == -6);
    CHECK(serviceRow["semantic"]["action"]["service"].as<std::string>() == "bank");
    REQUIRE(serviceRow["unresolved"].IsSequence());
    CHECK(serviceRow["unresolved"][0]["kind"].as<std::string>() == "service_behavior");
    CHECK(serviceRow["unresolved"][0]["status"].as<std::string>() == "typed_pending_exact_runtime_behavior");

    const OpenYAMM::Game::Mm9RudeFile zeroFile = requireRudeFile("NPC998.rude");
    const YAML::Node zeroRoot = YAML::Load(OpenYAMM::Game::generateMm9RudeYaml(zeroFile));
    bool foundZeroNext = false;
    bool foundRequiredKey = false;
    for (const YAML::Node &row : zeroRoot["rows"])
    {
        if (row["semantic"]["action"]["kind"].as<std::string>() == "unresolved")
        {
            foundZeroNext = true;
            REQUIRE(row["unresolved"].IsSequence());
            CHECK(row["unresolved"][0]["kind"].as<std::string>() == "next_zero");
        }

        const YAML::Node semantic = row["semantic"];
        const YAML::Node conditions = semantic ? semantic["conditions"] : YAML::Node();
        const YAML::Node requiredKeys = conditions ? conditions["required_keys"] : YAML::Node();
        if (requiredKeys && requiredKeys.IsSequence() && requiredKeys.size() > 0)
        {
            foundRequiredKey = true;
            CHECK(requiredKeys[0]["state_id"].as<std::string>().find("mm9.keys.") == 0);
            CHECK(requiredKeys[0]["qbit_id"].as<int32_t>() == 9000 + requiredKeys[0]["raw_id"].as<int32_t>());
            REQUIRE(row["semantic"]["state_refs"].IsSequence());
            CHECK(row["semantic"]["state_refs"][0]["domain"].as<std::string>() == "mm9.keys");
        }
    }

    CHECK(foundZeroNext);
    CHECK(foundRequiredKey);
}

TEST_CASE("MM9 RUDE parser sees every observed negative next opcode in source data")
{
    const std::set<int32_t> expectedOpcodes = {
        -1, -2, -3, -4, -5, -6, -7, -8, -10, -11, -13, -14, -15, -16
    };
    std::set<int32_t> observedOpcodes;

    const std::filesystem::path rudeDirectory = mm9ExtractedRoot() / "RUDE/RUDE";
    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(rudeDirectory))
    {
        if (!entry.is_regular_file() || entry.path().extension() != ".rude")
        {
            continue;
        }

        const std::string fileName = entry.path().filename().string();
        if (fileName == "NPCNAME.rude" || fileName == "TOPBLURB.rude")
        {
            continue;
        }

        const OpenYAMM::Game::Mm9RudeFile file = OpenYAMM::Game::parseMm9RudeFile(entry.path());
        REQUIRE(file.errors.empty());
        for (const OpenYAMM::Game::Mm9RudeRow &row : file.rows)
        {
            REQUIRE(row.columns.size() >= 6);
            const std::optional<int32_t> next = OpenYAMM::Game::parseMm9RudeInt(row.columns[5]);
            REQUIRE(next.has_value());
            if (*next < 0)
            {
                observedOpcodes.insert(*next);
            }
        }
    }

    CHECK(observedOpcodes == expectedOpcodes);
}

TEST_CASE("MM9 RUDE semantic guards preserve sparse fields and service opcode meanings")
{
    const OpenYAMM::Game::Mm9KeyRegistry registry = OpenYAMM::Game::buildMm9KeyRegistry(mm9ExtractedRoot());
    CHECK(registry.rudeCandidateEvidenceCount == 2213);

    std::set<int32_t> sparseIds;
    for (const auto &entryPair : registry.entries)
    {
        for (const OpenYAMM::Game::Mm9KeyEvidence &evidence : entryPair.second.evidence)
        {
            if (evidence.sourceKind == "rude_sparse_field")
            {
                sparseIds.insert(entryPair.first);
            }
        }
    }
    CHECK(sparseIds.size() == 524);

    OpenYAMM::Game::Mm9RudeDialogueProvider provider = {};
    REQUIRE(provider.loadFromFile(requireRudeFile("NPC100.rude")));
    REQUIRE(provider.enterNode(100, 999));
    std::vector<OpenYAMM::Game::Mm9RudeTopic> topics = provider.visibleTopics();
    REQUIRE(topics.size() == 1);
    CHECK(topics[0].next == -1);
    const OpenYAMM::Game::Mm9RudeSelectionResult closeResult = provider.selectTopic(0);
    CHECK(closeResult.kind == OpenYAMM::Game::Mm9RudeSelectionKind::Close);

    checkProviderServiceFixture("NPC251.rude", 251, 251, -2, "shop");
    checkProviderServiceFixture("NPC260.rude", 260, 260, -3, "training");
    checkProviderServiceFixture("NPC119.rude", 119, 119, -4, "skill_training");
    checkProviderServiceFixture("NPC144.rude", 144, 144, -5, "travel");
    checkProviderServiceFixture("NPC346.rude", 346, 346, -6, "bank");
    checkProviderServiceFixture("NPC101.rude", 101, 101, -7, "inn");
    checkProviderServiceFixture("NPC16.rude", 16, 16, -8, "healer");
    checkProviderServiceFixture("NPC126.rude", 126, 3, -10, "hire");
    checkProviderServiceFixture("NPC126.rude", 126, 126, -11, "dismiss");
    checkProviderServiceFixture("NPC418.rude", 418, 1, -13, "item_combine");
    checkProviderServiceFixture("NPC181.rude", 181, 998, -14, "quest_handoff");
    checkProviderServiceFixture("NPC179.rude", 179, 179, -15, "town_portal");
    checkProviderServiceFixture("NPC16.rude", 16, 16, -16, "donation");
}

TEST_CASE("MM9 script source inventory indexes command families with source preservation")
{
    const OpenYAMM::Game::Mm9ScriptSourceInventory inventory =
        OpenYAMM::Game::scanMm9ScriptSourceInventory(mm9ExtractedRoot());

    for (const OpenYAMM::Game::Mm9RudeParseError &error : inventory.errors)
    {
        INFO(error.sourcePath.string());
        INFO(error.rowNumber);
        INFO(error.message);
        CHECK(false);
    }

    CHECK(inventory.scriptFileCount == 715);
    CHECK(inventory.includeFileCount == 87);
    CHECK(inventory.parsedFileCount == 802);
    CHECK(inventory.lineCount == 105612);
    CHECK(inventory.labelCount == 6125);
    CHECK(inventory.includeDirectiveCount == 1077);
    CHECK(inventory.commandCount == 42610);

    CHECK(inventory.commandCounts.at("dorude") == 41);
    CHECK(inventory.commandCounts.at("onrudeexit") == 120);
    CHECK(inventory.commandCounts.at("givekey") == 343);
    CHECK(inventory.commandCounts.at("takekey") == 169);
    CHECK(inventory.commandCounts.at("haskey") == 727);
    CHECK(inventory.commandCounts.at("giveitem") == 101);
    CHECK(inventory.commandCounts.at("takeitem") == 54);
    CHECK(inventory.commandCounts.at("hasitem") == 52);
    CHECK(inventory.commandCounts.at("givegold") == 68);
    CHECK(inventory.commandCounts.at("giveexp") == 122);
    CHECK(inventory.commandCounts.at("setconsolenumvar") == 44);
    CHECK(inventory.commandCounts.at("getconsolenumvar") == 26);
    CHECK(inventory.commandCounts.at("setconsolestrvar") == 14);
    CHECK(inventory.commandCounts.at("getconsolestrvar") == 13);
    CHECK(inventory.commandCounts.at("getparam") == 1042);
    CHECK(inventory.commandCounts.at("setpropnumber") == 74);
    CHECK(inventory.commandCounts.at("getobjecthandlebyrudeid") == 12);
}

TEST_CASE("MM9 script parser preserves includes labels commands comments and line numbers")
{
    const OpenYAMM::Game::Mm9ScriptFile file = requireScriptFile("DORUDE.scr");

    REQUIRE(file.lines.size() >= 72);
    CHECK(file.lines[1].kind == OpenYAMM::Game::Mm9ScriptLineKind::Comment);
    CHECK(file.lines[1].rawLine == ";DoRude.scr");

    CHECK(file.lines[7].kind == OpenYAMM::Game::Mm9ScriptLineKind::Include);
    CHECK(file.lines[7].lineNumber == 8);
    CHECK(file.lines[7].name == "#include");
    CHECK(file.lines[7].argumentsText == "globals.inc");

    CHECK(file.lines[10].kind == OpenYAMM::Game::Mm9ScriptLineKind::Declaration);
    CHECK(file.lines[10].name == "#number");
    CHECK(file.lines[10].argumentsText == "NPC_ID");

    const OpenYAMM::Game::Mm9ScriptFile globalsFile = requireScriptFile("GLOBALS.inc");
    REQUIRE(globalsFile.lines.size() > 16);
    CHECK(globalsFile.lines[16].kind == OpenYAMM::Game::Mm9ScriptLineKind::Declaration);
    CHECK(globalsFile.lines[16].name == "#number");
    CHECK(globalsFile.lines[16].argumentsText == "g_bTemp");
    CHECK(globalsFile.lines[16].commentText == "; for booleans...");

    CHECK(file.lines[21].kind == OpenYAMM::Game::Mm9ScriptLineKind::Label);
    CHECK(file.lines[21].lineNumber == 22);
    CHECK(file.lines[21].name == "OnUse");

    CHECK(file.lines[30].kind == OpenYAMM::Game::Mm9ScriptLineKind::Command);
    CHECK(file.lines[30].lineNumber == 31);
    CHECK(OpenYAMM::Game::normalizeMm9ScriptCommandName(file.lines[30].name) == "dorude");
    CHECK(file.lines[30].argumentsText == "NPC_ID");

    CHECK(file.lines[71].kind == OpenYAMM::Game::Mm9ScriptLineKind::Command);
    CHECK(file.lines[71].lineNumber == 72);
    CHECK(OpenYAMM::Game::normalizeMm9ScriptCommandName(file.lines[71].name) == "onrudeexit");
    CHECK(file.lines[71].argumentsText == "OnRude");
}

TEST_CASE("MM9 script parser preserves opaque commands instead of rejecting unknown syntax")
{
    const OpenYAMM::Game::Mm9ScriptFile file = requireScriptFile("NPCBASE.inc");
    std::set<size_t> assignmentLineNumbers;

    for (const OpenYAMM::Game::Mm9ScriptLine &line : file.lines)
    {
        if (line.kind == OpenYAMM::Game::Mm9ScriptLineKind::Command &&
            line.codeText == "g_bChatting = FALSE")
        {
            assignmentLineNumbers.insert(line.lineNumber);
            CHECK(line.name == "g_bChatting");
            CHECK(line.argumentsText == "= FALSE");
        }
    }

    const std::set<size_t> expectedLineNumbers = {84, 236, 349};
    CHECK(assignmentLineNumbers == expectedLineNumbers);
}

TEST_CASE("MM9 key registry combines script key ops and RUDE sparse field evidence")
{
    const OpenYAMM::Game::Mm9KeyRegistry registry = OpenYAMM::Game::buildMm9KeyRegistry(mm9ExtractedRoot());

    CHECK(registry.stateDomain == "mm9.keys");
    CHECK(registry.scriptKeyOperationCount == 1239);
    CHECK(registry.resolvedScriptKeyOperationCount == 1188);
    CHECK(registry.unresolvedScriptReferences.size() == 51);
    CHECK(registry.rudeCandidateEvidenceCount == 2213);
    CHECK(registry.constants.size() == 871);
    CHECK(registry.conflictingConstants.size() == 34);
    CHECK(registry.entries.size() == 684);

    REQUIRE(registry.entries.count(93) == 1);
    CHECK(registry.entries.at(93).aliases.count("YRSAS_QUEST_PENDING") == 1);
    CHECK(registry.entries.at(93).aliases.count("93") == 1);

    REQUIRE(registry.entries.count(1) == 1);
    CHECK(registry.entries.at(1).aliases.count("ISLE_KEY_YRSATALK") == 1);
    CHECK(registry.entries.at(1).aliases.count("1") == 1);

    REQUIRE(registry.entries.count(365) == 1);
    CHECK(registry.entries.at(365).aliases.count("ISLE_KEY_YRSAFOUND") == 1);

    REQUIRE(registry.conflictingConstants.count("nTemp") == 1);
    const std::vector<int32_t> nTempValues = registry.conflictingConstants.at("nTemp");
    CHECK(std::find(nTempValues.begin(), nTempValues.end(), 0) != nTempValues.end());
    CHECK(std::find(nTempValues.begin(), nTempValues.end(), 2) != nTempValues.end());
}

TEST_CASE("MM9 key registry records source evidence and keeps unresolved dynamic references explicit")
{
    const OpenYAMM::Game::Mm9KeyRegistry registry = OpenYAMM::Game::buildMm9KeyRegistry(mm9ExtractedRoot());

    bool foundYrsaRudeEvidence = false;
    for (const OpenYAMM::Game::Mm9KeyEvidence &evidence : registry.entries.at(93).evidence)
    {
        if (evidence.sourceKind == "rude_sparse_field" && evidence.sourcePath.filename() == "NPC1.rude")
        {
            foundYrsaRudeEvidence = true;
            CHECK(evidence.rowNumber != 0);
            CHECK(evidence.columnNumber != 0);
        }
    }
    CHECK(foundYrsaRudeEvidence);

    bool foundThjorgardScriptEvidence = false;
    for (const OpenYAMM::Game::Mm9KeyEvidence &evidence : registry.entries.at(93).evidence)
    {
        if (evidence.sourceKind == "script_key_op" &&
            evidence.sourcePath.filename() == "THJORGARDGAMESCOMMON.inc" &&
            evidence.symbol == "YRSAS_QUEST_PENDING")
        {
            foundThjorgardScriptEvidence = true;
            CHECK(evidence.lineNumber != 0);
            CHECK(evidence.operation == "haskey");
        }
    }
    CHECK(foundThjorgardScriptEvidence);

    bool foundDynamicReference = false;
    for (const OpenYAMM::Game::Mm9KeyEvidence &evidence : registry.unresolvedScriptReferences)
    {
        if (evidence.sourcePath.filename() == "AK_IMPGATE.scr" && evidence.symbol == "nKey")
        {
            foundDynamicReference = true;
            CHECK(evidence.sourceKind == "script_key_op");
            CHECK(evidence.lineNumber != 0);
        }
    }
    CHECK(foundDynamicReference);
}

TEST_CASE("MM9 key registry YAML is deterministic and namespaced away from legacy qbits")
{
    const OpenYAMM::Game::Mm9KeyRegistry registry = OpenYAMM::Game::buildMm9KeyRegistry(mm9ExtractedRoot());

    const std::string firstYaml = OpenYAMM::Game::generateMm9KeyRegistryYaml(registry);
    const std::string secondYaml = OpenYAMM::Game::generateMm9KeyRegistryYaml(registry);
    CHECK(firstYaml == secondYaml);

    const YAML::Node root = YAML::Load(firstYaml);
    CHECK(root["state_domain"].as<std::string>() == "mm9.keys");
    REQUIRE(root["keys"]);
    REQUIRE(root["keys"].IsSequence());
    CHECK(root["keys"].size() == registry.entries.size());
    CHECK(firstYaml.find("QBit") == std::string::npos);
}

TEST_CASE("MM9 pseudo RUDE tables generate journal note and award YAML")
{
    struct PseudoCase
    {
        const char *pFileName;
        OpenYAMM::Game::Mm9PseudoRudeTableKind kind;
        const char *pKindName;
        size_t expectedRows;
    };

    const PseudoCase cases[] = {
        {"NPC997.rude", OpenYAMM::Game::Mm9PseudoRudeTableKind::JournalQuest, "journal_quests", 143},
        {"NPC998.rude", OpenYAMM::Game::Mm9PseudoRudeTableKind::JournalNote, "journal_notes", 91},
        {"NPC999.rude", OpenYAMM::Game::Mm9PseudoRudeTableKind::Award, "awards", 55},
    };

    for (const PseudoCase &testCase : cases)
    {
        const OpenYAMM::Game::Mm9RudeFile file = requireRudeFile(testCase.pFileName);
        const std::string firstYaml = OpenYAMM::Game::generateMm9PseudoRudeYaml(file, testCase.kind);
        const std::string secondYaml = OpenYAMM::Game::generateMm9PseudoRudeYaml(file, testCase.kind);
        CHECK(firstYaml == secondYaml);

        const YAML::Node root = YAML::Load(firstYaml);
        CHECK(root["table_kind"].as<std::string>() == testCase.pKindName);
        CHECK(root["source_file"].as<std::string>() == testCase.pFileName);
        REQUIRE(root["entries"]);
        REQUIRE(root["entries"].IsSequence());
        REQUIRE(root["entries"].size() == testCase.expectedRows);
        REQUIRE(root["entries"].size() == file.rows.size());

        for (size_t rowIndex = 0; rowIndex < file.rows.size(); ++rowIndex)
        {
            const YAML::Node yamlRow = root["entries"][rowIndex];
            CHECK(yamlRow["source"]["file"].as<std::string>() == testCase.pFileName);
            CHECK(yamlRow["source"]["row"].as<size_t>() == file.rows[rowIndex].rowNumber);
            REQUIRE(yamlRow["raw_columns"].size() == file.rows[rowIndex].columns.size());

            for (size_t columnIndex = 0; columnIndex < file.rows[rowIndex].columns.size(); ++columnIndex)
            {
                CHECK(yamlRow["raw_columns"][columnIndex].as<std::string>() ==
                    file.rows[rowIndex].columns[columnIndex]);
            }
        }
    }
}

TEST_CASE("MM9 pseudo RUDE YAML preserves decoded ids text next and raw sparse fields")
{
    const OpenYAMM::Game::Mm9RudeFile file = requireRudeFile("NPC997.rude");
    const YAML::Node root = YAML::Load(
        OpenYAMM::Game::generateMm9PseudoRudeYaml(
            file,
            OpenYAMM::Game::Mm9PseudoRudeTableKind::JournalQuest));
    const YAML::Node firstEntry = root["entries"][0];

    CHECK(firstEntry["decoded"]["rude_id"].as<std::string>() == file.rows[0].columns[0]);
    CHECK(firstEntry["decoded"]["node_id"].as<std::string>() == file.rows[0].columns[1]);
    CHECK(firstEntry["decoded"]["entry_id"].as<std::string>() == file.rows[0].columns[2]);
    CHECK(firstEntry["decoded"]["title"].as<std::string>() == file.rows[0].columns[3]);
    CHECK(firstEntry["decoded"]["text"].as<std::string>() == file.rows[0].columns[4]);
    CHECK(firstEntry["decoded"]["next"].as<std::string>() == file.rows[0].columns[5]);

    for (size_t columnIndex = 6; columnIndex < file.rows[0].columns.size(); ++columnIndex)
    {
        std::string key = "c";
        if (columnIndex + 1 < 10)
        {
            key += "0";
        }
        key += std::to_string(columnIndex + 1);
        CHECK(firstEntry["decoded"]["raw_fields"][key].as<std::string>() == file.rows[0].columns[columnIndex]);
    }
}

TEST_CASE("MM9 pseudo RUDE key references are covered by key registry")
{
    const OpenYAMM::Game::Mm9KeyRegistry registry = OpenYAMM::Game::buildMm9KeyRegistry(mm9ExtractedRoot());
    CHECK(OpenYAMM::Game::findMissingMm9PseudoRudeKeyReferences(requireRudeFile("NPC997.rude"), registry).empty());
    CHECK(OpenYAMM::Game::findMissingMm9PseudoRudeKeyReferences(requireRudeFile("NPC998.rude"), registry).empty());
    CHECK(OpenYAMM::Game::findMissingMm9PseudoRudeKeyReferences(requireRudeFile("NPC999.rude"), registry).empty());

    OpenYAMM::Game::Mm9KeyRegistry registryWithMissingKey = registry;
    registryWithMissingKey.entries.erase(473);
    const std::vector<OpenYAMM::Game::Mm9KeyEvidence> missing =
        OpenYAMM::Game::findMissingMm9PseudoRudeKeyReferences(
            requireRudeFile("NPC997.rude"),
            registryWithMissingKey);

    REQUIRE(!missing.empty());
    CHECK(missing[0].sourceKind == "missing_pseudo_rude_key");
    CHECK(missing[0].sourcePath.filename() == "NPC997.rude");
    CHECK(missing[0].symbol == "473");
}

TEST_CASE("MM9 script Lua generator emits deterministic source-preserving modules")
{
    const OpenYAMM::Game::Mm9ScriptFile file = requireScriptFile("DORUDE.scr");
    const std::string firstLua = OpenYAMM::Game::generateMm9ScriptLua(file);
    const std::string secondLua = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(firstLua == secondLua);
    CHECK(firstLua.find("local mm9 = mm9ScriptRuntime") != std::string::npos);
    CHECK(firstLua.find("script.source = \"DORUDE.scr\"") != std::string::npos);
    CHECK(firstLua.find("script.includes[#script.includes + 1] = { line = 8, path = \"globals.inc\" }") !=
        std::string::npos);
    CHECK(firstLua.find("script.labels[\"OnUse\"] = function(ctx)") != std::string::npos);
    CHECK(firstLua.find("-- Does NPC Rude") != std::string::npos);
    CHECK(firstLua.find("-- parameters:") != std::string::npos);
    CHECK(firstLua.find("-- p0 number of NPC to do") != std::string::npos);
    CHECK(firstLua.find("-- --------------------------------------------------") == std::string::npos);
    CHECK(firstLua.find("-- DORUDE.scr:31") != std::string::npos);
    CHECK(firstLua.find("ctx:doRude(\"NPC_ID\"") != std::string::npos);
    CHECK(firstLua.find("ctx:onRudeExit(\"OnRude\", script.labels[\"OnRude\"]") != std::string::npos);
    CHECK(firstLua.find("local function findLabel") == std::string::npos);
    CHECK(firstLua.find("local function gosub") == std::string::npos);

    const OpenYAMM::Game::Mm9ScriptFile npc3File = requireScriptFile("NPC3.scr");
    const std::string npc3Lua = OpenYAMM::Game::generateMm9ScriptLua(npc3File);
    CHECK(npc3Lua.find("script.labels[\"Lifesaver\"] = function(ctx)") != std::string::npos);
    CHECK(npc3Lua.find("if not ctx:hasKey(235) then -- NPC3.scr:68-69") != std::string::npos);
    CHECK(npc3Lua.find("if ctx:hasKey(108) then -- NPC3.scr:200-201") != std::string::npos);
    CHECK(npc3Lua.find("else -- NPC3.scr:79") != std::string::npos);
    CHECK(npc3Lua.find("end -- NPC3.scr:86") != std::string::npos);
    CHECK(npc3Lua.find("meta(") == std::string::npos);
    CHECK(npc3Lua.find("ctx:hasKey(108, \"g_ntemp\")") == std::string::npos);
    CHECK(npc3Lua.find("if ctx:condition(\"g_ntemp==TRUE\"") == std::string::npos);
    CHECK(npc3Lua.find("ctx:command(\"if\"") == std::string::npos);
    CHECK(npc3Lua.find("ctx:command(\"else\"") == std::string::npos);
    CHECK(npc3Lua.find("ctx:command(\"endif\"") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator preserves meaningful comments on declaration lines")
{
    const OpenYAMM::Game::Mm9ScriptFile globalsFile = requireScriptFile("GLOBALS.inc");
    const std::string globalsLua = OpenYAMM::Game::generateMm9ScriptLua(globalsFile);
    CHECK(globalsLua.find("-- for booleans...") != std::string::npos);

    const OpenYAMM::Game::Mm9ScriptFile flagsFile = requireScriptFile("FLAGS.inc");
    const std::string flagsLua = OpenYAMM::Game::generateMm9ScriptLua(flagsFile);
    CHECK(flagsLua.find("-- Is this model visible?") != std::string::npos);
    CHECK(flagsLua.find("-- Object can't go thru other solid objects.") != std::string::npos);
    CHECK(flagsLua.find("-- Gets touch notification.") != std::string::npos);
}

TEST_CASE("MM9 script Lua generator compiles every script and include")
{
    for (const std::filesystem::path &path : mm9ScriptSourceFiles())
    {
        const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
        REQUIRE(file.errors.empty());

        const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);
        OpenYAMM::Engine::LuaStateOwner lua = {};
        REQUIRE(lua.isValid());

        std::optional<std::string> error;
        INFO(path.string());
        CHECK(lua.runChunk(luaText, "@" + path.filename().string() + ".lua", error));
        if (error)
        {
            INFO(*error);
        }
    }
}

TEST_CASE("MM9 generated Lua routes key item reward console object and trigger operations")
{
    std::string combinedLua;
    for (const std::filesystem::path &path : mm9ScriptSourceFiles())
    {
        const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
        REQUIRE(file.errors.empty());
        combinedLua += OpenYAMM::Game::generateMm9ScriptLua(file);
    }

    CHECK(combinedLua.find("ctx:giveKey(") != std::string::npos);
    CHECK(combinedLua.find("ctx:takeKey(") != std::string::npos);
    CHECK(combinedLua.find("ctx:hasKey(") != std::string::npos);
    CHECK(combinedLua.find("ctx:giveItem(") != std::string::npos);
    CHECK(combinedLua.find("ctx:takeItem(") != std::string::npos);
    CHECK(combinedLua.find("ctx:hasItem(") != std::string::npos);
    CHECK(combinedLua.find("ctx:giveGold(") != std::string::npos);
    CHECK(combinedLua.find("ctx:giveExp(") != std::string::npos);
    CHECK(combinedLua.find("ctx:setConsoleNumVar(") != std::string::npos);
    CHECK(combinedLua.find("ctx:getConsoleNumVar(") != std::string::npos);
    CHECK(combinedLua.find("ctx:setConsoleStrVar(") != std::string::npos);
    CHECK(combinedLua.find("ctx:getConsoleStrVar(") != std::string::npos);
    CHECK(combinedLua.find("ctx:getParam(") != std::string::npos);
    CHECK(combinedLua.find("ctx:setPropNumber(") != std::string::npos);
    CHECK(combinedLua.find("ctx:getObjectHandleByRudeId(") != std::string::npos);
    CHECK(combinedLua.find("ctx:addTrigger(") != std::string::npos);
    CHECK(combinedLua.find("ctx:trigger(") != std::string::npos);
    CHECK(combinedLua.find("ctx:command(") != std::string::npos);
}

TEST_CASE("MM9 generated Lua literal DoRude calls reference known RUDE ids")
{
    const std::set<int32_t> knownRudeIds = mm9RudeIds();
    size_t literalDoRudeCount = 0;

    for (const std::filesystem::path &path : mm9ScriptSourceFiles())
    {
        const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
        REQUIRE(file.errors.empty());
        const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

        for (const OpenYAMM::Game::Mm9ScriptLine &line : file.lines)
        {
            if (line.kind != OpenYAMM::Game::Mm9ScriptLineKind::Command ||
                OpenYAMM::Game::normalizeMm9ScriptCommandName(line.name) != "dorude")
            {
                continue;
            }

            const std::string args = line.argumentsText;
            size_t end = 0;
            while (end < args.size() && args[end] != ',' && !std::isspace(static_cast<unsigned char>(args[end])))
            {
                ++end;
            }
            const std::optional<int32_t> rudeId = OpenYAMM::Game::parseMm9RudeInt(args.substr(0, end));
            if (!rudeId)
            {
                continue;
            }

            ++literalDoRudeCount;
            INFO(path.string());
            INFO(line.lineNumber);
            CHECK(knownRudeIds.count(*rudeId) == 1);
            CHECK(luaText.find("ctx:doRude(" + std::to_string(*rudeId)) != std::string::npos);
        }
    }

    CHECK(literalDoRudeCount > 0);
}

TEST_CASE("MM9 object dialogue binding scanner preserves relevant raw object properties")
{
    const OpenYAMM::Game::Mm9ObjectDialogueBindingIndex index =
        OpenYAMM::Game::scanMm9ObjectDialogueBindings(
            std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds/mm9/maps",
            mm9ExtractedRoot() / "SCRIPTS/SCRIPTS",
            mm9RudeIds());

    for (const OpenYAMM::Game::Mm9RudeParseError &error : index.errors)
    {
        INFO(error.sourcePath.string());
        INFO(error.message);
        CHECK(false);
    }

    CHECK(index.mapFileCount == 45);
    CHECK(index.objectCount > 0);
    CHECK(index.bindingCount > 0);
    CHECK(index.dialogueCapableCount > 0);
    CHECK(index.doRudeCount > 0);
    CHECK(index.npcNbrPropertyCount > 0);
    CHECK(index.linkedRudeIdCount > 0);
    CHECK(index.scriptNameCount > 0);
    CHECK(index.linkedScriptCount > 0);

    bool foundDrangheimNpc = false;
    for (const OpenYAMM::Game::Mm9ObjectDialogueBinding &binding : index.bindings)
    {
        if (binding.mapId == "drangheim" && binding.objectIndex == 23)
        {
            foundDrangheimNpc = true;
            CHECK(binding.objectClass == "ShopkeeperHuman2MaleA");
            CHECK(binding.doRude);
            REQUIRE(binding.rudeId.has_value());
            CHECK(*binding.rudeId == 103);
            CHECK(binding.rudeDecodeStatus == "raw_hex_float_integer");
            REQUIRE(binding.properties.count("NPCNbr") == 1);
            CHECK(binding.properties.at("NPCNbr").rawHex == "0000ce42");
            REQUIRE(binding.properties.count("DoRude") == 1);
            CHECK(binding.properties.at("DoRude").valueJson == "1");
            REQUIRE(binding.properties.count("GreetingSound") == 1);
            CHECK(binding.properties.at("GreetingSound").rawHex == "0000");
        }
    }
    CHECK(foundDrangheimNpc);
}

TEST_CASE("MM9 object dialogue bindings link scripts and preserve unresolved dialogue-capable objects")
{
    const OpenYAMM::Game::Mm9ObjectDialogueBindingIndex index =
        OpenYAMM::Game::scanMm9ObjectDialogueBindings(
            std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds/mm9/maps",
            mm9ExtractedRoot() / "SCRIPTS/SCRIPTS",
            mm9RudeIds());

    bool foundLinkedScript = false;
    bool foundUnlinkedDialogueCapable = false;
    for (const OpenYAMM::Game::Mm9ObjectDialogueBinding &binding : index.bindings)
    {
        if (binding.scriptName == "NPC90.scr")
        {
            foundLinkedScript = true;
            CHECK(binding.scriptSourceExists);
        }
        if (binding.dialogueCapable && !binding.rudeId)
        {
            foundUnlinkedDialogueCapable = true;
            REQUIRE(binding.properties.count("NPCNbr") == 1);
            CHECK(binding.rudeDecodeStatus == "unresolved");
        }
    }

    CHECK(foundLinkedScript);
    CHECK(index.unlinkedDialogueCapableCount > 0);
    CHECK(foundUnlinkedDialogueCapable);
}

TEST_CASE("MM9 linked object RUDE ids have dialogue name and top blurb data")
{
    const std::set<int32_t> dialogueIds = mm9RudeIds();
    const std::set<int32_t> nameIds = rudeIdSetFromTwoOrThreeColumnFile("NPCNAME.rude");
    const std::set<int32_t> topBlurbIds = rudeIdSetFromTwoOrThreeColumnFile("TOPBLURB.rude");
    const OpenYAMM::Game::Mm9ObjectDialogueBindingIndex index =
        OpenYAMM::Game::scanMm9ObjectDialogueBindings(
            std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds/mm9/maps",
            mm9ExtractedRoot() / "SCRIPTS/SCRIPTS",
            dialogueIds);

    for (const OpenYAMM::Game::Mm9ObjectDialogueBinding &binding : index.bindings)
    {
        if (!binding.rudeId)
        {
            continue;
        }

        INFO(binding.sourcePath.string());
        INFO(binding.objectIndex);
        CHECK(dialogueIds.count(*binding.rudeId) == 1);
        CHECK(nameIds.count(*binding.rudeId) == 1);
        CHECK(topBlurbIds.count(*binding.rudeId) == 1);
    }
}

TEST_CASE("MM9 RUDE dialogue provider builds from generated YAML and enters by rude id")
{
    const OpenYAMM::Game::Mm9RudeFile file = requireRudeFile("NPC100.rude");
    OpenYAMM::Game::Mm9RudeDialogueProvider provider = {};
    std::string error;

    REQUIRE(provider.loadFromGeneratedYaml(OpenYAMM::Game::generateMm9RudeYaml(file), error));
    CHECK(error.empty());
    REQUIRE(provider.enterRudeId(100));
    CHECK(provider.currentRudeId() == 100);
    CHECK(provider.currentNodeId() == 100);

    const std::vector<OpenYAMM::Game::Mm9RudeTopic> topics = provider.visibleTopics();
    REQUIRE(topics.size() >= 4);
    CHECK(topics[0].choiceSlot == 1);
    CHECK(topics[0].prompt == "We'd like to do some banking.");
    CHECK(topics[0].response == "Certainly.");
    CHECK(topics[0].rawColumns.size() == 30);
}

TEST_CASE("MM9 RUDE dialogue provider enters by object context")
{
    const OpenYAMM::Game::Mm9RudeFile file = requireRudeFile("NPC100.rude");
    OpenYAMM::Game::Mm9RudeDialogueProvider provider = {};
    REQUIRE(provider.loadFromFile(file));

    OpenYAMM::Game::Mm9ObjectDialogueBinding binding = {};
    binding.rudeId = 100;
    REQUIRE(provider.enterObjectContext(binding));
    CHECK(provider.currentRudeId() == 100);
    CHECK(provider.currentNodeId() == 100);
}

TEST_CASE("MM9 RUDE dialogue provider filters topics by required mm9 keys")
{
    const OpenYAMM::Game::Mm9RudeFile file = requireRudeFile("NPC100.rude");
    OpenYAMM::Game::Mm9RudeDialogueProvider provider = {};
    REQUIRE(provider.loadFromFile(file));
    REQUIRE(provider.enterRudeId(100));

    std::vector<OpenYAMM::Game::Mm9RudeTopic> topics = provider.visibleTopics();
    const auto closedTopicWithoutKey = std::find_if(
        topics.begin(),
        topics.end(),
        [](const OpenYAMM::Game::Mm9RudeTopic &topic)
        {
            return topic.response == "We're closed, sorry.";
        });
    CHECK(closedTopicWithoutKey == topics.end());

    provider.setKeyState({5017});
    topics = provider.visibleTopics();
    const auto closedTopicWithKey = std::find_if(
        topics.begin(),
        topics.end(),
        [](const OpenYAMM::Game::Mm9RudeTopic &topic)
        {
            return topic.response == "We're closed, sorry.";
        });
    CHECK(closedTopicWithKey != topics.end());
}

TEST_CASE("MM9 RUDE dialogue provider selects topics and follows branches")
{
    OpenYAMM::Game::Mm9RudeDialogueProvider provider = {};
    REQUIRE(provider.loadFromFile(requireRudeFile("NPC100.rude")));
    REQUIRE(provider.enterRudeId(100));

    const std::vector<OpenYAMM::Game::Mm9RudeTopic> topics = provider.visibleTopics();
    const auto askQuestions = std::find_if(
        topics.begin(),
        topics.end(),
        [](const OpenYAMM::Game::Mm9RudeTopic &topic)
        {
            return topic.prompt == "We'd like to ask you some questions.";
        });
    REQUIRE(askQuestions != topics.end());

    const OpenYAMM::Game::Mm9RudeSelectionResult result =
        provider.selectTopic(static_cast<size_t>(askQuestions - topics.begin()));
    CHECK(result.kind == OpenYAMM::Game::Mm9RudeSelectionKind::GotoNode);
    CHECK(result.response == "I suppose that would be alright.");
    CHECK(provider.currentNodeId() == 1);

    const std::vector<OpenYAMM::Game::Mm9RudeTopic> questionTopics = provider.visibleTopics();
    REQUIRE(!questionTopics.empty());
    CHECK(questionTopics[0].choiceSlot <= questionTopics.back().choiceSlot);
}

TEST_CASE("MM9 RUDE dialogue provider dispatches services and closes with OnRudeExit callback")
{
    OpenYAMM::Game::Mm9RudeDialogueProvider provider = {};
    REQUIRE(provider.loadFromFile(requireRudeFile("NPC100.rude")));
    provider.setOnRudeExitLabel("OnRude");
    REQUIRE(provider.enterRudeId(100));

    const OpenYAMM::Game::Mm9RudeSelectionResult serviceResult = provider.selectTopic(0);
    CHECK(serviceResult.kind == OpenYAMM::Game::Mm9RudeSelectionKind::Service);
    CHECK(serviceResult.next == -6);
    CHECK(serviceResult.serviceName == "bank");
    CHECK(!provider.closed());

    const std::vector<OpenYAMM::Game::Mm9RudeTopic> topics = provider.visibleTopics();
    const auto goodbye = std::find_if(
        topics.begin(),
        topics.end(),
        [](const OpenYAMM::Game::Mm9RudeTopic &topic)
        {
            return topic.next == -1;
        });
    REQUIRE(goodbye != topics.end());

    const OpenYAMM::Game::Mm9RudeSelectionResult closeResult =
        provider.selectTopic(static_cast<size_t>(goodbye - topics.begin()));
    CHECK(closeResult.kind == OpenYAMM::Game::Mm9RudeSelectionKind::Close);
    CHECK(closeResult.onRudeExitLabel == "OnRude");
    CHECK(provider.closed());
}

TEST_CASE("MM9 RUDE dialogue provider preserves unresolved next zero behavior")
{
    OpenYAMM::Game::Mm9RudeDialogueProvider provider = {};
    REQUIRE(provider.loadFromFile(requireRudeFile("NPC998.rude")));
    REQUIRE(provider.enterRudeId(998));
    provider.setKeyState({2006});

    const std::vector<OpenYAMM::Game::Mm9RudeTopic> topics = provider.visibleTopics();
    const auto zeroNext = std::find_if(
        topics.begin(),
        topics.end(),
        [](const OpenYAMM::Game::Mm9RudeTopic &topic)
        {
            return topic.next == 0;
        });
    REQUIRE(zeroNext != topics.end());

    const OpenYAMM::Game::Mm9RudeSelectionResult result =
        provider.selectTopic(static_cast<size_t>(zeroNext - topics.begin()));
    CHECK(result.kind == OpenYAMM::Game::Mm9RudeSelectionKind::UnresolvedZero);
    CHECK(result.next == 0);
    CHECK(!provider.closed());
}

TEST_CASE("MM9 RUDE dialogue provider exposes GUI-facing topics from RUDE rows")
{
    OpenYAMM::Game::Mm9RudeDialogueProvider provider = {};
    REQUIRE(provider.loadFromFile(requireRudeFile("NPC100.rude")));
    REQUIRE(provider.enterRudeId(100));

    const std::vector<OpenYAMM::Game::Mm9RudeTopic> topics = provider.visibleTopics();
    REQUIRE(!topics.empty());
    for (const OpenYAMM::Game::Mm9RudeTopic &topic : topics)
    {
        CHECK(!topic.prompt.empty());
        CHECK(!topic.response.empty());
        CHECK(topic.rawColumns.size() == 30);
        CHECK(topic.prompt == topic.rawColumns[3]);
        CHECK(topic.response == topic.rawColumns[4]);
    }
}

TEST_CASE("MM9 runtime fixtures cover representative service NPCs through generic provider")
{
    checkProviderServiceFixture("NPC251.rude", 251, 251, -2, "shop");
    checkProviderServiceFixture("NPC260.rude", 260, 260, -3, "training");
    checkProviderServiceFixture("NPC119.rude", 119, 119, -4, "skill_training");
    checkProviderServiceFixture("NPC144.rude", 144, 144, -5, "travel");
    checkProviderServiceFixture("NPC346.rude", 346, 346, -6, "bank");
    checkProviderServiceFixture("NPC101.rude", 101, 101, -7, "inn");
    checkProviderServiceFixture("NPC16.rude", 16, 16, -8, "healer");
    checkProviderServiceFixture("NPC126.rude", 126, 3, -10, "hire");
    checkProviderServiceFixture("NPC126.rude", 126, 126, -11, "dismiss");
    checkProviderServiceFixture("NPC418.rude", 418, 1, -13, "item_combine");
    checkProviderServiceFixture("NPC181.rude", 181, 998, -14, "quest_handoff");
    checkProviderServiceFixture("NPC179.rude", 179, 179, -15, "town_portal");
    checkProviderServiceFixture("NPC16.rude", 16, 16, -16, "donation");
}

TEST_CASE("MM9 runtime fixtures cover quest branching arena and pseudo journal tables")
{
    OpenYAMM::Game::Mm9RudeDialogueProvider questProvider = {};
    REQUIRE(questProvider.loadFromFile(requireRudeFile("NPC1.rude")));
    questProvider.setKeyState({27});
    REQUIRE(questProvider.enterNode(1, 1));
    std::vector<OpenYAMM::Game::Mm9RudeTopic> questTopics = questProvider.visibleTopics();
    REQUIRE(!questTopics.empty());
    CHECK(questTopics[0].prompt == "Who are you?");

    OpenYAMM::Game::Mm9RudeDialogueProvider arenaProvider = {};
    REQUIRE(arenaProvider.loadFromFile(requireRudeFile("NPC430.rude")));
    arenaProvider.setOnRudeExitLabel("OnRude");
    REQUIRE(arenaProvider.enterRudeId(430));
    CHECK(!arenaProvider.visibleTopics().empty());

    CHECK(YAML::Load(OpenYAMM::Game::generateMm9PseudoRudeYaml(
        requireRudeFile("NPC997.rude"),
        OpenYAMM::Game::Mm9PseudoRudeTableKind::JournalQuest))["entries"].size() == 143);
    CHECK(YAML::Load(OpenYAMM::Game::generateMm9PseudoRudeYaml(
        requireRudeFile("NPC998.rude"),
        OpenYAMM::Game::Mm9PseudoRudeTableKind::JournalNote))["entries"].size() == 91);
    CHECK(YAML::Load(OpenYAMM::Game::generateMm9PseudoRudeYaml(
        requireRudeFile("NPC999.rude"),
        OpenYAMM::Game::Mm9PseudoRudeTableKind::Award))["entries"].size() == 55);
}

TEST_CASE("MM9 generated RUDE YAML covers every original numbered RUDE row and column")
{
    const std::filesystem::path rudeDirectory = mm9ExtractedRoot() / "RUDE/RUDE";
    size_t fileCount = 0;
    size_t rowCount = 0;
    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(rudeDirectory))
    {
        if (!entry.is_regular_file() || entry.path().extension() != ".rude" ||
            entry.path().filename() == "NPCNAME.rude" || entry.path().filename() == "TOPBLURB.rude")
        {
            continue;
        }

        const OpenYAMM::Game::Mm9RudeFile file = OpenYAMM::Game::parseMm9RudeFile(entry.path());
        REQUIRE(file.errors.empty());
        const YAML::Node root = YAML::Load(OpenYAMM::Game::generateMm9RudeYaml(file));
        REQUIRE(root["rows"].size() == file.rows.size());
        ++fileCount;
        rowCount += file.rows.size();

        for (size_t rowIndex = 0; rowIndex < file.rows.size(); ++rowIndex)
        {
            const YAML::Node rawColumns = root["rows"][rowIndex]["raw_columns"];
            REQUIRE(rawColumns.size() == file.rows[rowIndex].columns.size());
            for (size_t columnIndex = 0; columnIndex < file.rows[rowIndex].columns.size(); ++columnIndex)
            {
                CHECK(rawColumns[columnIndex].as<std::string>() == file.rows[rowIndex].columns[columnIndex]);
            }
        }
    }

    CHECK(fileCount == 439);
    CHECK(rowCount == 4504);
}

TEST_CASE("MM9 key registry YAML exposes core qbit-backed key mapping")
{
    CHECK(OpenYAMM::Game::Mm9KeyQbitBase == 9000);
    CHECK(OpenYAMM::Game::Mm9CustomQbitBegin == 10000);
    CHECK(OpenYAMM::Game::mm9KeyToQbitId(44) == 9044);
    CHECK(OpenYAMM::Game::mm9KeyToQbitId(5017) == 14017);

    const OpenYAMM::Game::Mm9KeyRegistry registry = OpenYAMM::Game::buildMm9KeyRegistry(mm9ExtractedRoot());
    const YAML::Node root = YAML::Load(OpenYAMM::Game::generateMm9KeyRegistryYaml(registry));

    CHECK(root["state_domain"].as<std::string>() == "mm9.keys");
    CHECK(root["backend"].as<std::string>() == "qbits");
    CHECK(root["qbit_base"].as<int32_t>() == 9000);
    CHECK(root["qbit_mapping"].as<std::string>() == "9000 + raw_id");

    bool foundKey93 = false;
    for (const YAML::Node keyNode : root["keys"])
    {
        if (keyNode["raw_id"].as<int32_t>() == 93)
        {
            foundKey93 = true;
            CHECK(keyNode["id"].as<int32_t>() == 93);
            CHECK(keyNode["qbit_id"].as<int32_t>() == 9093);
        }
    }
    CHECK(foundKey93);
}

TEST_CASE("MM9 key-backed qbits are reserved without colliding with authored MM6-MM8 quest bits")
{
    const OpenYAMM::Game::Mm9KeyRegistry registry = OpenYAMM::Game::buildMm9KeyRegistry(mm9ExtractedRoot());
    const std::set<int32_t> reservedQbitIds = OpenYAMM::Game::mm9ReservedQbitIdsForRegistry(registry);
    REQUIRE(!reservedQbitIds.empty());
    CHECK(reservedQbitIds.count(OpenYAMM::Game::mm9KeyToQbitId(93)) == 1);

    const bool reservesCustomRangeQbits = std::any_of(
        reservedQbitIds.begin(),
        reservedQbitIds.end(),
        [](int32_t qbitId)
        {
            return OpenYAMM::Game::mm9QbitIdIsInCustomRange(qbitId);
        });
    REQUIRE(reservesCustomRangeQbits);
    CHECK_FALSE(OpenYAMM::Game::mm9QbitIdIsInCustomRange(9999));
    CHECK(OpenYAMM::Game::mm9QbitIdIsInCustomRange(OpenYAMM::Game::Mm9CustomQbitBegin));

    const std::set<int32_t> authoredQbitIds = authoredMm6Mm7Mm8QuestQbits();
    REQUIRE(!authoredQbitIds.empty());
    const std::vector<int32_t> authoredCollisions =
        OpenYAMM::Game::findMm9ReservedQbitCollisions(registry, authoredQbitIds);
    CHECK(authoredCollisions.empty());

    const int32_t reservedCustomQbit = *std::find_if(
        reservedQbitIds.begin(),
        reservedQbitIds.end(),
        [](int32_t qbitId)
        {
            return OpenYAMM::Game::mm9QbitIdIsInCustomRange(qbitId);
        });
    const std::vector<int32_t> syntheticCustomCollisions =
        OpenYAMM::Game::findMm9ReservedQbitCollisions(registry, {reservedCustomQbit});
    REQUIRE(syntheticCustomCollisions.size() == 1);
    CHECK(syntheticCustomCollisions[0] == reservedCustomQbit);
}

TEST_CASE("MM9 dialogue pipeline generates deterministic world-local outputs")
{
    const std::filesystem::path fixtureRoot = createPipelineFixtureRoot("openyamm_mm9_dialogue_pipeline_fixture");
    const OpenYAMM::Game::Mm9DialoguePipelineResult first =
        OpenYAMM::Game::generateMm9DialoguePipelineFiles(
            fixtureRoot / "extracted",
            fixtureRoot / "maps");
    const OpenYAMM::Game::Mm9DialoguePipelineResult second =
        OpenYAMM::Game::generateMm9DialoguePipelineFiles(
            fixtureRoot / "extracted",
            fixtureRoot / "maps");

    REQUIRE(first.errors.empty());
    REQUIRE(second.errors.empty());
    REQUIRE(first.files.size() == second.files.size());
    CHECK(first.files.size() == 14);

    std::set<std::filesystem::path> paths;
    for (size_t index = 0; index < first.files.size(); ++index)
    {
        const OpenYAMM::Game::Mm9DialoguePipelineGeneratedFile &left = first.files[index];
        const OpenYAMM::Game::Mm9DialoguePipelineGeneratedFile &right = second.files[index];
        CHECK(left.relativePath == right.relativePath);
        CHECK(left.contents == right.contents);
        CHECK(!left.relativePath.empty());
        CHECK(!left.relativePath.is_absolute());
        CHECK(left.relativePath.generic_string().find("..") == std::string::npos);
        CHECK(paths.insert(left.relativePath).second);
    }

    CHECK(paths.count("dialogue/npcs/1.yml") == 1);
    CHECK(paths.count("dialogue/npc_names.yml") == 1);
    CHECK(paths.count("dialogue/top_blurbs.yml") == 1);
    CHECK(paths.count("dialogue/services.yml") == 1);
    CHECK(paths.count("dialogue/journal_quests.yml") == 1);
    CHECK(paths.count("dialogue/journal_notes.yml") == 1);
    CHECK(paths.count("dialogue/awards.yml") == 1);
    CHECK(paths.count("state/keys.yml") == 1);
    CHECK(paths.count("state/defaults.yml") == 1);
    CHECK(paths.count("scripts/common/mm9_script_runtime.lua") == 1);
    CHECK(paths.count("scripts/DORUDE.lua") == 1);
    CHECK(paths.count("scripts/includes/globals.lua") == 1);
    CHECK(paths.count("scripts/script_index.yml") == 1);
    CHECK(paths.count("maps/dialogue_bindings.yml") == 1);

    std::error_code error;
    std::filesystem::remove_all(fixtureRoot, error);
}

TEST_CASE("MM9 dialogue pipeline write mode is idempotent and check mode detects stale files")
{
    const std::filesystem::path fixtureRoot = createPipelineFixtureRoot("openyamm_mm9_dialogue_pipeline_write_fixture");
    const std::filesystem::path outputRoot =
        std::filesystem::temp_directory_path() / "openyamm_mm9_dialogue_pipeline_test";
    std::error_code error;
    std::filesystem::remove_all(outputRoot, error);

    const OpenYAMM::Game::Mm9DialoguePipelineResult generated =
        OpenYAMM::Game::generateMm9DialoguePipelineFiles(
            fixtureRoot / "extracted",
            fixtureRoot / "maps");
    REQUIRE(generated.errors.empty());
    REQUIRE(!generated.files.empty());

    OpenYAMM::Game::Mm9DialoguePipelineWriteResult writeResult =
        OpenYAMM::Game::writeMm9DialoguePipelineFiles(outputRoot, generated.files, false);
    CHECK(writeResult.errors.empty());
    CHECK(writeResult.writtenFileCount == generated.files.size());
    CHECK(writeResult.unchangedFileCount == 0);

    writeResult = OpenYAMM::Game::writeMm9DialoguePipelineFiles(outputRoot, generated.files, false);
    CHECK(writeResult.errors.empty());
    CHECK(writeResult.writtenFileCount == 0);
    CHECK(writeResult.unchangedFileCount == generated.files.size());

    writeResult = OpenYAMM::Game::writeMm9DialoguePipelineFiles(outputRoot, generated.files, true);
    CHECK(writeResult.errors.empty());
    CHECK(writeResult.staleFileCount == 0);
    CHECK(writeResult.unchangedFileCount == generated.files.size());

    {
        std::ofstream stream(outputRoot / generated.files[0].relativePath, std::ios::binary);
        REQUIRE(stream.good());
        stream << "stale\n";
    }

    writeResult = OpenYAMM::Game::writeMm9DialoguePipelineFiles(outputRoot, generated.files, true);
    CHECK(!writeResult.errors.empty());
    CHECK(writeResult.staleFileCount == 1);

    std::filesystem::remove_all(outputRoot, error);
    std::filesystem::remove_all(fixtureRoot, error);
}
