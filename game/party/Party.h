#pragma once

#include "game/audio/SoundIds.h"
#include "game/gameplay/NpcFollowerTypes.h"
#include "game/items/ItemEnchantTables.h"
#include "game/outdoor/OutdoorMovementDriver.h"
#include "game/party/CharacterRulesetState.h"
#include "game/party/CharacterState.h"
#include "game/party/InventoryItem.h"
#include "game/party/QuickItemSlot.h"
#include "game/party/SpeechIds.h"
#include "game/tables/ClassSkillTable.h"
#include "game/tables/MonsterShields.h"
#include "game/tables/PortraitEnums.h"

#include <array>
#include <bitset>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Game
{
enum class CombatDamageType;
class ItemTable;
struct GameRules;
struct MonsterKillReward;
struct ItemDefinition;
class CharacterDollTable;
class ClassMultiplierTable;
class JournalQuestTable;
struct RosterEntry;
struct EventRuntimeState;
class StandardItemEnchantTable;
class SpecialItemEnchantTable;
class TrainerDirectory;

// A pin on the journal map of mapFileName (lowercase); ids are unique within one map.
struct JournalMapNote
{
    uint32_t id = 0;
    int32_t x = 0;
    int32_t y = 0;
    std::string mapFileName;
    std::string text;
    // Teacher pins without an autonote of their own also appear in the journal's trainer notes.
    bool listedWithTrainerNotes = false;
    // The player's own note (right click on the journal map): editable and removable there, ids from
    // PersonalJournalMapNoteIdBase.
    bool personal = false;
};

// Personal journal map notes take ids from here up, clear of event and quest pins.
constexpr uint32_t PersonalJournalMapNoteIdBase = 1000000;

struct LloydBeacon
{
    std::string mapName;
    std::string locationName;
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    float directionDegrees = 0.0f;
    float remainingSeconds = 0.0f;
    int previewWidth = 0;
    int previewHeight = 0;
    std::vector<uint8_t> previewPixelsBgra;
};

struct TimedPrimaryStatBonus
{
    int power = 0;
    float remainingSeconds = 0.0f;
};

// Ages are counted from this year: a character born in it is 0 years old (birthYear).
constexpr int CharacterAgeReferenceYear = 1168;
// MMMerge's extra quick spell slots per character (ExtraQuickSpells.lua SlotsAmount).
constexpr size_t ExtraQuickSpellSlotCount = 4;

struct Character
{
    static constexpr int InventoryWidth = 14;
    static constexpr int InventoryHeight = 9;

    std::string name;
    std::string role;
    std::string className;
    std::string portraitTextureName;
    uint32_t portraitPictureId = 0;
    PortraitId portraitState = PortraitId::Normal;
    uint32_t portraitElapsedTicks = 0;
    uint32_t portraitDurationTicks = 0;
    uint32_t portraitSequenceCounter = 0;
    uint16_t portraitImageIndex = 0;
    uint32_t rosterId = 0;
    uint32_t characterDataId = 0;
    int32_t voiceId = -1;
    uint32_t birthYear = 0;
    uint32_t sexId = 0;
    uint32_t raceId = 0;
    // 64 bits: MAW levels need more than 4 billion (level 1064); the rules cap it (ExperienceRules::maximumExperience).
    uint64_t experience = 0;
    uint32_t level = 1;
    uint32_t skillPoints = 0;
    // Raises technology skills only (Engrams add them); skill points cannot raise technology skills.
    uint32_t techPoints = 0;
    // Implant item ids in the four sockets (0: empty). Cybernetics opens them: Novice one, Grandmaster all four
    // (implantSocketCount). Hesper's implants; saved.
    std::array<uint32_t, 4> implants = {};
    uint32_t might = 0;
    uint32_t intellect = 0;
    uint32_t personality = 0;
    uint32_t endurance = 0;
    uint32_t speed = 0;
    uint32_t accuracy = 0;
    uint32_t luck = 0;
    int maxHealth = 100;
    int health = 100;
    int maxSpellPoints = 0;
    int spellPoints = 0;
    uint8_t armageddonCastsToday = 0;
    std::string quickSpellName;
    // MMMerge's four extra quick spells (ExtraQuickSpells.lua), set in the spellbook, cast by Quick Spell 1-4.
    std::array<std::string, ExtraQuickSpellSlotCount> extraQuickSpellNames;
    // The potion radial's six slots (QuickItemSlots): a kind of potion or scroll each.
    std::array<QuickItemSlot, QuickItemSlotCount> quickItemSlots = {};
    std::string attackSpellName;
    // The spellbook page the character last had open (a SpellbookSchool), or -1 before the first; it opens there.
    int32_t spellbookSchool = -1;
    std::unordered_set<uint32_t> knownSpellIds;
    CharacterResistanceSet baseResistances = {};
    CharacterStatBonuses permanentBonuses = {};
    CharacterStatBonuses temporaryEventBonuses = {};
    CharacterStatBonuses magicalBonuses = {};
    CharacterResistanceImmunitySet permanentImmunities = {};
    CharacterResistanceImmunitySet magicalImmunities = {};
    std::bitset<CharacterConditionCount> permanentConditionImmunities = {};
    std::bitset<CharacterConditionCount> magicalConditionImmunities = {};
    CharacterEquipment equipment = {};
    CharacterEquipmentRuntimeState equipmentRuntime = {};
    std::bitset<CharacterConditionCount> conditions = {};
    std::array<float, CharacterConditionCount> conditionStartGameMinutes = {};
    std::unordered_map<std::string, CharacterSkill> skills;
    std::unordered_set<uint32_t> awards;
    std::unordered_map<uint16_t, int32_t> eventVariables;
    float recoverySecondsRemaining = 0.0f;
    int armorClassModifier = 0;
    int levelModifier = 0;
    int ageModifier = 0;
    std::unordered_set<uint32_t> playerBits;
    uint32_t npcs2 = 0;
    int merchantBonus = 0;
    // The member's Glamour (the spell, a potion or an event's), also counted in merchantBonus; MAW weighs its power by
    // its mastery.
    int glamourPower = 0;
    SkillMastery glamourMastery = SkillMastery::None;
    int weaponEnchantmentDamageBonus = 0;
    float vampiricHealFraction = 0.0f;
    bool physicalAttackDisabled = false;
    bool physicalDamageImmune = false;
    bool halfMissileDamage = false;
    int meleeArmorClassBonus = 0;
    int missileArmorClassBonus = 0;
    int magicArmorClassBonus = 0;
    float physicalDamageTakenMultiplier = 1.0f;
    // The share of physical hits Mist Form lets through where the rules make it a cut, not immunity (MAW 0.25).
    float mistFormPhysicalShare = 1.0f;
    // Ruleset item immunities to monster attacks that are not conditions (MAW's paired immunity specials).
    bool manaDrainImmune = false;
    bool agingImmune = false;
    // Rulesets that keep item resistance enchantments apart from the resistances (MAW): the best one per element.
    CharacterResistanceSet itemResistanceEnchants = {};
    float experienceGainMultiplier = 1.0f;
    float randomEncounterChanceMultiplier = 1.0f;
    bool waterWalking = false;
    bool featherFalling = false;
    float healthRegenPerSecond = 0.0f;
    float spellRegenPerSecond = 0.0f;
    float healthRegenAccumulator = 0.0f;
    float spellRegenAccumulator = 0.0f;
    // Personal energy shield (COMBAT.md, Party shields): pool points from equipped items' personal_shield, emitters
    // (Shield Tech items) apart as they grow with Shield Tech. Runtime only: recomputed with the equipment and full
    // after a load.
    int armorShieldPoints = 0;
    int emitterShieldPoints = 0;
    int personalShieldCapacity = 0;
    float personalShield = 0.0f;
    float personalShieldSecondsSinceDamage = 0.0f;
    float personalShieldSecondsSinceBreak = -1.0f;
    bool personalShieldInitialized = false;
    // A Shield Cell's temporary shield on a member without one: its points (part of the capacity) and time left.
    int temporaryShieldPoints = 0;
    float temporaryShieldSecondsRemaining = 0.0f;
    // Energy resistance from equipped items (item_effects energy_resistance); runtime, rebuilt with the equipment.
    int energyResistance = 0;
    // A world's own weapon enchantments (WorldEnchantEffect) of the melee and the ranged weapon worn; runtime, rebuilt
    // with the equipment.
    WorldEnchantEffect meleeWeaponEnchant;
    WorldEnchantEffect rangedWeaponEnchant;
    // The rest of Hesper's item effects (ItemContentEffect), summed over equipment and implants; runtime, rebuilt with
    // the equipment.
    float shieldRegenDelaySeconds = 0.0f;
    int humPoints = 0;
    int rangedDamagePercent = 0;
    int meleeDamagePercent = 0;
    int spellDamagePercent = 0;
    int energyDamageTakenPercent = 0;
    int gunRecoveryReductionTicks = 0;
    int meleeRecoveryReductionTicks = 0;
    int attackRecoveryReductionTicks = 0;
    float recoveryProgressMultiplier = 1.0f;
    std::unordered_map<std::string, int> itemSkillBonuses;
    std::unordered_map<std::string, int> hiredNpcSkillBonuses;
    std::unordered_set<std::string> equippedItemEffectFlags;
    std::array<std::optional<LloydBeacon>, 5> lloydsBeacons = {};

    // Implant sockets Cybernetics opens: one per mastery (Novice 1, Grandmaster 4), none without the skill.
    size_t implantSocketCount() const;
    // The Augment row shows: the character has Cybernetics or an implant (never in MM6-MM8).
    bool showsImplantSockets() const;

    bool addInventoryItem(const InventoryItem &item);
    bool addInventoryItemAt(const InventoryItem &item, uint8_t gridX, uint8_t gridY);
    bool removeInventoryItem(uint32_t objectDescriptionId, uint32_t quantity = 1);
    const InventoryItem *inventoryItemAt(uint8_t gridX, uint8_t gridY) const;
    bool takeInventoryItemAt(uint8_t gridX, uint8_t gridY, InventoryItem &item);
    bool tryPlaceInventoryItemAt(
        const InventoryItem &item,
        uint8_t gridX,
        uint8_t gridY,
        std::optional<InventoryItem> &replacedItem);
    size_t inventoryItemCount() const;
    size_t usedInventoryCells() const;
    size_t inventoryCapacity() const;
    bool hasSkill(const std::string &skillName) const;
    bool hasCanonicalSkill(const std::string &canonicalSkillName) const;
    const CharacterSkill *findSkill(const std::string &skillName) const;
    const CharacterSkill *findSkillByCanonicalName(const std::string &canonicalSkillName) const;
    CharacterSkill *findSkill(const std::string &skillName);
    CharacterSkill *findSkillByCanonicalName(const std::string &canonicalSkillName);
    int skillBonus(const std::string &skillName) const;
    // The pool that raises this skill: tech points for technology skills, skill points otherwise.
    uint32_t pointsForRaisingSkill(const std::string &skillName) const;
    bool hasTechnologySkill() const;
    bool setSkillMastery(const std::string &skillName, SkillMastery mastery);
    void synchronizeInnateAbilitySpells();
    bool knowsSpell(uint32_t spellId) const;
    bool learnSpell(uint32_t spellId);
    bool forgetSpell(uint32_t spellId);

    std::vector<InventoryItem> inventory;
    std::array<TimedPrimaryStatBonus, 6> timedPrimaryStatBonuses = {};
    CharacterRulesetState rulesetState;
};

struct AdventurersInnMember
{
    Character character = {};
    uint32_t portraitPictureId = 0;
};

struct PartySeed
{
    std::vector<Character> members;
    std::vector<InventoryItem> inventory;
    int gold = 0;
    int food = 0;
};

enum class PartyBuffId : uint8_t
{
    TorchLight = 0,
    WizardEye,
    FeatherFall,
    DetectLife,
    WaterWalk,
    Fly,
    Invisibility,
    Stoneskin,
    DayOfGods,
    ProtectionFromMagic,
    FireResistance,
    WaterResistance,
    AirResistance,
    EarthResistance,
    MindResistance,
    BodyResistance,
    Shield,
    Heroism,
    Haste,
    Immolation,
    Glamour,
    Levitate,
    Count,
};

static constexpr size_t PartyBuffCount = static_cast<size_t>(PartyBuffId::Count);

enum class CharacterBuffId : uint8_t
{
    Bless = 0,
    Fate,
    Preservation,
    Regeneration,
    Hammerhands,
    PainReflection,
    FireAura,
    VampiricWeapon,
    Mistform,
    Glamour,
    // Potion buffs on the drinker only, as MM8 keeps them; they add to the party spells of the same kind.
    Haste,
    Heroism,
    Shield,
    Stoneskin,
    WaterBreathing,
    TempMight,
    TempIntellect,
    TempPersonality,
    TempEndurance,
    TempSpeed,
    TempAccuracy,
    TempLuck,
    FireResistance,
    AirResistance,
    WaterResistance,
    EarthResistance,
    MindResistance,
    BodyResistance,
    Count,
};

static constexpr size_t CharacterBuffCount = static_cast<size_t>(CharacterBuffId::Count);
// Character buffs stored by saves before the potion buffs were added.
static constexpr size_t LegacyCharacterBuffCount = static_cast<size_t>(CharacterBuffId::Haste);

struct PartyBuffState
{
    float remainingSeconds = 0.0f;
    uint32_t spellId = 0;
    uint32_t skillLevel = 0;
    SkillMastery skillMastery = SkillMastery::None;
    int power = 0;
    uint32_t casterMemberIndex = 0;

    bool active() const
    {
        return remainingSeconds > 0.0f;
    }
};

struct CharacterBuffState
{
    float remainingSeconds = 0.0f;
    float periodicAccumulatorSeconds = 0.0f;
    uint32_t spellId = 0;
    uint32_t skillLevel = 0;
    SkillMastery skillMastery = SkillMastery::None;
    int power = 0;
    uint32_t casterMemberIndex = 0;

    bool active() const
    {
        return remainingSeconds > 0.0f;
    }
};

// A story the party finished (world.yml completion; "grand" for every world of the grand certificate), recorded once
// when its certificate is given.
struct WorldCompletionRecord
{
    std::string certificateId;
    float gameMinutes = 0.0f;
    uint64_t score = 0;
    // Real time of the completion, seconds since 1970.
    int64_t completedAtUnixSeconds = 0;
    // False for a story finished before the game kept these records: no time, score or certificate.
    bool timed = true;
};

class Party
{
public:
    struct HouseStockState
    {
        uint32_t houseId = 0;
        float nextRefreshGameMinutes = 0.0f;
        uint32_t refreshSequence = 0;
        uint32_t generationVersion = 0;
        std::vector<InventoryItem> standardStock;
        std::vector<InventoryItem> specialStock;
        // A guild's shelves, one per school it teaches (HouseServiceRuntime::spellbookShelfSchools), one after another.
        std::vector<InventoryItem> spellbookStock;
    };

    struct Snapshot
    {
        std::vector<Character> members;
        std::vector<AdventurersInnMember> adventurersInnMembers;
        size_t activeMemberIndex = 0;
        std::array<PartyBuffState, PartyBuffCount> partyBuffs = {};
        std::array<std::array<CharacterBuffState, CharacterBuffCount>, 5> characterBuffs = {};
        int gold = 0;
        int bankGold = 0;
        int food = 0;
        int fineGold = 0;
        uint32_t waterDamageTicks = 0;
        uint32_t burningDamageTicks = 0;
        uint32_t splashCount = 0;
        uint32_t landingSoundCount = 0;
        uint32_t hardLandingSoundCount = 0;
        uint32_t monsterTargetSelectionCounter = 0;
        uint32_t houseStockSeed = 0;
        float itemEffectElapsedGameSeconds = 0.0f;
        uint32_t itemWeeklyEffectSequence = 0;
        float lastFallDamageDistance = 0.0f;
        int daysWithoutRest = 0;
        std::optional<int> awakeDayIndex;
        std::unordered_set<uint32_t> foundArtifactItems;
        std::unordered_set<uint32_t> arcomageWonHouseIds;
        std::vector<WorldCompletionRecord> worldCompletions;
        // A save from before the completion records: the stories it already finished get untimed records, no
        // certificate (CompletionCertificates::recordNewCompletions).
        bool worldCompletionsUntracked = false;
        uint32_t arcomageWinCount = 0;
        uint32_t arcomageLossCount = 0;
        std::vector<HouseStockState> houseStockStates;
        std::unordered_set<uint32_t> everOwnedItemIds;
        // MM9 talk rows the party has chosen (rude id << 32 | row index): the conversation bar's visited marks.
        std::unordered_set<uint64_t> chosenMm9RudeRows;
        // The continents whose Ledger of Teachers the party bought in a tavern (TrainerDirectory.h).
        std::unordered_set<uint32_t> teacherLedgers;
        std::unordered_map<uint32_t, int32_t> continentReputations;
        std::unordered_set<uint32_t> questBits;
        std::unordered_set<uint32_t> autonotes;
        // History entry id -> game minute it was recorded, per history continent.
        std::unordered_map<uint32_t, std::unordered_map<uint32_t, int32_t>> historyEventTimesByContinent;
        std::vector<JournalMapNote> journalMapNotes;
        std::unordered_map<uint16_t, int32_t> eventVariables;
        std::unordered_map<uint32_t, std::unordered_map<uint32_t, uint32_t>> npcTopicOverrides;
        std::unordered_map<uint32_t, uint32_t> npcGroupNews;
        std::unordered_map<uint32_t, uint32_t> npcGreetingOverrides;
        std::unordered_map<uint32_t, uint32_t> npcGreetingDisplayCounts;
        std::unordered_map<uint32_t, uint32_t> npcHouseOverrides;
        std::unordered_map<uint32_t, uint32_t> npcItemOverrides;
        std::unordered_set<uint32_t> unavailableNpcIds;
        std::vector<HiredNpcFollower> hiredNpcFollowers;
        // Potion pairs (target << 32 | held) that exploded when mixed, so the alchemy bench can warn.
        std::unordered_set<uint64_t> explosiveMixes;
    };

    struct PendingAudioRequest
    {
        enum class Kind : uint8_t
        {
            Sound,
            Speech,
        };

        Kind kind = Kind::Sound;
        SoundId soundId = SoundId::None;
        SpeechId speechId = SpeechId::None;
        size_t memberIndex = 0;
    };

    static PartySeed createDefaultSeed();

    void setItemTable(const ItemTable *pItemTable);
    // Regeneration and Shield Tech rules of the personal energy shields (the worlds' shields.yml; defaults without).
    void setPersonalShieldRules(const PartyShieldRules *pRules);
    const PartyShieldRules &personalShieldRules() const;

    struct PersonalShieldHit
    {
        // Damage left once the shield breaks (none while it holds).
        int passedDamage = 0;
        bool absorbed = false;
        bool broke = false;
    };
    // The member's raised personal shield takes the hit first; a member without one passes the whole damage.
    PersonalShieldHit absorbPersonalShieldHit(size_t memberIndex, int damage);
    // Shield Cell: refills the member's personal shield; a member without one gets the rules' temporary shield
    // (PartyShieldRules::shieldCellPoints for shieldCellSeconds). Runtime only, like the shields themselves.
    bool chargePersonalShield(size_t memberIndex);
    // Shield Burst Cell: every member's shield gains the rules' share of its pool; false when nobody has a shield.
    bool burstPersonalShields();
    void setJournalQuestTable(const JournalQuestTable *pJournalQuestTable);
    void setCharacterDollTable(const CharacterDollTable *pCharacterDollTable);
    void setItemEnchantTables(
        const StandardItemEnchantTable *pStandardItemEnchantTable,
        const SpecialItemEnchantTable *pSpecialItemEnchantTable);
    const ItemTable *itemTable() const;
    const JournalQuestTable *journalQuestTable() const;
    const StandardItemEnchantTable *standardItemEnchantTable() const;
    const SpecialItemEnchantTable *specialItemEnchantTable() const;
    size_t equippedItemSetPieceCount(size_t memberIndex, const std::string &setId) const;
    int32_t eventVariableValue(uint16_t variableId) const;
    void setEventVariableValue(uint16_t variableId, int32_t value);
    void addEventVariableValue(uint16_t variableId, int32_t value);
    void subtractEventVariableValue(uint16_t variableId, int32_t value);
    int fineGold() const;
    void addFineGold(int amount);
    void clearFineGold();
    int32_t continentReputation(uint32_t continentId) const;
    void setContinentReputation(uint32_t continentId, int32_t value);
    void setClassMultiplierTable(const ClassMultiplierTable *pClassMultiplierTable);
    const ClassMultiplierTable *classMultiplierTable() const;
    void setClassSkillTable(const ClassSkillTable *pClassSkillTable);
    // The active ruleset's rules, owned by the session; Standard until set.
    void setRules(const GameRules *pRules);
    // A ruleset's slow on the party's movement, set each frame (MAW's dimension affix 25 while enemies are near).
    // 1: none; not saved.
    void setRulesMovementMultiplier(float multiplier);
    float rulesMovementMultiplier() const;
    const GameRules &rules() const;
    const ClassSkillTable *classSkillTable() const;
    // Every skill teacher (the journal's trainer finder, the Ledger of Teachers, the trainer hints).
    void setTrainerDirectory(const TrainerDirectory *pTrainerDirectory);
    const TrainerDirectory *trainerDirectory() const;
    Snapshot snapshot() const;
    void restoreSnapshot(const Snapshot &snapshot);
    void reset();
    void seed(const PartySeed &seed);
    void applyMovementEffects(const OutdoorMovementEffects &effects);
    void applyEventRuntimeState(const EventRuntimeState &runtimeState, bool grantItemsToInventory = true);
    void setDebugDamageImmune(bool enabled);
    void setDebugUnlimitedMana(bool enabled);
    bool applyDamageToMember(
        size_t memberIndex,
        int damage,
        const std::string &status,
        bool allowUnconscious = false);
    bool applyDamageToActiveMember(int damage, const std::string &status);
    bool applyPotionExplosionToMember(size_t memberIndex, uint8_t damageLevel);
    bool applyDamageToAllLivingMembers(int damage, const std::string &status);
    uint64_t addExperienceToMember(size_t memberIndex, int64_t amount);
    uint64_t setMemberExperience(size_t memberIndex, uint64_t experience);
    uint32_t grantSharedExperience(uint32_t totalExperience);
    // Shares the experience for killing a monster under the experience rules; returns the amount before sharing.
    uint32_t grantMonsterKillExperience(const MonsterKillReward &kill);
    std::optional<size_t> chooseMonsterAttackTarget(uint32_t attackPreferences, uint32_t seedHint);
    void addGold(int amount);
    void addFood(int amount);
    void requestSound(SoundId soundId);
    void requestDamageImpactSoundForMember(size_t memberIndex);
    void requestSpeech(size_t memberIndex, SpeechId speechId);
    bool hasQuestBit(uint32_t questBitId) const;
    // The Hum where the party is (world.yml hum, set on each map load): its nodes' QBits and shares, and the map's own
    // share if it has one (0: a null field). spellDamagePercentFor: the caster's share of a damage spell's damage
    // (the Hum, raised by its Hum points to at most 100); castingBlockedFor: a null field without a Null Damper II.
    void setSpellField(std::vector<uint32_t> humQBits, std::vector<int> humPercents, std::optional<int> mapPercent);
    // A burning floor where the party is (world.yml floorBurn, set on each map load): its damage type and whether the
    // members' resistances cut it. MM: Fire, unresisted. A FireImmune item spares its wearer a Fire floor either way.
    void setFloorBurn(CombatDamageType type, bool resisted);
    // The world's major objectives (world.yml objectives, set on each map load) and how many of their QBits are set.
    void setObjectiveQBits(std::vector<uint32_t> qbits);
    size_t objectivesDone() const;
    int spellDamagePercentFor(const Character &caster) const;
    bool castingBlockedFor(const Character &caster) const;
    void setQuestBit(uint32_t questBitId, bool value);
    bool hasAutonote(uint32_t autonoteId) const;
    void setAutonote(uint32_t autonoteId, bool value);
    const std::unordered_map<uint32_t, int32_t> &historyEventTimes(uint32_t continentId) const;
    void recordHistoryEvent(uint32_t continentId, uint32_t historyId, int32_t gameMinutes);
    void clearHistoryEvent(uint32_t continentId, uint32_t historyId);
    const std::vector<JournalMapNote> &journalMapNotes() const;
    const JournalMapNote *findJournalMapNote(const std::string &mapFileName, uint32_t noteId) const;
    // Adds the note, or replaces the one with the same map and id.
    void setJournalMapNote(const JournalMapNote &note);
    // Removes the note with this map and id; false when there is none.
    bool removeJournalMapNote(const std::string &mapFileName, uint32_t noteId);
    uint64_t dialogueEligibilityRevision() const;
    void applyGlobalNpcStateTo(EventRuntimeState &runtimeState) const;
    void setNpcTopicOverride(uint32_t npcId, uint32_t topicSlotIndex, uint32_t topicId);
    void setNpcGroupNews(uint32_t groupId, uint32_t newsId);
    void setNpcGreetingOverride(uint32_t npcId, uint32_t greetingId);
    void setNpcHouseOverride(uint32_t npcId, uint32_t houseId);
    void clearNpcHouseOverride(uint32_t npcId);
    void setNpcItemOverride(uint32_t npcId, uint32_t itemId);
    void setNpcUnavailable(uint32_t npcId, bool unavailable);
    void addHiredNpcFollower(const HiredNpcFollower &follower);
    void removeHiredNpcFollower(uint32_t npcId);
    void setHiredNpcFollowerAbilityUsedDay(uint32_t npcId, uint32_t day);
    bool tryGrantItem(uint32_t objectDescriptionId, uint32_t quantity = 1);
    // tryGrantItem, tryGrantInventoryItem and tryGrantInventoryItemStartingAt give to the first member with room, from
    // the active one (or the first named) on, in any of their bags (MAW has four; the open bag first);
    // tryGrantInventoryItemToMember uses that member's open bag only.
    bool tryGrantInventoryItem(const InventoryItem &item, size_t *pRecipientMemberIndex = nullptr);
    bool tryGrantInventoryItemToMember(size_t memberIndex, const InventoryItem &item);
    bool tryGrantInventoryItemStartingAt(
        size_t firstMemberIndex,
        const InventoryItem &item,
        size_t *pRecipientMemberIndex = nullptr);
    // Whether tryGrantInventoryItem would find room for the item; changes nothing.
    bool canGrantInventoryItem(const InventoryItem &item) const;
    void grantItem(uint32_t objectDescriptionId, uint32_t quantity = 1);
    bool removeItem(uint32_t objectDescriptionId, uint32_t quantity = 1);
    static int effectiveMaximumHealth(const Character &member);
    static int effectiveMaximumSpellPoints(const Character &member);
    // The most HP or SP a member can fill to: the maximum less what its auras hold back (MAW's reservations).
    int reachableMaximumHealth(size_t memberIndex) const;
    int reachableMaximumSpellPoints(size_t memberIndex) const;
    bool needsHealing() const;
    bool activeMemberNeedsHealing() const;
    void restoreAll();
    void restAndHealAll();
    int daysWithoutRest() const;
    void clearDaysWithoutRest();
    void addDayWithoutRest();
    // Counts the 3 AM dawns passed since the last rest; from the second on the party weakens, starves and
    // eventually goes insane or dies. A rest or heal resynchronises the dawn clock without these effects.
    void updateDaysWithoutRest(float gameMinutes);
    // The world runtime that owns the clock publishes every change of it here, so conditions inflicted without a
    // caller-supplied time (damage knockouts, rule effects) record when they started.
    void setGameMinutes(float gameMinutes);
    float gameMinutes() const;
    void reviveAndRestoreAll();
    void restoreActiveMember();
    bool trainLeader(uint32_t maxLevel, uint32_t &newLevel, uint32_t &skillPointsEarned);
    bool trainActiveMember(uint32_t maxLevel, uint32_t &newLevel, uint32_t &skillPointsEarned);
    bool canMemberLearnSkill(size_t memberIndex, const std::string &skillName) const;
    bool learnMemberSkill(size_t memberIndex, const std::string &skillName);
    bool canActiveMemberLearnSkill(const std::string &skillName) const;
    bool learnActiveMemberSkill(const std::string &skillName);
    bool canIncreaseActiveMemberSkillLevel(const std::string &skillName) const;
    bool increaseActiveMemberSkillLevel(const std::string &skillName);
    // The rules' price for resetting the active member's skills, or nothing when the rules have no reset.
    std::optional<int> activeMemberSkillResetCost() const;
    // Pays for and resets the active member's skills (MAW's respec); lastStatus() says what happened.
    bool resetActiveMemberSkills();
    int depositGoldToBank(int amount);
    int withdrawBankGold(int amount);
    int depositAllGoldToBank();
    int withdrawAllBankGold();
    bool isFull() const;
    bool recruitRosterMember(const RosterEntry &rosterEntry);
    bool recruitCharacter(const Character &character);
    bool addAdventurersInnMember(const RosterEntry &rosterEntry, uint32_t portraitPictureId);
    bool addAdventurersInnMember(const Character &character, uint32_t portraitPictureId);
    bool hireAdventurersInnMember(size_t innIndex);
    bool dismissMemberToAdventurersInn(size_t memberIndex);
    bool replaceMemberWithRosterEntry(size_t memberIndex, const RosterEntry &rosterEntry);
    bool hasRosterMember(uint32_t rosterId) const;
    bool hasAward(uint32_t awardId) const;
    bool hasAward(size_t memberIndex, uint32_t awardId) const;
    void addAward(uint32_t awardId);
    void addAward(size_t memberIndex, uint32_t awardId);
    void removeAward(uint32_t awardId);
    void removeAward(size_t memberIndex, uint32_t awardId);
    // Carried and worn: every bag of a member (MAW's multibag) and the equipment.
    int inventoryItemCount(uint32_t objectDescriptionId, std::optional<size_t> memberIndex = std::nullopt) const;
    void recordEverOwnedItem(uint32_t objectDescriptionId);
    bool hasEverOwnedItem(uint32_t objectDescriptionId) const;
    void recordChosenMm9RudeRow(uint32_t rudeId, size_t rowIndex);
    bool hasChosenMm9RudeRow(uint32_t rudeId, size_t rowIndex) const;
    // The continent's Ledger of Teachers, bought in one of its taverns.
    bool hasTeacherLedger(uint32_t continent) const;
    void addTeacherLedger(uint32_t continent);
    const std::unordered_map<uint32_t, std::unordered_map<uint32_t, uint32_t>> &npcTopicOverrides() const;
    const std::unordered_map<uint32_t, uint32_t> &npcHouseOverrides() const;
    const std::unordered_set<uint32_t> &unavailableNpcIds() const;
    void recordExplosiveMix(uint32_t targetItemId, uint32_t heldItemId);
    bool isExplosiveMixKnown(uint32_t targetItemId, uint32_t heldItemId) const;
    void setHeldItemForQueries(const InventoryItem &item);
    uint32_t heldItemIdForQueries() const;
    void clearHeldItemForQueries();
    bool hasItemAnywhere(uint32_t objectDescriptionId) const;
    bool grantItemToMember(size_t memberIndex, uint32_t objectDescriptionId, uint32_t quantity = 1);
    bool removeItemFromMember(size_t memberIndex, uint32_t objectDescriptionId, uint32_t quantity = 1);
    bool takeItemFromMemberInventoryCell(size_t memberIndex, uint8_t gridX, uint8_t gridY, InventoryItem &item);
    // Into the member's open bag, else the first of their other bags with room (rulesets with several bags).
    bool tryAutoPlaceItemInMemberInventory(size_t memberIndex, const InventoryItem &item);
    // Regroups the inventory by item type and repacks it; leaves it unchanged when the items cannot be repacked.
    bool sortMemberInventory(size_t memberIndex);
    bool tryPlaceItemInMemberInventoryCell(
        size_t memberIndex,
        const InventoryItem &item,
        uint8_t gridX,
        uint8_t gridY,
        std::optional<InventoryItem> &replacedItem);
    bool takeEquippedItemFromMember(size_t memberIndex, EquipmentSlot slot, InventoryItem &item);
    // Puts a changed copy of a worn item back in its slot (crafting); nothing about wearing it is checked again.
    bool replaceEquippedItem(size_t memberIndex, EquipmentSlot slot, const InventoryItem &item);
    bool tryEquipItemOnMember(
        size_t memberIndex,
        EquipmentSlot targetSlot,
        const InventoryItem &item,
        std::optional<EquipmentSlot> displacedSlot,
        bool autoStoreDisplacedItem,
        std::optional<InventoryItem> &heldReplacement);
    std::optional<InventoryItem> equippedItem(size_t memberIndex, EquipmentSlot slot) const;
    // Implant sockets (Character::implants, the Augment panel): fits an implant item (equip stat Implant) into one of
    // the member's open sockets, handing back the implant it replaces in heldReplacement; false for a closed socket
    // or an item that is not an implant. takeImplant empties a socket into item.
    bool fitImplant(size_t memberIndex, size_t socket, const InventoryItem &item,
        std::optional<InventoryItem> &heldReplacement);
    bool takeImplant(size_t memberIndex, size_t socket, InventoryItem &item);
    const InventoryItem *memberInventoryItem(size_t memberIndex, uint8_t gridX, uint8_t gridY) const;
    InventoryItem *memberInventoryItemMutable(size_t memberIndex, uint8_t gridX, uint8_t gridY);
    uint32_t equippedItemId(size_t memberIndex, EquipmentSlot slot) const;
    // Whether the member's paperdoll can wear body armour (the doll type's Armor column); dragons cannot.
    bool memberCanWearArmor(size_t memberIndex) const;
    // The Workshop: the first item the member wears that the mod fits (main hand, bow, off hand, armour, helm, cloak,
    // then the rest), 0 for none. fitWorkshopMod fits it there (replacing a mod already fitted) and returns that item.
    uint32_t workshopModTarget(size_t memberIndex, uint16_t modId) const;
    uint32_t fitWorkshopMod(size_t memberIndex, uint16_t modId);
    const EquippedItemRuntimeState *equippedItemRuntime(size_t memberIndex, EquipmentSlot slot) const;
    EquippedItemRuntimeState *equippedItemRuntimeMutable(size_t memberIndex, EquipmentSlot slot);
    bool consumeEquippedWandCharge(size_t memberIndex);
    void refreshDerivedState();
    static bool isPartyWideUtilitySkill(std::string_view skillName);
    std::optional<size_t> bestPartyWideUtilitySkillMemberIndex(
        std::string_view skillName,
        bool requireCanAct = true) const;
    const Character *bestPartyWideUtilitySkillMember(std::string_view skillName, bool requireCanAct = true) const;
    int bestPartyWideUtilitySkillValue(std::string_view skillName, bool requireCanAct = true) const;
    bool canIdentifyItem(const ItemDefinition &itemDefinition) const;
    bool canRepairItem(const ItemDefinition &itemDefinition) const;
    bool tryIdentifyMemberInventoryItem(
        size_t memberIndex,
        uint8_t gridX,
        uint8_t gridY,
        size_t inspectorMemberIndex,
        std::string &statusText);
    bool tryRepairMemberInventoryItem(
        size_t memberIndex,
        uint8_t gridX,
        uint8_t gridY,
        size_t inspectorMemberIndex,
        std::string &statusText);
    bool identifyMemberInventoryItem(
        size_t memberIndex,
        uint8_t gridX,
        uint8_t gridY,
        std::string &statusText);
    bool repairMemberInventoryItem(
        size_t memberIndex,
        uint8_t gridX,
        uint8_t gridY,
        std::string &statusText);
    bool tryIdentifyEquippedItem(
        size_t memberIndex,
        EquipmentSlot slot,
        size_t inspectorMemberIndex,
        std::string &statusText);
    bool tryRepairEquippedItem(
        size_t memberIndex,
        EquipmentSlot slot,
        size_t inspectorMemberIndex,
        std::string &statusText);
    bool identifyEquippedItem(
        size_t memberIndex,
        EquipmentSlot slot,
        std::string &statusText);
    bool repairEquippedItem(
        size_t memberIndex,
        EquipmentSlot slot,
        std::string &statusText);
    // Sets the class; becoming a Lich also makes the member undead unless `classOnly` (MAW's promotions change the
    // class alone).
    bool setMemberClassName(size_t memberIndex, const std::string &className, bool classOnly = false);
    // Recomputes a member's maximum HP and SP from their class (after the rules' class numbers changed).
    void refreshMemberResources(size_t memberIndex);
    bool applyLichTransformation(size_t memberIndex);
    const Character *member(size_t memberIndex) const;
    Character *member(size_t memberIndex);
    bool canSelectMemberInGameplay(size_t memberIndex) const;
    bool hasSelectableMemberInGameplay() const;
    bool hasActableMember() const;
    bool setActiveMemberIndex(size_t memberIndex);
    bool canSpendSpellPoints(size_t memberIndex, int amount) const;
    bool spendSpellPoints(size_t memberIndex, int amount);
    bool spendSpellPointsOnActiveMember(int amount);
    void advanceTimedStates(float deltaSeconds);
    void updateRecovery(float deltaSeconds, float progressScale = 1.0f);
    // Personal shields regenerate after their delay without damage (part of updateRecovery).
    void updatePersonalShields(float deltaSeconds);
    bool applyRecoveryToMember(size_t memberIndex, float recoverySeconds);
    bool applyRecoveryToActiveMember(float recoverySeconds);
    bool switchToNextReadyMember();
    void applyPartyBuff(
        PartyBuffId buffId,
        float durationSeconds,
        int power,
        uint32_t spellId,
        uint32_t skillLevel,
        SkillMastery skillMastery,
        uint32_t casterMemberIndex);
    void applyCharacterBuff(
        size_t memberIndex,
        CharacterBuffId buffId,
        float durationSeconds,
        int power,
        uint32_t spellId,
        uint32_t skillLevel,
        SkillMastery skillMastery,
        uint32_t casterMemberIndex);
    void applyTemporaryPrimaryStatBonus(uint32_t statIndex, int power, float durationSeconds);
    void clearPartyBuff(PartyBuffId buffId);
    void clearCharacterBuff(size_t memberIndex, CharacterBuffId buffId);
    bool clearDispellableBuffs();
    bool hasDispellableBuffs() const;
    bool hasPartyBuff(PartyBuffId buffId) const;
    bool hasCharacterBuff(size_t memberIndex, CharacterBuffId buffId) const;
    const PartyBuffState *partyBuff(PartyBuffId buffId) const;
    const CharacterBuffState *characterBuff(size_t memberIndex, CharacterBuffId buffId) const;
    bool blockConditionWithProtectionFromMagic(CharacterCondition condition);
    // Starts the condition at the party's current game time.
    bool applyMemberCondition(size_t memberIndex, CharacterCondition condition);
    bool applyMemberCondition(size_t memberIndex, CharacterCondition condition, float gameMinutes);
    bool clearMemberCondition(size_t memberIndex, CharacterCondition condition);
    bool hasMemberConditionImmunity(size_t memberIndex, CharacterCondition condition) const;
    bool healMember(size_t memberIndex, int amount);
    // Changes a member's HP outside combat (drains, shared life), up to full: no shields, no speech; conditions follow.
    void adjustMemberHealth(size_t memberIndex, int amount);
    bool reviveMember(size_t memberIndex, int health, bool applyWeak);

    const std::vector<Character> &members() const;
    size_t memberCount() const;
    const std::vector<AdventurersInnMember> &adventurersInnMembers() const;
    const AdventurersInnMember *adventurersInnMember(size_t innIndex) const;
    AdventurersInnMember *adventurersInnMember(size_t innIndex);
    const Character *adventurersInnCharacter(size_t innIndex) const;
    Character *adventurersInnCharacter(size_t innIndex);
    void clearAdventurersInnMembers();
    const Character *activeMember() const;
    Character *activeMember();
    size_t activeMemberIndex() const;
    int totalHealth() const;
    int totalMaxHealth() const;
    int gold() const;
    int bankGold() const;
    int food() const;
    uint32_t houseStockSeed() const;
    bool hasFoundArtifactItem(uint32_t itemId) const;
    void markArtifactItemFound(uint32_t itemId);
    void clearFoundArtifactItems();
    bool hasArcomageWinAt(uint32_t houseId) const;
    // Whether winning at this tavern counts toward Arcomage Champion: MM7's Emerald Island tavern (between the MM8
    // and MM7 ranges) does not, as in the original (OY-308).
    static bool arcomageTavernCountsForChampion(uint32_t houseId);
    void recordArcomageWin(uint32_t houseId, int goldReward, uint32_t firstWinAwardId);
    void recordArcomageLoss();
    uint32_t arcomageWinCount() const;
    const std::vector<WorldCompletionRecord> &worldCompletions() const;
    const WorldCompletionRecord *findWorldCompletion(const std::string &certificateId) const;
    void addWorldCompletion(const WorldCompletionRecord &record);
    bool worldCompletionsUntracked() const;
    void clearWorldCompletionsUntracked();
    uint32_t arcomageLossCount() const;
    HouseStockState *houseStockState(uint32_t houseId);
    const HouseStockState *houseStockState(uint32_t houseId) const;
    HouseStockState &ensureHouseStockState(uint32_t houseId);
    void clearHouseStockStates();
    size_t inventoryItemCount() const;
    size_t usedInventoryCells() const;
    size_t inventoryCapacity() const;
    uint32_t waterDamageTicks() const;
    uint32_t burningDamageTicks() const;
    uint32_t splashCount() const;
    uint32_t landingSoundCount() const;
    uint32_t hardLandingSoundCount() const;
    float lastFallDamageDistance() const;
    const std::string &lastStatus() const;
    const std::vector<PendingAudioRequest> &pendingAudioRequests() const;
    void clearPendingAudioRequests();
    void rebuildMagicalBonusesFromBuffs();

private:
    static constexpr size_t MaxMembers = 5;

    uint8_t resolveInventoryWidth(uint32_t objectDescriptionId) const;
    uint8_t resolveInventoryHeight(uint32_t objectDescriptionId) const;
    void applyDefaultStartingSkills(Character &member) const;
    void markArtifactItemFoundIfRelevant(const InventoryItem &item);
    void recordEverOwnedItemIfRelevant(const InventoryItem &item);
    void recordEverOwnedItemsFromCurrentState();
    void applyWeeklyItemEffects();
    void queueSound(SoundId soundId);
    void queueSpeech(size_t memberIndex, SpeechId speechId);
    SoundId resolveDamageImpactSoundForMember(size_t memberIndex) const;

    const ItemTable *m_pItemTable = nullptr;
    const PartyShieldRules *m_pPersonalShieldRules = nullptr;
    const JournalQuestTable *m_pJournalQuestTable = nullptr;
    const CharacterDollTable *m_pCharacterDollTable = nullptr;
    const StandardItemEnchantTable *m_pStandardItemEnchantTable = nullptr;
    const SpecialItemEnchantTable *m_pSpecialItemEnchantTable = nullptr;
    const ClassMultiplierTable *m_pClassMultiplierTable = nullptr;
    const ClassSkillTable *m_pClassSkillTable = nullptr;
    const TrainerDirectory *m_pTrainerDirectory = nullptr;
    const GameRules *m_pRules = nullptr;
    std::vector<Character> m_members;
    std::vector<AdventurersInnMember> m_adventurersInnMembers;
    size_t m_activeMemberIndex = 0;
    std::array<PartyBuffState, PartyBuffCount> m_partyBuffs = {};
    std::array<std::array<CharacterBuffState, CharacterBuffCount>, MaxMembers> m_characterBuffs = {};
    int m_gold = 0;
    int m_bankGold = 0;
    int m_food = 0;
    int m_fineGold = 0;
    uint32_t m_waterDamageTicks = 0;
    uint32_t m_burningDamageTicks = 0;
    uint32_t m_splashCount = 0;
    uint32_t m_landingSoundCount = 0;
    uint32_t m_hardLandingSoundCount = 0;
    uint32_t m_monsterTargetSelectionCounter = 0;
    uint32_t m_houseStockSeed = 0;
    float m_periodicEffectElapsedGameSeconds = 0.0f;
    float m_gameMinutes = 0.0f;
    uint32_t m_itemWeeklyEffectSequence = 0;
    float m_lastFallDamageDistance = 0.0f;
    int m_daysWithoutRest = 0;
    std::optional<int> m_awakeDayIndex;
    std::string m_lastStatus;
    std::unordered_set<uint32_t> m_foundArtifactItems;
    std::unordered_set<uint32_t> m_arcomageWonHouseIds;
    std::vector<WorldCompletionRecord> m_worldCompletions;
    bool m_worldCompletionsUntracked = false;
    std::unordered_set<uint32_t> m_everOwnedItemIds;
    std::unordered_set<uint64_t> m_chosenMm9RudeRows;
    std::unordered_set<uint32_t> m_teacherLedgers;
    std::unordered_set<uint64_t> m_explosiveMixes;
    std::unordered_map<uint32_t, int32_t> m_continentReputations;
    std::unordered_set<uint32_t> m_questBits;
    std::unordered_set<uint32_t> m_autonotes;
    std::unordered_map<uint32_t, std::unordered_map<uint32_t, int32_t>> m_historyEventTimesByContinent;
    std::vector<JournalMapNote> m_journalMapNotes;
    uint64_t m_dialogueEligibilityRevision = 1;
    uint32_t m_arcomageWinCount = 0;
    uint32_t m_arcomageLossCount = 0;
    bool m_debugDamageImmune = false;
    float m_rulesMovementMultiplier = 1.0f;
    bool m_debugUnlimitedMana = false;
    std::unordered_map<uint32_t, HouseStockState> m_houseStockStates;
    std::unordered_map<uint16_t, int32_t> m_eventVariables;
    std::unordered_map<uint32_t, std::unordered_map<uint32_t, uint32_t>> m_npcTopicOverrides;
    std::unordered_map<uint32_t, uint32_t> m_npcGroupNews;
    std::unordered_map<uint32_t, uint32_t> m_npcGreetingOverrides;
    std::unordered_map<uint32_t, uint32_t> m_npcGreetingDisplayCounts;
    std::unordered_map<uint32_t, uint32_t> m_npcHouseOverrides;
    std::unordered_map<uint32_t, uint32_t> m_npcItemOverrides;
    std::unordered_set<uint32_t> m_unavailableNpcIds;
    std::vector<HiredNpcFollower> m_hiredNpcFollowers;
    PartyBuffState m_cartographerWizardEye = {};
    uint32_t m_heldItemIdForQueries = 0;
    std::vector<uint32_t> m_humQBits;
    std::vector<int> m_humPercents;
    std::optional<int> m_mapHumPercent;
    // Unset: Fire.
    std::optional<CombatDamageType> m_floorBurnType;
    bool m_floorBurnResisted = false;
    std::vector<uint32_t> m_objectiveQBits;
    std::vector<PendingAudioRequest> m_pendingAudioRequests;
};
}
