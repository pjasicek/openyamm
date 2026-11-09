#include "game/data/GameDataRepository.h"

#include "game/data/GameDataLoader.h"

#include <algorithm>
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
    m_rulesetGuideUrl.clear();
    m_rulesetWorlds.clear();
    m_pMapStats = nullptr;
    m_pMonsterTable = nullptr;
    m_pMonsterProjectileTable = nullptr;
    m_pObjectTable = nullptr;
    m_pSpellTable = nullptr;
    m_pItemTable = nullptr;
    m_pStandardItemEnchantTable = nullptr;
    m_pSpecialItemEnchantTable = nullptr;
    m_pChestTable = nullptr;
    m_pHouseTable = nullptr;
    m_pAwardTable = nullptr;
    m_pJournalQuestTable = nullptr;
    m_pJournalHistoryTable = nullptr;
    m_pJournalAutonoteTable = nullptr;
    m_pClassMultiplierTable = nullptr;
    m_pClassSkillTable = nullptr;
    m_pNpcDialogTable = nullptr;
    m_pMm9MapTransitionTable = nullptr;
    m_pMm9TeacherScheduleTable = nullptr;
    m_pMm9RudeDialogueTable = nullptr;
    m_pMm9SkillTrainerTable = nullptr;
    m_pMm9HirelingTable = nullptr;
    m_pMm9TransportRouteTable = nullptr;
    m_pMm9QuestInteractionTable = nullptr;
    m_pRosterTable = nullptr;
    m_pCharacterDollTable = nullptr;
    m_pCharacterVoiceTable = nullptr;
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
    m_pMergedTownPortalSwitchTable = nullptr;
    m_pMergedCharacterSelectionTable = nullptr;
    m_pMergedNewsAreaTopicTable = nullptr;
    m_pMergedNewsContinentTopicTable = nullptr;
    m_pMergedNpcProfessionTable = nullptr;
    m_pMergedNpcNameTable = nullptr;
    m_pMergedNpcBtbTable = nullptr;
    m_pMergedNewsProfessionTopicTable = nullptr;
    m_pMergedBolsterMapTable = nullptr;
    m_pMergedBolsterMonsterTable = nullptr;
    m_pMergedContinentSettingTable = nullptr;
    m_pMergedMonsterPortraitTable = nullptr;
    m_pMergedPotionSettingTable = nullptr;
    m_pMawMapLevels = nullptr;
    m_pMergedReagentSettingTable = nullptr;
    m_pMergedComplexItemPictureTable = nullptr;
    m_pMergedTeacherTopicTable = nullptr;
    m_pMergedRaceSkillTable = nullptr;
    m_pMergedTeacherAutonoteTable = nullptr;
    m_pTrainerDirectory = nullptr;
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
    m_pChestTable = &loader.getChestTable();
    m_pHouseTable = &loader.getHouseTable();
    m_pAwardTable = &loader.getAwardTable();
    m_pJournalQuestTable = &loader.getJournalQuestTable();
    m_pJournalHistoryTable = &loader.getJournalHistoryTable();
    m_pJournalAutonoteTable = &loader.getJournalAutonoteTable();
    m_pClassMultiplierTable = &loader.getClassMultiplierTable();
    m_pClassSkillTable = &loader.getClassSkillTable();
    m_pNpcDialogTable = &loader.getNpcDialogTable();
    m_pMm9MapTransitionTable = &loader.getMm9MapTransitionTable();
    m_pMm9TeacherScheduleTable = &loader.getMm9TeacherScheduleTable();
    m_pMm9RudeDialogueTable = &loader.getMm9RudeDialogueTable();
    m_pMm9SkillTrainerTable = &loader.getMm9SkillTrainerTable();
    m_pMm9HirelingTable = &loader.getMm9HirelingTable();
    m_pMm9TransportRouteTable = &loader.getMm9TransportRouteTable();
    m_pMm9QuestInteractionTable = &loader.getMm9QuestInteractionTable();
    m_pRosterTable = &loader.getRosterTable();
    m_pCharacterDollTable = &loader.getCharacterDollTable();
    m_pCharacterVoiceTable = &loader.getMergedCharacterVoiceTable();
    m_pCharacterInspectTable = &loader.getCharacterInspectTable();
    m_pRaceStartingStatsTable = &loader.getRaceStartingStatsTable();
    m_pReadableScrollTable = &loader.getReadableScrollTable();
    m_pPotionMixingTable = &loader.getPotionMixingTable();
    m_pPotionNoteTable = &loader.getPotionNoteTable();
    m_pArcomageLibrary = &loader.getArcomageLibrary();
    m_pPortraitFrameTable = &loader.getPortraitFrameTable();
    m_pIconFrameTable = &loader.getIconFrameTable();
    m_pSpellFxTable = &loader.getSpellFxTable();
    m_pPortraitFxEventTable = &loader.getPortraitFxEventTable();
    m_pFaceAnimationTable = &loader.getFaceAnimationTable();
    m_pTransitionTable = &loader.getTransitionTable();
    m_pMergedTownPortalSwitchTable = &loader.getMergedTownPortalSwitchTable();
    m_pMergedCharacterSelectionTable = &loader.getMergedCharacterSelectionTable();
    m_pMergedNewsAreaTopicTable = &loader.getMergedNewsAreaTopicTable();
    m_pMergedNewsContinentTopicTable = &loader.getMergedNewsContinentTopicTable();
    m_pMergedNpcProfessionTable = &loader.getMergedNpcProfessionTable();
    m_pMergedNpcNameTable = &loader.getMergedNpcNameTable();
    m_pMergedNpcBtbTable = &loader.getMergedNpcBtbTable();
    m_pMergedNewsProfessionTopicTable = &loader.getMergedNewsProfessionTopicTable();
    m_pMergedBolsterMapTable = &loader.getMergedBolsterMapTable();
    m_pMergedBolsterMonsterTable = &loader.getMergedBolsterMonsterTable();
    m_pMergedContinentSettingTable = &loader.getMergedContinentSettingTable();
    m_pMergedMonsterPortraitTable = &loader.getMergedMonsterPortraitTable();
    m_pMergedPotionSettingTable = &loader.getMergedPotionSettingTable();
    m_pMawMapLevels = loader.mawMapLevels();
    m_pMawItemData = loader.mawItemData();
    m_pMawPromotionData = loader.mawPromotionData();
    m_pMawCraftingData = loader.mawCraftingData();
    m_pMawDimensionData = loader.mawDimensionData();
    m_pMawTextData = loader.mawTextData();
    m_rulesetGuideUrl = loader.activeRuleset().guideUrl;
    m_rulesetWorlds = loader.activeRuleset().worlds;
    m_pMergedReagentSettingTable = &loader.getMergedReagentSettingTable();
    m_pMergedComplexItemPictureTable = &loader.getMergedComplexItemPictureTable();
    m_pMergedTeacherTopicTable = &loader.getMergedTeacherTopicTable();
    m_pMergedRaceSkillTable = &loader.getMergedRaceSkillTable();
    m_pMergedTeacherAutonoteTable = &loader.getMergedTeacherAutonoteTable();
    m_pTrainerDirectory = &loader.getTrainerDirectory();
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

