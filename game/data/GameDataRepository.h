#pragma once

#include "game/arcomage/ArcomageTypes.h"
#include "game/gameplay/TrainerDirectory.h"
#include "game/items/ItemEnchantTables.h"
#include "game/mm9/Mm9MapTransition.h"
#include "game/mm9/Mm9TeacherSchedule.h"
#include "game/mm9/Mm9QuestMarkers.h"
#include "game/mm9/Mm9RudeDialogue.h"
#include "game/mm9/Mm9SkillTrainer.h"
#include "game/mm9/Mm9TransportRoute.h"
#include "game/tables/CharacterDollTable.h"
#include "game/tables/CharacterInspectTable.h"
#include "game/tables/AwardTable.h"
#include "game/tables/ChestTable.h"
#include "game/tables/ClassMultiplierTable.h"
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
#include "game/tables/MergedBaseTables.h"
#include "game/tables/NpcDialogTable.h"
#include "game/tables/ObjectTable.h"
#include "game/tables/PortraitFrameTable.h"
#include "game/tables/PortraitFxEventTable.h"
#include "game/tables/PotionMixingTable.h"
#include "game/tables/PotionNoteTable.h"
#include "game/tables/RaceStartingStatsTable.h"
#include "game/tables/ReadableScrollTable.h"
#include "game/tables/RosterTable.h"
#include "game/tables/SpellTable.h"
#include "game/tables/SpellFxTable.h"
#include "game/tables/TransitionTable.h"

#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class GameDataLoader;
class MawItemData;
struct MawPromotionData;
class MawCraftingData;
class MawDimensionData;
class MawTextData;
class MawMapLevels;

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
    const ChestTable &chestTable() const;
    const HouseTable &houseTable() const;
    const AwardTable &awardTable() const;
    const JournalQuestTable &journalQuestTable() const;
    const JournalHistoryTable &journalHistoryTable() const;
    const JournalAutonoteTable &journalAutonoteTable() const;
    const ClassMultiplierTable &classMultiplierTable() const;
    const ClassSkillTable &classSkillTable() const;
    const NpcDialogTable &npcDialogTable() const;
    const Mm9MapTransitionTable &mm9MapTransitionTable() const;
    const Mm9TeacherScheduleTable &mm9TeacherScheduleTable() const;
    const Mm9RudeDialogueTable &mm9RudeDialogueTable() const;
    const Mm9SkillTrainerTable &mm9SkillTrainerTable() const;
    const Mm9TransportRouteTable &mm9TransportRouteTable() const;
    const Mm9QuestInteractionTable &mm9QuestInteractionTable() const;
    const RosterTable &rosterTable() const;
    const CharacterDollTable &characterDollTable() const;
    const CharacterInspectTable &characterInspectTable() const;
    const RaceStartingStatsTable &raceStartingStatsTable() const;
    const ReadableScrollTable &readableScrollTable() const;
    const PotionMixingTable &potionMixingTable() const;
    const PotionNoteTable &potionNoteTable() const;
    const ArcomageLibrary &arcomageLibrary() const;
    const PortraitFrameTable &portraitFrameTable() const;
    const IconFrameTable &iconFrameTable() const;
    const SpellFxTable &spellFxTable() const;
    const PortraitFxEventTable &portraitFxEventTable() const;
    const FaceAnimationTable &faceAnimationTable() const;
    const TransitionTable &transitionTable() const;
    const MergedTownPortalSwitchTable &mergedTownPortalSwitchTable() const;
    const MergedCharacterSelectionTable &mergedCharacterSelectionTable() const;
    const MergedNewsTopicTable &mergedNewsAreaTopicTable() const;
    const MergedNewsTopicTable &mergedNewsContinentTopicTable() const;
    const MergedNpcProfessionTable &mergedNpcProfessionTable() const;
    const MergedNpcNameTable &mergedNpcNameTable() const;
    const MergedNpcBtbTable &mergedNpcBtbTable() const;
    const MergedNewsProfessionTopicTable &mergedNewsProfessionTopicTable() const;
    const MergedBolsterMapTable &mergedBolsterMapTable() const;
    const MergedBolsterMonsterTable &mergedBolsterMonsterTable() const;
    const MergedContinentSettingTable &mergedContinentSettingTable() const;
    const MergedMonsterPortraitTable &mergedMonsterPortraitTable() const;
    const MergedPotionSettingTable &mergedPotionSettingTable() const;
    // The address of the active ruleset's player's guide (`guide_url`), empty for none.
    const std::string &rulesetGuideUrl() const;
    // Null unless the MAW ruleset is active.
    const MawMapLevels *mawMapLevels() const;
    const MawItemData *mawItemData() const;
    const MawPromotionData *mawPromotionData() const;
    const MawCraftingData *mawCraftingData() const;
    const MawDimensionData *mawDimensionData() const;
    const MawTextData *mawTextData() const;
    const MergedReagentSettingTable &mergedReagentSettingTable() const;
    const MergedComplexItemPictureTable &mergedComplexItemPictureTable() const;
    const MergedTeacherTopicTable &mergedTeacherTopicTable() const;
    const MergedRaceSkillTable &mergedRaceSkillTable() const;
    const MergedTeacherAutonoteTable &mergedTeacherAutonoteTable() const;
    const TrainerDirectory &trainerDirectory() const;

