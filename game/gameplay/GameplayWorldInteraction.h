#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

#include <bx/math.h>

namespace OpenYAMM::Game
{
inline constexpr size_t GameplayInvalidWorldIndex = size_t(-1);

struct GameplayWorldRay
{
    bx::Vec3 origin = {0.0f, 0.0f, 0.0f};
    bx::Vec3 direction = {0.0f, 0.0f, 0.0f};
};

struct GameplayWorldPickRequest
{
    float screenX = 0.0f;
    float screenY = 0.0f;
    int viewWidth = 0;
    int viewHeight = 0;
    std::array<float, 16> viewMatrix = {};
    std::array<float, 16> projectionMatrix = {};
    bx::Vec3 rayOrigin = {0.0f, 0.0f, 0.0f};
    bx::Vec3 rayDirection = {0.0f, 0.0f, 0.0f};
    bx::Vec3 eye = {0.0f, 0.0f, 0.0f};
    bool hasRay = false;
    bool ignoreActors = false;
};

struct GameplayWorldPickRequestInput
{
    float screenX = 0.0f;
    float screenY = 0.0f;
    int screenWidth = 0;
    int screenHeight = 0;
    bool includeRay = false;
};

enum class GameplayWorldHitKind
{
    None,
    Actor,
    WorldItem,
    Chest,
    Corpse,
    EventTarget,
    Object,
    Ground,
};

enum class GameplayWorldContainerSourceKind
{
    None,
    Chest,
    Corpse,
};

enum class GameplayWorldEventTargetKind
{
    None,
    Surface,
    Entity,
    Decoration,
    Object,
    Spawn,
    Mechanism,
};

struct GameplayActorTargetHit
{
    size_t actorIndex = GameplayInvalidWorldIndex;
    std::string displayName;
    bool isFriendly = false;
    int16_t npcId = 0;
    uint32_t actorGroup = 0;
    bx::Vec3 hitPoint = {0.0f, 0.0f, 0.0f};
    float distance = 0.0f;
};

struct GameplayWorldItemTargetHit
{
    size_t worldItemIndex = GameplayInvalidWorldIndex;
    std::string displayName;
    uint16_t objectDescriptionId = 0;
    uint16_t objectSpriteId = 0;
    bx::Vec3 hitPoint = {0.0f, 0.0f, 0.0f};
    float distance = 0.0f;
};

struct GameplayContainerTargetHit
{
    GameplayWorldContainerSourceKind sourceKind = GameplayWorldContainerSourceKind::None;
    size_t sourceIndex = GameplayInvalidWorldIndex;
    std::string displayName;
    float distance = 0.0f;
};

struct GameplayEventTargetContextActionMetadata
{
    std::string kind;
    std::string source;
    std::optional<uint32_t> houseId;
    std::optional<std::string> targetMap;
    std::optional<std::string> targetName;
    std::optional<int32_t> mm9SourceObjectIndex;
    std::optional<std::string> mm9ObjectId;
    std::optional<std::string> mm9SourceClass;
    std::optional<std::string> mm9SourceName;
    std::optional<std::string> mm9VisualId;
    std::optional<std::string> mm9ScriptName;
    std::optional<std::string> mm9ScriptParams;
    std::vector<uint32_t> chestIds;
    bool hidden = false;
};

struct GameplayEventTargetHit
{
    GameplayWorldEventTargetKind targetKind = GameplayWorldEventTargetKind::None;
    size_t targetIndex = GameplayInvalidWorldIndex;
    size_t secondaryIndex = GameplayInvalidWorldIndex;
    uint16_t eventIdPrimary = 0;
    uint16_t eventIdSecondary = 0;
    uint16_t triggeredEventId = 0;
    uint16_t trigger = 0;
    uint16_t variablePrimary = 0;
    uint16_t variableSecondary = 0;
    uint16_t specialTrigger = 0;
    uint32_t attributes = 0;
    std::string name;
    std::vector<uint32_t> openedChestIds;
    std::optional<GameplayEventTargetContextActionMetadata> contextActionMetadata;
    bx::Vec3 hitPoint = {0.0f, 0.0f, 0.0f};
    float distance = 0.0f;
    bool hintOnlyEvent = false;
};

struct GameplayObjectTargetHit
{
    size_t objectIndex = GameplayInvalidWorldIndex;
    uint16_t objectDescriptionId = 0;
    uint16_t objectSpriteId = 0;
    int32_t spellId = 0;
    bx::Vec3 hitPoint = {0.0f, 0.0f, 0.0f};
    float distance = 0.0f;
};

struct GameplayGroundTargetHit
{
    bx::Vec3 worldPoint = {0.0f, 0.0f, 0.0f};
    float distance = 0.0f;
    bool isValid = false;
};

struct GameplayWorldHit
{
    bool hasHit = false;
    GameplayWorldHitKind kind = GameplayWorldHitKind::None;
    std::optional<GameplayActorTargetHit> actor;
    std::optional<GameplayWorldItemTargetHit> worldItem;
    std::optional<GameplayContainerTargetHit> container;
    std::optional<GameplayEventTargetHit> eventTarget;
    std::optional<GameplayObjectTargetHit> object;
    std::optional<GameplayGroundTargetHit> ground;
};

struct GameplayHoverStatusPayload
{
    GameplayWorldHit worldHit;
    std::optional<std::string> eventTargetStatusText;
};

enum class GameplayWorldHoverProbeKind
{
    Standard,
    PendingSpell,
};

struct GameplayWorldHoverRequest
{
    GameplayWorldHoverProbeKind probeKind = GameplayWorldHoverProbeKind::Standard;
    GameplayWorldPickRequest primaryPickRequest = {};
    std::optional<GameplayWorldPickRequest> secondaryPickRequest;
    uint64_t updateTickNanoseconds = 0;
};

struct GameplayWorldHoverCacheState
{
    bool hasCachedHover = false;
    uint64_t lastUpdateNanoseconds = 0;
};

struct GameplayPendingSpellWorldTargetFacts
{
    GameplayWorldHit worldHit = {};
    std::optional<bx::Vec3> fallbackGroundTargetPoint;
};

enum class GameplayContextActionKind
{
    None,
    Talk,
    PickUpItem,
    LootCorpse,
    OpenChest,
    EnterHouse,
    OpenDoor,
    PressButton,
    UseLever,
    GenericEvent,
};

struct GameplayContextAction
{
    GameplayContextActionKind kind = GameplayContextActionKind::None;
    GameplayWorldHit worldHit = {};
    std::string label;
    std::string iconId;
    float score = 0.0f;
};

struct GameplayContextActionState
{
    bool visible = false;
    std::vector<GameplayContextAction> actions;
    size_t primaryIndex = 0;
    uint64_t lastUpdateNanoseconds = 0;
    bool hasLastUpdateRay = false;
    bx::Vec3 lastUpdateRayOrigin = {0.0f, 0.0f, 0.0f};
    bx::Vec3 lastUpdateRayDirection = {0.0f, 0.0f, 0.0f};
};
}
