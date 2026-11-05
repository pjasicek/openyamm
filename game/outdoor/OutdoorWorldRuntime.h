#pragma once

#include "game/gameplay/ActorBehaviorRuntime.h"
#include "game/gameplay/ActorInspectPreviewAnimation.h"
#include "game/gameplay/GameplayActorHitFeedback.h"
#include "game/gameplay/GameplayActorModifiers.h"
#include "game/gameplay/GameplayActorShields.h"

#include "game/events/ISceneEventContext.h"
#include "game/events/EventRuntime.h"
#include "game/events/ScriptedEventProgram.h"
#include "game/gameplay/GameplayActionController.h"
#include "game/gameplay/GameplayActorAiSystem.h"
#include "game/gameplay/GameplayBolsterRuntime.h"
#include "game/gameplay/GameplayActorService.h"
#include "game/gameplay/GameplayCombatController.h"
#include "game/gameplay/GameplayProjectileService.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/gameplay/MonsterDeathExplosion.h"
#include "game/gameplay/SearchableLootPropRuntime.h"
#include "game/maps/ActorModelManifest.h"
#include "game/maps/MapAssetLoader.h"
#include "game/maps/MapDeltaData.h"
#include "game/pathfinding/ActorPathRuntime.h"
#include "game/pathfinding/PathMap.h"
#include "game/tables/MapStats.h"
#include "game/tables/MonsterProjectileTable.h"
#include "game/tables/MonsterTable.h"
#include "game/tables/ObjectTable.h"
#include "game/outdoor/OutdoorGeometryUtils.h"
#include "game/outdoor/OutdoorMapData.h"
#include "game/outdoor/OutdoorMovementController.h"
#include "game/outdoor/OutdoorWeatherProfile.h"
#include "game/party/Party.h"
#include "game/rules/CorpseLoot.h"
#include "game/tables/SpellTable.h"

#include <array>
#include <optional>
#include <random>
#include <memory>
#include <string>
#include <utility>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
struct ItemModelBinding;
struct WorldItemSphereChain;
class ItemTable;
class ChestTable;
struct ChestTrapOpenResult;
class GameplayFxService;
class GameplayProjectileService;
class MergedBolsterMapTable;
class MergedBolsterMonsterTable;
class OutdoorGameView;
class StandardItemEnchantTable;
class SpecialItemEnchantTable;
class WorldFxSystem;
class OutdoorPartyRuntime;

class OutdoorWorldRuntime : public ISceneEventContext, public IGameplayWorldRuntime
{
public:
    using ChestItemState = GameplayChestItemState;
    using ChestViewState = GameplayChestViewState;
    using CorpseViewState = GameplayCorpseViewState;

    struct AtmosphereState
    {
        static constexpr int32_t WeatherFoggy = 1;
        static constexpr int32_t WeatherSnowing = 2;
        static constexpr int32_t WeatherRaining = 4;

        std::string sourceSkyTextureName;
        std::string skyTextureName;
        int32_t weatherFlags = 0;
        int32_t fogWeakDistance = 0;
        int32_t fogStrongDistance = 0;
        bool redFog = false;
        bool underwater = false;
        bool alwaysDark = false;
        bool alwaysLight = false;
        bool hasFogTint = false;
        uint8_t fogTintRed = 255;
        uint8_t fogTintGreen = 255;
        uint8_t fogTintBlue = 255;
        bool directFog = false;
        bool hasAuthoredFogColor = false;
        uint8_t authoredFogRed = 0;
        uint8_t authoredFogGreen = 0;
        uint8_t authoredFogBlue = 0;
        bool isNight = false;
        float fogDensity = 0.0f;
        // Game-time weather from WeatherModel, refreshed with the clock and not saved; the outdoor view fades it in
        // real time for display and audio. Intensity is 0-1; wind is in world units per second.
        PrecipitationKind precipitation = PrecipitationKind::None;
        float precipitationIntensity = 0.0f;
        float cloudCover = 0.0f;
        float windX = 0.0f;
        float windY = 0.0f;
        bool storm = false;
        // Lightning without rain (weather.yml dry_lightning).
        bool dryLightning = false;
        float wetness = 0.0f;
        // Haze of falling flakes that have one (ash), not saved: the fog closes to at most these distances while
        // it lasts. A strong distance of 0 is no haze.
        int32_t hazeWeakDistance = 0;
        int32_t hazeStrongDistance = 0;
        float ambientBrightness = 0.69f;
        float visibilityDistance = 200000.0f;
        float darknessOverlayAlpha = 0.0f;
        uint32_t darknessOverlayColorAbgr = 0x00000000u;
        float gameplayOverlayAlpha = 0.0f;
        uint32_t gameplayOverlayColorAbgr = 0x00000000u;
        float sunDirectionX = 0.0f;
        float sunDirectionY = 0.0f;
        float sunDirectionZ = 1.0f;
        uint32_t clearColorAbgr = 0x000000ffu;
        // Derived on every refresh and not saved: the weather sky before the Classic clock swap, and the
        // merged clear-to-storm ladder position (-1 when the map has no merged weather ladder).
        std::string weatherSkyTextureName;
        int mergedWeatherState = -1;
        int mergedWeatherStateCount = 0;

        struct ShownFog
        {
            bool foggy = false;
            int32_t weakDistance = 0;
            int32_t strongDistance = 0;
        };

        // The fog the world is drawn with: the map's fog weather (flag bit 1 and its distances), closed further by
        // any precipitation haze. Without a haze it is exactly the map's fog.
        ShownFog shownFog() const
        {
            const bool mapFoggy = (weatherFlags & 1) != 0;

            if (hazeStrongDistance <= 0)
            {
                return {mapFoggy, fogWeakDistance, fogStrongDistance};
            }

            if (!mapFoggy || fogWeakDistance < 0 || fogStrongDistance <= fogWeakDistance)
            {
                return {true, hazeWeakDistance, hazeStrongDistance};
            }

            return {true, std::min(fogWeakDistance, hazeWeakDistance), std::min(fogStrongDistance, hazeStrongDistance)};
        }
    };

    enum class ActorAiState
    {
        Standing,
        Wandering,
        Pursuing,
        Fleeing,
        Stunned,
        Attacking,
        Dying,
        Dead,
    };

    enum class ActorAnimation
    {
        Standing = 0,
        Walking = 1,
        AttackMelee = 2,
        AttackRanged = 3,
        GotHit = 4,
        Dying = 5,
        Dead = 6,
        Bored = 7,
    };

    using MonsterAttackAbility = GameplayProjectileService::MonsterAttackAbility;

    enum class DebugTargetKind
    {
        None,
        Party,
        Actor,
    };

    enum class ProjectileCollisionKind
    {
        None,
        Party,
        Actor,
        BModel,
        Terrain,
    };

    enum class ActorControlMode : uint8_t
    {
        None = 0,
        Charm,
        Berserk,
        Enslaved,
        ControlUndead,
        Reanimated,
    };

    // Runtime-only visual diagnostics for sky and weather captures; never saved.
    struct DebugSkyOverrides
    {
        std::optional<int> mergedWeatherState;
        std::optional<std::string> skyTextureName;
        std::optional<std::pair<int32_t, int32_t>> fogDistances;
        // Forced precipitation (None clears it) at the given 0-1 intensity.
        std::optional<PrecipitationKind> precipitation;
        float precipitationIntensity = 0.5f;
        // Forced wind, world units per second.
        std::optional<std::pair<float, float>> wind;
        std::optional<bool> storm;
    };

    struct SpellCastRequest;
    struct PartyProjectileRequest;

