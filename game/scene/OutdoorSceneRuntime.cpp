#include "game/scene/OutdoorSceneRuntime.h"
#include "game/FaceEnums.h"
#include "game/debug/GameplayDebugTrace.h"

#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
std::vector<OutdoorActorCollision> buildRuntimeActorColliders(const OutdoorWorldRuntime &worldRuntime)
{
    std::vector<OutdoorActorCollision> colliders;
    colliders.reserve(worldRuntime.mapActorCount());

    for (size_t actorIndex = 0; actorIndex < worldRuntime.mapActorCount(); ++actorIndex)
    {
        const OutdoorWorldRuntime::MapActorState *pActor = worldRuntime.mapActorState(actorIndex);

        if (pActor == nullptr
            || pActor->isDead
            || pActor->currentHp <= 0
            || pActor->aiState == OutdoorWorldRuntime::ActorAiState::Dying
            || pActor->aiState == OutdoorWorldRuntime::ActorAiState::Dead
            || pActor->isInvisible
            || !pActor->hostileToParty
            || pActor->radius == 0
            || pActor->height == 0)
        {
            continue;
        }

        OutdoorActorCollision collider = {};
        collider.sourceIndex = actorIndex;
        collider.source = OutdoorActorCollisionSource::MapDelta;
        collider.radius = pActor->radius;
        collider.height = pActor->height;
        collider.worldX = pActor->x;
        collider.worldY = pActor->y;
        collider.worldZ = pActor->z;
        collider.group = pActor->group;
        collider.name = pActor->displayName;
        colliders.push_back(std::move(collider));
    }

    return colliders;
}

void notifyFriendlyActorContacts(
    OutdoorWorldRuntime &worldRuntime,
    const OutdoorMoveState &partyMoveState,
    const OutdoorMovementEvents &movementEvents)
{
    for (size_t actorIndex : movementEvents.contactedActorIndices)
    {
        worldRuntime.notifyPartyContactWithMapActor(
            actorIndex,
            partyMoveState.x,
            partyMoveState.y,
            partyMoveState.footZ
        );
    }
}

bool enteredPressurePlateFace(const OutdoorMoveState &previousState, const OutdoorMoveState &currentState)
{
    if (currentState.airborne || currentState.supportKind != OutdoorSupportKind::BModelFace)
    {
        return false;
    }

    return previousState.airborne
        || previousState.supportKind != OutdoorSupportKind::BModelFace
        || previousState.supportBModelIndex != currentState.supportBModelIndex
        || previousState.supportFaceIndex != currentState.supportFaceIndex;
}

bool canOfferMapTransition(
    const OutdoorPartyRuntime &partyRuntime,
    const OutdoorMoveState &moveState,
    const MapEdgeTransition &transition)
{
    if (partyRuntime.partyMovementState().flying || moveState.airborne || moveState.supportOnBurning)
    {
        return false;
    }

    if (transition.requiredOriginSurface == MapTransitionSurfaceRequirement::Water)
    {
        return moveState.supportOnWater;
    }

    return !moveState.supportOnWater;
}

bool transitionQuestRequirementsMet(const Party &party, const MapEdgeTransition &transition)
{
    if (transition.requiredQuestBitsAny.empty())
    {
        return true;
    }

    for (uint32_t qbit : transition.requiredQuestBitsAny)
    {
        if (party.hasQuestBit(qbit))
        {
            return true;
        }
    }

    return false;
}

int32_t roundedOutdoorCoordinate(float value)
{
    return static_cast<int32_t>(std::lround(value));
}

float mmergeStraightTravelCoordinate(float coordinate)
{
    const float sign = coordinate > 0.0f ? -1.0f : 1.0f;
    return (std::abs(coordinate) - 30.0f) * sign;
}

