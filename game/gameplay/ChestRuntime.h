#pragma once

#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/maps/MapDeltaData.h"

#include <cstdint>

namespace OpenYAMM::Game
{
class ChestTable;
class ItemTable;
class Party;

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
}