    struct MapActorState
    {
        uint32_t actorId = 0;
        int16_t monsterId = 0;
        int16_t npcId = 0;
        int32_t mm9RudeId = 0;
        bool usesMm9ActorRules = false;
        bool canReceiveDamage = true;
        bool mm9Civilian = false;
        bool mm9Guard = false;
        bool mm9FleeingFromParty = false;
        float mm9FleeRemainingSeconds = 0.0f;
        // A villager the party yelled at runs from it until this runs out (scareNearbyPeasants); not saved.
        float yellFleeRemainingSeconds = 0.0f;
        float mm9HelpCooldownSeconds = 0.0f;
        uint8_t mm9PlayerHitCount = 0;
        std::string displayName;
        uint32_t uniqueNameId = 0;
        bool spawnedAtRuntime = false;
        // A runtime spawn's MM9 placement (an arena's mm9_ai, a death spawn's ScriptParams 1); a map actor's is the
        // map's (MapDeltaActor::mm9Ai, OutdoorWorldRuntime::mm9Placement).
        std::optional<Mm9AiPlacementRecord> mm9Ai;
        bool fromSpawnPoint = false;
        size_t spawnPointIndex = static_cast<size_t>(-1);
        uint32_t group = 0;
        uint32_t ally = 0;
        // The party member whose spell summoned it, -1 for none (MM8's Summoner field).
        int32_t summonerMemberIndex = -1;
        uint8_t hostilityType = 0;
        uint32_t specialItemId = 0;
        bool proceduralDeathLoot = true;
        int currentHp = 0;
        int maxHp = 0;
        float bolsterRewardMultiplier = 1.0f;
        ActorRulesetFacts rulesetFacts;
        int x = 0;
        int y = 0;
        int z = 0;
        float preciseX = 0.0f;
        float preciseY = 0.0f;
        float preciseZ = 0.0f;
        int homeX = 0;
        int homeY = 0;
        int homeZ = 0;
        float homePreciseX = 0.0f;
        float homePreciseY = 0.0f;
        float homePreciseZ = 0.0f;
        uint16_t radius = 0;
        uint16_t height = 0;
        uint16_t moveSpeed = 0;
        // The rules' speed while not hostile to the party (0: moveSpeed).
        uint16_t calmMoveSpeed = 0;
        GameplayActorAiType aiType = GameplayActorAiType::Normal;
        int armorClass = 0;
        bool immobile = false;
        // Resting until hurt or woken (the placement's dormant; MapDeltaActor::dormant).
        bool dormant = false;
        bool canFly = false;
        CombatDamageType attack1DamageType = CombatDamageType::Physical;
        CombatDamageType attack2DamageType = CombatDamageType::Physical;
        uint32_t spell1Id = 0;
        CombatDamageType spell1DamageType = CombatDamageType::Physical;
        bool spell1CastSupported = true;
        uint32_t spell2Id = 0;
        CombatDamageType spell2DamageType = CombatDamageType::Physical;
        bool spell2CastSupported = true;
        float wanderRadius = 0.0f;
        int attack1DamageDiceRolls = 0;
        int attack1DamageDiceSides = 0;
        int attack1DamageBonus = 0;
        int attack2DamageDiceRolls = 0;
        int attack2DamageDiceSides = 0;
        int attack2DamageBonus = 0;
        bool generatedAttack2 = false;
        bool generatedAttack2IsRanged = false;
        bool copyAttack1DamageToAttack2 = false;
        std::string generatedAttack2MissileType;
        int generatedAttack2Chance = 0;
        int generatedSpell1UseChance = 0;
        int generatedSpell2UseChance = 0;
        uint32_t spell1SkillLevel = 0;
        SkillMastery spell1SkillMastery = SkillMastery::None;
        uint32_t spell2SkillLevel = 0;
        SkillMastery spell2SkillMastery = SkillMastery::None;
        uint16_t spriteFrameIndex = 0;
        std::array<uint16_t, 8> actionSpriteFrameIndices = {};
        bool useStaticSpriteFrame = false;
        bool hostileToParty = false;
        bool isDead = false;
        // Runtime: the killing blow came from a party member (their weapons and spells), read when the death settles.
        bool killedByParty = false;
        bool isInvisible = false;
        bool alertStatusBit = false;
        bool bloodSplatSpawned = false;
        bool hasDetectedParty = false;
        // MM's Nearby attribute, which indoor actors keep in their attributes: set for good once the party's AI range
        // (5632) reaches it or the party hits it, whether or not it noticed the party. Wizard Eye shows it from then on.
        bool nearby = false;
        // The party made it hostile (hit it or its faction), so a hit on it still alerts its friendly faction; an
        // actor hostile on its own (map, template, event) alerts none.
        bool angeredByParty = false;
        // A party hit woke it beyond the full-AI range: it acts out to the engagement range until it comes within
        // the full-AI range or loses the party (MM8 leaves an outdoor monster shot from afar standing).
        bool provokedByParty = false;
        // The distance of the party's last hit when beyond the native missile reach: it may shoot back from there
        // (0 for the native reach), until it loses the party.
        float provokedAttackReach = 0.0f;
        ActorAiState aiState = ActorAiState::Standing;
        ActorAnimation animation = ActorAnimation::Standing;
        float animationTimeTicks = 0.0f;
        float recoverySeconds = 0.0f;
        float attackAnimationSeconds = 0.3f;
        float attackCooldownSeconds = 0.0f;
        float idleDecisionSeconds = 0.0f;
        float actionSeconds = 0.0f;
        float moveDirectionX = 0.0f;
        float moveDirectionY = 0.0f;
        float velocityX = 0.0f;
        float velocityY = 0.0f;
        float velocityZ = 0.0f;
        // Horizontal speed the AI's movement asked for before collision; 0 when it did not try to move.
        float intendedSpeed = 0.0f;
        float yawRadians = 0.0f;
        float slowRemainingSeconds = 0.0f;
        float slowMoveMultiplier = 1.0f;
        float slowRecoveryMultiplier = 1.0f;
        float stunRemainingSeconds = 0.0f;
        float paralyzeRemainingSeconds = 0.0f;
        float fearRemainingSeconds = 0.0f;
        float blindRemainingSeconds = 0.0f;
        float controlRemainingSeconds = 0.0f;
        ActorControlMode controlMode = ActorControlMode::None;
        float shrinkRemainingSeconds = 0.0f;
        float shrinkDamageMultiplier = 1.0f;
        float shrinkArmorClassMultiplier = 1.0f;
        float armorClassHalvedRemainingSeconds = 0.0f;
        float darkGraspRemainingSeconds = 0.0f;
        float dayOfProtectionRemainingSeconds = 0.0f;
        int dayOfProtectionPower = 0;
        float hourOfPowerRemainingSeconds = 0.0f;
        int hourOfPowerPower = 0;
        float painReflectionRemainingSeconds = 0.0f;
        float hammerhandsRemainingSeconds = 0.0f;
        int hammerhandsPower = 0;
        float hasteRemainingSeconds = 0.0f;
        float shieldRemainingSeconds = 0.0f;
        float stoneskinRemainingSeconds = 0.0f;
        int stoneskinPower = 0;
        float blessRemainingSeconds = 0.0f;
        int blessPower = 0;
        float fateRemainingSeconds = 0.0f;
        int fatePower = 0;
        float heroismRemainingSeconds = 0.0f;
        int heroismPower = 0;
        uint32_t idleDecisionCount = 0;
        uint32_t pursueDecisionCount = 0;
        uint32_t attackDecisionCount = 0;
        bool attackImpactTriggered = false;
        // A skirmisher's footwork (ActorRuntimeFacts::skirmishPhase); runtime only, not saved.
        ActorSkirmishPhase skirmishPhase = ActorSkirmishPhase::None;
        float skirmishSeconds = 0.0f;
        int8_t skirmishSide = 1;
        // An MM9 walker's loop (ActorRuntimeFacts::mm9) and what the world knows for it (ActorAiFacts::mm9World);
        // runtime only, not saved.
        ActorMm9State mm9;
        ActorMm9WorldFacts mm9World;
        MonsterAttackAbility queuedAttackAbility = MonsterAttackAbility::Attack1;
        OutdoorMoveState movementState = {};
        bool movementStateInitialized = false;
        float crowdSideLockRemainingSeconds = 0.0f;
        float crowdNoProgressSeconds = 0.0f;
        float crowdLastEdgeDistance = 0.0f;
        float crowdRetreatRemainingSeconds = 0.0f;
        float crowdStandRemainingSeconds = 0.0f;
        float crowdProbeX = 0.0f;
        float crowdProbeY = 0.0f;
        float crowdProbeEdgeDistance = 0.0f;
        float crowdProbeElapsedSeconds = 0.0f;
        uint8_t crowdEscapeAttempts = 0;
        int8_t crowdSideSign = 0;
        bool suppressLowHealthFlee = false;
    };

    using CombatEvent = GameplayCombatController::CombatEvent;

    struct ActorDecisionDebugInfo
    {
        size_t actorIndex = static_cast<size_t>(-1);
        int16_t monsterId = 0;
        uint8_t hostilityType = 0;
        bool hostileToParty = false;
        bool hasDetectedParty = false;
        ActorAiState aiState = ActorAiState::Standing;
        ActorAnimation animation = ActorAnimation::Standing;
        float idleDecisionSeconds = 0.0f;
        float actionSeconds = 0.0f;
        float attackCooldownSeconds = 0.0f;
        uint32_t idleDecisionCount = 0;
        uint32_t pursueDecisionCount = 0;
        uint32_t attackDecisionCount = 0;
        int monsterAiType = 0;
        bool movementAllowed = false;
        float partySenseRange = 0.0f;
        float distanceToParty = 0.0f;
        bool canSenseParty = false;
        DebugTargetKind targetKind = DebugTargetKind::None;
        size_t targetActorIndex = static_cast<size_t>(-1);
        int16_t targetMonsterId = 0;
        int relationToTarget = 0;
        float targetDistance = 0.0f;
        float targetEdgeDistance = 0.0f;
        bool targetCanSense = false;
        bool targetHasAttackLineOfSight = false;
        bool shouldPromoteHostility = false;
        float promotionRange = 0.0f;
        bool shouldEngageTarget = false;
        bool shouldFlee = false;
        bool inMeleeRange = false;
        bool attackJustCompleted = false;
        bool attackInProgress = false;
        bool friendlyNearParty = false;
    };

    using ProjectileState = GameplayProjectileService::ProjectileState;
    using ProjectileImpactState = GameplayProjectileService::ProjectileImpactState;

    struct ProjectileCollisionFacts
    {
        bool hit = false;
        float factor = 2.0f;
        bx::Vec3 point = {0.0f, 0.0f, 0.0f};
        ProjectileCollisionKind kind = ProjectileCollisionKind::None;
        std::string colliderName;
        size_t actorIndex = static_cast<size_t>(-1);
        size_t faceIndex = static_cast<size_t>(-1);
        bool waterTerrainImpact = false;
    };


    struct ProjectileFrameWorldFacts
    {
        GameplayProjectileService::ProjectileFrameFacts frame;
        ProjectileCollisionFacts collision;
    };

    struct FireSpikeTrapState
    {
        uint32_t trapId = 0;
        ProjectileState::SourceKind sourceKind = ProjectileState::SourceKind::Party;
        uint32_t sourceId = 0;
        uint32_t sourcePartyMemberIndex = 0;
        int16_t sourceMonsterId = 0;
        bool fromSummonedMonster = false;
        MonsterAttackAbility ability = MonsterAttackAbility::Attack1;
        uint16_t objectDescriptionId = 0;
        uint16_t objectSpriteId = 0;
        uint16_t objectSpriteFrameIndex = 0;
        uint16_t impactObjectDescriptionId = 0;
        uint16_t objectFlags = 0;
        uint16_t radius = 0;
        uint16_t height = 0;
        int spellId = 0;
        int effectSoundId = 0;
        uint32_t skillLevel = 0;
        uint32_t skillMastery = 0;
        std::string objectName;
        std::string objectSpriteName;
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        uint32_t timeSinceCreatedTicks = 0;
        bool isExpired = false;
    };

    struct WorldItemState
    {
        uint32_t worldItemId = 0;
        InventoryItem item = {};
        uint32_t goldAmount = 0;
        bool isGold = false;
        uint16_t objectDescriptionId = 0;
        uint16_t objectSpriteId = 0;
        uint16_t objectSpriteFrameIndex = 0;
        uint16_t objectFlags = 0;
        uint16_t radius = 0;
        uint16_t height = 0;
        uint16_t soundId = 0;
        uint16_t attributes = 0;
        int16_t sectorId = 0;
        std::string objectName;
        std::string objectSpriteName;
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        float velocityX = 0.0f;
        float velocityY = 0.0f;
        float velocityZ = 0.0f;
        float initialX = 0.0f;
        float initialY = 0.0f;
        float initialZ = 0.0f;
        uint32_t timeSinceCreatedTicks = 0;
        uint32_t lifetimeTicks = 0;
        bool spawnedByPlayer = false;
        bool isExpired = false;
        std::string semanticSourceId;
        bool semanticPlacedPickup = false;
        uint32_t semanticLootContainerId = 0;
        bool semanticLootContainer = false;
    };

    struct SpawnPointState
    {
        int x = 0;
        int y = 0;
        int z = 0;
        uint16_t radius = 0;
        uint16_t typeId = 0;
        uint16_t index = 0;
        uint16_t attributes = 0;
        uint32_t group = 0;
        int encounterSlot = 0;
        bool isFixedTier = false;
        char fixedTier = '\0';
        int minCount = 0;
        int maxCount = 0;
        int16_t representativeMonsterId = 0;
        uint8_t hostilityType = 0;
        bool hostileToParty = false;
        std::string monsterFamilyName;
        std::string representativePictureName;
    };

    using TimerState = ScriptedEventTimerState;

    struct AudioEvent
    {
        SoundScope soundScope = SoundScope::Engine;
        uint32_t soundId = 0;
        uint32_t sourceId = 0;
        std::string reason;
        std::optional<size_t> actorIndex;
        float pitch = 1.0f;
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        bool positional = true;
    };

    struct ArmageddonState
    {
        float remainingSeconds = 0.0f;
        uint32_t skillLevel = 0;
        SkillMastery skillMastery = SkillMastery::None;
        uint32_t casterMemberIndex = 0;
        uint32_t shakeStepsRemaining = 0;
        uint32_t shakeSequence = 0;
        float cameraShakeYawRadians = 0.0f;
        float cameraShakePitchRadians = 0.0f;

        bool active() const
        {
            return remainingSeconds > 0.0f;
        }
    };

    struct BloodSplatState
    {
        struct Vertex
        {
            float x = 0.0f;
            float y = 0.0f;
            float z = 0.0f;
            float u = 0.0f;
            float v = 0.0f;
        };

        uint32_t sourceActorId = 0;
        float x = 0.0f;
        float y = 0.0f;
        float z = 0.0f;
        float radius = 0.0f;
        std::vector<Vertex> vertices;
    };

