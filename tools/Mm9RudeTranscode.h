#pragma once

#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <map>
#include <optional>
#include <set>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct Mm9RudeParseError
{
    std::filesystem::path sourcePath;
    size_t rowNumber = 0;
    std::string message;
};

struct Mm9RudeRow
{
    std::filesystem::path sourcePath;
    size_t rowNumber = 0;
    std::vector<std::string> columns;
};

struct Mm9RudeFile
{
    std::filesystem::path sourcePath;
    std::vector<Mm9RudeRow> rows;
    std::vector<Mm9RudeParseError> errors;
};

struct Mm9RudeSourceInventory
{
    size_t numberedRudeFileCount = 0;
    size_t numberedRudeRowCount = 0;
    size_t numberedNpcIdCount = 0;
    size_t numberedNodePairCount = 0;
    size_t normalDialogueFileCount = 0;
    size_t normalDialogueRowCount = 0;
    size_t normalNpcIdCount = 0;
    size_t normalNodePairCount = 0;
    size_t npcNameRowCount = 0;
    size_t topBlurbRowCount = 0;
    size_t npc997RowCount = 0;
    size_t npc998RowCount = 0;
    size_t npc999RowCount = 0;
    size_t scriptFileCount = 0;
    size_t includeFileCount = 0;
    std::vector<Mm9RudeParseError> errors;
};

enum class Mm9ScriptLineKind
{
    Blank,
    Comment,
    Include,
    Declaration,
    Label,
    Command,
};

struct Mm9ScriptLine
{
    std::filesystem::path sourcePath;
    size_t lineNumber = 0;
    Mm9ScriptLineKind kind = Mm9ScriptLineKind::Blank;
    std::string rawLine;
    std::string codeText;
    std::string commentText;
    std::string name;
    std::string argumentsText;
};

struct Mm9ScriptFile
{
    std::filesystem::path sourcePath;
    std::vector<Mm9ScriptLine> lines;
    std::vector<Mm9RudeParseError> errors;
};

struct Mm9ScriptCommandRef
{
    std::filesystem::path sourcePath;
    size_t lineNumber = 0;
    std::string commandName;
    std::string argumentsText;
};

struct Mm9ScriptSourceInventory
{
    size_t scriptFileCount = 0;
    size_t includeFileCount = 0;
    size_t parsedFileCount = 0;
    size_t lineCount = 0;
    size_t commandCount = 0;
    size_t labelCount = 0;
    size_t includeDirectiveCount = 0;
    std::map<std::string, size_t> commandCounts;
    std::vector<Mm9ScriptCommandRef> commandRefs;
    std::vector<Mm9RudeParseError> errors;
};

struct Mm9KeyEvidence
{
    std::string sourceKind;
    std::filesystem::path sourcePath;
    size_t lineNumber = 0;
    size_t rowNumber = 0;
    size_t columnNumber = 0;
    std::string operation;
    std::string symbol;
};

struct Mm9KeyRegistryEntry
{
    int32_t keyId = 0;
    std::set<std::string> aliases;
    std::vector<Mm9KeyEvidence> evidence;
};

struct Mm9KeyRegistry
{
    std::string stateDomain = "mm9.keys";
    std::map<int32_t, Mm9KeyRegistryEntry> entries;
    std::map<std::string, int32_t> constants;
    std::map<std::string, std::vector<int32_t>> conflictingConstants;
    std::vector<Mm9KeyEvidence> unresolvedScriptReferences;
    size_t scriptKeyOperationCount = 0;
    size_t resolvedScriptKeyOperationCount = 0;
    size_t rudeCandidateEvidenceCount = 0;
};

constexpr int32_t Mm9KeyQbitBase = 9000;
constexpr int32_t Mm9CustomQbitBegin = 10000;

int32_t mm9KeyToQbitId(int32_t rawKeyId);
std::set<int32_t> mm9ReservedQbitIdsForRegistry(const Mm9KeyRegistry &registry);
std::vector<int32_t> findMm9ReservedQbitCollisions(
    const Mm9KeyRegistry &registry,
    const std::set<int32_t> &qbitIds);
bool mm9QbitIdIsInCustomRange(int32_t qbitId);

enum class Mm9PseudoRudeTableKind
{
    JournalQuest,
    JournalNote,
    Award,
};

struct Mm9RawObjectProperty
{
    std::string name;
    int32_t code = 0;
    int32_t flags = 0;
    bool decoded = false;
    std::string rawHex;
    std::string valueJson;
};

struct Mm9ObjectDialogueBinding
{
    std::filesystem::path sourcePath;
    std::string mapId;
    int32_t objectIndex = -1;
    std::string objectClass;
    std::string objectName;
    std::map<std::string, Mm9RawObjectProperty> properties;
    bool doRude = false;
    std::optional<int32_t> rudeId;
    std::string rudeDecodeStatus;
    std::string scriptName;
    bool scriptSourceExists = false;
    bool dialogueCapable = false;
};

