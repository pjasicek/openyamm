#include "game/scene/OutdoorSceneRuntime.h"

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
}

OutdoorSceneRuntime::OutdoorSceneRuntime(
    const std::string &mapFileName,
    OutdoorPartyRuntime &partyRuntime,
    OutdoorWorldRuntime &worldRuntime,
    const std::optional<EventIrProgram> &localEventIrProgram,
    const std::optional<EventIrProgram> &globalEventIrProgram)
    : m_mapFileName(mapFileName)
    , m_pPartyRuntime(&partyRuntime)
    , m_pWorldRuntime(&worldRuntime)
    , m_localEventIrProgram(localEventIrProgram)
    , m_globalEventIrProgram(globalEventIrProgram)
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

const std::optional<EventIrProgram> &OutdoorSceneRuntime::localEventIrProgram() const
{
    return m_localEventIrProgram;
}

const std::optional<EventIrProgram> &OutdoorSceneRuntime::globalEventIrProgram() const
{
    return m_globalEventIrProgram;
}

OutdoorSceneRuntime::AdvanceFrameResult OutdoorSceneRuntime::advanceFrame(
    const OutdoorMovementInput &movementInput,
    float deltaSeconds)
{
    AdvanceFrameResult result = {};
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
            m_localEventIrProgram,
            m_globalEventIrProgram))
    {
        m_pPartyRuntime->applyEventRuntimeState(*m_pWorldRuntime->eventRuntimeState());
        result.shouldOpenEventDialog = true;
    }

    const OutdoorMoveState &moveState = m_pPartyRuntime->movementState();
    m_pWorldRuntime->updateMapActors(deltaSeconds, moveState.x, moveState.y, moveState.footZ);
    notifyFriendlyActorContacts(*m_pWorldRuntime, moveState, m_pPartyRuntime->movementEvents());
    return result;
}

bool OutdoorSceneRuntime::executeEventById(
    const std::optional<EventIrProgram> &localEventIrProgram,
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
        localEventIrProgram,
        m_globalEventIrProgram,
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
    m_pPartyRuntime->applyEventRuntimeState(*pEventRuntimeState);
    return true;
}
}
