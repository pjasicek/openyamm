#include "game/gameplay/ActorAiTrace.h"

#include "game/gameplay/ActorBehaviorRuntime.h"

#include "game/events/EventRuntime.h"
#include "game/events/ISceneEventContext.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
struct DecisionName
{
    ActorAiDecisionKind kind;
    const char *pName;
    // A decision repeated while it lasts (a chase re-aimed every quarter second) is recorded once until another
    // decision or target comes between; a discrete one (an attack, an evade) every time.
    bool sustained;
};

constexpr auto DecisionNames = std::to_array<DecisionName>({
    {ActorAiDecisionKind::None, "none", true},
    {ActorAiDecisionKind::Stand, "stand", true},
    {ActorAiDecisionKind::Fidget, "fidget", false},
    {ActorAiDecisionKind::Wander, "wander", true},
    {ActorAiDecisionKind::ReturnHome, "return_home", true},
    {ActorAiDecisionKind::Pursue, "pursue", true},
    {ActorAiDecisionKind::Orbit, "orbit", true},
    {ActorAiDecisionKind::WaitCooldown, "wait_cooldown", true},
    {ActorAiDecisionKind::WaitNoShot, "wait_no_shot", true},
    {ActorAiDecisionKind::CrowdHold, "crowd_hold", true},
    {ActorAiDecisionKind::AttackMelee, "attack_melee", false},
    {ActorAiDecisionKind::AttackRanged, "attack_ranged", false},
    {ActorAiDecisionKind::AttackSpell, "attack_spell", false},
    {ActorAiDecisionKind::Flee, "flee", true},
    {ActorAiDecisionKind::BlindWander, "blind_wander", true},
    {ActorAiDecisionKind::StrafeAttack, "strafe_attack", false},
    {ActorAiDecisionKind::Evade, "evade", false},
    {ActorAiDecisionKind::Circle, "circle", false},
    {ActorAiDecisionKind::BackOff, "back_off", false},
    {ActorAiDecisionKind::Taunt, "taunt", false},
    {ActorAiDecisionKind::Throttle, "throttle", true},
    {ActorAiDecisionKind::Detect, "detect", false},
    {ActorAiDecisionKind::TauntDetect, "taunt_detect", false},
    {ActorAiDecisionKind::TauntKill, "taunt_kill", false},
    {ActorAiDecisionKind::Retarget, "retarget", false},
    {ActorAiDecisionKind::GiveUp, "give_up", false},
    {ActorAiDecisionKind::ShotCheck, "shot_check", false},
    {ActorAiDecisionKind::PursuitVeto, "pursuit_veto", true},
    {ActorAiDecisionKind::FleeDecision, "flee_decision", false},
    {ActorAiDecisionKind::Wince, "wince", false},
    {ActorAiDecisionKind::Hold, "hold", true},
    {ActorAiDecisionKind::Unreachable, "unreachable", true},
    {ActorAiDecisionKind::FlyPass, "fly_pass", false},
    {ActorAiDecisionKind::Swoop, "swoop", false},
    {ActorAiDecisionKind::MeleeWindow, "melee_window", false},
    {ActorAiDecisionKind::Scan, "scan", false},
    {ActorAiDecisionKind::PodLaunch, "pod_launch", false},
    {ActorAiDecisionKind::WanderWait, "wander_wait", false},
    {ActorAiDecisionKind::Patrol, "patrol", false},
    {ActorAiDecisionKind::MarkerReached, "marker_reached", false},
    {ActorAiDecisionKind::Leash, "leash", false},
    {ActorAiDecisionKind::SendAlert, "send_alert", false},
    {ActorAiDecisionKind::CallHelp, "call_help", false},
    {ActorAiDecisionKind::Alert, "alert", false},
    {ActorAiDecisionKind::Help, "help", false},
    {ActorAiDecisionKind::Hide, "hide", false},
    {ActorAiDecisionKind::Cower, "cower", false},
    {ActorAiDecisionKind::ResurrectAsk, "resurrect_ask", false},
    {ActorAiDecisionKind::ResurrectAccept, "resurrect_accept", false},
    {ActorAiDecisionKind::Resurrect, "resurrect", false},
    {ActorAiDecisionKind::Raised, "raised", false},
    {ActorAiDecisionKind::OpenDoor, "open_door", false},
    {ActorAiDecisionKind::Wake, "wake", false},
    {ActorAiDecisionKind::SpawnIn, "spawn_in", false},
    {ActorAiDecisionKind::DeathSpawn, "death_spawn", false},
    {ActorAiDecisionKind::TurnHostile, "turn_hostile", false},
    {ActorAiDecisionKind::Script, "script", false},
    {ActorAiDecisionKind::Reposition, "reposition", false},
    {ActorAiDecisionKind::RepositionArrived, "reposition_arrived", false},
    {ActorAiDecisionKind::BackOffRush, "back_off_rush", false},
});

