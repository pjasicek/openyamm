#include "game/mm9/Mm9DialoguePackage.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <exception>
#include <filesystem>
#include <optional>
#include <string>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
void addError(Mm9DialoguePackage &package, const std::string &virtualPath, const std::string &message)
{
    Mm9DialoguePackageError error = {};
    error.virtualPath = virtualPath;
    error.message = message;
    package.errors.push_back(std::move(error));
}

std::optional<YAML::Node> loadYaml(
    const Engine::AssetFileSystem &assetFileSystem,
    Mm9DialoguePackage &package,
    const std::string &virtualPath)
{
    const std::optional<std::string> text = assetFileSystem.readTextFile(virtualPath);
    if (!text)
    {
        addError(package, virtualPath, "missing generated file");
        return std::nullopt;
    }

    try
    {
        return YAML::Load(*text);
    }
    catch (const std::exception &exception)
    {
        addError(package, virtualPath, std::string("could not parse YAML: ") + exception.what());
        return std::nullopt;
    }
}

std::string scalarString(const YAML::Node &node, const char *pKey, const std::string &defaultValue = {})
{
    const YAML::Node child = node[pKey];
    if (!child || !child.IsScalar())
    {
        return defaultValue;
    }
    return child.as<std::string>();
}

int32_t scalarInt(const YAML::Node &node, const char *pKey, int32_t defaultValue = 0)
{
    const YAML::Node child = node[pKey];
    if (!child || !child.IsScalar())
    {
        return defaultValue;
    }
    return child.as<int32_t>();
}

size_t scalarSize(const YAML::Node &node, const char *pKey, size_t defaultValue = 0)
{
    const YAML::Node child = node[pKey];
    if (!child || !child.IsScalar())
    {
        return defaultValue;
    }
    return child.as<size_t>();
}

uint32_t scalarUint32(const YAML::Node &node, const char *pKey, uint32_t defaultValue = 0)
{
    const YAML::Node child = node[pKey];
    if (!child || !child.IsScalar())
    {
        return defaultValue;
    }
    return child.as<uint32_t>();
}

bool scalarBool(const YAML::Node &node, const char *pKey)
{
    const YAML::Node child = node[pKey];
    return child && child.IsScalar() && child.as<bool>();
}

std::vector<std::string> stringSequence(const YAML::Node &node)
{
    std::vector<std::string> values;
    if (!node || !node.IsSequence())
    {
        return values;
    }

    for (const YAML::Node &entry : node)
    {
        if (entry.IsScalar())
        {
            values.push_back(entry.as<std::string>());
        }
    }

    return values;
}

std::map<std::string, int32_t> intMap(const YAML::Node &node)
{
    std::map<std::string, int32_t> values;
    if (!node || !node.IsMap())
    {
        return values;
    }

    for (YAML::const_iterator iterator = node.begin(); iterator != node.end(); ++iterator)
    {
        if (iterator->first.IsScalar() && iterator->second.IsScalar())
        {
            values[iterator->first.as<std::string>()] = iterator->second.as<int32_t>();
        }
    }

    return values;
}

std::map<std::string, std::string> stringMap(const YAML::Node &node)
{
    std::map<std::string, std::string> values;
    if (!node || !node.IsMap())
    {
        return values;
    }

    for (YAML::const_iterator iterator = node.begin(); iterator != node.end(); ++iterator)
    {
        if (iterator->first.IsScalar() && iterator->second.IsScalar())
        {
            values[iterator->first.as<std::string>()] = iterator->second.as<std::string>();
        }
    }

    return values;
}

std::map<std::string, std::map<std::string, int32_t>> nestedIntMap(const YAML::Node &node)
{
    std::map<std::string, std::map<std::string, int32_t>> values;
    if (!node || !node.IsMap())
    {
        return values;
    }

    for (YAML::const_iterator iterator = node.begin(); iterator != node.end(); ++iterator)
    {
        if (iterator->first.IsScalar() && iterator->second.IsMap())
        {
            values[iterator->first.as<std::string>()] = intMap(iterator->second);
        }
    }

    return values;
}

