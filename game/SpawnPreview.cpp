#include "game/SpawnPreview.h"

#include <array>
#include <string>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint16_t ObjectTypeSprite = 2;
constexpr uint16_t ObjectTypeActor = 3;

const MapEncounterInfo *getEncounterInfo(const MapStatsEntry &map, int encounterSlot)
{
    if (encounterSlot == 1)
    {
        return &map.encounter1;
    }

    if (encounterSlot == 2)
    {
        return &map.encounter2;
    }

    if (encounterSlot == 3)
    {
        return &map.encounter3;
    }

    return nullptr;
}

std::string buildCountText(int minCount, int maxCount)
{
    if (minCount <= 0 && maxCount <= 0)
    {
        return "0";
    }

    if (minCount == maxCount)
    {
        return std::to_string(minCount);
    }

    return std::to_string(minCount) + "-" + std::to_string(maxCount);
}
}

SpawnPreview SpawnPreviewResolver::describe(
    const MapStatsEntry &map,
    const MonsterTable *pMonsterTable,
    uint16_t typeId,
    uint16_t index,
    uint16_t attributes,
    uint32_t group
)
{
    SpawnPreview preview = {};

    const auto buildMonsterDetail = [pMonsterTable](const std::string &monsterName) -> std::string
    {
        if (pMonsterTable == nullptr)
        {
            return {};
        }

        const MonsterEntry *pMonsterEntry = pMonsterTable->findByInternalName(monsterName);

        if (pMonsterEntry == nullptr)
        {
            return {};
        }

        std::string spriteName;

        for (const std::string &candidate : pMonsterEntry->spriteNames)
        {
            if (!candidate.empty())
            {
                spriteName = candidate;
                break;
            }
        }

        return "h=" + std::to_string(pMonsterEntry->height)
            + " r=" + std::to_string(pMonsterEntry->radius)
            + " speed=" + std::to_string(pMonsterEntry->movementSpeed)
            + " sprite=" + (spriteName.empty() ? "-" : spriteName);
    };

    if (typeId == ObjectTypeActor)
    {
        preview.typeName = "actor";

        if (index >= 1 && index <= 3)
        {
            const MapEncounterInfo *pEncounter = getEncounterInfo(map, index);

            if (pEncounter != nullptr)
            {
                preview.summary =
                    "enc" + std::to_string(index) + " " + pEncounter->monsterName + " count=" +
                    buildCountText(pEncounter->minCount, pEncounter->maxCount);
                preview.detail =
                    "chance=" + std::to_string(pEncounter->chance) + "% dif=" +
                    std::to_string(pEncounter->difficulty) + " group=" + std::to_string(group) +
                    " attr=0x" + [attributes]()
                    {
                        constexpr std::array<char, 17> HexDigits = {'0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f'};
                        std::string value = "0000";
                        value[0] = HexDigits[(attributes >> 12) & 0xf];
                        value[1] = HexDigits[(attributes >> 8) & 0xf];
                        value[2] = HexDigits[(attributes >> 4) & 0xf];
                        value[3] = HexDigits[attributes & 0xf];
                        return value;
                    }();
                const std::string monsterDetail = buildMonsterDetail(pEncounter->monsterName + " A");

                if (!monsterDetail.empty())
                {
                    preview.detail += " " + monsterDetail;
                }

                return preview;
            }
        }

        if (index >= 4 && index <= 12)
        {
            const int encounterSlot = ((index - 4) % 3) + 1;
            const int tierIndex = (index - 4) / 3;
            const char tierSuffix = static_cast<char>('A' + tierIndex);
            const MapEncounterInfo *pEncounter = getEncounterInfo(map, encounterSlot);

            if (pEncounter != nullptr)
            {
                preview.summary =
                    "enc" + std::to_string(encounterSlot) + " " + pEncounter->monsterName + " " +
                    std::string(1, tierSuffix);
                preview.detail =
                    "fixed tier group=" + std::to_string(group) + " attr=0x" +
                    [attributes]()
                    {
                        constexpr std::array<char, 17> HexDigits = {'0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f'};
                        std::string value = "0000";
                        value[0] = HexDigits[(attributes >> 12) & 0xf];
                        value[1] = HexDigits[(attributes >> 8) & 0xf];
                        value[2] = HexDigits[(attributes >> 4) & 0xf];
                        value[3] = HexDigits[attributes & 0xf];
                        return value;
                    }();
                const std::string monsterDetail =
                    buildMonsterDetail(pEncounter->monsterName + " " + std::string(1, tierSuffix));

                if (!monsterDetail.empty())
                {
                    preview.detail += " " + monsterDetail;
                }

                return preview;
            }
        }

        preview.summary = "actor spawn index=" + std::to_string(index);
        preview.detail = "group=" + std::to_string(group);
        return preview;
    }

    if (typeId == ObjectTypeSprite)
    {
        preview.typeName = "sprite";
        preview.summary = "treasure level " + std::to_string(index);

        if (index == 7)
        {
            preview.summary += " (Artefact)";
        }

        preview.detail = "map treasure remaps level; group=" + std::to_string(group);
        return preview;
    }

    preview.typeName = "unknown";
    preview.summary = "type=" + std::to_string(typeId) + " index=" + std::to_string(index);
    preview.detail = "group=" + std::to_string(group);
    return preview;
}
}