struct Mm9ObjectDialogueBindingIndex
{
    size_t mapFileCount = 0;
    size_t objectCount = 0;
    size_t bindingCount = 0;
    size_t dialogueCapableCount = 0;
    size_t doRudeCount = 0;
    size_t npcNbrPropertyCount = 0;
    size_t linkedRudeIdCount = 0;
    size_t unlinkedDialogueCapableCount = 0;
    size_t scriptNameCount = 0;
    size_t linkedScriptCount = 0;
    std::vector<Mm9ObjectDialogueBinding> bindings;
    std::vector<Mm9RudeParseError> errors;
};

struct Mm9RudeTopic
{
    size_t rowIndex = 0;
    size_t rowNumber = 0;
    int32_t choiceSlot = 0;
    int32_t next = 0;
    std::string prompt;
    std::string response;
    std::vector<std::string> rawColumns;
};

enum class Mm9RudeSelectionKind
{
    None,
    GotoNode,
    Close,
    Service,
    UnresolvedZero,
};

struct Mm9RudeSelectionResult
{
    Mm9RudeSelectionKind kind = Mm9RudeSelectionKind::None;
    int32_t next = 0;
    std::string response;
    std::string serviceName;
    std::string onRudeExitLabel;
};

class Mm9RudeDialogueProvider
{
public:
    bool loadFromFile(const Mm9RudeFile &file);
    bool loadFromGeneratedYaml(const std::string &yamlText, std::string &error);

    bool enterRudeId(int32_t rudeId);
    bool enterNode(int32_t rudeId, int32_t nodeId);
    bool enterObjectContext(const Mm9ObjectDialogueBinding &binding);
    void setOnRudeExitLabel(std::string label);
    void setKeyState(std::set<int32_t> keys);

    int32_t currentRudeId() const;
    int32_t currentNodeId() const;
    std::vector<Mm9RudeTopic> visibleTopics() const;
    Mm9RudeSelectionResult selectTopic(size_t visibleTopicIndex);
    bool closed() const;

private:
    static bool rowHasRequiredKeys(const Mm9RudeRow &row, const std::set<int32_t> &keys);

    Mm9RudeFile m_file;
    int32_t m_currentRudeId = 0;
    int32_t m_currentNodeId = 0;
    bool m_closed = true;
    std::set<int32_t> m_keys;
    std::string m_onRudeExitLabel;
};

std::optional<std::vector<std::string>> parseMm9RudeCsvLine(const std::string &line, std::string &error);

std::string serializeMm9RudeCsvLine(const std::vector<std::string> &columns);

Mm9RudeFile parseMm9RudeFile(const std::filesystem::path &path);

std::string generateMm9RudeYaml(const Mm9RudeFile &file);

Mm9RudeSourceInventory scanMm9RudeSourceInventory(const std::filesystem::path &extractedRoot);

std::optional<int32_t> parseMm9RudeInt(const std::string &text);

Mm9ScriptFile parseMm9ScriptFile(const std::filesystem::path &path);

Mm9ScriptSourceInventory scanMm9ScriptSourceInventory(const std::filesystem::path &extractedRoot);

std::string normalizeMm9ScriptCommandName(const std::string &name);

Mm9KeyRegistry buildMm9KeyRegistry(const std::filesystem::path &extractedRoot);

std::string generateMm9KeyRegistryYaml(const Mm9KeyRegistry &registry);

std::string generateMm9StateDefaultsYaml();

std::string generateMm9PseudoRudeYaml(const Mm9RudeFile &file, Mm9PseudoRudeTableKind kind);

std::vector<Mm9KeyEvidence> findMissingMm9PseudoRudeKeyReferences(
    const Mm9RudeFile &file,
    const Mm9KeyRegistry &registry);

std::string generateMm9ScriptLua(const Mm9ScriptFile &file);

Mm9ObjectDialogueBindingIndex scanMm9ObjectDialogueBindings(
    const std::filesystem::path &mapsDirectory,
    const std::filesystem::path &scriptsDirectory,
    const std::set<int32_t> &knownRudeIds);

struct Mm9DialoguePipelineGeneratedFile
{
    std::filesystem::path relativePath;
    std::string contents;
};

struct Mm9DialoguePipelineResult
{
    std::vector<Mm9DialoguePipelineGeneratedFile> files;
    std::vector<Mm9RudeParseError> errors;
};

struct Mm9DialoguePipelineWriteResult
{
    size_t writtenFileCount = 0;
    size_t unchangedFileCount = 0;
    size_t staleFileCount = 0;
    std::vector<Mm9RudeParseError> errors;
};

Mm9DialoguePipelineResult generateMm9DialoguePipelineFiles(
    const std::filesystem::path &extractedRoot,
    const std::filesystem::path &mapsDirectory);

Mm9DialoguePipelineWriteResult writeMm9DialoguePipelineFiles(
    const std::filesystem::path &outputRoot,
    const std::vector<Mm9DialoguePipelineGeneratedFile> &files,
    bool checkOnly);
}
