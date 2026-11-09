#pragma once

#include <filesystem>
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

struct ScenarioDocument
{
    std::string id;
    std::string title;
    std::string world;
    ScenarioMode mode = ScenarioMode::Hybrid;
    std::vector<std::string> tags;
    std::vector<ScenarioStep> steps;
};

struct ScenarioLoadResult
{
    ScenarioDocument document;
    std::vector<std::string> errors;
};
}