    struct Snapshot
    {
        float gameMinutes = 0.0f;
        MapDeltaLocationInfo locationInfo = {};
        MapDeltaLocationTime locationTime = {};
        bool hasLocationTime = false;
        AtmosphereState atmosphere = {};
        std::vector<TimerState> timers;
        std::vector<MapActorState> mapActors;
        std::vector<MapDeltaChest> chests;
        std::vector<uint8_t> openedChestFlags;
        std::vector<std::optional<ChestViewState>> materializedChestViews;
        std::optional<ChestViewState> activeChestView;
        std::optional<EventRuntimeState> eventRuntimeState;
        float actorUpdateAccumulatorSeconds = 0.0f;
        uint32_t sessionChestSeed = 0;
        uint32_t nextActorId = 0;
        std::vector<std::optional<CorpseViewState>> mapActorCorpseViews;
        std::vector<std::optional<CorpseViewState>> mapActorRevealedLoot;
        std::optional<CorpseViewState> activeCorpseView;
        std::vector<WorldItemState> worldItems;
        uint32_t nextWorldItemId = 1;
        uint32_t nextProjectileId = 1;
        uint32_t nextProjectileImpactId = 1;
        uint32_t nextFireSpikeTrapId = 1;
        float gameplayOverlayRemainingSeconds = 0.0f;
        float gameplayOverlayDurationSeconds = 0.0f;
        float gameplayOverlayPeakAlpha = 0.0f;
        uint32_t gameplayOverlayColorAbgr = 0x00000000u;
        std::vector<ProjectileState> projectiles;
        std::vector<ProjectileImpactState> projectileImpacts;
        std::vector<FireSpikeTrapState> fireSpikeTraps;
        std::vector<BloodSplatState> bloodSplats;
        ArmageddonState armageddon = {};
        std::vector<uint8_t> fullyRevealedCells;
        std::vector<uint8_t> partiallyRevealedCells;
        std::vector<uint32_t> faceAttributes;
        std::vector<std::string> searchedLootPropSourceIds;
        ActorBehaviorRuntime::Snapshot actorBehaviors;
        bool hasOutdoorRuntimeSaveParityFields = false;
    };

    void initialize(
        const MapStatsEntry &map,
        const MonsterTable &monsterTable,
        const MonsterProjectileTable &monsterProjectileTable,
        const ObjectTable &objectTable,
        const SpellTable &spellTable,
        const ItemTable &itemTable,
        Party *pParty,
        OutdoorPartyRuntime *pPartyRuntime,
        const StandardItemEnchantTable &standardItemEnchantTable,
        const SpecialItemEnchantTable &specialItemEnchantTable,
        const ChestTable *pChestTable,
        const std::optional<OutdoorMapData> &outdoorMapData,
        const std::optional<MapDeltaData> &outdoorMapDeltaData,
        const std::optional<OutdoorWeatherProfile> &outdoorWeatherProfile,
        const std::optional<EventRuntimeState> &eventRuntimeState,
        const std::optional<ActorPreviewBillboardSet> &outdoorActorPreviewBillboardSet = std::nullopt,
        const std::optional<std::vector<uint8_t>> &outdoorLandMask = std::nullopt,
        const std::optional<OutdoorDecorationCollisionSet> &outdoorDecorationCollisionSet = std::nullopt,
        const std::optional<OutdoorActorCollisionSet> &outdoorActorCollisionSet = std::nullopt,
        const std::optional<OutdoorSpriteObjectCollisionSet> &outdoorSpriteObjectCollisionSet = std::nullopt,
        const std::optional<SpriteObjectBillboardSet> &outdoorSpriteObjectBillboardSet = std::nullopt,
        GameplayActorService *pGameplayActorService = nullptr,
        GameplayProjectileService *pGameplayProjectileService = nullptr,
        GameplayCombatController *pGameplayCombatController = nullptr,
        GameplayFxService *pGameplayFxService = nullptr,
        const MergedBolsterMapTable *pMergedBolsterMapTable = nullptr,
        const MergedBolsterMonsterTable *pMergedBolsterMonsterTable = nullptr,
        const MapItemSourceData *pItemSourceData = nullptr
    );

    bool isInitialized() const;
    // Per map entity: whether the decoration is hidden now (evt.SetSprite, the map's invisible flag, a cleared
    // interactive decoration); hidden decorations neither draw nor collide.
    std::vector<bool> hiddenDecorationEntities() const;
    // Recomputes hiddenDecorationEntities for this frame's actor movement and returns it.
    const std::vector<bool> &refreshHiddenDecorationEntities();
    void setBolsterMonstersEnabled(bool enabled);
    void setPartyCollisionDimensions(float radius, float height);
    void bindInteractionView(OutdoorGameView *pView);
    void bindGlobalEventProgram(const std::optional<ScriptedEventProgram> *pGlobalEventProgram);
    void bindActorBehaviorCatalog(const ActorBehaviorCatalog *pCatalog);
    ActorBehaviorRuntime *actorBehaviorRuntime() override;
    const ActorBehaviorRuntime *actorBehaviorRuntime() const override;
    GameplayActorShields *actorShields() override
    {
        return &m_actorShields;
    }
    const GameplayActorShields *actorShields() const override
    {
        return &m_actorShields;
    }
    bool stunActor(size_t actorIndex, float seconds) override;
    bool debuffActor(size_t actorIndex, GameplayActorHitDebuff debuff, float seconds, float power) override;
    bool setMapActorBehavior(size_t actorIndex, const std::string &behaviorId) override;
    bool triggerMapActor(size_t actorIndex, const std::string &message) override;

    struct MonsterKilledEvent
    {
        uint32_t actorIndex = 0;
        uint32_t monsterId = 0;
    };

    void setMonsterKilledHooksEnabled(bool enabled);
    std::vector<MonsterKilledEvent> drainMonsterKilledEvents();
    int mapId() const;
    const std::string &mapName() const override;
    const MonsterTable *monsterTable() const override;
    const MergedBolsterMonsterTable *mergedBolsterMonsterTable() const override;
    GameplayWorldPoint chooseBountyHuntSpawnPoint(uint32_t seed) const override;
    bool isIndoorMap() const override;
    bool isUnderwaterMap() const override;
    bool allowsLloydsBeacon() const override;
    bool allowsRest() const override;
    Snapshot snapshot() const;
    void restoreSnapshot(const Snapshot &snapshot);
    void stampLastVisitTime();
    void applyMapReentryReset() override;
    void refreshRulesetMonsters() override;
    float currentGameMinutes() const override;
    float gameMinutes() const override;
    int currentHour() const override;
    int currentLocationReputation() const override;
    void setCurrentLocationReputation(int reputation) override;
    const OutdoorMapData *mapData() const;
    const AtmosphereState &atmosphereState() const;
    void setDebugSkyOverrides(const DebugSkyOverrides &overrides);
    const DebugSkyOverrides &debugSkyOverrides() const;
    // The weather rules this map uses, and its rolled weather (no event or debug overrides) at a game time.
    const WeatherRules &weatherRules() const;
    // The map's weather.yml settings (chances, ash look, dry lightning, rain colour).
    WeatherMapSettings weatherMapSettings() const;
    WeatherSample rolledWeatherAt(double gameMinutes) const;
    void advanceGameMinutes(float minutes) override;
    void updateMapActors(float deltaSeconds, float partyX, float partyY, float partyZ);
    void updateMm9FoundPlayerEvents(float deltaSeconds, float partyX, float partyY, float partyZ);
    void queueActorAiUpdate(float deltaSeconds, float partyX, float partyY, float partyZ);
    void setOutdoorPathfindingSettings(bool enabled, bool logEnabled);

