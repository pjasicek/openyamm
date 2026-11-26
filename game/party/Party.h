#pragma once

#include "game/audio/SoundIds.h"
#include "game/audio/SoundRef.h"
#include "game/gameplay/NpcFollowerTypes.h"
#include "game/items/ItemEnchantTables.h"
#include "game/outdoor/OutdoorMovementDriver.h"
#include "game/party/ActionBarSlot.h"
#include "game/party/BattleOrders.h"
#include "game/party/CampaignState.h"
#include "game/party/CharacterRulesetState.h"
#include "game/party/PartyRulesetState.h"
#include "game/party/CharacterState.h"
#include "game/party/InventoryItem.h"
#include "game/party/PlaythroughStatisticsTypes.h"
#include "game/party/QuickItemSlot.h"
#include "game/party/SoloTalentState.h"
#include "game/party/SpeechIds.h"
#include "game/tables/ClassSkillTable.h"
#include "game/tables/MonsterShields.h"
#include "game/tables/PortraitEnums.h"

#include <array>
#include <bitset>
#include <cstdint>
#include <functional>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <unordered_map>
#include <unordered_set>
#include <utility>
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
struct Mm9Hireling;
struct Mm9HirelingPassives;
class Mm9HirelingTable;
enum class Mm9HirelingKind : uint8_t;

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
    // The member's identity in the playthrough statistics (game/party/PlaythroughStatistics.h): random, given out the
    // first time the member is in the party, kept when dismissed and hired back. 0 until then. Saved.
    uint64_t statsMemberId = 0;
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
    // The solo run's action bar (devdocs/solo_action/HUD.md): spells, potion or scroll kinds, the weapon attack, later
    // special skills. Saved; party games keep it empty and never read it.
    std::array<ActionBarSlot, ActionBarSlotCount> actionBar = {};
    // The special skills (talents) learned in a MAW solo run, by talent id: their ranks (devdocs/solo_action/TALENTS.md).
    // Saved; empty in every other game. Two bytes: Conditioning has no last rank.
    std::unordered_map<std::string, uint16_t> talentRanks;
    // Their cooldowns and timed effects. Not saved.
    SoloTalentState talentState;
    // Battle orders (game/party/BattleOrders.h): what Attack does, tried in order, then the fallback. Saved; they
    // replace the single attack spell of older saves.
    std::vector<BattleOrder> battleOrders;
    BattleOrderFallback battleOrderFallback = BattleOrderFallback::Weapon;
    // The upkeep list: the buffs, heals and cures the Upkeep key casts when they are due, tried in order. Saved.
    std::vector<BattleOrder> upkeepOrders;
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
    // When a timed condition wears off (game minutes; 0: it lasts until cured), from a monster spell's duration
    // (spell_conditions minutes). Party::setGameMinutes clears it once the clock passes.
    std::array<float, CharacterConditionCount> conditionExpireGameMinutes = {};
    std::unordered_map<std::string, CharacterSkill> skills;
    std::unordered_set<uint32_t> awards;
    std::unordered_map<uint16_t, int32_t> eventVariables;
    float recoverySecondsRemaining = 0.0f;
    // The length of the recovery that recoverySecondsRemaining counts down (the longest applied since the member was
    // last ready), for the solo HUD's crosshair brackets. Not saved: after a load the brackets start full.
    float recoveryTotalSeconds = 0.0f;
    int armorClassModifier = 0;
    int levelModifier = 0;
    // Levels that worn items add while equipped ("of Power", +5), rebuilt with the magical bonuses (OY-199).
    int equippedLevelBonus = 0;
    int ageModifier = 0;
    // Whole game years since the game began, kept by Party::setGameMinutes (not saved): the character ages with them.
    uint32_t playedYears = 0;
    std::unordered_set<uint32_t> playerBits;
    uint32_t npcs2 = 0;
    int merchantBonus = 0;
    // The member's Glamour (the spell, a potion or an event's), also counted in merchantBonus; MAW weighs its power by
    // its mastery.
    int glamourPower = 0;
    SkillMastery glamourMastery = SkillMastery::None;
    // Flat damage the equipment adds to melee blows and to bow and gun shots (artifacts, item content effects); a
    // weapon's adds only to its own attacks. Elemental enchantment damage is rolled per hit instead.
    int meleeWeaponDamageBonus = 0;
    int rangedWeaponDamageBonus = 0;
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

// A new solo run's first action bar: the weapon attack on 1, then the spells the character knows in book order on
// 2-0 (devdocs/solo_action/HUD.md). Slots already set stay.
void prefillSoloActionBar(Character &member);
class Party;
// The skill a new solo run's character starts with (the user, 2026-11-19), where its ruleset lets its class learn it
// (MAW's Lone Discipline lets every class; Standard only the classes that have the skill).
inline constexpr const char *SoloRunStartSkill = "Regeneration";
// A new solo run's party: the first member alone (with the first's character buffs), its action bar filled, and
// SoloRunStartSkill learned. Every new game path with RulesetOptions::soloRun calls it once (New Game, the debug
// start, scenarios), with the party on the run's rules.
void makeSoloRunParty(Party &party);
// A new solo run's travel scrolls, one each of Water Walk, Jump, Town Portal, Fly and Lloyd's Beacon (user,
// 2026-11-15). Every new game path that starts a solo run gives them once; turning an existing game solo does not.
void giveSoloRunStartScrolls(Party &party);

