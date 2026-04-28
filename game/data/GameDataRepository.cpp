#include "game/data/GameDataRepository.h"

#include "game/data/GameDataLoader.h"

#include <cassert>

namespace OpenYAMM::Game
{
namespace
{
template<class T>
const T &requireBound(const T *pValue)
{
    assert(pValue != nullptr);
    return *pValue;
}
}

void GameDataRepository::clear()
{
    m_pMapStats = nullptr;
    m_pMonsterTable = nullptr;
    m_pMonsterProjectileTable = nullptr;
    m_pObjectTable = nullptr;
    m_pSpellTable = nullptr;
    m_pItemTable = nullptr;
    m_pStandardItemEnchantTable = nullptr;
    m_pSpecialItemEnchantTable = nullptr;
    m_pItemEquipPosTable = nullptr;
    m_pChestTable = nullptr;
    m_pHouseTable = nullptr;
    m_pJournalQuestTable = nullptr;
    m_pJournalHistoryTable = nullptr;
    m_pJournalAutonoteTable = nullptr;
    m_pClassMultiplierTable = nullptr;
    m_pClassSkillTable = nullptr;
    m_pNpcDialogTable = nullptr;
    m_pRosterTable = nullptr;
    m_pCharacterDollTable = nullptr;
    m_pCharacterInspectTable = nullptr;
    m_pRaceStartingStatsTable = nullptr;
    m_pReadableScrollTable = nullptr;
    m_pPotionMixingTable = nullptr;
    m_pArcomageLibrary = nullptr;
    m_pPortraitFrameTable = nullptr;
    m_pIconFrameTable = nullptr;
    m_pSpellFxTable = nullptr;
    m_pPortraitFxEventTable = nullptr;
    m_pFaceAnimationTable = nullptr;
    m_pTransitionTable = nullptr;
}

void GameDataRepository::bind(const GameDataLoader &loader)
{
    m_pMapStats = &loader.getMapStats();
    m_pMonsterTable = &loader.getMonsterTable();
    m_pMonsterProjectileTable = &loader.getMonsterProjectileTable();
    m_pObjectTable = &loader.getObjectTable();
    m_pSpellTable = &loader.getSpellTable();
    m_pItemTable = &loader.getItemTable();
    m_pStandardItemEnchantTable = &loader.getStandardItemEnchantTable();
    m_pSpecialItemEnchantTable = &loader.getSpecialItemEnchantTable();
    m_pItemEquipPosTable = &loader.getItemEquipPosTable();
    m_pChestTable = &loader.getChestTable();
    m_pHouseTable = &loader.getHouseTable();
    m_pJournalQuestTable = &loader.getJournalQuestTable();
    m_pJournalHistoryTable = &loader.getJournalHistoryTable();
    m_pJournalAutonoteTable = &loader.getJournalAutonoteTable();
    m_pClassMultiplierTable = &loader.getClassMultiplierTable();
    m_pClassSkillTable = &loader.getClassSkillTable();
    m_pNpcDialogTable = &loader.getNpcDialogTable();
    m_pRosterTable = &loader.getRosterTable();
    m_pCharacterDollTable = &loader.getCharacterDollTable();
    m_pCharacterInspectTable = &loader.getCharacterInspectTable();
    m_pRaceStartingStatsTable = &loader.getRaceStartingStatsTable();
    m_pReadableScrollTable = &loader.getReadableScrollTable();
    m_pPotionMixingTable = &loader.getPotionMixingTable();
    m_pArcomageLibrary = &loader.getArcomageLibrary();
    m_pPortraitFrameTable = &loader.getPortraitFrameTable();
    m_pIconFrameTable = &loader.getIconFrameTable();
    m_pSpellFxTable = &loader.getSpellFxTable();
    m_pPortraitFxEventTable = &loader.getPortraitFxEventTable();
    m_pFaceAnimationTable = &loader.getFaceAnimationTable();
    m_pTransitionTable = &loader.getTransitionTable();
}

bool GameDataRepository::isBound() const
{
    return m_pMapStats != nullptr;
}

const MapStats &GameDataRepository::mapStats() const
{
    return requireBound(m_pMapStats);
}

const std::vector<MapStatsEntry> &GameDataRepository::mapEntries() const
{
    return mapStats().getEntries();
}

const MonsterTable &GameDataRepository::monsterTable() const
{
    return requireBound(m_pMonsterTable);
}

const MonsterProjectileTable &GameDataRepository::monsterProjectileTable() const
{
    return requireBound(m_pMonsterProjectileTable);
}

const ObjectTable &GameDataRepository::objectTable() const
{
    return requireBound(m_pObjectTable);
}

const SpellTable &GameDataRepository::spellTable() const
{
    return requireBound(m_pSpellTable);
}

const ItemTable &GameDataRepository::itemTable() const
{
    return requireBound(m_pItemTable);
}

const StandardItemEnchantTable &GameDataRepository::standardItemEnchantTable() const
{
    return requireBound(m_pStandardItemEnchantTable);
}

const SpecialItemEnchantTable &GameDataRepository::specialItemEnchantTable() const
{
    return requireBound(m_pSpecialItemEnchantTable);
}

const ItemEquipPosTable &GameDataRepository::itemEquipPosTable() const
{
    return requireBound(m_pItemEquipPosTable);
}

const ChestTable &GameDataRepository::chestTable() const
{
    return requireBound(m_pChestTable);
}

const HouseTable &GameDataRepository::houseTable() const
{
    return requireBound(m_pHouseTable);
}

const JournalQuestTable &GameDataRepository::journalQuestTable() const
{
    return requireBound(m_pJournalQuestTable);
}

const JournalHistoryTable &GameDataRepository::journalHistoryTable() const
{
    return requireBound(m_pJournalHistoryTable);
}

const JournalAutonoteTable &GameDataRepository::journalAutonoteTable() const
{
    return requireBound(m_pJournalAutonoteTable);
}

const ClassMultiplierTable &GameDataRepository::classMultiplierTable() const
{
    return requireBound(m_pClassMultiplierTable);
}

const ClassSkillTable &GameDataRepository::classSkillTable() const
{
    return requireBound(m_pClassSkillTable);
}

const NpcDialogTable &GameDataRepository::npcDialogTable() const
{
    return requireBound(m_pNpcDialogTable);
}

const RosterTable &GameDataRepository::rosterTable() const
{
    return requireBound(m_pRosterTable);
}

const CharacterDollTable &GameDataRepository::characterDollTable() const
{
    return requireBound(m_pCharacterDollTable);
}

const CharacterInspectTable &GameDataRepository::characterInspectTable() const
{
    return requireBound(m_pCharacterInspectTable);
}

const RaceStartingStatsTable &GameDataRepository::raceStartingStatsTable() const
{
    return requireBound(m_pRaceStartingStatsTable);
}

const ReadableScrollTable &GameDataRepository::readableScrollTable() const
{
    return requireBound(m_pReadableScrollTable);
}

const PotionMixingTable &GameDataRepository::potionMixingTable() const
{
    return requireBound(m_pPotionMixingTable);
}

const ArcomageLibrary &GameDataRepository::arcomageLibrary() const
{
    return requireBound(m_pArcomageLibrary);
}

const PortraitFrameTable &GameDataRepository::portraitFrameTable() const
{
    return requireBound(m_pPortraitFrameTable);
}

const IconFrameTable &GameDataRepository::iconFrameTable() const
{
    return requireBound(m_pIconFrameTable);
}

const SpellFxTable &GameDataRepository::spellFxTable() const
{
    return requireBound(m_pSpellFxTable);
}

const PortraitFxEventTable &GameDataRepository::portraitFxEventTable() const
{
    return requireBound(m_pPortraitFxEventTable);
}

const FaceAnimationTable &GameDataRepository::faceAnimationTable() const
{
    return requireBound(m_pFaceAnimationTable);
}

const TransitionTable &GameDataRepository::transitionTable() const
{
    return requireBound(m_pTransitionTable);
}
} // namespace OpenYAMM::Game
