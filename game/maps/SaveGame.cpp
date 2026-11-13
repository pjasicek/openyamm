#include "game/maps/SaveGame.h"

#include "game/events/EventRuntime.h"
#include "game/events/EvtEnums.h"
#include "game/party/PlaythroughStatistics.h"
#include "game/tables/HouseTable.h"
#include "game/tables/ItemTable.h"

#include <algorithm>
#include <bitset>
#include <cctype>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <limits>
#include <type_traits>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t SaveVersion = 179;
constexpr uint32_t SaveVersionAttackSpell = 19;
constexpr uint32_t SaveVersionIndoorCorpseViews = 21;
constexpr uint32_t SaveVersionIndoorChestViews = 22;
constexpr uint32_t SaveVersionIndoorActorSpellEffects = 23;
constexpr uint32_t SaveVersionIndoorActorAiStates = 24;
constexpr uint32_t SaveVersionWandCharges = 25;
constexpr uint32_t SaveVersionLloydBeaconPreview = 26;
constexpr uint32_t SaveVersionActorCarriedItem = 27;
constexpr uint32_t SaveVersionDungeonTransitionDialogue = 28;
constexpr uint32_t SaveVersionIndoorSaveLoadParity = 29;
constexpr uint32_t SaveVersionCombatEffectState = 30;
constexpr uint32_t SaveVersionGlobalNpcState = 31;
constexpr uint32_t SaveVersionInputPromptAnswers = 32;
constexpr uint32_t SaveVersionDialogueParticipantPicture = 33;
constexpr uint32_t SaveVersionOutdoorJournalRevealMask = 34;
constexpr uint32_t SaveVersionRuntimeMapNotes = 35;
constexpr uint32_t SaveVersionScopedHistory = 36;
constexpr uint32_t SaveVersionMapLuaRuntimeOverlays = 37;
constexpr uint32_t SaveVersionHiredNpcFollowers = 38;
constexpr uint32_t SaveVersionGeneratedNpcOverrides = 39;
constexpr uint32_t SaveVersionDialogueActorSource = 40;
constexpr uint32_t SaveVersionPartyHiredNpcFollowers = 41;
constexpr uint32_t SaveVersionRuntimeMapNoteMapFile = 42;
constexpr uint32_t SaveVersionPartyEverOwnedItems = 43;
constexpr uint32_t SaveVersionNamedLuaVars = 44;
constexpr uint32_t SaveVersionActorExtraItemOverrides = 45;
constexpr uint32_t SaveVersionInputPromptAnswerSteps = 46;
constexpr uint32_t SaveVersionPersistentLuaRuntimeState = 47;
constexpr uint32_t SaveVersionOutdoorModelMechanisms = 48;
constexpr uint32_t SaveVersionOutdoorActorBolsterCache = 49;
constexpr uint32_t SaveVersionGeneratedMercenaryRecruits = 50;
constexpr uint32_t SaveVersionSessionNamedGlobalVars = 51;
constexpr uint32_t SaveVersionGeneratedMercenaryNpcPicture = 52;
constexpr uint32_t SaveVersionPartyContinentReputations = 53;
constexpr uint32_t SaveVersionPartyFineGold = 54;
constexpr uint32_t SaveVersionOutdoorLocationInfo = 55;
constexpr uint32_t SaveVersionFullProjectileState = 56;
constexpr uint32_t SaveVersionCharacterConditionStartTimes = 57;
constexpr uint32_t SaveVersionHiredNpcFollowerAbilityUseDay = 58;
constexpr uint32_t SaveVersionMonsterBolsterRewards = 59;
constexpr uint32_t SaveVersionMonsterBolsterDamageDice = 60;
constexpr uint32_t SaveVersionPendingSoundNames = 61;
constexpr uint32_t SaveVersionOutdoorRuntimeSaveParity = 62;
constexpr uint32_t SaveVersionProjectileVisualMode = 63;
constexpr uint32_t SaveVersionIndoorFireSpikeTraps = 64;
constexpr uint32_t SaveVersionHeldCursorItem = 65;
constexpr uint32_t SaveVersionActorDiagnosticSource = 66;
constexpr uint32_t SaveVersionLegacyEvtTimers = 67;
constexpr uint32_t SaveVersionHiredNpcFollowerIdentity = 68;
constexpr uint32_t SaveVersionOutdoorFaceAttributes = 69;
constexpr uint32_t SaveVersionOutdoorMechanismRotationDirection = 70;
constexpr uint32_t SaveVersionMm9DialogueActors = 71;
constexpr uint32_t SaveVersionRequiredContentPackages = 72;
constexpr uint32_t SaveVersionItemWeeklyEffects = 73;
constexpr uint32_t SaveVersionMm9ActorReactions = 74;
constexpr uint32_t SaveVersionActorProceduralDeathLoot = 75;
constexpr uint32_t SaveVersionMm9ItemSourceState = 76;
constexpr uint32_t SaveVersionMm9SemanticWorldItems = 77;
constexpr uint32_t SaveVersionMm9IndoorSemanticWorldItems = 78;
constexpr uint32_t SaveVersionTimedPrimaryStatBonuses = 79;
constexpr uint32_t SaveVersionSuspendedMm9RudeVendor = 80;
constexpr uint32_t SaveVersionVendorStockGeneration = 80;
constexpr uint32_t SaveVersionOutdoorDestructibles = 81;
constexpr uint32_t SaveVersionMm9Barrels = 82;
constexpr uint32_t SaveVersionTemporaryEventBonuses = 83;
constexpr uint32_t SaveVersionConsumedCorpseMarkers = 83;
constexpr uint32_t SaveVersionIndoorCamera = 84;
// Weather comes from the game-time weather model; the outdoor rain-intensity override is no longer saved.
constexpr uint32_t SaveVersionWeatherModel = 85;
constexpr uint32_t SaveVersionActorBehaviors = 86;
constexpr uint32_t SaveVersionActorBehaviorWardVisuals = 87;
constexpr uint32_t SaveVersionPartyExplosiveMixes = 88;
// Autonotes and history entries moved from each map's event state to the party.
constexpr uint32_t SaveVersionPartyAutonotes = 89;
constexpr uint32_t SaveVersionPartyHistory = 89;
constexpr uint32_t SaveVersionPartyJournalMapNotes = 89;
constexpr uint32_t SaveVersionBoundaryTravelDialogue = 89;
constexpr uint32_t SaveVersionPartyDaysWithoutRest = 90;
constexpr uint32_t SaveVersionActorRevealedLoot = 91;
constexpr uint32_t SaveVersionHardenedItems = 92;
constexpr uint32_t SaveVersionPotionCharacterBuffs = 93;
constexpr uint32_t SaveVersionMapMoveStartPoint = 94;
// Each character keeps a tech point pool for the technology skills (older saves load it as 0).
constexpr uint32_t SaveVersionCharacterTechPoints = 95;
// The ruleset id and options of the game (older saves load as the Standard ruleset).
constexpr uint32_t SaveVersionRuleset = 96;
// Items carry the fields a ruleset uses (ItemRulesetFields), and the game a root seed for its random streams.
constexpr uint32_t SaveVersionItemRulesetFields = 97;
constexpr uint32_t SaveVersionRandomRootSeed = 97;
// Actors carry what a ruleset resolved for them (ActorRulesetFacts), indoor actor HP is 32-bit, and MAW games keep
// their level banks (MawGameState).
constexpr uint32_t SaveVersionActorRulesetFacts = 98;
// MAW games keep their loot bad-luck counters (MawGameState).
constexpr uint32_t SaveVersionMawLootState = 99;
// Characters carry the state a ruleset keeps for them (CharacterRulesetState), and MAW games the auras they hold.
constexpr uint32_t SaveVersionCharacterRulesetState = 100;
constexpr uint32_t SaveVersionMawAuras = 100;
// The ruleset state of characters also keeps MAW's class spell switches and Elementalist progress.
constexpr uint32_t SaveVersionMawClassState = 101;
// Items count their crafts and keep a crafting material's state.
constexpr uint32_t SaveVersionItemCraftState = 102;
constexpr uint32_t SaveVersionMawCraftingPity = 103;
constexpr uint32_t SaveVersionElementalRotation = 104;
constexpr uint32_t SaveVersionRisenActors = 105;
// Items carry a dimension map's fields, and MAW games their dimension runs, the Dimensional Maps quest and the map drop
// counter.
constexpr uint32_t SaveVersionDimensionMaps = 106;
// Bosses keep the draw that places their level inside its band, and actors their Spear stacks.
constexpr uint32_t SaveVersionBossLevelDraw = 107;
// Characters keep MAW's poison timer and Divine Protection cooldown, MAW games the unique items they sold.
constexpr uint32_t SaveVersionMawCharacterTimers = 107;
// Actor ruleset facts mark the map's unique monsters.
constexpr uint32_t SaveVersionUniqueMonsters = 108;
// MAW games keep where their scroll, pedestal and temple auras came from.
constexpr uint32_t SaveVersionMawFixedAuras = 109;
constexpr uint32_t SaveVersionMawMultibag = 110;
// Characters keep the masteries a switch to horizontal progression, and a lone character's utility skills, took.
constexpr uint32_t SaveVersionProgressionMasteries = 111;
// The member who takes alchemy items when the party sorts (MAW).
constexpr uint32_t SaveVersionMawAlchemist = 112;
// MAW's challenge modes (devdocs/maw/PHASE9_SCOPE.md): the food Road to Insanity holds back, Beyond Madness's boss pity,
// the special attacks the Doom modes gave monsters.
constexpr uint32_t SaveVersionMawChallengeModes = 113;
// MAW games keep the maps cleared since their last refill (older saves take every completed map).
constexpr uint32_t SaveVersionMawClearedMaps = 114;
// A character's experience takes 64 bits: MAW levels need more than 4 billion (audit ROB-2-1).
constexpr uint32_t SaveVersionWideExperience = 115;
// Items on the floor indoors keep the whole item beside the MM record (audit ITM-1).
constexpr uint32_t SaveVersionIndoorHeldItems = 116;
// Indoor actors remember whether they came after the map's first fill (audit MON-11).
constexpr uint32_t SaveVersionActorSpawnedAfterFill = 117;
// MAW items keep their drop's ancient tier apart from their rarity (audit ALC-8).
constexpr uint32_t SaveVersionItemAncientTier = 118;
// A Regenerating boss keeps the party's hits on it with the actor (audit FCOR-2-6).
constexpr uint32_t SaveVersionRegeneratingHits = 119;
// Summoned actors keep the party member who summoned them: Summon Wisp's limit is per caster (MM8).
constexpr uint32_t SaveVersionActorSummoner = 120;
// MMMerge's four extra quick spells per character (ExtraQuickSpells.lua).
constexpr uint32_t SaveVersionExtraQuickSpells = 122;
// Each character's crafting and alchemy bags (MAW's crafting bag, zzzMaw_CraftingBag.lua; our alchemy bag).
constexpr uint32_t SaveVersionMawBagTags = 123;
// MAW games keep the maps the party left, the dimension runs cleared and the bounties claimed (the Progress tab).
constexpr uint32_t SaveVersionMawMapVisits = 124;
// Each character's six quick item slots (the potion radial).
constexpr uint32_t SaveVersionQuickItemSlots = 125;
// MAW's loot filter presets: the preset, the kinds without rarity turned into gold, and whether filtered drops stay where
// they fell (a flag on such an item); before, one rarity, migrated to the nearest preset.
constexpr uint32_t SaveVersionLootFilterPresets = 126;
// MAW games keep the barrels and cauldrons that raised a stat, which stay empty through refills.
constexpr uint32_t SaveVersionMawUsedStatDecorations = 127;
// MAW games keep Beyond Madness's death count in the save as well as in the death ledger.
constexpr uint32_t SaveVersionMawMadnessDeaths = 128;
// The decoration states (decorVars) are numbered with MMerge's campfire list; older map states keep a marker until the
// map renumbers them (EventRuntimeState::legacyCampFireDecorVars).
constexpr uint32_t SaveVersionMMergeCampfireDecorVars = 129;
// Each character remembers the spellbook page it last had open, as in MM8.
constexpr uint32_t SaveVersionSpellbookSchool = 130;
// A guild of several schools keeps a spellbook shelf for each (HouseServiceRuntime::spellbookShelfSchools); older saves
// kept one shelf of mixed schools.
constexpr uint32_t SaveVersionGuildSchoolShelves = 131;
// An outdoor monster the party hit beyond the full-AI range stays awake (OutdoorWorldRuntime provokedByParty).
constexpr uint32_t SaveVersionOutdoorProvokedActors = 132;
// ...and may shoot back from the distance of the hit (provokedAttackReach, dropped in version 169).
constexpr uint32_t SaveVersionOutdoorProvokedAttackReach = 133;
// A character's implant sockets (Character::implants, Hesper).
constexpr uint32_t SaveVersionCharacterImplants = 134;
constexpr uint32_t SaveVersionStoppedTimers = 135;
constexpr uint32_t SaveVersionActorKeepsHeight = 135;
constexpr uint32_t SaveVersionBehaviorSpeed = 135;
constexpr uint32_t SaveVersionProjectileHoming = 135;
constexpr uint32_t SaveVersionActorDormant = 135;
constexpr uint32_t SaveVersionActorPatrol = 136;
constexpr uint32_t SaveVersionWorkshopMods = 136;
// A homing missile's lock is a rate in radians a second; before, a cone tested every 1/60 s step.
constexpr uint32_t SaveVersionHomingLockRate = 137;
// A monster remembers that the party made it hostile, so a hit on it still alerts its friendly faction
// (angeredByParty indoors and outdoors).
constexpr uint32_t SaveVersionActorAngeredByParty = 138;
// Blood splats are saved without their triangles, which the map bakes again when it loads; they were most of a save's
// size before.
constexpr uint32_t SaveVersionBloodSplatsWithoutGeometry = 139;
// The Load and Save screens' summary (GameSaveSummary) leads the save behind its size; a save list reads only that.
constexpr uint32_t SaveVersionSummaryFirst = 140;
// History pages are numbered as in the history tables; MMerge events recorded them two pages late before
// (LegacyLuaExport read MM8's History variables with MM7's numbering).
constexpr uint32_t SaveVersionHistoryNumbering = 141;
// Outdoor actors keep MM's Nearby attribute (MapActorState::nearby) for Wizard Eye.
constexpr uint32_t SaveVersionOutdoorNearby = 142;
// The party keeps the stories it finished, with their time and score (completion certificates); older saves migrate
// to untimed records of the stories they already finished.
constexpr uint32_t SaveVersionWorldCompletions = 143;
// Liches no longer carry the Light and Dark immunity they took by mistake (Mind and Body, by race, are derived).
constexpr uint32_t SaveVersionLichImmunities = 144;
// MM6's small barrels are MMerge's stat barrels, not casks; older map states keep a marker until the map refills them
// (EventRuntimeState::legacySmallBarrelDecorVars).
constexpr uint32_t SaveVersionSmallStatBarrels = 144;
// Journal map notes say whether they are the player's own (JournalMapNote::personal).
constexpr uint32_t SaveVersionPersonalMapNotes = 145;
// The party keeps the MM9 talk rows it has chosen (Party::Snapshot::chosenMm9RudeRows), the conversation bar's
// visited marks; older saves start with none.
constexpr uint32_t SaveVersionChosenMm9RudeRows = 146;
// Placed actors keep their MM9 placement's AI settings (MapDeltaActor::mm9Ai); older saves have none (MM9's defaults).
constexpr uint32_t SaveVersionActorMm9AiPlacement = 147;
// An MM9 placement's hiding places (Mm9AiPlacementRecord::hidingPlaces); older saves have none.
constexpr uint32_t SaveVersionActorMm9HidingPlaces = 148;
// An MM9 placement's own script profile (Mm9AiPlacement::profile: its ScriptName's loop over its row's); an older
// save's placements are marked fromScene and take it from the map's scene when the map is next entered
// (refreshSavedLegacyMm9PlacementProfiles).
constexpr uint32_t SaveVersionActorMm9PlacementProfile = 149;
// Outdoor runtime spawns keep their MM9 placement (OutdoorWorldRuntime::MapActorState::mm9Ai); older saves have none
// (MM9's defaults).
constexpr uint32_t SaveVersionOutdoorSpawnMm9AiPlacement = 150;
// A Cryptic boss keeps its hidden affix (ActorRulesetFacts::crypticAffix); older saves have no Cryptic bosses.
constexpr uint32_t SaveVersionCrypticBossAffix = 151;
// The ruleset's Trainer hints preference (RulesetPreferences::trainerHints); older saves have it off.
constexpr uint32_t SaveVersionTrainerHints = 152;
// The continents whose Ledger of Teachers the party bought (Party::Snapshot::teacherLedgers); older saves have none.
constexpr uint32_t SaveVersionTeacherLedgers = 153;
// The ruleset's Bow preference (RulesetPreferences::bowDisabled, MAW's disableBow); older saves have the bow on.
constexpr uint32_t SaveVersionBowDisabled = 154;
// The party keeps the outdoor map it was last on (Party::Snapshot::lastOutdoorMapFileName); older saves have none.
constexpr uint32_t SaveVersionLastOutdoorMap = 155;
// A character's crafting and alchemy bag tags take 32 bits, for a solo character's 25 bags (OY-344); before, 8.
constexpr uint32_t SaveVersionWideBagTags = 156;
// The party keeps its MM9 hirelings (Party::Snapshot::mm9Hirelings); older saves have none.
constexpr uint32_t SaveVersionMm9Hirelings = 157;
// The members' MM9 formation cells (Party::Snapshot::memberFormationCells); older saves take the default formation.
// Hirelings saved before it had primary stats of 0 and get Party::Mm9HirelingPrimaryStat.
constexpr uint32_t SaveVersionMm9Formation = 158;
// The members' timed conditions (Character::conditionExpireGameMinutes, MM9 monster spells), and an MM9 placement's
// path stops (Mm9AiPlacementRecord::pathStops: the markers' facing, wait and clip), and a placed actor's draw scale
// (MapDeltaActor::drawScale, OutdoorWorldRuntime::MapActorState::drawScale); older saves have none of them.
constexpr uint32_t SaveVersionConditionExpiry = 159;
constexpr uint32_t SaveVersionMm9PathStops = 159;
constexpr uint32_t SaveVersionActorDrawScale = 159;
// An outdoor runtime spawn's patrol (OutdoorWorldRuntime::MapActorState::patrolPoints, evt.SummonMonstersById
// patrol); older saves have none.
constexpr uint32_t SaveVersionOutdoorSpawnPatrol = 160;
// A spinning mover's angle, speed and switch (RuntimeMechanismState::spin*, scene `mover.spin`); older saves have none.
constexpr uint32_t SaveVersionMoverSpin = 161;
// Each saved map state records the layout of the map it was saved on (mapLayoutIdentity, game/maps/MapLayoutIdentity.h);
// entering a map whose layout differs resets its state. Older states have none (0): judgeSavedMapState decides.
constexpr uint32_t SaveVersionMapLayoutIdentity = 162;
// The playthrough id, its statistics timeline and each member's statistics identity (PLAYTHROUGH_STATISTICS_PLAN.md).
constexpr uint32_t SaveVersionPlaythroughStatistics = 163;
// A placed actor's posed flag (MapDeltaActor::posed: MM9's posed props, never moved); older saves have none.
constexpr uint32_t SaveVersionActorPosed = 164;
// The scene's placed world items the party took (MapDeltaData::takenWorldItems); older saves have none.
constexpr uint32_t SaveVersionTakenWorldItems = 165;
// The indoor party's swim memory (whether it has been under water, a surface jump in flight); older saves guess it.
constexpr uint32_t SaveVersionPartySwimMemory = 166;
// Each character's battle orders (game/party/BattleOrders.h) replace the single attack spell, which older saves turn
// into one order (setAttackSpell).
constexpr uint32_t SaveVersionBattleOrders = 167;
// The party buff of MM9's Fleet Foot (PartyBuffId::FleetFoot, the last); older saves have one party buff fewer.
constexpr uint32_t SaveVersionFleetFootBuff = 168;
// Outdoor monsters no longer keep the reach of a far hit (provokedAttackReach, versions 133-168): the party hits no
// farther than monsters shoot (GameplayActorService::partyHitReach).
constexpr uint32_t SaveVersionNoProvokedAttackReach = 169;
// An indoor map's Armageddon in progress (IndoorWorldRuntime::Snapshot::armageddon: a BLV open to the sky); older saves
// have none.
constexpr uint32_t SaveVersionIndoorArmageddon = 170;
// A sprite object's key (MapDeltaSpriteObject::objectKey); older saves have none and the indoor runtime assigns them.
constexpr uint32_t SaveVersionSpriteObjectKeys = 171;
// Saves 172 to 177 hold the retired per-game "Loot from other worlds" choice after the ruleset options; it is read and
// dropped (the Gameplay setting GameSettings::mm9LootInOlderWorlds replaced it, devdocs/LOOT_POOL.md).
constexpr uint32_t SaveVersionOtherWorldsLoot = 172;
constexpr uint32_t SaveVersionOtherWorldsLootRetired = 178;
// An MM9 placement's idle clip (Mm9AiPlacement::idleClip, scene mm9_ai.idle_clip); an older save's placements are
// marked fromScene and take it, with the profile, from the map's scene when the map is next entered.
constexpr uint32_t SaveVersionMm9IdleClip = 173;
// A placed actor's held items (MapDeltaActor::heldItems, OutdoorWorldRuntime::MapActorState::heldItems) and an MM9
// placement's routines (Mm9AiPlacementRecord::routines); an older save's placements are marked fromScene and take
// their routines from the map's scene when the map is next entered.
constexpr uint32_t SaveVersionActorHeldItems = 174;
constexpr uint32_t SaveVersionMm9Routines = 174;
// The save's playthrough id and the real time played up to it are in the summary (GameSaveSummary::playthrough), for
// the save lists; older saves keep the id behind the game state and the time inside the sealed timeline.
constexpr uint32_t SaveVersionSummaryPlaythrough = 175;
// Each battle order's place and renew time, and each character's upkeep list (game/party/BattleOrders.h).
constexpr uint32_t SaveVersionUpkeepOrders = 176;
constexpr char SaveMagic[8] = {'O', 'Y', 'S', 'A', 'V', 'E', '1', '\0'};

std::string toLowerCopy(const std::string &value)
{
    std::string normalized = value;

    for (char &character : normalized)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return normalized;
}

// The file is `slot`.oysav or `slot`_<playthrough id>.oysav.
bool isSaveSlotPath(const std::filesystem::path &path, const std::string &slot)
{
    const std::string stem = toLowerCopy(path.stem().string());
    return stem == slot || stem.rfind(slot + "_", 0) == 0;
}

std::filesystem::path saveSlotPath(const std::string &slot, const std::string &playthroughId)
{
    return std::filesystem::path("saves")
        / (playthroughId.empty() ? slot + ".oysav" : slot + "_" + playthroughId + ".oysav");
}

int savePathDisplayPriority(const std::filesystem::path &path)
{
    // Quicksave first, the save players load most (Discord request, 2026-10-28), then Autosave.
    if (isQuickSavePath(path))
    {
        return 0;
    }

    if (isAutosavePath(path))
    {
        return 1;
    }

    return 2;
}

class BinaryWriter
{
public:
    void writeBytes(const void *pData, size_t size)
    {
        const uint8_t *pBytes = static_cast<const uint8_t *>(pData);
        m_bytes.insert(m_bytes.end(), pBytes, pBytes + size);
    }

    template <typename T>
    void write(const T &value)
    {
        writeValue(*this, value);
    }

    const std::vector<uint8_t> &bytes() const
    {
        return m_bytes;
    }

private:
    std::vector<uint8_t> m_bytes;
};

class BinaryReader
{
public:
    explicit BinaryReader(const std::vector<uint8_t> &bytes)
        : m_bytes(bytes)
    {
    }

    bool readBytes(void *pData, size_t size)
    {
        if (size > remainingBytes())
        {
            m_failed = true;
            return false;
        }

        std::memcpy(pData, m_bytes.data() + m_offset, size);
        m_offset += size;
        return true;
    }

    bool skipBytes(size_t size)
    {
        if (size > remainingBytes())
        {
            m_failed = true;
            return false;
        }

        m_offset += size;
        return true;
    }

    template <typename T>
    bool read(T &value)
    {
        return readValue(*this, value);
    }

    bool failed() const
    {
        return m_failed;
    }

    size_t remainingBytes() const
    {
        if (m_offset >= m_bytes.size())
        {
            return 0;
        }

        return m_bytes.size() - m_offset;
    }

    void setVersion(uint32_t version)
    {
        m_version = version;
    }

    uint32_t version() const
    {
        return m_version;
    }

private:
    const std::vector<uint8_t> &m_bytes;
    size_t m_offset = 0;
    bool m_failed = false;
    uint32_t m_version = SaveVersion;
};

void writeValue(BinaryWriter &writer, const HiredNpcFollower &value);
void writeValue(BinaryWriter &writer, const WorldCompletionRecord &value);
bool readValue(BinaryReader &reader, WorldCompletionRecord &value);
void writeValue(BinaryWriter &writer, const ArmageddonState &value);
bool readValue(BinaryReader &reader, ArmageddonState &value);
void writeValue(BinaryWriter &writer, const MawDimensionRun &value);
bool readValue(BinaryReader &reader, MawDimensionRun &value);
void writeValue(BinaryWriter &writer, const MawMapVisit &value);
bool readValue(BinaryReader &reader, MawMapVisit &value);
bool readValue(BinaryReader &reader, HiredNpcFollower &value);
void writeValue(BinaryWriter &writer, const Mm9PartyHireling &value);
bool readValue(BinaryReader &reader, Mm9PartyHireling &value);
void writeValue(BinaryWriter &writer, const GameplayProjectileService::Snapshot &value);
bool readValue(BinaryReader &reader, GameplayProjectileService::Snapshot &value);
void writeValue(BinaryWriter &writer, const ActorBehaviorRuntime::Snapshot &value);
bool readValue(BinaryReader &reader, ActorBehaviorRuntime::Snapshot &value);

bool canReadSerializedElementCount(const BinaryReader &reader, uint64_t count)
{
    if (count > std::numeric_limits<size_t>::max())
    {
        return false;
    }

    return count <= reader.remainingBytes();
}

template <typename T>
requires(std::is_arithmetic_v<T>)
void writeValue(BinaryWriter &writer, const T &value)
{
    writer.writeBytes(&value, sizeof(value));
}

template <typename T>
requires(std::is_arithmetic_v<T>)
bool readValue(BinaryReader &reader, T &value)
{
    return reader.readBytes(&value, sizeof(value));
}

template <typename T>
requires(std::is_enum_v<T>)
void writeValue(BinaryWriter &writer, const T &value)
{
    const std::underlying_type_t<T> rawValue = static_cast<std::underlying_type_t<T>>(value);
    writeValue(writer, rawValue);
}

template <typename T>
requires(std::is_enum_v<T>)
bool readValue(BinaryReader &reader, T &value)
{
    std::underlying_type_t<T> rawValue = {};

    if (!readValue(reader, rawValue))
    {
        return false;
    }

    value = static_cast<T>(rawValue);
    return true;
}

void writeValue(BinaryWriter &writer, const std::string &value)
{
    const uint64_t size = static_cast<uint64_t>(value.size());
    writeValue(writer, size);

    if (!value.empty())
    {
        writer.writeBytes(value.data(), value.size());
    }
}

bool readValue(BinaryReader &reader, std::string &value)
{
    uint64_t size = 0;

    if (!readValue(reader, size))
    {
        return false;
    }

    if (!canReadSerializedElementCount(reader, size))
    {
        return false;
    }

    value.resize(static_cast<size_t>(size));
    return value.empty() || reader.readBytes(value.data(), value.size());
}

template <size_t N>
void writeValue(BinaryWriter &writer, const std::bitset<N> &value)
{
    writeValue(writer, value.to_string());
}

template <size_t N>
bool readValue(BinaryReader &reader, std::bitset<N> &value)
{
    std::string encoded;

    if (!readValue(reader, encoded) || encoded.size() != N)
    {
        return false;
    }

    value = std::bitset<N>(encoded);
    return true;
}

template <typename T>
void writeValue(BinaryWriter &writer, const std::optional<T> &value)
{
    writeValue(writer, value.has_value());

    if (value.has_value())
    {
        writeValue(writer, *value);
    }
}

template <typename T>
bool readValue(BinaryReader &reader, std::optional<T> &value)
{
    bool hasValue = false;

    if (!readValue(reader, hasValue))
    {
        return false;
    }

    if (!hasValue)
    {
        value.reset();
        return true;
    }

    T decoded = {};

    if (!readValue(reader, decoded))
    {
        return false;
    }

    value = std::move(decoded);
    return true;
}

template <typename T>
void writeValue(BinaryWriter &writer, const std::vector<T> &value)
{
    const uint64_t size = static_cast<uint64_t>(value.size());
    writeValue(writer, size);

    for (const T &entry : value)
    {
        writeValue(writer, entry);
    }
}

template <typename T>
bool readValue(BinaryReader &reader, std::vector<T> &value)
{
    uint64_t size = 0;

    if (!readValue(reader, size))
    {
        return false;
    }

    if (!canReadSerializedElementCount(reader, size))
    {
        return false;
    }

    value.clear();
    value.reserve(static_cast<size_t>(size));

    for (uint64_t index = 0; index < size; ++index)
    {
        T entry = {};

        if (!readValue(reader, entry))
        {
            return false;
        }

        value.push_back(std::move(entry));
    }

    return true;
}

template <typename T, size_t N>
void writeValue(BinaryWriter &writer, const std::array<T, N> &value)
{
    for (const T &entry : value)
    {
        writeValue(writer, entry);
    }
}

template <typename T, size_t N>
bool readValue(BinaryReader &reader, std::array<T, N> &value)
{
    for (T &entry : value)
    {
        if (!readValue(reader, entry))
        {
            return false;
        }
    }

    return true;
}

template <typename K, typename V>
void writeValue(BinaryWriter &writer, const std::unordered_map<K, V> &value)
{
    const uint64_t size = static_cast<uint64_t>(value.size());
    writeValue(writer, size);

    for (const auto &[key, entry] : value)
    {
        writeValue(writer, key);
        writeValue(writer, entry);
    }
}

template <typename K, typename V>
bool readValue(BinaryReader &reader, std::unordered_map<K, V> &value)
{
    uint64_t size = 0;

    if (!readValue(reader, size))
    {
        return false;
    }

    if (!canReadSerializedElementCount(reader, size))
    {
        return false;
    }

    value.clear();
    value.reserve(static_cast<size_t>(size));

    for (uint64_t index = 0; index < size; ++index)
    {
        K key = {};
        V entry = {};

        if (!readValue(reader, key) || !readValue(reader, entry))
        {
            return false;
        }

        value.emplace(std::move(key), std::move(entry));
    }

    return true;
}

template <typename T>
void writeValue(BinaryWriter &writer, const std::unordered_set<T> &value)
{
    const uint64_t size = static_cast<uint64_t>(value.size());
    writeValue(writer, size);

    for (const T &entry : value)
    {
        writeValue(writer, entry);
    }
}

template <typename T>
bool readValue(BinaryReader &reader, std::unordered_set<T> &value)
{
    uint64_t size = 0;

    if (!readValue(reader, size))
    {
        return false;
    }

    if (!canReadSerializedElementCount(reader, size))
    {
        return false;
    }

    value.clear();
    value.reserve(static_cast<size_t>(size));

    for (uint64_t index = 0; index < size; ++index)
    {
        T entry = {};

        if (!readValue(reader, entry))
        {
            return false;
        }

        value.insert(std::move(entry));
    }

    return true;
}

void writeValue(BinaryWriter &writer, const QuickItemSlot &value)
{
    writeValue(writer, value.itemId);
    writeValue(writer, uint8_t(value.bottleRule));
}

