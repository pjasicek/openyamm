#include "game/mm9/Mm9ScriptRuntime.h"

#include "engine/scripting/LuaStateOwner.h"
#include "game/mm9/Mm9DialogueRuntime.h"
#include "game/mm9/Mm9InteractionRouting.h"
#include "game/party/Party.h"

#include <lua.hpp>

#include <algorithm>
#include <cctype>
#include <cstddef>
#include <cmath>
#include <cstdlib>
#include <map>
#include <optional>
#include <sstream>
#include <string>
#include <string_view>
#include <vector>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
Mm9ScriptRuntime *runtimeFromLua(lua_State *pLuaState)
{
    return static_cast<Mm9ScriptRuntime *>(lua_touserdata(pLuaState, lua_upvalueindex(1)));
}

std::optional<int32_t> parseInt(const std::string &text)
{
    if (text.empty())
    {
        return std::nullopt;
    }

    char *pEnd = nullptr;
    const long value = std::strtol(text.c_str(), &pEnd, 10);
    if (pEnd == text.c_str() || *pEnd != '\0')
    {
        return std::nullopt;
    }

    return static_cast<int32_t>(value);
}

std::optional<double> parseReal(const std::string &text)
{
    if (text.empty())
    {
        return std::nullopt;
    }

    char *pEnd = nullptr;
    const double value = std::strtod(text.c_str(), &pEnd);
    if (pEnd == text.c_str() || *pEnd != '\0')
    {
        return std::nullopt;
    }

    return value;
}

std::string realToScriptString(double value)
{
    if (std::floor(value) == value)
    {
        return std::to_string(static_cast<int32_t>(value));
    }

    std::ostringstream stream;
    stream << value;
    return stream.str();
}

std::string luaArgumentText(lua_State *pLuaState, int index)
{
    if (lua_isinteger(pLuaState, index))
    {
        return std::to_string(static_cast<int32_t>(lua_tointeger(pLuaState, index)));
    }
    if (lua_isstring(pLuaState, index))
    {
        return lua_tostring(pLuaState, index);
    }

    return {};
}

std::string luaScriptExpressionText(lua_State *pLuaState, int index)
{
    if (lua_isboolean(pLuaState, index))
    {
        return lua_toboolean(pLuaState, index) != 0 ? "true" : "false";
    }
    if (lua_isnumber(pLuaState, index))
    {
        return realToScriptString(lua_tonumber(pLuaState, index));
    }
    if (lua_isstring(pLuaState, index))
    {
        return lua_tostring(pLuaState, index);
    }

    return {};
}

std::string luaObjectProxyHandle(lua_State *pLuaState, int index)
{
    if (lua_isstring(pLuaState, index))
    {
        return lua_tostring(pLuaState, index);
    }
    if (!lua_istable(pLuaState, index))
    {
        return {};
    }

    lua_getfield(pLuaState, index, "__mm9Handle");
    const std::string handle = lua_isstring(pLuaState, -1) ? lua_tostring(pLuaState, -1) : "";
    lua_pop(pLuaState, 1);
    return handle;
}

std::optional<int32_t> luaRawKeyId(lua_State *pLuaState, int index, const Mm9ScriptRuntime &runtime)
{
    if (lua_isinteger(pLuaState, index))
    {
        return static_cast<int32_t>(lua_tointeger(pLuaState, index));
    }
    if (lua_isstring(pLuaState, index))
    {
        return runtime.resolveRawKeyId(lua_tostring(pLuaState, index));
    }

    return std::nullopt;
}

size_t luaMetadataLine(lua_State *pLuaState, int index)
{
    if (index <= 0)
    {
        return 0;
    }
    if (!lua_istable(pLuaState, index))
    {
        return 0;
    }

    lua_getfield(pLuaState, index, "line");
    const size_t line = lua_isinteger(pLuaState, -1)
        ? static_cast<size_t>(lua_tointeger(pLuaState, -1))
        : 0;
    lua_pop(pLuaState, 1);
    return line;
}

std::string luaMetadataRaw(lua_State *pLuaState, int index)
{
    if (index <= 0)
    {
        return {};
    }
    if (!lua_istable(pLuaState, index))
    {
        return {};
    }

    lua_getfield(pLuaState, index, "raw");
    const std::string raw = lua_isstring(pLuaState, -1) ? lua_tostring(pLuaState, -1) : "";
    lua_pop(pLuaState, 1);
    return raw;
}

std::string luaMetadataArgs(lua_State *pLuaState, int index)
{
    if (index <= 0)
    {
        return {};
    }
    if (!lua_istable(pLuaState, index))
    {
        return {};
    }

    lua_getfield(pLuaState, index, "args");
    const std::string args = lua_isstring(pLuaState, -1) ? lua_tostring(pLuaState, -1) : "";
    lua_pop(pLuaState, 1);
    return args;
}

std::vector<std::string> splitScriptArguments(const std::string &argumentsText);
std::vector<std::string> splitWhitespaceScriptArguments(const std::string &text);
std::string trimCopy(const std::string &text);

std::vector<std::string> luaCommandArguments(lua_State *pLuaState, int metadataIndex, int firstArgumentIndex)
{
    const std::vector<std::string> metadataArguments = splitScriptArguments(luaMetadataArgs(pLuaState, metadataIndex));
    if (!metadataArguments.empty())
    {
        return metadataArguments;
    }

    std::vector<std::string> arguments;
    const int top = lua_gettop(pLuaState);
    for (int index = firstArgumentIndex; index <= top; ++index)
    {
        if (index == metadataIndex && lua_istable(pLuaState, index))
        {
            continue;
        }
        if (lua_istable(pLuaState, index))
        {
            continue;
        }

        const std::string argument = luaArgumentText(pLuaState, index);
        if (!argument.empty() || lua_isnumber(pLuaState, index) || lua_isboolean(pLuaState, index))
        {
            arguments.push_back(argument);
        }
    }
    return arguments;
}

std::vector<std::string> luaServiceArguments(lua_State *pLuaState, int metadataIndex, int firstArgumentIndex)
{
    const std::vector<std::string> metadataArguments = splitScriptArguments(luaMetadataArgs(pLuaState, metadataIndex));
    if (!metadataArguments.empty())
    {
        return metadataArguments;
    }

    std::vector<std::string> arguments;
    const int top = lua_gettop(pLuaState);
    for (int index = firstArgumentIndex; index <= top; ++index)
    {
        if (index == metadataIndex && lua_istable(pLuaState, index))
        {
            continue;
        }
        if (lua_istable(pLuaState, index))
        {
            continue;
        }
        if (lua_isstring(pLuaState, index) || lua_isnumber(pLuaState, index) || lua_isboolean(pLuaState, index))
        {
            arguments.push_back(luaScriptExpressionText(pLuaState, index));
        }
    }
    return arguments;
}

std::vector<std::string> luaMovementArguments(lua_State *pLuaState, int metadataIndex, int firstArgumentIndex)
{
    const std::vector<std::string> metadataArguments = splitScriptArguments(luaMetadataArgs(pLuaState, metadataIndex));
    if (!metadataArguments.empty())
    {
        return metadataArguments;
    }

    std::vector<std::string> arguments;
    const int top = lua_gettop(pLuaState);
    for (int index = firstArgumentIndex; index <= top; ++index)
    {
        if (index == metadataIndex && lua_istable(pLuaState, index))
        {
            continue;
        }
        if (lua_istable(pLuaState, index))
        {
            const std::string handle = luaObjectProxyHandle(pLuaState, index);
            if (!handle.empty())
            {
                arguments.push_back(handle);
            }
            continue;
        }
        if (lua_isstring(pLuaState, index) || lua_isnumber(pLuaState, index) || lua_isboolean(pLuaState, index))
        {
            arguments.push_back(luaScriptExpressionText(pLuaState, index));
        }
    }
    return arguments;
}

int luaTrailingMetadataIndex(lua_State *pLuaState)
{
    const int top = lua_gettop(pLuaState);
    return top > 0 && lua_istable(pLuaState, top) ? top : 0;
}

std::string scriptArgumentsText(const std::vector<std::string> &arguments)
{
    std::string result;
    for (size_t index = 0; index < arguments.size(); ++index)
    {
        if (index != 0)
        {
            result += ", ";
        }
        result += arguments[index];
    }
    return result;
}

std::vector<std::string> normalizedWaitArguments(const std::vector<std::string> &arguments)
{
    if (arguments.size() != 2)
    {
        return arguments;
    }

    const std::vector<std::string> firstArguments = splitWhitespaceScriptArguments(arguments[0]);
    if (firstArguments.size() == 2)
    {
        return { firstArguments[0], firstArguments[1], arguments[1] };
    }

    const std::vector<std::string> secondArguments = splitWhitespaceScriptArguments(arguments[1]);
    if (secondArguments.size() == 2)
    {
        return { arguments[0], secondArguments[0], secondArguments[1] };
    }

    return { arguments[0], arguments[0], arguments[1] };
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
            if (!trimmed.empty())
            {
                result.push_back(trimmed);
            }
            continue;
        }

        result.insert(result.end(), parts.begin(), parts.end());
    }
    return result;
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
    std::string result = text;
    for (char &ch : result)
    {
        ch = static_cast<char>(std::tolower(static_cast<unsigned char>(ch)));
    }
    return result;
}

std::map<std::string, Mm9GeneratedScriptFile>::const_iterator findScriptFile(
    const Mm9DialoguePackage &package,
    const std::string &scriptSource)
{
    const auto exactIterator = package.scripts.find(scriptSource);
    if (exactIterator != package.scripts.end())
    {
        return exactIterator;
    }

    const std::string loweredSource = lowerCopy(scriptSource);
    return std::find_if(
        package.scripts.begin(),
        package.scripts.end(),
        [&](const std::pair<const std::string, Mm9GeneratedScriptFile> &scriptPair)
        {
            return lowerCopy(scriptPair.first) == loweredSource;
        });
}

std::string unquoteScriptString(const std::string &text)
{
    const std::string trimmed = trimCopy(text);
    if (trimmed.size() >= 2 && trimmed.front() == '"' && trimmed.back() == '"')
    {
        return trimmed.substr(1, trimmed.size() - 2);
    }

    return trimmed;
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

bool pushMm9ScriptRuntimeSupport(
    lua_State *pLuaState,
    const Mm9DialoguePackage &package,
    std::optional<std::string> &errorMessage)
{
    if (package.scriptRuntimeLuaText.empty())
    {
        errorMessage = "missing generated MM9 script runtime support";
        return false;
    }

    const std::string chunkName = "scripts/common/mm9_script_runtime.lua";
    if (luaL_loadbuffer(
            pLuaState,
            package.scriptRuntimeLuaText.c_str(),
            package.scriptRuntimeLuaText.size(),
            chunkName.c_str()) != LUA_OK)
    {
        errorMessage = lua_tostring(pLuaState, -1);
        lua_pop(pLuaState, 1);
        return false;
    }

    if (lua_pcall(pLuaState, 0, 1, 0) != LUA_OK)
    {
        errorMessage = lua_tostring(pLuaState, -1);
        lua_pop(pLuaState, 1);
        return false;
    }

    if (!lua_istable(pLuaState, -1))
    {
        errorMessage = "generated MM9 script runtime support did not return a table";
        lua_pop(pLuaState, 1);
        return false;
    }

    lua_setglobal(pLuaState, "mm9ScriptRuntime");
    return true;
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

std::string firstScriptArgument(const std::string &argumentsText, std::string &remainingArguments)
{
    const std::vector<std::string> arguments = splitWhitespaceScriptArguments(argumentsText);
    if (arguments.empty())
    {
        remainingArguments.clear();
        return {};
    }

    const std::string first = arguments.front();
    const size_t firstOffset = argumentsText.find(first);
    if (firstOffset == std::string::npos)
    {
        remainingArguments.clear();
        return first;
    }

    remainingArguments = trimCopy(argumentsText.substr(firstOffset + first.size()));
    return first;
}

std::string rawAssignmentTarget(const std::string &command, const std::string &rawLine)
{
    const size_t equals = rawLine.find('=');
    if (equals == std::string::npos)
    {
        return command;
    }

    return trimCopy(rawLine.substr(0, equals));
}

std::map<std::string, int32_t>::iterator findCaseInsensitiveStat(
    std::map<std::string, int32_t> &stats,
    const std::string &name)
{
    const std::string loweredName = lowerCopy(trimCopy(name));
    return std::find_if(
        stats.begin(),
        stats.end(),
        [&](const std::pair<const std::string, int32_t> &stat)
        {
            return lowerCopy(stat.first) == loweredName;
        });
}

std::optional<std::pair<std::string, int32_t>> mm9ObjectHandleParts(const std::string &handle)
{
    static const std::string prefix = "mm9:";
    static const std::string marker = ":object:";
    if (handle.compare(0, prefix.size(), prefix) != 0)
    {
        return std::nullopt;
    }

    const size_t markerOffset = handle.find(marker, prefix.size());
    if (markerOffset == std::string::npos)
    {
        return std::nullopt;
    }

    const std::string mapId = handle.substr(prefix.size(), markerOffset - prefix.size());
    const std::optional<int32_t> objectIndex = parseInt(handle.substr(markerOffset + marker.size()));
    if (!objectIndex)
    {
        return std::nullopt;
    }

    return std::make_pair(mapId, *objectIndex);
}

std::string objectNumberPropertyKeyForHandle(const std::string &handle, const std::string &propertyName)
{
    const std::optional<std::pair<std::string, int32_t>> parts = mm9ObjectHandleParts(handle);
    const std::string trimmedPropertyName = trimCopy(propertyName);
    if (!parts || trimmedPropertyName.empty())
    {
        return {};
    }

    return parts->first + ":" + std::to_string(parts->second) + ":" + trimmedPropertyName;
}

std::string normalizedObjectFlagName(const std::string &flagName)
{
    std::string flag = lowerCopy(trimCopy(flagName));
    constexpr std::string_view prefix = "flag_";
    if (flag.rfind(prefix, 0) == 0)
    {
        flag = flag.substr(prefix.size());
    }
    return flag;
}

bool objectFlagValue(
    const Mm9ScriptRuntimeState &state,
    const std::string &handle,
    const std::string &flagName,
    bool defaultValue)
{
    const std::string normalizedFlag = normalizedObjectFlagName(flagName);
    const auto objectIterator = state.objectFlags.find(handle);
    if (objectIterator == state.objectFlags.end())
    {
        return defaultValue;
    }

    const auto flagIterator = objectIterator->second.find(normalizedFlag);
    return flagIterator != objectIterator->second.end() ? flagIterator->second != 0 : defaultValue;
}

enum class Mm9ScriptValueKind
{
    Null,
    Number,
    String,
    Handle,
};

struct Mm9ScriptValue
{
    Mm9ScriptValueKind kind = Mm9ScriptValueKind::Null;
    double number = 0.0;
    std::string text;
};

Mm9ScriptValue evaluateScriptExpression(const Mm9ScriptRuntime &runtime, const std::string &expression);
Mm9ScriptValue scriptValueFromLua(lua_State *pLuaState, int index);
std::string objectHandleFromLua(Mm9ScriptRuntime &runtime, lua_State *pLuaState, int index);
void pushObjectProxy(lua_State *pLuaState, Mm9ScriptRuntime &runtime, const std::string &handle);

Mm9ScriptValue nullValue()
{
    return {};
}

Mm9ScriptValue numberValue(double value)
{
    Mm9ScriptValue result = {};
    result.kind = Mm9ScriptValueKind::Number;
    result.number = value;
    result.text = realToScriptString(value);
    return result;
}

Mm9ScriptValue stringValue(const std::string &value)
{
    Mm9ScriptValue result = {};
    result.kind = Mm9ScriptValueKind::String;
    result.text = value;
    return result;
}

Mm9ScriptValue handleValue(const std::string &value)
{
    Mm9ScriptValue result = {};
    result.kind = value.empty() ? Mm9ScriptValueKind::Null : Mm9ScriptValueKind::Handle;
    result.text = value;
    return result;
}

bool looksLikeMm9HandleVariableName(const std::string &name)
{
    const std::string trimmed = trimCopy(name);
    const std::string lowered = lowerCopy(trimmed);
    if (lowered.rfind("g_h", 0) == 0)
    {
        return true;
    }

    return trimmed.size() > 1 && trimmed.front() == 'h'
        && std::isupper(static_cast<unsigned char>(trimmed[1])) != 0;
}

bool scriptValueTruthy(const Mm9ScriptValue &value)
{
    if (value.kind == Mm9ScriptValueKind::Null)
    {
        return false;
    }

    if (value.kind == Mm9ScriptValueKind::Number)
    {
        return value.number != 0.0;
    }

    return !value.text.empty() && lowerCopy(value.text) != "false" && lowerCopy(value.text) != "null";
}

double scriptValueNumber(const Mm9ScriptValue &value)
{
    if (value.kind == Mm9ScriptValueKind::Number)
    {
        return value.number;
    }

    const std::optional<double> parsed = parseReal(value.text);
    return parsed.value_or(scriptValueTruthy(value) ? 1.0 : 0.0);
}

std::string scriptValueString(const Mm9ScriptValue &value)
{
    if (value.kind == Mm9ScriptValueKind::Null)
    {
        return {};
    }

    if (value.kind == Mm9ScriptValueKind::Number)
    {
        return realToScriptString(value.number);
    }

    return value.text;
}

bool scriptValueBool(const Mm9ScriptValue &value)
{
    return scriptValueTruthy(value);
}

bool isCallbackLabel(const std::string &label)
{
    const std::string lowered = lowerCopy(trimCopy(label));
    return !lowered.empty() && lowered != "donothing" && lowered != "none" && lowered != "null"
        && lowered != "false";
}

int32_t scriptArgumentNumber(
    const Mm9ScriptRuntime &runtime,
    const std::vector<std::string> &arguments,
    size_t index,
    int32_t defaultValue = 0)
{
    if (index >= arguments.size() || trimCopy(arguments[index]).empty())
    {
        return defaultValue;
    }

    return static_cast<int32_t>(scriptValueNumber(evaluateScriptExpression(runtime, arguments[index])));
}

bool scriptArgumentBool(
    const Mm9ScriptRuntime &runtime,
    const std::vector<std::string> &arguments,
    size_t index,
    bool defaultValue = false)
{
    if (index >= arguments.size() || trimCopy(arguments[index]).empty())
    {
        return defaultValue;
    }

    return scriptValueBool(evaluateScriptExpression(runtime, arguments[index]));
}

Mm9ScriptRuntimeVec3 scriptVectorFromArguments(
    const Mm9ScriptRuntime &runtime,
    const std::vector<std::string> &arguments,
    size_t offset)
{
    Mm9ScriptRuntimeVec3 result = {};
    result.x = scriptArgumentNumber(runtime, arguments, offset);
    result.y = scriptArgumentNumber(runtime, arguments, offset + 1);
    result.z = scriptArgumentNumber(runtime, arguments, offset + 2);
    return result;
}

double scriptVectorDistance(const Mm9ScriptRuntimeVec3 &a, const Mm9ScriptRuntimeVec3 &b)
{
    const double dx = a.x - b.x;
    const double dy = a.y - b.y;
    const double dz = a.z - b.z;
    return std::sqrt((dx * dx) + (dy * dy) + (dz * dz));
}

Mm9ScriptRuntimeVec3 objectDirectionVector(
    const Mm9ScriptRuntimeState &state,
    const std::string &handle,
    const std::string &operation)
{
    const auto directionIterator = state.objectFaceDirs.find(handle);
    Mm9ScriptRuntimeVec3 direction =
        directionIterator != state.objectFaceDirs.end() ? directionIterator->second : Mm9ScriptRuntimeVec3();
    if (operation == "rightdir")
    {
        return {direction.y, -direction.x, direction.z};
    }
    if (operation == "leftdir")
    {
        return {-direction.y, direction.x, direction.z};
    }
    if (operation == "reversedir")
    {
        return {-direction.x, -direction.y, -direction.z};
    }

    return direction;
}

double scheduledDelaySeconds(double minDelay, double maxDelay)
{
    const double low = std::max(0.0, std::min(minDelay, maxDelay));
    const double high = std::max(0.0, std::max(minDelay, maxDelay));
    if (high <= low)
    {
        return low;
    }

    const double t = static_cast<double>(std::rand()) / static_cast<double>(RAND_MAX);
    return low + ((high - low) * t);
}

void scriptClockHourMinute(double scriptTimeSeconds, int32_t &hour, int32_t &minute)
{
    const int32_t secondsPerDay = 24 * 60 * 60;
    int32_t wholeSeconds = static_cast<int32_t>(std::floor(std::max(0.0, scriptTimeSeconds)));
    wholeSeconds %= secondsPerDay;

    int32_t totalMinutes = wholeSeconds / 60;
    const int32_t roundedQuarter = static_cast<int32_t>(std::round(static_cast<double>(totalMinutes) / 15.0)) * 15;
    totalMinutes = roundedQuarter % (24 * 60);
    hour = totalMinutes / 60;
    minute = totalMinutes % 60;
}

int32_t mm9AttributeIdFromArgument(const Mm9ScriptRuntime &runtime, const std::string &argument)
{
    const std::string lowered = lowerCopy(trimCopy(argument));
    if (lowered == "stat_might" || lowered == "player_might")
    {
        return 0;
    }
    if (lowered == "stat_magic" || lowered == "player_magic")
    {
        return 1;
    }
    if (lowered == "stat_endurance" || lowered == "player_endurance")
    {
        return 2;
    }
    if (lowered == "stat_accuracy" || lowered == "player_accuracy")
    {
        return 3;
    }
    if (lowered == "stat_speed" || lowered == "player_speed")
    {
        return 4;
    }
    if (lowered == "stat_luck" || lowered == "player_luck")
    {
        return 5;
    }

    return static_cast<int32_t>(scriptValueNumber(evaluateScriptExpression(runtime, argument)));
}

int32_t mm9CharacterAttributeValue(const Character &member, int32_t attributeId)
{
    switch (attributeId)
    {
        case 0:
            return static_cast<int32_t>(member.might)
                + member.permanentBonuses.might
                + member.magicalBonuses.might;
        case 1:
            return static_cast<int32_t>(member.intellect)
                + member.permanentBonuses.intellect
                + member.magicalBonuses.intellect;
        case 2:
            return static_cast<int32_t>(member.endurance)
                + member.permanentBonuses.endurance
                + member.magicalBonuses.endurance;
        case 3:
            return static_cast<int32_t>(member.accuracy)
                + member.permanentBonuses.accuracy
                + member.magicalBonuses.accuracy;
        case 4:
            return static_cast<int32_t>(member.speed)
                + member.permanentBonuses.speed
                + member.magicalBonuses.speed;
        case 5:
            return static_cast<int32_t>(member.luck)
                + member.permanentBonuses.luck
                + member.magicalBonuses.luck;
        default:
            return 0;
    }
}

void applyMm9CharacterAttributeBonus(Character &member, int32_t attributeId, int32_t amount, bool permanent)
{
    CharacterStatBonuses &bonuses = permanent ? member.permanentBonuses : member.magicalBonuses;
    switch (attributeId)
    {
        case 0:
            bonuses.might += amount;
            break;
        case 1:
            bonuses.intellect += amount;
            break;
        case 2:
            bonuses.endurance += amount;
            break;
        case 3:
            bonuses.accuracy += amount;
            break;
        case 4:
            bonuses.speed += amount;
            break;
        case 5:
            bonuses.luck += amount;
            break;
        default:
            break;
    }
}

std::string normalizeControlConditionText(const std::string &command, const std::string &argumentsText)
{
    std::string text = trimCopy(argumentsText);
    const std::string normalizedCommand = lowerCopy(trimCopy(command));
    if (normalizedCommand == "if(" || normalizedCommand == "while(")
    {
        text = "(" + text;
    }

    if (!text.empty() && text.back() == ',')
    {
        text.pop_back();
    }

    return trimCopy(text);
}

bool parseMm9MinuteSchedule(
    const Mm9ScriptRuntime &runtime,
    const std::vector<std::string> &arguments,
    double &hour,
    double &minute,
    size_t &labelOffset)
{
    labelOffset = 0;
    hour = 0.0;
    minute = 0.0;
    if (arguments.empty())
    {
        return false;
    }

    const std::vector<std::string> firstTokens = splitWhitespaceScriptArguments(arguments[0]);
    if (firstTokens.size() >= 3 && firstTokens[1] == ":")
    {
        hour = scriptValueNumber(evaluateScriptExpression(runtime, firstTokens[0]));
        minute = scriptValueNumber(evaluateScriptExpression(runtime, firstTokens[2]));
        labelOffset = 3;
        return true;
    }

    const size_t colon = arguments[0].find(':');
    if (colon != std::string::npos)
    {
        hour = scriptValueNumber(evaluateScriptExpression(runtime, trimCopy(arguments[0].substr(0, colon))));
        minute = scriptValueNumber(evaluateScriptExpression(runtime, trimCopy(arguments[0].substr(colon + 1))));
        labelOffset = 1;
        return true;
    }

    if (firstTokens.size() >= 2 && !firstTokens[1].empty() && firstTokens[1].front() == ':')
    {
        hour = scriptValueNumber(evaluateScriptExpression(runtime, firstTokens[0]));
        minute = scriptValueNumber(evaluateScriptExpression(runtime, trimCopy(firstTokens[1].substr(1))));
        labelOffset = 2;
        return true;
    }

    return false;
}

std::vector<std::string> labelsAfterMm9MinuteSchedule(const std::vector<std::string> &arguments, size_t labelOffset)
{
    if (arguments.empty())
    {
        return {};
    }

    std::vector<std::string> labels;
    const std::vector<std::string> firstTokens = splitWhitespaceScriptArguments(arguments[0]);
    if (labelOffset < firstTokens.size())
    {
        labels.insert(labels.end(), firstTokens.begin() + static_cast<ptrdiff_t>(labelOffset), firstTokens.end());
    }
    for (size_t index = 1; index < arguments.size(); ++index)
    {
        const std::vector<std::string> tokens = splitWhitespaceScriptArguments(arguments[index]);
        labels.insert(labels.end(), tokens.begin(), tokens.end());
    }
    return labels;
}

class Mm9ExpressionParser
{
public:
    Mm9ExpressionParser(const Mm9ScriptRuntime &runtime, const std::string &text)
        : m_runtime(runtime)
        , m_text(text)
    {
    }

    Mm9ScriptValue parse()
    {
        return parseComparison();
    }

private:
    Mm9ScriptValue parseComparison()
    {
        Mm9ScriptValue left = parseAddSub();
        skipSpaces();

        while (true)
        {
            const std::string op = readComparisonOperator();
            if (op.empty())
            {
                return left;
            }

            Mm9ScriptValue right = parseAddSub();
            const bool numeric = left.kind == Mm9ScriptValueKind::Number || right.kind == Mm9ScriptValueKind::Number
                || parseReal(left.text).has_value() || parseReal(right.text).has_value();
            bool result = false;
            if (numeric)
            {
                const double l = scriptValueNumber(left);
                const double r = scriptValueNumber(right);
                if (op == "==")
                {
                    result = l == r;
                }
                else if (op == "!=")
                {
                    result = l != r;
                }
                else if (op == "<")
                {
                    result = l < r;
                }
                else if (op == "<=")
                {
                    result = l <= r;
                }
                else if (op == ">")
                {
                    result = l > r;
                }
                else if (op == ">=")
                {
                    result = l >= r;
                }
            }
            else
            {
                const std::string l = scriptValueString(left);
                const std::string r = scriptValueString(right);
                if (op == "==")
                {
                    result = l == r;
                }
                else if (op == "!=")
                {
                    result = l != r;
                }
                else if (op == "<")
                {
                    result = l < r;
                }
                else if (op == "<=")
                {
                    result = l <= r;
                }
                else if (op == ">")
                {
                    result = l > r;
                }
                else if (op == ">=")
                {
                    result = l >= r;
                }
            }

            left = numberValue(result ? 1.0 : 0.0);
            skipSpaces();
        }
    }

    Mm9ScriptValue parseAddSub()
    {
        Mm9ScriptValue left = parseMulDiv();
        skipSpaces();

        while (peek() == '+' || peek() == '-')
        {
            const char op = m_text[m_offset++];
            Mm9ScriptValue right = parseMulDiv();
            if (op == '+'
                && (left.kind == Mm9ScriptValueKind::String || left.kind == Mm9ScriptValueKind::Handle
                    || right.kind == Mm9ScriptValueKind::String || right.kind == Mm9ScriptValueKind::Handle))
            {
                left = stringValue(scriptValueString(left) + scriptValueString(right));
            }
            else if (op == '+')
            {
                left = numberValue(scriptValueNumber(left) + scriptValueNumber(right));
            }
            else
            {
                left = numberValue(scriptValueNumber(left) - scriptValueNumber(right));
            }
            skipSpaces();
        }

        return left;
    }

    Mm9ScriptValue parseMulDiv()
    {
        Mm9ScriptValue left = parseUnary();
        skipSpaces();

        while (peek() == '*' || peek() == '/')
        {
            const char op = m_text[m_offset++];
            Mm9ScriptValue right = parseUnary();
            if (op == '*')
            {
                left = numberValue(scriptValueNumber(left) * scriptValueNumber(right));
            }
            else
            {
                const double divisor = scriptValueNumber(right);
                left = numberValue(divisor == 0.0 ? 0.0 : scriptValueNumber(left) / divisor);
            }
            skipSpaces();
        }

        return left;
    }

    Mm9ScriptValue parseUnary()
    {
        skipSpaces();
        if (peek() == '-')
        {
            ++m_offset;
            return numberValue(-scriptValueNumber(parseUnary()));
        }

        return parsePrimary();
    }

    Mm9ScriptValue parsePrimary()
    {
        skipSpaces();
        if (peek() == '(')
        {
            ++m_offset;
            Mm9ScriptValue value = parseComparison();
            skipSpaces();
            if (peek() == ')')
            {
                ++m_offset;
            }
            return value;
        }

        if (peek() == '"')
        {
            return stringValue(readQuoted());
        }

        const std::string token = readToken();
        if (token.empty())
        {
            return nullValue();
        }

        return resolveToken(token);
    }

    Mm9ScriptValue resolveToken(const std::string &token) const
    {
        const std::string trimmed = trimCopy(token);
        const std::string lowered = lowerCopy(trimmed);
        if (lowered == "true")
        {
            return numberValue(1.0);
        }
        if (lowered == "false")
        {
            return numberValue(0.0);
        }
        if (lowered == "null")
        {
            return nullValue();
        }

        const std::optional<double> parsed = parseReal(trimmed);
        if (parsed)
        {
            return numberValue(*parsed);
        }

        const std::string missingHandle = "\x1f";
        const std::string handle = m_runtime.getObjectHandleVar(trimmed, missingHandle);
        if (handle != missingHandle)
        {
            return handleValue(handle);
        }

        if (lowered == "hme" || lowered == "g_hmyobject")
        {
            return handleValue(m_runtime.resolveScriptString(trimmed));
        }
        if (lowered == "hplayer" || lowered == "player")
        {
            return handleValue("mm9:player");
        }

        const std::string scriptString = m_runtime.getScriptStrVar(trimmed);
        if (!scriptString.empty())
        {
            return stringValue(scriptString);
        }

        const std::string consoleString = m_runtime.getConsoleStrVar(trimmed);
        if (!consoleString.empty())
        {
            return stringValue(consoleString);
        }

        const int32_t missingSentinel = -2147483647;
        const int32_t scriptNumber = m_runtime.getScriptNumVar(trimmed, missingSentinel);
        if (scriptNumber != missingSentinel)
        {
            return numberValue(scriptNumber);
        }

        const int32_t consoleNumber = m_runtime.getConsoleNumVar(trimmed, missingSentinel);
        if (consoleNumber != missingSentinel)
        {
            return numberValue(consoleNumber);
        }

        if (looksLikeMm9HandleVariableName(trimmed))
        {
            return nullValue();
        }

        return stringValue(trimmed);
    }

    char peek() const
    {
        return m_offset < m_text.size() ? m_text[m_offset] : '\0';
    }

    void skipSpaces()
    {
        while (m_offset < m_text.size() && std::isspace(static_cast<unsigned char>(m_text[m_offset])) != 0)
        {
            ++m_offset;
        }
    }

    std::string readComparisonOperator()
    {
        skipSpaces();
        static const std::vector<std::string> ops = {"==", "!=", "<=", ">=", "<", ">"};
        for (const std::string &op : ops)
        {
            if (m_text.compare(m_offset, op.size(), op) == 0)
            {
                m_offset += op.size();
                return op;
            }
        }

        return {};
    }

    std::string readQuoted()
    {
        if (peek() != '"')
        {
            return {};
        }

        ++m_offset;
        std::string value;
        while (m_offset < m_text.size())
        {
            const char ch = m_text[m_offset++];
            if (ch == '"')
            {
                break;
            }
            value.push_back(ch);
        }
        return value;
    }

    std::string readToken()
    {
        skipSpaces();
        std::string token;
        while (m_offset < m_text.size())
        {
            const char ch = m_text[m_offset];
            if (std::isspace(static_cast<unsigned char>(ch)) != 0 || ch == '(' || ch == ')' || ch == '+'
                || ch == '-' || ch == '*' || ch == '/' || ch == '<' || ch == '>' || ch == '=' || ch == '!')
            {
                break;
            }

            token.push_back(ch);
            ++m_offset;
        }
        return token;
    }

    const Mm9ScriptRuntime &m_runtime;
    const std::string &m_text;
    size_t m_offset = 0;
};

Mm9ScriptValue evaluateScriptExpression(const Mm9ScriptRuntime &runtime, const std::string &expression)
{
    Mm9ExpressionParser parser(runtime, expression);
    return parser.parse();
}

void setScriptVariableFromValue(Mm9ScriptRuntime &runtime, const std::string &name, const Mm9ScriptValue &value)
{
    if (name.empty())
    {
        return;
    }

    if (value.kind == Mm9ScriptValueKind::Handle)
    {
        runtime.setObjectHandleVar(name, value.text);
        return;
    }

    if (value.kind == Mm9ScriptValueKind::Null)
    {
        runtime.setScriptNumVar(name, 0);
        runtime.setScriptStrVar(name, "");
        runtime.setObjectHandleVar(name, "");
        return;
    }

    if (value.kind == Mm9ScriptValueKind::Number)
    {
        runtime.clearObjectHandleVar(name);
        runtime.setScriptNumVar(name, static_cast<int32_t>(value.number));
        runtime.setScriptStrVar(name, realToScriptString(value.number));
        return;
    }

    runtime.clearObjectHandleVar(name);
    runtime.setScriptStrVar(name, value.text);
    const std::optional<int32_t> parsed = parseInt(value.text);
    if (parsed)
    {
        runtime.setScriptNumVar(name, *parsed);
    }
}

std::optional<int32_t> rawKeyIdFromArguments(const Mm9ScriptRuntime &runtime, const std::vector<std::string> &arguments)
{
    for (const std::string &argument : arguments)
    {
        if (trimCopy(argument).empty())
        {
            continue;
        }

        const std::optional<int32_t> rawKeyId = runtime.resolveRawKeyId(trimCopy(argument));
        if (rawKeyId)
        {
            return rawKeyId;
        }
    }

    return std::nullopt;
}

uint32_t unsignedIdFromArgument(const Mm9ScriptRuntime &runtime, const std::string &argument)
{
    return static_cast<uint32_t>(std::max(0.0, scriptValueNumber(evaluateScriptExpression(runtime, argument))));
}

int32_t consoleNumValueFromToken(const std::string &token)
{
    const std::string trimmed = trimCopy(token);
    const std::string lowered = lowerCopy(trimmed);
    if (lowered == "true")
    {
        return 1;
    }
    if (lowered == "false")
    {
        return 0;
    }

    return parseInt(trimmed).value_or(0);
}

int32_t scriptNumberValueFromToken(const Mm9ScriptRuntime &runtime, const std::string &token)
{
    const std::string trimmed = trimCopy(token);
    const std::string lowered = lowerCopy(trimmed);
    if (lowered == "true")
    {
        return 1;
    }
    if (lowered == "false")
    {
        return 0;
    }

    return runtime.resolveScriptNumber(trimmed);
}

std::string consoleStrValueFromToken(const std::string &token)
{
    const std::string trimmed = trimCopy(token);
    if (trimmed.size() >= 2 && trimmed.front() == '"' && trimmed.back() == '"')
    {
        return trimmed.substr(1, trimmed.size() - 2);
    }

    return trimmed;
}

void setScriptVariableFromString(Mm9ScriptRuntime &runtime, const std::string &name, const std::string &value)
{
    if (name.empty())
    {
        return;
    }

    runtime.clearObjectHandleVar(name);
    runtime.setScriptStrVar(name, value);
    const std::optional<int32_t> parsed = parseInt(value);
    if (parsed)
    {
        runtime.setScriptNumVar(name, *parsed);
    }
}

void recordUnresolvedKnownCommand(lua_State *pLuaState, const std::string &command)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return;
    }

    pRuntime->recordUnimplementedCommand(
        command,
        luaArgumentText(pLuaState, 2),
        luaMetadataLine(pLuaState, 3),
        luaMetadataRaw(pLuaState, 3));
}

int luaDoRude(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushboolean(pLuaState, false);
        return 1;
    }

    const std::optional<int32_t> rudeId = luaRawKeyId(pLuaState, 2, *pRuntime);
    if (!rudeId)
    {
        recordUnresolvedKnownCommand(pLuaState, "doRude");
        lua_pushboolean(pLuaState, false);
        return 1;
    }

    lua_pushboolean(pLuaState, pRuntime->dialogueRuntime().enterRudeId(
        *rudeId,
        pRuntime->dialogueRuntime().owner()));
    return 1;
}

int luaOnRudeExit(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const std::string label = luaArgumentText(pLuaState, 2);
    if (!label.empty())
    {
        pRuntime->dialogueRuntime().setOnRudeExitLabel(label);
        pRuntime->registerCallback(label, luaMetadataLine(pLuaState, 4), "OnRudeExit");
    }

    return 0;
}