// Every decision kind has a name: a new kind adds its row here.
static_assert(DecisionNames.size() == size_t(ActorAiDecisionKind::BackOffRush) + 1);

const DecisionName *findDecision(ActorAiDecisionKind kind)
{
    for (const DecisionName &entry : DecisionNames)
    {
        if (entry.pName != nullptr && entry.kind == kind)
        {
            return &entry;
        }
    }

    return nullptr;
}

std::string formatFixed(float value, int decimals)
{
    char buffer[32] = {};
    std::snprintf(buffer, sizeof(buffer), "%.*f", decimals, double(value));
    return buffer;
}

bool parseOverrideValue(std::string_view text, float &value, std::string &error)
{
    // std::strtof, not std::from_chars: Android's libc++ has no floating-point from_chars.
    const std::string terminated(text);
    char *pEnd = nullptr;
    const float parsed = terminated.empty() ? 0.0f : std::strtof(terminated.c_str(), &pEnd);

    if (terminated.empty() || pEnd != terminated.c_str() + terminated.size() || !std::isfinite(parsed))
    {
        error = "'" + std::string(text) + "' is not a number";
        return false;
    }

    value = parsed;
    return true;
}

bool parseOverrideValue(std::string_view text, bool &value, std::string &error)
{
    if (text == "true" || text == "1" || text == "yes" || text == "on")
    {
        value = true;
        return true;
    }

    if (text == "false" || text == "0" || text == "no" || text == "off")
    {
        value = false;
        return true;
    }

    error = "'" + std::string(text) + "' is not a boolean";
    return false;
}

bool parseOverrideValue(std::string_view text, GameplayActorAiType &value, std::string &error)
{
    constexpr std::array<std::pair<std::string_view, GameplayActorAiType>, 4> Names = {{
        {"suicide", GameplayActorAiType::Suicide},
        {"wimp", GameplayActorAiType::Wimp},
        {"normal", GameplayActorAiType::Normal},
        {"aggressive", GameplayActorAiType::Aggressive},
    }};

    for (const std::pair<std::string_view, GameplayActorAiType> &entry : Names)
    {
        if (entry.first == text)
        {
            value = entry.second;
            return true;
        }
    }

    error = "'" + std::string(text) + "' is not an AI type (suicide, wimp, normal, aggressive)";
    return false;
}

struct OverrideField
{
    std::string_view name;
    bool (*parse)(ActorAiFacts &values, std::string_view text, std::string &error);
    void (*copy)(ActorAiFacts &target, const ActorAiFacts &values);
};

template <auto Member>
OverrideField tacticsField(std::string_view name)
{
    return {
        name,
        [](ActorAiFacts &values, std::string_view text, std::string &error)
        {
            return parseOverrideValue(text, values.tactics.*Member, error);
        },
        [](ActorAiFacts &target, const ActorAiFacts &values)
        {
            target.tactics.*Member = values.tactics.*Member;
        }};
}

// A reposition modifier parameter (RepositionModifier): only a monster with the modifier takes it.
template <auto Member>
OverrideField repositionField(std::string_view name)
{
    return {
        name,
        [](ActorAiFacts &values, std::string_view text, std::string &error)
        {
            if (!values.tactics.reposition)
            {
                values.tactics.reposition = RepositionModifier{};
            }

            return parseOverrideValue(text, (*values.tactics.reposition).*Member, error);
        },
        [](ActorAiFacts &target, const ActorAiFacts &values)
        {
            if (target.tactics.reposition && values.tactics.reposition)
            {
                (*target.tactics.reposition).*Member = (*values.tactics.reposition).*Member;
            }
        }};
}

template <auto Member>
OverrideField statsField(std::string_view name)
{
    return {
        name,
        [](ActorAiFacts &values, std::string_view text, std::string &error)
        {
            return parseOverrideValue(text, values.stats.*Member, error);
        },
        [](ActorAiFacts &target, const ActorAiFacts &values)
        {
            target.stats.*Member = values.stats.*Member;
        }};
}