bool readValue(BinaryReader &reader, QuickItemSlot &value)
{
    uint8_t bottleRule = 0;

    if (!readValue(reader, value.itemId) || !readValue(reader, bottleRule))
    {
        return false;
    }

    value.bottleRule = bottleRule == uint8_t(QuickItemBottleRule::Strongest) ? QuickItemBottleRule::Strongest
                                                                             : QuickItemBottleRule::Weakest;
    return true;
}

void writeValue(BinaryWriter &writer, const CharacterSkill &value)
{
    writeValue(writer, value.name);
    writeValue(writer, value.level);
    writeValue(writer, value.mastery);
}

bool readValue(BinaryReader &reader, CharacterSkill &value)
{
    return readValue(reader, value.name)
        && readValue(reader, value.level)
        && readValue(reader, value.mastery);
}

void writeValue(BinaryWriter &writer, const InventoryItem &value);
bool readValue(BinaryReader &reader, InventoryItem &value);

// One byte for a Standard character; the fields follow only when a ruleset set any.
void writeValue(BinaryWriter &writer, const CharacterRulesetState &value)
{
    const bool present = !value.empty();
    writeValue(writer, present);

    if (present)
    {
        writeValue(writer, value.rememberedMasteries);
        writeValue(writer, value.coverDisabled);
        writeValue(writer, value.manaShieldDisabled);
        writeValue(writer, value.classToggles);

        for (const double progress : value.elementalProgress)
        {
            writeValue(writer, progress);
        }

        writeValue(writer, uint32_t(value.potionEffects.size()));

        for (const TimedPotionEffect &effect : value.potionEffects)
        {
            writeValue(writer, effect.kind);
            writeValue(writer, effect.key);
            writeValue(writer, effect.amount);
            writeValue(writer, effect.remainingSeconds);
        }

        writeValue(writer, value.potionSteps);
        writeValue(writer, value.elementalRotationDisabled);
        writeValue(writer, value.poisonSeconds);
        writeValue(writer, value.divineProtectionReadyGameMinutes);
        writeValue(writer, value.legendaryProtectionReadyGameMinutes);
        writeValue(writer, value.currentBag);
        writeValue(writer, uint32_t(value.storedBags.size()));

        for (const auto &[bag, items] : value.storedBags)
        {
            writeValue(writer, bag);
            writeValue(writer, items);
        }

        writeValue(writer, value.progressionStoredMasteries);
        writeValue(writer, value.soloStoredMasteries);
        writeValue(writer, value.craftingBags);
        writeValue(writer, value.alchemyBags);
    }
}

bool readValue(BinaryReader &reader, CharacterRulesetState &value)
{
    bool present = false;
    value = {};
    const auto readClassState = [&reader, &value]()
    {
        return reader.version() < SaveVersionMawClassState
            || (readValue(reader, value.classToggles)
                && std::all_of(value.elementalProgress.begin(), value.elementalProgress.end(),
                    [&reader](double &progress) { return readValue(reader, progress); }));
    };
    const auto readPotionState = [&reader, &value]()
    {
        uint32_t count = 0;

        if (reader.version() < SaveVersionItemCraftState)
        {
            return true;
        }

        if (!readValue(reader, count) || !canReadSerializedElementCount(reader, count))
        {
            return false;
        }

        value.potionEffects.resize(count);

        for (TimedPotionEffect &effect : value.potionEffects)
        {
            if (!readValue(reader, effect.kind) || !readValue(reader, effect.key) || !readValue(reader, effect.amount)
                || !readValue(reader, effect.remainingSeconds))
            {
                return false;
            }
        }

        return readValue(reader, value.potionSteps);
    };
    const auto readRotationState = [&reader, &value]()
    {
        return reader.version() < SaveVersionElementalRotation || readValue(reader, value.elementalRotationDisabled);
    };
    const auto readTimers = [&reader, &value]()
    {
        return reader.version() < SaveVersionMawCharacterTimers
            || (readValue(reader, value.poisonSeconds) && readValue(reader, value.divineProtectionReadyGameMinutes)
                && readValue(reader, value.legendaryProtectionReadyGameMinutes));
    };
    const auto readBagTags = [&reader, &value]()
    {
        if (reader.version() < SaveVersionMawBagTags)
        {
            return true;
        }

        if (reader.version() >= SaveVersionWideBagTags)
        {
            return readValue(reader, value.craftingBags) && readValue(reader, value.alchemyBags);
        }

        uint8_t crafting = 0;
        uint8_t alchemy = 0;

        if (!readValue(reader, crafting) || !readValue(reader, alchemy))
        {
            return false;
        }

        value.craftingBags = crafting;
        value.alchemyBags = alchemy;
        return true;
    };
    const auto readBags = [&reader, &value]()
    {
        uint32_t count = 0;

        if (reader.version() < SaveVersionMawMultibag)
        {
            return true;
        }

        if (!readValue(reader, value.currentBag) || !readValue(reader, count)
            || !canReadSerializedElementCount(reader, count))
        {
            return false;
        }

        for (uint32_t index = 0; index < count; ++index)
        {
            uint8_t bag = 0;
            std::vector<InventoryItem> items;

            if (!readValue(reader, bag) || !readValue(reader, items))
            {
                return false;
            }

            value.storedBags[bag] = std::move(items);
        }

        return true;
    };
    return readValue(reader, present)
        && (!present
            || (readValue(reader, value.rememberedMasteries)
                && readValue(reader, value.coverDisabled)
                && readValue(reader, value.manaShieldDisabled)
                && readClassState()
                && readPotionState()
                && readRotationState()
                && readTimers()
                && readBags()
                && (reader.version() < SaveVersionProgressionMasteries
                    || (readValue(reader, value.progressionStoredMasteries)
                        && readValue(reader, value.soloStoredMasteries)))
                && readBagTags()));
}

// One byte for a Standard item; the fields follow only when a ruleset set any.
void writeValue(BinaryWriter &writer, const ItemRulesetFields &value)
{
    const bool present = !value.empty();
    writeValue(writer, present);

    if (!present)
    {
        return;
    }

    writeValue(writer, value.secondStandardEnchantId);
    writeValue(writer, value.secondStandardEnchantPower);
    writeValue(writer, value.lootRarity);
    writeValue(writer, value.legendaryAffixId);
    writeValue(writer, value.itemPower);
    writeValue(writer, value.dropLevel);
    writeValue(writer, value.qualityPercent);
    writeValue(writer, value.craftSeed);
    writeValue(writer, value.potionCharges);
    writeValue(writer, value.craftCount);
    writeValue(writer, value.craftState);
    writeValue(writer, value.dimensionMapId);
    writeValue(writer, value.dimensionAffixes);
    writeValue(writer, value.dimensionActiveSlots);
    writeValue(writer, value.dimensionPower);
    writeValue(writer, value.ancientTier);
    writeValue(writer, value.lootFiltered);
}

void writeValue(BinaryWriter &writer, const ActorRulesetFacts &value)
{
    const bool present = !value.empty();
    writeValue(writer, present);

    if (!present)
    {
        return;
    }

    writeValue(writer, value.level);
    writeValue(writer, value.familyLevel);
    writeValue(writer, value.tier);
    writeValue(writer, value.bossAffix);
    writeValue(writer, value.bossHealthMultiplier);
    writeValue(writer, value.bossDamageMultiplier);
    writeValue(writer, value.attack1Damage);
    writeValue(writer, value.attack2Damage);
    writeValue(writer, value.experience);
    writeValue(writer, value.maxHp);
    writeValue(writer, value.risen);
    writeValue(writer, value.bossLevelDraw);
    writeValue(writer, value.spearDamageTaken);
    writeValue(writer, value.legendaryDamageTaken);
    writeValue(writer, value.unique);
    writeValue(writer, value.doomSpecialAttack);
    writeValue(writer, value.regeneratingHits);
    writeValue(writer, value.crypticAffix);
}

bool readValue(BinaryReader &reader, ActorRulesetFacts &value)
{
    bool present = false;

    if (!readValue(reader, present))
    {
        return false;
    }

    value = {};
    return !present
        || (readValue(reader, value.level)
            && readValue(reader, value.familyLevel)
            && readValue(reader, value.tier)
            && readValue(reader, value.bossAffix)
            && readValue(reader, value.bossHealthMultiplier)
            && readValue(reader, value.bossDamageMultiplier)
            && readValue(reader, value.attack1Damage)
            && readValue(reader, value.attack2Damage)
            && readValue(reader, value.experience)
            && readValue(reader, value.maxHp)
            && (reader.version() < SaveVersionRisenActors || readValue(reader, value.risen))
            && (reader.version() < SaveVersionBossLevelDraw
                || (readValue(reader, value.bossLevelDraw) && readValue(reader, value.spearDamageTaken)
                    && readValue(reader, value.legendaryDamageTaken)))
            && (reader.version() < SaveVersionUniqueMonsters || readValue(reader, value.unique))
            && (reader.version() < SaveVersionMawChallengeModes || readValue(reader, value.doomSpecialAttack))
            && (reader.version() < SaveVersionRegeneratingHits || readValue(reader, value.regeneratingHits))
            && (reader.version() < SaveVersionCrypticBossAffix || readValue(reader, value.crypticAffix)));
}

void writeValue(BinaryWriter &writer, const MawDimensionRun &value)
{
    writeValue(writer, value.affixes);
    writeValue(writer, value.power);
    writeValue(writer, value.families);
    writeValue(writer, value.entering);
    writeValue(writer, value.completed);
    writeValue(writer, value.questTier);
}

bool readValue(BinaryReader &reader, MawDimensionRun &value)
{
    return readValue(reader, value.affixes)
        && readValue(reader, value.power)
        && readValue(reader, value.families)
        && readValue(reader, value.entering)
        && readValue(reader, value.completed)
        && readValue(reader, value.questTier);
}

void writeValue(BinaryWriter &writer, const MawGameState &value)
{
    writeValue(writer, value.continentLevels);
    writeValue(writer, value.bankedExperience);
    writeValue(writer, value.bankedLevel);
    writeValue(writer, value.mapResetCounts);
    writeValue(writer, value.completedMaps);
    writeValue(writer, value.celestialPity);
    writeValue(writer, value.legendaryPity);
    writeValue(writer, value.primordialPity);
    writeValue(writer, value.artifactPity);
    writeValue(writer, value.artifactDrops);
    writeValue(writer, value.legendaryAffixDrops);
    writeValue(writer, value.auraHolders);
    writeValue(writer, value.craftingPity);
    writeValue(writer, value.dimensionRuns);
    writeValue(writer, value.dimensionQuest.tierLevel);
    writeValue(writer, value.dimensionQuest.mapGiven);
    writeValue(writer, value.dimensionQuest.cleared);
    writeValue(writer, value.dimensionQuest.clearedLevel);
    writeValue(writer, value.dimensionQuest.clearedMapName);
    writeValue(writer, value.dimensionQuest.done);
    writeValue(writer, value.mapDropPity);
    writeValue(writer, value.mapsDropped);
    writeValue(writer, value.soldUniqueItems);
    writeValue(writer, value.fixedAuraMaps);
    writeValue(writer, value.alchemistMember);
    writeValue(writer, value.heldFood);
    writeValue(writer, value.broodlordPity);
    writeValue(writer, value.omnipotentPity);
    writeValue(writer, value.clearedSinceRefill);
    writeValue(writer, value.mapVisits);
    writeValue(writer, value.dimensionRunsCleared);
    writeValue(writer, value.bountiesClaimed);
    writeValue(writer, value.usedStatDecorations);
    writeValue(writer, value.madnessDeaths);
}

void writeValue(BinaryWriter &writer, const MawMapVisit &value)
{
    writeValue(writer, value.slain);
    writeValue(writer, value.counted);
    writeValue(writer, value.lastRefillDay);
}

bool readValue(BinaryReader &reader, MawMapVisit &value)
{
    return readValue(reader, value.slain) && readValue(reader, value.counted) && readValue(reader, value.lastRefillDay);
}

bool readValue(BinaryReader &reader, MawGameState &value)
{
    return readValue(reader, value.continentLevels)
        && readValue(reader, value.bankedExperience)
        && readValue(reader, value.bankedLevel)
        && readValue(reader, value.mapResetCounts)
        && readValue(reader, value.completedMaps)
        && (reader.version() < SaveVersionMawLootState
            || (readValue(reader, value.celestialPity)
                && readValue(reader, value.legendaryPity)
                && readValue(reader, value.primordialPity)
                && readValue(reader, value.artifactPity)
                && readValue(reader, value.artifactDrops)
                && readValue(reader, value.legendaryAffixDrops)))
        && (reader.version() < SaveVersionMawAuras || readValue(reader, value.auraHolders))
        && (reader.version() < SaveVersionMawCraftingPity || readValue(reader, value.craftingPity))
        && (reader.version() < SaveVersionDimensionMaps
            || (readValue(reader, value.dimensionRuns)
                && readValue(reader, value.dimensionQuest.tierLevel)
                && readValue(reader, value.dimensionQuest.mapGiven)
                && readValue(reader, value.dimensionQuest.cleared)
                && readValue(reader, value.dimensionQuest.clearedLevel)
                && readValue(reader, value.dimensionQuest.clearedMapName)
                && readValue(reader, value.dimensionQuest.done)
                && readValue(reader, value.mapDropPity)
                && readValue(reader, value.mapsDropped)))
        && (reader.version() < SaveVersionMawCharacterTimers || readValue(reader, value.soldUniqueItems))
        && (reader.version() < SaveVersionMawFixedAuras || readValue(reader, value.fixedAuraMaps))
        && (reader.version() < SaveVersionMawAlchemist || readValue(reader, value.alchemistMember))
        && (reader.version() < SaveVersionMawChallengeModes
            || (readValue(reader, value.heldFood)
                && readValue(reader, value.broodlordPity)
                && readValue(reader, value.omnipotentPity)))
        && (reader.version() < SaveVersionMawClearedMaps ? (value.clearedSinceRefill = value.completedMaps, true)
                                                         : readValue(reader, value.clearedSinceRefill))
        && (reader.version() < SaveVersionMawMapVisits
            || (readValue(reader, value.mapVisits)
                && readValue(reader, value.dimensionRunsCleared)
                && readValue(reader, value.bountiesClaimed)))
        && (reader.version() < SaveVersionMawUsedStatDecorations || readValue(reader, value.usedStatDecorations))
        && (reader.version() < SaveVersionMawMadnessDeaths || readValue(reader, value.madnessDeaths));
}

// Before the tier was saved apart: a drop's rarity tells its tier (crafted changes before then cannot be told).
uint8_t ancientTierOf(const ItemRulesetFields &value)
{
    // MawRarity: Ancient 5, Primordial 6, Celestial 8.
    return value.lootRarity == 5 ? 1 : value.lootRarity == 6 || value.lootRarity == 8 ? 2 : 0;
}

bool readValue(BinaryReader &reader, ItemRulesetFields &value)
{
    bool present = false;

    if (!readValue(reader, present))
    {
        return false;
    }

    value = {};
    return !present
        || (readValue(reader, value.secondStandardEnchantId)
            && readValue(reader, value.secondStandardEnchantPower)
            && readValue(reader, value.lootRarity)
            && readValue(reader, value.legendaryAffixId)
            && readValue(reader, value.itemPower)
            && readValue(reader, value.dropLevel)
            && readValue(reader, value.qualityPercent)
            && readValue(reader, value.craftSeed)
            && readValue(reader, value.potionCharges)
            && (reader.version() < SaveVersionItemCraftState
                || (readValue(reader, value.craftCount) && readValue(reader, value.craftState)))
            && (reader.version() < SaveVersionDimensionMaps
                || (readValue(reader, value.dimensionMapId)
                    && readValue(reader, value.dimensionAffixes)
                    && readValue(reader, value.dimensionActiveSlots)
                    && readValue(reader, value.dimensionPower)))
            && (reader.version() >= SaveVersionItemAncientTier ? readValue(reader, value.ancientTier)
                                                               : (value.ancientTier = ancientTierOf(value), true))
            && (reader.version() < SaveVersionLootFilterPresets || readValue(reader, value.lootFiltered)));
}

void writeValue(BinaryWriter &writer, const InventoryItem &value)
{
    writeValue(writer, value.objectDescriptionId);
    writeValue(writer, value.quantity);
    writeValue(writer, value.width);
    writeValue(writer, value.height);
    writeValue(writer, value.gridX);
    writeValue(writer, value.gridY);
    writeValue(writer, value.identified);
    writeValue(writer, value.broken);
    writeValue(writer, value.stolen);
    writeValue(writer, value.standardEnchantId);
    writeValue(writer, value.standardEnchantPower);
    writeValue(writer, value.specialEnchantId);
    writeValue(writer, value.artifactId);
    writeValue(writer, value.rarity);
    writeValue(writer, value.currentCharges);
    writeValue(writer, value.maxCharges);
    writeValue(writer, value.temporaryBonusRemainingSeconds);
    writeValue(writer, value.hardened);
    writeValue(writer, value.rulesetFields);
    writeValue(writer, value.workshopModId);
}

bool readValue(BinaryReader &reader, InventoryItem &value)
{
    return readValue(reader, value.objectDescriptionId)
        && readValue(reader, value.quantity)
        && readValue(reader, value.width)
        && readValue(reader, value.height)
        && readValue(reader, value.gridX)
        && readValue(reader, value.gridY)
        && readValue(reader, value.identified)
        && readValue(reader, value.broken)
        && readValue(reader, value.stolen)
        && readValue(reader, value.standardEnchantId)
        && readValue(reader, value.standardEnchantPower)
        && readValue(reader, value.specialEnchantId)
        && readValue(reader, value.artifactId)
        && readValue(reader, value.rarity)
        && (reader.version() < SaveVersionWandCharges || readValue(reader, value.currentCharges))
        && (reader.version() < SaveVersionWandCharges || readValue(reader, value.maxCharges))
        && readValue(reader, value.temporaryBonusRemainingSeconds)
        && (reader.version() < SaveVersionHardenedItems || readValue(reader, value.hardened))
        && (reader.version() < SaveVersionItemRulesetFields || readValue(reader, value.rulesetFields))
        && (reader.version() < SaveVersionWorkshopMods || readValue(reader, value.workshopModId));
}

void writeValue(BinaryWriter &writer, const LloydBeacon &value)
{
    writeValue(writer, value.mapName);
    writeValue(writer, value.locationName);
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.z);
    writeValue(writer, value.directionDegrees);
    writeValue(writer, value.remainingSeconds);
    writeValue(writer, value.previewWidth);
    writeValue(writer, value.previewHeight);
    writeValue(writer, value.previewPixelsBgra);
}

bool readValue(BinaryReader &reader, LloydBeacon &value)
{
    return readValue(reader, value.mapName)
        && readValue(reader, value.locationName)
        && readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.z)
        && readValue(reader, value.directionDegrees)
        && readValue(reader, value.remainingSeconds)
        && (reader.version() < SaveVersionLloydBeaconPreview || readValue(reader, value.previewWidth))
        && (reader.version() < SaveVersionLloydBeaconPreview || readValue(reader, value.previewHeight))
        && (reader.version() < SaveVersionLloydBeaconPreview || readValue(reader, value.previewPixelsBgra));
}

void writeValue(BinaryWriter &writer, const CharacterResistanceSet &value)
{
    writeValue(writer, value.fire);
    writeValue(writer, value.air);
    writeValue(writer, value.water);
    writeValue(writer, value.earth);
    writeValue(writer, value.mind);
    writeValue(writer, value.body);
    writeValue(writer, value.spirit);
}

bool readValue(BinaryReader &reader, CharacterResistanceSet &value)
{
    return readValue(reader, value.fire)
        && readValue(reader, value.air)
        && readValue(reader, value.water)
        && readValue(reader, value.earth)
        && readValue(reader, value.mind)
        && readValue(reader, value.body)
        && readValue(reader, value.spirit);
}

void writeValue(BinaryWriter &writer, const CharacterResistanceImmunitySet &value)
{
    writeValue(writer, value.fire);
    writeValue(writer, value.air);
    writeValue(writer, value.water);
    writeValue(writer, value.earth);
    writeValue(writer, value.mind);
    writeValue(writer, value.body);
    writeValue(writer, value.spirit);
}

bool readValue(BinaryReader &reader, CharacterResistanceImmunitySet &value)
{
    return readValue(reader, value.fire)
        && readValue(reader, value.air)
        && readValue(reader, value.water)
        && readValue(reader, value.earth)
        && readValue(reader, value.mind)
        && readValue(reader, value.body)
        && readValue(reader, value.spirit);
}

void writeValue(BinaryWriter &writer, const CharacterStatBonuses &value)
{
    writeValue(writer, value.might);
    writeValue(writer, value.intellect);
    writeValue(writer, value.personality);
    writeValue(writer, value.endurance);
    writeValue(writer, value.speed);
    writeValue(writer, value.accuracy);
    writeValue(writer, value.luck);
    writeValue(writer, value.maxHealth);
    writeValue(writer, value.maxSpellPoints);
    writeValue(writer, value.armorClass);
    writeValue(writer, value.meleeAttack);
    writeValue(writer, value.rangedAttack);
    writeValue(writer, value.meleeDamage);
    writeValue(writer, value.rangedDamage);
    writeValue(writer, value.resistances);
}

bool readValue(BinaryReader &reader, CharacterStatBonuses &value)
{
    return readValue(reader, value.might)
        && readValue(reader, value.intellect)
        && readValue(reader, value.personality)
        && readValue(reader, value.endurance)
        && readValue(reader, value.speed)
        && readValue(reader, value.accuracy)
        && readValue(reader, value.luck)
        && readValue(reader, value.maxHealth)
        && readValue(reader, value.maxSpellPoints)
        && readValue(reader, value.armorClass)
        && readValue(reader, value.meleeAttack)
        && readValue(reader, value.rangedAttack)
        && readValue(reader, value.meleeDamage)
        && readValue(reader, value.rangedDamage)
        && readValue(reader, value.resistances);
}

void writeValue(BinaryWriter &writer, const CharacterEquipment &value)
{
    writeValue(writer, value.offHand);
    writeValue(writer, value.mainHand);
    writeValue(writer, value.bow);
    writeValue(writer, value.armor);
    writeValue(writer, value.helm);
    writeValue(writer, value.belt);
    writeValue(writer, value.cloak);
    writeValue(writer, value.gauntlets);
    writeValue(writer, value.boots);
    writeValue(writer, value.amulet);
    writeValue(writer, value.ring1);
    writeValue(writer, value.ring2);
    writeValue(writer, value.ring3);
    writeValue(writer, value.ring4);
    writeValue(writer, value.ring5);
    writeValue(writer, value.ring6);
}

bool readValue(BinaryReader &reader, CharacterEquipment &value)
{
    return readValue(reader, value.offHand)
        && readValue(reader, value.mainHand)
        && readValue(reader, value.bow)
        && readValue(reader, value.armor)
        && readValue(reader, value.helm)
        && readValue(reader, value.belt)
        && readValue(reader, value.cloak)
        && readValue(reader, value.gauntlets)
        && readValue(reader, value.boots)
        && readValue(reader, value.amulet)
        && readValue(reader, value.ring1)
        && readValue(reader, value.ring2)
        && readValue(reader, value.ring3)
        && readValue(reader, value.ring4)
        && readValue(reader, value.ring5)
        && readValue(reader, value.ring6);
}

void writeValue(BinaryWriter &writer, const EquippedItemRuntimeState &value)
{
    writeValue(writer, value.identified);
    writeValue(writer, value.broken);
    writeValue(writer, value.stolen);
    writeValue(writer, value.standardEnchantId);
    writeValue(writer, value.standardEnchantPower);
    writeValue(writer, value.specialEnchantId);
    writeValue(writer, value.artifactId);
    writeValue(writer, value.rarity);
    writeValue(writer, value.currentCharges);
    writeValue(writer, value.maxCharges);
    writeValue(writer, value.temporaryBonusRemainingSeconds);
    writeValue(writer, value.hardened);
    writeValue(writer, value.rulesetFields);
    writeValue(writer, value.workshopModId);
}

bool readValue(BinaryReader &reader, EquippedItemRuntimeState &value)
{
    return readValue(reader, value.identified)
        && readValue(reader, value.broken)
        && readValue(reader, value.stolen)
        && readValue(reader, value.standardEnchantId)
        && readValue(reader, value.standardEnchantPower)
        && readValue(reader, value.specialEnchantId)
        && readValue(reader, value.artifactId)
        && readValue(reader, value.rarity)
        && (reader.version() < SaveVersionWandCharges || readValue(reader, value.currentCharges))
        && (reader.version() < SaveVersionWandCharges || readValue(reader, value.maxCharges))
        && readValue(reader, value.temporaryBonusRemainingSeconds)
        && (reader.version() < SaveVersionHardenedItems || readValue(reader, value.hardened))
        && (reader.version() < SaveVersionItemRulesetFields || readValue(reader, value.rulesetFields))
        && (reader.version() < SaveVersionWorkshopMods || readValue(reader, value.workshopModId));
}

void writeValue(BinaryWriter &writer, const CharacterEquipmentRuntimeState &value)
{
    writeValue(writer, value.offHand);
    writeValue(writer, value.mainHand);
    writeValue(writer, value.bow);
    writeValue(writer, value.armor);
    writeValue(writer, value.helm);
    writeValue(writer, value.belt);
    writeValue(writer, value.cloak);
    writeValue(writer, value.gauntlets);
    writeValue(writer, value.boots);
    writeValue(writer, value.amulet);
    writeValue(writer, value.ring1);
    writeValue(writer, value.ring2);
    writeValue(writer, value.ring3);
    writeValue(writer, value.ring4);
    writeValue(writer, value.ring5);
    writeValue(writer, value.ring6);
}

bool readValue(BinaryReader &reader, CharacterEquipmentRuntimeState &value)
{
    return readValue(reader, value.offHand)
        && readValue(reader, value.mainHand)
        && readValue(reader, value.bow)
        && readValue(reader, value.armor)
        && readValue(reader, value.helm)
        && readValue(reader, value.belt)
        && readValue(reader, value.cloak)
        && readValue(reader, value.gauntlets)
        && readValue(reader, value.boots)
        && readValue(reader, value.amulet)
        && readValue(reader, value.ring1)
        && readValue(reader, value.ring2)
        && readValue(reader, value.ring3)
        && readValue(reader, value.ring4)
        && readValue(reader, value.ring5)
        && readValue(reader, value.ring6);
}

void writeValue(BinaryWriter &writer, const TimedPrimaryStatBonus &value)
{
    writeValue(writer, value.power);
    writeValue(writer, value.remainingSeconds);
}

bool readValue(BinaryReader &reader, TimedPrimaryStatBonus &value)
{
    return readValue(reader, value.power)
        && readValue(reader, value.remainingSeconds);
}

void writeValue(BinaryWriter &writer, const BattleOrderDistance &value)
{
    writeValue(writer, value.minimum);
    writeValue(writer, value.maximum);
}

bool readValue(BinaryReader &reader, BattleOrderDistance &value)
{
    return readValue(reader, value.minimum)
        && readValue(reader, value.maximum);
}

void writeValue(BinaryWriter &writer, const BattleOrder &value)
{
    writeValue(writer, value.kind);
    writeValue(writer, value.spellName);
    writeValue(writer, value.enabled);
    writeValue(writer, value.distance);
    writeValue(writer, value.allyHealthBelowPercent);
    writeValue(writer, value.keepSpellPointsPercent);
    writeValue(writer, value.place);
    writeValue(writer, value.renewBelowMinutes);
}

bool readValue(BinaryReader &reader, BattleOrder &value)
{
    return readValue(reader, value.kind)
        && readValue(reader, value.spellName)
        && readValue(reader, value.enabled)
        && readValue(reader, value.distance)
        && readValue(reader, value.allyHealthBelowPercent)
        && readValue(reader, value.keepSpellPointsPercent)
        && (reader.version() < SaveVersionUpkeepOrders || readValue(reader, value.place))
        && (reader.version() < SaveVersionUpkeepOrders || readValue(reader, value.renewBelowMinutes));
}

void writeValue(BinaryWriter &writer, const Character &value)
{
    writeValue(writer, value.name);
    writeValue(writer, value.role);
    writeValue(writer, value.className);
    writeValue(writer, value.portraitTextureName);
    writeValue(writer, value.portraitPictureId);
    writeValue(writer, value.portraitState);
    writeValue(writer, value.portraitElapsedTicks);
    writeValue(writer, value.portraitDurationTicks);
    writeValue(writer, value.portraitSequenceCounter);
    writeValue(writer, value.portraitImageIndex);
    writeValue(writer, value.rosterId);
    writeValue(writer, value.characterDataId);
    writeValue(writer, value.voiceId);
    writeValue(writer, value.birthYear);
    writeValue(writer, value.sexId);
    writeValue(writer, value.raceId);
    writeValue(writer, value.experience);
    writeValue(writer, value.level);
    writeValue(writer, value.skillPoints);
    writeValue(writer, value.might);
    writeValue(writer, value.intellect);
    writeValue(writer, value.personality);
    writeValue(writer, value.endurance);
    writeValue(writer, value.speed);
    writeValue(writer, value.accuracy);
    writeValue(writer, value.luck);
    writeValue(writer, value.maxHealth);
    writeValue(writer, value.health);
    writeValue(writer, value.maxSpellPoints);
    writeValue(writer, value.spellPoints);
    writeValue(writer, value.quickSpellName);
    writeValue(writer, value.knownSpellIds);
    writeValue(writer, value.baseResistances);
    writeValue(writer, value.permanentBonuses);
    writeValue(writer, value.temporaryEventBonuses);
    writeValue(writer, value.magicalBonuses);
    writeValue(writer, value.permanentImmunities);
    writeValue(writer, value.magicalImmunities);
    writeValue(writer, value.permanentConditionImmunities);
    writeValue(writer, value.magicalConditionImmunities);
    writeValue(writer, value.equipment);
    writeValue(writer, value.equipmentRuntime);
    writeValue(writer, value.conditions);
    writeValue(writer, value.conditionStartGameMinutes);
    writeValue(writer, value.skills);
    writeValue(writer, value.awards);
    writeValue(writer, value.eventVariables);
    writeValue(writer, value.recoverySecondsRemaining);
    writeValue(writer, value.armorClassModifier);
    writeValue(writer, value.levelModifier);
    writeValue(writer, value.ageModifier);
    writeValue(writer, value.playerBits);
    writeValue(writer, value.npcs2);
    writeValue(writer, value.healthRegenAccumulator);
    writeValue(writer, value.spellRegenAccumulator);
    writeValue(writer, value.lloydsBeacons);
    writeValue(writer, value.inventory);
    writeValue(writer, value.timedPrimaryStatBonuses);
    writeValue(writer, value.techPoints);
    writeValue(writer, value.rulesetState);
    writeValue(writer, value.extraQuickSpellNames);
    writeValue(writer, value.quickItemSlots);
    writeValue(writer, value.spellbookSchool);
    writeValue(writer, value.implants);
    writeValue(writer, value.conditionExpireGameMinutes);
    writeValue(writer, value.statsMemberId);
    writeValue(writer, value.battleOrders);
    writeValue(writer, value.battleOrderFallback);
    writeValue(writer, value.upkeepOrders);
}

// Saves before SaveVersionWideExperience hold a character's experience in 32 bits.
bool readCharacterExperience(BinaryReader &reader, uint64_t &experience)
{
    if (reader.version() >= SaveVersionWideExperience)
    {
        return readValue(reader, experience);
    }

    uint32_t narrowExperience = 0;

    if (!readValue(reader, narrowExperience))
    {
        return false;
    }

    experience = narrowExperience;
    return true;
}