std::map<std::string, std::map<std::string, std::string>> nestedStringMap(const YAML::Node &node)
{
    std::map<std::string, std::map<std::string, std::string>> values;
    if (!node || !node.IsMap())
    {
        return values;
    }

    for (YAML::const_iterator iterator = node.begin(); iterator != node.end(); ++iterator)
    {
        if (iterator->first.IsScalar() && iterator->second.IsMap())
        {
            values[iterator->first.as<std::string>()] = stringMap(iterator->second);
        }
    }

    return values;
}

std::string jsonStringScalar(const std::string &valueJson)
{
    if (valueJson.empty())
    {
        return {};
    }

    try
    {
        const YAML::Node value = YAML::Load(valueJson);
        return value && value.IsScalar() ? value.as<std::string>() : "";
    }
    catch (const std::exception &)
    {
        return {};
    }
}

std::vector<std::string> splitScriptParams(const std::string &text)
{
    std::vector<std::string> params;
    std::string current;
    bool inQuote = false;

    for (const char ch : text)
    {
        if (ch == '"')
        {
            inQuote = !inQuote;
            continue;
        }

        if (!inQuote && std::isspace(static_cast<unsigned char>(ch)) != 0)
        {
            if (!current.empty())
            {
                params.push_back(current);
                current.clear();
            }
            continue;
        }

        current.push_back(ch);
    }

    if (!current.empty())
    {
        params.push_back(current);
    }

    return params;
}

size_t rudeColumnNumber(const std::string &column)
{
    if (column.size() < 2 || column[0] != 'c')
    {
        return 0;
    }

    size_t value = 0;
    for (size_t index = 1; index < column.size(); ++index)
    {
        const char ch = column[index];
        if (std::isdigit(static_cast<unsigned char>(ch)) == 0)
        {
            return 0;
        }
        value = value * 10 + static_cast<size_t>(ch - '0');
    }

    return value;
}

std::optional<YAML::Node> optionalChildNode(const YAML::Node &node, const char *pKey)
{
    try
    {
        const YAML::Node child = node[pKey];
        if (!child.IsDefined() || child.IsNull())
        {
            return std::nullopt;
        }
        return child;
    }
    catch (const YAML::InvalidNode &)
    {
        return std::nullopt;
    }
}

bool semanticConditionsNode(const YAML::Node &rowNode, YAML::Node &conditions)
{
    const YAML::Node semantic = rowNode["semantic"];
    if (!semantic.IsDefined() || semantic.IsNull() || !semantic.IsMap())
    {
        return false;
    }

    const std::optional<YAML::Node> conditionsNode = optionalChildNode(semantic, "conditions");
    if (!conditionsNode)
    {
        return false;
    }

    conditions = *conditionsNode;
    if (!conditions.IsDefined() || conditions.IsNull() || !conditions.IsMap())
    {
        return false;
    }

    return true;
}

void parseRequiredKeyConditions(
    Mm9DialoguePackage &package,
    const std::string &virtualPath,
    const YAML::Node &conditions,
    Mm9GeneratedRudeRow &row)
{
    const std::optional<YAML::Node> requiredKeysNode = optionalChildNode(conditions, "required_keys");
    if (!requiredKeysNode)
    {
        return;
    }
    const YAML::Node requiredKeys = *requiredKeysNode;

    if (!requiredKeys.IsSequence())
    {
        addError(package, virtualPath, "semantic.conditions.required_keys must be a sequence");
        return;
    }

    for (const YAML::Node &requiredKeyNode : requiredKeys)
    {
        if (!requiredKeyNode || !requiredKeyNode.IsMap())
        {
            addError(package, virtualPath, "semantic required key condition must be a map");
            continue;
        }

        Mm9GeneratedRequiredKeyCondition condition = {};
        condition.column = rudeColumnNumber(scalarString(requiredKeyNode, "column"));
        condition.rawId = scalarInt(requiredKeyNode, "raw_id");
        condition.qbitId = scalarUint32(requiredKeyNode, "qbit_id");
        condition.stateId = scalarString(requiredKeyNode, "state_id");
        if (condition.rawId <= 0)
        {
            addError(package, virtualPath, "semantic required key condition has invalid raw_id");
            continue;
        }

        row.requiredKeys.push_back(std::move(condition));
    }
}