template <auto Member>
OverrideField statusField(std::string_view name)
{
    return {
        name,
        [](ActorAiFacts &values, std::string_view text, std::string &error)
        {
            return parseOverrideValue(text, values.status.*Member, error);
        },
        [](ActorAiFacts &target, const ActorAiFacts &values)
        {
            target.status.*Member = values.status.*Member;
        }};
}

// The fields an arena may override, by the names of their data sources (modifiers.yml, behaviors.yml tactics).
const std::vector<OverrideField> &overrideFields()
{
    static const std::vector<OverrideField> fields = {
        tacticsField<&ActorTacticsFacts::skirmish>("skirmish"),
        tacticsField<&ActorTacticsFacts::strafeAttackChance>("strafe_attack_chance"),
        tacticsField<&ActorTacticsFacts::evadeChance>("evade_chance"),
        tacticsField<&ActorTacticsFacts::evadeSeconds>("evade_seconds"),
        tacticsField<&ActorTacticsFacts::backOffSeconds>("back_off_seconds"),
        tacticsField<&ActorTacticsFacts::tauntChance>("taunt_chance"),
        tacticsField<&ActorTacticsFacts::tauntSeconds>("taunt_seconds"),
        tacticsField<&ActorTacticsFacts::rangedMinDistance>("ranged_min_distance"),
        tacticsField<&ActorTacticsFacts::rangedMaxDistance>("ranged_max_distance"),
        tacticsField<&ActorTacticsFacts::traverseRadiansPerSecond>("traverse_radians_per_second"),
        tacticsField<&ActorTacticsFacts::fireToleranceRadians>("fire_tolerance_radians"),
        tacticsField<&ActorTacticsFacts::leadSeconds>("lead_seconds"),
        tacticsField<&ActorTacticsFacts::holdPost>("hold_post"),
        tacticsField<&ActorTacticsFacts::postLeashRadius>("post_leash_radius"),
        repositionField<&RepositionModifier::lostSightSeconds>("reposition_lost_sight_seconds"),
        repositionField<&RepositionModifier::leashRadius>("reposition_leash_radius"),
        repositionField<&RepositionModifier::searchDistance>("reposition_search_distance"),
        repositionField<&RepositionModifier::backOffTriggerDistance>("reposition_back_off_trigger_distance"),
        repositionField<&RepositionModifier::backOffDistance>("reposition_back_off_distance"),
        statsField<&ActorStatsFacts::aiType>("ai_type"),
        statusField<&ActorStatusFacts::suppressLowHealthFlee>("no_flee"),
    };
    return fields;
}

void appendPart(std::string &text, const std::string &part)
{
    if (!part.empty())
    {
        text += text.empty() ? "" : " ";
        text += part;
    }
}
}

const char *actorAiDecisionName(ActorAiDecisionKind kind)
{
    const DecisionName *pEntry = findDecision(kind);
    return pEntry != nullptr ? pEntry->pName : "unknown";
}

std::optional<ActorAiDecisionKind> actorAiDecisionFromName(std::string_view name)
{
    for (const DecisionName &entry : DecisionNames)
    {
        if (entry.pName != nullptr && name == entry.pName)
        {
            return entry.kind;
        }
    }

    return std::nullopt;
}

const char *actorAiMotionStateName(ActorAiMotionState state)
{
    switch (state)
    {
        case ActorAiMotionState::Standing:
            return "standing";
        case ActorAiMotionState::Wandering:
            return "wandering";
        case ActorAiMotionState::Pursuing:
            return "pursuing";
        case ActorAiMotionState::Fleeing:
            return "fleeing";
        case ActorAiMotionState::Stunned:
            return "stunned";
        case ActorAiMotionState::Attacking:
            return "attacking";
        case ActorAiMotionState::Dying:
            return "dying";
        case ActorAiMotionState::Dead:
            return "dead";
    }

    return "unknown";
}

const char *actorAiAttackAbilityName(GameplayActorAttackAbility ability)
{
    switch (ability)
    {
        case GameplayActorAttackAbility::Attack1:
            return "attack1";
        case GameplayActorAttackAbility::Attack2:
            return "attack2";
        case GameplayActorAttackAbility::Spell1:
            return "spell1";
        case GameplayActorAttackAbility::Spell2:
            return "spell2";
    }

    return "unknown";
}

std::string actorAiTargetText(ActorAiTargetKind kind, size_t actorIndex)
{
    if (kind == ActorAiTargetKind::Party)
    {
        return "party";
    }

    if (kind == ActorAiTargetKind::Actor)
    {
        return "actor:" + std::to_string(actorIndex);
    }

    return "none";
}

