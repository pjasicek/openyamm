#include "game/scene/OutdoorSceneRuntime.h"
#include "game/gameplay/InteractiveDecorationRules.h"
#include "game/FaceEnums.h"
#include "game/debug/GameplayDebugTrace.h"
#include "game/gameplay/TravelRuntime.h"

#include <SDL3/SDL.h>

#include <cmath>
#include <numbers>

namespace OpenYAMM::Game
{
namespace
{
constexpr float GameMinutesPerRealSecond = 0.5f;

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
            || !worldRuntime.mapActorBlocksPartyMovement(*pActor)
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
        collider.worldX = pActor->preciseX;
        collider.worldY = pActor->preciseY;
        collider.worldZ = pActor->preciseZ;
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
}

EventRuntimeState::PendingMapMove buildBoundaryTravelMapMove(
    const MapEdgeTransition &transition,
    MapBoundaryEdge edge,
    float x,
    float y,
    float footZ,
    float yawRadians)
{
    EventRuntimeState::PendingMapMove move = {};
    move.mapName = transition.destinationMapFileName;
    move.directionDegrees = transition.directionDegrees;
    move.useMapStartPosition = transition.useMapStartPosition;
    move.traceSourceKind = "map_boundary";
    move.traceSourceId = static_cast<uint32_t>(edge);
    move.traceDestinationName = transition.destinationMapFileName;

    if (!transition.useMapStartPosition
        && transition.arrivalX.has_value()
        && transition.arrivalY.has_value()
        && transition.arrivalZ.has_value())
    {
        move.x = *transition.arrivalX;
        move.y = *transition.arrivalY;
        move.z = *transition.arrivalZ;
        return move;
    }

    if (!transition.straightTravel || !transition.arrivalSide.has_value())
    {
        move.startPointName = mapStartPointName(transition.arrivalSide);
        return move;
    }

    // MMerge mirrors the crossing coordinate 30 units inside the opposite edge and keeps the party's heading.
    move.useMapStartPosition = false;
    move.x = roundedOutdoorCoordinate(x);
    move.y = roundedOutdoorCoordinate(y);
    move.z = roundedOutdoorCoordinate(footZ);

    switch (*transition.arrivalSide)
    {
        case MapBoundaryEdge::North:
        case MapBoundaryEdge::South:
            move.y = roundedOutdoorCoordinate(mmergeStraightTravelCoordinate(y));
            break;
        case MapBoundaryEdge::East:
        case MapBoundaryEdge::West:
            move.x = roundedOutdoorCoordinate(mmergeStraightTravelCoordinate(x));
            break;
    }

    if (!move.directionDegrees.has_value())
    {
        const int32_t degrees = static_cast<int32_t>(std::lround(yawRadians * 180.0f / std::numbers::pi_v<float>));
        move.directionDegrees = ((degrees % 360) + 360) % 360;
    }

    return move;
}

OutdoorSceneRuntime::OutdoorSceneRuntime(
    const std::string &mapFileName,
    const MapStatsEntry &mapEntry,
    OutdoorPartyRuntime &partyRuntime,
    OutdoorWorldRuntime &worldRuntime,
    const std::optional<ScriptedEventProgram> &localEventProgram,
    const std::optional<ScriptedEventProgram> &globalEventProgram,
    const HouseTable *pHouseTable,
    const NpcDialogTable *pNpcDialogTable,
    const Mm9MapTransitionTable *pMm9MapTransitionTable,
    const Mm9TeacherScheduleTable *pMm9TeacherScheduleTable)
    : m_mapFileName(mapFileName)
    , m_mapEntry(mapEntry)
    , m_pPartyRuntime(&partyRuntime)
    , m_pWorldRuntime(&worldRuntime)
    , m_localEventProgram(localEventProgram)
    , m_globalEventProgram(globalEventProgram)
    , m_eventRuntime(pHouseTable, pNpcDialogTable)
{
    m_pWorldRuntime->setMonsterKilledHooksEnabled(
        (m_localEventProgram && !m_localEventProgram->monsterKilledHookEventIds().empty())
        || (m_globalEventProgram && !m_globalEventProgram->monsterKilledHookEventIds().empty()));

    if (pMm9MapTransitionTable != nullptr)
    {
        m_mm9PositionedTransitionRuntime.configure(
            pMm9MapTransitionTable->forSourceMapFile(mapFileName));
    }
    if (pMm9TeacherScheduleTable != nullptr)
    {
        m_mm9TeacherScheduleRuntime.configure(
            pMm9TeacherScheduleTable->forSourceMapFile(mapFileName));
    }
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

void OutdoorSceneRuntime::advanceTurnBasedGameMinutes(float minutes)
{
    processMonsterKilledEvents();

    if (minutes <= 0.0f)
    {
        return;
    }

    const float equivalentRealSeconds = minutes / GameMinutesPerRealSecond;
    const bool timerExecuted = m_pWorldRuntime->updateTimers(
        equivalentRealSeconds,
        m_eventRuntime,
        m_localEventProgram,
        m_globalEventProgram,
        nullptr);

    applyMm9TeacherScheduleActivations(
        m_mm9TeacherScheduleRuntime.update(m_pWorldRuntime->gameMinutes()),
        *m_pWorldRuntime,
        *m_pWorldRuntime);

    if (timerExecuted && m_pWorldRuntime->eventRuntimeState() != nullptr)
    {
        m_pPartyRuntime->applyEventRuntimeState(*m_pWorldRuntime->eventRuntimeState(), false);
    }
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
    float deltaSeconds,
    GameplayWorldMovementFrameDiagnostics *pPerformanceDiagnostics)
{
    const uint64_t totalBeginTickCount = pPerformanceDiagnostics != nullptr ? SDL_GetTicksNS() : 0;
    AdvanceFrameResult result = {};
    const OutdoorMoveState previousMoveState = m_pPartyRuntime->movementState();

    uint64_t stageBeginTickCount = pPerformanceDiagnostics != nullptr ? SDL_GetTicksNS() : 0;
    m_pPartyRuntime->setActorColliders(buildRuntimeActorColliders(*m_pWorldRuntime));
    m_pPartyRuntime->setHiddenDecorationEntities(m_pWorldRuntime->refreshHiddenDecorationEntities());
    if (pPerformanceDiagnostics != nullptr)
    {
        pPerformanceDiagnostics->actorColliderBuildNanoseconds += SDL_GetTicksNS() - stageBeginTickCount;
        stageBeginTickCount = SDL_GetTicksNS();
    }

    m_pPartyRuntime->update(movementInput, deltaSeconds, pPerformanceDiagnostics);
    if (pPerformanceDiagnostics != nullptr)
    {
        pPerformanceDiagnostics->partyUpdateNanoseconds += SDL_GetTicksNS() - stageBeginTickCount;
        stageBeginTickCount = SDL_GetTicksNS();
    }

    EventRuntimeState *pEventRuntimeState = m_pWorldRuntime->eventRuntimeState();

    applyMm9TeacherScheduleActivations(
        m_mm9TeacherScheduleRuntime.update(m_pWorldRuntime->gameMinutes()),
        *m_pWorldRuntime,
        *m_pWorldRuntime);

    if (pEventRuntimeState != nullptr)
    {
        result.previousMessageCount = pEventRuntimeState->messages.size();
    }

    result.shouldOpenEventDialog = processMonsterKilledEvents();

    if (m_pWorldRuntime->updateTimers(
            deltaSeconds,
            m_eventRuntime,
            m_localEventProgram,
            m_globalEventProgram,
            pPerformanceDiagnostics))
    {
        if (pPerformanceDiagnostics != nullptr)
        {
            pPerformanceDiagnostics->timerNanoseconds += SDL_GetTicksNS() - stageBeginTickCount;
            stageBeginTickCount = SDL_GetTicksNS();
        }

        m_pPartyRuntime->applyEventRuntimeState(*m_pWorldRuntime->eventRuntimeState(), false);
        result.shouldOpenEventDialog = true;

        if (pPerformanceDiagnostics != nullptr)
        {
            pPerformanceDiagnostics->partyEventApplyNanoseconds += SDL_GetTicksNS() - stageBeginTickCount;
        }
    }
    else if (pPerformanceDiagnostics != nullptr)
    {
        pPerformanceDiagnostics->timerNanoseconds += SDL_GetTicksNS() - stageBeginTickCount;
    }

    const OutdoorMoveState &moveState = m_pPartyRuntime->movementState();

    stageBeginTickCount = pPerformanceDiagnostics != nullptr ? SDL_GetTicksNS() : 0;
    if (pEventRuntimeState != nullptr && enteredPressurePlateFace(previousMoveState, moveState))
    {
        const OutdoorMapData *pMapData = m_pWorldRuntime->mapData();

        if (pMapData != nullptr
            && moveState.supportBModelIndex < pMapData->bmodels.size()
            && moveState.supportFaceIndex < pMapData->bmodels[moveState.supportBModelIndex].faces.size())
        {
            const OutdoorBModelFace &face =
                pMapData->bmodels[moveState.supportBModelIndex].faces[moveState.supportFaceIndex];

            const bool bypassedByLevitate = m_pPartyRuntime->party().hasPartyBuff(PartyBuffId::Levitate)
                && m_localEventProgram
                && m_localEventProgram->isLevitateSensitivePressurePlate(face.cogTriggeredNumber, face.attributes);

            if (hasFaceAttribute(face.attributes, FaceAttribute::PressurePlate)
                && face.cogTriggeredNumber != 0 && !bypassedByLevitate)
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

    if (pPerformanceDiagnostics != nullptr)
    {
        pPerformanceDiagnostics->pressurePlateNanoseconds += SDL_GetTicksNS() - stageBeginTickCount;
    }

    if (pEventRuntimeState != nullptr)
    {
        const std::optional<Mm9PositionedTransitionActivation> activation =
            m_mm9PositionedTransitionRuntime.update(
                moveState.x,
                moveState.y,
                moveState.footZ,
                *pEventRuntimeState);
        if (activation)
        {
            result.shouldOpenEventDialog = result.shouldOpenEventDialog
                || activation->pTransition->askPlayer;
            // An exit that does not ask is a voyage (Ravensford's ship to the Isle of Ashes, its boat on to Sturmford):
            // the days pass, but only a walk between regions, which always asks, eats food.
            if (!activation->pTransition->askPlayer
                && applyTravelDaysSideEffects(
                    m_pPartyRuntime->party(),
                    m_pWorldRuntime,
                    activation->pTransition->travelDays,
                    0)
                && pEventRuntimeState->pendingMapMove)
            {
                pEventRuntimeState->pendingMapMove->travelTimeApplied = true;
            }
        }
    }

    stageBeginTickCount = pPerformanceDiagnostics != nullptr ? SDL_GetTicksNS() : 0;
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
            const MapBoundaryEdge edge = *m_pPartyRuntime->movementEvents().blockedBoundaryEdge;
            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::MapTransition;
            context.sourceId = static_cast<uint32_t>(edge);
            context.boundaryTravel = true;
            const EventRuntimeState::PendingMapMove transitionMove = buildBoundaryTravelMapMove(
                **pTransition,
                edge,
                moveState.x,
                moveState.y,
                moveState.footZ,
                m_pWorldRuntime->gameplayCameraYawRadians());

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

    if (pPerformanceDiagnostics != nullptr)
    {
        pPerformanceDiagnostics->boundaryTransitionNanoseconds += SDL_GetTicksNS() - stageBeginTickCount;
        stageBeginTickCount = SDL_GetTicksNS();
    }

    m_pWorldRuntime->queueActorAiUpdate(deltaSeconds, moveState.x, moveState.y, moveState.footZ);
    notifyFriendlyActorContacts(*m_pWorldRuntime, moveState, m_pPartyRuntime->movementEvents());

    if (pPerformanceDiagnostics != nullptr)
    {
        pPerformanceDiagnostics->actorQueueAndContactsNanoseconds += SDL_GetTicksNS() - stageBeginTickCount;
        pPerformanceDiagnostics->sceneAdvanceNanoseconds += SDL_GetTicksNS() - totalBeginTickCount;
    }

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

    if (m_pWorldRuntime->useMm9BarrelEvent(eventId))
    {
        pEventRuntimeState->lastActivationResult = "MM9 barrel event " + std::to_string(eventId) + " executed";
        return true;
    }

    pEventRuntimeState->activeDecorationContext = activeDecorationContext;
    const std::optional<ScriptedEventProgram> emptyLocalProgram;
    const std::optional<ScriptedEventProgram> &effectiveLocalEventProgram =
        activeDecorationContext.has_value() && allowGlobalFallback ? emptyLocalProgram : localEventProgram;
    const std::vector<int64_t> statsBefore =
        activeDecorationContext ? partyBaseStatSnapshot(m_pPartyRuntime->party()) : std::vector<int64_t>{};

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

    if (executed && activeDecorationContext)
    {
        reportDecorationStatGain(
            m_pPartyRuntime->party(), *pEventRuntimeState, activeDecorationContext->decorVarIndex, statsBefore);
    }

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

bool OutdoorSceneRuntime::processMonsterKilledEvents()
{
    // Dispatch after combat iteration: a Lua hook may summon actors and reallocate the actor array.
    const std::vector<OutdoorWorldRuntime::MonsterKilledEvent> events = m_pWorldRuntime->drainMonsterKilledEvents();
    EventRuntimeState *pState = eventRuntimeState();

    if (events.empty() || pState == nullptr)
    {
        return false;
    }

    const std::optional<EventRuntimeState::ActiveHookContext> previousContext = pState->activeHookContext;
    bool executed = false;

    for (const OutdoorWorldRuntime::MonsterKilledEvent &event : events)
    {
        EventRuntimeState::ActiveHookContext context = {};
        context.kind = EventRuntimeHookKind::MonsterKilled;
        context.actorIndex = event.actorIndex;
        context.monsterId = event.monsterId;
        context.byParty = event.byParty;
        pState->activeHookContext = std::move(context);
        executed = executeEventHooks(EventRuntimeHookKind::MonsterKilled) || executed;
    }

    pState->activeHookContext = previousContext;
    return executed;
}
}