void applyMergedStraightTravelArrival(
    EventRuntimeState::PendingMapMove &move,
    const MapEdgeTransition &transition,
    const OutdoorMoveState &moveState)
{
    if (!transition.straightTravel || !transition.straightTravelSide.has_value())
    {
        return;
    }

    move.useMapStartPosition = false;
    move.x = roundedOutdoorCoordinate(moveState.x);
    move.y = roundedOutdoorCoordinate(moveState.y);
    move.z = roundedOutdoorCoordinate(moveState.footZ);

    switch (*transition.straightTravelSide)
    {
        case MapBoundaryEdge::North:
        case MapBoundaryEdge::South:
            move.y = roundedOutdoorCoordinate(mmergeStraightTravelCoordinate(moveState.y));
            break;
        case MapBoundaryEdge::East:
        case MapBoundaryEdge::West:
            move.x = roundedOutdoorCoordinate(mmergeStraightTravelCoordinate(moveState.x));
            break;
    }
}
}

OutdoorSceneRuntime::OutdoorSceneRuntime(
    const std::string &mapFileName,
    const MapStatsEntry &mapEntry,
    OutdoorPartyRuntime &partyRuntime,
    OutdoorWorldRuntime &worldRuntime,
    const std::optional<ScriptedEventProgram> &localEventProgram,
    const std::optional<ScriptedEventProgram> &globalEventProgram,
    const HouseTable *pHouseTable,
    const NpcDialogTable *pNpcDialogTable)
    : m_mapFileName(mapFileName)
    , m_mapEntry(mapEntry)
    , m_pPartyRuntime(&partyRuntime)
    , m_pWorldRuntime(&worldRuntime)
    , m_localEventProgram(localEventProgram)
    , m_globalEventProgram(globalEventProgram)
    , m_eventRuntime(pHouseTable, pNpcDialogTable)
{
}

SceneKind OutdoorSceneRuntime::kind() const
{
    return SceneKind::Outdoor;
}

const std::string &OutdoorSceneRuntime::currentMapFileName() const
{
    return m_mapFileName;
}

Party &OutdoorSceneRuntime::party()
{
    return m_pPartyRuntime->party();
}

const Party &OutdoorSceneRuntime::party() const
{
    return m_pPartyRuntime->party();
}

EventRuntimeState *OutdoorSceneRuntime::eventRuntimeState()
{
    return m_pWorldRuntime->eventRuntimeState();
}

const EventRuntimeState *OutdoorSceneRuntime::eventRuntimeState() const
{
    return m_pWorldRuntime->eventRuntimeState();
}

ISceneEventContext *OutdoorSceneRuntime::sceneEventContext()
{
    return m_pWorldRuntime;
}

std::optional<EventRuntimeState::PendingMapMove> OutdoorSceneRuntime::consumePendingMapMove()
{
    return m_pWorldRuntime->consumePendingMapMove();
}

void OutdoorSceneRuntime::advanceGameMinutes(float minutes)
{
    m_pWorldRuntime->advanceGameMinutes(minutes);
}

OutdoorPartyRuntime &OutdoorSceneRuntime::partyRuntime()
{
    return *m_pPartyRuntime;
}

const OutdoorPartyRuntime &OutdoorSceneRuntime::partyRuntime() const
{
    return *m_pPartyRuntime;
}

OutdoorWorldRuntime &OutdoorSceneRuntime::worldRuntime()
{
    return *m_pWorldRuntime;
}

const OutdoorWorldRuntime &OutdoorSceneRuntime::worldRuntime() const
{
    return *m_pWorldRuntime;
}

const std::optional<ScriptedEventProgram> &OutdoorSceneRuntime::localEventProgram() const
{
    return m_localEventProgram;
}

const std::optional<ScriptedEventProgram> &OutdoorSceneRuntime::globalEventProgram() const
{
    return m_globalEventProgram;
}