std::string actorAiDecisionDetail(const ActorAiDecision &decision)
{
    std::string detail = decision.pNote != nullptr ? decision.pNote : "";

    if (decision.hasAbility)
    {
        appendPart(detail, std::string("ability ") + actorAiAttackAbilityName(decision.ability));
    }

    if (decision.chance >= 0.0f)
    {
        appendPart(detail, "chance " + formatFixed(decision.chance, 2));
    }

    if (decision.roll >= 0.0f)
    {
        appendPart(detail, "roll " + formatFixed(decision.roll, 2));
    }

    if (decision.marker >= 0)
    {
        appendPart(detail, "marker " + std::to_string(decision.marker));
    }

    if (decision.variant >= 0)
    {
        appendPart(detail, "variant " + std::to_string(decision.variant));
    }

    if (decision.seconds >= 0.0f)
    {
        appendPart(detail, "seconds " + formatFixed(decision.seconds, 2));
    }

    if (decision.hasPoint)
    {
        appendPart(detail, "at " + std::to_string(std::lround(decision.point.x)) + " "
            + std::to_string(std::lround(decision.point.y)) + " " + std::to_string(std::lround(decision.point.z)));
    }

    if (decision.checks >= 0)
    {
        appendPart(detail, "checks " + std::to_string(decision.checks));
    }

    return detail;
}

std::string formatActorAiTraceLine(const ActorAiTraceEntry &entry)
{
    std::string line = "[ai] t=" + formatFixed(entry.timeSeconds, 3) + " actor=" + std::to_string(entry.actorIndex)
        + " monster=" + std::to_string(entry.monsterId) + " \"" + entry.actorName + "\" "
        + (entry.decision ? "decision=" : "event=") + entry.name;

    if (!entry.target.empty())
    {
        line += " target=" + entry.target;
    }

    if (!entry.detail.empty())
    {
        line += " detail=\"" + entry.detail + "\"";
    }

    return line;
}

bool ActorAiFactsOverride::setField(std::string_view name, std::string_view value, std::string &error)
{
    const std::vector<OverrideField> &fields = overrideFields();

    for (size_t index = 0; index < fields.size(); ++index)
    {
        if (fields[index].name != name)
        {
            continue;
        }

        std::string valueError;

        if (!fields[index].parse(m_values, value, valueError))
        {
            error = "override " + std::string(name) + ": " + valueError;
            return false;
        }

        if (std::find(m_fields.begin(), m_fields.end(), index) == m_fields.end())
        {
            m_fields.push_back(index);
        }

        return true;
    }

    std::string known;

    for (std::string_view fieldName : fieldNames())
    {
        known += (known.empty() ? "" : ", ") + std::string(fieldName);
    }

    error = "unknown override '" + std::string(name) + "' (known: " + known + ")";
    return false;
}

void ActorAiFactsOverride::apply(ActorAiFacts &actor) const
{
    const std::vector<OverrideField> &fields = overrideFields();

    for (size_t index : m_fields)
    {
        fields[index].copy(actor, m_values);
    }
}

bool ActorAiFactsOverride::empty() const
{
    return m_fields.empty();
}

std::vector<std::string_view> ActorAiFactsOverride::fieldNames()
{
    std::vector<std::string_view> names;

    for (const OverrideField &field : overrideFields())
    {
        names.push_back(field.name);
    }

    return names;
}

void ActorAiTrace::reset()
{
    m_timeSeconds = 0.0f;
    m_tracedActors.clear();
    m_overrides.clear();
    m_actors.clear();
    m_entries.clear();
    m_actions.clear();
    m_lastTracedActor = 0;
}

void ActorAiTrace::scheduleAction(const ActorAiArenaAction &action)
{
    m_actions.push_back(action);
}