    void applyEventRuntimeState(bool syncPersistentHostilityMasks = false) override;
    void prepareTimers(
        const std::optional<ScriptedEventProgram> &localEventProgram,
        const std::optional<ScriptedEventProgram> &globalEventProgram
    );
    bool updateTimers(
        float deltaSeconds,
        const EventRuntime &eventRuntime,
        const std::optional<ScriptedEventProgram> &localEventProgram,
        const std::optional<ScriptedEventProgram> &globalEventProgram,
        GameplayWorldMovementFrameDiagnostics *pPerformanceDiagnostics = nullptr
    );
    bool isChestOpened(uint32_t chestId) const;
    size_t mapActorCount() const override;
    bool actorRuntimeState(size_t actorIndex, GameplayRuntimeActorState &state) const override;
    bool actorRulesView(size_t actorIndex, GameplayActorRulesView &view) const override;
    GameplayActorHitFeedback &actorHitFeedback() override
    {
        return m_actorHitFeedback;
    }
    const GameplayActorHitFeedback &actorHitFeedback() const override
    {
        return m_actorHitFeedback;
    }
    std::optional<uint32_t> corpseLootValue(size_t actorIndex) const override;
    std::optional<CorpseViewState> revealActorLoot(size_t actorIndex) override;
    bool setMapActorPosition(size_t actorIndex, float x, float y, float z) override;
    bool isMapActorHostile(size_t actorIndex) const override;
    bool isMapActorWithinPartyDistance(size_t actorIndex, float distance) const override;
    bool searchLootProp(const std::string &sourceId) override;
    bool useMm9Barrel(const std::string &sourceId) override;
    bool useMm9BarrelEvent(uint16_t eventId) override;
    bool spawnLootContainer(const std::string &sourceId) override;
    bool consumeWorldItem(const std::string &sourceId) override;
    bool setPersistentItemMechanismState(
        const std::string &sourceId,
        bool visible,
        bool solid) override;
    bool setPersistentItemMechanismVariant(
        const std::string &sourceId,
        uint32_t variantIndex) override;
    bool tryStealFromActor(size_t actorIndex, uint32_t successRoll, uint32_t caughtRoll) override;
    bool actorInspectState(
        size_t actorIndex,
        uint32_t animationTicks,
        GameplayActorInspectState &state) const override;
    std::optional<GameplayCombatActorInfo> combatActorInfoById(uint32_t actorId) const override;
    bool applyReflectedDamageToActor(
        uint32_t actorId,
        int damage,
        CombatDamageType damageType,
        uint32_t sourcePartyMemberIndex) override;
    const MapActorState *mapActorState(size_t actorIndex) const;
    std::optional<GameplayWorldPoint> partyAttackFallbackProjectionPoint(size_t actorIndex) const;
    std::optional<GameplayPartyAttackActorFacts> partyAttackActorFacts(
        size_t actorIndex,
        bool visibleForFallback) const override;
    bool partyAttackActorHasLineOfSight(size_t actorIndex) const;
    std::vector<GameplayPartyAttackActorFacts> collectPartyAttackFallbackActors(
        const GameplayPartyAttackFallbackQuery &query) const override;
    std::optional<GameplayWorldPoint> partyAttackActorContactPoint(
        size_t actorIndex,
        const GameplayPartyAttackFallbackQuery &query) const override;
    std::optional<ActorDecisionDebugInfo> debugActorDecisionInfo(
        size_t actorIndex,
        float partyX,
        float partyY,
        float partyZ
    ) const;
    bool debugActorPathfindingActive(size_t actorIndex) const;
    bool debugActorPathfindingPending(size_t actorIndex) const;
    bool debugSpawnMapActorProjectile(
        size_t actorIndex,
        MonsterAttackAbility ability,
        float targetX,
        float targetY,
        float targetZ);
    bool debugSpawnEncounterFromSpawnPoint(size_t spawnIndex, uint32_t countOverride = 0);
    bool setMapActorDead(size_t actorIndex, bool isDead, bool emitAudio = true);
    bool applyPartyAttackToMapActor(size_t actorIndex, int damage, float partyX, float partyY, float partyZ,
        ShieldAttackTier shieldTier = ShieldAttackTier::Physical, const ShieldHitModifiers &shieldModifiers = {});
    bool applyPartyAttackMeleeDamage(
        size_t actorIndex,
        int damage,
        const GameplayWorldPoint &source,
        ShieldAttackTier shieldTier,
        const ShieldHitModifiers &shieldModifiers = {}) override;
    void applyPartyAttackMeleeEffects(
        size_t actorIndex,
        const CharacterAttackResult &attack,
        const GameplayWorldPoint &source) override;
    bool spawnPartyAttackProjectile(const GameplayPartyAttackProjectileRequest &request) override;
    bool castPartyAttackSpell(const GameplayPartyAttackSpellRequest &request) override;
    std::vector<GameplayCombatFeedbackEvent> drainCombatFeedbackEvents() override;
    void recordPartyAttackWorldResult(
        std::optional<size_t> actorIndex,
        bool attacked,
        bool actionPerformed) override;
    bool worldInteractionReady() const override;
    bool worldInspectModeActive() const override;
    GameplayWorldPickRequest buildWorldPickRequest(const GameplayWorldPickRequestInput &input) const override;
    std::optional<GameplayHeldItemDropRequest> buildHeldItemDropRequest() const override;
    GameplayPartyAttackFrameInput buildPartyAttackFrameInput(
        const GameplayWorldPickRequest &pickRequest) const override;
    std::optional<size_t> spellActionHoveredActorIndex() const override;
    std::vector<size_t> spellActionVisibleHostileActorIndices() const override;
    std::optional<bx::Vec3> spellActionActorTargetPoint(size_t actorIndex) const override;
    std::optional<bx::Vec3> spellActionGroundTargetPoint(float screenX, float screenY) const override;
    bool applyPartySpellToActor(
        size_t actorIndex,
        uint32_t spellId,
        uint32_t skillLevel,
        SkillMastery skillMastery,
        int damage,
        float partyX,
        float partyY,
        float partyZ,
        uint32_t sourcePartyMemberIndex = 0,
        bool critical = false) override;
    bool applyPartySpellToMapActor(
        size_t actorIndex,
        uint32_t spellId,
        uint32_t skillLevel,
        SkillMastery skillMastery,
        int damage,
        float partyX,
        float partyY,
        float partyZ,
        uint32_t sourcePartyMemberIndex = 0,
        bool critical = false);
    bool applyDirectSpellImpactToMapActor(
        size_t actorIndex,
        uint32_t spellId,
        float partyX,
        float partyY,
        float partyZ,
        uint32_t sourcePartyMemberIndex,
        const GameplayActorService::DirectSpellImpactResult &impact,
        bool critical = false);
    bool healMapActor(size_t actorIndex, int amount) override;
    ActorRulesetFacts *mutableActorRulesetFacts(size_t actorIndex) override;
    bool resurrectMapActor(size_t actorIndex, int health, bool friendlyToParty);
    bool clearMapActorSpellEffects(size_t actorIndex);
    int effectiveMapActorArmorClass(size_t actorIndex) const;
    std::vector<size_t> collectMapActorIndicesWithinRadius(
        float centerX,
        float centerY,
        float centerZ,
        float radius,
        bool requireLineOfSight,
        float sourceX,
        float sourceY,
        float sourceZ) const override;
    std::vector<size_t> collectVisibleMapActorIndicesWithinRadius(
        float centerX,
        float centerY,
        float centerZ,
        float radius,
        float sourceX,
        float sourceY,
        float sourceZ,
        float viewX,
        float viewY,
        float viewZ,
        float viewYawRadians,
        float viewPitchRadians,
        float viewAspectRatio) const override;
    bool faceMapActorTowardPoint(size_t actorIndex, float targetX, float targetY);
    // The party talks to an actor: it faces the party (faceMapActorTowardPoint) and an MM9 one keeps the facing it
    // turns back to afterwards (ActorMm9State::beginTalk).
    bool faceMapActorForTalk(size_t actorIndex, float partyX, float partyY);
    bool notifyPartyContactWithMapActor(size_t actorIndex, float partyX, float partyY, float partyZ);
    float sampleSupportFloorHeight(float x, float y, float z, float maxRise, float xySlack) const;
    size_t spawnPointCount() const;
    const SpawnPointState *spawnPointState(size_t spawnIndex) const;
    size_t chestCount() const;
    size_t openedChestCount() const;
    void setPendingEventSourcePoint(std::optional<GameplayWorldPoint> point);
    ChestViewState *activeChestView() override;
    const ChestViewState *activeChestView() const override;
    void commitActiveChestView() override;
    bool takeActiveChestItem(size_t itemIndex, ChestItemState &item) override;
    bool takeActiveChestItemAt(uint8_t gridX, uint8_t gridY, ChestItemState &item) override;
    bool tryPlaceActiveChestItemAt(const ChestItemState &item, uint8_t gridX, uint8_t gridY) override;
    void closeActiveChestView() override;
    CorpseViewState *activeCorpseView() override;
    const CorpseViewState *activeCorpseView() const override;
    void commitActiveCorpseView() override;
    // Rolls the actor's corpse loot once (at death, before a steal, or after loading) into its corpse view.
    bool ensureMapActorCorpseView(size_t actorIndex);
    std::vector<uint32_t> mapActorGuaranteedItemIds(size_t actorIndex) const;
    // What the actor carries as the rules size it; nothing for an actor without random loot.
    CorpseLoot mapActorCorpseLoot(
        size_t actorIndex,
        const MonsterTable::MonsterStatsEntry &stats,
        CorpseLootPart part = CorpseLootPart::All) const;
    // After a load: dead actors whose corpse loot was never rolled (older saves, map deltas) get it on the first update,
    // once the event state that adds guaranteed items is bound.
    void rollPendingCorpseLoot();
    // An actor whose HP reached 0: its dying animation, killed event, corpse physics, drops and death blast.
    void beginOutdoorActorDeath(size_t actorIndex);
    void detonatePendingDeathExplosions();
    bool openMapActorCorpseView(size_t actorIndex);
    bool takeActiveCorpseItem(size_t itemIndex, ChestItemState &item) override;
    void closeActiveCorpseView() override;
    // On the ground a little ahead of the party and in its sight (LootGatherDistances), else at its feet.
    bx::Vec3 lootGatherSpot() const;
    const std::vector<AudioEvent> &pendingAudioEvents() const;
    void clearPendingAudioEvents();
    const std::vector<CombatEvent> &pendingCombatEvents() const;
    void clearPendingCombatEvents();
    size_t worldItemCount() const;
    const WorldItemState *worldItemState(size_t worldItemIndex) const;
    WorldItemState *worldItemStateMutable(size_t worldItemIndex);
    bool takeWorldItem(size_t worldItemIndex, WorldItemState &item);
    bool hasCustomWorldItemActivation(size_t worldItemIndex) const override;
    bool activateCustomWorldItem(size_t worldItemIndex) override;
    bool isSemanticWorldItem(size_t worldItemIndex) const;
    bool activateSemanticWorldItem(size_t worldItemIndex);
    bool activateSemanticLootContainer(size_t worldItemIndex);
    bool spawnWorldItem(
        const InventoryItem &item,
        float sourceX,
        float sourceY,
        float sourceZ,
        float yawRadians
    );
    void collectWorldItemPresentationStates(
        std::vector<GameplayWorldItemPresentationState> &items) const override;
    // The model a world item is drawn and picked with: a loot container is a bag of loot, not one of the items.
    static const ItemModelBinding &worldItemModel(const ItemTable &itemTable, const WorldItemState &worldItem);
    void collectFireSpikeTrapPresentationStates(
        std::vector<GameplayProjectilePresentationState> &traps) const override;
    bool spawnPartyFireSpikeTrap(
        uint32_t casterMemberIndex,
        uint32_t spellId,
        uint32_t skillLevel,
        uint32_t skillMastery,
        float x,
        float y,
        float z) override;
    size_t projectileCount() const;
    const ProjectileState *projectileState(size_t projectileIndex) const;
    size_t projectileImpactCount() const;
    const ProjectileImpactState *projectileImpactState(size_t effectIndex) const;
    void startGameplayScreenOverlay(uint32_t colorAbgr, float durationSeconds, float peakAlpha);
    bool tryStartArmageddon(
        size_t casterMemberIndex,
        uint32_t skillLevel,
        SkillMastery skillMastery,
        std::string &failureText) override;
    bool canActivateWorldHit(
        const GameplayWorldHit &hit,
        GameplayInteractionMethod interactionMethod) const override;
    bool activateWorldHit(const GameplayWorldHit &hit) override;
    bool activateWorldHitFromSpell(const GameplayWorldHit &hit, uint32_t spellId) override;
    bool canActivateTelekinesisTarget(const GameplayWorldHit &hit) const override;
    bool activateTelekinesisTarget(const GameplayWorldHit &hit) override;
    GameplayPendingSpellWorldTargetFacts pickPendingSpellWorldTarget(
        const GameplayWorldPickRequest &request) override;
    GameplayWorldHit pickKeyboardInteractionTarget(const GameplayWorldPickRequest &request) override;
    GameplayWorldHit pickHeldItemWorldTarget(const GameplayWorldPickRequest &request) override;
    GameplayWorldHit pickMouseInteractionTarget(const GameplayWorldPickRequest &request) override;
    GameplayWorldHit pickPartyAttackTarget(const GameplayWorldPickRequest &request) override;
    bool worldItemInspectState(size_t worldItemIndex, GameplayWorldItemInspectState &state) const override;
    bool updateWorldItemInspectState(size_t worldItemIndex, const InventoryItem &item) override;
    bool takeWorldItemInspectState(size_t worldItemIndex, GameplayWorldItemInspectState &state) override;
    GameplayWorldHoverCacheState worldHoverCacheState() const override;
    GameplayHoverStatusPayload refreshWorldHover(const GameplayWorldHoverRequest &request) override;
    GameplayHoverStatusPayload readCachedWorldHover() override;
    void clearWorldHover() override;
    bool canUseHeldItemOnWorld(const GameplayWorldHit &hit) const override;
    bool useHeldItemOnWorld(const GameplayWorldHit &hit) override;
    void applyPendingSpellCastWorldEffects(const PartySpellCastResult &castResult) override;
    bool dropHeldItemToWorld(const GameplayHeldItemDropRequest &request) override;
    bool tryGetGameplayMinimapState(GameplayMinimapState &state) const override;
    void collectGameplayMinimapLines(std::vector<GameplayMinimapLineState> &lines) override;
    void collectGameplayMinimapMarkers(std::vector<GameplayMinimapMarkerState> &markers) const override;
    bool isArmageddonActive() const;
    float armageddonCameraShakeYawRadians() const;
    float armageddonCameraShakePitchRadians() const;

    const EventRuntimeState::PendingMapMove *pendingMapMove() const;
    std::optional<EventRuntimeState::PendingMapMove> consumePendingMapMove();

