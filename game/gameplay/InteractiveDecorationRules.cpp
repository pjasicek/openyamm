#include "game/gameplay/InteractiveDecorationRules.h"

#include "game/StringUtils.h"
#include "game/events/EventRuntime.h"
#include "game/indoor/IndoorMapData.h"
#include "game/outdoor/OutdoorMapData.h"

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <initializer_list>
#include <random>
#include <string_view>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint16_t MMergeCrystalAmethystEventId = 65310;
constexpr uint16_t MMergeCrystalDiamondEventId = 65311;
constexpr uint16_t MMergeCrystalRubyEventId = 65312;
constexpr uint16_t MMergeCrystalSapphireEventId = 65313;
constexpr uint16_t MMergeCrystalMoonstoneEventId = 65314;
constexpr uint16_t MMergeCrystalPurpleTopazEventId = 65315;
constexpr uint16_t MMergeCrystalEmeraldEventId = 65316;

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

std::vector<std::string> collectDecorationKeys(const DecorationEntry &decoration, const std::string &instanceName)
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

    return keys;
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

        case InteractiveDecorationFamily::FlourSack:
            return 1741;

        case InteractiveDecorationFamily::LargeBag:
            return 1743;

        case InteractiveDecorationFamily::GoldBag:
            return 1747;

        case InteractiveDecorationFamily::Bucket:
            return 1755;

        case InteractiveDecorationFamily::MightAndMagicSixTrashHeap:
            return 1748;

        case InteractiveDecorationFamily::Crystal:
            break;

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

        case InteractiveDecorationFamily::FlourSack:
            return 2;

        case InteractiveDecorationFamily::LargeBag:
            return 5;

        case InteractiveDecorationFamily::GoldBag:
            // Retain the consumed marker (5) stored by the previous shared bag binding.
            return 5;

        case InteractiveDecorationFamily::Bucket:
            return 4;

        case InteractiveDecorationFamily::MightAndMagicSixTrashHeap:
            return 2;

        case InteractiveDecorationFamily::Crystal:
            return 1;

        case InteractiveDecorationFamily::None:
            break;
    }

    return 0;
}

bool interactiveDecorationHidesWhenCleared(InteractiveDecorationFamily family)
{
    return family == InteractiveDecorationFamily::FlourSack
        || family == InteractiveDecorationFamily::LargeBag
        || family == InteractiveDecorationFamily::GoldBag
        || family == InteractiveDecorationFamily::CampFire
        || family == InteractiveDecorationFamily::Crystal;
}

std::optional<uint16_t> resolveCrystalEventId(const std::vector<std::string> &keys)
{
    if (decorationMatchesAnyKey(keys, {"crystl0"}))
    {
        return MMergeCrystalAmethystEventId;
    }

    if (decorationMatchesAnyKey(keys, {"crclstr"}))
    {
        return MMergeCrystalDiamondEventId;
    }

    if (decorationMatchesAnyKey(keys, {"crys5"}))
    {
        return MMergeCrystalRubyEventId;
    }

    if (decorationMatchesAnyKey(keys, {"crys6"}))
    {
        return MMergeCrystalSapphireEventId;
    }

    if (decorationMatchesAnyKey(keys, {"dec09"}))
    {
        return MMergeCrystalMoonstoneEventId;
    }

    if (decorationMatchesAnyKey(keys, {"dec10", "dec12"}))
    {
        return MMergeCrystalPurpleTopazEventId;
    }

    if (decorationMatchesAnyKey(keys, {"dec11"}))
    {
        return MMergeCrystalEmeraldEventId;
    }

    return std::nullopt;
}

std::optional<uint16_t> resolveCrystalEventId(
    const DecorationEntry &decoration,
    const std::string &instanceName)
{
    std::vector<std::string> keys;
    keys.reserve(2);

    const std::string hint = normalizeDecorationKey(decoration.hint);
    const std::string internalName = normalizeDecorationKey(decoration.internalName);

    if (!internalName.empty())
    {
        keys.push_back(internalName);
    }

    if (hint == "crystal")
    {
        const std::string normalizedInstanceName = normalizeDecorationKey(instanceName);

        if (!normalizedInstanceName.empty()
            && std::find(keys.begin(), keys.end(), normalizedInstanceName) == keys.end())
        {
            keys.push_back(normalizedInstanceName);
        }
    }

    return resolveCrystalEventId(keys);
}
}