OutdoorSceneRuntime::AdvanceFrameResult OutdoorSceneRuntime::advanceFrame(
    const OutdoorMovementInput &movementInput,
    float deltaSeconds)
{
    AdvanceFrameResult result = {};
    const OutdoorMoveState previousMoveState = m_pPartyRuntime->movementState();
    m_pPartyRuntime->setActorColliders(buildRuntimeActorColliders(*m_pWorldRuntime));
    m_pPartyRuntime->update(movementInput, deltaSeconds);

    EventRuntimeState *pEventRuntimeState = m_pWorldRuntime->eventRuntimeState();

    if (pEventRuntimeState != nullptr)
    {
        result.previousMessageCount = pEventRuntimeState->messages.size();
    }

    if (m_pWorldRuntime->updateTimers(
            deltaSeconds,
            m_eventRuntime,
            m_localEventProgram,
            m_globalEventProgram))
    {
        m_pPartyRuntime->applyEventRuntimeState(*m_pWorldRuntime->eventRuntimeState(), false);
        result.shouldOpenEventDialog = true;
    }

    const OutdoorMoveState &moveState = m_pPartyRuntime->movementState();

    if (pEventRuntimeState != nullptr && enteredPressurePlateFace(previousMoveState, moveState))
    {
        const OutdoorMapData *pMapData = m_pWorldRuntime->mapData();

        if (pMapData != nullptr
            && moveState.supportBModelIndex < pMapData->bmodels.size()
            && moveState.supportFaceIndex < pMapData->bmodels[moveState.supportBModelIndex].faces.size())
        {
            const OutdoorBModelFace &face =
                pMapData->bmodels[moveState.supportBModelIndex].faces[moveState.supportFaceIndex];

            if (hasFaceAttribute(face.attributes, FaceAttribute::PressurePlate) && face.cogTriggeredNumber != 0)
            {
                pEventRuntimeState->lastPressurePlateTrigger = EventRuntimeState::PressurePlateTrigger{
                    .world = "outdoor",
                    .eventId = face.cogTriggeredNumber,
                    .bmodelIndex = moveState.supportBModelIndex,
                    .faceIndex = moveState.supportFaceIndex,
                    .attributes = face.attributes,
                };
                GAMEPLAY_DEBUG_TRACE(
                    "pressure_plate_triggered world=outdoor event_id=" + std::to_string(face.cogTriggeredNumber)
                    + " bmodel_index=" + std::to_string(moveState.supportBModelIndex)
                    + " face_index=" + std::to_string(moveState.supportFaceIndex)
                    + " attributes=" + std::to_string(face.attributes)
                    + " pos=(" + std::to_string(moveState.x) + "," + std::to_string(moveState.y)
                    + "," + std::to_string(moveState.footZ) + ")");

                m_pWorldRuntime->setPendingEventSourcePoint(GameplayWorldPoint{
                    .x = moveState.x,
                    .y = moveState.y,
                    .z = moveState.footZ,
                });

                const bool executed = m_eventRuntime.executeEventById(
                    m_localEventProgram,
                    m_globalEventProgram,
                    face.cogTriggeredNumber,
                    *pEventRuntimeState,
                    &m_pPartyRuntime->party(),
                    m_pWorldRuntime,
                    std::nullopt,
                    false
                );

                if (executed)
                {
                    m_pWorldRuntime->applyEventRuntimeState();
                    m_pPartyRuntime->applyEventRuntimeState(*pEventRuntimeState, false);
                    result.shouldOpenEventDialog = result.shouldOpenEventDialog
                        || pEventRuntimeState->pendingDialogueContext.has_value()
                        || pEventRuntimeState->messages.size() > result.previousMessageCount;
                }
                else
                {
                    m_pWorldRuntime->setPendingEventSourcePoint(std::nullopt);
                }
            }
        }
    }

    if (pEventRuntimeState != nullptr
        && !pEventRuntimeState->pendingDialogueContext.has_value()
        && !pEventRuntimeState->pendingMapMove.has_value()
        && m_pPartyRuntime->movementEvents().blockedBoundaryEdge.has_value())
    {
        const std::optional<MapEdgeTransition> *pTransition =
            m_mapEntry.edgeTransition(*m_pPartyRuntime->movementEvents().blockedBoundaryEdge);

        if (pTransition != nullptr
            && pTransition->has_value()
            && !(*pTransition)->destinationMapFileName.empty()
            && canOfferMapTransition(*m_pPartyRuntime, moveState, **pTransition)
            && transitionQuestRequirementsMet(m_pPartyRuntime->party(), **pTransition))
        {
            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::MapTransition;
            context.sourceId = static_cast<uint32_t>(*m_pPartyRuntime->movementEvents().blockedBoundaryEdge);
            EventRuntimeState::PendingMapMove transitionMove = {};
            transitionMove.mapName = (*pTransition)->destinationMapFileName;
            transitionMove.directionDegrees = (*pTransition)->directionDegrees;
            transitionMove.useMapStartPosition = (*pTransition)->useMapStartPosition;
            transitionMove.traceSourceKind = "map_boundary";
            transitionMove.traceSourceId = context.sourceId;
            transitionMove.traceDestinationName = (*pTransition)->destinationMapFileName;

            if (!(*pTransition)->useMapStartPosition
                && (*pTransition)->arrivalX.has_value()
                && (*pTransition)->arrivalY.has_value()
                && (*pTransition)->arrivalZ.has_value())
            {
                transitionMove.x = *(*pTransition)->arrivalX;
                transitionMove.y = *(*pTransition)->arrivalY;
                transitionMove.z = *(*pTransition)->arrivalZ;
            }
            else
            {
                applyMergedStraightTravelArrival(transitionMove, **pTransition, moveState);
            }

            GAMEPLAY_DEBUG_TRACE(
                std::string("map_transition_requested source_kind=\"map_boundary\"")
                + " source_id=" + std::to_string(context.sourceId)
                + " action_id=0 event_id=0 confirmation_required=true"
                + " destination_map=\"" + transitionMove.mapName.value_or(std::string()) + "\""
                + " destination_name=\"" + transitionMove.traceDestinationName + "\""
                + " use_start_position=" + (transitionMove.useMapStartPosition ? "true" : "false")
                + " pos=(" + std::to_string(transitionMove.x)
                + "," + std::to_string(transitionMove.y)
                + "," + std::to_string(transitionMove.z) + ")"
                + " direction_degrees="
                + (transitionMove.directionDegrees.has_value()
                    ? std::to_string(*transitionMove.directionDegrees)
                    : std::string("none")));
            pEventRuntimeState->lastMapTransitionRequested = EventRuntimeState::MapTransitionTrace{
                .sourceKind = "map_boundary",
                .sourceId = context.sourceId,
                .confirmationRequired = true,
                .destinationMap = transitionMove.mapName.value_or(std::string()),
                .destinationName = transitionMove.traceDestinationName,
                .useStartPosition = transitionMove.useMapStartPosition,
                .x = transitionMove.x,
                .y = transitionMove.y,
                .z = transitionMove.z,
                .directionDegrees = transitionMove.directionDegrees,
            };
            context.transitionMapMove = transitionMove;
            pEventRuntimeState->pendingDialogueContext = std::move(context);
            result.shouldOpenEventDialog = true;
        }
    }

    m_pWorldRuntime->queueActorAiUpdate(deltaSeconds, moveState.x, moveState.y, moveState.footZ);
    notifyFriendlyActorContacts(*m_pWorldRuntime, moveState, m_pPartyRuntime->movementEvents());
    return result;
}

