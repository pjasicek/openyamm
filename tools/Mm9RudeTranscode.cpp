#include "tools/Mm9RudeTranscode.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cctype>
#include <cmath>
#include <cstring>
#include <fstream>
#include <iterator>
#include <map>
#include <ostream>
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

std::vector<std::string> normalizedServiceArguments(const std::vector<std::string> &arguments);

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

bool isSimpleLuaNumberLiteral(const std::string &token)
{
    const std::string trimmed = trimCopy(token);
    if (trimmed.empty())
    {
        return false;
    }

    size_t index = 0;
    if (trimmed[index] == '-')
    {
        ++index;
    }

    bool sawDigit = false;
    bool sawDot = false;
    for (; index < trimmed.size(); ++index)
    {
        const char ch = trimmed[index];
        if (ch >= '0' && ch <= '9')
        {
            sawDigit = true;
            continue;
        }

        if (ch == '.' && !sawDot)
        {
            sawDot = true;
            continue;
        }

        return false;
    }

    return sawDigit;
}

std::string luaRuntimeArgumentForScriptToken(const std::string &token)
{
    const std::string trimmed = trimCopy(token);
    if (isSimpleLuaNumberLiteral(trimmed))
    {
        return trimmed;
    }

    if (trimmed.size() >= 2 && trimmed.front() == '"' && trimmed.back() == '"')
    {
        return luaString(trimmed.substr(1, trimmed.size() - 2));
    }

    return luaString(trimmed);
}

std::string luaTriggerTargetArgumentForScriptToken(const std::string &token)
{
    const std::string trimmed = trimCopy(token);
    const std::string lowered = lowerCopy(trimmed);
    if (lowered == "null" || lowered == "nil" || lowered == "0")
    {
        return "nil";
    }

    return luaValueForScriptToken(trimmed);
}

std::string luaRuntimeArgumentForScheduleToken(const std::string &token)
{
    const std::string trimmed = trimCopy(token);
    const std::optional<int32_t> number = parseMm9RudeInt(trimmed);
    if (number)
    {
        return std::to_string(*number);
    }

    return luaRuntimeArgumentForScriptToken(trimmed);
}

std::string unquotedScriptToken(const std::string &token)
{
    const std::string trimmed = trimCopy(token);
    if (trimmed.size() >= 2 && trimmed.front() == '"' && trimmed.back() == '"')
    {
        return trimmed.substr(1, trimmed.size() - 2);
    }

    return trimmed;
}

bool isLuaIdentifier(const std::string &text)
{
    if (text.empty())
    {
        return false;
    }

    const unsigned char first = static_cast<unsigned char>(text.front());
    if (std::isalpha(first) == 0 && text.front() != '_')
    {
        return false;
    }

    for (size_t index = 1; index < text.size(); ++index)
    {
        const unsigned char ch = static_cast<unsigned char>(text[index]);
        if (std::isalnum(ch) == 0 && text[index] != '_')
        {
            return false;
        }
    }

    return true;
}

std::string luaStateField(const std::string &name)
{
    return "ctx:state()." + name;
}

