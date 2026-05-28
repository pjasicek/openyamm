#pragma once

#include "engine/AssetFileSystem.h"

#include <cstddef>
#include <cstdint>
#include <map>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct Mm9DialoguePackageError
{
    std::string virtualPath;
    std::string message;
};

struct Mm9GeneratedRudeSource
{
    std::string file;
    size_t row = 0;
};

struct Mm9GeneratedRequiredKeyCondition
{
    size_t column = 0;
    int32_t rawId = 0;
    uint32_t qbitId = 0;
    std::string stateId;
};

struct Mm9GeneratedRequiredItemCondition
{
    size_t column = 0;
    uint32_t itemId = 0;
    std::string stateId;
};

struct Mm9GeneratedConsoleNumEqualsCondition
{
    std::string variable;
    int32_t value = 0;
    std::string stateId;
};

struct Mm9GeneratedConsoleStrEqualsCondition
{
    std::string variable;
    std::string value;
    std::string stateId;
};

struct Mm9GeneratedRudeRow
{
    Mm9GeneratedRudeSource source;
    std::vector<std::string> rawColumns;
    std::vector<Mm9GeneratedRequiredKeyCondition> requiredKeys;
    std::vector<Mm9GeneratedRequiredItemCondition> requiredItems;
    std::vector<Mm9GeneratedConsoleNumEqualsCondition> requiredConsoleNumEquals;
    std::vector<Mm9GeneratedConsoleStrEqualsCondition> requiredConsoleStrEquals;
    int32_t npcId = 0;
    int32_t nodeId = 0;
    int32_t choiceSlot = 0;
    std::string prompt;
    std::string response;
    int32_t next = 0;
};

struct Mm9GeneratedRudeDialogue
{
    std::string sourceFile;
    std::vector<Mm9GeneratedRudeRow> rows;
};

struct Mm9GeneratedService
{
    int32_t opcode = 0;
    std::string name;
    std::string status;
    size_t observedCount = 0;
};

struct Mm9GeneratedKey
{
    int32_t rawId = 0;
    int32_t qbitId = 0;
    std::vector<std::string> aliases;
};

struct Mm9GeneratedStateDefaults
{
    bool loaded = false;
    uint32_t keyQbitBase = 9000;
    std::map<std::string, int32_t> consoleNumVars;
    std::map<std::string, std::string> consoleStrVars;
    std::map<std::string, std::map<std::string, int32_t>> mapNumVars;
    std::map<std::string, std::map<std::string, std::string>> mapStrVars;
    std::map<std::string, int32_t> scriptNumVars;
    std::map<std::string, std::string> scriptStrVars;
    std::map<std::string, std::string> objectHandleVars;
    std::map<std::string, int32_t> objectNumberProperties;
};

struct Mm9GeneratedObjectProperty
{
    std::string name;
    int32_t code = 0;
    int32_t flags = 0;
    bool decoded = false;
    std::string rawHex;
    std::string valueJson;
};

struct Mm9GeneratedScriptCommand
{
    size_t line = 0;
    std::string name;
    std::string rawName;
    std::string argumentsText;
};

struct Mm9GeneratedScriptFile
{
    std::string source;
    std::string kind;
    std::string luaPath;
    std::string luaText;
    std::vector<std::string> labels;
    std::vector<Mm9GeneratedScriptCommand> commands;
};

struct Mm9GeneratedObjectDialogueBinding
{
    std::string sourceFile;
    std::string mapId;
    int32_t objectIndex = -1;
    std::string objectClass;
    std::string objectName;
    bool dialogueCapable = false;
    bool doRude = false;
    std::optional<int32_t> rudeId;
    std::string rudeDecodeStatus;
    std::string scriptName;
    std::vector<std::string> scriptParams;
    std::string greetingSound;
    std::map<std::string, Mm9GeneratedObjectProperty> properties;
    bool scriptSourceExists = false;
};

struct Mm9DialoguePackage
{
    std::map<int32_t, Mm9GeneratedRudeDialogue> npcDialogues;
    std::map<int32_t, std::string> npcNames;
    std::map<int32_t, std::string> topBlurbs;
    std::vector<Mm9GeneratedRudeRow> journalQuestRows;
    std::vector<Mm9GeneratedRudeRow> journalNoteRows;
    std::vector<Mm9GeneratedRudeRow> awardRows;
    std::map<int32_t, Mm9GeneratedService> services;
    std::map<int32_t, Mm9GeneratedKey> keys;
    Mm9GeneratedStateDefaults stateDefaults;
    std::string scriptRuntimeLuaText;
    std::map<std::string, Mm9GeneratedScriptFile> scripts;
    std::vector<Mm9GeneratedObjectDialogueBinding> objectBindings;
    std::vector<Mm9DialoguePackageError> errors;
};

bool loadMm9DialoguePackage(
    const Engine::AssetFileSystem &assetFileSystem,
    Mm9DialoguePackage &package);
}
