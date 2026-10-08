#pragma once

#include "game/tables/SpriteTables.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct IndoorEntity;
struct IndoorMapData;
struct OutdoorEntity;
struct EventRuntimeState;

const DecorationEntry *toggleableDecorationCounterpart(
    const DecorationTable &table, const DecorationEntry &decoration);
const DecorationEntry *runtimeDecorationEntry(
    const DecorationTable &table, const DecorationEntry &decoration,
    uint32_t spriteOverrideKey, const EventRuntimeState *pState);
const DecorationEntry *indoorDecorationLightToggleTarget(
    const IndoorMapData &map, const DecorationTable &table, size_t entityIndex,
    const EventRuntimeState *pState);
bool toggleIndoorDecorationLight(
    const IndoorMapData &map, const DecorationTable &table, size_t entityIndex,
    EventRuntimeState &state);

enum class InteractiveDecorationFamily : uint8_t
{
    None = 0,
    Barrel,
    Cauldron,
    TrashHeap,
    CampFire,
    Cask,
    FlourSack,
    LargeBag,
    Bucket,
    MightAndMagicSixTrashHeap,
    Crystal,
    GoldBag,
};

struct InteractiveDecorationBindingSpec
{
    uint16_t baseEventId = 0;
    uint8_t eventCount = 0;
    uint8_t initialState = 0;
    bool useSeededInitialState = false;
    bool hideWhenCleared = false;
    bool fixedEvent = false;
    InteractiveDecorationFamily family = InteractiveDecorationFamily::None;
};

std::optional<InteractiveDecorationFamily> classifyInteractiveDecorationFamily(
    const DecorationEntry &decoration,
    const std::string &instanceName);

std::optional<InteractiveDecorationBindingSpec> resolveInteractiveDecorationBindingSpec(
    const DecorationEntry &decoration,
    const std::string &instanceName);

uint32_t makeInteractiveDecorationSeed(
    size_t entityIndex,
    uint16_t decorationListId,
    int x,
    int y,
    int z);

uint8_t initialInteractiveDecorationState(InteractiveDecorationFamily family, uint32_t seed);

// Initialize fresh map assets only; saved map state must be restored afterwards.
void initializeMapInteractiveDecorations(
    std::span<const IndoorEntity> entities,
    const DecorationTable &decorationTable,
    std::array<uint8_t, 125> &decorVars,
    uint32_t randomSeed);

void initializeMapInteractiveDecorations(
    std::span<const OutdoorEntity> entities,
    const DecorationTable &decorationTable,
    std::array<uint8_t, 125> &decorVars,
    uint32_t randomSeed);

bool interactiveDecorationIsCleared(uint8_t state, uint8_t eventCount, bool hideWhenCleared);

std::optional<uint16_t> interactiveDecorationEventId(
    uint8_t state, uint16_t baseEventId, uint8_t eventCount, bool hideWhenCleared, bool fixedEvent);

std::vector<bool> hiddenIndoorDecorationEntities(
    std::span<const IndoorEntity> entities, const DecorationTable &table, const EventRuntimeState &state);
}
