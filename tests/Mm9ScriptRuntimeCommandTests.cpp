#include "doctest/doctest.h"

#include "game/mm9/Mm9DialogueRuntime.h"
#include "game/mm9/Mm9ScriptRuntime.h"
#include "game/party/Party.h"

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <fstream>
#include <optional>
#include <regex>
#include <set>
#include <sstream>
#include <string>

namespace
{
OpenYAMM::Game::Party makeParty()
{
    OpenYAMM::Game::PartySeed seed = {};
    seed.members.resize(1);

    OpenYAMM::Game::Party party = {};
    party.seed(seed);
    return party;
}

OpenYAMM::Game::Mm9DialoguePackage makePackage(const std::string &luaText)
{
    OpenYAMM::Game::Mm9DialoguePackage package = {};
    package.scriptRuntimeLuaText =
        "local runtime = {}\n"
        "function runtime.findLabel(script, name)\n"
        "  local direct = script.labels[name]\n"
        "  if direct ~= nil then return direct end\n"
        "  local lowered = string.lower(name)\n"
        "  for labelName, labelFunc in pairs(script.labels) do\n"
        "    if string.lower(labelName) == lowered then return labelFunc end\n"
        "  end\n"
        "  return nil\n"
        "end\n"
        "function runtime.gosub(script, ctx, name)\n"
        "  ctx:command(\"gosub\", name)\n"
        "  local labelFunc = runtime.findLabel(script, name)\n"
        "  if labelFunc ~= nil then return labelFunc(ctx) end\n"
        "  return nil\n"
        "end\n"
        "function runtime.gotoLabel(script, ctx, name)\n"
        "  ctx:command(\"goto\", name)\n"
        "  local labelFunc = runtime.findLabel(script, name)\n"
        "  if labelFunc ~= nil then return labelFunc(ctx) end\n"
        "  return nil\n"
        "end\n"
        "return runtime\n";

    OpenYAMM::Game::Mm9GeneratedKey key = {};
    key.rawId = 44;
    key.qbitId = OpenYAMM::Game::mm9KeyQbitIdForRawKey(44);
    key.aliases.push_back("TEST_KEY");
    package.keys[key.rawId] = key;

    OpenYAMM::Game::Mm9GeneratedObjectDialogueBinding binding = {};
    binding.mapId = "testmap";
    binding.objectIndex = 7;
    binding.objectClass = "Actor";
    binding.objectName = "Fixture";
    binding.rudeId = 1;
    package.objectBindings.push_back(binding);

    OpenYAMM::Game::Mm9GeneratedObjectDialogueBinding targetBinding = {};
    targetBinding.mapId = "testmap";
    targetBinding.objectIndex = 8;
    targetBinding.objectClass = "Marker";
    targetBinding.objectName = "TargetMarker";
    package.objectBindings.push_back(targetBinding);

    OpenYAMM::Game::Mm9GeneratedScriptFile script = {};
    script.source = "TEST.scr";
    script.luaPath = "scripts/TEST.lua";
    script.luaText = luaText;
    package.scripts[script.source] = script;

    return package;
}

void setOwner(OpenYAMM::Game::Mm9DialogueRuntime &runtime)
{
    OpenYAMM::Game::Mm9DialogueOwnerContext owner = {};
    owner.mapId = "testmap";
    owner.objectIndex = 7;
    owner.objectName = "Fixture";
    owner.scriptName = "TEST.scr";
    owner.scriptParams = {"1", "FixtureTarget"};
    runtime.setOwnerContext(owner);
}

bool runTestLabel(OpenYAMM::Game::Mm9ScriptRuntime &runtime, std::optional<std::string> &error)
{
    return runtime.runLabel("TEST.scr", "OnUse", error);
}

std::string trimGeneratedCommandTest(std::string text)
{
    while (!text.empty() && std::isspace(static_cast<unsigned char>(text.front())) != 0)
    {
        text.erase(text.begin());
    }
    while (!text.empty() && std::isspace(static_cast<unsigned char>(text.back())) != 0)
    {
        text.pop_back();
    }
    return text;
}

std::string lowerGeneratedCommandTest(std::string text)
{
    std::transform(
        text.begin(),
        text.end(),
        text.begin(),
        [](unsigned char character)
        {
            return static_cast<char>(std::tolower(character));
        });
    return text;
}

std::string normalizeGeneratedFallbackCommandTest(const std::string &command, const std::string &argumentsText)
{
    std::string normalizedCommand = lowerGeneratedCommandTest(trimGeneratedCommandTest(command));
    const std::string trimmedArguments = trimGeneratedCommandTest(argumentsText);
    if ((normalizedCommand.rfind("if(", 0) == 0 || normalizedCommand.rfind("while(", 0) == 0)
        && normalizedCommand.size() > 3 && normalizedCommand.back() == ')' && trimmedArguments.empty())
    {
        normalizedCommand = normalizedCommand.rfind("while(", 0) == 0 ? "while" : "if";
    }
    else if (normalizedCommand == "(if")
    {
        normalizedCommand = "if";
    }

    if (normalizedCommand.size() > 1 && normalizedCommand.back() == '(')
    {
        normalizedCommand.pop_back();
    }
    return normalizedCommand;
}

std::string readGeneratedScriptTextTest(const std::filesystem::path &path)
{
    std::ifstream input(path, std::ios::binary);
    REQUIRE(input.is_open());
    std::ostringstream stream;
    stream << input.rdbuf();
    return stream.str();
}

const std::set<std::string> &implementedGeneratedFallbackCommandsTest()
{
    static const std::set<std::string> commands = {
        "@m", "add", "addenemy", "addfriend",
        "addmodelkey", "addnpc", "addtrigger", "aigetdistance",
        "arrayget", "arrayput", "attachprop", "attack",
        "aware", "blendanim", "breakobjectlink", "breakpoint",
        "cacheclientfx", "cachescript", "cachesound", "cachetexture",
        "calcdist", "calcrotationrate", "canattack", "canrangeattack",
        "canreachobject", "canreachtarget", "castray", "checkworldcollision",
        "clearcondition", "clearflag", "consolecommand", "converse",
        "cos", "cprint", "createfx", "createobjectlink",
        "damage", "debugout", "detachprop", "die",
        "div", "divide", "docallback", "doclientfx",
        "dohighscore", "doletter", "dont_include_this_file", "dorude",
        "else", "endif", "endwhile", "estimaterangeattackhit",
        "exit", "exitscript", "facedir", "faceobject",
        "facepos", "findhidingplace", "findtargets", "getangletopos",
        "getanimname", "getanimnbr", "getattribute", "getclassname",
        "getconsolenumvar", "getconsolestrvar", "getcontainer", "getcontainercount",
        "getcrossproduct", "getcurranim", "getdims", "getdistance",
        "getfacedir", "getforwarddir", "getgametime", "getleftdir",
        "getliquidcontainer", "getmyhandle", "getobjecthandle", "getobjecthandlebyrudeid",
        "getobjectminmax", "getobjectname", "getobjects", "getobjecttarget",
        "getparam", "getpclevel", "getpcvoice", "getplayerhandle",
        "getplayerid", "getplayernbr", "getplayerswithindist", "getpos",
        "getrandomfloat", "getrandomint", "getreversedir", "getrightdir",
        "getrotation", "getsocketpos", "getsoundduration", "getstat",
        "getstatstr", "gettarget", "gettime", "getvelocity",
        "giveattribute", "giveexp", "givegold", "giveitem",
        "givekey", "givepromo", "gosub", "goto",
        "hasgold", "hasitem", "haskey", "hasrangeattack",
        "heal", "help", "hidepiece", "if",
        "isactor", "isai", "isattacking", "isclass",
        "isclearshot", "isdead", "isfacing", "isfear",
        "isfriend", "isinnorunzone", "ismoving", "isobjectactive",
        "isonground", "isplayer", "issounddone", "istargetinrange",
        "isturnbased", "isvisible", "isworldobject", "jump",
        "killcallback", "killsound", "land", "launch",
        "letterbox", "loopanim", "mod", "movedir",
        "movetopos", "mul", "multiply", "normalizevector",
        "onalert", "onattackready", "onavoidingobstacle", "oncachefiles",
        "oncongestion", "ondamage", "ondamagedone", "ondeath",
        "ondeathdone", "ondoor", "onenrage", "onenragedone",
        "onfear", "onfeardone", "onfoundplayer", "onfoundtarget",
        "onhelp", "onlosttarget", "onobjectlinkbroken", "onobstacle",
        "onobstacleavoided", "onpathclear", "onplayerinterrupt", "onpostminisaveload",
        "onpostsaveload", "onpoststartworld", "onprojectile", "onrudeexit",
        "onstuck", "onstuckdone", "ontargetbeyonddist", "ontargetdead",
        "ontargethit", "ontargetoutofrange", "ontargetwithindist", "ontouchnotify",
        "onworldswitch", "pausewait", "playanim", "playanimation",
        "playanimsound", "playsound", "playsoundhandle", "rangeattack",
        "removeenemy", "removefriend", "removemodelkey", "removenpc",
        "removeobject", "removetrigger", "restorepath", "resumewait",
        "rollovertext", "rotate", "rotatedir", "run",
        "runscript", "runto", "runtopos", "savepath",
        "screenfadein", "screenfadeout", "sendalert", "set",
        "setanimplaying", "setcallback", "setcondition", "setconsolenumvar",
        "setconsolestrvar", "setcrouch", "setflag", "setidle",
        "setint", "setmodelfilenames", "setparam", "setpos",
        "setpropnumber", "setpropstring", "setpushback", "setrotation",
        "setstat", "setstuck", "settargetlosttime", "setvelocity",
        "shouldrunaway", "sin", "spawn", "spawn2",
        "speak", "stop", "strafe", "sub",
        "subtract", "takegold", "takeitem", "takekey",
        "target", "taunt", "traceoff", "traceon",
        "trigger", "turnleft", "vecadd", "vecangle",
        "veccross", "vecdist", "vecmag", "vecnorm",
        "vecscale", "vecsub", "wait", "walk",
        "walkto", "walktopos", "while",
    };
    return commands;
}
}

TEST_CASE("MM9 script runtime executes pure generic commands without world services")
{
    const std::string luaText =
        "local script = { labels = {} }\n"
        "script.labels[\"OnUse\"] = function(ctx)\n"
        "  ctx:command(\"set\", \"bACTIII FALSE\", { line = 1, raw = \"set bACTIII FALSE\" })\n"
        "  ctx:command(\"g_nTemp\", \"= 1 + 2 * 3\", { line = 2, raw = \"g_nTemp = 1 + 2 * 3\" })\n"
        "  ctx:command(\"Add\", \"g_nTemp, 3\", { line = 3, raw = \"Add g_nTemp, 3\" })\n"
        "  ctx:command(\"Mul\", \"g_nTemp, 2\", { line = 4, raw = \"Mul g_nTemp, 2\" })\n"
        "  ctx:command(\"Div\", \"g_nTemp, 4\", { line = 5, raw = \"Div g_nTemp, 4\" })\n"
        "  ctx:command(\"set\", \"sMonsterA Orc\", { line = 6, raw = \"set sMonsterA Orc\" })\n"
        "  ctx:command(\"sMiniMonsterA\", \"= sMonsterA + Script\", "
        "{ line = 7, raw = \"sMiniMonsterA = sMonsterA + Script\" })\n"
        "  ctx:command(\"ArrayPut\", \"spSounds, 0, sounds\\\\Weapons\\\\nmetalhollow.wav\", "
        "{ line = 8, raw = \"ArrayPut spSounds, 0, sounds\\\\Weapons\\\\nmetalhollow.wav\" })\n"
        "  ctx:command(\"ArrayGet\", \"spSounds, 0, sTemp\", { line = 9, raw = \"ArrayGet spSounds, 0, sTemp\" })\n"
        "  ctx:command(\"GetRandomInt\", \"2, 2, nRandom\", { line = 10, raw = \"GetRandomInt 2, 2, nRandom\" })\n"
        "  ctx:command(\"GetRandomFloat\", \"1, 1, nRandomFloat\", "
        "{ line = 11, raw = \"GetRandomFloat 1, 1, nRandomFloat\" })\n"
        "  ctx:command(\"GetTime\", \"nTime\", { line = 12, raw = \"GetTime nTime\" })\n"
        "  ctx:command(\"Debugout\", \"sTemp\", { line = 13, raw = \"Debugout sTemp\" })\n"
        "  ctx:command(\"cprint\", \"sTemp\", { line = 14, raw = \"cprint sTemp\" })\n"
        "end\n"
        "return script\n";

    OpenYAMM::Game::Party party = makeParty();
    OpenYAMM::Game::Mm9DialoguePackage package = makePackage(luaText);
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    setOwner(dialogueRuntime);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    std::optional<std::string> error;
    REQUIRE(runTestLabel(scriptRuntime, error));
    CHECK_FALSE(error.has_value());
    CHECK(scriptRuntime.unimplementedCommands().empty());
    CHECK(scriptRuntime.getScriptNumVar("bACTIII", -1) == 0);
    CHECK(scriptRuntime.getScriptNumVar("g_nTemp", -1) == 5);
    CHECK(scriptRuntime.getScriptStrVar("sMiniMonsterA") == "OrcScript");
    CHECK(scriptRuntime.getScriptStrVar("sTemp") == "sounds\\Weapons\\nmetalhollow.wav");
    CHECK(scriptRuntime.getScriptNumVar("nRandom", -1) == 2);
    CHECK(scriptRuntime.getScriptNumVar("nRandomFloat", -1) == 1);
    CHECK(scriptRuntime.getScriptNumVar("nTime", -1) == 0);

    OpenYAMM::Game::Mm9ScriptRuntime restoredRuntime(package, dialogueRuntime);
    restoredRuntime.restoreState(scriptRuntime.state());
    CHECK(restoredRuntime.getScriptStrVar("sTemp") == "sounds\\Weapons\\nmetalhollow.wav");
}

TEST_CASE("MM9 script runtime writes source destination variables for direct query commands")
{
    const std::string luaText =
        "local script = { labels = {} }\n"
        "script.labels[\"OnUse\"] = function(ctx)\n"
        "  ctx:giveKey(\"TEST_KEY\", { line = 1, args = \"TEST_KEY\", raw = \"GiveKey TEST_KEY\" })\n"
        "  ctx:hasKey(\"TEST_KEY\", { line = 2, args = \"TEST_KEY, key_out\", raw = \"HasKey TEST_KEY, key_out\" })\n"
        "  ctx:giveItem(197, { line = 3, args = \"197\", raw = \"GiveItem 197\" })\n"
        "  ctx:hasItem(197, { line = 4, args = \"197 item_out\", raw = \"HasItem 197 item_out\" })\n"
        "  ctx:setConsoleNumVar(\"SCORE\", { line = 5, args = \"SCORE, 7\", raw = \"SetConsoleNumVar SCORE, 7\" })\n"
        "  ctx:getConsoleNumVar(\"SCORE\", "
        "{ line = 6, args = \"SCORE, score_out\", raw = \"GetConsoleNumVar SCORE, score_out\" })\n"
        "  ctx:setConsoleStrVar(\"GREETING\", "
        "{ line = 7, args = \"GREETING, \\\"hello\\\"\", raw = \"SetConsoleStrVar GREETING, \\\"hello\\\"\" })\n"
        "  ctx:getConsoleStrVar(\"GREETING\", "
        "{ line = 8, args = \"GREETING, greeting_out\", raw = \"GetConsoleStrVar GREETING, greeting_out\" })\n"
        "  ctx:getParam(0, { line = 9, args = \"0, npc_id\", raw = \"GetParam 0, npc_id\" })\n"
        "  ctx:getParam(1, { line = 10, args = \"1, target_name\", raw = \"GetParam 1, target_name\" })\n"
        "  ctx:getObjectHandleByRudeId(\"npc_id\", "
        "{ line = 11, args = \"npc_id, npc_object\", raw = \"GetObjectHandleByRUDEID npc_id, npc_object\" })\n"
        "  ctx:giveKey(\"\", { line = 12, args = \", 47\", raw = \"GiveKey , 47\" })\n"
        "  ctx:command(\"Set\", \"item_id 250\", { line = 13, raw = \"Set item_id 250\" })\n"
        "  ctx:giveItem(\"item_id\", { line = 14, raw = \"GiveItem item_id\" })\n"
        "  ctx:hasItem(\"item_id\", { line = 15, raw = \"HasItem item_id\" })\n"
        "  ctx:takeItem(\"item_id\", { line = 16, raw = \"TakeItem item_id\" })\n"
        "end\n"
        "return script\n";

    OpenYAMM::Game::Party party = makeParty();
    OpenYAMM::Game::Mm9DialoguePackage package = makePackage(luaText);
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    setOwner(dialogueRuntime);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    std::optional<std::string> error;
    REQUIRE(runTestLabel(scriptRuntime, error));
    CHECK_FALSE(error.has_value());
    CHECK(scriptRuntime.unimplementedCommands().empty());
    CHECK(scriptRuntime.getScriptNumVar("key_out", -1) == 1);
    CHECK(scriptRuntime.getScriptNumVar("item_out", -1) == 1);
    CHECK(scriptRuntime.getScriptNumVar("score_out", -1) == 7);
    CHECK(scriptRuntime.getScriptStrVar("greeting_out") == "hello");
    CHECK(scriptRuntime.getScriptNumVar("npc_id", -1) == 1);
    CHECK(scriptRuntime.getScriptStrVar("target_name") == "FixtureTarget");
    CHECK(scriptRuntime.getObjectHandleVar("npc_object") == "mm9:testmap:object:7");
    CHECK(dialogueRuntime.party().inventoryItemCount(250) == 0);

    const std::vector<OpenYAMM::Game::Mm9ScriptRuntimeKeyAccess> &keyAccesses = scriptRuntime.keyAccesses();
    REQUIRE(keyAccesses.size() >= 3);
    CHECK(keyAccesses.back().operation == "giveKey");
    CHECK(keyAccesses.back().rawKeyId == 47);
    const std::vector<OpenYAMM::Game::Mm9ScriptRuntimePartyAccess> &partyAccesses = scriptRuntime.partyAccesses();
    REQUIRE(partyAccesses.size() >= 4);
    CHECK(partyAccesses[partyAccesses.size() - 3].operation == "giveItem");
    CHECK(partyAccesses[partyAccesses.size() - 3].id == 250);
    CHECK(partyAccesses[partyAccesses.size() - 2].operation == "hasItem");
    CHECK(partyAccesses[partyAccesses.size() - 2].id == 250);
    CHECK(partyAccesses[partyAccesses.size() - 1].operation == "takeItem");
    CHECK(partyAccesses[partyAccesses.size() - 1].id == 250);
}