bool readValue(BinaryReader &reader, Character &value)
{
    // Before battle orders the attack spell sat after the quick spell.
    std::string legacyAttackSpellName;
    const bool read = readValue(reader, value.name)
        && readValue(reader, value.role)
        && readValue(reader, value.className)
        && readValue(reader, value.portraitTextureName)
        && readValue(reader, value.portraitPictureId)
        && readValue(reader, value.portraitState)
        && readValue(reader, value.portraitElapsedTicks)
        && readValue(reader, value.portraitDurationTicks)
        && readValue(reader, value.portraitSequenceCounter)
        && readValue(reader, value.portraitImageIndex)
        && readValue(reader, value.rosterId)
        && readValue(reader, value.characterDataId)
        && readValue(reader, value.voiceId)
        && readValue(reader, value.birthYear)
        && readValue(reader, value.sexId)
        && readValue(reader, value.raceId)
        && readCharacterExperience(reader, value.experience)
        && readValue(reader, value.level)
        && readValue(reader, value.skillPoints)
        && readValue(reader, value.might)
        && readValue(reader, value.intellect)
        && readValue(reader, value.personality)
        && readValue(reader, value.endurance)
        && readValue(reader, value.speed)
        && readValue(reader, value.accuracy)
        && readValue(reader, value.luck)
        && readValue(reader, value.maxHealth)
        && readValue(reader, value.health)
        && readValue(reader, value.maxSpellPoints)
        && readValue(reader, value.spellPoints)
        && readValue(reader, value.quickSpellName)
        && (reader.version() < SaveVersionAttackSpell || reader.version() >= SaveVersionBattleOrders
            || readValue(reader, legacyAttackSpellName))
        && readValue(reader, value.knownSpellIds)
        && readValue(reader, value.baseResistances)
        && readValue(reader, value.permanentBonuses)
        && (reader.version() < SaveVersionTemporaryEventBonuses
            || readValue(reader, value.temporaryEventBonuses))
        && readValue(reader, value.magicalBonuses)
        && readValue(reader, value.permanentImmunities)
        && readValue(reader, value.magicalImmunities)
        && readValue(reader, value.permanentConditionImmunities)
        && readValue(reader, value.magicalConditionImmunities)
        && readValue(reader, value.equipment)
        && readValue(reader, value.equipmentRuntime)
        && readValue(reader, value.conditions)
        && (reader.version() < SaveVersionCharacterConditionStartTimes
            || readValue(reader, value.conditionStartGameMinutes))
        && readValue(reader, value.skills)
        && readValue(reader, value.awards)
        && readValue(reader, value.eventVariables)
        && readValue(reader, value.recoverySecondsRemaining)
        && readValue(reader, value.armorClassModifier)
        && readValue(reader, value.levelModifier)
        && readValue(reader, value.ageModifier)
        && readValue(reader, value.playerBits)
        && readValue(reader, value.npcs2)
        && readValue(reader, value.healthRegenAccumulator)
        && readValue(reader, value.spellRegenAccumulator)
        && readValue(reader, value.lloydsBeacons)
        && readValue(reader, value.inventory)
        && (reader.version() < SaveVersionTimedPrimaryStatBonuses
            || readValue(reader, value.timedPrimaryStatBonuses))
        && (reader.version() < SaveVersionCharacterTechPoints || readValue(reader, value.techPoints))
        && (reader.version() < SaveVersionCharacterRulesetState || readValue(reader, value.rulesetState))
        && (reader.version() < SaveVersionExtraQuickSpells || readValue(reader, value.extraQuickSpellNames))
        && (reader.version() < SaveVersionQuickItemSlots || readValue(reader, value.quickItemSlots))
        && (reader.version() < SaveVersionSpellbookSchool || readValue(reader, value.spellbookSchool))
        && (reader.version() < SaveVersionCharacterImplants || readValue(reader, value.implants))
        && (reader.version() < SaveVersionConditionExpiry || readValue(reader, value.conditionExpireGameMinutes))
        && (reader.version() < SaveVersionPlaythroughStatistics || readValue(reader, value.statsMemberId))
        && (reader.version() < SaveVersionBattleOrders || readValue(reader, value.battleOrders))
        && (reader.version() < SaveVersionBattleOrders || readValue(reader, value.battleOrderFallback))
        && (reader.version() < SaveVersionUpkeepOrders || readValue(reader, value.upkeepOrders));

    if (read && reader.version() < SaveVersionBattleOrders)
    {
        setAttackSpell(legacyAttackSpellName, value.battleOrders, value.battleOrderFallback);
    }

    return read;
}

void writeValue(BinaryWriter &writer, const PartyBuffState &value)
{
    writeValue(writer, value.remainingSeconds);
    writeValue(writer, value.spellId);
    writeValue(writer, value.skillLevel);
    writeValue(writer, value.skillMastery);
    writeValue(writer, value.power);
    writeValue(writer, value.casterMemberIndex);
}

bool readValue(BinaryReader &reader, PartyBuffState &value)
{
    return readValue(reader, value.remainingSeconds)
        && readValue(reader, value.spellId)
        && readValue(reader, value.skillLevel)
        && readValue(reader, value.skillMastery)
        && readValue(reader, value.power)
        && readValue(reader, value.casterMemberIndex);
}

void writeValue(BinaryWriter &writer, const CharacterBuffState &value)
{
    writeValue(writer, value.remainingSeconds);
    writeValue(writer, value.periodicAccumulatorSeconds);
    writeValue(writer, value.spellId);
    writeValue(writer, value.skillLevel);
    writeValue(writer, value.skillMastery);
    writeValue(writer, value.power);
    writeValue(writer, value.casterMemberIndex);
}

bool readValue(BinaryReader &reader, CharacterBuffState &value)
{
    return readValue(reader, value.remainingSeconds)
        && readValue(reader, value.periodicAccumulatorSeconds)
        && readValue(reader, value.spellId)
        && readValue(reader, value.skillLevel)
        && readValue(reader, value.skillMastery)
        && readValue(reader, value.power)
        && readValue(reader, value.casterMemberIndex);
}

void writeValue(BinaryWriter &writer, const Party::HouseStockState &value)
{
    writeValue(writer, value.houseId);
    writeValue(writer, value.nextRefreshGameMinutes);
    writeValue(writer, value.refreshSequence);
    writeValue(writer, value.standardStock);
    writeValue(writer, value.specialStock);
    writeValue(writer, value.spellbookStock);
    writeValue(writer, value.generationVersion);
}

bool readValue(BinaryReader &reader, Party::HouseStockState &value)
{
    const bool read = readValue(reader, value.houseId)
        && readValue(reader, value.nextRefreshGameMinutes)
        && readValue(reader, value.refreshSequence)
        && readValue(reader, value.standardStock)
        && readValue(reader, value.specialStock)
        && readValue(reader, value.spellbookStock)
        && (reader.version() < SaveVersionVendorStockGeneration
            || readValue(reader, value.generationVersion));

    // A guild's single mixed shelf has no school shelves to keep: the guild restocks on the next visit.
    const bool guildStock = std::any_of(value.spellbookStock.begin(), value.spellbookStock.end(),
        [](const InventoryItem &item)
        {
            return item.objectDescriptionId != 0;
        });

    if (read && reader.version() < SaveVersionGuildSchoolShelves && guildStock)
    {
        value.standardStock.clear();
        value.specialStock.clear();
        value.spellbookStock.clear();
    }

    return read;
}

void writeValue(BinaryWriter &writer, const AdventurersInnMember &value)
{
    writeValue(writer, value.character);
    writeValue(writer, value.portraitPictureId);
}

bool readValue(BinaryReader &reader, AdventurersInnMember &value)
{
    return readValue(reader, value.character)
        && readValue(reader, value.portraitPictureId);
}

void writeValue(BinaryWriter &writer, const JournalMapNote &value)
{
    writeValue(writer, value.id);
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.mapFileName);
    writeValue(writer, value.text);
    writeValue(writer, value.listedWithTrainerNotes);
    writeValue(writer, value.personal);
}

bool readValue(BinaryReader &reader, JournalMapNote &value)
{
    return readValue(reader, value.id)
        && readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.mapFileName)
        && readValue(reader, value.text)
        && readValue(reader, value.listedWithTrainerNotes)
        && (reader.version() < SaveVersionPersonalMapNotes || readValue(reader, value.personal));
}

void writeValue(BinaryWriter &writer, const WorldCompletionRecord &value)
{
    writeValue(writer, value.certificateId);
    writeValue(writer, value.gameMinutes);
    writeValue(writer, value.score);
    writeValue(writer, value.completedAtUnixSeconds);
    writeValue(writer, value.timed);
}

bool readValue(BinaryReader &reader, WorldCompletionRecord &value)
{
    return readValue(reader, value.certificateId)
        && readValue(reader, value.gameMinutes)
        && readValue(reader, value.score)
        && readValue(reader, value.completedAtUnixSeconds)
        && readValue(reader, value.timed);
}

bool readWorldCompletions(BinaryReader &reader, Party::Snapshot &value)
{
    if (reader.version() < SaveVersionWorldCompletions)
    {
        value.worldCompletionsUntracked = true;
        return true;
    }

    return readValue(reader, value.worldCompletions) && readValue(reader, value.worldCompletionsUntracked);
}

// Older saves store only the character buffs that existed before the potion buffs.
bool readPartyBuffs(BinaryReader &reader, std::array<PartyBuffState, PartyBuffCount> &partyBuffs)
{
    const size_t storedCount =
        reader.version() < SaveVersionFleetFootBuff ? size_t(PartyBuffId::FleetFoot) : PartyBuffCount;

    for (size_t buffIndex = 0; buffIndex < storedCount; ++buffIndex)
    {
        if (!readValue(reader, partyBuffs[buffIndex]))
        {
            return false;
        }
    }

    return true;
}

bool readCharacterBuffs(
    BinaryReader &reader,
    std::array<std::array<CharacterBuffState, CharacterBuffCount>, 5> &characterBuffs)
{
    const size_t storedCount =
        reader.version() < SaveVersionPotionCharacterBuffs ? LegacyCharacterBuffCount : CharacterBuffCount;

    for (std::array<CharacterBuffState, CharacterBuffCount> &memberBuffs : characterBuffs)
    {
        for (size_t buffIndex = 0; buffIndex < storedCount; ++buffIndex)
        {
            if (!readValue(reader, memberBuffs[buffIndex]))
            {
                return false;
            }
        }
    }

    return true;
}

void writeValue(BinaryWriter &writer, const Mm9PartyHireling &value)
{
    writeValue(writer, value.rudeId);
    writeValue(writer, value.kind);
    writeValue(writer, value.character);
    writeValue(writer, value.buffs);
    writeValue(writer, value.hireDay);
    writeValue(writer, value.nextWageGameMinutes);
    writeValue(writer, value.serviceReadyGameMinutes);
    writeValue(writer, value.formationCell);
}

bool readValue(BinaryReader &reader, Mm9PartyHireling &value)
{
    return readValue(reader, value.rudeId)
        && readValue(reader, value.kind)
        && readValue(reader, value.character)
        && readValue(reader, value.buffs)
        && readValue(reader, value.hireDay)
        && readValue(reader, value.nextWageGameMinutes)
        && readValue(reader, value.serviceReadyGameMinutes)
        && readValue(reader, value.formationCell);
}

// Hirelings saved before SaveVersionMm9Formation had primary stats of 0, which the shared formulas read as penalties.
bool migrateMm9HirelingStats(const BinaryReader &reader, Party::Snapshot &value)
{
    if (reader.version() >= SaveVersionMm9Formation)
    {
        return true;
    }

    for (Mm9PartyHireling &hireling : value.mm9Hirelings)
    {
        Character &character = hireling.character;
        character.might = Party::Mm9HirelingPrimaryStat;
        character.intellect = Party::Mm9HirelingPrimaryStat;
        character.personality = Party::Mm9HirelingPrimaryStat;
        character.endurance = Party::Mm9HirelingPrimaryStat;
        character.speed = Party::Mm9HirelingPrimaryStat;
        character.accuracy = Party::Mm9HirelingPrimaryStat;
        character.luck = Party::Mm9HirelingPrimaryStat;
    }

    return true;
}

void writeValue(BinaryWriter &writer, const Party::Snapshot &value)
{
    writeValue(writer, value.members);
    writeValue(writer, value.adventurersInnMembers);
    writeValue(writer, value.activeMemberIndex);
    writeValue(writer, value.partyBuffs);
    writeValue(writer, value.characterBuffs);
    writeValue(writer, value.gold);
    writeValue(writer, value.bankGold);
    writeValue(writer, value.food);
    writeValue(writer, value.fineGold);
    writeValue(writer, value.waterDamageTicks);
    writeValue(writer, value.burningDamageTicks);
    writeValue(writer, value.splashCount);
    writeValue(writer, value.landingSoundCount);
    writeValue(writer, value.hardLandingSoundCount);
    writeValue(writer, value.monsterTargetSelectionCounter);
    writeValue(writer, value.houseStockSeed);
    writeValue(writer, value.itemEffectElapsedGameSeconds);
    writeValue(writer, value.itemWeeklyEffectSequence);
    writeValue(writer, value.lastFallDamageDistance);
    writeValue(writer, value.foundArtifactItems);
    writeValue(writer, value.arcomageWonHouseIds);
    writeValue(writer, value.arcomageWinCount);
    writeValue(writer, value.arcomageLossCount);
    writeValue(writer, value.houseStockStates);
    writeValue(writer, value.everOwnedItemIds);
    writeValue(writer, value.continentReputations);
    writeValue(writer, value.questBits);
    writeValue(writer, value.autonotes);
    writeValue(writer, value.historyEventTimesByContinent);
    writeValue(writer, value.journalMapNotes);
    writeValue(writer, value.eventVariables);
    writeValue(writer, value.npcTopicOverrides);
    writeValue(writer, value.npcGroupNews);
    writeValue(writer, value.npcGreetingOverrides);
    writeValue(writer, value.npcGreetingDisplayCounts);
    writeValue(writer, value.npcHouseOverrides);
    writeValue(writer, value.npcItemOverrides);
    writeValue(writer, value.unavailableNpcIds);
    writeValue(writer, value.hiredNpcFollowers);
    writeValue(writer, value.explosiveMixes);
    writeValue(writer, value.daysWithoutRest);
    writeValue(writer, value.awakeDayIndex);
    writeValue(writer, value.worldCompletions);
    writeValue(writer, value.worldCompletionsUntracked);
    writeValue(writer, value.chosenMm9RudeRows);
    writeValue(writer, value.teacherLedgers);
    writeValue(writer, value.mm9Hirelings);
    writeValue(writer, value.memberFormationCells);
    writeValue(writer, value.lastOutdoorMapFileName);
}

bool readValue(BinaryReader &reader, Party::Snapshot &value)
{
    return readValue(reader, value.members)
        && readValue(reader, value.adventurersInnMembers)
        && readValue(reader, value.activeMemberIndex)
        && readPartyBuffs(reader, value.partyBuffs)
        && readCharacterBuffs(reader, value.characterBuffs)
        && readValue(reader, value.gold)
        && readValue(reader, value.bankGold)
        && readValue(reader, value.food)
        && (reader.version() < SaveVersionPartyFineGold || readValue(reader, value.fineGold))
        && readValue(reader, value.waterDamageTicks)
        && readValue(reader, value.burningDamageTicks)
        && readValue(reader, value.splashCount)
        && readValue(reader, value.landingSoundCount)
        && readValue(reader, value.hardLandingSoundCount)
        && readValue(reader, value.monsterTargetSelectionCounter)
        && readValue(reader, value.houseStockSeed)
        && (reader.version() < SaveVersionItemWeeklyEffects
            || readValue(reader, value.itemEffectElapsedGameSeconds))
        && (reader.version() < SaveVersionItemWeeklyEffects
            || readValue(reader, value.itemWeeklyEffectSequence))
        && readValue(reader, value.lastFallDamageDistance)
        && readValue(reader, value.foundArtifactItems)
        && readValue(reader, value.arcomageWonHouseIds)
        && readValue(reader, value.arcomageWinCount)
        && readValue(reader, value.arcomageLossCount)
        && readValue(reader, value.houseStockStates)
        && (reader.version() < SaveVersionPartyEverOwnedItems || readValue(reader, value.everOwnedItemIds))
        && (reader.version() < SaveVersionPartyContinentReputations
            || readValue(reader, value.continentReputations))
        && readValue(reader, value.questBits)
        && (reader.version() < SaveVersionPartyAutonotes || readValue(reader, value.autonotes))
        && (reader.version() < SaveVersionPartyHistory || readValue(reader, value.historyEventTimesByContinent))
        && (reader.version() < SaveVersionPartyJournalMapNotes || readValue(reader, value.journalMapNotes))
        && readValue(reader, value.eventVariables)
        && (reader.version() < SaveVersionGlobalNpcState || readValue(reader, value.npcTopicOverrides))
        && (reader.version() < SaveVersionGlobalNpcState || readValue(reader, value.npcGroupNews))
        && (reader.version() < SaveVersionGlobalNpcState || readValue(reader, value.npcGreetingOverrides))
        && (reader.version() < SaveVersionGlobalNpcState || readValue(reader, value.npcGreetingDisplayCounts))
        && (reader.version() < SaveVersionGlobalNpcState || readValue(reader, value.npcHouseOverrides))
        && (reader.version() < SaveVersionGlobalNpcState || readValue(reader, value.npcItemOverrides))
        && (reader.version() < SaveVersionGlobalNpcState || readValue(reader, value.unavailableNpcIds))
        && (reader.version() < SaveVersionPartyHiredNpcFollowers || readValue(reader, value.hiredNpcFollowers))
        && (reader.version() < SaveVersionPartyExplosiveMixes || readValue(reader, value.explosiveMixes))
        && (reader.version() < SaveVersionPartyDaysWithoutRest || readValue(reader, value.daysWithoutRest))
        && (reader.version() < SaveVersionPartyDaysWithoutRest || readValue(reader, value.awakeDayIndex))
        && readWorldCompletions(reader, value)
        && (reader.version() < SaveVersionChosenMm9RudeRows || readValue(reader, value.chosenMm9RudeRows))
        && (reader.version() < SaveVersionTeacherLedgers || readValue(reader, value.teacherLedgers))
        && (reader.version() < SaveVersionMm9Hirelings || readValue(reader, value.mm9Hirelings))
        && (reader.version() < SaveVersionMm9Formation || readValue(reader, value.memberFormationCells))
        && (reader.version() < SaveVersionLastOutdoorMap || readValue(reader, value.lastOutdoorMapFileName))
        && migrateMm9HirelingStats(reader, value);
}

void writeValue(BinaryWriter &writer, const OutdoorMoveState &value)
{
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.footZ);
    writeValue(writer, value.verticalVelocity);
    writeValue(writer, value.supportKind);
    writeValue(writer, value.supportBModelIndex);
    writeValue(writer, value.supportFaceIndex);
    writeValue(writer, value.supportIsFluid);
    writeValue(writer, value.supportOnWater);
    writeValue(writer, value.supportOnBurning);
    writeValue(writer, value.airborne);
    writeValue(writer, value.landedThisFrame);
    writeValue(writer, value.fallStartZ);
    writeValue(writer, value.fallDistance);
}

bool readValue(BinaryReader &reader, OutdoorMoveState &value)
{
    return readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.footZ)
        && readValue(reader, value.verticalVelocity)
        && readValue(reader, value.supportKind)
        && readValue(reader, value.supportBModelIndex)
        && readValue(reader, value.supportFaceIndex)
        && readValue(reader, value.supportIsFluid)
        && readValue(reader, value.supportOnWater)
        && readValue(reader, value.supportOnBurning)
        && readValue(reader, value.airborne)
        && readValue(reader, value.landedThisFrame)
        && readValue(reader, value.fallStartZ)
        && readValue(reader, value.fallDistance);
}

void writeValue(BinaryWriter &writer, const IndoorMoveState &value)
{
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.footZ);
    writeValue(writer, value.eyeHeight);
    writeValue(writer, value.verticalVelocity);
    writeValue(writer, value.sectorId);
    writeValue(writer, value.eyeSectorId);
    writeValue(writer, value.supportFaceIndex);
    writeValue(writer, value.grounded);
}

bool readValue(BinaryReader &reader, IndoorMoveState &value)
{
    return readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.footZ)
        && readValue(reader, value.eyeHeight)
        && readValue(reader, value.verticalVelocity)
        && readValue(reader, value.sectorId)
        && readValue(reader, value.eyeSectorId)
        && readValue(reader, value.supportFaceIndex)
        && readValue(reader, value.grounded);
}

void writeValue(BinaryWriter &writer, const OutdoorPartyMovementState &value)
{
    writeValue(writer, value.running);
    writeValue(writer, value.flying);
    writeValue(writer, value.featherFall);
    writeValue(writer, value.waterWalk);
}

bool readValue(BinaryReader &reader, OutdoorPartyMovementState &value)
{
    value.activelyFlying = false;

    return readValue(reader, value.running)
        && readValue(reader, value.flying)
        && readValue(reader, value.featherFall)
        && readValue(reader, value.waterWalk);
}

void writeValue(BinaryWriter &writer, const IndoorPartyRuntime::Snapshot &value)
{
    writeValue(writer, value.movementState);
    writeValue(writer, value.movementAccumulatorSeconds);
    writeValue(writer, value.pendingJumpRequested);
    const IndoorSwimMemory swimMemory = value.swimMemory.value_or(IndoorSwimMemory{});
    writeValue(writer, swimMemory.wasSubmerged);
    writeValue(writer, swimMemory.surfaceJump);
}

bool readValue(BinaryReader &reader, IndoorPartyRuntime::Snapshot &value)
{
    if (!readValue(reader, value.movementState)
        || !readValue(reader, value.movementAccumulatorSeconds)
        || !readValue(reader, value.pendingJumpRequested))
    {
        return false;
    }

    if (reader.version() < SaveVersionPartySwimMemory)
    {
        return true;
    }

    IndoorSwimMemory swimMemory = {};

    if (!readValue(reader, swimMemory.wasSubmerged) || !readValue(reader, swimMemory.surfaceJump))
    {
        return false;
    }

    value.swimMemory = swimMemory;
    return true;
}

void writeValue(BinaryWriter &writer, const GameplayActorSpellEffectState &value)
{
    writeValue(writer, value.slowRemainingSeconds);
    writeValue(writer, value.slowMoveMultiplier);
    writeValue(writer, value.slowRecoveryMultiplier);
    writeValue(writer, value.stunRemainingSeconds);
    writeValue(writer, value.paralyzeRemainingSeconds);
    writeValue(writer, value.fearRemainingSeconds);
    writeValue(writer, value.blindRemainingSeconds);
    writeValue(writer, value.controlRemainingSeconds);
    writeValue(writer, value.controlMode);
    writeValue(writer, value.shrinkRemainingSeconds);
    writeValue(writer, value.shrinkDamageMultiplier);
    writeValue(writer, value.shrinkArmorClassMultiplier);
    writeValue(writer, value.armorClassHalvedRemainingSeconds);
    writeValue(writer, value.darkGraspRemainingSeconds);
    writeValue(writer, value.hostileToParty);
    writeValue(writer, value.hasDetectedParty);
    writeValue(writer, value.dayOfProtectionRemainingSeconds);
    writeValue(writer, value.dayOfProtectionPower);
    writeValue(writer, value.hourOfPowerRemainingSeconds);
    writeValue(writer, value.hourOfPowerPower);
    writeValue(writer, value.painReflectionRemainingSeconds);
    writeValue(writer, value.hammerhandsRemainingSeconds);
    writeValue(writer, value.hammerhandsPower);
    writeValue(writer, value.hasteRemainingSeconds);
    writeValue(writer, value.shieldRemainingSeconds);
    writeValue(writer, value.stoneskinRemainingSeconds);
    writeValue(writer, value.stoneskinPower);
    writeValue(writer, value.blessRemainingSeconds);
    writeValue(writer, value.blessPower);
    writeValue(writer, value.fateRemainingSeconds);
    writeValue(writer, value.fatePower);
    writeValue(writer, value.heroismRemainingSeconds);
    writeValue(writer, value.heroismPower);
}

bool readValue(BinaryReader &reader, GameplayActorSpellEffectState &value)
{
    return readValue(reader, value.slowRemainingSeconds)
        && readValue(reader, value.slowMoveMultiplier)
        && readValue(reader, value.slowRecoveryMultiplier)
        && readValue(reader, value.stunRemainingSeconds)
        && readValue(reader, value.paralyzeRemainingSeconds)
        && readValue(reader, value.fearRemainingSeconds)
        && readValue(reader, value.blindRemainingSeconds)
        && readValue(reader, value.controlRemainingSeconds)
        && readValue(reader, value.controlMode)
        && readValue(reader, value.shrinkRemainingSeconds)
        && readValue(reader, value.shrinkDamageMultiplier)
        && readValue(reader, value.shrinkArmorClassMultiplier)
        && (reader.version() < SaveVersionCombatEffectState
            || readValue(reader, value.armorClassHalvedRemainingSeconds))
        && readValue(reader, value.darkGraspRemainingSeconds)
        && readValue(reader, value.hostileToParty)
        && readValue(reader, value.hasDetectedParty)
        && (reader.version() < SaveVersionOutdoorRuntimeSaveParity
            || (readValue(reader, value.dayOfProtectionRemainingSeconds)
                && readValue(reader, value.dayOfProtectionPower)
                && readValue(reader, value.hourOfPowerRemainingSeconds)
                && readValue(reader, value.hourOfPowerPower)
                && readValue(reader, value.painReflectionRemainingSeconds)
                && readValue(reader, value.hammerhandsRemainingSeconds)
                && readValue(reader, value.hammerhandsPower)
                && readValue(reader, value.hasteRemainingSeconds)
                && readValue(reader, value.shieldRemainingSeconds)
                && readValue(reader, value.stoneskinRemainingSeconds)
                && readValue(reader, value.stoneskinPower)
                && readValue(reader, value.blessRemainingSeconds)
                && readValue(reader, value.blessPower)
                && readValue(reader, value.fateRemainingSeconds)
                && readValue(reader, value.fatePower)
                && readValue(reader, value.heroismRemainingSeconds)
                && readValue(reader, value.heroismPower)));
}

// Older saves carry each splat's triangles: a count, then x, y, z, u and v floats per vertex.
bool skipBloodSplatGeometry(BinaryReader &reader)
{
    uint64_t count = 0;
    return readValue(reader, count)
        && count <= reader.remainingBytes() / (5 * sizeof(float))
        && reader.skipBytes(size_t(count) * 5 * sizeof(float));
}

void writeValue(BinaryWriter &writer, const IndoorWorldRuntime::BloodSplatState &value)
{
    writeValue(writer, value.sourceActorId);
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.z);
    writeValue(writer, value.radius);
}

bool readValue(BinaryReader &reader, IndoorWorldRuntime::BloodSplatState &value)
{
    return readValue(reader, value.sourceActorId)
        && readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.z)
        && readValue(reader, value.radius)
        && (reader.version() >= SaveVersionBloodSplatsWithoutGeometry || skipBloodSplatGeometry(reader));
}

void writeValue(BinaryWriter &writer, const OutdoorWorldRuntime::BloodSplatState &value)
{
    writeValue(writer, value.sourceActorId);
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.z);
    writeValue(writer, value.radius);
}

bool readValue(BinaryReader &reader, OutdoorWorldRuntime::BloodSplatState &value)
{
    return readValue(reader, value.sourceActorId)
        && readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.z)
        && readValue(reader, value.radius)
        && (reader.version() >= SaveVersionBloodSplatsWithoutGeometry || skipBloodSplatGeometry(reader));
}

void writeValue(BinaryWriter &writer, const IndoorWorldRuntime::MapActorAiState &value)
{
    writeValue(writer, value.actorId);
    writeValue(writer, value.monsterId);
    writeValue(writer, value.displayName);
    writeValue(writer, value.hostileToParty);
    writeValue(writer, value.hasDetectedParty);
    writeValue(writer, value.bloodSplatSpawned);
    writeValue(writer, value.motionState);
    writeValue(writer, value.animationState);
    writeValue(writer, value.queuedAttackAbility);
    writeValue(writer, value.spellEffects);
    writeValue(writer, value.preciseX);
    writeValue(writer, value.preciseY);
    writeValue(writer, value.preciseZ);
    writeValue(writer, value.homePreciseX);
    writeValue(writer, value.homePreciseY);
    writeValue(writer, value.homePreciseZ);
    writeValue(writer, value.moveDirectionX);
    writeValue(writer, value.moveDirectionY);
    writeValue(writer, value.velocityX);
    writeValue(writer, value.velocityY);
    writeValue(writer, value.velocityZ);
    writeValue(writer, value.yawRadians);
    writeValue(writer, value.animationTimeTicks);
    writeValue(writer, value.recoverySeconds);
    writeValue(writer, value.attackAnimationSeconds);
    writeValue(writer, value.attackCooldownSeconds);
    writeValue(writer, value.idleDecisionSeconds);
    writeValue(writer, value.actionSeconds);
    writeValue(writer, value.idleDecisionCount);
    writeValue(writer, value.pursueDecisionCount);
    writeValue(writer, value.attackDecisionCount);
    writeValue(writer, value.attackImpactTriggered);
    writeValue(writer, value.spriteFrameIndex);
    writeValue(writer, value.actionSpriteFrameIndices);
    writeValue(writer, value.collisionRadius);
    writeValue(writer, value.collisionHeight);
    writeValue(writer, value.movementSpeed);
    writeValue(writer, value.bolsterRewardMultiplier);
    writeValue(writer, value.sectorId);
    writeValue(writer, value.eyeSectorId);
    writeValue(writer, value.supportFaceIndex);
    writeValue(writer, value.grounded);
    writeValue(writer, value.meleeAttackAnimationSeconds);
    writeValue(writer, value.rangedAttackAnimationSeconds);
    writeValue(writer, value.dyingAnimationSeconds);
    writeValue(writer, value.crowdSideLockRemainingSeconds);
    writeValue(writer, value.crowdNoProgressSeconds);
    writeValue(writer, value.crowdLastEdgeDistance);
    writeValue(writer, value.crowdRetreatRemainingSeconds);
    writeValue(writer, value.crowdStandRemainingSeconds);
    writeValue(writer, value.crowdProbeEdgeDistance);
    writeValue(writer, value.crowdProbeElapsedSeconds);
    writeValue(writer, value.crowdEscapeAttempts);
    writeValue(writer, value.crowdSideSign);
    writeValue(writer, value.suppressLowHealthFlee);
    writeValue(writer, value.angeredByParty);
}

bool readValue(BinaryReader &reader, IndoorWorldRuntime::MapActorAiState &value)
{
    return readValue(reader, value.actorId)
        && readValue(reader, value.monsterId)
        && readValue(reader, value.displayName)
        && readValue(reader, value.hostileToParty)
        && readValue(reader, value.hasDetectedParty)
        && readValue(reader, value.bloodSplatSpawned)
        && readValue(reader, value.motionState)
        && readValue(reader, value.animationState)
        && readValue(reader, value.queuedAttackAbility)
        && readValue(reader, value.spellEffects)
        && readValue(reader, value.preciseX)
        && readValue(reader, value.preciseY)
        && readValue(reader, value.preciseZ)
        && readValue(reader, value.homePreciseX)
        && readValue(reader, value.homePreciseY)
        && readValue(reader, value.homePreciseZ)
        && readValue(reader, value.moveDirectionX)
        && readValue(reader, value.moveDirectionY)
        && readValue(reader, value.velocityX)
        && readValue(reader, value.velocityY)
        && readValue(reader, value.velocityZ)
        && readValue(reader, value.yawRadians)
        && readValue(reader, value.animationTimeTicks)
        && readValue(reader, value.recoverySeconds)
        && readValue(reader, value.attackAnimationSeconds)
        && readValue(reader, value.attackCooldownSeconds)
        && readValue(reader, value.idleDecisionSeconds)
        && readValue(reader, value.actionSeconds)
        && readValue(reader, value.idleDecisionCount)
        && readValue(reader, value.pursueDecisionCount)
        && readValue(reader, value.attackDecisionCount)
        && readValue(reader, value.attackImpactTriggered)
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.spriteFrameIndex))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.actionSpriteFrameIndices))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.collisionRadius))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.collisionHeight))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.movementSpeed))
        && (reader.version() < SaveVersionMonsterBolsterRewards || readValue(reader, value.bolsterRewardMultiplier))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.sectorId))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.eyeSectorId))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.supportFaceIndex))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.grounded))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.meleeAttackAnimationSeconds))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.rangedAttackAnimationSeconds))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.dyingAnimationSeconds))
        && (reader.version() < SaveVersionIndoorSaveLoadParity
            || readValue(reader, value.crowdSideLockRemainingSeconds))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.crowdNoProgressSeconds))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.crowdLastEdgeDistance))
        && (reader.version() < SaveVersionIndoorSaveLoadParity
            || readValue(reader, value.crowdRetreatRemainingSeconds))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.crowdStandRemainingSeconds))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.crowdProbeEdgeDistance))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.crowdProbeElapsedSeconds))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.crowdEscapeAttempts))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.crowdSideSign))
        && (reader.version() < SaveVersionOutdoorRuntimeSaveParity || readValue(reader, value.suppressLowHealthFlee))
        && (reader.version() < SaveVersionActorAngeredByParty || readValue(reader, value.angeredByParty));
}

