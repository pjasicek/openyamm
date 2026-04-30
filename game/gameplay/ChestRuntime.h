#pragma once

#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/maps/MapDeltaData.h"
#include "game/tables/MapStats.h"

#include <cstddef>
#include <cstdint>
#include <vector>

namespace OpenYAMM::Game
{
class ChestTable;
class ItemTable;
class Party;
class StandardItemEnchantTable;
class SpecialItemEnchantTable;

struct ChestTrapOpenContext
{
    float trapX = 0.0f;
    float trapY = 0.0f;
    float trapZ = 0.0f;
    float partyX = 0.0f;
    float partyY = 0.0f;
    float partyZ = 0.0f;
    uint32_t seed = 0;
};

struct ChestTrapMemberResult
{
    size_t memberIndex = 0;
    bool avoided = false;
    int damage = 0;
};

struct ChestTrapOpenResult
{
    bool shouldOpenChest = true;
    bool trapWasPresent = false;
    bool trapDisarmed = false;
    bool trapDischarged = false;
    uint16_t trapObjectId = 0;
    CombatDamageType damageType = CombatDamageType::Physical;
    int trapDamage = 0;
    std::vector<ChestTrapMemberResult> memberResults;
};

GameplayChestViewState buildMaterializedChestView(
    uint32_t chestId,
    const MapDeltaChest &chest,
    int mapTreasureLevel,
    int mapId,
    uint32_t sessionChestSeed,
    const ChestTable *pChestTable,
    const ItemTable *pItemTable,
    Party *pParty);

bool takeChestItem(GameplayChestViewState &view, size_t itemIndex, GameplayChestItemState &item);
bool takeChestItemAt(GameplayChestViewState &view, uint8_t gridX, uint8_t gridY, GameplayChestItemState &item);
bool tryPlaceChestItemAt(
    GameplayChestViewState &view,
    const GameplayChestItemState &item,
    uint8_t gridX,
    uint8_t gridY);

ChestTrapOpenResult resolveChestTrapOpen(
    const Party &party,
    const MapStatsEntry &map,
    uint16_t chestFlags,
    const ChestTrapOpenContext &context,
    const ItemTable *pItemTable,
    const StandardItemEnchantTable *pStandardItemEnchantTable,
    const SpecialItemEnchantTable *pSpecialItemEnchantTable);

void applyChestTrapOpenResultToParty(Party &party, const ChestTrapOpenResult &result);
}