TEST_CASE("MM9 script runtime tracks trigger replacement removal and dispatch")
{
    const std::string luaText =
        "local script = { labels = {} }\n"
        "script.labels[\"OnUse\"] = function(ctx)\n"
        "  ctx:addTrigger(\"Use\", { line = 1, args = \"Use, First\", raw = \"AddTrigger Use, First\" })\n"
        "  ctx:addTrigger(\"Use\", { line = 2, args = \"Use, Second\", raw = \"AddTrigger Use, Second\" })\n"
        "  ctx:command(\"RemoveTrigger\", \"Use\", { line = 3, raw = \"RemoveTrigger Use\" })\n"
        "  ctx:addTrigger(\"Use\", { line = 4, args = \"Use, Final\", raw = \"AddTrigger Use, Final\" })\n"
        "  ctx:trigger(\"hMe\", { line = 5, args = \"hMe, Use\", raw = \"Trigger hMe, Use\" })\n"
        "end\n"
        "return script\n";

    OpenYAMM::Game::Party party = makeParty();
    OpenYAMM::Game::Mm9DialoguePackage package = makePackage(luaText);
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    setOwner(dialogueRuntime);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    std::optional<std::string> error;
    REQUIRE(runTestLabel(scriptRuntime, error));
    CHECK_FALSE(error.has_value());
    CHECK(scriptRuntime.unimplementedCommands().empty());

    const OpenYAMM::Game::Mm9ScriptRuntimeState &state = scriptRuntime.state();
    REQUIRE(state.triggers.size() == 1);
    CHECK(state.triggers[0].triggerName == "Use");
    CHECK(state.triggers[0].label == "Final");
    REQUIRE(state.triggerDispatches.size() == 1);
    CHECK(state.triggerDispatches[0].targetHandle == "mm9:testmap:object:7");
    CHECK(state.triggerDispatches[0].message == "Use");
}

TEST_CASE("MM9 script runtime dispatches registered trigger labels across package objects")
{
    const std::string sourceLuaText =
        "local script = { labels = {} }\n"
        "script.labels[\"OnUse\"] = function(ctx)\n"
        "  ctx:command(\"GetObjectHandle\", \"TargetMarker, hTarget\", "
        "{ line = 1, raw = \"GetObjectHandle TargetMarker, hTarget\" })\n"
        "  ctx:trigger(\"hTarget\", { line = 2, args = \"hTarget, Activate\", raw = \"Trigger hTarget, Activate\" })\n"
        "end\n"
        "return script\n";
    const std::string targetLuaText =
        "local script = { labels = {} }\n"
        "script.labels[\"OnUse\"] = function(ctx)\n"
        "  ctx:addTrigger(\"Activate\", "
        "{ line = 1, args = \"Activate, OnActivate\", raw = \"AddTrigger Activate, OnActivate\" })\n"
        "end\n"
        "script.labels[\"OnActivate\"] = function(ctx)\n"
        "  ctx:command(\"set\", \"g_nTriggered 1\", { line = 2, raw = \"set g_nTriggered 1\" })\n"
        "  ctx:command(\"GetMyHandle\", \"hTriggeredOwner\", { line = 3, raw = \"GetMyHandle hTriggeredOwner\" })\n"
        "end\n"
        "return script\n";

    OpenYAMM::Game::Party party = makeParty();
    OpenYAMM::Game::Mm9DialoguePackage package = makePackage(sourceLuaText);

    OpenYAMM::Game::Mm9GeneratedScriptFile targetScript = {};
    targetScript.source = "TARGET.scr";
    targetScript.luaPath = "scripts/TARGET.lua";
    targetScript.luaText = targetLuaText;
    package.scripts[targetScript.source] = targetScript;

    REQUIRE(package.objectBindings.size() >= 2);
    package.objectBindings[1].scriptName = "TARGET.scr";
    package.objectBindings[1].scriptSourceExists = true;

    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    OpenYAMM::Game::Mm9DialogueOwnerContext targetOwner = {};
    targetOwner.mapId = "testmap";
    targetOwner.objectIndex = 8;
    targetOwner.objectName = "TargetMarker";
    targetOwner.scriptName = "TARGET.scr";
    dialogueRuntime.setOwnerContext(targetOwner);

    std::optional<std::string> error;
    REQUIRE(scriptRuntime.runLabel("TARGET.scr", "OnUse", error));
    CHECK_FALSE(error.has_value());
    REQUIRE(scriptRuntime.state().triggers.size() == 1);
    CHECK(scriptRuntime.state().triggers[0].mapId == "testmap");
    CHECK(scriptRuntime.state().triggers[0].objectIndex == 8);
    CHECK(scriptRuntime.state().triggers[0].triggerName == "Activate");

    setOwner(dialogueRuntime);
    REQUIRE(runTestLabel(scriptRuntime, error));
    CHECK_FALSE(error.has_value());
    CHECK(scriptRuntime.unimplementedCommands().empty());
    CHECK(scriptRuntime.getScriptNumVar("g_nTriggered", 0) == 1);
    CHECK(scriptRuntime.getObjectHandleVar("hTriggeredOwner") == "mm9:testmap:object:8");
    REQUIRE(scriptRuntime.state().triggerDispatches.size() == 1);
    CHECK(scriptRuntime.state().triggerDispatches[0].targetHandle == "mm9:testmap:object:8");
    CHECK(scriptRuntime.state().triggerDispatches[0].message == "Activate");
    CHECK(dialogueRuntime.owner().objectIndex == 7);
}

TEST_CASE("MM9 script runtime resolves package backed object commands without DAT world services")
{
    const std::string luaText =
        "local script = { labels = {} }\n"
        "script.labels[\"OnUse\"] = function(ctx)\n"
        "  ctx:command(\"GetMyHandle\", \"hMe\", { line = 1, raw = \"GetMyHandle hMe\" })\n"
        "  ctx:command(\"GetPlayerHandle\", \"hPlayer\", { line = 2, raw = \"GetPlayerHandle hPlayer\" })\n"
        "  ctx:command(\"GetObjectHandle\", \"TargetMarker, hTarget\", "
        "{ line = 3, raw = \"GetObjectHandle TargetMarker, hTarget\" })\n"
        "  ctx:command(\"GetClassName\", \"hTarget, sClass\", "
        "{ line = 4, raw = \"GetClassName hTarget, sClass\" })\n"
        "  ctx:command(\"GetObjectName\", \"hTarget, sName\", "
        "{ line = 5, raw = \"GetObjectName hTarget, sName\" })\n"
        "  ctx:command(\"IsClass\", \"hTarget, Marker, bMarker\", "
        "{ line = 6, raw = \"IsClass hTarget, Marker, bMarker\" })\n"
        "  ctx:command(\"IsPlayer\", \"hPlayer, bPlayer\", "
        "{ line = 7, raw = \"IsPlayer hPlayer, bPlayer\" })\n"
        "  ctx:command(\"Target\", \"hTarget, TRUE\", { line = 8, raw = \"Target hTarget, TRUE\" })\n"
        "  ctx:command(\"GetTarget\", \"hTargetOut\", { line = 9, raw = \"GetTarget hTargetOut\" })\n"
        "  ctx:command(\"SetStat\", \"hMe, FlyVel, 42\", { line = 10, raw = \"SetStat hMe, FlyVel, 42\" })\n"
        "  ctx:command(\"GetStat\", \"hMe, FlyVel, nFlyVel\", { line = 11, raw = \"GetStat hMe, FlyVel, nFlyVel\" })\n"
        "  ctx:command(\"SetFlag\", \"hMe, FLAG_SOLID\", { line = 12, raw = \"SetFlag hMe, FLAG_SOLID\" })\n"
        "  ctx:command(\"ClearFlag\", \"hMe, FLAG_GOTHRUWORLD\", "
        "{ line = 13, raw = \"ClearFlag hMe, FLAG_GOTHRUWORLD\" })\n"
        "  ctx:command(\"RemoveObject\", \"hTarget\", { line = 14, raw = \"RemoveObject hTarget\" })\n"
        "end\n"
        "return script\n";

    OpenYAMM::Game::Party party = makeParty();
    OpenYAMM::Game::Mm9DialoguePackage package = makePackage(luaText);
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    setOwner(dialogueRuntime);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    std::optional<std::string> error;
    REQUIRE(runTestLabel(scriptRuntime, error));
    CHECK_FALSE(error.has_value());
    CHECK(scriptRuntime.unimplementedCommands().empty());
    CHECK(scriptRuntime.getObjectHandleVar("hMe") == "mm9:testmap:object:7");
    CHECK(scriptRuntime.getObjectHandleVar("hPlayer") == "mm9:player");
    CHECK(scriptRuntime.getObjectHandleVar("hTarget") == "mm9:testmap:object:8");
    CHECK(scriptRuntime.getScriptStrVar("sClass") == "Marker");
    CHECK(scriptRuntime.getScriptStrVar("sName") == "TargetMarker");
    CHECK(scriptRuntime.getScriptNumVar("bMarker", 0) == 1);
    CHECK(scriptRuntime.getScriptNumVar("bPlayer", 0) == 1);
    CHECK(scriptRuntime.getObjectHandleVar("hTargetOut") == "mm9:testmap:object:8");
    CHECK(scriptRuntime.getScriptNumVar("nFlyVel", 0) == 42);

    const OpenYAMM::Game::Mm9ScriptRuntimeState &state = scriptRuntime.state();
    REQUIRE(state.objectFlags.count("mm9:testmap:object:7") == 1);
    CHECK(state.objectFlags.at("mm9:testmap:object:7").at("FLAG_SOLID") == 1);
    CHECK(state.objectFlags.at("mm9:testmap:object:7").at("FLAG_GOTHRUWORLD") == 0);
    CHECK(state.removedObjects.at("mm9:testmap:object:8"));

    OpenYAMM::Game::Mm9ScriptRuntime restoredRuntime(package, dialogueRuntime);
    restoredRuntime.restoreState(state);
    CHECK(restoredRuntime.state().objectStats.at("mm9:testmap:object:7").at("FlyVel") == 42);
    CHECK(restoredRuntime.state().removedObjects.at("mm9:testmap:object:8"));
}

TEST_CASE("MM9 script runtime removes object callbacks links and pending schedules")
{
    const std::string luaText =
        "local script = { labels = {} }\n"
        "script.labels[\"OnUse\"] = function(ctx)\n"
        "  ctx:command(\"GetMyHandle\", \"hMe\", { line = 1, raw = \"GetMyHandle hMe\" })\n"
        "  ctx:command(\"GetObjectHandle\", \"TargetMarker, hTarget\", "
        "{ line = 2, raw = \"GetObjectHandle TargetMarker, hTarget\" })\n"
        "  ctx:addTrigger(\"Use\", { line = 3, args = \"Use, OnTriggered\", raw = \"AddTrigger Use, OnTriggered\" })\n"
        "  ctx:command(\"OnDamage\", \"OnDamageLabel\", { line = 4, raw = \"OnDamage OnDamageLabel\" })\n"
        "  ctx:command(\"SetCallBack\", \"10, OnDamageLabel\", { line = 5, raw = \"SetCallBack 10, OnDamageLabel\" })\n"
        "  ctx:command(\"Wait\", \"9, 9, OnTriggered\", { line = 6, raw = \"Wait 9, 9, OnTriggered\" })\n"
        "  ctx:command(\"CreateObjectLink\", \"hTarget\", { line = 7, raw = \"CreateObjectLink hTarget\" })\n"
        "  ctx:command(\"RemoveObject\", \"hMe\", { line = 8, raw = \"RemoveObject hMe\" })\n"
        "end\n"
        "script.labels[\"OnTriggered\"] = function(ctx)\n"
        "  ctx:command(\"set\", \"triggered_after_remove 1\", { line = 9, raw = \"set triggered_after_remove 1\" })\n"
        "end\n"
        "script.labels[\"OnDamageLabel\"] = function(ctx)\n"
        "  ctx:command(\"set\", \"damage_after_remove 1\", { line = 10, raw = \"set damage_after_remove 1\" })\n"
        "end\n"
        "return script\n";

    OpenYAMM::Game::Party party = makeParty();
    OpenYAMM::Game::Mm9DialoguePackage package = makePackage(luaText);
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    setOwner(dialogueRuntime);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    std::optional<std::string> error;
    REQUIRE(runTestLabel(scriptRuntime, error));
    CHECK_FALSE(error.has_value());
    CHECK(scriptRuntime.unimplementedCommands().empty());

    const std::string activeHandle = "mm9:testmap:object:7";
    CHECK(scriptRuntime.state().removedObjects.at(activeHandle));
    CHECK(scriptRuntime.state().objectLinks.count(activeHandle) == 0);
    CHECK(scriptRuntime.state().triggers.empty());
    CHECK(scriptRuntime.state().scheduledInvocations.empty());
    CHECK(scriptRuntime.state().registeredCallbacks.empty());
    CHECK(scriptRuntime.registeredCallbacks().empty());

    size_t dispatchedCount = 99;
    REQUIRE(scriptRuntime.dispatchRegisteredCallbacks("ondamage", "", "testmap", 7, error, dispatchedCount));
    CHECK(dispatchedCount == 0);
    REQUIRE(scriptRuntime.advanceScriptTime(20.0, error));
    CHECK(scriptRuntime.getScriptNumVar("triggered_after_remove", 0) == 0);
    CHECK(scriptRuntime.getScriptNumVar("damage_after_remove", 0) == 0);
}

TEST_CASE("MM9 script runtime records presentation audio animation and callback commands")
{
    const std::string luaText =
        "local script = { labels = {} }\n"
        "script.labels[\"OnUse\"] = function(ctx)\n"
        "  ctx:command(\"CacheSound\", \"\\\"sounds\\\\animsounds\\\\aware.wav\\\"\", "
        "{ line = 1, raw = \"CacheSound \\\"sounds\\\\animsounds\\\\aware.wav\\\"\" })\n"
        "  ctx:command(\"PlaySound\", "
        "\"sounds\\\\AnimSounds\\\\evileyeflap.wav, OnSoundDone, 1000, 400, FALSE, 90\", "
        "{ line = 2, raw = \"PlaySound sounds\\\\AnimSounds\\\\evileyeflap.wav OnSoundDone 1000 400 FALSE 90\" })\n"
        "  ctx:command(\"PlaySoundHandle\", "
        "\"voices\\\\cinema\\\\ake01.wav, soundhandle, 768, FALSE, 100\", "
        "{ line = 3, raw = \"PlaySoundHandle voices\\\\cinema\\\\ake01.wav, soundhandle, 768, FALSE, 100\" })\n"
        "  ctx:command(\"GetSoundDuration\", \", soundhandle, sounddur\", "
        "{ line = 4, raw = \"GetSoundDuration , soundhandle, sounddur\" })\n"
        "  ctx:command(\"KillSound\", \"soundhandle\", { line = 5, raw = \"KillSound soundhandle\" })\n"
        "  ctx:command(\"PlayAnim\", \"Taunt, StartSequence\", "
        "{ line = 6, raw = \"PlayAnim Taunt, StartSequence\" })\n"
        "  ctx:command(\"LoopAnim\", \"Hang, 0, CheckTrigger\", "
        "{ line = 7, raw = \"LoopAnim Hang, 0, CheckTrigger\" })\n"
        "  ctx:command(\"CacheClientFX\", \"SPELL_BLACKSMOKE\", "
        "{ line = 8, raw = \"CacheClientFX SPELL_BLACKSMOKE\" })\n"
        "  ctx:command(\"DoClientFX\", \"hMe, SPELL_BLACKSMOKE, TRUE, TRUE\", "
        "{ line = 9, raw = \"DoClientFX hMe, SPELL_BLACKSMOKE, TRUE, TRUE\" })\n"
        "  ctx:command(\"ScreenFadeOut\", \"1\", { line = 10, raw = \"ScreenFadeOut 1\" })\n"
        "  ctx:command(\"ScreenFadeIn\", \"1\", { line = 11, raw = \"ScreenFadeIn 1\" })\n"
        "  ctx:command(\"LetterBox\", \"True\", { line = 12, raw = \"LetterBox True\" })\n"
        "  ctx:command(\"RolloverText\", \"150, 1, 5000, 4000\", "
        "{ line = 13, raw = \"RolloverText 150, 1, 5000, 4000\" })\n"
        "  ctx:command(\"OnDamage\", \"OnDamage\", { line = 14, raw = \"OnDamage OnDamage\" })\n"
        "  ctx:command(\"OnTargetBeyondDist\", \"g_nMaxEvadeDist, BeAggressive\", "
        "{ line = 15, raw = \"OnTargetBeyondDist g_nMaxEvadeDist, BeAggressive\" })\n"
        "  ctx:command(\"AddModelKey\", \"DoResurrection, DoResurrectionTrigger\", "
        "{ line = 16, raw = \"AddModelKey DoResurrection, DoResurrectionTrigger\" })\n"
        "  ctx:command(\"SetCallBack\", \"0, OnZoomWait\", "
        "{ line = 17, raw = \"SetCallBack 0, OnZoomWait\" })\n"
        "end\n"
        "return script\n";

    OpenYAMM::Game::Party party = makeParty();
    OpenYAMM::Game::Mm9DialoguePackage package = makePackage(luaText);
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    setOwner(dialogueRuntime);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    std::optional<std::string> error;
    REQUIRE(runTestLabel(scriptRuntime, error));
    CHECK_FALSE(error.has_value());
    CHECK(scriptRuntime.unimplementedCommands().empty());
    CHECK(scriptRuntime.getSoundHandleVar("soundhandle") == "mm9:sound:1");
    CHECK(scriptRuntime.getScriptNumVar("sounddur", -1) == 0);
    CHECK(scriptRuntime.state().activeSoundHandles.empty());

    const std::vector<OpenYAMM::Game::Mm9ScriptRuntimeAudioRequest> &audioRequests =
        scriptRuntime.audioRequests();
    REQUIRE(audioRequests.size() == 5);
    CHECK(audioRequests[0].operation == "cachesound");
    CHECK(audioRequests[0].soundName == "sounds\\animsounds\\aware.wav");
    CHECK(audioRequests[1].operation == "playsound");
    CHECK(audioRequests[1].callbackLabel == "OnSoundDone");
    CHECK(audioRequests[1].radius == 1000);
    CHECK(audioRequests[2].operation == "playsoundhandle");
    CHECK(audioRequests[2].soundHandle == "mm9:sound:1");
    CHECK(audioRequests[4].operation == "killsound");

    const std::vector<OpenYAMM::Game::Mm9ScriptRuntimeAnimationRequest> &animationRequests =
        scriptRuntime.animationRequests();
    REQUIRE(animationRequests.size() == 2);
    CHECK(animationRequests[0].animationName == "Taunt");
    CHECK(animationRequests[0].callbackLabel == "StartSequence");
    CHECK(animationRequests[1].operation == "loopanim");
    CHECK(animationRequests[1].callbackLabel == "CheckTrigger");

    const std::vector<OpenYAMM::Game::Mm9ScriptRuntimeClientFxRequest> &clientFxRequests =
        scriptRuntime.clientFxRequests();
    REQUIRE(clientFxRequests.size() == 2);
    CHECK(clientFxRequests[0].operation == "cacheclientfx");
    CHECK(clientFxRequests[0].effectName == "SPELL_BLACKSMOKE");
    CHECK(clientFxRequests[1].objectHandle == "mm9:testmap:object:7");
    CHECK(clientFxRequests[1].attach);
    CHECK(clientFxRequests[1].loop);

    const std::vector<OpenYAMM::Game::Mm9ScriptRuntimePresentationRequest> &presentationRequests =
        scriptRuntime.presentationRequests();
    REQUIRE(presentationRequests.size() == 4);
    CHECK(presentationRequests[0].operation == "screenfadeout");
    CHECK(presentationRequests[3].arguments.size() == 4);

    OpenYAMM::Game::Mm9ScriptRuntime restoredRuntime(package, dialogueRuntime);
    restoredRuntime.restoreState(scriptRuntime.state());
    REQUIRE(restoredRuntime.clientFxRequests().size() == 2);
    CHECK(restoredRuntime.clientFxRequests()[1].effectName == "SPELL_BLACKSMOKE");
    REQUIRE(restoredRuntime.presentationRequests().size() == 4);
    CHECK(restoredRuntime.presentationRequests()[1].operation == "screenfadein");

    const std::vector<OpenYAMM::Game::Mm9ScriptRuntimeCallback> &callbacks =
        scriptRuntime.registeredCallbacks();
    const auto hasCallback = [&](const std::string &kind, const std::string &label)
    {
        return std::any_of(
            callbacks.begin(),
            callbacks.end(),
            [&](const OpenYAMM::Game::Mm9ScriptRuntimeCallback &callback)
            {
                return callback.kind == kind && callback.label == label;
            });
    };

    CHECK(hasCallback("playsound", "OnSoundDone"));
    CHECK(hasCallback("playanim", "StartSequence"));
    CHECK(hasCallback("loopanim", "CheckTrigger"));
    CHECK(hasCallback("ondamage", "OnDamage"));
    CHECK(hasCallback("ontargetbeyonddist", "BeAggressive"));
    CHECK(hasCallback("addmodelkey", "DoResurrectionTrigger"));
    CHECK(hasCallback("setcallback", "OnZoomWait"));

    CHECK(restoredRuntime.getSoundHandleVar("soundhandle") == "mm9:sound:1");
    CHECK(restoredRuntime.audioRequests().size() == 5);
}

