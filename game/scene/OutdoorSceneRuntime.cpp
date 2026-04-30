#include "game/scene/OutdoorSceneRuntime.h"
#include "game/FaceEnums.h"

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
    const OutdoorMoveState &moveState)
{
    return !partyRuntime.partyMovementState().flying
        && !moveState.airborne
        && !moveState.supportOnWater
        && !moveState.supportOnBurning;
}
}

OutdoorSceneRuntime::OutdoorSceneRuntime(
    const std::string &mapFileName,
    const MapStatsEntry &mapEntry,
    OutdoorPartyRuntime &partyRuntime,
    OutdoorWorldRuntime &worldRuntime,
    const std::optional<ScriptedEventProgram> &localEventProgram,
    const std::optional<ScriptedEventProgram> &globalEventProgram)
    : m_mapFileName(mapFileName)
    , m_mapEntry(mapEntry)
    , m_pPartyRuntime(&partyRuntime)
    , m_pWorldRuntime(&worldRuntime)
    , m_localEventProgram(localEventProgram)
    , m_globalEventProgram(globalEventProgram)
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
                const bool executed = m_eventRuntime.executeEventById(
                    m_localEventProgram,
                    m_globalEventProgram,
                    face.cogTriggeredNumber,
                    *pEventRuntimeState,
                    &m_pPartyRuntime->party(),
                    m_pWorldRuntime
                );

                if (executed)
                {
                    m_pWorldRuntime->applyEventRuntimeState();
                    m_pPartyRuntime->applyEventRuntimeState(*pEventRuntimeState, false);
                    result.shouldOpenEventDialog = result.shouldOpenEventDialog
                        || pEventRuntimeState->pendingDialogueContext.has_value()
                        || pEventRuntimeState->messages.size() > result.previousMessageCount;
                }
            }
        }
    }

    if (pEventRuntimeState != nullptr
        && !pEventRuntimeState->pendingDialogueContext.has_value()
        && !pEventRuntimeState->pendingMapMove.has_value()
        && m_pPartyRuntime->movementEvents().blockedBoundaryEdge.has_value()
        && canOfferMapTransition(*m_pPartyRuntime, moveState))
    {
        const std::optional<MapEdgeTransition> *pTransition =
            m_mapEntry.edgeTransition(*m_pPartyRuntime->movementEvents().blockedBoundaryEdge);

        if (pTransition != nullptr && pTransition->has_value() && !(*pTransition)->destinationMapFileName.empty())
        {
            EventRuntimeState::PendingDialogueContext context = {};
            context.kind = DialogueContextKind::MapTransition;
            context.sourceId = static_cast<uint32_t>(*m_pPartyRuntime->movementEvents().blockedBoundaryEdge);
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
    size_t &previousMessageCount)
{
    EventRuntimeState *pEventRuntimeState = m_pWorldRuntime->eventRuntimeState();

    if (pEventRuntimeState == nullptr || eventId == 0)
    {
        return false;
    }

    previousMessageCount = pEventRuntimeState->messages.size();
    pEventRuntimeState->activeDecorationContext = activeDecorationContext;

    const bool executed = m_eventRuntime.executeEventById(
        localEventProgram,
        m_globalEventProgram,
        eventId,
        *pEventRuntimeState,
        &m_pPartyRuntime->party(),
        m_pWorldRuntime
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
}
