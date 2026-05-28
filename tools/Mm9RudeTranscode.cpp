#include "tools/Mm9RudeTranscode.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cctype>
#include <cmath>
#include <cstring>
#include <fstream>
#include <iterator>
#include <map>
#include <set>
#include <sstream>
#include <system_error>

namespace OpenYAMM::Game
{
namespace
{
bool isDigits(const std::string &text)
{
    if (text.empty())
    {
        return false;
    }

    for (const char ch : text)
    {
        if (ch < '0' || ch > '9')
        {
            return false;
        }
    }

    return true;
}

std::string trimCopy(const std::string &text)
{
    size_t begin = 0;
    while (begin < text.size() && std::isspace(static_cast<unsigned char>(text[begin])) != 0)
    {
        ++begin;
    }

    size_t end = text.size();
    while (end > begin && std::isspace(static_cast<unsigned char>(text[end - 1])) != 0)
    {
        --end;
    }

    return text.substr(begin, end - begin);
}

std::string lowerCopy(const std::string &text)
{
    std::string result;
    result.reserve(text.size());
    for (const char ch : text)
    {
        result.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(ch))));
    }
    return result;
}

std::string firstToken(const std::string &text)
{
    size_t end = 0;
    while (end < text.size() && std::isspace(static_cast<unsigned char>(text[end])) == 0 && text[end] != ',')
    {
        ++end;
    }

    return text.substr(0, end);
}

std::string restAfterFirstToken(const std::string &text)
{
    const std::string token = firstToken(text);
    if (token.size() >= text.size())
    {
        return {};
    }

    return trimCopy(text.substr(token.size()));
}

std::string firstArgumentToken(const std::string &text)
{
    const std::string trimmed = trimCopy(text);
    size_t end = 0;
    while (end < trimmed.size() && std::isspace(static_cast<unsigned char>(trimmed[end])) == 0 &&
        trimmed[end] != ',')
    {
        ++end;
    }

    return trimmed.substr(0, end);
}

bool hasTopLevelComma(const std::string &text)
{
    bool inQuote = false;
    for (const char ch : text)
    {
        if (ch == '"')
        {
            inQuote = !inQuote;
            continue;
        }
        if (!inQuote && ch == ',')
        {
            return true;
        }
    }
    return false;
}

std::vector<std::string> splitWhitespaceScriptArguments(const std::string &text)
{
    std::vector<std::string> arguments;
    std::string current;
    bool inQuote = false;

    for (const char ch : text)
    {
        if (ch == '"')
        {
            inQuote = !inQuote;
            current.push_back(ch);
            continue;
        }
        if (!inQuote && std::isspace(static_cast<unsigned char>(ch)) != 0)
        {
            if (!trimCopy(current).empty())
            {
                arguments.push_back(trimCopy(current));
                current.clear();
            }
            continue;
        }
        current.push_back(ch);
    }

    if (!trimCopy(current).empty())
    {
        arguments.push_back(trimCopy(current));
    }
    return arguments;
}

std::vector<std::string> splitScriptArguments(const std::string &argumentsText)
{
    if (!hasTopLevelComma(argumentsText))
    {
        return splitWhitespaceScriptArguments(argumentsText);
    }

    std::vector<std::string> arguments;
    std::string current;
    bool inQuote = false;
    for (const char ch : argumentsText)
    {
        if (ch == '"')
        {
            inQuote = !inQuote;
            current.push_back(ch);
            continue;
        }
        if (!inQuote && ch == ',')
        {
            arguments.push_back(trimCopy(current));
            current.clear();
            continue;
        }
        current.push_back(ch);
    }

    arguments.push_back(trimCopy(current));
    return arguments;
}

std::optional<uint32_t> npcNumberFromFileName(const std::filesystem::path &path)
{
    const std::string fileName = path.filename().string();
    if (fileName.size() <= 8 || fileName.substr(0, 3) != "NPC" || fileName.substr(fileName.size() - 5) != ".rude")
    {
        return std::nullopt;
    }

    const std::string numberText = fileName.substr(3, fileName.size() - 8);
    if (!isDigits(numberText))
    {
        return std::nullopt;
    }

    return static_cast<uint32_t>(std::stoul(numberText));
}

bool isNormalNpcDialogueFile(const std::filesystem::path &path)
{
    const std::optional<uint32_t> npcNumber = npcNumberFromFileName(path);
    return npcNumber.has_value() && *npcNumber != 997 && *npcNumber != 998 && *npcNumber != 999;
}

std::vector<std::filesystem::path> listFilesWithExtension(
    const std::filesystem::path &directory,
    const std::string &extension)
{
    std::vector<std::filesystem::path> paths;
    std::error_code error;
    if (!std::filesystem::exists(directory, error))
    {
        return paths;
    }

    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(directory, error))
    {
        if (error)
        {
            break;
        }

        if (entry.is_regular_file(error) && entry.path().extension() == extension)
        {
            paths.push_back(entry.path());
        }
    }

    std::sort(paths.begin(), paths.end());
    return paths;
}

std::vector<std::filesystem::path> listScriptFiles(const std::filesystem::path &scriptsDirectory)
{
    std::vector<std::filesystem::path> paths = listFilesWithExtension(scriptsDirectory, ".scr");
    std::vector<std::filesystem::path> includePaths = listFilesWithExtension(scriptsDirectory, ".inc");
    paths.insert(paths.end(), includePaths.begin(), includePaths.end());
    std::sort(paths.begin(), paths.end());
    return paths;
}

std::optional<std::pair<std::string, int32_t>> parseNumberDeclaration(const Mm9ScriptLine &line)
{
    if (line.kind != Mm9ScriptLineKind::Declaration || normalizeMm9ScriptCommandName(line.name) != "#number")
    {
        return std::nullopt;
    }

    const size_t equals = line.argumentsText.find('=');
    if (equals == std::string::npos)
    {
        return std::nullopt;
    }

    const std::string name = trimCopy(line.argumentsText.substr(0, equals));
    const std::string valueText = trimCopy(line.argumentsText.substr(equals + 1));
    if (name.empty())
    {
        return std::nullopt;
    }

    const std::optional<int32_t> value = parseMm9RudeInt(valueText);
    if (!value)
    {
        return std::nullopt;
    }

    return std::make_pair(name, *value);
}

void addKeyEvidence(Mm9KeyRegistry &registry, int32_t keyId, const Mm9KeyEvidence &evidence)
{
    Mm9KeyRegistryEntry &entry = registry.entries[keyId];
    entry.keyId = keyId;
    if (!evidence.symbol.empty())
    {
        entry.aliases.insert(evidence.symbol);
    }
    entry.evidence.push_back(evidence);
}

void addConstant(Mm9KeyRegistry &registry, const std::string &name, int32_t value)
{
    const auto existing = registry.constants.find(name);
    if (existing != registry.constants.end() && existing->second != value)
    {
        std::vector<int32_t> &values = registry.conflictingConstants[name];
        if (std::find(values.begin(), values.end(), existing->second) == values.end())
        {
            values.push_back(existing->second);
        }
        if (std::find(values.begin(), values.end(), value) == values.end())
        {
            values.push_back(value);
        }
        return;
    }

    registry.constants[name] = value;
}

std::optional<int32_t> resolveKeyReference(const Mm9KeyRegistry &registry, const std::string &token)
{
    const std::optional<int32_t> literal = parseMm9RudeInt(token);
    if (literal)
    {
        return literal;
    }

    const auto iterator = registry.constants.find(token);
    if (iterator == registry.constants.end())
    {
        return std::nullopt;
    }

    return iterator->second;
}

std::string luaString(const std::string &text)
{
    std::string result = "\"";
    for (const char ch : text)
    {
        switch (ch)
        {
        case '\\':
            result += "\\\\";
            break;
        case '"':
            result += "\\\"";
            break;
        case '\n':
            result += "\\n";
            break;
        case '\r':
            result += "\\r";
            break;
        case '\t':
            result += "\\t";
            break;
        default:
            result.push_back(ch);
            break;
        }
    }
    result += '"';
    return result;
}

std::string luaValueForScriptToken(const std::string &token)
{
    const std::optional<int32_t> number = parseMm9RudeInt(token);
    return number ? std::to_string(*number) : luaString(token);
}

std::optional<std::string> meaningfulLuaCommentFromMm9Comment(const std::string &commentText)
{
    std::string comment = trimCopy(commentText);
    while (!comment.empty() && comment.front() == ';')
    {
        comment.erase(comment.begin());
        comment = trimCopy(comment);
    }

    bool hasText = false;
    std::string normalizedText;
    for (const char ch : comment)
    {
        if (std::isalnum(static_cast<unsigned char>(ch)) != 0)
        {
            hasText = true;
            normalizedText.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(ch))));
        }
    }

    if (normalizedText == "endoffile")
    {
        return std::nullopt;
    }

    if (!hasText)
    {
        return std::nullopt;
    }

    return comment;
}

void emitLuaComment(std::ostringstream &lua, const std::string &indent, const std::string &comment)
{
    lua << indent << "-- " << comment << '\n';
}

void emitPendingLuaComments(std::ostringstream &lua, std::vector<std::string> &comments, const std::string &indent)
{
    for (const std::string &comment : comments)
    {
        emitLuaComment(lua, indent, comment);
    }
    comments.clear();
}

std::string luaContextMethodForCommand(const std::string &normalizedCommand)
{
    if (normalizedCommand == "dorude")
    {
        return "doRude";
    }
    if (normalizedCommand == "onrudeexit")
    {
        return "onRudeExit";
    }
    if (normalizedCommand == "givekey")
    {
        return "giveKey";
    }
    if (normalizedCommand == "takekey")
    {
        return "takeKey";
    }
    if (normalizedCommand == "haskey")
    {
        return "hasKey";
    }
    if (normalizedCommand == "giveitem")
    {
        return "giveItem";
    }
    if (normalizedCommand == "takeitem")
    {
        return "takeItem";
    }
    if (normalizedCommand == "hasitem")
    {
        return "hasItem";
    }
    if (normalizedCommand == "givegold")
    {
        return "giveGold";
    }
    if (normalizedCommand == "giveexp")
    {
        return "giveExp";
    }
    if (normalizedCommand == "setconsolenumvar")
    {
        return "setConsoleNumVar";
    }
    if (normalizedCommand == "getconsolenumvar")
    {
        return "getConsoleNumVar";
    }
    if (normalizedCommand == "setconsolestrvar")
    {
        return "setConsoleStrVar";
    }
    if (normalizedCommand == "getconsolestrvar")
    {
        return "getConsoleStrVar";
    }
    if (normalizedCommand == "getparam")
    {
        return "getParam";
    }
    if (normalizedCommand == "setpropnumber")
    {
        return "setPropNumber";
    }
    if (normalizedCommand == "getobjecthandlebyrudeid")
    {
        return "getObjectHandleByRudeId";
    }
    if (normalizedCommand == "addtrigger")
    {
        return "addTrigger";
    }
    if (normalizedCommand == "trigger")
    {
        return "trigger";
    }
    return {};
}

std::string mm9RudeServiceName(int32_t opcode)
{
    switch (opcode)
    {
    case -2:
        return "shop";
    case -3:
        return "training";
    case -4:
        return "skill_training";
    case -5:
        return "travel";
    case -6:
        return "bank";
    case -7:
        return "inn";
    case -8:
        return "healer";
    case -10:
        return "hire";
    case -11:
        return "dismiss";
    case -13:
        return "item_combine";
    case -14:
        return "quest_handoff";
    case -15:
        return "town_portal";
    case -16:
        return "donation";
    default:
        return "unknown";
    }
}