void parseRequiredItemConditions(
    Mm9DialoguePackage &package,
    const std::string &virtualPath,
    const YAML::Node &conditions,
    Mm9GeneratedRudeRow &row)
{
    const std::optional<YAML::Node> requiredItemsNode = optionalChildNode(conditions, "required_items");
    if (!requiredItemsNode)
    {
        return;
    }
    const YAML::Node requiredItems = *requiredItemsNode;

    if (!requiredItems.IsSequence())
    {
        addError(package, virtualPath, "semantic.conditions.required_items must be a sequence");
        return;
    }

    for (const YAML::Node &requiredItemNode : requiredItems)
    {
        if (!requiredItemNode || !requiredItemNode.IsMap())
        {
            addError(package, virtualPath, "semantic required item condition must be a map");
            continue;
        }

        Mm9GeneratedRequiredItemCondition condition = {};
        condition.column = rudeColumnNumber(scalarString(requiredItemNode, "column"));
        condition.itemId = scalarUint32(requiredItemNode, "item_id");
        condition.stateId = scalarString(requiredItemNode, "state_id");
        if (condition.itemId == 0)
        {
            addError(package, virtualPath, "semantic required item condition has invalid item_id");
            continue;
        }

        row.requiredItems.push_back(std::move(condition));
    }
}

void parseConsoleNumEqualsConditions(
    Mm9DialoguePackage &package,
    const std::string &virtualPath,
    const YAML::Node &conditions,
    Mm9GeneratedRudeRow &row)
{
    const std::optional<YAML::Node> consoleConditionsNode =
        optionalChildNode(conditions, "required_console_num_equals");
    if (!consoleConditionsNode)
    {
        return;
    }
    const YAML::Node consoleConditions = *consoleConditionsNode;

    if (!consoleConditions.IsSequence())
    {
        addError(package, virtualPath, "semantic.conditions.required_console_num_equals must be a sequence");
        return;
    }

    for (const YAML::Node &conditionNode : consoleConditions)
    {
        if (!conditionNode || !conditionNode.IsMap())
        {
            addError(package, virtualPath, "semantic console num condition must be a map");
            continue;
        }

        Mm9GeneratedConsoleNumEqualsCondition condition = {};
        condition.variable = scalarString(conditionNode, "variable");
        condition.value = scalarInt(conditionNode, "value");
        condition.stateId = scalarString(conditionNode, "state_id");
        if (condition.variable.empty())
        {
            addError(package, virtualPath, "semantic console num condition has empty variable");
            continue;
        }

        row.requiredConsoleNumEquals.push_back(std::move(condition));
    }
}

void parseConsoleStrEqualsConditions(
    Mm9DialoguePackage &package,
    const std::string &virtualPath,
    const YAML::Node &conditions,
    Mm9GeneratedRudeRow &row)
{
    const std::optional<YAML::Node> consoleConditionsNode =
        optionalChildNode(conditions, "required_console_str_equals");
    if (!consoleConditionsNode)
    {
        return;
    }
    const YAML::Node consoleConditions = *consoleConditionsNode;

    if (!consoleConditions.IsSequence())
    {
        addError(package, virtualPath, "semantic.conditions.required_console_str_equals must be a sequence");
        return;
    }

    for (const YAML::Node &conditionNode : consoleConditions)
    {
        if (!conditionNode || !conditionNode.IsMap())
        {
            addError(package, virtualPath, "semantic console str condition must be a map");
            continue;
        }

        Mm9GeneratedConsoleStrEqualsCondition condition = {};
        condition.variable = scalarString(conditionNode, "variable");
        condition.value = scalarString(conditionNode, "value");
        condition.stateId = scalarString(conditionNode, "state_id");
        if (condition.variable.empty())
        {
            addError(package, virtualPath, "semantic console str condition has empty variable");
            continue;
        }

        row.requiredConsoleStrEquals.push_back(std::move(condition));
    }
}

void parseVisibilityConditions(
    Mm9DialoguePackage &package,
    const std::string &virtualPath,
    const YAML::Node &rowNode,
    Mm9GeneratedRudeRow &row)
{
    YAML::Node conditions;
    if (!semanticConditionsNode(rowNode, conditions))
    {
        return;
    }

    parseRequiredKeyConditions(package, virtualPath, conditions, row);
    parseRequiredItemConditions(package, virtualPath, conditions, row);
    parseConsoleNumEqualsConditions(package, virtualPath, conditions, row);
    parseConsoleStrEqualsConditions(package, virtualPath, conditions, row);
}

