#pragma once

#include "game/gameplay/GameplayActorAiTypes.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <optional>
#include <string>
#include <string_view>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Game
{
// The decision trace (devdocs/mm9_rework/MM9_MONSTER_AI_PLAN.md "The decision trace",
// tests/scenarios/mm9/ai/README.md): what the AI decided (ActorStateUpdate::decision) and the changes the world sees (spawn, motion state, target,
// damage, death), as log lines, a per-actor ring for the GUI overlay and a list the scenario asserts read. A world
// runtime feeds it only while one is bound (an AI arena); unbound it costs nothing.

const char *actorAiDecisionName(ActorAiDecisionKind kind);
std::optional<ActorAiDecisionKind> actorAiDecisionFromName(std::string_view name);
const char *actorAiMotionStateName(ActorAiMotionState state);
const char *actorAiAttackAbilityName(GameplayActorAttackAbility ability);
// "party", "actor:<index>" or "none".
std::string actorAiTargetText(ActorAiTargetKind kind, size_t actorIndex);
// The decision's note, ability, chance and roll, e.g. "ability attack1 chance 0.80 roll 0.13".
std::string actorAiDecisionDetail(const ActorAiDecision &decision);

// The world events the trace records besides decisions; `impact` is the moment an attack applies (its blow lands, its
// missile leaves or its spell is cast); `anim` is the 3D model's presentation (animation tracing).
inline constexpr std::array<std::string_view, 9> ActorAiTraceEventNames = {
    "spawn", "motion", "target", "damaged", "healed", "died", "revived", "impact", "anim"};

struct ActorAiTraceEntry
{
    float timeSeconds = 0.0f;
    size_t actorIndex = 0;
    int16_t monsterId = 0;
    std::string actorName;
    // An AI decision (name: actorAiDecisionName) or a world event (name: one of ActorAiTraceEventNames).
    bool decision = false;
    std::string name;
    std::string target;
    std::string detail;
};

// `[ai] t=12.300 actor=3 monster=9183 "Skeletoid" decision=strafe_attack target=party detail="chance 0.80 roll 0.13"`;
// a world event writes `event=<name>` instead of `decision=`.
std::string formatActorAiTraceLine(const ActorAiTraceEntry &entry);

// One frame of a traced actor's 3D model as WorldFxSystem::syncActorModels poses it: the clip on the main track (the
// whole body, or the legs under a layer) and the clip on the upper-body layer. The trace turns these into `anim` lines
// (ActorAiTrace::observeAnimation).
struct ActorAnimationTraceSample
{
    std::string_view clip;
    float timeSeconds = 0.0f;
    float durationSeconds = 0.0f;
    // The main clip plays backwards (a gait reversed while the actor backs away without a backpedal clip).
    bool reversed = false;
    // The upper-body layer's clip (empty without a layer) and its time.
    std::string_view layerClip;
    float layerTimeSeconds = 0.0f;
    float layerDurationSeconds = 0.0f;
    // Horizontal speed of the body (world units a second).
    float speed = 0.0f;
    float deltaSeconds = 0.0f;
    // The crossfade this frame starts, in seconds; 0 is a cut (the pose jumps); negative when none starts.
    float blendSeconds = -1.0f;
};

// An arena monster's overrides of its AI facts, applied every AI step after the world's own (monster modifiers,
// behaviours): fields by name, e.g. strafe_attack_chance, evade_chance, skirmish, ai_type. New profile fields add a
// row to the table in ActorAiTrace.cpp.
class ActorAiFactsOverride
{
public:
    bool setField(std::string_view name, std::string_view value, std::string &error);
    void apply(ActorAiFacts &actor) const;
    bool empty() const;
    static std::vector<std::string_view> fieldNames();

private:
    ActorAiFacts m_values = {};
    std::vector<size_t> m_fields;
};

// An arena's timed action (tests/scenarios/mm9/ai/README.md "events"), run by the world after the AI step at which
// the trace clock reaches it: a map trigger's evt.WakeActor (wake a dormant actor), evt.SetMonsterRelation (one
// monster row toward another: MM9's HateAll / AddEnemy as the converters' map Lua writes it) or an MM9 trigger message
// to an actor's behaviour script (MM9's Trigger <object>, <message>: its onTrigger); or a test's own move: open a door
// (as a click on it), or walk the party in a straight line to a point over walkSeconds (placed there step by step).
struct ActorAiArenaAction
{
    enum class Kind : uint8_t
    {
        Wake,
        Relation,
        Trigger,
        Door,
        PartyWalk,
    };

    float atSeconds = 0.0f;
    Kind kind = Kind::Wake;
    size_t actorIndex = 0;
    int16_t fromMonsterId = 0;
    int16_t toMonsterId = 0;
    int relation = 0;
    std::string message;
    uint32_t doorId = 0;
    GameplayWorldPoint walkTo = {};
    float walkSeconds = 0.0f;
    // Where the walk began (set at its first step).
    bool walkStarted = false;
    GameplayWorldPoint walkFrom = {};
};

class ActorAiTrace
{
public:
    static constexpr size_t RecentDecisionCount = 3;
    static constexpr size_t MaximumEntries = 200000;
    // The span over which an `anim` line's playback rate is measured.
    static constexpr float AnimationRateWindowSeconds = 0.1f;

    // The playback rate of one track of a traced model: the clip time last seen, the rate measured over the last window
    // (-1 before one), the window so far and the rate last written.
    struct AnimationRateMeter
    {
        float time = 0.0f;
        float rate = -1.0f;
        float advance = 0.0f;
        float seconds = 0.0f;
        float logged = -1.0f;
    };

    // Overlay text for one actor: its last decisions, newest first, anchored above its head.
    struct OverlayItem
    {
        size_t actorIndex = 0;
        GameplayWorldPoint anchor = {};
        std::vector<std::string> lines;
    };

    // Forgets every entry, the clock, the traced actors and their overrides; the log stays open.
    void reset();
    bool openLog(const std::filesystem::path &path, std::string &error);
    void closeLog();
    const std::filesystem::path &logPath() const;
    // Off: the overrides still apply, nothing is recorded.
    void setRecording(bool recording);
    bool recording() const;
    // Animation tracing (arena `trace_animation`, console `arena anim on|off`): the 3D model presentation of the traced
    // actors as `anim` lines. Off by default; the presentation then never calls the trace.
    void setAnimationRecording(bool recording);
    bool recordsAnimation() const;
    // The GUI's decision overlay (console `arena overlay on|off`), on by default.
    void setOverlayVisible(bool visible);
    bool overlayVisible() const;
    // Records only these actors (an arena's monsters) and the actors spawned after them; with none, every visible
    // actor.
    void traceActor(size_t actorIndex);
    void setOverride(size_t actorIndex, const ActorAiFactsOverride &actorOverride);
    void applyOverrides(ActorAiFrameFacts &facts) const;
    // One AI step: the facts the AI saw and its result.
    void observe(const ActorAiFrameFacts &facts, const ActorAiFrameResult &result);
    // One presented frame of a traced actor (one the trace has observed). Writes an `anim` line when the main or layer
    // clip changes, a crossfade or cut starts, or a clip's playback rate moves by more than a quarter:
    // `main=<clip>[ rev] [layer=<clip>] rate=<clip seconds a second>[ layer_rate=<the layer's>] speed=<units a
    // second>[ blend=<seconds>]`.
    void observeAnimation(size_t actorIndex, const ActorAnimationTraceSample &sample);
    // An arena's timed actions (reset() forgets them); runDueActions runs those the clock has reached, once each (the
    // world runtimes call it after observe).
    void scheduleAction(const ActorAiArenaAction &action);
    void runDueActions(IGameplayWorldRuntime &world);
    float timeSeconds() const;
    const std::vector<ActorAiTraceEntry> &entries() const;
    std::vector<OverlayItem> overlayItems() const;

private:
    struct ActorState
    {
        ActorAiMotionState motionState = ActorAiMotionState::Standing;
        ActorAiTargetKind targetKind = ActorAiTargetKind::None;
        size_t targetActorIndex = static_cast<size_t>(-1);
        int hp = 0;
        bool dead = false;
        ActorAiDecisionKind lastDecision = ActorAiDecisionKind::None;
        ActorAiTargetKind lastDecisionTargetKind = ActorAiTargetKind::None;
        size_t lastDecisionTargetActorIndex = static_cast<size_t>(-1);
        GameplayWorldPoint anchor = {};
        // The newest decisions, as overlay lines, newest last.
        std::vector<std::string> recent;
        int16_t monsterId = 0;
        std::string actorName;
        // The presentation last seen (observeAnimation) and the rate of its last `anim` line.
        std::string animClip;
        std::string animLayerClip;
        bool animReversed = false;
        AnimationRateMeter animRate;
        AnimationRateMeter animLayerRate;
        bool animSeen = false;
    };

    bool traces(const ActorAiFacts &actor) const;
    void observeActor(const ActorAiFacts &actor, const ActorAiUpdate *pUpdate);
    void observeDecision(const ActorAiFacts &actor, ActorState &state, const ActorAiDecision &decision);
    void record(const ActorAiFacts &actor, bool decision, std::string name, std::string target, std::string detail);
    void record(size_t actorIndex, int16_t monsterId, std::string actorName, bool decision, std::string name,
        std::string target, std::string detail);

    std::filesystem::path m_logPath;
    std::ofstream m_log;
    bool m_recording = true;
    bool m_recordsAnimation = false;
    bool m_overlayVisible = true;
    float m_timeSeconds = 0.0f;
    std::unordered_set<size_t> m_tracedActors;
    size_t m_lastTracedActor = 0;
    std::unordered_map<size_t, ActorAiFactsOverride> m_overrides;
    std::unordered_map<size_t, ActorState> m_actors;
    std::vector<ActorAiTraceEntry> m_entries;
    std::vector<ActorAiArenaAction> m_actions;
};
}