    Party *party() override;
    const Party *party() const override;
    const std::vector<uint8_t> *journalMapFullyRevealedCells() const override;
    const std::vector<uint8_t> *journalMapPartiallyRevealedCells() const override;
    int restFoodRequired() const override;
    float partyX() const override;
    float partyY() const override;
    float partyFootZ() const override;
    void teleportParty(float x, float y, float footZ) override;
    float partyEyeZ() const override;
    float partyEngagementRange() const override;
    float gameplayCameraYawRadians() const override;
    float gameplayCameraPitchRadians() const override;
    float gameplayViewAspectRatio() const override;
    bool partyIsAirborneForRest() const override;
    bool partyIsFlyingForEventChecks() const override;
    bool partyIsActivelyFlyingForHud() const override;
    bool partyNeedsTurnBasedPhysicsUpdate() const override;
    void syncSpellMovementStatesFromPartyBuffs() override;
    void requestPartyJump(float verticalVelocity = 0.0f, float lift = 1.0f) override;
    bool specialJump(uint32_t encodedHorizontalVelocity, uint32_t verticalVelocity) override;
    void setAlwaysRunEnabled(bool enabled) override;
    void updateWorldMovement(
        const GameplayInputFrame &input,
        float deltaSeconds,
        bool allowWorldInput) override;
    const GameplayWorldMovementFrameDiagnostics *lastWorldMovementFrameDiagnostics() const override;
    void updateActorAi(float deltaSeconds) override;
    void updateTurnBasedPausedActorAnimations(float deltaSeconds) override;
    size_t turnBasedPendingWorldActionCount() const override;
    void scareNearbyPeasants(float radius, float seconds) override;
    bool turnBasedActorActionInProgress() const override;
    void stopTurnBasedActorMovement() override;
    void setTurnBasedActorMode(ActorTurnBasedMode mode) override;
    void grantTurnBasedActorAction(size_t actorIndex) override;
    bool turnBasedActorActionGrantPending() const override;
    int turnBasedActorRecoveryTicks(size_t actorIndex) const override;
    void setActorAttackCooldownSeconds(size_t actorIndex, float seconds) override;
    void updateWorld(float deltaSeconds) override;
    void renderWorld(
        int width,
        int height,
        const GameplayInputFrame &input,
        float deltaSeconds) override;
    GameplayWorldUiRenderState gameplayUiRenderState(int width, int height) const override;
    bool requestTravelAutosave() override;
    void presentPendingEventDialog(size_t previousMessageCount, bool allowNpcFallbackContent);
    void handleDialogueCloseRequest();
    void executeActiveDialogAction();
    void openDebugNpcDialogue(uint32_t npcId);
    void applyGrantedEventItemsToHeldInventory();
    bool tryTriggerLocalEventById(uint16_t eventId);
    void cancelPendingMapTransition() override;
    bool executeNpcTopicEvent(
        uint16_t eventId,
        size_t &previousMessageCount,
        std::optional<uint8_t> continueStep = std::nullopt) override;
    bool executeMapEvent(
        uint16_t eventId,
        size_t &previousMessageCount,
        std::optional<uint8_t> continueStep = std::nullopt) override;
    bool executeEventHooks(EventRuntimeHookKind kind) override;
    const std::optional<ScriptedEventProgram> *globalEventProgram() const override;
    const MapDeltaData *mapDeltaData() const override;
    MapDeltaData *mapDeltaData() override;
    bool setFacetBit(uint32_t cogNumber, uint32_t bit, bool isOn) override;
    bool registerOutdoorModelMechanism(
        uint32_t mechanismId,
        const std::string &modelName,
        int32_t dx,
        int32_t dy,
        int32_t dz,
        uint32_t moveTimeMs,
        bool closed,
        bool moveParty) override;
    EventRuntimeState *eventRuntimeState() override;
    const EventRuntimeState *eventRuntimeState() const override;
    // evt.DamageDestructible and the rest (ISceneEventContext): an outdoor destructible by its source object index.
    bool damageDestructible(uint32_t id, int damage) override;
    bool destroyDestructible(uint32_t id) override;
    bool setDestructibleDamageEnabled(uint32_t id, bool enabled) override;
    bool damageOutdoorDestructible(uint32_t sourceObjectIndex, int damage);
    bool destroyOutdoorDestructible(uint32_t sourceObjectIndex, bool playEffects = true);
    const RuntimeDestructibleState *outdoorDestructibleState(uint32_t sourceObjectIndex) const;
    bool applyPartyAttackMeleeBModelDamage(size_t bModelIndex, int damage) override;
    bool isPartyAttackMeleeBModelTarget(size_t bModelIndex) const override;
    bool isOutdoorDestructibleBModel(size_t bModelIndex) const;
    bool fireEventMissile(const EventMissileRequest &request) override;
    bool turnMapActors(std::optional<size_t> actorIndex, uint32_t group, float seconds) override;
    bool wakeMapActors(std::optional<size_t> actorIndex, uint32_t group) override;
    bool hasLineOfSight(float fromX, float fromY, float fromZ, float toX, float toY, float toZ) const override;
    bool summonEventGold(uint32_t amount, int32_t x, int32_t y, int32_t z, int32_t speed) override;
    bool mapActorPosition(size_t actorIndex, float &x, float &y, float &z) const override;
    bool castEventSpell(
        uint32_t spellId,
        uint32_t skillLevel,
        uint32_t skillMastery,
        int32_t fromX,
        int32_t fromY,
        int32_t fromZ,
        int32_t toX,
        int32_t toY,
        int32_t toZ
    ) override;
    bool castPartySpell(const SpellCastRequest &request);
    bool castPartySpellProjectile(const GameplayPartySpellProjectileRequest &request) override;
    bool spawnPartyProjectile(const PartyProjectileRequest &request);
    bool summonMonsters(
        uint32_t typeIndexInMapStats,
        uint32_t level,
        uint32_t count,
        int32_t x,
        int32_t y,
        int32_t z,
        uint32_t group,
        uint32_t uniqueNameId
    ) override;
    bool summonEventItem(
        uint32_t itemId,
        int32_t x,
        int32_t y,
        int32_t z,
        int32_t speed,
        uint32_t count,
        bool randomRotate
    ) override;
    bool summonEventInventoryItem(
        const InventoryItem &item,
        int32_t x,
        int32_t y,
        int32_t z,
        int32_t speed,
        bool randomRotate
    ) override;
    bool summonEventObject(
        uint32_t objectId,
        int32_t x,
        int32_t y,
        int32_t z,
        int32_t speed,
        uint32_t count,
        bool randomRotate
    ) override;
    bool summonFriendlyMonsterById(
        int16_t monsterId,
        uint32_t count,
        float durationSeconds,
        float x,
        float y,
        float z,
        int32_t summonerMemberIndex) override;
    bool debugFireActorProjectile(
        size_t actorIndex,
        GameplayActorAttackAbility ability,
        const GameplayWorldPoint &target) override;
    bool debugFireActorProjectileAtParty(size_t actorIndex, GameplayActorAttackAbility ability, int damage) override;
    bool blinkActor(size_t actorIndex) override;
    bool suspendActorShield(size_t actorIndex, float seconds) override;
    bool restoreActorShield(size_t actorIndex) override;
    bool swapActorPlaces(size_t actorIndex, std::optional<size_t> otherActorIndex) override;
    bool pushActor(size_t actorIndex, float directionX, float directionY, float distance) override;
    bool launchParty(float headingRadians, float horizontalSpeed, float verticalSpeed) override;
    bool liftParty(float height) override;
    bool dashParty(float directionX, float directionY, float distance) override;
    size_t gatherCorpsesToParty(size_t maxCount) override;
    size_t gatherWorldItemsToParty(size_t maxCount, const std::function<bool(const InventoryItem &)> &gathers) override;
    std::vector<size_t> lootableCorpseActorIndices() const override;
    bool openActorCorpseView(size_t actorIndex) override;
    const GameplayProjectileService *projectileServiceView() const override
    {
        return &projectileService();
    }
    bool chargeActor(size_t actorIndex) override;
    bool frenzyActor(size_t actorIndex) override;
    std::optional<GameplayChargeCounts> chargeCounts() const override;
    // Moves a living actor to (x, y) for a blink or a charge's step when the spot is free: a floor within
    // maxHeightChange of its own (no water or steep slope for walkers), no wall, decoration, other actor or the party
    // in its cylinder, and a clear line from where it stands; with keepSightOf also a clear line from there to that
    // point. pBlockedByParty (optional) tells that the party's cylinder was in the way.
    bool blinkMapActorTo(size_t actorIndex, float x, float y, float maxHeightChange,
        const std::optional<std::array<float, 3>> &keepSightOf = std::nullopt, bool *pBlockedByParty = nullptr);
    // Stands an actor at a point without any checks, still and keeping its home (swaps, the gather key).
    void placeMapActor(size_t actorIndex, float x, float y, float z);
    // Where a living actor could stand at (x, y), its feet's height there: the blink's checks without the move
    // (blinkMapActorTo). The sight line to keepSightOf starts at its eye eyeBelowTop under the top of its body (MM9's
    // eye; none: 70 % of its height); pSightChecks (optional) counts the sight lines tested.
    std::optional<float> checkMapActorSpot(size_t actorIndex, float x, float y, float maxHeightChange,
        const std::optional<std::array<float, 3>> &keepSightOf, bool *pBlockedByParty,
        std::optional<float> eyeBelowTop, int *pSightChecks);
    bool mapKillProgress(MapKillProgress &progress) const override;
    std::vector<size_t> spawnMonsters(const GameplayMonsterSpawnRequest &request) override;
    void bindActorAiTrace(ActorAiTrace *pTrace) override;
    const ActorAiTrace *actorAiTrace() const override;
    bool summonHostileMonsterById(
        int16_t monsterId,
        uint32_t count,
        float x,
        float y,
        float z,
        uint32_t group
    ) override;
    void setWorldFxSystem(WorldFxSystem *pWorldFxSystem);
    bool checkMonstersKilled(uint32_t checkType, uint32_t id, uint32_t count, bool invisibleAsDead) const override;

public:
    struct ResolvedProjectileDefinition
    {
        uint16_t objectDescriptionId = 0;
        uint16_t objectSpriteId = 0;
        uint16_t impactObjectDescriptionId = 0;
        uint16_t impactObjectSpriteId = 0;
        uint16_t objectFlags = 0;
        GameplayProjectileVisualMode visualMode = GameplayProjectileVisualMode::SpriteBillboard;
        uint16_t radius = 0;
        uint16_t height = 0;
        uint32_t lifetimeTicks = 0;
        float speed = 0.0f;
        int spellId = 0;
        int effectSoundId = 0;
        std::string objectName;
        std::string objectSpriteName;
        std::string impactObjectName;
        std::string impactObjectSpriteName;
        // A world missile's shield tier (monster_projectiles.yml); unset follows the attack's damage type.
        std::optional<ShieldAttackTier> shieldTier;
        // Its impact's sound (monster_projectiles.yml impact_sound_id), 0: none.
        uint32_t impactSoundId = 0;
    };

    enum class RuntimeSpellSourceKind
    {
        Actor,
        Event,
        Party,
    };

    struct SpellCastRequest
    {
        RuntimeSpellSourceKind sourceKind = RuntimeSpellSourceKind::Event;
        uint32_t sourceId = 0;
        int16_t sourceMonsterId = 0;
        bool fromSummonedMonster = false;
        MonsterAttackAbility ability = MonsterAttackAbility::Spell1;
        uint32_t spellId = 0;
        uint32_t skillLevel = 0;
        uint32_t skillMastery = 0;
        uint32_t sourcePartyMemberIndex = 0;
        int damage = 0;
        int attackBonus = 0;
        bool useActorHitChance = false;
        CombatDamageType damageType = CombatDamageType::Physical;
        float sourceX = 0.0f;
        float sourceY = 0.0f;
        float sourceZ = 0.0f;
        float targetX = 0.0f;
        float targetY = 0.0f;
        float targetZ = 0.0f;
        uint32_t effectSoundIdOverride = 0;
        uint32_t impactSoundIdOverride = 0;
        bool turnBasedPendingAction = false;
        // A party spell whose damage was a critical hit (ProjectileState::critical).
        bool critical = false;
    };