int luaOnEvent(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const std::string eventName = luaArgumentText(pLuaState, 2);
    if (eventName.empty())
    {
        return 0;
    }

    const int top = lua_gettop(pLuaState);
    const std::string selector = top >= 4 ? luaScriptExpressionText(pLuaState, 3) : "";
    const std::string label = top >= 4 ? luaArgumentText(pLuaState, 4) : luaArgumentText(pLuaState, 3);
    pRuntime->registerCallback(label, luaMetadataLine(pLuaState, top >= 5 ? 5 : 4), eventName, selector);
    return 0;
}

int luaAddModelKey(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    pRuntime->registerCallback(
        luaArgumentText(pLuaState, 3),
        luaMetadataLine(pLuaState, 4),
        "AddModelKey",
        luaScriptExpressionText(pLuaState, 2));
    return 0;
}

int luaRemoveModelKey(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    pRuntime->removeCallbackRegistrations("addmodelkey", luaScriptExpressionText(pLuaState, 2));
    return 0;
}

int luaSetCallback(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    pRuntime->registerCallback(
        luaArgumentText(pLuaState, 3),
        luaMetadataLine(pLuaState, 4),
        "SetCallBack",
        luaScriptExpressionText(pLuaState, 2));
    return 0;
}

int luaKillCallback(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    pRuntime->removeCallbackRegistrations("setcallback", luaScriptExpressionText(pLuaState, 2));
    return 0;
}

int luaDebugOut(lua_State *pLuaState)
{
    return 0;
}

int luaCPrint(lua_State *pLuaState)
{
    return 0;
}

bool executeReadableCommand(lua_State *pLuaState, const std::string &command, int firstArgumentIndex)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return false;
    }

    const int metadataIndex = luaTrailingMetadataIndex(pLuaState);
    const std::vector<std::string> arguments =
        luaCommandArguments(pLuaState, metadataIndex, firstArgumentIndex);
    return pRuntime->executeCommand(
        command,
        scriptArgumentsText(arguments),
        luaMetadataLine(pLuaState, metadataIndex),
        {});
}

int luaAtTime(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const int metadataIndex = luaTrailingMetadataIndex(pLuaState);
    const std::vector<std::string> arguments = luaCommandArguments(pLuaState, metadataIndex, 2);
    if (arguments.size() < 2)
    {
        recordUnresolvedKnownCommand(pLuaState, "atTime");
        return 0;
    }

    std::string argumentsText = arguments[0] + " : " + arguments[1];
    for (size_t index = 2; index < arguments.size(); ++index)
    {
        argumentsText += ", " + arguments[index];
    }

    if (!pRuntime->executeCommand("@m", argumentsText, luaMetadataLine(pLuaState, metadataIndex), {}))
    {
        recordUnresolvedKnownCommand(pLuaState, "atTime");
    }
    return 0;
}

int luaDoCallback(lua_State *pLuaState)
{
    if (!executeReadableCommand(pLuaState, "DoCallback", 2))
    {
        recordUnresolvedKnownCommand(pLuaState, "doCallback");
    }
    return 0;
}

int luaExitScript(lua_State *pLuaState)
{
    executeReadableCommand(pLuaState, "ExitScript", 2);
    return 0;
}

int luaIsTurnBased(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushboolean(pLuaState, false);
        return 1;
    }

    if (!executeReadableCommand(pLuaState, "IsTurnBased", 2))
    {
        recordUnresolvedKnownCommand(pLuaState, "isTurnBased");
    }
    const std::string target = luaArgumentText(pLuaState, 2);
    lua_pushboolean(pLuaState, pRuntime->getScriptNumVar(target, 0) != 0);
    return 1;
}

int luaGetPcVoice(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushinteger(pLuaState, 0);
        return 1;
    }

    const int metadataIndex = luaTrailingMetadataIndex(pLuaState);
    const std::vector<std::string> arguments = luaCommandArguments(pLuaState, metadataIndex, 2);
    if (arguments.empty()
        || !pRuntime->executeCommand(
            "GetPcVoice",
            scriptArgumentsText(arguments),
            luaMetadataLine(pLuaState, metadataIndex),
            {}))
    {
        recordUnresolvedKnownCommand(pLuaState, "getPcVoice");
        lua_pushinteger(pLuaState, 0);
        return 1;
    }

    lua_pushinteger(pLuaState, pRuntime->getScriptNumVar(arguments[0], 0));
    return 1;
}

int luaGetPcLevel(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushinteger(pLuaState, 0);
        return 1;
    }

    const int metadataIndex = luaTrailingMetadataIndex(pLuaState);
    const std::vector<std::string> arguments = luaCommandArguments(pLuaState, metadataIndex, 2);
    if (arguments.size() < 2
        || !pRuntime->executeCommand(
            "GetPcLevel",
            scriptArgumentsText(arguments),
            luaMetadataLine(pLuaState, metadataIndex),
            {}))
    {
        recordUnresolvedKnownCommand(pLuaState, "getPcLevel");
        lua_pushinteger(pLuaState, 0);
        return 1;
    }

    lua_pushinteger(pLuaState, pRuntime->getScriptNumVar(arguments[1], 0));
    return 1;
}

int luaGetGameTime(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushinteger(pLuaState, 0);
        lua_pushinteger(pLuaState, 0);
        return 2;
    }

    const int metadataIndex = luaTrailingMetadataIndex(pLuaState);
    const std::vector<std::string> arguments = luaCommandArguments(pLuaState, metadataIndex, 2);
    if (arguments.size() < 2
        || !pRuntime->executeCommand(
            "GetGameTime",
            scriptArgumentsText(arguments),
            luaMetadataLine(pLuaState, metadataIndex),
            {}))
    {
        recordUnresolvedKnownCommand(pLuaState, "getGameTime");
        lua_pushinteger(pLuaState, 0);
        lua_pushinteger(pLuaState, 0);
        return 2;
    }

    lua_pushinteger(pLuaState, pRuntime->getScriptNumVar(arguments[0], 0));
    lua_pushinteger(pLuaState, pRuntime->getScriptNumVar(arguments[1], 0));
    return 2;
}

int luaHeal(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const int metadataIndex = luaTrailingMetadataIndex(pLuaState);
    const std::vector<std::string> arguments = luaMovementArguments(pLuaState, metadataIndex, 2);
    if (!pRuntime->executeCommand(
        "Heal",
        scriptArgumentsText(arguments),
        luaMetadataLine(pLuaState, metadataIndex),
        {}))
    {
        recordUnresolvedKnownCommand(pLuaState, "heal");
    }
    return 0;
}

int luaAddNpc(lua_State *pLuaState)
{
    if (!executeReadableCommand(pLuaState, "AddNPC", 2))
    {
        recordUnresolvedKnownCommand(pLuaState, "addNpc");
    }
    return 0;
}

int luaRemoveNpc(lua_State *pLuaState)
{
    if (!executeReadableCommand(pLuaState, "RemoveNPC", 2))
    {
        recordUnresolvedKnownCommand(pLuaState, "removeNpc");
    }
    return 0;
}

int luaSetParam(lua_State *pLuaState)
{
    if (!executeReadableCommand(pLuaState, "SetParam", 2))
    {
        recordUnresolvedKnownCommand(pLuaState, "setParam");
    }
    return 0;
}

int luaSavePath(lua_State *pLuaState)
{
    if (!executeReadableCommand(pLuaState, "SavePath", 2))
    {
        recordUnresolvedKnownCommand(pLuaState, "savePath");
    }
    return 0;
}

int luaRestorePath(lua_State *pLuaState)
{
    if (!executeReadableCommand(pLuaState, "RestorePath", 2))
    {
        recordUnresolvedKnownCommand(pLuaState, "restorePath");
    }
    return 0;
}

int luaCastRay(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const int metadataIndex = luaTrailingMetadataIndex(pLuaState);
    const std::vector<std::string> arguments = luaMovementArguments(pLuaState, metadataIndex, 2);
    if (!pRuntime->executeCommand(
        "CastRay",
        scriptArgumentsText(arguments),
        luaMetadataLine(pLuaState, metadataIndex),
        luaMetadataRaw(pLuaState, metadataIndex)))
    {
        recordUnresolvedKnownCommand(pLuaState, "castRay");
    }
    return 0;
}

int luaTraceOff(lua_State *pLuaState)
{
    executeReadableCommand(pLuaState, "TraceOff", 2);
    return 0;
}

int luaTraceOn(lua_State *pLuaState)
{
    executeReadableCommand(pLuaState, "TraceOn", 2);
    return 0;
}

int luaBreakpoint(lua_State *pLuaState)
{
    executeReadableCommand(pLuaState, "Breakpoint", 2);
    return 0;
}

int luaDontIncludeThisFile(lua_State *pLuaState)
{
    executeReadableCommand(pLuaState, "Dont_Include_This_File", 2);
    return 0;
}

int luaCacheTexture(lua_State *pLuaState)
{
    executeReadableCommand(pLuaState, "CacheTexture", 2);
    return 0;
}

int luaHidePiece(lua_State *pLuaState)
{
    executeReadableCommand(pLuaState, "HidePiece", 2);
    return 0;
}

int luaDoLetter(lua_State *pLuaState)
{
    executeReadableCommand(pLuaState, "DoLetter", 2);
    return 0;
}

int luaGetContainerCount(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushinteger(pLuaState, 0);
        return 1;
    }

    const int metadataIndex = luaTrailingMetadataIndex(pLuaState);
    const std::vector<std::string> arguments =
        luaMovementArguments(pLuaState, metadataIndex, 2);
    if (!pRuntime->executeCommand(
        "GetContainerCount",
        scriptArgumentsText(arguments),
        luaMetadataLine(pLuaState, metadataIndex),
        {}))
    {
        recordUnresolvedKnownCommand(pLuaState, "getContainerCount");
    }

    const std::string target = arguments.size() >= 2 ? arguments[1] : "";
    lua_pushinteger(pLuaState, pRuntime->getScriptNumVar(target, 0));
    return 1;
}

int luaHasKey(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushboolean(pLuaState, false);
        return 1;
    }

    const std::vector<std::string> arguments = luaCommandArguments(pLuaState, 3, 2);
    const std::optional<int32_t> rawKeyId = arguments.empty()
        ? luaRawKeyId(pLuaState, 2, *pRuntime)
        : rawKeyIdFromArguments(*pRuntime, arguments);
    const bool result = rawKeyId && pRuntime->dialogueRuntime().hasKey(*rawKeyId);
    if (rawKeyId)
    {
        pRuntime->recordKeyAccess("hasKey", *rawKeyId, result, luaMetadataLine(pLuaState, 3));
        if (arguments.size() >= 2 && !trimCopy(arguments[1]).empty())
        {
            pRuntime->setScriptNumVar(arguments[1], result ? 1 : 0);
        }
    }
    else
    {
        recordUnresolvedKnownCommand(pLuaState, "hasKey");
    }
    lua_pushboolean(pLuaState, result);
    return 1;
}

int luaGiveKey(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const std::vector<std::string> arguments = luaCommandArguments(pLuaState, 3, 2);
    const std::optional<int32_t> rawKeyId = arguments.empty()
        ? luaRawKeyId(pLuaState, 2, *pRuntime)
        : rawKeyIdFromArguments(*pRuntime, arguments);
    if (rawKeyId)
    {
        pRuntime->dialogueRuntime().giveKey(*rawKeyId);
        pRuntime->recordKeyAccess("giveKey", *rawKeyId, true, luaMetadataLine(pLuaState, 3));
    }
    else
    {
        recordUnresolvedKnownCommand(pLuaState, "giveKey");
    }

    return 0;
}

int luaTakeKey(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const std::vector<std::string> arguments = luaCommandArguments(pLuaState, 3, 2);
    const std::optional<int32_t> rawKeyId = arguments.empty()
        ? luaRawKeyId(pLuaState, 2, *pRuntime)
        : rawKeyIdFromArguments(*pRuntime, arguments);
    if (rawKeyId)
    {
        pRuntime->dialogueRuntime().takeKey(*rawKeyId);
        pRuntime->recordKeyAccess("takeKey", *rawKeyId, true, luaMetadataLine(pLuaState, 3));
    }
    else
    {
        recordUnresolvedKnownCommand(pLuaState, "takeKey");
    }

    return 0;
}

int luaGiveItem(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushboolean(pLuaState, false);
        return 1;
    }

    const std::vector<std::string> arguments = luaCommandArguments(pLuaState, 3, 2);
    if (arguments.empty())
    {
        recordUnresolvedKnownCommand(pLuaState, "giveItem");
        lua_pushboolean(pLuaState, false);
        return 1;
    }

    const uint32_t itemId = unsignedIdFromArgument(*pRuntime, arguments[0]);
    const bool granted = pRuntime->dialogueRuntime().party().tryGrantItem(itemId);
    pRuntime->recordPartyAccess("giveItem", itemId, 1, granted, luaMetadataLine(pLuaState, 3));
    lua_pushboolean(pLuaState, granted);
    return 1;
}

int luaTakeItem(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushboolean(pLuaState, false);
        return 1;
    }

    const std::vector<std::string> arguments = luaCommandArguments(pLuaState, 3, 2);
    if (arguments.empty())
    {
        recordUnresolvedKnownCommand(pLuaState, "takeItem");
        lua_pushboolean(pLuaState, false);
        return 1;
    }

    const uint32_t itemId = unsignedIdFromArgument(*pRuntime, arguments[0]);
    const bool removed = pRuntime->dialogueRuntime().party().removeItem(itemId);
    pRuntime->recordPartyAccess("takeItem", itemId, 1, removed, luaMetadataLine(pLuaState, 3));
    lua_pushboolean(pLuaState, removed);
    return 1;
}

int luaHasItem(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushboolean(pLuaState, false);
        return 1;
    }

    const std::vector<std::string> arguments = luaCommandArguments(pLuaState, 3, 2);
    if (arguments.empty())
    {
        recordUnresolvedKnownCommand(pLuaState, "hasItem");
        lua_pushboolean(pLuaState, false);
        return 1;
    }

    const uint32_t itemId = unsignedIdFromArgument(*pRuntime, arguments[0]);
    const bool found = pRuntime->dialogueRuntime().party().hasItemAnywhere(itemId);
    pRuntime->recordPartyAccess("hasItem", itemId, 0, found, luaMetadataLine(pLuaState, 3));
    if (arguments.size() >= 2 && !trimCopy(arguments[1]).empty())
    {
        pRuntime->setScriptNumVar(arguments[1], found ? 1 : 0);
    }
    lua_pushboolean(pLuaState, found);
    return 1;
}

int luaGiveGold(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const std::vector<std::string> arguments = luaCommandArguments(pLuaState, 3, 2);
    const int32_t amount = arguments.empty()
        ? 0
        : static_cast<int32_t>(scriptValueNumber(evaluateScriptExpression(*pRuntime, arguments[0])));
    pRuntime->dialogueRuntime().party().addGold(amount);
    pRuntime->recordPartyAccess("giveGold", 0, amount, true, luaMetadataLine(pLuaState, 3));
    return 0;
}

int luaHasGold(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushboolean(pLuaState, false);
        return 1;
    }

    const int metadataIndex = luaTrailingMetadataIndex(pLuaState);
    const std::vector<std::string> arguments =
        normalizedServiceArguments(luaCommandArguments(pLuaState, metadataIndex, 2));
    if (arguments.size() < 2)
    {
        recordUnresolvedKnownCommand(pLuaState, "hasGold");
        lua_pushboolean(pLuaState, false);
        return 1;
    }

    const bool executed = pRuntime->executeCommand(
        "HasGold",
        scriptArgumentsText(arguments),
        luaMetadataLine(pLuaState, metadataIndex),
        {});
    lua_pushboolean(pLuaState, executed && pRuntime->getScriptNumVar(arguments[1], 0) != 0);
    return 1;
}

int luaTakeGold(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushboolean(pLuaState, false);
        return 1;
    }

    const int metadataIndex = luaTrailingMetadataIndex(pLuaState);
    const std::vector<std::string> arguments =
        normalizedServiceArguments(luaCommandArguments(pLuaState, metadataIndex, 2));
    if (arguments.empty())
    {
        recordUnresolvedKnownCommand(pLuaState, "takeGold");
        lua_pushboolean(pLuaState, false);
        return 1;
    }

    const size_t oldAccessCount = pRuntime->partyAccesses().size();
    const bool executed = pRuntime->executeCommand(
        "TakeGold",
        scriptArgumentsText(arguments),
        luaMetadataLine(pLuaState, metadataIndex),
        {});
    const std::vector<Mm9ScriptRuntimePartyAccess> &accesses = pRuntime->partyAccesses();
    const bool tookGold = executed && accesses.size() > oldAccessCount
        && accesses.back().operation == "takeGold" && accesses.back().result;
    lua_pushboolean(pLuaState, tookGold);
    return 1;
}

int luaCacheScript(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const int metadataIndex = luaTrailingMetadataIndex(pLuaState);
    const std::vector<std::string> arguments = luaCommandArguments(pLuaState, metadataIndex, 2);
    if (arguments.empty())
    {
        recordUnresolvedKnownCommand(pLuaState, "cacheScript");
        return 0;
    }

    pRuntime->executeCommand(
        "CacheScript",
        scriptArgumentsText(arguments),
        luaMetadataLine(pLuaState, metadataIndex),
        {});
    return 0;
}

int luaRunScript(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const int metadataIndex = luaTrailingMetadataIndex(pLuaState);
    const std::vector<std::string> arguments = luaCommandArguments(pLuaState, metadataIndex, 2);
    if (arguments.empty())
    {
        recordUnresolvedKnownCommand(pLuaState, "runScript");
        return 0;
    }

    pRuntime->executeCommand(
        "RunScript",
        scriptArgumentsText(arguments),
        luaMetadataLine(pLuaState, metadataIndex),
        {});
    return 0;
}

int luaGivePromo(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const int metadataIndex = luaTrailingMetadataIndex(pLuaState);
    const std::vector<std::string> arguments =
        normalizedServiceArguments(luaCommandArguments(pLuaState, metadataIndex, 2));
    if (arguments.size() < 2)
    {
        recordUnresolvedKnownCommand(pLuaState, "givePromo");
        return 0;
    }

    pRuntime->executeCommand(
        "GivePromo",
        scriptArgumentsText(arguments),
        luaMetadataLine(pLuaState, metadataIndex),
        {});
    return 0;
}

int luaGetAttribute(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushinteger(pLuaState, 0);
        return 1;
    }

    const int metadataIndex = luaTrailingMetadataIndex(pLuaState);
    const std::vector<std::string> arguments =
        normalizedServiceArguments(luaCommandArguments(pLuaState, metadataIndex, 2));
    if (arguments.size() < 2)
    {
        recordUnresolvedKnownCommand(pLuaState, "getAttribute");
        lua_pushinteger(pLuaState, 0);
        return 1;
    }

    pRuntime->executeCommand(
        "GetAttribute",
        scriptArgumentsText(arguments),
        luaMetadataLine(pLuaState, metadataIndex),
        {});
    lua_pushinteger(pLuaState, pRuntime->getScriptNumVar(arguments[1], 0));
    return 1;
}

int luaGiveAttribute(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const int metadataIndex = luaTrailingMetadataIndex(pLuaState);
    const std::vector<std::string> arguments =
        normalizedServiceArguments(luaCommandArguments(pLuaState, metadataIndex, 2));
    if (arguments.size() < 3)
    {
        recordUnresolvedKnownCommand(pLuaState, "giveAttribute");
        return 0;
    }

    pRuntime->executeCommand(
        "GiveAttribute",
        scriptArgumentsText(arguments),
        luaMetadataLine(pLuaState, metadataIndex),
        {});
    return 0;
}

int luaGiveExp(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushinteger(pLuaState, 0);
        return 1;
    }

    const std::vector<std::string> arguments = luaCommandArguments(pLuaState, 3, 2);
    const uint32_t amount = arguments.empty()
        ? 0
        : unsignedIdFromArgument(*pRuntime, arguments[0]);
    const uint32_t granted = pRuntime->dialogueRuntime().party().grantSharedExperience(amount);
    pRuntime->recordPartyAccess(
        "giveExp",
        0,
        static_cast<int32_t>(amount),
        granted > 0,
        luaMetadataLine(pLuaState, 3));
    lua_pushinteger(pLuaState, granted);
    return 1;
}

int luaSetConsoleNumVar(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const std::vector<std::string> arguments = luaCommandArguments(pLuaState, 3, 2);
    if (arguments.size() >= 2)
    {
        pRuntime->setConsoleNumVar(
            arguments[0],
            static_cast<int32_t>(scriptValueNumber(evaluateScriptExpression(*pRuntime, arguments[1]))));
    }
    else
    {
        recordUnresolvedKnownCommand(pLuaState, "setConsoleNumVar");
    }

    return 0;
}

int luaGetConsoleNumVar(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushinteger(pLuaState, 0);
        return 1;
    }

    const std::vector<std::string> arguments = luaCommandArguments(pLuaState, 3, 2);
    if (!arguments.empty())
    {
        const int32_t value = pRuntime->getConsoleNumVar(arguments[0]);
        if (arguments.size() >= 2)
        {
            pRuntime->setScriptNumVar(arguments[1], value);
        }
        lua_pushinteger(pLuaState, value);
        return 1;
    }

    recordUnresolvedKnownCommand(pLuaState, "getConsoleNumVar");
    lua_pushinteger(pLuaState, 0);
    return 1;
}

int luaSetConsoleStrVar(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const std::vector<std::string> arguments = luaCommandArguments(pLuaState, 3, 2);
    if (arguments.size() >= 2)
    {
        pRuntime->setConsoleStrVar(arguments[0], consoleStrValueFromToken(arguments[1]));
    }
    else
    {
        recordUnresolvedKnownCommand(pLuaState, "setConsoleStrVar");
    }

    return 0;
}

int luaGetConsoleStrVar(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushstring(pLuaState, "");
        return 1;
    }

    const std::vector<std::string> arguments = luaCommandArguments(pLuaState, 3, 2);
    if (!arguments.empty())
    {
        const std::string value = pRuntime->getConsoleStrVar(arguments[0]);
        if (arguments.size() >= 2)
        {
            setScriptVariableFromString(*pRuntime, arguments[1], value);
        }
        lua_pushstring(pLuaState, value.c_str());
        return 1;
    }

    recordUnresolvedKnownCommand(pLuaState, "getConsoleStrVar");
    lua_pushstring(pLuaState, "");
    return 1;
}

int luaGetParam(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushstring(pLuaState, "");
        return 1;
    }

    const std::vector<std::string> arguments = luaCommandArguments(pLuaState, 3, 2);
    if (arguments.size() < 2)
    {
        recordUnresolvedKnownCommand(pLuaState, "getParam");
        lua_pushstring(pLuaState, "");
        return 1;
    }

    const int32_t paramIndex = scriptNumberValueFromToken(*pRuntime, arguments[0]);
    const std::vector<std::string> &params = pRuntime->dialogueRuntime().owner().scriptParams;
    const std::string value = paramIndex >= 0 && static_cast<size_t>(paramIndex) < params.size()
        ? params[static_cast<size_t>(paramIndex)]
        : "";
    setScriptVariableFromString(*pRuntime, arguments[1], value);
    lua_pushstring(pLuaState, value.c_str());
    return 1;
}

int luaSetPropNumber(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const std::vector<std::string> arguments = luaCommandArguments(pLuaState, 3, 2);
    if (arguments.size() >= 2)
    {
        pRuntime->setObjectNumberProperty(
            arguments[0],
            static_cast<int32_t>(scriptValueNumber(evaluateScriptExpression(*pRuntime, arguments[1]))),
            luaMetadataLine(pLuaState, 3));
    }
    else
    {
        recordUnresolvedKnownCommand(pLuaState, "setPropNumber");
    }

    return 0;
}

int luaGetObjectHandleByRudeId(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushstring(pLuaState, "");
        return 1;
    }

    const std::vector<std::string> arguments = luaCommandArguments(pLuaState, 3, 2);
    if (arguments.size() < 2)
    {
        recordUnresolvedKnownCommand(pLuaState, "getObjectHandleByRudeId");
        lua_pushstring(pLuaState, "");
        return 1;
    }

    const int32_t rudeId = static_cast<int32_t>(scriptValueNumber(evaluateScriptExpression(*pRuntime, arguments[0])));
    const std::string handle = pRuntime->objectHandleForRudeId(rudeId);
    pRuntime->setObjectHandleVar(arguments[1], handle);
    lua_pushstring(pLuaState, handle.c_str());
    return 1;
}

int luaAddTrigger(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const std::vector<std::string> arguments = luaCommandArguments(pLuaState, 3, 2);
    if (arguments.size() >= 2)
    {
        pRuntime->registerTrigger(arguments[0], arguments[1], luaMetadataLine(pLuaState, 3));
    }
    else
    {
        recordUnresolvedKnownCommand(pLuaState, "addTrigger");
    }

    return 0;
}

int luaRemoveTrigger(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    pRuntime->removeTrigger(luaArgumentText(pLuaState, 2));
    return 0;
}

std::string triggerTargetHandleFromScriptToken(Mm9ScriptRuntime &runtime, const std::string &token)
{
    const std::string trimmed = trimCopy(token);
    const std::string lowered = lowerCopy(trimmed);
    if (lowered == "null" || lowered == "nil" || lowered == "0")
    {
        return {};
    }

    return runtime.resolveScriptString(trimmed);
}

int luaTrigger(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const int metadataIndex = luaTrailingMetadataIndex(pLuaState);
    if (metadataIndex == 0 && lua_gettop(pLuaState) >= 3)
    {
        pRuntime->dispatchTrigger(
            objectHandleFromLua(*pRuntime, pLuaState, 2),
            pRuntime->resolveScriptString(luaArgumentText(pLuaState, 3)),
            0);
        return 0;
    }

    const std::vector<std::string> arguments = luaCommandArguments(pLuaState, metadataIndex, 2);
    if (arguments.size() >= 2)
    {
        pRuntime->dispatchTrigger(
            triggerTargetHandleFromScriptToken(*pRuntime, arguments[0]),
            pRuntime->resolveScriptString(arguments[1]),
            luaMetadataLine(pLuaState, metadataIndex));
    }
    else
    {
        recordUnresolvedKnownCommand(pLuaState, "trigger");
    }

    return 0;
}

int luaGetObjects(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const std::vector<std::string> arguments = luaCommandArguments(pLuaState, 7, 2);
    const size_t line = luaMetadataLine(pLuaState, 7);
    const std::string raw = luaMetadataRaw(pLuaState, 7);
    const std::string argumentsText = scriptArgumentsText(arguments);
    if (!pRuntime->executeCommand("getobjects", argumentsText, line, raw))
    {
        pRuntime->recordUnimplementedCommand("getobjects", argumentsText, line, raw);
    }
    return 0;
}

int luaArrayPut(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const std::vector<std::string> arguments = luaCommandArguments(pLuaState, 5, 2);
    const size_t line = luaMetadataLine(pLuaState, 5);
    const std::string raw = luaMetadataRaw(pLuaState, 5);
    const std::string argumentsText = scriptArgumentsText(arguments);
    if (!pRuntime->executeCommand("arrayput", argumentsText, line, raw))
    {
        pRuntime->recordUnimplementedCommand("arrayput", argumentsText, line, raw);
    }
    return 0;
}

int luaArrayGet(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const std::vector<std::string> arguments = luaCommandArguments(pLuaState, 5, 2);
    const size_t line = luaMetadataLine(pLuaState, 5);
    const std::string raw = luaMetadataRaw(pLuaState, 5);
    const std::string argumentsText = scriptArgumentsText(arguments);
    if (!pRuntime->executeCommand("arrayget", argumentsText, line, raw))
    {
        pRuntime->recordUnimplementedCommand("arrayget", argumentsText, line, raw);
    }
    return 0;
}

int luaRandomInt(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const std::vector<std::string> arguments = luaCommandArguments(pLuaState, 5, 2);
    const size_t line = luaMetadataLine(pLuaState, 5);
    const std::string raw = luaMetadataRaw(pLuaState, 5);
    const std::string argumentsText = scriptArgumentsText(arguments);
    if (!pRuntime->executeCommand("getrandomint", argumentsText, line, raw))
    {
        pRuntime->recordUnimplementedCommand("getrandomint", argumentsText, line, raw);
    }
    return 0;
}

int luaRandomFloat(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const std::vector<std::string> arguments = luaCommandArguments(pLuaState, 5, 2);
    const size_t line = luaMetadataLine(pLuaState, 5);
    const std::string raw = luaMetadataRaw(pLuaState, 5);
    const std::string argumentsText = scriptArgumentsText(arguments);
    if (!pRuntime->executeCommand("getrandomfloat", argumentsText, line, raw))
    {
        pRuntime->recordUnimplementedCommand("getrandomfloat", argumentsText, line, raw);
    }
    return 0;
}

int luaGetTime(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const std::vector<std::string> arguments = luaCommandArguments(pLuaState, 3, 2);
    const size_t line = luaMetadataLine(pLuaState, 3);
    const std::string raw = luaMetadataRaw(pLuaState, 3);
    const std::string argumentsText = scriptArgumentsText(arguments);
    if (!pRuntime->executeCommand("gettime", argumentsText, line, raw))
    {
        pRuntime->recordUnimplementedCommand("gettime", argumentsText, line, raw);
    }
    return 0;
}

int luaStateCommand(lua_State *pLuaState, const std::string &command)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const std::vector<std::string> arguments = luaCommandArguments(pLuaState, 4, 2);
    const size_t line = luaMetadataLine(pLuaState, 4);
    const std::string raw = luaMetadataRaw(pLuaState, 4);
    const std::string argumentsText = scriptArgumentsText(arguments);
    if (!pRuntime->executeCommand(command, argumentsText, line, raw))
    {
        pRuntime->recordUnimplementedCommand(command, argumentsText, line, raw);
    }
    return 0;
}

int luaRuntimeCommand(lua_State *pLuaState, const std::string &command, bool objectArguments)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const int metadataIndex = luaTrailingMetadataIndex(pLuaState);
    const std::vector<std::string> arguments = objectArguments
        ? luaMovementArguments(pLuaState, metadataIndex, 2)
        : luaServiceArguments(pLuaState, metadataIndex, 2);
    const std::string argumentsText = scriptArgumentsText(arguments);
    if (!pRuntime->executeCommand(
        command,
        argumentsText,
        luaMetadataLine(pLuaState, metadataIndex),
        luaMetadataRaw(pLuaState, metadataIndex)))
    {
        pRuntime->recordUnimplementedCommand(
            command,
            argumentsText,
            luaMetadataLine(pLuaState, metadataIndex),
            luaMetadataRaw(pLuaState, metadataIndex));
    }
    return 0;
}

int luaGetPlayerId(lua_State *pLuaState)
{
    return luaRuntimeCommand(pLuaState, "getplayerid", true);
}

int luaGetPlayerNumber(lua_State *pLuaState)
{
    return luaRuntimeCommand(pLuaState, "getplayernbr", true);
}

int luaGetPlayersWithinDist(lua_State *pLuaState)
{
    return luaRuntimeCommand(pLuaState, "getplayerswithindist", false);
}

int luaConsoleCommand(lua_State *pLuaState)
{
    return luaRuntimeCommand(pLuaState, "consolecommand", false);
}

int luaDoHighScore(lua_State *pLuaState)
{
    return luaRuntimeCommand(pLuaState, "dohighscore", false);
}

int luaClearCondition(lua_State *pLuaState)
{
    return luaRuntimeCommand(pLuaState, "clearcondition", false);
}

int luaSetCondition(lua_State *pLuaState)
{
    return luaRuntimeCommand(pLuaState, "setcondition", false);
}

int luaSetInt(lua_State *pLuaState)
{
    return luaRuntimeCommand(pLuaState, "setint", false);
}

int luaSin(lua_State *pLuaState)
{
    return luaRuntimeCommand(pLuaState, "sin", false);
}

int luaCos(lua_State *pLuaState)
{
    return luaRuntimeCommand(pLuaState, "cos", false);
}

int luaGetAngleToPos(lua_State *pLuaState)
{
    return luaRuntimeCommand(pLuaState, "getangletopos", false);
}

int luaGetRotation(lua_State *pLuaState)
{
    return luaRuntimeCommand(pLuaState, "getrotation", true);
}

int luaSetRotation(lua_State *pLuaState)
{
    return luaRuntimeCommand(pLuaState, "setrotation", true);
}

int luaCalcRotationRate(lua_State *pLuaState)
{
    return luaRuntimeCommand(pLuaState, "calcrotationrate", true);
}

int luaCheckWorldCollision(lua_State *pLuaState)
{
    return luaRuntimeCommand(pLuaState, "checkworldcollision", false);
}

int luaSetStateValue(lua_State *pLuaState)
{
    return luaStateCommand(pLuaState, "set");
}

int luaAddStateValue(lua_State *pLuaState)
{
    return luaStateCommand(pLuaState, "add");
}

int luaSubStateValue(lua_State *pLuaState)
{
    return luaStateCommand(pLuaState, "sub");
}

int luaMulStateValue(lua_State *pLuaState)
{
    return luaStateCommand(pLuaState, "mul");
}

int luaDivStateValue(lua_State *pLuaState)
{
    return luaStateCommand(pLuaState, "div");
}

int luaModStateValue(lua_State *pLuaState)
{
    return luaStateCommand(pLuaState, "mod");
}

double luaEvaluatedNumber(Mm9ScriptRuntime &runtime, lua_State *pLuaState, int index)
{
    return scriptValueNumber(evaluateScriptExpression(runtime, luaScriptExpressionText(pLuaState, index)));
}

void luaPushVec3(lua_State *pLuaState, double x, double y, double z)
{
    lua_pushnumber(pLuaState, x);
    lua_pushnumber(pLuaState, y);
    lua_pushnumber(pLuaState, z);
}

int luaVecScale(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const double x = luaEvaluatedNumber(*pRuntime, pLuaState, 2);
    const double y = luaEvaluatedNumber(*pRuntime, pLuaState, 3);
    const double z = luaEvaluatedNumber(*pRuntime, pLuaState, 4);
    const double scale = luaEvaluatedNumber(*pRuntime, pLuaState, 5);
    luaPushVec3(pLuaState, x * scale, y * scale, z * scale);
    return 3;
}

int luaVecNorm(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const double x = luaEvaluatedNumber(*pRuntime, pLuaState, 2);
    const double y = luaEvaluatedNumber(*pRuntime, pLuaState, 3);
    const double z = luaEvaluatedNumber(*pRuntime, pLuaState, 4);
    const double length = std::sqrt((x * x) + (y * y) + (z * z));
    if (length == 0.0)
    {
        luaPushVec3(pLuaState, 0.0, 0.0, 0.0);
        return 3;
    }

    luaPushVec3(pLuaState, x / length, y / length, z / length);
    return 3;
}

int luaVecAdd(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    luaPushVec3(
        pLuaState,
        luaEvaluatedNumber(*pRuntime, pLuaState, 2) + luaEvaluatedNumber(*pRuntime, pLuaState, 5),
        luaEvaluatedNumber(*pRuntime, pLuaState, 3) + luaEvaluatedNumber(*pRuntime, pLuaState, 6),
        luaEvaluatedNumber(*pRuntime, pLuaState, 4) + luaEvaluatedNumber(*pRuntime, pLuaState, 7));
    return 3;
}

int luaVecSub(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    luaPushVec3(
        pLuaState,
        luaEvaluatedNumber(*pRuntime, pLuaState, 2) - luaEvaluatedNumber(*pRuntime, pLuaState, 5),
        luaEvaluatedNumber(*pRuntime, pLuaState, 3) - luaEvaluatedNumber(*pRuntime, pLuaState, 6),
        luaEvaluatedNumber(*pRuntime, pLuaState, 4) - luaEvaluatedNumber(*pRuntime, pLuaState, 7));
    return 3;
}

int luaVecCross(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const double ax = luaEvaluatedNumber(*pRuntime, pLuaState, 2);
    const double ay = luaEvaluatedNumber(*pRuntime, pLuaState, 3);
    const double az = luaEvaluatedNumber(*pRuntime, pLuaState, 4);
    const double bx = luaEvaluatedNumber(*pRuntime, pLuaState, 5);
    const double by = luaEvaluatedNumber(*pRuntime, pLuaState, 6);
    const double bz = luaEvaluatedNumber(*pRuntime, pLuaState, 7);
    luaPushVec3(pLuaState, (ay * bz) - (az * by), (az * bx) - (ax * bz), (ax * by) - (ay * bx));
    return 3;
}

int luaVecDist(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const Mm9ScriptRuntimeVec3 first = {
        luaEvaluatedNumber(*pRuntime, pLuaState, 2),
        luaEvaluatedNumber(*pRuntime, pLuaState, 3),
        luaEvaluatedNumber(*pRuntime, pLuaState, 4)
    };
    const Mm9ScriptRuntimeVec3 second = {
        luaEvaluatedNumber(*pRuntime, pLuaState, 5),
        luaEvaluatedNumber(*pRuntime, pLuaState, 6),
        luaEvaluatedNumber(*pRuntime, pLuaState, 7)
    };
    lua_pushnumber(pLuaState, scriptVectorDistance(first, second));
    return 1;
}

int luaVecMag(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const double x = luaEvaluatedNumber(*pRuntime, pLuaState, 2);
    const double y = luaEvaluatedNumber(*pRuntime, pLuaState, 3);
    const double z = luaEvaluatedNumber(*pRuntime, pLuaState, 4);
    lua_pushnumber(pLuaState, std::sqrt((x * x) + (y * y) + (z * z)));
    return 1;
}

int luaVecAngle(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const Mm9ScriptRuntimeVec3 first = {
        luaEvaluatedNumber(*pRuntime, pLuaState, 2),
        luaEvaluatedNumber(*pRuntime, pLuaState, 3),
        luaEvaluatedNumber(*pRuntime, pLuaState, 4)
    };
    const Mm9ScriptRuntimeVec3 second = {
        luaEvaluatedNumber(*pRuntime, pLuaState, 5),
        luaEvaluatedNumber(*pRuntime, pLuaState, 6),
        luaEvaluatedNumber(*pRuntime, pLuaState, 7)
    };
    const double firstLength = std::sqrt((first.x * first.x) + (first.y * first.y) + (first.z * first.z));
    const double secondLength = std::sqrt((second.x * second.x) + (second.y * second.y) + (second.z * second.z));
    double angle = 0.0;
    if (firstLength != 0.0 && secondLength != 0.0)
    {
        const double dot = (first.x * second.x) + (first.y * second.y) + (first.z * second.z);
        const double cosine = std::max(-1.0, std::min(1.0, dot / (firstLength * secondLength)));
        angle = std::acos(cosine) * 180.0 / std::acos(-1.0);
    }

    lua_pushnumber(pLuaState, angle);
    return 1;
}

