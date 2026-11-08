#include "game/mm9/Mm9PositionedTransitionRuntime.h"

#include <algorithm>
#include <cmath>
#include <string>

namespace OpenYAMM::Game
{
namespace
{
// The party's body (feet at z, radius, height) against the volume; a zero body is the point at its feet.
bool bodyTouches(const Mm9MapTransition &transition, float x, float y, float z, float radius, float height)
{
    const float centerZ = static_cast<float>(transition.centerZ);
    const float halfZ = static_cast<float>(transition.halfExtentZ);
    return std::abs(x - static_cast<float>(transition.centerX)) <= static_cast<float>(transition.halfExtentX) + radius
        && std::abs(y - static_cast<float>(transition.centerY)) <= static_cast<float>(transition.halfExtentY) + radius
        && z <= centerZ + halfZ
        && z + height >= centerZ - halfZ;
}

// A map script turns an exit off (MM9's disabled-at-start exit triggers, enabled later by a trigger) with the named
// map var "Mm9ExitDisabled<source object index>" (saved with the map); 0 or unset: on.
bool mm9ExitDisabled(const Mm9MapTransition &transition, const EventRuntimeState &eventRuntimeState)
{
    const auto found = eventRuntimeState.namedMapVars.find(
        "Mm9ExitDisabled" + std::to_string(transition.sourceObjectIndex));
    return found != eventRuntimeState.namedMapVars.end() && found->second != 0;
}

EventRuntimeState::PendingMapMove buildPendingMove(const Mm9MapTransition &transition)
{
    EventRuntimeState::PendingMapMove move = {};
    move.x = transition.arrivalX;
    move.y = transition.arrivalY;
    move.z = transition.arrivalZ;
    move.mapName = transition.destinationMapFileName;
    move.directionDegrees = static_cast<int32_t>(std::lround(transition.facingDegrees)) % 360;
    move.useMapStartPosition = false;
    move.useFullscreenLoading = !transition.loadScreen.empty();
    move.traceSourceKind = "mm9_exit_trigger";
    move.traceSourceId = transition.sourceObjectIndex;
    move.traceDestinationName = transition.destinationMapFileName;
    return move;
}

EventRuntimeState::MapTransitionTrace buildTrace(
    const Mm9MapTransition &transition,
    const EventRuntimeState::PendingMapMove &move)
{
    EventRuntimeState::MapTransitionTrace trace = {};
    trace.sourceKind = "mm9_exit_trigger";
    trace.sourceId = transition.sourceObjectIndex;
    trace.confirmationRequired = transition.askPlayer;
    trace.destinationMap = transition.destinationMapFileName;
    trace.destinationName = transition.destinationMapFileName;
    trace.travelDays = static_cast<uint32_t>(std::max(0, transition.travelDays));
    trace.x = move.x;
    trace.y = move.y;
    trace.z = move.z;
    trace.directionDegrees = move.directionDegrees;
    return trace;
}
}

void Mm9PositionedTransitionRuntime::configure(const std::vector<const Mm9MapTransition *> &transitions)
{
    clear();
    m_gates.reserve(transitions.size());
    for (const Mm9MapTransition *pTransition : transitions)
    {
        if (pTransition != nullptr)
        {
            m_gates.push_back({.pTransition = pTransition});
        }
    }
}

void Mm9PositionedTransitionRuntime::clear()
{
    m_gates.clear();
    m_initialized = false;
}

void Mm9PositionedTransitionRuntime::resetOverlapState()
{
    for (Gate &gate : m_gates)
    {
        gate.inside = false;
    }
    m_initialized = false;
}

bool Mm9PositionedTransitionRuntime::empty() const
{
    return m_gates.empty();
}

std::optional<Mm9PositionedTransitionActivation> Mm9PositionedTransitionRuntime::update(
    float partyX,
    float partyY,
    float partyZ,
    EventRuntimeState &eventRuntimeState,
    float bodyRadius,
    float bodyHeight)
{
    const bool canActivate = m_initialized
        && !eventRuntimeState.pendingDialogueContext.has_value()
        && !eventRuntimeState.pendingMapMove.has_value();
    const Mm9MapTransition *pActivatedTransition = nullptr;
    for (Gate &gate : m_gates)
    {
        const bool inside = !mm9ExitDisabled(*gate.pTransition, eventRuntimeState)
            && bodyTouches(*gate.pTransition, partyX, partyY, partyZ, bodyRadius, bodyHeight);
        if (canActivate && !gate.inside && inside && pActivatedTransition == nullptr)
        {
            pActivatedTransition = gate.pTransition;
        }
        gate.inside = inside;
    }
    m_initialized = true;
    if (pActivatedTransition == nullptr)
    {
        return std::nullopt;
    }

    Mm9PositionedTransitionActivation activation = {};
    activation.pTransition = pActivatedTransition;
    activation.move = buildPendingMove(*pActivatedTransition);
    eventRuntimeState.lastMapTransitionRequested = buildTrace(*pActivatedTransition, activation.move);
    if (pActivatedTransition->askPlayer)
    {
        EventRuntimeState::PendingDialogueContext context = {};
        context.kind = DialogueContextKind::MapTransition;
        context.sourceId = pActivatedTransition->sourceObjectIndex;
        context.transitionMapMove = activation.move;
        context.transitionTravelDays = std::max(0, pActivatedTransition->travelDays);
        eventRuntimeState.pendingDialogueContext = std::move(context);
    }
    else
    {
        eventRuntimeState.pendingMapMove = activation.move;
    }
    return activation;
}
}
