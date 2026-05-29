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
#include <sstream>
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

TEST_CASE("MM9 script Lua generator keeps readable callback command casing")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_CALLBACK_CASING.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "ondamage OnDamage\n"
        "OnDeath OnDeath\n"
        "OnPostStartWorld Init\n"
        "oncongestion BaseCongestion\n"
        "onenrage OnEnrage\n"
        "OnPlayerInterrupt Interrupted\n"
        "ontargethit TargetHit\n"
        "onworldswitch TakeKey\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:onEvent(\"OnDamage\", \"OnDamage\") -- MM9_CALLBACK_CASING.scr:2") !=
        std::string::npos);
    CHECK(luaText.find("ctx:onEvent(\"OnDeath\", \"OnDeath\") -- MM9_CALLBACK_CASING.scr:3") !=
        std::string::npos);
    CHECK(luaText.find("ctx:onEvent(\"OnPostStartWorld\", \"Init\") -- MM9_CALLBACK_CASING.scr:4") !=
        std::string::npos);
    CHECK(luaText.find("ctx:onEvent(\"OnCongestion\", \"BaseCongestion\") -- MM9_CALLBACK_CASING.scr:5") !=
        std::string::npos);
    CHECK(luaText.find("ctx:onEvent(\"OnEnrage\", \"OnEnrage\") -- MM9_CALLBACK_CASING.scr:6") !=
        std::string::npos);
    CHECK(luaText.find("ctx:onEvent(\"OnPlayerInterrupt\", \"Interrupted\") -- MM9_CALLBACK_CASING.scr:7") !=
        std::string::npos);
    CHECK(luaText.find("ctx:onEvent(\"OnTargetHit\", \"TargetHit\") -- MM9_CALLBACK_CASING.scr:8") !=
        std::string::npos);
    CHECK(luaText.find("ctx:onEvent(\"OnWorldSwitch\", \"TakeKey\") -- MM9_CALLBACK_CASING.scr:9") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"ondamage\"") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"ondeath\"") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"onpoststartworld\"") == std::string::npos);
    CHECK(luaText.find("ctx:onEvent(\"on") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator lowers routed event registration commands")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_EVENTS.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "OnDamage OnDamageLabel\n"
        "OnTargetBeyondDist g_nMaxDist, TooFar\n"
        "AddModelKey DoResurrection, DoResurrectionTrigger\n"
        "RemoveModelKey DoResurrection\n"
        "SetCallBack 0, OnZoomWait\n"
        "KillCallBack 0\n"
        "RemoveTrigger Use\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:onEvent(\"OnDamage\", \"OnDamageLabel\") -- MM9_EVENTS.scr:2") !=
        std::string::npos);
    CHECK(luaText.find("ctx:onEvent(\"OnTargetBeyondDist\", \"g_nMaxDist\", \"TooFar\") "
        "-- MM9_EVENTS.scr:3") != std::string::npos);
    CHECK(luaText.find("ctx:addModelKey(\"DoResurrection\", \"DoResurrectionTrigger\") "
        "-- MM9_EVENTS.scr:4") != std::string::npos);
    CHECK(luaText.find("ctx:removeModelKey(\"DoResurrection\") -- MM9_EVENTS.scr:5") != std::string::npos);
    CHECK(luaText.find("ctx:setCallback(0, \"OnZoomWait\") -- MM9_EVENTS.scr:6") != std::string::npos);
    CHECK(luaText.find("ctx:killCallback(0) -- MM9_EVENTS.scr:7") != std::string::npos);
    CHECK(luaText.find("ctx:removeTrigger(\"Use\") -- MM9_EVENTS.scr:8") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"AddModelKey\"") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"RemoveTrigger\"") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator collapses safe immediate object trigger handles")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_OBJECT_COLLAPSE.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "GetObjectHandle Terrain3 g_hObject\n"
        "Trigger g_hObject open\n"
        "Trigger g_hObject sinkspeed\n"
        ":OnSingleUse\n"
        "GetObjectHandle Camera2 hCamera\n"
        "Trigger hCamera Play\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("local object = ctx:object(\"Terrain3\") -- MM9_OBJECT_COLLAPSE.scr:2") !=
        std::string::npos);
    CHECK(luaText.find("object:trigger(\"open\") -- MM9_OBJECT_COLLAPSE.scr:3") != std::string::npos);
    CHECK(luaText.find("object:trigger(\"sinkspeed\") -- MM9_OBJECT_COLLAPSE.scr:4") != std::string::npos);
    CHECK(luaText.find("ctx:object(\"Camera2\"):trigger(\"Play\") -- MM9_OBJECT_COLLAPSE.scr:6-7") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"getobjecthandle\", \"Terrain3 g_hObject\")") == std::string::npos);
    CHECK(luaText.find("ctx:trigger(\"g_hObject\", \"open\")") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator does not collapse object handles across null checks")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_OBJECT_NULL_CHECK.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "GetObjectHandle Target g_hObject\n"
        "if (g_hObject != NULL)\n"
        "Trigger g_hObject open\n"
        "endif\n"
        "Trigger NULL open\n"
        "Trigger 0 close\n"
        "Trigger nil lock\n"
        "Trigger hMissing\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:state().g_hObject = ctx:objectOrNil(\"Target\") "
        "-- MM9_OBJECT_NULL_CHECK.scr:2") != std::string::npos);
    CHECK(luaText.find("if ctx:condition(\"g_hObject != NULL\") then -- MM9_OBJECT_NULL_CHECK.scr:3") !=
        std::string::npos);
    CHECK(luaText.find("ctx:trigger(\"g_hObject\", \"open\") -- MM9_OBJECT_NULL_CHECK.scr:4") !=
        std::string::npos);
    CHECK(luaText.find("ctx:trigger(nil, \"open\") -- MM9_OBJECT_NULL_CHECK.scr:6") != std::string::npos);
    CHECK(luaText.find("ctx:trigger(nil, \"close\") -- MM9_OBJECT_NULL_CHECK.scr:7") != std::string::npos);
    CHECK(luaText.find("ctx:trigger(nil, \"lock\") -- MM9_OBJECT_NULL_CHECK.scr:8") != std::string::npos);
    CHECK(luaText.find("ctx:trigger(\"hMissing\") -- MM9_OBJECT_NULL_CHECK.scr:9") != std::string::npos);
    CHECK(luaText.find("ctx:trigger(\"NULL\"") == std::string::npos);
    CHECK(luaText.find("ctx:trigger(0") == std::string::npos);
    CHECK(luaText.find("ctx:object(\"Target\")") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator trims compact control parentheses")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_COMPACT_CONTROL.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "if( hDoorR!=NULL )\n"
        "Trigger hDoorR open\n"
        "endif\n"
        "while( nProgress<4 )\n"
        "Add nProgress, 1\n"
        "endwhile\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("if ctx:condition(\"hDoorR!=NULL\") then -- MM9_COMPACT_CONTROL.scr:2") !=
        std::string::npos);
    CHECK(luaText.find("while ctx:condition(\"nProgress<4\") do -- MM9_COMPACT_CONTROL.scr:5") !=
        std::string::npos);
    CHECK(luaText.find("hDoorR!=NULL )") == std::string::npos);
    CHECK(luaText.find("nProgress<4 )") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator collapses safe immediate object flag handles")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_OBJECT_FLAG_COLLAPSE.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "GetObjectHandle Door0 hDoor\n"
        "SetFlag hDoor FLAG_VISIBLE\n"
        "ClearFlag hDoor FLAG_SOLID\n"
        ":OnSingleUse\n"
        "GetObjectHandle Light0 hLight\n"
        "SetFlag hLight FLAG_VISIBLE\n"
        ":OnCheckedUse\n"
        "GetObjectHandle Checked hChecked\n"
        "if (hChecked != NULL)\n"
        "SetFlag hChecked FLAG_VISIBLE\n"
        "endif\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("local object = ctx:object(\"Door0\") -- MM9_OBJECT_FLAG_COLLAPSE.scr:2") !=
        std::string::npos);
    CHECK(luaText.find("object:setFlag(\"FLAG_VISIBLE\", true) -- MM9_OBJECT_FLAG_COLLAPSE.scr:3") !=
        std::string::npos);
    CHECK(luaText.find("object:setFlag(\"FLAG_SOLID\", false) -- MM9_OBJECT_FLAG_COLLAPSE.scr:4") !=
        std::string::npos);
    CHECK(luaText.find("ctx:object(\"Light0\"):setFlag(\"FLAG_VISIBLE\", true) "
        "-- MM9_OBJECT_FLAG_COLLAPSE.scr:6-7") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"getobjecthandle\", \"Door0 hDoor\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"setflag\", \"hDoor FLAG_VISIBLE\")") == std::string::npos);
    CHECK(luaText.find("ctx:state().hChecked = ctx:objectOrNil(\"Checked\") "
        "-- MM9_OBJECT_FLAG_COLLAPSE.scr:9") != std::string::npos);
    CHECK(luaText.find("ctx:object(\"hChecked\"):setFlag(\"FLAG_VISIBLE\", true) "
        "-- MM9_OBJECT_FLAG_COLLAPSE.scr:11") != std::string::npos);
}

TEST_CASE("MM9 script Lua generator lowers standalone generic object flag commands")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_OBJECT_FLAG.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "SetFlag hTarget FLAG_VISIBLE\n"
        "ClearFlag hTarget, solid\n"
        "SetFlag hTarget, 8192\n"
        "SetFlag NULL FLAG_VISIBLE\n"
        "ClearFlag 0 FLAG_VISIBLE\n"
        "SetFlag hTarget\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:object(\"hTarget\"):setFlag(\"FLAG_VISIBLE\", true) "
        "-- MM9_OBJECT_FLAG.scr:2") != std::string::npos);
    CHECK(luaText.find("ctx:object(\"hTarget\"):setFlag(\"solid\", false) "
        "-- MM9_OBJECT_FLAG.scr:3") != std::string::npos);
    CHECK(luaText.find("ctx:object(\"hTarget\"):setFlag(\"8192\", true) "
        "-- MM9_OBJECT_FLAG.scr:4") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"setflag\", \"NULL FLAG_VISIBLE\") -- MM9_OBJECT_FLAG.scr:5") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"clearflag\", \"0 FLAG_VISIBLE\") -- MM9_OBJECT_FLAG.scr:6") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"setflag\", \"hTarget\") -- MM9_OBJECT_FLAG.scr:7") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"setflag\", \"hTarget FLAG_VISIBLE\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"clearflag\", \"hTarget, solid\")") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator collapses safe immediate object stat handles")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_OBJECT_STAT_COLLAPSE.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "GetObjectHandle Door0 hDoor\n"
        "GetStat hDoor HitPoints nHp\n"
        "SetStat hDoor Locked TRUE\n"
        ":OnSingleUse\n"
        "GetObjectHandle Actor0 hActor\n"
        "SetStat hActor GaveTreasure FALSE\n"
        ":OnVariableUse\n"
        "GetObjectHandle Dynamic0 hDynamic\n"
        "SetStat hDynamic HitPoints nHp\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("local object = ctx:object(\"Door0\") -- MM9_OBJECT_STAT_COLLAPSE.scr:2") !=
        std::string::npos);
    CHECK(luaText.find("ctx:state().nHp = object:getStat(\"HitPoints\") -- MM9_OBJECT_STAT_COLLAPSE.scr:3") !=
        std::string::npos);
    CHECK(luaText.find("object:setStat(\"Locked\", true) -- MM9_OBJECT_STAT_COLLAPSE.scr:4") !=
        std::string::npos);
    CHECK(luaText.find("ctx:object(\"Actor0\"):setStat(\"GaveTreasure\", false) "
        "-- MM9_OBJECT_STAT_COLLAPSE.scr:6-7") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"getobjecthandle\", \"Door0 hDoor\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"getstat\", \"hDoor HitPoints nHp\")") == std::string::npos);
    CHECK(luaText.find("ctx:state().hDynamic = ctx:objectOrNil(\"Dynamic0\") "
        "-- MM9_OBJECT_STAT_COLLAPSE.scr:9") != std::string::npos);
    CHECK(luaText.find("ctx:object(\"hDynamic\"):setStat(\"HitPoints\", \"nHp\") "
        "-- MM9_OBJECT_STAT_COLLAPSE.scr:10") != std::string::npos);
}

