#include "game/gameplay/GenericActorDialog.h"

#include "game/events/EvtEnums.h"
#include "game/tables/MergedBaseTables.h"
#include "game/tables/MapStats.h"
#include "game/tables/NpcDialogTable.h"

#include <algorithm>
#include <array>
#include <charconv>
#include <cmath>
#include <cstdlib>
#include <limits>
#include <random>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t FirstGeneratedNpcId = 1184;
constexpr uint32_t LastGeneratedNpcId = 1223;
constexpr char NpcRosterSeedVariable[] = "MMerge.RandomNPC.Seed";
constexpr char NpcRosterRefillVariable[] = "MMerge.RandomNPC.RefillMinutes";
constexpr int32_t MinutesPerMonth = 28 * 24 * 60;

uint64_t fnv1a64(const std::string &text)
{
    uint64_t hash = 14695981039346656037ull;

    for (char character : text)
    {
        hash ^= static_cast<uint8_t>(character);
        hash *= 1099511628211ull;
    }

    return hash;
}

uint32_t findNpcIdByName(const NpcDialogTable &npcDialogTable, const std::string &name)
{
    const NpcEntry *pNpcEntry = npcDialogTable.findNpcByName(name);
    return pNpcEntry != nullptr ? pNpcEntry->id : 0;
}

uint32_t resolveActorPortraitId(
    const MergedMonsterPortraitTable *pMonsterPortraitTable,
    const std::string &actorName,
    const std::string &actorKey,
    uint32_t actorMonsterId,
    uint32_t rosterSeed = 0)
{
    if (pMonsterPortraitTable == nullptr)
    {
        return 0;
    }

    const uint64_t seed = fnv1a64(actorKey) ^ rosterSeed;
    const std::optional<uint32_t> monsterPortrait =
        pMonsterPortraitTable->portraitForMonsterId(actorMonsterId, seed);

    if (monsterPortrait.has_value())
    {
        return *monsterPortrait;
    }

    return pMonsterPortraitTable->portraitForName(actorName, seed).value_or(0);
}

std::string generatedActorKey(
    const std::string &mapFileName,
    uint32_t actorGroup,
    const std::string &actorName,
    std::optional<size_t> actorIndex)
{
    return mapFileName + "#" + std::to_string(actorIndex.value_or(static_cast<size_t>(actorGroup)))
        + "#" + std::to_string(actorGroup) + "#" + actorName;
}

bool isGeneratedNpcSlot(uint32_t npcId)
{
    return npcId >= FirstGeneratedNpcId && npcId <= LastGeneratedNpcId;
}

uint32_t chooseGeneratedNpcId(const EventRuntimeState &runtimeState, const std::string &actorKey)
{
    const std::unordered_map<std::string, uint32_t>::const_iterator existingIt =
        runtimeState.generatedNpcIdsByActorKey.find(actorKey);

    if (existingIt != runtimeState.generatedNpcIdsByActorKey.end() && isGeneratedNpcSlot(existingIt->second))
    {
        if (runtimeState.unavailableNpcIds.contains(existingIt->second))
        {
            return 0;
        }

        return existingIt->second;
    }

    std::array<bool, LastGeneratedNpcId - FirstGeneratedNpcId + 1> usedSlots = {};

    for (const auto &[existingActorKey, npcId] : runtimeState.generatedNpcIdsByActorKey)
    {
        static_cast<void>(existingActorKey);

        if (isGeneratedNpcSlot(npcId))
        {
            usedSlots[npcId - FirstGeneratedNpcId] = true;
        }
    }

    const size_t slotCount = usedSlots.size();
    const size_t startSlot = static_cast<size_t>(fnv1a64(actorKey) % slotCount);

    for (size_t offset = 0; offset < slotCount; ++offset)
    {
        const size_t slot = (startSlot + offset) % slotCount;
        const uint32_t npcId = FirstGeneratedNpcId + static_cast<uint32_t>(slot);

        if (!usedSlots[slot] && !runtimeState.unavailableNpcIds.contains(npcId))
        {
            return npcId;
        }
    }

    return 0;
}

const MergedBolsterMapEntry *currentBolsterMapEntry(
    const MapStatsEntry *pCurrentMap,
    const MergedBolsterMapTable *pBolsterMapTable)
{
    if (pCurrentMap == nullptr || pBolsterMapTable == nullptr || pCurrentMap->id < 0)
    {
        return nullptr;
    }

    return pBolsterMapTable->findById(static_cast<uint32_t>(pCurrentMap->id));
}