const DecorationEntry *toggleableDecorationCounterpart(
    const DecorationTable &table, const DecorationEntry &decoration)
{
    const std::string name = toLowerCopy(decoration.internalName);
    const char *counterpart = nullptr;
    if (name == "brazir2f") counterpart = "brzier00";
    else if (name == "brzier00") counterpart = "brazir2f";
    else if (name == "nwtrchnf") counterpart = "TrchB00";
    else if (name == "trchb00") counterpart = "nwtrchnf";
    return counterpart != nullptr ? table.findByInternalName(counterpart) : nullptr;
}

const DecorationEntry *runtimeDecorationEntry(
    const DecorationTable &table, const DecorationEntry &decoration,
    uint32_t spriteOverrideKey, const EventRuntimeState *pState)
{
    if (pState != nullptr)
    {
        const auto override = pState->spriteOverrides.find(spriteOverrideKey);
        if (override != pState->spriteOverrides.end())
        {
            if (override->second.hidden) return nullptr;
            if (override->second.textureName)
            {
                if (const DecorationEntry *entry = table.findByInternalName(*override->second.textureName))
                {
                    return entry;
                }
            }
        }
    }
    return &decoration;
}

const DecorationEntry *indoorDecorationLightToggleTarget(
    const IndoorMapData &map, const DecorationTable &table, size_t entityIndex,
    const EventRuntimeState *pState)
{
    if (entityIndex >= map.entities.size()) return nullptr;
    const IndoorEntity &entity = map.entities[entityIndex];
    if (entity.scriptEventId() != 0) return nullptr;
    const DecorationEntry *entry = table.resolveMapDecoration(entity.decorationListId, entity.name).pEntry;
    if (entry == nullptr || toggleableDecorationCounterpart(table, *entry) == nullptr) return nullptr;
    entry = runtimeDecorationEntry(table, *entry, entity.spriteOverrideKey(entityIndex), pState);
    return entry != nullptr ? toggleableDecorationCounterpart(table, *entry) : nullptr;
}

bool toggleIndoorDecorationLight(
    const IndoorMapData &map, const DecorationTable &table, size_t entityIndex,
    EventRuntimeState &state)
{
    const DecorationEntry *target = indoorDecorationLightToggleTarget(map, table, entityIndex, &state);
    if (target == nullptr) return false;
    const IndoorEntity &entity = map.entities[entityIndex];
    state.spriteOverrides[entity.spriteOverrideKey(entityIndex)].textureName = target->internalName;
    const bool enabled = target->lightRadius > 0;
    // MMMerge associates authored lights within 100 map units on each axis with the decoration.
    for (size_t lightIndex = 0; lightIndex < map.lights.size(); ++lightIndex)
    {
        const IndoorLight &light = map.lights[lightIndex];
        if (std::abs(int64_t(light.x) - entity.x) <= 100
            && std::abs(int64_t(light.y) - entity.y) <= 100
            && std::abs(int64_t(light.z) - entity.z) <= 100)
        {
            state.indoorLightsEnabled[static_cast<uint32_t>(lightIndex)] = enabled;
        }
    }
    ++state.indoorLightRevision;
    state.lastActivationResult = enabled ? "decoration light lit" : "decoration light extinguished";
    return true;
}