TEST_CASE("MM9 script Lua generator lowers standalone generic object stat commands")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_OBJECT_STAT.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "GetStat hTarget, HitPoints, nHp\n"
        "SetStat hTarget, HitPoints, nHp\n"
        "SetStat hTarget, Locked, TRUE\n"
        "SetStat hTarget, AC, 20\n"
        "GetStat NULL, HitPoints, nHp\n"
        "SetStat 0, HitPoints, nHp\n"
        "GetStat hTarget, HitPoints, 1bad\n"
        "SetStat hTarget, HitPoints\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:state().nHp = ctx:object(\"hTarget\"):getStat(\"HitPoints\") "
        "-- MM9_OBJECT_STAT.scr:2") != std::string::npos);
    CHECK(luaText.find("ctx:object(\"hTarget\"):setStat(\"HitPoints\", \"nHp\") "
        "-- MM9_OBJECT_STAT.scr:3") != std::string::npos);
    CHECK(luaText.find("ctx:object(\"hTarget\"):setStat(\"Locked\", \"TRUE\") "
        "-- MM9_OBJECT_STAT.scr:4") != std::string::npos);
    CHECK(luaText.find("ctx:object(\"hTarget\"):setStat(\"AC\", 20) -- MM9_OBJECT_STAT.scr:5") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"getstat\", \"NULL, HitPoints, nHp\") -- MM9_OBJECT_STAT.scr:6") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"setstat\", \"0, HitPoints, nHp\") -- MM9_OBJECT_STAT.scr:7") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"getstat\", \"hTarget, HitPoints, 1bad\") "
        "-- MM9_OBJECT_STAT.scr:8") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"setstat\", \"hTarget, HitPoints\") -- MM9_OBJECT_STAT.scr:9") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"getstat\", \"hTarget, HitPoints, nHp\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"setstat\", \"hTarget, HitPoints, nHp\")") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator lowers standalone generic object property commands")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_OBJECT_PROPERTY.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "SetPropNumber DoRude, TRUE\n"
        "SetPropNumber HearingRange, g_nTemp\n"
        "SetPropString ScriptName, Custom.scr\n"
        "SetPropString TeleportDestination DESTINATION_NAME\n"
        "GetStatStr hTarget, ScriptName, sScript\n"
        "SetPropNumber DoRude\n"
        "SetPropString ScriptName\n"
        "GetStatStr NULL, ScriptName, sScript\n"
        "GetStatStr hTarget, ScriptName, 1bad\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:self():setNumberProperty(\"DoRude\", \"TRUE\") "
        "-- MM9_OBJECT_PROPERTY.scr:2") != std::string::npos);
    CHECK(luaText.find("ctx:self():setNumberProperty(\"HearingRange\", \"g_nTemp\") "
        "-- MM9_OBJECT_PROPERTY.scr:3") != std::string::npos);
    CHECK(luaText.find("ctx:self():setStringProperty(\"ScriptName\", \"Custom.scr\") "
        "-- MM9_OBJECT_PROPERTY.scr:4") != std::string::npos);
    CHECK(luaText.find("ctx:self():setStringProperty(\"TeleportDestination\", \"DESTINATION_NAME\") "
        "-- MM9_OBJECT_PROPERTY.scr:5") != std::string::npos);
    CHECK(luaText.find("ctx:state().sScript = ctx:object(\"hTarget\"):stringProperty(\"ScriptName\") "
        "-- MM9_OBJECT_PROPERTY.scr:6") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"setpropnumber\", \"DoRude\") -- MM9_OBJECT_PROPERTY.scr:7") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"setpropstring\", \"ScriptName\") -- MM9_OBJECT_PROPERTY.scr:8") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"getstatstr\", \"NULL, ScriptName, sScript\") "
        "-- MM9_OBJECT_PROPERTY.scr:9") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"getstatstr\", \"hTarget, ScriptName, 1bad\") "
        "-- MM9_OBJECT_PROPERTY.scr:10") != std::string::npos);
    CHECK(luaText.find("ctx:setPropNumber(\"DoRude\"") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"setpropstring\", \"ScriptName, Custom.scr\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"getstatstr\", \"hTarget, ScriptName, sScript\")") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator lowers standalone generic object distance queries")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_OBJECT_DISTANCE.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "GetDistance hFirst, hSecond, nDistance\n"
        "GetDistance hFirst hSecond nDistance2\n"
        "GetDistance NULL, hSecond, nDistance\n"
        "GetDistance hFirst, 0, nDistance\n"
        "GetDistance hFirst, hSecond, 1bad\n"
        "GetDistance hFirst, hSecond\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:state().nDistance = ctx:object(\"hFirst\"):distanceTo(ctx:object(\"hSecond\")) "
        "-- MM9_OBJECT_DISTANCE.scr:2") != std::string::npos);
    CHECK(luaText.find("ctx:state().nDistance2 = ctx:object(\"hFirst\"):distanceTo(ctx:object(\"hSecond\")) "
        "-- MM9_OBJECT_DISTANCE.scr:3") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"getdistance\", \"NULL, hSecond, nDistance\") "
        "-- MM9_OBJECT_DISTANCE.scr:4") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"getdistance\", \"hFirst, 0, nDistance\") "
        "-- MM9_OBJECT_DISTANCE.scr:5") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"getdistance\", \"hFirst, hSecond, 1bad\") "
        "-- MM9_OBJECT_DISTANCE.scr:6") != std::string::npos);
    CHECK(luaText.find("ctx:state().hSecond = ctx:self():distanceTo(ctx:object(\"hFirst\")) "
        "-- MM9_OBJECT_DISTANCE.scr:7") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"getdistance\", \"hFirst, hSecond, nDistance\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"getdistance\", \"hFirst hSecond nDistance2\")") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator collapses safe immediate object position handles")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_OBJECT_POSITION_COLLAPSE.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "GetObjectHandle Marker0 hMarker\n"
        "GetPOS hMarker xMarker yMarker zMarker\n"
        "SetPos hMarker 10 20 30\n"
        ":OnSingleUse\n"
        "GetObjectHandle Door0 hDoor\n"
        "SetPos hDoor -1 0 42\n"
        ":OnVariableUse\n"
        "GetObjectHandle Dynamic0 hDynamic\n"
        "SetPos hDynamic xMarker yMarker zMarker\n"
        ":OnCheckedUse\n"
        "GetObjectHandle Checked hChecked\n"
        "if (hChecked != NULL)\n"
        "GetPOS hChecked x y z\n"
        "endif\n"
        ":OnLaterUse\n"
        "GetObjectHandle Later0 hLater\n"
        "GetPOS hLater xLater yLater zLater\n"
        "Trigger hLater Use\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("local object = ctx:object(\"Marker0\") -- MM9_OBJECT_POSITION_COLLAPSE.scr:2") !=
        std::string::npos);
    CHECK(luaText.find("ctx:state().xMarker, ctx:state().yMarker, ctx:state().zMarker = object:pos() "
        "-- MM9_OBJECT_POSITION_COLLAPSE.scr:3") != std::string::npos);
    CHECK(luaText.find("object:setPos(10, 20, 30) -- MM9_OBJECT_POSITION_COLLAPSE.scr:4") !=
        std::string::npos);
    CHECK(luaText.find("ctx:object(\"Door0\"):setPos(-1, 0, 42) "
        "-- MM9_OBJECT_POSITION_COLLAPSE.scr:6-7") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"getobjecthandle\", \"Marker0 hMarker\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"getpos\", \"hMarker xMarker yMarker zMarker\")") == std::string::npos);
    CHECK(luaText.find("ctx:state().hDynamic = ctx:objectOrNil(\"Dynamic0\") "
        "-- MM9_OBJECT_POSITION_COLLAPSE.scr:9") != std::string::npos);
    CHECK(luaText.find("ctx:object(\"hDynamic\"):setPos(\"xMarker\", \"yMarker\", \"zMarker\") "
        "-- MM9_OBJECT_POSITION_COLLAPSE.scr:10") != std::string::npos);
    CHECK(luaText.find("ctx:state().hChecked = ctx:objectOrNil(\"Checked\") "
        "-- MM9_OBJECT_POSITION_COLLAPSE.scr:12") != std::string::npos);
    CHECK(luaText.find("ctx:state().x, ctx:state().y, ctx:state().z = "
        "ctx:object(\"hChecked\"):pos() -- MM9_OBJECT_POSITION_COLLAPSE.scr:14") != std::string::npos);
    CHECK(luaText.find("ctx:state().hLater = ctx:objectOrNil(\"Later0\") "
        "-- MM9_OBJECT_POSITION_COLLAPSE.scr:17") != std::string::npos);
    CHECK(luaText.find("ctx:state().xLater, ctx:state().yLater, ctx:state().zLater = "
        "ctx:object(\"hLater\"):pos() -- MM9_OBJECT_POSITION_COLLAPSE.scr:18") != std::string::npos);
    CHECK(luaText.find("ctx:trigger(\"hLater\", \"Use\")") != std::string::npos);
}

