#pragma once

#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/tables/MonsterTable.h"

#include <string>

namespace OpenYAMM::Game
{
class ItemTable;
class Party;

GameplayCorpseViewState buildMonsterCorpseView(
    const std::string &title,
    const MonsterTable::LootPrototype &loot,
    const ItemTable *pItemTable,
    Party *pParty);
}