TEST_CASE("MM9 script runtime dispatches audio completion callbacks and sound handles")
{
    const std::string luaText =
        "local script = { labels = {} }\n"
        "script.labels[\"OnUse\"] = function(ctx)\n"
        "  ctx:command(\"PlaySound\", \"tone.wav, SoundDone, 100, 90, FALSE\", "
        "{ line = 1, raw = \"PlaySound tone.wav, SoundDone, 100, 90, FALSE\" })\n"
        "  ctx:command(\"PlaySoundHandle\", \"loop.wav, soundhandle, 100, TRUE, 90\", "
        "{ line = 2, raw = \"PlaySoundHandle loop.wav, soundhandle, 100, TRUE, 90\" })\n"
        "  ctx:command(\"IsSoundDone\", \"soundhandle, soundDoneBefore\", "
        "{ line = 3, raw = \"IsSoundDone soundhandle, soundDoneBefore\" })\n"
        "end\n"
        "script.labels[\"SoundDone\"] = function(ctx)\n"
        "  ctx:command(\"set\", \"sound_callback 1\", { line = 4, raw = \"set sound_callback 1\" })\n"
        "  ctx:command(\"GetMyHandle\", \"sound_owner\", { line = 5, raw = \"GetMyHandle sound_owner\" })\n"
        "end\n"
        "return script\n";

    OpenYAMM::Game::Party party = makeParty();
    OpenYAMM::Game::Mm9DialoguePackage package = makePackage(luaText);
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    setOwner(dialogueRuntime);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    std::optional<std::string> error;
    REQUIRE(runTestLabel(scriptRuntime, error));
    CHECK_FALSE(error.has_value());
    REQUIRE(scriptRuntime.audioRequests().size() == 3);
    REQUIRE(scriptRuntime.state().audioRequests.size() == 3);
    CHECK(scriptRuntime.getSoundHandleVar("soundhandle") == "mm9:sound:1");
    CHECK(scriptRuntime.getScriptNumVar("soundDoneBefore", 1) == 0);
    REQUIRE(scriptRuntime.state().activeSoundHandles.count("mm9:sound:1") == 1);

    OpenYAMM::Game::Mm9ScriptRuntime restoredRuntime(package, dialogueRuntime);
    restoredRuntime.restoreState(scriptRuntime.state());
    REQUIRE(restoredRuntime.audioRequests().size() == 3);
    REQUIRE(restoredRuntime.state().activeSoundHandles.count("mm9:sound:1") == 1);

    size_t dispatchedCount = 0;
    REQUIRE(restoredRuntime.dispatchAudioResult(0, "complete", error, dispatchedCount));
    CHECK(dispatchedCount == 1);
    CHECK(restoredRuntime.getScriptNumVar("sound_callback", 0) == 1);
    CHECK(restoredRuntime.getObjectHandleVar("sound_owner") == "mm9:testmap:object:7");

    REQUIRE(restoredRuntime.dispatchAudioResult(1, "complete", error, dispatchedCount));
    CHECK(dispatchedCount == 0);
    CHECK(restoredRuntime.state().activeSoundHandles.count("mm9:sound:1") == 0);
    REQUIRE(restoredRuntime.executeCommand("IsSoundDone", "soundhandle, soundDoneAfter", 6, "IsSoundDone"));
    CHECK(restoredRuntime.getScriptNumVar("soundDoneAfter", 0) == 1);
}

TEST_CASE("MM9 script runtime records transform movement spawn and script switch commands")
{
    const std::string luaText =
        "local script = { labels = {} }\n"
        "script.labels[\"OnUse\"] = function(ctx)\n"
        "  ctx:command(\"GetMyHandle\", \"hMe\", { line = 1, raw = \"GetMyHandle hMe\" })\n"
        "  ctx:command(\"SetPos\", \"hMe, 10, 20, 30\", { line = 2, raw = \"SetPos hMe, 10, 20, 30\" })\n"
        "  ctx:command(\"GetPOS\", \"hMe, xMe, yMe, zMe\", { line = 3, raw = \"GetPOS hMe, xMe,yMe,zMe\" })\n"
        "  ctx:command(\"FaceDir\", \"1, 0, 0, 0\", { line = 4, raw = \"FaceDir 1,0,0,0\" })\n"
        "  ctx:command(\"GetFaceDir\", \"hMe, dx, dy, dz\", "
        "{ line = 5, raw = \"GetFaceDir hMe, dx,dy,dz\" })\n"
        "  ctx:command(\"RotateDir\", \"dx, dy, dz, 90\", { line = 6, raw = \"RotateDir dx,dy,dz,90\" })\n"
        "  ctx:command(\"MoveToPos\", \"50, 60, 70, 500, UpdatePOS\", "
        "{ line = 7, raw = \"MoveToPos 50,60,70,500,UpdatePOS\" })\n"
        "  ctx:command(\"WalkTo\", \"hMe, 1, OnWalk\", { line = 8, raw = \"WalkTo hMe, 1, OnWalk\" })\n"
        "  ctx:command(\"RunTo\", \"hMe, 128, OnArrive\", { line = 9, raw = \"RunTo hMe, 128, OnArrive\" })\n"
        "  ctx:command(\"MoveDir\", \"dx, dy, dz, 10, 20, CameraOff\", "
        "{ line = 10, raw = \"MoveDir dx,dy,dz,10,20,CameraOff\" })\n"
        "  ctx:command(\"FaceObject\", \"hMe, 450\", { line = 11, raw = \"FaceObject hMe, 450\" })\n"
        "  ctx:command(\"Stop\", \"\", { line = 12, raw = \"Stop\" })\n"
        "  ctx:command(\"CreateObjectLink\", \"hMe\", { line = 13, raw = \"CreateObjectLink hMe\" })\n"
        "  ctx:command(\"Spawn\", \"hCreature, 11, 12, 13, SPAWN_PARAM\", "
        "{ line = 14, raw = \"Spawn hCreature, 11, 12, 13, SPAWN_PARAM\" })\n"
        "  ctx:command(\"set\", \"g_sDefaultScript BASE.scr\", "
        "{ line = 15, raw = \"set g_sDefaultScript BASE.scr\" })\n"
        "  ctx:command(\"RunScript\", \"g_sDefaultScript\", { line = 16, raw = \"RunScript g_sDefaultScript\" })\n"
        "end\n"
        "return script\n";

    OpenYAMM::Game::Party party = makeParty();
    OpenYAMM::Game::Mm9DialoguePackage package = makePackage(luaText);
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    setOwner(dialogueRuntime);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    std::optional<std::string> error;
    REQUIRE(runTestLabel(scriptRuntime, error));
    CHECK_FALSE(error.has_value());
    CHECK(scriptRuntime.unimplementedCommands().empty());
    CHECK(scriptRuntime.getScriptNumVar("xMe", 0) == 10);
    CHECK(scriptRuntime.getScriptNumVar("yMe", 0) == 20);
    CHECK(scriptRuntime.getScriptNumVar("zMe", 0) == 30);
    CHECK(scriptRuntime.getScriptNumVar("dx", -1) == 0);
    CHECK(scriptRuntime.getScriptNumVar("dy", 0) == 1);
    CHECK(scriptRuntime.getScriptNumVar("dz", -1) == 0);
    CHECK(scriptRuntime.getObjectHandleVar("hCreature") == "mm9:spawn:1");

    const OpenYAMM::Game::Mm9ScriptRuntimeState &state = scriptRuntime.state();
    REQUIRE(state.objectPositions.count("mm9:testmap:object:7") == 1);
    CHECK(state.objectPositions.at("mm9:testmap:object:7").x == 10.0);
    REQUIRE(state.objectFaceDirs.count("mm9:testmap:object:7") == 1);
    CHECK(state.objectFaceDirs.at("mm9:testmap:object:7").x == 1.0);
    REQUIRE(state.objectLinks.count("mm9:testmap:object:7") == 1);
    CHECK(state.objectLinks.at("mm9:testmap:object:7").front() == "mm9:testmap:object:7");
    CHECK(state.objectScriptOverrides.at("mm9:testmap:object:7") == "BASE.scr");
    REQUIRE(state.spawnRequests.size() == 1);
    CHECK(state.spawnRequests[0].spawnedHandle == "mm9:spawn:1");
    CHECK(state.spawnRequests[0].position.z == 13.0);
    REQUIRE(state.movementRequests.size() == 6);
    CHECK(state.movementRequests[0].operation == "movetopos");
    CHECK(state.movementRequests[0].callbackLabel == "UpdatePOS");
    CHECK(state.movementRequests[1].targetHandle == "mm9:testmap:object:7");
    CHECK(state.movementRequests[3].operation == "movedir");
    CHECK(state.movementRequests[3].callbackLabel == "CameraOff");
    CHECK(state.movementRequests[5].operation == "stop");

    const std::vector<OpenYAMM::Game::Mm9ScriptRuntimeCallback> &callbacks =
        scriptRuntime.registeredCallbacks();
    const auto hasCallback = [&](const std::string &kind, const std::string &label)
    {
        return std::any_of(
            callbacks.begin(),
            callbacks.end(),
            [&](const OpenYAMM::Game::Mm9ScriptRuntimeCallback &callback)
            {
                return callback.kind == kind && callback.label == label;
            });
    };
    CHECK(hasCallback("movetopos", "UpdatePOS"));
    CHECK(hasCallback("walkto", "OnWalk"));
    CHECK(hasCallback("runto", "OnArrive"));
    CHECK(hasCallback("movedir", "CameraOff"));

    OpenYAMM::Game::Mm9ScriptRuntime restoredRuntime(package, dialogueRuntime);
    restoredRuntime.restoreState(state);
    REQUIRE(restoredRuntime.movementRequests().size() == 6);
    REQUIRE(restoredRuntime.spawnRequests().size() == 1);
    CHECK(restoredRuntime.spawnRequests()[0].spawnedHandle == "mm9:spawn:1");
}

TEST_CASE("MM9 script runtime dispatches movement result callbacks")
{
    const std::string luaText =
        "local script = { labels = {} }\n"
        "script.labels[\"OnUse\"] = function(ctx)\n"
        "  ctx:command(\"OnStuck\", \"OnStuckLabel\", { line = 1, raw = \"OnStuck OnStuckLabel\" })\n"
        "  ctx:command(\"OnStuckDone\", \"OnStuckDoneLabel\", { line = 2, raw = \"OnStuckDone OnStuckDoneLabel\" })\n"
        "  ctx:command(\"OnObstacle\", \"OnObstacleLabel\", { line = 3, raw = \"OnObstacle OnObstacleLabel\" })\n"
        "  ctx:command(\"OnTouchNotify\", \"OnTouchLabel\", { line = 4, raw = \"OnTouchNotify OnTouchLabel\" })\n"
        "  ctx:command(\"MoveToPos\", \"1, 2, 3, 100, OnArrived\", "
        "{ line = 5, raw = \"MoveToPos 1,2,3,100,OnArrived\" })\n"
        "  ctx:command(\"WalkTo\", \"hMe, 1, OnWalkDone\", { line = 6, raw = \"WalkTo hMe,1,OnWalkDone\" })\n"
        "end\n"
        "script.labels[\"OnArrived\"] = function(ctx)\n"
        "  ctx:command(\"set\", \"arrived 1\", { line = 7, raw = \"set arrived 1\" })\n"
        "  ctx:command(\"GetMyHandle\", \"arrival_owner\", { line = 8, raw = \"GetMyHandle arrival_owner\" })\n"
        "end\n"
        "script.labels[\"OnWalkDone\"] = function(ctx)\n"
        "  ctx:command(\"set\", \"walk_done 1\", { line = 9, raw = \"set walk_done 1\" })\n"
        "end\n"
        "script.labels[\"OnStuckLabel\"] = function(ctx)\n"
        "  ctx:command(\"set\", \"stuck_seen 1\", { line = 10, raw = \"set stuck_seen 1\" })\n"
        "end\n"
        "script.labels[\"OnStuckDoneLabel\"] = function(ctx)\n"
        "  ctx:command(\"set\", \"stuck_done_seen 1\", { line = 11, raw = \"set stuck_done_seen 1\" })\n"
        "end\n"
        "script.labels[\"OnObstacleLabel\"] = function(ctx)\n"
        "  ctx:command(\"set\", \"obstacle_seen 1\", { line = 12, raw = \"set obstacle_seen 1\" })\n"
        "end\n"
        "script.labels[\"OnTouchLabel\"] = function(ctx)\n"
        "  ctx:command(\"set\", \"touch_seen 1\", { line = 13, raw = \"set touch_seen 1\" })\n"
        "end\n"
        "return script\n";

    OpenYAMM::Game::Party party = makeParty();
    OpenYAMM::Game::Mm9DialoguePackage package = makePackage(luaText);
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    setOwner(dialogueRuntime);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    std::optional<std::string> error;
    REQUIRE(runTestLabel(scriptRuntime, error));
    CHECK_FALSE(error.has_value());
    REQUIRE(scriptRuntime.state().movementRequests.size() == 2);

    size_t dispatchedCount = 0;
    REQUIRE(scriptRuntime.dispatchMovementResult(0, "arrived", error, dispatchedCount));
    CHECK(dispatchedCount == 1);
    CHECK(scriptRuntime.getScriptNumVar("arrived", 0) == 1);
    CHECK(scriptRuntime.getObjectHandleVar("arrival_owner") == "mm9:testmap:object:7");

    REQUIRE(scriptRuntime.dispatchMovementResult(1, "stuck", error, dispatchedCount));
    CHECK(dispatchedCount == 2);
    CHECK(scriptRuntime.getScriptNumVar("stuck_seen", 0) == 1);
    CHECK(scriptRuntime.getScriptNumVar("stuck_done_seen", 0) == 1);

    REQUIRE(scriptRuntime.dispatchMovementResult(1, "obstacle", error, dispatchedCount));
    CHECK(dispatchedCount == 1);
    CHECK(scriptRuntime.getScriptNumVar("obstacle_seen", 0) == 1);

    OpenYAMM::Game::Mm9ScriptRuntime restoredRuntime(package, dialogueRuntime);
    restoredRuntime.restoreState(scriptRuntime.state());
    REQUIRE(restoredRuntime.dispatchMovementResult(1, "touch", error, dispatchedCount));
    CHECK(dispatchedCount == 1);
    CHECK(restoredRuntime.getScriptNumVar("touch_seen", 0) == 1);

    CHECK(dialogueRuntime.owner().objectIndex == 7);
}

