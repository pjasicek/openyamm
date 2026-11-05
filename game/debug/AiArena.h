#pragma once

#include "game/gameplay/ActorAiTrace.h"

#include <bx/math.h>

#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <functional>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;
class IGameplayWorldRuntime;

// An AI arena (tests/scenarios/mm9/ai/README.md, devdocs/mm9_rework/MM9_MONSTER_AI_PLAN.md "The arena"): a map with
// its placed actors removed, only the arena's monsters spawned, the party placed, and the AI decision trace on. The
// same file plays in the game window (debug.ai_arena_path, console `arena`) and headless (scenario step ai_arena).
struct AiArenaMonster
{
    int16_t monsterId = 0;
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    std::optional<float> yawRadians;
    bool hostile = true;
    uint32_t group = 0;
    // Fights for the party (a friendly summon), so the arena's monsters can be attacked by someone besides the party.
    bool partyAlly = false;
    // An MM9 placement (the scene actor's mm9_ai map: sight, hearing, runaway_chance, ranged_type, hiding_places ...).
    std::optional<Mm9AiPlacementRecord> mm9Ai;
    ActorAiFactsOverride overrides;
};

struct AiArenaParty
{
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    float yawRadians = 0.0f;
    float pitchRadians = 0.0f;
    // The monsters' blows do no harm (the Immortal cheat's damage immunity).
    bool invulnerable = true;
    // Dismisses members beyond this many (none: keep the party).
    std::optional<size_t> members;
};

// A timed arena event, the map trigger of a test: at the trace time, wake arena monster `wake` (evt.WakeActor), set one
// monster row's relation toward another (evt.SetMonsterRelation, as MM9's HateAll the converters' map Lua writes),
// open a door, or walk the party to a point over some seconds.
struct AiArenaEvent
{
    float atSeconds = 0.0f;
    ActorAiArenaAction::Kind kind = ActorAiArenaAction::Kind::Wake;
    size_t monster = 0;
    int16_t fromMonsterId = 0;
    int16_t toMonsterId = 0;
    int relation = 0;
    std::string message;
    uint32_t doorId = 0;
    GameplayWorldPoint walkTo = {};
    float walkSeconds = 0.0f;
};

struct AiArena
{
    std::filesystem::path sourcePath;
    std::string name;
    std::string world;
    std::string map;
    // The asset root the arena's map lives in, for the reader (the game's own root is chosen at launch).
    std::string assetRoot;
    AiArenaParty party;
    // Removes every actor the map placed (hidden as an event's invisible bit: no loot, experience or events).
    bool clearActors = true;
    bool trace = true;
    // Also trace the monsters' 3D model presentation (ActorAiTrace `anim` lines); headless runs then pose the models.
    bool traceAnimation = false;
    // Seeds the spawns (positions are exact, so only a boss roll would read it).
    uint64_t seed = 1;
    std::vector<AiArenaMonster> monsters;
    std::vector<AiArenaEvent> events;
};

std::optional<AiArena> loadAiArena(const std::filesystem::path &path, std::string &error);
std::optional<AiArena> parseAiArenaText(const std::string &text, const std::filesystem::path &sourcePath,
    std::string &error);

// Clears the map's actors, spawns the arena's monsters with their overrides and binds the trace (reset first) to the
// world. spawnedActorIndices: the monsters' actor indices in arena order.
bool applyAiArenaActors(
    const AiArena &arena,
    IGameplayWorldRuntime &world,
    ActorAiTrace &trace,
    std::vector<size_t> &spawnedActorIndices,
    std::string &error);

// Draws each traced actor's latest decisions above it; project maps a world point to screen pixels (false: behind
// the camera).
void renderAiTraceOverlay(
    const GameplayScreenRuntime &screenRuntime,
    const ActorAiTrace &trace,
    const std::function<bool(const bx::Vec3 &, float &, float &)> &project);
}