int luaRotateDir(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const double x = luaEvaluatedNumber(*pRuntime, pLuaState, 2);
    const double y = luaEvaluatedNumber(*pRuntime, pLuaState, 3);
    const double z = luaEvaluatedNumber(*pRuntime, pLuaState, 4);
    const double radians = luaEvaluatedNumber(*pRuntime, pLuaState, 5) * std::acos(-1.0) / 180.0;
    luaPushVec3(pLuaState, (x * std::cos(radians)) - (y * std::sin(radians)),
        (x * std::sin(radians)) + (y * std::cos(radians)), z);
    return 3;
}

int luaWait(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const std::vector<std::string> arguments = luaCommandArguments(pLuaState, 5, 2);
    const size_t line = luaMetadataLine(pLuaState, 5);
    const std::string raw = luaMetadataRaw(pLuaState, 5);
    const std::string argumentsText = scriptArgumentsText(arguments);
    if (!pRuntime->executeCommand("wait", argumentsText, line, raw))
    {
        pRuntime->recordUnimplementedCommand("wait", argumentsText, line, raw);
    }
    return 0;
}

int luaAudioCommand(lua_State *pLuaState, const std::string &command)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const std::vector<std::string> arguments = luaServiceArguments(pLuaState, 8, 2);
    const size_t line = luaMetadataLine(pLuaState, 8);
    const std::string raw = luaMetadataRaw(pLuaState, 8);
    const std::string argumentsText = scriptArgumentsText(arguments);
    if (!pRuntime->executeCommand(command, argumentsText, line, raw))
    {
        pRuntime->recordUnimplementedCommand(command, argumentsText, line, raw);
    }
    return 0;
}

int luaCacheSound(lua_State *pLuaState)
{
    return luaAudioCommand(pLuaState, "cachesound");
}

int luaPlaySound(lua_State *pLuaState)
{
    return luaAudioCommand(pLuaState, "playsound");
}

int luaSpeak(lua_State *pLuaState)
{
    return luaAudioCommand(pLuaState, "speak");
}

int luaPlaySoundHandle(lua_State *pLuaState)
{
    return luaAudioCommand(pLuaState, "playsoundhandle");
}

int luaKillSound(lua_State *pLuaState)
{
    return luaAudioCommand(pLuaState, "killsound");
}

int luaGetSoundDuration(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    std::vector<std::string> arguments = luaServiceArguments(pLuaState, 8, 2);
    if (arguments.size() == 2)
    {
        arguments.insert(arguments.begin(), "");
    }

    const size_t line = luaMetadataLine(pLuaState, 8);
    const std::string raw = luaMetadataRaw(pLuaState, 8);
    const std::string argumentsText = scriptArgumentsText(arguments);
    if (!pRuntime->executeCommand("getsoundduration", argumentsText, line, raw))
    {
        pRuntime->recordUnimplementedCommand("getsoundduration", argumentsText, line, raw);
    }
    return 0;
}

int luaIsSoundDone(lua_State *pLuaState)
{
    return luaAudioCommand(pLuaState, "issounddone");
}

int luaCacheClientFx(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const std::vector<std::string> arguments = luaServiceArguments(pLuaState, 8, 2);
    const size_t line = luaMetadataLine(pLuaState, 8);
    const std::string raw = luaMetadataRaw(pLuaState, 8);
    const std::string argumentsText = scriptArgumentsText(arguments);
    if (!pRuntime->executeCommand("cacheclientfx", argumentsText, line, raw))
    {
        pRuntime->recordUnimplementedCommand("cacheclientfx", argumentsText, line, raw);
    }
    return 0;
}

int luaObjectHandle(lua_State *pLuaState)
{
    lua_pushstring(pLuaState, luaObjectProxyHandle(pLuaState, 1).c_str());
    return 1;
}

int luaObjectName(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushstring(pLuaState, "");
        return 1;
    }

    const std::string name = pRuntime->objectNameForHandle(luaObjectProxyHandle(pLuaState, 1));
    lua_pushstring(pLuaState, name.c_str());
    return 1;
}

int luaObjectClassName(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushstring(pLuaState, "");
        return 1;
    }

    const std::string className = pRuntime->objectClassNameForHandle(luaObjectProxyHandle(pLuaState, 1));
    lua_pushstring(pLuaState, className.c_str());
    return 1;
}

int luaObjectIsClass(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushboolean(pLuaState, 0);
        return 1;
    }

    const std::string expected = lowerCopy(unquoteScriptString(luaArgumentText(pLuaState, 2)));
    const std::string handle = luaObjectProxyHandle(pLuaState, 1);
    const bool matches = lowerCopy(pRuntime->objectClassNameForHandle(handle)) == expected
        || lowerCopy(pRuntime->objectNameForHandle(handle)) == expected;
    lua_pushboolean(pLuaState, matches ? 1 : 0);
    return 1;
}

int luaObjectIsPlayer(lua_State *pLuaState)
{
    const std::string handle = luaObjectProxyHandle(pLuaState, 1);
    lua_pushboolean(pLuaState, handle == "mm9:player" ? 1 : 0);
    return 1;
}

int luaObjectIsActor(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushboolean(pLuaState, 0);
        return 1;
    }

    lua_pushboolean(
        pLuaState,
        lowerCopy(pRuntime->objectClassNameForHandle(luaObjectProxyHandle(pLuaState, 1))) == "actor" ? 1 : 0);
    return 1;
}

int luaObjectIsAi(lua_State *pLuaState)
{
    return luaObjectIsActor(pLuaState);
}

int luaObjectIsActive(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushboolean(pLuaState, 0);
        return 1;
    }

    const std::string handle = luaObjectProxyHandle(pLuaState, 1);
    const auto removedIterator = pRuntime->state().removedObjects.find(handle);
    const bool active = !handle.empty() && (removedIterator == pRuntime->state().removedObjects.end()
        || !removedIterator->second);
    lua_pushboolean(pLuaState, active ? 1 : 0);
    return 1;
}

int luaObjectIsVisible(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushboolean(pLuaState, 0);
        return 1;
    }

    const std::string handle = luaObjectProxyHandle(pLuaState, 1);
    const auto removedIterator = pRuntime->state().removedObjects.find(handle);
    const bool active = !handle.empty() && (removedIterator == pRuntime->state().removedObjects.end()
        || !removedIterator->second);
    lua_pushboolean(pLuaState, active && objectFlagValue(pRuntime->state(), handle, "visible", true) ? 1 : 0);
    return 1;
}

int luaObjectTrigger(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const std::string handle = luaObjectProxyHandle(pLuaState, 1);
    const std::string message = pRuntime->resolveScriptString(luaArgumentText(pLuaState, 2));
    pRuntime->dispatchTrigger(handle, message, 0);
    return 0;
}

int luaObjectPos(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushinteger(pLuaState, 0);
        lua_pushinteger(pLuaState, 0);
        lua_pushinteger(pLuaState, 0);
        return 3;
    }

    const std::string handle = luaObjectProxyHandle(pLuaState, 1);
    const auto positionIterator = pRuntime->state().objectPositions.find(handle);
    const Mm9ScriptRuntimeVec3 position = positionIterator != pRuntime->state().objectPositions.end()
        ? positionIterator->second
        : Mm9ScriptRuntimeVec3();
    lua_pushinteger(pLuaState, static_cast<int32_t>(position.x));
    lua_pushinteger(pLuaState, static_cast<int32_t>(position.y));
    lua_pushinteger(pLuaState, static_cast<int32_t>(position.z));
    return 3;
}

int luaObjectSetPos(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const std::string handle = luaObjectProxyHandle(pLuaState, 1);
    if (handle.empty())
    {
        return 0;
    }

    const std::string arguments = handle + ", "
        + luaArgumentText(pLuaState, 2) + ", "
        + luaArgumentText(pLuaState, 3) + ", "
        + luaArgumentText(pLuaState, 4);
    pRuntime->executeCommand("setpos", arguments, 0, "object:setPos");
    return 0;
}

int luaObjectRotation(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushinteger(pLuaState, 0);
        lua_pushinteger(pLuaState, 0);
        lua_pushinteger(pLuaState, 0);
        return 3;
    }

    const std::string handle = luaObjectProxyHandle(pLuaState, 1);
    const auto directionIterator = pRuntime->state().objectFaceDirs.find(handle);
    const Mm9ScriptRuntimeVec3 direction = directionIterator != pRuntime->state().objectFaceDirs.end()
        ? directionIterator->second
        : Mm9ScriptRuntimeVec3();
    lua_pushinteger(pLuaState, static_cast<int32_t>(direction.x));
    lua_pushinteger(pLuaState, static_cast<int32_t>(direction.y));
    lua_pushinteger(pLuaState, static_cast<int32_t>(direction.z));
    return 3;
}

int luaObjectDirection(lua_State *pLuaState, const std::string &operation)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushinteger(pLuaState, 0);
        lua_pushinteger(pLuaState, 0);
        lua_pushinteger(pLuaState, 0);
        return 3;
    }

    const Mm9ScriptRuntimeVec3 direction =
        objectDirectionVector(pRuntime->state(), luaObjectProxyHandle(pLuaState, 1), operation);
    lua_pushnumber(pLuaState, direction.x);
    lua_pushnumber(pLuaState, direction.y);
    lua_pushnumber(pLuaState, direction.z);
    return 3;
}

int luaObjectForwardDir(lua_State *pLuaState)
{
    return luaObjectDirection(pLuaState, "forwarddir");
}

int luaObjectReverseDir(lua_State *pLuaState)
{
    return luaObjectDirection(pLuaState, "reversedir");
}

int luaObjectRightDir(lua_State *pLuaState)
{
    return luaObjectDirection(pLuaState, "rightdir");
}

int luaObjectLeftDir(lua_State *pLuaState)
{
    return luaObjectDirection(pLuaState, "leftdir");
}

int luaObjectSetRotation(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const std::string handle = luaObjectProxyHandle(pLuaState, 1);
    if (handle.empty())
    {
        return 0;
    }

    std::string arguments = handle + ", "
        + luaArgumentText(pLuaState, 2) + ", "
        + luaArgumentText(pLuaState, 3) + ", "
        + luaArgumentText(pLuaState, 4);
    if (lua_gettop(pLuaState) >= 5 && !lua_isnil(pLuaState, 5))
    {
        arguments += ", " + luaArgumentText(pLuaState, 5);
    }

    pRuntime->executeCommand("setrotation", arguments, 0, "object:setRotation");
    return 0;
}

int luaObjectVelocity(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushinteger(pLuaState, 0);
        lua_pushinteger(pLuaState, 0);
        lua_pushinteger(pLuaState, 0);
        return 3;
    }

    const std::string handle = luaObjectProxyHandle(pLuaState, 1);
    const auto objectIterator = pRuntime->state().objectStats.find(handle);
    const auto statValue = [&](const std::string &name) -> int32_t
    {
        if (objectIterator == pRuntime->state().objectStats.end())
        {
            return 0;
        }

        const auto valueIterator = objectIterator->second.find(name);
        return valueIterator != objectIterator->second.end() ? valueIterator->second : 0;
    };

    lua_pushinteger(pLuaState, statValue("VelocityX"));
    lua_pushinteger(pLuaState, statValue("VelocityY"));
    lua_pushinteger(pLuaState, statValue("VelocityZ"));
    return 3;
}

int luaObjectDims(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushinteger(pLuaState, 0);
        lua_pushinteger(pLuaState, 0);
        lua_pushinteger(pLuaState, 0);
        return 3;
    }

    const std::string handle = luaObjectProxyHandle(pLuaState, 1);
    const auto objectIterator = pRuntime->state().objectStats.find(handle);
    const auto statValue = [&](const std::string &name) -> int32_t
    {
        if (objectIterator == pRuntime->state().objectStats.end())
        {
            return 0;
        }

        const auto valueIterator = objectIterator->second.find(name);
        return valueIterator != objectIterator->second.end() ? valueIterator->second : 0;
    };

    lua_pushinteger(pLuaState, statValue("DimsX"));
    lua_pushinteger(pLuaState, statValue("DimsY"));
    lua_pushinteger(pLuaState, statValue("DimsZ"));
    return 3;
}

int luaObjectMinMax(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        for (int32_t i = 0; i < 6; ++i)
        {
            lua_pushinteger(pLuaState, 0);
        }
        return 6;
    }

    const std::string handle = luaObjectProxyHandle(pLuaState, 1);
    const auto objectIterator = pRuntime->state().objectStats.find(handle);
    const auto statValue = [&](const std::string &name) -> int32_t
    {
        if (objectIterator == pRuntime->state().objectStats.end())
        {
            return 0;
        }

        const auto valueIterator = objectIterator->second.find(name);
        return valueIterator != objectIterator->second.end() ? valueIterator->second : 0;
    };

    lua_pushinteger(pLuaState, statValue("MinX"));
    lua_pushinteger(pLuaState, statValue("MinY"));
    lua_pushinteger(pLuaState, statValue("MinZ"));
    lua_pushinteger(pLuaState, statValue("MaxX"));
    lua_pushinteger(pLuaState, statValue("MaxY"));
    lua_pushinteger(pLuaState, statValue("MaxZ"));
    return 6;
}

int luaObjectSetVelocity(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const std::string handle = luaObjectProxyHandle(pLuaState, 1);
    if (handle.empty())
    {
        return 0;
    }

    const std::string arguments = handle + ", "
        + luaArgumentText(pLuaState, 2) + ", "
        + luaArgumentText(pLuaState, 3) + ", "
        + luaArgumentText(pLuaState, 4);
    pRuntime->executeCommand("setvelocity", arguments, 0, "object:setVelocity");
    return 0;
}

int luaObjectSetNumberProperty(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const std::string key = objectNumberPropertyKeyForHandle(
        luaObjectProxyHandle(pLuaState, 1),
        luaArgumentText(pLuaState, 2));
    if (key.empty())
    {
        return 0;
    }

    pRuntime->setObjectNumberPropertyForHandle(
        luaObjectProxyHandle(pLuaState, 1),
        luaArgumentText(pLuaState, 2),
        static_cast<int32_t>(
            scriptValueNumber(evaluateScriptExpression(*pRuntime, luaScriptExpressionText(pLuaState, 3)))));
    return 0;
}

int luaObjectNumberProperty(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushinteger(pLuaState, 0);
        return 1;
    }

    lua_pushinteger(
        pLuaState,
        pRuntime->getObjectNumberPropertyForHandle(
            luaObjectProxyHandle(pLuaState, 1),
            luaArgumentText(pLuaState, 2)));
    return 1;
}

int luaObjectSetStringProperty(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    pRuntime->setObjectStringPropertyForHandle(
        luaObjectProxyHandle(pLuaState, 1),
        luaArgumentText(pLuaState, 2),
        luaArgumentText(pLuaState, 3));
    return 0;
}

int luaObjectStringProperty(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushstring(pLuaState, "");
        return 1;
    }

    const std::string value = pRuntime->getObjectStringPropertyForHandle(
        luaObjectProxyHandle(pLuaState, 1),
        luaArgumentText(pLuaState, 2));

    lua_pushstring(pLuaState, value.c_str());
    return 1;
}

int luaObjectSetFlag(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const std::string flag = normalizedObjectFlagName(luaArgumentText(pLuaState, 2));
    const bool enabled = lua_gettop(pLuaState) < 3 || lua_isnil(pLuaState, 3)
        || lua_toboolean(pLuaState, 3) != 0;
    const std::string command = enabled ? "setflag" : "clearflag";
    pRuntime->executeCommand(command, luaObjectProxyHandle(pLuaState, 1) + ", " + flag, 0, "object:setFlag");
    return 0;
}

int luaObjectFlag(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushboolean(pLuaState, false);
        return 1;
    }

    const std::string handle = luaObjectProxyHandle(pLuaState, 1);
    lua_pushboolean(pLuaState, objectFlagValue(pRuntime->state(), handle, luaArgumentText(pLuaState, 2), false));
    return 1;
}

int luaObjectGetStat(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushinteger(pLuaState, 0);
        return 1;
    }

    const std::string handle = luaObjectProxyHandle(pLuaState, 1);
    const std::string statName = luaArgumentText(pLuaState, 2);
    const auto objectIterator = pRuntime->state().objectStats.find(handle);
    if (objectIterator == pRuntime->state().objectStats.end())
    {
        lua_pushinteger(pLuaState, 0);
        return 1;
    }

    const auto statIterator = objectIterator->second.find(statName);
    lua_pushinteger(
        pLuaState,
        statIterator != objectIterator->second.end() ? statIterator->second : 0);
    return 1;
}

int luaObjectSetStat(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const std::string handle = luaObjectProxyHandle(pLuaState, 1);
    const std::string statName = luaArgumentText(pLuaState, 2);
    if (handle.empty() || statName.empty())
    {
        return 0;
    }

    const std::string value = luaScriptExpressionText(pLuaState, 3);
    if (value.empty())
    {
        return 0;
    }

    pRuntime->executeCommand(
        "setstat",
        handle + ", " + statName + ", " + value,
        0,
        "object:setStat");
    return 0;
}

int luaObjectAnimationCommand(lua_State *pLuaState, const std::string &command)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const std::string handle = luaObjectProxyHandle(pLuaState, 1);
    if (handle.empty())
    {
        return 0;
    }

    if (!pRuntime->requestAnimation(handle, command, luaServiceArguments(pLuaState, 8, 2), 0))
    {
        pRuntime->recordUnimplementedCommand(command, {}, 0, "object animation request");
    }
    return 0;
}

int luaObjectPlayAnimation(lua_State *pLuaState)
{
    return luaObjectAnimationCommand(pLuaState, "playanim");
}

int luaObjectPlayAnimationCommand(lua_State *pLuaState)
{
    return luaObjectAnimationCommand(pLuaState, "playanimation");
}

int luaObjectLoopAnimation(lua_State *pLuaState)
{
    return luaObjectAnimationCommand(pLuaState, "loopanim");
}

int luaObjectPlayAnimSound(lua_State *pLuaState)
{
    return luaObjectAnimationCommand(pLuaState, "playanimsound");
}

int luaObjectSetAnimationPlaying(lua_State *pLuaState)
{
    return luaObjectAnimationCommand(pLuaState, "setanimplaying");
}

int luaObjectAnimationQuery(lua_State *pLuaState, const std::string &command)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushinteger(pLuaState, 0);
        return 1;
    }

    const int metadataIndex = luaTrailingMetadataIndex(pLuaState);
    const std::string handle = luaObjectProxyHandle(pLuaState, 1);
    std::vector<std::string> arguments = {handle};
    const std::vector<std::string> luaArguments = luaCommandArguments(pLuaState, metadataIndex, 2);
    arguments.insert(arguments.end(), luaArguments.begin(), luaArguments.end());
    if (!pRuntime->executeCommand(
        command,
        scriptArgumentsText(arguments),
        luaMetadataLine(pLuaState, metadataIndex),
        luaMetadataRaw(pLuaState, metadataIndex)))
    {
        recordUnresolvedKnownCommand(pLuaState, command);
    }

    const std::string loweredCommand = lowerCopy(command);
    const size_t destinationIndex = loweredCommand == "getcurranim" ? 1 : 2;
    const std::string destination = arguments.size() > destinationIndex ? arguments[destinationIndex] : "";
    if (loweredCommand == "getanimname")
    {
        const std::string value = pRuntime->getScriptStrVar(destination);
        lua_pushstring(pLuaState, value.c_str());
        return 1;
    }

    lua_pushinteger(pLuaState, pRuntime->getScriptNumVar(destination, 0));
    return 1;
}

int luaObjectGetCurrentAnimation(lua_State *pLuaState)
{
    return luaObjectAnimationQuery(pLuaState, "GetCurrAnim");
}

int luaObjectGetAnimationName(lua_State *pLuaState)
{
    return luaObjectAnimationQuery(pLuaState, "GetAnimName");
}

int luaObjectGetAnimationNumber(lua_State *pLuaState)
{
    return luaObjectAnimationQuery(pLuaState, "GetAnimNbr");
}

int luaObjectBlendAnimation(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    if (!pRuntime->requestActorAction(
        luaObjectProxyHandle(pLuaState, 1),
        "blendanim",
        luaMovementArguments(pLuaState, 8, 2),
        0))
    {
        pRuntime->recordUnimplementedCommand("blendanim", {}, 0, "object actor action request");
    }
    return 0;
}

int luaObjectClientFxCommand(lua_State *pLuaState, const std::string &command)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const std::string handle = luaObjectProxyHandle(pLuaState, 1);
    if (handle.empty())
    {
        return 0;
    }

    std::vector<std::string> arguments = luaServiceArguments(pLuaState, 8, 2);
    if (arguments.empty())
    {
        pRuntime->recordUnimplementedCommand(command, {}, 0, "object client FX request");
        return 0;
    }

    if (command == "createfx")
    {
        arguments.insert(arguments.begin() + 1, handle);
    }
    else
    {
        arguments.insert(arguments.begin(), handle);
    }

    const std::string argumentsText = scriptArgumentsText(arguments);
    if (!pRuntime->executeCommand(command, argumentsText, 0, "object client FX request"))
    {
        pRuntime->recordUnimplementedCommand(command, argumentsText, 0, "object client FX request");
    }
    return 0;
}

int luaObjectDoClientFx(lua_State *pLuaState)
{
    return luaObjectClientFxCommand(pLuaState, "doclientfx");
}

int luaObjectCreateFx(lua_State *pLuaState)
{
    return luaObjectClientFxCommand(pLuaState, "createfx");
}

int luaObjectSetModelFilenames(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    pRuntime->setObjectModelFilenames(
        luaObjectProxyHandle(pLuaState, 1),
        luaServiceArguments(pLuaState, 8, 2));
    return 0;
}

int luaObjectAttachmentCommand(lua_State *pLuaState, const std::string &command)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    if (!pRuntime->requestAttachment(
        luaObjectProxyHandle(pLuaState, 1),
        command,
        luaMovementArguments(pLuaState, 8, 2),
        0))
    {
        pRuntime->recordUnimplementedCommand(command, {}, 0, "object attachment request");
    }
    return 0;
}

int luaObjectAttachProp(lua_State *pLuaState)
{
    return luaObjectAttachmentCommand(pLuaState, "attachprop");
}

int luaObjectDetachProp(lua_State *pLuaState)
{
    return luaObjectAttachmentCommand(pLuaState, "detachprop");
}

int luaObjectMovementCommand(lua_State *pLuaState, const std::string &command)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const std::string handle = luaObjectProxyHandle(pLuaState, 1);
    if (handle.empty())
    {
        return 0;
    }

    if (!pRuntime->requestMovement(handle, command, luaMovementArguments(pLuaState, 8, 2), 0))
    {
        pRuntime->recordUnimplementedCommand(command, {}, 0, "object movement request");
    }
    return 0;
}

int luaObjectMoveToPos(lua_State *pLuaState)
{
    return luaObjectMovementCommand(pLuaState, "movetopos");
}

int luaObjectRunToPos(lua_State *pLuaState)
{
    return luaObjectMovementCommand(pLuaState, "runtopos");
}

int luaObjectWalkToPos(lua_State *pLuaState)
{
    return luaObjectMovementCommand(pLuaState, "walktopos");
}

int luaObjectWalkTo(lua_State *pLuaState)
{
    return luaObjectMovementCommand(pLuaState, "walkto");
}

int luaObjectRunTo(lua_State *pLuaState)
{
    return luaObjectMovementCommand(pLuaState, "runto");
}

int luaObjectMoveDir(lua_State *pLuaState)
{
    return luaObjectMovementCommand(pLuaState, "movedir");
}

int luaObjectFaceObject(lua_State *pLuaState)
{
    return luaObjectMovementCommand(pLuaState, "faceobject");
}

int luaObjectFacePos(lua_State *pLuaState)
{
    return luaObjectMovementCommand(pLuaState, "facepos");
}

int luaObjectStop(lua_State *pLuaState)
{
    return luaObjectMovementCommand(pLuaState, "stop");
}

int luaObjectWalk(lua_State *pLuaState)
{
    return luaObjectMovementCommand(pLuaState, "walk");
}

int luaObjectRun(lua_State *pLuaState)
{
    return luaObjectMovementCommand(pLuaState, "run");
}

int luaObjectRotate(lua_State *pLuaState)
{
    return luaObjectMovementCommand(pLuaState, "rotate");
}

int luaObjectFaceDir(lua_State *pLuaState)
{
    return luaObjectMovementCommand(pLuaState, "facedir");
}

int luaObjectStrafe(lua_State *pLuaState)
{
    return luaObjectMovementCommand(pLuaState, "strafe");
}

int luaObjectSetPushBack(lua_State *pLuaState)
{
    return luaObjectMovementCommand(pLuaState, "setpushback");
}

int luaObjectTurnLeft(lua_State *pLuaState)
{
    return luaObjectMovementCommand(pLuaState, "turnleft");
}

std::string objectHandleFromLua(Mm9ScriptRuntime &runtime, lua_State *pLuaState, int index);

int luaObjectSetIdle(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    pRuntime->setObjectIdle(luaObjectProxyHandle(pLuaState, 1));
    return 0;
}

int luaObjectSetStuck(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    pRuntime->setObjectStuck(luaObjectProxyHandle(pLuaState, 1));
    return 0;
}

int luaObjectAddRelation(lua_State *pLuaState, const std::string &operation)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const std::string token = luaArgumentText(pLuaState, 2);
    if (!token.empty())
    {
        pRuntime->addObjectRelation(luaObjectProxyHandle(pLuaState, 1), operation, token);
    }
    return 0;
}

int luaObjectRemoveRelation(lua_State *pLuaState, const std::string &operation)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const std::string token = luaArgumentText(pLuaState, 2);
    if (!token.empty())
    {
        pRuntime->removeObjectRelation(luaObjectProxyHandle(pLuaState, 1), operation, token);
    }
    return 0;
}

int luaObjectAddFriend(lua_State *pLuaState)
{
    return luaObjectAddRelation(pLuaState, "addfriend");
}

int luaObjectAddEnemy(lua_State *pLuaState)
{
    return luaObjectAddRelation(pLuaState, "addenemy");
}

int luaObjectRemoveFriend(lua_State *pLuaState)
{
    return luaObjectRemoveRelation(pLuaState, "removefriend");
}

int luaObjectRemoveEnemy(lua_State *pLuaState)
{
    return luaObjectRemoveRelation(pLuaState, "removeenemy");
}

int luaObjectIsFriend(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushboolean(pLuaState, 0);
        return 1;
    }

    const bool isFriend = pRuntime->objectIsFriend(
        luaObjectProxyHandle(pLuaState, 1),
        objectHandleFromLua(*pRuntime, pLuaState, 2));
    lua_pushboolean(pLuaState, isFriend ? 1 : 0);
    return 1;
}

int luaObjectAiDistanceTo(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushinteger(pLuaState, 0);
        return 1;
    }

    lua_pushnumber(
        pLuaState,
        pRuntime->objectDistanceTo(
            luaObjectProxyHandle(pLuaState, 1),
            objectHandleFromLua(*pRuntime, pLuaState, 2)));
    return 1;
}

int luaObjectAiCommand(lua_State *pLuaState, const std::string &operation)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    if (!pRuntime->requestAi(
        luaObjectProxyHandle(pLuaState, 1),
        operation,
        luaMovementArguments(pLuaState, 8, 2),
        0))
    {
        pRuntime->recordUnimplementedCommand(operation, {}, 0, "object AI request");
    }
    return 0;
}

int luaObjectAttack(lua_State *pLuaState)
{
    return luaObjectAiCommand(pLuaState, "attack");
}

int luaObjectRangeAttack(lua_State *pLuaState)
{
    return luaObjectAiCommand(pLuaState, "rangeattack");
}

int luaObjectFindTargets(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const int metadataIndex = luaTrailingMetadataIndex(pLuaState);
    const std::vector<std::string> arguments = luaCommandArguments(pLuaState, metadataIndex, 2);
    if (!pRuntime->executeCommand("FindTargets", scriptArgumentsText(arguments),
        luaMetadataLine(pLuaState, metadataIndex), {}))
    {
        pRuntime->recordUnimplementedCommand("findtargets", scriptArgumentsText(arguments), 0,
            "object AI request");
    }
    return 0;
}

int luaObjectFindHidingPlace(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushnil(pLuaState);
        return 1;
    }

    pushObjectProxy(pLuaState, *pRuntime, luaObjectProxyHandle(pLuaState, 1));
    return 1;
}

int luaObjectActorActionCommand(lua_State *pLuaState, const std::string &operation)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    if (!pRuntime->requestActorAction(
        luaObjectProxyHandle(pLuaState, 1),
        operation,
        luaMovementArguments(pLuaState, 8, 2),
        0))
    {
        pRuntime->recordUnimplementedCommand(operation, {}, 0, "object actor action request");
    }
    return 0;
}

int luaObjectSetCrouch(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const int32_t value = scriptValueTruthy(
        evaluateScriptExpression(*pRuntime, luaScriptExpressionText(pLuaState, 2))) ? 1 : 0;
    pRuntime->executeCommand(
        "setstat",
        luaObjectProxyHandle(pLuaState, 1) + ", Crouch, " + std::to_string(value),
        0,
        "object:setCrouch");
    return 0;
}

int luaObjectSetTargetLostTime(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    pRuntime->executeCommand(
        "setstat",
        luaObjectProxyHandle(pLuaState, 1) + ", TargetLostTime, " + luaScriptExpressionText(pLuaState, 2),
        0,
        "object:setTargetLostTime");
    return 0;
}

int luaObjectLiquidContainer(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushnil(pLuaState);
        return 1;
    }

    pushObjectProxy(pLuaState, *pRuntime, luaObjectProxyHandle(pLuaState, 1));
    return 1;
}

int luaObjectContainer(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushnil(pLuaState);
        return 1;
    }

    pushObjectProxy(pLuaState, *pRuntime, luaObjectProxyHandle(pLuaState, 1));
    return 1;
}

int luaObjectSocketPos(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushinteger(pLuaState, 0);
        lua_pushinteger(pLuaState, 0);
        lua_pushinteger(pLuaState, 0);
        return 3;
    }

    const std::string handle = luaObjectProxyHandle(pLuaState, 1);
    const auto positionIterator = pRuntime->state().objectPositions.find(handle);
    const Mm9ScriptRuntimeVec3 position = positionIterator != pRuntime->state().objectPositions.end()
        ? positionIterator->second
        : Mm9ScriptRuntimeVec3();
    lua_pushnumber(pLuaState, position.x);
    lua_pushnumber(pLuaState, position.y);
    lua_pushnumber(pLuaState, position.z);
    return 3;
}

int luaObjectJump(lua_State *pLuaState)
{
    return luaObjectActorActionCommand(pLuaState, "jump");
}

int luaObjectTaunt(lua_State *pLuaState)
{
    return luaObjectActorActionCommand(pLuaState, "taunt");
}

int luaObjectAware(lua_State *pLuaState)
{
    return luaObjectActorActionCommand(pLuaState, "aware");
}

int luaObjectLaunch(lua_State *pLuaState)
{
    return luaObjectActorActionCommand(pLuaState, "launch");
}

int luaObjectConverse(lua_State *pLuaState)
{
    return luaObjectActorActionCommand(pLuaState, "converse");
}

int luaObjectResumeWait(lua_State *pLuaState)
{
    return luaObjectActorActionCommand(pLuaState, "resumewait");
}

int luaObjectPauseWait(lua_State *pLuaState)
{
    return luaObjectActorActionCommand(pLuaState, "pausewait");
}

int luaObjectAiQuery(lua_State *pLuaState, const std::string &operation)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushboolean(pLuaState, 0);
        return 1;
    }

    lua_pushboolean(
        pLuaState,
        pRuntime->objectAiQuery(luaObjectProxyHandle(pLuaState, 1), operation) ? 1 : 0);
    return 1;
}

int luaObjectRuntimeQuery(lua_State *pLuaState, const std::string &operation)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushboolean(pLuaState, 0);
        return 1;
    }

    const std::string handle = luaObjectProxyHandle(pLuaState, 1);
    bool result = false;
    if (operation == "ismoving")
    {
        const auto stateIterator = pRuntime->state().objectAiStates.find(handle);
        result = stateIterator != pRuntime->state().objectAiStates.end()
            && stateIterator->second != "idle"
            && stateIterator->second != "stopped";
        result = result || std::any_of(
            pRuntime->state().movementRequests.begin(),
            pRuntime->state().movementRequests.end(),
            [&](const Mm9ScriptRuntimeMovementRequest &request)
            {
                return request.objectHandle == handle;
            });
    }
    else if (operation == "isonground")
    {
        const auto objectIterator = pRuntime->state().objectStats.find(handle);
        if (objectIterator != pRuntime->state().objectStats.end())
        {
            const auto groundedIterator = std::find_if(
                objectIterator->second.begin(),
                objectIterator->second.end(),
                [](const std::pair<const std::string, int32_t> &stat)
                {
                    return lowerCopy(stat.first) == "grounded";
                });
            const auto onGroundIterator = std::find_if(
                objectIterator->second.begin(),
                objectIterator->second.end(),
                [](const std::pair<const std::string, int32_t> &stat)
                {
                    return lowerCopy(stat.first) == "onground";
                });
            result = groundedIterator != objectIterator->second.end() && groundedIterator->second != 0;
            result = result || (onGroundIterator != objectIterator->second.end() && onGroundIterator->second != 0);
        }
    }
    else if (operation == "isdead")
    {
        const auto aiIterator = pRuntime->state().objectAiStates.find(handle);
        const auto removedIterator = pRuntime->state().removedObjects.find(handle);
        result = (aiIterator != pRuntime->state().objectAiStates.end() && aiIterator->second == "dead")
            || (removedIterator != pRuntime->state().removedObjects.end() && removedIterator->second);
    }
    else if (operation == "canreachtarget")
    {
        const std::string targetHandle = pRuntime->objectTargetHandle(handle);
        result = !targetHandle.empty();
    }
    else if (operation == "isworldobject")
    {
        result = handle != "mm9:player" && !handle.empty();
    }

    lua_pushboolean(pLuaState, result ? 1 : 0);
    return 1;
}

int luaObjectRuntimeTargetQuery(lua_State *pLuaState, const std::string &operation)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushboolean(pLuaState, 0);
        return 1;
    }

    const std::string targetHandle = objectHandleFromLua(*pRuntime, pLuaState, 2);
    bool result = false;
    if (operation == "canreachobject" || operation == "isfacing")
    {
        result = !targetHandle.empty();
    }
    else if (operation == "isclearshot")
    {
        const auto removedIterator = pRuntime->state().removedObjects.find(targetHandle);
        result = !targetHandle.empty()
            && (removedIterator == pRuntime->state().removedObjects.end() || !removedIterator->second);
    }

    lua_pushboolean(pLuaState, result ? 1 : 0);
    if (operation == "isclearshot")
    {
        lua_pushnil(pLuaState);
        return 2;
    }
    return 1;
}

int luaObjectCanAttack(lua_State *pLuaState)
{
    return luaObjectAiQuery(pLuaState, "canattack");
}

int luaObjectCanRangeAttack(lua_State *pLuaState)
{
    return luaObjectAiQuery(pLuaState, "canrangeattack");
}

int luaObjectHasRangeAttack(lua_State *pLuaState)
{
    return luaObjectAiQuery(pLuaState, "hasrangeattack");
}

int luaObjectIsTargetInRange(lua_State *pLuaState)
{
    return luaObjectAiQuery(pLuaState, "istargetinrange");
}

int luaObjectIsAttacking(lua_State *pLuaState)
{
    return luaObjectAiQuery(pLuaState, "isattacking");
}

int luaObjectIsMoving(lua_State *pLuaState)
{
    return luaObjectRuntimeQuery(pLuaState, "ismoving");
}

int luaObjectIsOnGround(lua_State *pLuaState)
{
    return luaObjectRuntimeQuery(pLuaState, "isonground");
}

int luaObjectIsDead(lua_State *pLuaState)
{
    return luaObjectRuntimeQuery(pLuaState, "isdead");
}

int luaObjectCanReachTarget(lua_State *pLuaState)
{
    return luaObjectRuntimeQuery(pLuaState, "canreachtarget");
}

int luaObjectCanReachObject(lua_State *pLuaState)
{
    return luaObjectRuntimeTargetQuery(pLuaState, "canreachobject");
}

int luaObjectIsFacing(lua_State *pLuaState)
{
    return luaObjectRuntimeTargetQuery(pLuaState, "isfacing");
}

int luaObjectShouldRunAwayFrom(lua_State *pLuaState)
{
    return luaObjectRuntimeTargetQuery(pLuaState, "shouldrunaway");
}

int luaObjectIsClearShot(lua_State *pLuaState)
{
    return luaObjectRuntimeTargetQuery(pLuaState, "isclearshot");
}

int luaObjectIsWorldObject(lua_State *pLuaState)
{
    return luaObjectRuntimeQuery(pLuaState, "isworldobject");
}

int luaObjectIsFear(lua_State *pLuaState)
{
    return luaObjectRuntimeQuery(pLuaState, "isfear");
}

int luaObjectIsInNoRunZone(lua_State *pLuaState)
{
    return luaObjectRuntimeQuery(pLuaState, "isinnorunzone");
}

int luaObjectSendAlert(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    std::vector<std::string> arguments;
    if (lua_gettop(pLuaState) >= 2)
    {
        if (lua_isnil(pLuaState, 2))
        {
            arguments.push_back("NULL");
        }
        else if (lua_istable(pLuaState, 2))
        {
            arguments.push_back(luaObjectProxyHandle(pLuaState, 2));
        }
        else
        {
            arguments.push_back(luaScriptExpressionText(pLuaState, 2));
        }
    }

    if (!pRuntime->requestAi(luaObjectProxyHandle(pLuaState, 1), "sendalert", arguments, 0))
    {
        pRuntime->recordUnimplementedCommand("sendalert", scriptArgumentsText(arguments), 0, "object AI request");
    }
    return 0;
}