std::optional<std::string> yamlScalarString(const YAML::Node &node, const char *pKey)
{
    const YAML::Node child = node[pKey];
    if (!child)
    {
        return std::nullopt;
    }

    try
    {
        return child.as<std::string>();
    }
    catch (...)
    {
        return std::nullopt;
    }
}

int32_t yamlScalarInt(const YAML::Node &node, const char *pKey, int32_t fallback)
{
    const YAML::Node child = node[pKey];
    if (!child)
    {
        return fallback;
    }

    try
    {
        return child.as<int32_t>();
    }
    catch (...)
    {
        return fallback;
    }
}

bool yamlScalarBool(const YAML::Node &node, const char *pKey)
{
    const YAML::Node child = node[pKey];
    if (!child)
    {
        return false;
    }

    try
    {
        return child.as<bool>();
    }
    catch (...)
    {
        return false;
    }
}

std::string jsonStringScalar(const std::string &valueJson)
{
    try
    {
        const YAML::Node node = YAML::Load(valueJson);
        return node.as<std::string>();
    }
    catch (...)
    {
        return {};
    }
}

std::optional<uint8_t> hexByte(const std::string &text, size_t offset)
{
    if (offset + 2 > text.size())
    {
        return std::nullopt;
    }

    const std::string byteText = text.substr(offset, 2);
    try
    {
        return static_cast<uint8_t>(std::stoul(byteText, nullptr, 16));
    }
    catch (...)
    {
        return std::nullopt;
    }
}

std::optional<int32_t> decodeLittleEndianFloatInteger(const std::string &rawHex)
{
    if (rawHex.size() != 8)
    {
        return std::nullopt;
    }

    uint8_t bytes[4] = {};
    for (size_t index = 0; index < 4; ++index)
    {
        const std::optional<uint8_t> byte = hexByte(rawHex, index * 2);
        if (!byte)
        {
            return std::nullopt;
        }
        bytes[index] = *byte;
    }

    float value = 0.0f;
    std::memcpy(&value, bytes, sizeof(value));
    if (!std::isfinite(value))
    {
        return std::nullopt;
    }

    const float rounded = std::round(value);
    if (std::fabs(value - rounded) > 0.0001f || rounded < 0.0f || rounded > 100000.0f)
    {
        return std::nullopt;
    }

    return static_cast<int32_t>(rounded);
}

bool isTruthyValueJson(const std::string &valueJson)
{
    const std::optional<int32_t> numeric = parseMm9RudeInt(valueJson);
    return numeric && *numeric != 0;
}

Mm9RudeFile rudeFileFromGeneratedYaml(const std::string &yamlText, std::string &error)
{
    Mm9RudeFile file = {};
    YAML::Node root;
    try
    {
        root = YAML::Load(yamlText);
    }
    catch (const std::exception &exception)
    {
        error = exception.what();
        return file;
    }

    file.sourcePath = root["source_file"] ? root["source_file"].as<std::string>() : "";
    const YAML::Node rows = root["rows"];
    if (!rows || !rows.IsSequence())
    {
        error = "generated RUDE YAML is missing rows";
        return file;
    }

    for (const YAML::Node &rowNode : rows)
    {
        Mm9RudeRow row = {};
        if (rowNode["source"])
        {
            row.sourcePath = rowNode["source"]["file"] ? rowNode["source"]["file"].as<std::string>() : "";
            row.rowNumber = rowNode["source"]["row"] ? rowNode["source"]["row"].as<size_t>() : 0;
        }

        const YAML::Node rawColumns = rowNode["raw_columns"];
        if (!rawColumns || !rawColumns.IsSequence())
        {
            error = "generated RUDE YAML row is missing raw_columns";
            file.rows.clear();
            return file;
        }

        for (const YAML::Node &column : rawColumns)
        {
            row.columns.push_back(column.as<std::string>());
        }
        file.rows.push_back(std::move(row));
    }

    return file;
}

std::set<std::string> collectScriptSourceNames(const std::filesystem::path &scriptsDirectory)
{
    std::set<std::string> names;
    for (const std::filesystem::path &path : listScriptFiles(scriptsDirectory))
    {
        names.insert(lowerCopy(path.filename().string()));
    }
    return names;
}

std::string luaIndent(size_t depth)
{
    return std::string(4 + (depth * 4), ' ');
}

std::string luaArgumentList(const std::vector<std::string> &arguments)
{
    std::string result;
    for (const std::string &argument : arguments)
    {
        if (!result.empty())
        {
            result += ", ";
        }
        result += luaValueForScriptToken(argument);
    }
    return result;
}

std::string luaArgumentList(const std::string &argumentsText)
{
    return luaArgumentList(splitScriptArguments(argumentsText));
}

std::string readableControlConditionText(const Mm9ScriptLine &line)
{
    const std::string normalizedCommand = normalizeMm9ScriptCommandName(line.name);
    if ((normalizedCommand.rfind("if(", 0) == 0 || normalizedCommand.rfind("while(", 0) == 0)
        && normalizedCommand.size() > 3)
    {
        const size_t openParen = line.name.find('(');
        const size_t closeParen = line.name.rfind(')');
        if (openParen != std::string::npos && closeParen != std::string::npos && closeParen > openParen)
        {
            return trimCopy(line.name.substr(openParen + 1, closeParen - openParen - 1));
        }
    }
    std::string condition = trimCopy(line.argumentsText);
    if (normalizedCommand == "(if" && !condition.empty() && condition.back() == ')')
    {
        condition.pop_back();
    }
    if ((normalizedCommand.rfind("if(", 0) == 0 || normalizedCommand.rfind("while(", 0) == 0)
        && !condition.empty() && condition.back() == ')')
    {
        condition.pop_back();
    }
    condition = trimCopy(condition);
    if (condition.size() >= 2 && condition.front() == '(' && condition.back() == ')')
    {
        condition = trimCopy(condition.substr(1, condition.size() - 2));
    }
    if (!condition.empty() && condition.back() == ',')
    {
        condition.pop_back();
    }
    return trimCopy(condition);
}

bool isMm9ControlOpenCommand(const std::string &normalizedCommand)
{
    return normalizedCommand == "if" || normalizedCommand == "(if" || normalizedCommand == "while" ||
        normalizedCommand.rfind("if(", 0) == 0 || normalizedCommand.rfind("while(", 0) == 0;
}

bool isMm9ControlCloseCommand(const std::string &normalizedCommand)
{
    return normalizedCommand == "endif" || normalizedCommand == "endwhile";
}

struct Mm9LuaCollapsedPredicate
{
    bool valid = false;
    bool negated = false;
    std::string method;
    std::string arguments;
};

std::optional<bool> boolLiteralForConditionToken(const std::string &token)
{
    const std::string normalized = lowerCopy(trimCopy(token));
    if (normalized == "true" || normalized == "1")
    {
        return true;
    }
    if (normalized == "false" || normalized == "0")
    {
        return false;
    }
    return std::nullopt;
}

std::optional<bool> conditionChecksScriptBoolVar(const Mm9ScriptLine &line, const std::string &variableName)
{
    std::string condition = readableControlConditionText(line);
    condition.erase(
        std::remove_if(
            condition.begin(),
            condition.end(),
            [](const char ch)
            {
                return std::isspace(static_cast<unsigned char>(ch)) != 0;
            }),
        condition.end());

    const std::string normalizedCondition = lowerCopy(condition);
    const std::string normalizedVariable = lowerCopy(variableName);

    const auto checkOperator =
        [&](const std::string &operatorText) -> std::optional<bool>
        {
            const size_t operatorOffset = normalizedCondition.find(operatorText);
            if (operatorOffset == std::string::npos)
            {
                return std::nullopt;
            }

            const std::string left = normalizedCondition.substr(0, operatorOffset);
            const std::string right = normalizedCondition.substr(operatorOffset + operatorText.size());
            std::optional<bool> result;
            if (left == normalizedVariable)
            {
                result = boolLiteralForConditionToken(right);
            }
            else if (right == normalizedVariable)
            {
                result = boolLiteralForConditionToken(left);
            }
            if (!result)
            {
                return std::nullopt;
            }

            return operatorText == "!=" ? !*result : *result;
        };

    if (const std::optional<bool> equality = checkOperator("=="))
    {
        return equality;
    }
    return checkOperator("!=");
}

Mm9LuaCollapsedPredicate collapsedPredicateForCommandIfPair(
    const Mm9ScriptLine &predicateLine,
    const Mm9ScriptLine &conditionLine)
{
    Mm9LuaCollapsedPredicate predicate = {};
    const std::string normalizedPredicateCommand = normalizeMm9ScriptCommandName(predicateLine.name);
    if (normalizedPredicateCommand != "haskey" && normalizedPredicateCommand != "hasitem")
    {
        return predicate;
    }

    const std::string normalizedConditionCommand = normalizeMm9ScriptCommandName(conditionLine.name);
    if (!isMm9ControlOpenCommand(normalizedConditionCommand) || normalizedConditionCommand.rfind("while", 0) == 0)
    {
        return predicate;
    }

    const std::vector<std::string> arguments = splitScriptArguments(predicateLine.argumentsText);
    if (arguments.size() != 2 || lowerCopy(trimCopy(arguments[1])) != "g_ntemp")
    {
        return predicate;
    }

    const std::optional<bool> expectedValue = conditionChecksScriptBoolVar(conditionLine, arguments[1]);
    if (!expectedValue)
    {
        return predicate;
    }

    predicate.valid = true;
    predicate.negated = !*expectedValue;
    predicate.method = luaContextMethodForCommand(normalizedPredicateCommand);
    predicate.arguments = luaArgumentList(std::vector<std::string>{ arguments[0] });
    return predicate;
}

void emitCollapsedPredicateIf(
    std::ostringstream &lua,
    const Mm9ScriptLine &predicateLine,
    const Mm9ScriptLine &conditionLine,
    const Mm9LuaCollapsedPredicate &predicate,
    size_t indentDepth)
{
    const std::string indent = luaIndent(indentDepth);
    const std::optional<std::string> predicateComment =
        meaningfulLuaCommentFromMm9Comment(predicateLine.commentText);
    if (predicateComment)
    {
        emitLuaComment(lua, indent, *predicateComment);
    }

    const std::optional<std::string> conditionComment =
        meaningfulLuaCommentFromMm9Comment(conditionLine.commentText);
    if (conditionComment)
    {
        emitLuaComment(lua, indent, *conditionComment);
    }

    lua << indent << "if ";
    if (predicate.negated)
    {
        lua << "not ";
    }
    lua << "ctx:" << predicate.method << '(' << predicate.arguments << ") then"
        << " -- " << predicateLine.sourcePath.filename().string() << ':' << predicateLine.lineNumber
        << '-' << conditionLine.lineNumber << '\n';
}

void emitLuaCommandCall(std::ostringstream &lua, const Mm9ScriptLine &line, size_t indentDepth)
{
    const std::string normalizedCommand = normalizeMm9ScriptCommandName(line.name);
    const std::string method = luaContextMethodForCommand(normalizedCommand);
    const std::string firstArg = firstArgumentToken(line.argumentsText);
    const std::string indent = luaIndent(indentDepth);

    const std::optional<std::string> comment = meaningfulLuaCommentFromMm9Comment(line.commentText);
    if (comment)
    {
        emitLuaComment(lua, indent, *comment);
    }

    if (isMm9ControlOpenCommand(normalizedCommand))
    {
        const std::string keyword = normalizedCommand.rfind("while", 0) == 0 ? "while" : "if";
        lua << indent << keyword << " ctx:condition(" << luaString(readableControlConditionText(line))
            << ") " << (keyword == "while" ? "do" : "then")
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return;
    }
    if (normalizedCommand == "else")
    {
        lua << indent << "else -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return;
    }
    if (isMm9ControlCloseCommand(normalizedCommand))
    {
        lua << indent << "end -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return;
    }
    if (normalizedCommand == "exit")
    {
        lua << indent << "do return ctx:exit(" << luaValueForScriptToken(firstArg)
            << ") end -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return;
    }
    if (normalizedCommand == "gosub")
    {
        lua << indent << "mm9.gosub(script, ctx, " << luaString(firstArg) << ")"
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return;
    }
    if (normalizedCommand == "goto")
    {
        lua << indent << "do return mm9.gotoLabel(script, ctx, " << luaString(firstArg) << ") end"
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return;
    }

    if (!method.empty())
    {
        if (normalizedCommand == "onrudeexit")
        {
            lua << indent << "ctx:" << method << '(' << luaValueForScriptToken(firstArg)
                << ", script.labels[" << luaString(firstArg) << "])";
        }
        else
        {
            lua << indent << "ctx:" << method << '(' << luaArgumentList(line.argumentsText) << ")";
        }
    }
    else
    {
        lua << indent << "ctx:command(" << luaString(normalizedCommand) << ", "
            << luaString(line.argumentsText) << ")";
    }
    lua << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
}