std::optional<std::string> luaLiteralForSimpleScriptExpression(const std::string &expression)
{
    const std::string trimmed = trimCopy(expression);
    if (trimmed.empty())
    {
        return std::nullopt;
    }

    const std::string lowered = lowerCopy(trimmed);
    if (lowered == "true")
    {
        return "true";
    }
    if (lowered == "false")
    {
        return "false";
    }
    if (lowered == "null")
    {
        return "nil";
    }

    const std::optional<int32_t> number = parseMm9RudeInt(trimmed);
    if (number)
    {
        return std::to_string(*number);
    }

    if (trimmed.size() >= 2 && trimmed.front() == '"' && trimmed.back() == '"')
    {
        return luaString(trimmed.substr(1, trimmed.size() - 2));
    }

    return std::nullopt;
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
    if (normalizedCommand == "docallback")
    {
        return "doCallback";
    }
    if (normalizedCommand == "exitscript")
    {
        return "exitScript";
    }
    if (normalizedCommand == "isturnbased")
    {
        return "isTurnBased";
    }
    if (normalizedCommand == "traceoff")
    {
        return "traceOff";
    }
    if (normalizedCommand == "traceon")
    {
        return "traceOn";
    }
    if (normalizedCommand == "breakpoint")
    {
        return "breakpoint";
    }
    if (normalizedCommand == "dont_include_this_file")
    {
        return "dontIncludeThisFile";
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
    if (normalizedCommand == "hasgold")
    {
        return "hasGold";
    }
    if (normalizedCommand == "takegold")
    {
        return "takeGold";
    }
    if (normalizedCommand == "giveexp")
    {
        return "giveExp";
    }
    if (normalizedCommand == "givepromo")
    {
        return "givePromo";
    }
    if (normalizedCommand == "getattribute")
    {
        return "getAttribute";
    }
    if (normalizedCommand == "giveattribute")
    {
        return "giveAttribute";
    }
    if (normalizedCommand == "cachescript")
    {
        return "cacheScript";
    }
    if (normalizedCommand == "runscript")
    {
        return "runScript";
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

std::string readableLuaCommandName(const Mm9ScriptLine &line)
{
    const std::string normalizedCommand = normalizeMm9ScriptCommandName(line.name);
    static const std::map<std::string, std::string> readableNames = {
        {"addmodelkey", "AddModelKey"},
        {"removeattrigger", "RemoveATrigger"},
        {"removemodelkey", "RemoveModelKey"},
        {"removetrigger", "RemoveTrigger"},
        {"onalert", "OnAlert"},
        {"onattackready", "OnAttackReady"},
        {"onavoidingobstacle", "OnAvoidingObstacle"},
        {"oncachefiles", "OnCacheFiles"},
        {"oncongestion", "OnCongestion"},
        {"ondamage", "OnDamage"},
        {"ondamagedone", "OnDamageDone"},
        {"ondeath", "OnDeath"},
        {"ondeathdone", "OnDeathDone"},
        {"ondoor", "OnDoor"},
        {"onenrage", "OnEnrage"},
        {"onenragedone", "OnEnrageDone"},
        {"onfear", "OnFear"},
        {"onfeardone", "OnFearDone"},
        {"onfoundplayer", "OnFoundPlayer"},
        {"onfoundtarget", "OnFoundTarget"},
        {"onhelp", "OnHelp"},
        {"onlosttarget", "OnLostTarget"},
        {"onobjectlinkbroken", "OnObjectLinkBroken"},
        {"onobstacle", "OnObstacle"},
        {"onobstacleavoided", "OnObstacleAvoided"},
        {"onpathclear", "OnPathClear"},
        {"onplayerinterrupt", "OnPlayerInterrupt"},
        {"onpostminisaveload", "OnPostMiniSaveLoad"},
        {"onpostsaveload", "OnPostSaveLoad"},
        {"onpoststartworld", "OnPostStartWorld"},
        {"onprojectile", "OnProjectile"},
        {"onstuck", "OnStuck"},
        {"onstuckdone", "OnStuckDone"},
        {"ontargetbeyonddist", "OnTargetBeyondDist"},
        {"ontargetdead", "OnTargetDead"},
        {"ontargethit", "OnTargetHit"},
        {"ontargetoutofrange", "OnTargetOutOfRange"},
        {"ontargetwithindist", "OnTargetWithinDist"},
        {"ontouchnotify", "OnTouchNotify"},
        {"onworldswitch", "OnWorldSwitch"},
    };

    const auto readableIterator = readableNames.find(normalizedCommand);
    if (readableIterator != readableNames.end())
    {
        return readableIterator->second;
    }

    return normalizedCommand;
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
    const std::string rawCommand = lowerCopy(trimCopy(line.name));
    const std::string normalizedCommand = normalizeMm9ScriptCommandName(line.name);
    const bool compactParenCommand = rawCommand.rfind("if(", 0) == 0 || rawCommand.rfind("while(", 0) == 0;
    if (compactParenCommand && rawCommand.size() > 3)
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
    if (compactParenCommand && !condition.empty() && condition.back() == ')')
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

std::optional<std::pair<std::string, std::string>> simpleSetAssignment(const std::string &argumentsText)
{
    const std::vector<std::string> commaArguments = splitScriptArguments(argumentsText);
    if (hasTopLevelComma(argumentsText))
    {
        if (commaArguments.size() < 2)
        {
            return std::nullopt;
        }
        return std::make_pair(trimCopy(commaArguments[0]), trimCopy(commaArguments[1]));
    }

    const std::string target = firstArgumentToken(argumentsText);
    if (target.empty())
    {
        return std::nullopt;
    }

    return std::make_pair(target, trimCopy(restAfterFirstToken(argumentsText)));
}

bool emitNativeStateMutationIfSupported(std::ostringstream &lua, const Mm9ScriptLine &line, size_t indentDepth)
{
    const std::string normalizedCommand = normalizeMm9ScriptCommandName(line.name);
    const std::string trimmedArguments = trimCopy(line.argumentsText);
    const std::string indent = luaIndent(indentDepth);

    if (!trimmedArguments.empty() && trimmedArguments.front() == '=')
    {
        const std::string target = trimCopy(line.name);
        if (!isLuaIdentifier(target))
        {
            return false;
        }

        const std::optional<std::string> expression =
            luaLiteralForSimpleScriptExpression(trimCopy(trimmedArguments.substr(1)));
        if (!expression)
        {
            return false;
        }

        lua << indent << luaStateField(target) << " = " << *expression
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return true;
    }

    if (normalizedCommand == "set")
    {
        const std::optional<std::pair<std::string, std::string>> assignment =
            simpleSetAssignment(line.argumentsText);
        if (!assignment || !isLuaIdentifier(assignment->first))
        {
            return false;
        }

        const std::optional<std::string> expression = luaLiteralForSimpleScriptExpression(assignment->second);
        if (!expression)
        {
            return false;
        }

        lua << indent << luaStateField(assignment->first) << " = " << *expression
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return true;
    }

    if (normalizedCommand == "setint")
    {
        const std::vector<std::string> arguments = normalizedServiceArguments(splitScriptArguments(line.argumentsText));
        if (arguments.size() < 2 || !isLuaIdentifier(trimCopy(arguments[0])))
        {
            return false;
        }

        lua << indent << "ctx:setInt(" << luaString(trimCopy(arguments[0])) << ", "
            << luaRuntimeArgumentForScriptToken(arguments[1]) << ")"
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return true;
    }

    if (normalizedCommand == "add" || normalizedCommand == "sub" || normalizedCommand == "subtract"
        || normalizedCommand == "mul" || normalizedCommand == "multiply"
        || normalizedCommand == "div" || normalizedCommand == "divide")
    {
        const std::vector<std::string> arguments = splitScriptArguments(line.argumentsText);
        if (arguments.size() < 2 || !isLuaIdentifier(trimCopy(arguments[0])))
        {
            return false;
        }

        const std::optional<int32_t> operand = parseMm9RudeInt(trimCopy(arguments[1]));
        if (!operand)
        {
            return false;
        }

        const std::string target = trimCopy(arguments[0]);
        if ((normalizedCommand == "div" || normalizedCommand == "divide") && *operand == 0)
        {
            lua << indent << luaStateField(target) << " = 0"
                << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
            return true;
        }

        std::string op;
        if (normalizedCommand == "add")
        {
            op = "+";
        }
        else if (normalizedCommand == "sub" || normalizedCommand == "subtract")
        {
            op = "-";
        }
        else if (normalizedCommand == "mul" || normalizedCommand == "multiply")
        {
            op = "*";
        }
        else
        {
            op = "/";
        }

        lua << indent << luaStateField(target) << " = (tonumber(" << luaStateField(target) << ") or 0) "
            << op << ' ' << *operand
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return true;
    }

    return false;
}

bool emitNativeHandleAssignmentIfSupported(std::ostringstream &lua, const Mm9ScriptLine &line, size_t indentDepth)
{
    const std::string normalizedCommand = normalizeMm9ScriptCommandName(line.name);
    if (normalizedCommand != "getmyhandle" && normalizedCommand != "getplayerhandle")
    {
        return false;
    }

    const std::vector<std::string> arguments =
        normalizedServiceArguments(splitScriptArguments(line.argumentsText));
    size_t destinationIndex = 0;
    if (arguments.size() >= 2 && trimCopy(arguments[0]).empty())
    {
        destinationIndex = 1;
    }
    if (arguments.size() <= destinationIndex || !isLuaIdentifier(trimCopy(arguments[destinationIndex])))
    {
        return false;
    }

    const std::string targetName = trimCopy(arguments[destinationIndex]);
    const std::string loweredTargetName = lowerCopy(targetName);
    if (normalizedCommand == "getmyhandle" && (loweredTargetName == "hme" || loweredTargetName == "g_hmyobject"))
    {
        return true;
    }
    if (normalizedCommand == "getplayerhandle" && (loweredTargetName == "hplayer" || loweredTargetName == "player"))
    {
        return true;
    }

    const std::string method = normalizedCommand == "getmyhandle" ? "self" : "player";
    const std::string indent = luaIndent(indentDepth);
    lua << indent << luaStateField(targetName) << " = ctx:" << method << "()"
        << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
    return true;
}

struct Mm9LuaGenerationState
{
    std::map<std::string, std::string> handleAliases;
    struct AliasFrame
    {
        std::map<std::string, std::string> entryAliases;
        std::map<std::string, std::string> thenAliases;
        bool sawElse = false;
        bool restoreOnElse = false;
    };
    std::vector<AliasFrame> aliasFrames;
};

std::string handleAliasKey(const std::string &token)
{
    return lowerCopy(trimCopy(token));
}

void clearHandleAlias(Mm9LuaGenerationState &state, const std::string &token)
{
    state.handleAliases.erase(handleAliasKey(token));
}

std::map<std::string, std::string> intersectHandleAliases(
    const std::map<std::string, std::string> &first,
    const std::map<std::string, std::string> &second)
{
    std::map<std::string, std::string> result;
    for (const std::pair<const std::string, std::string> &alias : first)
    {
        const auto iterator = second.find(alias.first);
        if (iterator != second.end() && iterator->second == alias.second)
        {
            result[alias.first] = alias.second;
        }
    }
    return result;
}

void applyHandleAliasMutationForCommand(Mm9LuaGenerationState &state, const Mm9ScriptLine &line)
{
    const std::string normalizedCommand = normalizeMm9ScriptCommandName(line.name);
    const std::vector<std::string> arguments =
        normalizedServiceArguments(splitScriptArguments(line.argumentsText));
    const std::string trimmedArguments = trimCopy(line.argumentsText);
    if (!trimmedArguments.empty() && trimmedArguments.front() == '=')
    {
        clearHandleAlias(state, line.name);
        return;
    }

    if (normalizedCommand == "getmyhandle" || normalizedCommand == "getplayerhandle")
    {
        size_t destinationIndex = 0;
        if (arguments.size() >= 2 && trimCopy(arguments[0]).empty())
        {
            destinationIndex = 1;
        }
        if (arguments.size() > destinationIndex && isLuaIdentifier(trimCopy(arguments[destinationIndex])))
        {
            state.handleAliases[handleAliasKey(arguments[destinationIndex])] =
                normalizedCommand == "getmyhandle" ? "self" : "player";
            return;
        }
    }

    if (normalizedCommand == "getobjecthandle" && arguments.size() >= 2)
    {
        const size_t destinationIndex = trimCopy(arguments[0]).empty() && arguments.size() >= 3 ? 2 : 1;
        clearHandleAlias(state, arguments[destinationIndex]);
        return;
    }

    if ((normalizedCommand == "set" || normalizedCommand == "add" || normalizedCommand == "sub"
        || normalizedCommand == "subtract" || normalizedCommand == "mul" || normalizedCommand == "multiply"
        || normalizedCommand == "div" || normalizedCommand == "divide") && !arguments.empty())
    {
        clearHandleAlias(state, arguments[0]);
    }
}

std::optional<std::string> luaHandleAliasExpression(
    const Mm9LuaGenerationState *pState,
    const std::string &token)
{
    if (pState == nullptr)
    {
        return std::nullopt;
    }

    const auto aliasIterator = pState->handleAliases.find(handleAliasKey(token));
    if (aliasIterator == pState->handleAliases.end())
    {
        return std::nullopt;
    }
    if (aliasIterator->second == "self")
    {
        return "ctx:self()";
    }
    if (aliasIterator->second == "player")
    {
        return "ctx:player()";
    }

    return std::nullopt;
}

bool emitNativeObjectHandleLookupIfSupported(std::ostringstream &lua, const Mm9ScriptLine &line, size_t indentDepth)
{
    if (normalizeMm9ScriptCommandName(line.name) != "getobjecthandle")
    {
        return false;
    }

    const std::vector<std::string> arguments = normalizedServiceArguments(splitScriptArguments(line.argumentsText));
    const size_t sourceIndex = arguments.size() >= 3 && trimCopy(arguments[0]).empty() ? 1 : 0;
    const size_t destinationIndex = sourceIndex + 1;
    if (arguments.size() <= destinationIndex || trimCopy(arguments[sourceIndex]).empty()
        || !isLuaIdentifier(trimCopy(arguments[destinationIndex])))
    {
        return false;
    }

    const std::string indent = luaIndent(indentDepth);
    lua << indent << luaStateField(trimCopy(arguments[destinationIndex])) << " = ctx:objectOrNil("
        << luaString(trimCopy(arguments[sourceIndex])) << ")"
        << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
    return true;
}

std::optional<std::string> luaObjectTargetExpression(
    const std::string &token,
    const Mm9LuaGenerationState *pState = nullptr)
{
    const std::string trimmed = trimCopy(token);
    if (trimmed.empty())
    {
        return std::nullopt;
    }

    const std::string lowered = lowerCopy(trimmed);
    if (lowered == "null" || lowered == "nil" || lowered == "0")
    {
        return "nil";
    }
    if (lowered == "hme" || lowered == "g_hmyobject")
    {
        return "ctx:self()";
    }
    if (lowered == "hplayer" || lowered == "g_hplayer" || lowered == "player")
    {
        return "ctx:player()";
    }
    const std::optional<std::string> aliasExpression = luaHandleAliasExpression(pState, trimmed);
    if (aliasExpression)
    {
        return aliasExpression;
    }

    return "ctx:object(" + luaString(trimmed) + ")";
}

bool emitNativeObjectIdentityIfSupported(std::ostringstream &lua, const Mm9ScriptLine &line, size_t indentDepth)
{
    const std::string normalizedCommand = normalizeMm9ScriptCommandName(line.name);
    if (normalizedCommand != "getobjectname" && normalizedCommand != "getclassname"
        && normalizedCommand != "isclass")
    {
        return false;
    }

    const std::vector<std::string> arguments = normalizedServiceArguments(splitScriptArguments(line.argumentsText));
    const std::string indent = luaIndent(indentDepth);
    if (normalizedCommand == "getobjectname" || normalizedCommand == "getclassname")
    {
        if (arguments.size() < 2 || !isLuaIdentifier(trimCopy(arguments[1])))
        {
            return false;
        }

        const std::optional<std::string> objectExpression = luaObjectTargetExpression(arguments[0]);
        if (!objectExpression || *objectExpression == "nil")
        {
            return false;
        }

        const std::string method = normalizedCommand == "getobjectname" ? "name" : "className";
        lua << indent << luaStateField(trimCopy(arguments[1])) << " = "
            << *objectExpression << ':' << method << "()"
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return true;
    }

    if (arguments.size() < 3 || trimCopy(arguments[1]).empty() || !isLuaIdentifier(trimCopy(arguments[2])))
    {
        return false;
    }

    const std::optional<std::string> objectExpression = luaObjectTargetExpression(arguments[0]);
    if (!objectExpression || *objectExpression == "nil")
    {
        return false;
    }

    lua << indent << luaStateField(trimCopy(arguments[2])) << " = "
        << *objectExpression << ":isClass(" << luaString(unquotedScriptToken(arguments[1])) << ")"
        << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
    return true;
}

bool emitNativeObjectQueryIfSupported(std::ostringstream &lua, const Mm9ScriptLine &line, size_t indentDepth)
{
    const std::string normalizedCommand = normalizeMm9ScriptCommandName(line.name);
    if (normalizedCommand != "isplayer" && normalizedCommand != "isactor" && normalizedCommand != "isai"
        && normalizedCommand != "isvisible" && normalizedCommand != "isobjectactive")
    {
        return false;
    }

    const std::vector<std::string> arguments = splitScriptArguments(line.argumentsText);
    if (arguments.size() != 2 || !isLuaIdentifier(trimCopy(arguments[1])))
    {
        return false;
    }

    const std::optional<std::string> objectExpression = luaObjectTargetExpression(arguments[0]);
    if (!objectExpression || *objectExpression == "nil")
    {
        return false;
    }

    std::string method = "isPlayer";
    if (normalizedCommand == "isactor")
    {
        method = "isActor";
    }
    else if (normalizedCommand == "isai")
    {
        method = "isAi";
    }
    else if (normalizedCommand == "isvisible")
    {
        method = "isVisible";
    }
    else if (normalizedCommand == "isobjectactive")
    {
        method = "isActive";
    }

    lua << luaIndent(indentDepth) << luaStateField(trimCopy(arguments[1])) << " = ";
    if (normalizedCommand == "isactor" || normalizedCommand == "isai")
    {
        lua << '(' << *objectExpression << ':' << method << "() and 1 or 0)";
    }
    else
    {
        lua << *objectExpression << ':' << method << "()";
    }
    lua << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
    return true;
}

bool emitNativeObjectBoundsIfSupported(std::ostringstream &lua, const Mm9ScriptLine &line, size_t indentDepth)
{
    const std::string normalizedCommand = normalizeMm9ScriptCommandName(line.name);
    if (normalizedCommand != "getdims" && normalizedCommand != "getobjectminmax")
    {
        return false;
    }

    const std::vector<std::string> arguments = splitScriptArguments(line.argumentsText);
    const size_t expectedArgumentCount = normalizedCommand == "getdims" ? 4 : 7;
    if (arguments.size() < expectedArgumentCount)
    {
        return false;
    }

    const std::optional<std::string> objectExpression = luaObjectTargetExpression(arguments[0]);
    if (!objectExpression || *objectExpression == "nil")
    {
        return false;
    }

    for (size_t index = 1; index < expectedArgumentCount; ++index)
    {
        if (!isLuaIdentifier(trimCopy(arguments[index])))
        {
            return false;
        }
    }

    const std::string method = normalizedCommand == "getdims" ? "dims" : "minMax";
    lua << luaIndent(indentDepth);
    for (size_t index = 1; index < expectedArgumentCount; ++index)
    {
        if (index != 1)
        {
            lua << ", ";
        }
        lua << luaStateField(trimCopy(arguments[index]));
    }
    lua << " = " << *objectExpression << ':' << method << "()"
        << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
    return true;
}

bool emitNativeObjectFlagIfSupported(
    std::ostringstream &lua,
    const Mm9ScriptLine &line,
    size_t indentDepth,
    const Mm9LuaGenerationState &generationState)
{
    const std::string normalizedCommand = normalizeMm9ScriptCommandName(line.name);
    if (normalizedCommand != "setflag" && normalizedCommand != "clearflag")
    {
        return false;
    }

    const std::vector<std::string> arguments = splitScriptArguments(line.argumentsText);
    if (arguments.size() < 2 || trimCopy(arguments[1]).empty())
    {
        return false;
    }

    const std::optional<std::string> objectExpression = luaObjectTargetExpression(arguments[0], &generationState);
    if (!objectExpression || *objectExpression == "nil")
    {
        return false;
    }

    lua << luaIndent(indentDepth) << *objectExpression << ":setFlag("
        << luaString(trimCopy(arguments[1])) << ", "
        << (normalizedCommand == "setflag" ? "true" : "false") << ")"
        << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
    return true;
}

bool emitNativeObjectPositionIfSupported(
    std::ostringstream &lua,
    const Mm9ScriptLine &line,
    size_t indentDepth,
    const Mm9LuaGenerationState &generationState)
{
    const std::string normalizedCommand = normalizeMm9ScriptCommandName(line.name);
    if (normalizedCommand != "getpos" && normalizedCommand != "setpos")
    {
        return false;
    }

    const std::vector<std::string> arguments =
        normalizedServiceArguments(splitScriptArguments(line.argumentsText));
    if (arguments.size() < 4)
    {
        return false;
    }

    const std::optional<std::string> objectExpression = luaObjectTargetExpression(arguments[0], &generationState);
    if (!objectExpression || *objectExpression == "nil")
    {
        return false;
    }

    const std::string indent = luaIndent(indentDepth);
    if (normalizedCommand == "getpos")
    {
        for (size_t index = 1; index <= 3; ++index)
        {
            if (!isLuaIdentifier(trimCopy(arguments[index])))
            {
                return false;
            }
        }

        lua << indent << luaStateField(trimCopy(arguments[1])) << ", "
            << luaStateField(trimCopy(arguments[2])) << ", "
            << luaStateField(trimCopy(arguments[3])) << " = "
            << *objectExpression << ":pos()"
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return true;
    }

    if (trimCopy(arguments[1]).empty() || trimCopy(arguments[2]).empty() || trimCopy(arguments[3]).empty())
    {
        return false;
    }

    lua << indent << *objectExpression << ":setPos("
        << luaRuntimeArgumentForScriptToken(arguments[1]) << ", "
        << luaRuntimeArgumentForScriptToken(arguments[2]) << ", "
        << luaRuntimeArgumentForScriptToken(arguments[3]) << ")"
        << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
    return true;
}

bool emitNativeObjectStatIfSupported(std::ostringstream &lua, const Mm9ScriptLine &line, size_t indentDepth)
{
    const std::string normalizedCommand = normalizeMm9ScriptCommandName(line.name);
    if (normalizedCommand != "getstat" && normalizedCommand != "setstat")
    {
        return false;
    }

    const std::vector<std::string> arguments = splitScriptArguments(line.argumentsText);
    if (arguments.size() != 3 || trimCopy(arguments[1]).empty())
    {
        return false;
    }

    const std::optional<std::string> objectExpression = luaObjectTargetExpression(arguments[0]);
    if (!objectExpression || *objectExpression == "nil")
    {
        return false;
    }

    const std::string indent = luaIndent(indentDepth);
    if (normalizedCommand == "getstat")
    {
        if (!isLuaIdentifier(trimCopy(arguments[2])))
        {
            return false;
        }

        lua << indent << luaStateField(trimCopy(arguments[2])) << " = "
            << *objectExpression << ":getStat(" << luaString(trimCopy(arguments[1])) << ")"
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return true;
    }

    if (trimCopy(arguments[2]).empty())
    {
        return false;
    }

    lua << indent << *objectExpression << ":setStat("
        << luaString(trimCopy(arguments[1])) << ", "
        << luaRuntimeArgumentForScriptToken(arguments[2]) << ")"
        << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
    return true;
}

bool emitNativeObjectDistanceIfSupported(std::ostringstream &lua, const Mm9ScriptLine &line, size_t indentDepth)
{
    if (normalizeMm9ScriptCommandName(line.name) != "getdistance")
    {
        return false;
    }

    const std::vector<std::string> arguments =
        normalizedServiceArguments(splitScriptArguments(line.argumentsText));
    if ((arguments.size() != 2 && arguments.size() != 3)
        || !isLuaIdentifier(trimCopy(arguments.back())))
    {
        return false;
    }

    const bool implicitSource = arguments.size() == 2;
    const std::optional<std::string> sourceExpression = implicitSource
        ? std::optional<std::string>("ctx:self()")
        : luaObjectTargetExpression(arguments[0]);
    const std::optional<std::string> targetExpression = luaObjectTargetExpression(arguments[implicitSource ? 0 : 1]);
    if (!sourceExpression || !targetExpression || *sourceExpression == "nil" || *targetExpression == "nil")
    {
        return false;
    }

    lua << luaIndent(indentDepth) << luaStateField(trimCopy(arguments.back())) << " = "
        << *sourceExpression << ":distanceTo(" << *targetExpression << ")"
        << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
    return true;
}

bool emitNativeObjectPropertyIfSupported(std::ostringstream &lua, const Mm9ScriptLine &line, size_t indentDepth)
{
    const std::string normalizedCommand = normalizeMm9ScriptCommandName(line.name);
    if (normalizedCommand != "setpropnumber" && normalizedCommand != "setpropstring"
        && normalizedCommand != "getstatstr")
    {
        return false;
    }

    const std::vector<std::string> arguments = splitScriptArguments(line.argumentsText);
    const std::string indent = luaIndent(indentDepth);
    if (normalizedCommand == "setpropnumber" || normalizedCommand == "setpropstring")
    {
        if (arguments.size() != 2 || trimCopy(arguments[0]).empty() || trimCopy(arguments[1]).empty())
        {
            return false;
        }

        const std::string method = normalizedCommand == "setpropnumber"
            ? "setNumberProperty"
            : "setStringProperty";
        lua << indent << "ctx:self():" << method << '('
            << luaString(trimCopy(arguments[0])) << ", "
            << luaRuntimeArgumentForScriptToken(arguments[1]) << ")"
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return true;
    }

    if (arguments.size() != 3 || trimCopy(arguments[1]).empty() || !isLuaIdentifier(trimCopy(arguments[2])))
    {
        return false;
    }

    const std::optional<std::string> objectExpression = luaObjectTargetExpression(arguments[0]);
    if (!objectExpression || *objectExpression == "nil")
    {
        return false;
    }

    lua << indent << luaStateField(trimCopy(arguments[2])) << " = "
        << *objectExpression << ":stringProperty(" << luaString(trimCopy(arguments[1])) << ")"
        << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
    return true;
}

bool looksLikeScriptHandleToken(const std::string &token)
{
    const std::string lowered = lowerCopy(trimCopy(token));
    return lowered == "hme" || lowered == "hplayer" || lowered == "g_hobject" ||
        lowered.rfind("g_h", 0) == 0 || lowered.rfind("h", 0) == 0;
}

bool emitNativeObjectMotionIfSupported(std::ostringstream &lua, const Mm9ScriptLine &line, size_t indentDepth)
{
    const std::string normalizedCommand = normalizeMm9ScriptCommandName(line.name);
    if (normalizedCommand != "getvelocity" && normalizedCommand != "setvelocity"
        && normalizedCommand != "getfacedir" && normalizedCommand != "facedir"
        && normalizedCommand != "getforwarddir" && normalizedCommand != "getreversedir"
        && normalizedCommand != "getrightdir" && normalizedCommand != "getleftdir")
    {
        return false;
    }

    const std::vector<std::string> arguments = normalizedServiceArguments(splitScriptArguments(line.argumentsText));
    const std::string indent = luaIndent(indentDepth);
    if (normalizedCommand == "getforwarddir" || normalizedCommand == "getreversedir"
        || normalizedCommand == "getrightdir" || normalizedCommand == "getleftdir")
    {
        if (arguments.size() != 3 && arguments.size() != 4)
        {
            return false;
        }

        const size_t destinationOffset = arguments.size() == 4 ? 1 : 0;
        const std::optional<std::string> objectExpression = arguments.size() == 4
            ? luaObjectTargetExpression(arguments[0])
            : std::optional<std::string>("ctx:self()");
        if (!objectExpression || *objectExpression == "nil")
        {
            return false;
        }

        for (size_t index = destinationOffset; index < arguments.size(); ++index)
        {
            if (!isLuaIdentifier(trimCopy(arguments[index])))
            {
                return false;
            }
        }

        std::string method = "forwardDir";
        if (normalizedCommand == "getreversedir")
        {
            method = "reverseDir";
        }
        else if (normalizedCommand == "getrightdir")
        {
            method = "rightDir";
        }
        else if (normalizedCommand == "getleftdir")
        {
            method = "leftDir";
        }

        lua << indent << luaStateField(trimCopy(arguments[destinationOffset])) << ", "
            << luaStateField(trimCopy(arguments[destinationOffset + 1])) << ", "
            << luaStateField(trimCopy(arguments[destinationOffset + 2])) << " = "
            << *objectExpression << ':' << method << "()"
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return true;
    }

    if (normalizedCommand == "getvelocity" || normalizedCommand == "getfacedir")
    {
        if (arguments.size() < 4)
        {
            return false;
        }

        const std::optional<std::string> objectExpression = luaObjectTargetExpression(arguments[0]);
        if (!objectExpression || *objectExpression == "nil")
        {
            return false;
        }

        for (size_t index = 1; index < arguments.size(); ++index)
        {
            if (!isLuaIdentifier(trimCopy(arguments[index])))
            {
                return false;
            }
        }

        const std::string method = normalizedCommand == "getvelocity" ? "velocity" : "rotation";
        lua << indent << luaStateField(trimCopy(arguments[1])) << ", "
            << luaStateField(trimCopy(arguments[2])) << ", "
            << luaStateField(trimCopy(arguments[3])) << " = "
            << *objectExpression << ':' << method << "()"
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return true;
    }

    if (normalizedCommand == "setvelocity")
    {
        if (arguments.size() != 4)
        {
            return false;
        }

        const std::optional<std::string> objectExpression = luaObjectTargetExpression(arguments[0]);
        if (!objectExpression || *objectExpression == "nil")
        {
            return false;
        }

        lua << indent << *objectExpression << ":setVelocity("
            << luaRuntimeArgumentForScriptToken(arguments[1]) << ", "
            << luaRuntimeArgumentForScriptToken(arguments[2]) << ", "
            << luaRuntimeArgumentForScriptToken(arguments[3]) << ")"
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return true;
    }

    if (arguments.size() < 3 || arguments.size() > 5)
    {
        return false;
    }

    if (arguments.size() >= 4 && looksLikeScriptHandleToken(arguments[0]))
    {
        return false;
    }

    lua << indent << "ctx:self():faceDir("
        << luaRuntimeArgumentForScriptToken(arguments[0]) << ", "
        << luaRuntimeArgumentForScriptToken(arguments[1]) << ", "
        << luaRuntimeArgumentForScriptToken(arguments[2]);
    for (size_t index = 3; index < arguments.size(); ++index)
    {
        lua << ", " << luaRuntimeArgumentForScriptToken(arguments[index]);
    }
    lua << ")"
        << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
    return true;
}

bool emitNativeObjectTargetIfSupported(std::ostringstream &lua, const Mm9ScriptLine &line, size_t indentDepth)
{
    const std::string normalizedCommand = normalizeMm9ScriptCommandName(line.name);
    if (normalizedCommand != "target" && normalizedCommand != "gettarget" && normalizedCommand != "getobjecttarget")
    {
        return false;
    }

    const std::vector<std::string> arguments = splitScriptArguments(line.argumentsText);
    const std::string indent = luaIndent(indentDepth);
    if (normalizedCommand == "target")
    {
        if (arguments.empty())
        {
            return false;
        }

        const std::optional<std::string> targetExpression = luaObjectTargetExpression(arguments[0]);
        if (!targetExpression)
        {
            return false;
        }

        lua << indent << "ctx:self():setTarget(" << *targetExpression << ")"
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return true;
    }

    if (normalizedCommand == "gettarget")
    {
        if (arguments.empty() || !isLuaIdentifier(trimCopy(arguments[0])))
        {
            return false;
        }

        lua << indent << luaStateField(trimCopy(arguments[0])) << " = ctx:self():target()"
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return true;
    }

    if (arguments.size() < 2 || !isLuaIdentifier(trimCopy(arguments[1])))
    {
        return false;
    }

    const std::optional<std::string> sourceExpression = luaObjectTargetExpression(arguments[0]);
    if (!sourceExpression || *sourceExpression == "nil")
    {
        return false;
    }

    lua << indent << luaStateField(trimCopy(arguments[1])) << " = "
        << *sourceExpression << ":target()"
        << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
    return true;
}

bool emitNativeObjectLinkIfSupported(std::ostringstream &lua, const Mm9ScriptLine &line, size_t indentDepth)
{
    const std::string normalizedCommand = normalizeMm9ScriptCommandName(line.name);
    if (normalizedCommand != "createobjectlink" && normalizedCommand != "breakobjectlink")
    {
        return false;
    }

    const std::vector<std::string> arguments = splitScriptArguments(line.argumentsText);
    if (arguments.empty())
    {
        return false;
    }

    const std::optional<std::string> linkedExpression = luaObjectTargetExpression(arguments[0]);
    if (!linkedExpression)
    {
        return false;
    }

    const std::string method = normalizedCommand == "createobjectlink" ? "link" : "unlink";
    lua << luaIndent(indentDepth) << "ctx:self():" << method << '(' << *linkedExpression << ")"
        << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
    return true;
}

bool emitNativeObjectLifetimeIfSupported(std::ostringstream &lua, const Mm9ScriptLine &line, size_t indentDepth)
{
    if (normalizeMm9ScriptCommandName(line.name) != "removeobject")
    {
        return false;
    }

    const std::vector<std::string> arguments = splitScriptArguments(line.argumentsText);
    std::string objectExpression = "ctx:self()";
    if (!arguments.empty())
    {
        const std::optional<std::string> candidate = luaObjectTargetExpression(arguments[0]);
        if (!candidate || *candidate == "nil")
        {
            return false;
        }
        objectExpression = *candidate;
    }

    lua << luaIndent(indentDepth) << objectExpression << ":remove()"
        << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
    return true;
}

bool emitNativeObjectRegistryQueryIfSupported(std::ostringstream &lua, const Mm9ScriptLine &line, size_t indentDepth)
{
    const std::string normalizedCommand = normalizeMm9ScriptCommandName(line.name);
    if (normalizedCommand != "getobjects" && normalizedCommand != "getliquidcontainer"
        && normalizedCommand != "getcontainer")
    {
        return false;
    }

    const std::vector<std::string> arguments = normalizedServiceArguments(splitScriptArguments(line.argumentsText));
    if (normalizedCommand == "getliquidcontainer")
    {
        if (arguments.size() < 2 || !isLuaIdentifier(trimCopy(arguments[1])))
        {
            return false;
        }

        const std::optional<std::string> objectExpression = luaObjectTargetExpression(arguments[0]);
        if (!objectExpression || *objectExpression == "nil")
        {
            return false;
        }

        lua << luaIndent(indentDepth) << luaStateField(trimCopy(arguments[1])) << " = "
            << *objectExpression << ":liquidContainer()"
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return true;
    }

    if (normalizedCommand == "getcontainer")
    {
        if (arguments.size() < 3 || !isLuaIdentifier(trimCopy(arguments[2])))
        {
            return false;
        }

        const std::optional<std::string> objectExpression = luaObjectTargetExpression(arguments[0]);
        if (!objectExpression || *objectExpression == "nil")
        {
            return false;
        }

        lua << luaIndent(indentDepth) << luaStateField(trimCopy(arguments[2])) << " = "
            << *objectExpression << ":container(" << luaRuntimeArgumentForScriptToken(arguments[1]) << ")"
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return true;
    }

    if (arguments.size() != 5 || trimCopy(arguments[0]).empty() || trimCopy(arguments[1]).empty()
        || trimCopy(arguments[2]).empty() || !isLuaIdentifier(trimCopy(arguments[3]))
        || !isLuaIdentifier(trimCopy(arguments[4])))
    {
        return false;
    }

    lua << luaIndent(indentDepth) << "ctx:getObjects("
        << luaRuntimeArgumentForScriptToken(arguments[0]) << ", "
        << luaRuntimeArgumentForScriptToken(arguments[1]) << ", "
        << luaRuntimeArgumentForScriptToken(arguments[2]) << ", "
        << luaString(trimCopy(arguments[3])) << ", "
        << luaString(trimCopy(arguments[4])) << ")"
        << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
    return true;
}

bool emitNativeArrayAccessIfSupported(std::ostringstream &lua, const Mm9ScriptLine &line, size_t indentDepth)
{
    const std::string normalizedCommand = normalizeMm9ScriptCommandName(line.name);
    if (normalizedCommand != "arrayput" && normalizedCommand != "arrayget")
    {
        return false;
    }

    std::vector<std::string> arguments = splitScriptArguments(line.argumentsText);
    if (arguments.size() == 2)
    {
        const std::string arrayName = firstArgumentToken(arguments[0]);
        const std::string indexExpression = trimCopy(restAfterFirstToken(arguments[0]));
        if (!arrayName.empty() && !indexExpression.empty())
        {
            arguments = { arrayName, indexExpression, arguments[1] };
        }
    }

    if (arguments.size() != 3 || trimCopy(arguments[0]).empty() || trimCopy(arguments[1]).empty())
    {
        return false;
    }

    const std::string method = normalizedCommand == "arrayput" ? "arrayPut" : "arrayGet";
    if (normalizedCommand == "arrayget" && !isLuaIdentifier(trimCopy(arguments[2])))
    {
        return false;
    }
    if (normalizedCommand == "arrayput" && trimCopy(arguments[2]).empty())
    {
        return false;
    }

    lua << luaIndent(indentDepth) << "ctx:" << method << '('
        << luaString(trimCopy(arguments[0])) << ", "
        << luaRuntimeArgumentForScriptToken(arguments[1]) << ", ";
    if (normalizedCommand == "arrayget")
    {
        lua << luaString(trimCopy(arguments[2]));
    }
    else
    {
        lua << luaRuntimeArgumentForScriptToken(arguments[2]);
    }
    lua << ")"
        << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
    return true;
}

bool emitNativeRuntimeUtilityIfSupported(std::ostringstream &lua, const Mm9ScriptLine &line, size_t indentDepth)
{
    const std::string normalizedCommand = normalizeMm9ScriptCommandName(line.name);
    if (normalizedCommand != "getrandomint" && normalizedCommand != "getrandomfloat" && normalizedCommand != "gettime"
        && normalizedCommand != "debugout" && normalizedCommand != "cprint" && normalizedCommand != "getpcvoice"
        && normalizedCommand != "getgametime" && normalizedCommand != "setparam" && normalizedCommand != "savepath"
        && normalizedCommand != "restorepath" && normalizedCommand != "castray"
        && normalizedCommand != "getplayerid" && normalizedCommand != "getplayernbr"
        && normalizedCommand != "getplayerswithindist" && normalizedCommand != "consolecommand"
        && normalizedCommand != "dohighscore" && normalizedCommand != "clearcondition"
        && normalizedCommand != "setcondition" && normalizedCommand != "sin" && normalizedCommand != "cos"
        && normalizedCommand != "getangletopos" && normalizedCommand != "getrotation"
        && normalizedCommand != "setrotation" && normalizedCommand != "calcrotationrate"
        && normalizedCommand != "checkworldcollision")
    {
        return false;
    }

    std::vector<std::string> arguments = normalizedServiceArguments(splitScriptArguments(line.argumentsText));
    if (normalizedCommand == "debugout" || normalizedCommand == "cprint")
    {
        lua << luaIndent(indentDepth) << "ctx:" << (normalizedCommand == "debugout" ? "debugOut" : "cprint") << '(';
        for (size_t index = 0; index < arguments.size(); ++index)
        {
            if (index != 0)
            {
                lua << ", ";
            }
            lua << luaRuntimeArgumentForScriptToken(arguments[index]);
        }
        lua << ")"
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return true;
    }

    if (normalizedCommand == "consolecommand" || normalizedCommand == "dohighscore"
        || normalizedCommand == "clearcondition" || normalizedCommand == "setcondition")
    {
        std::string method;
        if (normalizedCommand == "consolecommand")
        {
            method = "consoleCommand";
        }
        else if (normalizedCommand == "dohighscore")
        {
            method = "doHighScore";
        }
        else if (normalizedCommand == "clearcondition")
        {
            method = "clearCondition";
        }
        else
        {
            method = "setCondition";
        }

        lua << luaIndent(indentDepth) << "ctx:" << method << '(';
        for (size_t index = 0; index < arguments.size(); ++index)
        {
            if (index != 0)
            {
                lua << ", ";
            }
            lua << luaRuntimeArgumentForScriptToken(arguments[index]);
        }
        lua << ")"
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return true;
    }

    if (normalizedCommand == "sin" || normalizedCommand == "cos")
    {
        if (arguments.size() != 2 || !isLuaIdentifier(trimCopy(arguments[1])))
        {
            return false;
        }

        lua << luaIndent(indentDepth) << "ctx:" << normalizedCommand << '('
            << luaRuntimeArgumentForScriptToken(arguments[0]) << ", "
            << luaString(trimCopy(arguments[1])) << ")"
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return true;
    }

    if (normalizedCommand == "getangletopos")
    {
        if (arguments.size() != 4 || !isLuaIdentifier(trimCopy(arguments[3])))
        {
            return false;
        }

        lua << luaIndent(indentDepth) << "ctx:getAngleToPos("
            << luaRuntimeArgumentForScriptToken(arguments[0]) << ", "
            << luaRuntimeArgumentForScriptToken(arguments[1]) << ", "
            << luaRuntimeArgumentForScriptToken(arguments[2]) << ", "
            << luaString(trimCopy(arguments[3])) << ")"
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return true;
    }

    if (normalizedCommand == "getrotation")
    {
        if (arguments.size() != 5 || !isLuaIdentifier(trimCopy(arguments[1]))
            || !isLuaIdentifier(trimCopy(arguments[2])) || !isLuaIdentifier(trimCopy(arguments[3]))
            || !isLuaIdentifier(trimCopy(arguments[4])))
        {
            return false;
        }

        const std::optional<std::string> objectExpression = luaObjectTargetExpression(arguments[0]);
        if (!objectExpression || *objectExpression == "nil")
        {
            return false;
        }

        lua << luaIndent(indentDepth) << "ctx:getRotation(" << *objectExpression << ", "
            << luaString(trimCopy(arguments[1])) << ", " << luaString(trimCopy(arguments[2])) << ", "
            << luaString(trimCopy(arguments[3])) << ", " << luaString(trimCopy(arguments[4])) << ")"
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return true;
    }

    if (normalizedCommand == "setrotation")
    {
        if (arguments.size() < 3)
        {
            return false;
        }

        lua << luaIndent(indentDepth) << "ctx:setRotation(";
        for (size_t index = 0; index < arguments.size(); ++index)
        {
            if (index != 0)
            {
                lua << ", ";
            }

            const std::optional<std::string> objectExpression = index == 0 && looksLikeScriptHandleToken(arguments[0])
                ? luaObjectTargetExpression(arguments[0])
                : std::nullopt;
            lua << (objectExpression && *objectExpression != "nil"
                ? *objectExpression
                : luaRuntimeArgumentForScriptToken(arguments[index]));
        }
        lua << ")"
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return true;
    }

    if (normalizedCommand == "calcrotationrate")
    {
        if (arguments.size() != 3 || !isLuaIdentifier(trimCopy(arguments[2])))
        {
            return false;
        }

        const std::optional<std::string> objectExpression = luaObjectTargetExpression(arguments[0]);
        if (!objectExpression || *objectExpression == "nil")
        {
            return false;
        }

        lua << luaIndent(indentDepth) << "ctx:calcRotationRate(" << *objectExpression << ", "
            << luaRuntimeArgumentForScriptToken(arguments[1]) << ", " << luaString(trimCopy(arguments[2])) << ")"
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return true;
    }

    if (normalizedCommand == "checkworldcollision")
    {
        if (arguments.size() != 8 || !isLuaIdentifier(trimCopy(arguments[3]))
            || !isLuaIdentifier(trimCopy(arguments[4])) || !isLuaIdentifier(trimCopy(arguments[5]))
            || !isLuaIdentifier(trimCopy(arguments[6])) || !isLuaIdentifier(trimCopy(arguments[7])))
        {
            return false;
        }

        lua << luaIndent(indentDepth) << "ctx:checkWorldCollision(";
        for (size_t index = 0; index < arguments.size(); ++index)
        {
            if (index != 0)
            {
                lua << ", ";
            }
            if (index >= 3)
            {
                lua << luaString(trimCopy(arguments[index]));
            }
            else
            {
                lua << luaRuntimeArgumentForScriptToken(arguments[index]);
            }
        }
        lua << ")"
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return true;
    }

    if (normalizedCommand == "restorepath")
    {
        lua << luaIndent(indentDepth) << "ctx:restorePath()"
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return true;
    }

    if (normalizedCommand == "savepath")
    {
        lua << luaIndent(indentDepth) << "ctx:savePath()"
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return true;
    }

    if (normalizedCommand == "castray")
    {
        if (arguments.size() < 6 || !isLuaIdentifier(trimCopy(arguments[4]))
            || !isLuaIdentifier(trimCopy(arguments[5])))
        {
            return false;
        }

        lua << luaIndent(indentDepth) << "ctx:castRay(";
        for (size_t index = 0; index < arguments.size(); ++index)
        {
            if (index != 0)
            {
                lua << ", ";
            }
            if (index >= 4)
            {
                lua << luaString(trimCopy(arguments[index]));
            }
            else
            {
                lua << luaRuntimeArgumentForScriptToken(arguments[index]);
            }
        }
        lua << ")"
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return true;
    }

    if (normalizedCommand == "getplayerid" || normalizedCommand == "getplayernbr")
    {
        if (arguments.size() != 2 || !isLuaIdentifier(trimCopy(arguments[1])))
        {
            return false;
        }

        const std::optional<std::string> objectExpression = luaObjectTargetExpression(arguments[0]);
        if (!objectExpression || *objectExpression == "nil")
        {
            return false;
        }

        lua << luaIndent(indentDepth) << "ctx:"
            << (normalizedCommand == "getplayerid" ? "getPlayerId" : "getPlayerNumber")
            << '(' << *objectExpression << ", " << luaString(trimCopy(arguments[1])) << ")"
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return true;
    }

    if (normalizedCommand == "getplayerswithindist")
    {
        if (arguments.size() != 7 || !isLuaIdentifier(trimCopy(arguments[4]))
            || !isLuaIdentifier(trimCopy(arguments[6])))
        {
            return false;
        }

        lua << luaIndent(indentDepth) << "ctx:getPlayersWithinDist(";
        for (size_t index = 0; index < arguments.size(); ++index)
        {
            if (index != 0)
            {
                lua << ", ";
            }
            if (index == 4 || index == 6)
            {
                lua << luaString(trimCopy(arguments[index]));
            }
            else
            {
                lua << luaRuntimeArgumentForScriptToken(arguments[index]);
            }
        }
        lua << ")"
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return true;
    }

    if ((normalizedCommand == "getrandomint" || normalizedCommand == "getrandomfloat") && arguments.size() == 2)
    {
        const std::string maxExpression = firstArgumentToken(arguments[1]);
        const std::string destinationName = trimCopy(restAfterFirstToken(arguments[1]));
        if (!maxExpression.empty() && !destinationName.empty())
        {
            arguments = { arguments[0], maxExpression, destinationName };
        }
    }

    if (normalizedCommand == "gettime")
    {
        if (arguments.size() != 1 || !isLuaIdentifier(trimCopy(arguments[0])))
        {
            return false;
        }

        lua << luaIndent(indentDepth) << "ctx:getTime(" << luaString(trimCopy(arguments[0])) << ")"
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return true;
    }

    if (normalizedCommand == "getpcvoice")
    {
        if (arguments.size() != 1 || !isLuaIdentifier(trimCopy(arguments[0])))
        {
            return false;
        }

        lua << luaIndent(indentDepth) << "ctx:getPcVoice(" << luaString(trimCopy(arguments[0])) << ")"
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return true;
    }

    if (normalizedCommand == "getgametime")
    {
        if (arguments.size() != 2 || !isLuaIdentifier(trimCopy(arguments[0]))
            || !isLuaIdentifier(trimCopy(arguments[1])))
        {
            return false;
        }

        lua << luaIndent(indentDepth) << "ctx:getGameTime("
            << luaString(trimCopy(arguments[0])) << ", " << luaString(trimCopy(arguments[1])) << ")"
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return true;
    }

    if (normalizedCommand == "setparam")
    {
        if (arguments.size() < 2)
        {
            return false;
        }

        lua << luaIndent(indentDepth) << "ctx:setParam(";
        for (size_t index = 0; index < arguments.size(); ++index)
        {
            if (index != 0)
            {
                lua << ", ";
            }
            lua << luaRuntimeArgumentForScriptToken(arguments[index]);
        }
        lua << ")"
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return true;
    }

    if (arguments.size() != 3 || trimCopy(arguments[0]).empty() || trimCopy(arguments[1]).empty()
        || !isLuaIdentifier(trimCopy(arguments[2])))
    {
        return false;
    }

    const std::string method = normalizedCommand == "getrandomint" ? "randomInt" : "randomFloat";
    lua << luaIndent(indentDepth) << "ctx:" << method << '('
        << luaRuntimeArgumentForScriptToken(arguments[0]) << ", "
        << luaRuntimeArgumentForScriptToken(arguments[1]) << ", "
        << luaString(trimCopy(arguments[2])) << ")"
        << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
    return true;
}

bool emitNativePartyScriptServiceIfSupported(std::ostringstream &lua, const Mm9ScriptLine &line, size_t indentDepth)
{
    const std::string normalizedCommand = normalizeMm9ScriptCommandName(line.name);
    std::string method;
    if (normalizedCommand == "hasgold")
    {
        method = "hasGold";
    }
    else if (normalizedCommand == "takegold")
    {
        method = "takeGold";
    }
    else if (normalizedCommand == "givepromo")
    {
        method = "givePromo";
    }
    else if (normalizedCommand == "getattribute")
    {
        method = "getAttribute";
    }
    else if (normalizedCommand == "getpclevel")
    {
        method = "getPcLevel";
    }
    else if (normalizedCommand == "heal")
    {
        method = "heal";
    }
    else if (normalizedCommand == "addnpc")
    {
        method = "addNpc";
    }
    else if (normalizedCommand == "removenpc")
    {
        method = "removeNpc";
    }
    else if (normalizedCommand == "giveattribute")
    {
        method = "giveAttribute";
    }
    else if (normalizedCommand == "cachescript")
    {
        method = "cacheScript";
    }
    else if (normalizedCommand == "runscript")
    {
        method = "runScript";
    }
    else
    {
        return false;
    }

    const std::vector<std::string> arguments = normalizedServiceArguments(splitScriptArguments(line.argumentsText));
    if ((normalizedCommand == "takegold" || normalizedCommand == "cachescript" || normalizedCommand == "runscript")
        && arguments.empty())
    {
        return false;
    }
    if ((normalizedCommand == "addnpc" || normalizedCommand == "removenpc") && arguments.empty())
    {
        return false;
    }
    if ((normalizedCommand == "hasgold" || normalizedCommand == "givepromo" || normalizedCommand == "getattribute")
        && arguments.size() < 2)
    {
        return false;
    }
    if (normalizedCommand == "getpclevel" && arguments.size() < 2)
    {
        return false;
    }
    if (normalizedCommand == "heal")
    {
        if (arguments.size() < 2)
        {
            return false;
        }

        const std::optional<std::string> targetExpression = luaObjectTargetExpression(arguments[0]);
        if (!targetExpression || *targetExpression == "nil")
        {
            return false;
        }

        lua << luaIndent(indentDepth) << "ctx:heal(" << *targetExpression;
        for (size_t index = 1; index < arguments.size(); ++index)
        {
            lua << ", " << luaRuntimeArgumentForScriptToken(arguments[index]);
        }
        lua << ")"
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return true;
    }
    if (normalizedCommand == "giveattribute" && arguments.size() < 3)
    {
        return false;
    }

    lua << luaIndent(indentDepth) << "ctx:" << method << '(';
    for (size_t index = 0; index < arguments.size(); ++index)
    {
        if (index != 0)
        {
            lua << ", ";
        }
        lua << luaRuntimeArgumentForScriptToken(arguments[index]);
    }
    lua << ")"
        << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
    return true;
}

bool emitNativeStateCommandIfSupported(std::ostringstream &lua, const Mm9ScriptLine &line, size_t indentDepth)
{
    const std::string normalizedCommand = normalizeMm9ScriptCommandName(line.name);
    const std::string trimmedArguments = trimCopy(line.argumentsText);
    if (!trimmedArguments.empty() && trimmedArguments.front() == '=')
    {
        const std::string target = trimCopy(line.name);
        const std::string expression = trimCopy(trimmedArguments.substr(1));
        if (!isLuaIdentifier(target) || expression.empty())
        {
            return false;
        }

        lua << luaIndent(indentDepth) << "ctx:set("
            << luaString(target) << ", "
            << luaRuntimeArgumentForScriptToken(expression) << ")"
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return true;
    }

    if (normalizedCommand == "set")
    {
        const std::optional<std::pair<std::string, std::string>> assignment =
            simpleSetAssignment(line.argumentsText);
        if (!assignment || trimCopy(assignment->first).empty() || trimCopy(assignment->second).empty())
        {
            return false;
        }

        lua << luaIndent(indentDepth) << "ctx:set("
            << luaString(trimCopy(assignment->first)) << ", "
            << luaRuntimeArgumentForScriptToken(assignment->second) << ")"
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return true;
    }

    if (normalizedCommand != "add" && normalizedCommand != "sub" && normalizedCommand != "subtract"
        && normalizedCommand != "mul" && normalizedCommand != "multiply" && normalizedCommand != "div"
        && normalizedCommand != "divide" && normalizedCommand != "mod")
    {
        return false;
    }

    const std::vector<std::string> arguments = splitScriptArguments(line.argumentsText);
    if (arguments.size() != 2 || trimCopy(arguments[0]).empty() || trimCopy(arguments[1]).empty())
    {
        return false;
    }

    std::string method = normalizedCommand;
    if (method == "subtract")
    {
        method = "sub";
    }
    else if (method == "multiply")
    {
        method = "mul";
    }
    else if (method == "divide")
    {
        method = "div";
    }

    lua << luaIndent(indentDepth) << "ctx:" << method << '('
        << luaString(trimCopy(arguments[0])) << ", "
        << luaRuntimeArgumentForScriptToken(arguments[1]) << ")"
        << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
    return true;
}

bool emitNativeWaitIfSupported(std::ostringstream &lua, const Mm9ScriptLine &line, size_t indentDepth)
{
    if (normalizeMm9ScriptCommandName(line.name) != "wait")
    {
        return false;
    }

    std::vector<std::string> arguments = splitScriptArguments(line.argumentsText);
    if (arguments.size() == 2)
    {
        const std::vector<std::string> firstArguments = splitWhitespaceScriptArguments(arguments[0]);
        if (firstArguments.size() == 2)
        {
            arguments = { firstArguments[0], firstArguments[1], arguments[1] };
        }
        else
        {
            const std::vector<std::string> secondArguments = splitWhitespaceScriptArguments(arguments[1]);
            if (secondArguments.size() == 2)
            {
                arguments = { arguments[0], secondArguments[0], secondArguments[1] };
            }
            else
            {
                arguments = { arguments[0], arguments[0], arguments[1] };
            }
        }
    }

    if (arguments.size() != 3 || trimCopy(arguments[0]).empty() || trimCopy(arguments[1]).empty()
        || trimCopy(arguments[2]).empty())
    {
        return false;
    }

    lua << luaIndent(indentDepth) << "ctx:wait("
        << luaRuntimeArgumentForScriptToken(arguments[0]) << ", "
        << luaRuntimeArgumentForScriptToken(arguments[1]) << ", "
        << luaString(trimCopy(arguments[2])) << ")"
        << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
    return true;
}

struct Mm9LuaAtTimeArguments
{
    bool valid = false;
    std::string hour;
    std::string minute;
    std::vector<std::string> labels;
};

Mm9LuaAtTimeArguments parseLuaAtTimeArguments(const std::string &argumentsText)
{
    const std::vector<std::string> arguments = splitScriptArguments(argumentsText);
    Mm9LuaAtTimeArguments result = {};
    if (arguments.empty())
    {
        return result;
    }

    size_t labelOffset = 0;
    bool labelsStartInFirstArgument = false;
    if (arguments.size() >= 3 && trimCopy(arguments[1]) == ":")
    {
        result.hour = trimCopy(arguments[0]);
        result.minute = trimCopy(arguments[2]);
        labelOffset = 3;
        result.valid = true;
    }
    else
    {
        const std::vector<std::string> firstTokens = splitWhitespaceScriptArguments(arguments[0]);
        const size_t colon = arguments[0].find(':');
        if (firstTokens.size() >= 3 && firstTokens[1] == ":")
        {
            result.hour = trimCopy(firstTokens[0]);
            result.minute = trimCopy(firstTokens[2]);
            labelOffset = 3;
            labelsStartInFirstArgument = true;
            result.valid = true;
        }
        else if (colon != std::string::npos)
        {
            result.hour = trimCopy(arguments[0].substr(0, colon));
            result.minute = trimCopy(arguments[0].substr(colon + 1));
            labelOffset = 1;
            labelsStartInFirstArgument = true;
            result.valid = true;
        }
        else if (firstTokens.size() >= 2 && !firstTokens[1].empty() && firstTokens[1].front() == ':')
        {
            result.hour = trimCopy(firstTokens[0]);
            result.minute = trimCopy(firstTokens[1].substr(1));
            labelOffset = 2;
            labelsStartInFirstArgument = true;
            result.valid = true;
        }
    }

    result.valid = result.valid && !result.hour.empty() && !result.minute.empty();
    if (!result.valid)
    {
        return result;
    }

    if (labelsStartInFirstArgument)
    {
        const std::vector<std::string> firstTokens = splitWhitespaceScriptArguments(arguments[0]);
        if (labelOffset < firstTokens.size())
        {
            result.labels.insert(result.labels.end(), firstTokens.begin() + static_cast<ptrdiff_t>(labelOffset),
                firstTokens.end());
        }
    }

    const size_t firstLabelArgument = labelsStartInFirstArgument ? 1 : labelOffset;
    for (size_t index = firstLabelArgument; index < arguments.size(); ++index)
    {
        const std::vector<std::string> tokens = splitWhitespaceScriptArguments(arguments[index]);
        result.labels.insert(result.labels.end(), tokens.begin(), tokens.end());
    }
    return result;
}

bool emitNativeAtTimeIfSupported(std::ostringstream &lua, const Mm9ScriptLine &line, size_t indentDepth)
{
    if (normalizeMm9ScriptCommandName(line.name) != "@m")
    {
        return false;
    }

    const Mm9LuaAtTimeArguments arguments = parseLuaAtTimeArguments(line.argumentsText);
    if (!arguments.valid)
    {
        return false;
    }

    lua << luaIndent(indentDepth) << "ctx:atTime("
        << luaRuntimeArgumentForScheduleToken(arguments.hour) << ", "
        << luaRuntimeArgumentForScheduleToken(arguments.minute);
    for (const std::string &label : arguments.labels)
    {
        lua << ", " << luaString(unquotedScriptToken(label));
    }
    lua << ")"
        << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
    return true;
}

bool emitNativeAudioServiceIfSupported(std::ostringstream &lua, const Mm9ScriptLine &line, size_t indentDepth)
{
    const std::string normalizedCommand = normalizeMm9ScriptCommandName(line.name);
    std::string method;
    if (normalizedCommand == "cachesound")
    {
        method = "cacheSound";
    }
    else if (normalizedCommand == "playsound")
    {
        method = "playSound";
    }
    else if (normalizedCommand == "playsoundhandle")
    {
        method = "playSoundHandle";
    }
    else if (normalizedCommand == "killsound")
    {
        method = "killSound";
    }
    else if (normalizedCommand == "getsoundduration")
    {
        method = "getSoundDuration";
    }
    else if (normalizedCommand == "issounddone")
    {
        method = "isSoundDone";
    }
    else if (normalizedCommand == "speak")
    {
        method = "speak";
    }
    else
    {
        return false;
    }

    const std::vector<std::string> arguments = splitScriptArguments(line.argumentsText);
    if (arguments.empty())
    {
        return false;
    }
    if ((normalizedCommand == "playsoundhandle" || normalizedCommand == "issounddone") && arguments.size() < 2)
    {
        return false;
    }
    if (normalizedCommand == "getsoundduration" && arguments.size() < 3)
    {
        return false;
    }

    lua << luaIndent(indentDepth) << "ctx:" << method << '(';
    for (size_t index = 0; index < arguments.size(); ++index)
    {
        if (index != 0)
        {
            lua << ", ";
        }
        lua << luaRuntimeArgumentForScriptToken(arguments[index]);
    }
    lua << ")"
        << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
    return true;
}

bool emitNativeAnimationServiceIfSupported(std::ostringstream &lua, const Mm9ScriptLine &line, size_t indentDepth)
{
    const std::string normalizedCommand = normalizeMm9ScriptCommandName(line.name);
    std::string method;
    if (normalizedCommand == "playanim")
    {
        method = "playAnimation";
    }
    else if (normalizedCommand == "playanimation")
    {
        method = "playAnimationCommand";
    }
    else if (normalizedCommand == "loopanim")
    {
        method = "loopAnimation";
    }
    else if (normalizedCommand == "blendanim")
    {
        method = "blendAnimation";
    }
    else if (normalizedCommand == "getcurranim")
    {
        method = "getCurrentAnimation";
    }
    else if (normalizedCommand == "getanimname")
    {
        method = "getAnimationName";
    }
    else if (normalizedCommand == "getanimnbr")
    {
        method = "getAnimationNumber";
    }
    else if (normalizedCommand == "playanimsound")
    {
        method = "playAnimSound";
    }
    else if (normalizedCommand == "setanimplaying")
    {
        method = "setAnimationPlaying";
    }
    else
    {
        return false;
    }

    std::vector<std::string> arguments = normalizedServiceArguments(splitScriptArguments(line.argumentsText));
    if (normalizedCommand == "loopanim" && arguments.size() == 2)
    {
        const std::vector<std::string> secondArguments = splitWhitespaceScriptArguments(arguments[1]);
        if (secondArguments.size() == 2)
        {
            arguments = { arguments[0], secondArguments[0], secondArguments[1] };
        }
    }
    if (arguments.empty())
    {
        return false;
    }

    std::string objectExpression = "ctx:self()";
    if (normalizedCommand == "getcurranim" || normalizedCommand == "getanimname" || normalizedCommand == "getanimnbr")
    {
        const size_t minimumArguments = normalizedCommand == "getcurranim" ? 2 : 3;
        if (arguments.size() < minimumArguments)
        {
            return false;
        }

        const std::optional<std::string> targetExpression = luaObjectTargetExpression(arguments[0]);
        if (!targetExpression || *targetExpression == "nil")
        {
            return false;
        }
        objectExpression = *targetExpression;
        arguments.erase(arguments.begin());
    }

    lua << luaIndent(indentDepth) << objectExpression << ':' << method << '(';
    for (size_t index = 0; index < arguments.size(); ++index)
    {
        if (index != 0)
        {
            lua << ", ";
        }
        lua << luaRuntimeArgumentForScriptToken(arguments[index]);
    }
    lua << ")"
        << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
    return true;
}

bool emitNativeClientFxServiceIfSupported(std::ostringstream &lua, const Mm9ScriptLine &line, size_t indentDepth)
{
    const std::string normalizedCommand = normalizeMm9ScriptCommandName(line.name);
    const std::vector<std::string> arguments = splitScriptArguments(line.argumentsText);
    if (normalizedCommand == "cacheclientfx")
    {
        if (arguments.empty())
        {
            return false;
        }

        lua << luaIndent(indentDepth) << "ctx:cacheClientFx("
            << luaRuntimeArgumentForScriptToken(arguments[0]) << ")"
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return true;
    }

    if (normalizedCommand != "doclientfx" && normalizedCommand != "createfx")
    {
        return false;
    }
    if (arguments.size() < 2)
    {
        return false;
    }

    const size_t objectArgumentIndex = normalizedCommand == "createfx" ? 1 : 0;
    const size_t effectArgumentIndex = normalizedCommand == "createfx" ? 0 : 1;
    const std::optional<std::string> objectExpression = luaObjectTargetExpression(arguments[objectArgumentIndex]);
    if (!objectExpression || *objectExpression == "nil")
    {
        return false;
    }

    lua << luaIndent(indentDepth) << *objectExpression
        << (normalizedCommand == "createfx" ? ":createFx(" : ":doClientFx(")
        << luaRuntimeArgumentForScriptToken(arguments[effectArgumentIndex]);
    for (size_t index = 2; index < arguments.size(); ++index)
    {
        lua << ", " << luaRuntimeArgumentForScriptToken(arguments[index]);
    }
    lua << ")"
        << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
    return true;
}

std::vector<std::string> normalizedServiceArguments(const std::vector<std::string> &arguments);

bool emitNativeModelCapabilityServiceIfSupported(std::ostringstream &lua, const Mm9ScriptLine &line, size_t indentDepth)
{
    const std::string normalizedCommand = normalizeMm9ScriptCommandName(line.name);
    const std::vector<std::string> arguments = normalizedServiceArguments(splitScriptArguments(line.argumentsText));
    const std::string indent = luaIndent(indentDepth);
    const std::string sourceComment =
        " -- " + line.sourcePath.filename().string() + ':' + std::to_string(line.lineNumber);

    if (normalizedCommand == "getsocketpos")
    {
        if (arguments.size() != 4 || !isLuaIdentifier(trimCopy(arguments[1]))
            || !isLuaIdentifier(trimCopy(arguments[2])) || !isLuaIdentifier(trimCopy(arguments[3])))
        {
            return false;
        }

        lua << indent << luaStateField(trimCopy(arguments[1])) << ", "
            << luaStateField(trimCopy(arguments[2])) << ", "
            << luaStateField(trimCopy(arguments[3])) << " = ctx:self():socketPos("
            << luaRuntimeArgumentForScriptToken(arguments[0]) << ")" << sourceComment << '\n';
        return true;
    }

    if (normalizedCommand == "setmodelfilenames")
    {
        if (arguments.empty())
        {
            return false;
        }

        lua << indent << "ctx:self():setModelFilenames(";
        for (size_t index = 0; index < arguments.size(); ++index)
        {
            if (index != 0)
            {
                lua << ", ";
            }
            lua << luaRuntimeArgumentForScriptToken(arguments[index]);
        }
        lua << ")" << sourceComment << '\n';
        return true;
    }

    if (normalizedCommand == "attachprop")
    {
        if (arguments.size() < 4)
        {
            return false;
        }

        const std::optional<std::string> attachedExpression = luaObjectTargetExpression(arguments[3]);
        if (!attachedExpression || *attachedExpression == "nil")
        {
            return false;
        }

        lua << indent << "ctx:self():attachProp("
            << luaRuntimeArgumentForScriptToken(arguments[0]) << ", "
            << luaRuntimeArgumentForScriptToken(arguments[1]) << ", "
            << luaRuntimeArgumentForScriptToken(arguments[2]) << ", "
            << *attachedExpression << ")" << sourceComment << '\n';
        return true;
    }

    if (normalizedCommand == "detachprop")
    {
        if (arguments.empty())
        {
            return false;
        }

        const std::optional<std::string> attachedExpression = luaObjectTargetExpression(arguments[0]);
        if (!attachedExpression || *attachedExpression == "nil")
        {
            return false;
        }

        lua << indent << "ctx:self():detachProp(" << *attachedExpression;
        for (size_t index = 1; index < arguments.size(); ++index)
        {
            lua << ", " << luaRuntimeArgumentForScriptToken(arguments[index]);
        }
        lua << ")" << sourceComment << '\n';
        return true;
    }

    return false;
}

std::vector<std::string> normalizedServiceArguments(const std::vector<std::string> &arguments)
{
    std::vector<std::string> result;
    for (const std::string &argument : arguments)
    {
        const std::vector<std::string> parts = splitWhitespaceScriptArguments(argument);
        if (parts.empty())
        {
            const std::string trimmed = trimCopy(argument);
            if (!trimmed.empty() && trimmed != ")")
            {
                result.push_back(trimmed);
            }
            continue;
        }

        for (const std::string &part : parts)
        {
            if (trimCopy(part) != ")")
            {
                result.push_back(part);
            }
        }
    }
    return result;
}

void emitLuaStateTuple(std::ostringstream &lua, const std::vector<std::string> &arguments, size_t count)
{
    for (size_t index = 0; index < count; ++index)
    {
        if (index != 0)
        {
            lua << ", ";
        }
        lua << luaStateField(trimCopy(arguments[index]));
    }
}

bool emitNativeVectorUtilityIfSupported(std::ostringstream &lua, const Mm9ScriptLine &line, size_t indentDepth)
{
    const std::string normalizedCommand = normalizeMm9ScriptCommandName(line.name);
    const std::vector<std::string> arguments = normalizedServiceArguments(splitScriptArguments(line.argumentsText));
    const std::string indent = luaIndent(indentDepth);
    const std::string sourceComment =
        " -- " + line.sourcePath.filename().string() + ':' + std::to_string(line.lineNumber);

    auto allIdentifiers = [&](size_t offset, size_t count)
    {
        for (size_t index = offset; index < offset + count; ++index)
        {
            if (index >= arguments.size() || !isLuaIdentifier(trimCopy(arguments[index])))
            {
                return false;
            }
        }
        return true;
    };

    std::string method;
    size_t inputCount = 0;
    if (normalizedCommand == "vecscale")
    {
        method = "vecScale";
        inputCount = 4;
    }
    else if (normalizedCommand == "vecnorm" || normalizedCommand == "normalizevector")
    {
        method = "vecNorm";
        inputCount = 3;
    }
    else if (normalizedCommand == "rotatedir")
    {
        method = "rotateDir";
        inputCount = 4;
    }
    else if (normalizedCommand == "vecadd")
    {
        method = "vecAdd";
        inputCount = 6;
    }
    else if (normalizedCommand == "vecsub")
    {
        method = "vecSub";
        inputCount = 6;
    }
    if (!method.empty())
    {
        if (arguments.size() < inputCount || !allIdentifiers(0, 3))
        {
            return false;
        }

        lua << indent;
        emitLuaStateTuple(lua, arguments, 3);
        lua << " = ctx:" << method << '(';
        for (size_t index = 0; index < inputCount; ++index)
        {
            if (index != 0)
            {
                lua << ", ";
            }
            lua << luaRuntimeArgumentForScriptToken(arguments[index]);
        }
        lua << ")" << sourceComment << '\n';
        return true;
    }

    if (normalizedCommand == "veccross" || normalizedCommand == "getcrossproduct")
    {
        if (arguments.size() < 9 || !isLuaIdentifier(trimCopy(arguments[6]))
            || !isLuaIdentifier(trimCopy(arguments[7])) || !isLuaIdentifier(trimCopy(arguments[8])))
        {
            return false;
        }

        lua << indent;
        emitLuaStateTuple(lua, std::vector<std::string>{ arguments[6], arguments[7], arguments[8] }, 3);
        lua << " = ctx:vecCross(";
        for (size_t index = 0; index < 6; ++index)
        {
            if (index != 0)
            {
                lua << ", ";
            }
            lua << luaRuntimeArgumentForScriptToken(arguments[index]);
        }
        lua << ")" << sourceComment << '\n';
        return true;
    }

    if (normalizedCommand == "calcdist" || normalizedCommand == "vecdist"
        || normalizedCommand == "vecangle")
    {
        if (arguments.size() < 7 || !isLuaIdentifier(trimCopy(arguments[6])))
        {
            return false;
        }

        lua << indent << luaStateField(trimCopy(arguments[6])) << " = ctx:"
            << (normalizedCommand == "vecangle" ? "vecAngle" : "vecDist") << '(';
        for (size_t index = 0; index < 6; ++index)
        {
            if (index != 0)
            {
                lua << ", ";
            }
            lua << luaRuntimeArgumentForScriptToken(arguments[index]);
        }
        lua << ")" << sourceComment << '\n';
        return true;
    }

    if (normalizedCommand == "vecmag")
    {
        if (arguments.size() < 4 || !isLuaIdentifier(trimCopy(arguments[3])))
        {
            return false;
        }

        lua << indent << luaStateField(trimCopy(arguments[3])) << " = ctx:vecMag("
            << luaRuntimeArgumentForScriptToken(arguments[0]) << ", "
            << luaRuntimeArgumentForScriptToken(arguments[1]) << ", "
            << luaRuntimeArgumentForScriptToken(arguments[2]) << ")"
            << sourceComment << '\n';
        return true;
    }

    return false;
}

bool emitNativeMovementServiceIfSupported(
    std::ostringstream &lua,
    const Mm9ScriptLine &line,
    size_t indentDepth,
    const Mm9LuaGenerationState &generationState)
{
    const std::string normalizedCommand = normalizeMm9ScriptCommandName(line.name);
    std::string method;
    if (normalizedCommand == "movetopos")
    {
        method = "moveToPos";
    }
    else if (normalizedCommand == "runtopos")
    {
        method = "runToPos";
    }
    else if (normalizedCommand == "walktopos")
    {
        method = "walkToPos";
    }
    else if (normalizedCommand == "walkto")
    {
        method = "walkTo";
    }
    else if (normalizedCommand == "runto")
    {
        method = "runTo";
    }
    else if (normalizedCommand == "movedir")
    {
        method = "moveDir";
    }
    else if (normalizedCommand == "faceobject")
    {
        method = "faceObject";
    }
    else if (normalizedCommand == "facepos")
    {
        method = "facePos";
    }
    else if (normalizedCommand == "stop")
    {
        method = "stop";
    }
    else if (normalizedCommand == "walk")
    {
        method = "walk";
    }
    else if (normalizedCommand == "run")
    {
        method = "run";
    }
    else if (normalizedCommand == "rotate")
    {
        method = "rotate";
    }
    else if (normalizedCommand == "facedir")
    {
        method = "faceDir";
    }
    else if (normalizedCommand == "strafe")
    {
        method = "strafe";
    }
    else if (normalizedCommand == "setpushback")
    {
        method = "setPushBack";
    }
    else if (normalizedCommand == "turnleft")
    {
        method = "turnLeft";
    }
    else
    {
        return false;
    }

    const std::vector<std::string> arguments = normalizedServiceArguments(splitScriptArguments(line.argumentsText));
    if (normalizedCommand != "stop" && normalizedCommand != "walk" && normalizedCommand != "run"
        && arguments.empty())
    {
        return false;
    }
    if (normalizedCommand == "facedir" && arguments.size() >= 4 && looksLikeScriptHandleToken(arguments[0]))
    {
        return false;
    }

    lua << luaIndent(indentDepth) << "ctx:self():" << method << '(';
    if (normalizedCommand == "walkto" || normalizedCommand == "runto" || normalizedCommand == "faceobject")
    {
        if (arguments.empty())
        {
            return false;
        }
        const std::optional<std::string> targetExpression = luaObjectTargetExpression(arguments[0], &generationState);
        if (!targetExpression || *targetExpression == "nil")
        {
            return false;
        }
        lua << *targetExpression;
        for (size_t index = 1; index < arguments.size(); ++index)
        {
            lua << ", " << luaRuntimeArgumentForScriptToken(arguments[index]);
        }
    }
    else if (normalizedCommand == "stop" || normalizedCommand == "walk" || normalizedCommand == "run")
    {
    }
    else
    {
        for (size_t index = 0; index < arguments.size(); ++index)
        {
            if (index != 0)
            {
                lua << ", ";
            }
            lua << luaRuntimeArgumentForScriptToken(arguments[index]);
        }
    }
    lua << ")"
        << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
    return true;
}

bool emitNativePresentationServiceIfSupported(std::ostringstream &lua, const Mm9ScriptLine &line, size_t indentDepth)
{
    const std::string normalizedCommand = normalizeMm9ScriptCommandName(line.name);
    std::string method;
    if (normalizedCommand == "screenfadeout")
    {
        method = "screenFadeOut";
    }
    else if (normalizedCommand == "screenfadein")
    {
        method = "screenFadeIn";
    }
    else if (normalizedCommand == "letterbox")
    {
        method = "letterBox";
    }
    else if (normalizedCommand == "rollovertext")
    {
        method = "rolloverText";
    }
    else if (normalizedCommand == "cachetexture")
    {
        method = "cacheTexture";
    }
    else if (normalizedCommand == "hidepiece")
    {
        method = "hidePiece";
    }
    else if (normalizedCommand == "doletter")
    {
        method = "doLetter";
    }
    else if (normalizedCommand == "getcontainercount")
    {
        method = "getContainerCount";
    }
    else
    {
        return false;
    }

    const std::vector<std::string> arguments = splitScriptArguments(line.argumentsText);
    if (normalizedCommand == "getcontainercount" && arguments.size() < 2)
    {
        return false;
    }
    lua << luaIndent(indentDepth) << "ctx:" << method << '(';
    for (size_t index = 0; index < arguments.size(); ++index)
    {
        if (index != 0)
        {
            lua << ", ";
        }
        lua << luaRuntimeArgumentForScriptToken(arguments[index]);
    }
    lua << ")"
        << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
    return true;
}

bool emitNativeSpawnServiceIfSupported(std::ostringstream &lua, const Mm9ScriptLine &line, size_t indentDepth)
{
    const std::string normalizedCommand = normalizeMm9ScriptCommandName(line.name);
    if (normalizedCommand != "spawn" && normalizedCommand != "spawn2")
    {
        return false;
    }

    const std::vector<std::string> arguments = normalizedServiceArguments(splitScriptArguments(line.argumentsText));
    if (arguments.size() < 5)
    {
        return false;
    }

    const std::string handleVar = trimCopy(arguments[0]);
    const std::string loweredHandleVar = lowerCopy(handleVar);
    if (!isLuaIdentifier(handleVar) || loweredHandleVar == "null" || loweredHandleVar == "nil" || handleVar == "0")
    {
        return false;
    }

    lua << luaIndent(indentDepth) << luaStateField(handleVar) << " = ctx:"
        << (normalizedCommand == "spawn2" ? "spawn2" : "spawn") << '(';
    for (size_t index = 1; index < arguments.size(); ++index)
    {
        if (index != 1)
        {
            lua << ", ";
        }
        lua << luaRuntimeArgumentForScriptToken(arguments[index]);
    }
    lua << ")"
        << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
    return true;
}

bool emitNativeAiCombatServiceIfSupported(std::ostringstream &lua, const Mm9ScriptLine &line, size_t indentDepth)
{
    const std::string normalizedCommand = normalizeMm9ScriptCommandName(line.name);
    const std::vector<std::string> arguments = normalizedServiceArguments(splitScriptArguments(line.argumentsText));
    const std::string indent = luaIndent(indentDepth);
    const std::string sourceComment =
        " -- " + line.sourcePath.filename().string() + ':' + std::to_string(line.lineNumber);

    if (normalizedCommand == "setidle")
    {
        lua << indent << "ctx:self():setIdle()" << sourceComment << '\n';
        return true;
    }

    if (normalizedCommand == "setstuck")
    {
        lua << indent << "ctx:self():setStuck()" << sourceComment << '\n';
        return true;
    }

    if (normalizedCommand == "setcrouch" || normalizedCommand == "settargetlosttime")
    {
        if (arguments.empty())
        {
            return false;
        }

        lua << indent << "ctx:self():"
            << (normalizedCommand == "setcrouch" ? "setCrouch" : "setTargetLostTime")
            << '(' << luaRuntimeArgumentForScriptToken(arguments[0]) << ")" << sourceComment << '\n';
        return true;
    }

    if (normalizedCommand == "die")
    {
        if (!arguments.empty())
        {
            return false;
        }

        lua << indent << "ctx:self():die()" << sourceComment << '\n';
        return true;
    }

    if (normalizedCommand == "damage")
    {
        if (arguments.size() < 3)
        {
            return false;
        }

        const std::optional<std::string> targetExpression = luaObjectTargetExpression(arguments[0]);
        if (!targetExpression || *targetExpression == "nil")
        {
            return false;
        }

        lua << indent << *targetExpression << ":damage("
            << luaRuntimeArgumentForScriptToken(arguments[1]) << ", "
            << luaRuntimeArgumentForScriptToken(arguments[2]);
        for (size_t index = 3; index < arguments.size(); ++index)
        {
            lua << ", " << luaRuntimeArgumentForScriptToken(arguments[index]);
        }
        lua << ")" << sourceComment << '\n';
        return true;
    }

    std::string relationMethod;
    if (normalizedCommand == "addfriend")
    {
        relationMethod = "addFriend";
    }
    else if (normalizedCommand == "addenemy")
    {
        relationMethod = "addEnemy";
    }
    else if (normalizedCommand == "removefriend")
    {
        relationMethod = "removeFriend";
    }
    else if (normalizedCommand == "removeenemy")
    {
        relationMethod = "removeEnemy";
    }
    if (!relationMethod.empty())
    {
        if (arguments.empty())
        {
            return false;
        }

        lua << indent << "ctx:self():" << relationMethod << '('
            << luaString(unquotedScriptToken(arguments[0])) << ")" << sourceComment << '\n';
        return true;
    }

    if (normalizedCommand == "isfriend" || normalizedCommand == "aigetdistance")
    {
        if (arguments.size() < 2 || !isLuaIdentifier(trimCopy(arguments[1])))
        {
            return false;
        }

        const std::optional<std::string> targetExpression = luaObjectTargetExpression(arguments[0]);
        if (!targetExpression || *targetExpression == "nil")
        {
            return false;
        }

        const std::string method = normalizedCommand == "isfriend" ? "isFriend" : "aiDistanceTo";
        lua << indent << luaStateField(trimCopy(arguments[1])) << " = ctx:self():"
            << method << '(' << *targetExpression << ")" << sourceComment << '\n';
        return true;
    }

    if (normalizedCommand == "sendalert")
    {
        if (arguments.empty())
        {
            return false;
        }

        const std::optional<std::string> targetExpression = luaObjectTargetExpression(arguments[0]);
        if (!targetExpression)
        {
            return false;
        }

        lua << indent << "ctx:self():sendAlert(" << *targetExpression << ")" << sourceComment << '\n';
        return true;
    }

    if (normalizedCommand == "help" || normalizedCommand == "estimaterangeattackhit")
    {
        if (arguments.size() != 1)
        {
            return false;
        }

        const std::optional<std::string> targetExpression = luaObjectTargetExpression(arguments[0]);
        if (!targetExpression || *targetExpression == "nil")
        {
            return false;
        }

        const std::string method = normalizedCommand == "help" ? "help" : "estimateRangeAttackHit";
        lua << indent << "ctx:self():" << method << '(' << *targetExpression << ")" << sourceComment << '\n';
        return true;
    }

    if (normalizedCommand == "land")
    {
        if (!arguments.empty())
        {
            return false;
        }

        lua << indent << "ctx:self():land()" << sourceComment << '\n';
        return true;
    }

    std::string requestMethod;
    if (normalizedCommand == "attack")
    {
        requestMethod = "attack";
    }
    else if (normalizedCommand == "rangeattack")
    {
        requestMethod = "rangeAttack";
    }
    if (!requestMethod.empty())
    {
        lua << indent << "ctx:self():" << requestMethod << '(';
        if (!arguments.empty())
        {
            lua << luaString(trimCopy(arguments[0]));
        }
        lua << ")" << sourceComment << '\n';
        return true;
    }

    if (normalizedCommand == "findtargets")
    {
        if (arguments.size() < 3)
        {
            return false;
        }

        lua << indent << "ctx:self():findTargets(";
        for (size_t index = 0; index < arguments.size(); ++index)
        {
            if (index != 0)
            {
                lua << ", ";
            }
            lua << luaRuntimeArgumentForScriptToken(arguments[index]);
        }
        lua << ")" << sourceComment << '\n';
        return true;
    }

    if (normalizedCommand == "findhidingplace")
    {
        if (arguments.size() != 1 || !isLuaIdentifier(trimCopy(arguments[0])))
        {
            return false;
        }

        lua << indent << luaStateField(trimCopy(arguments[0]))
            << " = ctx:self():findHidingPlace()" << sourceComment << '\n';
        return true;
    }

    std::string actorActionMethod;
    if (normalizedCommand == "taunt")
    {
        actorActionMethod = "taunt";
    }
    else if (normalizedCommand == "aware")
    {
        actorActionMethod = "aware";
    }
    else if (normalizedCommand == "launch")
    {
        actorActionMethod = "launch";
    }
    else if (normalizedCommand == "converse")
    {
        actorActionMethod = "converse";
    }
    else if (normalizedCommand == "resumewait")
    {
        actorActionMethod = "resumeWait";
    }
    else if (normalizedCommand == "pausewait")
    {
        actorActionMethod = "pauseWait";
    }
    else if (normalizedCommand == "jump")
    {
        actorActionMethod = "jump";
    }
    if (!actorActionMethod.empty())
    {
        lua << indent << "ctx:self():" << actorActionMethod << '(';
        for (size_t index = 0; index < arguments.size(); ++index)
        {
            if (index != 0)
            {
                lua << ", ";
            }
            lua << luaRuntimeArgumentForScriptToken(arguments[index]);
        }
        lua << ")" << sourceComment << '\n';
        return true;
    }

    std::string queryMethod;
    if (normalizedCommand == "canattack")
    {
        queryMethod = "canAttack";
    }
    else if (normalizedCommand == "canrangeattack")
    {
        queryMethod = "canRangeAttack";
    }
    else if (normalizedCommand == "hasrangeattack")
    {
        queryMethod = "hasRangeAttack";
    }
    else if (normalizedCommand == "istargetinrange")
    {
        queryMethod = "isTargetInRange";
    }
    else if (normalizedCommand == "isattacking")
    {
        queryMethod = "isAttacking";
    }
    if (!queryMethod.empty())
    {
        if (arguments.empty() || !isLuaIdentifier(trimCopy(arguments[0])))
        {
            return false;
        }

        lua << indent << luaStateField(trimCopy(arguments[0])) << " = ctx:self():"
            << queryMethod << "()" << sourceComment << '\n';
        return true;
    }

    std::string runtimeQueryMethod;
    if (normalizedCommand == "ismoving")
    {
        runtimeQueryMethod = "isMoving";
    }
    else if (normalizedCommand == "isonground")
    {
        runtimeQueryMethod = "isOnGround";
    }
    if (!runtimeQueryMethod.empty())
    {
        if (arguments.size() != 1 || !isLuaIdentifier(trimCopy(arguments[0])))
        {
            return false;
        }

        lua << indent << luaStateField(trimCopy(arguments[0])) << " = ctx:self():"
            << runtimeQueryMethod << "()" << sourceComment << '\n';
        return true;
    }

    if (normalizedCommand == "isdead")
    {
        if (arguments.size() != 2 || !isLuaIdentifier(trimCopy(arguments[1])))
        {
            return false;
        }

        const std::optional<std::string> targetExpression = luaObjectTargetExpression(arguments[0]);
        if (!targetExpression || *targetExpression == "nil")
        {
            return false;
        }

        lua << indent << luaStateField(trimCopy(arguments[1])) << " = "
            << *targetExpression << ":isDead()" << sourceComment << '\n';
        return true;
    }

    if (normalizedCommand == "canreachtarget" || normalizedCommand == "isfear"
        || normalizedCommand == "isinnorunzone")
    {
        if (arguments.size() != 1 || !isLuaIdentifier(trimCopy(arguments[0])))
        {
            return false;
        }

        std::string method = "canReachTarget";
        if (normalizedCommand == "isfear")
        {
            method = "isFear";
        }
        else if (normalizedCommand == "isinnorunzone")
        {
            method = "isInNoRunZone";
        }

        lua << indent << luaStateField(trimCopy(arguments[0])) << " = ctx:self():"
            << method << "()" << sourceComment << '\n';
        return true;
    }

    if (normalizedCommand == "canreachobject" || normalizedCommand == "isfacing"
        || normalizedCommand == "shouldrunaway" || normalizedCommand == "isworldobject"
        || normalizedCommand == "isclearshot")
    {
        const bool supportedArgumentCount = normalizedCommand == "isclearshot"
            ? (arguments.size() == 2 || arguments.size() == 3)
            : arguments.size() == 2;
        if (!supportedArgumentCount || !isLuaIdentifier(trimCopy(arguments[1])))
        {
            return false;
        }
        if (arguments.size() == 3 && !isLuaIdentifier(trimCopy(arguments[2])))
        {
            return false;
        }

        const std::optional<std::string> targetExpression = luaObjectTargetExpression(arguments[0]);
        if (!targetExpression || *targetExpression == "nil")
        {
            return false;
        }

        if (normalizedCommand == "isworldobject")
        {
            lua << indent << luaStateField(trimCopy(arguments[1])) << " = "
                << *targetExpression << ":isWorldObject()" << sourceComment << '\n';
            return true;
        }
        if (normalizedCommand == "isclearshot")
        {
            lua << indent << luaStateField(trimCopy(arguments[1]));
            if (arguments.size() == 3)
            {
                lua << ", " << luaStateField(trimCopy(arguments[2]));
            }
            lua << " = ctx:self():isClearShot(" << *targetExpression << ")" << sourceComment << '\n';
            return true;
        }

        std::string method = "canReachObject";
        if (normalizedCommand == "isfacing")
        {
            method = "isFacing";
        }
        else if (normalizedCommand == "shouldrunaway")
        {
            method = "shouldRunAwayFrom";
        }

        lua << indent << luaStateField(trimCopy(arguments[1])) << " = ctx:self():"
            << method << '(' << *targetExpression << ")" << sourceComment << '\n';
        return true;
    }

    return false;
}

bool isMm9SimpleEventRegistrationCommand(const std::string &normalizedCommand)
{
    return normalizedCommand == "ondamage" || normalizedCommand == "onpoststartworld"
        || normalizedCommand == "onpostminisaveload" || normalizedCommand == "onpostsaveload"
        || normalizedCommand == "onfoundplayer" || normalizedCommand == "onfoundtarget"
        || normalizedCommand == "ontargetdead" || normalizedCommand == "ontouchnotify"
        || normalizedCommand == "onlosttarget" || normalizedCommand == "onobjectlinkbroken"
        || normalizedCommand == "onobstacle" || normalizedCommand == "onalert"
        || normalizedCommand == "onstuck" || normalizedCommand == "ondeath"
        || normalizedCommand == "onattackready" || normalizedCommand == "ondamagedone"
        || normalizedCommand == "onstuckdone" || normalizedCommand == "ondeathdone"
        || normalizedCommand == "oncongestion" || normalizedCommand == "ondoor"
        || normalizedCommand == "onpathclear" || normalizedCommand == "ontargetoutofrange"
        || normalizedCommand == "onprojectile" || normalizedCommand == "onavoidingobstacle"
        || normalizedCommand == "onobstacleavoided" || normalizedCommand == "onhelp"
        || normalizedCommand == "onworldswitch" || normalizedCommand == "oncachefiles"
        || normalizedCommand == "onenrage" || normalizedCommand == "onenragedone"
        || normalizedCommand == "onfear" || normalizedCommand == "onfeardone"
        || normalizedCommand == "onplayerinterrupt" || normalizedCommand == "ontargethit";
}

bool emitNativeEventRegistrationIfSupported(std::ostringstream &lua, const Mm9ScriptLine &line, size_t indentDepth)
{
    const std::string normalizedCommand = normalizeMm9ScriptCommandName(line.name);
    const std::vector<std::string> arguments = splitScriptArguments(line.argumentsText);
    const std::string indent = luaIndent(indentDepth);
    const std::string sourceComment =
        " -- " + line.sourcePath.filename().string() + ':' + std::to_string(line.lineNumber);

    if (isMm9SimpleEventRegistrationCommand(normalizedCommand))
    {
        lua << indent << "ctx:onEvent(" << luaString(readableLuaCommandName(line));
        if (!arguments.empty())
        {
            lua << ", " << luaString(trimCopy(arguments[0]));
        }
        lua << ")" << sourceComment << '\n';
        return true;
    }

    if (normalizedCommand == "ontargetbeyonddist" || normalizedCommand == "ontargetwithindist")
    {
        if (arguments.empty())
        {
            lua << indent << "ctx:onEvent(" << luaString(readableLuaCommandName(line)) << ")"
                << sourceComment << '\n';
            return true;
        }

        lua << indent << "ctx:onEvent(" << luaString(readableLuaCommandName(line)) << ", "
            << luaRuntimeArgumentForScriptToken(arguments[0]);
        if (arguments.size() >= 2)
        {
            lua << ", " << luaString(trimCopy(arguments[1]));
        }
        lua << ")" << sourceComment << '\n';
        return true;
    }

    if (normalizedCommand == "addmodelkey")
    {
        if (arguments.empty())
        {
            return false;
        }

        lua << indent << "ctx:addModelKey(" << luaRuntimeArgumentForScriptToken(arguments[0]);
        if (arguments.size() >= 2)
        {
            lua << ", " << luaString(trimCopy(arguments[1]));
        }
        lua << ")" << sourceComment << '\n';
        return true;
    }

    if (normalizedCommand == "removemodelkey")
    {
        if (arguments.empty())
        {
            return false;
        }

        lua << indent << "ctx:removeModelKey(" << luaRuntimeArgumentForScriptToken(arguments[0])
            << ")" << sourceComment << '\n';
        return true;
    }

    if (normalizedCommand == "setcallback")
    {
        if (arguments.empty())
        {
            return false;
        }

        lua << indent << "ctx:setCallback(" << luaRuntimeArgumentForScriptToken(arguments[0]);
        if (arguments.size() >= 2)
        {
            lua << ", " << luaString(trimCopy(arguments[1]));
        }
        lua << ")" << sourceComment << '\n';
        return true;
    }

    if (normalizedCommand == "killcallback")
    {
        if (arguments.empty())
        {
            return false;
        }

        lua << indent << "ctx:killCallback(" << luaRuntimeArgumentForScriptToken(arguments[0])
            << ")" << sourceComment << '\n';
        return true;
    }

    if (normalizedCommand == "removetrigger")
    {
        if (arguments.empty())
        {
            return false;
        }

        lua << indent << "ctx:removeTrigger(" << luaRuntimeArgumentForScriptToken(arguments[0])
            << ")" << sourceComment << '\n';
        return true;
    }

    return false;
}

void emitLuaCommandCall(
    std::ostringstream &lua,
    const Mm9ScriptLine &line,
    size_t indentDepth,
    Mm9LuaGenerationState &generationState)
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
        if (normalizedCommand.rfind("while", 0) == 0)
        {
            Mm9LuaGenerationState::AliasFrame frame = {};
            frame.restoreOnElse = false;
            generationState.aliasFrames.push_back(std::move(frame));
            generationState.handleAliases.clear();
        }
        else
        {
            Mm9LuaGenerationState::AliasFrame frame = {};
            frame.entryAliases = generationState.handleAliases;
            frame.restoreOnElse = true;
            generationState.aliasFrames.push_back(std::move(frame));
        }
        const std::string keyword = normalizedCommand.rfind("while", 0) == 0 ? "while" : "if";
        lua << indent << keyword << " ctx:condition(" << luaString(readableControlConditionText(line))
            << ") " << (keyword == "while" ? "do" : "then")
            << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return;
    }
    if (normalizedCommand == "else")
    {
        if (!generationState.aliasFrames.empty() && generationState.aliasFrames.back().restoreOnElse)
        {
            generationState.aliasFrames.back().thenAliases = generationState.handleAliases;
            generationState.aliasFrames.back().sawElse = true;
            generationState.handleAliases = generationState.aliasFrames.back().entryAliases;
        }
        else
        {
            generationState.handleAliases.clear();
        }
        lua << indent << "else -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return;
    }
    if (isMm9ControlCloseCommand(normalizedCommand))
    {
        std::map<std::string, std::string> joinedAliases;
        if (!generationState.aliasFrames.empty())
        {
            const Mm9LuaGenerationState::AliasFrame frame = generationState.aliasFrames.back();
            generationState.aliasFrames.pop_back();
            if (frame.restoreOnElse)
            {
                joinedAliases = frame.sawElse
                    ? intersectHandleAliases(frame.thenAliases, generationState.handleAliases)
                    : intersectHandleAliases(frame.entryAliases, generationState.handleAliases);
            }
        }
        generationState.handleAliases = std::move(joinedAliases);
        lua << indent << "end -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
        return;
    }

    applyHandleAliasMutationForCommand(generationState, line);

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
    if (emitNativeStateMutationIfSupported(lua, line, indentDepth))
    {
        return;
    }
    if (emitNativeHandleAssignmentIfSupported(lua, line, indentDepth))
    {
        return;
    }
    if (emitNativeObjectHandleLookupIfSupported(lua, line, indentDepth))
    {
        return;
    }
    if (emitNativeObjectIdentityIfSupported(lua, line, indentDepth))
    {
        return;
    }
    if (emitNativeObjectQueryIfSupported(lua, line, indentDepth))
    {
        return;
    }
    if (emitNativeObjectBoundsIfSupported(lua, line, indentDepth))
    {
        return;
    }
    if (emitNativeObjectFlagIfSupported(lua, line, indentDepth, generationState))
    {
        return;
    }
    if (emitNativeObjectPositionIfSupported(lua, line, indentDepth, generationState))
    {
        return;
    }
    if (emitNativeObjectStatIfSupported(lua, line, indentDepth))
    {
        return;
    }
    if (emitNativeObjectDistanceIfSupported(lua, line, indentDepth))
    {
        return;
    }
    if (emitNativeObjectPropertyIfSupported(lua, line, indentDepth))
    {
        return;
    }
    if (emitNativeObjectMotionIfSupported(lua, line, indentDepth))
    {
        return;
    }
    if (emitNativeObjectTargetIfSupported(lua, line, indentDepth))
    {
        return;
    }
    if (emitNativeObjectLinkIfSupported(lua, line, indentDepth))
    {
        return;
    }
    if (emitNativeObjectLifetimeIfSupported(lua, line, indentDepth))
    {
        return;
    }
    if (emitNativeObjectRegistryQueryIfSupported(lua, line, indentDepth))
    {
        return;
    }
    if (emitNativeArrayAccessIfSupported(lua, line, indentDepth))
    {
        return;
    }
    if (emitNativeRuntimeUtilityIfSupported(lua, line, indentDepth))
    {
        return;
    }
    if (emitNativePartyScriptServiceIfSupported(lua, line, indentDepth))
    {
        return;
    }
    if (emitNativeStateCommandIfSupported(lua, line, indentDepth))
    {
        return;
    }
    if (emitNativeVectorUtilityIfSupported(lua, line, indentDepth))
    {
        return;
    }
    if (emitNativeWaitIfSupported(lua, line, indentDepth))
    {
        return;
    }
    if (emitNativeAtTimeIfSupported(lua, line, indentDepth))
    {
        return;
    }
    if (emitNativeAudioServiceIfSupported(lua, line, indentDepth))
    {
        return;
    }
    if (emitNativeAnimationServiceIfSupported(lua, line, indentDepth))
    {
        return;
    }
    if (emitNativeClientFxServiceIfSupported(lua, line, indentDepth))
    {
        return;
    }
    if (emitNativeModelCapabilityServiceIfSupported(lua, line, indentDepth))
    {
        return;
    }
    if (emitNativeMovementServiceIfSupported(lua, line, indentDepth, generationState))
    {
        return;
    }
    if (emitNativePresentationServiceIfSupported(lua, line, indentDepth))
    {
        return;
    }
    if (emitNativeSpawnServiceIfSupported(lua, line, indentDepth))
    {
        return;
    }
    if (emitNativeAiCombatServiceIfSupported(lua, line, indentDepth))
    {
        return;
    }
    if (emitNativeEventRegistrationIfSupported(lua, line, indentDepth))
    {
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
            if (normalizedCommand == "trigger")
            {
                const std::vector<std::string> arguments = splitScriptArguments(line.argumentsText);
                if (arguments.size() == 2)
                {
                    lua << indent << "ctx:trigger(" << luaTriggerTargetArgumentForScriptToken(arguments[0]) << ", "
                        << luaValueForScriptToken(arguments[1]) << ")";
                }
                else
                {
                    lua << indent << "ctx:" << method << '(' << luaArgumentList(line.argumentsText) << ")";
                }
            }
            else
            {
                lua << indent << "ctx:" << method << '(' << luaArgumentList(line.argumentsText) << ")";
            }
        }
    }
    else
    {
        generationState.handleAliases.clear();
        lua << indent << "ctx:command(" << luaString(readableLuaCommandName(line)) << ", "
            << luaString(line.argumentsText) << ")";
    }
    lua << " -- " << line.sourcePath.filename().string() << ':' << line.lineNumber << '\n';
}

struct Mm9LuaObjectTriggerCollapse
{
    bool valid = false;
    std::string objectName;
    std::string handleVar;
    std::vector<Mm9ScriptLine> triggerLines;
};

struct Mm9LuaObjectFlagAction
{
    Mm9ScriptLine line;
    std::string flag;
    bool enabled = false;
};

struct Mm9LuaObjectFlagCollapse
{
    bool valid = false;
    std::string objectName;
    std::string handleVar;
    std::vector<Mm9LuaObjectFlagAction> actions;
};

struct Mm9LuaObjectStatAction
{
    Mm9ScriptLine line;
    std::string statName;
    std::string destinationName;
    std::string valueExpression;
    bool getter = false;
};

struct Mm9LuaObjectStatCollapse
{
    bool valid = false;
    std::string objectName;
    std::string handleVar;
    std::vector<Mm9LuaObjectStatAction> actions;
};

struct Mm9LuaObjectPositionAction
{
    Mm9ScriptLine line;
    bool getter = false;
    std::vector<std::string> values;
};

struct Mm9LuaObjectPositionCollapse
{
    bool valid = false;
    std::string objectName;
    std::string handleVar;
    std::vector<Mm9LuaObjectPositionAction> actions;
};

bool textHasCaseInsensitiveToken(const std::string &text, const std::string &token)
{
    const std::string loweredToken = lowerCopy(token);
    std::string current;
    for (const char ch : text)
    {
        const unsigned char byte = static_cast<unsigned char>(ch);
        if (std::isalnum(byte) != 0 || ch == '_')
        {
            current.push_back(static_cast<char>(std::tolower(byte)));
            continue;
        }

        if (current == loweredToken)
        {
            return true;
        }
        current.clear();
    }

    return current == loweredToken;
}

bool scriptHandleIsReferencedBeforeReassignment(
    const Mm9ScriptFile &file,
    size_t startLineIndex,
    const std::string &handleVar)
{
    for (size_t index = startLineIndex; index < file.lines.size(); ++index)
    {
        const Mm9ScriptLine &line = file.lines[index];
        if (line.kind != Mm9ScriptLineKind::Command)
        {
            continue;
        }

        if (normalizeMm9ScriptCommandName(line.name) == "getobjecthandle")
        {
            const std::vector<std::string> arguments = splitScriptArguments(line.argumentsText);
            if (arguments.size() == 2 && lowerCopy(trimCopy(arguments[1])) == lowerCopy(handleVar))
            {
                return false;
            }
        }

        if (textHasCaseInsensitiveToken(line.codeText, handleVar))
        {
            return true;
        }
    }

    return false;
}

Mm9LuaObjectTriggerCollapse objectTriggerCollapseAtLine(const Mm9ScriptFile &file, size_t lineIndex)
{
    Mm9LuaObjectTriggerCollapse collapse = {};
    if (lineIndex >= file.lines.size())
    {
        return collapse;
    }

    const Mm9ScriptLine &handleLine = file.lines[lineIndex];
    if (handleLine.kind != Mm9ScriptLineKind::Command ||
        normalizeMm9ScriptCommandName(handleLine.name) != "getobjecthandle")
    {
        return collapse;
    }

    const std::vector<std::string> handleArguments = splitScriptArguments(handleLine.argumentsText);
    if (handleArguments.size() != 2)
    {
        return collapse;
    }

    const std::string objectName = trimCopy(handleArguments[0]);
    const std::string handleVar = trimCopy(handleArguments[1]);
    if (objectName.empty() || handleVar.empty())
    {
        return collapse;
    }

    for (size_t index = lineIndex + 1; index < file.lines.size(); ++index)
    {
        const Mm9ScriptLine &line = file.lines[index];
        if (line.kind != Mm9ScriptLineKind::Command || normalizeMm9ScriptCommandName(line.name) != "trigger")
        {
            break;
        }

        const std::vector<std::string> triggerArguments = splitScriptArguments(line.argumentsText);
        if (triggerArguments.size() != 2 || lowerCopy(trimCopy(triggerArguments[0])) != lowerCopy(handleVar))
        {
            break;
        }

        collapse.triggerLines.push_back(line);
    }

    collapse.valid = !collapse.triggerLines.empty();
    collapse.objectName = objectName;
    collapse.handleVar = handleVar;
    return collapse;
}

Mm9LuaObjectFlagCollapse objectFlagCollapseAtLine(const Mm9ScriptFile &file, size_t lineIndex)
{
    Mm9LuaObjectFlagCollapse collapse = {};
    if (lineIndex >= file.lines.size())
    {
        return collapse;
    }

    const Mm9ScriptLine &handleLine = file.lines[lineIndex];
    if (handleLine.kind != Mm9ScriptLineKind::Command ||
        normalizeMm9ScriptCommandName(handleLine.name) != "getobjecthandle")
    {
        return collapse;
    }

    const std::vector<std::string> handleArguments = splitScriptArguments(handleLine.argumentsText);
    if (handleArguments.size() != 2)
    {
        return collapse;
    }

    const std::string objectName = trimCopy(handleArguments[0]);
    const std::string handleVar = trimCopy(handleArguments[1]);
    if (objectName.empty() || handleVar.empty())
    {
        return collapse;
    }

    for (size_t index = lineIndex + 1; index < file.lines.size(); ++index)
    {
        const Mm9ScriptLine &line = file.lines[index];
        const std::string normalizedCommand =
            line.kind == Mm9ScriptLineKind::Command ? normalizeMm9ScriptCommandName(line.name) : "";
        if (normalizedCommand != "setflag" && normalizedCommand != "clearflag")
        {
            break;
        }

        const std::vector<std::string> arguments = splitScriptArguments(line.argumentsText);
        if (arguments.size() != 2 || lowerCopy(trimCopy(arguments[0])) != lowerCopy(handleVar))
        {
            break;
        }

        Mm9LuaObjectFlagAction action = {};
        action.line = line;
        action.flag = trimCopy(arguments[1]);
        action.enabled = normalizedCommand == "setflag";
        collapse.actions.push_back(action);
    }

    collapse.valid = !collapse.actions.empty();
    collapse.objectName = objectName;
    collapse.handleVar = handleVar;
    return collapse;
}

Mm9LuaObjectStatCollapse objectStatCollapseAtLine(const Mm9ScriptFile &file, size_t lineIndex)
{
    Mm9LuaObjectStatCollapse collapse = {};
    if (lineIndex >= file.lines.size())
    {
        return collapse;
    }

    const Mm9ScriptLine &handleLine = file.lines[lineIndex];
    if (handleLine.kind != Mm9ScriptLineKind::Command ||
        normalizeMm9ScriptCommandName(handleLine.name) != "getobjecthandle")
    {
        return collapse;
    }

    const std::vector<std::string> handleArguments = splitScriptArguments(handleLine.argumentsText);
    if (handleArguments.size() != 2)
    {
        return collapse;
    }

    const std::string objectName = trimCopy(handleArguments[0]);
    const std::string handleVar = trimCopy(handleArguments[1]);
    if (objectName.empty() || handleVar.empty())
    {
        return collapse;
    }

    for (size_t index = lineIndex + 1; index < file.lines.size(); ++index)
    {
        const Mm9ScriptLine &line = file.lines[index];
        const std::string normalizedCommand =
            line.kind == Mm9ScriptLineKind::Command ? normalizeMm9ScriptCommandName(line.name) : "";
        if (normalizedCommand != "getstat" && normalizedCommand != "setstat")
        {
            break;
        }

        const std::vector<std::string> arguments = splitScriptArguments(line.argumentsText);
        if (arguments.size() != 3 || lowerCopy(trimCopy(arguments[0])) != lowerCopy(handleVar)
            || trimCopy(arguments[1]).empty())
        {
            break;
        }

        Mm9LuaObjectStatAction action = {};
        action.line = line;
        action.statName = trimCopy(arguments[1]);
        action.getter = normalizedCommand == "getstat";
        if (action.getter)
        {
            action.destinationName = trimCopy(arguments[2]);
            if (!isLuaIdentifier(action.destinationName))
            {
                break;
            }
        }
        else
        {
            const std::optional<std::string> expression = luaLiteralForSimpleScriptExpression(arguments[2]);
            if (!expression)
            {
                break;
            }
            action.valueExpression = *expression;
        }

        collapse.actions.push_back(action);
    }

    collapse.valid = !collapse.actions.empty();
    collapse.objectName = objectName;
    collapse.handleVar = handleVar;
    return collapse;
}

Mm9LuaObjectPositionCollapse objectPositionCollapseAtLine(const Mm9ScriptFile &file, size_t lineIndex)
{
    Mm9LuaObjectPositionCollapse collapse = {};
    if (lineIndex >= file.lines.size())
    {
        return collapse;
    }

    const Mm9ScriptLine &handleLine = file.lines[lineIndex];
    if (handleLine.kind != Mm9ScriptLineKind::Command ||
        normalizeMm9ScriptCommandName(handleLine.name) != "getobjecthandle")
    {
        return collapse;
    }

    const std::vector<std::string> handleArguments = splitScriptArguments(handleLine.argumentsText);
    if (handleArguments.size() != 2)
    {
        return collapse;
    }

    const std::string objectName = trimCopy(handleArguments[0]);
    const std::string handleVar = trimCopy(handleArguments[1]);
    if (objectName.empty() || handleVar.empty())
    {
        return collapse;
    }

    size_t nextLineIndex = lineIndex + 1;
    for (; nextLineIndex < file.lines.size(); ++nextLineIndex)
    {
        const Mm9ScriptLine &line = file.lines[nextLineIndex];
        const std::string normalizedCommand =
            line.kind == Mm9ScriptLineKind::Command ? normalizeMm9ScriptCommandName(line.name) : "";
        if (normalizedCommand != "getpos" && normalizedCommand != "setpos")
        {
            break;
        }

        const std::vector<std::string> arguments = splitScriptArguments(line.argumentsText);
        if (arguments.size() != 4 || lowerCopy(trimCopy(arguments[0])) != lowerCopy(handleVar))
        {
            return {};
        }

        Mm9LuaObjectPositionAction action = {};
        action.line = line;
        action.getter = normalizedCommand == "getpos";
        for (size_t argumentIndex = 1; argumentIndex < arguments.size(); ++argumentIndex)
        {
            const std::string value = trimCopy(arguments[argumentIndex]);
            if (action.getter)
            {
                if (!isLuaIdentifier(value))
                {
                    return {};
                }
                action.values.push_back(value);
                continue;
            }

            const std::optional<int32_t> numericValue = parseMm9RudeInt(value);
            if (!numericValue)
            {
                return {};
            }
            action.values.push_back(std::to_string(*numericValue));
        }

        collapse.actions.push_back(action);
    }

    if (collapse.actions.empty() || scriptHandleIsReferencedBeforeReassignment(file, nextLineIndex, handleVar))
    {
        return {};
    }

    collapse.valid = true;
    collapse.objectName = objectName;
    collapse.handleVar = handleVar;
    return collapse;
}

void emitObjectTriggerCollapse(
    std::ostringstream &lua,
    const Mm9ScriptLine &handleLine,
    const Mm9LuaObjectTriggerCollapse &collapse,
    size_t indentDepth)
{
    const std::string indent = luaIndent(indentDepth);
    if (collapse.triggerLines.size() == 1)
    {
        const Mm9ScriptLine &triggerLine = collapse.triggerLines.front();
        const std::vector<std::string> triggerArguments = splitScriptArguments(triggerLine.argumentsText);
        lua << indent << "ctx:object(" << luaString(collapse.objectName) << "):trigger("
            << luaString(trimCopy(triggerArguments[1])) << ") -- "
            << handleLine.sourcePath.filename().string() << ':' << handleLine.lineNumber
            << '-' << triggerLine.lineNumber << '\n';
        return;
    }

    lua << indent << "local object = ctx:object(" << luaString(collapse.objectName) << ") -- "
        << handleLine.sourcePath.filename().string() << ':' << handleLine.lineNumber << '\n';
    for (const Mm9ScriptLine &triggerLine : collapse.triggerLines)
    {
        const std::vector<std::string> triggerArguments = splitScriptArguments(triggerLine.argumentsText);
        lua << indent << "object:trigger(" << luaString(trimCopy(triggerArguments[1])) << ") -- "
            << triggerLine.sourcePath.filename().string() << ':' << triggerLine.lineNumber << '\n';
    }
}

void emitObjectStatAction(
    std::ostringstream &lua,
    const std::string &indent,
    const std::string &objectExpression,
    const Mm9LuaObjectStatAction &action)
{
    if (action.getter)
    {
        lua << indent << luaStateField(action.destinationName) << " = "
            << objectExpression << ":getStat(" << luaString(action.statName) << ") -- "
            << action.line.sourcePath.filename().string() << ':' << action.line.lineNumber << '\n';
        return;
    }

    lua << indent << objectExpression << ":setStat(" << luaString(action.statName) << ", "
        << action.valueExpression << ") -- "
        << action.line.sourcePath.filename().string() << ':' << action.line.lineNumber << '\n';
}

void emitObjectStatCollapse(
    std::ostringstream &lua,
    const Mm9ScriptLine &handleLine,
    const Mm9LuaObjectStatCollapse &collapse,
    size_t indentDepth)
{
    const std::string indent = luaIndent(indentDepth);
    if (collapse.actions.size() == 1)
    {
        const Mm9LuaObjectStatAction &action = collapse.actions.front();
        const std::string objectExpression = "ctx:object(" + luaString(collapse.objectName) + ")";
        if (action.getter)
        {
            lua << indent << luaStateField(action.destinationName) << " = "
                << objectExpression << ":getStat(" << luaString(action.statName) << ") -- "
                << handleLine.sourcePath.filename().string() << ':' << handleLine.lineNumber
                << '-' << action.line.lineNumber << '\n';
        }
        else
        {
            lua << indent << objectExpression << ":setStat(" << luaString(action.statName) << ", "
                << action.valueExpression << ") -- "
                << handleLine.sourcePath.filename().string() << ':' << handleLine.lineNumber
                << '-' << action.line.lineNumber << '\n';
        }
        return;
    }

    lua << indent << "local object = ctx:object(" << luaString(collapse.objectName) << ") -- "
        << handleLine.sourcePath.filename().string() << ':' << handleLine.lineNumber << '\n';
    for (const Mm9LuaObjectStatAction &action : collapse.actions)
    {
        emitObjectStatAction(lua, indent, "object", action);
    }
}

void emitObjectPositionAction(
    std::ostringstream &lua,
    const std::string &indent,
    const std::string &objectExpression,
    const Mm9LuaObjectPositionAction &action)
{
    if (action.getter)
    {
        lua << indent << luaStateField(action.values[0]) << ", "
            << luaStateField(action.values[1]) << ", "
            << luaStateField(action.values[2]) << " = "
            << objectExpression << ":pos() -- "
            << action.line.sourcePath.filename().string() << ':' << action.line.lineNumber << '\n';
        return;
    }

    lua << indent << objectExpression << ":setPos("
        << action.values[0] << ", " << action.values[1] << ", " << action.values[2] << ") -- "
        << action.line.sourcePath.filename().string() << ':' << action.line.lineNumber << '\n';
}

void emitObjectPositionCollapse(
    std::ostringstream &lua,
    const Mm9ScriptLine &handleLine,
    const Mm9LuaObjectPositionCollapse &collapse,
    size_t indentDepth)
{
    const std::string indent = luaIndent(indentDepth);
    if (collapse.actions.size() == 1)
    {
        const Mm9LuaObjectPositionAction &action = collapse.actions.front();
        const std::string objectExpression = "ctx:object(" + luaString(collapse.objectName) + ")";
        if (action.getter)
        {
            lua << indent << luaStateField(action.values[0]) << ", "
                << luaStateField(action.values[1]) << ", "
                << luaStateField(action.values[2]) << " = "
                << objectExpression << ":pos() -- "
                << handleLine.sourcePath.filename().string() << ':' << handleLine.lineNumber
                << '-' << action.line.lineNumber << '\n';
        }
        else
        {
            lua << indent << objectExpression << ":setPos("
                << action.values[0] << ", " << action.values[1] << ", " << action.values[2] << ") -- "
                << handleLine.sourcePath.filename().string() << ':' << handleLine.lineNumber
                << '-' << action.line.lineNumber << '\n';
        }
        return;
    }

    lua << indent << "local object = ctx:object(" << luaString(collapse.objectName) << ") -- "
        << handleLine.sourcePath.filename().string() << ':' << handleLine.lineNumber << '\n';
    for (const Mm9LuaObjectPositionAction &action : collapse.actions)
    {
        emitObjectPositionAction(lua, indent, "object", action);
    }
}

void emitObjectFlagCollapse(
    std::ostringstream &lua,
    const Mm9ScriptLine &handleLine,
    const Mm9LuaObjectFlagCollapse &collapse,
    size_t indentDepth)
{
    const std::string indent = luaIndent(indentDepth);
    if (collapse.actions.size() == 1)
    {
        const Mm9LuaObjectFlagAction &action = collapse.actions.front();
        lua << indent << "ctx:object(" << luaString(collapse.objectName) << "):setFlag("
            << luaString(action.flag) << ", " << (action.enabled ? "true" : "false") << ") -- "
            << handleLine.sourcePath.filename().string() << ':' << handleLine.lineNumber
            << '-' << action.line.lineNumber << '\n';
        return;
    }

    lua << indent << "local object = ctx:object(" << luaString(collapse.objectName) << ") -- "
        << handleLine.sourcePath.filename().string() << ':' << handleLine.lineNumber << '\n';
    for (const Mm9LuaObjectFlagAction &action : collapse.actions)
    {
        lua << indent << "object:setFlag(" << luaString(action.flag) << ", "
            << (action.enabled ? "true" : "false") << ") -- "
            << action.line.sourcePath.filename().string() << ':' << action.line.lineNumber << '\n';
    }
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
    std::string normalized = lowerCopy(trimCopy(name));
    while (!normalized.empty() && normalized.back() == '(')
    {
        normalized.pop_back();
        normalized = trimCopy(normalized);
    }
    return normalized;
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
    Mm9LuaGenerationState generationState;
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
            generationState.handleAliases.clear();
            generationState.aliasFrames.clear();
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
            applyHandleAliasMutationForCommand(generationState, line);
            const Mm9LuaObjectTriggerCollapse objectTriggerCollapse = objectTriggerCollapseAtLine(file, lineIndex);
            if (objectTriggerCollapse.valid)
            {
                emitObjectTriggerCollapse(lua, line, objectTriggerCollapse, indentDepth);
                lineIndex += objectTriggerCollapse.triggerLines.size();
                continue;
            }
            const Mm9LuaObjectFlagCollapse objectFlagCollapse = objectFlagCollapseAtLine(file, lineIndex);
            if (objectFlagCollapse.valid)
            {
                emitObjectFlagCollapse(lua, line, objectFlagCollapse, indentDepth);
                lineIndex += objectFlagCollapse.actions.size();
                continue;
            }
            const Mm9LuaObjectStatCollapse objectStatCollapse = objectStatCollapseAtLine(file, lineIndex);
            if (objectStatCollapse.valid)
            {
                emitObjectStatCollapse(lua, line, objectStatCollapse, indentDepth);
                lineIndex += objectStatCollapse.actions.size();
                continue;
            }
            const Mm9LuaObjectPositionCollapse objectPositionCollapse = objectPositionCollapseAtLine(file, lineIndex);
            if (objectPositionCollapse.valid)
            {
                emitObjectPositionCollapse(lua, line, objectPositionCollapse, indentDepth);
                lineIndex += objectPositionCollapse.actions.size();
                continue;
            }

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
            emitLuaCommandCall(lua, line, indentDepth, generationState);
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
    const std::set<int32_t> &knownRudeIds,
    std::ostream *pDebugStream)
{
    Mm9ObjectDialogueBindingIndex index = {};
    const std::set<std::string> scriptSourceNames = collectScriptSourceNames(scriptsDirectory);
    const std::vector<std::filesystem::path> mapFiles = listFilesWithExtension(mapsDirectory, ".yml");
    std::vector<std::filesystem::path> rawObjectMapFiles;
    for (const std::filesystem::path &path : mapFiles)
    {
        if (path.filename().string().find(".raw_objects.yml") != std::string::npos)
        {
            rawObjectMapFiles.push_back(path);
        }
    }

    for (size_t mapIndex = 0; mapIndex < rawObjectMapFiles.size(); ++mapIndex)
    {
        const std::filesystem::path &path = rawObjectMapFiles[mapIndex];
        if (pDebugStream != nullptr)
        {
            *pDebugStream << "mm9_dialogue_pipeline: map raw objects "
                          << (mapIndex + 1) << "/" << rawObjectMapFiles.size()
                          << " " << path.filename().string() << '\n';
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

void writePipelineDebug(std::ostream *pDebugStream, const std::string &message)
{
    if (pDebugStream == nullptr)
    {
        return;
    }

    *pDebugStream << "mm9_dialogue_pipeline: " << message << '\n';
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
    const std::filesystem::path &mapsDirectory,
    std::ostream *pDebugStream)
{
    Mm9DialoguePipelineResult result = {};
    std::set<std::filesystem::path> generatedPaths;
    const std::filesystem::path rudeDirectory = extractedRoot / "RUDE/RUDE";
    const std::filesystem::path scriptsDirectory = extractedRoot / "SCRIPTS/SCRIPTS";

    writePipelineDebug(pDebugStream, "scan source inventories");
    const Mm9RudeSourceInventory rudeInventory = scanMm9RudeSourceInventory(extractedRoot);
    result.errors.insert(result.errors.end(), rudeInventory.errors.begin(), rudeInventory.errors.end());
    const Mm9ScriptSourceInventory scriptInventory = scanMm9ScriptSourceInventory(extractedRoot);
    result.errors.insert(result.errors.end(), scriptInventory.errors.begin(), scriptInventory.errors.end());

    const std::vector<std::filesystem::path> rudeFiles = listFilesWithExtension(rudeDirectory, ".rude");
    writePipelineDebug(pDebugStream, "parse RUDE files " + std::to_string(rudeFiles.size()));
    for (size_t index = 0; index < rudeFiles.size(); ++index)
    {
        const std::filesystem::path &path = rudeFiles[index];
        writePipelineDebug(
            pDebugStream,
            "RUDE " + std::to_string(index + 1) + "/" + std::to_string(rudeFiles.size()) +
                " " + path.filename().string());
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

    writePipelineDebug(pDebugStream, "build key registry");
    const Mm9KeyRegistry keyRegistry = buildMm9KeyRegistry(extractedRoot);
    addGeneratedFile(result, generatedPaths, "state/keys.yml", generateMm9KeyRegistryYaml(keyRegistry));
    addGeneratedFile(result, generatedPaths, "state/defaults.yml", generateMm9StateDefaultsYaml());
    addGeneratedFile(
        result,
        generatedPaths,
        "scripts/common/mm9_script_runtime.lua",
        generateMm9ScriptRuntimeLua());

    const std::vector<std::filesystem::path> scriptFiles = listScriptFiles(scriptsDirectory);
    writePipelineDebug(pDebugStream, "generate script Lua files " + std::to_string(scriptFiles.size()));
    for (size_t index = 0; index < scriptFiles.size(); ++index)
    {
        const std::filesystem::path &path = scriptFiles[index];
        writePipelineDebug(
            pDebugStream,
            "script " + std::to_string(index + 1) + "/" + std::to_string(scriptFiles.size()) +
                " " + path.filename().string());
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

    writePipelineDebug(pDebugStream, "scan object dialogue bindings");
    const std::set<int32_t> knownRudeIds = collectKnownRudeIds(rudeDirectory);
    const Mm9ObjectDialogueBindingIndex objectBindings =
        scanMm9ObjectDialogueBindings(mapsDirectory, scriptsDirectory, knownRudeIds, pDebugStream);
    result.errors.insert(result.errors.end(), objectBindings.errors.begin(), objectBindings.errors.end());
    addGeneratedFile(
        result,
        generatedPaths,
        "maps/dialogue_bindings.yml",
        generateMm9ObjectDialogueBindingsYaml(objectBindings));

    writePipelineDebug(pDebugStream, "sort generated outputs " + std::to_string(result.files.size()));
    std::sort(
        result.files.begin(),
        result.files.end(),
        [](const Mm9DialoguePipelineGeneratedFile &left, const Mm9DialoguePipelineGeneratedFile &right)
        {
            return left.relativePath.generic_string() < right.relativePath.generic_string();
        });

    writePipelineDebug(pDebugStream, "generation complete");
    return result;
}

Mm9DialoguePipelineWriteResult writeMm9DialoguePipelineFiles(
    const std::filesystem::path &outputRoot,
    const std::vector<Mm9DialoguePipelineGeneratedFile> &files,
    bool checkOnly,
    std::ostream *pDebugStream)
{
    Mm9DialoguePipelineWriteResult result = {};
    writePipelineDebug(
        pDebugStream,
        std::string(checkOnly ? "check " : "write ") + std::to_string(files.size()) +
            " generated files to " + outputRoot.generic_string());
    for (size_t index = 0; index < files.size(); ++index)
    {
        const Mm9DialoguePipelineGeneratedFile &file = files[index];
        const std::string progress =
            std::to_string(index + 1) + "/" + std::to_string(files.size()) + " " +
            file.relativePath.generic_string();
        if (!isSafeGeneratedRelativePath(file.relativePath))
        {
            addWriteError(result, file.relativePath, "generated path is not a safe relative path");
            writePipelineDebug(pDebugStream, "error unsafe path " + progress);
            continue;
        }

        const std::filesystem::path outputPath = outputRoot / file.relativePath;
        std::string existingContents;
        if (readWholeTextFile(outputPath, existingContents) && existingContents == file.contents)
        {
            ++result.unchangedFileCount;
            writePipelineDebug(pDebugStream, "unchanged " + progress);
            continue;
        }

        if (checkOnly)
        {
            ++result.staleFileCount;
            addWriteError(result, outputPath, "generated file is missing or stale");
            writePipelineDebug(pDebugStream, "stale " + progress);
            continue;
        }

        if (!writeWholeTextFile(outputPath, file.contents))
        {
            addWriteError(result, outputPath, "could not write generated file");
            writePipelineDebug(pDebugStream, "error write failed " + progress);
            continue;
        }

        ++result.writtenFileCount;
        writePipelineDebug(pDebugStream, "written " + progress);
    }

    writePipelineDebug(pDebugStream, "write/check complete");
    return result;
}
}