TEST_CASE("MM9 script Lua generator lowers standalone generic object position commands")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_OBJECT_POSITION.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "GetPOS hTarget, x, y, z\n"
        "SetPos hTarget, x, y, z\n"
        "SetPos hTarget, -1, 2.5, 3\n"
        "GetPOS NULL, x, y, z\n"
        "SetPos 0, x, y, z\n"
        "GetPOS hTarget, x, y\n"
        "SetPos hTarget, x, y, z, Done\n"
        "GetPOS hTarget x2, y2, z2\n"
        "SetPos hTarget, x2 y2 z2\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:state().x, ctx:state().y, ctx:state().z = "
        "ctx:object(\"hTarget\"):pos() -- MM9_OBJECT_POSITION.scr:2") != std::string::npos);
    CHECK(luaText.find("ctx:object(\"hTarget\"):setPos(\"x\", \"y\", \"z\") "
        "-- MM9_OBJECT_POSITION.scr:3") != std::string::npos);
    CHECK(luaText.find("ctx:object(\"hTarget\"):setPos(-1, 2.5, 3) -- MM9_OBJECT_POSITION.scr:4") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"getpos\", \"NULL, x, y, z\") -- MM9_OBJECT_POSITION.scr:5") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"setpos\", \"0, x, y, z\") -- MM9_OBJECT_POSITION.scr:6") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"getpos\", \"hTarget, x, y\") -- MM9_OBJECT_POSITION.scr:7") !=
        std::string::npos);
    CHECK(luaText.find("ctx:object(\"hTarget\"):setPos(\"x\", \"y\", \"z\") "
        "-- MM9_OBJECT_POSITION.scr:8") != std::string::npos);
    CHECK(luaText.find("ctx:state().x2, ctx:state().y2, ctx:state().z2 = "
        "ctx:object(\"hTarget\"):pos() -- MM9_OBJECT_POSITION.scr:9") != std::string::npos);
    CHECK(luaText.find("ctx:object(\"hTarget\"):setPos(\"x2\", \"y2\", \"z2\") "
        "-- MM9_OBJECT_POSITION.scr:10") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"getpos\", \"hTarget, x, y, z\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"setpos\", \"hTarget, x, y, z\")") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator lowers standalone generic object velocity and facing commands")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_OBJECT_MOTION.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "GetVelocity hTarget, vx, vy, vz\n"
        "SetVelocity hTarget, vx, vy, vz\n"
        "SetVelocity hTarget, -1, 2.5, 3\n"
        "GetFaceDir hTarget, dx, dy, dz\n"
        "GetForwardDir hTarget, fdx, fdy, fdz\n"
        "GetRightDir hTarget, rdx, rdy, rdz\n"
        "GetLeftDir ldx, ldy, ldz\n"
        "GetReverseDir bdx, bdy, bdz\n"
        "FaceDir dx, dy, dz\n"
        "FaceDir dx, dy, dz, 360\n"
        "GetVelocity NULL, vx, vy, vz\n"
        "SetVelocity 0, vx, vy, vz\n"
        "GetFaceDir hTarget, dx, dy\n"
        "FaceDir hTarget, dx, dy, dz\n"
        "FaceDir dx, dy, dz, 360, Done\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:state().vx, ctx:state().vy, ctx:state().vz = "
        "ctx:object(\"hTarget\"):velocity() -- MM9_OBJECT_MOTION.scr:2") != std::string::npos);
    CHECK(luaText.find("ctx:object(\"hTarget\"):setVelocity(\"vx\", \"vy\", \"vz\") "
        "-- MM9_OBJECT_MOTION.scr:3") != std::string::npos);
    CHECK(luaText.find("ctx:object(\"hTarget\"):setVelocity(-1, 2.5, 3) -- MM9_OBJECT_MOTION.scr:4") !=
        std::string::npos);
    CHECK(luaText.find("ctx:state().dx, ctx:state().dy, ctx:state().dz = "
        "ctx:object(\"hTarget\"):rotation() -- MM9_OBJECT_MOTION.scr:5") != std::string::npos);
    CHECK(luaText.find("ctx:state().fdx, ctx:state().fdy, ctx:state().fdz = "
        "ctx:object(\"hTarget\"):forwardDir() -- MM9_OBJECT_MOTION.scr:6") != std::string::npos);
    CHECK(luaText.find("ctx:state().rdx, ctx:state().rdy, ctx:state().rdz = "
        "ctx:object(\"hTarget\"):rightDir() -- MM9_OBJECT_MOTION.scr:7") != std::string::npos);
    CHECK(luaText.find("ctx:state().ldx, ctx:state().ldy, ctx:state().ldz = "
        "ctx:self():leftDir() -- MM9_OBJECT_MOTION.scr:8") != std::string::npos);
    CHECK(luaText.find("ctx:state().bdx, ctx:state().bdy, ctx:state().bdz = "
        "ctx:self():reverseDir() -- MM9_OBJECT_MOTION.scr:9") != std::string::npos);
    CHECK(luaText.find("ctx:self():faceDir(\"dx\", \"dy\", \"dz\") -- MM9_OBJECT_MOTION.scr:10") !=
        std::string::npos);
    CHECK(luaText.find("ctx:self():faceDir(\"dx\", \"dy\", \"dz\", 360) "
        "-- MM9_OBJECT_MOTION.scr:11") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"getvelocity\", \"NULL, vx, vy, vz\") -- MM9_OBJECT_MOTION.scr:12") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"setvelocity\", \"0, vx, vy, vz\") -- MM9_OBJECT_MOTION.scr:13") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"getfacedir\", \"hTarget, dx, dy\") -- MM9_OBJECT_MOTION.scr:14") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"facedir\", \"hTarget, dx, dy, dz\") -- MM9_OBJECT_MOTION.scr:15") !=
        std::string::npos);
    CHECK(luaText.find("ctx:self():faceDir(\"dx\", \"dy\", \"dz\", 360, \"Done\") "
        "-- MM9_OBJECT_MOTION.scr:16") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"getvelocity\", \"hTarget, vx, vy, vz\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"setvelocity\", \"hTarget, vx, vy, vz\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"getfacedir\", \"hTarget, dx, dy, dz\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"getforwarddir\", \"hTarget, fdx, fdy, fdz\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"getrightdir\", \"hTarget, rdx, rdy, rdz\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"getleftdir\", \"ldx, ldy, ldz\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"getreversedir\", \"bdx, bdy, bdz\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"facedir\", \"dx, dy, dz\")") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator lowers simple state assignments conservatively")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_STATE_ASSIGNMENT.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "set counter, 0\n"
        "set bReady TRUE\n"
        "set sMode \"Rise\"\n"
        "add counter, 1\n"
        "subtract counter, 2\n"
        "mul counter, -3\n"
        "div counter, 0\n"
        "bCasting = FALSE\n"
        "set target, otherVar\n"
        "add counter, otherVar\n"
        "done = done + 1\n"
        "current_group = Group1\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:state().counter = 0 -- MM9_STATE_ASSIGNMENT.scr:2") != std::string::npos);
    CHECK(luaText.find("ctx:state().bReady = true -- MM9_STATE_ASSIGNMENT.scr:3") != std::string::npos);
    CHECK(luaText.find("ctx:state().sMode = \"Rise\" -- MM9_STATE_ASSIGNMENT.scr:4") != std::string::npos);
    CHECK(luaText.find("ctx:state().counter = (tonumber(ctx:state().counter) or 0) + 1 "
        "-- MM9_STATE_ASSIGNMENT.scr:5") != std::string::npos);
    CHECK(luaText.find("ctx:state().counter = (tonumber(ctx:state().counter) or 0) - 2 "
        "-- MM9_STATE_ASSIGNMENT.scr:6") != std::string::npos);
    CHECK(luaText.find("ctx:state().counter = (tonumber(ctx:state().counter) or 0) * -3 "
        "-- MM9_STATE_ASSIGNMENT.scr:7") != std::string::npos);
    CHECK(luaText.find("ctx:state().counter = 0 -- MM9_STATE_ASSIGNMENT.scr:8") != std::string::npos);
    CHECK(luaText.find("ctx:state().bCasting = false -- MM9_STATE_ASSIGNMENT.scr:9") != std::string::npos);
    CHECK(luaText.find("ctx:set(\"target\", \"otherVar\") -- MM9_STATE_ASSIGNMENT.scr:10") !=
        std::string::npos);
    CHECK(luaText.find("ctx:add(\"counter\", \"otherVar\") -- MM9_STATE_ASSIGNMENT.scr:11") !=
        std::string::npos);
    CHECK(luaText.find("ctx:set(\"done\", \"done + 1\") -- MM9_STATE_ASSIGNMENT.scr:12") !=
        std::string::npos);
    CHECK(luaText.find("ctx:set(\"current_group\", \"Group1\") -- MM9_STATE_ASSIGNMENT.scr:13") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"done\", \"= done + 1\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"current_group\", \"= Group1\")") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator lowers self and player handle assignments")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_HANDLE_ASSIGNMENT.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "GetMyHandle hMe\n"
        "GetMyHandle hCustom\n"
        "GetPlayerHandle hPlayer\n"
        "GetMyHandle 1bad\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:state().hMe = ctx:self()") == std::string::npos);
    CHECK(luaText.find("ctx:state().hCustom = ctx:self() -- MM9_HANDLE_ASSIGNMENT.scr:3") !=
        std::string::npos);
    CHECK(luaText.find("ctx:state().hPlayer = ctx:player()") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"getmyhandle\", \"1bad\") -- MM9_HANDLE_ASSIGNMENT.scr:5") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"getmyhandle\", \"hMe\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"getplayerhandle\", \"hPlayer\")") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator compacts built-in self handle aliases")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_SELF_ALIAS.scr";
    writeTextFileForTest(
        path,
        ":OnMove\n"
        "GetMyHandle g_hMyObject\n"
        "SetFlag g_hmyobject visible\n"
        "GetPOS g_hMyObject MyX MyY MyZ\n"
        "RemoveObject g_hmyobject\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:state().g_hMyObject = ctx:self()") == std::string::npos);
    CHECK(luaText.find("ctx:self():setFlag(\"visible\", true) -- MM9_SELF_ALIAS.scr:3") !=
        std::string::npos);
    CHECK(luaText.find("ctx:state().MyX, ctx:state().MyY, ctx:state().MyZ = ctx:self():pos() "
        "-- MM9_SELF_ALIAS.scr:4") != std::string::npos);
    CHECK(luaText.find("ctx:self():remove() -- MM9_SELF_ALIAS.scr:5") != std::string::npos);
    CHECK(luaText.find("ctx:object(\"g_hmyobject\")") == std::string::npos);
    CHECK(luaText.find("ctx:object(\"g_hMyObject\")") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator compacts transient self handle aliases until overwritten")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_TRANSIENT_SELF_ALIAS.scr";
    writeTextFileForTest(
        path,
        ":OnEnter\n"
        "GetMyHandle g_hobject\n"
        "SetFlag g_hobject visible\n"
        "SetFlag g_hobject solid\n"
        "GetObjectHandle Marker2 g_hobject\n"
        "WalkTo g_hobject 16 DoNothing\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:state().g_hobject = ctx:self() -- MM9_TRANSIENT_SELF_ALIAS.scr:2") !=
        std::string::npos);
    CHECK(luaText.find("ctx:self():setFlag(\"visible\", true) -- MM9_TRANSIENT_SELF_ALIAS.scr:3") !=
        std::string::npos);
    CHECK(luaText.find("ctx:self():setFlag(\"solid\", true) -- MM9_TRANSIENT_SELF_ALIAS.scr:4") !=
        std::string::npos);
    CHECK(luaText.find("ctx:state().g_hobject = ctx:objectOrNil(\"Marker2\") "
        "-- MM9_TRANSIENT_SELF_ALIAS.scr:5") != std::string::npos);
    CHECK(luaText.find("ctx:self():walkTo(ctx:object(\"g_hobject\"), 16, \"DoNothing\") "
        "-- MM9_TRANSIENT_SELF_ALIAS.scr:6") != std::string::npos);
    CHECK(luaText.find("ctx:object(\"g_hobject\"):setFlag") == std::string::npos);
    CHECK(luaText.find("ctx:self():walkTo(ctx:self(), 16") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator carries self handle aliases into if blocks until overwritten")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_IF_SELF_ALIAS.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "GetMyHandle g_hobject\n"
        "if (g_nTemp==1)\n"
        "ClearFlag g_hobject visible\n"
        "GetObjectHandle Marker2 g_hobject\n"
        "SetFlag g_hobject solid\n"
        "else\n"
        "SetFlag g_hobject gravity\n"
        "endif\n"
        "SetFlag g_hobject solid\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:self():setFlag(\"visible\", false) -- MM9_IF_SELF_ALIAS.scr:4") !=
        std::string::npos);
    CHECK(luaText.find("ctx:object(\"Marker2\"):setFlag(\"solid\", true) -- MM9_IF_SELF_ALIAS.scr:5-6") !=
        std::string::npos);
    CHECK(luaText.find("ctx:self():setFlag(\"gravity\", true) -- MM9_IF_SELF_ALIAS.scr:8") !=
        std::string::npos);
    CHECK(luaText.find("ctx:object(\"g_hobject\"):setFlag(\"solid\", true) -- MM9_IF_SELF_ALIAS.scr:10") !=
        std::string::npos);
}

TEST_CASE("MM9 script Lua generator carries self handle aliases after branches only when all paths agree")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_JOIN_SELF_ALIAS.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "GetMyHandle g_hobject\n"
        "if (g_nTemp==1)\n"
        "SetFlag g_hobject visible\n"
        "endif\n"
        "SetFlag g_hobject solid\n"
        "if (g_nTemp==2)\n"
        "GetObjectHandle Marker2 g_hobject\n"
        "else\n"
        "SetFlag g_hobject gravity\n"
        "endif\n"
        "SetFlag g_hobject visible\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:self():setFlag(\"visible\", true) -- MM9_JOIN_SELF_ALIAS.scr:4") !=
        std::string::npos);
    CHECK(luaText.find("ctx:self():setFlag(\"solid\", true) -- MM9_JOIN_SELF_ALIAS.scr:6") !=
        std::string::npos);
    CHECK(luaText.find("ctx:state().g_hobject = ctx:objectOrNil(\"Marker2\") -- MM9_JOIN_SELF_ALIAS.scr:8") !=
        std::string::npos);
    CHECK(luaText.find("ctx:self():setFlag(\"gravity\", true) -- MM9_JOIN_SELF_ALIAS.scr:10") !=
        std::string::npos);
    CHECK(luaText.find("ctx:object(\"g_hobject\"):setFlag(\"visible\", true) -- MM9_JOIN_SELF_ALIAS.scr:12") !=
        std::string::npos);
}

TEST_CASE("MM9 script Lua generator does not carry self handle aliases into while loops")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_WHILE_SELF_ALIAS.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "GetMyHandle g_hobject\n"
        "while (g_nTemp==1)\n"
        "ClearFlag g_hobject visible\n"
        "endwhile\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:object(\"g_hobject\"):setFlag(\"visible\", false) "
        "-- MM9_WHILE_SELF_ALIAS.scr:4") != std::string::npos);
    CHECK(luaText.find("ctx:self():setFlag(\"visible\", false)") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator compacts built-in player handle aliases")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_PLAYER_ALIAS.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "GetPlayerHandle hPlayer\n"
        "GetFaceDir hPlayer, dx, dy, dz\n"
        "GetPlayerHandle g_hPlayer\n"
        "IsPlayer g_hPlayer, bPlayer\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:state().hPlayer = ctx:player()") == std::string::npos);
    CHECK(luaText.find("ctx:state().dx, ctx:state().dy, ctx:state().dz = ctx:player():rotation() "
        "-- MM9_PLAYER_ALIAS.scr:3") != std::string::npos);
    CHECK(luaText.find("ctx:state().g_hPlayer = ctx:player() -- MM9_PLAYER_ALIAS.scr:4") !=
        std::string::npos);
    CHECK(luaText.find("ctx:state().bPlayer = ctx:player():isPlayer() "
        "-- MM9_PLAYER_ALIAS.scr:5") != std::string::npos);
}

TEST_CASE("MM9 script Lua generator lowers generic object handle lookups")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_OBJECT_HANDLE_LOOKUP.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "GetObjectHandle TargetMarker, hTarget\n"
        "GetObjectHandle sDynamicTarget hDynamicTarget\n"
        "GetMyHandle , hMeAgain\n"
        "GetObjectHandle , g_sSpawn, g_hSpawn\n"
        "GetObjectHandle MissingObject, 1bad\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:state().hTarget = ctx:objectOrNil(\"TargetMarker\") "
        "-- MM9_OBJECT_HANDLE_LOOKUP.scr:2") != std::string::npos);
    CHECK(luaText.find("ctx:state().hDynamicTarget = ctx:objectOrNil(\"sDynamicTarget\") "
        "-- MM9_OBJECT_HANDLE_LOOKUP.scr:3") != std::string::npos);
    CHECK(luaText.find("ctx:state().hMeAgain = ctx:self() -- MM9_OBJECT_HANDLE_LOOKUP.scr:4") !=
        std::string::npos);
    CHECK(luaText.find("ctx:state().g_hSpawn = ctx:objectOrNil(\"g_sSpawn\") "
        "-- MM9_OBJECT_HANDLE_LOOKUP.scr:5") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"getobjecthandle\", \"MissingObject, 1bad\") "
        "-- MM9_OBJECT_HANDLE_LOOKUP.scr:6") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"getobjecthandle\", \"TargetMarker, hTarget\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"getobjecthandle\", \"sDynamicTarget hDynamicTarget\")") ==
        std::string::npos);
}