std::optional<uint32_t> generatedProfessionId(
    const std::string &actorKey,
    const MergedNpcProfessionTable &professionTable,
    uint32_t maxRarity,
    uint32_t rosterSeed)
{
    std::vector<uint32_t> candidateIds;

    for (const MergedNpcProfessionEntry &entry : professionTable.entries())
    {
        if (entry.id != 0 && entry.rarity <= maxRarity)
        {
            candidateIds.push_back(entry.id);
        }
    }

    if (candidateIds.empty())
    {
        return std::nullopt;
    }

    return candidateIds[(fnv1a64(actorKey + "#profession") ^ rosterSeed) % candidateIds.size()];
}

std::string generatedNpcName(
    const std::string &actorKey,
    const MergedNpcNameTable &nameTable,
    const MergedBolsterMonsterEntry *pBolsterMonster,
    uint32_t rosterSeed)
{
    const bool useFemaleName = pBolsterMonster != nullptr
        ? pBolsterMonster->gender == "F"
        : (fnv1a64(actorKey + "#gender") % 2u) != 0;
    const std::vector<std::string> &names = useFemaleName ? nameTable.femaleNames() : nameTable.maleNames();

    if (names.empty())
    {
        return {};
    }

    return names[(fnv1a64(actorKey + "#name") ^ rosterSeed) % names.size()];
}

bool canGenerateNpcFromBolsterMonster(const MergedBolsterMonsterEntry *pBolsterMonster)
{
    // MMerge's NPCNewsTopics.lua only randomizes profession NPCs from bolster monsters with peasant creed.
    return pBolsterMonster != nullptr && pBolsterMonster->creed == "Peasant";
}

std::optional<GenericActorDialogResolution> resolveGeneratedActorDialog(
    const std::string &mapFileName,
    const std::string &actorName,
    uint32_t actorGroup,
    const EventRuntimeState &runtimeState,
    const MergedMonsterPortraitTable *pMonsterPortraitTable,
    const MapStatsEntry *pCurrentMap,
    const MergedNpcNameTable *pNpcNameTable,
    const MergedNpcProfessionTable *pNpcProfessionTable,
    const MergedBolsterMapTable *pBolsterMapTable,
    const MergedBolsterMonsterTable *pBolsterMonsterTable,
    uint32_t actorMonsterId,
    std::optional<size_t> actorIndex)
{
    const MergedBolsterMapEntry *pBolsterEntry = currentBolsterMapEntry(pCurrentMap, pBolsterMapTable);

    if (pNpcNameTable == nullptr
        || pNpcProfessionTable == nullptr
        || pBolsterEntry == nullptr
        || !pBolsterEntry->professionMaxRarity.has_value()
        || *pBolsterEntry->professionMaxRarity == 0)
    {
        return std::nullopt;
    }

    const MergedBolsterMonsterEntry *pBolsterMonster =
        pBolsterMonsterTable != nullptr ? pBolsterMonsterTable->findById(actorMonsterId) : nullptr;

    if (!canGenerateNpcFromBolsterMonster(pBolsterMonster))
    {
        return std::nullopt;
    }

    const std::string actorKey = generatedActorKey(mapFileName, actorGroup, actorName, actorIndex);
    const uint32_t npcId = chooseGeneratedNpcId(runtimeState, actorKey);

    if (npcId == 0 || runtimeState.unavailableNpcIds.contains(npcId))
    {
        return std::nullopt;
    }

    GenericActorDialogResolution resolution = {};
    resolution.npcId = npcId;
    resolution.opensNpcTalk = true;
    resolution.generatedNpc = true;
    resolution.generatedActorKey = actorKey;

    if (runtimeState.generatedNpcIdsByActorKey.contains(actorKey))
    {
        const auto nameIt = runtimeState.npcNameOverrides.find(npcId);
        const auto pictureIt = runtimeState.npcPictureOverrides.find(npcId);
        const auto professionIt = runtimeState.npcProfessionOverrides.find(npcId);
        if (nameIt == runtimeState.npcNameOverrides.end()
            || pictureIt == runtimeState.npcPictureOverrides.end()
            || professionIt == runtimeState.npcProfessionOverrides.end())
        {
            return std::nullopt;
        }
        resolution.generatedName = nameIt->second;
        resolution.portraitPictureId = pictureIt->second;
        resolution.generatedProfessionId = professionIt->second;
    }
    else
    {
        const auto seedIt = runtimeState.namedMapVars.find(NpcRosterSeedVariable);
        const uint32_t rosterSeed = seedIt != runtimeState.namedMapVars.end() ? seedIt->second : 0;
        const std::optional<uint32_t> professionId = generatedProfessionId(
            actorKey, *pNpcProfessionTable, *pBolsterEntry->professionMaxRarity, rosterSeed);
        resolution.generatedName = generatedNpcName(actorKey, *pNpcNameTable, pBolsterMonster, rosterSeed);
        if (!professionId || resolution.generatedName.empty())
        {
            return std::nullopt;
        }
        resolution.generatedProfessionId = *professionId;
        resolution.portraitPictureId =
            resolveActorPortraitId(pMonsterPortraitTable, actorName, actorKey, actorMonsterId, rosterSeed);
    }
    return resolution;
}