    struct PartyProjectileRequest
    {
        uint32_t sourcePartyMemberIndex = 0;
        uint32_t objectId = 0;
        uint32_t impactObjectId = 0;
        uint32_t impactSoundId = 0;
        int damage = 0;
        int attackBonus = 0;
        bool useActorHitChance = false;
        CombatDamageType damageType = CombatDamageType::Physical;
        std::optional<ShieldAttackTier> shieldTier;
        ShieldHitModifiers shieldModifiers;
        bool weakerOfPhysicalAndFire = false;
        float explosionRadius = 0.0f;
        float sourceX = 0.0f;
        float sourceY = 0.0f;
        float sourceZ = 0.0f;
        float targetX = 0.0f;
        float targetY = 0.0f;
        float targetZ = 0.0f;
        bool turnBasedPendingAction = false;
        // Its damage was a critical hit (ProjectileState::critical).
        bool critical = false;
    };

    struct MonsterVisualState
    {
        uint16_t spriteFrameIndex = 0;
        std::array<uint16_t, 8> actionSpriteFrameIndices = {};
        bool useStaticFrame = false;
    };

    void collectOutdoorFaceCandidates(
        float minX,
        float minY,
        float maxX,
        float maxY,
        std::vector<size_t> &indices) const;
    const OutdoorFaceGeometryData *outdoorFace(size_t faceIndex) const;
    bool hasClearOutdoorLineOfSight(
        const bx::Vec3 &start, const bx::Vec3 &end, bool includeWalkableFaces = false) const;
    size_t bloodSplatCount() const;
    const BloodSplatState *bloodSplatState(size_t splatIndex) const;
    uint64_t bloodSplatRevision() const;

private:
    MonsterKillReward killReward(const MapActorState &actor, const MonsterTable::MonsterStatsEntry &stats) const;
    // After a kill: the ruleset's reward for clearing the map, if it has one.
    void rewardRulesetMapProgress();
    // Homing for the missiles a party member just fired at an actor, when the rules make them home (MAW).
    // The ruleset's homing (MAW), or a weapon's (weaponHoming: an Energy Guns Grandmaster's shot, 360 degrees a second
    // for 1.5 s).
    void attachPartyMissileHoming(
        uint32_t firstProjectileId,
        uint32_t sourcePartyMemberIndex,
        std::optional<size_t> targetActorIndex,
        bool weaponHoming = false);
    GameplayBolsterRuntimeContext monsterRulesContext() const;
    // The ruleset's map-wide choices when the map's monsters are first placed (MAW bosses).
    void placeRulesetMapMonsters();
    void refreshRulesetMonster(MapActorState &actor);
    bool summonEventPayload(
        uint32_t payloadId,
        bool payloadIsObjectId,
        int32_t x,
        int32_t y,
        int32_t z,
        int32_t speed,
        uint32_t count,
        bool randomRotate
    );

    bool applyMonsterActorMeleeAttackToMapActor(
        size_t actorIndex,
        int damage,
        uint32_t sourceActorId,
        int attackBonus,
        CombatDamageType damageType);
    bool applyMonsterAttackToMapActor(
        size_t actorIndex,
        int damage,
        uint32_t sourceActorId,
        ShieldAttackTier shieldTier,
        bool emitAudio = true,
        bool allowZeroDamageHit = false);
    // Energy shields: regeneration and presentation per actor step, and the QBit-switched relations of the world
    // add-on (MonsterRelationAddOns) applied to the map's actors whenever they change and after every load.
    void updateActorShields(float deltaSeconds);
    void refreshConditionalMonsterRelations();
    // A hit through the actor's shield (GameplayActorShields::applyHit), the ripple at the source's side of the body.
    GameplayActorShieldHit applyActorShieldHit(size_t actorIndex, int damage, ShieldAttackTier shieldTier,
        float sourceX, float sourceY, float sourceZ, const ShieldHitModifiers &shieldModifiers = {});
    // Monster modifiers (MonsterModifiers): blinks per actor step, a true_aim monster's shots, never_staggers.
    void updateActorModifiers(float deltaSeconds);
    bool blinkMapActor(const GameplayActorModifiers::BlinkRequest &request);
    // Charges (GameplayActorModifiers) per fixed actor step after the AI, and what a charge does in this world.
    void updateActorCharges(float deltaSeconds);
    GameplayActorModifiers::ChargeWorld chargeWorld();
    GameplayActorModifiers::ChargeActorFacts chargeActorFacts(size_t actorIndex) const;
    void handleChargeEvent(const GameplayActorModifiers::ChargeEvent &event);
    // A monster's missile homes: a true_aim monster's at its target, the rules' cone at the party (MAW).
    void attachTrueAim(uint32_t firstProjectileId, const MapActorState &actor, ActorAiTargetKind targetKind,
        size_t targetActorIndex, uint32_t spellId);
    // One step of a homing projectile toward its target's current position; true when it is to expire.
    bool steerOutdoorHomingProjectile(ProjectileState &projectile, float deltaSeconds, float partyX, float partyY,
        float partyZ);
    bool monsterNeverStaggers(int16_t monsterId) const;
    bool spawnEncounterFromResolvedData(
        int encounterSlot,
        char fixedTier,
        uint32_t count,
        float x,
        float y,
        float z,
        uint16_t radius,
        uint16_t attributes,
        uint32_t group,
        uint32_t uniqueNameId,
        bool fromSpawnPoint,
        size_t spawnPointIndex,
        bool aggro);
    bool setMapActorHostileToParty(size_t actorIndex, float partyX, float partyY, float partyZ, bool resetActionState);
    void aggroNearbyMapActorFaction(
        size_t actorIndex,
        bool alertsFriendlyActors,
        float partyX,
        float partyY,
        float partyZ);
    ChestViewState buildChestView(uint32_t chestId) const;
    void activateChestView(uint32_t chestId);
    bool attemptOpenChest(uint32_t chestId, bool openedByTelekinesis = false);
    GameplayWorldPoint chestTrapSourcePoint() const;
    GameplayWorldPoint chestTrapVisualPoint(const GameplayWorldPoint &sourcePoint) const;
    void applyChestTrapState(uint32_t chestId, const ChestTrapOpenResult &trapResult);
    // The impact of object objectId at point, with the fireball's sound: a chest trap or a monster's death blast.
    void spawnObjectBurstVisual(const GameplayWorldPoint &point, uint16_t objectId, CombatDamageType damageType);
    void pushAudioEvent(
        uint32_t soundId,
        uint32_t sourceId,
        const std::string &reason,
        float x,
        float y,
        float z,
        bool positional = true,
        SoundScope soundScope = SoundScope::Engine);
    void pushOutdoorMonsterSound(size_t actorIndex, uint32_t soundId, const char *pReason);
    bool beginMapActorHitReaction(size_t actorIndex, bool force = false, bool emitAudio = true);
    // A hit on an MM9 walker (ActorMm9WorldFacts): its attacker (the party, or the actor at attackerActorIndex), the
    // largest hit and the count its AI reacts to. Nothing for any other actor.
    void noteMm9ActorHit(size_t actorIndex, ActorAiTargetKind attackerKind, size_t attackerActorIndex, int damage);
    // A reaction turn (hit, alert, stun) toward a point; skipped for a monster that turns at a tactics traverse rate
    // (a turret), whose AI turns it there at that rate instead.
    void faceMapActorReaction(MapActorState &actor, float deltaX, float deltaY) const;
    void pushProjectileAudioEvent(const GameplayProjectileService::ProjectileAudioRequest &request);
    bool spawnProjectileFromMapActor(
        const MapActorState &actor,
        const MonsterTable::MonsterStatsEntry &stats,
        MonsterAttackAbility ability,
        float targetX,
        float targetY,
        float targetZ,
        int damage = 0,
        int attackBonus = 0,
        uint32_t spellId = 0,
        uint32_t skillLevel = 0,
        SkillMastery skillMastery = SkillMastery::None,
        const std::string &projectileTokenOverride = std::string()
    );
    // The world point a model actor launches its missile or spell from (its actors.yml release point); empty for
    // sprite actors and models without one, which launch from the body (mapActorBodyLaunchPoint).
    std::optional<std::array<float, 3>> mapActorModelLaunchPoint(const MapActorState &actor, bool spell) const;
    // An attack role's timing: the actor's sprite's, or its 3D model's clip where that times it
    // (resolveActorAttackTiming).
    ActorAttackTiming mapActorAttackTiming(const MapActorState &actor, ActorModelManifest::AttackRole role) const;
    static std::array<float, 3> mapActorBodyLaunchPoint(const MapActorState &actor);
    bool castSpellFromMapActor(
        const MapActorState &actor,
        const MonsterTable::MonsterStatsEntry &stats,
        MonsterAttackAbility ability,
        float targetX,
        float targetY,
        float targetZ
    );
    bool castSpell(const SpellCastRequest &request);
    bool resolveObjectProjectileDefinition(
        int objectId,
        int impactObjectId,
        ResolvedProjectileDefinition &definition) const;
    bool castDirectSpellProjectile(
        const SpellCastRequest &request,
        const ResolvedProjectileDefinition &definition
    );
    bool spawnDeathBlossomFalloutProjectiles(
        const ProjectileState &projectile,
        float x,
        float y,
        float z);
    bool castMeteorShower(
        const SpellCastRequest &request,
        const ResolvedProjectileDefinition &definition
    );
    bool castStarburst(
        const SpellCastRequest &request,
        const ResolvedProjectileDefinition &definition
    );
    bool projectileSourceIsFriendlyToActor(const ProjectileState &projectile, const MapActorState &actor) const;
    bool spawnSpellProjectile(
        const SpellCastRequest &request,
        const ResolvedProjectileDefinition &definition,
        float sourceX,
        float sourceY,
        float sourceZ,
        float targetX,
        float targetY,
        float targetZ,
        float spawnForwardOffset
    );
    void buildOutdoorFaceSpatialIndex();
    void rebuildOutdoorFaceGeometryCache();
    void syncOutdoorFaceGeometryAttributesFromMapDelta();
    void setOutdoorFaceGeometryAttributes(size_t bModelIndex, size_t faceIndex, uint32_t attributes);
    void initializeOutdoorModelMechanismsFromMapData();
    void initializeOutdoorDestructiblesFromMapData();
    void updateOutdoorTriggerVolumes();
    void applyOutdoorDestructibleStates(bool playEffects);
    void projectOutdoorDestructibleGeometry(const OutdoorDestructible &definition, bool destroyed);
    void applyOutdoorDestructibleDeathOutput(const OutdoorDestructible &definition);
    void updateOutdoorMechanismOpenAwayDirections();
    void refreshOutdoorModelMechanismGeometry();
    void resyncOutdoorModelMechanismGeometry();
    bool setOutdoorFaceGeometry(const OutdoorFaceGeometryData &geometry);
    bool materializeTreasureSpawnFromSpawnPoint(size_t spawnPointIndex);
    bool resolveWorldItemVisual(
        uint32_t itemId,
        uint16_t &objectDescriptionId,
        uint16_t &objectSpriteId,
        uint16_t &objectSpriteFrameIndex,
        uint16_t &objectFlags,
        uint16_t &radius,
        uint16_t &height,
        std::string &objectName,
        std::string &objectSpriteName) const;
    void materializeMapDeltaWorldItems();
    void materializeSemanticWorldItems();
    bool groundMm9WorldItemPlacement(WorldItemState &worldItem) const;
    bool groundMm9ActorPlacement(MapActorState &actor);
    void groundMm9LoadedPlacements(bool updateActorHomes, bool includeRuntimeActors);
    void removeDepletedSemanticLootContainer(uint32_t containerId);
    void spawnMonsterDeathDropsForActor(size_t actorIndex, const MapActorState &actor);
    void queueMonsterKilledEvent(size_t actorIndex, int16_t monsterId);
    bool spawnMonsterDeathDropWorldItem(
        const InventoryItem &item,
        float x,
        float y,
        float z,
        uint32_t seed);
    std::optional<float> sampleBModelWorldItemFloorHeight(
        float x,
        float y,
        float maximumZ,
        std::vector<size_t> &candidateFaceIndices) const;
    void updateWorldItems(float deltaSeconds);
    // One sub-step of a moving item: gravity, its sphere chain against walls (none: it moves as a point), its floor,
    // water.
    void stepWorldItem(
        WorldItemState &worldItem,
        float deltaSeconds,
        const WorldItemSphereChain *pChain,
        std::vector<size_t> &candidateFaceIndices);
    // The nearest BModel wall an item's sphere chain meets moving from start to end: the distance travelled to it and
    // the wall's normal.
    std::optional<std::pair<float, bx::Vec3>> sweepWorldItemAgainstWalls(
        const WorldItemSphereChain &chain,
        const bx::Vec3 &start,
        const bx::Vec3 &end,
        std::vector<size_t> &candidateFaceIndices) const;
    void updateImmolation(float deltaSeconds);
    void updateFireSpikeTraps(float deltaSeconds, float partyX, float partyY, float partyZ);
    void applyFireSpikeTrapTriggerResult(
        FireSpikeTrapState &trap,
        const GameplayProjectileService::FireSpikeTrapTriggerResult &result);
    int resolveProjectilePartyImpactDamage(const ProjectileState &projectile) const;
    GameplayProjectileService::ProjectileAreaImpactInput buildProjectileAreaImpactInput(
        const ProjectileState &projectile,
        const bx::Vec3 &impactPoint,
        float impactRadius,
        float partyX,
        float partyY,
        float partyZ,
        bool canHitParty,
        size_t directActorIndex) const;
    int resolvePartyProjectileDamageMultiplier(
        const ProjectileState &projectile,
        size_t actorIndex) const;
    GameplayProjectileService::ProjectileDirectActorImpactInput buildProjectileDirectActorImpactInput(
        const ProjectileState &projectile,
        size_t actorIndex) const;
    ProjectileCollisionFacts buildProjectileCollisionFacts(
        const ProjectileState &projectile,
        const bx::Vec3 &segmentStart,
        const bx::Vec3 &segmentEnd,
        float partyX,
        float partyY,
        float partyZ) const;
    ProjectileFrameWorldFacts collectProjectileFrameFacts(
        const ProjectileState &projectile,
        float deltaSeconds,
        float partyX,
        float partyY,
        float partyZ) const;
    GameplayProjectileService::ProjectileBounceSurfaceFacts buildProjectileBounceSurfaceFacts(
        const ProjectileCollisionFacts &collision) const;
    void applyProjectileFrameResult(
        ProjectileState &projectile,
        const ProjectileCollisionFacts &collision,
        const GameplayProjectileService::ProjectileFrameResult &frameResult);
    bool applyProjectileSpawnEffects(
        const GameplayProjectileService::ProjectileSpawnResult &spawnResult,
        const GameplayProjectileService::ProjectileSpawnEffects &effects,
        const std::string &spawnKindName,
        const std::string &instantColliderName);
    static const char *projectileCollisionKindName(ProjectileCollisionKind kind);
    void updateProjectiles(float deltaSeconds, float partyX, float partyY, float partyZ);
    bool shouldTraceOutdoorActorAi(float deltaSeconds);
    void traceOutdoorActorAiDecisions(
        const ActorAiFrameFacts &facts,
        const ActorAiFrameResult &result,
        const std::vector<bool> &activeActorMask) const;
    void traceOutdoorActorAiAfter(const std::vector<bool> &activeActorMask) const;
    void spawnProjectileImpact(
        const ProjectileState &projectile,
        float x,
        float y,
        float z,
        bool centerVertically = false,
        size_t targetActorIndex = static_cast<size_t>(-1));
    bool spawnImmediateSpellVisual(
        uint32_t spellId,
        float x,
        float y,
        float z,
        bool centerVertically = false,
        bool preferImpactObject = true,
        size_t targetActorIndex = static_cast<size_t>(-1));
    bool spawnWaterSplashImpact(float x, float y, float z);
    void addBloodSplat(uint32_t sourceActorId, float x, float y, float z, float radius);
    void bakeBloodSplatGeometry(BloodSplatState &splat) const;
    void spawnBloodSplatForActorIfNeeded(size_t actorIndex);
    void removeBloodSplat(uint32_t sourceActorId);
    void refreshRuntimeActorVisualResources();
    void initializeMm9Barrels();
    void applyMm9BarrelVisual(const MapMm9BarrelSource &source, const MapDeltaMm9BarrelState &state);
    GameplayProjectileService &projectileService();
    const GameplayProjectileService &projectileService() const;
    GameplayProjectileService::ProjectileImpactSpawnResult spawnProjectileImpactVisual(
        const ProjectileState &projectile,
        const GameplayProjectileService::ProjectileImpactVisualDefinition &definition,
        float x,
        float y,
        float z,
        bool centerVertically,
        size_t targetActorIndex = static_cast<size_t>(-1));
    GameplayProjectileService::ProjectileImpactSpawnResult spawnWaterSplashImpactVisual(
        const GameplayProjectileService::ProjectileImpactVisualDefinition &definition,
        float x,
        float y,
        float z);
    GameplayProjectileService::ProjectileImpactSpawnResult spawnImmediateSpellImpactVisual(
        const GameplayProjectileService::ProjectileImpactVisualDefinition &definition,
        int sourceSpellId,
        const std::string &sourceObjectName,
        const std::string &sourceObjectSpriteName,
        float x,
        float y,
        float z,
        bool centerVertically,
        bool freezeAnimation,
        size_t targetActorIndex);