std::optional<Mm9GeneratedRudeRow> parseGeneratedRudeRow(
    Mm9DialoguePackage &package,
    const std::string &virtualPath,
    const YAML::Node &rowNode)
{
    if (!rowNode || !rowNode.IsMap())
    {
        addError(package, virtualPath, "row must be a map");
        return std::nullopt;
    }

    const YAML::Node rawColumns = rowNode["raw_columns"];
    if (!rawColumns || !rawColumns.IsSequence())
    {
        addError(package, virtualPath, "row is missing raw_columns sequence");
        return std::nullopt;
    }

    Mm9GeneratedRudeRow row = {};
    row.rawColumns.reserve(rawColumns.size());
    for (const YAML::Node &rawColumn : rawColumns)
    {
        row.rawColumns.push_back(rawColumn.IsScalar() ? rawColumn.as<std::string>() : "");
    }

    const YAML::Node source = rowNode["source"];
    if (source && source.IsMap())
    {
        row.source.file = scalarString(source, "file");
        row.source.row = scalarSize(source, "row");
    }

    const YAML::Node decoded = rowNode["decoded"];
    if (decoded && decoded.IsMap())
    {
        row.npcId = scalarInt(decoded, "npc_id", scalarInt(decoded, "rude_id"));
        row.nodeId = scalarInt(decoded, "node_id");
        row.choiceSlot = scalarInt(decoded, "choice_slot", scalarInt(decoded, "entry_id"));
        row.prompt = scalarString(decoded, "prompt", scalarString(decoded, "title"));
        row.response = scalarString(decoded, "response", scalarString(decoded, "text"));
        row.next = scalarInt(decoded, "next");
    }

    parseVisibilityConditions(package, virtualPath, rowNode, row);
    return row;
}

std::optional<Mm9GeneratedRudeDialogue> parseDialogueFile(
    Mm9DialoguePackage &package,
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &virtualPath)
{
    const std::optional<YAML::Node> root = loadYaml(assetFileSystem, package, virtualPath);
    if (!root)
    {
        return std::nullopt;
    }

    const YAML::Node rows = (*root)["rows"];
    if (!rows || !rows.IsSequence())
    {
        addError(package, virtualPath, "generated dialogue file is missing rows sequence");
        return std::nullopt;
    }

    Mm9GeneratedRudeDialogue dialogue = {};
    dialogue.sourceFile = scalarString(*root, "source_file");
    for (const YAML::Node &rowNode : rows)
    {
        const std::optional<Mm9GeneratedRudeRow> row = parseGeneratedRudeRow(package, virtualPath, rowNode);
        if (row)
        {
            dialogue.rows.push_back(*row);
        }
    }

    return dialogue;
}

std::vector<Mm9GeneratedRudeRow> parsePseudoRows(
    Mm9DialoguePackage &package,
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &virtualPath)
{
    std::vector<Mm9GeneratedRudeRow> parsedRows;
    const std::optional<YAML::Node> root = loadYaml(assetFileSystem, package, virtualPath);
    if (!root)
    {
        return parsedRows;
    }

    const YAML::Node entries = (*root)["entries"];
    if (!entries || !entries.IsSequence())
    {
        addError(package, virtualPath, "generated pseudo-RUDE file is missing entries sequence");
        return parsedRows;
    }

    for (const YAML::Node &entryNode : entries)
    {
        const std::optional<Mm9GeneratedRudeRow> row = parseGeneratedRudeRow(package, virtualPath, entryNode);
        if (row)
        {
            parsedRows.push_back(*row);
        }
    }

    return parsedRows;
}