void appendInventoryError(
    Mm9RudeSourceInventory &inventory,
    const std::filesystem::path &path,
    size_t rowNumber,
    const std::string &message)
{
    Mm9RudeParseError error = {};
    error.sourcePath = path;
    error.rowNumber = rowNumber;
    error.message = message;
    inventory.errors.push_back(error);
}

void validateColumnCount(
    Mm9RudeSourceInventory &inventory,
    const Mm9RudeFile &file,
    size_t expectedColumns)
{
    for (const Mm9RudeRow &row : file.rows)
    {
        if (row.columns.size() != expectedColumns)
        {
            std::ostringstream message;
            message << "expected " << expectedColumns << " columns, got " << row.columns.size();
            appendInventoryError(inventory, row.sourcePath, row.rowNumber, message.str());
        }
    }
}

void emitSource(YAML::Emitter &emitter, const Mm9RudeRow &row)
{
    emitter << YAML::Key << "source" << YAML::Value << YAML::BeginMap;
    emitter << YAML::Key << "file" << YAML::Value << row.sourcePath.filename().string();
    emitter << YAML::Key << "row" << YAML::Value << static_cast<uint32_t>(row.rowNumber);
    emitter << YAML::EndMap;
}

void emitDecodedNormalRow(YAML::Emitter &emitter, const Mm9RudeRow &row)
{
    if (row.columns.size() < 6)
    {
        return;
    }

    emitter << YAML::Key << "decoded" << YAML::Value << YAML::BeginMap;
    emitter << YAML::Key << "npc_id" << YAML::Value << row.columns[0];
    emitter << YAML::Key << "node_id" << YAML::Value << row.columns[1];
    emitter << YAML::Key << "choice_slot" << YAML::Value << row.columns[2];
    emitter << YAML::Key << "prompt" << YAML::Value << row.columns[3];
    emitter << YAML::Key << "response" << YAML::Value << row.columns[4];
    emitter << YAML::Key << "next" << YAML::Value << row.columns[5];

    emitter << YAML::Key << "raw_fields" << YAML::Value << YAML::BeginMap;
    for (size_t columnIndex = 6; columnIndex < row.columns.size(); ++columnIndex)
    {
        std::ostringstream key;
        key << 'c';
        if (columnIndex + 1 < 10)
        {
            key << '0';
        }
        key << (columnIndex + 1);
        emitter << YAML::Key << key.str() << YAML::Value << row.columns[columnIndex];
    }
    emitter << YAML::EndMap;
    emitter << YAML::EndMap;
}

const char *pseudoRudeTableKindName(Mm9PseudoRudeTableKind kind)
{
    switch (kind)
    {
    case Mm9PseudoRudeTableKind::JournalQuest:
        return "journal_quests";
    case Mm9PseudoRudeTableKind::JournalNote:
        return "journal_notes";
    case Mm9PseudoRudeTableKind::Award:
        return "awards";
    }

    return "unknown";
}

void emitRawColumns(YAML::Emitter &emitter, const Mm9RudeRow &row)
{
    emitter << YAML::Key << "raw_columns" << YAML::Value << YAML::BeginSeq;
    for (const std::string &column : row.columns)
    {
        emitter << column;
    }
    emitter << YAML::EndSeq;
}

std::string rudeColumnKey(size_t columnIndex)
{
    std::ostringstream key;
    key << 'c';
    if (columnIndex + 1 < 10)
    {
        key << '0';
    }
    key << (columnIndex + 1);
    return key.str();
}

bool rudeColumnValueIsEmptyZero(const std::string &value)
{
    if (value.empty())
    {
        return true;
    }

    const std::optional<int32_t> parsed = parseMm9RudeInt(value);
    return parsed && *parsed == 0;
}

bool rudeColumnIsValidatedRequiredKey(size_t columnIndex)
{
    constexpr size_t RequiredKeyColumns[] = {6, 8, 10, 12};
    for (const size_t requiredKeyColumn : RequiredKeyColumns)
    {
        if (columnIndex == requiredKeyColumn)
        {
            return true;
        }
    }
    return false;
}

void emitMm9KeyStateRef(YAML::Emitter &emitter, int32_t rawKeyId)
{
    emitter << YAML::BeginMap;
    emitter << YAML::Key << "domain" << YAML::Value << "mm9.keys";
    emitter << YAML::Key << "raw_id" << YAML::Value << rawKeyId;
    emitter << YAML::Key << "qbit_id" << YAML::Value << mm9KeyToQbitId(rawKeyId);
    emitter << YAML::Key << "state_id" << YAML::Value << ("mm9.keys." + std::to_string(rawKeyId));
    emitter << YAML::EndMap;
}

void emitSemanticAndUnresolvedBlocks(YAML::Emitter &emitter, const Mm9RudeRow &row)
{
    if (row.columns.size() < 6)
    {
        return;
    }

    const std::optional<int32_t> next = parseMm9RudeInt(row.columns[5]);

    std::vector<std::pair<size_t, int32_t>> requiredKeys;
    constexpr size_t RequiredKeyColumns[] = {6, 8, 10, 12};
    for (const size_t columnIndex : RequiredKeyColumns)
    {
        if (columnIndex >= row.columns.size())
        {
            continue;
        }

        const std::optional<int32_t> rawKeyId = parseMm9RudeInt(row.columns[columnIndex]);
        if (rawKeyId && *rawKeyId != 0)
        {
            requiredKeys.push_back({columnIndex, *rawKeyId});
        }
    }

    emitter << YAML::Key << "semantic" << YAML::Value << YAML::BeginMap;
    if (next)
    {
        emitter << YAML::Key << "action" << YAML::Value << YAML::BeginMap;
        if (*next > 0)
        {
            emitter << YAML::Key << "kind" << YAML::Value << "goto_node";
            emitter << YAML::Key << "target_node" << YAML::Value << *next;
        }
        else if (*next == -1)
        {
            emitter << YAML::Key << "kind" << YAML::Value << "close";
        }
        else if (*next < -1)
        {
            emitter << YAML::Key << "kind" << YAML::Value << "service";
            emitter << YAML::Key << "opcode" << YAML::Value << *next;
            emitter << YAML::Key << "service" << YAML::Value << mm9RudeServiceName(*next);
        }
        else
        {
            emitter << YAML::Key << "kind" << YAML::Value << "unresolved";
        }
        emitter << YAML::EndMap;
    }

    if (!requiredKeys.empty())
    {
        emitter << YAML::Key << "conditions" << YAML::Value << YAML::BeginMap;
        emitter << YAML::Key << "required_keys" << YAML::Value << YAML::BeginSeq;
        for (const std::pair<size_t, int32_t> &requiredKey : requiredKeys)
        {
            emitter << YAML::BeginMap;
            emitter << YAML::Key << "column" << YAML::Value << rudeColumnKey(requiredKey.first);
            emitter << YAML::Key << "raw_id" << YAML::Value << requiredKey.second;
            emitter << YAML::Key << "qbit_id" << YAML::Value << mm9KeyToQbitId(requiredKey.second);
            emitter << YAML::Key << "state_id" << YAML::Value
                << ("mm9.keys." + std::to_string(requiredKey.second));
            emitter << YAML::EndMap;
        }
        emitter << YAML::EndSeq;
        emitter << YAML::EndMap;

        emitter << YAML::Key << "state_refs" << YAML::Value << YAML::BeginSeq;
        for (const std::pair<size_t, int32_t> &requiredKey : requiredKeys)
        {
            emitMm9KeyStateRef(emitter, requiredKey.second);
        }
        emitter << YAML::EndSeq;
    }
    emitter << YAML::EndMap;

    bool hasUnresolved = (next && *next == 0) || (next && *next < -1);
    for (size_t columnIndex = 6; columnIndex < row.columns.size(); ++columnIndex)
    {
        if (!rudeColumnIsValidatedRequiredKey(columnIndex)
            && !rudeColumnValueIsEmptyZero(row.columns[columnIndex]))
        {
            hasUnresolved = true;
        }
    }

    if (!hasUnresolved)
    {
        return;
    }

    emitter << YAML::Key << "unresolved" << YAML::Value << YAML::BeginSeq;
    if (next && *next == 0)
    {
        emitter << YAML::BeginMap;
        emitter << YAML::Key << "kind" << YAML::Value << "next_zero";
        emitter << YAML::Key << "column" << YAML::Value << "c06";
        emitter << YAML::Key << "value" << YAML::Value << row.columns[5];
        emitter << YAML::Key << "status" << YAML::Value << "preserved_pending_exact_runtime_semantics";
        emitter << YAML::EndMap;
    }

    if (next && *next < -1)
    {
        emitter << YAML::BeginMap;
        emitter << YAML::Key << "kind" << YAML::Value << "service_behavior";
        emitter << YAML::Key << "column" << YAML::Value << "c06";
        emitter << YAML::Key << "opcode" << YAML::Value << *next;
        emitter << YAML::Key << "service" << YAML::Value << mm9RudeServiceName(*next);
        emitter << YAML::Key << "status" << YAML::Value << "typed_pending_exact_runtime_behavior";
        emitter << YAML::EndMap;
    }

    for (size_t columnIndex = 6; columnIndex < row.columns.size(); ++columnIndex)
    {
        if (rudeColumnIsValidatedRequiredKey(columnIndex)
            || rudeColumnValueIsEmptyZero(row.columns[columnIndex]))
        {
            continue;
        }

        emitter << YAML::BeginMap;
        emitter << YAML::Key << "kind" << YAML::Value << "unknown_sparse_field";
        emitter << YAML::Key << "column" << YAML::Value << rudeColumnKey(columnIndex);
        emitter << YAML::Key << "value" << YAML::Value << row.columns[columnIndex];
        emitter << YAML::Key << "status" << YAML::Value << "raw_value_preserved";
        emitter << YAML::EndMap;
    }
    emitter << YAML::EndSeq;
}

void emitRawTailFields(YAML::Emitter &emitter, const Mm9RudeRow &row)
{
    emitter << YAML::Key << "raw_fields" << YAML::Value << YAML::BeginMap;
    for (size_t columnIndex = 6; columnIndex < row.columns.size(); ++columnIndex)
    {
        std::ostringstream key;
        key << 'c';
        if (columnIndex + 1 < 10)
        {
            key << '0';
        }
        key << (columnIndex + 1);
        emitter << YAML::Key << key.str() << YAML::Value << row.columns[columnIndex];
    }
    emitter << YAML::EndMap;
}