namespace
{
// Opens a map door as a click on it would (its mechanism to Open).
void openArenaDoor(IGameplayWorldRuntime &world, uint32_t doorId)
{
    ISceneEventContext *pScene = dynamic_cast<ISceneEventContext *>(&world);
    EventRuntimeState *pEventState = world.eventRuntimeState();
    const MapDeltaData *pMapDeltaData = pScene != nullptr ? pScene->mapDeltaData() : nullptr;

    if (pEventState == nullptr || pMapDeltaData == nullptr)
    {
        return;
    }

    const auto door = std::find_if(pMapDeltaData->doors.begin(), pMapDeltaData->doors.end(),
        [doorId](const MapDeltaDoor &candidate) { return candidate.doorId == doorId; });

    if (door == pMapDeltaData->doors.end())
    {
        return;
    }

    auto [iterator, inserted] = pEventState->mechanisms.try_emplace(doorId);
    RuntimeMechanismState &mechanism = iterator->second;

    if (inserted)
    {
        mechanism.state = door->state;
        mechanism.timeSinceTriggeredMs = float(door->timeSinceTriggered);
        mechanism.currentDistance = EventRuntime::calculateMechanismDistance(*door, mechanism);
        mechanism.isMoving = door->state == static_cast<uint16_t>(EvtMechanismState::Opening)
            || door->state == static_cast<uint16_t>(EvtMechanismState::Closing);
    }

    EventRuntime::applyMechanismAction(mechanism, &*door, MechanismAction::Open);
}
}

void ActorAiTrace::runDueActions(IGameplayWorldRuntime &world)
{
    for (size_t index = 0; index < m_actions.size();)
    {
        ActorAiArenaAction &walk = m_actions[index];

        if (walk.atSeconds > m_timeSeconds)
        {
            ++index;
            continue;
        }

        // A party walk places the party along its line every step until it arrives.
        if (walk.kind == ActorAiArenaAction::Kind::PartyWalk)
        {
            if (!walk.walkStarted)
            {
                walk.walkStarted = true;
                walk.walkFrom = {world.partyX(), world.partyY(), world.partyFootZ()};
            }

            const float share = walk.walkSeconds > 0.0f
                ? std::clamp((m_timeSeconds - walk.atSeconds) / walk.walkSeconds, 0.0f, 1.0f) : 1.0f;
            world.teleportParty(walk.walkFrom.x + (walk.walkTo.x - walk.walkFrom.x) * share,
                walk.walkFrom.y + (walk.walkTo.y - walk.walkFrom.y) * share,
                walk.walkFrom.z + (walk.walkTo.z - walk.walkFrom.z) * share);

            if (share < 1.0f)
            {
                ++index;
                continue;
            }
        }

        const ActorAiArenaAction action = m_actions[index];
        m_actions.erase(m_actions.begin() + std::ptrdiff_t(index));

        if (action.kind == ActorAiArenaAction::Kind::Wake)
        {
            if (ISceneEventContext *pScene = dynamic_cast<ISceneEventContext *>(&world))
            {
                pScene->wakeMapActors(action.actorIndex, 0);
            }
        }
        else if (action.kind == ActorAiArenaAction::Kind::Door)
        {
            openArenaDoor(world, action.doorId);
        }
        else if (action.kind == ActorAiArenaAction::Kind::Trigger)
        {
            if (ActorBehaviorRuntime *pBehaviors = world.actorBehaviorRuntime())
            {
                pBehaviors->trigger(action.actorIndex, action.message);
            }
        }
        else if (EventRuntimeState *pEventState = world.eventRuntimeState();
                 action.kind == ActorAiArenaAction::Kind::Relation && pEventState != nullptr)
        {
            pEventState->monsterRelationOverrides[EventRuntime::monsterRelationOverrideKey(
                uint32_t(action.fromMonsterId), uint32_t(action.toMonsterId))] = action.relation;
        }
    }
}

bool ActorAiTrace::openLog(const std::filesystem::path &path, std::string &error)
{
    closeLog();
    m_log.open(path, std::ios::out | std::ios::trunc);

    if (!m_log)
    {
        error = "cannot write the AI trace log " + path.string();
        return false;
    }

    m_logPath = path;
    return true;
}

void ActorAiTrace::closeLog()
{
    if (m_log.is_open())
    {
        m_log.close();
    }

    m_logPath.clear();
}

const std::filesystem::path &ActorAiTrace::logPath() const
{
    return m_logPath;
}

void ActorAiTrace::setRecording(bool recording)
{
    m_recording = recording;
}

bool ActorAiTrace::recording() const
{
    return m_recording;
}

void ActorAiTrace::setAnimationRecording(bool recording)
{
    m_recordsAnimation = recording;
}

bool ActorAiTrace::recordsAnimation() const
{
    return m_recording && m_recordsAnimation;
}

void ActorAiTrace::setOverlayVisible(bool visible)
{
    m_overlayVisible = visible;
}

bool ActorAiTrace::overlayVisible() const
{
    return m_overlayVisible;
}