TEST_CASE("MM9 script runtime records AI targeting faction and attack commands")
{
    const std::string luaText =
        "local script = { labels = {} }\n"
        "script.labels[\"OnUse\"] = function(ctx)\n"
        "  ctx:command(\"GetMyHandle\", \"hMe\", { line = 1, raw = \"GetMyHandle hMe\" })\n"
        "  ctx:command(\"GetObjectHandle\", \"TargetMarker, hTarget\", "
        "{ line = 2, raw = \"GetObjectHandle TargetMarker, hTarget\" })\n"
        "  ctx:command(\"SetPos\", \"hMe, 0, 0, 0\", { line = 3, raw = \"SetPos hMe, 0, 0, 0\" })\n"
        "  ctx:command(\"SetPos\", \"hTarget, 3, 4, 0\", { line = 4, raw = \"SetPos hTarget, 3, 4, 0\" })\n"
        "  ctx:command(\"Target\", \"hTarget, TRUE\", { line = 5, raw = \"Target hTarget, TRUE\" })\n"
        "  ctx:command(\"AIGetDistance\", \"hTarget, nDist\", "
        "{ line = 6, raw = \"AIGetDistance hTarget, nDist\" })\n"
        "  ctx:command(\"AddFriend\", \"Actor\", { line = 7, raw = \"AddFriend Actor\" })\n"
        "  ctx:command(\"AddEnemy\", \"Marker\", { line = 8, raw = \"AddEnemy Marker\" })\n"
        "  ctx:command(\"CanAttack\", \"bCanAttack\", { line = 9, raw = \"CanAttack bCanAttack\" })\n"
        "  ctx:command(\"CanRangeAttack\", \"bCanRangeAttack\", "
        "{ line = 10, raw = \"CanRangeAttack bCanRangeAttack\" })\n"
        "  ctx:command(\"Attack\", \"OnStop\", { line = 11, raw = \"Attack OnStop\" })\n"
        "  ctx:command(\"IsAttacking\", \"bAttacking\", { line = 12, raw = \"IsAttacking bAttacking\" })\n"
        "  ctx:command(\"RangeAttack\", \"OnRangeStop\", { line = 13, raw = \"RangeAttack OnRangeStop\" })\n"
        "  ctx:command(\"SetIdle\", \"\", { line = 14, raw = \"SetIdle\" })\n"
        "  ctx:command(\"IsAttacking\", \"bAttackingAfterIdle\", "
        "{ line = 15, raw = \"IsAttacking bAttackingAfterIdle\" })\n"
        "end\n"
        "return script\n";

    OpenYAMM::Game::Party party = makeParty();
    OpenYAMM::Game::Mm9DialoguePackage package = makePackage(luaText);
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    setOwner(dialogueRuntime);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    std::optional<std::string> error;
    REQUIRE(runTestLabel(scriptRuntime, error));
    CHECK_FALSE(error.has_value());
    CHECK(scriptRuntime.unimplementedCommands().empty());
    CHECK(scriptRuntime.getScriptNumVar("nDist", 0) == 5);
    CHECK(scriptRuntime.getScriptNumVar("bCanAttack", 0) == 1);
    CHECK(scriptRuntime.getScriptNumVar("bCanRangeAttack", 0) == 1);
    CHECK(scriptRuntime.getScriptNumVar("bAttacking", 0) == 1);
    CHECK(scriptRuntime.getScriptNumVar("bAttackingAfterIdle", 1) == 0);

    const OpenYAMM::Game::Mm9ScriptRuntimeState &state = scriptRuntime.state();
    const std::string activeHandle = "mm9:testmap:object:7";
    REQUIRE(state.objectFriends.count(activeHandle) == 1);
    REQUIRE(state.objectEnemies.count(activeHandle) == 1);
    CHECK(state.objectFriends.at(activeHandle).front() == "Actor");
    CHECK(state.objectEnemies.at(activeHandle).front() == "Marker");
    CHECK(state.objectAiStates.at(activeHandle) == "idle");
    CHECK_FALSE(state.objectAttackStates.at(activeHandle));
    REQUIRE(state.aiRequests.size() == 2);
    CHECK(state.aiRequests[0].operation == "attack");
    CHECK(state.aiRequests[0].targetHandle == "mm9:testmap:object:8");
    CHECK(state.aiRequests[0].callbackLabel == "OnStop");
    CHECK(state.aiRequests[1].operation == "rangeattack");
    CHECK(state.aiRequests[1].callbackLabel == "OnRangeStop");

    const std::vector<OpenYAMM::Game::Mm9ScriptRuntimeCallback> &callbacks =
        scriptRuntime.registeredCallbacks();
    const auto hasCallback = [&](const std::string &kind, const std::string &label)
    {
        return std::any_of(
            callbacks.begin(),
            callbacks.end(),
            [&](const OpenYAMM::Game::Mm9ScriptRuntimeCallback &callback)
            {
                return callback.kind == kind && callback.label == label;
            });
    };
    CHECK(hasCallback("attack", "OnStop"));
    CHECK(hasCallback("rangeattack", "OnRangeStop"));

    OpenYAMM::Game::Mm9ScriptRuntime restoredRuntime(package, dialogueRuntime);
    restoredRuntime.restoreState(state);
    REQUIRE(restoredRuntime.aiRequests().size() == 2);
    CHECK(restoredRuntime.aiRequests()[1].operation == "rangeattack");
}

TEST_CASE("MM9 script runtime records model attachment promotion and vector helper commands")
{
    const std::string luaText =
        "local script = { labels = {} }\n"
        "script.labels[\"OnUse\"] = function(ctx)\n"
        "  ctx:command(\"GetMyHandle\", \"hMe\", { line = 1, raw = \"GetMyHandle hMe\" })\n"
        "  ctx:command(\"GetObjectHandle\", \"TargetMarker, hProp\", "
        "{ line = 2, raw = \"GetObjectHandle TargetMarker, hProp\" })\n"
        "  ctx:command(\"set\", \"dx 2\", { line = 3, raw = \"set dx 2\" })\n"
        "  ctx:command(\"set\", \"dy 3\", { line = 4, raw = \"set dy 3\" })\n"
        "  ctx:command(\"set\", \"dz 4\", { line = 5, raw = \"set dz 4\" })\n"
        "  ctx:command(\"VecScale\", \"dx, dy, dz, 5\", { line = 6, raw = \"VecScale dx,dy,dz,5\" })\n"
        "  ctx:command(\"SetModelFilenames\", "
        "\"models\\\\flyingicky.abc, TEXTURES\\\\LevelTextures\\\\Misc\\\\black.dtx\", "
        "{ line = 7, raw = "
        "\"SetModelFilenames models\\\\flyingicky.abc TEXTURES\\\\LevelTextures\\\\Misc\\\\black.dtx\" })\n"
        "  ctx:command(\"AttachProp\", \"kirasword.ABC, KiraSword.dtx, Sheath, hProp\", "
        "{ line = 8, raw = \"AttachProp kirasword.ABC KiraSword.dtx Sheath hProp\" })\n"
        "  ctx:command(\"GivePromo\", \"Lich, Char1\", { line = 9, raw = \"GivePromo Lich Char1\" })\n"
        "end\n"
        "return script\n";

    OpenYAMM::Game::Party party = makeParty();
    OpenYAMM::Game::Mm9DialoguePackage package = makePackage(luaText);
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    setOwner(dialogueRuntime);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    std::optional<std::string> error;
    REQUIRE(runTestLabel(scriptRuntime, error));
    CHECK_FALSE(error.has_value());
    CHECK(scriptRuntime.unimplementedCommands().empty());
    CHECK(scriptRuntime.getScriptNumVar("dx", 0) == 10);
    CHECK(scriptRuntime.getScriptNumVar("dy", 0) == 15);
    CHECK(scriptRuntime.getScriptNumVar("dz", 0) == 20);

    const OpenYAMM::Game::Mm9ScriptRuntimeState &state = scriptRuntime.state();
    const std::string activeHandle = "mm9:testmap:object:7";
    REQUIRE(state.objectModelFilenames.count(activeHandle) == 1);
    CHECK(state.objectModelFilenames.at(activeHandle)[0] == "models\\flyingicky.abc");
    CHECK(state.objectModelFilenames.at(activeHandle)[1] == "TEXTURES\\LevelTextures\\Misc\\black.dtx");

    REQUIRE(scriptRuntime.attachmentRequests().size() == 1);
    CHECK(scriptRuntime.attachmentRequests()[0].modelName == "kirasword.ABC");
    CHECK(scriptRuntime.attachmentRequests()[0].textureName == "KiraSword.dtx");
    CHECK(scriptRuntime.attachmentRequests()[0].socketName == "Sheath");
    CHECK(scriptRuntime.attachmentRequests()[0].attachedHandle == "mm9:testmap:object:8");

    REQUIRE(scriptRuntime.promotionRequests().size() == 1);
    CHECK(scriptRuntime.promotionRequests()[0].promotionName == "Lich");
    CHECK(scriptRuntime.promotionRequests()[0].characterToken == "Char1");
    REQUIRE(scriptRuntime.partyAccesses().size() == 1);
    CHECK(scriptRuntime.partyAccesses()[0].operation == "givePromo");

    OpenYAMM::Game::Mm9ScriptRuntime restoredRuntime(package, dialogueRuntime);
    restoredRuntime.restoreState(state);
    REQUIRE(restoredRuntime.attachmentRequests().size() == 1);
    REQUIRE(restoredRuntime.promotionRequests().size() == 1);
    CHECK(restoredRuntime.promotionRequests()[0].promotionName == "Lich");
}

TEST_CASE("MM9 script runtime records legacy control and wait commands")
{
    const std::string luaText =
        "local script = { labels = {} }\n"
        "script.labels[\"OnUse\"] = function(ctx)\n"
        "  ctx:command(\"set\", \"bReady TRUE\", { line = 1, raw = \"set bReady TRUE\" })\n"
        "  ctx:command(\"if\", \"bReady == TRUE\", { line = 2, raw = \"if bReady == TRUE\" })\n"
        "  ctx:command(\"gosub\", \"DoWork\", { line = 3, raw = \"gosub DoWork\" })\n"
        "  ctx:command(\"else\", \"\", { line = 4, raw = \"else\" })\n"
        "  ctx:command(\"endif\", \"\", { line = 5, raw = \"endif\" })\n"
        "  ctx:command(\"while(\", \"bReady==TRUE )\", { line = 6, raw = \"while( bReady==TRUE )\" })\n"
        "  ctx:command(\"endwhile\", \"\", { line = 7, raw = \"endwhile\" })\n"
        "  ctx:command(\"wait\", \"30, 0.5, Resume\", { line = 8, raw = \"Wait 30, 0.5, Resume\" })\n"
        "  ctx:command(\"goto\", \"Done\", { line = 9, raw = \"goto Done\" })\n"
        "  ctx:command(\"exit\", \"TRUE\", { line = 10, raw = \"Exit TRUE\" })\n"
        "end\n"
        "return script\n";

    OpenYAMM::Game::Party party = makeParty();
    OpenYAMM::Game::Mm9DialoguePackage package = makePackage(luaText);
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    setOwner(dialogueRuntime);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    std::optional<std::string> error;
    REQUIRE(runTestLabel(scriptRuntime, error));
    CHECK_FALSE(error.has_value());
    CHECK(scriptRuntime.unimplementedCommands().empty());

    const std::vector<OpenYAMM::Game::Mm9ScriptRuntimeControlRequest> &requests =
        scriptRuntime.controlRequests();
    REQUIRE(requests.size() == 9);
    CHECK(requests[0].operation == "if");
    CHECK(requests[0].conditionText == "bReady == TRUE");
    CHECK(requests[0].conditionResult);
    CHECK(requests[1].operation == "gosub");
    CHECK(requests[1].label == "DoWork");
    CHECK(requests[2].operation == "else");
    CHECK(requests[4].operation == "while");
    CHECK(requests[5].operation == "endwhile");
    CHECK(requests[6].operation == "wait");
    CHECK(requests[6].minDelay == 30.0);
    CHECK(requests[6].maxDelay == 0.5);
    CHECK(requests[6].label == "Resume");
    REQUIRE(scriptRuntime.scheduledInvocations().size() == 1);
    CHECK(scriptRuntime.scheduledInvocations()[0].operation == "wait");
    CHECK(scriptRuntime.scheduledInvocations()[0].label == "Resume");
    CHECK(scriptRuntime.scheduledInvocations()[0].mapId == "testmap");
    CHECK(scriptRuntime.scheduledInvocations()[0].objectIndex == 7);
    CHECK(requests[7].operation == "goto");
    CHECK(requests[7].label == "Done");
    CHECK(requests[8].operation == "exit");
    CHECK(requests[8].exitValue == "1");

    OpenYAMM::Game::Mm9ScriptRuntime restoredRuntime(package, dialogueRuntime);
    restoredRuntime.restoreState(scriptRuntime.state());
    REQUIRE(restoredRuntime.controlRequests().size() == 9);
    CHECK(restoredRuntime.controlRequests()[6].label == "Resume");
    REQUIRE(restoredRuntime.scheduledInvocations().size() == 1);
    CHECK(restoredRuntime.scheduledInvocations()[0].label == "Resume");
}

TEST_CASE("MM9 script runtime advances scheduled wait and numbered callbacks")
{
    const std::string luaText =
        "local script = { labels = {} }\n"
        "script.labels[\"OnUse\"] = function(ctx)\n"
        "  ctx:command(\"Wait\", \"2, 2, Resume\", { line = 1, raw = \"Wait 2, 2, Resume\" })\n"
        "  ctx:command(\"SetCallBack\", \"3, CallbackDone\", "
        "{ line = 2, raw = \"SetCallBack 3, CallbackDone\" })\n"
        "  ctx:command(\"DoCallback\", \"3\", { line = 3, raw = \"DoCallback 3\" })\n"
        "end\n"
        "script.labels[\"Resume\"] = function(ctx)\n"
        "  ctx:command(\"set\", \"wait_done 1\", { line = 4, raw = \"set wait_done 1\" })\n"
        "  ctx:command(\"GetMyHandle\", \"wait_owner\", { line = 5, raw = \"GetMyHandle wait_owner\" })\n"
        "end\n"
        "script.labels[\"CallbackDone\"] = function(ctx)\n"
        "  ctx:command(\"set\", \"callback_done 1\", { line = 6, raw = \"set callback_done 1\" })\n"
        "end\n"
        "return script\n";

    OpenYAMM::Game::Party party = makeParty();
    OpenYAMM::Game::Mm9DialoguePackage package = makePackage(luaText);
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    setOwner(dialogueRuntime);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    std::optional<std::string> error;
    REQUIRE(runTestLabel(scriptRuntime, error));
    CHECK_FALSE(error.has_value());
    REQUIRE(scriptRuntime.scheduledInvocations().size() == 1);
    CHECK(scriptRuntime.scheduledInvocations()[0].operation == "wait");
    CHECK(scriptRuntime.scheduledInvocations()[0].dueTimeSeconds == 2.0);
    CHECK(scriptRuntime.getScriptNumVar("callback_done", 0) == 1);

    REQUIRE(scriptRuntime.advanceScriptTime(1.0, error));
    CHECK(scriptRuntime.getScriptNumVar("wait_done", 0) == 0);
    REQUIRE(scriptRuntime.scheduledInvocations().size() == 1);

    REQUIRE(scriptRuntime.advanceScriptTime(1.0, error));
    CHECK(scriptRuntime.getScriptNumVar("wait_done", 0) == 1);
    CHECK(scriptRuntime.getObjectHandleVar("wait_owner") == "mm9:testmap:object:7");
    CHECK(scriptRuntime.scheduledInvocations().empty());
    CHECK(scriptRuntime.scriptTimeSeconds() == 2.0);
    CHECK(dialogueRuntime.owner().objectIndex == 7);

    REQUIRE(scriptRuntime.advanceScriptTime(4498.0, error));
    REQUIRE(scriptRuntime.executeCommand("GetTime", "nScriptTime", 6, "GetTime nScriptTime"));
    REQUIRE(scriptRuntime.executeCommand("GetGameTime", "nHour, nMinute", 7, "GetGameTime nHour,nMinute"));
    CHECK(scriptRuntime.getScriptNumVar("nScriptTime", 0) == 4500);
    CHECK(scriptRuntime.getScriptNumVar("nHour", 0) == 1);
    CHECK(scriptRuntime.getScriptNumVar("nMinute", 0) == 15);
}

TEST_CASE("MM9 script runtime removes numbered and model-key callbacks")
{
    const std::string luaText =
        "local script = { labels = {} }\n"
        "script.labels[\"OnUse\"] = function(ctx)\n"
        "  ctx:command(\"SetCallback\", \"2, RemovedCallback\", "
        "{ line = 1, raw = \"SetCallback 2, RemovedCallback\" })\n"
        "  ctx:command(\"KillCallback\", \"2\", { line = 2, raw = \"KillCallback 2\" })\n"
        "  ctx:command(\"DoCallback\", \"2\", { line = 3, raw = \"DoCallback 2\" })\n"
        "  ctx:command(\"SetCallback\", \"3, LiveCallback\", "
        "{ line = 4, raw = \"SetCallback 3, LiveCallback\" })\n"
        "  ctx:command(\"DoCallback\", \"3\", { line = 5, raw = \"DoCallback 3\" })\n"
        "  ctx:command(\"AddModelKey\", \"RemovedKey, RemovedModel\", "
        "{ line = 6, raw = \"AddModelKey RemovedKey, RemovedModel\" })\n"
        "  ctx:command(\"AddModelKey\", \"LiveKey, LiveModel\", "
        "{ line = 7, raw = \"AddModelKey LiveKey, LiveModel\" })\n"
        "  ctx:command(\"RemoveModelKey\", \"RemovedKey\", { line = 8, raw = \"RemoveModelKey RemovedKey\" })\n"
        "end\n"
        "script.labels[\"RemovedCallback\"] = function(ctx)\n"
        "  ctx:command(\"set\", \"removed_callback 1\", { line = 9, raw = \"set removed_callback 1\" })\n"
        "end\n"
        "script.labels[\"LiveCallback\"] = function(ctx)\n"
        "  ctx:command(\"set\", \"live_callback 1\", { line = 10, raw = \"set live_callback 1\" })\n"
        "end\n"
        "script.labels[\"RemovedModel\"] = function(ctx)\n"
        "  ctx:command(\"set\", \"removed_model 1\", { line = 11, raw = \"set removed_model 1\" })\n"
        "end\n"
        "script.labels[\"LiveModel\"] = function(ctx)\n"
        "  ctx:command(\"set\", \"live_model 1\", { line = 12, raw = \"set live_model 1\" })\n"
        "end\n"
        "return script\n";

    OpenYAMM::Game::Party party = makeParty();
    OpenYAMM::Game::Mm9DialoguePackage package = makePackage(luaText);
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    setOwner(dialogueRuntime);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    std::optional<std::string> error;
    REQUIRE(runTestLabel(scriptRuntime, error));
    CHECK_FALSE(error.has_value());
    CHECK(scriptRuntime.getScriptNumVar("removed_callback", 0) == 0);
    CHECK(scriptRuntime.getScriptNumVar("live_callback", 0) == 1);

    size_t dispatchedCount = 0;
    REQUIRE(scriptRuntime.dispatchRegisteredCallbacks(
        "addmodelkey",
        "RemovedKey",
        "testmap",
        7,
        error,
        dispatchedCount));
    CHECK(dispatchedCount == 0);
    CHECK(scriptRuntime.getScriptNumVar("removed_model", 0) == 0);
    REQUIRE(scriptRuntime.dispatchRegisteredCallbacks("addmodelkey", "LiveKey", "testmap", 7, error, dispatchedCount));
    CHECK(dispatchedCount == 1);
    CHECK(scriptRuntime.getScriptNumVar("live_model", 0) == 1);
}