const ChestTable &GameDataRepository::chestTable() const
{
    return requireBound(m_pChestTable);
}

const HouseTable &GameDataRepository::houseTable() const
{
    return requireBound(m_pHouseTable);
}

const AwardTable &GameDataRepository::awardTable() const
{
    return requireBound(m_pAwardTable);
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

const Mm9MapTransitionTable &GameDataRepository::mm9MapTransitionTable() const
{
    return requireBound(m_pMm9MapTransitionTable);
}

const Mm9TeacherScheduleTable &GameDataRepository::mm9TeacherScheduleTable() const
{
    return requireBound(m_pMm9TeacherScheduleTable);
}

const Mm9RudeDialogueTable &GameDataRepository::mm9RudeDialogueTable() const
{
    return requireBound(m_pMm9RudeDialogueTable);
}

const Mm9SkillTrainerTable &GameDataRepository::mm9SkillTrainerTable() const
{
    return requireBound(m_pMm9SkillTrainerTable);
}

const Mm9HirelingTable &GameDataRepository::mm9HirelingTable() const
{
    return requireBound(m_pMm9HirelingTable);
}

const Mm9TransportRouteTable &GameDataRepository::mm9TransportRouteTable() const
{
    return requireBound(m_pMm9TransportRouteTable);
}

const Mm9QuestInteractionTable &GameDataRepository::mm9QuestInteractionTable() const
{
    return requireBound(m_pMm9QuestInteractionTable);
}

const RosterTable &GameDataRepository::rosterTable() const
{
    return requireBound(m_pRosterTable);
}

const CharacterDollTable &GameDataRepository::characterDollTable() const
{
    return requireBound(m_pCharacterDollTable);
}

const MergedCharacterVoiceTable &GameDataRepository::characterVoiceTable() const
{
    return requireBound(m_pCharacterVoiceTable);
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

const PotionNoteTable &GameDataRepository::potionNoteTable() const
{
    return requireBound(m_pPotionNoteTable);
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

const MergedTownPortalSwitchTable &GameDataRepository::mergedTownPortalSwitchTable() const
{
    return requireBound(m_pMergedTownPortalSwitchTable);
}

const MergedCharacterSelectionTable &GameDataRepository::mergedCharacterSelectionTable() const
{
    return requireBound(m_pMergedCharacterSelectionTable);
}

const MergedNewsTopicTable &GameDataRepository::mergedNewsAreaTopicTable() const
{
    return requireBound(m_pMergedNewsAreaTopicTable);
}

const MergedNewsTopicTable &GameDataRepository::mergedNewsContinentTopicTable() const
{
    return requireBound(m_pMergedNewsContinentTopicTable);
}

const MergedNpcProfessionTable &GameDataRepository::mergedNpcProfessionTable() const
{
    return requireBound(m_pMergedNpcProfessionTable);
}

const MergedNpcNameTable &GameDataRepository::mergedNpcNameTable() const
{
    return requireBound(m_pMergedNpcNameTable);
}

const MergedNpcBtbTable &GameDataRepository::mergedNpcBtbTable() const
{
    return requireBound(m_pMergedNpcBtbTable);
}

const MergedNewsProfessionTopicTable &GameDataRepository::mergedNewsProfessionTopicTable() const
{
    return requireBound(m_pMergedNewsProfessionTopicTable);
}

const MergedBolsterMapTable &GameDataRepository::mergedBolsterMapTable() const
{
    return requireBound(m_pMergedBolsterMapTable);
}

const MergedBolsterMonsterTable &GameDataRepository::mergedBolsterMonsterTable() const
{
    return requireBound(m_pMergedBolsterMonsterTable);
}

const MergedContinentSettingTable &GameDataRepository::mergedContinentSettingTable() const
{
    return requireBound(m_pMergedContinentSettingTable);
}

const MergedMonsterPortraitTable &GameDataRepository::mergedMonsterPortraitTable() const
{
    return requireBound(m_pMergedMonsterPortraitTable);
}

const MergedPotionSettingTable &GameDataRepository::mergedPotionSettingTable() const
{
    return requireBound(m_pMergedPotionSettingTable);
}

const MawMapLevels *GameDataRepository::mawMapLevels() const
{
    return m_pMawMapLevels;
}

const MawPromotionData *GameDataRepository::mawPromotionData() const
{
    return m_pMawPromotionData;
}

const MawCraftingData *GameDataRepository::mawCraftingData() const
{
    return m_pMawCraftingData;
}

const MawDimensionData *GameDataRepository::mawDimensionData() const
{
    return m_pMawDimensionData;
}

const std::string &GameDataRepository::rulesetGuideUrl() const
{
    return m_rulesetGuideUrl;
}

bool GameDataRepository::rulesetSupportsWorld(const std::string &worldId) const
{
    return m_rulesetWorlds.empty() || std::find(m_rulesetWorlds.begin(), m_rulesetWorlds.end(), worldId)
        != m_rulesetWorlds.end();
}

const MawTextData *GameDataRepository::mawTextData() const
{
    return m_pMawTextData;
}

const MawItemData *GameDataRepository::mawItemData() const
{
    return m_pMawItemData;
}

const MergedReagentSettingTable &GameDataRepository::mergedReagentSettingTable() const
{
    return requireBound(m_pMergedReagentSettingTable);
}

const MergedComplexItemPictureTable &GameDataRepository::mergedComplexItemPictureTable() const
{
    return requireBound(m_pMergedComplexItemPictureTable);
}

const MergedTeacherTopicTable &GameDataRepository::mergedTeacherTopicTable() const
{
    return requireBound(m_pMergedTeacherTopicTable);
}

const MergedRaceSkillTable &GameDataRepository::mergedRaceSkillTable() const
{
    return requireBound(m_pMergedRaceSkillTable);
}

const MergedTeacherAutonoteTable &GameDataRepository::mergedTeacherAutonoteTable() const
{
    return requireBound(m_pMergedTeacherAutonoteTable);
}

const TrainerDirectory &GameDataRepository::trainerDirectory() const
{
    return requireBound(m_pTrainerDirectory);
}
} // namespace OpenYAMM::Game