private:
    const MapStats *m_pMapStats = nullptr;
    const MonsterTable *m_pMonsterTable = nullptr;
    const MonsterProjectileTable *m_pMonsterProjectileTable = nullptr;
    const ObjectTable *m_pObjectTable = nullptr;
    const SpellTable *m_pSpellTable = nullptr;
    const ItemTable *m_pItemTable = nullptr;
    const StandardItemEnchantTable *m_pStandardItemEnchantTable = nullptr;
    const SpecialItemEnchantTable *m_pSpecialItemEnchantTable = nullptr;
    const ChestTable *m_pChestTable = nullptr;
    const HouseTable *m_pHouseTable = nullptr;
    const AwardTable *m_pAwardTable = nullptr;
    const JournalQuestTable *m_pJournalQuestTable = nullptr;
    const JournalHistoryTable *m_pJournalHistoryTable = nullptr;
    const JournalAutonoteTable *m_pJournalAutonoteTable = nullptr;
    const ClassMultiplierTable *m_pClassMultiplierTable = nullptr;
    const ClassSkillTable *m_pClassSkillTable = nullptr;
    const NpcDialogTable *m_pNpcDialogTable = nullptr;
    const Mm9MapTransitionTable *m_pMm9MapTransitionTable = nullptr;
    const Mm9TeacherScheduleTable *m_pMm9TeacherScheduleTable = nullptr;
    const Mm9RudeDialogueTable *m_pMm9RudeDialogueTable = nullptr;
    const Mm9SkillTrainerTable *m_pMm9SkillTrainerTable = nullptr;
    const Mm9TransportRouteTable *m_pMm9TransportRouteTable = nullptr;
    const Mm9QuestInteractionTable *m_pMm9QuestInteractionTable = nullptr;
    const RosterTable *m_pRosterTable = nullptr;
    const CharacterDollTable *m_pCharacterDollTable = nullptr;
    const CharacterInspectTable *m_pCharacterInspectTable = nullptr;
    const RaceStartingStatsTable *m_pRaceStartingStatsTable = nullptr;
    const ReadableScrollTable *m_pReadableScrollTable = nullptr;
    const PotionMixingTable *m_pPotionMixingTable = nullptr;
    const PotionNoteTable *m_pPotionNoteTable = nullptr;
    const ArcomageLibrary *m_pArcomageLibrary = nullptr;
    const PortraitFrameTable *m_pPortraitFrameTable = nullptr;
    const IconFrameTable *m_pIconFrameTable = nullptr;
    const SpellFxTable *m_pSpellFxTable = nullptr;
    const PortraitFxEventTable *m_pPortraitFxEventTable = nullptr;
    const FaceAnimationTable *m_pFaceAnimationTable = nullptr;
    const TransitionTable *m_pTransitionTable = nullptr;
    const MergedTownPortalSwitchTable *m_pMergedTownPortalSwitchTable = nullptr;
    const MergedCharacterSelectionTable *m_pMergedCharacterSelectionTable = nullptr;
    const MergedNewsTopicTable *m_pMergedNewsAreaTopicTable = nullptr;
    const MergedNewsTopicTable *m_pMergedNewsContinentTopicTable = nullptr;
    const MergedNpcProfessionTable *m_pMergedNpcProfessionTable = nullptr;
    const MergedNpcNameTable *m_pMergedNpcNameTable = nullptr;
    const MergedNpcBtbTable *m_pMergedNpcBtbTable = nullptr;
    const MergedNewsProfessionTopicTable *m_pMergedNewsProfessionTopicTable = nullptr;
    const MergedBolsterMapTable *m_pMergedBolsterMapTable = nullptr;
    const MergedBolsterMonsterTable *m_pMergedBolsterMonsterTable = nullptr;
    const MergedContinentSettingTable *m_pMergedContinentSettingTable = nullptr;
    const MergedMonsterPortraitTable *m_pMergedMonsterPortraitTable = nullptr;
    const MergedPotionSettingTable *m_pMergedPotionSettingTable = nullptr;
    const MawMapLevels *m_pMawMapLevels = nullptr;
    const MawItemData *m_pMawItemData = nullptr;
    const MawPromotionData *m_pMawPromotionData = nullptr;
    const MawCraftingData *m_pMawCraftingData = nullptr;
    const MawDimensionData *m_pMawDimensionData = nullptr;
    const MawTextData *m_pMawTextData = nullptr;
    std::string m_rulesetGuideUrl;
    const MergedReagentSettingTable *m_pMergedReagentSettingTable = nullptr;
    const MergedComplexItemPictureTable *m_pMergedComplexItemPictureTable = nullptr;
    const MergedTeacherTopicTable *m_pMergedTeacherTopicTable = nullptr;
    const MergedRaceSkillTable *m_pMergedRaceSkillTable = nullptr;
    const MergedTeacherAutonoteTable *m_pMergedTeacherAutonoteTable = nullptr;
    const TrainerDirectory *m_pTrainerDirectory = nullptr;
};
} // namespace OpenYAMM::Game