int luaObjectHelp(lua_State *pLuaState)
{
    return luaObjectAiCommand(pLuaState, "help");
}

int luaObjectEstimateRangeAttackHit(lua_State *pLuaState)
{
    return luaObjectAiCommand(pLuaState, "estimaterangeattackhit");
}

int luaObjectLand(lua_State *pLuaState)
{
    return luaObjectAiCommand(pLuaState, "land");
}

int luaPresentationCommand(lua_State *pLuaState, const std::string &command)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const std::vector<std::string> arguments = luaServiceArguments(pLuaState, 8, 2);
    const size_t line = luaMetadataLine(pLuaState, 8);
    const std::string raw = luaMetadataRaw(pLuaState, 8);
    const std::string argumentsText = scriptArgumentsText(arguments);
    if (!pRuntime->executeCommand(command, argumentsText, line, raw))
    {
        pRuntime->recordUnimplementedCommand(command, argumentsText, line, raw);
    }
    return 0;
}

int luaScreenFadeOut(lua_State *pLuaState)
{
    return luaPresentationCommand(pLuaState, "screenfadeout");
}

int luaScreenFadeIn(lua_State *pLuaState)
{
    return luaPresentationCommand(pLuaState, "screenfadein");
}

int luaLetterBox(lua_State *pLuaState)
{
    return luaPresentationCommand(pLuaState, "letterbox");
}

int luaRolloverText(lua_State *pLuaState)
{
    return luaPresentationCommand(pLuaState, "rollovertext");
}

std::string objectTargetHandleFromLua(Mm9ScriptRuntime &runtime, lua_State *pLuaState, int index)
{
    const Mm9ScriptValue value = scriptValueFromLua(pLuaState, index);
    if (value.kind == Mm9ScriptValueKind::Null)
    {
        return {};
    }
    if (value.kind == Mm9ScriptValueKind::Handle)
    {
        return value.text;
    }
    if (value.kind == Mm9ScriptValueKind::Number)
    {
        return value.number == 0.0 ? std::string() : value.text;
    }

    const std::string lowered = lowerCopy(trimCopy(value.text));
    if (lowered == "null" || lowered == "nil" || lowered == "0")
    {
        return {};
    }

    return runtime.resolveScriptString(value.text);
}

std::string objectHandleFromLua(Mm9ScriptRuntime &runtime, lua_State *pLuaState, int index)
{
    const Mm9ScriptValue value = scriptValueFromLua(pLuaState, index);
    if (value.kind == Mm9ScriptValueKind::Null)
    {
        return {};
    }
    if (value.kind == Mm9ScriptValueKind::Handle)
    {
        return value.text;
    }
    if (value.kind == Mm9ScriptValueKind::Number && value.number == 0.0)
    {
        return {};
    }
    if (value.kind == Mm9ScriptValueKind::String)
    {
        const std::string lowered = lowerCopy(trimCopy(value.text));
        if (lowered == "null" || lowered == "nil" || lowered == "0")
        {
            return {};
        }
    }

    return runtime.resolveScriptString(value.text);
}

int luaObjectTarget(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushnil(pLuaState);
        return 1;
    }

    const std::string targetHandle = pRuntime->objectTargetHandle(luaObjectProxyHandle(pLuaState, 1));
    if (targetHandle.empty())
    {
        lua_pushnil(pLuaState);
    }
    else
    {
        pushObjectProxy(pLuaState, *pRuntime, targetHandle);
    }
    return 1;
}

int luaObjectSetTarget(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const std::string objectHandle = luaObjectProxyHandle(pLuaState, 1);
    pRuntime->setObjectTargetHandle(objectHandle, objectTargetHandleFromLua(*pRuntime, pLuaState, 2));
    return 0;
}

int luaObjectLink(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    pRuntime->createObjectLink(
        luaObjectProxyHandle(pLuaState, 1),
        objectHandleFromLua(*pRuntime, pLuaState, 2));
    return 0;
}

int luaObjectUnlink(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    pRuntime->breakObjectLink(
        luaObjectProxyHandle(pLuaState, 1),
        objectHandleFromLua(*pRuntime, pLuaState, 2));
    return 0;
}

int luaObjectLinks(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_newtable(pLuaState);
        return 1;
    }

    const std::vector<std::string> linkedHandles =
        pRuntime->objectLinkedHandles(luaObjectProxyHandle(pLuaState, 1));
    lua_newtable(pLuaState);
    int32_t luaIndex = 1;
    for (const std::string &linkedHandle : linkedHandles)
    {
        pushObjectProxy(pLuaState, *pRuntime, linkedHandle);
        lua_rawseti(pLuaState, -2, luaIndex);
        ++luaIndex;
    }
    return 1;
}

int luaObjectDistanceTo(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushinteger(pLuaState, 0);
        return 1;
    }

    const std::string sourceHandle = luaObjectProxyHandle(pLuaState, 1);
    const std::string targetHandle = objectHandleFromLua(*pRuntime, pLuaState, 2);
    const auto sourcePositionIterator = pRuntime->state().objectPositions.find(sourceHandle);
    const auto targetPositionIterator = pRuntime->state().objectPositions.find(targetHandle);
    const Mm9ScriptRuntimeVec3 sourcePosition =
        sourcePositionIterator != pRuntime->state().objectPositions.end()
            ? sourcePositionIterator->second
            : Mm9ScriptRuntimeVec3();
    const Mm9ScriptRuntimeVec3 targetPosition =
        targetPositionIterator != pRuntime->state().objectPositions.end()
            ? targetPositionIterator->second
            : Mm9ScriptRuntimeVec3();
    lua_pushnumber(pLuaState, scriptVectorDistance(sourcePosition, targetPosition));
    return 1;
}

int luaObjectRemove(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const std::string handle = luaObjectProxyHandle(pLuaState, 1);
    if (handle.empty())
    {
        return 0;
    }

    pRuntime->executeCommand("removeobject", handle, 0, "object:remove");
    return 0;
}

int luaObjectDamage(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    if (!pRuntime->damageObject(
        luaObjectProxyHandle(pLuaState, 1),
        luaMovementArguments(pLuaState, 8, 2),
        0))
    {
        pRuntime->recordUnimplementedCommand("damage", {}, 0, "object damage request");
    }
    return 0;
}

int luaObjectDie(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    if (!pRuntime->killObject(luaObjectProxyHandle(pLuaState, 1)))
    {
        pRuntime->recordUnimplementedCommand("die", {}, 0, "object death request");
    }
    return 0;
}

void pushObjectProxyMethod(lua_State *pLuaState, Mm9ScriptRuntime &runtime, const char *pName, lua_CFunction function)
{
    lua_pushlightuserdata(pLuaState, &runtime);
    lua_pushcclosure(pLuaState, function, 1);
    lua_setfield(pLuaState, -2, pName);
}

void pushObjectProxy(lua_State *pLuaState, Mm9ScriptRuntime &runtime, const std::string &handle)
{
    lua_newtable(pLuaState);
    lua_pushstring(pLuaState, handle.c_str());
    lua_setfield(pLuaState, -2, "__mm9Handle");
    pushObjectProxyMethod(pLuaState, runtime, "handle", luaObjectHandle);
    pushObjectProxyMethod(pLuaState, runtime, "name", luaObjectName);
    pushObjectProxyMethod(pLuaState, runtime, "className", luaObjectClassName);
    pushObjectProxyMethod(pLuaState, runtime, "isClass", luaObjectIsClass);
    pushObjectProxyMethod(pLuaState, runtime, "isPlayer", luaObjectIsPlayer);
    pushObjectProxyMethod(pLuaState, runtime, "isActor", luaObjectIsActor);
    pushObjectProxyMethod(pLuaState, runtime, "isAi", luaObjectIsAi);
    pushObjectProxyMethod(pLuaState, runtime, "isActive", luaObjectIsActive);
    pushObjectProxyMethod(pLuaState, runtime, "isVisible", luaObjectIsVisible);
    pushObjectProxyMethod(pLuaState, runtime, "trigger", luaObjectTrigger);
    pushObjectProxyMethod(pLuaState, runtime, "pos", luaObjectPos);
    pushObjectProxyMethod(pLuaState, runtime, "setPos", luaObjectSetPos);
    pushObjectProxyMethod(pLuaState, runtime, "rotation", luaObjectRotation);
    pushObjectProxyMethod(pLuaState, runtime, "setRotation", luaObjectSetRotation);
    pushObjectProxyMethod(pLuaState, runtime, "forwardDir", luaObjectForwardDir);
    pushObjectProxyMethod(pLuaState, runtime, "reverseDir", luaObjectReverseDir);
    pushObjectProxyMethod(pLuaState, runtime, "rightDir", luaObjectRightDir);
    pushObjectProxyMethod(pLuaState, runtime, "leftDir", luaObjectLeftDir);
    pushObjectProxyMethod(pLuaState, runtime, "velocity", luaObjectVelocity);
    pushObjectProxyMethod(pLuaState, runtime, "dims", luaObjectDims);
    pushObjectProxyMethod(pLuaState, runtime, "minMax", luaObjectMinMax);
    pushObjectProxyMethod(pLuaState, runtime, "setVelocity", luaObjectSetVelocity);
    pushObjectProxyMethod(pLuaState, runtime, "setNumberProperty", luaObjectSetNumberProperty);
    pushObjectProxyMethod(pLuaState, runtime, "numberProperty", luaObjectNumberProperty);
    pushObjectProxyMethod(pLuaState, runtime, "setStringProperty", luaObjectSetStringProperty);
    pushObjectProxyMethod(pLuaState, runtime, "stringProperty", luaObjectStringProperty);
    pushObjectProxyMethod(pLuaState, runtime, "setFlag", luaObjectSetFlag);
    pushObjectProxyMethod(pLuaState, runtime, "flag", luaObjectFlag);
    pushObjectProxyMethod(pLuaState, runtime, "getStat", luaObjectGetStat);
    pushObjectProxyMethod(pLuaState, runtime, "setStat", luaObjectSetStat);
    pushObjectProxyMethod(pLuaState, runtime, "setCrouch", luaObjectSetCrouch);
    pushObjectProxyMethod(pLuaState, runtime, "setTargetLostTime", luaObjectSetTargetLostTime);
    pushObjectProxyMethod(pLuaState, runtime, "liquidContainer", luaObjectLiquidContainer);
    pushObjectProxyMethod(pLuaState, runtime, "container", luaObjectContainer);
    pushObjectProxyMethod(pLuaState, runtime, "socketPos", luaObjectSocketPos);
    pushObjectProxyMethod(pLuaState, runtime, "playAnimation", luaObjectPlayAnimation);
    pushObjectProxyMethod(pLuaState, runtime, "playAnimationCommand", luaObjectPlayAnimationCommand);
    pushObjectProxyMethod(pLuaState, runtime, "loopAnimation", luaObjectLoopAnimation);
    pushObjectProxyMethod(pLuaState, runtime, "playAnimSound", luaObjectPlayAnimSound);
    pushObjectProxyMethod(pLuaState, runtime, "setAnimationPlaying", luaObjectSetAnimationPlaying);
    pushObjectProxyMethod(pLuaState, runtime, "getCurrentAnimation", luaObjectGetCurrentAnimation);
    pushObjectProxyMethod(pLuaState, runtime, "getAnimationName", luaObjectGetAnimationName);
    pushObjectProxyMethod(pLuaState, runtime, "getAnimationNumber", luaObjectGetAnimationNumber);
    pushObjectProxyMethod(pLuaState, runtime, "blendAnimation", luaObjectBlendAnimation);
    pushObjectProxyMethod(pLuaState, runtime, "doClientFx", luaObjectDoClientFx);
    pushObjectProxyMethod(pLuaState, runtime, "createFx", luaObjectCreateFx);
    pushObjectProxyMethod(pLuaState, runtime, "setModelFilenames", luaObjectSetModelFilenames);
    pushObjectProxyMethod(pLuaState, runtime, "attachProp", luaObjectAttachProp);
    pushObjectProxyMethod(pLuaState, runtime, "detachProp", luaObjectDetachProp);
    pushObjectProxyMethod(pLuaState, runtime, "moveToPos", luaObjectMoveToPos);
    pushObjectProxyMethod(pLuaState, runtime, "runToPos", luaObjectRunToPos);
    pushObjectProxyMethod(pLuaState, runtime, "walkToPos", luaObjectWalkToPos);
    pushObjectProxyMethod(pLuaState, runtime, "walkTo", luaObjectWalkTo);
    pushObjectProxyMethod(pLuaState, runtime, "runTo", luaObjectRunTo);
    pushObjectProxyMethod(pLuaState, runtime, "moveDir", luaObjectMoveDir);
    pushObjectProxyMethod(pLuaState, runtime, "faceObject", luaObjectFaceObject);
    pushObjectProxyMethod(pLuaState, runtime, "facePos", luaObjectFacePos);
    pushObjectProxyMethod(pLuaState, runtime, "stop", luaObjectStop);
    pushObjectProxyMethod(pLuaState, runtime, "walk", luaObjectWalk);
    pushObjectProxyMethod(pLuaState, runtime, "run", luaObjectRun);
    pushObjectProxyMethod(pLuaState, runtime, "rotate", luaObjectRotate);
    pushObjectProxyMethod(pLuaState, runtime, "faceDir", luaObjectFaceDir);
    pushObjectProxyMethod(pLuaState, runtime, "strafe", luaObjectStrafe);
    pushObjectProxyMethod(pLuaState, runtime, "setPushBack", luaObjectSetPushBack);
    pushObjectProxyMethod(pLuaState, runtime, "turnLeft", luaObjectTurnLeft);
    pushObjectProxyMethod(pLuaState, runtime, "setIdle", luaObjectSetIdle);
    pushObjectProxyMethod(pLuaState, runtime, "setStuck", luaObjectSetStuck);
    pushObjectProxyMethod(pLuaState, runtime, "addFriend", luaObjectAddFriend);
    pushObjectProxyMethod(pLuaState, runtime, "addEnemy", luaObjectAddEnemy);
    pushObjectProxyMethod(pLuaState, runtime, "removeFriend", luaObjectRemoveFriend);
    pushObjectProxyMethod(pLuaState, runtime, "removeEnemy", luaObjectRemoveEnemy);
    pushObjectProxyMethod(pLuaState, runtime, "isFriend", luaObjectIsFriend);
    pushObjectProxyMethod(pLuaState, runtime, "aiDistanceTo", luaObjectAiDistanceTo);
    pushObjectProxyMethod(pLuaState, runtime, "sendAlert", luaObjectSendAlert);
    pushObjectProxyMethod(pLuaState, runtime, "attack", luaObjectAttack);
    pushObjectProxyMethod(pLuaState, runtime, "rangeAttack", luaObjectRangeAttack);
    pushObjectProxyMethod(pLuaState, runtime, "findTargets", luaObjectFindTargets);
    pushObjectProxyMethod(pLuaState, runtime, "findHidingPlace", luaObjectFindHidingPlace);
    pushObjectProxyMethod(pLuaState, runtime, "jump", luaObjectJump);
    pushObjectProxyMethod(pLuaState, runtime, "taunt", luaObjectTaunt);
    pushObjectProxyMethod(pLuaState, runtime, "aware", luaObjectAware);
    pushObjectProxyMethod(pLuaState, runtime, "launch", luaObjectLaunch);
    pushObjectProxyMethod(pLuaState, runtime, "converse", luaObjectConverse);
    pushObjectProxyMethod(pLuaState, runtime, "resumeWait", luaObjectResumeWait);
    pushObjectProxyMethod(pLuaState, runtime, "pauseWait", luaObjectPauseWait);
    pushObjectProxyMethod(pLuaState, runtime, "canAttack", luaObjectCanAttack);
    pushObjectProxyMethod(pLuaState, runtime, "canRangeAttack", luaObjectCanRangeAttack);
    pushObjectProxyMethod(pLuaState, runtime, "hasRangeAttack", luaObjectHasRangeAttack);
    pushObjectProxyMethod(pLuaState, runtime, "isTargetInRange", luaObjectIsTargetInRange);
    pushObjectProxyMethod(pLuaState, runtime, "isAttacking", luaObjectIsAttacking);
    pushObjectProxyMethod(pLuaState, runtime, "isMoving", luaObjectIsMoving);
    pushObjectProxyMethod(pLuaState, runtime, "isOnGround", luaObjectIsOnGround);
    pushObjectProxyMethod(pLuaState, runtime, "isDead", luaObjectIsDead);
    pushObjectProxyMethod(pLuaState, runtime, "canReachTarget", luaObjectCanReachTarget);
    pushObjectProxyMethod(pLuaState, runtime, "canReachObject", luaObjectCanReachObject);
    pushObjectProxyMethod(pLuaState, runtime, "isFacing", luaObjectIsFacing);
    pushObjectProxyMethod(pLuaState, runtime, "shouldRunAwayFrom", luaObjectShouldRunAwayFrom);
    pushObjectProxyMethod(pLuaState, runtime, "isClearShot", luaObjectIsClearShot);
    pushObjectProxyMethod(pLuaState, runtime, "isWorldObject", luaObjectIsWorldObject);
    pushObjectProxyMethod(pLuaState, runtime, "isFear", luaObjectIsFear);
    pushObjectProxyMethod(pLuaState, runtime, "isInNoRunZone", luaObjectIsInNoRunZone);
    pushObjectProxyMethod(pLuaState, runtime, "help", luaObjectHelp);
    pushObjectProxyMethod(pLuaState, runtime, "estimateRangeAttackHit", luaObjectEstimateRangeAttackHit);
    pushObjectProxyMethod(pLuaState, runtime, "land", luaObjectLand);
    pushObjectProxyMethod(pLuaState, runtime, "target", luaObjectTarget);
    pushObjectProxyMethod(pLuaState, runtime, "setTarget", luaObjectSetTarget);
    pushObjectProxyMethod(pLuaState, runtime, "link", luaObjectLink);
    pushObjectProxyMethod(pLuaState, runtime, "unlink", luaObjectUnlink);
    pushObjectProxyMethod(pLuaState, runtime, "links", luaObjectLinks);
    pushObjectProxyMethod(pLuaState, runtime, "distanceTo", luaObjectDistanceTo);
    pushObjectProxyMethod(pLuaState, runtime, "remove", luaObjectRemove);
    pushObjectProxyMethod(pLuaState, runtime, "damage", luaObjectDamage);
    pushObjectProxyMethod(pLuaState, runtime, "die", luaObjectDie);
}

std::string objectHandleForLuaValue(Mm9ScriptRuntime &runtime, const std::string &value)
{
    const std::string resolved = runtime.resolveScriptString(value);
    const std::string handle = runtime.objectHandleForName(resolved);
    return !handle.empty() ? handle : runtime.objectHandleForName(value);
}

int luaSelfObject(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushnil(pLuaState);
        return 1;
    }

    pushObjectProxy(pLuaState, *pRuntime, pRuntime->objectHandleForName("hMe"));
    return 1;
}

int luaPlayerObject(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushnil(pLuaState);
        return 1;
    }

    pushObjectProxy(pLuaState, *pRuntime, "mm9:player");
    return 1;
}

int luaObjectByName(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushnil(pLuaState);
        return 1;
    }

    pushObjectProxy(pLuaState, *pRuntime, objectHandleForLuaValue(*pRuntime, luaArgumentText(pLuaState, 2)));
    return 1;
}

int luaObjectByNameOrNil(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushnil(pLuaState);
        return 1;
    }

    const std::string handle = objectHandleForLuaValue(*pRuntime, luaArgumentText(pLuaState, 2));
    if (handle.empty())
    {
        lua_pushnil(pLuaState);
        return 1;
    }

    pushObjectProxy(pLuaState, *pRuntime, handle);
    return 1;
}

int luaSpawnCommand(lua_State *pLuaState, bool extended)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushnil(pLuaState);
        return 1;
    }

    const int metadataIndex = lua_istable(pLuaState, lua_gettop(pLuaState)) ? lua_gettop(pLuaState) : 8;
    const std::vector<std::string> arguments = luaMovementArguments(pLuaState, metadataIndex, 2);
    const std::string handle = pRuntime->spawnObject(
        "",
        arguments,
        extended,
        luaMetadataLine(pLuaState, metadataIndex));
    if (handle.empty())
    {
        lua_pushnil(pLuaState);
        return 1;
    }

    pushObjectProxy(pLuaState, *pRuntime, handle);
    return 1;
}

int luaSpawn(lua_State *pLuaState)
{
    return luaSpawnCommand(pLuaState, false);
}

int luaSpawn2(lua_State *pLuaState)
{
    return luaSpawnCommand(pLuaState, true);
}

int luaParamObject(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushnil(pLuaState);
        return 1;
    }

    const int32_t paramIndex = static_cast<int32_t>(lua_tointeger(pLuaState, 2));
    const std::vector<std::string> &params = pRuntime->dialogueRuntime().owner().scriptParams;
    const std::string value = paramIndex >= 0 && static_cast<size_t>(paramIndex) < params.size()
        ? params[static_cast<size_t>(paramIndex)]
        : "";
    pushObjectProxy(pLuaState, *pRuntime, objectHandleForLuaValue(*pRuntime, value));
    return 1;
}

int luaParam(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushstring(pLuaState, "");
        return 1;
    }

    const int32_t paramIndex = static_cast<int32_t>(lua_tointeger(pLuaState, 2));
    const std::vector<std::string> &params = pRuntime->dialogueRuntime().owner().scriptParams;
    const std::string value = paramIndex >= 0 && static_cast<size_t>(paramIndex) < params.size()
        ? params[static_cast<size_t>(paramIndex)]
        : "";
    lua_pushstring(pLuaState, value.c_str());
    return 1;
}

void pushScriptStateValue(lua_State *pLuaState, Mm9ScriptRuntime &runtime, const std::string &name)
{
    const std::string missingHandle = "\x1f";
    const std::string handle = runtime.getObjectHandleVar(name, missingHandle);
    if (handle != missingHandle)
    {
        if (handle.empty())
        {
            lua_pushnil(pLuaState);
        }
        else
        {
            pushObjectProxy(pLuaState, runtime, handle);
        }
        return;
    }

    const Mm9ScriptRuntimeState &state = runtime.state();
    const auto numberIterator = state.scriptNumVars.find(name);
    if (numberIterator != state.scriptNumVars.end())
    {
        lua_pushinteger(pLuaState, numberIterator->second);
        return;
    }

    const auto stringIterator = state.scriptStrVars.find(name);
    if (stringIterator != state.scriptStrVars.end())
    {
        lua_pushstring(pLuaState, stringIterator->second.c_str());
        return;
    }

    lua_pushnil(pLuaState);
}

Mm9ScriptValue scriptValueFromLua(lua_State *pLuaState, int index)
{
    if (lua_isnil(pLuaState, index))
    {
        return nullValue();
    }
    if (lua_isboolean(pLuaState, index))
    {
        return numberValue(lua_toboolean(pLuaState, index) != 0 ? 1.0 : 0.0);
    }
    if (lua_isnumber(pLuaState, index))
    {
        return numberValue(lua_tonumber(pLuaState, index));
    }

    if (lua_istable(pLuaState, index))
    {
        const std::string handle = luaObjectProxyHandle(pLuaState, index);
        if (!handle.empty())
        {
            return handleValue(handle);
        }
    }

    if (lua_isstring(pLuaState, index))
    {
        const std::string value = lua_tostring(pLuaState, index);
        if (value == "mm9:player" || mm9ObjectHandleParts(value))
        {
            return handleValue(value);
        }
        return stringValue(value);
    }

    return nullValue();
}

int luaStateIndex(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushnil(pLuaState);
        return 1;
    }

    pushScriptStateValue(pLuaState, *pRuntime, luaArgumentText(pLuaState, 2));
    return 1;
}

int luaStateNewIndex(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    setScriptVariableFromValue(*pRuntime, luaArgumentText(pLuaState, 2), scriptValueFromLua(pLuaState, 3));
    return 0;
}

int luaState(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushnil(pLuaState);
        return 1;
    }

    lua_newtable(pLuaState);
    lua_newtable(pLuaState);
    lua_pushlightuserdata(pLuaState, pRuntime);
    lua_pushcclosure(pLuaState, luaStateIndex, 1);
    lua_setfield(pLuaState, -2, "__index");
    lua_pushlightuserdata(pLuaState, pRuntime);
    lua_pushcclosure(pLuaState, luaStateNewIndex, 1);
    lua_setfield(pLuaState, -2, "__newindex");
    lua_setmetatable(pLuaState, -2);
    return 1;
}

int luaCondition(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        lua_pushboolean(pLuaState, false);
        return 1;
    }

    const std::string condition = luaArgumentText(pLuaState, 2);
    const size_t line = luaMetadataLine(pLuaState, 3);
    const std::string raw = luaMetadataRaw(pLuaState, 3);
    pRuntime->executeCommand("if", condition, line, raw);
    lua_pushboolean(pLuaState, scriptValueTruthy(evaluateScriptExpression(*pRuntime, condition)));
    return 1;
}

int luaExit(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const std::string exitValue = luaArgumentText(pLuaState, 2);
    const size_t line = luaMetadataLine(pLuaState, 3);
    const std::string raw = luaMetadataRaw(pLuaState, 3);
    pRuntime->executeCommand("exit", exitValue, line, raw);
    return 0;
}

int luaCommand(lua_State *pLuaState)
{
    Mm9ScriptRuntime *pRuntime = runtimeFromLua(pLuaState);
    if (pRuntime == nullptr)
    {
        return 0;
    }

    const std::string command = luaArgumentText(pLuaState, 2);
    const std::string argumentsText = luaArgumentText(pLuaState, 3);
    const size_t line = luaMetadataLine(pLuaState, 4);
    const std::string raw = luaMetadataRaw(pLuaState, 4);
    if (!pRuntime->executeCommand(command, argumentsText, line, raw))
    {
        pRuntime->recordUnimplementedCommand(command, argumentsText, line, raw);
    }
    return 0;
}

void pushRuntimeMethod(lua_State *pLuaState, Mm9ScriptRuntime &runtime, const char *pName, lua_CFunction function)
{
    lua_pushlightuserdata(pLuaState, &runtime);
    lua_pushcclosure(pLuaState, function, 1);
    lua_setfield(pLuaState, -2, pName);
}

void pushContext(lua_State *pLuaState, Mm9ScriptRuntime &runtime)
{
    lua_newtable(pLuaState);
    pushRuntimeMethod(pLuaState, runtime, "doRude", luaDoRude);
    pushRuntimeMethod(pLuaState, runtime, "onRudeExit", luaOnRudeExit);
    pushRuntimeMethod(pLuaState, runtime, "onEvent", luaOnEvent);
    pushRuntimeMethod(pLuaState, runtime, "addModelKey", luaAddModelKey);
    pushRuntimeMethod(pLuaState, runtime, "removeModelKey", luaRemoveModelKey);
    pushRuntimeMethod(pLuaState, runtime, "setCallback", luaSetCallback);
    pushRuntimeMethod(pLuaState, runtime, "killCallback", luaKillCallback);
    pushRuntimeMethod(pLuaState, runtime, "atTime", luaAtTime);
    pushRuntimeMethod(pLuaState, runtime, "doCallback", luaDoCallback);
    pushRuntimeMethod(pLuaState, runtime, "exitScript", luaExitScript);
    pushRuntimeMethod(pLuaState, runtime, "isTurnBased", luaIsTurnBased);
    pushRuntimeMethod(pLuaState, runtime, "getPcVoice", luaGetPcVoice);
    pushRuntimeMethod(pLuaState, runtime, "getPcLevel", luaGetPcLevel);
    pushRuntimeMethod(pLuaState, runtime, "getGameTime", luaGetGameTime);
    pushRuntimeMethod(pLuaState, runtime, "getPlayerId", luaGetPlayerId);
    pushRuntimeMethod(pLuaState, runtime, "getPlayerNumber", luaGetPlayerNumber);
    pushRuntimeMethod(pLuaState, runtime, "getPlayersWithinDist", luaGetPlayersWithinDist);
    pushRuntimeMethod(pLuaState, runtime, "setInt", luaSetInt);
    pushRuntimeMethod(pLuaState, runtime, "heal", luaHeal);
    pushRuntimeMethod(pLuaState, runtime, "addNpc", luaAddNpc);
    pushRuntimeMethod(pLuaState, runtime, "removeNpc", luaRemoveNpc);
    pushRuntimeMethod(pLuaState, runtime, "setParam", luaSetParam);
    pushRuntimeMethod(pLuaState, runtime, "savePath", luaSavePath);
    pushRuntimeMethod(pLuaState, runtime, "restorePath", luaRestorePath);
    pushRuntimeMethod(pLuaState, runtime, "castRay", luaCastRay);
    pushRuntimeMethod(pLuaState, runtime, "traceOff", luaTraceOff);
    pushRuntimeMethod(pLuaState, runtime, "traceOn", luaTraceOn);
    pushRuntimeMethod(pLuaState, runtime, "breakpoint", luaBreakpoint);
    pushRuntimeMethod(pLuaState, runtime, "dontIncludeThisFile", luaDontIncludeThisFile);
    pushRuntimeMethod(pLuaState, runtime, "cacheTexture", luaCacheTexture);
    pushRuntimeMethod(pLuaState, runtime, "hidePiece", luaHidePiece);
    pushRuntimeMethod(pLuaState, runtime, "doLetter", luaDoLetter);
    pushRuntimeMethod(pLuaState, runtime, "getContainerCount", luaGetContainerCount);
    pushRuntimeMethod(pLuaState, runtime, "hasKey", luaHasKey);
    pushRuntimeMethod(pLuaState, runtime, "giveKey", luaGiveKey);
    pushRuntimeMethod(pLuaState, runtime, "takeKey", luaTakeKey);
    pushRuntimeMethod(pLuaState, runtime, "giveItem", luaGiveItem);
    pushRuntimeMethod(pLuaState, runtime, "takeItem", luaTakeItem);
    pushRuntimeMethod(pLuaState, runtime, "hasItem", luaHasItem);
    pushRuntimeMethod(pLuaState, runtime, "giveGold", luaGiveGold);
    pushRuntimeMethod(pLuaState, runtime, "hasGold", luaHasGold);
    pushRuntimeMethod(pLuaState, runtime, "takeGold", luaTakeGold);
    pushRuntimeMethod(pLuaState, runtime, "giveExp", luaGiveExp);
    pushRuntimeMethod(pLuaState, runtime, "givePromo", luaGivePromo);
    pushRuntimeMethod(pLuaState, runtime, "getAttribute", luaGetAttribute);
    pushRuntimeMethod(pLuaState, runtime, "giveAttribute", luaGiveAttribute);
    pushRuntimeMethod(pLuaState, runtime, "cacheScript", luaCacheScript);
    pushRuntimeMethod(pLuaState, runtime, "runScript", luaRunScript);
    pushRuntimeMethod(pLuaState, runtime, "setConsoleNumVar", luaSetConsoleNumVar);
    pushRuntimeMethod(pLuaState, runtime, "getConsoleNumVar", luaGetConsoleNumVar);
    pushRuntimeMethod(pLuaState, runtime, "setConsoleStrVar", luaSetConsoleStrVar);
    pushRuntimeMethod(pLuaState, runtime, "getConsoleStrVar", luaGetConsoleStrVar);
    pushRuntimeMethod(pLuaState, runtime, "getParam", luaGetParam);
    pushRuntimeMethod(pLuaState, runtime, "param", luaParam);
    pushRuntimeMethod(pLuaState, runtime, "paramObject", luaParamObject);
    pushRuntimeMethod(pLuaState, runtime, "self", luaSelfObject);
    pushRuntimeMethod(pLuaState, runtime, "player", luaPlayerObject);
    pushRuntimeMethod(pLuaState, runtime, "object", luaObjectByName);
    pushRuntimeMethod(pLuaState, runtime, "objectOrNil", luaObjectByNameOrNil);
    pushRuntimeMethod(pLuaState, runtime, "spawn", luaSpawn);
    pushRuntimeMethod(pLuaState, runtime, "spawn2", luaSpawn2);
    pushRuntimeMethod(pLuaState, runtime, "state", luaState);
    pushRuntimeMethod(pLuaState, runtime, "setPropNumber", luaSetPropNumber);
    pushRuntimeMethod(pLuaState, runtime, "getObjectHandleByRudeId", luaGetObjectHandleByRudeId);
    pushRuntimeMethod(pLuaState, runtime, "addTrigger", luaAddTrigger);
    pushRuntimeMethod(pLuaState, runtime, "removeTrigger", luaRemoveTrigger);
    pushRuntimeMethod(pLuaState, runtime, "trigger", luaTrigger);
    pushRuntimeMethod(pLuaState, runtime, "debugOut", luaDebugOut);
    pushRuntimeMethod(pLuaState, runtime, "cprint", luaCPrint);
    pushRuntimeMethod(pLuaState, runtime, "getObjects", luaGetObjects);
    pushRuntimeMethod(pLuaState, runtime, "arrayPut", luaArrayPut);
    pushRuntimeMethod(pLuaState, runtime, "arrayGet", luaArrayGet);
    pushRuntimeMethod(pLuaState, runtime, "randomInt", luaRandomInt);
    pushRuntimeMethod(pLuaState, runtime, "randomFloat", luaRandomFloat);
    pushRuntimeMethod(pLuaState, runtime, "getTime", luaGetTime);
    pushRuntimeMethod(pLuaState, runtime, "set", luaSetStateValue);
    pushRuntimeMethod(pLuaState, runtime, "add", luaAddStateValue);
    pushRuntimeMethod(pLuaState, runtime, "sub", luaSubStateValue);
    pushRuntimeMethod(pLuaState, runtime, "subtract", luaSubStateValue);
    pushRuntimeMethod(pLuaState, runtime, "mul", luaMulStateValue);
    pushRuntimeMethod(pLuaState, runtime, "multiply", luaMulStateValue);
    pushRuntimeMethod(pLuaState, runtime, "div", luaDivStateValue);
    pushRuntimeMethod(pLuaState, runtime, "divide", luaDivStateValue);
    pushRuntimeMethod(pLuaState, runtime, "mod", luaModStateValue);
    pushRuntimeMethod(pLuaState, runtime, "vecScale", luaVecScale);
    pushRuntimeMethod(pLuaState, runtime, "vecNorm", luaVecNorm);
    pushRuntimeMethod(pLuaState, runtime, "vecAdd", luaVecAdd);
    pushRuntimeMethod(pLuaState, runtime, "vecSub", luaVecSub);
    pushRuntimeMethod(pLuaState, runtime, "vecCross", luaVecCross);
    pushRuntimeMethod(pLuaState, runtime, "vecDist", luaVecDist);
    pushRuntimeMethod(pLuaState, runtime, "vecMag", luaVecMag);
    pushRuntimeMethod(pLuaState, runtime, "vecAngle", luaVecAngle);
    pushRuntimeMethod(pLuaState, runtime, "rotateDir", luaRotateDir);
    pushRuntimeMethod(pLuaState, runtime, "sin", luaSin);
    pushRuntimeMethod(pLuaState, runtime, "cos", luaCos);
    pushRuntimeMethod(pLuaState, runtime, "getAngleToPos", luaGetAngleToPos);
    pushRuntimeMethod(pLuaState, runtime, "getRotation", luaGetRotation);
    pushRuntimeMethod(pLuaState, runtime, "setRotation", luaSetRotation);
    pushRuntimeMethod(pLuaState, runtime, "calcRotationRate", luaCalcRotationRate);
    pushRuntimeMethod(pLuaState, runtime, "checkWorldCollision", luaCheckWorldCollision);
    pushRuntimeMethod(pLuaState, runtime, "wait", luaWait);
    pushRuntimeMethod(pLuaState, runtime, "cacheSound", luaCacheSound);
    pushRuntimeMethod(pLuaState, runtime, "playSound", luaPlaySound);
    pushRuntimeMethod(pLuaState, runtime, "speak", luaSpeak);
    pushRuntimeMethod(pLuaState, runtime, "playSoundHandle", luaPlaySoundHandle);
    pushRuntimeMethod(pLuaState, runtime, "killSound", luaKillSound);
    pushRuntimeMethod(pLuaState, runtime, "getSoundDuration", luaGetSoundDuration);
    pushRuntimeMethod(pLuaState, runtime, "isSoundDone", luaIsSoundDone);
    pushRuntimeMethod(pLuaState, runtime, "cacheClientFx", luaCacheClientFx);
    pushRuntimeMethod(pLuaState, runtime, "screenFadeOut", luaScreenFadeOut);
    pushRuntimeMethod(pLuaState, runtime, "screenFadeIn", luaScreenFadeIn);
    pushRuntimeMethod(pLuaState, runtime, "letterBox", luaLetterBox);
    pushRuntimeMethod(pLuaState, runtime, "rolloverText", luaRolloverText);
    pushRuntimeMethod(pLuaState, runtime, "consoleCommand", luaConsoleCommand);
    pushRuntimeMethod(pLuaState, runtime, "doHighScore", luaDoHighScore);
    pushRuntimeMethod(pLuaState, runtime, "clearCondition", luaClearCondition);
    pushRuntimeMethod(pLuaState, runtime, "setCondition", luaSetCondition);
    pushRuntimeMethod(pLuaState, runtime, "condition", luaCondition);
    pushRuntimeMethod(pLuaState, runtime, "exit", luaExit);
    pushRuntimeMethod(pLuaState, runtime, "command", luaCommand);
}
}

Mm9ScriptRuntimeState createInitialMm9ScriptRuntimeState(const Mm9DialoguePackage &package)
{
    Mm9ScriptRuntimeState state = {};
    state.consoleNumVars = package.stateDefaults.consoleNumVars;
    state.consoleStrVars = package.stateDefaults.consoleStrVars;
    state.mapNumVars = package.stateDefaults.mapNumVars;
    state.mapStrVars = package.stateDefaults.mapStrVars;
    state.scriptNumVars = package.stateDefaults.scriptNumVars;
    state.scriptStrVars = package.stateDefaults.scriptStrVars;
    state.objectHandleVars = package.stateDefaults.objectHandleVars;
    state.objectNumberProperties = package.stateDefaults.objectNumberProperties;
    return state;
}