Mm9ScriptLine parseMm9ScriptLine(const std::filesystem::path &path, size_t lineNumber, const std::string &rawLine)
{
    Mm9ScriptLine line = {};
    line.sourcePath = path;
    line.lineNumber = lineNumber;
    line.rawLine = rawLine;

    const size_t commentStart = rawLine.find(';');
    std::string codeText = commentStart == std::string::npos ? rawLine : rawLine.substr(0, commentStart);
    if (commentStart != std::string::npos)
    {
        line.commentText = rawLine.substr(commentStart);
    }

    line.codeText = trimCopy(codeText);
    if (line.codeText.empty())
    {
        line.kind = line.commentText.empty() ? Mm9ScriptLineKind::Blank : Mm9ScriptLineKind::Comment;
        return line;
    }

    if (line.codeText[0] == ':')
    {
        line.kind = Mm9ScriptLineKind::Label;
        line.name = trimCopy(line.codeText.substr(1));
        return line;
    }

    if (line.codeText[0] == '#')
    {
        line.name = firstToken(line.codeText);
        line.argumentsText = restAfterFirstToken(line.codeText);
        line.kind = lowerCopy(line.name) == "#include" ? Mm9ScriptLineKind::Include : Mm9ScriptLineKind::Declaration;
        return line;
    }

    line.kind = Mm9ScriptLineKind::Command;
    line.name = firstToken(line.codeText);
    line.argumentsText = restAfterFirstToken(line.codeText);
    return line;
}
}

std::optional<std::vector<std::string>> parseMm9RudeCsvLine(const std::string &line, std::string &error)
{
    std::vector<std::string> columns;
    std::string current;
    bool inQuote = false;

    for (size_t index = 0; index < line.size(); ++index)
    {
        const char ch = line[index];
        if (inQuote)
        {
            if (ch == '"')
            {
                if (index + 1 < line.size() && line[index + 1] == '"')
                {
                    current.push_back('"');
                    ++index;
                }
                else
                {
                    inQuote = false;
                }
            }
            else
            {
                current.push_back(ch);
            }
            continue;
        }

        if (ch == '"')
        {
            if (!current.empty())
            {
                error = "quote begins after unquoted data";
                return std::nullopt;
            }
            inQuote = true;
            continue;
        }

        if (ch == ',')
        {
            columns.push_back(current);
            current.clear();
            continue;
        }

        current.push_back(ch);
    }

    if (inQuote)
    {
        error = "unterminated quote";
        return std::nullopt;
    }

    columns.push_back(current);
    return columns;
}

int32_t mm9KeyToQbitId(int32_t rawKeyId)
{
    return Mm9KeyQbitBase + rawKeyId;
}

std::set<int32_t> mm9ReservedQbitIdsForRegistry(const Mm9KeyRegistry &registry)
{
    std::set<int32_t> qbitIds;
    for (const auto &entryPair : registry.entries)
    {
        qbitIds.insert(mm9KeyToQbitId(entryPair.second.keyId));
    }
    return qbitIds;
}

std::vector<int32_t> findMm9ReservedQbitCollisions(
    const Mm9KeyRegistry &registry,
    const std::set<int32_t> &qbitIds)
{
    std::vector<int32_t> collisions;
    const std::set<int32_t> reservedQbitIds = mm9ReservedQbitIdsForRegistry(registry);
    for (const int32_t qbitId : qbitIds)
    {
        if (reservedQbitIds.count(qbitId) != 0)
        {
            collisions.push_back(qbitId);
        }
    }
    return collisions;
}

bool mm9QbitIdIsInCustomRange(int32_t qbitId)
{
    return qbitId >= Mm9CustomQbitBegin;
}

std::string serializeMm9RudeCsvLine(const std::vector<std::string> &columns)
{
    std::string line;
    for (size_t columnIndex = 0; columnIndex < columns.size(); ++columnIndex)
    {
        if (columnIndex != 0)
        {
            line.push_back(',');
        }

        const std::string &column = columns[columnIndex];
        const bool needsQuote = column.find_first_of(",\"\r\n") != std::string::npos;
        if (!needsQuote)
        {
            line += column;
            continue;
        }

        line.push_back('"');
        for (const char ch : column)
        {
            if (ch == '"')
            {
                line += "\"\"";
            }
            else
            {
                line.push_back(ch);
            }
        }
        line.push_back('"');
    }

    return line;
}

Mm9RudeFile parseMm9RudeFile(const std::filesystem::path &path)
{
    Mm9RudeFile file = {};
    file.sourcePath = path;

    std::ifstream stream(path);
    if (!stream.good())
    {
        Mm9RudeParseError error = {};
        error.sourcePath = path;
        error.message = "failed to open file";
        file.errors.push_back(error);
        return file;
    }

    std::string line;
    size_t rowNumber = 0;
    while (std::getline(stream, line))
    {
        ++rowNumber;
        if (!line.empty() && line.back() == '\r')
        {
            line.pop_back();
        }

        std::string errorText;
        std::optional<std::vector<std::string>> columns = parseMm9RudeCsvLine(line, errorText);
        if (!columns)
        {
            Mm9RudeParseError error = {};
            error.sourcePath = path;
            error.rowNumber = rowNumber;
            error.message = errorText;
            file.errors.push_back(error);
            continue;
        }

        Mm9RudeRow row = {};
        row.sourcePath = path;
        row.rowNumber = rowNumber;
        row.columns = std::move(*columns);
        file.rows.push_back(std::move(row));
    }

    return file;
}

std::string generateMm9RudeYaml(const Mm9RudeFile &file)
{
    YAML::Emitter emitter;
    emitter << YAML::BeginMap;
    emitter << YAML::Key << "format_version" << YAML::Value << 1;
    emitter << YAML::Key << "source_file" << YAML::Value << file.sourcePath.filename().string();
    emitter << YAML::Key << "rows" << YAML::Value << YAML::BeginSeq;

    for (const Mm9RudeRow &row : file.rows)
    {
        emitter << YAML::BeginMap;
        emitSource(emitter, row);
        emitRawColumns(emitter, row);
        emitDecodedNormalRow(emitter, row);
        emitSemanticAndUnresolvedBlocks(emitter, row);
        emitter << YAML::EndMap;
    }

    emitter << YAML::EndSeq;
    emitter << YAML::EndMap;
    return std::string(emitter.c_str());
}

Mm9RudeSourceInventory scanMm9RudeSourceInventory(const std::filesystem::path &extractedRoot)
{
    Mm9RudeSourceInventory inventory = {};
    const std::filesystem::path rudeDirectory = extractedRoot / "RUDE/RUDE";
    const std::filesystem::path scriptsDirectory = extractedRoot / "SCRIPTS/SCRIPTS";

    std::set<int32_t> numberedNpcIds;
    std::set<std::pair<int32_t, int32_t>> numberedNodePairs;
    std::set<int32_t> normalNpcIds;
    std::set<std::pair<int32_t, int32_t>> normalNodePairs;

    const std::vector<std::filesystem::path> rudeFiles = listFilesWithExtension(rudeDirectory, ".rude");
    for (const std::filesystem::path &path : rudeFiles)
    {
        const Mm9RudeFile file = parseMm9RudeFile(path);
        inventory.errors.insert(inventory.errors.end(), file.errors.begin(), file.errors.end());

        if (path.filename() == "NPCNAME.rude")
        {
            inventory.npcNameRowCount = file.rows.size();
            validateColumnCount(inventory, file, 2);
            continue;
        }

        if (path.filename() == "TOPBLURB.rude")
        {
            inventory.topBlurbRowCount = file.rows.size();
            validateColumnCount(inventory, file, 3);
            continue;
        }

        const std::optional<uint32_t> npcNumber = npcNumberFromFileName(path);
        if (!npcNumber)
        {
            continue;
        }

        ++inventory.numberedRudeFileCount;
        inventory.numberedRudeRowCount += file.rows.size();
        validateColumnCount(inventory, file, 30);

        for (const Mm9RudeRow &row : file.rows)
        {
            if (row.columns.size() < 2)
            {
                continue;
            }

            const std::optional<int32_t> npcId = parseMm9RudeInt(row.columns[0]);
            const std::optional<int32_t> nodeId = parseMm9RudeInt(row.columns[1]);
            if (npcId && nodeId)
            {
                numberedNpcIds.insert(*npcId);
                numberedNodePairs.insert({*npcId, *nodeId});
            }
        }

        if (*npcNumber == 997)
        {
            inventory.npc997RowCount = file.rows.size();
            continue;
        }
        if (*npcNumber == 998)
        {
            inventory.npc998RowCount = file.rows.size();
            continue;
        }
        if (*npcNumber == 999)
        {
            inventory.npc999RowCount = file.rows.size();
            continue;
        }

        if (isNormalNpcDialogueFile(path))
        {
            ++inventory.normalDialogueFileCount;
            inventory.normalDialogueRowCount += file.rows.size();

            for (const Mm9RudeRow &row : file.rows)
            {
                if (row.columns.size() < 2)
                {
                    continue;
                }

                const std::optional<int32_t> npcId = parseMm9RudeInt(row.columns[0]);
                const std::optional<int32_t> nodeId = parseMm9RudeInt(row.columns[1]);
                if (npcId && nodeId)
                {
                    normalNpcIds.insert(*npcId);
                    normalNodePairs.insert({*npcId, *nodeId});
                }
            }
        }
    }

    inventory.numberedNpcIdCount = numberedNpcIds.size();
    inventory.numberedNodePairCount = numberedNodePairs.size();
    inventory.normalNpcIdCount = normalNpcIds.size();
    inventory.normalNodePairCount = normalNodePairs.size();
    inventory.scriptFileCount = listFilesWithExtension(scriptsDirectory, ".scr").size();
    inventory.includeFileCount = listFilesWithExtension(scriptsDirectory, ".inc").size();
    return inventory;
}

std::optional<int32_t> parseMm9RudeInt(const std::string &text)
{
    if (text.empty())
    {
        return std::nullopt;
    }

    size_t index = 0;
    if (text[index] == '-')
    {
        ++index;
    }

    if (index == text.size())
    {
        return std::nullopt;
    }

    for (; index < text.size(); ++index)
    {
        if (text[index] < '0' || text[index] > '9')
        {
            return std::nullopt;
        }
    }

    try
    {
        return static_cast<int32_t>(std::stol(text));
    }
    catch (...)
    {
        return std::nullopt;
    }
}

bool Mm9RudeDialogueProvider::loadFromFile(const Mm9RudeFile &file)
{
    m_file = file;
    m_currentRudeId = 0;
    m_currentNodeId = 0;
    m_closed = true;
    return !m_file.rows.empty();
}

bool Mm9RudeDialogueProvider::loadFromGeneratedYaml(const std::string &yamlText, std::string &error)
{
    Mm9RudeFile file = rudeFileFromGeneratedYaml(yamlText, error);
    if (!error.empty())
    {
        return false;
    }

    return loadFromFile(file);
}

bool Mm9RudeDialogueProvider::enterRudeId(int32_t rudeId)
{
    return enterNode(rudeId, rudeId);
}

bool Mm9RudeDialogueProvider::enterNode(int32_t rudeId, int32_t nodeId)
{
    for (const Mm9RudeRow &row : m_file.rows)
    {
        if (row.columns.size() < 2)
        {
            continue;
        }

        const std::optional<int32_t> rowRudeId = parseMm9RudeInt(row.columns[0]);
        const std::optional<int32_t> rowNodeId = parseMm9RudeInt(row.columns[1]);
        if (rowRudeId && rowNodeId && *rowRudeId == rudeId && *rowNodeId == nodeId)
        {
            m_currentRudeId = rudeId;
            m_currentNodeId = nodeId;
            m_closed = false;
            return true;
        }
    }

    return false;
}

bool Mm9RudeDialogueProvider::enterObjectContext(const Mm9ObjectDialogueBinding &binding)
{
    return binding.rudeId ? enterRudeId(*binding.rudeId) : false;
}

