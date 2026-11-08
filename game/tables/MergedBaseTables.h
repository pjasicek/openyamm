#pragma once

#include "game/tables/PotionEffectTable.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
// These tables are imported from the MMerge data set into OpenYAMM's shared engine/base layer.
struct MergedClassExtraEntry
{
    uint32_t classId = 0;
    uint32_t kind = 0;
    uint32_t promotionStep = 0;
    std::string note;
};

struct MergedCharacterSelectionContinent
{
    uint32_t id = 0;
    std::string key;
    std::string name;
    std::vector<uint32_t> availableClassIds;
    std::vector<uint32_t> availableRaceIds;
    std::vector<std::string> portraitExceptions;
};

struct MergedTeacherTopicEntry
{
    uint32_t topicId = 0;
    std::string note;
    uint32_t skillId = 0;
    uint32_t mastery = 0;
    uint32_t textId = 0;
    uint32_t requiredGold = 0;
    uint32_t requiredSkill = 0;
};

struct MergedNpcProfessionEntry
{
    uint32_t id = 0;
    std::string profession;
    uint32_t globalTextId = 0;
    uint32_t rarity = 0;
    uint32_t weeklyCost = 0;
    std::string personality;
    uint32_t actionTopicId = 0;
    bool joins = false;
    bool recruit = false;
    uint32_t joinTextId = 0;
    uint32_t descriptionTextId = 0;
};

struct MergedNpcBtbEntry
{
    std::string personality;
    bool acceptBeg = false;
    bool acceptBribe = false;
    bool acceptThreat = false;
    std::string creed;
    uint32_t requiredFame = 0;
    int32_t requiredReputation = 0;
    uint32_t reputationOkFirstTextId = 0;
    uint32_t reputationOkSecondTextId = 0;
    uint32_t begReturnTextId = 0;
    uint32_t bribeReturnTextId = 0;
    uint32_t threatReturnTextId = 0;
    uint32_t fameTooLowTextId = 0;
    uint32_t reputationNotoriousGoodTextId = 0;
    uint32_t reputationNotoriousEvilTextId = 0;
    uint32_t reputationSaintlyGoodTextId = 0;
    uint32_t reputationSaintlyEvilTextId = 0;
    uint32_t reputationBelowZeroFirstGoodTextId = 0;
    uint32_t reputationAboveTenFirstEvilTextId = 0;
    uint32_t lowReputationFirstGoodTextId = 0;
    uint32_t lowReputationFirstEvilTextId = 0;
    uint32_t reputationBelowZeroSecondGoodTextId = 0;
    uint32_t reputationAboveTenSecondEvilTextId = 0;
    uint32_t lowReputationSecondGoodTextId = 0;
    uint32_t lowReputationSecondEvilTextId = 0;
    uint32_t begSuccessTextId = 0;
    uint32_t begFailTextId = 0;
    uint32_t bribeSuccessTextId = 0;
    uint32_t bribeFailTextId = 0;
    uint32_t threatSuccessTextId = 0;
    uint32_t threatFailTextId = 0;
};

struct MergedNewsTopicEntry
{
    uint32_t ownerId = 0;
    uint32_t topicTextId = 0;
    uint32_t newsTextId = 0;
};

struct MergedPotionSettingEntry
{
    uint32_t potionId = 0;
    uint32_t itemId = 0;
    std::optional<uint32_t> requiredMastery;
    bool drinkable = false;
    bool usable = false;
    std::string note;
};

struct MergedReagentSettingEntry
{
    uint32_t reagentId = 0;
    uint32_t itemId = 0;
    uint32_t resultItemId = 0;
    std::string note;
};

struct MergedTeacherAutonoteMapping
{
    uint32_t topicId = 0;
    uint32_t npcId = 0;
    uint32_t autonoteId = 0;
};

struct MergedRaceSkillOverride
{
    std::string race;
    std::optional<uint32_t> raceId;
    std::string classKind;
    std::string skillName;
    std::string rawToken;
    uint32_t minMastery = 0;
    // The highest mastery the race allows (0 forbids the skill); nothing for no limit.
    std::optional<uint32_t> maxMastery;
    int32_t add = 0;
    int32_t exceptionCode = 0;
    std::string exception;
};

