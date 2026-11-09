#include "game/content/RulesetDefinition.h"

#include "game/content/ContentTableComposer.h"
#include "game/party/SkillData.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cctype>
#include <exception>
#include <filesystem>
#include <functional>
#include <unordered_set>

namespace OpenYAMM::Game
{
namespace
{
constexpr const char *EngineDataTableRoot = "engine/data_tables/";

bool isValidRulesetId(const std::string &id)
{
    return !id.empty()
        && std::all_of(
            id.begin(),
            id.end(),
            [](char character)
            {
                return std::islower(static_cast<unsigned char>(character))
                    || std::isdigit(static_cast<unsigned char>(character))
                    || character == '_';
            });
}

bool isSafeRelativePath(const std::string &path)
{
    if (path.empty() || path.find('\\') != std::string::npos)
    {
        return false;
    }

    const std::filesystem::path parsedPath(path);

    if (parsedPath.is_absolute())
    {
        return false;
    }

    for (const std::filesystem::path &component : parsedPath)
    {
        if (component == ".." || component == ".")
        {
            return false;
        }
    }

    return true;
}

std::string scalarString(const YAML::Node &node, const char *pKey)
{
    const YAML::Node child = node[pKey];
    return child && child.IsScalar() ? child.as<std::string>() : std::string();
}

// Reads an optional list of option ids into `values`; a missing key leaves the list empty.
template <typename Enum>
bool readChoiceList(
    const YAML::Node &node,
    const char *pKey,
    const std::function<std::optional<Enum>(std::string_view)> &parse,
    std::vector<Enum> &values,
    std::string &errorMessage)
{
    const YAML::Node listNode = node[pKey];

    if (!listNode)
    {
        return true;
    }

    if (!listNode.IsSequence() || listNode.size() == 0)
    {
        errorMessage = std::string("options.") + pKey + " must be a non-empty list";
        return false;
    }

    for (const YAML::Node &valueNode : listNode)
    {
        const std::optional<Enum> value = valueNode.IsScalar() ? parse(valueNode.as<std::string>()) : std::nullopt;

        if (!value || std::find(values.begin(), values.end(), *value) != values.end())
        {
            errorMessage = std::string("options.") + pKey + " has an unknown or repeated value";
            return false;
        }

        values.push_back(*value);
    }

    return true;
}

template <typename Enum>
bool readChoiceDefault(
    const YAML::Node &node,
    const char *pKey,
    const std::function<std::optional<Enum>(std::string_view)> &parse,
    const std::vector<Enum> &values,
    Enum &defaultValue,
    std::string &errorMessage)
{
    if (values.empty())
    {
        return true;
    }

    const std::string text = scalarString(node, pKey);
    const std::optional<Enum> parsed = text.empty() ? values.front() : parse(text);

    if (!parsed || std::find(values.begin(), values.end(), *parsed) == values.end())
    {
        errorMessage = std::string("options.") + pKey + " must be one of the listed values";
        return false;
    }

    defaultValue = *parsed;
    return true;
}

bool parseChoices(const YAML::Node &optionsNode, RulesetChoices &choices, std::string &errorMessage)
{
    if (!optionsNode)
    {
        return true;
    }

    if (!optionsNode.IsMap())
    {
        errorMessage = "options must be a map";
        return false;
    }

    const std::function<std::optional<RulesetDifficulty>(std::string_view)> parseDifficulty = parseRulesetDifficulty;
    const std::function<std::optional<RulesetProgression>(std::string_view)> parseProgression =
        parseRulesetProgression;
    const std::function<std::optional<RulesetChallengeMode>(std::string_view)> parseChallengeMode =
        parseRulesetChallengeMode;

    if (!readChoiceList(optionsNode, "difficulties", parseDifficulty, choices.difficulties, errorMessage)
        || !readChoiceDefault(
            optionsNode,
            "defaultDifficulty",
            parseDifficulty,
            choices.difficulties,
            choices.defaultDifficulty,
            errorMessage)
        || !readChoiceList(optionsNode, "progressions", parseProgression, choices.progressions, errorMessage)
        || !readChoiceDefault(
            optionsNode,
            "defaultProgression",
            parseProgression,
            choices.progressions,
            choices.defaultProgression,
            errorMessage)
        || !readChoiceList(optionsNode, "challengeModes", parseChallengeMode, choices.challengeModes, errorMessage))
    {
        return false;
    }

    if (!choices.challengeModes.empty() && choices.challengeModes.front() != RulesetChallengeMode::None)
    {
        errorMessage = "options.challengeModes must start with none";
        return false;
    }

    for (const char *pFlag : {"randomizer", "preferences"})
    {
        const YAML::Node flagNode = optionsNode[pFlag];

        if (flagNode && !flagNode.IsScalar())
        {
            errorMessage = std::string("options.") + pFlag + " must be true or false";
            return false;
        }
    }

    choices.randomizer = optionsNode["randomizer"] && optionsNode["randomizer"].as<bool>();
    choices.preferences = optionsNode["preferences"] && optionsNode["preferences"].as<bool>();
    return true;
}

// Reads `key: text` pairs of a map whose keys are option ids.
template <typename Enum>
bool readOptionTexts(
    const YAML::Node &node,
    const char *pKey,
    const std::function<std::optional<Enum>(std::string_view)> &parse,
    std::map<Enum, std::string> &texts,
    std::string &errorMessage)
{
    const YAML::Node mapNode = node[pKey];

    if (!mapNode)
    {
        return true;
    }

    if (!mapNode.IsMap())
    {
        errorMessage = std::string("rulesPanel.") + pKey + " must be a map";
        return false;
    }

    for (const auto &entry : mapNode)
    {
        const std::optional<Enum> value = parse(entry.first.as<std::string>());

        if (!value || !entry.second.IsScalar())
        {
            errorMessage = std::string("rulesPanel.") + pKey + " has an unknown id or a non-text value";
            return false;
        }

        texts[*value] = entry.second.as<std::string>();
    }

    return true;
}

bool parsePanel(const YAML::Node &panelNode, RulesetPanelText &panel, std::string &errorMessage)
{
    if (!panelNode)
    {
        return true;
    }

    if (!panelNode.IsMap())
    {
        errorMessage = "rulesPanel must be a map";
        return false;
    }

    panel.title = scalarString(panelNode, "title");
    panel.subtitle = scalarString(panelNode, "subtitle");
    panel.summary = scalarString(panelNode, "summary");
    panel.randomizer = scalarString(panelNode, "randomizer");
    const YAML::Node columnsNode = panelNode["difficultyColumns"];

    if (columnsNode)
    {
        if (!columnsNode.IsSequence())
        {
            errorMessage = "rulesPanel.difficultyColumns must be a list";
            return false;
        }

        for (const YAML::Node &columnNode : columnsNode)
        {
            panel.difficultyColumns.push_back(columnNode.as<std::string>());
        }
    }

    const YAML::Node difficultiesNode = panelNode["difficulties"];

    if (difficultiesNode)
    {
        if (!difficultiesNode.IsMap())
        {
            errorMessage = "rulesPanel.difficulties must be a map";
            return false;
        }

        for (const auto &entry : difficultiesNode)
        {
            const std::optional<RulesetDifficulty> difficulty = parseRulesetDifficulty(entry.first.as<std::string>());
            const YAML::Node valuesNode = entry.second["values"];

            if (!difficulty || !entry.second.IsMap() || (valuesNode && !valuesNode.IsSequence()))
            {
                errorMessage = "rulesPanel.difficulties has an unknown id or a malformed entry";
                return false;
            }

            RulesetPanelText::Difficulty text = {};
            text.description = scalarString(entry.second, "description");
            text.warning = scalarString(entry.second, "warning");

            for (const YAML::Node &valueNode : valuesNode)
            {
                text.values.push_back(valueNode.as<std::string>());
            }

            if (text.values.size() > panel.difficultyColumns.size())
            {
                errorMessage = "rulesPanel.difficulties has more values than difficultyColumns";
                return false;
            }

            panel.difficulties[*difficulty] = std::move(text);
        }
    }

    const std::function<std::optional<RulesetProgression>(std::string_view)> parseProgression =
        parseRulesetProgression;
    const std::function<std::optional<RulesetChallengeMode>(std::string_view)> parseChallengeMode =
        parseRulesetChallengeMode;
    return readOptionTexts(panelNode, "progressions", parseProgression, panel.progressions, errorMessage)
        && readOptionTexts(panelNode, "challengeModes", parseChallengeMode, panel.challengeModes, errorMessage);
}

bool parseTables(const YAML::Node &tablesNode, std::vector<RulesetTableContribution> &tables, std::string &errorMessage)
{
    if (!tablesNode)
    {
        return true;
    }

    if (!tablesNode.IsSequence())
    {
        errorMessage = "tables must be a list";
        return false;
    }

    std::unordered_set<std::string> tablePaths;

    for (const YAML::Node &tableNode : tablesNode)
    {
        if (!tableNode.IsMap())
        {
            errorMessage = "tables entries must be maps";
            return false;
        }

        RulesetTableContribution table = {};
        table.world = scalarString(tableNode, "world");
        table.table = scalarString(tableNode, "table");
        table.path = scalarString(tableNode, "path");
        const std::string mode = scalarString(tableNode, "mode");

        if (mode == "override")
        {
            table.mode = TableContributionMode::Override;
        }
        else if (mode == "replace")
        {
            table.mode = TableContributionMode::Replace;
        }
        else
        {
            errorMessage = "table '" + table.table + "' mode must be override or replace";
            return false;
        }

        if (!isSafeRelativePath(table.table) || !isSafeRelativePath(table.path))
        {
            errorMessage = "table '" + table.table + "' needs a relative table name and patch path";
            return false;
        }

        if (!table.world.empty() && !isValidRulesetId(table.world))
        {
            errorMessage = "table '" + table.table + "' names an invalid world id '" + table.world + "'";
            return false;
        }

        if (!tablePaths.insert(table.world + '\n' + table.table + '\n' + table.path).second)
        {
            errorMessage = "table '" + table.table + "' lists " + table.path + " twice";
            return false;
        }

        const std::string keyColumn = scalarString(tableNode, "keyColumn");
        table.keyColumn = keyColumn == "row" ? RowNumberKeyColumn
            : keyColumn.empty()               ? 0
                                              : tableNode["keyColumn"].as<size_t>();
        table.appendPath = scalarString(tableNode, "append");
        table.appendColumnsPath = scalarString(tableNode, "appendColumns");

        for (const std::string &path : {table.appendPath, table.appendColumnsPath})
        {
            if (!path.empty() && (table.mode != TableContributionMode::Override || !isSafeRelativePath(path)))
            {
                errorMessage = "table '" + table.table + "' append needs override mode and a relative path";
                return false;
            }
        }

        table.headerRow = tableNode["headerRow"] ? tableNode["headerRow"].as<size_t>() : 0;
        tables.push_back(std::move(table));
    }

    return true;
}
}

bool RulesetDefinition::isStandard() const
{
    return id == StandardRulesetId;
}

bool RulesetDefinition::supportsWorld(const std::string &worldId) const
{
    return worlds.empty() || std::find(worlds.begin(), worlds.end(), worldId) != worlds.end();
}

RulesetOptions RulesetDefinition::defaultOptions() const
{
    RulesetOptions options = {};

    if (!choices.difficulties.empty())
    {
        options.difficulty = choices.defaultDifficulty;
    }

    if (!choices.progressions.empty())
    {
        options.progression = choices.defaultProgression;
    }

    return options;
}

bool RulesetDefinition::offers(const RulesetOptions &options) const
{
    const auto offered = [](const auto &values, auto value)
    {
        return values.empty() || std::find(values.begin(), values.end(), value) != values.end();
    };

    const RulesetOptions defaults = defaultOptions();
    return rulesetOptionsValid(options)
        && (choices.difficulties.empty() ? options.difficulty == defaults.difficulty
                                         : offered(choices.difficulties, options.difficulty))
        && (choices.progressions.empty() ? options.progression == defaults.progression
                                         : offered(choices.progressions, options.progression))
        && (choices.challengeModes.empty() ? options.challengeMode == RulesetChallengeMode::None
                                           : offered(choices.challengeModes, options.challengeMode))
        && (choices.randomizer || !options.randomizer)
        && rulesetChallengeModeProgression(options.challengeMode).value_or(options.progression) == options.progression
        && rulesetChallengeModeDifficulty(options.challengeMode).value_or(options.difficulty) == options.difficulty;
}

std::vector<const RulesetTableContribution *> RulesetDefinition::findTables(
    const std::string &tableVirtualPath) const
{
    std::vector<const RulesetTableContribution *> found;

    for (const RulesetTableContribution &table : tables)
    {
        const std::string tablePath = table.world.empty() ? EngineDataTableRoot + table.table
                                                          : "worlds/" + table.world + "/" + table.table;

        if (tablePath == tableVirtualPath)
        {
            found.push_back(&table);
        }
    }

    return found;
}

RulesetDefinition standardRulesetDefinition()
{
    RulesetDefinition definition = {};
    definition.description = Engine::trNoop("The merged Might and Magic VI-VIII rules.");
    definition.panel.summary = definition.description;
    return definition;
}

std::string rulesetPackageRoot(const std::string &rulesetId)
{
    return std::string(RulesetsRoot) + "/" + rulesetId + "/";
}

std::optional<RulesetDefinition> parseRulesetDefinition(
    const std::string &yamlText,
    const std::string &expectedId,
    std::string &errorMessage)
{
    errorMessage.clear();
    RulesetDefinition definition = {};

    try
    {
        const YAML::Node root = YAML::Load(yamlText);

        if (!root || !root.IsMap())
        {
            errorMessage = "ruleset.yml root must be a map";
            return std::nullopt;
        }

        definition.id = scalarString(root, "id");
        definition.name = scalarString(root, "name");
        definition.description = scalarString(root, "description");
        definition.guideUrl = scalarString(root, "guide_url");

        if (!isValidRulesetId(definition.id) || definition.id == StandardRulesetId || definition.id != expectedId)
        {
            errorMessage = "ruleset id '" + definition.id + "' must be lowercase, not '" + StandardRulesetId
                + "', and match its package folder '" + expectedId + "'";
            return std::nullopt;
        }

        if (definition.name.empty())
        {
            errorMessage = "ruleset '" + definition.id + "' needs a name";
            return std::nullopt;
        }

        const YAML::Node schemaNode = root["contentSchemaVersion"];
        definition.contentSchemaVersion = schemaNode ? schemaNode.as<uint32_t>() : 1;

        if (definition.contentSchemaVersion == 0)
        {
            errorMessage = "ruleset contentSchemaVersion must be non-zero";
            return std::nullopt;
        }

        if (!parseContentIdRanges(root["idRanges"], "ruleset.yml", definition.idRanges, errorMessage))
        {
            return std::nullopt;
        }

        const YAML::Node creditsNode = root["credits"];

        if (creditsNode)
        {
            if (!creditsNode.IsSequence())
            {
                errorMessage = "ruleset credits must be a list";
                return std::nullopt;
            }

            for (const YAML::Node &creditNode : creditsNode)
            {
                definition.credits.push_back(creditNode.as<std::string>());
            }
        }

        const YAML::Node skillNamesNode = root["skillNames"];

        if (skillNamesNode)
        {
            if (!skillNamesNode.IsMap())
            {
                errorMessage = "ruleset skillNames must be a map";
                return std::nullopt;
            }

            for (const auto &entry : skillNamesNode)
            {
                const std::string skillName = canonicalSkillName(entry.first.as<std::string>());

                if (!skillIdForSkillName(skillName))
                {
                    errorMessage = "ruleset skillNames names an unknown skill: " + entry.first.as<std::string>();
                    return std::nullopt;
                }

                definition.skillNames[skillName] = entry.second.as<std::string>();
            }
        }

        const YAML::Node worldsNode = root["worlds"];

        if (worldsNode)
        {
            if (!worldsNode.IsSequence())
            {
                errorMessage = "ruleset worlds must be a list of world ids";
                return std::nullopt;
            }

            for (const YAML::Node &worldNode : worldsNode)
            {
                definition.worlds.push_back(worldNode.as<std::string>());
            }
        }

        if (!parseChoices(root["options"], definition.choices, errorMessage)
            || !parsePanel(root["rulesPanel"], definition.panel, errorMessage)
            || !parseTables(root["tables"], definition.tables, errorMessage))
        {
            errorMessage = "ruleset '" + definition.id + "': " + errorMessage;
            return std::nullopt;
        }
    }
    catch (const std::exception &exception)
    {
        errorMessage = std::string("ruleset.yml could not be parsed: ") + exception.what();
        return std::nullopt;
    }

    return definition;
}

std::optional<RulesetDefinition> loadRulesetDefinition(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &rulesetId,
    std::string &errorMessage)
{
    errorMessage.clear();

    if (rulesetId == StandardRulesetId)
    {
        return standardRulesetDefinition();
    }

    if (!isValidRulesetId(rulesetId))
    {
        errorMessage = "invalid ruleset id '" + rulesetId + "'";
        return std::nullopt;
    }

    const std::string manifestPath = rulesetPackageRoot(rulesetId) + "ruleset.yml";
    const std::optional<std::string> text = assetFileSystem.readTextFile(manifestPath);

    if (!text)
    {
        errorMessage = "the ruleset '" + rulesetId + "' is not installed";
        return std::nullopt;
    }

    return parseRulesetDefinition(*text, rulesetId, errorMessage);
}

bool loadAvailableRulesets(
    const Engine::AssetFileSystem &assetFileSystem,
    std::vector<RulesetDefinition> &rulesets,
    std::string &errorMessage)
{
    rulesets.clear();
    errorMessage.clear();
    rulesets.push_back(standardRulesetDefinition());

    // enumerate() returns sorted names, so the packages come in id order.
    for (const std::string &packageName : assetFileSystem.enumerate(RulesetsRoot))
    {
        if (!assetFileSystem.exists(rulesetPackageRoot(packageName) + "ruleset.yml"))
        {
            continue;
        }

        std::optional<RulesetDefinition> definition =
            loadRulesetDefinition(assetFileSystem, packageName, errorMessage);

        if (!definition)
        {
            errorMessage = rulesetPackageRoot(packageName) + ": " + errorMessage;
            return false;
        }

        rulesets.push_back(std::move(*definition));
    }

    return true;
}
}