void Mm9RudeDialogueProvider::setOnRudeExitLabel(std::string label)
{
    m_onRudeExitLabel = std::move(label);
}

void Mm9RudeDialogueProvider::setKeyState(std::set<int32_t> keys)
{
    m_keys = std::move(keys);
}

int32_t Mm9RudeDialogueProvider::currentRudeId() const
{
    return m_currentRudeId;
}

int32_t Mm9RudeDialogueProvider::currentNodeId() const
{
    return m_currentNodeId;
}

std::vector<Mm9RudeTopic> Mm9RudeDialogueProvider::visibleTopics() const
{
    std::vector<Mm9RudeTopic> topics;
    if (m_closed)
    {
        return topics;
    }

    for (size_t rowIndex = 0; rowIndex < m_file.rows.size(); ++rowIndex)
    {
        const Mm9RudeRow &row = m_file.rows[rowIndex];
        if (row.columns.size() < 6)
        {
            continue;
        }

        const std::optional<int32_t> rudeId = parseMm9RudeInt(row.columns[0]);
        const std::optional<int32_t> nodeId = parseMm9RudeInt(row.columns[1]);
        const std::optional<int32_t> choiceSlot = parseMm9RudeInt(row.columns[2]);
        const std::optional<int32_t> next = parseMm9RudeInt(row.columns[5]);
        if (!rudeId || !nodeId || !choiceSlot || !next || *rudeId != m_currentRudeId ||
            *nodeId != m_currentNodeId || !rowHasRequiredKeys(row, m_keys))
        {
            continue;
        }

        Mm9RudeTopic topic = {};
        topic.rowIndex = rowIndex;
        topic.rowNumber = row.rowNumber;
        topic.choiceSlot = *choiceSlot;
        topic.next = *next;
        topic.prompt = row.columns[3];
        topic.response = row.columns[4];
        topic.rawColumns = row.columns;
        topics.push_back(std::move(topic));
    }

    std::sort(
        topics.begin(),
        topics.end(),
        [](const Mm9RudeTopic &left, const Mm9RudeTopic &right)
        {
            if (left.choiceSlot != right.choiceSlot)
            {
                return left.choiceSlot < right.choiceSlot;
            }
            return left.rowNumber < right.rowNumber;
        });

    return topics;
}

Mm9RudeSelectionResult Mm9RudeDialogueProvider::selectTopic(size_t visibleTopicIndex)
{
    Mm9RudeSelectionResult result = {};
    const std::vector<Mm9RudeTopic> topics = visibleTopics();
    if (visibleTopicIndex >= topics.size())
    {
        return result;
    }

    const Mm9RudeTopic &topic = topics[visibleTopicIndex];
    result.next = topic.next;
    result.response = topic.response;

    if (topic.next > 0)
    {
        result.kind = Mm9RudeSelectionKind::GotoNode;
        m_currentNodeId = topic.next;
    }
    else if (topic.next == -1)
    {
        result.kind = Mm9RudeSelectionKind::Close;
        result.onRudeExitLabel = m_onRudeExitLabel;
        m_closed = true;
    }
    else if (topic.next < -1)
    {
        result.kind = Mm9RudeSelectionKind::Service;
        result.serviceName = mm9RudeServiceName(topic.next);
    }
    else
    {
        result.kind = Mm9RudeSelectionKind::UnresolvedZero;
    }

    return result;
}

bool Mm9RudeDialogueProvider::closed() const
{
    return m_closed;
}

bool Mm9RudeDialogueProvider::rowHasRequiredKeys(const Mm9RudeRow &row, const std::set<int32_t> &keys)
{
    const size_t requiredKeyColumns[] = {6, 8, 10, 12};
    for (const size_t columnIndex : requiredKeyColumns)
    {
        if (columnIndex >= row.columns.size())
        {
            continue;
        }

        const std::optional<int32_t> keyId = parseMm9RudeInt(row.columns[columnIndex]);
        if (keyId && *keyId != 0 && keys.count(*keyId) == 0)
        {
            return false;
        }
    }

    return true;
}

Mm9ScriptFile parseMm9ScriptFile(const std::filesystem::path &path)
{
    Mm9ScriptFile file = {};
    file.sourcePath = path;

    std::ifstream stream(path);
    if (!stream.good())
    {
        Mm9RudeParseError error = {};
        error.sourcePath = path;
        error.message = "failed to open file";
        file.errors.push_back(error);
        return file;
    }

    std::string lineText;
    size_t lineNumber = 0;
    while (std::getline(stream, lineText))
    {
        ++lineNumber;
        if (!lineText.empty() && lineText.back() == '\r')
        {
            lineText.pop_back();
        }

        file.lines.push_back(parseMm9ScriptLine(path, lineNumber, lineText));
    }

    return file;
}

Mm9ScriptSourceInventory scanMm9ScriptSourceInventory(const std::filesystem::path &extractedRoot)
{
    Mm9ScriptSourceInventory inventory = {};
    const std::filesystem::path scriptsDirectory = extractedRoot / "SCRIPTS/SCRIPTS";
    inventory.scriptFileCount = listFilesWithExtension(scriptsDirectory, ".scr").size();
    inventory.includeFileCount = listFilesWithExtension(scriptsDirectory, ".inc").size();

    const std::vector<std::filesystem::path> scriptFiles = listScriptFiles(scriptsDirectory);
    for (const std::filesystem::path &path : scriptFiles)
    {
        const Mm9ScriptFile file = parseMm9ScriptFile(path);
        inventory.errors.insert(inventory.errors.end(), file.errors.begin(), file.errors.end());
        if (!file.errors.empty())
        {
            continue;
        }

        ++inventory.parsedFileCount;
        inventory.lineCount += file.lines.size();
        for (const Mm9ScriptLine &line : file.lines)
        {
            if (line.kind == Mm9ScriptLineKind::Label)
            {
                ++inventory.labelCount;
            }
            else if (line.kind == Mm9ScriptLineKind::Include)
            {
                ++inventory.includeDirectiveCount;
            }
            else if (line.kind == Mm9ScriptLineKind::Command)
            {
                const std::string normalizedName = normalizeMm9ScriptCommandName(line.name);
                ++inventory.commandCount;
                ++inventory.commandCounts[normalizedName];

                Mm9ScriptCommandRef commandRef = {};
                commandRef.sourcePath = line.sourcePath;
                commandRef.lineNumber = line.lineNumber;
                commandRef.commandName = normalizedName;
                commandRef.argumentsText = line.argumentsText;
                inventory.commandRefs.push_back(commandRef);
            }
        }
    }

    return inventory;
}

std::string normalizeMm9ScriptCommandName(const std::string &name)
{
    return lowerCopy(trimCopy(name));
}

Mm9KeyRegistry buildMm9KeyRegistry(const std::filesystem::path &extractedRoot)
{
    Mm9KeyRegistry registry = {};
    const std::filesystem::path rudeDirectory = extractedRoot / "RUDE/RUDE";
    const std::filesystem::path scriptsDirectory = extractedRoot / "SCRIPTS/SCRIPTS";

    const std::vector<std::filesystem::path> scriptFiles = listScriptFiles(scriptsDirectory);
    std::vector<Mm9ScriptFile> parsedScriptFiles;
    parsedScriptFiles.reserve(scriptFiles.size());

    for (const std::filesystem::path &path : scriptFiles)
    {
        Mm9ScriptFile file = parseMm9ScriptFile(path);
        for (const Mm9ScriptLine &line : file.lines)
        {
            const std::optional<std::pair<std::string, int32_t>> declaration = parseNumberDeclaration(line);
            if (declaration)
            {
                addConstant(registry, declaration->first, declaration->second);
            }
        }
        parsedScriptFiles.push_back(std::move(file));
    }

    for (const Mm9ScriptFile &file : parsedScriptFiles)
    {
        for (const Mm9ScriptLine &line : file.lines)
        {
            if (line.kind != Mm9ScriptLineKind::Command)
            {
                continue;
            }

            const std::string commandName = normalizeMm9ScriptCommandName(line.name);
            if (commandName != "givekey" && commandName != "takekey" && commandName != "haskey")
            {
                continue;
            }

            ++registry.scriptKeyOperationCount;
            const std::string token = firstArgumentToken(line.argumentsText);

            Mm9KeyEvidence evidence = {};
            evidence.sourceKind = "script_key_op";
            evidence.sourcePath = line.sourcePath;
            evidence.lineNumber = line.lineNumber;
            evidence.operation = commandName;
            evidence.symbol = token;

            const std::optional<int32_t> keyId = resolveKeyReference(registry, token);
            if (keyId)
            {
                ++registry.resolvedScriptKeyOperationCount;
                addKeyEvidence(registry, *keyId, evidence);
            }
            else
            {
                registry.unresolvedScriptReferences.push_back(evidence);
            }
        }
    }

    const std::vector<std::filesystem::path> rudeFiles = listFilesWithExtension(rudeDirectory, ".rude");
    for (const std::filesystem::path &path : rudeFiles)
    {
        if (path.filename() == "NPCNAME.rude" || path.filename() == "TOPBLURB.rude")
        {
            continue;
        }

        const Mm9RudeFile file = parseMm9RudeFile(path);
        for (const Mm9RudeRow &row : file.rows)
        {
            if (row.columns.size() < 30)
            {
                continue;
            }

            for (size_t columnIndex = 6; columnIndex < row.columns.size(); ++columnIndex)
            {
                const std::optional<int32_t> value = parseMm9RudeInt(row.columns[columnIndex]);
                if (!value || *value == 0)
                {
                    continue;
                }

                Mm9KeyEvidence evidence = {};
                evidence.sourceKind = "rude_sparse_field";
                evidence.sourcePath = row.sourcePath;
                evidence.rowNumber = row.rowNumber;
                evidence.columnNumber = columnIndex + 1;
                ++registry.rudeCandidateEvidenceCount;
                addKeyEvidence(registry, *value, evidence);
            }
        }
    }

    return registry;
}

std::string generateMm9KeyRegistryYaml(const Mm9KeyRegistry &registry)
{
    YAML::Emitter emitter;
    emitter << YAML::BeginMap;
    emitter << YAML::Key << "format_version" << YAML::Value << 1;
    emitter << YAML::Key << "state_domain" << YAML::Value << registry.stateDomain;
    emitter << YAML::Key << "backend" << YAML::Value << "qbits";
    emitter << YAML::Key << "qbit_base" << YAML::Value << Mm9KeyQbitBase;
    emitter << YAML::Key << "qbit_mapping" << YAML::Value << "9000 + raw_id";
    emitter << YAML::Key << "keys" << YAML::Value << YAML::BeginSeq;

    for (const auto &entryPair : registry.entries)
    {
        const Mm9KeyRegistryEntry &entry = entryPair.second;
        emitter << YAML::BeginMap;
        emitter << YAML::Key << "id" << YAML::Value << entry.keyId;
        emitter << YAML::Key << "raw_id" << YAML::Value << entry.keyId;
        emitter << YAML::Key << "qbit_id" << YAML::Value << mm9KeyToQbitId(entry.keyId);
        emitter << YAML::Key << "aliases" << YAML::Value << YAML::BeginSeq;
        for (const std::string &alias : entry.aliases)
        {
            emitter << alias;
        }
        emitter << YAML::EndSeq;
        emitter << YAML::Key << "evidence" << YAML::Value << YAML::BeginSeq;
        for (const Mm9KeyEvidence &evidence : entry.evidence)
        {
            emitter << YAML::BeginMap;
            emitter << YAML::Key << "kind" << YAML::Value << evidence.sourceKind;
            emitter << YAML::Key << "file" << YAML::Value << evidence.sourcePath.filename().string();
            if (evidence.lineNumber != 0)
            {
                emitter << YAML::Key << "line" << YAML::Value << static_cast<uint32_t>(evidence.lineNumber);
            }
            if (evidence.rowNumber != 0)
            {
                emitter << YAML::Key << "row" << YAML::Value << static_cast<uint32_t>(evidence.rowNumber);
            }
            if (evidence.columnNumber != 0)
            {
                emitter << YAML::Key << "column" << YAML::Value << static_cast<uint32_t>(evidence.columnNumber);
            }
            if (!evidence.operation.empty())
            {
                emitter << YAML::Key << "operation" << YAML::Value << evidence.operation;
            }
            if (!evidence.symbol.empty())
            {
                emitter << YAML::Key << "symbol" << YAML::Value << evidence.symbol;
            }
            emitter << YAML::EndMap;
        }
        emitter << YAML::EndSeq;
        emitter << YAML::EndMap;
    }

    emitter << YAML::EndSeq;
    emitter << YAML::Key << "unresolved_script_references" << YAML::Value << YAML::BeginSeq;
    for (const Mm9KeyEvidence &evidence : registry.unresolvedScriptReferences)
    {
        emitter << YAML::BeginMap;
        emitter << YAML::Key << "file" << YAML::Value << evidence.sourcePath.filename().string();
        emitter << YAML::Key << "line" << YAML::Value << static_cast<uint32_t>(evidence.lineNumber);
        emitter << YAML::Key << "operation" << YAML::Value << evidence.operation;
        emitter << YAML::Key << "symbol" << YAML::Value << evidence.symbol;
        emitter << YAML::EndMap;
    }
    emitter << YAML::EndSeq;
    emitter << YAML::EndMap;
    return std::string(emitter.c_str());
}

