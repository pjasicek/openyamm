#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>

#include <bx/math.h>

namespace OpenYAMM::Game
{
inline constexpr size_t GameplayInvalidWorldIndex = size_t(-1);

struct GameplayWorldRay
{
    bx::Vec3 origin = {0.0f, 0.0f, 0.0f};
    bx::Vec3 direction = {0.0f, 0.0f, 0.0f};
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
};

struct GameplayActorTargetHit
{
    size_t actorIndex = GameplayInvalidWorldIndex;
    std::string displayName;
    bool isFriendly = false;
    bx::Vec3 hitPoint = {0.0f, 0.0f, 0.0f};
    float distance = 0.0f;
};

struct GameplayWorldItemTargetHit
{
    size_t worldItemIndex = GameplayInvalidWorldIndex;
    uint16_t objectDescriptionId = 0;
    uint16_t objectSpriteId = 0;
    bx::Vec3 hitPoint = {0.0f, 0.0f, 0.0f};
    float distance = 0.0f;
};

struct GameplayContainerTargetHit
{
    GameplayWorldContainerSourceKind sourceKind = GameplayWorldContainerSourceKind::None;
    size_t sourceIndex = GameplayInvalidWorldIndex;
    float distance = 0.0f;
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
    std::string name;
    bx::Vec3 hitPoint = {0.0f, 0.0f, 0.0f};
    float distance = 0.0f;
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
}
