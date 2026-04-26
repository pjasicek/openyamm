#include "game/gameplay/InteractiveDecorationRules.h"

#include "game/StringUtils.h"

#include <algorithm>
#include <cctype>
#include <initializer_list>
#include <string_view>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
std::string normalizeDecorationKey(const std::string &value)
{
    const std::string lowered = toLowerCopy(value);
    size_t begin = 0;

    while (begin < lowered.size() && std::isspace(static_cast<unsigned char>(lowered[begin])) != 0)
    {
        ++begin;
    }

    size_t end = lowered.size();

    while (end > begin && std::isspace(static_cast<unsigned char>(lowered[end - 1])) != 0)
    {
        --end;
    }

    return lowered.substr(begin, end - begin);
}

bool decorationMatchesAnyKey(
    const std::vector<std::string> &keys,
    std::initializer_list<std::string_view> candidates)
{
    for (const std::string &key : keys)
    {
        for (std::string_view candidate : candidates)
        {
            if (key == candidate)
            {
                return true;
            }
        }
    }

    return false;
}

std::optional<int> parseDecorationInternalNumber(const std::string &value)
{
    const std::string normalized = normalizeDecorationKey(value);

    if (normalized.size() < 4 || normalized.rfind("dec", 0) != 0)
    {
        return std::nullopt;
    }

    int number = 0;

    for (size_t index = 3; index < normalized.size(); ++index)
    {
        const char character = normalized[index];

        if (!std::isdigit(static_cast<unsigned char>(character)))
        {
            return std::nullopt;
        }

        number = number * 10 + (character - '0');
    }

    return number;
}

std::optional<int> resolveDecorationInternalNumber(
    const DecorationEntry &decoration,
    const std::string &instanceName)
{
    if (const std::optional<int> internalNumber = parseDecorationInternalNumber(decoration.internalName))
    {
        return internalNumber;
    }

    return parseDecorationInternalNumber(instanceName);
}

uint16_t interactiveDecorationBaseEventId(InteractiveDecorationFamily family)
{
    switch (family)
    {
        case InteractiveDecorationFamily::Barrel:
            return 268;

        case InteractiveDecorationFamily::Cauldron:
            return 276;

        case InteractiveDecorationFamily::TrashHeap:
            return 281;

        case InteractiveDecorationFamily::CampFire:
            return 285;

        case InteractiveDecorationFamily::Cask:
            return 288;

        case InteractiveDecorationFamily::None:
            break;
    }

    return 0;
}

uint8_t interactiveDecorationEventCount(InteractiveDecorationFamily family)
{
    switch (family)
    {
        case InteractiveDecorationFamily::Barrel:
            return 8;

        case InteractiveDecorationFamily::Cauldron:
            return 5;

        case InteractiveDecorationFamily::TrashHeap:
            return 4;

        case InteractiveDecorationFamily::CampFire:
            return 2;

        case InteractiveDecorationFamily::Cask:
            return 2;

        case InteractiveDecorationFamily::None:
            break;
    }

    return 0;
}

bool interactiveDecorationHidesWhenCleared(InteractiveDecorationFamily family)
{
    return family == InteractiveDecorationFamily::CampFire;
}
}