std::optional<InteractiveDecorationFamily> classifyInteractiveDecorationFamily(
    const DecorationEntry &decoration,
    const std::string &instanceName)
{
    const std::vector<std::string> keys = collectDecorationKeys(decoration, instanceName);

    if (resolveCrystalEventId(decoration, instanceName))
    {
        return InteractiveDecorationFamily::Crystal;
    }

    if (decorationMatchesAnyKey(keys, {"barrel", "dec03", "dec32"}))
    {
        return InteractiveDecorationFamily::Barrel;
    }

    if (decorationMatchesAnyKey(keys, {"cauldron", "dec26"}))
    {
        return InteractiveDecorationFamily::Cauldron;
    }

    if (decorationMatchesAnyKey(keys, {"trasheap"}))
    {
        return InteractiveDecorationFamily::MightAndMagicSixTrashHeap;
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

    if (decorationMatchesAnyKey(keys, {"floursac"}))
    {
        return InteractiveDecorationFamily::FlourSack;
    }

    if (decorationMatchesAnyKey(keys, {"bag_a"}))
    {
        return InteractiveDecorationFamily::GoldBag;
    }

    if (decorationMatchesAnyKey(keys, {"bag01"}))
    {
        return InteractiveDecorationFamily::LargeBag;
    }

    if (decorationMatchesAnyKey(keys, {"bucket"}))
    {
        return InteractiveDecorationFamily::Bucket;
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
        uint16_t baseEventId = interactiveDecorationBaseEventId(*family);
        const uint8_t eventCount = interactiveDecorationEventCount(*family);

        if (*family == InteractiveDecorationFamily::Crystal)
        {
            const std::optional<uint16_t> crystalEventId = resolveCrystalEventId(decoration, instanceName);
            baseEventId = crystalEventId.value_or(0);
        }

        if (baseEventId == 0 || eventCount == 0)
        {
            return std::nullopt;
        }

        InteractiveDecorationBindingSpec spec = {};
        spec.baseEventId = baseEventId;
        spec.eventCount = eventCount;
        spec.hideWhenCleared = interactiveDecorationHidesWhenCleared(*family);
        spec.fixedEvent = *family == InteractiveDecorationFamily::GoldBag;
        spec.family = *family;
        return spec;
    }

    const std::optional<int> internalNumber = resolveDecorationInternalNumber(decoration, instanceName);

    if (!internalNumber)
    {
        return std::nullopt;
    }

    InteractiveDecorationBindingSpec spec = {};

    if ((*internalNumber >= 44 && *internalNumber <= 55)
        || (*internalNumber >= 64 && *internalNumber <= 75))
    {
        spec.baseEventId = 531;
        spec.eventCount = 12;
        spec.initialState = static_cast<uint8_t>(*internalNumber - (*internalNumber >= 64 ? 64 : 44));
        return spec;
    }

    if (*internalNumber >= 40 && *internalNumber <= 43)
    {
        spec.baseEventId = static_cast<uint16_t>(543 + (*internalNumber - 40) * 7);
        spec.eventCount = 7;
        spec.useSeededInitialState = true;
        return spec;
    }

    if (*internalNumber >= 60 && *internalNumber <= 63)
    {
        spec.baseEventId = static_cast<uint16_t>(543 + (*internalNumber - 60) * 7);
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

        case InteractiveDecorationFamily::FlourSack:
            return 1;

        case InteractiveDecorationFamily::LargeBag:
            return static_cast<uint8_t>(1u + seed % 4u);

        case InteractiveDecorationFamily::GoldBag:
            return 1;

        case InteractiveDecorationFamily::Bucket:
            return static_cast<uint8_t>(1u + seed % 3u);

        case InteractiveDecorationFamily::MightAndMagicSixTrashHeap:
            return 1;

        case InteractiveDecorationFamily::TrashHeap:
        case InteractiveDecorationFamily::CampFire:
        case InteractiveDecorationFamily::Crystal:
        case InteractiveDecorationFamily::None:
            break;
    }

    return 0;
}

namespace
{
template<typename Entity>
void initializeMapDecorations(
    std::span<const Entity> entities,
    const DecorationTable &decorationTable,
    std::array<uint8_t, 125> &decorVars,
    uint32_t randomSeed)
{
    if (std::any_of(decorVars.begin(), decorVars.end(), [](uint8_t value) { return value != 0; }))
    {
        return;
    }

    std::mt19937 rng(randomSeed);
    std::uniform_int_distribution<int> barrelContents(1, 7);
    size_t decorVarIndex = 0;

    for (size_t entityIndex = 0; entityIndex < entities.size(); ++entityIndex)
    {
        const Entity &entity = entities[entityIndex];
        if (entity.scriptEventId() != 0)
        {
            continue;
        }

        const DecorationLookupResult decoration =
            decorationTable.resolveMapDecoration(entity.decorationListId, entity.name);
        if (decoration.pEntry == nullptr)
        {
            continue;
        }

        const std::optional<InteractiveDecorationBindingSpec> spec =
            resolveInteractiveDecorationBindingSpec(*decoration.pEntry, entity.name);
        if (!spec || decorVarIndex >= decorVars.size())
        {
            continue;
        }

        uint8_t state = spec->initialState;
        const uint32_t seed = makeInteractiveDecorationSeed(
            entityIndex, entity.decorationListId, entity.x, entity.y, entity.z);
        if (spec->family == InteractiveDecorationFamily::Barrel)
        {
            state = static_cast<uint8_t>(barrelContents(rng));
        }
        else if (spec->useSeededInitialState)
        {
            state = static_cast<uint8_t>(seed % spec->eventCount);
        }
        else if (spec->family != InteractiveDecorationFamily::None)
        {
            state = initialInteractiveDecorationState(spec->family, seed);
        }

        decorVars[decorVarIndex++] = state;
    }
}
}

void initializeMapInteractiveDecorations(
    std::span<const IndoorEntity> entities,
    const DecorationTable &decorationTable,
    std::array<uint8_t, 125> &decorVars,
    uint32_t randomSeed)
{
    initializeMapDecorations(entities, decorationTable, decorVars, randomSeed);
}

void initializeMapInteractiveDecorations(
    std::span<const OutdoorEntity> entities,
    const DecorationTable &decorationTable,
    std::array<uint8_t, 125> &decorVars,
    uint32_t randomSeed)
{
    initializeMapDecorations(entities, decorationTable, decorVars, randomSeed);
}

bool interactiveDecorationIsCleared(uint8_t state, uint8_t eventCount, bool hideWhenCleared)
{
    return hideWhenCleared && eventCount != 0 && state == eventCount;
}

std::optional<uint16_t> interactiveDecorationEventId(
    uint8_t state, uint16_t baseEventId, uint8_t eventCount, bool hideWhenCleared, bool fixedEvent)
{
    if (baseEventId == 0 || eventCount == 0
        || interactiveDecorationIsCleared(state, eventCount, hideWhenCleared))
    {
        return std::nullopt;
    }

    return static_cast<uint16_t>(baseEventId + (fixedEvent || state >= eventCount ? 0 : state));
}

std::vector<bool> hiddenIndoorDecorationEntities(
    std::span<const IndoorEntity> entities, const DecorationTable &table, const EventRuntimeState &state)
{
    std::vector<bool> hidden(entities.size(), false);
    size_t decorVarIndex = 0;

    for (size_t entityIndex = 0; entityIndex < entities.size(); ++entityIndex)
    {
        const IndoorEntity &entity = entities[entityIndex];
        const auto override = state.spriteOverrides.find(entity.spriteOverrideKey(entityIndex));
        hidden[entityIndex] = override != state.spriteOverrides.end() && override->second.hidden;

        if (entity.scriptEventId() != 0)
        {
            continue;
        }

        const DecorationEntry *pDecoration = table.resolveMapDecoration(entity.decorationListId, entity.name).pEntry;
        if (pDecoration == nullptr)
        {
            continue;
        }

        const std::optional<InteractiveDecorationBindingSpec> spec =
            resolveInteractiveDecorationBindingSpec(*pDecoration, entity.name);
        if (!spec || decorVarIndex >= state.decorVars.size())
        {
            continue;
        }

        hidden[entityIndex] = hidden[entityIndex]
            || interactiveDecorationIsCleared(state.decorVars[decorVarIndex], spec->eventCount, spec->hideWhenCleared);
        ++decorVarIndex;
    }

    return hidden;
}
}