void ActorAiTrace::traceActor(size_t actorIndex)
{
    m_tracedActors.insert(actorIndex);
    m_lastTracedActor = std::max(m_lastTracedActor, actorIndex);
}

void ActorAiTrace::setOverride(size_t actorIndex, const ActorAiFactsOverride &actorOverride)
{
    if (actorOverride.empty())
    {
        m_overrides.erase(actorIndex);
        return;
    }

    m_overrides[actorIndex] = actorOverride;
}

void ActorAiTrace::applyOverrides(ActorAiFrameFacts &facts) const
{
    if (m_overrides.empty())
    {
        return;
    }

    for (std::vector<ActorAiFacts> *pActors : {&facts.activeActors, &facts.backgroundActors})
    {
        for (ActorAiFacts &actor : *pActors)
        {
            const auto iterator = m_overrides.find(actor.actorIndex);

            if (iterator != m_overrides.end())
            {
                iterator->second.apply(actor);
            }
        }
    }
}

bool ActorAiTrace::traces(const ActorAiFacts &actor) const
{
    // An arena's monsters, and what they spawn later (pods, a death spawn: the actors after the last of them).
    return m_tracedActors.empty() ? !actor.status.invisible
        : m_tracedActors.contains(actor.actorIndex) || actor.actorIndex > m_lastTracedActor;
}

void ActorAiTrace::observe(const ActorAiFrameFacts &facts, const ActorAiFrameResult &result)
{
    m_timeSeconds += facts.fixedStepSeconds;

    if (!m_recording)
    {
        return;
    }

    std::unordered_map<size_t, const ActorAiUpdate *> updates;

    for (const ActorAiUpdate &update : result.actorUpdates)
    {
        updates[update.actorIndex] = &update;
    }

    for (const std::vector<ActorAiFacts> *pActors : {&facts.activeActors, &facts.backgroundActors})
    {
        for (const ActorAiFacts &actor : *pActors)
        {
            if (traces(actor))
            {
                const auto iterator = updates.find(actor.actorIndex);
                observeActor(actor, iterator != updates.end() ? iterator->second : nullptr);
            }
        }
    }

    if (m_log.is_open())
    {
        m_log.flush();
    }
}

void ActorAiTrace::observeActor(const ActorAiFacts &actor, const ActorAiUpdate *pUpdate)
{
    const auto [iterator, inserted] = m_actors.try_emplace(actor.actorIndex);
    ActorState &state = iterator->second;
    state.monsterId = actor.identity.monsterId;
    state.actorName = actor.identity.displayName;
    state.anchor = {
        actor.movement.position.x, actor.movement.position.y, actor.movement.position.z + float(actor.stats.height)};

    if (inserted)
    {
        state.motionState = actor.runtime.motionState;
        state.hp = actor.stats.currentHp;
        record(actor, false, "spawn", "", "hp " + std::to_string(actor.stats.currentHp) + " at "
            + formatFixed(actor.movement.position.x, 0) + " " + formatFixed(actor.movement.position.y, 0) + " "
            + formatFixed(actor.movement.position.z, 0));
    }

    if (actor.target.currentKind != state.targetKind
        || (actor.target.currentKind == ActorAiTargetKind::Actor
            && actor.target.currentActorIndex != state.targetActorIndex))
    {
        state.targetKind = actor.target.currentKind;
        state.targetActorIndex = actor.target.currentActorIndex;
        record(actor, false, "target", actorAiTargetText(state.targetKind, state.targetActorIndex), "");
    }

    if (actor.stats.currentHp != state.hp)
    {
        record(actor, false, actor.stats.currentHp < state.hp ? "damaged" : "healed", "",
            "hp " + std::to_string(state.hp) + " -> " + std::to_string(actor.stats.currentHp));
        state.hp = actor.stats.currentHp;
    }

    const ActorAiMotionState motionState =
        pUpdate != nullptr ? pUpdate->state.motionState.value_or(actor.runtime.motionState) : actor.runtime.motionState;

    const bool dead = actor.status.dead || motionState == ActorAiMotionState::Dying
        || motionState == ActorAiMotionState::Dead;

    if (!state.dead && dead)
    {
        state.dead = true;
        record(actor, false, "died", "", "");
    }
    else if (state.dead && !dead && actor.stats.currentHp > 0)
    {
        // Raised again (an MM9 resurrection).
        state.dead = false;
        record(actor, false, "revived", "", "");
    }

    // A behaviour script's own decisions (self:trace), before the step's: the script ran before the AI.
    for (const std::string &line : actor.behavior.mm9Script.traceLines)
    {
        state.lastDecision = ActorAiDecisionKind::Script;
        const ActorMm9State &mm9 = actor.runtime.mm9;
        record(actor, true, "script", actorAiTargetText(mm9.targetKind, mm9.targetActorIndex), line);
        state.recent.push_back(formatFixed(m_timeSeconds, 1) + " script " + line);

        if (state.recent.size() > RecentDecisionCount)
        {
            state.recent.erase(state.recent.begin());
        }
    }

    if (pUpdate != nullptr)
    {
        for (const std::optional<ActorAiDecision> *pDecision :
            {&pUpdate->state.earlierDecision, &pUpdate->state.layerDecision, &pUpdate->state.decision})
        {
            if (*pDecision && (*pDecision)->kind != ActorAiDecisionKind::None)
            {
                observeDecision(actor, state, **pDecision);
            }
        }
    }

    // The attack applies this step: its ability and the time since the attack started.
    if (pUpdate != nullptr && pUpdate->state.attackImpactTriggered.value_or(false)
        && !actor.runtime.attackImpactTriggered)
    {
        record(actor, false, "impact", "", std::string(actorAiAttackAbilityName(actor.runtime.queuedAttackAbility))
            + " at " + formatFixed(std::max(actor.runtime.animationTimeTicks, 0.0f) / 128.0f, 3));
    }

    if (motionState != state.motionState)
    {
        state.motionState = motionState;
        record(actor, false, "motion", "", actorAiMotionStateName(motionState));
    }
}