TEST_CASE("MM9 script runtime dispatches object-scoped registered callbacks")
{
    const std::string luaText =
        "local script = { labels = {} }\n"
        "script.labels[\"OnUse\"] = function(ctx)\n"
        "  ctx:command(\"OnDamage\", \"OnDamaged\", { line = 1, raw = \"OnDamage OnDamaged\" })\n"
        "  ctx:command(\"AddModelKey\", \"DoKey, OnModelKey\", { line = 2, raw = \"AddModelKey DoKey, OnModelKey\" })\n"
        "end\n"
        "script.labels[\"OnDamaged\"] = function(ctx)\n"
        "  ctx:command(\"set\", \"damage_seen 1\", { line = 3, raw = \"set damage_seen 1\" })\n"
        "  ctx:command(\"GetMyHandle\", \"damage_owner\", { line = 4, raw = \"GetMyHandle damage_owner\" })\n"
        "end\n"
        "script.labels[\"OnModelKey\"] = function(ctx)\n"
        "  ctx:command(\"set\", \"model_key_seen 1\", { line = 5, raw = \"set model_key_seen 1\" })\n"
        "end\n"
        "return script\n";

    OpenYAMM::Game::Party party = makeParty();
    OpenYAMM::Game::Mm9DialoguePackage package = makePackage(luaText);
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    setOwner(dialogueRuntime);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    std::optional<std::string> error;
    REQUIRE(runTestLabel(scriptRuntime, error));
    CHECK_FALSE(error.has_value());
    REQUIRE(scriptRuntime.registeredCallbacks().size() == 2);
    CHECK(scriptRuntime.registeredCallbacks()[0].mapId == "testmap");
    CHECK(scriptRuntime.registeredCallbacks()[0].objectIndex == 7);
    CHECK(scriptRuntime.registeredCallbacks()[0].kind == "ondamage");
    CHECK(scriptRuntime.registeredCallbacks()[1].selector == "DoKey");

    size_t dispatchedCount = 99;
    REQUIRE(scriptRuntime.dispatchRegisteredCallbacks("ondamage", "", "testmap", 8, error, dispatchedCount));
    CHECK(dispatchedCount == 0);
    CHECK(scriptRuntime.getScriptNumVar("damage_seen", 0) == 0);

    REQUIRE(scriptRuntime.dispatchRegisteredCallbacks("ondamage", "", "testmap", 7, error, dispatchedCount));
    CHECK(dispatchedCount == 1);
    CHECK(scriptRuntime.getScriptNumVar("damage_seen", 0) == 1);
    CHECK(scriptRuntime.getObjectHandleVar("damage_owner") == "mm9:testmap:object:7");
    CHECK(dialogueRuntime.owner().objectIndex == 7);

    REQUIRE(scriptRuntime.dispatchRegisteredCallbacks("addmodelkey", "OtherKey", "testmap", 7, error, dispatchedCount));
    CHECK(dispatchedCount == 0);
    CHECK(scriptRuntime.getScriptNumVar("model_key_seen", 0) == 0);

    OpenYAMM::Game::Mm9ScriptRuntime restoredRuntime(package, dialogueRuntime);
    restoredRuntime.restoreState(scriptRuntime.state());
    REQUIRE(restoredRuntime.dispatchRegisteredCallbacks("addmodelkey", "DoKey", "testmap", 7, error, dispatchedCount));
    CHECK(dispatchedCount == 1);
    CHECK(restoredRuntime.getScriptNumVar("model_key_seen", 0) == 1);
}

TEST_CASE("MM9 script runtime applies object damage and dispatches lifecycle callbacks")
{
    const std::string luaText =
        "local script = { labels = {} }\n"
        "script.labels[\"OnUse\"] = function(ctx)\n"
        "  ctx:command(\"GetMyHandle\", \"hMe\", { line = 1, raw = \"GetMyHandle hMe\" })\n"
        "  ctx:command(\"SetStat\", \"hMe, HitPoints, 75\", { line = 2, raw = \"SetStat hMe, HitPoints, 75\" })\n"
        "  ctx:command(\"OnDamage\", \"OnDamageLabel\", { line = 3, raw = \"OnDamage OnDamageLabel\" })\n"
        "  ctx:command(\"OnDamageDone\", \"OnDamageDoneLabel\", "
        "{ line = 4, raw = \"OnDamageDone OnDamageDoneLabel\" })\n"
        "  ctx:command(\"OnDeath\", \"OnDeathLabel\", { line = 5, raw = \"OnDeath OnDeathLabel\" })\n"
        "  ctx:command(\"OnDeathDone\", \"OnDeathDoneLabel\", { line = 6, raw = \"OnDeathDone OnDeathDoneLabel\" })\n"
        "  ctx:command(\"Damage\", \"hMe, 40, 4, FALSE\", { line = 7, raw = \"Damage hMe, 40, 4, FALSE\" })\n"
        "  ctx:command(\"GetStat\", \"hMe, HitPoints, hpAfterFirst\", "
        "{ line = 8, raw = \"GetStat hMe, HitPoints, hpAfterFirst\" })\n"
        "  ctx:command(\"Damage\", \"hMe, 50, 4, FALSE\", { line = 9, raw = \"Damage hMe, 50, 4, FALSE\" })\n"
        "  ctx:command(\"GetStat\", \"hMe, HitPoints, hpAfterSecond\", "
        "{ line = 10, raw = \"GetStat hMe, HitPoints, hpAfterSecond\" })\n"
        "end\n"
        "script.labels[\"OnDamageLabel\"] = function(ctx)\n"
        "  ctx:command(\"Add\", \"damage_seen, 1\", { line = 11, raw = \"Add damage_seen, 1\" })\n"
        "  ctx:command(\"GetMyHandle\", \"damage_owner\", { line = 12, raw = \"GetMyHandle damage_owner\" })\n"
        "end\n"
        "script.labels[\"OnDamageDoneLabel\"] = function(ctx)\n"
        "  ctx:command(\"Add\", \"damage_done_seen, 1\", { line = 13, raw = \"Add damage_done_seen, 1\" })\n"
        "end\n"
        "script.labels[\"OnDeathLabel\"] = function(ctx)\n"
        "  ctx:command(\"set\", \"death_seen 1\", { line = 14, raw = \"set death_seen 1\" })\n"
        "end\n"
        "script.labels[\"OnDeathDoneLabel\"] = function(ctx)\n"
        "  ctx:command(\"set\", \"death_done_seen 1\", { line = 15, raw = \"set death_done_seen 1\" })\n"
        "end\n"
        "return script\n";

    OpenYAMM::Game::Party party = makeParty();
    OpenYAMM::Game::Mm9DialoguePackage package = makePackage(luaText);
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    setOwner(dialogueRuntime);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    std::optional<std::string> error;
    REQUIRE(runTestLabel(scriptRuntime, error));
    CHECK_FALSE(error.has_value());
    CHECK(scriptRuntime.unimplementedCommands().empty());
    REQUIRE(scriptRuntime.damageRequests().size() == 2);
    CHECK(scriptRuntime.getScriptNumVar("hpAfterFirst", 0) == 35);
    CHECK(scriptRuntime.getScriptNumVar("hpAfterSecond", -1) == 0);
    CHECK(scriptRuntime.getScriptNumVar("damage_seen", 0) == 2);
    CHECK(scriptRuntime.getScriptNumVar("damage_done_seen", 0) == 2);
    CHECK(scriptRuntime.getScriptNumVar("death_seen", 0) == 1);
    CHECK(scriptRuntime.getScriptNumVar("death_done_seen", 0) == 1);
    CHECK(scriptRuntime.getObjectHandleVar("damage_owner") == "mm9:testmap:object:7");

    const std::string activeHandle = "mm9:testmap:object:7";
    const OpenYAMM::Game::Mm9ScriptRuntimeState &state = scriptRuntime.state();
    REQUIRE(state.objectStats.count(activeHandle) == 1);
    CHECK(state.objectStats.at(activeHandle).at("HitPoints") == 0);
    CHECK(state.objectAiStates.at(activeHandle) == "dead");
    CHECK_FALSE(state.objectAttackStates.at(activeHandle));
    CHECK(state.removedObjects.at(activeHandle));

    OpenYAMM::Game::Mm9ScriptRuntime restoredRuntime(package, dialogueRuntime);
    restoredRuntime.restoreState(state);
    REQUIRE(restoredRuntime.damageRequests().size() == 2);
    CHECK(restoredRuntime.state().objectStats.at(activeHandle).at("HitPoints") == 0);
}

TEST_CASE("MM9 script runtime dispatches animation completion and model key callbacks")
{
    const std::string luaText =
        "local script = { labels = {} }\n"
        "script.labels[\"OnUse\"] = function(ctx)\n"
        "  ctx:command(\"PlayAnim\", \"Taunt, AnimDone\", { line = 1, raw = \"PlayAnim Taunt, AnimDone\" })\n"
        "  ctx:command(\"AddModelKey\", \"DoKey, OnModelKey\", { line = 2, raw = \"AddModelKey DoKey, OnModelKey\" })\n"
        "end\n"
        "script.labels[\"AnimDone\"] = function(ctx)\n"
        "  ctx:command(\"set\", \"anim_done 1\", { line = 3, raw = \"set anim_done 1\" })\n"
        "  ctx:command(\"GetMyHandle\", \"anim_owner\", { line = 4, raw = \"GetMyHandle anim_owner\" })\n"
        "end\n"
        "script.labels[\"OnModelKey\"] = function(ctx)\n"
        "  ctx:command(\"set\", \"model_key_done 1\", { line = 5, raw = \"set model_key_done 1\" })\n"
        "end\n"
        "return script\n";

    OpenYAMM::Game::Party party = makeParty();
    OpenYAMM::Game::Mm9DialoguePackage package = makePackage(luaText);
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    setOwner(dialogueRuntime);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    std::optional<std::string> error;
    REQUIRE(runTestLabel(scriptRuntime, error));
    CHECK_FALSE(error.has_value());
    REQUIRE(scriptRuntime.animationRequests().size() == 1);
    REQUIRE(scriptRuntime.state().animationRequests.size() == 1);
    CHECK(scriptRuntime.animationRequests()[0].animationName == "Taunt");

    size_t dispatchedCount = 0;
    REQUIRE(scriptRuntime.dispatchAnimationResult(0, "complete", "", error, dispatchedCount));
    CHECK(dispatchedCount == 1);
    CHECK(scriptRuntime.getScriptNumVar("anim_done", 0) == 1);
    CHECK(scriptRuntime.getObjectHandleVar("anim_owner") == "mm9:testmap:object:7");

    OpenYAMM::Game::Mm9ScriptRuntime restoredRuntime(package, dialogueRuntime);
    restoredRuntime.restoreState(scriptRuntime.state());
    REQUIRE(restoredRuntime.animationRequests().size() == 1);
    REQUIRE(restoredRuntime.dispatchAnimationResult(0, "modelkey", "DoKey", error, dispatchedCount));
    CHECK(dispatchedCount == 1);
    CHECK(restoredRuntime.getScriptNumVar("model_key_done", 0) == 1);
}

TEST_CASE("MM9 script runtime records combat lifecycle aliases and callbacks")
{
    const std::string luaText =
        "local script = { labels = {} }\n"
        "script.labels[\"OnUse\"] = function(ctx)\n"
        "  ctx:command(\"GetObjectHandle\", \"TargetMarker, hTarget\", "
        "{ line = 1, raw = \"GetObjectHandle TargetMarker, hTarget\" })\n"
        "  ctx:command(\"set\", \"sounddur 10\", { line = 2, raw = \"set sounddur 10\" })\n"
        "  ctx:command(\"Subtract\", \"sounddur, 5\", { line = 3, raw = \"Subtract sounddur, 5\" })\n"
        "  ctx:command(\"Rotate\", \"0, 1, 0, 180, 45, DoneRotating\", "
        "{ line = 4, raw = \"Rotate 0,1,0,180,45,DoneRotating\" })\n"
        "  ctx:command(\"Damage\", \"hTarget, 100, 4, FALSE\", "
        "{ line = 5, raw = \"Damage hTarget, 100, 4, FALSE\" })\n"
        "  ctx:command(\"OnAttackReady\", \"AttackReady\", "
        "{ line = 6, raw = \"OnAttackReady AttackReady\" })\n"
        "  ctx:command(\"OnTargetWithinDist\", \"128, OnClose\", "
        "{ line = 7, raw = \"OnTargetWithinDist 128, OnClose\" })\n"
        "  ctx:command(\"ExitScript\", \"\", { line = 8, raw = \"ExitScript\" })\n"
        "  ctx:command(\"Die\", \"\", { line = 9, raw = \"Die\" })\n"
        "end\n"
        "return script\n";

    OpenYAMM::Game::Party party = makeParty();
    OpenYAMM::Game::Mm9DialoguePackage package = makePackage(luaText);
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    setOwner(dialogueRuntime);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    std::optional<std::string> error;
    REQUIRE(runTestLabel(scriptRuntime, error));
    CHECK_FALSE(error.has_value());
    CHECK(scriptRuntime.unimplementedCommands().empty());
    CHECK(scriptRuntime.getScriptNumVar("sounddur", 0) == 5);

    const OpenYAMM::Game::Mm9ScriptRuntimeState &state = scriptRuntime.state();
    const std::string activeHandle = "mm9:testmap:object:7";
    REQUIRE(state.movementRequests.size() == 1);
    CHECK(state.movementRequests[0].operation == "rotate");
    CHECK(state.movementRequests[0].direction.y == 1.0);
    CHECK(state.movementRequests[0].distance == 180.0);
    CHECK(state.movementRequests[0].speed == 45.0);
    CHECK(state.movementRequests[0].callbackLabel == "DoneRotating");

    REQUIRE(scriptRuntime.damageRequests().size() == 1);
    CHECK(scriptRuntime.damageRequests()[0].targetHandle == "mm9:testmap:object:8");
    CHECK(scriptRuntime.damageRequests()[0].amount == 100);
    CHECK(scriptRuntime.damageRequests()[0].damageType == 4);
    CHECK_FALSE(scriptRuntime.damageRequests()[0].noReaction);
    CHECK(state.objectAiStates.at(activeHandle) == "dead");
    CHECK_FALSE(state.objectAttackStates.at(activeHandle));
    CHECK(state.removedObjects.at(activeHandle));

    const std::vector<OpenYAMM::Game::Mm9ScriptRuntimeCallback> &callbacks =
        scriptRuntime.registeredCallbacks();
    const auto hasCallback = [&](const std::string &kind, const std::string &label)
    {
        return std::any_of(
            callbacks.begin(),
            callbacks.end(),
            [&](const OpenYAMM::Game::Mm9ScriptRuntimeCallback &callback)
            {
                return callback.kind == kind && callback.label == label;
            });
    };
    CHECK(hasCallback("rotate", "DoneRotating"));
    CHECK(hasCallback("onattackready", "AttackReady"));
    CHECK(hasCallback("ontargetwithindist", "OnClose"));

    REQUIRE(scriptRuntime.controlRequests().size() == 1);
    CHECK(scriptRuntime.controlRequests()[0].operation == "exitscript");

    OpenYAMM::Game::Mm9ScriptRuntime restoredRuntime(package, dialogueRuntime);
    restoredRuntime.restoreState(state);
    REQUIRE(restoredRuntime.damageRequests().size() == 1);
    CHECK(restoredRuntime.damageRequests()[0].amount == 100);
}

TEST_CASE("MM9 script runtime handles schedule utility query and gold commands")
{
    const std::string luaText =
        "local script = { labels = {} }\n"
        "script.labels[\"OnUse\"] = function(ctx)\n"
        "  ctx:command(\"GetMyHandle\", \"hMe\", { line = 1, raw = \"GetMyHandle hMe\" })\n"
        "  ctx:command(\"@M\", \"6 : 15, GoWork, WarpWork\", "
        "{ line = 2, raw = \"@M 6 : 15, GoWork, WarpWork\" })\n"
        "  ctx:command(\"SetPos\", \"hMe, 0, 0, 0\", { line = 3, raw = \"SetPos hMe, 0, 0, 0\" })\n"
        "  ctx:command(\"GetObjectHandle\", \"TargetMarker, hTarget\", "
        "{ line = 4, raw = \"GetObjectHandle TargetMarker, hTarget\" })\n"
        "  ctx:command(\"SetPos\", \"hTarget, 6, 8, 0\", { line = 5, raw = \"SetPos hTarget, 6, 8, 0\" })\n"
        "  ctx:command(\"GetDistance\", \"hMe, hTarget, nDist\", "
        "{ line = 6, raw = \"GetDistance hMe, hTarget, nDist\" })\n"
        "  ctx:command(\"SetStat\", \"hMe, DimsX, 11\", { line = 7, raw = \"SetStat hMe, DimsX, 11\" })\n"
        "  ctx:command(\"SetStat\", \"hMe, DimsY, 12\", { line = 8, raw = \"SetStat hMe, DimsY, 12\" })\n"
        "  ctx:command(\"SetStat\", \"hMe, DimsZ, 13\", { line = 9, raw = \"SetStat hMe, DimsZ, 13\" })\n"
        "  ctx:command(\"GetDims\", \"hMe, xDim, yDim, zDim\", "
        "{ line = 10, raw = \"GetDims hMe, xDim, yDim, zDim\" })\n"
        "  ctx:command(\"SetVelocity\", \"hMe, 1, 2, 3\", { line = 11, raw = \"SetVelocity hMe, 1, 2, 3\" })\n"
        "  ctx:command(\"set\", \"vx 3\", { line = 12, raw = \"set vx 3\" })\n"
        "  ctx:command(\"set\", \"vy 4\", { line = 13, raw = \"set vy 4\" })\n"
        "  ctx:command(\"set\", \"vz 0\", { line = 14, raw = \"set vz 0\" })\n"
        "  ctx:command(\"VecNorm\", \"vx, vy, vz\", { line = 15, raw = \"VecNorm vx, vy, vz\" })\n"
        "  ctx:command(\"set\", \"nCounter 17\", { line = 16, raw = \"set nCounter 17\" })\n"
        "  ctx:command(\"Mod\", \"nCounter, 5\", { line = 17, raw = \"Mod nCounter, 5\" })\n"
        "  ctx:command(\"PlaySoundHandle\", \"tone.wav, soundhandle, 1, FALSE, 100\", "
        "{ line = 18, raw = \"PlaySoundHandle tone.wav, soundhandle, 1, FALSE, 100\" })\n"
        "  ctx:command(\"IsSoundDone\", \"soundhandle, soundDone\", "
        "{ line = 19, raw = \"IsSoundDone soundhandle, soundDone\" })\n"
        "  ctx:command(\"KillSound\", \"soundhandle\", { line = 20, raw = \"KillSound soundhandle\" })\n"
        "  ctx:command(\"IsSoundDone\", \"soundhandle, soundDoneAfterKill\", "
        "{ line = 21, raw = \"IsSoundDone soundhandle, soundDoneAfterKill\" })\n"
        "  ctx:command(\"GetObjects\", \"Marker, 1000, 5, hObjects, nObjects\", "
        "{ line = 22, raw = \"GetObjects Marker, 1000, 5, hObjects, nObjects\" })\n"
        "  ctx:command(\"SetPropString\", \"ScriptName, Custom.scr\", "
        "{ line = 23, raw = \"SetPropString ScriptName, Custom.scr\" })\n"
        "  ctx:command(\"GetStatStr\", \"hMe, ScriptName, sScript\", "
        "{ line = 24, raw = \"GetStatStr hMe, ScriptName, sScript\" })\n"
        "  ctx:command(\"HasGold\", \"50, bHasGold\", { line = 25, raw = \"HasGold 50, bHasGold\" })\n"
        "  ctx:command(\"TakeGold\", \"50\", { line = 26, raw = \"TakeGold 50\" })\n"
        "  ctx:command(\"Walk\", \"\", { line = 27, raw = \"Walk\" })\n"
        "  ctx:command(\"Run\", \"\", { line = 28, raw = \"Run\" })\n"
        "end\n"
        "return script\n";

    OpenYAMM::Game::Party party = makeParty();
    party.addGold(75);
    OpenYAMM::Game::Mm9DialoguePackage package = makePackage(luaText);
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    setOwner(dialogueRuntime);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    std::optional<std::string> error;
    REQUIRE(runTestLabel(scriptRuntime, error));
    CHECK_FALSE(error.has_value());
    CHECK(scriptRuntime.unimplementedCommands().empty());
    CHECK(scriptRuntime.getScriptNumVar("nDist", 0) == 10);
    CHECK(scriptRuntime.getScriptNumVar("xDim", 0) == 11);
    CHECK(scriptRuntime.getScriptNumVar("yDim", 0) == 12);
    CHECK(scriptRuntime.getScriptNumVar("zDim", 0) == 13);
    CHECK(scriptRuntime.getScriptNumVar("nCounter", 0) == 2);
    CHECK(scriptRuntime.getScriptNumVar("soundDone", 1) == 0);
    CHECK(scriptRuntime.getScriptNumVar("soundDoneAfterKill", 0) == 1);
    CHECK(scriptRuntime.getScriptNumVar("nObjects", 0) == 1);
    CHECK(scriptRuntime.getScriptStrVar("sScript") == "Custom.scr");
    CHECK(scriptRuntime.getScriptNumVar("bHasGold", 0) == 1);
    CHECK(party.gold() == 25);

    const OpenYAMM::Game::Mm9ScriptRuntimeState &state = scriptRuntime.state();
    const std::string activeHandle = "mm9:testmap:object:7";
    REQUIRE(state.controlRequests.size() == 1);
    CHECK(state.controlRequests[0].operation == "@m");
    CHECK(state.controlRequests[0].minDelay == 6.0);
    CHECK(state.controlRequests[0].maxDelay == 15.0);
    CHECK(state.controlRequests[0].label == "GoWork");
    CHECK(state.controlRequests[0].exitValue == "WarpWork");
    CHECK(state.objectStats.at(activeHandle).at("VelocityX") == 1);
    CHECK(state.objectStats.at(activeHandle).at("VelocityY") == 2);
    CHECK(state.objectStats.at(activeHandle).at("VelocityZ") == 3);
    CHECK(state.scriptStrArrays.at("hObjects").at(0) == "mm9:testmap:object:8");
    CHECK(state.objectAiStates.at(activeHandle) == "run");
    REQUIRE(state.movementRequests.size() == 2);
    CHECK(state.movementRequests[0].operation == "walk");
    CHECK(state.movementRequests[1].operation == "run");

    OpenYAMM::Game::Mm9ScriptRuntime restoredRuntime(package, dialogueRuntime);
    restoredRuntime.restoreState(state);
    CHECK(restoredRuntime.state().objectStringProperties.at(activeHandle).at("ScriptName") == "Custom.scr");
}

