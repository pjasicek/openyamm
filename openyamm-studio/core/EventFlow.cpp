#include "core/EventFlow.h"

#include "core/Json.h"

#include "engine/scripting/LuaStateOwner.h"

#include <lua.hpp>
#include <yaml-cpp/yaml.h>

#include <map>
#include <algorithm>
#include <set>

namespace OpenYAMM::Studio
{
namespace
{
// Runs before the game's scripts: `evt` as a recorder. A test (a function the handler branches on) takes its
// answer from the current list of decisions; everything else is written down and returns nothing.
const char *const SandboxPrelude = R"lua(
__flow = {decisions = {}, limits = {}, cursor = 0, trace = {}, known = {}}
local flow = __flow
for name in __flow_known_names:gmatch("%S+") do flow.known[name] = true end
-- Questions about a count: answered "none" or "plenty" as a test is answered no or yes.
local countTests = {PartyMemberItemCount = true, CountItems = true}
-- A draw by the game's dice (evt.RandomBetween(low, high); evt._RandomJump(event, step, targets), which the
-- scripts' PickRandomOption calls): every outcome is a way of its own, up to this many (a wider range shows its
-- first outcomes only).
local MAX_DRAWN = 12
local function drawn(count)
    flow.cursor = flow.cursor + 1
    local taken = flow.decisions[flow.cursor]
    if type(taken) ~= "number" then
        taken = 0
        flow.decisions[flow.cursor] = 0
    end
    flow.limits[flow.cursor] = math.max(1, math.min(count, MAX_DRAWN))
    return taken
end
local function isTest(name)
    return name == "Cmp" or name == "Question" or name:find("^Check") or name:find("^Is") or name:find("^Has")
        or name:find("^Random") or name:find("^Can") or name:find("^PartyMemberHas") or name:find("^PartyMemberCan")
        or name:find("^PartyMemberKnows") or countTests[name]
end
-- What the game's questions about the party and the world answer here, where no game runs: a party of four at the
-- origin at time nothing, with no variable set (a variable answers the default the handler gives) and an empty
-- hook context. There are no actors: a question about one answers nothing, which ends a handler's scan of them.
-- Without these answers a handler that reckons with one stops on nil (7d23's exit counts the party's wetsuits).
local function zero() return 0 end
local function default(args) return args[2] or 0 end
local function origin() return 0, 0, 0 end
local answers = {
    GetMapVar = default, GetGlobalVar = default, GetPartyVariable = default, GetRuntimeVariable = default,
    GetPartyMemberCount = function() return 4 end,
    GetCurrentPlayerIndex = zero, CurrentGameMinutes = zero, GetHookContext = function() return {} end,
    GetHeldItemId = zero, GetPlayerSkill = zero, GetClassSkillCap = zero, SkillResetCost = zero, GetClassId = zero,
    GetPlayerClass = zero, GetPartyMemberPortraitId = zero, GetActiveEventSpellId = zero,
    GetPartyPosition = origin,
}
evt = setmetatable({global = {}, map = {}, CanShowTopic = {}, meta = {global = {}, map = {}}}, {
    __index = function(_, name)
        if type(name) ~= "string" then return nil end
        return function(...)
            local args = {...}
            if name == "_RandomJump" and type(args[3]) == "table" and #args[3] > 0 then
                local taken = drawn(#args[3])
                flow.trace[#flow.trace + 1] = {test = true, drawn = true, taken = true,
                    name = "one of " .. #args[3] .. " at random: the " .. (taken + 1) .. "."}
                return args[3][taken + 1]
            end
            if name == "RandomBetween" and type(args[1]) == "number" and type(args[2]) == "number"
                and args[2] >= args[1] then
                local taken = drawn(args[2] - args[1] + 1)
                flow.trace[#flow.trace + 1] = {test = true, drawn = true, taken = true,
                    name = "random " .. args[1] .. " to " .. args[2] .. " is " .. (args[1] + taken)}
                return args[1] + taken
            end
            if name:sub(1, 1) == "_" then return nil end
            -- A function the game does not give scripts: the game would stop the handler there.
            local unknown = not flow.known[name] or nil
            if isTest(name) then
                flow.cursor = flow.cursor + 1
                local taken = flow.decisions[flow.cursor]
                if taken == nil then
                    taken = false
                    flow.decisions[flow.cursor] = false
                end
                flow.trace[#flow.trace + 1] = {test = true, name = name, args = args, taken = taken, unknown = unknown}
                if countTests[name] then return taken and 9999 or 0 end
                return taken
            end
            flow.trace[#flow.trace + 1] = {name = name, args = args, unknown = unknown}
            local answer = answers[name]
            if answer then return answer(args) end
            return nil
        end
    end,
})
tr = function(text) return text end
)lua";

// Runs after the game's scripts: every handler, every way its tests can come out, and the result as JSON text.
const char *const SandboxExplorer = R"lua(
local flow = __flow
local support = eventSupport or {}
local tagNames = {}
for name, tag in pairs(support.varTag or {}) do
    if type(tag) == "number" and (tagNames[tag] == nil or #name < #tagNames[tag]) then tagNames[tag] = name end
end
local doorActions = {[0] = "open", [1] = "close", [2] = "toggle"}

local function selectorText(selector)
    if type(selector) ~= "number" then return tostring(selector) end
    local tag = selector % 65536
    local index = math.floor(selector / 65536)
    if selector >= 0x7B and selector < 0x7B + 100 then return "map_var " .. (selector - 0x7B) end
    local name = tagNames[tag]
    if name == "QBits" then return "qbit " .. index end
    if name == "Inventory" then return "item " .. index end
    if name == "Awards" then return "award " .. index end
    if name == "AutonotesBits" then return "autonote " .. index end
    if name ~= nil then return name .. (index ~= 0 and (" " .. index) or "") end
    return "selector " .. selector
end

local function argText(value)
    if type(value) == "string" then return '"' .. value .. '"' end
    if type(value) == "table" then return "{...}" end
    return tostring(value)
end

local function describe(entry)
    if entry.drawn then return entry.name end
    local name, a = entry.name, entry.args
    if name == "Cmp" then
        local what = selectorText(a[1])
        if what:find("^qbit") or what:find("^item") or what:find("^award") or what:find("^autonote") then
            return what
        end
        return what .. " >= " .. tostring(a[2])
    end
    if name == "Set" then return "set " .. selectorText(a[1]) .. " = " .. tostring(a[2]) end
    if name == "Add" then
        local what = selectorText(a[1])
        if what:find("^qbit") or what:find("^award") or what:find("^autonote") then return "set " .. what end
        if what:find("^item") then return "give " .. what end
        return "add " .. what .. " + " .. tostring(a[2])
    end
    if name == "Subtract" then
        local what = selectorText(a[1])
        if what:find("^qbit") or what:find("^award") or what:find("^autonote") then return "clear " .. what end
        if what:find("^item") then return "take " .. what end
        return "subtract " .. what .. " - " .. tostring(a[2])
    end
    -- A member's count of an item (PlayerItemCount, Xeen.itemCount): as a test on the item.
    if name == "PartyMemberItemCount" and type(a[2]) == "number" then return "item " .. a[2] end
    if name == "SetDoorState" then
        return "door " .. tostring(a[1]) .. " " .. (doorActions[a[2]] or tostring(a[2]))
    end
    if name == "OpenChest" then return "open chest " .. tostring(a[1]) end
    if name == "SetMapVar" then return "set map_var " .. argText(a[1]) .. " = " .. tostring(a[2]) end
    if name == "MoveToMap" then
        local target = a[9]
        local rest = {}
        for index = 4, 8 do rest[#rest + 1] = tostring(a[index]) end
        local where = tostring(a[1]) .. ", " .. tostring(a[2]) .. ", " .. tostring(a[3])
            .. " (direction, look, speed, house, icon: " .. table.concat(rest, ", ") .. ")"
        if type(target) == "string" and target ~= "" then return "leave to " .. target .. " at " .. where end
        return "teleport to " .. where
    end
    local parts = {}
    for index = 1, #a do parts[#parts + 1] = argText(a[index]) end
    return name .. "(" .. table.concat(parts, ", ") .. ")"
end

-- What is wrong with a call whatever the path: a function the game does not have, or a variable selector that is
-- not a number (a name in quotes, or a name that does not exist and so is nil).
local selectorCalls = {Cmp = true, Set = true, Add = true, Subtract = true}
local function problemOf(entry)
    if entry.drawn then return nil end
    if entry.unknown then return "evt." .. entry.name .. " is not a function of the game" end
    if selectorCalls[entry.name] and type(entry.args[1]) ~= "number" then
        return "evt." .. entry.name .. " is given " .. argText(entry.args[1])
            .. " where a variable selector belongs (a number: MapVar(2), QBit(5), or a global of the scripts such as"
            .. " Gold, HP, BaseLuck; nil means the name used does not exist)"
    end
    return nil
end

local function quote(text)
    text = tostring(text):gsub('[%c"\\]', function(character)
        if character == '"' then return '\\"' end
        if character == "\\" then return "\\\\" end
        if character == "\n" then return "\\n" end
        return " "
    end)
    return '"' .. text .. '"'
end

local MAX_PATHS = 48
local MAX_TESTS = 24
local ids = {}
for id in pairs(evt.map) do if type(id) == "number" then ids[#ids + 1] = id end end
table.sort(ids)
local out = {}
local titles = (evt.meta.map or {}).title or {}
for _, id in ipairs(ids) do
    local handler = evt.map[id]
    local paths = {}
    local truncated = false
    -- Steps a question continues the handler at (AskQuestion's wrong and right answer, AskQuestionWithAnswerSteps' and
    -- AskChoiceWithAnswerSteps' fallback and answers): each is explored as a run of its own, after the first run's.
    local continued, continueOrder = {}, {}
    local function noteStep(step)
        if type(step) == "number" and not continued[step] then
            continued[step] = true
            continueOrder[#continueOrder + 1] = step
        end
    end
    local function explore(step)
    flow.decisions = {}
    while true do
        flow.cursor = 0
        flow.trace = {}
        -- The same random numbers on every run, so two readings of one handler agree.
        math.randomseed(1)
        -- Without arguments, as an event is first run (a handler's own argument is its step when it is continued).
        local ok, message = pcall(handler, step)
        local tests, effects, problems = {}, {}, {}
        if step ~= nil then
            tests[1] = '{"what":' .. quote("answered: continued at step " .. step) .. ',"taken":true}'
        end
        for _, entry in ipairs(flow.trace) do
            if not entry.test and entry.name == "AskQuestion" and type(entry.args) == "table" then
                noteStep(entry.args[2])
                noteStep(entry.args[4])
            elseif not entry.test and (entry.name == "AskQuestionWithAnswerSteps"
                    or entry.name == "AskChoiceWithAnswerSteps") and type(entry.args) == "table" then
                noteStep(entry.args[2])
                if type(entry.args[4]) == "table" then
                    for _, choice in ipairs(entry.args[4]) do
                        if type(choice) == "table" then noteStep(choice.Step) end
                    end
                end
            end
            local problem = problemOf(entry)
            if problem then problems[#problems + 1] = quote(problem) end
            if entry.test then
                tests[#tests + 1] = '{"what":' .. quote(describe(entry)) .. ',"taken":' .. tostring(entry.taken) .. "}"
            else
                effects[#effects + 1] = quote(describe(entry))
            end
        end
        local path = '{"tests":[' .. table.concat(tests, ",") .. '],"effects":[' .. table.concat(effects, ",") .. "]"
        if #problems > 0 then path = path .. ',"problems":[' .. table.concat(problems, ",") .. "]" end
        if not ok then path = path .. ',"error":' .. quote(message) end
        paths[#paths + 1] = path .. "}"
        -- The next way: flip the last test still answered "no", or take the next outcome of the last draw that
        -- has one left; drop what came after it.
        local last = math.min(flow.cursor, MAX_TESTS)
        if flow.cursor > MAX_TESTS then truncated = true end
        local function spent(index)
            local decision = flow.decisions[index]
            if type(decision) == "number" then return decision >= flow.limits[index] - 1 end
            return decision
        end
        while last >= 1 and spent(last) do last = last - 1 end
        if last < 1 then break end
        if #paths >= MAX_PATHS then truncated = true; break end
        if type(flow.decisions[last]) == "number" then
            flow.decisions[last] = flow.decisions[last] + 1
        else
            flow.decisions[last] = true
        end
        for index = last + 1, #flow.decisions do flow.decisions[index] = nil end
    end
    end
    explore(nil)
    local nextStep = 1
    while nextStep <= #continueOrder and #paths < MAX_PATHS do
        explore(continueOrder[nextStep])
        nextStep = nextStep + 1
    end
    if nextStep <= #continueOrder then truncated = true end
    out[#out + 1] = '{"event":' .. id .. ',"title":' .. quote(titles[id] or "") .. ',"paths":['
        .. table.concat(paths, ",") .. '],"truncated":' .. tostring(truncated) .. "}"
end
__flow_result = "[" .. table.concat(out, ",\n") .. "]"
)lua";

// A handler that never ends would hang the tool: stop it after a fixed number of instructions.
void instructionLimitHook(lua_State *pLuaState, lua_Debug *)
{
    luaL_error(pLuaState, "the handler ran past the sandbox's instruction limit");
}
}

bool exploreEventHandlers(const LoadedMap &map, std::string &json, std::string &errorMessage)
{
    json = "[]";

    if (map.fullScriptSource.empty())
    {
        return true;
    }

    Engine::LuaStateOwner lua;

    if (!lua.isValid())
    {
        errorMessage = "no Lua state";
        return false;
    }

    lua.openApprovedLibraries();
    std::optional<std::string> runError;

    lua_pushstring(lua.state(), EventFunctionNames);
    lua_setglobal(lua.state(), "__flow_known_names");

    if (!lua.runChunk(SandboxPrelude, "@sandbox prelude", runError)
        || !lua.runChunk(map.fullScriptSource, "@map script", runError))
    {
        errorMessage = "the map's script does not run in the sandbox: " + runError.value_or("unknown error");
        return false;
    }

    lua_sethook(lua.state(), instructionLimitHook, LUA_MASKCOUNT, 20000000);

    if (!lua.runChunk(SandboxExplorer, "@sandbox explorer", runError))
    {
        errorMessage = "the sandbox failed: " + runError.value_or("unknown error");
        return false;
    }

    lua_sethook(lua.state(), nullptr, 0, 0);
    lua_getglobal(lua.state(), "__flow_result");
    size_t length = 0;
    const char *pText = lua_tolstring(lua.state(), -1, &length);

    if (pText != nullptr)
    {
        json.assign(pText, length);
    }

    lua_pop(lua.state(), 1);
    return true;
}

bool scriptReference(const std::string &supportSource, std::string &text, std::string &errorMessage)
{
    Engine::LuaStateOwner lua;

    if (!lua.isValid())
    {
        errorMessage = "no Lua state";
        return false;
    }

    lua.openApprovedLibraries();
    lua_pushstring(lua.state(), EventFunctionNames);
    lua_setglobal(lua.state(), "__flow_known_names");
    std::optional<std::string> runError;
    // Whatever is global after the support script and was not before is the scripts' vocabulary.
    const char *const before = "__before = {} for name in pairs(_G) do __before[name] = true end";
    const char *const after = R"lua(
local helpers, selectors, enums = {}, {}, {}
for name, value in pairs(_G) do
    if not __before[name] and type(name) == "string" and name:sub(1, 2) ~= "__" then
        if type(value) == "function" then
            helpers[#helpers + 1] = name
        elseif type(value) == "number" then
            selectors[#selectors + 1] = name
        elseif type(value) == "table" and name ~= "evt" and name ~= "eventSupport" and name ~= "Game" then
            local keys, plain = {}, true
            for key, item in pairs(value) do
                if type(key) ~= "string" or type(item) ~= "number" then plain = false break end
                keys[#keys + 1] = key
            end
            if plain and #keys > 0 then
                table.sort(keys)
                local shown = #keys > 48 and (table.concat(keys, " ", 1, 48) .. " ... " .. (#keys - 48) .. " more")
                    or table.concat(keys, " ")
                enums[#enums + 1] = name .. ": " .. shown
            end
        end
    end
end
table.sort(helpers) table.sort(selectors) table.sort(enums)
__reference = "Helper functions (called without evt.):\n" .. table.concat(helpers, " ")
    .. "\n\nVariable selectors (numbers; first argument of IsAtLeast, SetValue, AddValue, SubtractValue, evt.Cmp, "
    .. "evt.Set, evt.Add, evt.Subtract):\n" .. table.concat(selectors, " ")
    .. "\n\nEnumerations (written Name.Key):\n" .. table.concat(enums, "\n")
)lua";

    if (!lua.runChunk(SandboxPrelude, "@sandbox prelude", runError) || !lua.runChunk(before, "@before", runError)
        || !lua.runChunk(supportSource, "@support script", runError) || !lua.runChunk(after, "@after", runError))
    {
        errorMessage = "the support script does not run in the sandbox: " + runError.value_or("unknown error");
        return false;
    }

    lua_getglobal(lua.state(), "__reference");
    size_t length = 0;
    const char *pText = lua_tolstring(lua.state(), -1, &length);
    text = pText != nullptr ? std::string(pText, length) : std::string();
    lua_pop(lua.state(), 1);
    return true;
}

std::vector<std::string> eventFlowProblems(const std::string &eventFlowJson, const std::vector<int> &onlyEvents)
{
    std::vector<std::string> problems;
    YAML::Node events;

    try
    {
        events = YAML::Load(eventFlowJson);
    }
    catch (const YAML::Exception &)
    {
        return problems;
    }

    for (const YAML::Node &event : events)
    {
        const int eventId = event["event"].as<int>();

        if (!onlyEvents.empty() && std::find(onlyEvents.begin(), onlyEvents.end(), eventId) == onlyEvents.end())
        {
            continue;
        }

        std::set<std::string> seen;

        for (const YAML::Node &path : event["paths"])
        {
            for (const YAML::Node &problem : path["problems"])
            {
                seen.insert(problem.Scalar());
            }

            // Only a call of something that is not a function is certainly the script's fault. Other errors
            // (arithmetic on nil ...) also come from the sandbox itself, whose game functions return nothing; 247
            // shipped maps have 460 of those and none of the kinds reported here.
            if (path["error"] && path["error"].Scalar().find("attempt to call") != std::string::npos)
            {
                seen.insert("the handler stops with a Lua error: " + path["error"].Scalar());
            }
        }

        for (const std::string &problem : seen)
        {
            problems.push_back("event " + std::to_string(eventId) + ": " + problem);
        }
    }

    return problems;
}

std::vector<AuditFinding> auditEventFlow(const std::string &eventFlowJson)
{
    std::vector<AuditFinding> findings;
    YAML::Node events;

    try
    {
        events = YAML::Load(eventFlowJson);
    }
    catch (const YAML::Exception &)
    {
        return findings;
    }

    for (const std::string &problem : eventFlowProblems(eventFlowJson, {}))
    {
        findings.push_back({
            "script.problem",
            "error",
            problem,
            "use a function of the game (oymap flow shows what the shipped handlers call) and number selectors"});
    }

    // Map variable (as written, "map_var 5") to the events that read and that set it.
    std::map<std::string, std::set<int>> readBy;
    std::map<std::string, std::set<int>> setBy;
    const auto variableOf = [](const std::string &text, size_t from) -> std::string
    {
        const size_t begin = text.find("map_var ", from);

        if (begin == std::string::npos)
        {
            return {};
        }

        size_t end = begin + 8;

        while (end < text.size() && text[end] != ' ')
        {
            ++end;
        }

        return text.substr(begin, end - begin);
    };

    for (const YAML::Node &event : events)
    {
        const int eventId = event["event"].as<int>();

        for (const YAML::Node &path : event["paths"])
        {
            for (const YAML::Node &test : path["tests"])
            {
                const std::string variable = variableOf(test["what"].Scalar(), 0);

                if (!variable.empty())
                {
                    readBy[variable].insert(eventId);
                }
            }

            for (const YAML::Node &effect : path["effects"])
            {
                const std::string &text = effect.Scalar();

                if (text.starts_with("set ") || text.starts_with("add ") || text.starts_with("subtract "))
                {
                    const std::string variable = variableOf(text, 0);

                    if (!variable.empty())
                    {
                        setBy[variable].insert(eventId);
                    }
                }
            }
        }
    }

    const auto listEvents = [](const std::set<int> &eventIds)
    {
        std::string text;

        for (const int eventId : eventIds)
        {
            text += (text.empty() ? "" : ", ") + std::to_string(eventId);
        }

        return text;
    };

    for (const std::pair<const std::string, std::set<int>> &entry : readBy)
    {
        if (!setBy.contains(entry.first))
        {
            findings.push_back({
                "state.never_set",
                "warning",
                entry.first + " is tested by event " + listEvents(entry.second)
                    + " but no handler of the map ever sets it: the test always fails",
                "set it where the handler means it to be set, or test the variable that is"});
        }
    }

    for (const std::pair<const std::string, std::set<int>> &entry : setBy)
    {
        if (!readBy.contains(entry.first))
        {
            findings.push_back({
                "state.never_read",
                "info",
                entry.first + " is set by event " + listEvents(entry.second) + " but no handler of the map tests it",
                "remove it, or test it where it was meant to matter"});
        }
    }

    return findings;
}
}