TEST_CASE("MM9 script Lua generator lowers generic object identity queries")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_OBJECT_IDENTITY.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "GetObjectName hTarget sName\n"
        "GetClassName hTarget, sClass\n"
        "IsClass hTarget, \"Marker\", bMarker\n"
        "IsClass hTarget, Actor, bActor\n"
        "GetObjectName hTarget 1bad\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:state().sName = ctx:object(\"hTarget\"):name() -- MM9_OBJECT_IDENTITY.scr:2") !=
        std::string::npos);
    CHECK(luaText.find("ctx:state().sClass = ctx:object(\"hTarget\"):className() -- MM9_OBJECT_IDENTITY.scr:3") !=
        std::string::npos);
    CHECK(luaText.find("ctx:state().bMarker = ctx:object(\"hTarget\"):isClass(\"Marker\") "
        "-- MM9_OBJECT_IDENTITY.scr:4") != std::string::npos);
    CHECK(luaText.find("ctx:state().bActor = ctx:object(\"hTarget\"):isClass(\"Actor\") "
        "-- MM9_OBJECT_IDENTITY.scr:5") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"getobjectname\", \"hTarget 1bad\") -- MM9_OBJECT_IDENTITY.scr:6") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"getobjectname\", \"hTarget sName\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"getclassname\", \"hTarget, sClass\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"isclass\", \"hTarget, \\\"Marker\\\", bMarker\")") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator lowers generic object state queries")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_OBJECT_QUERY.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "IsPlayer hTarget, bPlayer\n"
        "IsActor hTarget, bActor\n"
        "IsAI hTarget, bAI\n"
        "IsVisible hTarget, bVisible\n"
        "IsObjectActive hTarget, bActive\n"
        "IsPlayer NULL, bPlayer\n"
        "IsVisible 0, bVisible\n"
        "IsObjectActive hTarget, 1bad\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:state().bPlayer = ctx:object(\"hTarget\"):isPlayer() "
        "-- MM9_OBJECT_QUERY.scr:2") != std::string::npos);
    CHECK(luaText.find("ctx:state().bActor = (ctx:object(\"hTarget\"):isActor() and 1 or 0) "
        "-- MM9_OBJECT_QUERY.scr:3") != std::string::npos);
    CHECK(luaText.find("ctx:state().bAI = (ctx:object(\"hTarget\"):isAi() and 1 or 0) "
        "-- MM9_OBJECT_QUERY.scr:4") != std::string::npos);
    CHECK(luaText.find("ctx:state().bVisible = ctx:object(\"hTarget\"):isVisible() "
        "-- MM9_OBJECT_QUERY.scr:5") != std::string::npos);
    CHECK(luaText.find("ctx:state().bActive = ctx:object(\"hTarget\"):isActive() "
        "-- MM9_OBJECT_QUERY.scr:6") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"isplayer\", \"NULL, bPlayer\") -- MM9_OBJECT_QUERY.scr:7") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"isvisible\", \"0, bVisible\") -- MM9_OBJECT_QUERY.scr:8") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"isobjectactive\", \"hTarget, 1bad\") "
        "-- MM9_OBJECT_QUERY.scr:9") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"isplayer\", \"hTarget, bPlayer\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"isactor\", \"hTarget, bActor\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"isai\", \"hTarget, bAI\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"isvisible\", \"hTarget, bVisible\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"isobjectactive\", \"hTarget, bActive\")") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator lowers generic object registry queries")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_OBJECT_REGISTRY.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "GetObjects AIBase, 500, 10, g_hMonsterArray, g_nMonsterCount\n"
        "GetObjects g_sEnemyName, MAX_RESURRECT_DIST, MAX_OBJECTS, g_hObjectArray, g_nTemp\n"
        "GetLiquidContainer g_hMyObject, hWater\n"
        "GetContainer g_hplayer 0 g_hobject\n"
        "GetObjects AIBase, 500, 10, bad-name, g_nMonsterCount\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:getObjects(\"AIBase\", 500, 10, \"g_hMonsterArray\", "
        "\"g_nMonsterCount\") -- MM9_OBJECT_REGISTRY.scr:2") != std::string::npos);
    CHECK(luaText.find("ctx:getObjects(\"g_sEnemyName\", \"MAX_RESURRECT_DIST\", \"MAX_OBJECTS\", "
        "\"g_hObjectArray\", \"g_nTemp\") -- MM9_OBJECT_REGISTRY.scr:3") != std::string::npos);
    CHECK(luaText.find("ctx:state().hWater = ctx:self():liquidContainer() "
        "-- MM9_OBJECT_REGISTRY.scr:4") != std::string::npos);
    CHECK(luaText.find("ctx:state().g_hobject = ctx:player():container(0) "
        "-- MM9_OBJECT_REGISTRY.scr:5") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"getobjects\", \"AIBase, 500, 10, bad-name, "
        "g_nMonsterCount\") -- MM9_OBJECT_REGISTRY.scr:6") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"getobjects\", \"AIBase, 500, 10, g_hMonsterArray, "
        "g_nMonsterCount\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"getliquidcontainer\", \"g_hMyObject, hWater\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"getcontainer\", \"g_hplayer 0 g_hobject\")") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator lowers script array access")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_ARRAY_ACCESS.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "ArrayPut spSounds, 0, sounds\\Weapons\\SwordClang.wav\n"
        "ArrayPut npItems, nTemp, g_hTarget\n"
        "ArrayGet spSounds, nRandom, sTemp\n"
        "ArrayPut KeyArray 0, 1\n"
        "ArrayGet npItems, nTemp, 1bad\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:arrayPut(\"spSounds\", 0, \"sounds\\\\Weapons\\\\SwordClang.wav\") "
        "-- MM9_ARRAY_ACCESS.scr:2") != std::string::npos);
    CHECK(luaText.find("ctx:arrayPut(\"npItems\", \"nTemp\", \"g_hTarget\") "
        "-- MM9_ARRAY_ACCESS.scr:3") != std::string::npos);
    CHECK(luaText.find("ctx:arrayGet(\"spSounds\", \"nRandom\", \"sTemp\") "
        "-- MM9_ARRAY_ACCESS.scr:4") != std::string::npos);
    CHECK(luaText.find("ctx:arrayPut(\"KeyArray\", 0, 1) -- MM9_ARRAY_ACCESS.scr:5") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"arrayget\", \"npItems, nTemp, 1bad\") "
        "-- MM9_ARRAY_ACCESS.scr:6") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"arrayput\", \"spSounds, 0, "
        "sounds\\\\Weapons\\\\SwordClang.wav\")") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator lowers runtime utility commands")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_RUNTIME_UTIL.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "GetRandomInt 0, 100, g_nRandom\n"
        "GetRandomInt 0, 5 g_ntemp\n"
        "GetRandomFloat MIN_WAIT, MAX_WAIT, random\n"
        "GetTime g_nLastAttackTime\n"
        "GetTime 1bad\n"
        "Debugout sTemp\n"
        "cprint backpedal\n"
        "IsTurnBased g_nTemp\n"
        "GetPcVoice g_nVoice\n"
        "GetGameTime nHour nMinute\n"
        "SetParam 0, Door0\n"
        "RestorePath\n"
        "SavePath\n"
        "CastRay g_posX, g_posY, g_posZ, 100, g_hObject, g_nTemp\n"
        "DoCallback 2\n"
        "ExitScript\n"
        "TraceOff\n"
        "TraceOn\n"
        "Breakpoint\n"
        "Dont_Include_This_File\n"
        "GetPlayerId g_hplayer, g_nPlayerId\n"
        "GetPlayerNbr g_hplayer, g_nPlayerNbr\n"
        "GetPlayersWithinDist VolumeX, VolumeY, VolumeZ, 512, PlayerIds, 8, Playercount\n"
        "ConsoleCommand NumConsoleLines 1\n"
        "DoHighScore\n"
        "ClearCondition 13\n"
        "SetCondition 13\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:randomInt(0, 100, \"g_nRandom\") -- MM9_RUNTIME_UTIL.scr:2") !=
        std::string::npos);
    CHECK(luaText.find("ctx:randomInt(0, 5, \"g_ntemp\") -- MM9_RUNTIME_UTIL.scr:3") !=
        std::string::npos);
    CHECK(luaText.find("ctx:randomFloat(\"MIN_WAIT\", \"MAX_WAIT\", \"random\") "
        "-- MM9_RUNTIME_UTIL.scr:4") != std::string::npos);
    CHECK(luaText.find("ctx:getTime(\"g_nLastAttackTime\") -- MM9_RUNTIME_UTIL.scr:5") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"gettime\", \"1bad\") -- MM9_RUNTIME_UTIL.scr:6") !=
        std::string::npos);
    CHECK(luaText.find("ctx:debugOut(\"sTemp\") -- MM9_RUNTIME_UTIL.scr:7") !=
        std::string::npos);
    CHECK(luaText.find("ctx:cprint(\"backpedal\") -- MM9_RUNTIME_UTIL.scr:8") !=
        std::string::npos);
    CHECK(luaText.find("ctx:isTurnBased(\"g_nTemp\") -- MM9_RUNTIME_UTIL.scr:9") !=
        std::string::npos);
    CHECK(luaText.find("ctx:getPcVoice(\"g_nVoice\") -- MM9_RUNTIME_UTIL.scr:10") !=
        std::string::npos);
    CHECK(luaText.find("ctx:getGameTime(\"nHour\", \"nMinute\") -- MM9_RUNTIME_UTIL.scr:11") !=
        std::string::npos);
    CHECK(luaText.find("ctx:setParam(0, \"Door0\") -- MM9_RUNTIME_UTIL.scr:12") != std::string::npos);
    CHECK(luaText.find("ctx:restorePath() -- MM9_RUNTIME_UTIL.scr:13") != std::string::npos);
    CHECK(luaText.find("ctx:savePath() -- MM9_RUNTIME_UTIL.scr:14") != std::string::npos);
    CHECK(luaText.find("ctx:castRay(\"g_posX\", \"g_posY\", \"g_posZ\", 100, \"g_hObject\", \"g_nTemp\") "
        "-- MM9_RUNTIME_UTIL.scr:15") != std::string::npos);
    CHECK(luaText.find("ctx:doCallback(2) -- MM9_RUNTIME_UTIL.scr:16") != std::string::npos);
    CHECK(luaText.find("ctx:exitScript() -- MM9_RUNTIME_UTIL.scr:17") != std::string::npos);
    CHECK(luaText.find("ctx:traceOff() -- MM9_RUNTIME_UTIL.scr:18") != std::string::npos);
    CHECK(luaText.find("ctx:traceOn() -- MM9_RUNTIME_UTIL.scr:19") != std::string::npos);
    CHECK(luaText.find("ctx:breakpoint() -- MM9_RUNTIME_UTIL.scr:20") != std::string::npos);
    CHECK(luaText.find("ctx:dontIncludeThisFile() -- MM9_RUNTIME_UTIL.scr:21") !=
        std::string::npos);
    CHECK(luaText.find("ctx:getPlayerId(ctx:player(), \"g_nPlayerId\") -- MM9_RUNTIME_UTIL.scr:22") !=
        std::string::npos);
    CHECK(luaText.find("ctx:getPlayerNumber(ctx:player(), \"g_nPlayerNbr\") -- MM9_RUNTIME_UTIL.scr:23") !=
        std::string::npos);
    CHECK(luaText.find("ctx:getPlayersWithinDist(\"VolumeX\", \"VolumeY\", \"VolumeZ\", 512, "
        "\"PlayerIds\", 8, \"Playercount\") -- MM9_RUNTIME_UTIL.scr:24") != std::string::npos);
    CHECK(luaText.find("ctx:consoleCommand(\"NumConsoleLines\", 1) -- MM9_RUNTIME_UTIL.scr:25") !=
        std::string::npos);
    CHECK(luaText.find("ctx:doHighScore() -- MM9_RUNTIME_UTIL.scr:26") != std::string::npos);
    CHECK(luaText.find("ctx:clearCondition(13) -- MM9_RUNTIME_UTIL.scr:27") != std::string::npos);
    CHECK(luaText.find("ctx:setCondition(13) -- MM9_RUNTIME_UTIL.scr:28") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"getrandomint\", \"0, 100, g_nRandom\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"getrandomfloat\", \"MIN_WAIT, MAX_WAIT, random\")") ==
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"debugout\", \"sTemp\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"cprint\", \"backpedal\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"isturnbased\", \"g_nTemp\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"getpcvoice\", \"g_nVoice\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"getgametime\", \"nHour nMinute\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"setparam\", \"0, Door0\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"restorepath\", \"\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"savepath\", \"\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"castray\", \"g_posX, g_posY, g_posZ, 100, g_hObject, g_nTemp\")") ==
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"docallback\", \"2\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"exitscript\", \"\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"getplayerid\", \"g_hplayer, g_nPlayerId\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"getplayernbr\", \"g_hplayer, g_nPlayerNbr\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"getplayerswithindist\", \"VolumeX, VolumeY, VolumeZ, 512, "
        "PlayerIds, 8, Playercount\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"consolecommand\", \"NumConsoleLines 1\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"dohighscore\", \"\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"clearcondition\", \"13\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"setcondition\", \"13\")") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator lowers minute schedule callbacks")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_AT_TIME.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "@m 6 : 15 GoWork WarpWork\n"
        "@m 00:15 OnBlabber\n"
        "@m nHour : nMinute Givekey Givekey\n"
        "@m 7 : 0, StartTrip, DoNothing\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:atTime(6, 15, \"GoWork\", \"WarpWork\") -- MM9_AT_TIME.scr:2") !=
        std::string::npos);
    CHECK(luaText.find("ctx:atTime(0, 15, \"OnBlabber\") -- MM9_AT_TIME.scr:3") != std::string::npos);
    CHECK(luaText.find("ctx:atTime(\"nHour\", \"nMinute\", \"Givekey\", \"Givekey\") "
        "-- MM9_AT_TIME.scr:4") != std::string::npos);
    CHECK(luaText.find("ctx:atTime(7, 0, \"StartTrip\", \"DoNothing\") -- MM9_AT_TIME.scr:5") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"@m\"") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator lowers vector utility commands")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_VECTOR_UTIL.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "VecScale dx, dy, dz, 5\n"
        "VecNorm dx, dy, dz\n"
        "VecSub ax, ay, az, 1, 2, 3\n"
        "VecAdd ax, ay, az, 1, 2, 3\n"
        "CalcDist 0, 0, 0, 3, 4, 0, dist\n"
        "VecDist x1, y1, z1, x2, y2, z2, dist2\n"
        "VecMag 3, 4, 0, magOut\n"
        "VecAngle 1, 0, 0, 0, 1, 0, angleOut\n"
        "RotateDir dx, dy, dz, 90\n"
        "VecScale 1bad, dy, dz, 5\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:state().dx, ctx:state().dy, ctx:state().dz = "
        "ctx:vecScale(\"dx\", \"dy\", \"dz\", 5) -- MM9_VECTOR_UTIL.scr:2") != std::string::npos);
    CHECK(luaText.find("ctx:state().dx, ctx:state().dy, ctx:state().dz = "
        "ctx:vecNorm(\"dx\", \"dy\", \"dz\") -- MM9_VECTOR_UTIL.scr:3") != std::string::npos);
    CHECK(luaText.find("ctx:state().ax, ctx:state().ay, ctx:state().az = "
        "ctx:vecSub(\"ax\", \"ay\", \"az\", 1, 2, 3) -- MM9_VECTOR_UTIL.scr:4") !=
        std::string::npos);
    CHECK(luaText.find("ctx:state().ax, ctx:state().ay, ctx:state().az = "
        "ctx:vecAdd(\"ax\", \"ay\", \"az\", 1, 2, 3) -- MM9_VECTOR_UTIL.scr:5") !=
        std::string::npos);
    CHECK(luaText.find("ctx:state().dist = ctx:vecDist(0, 0, 0, 3, 4, 0) "
        "-- MM9_VECTOR_UTIL.scr:6") != std::string::npos);
    CHECK(luaText.find("ctx:state().dist2 = ctx:vecDist(\"x1\", \"y1\", \"z1\", \"x2\", \"y2\", \"z2\") "
        "-- MM9_VECTOR_UTIL.scr:7") != std::string::npos);
    CHECK(luaText.find("ctx:state().magOut = ctx:vecMag(3, 4, 0) -- MM9_VECTOR_UTIL.scr:8") !=
        std::string::npos);
    CHECK(luaText.find("ctx:state().angleOut = ctx:vecAngle(1, 0, 0, 0, 1, 0) "
        "-- MM9_VECTOR_UTIL.scr:9") != std::string::npos);
    CHECK(luaText.find("ctx:state().dx, ctx:state().dy, ctx:state().dz = "
        "ctx:rotateDir(\"dx\", \"dy\", \"dz\", 90) -- MM9_VECTOR_UTIL.scr:10") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"vecscale\", \"1bad, dy, dz, 5\") -- MM9_VECTOR_UTIL.scr:11") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"vecscale\", \"dx, dy, dz, 5\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"vecnorm\", \"dx, dy, dz\")") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator lowers generic state commands")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_STATE_COMMANDS.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "set Jarl, Bjarni\n"
        "set Current_Marker L_Marker\n"
        "add nDestPosY, nMoveDistance\n"
        "sub nDestPosY, 4\n"
        "subtract sounddur, .4\n"
        "mul minJumpDist, jumpTime\n"
        "div nTotal, nCount\n"
        "mod nMoveCount, 2\n"
        "set 1bad, value\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:set(\"Jarl\", \"Bjarni\") -- MM9_STATE_COMMANDS.scr:2") !=
        std::string::npos);
    CHECK(luaText.find("ctx:set(\"Current_Marker\", \"L_Marker\") -- MM9_STATE_COMMANDS.scr:3") !=
        std::string::npos);
    CHECK(luaText.find("ctx:add(\"nDestPosY\", \"nMoveDistance\") -- MM9_STATE_COMMANDS.scr:4") !=
        std::string::npos);
    CHECK(luaText.find("ctx:state().nDestPosY = (tonumber(ctx:state().nDestPosY) or 0) - 4 "
        "-- MM9_STATE_COMMANDS.scr:5") !=
        std::string::npos);
    CHECK(luaText.find("ctx:sub(\"sounddur\", .4) -- MM9_STATE_COMMANDS.scr:6") !=
        std::string::npos);
    CHECK(luaText.find("ctx:mul(\"minJumpDist\", \"jumpTime\") -- MM9_STATE_COMMANDS.scr:7") !=
        std::string::npos);
    CHECK(luaText.find("ctx:div(\"nTotal\", \"nCount\") -- MM9_STATE_COMMANDS.scr:8") !=
        std::string::npos);
    CHECK(luaText.find("ctx:mod(\"nMoveCount\", 2) -- MM9_STATE_COMMANDS.scr:9") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"set\", \"Jarl, Bjarni\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"mod\", \"nMoveCount, 2\")") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator lowers scheduler wait commands")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_WAIT.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "Wait 0, 0.5, Main2\n"
        "Wait 0 .1 main2\n"
        "Wait 1 6.5, Trigger2\n"
        "Wait HANGOUT_WAIT, nWait, LookForPerson\n"
        "Wait 3, OnAware\n"
        "Wait 1, 3 TurnCameraOff\n"
        "Wait .5 anim\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:wait(0, 0.5, \"Main2\") -- MM9_WAIT.scr:2") != std::string::npos);
    CHECK(luaText.find("ctx:wait(0, .1, \"main2\") -- MM9_WAIT.scr:3") != std::string::npos);
    CHECK(luaText.find("ctx:wait(1, 6.5, \"Trigger2\") -- MM9_WAIT.scr:4") != std::string::npos);
    CHECK(luaText.find("ctx:wait(\"HANGOUT_WAIT\", \"nWait\", \"LookForPerson\") -- MM9_WAIT.scr:5") !=
        std::string::npos);
    CHECK(luaText.find("ctx:wait(3, 3, \"OnAware\") -- MM9_WAIT.scr:6") != std::string::npos);
    CHECK(luaText.find("ctx:wait(1, 3, \"TurnCameraOff\") -- MM9_WAIT.scr:7") != std::string::npos);
    CHECK(luaText.find("ctx:wait(.5, .5, \"anim\") -- MM9_WAIT.scr:8") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"wait\", \"0, 0.5, Main2\")") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator lowers party and script service commands")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_PARTY_SCRIPT.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "HasGold 500 g_ntemp\n"
        "TakeGold 500\n"
        "GivePromo Lich Char1\n"
        "GetAttribute STAT_MIGHT, nMight\n"
        "GetPcLevel 0 g_nLevel\n"
        "Heal hPlayer, nQuantity\n"
        "GiveAttribute STAT_SPEED, 3, TRUE, 10\n"
        "CacheScript TEST.scr\n"
        "RunScript g_sDefaultScript\n"
        "AddNPC 2 g_hobject\n"
        "RemoveNPC 2 g_hobject\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:hasGold(500, \"g_ntemp\") -- MM9_PARTY_SCRIPT.scr:2") != std::string::npos);
    CHECK(luaText.find("ctx:takeGold(500) -- MM9_PARTY_SCRIPT.scr:3") != std::string::npos);
    CHECK(luaText.find("ctx:givePromo(\"Lich\", \"Char1\") -- MM9_PARTY_SCRIPT.scr:4") != std::string::npos);
    CHECK(luaText.find("ctx:getAttribute(\"STAT_MIGHT\", \"nMight\") -- MM9_PARTY_SCRIPT.scr:5") !=
        std::string::npos);
    CHECK(luaText.find("ctx:getPcLevel(0, \"g_nLevel\") -- MM9_PARTY_SCRIPT.scr:6") !=
        std::string::npos);
    CHECK(luaText.find("ctx:heal(ctx:player(), \"nQuantity\") -- MM9_PARTY_SCRIPT.scr:7") !=
        std::string::npos);
    CHECK(luaText.find("ctx:giveAttribute(\"STAT_SPEED\", 3, \"TRUE\", 10) -- MM9_PARTY_SCRIPT.scr:8") !=
        std::string::npos);
    CHECK(luaText.find("ctx:cacheScript(\"TEST.scr\") -- MM9_PARTY_SCRIPT.scr:9") != std::string::npos);
    CHECK(luaText.find("ctx:runScript(\"g_sDefaultScript\") -- MM9_PARTY_SCRIPT.scr:10") != std::string::npos);
    CHECK(luaText.find("ctx:addNpc(2, \"g_hobject\") -- MM9_PARTY_SCRIPT.scr:11") != std::string::npos);
    CHECK(luaText.find("ctx:removeNpc(2, \"g_hobject\") -- MM9_PARTY_SCRIPT.scr:12") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"hasgold\"") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"givepromo\"") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"getpclevel\"") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"heal\"") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"addnpc\"") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"removenpc\"") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"runscript\"") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator lowers audio service commands")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_AUDIO.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "CacheSound \"sounds\\door\\doorlatch01.wav\"\n"
        "PlaySound sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100\n"
        "PlaySound Sounds\\Door\\doorslammetal01.wav DoNothing hDummy 400 FALSE 100\n"
        "PlaySoundHandle loop.wav, soundhandle, 100, TRUE, 90\n"
        "GetSoundDuration , soundhandle, sounddur\n"
        "IsSoundDone soundhandle, soundDone\n"
        "KillSound soundhandle\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:cacheSound(\"sounds\\\\door\\\\doorlatch01.wav\") -- MM9_AUDIO.scr:2") !=
        std::string::npos);
    CHECK(luaText.find("ctx:playSound(\"sounds\\\\events\\\\quest.wav\", \"DoNothing\", 100, 240, "
        "\"FALSE\", 100) -- MM9_AUDIO.scr:3") != std::string::npos);
    CHECK(luaText.find("ctx:playSound(\"Sounds\\\\Door\\\\doorslammetal01.wav\", \"DoNothing\", "
        "\"hDummy\", 400, \"FALSE\", 100) -- MM9_AUDIO.scr:4") != std::string::npos);
    CHECK(luaText.find("ctx:playSoundHandle(\"loop.wav\", \"soundhandle\", 100, \"TRUE\", 90) "
        "-- MM9_AUDIO.scr:5") != std::string::npos);
    CHECK(luaText.find("ctx:getSoundDuration(\"\", \"soundhandle\", \"sounddur\") -- MM9_AUDIO.scr:6") !=
        std::string::npos);
    CHECK(luaText.find("ctx:isSoundDone(\"soundhandle\", \"soundDone\") -- MM9_AUDIO.scr:7") !=
        std::string::npos);
    CHECK(luaText.find("ctx:killSound(\"soundhandle\") -- MM9_AUDIO.scr:8") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"playsound\", \"sounds\\\\events\\\\quest.wav") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator lowers model animation service commands")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_ANIMATION.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "PlayAnim Taunt, StartSequence\n"
        "LoopAnim Hang, 0 CheckTrigger\n"
        "BlendAnim Aware, BlendDone\n"
        "GetCurrAnim g_hMyObject, g_nTemp\n"
        "GetAnimName g_hMyObject, g_nTemp, g_sTemp\n"
        "GetAnimNbr g_hMyObject, Cower, g_nCowerAnim\n"
        "PlayAnimSound JumpingDown,0\n"
        "SetAnimPlaying FALSE\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:self():playAnimation(\"Taunt\", \"StartSequence\") "
        "-- MM9_ANIMATION.scr:2") != std::string::npos);
    CHECK(luaText.find("ctx:self():loopAnimation(\"Hang\", 0, \"CheckTrigger\") "
        "-- MM9_ANIMATION.scr:3") != std::string::npos);
    CHECK(luaText.find("ctx:self():blendAnimation(\"Aware\", \"BlendDone\") "
        "-- MM9_ANIMATION.scr:4") != std::string::npos);
    CHECK(luaText.find("ctx:self():getCurrentAnimation(\"g_nTemp\") "
        "-- MM9_ANIMATION.scr:5") != std::string::npos);
    CHECK(luaText.find("ctx:self():getAnimationName(\"g_nTemp\", \"g_sTemp\") "
        "-- MM9_ANIMATION.scr:6") != std::string::npos);
    CHECK(luaText.find("ctx:self():getAnimationNumber(\"Cower\", \"g_nCowerAnim\") "
        "-- MM9_ANIMATION.scr:7") != std::string::npos);
    CHECK(luaText.find("ctx:self():playAnimSound(\"JumpingDown\", 0) "
        "-- MM9_ANIMATION.scr:8") != std::string::npos);
    CHECK(luaText.find("ctx:self():setAnimationPlaying(\"FALSE\") "
        "-- MM9_ANIMATION.scr:9") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"playanim\", \"Taunt, StartSequence\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"loopanim\", \"Hang, 0, CheckTrigger\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"blendanim\"") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"getcurranim\"") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"getanimname\"") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"getanimnbr\"") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"playanimsound\"") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"setanimplaying\"") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator lowers client FX service commands")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_CLIENT_FX.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "CacheClientFX SPELL_BLACKSMOKE\n"
        "DoClientFX hMe, SPELL_BLACKSMOKE, TRUE, TRUE\n"
        "DoClientFX hCaster, \"fireblue\", 0, 1\n"
        "CreateFX spell, hCreated, 1\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:cacheClientFx(\"SPELL_BLACKSMOKE\") -- MM9_CLIENT_FX.scr:2") !=
        std::string::npos);
    CHECK(luaText.find("ctx:self():doClientFx(\"SPELL_BLACKSMOKE\", \"TRUE\", \"TRUE\") "
        "-- MM9_CLIENT_FX.scr:3") != std::string::npos);
    CHECK(luaText.find("ctx:object(\"hCaster\"):doClientFx(\"fireblue\", 0, 1) "
        "-- MM9_CLIENT_FX.scr:4") != std::string::npos);
    CHECK(luaText.find("ctx:object(\"hCreated\"):createFx(\"spell\", 1) -- MM9_CLIENT_FX.scr:5") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"cacheclientfx\", \"SPELL_BLACKSMOKE\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"doclientfx\", \"hMe, SPELL_BLACKSMOKE") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"createfx\", \"spell, hCreated, 1\")") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator lowers model capability service commands")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_MODEL_CAPABILITY.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "SetModelFilenames models\\flyingicky.abc TEXTURES\\LevelTextures\\Misc\\black.dtx\n"
        "AttachProp kirasword.ABC, KiraSword.dtx, Sheath, hProp\n"
        "DetachProp hProp, FALSE\n"
        "GetSocketPos RHand1,g_posX,g_posY,g_posZ\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:self():setModelFilenames(\"models\\\\flyingicky.abc\", "
        "\"TEXTURES\\\\LevelTextures\\\\Misc\\\\black.dtx\") -- MM9_MODEL_CAPABILITY.scr:2") !=
        std::string::npos);
    CHECK(luaText.find("ctx:self():attachProp(\"kirasword.ABC\", \"KiraSword.dtx\", \"Sheath\", "
        "ctx:object(\"hProp\")) -- MM9_MODEL_CAPABILITY.scr:3") != std::string::npos);
    CHECK(luaText.find("ctx:self():detachProp(ctx:object(\"hProp\"), \"FALSE\") "
        "-- MM9_MODEL_CAPABILITY.scr:4") != std::string::npos);
    CHECK(luaText.find("ctx:state().g_posX, ctx:state().g_posY, ctx:state().g_posZ = "
        "ctx:self():socketPos(\"RHand1\") -- MM9_MODEL_CAPABILITY.scr:5") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"setmodelfilenames\"") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"attachprop\"") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"detachprop\"") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"getsocketpos\"") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator lowers movement service commands")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_MOVEMENT.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "MoveToPos xMe YMe zMe 100 MoveDone\n"
        "WalkTo hTarget, 10, WalkDone\n"
        "RunTo g_hobject 32 RunDone\n"
        "GetObjectHandle Marker2 g_hobject\n"
        "WalkTo g_hobject 16 DoNothing\n"
        "MoveDir dx,0,dz, nDist, nSpeed, Ready\n"
        "FaceObject hTarget 180 FaceDone\n"
        "FacePos xMe, yMe, zMe, 45, FacePosDone\n"
        "Stop\n"
        "Walk\n"
        "Run\n"
        "Rotate 0,1,0,g_turnDeg,g_turnRate,RotDone\n"
        "Strafe g_targetDirX, g_targetDirY, g_targetDirZ, TRUE\n"
        "SetPushBack g_dirX,g_dirY,g_dirZ,2\n"
        "TurnLeft 90\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:self():moveToPos(\"xMe\", \"YMe\", \"zMe\", 100, \"MoveDone\") "
        "-- MM9_MOVEMENT.scr:2") != std::string::npos);
    CHECK(luaText.find("ctx:self():walkTo(ctx:object(\"hTarget\"), 10, \"WalkDone\") "
        "-- MM9_MOVEMENT.scr:3") != std::string::npos);
    CHECK(luaText.find("ctx:self():runTo(ctx:object(\"g_hobject\"), 32, \"RunDone\") -- MM9_MOVEMENT.scr:4") !=
        std::string::npos);
    CHECK(luaText.find("ctx:state().g_hobject = ctx:objectOrNil(\"Marker2\") -- MM9_MOVEMENT.scr:5") !=
        std::string::npos);
    CHECK(luaText.find("ctx:self():walkTo(ctx:object(\"g_hobject\"), 16, \"DoNothing\") "
        "-- MM9_MOVEMENT.scr:6") != std::string::npos);
    CHECK(luaText.find("ctx:self():moveDir(\"dx\", 0, \"dz\", \"nDist\", \"nSpeed\", \"Ready\") "
        "-- MM9_MOVEMENT.scr:7") != std::string::npos);
    CHECK(luaText.find("ctx:self():faceObject(ctx:object(\"hTarget\"), 180, \"FaceDone\") "
        "-- MM9_MOVEMENT.scr:8") != std::string::npos);
    CHECK(luaText.find("ctx:self():facePos(\"xMe\", \"yMe\", \"zMe\", 45, \"FacePosDone\") "
        "-- MM9_MOVEMENT.scr:9") != std::string::npos);
    CHECK(luaText.find("ctx:self():stop() -- MM9_MOVEMENT.scr:10") != std::string::npos);
    CHECK(luaText.find("ctx:self():walk() -- MM9_MOVEMENT.scr:11") != std::string::npos);
    CHECK(luaText.find("ctx:self():run() -- MM9_MOVEMENT.scr:12") != std::string::npos);
    CHECK(luaText.find("ctx:self():rotate(0, 1, 0, \"g_turnDeg\", \"g_turnRate\", \"RotDone\") "
        "-- MM9_MOVEMENT.scr:13") != std::string::npos);
    CHECK(luaText.find("ctx:self():strafe(\"g_targetDirX\", \"g_targetDirY\", \"g_targetDirZ\", \"TRUE\") "
        "-- MM9_MOVEMENT.scr:14") != std::string::npos);
    CHECK(luaText.find("ctx:self():setPushBack(\"g_dirX\", \"g_dirY\", \"g_dirZ\", 2) "
        "-- MM9_MOVEMENT.scr:15") != std::string::npos);
    CHECK(luaText.find("ctx:self():turnLeft(90) -- MM9_MOVEMENT.scr:16") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"movetopos\", \"xMe YMe zMe 100 MoveDone\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"stop\", \"\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"walk\", \"\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"rotate\", \"0,1,0,g_turnDeg,g_turnRate,RotDone\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"setpushback\", \"g_dirX,g_dirY,g_dirZ,2\")") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator lowers residual MM9 readable service commands")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_RESIDUAL_NATIVE.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "SetInt g_sOut, g_hObject\n"
        "Sin circle_SumdA, circle_v\n"
        "Cos circle_SumdA, circle_u\n"
        "GetAngleToPos g_nPlayerX, g_nPlayerY, g_nPlayerZ, g_nAngle\n"
        "GetRotation hFollowPathObject, g_rotX, g_rotY, g_rotZ, g_rotSpin\n"
        "SetRotation hFollowPathObject, g_rotX,g_rotY,g_rotZ\n"
        "SetRotation g_rotX,g_rotY,g_rotZ,g_rotSpin,nFollowPathRate\n"
        "CalcRotationRate hFollowPathObject,g_nFollowPathSpeed, nFollowPathRate\n"
        "CheckWorldCollision g_posX, g_posY, g_posZ, normalX, normalY, normalZ, g_nTemp, g_hObject\n"
        "GetPos( g_hMyObject, g_posX, g_posY, g_posZ )\n"
        "GetFaceDir( g_hUsedBy, g_faceX, g_faceY, g_faceZ )\n"
        "MoveDir( X, Y, Z, g_nDist, g_nRate, TrapsSpikeMoveDone )\n"
        "MoveToPos( g_posX, g_posY, g_posZ, g_nReturnRate, TrapsMoveBackDone )\n"
        "Rotate( g_rotX, g_rotY, g_rotZ, g_nRotDegrees, g_nRotPerSec, SwingDone )\n"
        "VecCross g_x1, g_y1, g_z1, g_x2, g_y2, g_z2, g_rotX, g_rotY, g_rotZ\n"
        "GetCrossProduct( g_x1, g_y1, g_z1, g_x2, g_y2, g_z2, g_rotX, g_rotY, g_rotZ )\n"
        "Speak cinematic\\blood2.wav, OnSpeakDone\n"
        "PlayAnimation Threat, FALSE, BaseGoGetHim\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:setInt(\"g_sOut\", \"g_hObject\") -- MM9_RESIDUAL_NATIVE.scr:2") !=
        std::string::npos);
    CHECK(luaText.find("ctx:sin(\"circle_SumdA\", \"circle_v\") -- MM9_RESIDUAL_NATIVE.scr:3") !=
        std::string::npos);
    CHECK(luaText.find("ctx:cos(\"circle_SumdA\", \"circle_u\") -- MM9_RESIDUAL_NATIVE.scr:4") !=
        std::string::npos);
    CHECK(luaText.find("ctx:getAngleToPos(\"g_nPlayerX\", \"g_nPlayerY\", \"g_nPlayerZ\", \"g_nAngle\") "
        "-- MM9_RESIDUAL_NATIVE.scr:5") != std::string::npos);
    CHECK(luaText.find("ctx:getRotation(ctx:object(\"hFollowPathObject\"), \"g_rotX\", \"g_rotY\", "
        "\"g_rotZ\", \"g_rotSpin\") -- MM9_RESIDUAL_NATIVE.scr:6") != std::string::npos);
    CHECK(luaText.find("ctx:setRotation(ctx:object(\"hFollowPathObject\"), \"g_rotX\", \"g_rotY\", "
        "\"g_rotZ\") -- MM9_RESIDUAL_NATIVE.scr:7") != std::string::npos);
    CHECK(luaText.find("ctx:setRotation(\"g_rotX\", \"g_rotY\", \"g_rotZ\", \"g_rotSpin\", "
        "\"nFollowPathRate\") -- MM9_RESIDUAL_NATIVE.scr:8") != std::string::npos);
    CHECK(luaText.find("ctx:calcRotationRate(ctx:object(\"hFollowPathObject\"), "
        "\"g_nFollowPathSpeed\", \"nFollowPathRate\") -- MM9_RESIDUAL_NATIVE.scr:9") != std::string::npos);
    CHECK(luaText.find("ctx:checkWorldCollision(\"g_posX\", \"g_posY\", \"g_posZ\", \"normalX\", "
        "\"normalY\", \"normalZ\", \"g_nTemp\", \"g_hObject\") -- MM9_RESIDUAL_NATIVE.scr:10") !=
        std::string::npos);
    CHECK(luaText.find("ctx:state().g_posX, ctx:state().g_posY, ctx:state().g_posZ = "
        "ctx:self():pos() -- MM9_RESIDUAL_NATIVE.scr:11") != std::string::npos);
    CHECK(luaText.find("ctx:state().g_faceX, ctx:state().g_faceY, ctx:state().g_faceZ = "
        "ctx:object(\"g_hUsedBy\"):rotation() -- MM9_RESIDUAL_NATIVE.scr:12") != std::string::npos);
    CHECK(luaText.find("ctx:self():moveDir(\"X\", \"Y\", \"Z\", \"g_nDist\", \"g_nRate\", "
        "\"TrapsSpikeMoveDone\") -- MM9_RESIDUAL_NATIVE.scr:13") != std::string::npos);
    CHECK(luaText.find("ctx:self():moveToPos(\"g_posX\", \"g_posY\", \"g_posZ\", \"g_nReturnRate\", "
        "\"TrapsMoveBackDone\") -- MM9_RESIDUAL_NATIVE.scr:14") != std::string::npos);
    CHECK(luaText.find("ctx:self():rotate(\"g_rotX\", \"g_rotY\", \"g_rotZ\", \"g_nRotDegrees\", "
        "\"g_nRotPerSec\", \"SwingDone\") -- MM9_RESIDUAL_NATIVE.scr:15") != std::string::npos);
    CHECK(luaText.find("ctx:state().g_rotX, ctx:state().g_rotY, ctx:state().g_rotZ = "
        "ctx:vecCross(\"g_x1\", \"g_y1\", \"g_z1\", \"g_x2\", \"g_y2\", \"g_z2\") "
        "-- MM9_RESIDUAL_NATIVE.scr:16") != std::string::npos);
    CHECK(luaText.find("ctx:state().g_rotX, ctx:state().g_rotY, ctx:state().g_rotZ = "
        "ctx:vecCross(\"g_x1\", \"g_y1\", \"g_z1\", \"g_x2\", \"g_y2\", \"g_z2\") "
        "-- MM9_RESIDUAL_NATIVE.scr:17") != std::string::npos);
    CHECK(luaText.find("ctx:speak(\"cinematic\\\\blood2.wav\", \"OnSpeakDone\") "
        "-- MM9_RESIDUAL_NATIVE.scr:18") != std::string::npos);
    CHECK(luaText.find("ctx:self():playAnimationCommand(\"Threat\", \"FALSE\", \"BaseGoGetHim\") "
        "-- MM9_RESIDUAL_NATIVE.scr:19") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"setint\"") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"getpos(\"") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"playanimation\"") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator preserves mutable g_hobject handle overwrites")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_MUTABLE_HANDLE.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "GetMyHandle g_hobject\n"
        "SetFlag g_hobject, visible\n"
        "GetObjectHandle Marker2 g_hobject\n"
        "WalkTo g_hobject 16 DoNothing\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:state().g_hobject = ctx:self() -- MM9_MUTABLE_HANDLE.scr:2") !=
        std::string::npos);
    CHECK(luaText.find("ctx:self():setFlag(\"visible\", true) -- MM9_MUTABLE_HANDLE.scr:3") !=
        std::string::npos);
    CHECK(luaText.find("ctx:state().g_hobject = ctx:objectOrNil(\"Marker2\") -- MM9_MUTABLE_HANDLE.scr:4") !=
        std::string::npos);
    CHECK(luaText.find("ctx:self():walkTo(ctx:object(\"g_hobject\"), 16, \"DoNothing\") "
        "-- MM9_MUTABLE_HANDLE.scr:5") != std::string::npos);
    CHECK(luaText.find("ctx:self():walkTo(ctx:self(), 16") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator lowers spawn service commands")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_SPAWN.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "Spawn hCreature, xLoc, yLoc, zLoc, SPAWN_PARAM\n"
        "Spawn hMonster Xpos YPos ZPos sMonster\n"
        "Spawn2 hMonster2, 1, 2, 3, 1, 0, 0, MonsterScript\n"
        "Spawn 0, x, y, z, Bad\n"
        "Spawn hBad, x, y, z\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:state().hCreature = ctx:spawn(\"xLoc\", \"yLoc\", \"zLoc\", \"SPAWN_PARAM\") "
        "-- MM9_SPAWN.scr:2") != std::string::npos);
    CHECK(luaText.find("ctx:state().hMonster = ctx:spawn(\"Xpos\", \"YPos\", \"ZPos\", \"sMonster\") "
        "-- MM9_SPAWN.scr:3") != std::string::npos);
    CHECK(luaText.find("ctx:state().hMonster2 = ctx:spawn2(1, 2, 3, 1, 0, 0, \"MonsterScript\") "
        "-- MM9_SPAWN.scr:4") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"spawn\", \"0, x, y, z, Bad\"") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"spawn\", \"hBad, x, y, z\"") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"spawn\", \"hCreature, xLoc") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"spawn2\", \"hMonster2") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator lowers presentation service commands")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_PRESENTATION.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "ScreenFadeOut 1\n"
        "ScreenFadeIn .5\n"
        "LetterBox TRUE\n"
        "RolloverText TEXT_DEFEAT, 1, 3000, 2000\n"
        "CacheTexture skins\\Njam1.dtx\n"
        "HidePiece DaggerMagic\n"
        "DoLetter Item_Id\n"
        "GetContainerCount g_hplayer g_ntemp\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:screenFadeOut(1) -- MM9_PRESENTATION.scr:2") != std::string::npos);
    CHECK(luaText.find("ctx:screenFadeIn(.5) -- MM9_PRESENTATION.scr:3") != std::string::npos);
    CHECK(luaText.find("ctx:letterBox(\"TRUE\") -- MM9_PRESENTATION.scr:4") != std::string::npos);
    CHECK(luaText.find("ctx:rolloverText(\"TEXT_DEFEAT\", 1, 3000, 2000) "
        "-- MM9_PRESENTATION.scr:5") != std::string::npos);
    CHECK(luaText.find("ctx:cacheTexture(\"skins\\\\Njam1.dtx\") -- MM9_PRESENTATION.scr:6") !=
        std::string::npos);
    CHECK(luaText.find("ctx:hidePiece(\"DaggerMagic\") -- MM9_PRESENTATION.scr:7") != std::string::npos);
    CHECK(luaText.find("ctx:doLetter(\"Item_Id\") -- MM9_PRESENTATION.scr:8") != std::string::npos);
    CHECK(luaText.find("ctx:getContainerCount(\"g_hplayer\", \"g_ntemp\") -- MM9_PRESENTATION.scr:9") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"screenfadeout\", \"1\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"rollovertext\", \"TEXT_DEFEAT, 1, 3000, 2000\")") ==
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"cachetexture\", \"skins\\\\Njam1.dtx\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"hidepiece\", \"DaggerMagic\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"doletter\", \"Item_Id\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"getcontainercount\", \"g_hplayer g_ntemp\")") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator lowers AI combat service commands")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_AI_COMBAT.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "AddFriend Actor\n"
        "AddEnemy Marker\n"
        "RemoveFriend Ally\n"
        "RemoveEnemy Foe\n"
        "IsFriend hTarget, bFriend\n"
        "AIGetDistance hTarget, nDist\n"
        "CanAttack bCanAttack\n"
        "CanRangeAttack bCanRangeAttack\n"
        "HasRangeAttack bHasRange\n"
        "IsTargetInRange bInRange\n"
        "IsAttacking bAttacking\n"
        "Attack OnStop\n"
        "RangeAttack OnRangeStop\n"
        "SendAlert hTarget\n"
        "SetIdle\n"
        "SetCrouch TRUE\n"
        "SetTargetLostTime 30\n"
        "Jump JumpDone\n"
        "SendAlert NULL\n"
        "Taunt TauntDone\n"
        "Aware AwareDone\n"
        "Launch LaunchDone, 24\n"
        "Converse -1 ConvDone\n"
        "ResumeWait -1\n"
        "PauseWait -1\n"
        "Damage hTarget, 100, 4, FALSE\n"
        "Damage NULL, 10, 4, FALSE\n"
        "Die\n"
        "Die Now\n"
        "FindTargets hTargetArray,16,nTargetsFound,100,0\n"
        "FindHidingPlace hHidingPlace\n"
        "SetStuck\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:self():addFriend(\"Actor\") -- MM9_AI_COMBAT.scr:2") != std::string::npos);
    CHECK(luaText.find("ctx:self():addEnemy(\"Marker\") -- MM9_AI_COMBAT.scr:3") != std::string::npos);
    CHECK(luaText.find("ctx:self():removeFriend(\"Ally\") -- MM9_AI_COMBAT.scr:4") != std::string::npos);
    CHECK(luaText.find("ctx:self():removeEnemy(\"Foe\") -- MM9_AI_COMBAT.scr:5") != std::string::npos);
    CHECK(luaText.find("ctx:state().bFriend = ctx:self():isFriend(ctx:object(\"hTarget\")) "
        "-- MM9_AI_COMBAT.scr:6") != std::string::npos);
    CHECK(luaText.find("ctx:state().nDist = ctx:self():aiDistanceTo(ctx:object(\"hTarget\")) "
        "-- MM9_AI_COMBAT.scr:7") != std::string::npos);
    CHECK(luaText.find("ctx:state().bCanAttack = ctx:self():canAttack() -- MM9_AI_COMBAT.scr:8") !=
        std::string::npos);
    CHECK(luaText.find("ctx:state().bCanRangeAttack = ctx:self():canRangeAttack() "
        "-- MM9_AI_COMBAT.scr:9") != std::string::npos);
    CHECK(luaText.find("ctx:state().bHasRange = ctx:self():hasRangeAttack() -- MM9_AI_COMBAT.scr:10") !=
        std::string::npos);
    CHECK(luaText.find("ctx:state().bInRange = ctx:self():isTargetInRange() -- MM9_AI_COMBAT.scr:11") !=
        std::string::npos);
    CHECK(luaText.find("ctx:state().bAttacking = ctx:self():isAttacking() -- MM9_AI_COMBAT.scr:12") !=
        std::string::npos);
    CHECK(luaText.find("ctx:self():attack(\"OnStop\") -- MM9_AI_COMBAT.scr:13") != std::string::npos);
    CHECK(luaText.find("ctx:self():rangeAttack(\"OnRangeStop\") -- MM9_AI_COMBAT.scr:14") !=
        std::string::npos);
    CHECK(luaText.find("ctx:self():sendAlert(ctx:object(\"hTarget\")) -- MM9_AI_COMBAT.scr:15") !=
        std::string::npos);
    CHECK(luaText.find("ctx:self():setIdle() -- MM9_AI_COMBAT.scr:16") != std::string::npos);
    CHECK(luaText.find("ctx:self():setCrouch(\"TRUE\") -- MM9_AI_COMBAT.scr:17") != std::string::npos);
    CHECK(luaText.find("ctx:self():setTargetLostTime(30) -- MM9_AI_COMBAT.scr:18") != std::string::npos);
    CHECK(luaText.find("ctx:self():jump(\"JumpDone\") -- MM9_AI_COMBAT.scr:19") != std::string::npos);
    CHECK(luaText.find("ctx:self():sendAlert(nil) -- MM9_AI_COMBAT.scr:20") != std::string::npos);
    CHECK(luaText.find("ctx:self():taunt(\"TauntDone\") -- MM9_AI_COMBAT.scr:21") != std::string::npos);
    CHECK(luaText.find("ctx:self():aware(\"AwareDone\") -- MM9_AI_COMBAT.scr:22") != std::string::npos);
    CHECK(luaText.find("ctx:self():launch(\"LaunchDone\", 24) -- MM9_AI_COMBAT.scr:23") != std::string::npos);
    CHECK(luaText.find("ctx:self():converse(-1, \"ConvDone\") -- MM9_AI_COMBAT.scr:24") != std::string::npos);
    CHECK(luaText.find("ctx:self():resumeWait(-1) -- MM9_AI_COMBAT.scr:25") != std::string::npos);
    CHECK(luaText.find("ctx:self():pauseWait(-1) -- MM9_AI_COMBAT.scr:26") != std::string::npos);
    CHECK(luaText.find("ctx:object(\"hTarget\"):damage(100, 4, \"FALSE\") -- MM9_AI_COMBAT.scr:27") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"damage\", \"NULL, 10, 4, FALSE\") -- MM9_AI_COMBAT.scr:28") !=
        std::string::npos);
    CHECK(luaText.find("ctx:self():die() -- MM9_AI_COMBAT.scr:29") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"die\", \"Now\") -- MM9_AI_COMBAT.scr:30") != std::string::npos);
    CHECK(luaText.find("ctx:self():findTargets(\"hTargetArray\", 16, \"nTargetsFound\", 100, 0) "
        "-- MM9_AI_COMBAT.scr:31") != std::string::npos);
    CHECK(luaText.find("ctx:state().hHidingPlace = ctx:self():findHidingPlace() "
        "-- MM9_AI_COMBAT.scr:32") != std::string::npos);
    CHECK(luaText.find("ctx:self():setStuck() -- MM9_AI_COMBAT.scr:33") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"addfriend\", \"Actor\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"setidle\", \"\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"setcrouch\", \"TRUE\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"settargetlosttime\", \"30\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"jump\", \"JumpDone\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"taunt\", \"TauntDone\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"damage\", \"hTarget, 100, 4, FALSE\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"die\", \"\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"findtargets\", \"hTargetArray,16,nTargetsFound,100,0\")") ==
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"findhidingplace\", \"hHidingPlace\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"setstuck\", \"\")") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator lowers generic object runtime state queries")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_OBJECT_STATE_QUERY.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "IsMoving bMoving\n"
        "IsOnGround bGrounded\n"
        "IsDead hTarget, bDead\n"
        "IsDead NULL, bDead\n"
        "IsMoving hTarget, bMoving\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:state().bMoving = ctx:self():isMoving() -- MM9_OBJECT_STATE_QUERY.scr:2") !=
        std::string::npos);
    CHECK(luaText.find("ctx:state().bGrounded = ctx:self():isOnGround() -- MM9_OBJECT_STATE_QUERY.scr:3") !=
        std::string::npos);
    CHECK(luaText.find("ctx:state().bDead = ctx:object(\"hTarget\"):isDead() "
        "-- MM9_OBJECT_STATE_QUERY.scr:4") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"isdead\", \"NULL, bDead\") -- MM9_OBJECT_STATE_QUERY.scr:5") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"ismoving\", \"hTarget, bMoving\") -- MM9_OBJECT_STATE_QUERY.scr:6") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"ismoving\", \"bMoving\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"isonground\", \"bGrounded\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"isdead\", \"hTarget, bDead\")") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator lowers generic AI perception boolean queries")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_AI_PERCEPTION.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "CanReachTarget bCanReach\n"
        "CanReachObject hTarget, bCanReachObject\n"
        "IsFacing hTarget, bFacing\n"
        "ShouldRunAway hTarget, bRunAway\n"
        "IsWorldObject hTarget, bWorld\n"
        "IsFear bFear\n"
        "IsInNoRunZone bNoRun\n"
        "CanReachObject NULL, bCanReachObject\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:state().bCanReach = ctx:self():canReachTarget() -- MM9_AI_PERCEPTION.scr:2") !=
        std::string::npos);
    CHECK(luaText.find("ctx:state().bCanReachObject = ctx:self():canReachObject(ctx:object(\"hTarget\")) "
        "-- MM9_AI_PERCEPTION.scr:3") != std::string::npos);
    CHECK(luaText.find("ctx:state().bFacing = ctx:self():isFacing(ctx:object(\"hTarget\")) "
        "-- MM9_AI_PERCEPTION.scr:4") != std::string::npos);
    CHECK(luaText.find("ctx:state().bRunAway = ctx:self():shouldRunAwayFrom(ctx:object(\"hTarget\")) "
        "-- MM9_AI_PERCEPTION.scr:5") != std::string::npos);
    CHECK(luaText.find("ctx:state().bWorld = ctx:object(\"hTarget\"):isWorldObject() "
        "-- MM9_AI_PERCEPTION.scr:6") != std::string::npos);
    CHECK(luaText.find("ctx:state().bFear = ctx:self():isFear() -- MM9_AI_PERCEPTION.scr:7") !=
        std::string::npos);
    CHECK(luaText.find("ctx:state().bNoRun = ctx:self():isInNoRunZone() -- MM9_AI_PERCEPTION.scr:8") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"canreachobject\", \"NULL, bCanReachObject\") "
        "-- MM9_AI_PERCEPTION.scr:9") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"canreachtarget\", \"bCanReach\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"isfacing\", \"hTarget, bFacing\")") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator lowers routed AI request helpers")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_AI_HELPERS.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "IsClearShot hTarget, bClearShot\n"
        "IsClearShot hTarget, bClearShot, hObstacle\n"
        "Help g_hTarget\n"
        "EstimateRangeAttackHit g_hObject\n"
        "Land\n"
        "Land Now\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:state().bClearShot = ctx:self():isClearShot(ctx:object(\"hTarget\")) "
        "-- MM9_AI_HELPERS.scr:2") != std::string::npos);
    CHECK(luaText.find("ctx:state().bClearShot, ctx:state().hObstacle = "
        "ctx:self():isClearShot(ctx:object(\"hTarget\")) -- MM9_AI_HELPERS.scr:3") != std::string::npos);
    CHECK(luaText.find("ctx:self():help(ctx:object(\"g_hTarget\")) -- MM9_AI_HELPERS.scr:4") !=
        std::string::npos);
    CHECK(luaText.find("ctx:self():estimateRangeAttackHit(ctx:object(\"g_hObject\")) "
        "-- MM9_AI_HELPERS.scr:5") != std::string::npos);
    CHECK(luaText.find("ctx:self():land() -- MM9_AI_HELPERS.scr:6") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"land\", \"Now\") -- MM9_AI_HELPERS.scr:7") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"isclearshot\", \"hTarget, bClearShot\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"isclearshot\", \"hTarget, bClearShot, hObstacle\")") ==
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"help\", \"g_hTarget\")") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator lowers generic object bounds queries")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_OBJECT_BOUNDS.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "GetDims hTarget, dimX, dimY, dimZ\n"
        "GetObjectMinMax hTarget, minX, minY, minZ, maxX, maxY, maxZ\n"
        "GetDims hTarget, 1bad, dimY, dimZ\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:state().dimX, ctx:state().dimY, ctx:state().dimZ = "
        "ctx:object(\"hTarget\"):dims() -- MM9_OBJECT_BOUNDS.scr:2") != std::string::npos);
    CHECK(luaText.find("ctx:state().minX, ctx:state().minY, ctx:state().minZ, "
        "ctx:state().maxX, ctx:state().maxY, ctx:state().maxZ = "
        "ctx:object(\"hTarget\"):minMax() -- MM9_OBJECT_BOUNDS.scr:3") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"getdims\", \"hTarget, 1bad, dimY, dimZ\") "
        "-- MM9_OBJECT_BOUNDS.scr:4") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"getdims\", \"hTarget, dimX, dimY, dimZ\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"getobjectminmax\", "
        "\"hTarget, minX, minY, minZ, maxX, maxY, maxZ\")") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator lowers generic object lifetime commands")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_OBJECT_LIFETIME.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "RemoveObject hTarget\n"
        "RemoveObject\n"
        "RemoveObject NULL\n"
        "RemoveObject 0\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:object(\"hTarget\"):remove() -- MM9_OBJECT_LIFETIME.scr:2") !=
        std::string::npos);
    CHECK(luaText.find("ctx:self():remove() -- MM9_OBJECT_LIFETIME.scr:3") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"removeobject\", \"NULL\") -- MM9_OBJECT_LIFETIME.scr:4") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"removeobject\", \"0\") -- MM9_OBJECT_LIFETIME.scr:5") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"removeobject\", \"hTarget\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"removeobject\", \"\")") == std::string::npos);
}