TEST_CASE("MM9 script runtime records remaining high frequency service commands")
{
    const std::string luaText =
        "local script = { labels = {} }\n"
        "script.labels[\"OnUse\"] = function(ctx)\n"
        "  ctx:command(\"GetMyHandle\", \"hMe\", { line = 1, raw = \"GetMyHandle hMe\" })\n"
        "  ctx:command(\"GetObjectHandle\", \"TargetMarker, hTarget\", "
        "{ line = 2, raw = \"GetObjectHandle TargetMarker, hTarget\" })\n"
        "  ctx:command(\"AddFriend\", \"Marker\", { line = 3, raw = \"AddFriend Marker\" })\n"
        "  ctx:command(\"IsFriend\", \"hTarget, bFriend\", { line = 4, raw = \"IsFriend hTarget, bFriend\" })\n"
        "  ctx:command(\"CacheScript\", \"TEST.scr\", { line = 5, raw = \"CacheScript TEST.scr\" })\n"
        "  ctx:command(\"DoCallback\", \"2\", { line = 6, raw = \"DoCallback 2\" })\n"
        "  ctx:command(\"CacheTexture\", \"skins\\\\Njam1.dtx\", "
        "{ line = 7, raw = \"CacheTexture skins\\\\Njam1.dtx\" })\n"
        "  ctx:command(\"Taunt\", \"TauntDone\", { line = 8, raw = \"Taunt TauntDone\" })\n"
        "  ctx:command(\"Aware\", \"AwareDone\", { line = 9, raw = \"Aware AwareDone\" })\n"
        "  ctx:command(\"Launch\", \"LaunchDone, 24\", { line = 10, raw = \"Launch LaunchDone, 24\" })\n"
        "  ctx:command(\"Converse\", \"-1, ConvDone\", { line = 11, raw = \"Converse -1 ConvDone\" })\n"
        "  ctx:command(\"ResumeWait\", \"-1\", { line = 12, raw = \"ResumeWait -1\" })\n"
        "  ctx:command(\"SendAlert\", \"hTarget\", { line = 13, raw = \"SendAlert hTarget\" })\n"
        "  ctx:command(\"SetPushBack\", \"1, 2, 3, 4\", { line = 14, raw = \"SetPushBack 1,2,3,4\" })\n"
        "  ctx:command(\"RunToPos\", \"10, 20, 30, 5, RunDone\", "
        "{ line = 15, raw = \"RunToPos 10,20,30,5,RunDone\" })\n"
        "  ctx:command(\"SetStat\", \"hMe, MinX, 1\", { line = 16, raw = \"SetStat hMe, MinX, 1\" })\n"
        "  ctx:command(\"SetStat\", \"hMe, MinY, 2\", { line = 17, raw = \"SetStat hMe, MinY, 2\" })\n"
        "  ctx:command(\"SetStat\", \"hMe, MinZ, 3\", { line = 18, raw = \"SetStat hMe, MinZ, 3\" })\n"
        "  ctx:command(\"SetStat\", \"hMe, MaxX, 4\", { line = 19, raw = \"SetStat hMe, MaxX, 4\" })\n"
        "  ctx:command(\"SetStat\", \"hMe, MaxY, 5\", { line = 20, raw = \"SetStat hMe, MaxY, 5\" })\n"
        "  ctx:command(\"SetStat\", \"hMe, MaxZ, 6\", { line = 21, raw = \"SetStat hMe, MaxZ, 6\" })\n"
        "  ctx:command(\"GetObjectMinMax\", "
        "\"hMe, minX, minY, minZ, maxX, maxY, maxZ\", "
        "{ line = 22, raw = \"GetObjectMinMax hMe, minX, minY, minZ, maxX, maxY, maxZ\" })\n"
        "  ctx:command(\"DetachProp\", \"hTarget, FALSE\", { line = 23, raw = \"DetachProp hTarget, FALSE\" })\n"
        "  ctx:command(\"GiveAttribute\", \"0, 10, TRUE, 3000\", "
        "{ line = 24, raw = \"GiveAttribute 0, 10, TRUE, 3000\" })\n"
        "  ctx:command(\"OnDamageDone\", \"DamageDone\", { line = 25, raw = \"OnDamageDone DamageDone\" })\n"
        "  ctx:command(\"OnStuckDone\", \"StuckDone\", { line = 26, raw = \"OnStuckDone StuckDone\" })\n"
        "  ctx:command(\"OnObstacleAvoided\", \"AvoidDone\", "
        "{ line = 27, raw = \"OnObstacleAvoided AvoidDone\" })\n"
        "  ctx:command(\"IsTurnBased\", \"bTurn\", { line = 28, raw = \"IsTurnBased bTurn\" })\n"
        "  ctx:command(\"TraceOff\", \"\", { line = 29, raw = \"TraceOff\" })\n"
        "end\n"
        "return script\n";

    OpenYAMM::Game::Party party = makeParty();
    OpenYAMM::Game::Mm9DialoguePackage package = makePackage(luaText);
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    setOwner(dialogueRuntime);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    std::optional<std::string> error;
    REQUIRE(runTestLabel(scriptRuntime, error));
    CHECK_FALSE(error.has_value());
    CHECK(scriptRuntime.unimplementedCommands().empty());
    CHECK(scriptRuntime.getScriptNumVar("bFriend", 0) == 1);
    CHECK(scriptRuntime.getScriptNumVar("minX", 0) == 1);
    CHECK(scriptRuntime.getScriptNumVar("minY", 0) == 2);
    CHECK(scriptRuntime.getScriptNumVar("minZ", 0) == 3);
    CHECK(scriptRuntime.getScriptNumVar("maxX", 0) == 4);
    CHECK(scriptRuntime.getScriptNumVar("maxY", 0) == 5);
    CHECK(scriptRuntime.getScriptNumVar("maxZ", 0) == 6);
    CHECK(scriptRuntime.getScriptNumVar("bTurn", -1) == 0);

    const std::vector<OpenYAMM::Game::Mm9ScriptRuntimeAnimationRequest> &animations =
        scriptRuntime.animationRequests();
    REQUIRE(animations.size() == 5);
    CHECK(animations[0].operation == "taunt");
    CHECK(animations[2].operation == "launch");
    CHECK(animations[2].loopCount == 24);
    CHECK(animations[3].callbackLabel == "ConvDone");

    const std::vector<OpenYAMM::Game::Mm9ScriptRuntimeControlRequest> &controls =
        scriptRuntime.controlRequests();
    REQUIRE(controls.size() == 2);
    CHECK(controls[0].operation == "cachescript");
    CHECK(controls[0].label == "TEST.scr");
    CHECK(controls[1].operation == "docallback");
    CHECK(controls[1].label == "2");

    REQUIRE(scriptRuntime.presentationRequests().size() == 1);
    CHECK(scriptRuntime.presentationRequests()[0].operation == "cachetexture");
    REQUIRE(scriptRuntime.aiRequests().size() == 1);
    CHECK(scriptRuntime.aiRequests()[0].operation == "sendalert");
    CHECK(scriptRuntime.aiRequests()[0].targetHandle == "mm9:testmap:object:8");

    const OpenYAMM::Game::Mm9ScriptRuntimeState &state = scriptRuntime.state();
    REQUIRE(state.movementRequests.size() == 2);
    CHECK(state.movementRequests[0].operation == "setpushback");
    CHECK(state.movementRequests[0].direction.z == 3.0);
    CHECK(state.movementRequests[1].operation == "runtopos");
    CHECK(state.movementRequests[1].callbackLabel == "RunDone");
    REQUIRE(scriptRuntime.attachmentRequests().size() == 1);
    CHECK(scriptRuntime.attachmentRequests()[0].operation == "detachprop");
    CHECK(scriptRuntime.attachmentRequests()[0].attachedHandle == "mm9:testmap:object:8");
    REQUIRE(scriptRuntime.partyCommandRequests().size() == 1);
    CHECK(scriptRuntime.partyCommandRequests()[0].operation == "giveattribute");
    CHECK(scriptRuntime.partyCommandRequests()[0].arguments[3] == "3000");

    const auto hasCallback = [&](const std::string &kind, const std::string &label)
    {
        const std::vector<OpenYAMM::Game::Mm9ScriptRuntimeCallback> &callbacks =
            scriptRuntime.registeredCallbacks();
        return std::any_of(
            callbacks.begin(),
            callbacks.end(),
            [&](const OpenYAMM::Game::Mm9ScriptRuntimeCallback &callback)
            {
                return callback.kind == kind && callback.label == label;
            });
    };
    CHECK(hasCallback("taunt", "TauntDone"));
    CHECK(hasCallback("ondamagedone", "DamageDone"));
    CHECK(hasCallback("onstuckdone", "StuckDone"));
    CHECK(hasCallback("onobstacleavoided", "AvoidDone"));

    OpenYAMM::Game::Mm9ScriptRuntime restoredRuntime(package, dialogueRuntime);
    restoredRuntime.restoreState(state);
    REQUIRE(restoredRuntime.partyCommandRequests().size() == 1);
    CHECK(restoredRuntime.partyCommandRequests()[0].arguments[1] == "10");
    REQUIRE(restoredRuntime.attachmentRequests().size() == 1);
    CHECK(restoredRuntime.attachmentRequests()[0].operation == "detachprop");
}

TEST_CASE("MM9 script runtime records lower frequency service command aliases")
{
    const std::string luaText =
        "local script = { labels = {} }\n"
        "script.labels[\"OnUse\"] = function(ctx)\n"
        "  ctx:command(\"GetMyHandle\", \"hMe\", { line = 1, raw = \"GetMyHandle hMe\" })\n"
        "  ctx:command(\"GetObjectHandle\", \"TargetMarker, hTarget\", "
        "{ line = 2, raw = \"GetObjectHandle TargetMarker, hTarget\" })\n"
        "  ctx:command(\"AddFriend\", \"Marker\", { line = 3, raw = \"AddFriend Marker\" })\n"
        "  ctx:command(\"RemoveFriend\", \"Marker\", { line = 4, raw = \"RemoveFriend Marker\" })\n"
        "  ctx:command(\"AddEnemy\", \"NPC\", { line = 5, raw = \"AddEnemy NPC\" })\n"
        "  ctx:command(\"RemoveEnemy\", \"NPC\", { line = 6, raw = \"RemoveEnemy NPC\" })\n"
        "  ctx:command(\"SetStat\", \"hMe, Grounded, 1\", { line = 7, raw = \"SetStat hMe, Grounded, 1\" })\n"
        "  ctx:command(\"SetStat\", \"hMe, VelocityX, 3\", { line = 8, raw = \"SetStat hMe, VelocityX, 3\" })\n"
        "  ctx:command(\"SetStat\", \"hMe, VelocityY, 4\", { line = 9, raw = \"SetStat hMe, VelocityY, 4\" })\n"
        "  ctx:command(\"SetStat\", \"hMe, VelocityZ, 5\", { line = 10, raw = \"SetStat hMe, VelocityZ, 5\" })\n"
        "  ctx:command(\"IsOnGround\", \"bGround\", { line = 11, raw = \"IsOnGround bGround\" })\n"
        "  ctx:command(\"IsClearShot\", \"hTarget, bClear\", "
        "{ line = 12, raw = \"IsClearShot hTarget, bClear\" })\n"
        "  ctx:command(\"IsVisible\", \"hTarget, bVisible\", { line = 13, raw = \"IsVisible hTarget, bVisible\" })\n"
        "  ctx:command(\"IsAI\", \"hTarget, bAi\", { line = 14, raw = \"IsAI hTarget, bAi\" })\n"
        "  ctx:command(\"FindTargets\", \"hTargets, 2, nTargets, 512, 0\", "
        "{ line = 15, raw = \"FindTargets hTargets,2,nTargets,512,0\" })\n"
        "  ctx:command(\"GetGameTime\", \"nHour, nMinute\", { line = 16, raw = \"GetGameTime nHour,nMinute\" })\n"
        "  ctx:command(\"GetPCLevel\", \"0, pcLevel\", { line = 17, raw = \"GetPCLevel 0 pcLevel\" })\n"
        "  ctx:command(\"GetPCVoice\", \"pcVoice\", { line = 18, raw = \"GetPCVoice pcVoice\" })\n"
        "  ctx:command(\"SetVelocity\", \"hMe, 7, 8, 9\", { line = 19, raw = \"SetVelocity hMe,7,8,9\" })\n"
        "  ctx:command(\"GetVelocity\", \"hMe, vx, vy, vz\", "
        "{ line = 20, raw = \"GetVelocity hMe,vx,vy,vz\" })\n"
        "  ctx:command(\"set\", \"ax 10\", { line = 21, raw = \"set ax 10\" })\n"
        "  ctx:command(\"set\", \"ay 20\", { line = 22, raw = \"set ay 20\" })\n"
        "  ctx:command(\"set\", \"az 30\", { line = 23, raw = \"set az 30\" })\n"
        "  ctx:command(\"VecSub\", \"ax, ay, az, 1, 2, 3\", "
        "{ line = 24, raw = \"VecSub ax,ay,az,1,2,3\" })\n"
        "  ctx:command(\"VecAdd\", \"ax, ay, az, 1, 2, 3\", "
        "{ line = 25, raw = \"VecAdd ax,ay,az,1,2,3\" })\n"
        "  ctx:command(\"CalcDist\", \"0, 0, 0, 3, 4, 0, dist\", "
        "{ line = 26, raw = \"CalcDist 0,0,0,3,4,0,dist\" })\n"
        "  ctx:command(\"Multiply\", \"dist, 2\", { line = 27, raw = \"Multiply dist,2\" })\n"
        "  ctx:command(\"Divide\", \"dist, 5\", { line = 28, raw = \"Divide dist,5\" })\n"
        "  ctx:command(\"CreateObjectLink\", \"hTarget\", { line = 29, raw = \"CreateObjectLink hTarget\" })\n"
        "  ctx:command(\"BreakObjectLink\", \"hTarget\", { line = 30, raw = \"BreakObjectLink hTarget\" })\n"
        "  ctx:command(\"GetLiquidContainer\", \"hMe, hWater\", "
        "{ line = 31, raw = \"GetLiquidContainer hMe hWater\" })\n"
        "  ctx:command(\"WalkToPos\", \"1, 2, 3, 4, WalkDone\", "
        "{ line = 32, raw = \"WalkToPos 1,2,3,4,WalkDone\" })\n"
        "  ctx:command(\"PauseWait\", \"-1\", { line = 33, raw = \"PauseWait -1\" })\n"
        "  ctx:command(\"Jump\", \"JumpDone\", { line = 34, raw = \"Jump JumpDone\" })\n"
        "  ctx:command(\"BlendAnim\", \"Taunt, BlendDone\", { line = 35, raw = \"BlendAnim Taunt BlendDone\" })\n"
        "  ctx:command(\"SetParam\", \"0, Door0\", { line = 36, raw = \"SetParam 0, Door0\" })\n"
        "  ctx:command(\"Heal\", \"hPlayer, 25\", { line = 37, raw = \"Heal hPlayer, 25\" })\n"
        "  ctx:command(\"GetAttribute\", \"0, Player_Strength\", "
        "{ line = 38, raw = \"GetAttribute 0, Player_Strength\" })\n"
        "  ctx:command(\"OnCongestion\", \"Congested\", { line = 39, raw = \"OnCongestion Congested\" })\n"
        "  ctx:command(\"OnDeathDone\", \"DeathDone\", { line = 40, raw = \"OnDeathDone DeathDone\" })\n"
        "  ctx:command(\"OnDoor\", \"DoorDone\", { line = 41, raw = \"OnDoor DoorDone\" })\n"
        "  ctx:command(\"OnPathClear\", \"PathClear\", { line = 42, raw = \"OnPathClear PathClear\" })\n"
        "  ctx:command(\"OnTargetOutOfRange\", \"OutOfRange\", "
        "{ line = 43, raw = \"OnTargetOutOfRange OutOfRange\" })\n"
        "  ctx:command(\"OnProjectile\", \"ProjectileDone, 500\", "
        "{ line = 44, raw = \"OnProjectile ProjectileDone, 500\" })\n"
        "  ctx:command(\"OnAvoidingObstacle\", \"Avoiding\", "
        "{ line = 45, raw = \"OnAvoidingObstacle Avoiding\" })\n"
        "  ctx:command(\"TraceOn\", \"\", { line = 46, raw = \"TraceOn\" })\n"
        "  ctx:command(\"HidePiece\", \"spear\", { line = 47, raw = \"HidePiece spear\" })\n"
        "end\n"
        "return script\n";

    OpenYAMM::Game::Party party = makeParty();
    OpenYAMM::Game::Mm9DialoguePackage package = makePackage(luaText);
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    setOwner(dialogueRuntime);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    std::optional<std::string> error;
    REQUIRE(runTestLabel(scriptRuntime, error));
    CHECK_FALSE(error.has_value());
    CHECK(scriptRuntime.unimplementedCommands().empty());
    CHECK(scriptRuntime.getScriptNumVar("bGround", 0) == 1);
    CHECK(scriptRuntime.getScriptNumVar("bClear", 0) == 1);
    CHECK(scriptRuntime.getScriptNumVar("bVisible", 0) == 1);
    CHECK(scriptRuntime.getScriptNumVar("bAi", 1) == 0);
    CHECK(scriptRuntime.getScriptNumVar("nTargets", 0) == 1);
    CHECK(scriptRuntime.getScriptNumVar("nHour", -1) == 0);
    CHECK(scriptRuntime.getScriptNumVar("nMinute", -1) == 0);
    CHECK(scriptRuntime.getScriptNumVar("pcLevel", 0) == 1);
    CHECK(scriptRuntime.getScriptNumVar("pcVoice", -1) == 0);
    CHECK(scriptRuntime.getScriptNumVar("vx", 0) == 7);
    CHECK(scriptRuntime.getScriptNumVar("vy", 0) == 8);
    CHECK(scriptRuntime.getScriptNumVar("vz", 0) == 9);
    CHECK(scriptRuntime.getScriptNumVar("ax", 0) == 10);
    CHECK(scriptRuntime.getScriptNumVar("ay", 0) == 20);
    CHECK(scriptRuntime.getScriptNumVar("az", 0) == 30);
    CHECK(scriptRuntime.getScriptNumVar("dist", 0) == 2);
    CHECK(scriptRuntime.getObjectHandleVar("hWater") == "mm9:testmap:object:7");
    CHECK(scriptRuntime.getScriptNumVar("Player_Strength", -1) == 0);

    const OpenYAMM::Game::Mm9ScriptRuntimeState &state = scriptRuntime.state();
    CHECK(state.scriptStrArrays.at("hTargets").at(0) == "mm9:player");
    CHECK(state.objectFriends.at("mm9:testmap:object:7").empty());
    CHECK(state.objectEnemies.at("mm9:testmap:object:7").empty());
    CHECK(state.objectLinks.at("mm9:testmap:object:7").empty());
    REQUIRE(state.movementRequests.size() == 1);
    CHECK(state.movementRequests[0].operation == "walktopos");
    REQUIRE(scriptRuntime.animationRequests().size() == 3);
    CHECK(scriptRuntime.animationRequests()[0].operation == "pausewait");
    CHECK(scriptRuntime.animationRequests()[1].callbackLabel == "JumpDone");
    CHECK(scriptRuntime.animationRequests()[2].animationName == "Taunt");
    REQUIRE(scriptRuntime.controlRequests().size() == 1);
    CHECK(scriptRuntime.controlRequests()[0].operation == "setparam");
    REQUIRE(scriptRuntime.partyCommandRequests().size() == 2);
    CHECK(scriptRuntime.partyCommandRequests()[0].operation == "heal");
    CHECK(scriptRuntime.partyCommandRequests()[1].operation == "getattribute");
    REQUIRE(scriptRuntime.presentationRequests().size() == 1);
    CHECK(scriptRuntime.presentationRequests()[0].operation == "hidepiece");

    const auto hasCallback = [&](const std::string &kind, const std::string &label)
    {
        const std::vector<OpenYAMM::Game::Mm9ScriptRuntimeCallback> &callbacks =
            scriptRuntime.registeredCallbacks();
        return std::any_of(
            callbacks.begin(),
            callbacks.end(),
            [&](const OpenYAMM::Game::Mm9ScriptRuntimeCallback &callback)
            {
                return callback.kind == kind && callback.label == label;
            });
    };
    CHECK(hasCallback("oncongestion", "Congested"));
    CHECK(hasCallback("ondeathdone", "DeathDone"));
    CHECK(hasCallback("ondoor", "DoorDone"));
    CHECK(hasCallback("onpathclear", "PathClear"));
    CHECK(hasCallback("ontargetoutofrange", "OutOfRange"));
    CHECK(hasCallback("onprojectile", "ProjectileDone"));
    CHECK(hasCallback("onavoidingobstacle", "Avoiding"));

    OpenYAMM::Game::Mm9ScriptRuntime restoredRuntime(package, dialogueRuntime);
    restoredRuntime.restoreState(state);
    REQUIRE(restoredRuntime.partyCommandRequests().size() == 2);
    CHECK(restoredRuntime.partyCommandRequests()[1].arguments[1] == "Player_Strength");
}