Mm9ScriptRuntime::Mm9ScriptRuntime(const Mm9DialoguePackage &package, Mm9DialogueRuntime &dialogueRuntime)
    : m_package(package)
    , m_dialogueRuntime(dialogueRuntime)
{
    m_dialogueRuntime.bindScriptRuntimeState(&m_state);
}

bool Mm9ScriptRuntime::runLabel(
    const std::string &scriptSource,
    const std::string &label,
    std::optional<std::string> &errorMessage)
{
    const auto scriptIterator = findScriptFile(m_package, scriptSource);
    if (scriptIterator == m_package.scripts.end())
    {
        errorMessage = "missing generated MM9 script: " + scriptSource;
        return false;
    }

    Engine::LuaStateOwner lua = {};
    if (!lua.isValid())
    {
        errorMessage = "lua state unavailable";
        return false;
    }
    lua.openApprovedLibraries();

    lua_State *pLuaState = lua.state();
    if (!pushMm9ScriptRuntimeSupport(pLuaState, m_package, errorMessage))
    {
        lua_settop(pLuaState, 0);
        return false;
    }

    const Mm9GeneratedScriptFile &script = scriptIterator->second;
    if (luaL_loadbuffer(pLuaState, script.luaText.c_str(), script.luaText.size(), script.luaPath.c_str()) != LUA_OK)
    {
        errorMessage = lua_tostring(pLuaState, -1);
        lua_pop(pLuaState, 1);
        return false;
    }
    if (!lua.call(0, 1, errorMessage))
    {
        lua_settop(pLuaState, 0);
        return false;
    }

    if (!lua_istable(pLuaState, -1))
    {
        errorMessage = "generated MM9 script did not return a script table: " + scriptSource;
        lua_settop(pLuaState, 0);
        return false;
    }

    const int scriptTableIndex = lua_gettop(pLuaState);
    lua_getfield(pLuaState, scriptTableIndex, "labels");
    if (!lua_istable(pLuaState, -1))
    {
        errorMessage = "generated MM9 script has no labels table: " + scriptSource;
        lua_settop(pLuaState, 0);
        return false;
    }

    const int labelsTableIndex = lua_gettop(pLuaState);
    lua_getfield(pLuaState, labelsTableIndex, label.c_str());
    if (!lua_isfunction(pLuaState, -1))
    {
        errorMessage = "generated MM9 script has no label " + label + ": " + scriptSource;
        lua_settop(pLuaState, 0);
        return false;
    }

    const std::string previousActiveScriptSource = m_activeScriptSource;
    m_activeScriptSource = scriptIterator->second.source;
    pushContext(pLuaState, *this);
    const bool called = lua.call(1, 0, errorMessage);
    m_activeScriptSource = previousActiveScriptSource;
    lua_settop(pLuaState, 0);
    return called;
}

Mm9ObjectActivationResult Mm9ScriptRuntime::activateObject(const std::string &mapId, int32_t objectIndex)
{
    Mm9ObjectActivationResult result = {};

    const Mm9GeneratedObjectDialogueBinding *pBinding = objectBindingForObject(mapId, objectIndex);
    if (pBinding == nullptr)
    {
        result.error = "MM9 dialogue binding was not found for selected object";
        return result;
    }

    Mm9DialogueOwnerContext owner = {};
    if (!m_dialogueRuntime.ownerContextForObject(mapId, objectIndex, owner, &result.error))
    {
        return result;
    }

    result.activated = true;
    const bool hasRunnableScript = !pBinding->scriptName.empty() && pBinding->scriptSourceExists;
    if (!hasRunnableScript && !pBinding->rudeId)
    {
        result.error = "MM9 dialogue binding has no resolved RUDE id";
        return result;
    }

    m_dialogueRuntime.setOwnerContext(owner);

    if (!owner.greetingSound.empty())
    {
        queueGreetingSoundRequest(owner);
        result.queuedGreetingSound = true;
        result.audioRequest = m_audioRequests.back();
    }

    if (hasRunnableScript)
    {
        std::optional<std::string> scriptError;
        result.ranScript = true;
        if (!runLabel(pBinding->scriptName, "OnUse", scriptError))
        {
            result.error = scriptError.value_or("failed to run generated MM9 object script");
            return result;
        }

        result.openedDialogue = !m_dialogueRuntime.closed() && m_dialogueRuntime.currentRudeId() > 0;
        if (result.openedDialogue)
        {
            return result;
        }
    }

    if (!pBinding->rudeId)
    {
        result.error = "MM9 dialogue binding has no resolved RUDE id";
        return result;
    }

    result.directDialogue = true;
    if (!m_dialogueRuntime.enterRudeId(*pBinding->rudeId, owner))
    {
        result.error = "MM9 dialogue binding points to a missing generated RUDE dialogue";
        return result;
    }

    result.openedDialogue = true;
    return result;
}

Mm9ObjectActivationResult Mm9ScriptRuntime::activateObject(const GameplayWorldHit &hit)
{
    const std::optional<Mm9InteractionObjectBinding> binding = mm9InteractionObjectBindingFromWorldHit(hit);
    if (!binding)
    {
        Mm9ObjectActivationResult result = {};
        result.error = "selected world hit is not an MM9 dialogue-capable object";
        return result;
    }

    return activateObject(binding->mapId, binding->sourceObjectIndex);
}

const std::vector<Mm9ScriptRuntimeCommand> &Mm9ScriptRuntime::unimplementedCommands() const
{
    return m_unimplementedCommands;
}

const std::vector<Mm9ScriptRuntimeCallback> &Mm9ScriptRuntime::registeredCallbacks() const
{
    return m_registeredCallbacks;
}

const std::vector<Mm9ScriptRuntimeKeyAccess> &Mm9ScriptRuntime::keyAccesses() const
{
    return m_keyAccesses;
}

const std::vector<Mm9ScriptRuntimePartyAccess> &Mm9ScriptRuntime::partyAccesses() const
{
    return m_partyAccesses;
}

const std::vector<Mm9ScriptRuntimeAudioRequest> &Mm9ScriptRuntime::audioRequests() const
{
    return m_audioRequests;
}

const std::vector<Mm9ScriptRuntimeAnimationRequest> &Mm9ScriptRuntime::animationRequests() const
{
    return m_animationRequests;
}

const std::vector<Mm9ScriptRuntimeClientFxRequest> &Mm9ScriptRuntime::clientFxRequests() const
{
    return m_clientFxRequests;
}

const std::vector<Mm9ScriptRuntimePresentationRequest> &Mm9ScriptRuntime::presentationRequests() const
{
    return m_presentationRequests;
}

const std::vector<Mm9ScriptRuntimeMovementRequest> &Mm9ScriptRuntime::movementRequests() const
{
    return m_movementRequests;
}

const std::vector<Mm9ScriptRuntimeSpawnRequest> &Mm9ScriptRuntime::spawnRequests() const
{
    return m_spawnRequests;
}

const std::vector<Mm9ScriptRuntimeAiRequest> &Mm9ScriptRuntime::aiRequests() const
{
    return m_aiRequests;
}

const std::vector<Mm9ScriptRuntimeAttachmentRequest> &Mm9ScriptRuntime::attachmentRequests() const
{
    return m_attachmentRequests;
}

const std::vector<Mm9ScriptRuntimePromotionRequest> &Mm9ScriptRuntime::promotionRequests() const
{
    return m_promotionRequests;
}

const std::vector<Mm9ScriptRuntimePartyCommandRequest> &Mm9ScriptRuntime::partyCommandRequests() const
{
    return m_partyCommandRequests;
}

const std::vector<Mm9ScriptRuntimeControlRequest> &Mm9ScriptRuntime::controlRequests() const
{
    return m_controlRequests;
}

const std::vector<Mm9ScriptRuntimeScheduledInvocation> &Mm9ScriptRuntime::scheduledInvocations() const
{
    return m_state.scheduledInvocations;
}

const std::vector<Mm9ScriptRuntimeDamageRequest> &Mm9ScriptRuntime::damageRequests() const
{
    return m_damageRequests;
}

double Mm9ScriptRuntime::scriptTimeSeconds() const
{
    return m_state.scriptTimeSeconds;
}

bool Mm9ScriptRuntime::advanceScriptTime(double elapsedSeconds, std::optional<std::string> &errorMessage)
{
    if (elapsedSeconds < 0.0)
    {
        elapsedSeconds = 0.0;
    }
    m_state.scriptTimeSeconds += elapsedSeconds;
    expireAttributeEffects();

    size_t processedCount = 0;
    for (size_t index = 0; index < m_state.scheduledInvocations.size();)
    {
        if (m_state.scheduledInvocations[index].dueTimeSeconds > m_state.scriptTimeSeconds)
        {
            ++index;
            continue;
        }
        if (processedCount++ >= 1024 || m_schedulerDispatchDepth >= 16)
        {
            errorMessage = "MM9 script scheduler recursion limit reached";
            return false;
        }

        const Mm9ScriptRuntimeScheduledInvocation invocation = m_state.scheduledInvocations[index];
        m_state.scheduledInvocations.erase(m_state.scheduledInvocations.begin() + static_cast<std::ptrdiff_t>(index));

        Mm9DialogueOwnerContext owner = {};
        std::string ownerError;
        if (!m_dialogueRuntime.ownerContextForObject(invocation.mapId, invocation.objectIndex, owner, &ownerError))
        {
            owner.mapId = invocation.mapId;
            owner.objectIndex = invocation.objectIndex;
            owner.scriptName = invocation.scriptSource;
        }

        const Mm9DialogueOwnerContext previousOwner = m_dialogueRuntime.owner();
        m_dialogueRuntime.setOwnerContext(std::move(owner));
        ++m_schedulerDispatchDepth;
        const bool ran = runLabel(invocation.scriptSource, invocation.label, errorMessage);
        --m_schedulerDispatchDepth;
        m_dialogueRuntime.setOwnerContext(previousOwner);
        if (!ran)
        {
            return false;
        }
    }

    return true;
}

void Mm9ScriptRuntime::expireAttributeEffects()
{
    for (size_t index = 0; index < m_state.attributeEffects.size();)
    {
        const Mm9ScriptRuntimeAttributeEffect &effect = m_state.attributeEffects[index];
        if (effect.expiresAtSeconds > m_state.scriptTimeSeconds)
        {
            ++index;
            continue;
        }

        Character *pMember = m_dialogueRuntime.party().member(effect.memberIndex);
        if (pMember != nullptr)
        {
            applyMm9CharacterAttributeBonus(*pMember, effect.attributeId, -effect.amount, false);
        }

        m_state.attributeEffects.erase(m_state.attributeEffects.begin() + static_cast<std::ptrdiff_t>(index));
    }
}

bool Mm9ScriptRuntime::dispatchRegisteredCallbacks(
    const std::string &kind,
    const std::string &selector,
    const std::string &mapId,
    int32_t objectIndex,
    std::optional<std::string> &errorMessage,
    size_t &dispatchedCount)
{
    const std::optional<std::vector<std::string>> scriptParams = std::nullopt;
    return dispatchRegisteredCallbacks(
        kind,
        selector,
        mapId,
        objectIndex,
        scriptParams,
        errorMessage,
        dispatchedCount);
}

bool Mm9ScriptRuntime::dispatchRegisteredCallbacks(
    const std::string &kind,
    const std::string &selector,
    const std::string &mapId,
    int32_t objectIndex,
    const std::vector<std::string> &scriptParams,
    std::optional<std::string> &errorMessage,
    size_t &dispatchedCount)
{
    return dispatchRegisteredCallbacks(
        kind,
        selector,
        mapId,
        objectIndex,
        std::optional<std::vector<std::string>>(scriptParams),
        errorMessage,
        dispatchedCount);
}

bool Mm9ScriptRuntime::dispatchRegisteredCallbacks(
    const std::string &kind,
    const std::string &selector,
    const std::string &mapId,
    int32_t objectIndex,
    const std::optional<std::vector<std::string>> &scriptParams,
    std::optional<std::string> &errorMessage,
    size_t &dispatchedCount)
{
    dispatchedCount = 0;

    const std::string loweredKind = lowerCopy(trimCopy(kind));
    const std::string loweredSelector = lowerCopy(trimCopy(selector));
    if (loweredKind.empty())
    {
        return true;
    }

    std::vector<Mm9ScriptRuntimeCallback> matchingCallbacks;
    for (const Mm9ScriptRuntimeCallback &callback : m_state.registeredCallbacks)
    {
        if (callback.mapId != mapId || callback.objectIndex != objectIndex
            || lowerCopy(callback.kind) != loweredKind)
        {
            continue;
        }

        const std::string callbackSelector = lowerCopy(trimCopy(callback.selector));
        if (!loweredSelector.empty() && !callbackSelector.empty() && callbackSelector != loweredSelector)
        {
            continue;
        }

        matchingCallbacks.push_back(callback);
    }

    const Mm9DialogueOwnerContext previousOwner = m_dialogueRuntime.owner();
    for (const Mm9ScriptRuntimeCallback &callback : matchingCallbacks)
    {
        Mm9DialogueOwnerContext owner = {};
        std::string ownerError;
        if (!m_dialogueRuntime.ownerContextForObject(mapId, objectIndex, owner, &ownerError))
        {
            owner.mapId = mapId;
            owner.objectIndex = objectIndex;
            owner.scriptName = callback.scriptSource;
        }
        if (scriptParams)
        {
            owner.scriptParams = *scriptParams;
        }

        m_dialogueRuntime.setOwnerContext(std::move(owner));
        if (!runLabel(callback.scriptSource, callback.label, errorMessage))
        {
            m_dialogueRuntime.setOwnerContext(previousOwner);
            return false;
        }

        ++dispatchedCount;
    }

    m_dialogueRuntime.setOwnerContext(previousOwner);
    return true;
}

bool Mm9ScriptRuntime::dispatchMovementResult(
    size_t movementRequestIndex,
    const std::string &resultKind,
    std::optional<std::string> &errorMessage,
    size_t &dispatchedCount)
{
    dispatchedCount = 0;
    if (movementRequestIndex >= m_state.movementRequests.size())
    {
        errorMessage = "MM9 movement request index is out of range";
        return false;
    }

    const Mm9ScriptRuntimeMovementRequest &request = m_state.movementRequests[movementRequestIndex];
    const std::optional<std::pair<std::string, int32_t>> ownerParts = mm9ObjectHandleParts(request.objectHandle);
    if (!ownerParts)
    {
        errorMessage = "MM9 movement request has no package-backed owner handle";
        return false;
    }

    const std::string loweredResult = lowerCopy(trimCopy(resultKind));
    if (loweredResult.empty() || loweredResult == "arrived" || loweredResult == "arrival"
        || loweredResult == "complete" || loweredResult == "completed" || loweredResult == "success")
    {
        if (!isCallbackLabel(request.callbackLabel))
        {
            return true;
        }

        if (!runLabelForObject(
                request.scriptSource,
                request.callbackLabel,
                ownerParts->first,
                ownerParts->second,
                errorMessage))
        {
            return false;
        }

        dispatchedCount = 1;
        return true;
    }

    if (loweredResult == "stuck" || loweredResult == "blocked")
    {
        size_t firstCount = 0;
        size_t secondCount = 0;
        if (!dispatchRegisteredCallbacks("onstuck", "", ownerParts->first, ownerParts->second, errorMessage, firstCount)
            || !dispatchRegisteredCallbacks(
                "onstuckdone",
                "",
                ownerParts->first,
                ownerParts->second,
                errorMessage,
                secondCount))
        {
            return false;
        }

        dispatchedCount = firstCount + secondCount;
        return true;
    }

    if (loweredResult == "obstacle")
    {
        return dispatchRegisteredCallbacks(
            "onobstacle",
            "",
            ownerParts->first,
            ownerParts->second,
            errorMessage,
            dispatchedCount);
    }

    if (loweredResult == "obstacleavoided" || loweredResult == "avoided")
    {
        return dispatchRegisteredCallbacks(
            "onobstacleavoided",
            "",
            ownerParts->first,
            ownerParts->second,
            errorMessage,
            dispatchedCount);
    }

    if (loweredResult == "touch" || loweredResult == "touchnotify")
    {
        return dispatchRegisteredCallbacks(
            "ontouchnotify",
            "",
            ownerParts->first,
            ownerParts->second,
            errorMessage,
            dispatchedCount);
    }

    errorMessage = "unknown MM9 movement result kind: " + resultKind;
    return false;
}

bool Mm9ScriptRuntime::dispatchAnimationResult(
    size_t animationRequestIndex,
    const std::string &resultKind,
    const std::string &selector,
    std::optional<std::string> &errorMessage,
    size_t &dispatchedCount)
{
    dispatchedCount = 0;
    if (animationRequestIndex >= m_state.animationRequests.size())
    {
        errorMessage = "MM9 animation request index is out of range";
        return false;
    }

    const Mm9ScriptRuntimeAnimationRequest &request = m_state.animationRequests[animationRequestIndex];
    const std::optional<std::pair<std::string, int32_t>> ownerParts = mm9ObjectHandleParts(request.objectHandle);
    if (!ownerParts)
    {
        errorMessage = "MM9 animation request has no package-backed owner handle";
        return false;
    }

    const std::string loweredResult = lowerCopy(trimCopy(resultKind));
    if (loweredResult.empty() || loweredResult == "complete" || loweredResult == "completed"
        || loweredResult == "done" || loweredResult == "success")
    {
        if (!isCallbackLabel(request.callbackLabel))
        {
            return true;
        }

        if (!runLabelForObject(
                request.scriptSource,
                request.callbackLabel,
                ownerParts->first,
                ownerParts->second,
                errorMessage))
        {
            return false;
        }

        dispatchedCount = 1;
        return true;
    }

    if (loweredResult == "modelkey" || loweredResult == "modelstringkey")
    {
        const std::string keySelector = selector.empty() ? request.animationName : selector;
        return dispatchRegisteredCallbacks(
            "addmodelkey",
            keySelector,
            ownerParts->first,
            ownerParts->second,
            errorMessage,
            dispatchedCount);
    }

    errorMessage = "unknown MM9 animation result kind: " + resultKind;
    return false;
}

bool Mm9ScriptRuntime::dispatchAudioResult(
    size_t audioRequestIndex,
    const std::string &resultKind,
    std::optional<std::string> &errorMessage,
    size_t &dispatchedCount)
{
    dispatchedCount = 0;
    if (audioRequestIndex >= m_state.audioRequests.size())
    {
        errorMessage = "MM9 audio request index is out of range";
        return false;
    }

    const Mm9ScriptRuntimeAudioRequest &request = m_state.audioRequests[audioRequestIndex];
    const std::string loweredResult = lowerCopy(trimCopy(resultKind));
    if (!loweredResult.empty() && loweredResult != "complete" && loweredResult != "completed"
        && loweredResult != "done" && loweredResult != "success" && loweredResult != "stopped")
    {
        errorMessage = "unknown MM9 audio result kind: " + resultKind;
        return false;
    }

    if (!request.soundHandle.empty())
    {
        m_state.activeSoundHandles.erase(request.soundHandle);
    }

    if (loweredResult == "stopped" || !isCallbackLabel(request.callbackLabel))
    {
        return true;
    }

    if (!runLabelForObject(
            request.scriptSource,
            request.callbackLabel,
            request.mapId,
            request.objectIndex,
            errorMessage))
    {
        return false;
    }

    dispatchedCount = 1;
    return true;
}

std::optional<int32_t> Mm9ScriptRuntime::resolveRawKeyId(const std::string &token) const
{
    const std::optional<int32_t> parsed = parseInt(token);
    if (parsed)
    {
        return parsed;
    }

    for (const auto &keyPair : m_package.keys)
    {
        const Mm9GeneratedKey &key = keyPair.second;
        for (const std::string &alias : key.aliases)
        {
            if (alias == token)
            {
                return key.rawId;
            }
        }
    }

    return std::nullopt;
}

int32_t Mm9ScriptRuntime::resolveScriptNumber(const std::string &token, int32_t defaultValue) const
{
    const std::string lowered = lowerCopy(trimCopy(token));
    if (lowered == "true")
    {
        return 1;
    }
    if (lowered == "false")
    {
        return 0;
    }

    const std::optional<int32_t> parsed = parseInt(token);
    if (parsed)
    {
        return *parsed;
    }

    const auto consoleIterator = m_state.consoleNumVars.find(token);
    if (consoleIterator != m_state.consoleNumVars.end())
    {
        return consoleIterator->second;
    }

    const auto scriptIterator = m_state.scriptNumVars.find(token);
    return scriptIterator != m_state.scriptNumVars.end() ? scriptIterator->second : defaultValue;
}

void Mm9ScriptRuntime::setConsoleNumVar(const std::string &name, int32_t value)
{
    if (!name.empty())
    {
        m_state.consoleNumVars[name] = value;
    }
}

int32_t Mm9ScriptRuntime::getConsoleNumVar(const std::string &name, int32_t defaultValue) const
{
    const auto iterator = m_state.consoleNumVars.find(name);
    return iterator != m_state.consoleNumVars.end() ? iterator->second : defaultValue;
}

void Mm9ScriptRuntime::setConsoleStrVar(const std::string &name, const std::string &value)
{
    if (!name.empty())
    {
        m_state.consoleStrVars[name] = value;
    }
}

std::string Mm9ScriptRuntime::getConsoleStrVar(const std::string &name, const std::string &defaultValue) const
{
    const auto iterator = m_state.consoleStrVars.find(name);
    return iterator != m_state.consoleStrVars.end() ? iterator->second : defaultValue;
}

void Mm9ScriptRuntime::setMapNumVar(const std::string &mapId, const std::string &name, int32_t value)
{
    if (!mapId.empty() && !name.empty())
    {
        m_state.mapNumVars[mapId][name] = value;
    }
}

int32_t Mm9ScriptRuntime::getMapNumVar(
    const std::string &mapId,
    const std::string &name,
    int32_t defaultValue) const
{
    const auto mapIterator = m_state.mapNumVars.find(mapId);
    if (mapIterator == m_state.mapNumVars.end())
    {
        return defaultValue;
    }

    const auto valueIterator = mapIterator->second.find(name);
    return valueIterator != mapIterator->second.end() ? valueIterator->second : defaultValue;
}

void Mm9ScriptRuntime::setMapStrVar(
    const std::string &mapId,
    const std::string &name,
    const std::string &value)
{
    if (!mapId.empty() && !name.empty())
    {
        m_state.mapStrVars[mapId][name] = value;
    }
}

std::string Mm9ScriptRuntime::getMapStrVar(
    const std::string &mapId,
    const std::string &name,
    const std::string &defaultValue) const
{
    const auto mapIterator = m_state.mapStrVars.find(mapId);
    if (mapIterator == m_state.mapStrVars.end())
    {
        return defaultValue;
    }

    const auto valueIterator = mapIterator->second.find(name);
    return valueIterator != mapIterator->second.end() ? valueIterator->second : defaultValue;
}

void Mm9ScriptRuntime::setScriptNumVar(const std::string &name, int32_t value)
{
    if (!name.empty())
    {
        m_state.scriptNumVars[name] = value;
    }
}

int32_t Mm9ScriptRuntime::getScriptNumVar(const std::string &name, int32_t defaultValue) const
{
    const auto iterator = m_state.scriptNumVars.find(name);
    return iterator != m_state.scriptNumVars.end() ? iterator->second : defaultValue;
}

void Mm9ScriptRuntime::setScriptStrVar(const std::string &name, const std::string &value)
{
    if (!name.empty())
    {
        m_state.scriptStrVars[name] = value;
    }
}

std::string Mm9ScriptRuntime::getScriptStrVar(const std::string &name, const std::string &defaultValue) const
{
    const auto iterator = m_state.scriptStrVars.find(name);
    return iterator != m_state.scriptStrVars.end() ? iterator->second : defaultValue;
}

void Mm9ScriptRuntime::setObjectHandleVar(const std::string &name, const std::string &handle)
{
    if (!name.empty())
    {
        m_state.objectHandleVars[name] = handle;
        setScriptStrVar(name, handle);
    }
}

void Mm9ScriptRuntime::clearObjectHandleVar(const std::string &name)
{
    const std::string loweredName = lowerCopy(trimCopy(name));
    if (loweredName.empty())
    {
        return;
    }

    const auto matchesName = [&](const std::string &entryName)
    {
        return lowerCopy(trimCopy(entryName)) == loweredName;
    };

    for (std::map<std::string, std::string>::iterator iterator = m_state.objectHandleVars.begin();
         iterator != m_state.objectHandleVars.end();)
    {
        if (matchesName(iterator->first))
        {
            iterator = m_state.objectHandleVars.erase(iterator);
        }
        else
        {
            ++iterator;
        }
    }

    for (std::map<std::string, std::string>::iterator iterator = m_state.scriptStrVars.begin();
         iterator != m_state.scriptStrVars.end();)
    {
        if (matchesName(iterator->first))
        {
            iterator = m_state.scriptStrVars.erase(iterator);
        }
        else
        {
            ++iterator;
        }
    }

    for (std::map<std::string, int32_t>::iterator iterator = m_state.scriptNumVars.begin();
         iterator != m_state.scriptNumVars.end();)
    {
        if (matchesName(iterator->first))
        {
            iterator = m_state.scriptNumVars.erase(iterator);
        }
        else
        {
            ++iterator;
        }
    }
}

std::string Mm9ScriptRuntime::getObjectHandleVar(const std::string &name, const std::string &defaultValue) const
{
    const auto iterator = m_state.objectHandleVars.find(name);
    if (iterator != m_state.objectHandleVars.end())
    {
        return iterator->second;
    }

    const std::string loweredName = lowerCopy(trimCopy(name));
    const auto caseInsensitiveIterator = std::find_if(
        m_state.objectHandleVars.begin(),
        m_state.objectHandleVars.end(),
        [&](const std::pair<const std::string, std::string> &entry)
        {
            return lowerCopy(trimCopy(entry.first)) == loweredName;
        });
    return caseInsensitiveIterator != m_state.objectHandleVars.end()
        ? caseInsensitiveIterator->second
        : defaultValue;
}

std::string Mm9ScriptRuntime::getSoundHandleVar(const std::string &name, const std::string &defaultValue) const
{
    const auto iterator = m_state.soundHandleVars.find(name);
    return iterator != m_state.soundHandleVars.end() ? iterator->second : defaultValue;
}

std::string Mm9ScriptRuntime::objectHandleForName(const std::string &name) const
{
    const std::string trimmed = trimCopy(name);
    if (trimmed.empty())
    {
        return {};
    }

    if (trimmed == "mm9:player" || mm9ObjectHandleParts(trimmed))
    {
        return trimmed;
    }

    const std::string lowered = lowerCopy(trimmed);
    if (lowered == "hme" || lowered == "g_hmyobject")
    {
        return activeObjectHandle();
    }
    if (lowered == "hplayer" || lowered == "player")
    {
        return "mm9:player";
    }

    const std::string &mapId = m_dialogueRuntime.owner().mapId;
    for (const Mm9GeneratedObjectDialogueBinding &binding : m_package.objectBindings)
    {
        if (!mapId.empty() && binding.mapId != mapId)
        {
            continue;
        }

        if (lowerCopy(binding.objectName) == lowered || lowerCopy(binding.objectClass) == lowered)
        {
            return "mm9:" + binding.mapId + ":object:" + std::to_string(binding.objectIndex);
        }
    }

    return {};
}

std::string Mm9ScriptRuntime::objectNameForHandle(const std::string &handle) const
{
    if (handle == "mm9:player")
    {
        return "Player";
    }

    const Mm9GeneratedObjectDialogueBinding *pBinding = objectBindingForHandle(handle);
    return pBinding != nullptr ? pBinding->objectName : "";
}

std::string Mm9ScriptRuntime::objectClassNameForHandle(const std::string &handle) const
{
    if (handle == "mm9:player")
    {
        return "Player";
    }

    const Mm9GeneratedObjectDialogueBinding *pBinding = objectBindingForHandle(handle);
    return pBinding != nullptr ? pBinding->objectClass : "";
}

void Mm9ScriptRuntime::setObjectTargetHandle(const std::string &objectHandle, const std::string &targetHandle)
{
    if (objectHandle.empty())
    {
        return;
    }

    if (targetHandle.empty())
    {
        m_state.objectTargetHandles.erase(objectHandle);
        return;
    }

    m_state.objectTargetHandles[objectHandle] = targetHandle;
}

std::string Mm9ScriptRuntime::objectTargetHandle(const std::string &objectHandle) const
{
    const auto iterator = m_state.objectTargetHandles.find(objectHandle);
    return iterator != m_state.objectTargetHandles.end() ? iterator->second : "";
}

void Mm9ScriptRuntime::createObjectLink(const std::string &objectHandle, const std::string &linkedHandle)
{
    if (objectHandle.empty() || linkedHandle.empty())
    {
        return;
    }

    m_state.objectLinks[objectHandle].push_back(linkedHandle);
}

void Mm9ScriptRuntime::breakObjectLink(const std::string &objectHandle, const std::string &linkedHandle)
{
    if (objectHandle.empty() || linkedHandle.empty())
    {
        return;
    }

    std::vector<std::string> &links = m_state.objectLinks[objectHandle];
    links.erase(std::remove(links.begin(), links.end(), linkedHandle), links.end());
}

std::vector<std::string> Mm9ScriptRuntime::objectLinkedHandles(const std::string &objectHandle) const
{
    const auto iterator = m_state.objectLinks.find(objectHandle);
    return iterator != m_state.objectLinks.end() ? iterator->second : std::vector<std::string>();
}

void Mm9ScriptRuntime::setObjectNumberProperty(const std::string &propertyName, int32_t value, size_t line)
{
    const std::string key = activeObjectPropertyKey(propertyName);
    if (!key.empty())
    {
        m_state.objectNumberProperties[key] = value;
    }
    else
    {
        recordUnimplementedCommand("setPropNumber", propertyName, line, {});
    }
}

int32_t Mm9ScriptRuntime::getObjectNumberProperty(const std::string &propertyKey, int32_t defaultValue) const
{
    const auto iterator = m_state.objectNumberProperties.find(propertyKey);
    return iterator != m_state.objectNumberProperties.end() ? iterator->second : defaultValue;
}

void Mm9ScriptRuntime::setObjectNumberPropertyForHandle(
    const std::string &objectHandle,
    const std::string &propertyName,
    int32_t value)
{
    const std::string key = objectNumberPropertyKeyForHandle(objectHandle, propertyName);
    if (!key.empty())
    {
        m_state.objectNumberProperties[key] = value;
    }
}

int32_t Mm9ScriptRuntime::getObjectNumberPropertyForHandle(
    const std::string &objectHandle,
    const std::string &propertyName,
    int32_t defaultValue) const
{
    const std::string key = objectNumberPropertyKeyForHandle(objectHandle, propertyName);
    if (key.empty())
    {
        return defaultValue;
    }

    const auto iterator = m_state.objectNumberProperties.find(key);
    return iterator != m_state.objectNumberProperties.end() ? iterator->second : defaultValue;
}

void Mm9ScriptRuntime::setObjectStringPropertyForHandle(
    const std::string &objectHandle,
    const std::string &propertyName,
    const std::string &value)
{
    const std::string trimmedPropertyName = trimCopy(propertyName);
    if (objectHandle.empty() || trimmedPropertyName.empty())
    {
        return;
    }

    m_state.objectStringProperties[objectHandle][trimmedPropertyName] = resolveScriptString(value);
}

std::string Mm9ScriptRuntime::getObjectStringPropertyForHandle(
    const std::string &objectHandle,
    const std::string &propertyName) const
{
    const std::string trimmedPropertyName = trimCopy(propertyName);
    std::string value;
    const auto objectIterator = m_state.objectStringProperties.find(objectHandle);
    if (objectIterator != m_state.objectStringProperties.end())
    {
        const auto valueIterator = objectIterator->second.find(trimmedPropertyName);
        if (valueIterator != objectIterator->second.end())
        {
            value = valueIterator->second;
        }
    }
    if (value.empty() && lowerCopy(trimmedPropertyName) == "scriptname")
    {
        const auto scriptIterator = m_state.objectScriptOverrides.find(objectHandle);
        value = scriptIterator != m_state.objectScriptOverrides.end() ? scriptIterator->second : m_activeScriptSource;
    }
    return value;
}

std::string Mm9ScriptRuntime::resolveScriptString(const std::string &token) const
{
    const std::string trimmed = trimCopy(token);
    if (trimmed.size() >= 2 && trimmed.front() == '"' && trimmed.back() == '"')
    {
        return trimmed.substr(1, trimmed.size() - 2);
    }

    const std::string lowered = lowerCopy(trimmed);
    const std::string missingHandle = "\x1f";
    const std::string objectHandleVar = getObjectHandleVar(trimmed, missingHandle);
    if (objectHandleVar != missingHandle)
    {
        return objectHandleVar;
    }

    const auto scriptIterator = m_state.scriptStrVars.find(trimmed);
    if (scriptIterator != m_state.scriptStrVars.end())
    {
        return scriptIterator->second;
    }

    const auto consoleIterator = m_state.consoleStrVars.find(trimmed);
    if (consoleIterator != m_state.consoleStrVars.end())
    {
        return consoleIterator->second;
    }

    if (lowered == "hme" || lowered == "g_hmyobject")
    {
        return activeObjectHandle();
    }
    if (lowered == "hplayer" || lowered == "player")
    {
        return "mm9:player";
    }

    const std::string objectHandle = objectHandleForName(trimmed);
    if (!objectHandle.empty())
    {
        return objectHandle;
    }

    return trimmed;
}