TEST_CASE("MM9 script Lua generator lowers generic object target slot commands")
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "MM9_OBJECT_TARGET.scr";
    writeTextFileForTest(
        path,
        ":OnUse\n"
        "Target hTarget, TRUE\n"
        "GetTarget hCurrentTarget\n"
        "GetObjectTarget hOther, hOtherTarget\n"
        "Target NULL\n"
        "Target 0\n"
        "GetTarget 1bad\n"
        "CreateObjectLink hTarget\n"
        "BreakObjectLink hTarget\n");

    const OpenYAMM::Game::Mm9ScriptFile file = OpenYAMM::Game::parseMm9ScriptFile(path);
    REQUIRE(file.errors.empty());
    const std::string luaText = OpenYAMM::Game::generateMm9ScriptLua(file);

    CHECK(luaText.find("ctx:self():setTarget(ctx:object(\"hTarget\")) -- MM9_OBJECT_TARGET.scr:2") !=
        std::string::npos);
    CHECK(luaText.find("ctx:state().hCurrentTarget = ctx:self():target() -- MM9_OBJECT_TARGET.scr:3") !=
        std::string::npos);
    CHECK(luaText.find("ctx:state().hOtherTarget = ctx:object(\"hOther\"):target() -- MM9_OBJECT_TARGET.scr:4") !=
        std::string::npos);
    CHECK(luaText.find("ctx:self():setTarget(nil) -- MM9_OBJECT_TARGET.scr:5") != std::string::npos);
    CHECK(luaText.find("ctx:self():setTarget(nil) -- MM9_OBJECT_TARGET.scr:6") != std::string::npos);
    CHECK(luaText.find("ctx:command(\"gettarget\", \"1bad\") -- MM9_OBJECT_TARGET.scr:7") !=
        std::string::npos);
    CHECK(luaText.find("ctx:self():link(ctx:object(\"hTarget\")) -- MM9_OBJECT_TARGET.scr:8") !=
        std::string::npos);
    CHECK(luaText.find("ctx:self():unlink(ctx:object(\"hTarget\")) -- MM9_OBJECT_TARGET.scr:9") !=
        std::string::npos);
    CHECK(luaText.find("ctx:command(\"target\", \"hTarget, TRUE\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"gettarget\", \"hCurrentTarget\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"createobjectlink\", \"hTarget\")") == std::string::npos);
    CHECK(luaText.find("ctx:command(\"breakobjectlink\", \"hTarget\")") == std::string::npos);
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
    CHECK(combinedLua.find("ctx:hasGold(") != std::string::npos);
    CHECK(combinedLua.find("ctx:takeGold(") != std::string::npos);
    CHECK(combinedLua.find("ctx:giveExp(") != std::string::npos);
    CHECK(combinedLua.find("ctx:givePromo(") != std::string::npos);
    CHECK(combinedLua.find("ctx:getAttribute(") != std::string::npos);
    CHECK(combinedLua.find("ctx:giveAttribute(") != std::string::npos);
    CHECK(combinedLua.find("ctx:cacheScript(") != std::string::npos);
    CHECK(combinedLua.find("ctx:runScript(") != std::string::npos);
    CHECK(combinedLua.find("ctx:setConsoleNumVar(") != std::string::npos);
    CHECK(combinedLua.find("ctx:getConsoleNumVar(") != std::string::npos);
    CHECK(combinedLua.find("ctx:setConsoleStrVar(") != std::string::npos);
    CHECK(combinedLua.find("ctx:getConsoleStrVar(") != std::string::npos);
    CHECK(combinedLua.find("ctx:getParam(") != std::string::npos);
    CHECK(combinedLua.find(":setNumberProperty(") != std::string::npos);
    CHECK(combinedLua.find("ctx:getObjectHandleByRudeId(") != std::string::npos);
    CHECK(combinedLua.find("ctx:addTrigger(") != std::string::npos);
    CHECK(combinedLua.find("ctx:trigger(") != std::string::npos);
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