void writeValue(BinaryWriter &writer, const ActorBehaviorSpell &value)
{
    writeValue(writer, value.spellId);
    writeValue(writer, value.skillLevel);
    writeValue(writer, value.skillMastery);
    writeValue(writer, value.useChance);
}

bool readValue(BinaryReader &reader, ActorBehaviorSpell &value)
{
    return readValue(reader, value.spellId)
        && readValue(reader, value.skillLevel)
        && readValue(reader, value.skillMastery)
        && readValue(reader, value.useChance);
}

void writeValue(BinaryWriter &writer, const ActorBehaviorTimer &value)
{
    writeValue(writer, value.name);
    writeValue(writer, value.remainingSeconds);
}

bool readValue(BinaryReader &reader, ActorBehaviorTimer &value)
{
    return readValue(reader, value.name) && readValue(reader, value.remainingSeconds);
}

void writeValue(BinaryWriter &writer, const ActorBehaviorWardVisual &value)
{
    writeValue(writer, value.dome);
    writeValue(writer, value.color);
    writeValue(writer, value.intensity);
    writeValue(writer, value.rimPower);
    writeValue(writer, value.noise);
}

bool readValue(BinaryReader &reader, ActorBehaviorWardVisual &value)
{
    return readValue(reader, value.dome)
        && readValue(reader, value.color)
        && readValue(reader, value.intensity)
        && readValue(reader, value.rimPower)
        && readValue(reader, value.noise);
}

void writeValue(BinaryWriter &writer, const ActorBehaviorWard &value)
{
    writeValue(writer, value.id);
    writeValue(writer, value.radius);
    writeValue(writer, value.remainingSeconds);
    writeValue(writer, value.effectId);
    writeValue(writer, value.effectScale);
    writeValue(writer, value.effectIntervalSeconds);
    writeValue(writer, value.effectCooldownSeconds);
    writeValue(writer, value.ageSeconds);
    writeValue(writer, value.visual);
}

bool readValue(BinaryReader &reader, ActorBehaviorWard &value)
{
    return readValue(reader, value.id)
        && readValue(reader, value.radius)
        && readValue(reader, value.remainingSeconds)
        && readValue(reader, value.effectId)
        && readValue(reader, value.effectScale)
        && readValue(reader, value.effectIntervalSeconds)
        && readValue(reader, value.effectCooldownSeconds)
        && (reader.version() < SaveVersionActorBehaviorWardVisuals
            || (readValue(reader, value.ageSeconds) && readValue(reader, value.visual)));
}

void writeValue(BinaryWriter &writer, const ActorBehaviorPerform &value)
{
    writeValue(writer, value.clip);
    writeValue(writer, value.fallbackAnimation);
    writeValue(writer, value.durationSeconds);
    writeValue(writer, value.elapsedSeconds);
    writeValue(writer, value.started);
}

bool readValue(BinaryReader &reader, ActorBehaviorPerform &value)
{
    return readValue(reader, value.clip)
        && readValue(reader, value.fallbackAnimation)
        && readValue(reader, value.durationSeconds)
        && readValue(reader, value.elapsedSeconds)
        && readValue(reader, value.started);
}

void writeValue(BinaryWriter &writer, const ActorBehaviorInstanceState &value)
{
    writeValue(writer, static_cast<uint64_t>(value.actorIndex));
    writeValue(writer, value.actorId);
    writeValue(writer, value.behaviorId);
    writeValue(writer, value.started);
    writeValue(writer, value.deathHandled);
    writeValue(writer, value.lastHp);
    writeValue(writer, value.ageSeconds);
    writeValue(writer, value.thinkCooldownSeconds);
    writeValue(writer, value.randomState);
    writeValue(writer, value.scriptState);
    writeValue(writer, value.firedHealthThresholds);
    writeValue(writer, value.timers);
    writeValue(writer, value.wards);
    writeValue(writer, value.perform);
    writeValue(writer, value.spellOverride);
    writeValue(writer, value.nextCast);
    writeValue(writer, value.aiTypeOverride);
    writeValue(writer, value.suppressFlee);
    writeValue(writer, value.speedMultiplier);
    writeValue(writer, value.invulnerable);
    writeValue(writer, value.leashRadius);
    writeValue(writer, value.rangedBand.has_value());
    writeValue(writer, value.rangedBand.value_or(std::array<float, 2>{})[0]);
    writeValue(writer, value.rangedBand.value_or(std::array<float, 2>{})[1]);
    writeValue(writer, value.moveTarget.has_value());
    writeValue(writer, value.moveTarget.value_or(GameplayWorldPoint{}).x);
    writeValue(writer, value.moveTarget.value_or(GameplayWorldPoint{}).y);
    writeValue(writer, value.moveTarget.value_or(GameplayWorldPoint{}).z);
    writeValue(writer, value.armoredFront.has_value());
    writeValue(writer, value.armoredFront.value_or(std::array<float, 2>{})[0]);
    writeValue(writer, value.armoredFront.value_or(std::array<float, 2>{})[1]);
}

// Per-actor tactics and the armoured front a script set (save version 135).
bool readBehaviorTactics(BinaryReader &reader, ActorBehaviorInstanceState &value)
{
    bool hasBand = false;
    bool hasTarget = false;
    bool hasFront = false;
    std::array<float, 2> band = {};
    GameplayWorldPoint target = {};
    std::array<float, 2> front = {};
    if (!readValue(reader, value.leashRadius)
        || !readValue(reader, hasBand) || !readValue(reader, band[0]) || !readValue(reader, band[1])
        || !readValue(reader, hasTarget) || !readValue(reader, target.x) || !readValue(reader, target.y)
        || !readValue(reader, target.z)
        || !readValue(reader, hasFront) || !readValue(reader, front[0]) || !readValue(reader, front[1]))
    {
        return false;
    }
    value.rangedBand = hasBand ? std::optional<std::array<float, 2>>(band) : std::nullopt;
    value.moveTarget = hasTarget ? std::optional<GameplayWorldPoint>(target) : std::nullopt;
    value.armoredFront = hasFront ? std::optional<std::array<float, 2>>(front) : std::nullopt;
    return true;
}

bool readValue(BinaryReader &reader, ActorBehaviorInstanceState &value)
{
    uint64_t actorIndex = 0;
    const bool loaded = readValue(reader, actorIndex)
        && readValue(reader, value.actorId)
        && readValue(reader, value.behaviorId)
        && readValue(reader, value.started)
        && readValue(reader, value.deathHandled)
        && readValue(reader, value.lastHp)
        && readValue(reader, value.ageSeconds)
        && readValue(reader, value.thinkCooldownSeconds)
        && readValue(reader, value.randomState)
        && readValue(reader, value.scriptState)
        && readValue(reader, value.firedHealthThresholds)
        && readValue(reader, value.timers)
        && readValue(reader, value.wards)
        && readValue(reader, value.perform)
        && readValue(reader, value.spellOverride)
        && readValue(reader, value.nextCast)
        && readValue(reader, value.aiTypeOverride)
        && readValue(reader, value.suppressFlee)
        && (reader.version() < SaveVersionBehaviorSpeed
            || (readValue(reader, value.speedMultiplier) && readValue(reader, value.invulnerable)
                && readBehaviorTactics(reader, value)));
    value.actorIndex = static_cast<size_t>(actorIndex);
    return loaded;
}

void writeValue(BinaryWriter &writer, const ActorBehaviorRuntime::Snapshot &value)
{
    writeValue(writer, value.instances);
    writeValue(writer, value.scannedActorCount);
}

bool readValue(BinaryReader &reader, ActorBehaviorRuntime::Snapshot &value)
{
    return readValue(reader, value.instances) && readValue(reader, value.scannedActorCount);
}

void writeValue(BinaryWriter &writer, const IndoorWorldRuntime::Snapshot &value)
{
    writeValue(writer, value.gameMinutes);
    writeValue(writer, value.currentLocationReputation);
    writeValue(writer, value.sessionChestSeed);
    writeValue(writer, value.materializedChestViews);
    writeValue(writer, value.activeChestView);
    writeValue(writer, value.mapActorCorpseViews);
    writeValue(writer, value.activeCorpseView);
    writeValue(writer, value.mapActorAiStates);
    writeValue(writer, value.bloodSplats);
    writeValue(writer, value.fireSpikeTraps);
    writeValue(writer, value.actorUpdateAccumulatorSeconds);
    writeValue(writer, value.projectileState);
    writeValue(writer, value.searchedLootPropSourceIds);
    writeValue(writer, value.actorBehaviors);
    writeValue(writer, value.mapActorRevealedLoot);
    writeValue(writer, value.armageddon);
}

bool readValue(BinaryReader &reader, IndoorWorldRuntime::Snapshot &value)
{
    return readValue(reader, value.gameMinutes)
        && readValue(reader, value.currentLocationReputation)
        && (reader.version() < SaveVersionIndoorChestViews || readValue(reader, value.sessionChestSeed))
        && (reader.version() < SaveVersionIndoorChestViews || readValue(reader, value.materializedChestViews))
        && (reader.version() < SaveVersionIndoorChestViews || readValue(reader, value.activeChestView))
        && (reader.version() < SaveVersionIndoorCorpseViews || readValue(reader, value.mapActorCorpseViews))
        && (reader.version() < SaveVersionIndoorCorpseViews || readValue(reader, value.activeCorpseView))
        && (reader.version() < SaveVersionIndoorActorSpellEffects
            || reader.version() >= SaveVersionIndoorActorAiStates
            || readValue(reader, value.mapActorSpellEffectStates))
        && (reader.version() < SaveVersionIndoorActorAiStates || readValue(reader, value.mapActorAiStates))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.bloodSplats))
        && (reader.version() < SaveVersionIndoorFireSpikeTraps || readValue(reader, value.fireSpikeTraps))
        && (reader.version() < SaveVersionIndoorSaveLoadParity
            || readValue(reader, value.actorUpdateAccumulatorSeconds))
        && (reader.version() < SaveVersionFullProjectileState || readValue(reader, value.projectileState))
        && (reader.version() < SaveVersionMm9ItemSourceState
            || readValue(reader, value.searchedLootPropSourceIds))
        && (reader.version() < SaveVersionActorBehaviors || readValue(reader, value.actorBehaviors))
        && (reader.version() < SaveVersionActorRevealedLoot || readValue(reader, value.mapActorRevealedLoot))
        && (reader.version() < SaveVersionIndoorArmageddon || readValue(reader, value.armageddon));
}

void writeValue(BinaryWriter &writer, const OutdoorPartyRuntime::Snapshot &value)
{
    writeValue(writer, value.movementState);
    writeValue(writer, value.partyMovementState);
}

bool readValue(BinaryReader &reader, OutdoorPartyRuntime::Snapshot &value)
{
    return readValue(reader, value.movementState)
        && readValue(reader, value.partyMovementState);
}

void writeValue(BinaryWriter &writer, const RuntimeMechanismState &value)
{
    writeValue(writer, value.state);
    writeValue(writer, value.timeSinceTriggeredMs);
    writeValue(writer, value.currentDistance);
    writeValue(writer, value.isMoving);
    writeValue(writer, value.rotationDirection);
    writeValue(writer, value.spinDegrees);
    writeValue(writer, value.spinRate);
    writeValue(writer, value.spinOn);
    writeValue(writer, value.spinDirection);
    writeValue(writer, value.spinSet);
}

bool readValue(BinaryReader &reader, RuntimeMechanismState &value)
{
    return readValue(reader, value.state)
        && readValue(reader, value.timeSinceTriggeredMs)
        && readValue(reader, value.currentDistance)
        && readValue(reader, value.isMoving)
        && (reader.version() < SaveVersionOutdoorMechanismRotationDirection
            || readValue(reader, value.rotationDirection))
        && (reader.version() < SaveVersionMoverSpin
            || (readValue(reader, value.spinDegrees)
                && readValue(reader, value.spinRate)
                && readValue(reader, value.spinOn)
                && readValue(reader, value.spinDirection)
                && readValue(reader, value.spinSet)));
}

void writeValue(BinaryWriter &writer, const RuntimeDestructibleState &value)
{
    writeValue(writer, value.hp);
    writeValue(writer, value.damageEnabled);
    writeValue(writer, value.destroyed);
}

bool readValue(BinaryReader &reader, RuntimeDestructibleState &value)
{
    return readValue(reader, value.hp)
        && readValue(reader, value.damageEnabled)
        && readValue(reader, value.destroyed);
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::OutdoorModelMechanismDefinition &value)
{
    writeValue(writer, value.mechanismId);
    writeValue(writer, value.modelName);
    writeValue(writer, value.bmodelIndex);
    writeValue(writer, value.dx);
    writeValue(writer, value.dy);
    writeValue(writer, value.dz);
    writeValue(writer, value.moveTimeMs);
    writeValue(writer, value.closed);
    writeValue(writer, value.moveParty);
}

bool readValue(BinaryReader &reader, EventRuntimeState::OutdoorModelMechanismDefinition &value)
{
    return readValue(reader, value.mechanismId)
        && readValue(reader, value.modelName)
        && readValue(reader, value.bmodelIndex)
        && readValue(reader, value.dx)
        && readValue(reader, value.dy)
        && readValue(reader, value.dz)
        && readValue(reader, value.moveTimeMs)
        && readValue(reader, value.closed)
        && readValue(reader, value.moveParty);
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::PendingMapMove &value)
{
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.z);
    writeValue(writer, value.mapName);
    writeValue(writer, value.directionDegrees);
    writeValue(writer, value.useMapStartPosition);
    writeValue(writer, value.startPointName);
}

bool readValue(BinaryReader &reader, EventRuntimeState::PendingMapMove &value)
{
    return readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.z)
        && readValue(reader, value.mapName)
        && readValue(reader, value.directionDegrees)
        && readValue(reader, value.useMapStartPosition)
        && (reader.version() < SaveVersionMapMoveStartPoint || readValue(reader, value.startPointName));
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::PendingDialogueContext &value)
{
    writeValue(writer, value.kind);
    writeValue(writer, value.sourceId);
    writeValue(writer, value.sourceActorIndex);
    writeValue(writer, value.hostHouseId);
    writeValue(writer, value.newsId);
    writeValue(writer, value.participantPictureId);
    writeValue(writer, value.titleOverride);
    writeValue(writer, value.transitionMapMove);
    writeValue(writer, value.transitionTextId);
    writeValue(writer, value.transitionImageId);
    writeValue(writer, value.boundaryTravel);
}

bool readValue(BinaryReader &reader, EventRuntimeState::PendingDialogueContext &value)
{
    return readValue(reader, value.kind)
        && readValue(reader, value.sourceId)
        && (reader.version() < SaveVersionDialogueActorSource || readValue(reader, value.sourceActorIndex))
        && readValue(reader, value.hostHouseId)
        && readValue(reader, value.newsId)
        && (reader.version() < SaveVersionDialogueParticipantPicture
            || readValue(reader, value.participantPictureId))
        && readValue(reader, value.titleOverride)
        && (reader.version() < SaveVersionDungeonTransitionDialogue || readValue(reader, value.transitionMapMove))
        && (reader.version() < SaveVersionDungeonTransitionDialogue || readValue(reader, value.transitionTextId))
        && (reader.version() < SaveVersionDungeonTransitionDialogue || readValue(reader, value.transitionImageId))
        && (reader.version() < SaveVersionBoundaryTravelDialogue || readValue(reader, value.boundaryTravel));
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::PendingMovie &value)
{
    writeValue(writer, value.movieName);
    writeValue(writer, value.restoreAfterPlayback);
}

bool readValue(BinaryReader &reader, EventRuntimeState::PendingMovie &value)
{
    return readValue(reader, value.movieName)
        && readValue(reader, value.restoreAfterPlayback);
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::PendingInputPrompt &value)
{
    writeValue(writer, value.kind);
    writeValue(writer, value.eventId);
    writeValue(writer, value.continueStep);
    writeValue(writer, value.correctStep);
    writeValue(writer, value.textId);
    writeValue(writer, value.answerTextIds);
    writeValue(writer, value.answers);
    writeValue(writer, value.answerContinueSteps);
    writeValue(writer, value.text);
}

bool readValue(BinaryReader &reader, EventRuntimeState::PendingInputPrompt &value)
{
    return readValue(reader, value.kind)
        && readValue(reader, value.eventId)
        && readValue(reader, value.continueStep)
        && (reader.version() < SaveVersionInputPromptAnswers || readValue(reader, value.correctStep))
        && readValue(reader, value.textId)
        && (reader.version() < SaveVersionInputPromptAnswers || readValue(reader, value.answerTextIds))
        && (reader.version() < SaveVersionInputPromptAnswers || readValue(reader, value.answers))
        && (reader.version() < SaveVersionInputPromptAnswerSteps || readValue(reader, value.answerContinueSteps))
        && readValue(reader, value.text);
}

void writePendingInputPromptForSave(BinaryWriter &writer, const EventRuntimeState &value)
{
    (void)value;
    const std::optional<EventRuntimeState::PendingInputPrompt> emptyPrompt = std::nullopt;
    writeValue(writer, emptyPrompt);
}

bool readPendingInputPromptForSave(BinaryReader &reader, EventRuntimeState &value)
{
    std::optional<EventRuntimeState::PendingInputPrompt> discardedPrompt;

    if (!readValue(reader, discardedPrompt))
    {
        return false;
    }

    value.pendingInputPrompt.reset();
    return true;
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::PendingSound &value)
{
    writeValue(writer, value.soundId);
    writeValue(writer, value.soundName);
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.z);
    writeValue(writer, value.positional);
    writeValue(writer, value.hasExplicitZ);
}

bool readValue(BinaryReader &reader, EventRuntimeState::PendingSound &value)
{
    return readValue(reader, value.soundId)
        && (reader.version() < SaveVersionPendingSoundNames || readValue(reader, value.soundName))
        && readValue(reader, value.x)
        && readValue(reader, value.y)
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.z))
        && readValue(reader, value.positional)
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.hasExplicitZ));
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::SpriteOverride &value)
{
    writeValue(writer, value.hidden);
    writeValue(writer, value.textureName);
}

bool readValue(BinaryReader &reader, EventRuntimeState::SpriteOverride &value)
{
    return readValue(reader, value.hidden)
        && readValue(reader, value.textureName);
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::PendingArcomageGame &value)
{
    writeValue(writer, value.houseId);
}

bool readValue(BinaryReader &reader, EventRuntimeState::PendingArcomageGame &value)
{
    return readValue(reader, value.houseId);
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::DialogueOfferState &value)
{
    writeValue(writer, value.kind);
    writeValue(writer, value.npcId);
    writeValue(writer, value.topicId);
    writeValue(writer, value.messageTextId);
    writeValue(writer, value.rosterId);
    writeValue(writer, value.partyFullTextId);
    writeValue(writer, value.sourceActorIndex);
}

bool readValue(BinaryReader &reader, EventRuntimeState::DialogueOfferState &value)
{
    return readValue(reader, value.kind)
        && readValue(reader, value.npcId)
        && readValue(reader, value.topicId)
        && readValue(reader, value.messageTextId)
        && readValue(reader, value.rosterId)
        && readValue(reader, value.partyFullTextId)
        && (reader.version() < SaveVersionDialogueActorSource || readValue(reader, value.sourceActorIndex));
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::SuspendedMm9RudeDialogue &value)
{
    writeValue(writer, value.rudeId);
    writeValue(writer, value.nodeId);
    writeValue(writer, value.sourceActorIndex);
    writeValue(writer, value.response);
    writeValue(writer, value.selectionIndex);
    writeValue(writer, value.exitCallbackExecuted);
}

bool readValue(BinaryReader &reader, EventRuntimeState::SuspendedMm9RudeDialogue &value)
{
    return readValue(reader, value.rudeId)
        && readValue(reader, value.nodeId)
        && readValue(reader, value.sourceActorIndex)
        && readValue(reader, value.response)
        && readValue(reader, value.selectionIndex)
        && readValue(reader, value.exitCallbackExecuted);
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::DialogueRuntimeState &value)
{
    writeValue(writer, value.hostHouseId);
    writeValue(writer, value.menuStack);
    writeValue(writer, value.currentOffer);
    writeValue(writer, value.suspendedMm9RudeDialogue);
}

bool readValue(BinaryReader &reader, EventRuntimeState::DialogueRuntimeState &value)
{
    return readValue(reader, value.hostHouseId)
        && readValue(reader, value.menuStack)
        && readValue(reader, value.currentOffer)
        && (reader.version() < SaveVersionSuspendedMm9RudeVendor
            || readValue(reader, value.suspendedMm9RudeDialogue));
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::GeneratedMercenaryRecruit &value)
{
    writeValue(writer, value.npcId);
    writeValue(writer, value.rosterId);
    writeValue(writer, value.houseId);
    writeValue(writer, value.portraitPictureId);
    writeValue(writer, value.npcPictureId);
    writeValue(writer, value.character);
}

bool readValue(BinaryReader &reader, EventRuntimeState::GeneratedMercenaryRecruit &value)
{
    const bool loaded = readValue(reader, value.npcId)
        && readValue(reader, value.rosterId)
        && readValue(reader, value.houseId)
        && readValue(reader, value.portraitPictureId)
        && (reader.version() < SaveVersionGeneratedMercenaryNpcPicture
            || readValue(reader, value.npcPictureId))
        && readValue(reader, value.character);

    if (loaded && reader.version() < SaveVersionGeneratedMercenaryNpcPicture)
    {
        value.npcPictureId = value.portraitPictureId;
    }

    return loaded;
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::ActiveDecorationContext &value)
{
    writeValue(writer, value.decorVarIndex);
    writeValue(writer, value.baseEventId);
    writeValue(writer, value.currentEventId);
    writeValue(writer, value.eventCount);
    writeValue(writer, value.hideWhenCleared);
}

bool readValue(BinaryReader &reader, EventRuntimeState::ActiveDecorationContext &value)
{
    return readValue(reader, value.decorVarIndex)
        && readValue(reader, value.baseEventId)
        && readValue(reader, value.currentEventId)
        && readValue(reader, value.eventCount)
        && readValue(reader, value.hideWhenCleared);
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::PortraitFxRequest &value)
{
    writeValue(writer, value.kind);
    writeValue(writer, value.memberIndices);
}

bool readValue(BinaryReader &reader, EventRuntimeState::PortraitFxRequest &value)
{
    return readValue(reader, value.kind)
        && readValue(reader, value.memberIndices);
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::SpellFxRequest &value)
{
    writeValue(writer, value.spellId);
    writeValue(writer, value.memberIndices);
}

bool readValue(BinaryReader &reader, EventRuntimeState::SpellFxRequest &value)
{
    return readValue(reader, value.spellId)
        && readValue(reader, value.memberIndices);
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::RuntimeMapNote &value)
{
    writeValue(writer, value.id);
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.mapFileName);
    writeValue(writer, value.text);
    writeValue(writer, value.active);
}

bool readValue(BinaryReader &reader, EventRuntimeState::RuntimeMapNote &value)
{
    if (!readValue(reader, value.id)
        || !readValue(reader, value.x)
        || !readValue(reader, value.y))
    {
        return false;
    }

    if (reader.version() >= SaveVersionRuntimeMapNoteMapFile)
    {
        if (!readValue(reader, value.mapFileName))
        {
            return false;
        }
    }
    else
    {
        value.mapFileName.clear();
    }

    return readValue(reader, value.text)
        && readValue(reader, value.active);
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::ChestItemRequest &value)
{
    writeValue(writer, value.itemId);
    writeValue(writer, value.gridX);
    writeValue(writer, value.gridY);
}

bool readValue(BinaryReader &reader, EventRuntimeState::ChestItemRequest &value)
{
    return readValue(reader, value.itemId)
        && readValue(reader, value.gridX)
        && readValue(reader, value.gridY);
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::HiredNpcFollower &value)
{
    writeValue(writer, value.npcId);
    writeValue(writer, value.professionId);
    writeValue(writer, value.weeklyCost);
    writeValue(writer, value.abilityUsedDay);
    writeValue(writer, value.name);
    writeValue(writer, value.pictureId);
}

bool readValue(BinaryReader &reader, EventRuntimeState::HiredNpcFollower &value)
{
    return readValue(reader, value.npcId)
        && readValue(reader, value.professionId)
        && readValue(reader, value.weeklyCost)
        && (reader.version() < SaveVersionHiredNpcFollowerAbilityUseDay || readValue(reader, value.abilityUsedDay))
        && (reader.version() < SaveVersionHiredNpcFollowerIdentity || readValue(reader, value.name))
        && (reader.version() < SaveVersionHiredNpcFollowerIdentity || readValue(reader, value.pictureId));
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::SavedLocation &value)
{
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.z);
    writeValue(writer, value.continentId);
    writeValue(writer, value.mapName);
}

bool readValue(BinaryReader &reader, EventRuntimeState::SavedLocation &value)
{
    return readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.z)
        && readValue(reader, value.continentId)
        && readValue(reader, value.mapName);
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::TransportRouteOverride &value)
{
    writeValue(writer, value.houseId);
    writeValue(writer, value.routeIndex);
    writeValue(writer, value.destinationName);
    writeValue(writer, value.mapFileName);
    writeValue(writer, value.daysAvailable);
    writeValue(writer, value.travelDays);
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.z);
    writeValue(writer, value.directionDegrees);
    writeValue(writer, value.requiredQBit);
    writeValue(writer, value.useMapStartPosition);
}

bool readValue(BinaryReader &reader, EventRuntimeState::TransportRouteOverride &value)
{
    return readValue(reader, value.houseId)
        && readValue(reader, value.routeIndex)
        && readValue(reader, value.destinationName)
        && readValue(reader, value.mapFileName)
        && readValue(reader, value.daysAvailable)
        && readValue(reader, value.travelDays)
        && readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.z)
        && readValue(reader, value.directionDegrees)
        && readValue(reader, value.requiredQBit)
        && readValue(reader, value.useMapStartPosition);
}

void writeValue(BinaryWriter &writer, const EventRuntimeState &value)
{
    writeValue(writer, value.variables);
    writeValue(writer, value.namedMapVars);
    writeValue(writer, value.namedGlobalVars);
    writeValue(writer, value.runtimeMapNotes);
    writeValue(writer, value.savedLocations);
    writeValue(writer, value.transportRouteOverrides);
    writeValue(writer, value.activeHistoryContinentId);
    writeValue(writer, value.historyEventTimes);
    writeValue(writer, value.historyEventTimesByContinent);
    writeValue(writer, value.mapVars);
    writeValue(writer, value.currentLocationReputation);
    writeValue(writer, value.facetSetMasks);
    writeValue(writer, value.facetClearMasks);
    writeValue(writer, value.mechanisms);
    writeValue(writer, value.destructibles);
    writeValue(writer, value.outdoorModelMechanisms);
    writeValue(writer, value.textureOverrides);
    writeValue(writer, value.outdoorModelFacetTextureOverrides);
    writeValue(writer, value.spriteOverrides);
    writeValue(writer, value.indoorLightsEnabled);
    writeValue(writer, value.snowEnabled);
    writeValue(writer, value.rainEnabled);
    writeValue(writer, value.actorSetMasks);
    writeValue(writer, value.actorClearMasks);
    writeValue(writer, value.actorGroupSetMasks);
    writeValue(writer, value.actorGroupClearMasks);
    writeValue(writer, value.actorIdGroupOverrides);
    writeValue(writer, value.actorGroupOverrides);
    writeValue(writer, value.actorGroupAllyOverrides);
    writeValue(writer, value.chestSetMasks);
    writeValue(writer, value.chestClearMasks);
    writeValue(writer, value.npcTopicOverrides);
    writeValue(writer, value.npcGroupNews);
    writeValue(writer, value.npcGreetingOverrides);
    writeValue(writer, value.npcGreetingDisplayCounts);
    writeValue(writer, value.npcHouseOverrides);
    writeValue(writer, value.npcNameOverrides);
    writeValue(writer, value.npcPictureOverrides);
    writeValue(writer, value.npcProfessionOverrides);
    writeValue(writer, value.generatedNpcIdsByActorKey);
    writeValue(writer, value.generatedMercenaryRecruitsByNpcId);
    writeValue(writer, value.npcItemOverrides);
    writeValue(writer, value.actorItemOverrides);
    writeValue(writer, value.actorExtraItemOverrides);
    writeValue(writer, value.monsterRelationOverrides);
    writeValue(writer, value.chestItemRequests);
    writeValue(writer, value.unavailableNpcIds);
    writeValue(writer, value.hiredNpcFollowers);
    writeValue(writer, value.dialogueState);
    writeValue(writer, value.decorVars);
    writeValue(writer, value.activeDecorationContext);
    writeValue(writer, value.messages);
    writeValue(writer, value.statusMessages);
    writeValue(writer, value.openedChestIds);
    writeValue(writer, value.grantedItems);
    writeValue(writer, value.grantedItemIds);
    writeValue(writer, value.removedItemIds);
    writeValue(writer, value.grantedAwardIds);
    writeValue(writer, value.removedAwardIds);
    writeValue(writer, value.portraitFxRequests);
    writeValue(writer, value.spellFxRequests);
    writeValue(writer, value.pendingDialogueContext);
    writeValue(writer, value.pendingMapMove);
    writeValue(writer, value.pendingMovie);
    writePendingInputPromptForSave(writer, value);
    writeValue(writer, value.pendingArcomageGame);
    writeValue(writer, value.pendingSounds);
    writeValue(writer, value.lastAffectedMechanismIds);
    writeValue(writer, value.lastActivationResult);
    writeValue(writer, value.localOnLoadEventsExecuted);
    writeValue(writer, value.globalOnLoadEventsExecuted);
    writeValue(writer, value.processedMapRespawnCount);
    writeValue(writer, value.legacyCampFireDecorVars);
    writeValue(writer, value.legacySmallBarrelDecorVars);
}