bool Mm9ScriptRuntime::executeCommand(
    const std::string &command,
    const std::string &argumentsText,
    size_t line,
    const std::string &rawLine)
{
    std::string normalizedCommand = lowerCopy(trimCopy(command));
    std::string trimmedArguments = trimCopy(argumentsText);

    if ((normalizedCommand.rfind("if(", 0) == 0 || normalizedCommand.rfind("while(", 0) == 0)
        && normalizedCommand.size() > 3 && normalizedCommand.back() == ')' && trimmedArguments.empty())
    {
        const bool isWhile = normalizedCommand.rfind("while(", 0) == 0;
        const size_t conditionOffset = isWhile ? 6 : 3;
        trimmedArguments = normalizedCommand.substr(conditionOffset, normalizedCommand.size() - conditionOffset - 1);
        normalizedCommand = isWhile ? "while" : "if";
    }
    else if (normalizedCommand == "(if")
    {
        normalizedCommand = "if";
    }

    if (normalizedCommand.size() > 1 && normalizedCommand.back() == '(')
    {
        normalizedCommand.pop_back();
        if (!trimmedArguments.empty() && trimmedArguments.back() == ')')
        {
            trimmedArguments = trimCopy(trimmedArguments.substr(0, trimmedArguments.size() - 1));
        }
    }

    if (!trimmedArguments.empty() && trimmedArguments.front() == '=')
    {
        const std::string target = rawAssignmentTarget(command, rawLine);
        const Mm9ScriptValue value = evaluateScriptExpression(*this, trimCopy(trimmedArguments.substr(1)));
        setScriptVariableFromValue(*this, target, value);
        return true;
    }

    if (normalizedCommand == "set")
    {
        std::string target;
        std::string expression;
        if (hasTopLevelComma(trimmedArguments))
        {
            const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
            if (arguments.size() < 2)
            {
                return false;
            }
            target = trimCopy(arguments[0]);
            expression = trimCopy(arguments[1]);
        }
        else
        {
            target = firstScriptArgument(trimmedArguments, expression);
        }
        setScriptVariableFromValue(*this, target, evaluateScriptExpression(*this, expression));
        return true;
    }

    if (normalizedCommand == "setint")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 2)
        {
            return false;
        }

        setScriptVariableFromValue(*this, arguments[0], evaluateScriptExpression(*this, arguments[1]));
        return true;
    }

    if (normalizedCommand == "exit")
    {
        Mm9ScriptRuntimeControlRequest request = {};
        request.scriptSource = m_activeScriptSource;
        request.operation = normalizedCommand;
        request.exitValue = trimmedArguments.empty()
            ? ""
            : scriptValueString(evaluateScriptExpression(*this, trimmedArguments));
        request.line = line;
        recordControlRequest(std::move(request));
        return true;
    }

    if (normalizedCommand == "gosub" || normalizedCommand == "goto")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.empty())
        {
            return false;
        }

        Mm9ScriptRuntimeControlRequest request = {};
        request.scriptSource = m_activeScriptSource;
        request.operation = normalizedCommand;
        request.label = trimCopy(arguments[0]);
        request.line = line;
        recordControlRequest(std::move(request));
        return true;
    }

    if (normalizedCommand == "wait")
    {
        const std::vector<std::string> arguments = normalizedWaitArguments(splitScriptArguments(trimmedArguments));
        if (arguments.size() < 3)
        {
            return false;
        }

        Mm9ScriptRuntimeControlRequest request = {};
        request.scriptSource = m_activeScriptSource;
        request.operation = normalizedCommand;
        request.minDelay = scriptValueNumber(evaluateScriptExpression(*this, arguments[0]));
        request.maxDelay = scriptValueNumber(evaluateScriptExpression(*this, arguments[1]));
        request.label = trimCopy(arguments[2]);
        request.line = line;
        scheduleInvocation(normalizedCommand, request.label, request.minDelay, request.maxDelay, line);
        recordControlRequest(std::move(request));
        return true;
    }

    if (normalizedCommand == "@m")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        double hour = 0.0;
        double minute = 0.0;
        size_t labelOffset = 0;
        if (!parseMm9MinuteSchedule(*this, arguments, hour, minute, labelOffset))
        {
            return false;
        }

        const std::vector<std::string> labels = labelsAfterMm9MinuteSchedule(arguments, labelOffset);
        Mm9ScriptRuntimeControlRequest request = {};
        request.scriptSource = m_activeScriptSource;
        request.operation = normalizedCommand;
        request.minDelay = hour;
        request.maxDelay = minute;
        request.label = !labels.empty() ? labels[0] : "";
        request.exitValue = labels.size() >= 2 ? labels[1] : "";
        request.conditionText = trimmedArguments;
        request.line = line;
        recordControlRequest(std::move(request));
        return true;
    }

    if (normalizedCommand == "if" || normalizedCommand == "if(" || normalizedCommand == "while"
        || normalizedCommand == "while(")
    {
        Mm9ScriptRuntimeControlRequest request = {};
        request.scriptSource = m_activeScriptSource;
        request.operation = normalizedCommand == "if(" ? "if" : normalizedCommand;
        request.operation = request.operation == "while(" ? "while" : request.operation;
        request.conditionText = normalizeControlConditionText(normalizedCommand, trimmedArguments);
        request.conditionResult = scriptValueTruthy(evaluateScriptExpression(*this, request.conditionText));
        request.line = line;
        recordControlRequest(std::move(request));
        return true;
    }

    if (normalizedCommand == "else" || normalizedCommand == "endif" || normalizedCommand == "endwhile")
    {
        Mm9ScriptRuntimeControlRequest request = {};
        request.scriptSource = m_activeScriptSource;
        request.operation = normalizedCommand;
        request.line = line;
        recordControlRequest(std::move(request));
        return true;
    }

    if (normalizedCommand == "add" || normalizedCommand == "sub" || normalizedCommand == "subtract"
        || normalizedCommand == "mul" || normalizedCommand == "multiply"
        || normalizedCommand == "div" || normalizedCommand == "divide")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 2 || trimCopy(arguments[0]).empty())
        {
            return false;
        }

        const std::string target = trimCopy(arguments[0]);
        const double currentValue = getScriptNumVar(target, 0);
        const double operand = scriptValueNumber(evaluateScriptExpression(*this, arguments[1]));
        double result = currentValue;
        if (normalizedCommand == "add")
        {
            result += operand;
        }
        else if (normalizedCommand == "sub" || normalizedCommand == "subtract")
        {
            result -= operand;
        }
        else if (normalizedCommand == "mul" || normalizedCommand == "multiply")
        {
            result *= operand;
        }
        else if (operand != 0.0)
        {
            result /= operand;
        }
        else
        {
            result = 0.0;
        }

        setScriptVariableFromValue(*this, target, numberValue(result));
        return true;
    }

    if (normalizedCommand == "mod")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 2)
        {
            return false;
        }

        const int32_t dividend = static_cast<int32_t>(scriptValueNumber(evaluateScriptExpression(*this, arguments[0])));
        const int32_t divisor = static_cast<int32_t>(scriptValueNumber(evaluateScriptExpression(*this, arguments[1])));
        setScriptVariableFromValue(*this, arguments[0], numberValue(divisor == 0 ? 0 : dividend % divisor));
        return true;
    }

    if (normalizedCommand == "sin" || normalizedCommand == "cos")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 2)
        {
            return false;
        }

        const double radians = scriptValueNumber(evaluateScriptExpression(*this, arguments[0])) * std::acos(-1.0)
            / 180.0;
        const double result = normalizedCommand == "sin" ? std::sin(radians) : std::cos(radians);
        setScriptVariableFromValue(*this, arguments[1], numberValue(result));
        return true;
    }

    if (normalizedCommand == "arrayput")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 3)
        {
            return false;
        }

        const std::string arrayName = trimCopy(arguments[0]);
        const int32_t index = static_cast<int32_t>(scriptValueNumber(evaluateScriptExpression(*this, arguments[1])));
        const Mm9ScriptValue value = evaluateScriptExpression(*this, arguments[2]);
        m_state.scriptStrArrays[arrayName][index] = scriptValueString(value);
        m_state.scriptNumArrays[arrayName][index] = static_cast<int32_t>(scriptValueNumber(value));
        return true;
    }

    if (normalizedCommand == "arrayget")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 3)
        {
            return false;
        }

        const std::string arrayName = trimCopy(arguments[0]);
        const int32_t index = static_cast<int32_t>(scriptValueNumber(evaluateScriptExpression(*this, arguments[1])));
        const std::string target = trimCopy(arguments[2]);
        const auto strArrayIterator = m_state.scriptStrArrays.find(arrayName);
        if (strArrayIterator != m_state.scriptStrArrays.end())
        {
            const auto valueIterator = strArrayIterator->second.find(index);
            if (valueIterator != strArrayIterator->second.end())
            {
                if (valueIterator->second == "mm9:player" || mm9ObjectHandleParts(valueIterator->second))
                {
                    setObjectHandleVar(target, valueIterator->second);
                }
                else
                {
                    setScriptVariableFromString(*this, target, valueIterator->second);
                }
                return true;
            }
        }

        const auto numArrayIterator = m_state.scriptNumArrays.find(arrayName);
        if (numArrayIterator != m_state.scriptNumArrays.end())
        {
            const auto valueIterator = numArrayIterator->second.find(index);
            if (valueIterator != numArrayIterator->second.end())
            {
                setScriptVariableFromValue(*this, target, numberValue(valueIterator->second));
                return true;
            }
        }

        setScriptVariableFromValue(*this, target, nullValue());
        return true;
    }

    if (normalizedCommand == "getrandomint")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 3)
        {
            return false;
        }

        const int32_t minValue =
            static_cast<int32_t>(scriptValueNumber(evaluateScriptExpression(*this, arguments[0])));
        const int32_t maxValue =
            static_cast<int32_t>(scriptValueNumber(evaluateScriptExpression(*this, arguments[1])));
        const int32_t low = std::min(minValue, maxValue);
        const int32_t high = std::max(minValue, maxValue);
        const int32_t span = std::max(1, high - low + 1);
        setScriptVariableFromValue(*this, trimCopy(arguments[2]), numberValue(low + (std::rand() % span)));
        return true;
    }

    if (normalizedCommand == "getrandomfloat")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 3)
        {
            return false;
        }

        const double minValue = scriptValueNumber(evaluateScriptExpression(*this, arguments[0]));
        const double maxValue = scriptValueNumber(evaluateScriptExpression(*this, arguments[1]));
        const double low = std::min(minValue, maxValue);
        const double high = std::max(minValue, maxValue);
        const double t = static_cast<double>(std::rand()) / static_cast<double>(RAND_MAX);
        setScriptVariableFromValue(*this, trimCopy(arguments[2]), numberValue(low + ((high - low) * t)));
        return true;
    }

    if (normalizedCommand == "gettime")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.empty())
        {
            return false;
        }

        setScriptVariableFromValue(*this, trimCopy(arguments[0]), numberValue(m_state.scriptTimeSeconds));
        return true;
    }

    if (normalizedCommand == "debugout" || normalizedCommand == "cprint")
    {
        return true;
    }

    if (normalizedCommand == "breakpoint" || normalizedCommand == "dont_include_this_file")
    {
        return true;
    }

    if (normalizedCommand == "traceoff" || normalizedCommand == "traceon")
    {
        return true;
    }

    if (normalizedCommand == "isturnbased" || normalizedCommand == "getpcvoice")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.empty())
        {
            return false;
        }

        setScriptVariableFromValue(*this, arguments[0], numberValue(0.0));
        return true;
    }

    if (normalizedCommand == "getgametime")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 2)
        {
            return false;
        }

        int32_t hour = 0;
        int32_t minute = 0;
        scriptClockHourMinute(m_state.scriptTimeSeconds, hour, minute);
        setScriptVariableFromValue(*this, arguments[0], numberValue(hour));
        setScriptVariableFromValue(*this, arguments[1], numberValue(minute));
        return true;
    }

    if (normalizedCommand == "getpclevel")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 2)
        {
            return false;
        }

        const int32_t memberIndex = scriptArgumentNumber(*this, arguments, 0);
        const std::vector<Character> &members = m_dialogueRuntime.party().members();
        const bool validIndex = memberIndex >= 0 && static_cast<size_t>(memberIndex) < members.size();
        const uint32_t level = validIndex ? members[static_cast<size_t>(memberIndex)].level : 0;
        setScriptVariableFromValue(*this, arguments[1], numberValue(level));
        recordPartyAccess("getPcLevel", static_cast<uint32_t>(std::max(0, memberIndex)), 0, validIndex, line);
        return true;
    }

    if (normalizedCommand == "getattribute" || normalizedCommand == "heal")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 2)
        {
            return false;
        }

        Mm9ScriptRuntimePartyCommandRequest request = {};
        request.scriptSource = m_activeScriptSource;
        request.operation = normalizedCommand;
        request.arguments = arguments;
        request.line = line;
        recordPartyCommandRequest(std::move(request));

        if (normalizedCommand == "getattribute")
        {
            const Character *pMember = m_dialogueRuntime.party().activeMember();
            const int32_t attributeId = mm9AttributeIdFromArgument(*this, arguments[0]);
            const int32_t value = pMember != nullptr ? mm9CharacterAttributeValue(*pMember, attributeId) : 0;
            setScriptVariableFromValue(*this, arguments[1], numberValue(value));
        }
        else
        {
            const std::string targetHandle = resolveScriptString(arguments[0]);
            const int32_t amount = std::max(0, scriptArgumentNumber(*this, arguments, 1));
            if (targetHandle == "mm9:player")
            {
                m_dialogueRuntime.party().healMember(m_dialogueRuntime.party().activeMemberIndex(), amount);
            }
            else
            {
                auto objectIterator = m_state.objectStats.find(targetHandle);
                if (objectIterator != m_state.objectStats.end())
                {
                    auto hitPointsIterator = findCaseInsensitiveStat(objectIterator->second, "HitPoints");
                    if (hitPointsIterator != objectIterator->second.end())
                    {
                        const auto maxHitPointsIterator =
                            findCaseInsensitiveStat(objectIterator->second, "MaxHitPoints");
                        const int32_t maxHitPoints = maxHitPointsIterator != objectIterator->second.end()
                            ? std::max(0, maxHitPointsIterator->second)
                            : std::max(0, hitPointsIterator->second + amount);
                        hitPointsIterator->second =
                            std::clamp(hitPointsIterator->second + amount, 0, maxHitPoints);
                    }
                }
            }
        }

        recordPartyAccess(
            normalizedCommand,
            normalizedCommand == "getattribute" ? static_cast<uint32_t>(mm9AttributeIdFromArgument(*this, arguments[0]))
                                                : 0,
            scriptArgumentNumber(*this, arguments, 1),
            true,
            line);
        return true;
    }

    if (normalizedCommand == "addnpc" || normalizedCommand == "removenpc")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.empty())
        {
            return false;
        }

        Mm9ScriptRuntimePartyCommandRequest request = {};
        request.scriptSource = m_activeScriptSource;
        request.operation = normalizedCommand;
        request.arguments = arguments;
        request.line = line;
        recordPartyCommandRequest(std::move(request));
        if (normalizedCommand == "addnpc" && arguments.size() >= 2)
        {
            const std::string npcHandle =
                "mm9:npc:" + scriptValueString(evaluateScriptExpression(*this, arguments[0]));
            setObjectHandleVar(arguments[1], npcHandle);
        }
        recordPartyAccess(
            normalizedCommand,
            unsignedIdFromArgument(*this, arguments[0]),
            1,
            true,
            line);
        return true;
    }

    if (normalizedCommand == "cachescript")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.empty())
        {
            return false;
        }

        Mm9ScriptRuntimeControlRequest request = {};
        request.scriptSource = m_activeScriptSource;
        request.operation = normalizedCommand;
        request.label = resolveScriptString(arguments[0]);
        request.line = line;
        recordControlRequest(std::move(request));
        return true;
    }

    if (normalizedCommand == "getparam")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 2)
        {
            return false;
        }

        const int32_t paramIndex = scriptArgumentNumber(*this, arguments, 0);
        const std::vector<std::string> &params = m_dialogueRuntime.owner().scriptParams;
        const std::string value = paramIndex >= 0 && static_cast<size_t>(paramIndex) < params.size()
            ? params[static_cast<size_t>(paramIndex)]
            : "";
        setScriptVariableFromString(*this, arguments[1], value);
        return true;
    }

    if (normalizedCommand == "setparam" || normalizedCommand == "consolecommand"
        || normalizedCommand == "dohighscore" || normalizedCommand == "killcallback"
        || normalizedCommand == "savepath" || normalizedCommand == "restorepath"
        || normalizedCommand == "removemodelkey" || normalizedCommand == "clearcondition"
        || normalizedCommand == "setcondition" || normalizedCommand == "setstuck")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (normalizedCommand == "setparam" && arguments.size() < 2)
        {
            return false;
        }

        if (normalizedCommand == "setstuck")
        {
            m_state.objectAiStates[activeObjectHandle()] = "stuck";
        }
        if (normalizedCommand == "setparam")
        {
            const int32_t paramIndex = scriptArgumentNumber(*this, arguments, 0);
            if (paramIndex >= 0)
            {
                Mm9DialogueOwnerContext owner = m_dialogueRuntime.owner();
                std::vector<std::string> &params = owner.scriptParams;
                const size_t index = static_cast<size_t>(paramIndex);
                if (params.size() <= index)
                {
                    params.resize(index + 1);
                }
                params[index] = resolveScriptString(arguments[1]);
                m_dialogueRuntime.setOwnerContext(std::move(owner));
            }
        }
        else if (normalizedCommand == "killcallback" && !arguments.empty())
        {
            removeCallbackRegistrations("setcallback", arguments[0]);
            m_state.scheduledInvocations.erase(
                std::remove_if(
                    m_state.scheduledInvocations.begin(),
                    m_state.scheduledInvocations.end(),
                    [&](const Mm9ScriptRuntimeScheduledInvocation &invocation)
                    {
                        return invocation.operation == "setcallback" && invocation.minDelay == scriptArgumentNumber(
                            *this,
                            arguments,
                            0);
                    }),
                m_state.scheduledInvocations.end());
        }
        else if (normalizedCommand == "removemodelkey" && !arguments.empty())
        {
            removeCallbackRegistrations("addmodelkey", arguments[0]);
        }

        Mm9ScriptRuntimeControlRequest request = {};
        request.scriptSource = m_activeScriptSource;
        request.operation = normalizedCommand;
        if (!arguments.empty())
        {
            request.label = trimCopy(arguments[0]);
        }
        if (arguments.size() >= 2)
        {
            request.exitValue = resolveScriptString(arguments[1]);
        }
        request.conditionText = trimmedArguments;
        request.line = line;
        recordControlRequest(std::move(request));
        return true;
    }

    if (normalizedCommand == "docallback")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.empty())
        {
            return false;
        }

        Mm9ScriptRuntimeControlRequest request = {};
        request.scriptSource = m_activeScriptSource;
        request.operation = normalizedCommand;
        request.label = trimCopy(arguments[0]);
        request.conditionText = trimmedArguments;
        request.conditionResult = scriptValueBool(evaluateScriptExpression(*this, arguments[0]));
        request.line = line;
        recordControlRequest(std::move(request));
        std::optional<std::string> error;
        size_t dispatchedCount = 0;
        return dispatchRegisteredCallbacks(
            "setcallback",
            arguments[0],
            m_dialogueRuntime.owner().mapId,
            m_dialogueRuntime.owner().objectIndex,
            error,
            dispatchedCount);
    }

    if (normalizedCommand == "cachetexture" || normalizedCommand == "hidepiece" || normalizedCommand == "doletter"
        || normalizedCommand == "getcontainercount")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (normalizedCommand == "getcontainercount")
        {
            if (arguments.size() < 2)
            {
                return false;
            }
            setScriptVariableFromValue(*this, arguments[1], numberValue(0.0));
        }
        recordPresentationRequest(normalizedCommand, arguments, line);
        return true;
    }

    if (normalizedCommand == "cachesound" || normalizedCommand == "playsound"
        || normalizedCommand == "playsoundhandle" || normalizedCommand == "killsound"
        || normalizedCommand == "getsoundduration" || normalizedCommand == "issounddone"
        || normalizedCommand == "speak")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.empty())
        {
            return false;
        }

        Mm9ScriptRuntimeAudioRequest request = {};
        request.operation = normalizedCommand;
        request.line = line;

        if (normalizedCommand == "killsound")
        {
            request.soundHandle = resolveSoundHandle(arguments[0]);
            m_state.activeSoundHandles.erase(request.soundHandle);
            recordAudioRequest(std::move(request));
            return true;
        }

        if (normalizedCommand == "getsoundduration")
        {
            if (arguments.size() < 3)
            {
                return false;
            }

            request.soundName = resolveScriptString(arguments[0]);
            request.soundHandle = resolveSoundHandle(arguments[1]);
            setScriptVariableFromValue(*this, arguments[2], numberValue(0.0));
            recordAudioRequest(std::move(request));
            return true;
        }

        if (normalizedCommand == "issounddone")
        {
            if (arguments.size() < 2)
            {
                return false;
            }

            request.soundHandle = resolveSoundHandle(arguments[0]);
            setScriptVariableFromValue(
                *this,
                arguments[1],
                numberValue(m_state.activeSoundHandles.count(request.soundHandle) == 0 ? 1.0 : 0.0));
            recordAudioRequest(std::move(request));
            return true;
        }

        request.soundName = resolveScriptString(arguments[0]);
        if ((normalizedCommand == "playsound" || normalizedCommand == "speak") && arguments.size() >= 2)
        {
            request.callbackLabel = trimCopy(arguments[1]);
            request.radius = scriptArgumentNumber(*this, arguments, 2);
            request.volume = scriptArgumentNumber(*this, arguments, 3);
            request.loop = scriptArgumentBool(*this, arguments, 4);
            if (isCallbackLabel(request.callbackLabel))
            {
                registerCallback(request.callbackLabel, line, "playsound", request.soundName);
            }
        }
        else if (normalizedCommand == "playsoundhandle")
        {
            if (arguments.size() < 2)
            {
                return false;
            }

            request.handleVar = trimCopy(arguments[1]);
            request.radius = scriptArgumentNumber(*this, arguments, 2);
            request.loop = scriptArgumentBool(*this, arguments, 3);
            request.volume = scriptArgumentNumber(*this, arguments, 4);
            request.soundHandle = "mm9:sound:" + std::to_string(m_state.nextSoundHandleId++);
            m_state.soundHandleVars[request.handleVar] = request.soundHandle;
            m_state.activeSoundHandles[request.soundHandle] = request.soundName;
            setScriptVariableFromString(*this, request.handleVar, request.soundHandle);
        }

        recordAudioRequest(std::move(request));
        return true;
    }

    if (normalizedCommand == "playanim" || normalizedCommand == "loopanim" || normalizedCommand == "playanimation")
    {
        return requestAnimation(activeObjectHandle(), normalizedCommand, splitScriptArguments(trimmedArguments), line);
    }

    if (normalizedCommand == "playanimsound")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.empty())
        {
            return false;
        }

        Mm9ScriptRuntimeAnimationRequest request = {};
        request.scriptSource = m_activeScriptSource;
        request.objectHandle = activeObjectHandle();
        request.operation = normalizedCommand;
        request.animationName = resolveScriptString(arguments[0]);
        request.loopCount = scriptArgumentNumber(*this, arguments, 1);
        request.line = line;
        recordAnimationRequest(std::move(request));
        return true;
    }

    if (normalizedCommand == "taunt" || normalizedCommand == "aware" || normalizedCommand == "launch"
        || normalizedCommand == "converse" || normalizedCommand == "resumewait"
        || normalizedCommand == "pausewait" || normalizedCommand == "jump" || normalizedCommand == "blendanim")
    {
        return requestActorAction(
            activeObjectHandle(),
            normalizedCommand,
            splitScriptArguments(trimmedArguments),
            line);
    }

    if (normalizedCommand == "getcurranim" || normalizedCommand == "getanimname" || normalizedCommand == "getanimnbr")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if ((normalizedCommand == "getcurranim" && arguments.size() < 2)
            || ((normalizedCommand == "getanimname" || normalizedCommand == "getanimnbr") && arguments.size() < 3))
        {
            return false;
        }

        if (normalizedCommand == "getcurranim")
        {
            setScriptVariableFromValue(*this, arguments[1], numberValue(0.0));
        }
        else if (normalizedCommand == "getanimnbr")
        {
            setScriptVariableFromValue(*this, arguments[2], numberValue(0.0));
        }
        else
        {
            const auto requestIterator = std::find_if(
                m_animationRequests.rbegin(),
                m_animationRequests.rend(),
                [&](const Mm9ScriptRuntimeAnimationRequest &request)
                {
                    return request.objectHandle == resolveScriptString(arguments[0]);
                });
            const std::string animationName = requestIterator != m_animationRequests.rend()
                ? requestIterator->animationName
                : "";
            setScriptVariableFromString(*this, arguments[2], animationName);
        }
        return true;
    }

    if (normalizedCommand == "setanimplaying")
    {
        Mm9ScriptRuntimeAnimationRequest request = {};
        request.scriptSource = m_activeScriptSource;
        request.objectHandle = activeObjectHandle();
        request.operation = normalizedCommand;
        request.animationName = scriptValueString(evaluateScriptExpression(*this, trimmedArguments));
        request.line = line;
        recordAnimationRequest(std::move(request));
        return true;
    }

    if (normalizedCommand == "cacheclientfx" || normalizedCommand == "doclientfx"
        || normalizedCommand == "createfx")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.empty() || ((normalizedCommand == "doclientfx" || normalizedCommand == "createfx")
            && arguments.size() < 2))
        {
            return false;
        }

        Mm9ScriptRuntimeClientFxRequest request = {};
        request.scriptSource = m_activeScriptSource;
        request.operation = normalizedCommand;
        request.line = line;
        if (normalizedCommand == "cacheclientfx")
        {
            request.effectName = resolveScriptString(arguments[0]);
        }
        else
        {
            request.objectHandle = normalizedCommand == "createfx"
                ? resolveScriptString(arguments[1])
                : resolveScriptString(arguments[0]);
            request.effectName = normalizedCommand == "createfx"
                ? resolveScriptString(arguments[0])
                : resolveScriptString(arguments[1]);
            request.attach = scriptArgumentBool(*this, arguments, 2);
            request.loop = scriptArgumentBool(*this, arguments, 3);
        }

        recordClientFxRequest(std::move(request));
        return true;
    }

    if (normalizedCommand == "screenfadeout" || normalizedCommand == "screenfadein"
        || normalizedCommand == "letterbox" || normalizedCommand == "rollovertext")
    {
        recordPresentationRequest(normalizedCommand, splitScriptArguments(trimmedArguments), line);
        return true;
    }

    if (normalizedCommand == "getpos")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 4)
        {
            return false;
        }

        const std::string handle = resolveScriptString(arguments[0]);
        const auto positionIterator = m_state.objectPositions.find(handle);
        const Mm9ScriptRuntimeVec3 position =
            positionIterator != m_state.objectPositions.end() ? positionIterator->second : Mm9ScriptRuntimeVec3();
        setScriptVariableFromValue(*this, arguments[1], numberValue(position.x));
        setScriptVariableFromValue(*this, arguments[2], numberValue(position.y));
        setScriptVariableFromValue(*this, arguments[3], numberValue(position.z));
        return true;
    }

    if (normalizedCommand == "setpos")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 4)
        {
            return false;
        }

        const std::string handle = resolveScriptString(arguments[0]);
        m_state.objectPositions[handle] = scriptVectorFromArguments(*this, arguments, 1);
        return true;
    }

    if (normalizedCommand == "movetopos" || normalizedCommand == "runtopos"
        || normalizedCommand == "walktopos" || normalizedCommand == "walkto" || normalizedCommand == "runto"
        || normalizedCommand == "movedir" || normalizedCommand == "faceobject" || normalizedCommand == "rotate"
        || normalizedCommand == "facedir" || normalizedCommand == "facepos" || normalizedCommand == "walk"
        || normalizedCommand == "run" || normalizedCommand == "strafe" || normalizedCommand == "stop")
    {
        return requestMovement(activeObjectHandle(), normalizedCommand, splitScriptArguments(trimmedArguments), line);
    }

    if (normalizedCommand == "setrotation")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 3)
        {
            return false;
        }

        const std::string firstArgumentHandle = resolveScriptString(arguments[0]);
        const bool hasExplicitHandle = firstArgumentHandle == "mm9:player" || mm9ObjectHandleParts(firstArgumentHandle);
        const std::string handle = hasExplicitHandle ? firstArgumentHandle : activeObjectHandle();
        const size_t vectorOffset = hasExplicitHandle ? 1 : 0;
        m_state.objectFaceDirs[handle] = scriptVectorFromArguments(*this, arguments, vectorOffset);

        Mm9ScriptRuntimeMovementRequest request = {};
        request.scriptSource = m_activeScriptSource;
        request.objectHandle = handle;
        request.operation = normalizedCommand;
        request.direction = m_state.objectFaceDirs[handle];
        request.distance = arguments.size() >= vectorOffset + 4
            ? scriptValueNumber(evaluateScriptExpression(*this, arguments[vectorOffset + 3]))
            : 0.0;
        request.speed = arguments.size() >= vectorOffset + 5
            ? scriptValueNumber(evaluateScriptExpression(*this, arguments[vectorOffset + 4]))
            : 0.0;
        request.line = line;
        recordMovementRequest(std::move(request));
        return true;
    }

    if (normalizedCommand == "calcrotationrate")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 3)
        {
            return false;
        }

        setScriptVariableFromValue(
            *this,
            arguments[2],
            numberValue(scriptValueNumber(evaluateScriptExpression(*this, arguments[1]))));
        return true;
    }

    if (normalizedCommand == "setpushback" || normalizedCommand == "strafe" || normalizedCommand == "turnleft")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if ((normalizedCommand == "setpushback" && arguments.size() < 4)
            || (normalizedCommand == "strafe" && arguments.size() < 3)
            || (normalizedCommand == "turnleft" && arguments.empty()))
        {
            return false;
        }

        Mm9ScriptRuntimeMovementRequest request = {};
        request.scriptSource = m_activeScriptSource;
        request.objectHandle = activeObjectHandle();
        request.operation = normalizedCommand;
        if (normalizedCommand == "turnleft")
        {
            request.direction = {0.0, 0.0, 1.0};
            request.distance = scriptValueNumber(evaluateScriptExpression(*this, arguments[0]));
        }
        else
        {
            request.direction = scriptVectorFromArguments(*this, arguments, 0);
            if (arguments.size() >= 4)
            {
                request.speed = scriptValueNumber(evaluateScriptExpression(*this, arguments[3]));
            }
        }
        request.line = line;
        recordMovementRequest(std::move(request));
        return true;
    }

    if (normalizedCommand == "setidle")
    {
        const std::string handle = activeObjectHandle();
        if (handle.empty())
        {
            return false;
        }

        m_state.objectAiStates[handle] = "idle";
        m_state.objectAttackStates[handle] = false;
        return true;
    }

    if (normalizedCommand == "setcrouch")
    {
        m_state.objectStats[activeObjectHandle()]["Crouch"] =
            scriptValueTruthy(evaluateScriptExpression(*this, trimmedArguments)) ? 1 : 0;
        return true;
    }

    if (normalizedCommand == "addfriend" || normalizedCommand == "addenemy")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.empty())
        {
            return false;
        }

        const std::string handle = activeObjectHandle();
        const std::string classOrName = unquoteScriptString(arguments[0]);
        if (normalizedCommand == "addfriend")
        {
            m_state.objectFriends[handle].push_back(classOrName);
        }
        else
        {
            m_state.objectEnemies[handle].push_back(classOrName);
        }
        return true;
    }

    if (normalizedCommand == "removefriend" || normalizedCommand == "removeenemy")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.empty())
        {
            return false;
        }

        const std::string handle = activeObjectHandle();
        std::vector<std::string> &relations = normalizedCommand == "removefriend"
            ? m_state.objectFriends[handle]
            : m_state.objectEnemies[handle];
        const std::string loweredRelation = lowerCopy(unquoteScriptString(arguments[0]));
        relations.erase(
            std::remove_if(
                relations.begin(),
                relations.end(),
                [&](const std::string &relation)
                {
                    return lowerCopy(relation) == loweredRelation;
                }),
            relations.end());
        return true;
    }

    if (normalizedCommand == "isfriend")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 2)
        {
            return false;
        }

        const std::string activeHandle = activeObjectHandle();
        const std::string targetHandle = resolveScriptString(arguments[0]);
        const Mm9GeneratedObjectDialogueBinding *pBinding = objectBindingForHandle(targetHandle);
        const auto friendsIterator = m_state.objectFriends.find(activeHandle);
        bool isFriend = false;
        if (friendsIterator != m_state.objectFriends.end())
        {
            for (const std::string &friendToken : friendsIterator->second)
            {
                const std::string loweredFriend = lowerCopy(friendToken);
                isFriend = isFriend || loweredFriend == lowerCopy(targetHandle);
                isFriend = isFriend || (pBinding != nullptr && loweredFriend == lowerCopy(pBinding->objectName));
                isFriend = isFriend || (pBinding != nullptr && loweredFriend == lowerCopy(pBinding->objectClass));
            }
        }

        setScriptVariableFromValue(*this, arguments[1], numberValue(isFriend ? 1.0 : 0.0));
        return true;
    }

    if (normalizedCommand == "isai" || normalizedCommand == "isactor" || normalizedCommand == "isvisible")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 2)
        {
            return false;
        }

        const std::string handle = resolveScriptString(arguments[0]);
        const Mm9GeneratedObjectDialogueBinding *pBinding = objectBindingForHandle(handle);
        bool result = false;
        if (normalizedCommand == "isvisible")
        {
            const auto removedIterator = m_state.removedObjects.find(handle);
            const bool active = removedIterator == m_state.removedObjects.end() || !removedIterator->second;
            result = active && objectFlagValue(m_state, handle, "visible", true);
        }
        else
        {
            result = pBinding != nullptr && lowerCopy(pBinding->objectClass) == "actor";
        }

        setScriptVariableFromValue(*this, arguments[1], numberValue(result ? 1.0 : 0.0));
        return true;
    }

    if (normalizedCommand == "isonground")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.empty())
        {
            return false;
        }

        const std::string handle = activeObjectHandle();
        const auto objectIterator = m_state.objectStats.find(handle);
        bool result = false;
        if (objectIterator != m_state.objectStats.end())
        {
            const auto groundedIterator = objectIterator->second.find("Grounded");
            const auto onGroundIterator = objectIterator->second.find("OnGround");
            result = groundedIterator != objectIterator->second.end() && groundedIterator->second != 0;
            result = result || (onGroundIterator != objectIterator->second.end() && onGroundIterator->second != 0);
        }

        setScriptVariableFromValue(*this, arguments[0], numberValue(result ? 1.0 : 0.0));
        return true;
    }

    if (normalizedCommand == "isclearshot")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 2)
        {
            return false;
        }

        const std::string targetHandle = resolveScriptString(arguments[0]);
        const auto removedIterator = m_state.removedObjects.find(targetHandle);
        const bool result = !targetHandle.empty()
            && (removedIterator == m_state.removedObjects.end() || !removedIterator->second);
        setScriptVariableFromValue(*this, arguments[1], numberValue(result ? 1.0 : 0.0));
        if (arguments.size() >= 3)
        {
            setScriptVariableFromValue(*this, arguments[2], nullValue());
        }
        return true;
    }

    if (normalizedCommand == "canreachobject" || normalizedCommand == "canreachtarget"
        || normalizedCommand == "isobjectactive" || normalizedCommand == "isworldobject"
        || normalizedCommand == "isdead" || normalizedCommand == "isfear"
        || normalizedCommand == "isinnorunzone" || normalizedCommand == "shouldrunaway")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        const size_t resultIndex = normalizedCommand == "canreachtarget"
            || normalizedCommand == "isfear" || normalizedCommand == "isinnorunzone" ? 0 : 1;
        if (arguments.size() <= resultIndex)
        {
            return false;
        }

        std::string handle = resultIndex == 0 ? activeObjectHandle() : resolveScriptString(arguments[0]);
        if (normalizedCommand == "canreachtarget")
        {
            const auto targetIterator = m_state.objectTargetHandles.find(activeObjectHandle());
            handle = targetIterator != m_state.objectTargetHandles.end() ? targetIterator->second : "";
        }

        bool result = false;
        if (normalizedCommand == "canreachobject" || normalizedCommand == "canreachtarget")
        {
            result = !handle.empty();
        }
        else if (normalizedCommand == "isobjectactive")
        {
            const auto removedIterator = m_state.removedObjects.find(handle);
            result = removedIterator == m_state.removedObjects.end() || !removedIterator->second;
        }
        else if (normalizedCommand == "isworldobject")
        {
            result = handle != "mm9:player" && !handle.empty();
        }
        else if (normalizedCommand == "isdead")
        {
            const auto aiIterator = m_state.objectAiStates.find(handle);
            const auto removedIterator = m_state.removedObjects.find(handle);
            result = (aiIterator != m_state.objectAiStates.end() && aiIterator->second == "dead")
                || (removedIterator != m_state.removedObjects.end() && removedIterator->second);
        }

        setScriptVariableFromValue(*this, arguments[resultIndex], numberValue(result ? 1.0 : 0.0));
        return true;
    }

    if (normalizedCommand == "ismoving" || normalizedCommand == "isfacing")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.empty() || (normalizedCommand == "isfacing" && arguments.size() < 2))
        {
            return false;
        }

        const std::string handle = activeObjectHandle();
        bool result = false;
        if (normalizedCommand == "ismoving")
        {
            const auto stateIterator = m_state.objectAiStates.find(handle);
            result = stateIterator != m_state.objectAiStates.end()
                && stateIterator->second != "idle"
                && stateIterator->second != "stopped";
            result = result || std::any_of(
                m_state.movementRequests.begin(),
                m_state.movementRequests.end(),
                [&](const Mm9ScriptRuntimeMovementRequest &request)
                {
                    return request.objectHandle == handle;
                });
            setScriptVariableFromValue(*this, arguments[0], numberValue(result ? 1.0 : 0.0));
        }
        else
        {
            const std::string targetHandle = resolveScriptString(arguments[0]);
            result = !targetHandle.empty();
            setScriptVariableFromValue(*this, arguments[1], numberValue(result ? 1.0 : 0.0));
        }
        return true;
    }

    if (normalizedCommand == "findtargets")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 3)
        {
            return false;
        }

        const std::string arrayName = trimCopy(arguments[0]);
        const int32_t maxTargets = std::max(0, scriptArgumentNumber(*this, arguments, 1));
        int32_t count = 0;
        if (maxTargets > 0)
        {
            m_state.scriptStrArrays[arrayName][count] = "mm9:player";
            ++count;
        }

        setScriptVariableFromValue(*this, arguments[2], numberValue(count));
        return true;
    }

    if (normalizedCommand == "findhidingplace")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.empty())
        {
            return false;
        }

        setObjectHandleVar(arguments[0], activeObjectHandle());
        return true;
    }

    if (normalizedCommand == "castray")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 6)
        {
            return false;
        }

        setObjectHandleVar(arguments[4], activeObjectHandle());
        setScriptVariableFromValue(*this, arguments[5], numberValue(0.0));
        return true;
    }

    if (normalizedCommand == "sendalert")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.empty())
        {
            return false;
        }

        std::string targetHandle = resolveScriptString(arguments[0]);
        const std::string loweredTarget = lowerCopy(trimCopy(targetHandle));
        if (loweredTarget == "null" || loweredTarget == "nil" || loweredTarget == "0")
        {
            targetHandle.clear();
        }

        Mm9ScriptRuntimeAiRequest request = {};
        request.scriptSource = m_activeScriptSource;
        request.objectHandle = activeObjectHandle();
        request.operation = normalizedCommand;
        request.targetHandle = targetHandle;
        request.line = line;
        recordAiRequest(std::move(request));
        return true;
    }

    if (normalizedCommand == "help" || normalizedCommand == "estimaterangeattackhit"
        || normalizedCommand == "land")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        Mm9ScriptRuntimeAiRequest request = {};
        request.scriptSource = m_activeScriptSource;
        request.objectHandle = activeObjectHandle();
        request.operation = normalizedCommand;
        if (!arguments.empty())
        {
            request.targetHandle = resolveScriptString(arguments[0]);
        }
        request.line = line;
        recordAiRequest(std::move(request));
        return true;
    }

    if (normalizedCommand == "settargetlosttime")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.empty())
        {
            return false;
        }

        m_state.objectStats[activeObjectHandle()]["TargetLostTime"] = scriptArgumentNumber(*this, arguments, 0);
        return true;
    }

    if (normalizedCommand == "aigetdistance")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 2)
        {
            return false;
        }

        const std::string sourceHandle = activeObjectHandle();
        const std::string targetHandle = resolveScriptString(arguments[0]);
        const auto sourcePositionIterator = m_state.objectPositions.find(sourceHandle);
        const auto targetPositionIterator = m_state.objectPositions.find(targetHandle);
        const Mm9ScriptRuntimeVec3 sourcePosition = sourcePositionIterator != m_state.objectPositions.end()
            ? sourcePositionIterator->second
            : Mm9ScriptRuntimeVec3();
        const Mm9ScriptRuntimeVec3 targetPosition = targetPositionIterator != m_state.objectPositions.end()
            ? targetPositionIterator->second
            : Mm9ScriptRuntimeVec3();
        setScriptVariableFromValue(
            *this,
            arguments[1],
            numberValue(scriptVectorDistance(sourcePosition, targetPosition)));
        return true;
    }

    if (normalizedCommand == "getdistance")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 3)
        {
            return false;
        }

        const std::string firstHandle = resolveScriptString(arguments[0]);
        const std::string secondHandle = resolveScriptString(arguments[1]);
        const auto firstPositionIterator = m_state.objectPositions.find(firstHandle);
        const auto secondPositionIterator = m_state.objectPositions.find(secondHandle);
        const Mm9ScriptRuntimeVec3 firstPosition = firstPositionIterator != m_state.objectPositions.end()
            ? firstPositionIterator->second
            : Mm9ScriptRuntimeVec3();
        const Mm9ScriptRuntimeVec3 secondPosition = secondPositionIterator != m_state.objectPositions.end()
            ? secondPositionIterator->second
            : Mm9ScriptRuntimeVec3();
        setScriptVariableFromValue(
            *this,
            arguments[2],
            numberValue(scriptVectorDistance(firstPosition, secondPosition)));
        return true;
    }

    if (normalizedCommand == "getdims")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 4)
        {
            return false;
        }

        const std::string handle = resolveScriptString(arguments[0]);
        const auto objectIterator = m_state.objectStats.find(handle);
        const auto statValue = [&](const std::string &name) -> int32_t
        {
            if (objectIterator == m_state.objectStats.end())
            {
                return 0;
            }
            const auto valueIterator = objectIterator->second.find(name);
            return valueIterator != objectIterator->second.end() ? valueIterator->second : 0;
        };
        setScriptVariableFromValue(*this, arguments[1], numberValue(statValue("DimsX")));
        setScriptVariableFromValue(*this, arguments[2], numberValue(statValue("DimsY")));
        setScriptVariableFromValue(*this, arguments[3], numberValue(statValue("DimsZ")));
        return true;
    }

    if (normalizedCommand == "getobjectminmax")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 7)
        {
            return false;
        }

        const std::string handle = resolveScriptString(arguments[0]);
        const auto objectIterator = m_state.objectStats.find(handle);
        const auto statValue = [&](const std::string &name) -> int32_t
        {
            if (objectIterator == m_state.objectStats.end())
            {
                return 0;
            }

            const auto valueIterator = objectIterator->second.find(name);
            return valueIterator != objectIterator->second.end() ? valueIterator->second : 0;
        };

        setScriptVariableFromValue(*this, arguments[1], numberValue(statValue("MinX")));
        setScriptVariableFromValue(*this, arguments[2], numberValue(statValue("MinY")));
        setScriptVariableFromValue(*this, arguments[3], numberValue(statValue("MinZ")));
        setScriptVariableFromValue(*this, arguments[4], numberValue(statValue("MaxX")));
        setScriptVariableFromValue(*this, arguments[5], numberValue(statValue("MaxY")));
        setScriptVariableFromValue(*this, arguments[6], numberValue(statValue("MaxZ")));
        return true;
    }

    if (normalizedCommand == "getplayerswithindist")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 7)
        {
            return false;
        }

        const std::string arrayName = trimCopy(arguments[4]);
        const int32_t maxPlayers = std::max(0, scriptArgumentNumber(*this, arguments, 5));
        const int32_t count = maxPlayers > 0 ? 1 : 0;
        if (count > 0)
        {
            m_state.scriptStrArrays[arrayName][0] = "mm9:player";
            m_state.scriptNumArrays[arrayName][0] = 0;
        }
        setScriptVariableFromValue(*this, arguments[6], numberValue(count));
        return true;
    }

    if (normalizedCommand == "checkworldcollision")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 7)
        {
            return false;
        }

        setScriptVariableFromValue(*this, arguments[3], numberValue(0.0));
        setScriptVariableFromValue(*this, arguments[4], numberValue(0.0));
        setScriptVariableFromValue(*this, arguments[5], numberValue(1.0));
        setScriptVariableFromValue(*this, arguments[6], numberValue(0.0));
        return true;
    }

    if (normalizedCommand == "getvelocity")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 4)
        {
            return false;
        }

        const std::string handle = resolveScriptString(arguments[0]);
        const auto objectIterator = m_state.objectStats.find(handle);
        const auto statValue = [&](const std::string &name) -> int32_t
        {
            if (objectIterator == m_state.objectStats.end())
            {
                return 0;
            }

            const auto valueIterator = objectIterator->second.find(name);
            return valueIterator != objectIterator->second.end() ? valueIterator->second : 0;
        };

        setScriptVariableFromValue(*this, arguments[1], numberValue(statValue("VelocityX")));
        setScriptVariableFromValue(*this, arguments[2], numberValue(statValue("VelocityY")));
        setScriptVariableFromValue(*this, arguments[3], numberValue(statValue("VelocityZ")));
        return true;
    }

    if (normalizedCommand == "setvelocity")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 4)
        {
            return false;
        }

        const std::string handle = resolveScriptString(arguments[0]);
        m_state.objectStats[handle]["VelocityX"] = scriptArgumentNumber(*this, arguments, 1);
        m_state.objectStats[handle]["VelocityY"] = scriptArgumentNumber(*this, arguments, 2);
        m_state.objectStats[handle]["VelocityZ"] = scriptArgumentNumber(*this, arguments, 3);
        return true;
    }

    if (normalizedCommand == "attack" || normalizedCommand == "rangeattack")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        const std::string handle = activeObjectHandle();
        if (handle.empty())
        {
            return false;
        }

        Mm9ScriptRuntimeAiRequest request = {};
        request.scriptSource = m_activeScriptSource;
        request.objectHandle = handle;
        request.operation = normalizedCommand;
        request.targetHandle = m_state.objectTargetHandles[handle];
        request.line = line;
        if (!arguments.empty())
        {
            request.callbackLabel = trimCopy(arguments[0]);
        }

        m_state.objectAttackStates[handle] = true;
        m_state.objectAiStates[handle] = normalizedCommand;
        if (isCallbackLabel(request.callbackLabel))
        {
            registerCallback(request.callbackLabel, line, normalizedCommand, request.targetHandle);
        }
        recordAiRequest(std::move(request));
        return true;
    }

    if (normalizedCommand == "canattack" || normalizedCommand == "canrangeattack"
        || normalizedCommand == "hasrangeattack" || normalizedCommand == "istargetinrange"
        || normalizedCommand == "isattacking")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.empty())
        {
            return false;
        }

        const std::string handle = activeObjectHandle();
        const auto attackStateIterator = m_state.objectAttackStates.find(handle);
        bool result = false;
        if (normalizedCommand == "isattacking")
        {
            result = attackStateIterator != m_state.objectAttackStates.end() && attackStateIterator->second;
        }
        else if (normalizedCommand == "hasrangeattack")
        {
            const auto objectIterator = m_state.objectStats.find(handle);
            const auto rangeIterator = objectIterator != m_state.objectStats.end()
                ? objectIterator->second.find("RangeAttack")
                : std::map<std::string, int32_t>::const_iterator();
            result = objectIterator == m_state.objectStats.end()
                || rangeIterator == objectIterator->second.end()
                || rangeIterator->second != 0;
        }
        else
        {
            const auto targetIterator = m_state.objectTargetHandles.find(handle);
            const auto removedIterator = targetIterator != m_state.objectTargetHandles.end()
                ? m_state.removedObjects.find(targetIterator->second)
                : m_state.removedObjects.end();
            result = targetIterator != m_state.objectTargetHandles.end() && !targetIterator->second.empty()
                && (removedIterator == m_state.removedObjects.end() || !removedIterator->second);
        }

        setScriptVariableFromValue(*this, arguments[0], numberValue(result ? 1.0 : 0.0));
        return true;
    }

    if (normalizedCommand == "walk" || normalizedCommand == "run")
    {
        const std::string handle = activeObjectHandle();
        if (handle.empty())
        {
            return false;
        }

        m_state.objectAiStates[handle] = normalizedCommand;
        Mm9ScriptRuntimeMovementRequest request = {};
        request.scriptSource = m_activeScriptSource;
        request.objectHandle = handle;
        request.operation = normalizedCommand;
        request.line = line;
        recordMovementRequest(std::move(request));
        return true;
    }

    if (normalizedCommand == "facedir")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 3)
        {
            return false;
        }

        const std::string handle = arguments.size() >= 4 && mm9ObjectHandleParts(resolveScriptString(arguments[0]))
            ? resolveScriptString(arguments[0])
            : activeObjectHandle();
        const size_t offset = handle == activeObjectHandle() ? 0 : 1;
        m_state.objectFaceDirs[handle] = scriptVectorFromArguments(*this, arguments, offset);
        return true;
    }

    if (normalizedCommand == "getfacedir")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 4)
        {
            return false;
        }

        const std::string handle = resolveScriptString(arguments[0]);
        const auto directionIterator = m_state.objectFaceDirs.find(handle);
        const Mm9ScriptRuntimeVec3 direction =
            directionIterator != m_state.objectFaceDirs.end() ? directionIterator->second : Mm9ScriptRuntimeVec3();
        setScriptVariableFromValue(*this, arguments[1], numberValue(direction.x));
        setScriptVariableFromValue(*this, arguments[2], numberValue(direction.y));
        setScriptVariableFromValue(*this, arguments[3], numberValue(direction.z));
        return true;
    }

    if (normalizedCommand == "getforwarddir" || normalizedCommand == "getreversedir"
        || normalizedCommand == "getrightdir" || normalizedCommand == "getleftdir")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 3)
        {
            return false;
        }

        const bool hasHandle = arguments.size() >= 4;
        const std::string handle = hasHandle ? resolveScriptString(arguments[0]) : activeObjectHandle();
        const size_t destinationOffset = hasHandle ? 1 : 0;
        const Mm9ScriptRuntimeVec3 direction =
            objectDirectionVector(m_state, handle, normalizedCommand.substr(3));

        setScriptVariableFromValue(*this, arguments[destinationOffset], numberValue(direction.x));
        setScriptVariableFromValue(*this, arguments[destinationOffset + 1], numberValue(direction.y));
        setScriptVariableFromValue(*this, arguments[destinationOffset + 2], numberValue(direction.z));
        return true;
    }

    if (normalizedCommand == "getsocketpos")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 4)
        {
            return false;
        }

        const auto positionIterator = m_state.objectPositions.find(activeObjectHandle());
        const Mm9ScriptRuntimeVec3 position =
            positionIterator != m_state.objectPositions.end() ? positionIterator->second : Mm9ScriptRuntimeVec3();
        setScriptVariableFromValue(*this, arguments[1], numberValue(position.x));
        setScriptVariableFromValue(*this, arguments[2], numberValue(position.y));
        setScriptVariableFromValue(*this, arguments[3], numberValue(position.z));
        return true;
    }

    if (normalizedCommand == "getrotation")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 5)
        {
            return false;
        }

        setScriptVariableFromValue(*this, arguments[1], numberValue(0.0));
        setScriptVariableFromValue(*this, arguments[2], numberValue(0.0));
        setScriptVariableFromValue(*this, arguments[3], numberValue(0.0));
        setScriptVariableFromValue(*this, arguments[4], numberValue(0.0));
        return true;
    }

    if (normalizedCommand == "getangletopos")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 4)
        {
            return false;
        }

        setScriptVariableFromValue(*this, arguments[3], numberValue(0.0));
        return true;
    }

    if (normalizedCommand == "rotatedir")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 4)
        {
            return false;
        }

        const double x = scriptValueNumber(evaluateScriptExpression(*this, arguments[0]));
        const double y = scriptValueNumber(evaluateScriptExpression(*this, arguments[1]));
        const double z = scriptValueNumber(evaluateScriptExpression(*this, arguments[2]));
        const double radians = scriptValueNumber(evaluateScriptExpression(*this, arguments[3])) * 3.14159265358979323846
            / 180.0;
        setScriptVariableFromValue(*this, arguments[0], numberValue((x * std::cos(radians)) - (y * std::sin(radians))));
        setScriptVariableFromValue(*this, arguments[1], numberValue((x * std::sin(radians)) + (y * std::cos(radians))));
        setScriptVariableFromValue(*this, arguments[2], numberValue(z));
        return true;
    }

    if (normalizedCommand == "vecadd" || normalizedCommand == "vecsub")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 6)
        {
            return false;
        }

        for (size_t index = 0; index < 3; ++index)
        {
            const double left = scriptValueNumber(evaluateScriptExpression(*this, arguments[index]));
            const double right = scriptValueNumber(evaluateScriptExpression(*this, arguments[index + 3]));
            const double result = normalizedCommand == "vecadd" ? left + right : left - right;
            setScriptVariableFromValue(*this, arguments[index], numberValue(result));
        }
        return true;
    }

    if (normalizedCommand == "veccross" || normalizedCommand == "getcrossproduct")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 9)
        {
            return false;
        }

        const double ax = scriptValueNumber(evaluateScriptExpression(*this, arguments[0]));
        const double ay = scriptValueNumber(evaluateScriptExpression(*this, arguments[1]));
        const double az = scriptValueNumber(evaluateScriptExpression(*this, arguments[2]));
        const double bx = scriptValueNumber(evaluateScriptExpression(*this, arguments[3]));
        const double by = scriptValueNumber(evaluateScriptExpression(*this, arguments[4]));
        const double bz = scriptValueNumber(evaluateScriptExpression(*this, arguments[5]));
        setScriptVariableFromValue(*this, arguments[6], numberValue((ay * bz) - (az * by)));
        setScriptVariableFromValue(*this, arguments[7], numberValue((az * bx) - (ax * bz)));
        setScriptVariableFromValue(*this, arguments[8], numberValue((ax * by) - (ay * bx)));
        return true;
    }

    if (normalizedCommand == "calcdist" || normalizedCommand == "vecdist")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 7)
        {
            return false;
        }

        const Mm9ScriptRuntimeVec3 first = scriptVectorFromArguments(*this, arguments, 0);
        const Mm9ScriptRuntimeVec3 second = scriptVectorFromArguments(*this, arguments, 3);
        setScriptVariableFromValue(*this, arguments[6], numberValue(scriptVectorDistance(first, second)));
        return true;
    }

    if (normalizedCommand == "vecmag")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 4)
        {
            return false;
        }

        const double x = scriptValueNumber(evaluateScriptExpression(*this, arguments[0]));
        const double y = scriptValueNumber(evaluateScriptExpression(*this, arguments[1]));
        const double z = scriptValueNumber(evaluateScriptExpression(*this, arguments[2]));
        setScriptVariableFromValue(*this, arguments[3], numberValue(std::sqrt((x * x) + (y * y) + (z * z))));
        return true;
    }

    if (normalizedCommand == "vecangle")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 7)
        {
            return false;
        }

        const Mm9ScriptRuntimeVec3 first = scriptVectorFromArguments(*this, arguments, 0);
        const Mm9ScriptRuntimeVec3 second = scriptVectorFromArguments(*this, arguments, 3);
        const double firstLength = std::sqrt((first.x * first.x) + (first.y * first.y) + (first.z * first.z));
        const double secondLength = std::sqrt((second.x * second.x) + (second.y * second.y) + (second.z * second.z));
        double angle = 0.0;
        if (firstLength != 0.0 && secondLength != 0.0)
        {
            const double dot = (first.x * second.x) + (first.y * second.y) + (first.z * second.z);
            const double cosine = std::max(-1.0, std::min(1.0, dot / (firstLength * secondLength)));
            angle = std::acos(cosine) * 180.0 / std::acos(-1.0);
        }
        setScriptVariableFromValue(*this, arguments[6], numberValue(angle));
        return true;
    }

    if (normalizedCommand == "vecscale")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 4)
        {
            return false;
        }

        const double scale = scriptValueNumber(evaluateScriptExpression(*this, arguments[3]));
        setScriptVariableFromValue(
            *this,
            arguments[0],
            numberValue(scriptValueNumber(evaluateScriptExpression(*this, arguments[0])) * scale));
        setScriptVariableFromValue(
            *this,
            arguments[1],
            numberValue(scriptValueNumber(evaluateScriptExpression(*this, arguments[1])) * scale));
        setScriptVariableFromValue(
            *this,
            arguments[2],
            numberValue(scriptValueNumber(evaluateScriptExpression(*this, arguments[2])) * scale));
        return true;
    }

    if (normalizedCommand == "vecnorm" || normalizedCommand == "normalizevector")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 3)
        {
            return false;
        }

        const double x = scriptValueNumber(evaluateScriptExpression(*this, arguments[0]));
        const double y = scriptValueNumber(evaluateScriptExpression(*this, arguments[1]));
        const double z = scriptValueNumber(evaluateScriptExpression(*this, arguments[2]));
        const double length = std::sqrt((x * x) + (y * y) + (z * z));
        if (length == 0.0)
        {
            setScriptVariableFromValue(*this, arguments[0], numberValue(0.0));
            setScriptVariableFromValue(*this, arguments[1], numberValue(0.0));
            setScriptVariableFromValue(*this, arguments[2], numberValue(0.0));
            return true;
        }

        setScriptVariableFromValue(*this, arguments[0], numberValue(x / length));
        setScriptVariableFromValue(*this, arguments[1], numberValue(y / length));
        setScriptVariableFromValue(*this, arguments[2], numberValue(z / length));
        return true;
    }

    if (normalizedCommand == "removetrigger")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.empty())
        {
            return false;
        }

        removeTrigger(arguments[0]);
        return true;
    }

    if (normalizedCommand == "getmyhandle")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.empty())
        {
            return false;
        }

        setObjectHandleVar(arguments[0], activeObjectHandle());
        return true;
    }

    if (normalizedCommand == "getplayerhandle")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.empty())
        {
            return false;
        }

        setObjectHandleVar(arguments[0], "mm9:player");
        return true;
    }

    if (normalizedCommand == "getplayerid" || normalizedCommand == "getplayernbr")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 2)
        {
            return false;
        }

        setScriptVariableFromValue(*this, arguments[1], numberValue(0.0));
        return true;
    }

    if (normalizedCommand == "getobjecthandle")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 2)
        {
            return false;
        }

        const std::string objectName = resolveScriptString(arguments[0]);
        setObjectHandleVar(arguments[1], objectHandleForName(objectName));
        return true;
    }

    if (normalizedCommand == "getclassname")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 2)
        {
            return false;
        }

        const Mm9GeneratedObjectDialogueBinding *pBinding = objectBindingForHandle(resolveScriptString(arguments[0]));
        setScriptVariableFromString(*this, arguments[1], pBinding != nullptr ? pBinding->objectClass : "");
        return true;
    }

    if (normalizedCommand == "getobjectname")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 2)
        {
            return false;
        }

        const Mm9GeneratedObjectDialogueBinding *pBinding = objectBindingForHandle(resolveScriptString(arguments[0]));
        setScriptVariableFromString(*this, arguments[1], pBinding != nullptr ? pBinding->objectName : "");
        return true;
    }

    if (normalizedCommand == "isplayer")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 2)
        {
            return false;
        }

        const std::string handle = resolveScriptString(arguments[0]);
        setScriptVariableFromValue(*this, arguments[1], numberValue(handle == "mm9:player" ? 1.0 : 0.0));
        return true;
    }

    if (normalizedCommand == "isclass")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 3)
        {
            return false;
        }

        const Mm9GeneratedObjectDialogueBinding *pBinding = objectBindingForHandle(resolveScriptString(arguments[0]));
        const std::string expected = lowerCopy(unquoteScriptString(arguments[1]));
        const bool matches = pBinding != nullptr
            && (lowerCopy(pBinding->objectClass) == expected || lowerCopy(pBinding->objectName) == expected);
        setScriptVariableFromValue(*this, arguments[2], numberValue(matches ? 1.0 : 0.0));
        return true;
    }

    if (normalizedCommand == "target")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.empty())
        {
            return false;
        }

        const std::string handle = activeObjectHandle();
        if (!handle.empty())
        {
            const std::string loweredTarget = lowerCopy(trimCopy(arguments[0]));
            const std::string targetHandle = loweredTarget == "null" || loweredTarget == "nil" || loweredTarget == "0"
                ? std::string()
                : resolveScriptString(arguments[0]);
            setObjectTargetHandle(handle, targetHandle);
        }
        return true;
    }

    if (normalizedCommand == "gettarget")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.empty())
        {
            return false;
        }

        const auto iterator = m_state.objectTargetHandles.find(activeObjectHandle());
        setObjectHandleVar(arguments[0], iterator != m_state.objectTargetHandles.end() ? iterator->second : "");
        return true;
    }

    if (normalizedCommand == "getobjecttarget")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 2)
        {
            return false;
        }

        const std::string handle = resolveScriptString(arguments[0]);
        const auto iterator = m_state.objectTargetHandles.find(handle);
        setObjectHandleVar(arguments[1], iterator != m_state.objectTargetHandles.end() ? iterator->second : "");
        return true;
    }

    if (normalizedCommand == "getobjects")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 5)
        {
            return false;
        }

        const std::string query = lowerCopy(unquoteScriptString(arguments[0]));
        const int32_t maxObjects = std::max(0, scriptArgumentNumber(*this, arguments, 2));
        const std::string arrayName = trimCopy(arguments[3]);
        int32_t count = 0;
        for (const Mm9GeneratedObjectDialogueBinding &binding : m_package.objectBindings)
        {
            if (count >= maxObjects)
            {
                break;
            }
            if (lowerCopy(binding.objectName) != query && lowerCopy(binding.objectClass) != query)
            {
                continue;
            }

            m_state.scriptStrArrays[arrayName][count] =
                "mm9:" + binding.mapId + ":object:" + std::to_string(binding.objectIndex);
            ++count;
        }

        setScriptVariableFromValue(*this, arguments[4], numberValue(count));
        return true;
    }

    if (normalizedCommand == "getliquidcontainer" || normalizedCommand == "getcontainer")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 2)
        {
            return false;
        }

        const std::string sourceHandle = resolveScriptString(arguments[0]);
        const size_t destinationIndex = normalizedCommand == "getcontainer" && arguments.size() >= 3 ? 2 : 1;
        setObjectHandleVar(arguments[destinationIndex], sourceHandle);
        return true;
    }

    if (normalizedCommand == "setstat" || normalizedCommand == "getstat")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 3)
        {
            return false;
        }

        const std::string handle = resolveScriptString(arguments[0]);
        const std::string statName = trimCopy(arguments[1]);
        if (normalizedCommand == "setstat")
        {
            m_state.objectStats[handle][statName] =
                static_cast<int32_t>(scriptValueNumber(evaluateScriptExpression(*this, arguments[2])));
        }
        else
        {
            const auto objectIterator = m_state.objectStats.find(handle);
            const auto statIterator = objectIterator != m_state.objectStats.end()
                ? objectIterator->second.find(statName)
                : std::map<std::string, int32_t>::const_iterator();
            const int32_t value = objectIterator != m_state.objectStats.end()
                    && statIterator != objectIterator->second.end()
                ? statIterator->second
                : 0;
            setScriptVariableFromValue(*this, arguments[2], numberValue(value));
        }
        return true;
    }

    if (normalizedCommand == "getstatstr")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 3)
        {
            return false;
        }

        const std::string handle = resolveScriptString(arguments[0]);
        const std::string statName = trimCopy(arguments[1]);
        std::string value;
        const auto objectIterator = m_state.objectStringProperties.find(handle);
        if (objectIterator != m_state.objectStringProperties.end())
        {
            const auto valueIterator = objectIterator->second.find(statName);
            if (valueIterator != objectIterator->second.end())
            {
                value = valueIterator->second;
            }
        }
        if (value.empty() && lowerCopy(statName) == "scriptname")
        {
            const auto scriptIterator = m_state.objectScriptOverrides.find(handle);
            value = scriptIterator != m_state.objectScriptOverrides.end()
                ? scriptIterator->second
                : m_activeScriptSource;
        }

        setScriptVariableFromString(*this, arguments[2], value);
        return true;
    }

    if (normalizedCommand == "setpropstring")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 2)
        {
            return false;
        }

        m_state.objectStringProperties[activeObjectHandle()][trimCopy(arguments[0])] =
            resolveScriptString(arguments[1]);
        return true;
    }

    if (normalizedCommand == "setflag" || normalizedCommand == "clearflag")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 2)
        {
            return false;
        }

        m_state.objectFlags[resolveScriptString(arguments[0])][normalizedObjectFlagName(arguments[1])] =
            normalizedCommand == "setflag" ? 1 : 0;
        return true;
    }

    if (normalizedCommand == "removeobject")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        const std::string handle = arguments.empty() ? activeObjectHandle() : resolveScriptString(arguments[0]);
        if (handle.empty())
        {
            return false;
        }

        removeRuntimeObject(handle);
        return true;
    }

    if (normalizedCommand == "hasgold")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 2)
        {
            return false;
        }

        const int32_t amount = scriptArgumentNumber(*this, arguments, 0);
        const bool hasGold = m_dialogueRuntime.party().gold() >= amount;
        setScriptVariableFromValue(*this, arguments[1], numberValue(hasGold ? 1.0 : 0.0));
        recordPartyAccess("hasGold", 0, amount, hasGold, line);
        return true;
    }

    if (normalizedCommand == "takegold")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.empty())
        {
            return false;
        }

        const int32_t amount = scriptArgumentNumber(*this, arguments, 0);
        const bool tookGold = m_dialogueRuntime.party().gold() >= amount;
        if (tookGold)
        {
            m_dialogueRuntime.party().addGold(-amount);
        }
        recordPartyAccess("takeGold", 0, amount, tookGold, line);
        return true;
    }

    if (normalizedCommand == "die")
    {
        return killObject(activeObjectHandle());
    }

    if (normalizedCommand == "damage")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 3)
        {
            return false;
        }

        return damageObject(resolveScriptString(arguments[0]), {arguments.begin() + 1, arguments.end()}, line);
    }

    if (normalizedCommand == "setmodelfilenames")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.empty())
        {
            return false;
        }

        setObjectModelFilenames(activeObjectHandle(), arguments);
        return true;
    }

    if (normalizedCommand == "attachprop")
    {
        return requestAttachment(activeObjectHandle(), normalizedCommand, splitScriptArguments(trimmedArguments), line);
    }

    if (normalizedCommand == "detachprop")
    {
        return requestAttachment(activeObjectHandle(), normalizedCommand, splitScriptArguments(trimmedArguments), line);
    }

    if (normalizedCommand == "createobjectlink")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.empty())
        {
            return false;
        }

        createObjectLink(activeObjectHandle(), resolveScriptString(arguments[0]));
        return true;
    }

    if (normalizedCommand == "breakobjectlink")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.empty())
        {
            return false;
        }

        breakObjectLink(activeObjectHandle(), resolveScriptString(arguments[0]));
        return true;
    }

    if (normalizedCommand == "spawn" || normalizedCommand == "spawn2")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 5)
        {
            return false;
        }

        const std::vector<std::string> spawnArguments(arguments.begin() + 1, arguments.end());
        return !spawnObject(arguments[0], spawnArguments, normalizedCommand == "spawn2", line).empty();
    }

    if (normalizedCommand == "runscript")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.empty())
        {
            return false;
        }

        m_state.objectScriptOverrides[activeObjectHandle()] = resolveScriptString(arguments[0]);
        return true;
    }

    if (normalizedCommand == "exitscript")
    {
        Mm9ScriptRuntimeControlRequest request = {};
        request.scriptSource = m_activeScriptSource;
        request.operation = normalizedCommand;
        request.line = line;
        recordControlRequest(std::move(request));
        return true;
    }

    if (normalizedCommand == "givepromo")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 2)
        {
            return false;
        }

        Mm9ScriptRuntimePromotionRequest request = {};
        request.scriptSource = m_activeScriptSource;
        request.promotionName = unquoteScriptString(arguments[0]);
        request.characterToken = unquoteScriptString(arguments[1]);
        request.line = line;
        recordPromotionRequest(std::move(request));
        recordPartyAccess("givePromo", 0, 1, true, line);
        return true;
    }

    if (normalizedCommand == "giveattribute")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.size() < 3)
        {
            return false;
        }

        Mm9ScriptRuntimePartyCommandRequest request = {};
        request.scriptSource = m_activeScriptSource;
        request.operation = normalizedCommand;
        request.arguments = arguments;
        request.line = line;
        recordPartyCommandRequest(std::move(request));

        const int32_t attributeId = mm9AttributeIdFromArgument(*this, arguments[0]);
        const int32_t amount = scriptArgumentNumber(*this, arguments, 1);
        const bool applyToAll = scriptArgumentBool(*this, arguments, 2, false);
        const double durationSeconds = arguments.size() >= 4
            ? std::max(0.0, scriptValueNumber(evaluateScriptExpression(*this, arguments[3])))
            : 0.0;
        const bool permanent = durationSeconds <= 0.0;
        Party &party = m_dialogueRuntime.party();
        const size_t firstMemberIndex = applyToAll ? 0 : party.activeMemberIndex();
        const size_t lastMemberIndex = applyToAll
            ? party.memberCount()
            : std::min(firstMemberIndex + 1, party.memberCount());
        for (size_t memberIndex = firstMemberIndex; memberIndex < lastMemberIndex; ++memberIndex)
        {
            Character *pMember = party.member(memberIndex);
            if (pMember == nullptr)
            {
                continue;
            }

            applyMm9CharacterAttributeBonus(*pMember, attributeId, amount, permanent);
            if (!permanent)
            {
                Mm9ScriptRuntimeAttributeEffect effect = {};
                effect.memberIndex = static_cast<uint32_t>(memberIndex);
                effect.attributeId = attributeId;
                effect.amount = amount;
                effect.expiresAtSeconds = m_state.scriptTimeSeconds + durationSeconds;
                m_state.attributeEffects.push_back(effect);
            }
        }

        recordPartyAccess(
            "giveAttribute",
            static_cast<uint32_t>(std::max(0, attributeId)),
            amount,
            true,
            line);
        return true;
    }

    if (normalizedCommand == "ondamage" || normalizedCommand == "onpoststartworld"
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
        || normalizedCommand == "onworldswitch"
        || normalizedCommand == "oncachefiles" || normalizedCommand == "onenrage"
        || normalizedCommand == "onenragedone" || normalizedCommand == "onfear"
        || normalizedCommand == "onfeardone" || normalizedCommand == "onplayerinterrupt"
        || normalizedCommand == "ontargethit")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.empty())
        {
            return true;
        }

        registerCallback(arguments[0], line, trimCopy(command));
        return true;
    }

    if (normalizedCommand == "ontargetbeyonddist" || normalizedCommand == "ontargetwithindist"
        || normalizedCommand == "addmodelkey"
        || normalizedCommand == "setcallback")
    {
        const std::vector<std::string> arguments = splitScriptArguments(trimmedArguments);
        if (arguments.empty())
        {
            return true;
        }
        if (arguments.size() < 2)
        {
            registerCallback("", line, trimCopy(command), arguments[0]);
            return true;
        }

        registerCallback(arguments[1], line, trimCopy(command), arguments[0]);
        return true;
    }

    return false;
}