TEST_CASE("MM9 script runtime maps current PC attributes and heal command to runtime state")
{
    const std::string luaText =
        "local script = { labels = {} }\n"
        "script.labels.OnUse = function(ctx)\n"
        "  ctx:command(\"GetPlayerHandle\", \"hPlayer\", { line = 1, raw = \"GetPlayerHandle hPlayer\" })\n"
        "  ctx:command(\"GetAttribute\", \"STAT_MIGHT, nMight\", "
        "{ line = 2, raw = \"GetAttribute STAT_MIGHT, nMight\" })\n"
        "  ctx:command(\"GetAttribute\", \"1, nMagic\", { line = 3, raw = \"GetAttribute 1, nMagic\" })\n"
        "  ctx:command(\"Heal\", \"hPlayer, 25\", { line = 4, raw = \"Heal hPlayer, 25\" })\n"
        "  ctx:command(\"SetStat\", \"hMe, HitPoints, 15\", { line = 5, raw = \"SetStat hMe, HitPoints, 15\" })\n"
        "  ctx:command(\"SetStat\", \"hMe, MaxHitPoints, 20\", { line = 6, raw = \"SetStat hMe, MaxHitPoints, 20\" })\n"
        "  ctx:command(\"Heal\", \"hMe, 10\", { line = 7, raw = \"Heal hMe, 10\" })\n"
        "  ctx:command(\"GetStat\", \"hMe, HitPoints, objectHp\", "
        "{ line = 8, raw = \"GetStat hMe, HitPoints, objectHp\" })\n"
        "end\n"
        "return script\n";

    OpenYAMM::Game::PartySeed seed = {};
    seed.members.resize(1);
    seed.members[0].might = 12;
    seed.members[0].permanentBonuses.might = 3;
    seed.members[0].magicalBonuses.might = 2;
    seed.members[0].intellect = 7;
    seed.members[0].permanentBonuses.intellect = 4;
    seed.members[0].magicalBonuses.intellect = 1;
    seed.members[0].maxHealth = 40;
    seed.members[0].health = 10;

    OpenYAMM::Game::Party party = {};
    party.seed(seed);
    REQUIRE(party.member(0) != nullptr);
    party.member(0)->magicalBonuses.might = 2;
    party.member(0)->magicalBonuses.intellect = 1;

    OpenYAMM::Game::Mm9DialoguePackage package = makePackage(luaText);
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    setOwner(dialogueRuntime);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    std::optional<std::string> error;
    REQUIRE(runTestLabel(scriptRuntime, error));
    CHECK_FALSE(error.has_value());

    CHECK(scriptRuntime.getScriptNumVar("nMight", 0) == 17);
    CHECK(scriptRuntime.getScriptNumVar("nMagic", 0) == 12);
    CHECK(scriptRuntime.getScriptNumVar("objectHp", 0) == 20);
    REQUIRE(dialogueRuntime.party().member(0) != nullptr);
    CHECK(dialogueRuntime.party().member(0)->health == 35);

    REQUIRE(scriptRuntime.partyCommandRequests().size() == 4);
    CHECK(scriptRuntime.partyCommandRequests()[0].operation == "getattribute");
    CHECK(scriptRuntime.partyCommandRequests()[1].operation == "getattribute");
    CHECK(scriptRuntime.partyCommandRequests()[2].operation == "heal");
    CHECK(scriptRuntime.partyCommandRequests()[3].operation == "heal");
}

TEST_CASE("MM9 script runtime applies permanent and timed GiveAttribute effects")
{
    const std::string luaText =
        "local script = { labels = {} }\n"
        "script.labels.OnUse = function(ctx)\n"
        "  ctx:command(\"GiveAttribute\", \"STAT_MIGHT, 5, FALSE\", "
        "{ line = 1, raw = \"GiveAttribute STAT_MIGHT, 5, FALSE\" })\n"
        "  ctx:command(\"GiveAttribute\", \"STAT_SPEED, 3, TRUE, 10\", "
        "{ line = 2, raw = \"GiveAttribute STAT_SPEED, 3, TRUE, 10\" })\n"
        "  ctx:command(\"GetAttribute\", \"STAT_MIGHT, nMight\", "
        "{ line = 3, raw = \"GetAttribute STAT_MIGHT, nMight\" })\n"
        "  ctx:command(\"GetAttribute\", \"STAT_SPEED, nSpeed\", "
        "{ line = 4, raw = \"GetAttribute STAT_SPEED, nSpeed\" })\n"
        "end\n"
        "return script\n";

    OpenYAMM::Game::PartySeed seed = {};
    seed.members.resize(2);
    seed.members[0].might = 10;
    seed.members[0].speed = 10;
    seed.members[1].might = 20;
    seed.members[1].speed = 20;

    OpenYAMM::Game::Party party = {};
    party.seed(seed);
    OpenYAMM::Game::Mm9DialoguePackage package = makePackage(luaText);
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    setOwner(dialogueRuntime);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    std::optional<std::string> error;
    REQUIRE(runTestLabel(scriptRuntime, error));
    CHECK_FALSE(error.has_value());

    REQUIRE(dialogueRuntime.party().member(0) != nullptr);
    REQUIRE(dialogueRuntime.party().member(1) != nullptr);
    CHECK(scriptRuntime.getScriptNumVar("nMight", 0) == 15);
    CHECK(scriptRuntime.getScriptNumVar("nSpeed", 0) == 13);
    CHECK(dialogueRuntime.party().member(0)->permanentBonuses.might == 5);
    CHECK(dialogueRuntime.party().member(0)->magicalBonuses.speed == 3);
    CHECK(dialogueRuntime.party().member(1)->permanentBonuses.might == 0);
    CHECK(dialogueRuntime.party().member(1)->magicalBonuses.speed == 3);
    REQUIRE(scriptRuntime.state().attributeEffects.size() == 2);

    REQUIRE(scriptRuntime.advanceScriptTime(9.0, error));
    CHECK(dialogueRuntime.party().member(0)->magicalBonuses.speed == 3);
    CHECK(dialogueRuntime.party().member(1)->magicalBonuses.speed == 3);

    OpenYAMM::Game::Party restoredParty = dialogueRuntime.party();
    OpenYAMM::Game::Mm9DialogueRuntime restoredDialogueRuntime(package, restoredParty);
    setOwner(restoredDialogueRuntime);
    OpenYAMM::Game::Mm9ScriptRuntime restoredRuntime(package, restoredDialogueRuntime);
    restoredRuntime.restoreState(scriptRuntime.state());
    REQUIRE(restoredRuntime.advanceScriptTime(1.0, error));
    REQUIRE(restoredDialogueRuntime.party().member(0) != nullptr);
    REQUIRE(restoredDialogueRuntime.party().member(1) != nullptr);
    CHECK(restoredDialogueRuntime.party().member(0)->magicalBonuses.speed == 0);
    CHECK(restoredDialogueRuntime.party().member(1)->magicalBonuses.speed == 0);
    CHECK(restoredRuntime.state().attributeEffects.empty());
}

TEST_CASE("MM9 script runtime SetParam updates active owner parameters")
{
    const std::string luaText =
        "local script = { labels = {} }\n"
        "script.labels.OnUse = function(ctx)\n"
        "  ctx:getParam(0, { line = 1, args = \"0, before\", raw = \"GetParam 0, before\" })\n"
        "  ctx:command(\"SetParam\", \"0, Changed\", { line = 2, raw = \"SetParam 0, Changed\" })\n"
        "  ctx:command(\"SetParam\", \"2, 42\", { line = 3, raw = \"SetParam 2, 42\" })\n"
        "  ctx:command(\"GetParam\", \"0, after\", { line = 4, raw = \"GetParam 0, after\" })\n"
        "  ctx:getParam(2, { line = 5, args = \"2, numberParam\", raw = \"GetParam 2, numberParam\" })\n"
        "end\n"
        "return script\n";

    OpenYAMM::Game::Party party = makeParty();
    OpenYAMM::Game::Mm9DialoguePackage package = makePackage(luaText);
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    setOwner(dialogueRuntime);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    std::optional<std::string> error;
    REQUIRE(runTestLabel(scriptRuntime, error));
    CHECK_FALSE(error.has_value());

    CHECK(scriptRuntime.getScriptStrVar("before") == "1");
    CHECK(scriptRuntime.getScriptStrVar("after") == "Changed");
    CHECK(scriptRuntime.getScriptStrVar("numberParam") == "42");
    CHECK(scriptRuntime.getScriptNumVar("numberParam", 0) == 42);
    REQUIRE(dialogueRuntime.owner().scriptParams.size() == 3);
    CHECK(dialogueRuntime.owner().scriptParams[0] == "Changed");
    CHECK(dialogueRuntime.owner().scriptParams[2] == "42");
    REQUIRE(scriptRuntime.controlRequests().size() == 2);
    CHECK(scriptRuntime.controlRequests()[0].operation == "setparam");
    CHECK(scriptRuntime.controlRequests()[1].operation == "setparam");
}