bool readValue(BinaryReader &reader, EventRuntimeState &value)
{
    const bool ok = readValue(reader, value.variables)
        && (reader.version() < SaveVersionNamedLuaVars || readValue(reader, value.namedMapVars))
        && (reader.version() < SaveVersionNamedLuaVars || readValue(reader, value.namedGlobalVars))
        && (reader.version() < SaveVersionRuntimeMapNotes || readValue(reader, value.runtimeMapNotes))
        && (reader.version() < SaveVersionPersistentLuaRuntimeState || readValue(reader, value.savedLocations))
        && (reader.version() < SaveVersionPersistentLuaRuntimeState || readValue(reader, value.transportRouteOverrides))
        && (reader.version() < SaveVersionScopedHistory || readValue(reader, value.activeHistoryContinentId))
        && readValue(reader, value.historyEventTimes)
        && (reader.version() < SaveVersionScopedHistory || readValue(reader, value.historyEventTimesByContinent))
        && readValue(reader, value.mapVars)
        && (reader.version() < SaveVersionPartyContinentReputations
            || readValue(reader, value.currentLocationReputation))
        && readValue(reader, value.facetSetMasks)
        && readValue(reader, value.facetClearMasks)
        && readValue(reader, value.mechanisms)
        && (reader.version() < SaveVersionOutdoorDestructibles
            || readValue(reader, value.destructibles))
        && (reader.version() < SaveVersionOutdoorModelMechanisms
            || readValue(reader, value.outdoorModelMechanisms))
        && readValue(reader, value.textureOverrides)
        && (reader.version() < SaveVersionMapLuaRuntimeOverlays
            || readValue(reader, value.outdoorModelFacetTextureOverrides))
        && readValue(reader, value.spriteOverrides)
        && readValue(reader, value.indoorLightsEnabled)
        && readValue(reader, value.snowEnabled)
        && readValue(reader, value.rainEnabled)
        && readValue(reader, value.actorSetMasks)
        && readValue(reader, value.actorClearMasks)
        && readValue(reader, value.actorGroupSetMasks)
        && readValue(reader, value.actorGroupClearMasks)
        && readValue(reader, value.actorIdGroupOverrides)
        && readValue(reader, value.actorGroupOverrides)
        && readValue(reader, value.actorGroupAllyOverrides)
        && readValue(reader, value.chestSetMasks)
        && readValue(reader, value.chestClearMasks)
        && readValue(reader, value.npcTopicOverrides)
        && readValue(reader, value.npcGroupNews)
        && readValue(reader, value.npcGreetingOverrides)
        && readValue(reader, value.npcGreetingDisplayCounts)
        && readValue(reader, value.npcHouseOverrides)
        && (reader.version() < SaveVersionGeneratedNpcOverrides || readValue(reader, value.npcNameOverrides))
        && (reader.version() < SaveVersionGeneratedNpcOverrides || readValue(reader, value.npcPictureOverrides))
        && (reader.version() < SaveVersionGeneratedNpcOverrides || readValue(reader, value.npcProfessionOverrides))
        && (reader.version() < SaveVersionGeneratedNpcOverrides || readValue(reader, value.generatedNpcIdsByActorKey))
        && (reader.version() < SaveVersionGeneratedMercenaryRecruits
            || readValue(reader, value.generatedMercenaryRecruitsByNpcId))
        && readValue(reader, value.npcItemOverrides)
        && readValue(reader, value.actorItemOverrides)
        && (reader.version() < SaveVersionActorExtraItemOverrides
            || readValue(reader, value.actorExtraItemOverrides))
        && (reader.version() < SaveVersionMapLuaRuntimeOverlays || readValue(reader, value.monsterRelationOverrides))
        && (reader.version() < SaveVersionMapLuaRuntimeOverlays || readValue(reader, value.chestItemRequests))
        && readValue(reader, value.unavailableNpcIds)
        && (reader.version() < SaveVersionHiredNpcFollowers || readValue(reader, value.hiredNpcFollowers))
        && readValue(reader, value.dialogueState)
        && readValue(reader, value.decorVars)
        && readValue(reader, value.activeDecorationContext)
        && readValue(reader, value.messages)
        && readValue(reader, value.statusMessages)
        && readValue(reader, value.openedChestIds)
        && readValue(reader, value.grantedItems)
        && readValue(reader, value.grantedItemIds)
        && readValue(reader, value.removedItemIds)
        && readValue(reader, value.grantedAwardIds)
        && readValue(reader, value.removedAwardIds)
        && readValue(reader, value.portraitFxRequests)
        && readValue(reader, value.spellFxRequests)
        && readValue(reader, value.pendingDialogueContext)
        && readValue(reader, value.pendingMapMove)
        && readValue(reader, value.pendingMovie)
        && readPendingInputPromptForSave(reader, value)
        && readValue(reader, value.pendingArcomageGame)
        && readValue(reader, value.pendingSounds)
        && readValue(reader, value.lastAffectedMechanismIds)
        && readValue(reader, value.lastActivationResult)
        && readValue(reader, value.localOnLoadEventsExecuted)
        && readValue(reader, value.globalOnLoadEventsExecuted)
        && (reader.version() < SaveVersionActorExtraItemOverrides
            || readValue(reader, value.processedMapRespawnCount))
        && (reader.version() < SaveVersionMMergeCampfireDecorVars
            || readValue(reader, value.legacyCampFireDecorVars))
        && (reader.version() < SaveVersionSmallStatBarrels
            || readValue(reader, value.legacySmallBarrelDecorVars));

    if (!ok)
    {
        return false;
    }

    value.activeHistoryContinentId = normalizedHistoryContinentId(value.activeHistoryContinentId);

    if (value.historyEventTimesByContinent.empty() && !value.historyEventTimes.empty())
    {
        value.historyEventTimesByContinent[1u] = value.historyEventTimes;
    }

    return true;
}

void writeValue(BinaryWriter &writer, const MapDeltaChest &value)
{
    writeValue(writer, value.chestTypeId);
    writeValue(writer, value.flags);
    writeValue(writer, value.rawItems);
    writeValue(writer, value.inventoryMatrix);
}

bool readValue(BinaryReader &reader, MapDeltaChest &value)
{
    return readValue(reader, value.chestTypeId)
        && readValue(reader, value.flags)
        && readValue(reader, value.rawItems)
        && readValue(reader, value.inventoryMatrix);
}

void writeValue(BinaryWriter &writer, const MapDeltaLocationInfo &value)
{
    writeValue(writer, value.respawnCount);
    writeValue(writer, value.lastRespawnDay);
    writeValue(writer, value.reputation);
    writeValue(writer, value.alertStatus);
    writeValue(writer, value.totalFacesCount);
    writeValue(writer, value.decorationCount);
    writeValue(writer, value.bmodelCount);
}

bool readValue(BinaryReader &reader, MapDeltaLocationInfo &value)
{
    return readValue(reader, value.respawnCount)
        && readValue(reader, value.lastRespawnDay)
        && readValue(reader, value.reputation)
        && readValue(reader, value.alertStatus)
        && readValue(reader, value.totalFacesCount)
        && readValue(reader, value.decorationCount)
        && readValue(reader, value.bmodelCount);
}

void writeValue(BinaryWriter &writer, const MapDeltaPersistentVariables &value)
{
    writeValue(writer, value.mapVars);
    writeValue(writer, value.decorVars);
}

bool readValue(BinaryReader &reader, MapDeltaPersistentVariables &value)
{
    return readValue(reader, value.mapVars)
        && readValue(reader, value.decorVars);
}

void writeValue(BinaryWriter &writer, const MapDeltaLocationTime &value)
{
    writeValue(writer, value.lastVisitTime);
    writeValue(writer, value.skyTextureName);
    writeValue(writer, value.weatherFlags);
    writeValue(writer, value.fogWeakDistance);
    writeValue(writer, value.fogStrongDistance);
    writeValue(writer, value.reserved);
}

bool readValue(BinaryReader &reader, MapDeltaLocationTime &value)
{
    return readValue(reader, value.lastVisitTime)
        && readValue(reader, value.skyTextureName)
        && readValue(reader, value.weatherFlags)
        && readValue(reader, value.fogWeakDistance)
        && readValue(reader, value.fogStrongDistance)
        && readValue(reader, value.reserved);
}

void writeValue(BinaryWriter &writer, const Mm9AiPlacementProfile &value)
{
    writeValue(writer, value.archetype);
    writeValue(writer, value.ranged);
    writeValue(writer, value.rangedWeapon);
    writeValue(writer, value.guardRefuge);
    writeValue(writer, value.throttle);
    writeValue(writer, value.alwaysEvade);
    writeValue(writer, value.evadeMinSeconds);
    writeValue(writer, value.evadeMaxSeconds);
    writeValue(writer, value.meleeWindowSeconds);
    writeValue(writer, value.spawnIn);
    writeValue(writer, value.deathSpawnMonsterId);
    writeValue(writer, value.passive);
    writeValue(writer, value.fromScene);
    writeValue(writer, value.footwork.has_value());

    if (value.footwork)
    {
        writeValue(writer, value.footwork->enabled);
        writeValue(writer, value.footwork->strafeAttackChance);
        writeValue(writer, value.footwork->evadeChance);
        writeValue(writer, value.footwork->tauntSeconds);
    }
}

bool readValue(BinaryReader &reader, Mm9AiPlacementProfile &value)
{
    bool hasFootwork = false;

    if (!readValue(reader, value.archetype)
        || !readValue(reader, value.ranged)
        || !readValue(reader, value.rangedWeapon)
        || !readValue(reader, value.guardRefuge)
        || !readValue(reader, value.throttle)
        || !readValue(reader, value.alwaysEvade)
        || !readValue(reader, value.evadeMinSeconds)
        || !readValue(reader, value.evadeMaxSeconds)
        || !readValue(reader, value.meleeWindowSeconds)
        || !readValue(reader, value.spawnIn)
        || !readValue(reader, value.deathSpawnMonsterId)
        || !readValue(reader, value.passive)
        || !readValue(reader, value.fromScene)
        || !readValue(reader, hasFootwork))
    {
        return false;
    }

    if (!hasFootwork)
    {
        value.footwork.reset();
        return true;
    }

    Mm9AiFootwork footwork = {};

    if (!readValue(reader, footwork.enabled)
        || !readValue(reader, footwork.strafeAttackChance)
        || !readValue(reader, footwork.evadeChance)
        || !readValue(reader, footwork.tauntSeconds))
    {
        return false;
    }

    value.footwork = footwork;
    return true;
}

void writeValue(BinaryWriter &writer, const Mm9AiPathStop &value)
{
    writeValue(writer, value.point);
    writeValue(writer, value.faces);
    writeValue(writer, value.faceYawRadians);
    writeValue(writer, value.ownWait);
    writeValue(writer, value.waitMinSeconds);
    writeValue(writer, value.waitMaxSeconds);
    writeValue(writer, value.clip);
    writeValue(writer, value.loop);
}

bool readValue(BinaryReader &reader, Mm9AiPathStop &value)
{
    return readValue(reader, value.point)
        && readValue(reader, value.faces)
        && readValue(reader, value.faceYawRadians)
        && readValue(reader, value.ownWait)
        && readValue(reader, value.waitMinSeconds)
        && readValue(reader, value.waitMaxSeconds)
        && readValue(reader, value.clip)
        && readValue(reader, value.loop);
}

void writeValue(BinaryWriter &writer, const Mm9AiRoutineClip &value)
{
    writeValue(writer, value.clip);
    writeValue(writer, value.seconds);
}

bool readValue(BinaryReader &reader, Mm9AiRoutineClip &value)
{
    return readValue(reader, value.clip) && readValue(reader, value.seconds);
}

void writeValue(BinaryWriter &writer, const Mm9AiRoutineStep &value)
{
    writeValue(writer, value.kind);
    writeValue(writer, value.point);
    writeValue(writer, value.faceYawRadians);
    writeValue(writer, value.clips);
    writeValue(writer, value.waitMinSeconds);
    writeValue(writer, value.waitMaxSeconds);
    writeValue(writer, value.chance);
    writeValue(writer, value.skip);
}

bool readValue(BinaryReader &reader, Mm9AiRoutineStep &value)
{
    return readValue(reader, value.kind)
        && readValue(reader, value.point)
        && readValue(reader, value.faceYawRadians)
        && readValue(reader, value.clips)
        && readValue(reader, value.waitMinSeconds)
        && readValue(reader, value.waitMaxSeconds)
        && readValue(reader, value.chance)
        && readValue(reader, value.skip);
}

void writeValue(BinaryWriter &writer, const Mm9AiRoutine &value)
{
    writeValue(writer, value.name);
    writeValue(writer, value.steps);
}

bool readValue(BinaryReader &reader, Mm9AiRoutine &value)
{
    return readValue(reader, value.name) && readValue(reader, value.steps);
}

void writeValue(BinaryWriter &writer, const MapDeltaHeldItem &value)
{
    writeValue(writer, value.model);
    writeValue(writer, value.node);
}

bool readValue(BinaryReader &reader, MapDeltaHeldItem &value)
{
    return readValue(reader, value.model) && readValue(reader, value.node);
}

void writeValue(BinaryWriter &writer, const Mm9AiPlacementRecord &value)
{
    const Mm9AiPlacement &settings = value.settings;
    writeValue(writer, settings.sight);
    writeValue(writer, settings.hearing);
    writeValue(writer, settings.runawayChance);
    writeValue(writer, settings.rangedType);
    writeValue(writer, settings.canBeResurrected);
    writeValue(writer, settings.wander);
    writeValue(writer, settings.wanderLeash);
    writeValue(writer, settings.wanderWaitMinSeconds);
    writeValue(writer, settings.wanderWaitMaxSeconds);
    writeValue(writer, settings.wanderTimeMinSeconds);
    writeValue(writer, settings.wanderTimeMaxSeconds);
    writeValue(writer, settings.pathRandom);
    writeValue(writer, settings.dormantUntil);
    writeValue(writer, settings.dormantPose);
    writeValue(writer, settings.hostility);
    writeValue(writer, settings.faction);
    writeValue(writer, settings.summoner);
    writeValue(writer, settings.startsDead);
    writeValue(writer, settings.boss);
    writeValue(writer, value.pathPoints);
    writeValue(writer, value.summonPoints);
    writeValue(writer, value.summonClass);
    writeValue(writer, value.script);
    writeValue(writer, value.scriptParams);
    writeValue(writer, value.hidingPlaces);
    writeValue(writer, settings.profile);
    writeValue(writer, value.pathStops);
    writeValue(writer, settings.idleClip);
    writeValue(writer, value.routines);
}

bool readValue(BinaryReader &reader, Mm9AiPlacementRecord &value)
{
    Mm9AiPlacement &settings = value.settings;
    return readValue(reader, settings.sight)
        && readValue(reader, settings.hearing)
        && readValue(reader, settings.runawayChance)
        && readValue(reader, settings.rangedType)
        && readValue(reader, settings.canBeResurrected)
        && readValue(reader, settings.wander)
        && readValue(reader, settings.wanderLeash)
        && readValue(reader, settings.wanderWaitMinSeconds)
        && readValue(reader, settings.wanderWaitMaxSeconds)
        && readValue(reader, settings.wanderTimeMinSeconds)
        && readValue(reader, settings.wanderTimeMaxSeconds)
        && readValue(reader, settings.pathRandom)
        && readValue(reader, settings.dormantUntil)
        && readValue(reader, settings.dormantPose)
        && readValue(reader, settings.hostility)
        && readValue(reader, settings.faction)
        && readValue(reader, settings.summoner)
        && readValue(reader, settings.startsDead)
        && readValue(reader, settings.boss)
        && readValue(reader, value.pathPoints)
        && readValue(reader, value.summonPoints)
        && readValue(reader, value.summonClass)
        && readValue(reader, value.script)
        && readValue(reader, value.scriptParams)
        && (reader.version() < SaveVersionActorMm9HidingPlaces || readValue(reader, value.hidingPlaces))
        && (reader.version() < SaveVersionActorMm9PlacementProfile ? (settings.profile.fromScene = true)
            : readValue(reader, settings.profile))
        && (reader.version() < SaveVersionMm9PathStops || readValue(reader, value.pathStops))
        && (reader.version() >= SaveVersionMm9IdleClip ? readValue(reader, settings.idleClip)
                                                       : (settings.profile.fromScene = true))
        && (reader.version() >= SaveVersionMm9Routines ? readValue(reader, value.routines)
                                                       : (settings.profile.fromScene = true));
}

void writeValue(BinaryWriter &writer, const MapDeltaActor &value)
{
    writeValue(writer, value.name);
    writeValue(writer, value.npcId);
    writeValue(writer, value.attributes);
    writeValue(writer, value.hp);
    writeValue(writer, value.hostilityType);
    writeValue(writer, value.monsterInfoId);
    writeValue(writer, value.monsterId);
    writeValue(writer, value.radius);
    writeValue(writer, value.height);
    writeValue(writer, value.moveSpeed);
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.z);
    writeValue(writer, value.spriteIds);
    writeValue(writer, value.sectorId);
    writeValue(writer, value.currentActionAnimation);
    writeValue(writer, value.carriedItemId);
    writeValue(writer, value.group);
    writeValue(writer, value.ally);
    writeValue(writer, value.uniqueNameIndex);
    writeValue(writer, value.bolsterRewardMultiplier);
    const uint64_t diagnosticSourceActorIndex =
        value.diagnosticSourceActorIndex != static_cast<size_t>(-1)
            ? static_cast<uint64_t>(value.diagnosticSourceActorIndex)
            : std::numeric_limits<uint64_t>::max();
    writeValue(writer, diagnosticSourceActorIndex);
    writeValue(writer, value.mm9RudeId);
    writeValue(writer, value.mm9SourceObjectIndex);
    writeValue(writer, value.initialYawUnits);
    writeValue(writer, value.immobile);
    writeValue(writer, value.mm9CanReceiveDamage);
    writeValue(writer, value.mm9Civilian);
    writeValue(writer, value.mm9Guard);
    writeValue(writer, value.proceduralDeathLoot);
    writeValue(writer, value.rulesetFacts);
    writeValue(writer, value.spawnedAfterFill);
    writeValue(writer, value.summonerMemberIndex);
    writeValue(writer, value.keepsHeight);
    writeValue(writer, value.leashRadius);
    writeValue(writer, value.dormant);
    writeValue(writer, value.patrolPoints);
    writeValue(writer, value.mm9Ai);
    writeValue(writer, value.drawScale);
    writeValue(writer, value.posed);
    writeValue(writer, value.heldItems);
}

bool readHitPoints(BinaryReader &reader, int32_t &value)
{
    if (reader.version() >= SaveVersionActorRulesetFacts)
    {
        return readValue(reader, value);
    }

    int16_t narrowHitPoints = 0;

    if (!readValue(reader, narrowHitPoints))
    {
        return false;
    }

    value = narrowHitPoints;
    return true;
}

bool readValue(BinaryReader &reader, MapDeltaActor &value)
{
    if (!(readValue(reader, value.name)
        && readValue(reader, value.npcId)
        && readValue(reader, value.attributes)
        && readHitPoints(reader, value.hp)
        && readValue(reader, value.hostilityType)
        && readValue(reader, value.monsterInfoId)
        && readValue(reader, value.monsterId)
        && readValue(reader, value.radius)
        && readValue(reader, value.height)
        && readValue(reader, value.moveSpeed)
        && readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.z)
        && readValue(reader, value.spriteIds)
        && readValue(reader, value.sectorId)
        && readValue(reader, value.currentActionAnimation)
        && (reader.version() < SaveVersionActorCarriedItem || readValue(reader, value.carriedItemId))
        && readValue(reader, value.group)
        && readValue(reader, value.ally)
        && readValue(reader, value.uniqueNameIndex)
        && (reader.version() < SaveVersionMonsterBolsterRewards || readValue(reader, value.bolsterRewardMultiplier))))
    {
        return false;
    }

    if (reader.version() >= SaveVersionActorDiagnosticSource)
    {
        uint64_t diagnosticSourceActorIndex = std::numeric_limits<uint64_t>::max();

        if (!readValue(reader, diagnosticSourceActorIndex))
        {
            return false;
        }

        value.diagnosticSourceActorIndex = static_cast<size_t>(-1);

        if (diagnosticSourceActorIndex != std::numeric_limits<uint64_t>::max()
            && diagnosticSourceActorIndex <= static_cast<uint64_t>(std::numeric_limits<size_t>::max()))
        {
            value.diagnosticSourceActorIndex = static_cast<size_t>(diagnosticSourceActorIndex);
        }
    }

    if (reader.version() >= SaveVersionMm9DialogueActors
        && (!readValue(reader, value.mm9RudeId)
            || !readValue(reader, value.mm9SourceObjectIndex)
            || !readValue(reader, value.initialYawUnits)
            || !readValue(reader, value.immobile)))
    {
        return false;
    }

    if (reader.version() >= SaveVersionMm9ActorReactions
        && (!readValue(reader, value.mm9CanReceiveDamage)
            || !readValue(reader, value.mm9Civilian)
            || !readValue(reader, value.mm9Guard)))
    {
        return false;
    }

    if (reader.version() >= SaveVersionActorProceduralDeathLoot
        && !readValue(reader, value.proceduralDeathLoot))
    {
        return false;
    }

    return (reader.version() < SaveVersionActorRulesetFacts || readValue(reader, value.rulesetFacts))
        && (reader.version() < SaveVersionActorSpawnedAfterFill || readValue(reader, value.spawnedAfterFill))
        && (reader.version() < SaveVersionActorSummoner || readValue(reader, value.summonerMemberIndex))
        && (reader.version() < SaveVersionActorKeepsHeight
            || (readValue(reader, value.keepsHeight) && readValue(reader, value.leashRadius)
                && readValue(reader, value.dormant)))
        && (reader.version() < SaveVersionActorPatrol || readValue(reader, value.patrolPoints))
        && (reader.version() < SaveVersionActorMm9AiPlacement || readValue(reader, value.mm9Ai))
        && (reader.version() < SaveVersionActorDrawScale || readValue(reader, value.drawScale))
        && (reader.version() < SaveVersionActorPosed || readValue(reader, value.posed))
        && (reader.version() < SaveVersionActorHeldItems || readValue(reader, value.heldItems));
}

void writeValue(BinaryWriter &writer, const MapDeltaSpriteObject &value)
{
    writeValue(writer, value.spriteId);
    writeValue(writer, value.objectDescriptionId);
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.z);
    writeValue(writer, value.velocityX);
    writeValue(writer, value.velocityY);
    writeValue(writer, value.velocityZ);
    writeValue(writer, value.yawAngle);
    writeValue(writer, value.soundId);
    writeValue(writer, value.attributes);
    writeValue(writer, value.sectorId);
    writeValue(writer, value.timeSinceCreated);
    writeValue(writer, value.temporaryLifetime);
    writeValue(writer, value.glowRadiusMultiplier);
    writeValue(writer, value.spellId);
    writeValue(writer, value.spellLevel);
    writeValue(writer, value.spellSkill);
    writeValue(writer, value.field54);
    writeValue(writer, value.spellCasterPid);
    writeValue(writer, value.spellTargetPid);
    writeValue(writer, value.lodDistance);
    writeValue(writer, value.spellCasterAbility);
    writeValue(writer, value.initialX);
    writeValue(writer, value.initialY);
    writeValue(writer, value.initialZ);
    writeValue(writer, value.rawContainingItem);
    writeValue(writer, value.semanticSourceId);
    writeValue(writer, value.semanticLootContainerId);
    writeValue(writer, value.semanticPlacedPickup);
    writeValue(writer, value.semanticLootContainer);
    writeValue(writer, value.semanticPolicyHidden);
    writeValue(writer, value.heldItem);
    writeValue(writer, value.objectKey);
}

bool readValue(BinaryReader &reader, MapDeltaSpriteObject &value)
{
    return readValue(reader, value.spriteId)
        && readValue(reader, value.objectDescriptionId)
        && readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.z)
        && readValue(reader, value.velocityX)
        && readValue(reader, value.velocityY)
        && readValue(reader, value.velocityZ)
        && readValue(reader, value.yawAngle)
        && readValue(reader, value.soundId)
        && readValue(reader, value.attributes)
        && readValue(reader, value.sectorId)
        && readValue(reader, value.timeSinceCreated)
        && readValue(reader, value.temporaryLifetime)
        && readValue(reader, value.glowRadiusMultiplier)
        && readValue(reader, value.spellId)
        && readValue(reader, value.spellLevel)
        && readValue(reader, value.spellSkill)
        && readValue(reader, value.field54)
        && readValue(reader, value.spellCasterPid)
        && readValue(reader, value.spellTargetPid)
        && readValue(reader, value.lodDistance)
        && readValue(reader, value.spellCasterAbility)
        && readValue(reader, value.initialX)
        && readValue(reader, value.initialY)
        && readValue(reader, value.initialZ)
        && readValue(reader, value.rawContainingItem)
        && (reader.version() < SaveVersionMm9IndoorSemanticWorldItems
            || (readValue(reader, value.semanticSourceId)
                && readValue(reader, value.semanticLootContainerId)
                && readValue(reader, value.semanticPlacedPickup)
                && readValue(reader, value.semanticLootContainer)
                && readValue(reader, value.semanticPolicyHidden)))
        && (reader.version() < SaveVersionIndoorHeldItems || readValue(reader, value.heldItem))
        && (reader.version() < SaveVersionSpriteObjectKeys || readValue(reader, value.objectKey));
}

void writeValue(BinaryWriter &writer, const MapDeltaDoor &value)
{
    writeValue(writer, value.slotIndex);
    writeValue(writer, value.attributes);
    writeValue(writer, value.doorId);
    writeValue(writer, value.timeSinceTriggered);
    writeValue(writer, value.directionX);
    writeValue(writer, value.directionY);
    writeValue(writer, value.directionZ);
    writeValue(writer, value.moveLength);
    writeValue(writer, value.openSpeed);
    writeValue(writer, value.closeSpeed);
    writeValue(writer, value.numVertices);
    writeValue(writer, value.numFaces);
    writeValue(writer, value.numSectors);
    writeValue(writer, value.numOffsets);
    writeValue(writer, value.state);
    writeValue(writer, value.vertexIds);
    writeValue(writer, value.faceIds);
    writeValue(writer, value.sectorIds);
    writeValue(writer, value.deltaUs);
    writeValue(writer, value.deltaVs);
    writeValue(writer, value.xOffsets);
    writeValue(writer, value.yOffsets);
    writeValue(writer, value.zOffsets);
}

bool readValue(BinaryReader &reader, MapDeltaDoor &value)
{
    return readValue(reader, value.slotIndex)
        && readValue(reader, value.attributes)
        && readValue(reader, value.doorId)
        && readValue(reader, value.timeSinceTriggered)
        && readValue(reader, value.directionX)
        && readValue(reader, value.directionY)
        && readValue(reader, value.directionZ)
        && readValue(reader, value.moveLength)
        && readValue(reader, value.openSpeed)
        && readValue(reader, value.closeSpeed)
        && readValue(reader, value.numVertices)
        && readValue(reader, value.numFaces)
        && readValue(reader, value.numSectors)
        && readValue(reader, value.numOffsets)
        && readValue(reader, value.state)
        && readValue(reader, value.vertexIds)
        && readValue(reader, value.faceIds)
        && readValue(reader, value.sectorIds)
        && readValue(reader, value.deltaUs)
        && readValue(reader, value.deltaVs)
        && readValue(reader, value.xOffsets)
        && readValue(reader, value.yOffsets)
        && readValue(reader, value.zOffsets);
}

void writeValue(BinaryWriter &writer, const MapDeltaMm9BarrelState &value)
{
    writeValue(writer, value.sourceObjectIndex);
    writeValue(writer, value.type);
    writeValue(writer, value.used);
}

bool readValue(BinaryReader &reader, MapDeltaMm9BarrelState &value)
{
    uint8_t rawType = 0;
    if (!readValue(reader, value.sourceObjectIndex)
        || !readValue(reader, rawType)
        || !readValue(reader, value.used)
        || rawType < static_cast<uint8_t>(Mm9BarrelType::RedMight)
        || rawType > static_cast<uint8_t>(Mm9BarrelType::Water))
    {
        return false;
    }
    value.type = static_cast<Mm9BarrelType>(rawType);
    return true;
}

void writeValue(BinaryWriter &writer, const MapDeltaData &value)
{
    writeValue(writer, value.locationInfo);
    writeValue(writer, value.fullyRevealedCells);
    writeValue(writer, value.partiallyRevealedCells);
    writeValue(writer, value.visibleOutlines);
    writeValue(writer, value.faceAttributes);
    writeValue(writer, value.decorationFlags);
    writeValue(writer, value.actors);
    writeValue(writer, value.spriteObjects);
    writeValue(writer, value.chests);
    writeValue(writer, value.doorSlotCount);
    writeValue(writer, value.doors);
    writeValue(writer, value.doorsData);
    writeValue(writer, value.eventVariables);
    writeValue(writer, value.locationTime);
    writeValue(writer, value.mm9Barrels);
    writeValue(writer, value.takenWorldItems);
}

bool readValue(BinaryReader &reader, MapDeltaData &value)
{
    return readValue(reader, value.locationInfo)
        && readValue(reader, value.fullyRevealedCells)
        && readValue(reader, value.partiallyRevealedCells)
        && readValue(reader, value.visibleOutlines)
        && readValue(reader, value.faceAttributes)
        && readValue(reader, value.decorationFlags)
        && readValue(reader, value.actors)
        && readValue(reader, value.spriteObjects)
        && readValue(reader, value.chests)
        && readValue(reader, value.doorSlotCount)
        && readValue(reader, value.doors)
        && readValue(reader, value.doorsData)
        && readValue(reader, value.eventVariables)
        && readValue(reader, value.locationTime)
        && (reader.version() < SaveVersionMm9Barrels || readValue(reader, value.mm9Barrels))
        && (reader.version() < SaveVersionTakenWorldItems || readValue(reader, value.takenWorldItems));
}

void writeValue(BinaryWriter &writer, const ScriptedEventTimerDefinition &value)
{
    writeValue(writer, value.scope);
    writeValue(writer, value.origin);
    writeValue(writer, value.triggerKind);
    writeValue(writer, value.scheduleKind);
    writeValue(writer, value.eventId);
    writeValue(writer, value.sourceEventId);
    writeValue(writer, value.triggerStep);
    writeValue(writer, value.registrationIndex);
    writeValue(writer, value.repeating);
    writeValue(writer, value.intervalHalfMinutes);
    writeValue(writer, value.startHour);
    writeValue(writer, value.startMinute);
    writeValue(writer, value.startSecond);
    writeValue(writer, value.intervalGameMinutes);
    writeValue(writer, value.initialDelayGameMinutes);
}

bool readValue(BinaryReader &reader, ScriptedEventTimerDefinition &value)
{
    return readValue(reader, value.scope)
        && readValue(reader, value.origin)
        && readValue(reader, value.triggerKind)
        && readValue(reader, value.scheduleKind)
        && readValue(reader, value.eventId)
        && readValue(reader, value.sourceEventId)
        && readValue(reader, value.triggerStep)
        && readValue(reader, value.registrationIndex)
        && readValue(reader, value.repeating)
        && readValue(reader, value.intervalHalfMinutes)
        && readValue(reader, value.startHour)
        && readValue(reader, value.startMinute)
        && readValue(reader, value.startSecond)
        && readValue(reader, value.intervalGameMinutes)
        && readValue(reader, value.initialDelayGameMinutes);
}

void writeValue(BinaryWriter &writer, const ScriptedEventTimerState &value)
{
    writeValue(writer, value.definition);
    writeValue(writer, value.nextAlarmGameMinutes);
    writeValue(writer, value.eligibleGameMinutes);
    writeValue(writer, value.hasFired);
    writeValue(writer, value.initialCalendarFirePending);
    writeValue(writer, value.migratedFromLegacySave);
    writeValue(writer, value.migratedRemainingGameMinutes);
    writeValue(writer, value.stopped);
}

bool readValue(BinaryReader &reader, ScriptedEventTimerState &value)
{
    return readValue(reader, value.definition)
        && readValue(reader, value.nextAlarmGameMinutes)
        && readValue(reader, value.eligibleGameMinutes)
        && readValue(reader, value.hasFired)
        && readValue(reader, value.initialCalendarFirePending)
        && readValue(reader, value.migratedFromLegacySave)
        && readValue(reader, value.migratedRemainingGameMinutes)
        && (reader.version() < SaveVersionStoppedTimers || readValue(reader, value.stopped));
}

struct LegacyOutdoorTimerState
{
    uint16_t eventId = 0;
    bool repeating = false;
    float intervalGameMinutes = 0.0f;
    float remainingGameMinutes = 0.0f;
    std::optional<int> targetHour;
    bool hasFired = false;
};

