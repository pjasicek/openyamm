#pragma once

#include "game/arcomage/ArcomageTypes.h"
#include "game/events/ScriptedEventProgram.h"
#include "game/items/ItemEnchantTables.h"
#include "game/tables/CharacterDollTable.h"
#include "game/tables/ClassSkillTable.h"
#include "game/tables/HouseTable.h"
#include "game/tables/ItemTable.h"
#include "game/tables/NpcDialogTable.h"
#include "game/tables/ReadableScrollTable.h"
#include "game/tables/RosterTable.h"
#include "game/tables/SpellTable.h"

#include <optional>
#include <string>

namespace OpenYAMM::Tests
{
struct RegressionGameData
{
    Game::ArcomageLibrary arcomageLibrary = {};
    std::optional<Game::ScriptedEventProgram> globalEventProgram = std::nullopt;
    std::optional<Game::ScriptedEventProgram> out01LocalEventProgram = std::nullopt;
    Game::ItemTable itemTable = {};
    Game::StandardItemEnchantTable standardItemEnchantTable = {};
    Game::SpecialItemEnchantTable specialItemEnchantTable = {};
    Game::ReadableScrollTable readableScrollTable = {};
    Game::SpellTable spellTable = {};
    Game::CharacterDollTable characterDollTable = {};
    Game::ClassSkillTable classSkillTable = {};
    Game::HouseTable houseTable = {};
    Game::NpcDialogTable npcDialogTable = {};
    Game::RosterTable rosterTable = {};
};

bool regressionGameDataLoaded();
const std::string &regressionGameDataFailure();
const RegressionGameData &regressionGameData();
}