std::string resolveGenericNpcName(const std::string &actorName, uint32_t actorGroup)
{
    if (actorName == "Lizardman Peasant")
    {
        return "Lizardman Peasant";
    }

    if (actorName == "Lizardman Villager")
    {
        return "Lizardman Peasant";
    }

    if ((actorName == "Swordsman" || actorName == "Guard" || actorName == "Adventurer")
        && actorGroup >= 54
        && actorGroup <= 60)
    {
        return "Guard";
    }

    if (actorName == "Lizardman Guard"
        || actorName == "Lizardman Soldier"
        || actorName == "Lizardman Warrior"
        || actorName == "Lizardman Lookout")
    {
        return "Lizardman Guard";
    }

    if (actorName == "Dark Elf Peasant")
    {
        return "Dark Elf Peasant";
    }

    if (actorName == "Dark Elf Guard")
    {
        return "Dark Elf Guard";
    }

    if (actorName == "Ogre Peasant")
    {
        return "Ogre Peasant";
    }

    if (actorName == "Wererat Peasant" || actorName == "Wererat Peasants")
    {
        return "Wererat Peasants";
    }

    if (actorName == "Troll Peasant")
    {
        return "Troll Peasant";
    }

    if (actorName == "Dragon Hunter")
    {
        return "Dragon Hunter";
    }

    if (actorName == "Necromancer Peasant")
    {
        return "Necromancer Peasant";
    }

    if (actorName == "Cleric Peasant")
    {
        return "Cleric Peasant";
    }

    if (actorName == "Regnan Peasant" || actorName == "Pirate")
    {
        return "Regnan Peasant";
    }

    if (actorName == "Minotaur Peasant")
    {
        return "Minotaur Peasant";
    }

    switch (actorGroup)
    {
        case 1:
        case 3:
            return "Lizardman Peasant";

        case 2:
        case 9:
            return "Lizardman Guard";

        case 5:
        case 6:
        case 7:
        case 16:
        case 17:
        case 18:
            return "Dark Elf Peasant";

        case 8:
            return "Wererat Peasants";

        case 19:
        case 20:
        case 21:
            return "Troll Peasant";

        case 22:
        case 23:
        case 24:
            return "Dragon Hunter";

        case 25:
        case 26:
        case 27:
            return "Necromancer Peasant";

        case 28:
        case 29:
            return "Cleric Peasant";

        case 32:
        case 33:
        case 34:
            return "Regnan Peasant";

        case 35:
        case 36:
        case 37:
            return "Minotaur Peasant";

        default:
            return {};
    }
}

std::optional<uint32_t> firstMapAreaNewsId(
    const MapStatsEntry *pCurrentMap,
    const MergedNewsTopicTable *pNewsAreaTopicTable)
{
    if (pCurrentMap == nullptr || pNewsAreaTopicTable == nullptr)
    {
        return std::nullopt;
    }

    const uint32_t mapId = static_cast<uint32_t>(std::max(pCurrentMap->id, 0));

    for (const MergedNewsTopicEntry &entry : pNewsAreaTopicTable->entries())
    {
        if (entry.ownerId == mapId && entry.newsTextId != 0)
        {
            return entry.newsTextId;
        }
    }

    return std::nullopt;
}

std::optional<uint32_t> firstContinentNewsId(
    const MapStatsEntry *pCurrentMap,
    const MergedNewsTopicTable *pNewsContinentTopicTable)
{
    if (pCurrentMap == nullptr || pNewsContinentTopicTable == nullptr || pCurrentMap->mergedContinentId == 0)
    {
        return std::nullopt;
    }

    for (const MergedNewsTopicEntry &entry : pNewsContinentTopicTable->entries())
    {
        if (entry.ownerId == pCurrentMap->mergedContinentId && entry.newsTextId != 0)
        {
            return entry.newsTextId;
        }
    }

    return std::nullopt;
}