void ActorAiTrace::observeDecision(const ActorAiFacts &actor, ActorState &state, const ActorAiDecision &decision)
{
    const DecisionName *pName = findDecision(decision.kind);
    const bool repeated = pName != nullptr && pName->sustained && decision.kind == state.lastDecision
        && decision.targetKind == state.lastDecisionTargetKind
        && decision.targetActorIndex == state.lastDecisionTargetActorIndex;

    if (repeated)
    {
        return;
    }

    state.lastDecision = decision.kind;
    state.lastDecisionTargetKind = decision.targetKind;
    state.lastDecisionTargetActorIndex = decision.targetActorIndex;
    const std::string detail = actorAiDecisionDetail(decision);
    record(actor, true, actorAiDecisionName(decision.kind),
        actorAiTargetText(decision.targetKind, decision.targetActorIndex), detail);
    std::string line = formatFixed(m_timeSeconds, 1) + " " + actorAiDecisionName(decision.kind);
    appendPart(line, detail);
    state.recent.push_back(std::move(line));

    if (state.recent.size() > RecentDecisionCount)
    {
        state.recent.erase(state.recent.begin());
    }
}

namespace
{
// Clip seconds per second of one track, across a loop's wrap (no clip advances half its length in one frame), measured
// over at least AnimationRateWindowSeconds: a body moves in AI steps, so single frames read uneven rates. Returns
// whether a window closed (meter.rate is new).
bool measureAnimationRate(ActorAiTrace::AnimationRateMeter &meter, bool sameClip, float timeSeconds,
    float durationSeconds, float deltaSeconds)
{
    bool measured = false;

    if (sameClip)
    {
        float advanced = timeSeconds - meter.time;

        if (durationSeconds > 0.0f && std::abs(advanced) > 0.5f * durationSeconds)
        {
            advanced -= std::copysign(durationSeconds, advanced);
        }

        meter.advance += std::abs(advanced);
        meter.seconds += deltaSeconds;

        if (meter.seconds >= ActorAiTrace::AnimationRateWindowSeconds)
        {
            meter.rate = meter.advance / meter.seconds;
            meter.advance = 0.0f;
            meter.seconds = 0.0f;
            measured = true;
        }
    }
    else
    {
        meter = {};
    }

    meter.time = timeSeconds;
    return measured;
}

// A measured rate moved enough since the rate last written to deserve a line of its own.
bool animationRateMoved(const ActorAiTrace::AnimationRateMeter &meter, bool measured)
{
    return measured && meter.logged >= 0.0f && std::abs(meter.rate - meter.logged) > 0.1f
        && std::abs(meter.rate - meter.logged) > 0.25f * std::max(meter.rate, meter.logged);
}
}