bool readValue(BinaryReader &reader, LegacyOutdoorTimerState &value)
{
    return readValue(reader, value.eventId)
        && readValue(reader, value.repeating)
        && readValue(reader, value.intervalGameMinutes)
        && readValue(reader, value.remainingGameMinutes)
        && readValue(reader, value.targetHour)
        && readValue(reader, value.hasFired);
}

struct LegacyIndoorTimerState
{
    uint16_t eventId = 0;
    bool repeating = false;
    int targetHour = 0;
    float intervalGameMinutes = 0.0f;
    float remainingGameMinutes = 0.0f;
    bool hasFired = false;
};

bool readValue(BinaryReader &reader, LegacyIndoorTimerState &value)
{
    return readValue(reader, value.eventId)
        && readValue(reader, value.repeating)
        && readValue(reader, value.targetHour)
        && readValue(reader, value.intervalGameMinutes)
        && readValue(reader, value.remainingGameMinutes)
        && readValue(reader, value.hasFired);
}

ScriptedEventTimerState migrateLegacyTimerState(
    uint16_t eventId,
    bool repeating,
    float intervalGameMinutes,
    float remainingGameMinutes,
    bool hasFired,
    uint32_t registrationIndex)
{
    ScriptedEventTimerState state = {};
    state.definition.scope = ScriptedEventScope::Map;
    state.definition.origin = ScriptedEventTimerOrigin::Native;
    state.definition.scheduleKind = ScriptedEventTimerScheduleKind::Relative;
    state.definition.eventId = eventId;
    state.definition.sourceEventId = eventId;
    state.definition.registrationIndex = registrationIndex;
    state.definition.repeating = repeating;
    state.definition.intervalGameMinutes = intervalGameMinutes;
    state.hasFired = hasFired;
    state.migratedFromLegacySave = true;
    state.migratedRemainingGameMinutes = remainingGameMinutes;
    return state;
}

bool readOutdoorTimerStates(BinaryReader &reader, std::vector<ScriptedEventTimerState> &values)
{
    if (reader.version() >= SaveVersionLegacyEvtTimers)
    {
        return readValue(reader, values);
    }

    std::vector<LegacyOutdoorTimerState> legacyValues;
    if (!readValue(reader, legacyValues))
    {
        return false;
    }

    values.clear();
    values.reserve(legacyValues.size());

    for (size_t index = 0; index < legacyValues.size(); ++index)
    {
        const LegacyOutdoorTimerState &legacyValue = legacyValues[index];
        values.push_back(migrateLegacyTimerState(
            legacyValue.eventId,
            legacyValue.repeating,
            legacyValue.intervalGameMinutes,
            legacyValue.remainingGameMinutes,
            legacyValue.hasFired,
            static_cast<uint32_t>(index + 1)));
    }

    return true;
}

bool readIndoorTimerStates(BinaryReader &reader, std::vector<ScriptedEventTimerState> &values)
{
    if (reader.version() >= SaveVersionLegacyEvtTimers)
    {
        return readValue(reader, values);
    }

    std::vector<LegacyIndoorTimerState> legacyValues;
    if (!readValue(reader, legacyValues))
    {
        return false;
    }

    values.clear();
    values.reserve(legacyValues.size());

    for (size_t index = 0; index < legacyValues.size(); ++index)
    {
        const LegacyIndoorTimerState &legacyValue = legacyValues[index];
        values.push_back(migrateLegacyTimerState(
            legacyValue.eventId,
            legacyValue.repeating,
            legacyValue.intervalGameMinutes,
            legacyValue.remainingGameMinutes,
            legacyValue.hasFired,
            static_cast<uint32_t>(index + 1)));
    }

    return true;
}

void writeValue(BinaryWriter &writer, const OutdoorWorldRuntime::MapActorState &value)
{
    writeValue(writer, value.actorId);
    writeValue(writer, value.monsterId);
    writeValue(writer, value.displayName);
    writeValue(writer, value.uniqueNameId);
    writeValue(writer, value.spawnedAtRuntime);
    writeValue(writer, value.fromSpawnPoint);
    writeValue(writer, value.spawnPointIndex);
    writeValue(writer, value.group);
    writeValue(writer, value.ally);
    writeValue(writer, value.hostilityType);
    writeValue(writer, value.specialItemId);
    writeValue(writer, value.currentHp);
    writeValue(writer, value.maxHp);
    writeValue(writer, value.bolsterRewardMultiplier);
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.z);
    writeValue(writer, value.preciseX);
    writeValue(writer, value.preciseY);
    writeValue(writer, value.preciseZ);
    writeValue(writer, value.homeX);
    writeValue(writer, value.homeY);
    writeValue(writer, value.homeZ);
    writeValue(writer, value.homePreciseX);
    writeValue(writer, value.homePreciseY);
    writeValue(writer, value.homePreciseZ);
    writeValue(writer, value.radius);
    writeValue(writer, value.height);
    writeValue(writer, value.moveSpeed);
    writeValue(writer, value.armorClass);
    writeValue(writer, value.immobile);
    writeValue(writer, value.attack1DamageDiceRolls);
    writeValue(writer, value.attack1DamageDiceSides);
    writeValue(writer, value.attack1DamageBonus);
    writeValue(writer, value.attack2DamageDiceRolls);
    writeValue(writer, value.attack2DamageDiceSides);
    writeValue(writer, value.attack2DamageBonus);
    writeValue(writer, value.spell1SkillLevel);
    writeValue(writer, value.spell1SkillMastery);
    writeValue(writer, value.spell2SkillLevel);
    writeValue(writer, value.spell2SkillMastery);
    writeValue(writer, value.spriteFrameIndex);
    writeValue(writer, value.actionSpriteFrameIndices);
    writeValue(writer, value.useStaticSpriteFrame);
    writeValue(writer, value.hostileToParty);
    writeValue(writer, value.isDead);
    writeValue(writer, value.isInvisible);
    writeValue(writer, value.hasDetectedParty);
    writeValue(writer, value.aiState);
    writeValue(writer, value.animation);
    writeValue(writer, value.animationTimeTicks);
    writeValue(writer, value.recoverySeconds);
    writeValue(writer, value.attackAnimationSeconds);
    writeValue(writer, value.attackCooldownSeconds);
    writeValue(writer, value.idleDecisionSeconds);
    writeValue(writer, value.actionSeconds);
    writeValue(writer, value.moveDirectionX);
    writeValue(writer, value.moveDirectionY);
    writeValue(writer, value.velocityX);
    writeValue(writer, value.velocityY);
    writeValue(writer, value.velocityZ);
    writeValue(writer, value.yawRadians);
    writeValue(writer, value.slowRemainingSeconds);
    writeValue(writer, value.slowMoveMultiplier);
    writeValue(writer, value.slowRecoveryMultiplier);
    writeValue(writer, value.stunRemainingSeconds);
    writeValue(writer, value.paralyzeRemainingSeconds);
    writeValue(writer, value.fearRemainingSeconds);
    writeValue(writer, value.blindRemainingSeconds);
    writeValue(writer, value.controlRemainingSeconds);
    writeValue(writer, value.controlMode);
    writeValue(writer, value.shrinkRemainingSeconds);
    writeValue(writer, value.shrinkDamageMultiplier);
    writeValue(writer, value.shrinkArmorClassMultiplier);
    writeValue(writer, value.armorClassHalvedRemainingSeconds);
    writeValue(writer, value.darkGraspRemainingSeconds);
    writeValue(writer, value.idleDecisionCount);
    writeValue(writer, value.pursueDecisionCount);
    writeValue(writer, value.attackDecisionCount);
    writeValue(writer, value.attackImpactTriggered);
    writeValue(writer, value.queuedAttackAbility);
    writeValue(writer, value.movementState);
    writeValue(writer, value.movementStateInitialized);
    writeValue(writer, value.npcId);
    writeValue(writer, value.aiType);
    writeValue(writer, value.canFly);
    writeValue(writer, value.attack1DamageType);
    writeValue(writer, value.attack2DamageType);
    writeValue(writer, value.spell1Id);
    writeValue(writer, value.spell1DamageType);
    writeValue(writer, value.spell1CastSupported);
    writeValue(writer, value.spell2Id);
    writeValue(writer, value.spell2DamageType);
    writeValue(writer, value.spell2CastSupported);
    writeValue(writer, value.wanderRadius);
    writeValue(writer, value.generatedAttack2);
    writeValue(writer, value.generatedAttack2IsRanged);
    writeValue(writer, value.copyAttack1DamageToAttack2);
    writeValue(writer, value.generatedAttack2MissileType);
    writeValue(writer, value.generatedAttack2Chance);
    writeValue(writer, value.generatedSpell1UseChance);
    writeValue(writer, value.generatedSpell2UseChance);
    writeValue(writer, value.alertStatusBit);
    writeValue(writer, value.bloodSplatSpawned);
    writeValue(writer, value.dayOfProtectionRemainingSeconds);
    writeValue(writer, value.dayOfProtectionPower);
    writeValue(writer, value.hourOfPowerRemainingSeconds);
    writeValue(writer, value.hourOfPowerPower);
    writeValue(writer, value.painReflectionRemainingSeconds);
    writeValue(writer, value.hammerhandsRemainingSeconds);
    writeValue(writer, value.hammerhandsPower);
    writeValue(writer, value.hasteRemainingSeconds);
    writeValue(writer, value.shieldRemainingSeconds);
    writeValue(writer, value.stoneskinRemainingSeconds);
    writeValue(writer, value.stoneskinPower);
    writeValue(writer, value.blessRemainingSeconds);
    writeValue(writer, value.blessPower);
    writeValue(writer, value.fateRemainingSeconds);
    writeValue(writer, value.fatePower);
    writeValue(writer, value.heroismRemainingSeconds);
    writeValue(writer, value.heroismPower);
    writeValue(writer, value.crowdSideLockRemainingSeconds);
    writeValue(writer, value.crowdNoProgressSeconds);
    writeValue(writer, value.crowdLastEdgeDistance);
    writeValue(writer, value.crowdRetreatRemainingSeconds);
    writeValue(writer, value.crowdStandRemainingSeconds);
    writeValue(writer, value.crowdProbeX);
    writeValue(writer, value.crowdProbeY);
    writeValue(writer, value.crowdProbeEdgeDistance);
    writeValue(writer, value.crowdProbeElapsedSeconds);
    writeValue(writer, value.crowdEscapeAttempts);
    writeValue(writer, value.crowdSideSign);
    writeValue(writer, value.suppressLowHealthFlee);
    writeValue(writer, value.mm9RudeId);
    writeValue(writer, value.usesMm9ActorRules);
    writeValue(writer, value.canReceiveDamage);
    writeValue(writer, value.mm9Civilian);
    writeValue(writer, value.mm9Guard);
    writeValue(writer, value.mm9FleeingFromParty);
    writeValue(writer, value.mm9FleeRemainingSeconds);
    writeValue(writer, value.mm9HelpCooldownSeconds);
    writeValue(writer, value.mm9PlayerHitCount);
    writeValue(writer, value.proceduralDeathLoot);
    writeValue(writer, value.rulesetFacts);
    writeValue(writer, value.summonerMemberIndex);
    writeValue(writer, value.provokedByParty);
    writeValue(writer, value.dormant);
    writeValue(writer, value.angeredByParty);
    writeValue(writer, value.nearby);
    writeValue(writer, value.mm9Ai);
    writeValue(writer, value.drawScale);
    writeValue(writer, value.patrolPoints);
    writeValue(writer, value.heldItems);
}

// Versions 133-168 saved the reach of a far hit after provokedByParty; it is read and dropped.
bool skipProvokedAttackReach(BinaryReader &reader)
{
    float provokedAttackReach = 0.0f;
    return reader.version() < SaveVersionOutdoorProvokedAttackReach
        || reader.version() >= SaveVersionNoProvokedAttackReach
        || readValue(reader, provokedAttackReach);
}

bool readValue(BinaryReader &reader, OutdoorWorldRuntime::MapActorState &value)
{
    return readValue(reader, value.actorId)
        && readValue(reader, value.monsterId)
        && readValue(reader, value.displayName)
        && readValue(reader, value.uniqueNameId)
        && readValue(reader, value.spawnedAtRuntime)
        && readValue(reader, value.fromSpawnPoint)
        && readValue(reader, value.spawnPointIndex)
        && readValue(reader, value.group)
        && readValue(reader, value.ally)
        && readValue(reader, value.hostilityType)
        && readValue(reader, value.specialItemId)
        && readValue(reader, value.currentHp)
        && readValue(reader, value.maxHp)
        && (reader.version() < SaveVersionMonsterBolsterRewards || readValue(reader, value.bolsterRewardMultiplier))
        && readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.z)
        && readValue(reader, value.preciseX)
        && readValue(reader, value.preciseY)
        && readValue(reader, value.preciseZ)
        && readValue(reader, value.homeX)
        && readValue(reader, value.homeY)
        && readValue(reader, value.homeZ)
        && readValue(reader, value.homePreciseX)
        && readValue(reader, value.homePreciseY)
        && readValue(reader, value.homePreciseZ)
        && readValue(reader, value.radius)
        && readValue(reader, value.height)
        && readValue(reader, value.moveSpeed)
        && (reader.version() < SaveVersionOutdoorActorBolsterCache
            || (readValue(reader, value.armorClass)
                && readValue(reader, value.immobile)
                && (reader.version() < SaveVersionMonsterBolsterDamageDice
                    || (readValue(reader, value.attack1DamageDiceRolls)
                        && readValue(reader, value.attack1DamageDiceSides)))
                && readValue(reader, value.attack1DamageBonus)
                && (reader.version() < SaveVersionMonsterBolsterDamageDice
                    || (readValue(reader, value.attack2DamageDiceRolls)
                        && readValue(reader, value.attack2DamageDiceSides)))
                && readValue(reader, value.attack2DamageBonus)
                && readValue(reader, value.spell1SkillLevel)
                && readValue(reader, value.spell1SkillMastery)
                && readValue(reader, value.spell2SkillLevel)
                && readValue(reader, value.spell2SkillMastery)))
        && readValue(reader, value.spriteFrameIndex)
        && readValue(reader, value.actionSpriteFrameIndices)
        && readValue(reader, value.useStaticSpriteFrame)
        && readValue(reader, value.hostileToParty)
        && readValue(reader, value.isDead)
        && readValue(reader, value.isInvisible)
        && readValue(reader, value.hasDetectedParty)
        && readValue(reader, value.aiState)
        && readValue(reader, value.animation)
        && readValue(reader, value.animationTimeTicks)
        && readValue(reader, value.recoverySeconds)
        && readValue(reader, value.attackAnimationSeconds)
        && readValue(reader, value.attackCooldownSeconds)
        && readValue(reader, value.idleDecisionSeconds)
        && readValue(reader, value.actionSeconds)
        && readValue(reader, value.moveDirectionX)
        && readValue(reader, value.moveDirectionY)
        && readValue(reader, value.velocityX)
        && readValue(reader, value.velocityY)
        && readValue(reader, value.velocityZ)
        && readValue(reader, value.yawRadians)
        && readValue(reader, value.slowRemainingSeconds)
        && readValue(reader, value.slowMoveMultiplier)
        && readValue(reader, value.slowRecoveryMultiplier)
        && readValue(reader, value.stunRemainingSeconds)
        && readValue(reader, value.paralyzeRemainingSeconds)
        && readValue(reader, value.fearRemainingSeconds)
        && readValue(reader, value.blindRemainingSeconds)
        && readValue(reader, value.controlRemainingSeconds)
        && readValue(reader, value.controlMode)
        && readValue(reader, value.shrinkRemainingSeconds)
        && readValue(reader, value.shrinkDamageMultiplier)
        && readValue(reader, value.shrinkArmorClassMultiplier)
        && (reader.version() < SaveVersionCombatEffectState
            || readValue(reader, value.armorClassHalvedRemainingSeconds))
        && readValue(reader, value.darkGraspRemainingSeconds)
        && readValue(reader, value.idleDecisionCount)
        && readValue(reader, value.pursueDecisionCount)
        && readValue(reader, value.attackDecisionCount)
        && readValue(reader, value.attackImpactTriggered)
        && readValue(reader, value.queuedAttackAbility)
        && readValue(reader, value.movementState)
        && readValue(reader, value.movementStateInitialized)
        && (reader.version() < SaveVersionOutdoorRuntimeSaveParity
            || (readValue(reader, value.npcId)
                && readValue(reader, value.aiType)
                && readValue(reader, value.canFly)
                && readValue(reader, value.attack1DamageType)
                && readValue(reader, value.attack2DamageType)
                && readValue(reader, value.spell1Id)
                && readValue(reader, value.spell1DamageType)
                && readValue(reader, value.spell1CastSupported)
                && readValue(reader, value.spell2Id)
                && readValue(reader, value.spell2DamageType)
                && readValue(reader, value.spell2CastSupported)
                && readValue(reader, value.wanderRadius)
                && readValue(reader, value.generatedAttack2)
                && readValue(reader, value.generatedAttack2IsRanged)
                && readValue(reader, value.copyAttack1DamageToAttack2)
                && readValue(reader, value.generatedAttack2MissileType)
                && readValue(reader, value.generatedAttack2Chance)
                && readValue(reader, value.generatedSpell1UseChance)
                && readValue(reader, value.generatedSpell2UseChance)
                && readValue(reader, value.alertStatusBit)
                && readValue(reader, value.bloodSplatSpawned)
                && readValue(reader, value.dayOfProtectionRemainingSeconds)
                && readValue(reader, value.dayOfProtectionPower)
                && readValue(reader, value.hourOfPowerRemainingSeconds)
                && readValue(reader, value.hourOfPowerPower)
                && readValue(reader, value.painReflectionRemainingSeconds)
                && readValue(reader, value.hammerhandsRemainingSeconds)
                && readValue(reader, value.hammerhandsPower)
                && readValue(reader, value.hasteRemainingSeconds)
                && readValue(reader, value.shieldRemainingSeconds)
                && readValue(reader, value.stoneskinRemainingSeconds)
                && readValue(reader, value.stoneskinPower)
                && readValue(reader, value.blessRemainingSeconds)
                && readValue(reader, value.blessPower)
                && readValue(reader, value.fateRemainingSeconds)
                && readValue(reader, value.fatePower)
                && readValue(reader, value.heroismRemainingSeconds)
                && readValue(reader, value.heroismPower)
                && readValue(reader, value.crowdSideLockRemainingSeconds)
                && readValue(reader, value.crowdNoProgressSeconds)
                && readValue(reader, value.crowdLastEdgeDistance)
                && readValue(reader, value.crowdRetreatRemainingSeconds)
                && readValue(reader, value.crowdStandRemainingSeconds)
                && readValue(reader, value.crowdProbeX)
                && readValue(reader, value.crowdProbeY)
                && readValue(reader, value.crowdProbeEdgeDistance)
                && readValue(reader, value.crowdProbeElapsedSeconds)
                && readValue(reader, value.crowdEscapeAttempts)
                && readValue(reader, value.crowdSideSign)
                && readValue(reader, value.suppressLowHealthFlee)))
        && (reader.version() < SaveVersionMm9DialogueActors || readValue(reader, value.mm9RudeId))
        && (reader.version() < SaveVersionMm9ActorReactions
            || (readValue(reader, value.usesMm9ActorRules)
                && readValue(reader, value.canReceiveDamage)
                && readValue(reader, value.mm9Civilian)
                && readValue(reader, value.mm9Guard)
                && readValue(reader, value.mm9FleeingFromParty)
                && readValue(reader, value.mm9FleeRemainingSeconds)
                && readValue(reader, value.mm9HelpCooldownSeconds)
                && readValue(reader, value.mm9PlayerHitCount)))
        && (reader.version() < SaveVersionActorProceduralDeathLoot
            || readValue(reader, value.proceduralDeathLoot))
        && (reader.version() < SaveVersionActorRulesetFacts || readValue(reader, value.rulesetFacts))
        && (reader.version() < SaveVersionActorSummoner || readValue(reader, value.summonerMemberIndex))
        && (reader.version() < SaveVersionOutdoorProvokedActors || readValue(reader, value.provokedByParty))
        && skipProvokedAttackReach(reader)
        && (reader.version() < SaveVersionActorDormant || readValue(reader, value.dormant))
        && (reader.version() < SaveVersionActorAngeredByParty || readValue(reader, value.angeredByParty))
        && (reader.version() < SaveVersionOutdoorNearby || readValue(reader, value.nearby))
        && (reader.version() < SaveVersionOutdoorSpawnMm9AiPlacement || readValue(reader, value.mm9Ai))
        && (reader.version() < SaveVersionActorDrawScale || readValue(reader, value.drawScale))
        && (reader.version() < SaveVersionOutdoorSpawnPatrol || readValue(reader, value.patrolPoints))
        && (reader.version() < SaveVersionActorHeldItems || readValue(reader, value.heldItems));
}

void writeValue(BinaryWriter &writer, const OutdoorWorldRuntime::ChestItemState &value)
{
    writeValue(writer, value.item);
    writeValue(writer, value.itemId);
    writeValue(writer, value.quantity);
    writeValue(writer, value.goldAmount);
    writeValue(writer, value.goldRollCount);
    writeValue(writer, value.isGold);
    writeValue(writer, value.width);
    writeValue(writer, value.height);
    writeValue(writer, value.gridX);
    writeValue(writer, value.gridY);
}

bool readValue(BinaryReader &reader, OutdoorWorldRuntime::ChestItemState &value)
{
    return readValue(reader, value.item)
        && readValue(reader, value.itemId)
        && readValue(reader, value.quantity)
        && readValue(reader, value.goldAmount)
        && readValue(reader, value.goldRollCount)
        && readValue(reader, value.isGold)
        && readValue(reader, value.width)
        && readValue(reader, value.height)
        && readValue(reader, value.gridX)
        && readValue(reader, value.gridY);
}

void writeValue(BinaryWriter &writer, const OutdoorWorldRuntime::ChestViewState &value)
{
    writeValue(writer, value.chestId);
    writeValue(writer, value.chestTypeId);
    writeValue(writer, value.flags);
    writeValue(writer, value.gridWidth);
    writeValue(writer, value.gridHeight);
    writeValue(writer, value.items);
    writeValue(writer, value.hiddenItems);
}

bool readValue(BinaryReader &reader, OutdoorWorldRuntime::ChestViewState &value)
{
    return readValue(reader, value.chestId)
        && readValue(reader, value.chestTypeId)
        && readValue(reader, value.flags)
        && readValue(reader, value.gridWidth)
        && readValue(reader, value.gridHeight)
        && readValue(reader, value.items)
        && readValue(reader, value.hiddenItems);
}

void writeValue(BinaryWriter &writer, const OutdoorWorldRuntime::CorpseViewState &value)
{
    writeValue(writer, value.fromSummonedMonster);
    writeValue(writer, value.sourceIndex);
    writeValue(writer, value.title);
    writeValue(writer, value.items);
}

bool readValue(BinaryReader &reader, OutdoorWorldRuntime::CorpseViewState &value)
{
    return readValue(reader, value.fromSummonedMonster)
        && readValue(reader, value.sourceIndex)
        && readValue(reader, value.title)
        && readValue(reader, value.items);
}

void writeValue(BinaryWriter &writer, const OutdoorWorldRuntime::WorldItemState &value)
{
    writeValue(writer, value.worldItemId);
    writeValue(writer, value.item);
    writeValue(writer, value.goldAmount);
    writeValue(writer, value.isGold);
    writeValue(writer, value.objectDescriptionId);
    writeValue(writer, value.objectSpriteId);
    writeValue(writer, value.objectSpriteFrameIndex);
    writeValue(writer, value.objectFlags);
    writeValue(writer, value.radius);
    writeValue(writer, value.height);
    writeValue(writer, value.soundId);
    writeValue(writer, value.attributes);
    writeValue(writer, value.sectorId);
    writeValue(writer, value.objectName);
    writeValue(writer, value.objectSpriteName);
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.z);
    writeValue(writer, value.velocityX);
    writeValue(writer, value.velocityY);
    writeValue(writer, value.velocityZ);
    writeValue(writer, value.initialX);
    writeValue(writer, value.initialY);
    writeValue(writer, value.initialZ);
    writeValue(writer, value.timeSinceCreatedTicks);
    writeValue(writer, value.lifetimeTicks);
    writeValue(writer, value.spawnedByPlayer);
    writeValue(writer, value.isExpired);
    writeValue(writer, value.semanticSourceId);
    writeValue(writer, value.semanticPlacedPickup);
    writeValue(writer, value.semanticLootContainerId);
    writeValue(writer, value.semanticLootContainer);
}

bool readValue(BinaryReader &reader, OutdoorWorldRuntime::WorldItemState &value)
{
    return readValue(reader, value.worldItemId)
        && readValue(reader, value.item)
        && readValue(reader, value.goldAmount)
        && readValue(reader, value.isGold)
        && readValue(reader, value.objectDescriptionId)
        && readValue(reader, value.objectSpriteId)
        && readValue(reader, value.objectSpriteFrameIndex)
        && readValue(reader, value.objectFlags)
        && readValue(reader, value.radius)
        && readValue(reader, value.height)
        && readValue(reader, value.soundId)
        && readValue(reader, value.attributes)
        && readValue(reader, value.sectorId)
        && readValue(reader, value.objectName)
        && readValue(reader, value.objectSpriteName)
        && readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.z)
        && readValue(reader, value.velocityX)
        && readValue(reader, value.velocityY)
        && readValue(reader, value.velocityZ)
        && readValue(reader, value.initialX)
        && readValue(reader, value.initialY)
        && readValue(reader, value.initialZ)
        && readValue(reader, value.timeSinceCreatedTicks)
        && readValue(reader, value.lifetimeTicks)
        && readValue(reader, value.spawnedByPlayer)
        && readValue(reader, value.isExpired)
        && (reader.version() < SaveVersionMm9SemanticWorldItems
            || (readValue(reader, value.semanticSourceId)
                && readValue(reader, value.semanticPlacedPickup)
                && readValue(reader, value.semanticLootContainerId)
                && readValue(reader, value.semanticLootContainer)));
}

void writeValue(BinaryWriter &writer, const ArmageddonState &value)
{
    writeValue(writer, value.remainingSeconds);
    writeValue(writer, value.skillLevel);
    writeValue(writer, value.skillMastery);
    writeValue(writer, value.casterMemberIndex);
    writeValue(writer, value.shakeStepsRemaining);
    writeValue(writer, value.shakeSequence);
    writeValue(writer, value.cameraShakeYawRadians);
    writeValue(writer, value.cameraShakePitchRadians);
}

bool readValue(BinaryReader &reader, ArmageddonState &value)
{
    return readValue(reader, value.remainingSeconds)
        && readValue(reader, value.skillLevel)
        && readValue(reader, value.skillMastery)
        && readValue(reader, value.casterMemberIndex)
        && readValue(reader, value.shakeStepsRemaining)
        && readValue(reader, value.shakeSequence)
        && readValue(reader, value.cameraShakeYawRadians)
        && readValue(reader, value.cameraShakePitchRadians);
}

void writeValue(BinaryWriter &writer, const GameplayProjectileService::ProjectileState &value)
{
    writeValue(writer, value.projectileId);
    writeValue(writer, value.sourceKind);
    writeValue(writer, value.sourceId);
    writeValue(writer, value.sourcePartyMemberIndex);
    writeValue(writer, value.sourceMonsterId);
    writeValue(writer, value.fromSummonedMonster);
    writeValue(writer, value.ability);
    writeValue(writer, value.objectDescriptionId);
    writeValue(writer, value.objectSpriteId);
    writeValue(writer, value.objectSpriteFrameIndex);
    writeValue(writer, value.impactObjectDescriptionId);
    writeValue(writer, value.objectFlags);
    writeValue(writer, value.visualMode);
    writeValue(writer, value.radius);
    writeValue(writer, value.height);
    writeValue(writer, value.spellId);
    writeValue(writer, value.effectSoundId);
    writeValue(writer, value.impactSoundIdOverride);
    writeValue(writer, value.skillLevel);
    writeValue(writer, value.skillMastery);
    writeValue(writer, value.objectName);
    writeValue(writer, value.objectSpriteName);
    writeValue(writer, value.sourceX);
    writeValue(writer, value.sourceY);
    writeValue(writer, value.sourceZ);
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.z);
    writeValue(writer, value.velocityX);
    writeValue(writer, value.velocityY);
    writeValue(writer, value.velocityZ);
    writeValue(writer, value.damage);
    writeValue(writer, value.attackBonus);
    writeValue(writer, value.damageType);
    writeValue(writer, value.useActorHitChance);
    writeValue(writer, value.timeSinceCreatedTicks);
    writeValue(writer, value.lifetimeTickAccumulator);
    writeValue(writer, value.lifetimeTicks);
    writeValue(writer, value.sectorId);
    writeValue(writer, value.isSettled);
    writeValue(writer, value.isExpired);
    writeValue(writer, value.shieldTier);
    writeValue(writer, value.explosionRadius);
    writeValue(writer, value.eventMissile);
    writeValue(writer, value.targetX);
    writeValue(writer, value.targetY);
    writeValue(writer, value.targetZ);
    writeValue(writer, value.homing.has_value());
    if (value.homing)
    {
        const GameplayProjectileService::ProjectileHoming &homing = *value.homing;
        writeValue(writer, homing.targetKind);
        writeValue(writer, static_cast<uint64_t>(homing.targetActorIndex));
        writeValue(writer, homing.targetActorId);
        writeValue(writer, homing.turnRadiansPerSecond);
        writeValue(writer, homing.maxSeconds);
        writeValue(writer, homing.expireAfter);
        writeValue(writer, homing.speed);
        writeValue(writer, homing.elapsedSeconds);
        writeValue(writer, homing.lost);
        writeValue(writer, homing.lockRadiansPerSecond);
    }
}

// A homing missile keeps its target across a save (save version 135), with its shield tier, its explosion radius
// and an event missile's burst point.
bool readProjectileHoming(BinaryReader &reader, GameplayProjectileService::ProjectileState &value)
{
    bool hasHoming = false;
    if (!readValue(reader, value.shieldTier)
        || !readValue(reader, value.explosionRadius)
        || !readValue(reader, value.eventMissile)
        || !readValue(reader, value.targetX)
        || !readValue(reader, value.targetY)
        || !readValue(reader, value.targetZ)
        || !readValue(reader, hasHoming))
    {
        return false;
    }
    if (!hasHoming)
    {
        return true;
    }
    GameplayProjectileService::ProjectileHoming homing = {};
    uint64_t targetActorIndex = 0;
    if (!readValue(reader, homing.targetKind)
        || !readValue(reader, targetActorIndex)
        || !readValue(reader, homing.targetActorId)
        || !readValue(reader, homing.turnRadiansPerSecond)
        || !readValue(reader, homing.maxSeconds)
        || !readValue(reader, homing.expireAfter)
        || !readValue(reader, homing.speed)
        || !readValue(reader, homing.elapsedSeconds)
        || !readValue(reader, homing.lost)
        || !readValue(reader, homing.lockRadiansPerSecond))
    {
        return false;
    }
    homing.targetActorIndex = static_cast<size_t>(targetActorIndex);

    // An older save holds the lock cone of one 1/60 s projectile step: the same lock as a rate.
    if (reader.version() < SaveVersionHomingLockRate)
    {
        homing.lockRadiansPerSecond *= 60.0f;
    }

    value.homing = homing;
    return true;
}