    int m_mapId = 0;
    int m_mapTreasureLevel = 0;
    MapStatsEntry m_map = {};
    std::string m_mapName;
    // Frame-sized increments must remain representable after months of campaign time.
    double m_gameMinutes = 9.0 * 60.0;
    AtmosphereState m_atmosphereState = {};
    std::optional<OutdoorWeatherProfile> m_outdoorWeatherProfile;
    bool m_mergedWeatherStateCacheValid = false;
    int m_cachedMergedWeatherMapId = 0;
    int m_cachedMergedWeatherHourIndex = 0;
    int m_cachedMergedWeatherState = 0;
    // Wetness integrates hours of weather, so it is resampled once per game minute.
    int64_t m_cachedWetnessMinute = -1;
    int m_cachedWetnessMapId = 0;
    float m_cachedWetness = 0.0f;
    std::vector<TimerState> m_timers;
    bool m_timerDefinitionsInitialized = false;
    bool m_resetLegacyTimersOnInitialize = false;
    std::vector<MapActorState> m_mapActors;
    bool m_monsterKilledHooksEnabled = false;
    std::vector<MonsterKilledEvent> m_pendingMonsterKilledEvents;
    // Deaths of exploding monsters, detonated on the next actor update (MonsterDeathExplosion.h).
    std::vector<PendingMonsterDeathExplosion> m_pendingDeathExplosions;
    std::vector<size_t> m_mm9FoundPlayerActorIndices;
    std::vector<bool> m_mm9FoundPlayerEventAttempted;
    std::vector<size_t> m_mm9CivilianActorIndices;
    // Villagers still fleeing a yell (yellFleeRemainingSeconds > 0).
    std::vector<size_t> m_yellFleeingActorIndices;
    std::vector<size_t> m_mm9GuardActorIndices;
    std::vector<SpawnPointState> m_spawnPoints;
    std::vector<MapDeltaChest> m_chests;
    std::vector<bool> m_openedChests;
    std::vector<std::optional<ChestViewState>> m_materializedChestViews;
    std::optional<ChestViewState> m_activeChestView;
    std::optional<GameplayWorldPoint> m_pendingEventSourcePoint;
    std::optional<EventRuntimeState> m_eventRuntimeState;
    mutable ActorInspectPreviewAnimation m_actorInspectPreviewAnimation = {};
    const ItemTable *m_pItemTable = nullptr;
    Party *m_pParty = nullptr;
    OutdoorPartyRuntime *m_pPartyRuntime = nullptr;
    const StandardItemEnchantTable *m_pStandardItemEnchantTable = nullptr;
    const SpecialItemEnchantTable *m_pSpecialItemEnchantTable = nullptr;
    MapItemSourceData m_itemSourceData;
    SearchableLootPropState m_searchableLootPropState;
    const ChestTable *m_pChestTable = nullptr;
    const MonsterTable *m_pMonsterTable = nullptr;
    const MergedBolsterMapTable *m_pMergedBolsterMapTable = nullptr;
    const MergedBolsterMonsterTable *m_pMergedBolsterMonsterTable = nullptr;
    const MonsterProjectileTable *m_pMonsterProjectileTable = nullptr;
    const ObjectTable *m_pObjectTable = nullptr;
    OutdoorMapData *m_pOutdoorMapData = nullptr;
    bool m_usesBModelGround = false;
    MapDeltaData *m_pOutdoorMapDeltaData = nullptr;
    bool m_enclosedMinimapLinesValid = false;
    int32_t m_enclosedMinimapCellX = 0;
    int32_t m_enclosedMinimapCellY = 0;
    int32_t m_enclosedMinimapLevel = 0;
    uint64_t m_enclosedMinimapMechanismSignature = 0;
    std::vector<GameplayMinimapLineState> m_cachedEnclosedMinimapLines;
    const SpellTable *m_pSpellTable = nullptr;
    bool m_bolsterMonstersEnabled = false;
    GameplayActorService *m_pGameplayActorService = nullptr;
    GameplayProjectileService *m_pGameplayProjectileService = nullptr;
    GameplayProjectileService m_fallbackGameplayProjectileService;
    ActorBehaviorRuntime m_actorBehaviors;
    // The AI arena's decision trace (GameApplication owns it), null while off.
    ActorAiTrace *m_pActorAiTrace = nullptr;
    ActorPartyVelocityTracker m_actorAiPartyVelocity;
    GameplayActorHitFeedback m_actorHitFeedback;
    GameplayActorShields m_actorShields;
    GameplayActorModifiers m_actorModifiers;
    // Decoration cylinders a blink must not land in; filled only when some monster blinks.
    std::vector<OutdoorDecorationCollision> m_blinkDecorationColliders;
    std::vector<DecorationClearRule> m_decorationClearRules;
    std::vector<bool> m_hiddenDecorationEntities;
    // MonsterRelationAddOns::revision() last applied to the actors; UINT64_MAX after a load.
    uint64_t m_appliedRelationRevision = UINT64_MAX;
    GameplayCombatController *m_pGameplayCombatController = nullptr;
    GameplayFxService *m_pGameplayFxService = nullptr;
    const std::optional<ScriptedEventProgram> *m_pGlobalEventProgram = nullptr;
    const SpriteFrameTable *m_pActorSpriteFrameTable = nullptr;
    const SpriteFrameTable *m_pProjectileSpriteFrameTable = nullptr;
    WorldFxSystem *m_pWorldFxSystem = nullptr;
    OutdoorGameView *m_pInteractionView = nullptr;
    GameplayWorldMovementFrameDiagnostics m_lastWorldMovementFrameDiagnostics = {};
    std::optional<std::vector<uint8_t>> m_outdoorLandMask;
    std::vector<OutdoorFaceGeometryData> m_outdoorFaces;
    std::vector<std::vector<size_t>> m_outdoorFaceGridCells;
    mutable std::vector<uint32_t> m_outdoorFaceVisitGenerations;
    mutable uint32_t m_outdoorFaceVisitGenerationCounter = 1;
    float m_outdoorFaceGridMinX = 0.0f;
    float m_outdoorFaceGridMinY = 0.0f;
    size_t m_outdoorFaceGridWidth = 0;
    size_t m_outdoorFaceGridHeight = 0;
    std::optional<OutdoorMovementController> m_outdoorMovementController;
    bool m_outdoorPathMapValid = false;
    bool m_outdoorLandPathMapValid = false;
    bool m_outdoorPathfindingEnabled = false;
    bool m_logOutdoorPathfinding = false;
    std::shared_ptr<const PathMap> m_outdoorPathMapSnapshot;
    std::shared_ptr<const PathMap> m_outdoorLandPathMapSnapshot;
    ActorPathRuntime m_actorPathRuntime;
    double m_actorPathRuntimeSeconds = 0.0;
    // Actor detection rays (actor to party, actor to actor) are reused for 0.125-0.23 s while both ends stay within
    // 48 units of the checked positions, like MM8's cached Nearby detection; the AI itself still steps at 128 Hz.
    struct ActorSightCacheEntry
    {
        bool visible = false;
        double checkedSeconds = 0.0;
        std::array<float, 3> start = {};
        std::array<float, 3> end = {};
    };
    mutable std::unordered_map<uint64_t, ActorSightCacheEntry> m_actorSightCache;
    size_t m_actorPathPlansThisStep = 0;
    float m_outdoorMechanismGeometryRefreshAccumulatorSeconds = 0.0f;
    std::unordered_map<uint32_t, std::array<int32_t, 3>> m_outdoorMechanismOffsets;
    std::unordered_map<uint32_t, bool> m_outdoorNavigationMechanismMovingStates;
    std::unordered_map<uint32_t, size_t> m_outdoorDestructibleDefinitionBySourceObject;
    std::unordered_map<size_t, uint32_t> m_outdoorDestructibleSourceObjectByBModel;
    std::unordered_map<uint32_t, bool> m_outdoorTriggerWasInside;
    std::unordered_map<int16_t, MonsterVisualState> m_monsterVisualsById;
    float m_actorUpdateAccumulatorSeconds = 0.0f;
    float m_mm9FoundPlayerAccumulatorSeconds = 0.0f;
    float m_actorAiTraceAccumulatorSeconds = 0.0f;
    float m_projectileUpdateAccumulatorSeconds = 0.0f;
    float m_immolationTickAccumulatorGameMinutes = 0.0f;
    uint32_t m_immolationTickSequence = 0;
    bool m_actorAiUpdateQueued = false;
    ActorTurnBasedFrameFacts m_turnBasedActorFacts = {};
    float m_queuedActorAiDeltaSeconds = 0.0f;
    float m_queuedActorAiPartyX = 0.0f;
    float m_queuedActorAiPartyY = 0.0f;
    float m_queuedActorAiPartyZ = 0.0f;
    uint32_t m_sessionChestSeed = 0;
    uint32_t m_nextActorId = 0;
    std::vector<std::optional<CorpseViewState>> m_mapActorCorpseViews;
    // Gold and random item that Telepathy rolled for a living actor; its corpse takes them at death.
    std::vector<std::optional<CorpseViewState>> m_mapActorRevealedLoot;
    bool m_corpseLootPending = false;
    std::optional<CorpseViewState> m_activeCorpseView;
    std::vector<size_t> m_actorCorpsePhysicsActorIndices;
    std::vector<AudioEvent> m_pendingAudioEvents;
    std::vector<WorldItemState> m_worldItems;
    uint32_t m_nextWorldItemId = 1;
    float m_gameplayOverlayRemainingSeconds = 0.0f;
    std::vector<GameplayCombatFeedbackEvent> m_combatFeedbackEvents;
    float m_gameplayOverlayDurationSeconds = 0.0f;
    float m_gameplayOverlayPeakAlpha = 0.0f;
    uint32_t m_gameplayOverlayColorAbgr = 0x00000000u;
    DebugSkyOverrides m_debugSkyOverrides;
    std::vector<FireSpikeTrapState> m_fireSpikeTraps;
    std::vector<BloodSplatState> m_bloodSplats;
    uint64_t m_bloodSplatRevision = 0;
    ArmageddonState m_armageddonState = {};
    float m_partyCollisionRadius = 37.0f;
    float m_partyCollisionHeight = 192.0f;

