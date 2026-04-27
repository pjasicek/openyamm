#pragma once

#include "game/audio/SoundIds.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayCombatController.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/gameplay/GameplayScreenState.h"
#include "game/gameplay/GameplaySpellActionController.h"

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class ItemTable;
class MonsterTable;
class Party;
class GameplayScreenRuntime;
class GameplaySpellService;
class SpecialItemEnchantTable;
class SpellTable;

class GameplayActionController
{
public:
    enum class QuickCastActionResult
    {
        Failed,
        CastStarted,
        AttackFallback
    };

    struct QuickCastActionConfig
    {
        bool canRunAction = false;
        bool quickCastPressed = false;
        bool hasReadyMember = false;
    };

    struct QuickCastActionDecision
    {
        bool shouldBeginQuickCast = false;
    };

    struct AttackActionConfig
    {
        bool attackPressed = false;
        bool hasReadyMember = false;
    };

    struct AttackActionDecision
    {
        bool shouldAttemptAttack = false;
        bool pressedThisFrame = false;
    };

    struct WorldPoint
    {
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
    };

    struct PartyAttackActorFacts
    {
        size_t actorIndex = 0;
        int16_t monsterId = 0;
        std::string displayName;
        WorldPoint position = {};
        uint16_t radius = 0;
        uint16_t height = 0;
        int currentHp = 0;
        int maxHp = 0;
        int effectiveArmorClass = 0;
        bool isDead = false;
        bool isInvisible = false;
        bool hostileToParty = false;
        bool visibleForFallback = false;
    };

    struct AttackCastResult
    {
        bool castStarted = false;
        bool followupUiActive = false;
    };

    struct PartyAttackConfig
    {
        GameplayScreenRuntime *pRuntime = nullptr;
        GameplaySpellService *pSpellService = nullptr;
        IGameplayWorldRuntime *pWorldRuntime = nullptr;
        Party *pParty = nullptr;
        const ItemTable *pItemTable = nullptr;
        const SpellTable *pSpellTable = nullptr;
        const MonsterTable *pMonsterTable = nullptr;
        const SpecialItemEnchantTable *pSpecialItemEnchantTable = nullptr;
        std::optional<size_t> directTargetActorIndex;
        std::string directTargetName;
        WorldPoint partyPosition = {};
        WorldPoint rangedSource = {};
        WorldPoint rangedRight = {};
        WorldPoint defaultRangedTarget = {};
        WorldPoint rayRangedTarget = {};
        bool hasRayRangedTarget = false;
        GameplayPartyAttackFallbackQuery fallbackQuery = {};
        GameplayWorldHoverRequest worldInspectionRefreshRequest = {};
        uint32_t randomSeed = 0;
        uint32_t arrowProjectileObjectId = 0;
        uint32_t blasterProjectileObjectId = 0;
        bool pressedThisFrame = false;
        GameplaySpellActionController::TargetQueries targetQueries = {};
    };

    struct PartyAttackExecutionResult
    {
        bool attempted = false;
        bool actionPerformed = false;
        bool attacked = false;
        bool killed = false;
        std::optional<size_t> targetActorIndex;
        size_t actingMemberIndex = 0;
        CharacterAttackResult attack = {};
    };

    static constexpr float HeldActionRepeatDebounceSeconds = 0.14f;

    static void updateCooldowns(GameplayScreenState &screenState, float deltaSeconds);
    static QuickCastActionDecision updateQuickCastAction(
        GameplayScreenState::QuickSpellState &quickSpellState,
        const QuickCastActionConfig &config);
    static void applyQuickCastActionResult(
        GameplayScreenState::QuickSpellState &quickSpellState,
        QuickCastActionResult result);
    static AttackActionDecision updateAttackAction(
        GameplayScreenState::AttackActionState &attackActionState,
        GameplayScreenState::QuickSpellState &quickSpellState,
        const AttackActionConfig &config);
    static PartyAttackExecutionResult executePartyAttack(const PartyAttackConfig &config);
};
} // namespace OpenYAMM::Game