bool readValue(BinaryReader &reader, GameplayProjectileService::ProjectileState &value)
{
    return readValue(reader, value.projectileId)
        && readValue(reader, value.sourceKind)
        && readValue(reader, value.sourceId)
        && readValue(reader, value.sourcePartyMemberIndex)
        && readValue(reader, value.sourceMonsterId)
        && readValue(reader, value.fromSummonedMonster)
        && readValue(reader, value.ability)
        && readValue(reader, value.objectDescriptionId)
        && readValue(reader, value.objectSpriteId)
        && readValue(reader, value.objectSpriteFrameIndex)
        && readValue(reader, value.impactObjectDescriptionId)
        && readValue(reader, value.objectFlags)
        && (reader.version() < SaveVersionProjectileVisualMode || readValue(reader, value.visualMode))
        && readValue(reader, value.radius)
        && readValue(reader, value.height)
        && readValue(reader, value.spellId)
        && readValue(reader, value.effectSoundId)
        && (reader.version() < SaveVersionFullProjectileState || readValue(reader, value.impactSoundIdOverride))
        && readValue(reader, value.skillLevel)
        && readValue(reader, value.skillMastery)
        && readValue(reader, value.objectName)
        && readValue(reader, value.objectSpriteName)
        && readValue(reader, value.sourceX)
        && readValue(reader, value.sourceY)
        && readValue(reader, value.sourceZ)
        && readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.z)
        && readValue(reader, value.velocityX)
        && readValue(reader, value.velocityY)
        && readValue(reader, value.velocityZ)
        && readValue(reader, value.damage)
        && readValue(reader, value.attackBonus)
        && (reader.version() < SaveVersionFullProjectileState || readValue(reader, value.damageType))
        && readValue(reader, value.useActorHitChance)
        && readValue(reader, value.timeSinceCreatedTicks)
        && (reader.version() < SaveVersionFullProjectileState || readValue(reader, value.lifetimeTickAccumulator))
        && readValue(reader, value.lifetimeTicks)
        && (reader.version() < SaveVersionFullProjectileState || readValue(reader, value.sectorId))
        && (reader.version() < SaveVersionFullProjectileState || readValue(reader, value.isSettled))
        && readValue(reader, value.isExpired)
        && (reader.version() < SaveVersionProjectileHoming || readProjectileHoming(reader, value));
}

void writeValue(BinaryWriter &writer, const GameplayProjectileService::ProjectileImpactState &value)
{
    writeValue(writer, value.effectId);
    writeValue(writer, value.objectDescriptionId);
    writeValue(writer, value.objectSpriteId);
    writeValue(writer, value.objectSpriteFrameIndex);
    writeValue(writer, value.sourceObjectFlags);
    writeValue(writer, value.sourceSpellId);
    writeValue(writer, value.objectName);
    writeValue(writer, value.objectSpriteName);
    writeValue(writer, value.sourceObjectName);
    writeValue(writer, value.sourceObjectSpriteName);
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.z);
    writeValue(writer, value.timeSinceCreatedTicks);
    writeValue(writer, value.lifetimeTickAccumulator);
    writeValue(writer, value.lifetimeTicks);
    writeValue(writer, value.sectorId);
    writeValue(writer, value.freezeAnimation);
    writeValue(writer, value.isExpired);
}

bool readValue(BinaryReader &reader, GameplayProjectileService::ProjectileImpactState &value)
{
    return readValue(reader, value.effectId)
        && readValue(reader, value.objectDescriptionId)
        && readValue(reader, value.objectSpriteId)
        && readValue(reader, value.objectSpriteFrameIndex)
        && (reader.version() < SaveVersionFullProjectileState || readValue(reader, value.sourceObjectFlags))
        && (reader.version() < SaveVersionFullProjectileState || readValue(reader, value.sourceSpellId))
        && readValue(reader, value.objectName)
        && readValue(reader, value.objectSpriteName)
        && (reader.version() < SaveVersionFullProjectileState || readValue(reader, value.sourceObjectName))
        && (reader.version() < SaveVersionFullProjectileState || readValue(reader, value.sourceObjectSpriteName))
        && readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.z)
        && readValue(reader, value.timeSinceCreatedTicks)
        && (reader.version() < SaveVersionFullProjectileState || readValue(reader, value.lifetimeTickAccumulator))
        && readValue(reader, value.lifetimeTicks)
        && (reader.version() < SaveVersionFullProjectileState || readValue(reader, value.sectorId))
        && (reader.version() < SaveVersionFullProjectileState || readValue(reader, value.freezeAnimation))
        && readValue(reader, value.isExpired);
}

void writeValue(BinaryWriter &writer, const OutdoorWorldRuntime::FireSpikeTrapState &value)
{
    writeValue(writer, value.trapId);
    writeValue(writer, value.sourceKind);
    writeValue(writer, value.sourceId);
    writeValue(writer, value.sourcePartyMemberIndex);
    writeValue(writer, value.sourceMonsterId);
    writeValue(writer, value.fromSummonedMonster);
    writeValue(writer, value.ability);
    writeValue(writer, value.objectDescriptionId);
    writeValue(writer, value.objectSpriteId);
    writeValue(writer, value.objectSpriteFrameIndex);
    writeValue(writer, value.impactObjectDescriptionId);
    writeValue(writer, value.objectFlags);
    writeValue(writer, value.radius);
    writeValue(writer, value.height);
    writeValue(writer, value.spellId);
    writeValue(writer, value.effectSoundId);
    writeValue(writer, value.skillLevel);
    writeValue(writer, value.skillMastery);
    writeValue(writer, value.objectName);
    writeValue(writer, value.objectSpriteName);
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.z);
    writeValue(writer, value.timeSinceCreatedTicks);
    writeValue(writer, value.isExpired);
}

bool readValue(BinaryReader &reader, OutdoorWorldRuntime::FireSpikeTrapState &value)
{
    return readValue(reader, value.trapId)
        && readValue(reader, value.sourceKind)
        && readValue(reader, value.sourceId)
        && readValue(reader, value.sourcePartyMemberIndex)
        && readValue(reader, value.sourceMonsterId)
        && readValue(reader, value.fromSummonedMonster)
        && readValue(reader, value.ability)
        && readValue(reader, value.objectDescriptionId)
        && readValue(reader, value.objectSpriteId)
        && readValue(reader, value.objectSpriteFrameIndex)
        && readValue(reader, value.impactObjectDescriptionId)
        && readValue(reader, value.objectFlags)
        && readValue(reader, value.radius)
        && readValue(reader, value.height)
        && readValue(reader, value.spellId)
        && readValue(reader, value.effectSoundId)
        && readValue(reader, value.skillLevel)
        && readValue(reader, value.skillMastery)
        && readValue(reader, value.objectName)
        && readValue(reader, value.objectSpriteName)
        && readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.z)
        && readValue(reader, value.timeSinceCreatedTicks)
        && readValue(reader, value.isExpired);
}

void writeValue(BinaryWriter &writer, const IndoorWorldRuntime::FireSpikeTrapState &value)
{
    writeValue(writer, value.trapId);
    writeValue(writer, value.sourceKind);
    writeValue(writer, value.sourceId);
    writeValue(writer, value.sourcePartyMemberIndex);
    writeValue(writer, value.sourceMonsterId);
    writeValue(writer, value.fromSummonedMonster);
    writeValue(writer, value.ability);
    writeValue(writer, value.objectDescriptionId);
    writeValue(writer, value.objectSpriteId);
    writeValue(writer, value.objectSpriteFrameIndex);
    writeValue(writer, value.impactObjectDescriptionId);
    writeValue(writer, value.objectFlags);
    writeValue(writer, value.radius);
    writeValue(writer, value.height);
    writeValue(writer, value.spellId);
    writeValue(writer, value.effectSoundId);
    writeValue(writer, value.skillLevel);
    writeValue(writer, value.skillMastery);
    writeValue(writer, value.objectName);
    writeValue(writer, value.objectSpriteName);
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.z);
    writeValue(writer, value.sectorId);
    writeValue(writer, value.timeSinceCreatedTicks);
    writeValue(writer, value.isExpired);
}

bool readValue(BinaryReader &reader, IndoorWorldRuntime::FireSpikeTrapState &value)
{
    return readValue(reader, value.trapId)
        && readValue(reader, value.sourceKind)
        && readValue(reader, value.sourceId)
        && readValue(reader, value.sourcePartyMemberIndex)
        && readValue(reader, value.sourceMonsterId)
        && readValue(reader, value.fromSummonedMonster)
        && readValue(reader, value.ability)
        && readValue(reader, value.objectDescriptionId)
        && readValue(reader, value.objectSpriteId)
        && readValue(reader, value.objectSpriteFrameIndex)
        && readValue(reader, value.impactObjectDescriptionId)
        && readValue(reader, value.objectFlags)
        && readValue(reader, value.radius)
        && readValue(reader, value.height)
        && readValue(reader, value.spellId)
        && readValue(reader, value.effectSoundId)
        && readValue(reader, value.skillLevel)
        && readValue(reader, value.skillMastery)
        && readValue(reader, value.objectName)
        && readValue(reader, value.objectSpriteName)
        && readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.z)
        && readValue(reader, value.sectorId)
        && readValue(reader, value.timeSinceCreatedTicks)
        && readValue(reader, value.isExpired);
}

void writeValue(BinaryWriter &writer, const GameplayProjectileService::Snapshot &value)
{
    writeValue(writer, value.nextProjectileId);
    writeValue(writer, value.nextProjectileImpactId);
    writeValue(writer, value.nextFireSpikeTrapId);
    writeValue(writer, value.projectiles);
    writeValue(writer, value.projectileImpacts);
}

bool readValue(BinaryReader &reader, GameplayProjectileService::Snapshot &value)
{
    return readValue(reader, value.nextProjectileId)
        && readValue(reader, value.nextProjectileImpactId)
        && (reader.version() < SaveVersionFullProjectileState || readValue(reader, value.nextFireSpikeTrapId))
        && readValue(reader, value.projectiles)
        && readValue(reader, value.projectileImpacts);
}

// Saves before SaveVersionWeatherModel stored a debug rain-intensity override (flag and preset byte); the weather
// model replaces it, so older saves read and drop it.
bool skipRetiredRainIntensityOverride(BinaryReader &reader)
{
    bool hasOverride = false;
    uint8_t preset = 0;
    return readValue(reader, hasOverride) && readValue(reader, preset);
}

void writeValue(BinaryWriter &writer, const OutdoorWorldRuntime::AtmosphereState &value)
{
    writeValue(writer, value.sourceSkyTextureName);
    writeValue(writer, value.skyTextureName);
    writeValue(writer, value.weatherFlags);
    writeValue(writer, value.fogWeakDistance);
    writeValue(writer, value.fogStrongDistance);
    writeValue(writer, value.redFog);
    writeValue(writer, value.isNight);
    writeValue(writer, value.fogDensity);
    writeValue(writer, value.ambientBrightness);
    writeValue(writer, value.visibilityDistance);
    writeValue(writer, value.darknessOverlayAlpha);
    writeValue(writer, value.darknessOverlayColorAbgr);
    writeValue(writer, value.sunDirectionX);
    writeValue(writer, value.sunDirectionY);
    writeValue(writer, value.sunDirectionZ);
    writeValue(writer, value.clearColorAbgr);
}

bool readValue(BinaryReader &reader, OutdoorWorldRuntime::AtmosphereState &value)
{
    return readValue(reader, value.sourceSkyTextureName)
        && readValue(reader, value.skyTextureName)
        && readValue(reader, value.weatherFlags)
        && readValue(reader, value.fogWeakDistance)
        && readValue(reader, value.fogStrongDistance)
        && readValue(reader, value.redFog)
        && readValue(reader, value.isNight)
        && readValue(reader, value.fogDensity)
        && readValue(reader, value.ambientBrightness)
        && readValue(reader, value.visibilityDistance)
        && readValue(reader, value.darknessOverlayAlpha)
        && readValue(reader, value.darknessOverlayColorAbgr)
        && readValue(reader, value.sunDirectionX)
        && readValue(reader, value.sunDirectionY)
        && readValue(reader, value.sunDirectionZ)
        && readValue(reader, value.clearColorAbgr);
}

void writeValue(BinaryWriter &writer, const OutdoorWorldRuntime::Snapshot &value)
{
    writeValue(writer, value.gameMinutes);
    writeValue(writer, value.locationInfo);
    writeValue(writer, value.locationTime);
    writeValue(writer, value.hasLocationTime);
    writeValue(writer, value.atmosphere);
    writeValue(writer, value.timers);
    writeValue(writer, value.mapActors);
    writeValue(writer, value.chests);
    writeValue(writer, value.openedChestFlags);
    writeValue(writer, value.materializedChestViews);
    writeValue(writer, value.activeChestView);
    writeValue(writer, value.eventRuntimeState);
    writeValue(writer, value.actorUpdateAccumulatorSeconds);
    writeValue(writer, value.sessionChestSeed);
    writeValue(writer, value.nextActorId);
    writeValue(writer, value.mapActorCorpseViews);
    writeValue(writer, value.activeCorpseView);
    writeValue(writer, value.worldItems);
    writeValue(writer, value.nextWorldItemId);
    writeValue(writer, value.nextProjectileId);
    writeValue(writer, value.nextProjectileImpactId);
    writeValue(writer, value.nextFireSpikeTrapId);
    writeValue(writer, value.projectiles);
    writeValue(writer, value.projectileImpacts);
    writeValue(writer, value.fireSpikeTraps);
    writeValue(writer, value.fullyRevealedCells);
    writeValue(writer, value.partiallyRevealedCells);
    writeValue(writer, value.gameplayOverlayRemainingSeconds);
    writeValue(writer, value.gameplayOverlayDurationSeconds);
    writeValue(writer, value.gameplayOverlayPeakAlpha);
    writeValue(writer, value.gameplayOverlayColorAbgr);
    writeValue(writer, value.armageddon);
    writeValue(writer, value.bloodSplats);
    writeValue(writer, value.faceAttributes);
    writeValue(writer, value.searchedLootPropSourceIds);
    writeValue(writer, value.actorBehaviors);
    writeValue(writer, value.mapActorRevealedLoot);
    writeValue(writer, value.mapLayoutIdentity);
}

bool readValue(BinaryReader &reader, OutdoorWorldRuntime::Snapshot &value)
{
    const bool loaded = readValue(reader, value.gameMinutes)
        && (reader.version() < SaveVersionOutdoorLocationInfo || readValue(reader, value.locationInfo))
        && (reader.version() < SaveVersionLegacyEvtTimers || readValue(reader, value.locationTime))
        && (reader.version() < SaveVersionLegacyEvtTimers || readValue(reader, value.hasLocationTime))
        && readValue(reader, value.atmosphere)
        && readOutdoorTimerStates(reader, value.timers)
        && readValue(reader, value.mapActors)
        && readValue(reader, value.chests)
        && readValue(reader, value.openedChestFlags)
        && readValue(reader, value.materializedChestViews)
        && readValue(reader, value.activeChestView)
        && readValue(reader, value.eventRuntimeState)
        && readValue(reader, value.actorUpdateAccumulatorSeconds)
        && readValue(reader, value.sessionChestSeed)
        && readValue(reader, value.nextActorId)
        && readValue(reader, value.mapActorCorpseViews)
        && readValue(reader, value.activeCorpseView)
        && readValue(reader, value.worldItems)
        && readValue(reader, value.nextWorldItemId)
        && readValue(reader, value.nextProjectileId)
        && readValue(reader, value.nextProjectileImpactId)
        && (reader.version() < SaveVersionFullProjectileState || readValue(reader, value.nextFireSpikeTrapId))
        && readValue(reader, value.projectiles)
        && readValue(reader, value.projectileImpacts)
        && (reader.version() < SaveVersionFullProjectileState || readValue(reader, value.fireSpikeTraps))
        && (reader.version() < SaveVersionOutdoorJournalRevealMask
            || readValue(reader, value.fullyRevealedCells))
        && (reader.version() < SaveVersionOutdoorJournalRevealMask
            || readValue(reader, value.partiallyRevealedCells))
        && (reader.version() < SaveVersionOutdoorRuntimeSaveParity
            || (readValue(reader, value.gameplayOverlayRemainingSeconds)
                && readValue(reader, value.gameplayOverlayDurationSeconds)
                && readValue(reader, value.gameplayOverlayPeakAlpha)
                && readValue(reader, value.gameplayOverlayColorAbgr)
                && readValue(reader, value.armageddon)
                && (reader.version() >= SaveVersionWeatherModel || skipRetiredRainIntensityOverride(reader))
                && readValue(reader, value.bloodSplats)))
        && (reader.version() < SaveVersionOutdoorFaceAttributes
            || readValue(reader, value.faceAttributes))
        && (reader.version() < SaveVersionMm9ItemSourceState
            || readValue(reader, value.searchedLootPropSourceIds))
        && (reader.version() < SaveVersionActorBehaviors || readValue(reader, value.actorBehaviors))
        && (reader.version() < SaveVersionActorRevealedLoot || readValue(reader, value.mapActorRevealedLoot))
        && (reader.version() < SaveVersionMapLayoutIdentity || readValue(reader, value.mapLayoutIdentity));

    if (loaded && reader.version() >= SaveVersionOutdoorRuntimeSaveParity)
    {
        value.hasOutdoorRuntimeSaveParityFields = true;
    }

    return loaded;
}

void writeValue(BinaryWriter &writer, const IndoorSceneRuntime::Snapshot &value)
{
    writeValue(writer, value.mapDeltaData);
    writeValue(writer, value.eventRuntimeState);
    writeValue(writer, value.worldRuntime);
    writeValue(writer, value.partyRuntime);
    writeValue(writer, value.timers);
    writeValue(writer, value.lastProcessedPartyMoveStateForFaceTriggers);
    writeValue(writer, value.mechanismAccumulatorMilliseconds);
    writeValue(writer, value.mapLayoutIdentity);
}

bool readValue(BinaryReader &reader, IndoorSceneRuntime::Snapshot &value)
{
    return readValue(reader, value.mapDeltaData)
        && readValue(reader, value.eventRuntimeState)
        && (reader.version() < 20 || readValue(reader, value.worldRuntime))
        && (reader.version() < 20 || readValue(reader, value.partyRuntime))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readIndoorTimerStates(reader, value.timers))
        && (reader.version() < SaveVersionIndoorSaveLoadParity
            || readValue(reader, value.lastProcessedPartyMoveStateForFaceTriggers))
        && readValue(reader, value.mechanismAccumulatorMilliseconds)
        && (reader.version() < SaveVersionMapLayoutIdentity || readValue(reader, value.mapLayoutIdentity));
}

void writeValue(BinaryWriter &writer, const RulesetSelection &value)
{
    writeValue(writer, value.id);
    writeValue(writer, value.options.difficulty);
    writeValue(writer, value.options.progression);
    writeValue(writer, value.options.challengeMode);
    writeValue(writer, value.options.randomizer);
    writeValue(writer, value.options.preferences.homingProjectiles);
    writeValue(writer, value.options.preferences.friendlyFire);
    writeValue(writer, value.options.preferences.lootFilter.preset);
    writeValue(writer, value.options.preferences.lootFilter.goldKinds);
    writeValue(writer, value.options.preferences.lootFilter.leaveOnGround);
    writeValue(writer, value.options.preferences.disintegration);
    writeValue(writer, value.options.preferences.trainerHints);
    writeValue(writer, value.options.preferences.bowDisabled);
}

// The retired per-game loot choice of saves 172 to 177 (SaveVersionOtherWorldsLootRetired).
bool skipRetiredOtherWorldsLoot(BinaryReader &reader)
{
    if (reader.version() < SaveVersionOtherWorldsLoot || reader.version() >= SaveVersionOtherWorldsLootRetired)
    {
        return true;
    }

    bool retired = true;
    return readValue(reader, retired);
}

bool readLootFilter(BinaryReader &reader, RulesetLootFilter &filter)
{
    if (reader.version() >= SaveVersionLootFilterPresets)
    {
        return readValue(reader, filter.preset) && readValue(reader, filter.goldKinds)
            && readValue(reader, filter.leaveOnGround);
    }

    uint8_t legacyRarity = 0;

    if (!readValue(reader, legacyRarity))
    {
        return false;
    }

    filter = rulesetLootFilterFromLegacyRarity(legacyRarity);
    return true;
}

bool readValue(BinaryReader &reader, RulesetSelection &value)
{
    return readValue(reader, value.id)
        && readValue(reader, value.options.difficulty)
        && readValue(reader, value.options.progression)
        && readValue(reader, value.options.challengeMode)
        && readValue(reader, value.options.randomizer)
        && readValue(reader, value.options.preferences.homingProjectiles)
        && readValue(reader, value.options.preferences.friendlyFire)
        && readLootFilter(reader, value.options.preferences.lootFilter)
        && (reader.version() < SaveVersionMawChallengeModes
            || readValue(reader, value.options.preferences.disintegration))
        && (reader.version() < SaveVersionTrainerHints
            || readValue(reader, value.options.preferences.trainerHints))
        && (reader.version() < SaveVersionBowDisabled
            || readValue(reader, value.options.preferences.bowDisabled))
        && skipRetiredOtherWorldsLoot(reader)
        && !value.id.empty()
        && rulesetOptionsValid(value.options);
}

bool readSummaryFields(BinaryReader &reader, GameSaveSummary &value)
{
    if (!readValue(reader, value.mapFileName)
        || !readValue(reader, value.savedGameMinutes)
        || !readValue(reader, value.ruleset)
        || !readValue(reader, value.saveName)
        || !readValue(reader, value.previewBmp))
    {
        return false;
    }

    if (reader.version() < SaveVersionSummaryPlaythrough)
    {
        return true;
    }

    value.playthrough.emplace();
    return readValue(reader, value.playthrough->id) && readValue(reader, value.playthrough->playedSeconds);
}

void writeValue(BinaryWriter &writer, const GameSaveData &value)
{
    BinaryWriter summary;
    writeValue(summary, value.mapFileName);
    writeValue(summary, value.savedGameMinutes);
    writeValue(summary, value.ruleset);
    writeValue(summary, value.saveName);
    writeValue(summary, value.previewBmp);
    writeValue(summary, value.playthroughId);
    writeValue(summary, value.playthroughPlayedSeconds);
    const uint32_t summaryByteCount = uint32_t(summary.bytes().size());
    writeValue(writer, summaryByteCount);
    writer.writeBytes(summary.bytes().data(), summary.bytes().size());

    writeValue(writer, value.currentSceneKind);
    writeValue(writer, value.party);
    writeValue(writer, value.namedGlobalVars);
    writeValue(writer, value.hasOutdoorRuntimeState);
    writeValue(writer, value.outdoorParty);
    writeValue(writer, value.outdoorWorld);
    writeValue(writer, value.outdoorWorldStates);
    writeValue(writer, value.hasIndoorSceneState);
    writeValue(writer, value.indoorScene);
    writeValue(writer, value.indoorSceneStates);
    writeValue(writer, value.cameraYawRadians);
    writeValue(writer, value.cameraPitchRadians);
    writeValue(writer, value.heldInventoryItemActive);
    writeValue(writer, value.heldInventoryItem);
    writeValue(writer, value.heldInventoryItemGrabCellOffsetX);
    writeValue(writer, value.heldInventoryItemGrabCellOffsetY);
    writeValue(writer, value.heldInventoryItemGrabOffsetX);
    writeValue(writer, value.heldInventoryItemGrabOffsetY);
    writeValue(writer, value.requiredContentPackages);
    writeValue(writer, value.randomRootSeed);
    writeValue(writer, value.mawState);
    writeValue(writer, value.playthroughTimeline);
}

bool readValue(BinaryReader &reader, GameSaveData &value)
{
    const bool summaryFirst = reader.version() >= SaveVersionSummaryFirst;
    if (summaryFirst)
    {
        uint32_t summaryByteCount = 0;
        GameSaveSummary summary;
        if (!readValue(reader, summaryByteCount))
        {
            return false;
        }
        const size_t remainingBeforeSummary = reader.remainingBytes();
        if (!readSummaryFields(reader, summary)
            || remainingBeforeSummary - reader.remainingBytes() != summaryByteCount)
        {
            return false;
        }
        value.mapFileName = std::move(summary.mapFileName);
        value.savedGameMinutes = summary.savedGameMinutes;
        value.ruleset = std::move(summary.ruleset);
        value.saveName = std::move(summary.saveName);
        value.previewBmp = std::move(summary.previewBmp);

        if (summary.playthrough)
        {
            value.playthroughId = std::move(summary.playthrough->id);
            value.playthroughPlayedSeconds = summary.playthrough->playedSeconds;
        }
    }

    const bool read = readValue(reader, value.currentSceneKind)
        && (summaryFirst || readValue(reader, value.mapFileName))
        && readValue(reader, value.party)
        && (reader.version() < SaveVersionSessionNamedGlobalVars || readValue(reader, value.namedGlobalVars))
        && readValue(reader, value.hasOutdoorRuntimeState)
        && readValue(reader, value.outdoorParty)
        && readValue(reader, value.outdoorWorld)
        && readValue(reader, value.outdoorWorldStates)
        && readValue(reader, value.hasIndoorSceneState)
        && readValue(reader, value.indoorScene)
        && readValue(reader, value.indoorSceneStates)
        && (summaryFirst || readValue(reader, value.savedGameMinutes))
        && readValue(reader, value.cameraYawRadians)
        && readValue(reader, value.cameraPitchRadians)
        && (reader.version() < SaveVersionHeldCursorItem || readValue(reader, value.heldInventoryItemActive))
        && (reader.version() < SaveVersionHeldCursorItem || readValue(reader, value.heldInventoryItem))
        && (reader.version() < SaveVersionHeldCursorItem
            || readValue(reader, value.heldInventoryItemGrabCellOffsetX))
        && (reader.version() < SaveVersionHeldCursorItem
            || readValue(reader, value.heldInventoryItemGrabCellOffsetY))
        && (reader.version() < SaveVersionHeldCursorItem || readValue(reader, value.heldInventoryItemGrabOffsetX))
        && (reader.version() < SaveVersionHeldCursorItem || readValue(reader, value.heldInventoryItemGrabOffsetY))
        && (reader.version() < SaveVersionRequiredContentPackages
            || readValue(reader, value.requiredContentPackages))
        && (summaryFirst || reader.version() < SaveVersionRuleset || readValue(reader, value.ruleset))
        && (reader.version() < SaveVersionRandomRootSeed || readValue(reader, value.randomRootSeed))
        && (reader.version() < SaveVersionActorRulesetFacts || readValue(reader, value.mawState))
        && (reader.version() < SaveVersionPlaythroughStatistics || reader.version() >= SaveVersionSummaryPlaythrough
            || readValue(reader, value.playthroughId))
        && (reader.version() < SaveVersionPlaythroughStatistics || readValue(reader, value.playthroughTimeline))
        && (summaryFirst || readValue(reader, value.saveName))
        && (summaryFirst || readValue(reader, value.previewBmp));
    value.cameraAnglesValid = reader.version() >= SaveVersionIndoorCamera || value.currentSceneKind == SceneKind::Outdoor;
    return read;
}
}

namespace
{
void migrateLegacyIndoorCorpseMarkers(IndoorSceneRuntime::Snapshot &snapshot)
{
    if (!snapshot.mapDeltaData)
    {
        return;
    }

    const std::vector<MapDeltaActor> &actors = snapshot.mapDeltaData->actors;
    std::vector<std::optional<GameplayCorpseViewState>> &corpseViews =
        snapshot.worldRuntime.mapActorCorpseViews;
    corpseViews.resize(std::max(corpseViews.size(), actors.size()));
    const uint32_t invisibleMask = static_cast<uint32_t>(EvtActorAttribute::Invisible);

    for (size_t actorIndex = 0; actorIndex < actors.size(); ++actorIndex)
    {
        const MapDeltaActor &actor = actors[actorIndex];

        if (actor.hp <= 0 && (actor.attributes & invisibleMask) != 0 && !corpseViews[actorIndex].has_value())
        {
            GameplayCorpseViewState consumedCorpse = {};
            consumedCorpse.sourceIndex = static_cast<uint32_t>(actorIndex);
            corpseViews[actorIndex] = std::move(consumedCorpse);
        }
    }
}

void migrateLegacyOutdoorCorpseMarkers(OutdoorWorldRuntime::Snapshot &snapshot)
{
    std::vector<std::optional<GameplayCorpseViewState>> &corpseViews = snapshot.mapActorCorpseViews;
    corpseViews.resize(std::max(corpseViews.size(), snapshot.mapActors.size()));

    for (size_t actorIndex = 0; actorIndex < snapshot.mapActors.size(); ++actorIndex)
    {
        const OutdoorWorldRuntime::MapActorState &actor = snapshot.mapActors[actorIndex];
        const bool terminalCorpse = actor.isDead
            || actor.currentHp <= 0
            || actor.aiState == OutdoorWorldRuntime::ActorAiState::Dying
            || actor.aiState == OutdoorWorldRuntime::ActorAiState::Dead;

        if (terminalCorpse && actor.isInvisible && !corpseViews[actorIndex].has_value())
        {
            GameplayCorpseViewState consumedCorpse = {};
            consumedCorpse.sourceIndex = static_cast<uint32_t>(actorIndex);
            corpseViews[actorIndex] = std::move(consumedCorpse);
        }
    }
}

std::vector<uint32_t> persistentSaveItemIds(const GameSaveData &data)
{
    std::vector<uint32_t> itemIds;
    const auto appendInventoryItem = [&itemIds](const InventoryItem &item)
    {
        if (item.objectDescriptionId != 0)
        {
            itemIds.push_back(item.objectDescriptionId);
        }
    };
    const auto appendChestView = [&appendInventoryItem](const GameplayChestViewState &view)
    {
        for (const GameplayChestItemState &item : view.items)
        {
            appendInventoryItem(item.item);
        }
        for (const GameplayChestItemState &item : view.hiddenItems)
        {
            appendInventoryItem(item.item);
        }
    };
    const auto appendCorpseView = [&appendInventoryItem](const GameplayCorpseViewState &view)
    {
        for (const GameplayChestItemState &item : view.items)
        {
            appendInventoryItem(item.item);
        }
    };
    const auto appendCharacterItems = [&itemIds](const Character &member)
    {
        for (const InventoryItem &item : member.inventory)
        {
            if (item.objectDescriptionId != 0)
            {
                itemIds.push_back(item.objectDescriptionId);
            }
        }

        const CharacterEquipment &equipment = member.equipment;
        for (uint32_t itemId : {
                 equipment.offHand,
                 equipment.mainHand,
                 equipment.bow,
                 equipment.armor,
                 equipment.helm,
                 equipment.belt,
                 equipment.cloak,
                 equipment.gauntlets,
                 equipment.boots,
                 equipment.amulet,
                 equipment.ring1,
                 equipment.ring2,
                 equipment.ring3,
                 equipment.ring4,
                 equipment.ring5,
                 equipment.ring6})
        {
            if (itemId != 0)
            {
                itemIds.push_back(itemId);
            }
        }
    };

    for (const Character &member : data.party.members)
    {
        appendCharacterItems(member);
    }

    for (const AdventurersInnMember &member : data.party.adventurersInnMembers)
    {
        appendCharacterItems(member.character);
    }

    for (const Party::HouseStockState &state : data.party.houseStockStates)
    {
        for (const InventoryItem &item : state.standardStock)
        {
            appendInventoryItem(item);
        }
        for (const InventoryItem &item : state.specialStock)
        {
            appendInventoryItem(item);
        }
        for (const InventoryItem &item : state.spellbookStock)
        {
            appendInventoryItem(item);
        }
    }

    if (data.heldInventoryItemActive && data.heldInventoryItem.objectDescriptionId != 0)
    {
        itemIds.push_back(data.heldInventoryItem.objectDescriptionId);
    }

    const auto appendOutdoorWorld = [&](const OutdoorWorldRuntime::Snapshot &snapshot)
    {
        for (const std::optional<GameplayChestViewState> &view : snapshot.materializedChestViews)
        {
            if (view)
            {
                appendChestView(*view);
            }
        }
        if (snapshot.activeChestView)
        {
            appendChestView(*snapshot.activeChestView);
        }
        for (const std::optional<GameplayCorpseViewState> &view : snapshot.mapActorCorpseViews)
        {
            if (view)
            {
                appendCorpseView(*view);
            }
        }
        if (snapshot.activeCorpseView)
        {
            appendCorpseView(*snapshot.activeCorpseView);
        }
        for (const OutdoorWorldRuntime::WorldItemState &item : snapshot.worldItems)
        {
            appendInventoryItem(item.item);
        }
    };
    const auto appendIndoorWorld = [&](const IndoorWorldRuntime::Snapshot &snapshot)
    {
        for (const std::optional<GameplayChestViewState> &view : snapshot.materializedChestViews)
        {
            if (view)
            {
                appendChestView(*view);
            }
        }
        if (snapshot.activeChestView)
        {
            appendChestView(*snapshot.activeChestView);
        }
        for (const std::optional<GameplayCorpseViewState> &view : snapshot.mapActorCorpseViews)
        {
            if (view)
            {
                appendCorpseView(*view);
            }
        }
        if (snapshot.activeCorpseView)
        {
            appendCorpseView(*snapshot.activeCorpseView);
        }
    };

    if (data.hasOutdoorRuntimeState)
    {
        appendOutdoorWorld(data.outdoorWorld);
    }
    for (const auto &[mapName, snapshot] : data.outdoorWorldStates)
    {
        (void)mapName;
        appendOutdoorWorld(snapshot);
    }
    if (data.hasIndoorSceneState)
    {
        appendIndoorWorld(data.indoorScene.worldRuntime);
    }
    for (const auto &[mapName, snapshot] : data.indoorSceneStates)
    {
        (void)mapName;
        appendIndoorWorld(snapshot.worldRuntime);
    }

    std::sort(itemIds.begin(), itemIds.end());
    itemIds.erase(std::unique(itemIds.begin(), itemIds.end()), itemIds.end());
    return itemIds;
}
}

