#pragma once

#include <filesystem>
#include <optional>
#include <string>
#include <vector>

#include <yaml-cpp/yaml.h>

namespace OpenYAMM::Game
{
enum class ScenarioMode
{
    Faithful,
    Hybrid,
    Unitized,
};

enum class ScenarioStepKind
{
    NewGameFlow,
    LoadMap,
    Travel,
    SetPose,
    PressAction,
    PressInteract,
    SpeakNpc,
    SelectTopic,
    AnswerInput,
    InteractTarget,
    InteractActor,
    MovementSegment,
    EnterDoorAt,
    AdvanceRuntime,
    AdvanceGameTime,
    WaitUntil,
    Assert,
    AssertMechanism,
    CombatLoot,
    DamageActor,
    PartyAttack,
    SetRuleset,
    SpawnActor,
    FireActorProjectile,
    BlinkActor,
    ExecuteEvent,
    LuaEvent,
    ChargeActor,
    FrenzyActor,
    AiArena,
    AiTraceDump,
    SetupShortcut,
    GrantItem,
    RulesetBanks,
    ConsoleCommand,
    DebugLaunch,
    WalkTo,
    ClearHostiles,
    PlayLua,
    PartyDefeat,
    Reload,
    PickUp,
    Climb,
    QuickLoad,
    UseItem,
    TurnBasedTurns,
    RightClickPortrait,
    CastSpell,
    PartyCharge,
    Craft,
    CombineGems,
    SaveCheckpoint,
    LoadCheckpoint,
    SaveGame,
    LoadGame,
    Note,
    Todo,
    TraceObservation,
};

struct ScenarioStep
{
    ScenarioStepKind kind = ScenarioStepKind::Assert;
    std::string kindName;
    YAML::Node payload;
    std::filesystem::path sourcePath;
    int sourceLine = 0;
    int traceSourceLine = 0;
    size_t stepIndex = 0;
};

// A scenario's `mods` (devdocs/NAMED_MODS.md): the named mods it plays with. Other scenarios play none.
struct ScenarioMods
{
    // `fixture`: a mods folder beside the scenario, copied into the run's folder, so a `mods enable` or `mods disable`
    // in the run changes only the copy.
    std::filesystem::path fixture;
    // `enabled`: written as the copy's enabled.yml in place of the fixture's.
    std::optional<std::vector<std::string>> enabled;
    // `user_data: true`: the mods folder of the user data (--user-data), as the game reads it.
    bool userData = false;
};

struct ScenarioDocument
{
    std::string id;
    std::string title;
    std::string world;
    ScenarioMode mode = ScenarioMode::Hybrid;
    std::vector<std::string> tags;
    std::optional<ScenarioMods> mods;
    std::vector<ScenarioStep> steps;
};

struct ScenarioLoadResult
{
    ScenarioDocument document;
    std::vector<std::string> errors;
};
}