bool OutdoorSceneRuntime::executeEventById(
    const std::optional<ScriptedEventProgram> &localEventProgram,
    uint16_t eventId,
    const std::optional<EventRuntimeState::ActiveDecorationContext> &activeDecorationContext,
    size_t &previousMessageCount,
    bool allowGlobalFallback)
{
    EventRuntimeState *pEventRuntimeState = m_pWorldRuntime->eventRuntimeState();

    if (pEventRuntimeState == nullptr || eventId == 0)
    {
        return false;
    }

    previousMessageCount = pEventRuntimeState->messages.size();
    pEventRuntimeState->activeDecorationContext = activeDecorationContext;
    const std::optional<ScriptedEventProgram> emptyLocalProgram;
    const std::optional<ScriptedEventProgram> &effectiveLocalEventProgram =
        activeDecorationContext.has_value() && allowGlobalFallback ? emptyLocalProgram : localEventProgram;

    const bool executed = m_eventRuntime.executeEventById(
        effectiveLocalEventProgram,
        m_globalEventProgram,
        eventId,
        *pEventRuntimeState,
        &m_pPartyRuntime->party(),
        m_pWorldRuntime,
        std::nullopt,
        allowGlobalFallback
    );
    pEventRuntimeState->activeDecorationContext.reset();

    if (!executed)
    {
        return false;
    }

    m_pWorldRuntime->applyEventRuntimeState();
    m_pPartyRuntime->applyEventRuntimeState(*pEventRuntimeState, false);
    return true;
}