struct MergedNewsProfessionDayTopic
{
    uint32_t professionId = 0;
    uint32_t dayIndex = 0;
    uint32_t topicTextId = 0;
    uint32_t newsTextId = 0;
};

struct MergedAdditionalUiEntry
{
    uint32_t id = 0;
    std::string lodName;
    std::string dLodName;
    bool showBlankHostileIndicator = false;
    int32_t hostileIndicatorY = 0;
    int32_t hostileIndicatorXOffset = 0;
    bool selectionRingOnTop = false;
    int32_t selectionRingY = 0;
    int32_t selectionRingXOffset = 0;
    std::string notes;
};

struct MergedBolsterFormulaEntry
{
    std::string target;
    std::optional<uint32_t> monsterKindId;
    std::string stat;
    std::string formula;
    std::string notes;
};

struct MergedBolsterMapEntry
{
    uint32_t id = 0;
    std::string note;
    uint32_t continent = 0;
    std::string bolsterKind;
    bool spells = false;
    bool summons = false;
    bool weather = false;
    bool rain = true;
    bool snow = false;
    uint32_t bolsterExtra = 0;
    std::optional<uint32_t> professionMaxRarity;
    std::string customSky;
};

struct MergedBolsterMonsterEntry
{
    uint32_t id = 0;
    std::string note;
    std::string type;
    std::vector<std::string> extraTypes;
    std::string creed;
    std::string gender;
    std::string style;
    std::string preferredMagic;
    bool noBountyHunt = false;
    bool newRangedAttacks = false;
    bool newSpells = false;
    bool sizeAffectsHp = false;
    bool replicate = false;
    bool newSummons = false;
    std::optional<uint32_t> summonId;
    std::optional<uint32_t> extraPoints;
    std::optional<uint32_t> maxHpBoostPercent;
};

struct MergedCharacterVoiceEntry
{
    std::string soundType;
    std::vector<uint32_t> soundIdsByVoiceSetId;
    // The row's cells as written, by voice set: the sets' properties (Name, World, Man, Woman, Undead Man, ...).
    std::vector<std::string> cellsByVoiceSetId;
};

struct MergedClassStartingStatEntry
{
    std::string statName;
    std::string raceName;
    std::optional<uint32_t> raceId;
    uint32_t baseValue = 0;
    uint32_t maxValue = 0;
    uint32_t addNumerator = 0;
    uint32_t addDenominator = 1;
};

struct MergedComplexItemPictureOffsetEntry
{
    uint32_t portraitId = 0;
    uint32_t itemId = 0;
    int32_t x = 0;
    int32_t y = 0;
};

struct MergedPoint
{
    int32_t x = 0;
    int32_t y = 0;
    int32_t z = 0;
};

struct MergedComplexItemPictureEntry
{
    uint32_t id = 0;
    uint32_t itemId = 0;
    std::string notes;
    std::vector<MergedPoint> points;
};

struct MergedContinentSettingEntry
{
    uint32_t id = 0;
    std::string note;
    bool reputationAffectsGuards = false;
    bool reputationAffectsShops = false;
    bool reputationAffectsNpc = false;
    bool tellProfessionNews = false;
    bool npcFollowers = false;
    double saturation = 0.0;
    double softness = 0.0;
    std::string deathMovie;
    std::string specificWater;
    std::string deathMap1;
    int32_t deathMap1X = 0;
    int32_t deathMap1Y = 0;
    int32_t deathMap1Z = 0;
    int32_t deathMap1Direction = 0;
    std::string deathMap2;
    int32_t deathMap2X = 0;
    int32_t deathMap2Y = 0;
    int32_t deathMap2Z = 0;
    int32_t deathMap2Direction = 0;
    std::vector<std::string> skies;
    std::vector<std::string> loadingPictures;
};

struct MergedHardwareWaterTextureEntry
{
    std::string softwareTexture;
    std::string hardwareTexturePrefix;
};

