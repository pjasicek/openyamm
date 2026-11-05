#pragma once

#include "game/arcomage/ArcomageTypes.h"
#include "game/events/ScriptedEventProgram.h"
#include "game/items/ItemEnchantTables.h"
#include "game/tables/CharacterDollTable.h"
#include "game/tables/ClassMultiplierTable.h"
#include "game/tables/ClassSkillTable.h"
#include "game/tables/HouseTable.h"
#include "game/tables/ItemTable.h"
#include "game/tables/MapStats.h"
#include "game/tables/MonsterTable.h"
#include "game/tables/MergedBaseTables.h"
#include "game/tables/NpcDialogTable.h"
#include "game/tables/PotionMixingTable.h"
#include "game/tables/PotionNoteTable.h"
#include "game/tables/ReadableScrollTable.h"
#include "game/tables/RosterTable.h"
#include "game/tables/SpellTable.h"
#include "game/tables/TransitionTable.h"

#include <optional>
#include <string>

namespace OpenYAMM::Tests
{
struct RegressionGameData
{
    Game::ArcomageLibrary arcomageLibrary = {};
    std::optional<Game::ScriptedEventProgram> globalEventProgram = std::nullopt;
    std::optional<Game::ScriptedEventProgram> out01LocalEventProgram = std::nullopt;
    std::optional<Game::ScriptedEventProgram> out02LocalEventProgram = std::nullopt;
    Game::ItemTable itemTable = {};
    Game::StandardItemEnchantTable standardItemEnchantTable = {};
    Game::SpecialItemEnchantTable specialItemEnchantTable = {};
    Game::PotionMixingTable potionMixingTable = {};
    Game::PotionNoteTable potionNoteTable = {};
    Game::MergedPotionSettingTable mergedPotionSettingTable = {};
    Game::MergedReagentSettingTable mergedReagentSettingTable = {};
    Game::MergedTeacherTopicTable mergedTeacherTopicTable = {};
    Game::MergedTeacherAutonoteTable mergedTeacherAutonoteTable = {};
    Game::MergedNpcProfessionTable mergedNpcProfessionTable = {};
    Game::MergedNpcNameTable mergedNpcNameTable = {};
    Game::MergedNpcBtbTable mergedNpcBtbTable = {};
    Game::MergedNewsProfessionTopicTable mergedNewsProfessionTopicTable = {};
    Game::MergedBolsterMapTable mergedBolsterMapTable = {};
    Game::MergedBolsterMonsterTable mergedBolsterMonsterTable = {};
    Game::MergedCharacterVoiceTable mergedCharacterVoiceTable = {};
    Game::MergedMonsterPortraitTable mergedMonsterPortraitTable = {};
    Game::MergedContinentSettingTable mergedContinentSettingTable = {};
    Game::ReadableScrollTable readableScrollTable = {};
    Game::SpellTable spellTable = {};
    Game::CharacterDollTable characterDollTable = {};
    Game::ClassMultiplierTable classMultiplierTable = {};
    Game::ClassSkillTable classSkillTable = {};
    Game::HouseTable houseTable = {};
    // With world ownership, edge crossings (map_navigation.txt) and the bolster maps' continents.
    Game::MapStats mapStats = {};
    Game::MonsterTable monsterTable = {};
    Game::NpcDialogTable npcDialogTable = {};
    Game::RosterTable rosterTable = {};
    Game::TransitionTable transitionTable = {};
};

bool regressionGameDataLoaded();
const std::string &regressionGameDataFailure();
const RegressionGameData &regressionGameData();
}