void loadNpcTextMap(
    const Engine::AssetFileSystem &assetFileSystem,
    Mm9DialoguePackage &package,
    const std::string &virtualPath,
    size_t textColumnIndex,
    std::map<int32_t, std::string> &target)
{
    const std::optional<Mm9GeneratedRudeDialogue> dialogue =
        parseDialogueFile(package, assetFileSystem, virtualPath);
    if (!dialogue)
    {
        return;
    }

    for (const Mm9GeneratedRudeRow &row : dialogue->rows)
    {
        if (row.rawColumns.size() <= textColumnIndex)
        {
            addError(package, virtualPath, "NPC text row has too few columns");
            continue;
        }

        char *pEnd = nullptr;
        const long parsedId = std::strtol(row.rawColumns[0].c_str(), &pEnd, 10);
        if (pEnd == row.rawColumns[0].c_str() || *pEnd != '\0')
        {
            addError(package, virtualPath, "NPC text row has invalid id column");
            continue;
        }

        target[static_cast<int32_t>(parsedId)] = row.rawColumns[textColumnIndex];
    }
}

void loadNpcDialogues(
    const Engine::AssetFileSystem &assetFileSystem,
    Mm9DialoguePackage &package)
{
    std::vector<std::string> entries = assetFileSystem.enumerate("dialogue/npcs");
    std::sort(entries.begin(), entries.end());

    if (entries.empty())
    {
        addError(package, "dialogue/npcs", "missing generated NPC dialogue directory");
        return;
    }

    for (const std::string &entry : entries)
    {
        if (!entry.ends_with(".yml"))
        {
            continue;
        }

        const std::string virtualPath = "dialogue/npcs/" + entry;
        const std::optional<Mm9GeneratedRudeDialogue> dialogue =
            parseDialogueFile(package, assetFileSystem, virtualPath);
        if (!dialogue || dialogue->rows.empty())
        {
            continue;
        }

        package.npcDialogues[dialogue->rows.front().npcId] = *dialogue;
    }
}

void loadServices(const Engine::AssetFileSystem &assetFileSystem, Mm9DialoguePackage &package)
{
    const std::string virtualPath = "dialogue/services.yml";
    const std::optional<YAML::Node> root = loadYaml(assetFileSystem, package, virtualPath);
    if (!root)
    {
        return;
    }

    const YAML::Node services = (*root)["services"];
    if (!services || !services.IsSequence())
    {
        addError(package, virtualPath, "services must be a sequence");
        return;
    }

    for (const YAML::Node &serviceNode : services)
    {
        Mm9GeneratedService service = {};
        service.opcode = scalarInt(serviceNode, "opcode");
        service.name = scalarString(serviceNode, "name");
        service.status = scalarString(serviceNode, "status");
        service.observedCount = scalarSize(serviceNode, "observed_count");
        package.services[service.opcode] = service;
    }
}

void loadKeys(const Engine::AssetFileSystem &assetFileSystem, Mm9DialoguePackage &package)
{
    const std::string virtualPath = "state/keys.yml";
    const std::optional<YAML::Node> root = loadYaml(assetFileSystem, package, virtualPath);
    if (!root)
    {
        return;
    }

    if (scalarString(*root, "state_domain") != "mm9.keys" || scalarString(*root, "backend") != "qbits")
    {
        addError(package, virtualPath, "keys registry must declare mm9.keys qbit backend");
        return;
    }

    const YAML::Node keys = (*root)["keys"];
    if (!keys || !keys.IsSequence())
    {
        addError(package, virtualPath, "keys must be a sequence");
        return;
    }

    for (const YAML::Node &keyNode : keys)
    {
        Mm9GeneratedKey key = {};
        key.rawId = scalarInt(keyNode, "raw_id", scalarInt(keyNode, "id"));
        key.qbitId = scalarInt(keyNode, "qbit_id");
        key.aliases = stringSequence(keyNode["aliases"]);
        if (key.qbitId != 9000 + key.rawId)
        {
            addError(package, virtualPath, "key qbit_id does not match 9000 + raw_id");
            continue;
        }
        package.keys[key.rawId] = key;
    }
}