std::optional<InteractiveDecorationFamily> classifyInteractiveDecorationFamily(
    const DecorationEntry &decoration,
    const std::string &instanceName)
{
    std::vector<std::string> keys;
    keys.reserve(3);

    const std::string hint = normalizeDecorationKey(decoration.hint);
    const std::string internalName = normalizeDecorationKey(decoration.internalName);
    const std::string normalizedInstanceName = normalizeDecorationKey(instanceName);

    if (!hint.empty())
    {
        keys.push_back(hint);
    }

    if (!internalName.empty() && std::find(keys.begin(), keys.end(), internalName) == keys.end())
    {
        keys.push_back(internalName);
    }

    if (!normalizedInstanceName.empty()
        && std::find(keys.begin(), keys.end(), normalizedInstanceName) == keys.end())
    {
        keys.push_back(normalizedInstanceName);
    }

    if (decorationMatchesAnyKey(keys, {"barrel", "dec03", "dec32"}))
    {
        return InteractiveDecorationFamily::Barrel;
    }

    if (decorationMatchesAnyKey(keys, {"cauldron", "dec26"}))
    {
        return InteractiveDecorationFamily::Cauldron;
    }

    if (decorationMatchesAnyKey(keys, {"trash heap", "trash pile", "dec01", "dec10", "dec23"}))
    {
        return InteractiveDecorationFamily::TrashHeap;
    }

    if (decorationMatchesAnyKey(keys, {"campfire", "camp fire", "dec24", "dec25"}))
    {
        return InteractiveDecorationFamily::CampFire;
    }

    if (decorationMatchesAnyKey(keys, {"keg", "cask", "dec21"}))
    {
        return InteractiveDecorationFamily::Cask;
    }

    return std::nullopt;
}

std::optional<InteractiveDecorationBindingSpec> resolveInteractiveDecorationBindingSpec(
    const DecorationEntry &decoration,
    const std::string &instanceName)
{
    const std::optional<InteractiveDecorationFamily> family =
        classifyInteractiveDecorationFamily(decoration, instanceName);

    if (family)
    {
        const uint16_t baseEventId = interactiveDecorationBaseEventId(*family);
        const uint8_t eventCount = interactiveDecorationEventCount(*family);

        if (baseEventId == 0 || eventCount == 0)
        {
            return std::nullopt;
        }

        InteractiveDecorationBindingSpec spec = {};
        spec.baseEventId = baseEventId;
        spec.eventCount = eventCount;
        spec.hideWhenCleared = interactiveDecorationHidesWhenCleared(*family);
        spec.family = *family;
        return spec;
    }

    const std::optional<int> internalNumber = resolveDecorationInternalNumber(decoration, instanceName);

    if (!internalNumber)
    {
        return std::nullopt;
    }

    InteractiveDecorationBindingSpec spec = {};

    if (*internalNumber >= 44 && *internalNumber <= 55)
    {
        spec.baseEventId = 531;
        spec.eventCount = 12;
        spec.initialState = static_cast<uint8_t>(*internalNumber - 44);
        return spec;
    }

    if (*internalNumber >= 40 && *internalNumber <= 43)
    {
        spec.baseEventId = static_cast<uint16_t>(542 + (*internalNumber - 40) * 7);
        spec.eventCount = 7;
        spec.useSeededInitialState = true;
        return spec;
    }

    return std::nullopt;
}

uint32_t makeInteractiveDecorationSeed(
    size_t entityIndex,
    uint16_t decorationListId,
    int x,
    int y,
    int z)
{
    uint32_t seed = static_cast<uint32_t>((entityIndex + 1u) * 2654435761u);
    seed ^= static_cast<uint32_t>(decorationListId + 1u) * 2246822519u;
    seed ^= static_cast<uint32_t>(x) * 3266489917u;
    seed ^= static_cast<uint32_t>(y) * 668265263u;
    seed ^= static_cast<uint32_t>(z + 1) * 374761393u;
    return seed;
}

uint8_t initialInteractiveDecorationState(InteractiveDecorationFamily family, uint32_t seed)
{
    switch (family)
    {
        case InteractiveDecorationFamily::Barrel:
            return static_cast<uint8_t>(1u + seed % 7u);

        case InteractiveDecorationFamily::Cauldron:
            return static_cast<uint8_t>(1u + seed % 4u);

        case InteractiveDecorationFamily::Cask:
            return 1;

        case InteractiveDecorationFamily::TrashHeap:
        case InteractiveDecorationFamily::CampFire:
        case InteractiveDecorationFamily::None:
            break;
    }

    return 0;
}
}
