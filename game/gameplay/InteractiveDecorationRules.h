#pragma once

#include "game/tables/SpriteTables.h"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>

namespace OpenYAMM::Game
{
enum class InteractiveDecorationFamily : uint8_t
{
    None = 0,
    Barrel,
    Cauldron,
    TrashHeap,
    CampFire,
    Cask,
};

struct InteractiveDecorationBindingSpec
{
    uint16_t baseEventId = 0;
    uint8_t eventCount = 0;
    uint8_t initialState = 0;
    bool useSeededInitialState = false;
    bool hideWhenCleared = false;
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
}
