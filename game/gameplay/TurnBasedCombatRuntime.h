#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <random>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
class Party;
struct GameplayInputFrame;
class IGameplayWorldRuntime;
enum class ActorTurnBasedMode : uint8_t;

enum class TurnBasedCombatStage : uint8_t
{
    None,
    Wait,
    Attack,
    Movement,
};

// Whose turn the game clock may hurry (the turn-based speed settings): the monsters' wait and actions, or the party's
// attacks still in flight. None while a character chooses, while the party walks and in real time.
enum class TurnBasedSpeedPhase : uint8_t
{
    None,
    Monsters,
    Party,
};

class TurnBasedCombatRuntime
{
public:
    struct QueueEntry
    {
        enum class Kind : uint8_t
        {
            Character,
            Actor,
        };

        Kind kind = Kind::Character;
        size_t id = 0;
        int initiative = 0;
        float actionRecoverySeconds = 0.0f;
    };

    bool active() const;
    TurnBasedCombatStage stage() const;
    int movementActionPoints() const;
    int pendingActions() const;
    bool hasPendingActions() const;
    TurnBasedSpeedPhase speedPhase() const;
    bool playerActionReady(const Party &party) const;
    bool shouldUpdateActorAi(const Party *pParty) const;
    ActorTurnBasedMode actorMode() const;
    bool frontQueueCharacter(size_t &memberIndex) const;
    const std::vector<QueueEntry> &queue() const;

    // attackRecoverySeconds: each combatant's melee attack recovery; ready members enter fastest first (MM8 Start).
    bool begin(
        Party &party,
        const IGameplayWorldRuntime *pWorldRuntime,
        const std::vector<float> &attackRecoverySeconds = {});
    void end(Party *pParty, IGameplayWorldRuntime *pWorldRuntime, bool preserveRecovery = true);
    void reset();

    bool canToggleOff(const Party &party) const;
    bool toggle(
        Party &party,
        IGameplayWorldRuntime *pWorldRuntime,
        const std::vector<float> &attackRecoverySeconds = {});
    // Seeds the monsters' entry initiative rolls (MM8 rolls rand() % 99 per monster at the start).
    void seedRandom(uint32_t seed);
    bool update(Party *pParty, IGameplayWorldRuntime *pWorldRuntime, float deltaSeconds);

    // Movement-stage input spends the movement budget by walking time (one point per 1/128 s held).
    // In the classic scheme Left/Right turn the party, which is free in every turn-based stage like the original.
    bool noteMovementInput(GameplayInputFrame &input, float deltaSeconds, bool classicTurnKeys = false);
    float movementDeltaSecondsForFrame(float fallbackDeltaSeconds) const;
    float consumePendingGameTimeAdvanceMinutes();
    void clearMovementInput(GameplayInputFrame &input) const;
    bool finishMovementPhase();

    bool canBeginPlayerAction(const Party &party) const;
    // The member whose turn it is, when one may act now. Only that member may attack, cast, read or drink.
    std::optional<size_t> readyMemberIndex(const Party &party) const;
    bool beginPlayerActionOrFinishMovement(Party &party);
    bool applyPlayerAction(Party &party, size_t memberIndex, float recoverySeconds);
    // Pass ends the party's movement phase, or spends the ready member's action without acting.
    bool canPassTurn(const Party &party) const;
    bool passTurn(Party &party, float recoverySeconds);
    void storeMemberTurnRecovery(size_t memberIndex, float recoverySeconds);

    void registerPendingAction();
    void resolvePendingAction();

private:
    // Five members and three MM9 hirelings (Party::combatantCount).
    static constexpr size_t MaximumTrackedMembers = 8;

    bool noteMovementInputHeld(
        GameplayInputFrame &input,
        float deltaSeconds,
        bool forwardHeld,
        bool backwardHeld,
        bool leftHeld,
        bool rightHeld);
    void rebuildInitialQueue(
        Party &party,
        const IGameplayWorldRuntime *pWorldRuntime,
        const std::vector<float> &attackRecoverySeconds);
    void addArrivedCombatants(const Party &party, const IGameplayWorldRuntime *pWorldRuntime);
    void removeInvalidActorEntries(const IGameplayWorldRuntime *pWorldRuntime);
    std::optional<size_t> readyCharacterQueueIndex(const Party *pParty) const;
    bool readyActorQueued() const;
    void sortQueue(Party *pParty);
    void selectFrontCharacter(Party *pParty);
    void removeInvalidEntries(const Party &party);
    void advanceAttackQueue(Party *pParty);
    void beginReadyActorActions(Party *pParty, IGameplayWorldRuntime *pWorldRuntime);
    void updateAttackStage(Party *pParty, IGameplayWorldRuntime *pWorldRuntime, float deltaSeconds);
    void enterWaitStage();
    void enterAttackStage(Party *pParty, IGameplayWorldRuntime *pWorldRuntime);
    void enterMovementStage();
    float spendMovementBudget(float deltaSeconds);
    void clearMovementLatches();

    bool m_active = false;
    TurnBasedCombatStage m_stage = TurnBasedCombatStage::None;
    std::vector<QueueEntry> m_queue;
    int m_turnInitiative = 100;
    float m_aiTurnTimerTicks = 0.0f;
    float m_movementActionPoints = 0.0f;
    int m_pendingActions = 0;
    uint32_t m_turnCount = 0;
    float m_actorActionTimerTicks = 0.0f;
    bool m_movementFinished = false;
    // Where the party stood when the movement stage's first update ran.
    std::optional<std::pair<float, float>> m_movementStart;
    bool m_movementStepThisFrame = false;
    float m_movementStepSeconds = 0.0f;
    bool m_waitingForActorActionResolution = false;
    // Attack stage: granted actors are taking their queued action; the queue waits for them.
    bool m_resolvingActorActions = false;
    float m_pendingGameTimeAdvanceMinutes = 0.0f;
    bool m_forwardLatch = false;
    bool m_backwardLatch = false;
    bool m_strafeLeftLatch = false;
    bool m_strafeRightLatch = false;
    std::optional<size_t> m_loggedReadyMemberIndex;
    float m_memberTurnRecoverySeconds[MaximumTrackedMembers] = {};
    std::mt19937 m_random{1u};
    // Each combatant's melee attack recovery when the combat began, for a rebuilt queue's entry order.
    std::vector<float> m_attackRecoverySeconds;
};
} // namespace OpenYAMM::Game