bool isPlaceholderGroupNews(uint32_t newsId)
{
    // MMerge uses this as a default "change me" entry for many imported MM6/MM7 peasant groups.
    return newsId == 51;
}
}

void refreshGenericActorNpcRoster(EventRuntimeState &runtimeState, float gameMinutes)
{
    const int32_t currentMinute = std::max(0, int32_t(std::floor(gameMinutes)));
    const auto refillIt = runtimeState.namedMapVars.find(NpcRosterRefillVariable);
    if (refillIt != runtimeState.namedMapVars.end()
        && int64_t(currentMinute) <= int64_t(refillIt->second) + MinutesPerMonth)
    {
        return;
    }

    for (auto actorIt = runtimeState.generatedNpcIdsByActorKey.begin();
         actorIt != runtimeState.generatedNpcIdsByActorKey.end();)
    {
        const uint32_t npcId = actorIt->second;
        if (runtimeState.unavailableNpcIds.contains(npcId))
        {
            ++actorIt;
            continue;
        }
        runtimeState.npcNameOverrides.erase(npcId);
        runtimeState.npcPictureOverrides.erase(npcId);
        runtimeState.npcProfessionOverrides.erase(npcId);
        runtimeState.npcGreetingDisplayCounts.erase(npcId);
        actorIt = runtimeState.generatedNpcIdsByActorKey.erase(actorIt);
    }

    std::random_device randomDevice;
    std::uniform_int_distribution<int32_t> seedDistribution(1, std::numeric_limits<int32_t>::max());
    runtimeState.namedMapVars[NpcRosterSeedVariable] = seedDistribution(randomDevice);
    runtimeState.namedMapVars[NpcRosterRefillVariable] = currentMinute;
}

std::optional<GenericActorDialogResolution> resolveGenericActorDialog(
    const std::string &mapFileName,
    const std::string &actorName,
    uint32_t actorGroup,
    const EventRuntimeState &runtimeState,
    const NpcDialogTable &npcDialogTable,
    const MergedMonsterPortraitTable *pMonsterPortraitTable,
    const MapStatsEntry *pCurrentMap,
    const MergedNewsTopicTable *pNewsAreaTopicTable,
    const MergedNewsTopicTable *pNewsContinentTopicTable,
    const MergedNpcNameTable *pNpcNameTable,
    const MergedNpcProfessionTable *pNpcProfessionTable,
    const MergedBolsterMapTable *pBolsterMapTable,
    const MergedBolsterMonsterTable *pBolsterMonsterTable,
    uint32_t actorMonsterId,
    std::optional<size_t> actorIndex
)
{
    const std::string genericNpcName = resolveGenericNpcName(actorName, actorGroup);
    const uint32_t genericNpcId = findNpcIdByName(npcDialogTable, genericNpcName);

    const auto seedIt = runtimeState.namedMapVars.find(NpcRosterSeedVariable);
    const bool randomizedRoster = seedIt != runtimeState.namedMapVars.end() && seedIt->second != 0;
    if (genericNpcId == 0 || randomizedRoster)
    {
        const std::optional<GenericActorDialogResolution> generatedResolution =
            resolveGeneratedActorDialog(
                mapFileName,
                actorName,
                actorGroup,
                runtimeState,
                pMonsterPortraitTable,
                pCurrentMap,
                pNpcNameTable,
                pNpcProfessionTable,
                pBolsterMapTable,
                pBolsterMonsterTable,
                actorMonsterId,
                actorIndex);

        if (generatedResolution.has_value())
        {
            return generatedResolution;
        }
    }

    uint32_t newsId = 0;
    const std::unordered_map<uint32_t, uint32_t>::const_iterator overrideIt =
        runtimeState.npcGroupNews.find(actorGroup);

    if (overrideIt != runtimeState.npcGroupNews.end())
    {
        newsId = overrideIt->second;
    }
    else
    {
        const std::optional<uint32_t> defaultNewsId = npcDialogTable.getNewsIdForGroup(actorGroup);

        if (defaultNewsId)
        {
            newsId = *defaultNewsId;
        }
    }

    if (isPlaceholderGroupNews(newsId))
    {
        newsId = 0;
    }

    if (newsId == 0)
    {
        newsId = firstMapAreaNewsId(pCurrentMap, pNewsAreaTopicTable).value_or(0);
    }

    if (newsId == 0)
    {
        newsId = firstContinentNewsId(pCurrentMap, pNewsContinentTopicTable).value_or(0);
    }

    if (newsId == 0 || !npcDialogTable.getNewsDialogText(newsId))
    {
        return std::nullopt;
    }

    GenericActorDialogResolution resolution = {};
    resolution.npcId = genericNpcId;
    resolution.newsId = newsId;
    resolution.portraitPictureId = resolveActorPortraitId(
        pMonsterPortraitTable,
        actorName,
        generatedActorKey(mapFileName, actorGroup, actorName, actorIndex),
        actorMonsterId);
    return resolution;
}

