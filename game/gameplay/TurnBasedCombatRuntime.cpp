#include "game/gameplay/TurnBasedCombatRuntime.h"

#include "game/debug/GameplayDebugTrace.h"
#include "game/gameplay/GameplayInputFrame.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/gameplay/GameMechanics.h"
#include "game/party/Party.h"
#include "game/party/PlaythroughStatistics.h"
#include "game/rules/GameRules.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <cmath>
#include <sstream>

namespace OpenYAMM::Game
{
namespace
{
constexpr float OeRealtimeRecoveryScale = 2.133333333333333f;
constexpr float TurnTicksPerSecond = 128.0f;
// 130 movement points per turn, spent at one point per tick of walking: about one second of movement.
constexpr float TurnMovementActionPoints = 130.0f;
constexpr float LegacyGameTicksPerMinute = 256.0f;
constexpr float CompletedTurnGameTimeTicks = 213.0f;
constexpr float CompletedTurnGameTimeMinutes = CompletedTurnGameTimeTicks / LegacyGameTicksPerMinute;
constexpr float InitialWaitTicks = 64.0f;
constexpr float ActorActionResolutionMaxTicks = 128.0f;
constexpr float ActorNearbyDistance = 5120.0f;
constexpr int InactiveInitiative = 1001;
constexpr int MinimumPlayerRecoveryTicks = 30;
// Granted actors finish their attack (animation and impact) within this many ticks; longer means stuck.
constexpr float ActorTurnActionMaxTicks = 384.0f;
constexpr int ArrivedActorInitiative = 1;
constexpr int ArrivedCharacterInitiative = 100;

int recoverySecondsToTicks(float recoverySeconds)
{
    return static_cast<int>(std::lround(
        std::max(0.0f, recoverySeconds) / OeRealtimeRecoveryScale * TurnTicksPerSecond));
}

bool memberCanStayInTurnQueue(const Character &member)
{
    return GameMechanics::canSelectInGameplay(member);
}

bool actorCanEnterTurnQueue(const GameplayRuntimeActorState &actor)
{
    return !actor.isDead && actor.hostileToParty;
}

bool actorIsNearParty(
    const GameplayRuntimeActorState &actor,
    float partyX,
    float partyY,
    float partyZ);

bool actorCanJoinTurnQueue(const IGameplayWorldRuntime &worldRuntime, size_t actorIndex, bool &distant)
{
    GameplayRuntimeActorState actor = {};
    distant = false;

    if (!worldRuntime.actorRuntimeState(actorIndex, actor) || !actorCanEnterTurnQueue(actor))
    {
        return false;
    }

    if (!actorIsNearParty(actor, worldRuntime.partyX(), worldRuntime.partyY(), worldRuntime.partyFootZ()))
    {
        distant = true;
        return false;
    }

    return true;
}

bool actorIsNearParty(
    const GameplayRuntimeActorState &actor,
    float partyX,
    float partyY,
    float partyZ)
{
    const float deltaX = actor.preciseX - partyX;
    const float deltaY = actor.preciseY - partyY;
    const float deltaZ = actor.preciseZ - partyZ;
    const float distance = std::sqrt(deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ);
    return std::max(0.0f, distance - static_cast<float>(actor.radius)) <= ActorNearbyDistance;
}

const char *turnStageName(TurnBasedCombatStage stage)
{
    switch (stage)
    {
        case TurnBasedCombatStage::None:
            return "none";
        case TurnBasedCombatStage::Wait:
            return "wait";
        case TurnBasedCombatStage::Attack:
            return "attack";
        case TurnBasedCombatStage::Movement:
            return "movement";
        default:
            return "unknown";
    }
}

const char *queueEntryKindName(TurnBasedCombatRuntime::QueueEntry::Kind kind)
{
    return kind == TurnBasedCombatRuntime::QueueEntry::Kind::Character ? "character" : "actor";
}

std::string queueSummary(const std::vector<TurnBasedCombatRuntime::QueueEntry> &queue, size_t limit = 8)
{
    std::ostringstream out;
    out << "queue_size=" << queue.size();

    for (size_t index = 0; index < queue.size() && index < limit; ++index)
    {
        const TurnBasedCombatRuntime::QueueEntry &entry = queue[index];
        out << " q" << index << "=" << queueEntryKindName(entry.kind) << ":" << entry.id
            << ":" << entry.initiative;
    }

    if (queue.size() > limit)
    {
        out << " queue_truncated=true";
    }

    return out.str();
}

void setActionState(GameplayInputFrame &input, KeyboardAction action, bool value)
{
    GameplayButtonInputState &state = input.actions[keyboardActionIndex(action)];
    state.held = value;
    state.pressed = false;
    state.released = false;
}
} // namespace

bool TurnBasedCombatRuntime::active() const
{
    return m_active;
}

TurnBasedCombatStage TurnBasedCombatRuntime::stage() const
{
    return m_stage;
}

int TurnBasedCombatRuntime::movementActionPoints() const
{
    return static_cast<int>(std::ceil(m_movementActionPoints));
}

int TurnBasedCombatRuntime::pendingActions() const
{
    return m_pendingActions;
}

bool TurnBasedCombatRuntime::hasPendingActions() const
{
    return m_pendingActions > 0;
}

TurnBasedSpeedPhase TurnBasedCombatRuntime::speedPhase() const
{
    if (!m_active)
    {
        return TurnBasedSpeedPhase::None;
    }

    // GrayFace's MM8Patch DoubleSpeedHook: monsters during the wait stage, the party while its objects fly.
    if (m_stage == TurnBasedCombatStage::Wait || (m_stage == TurnBasedCombatStage::Attack && m_resolvingActorActions))
    {
        return TurnBasedSpeedPhase::Monsters;
    }

    if (m_stage == TurnBasedCombatStage::Attack && hasPendingActions())
    {
        return TurnBasedSpeedPhase::Party;
    }

    return TurnBasedSpeedPhase::None;
}

bool TurnBasedCombatRuntime::playerActionReady(const Party &party) const
{
    return m_active && m_stage == TurnBasedCombatStage::Attack && !hasPendingActions() && canBeginPlayerAction(party);
}

bool TurnBasedCombatRuntime::shouldUpdateActorAi(const Party *pParty) const
{
    (void)pParty;

    if (!m_active)
    {
        return true;
    }

    if (m_stage == TurnBasedCombatStage::Wait)
    {
        return true;
    }

    // In the attack stage actor AI runs only while granted actors take their queued action.
    return m_stage == TurnBasedCombatStage::Attack && m_resolvingActorActions;
}

ActorTurnBasedMode TurnBasedCombatRuntime::actorMode() const
{
    if (!m_active)
    {
        return ActorTurnBasedMode::RealTime;
    }

    // OE moves actors only during the wait stage and lets them attack only on their attack-stage turn.
    return m_stage == TurnBasedCombatStage::Wait ? ActorTurnBasedMode::MoveOnly : ActorTurnBasedMode::Hold;
}

bool TurnBasedCombatRuntime::frontQueueCharacter(size_t &memberIndex) const
{
    const std::optional<size_t> queueIndex = readyCharacterQueueIndex(nullptr);
    if (!queueIndex)
    {
        return false;
    }

    memberIndex = m_queue[*queueIndex].id;
    return true;
}

const std::vector<TurnBasedCombatRuntime::QueueEntry> &TurnBasedCombatRuntime::queue() const
{
    return m_queue;
}

bool TurnBasedCombatRuntime::begin(
    Party &party,
    const IGameplayWorldRuntime *pWorldRuntime,
    const std::vector<float> &attackRecoverySeconds)
{
    if (m_active || party.members().empty())
    {
        return false;
    }

    m_active = true;
    m_turnInitiative = 100;
    m_turnCount = 0;
    m_pendingActions = 0;
    m_movementActionPoints = 0.0f;
    m_actorActionTimerTicks = 0.0f;
    m_movementFinished = false;
    m_waitingForActorActionResolution = false;
    m_resolvingActorActions = false;
    m_pendingGameTimeAdvanceMinutes = 0.0f;
    clearMovementLatches();
    m_loggedReadyMemberIndex.reset();

    for (float &recoverySeconds : m_memberTurnRecoverySeconds)
    {
        recoverySeconds = 0.0f;
    }

    m_attackRecoverySeconds = attackRecoverySeconds;
    rebuildInitialQueue(party, pWorldRuntime, m_attackRecoverySeconds);
    enterWaitStage();
    sortQueue(&party);

    if (PlaythroughStatistics *pStatistics = party.statistics())
    {
        pStatistics->recordTurnBasedFight();
    }
    GAMEPLAY_DEBUG_TRACE(
        "turn_based_begin stage=" + std::string(turnStageName(m_stage))
        + " members=" + std::to_string(party.members().size())
        + " " + queueSummary(m_queue)
        + " ai_timer_ticks=" + std::to_string(m_aiTurnTimerTicks));
    return true;
}

void TurnBasedCombatRuntime::end(Party *pParty, IGameplayWorldRuntime *pWorldRuntime, bool preserveRecovery)
{
    GAMEPLAY_DEBUG_TRACE(
        "turn_based_end stage=" + std::string(turnStageName(m_stage))
        + " preserve_recovery=" + (preserveRecovery ? "true" : "false")
        + " pending=" + std::to_string(m_pendingActions)
        + " movement_ap=" + std::to_string(m_movementActionPoints)
        + " actor_action_ticks=" + std::to_string(m_actorActionTimerTicks)
        + " " + queueSummary(m_queue));

    if (preserveRecovery)
    {
        for (const QueueEntry &entry : m_queue)
        {
            const int remainingTicks = std::max(0, entry.initiative);
            if (remainingTicks >= InactiveInitiative)
            {
                continue;
            }

            if (entry.kind == QueueEntry::Kind::Character)
            {
                if (pParty != nullptr && entry.id < pParty->combatantCount() && remainingTicks > 0)
                {
                    pParty->applyRecoveryToMember(entry.id, ticksToRecoverySeconds(remainingTicks));
                }
            }
            else if (pWorldRuntime != nullptr)
            {
                // OE carries each monster's remaining initiative into its realtime recovery.
                pWorldRuntime->setActorAttackCooldownSeconds(entry.id, ticksToRecoverySeconds(remainingTicks));
            }
        }
    }

    if (pWorldRuntime != nullptr)
    {
        pWorldRuntime->setTurnBasedActorMode(ActorTurnBasedMode::RealTime);
    }

    reset();
}

void TurnBasedCombatRuntime::reset()
{
    m_active = false;
    m_stage = TurnBasedCombatStage::None;
    m_queue.clear();
    m_turnInitiative = 100;
    m_aiTurnTimerTicks = 0.0f;
    m_movementActionPoints = 0.0f;
    m_pendingActions = 0;
    m_turnCount = 0;
    m_actorActionTimerTicks = 0.0f;
    m_movementFinished = false;
    m_waitingForActorActionResolution = false;
    m_resolvingActorActions = false;
    m_pendingGameTimeAdvanceMinutes = 0.0f;
    clearMovementLatches();
    m_loggedReadyMemberIndex.reset();
    m_attackRecoverySeconds.clear();

    for (float &recoverySeconds : m_memberTurnRecoverySeconds)
    {
        recoverySeconds = 0.0f;
    }
}

bool TurnBasedCombatRuntime::canToggleOff(const Party &party) const
{
    if (!m_active)
    {
        return true;
    }

    if (m_stage == TurnBasedCombatStage::Movement)
    {
        return true;
    }

    return canBeginPlayerAction(party);
}

bool TurnBasedCombatRuntime::toggle(
    Party &party,
    IGameplayWorldRuntime *pWorldRuntime,
    const std::vector<float> &attackRecoverySeconds)
{
    if (!m_active)
    {
        return begin(party, pWorldRuntime, attackRecoverySeconds);
    }

    if (!canToggleOff(party))
    {
        GAMEPLAY_DEBUG_TRACE(
            "turn_based_toggle_refused stage=" + std::string(turnStageName(m_stage))
            + " player_action_ready=" + (playerActionReady(party) ? "true" : "false")
            + " pending=" + std::to_string(m_pendingActions)
            + " " + queueSummary(m_queue));
        return false;
    }

    end(&party, pWorldRuntime);
    return true;
}

void TurnBasedCombatRuntime::seedRandom(uint32_t seed)
{
    m_random.seed(seed);
}

bool TurnBasedCombatRuntime::update(Party *pParty, IGameplayWorldRuntime *pWorldRuntime, float deltaSeconds)
{
    if (!m_active)
    {
        return false;
    }

    if (pParty == nullptr)
    {
        reset();
        return false;
    }

    removeInvalidEntries(*pParty);
    removeInvalidActorEntries(pWorldRuntime);

    if (m_stage == TurnBasedCombatStage::Wait)
    {
        if (m_waitingForActorActionResolution)
        {
            m_actorActionTimerTicks += std::max(0.0f, deltaSeconds) * TurnTicksPerSecond;

            if (pWorldRuntime != nullptr && pWorldRuntime->turnBasedActorActionInProgress())
            {
                if (m_actorActionTimerTicks < ActorActionResolutionMaxTicks)
                {
                    return true;
                }

                GAMEPLAY_DEBUG_TRACE(
                    "turn_based_wait_actor_action_timeout ticks=" + std::to_string(m_actorActionTimerTicks));
            }

            if (pWorldRuntime != nullptr)
            {
                GAMEPLAY_DEBUG_TRACE("turn_based_wait_finished stop_actor_movement=true");
                pWorldRuntime->stopTurnBasedActorMovement();
            }

            enterAttackStage(pParty, pWorldRuntime);
            GAMEPLAY_DEBUG_TRACE(
                "turn_based_stage stage=attack reason=actor_actions_resolved " + queueSummary(m_queue));
            return true;
        }

        m_aiTurnTimerTicks = std::max(0.0f, m_aiTurnTimerTicks - std::max(0.0f, deltaSeconds) * TurnTicksPerSecond);

        if (m_aiTurnTimerTicks <= 0.0f)
        {
            if (pWorldRuntime != nullptr && pWorldRuntime->turnBasedActorActionInProgress())
            {
                m_aiTurnTimerTicks = 0.0f;
                m_waitingForActorActionResolution = true;
                m_actorActionTimerTicks = 0.0f;
                GAMEPLAY_DEBUG_TRACE("turn_based_wait_pending_actor_action");
                return true;
            }

            if (pWorldRuntime != nullptr)
            {
                GAMEPLAY_DEBUG_TRACE("turn_based_wait_finished stop_actor_movement=true");
                pWorldRuntime->stopTurnBasedActorMovement();
            }

            enterAttackStage(pParty, pWorldRuntime);
            GAMEPLAY_DEBUG_TRACE(
                "turn_based_stage stage=attack reason=wait_finished " + queueSummary(m_queue));
        }
    }
    else if (m_stage == TurnBasedCombatStage::Attack)
    {
        updateAttackStage(pParty, pWorldRuntime, deltaSeconds);
    }
    else if (m_stage == TurnBasedCombatStage::Movement)
    {
        // The rules may also end the walk by distance from where it began (MAW's Doom modes and Austerity).
        if (pWorldRuntime != nullptr)
        {
            if (!m_movementStart)
            {
                m_movementStart = std::pair(pWorldRuntime->partyX(), pWorldRuntime->partyY());
            }
            else if (const std::optional<float> limit = pParty->rules().combat.turnBasedWalkLimit();
                limit && std::hypot(pWorldRuntime->partyX() - m_movementStart->first,
                    pWorldRuntime->partyY() - m_movementStart->second) > *limit)
            {
                m_movementFinished = true;
            }
        }

        if (m_movementFinished || m_movementActionPoints <= 0)
        {
            GAMEPLAY_DEBUG_TRACE(
                "turn_based_stage stage=wait reason=movement_finished movement_ap="
                + std::to_string(m_movementActionPoints));
            enterWaitStage();
        }
    }

    if (m_queue.empty() && pWorldRuntime != nullptr)
    {
        rebuildInitialQueue(*pParty, pWorldRuntime, m_attackRecoverySeconds);
        sortQueue(pParty);
    }

    return true;
}

bool TurnBasedCombatRuntime::noteMovementInput(GameplayInputFrame &input, float deltaSeconds, bool classicTurnKeys)
{
    m_movementStepThisFrame = false;
    m_movementStepSeconds = 0.0f;

    if (!m_active)
    {
        return false;
    }

    if (classicTurnKeys)
    {
        // Turning keys pass through untouched; raw W/A/S/D are not movement in the classic scheme (A attacks).
        const GameplayButtonInputState turnLeft = input.action(KeyboardAction::Left);
        const GameplayButtonInputState turnRight = input.action(KeyboardAction::Right);
        const bool movementStep = noteMovementInputHeld(
            input,
            deltaSeconds,
            input.action(KeyboardAction::Forward).held,
            input.action(KeyboardAction::Backward).held,
            false,
            false);
        input.actions[keyboardActionIndex(KeyboardAction::Left)] = turnLeft;
        input.actions[keyboardActionIndex(KeyboardAction::Right)] = turnRight;
        return movementStep;
    }

    return noteMovementInputHeld(
        input,
        deltaSeconds,
        input.action(KeyboardAction::Forward).held || input.keyboardHeld[SDL_SCANCODE_W],
        input.action(KeyboardAction::Backward).held || input.keyboardHeld[SDL_SCANCODE_S],
        input.action(KeyboardAction::Left).held || input.keyboardHeld[SDL_SCANCODE_A],
        input.action(KeyboardAction::Right).held || input.keyboardHeld[SDL_SCANCODE_D]);
}

bool TurnBasedCombatRuntime::noteMovementInputHeld(
    GameplayInputFrame &input,
    float deltaSeconds,
    bool forwardHeld,
    bool backwardHeld,
    bool leftHeld,
    bool rightHeld)
{
    const bool movementHeld = forwardHeld || backwardHeld || leftHeld || rightHeld;

    if (m_stage != TurnBasedCombatStage::Movement)
    {
        const bool movementStateChanged =
            forwardHeld != m_forwardLatch
            || backwardHeld != m_backwardLatch
            || leftHeld != m_strafeLeftLatch
            || rightHeld != m_strafeRightLatch;

        if (movementHeld && movementStateChanged)
        {
            GAMEPLAY_DEBUG_TRACE(
                "turn_based_movement_input_blocked stage=" + std::string(turnStageName(m_stage))
                + " forward=" + (forwardHeld ? "true" : "false")
                + " backward=" + (backwardHeld ? "true" : "false")
                + " left=" + (leftHeld ? "true" : "false")
                + " right=" + (rightHeld ? "true" : "false")
                + " movement_ap=" + std::to_string(m_movementActionPoints));
        }

        clearMovementInput(input);
        m_forwardLatch = forwardHeld;
        m_backwardLatch = backwardHeld;
        m_strafeLeftLatch = leftHeld;
        m_strafeRightLatch = rightHeld;
        return false;
    }

    m_forwardLatch = forwardHeld;
    m_backwardLatch = backwardHeld;
    m_strafeLeftLatch = leftHeld;
    m_strafeRightLatch = rightHeld;

    const bool consumeAny = forwardHeld || backwardHeld || leftHeld || rightHeld;

    const float stepSeconds = consumeAny ? spendMovementBudget(deltaSeconds) : 0.0f;

    if (stepSeconds <= 0.0f)
    {
        if (consumeAny)
        {
            GAMEPLAY_DEBUG_TRACE(
                "turn_based_movement_input_refused movement_ap=" + std::to_string(m_movementActionPoints)
                + " finished=" + (m_movementFinished ? "true" : "false"));
        }

        clearMovementInput(input);
        return false;
    }

    setActionState(input, KeyboardAction::Forward, forwardHeld);
    setActionState(input, KeyboardAction::Backward, backwardHeld);
    setActionState(input, KeyboardAction::Left, leftHeld);
    setActionState(input, KeyboardAction::Right, rightHeld);
    input.keyboardHeld[SDL_SCANCODE_W] = forwardHeld;
    input.keyboardHeld[SDL_SCANCODE_S] = backwardHeld;
    input.keyboardHeld[SDL_SCANCODE_A] = leftHeld;
    input.keyboardHeld[SDL_SCANCODE_D] = rightHeld;
    input.keyboardHeld[SDL_SCANCODE_X] = false;
    setActionState(input, KeyboardAction::Jump, false);
    setActionState(input, KeyboardAction::FlyUp, false);
    setActionState(input, KeyboardAction::FlyDown, false);
    input.turnBasedMovementStep = true;
    m_movementStepThisFrame = true;
    m_movementStepSeconds = stepSeconds;
    GAMEPLAY_DEBUG_TRACE(
        std::string("turn_based_movement_step forward=") + (forwardHeld ? "true" : "false")
        + " backward=" + (backwardHeld ? "true" : "false")
        + " left=" + (leftHeld ? "true" : "false")
        + " right=" + (rightHeld ? "true" : "false")
        + " movement_ap=" + std::to_string(m_movementActionPoints));
    return true;
}

float TurnBasedCombatRuntime::movementDeltaSecondsForFrame(float fallbackDeltaSeconds) const
{
    if (!m_active)
    {
        return fallbackDeltaSeconds;
    }

    if (m_stage == TurnBasedCombatStage::Movement && m_movementStepThisFrame)
    {
        (void)fallbackDeltaSeconds;
        return m_movementStepSeconds;
    }

    return 0.0f;
}

float TurnBasedCombatRuntime::consumePendingGameTimeAdvanceMinutes()
{
    const float pendingMinutes = m_pendingGameTimeAdvanceMinutes;
    m_pendingGameTimeAdvanceMinutes = 0.0f;
    return pendingMinutes;
}

void TurnBasedCombatRuntime::clearMovementInput(GameplayInputFrame &input) const
{
    setActionState(input, KeyboardAction::Forward, false);
    setActionState(input, KeyboardAction::Backward, false);
    setActionState(input, KeyboardAction::Left, false);
    setActionState(input, KeyboardAction::Right, false);
    setActionState(input, KeyboardAction::Jump, false);
    setActionState(input, KeyboardAction::FlyUp, false);
    setActionState(input, KeyboardAction::FlyDown, false);
    input.keyboardHeld[SDL_SCANCODE_W] = false;
    input.keyboardHeld[SDL_SCANCODE_S] = false;
    input.keyboardHeld[SDL_SCANCODE_A] = false;
    input.keyboardHeld[SDL_SCANCODE_D] = false;
    input.keyboardHeld[SDL_SCANCODE_X] = false;
    input.turnBasedMovementStep = false;
}

bool TurnBasedCombatRuntime::finishMovementPhase()
{
    if (!m_active || m_stage != TurnBasedCombatStage::Movement)
    {
        return false;
    }

    m_movementFinished = true;
    GAMEPLAY_DEBUG_TRACE(
        "turn_based_finish_movement_requested movement_ap=" + std::to_string(m_movementActionPoints));
    return true;
}

bool TurnBasedCombatRuntime::canBeginPlayerAction(const Party &party) const
{
    if (!m_active || m_stage != TurnBasedCombatStage::Attack || hasPendingActions())
    {
        return false;
    }

    return readyCharacterQueueIndex(&party).has_value();
}

std::optional<size_t> TurnBasedCombatRuntime::readyMemberIndex(const Party &party) const
{
    if (!canBeginPlayerAction(party))
    {
        return std::nullopt;
    }

    const std::optional<size_t> queueIndex = readyCharacterQueueIndex(&party);
    return queueIndex ? std::optional<size_t>(m_queue[*queueIndex].id) : std::nullopt;
}

bool TurnBasedCombatRuntime::beginPlayerActionOrFinishMovement(Party &party)
{
    if (!m_active)
    {
        return true;
    }

    if (m_stage == TurnBasedCombatStage::Movement)
    {
        finishMovementPhase();
        return false;
    }

    const std::optional<size_t> memberIndex = readyMemberIndex(party);

    if (!memberIndex)
    {
        return false;
    }

    // The action is the ready member's, whoever the player selected since the queue chose it.
    party.setActiveCombatantIndex(*memberIndex);
    return true;
}

bool TurnBasedCombatRuntime::canPassTurn(const Party &party) const
{
    return (m_active && m_stage == TurnBasedCombatStage::Movement) || canBeginPlayerAction(party);
}

bool TurnBasedCombatRuntime::passTurn(Party &party, float recoverySeconds)
{
    if (m_active && m_stage == TurnBasedCombatStage::Movement)
    {
        return finishMovementPhase();
    }

    return canBeginPlayerAction(party) && applyPlayerAction(party, party.activeCombatantIndex(), recoverySeconds);
}

bool TurnBasedCombatRuntime::applyPlayerAction(Party &party, size_t memberIndex, float recoverySeconds)
{
    if (!m_active)
    {
        return false;
    }

    if (m_stage != TurnBasedCombatStage::Attack || hasPendingActions() || m_queue.empty())
    {
        GAMEPLAY_DEBUG_TRACE(
            "turn_based_player_action_refused stage=" + std::string(turnStageName(m_stage))
            + " pending=" + std::to_string(m_pendingActions)
            + " queue_empty=" + (m_queue.empty() ? "true" : "false")
            + " requested_member=" + std::to_string(memberIndex));
        return false;
    }

    const std::optional<size_t> queueIndex = readyCharacterQueueIndex(&party);
    if (!queueIndex || m_queue[*queueIndex].id != memberIndex)
    {
        GAMEPLAY_DEBUG_TRACE(
            "turn_based_player_action_wrong_front requested_member=" + std::to_string(memberIndex)
            + " ready_member=" + (queueIndex ? std::to_string(m_queue[*queueIndex].id) : std::string("none"))
            + " " + queueSummary(m_queue));
        return false;
    }

    const int requestedRecoveryTicks = std::max(
        MinimumPlayerRecoveryTicks,
        recoverySecondsToTicks(
            m_memberTurnRecoverySeconds[std::min(memberIndex, MaximumTrackedMembers - 1)] > 0.0f
                ? m_memberTurnRecoverySeconds[std::min(memberIndex, MaximumTrackedMembers - 1)]
                : recoverySeconds));
    m_queue[*queueIndex].initiative = requestedRecoveryTicks;
    m_actorActionTimerTicks = 0.0f;
    m_loggedReadyMemberIndex.reset();

    if (memberIndex < MaximumTrackedMembers)
    {
        m_memberTurnRecoverySeconds[memberIndex] = 0.0f;
    }

    Character *pMember = party.combatant(memberIndex);
    if (pMember != nullptr)
    {
        pMember->recoverySecondsRemaining = 0.0f;
    }

    sortQueue(&party);
    advanceAttackQueue(&party);
    GAMEPLAY_DEBUG_TRACE(
        "turn_based_player_action_applied member=" + std::to_string(memberIndex)
        + " recovery_ticks=" + std::to_string(requestedRecoveryTicks)
        + " stage=" + std::string(turnStageName(m_stage))
        + " " + queueSummary(m_queue));
    return true;
}

void TurnBasedCombatRuntime::storeMemberTurnRecovery(size_t memberIndex, float recoverySeconds)
{
    if (memberIndex < MaximumTrackedMembers)
    {
        m_memberTurnRecoverySeconds[memberIndex] = std::max(0.0f, recoverySeconds);
    }
}

void TurnBasedCombatRuntime::registerPendingAction()
{
    if (m_active)
    {
        ++m_pendingActions;
        GAMEPLAY_DEBUG_TRACE("turn_based_pending_increment pending=" + std::to_string(m_pendingActions));
    }
}

void TurnBasedCombatRuntime::resolvePendingAction()
{
    if (m_pendingActions > 0)
    {
        --m_pendingActions;
        GAMEPLAY_DEBUG_TRACE("turn_based_pending_decrement pending=" + std::to_string(m_pendingActions));
    }
}

void TurnBasedCombatRuntime::rebuildInitialQueue(
    Party &party,
    const IGameplayWorldRuntime *pWorldRuntime,
    const std::vector<float> &attackRecoverySeconds)
{
    m_queue.clear();

    std::vector<size_t> readyMembers;

    // Character entries are combatants: the members, then the MM9 hirelings, who wait for the player's command on
    // their turn as the members do (MM9_HIRELINGS.md 9.1).
    for (size_t memberIndex = 0; memberIndex < party.combatantCount(); ++memberIndex)
    {
        const Character &member = *party.combatant(memberIndex);

        if (!memberCanStayInTurnQueue(member))
        {
            continue;
        }

        if (member.recoverySecondsRemaining <= 0.0f)
        {
            readyMembers.push_back(memberIndex);
        }
        else
        {
            m_queue.push_back(QueueEntry{
                .kind = QueueEntry::Kind::Character,
                .id = memberIndex,
                // MM8 Start scales remaining recovery by 0.46875 and, unlike OE, adds no 16-tick offset.
                .initiative = recoverySecondsToTicks(member.recoverySecondsRemaining) * 15 / 32,
            });
        }
    }

    // MM8 Start (0x4065d7) orders the ready members by their attack recovery: the fastest acts first. Party order
    // breaks ties.
    const auto attackRecovery = [&attackRecoverySeconds](size_t memberIndex)
    {
        return memberIndex < attackRecoverySeconds.size() ? attackRecoverySeconds[memberIndex] : 0.0f;
    };
    std::stable_sort(
        readyMembers.begin(),
        readyMembers.end(),
        [&attackRecovery](size_t left, size_t right)
        {
            return attackRecovery(left) < attackRecovery(right);
        });

    int initiative = 2;
    for (size_t memberIndex : readyMembers)
    {
        m_queue.push_back(QueueEntry{
            .kind = QueueEntry::Kind::Character,
            .id = memberIndex,
            .initiative = initiative++,
        });
    }

    if (pWorldRuntime != nullptr)
    {
        const size_t actorCount = pWorldRuntime->mapActorCount();
        const float partyX = pWorldRuntime->partyX();
        const float partyY = pWorldRuntime->partyY();
        const float partyZ = pWorldRuntime->partyFootZ();

        size_t candidateActors = 0;
        size_t queuedActors = 0;
        size_t distantActors = 0;

        for (size_t actorIndex = 0; actorIndex < actorCount; ++actorIndex)
        {
            bool distant = false;
            if (!actorCanJoinTurnQueue(*pWorldRuntime, actorIndex, distant))
            {
                if (distant)
                {
                    ++candidateActors;
                    ++distantActors;
                }

                continue;
            }

            ++candidateActors;

            // MM8 Start rolls rand() % 99 per monster: under 33 enters at 1, under 66 at 3, else 5.
            const uint32_t roll = m_random() % 99u;
            m_queue.push_back(QueueEntry{
                .kind = QueueEntry::Kind::Actor,
                .id = actorIndex,
                .initiative = roll < 33u ? 1 : roll < 66u ? 3 : 5,
            });
            ++queuedActors;
        }

        GAMEPLAY_DEBUG_TRACE(
            "turn_based_actor_queue_scan actor_count=" + std::to_string(actorCount)
            + " candidates=" + std::to_string(candidateActors)
            + " queued=" + std::to_string(queuedActors)
            + " distant=" + std::to_string(distantActors)
            + " party=(" + std::to_string(partyX) + "," + std::to_string(partyY)
            + "," + std::to_string(partyZ) + ")");
    }
}

void TurnBasedCombatRuntime::addArrivedCombatants(const Party &party, const IGameplayWorldRuntime *pWorldRuntime)
{
    const auto queued = [this](QueueEntry::Kind kind, size_t id)
    {
        return std::any_of(
            m_queue.begin(),
            m_queue.end(),
            [kind, id](const QueueEntry &entry)
            {
                return entry.kind == kind && entry.id == id;
            });
    };

    // OE StartTurn: members able to act again rejoin at full turn initiative, newly arrived actors act first.
    for (size_t memberIndex = 0; memberIndex < party.combatantCount(); ++memberIndex)
    {
        if (memberCanStayInTurnQueue(*party.combatant(memberIndex))
            && !queued(QueueEntry::Kind::Character, memberIndex))
        {
            m_queue.push_back(QueueEntry{
                .kind = QueueEntry::Kind::Character,
                .id = memberIndex,
                .initiative = ArrivedCharacterInitiative,
            });
        }
    }

    if (pWorldRuntime == nullptr)
    {
        return;
    }

    for (size_t actorIndex = 0; actorIndex < pWorldRuntime->mapActorCount(); ++actorIndex)
    {
        bool distant = false;
        if (!queued(QueueEntry::Kind::Actor, actorIndex)
            && actorCanJoinTurnQueue(*pWorldRuntime, actorIndex, distant))
        {
            m_queue.push_back(QueueEntry{
                .kind = QueueEntry::Kind::Actor,
                .id = actorIndex,
                .initiative = ArrivedActorInitiative,
            });
            GAMEPLAY_DEBUG_TRACE("turn_based_actor_joined actor=" + std::to_string(actorIndex));
        }
    }
}

void TurnBasedCombatRuntime::removeInvalidActorEntries(const IGameplayWorldRuntime *pWorldRuntime)
{
    if (pWorldRuntime == nullptr)
    {
        return;
    }

    m_queue.erase(
        std::remove_if(
            m_queue.begin(),
            m_queue.end(),
            [pWorldRuntime](const QueueEntry &entry)
            {
                if (entry.kind != QueueEntry::Kind::Actor)
                {
                    return false;
                }

                GameplayRuntimeActorState actor = {};
                return !pWorldRuntime->actorRuntimeState(entry.id, actor) || !actorCanEnterTurnQueue(actor);
            }),
        m_queue.end());
}

std::optional<size_t> TurnBasedCombatRuntime::readyCharacterQueueIndex(const Party *pParty) const
{
    for (size_t queueIndex = 0; queueIndex < m_queue.size(); ++queueIndex)
    {
        const QueueEntry &entry = m_queue[queueIndex];
        if (entry.kind != QueueEntry::Kind::Character || entry.initiative > 0)
        {
            continue;
        }

        if (pParty != nullptr)
        {
            if (entry.id >= pParty->combatantCount() || !memberCanStayInTurnQueue(*pParty->combatant(entry.id)))
            {
                continue;
            }
        }

        return queueIndex;
    }

    return std::nullopt;
}

bool TurnBasedCombatRuntime::readyActorQueued() const
{
    return std::any_of(
        m_queue.begin(),
        m_queue.end(),
        [](const QueueEntry &entry)
        {
            return entry.kind == QueueEntry::Kind::Actor && entry.initiative <= 0;
        });
}

void TurnBasedCombatRuntime::sortQueue(Party *pParty)
{
    if (pParty != nullptr)
    {
        removeInvalidEntries(*pParty);
    }

    std::stable_sort(
        m_queue.begin(),
        m_queue.end(),
        [](const QueueEntry &left, const QueueEntry &right)
        {
            if (left.initiative != right.initiative)
            {
                return left.initiative < right.initiative;
            }

            if (left.kind != right.kind)
            {
                return left.kind == QueueEntry::Kind::Character;
            }

            return left.id < right.id;
        });

    while (!m_queue.empty() && m_queue.back().initiative >= InactiveInitiative)
    {
        m_queue.pop_back();
    }

    selectFrontCharacter(pParty);
}

void TurnBasedCombatRuntime::selectFrontCharacter(Party *pParty)
{
    if (pParty == nullptr)
    {
        return;
    }

    const std::optional<size_t> queueIndex = readyCharacterQueueIndex(pParty);
    if (!queueIndex)
    {
        return;
    }

    const size_t memberIndex = m_queue[*queueIndex].id;
    pParty->setActiveCombatantIndex(memberIndex);

    Character *pMember = pParty->combatant(memberIndex);
    if (pMember != nullptr)
    {
        pMember->recoverySecondsRemaining = 0.0f;
    }
}

void TurnBasedCombatRuntime::removeInvalidEntries(const Party &party)
{
    m_queue.erase(
        std::remove_if(
            m_queue.begin(),
            m_queue.end(),
            [&party](const QueueEntry &entry)
            {
                if (entry.kind != QueueEntry::Kind::Character)
                {
                    return false;
                }

                return entry.id >= party.combatantCount() || !memberCanStayInTurnQueue(*party.combatant(entry.id));
            }),
        m_queue.end());
}

void TurnBasedCombatRuntime::advanceAttackQueue(Party *pParty)
{
    if (pParty == nullptr || m_queue.empty())
    {
        enterMovementStage();
        return;
    }

    for (;;)
    {
        sortQueue(pParty);

        const std::optional<size_t> readyCharacterIndex = readyCharacterQueueIndex(pParty);
        if (readyCharacterIndex)
        {
            selectFrontCharacter(pParty);
            const size_t memberIndex = m_queue[*readyCharacterIndex].id;
            if (!m_loggedReadyMemberIndex || *m_loggedReadyMemberIndex != memberIndex)
            {
                GAMEPLAY_DEBUG_TRACE(
                    "turn_based_front_player member=" + std::to_string(memberIndex)
                    + " " + queueSummary(m_queue));
                m_loggedReadyMemberIndex = memberIndex;
            }
            return;
        }

        if (readyActorQueued())
        {
            // Ready actors take their action through beginReadyActorActions, which needs the world.
            m_loggedReadyMemberIndex.reset();
            return;
        }

        int nextInitiative = InactiveInitiative;
        for (const QueueEntry &entry : m_queue)
        {
            if (entry.initiative > 0)
            {
                nextInitiative = std::min(nextInitiative, entry.initiative);
            }
        }

        if (nextInitiative == InactiveInitiative || m_turnInitiative <= 0)
        {
            enterMovementStage();
            GAMEPLAY_DEBUG_TRACE(
                "turn_based_stage stage=movement reason=attack_queue_exhausted turn_initiative="
                + std::to_string(m_turnInitiative)
                + " movement_ap=" + std::to_string(m_movementActionPoints)
                + " " + queueSummary(m_queue));
            return;
        }

        const int initiativeStep = std::min(nextInitiative, m_turnInitiative);
        m_loggedReadyMemberIndex.reset();
        for (QueueEntry &entry : m_queue)
        {
            if (entry.initiative < InactiveInitiative)
            {
                entry.initiative = std::max(0, entry.initiative - initiativeStep);
            }
        }

        m_turnInitiative -= initiativeStep;
        sortQueue(pParty);
        GAMEPLAY_DEBUG_TRACE(
            "turn_based_initiative_step step=" + std::to_string(initiativeStep)
            + " turn_initiative=" + std::to_string(m_turnInitiative)
            + " " + queueSummary(m_queue));

        if (m_turnInitiative <= 0 && !readyCharacterQueueIndex(pParty) && !readyActorQueued())
        {
            enterMovementStage();
            GAMEPLAY_DEBUG_TRACE(
                "turn_based_stage stage=movement reason=attack_queue_blocked turn_initiative="
                + std::to_string(m_turnInitiative)
                + " movement_ap=" + std::to_string(m_movementActionPoints)
                + " " + queueSummary(m_queue));
            return;
        }
    }
}

void TurnBasedCombatRuntime::beginReadyActorActions(Party *pParty, IGameplayWorldRuntime *pWorldRuntime)
{
    if (pWorldRuntime == nullptr
        || m_stage != TurnBasedCombatStage::Attack
        || m_resolvingActorActions
        || readyCharacterQueueIndex(pParty)
        || !readyActorQueued())
    {
        return;
    }

    size_t grantedActors = 0;
    for (QueueEntry &entry : m_queue)
    {
        if (entry.kind != QueueEntry::Kind::Actor || entry.initiative > 0)
        {
            continue;
        }

        // OE: an actor acts when its initiative runs out, then waits its own monster recovery.
        pWorldRuntime->grantTurnBasedActorAction(entry.id);
        entry.initiative = std::max(1, pWorldRuntime->turnBasedActorRecoveryTicks(entry.id));
        ++grantedActors;
    }

    m_resolvingActorActions = true;
    m_actorActionTimerTicks = 0.0f;
    sortQueue(pParty);
    GAMEPLAY_DEBUG_TRACE(
        "turn_based_actor_actions_granted count=" + std::to_string(grantedActors)
        + " " + queueSummary(m_queue));
}

void TurnBasedCombatRuntime::updateAttackStage(
    Party *pParty,
    IGameplayWorldRuntime *pWorldRuntime,
    float deltaSeconds)
{
    if (m_resolvingActorActions)
    {
        m_actorActionTimerTicks += std::max(0.0f, deltaSeconds) * TurnTicksPerSecond;
        const bool actorsBusy =
            pWorldRuntime != nullptr
            && (pWorldRuntime->turnBasedActorActionGrantPending() || pWorldRuntime->turnBasedActorActionInProgress());

        if (actorsBusy && m_actorActionTimerTicks < ActorTurnActionMaxTicks)
        {
            return;
        }

        GAMEPLAY_DEBUG_TRACE(
            std::string("turn_based_actor_actions_resolved timeout=") + (actorsBusy ? "true" : "false")
            + " ticks=" + std::to_string(m_actorActionTimerTicks));
        m_resolvingActorActions = false;
    }

    if (hasPendingActions())
    {
        return;
    }

    advanceAttackQueue(pParty);
    beginReadyActorActions(pParty, pWorldRuntime);
}

void TurnBasedCombatRuntime::enterWaitStage()
{
    m_stage = TurnBasedCombatStage::Wait;
    m_aiTurnTimerTicks = InitialWaitTicks;
    m_actorActionTimerTicks = 0.0f;
    m_movementActionPoints = 0.0f;
    m_movementFinished = false;
    m_movementStepThisFrame = false;
    m_movementStepSeconds = 0.0f;
    m_waitingForActorActionResolution = false;
    clearMovementLatches();
    m_loggedReadyMemberIndex.reset();
}

void TurnBasedCombatRuntime::enterAttackStage(Party *pParty, IGameplayWorldRuntime *pWorldRuntime)
{
    m_stage = TurnBasedCombatStage::Attack;
    m_turnInitiative = 100;
    m_actorActionTimerTicks = 0.0f;
    ++m_turnCount;

    if (pParty != nullptr && pParty->statistics() != nullptr)
    {
        pParty->statistics()->recordTurnBasedTurn();
    }

    m_movementActionPoints = 0.0f;
    m_movementFinished = false;
    m_waitingForActorActionResolution = false;
    m_resolvingActorActions = false;
    m_loggedReadyMemberIndex.reset();

    for (QueueEntry &entry : m_queue)
    {
        if (entry.initiative <= 0)
        {
            entry.initiative = 100;
        }
    }

    if (pParty != nullptr)
    {
        addArrivedCombatants(*pParty, pWorldRuntime);
    }

    advanceAttackQueue(pParty);
    beginReadyActorActions(pParty, pWorldRuntime);
}

void TurnBasedCombatRuntime::enterMovementStage()
{
    m_stage = TurnBasedCombatStage::Movement;
    m_pendingGameTimeAdvanceMinutes += CompletedTurnGameTimeMinutes;
    m_movementActionPoints = TurnMovementActionPoints;
    m_movementFinished = false;
    m_movementStart.reset();
    m_movementStepThisFrame = false;
    m_movementStepSeconds = 0.0f;
    m_waitingForActorActionResolution = false;
    clearMovementLatches();
    m_loggedReadyMemberIndex.reset();
}

float TurnBasedCombatRuntime::spendMovementBudget(float deltaSeconds)
{
    if (m_movementActionPoints <= 0.0f || deltaSeconds <= 0.0f)
    {
        m_movementActionPoints = std::max(0.0f, m_movementActionPoints);
        m_movementFinished = m_movementFinished || m_movementActionPoints <= 0.0f;
        return 0.0f;
    }

    const float stepSeconds = std::min(deltaSeconds, m_movementActionPoints / TurnTicksPerSecond);
    m_movementActionPoints = std::max(0.0f, m_movementActionPoints - stepSeconds * TurnTicksPerSecond);

    if (m_movementActionPoints <= 0.001f)
    {
        m_movementActionPoints = 0.0f;
        m_movementFinished = true;
    }

    return stepSeconds;
}

void TurnBasedCombatRuntime::clearMovementLatches()
{
    m_forwardLatch = false;
    m_backwardLatch = false;
    m_strafeLeftLatch = false;
    m_strafeRightLatch = false;
}
} // namespace OpenYAMM::Game