std::string generateMm9StateDefaultsYaml()
{
    YAML::Emitter emitter;
    emitter << YAML::BeginMap;
    emitter << YAML::Key << "format_version" << YAML::Value << 1;
    emitter << YAML::Key << "state_domains" << YAML::Value << YAML::BeginMap;

    emitter << YAML::Key << "keys" << YAML::Value << YAML::BeginMap;
    emitter << YAML::Key << "state_id_prefix" << YAML::Value << "mm9.keys";
    emitter << YAML::Key << "backend" << YAML::Value << "qbits";
    emitter << YAML::Key << "qbit_base" << YAML::Value << Mm9KeyQbitBase;
    emitter << YAML::Key << "default" << YAML::Value << false;
    emitter << YAML::EndMap;

    emitter << YAML::Key << "console_num_vars" << YAML::Value << YAML::BeginMap;
    emitter << YAML::Key << "backend" << YAML::Value << "mm9_script_state";
    emitter << YAML::Key << "default" << YAML::Value << 0;
    emitter << YAML::EndMap;

    emitter << YAML::Key << "console_str_vars" << YAML::Value << YAML::BeginMap;
    emitter << YAML::Key << "backend" << YAML::Value << "mm9_script_state";
    emitter << YAML::Key << "default" << YAML::Value << "";
    emitter << YAML::EndMap;

    emitter << YAML::Key << "map_vars" << YAML::Value << YAML::BeginMap;
    emitter << YAML::Key << "backend" << YAML::Value << "mm9_script_state";
    emitter << YAML::Key << "scope" << YAML::Value << "map";
    emitter << YAML::EndMap;

    emitter << YAML::Key << "object_properties" << YAML::Value << YAML::BeginMap;
    emitter << YAML::Key << "backend" << YAML::Value << "mm9_script_state";
    emitter << YAML::Key << "scope" << YAML::Value << "map_object";
    emitter << YAML::EndMap;
    emitter << YAML::EndMap;

    emitter << YAML::Key << "initial_state" << YAML::Value << YAML::BeginMap;
    emitter << YAML::Key << "console_num_vars" << YAML::Value << YAML::BeginMap << YAML::EndMap;
    emitter << YAML::Key << "console_str_vars" << YAML::Value << YAML::BeginMap << YAML::EndMap;
    emitter << YAML::Key << "map_num_vars" << YAML::Value << YAML::BeginMap << YAML::EndMap;
    emitter << YAML::Key << "map_str_vars" << YAML::Value << YAML::BeginMap << YAML::EndMap;
    emitter << YAML::Key << "script_num_vars" << YAML::Value << YAML::BeginMap << YAML::EndMap;
    emitter << YAML::Key << "script_str_vars" << YAML::Value << YAML::BeginMap << YAML::EndMap;
    emitter << YAML::Key << "object_handle_vars" << YAML::Value << YAML::BeginMap << YAML::EndMap;
    emitter << YAML::Key << "object_number_properties" << YAML::Value << YAML::BeginMap << YAML::EndMap;
    emitter << YAML::Key << "triggers" << YAML::Value << YAML::BeginSeq << YAML::EndSeq;
    emitter << YAML::Key << "trigger_dispatches" << YAML::Value << YAML::BeginSeq << YAML::EndSeq;
    emitter << YAML::EndMap;
    emitter << YAML::EndMap;
    return std::string(emitter.c_str());
}

std::string generateMm9PseudoRudeYaml(const Mm9RudeFile &file, Mm9PseudoRudeTableKind kind)
{
    YAML::Emitter emitter;
    emitter << YAML::BeginMap;
    emitter << YAML::Key << "format_version" << YAML::Value << 1;
    emitter << YAML::Key << "table_kind" << YAML::Value << pseudoRudeTableKindName(kind);
    emitter << YAML::Key << "source_file" << YAML::Value << file.sourcePath.filename().string();
    emitter << YAML::Key << "entries" << YAML::Value << YAML::BeginSeq;

    for (const Mm9RudeRow &row : file.rows)
    {
        emitter << YAML::BeginMap;
        emitSource(emitter, row);
        emitRawColumns(emitter, row);

        if (row.columns.size() >= 6)
        {
            emitter << YAML::Key << "decoded" << YAML::Value << YAML::BeginMap;
            emitter << YAML::Key << "rude_id" << YAML::Value << row.columns[0];
            emitter << YAML::Key << "node_id" << YAML::Value << row.columns[1];
            emitter << YAML::Key << "entry_id" << YAML::Value << row.columns[2];
            emitter << YAML::Key << "title" << YAML::Value << row.columns[3];
            emitter << YAML::Key << "text" << YAML::Value << row.columns[4];
            emitter << YAML::Key << "next" << YAML::Value << row.columns[5];
            emitRawTailFields(emitter, row);
            emitter << YAML::EndMap;
        }

        emitter << YAML::EndMap;
    }

    emitter << YAML::EndSeq;
    emitter << YAML::EndMap;
    return std::string(emitter.c_str());
}

std::vector<Mm9KeyEvidence> findMissingMm9PseudoRudeKeyReferences(
    const Mm9RudeFile &file,
    const Mm9KeyRegistry &registry)
{
    std::vector<Mm9KeyEvidence> missing;
    for (const Mm9RudeRow &row : file.rows)
    {
        if (row.columns.size() < 30)
        {
            continue;
        }

        for (size_t columnIndex = 6; columnIndex < row.columns.size(); ++columnIndex)
        {
            const std::optional<int32_t> keyId = parseMm9RudeInt(row.columns[columnIndex]);
            if (!keyId || *keyId == 0 || registry.entries.count(*keyId) != 0)
            {
                continue;
            }

            Mm9KeyEvidence evidence = {};
            evidence.sourceKind = "missing_pseudo_rude_key";
            evidence.sourcePath = row.sourcePath;
            evidence.rowNumber = row.rowNumber;
            evidence.columnNumber = columnIndex + 1;
            evidence.symbol = row.columns[columnIndex];
            missing.push_back(evidence);
        }
    }

    return missing;
}

std::string generateMm9ScriptRuntimeLua()
{
    std::ostringstream lua;
    lua << "-- generated MM9 script runtime support; do not edit by hand\n";
    lua << "local runtime = {}\n\n";
    lua << "function runtime.findLabel(script, name)\n";
    lua << "    local direct = script.labels[name]\n";
    lua << "    if direct ~= nil then\n";
    lua << "        return direct\n";
    lua << "    end\n";
    lua << "    local lowered = string.lower(name)\n";
    lua << "    for labelName, labelFunc in pairs(script.labels) do\n";
    lua << "        if string.lower(labelName) == lowered then\n";
    lua << "            return labelFunc\n";
    lua << "        end\n";
    lua << "    end\n";
    lua << "    return nil\n";
    lua << "end\n\n";
    lua << "function runtime.gosub(script, ctx, name)\n";
    lua << "    ctx:command(\"gosub\", name)\n";
    lua << "    local labelFunc = runtime.findLabel(script, name)\n";
    lua << "    if labelFunc ~= nil then\n";
    lua << "        return labelFunc(ctx)\n";
    lua << "    end\n";
    lua << "    return nil\n";
    lua << "end\n\n";
    lua << "function runtime.gotoLabel(script, ctx, name)\n";
    lua << "    ctx:command(\"goto\", name)\n";
    lua << "    local labelFunc = runtime.findLabel(script, name)\n";
    lua << "    if labelFunc ~= nil then\n";
    lua << "        return labelFunc(ctx)\n";
    lua << "    end\n";
    lua << "    return nil\n";
    lua << "end\n\n";
    lua << "return runtime\n";
    return lua.str();
}

std::string generateMm9ScriptLua(const Mm9ScriptFile &file)
{
    std::ostringstream lua;
    lua << "-- generated from MM9 script source; do not edit by hand\n";
    lua << "local mm9 = mm9ScriptRuntime\n";
    lua << "local script = {}\n";
    lua << "script.source = " << luaString(file.sourcePath.filename().string()) << "\n";
    lua << "script.includes = {}\n";
    lua << "script.labels = {}\n\n";

    for (const Mm9ScriptLine &line : file.lines)
    {
        if (line.kind == Mm9ScriptLineKind::Include)
        {
            lua << "script.includes[#script.includes + 1] = { line = " << line.lineNumber
                << ", path = " << luaString(line.argumentsText) << " }\n";
        }
    }
    lua << '\n';

    bool inTopLevel = false;
    bool inLabel = false;
    size_t indentDepth = 0;
    std::vector<std::string> pendingComments;
    for (size_t lineIndex = 0; lineIndex < file.lines.size(); ++lineIndex)
    {
        const Mm9ScriptLine &line = file.lines[lineIndex];
        if (line.kind == Mm9ScriptLineKind::Comment)
        {
            const std::optional<std::string> comment = meaningfulLuaCommentFromMm9Comment(line.commentText);
            if (comment)
            {
                pendingComments.push_back(*comment);
            }
            continue;
        }

        if (line.kind == Mm9ScriptLineKind::Label)
        {
            while (indentDepth > 0)
            {
                --indentDepth;
                lua << luaIndent(indentDepth) << "end -- implicit close before "
                    << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
            }
            if (inTopLevel)
            {
                lua << "end\n\n";
                inTopLevel = false;
            }
            if (inLabel)
            {
                lua << "end\n\n";
            }

            emitPendingLuaComments(lua, pendingComments, "");
            lua << "script.labels[" << luaString(line.name) << "] = function(ctx)\n";
            lua << "    -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
            indentDepth = 0;
            const std::optional<std::string> labelComment = meaningfulLuaCommentFromMm9Comment(line.commentText);
            if (labelComment)
            {
                emitLuaComment(lua, "    ", *labelComment);
            }
            inLabel = true;
            continue;
        }

        if (line.kind == Mm9ScriptLineKind::Command)
        {
            if (!inLabel && !inTopLevel)
            {
                lua << "script.topLevel = function(ctx)\n";
                inTopLevel = true;
                indentDepth = 0;
            }
            emitPendingLuaComments(lua, pendingComments, luaIndent(indentDepth));
            const std::string normalizedCommand = normalizeMm9ScriptCommandName(line.name);
            if (lineIndex + 1 < file.lines.size() && file.lines[lineIndex + 1].kind == Mm9ScriptLineKind::Command)
            {
                const Mm9ScriptLine &conditionLine = file.lines[lineIndex + 1];
                const Mm9LuaCollapsedPredicate collapsedPredicate =
                    collapsedPredicateForCommandIfPair(line, conditionLine);
                if (collapsedPredicate.valid)
                {
                    emitCollapsedPredicateIf(lua, line, conditionLine, collapsedPredicate, indentDepth);
                    ++indentDepth;
                    ++lineIndex;
                    continue;
                }
            }

            if ((normalizedCommand == "else" || isMm9ControlCloseCommand(normalizedCommand)) && indentDepth == 0)
            {
                lua << luaIndent(0) << "-- unmatched " << normalizedCommand
                    << " at " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
                continue;
            }
            if (normalizedCommand == "else" || isMm9ControlCloseCommand(normalizedCommand))
            {
                --indentDepth;
            }
            emitLuaCommandCall(lua, line, indentDepth);
            if (isMm9ControlOpenCommand(normalizedCommand) || normalizedCommand == "else")
            {
                ++indentDepth;
            }
        }

        if (line.kind == Mm9ScriptLineKind::Include || line.kind == Mm9ScriptLineKind::Declaration)
        {
            const std::optional<std::string> comment = meaningfulLuaCommentFromMm9Comment(line.commentText);
            if (comment)
            {
                pendingComments.push_back(*comment);
            }
        }
    }

    if (inTopLevel)
    {
        while (indentDepth > 0)
        {
            --indentDepth;
            lua << luaIndent(indentDepth) << "end -- implicit close before end of file\n";
        }
        lua << "end\n\n";
    }

    if (inLabel)
    {
        while (indentDepth > 0)
        {
            --indentDepth;
            lua << luaIndent(indentDepth) << "end -- implicit close before end of file\n";
        }
        lua << "end\n\n";
    }

    emitPendingLuaComments(lua, pendingComments, "");
    lua << "return script\n";
    return lua.str();
}