TEST_CASE("MM9 dialogue pipeline can emit opt-in debug progress")
{
    const std::filesystem::path fixtureRoot =
        createPipelineFixtureRoot("openyamm_mm9_dialogue_pipeline_debug_fixture");
    const std::filesystem::path outputRoot =
        std::filesystem::temp_directory_path() / "openyamm_mm9_dialogue_pipeline_debug_output";
    std::error_code error;
    std::filesystem::remove_all(outputRoot, error);

    std::ostringstream generateDebug;
    const OpenYAMM::Game::Mm9DialoguePipelineResult generated =
        OpenYAMM::Game::generateMm9DialoguePipelineFiles(
            fixtureRoot / "extracted",
            fixtureRoot / "maps",
            &generateDebug);
    REQUIRE(generated.errors.empty());
    CHECK(generateDebug.str().find("scan source inventories") != std::string::npos);
    CHECK(generateDebug.str().find("script 1/") != std::string::npos);
    CHECK(generateDebug.str().find("generation complete") != std::string::npos);

    std::ostringstream writeDebug;
    const OpenYAMM::Game::Mm9DialoguePipelineWriteResult writeResult =
        OpenYAMM::Game::writeMm9DialoguePipelineFiles(outputRoot, generated.files, false, &writeDebug);
    CHECK(writeResult.errors.empty());
    CHECK(writeDebug.str().find("write ") != std::string::npos);
    CHECK(writeDebug.str().find("written 1/") != std::string::npos);
    CHECK(writeDebug.str().find("write/check complete") != std::string::npos);

    std::filesystem::remove_all(outputRoot, error);
    std::filesystem::remove_all(fixtureRoot, error);
}