void migrateLegacyNpcRosters(GameSaveData &data)
{
    const float gameMinutes = data.savedGameMinutes > 0.0f ? data.savedGameMinutes
        : (data.currentSceneKind == SceneKind::Outdoor ? data.outdoorWorld.gameMinutes
                                                     : data.indoorScene.worldRuntime.gameMinutes);
    const int32_t currentMinute = std::max(0, int32_t(std::floor(gameMinutes)));
    const auto migrate = [currentMinute](std::optional<EventRuntimeState> &state)
    {
        if (!state)
        {
            return;
        }
        // Legacy map hashes are seed zero; keep the whole saved roster until its next monthly refill.
        if (state->namedMapVars.try_emplace("MMerge.RandomNPC.Seed", 0).second)
        {
            state->namedMapVars["MMerge.RandomNPC.RefillMinutes"] = currentMinute;
        }
        if (!state->generatedMercenaryRecruitsByNpcId.empty())
        {
            state->namedMapVars.try_emplace("MMerge.Mercenaries.RefillMonth", currentMinute / (28 * 24 * 60));
        }
    };
    migrate(data.outdoorWorld.eventRuntimeState);
    migrate(data.indoorScene.eventRuntimeState);
    for (auto &[mapFileName, snapshot] : data.outdoorWorldStates)
    {
        migrate(snapshot.eventRuntimeState);
    }
    for (auto &[mapFileName, snapshot] : data.indoorSceneStates)
    {
        migrate(snapshot.eventRuntimeState);
    }
}

void markLegacyCampFireDecorVars(GameSaveData &data, uint32_t sourceSaveVersion)
{
    if (sourceSaveVersion >= SaveVersionMMergeCampfireDecorVars)
    {
        return;
    }

    // Renumbering needs the map's decorations, so each map does it when next entered.
    const auto mark = [](std::optional<EventRuntimeState> &state)
    {
        if (state)
        {
            state->legacyCampFireDecorVars = true;
        }
    };
    mark(data.outdoorWorld.eventRuntimeState);
    mark(data.indoorScene.eventRuntimeState);
    for (auto &[mapFileName, snapshot] : data.outdoorWorldStates)
    {
        mark(snapshot.eventRuntimeState);
    }
    for (auto &[mapFileName, snapshot] : data.indoorSceneStates)
    {
        mark(snapshot.eventRuntimeState);
    }
}

void markLegacySmallBarrelDecorVars(GameSaveData &data, uint32_t sourceSaveVersion)
{
    if (sourceSaveVersion >= SaveVersionSmallStatBarrels)
    {
        return;
    }

    const auto mark = [](std::optional<EventRuntimeState> &state)
    {
        if (state)
        {
            state->legacySmallBarrelDecorVars = true;
        }
    };
    mark(data.outdoorWorld.eventRuntimeState);
    mark(data.indoorScene.eventRuntimeState);
    for (auto &[mapFileName, snapshot] : data.outdoorWorldStates)
    {
        mark(snapshot.eventRuntimeState);
    }
    for (auto &[mapFileName, snapshot] : data.indoorSceneStates)
    {
        mark(snapshot.eventRuntimeState);
    }
}

// Lich promotion and Lich or vampire mercenaries wrote MM8's Mind and Body resistance slots into our Light and Dark;
// nothing else sets either to an immunity.
void migrateLegacyLichImmunities(GameSaveData &data, uint32_t sourceSaveVersion)
{
    if (sourceSaveVersion >= SaveVersionLichImmunities)
    {
        return;
    }

    constexpr int MistakenImmunity = 65000;
    const auto migrate = [](Character &character)
    {
        character.permanentImmunities.light = false;
        character.permanentImmunities.dark = false;

        if (character.baseResistances.light >= MistakenImmunity)
        {
            character.baseResistances.light = 0;
        }

        if (character.baseResistances.dark >= MistakenImmunity)
        {
            character.baseResistances.dark = 0;
        }
    };
    const auto migrateRecruits = [&migrate](std::optional<EventRuntimeState> &state)
    {
        if (!state)
        {
            return;
        }

        for (auto &[npcId, recruit] : state->generatedMercenaryRecruitsByNpcId)
        {
            migrate(recruit.character);
        }
    };

    for (Character &member : data.party.members)
    {
        migrate(member);
    }

    for (AdventurersInnMember &innMember : data.party.adventurersInnMembers)
    {
        migrate(innMember.character);
    }

    migrateRecruits(data.outdoorWorld.eventRuntimeState);
    migrateRecruits(data.indoorScene.eventRuntimeState);
    for (auto &[mapFileName, snapshot] : data.outdoorWorldStates)
    {
        migrateRecruits(snapshot.eventRuntimeState);
    }
    for (auto &[mapFileName, snapshot] : data.indoorSceneStates)
    {
        migrateRecruits(snapshot.eventRuntimeState);
    }
}

void migrateLegacyMapAutonotes(GameSaveData &data, uint32_t sourceSaveVersion)
{
    if (sourceSaveVersion >= SaveVersionPartyAutonotes)
    {
        return;
    }

    constexpr uint32_t AutoNotesVariableTag = 0x00DFu;
    constexpr uint32_t AutoNoteVariableTag = 0x00E1u;
    std::unordered_set<uint32_t> &autonotes = data.party.autonotes;
    const auto migrate = [&autonotes](std::optional<EventRuntimeState> &state)
    {
        if (!state)
        {
            return;
        }

        for (auto iterator = state->variables.begin(); iterator != state->variables.end();)
        {
            const uint32_t tag = iterator->first & 0xFFFFu;
            const uint32_t autonoteId = iterator->first >> 16;

            if (autonoteId == 0 || (tag != AutoNoteVariableTag && tag != AutoNotesVariableTag))
            {
                ++iterator;
                continue;
            }

            if (iterator->second != 0)
            {
                autonotes.insert(autonoteId);
            }

            iterator = state->variables.erase(iterator);
        }
    };
    migrate(data.outdoorWorld.eventRuntimeState);
    migrate(data.indoorScene.eventRuntimeState);
    for (auto &[mapFileName, snapshot] : data.outdoorWorldStates)
    {
        migrate(snapshot.eventRuntimeState);
    }
    for (auto &[mapFileName, snapshot] : data.indoorSceneStates)
    {
        migrate(snapshot.eventRuntimeState);
    }
}

void migrateLegacyMapHistory(GameSaveData &data, uint32_t sourceSaveVersion)
{
    if (sourceSaveVersion >= SaveVersionPartyHistory)
    {
        return;
    }

    std::unordered_map<uint32_t, std::unordered_map<uint32_t, int32_t>> &partyHistory =
        data.party.historyEventTimesByContinent;
    const auto migrate = [&partyHistory](std::optional<EventRuntimeState> &state)
    {
        if (!state)
        {
            return;
        }

        // Keep the earliest time an entry was recorded on any map.
        for (const auto &[continentId, historyTimes] : state->historyEventTimesByContinent)
        {
            for (const auto &[historyId, gameMinutes] : historyTimes)
            {
                const auto [iterator, inserted] = partyHistory[continentId].try_emplace(historyId, gameMinutes);

                if (!inserted)
                {
                    iterator->second = std::min(iterator->second, gameMinutes);
                }
            }
        }

        state->historyEventTimesByContinent.clear();
        state->historyEventTimes.clear();
    };
    migrate(data.outdoorWorld.eventRuntimeState);
    migrate(data.indoorScene.eventRuntimeState);
    for (auto &[mapFileName, snapshot] : data.outdoorWorldStates)
    {
        migrate(snapshot.eventRuntimeState);
    }
    for (auto &[mapFileName, snapshot] : data.indoorSceneStates)
    {
        migrate(snapshot.eventRuntimeState);
    }
}

// Older events recorded every history page two pages late. Pages 1 and 2 are the forward pages, which no event recorded
// late, so only pages from 3 move.
void migrateLegacyHistoryNumbering(GameSaveData &data, uint32_t sourceSaveVersion)
{
    if (sourceSaveVersion >= SaveVersionHistoryNumbering)
    {
        return;
    }

    constexpr uint32_t HistoryPageShift = 2;
    const auto renumber = [](std::unordered_map<uint32_t, int32_t> &historyTimes)
    {
        std::unordered_map<uint32_t, int32_t> renumbered;

        for (const auto &[historyId, gameMinutes] : historyTimes)
        {
            const uint32_t correctedId = historyId > HistoryPageShift ? historyId - HistoryPageShift : historyId;
            const auto [iterator, inserted] = renumbered.try_emplace(correctedId, gameMinutes);

            if (!inserted)
            {
                iterator->second = std::min(iterator->second, gameMinutes);
            }
        }

        historyTimes = std::move(renumbered);
    };
    const auto renumberState = [&renumber](std::optional<EventRuntimeState> &state)
    {
        if (!state)
        {
            return;
        }

        renumber(state->historyEventTimes);

        for (auto &[continentId, historyTimes] : state->historyEventTimesByContinent)
        {
            renumber(historyTimes);
        }
    };

    for (auto &[continentId, historyTimes] : data.party.historyEventTimesByContinent)
    {
        renumber(historyTimes);
    }

    renumberState(data.outdoorWorld.eventRuntimeState);
    renumberState(data.indoorScene.eventRuntimeState);
    for (auto &[mapFileName, snapshot] : data.outdoorWorldStates)
    {
        renumberState(snapshot.eventRuntimeState);
    }
    for (auto &[mapFileName, snapshot] : data.indoorSceneStates)
    {
        renumberState(snapshot.eventRuntimeState);
    }
}

void migrateLegacyMapJournalNotes(GameSaveData &data, uint32_t sourceSaveVersion)
{
    if (sourceSaveVersion >= SaveVersionPartyJournalMapNotes)
    {
        return;
    }

    std::vector<JournalMapNote> &partyNotes = data.party.journalMapNotes;
    const auto migrate = [&partyNotes](std::optional<EventRuntimeState> &state)
    {
        if (!state)
        {
            return;
        }

        for (const auto &[noteId, legacyNote] : state->runtimeMapNotes)
        {
            const std::string mapFileName = toLowerCopy(legacyNote.mapFileName);
            const bool alreadyMigrated = std::any_of(
                partyNotes.begin(),
                partyNotes.end(),
                [&](const JournalMapNote &note) { return note.id == legacyNote.id && note.mapFileName == mapFileName; });

            // Notes without a map were never drawn, and the active map's state repeats the stored one.
            if (!legacyNote.active || mapFileName.empty() || alreadyMigrated)
            {
                continue;
            }

            // Old saves did not record which teacher pins had an autonote; revisiting the teacher corrects it.
            partyNotes.push_back(JournalMapNote{
                legacyNote.id, legacyNote.x, legacyNote.y, mapFileName, legacyNote.text, true});
        }

        state->runtimeMapNotes.clear();
    };
    migrate(data.outdoorWorld.eventRuntimeState);
    migrate(data.indoorScene.eventRuntimeState);
    for (auto &[mapFileName, snapshot] : data.outdoorWorldStates)
    {
        migrate(snapshot.eventRuntimeState);
    }
    for (auto &[mapFileName, snapshot] : data.indoorSceneStates)
    {
        migrate(snapshot.eventRuntimeState);
    }
}

void migrateLegacyMm6FaceTextureKeys(
    GameSaveData &data,
    const std::function<bool(const std::string &mapFileName)> &isMm6IndoorMap)
{
    if (data.sourceSaveVersion >= SaveVersionWideExperience)
    {
        return;
    }

    // MM6's scripts make no cog swaps (every reference is negative), so any key without the face bit is a face.
    const auto migrate = [](std::optional<EventRuntimeState> &state)
    {
        if (!state)
        {
            return;
        }

        std::unordered_map<uint32_t, std::string> overrides;

        for (auto &[key, textureName] : state->textureOverrides)
        {
            overrides[EventRuntime::indoorFaceReferenceKey(key)] = std::move(textureName);
        }

        state->textureOverrides = std::move(overrides);
    };

    if (data.currentSceneKind == SceneKind::Indoor && isMm6IndoorMap(data.mapFileName))
    {
        migrate(data.indoorScene.eventRuntimeState);
    }

    for (auto &[mapFileName, snapshot] : data.indoorSceneStates)
    {
        if (isMm6IndoorMap(mapFileName))
        {
            migrate(snapshot.eventRuntimeState);
        }
    }
}

void migrateLegacyConsumedCorpseMarkers(GameSaveData &data, uint32_t sourceSaveVersion)
{
    if (sourceSaveVersion >= SaveVersionConsumedCorpseMarkers)
    {
        return;
    }

    if (data.hasOutdoorRuntimeState)
    {
        migrateLegacyOutdoorCorpseMarkers(data.outdoorWorld);
    }

    for (auto &[mapName, snapshot] : data.outdoorWorldStates)
    {
        (void)mapName;
        migrateLegacyOutdoorCorpseMarkers(snapshot);
    }

    if (data.hasIndoorSceneState)
    {
        migrateLegacyIndoorCorpseMarkers(data.indoorScene);
    }

    for (auto &[mapName, snapshot] : data.indoorSceneStates)
    {
        (void)mapName;
        migrateLegacyIndoorCorpseMarkers(snapshot);
    }
}

std::unordered_map<std::string, uint32_t> collectRequiredContentPackages(
    const GameSaveData &data,
    const ItemTable &itemTable,
    const HouseTable &houseTable,
    const std::unordered_map<std::string, uint32_t> &loadedPackageSchemas)
{
    std::unordered_map<std::string, uint32_t> result;

    for (uint32_t itemId : persistentSaveItemIds(data))
    {
        const ItemDefinition *pDefinition = itemTable.get(itemId);

        if (pDefinition == nullptr || pDefinition->packageId.empty() || pDefinition->packageId == "engine")
        {
            continue;
        }

        const auto foundSchema = loadedPackageSchemas.find(pDefinition->packageId);
        result[pDefinition->packageId] = foundSchema != loadedPackageSchemas.end() ? foundSchema->second : 0;
    }

    for (const Party::HouseStockState &state : data.party.houseStockStates)
    {
        const HouseEntry *pHouseEntry = houseTable.get(state.houseId);
        if (state.generationVersion == 0
            || pHouseEntry == nullptr
            || pHouseEntry->packageId.empty()
            || pHouseEntry->packageId == "engine")
        {
            continue;
        }
        const auto foundSchema = loadedPackageSchemas.find(pHouseEntry->packageId);
        result[pHouseEntry->packageId] = foundSchema != loadedPackageSchemas.end() ? foundSchema->second : 0;
    }

    // A ruleset game needs its ruleset package at the same content schema.
    if (!data.ruleset.isStandard())
    {
        const std::string packageId = RulesetContentPackagePrefix + data.ruleset.id;
        const auto foundSchema = loadedPackageSchemas.find(packageId);
        result[packageId] = foundSchema != loadedPackageSchemas.end() ? foundSchema->second : 0;
    }

    return result;
}

bool validateRequiredContentPackageSchemas(
    const GameSaveData &data,
    const std::unordered_map<std::string, uint32_t> &loadedPackageSchemas,
    std::string &error)
{
    error.clear();

    for (const auto &[packageId, requiredSchema] : data.requiredContentPackages)
    {
        const auto foundPackage = loadedPackageSchemas.find(packageId);

        if (foundPackage == loadedPackageSchemas.end())
        {
            error = "save requires missing content package '" + packageId + "'";
            return false;
        }

        if (requiredSchema == 0 || foundPackage->second != requiredSchema)
        {
            error = "save requires content package '" + packageId + "' schema "
                + std::to_string(requiredSchema) + ", loaded schema is " + std::to_string(foundPackage->second);
            return false;
        }
    }

    return true;
}

bool validateRequiredContentPackages(
    const GameSaveData &data,
    const ItemTable &itemTable,
    const HouseTable &houseTable,
    const std::unordered_map<std::string, uint32_t> &loadedPackageSchemas,
    std::string &error)
{
    if (!validateRequiredContentPackageSchemas(data, loadedPackageSchemas, error))
    {
        return false;
    }

    for (uint32_t itemId : persistentSaveItemIds(data))
    {
        const ItemDefinition *pDefinition = itemTable.get(itemId);

        if (pDefinition == nullptr)
        {
            error = "save references missing item definition " + std::to_string(itemId);
            return false;
        }

        if (pDefinition->packageId != "engine"
            && !data.requiredContentPackages.contains(pDefinition->packageId))
        {
            error = "save item " + std::to_string(itemId) + " is missing required package metadata for '"
                + pDefinition->packageId + "'";
            return false;
        }
    }

    for (const Party::HouseStockState &state : data.party.houseStockStates)
    {
        if (state.generationVersion == 0)
        {
            continue;
        }
        const HouseEntry *pHouseEntry = houseTable.get(state.houseId);
        if (pHouseEntry == nullptr || pHouseEntry->vendorStockProfile == VendorStockProfile::None)
        {
            error = "save references missing vendor definition " + std::to_string(state.houseId);
            return false;
        }
        if (pHouseEntry->packageId != "engine"
            && !data.requiredContentPackages.contains(pHouseEntry->packageId))
        {
            error = "save vendor " + std::to_string(state.houseId)
                + " is missing required package metadata for '" + pHouseEntry->packageId + "'";
            return false;
        }
    }

    return true;
}

bool saveGameDataToPath(const std::filesystem::path &path, const GameSaveData &data, std::string &error)
{
    BinaryWriter writer;
    writer.writeBytes(SaveMagic, sizeof(SaveMagic));
    writer.write(SaveVersion);
    writer.write(data);

    std::filesystem::create_directories(path.parent_path());
    std::ofstream output(path, std::ios::binary);

    if (!output)
    {
        error = "could not open save file for writing";
        return false;
    }

    const std::vector<uint8_t> &bytes = writer.bytes();
    output.write(reinterpret_cast<const char *>(bytes.data()), static_cast<std::streamsize>(bytes.size()));

    if (!output.good())
    {
        error = "could not write save file";
        return false;
    }

    return true;
}

std::optional<GameSaveData> loadGameDataFromPath(const std::filesystem::path &path, std::string &error)
{
    std::ifstream input(path, std::ios::binary);

    if (!input)
    {
        error = "save file not found";
        return std::nullopt;
    }

    input.seekg(0, std::ios::end);
    const std::streamoff size = input.tellg();
    input.seekg(0, std::ios::beg);

    if (size <= 0)
    {
        error = "save file is empty";
        return std::nullopt;
    }

    std::vector<uint8_t> bytes(static_cast<size_t>(size));
    input.read(reinterpret_cast<char *>(bytes.data()), size);

    if (!input.good() && !input.eof())
    {
        error = "could not read save file";
        return std::nullopt;
    }

    BinaryReader reader(bytes);
    char magic[sizeof(SaveMagic)] = {};
    uint32_t version = 0;

    if (!reader.readBytes(magic, sizeof(magic))
        || std::memcmp(magic, SaveMagic, sizeof(SaveMagic)) != 0
        || !reader.read(version))
    {
        error = "invalid save header";
        return std::nullopt;
    }

    if (version > SaveVersion)
    {
        error = SaveFromNewerVersionError;
        return std::nullopt;
    }

    reader.setVersion(version);

    GameSaveData data = {};
    bool decoded = false;

    try
    {
        decoded = reader.read(data);
    }
    catch (const std::exception &exception)
    {
        error = std::string("save data is corrupted: ") + exception.what();
        return std::nullopt;
    }

    if (!decoded || reader.failed())
    {
        error = "save data is corrupted";
        return std::nullopt;
    }

    migrateLegacyConsumedCorpseMarkers(data, version);
    migrateLegacyNpcRosters(data);
    migrateLegacyMapAutonotes(data, version);
    migrateLegacyMapHistory(data, version);
    migrateLegacyHistoryNumbering(data, version);
    migrateLegacyMapJournalNotes(data, version);
    markLegacyCampFireDecorVars(data, version);
    markLegacySmallBarrelDecorVars(data, version);
    migrateLegacyLichImmunities(data, version);
    data.sourceSaveVersion = version;

    return data;
}

namespace
{
SavePlaythroughInfo savePlaythroughInfo(const GameSaveData &data)
{
    SavePlaythroughInfo info;
    info.id = PlaythroughStatistics::playthroughIdOfSave(data.playthroughId, data.randomRootSeed);
    info.playedSeconds = data.sourceSaveVersion >= SaveVersionSummaryPlaythrough
        ? data.playthroughPlayedSeconds
        : PlaythroughStatistics::timelinePlayedSeconds(info.id, data.playthroughTimeline);
    return info;
}
}

std::optional<SavePlaythroughInfo> loadSavePlaythroughInfoFromPath(
    const std::filesystem::path &path,
    std::string &error)
{
    const std::optional<GameSaveData> data = loadGameDataFromPath(path, error);
    return data ? std::optional<SavePlaythroughInfo>(savePlaythroughInfo(*data)) : std::nullopt;
}

namespace
{
// "quicksave", "quicksave2", "quicksave3".
std::string quickSaveSlotName(int slot)
{
    return slot <= 1 ? "quicksave" : "quicksave" + std::to_string(slot);
}
}

std::filesystem::path quickSavePath(const std::string &playthroughId, int slot)
{
    return saveSlotPath(quickSaveSlotName(slot), playthroughId);
}

std::filesystem::path autosavePath(const std::string &playthroughId)
{
    return saveSlotPath("autosave", playthroughId);
}

bool isQuickSavePath(const std::filesystem::path &path)
{
    return quickSaveSlot(path) != 0;
}

int quickSaveSlot(const std::filesystem::path &path)
{
    // "quicksave", then the slot number from 2 up, then nothing or "_<playthrough id>".
    const std::string stem = toLowerCopy(path.stem().string());
    const std::string first = quickSaveSlotName(1);

    if (stem.rfind(first, 0) != 0)
    {
        return 0;
    }

    const size_t numberEnd = std::min(stem.find_first_not_of("0123456789", first.size()), stem.size());

    if (numberEnd != stem.size() && stem[numberEnd] != '_')
    {
        return 0;
    }

    if (numberEnd == first.size())
    {
        return 1;
    }

    const std::string number = stem.substr(first.size(), numberEnd - first.size());

    // Written without leading zeros, and the first slot without a number.
    if (number.size() > 2 || number[0] == '0')
    {
        return 0;
    }

    const int slot = std::stoi(number);
    return slot >= 2 && slot <= MaxQuickSaveSlotCount ? slot : 0;
}

bool saveQuickSaveToPath(
    const std::filesystem::path &path,
    const GameSaveData &data,
    int slotCount,
    std::string &error)
{
    slotCount = std::clamp(slotCount, 1, MaxQuickSaveSlotCount);

    if (quickSaveSlot(path) != 1)
    {
        return saveGameDataToPath(path, data, error);
    }

    // Written beside the slots first, so that nothing moves for a save that fails.
    std::filesystem::path written = path;
    written += ".tmp";
    std::error_code fileError;

    if (!saveGameDataToPath(written, data, error))
    {
        std::filesystem::remove(written, fileError);
        return false;
    }

    // The slots' file names differ only in the number behind "quicksave".
    const std::string tail = path.filename().string().substr(quickSaveSlotName(1).size());
    const auto slotPath = [&path, &tail](int slot)
    {
        return path.parent_path() / (quickSaveSlotName(slot) + tail);
    };
    int last = 1;

    while (last < slotCount && std::filesystem::exists(slotPath(last), fileError))
    {
        ++last;
    }

    for (int slot = last; slot > 1; --slot)
    {
        std::filesystem::rename(slotPath(slot - 1), slotPath(slot), fileError);
    }

    for (int slot = slotCount + 1; slot <= MaxQuickSaveSlotCount; ++slot)
    {
        std::filesystem::remove(slotPath(slot), fileError);
    }

    std::filesystem::rename(written, path, fileError);

    if (fileError)
    {
        error = "could not write save file";
        std::filesystem::remove(written, fileError);
        return false;
    }

    return true;
}

bool isAutosavePath(const std::filesystem::path &path)
{
    return isSaveSlotPath(path, "autosave");
}

void migrateSharedSaveSlots(const std::filesystem::path &savesDirectory)
{
    for (const char *pSlot : {"quicksave", "autosave"})
    {
        const std::filesystem::path shared = savesDirectory / (std::string(pSlot) + ".oysav");
        std::error_code error;

        if (!std::filesystem::is_regular_file(shared, error))
        {
            continue;
        }

        std::string loadError;
        const std::optional<GameSaveSummary> summary = loadGameSaveSummaryFromPath(shared, loadError);
        std::optional<SavePlaythroughInfo> playthrough = summary ? summary->playthrough : std::nullopt;

        if (summary && !playthrough)
        {
            playthrough = loadSavePlaythroughInfoFromPath(shared, loadError);
        }

        if (!playthrough || playthrough->id.empty())
        {
            continue;
        }

        const std::filesystem::path own = savesDirectory / saveSlotPath(pSlot, playthrough->id).filename();

        if (!std::filesystem::exists(own, error))
        {
            std::filesystem::rename(shared, own, error);
        }
    }
}

std::optional<GameSaveSummary> loadGameSaveSummaryFromPath(const std::filesystem::path &path, std::string &error)
{
    std::ifstream input(path, std::ios::binary);

    if (!input)
    {
        error = "save file not found";
        return std::nullopt;
    }

    std::vector<uint8_t> header(sizeof(SaveMagic) + 2 * sizeof(uint32_t));
    input.read(reinterpret_cast<char *>(header.data()), static_cast<std::streamsize>(header.size()));
    header.resize(static_cast<size_t>(input.gcount()));
    BinaryReader headerReader(header);
    char magic[sizeof(SaveMagic)] = {};
    uint32_t version = 0;

    if (!headerReader.readBytes(magic, sizeof(magic))
        || std::memcmp(magic, SaveMagic, sizeof(SaveMagic)) != 0
        || !headerReader.read(version))
    {
        error = "invalid save header";
        return std::nullopt;
    }

    if (version > SaveVersion)
    {
        error = SaveFromNewerVersionError;
        return std::nullopt;
    }

    if (version < SaveVersionSummaryFirst)
    {
        // Older saves keep the summary behind the game state.
        input.close();
        std::optional<GameSaveData> data = loadGameDataFromPath(path, error);

        if (!data)
        {
            return std::nullopt;
        }

        GameSaveSummary summary;
        summary.mapFileName = std::move(data->mapFileName);
        summary.savedGameMinutes = data->savedGameMinutes;
        summary.ruleset = std::move(data->ruleset);
        summary.saveName = std::move(data->saveName);
        summary.previewBmp = std::move(data->previewBmp);
        summary.playthrough = savePlaythroughInfo(*data);
        return summary;
    }

    uint32_t summaryByteCount = 0;
    std::error_code sizeError;
    const uintmax_t fileSize = std::filesystem::file_size(path, sizeError);

    if (!headerReader.read(summaryByteCount) || sizeError || summaryByteCount > fileSize - header.size())
    {
        error = "save data is corrupted";
        return std::nullopt;
    }

    std::vector<uint8_t> summaryBytes(summaryByteCount);
    input.read(reinterpret_cast<char *>(summaryBytes.data()), static_cast<std::streamsize>(summaryBytes.size()));
    BinaryReader reader(summaryBytes);
    reader.setVersion(version);
    GameSaveSummary summary;

    if (static_cast<size_t>(input.gcount()) != summaryBytes.size()
        || !readSummaryFields(reader, summary)
        || reader.failed()
        || reader.remainingBytes() != 0)
    {
        error = "save data is corrupted";
        return std::nullopt;
    }

    return summary;
}

int compareSaveNamesNaturally(const std::string &left, const std::string &right)
{
    size_t leftIndex = 0;
    size_t rightIndex = 0;

    while (leftIndex < left.size() && rightIndex < right.size())
    {
        const unsigned char leftChar = static_cast<unsigned char>(left[leftIndex]);
        const unsigned char rightChar = static_cast<unsigned char>(right[rightIndex]);

        if (std::isdigit(leftChar) && std::isdigit(rightChar))
        {
            // Digit runs compare as numbers, so "Sewer 2" sorts before "Sewer 10".
            size_t leftStart = leftIndex;
            size_t rightStart = rightIndex;

            while (leftStart < left.size() && left[leftStart] == '0')
            {
                ++leftStart;
            }

            while (rightStart < right.size() && right[rightStart] == '0')
            {
                ++rightStart;
            }

            size_t leftEnd = leftStart;
            size_t rightEnd = rightStart;

            while (leftEnd < left.size() && std::isdigit(static_cast<unsigned char>(left[leftEnd])))
            {
                ++leftEnd;
            }

            while (rightEnd < right.size() && std::isdigit(static_cast<unsigned char>(right[rightEnd])))
            {
                ++rightEnd;
            }

            if (leftEnd - leftStart != rightEnd - rightStart)
            {
                return leftEnd - leftStart < rightEnd - rightStart ? -1 : 1;
            }

            const int digitOrder = left.compare(leftStart, leftEnd - leftStart, right, rightStart, rightEnd - rightStart);

            if (digitOrder != 0)
            {
                return digitOrder < 0 ? -1 : 1;
            }

            leftIndex = leftEnd;
            rightIndex = rightEnd;
            continue;
        }

        const int lowerLeft = std::tolower(leftChar);
        const int lowerRight = std::tolower(rightChar);

        if (lowerLeft != lowerRight)
        {
            return lowerLeft < lowerRight ? -1 : 1;
        }

        ++leftIndex;
        ++rightIndex;
    }

    if (leftIndex < left.size() || rightIndex < right.size())
    {
        return leftIndex < left.size() ? 1 : -1;
    }

    return 0;
}

bool compareSavesForDisplay(
    const std::filesystem::path &leftPath,
    const std::string &leftName,
    const std::filesystem::path &rightPath,
    const std::string &rightName)
{
    const int leftPriority = savePathDisplayPriority(leftPath);
    const int rightPriority = savePathDisplayPriority(rightPath);

    if (leftPriority != rightPriority)
    {
        return leftPriority < rightPriority;
    }

    const int nameOrder = compareSaveNamesNaturally(leftName, rightName);

    if (nameOrder != 0)
    {
        return nameOrder < 0;
    }

    return compareSaveNamesNaturally(leftPath.filename().string(), rightPath.filename().string()) < 0;
}
}