const Mm9ScriptRuntimeState &Mm9ScriptRuntime::state() const
{
    return m_state;
}

void Mm9ScriptRuntime::restoreState(const Mm9ScriptRuntimeState &state)
{
    m_state = state;
    m_audioRequests = m_state.audioRequests;
    m_registeredCallbacks = m_state.registeredCallbacks;
    m_movementRequests = m_state.movementRequests;
    m_spawnRequests = m_state.spawnRequests;
    m_aiRequests = m_state.aiRequests;
    m_animationRequests = m_state.animationRequests;
    m_clientFxRequests = m_state.clientFxRequests;
    m_presentationRequests = m_state.presentationRequests;
    m_attachmentRequests = m_state.attachmentRequests;
    m_promotionRequests = m_state.promotionRequests;
    m_partyCommandRequests = m_state.partyCommandRequests;
    m_controlRequests = m_state.controlRequests;
    m_damageRequests = m_state.damageRequests;
    m_dialogueRuntime.bindScriptRuntimeState(&m_state);
}

void Mm9ScriptRuntime::recordUnimplementedCommand(
    const std::string &command,
    const std::string &argumentsText,
    size_t line,
    const std::string &rawLine)
{
    Mm9ScriptRuntimeCommand runtimeCommand = {};
    runtimeCommand.scriptSource = m_activeScriptSource;
    runtimeCommand.line = line;
    runtimeCommand.command = command;
    runtimeCommand.argumentsText = argumentsText;
    runtimeCommand.rawLine = rawLine;
    m_unimplementedCommands.push_back(std::move(runtimeCommand));
}

void Mm9ScriptRuntime::registerCallback(
    const std::string &label,
    size_t line,
    const std::string &kind,
    const std::string &selector)
{
    if (!isCallbackLabel(label))
    {
        return;
    }

    Mm9ScriptRuntimeCallback callback = {};
    callback.scriptSource = m_activeScriptSource;
    callback.mapId = m_dialogueRuntime.owner().mapId;
    callback.objectIndex = m_dialogueRuntime.owner().objectIndex;
    callback.kind = kind;
    callback.selector = selector;
    callback.label = label;
    callback.line = line;
    m_state.registeredCallbacks.push_back(callback);
    m_registeredCallbacks.push_back(std::move(callback));
}

void Mm9ScriptRuntime::removeCallbackRegistrations(const std::string &kind, const std::string &selector)
{
    const std::string loweredKind = lowerCopy(trimCopy(kind));
    const std::string loweredSelector = lowerCopy(trimCopy(selector));
    const Mm9DialogueOwnerContext &owner = m_dialogueRuntime.owner();

    const auto shouldRemove = [&](const Mm9ScriptRuntimeCallback &callback)
    {
        if (callback.mapId != owner.mapId || callback.objectIndex != owner.objectIndex)
        {
            return false;
        }
        if (!loweredKind.empty() && lowerCopy(trimCopy(callback.kind)) != loweredKind)
        {
            return false;
        }
        if (!loweredSelector.empty() && lowerCopy(trimCopy(callback.selector)) != loweredSelector)
        {
            return false;
        }

        return true;
    };

    m_state.registeredCallbacks.erase(
        std::remove_if(m_state.registeredCallbacks.begin(), m_state.registeredCallbacks.end(), shouldRemove),
        m_state.registeredCallbacks.end());
    m_registeredCallbacks = m_state.registeredCallbacks;
}

void Mm9ScriptRuntime::recordKeyAccess(const std::string &operation, int32_t rawKeyId, bool result, size_t line)
{
    Mm9ScriptRuntimeKeyAccess access = {};
    access.scriptSource = m_activeScriptSource;
    access.operation = operation;
    access.rawKeyId = rawKeyId;
    access.qbitId = mm9KeyQbitIdForRawKey(rawKeyId);
    access.result = result;
    access.line = line;
    m_keyAccesses.push_back(std::move(access));
}

void Mm9ScriptRuntime::recordPartyAccess(
    const std::string &operation,
    uint32_t id,
    int32_t amount,
    bool result,
    size_t line)
{
    Mm9ScriptRuntimePartyAccess access = {};
    access.scriptSource = m_activeScriptSource;
    access.operation = operation;
    access.id = id;
    access.amount = amount;
    access.result = result;
    access.line = line;
    m_partyAccesses.push_back(std::move(access));
}

std::string Mm9ScriptRuntime::objectHandleForRudeId(int32_t rudeId) const
{
    if (rudeId <= 0)
    {
        return {};
    }

    const std::string &mapId = m_dialogueRuntime.owner().mapId;
    for (const Mm9GeneratedObjectDialogueBinding &binding : m_package.objectBindings)
    {
        if (binding.rudeId && *binding.rudeId == rudeId && (mapId.empty() || binding.mapId == mapId))
        {
            return "mm9:" + binding.mapId + ":object:" + std::to_string(binding.objectIndex);
        }
    }

    return {};
}

void Mm9ScriptRuntime::registerTrigger(const std::string &triggerName, const std::string &label, size_t line)
{
    if (triggerName.empty() || label.empty())
    {
        return;
    }

    const Mm9DialogueOwnerContext &owner = m_dialogueRuntime.owner();
    const auto existing = std::find_if(
        m_state.triggers.begin(),
        m_state.triggers.end(),
        [&](const Mm9ScriptRuntimeTriggerRegistration &trigger)
        {
            return trigger.mapId == owner.mapId && trigger.objectIndex == owner.objectIndex
                && lowerCopy(trigger.triggerName) == lowerCopy(triggerName);
        });

    Mm9ScriptRuntimeTriggerRegistration trigger = {};
    trigger.scriptSource = m_activeScriptSource;
    trigger.mapId = owner.mapId;
    trigger.objectIndex = owner.objectIndex;
    trigger.triggerName = triggerName;
    trigger.label = label;
    trigger.line = line;
    if (existing != m_state.triggers.end())
    {
        *existing = std::move(trigger);
    }
    else
    {
        m_state.triggers.push_back(std::move(trigger));
    }
}

void Mm9ScriptRuntime::removeTrigger(const std::string &triggerName)
{
    const Mm9DialogueOwnerContext &owner = m_dialogueRuntime.owner();
    const std::string loweredTriggerName = lowerCopy(trimCopy(triggerName));
    m_state.triggers.erase(
        std::remove_if(
            m_state.triggers.begin(),
            m_state.triggers.end(),
            [&](const Mm9ScriptRuntimeTriggerRegistration &trigger)
            {
                return trigger.mapId == owner.mapId && trigger.objectIndex == owner.objectIndex
                    && lowerCopy(trigger.triggerName) == loweredTriggerName;
            }),
        m_state.triggers.end());
}

void Mm9ScriptRuntime::dispatchTrigger(const std::string &targetHandle, const std::string &message, size_t line)
{
    const std::string resolvedTargetHandle = triggerTargetHandleFromScriptToken(*this, targetHandle);
    if (resolvedTargetHandle.empty() || message.empty())
    {
        return;
    }

    Mm9ScriptRuntimeTriggerDispatch dispatch = {};
    dispatch.scriptSource = m_activeScriptSource;
    dispatch.mapId = m_dialogueRuntime.owner().mapId;
    dispatch.objectIndex = m_dialogueRuntime.owner().objectIndex;
    dispatch.targetHandle = resolvedTargetHandle;
    dispatch.message = message;
    dispatch.line = line;
    m_state.triggerDispatches.push_back(std::move(dispatch));

    if (m_triggerDispatchDepth >= 16)
    {
        return;
    }

    const Mm9GeneratedObjectDialogueBinding *pTargetBinding = objectBindingForHandle(resolvedTargetHandle);
    if (pTargetBinding == nullptr)
    {
        return;
    }

    const std::string loweredMessage = lowerCopy(trimCopy(message));
    const auto triggerIterator = std::find_if(
        m_state.triggers.begin(),
        m_state.triggers.end(),
        [&](const Mm9ScriptRuntimeTriggerRegistration &trigger)
        {
            return trigger.mapId == pTargetBinding->mapId && trigger.objectIndex == pTargetBinding->objectIndex
                && lowerCopy(trigger.triggerName) == loweredMessage;
        });
    if (triggerIterator == m_state.triggers.end() || triggerIterator->label.empty())
    {
        return;
    }

    Mm9DialogueOwnerContext targetOwner = {};
    std::string ownerError;
    if (!m_dialogueRuntime.ownerContextForObject(
        pTargetBinding->mapId,
        pTargetBinding->objectIndex,
        targetOwner,
        &ownerError))
    {
        return;
    }

    const auto overrideIterator = m_state.objectScriptOverrides.find(resolvedTargetHandle);
    const std::string scriptOverride = overrideIterator != m_state.objectScriptOverrides.end()
        ? overrideIterator->second
        : "";
    const std::string scriptSource = !scriptOverride.empty()
        ? scriptOverride
        : (!triggerIterator->scriptSource.empty() ? triggerIterator->scriptSource : pTargetBinding->scriptName);
    if (scriptSource.empty())
    {
        return;
    }

    const Mm9DialogueOwnerContext previousOwner = m_dialogueRuntime.owner();
    m_dialogueRuntime.setOwnerContext(std::move(targetOwner));
    ++m_triggerDispatchDepth;
    std::optional<std::string> scriptError;
    runLabel(scriptSource, triggerIterator->label, scriptError);
    --m_triggerDispatchDepth;
    m_dialogueRuntime.setOwnerContext(previousOwner);
}