struct SpellEntry;

// SpellTable::findByName's choice among spells that share a name (two Charms): the one the character knows (OY-337).
std::function<bool(const SpellEntry &)> spellKnownBy(const Character &character);

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
    // MM9's Fleet Foot, cast from Fly's slot in a world whose world.yml says fleetFoot (game/party/WorldSpells.h):
    // the party runs faster. Its power is the speed in percent (125 is a quarter faster).
    FleetFoot,
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

// An MM9 hireling with the party (devdocs/mm9/MM9_HIRELINGS_PLAN.md). Kept apart from Party::members(), so MM6-MM8
// code never sees hirelings; the systems that include them opt in.
struct Mm9PartyHireling
{
    // Its row in the MM9 hireling table (Mm9HirelingTable::find).
    uint32_t rudeId = 0;
    Mm9HirelingKind kind = {};
    // HP, conditions, recovery and the row's level, armour class (armorClassModifier) and resistances; never an
    // inventory, equipment or spellbook.
    Character character;
    // Its personal buffs, as the members' (Party::characterBuff).
    std::array<CharacterBuffState, CharacterBuffCount> buffs = {};
    // Day index (game minutes / 1440) of the hire.
    uint32_t hireDay = 0;
    // When the next 28-day wage is due; 0 for story companions, who take none.
    float nextWageGameMinutes = 0.0f;
    // The -15 service is ready again from this time.
    float serviceReadyGameMinutes = 0.0f;
    // Its cell in the formation grid (Party::formationCell); -1 unset.
    int32_t formationCell = -1;
    // What the rules make of its row (MAW: the party's level, MawClassRules::scaleHirelings), multiplying its attacks'
    // damage and its spells' skill; 1 under Standard. Not saved: the rules set them again.
    float rulesDamageScale = 1.0f;
    float rulesSkillScale = 1.0f;
};

// The MM9 formation grid (MM9_HIRELINGS.md section 10): cells 0-8 row by row, 0-2 the front rank, 3-5 the middle,
// 6-8 the rear.
constexpr int32_t Mm9FormationCellCount = 9;
constexpr int32_t Mm9FormationRankSize = 3;

class Party
{
public:
    // MM9: at most three hirelings, at most two of them paid retainers (the third slot is a story companion's).
    static constexpr size_t MaxMm9Hirelings = 3;
    static constexpr size_t MaxPaidMm9Hirelings = 2;
    static constexpr float Mm9HirelingWagePeriodGameMinutes = 28.0f * 24.0f * 60.0f;
    // A hireling's primary stats: the value whose parameter bonus is 0 (MM's table gives 0 for 13-14), so the shared
    // formulas (armour from speed, saves and resistance rolls from luck) add nothing to its row's values.
    static constexpr uint32_t Mm9HirelingPrimaryStat = 13;

    struct Snapshot
    {
        // The game's own record (Party::campaign), saved with the party.
        CampaignState::Snapshot campaign;
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
        float itemEffectElapsedGameSeconds = 0.0f;
        uint32_t itemWeeklyEffectSequence = 0;
        float lastFallDamageDistance = 0.0f;
        int daysWithoutRest = 0;
        std::optional<int> awakeDayIndex;
        uint32_t arcomageWinCount = 0;
        uint32_t arcomageLossCount = 0;
        std::unordered_set<uint32_t> everOwnedItemIds;
        // MM9 talk rows the party has chosen (rude id << 32 | row index): the conversation bar's visited marks.
        std::unordered_set<uint64_t> chosenMm9RudeRows;
        // The continents whose Ledger of Teachers the party bought in a tavern (TrainerDirectory.h).
        std::unordered_set<uint32_t> teacherLedgers;
        std::vector<HiredNpcFollower> hiredNpcFollowers;
        std::vector<Mm9PartyHireling> mm9Hirelings;
        // The members' formation cells (Party::formationCell), one per member; older saves have none (defaults).
        std::vector<int32_t> memberFormationCells;
        // The outdoor map the party was last on (MMerge's vars.LastOutdoorMap); older saves have none.
        std::string lastOutdoorMapFileName;
        // Potion pairs (target << 32 | held) that exploded when mixed, so the alchemy bench can warn.
        std::unordered_set<uint64_t> explosiveMixes;
        // The shared pouches' items (Party::pouchItems), by ItemPouch; older saves have none and gather theirs when
        // loaded (Party::gatherPouchItems).
        // The party's own three; the quest pouch is the campaign's (campaign.questPouch) and its place here stays
        // empty.
        std::array<std::vector<InventoryItem>, ItemPouchCount> pouches;
        // What the ruleset keeps for the party (Party::rulesetState). A save holds it inside the ruleset's state.
        PartyRulesetState rulesetState;
        // Items an event gave that found no room yet (Party::waitingGivenItems); older saves have none.
        std::vector<InventoryItem> waitingGivenItems;
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
        // Which sound table the id names: the engine's (SoundId), or the mounted worlds' (a world's sounds.txt row,
        // as an implant's fit, remove and evolve sounds).
        SoundScope scope = SoundScope::Engine;
        SpeechId speechId = SpeechId::None;
        size_t memberIndex = 0;
    };