bool OutdoorSceneRuntime::executeNpcTopicEventById(
    uint16_t eventId,
    size_t &previousMessageCount,
    std::optional<uint8_t> continueStep)
{
    EventRuntimeState *pEventRuntimeState = m_pWorldRuntime->eventRuntimeState();

    if (pEventRuntimeState == nullptr || eventId == 0)
    {
        return false;
    }

    previousMessageCount = pEventRuntimeState->messages.size();

    const bool executed = m_eventRuntime.executeNpcTopicEventById(
        m_localEventProgram,
        m_globalEventProgram,
        eventId,
        *pEventRuntimeState,
        &m_pPartyRuntime->party(),
        m_pWorldRuntime,
        continueStep
    );

    if (!executed)
    {
        return false;
    }

    m_pWorldRuntime->applyEventRuntimeState();
    m_pPartyRuntime->applyEventRuntimeState(*pEventRuntimeState, false);
    return true;
}

bool OutdoorSceneRuntime::executeMapEventById(
    uint16_t eventId,
    size_t &previousMessageCount,
    std::optional<uint8_t> continueStep)
{
    EventRuntimeState *pEventRuntimeState = m_pWorldRuntime->eventRuntimeState();

    if (pEventRuntimeState == nullptr || eventId == 0)
    {
        return false;
    }

    previousMessageCount = pEventRuntimeState->messages.size();

    const bool executed = m_eventRuntime.executeEventById(
        m_localEventProgram,
        m_globalEventProgram,
        eventId,
        *pEventRuntimeState,
        &m_pPartyRuntime->party(),
        m_pWorldRuntime,
        continueStep
    );

    if (!executed)
    {
        return false;
    }

    m_pWorldRuntime->applyEventRuntimeState();
    m_pPartyRuntime->applyEventRuntimeState(*pEventRuntimeState, false);
    return true;
}

bool OutdoorSceneRuntime::executeEventHooks(EventRuntimeHookKind kind)
{
    EventRuntimeState *pEventRuntimeState = m_pWorldRuntime->eventRuntimeState();

    if (pEventRuntimeState == nullptr)
    {
        return false;
    }

    const bool executed = m_eventRuntime.executeHooks(
        m_localEventProgram,
        m_globalEventProgram,
        kind,
        *pEventRuntimeState,
        &m_pPartyRuntime->party(),
        m_pWorldRuntime);

    if (!executed)
    {
        return false;
    }

    m_pWorldRuntime->applyEventRuntimeState();
    m_pPartyRuntime->applyEventRuntimeState(*pEventRuntimeState, false);
    return true;
}
}