TEST_CASE("MM9 script runtime accepts one-off and malformed legacy command tokens")
{
    const std::string luaText =
        "local script = { labels = {} }\n"
        "script.labels[\"OnUse\"] = function(ctx)\n"
        "  ctx:command(\"GetMyHandle\", \"hMe\", { line = 1, raw = \"GetMyHandle hMe\" })\n"
        "  ctx:command(\"SetPos\", \"hMe, 10, 20, 30\", { line = 2, raw = \"SetPos hMe, 10,20,30\" })\n"
        "  ctx:command(\"FaceDir\", \"1, 0, 0\", { line = 3, raw = \"FaceDir 1,0,0\" })\n"
        "  ctx:command(\"if(n_istriggered==1)\", \"\", "
        "{ line = 4, raw = \"if(n_istriggered==1)\" })\n"
        "  ctx:command(\"while(nTemp>0)\", \"\", { line = 5, raw = \"while(nTemp>0)\" })\n"
        "  ctx:command(\"Rotate(\", \"0, 0, 1, 90, 10, RotateDone )\", "
        "{ line = 6, raw = \"Rotate( 0,0,1,90,10,RotateDone )\" })\n"
        "  ctx:command(\"GetPOS(\", \"hMe, px, py, pz )\", "
        "{ line = 7, raw = \"GetPOS( hMe, px, py, pz )\" })\n"
        "  ctx:command(\"GetFaceDir(\", \"hMe, fx, fy, fz )\", "
        "{ line = 8, raw = \"GetFaceDir( hMe, fx, fy, fz )\" })\n"
        "  ctx:command(\"NormalizeVector(\", \"fx, fy, fz )\", "
        "{ line = 9, raw = \"NormalizeVector( fx, fy, fz )\" })\n"
        "  ctx:command(\"GetRightDir\", \"hMe, rx, ry, rz\", "
        "{ line = 10, raw = \"GetRightDir hMe, rx, ry, rz\" })\n"
        "  ctx:command(\"GetForwardDir\", \"hMe, f2x, f2y, f2z\", "
        "{ line = 11, raw = \"GetForwardDir hMe, f2x, f2y, f2z\" })\n"
        "  ctx:command(\"GetReverseDir\", \"hMe, revx, revy, revz\", "
        "{ line = 12, raw = \"GetReverseDir hMe, revx, revy, revz\" })\n"
        "  ctx:command(\"GetSocketPos\", \"RHand1, sx, sy, sz\", "
        "{ line = 13, raw = \"GetSocketPos RHand1, sx, sy, sz\" })\n"
        "  ctx:command(\"GetRotation(\", \"hMe, rotx, roty, rotz, spin )\", "
        "{ line = 14, raw = \"GetRotation( hMe, rotx, roty, rotz, spin )\" })\n"
        "  ctx:command(\"GetAngleToPos\", \"1, 2, 3, angle\", "
        "{ line = 15, raw = \"GetAngleToPos 1, 2, 3, angle\" })\n"
        "  ctx:command(\"PlayAnim\", \"Wave, AnimDone\", { line = 16, raw = \"PlayAnim Wave, AnimDone\" })\n"
        "  ctx:command(\"GetCurrAnim\", \"hMe, animIndex\", "
        "{ line = 17, raw = \"GetCurrAnim hMe animIndex\" })\n"
        "  ctx:command(\"GetAnimName\", \"hMe, animIndex, animName\", "
        "{ line = 18, raw = \"GetAnimName hMe animIndex animName\" })\n"
        "  ctx:command(\"GetPlayersWithinDist\", \"0, 0, 0, 512, playerIds, 8, playerCount\", "
        "{ line = 19, raw = \"GetPlayersWithinDist 0,0,0,512,playerIds,8,playerCount\" })\n"
        "  ctx:command(\"AddNPC\", \"2, hNpc\", { line = 20, raw = \"AddNPC 2 hNpc\" })\n"
        "  ctx:command(\"RemoveNPC\", \"2, hNpc\", { line = 21, raw = \"RemoveNPC 2 hNpc\" })\n"
        "  ctx:command(\"GetContainerCount\", \"hPlayer, nContainer\", "
        "{ line = 22, raw = \"GetContainerCount hPlayer nContainer\" })\n"
        "  ctx:command(\"Spawn2\", \"hMonster, 1, 2, 3, 1, 0, 0, MonsterScript\", "
        "{ line = 23, raw = \"Spawn2 hMonster 1 2 3 1 0 0 MonsterScript\" })\n"
        "  ctx:command(\"SetInt\", \"sOut, hMe\", { line = 24, raw = \"SetInt sOut hMe\" })\n"
        "  ctx:command(\"Speak\", \"cinematic\\\\blood2.wav, SpeakDone\", "
        "{ line = 25, raw = \"Speak cinematic\\\\blood2.wav, SpeakDone\" })\n"
        "  ctx:command(\"CheckWorldCollision\", \"1, 2, 3, nx, ny, nz, hit, hMe\", "
        "{ line = 26, raw = \"CheckWorldCollision 1,2,3,nx,ny,nz,hit,hMe\" })\n"
        "  ctx:command(\"GetCrossProduct(\", \"1, 0, 0, 0, 1, 0, cx, cy, cz )\", "
        "{ line = 27, raw = \"GetCrossProduct( 1,0,0,0,1,0,cx,cy,cz )\" })\n"
        "  ctx:command(\"CreateFX\", \"spell, hMe, 1\", { line = 28, raw = \"CreateFX spell hMe 1\" })\n"
        "  ctx:command(\"EstimateRangeAttackHit\", \"hMe\", "
        "{ line = 29, raw = \"EstimateRangeAttackHit hMe\" })\n"
        "  ctx:command(\"SetTargetLostTime\", \"30\", { line = 30, raw = \"SetTargetLostTime 30\" })\n"
        "  ctx:command(\"Help\", \"hMe\", { line = 31, raw = \"Help hMe\" })\n"
        "  ctx:command(\"Land\", \"\", { line = 32, raw = \"Land\" })\n"
        "  ctx:command(\"Strafe\", \"1, 0, 0, FALSE\", { line = 33, raw = \"Strafe 1,0,0,FALSE\" })\n"
        "  ctx:command(\"TurnLeft\", \"90\", { line = 34, raw = \"TurnLeft 90\" })\n"
        "  ctx:command(\"IsMoving\", \"bMoving\", { line = 35, raw = \"IsMoving bMoving\" })\n"
        "  ctx:command(\"IsFacing\", \"hMe, bFacing\", { line = 36, raw = \"IsFacing hMe, bFacing\" })\n"
        "  ctx:command(\"SetAnimPlaying\", \"FALSE\", { line = 37, raw = \"SetAnimPlaying FALSE\" })\n"
        "  ctx:command(\"ConsoleCommand\", \"NumConsoleLines 1\", "
        "{ line = 38, raw = \"ConsoleCommand NumConsoleLines 1\" })\n"
        "  ctx:command(\"DoHighScore\", \"\", { line = 39, raw = \"DoHighScore\" })\n"
        "  ctx:command(\"KillCallback\", \"0\", { line = 40, raw = \"KillCallback 0\" })\n"
        "  ctx:command(\"SavePath\", \"\", { line = 41, raw = \"SavePath\" })\n"
        "  ctx:command(\"RestorePath\", \"\", { line = 42, raw = \"RestorePath\" })\n"
        "  ctx:command(\"RemoveModelKey\", \"Rattack\", { line = 43, raw = \"RemoveModelKey Rattack\" })\n"
        "  ctx:command(\"GetPlayerId\", \"hMe, playerId\", { line = 44, raw = \"GetPlayerId hMe playerId\" })\n"
        "  ctx:command(\"GetPlayerNbr\", \"hMe, playerNbr\", { line = 45, raw = \"GetPlayerNbr hMe playerNbr\" })\n"
        "end\n"
        "return script\n";

    OpenYAMM::Game::Party party = makeParty();
    OpenYAMM::Game::Mm9DialoguePackage package = makePackage(luaText);
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    setOwner(dialogueRuntime);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    std::optional<std::string> error;
    REQUIRE(runTestLabel(scriptRuntime, error));
    CHECK_FALSE(error.has_value());
    CHECK(scriptRuntime.unimplementedCommands().empty());
    CHECK(scriptRuntime.getScriptNumVar("px", 0) == 10);
    CHECK(scriptRuntime.getScriptNumVar("py", 0) == 20);
    CHECK(scriptRuntime.getScriptNumVar("pz", 0) == 30);
    CHECK(scriptRuntime.getScriptNumVar("fx", 0) == 1);
    CHECK(scriptRuntime.getScriptNumVar("rx", 1) == 0);
    CHECK(scriptRuntime.getScriptNumVar("ry", 0) == -1);
    CHECK(scriptRuntime.getScriptNumVar("f2x", 0) == 1);
    CHECK(scriptRuntime.getScriptNumVar("revx", 0) == -1);
    CHECK(scriptRuntime.getScriptNumVar("sx", 0) == 10);
    CHECK(scriptRuntime.getScriptNumVar("spin", -1) == 0);
    CHECK(scriptRuntime.getScriptNumVar("angle", -1) == 0);
    CHECK(scriptRuntime.getScriptNumVar("animIndex", -1) == 0);
    CHECK(scriptRuntime.getScriptStrVar("animName") == "Wave");
    CHECK(scriptRuntime.getScriptNumVar("playerCount", 0) == 1);
    CHECK(scriptRuntime.getObjectHandleVar("hNpc") == "mm9:npc:2");
    CHECK(scriptRuntime.getScriptNumVar("nContainer", -1) == 0);
    CHECK(scriptRuntime.getObjectHandleVar("hMonster") == "mm9:spawn:1");
    CHECK(scriptRuntime.getObjectHandleVar("sOut") == "mm9:testmap:object:7");
    CHECK(scriptRuntime.getScriptNumVar("nx", -1) == 0);
    CHECK(scriptRuntime.getScriptNumVar("ny", -1) == 0);
    CHECK(scriptRuntime.getScriptNumVar("nz", 0) == 1);
    CHECK(scriptRuntime.getScriptNumVar("hit", -1) == 0);
    CHECK(scriptRuntime.getScriptNumVar("cx", -1) == 0);
    CHECK(scriptRuntime.getScriptNumVar("cy", -1) == 0);
    CHECK(scriptRuntime.getScriptNumVar("cz", 0) == 1);
    CHECK(scriptRuntime.getScriptNumVar("bMoving", 0) == 1);
    CHECK(scriptRuntime.getScriptNumVar("bFacing", 0) == 1);
    CHECK(scriptRuntime.getScriptNumVar("playerId", -1) == 0);
    CHECK(scriptRuntime.getScriptNumVar("playerNbr", -1) == 0);

    const OpenYAMM::Game::Mm9ScriptRuntimeState &state = scriptRuntime.state();
    REQUIRE(state.controlRequests.size() == 8);
    CHECK(state.controlRequests[0].operation == "if");
    CHECK(state.controlRequests[1].operation == "while");
    CHECK(state.controlRequests.back().operation == "removemodelkey");
    REQUIRE(state.movementRequests.size() == 3);
    CHECK(state.movementRequests[0].operation == "rotate");
    CHECK(state.movementRequests[1].operation == "strafe");
    CHECK(state.movementRequests[2].operation == "turnleft");
    REQUIRE(scriptRuntime.clientFxRequests().size() == 1);
    CHECK(scriptRuntime.clientFxRequests()[0].operation == "createfx");
    CHECK(state.clientFxRequests.size() == 1);
    CHECK(state.clientFxRequests[0].effectName == "spell");
    REQUIRE(scriptRuntime.audioRequests().size() == 1);
    CHECK(scriptRuntime.audioRequests()[0].operation == "speak");
    REQUIRE(scriptRuntime.aiRequests().size() == 3);
    CHECK(scriptRuntime.aiRequests()[0].operation == "estimaterangeattackhit");
    CHECK(state.objectStats.at("mm9:testmap:object:7").at("TargetLostTime") == 30);
    CHECK(state.scriptStrArrays.at("playerIds").at(0) == "mm9:player");
    REQUIRE(state.spawnRequests.size() == 1);
    CHECK(state.spawnRequests[0].parameter == "1, 0, 0, MonsterScript");
    REQUIRE(scriptRuntime.partyCommandRequests().size() == 2);
    CHECK(scriptRuntime.partyCommandRequests()[0].operation == "addnpc");
    CHECK(scriptRuntime.partyCommandRequests()[1].operation == "removenpc");
}

TEST_CASE("MM9 script runtime records include-only AI helper commands")
{
    const std::string luaText =
        "local script = { labels = {} }\n"
        "script.labels[\"OnUse\"] = function(ctx)\n"
        "  ctx:command(\"GetMyHandle\", \"hMe\", { line = 1, raw = \"GetMyHandle hMe\" })\n"
        "  ctx:command(\"GetObjectHandle\", \"TargetMarker, hTarget\", "
        "{ line = 2, raw = \"GetObjectHandle TargetMarker, hTarget\" })\n"
        "  ctx:command(\"Target\", \"hTarget, TRUE\", { line = 3, raw = \"Target hTarget, TRUE\" })\n"
        "  ctx:command(\"FaceDir\", \"1, 0, 0\", { line = 4, raw = \"FaceDir 1,0,0\" })\n"
        "  ctx:command(\"Sin\", \"90, sinOut\", { line = 5, raw = \"Sin 90, sinOut\" })\n"
        "  ctx:command(\"Cos\", \"0, cosOut\", { line = 6, raw = \"Cos 0, cosOut\" })\n"
        "  ctx:command(\"VecMag\", \"3, 4, 0, magOut\", { line = 7, raw = \"VecMag 3,4,0,magOut\" })\n"
        "  ctx:command(\"VecAngle\", \"1, 0, 0, 0, 1, 0, angleOut\", "
        "{ line = 8, raw = \"VecAngle 1,0,0,0,1,0,angleOut\" })\n"
        "  ctx:command(\"GetLeftDir\", \"lx, ly, lz\", { line = 9, raw = \"GetLeftDir lx,ly,lz\" })\n"
        "  ctx:command(\"SetRotation\", \"0, 1, 0, 0, 15\", "
        "{ line = 10, raw = \"SetRotation 0,1,0,0,15\" })\n"
        "  ctx:command(\"CalcRotationRate\", \"hMe, 12, rotateRate\", "
        "{ line = 11, raw = \"CalcRotationRate hMe,12,rotateRate\" })\n"
        "  ctx:command(\"CanReachTarget\", \"canReach\", { line = 12, raw = \"CanReachTarget canReach\" })\n"
        "  ctx:command(\"CanReachObject\", \"hTarget, canReachObject\", "
        "{ line = 13, raw = \"CanReachObject hTarget,canReachObject\" })\n"
        "  ctx:command(\"CastRay\", \"0, 0, 0, 100, rayHandle, rayHit\", "
        "{ line = 14, raw = \"CastRay 0,0,0,100,rayHandle,rayHit\" })\n"
        "  ctx:command(\"FindHidingPlace\", \"hHide\", { line = 15, raw = \"FindHidingPlace hHide\" })\n"
        "  ctx:command(\"GetObjectTarget\", \"hMe, hObjectTarget\", "
        "{ line = 16, raw = \"GetObjectTarget hMe,hObjectTarget\" })\n"
        "  ctx:command(\"IsObjectActive\", \"hTarget, bActive\", "
        "{ line = 17, raw = \"IsObjectActive hTarget,bActive\" })\n"
        "  ctx:command(\"IsWorldObject\", \"hTarget, bWorld\", "
        "{ line = 18, raw = \"IsWorldObject hTarget,bWorld\" })\n"
        "  ctx:command(\"IsDead\", \"hTarget, bDead\", { line = 19, raw = \"IsDead hTarget,bDead\" })\n"
        "  ctx:command(\"ShouldRunAway\", \"hTarget, bRunAway\", "
        "{ line = 20, raw = \"ShouldRunAway hTarget,bRunAway\" })\n"
        "  ctx:command(\"SetCrouch\", \"TRUE\", { line = 21, raw = \"SetCrouch TRUE\" })\n"
        "  ctx:command(\"SetCondition\", \"13\", { line = 22, raw = \"SetCondition 13\" })\n"
        "  ctx:command(\"ClearCondition\", \"13\", { line = 23, raw = \"ClearCondition 13\" })\n"
        "  ctx:command(\"SetStuck\", \"\", { line = 24, raw = \"SetStuck\" })\n"
        "  ctx:command(\"OnEnrage\", \"Enraged\", { line = 25, raw = \"OnEnrage Enraged\" })\n"
        "  ctx:command(\"OnFearDone\", \"FearDone\", { line = 26, raw = \"OnFearDone FearDone\" })\n"
        "  ctx:command(\"OnPlayerInterrupt\", \"Interrupted\", "
        "{ line = 27, raw = \"OnPlayerInterrupt Interrupted\" })\n"
        "  ctx:command(\"OnTargetHit\", \"TargetHit\", { line = 28, raw = \"OnTargetHit TargetHit\" })\n"
        "  ctx:command(\"PlayAnimation\", \"Threat, FALSE, ThreatDone\", "
        "{ line = 29, raw = \"PlayAnimation Threat,FALSE,ThreatDone\" })\n"
        "  ctx:command(\"PlayAnimSound\", \"JumpingDown, 0\", "
        "{ line = 30, raw = \"PlayAnimSound JumpingDown,0\" })\n"
        "end\n"
        "return script\n";

    OpenYAMM::Game::Party party = makeParty();
    OpenYAMM::Game::Mm9DialoguePackage package = makePackage(luaText);
    OpenYAMM::Game::Mm9DialogueRuntime dialogueRuntime(package, party);
    setOwner(dialogueRuntime);
    OpenYAMM::Game::Mm9ScriptRuntime scriptRuntime(package, dialogueRuntime);

    std::optional<std::string> error;
    REQUIRE(runTestLabel(scriptRuntime, error));
    CHECK_FALSE(error.has_value());
    CHECK(scriptRuntime.unimplementedCommands().empty());
    CHECK(scriptRuntime.getScriptNumVar("sinOut", 0) == 1);
    CHECK(scriptRuntime.getScriptNumVar("cosOut", 0) == 1);
    CHECK(scriptRuntime.getScriptNumVar("magOut", 0) == 5);
    CHECK(scriptRuntime.getScriptNumVar("angleOut", 0) == 90);
    CHECK(scriptRuntime.getScriptNumVar("ly", 0) == 1);
    CHECK(scriptRuntime.getScriptNumVar("rotateRate", 0) == 12);
    CHECK(scriptRuntime.getScriptNumVar("canReach", 0) == 1);
    CHECK(scriptRuntime.getScriptNumVar("canReachObject", 0) == 1);
    CHECK(scriptRuntime.getObjectHandleVar("rayHandle") == "mm9:testmap:object:7");
    CHECK(scriptRuntime.getScriptNumVar("rayHit", -1) == 0);
    CHECK(scriptRuntime.getObjectHandleVar("hHide") == "mm9:testmap:object:7");
    CHECK(scriptRuntime.getObjectHandleVar("hObjectTarget") == "mm9:testmap:object:8");
    CHECK(scriptRuntime.getScriptNumVar("bActive", 0) == 1);
    CHECK(scriptRuntime.getScriptNumVar("bWorld", 0) == 1);
    CHECK(scriptRuntime.getScriptNumVar("bDead", -1) == 0);
    CHECK(scriptRuntime.getScriptNumVar("bRunAway", -1) == 0);

    const OpenYAMM::Game::Mm9ScriptRuntimeState &state = scriptRuntime.state();
    CHECK(state.objectStats.at("mm9:testmap:object:7").at("Crouch") == 1);
    CHECK(state.objectAiStates.at("mm9:testmap:object:7") == "stuck");
    REQUIRE(state.movementRequests.size() == 1);
    CHECK(state.movementRequests[0].operation == "setrotation");
    REQUIRE(scriptRuntime.animationRequests().size() == 2);
    CHECK(scriptRuntime.animationRequests()[0].operation == "playanimation");
    CHECK(scriptRuntime.animationRequests()[0].callbackLabel == "ThreatDone");
    CHECK(scriptRuntime.animationRequests()[1].operation == "playanimsound");

    const auto hasCallback = [&](const std::string &kind, const std::string &label)
    {
        const std::vector<OpenYAMM::Game::Mm9ScriptRuntimeCallback> &callbacks =
            scriptRuntime.registeredCallbacks();
        return std::any_of(
            callbacks.begin(),
            callbacks.end(),
            [&](const OpenYAMM::Game::Mm9ScriptRuntimeCallback &callback)
            {
                return callback.kind == kind && callback.label == label;
            });
    };
    CHECK(hasCallback("onenrage", "Enraged"));
    CHECK(hasCallback("onfeardone", "FearDone"));
    CHECK(hasCallback("onplayerinterrupt", "Interrupted"));
    CHECK(hasCallback("ontargethit", "TargetHit"));
    CHECK(hasCallback("playanimation", "ThreatDone"));
}

TEST_CASE("MM9 script runtime generated fallback command surface is statically covered")
{
    const std::filesystem::path scriptsRoot =
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds/mm9/scripts";
    REQUIRE(std::filesystem::exists(scriptsRoot));

    const std::regex commandPattern(R"mm9(ctx:command\("((?:\\.|[^"\\])*)", "((?:\\.|[^"\\])*)")mm9");
    const std::set<std::string> &implementedCommands = implementedGeneratedFallbackCommandsTest();
    std::set<std::string> missingCommands;
    std::vector<std::string> missingContexts;
    size_t commandCalls = 0;

    for (const std::filesystem::directory_entry &entry :
        std::filesystem::recursive_directory_iterator(scriptsRoot))
    {
        if (!entry.is_regular_file() || entry.path().extension() != ".lua")
        {
            continue;
        }

        const std::string text = readGeneratedScriptTextTest(entry.path());
        for (std::sregex_iterator iterator(text.begin(), text.end(), commandPattern), end; iterator != end; ++iterator)
        {
            ++commandCalls;
            const std::string command =
                normalizeGeneratedFallbackCommandTest((*iterator)[1].str(), (*iterator)[2].str());
            const std::string argumentsText = trimGeneratedCommandTest((*iterator)[2].str());
            if (!argumentsText.empty() && argumentsText.front() == '=')
            {
                continue;
            }
            if (implementedCommands.count(command) != 0)
            {
                continue;
            }

            missingCommands.insert(command);
            if (missingContexts.size() < 20)
            {
                missingContexts.push_back(entry.path().lexically_relative(scriptsRoot).string() + ": " + command);
            }
        }
    }

    std::ostringstream missingStream;
    for (const std::string &context : missingContexts)
    {
        missingStream << context << "\n";
    }

    INFO("Missing generated MM9 fallback commands:\n" << missingStream.str());
    CHECK(commandCalls > 0);
    CHECK(missingCommands.empty());
}
