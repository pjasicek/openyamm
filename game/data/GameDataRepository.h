#pragma once

#include "game/arcomage/ArcomageTypes.h"
#include "game/items/ItemEnchantTables.h"
#include "game/items/ItemEquipPosTable.h"
#include "game/tables/CharacterDollTable.h"
#include "game/tables/CharacterInspectTable.h"
#include "game/tables/ChestTable.h"
#include "game/tables/ClassSkillTable.h"
#include "game/tables/FaceAnimationTable.h"
#include "game/tables/HouseTable.h"
#include "game/tables/IconFrameTable.h"
#include "game/tables/ItemTable.h"
#include "game/tables/JournalAutonoteTable.h"
#include "game/tables/JournalHistoryTable.h"
#include "game/tables/JournalQuestTable.h"
#include "game/tables/MapStats.h"
#include "game/tables/MonsterProjectileTable.h"
#include "game/tables/MonsterTable.h"
#include "game/tables/NpcDialogTable.h"
#include "game/tables/ObjectTable.h"
#include "game/tables/PortraitFrameTable.h"
#include "game/tables/PortraitFxEventTable.h"
#include "game/tables/PotionMixingTable.h"
#include "game/tables/RaceStartingStatsTable.h"
#include "game/tables/ReadableScrollTable.h"
#include "game/tables/RosterTable.h"
#include "game/tables/SpellTable.h"
#include "game/tables/SpellFxTable.h"
#include "game/tables/TransitionTable.h"

#include <vector>

namespace OpenYAMM::Game
{
class GameDataLoader;

class GameDataRepository
{
public:
    void clear();
    void bind(const GameDataLoader &loader);
    bool isBound() const;

    const MapStats &mapStats() const;
    const std::vector<MapStatsEntry> &mapEntries() const;
    const MonsterTable &monsterTable() const;
    const MonsterProjectileTable &monsterProjectileTable() const;
    const ObjectTable &objectTable() const;
    const SpellTable &spellTable() const;
    const ItemTable &itemTable() const;
    const StandardItemEnchantTable &standardItemEnchantTable() const;
    const SpecialItemEnchantTable &specialItemEnchantTable() const;
    const ItemEquipPosTable &itemEquipPosTable() const;
    const ChestTable &chestTable() const;
    const HouseTable &houseTable() const;
    const JournalQuestTable &journalQuestTable() const;
    const JournalHistoryTable &journalHistoryTable() const;
    const JournalAutonoteTable &journalAutonoteTable() const;
    const ClassSkillTable &classSkillTable() const;
    const NpcDialogTable &npcDialogTable() const;
    const RosterTable &rosterTable() const;
    const CharacterDollTable &characterDollTable() const;
    const CharacterInspectTable &characterInspectTable() const;
    const RaceStartingStatsTable &raceStartingStatsTable() const;
    const ReadableScrollTable &readableScrollTable() const;
    const PotionMixingTable &potionMixingTable() const;
    const ArcomageLibrary &arcomageLibrary() const;
    const PortraitFrameTable &portraitFrameTable() const;
    const IconFrameTable &iconFrameTable() const;
    const SpellFxTable &spellFxTable() const;
    const PortraitFxEventTable &portraitFxEventTable() const;
    const FaceAnimationTable &faceAnimationTable() const;
    const TransitionTable &transitionTable() const;

private:
    const MapStats *m_pMapStats = nullptr;
    const MonsterTable *m_pMonsterTable = nullptr;
    const MonsterProjectileTable *m_pMonsterProjectileTable = nullptr;
    const ObjectTable *m_pObjectTable = nullptr;
    const SpellTable *m_pSpellTable = nullptr;
    const ItemTable *m_pItemTable = nullptr;
    const StandardItemEnchantTable *m_pStandardItemEnchantTable = nullptr;
    const SpecialItemEnchantTable *m_pSpecialItemEnchantTable = nullptr;
    const ItemEquipPosTable *m_pItemEquipPosTable = nullptr;
    const ChestTable *m_pChestTable = nullptr;
    const HouseTable *m_pHouseTable = nullptr;
    const JournalQuestTable *m_pJournalQuestTable = nullptr;
    const JournalHistoryTable *m_pJournalHistoryTable = nullptr;
    const JournalAutonoteTable *m_pJournalAutonoteTable = nullptr;
    const ClassSkillTable *m_pClassSkillTable = nullptr;
    const NpcDialogTable *m_pNpcDialogTable = nullptr;
    const RosterTable *m_pRosterTable = nullptr;
    const CharacterDollTable *m_pCharacterDollTable = nullptr;
    const CharacterInspectTable *m_pCharacterInspectTable = nullptr;
    const RaceStartingStatsTable *m_pRaceStartingStatsTable = nullptr;
    const ReadableScrollTable *m_pReadableScrollTable = nullptr;
    const PotionMixingTable *m_pPotionMixingTable = nullptr;
    const ArcomageLibrary *m_pArcomageLibrary = nullptr;
    const PortraitFrameTable *m_pPortraitFrameTable = nullptr;
    const IconFrameTable *m_pIconFrameTable = nullptr;
    const SpellFxTable *m_pSpellFxTable = nullptr;
    const PortraitFxEventTable *m_pPortraitFxEventTable = nullptr;
    const FaceAnimationTable *m_pFaceAnimationTable = nullptr;
    const TransitionTable *m_pTransitionTable = nullptr;
};
} // namespace OpenYAMM::Game