    // A potion's effect that just entered its last PotionExpiryWarningSeconds (advanceTimedStates): a party or
    // personal buff applied without a spell, or a ruleset potion effect. The gameplay screen announces it.
    struct ExpiringPotionEffect
    {
        enum class Kind : uint8_t
        {
            PartyBuff,
            CharacterBuff,
            RulesetEffect,
        };

        Kind kind = Kind::PartyBuff;
        // The combatant (CharacterBuff) or member (RulesetEffect); unused for a party buff.
        size_t memberIndex = 0;
        PartyBuffId partyBuff = PartyBuffId::TorchLight;
        CharacterBuffId characterBuff = CharacterBuffId::Bless;
        TimedPotionEffect::Kind rulesetEffect = TimedPotionEffect::Kind::Immunity;
        uint32_t rulesetEffectKey = 0;
    };

    // Ten game minutes (twenty real seconds), as Fly and Wizard Eye blink before they end (OY-508).
    static constexpr float PotionExpiryWarningSeconds = 600.0f;

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
    int fineGold() const;
    void addFineGold(int amount);
    void clearFineGold();
    void setClassMultiplierTable(const ClassMultiplierTable *pClassMultiplierTable);
    const ClassMultiplierTable *classMultiplierTable() const;
    void setClassSkillTable(const ClassSkillTable *pClassSkillTable);
    // The active ruleset's rules, owned by the session; Standard until set.
    void setRules(const GameRules *pRules);
    // A ruleset's slow on the party's movement, set each frame (MAW's dimension affix 25 while enemies are near).
    // 1: none; not saved.
    void setRulesMovementMultiplier(float multiplier);
    float rulesMovementMultiplier() const;
    // A spell's speed-up of the party's movement, set each frame (MM9's Fleet Foot: fleetFootSpeedMultiplier).
    // 1: none; not saved.
    void setSpellMovementMultiplier(float multiplier);
    // A solo run talent's speed-up of the party's movement (Quickfoot), set when it changes. 1: none; not saved.
    void setTalentMovementMultiplier(float multiplier);
    // What the party's walking and running speed is multiplied by: the ruleset's slow and the spell's and talent's
    // speed-ups.
    float movementMultiplier() const;
    const GameRules &rules() const;
    // The session's playthrough statistics (devdocs/PLAYTHROUGH_STATISTICS_PLAN.md). A copy of the party does not
    // carry it, so trial copies never record; assigning another party's state keeps this party's binding.
    void setStatistics(PlaythroughStatistics *pStatistics);
    PlaythroughStatistics *statistics() const;
    // Gives every member without one a statistics identity (Character::statsMemberId).
    void assignStatsMemberIds();
    StatMemberRef statsMember(size_t memberIndex) const;
    // What the next applyDamageToMember is from: the combat controller names a monster's hit before it lands.
    void setIncomingDamageSource(StatDamageTakenKind kind, const std::string &cause);
    const ClassSkillTable *classSkillTable() const;
    // Every skill teacher (the journal's trainer finder, the Ledger of Teachers, the trainer hints).
    void setTrainerDirectory(const TrainerDirectory *pTrainerDirectory);
    const TrainerDirectory *trainerDirectory() const;
    // The game this party plays in: quest progress, the journal, what events and NPCs remember, shop stock. It is the
    // session's once the session has bound it (bindCampaign), so that every party of one game reads and writes the
    // same state; until then it is the party's own.
    CampaignState &campaign();
    const CampaignState &campaign() const;
    // Makes the party play in this campaign, owned by the caller, which outlives the party. The party's own campaign
    // state is dropped: whoever binds has taken it over first where it matters (GameSession::setPartyState).
    void bindCampaign(CampaignState *pCampaign);
    bool campaignBoundTo(const CampaignState *pCampaign) const;
    Snapshot snapshot() const;
    // The same without the campaign (quest bits, notes, every shop's stock), which is left empty: for what is
    // made many times a second and does not carry it (a co-op character on the wire).
    Snapshot characterSnapshot() const;
    void restoreSnapshot(const Snapshot &snapshot);
    // A co-op guest's party in its own game: a mirror of the party the host keeps for it. Its recovery and timed
    // states do not run here: the host runs them, and applyMirror brings the result. What the player does with the
    // party is done here and sent to the host (game/coop/CoopSession.h).
    void setMirror(bool mirror);
    bool mirror() const;
    // What the ruleset keeps for this party (MAW: its auras, held food and deaths); empty under Standard. Part of the
    // snapshot, so it is saved, and travels with the party to another game.
    PartyRulesetState &rulesetState();
    const PartyRulesetState &rulesetState() const;
    // Takes the party's own state from a snapshot and leaves the campaign, what the members' portraits show and what
    // waits to be heard as they are: a co-op guest's game keeps its party the same as the host's this way, many times
    // a second (game/coop/CoopSession.h).
    void applyMirror(const Snapshot &snapshot);
    // Every member's Unconscious and Dead as its hit points make them (as a hit sets them): for a mirror whose
    // hit points were set from outside.
    void refreshIncapacitatedConditions();
    void reset();
    void seed(const PartySeed &seed);
    const std::string &lastOutdoorMapFileName() const;
    void setLastOutdoorMapFileName(const std::string &mapFileName);
    void applyMovementEffects(const OutdoorMovementEffects &effects);
    void applyEventRuntimeState(const EventRuntimeState &runtimeState, bool grantItemsToInventory = true);
    void setDebugDamageImmune(bool enabled);
    // The solo HUD's self combat text (GameplaySoloHud): what befell a member, pushed as it happens and taken where
    // the HUD draws. Transient; at most SelfTextEventLimit wait (a party game never takes them).
    struct SelfTextEvent
    {
        enum class Kind : uint8_t
        {
            Damage,
            Heal,
            // A regeneration tick (healMember's regeneration flag): the HUD shows these summed, not one by one.
            Regeneration,
            ConditionGained,
            ConditionCleared,
        };
        Kind kind = Kind::Damage;
        size_t memberIndex = 0;
        int amount = 0;
        CharacterCondition condition = CharacterCondition::Weak;
    };
    std::vector<SelfTextEvent> takeSelfTextEvents()
    {
        return std::exchange(m_selfTextEvents, {});
    }
    void setDebugUnlimitedMana(bool enabled);
    bool applyDamageToMember(
        size_t memberIndex,
        int damage,
        const std::string &status,
        bool allowUnconscious = false);
    bool applyDamageToActiveMember(int damage, const std::string &status);
    bool applyPotionExplosionToMember(size_t memberIndex, uint8_t damageLevel);
    bool applyDamageToAllLivingMembers(int damage, const std::string &status);
    // The statistics count a gain under the reason given; kill experience (grantMonsterKillExperience) as Monster.
    uint64_t addExperienceToMember(
        size_t memberIndex, int64_t amount, ExperienceReason reason = ExperienceReason::Other);
    uint64_t setMemberExperience(size_t memberIndex, uint64_t experience);
    uint32_t grantSharedExperience(uint32_t totalExperience, ExperienceReason reason = ExperienceReason::Other);
    // Shares the experience for killing a monster under the experience rules; returns the amount before sharing.
    uint32_t grantMonsterKillExperience(const MonsterKillReward &kill);
    std::optional<size_t> chooseMonsterAttackTarget(uint32_t attackPreferences, uint32_t seedHint);
    // The statistics count the change under the reason given (game/party/PlaythroughStatisticsTypes.h).
    void addGold(int amount, GoldReason reason = GoldReason::Other);
    void addFood(int amount);
    void requestSound(SoundId soundId);
    // A sound of a world's sound table by its id (0: none).
    void requestWorldSound(uint32_t soundId);
    void requestDamageImpactSoundForMember(size_t memberIndex);
    void requestSpeech(size_t memberIndex, SpeechId speechId);
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
    // Changes whenever something a dialogue's conditions may read has changed: the party's own state or the campaign's
    // quest bits.
    uint64_t dialogueEligibilityRevision() const;
    // The campaign's NPC state (CampaignState::applyNpcStateTo) and the party's followers, over a map's event state.
    void applyGlobalNpcStateTo(EventRuntimeState &runtimeState) const;
    void addHiredNpcFollower(const HiredNpcFollower &follower);
    void removeHiredNpcFollower(uint32_t npcId);
    void setHiredNpcFollowerAbilityUsedDay(uint32_t npcId, uint32_t day);
    // Whether the MM6-MM8 hired NPC followers count in the active world (world.yml npcFollowers; off in MM9, whose
    // hirelings replace them). Off, the party keeps its followers but they are not shown, take no share of found gold
    // and give no bonuses; they come back in a world that has them.
    void setNpcFollowersActive(bool active);
    bool npcFollowersActive() const;
    // Whether the MM9 hirelings travel with the party in the active world (the worlds with MM9's hireling table:
    // MM9). Off, they wait behind: the party keeps them (and saves them) but none is shown, fights, is paid or gives
    // a bonus, as if it had none; they rejoin in a world that has them.
    void setMm9HirelingsAlong(bool along);
    bool mm9HirelingsAlong() const;
    // The MM9 hirelings with the party, in hiring order (none while they wait behind).
    const std::vector<Mm9PartyHireling> &hirelings() const;
    const Mm9PartyHireling *findHireling(uint32_t rudeId) const;
    Mm9PartyHireling *findHireling(uint32_t rudeId);
    size_t paidHirelingCount() const;
    // False when the hireling is already along or the party is at a limit (MaxMm9Hirelings, MaxPaidMm9Hirelings).
    bool canAddHireling(const Mm9Hireling &row) const;
    // Adds the table row's hireling at full HP, hired now, its first wage due in 28 days; false as canAddHireling.
    bool addHireling(const Mm9Hireling &row);
    bool removeHireling(uint32_t rudeId);
    // Adds the table row of rudeId (a script: Tamur Leng joins); no fee, and keys stay as the script sets them. False
    // without a table or a row, or as addHireling.
    bool addHirelingByRudeId(uint32_t rudeId);
    // The MM9 world's hireling table (GameDataRepository::mm9HirelingTable), for the hirelings' passives and scripts.
    void setMm9HirelingTable(const Mm9HirelingTable *pTable);
    const Mm9HirelingTable *mm9HirelingTable() const;
    // What the hirelings along give (mm9PartyHirelingPassives): +20 % found gold (Edina), +10 % experience
    // (Cleirach), identify and repair that never fail, skill bonuses for the members who have the skill.
    Mm9HirelingPassives mm9HirelingPassives() const;
    // Combatants (MM9 hirelings, devdocs/mm9/MM9_HIRELINGS_PLAN.md phases 3-5): the members (0 .. memberCount() - 1),
    // then the hirelings in hiring order. Without hirelings (every MM6-MM8 party) they are exactly the members. The
    // damage, condition, heal, buff and recovery calls below take combatant indices; member() and members() stay the
    // player characters only.
    size_t combatantCount() const;
    const Character *combatant(size_t combatantIndex) const;
    Character *combatant(size_t combatantIndex);
    bool isHirelingCombatant(size_t combatantIndex) const;
    // The hireling a combatant index names; nullptr for a member.
    const Mm9PartyHireling *hirelingCombatant(size_t combatantIndex) const;
    // The acting combatant: the active member, or the active hireling while one is selected (the active-member
    // rotation runs over the members, then the hirelings, as MM9's). activeMember() stays the last active member, so
    // the inventory, spellbook and other character screens keep showing a player character.
    size_t activeCombatantIndex() const;
    const Mm9PartyHireling *activeHireling() const;
    // A member index makes that member active; a hireling's index makes the hireling act. False when out of range.
    bool setActiveCombatantIndex(size_t combatantIndex);
    // The combatants who take turns and act (0 .. actingCombatantCount() - 1): every combatant, or only the members in
    // a solo run, whose MM9 hirelings come along but never act (setSoloRun).
    size_t actingCombatantCount() const;
    // A solo run (RulesetOptions::soloRun, devdocs/solo_action/README.md), set by the session like the rules: a party
    // of one that nobody joins, with hirelings who take no combat actions. Not saved.
    void setSoloRun(bool soloRun);
    bool soloRun() const;
    // The world is shared with other players' parties (a co-op session): the comforts a lone adventurer is given
    // for being alone (the day-long scroll buffs, the day's least of timed potions) are not given there.
    bool worldShared() const;
    bool canSelectCombatantInGameplay(size_t combatantIndex) const;
    // A hireling's recovery after its attack or spell: the row's recovery_seconds less what haste takes off a
    // member's attack (attackRecoveryReductionTicks), at least a melee blow's minimum.
    static float hirelingRecoverySeconds(const Character &hireling, float rowRecoverySeconds);
    // MM9's formation (world.yml formations; devdocs/mm9/MM9_HIRELINGS.md section 10). Each member and hireling has a
    // cell 0-8; new ones take the lowest free cell. With formation targeting on (the MM9 world), a monster's blow picks
    // its victim by rank: front 70 %, middle 20 %, rear 10 %, then a cell of that rank. Off (MM6-MM8), monsters choose
    // among the members as before and the cells are unused.
    void setFormationTargetingActive(bool active);
    bool formationTargetingActive() const;
    // Whether the world casts MM9's Fleet Foot from Fly's slot (world.yml fleetFoot; game/party/WorldSpells.h).
    // Entering another world ends a Fleet Foot the party still has, so it never runs outside MM9; entering MM9 turns a
    // Fly into Fleet Foot for its remaining time.
    void setFleetFootWorld(bool active);
    bool fleetFootWorld() const;
    // The Gameplay setting GameSettings::mm9LootInOlderWorlds: off, random loot on maps of the merged MM6-MM8 base
    // keeps to the base's equipment; MM9's maps roll every world's.
    void setMm9LootInOlderWorlds(bool active);
    bool mm9LootInOlderWorlds() const;
    int32_t formationCell(size_t combatantIndex) const;
    // Moves a combatant to an empty cell; false for an occupied or invalid cell.
    bool setFormationCell(size_t combatantIndex, int32_t cell);
    // Every combatant's cell, in combatant order (the formation builder edits a copy).
    std::vector<int32_t> formationCells() const;
    // Applies a whole arrangement: one valid, distinct cell per combatant, else false and nothing changes.
    bool setFormationCells(const std::vector<int32_t> &cells);
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
    // The shared pouch the party keeps the item in instead of a member's bag (ItemRules::pouch), or none. The grants
    // above and the placements below put such an item into its pouch whatever bag they were asked for, and refuse
    // anything else a place in a pouch.
    std::optional<ItemPouch> pouchFor(const InventoryItem &item) const;
    // Whether the party has this pouch: all of them under a ruleset with pouches (MAW); the alchemy and quest pouches
    // under one without, while the Gameplay setting Party pouches is on (partyPouches); and the quest pouch alone in
    // a world shared with other players, where quest items are the world's under any ruleset
    // (CampaignState::questPouchShared). A pouch that still holds something is there too, so nothing in it is out of
    // reach.
    bool hasPouch(ItemPouch pouch) const;
    bool hasPouches() const;
    // The Gameplay setting GameSettings::partyPouches. Under a ruleset without pouches of its own (Standard) the
    // party then keeps its potions, bottles and reagents in the alchemy pouch and its quest items in the quest pouch,
    // as MAW does (ItemRules::alchemyOrQuestPouch); not in a world shared with other players, which keeps only the
    // quest pouch, the world's. Setting it moves nothing: sortPouchItems does.
    void setPartyPouches(bool enabled);
    // Whether the setting is on and has effect: a ruleset without pouches, in a game of one player.
    bool partyPouches() const;
    // The Gameplay setting GameSettings::lootPouch: what the party picks up or loots (storePickedUpItem: the ground,
    // chests' Take All, corpses) and has no pouch of its own goes to the loot pouch instead of the bags, under any
    // ruleset. Under a ruleset with pouches the loot pouch is there either way; under one without, while the setting is
    // on or it holds something (hasPouch). The setting moves nothing.
    void setLootPouch(bool enabled);
    bool lootGoesToPouch(const InventoryItem &item) const;
    // An item picked up or looted: into the loot pouch when lootGoesToPouch, else as tryGrantInventoryItem. The pouch
    // it went to, if any, is in pPouch.
    bool tryGrantLootItem(const InventoryItem &item, size_t *pRecipientMemberIndex, std::optional<ItemPouch> *pPouch);
    // Under a ruleset without pouches, after the setting or the shared world changed: the items of a pouch the
    // party no longer keeps go back into the members' bags (what finds no room stays in the pouch, which then stays:
    // hasPouch), then the items of the pouches it keeps come out of the bags (gatherPouchItems). Returns how many
    // moved. A ruleset with pouches is left alone.
    size_t sortPouchItems();
    // Takes the quest items out of the members' bags for good: a character that comes into another world brings
    // none of its own world's along (they stayed there). Returns how many went.
    size_t dropQuestItemsFromBags();
    // A pouch's items, each at its cell of the pouch's grid (InventoryBags::PouchColumns). While a member has the
    // pouch open for an operation (InventoryBags::withBagOpen) they are that member's inventory.
    const std::vector<InventoryItem> &pouchItems(ItemPouch pouch) const;
    std::vector<InventoryItem> &pouchItemsMutable(ItemPouch pouch);
    // Into the pouch's first free place, row by row; false when it is full.
    bool addToPouch(ItemPouch pouch, const InventoryItem &item);
    // Moves every item with a pouch out of the members' bags into its pouch: a save from before the pouches, a party
    // just made, a member who joined. Returns how many moved; what a full pouch cannot take stays where it lies.
    size_t gatherPouchItems();
    // Moves every pouch item whose pouch is now another one there: a save from before the rules moved a kind of item
    // (dimension maps, from quest to crafting). Returns how many moved; what a full pouch cannot take stays.
    size_t movePouchItemsToTheirPouches();
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
    // Full at five members, at one in a solo run: nobody joins a solo run (setSoloRun).
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
    void recordExplosiveMix(uint32_t targetItemId, uint32_t heldItemId);
    bool isExplosiveMixKnown(uint32_t targetItemId, uint32_t heldItemId) const;
    void setHeldItemForQueries(const InventoryItem &item);
    uint32_t heldItemIdForQueries() const;
    void clearHeldItemForQueries();
    // Items an event gave that found no room yet: GameplayHeldItemController::applyGrantedEventItemsToHeldInventory
    // hands them on when there is room. The party's, so they go with it from map to map and into the save.
    std::vector<InventoryItem> &waitingGivenItems();
    const std::vector<InventoryItem> &waitingGivenItems() const;
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
    // Debug paperdoll review: wears the item in the slot without any wearing rules (an item id of 0 empties it).
    bool forceEquippedItem(size_t memberIndex, EquipmentSlot slot, const InventoryItem &item);
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
    // class alone). The rules then grant the masteries the new class's limits allow (SkillRules::afterClassChanged).
    bool setMemberClassName(size_t memberIndex, const std::string &className, bool classOnly = false);
    // Every member's and Adventurer's Inn character's class-change masteries, for saves from before promotions granted
    // them (SaveVersionClassChangeMasteries).
    void grantClassChangeMasteries();
    // Every carried, stored and worn Special item of the members and Adventurer's Inn characters gets its own
    // enchantment (ItemGenerator::assignSpecialItemEnchants), for saves from before Special items had them
    // (SaveVersionSpecialItemEnchants, OY-553).
    void assignSpecialItemEnchants();
    // For saves from before formations were on in every world (SaveVersionFormationsEverywhere): a party whose members
    // still stand in the default cells (party order from the first) puts its sturdiest members (highest maximum HP)
    // in the front rank and the others in the middle. A formation the player arranged is kept.
    void arrangeDefaultFormationByHealth();
    // Recomputes a member's maximum HP and SP from their class (after the rules' class numbers changed).
    void refreshMemberResources(size_t memberIndex);
    bool applyLichTransformation(size_t memberIndex);
    const Character *member(size_t memberIndex) const;
    Character *member(size_t memberIndex);
    bool canSelectMemberInGameplay(size_t memberIndex) const;
    // The held Attack and Quick Cast keys' fast lane (the user, 2026-11-26): the first member who can act now and
    // whose last recovery (recoveryTotalSeconds) was shorter than repeatSeconds, the held-key repeat; none in
    // turn-based play is the caller's rule. Everyone else keeps the repeat.
    std::optional<size_t> quickRecoveryReadyMember(float repeatSeconds) const;
    bool hasSelectableMemberInGameplay() const;
    bool hasActableMember() const;
    bool setActiveMemberIndex(size_t memberIndex);
    bool canSpendSpellPoints(size_t memberIndex, int amount) const;
    bool spendSpellPoints(size_t memberIndex, int amount);
    bool spendSpellPointsOnActiveMember(int amount);
    void advanceTimedStates(float deltaSeconds);
    void updateRecovery(float deltaSeconds, float progressScale = 1.0f);
    // Per-second HP/SP regeneration (items, spells, skills) and personal shields, part of updateRecovery. Turn-based
    // combat runs it once per turn for the turn's game time instead (OE NextTurn -> _494035_timed_effects).
    void updateRegeneration(float deltaSeconds);
    // Personal shields regenerate after their delay without damage (part of updateRegeneration).
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
    // A timed condition wears off at expireGameMinutes (0: until cured). Recast on a member who has it, until-cured
    // beats any time, and of two times the later wins.
    bool applyMemberCondition(
        size_t memberIndex, CharacterCondition condition, float gameMinutes, float expireGameMinutes);
    // A condition from a monster, an event, a trap or a hazard: an immune member is spared, and Protection from Magic
    // spends a charge to stop one the member does not have yet. Applied as applyMemberCondition otherwise.
    bool applyBlockableMemberCondition(
        size_t memberIndex, CharacterCondition condition, float gameMinutes, float expireGameMinutes = 0.0f);
    bool clearMemberCondition(size_t memberIndex, CharacterCondition condition);
    bool hasMemberConditionImmunity(size_t memberIndex, CharacterCondition condition) const;
    // regeneration: a periodic tick rather than a heal, which the solo HUD's self combat text sums over time.
    bool healMember(size_t memberIndex, int amount, bool regeneration = false);
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
    // Whether winning at this tavern counts toward Arcomage Champion: MM7's Emerald Island tavern (between the MM8
    // and MM7 ranges) does not, as in the original (OY-308).
    static bool arcomageTavernCountsForChampion(uint32_t houseId);
    void recordArcomageWin(uint32_t houseId, int goldReward, uint32_t firstWinAwardId);
    void recordArcomageLoss();
    uint32_t arcomageWinCount() const;
    uint32_t arcomageLossCount() const;
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
    // Adds what another game queued for this party (a co-op guest's mirror hears what the host's copy would say).
    void addPendingAudioRequests(const std::vector<PendingAudioRequest> &requests);
    const std::vector<ExpiringPotionEffect> &expiringPotionEffects() const;
    void clearExpiringPotionEffects();
    void rebuildMagicalBonusesFromBuffs();
    // The most members a party holds.
    static constexpr size_t MaxMembers = 5;

private:
    uint8_t resolveInventoryWidth(uint32_t objectDescriptionId) const;
    uint8_t resolveInventoryHeight(uint32_t objectDescriptionId) const;
    void applyDefaultStartingSkills(Character &member) const;
    void markArtifactItemFoundIfRelevant(const InventoryItem &item);
    void recordEverOwnedItemIfRelevant(const InventoryItem &item);
    void recordEverOwnedItemsFromCurrentState();
    void applyWeeklyItemEffects();
    void queueSound(SoundId soundId, SoundScope scope = SoundScope::Engine);
    void queueSpeech(size_t memberIndex, SpeechId speechId);
    void pushSelfTextEvent(const SelfTextEvent &event);
    SoundId resolveDamageImpactSoundForMember(size_t memberIndex) const;
    // The followers that count in the active world: none where they are off (setNpcFollowersActive).
    std::span<const HiredNpcFollower> activeHiredNpcFollowers() const;
    // A combatant's personal buffs: the member's row of m_characterBuffs or the hireling's own; nullptr out of range.
    std::array<CharacterBuffState, CharacterBuffCount> *combatantBuffs(size_t combatantIndex);
    const std::array<CharacterBuffState, CharacterBuffCount> *combatantBuffs(size_t combatantIndex) const;
    // MM9's knock-out (MM9_HIRELINGS.md 9.3): a hireling at 0 HP is Unconscious, never Dead and never below 0; any HP
    // wakes it. Dead and Eradicated set by an effect stay.
    void updateHirelingKnockOut(Character &hireling) const;
    bool applyDamageToHireling(size_t combatantIndex, int damage, const std::string &status);
    // The hirelings' magical bonuses from the party buffs and their own (rebuildMagicalBonusesFromBuffs).
    void applyBuffBonusesToHirelings();
    // What the party buffs and a character's own buffs add (rebuildMagicalBonusesFromBuffs), for members and hirelings.
    void applyPartyBuffBonuses(Character &member) const;
    void applyCharacterBuffBonuses(
        Character &member,
        const std::array<CharacterBuffState, CharacterBuffCount> &buffs) const;
    // Gives every member and hireling without a valid cell the lowest free one, keeping the cells already held.
    void normalizeFormationCells();
    std::optional<size_t> chooseFormationAttackTarget(uint32_t selectionSeed) const;