struct MergedHouseExitEntry
{
    std::string mapName;
    std::vector<MergedPoint> positions;
};

struct MergedHouseExitTableData
{
    std::vector<uint32_t> npcPictureIds;
    std::optional<uint32_t> freeNpcId;
    std::optional<uint32_t> freeTopicId;
    std::vector<MergedHouseExitEntry> exits;
};

struct MergedHouseRuleSection
{
    std::string name;
    std::vector<std::vector<int32_t>> numericRows;
};

struct MergedHistoryEntry
{
    uint32_t id = 0;
    std::string text;
    std::string time;
    std::string pageTitle;
};

struct MergedOutdoorTravelDirection
{
    std::string mapName;
    std::string side;
    std::optional<uint32_t> days;
    std::string requirements;
};

struct MergedOutdoorTravelEntry
{
    std::string keyMap;
    MergedOutdoorTravelDirection up;
    MergedOutdoorTravelDirection down;
    MergedOutdoorTravelDirection left;
    MergedOutdoorTravelDirection right;
    bool straightTravel = false;
    std::string notes;
};

struct MergedOverlayEntry
{
    uint32_t id = 0;
    uint32_t type = 0;
    std::string sftGroup;
};

struct MergedTownPortalDestination
{
    uint32_t id = 0;
    uint32_t mapId = 0;
    int32_t x = 0;
    int32_t y = 0;
    int32_t z = 0;
    int32_t direction = 0;
    int32_t lookAngle = 0;
    std::string iconName;
    int32_t iconX = 0;
    int32_t iconY = 0;
    std::optional<uint32_t> iconWidth;
    std::optional<uint32_t> iconHeight;
    uint32_t qbitIndex = 0;
    std::string description;
};

struct MergedTownPortalSwitchGroup
{
    std::string name;
    uint32_t topicId = 0;
    std::vector<MergedTownPortalDestination> destinations;
};

struct MergedTransportIndexEntry
{
    uint32_t houseEventId = 0;
    std::vector<int32_t> locationIndicesByPeriod;
};

struct MergedTransportLocationEntry
{
    uint32_t id = 0;
    std::string mapName;
    std::array<bool, 7> weekdays = {};
    uint32_t daysCount = 0;
    int32_t x = 0;
    int32_t y = 0;
    int32_t z = 0;
    int32_t direction = 0;
    uint32_t qbit = 0;
};

class MergedClassExtraTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const std::vector<MergedClassExtraEntry> &entries() const;

private:
    std::vector<MergedClassExtraEntry> m_entries;
};

class MergedCharacterSelectionTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    bool loadFromYaml(const std::string &yamlText, std::string &errorMessage);
    const std::vector<std::string> *allowedClassesForRaceId(uint32_t raceId) const;
    const std::vector<MergedCharacterSelectionContinent> &continents() const;
    std::optional<std::string> raceNameForId(uint32_t raceId) const;
    size_t raceCount() const;
    // MAW's free selection (`free_selection: true`): every portrait is offered at start, whatever its "available at
    // start" mark, and the continent does not turn Clerics into Priests or Sorcerers into Necromancers.
    bool freeSelection() const;

private:
    bool m_freeSelection = false;
    std::unordered_map<uint32_t, std::vector<std::string>> m_characterSelectionAllowedClassesByRaceId;
    std::unordered_map<uint32_t, std::string> m_characterSelectionRaceNamesById;
    std::vector<MergedCharacterSelectionContinent> m_characterSelectionContinents;
};

class MergedRaceSkillTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    bool loadFromYaml(const std::string &yamlText, std::string &errorMessage);
    const std::vector<MergedRaceSkillOverride> &overrides() const;
    size_t overrideCount() const;
    // MAW's Race Skillz rules (`shift_without_class_cap: true`): the race's shift applies even when the class cannot
    // learn the skill, and the maximum and minimum clamp after it. MMMerge adds the shift only to a class cap.
    bool shiftWithoutClassCap() const;

private:
    std::vector<MergedRaceSkillOverride> m_overrides;
    bool m_shiftWithoutClassCap = false;
};

class MergedTeacherTopicTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const MergedTeacherTopicEntry *get(uint32_t topicId) const;
    const std::vector<MergedTeacherTopicEntry> &entries() const;

private:
    std::vector<MergedTeacherTopicEntry> m_entries;
    std::unordered_map<uint32_t, size_t> m_entryIndicesByTopicId;
};

class MergedTeacherAutonoteTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    std::optional<uint32_t> autonoteIdForTopicAndNpc(uint32_t topicId, uint32_t npcId) const;
    size_t mappingCount() const;

private:
    static uint64_t key(uint32_t topicId, uint32_t npcId);

    std::vector<MergedTeacherAutonoteMapping> m_mappings;
    std::unordered_map<uint64_t, uint32_t> m_autonoteIdsByTopicAndNpc;
};

class MergedNpcProfessionTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const MergedNpcProfessionEntry *get(uint32_t professionId) const;
    const std::vector<MergedNpcProfessionEntry> &entries() const;
    // "Name the Profession", as the original NameAndTitle; the plain name when the NPC has no profession.
    std::string nameAndTitle(const std::string &name, uint32_t professionId) const;

private:
    std::vector<MergedNpcProfessionEntry> m_entries;
};

class MergedNpcNameTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    size_t maleNameCount() const;
    size_t femaleNameCount() const;
    const std::vector<std::string> &maleNames() const;
    const std::vector<std::string> &femaleNames() const;

private:
    std::vector<std::string> m_npcMaleNames;
    std::vector<std::string> m_npcFemaleNames;
};

class MergedNpcBtbTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const MergedNpcBtbEntry *get(const std::string &personality) const;
    const std::vector<MergedNpcBtbEntry> &entries() const;
    size_t personalityCount() const;

private:
    std::vector<MergedNpcBtbEntry> m_entries;
};

class MergedNewsTopicTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const std::vector<MergedNewsTopicEntry> &entries() const;

private:
    std::vector<MergedNewsTopicEntry> m_entries;
};

class MergedNewsProfessionTopicTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const MergedNewsProfessionDayTopic *get(uint32_t professionId, uint32_t dayIndex) const;
    size_t topicCount() const;

private:
    std::vector<MergedNewsProfessionDayTopic> m_topics;
};

class MergedMonsterPortraitTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    std::optional<uint32_t> firstPortraitForName(const std::string &name) const;
    std::optional<uint32_t> portraitForMonsterId(uint32_t monsterId, uint64_t seed) const;
    std::optional<uint32_t> portraitForName(const std::string &name, uint64_t seed) const;
    size_t groupCount() const;

private:
    std::unordered_map<uint32_t, std::vector<uint32_t>> m_monsterPortraitsByGroupId;
    std::unordered_map<std::string, std::vector<uint32_t>> m_monsterPortraitsByName;
};

class MergedPotionSettingTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const MergedPotionSettingEntry *getByItemId(uint32_t itemId) const;
    uint32_t emptyBottleItemId() const;
    uint32_t catalystPotionItemId() const;
    const std::vector<MergedPotionSettingEntry> &entries() const;
    // What the same potion items do when drunk or applied (potion_effects.yml); the drink and mix code reach both
    // through this table.
    void setEffects(PotionEffectTable effects);
    const PotionEffectTable &effects() const;

private:
    std::vector<MergedPotionSettingEntry> m_entries;
    std::unordered_map<uint32_t, size_t> m_entryIndicesByItemId;
    PotionEffectTable m_effects;
};

class MergedReagentSettingTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    std::optional<uint32_t> resultItemIdForReagent(uint32_t itemId) const;
    const std::vector<MergedReagentSettingEntry> &entries() const;

private:
    std::vector<MergedReagentSettingEntry> m_entries;
    std::unordered_map<uint32_t, uint32_t> m_resultItemIdsByReagentItemId;
};

class MergedAdditionalUiTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const std::vector<MergedAdditionalUiEntry> &entries() const;

private:
    std::vector<MergedAdditionalUiEntry> m_entries;
};

class MergedBolsterFormulaTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const std::vector<MergedBolsterFormulaEntry> &entries() const;

private:
    std::vector<MergedBolsterFormulaEntry> m_entries;
};

class MergedBolsterMapTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const std::vector<MergedBolsterMapEntry> &entries() const;
    const MergedBolsterMapEntry *findById(uint32_t id) const;

private:
    std::vector<MergedBolsterMapEntry> m_entries;
};

class MergedBolsterMonsterTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const std::vector<MergedBolsterMonsterEntry> &entries() const;
    const MergedBolsterMonsterEntry *findById(uint32_t id) const;

private:
    std::vector<MergedBolsterMonsterEntry> m_entries;
    std::unordered_map<uint32_t, size_t> m_entryIndexById;
};

class MergedCharacterVoiceTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const std::vector<MergedCharacterVoiceEntry> &entries() const;
    std::vector<uint32_t> soundIdsForTypes(uint32_t voiceSetId, const std::vector<std::string> &soundTypes) const;
    // A voice set's cell in the named property row (Name, World, Man, Woman, Undead Man, Undead Woman), or empty.
    std::string voiceSetProperty(uint32_t voiceSetId, std::string_view rowName) const;
    // The voice sets whose World row names the world (MM9's own voices).
    std::vector<uint32_t> voiceSetsOfWorld(std::string_view worldId) const;

private:
    std::vector<MergedCharacterVoiceEntry> m_entries;
};

class MergedClassStartingStatTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const std::vector<MergedClassStartingStatEntry> &entries() const;

private:
    std::vector<MergedClassStartingStatEntry> m_entries;
};

class MergedComplexItemPictureOffsetTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const std::vector<MergedComplexItemPictureOffsetEntry> &entries() const;

private:
    std::vector<MergedComplexItemPictureOffsetEntry> m_entries;
};

class MergedComplexItemPictureTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const MergedComplexItemPictureEntry *get(uint32_t itemId) const;
    const std::vector<MergedComplexItemPictureEntry> &entries() const;

private:
    std::vector<MergedComplexItemPictureEntry> m_entries;
    std::unordered_map<uint32_t, size_t> m_entryIndicesByItemId;
};

class MergedContinentSettingTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const std::vector<MergedContinentSettingEntry> &entries() const;
    const MergedContinentSettingEntry *findById(uint32_t id) const;

private:
    std::vector<MergedContinentSettingEntry> m_entries;
};

class MergedHardwareWaterTextureTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const std::vector<MergedHardwareWaterTextureEntry> &entries() const;

private:
    std::vector<MergedHardwareWaterTextureEntry> m_entries;
};

class MergedHouseExitTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const MergedHouseExitTableData &data() const;

private:
    MergedHouseExitTableData m_data;
};

class MergedHouseRuleTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const std::vector<MergedHouseRuleSection> &sections() const;

private:
    std::vector<MergedHouseRuleSection> m_sections;
};

class MergedHistoryTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const std::vector<MergedHistoryEntry> &entries() const;

private:
    std::vector<MergedHistoryEntry> m_entries;
};

class MergedOutdoorTravelTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const std::vector<MergedOutdoorTravelEntry> &entries() const;

private:
    std::vector<MergedOutdoorTravelEntry> m_entries;
};

class MergedOverlayTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const std::vector<MergedOverlayEntry> &entries() const;

private:
    std::vector<MergedOverlayEntry> m_entries;
};

class MergedTownPortalSwitchTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const std::vector<MergedTownPortalSwitchGroup> &groups() const;

private:
    std::vector<MergedTownPortalSwitchGroup> m_groups;
};

class MergedTransportIndexTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const std::vector<MergedTransportIndexEntry> &entries() const;

private:
    std::vector<MergedTransportIndexEntry> m_entries;
};

class MergedTransportLocationTable
{
public:
    bool loadFromRows(const std::vector<std::vector<std::string>> &rows);
    const std::vector<MergedTransportLocationEntry> &entries() const;

private:
    std::vector<MergedTransportLocationEntry> m_entries;
};
}