void loadStateDefaults(const Engine::AssetFileSystem &assetFileSystem, Mm9DialoguePackage &package)
{
    const std::string virtualPath = "state/defaults.yml";
    const std::optional<YAML::Node> root = loadYaml(assetFileSystem, package, virtualPath);
    if (!root)
    {
        return;
    }

    const YAML::Node stateDomains = (*root)["state_domains"];
    const YAML::Node keysDomain = stateDomains ? stateDomains["keys"] : YAML::Node();
    if (!stateDomains || !stateDomains.IsMap() || !keysDomain || !keysDomain.IsMap())
    {
        addError(package, virtualPath, "state defaults must declare state_domains.keys");
        return;
    }

    if (scalarString(keysDomain, "backend") != "qbits" || scalarString(keysDomain, "state_id_prefix") != "mm9.keys")
    {
        addError(package, virtualPath, "MM9 key defaults must declare mm9.keys qbit backend");
        return;
    }

    Mm9GeneratedStateDefaults defaults = {};
    defaults.loaded = true;
    defaults.keyQbitBase = scalarUint32(keysDomain, "qbit_base", 9000);
    if (defaults.keyQbitBase != 9000)
    {
        addError(package, virtualPath, "MM9 key defaults qbit_base must be 9000");
        return;
    }

    const YAML::Node initialState = (*root)["initial_state"];
    if (!initialState || !initialState.IsMap())
    {
        addError(package, virtualPath, "state defaults must declare initial_state map");
        return;
    }

    defaults.consoleNumVars = intMap(initialState["console_num_vars"]);
    defaults.consoleStrVars = stringMap(initialState["console_str_vars"]);
    defaults.mapNumVars = nestedIntMap(initialState["map_num_vars"]);
    defaults.mapStrVars = nestedStringMap(initialState["map_str_vars"]);
    defaults.scriptNumVars = intMap(initialState["script_num_vars"]);
    defaults.scriptStrVars = stringMap(initialState["script_str_vars"]);
    defaults.objectHandleVars = stringMap(initialState["object_handle_vars"]);
    defaults.objectNumberProperties = intMap(initialState["object_number_properties"]);
    package.stateDefaults = std::move(defaults);
}

std::string luaPathForScript(const Mm9GeneratedScriptFile &script)
{
    const std::filesystem::path sourcePath(script.source);
    if (script.kind == "include")
    {
        return "scripts/includes/" + sourcePath.stem().string() + ".lua";
    }

    return "scripts/" + sourcePath.stem().string() + ".lua";
}

void loadScriptIndex(const Engine::AssetFileSystem &assetFileSystem, Mm9DialoguePackage &package)
{
    const std::string virtualPath = "scripts/script_index.yml";
    const std::optional<YAML::Node> root = loadYaml(assetFileSystem, package, virtualPath);
    if (!root)
    {
        return;
    }

    const YAML::Node files = (*root)["files"];
    if (!files || !files.IsSequence())
    {
        addError(package, virtualPath, "script index files must be a sequence");
        return;
    }

    for (const YAML::Node &fileNode : files)
    {
        Mm9GeneratedScriptFile script = {};
        script.source = scalarString(fileNode, "source");
        script.kind = scalarString(fileNode, "kind");
        script.luaPath = luaPathForScript(script);

        const std::optional<std::string> luaText = assetFileSystem.readTextFile(script.luaPath);
        if (!luaText)
        {
            addError(package, script.luaPath, "missing generated Lua for script index entry");
            continue;
        }
        script.luaText = *luaText;

        const YAML::Node labels = fileNode["labels"];
        if (labels && labels.IsSequence())
        {
            for (const YAML::Node &labelNode : labels)
            {
                script.labels.push_back(scalarString(labelNode, "name"));
            }
        }

        const YAML::Node commands = fileNode["commands"];
        if (commands && commands.IsSequence())
        {
            for (const YAML::Node &commandNode : commands)
            {
                Mm9GeneratedScriptCommand command = {};
                command.line = scalarSize(commandNode, "line");
                command.name = scalarString(commandNode, "name");
                command.rawName = scalarString(commandNode, "raw_name");
                command.argumentsText = scalarString(commandNode, "args");
                script.commands.push_back(std::move(command));
            }
        }

        package.scripts[script.source] = std::move(script);
    }
}

void loadScriptRuntime(const Engine::AssetFileSystem &assetFileSystem, Mm9DialoguePackage &package)
{
    const std::string virtualPath = "scripts/common/mm9_script_runtime.lua";
    const std::optional<std::string> luaText = assetFileSystem.readTextFile(virtualPath);
    if (!luaText)
    {
        addError(package, virtualPath, "missing generated MM9 script runtime support");
        return;
    }

    package.scriptRuntimeLuaText = *luaText;
}