    const ItemTable *m_pItemTable = nullptr;
    const PartyShieldRules *m_pPersonalShieldRules = nullptr;
    const JournalQuestTable *m_pJournalQuestTable = nullptr;
    const CharacterDollTable *m_pCharacterDollTable = nullptr;
    const StandardItemEnchantTable *m_pStandardItemEnchantTable = nullptr;
    const SpecialItemEnchantTable *m_pSpecialItemEnchantTable = nullptr;
    const ClassMultiplierTable *m_pClassMultiplierTable = nullptr;
    const ClassSkillTable *m_pClassSkillTable = nullptr;
    const TrainerDirectory *m_pTrainerDirectory = nullptr;
    const Mm9HirelingTable *m_pMm9HirelingTable = nullptr;
    const GameRules *m_pRules = nullptr;

    // Not copied with the party; kept by assignment (setStatistics).
    struct StatisticsBinding
    {
        StatisticsBinding() = default;
        StatisticsBinding(const StatisticsBinding &)
        {
        }
        StatisticsBinding &operator=(const StatisticsBinding &)
        {
            return *this;
        }

        PlaythroughStatistics *pStatistics = nullptr;
    };

    StatisticsBinding m_statistics;

    // The party's campaign: one bound by its owner, else its own. A copy of a party is never bound: it owns a copy of
    // the campaign's state, so a trial party or a checkpoint keeps what the game was and changes nothing in it.
    // Assigning a party over another writes the campaign's state into the target's campaign and leaves the target's
    // binding as it was. Together these keep a party a value, as it was while it held the campaign itself.
    struct CampaignLink
    {
        CampaignLink() = default;
        CampaignLink(const CampaignLink &other)
            : own(other.get())
        {
        }
        CampaignLink &operator=(const CampaignLink &other)
        {
            if (&get() != &other.get())
            {
                get() = other.get();
            }

            return *this;
        }