Mm9ObjectDialogueBindingIndex scanMm9ObjectDialogueBindings(
    const std::filesystem::path &mapsDirectory,
    const std::filesystem::path &scriptsDirectory,
    const std::set<int32_t> &knownRudeIds)
{
    Mm9ObjectDialogueBindingIndex index = {};
    const std::set<std::string> scriptSourceNames = collectScriptSourceNames(scriptsDirectory);
    const std::vector<std::filesystem::path> mapFiles = listFilesWithExtension(mapsDirectory, ".yml");

    for (const std::filesystem::path &path : mapFiles)
    {
        if (path.filename().string().find(".raw_objects.yml") == std::string::npos)
        {
            continue;
        }

        ++index.mapFileCount;
        YAML::Node root;
        try
        {
            root = YAML::LoadFile(path.string());
        }
        catch (const std::exception &exception)
        {
            Mm9RudeParseError error = {};
            error.sourcePath = path;
            error.message = exception.what();
            index.errors.push_back(error);
            continue;
        }

        const YAML::Node objects = root["objects"];
        if (!objects || !objects.IsSequence())
        {
            continue;
        }

        const std::string mapId = path.filename().string().substr(
            0,
            path.filename().string().find(".raw_objects.yml"));

        for (const YAML::Node &objectNode : objects)
        {
            ++index.objectCount;

            Mm9ObjectDialogueBinding binding = {};
            binding.sourcePath = path;
            binding.mapId = mapId;
            binding.objectIndex = yamlScalarInt(objectNode, "object_index", -1);
            binding.objectClass = yamlScalarString(objectNode, "name").value_or("");

            const YAML::Node properties = objectNode["properties"];
            if (!properties || !properties.IsSequence())
            {
                continue;
            }

            for (const YAML::Node &propertyNode : properties)
            {
                Mm9RawObjectProperty property = {};
                property.name = yamlScalarString(propertyNode, "name").value_or("");
                if (property.name.empty())
                {
                    continue;
                }

                property.code = yamlScalarInt(propertyNode, "code", 0);
                property.flags = yamlScalarInt(propertyNode, "flags", 0);
                property.decoded = yamlScalarBool(propertyNode, "decoded");
                property.rawHex = yamlScalarString(propertyNode, "raw_hex").value_or("");
                property.valueJson = yamlScalarString(propertyNode, "value_json").value_or("");

                if (property.name == "Name")
                {
                    binding.objectName = jsonStringScalar(property.valueJson);
                }

                if (property.name == "DoRude" || property.name == "NPCNbr" || property.name == "ScriptName" ||
                    property.name == "ScriptParams" || property.name == "GreetingSound")
                {
                    binding.properties[property.name] = property;
                }
            }

            const auto doRudeProperty = binding.properties.find("DoRude");
            if (doRudeProperty != binding.properties.end() && isTruthyValueJson(doRudeProperty->second.valueJson))
            {
                binding.doRude = true;
                ++index.doRudeCount;
            }

            const auto npcNbrProperty = binding.properties.find("NPCNbr");
            if (npcNbrProperty != binding.properties.end())
            {
                ++index.npcNbrPropertyCount;
                const std::optional<int32_t> decodedRudeId =
                    decodeLittleEndianFloatInteger(npcNbrProperty->second.rawHex);
                if (decodedRudeId && knownRudeIds.count(*decodedRudeId) != 0)
                {
                    binding.rudeId = *decodedRudeId;
                    binding.rudeDecodeStatus = "raw_hex_float_integer";
                    ++index.linkedRudeIdCount;
                }
                else
                {
                    binding.rudeDecodeStatus = "unresolved";
                }
            }

            const auto scriptNameProperty = binding.properties.find("ScriptName");
            if (scriptNameProperty != binding.properties.end())
            {
                binding.scriptName = jsonStringScalar(scriptNameProperty->second.valueJson);
                if (!binding.scriptName.empty())
                {
                    ++index.scriptNameCount;
                    binding.scriptSourceExists = scriptSourceNames.count(lowerCopy(binding.scriptName)) != 0;
                    if (binding.scriptSourceExists)
                    {
                        ++index.linkedScriptCount;
                    }
                }
            }

            binding.dialogueCapable = binding.doRude || binding.rudeId.has_value() ||
                binding.properties.count("NPCNbr") != 0;
            if (binding.dialogueCapable)
            {
                ++index.dialogueCapableCount;
                if (!binding.rudeId)
                {
                    ++index.unlinkedDialogueCapableCount;
                }
            }

            if (!binding.properties.empty())
            {
                ++index.bindingCount;
                index.bindings.push_back(std::move(binding));
            }
        }
    }

    return index;
}