void Mm9ScriptRuntime::dispatchTriggerFromObject(
    const Mm9DialogueOwnerContext &owner,
    const std::string &scriptSource,
    const std::string &targetHandle,
    const std::string &message,
    size_t line)
{
    const Mm9DialogueOwnerContext previousOwner = m_dialogueRuntime.owner();
    const std::string previousActiveScriptSource = m_activeScriptSource;
    m_dialogueRuntime.setOwnerContext(owner);
    m_activeScriptSource = scriptSource;
    dispatchTrigger(targetHandle, message, line);
    m_activeScriptSource = previousActiveScriptSource;
    m_dialogueRuntime.setOwnerContext(previousOwner);
}

bool Mm9ScriptRuntime::setObjectIdle(const std::string &objectHandle)
{
    const std::string handle = objectHandle.empty() ? activeObjectHandle() : objectHandle;
    if (handle.empty())
    {
        return false;
    }

    m_state.objectAiStates[handle] = "idle";
    m_state.objectAttackStates[handle] = false;
    return true;
}

bool Mm9ScriptRuntime::setObjectStuck(const std::string &objectHandle)
{
    const std::string handle = objectHandle.empty() ? activeObjectHandle() : objectHandle;
    if (handle.empty())
    {
        return false;
    }

    m_state.objectAiStates[handle] = "stuck";
    return true;
}

void Mm9ScriptRuntime::addObjectRelation(
    const std::string &objectHandle,
    const std::string &operation,
    const std::string &classOrName)
{
    const std::string handle = objectHandle.empty() ? activeObjectHandle() : objectHandle;
    const std::string token = unquoteScriptString(classOrName);
    if (handle.empty() || token.empty())
    {
        return;
    }

    if (lowerCopy(trimCopy(operation)) == "addenemy")
    {
        m_state.objectEnemies[handle].push_back(token);
    }
    else
    {
        m_state.objectFriends[handle].push_back(token);
    }
}

void Mm9ScriptRuntime::removeObjectRelation(
    const std::string &objectHandle,
    const std::string &operation,
    const std::string &classOrName)
{
    const std::string handle = objectHandle.empty() ? activeObjectHandle() : objectHandle;
    if (handle.empty())
    {
        return;
    }

    std::vector<std::string> &relations = lowerCopy(trimCopy(operation)) == "removeenemy"
        ? m_state.objectEnemies[handle]
        : m_state.objectFriends[handle];
    const std::string loweredRelation = lowerCopy(unquoteScriptString(classOrName));
    relations.erase(
        std::remove_if(
            relations.begin(),
            relations.end(),
            [&](const std::string &relation)
            {
                return lowerCopy(relation) == loweredRelation;
            }),
        relations.end());
}

bool Mm9ScriptRuntime::objectIsFriend(const std::string &objectHandle, const std::string &targetHandle) const
{
    const Mm9GeneratedObjectDialogueBinding *pBinding = objectBindingForHandle(targetHandle);
    const auto friendsIterator = m_state.objectFriends.find(objectHandle);
    if (friendsIterator == m_state.objectFriends.end())
    {
        return false;
    }

    for (const std::string &friendToken : friendsIterator->second)
    {
        const std::string loweredFriend = lowerCopy(friendToken);
        if (loweredFriend == lowerCopy(targetHandle))
        {
            return true;
        }
        if (pBinding != nullptr && loweredFriend == lowerCopy(pBinding->objectName))
        {
            return true;
        }
        if (pBinding != nullptr && loweredFriend == lowerCopy(pBinding->objectClass))
        {
            return true;
        }
    }

    return false;
}

double Mm9ScriptRuntime::objectDistanceTo(const std::string &sourceHandle, const std::string &targetHandle) const
{
    const auto sourcePositionIterator = m_state.objectPositions.find(sourceHandle);
    const auto targetPositionIterator = m_state.objectPositions.find(targetHandle);
    const Mm9ScriptRuntimeVec3 sourcePosition = sourcePositionIterator != m_state.objectPositions.end()
        ? sourcePositionIterator->second
        : Mm9ScriptRuntimeVec3();
    const Mm9ScriptRuntimeVec3 targetPosition = targetPositionIterator != m_state.objectPositions.end()
        ? targetPositionIterator->second
        : Mm9ScriptRuntimeVec3();
    return scriptVectorDistance(sourcePosition, targetPosition);
}

bool Mm9ScriptRuntime::objectAiQuery(const std::string &objectHandle, const std::string &operation) const
{
    const std::string normalizedOperation = lowerCopy(trimCopy(operation));
    const auto attackStateIterator = m_state.objectAttackStates.find(objectHandle);
    if (normalizedOperation == "isattacking")
    {
        return attackStateIterator != m_state.objectAttackStates.end() && attackStateIterator->second;
    }
    if (normalizedOperation == "hasrangeattack")
    {
        const auto objectIterator = m_state.objectStats.find(objectHandle);
        const auto rangeIterator = objectIterator != m_state.objectStats.end()
            ? objectIterator->second.find("RangeAttack")
            : std::map<std::string, int32_t>::const_iterator();
        return objectIterator == m_state.objectStats.end()
            || rangeIterator == objectIterator->second.end()
            || rangeIterator->second != 0;
    }
    if (normalizedOperation == "canattack" || normalizedOperation == "canrangeattack"
        || normalizedOperation == "istargetinrange")
    {
        const auto targetIterator = m_state.objectTargetHandles.find(objectHandle);
        const auto removedIterator = targetIterator != m_state.objectTargetHandles.end()
            ? m_state.removedObjects.find(targetIterator->second)
            : m_state.removedObjects.end();
        return targetIterator != m_state.objectTargetHandles.end() && !targetIterator->second.empty()
            && (removedIterator == m_state.removedObjects.end() || !removedIterator->second);
    }

    return false;
}

bool Mm9ScriptRuntime::requestAi(
    const std::string &objectHandle,
    const std::string &operation,
    const std::vector<std::string> &arguments,
    size_t line)
{
    const std::string handle = objectHandle.empty() ? activeObjectHandle() : objectHandle;
    const std::string normalizedOperation = lowerCopy(trimCopy(operation));
    const std::vector<std::string> normalizedArguments = normalizedServiceArguments(arguments);
    if (handle.empty())
    {
        return false;
    }

    if (normalizedOperation == "setidle")
    {
        return setObjectIdle(handle);
    }
    if (normalizedOperation == "addfriend" || normalizedOperation == "addenemy")
    {
        if (normalizedArguments.empty())
        {
            return false;
        }
        addObjectRelation(handle, normalizedOperation, normalizedArguments[0]);
        return true;
    }
    if (normalizedOperation == "removefriend" || normalizedOperation == "removeenemy")
    {
        if (normalizedArguments.empty())
        {
            return false;
        }
        removeObjectRelation(handle, normalizedOperation, normalizedArguments[0]);
        return true;
    }
    if (normalizedOperation == "sendalert")
    {
        if (normalizedArguments.empty())
        {
            return false;
        }

        std::string targetHandle = resolveScriptString(normalizedArguments[0]);
        const std::string loweredTarget = lowerCopy(trimCopy(targetHandle));
        if (loweredTarget == "null" || loweredTarget == "nil" || loweredTarget == "0")
        {
            targetHandle.clear();
        }

        Mm9ScriptRuntimeAiRequest request = {};
        request.scriptSource = m_activeScriptSource;
        request.objectHandle = handle;
        request.operation = normalizedOperation;
        request.targetHandle = targetHandle;
        request.line = line;
        recordAiRequest(std::move(request));
        return true;
    }
    if (normalizedOperation == "help" || normalizedOperation == "estimaterangeattackhit"
        || normalizedOperation == "land")
    {
        Mm9ScriptRuntimeAiRequest request = {};
        request.scriptSource = m_activeScriptSource;
        request.objectHandle = handle;
        request.operation = normalizedOperation;
        if (!normalizedArguments.empty())
        {
            request.targetHandle = resolveScriptString(normalizedArguments[0]);
        }
        request.line = line;
        recordAiRequest(std::move(request));
        return true;
    }
    if (normalizedOperation == "attack" || normalizedOperation == "rangeattack")
    {
        Mm9ScriptRuntimeAiRequest request = {};
        request.scriptSource = m_activeScriptSource;
        request.objectHandle = handle;
        request.operation = normalizedOperation;
        request.targetHandle = m_state.objectTargetHandles[handle];
        request.line = line;
        if (!normalizedArguments.empty())
        {
            request.callbackLabel = trimCopy(normalizedArguments[0]);
        }

        m_state.objectAttackStates[handle] = true;
        m_state.objectAiStates[handle] = normalizedOperation;
        if (isCallbackLabel(request.callbackLabel))
        {
            registerCallback(request.callbackLabel, line, normalizedOperation, request.targetHandle);
        }
        recordAiRequest(std::move(request));
        return true;
    }

    return false;
}

std::string Mm9ScriptRuntime::spawnObject(
    const std::string &handleVar,
    const std::vector<std::string> &arguments,
    bool extended,
    size_t line)
{
    const std::vector<std::string> normalizedArguments = normalizedServiceArguments(arguments);
    if (normalizedArguments.size() < 4)
    {
        return {};
    }

    Mm9ScriptRuntimeSpawnRequest request = {};
    request.scriptSource = m_activeScriptSource;
    request.handleVar = trimCopy(handleVar);
    request.spawnedHandle = "mm9:spawn:" + std::to_string(m_state.nextSpawnHandleId++);
    request.position = scriptVectorFromArguments(*this, normalizedArguments, 0);
    if (extended)
    {
        for (size_t index = 3; index < normalizedArguments.size(); ++index)
        {
            if (!request.parameter.empty())
            {
                request.parameter += ", ";
            }
            request.parameter += normalizedArguments[index];
        }
    }
    else
    {
        request.parameter = resolveScriptString(normalizedArguments[3]);
    }
    request.line = line;

    const std::string spawnedHandle = request.spawnedHandle;
    if (!request.handleVar.empty())
    {
        setObjectHandleVar(request.handleVar, spawnedHandle);
    }
    m_state.objectPositions[spawnedHandle] = request.position;
    recordSpawnRequest(std::move(request));
    return spawnedHandle;
}

void Mm9ScriptRuntime::setObjectModelFilenames(
    const std::string &objectHandle,
    const std::vector<std::string> &filenames)
{
    const std::string handle = objectHandle.empty() ? activeObjectHandle() : objectHandle;
    if (handle.empty() || filenames.empty())
    {
        return;
    }

    m_state.objectModelFilenames[handle] = filenames;
}

bool Mm9ScriptRuntime::requestAttachment(
    const std::string &objectHandle,
    const std::string &operation,
    const std::vector<std::string> &arguments,
    size_t line)
{
    const std::string handle = objectHandle.empty() ? activeObjectHandle() : objectHandle;
    const std::string normalizedOperation = lowerCopy(trimCopy(operation));
    const std::vector<std::string> normalizedArguments = normalizedServiceArguments(arguments);
    if (handle.empty())
    {
        return false;
    }

    if (normalizedOperation == "attachprop")
    {
        if (normalizedArguments.size() < 4)
        {
            return false;
        }

        Mm9ScriptRuntimeAttachmentRequest request = {};
        request.scriptSource = m_activeScriptSource;
        request.objectHandle = handle;
        request.operation = normalizedOperation;
        request.modelName = resolveScriptString(normalizedArguments[0]);
        request.textureName = resolveScriptString(normalizedArguments[1]);
        request.socketName = resolveScriptString(normalizedArguments[2]);
        request.attachedHandle = resolveScriptString(normalizedArguments[3]);
        request.line = line;
        recordAttachmentRequest(std::move(request));
        return true;
    }

    if (normalizedOperation == "detachprop")
    {
        if (normalizedArguments.empty())
        {
            return false;
        }

        Mm9ScriptRuntimeAttachmentRequest request = {};
        request.scriptSource = m_activeScriptSource;
        request.objectHandle = handle;
        request.operation = normalizedOperation;
        request.attachedHandle = resolveScriptString(normalizedArguments[0]);
        if (normalizedArguments.size() >= 2)
        {
            request.textureName = scriptArgumentBool(*this, normalizedArguments, 1) ? "true" : "false";
        }
        request.line = line;
        recordAttachmentRequest(std::move(request));
        return true;
    }

    return false;
}

bool Mm9ScriptRuntime::requestAnimation(
    const std::string &objectHandle,
    const std::string &operation,
    const std::vector<std::string> &arguments,
    size_t line)
{
    const std::string normalizedOperation = lowerCopy(trimCopy(operation));
    std::vector<std::string> normalizedArguments = arguments;
    if (normalizedOperation == "loopanim" && normalizedArguments.size() == 2)
    {
        const std::vector<std::string> secondArguments = splitWhitespaceScriptArguments(normalizedArguments[1]);
        if (secondArguments.size() == 2)
        {
            normalizedArguments = { normalizedArguments[0], secondArguments[0], secondArguments[1] };
        }
    }
    if (normalizedOperation != "playanim" && normalizedOperation != "loopanim"
        && normalizedOperation != "playanimation" && normalizedOperation != "playanimsound"
        && normalizedOperation != "setanimplaying")
    {
        return false;
    }
    if (normalizedArguments.empty())
    {
        return false;
    }

    Mm9ScriptRuntimeAnimationRequest request = {};
    request.scriptSource = m_activeScriptSource;
    request.objectHandle = objectHandle.empty() ? activeObjectHandle() : objectHandle;
    request.operation = normalizedOperation;
    request.animationName = normalizedOperation == "setanimplaying"
        ? scriptValueString(evaluateScriptExpression(*this, normalizedArguments[0]))
        : resolveScriptString(normalizedArguments[0]);
    request.line = line;
    if ((normalizedOperation == "playanim" || normalizedOperation == "playanimation")
        && normalizedArguments.size() >= 2)
    {
        const size_t callbackIndex = normalizedOperation == "playanimation" && normalizedArguments.size() >= 3 ? 2 : 1;
        request.callbackLabel = trimCopy(normalizedArguments[callbackIndex]);
    }
    else if (normalizedOperation == "playanimsound")
    {
        request.loopCount = scriptArgumentNumber(*this, normalizedArguments, 1);
    }
    else if (normalizedOperation == "loopanim")
    {
        request.loopCount = scriptArgumentNumber(*this, normalizedArguments, 1);
        if (normalizedArguments.size() >= 3)
        {
            request.callbackLabel = trimCopy(normalizedArguments[2]);
        }
    }

    if (isCallbackLabel(request.callbackLabel))
    {
        registerCallback(request.callbackLabel, line, normalizedOperation, request.animationName);
    }

    recordAnimationRequest(std::move(request));
    return true;
}

bool Mm9ScriptRuntime::requestActorAction(
    const std::string &objectHandle,
    const std::string &operation,
    const std::vector<std::string> &arguments,
    size_t line)
{
    const std::string normalizedOperation = lowerCopy(trimCopy(operation));
    const std::vector<std::string> normalizedArguments = normalizedServiceArguments(arguments);
    if (normalizedOperation != "taunt" && normalizedOperation != "aware" && normalizedOperation != "launch"
        && normalizedOperation != "converse" && normalizedOperation != "resumewait"
        && normalizedOperation != "pausewait" && normalizedOperation != "jump" && normalizedOperation != "blendanim")
    {
        return false;
    }

    const std::string handle = objectHandle.empty() ? activeObjectHandle() : objectHandle;
    if (handle.empty())
    {
        return false;
    }

    Mm9ScriptRuntimeAnimationRequest request = {};
    request.scriptSource = m_activeScriptSource;
    request.objectHandle = handle;
    request.operation = normalizedOperation;
    request.animationName = normalizedOperation;
    request.line = line;

    if (normalizedOperation == "blendanim" && !normalizedArguments.empty())
    {
        request.animationName = resolveScriptString(normalizedArguments[0]);
        if (normalizedArguments.size() >= 2)
        {
            request.callbackLabel = trimCopy(normalizedArguments[1]);
        }
    }
    else if (normalizedOperation == "converse" && normalizedArguments.size() >= 2)
    {
        request.loopCount = scriptArgumentNumber(*this, normalizedArguments, 0);
        request.callbackLabel = trimCopy(normalizedArguments[1]);
    }
    else if (normalizedOperation == "launch")
    {
        if (!normalizedArguments.empty())
        {
            request.callbackLabel = trimCopy(normalizedArguments[0]);
        }
        request.loopCount = scriptArgumentNumber(*this, normalizedArguments, 1);
    }
    else if (normalizedOperation == "resumewait" || normalizedOperation == "pausewait")
    {
        request.loopCount = scriptArgumentNumber(*this, normalizedArguments, 0);
    }
    else if (!normalizedArguments.empty())
    {
        request.callbackLabel = trimCopy(normalizedArguments[0]);
    }

    m_state.objectAiStates[handle] = normalizedOperation;
    if (isCallbackLabel(request.callbackLabel))
    {
        registerCallback(request.callbackLabel, line, normalizedOperation, request.animationName);
    }

    recordAnimationRequest(std::move(request));
    return true;
}

bool Mm9ScriptRuntime::killObject(const std::string &objectHandle)
{
    const std::string handle = objectHandle.empty() ? activeObjectHandle() : objectHandle;
    if (handle.empty())
    {
        return false;
    }

    m_state.objectAiStates[handle] = "dead";
    m_state.objectAttackStates[handle] = false;
    m_state.removedObjects[handle] = true;
    return true;
}

bool Mm9ScriptRuntime::damageObject(
    const std::string &targetHandle,
    const std::vector<std::string> &arguments,
    size_t line)
{
    const std::vector<std::string> normalizedArguments = normalizedServiceArguments(arguments);
    if (targetHandle.empty() || normalizedArguments.size() < 2)
    {
        return false;
    }

    Mm9ScriptRuntimeDamageRequest request = {};
    request.scriptSource = m_activeScriptSource;
    request.targetHandle = targetHandle;
    request.amount = scriptArgumentNumber(*this, normalizedArguments, 0);
    request.damageType = scriptArgumentNumber(*this, normalizedArguments, 1);
    request.noReaction = scriptArgumentBool(*this, normalizedArguments, 2);
    request.line = line;
    const int32_t amount = request.amount;
    const bool noReaction = request.noReaction;
    recordDamageRequest(std::move(request));

    const std::optional<std::pair<std::string, int32_t>> targetParts = mm9ObjectHandleParts(targetHandle);
    if (!targetParts)
    {
        return true;
    }

    auto objectIterator = m_state.objectStats.find(targetHandle);
    if (objectIterator == m_state.objectStats.end())
    {
        return true;
    }

    auto hitPointsIterator = findCaseInsensitiveStat(objectIterator->second, "HitPoints");
    if (hitPointsIterator == objectIterator->second.end())
    {
        return true;
    }

    hitPointsIterator->second = std::max(0, hitPointsIterator->second - std::max(0, amount));
    if (!noReaction)
    {
        std::optional<std::string> callbackError;
        size_t callbackCount = 0;
        dispatchRegisteredCallbacks(
            "ondamage",
            "",
            targetParts->first,
            targetParts->second,
            callbackError,
            callbackCount);
        dispatchRegisteredCallbacks(
            "ondamagedone",
            "",
            targetParts->first,
            targetParts->second,
            callbackError,
            callbackCount);
    }

    if (hitPointsIterator->second != 0)
    {
        return true;
    }

    m_state.objectAiStates[targetHandle] = "dead";
    m_state.objectAttackStates[targetHandle] = false;
    m_state.removedObjects[targetHandle] = true;
    if (!noReaction)
    {
        std::optional<std::string> callbackError;
        size_t callbackCount = 0;
        dispatchRegisteredCallbacks(
            "ondeath",
            "",
            targetParts->first,
            targetParts->second,
            callbackError,
            callbackCount);
        dispatchRegisteredCallbacks(
            "ondeathdone",
            "",
            targetParts->first,
            targetParts->second,
            callbackError,
            callbackCount);
    }

    return true;
}

bool Mm9ScriptRuntime::requestMovement(
    const std::string &objectHandle,
    const std::string &operation,
    const std::vector<std::string> &arguments,
    size_t line)
{
    const std::string normalizedOperation = lowerCopy(trimCopy(operation));
    const std::vector<std::string> normalizedArguments = normalizedServiceArguments(arguments);
    if (normalizedOperation != "stop" && normalizedOperation != "walk" && normalizedOperation != "run"
        && normalizedArguments.empty())
    {
        return false;
    }

    Mm9ScriptRuntimeMovementRequest request = {};
    request.scriptSource = m_activeScriptSource;
    request.objectHandle = objectHandle.empty() ? activeObjectHandle() : objectHandle;
    request.operation = normalizedOperation;
    request.line = line;

    if (normalizedOperation == "walk" || normalizedOperation == "run")
    {
        m_state.objectAiStates[request.objectHandle] = normalizedOperation;
    }
    else if (normalizedOperation == "movetopos")
    {
        if (normalizedArguments.size() < 4)
        {
            return false;
        }

        request.targetPosition = scriptVectorFromArguments(*this, normalizedArguments, 0);
        request.speed = scriptValueNumber(evaluateScriptExpression(*this, normalizedArguments[3]));
        if (normalizedArguments.size() >= 5)
        {
            request.callbackLabel = trimCopy(normalizedArguments[4]);
        }
    }
    else if (normalizedOperation == "runtopos" || normalizedOperation == "walktopos")
    {
        if (normalizedArguments.size() < 3)
        {
            return false;
        }

        request.targetPosition = scriptVectorFromArguments(*this, normalizedArguments, 0);
        request.speed = scriptArgumentNumber(*this, normalizedArguments, 3);
        if (normalizedArguments.size() >= 5)
        {
            request.callbackLabel = trimCopy(normalizedArguments[4]);
        }
    }
    else if (normalizedOperation == "walkto" || normalizedOperation == "runto")
    {
        if (normalizedArguments.empty())
        {
            return false;
        }

        request.targetHandle = resolveScriptString(normalizedArguments[0]);
        if (normalizedArguments.size() >= 2)
        {
            request.distance = scriptValueNumber(evaluateScriptExpression(*this, normalizedArguments[1]));
        }
        if (normalizedArguments.size() >= 3)
        {
            request.callbackLabel = trimCopy(normalizedArguments[2]);
        }
    }
    else if (normalizedOperation == "movedir")
    {
        if (normalizedArguments.size() < 5)
        {
            return false;
        }

        request.direction = scriptVectorFromArguments(*this, normalizedArguments, 0);
        request.distance = scriptValueNumber(evaluateScriptExpression(*this, normalizedArguments[3]));
        request.speed = scriptValueNumber(evaluateScriptExpression(*this, normalizedArguments[4]));
        if (normalizedArguments.size() >= 6)
        {
            request.callbackLabel = trimCopy(normalizedArguments[5]);
        }
    }
    else if (normalizedOperation == "faceobject")
    {
        request.targetHandle = resolveScriptString(normalizedArguments[0]);
        if (normalizedArguments.size() >= 2)
        {
            request.speed = scriptValueNumber(evaluateScriptExpression(*this, normalizedArguments[1]));
        }
        if (normalizedArguments.size() >= 3)
        {
            request.callbackLabel = trimCopy(normalizedArguments[2]);
        }
    }
    else if (normalizedOperation == "facepos")
    {
        if (normalizedArguments.size() < 3)
        {
            return false;
        }

        request.targetPosition = scriptVectorFromArguments(*this, normalizedArguments, 0);
        if (normalizedArguments.size() >= 4)
        {
            request.speed = scriptValueNumber(evaluateScriptExpression(*this, normalizedArguments[3]));
        }
        if (normalizedArguments.size() >= 5)
        {
            request.callbackLabel = trimCopy(normalizedArguments[4]);
        }
    }
    else if (normalizedOperation == "rotate")
    {
        if (normalizedArguments.size() < 5)
        {
            return false;
        }

        request.direction = scriptVectorFromArguments(*this, normalizedArguments, 0);
        request.distance = scriptValueNumber(evaluateScriptExpression(*this, normalizedArguments[3]));
        request.speed = scriptValueNumber(evaluateScriptExpression(*this, normalizedArguments[4]));
        if (normalizedArguments.size() >= 6)
        {
            request.callbackLabel = trimCopy(normalizedArguments[5]);
        }
    }
    else if (normalizedOperation == "facedir")
    {
        if (normalizedArguments.size() < 3)
        {
            return false;
        }

        request.direction = scriptVectorFromArguments(*this, normalizedArguments, 0);
        m_state.objectFaceDirs[request.objectHandle] = request.direction;
        if (normalizedArguments.size() >= 4)
        {
            request.speed = scriptValueNumber(evaluateScriptExpression(*this, normalizedArguments[3]));
        }
        if (normalizedArguments.size() >= 5)
        {
            request.callbackLabel = trimCopy(normalizedArguments[4]);
        }
    }
    else if (normalizedOperation == "strafe")
    {
        if (normalizedArguments.size() < 3)
        {
            return false;
        }

        request.direction = scriptVectorFromArguments(*this, normalizedArguments, 0);
        if (normalizedArguments.size() >= 4)
        {
            request.speed = scriptValueNumber(evaluateScriptExpression(*this, normalizedArguments[3]));
        }
    }
    else if (normalizedOperation == "setpushback")
    {
        if (normalizedArguments.size() < 4)
        {
            return false;
        }

        request.direction = scriptVectorFromArguments(*this, normalizedArguments, 0);
        request.speed = scriptValueNumber(evaluateScriptExpression(*this, normalizedArguments[3]));
    }
    else if (normalizedOperation == "turnleft")
    {
        if (normalizedArguments.empty())
        {
            return false;
        }

        request.direction = {0.0, 0.0, 1.0};
        request.distance = scriptValueNumber(evaluateScriptExpression(*this, normalizedArguments[0]));
    }
    else if (normalizedOperation == "stop")
    {
        m_state.objectAttackStates[request.objectHandle] = false;
        m_state.objectAiStates[request.objectHandle] = "stopped";
    }
    else
    {
        return false;
    }

    if (isCallbackLabel(request.callbackLabel))
    {
        registerCallback(request.callbackLabel, line, normalizedOperation, request.targetHandle);
    }
    recordMovementRequest(std::move(request));
    return true;
}

Mm9DialogueRuntime &Mm9ScriptRuntime::dialogueRuntime()
{
    return m_dialogueRuntime;
}

const std::string &Mm9ScriptRuntime::activeScriptSource() const
{
    return m_activeScriptSource;
}

std::string Mm9ScriptRuntime::activeObjectPropertyKey(const std::string &propertyName) const
{
    if (propertyName.empty())
    {
        return {};
    }

    const Mm9DialogueOwnerContext &owner = m_dialogueRuntime.owner();
    if (owner.mapId.empty() || owner.objectIndex < 0)
    {
        return {};
    }

    return owner.mapId + ":" + std::to_string(owner.objectIndex) + ":" + propertyName;
}

std::string Mm9ScriptRuntime::activeObjectHandle() const
{
    const Mm9DialogueOwnerContext &owner = m_dialogueRuntime.owner();
    if (owner.mapId.empty() || owner.objectIndex < 0)
    {
        return {};
    }

    return "mm9:" + owner.mapId + ":object:" + std::to_string(owner.objectIndex);
}

const Mm9GeneratedObjectDialogueBinding *Mm9ScriptRuntime::objectBindingForHandle(const std::string &handle) const
{
    const std::optional<std::pair<std::string, int32_t>> parts = mm9ObjectHandleParts(handle);
    if (!parts)
    {
        return nullptr;
    }

    return objectBindingForObject(parts->first, parts->second);
}

const Mm9GeneratedObjectDialogueBinding *Mm9ScriptRuntime::objectBindingForObject(
    const std::string &mapId,
    int32_t objectIndex) const
{
    const auto bindingIterator = std::find_if(
        m_package.objectBindings.begin(),
        m_package.objectBindings.end(),
        [&](const Mm9GeneratedObjectDialogueBinding &binding)
        {
            return binding.mapId == mapId && binding.objectIndex == objectIndex;
        });

    return bindingIterator != m_package.objectBindings.end() ? &*bindingIterator : nullptr;
}

bool Mm9ScriptRuntime::runLabelForObject(
    const std::string &scriptSource,
    const std::string &label,
    const std::string &mapId,
    int32_t objectIndex,
    std::optional<std::string> &errorMessage)
{
    const std::optional<std::vector<std::string>> scriptParams = std::nullopt;
    return runLabelForObject(scriptSource, label, mapId, objectIndex, scriptParams, errorMessage);
}

bool Mm9ScriptRuntime::runLabelForObject(
    const std::string &scriptSource,
    const std::string &label,
    const std::string &mapId,
    int32_t objectIndex,
    const std::vector<std::string> &scriptParams,
    std::optional<std::string> &errorMessage)
{
    return runLabelForObject(
        scriptSource,
        label,
        mapId,
        objectIndex,
        std::optional<std::vector<std::string>>(scriptParams),
        errorMessage);
}

bool Mm9ScriptRuntime::runLabelForObject(
    const std::string &scriptSource,
    const std::string &label,
    const std::string &mapId,
    int32_t objectIndex,
    const std::optional<std::vector<std::string>> &scriptParams,
    std::optional<std::string> &errorMessage)
{
    Mm9DialogueOwnerContext owner = {};
    std::string ownerError;
    if (!m_dialogueRuntime.ownerContextForObject(mapId, objectIndex, owner, &ownerError))
    {
        owner.mapId = mapId;
        owner.objectIndex = objectIndex;
        owner.scriptName = scriptSource;
    }
    if (scriptParams)
    {
        owner.scriptParams = *scriptParams;
    }

    const Mm9DialogueOwnerContext previousOwner = m_dialogueRuntime.owner();
    m_dialogueRuntime.setOwnerContext(std::move(owner));
    const bool ran = runLabel(scriptSource, label, errorMessage);
    m_dialogueRuntime.setOwnerContext(previousOwner);
    return ran;
}

void Mm9ScriptRuntime::removeRuntimeObject(const std::string &handle)
{
    if (handle.empty())
    {
        return;
    }

    m_state.removedObjects[handle] = true;
    m_state.objectLinks.erase(handle);
    for (auto &linkPair : m_state.objectLinks)
    {
        std::vector<std::string> &links = linkPair.second;
        links.erase(std::remove(links.begin(), links.end(), handle), links.end());
    }

    const std::optional<std::pair<std::string, int32_t>> objectParts = mm9ObjectHandleParts(handle);
    if (!objectParts)
    {
        return;
    }

    const std::string &mapId = objectParts->first;
    const int32_t objectIndex = objectParts->second;
    m_state.triggers.erase(
        std::remove_if(
            m_state.triggers.begin(),
            m_state.triggers.end(),
            [&](const Mm9ScriptRuntimeTriggerRegistration &trigger)
            {
                return trigger.mapId == mapId && trigger.objectIndex == objectIndex;
            }),
        m_state.triggers.end());
    m_state.scheduledInvocations.erase(
        std::remove_if(
            m_state.scheduledInvocations.begin(),
            m_state.scheduledInvocations.end(),
            [&](const Mm9ScriptRuntimeScheduledInvocation &invocation)
            {
                return invocation.mapId == mapId && invocation.objectIndex == objectIndex;
            }),
        m_state.scheduledInvocations.end());
    m_state.registeredCallbacks.erase(
        std::remove_if(
            m_state.registeredCallbacks.begin(),
            m_state.registeredCallbacks.end(),
            [&](const Mm9ScriptRuntimeCallback &callback)
            {
                return callback.mapId == mapId && callback.objectIndex == objectIndex;
            }),
        m_state.registeredCallbacks.end());
    m_registeredCallbacks = m_state.registeredCallbacks;
}

std::string Mm9ScriptRuntime::resolveSoundHandle(const std::string &token) const
{
    const std::string trimmed = trimCopy(token);
    if (trimmed.empty())
    {
        return {};
    }

    const auto soundHandleIterator = m_state.soundHandleVars.find(trimmed);
    if (soundHandleIterator != m_state.soundHandleVars.end())
    {
        return soundHandleIterator->second;
    }

    const std::string scriptString = getScriptStrVar(trimmed);
    if (!scriptString.empty())
    {
        return scriptString;
    }

    return unquoteScriptString(trimmed);
}

void Mm9ScriptRuntime::recordAudioRequest(Mm9ScriptRuntimeAudioRequest request)
{
    const Mm9DialogueOwnerContext &owner = m_dialogueRuntime.owner();
    request.mapId = owner.mapId;
    request.objectIndex = owner.objectIndex;
    request.objectName = owner.objectName;
    request.scriptSource = m_activeScriptSource.empty() ? owner.scriptName : m_activeScriptSource;
    m_state.audioRequests.push_back(request);
    m_audioRequests.push_back(std::move(request));
}

void Mm9ScriptRuntime::recordAnimationRequest(Mm9ScriptRuntimeAnimationRequest request)
{
    if (request.scriptSource.empty())
    {
        request.scriptSource = m_activeScriptSource;
    }
    if (request.objectHandle.empty())
    {
        request.objectHandle = activeObjectHandle();
    }
    m_state.animationRequests.push_back(request);
    m_animationRequests.push_back(std::move(request));
}

void Mm9ScriptRuntime::recordClientFxRequest(Mm9ScriptRuntimeClientFxRequest request)
{
    if (request.scriptSource.empty())
    {
        request.scriptSource = m_activeScriptSource;
    }
    m_state.clientFxRequests.push_back(request);
    m_clientFxRequests.push_back(std::move(request));
}

void Mm9ScriptRuntime::recordPresentationRequest(
    const std::string &operation,
    const std::vector<std::string> &arguments,
    size_t line)
{
    Mm9ScriptRuntimePresentationRequest request = {};
    request.scriptSource = m_activeScriptSource;
    request.operation = operation;
    request.arguments = arguments;
    request.line = line;
    m_state.presentationRequests.push_back(request);
    m_presentationRequests.push_back(std::move(request));
}

void Mm9ScriptRuntime::recordMovementRequest(Mm9ScriptRuntimeMovementRequest request)
{
    if (request.scriptSource.empty())
    {
        request.scriptSource = m_activeScriptSource;
    }
    if (request.objectHandle.empty())
    {
        request.objectHandle = activeObjectHandle();
    }
    m_state.movementRequests.push_back(request);
    m_movementRequests.push_back(std::move(request));
}

void Mm9ScriptRuntime::recordSpawnRequest(Mm9ScriptRuntimeSpawnRequest request)
{
    if (request.scriptSource.empty())
    {
        request.scriptSource = m_activeScriptSource;
    }
    m_state.spawnRequests.push_back(request);
    m_spawnRequests.push_back(std::move(request));
}

void Mm9ScriptRuntime::recordAiRequest(Mm9ScriptRuntimeAiRequest request)
{
    if (request.scriptSource.empty())
    {
        request.scriptSource = m_activeScriptSource;
    }
    if (request.objectHandle.empty())
    {
        request.objectHandle = activeObjectHandle();
    }
    m_state.aiRequests.push_back(request);
    m_aiRequests.push_back(std::move(request));
}

void Mm9ScriptRuntime::recordAttachmentRequest(Mm9ScriptRuntimeAttachmentRequest request)
{
    if (request.scriptSource.empty())
    {
        request.scriptSource = m_activeScriptSource;
    }
    if (request.objectHandle.empty())
    {
        request.objectHandle = activeObjectHandle();
    }
    m_state.attachmentRequests.push_back(request);
    m_attachmentRequests.push_back(std::move(request));
}

void Mm9ScriptRuntime::recordPromotionRequest(Mm9ScriptRuntimePromotionRequest request)
{
    if (request.scriptSource.empty())
    {
        request.scriptSource = m_activeScriptSource;
    }
    m_state.promotionRequests.push_back(request);
    m_promotionRequests.push_back(std::move(request));
}

void Mm9ScriptRuntime::recordPartyCommandRequest(Mm9ScriptRuntimePartyCommandRequest request)
{
    if (request.scriptSource.empty())
    {
        request.scriptSource = m_activeScriptSource;
    }
    m_state.partyCommandRequests.push_back(request);
    m_partyCommandRequests.push_back(std::move(request));
}

void Mm9ScriptRuntime::recordControlRequest(Mm9ScriptRuntimeControlRequest request)
{
    if (request.scriptSource.empty())
    {
        request.scriptSource = m_activeScriptSource;
    }
    m_state.controlRequests.push_back(request);
    m_controlRequests.push_back(std::move(request));
}

void Mm9ScriptRuntime::scheduleInvocation(
    const std::string &operation,
    const std::string &label,
    double minDelay,
    double maxDelay,
    size_t line)
{
    if (label.empty() || m_activeScriptSource.empty())
    {
        return;
    }

    const Mm9DialogueOwnerContext &owner = m_dialogueRuntime.owner();
    Mm9ScriptRuntimeScheduledInvocation invocation = {};
    invocation.scriptSource = m_activeScriptSource;
    invocation.operation = operation;
    invocation.mapId = owner.mapId;
    invocation.objectIndex = owner.objectIndex;
    invocation.label = label;
    invocation.minDelay = minDelay;
    invocation.maxDelay = maxDelay;
    invocation.dueTimeSeconds = m_state.scriptTimeSeconds + scheduledDelaySeconds(minDelay, maxDelay);
    invocation.line = line;
    m_state.scheduledInvocations.push_back(std::move(invocation));
}

void Mm9ScriptRuntime::recordDamageRequest(Mm9ScriptRuntimeDamageRequest request)
{
    if (request.scriptSource.empty())
    {
        request.scriptSource = m_activeScriptSource;
    }
    m_state.damageRequests.push_back(request);
    m_damageRequests.push_back(std::move(request));
}

void Mm9ScriptRuntime::queueGreetingSoundRequest(const Mm9DialogueOwnerContext &owner)
{
    Mm9ScriptRuntimeAudioRequest request = {};
    request.mapId = owner.mapId;
    request.objectIndex = owner.objectIndex;
    request.objectName = owner.objectName;
    request.scriptSource = owner.scriptName;
    request.operation = "greeting";
    request.soundName = owner.greetingSound;
    m_audioRequests.push_back(std::move(request));
}
}