        CampaignState &get()
        {
            return pBound != nullptr ? *pBound : own;
        }
        const CampaignState &get() const
        {
            return pBound != nullptr ? *pBound : own;
        }

        CampaignState own;
        CampaignState *pBound = nullptr;
    };
    void recordConditionStatistics(size_t memberIndex, CharacterCondition condition);
    ExperienceReason m_experienceReasonScope = ExperienceReason::Other;
    std::optional<std::pair<StatDamageTakenKind, std::string>> m_incomingDamageSource;
    // The last thing that hurt each member (by statistics identity), named in the death log.
    std::unordered_map<uint64_t, std::string> m_lastDamageCause;
    CampaignLink m_campaign;
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
    float m_periodicEffectElapsedGameSeconds = 0.0f;
    float m_gameMinutes = 0.0f;
    uint32_t m_itemWeeklyEffectSequence = 0;
    float m_lastFallDamageDistance = 0.0f;
    int m_daysWithoutRest = 0;
    std::optional<int> m_awakeDayIndex;
    std::string m_lastStatus;
    std::unordered_set<uint32_t> m_everOwnedItemIds;
    // The crafting, alchemy and loot pouches. The quest pouch is the campaign's (CampaignState::questPouch): its
    // place here stays empty.
    std::array<std::vector<InventoryItem>, ItemPouchCount> m_pouches;
    PartyRulesetState m_rulesetState;
    bool m_mirror = false;
    // The snapshot's fields that are the party's own, as they are: what restoreSnapshot and applyMirror share.
    void assignSnapshotFields(const Snapshot &snapshot);
    // Where each pouch's items are kept, in ItemPouch order.
    std::array<std::vector<InventoryItem> *, ItemPouchCount> pouchStorages();
    std::array<const std::vector<InventoryItem> *, ItemPouchCount> pouchStorages() const;
    std::unordered_set<uint64_t> m_chosenMm9RudeRows;
    std::unordered_set<uint32_t> m_teacherLedgers;
    std::unordered_set<uint64_t> m_explosiveMixes;
    std::vector<InventoryItem> m_waitingGivenItems;
    uint64_t m_dialogueEligibilityRevision = 1;
    uint32_t m_arcomageWinCount = 0;
    uint32_t m_arcomageLossCount = 0;
    bool m_debugDamageImmune = false;
    std::vector<SelfTextEvent> m_selfTextEvents;
    float m_rulesMovementMultiplier = 1.0f;
    float m_spellMovementMultiplier = 1.0f;
    float m_talentMovementMultiplier = 1.0f;
    bool m_debugUnlimitedMana = false;
    std::vector<HiredNpcFollower> m_hiredNpcFollowers;
    // World configuration like m_pRules: not saved, not reset.
    bool m_npcFollowersActive = true;
    bool m_soloRun = false;
    std::vector<Mm9PartyHireling> m_mm9Hirelings;
    // The hirelings while they wait behind (setMm9HirelingsAlong(false)); m_mm9Hirelings is then empty. World
    // configuration like m_npcFollowersActive: the flag is not saved and not reset.
    std::vector<Mm9PartyHireling> m_mm9HirelingsBehind;
    bool m_mm9HirelingsAlong = true;
    // The active hireling (an index into m_mm9Hirelings) while one acts; runtime only.
    std::optional<size_t> m_activeHirelingIndex;
    // One cell per member (formationCell); saved.
    std::vector<int32_t> m_memberFormationCells;
    // The outdoor map the party was last on; saved. A defeat in an Arena wakes the party on its continent.
    std::string m_lastOutdoorMapFileName;
    // World configuration like m_npcFollowersActive: not saved, not reset.
    bool m_formationTargetingActive = false;
    bool m_fleetFootWorld = false;
    // A setting like m_formationTargetingActive: not saved, not reset.
    bool m_mm9LootInOlderWorlds = false;
    bool m_partyPouches = false;
    bool m_lootPouch = false;
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
    std::vector<ExpiringPotionEffect> m_expiringPotionEffects;
};
}