    void invalidateOutdoorPathMaps(bool clearActorPaths);
    std::shared_ptr<const PathMap> outdoorPathMap(bool landOnly);
    bool outdoorActorPathfindingEnabled() const;
    bool logOutdoorPathfindingEnabled() const;
    void updateGameplayScreenOverlay(float deltaSeconds);
    void updateActorFrameGlobalEffects(float deltaSeconds, float partyX, float partyY, float partyZ);
    std::vector<bool> selectOutdoorActiveActors(float partyX, float partyY, float partyZ);
    ActorAiFrameFacts collectOutdoorActorAiFrameFacts(
        float deltaSeconds,
        float partyX,
        float partyY,
        float partyZ,
        const std::vector<bool> &activeActorMask) const;
    // Each patrolling actor's place in its round (MapDeltaActor::patrolPoints); advanced as the AI facts are read, not
    // saved (a load starts the round at its first waypoint).
    mutable std::unordered_map<size_t, size_t> m_actorPatrolIndices;
    std::optional<ActorAiFacts> collectOutdoorActorAiFacts(
        size_t actorIndex,
        bool active,
        float partyX,
        float partyY,
        float partyZ) const;
    // An actor's MM9 placement: a map actor's from the map, a runtime spawn's its own; none for MM9's defaults.
    const Mm9AiPlacementRecord *mm9PlacementRecord(size_t actorIndex) const;
    // How far an MM9 monster on its loop senses the party (its placement's sight and hearing, doubled after contact);
    // 0 for every other actor.
    float mm9PerceptionRangeOf(size_t actorIndex) const;
    bool cachedActorLineOfSight(size_t startActorIndex, size_t endActorIndex, const bx::Vec3 &start,
        const bx::Vec3 &end) const;
    void applyOutdoorActorAiFrameResult(
        const ActorAiFrameResult &result,
        const std::vector<bool> &activeActorMask,
        const GameplayActorAiSystem &actorAiSystem);
    void applyOutdoorActorRequests(const ActorAiFrameResult &result, const std::vector<bool> &activeActorMask);
    // The reposition modifier's query (ActorMm9Request::reposition): the first of its spots that passes, answered in
    // the actor's ActorMm9WorldFacts (repositionSerial).
    void answerRepositionQuery(size_t actorIndex, const ActorRepositionQuery &query);
    void applyOutdoorActorProjectileRequests(
        const std::vector<ActorProjectileRequest> &projectileRequests,
        const std::vector<bool> &activeActorMask);
    void applyOutdoorActorProjectileRequest(const ActorProjectileRequest &projectileRequest);
    void applyOutdoorActorAudioRequests(const std::vector<ActorAudioRequest> &audioRequests);
    void applyOutdoorActorFxRequests(const std::vector<ActorFxRequest> &fxRequests);
    bool hasOutdoorActorBehaviorUpdate(const ActorAiUpdate &update) const;
    void ensureOutdoorActorMovementState(MapActorState &actor, const MonsterTable::MonsterStatsEntry &stats);
    void applyOeOutdoorActorFloorCorrection(MapActorState &actor, const MonsterTable::MonsterStatsEntry &stats);
    void applyOutdoorActorStateUpdate(MapActorState &actor, const ActorStateUpdate &state);
    void applyOutdoorActorAnimationUpdate(MapActorState &actor, const ActorAnimationUpdate &animation);
    void applyOutdoorActorMovementIntent(
        size_t actorIndex,
        MapActorState &actor,
        const MonsterTable::MonsterStatsEntry *pStats,
        const ActorMovementIntent &movementIntent,
        const std::vector<bool> &activeActorMask,
        const GameplayActorAiSystem &actorAiSystem);
    void applyOutdoorActorAttackRequest(
        MapActorState &actor,
        const std::optional<ActorAttackRequest> &attackRequest);
    bool outdoorActorCanApplyPartyMeleeImpact(const MapActorState &actor) const;
    void applyOutdoorActorTerminalUpdate(size_t actorIndex, MapActorState &actor, const ActorAiUpdate &update);
    void syncOutdoorActorIntegerPosition(MapActorState &actor) const;
    void activateOutdoorActorCorpsePhysics(size_t actorIndex);
    void applyOutdoorActorCorpsePhysicsSteps(
        const std::vector<bool> &activeActorMask,
        const std::vector<uint8_t> &actorPhysicsApplied);
    bool applyOutdoorActorPhysicsStep(
        size_t actorIndex,
        const MonsterTable::MonsterStatsEntry &stats,
        const std::vector<bool> &activeActorMask,
        bool refreshActorColliders = true);
    void applyOutdoorActorPostMovementAiUpdate(
        MapActorState &actor,
        const ActorAiUpdate &movementUpdate,
        float &desiredMoveX,
        float &desiredMoveY);
    void applyOutdoorActorMovementIntegration(
        size_t actorIndex,
        const MonsterTable::MonsterStatsEntry *pStats,
        const std::vector<bool> &activeActorMask,
        ActorAiMovementAction movementAction,
        float moveSpeed,
        float desiredMoveZ,
        bool meleePursuitActive,
        bool crowdSteeringActive,
        bool inMeleeRange,
        const GameplayWorldPoint &targetPosition,
        float targetEdgeDistance,
        bool targetHasAttackLineOfSight,
        const GameplayActorAiSystem &actorAiSystem,
        ActorAiState &nextAiState,
        ActorAnimation &nextAnimation,
        float &desiredMoveX,
        float &desiredMoveY);
    void updateOutdoorInactiveAndInvalidActors(const std::vector<bool> &activeActorMask);
    void applyActorFrameSideEffects(float deltaSeconds, float partyX, float partyY, float partyZ);
    void updateMm9ActorReactions(float deltaSeconds, float partyX, float partyY, float partyZ);
    void updateYellFleeing(float deltaSeconds);
    void startMm9CivilianFlee(MapActorState &actor);
    void advanceGameMinutesInternal(float minutes);
    void initializeTimers(
        const std::optional<ScriptedEventProgram> &localEventProgram,
        const std::optional<ScriptedEventProgram> &globalEventProgram,
        double registrationGameMinutes
    );
    void applyInitialWeatherProfile();
    int cachedMergedWeatherState(const OutdoorWeatherProfile &profile);
    int mergedLadderState(const OutdoorWeatherProfile &profile, const WeatherSample &sample);
    bool isMergedWeatherMap() const;
    // The weather now, with scene, event and debug overrides applied.
    WeatherSample currentWeatherSample();
    void applyPrecipitationState(const WeatherSample &sample);
    bool applyMergedWeatherProfile();
    void applyDailyWeatherRollover(int weatherDayIndex);
    void applyFogDistances(const OutdoorFogDistances &distances, bool foggy);
    void syncAtmosphereStateToMapDelta();
    int weatherDayIndexForMinutes(float gameMinutes) const;
    void resetDailySpellCounters();
    void updateArmageddon(float deltaSeconds, float partyX, float partyY, float partyZ);
    void spawnArmageddonStrikes(float elapsedBefore, float elapsedAfter, float partyX, float partyY, float partyZ);
    void resolveArmageddonDetonation(float partyX, float partyY, float partyZ);
    void refreshAtmosphereState();
};
}
