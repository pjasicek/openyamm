#pragma once

#include "game/audio/SoundIds.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayCombatController.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/gameplay/GameplayScreenState.h"
#include "game/gameplay/GameplaySpellActionController.h"
#include "game/ui/GameplayUiController.h"

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class ItemTable;
class MonsterProjectileTable;
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
        int hourOfPowerPower = 0;
        ActorRulesetFacts rulesetFacts;
        bool isDead = false;
        bool isInvisible = false;
        bool hostileToParty = false;
        bool visibleForFallback = false;
        bool lineOfSightToParty = true;
    };

    static bool isPartyAttackActorTargetable(const GameplayPartyAttackActorFacts &actor)
    {
        return !actor.isDead && actor.currentHp > 0 && !actor.isInvisible;
    }

    static bool isPartyAttackFallbackCandidate(const GameplayPartyAttackActorFacts &actor)
    {
        return isPartyAttackActorTargetable(actor)
            && actor.hostileToParty
            && actor.visibleForFallback
            && actor.lineOfSightToParty;
    }

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
        // The worlds' party guns (monster_projectiles.yml party): a listed gun fires its own missile and sound.
        const MonsterProjectileTable *pMonsterProjectileTable = nullptr;
        const SpecialItemEnchantTable *pSpecialItemEnchantTable = nullptr;
        std::optional<size_t> directTargetActorIndex;
        std::optional<WorldPoint> directTargetHitPoint;
        std::optional<size_t> directTargetBModelIndex;
        // A decoration under the cursor (an indoor entity index): a destructible prop a blow damages.
        std::optional<size_t> directTargetEntityIndex;
        float directWorldTargetDistance = 0.0f;
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
        uint32_t fireArrowProjectileObjectId = 0;
        uint32_t throwingDaggerProjectileObjectId = 0;
        uint32_t throwingAxeProjectileObjectId = 0;
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
    // The Unstuck action (MAW's L key): lifts the party when its rules allow it now, else does nothing and says why.
    // True when the party was lifted.
    static bool tryUnstuckParty(Party &party, IGameplayWorldRuntime &worldRuntime, std::string &statusText);
    // The Knight Charge action at the actor under the cursor: what the party's rules say of it (empty for nothing to
    // show); nothing in rules or parties without a charge.
    static std::optional<std::string> tryPartyCharge(
        Party &party,
        IGameplayWorldRuntime &worldRuntime,
        std::optional<size_t> targetActorIndex);
    struct GatherLootResult
    {
        std::optional<std::string> statusText;
        // Set (active) when the map was complete and its satchels were looted outright.
        GameplayUiController::LootSummaryOverlayState summary;
    };

    // The gather key (MAW's K): brings the corpses and ground items the party's rules name in front of the party and
    // says how many came; on a completed map it first loots every satchel into the bags. Nothing in rules without it.
    static GatherLootResult gatherLoot(Party &party, IGameplayWorldRuntime &worldRuntime);
};
} // namespace OpenYAMM::Game