void ActorAiTrace::observeAnimation(size_t actorIndex, const ActorAnimationTraceSample &sample)
{
    const auto iterator = m_actors.find(actorIndex);

    if (!recordsAnimation() || iterator == m_actors.end() || sample.deltaSeconds <= 0.0f)
    {
        return;
    }

    ActorState &state = iterator->second;
    const bool sameClip = state.animSeen && state.animClip == sample.clip && state.animReversed == sample.reversed;
    const bool sameLayer = state.animSeen && state.animLayerClip == sample.layerClip && !sample.layerClip.empty();
    const bool measured = measureAnimationRate(state.animRate, sameClip, sample.timeSeconds,
        sample.durationSeconds, sample.deltaSeconds);
    const bool layerMeasured = measureAnimationRate(state.animLayerRate, sameLayer, sample.layerTimeSeconds,
        sample.layerDurationSeconds, sample.deltaSeconds);
    const bool changed = !sameClip || state.animLayerClip != sample.layerClip;
    // A clip's first measured rate is taken without a line of its own.
    const bool rateMoved = animationRateMoved(state.animRate, measured)
        || animationRateMoved(state.animLayerRate, layerMeasured);

    if (measured && state.animRate.logged < 0.0f)
    {
        state.animRate.logged = state.animRate.rate;
    }

    if (layerMeasured && state.animLayerRate.logged < 0.0f)
    {
        state.animLayerRate.logged = state.animLayerRate.rate;
    }

    state.animSeen = true;
    state.animClip = sample.clip;
    state.animReversed = sample.reversed;

    if (!changed && !rateMoved && sample.blendSeconds < 0.0f)
    {
        return;
    }

    state.animLayerClip = sample.layerClip;
    std::string detail = "main=" + std::string(sample.clip) + (sample.reversed ? " rev" : "");

    if (!sample.layerClip.empty())
    {
        detail += " layer=" + std::string(sample.layerClip);
    }

    if (state.animRate.rate >= 0.0f)
    {
        state.animRate.logged = state.animRate.rate;
        detail += " rate=" + formatFixed(state.animRate.rate, 2);
    }

    if (!sample.layerClip.empty() && state.animLayerRate.rate >= 0.0f)
    {
        state.animLayerRate.logged = state.animLayerRate.rate;
        detail += " layer_rate=" + formatFixed(state.animLayerRate.rate, 2);
    }

    detail += " speed=" + formatFixed(sample.speed, 0);

    if (sample.blendSeconds >= 0.0f)
    {
        detail += " blend=" + formatFixed(sample.blendSeconds, 2);
    }

    record(actorIndex, state.monsterId, state.actorName, false, "anim", "", std::move(detail));
}

void ActorAiTrace::record(
    const ActorAiFacts &actor, bool decision, std::string name, std::string target, std::string detail)
{
    record(actor.actorIndex, actor.identity.monsterId, actor.identity.displayName, decision, std::move(name),
        std::move(target), std::move(detail));
}

void ActorAiTrace::record(size_t actorIndex, int16_t monsterId, std::string actorName, bool decision,
    std::string name, std::string target, std::string detail)
{
    ActorAiTraceEntry entry = {};
    entry.timeSeconds = m_timeSeconds;
    entry.actorIndex = actorIndex;
    entry.monsterId = monsterId;
    entry.actorName = std::move(actorName);
    entry.decision = decision;
    entry.name = std::move(name);
    entry.target = std::move(target);
    entry.detail = std::move(detail);

    if (m_log.is_open())
    {
        m_log << formatActorAiTraceLine(entry) << '\n';
    }

    if (m_entries.size() < MaximumEntries)
    {
        m_entries.push_back(std::move(entry));
    }
}

float ActorAiTrace::timeSeconds() const
{
    return m_timeSeconds;
}

const std::vector<ActorAiTraceEntry> &ActorAiTrace::entries() const
{
    return m_entries;
}

std::vector<ActorAiTrace::OverlayItem> ActorAiTrace::overlayItems() const
{
    std::vector<OverlayItem> items;

    for (const auto &[actorIndex, state] : m_actors)
    {
        if (state.recent.empty() && !state.dead)
        {
            continue;
        }

        OverlayItem item = {};
        item.actorIndex = actorIndex;
        item.anchor = state.anchor;
        item.lines.assign(state.recent.rbegin(), state.recent.rend());

        if (state.dead)
        {
            item.lines.insert(item.lines.begin(), "dead");
        }

        items.push_back(std::move(item));
    }

    std::sort(items.begin(), items.end(),
        [](const OverlayItem &left, const OverlayItem &right)
        {
            return left.actorIndex < right.actorIndex;
        });
    return items;
}
}