void loadObjectBindings(const Engine::AssetFileSystem &assetFileSystem, Mm9DialoguePackage &package)
{
    const std::string virtualPath = "maps/dialogue_bindings.yml";
    const std::optional<YAML::Node> root = loadYaml(assetFileSystem, package, virtualPath);
    if (!root)
    {
        return;
    }

    const YAML::Node bindings = (*root)["bindings"];
    if (!bindings || !bindings.IsSequence())
    {
        addError(package, virtualPath, "object dialogue bindings must be a sequence");
        return;
    }

    for (const YAML::Node &bindingNode : bindings)
    {
        Mm9GeneratedObjectDialogueBinding binding = {};
        binding.sourceFile = scalarString(bindingNode, "source_file");
        binding.mapId = scalarString(bindingNode, "map");
        binding.objectIndex = scalarInt(bindingNode, "object_index", -1);
        binding.objectClass = scalarString(bindingNode, "object_class");
        binding.objectName = scalarString(bindingNode, "object_name");
        binding.dialogueCapable = scalarBool(bindingNode, "dialogue_capable");
        binding.doRude = scalarBool(bindingNode, "do_rude");
        binding.rudeDecodeStatus = scalarString(bindingNode, "rude_decode_status");
        if (bindingNode["rude_id"] && bindingNode["rude_id"].IsScalar())
        {
            binding.rudeId = bindingNode["rude_id"].as<int32_t>();
        }
        binding.scriptName = scalarString(bindingNode, "script_name");
        binding.scriptSourceExists = scalarBool(bindingNode, "script_source_exists");

        const YAML::Node properties = bindingNode["properties"];
        if (properties && properties.IsMap())
        {
            for (YAML::const_iterator propertyIterator = properties.begin();
                 propertyIterator != properties.end();
                 ++propertyIterator)
            {
                if (!propertyIterator->first.IsScalar() || !propertyIterator->second.IsMap())
                {
                    continue;
                }

                Mm9GeneratedObjectProperty property = {};
                property.name = propertyIterator->first.as<std::string>();
                property.code = scalarInt(propertyIterator->second, "code");
                property.flags = scalarInt(propertyIterator->second, "flags");
                property.decoded = scalarBool(propertyIterator->second, "decoded");
                property.rawHex = scalarString(propertyIterator->second, "raw_hex");
                property.valueJson = scalarString(propertyIterator->second, "value_json");
                binding.properties[property.name] = std::move(property);
            }
        }

        const auto scriptParamsIterator = binding.properties.find("ScriptParams");
        if (scriptParamsIterator != binding.properties.end())
        {
            binding.scriptParams = splitScriptParams(jsonStringScalar(scriptParamsIterator->second.valueJson));
        }

        const auto greetingSoundIterator = binding.properties.find("GreetingSound");
        if (greetingSoundIterator != binding.properties.end())
        {
            binding.greetingSound = jsonStringScalar(greetingSoundIterator->second.valueJson);
        }

        package.objectBindings.push_back(std::move(binding));
    }
}
}

bool loadMm9DialoguePackage(
    const Engine::AssetFileSystem &assetFileSystem,
    Mm9DialoguePackage &package)
{
    package = {};

    loadNpcDialogues(assetFileSystem, package);
    loadNpcTextMap(assetFileSystem, package, "dialogue/npc_names.yml", 1, package.npcNames);
    loadNpcTextMap(assetFileSystem, package, "dialogue/top_blurbs.yml", 2, package.topBlurbs);
    package.journalQuestRows = parsePseudoRows(package, assetFileSystem, "dialogue/journal_quests.yml");
    package.journalNoteRows = parsePseudoRows(package, assetFileSystem, "dialogue/journal_notes.yml");
    package.awardRows = parsePseudoRows(package, assetFileSystem, "dialogue/awards.yml");
    loadServices(assetFileSystem, package);
    loadKeys(assetFileSystem, package);
    loadStateDefaults(assetFileSystem, package);
    loadScriptRuntime(assetFileSystem, package);
    loadScriptIndex(assetFileSystem, package);
    loadObjectBindings(assetFileSystem, package);

    return package.errors.empty();
}
}