namespace
{
void addPipelineError(
    Mm9DialoguePipelineResult &result,
    const std::filesystem::path &path,
    const std::string &message)
{
    Mm9RudeParseError error = {};
    error.sourcePath = path;
    error.message = message;
    result.errors.push_back(std::move(error));
}

void addWriteError(
    Mm9DialoguePipelineWriteResult &result,
    const std::filesystem::path &path,
    const std::string &message)
{
    Mm9RudeParseError error = {};
    error.sourcePath = path;
    error.message = message;
    result.errors.push_back(std::move(error));
}

bool isSafeGeneratedRelativePath(const std::filesystem::path &path)
{
    if (path.empty() || path.is_absolute())
    {
        return false;
    }

    for (const std::filesystem::path &part : path)
    {
        if (part == "..")
        {
            return false;
        }
    }

    return true;
}

void addGeneratedFile(
    Mm9DialoguePipelineResult &result,
    std::set<std::filesystem::path> &paths,
    const std::filesystem::path &relativePath,
    std::string contents)
{
    if (!isSafeGeneratedRelativePath(relativePath))
    {
        addPipelineError(result, relativePath, "generated path is not a safe relative path");
        return;
    }

    if (!paths.insert(relativePath).second)
    {
        addPipelineError(result, relativePath, "duplicate generated output path");
        return;
    }

    Mm9DialoguePipelineGeneratedFile file = {};
    file.relativePath = relativePath;
    file.contents = std::move(contents);
    result.files.push_back(std::move(file));
}

std::set<int32_t> collectKnownRudeIds(const std::filesystem::path &rudeDirectory)
{
    std::set<int32_t> ids;
    const std::vector<std::filesystem::path> rudeFiles = listFilesWithExtension(rudeDirectory, ".rude");
    for (const std::filesystem::path &path : rudeFiles)
    {
        if (path.filename() == "NPCNAME.rude" || path.filename() == "TOPBLURB.rude")
        {
            continue;
        }

        const Mm9RudeFile file = parseMm9RudeFile(path);
        for (const Mm9RudeRow &row : file.rows)
        {
            if (!row.columns.empty())
            {
                const std::optional<int32_t> id = parseMm9RudeInt(row.columns[0]);
                if (id)
                {
                    ids.insert(*id);
                }
            }
        }
    }
    return ids;
}

std::string serviceNameForOpcode(int32_t opcode)
{
    if (opcode == -1)
    {
        return "close";
    }

    return mm9RudeServiceName(opcode);
}

std::string generateMm9RudeServicesYaml(const std::filesystem::path &rudeDirectory)
{
    std::map<int32_t, size_t> opcodeCounts;
    const std::vector<std::filesystem::path> rudeFiles = listFilesWithExtension(rudeDirectory, ".rude");
    for (const std::filesystem::path &path : rudeFiles)
    {
        if (path.filename() == "NPCNAME.rude" || path.filename() == "TOPBLURB.rude")
        {
            continue;
        }

        const Mm9RudeFile file = parseMm9RudeFile(path);
        for (const Mm9RudeRow &row : file.rows)
        {
            if (row.columns.size() < 6)
            {
                continue;
            }

            const std::optional<int32_t> next = parseMm9RudeInt(row.columns[5]);
            if (next && *next < 0)
            {
                ++opcodeCounts[*next];
            }
        }
    }

    YAML::Emitter emitter;
    emitter << YAML::BeginMap;
    emitter << YAML::Key << "format_version" << YAML::Value << 1;
    emitter << YAML::Key << "services" << YAML::Value << YAML::BeginSeq;
    for (const auto &opcodeCount : opcodeCounts)
    {
        emitter << YAML::BeginMap;
        emitter << YAML::Key << "opcode" << YAML::Value << opcodeCount.first;
        emitter << YAML::Key << "name" << YAML::Value << serviceNameForOpcode(opcodeCount.first);
        emitter << YAML::Key << "observed_count" << YAML::Value << opcodeCount.second;
        emitter << YAML::Key << "status" << YAML::Value;
        if (opcodeCount.first == -14)
        {
            emitter << "pending_exact_validation";
        }
        else if (serviceNameForOpcode(opcodeCount.first) == "unknown")
        {
            emitter << "unknown_preserved";
        }
        else
        {
            emitter << "typed";
        }
        emitter << YAML::EndMap;
    }
    emitter << YAML::EndSeq;
    emitter << YAML::EndMap;
    return std::string(emitter.c_str());
}

std::string generateMm9ScriptIndexYaml(const std::filesystem::path &scriptsDirectory)
{
    YAML::Emitter emitter;
    emitter << YAML::BeginMap;
    emitter << YAML::Key << "format_version" << YAML::Value << 1;
    emitter << YAML::Key << "files" << YAML::Value << YAML::BeginSeq;

    const std::vector<std::filesystem::path> scriptFiles = listScriptFiles(scriptsDirectory);
    for (const std::filesystem::path &path : scriptFiles)
    {
        const Mm9ScriptFile file = parseMm9ScriptFile(path);
        emitter << YAML::BeginMap;
        emitter << YAML::Key << "source" << YAML::Value << path.filename().string();
        emitter << YAML::Key << "kind" << YAML::Value << (path.extension() == ".inc" ? "include" : "script");

        emitter << YAML::Key << "includes" << YAML::Value << YAML::BeginSeq;
        for (const Mm9ScriptLine &line : file.lines)
        {
            if (line.kind == Mm9ScriptLineKind::Include)
            {
                emitter << YAML::BeginMap;
                emitter << YAML::Key << "line" << YAML::Value << line.lineNumber;
                emitter << YAML::Key << "path" << YAML::Value << line.argumentsText;
                emitter << YAML::EndMap;
            }
        }
        emitter << YAML::EndSeq;

        emitter << YAML::Key << "labels" << YAML::Value << YAML::BeginSeq;
        for (const Mm9ScriptLine &line : file.lines)
        {
            if (line.kind == Mm9ScriptLineKind::Label)
            {
                emitter << YAML::BeginMap;
                emitter << YAML::Key << "line" << YAML::Value << line.lineNumber;
                emitter << YAML::Key << "name" << YAML::Value << line.name;
                emitter << YAML::EndMap;
            }
        }
        emitter << YAML::EndSeq;

        emitter << YAML::Key << "commands" << YAML::Value << YAML::BeginSeq;
        for (const Mm9ScriptLine &line : file.lines)
        {
            if (line.kind == Mm9ScriptLineKind::Command)
            {
                emitter << YAML::BeginMap;
                emitter << YAML::Key << "line" << YAML::Value << line.lineNumber;
                emitter << YAML::Key << "name" << YAML::Value << normalizeMm9ScriptCommandName(line.name);
                emitter << YAML::Key << "raw_name" << YAML::Value << line.name;
                emitter << YAML::Key << "args" << YAML::Value << line.argumentsText;
                emitter << YAML::EndMap;
            }
        }
        emitter << YAML::EndSeq;
        emitter << YAML::EndMap;
    }

    emitter << YAML::EndSeq;
    emitter << YAML::EndMap;
    return std::string(emitter.c_str());
}

std::string generateMm9ObjectDialogueBindingsYaml(const Mm9ObjectDialogueBindingIndex &index)
{
    YAML::Emitter emitter;
    emitter << YAML::BeginMap;
    emitter << YAML::Key << "format_version" << YAML::Value << 1;
    emitter << YAML::Key << "map_file_count" << YAML::Value << index.mapFileCount;
    emitter << YAML::Key << "object_count" << YAML::Value << index.objectCount;
    emitter << YAML::Key << "bindings" << YAML::Value << YAML::BeginSeq;

    for (const Mm9ObjectDialogueBinding &binding : index.bindings)
    {
        emitter << YAML::BeginMap;
        emitter << YAML::Key << "source_file" << YAML::Value << binding.sourcePath.filename().string();
        emitter << YAML::Key << "map" << YAML::Value << binding.mapId;
        emitter << YAML::Key << "object_index" << YAML::Value << binding.objectIndex;
        emitter << YAML::Key << "object_class" << YAML::Value << binding.objectClass;
        emitter << YAML::Key << "object_name" << YAML::Value << binding.objectName;
        emitter << YAML::Key << "dialogue_capable" << YAML::Value << binding.dialogueCapable;
        emitter << YAML::Key << "do_rude" << YAML::Value << binding.doRude;
        emitter << YAML::Key << "rude_decode_status" << YAML::Value << binding.rudeDecodeStatus;
        if (binding.rudeId)
        {
            emitter << YAML::Key << "rude_id" << YAML::Value << *binding.rudeId;
        }
        if (!binding.scriptName.empty())
        {
            emitter << YAML::Key << "script_name" << YAML::Value << binding.scriptName;
            emitter << YAML::Key << "script_source_exists" << YAML::Value << binding.scriptSourceExists;
        }

        emitter << YAML::Key << "properties" << YAML::Value << YAML::BeginMap;
        for (const auto &propertyPair : binding.properties)
        {
            const Mm9RawObjectProperty &property = propertyPair.second;
            emitter << YAML::Key << propertyPair.first << YAML::Value << YAML::BeginMap;
            emitter << YAML::Key << "code" << YAML::Value << property.code;
            emitter << YAML::Key << "flags" << YAML::Value << property.flags;
            emitter << YAML::Key << "decoded" << YAML::Value << property.decoded;
            emitter << YAML::Key << "raw_hex" << YAML::Value << property.rawHex;
            emitter << YAML::Key << "value_json" << YAML::Value << property.valueJson;
            emitter << YAML::EndMap;
        }
        emitter << YAML::EndMap;
        emitter << YAML::EndMap;
    }

    emitter << YAML::EndSeq;
    emitter << YAML::EndMap;
    return std::string(emitter.c_str());
}

bool readWholeTextFile(const std::filesystem::path &path, std::string &contents)
{
    std::ifstream stream(path, std::ios::binary);
    if (!stream)
    {
        return false;
    }

    std::ostringstream buffer;
    buffer << stream.rdbuf();
    contents = buffer.str();
    return stream.good();
}

bool writeWholeTextFile(const std::filesystem::path &path, const std::string &contents)
{
    std::error_code error;
    std::filesystem::create_directories(path.parent_path(), error);
    if (error)
    {
        return false;
    }

    std::ofstream stream(path, std::ios::binary);
    if (!stream)
    {
        return false;
    }

    stream.write(contents.data(), static_cast<std::streamsize>(contents.size()));
    return stream.good();
}
}

Mm9DialoguePipelineResult generateMm9DialoguePipelineFiles(
    const std::filesystem::path &extractedRoot,
    const std::filesystem::path &mapsDirectory)
{
    Mm9DialoguePipelineResult result = {};
    std::set<std::filesystem::path> generatedPaths;
    const std::filesystem::path rudeDirectory = extractedRoot / "RUDE/RUDE";
    const std::filesystem::path scriptsDirectory = extractedRoot / "SCRIPTS/SCRIPTS";

    const Mm9RudeSourceInventory rudeInventory = scanMm9RudeSourceInventory(extractedRoot);
    result.errors.insert(result.errors.end(), rudeInventory.errors.begin(), rudeInventory.errors.end());
    const Mm9ScriptSourceInventory scriptInventory = scanMm9ScriptSourceInventory(extractedRoot);
    result.errors.insert(result.errors.end(), scriptInventory.errors.begin(), scriptInventory.errors.end());

    const std::vector<std::filesystem::path> rudeFiles = listFilesWithExtension(rudeDirectory, ".rude");
    for (const std::filesystem::path &path : rudeFiles)
    {
        const Mm9RudeFile file = parseMm9RudeFile(path);
        result.errors.insert(result.errors.end(), file.errors.begin(), file.errors.end());
        if (!file.errors.empty())
        {
            continue;
        }

        if (path.filename() == "NPCNAME.rude")
        {
            addGeneratedFile(result, generatedPaths, "dialogue/npc_names.yml", generateMm9RudeYaml(file));
            continue;
        }

        if (path.filename() == "TOPBLURB.rude")
        {
            addGeneratedFile(result, generatedPaths, "dialogue/top_blurbs.yml", generateMm9RudeYaml(file));
            continue;
        }

        if (path.filename() == "NPC997.rude")
        {
            addGeneratedFile(
                result,
                generatedPaths,
                "dialogue/journal_quests.yml",
                generateMm9PseudoRudeYaml(file, Mm9PseudoRudeTableKind::JournalQuest));
            continue;
        }

        if (path.filename() == "NPC998.rude")
        {
            addGeneratedFile(
                result,
                generatedPaths,
                "dialogue/journal_notes.yml",
                generateMm9PseudoRudeYaml(file, Mm9PseudoRudeTableKind::JournalNote));
            continue;
        }

        if (path.filename() == "NPC999.rude")
        {
            addGeneratedFile(
                result,
                generatedPaths,
                "dialogue/awards.yml",
                generateMm9PseudoRudeYaml(file, Mm9PseudoRudeTableKind::Award));
            continue;
        }

        const std::optional<uint32_t> npcNumber = npcNumberFromFileName(path);
        if (npcNumber && isNormalNpcDialogueFile(path))
        {
            const std::filesystem::path relativePath =
                std::filesystem::path("dialogue/npcs") / (std::to_string(*npcNumber) + ".yml");
            addGeneratedFile(result, generatedPaths, relativePath, generateMm9RudeYaml(file));
        }
    }

    addGeneratedFile(
        result,
        generatedPaths,
        "dialogue/services.yml",
        generateMm9RudeServicesYaml(rudeDirectory));

    const Mm9KeyRegistry keyRegistry = buildMm9KeyRegistry(extractedRoot);
    addGeneratedFile(result, generatedPaths, "state/keys.yml", generateMm9KeyRegistryYaml(keyRegistry));
    addGeneratedFile(result, generatedPaths, "state/defaults.yml", generateMm9StateDefaultsYaml());
    addGeneratedFile(
        result,
        generatedPaths,
        "scripts/common/mm9_script_runtime.lua",
        generateMm9ScriptRuntimeLua());

    const std::vector<std::filesystem::path> scriptFiles = listScriptFiles(scriptsDirectory);
    for (const std::filesystem::path &path : scriptFiles)
    {
        const Mm9ScriptFile file = parseMm9ScriptFile(path);
        result.errors.insert(result.errors.end(), file.errors.begin(), file.errors.end());
        if (!file.errors.empty())
        {
            continue;
        }

        const std::filesystem::path outputDirectory =
            path.extension() == ".inc" ? std::filesystem::path("scripts/includes") : std::filesystem::path("scripts");
        const std::filesystem::path relativePath = outputDirectory / (path.stem().string() + ".lua");
        addGeneratedFile(result, generatedPaths, relativePath, generateMm9ScriptLua(file));
    }

    addGeneratedFile(result, generatedPaths, "scripts/script_index.yml", generateMm9ScriptIndexYaml(scriptsDirectory));

    const std::set<int32_t> knownRudeIds = collectKnownRudeIds(rudeDirectory);
    const Mm9ObjectDialogueBindingIndex objectBindings =
        scanMm9ObjectDialogueBindings(mapsDirectory, scriptsDirectory, knownRudeIds);
    result.errors.insert(result.errors.end(), objectBindings.errors.begin(), objectBindings.errors.end());
    addGeneratedFile(
        result,
        generatedPaths,
        "maps/dialogue_bindings.yml",
        generateMm9ObjectDialogueBindingsYaml(objectBindings));

    std::sort(
        result.files.begin(),
        result.files.end(),
        [](const Mm9DialoguePipelineGeneratedFile &left, const Mm9DialoguePipelineGeneratedFile &right)
        {
            return left.relativePath.generic_string() < right.relativePath.generic_string();
        });

    return result;
}

Mm9DialoguePipelineWriteResult writeMm9DialoguePipelineFiles(
    const std::filesystem::path &outputRoot,
    const std::vector<Mm9DialoguePipelineGeneratedFile> &files,
    bool checkOnly)
{
    Mm9DialoguePipelineWriteResult result = {};
    for (const Mm9DialoguePipelineGeneratedFile &file : files)
    {
        if (!isSafeGeneratedRelativePath(file.relativePath))
        {
            addWriteError(result, file.relativePath, "generated path is not a safe relative path");
            continue;
        }

        const std::filesystem::path outputPath = outputRoot / file.relativePath;
        std::string existingContents;
        if (readWholeTextFile(outputPath, existingContents) && existingContents == file.contents)
        {
            ++result.unchangedFileCount;
            continue;
        }

        if (checkOnly)
        {
            ++result.staleFileCount;
            addWriteError(result, outputPath, "generated file is missing or stale");
            continue;
        }

        if (!writeWholeTextFile(outputPath, file.contents))
        {
            addWriteError(result, outputPath, "could not write generated file");
            continue;
        }

        ++result.writtenFileCount;
    }

    return result;
}
}