void applyGenericActorDialogResolution(
    EventRuntimeState &runtimeState,
    const GenericActorDialogResolution &resolution
)
{
    if (!resolution.generatedNpc || resolution.npcId == 0)
    {
        return;
    }

    runtimeState.generatedNpcIdsByActorKey[resolution.generatedActorKey] = resolution.npcId;
    runtimeState.npcNameOverrides[resolution.npcId] = resolution.generatedName;
    runtimeState.npcPictureOverrides[resolution.npcId] = resolution.portraitPictureId;
    runtimeState.npcProfessionOverrides[resolution.npcId] = resolution.generatedProfessionId;
}

std::optional<std::string> generatedNpcGroupNewsText(
    const EventRuntimeState &runtimeState,
    const NpcDialogTable &npcDialogTable,
    uint32_t npcId,
    const MapStatsEntry *pCurrentMap)
{
    for (const auto &[actorKey, mappedNpcId] : runtimeState.generatedNpcIdsByActorKey)
    {
        if (mappedNpcId != npcId
            || (pCurrentMap != nullptr && !actorKey.starts_with(pCurrentMap->fileName + "#")))
        {
            continue;
        }

        // The saved actor identity is map#actor-index#group#actor-name.
        const size_t mapEnd = actorKey.find('#');
        const size_t actorEnd = mapEnd != std::string::npos ? actorKey.find('#', mapEnd + 1) : std::string::npos;
        const size_t groupEnd = actorEnd != std::string::npos ? actorKey.find('#', actorEnd + 1) : std::string::npos;
        if (groupEnd == std::string::npos)
        {
            return std::nullopt;
        }

        uint32_t groupId = 0;
        const std::from_chars_result parsed = std::from_chars(
            actorKey.data() + actorEnd + 1, actorKey.data() + groupEnd, groupId);
        if (parsed.ec != std::errc() || parsed.ptr != actorKey.data() + groupEnd || groupId == 0)
        {
            return std::nullopt;
        }

        const auto overrideIt = runtimeState.npcGroupNews.find(groupId);
        const uint32_t newsId = overrideIt != runtimeState.npcGroupNews.end()
            ? overrideIt->second
            : npcDialogTable.getNewsIdForGroup(groupId).value_or(0);
        return newsId != 0 && !isPlaceholderGroupNews(newsId)
            ? npcDialogTable.getNewsText(newsId)
            : std::nullopt;
    }

    return std::nullopt;
}

bool hideGeneratedNpcActor(
    EventRuntimeState &runtimeState,
    uint32_t npcId,
    const MapStatsEntry *pCurrentMap
)
{
    if (npcId == 0 || pCurrentMap == nullptr || pCurrentMap->fileName.empty())
    {
        return false;
    }

    const std::string keyPrefix = pCurrentMap->fileName + "#";

    for (const auto &[actorKey, mappedNpcId] : runtimeState.generatedNpcIdsByActorKey)
    {
        if (mappedNpcId != npcId || actorKey.rfind(keyPrefix, 0) != 0)
        {
            continue;
        }

        const size_t actorIndexBegin = keyPrefix.size();
        const size_t actorIndexEnd = actorKey.find('#', actorIndexBegin);

        if (actorIndexEnd == std::string::npos || actorIndexEnd == actorIndexBegin)
        {
            continue;
        }

        const uint32_t actorIndex = static_cast<uint32_t>(
            std::strtoul(actorKey.substr(actorIndexBegin, actorIndexEnd - actorIndexBegin).c_str(), nullptr, 10));
        return hideMapActorByIndex(runtimeState, actorIndex);
    }

    return false;
}

bool hideMapActorByIndex(EventRuntimeState &runtimeState, uint32_t actorIndex)
{
    const uint32_t invisibleBit = static_cast<uint32_t>(EvtActorAttribute::Invisible);
    runtimeState.actorSetMasks[actorIndex] |= invisibleBit;
    runtimeState.actorClearMasks[actorIndex] &= ~invisibleBit;

    if (runtimeState.actorClearMasks[actorIndex] == 0)
    {
        runtimeState.actorClearMasks.erase(actorIndex);
    }

    return true;
}
}
