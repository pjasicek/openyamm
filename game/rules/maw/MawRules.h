#pragma once

#include "game/content/RulesetOptions.h"
#include "game/rules/GameRules.h"
#include "game/rules/maw/MawBalanceModel.h"
#include "game/rules/maw/MawClassRules.h"
#include "game/rules/maw/MawCombatRules.h"
#include "game/rules/maw/MawCraftingData.h"
#include "game/rules/maw/MawDimensionMaps.h"
#include "game/rules/maw/MawTexts.h"
#include "game/rules/maw/MawCraftingRules.h"
#include "game/rules/maw/MawExperienceRules.h"
#include "game/rules/maw/MawGameState.h"
#include "game/rules/maw/MawItemData.h"
#include "game/rules/maw/MawItemRules.h"
#include "game/rules/maw/MawMadnessLedger.h"
#include "game/rules/maw/MawMonsterLevels.h"
#include "game/rules/maw/MawMonsterRules.h"
#include "game/rules/maw/MawPotionRules.h"
#include "game/rules/maw/MawPromotions.h"
#include "game/rules/maw/MawSkillRules.h"
#include "game/rules/maw/MawSpellRules.h"
#include "game/rules/maw/MawTrainerHints.h"

#include <array>
#include <map>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
class SpellTable;
class ItemTable;
class ClassMultiplierTable;
class StandardItemEnchantTable;
class SpecialItemEnchantTable;
class MapStats;
struct MapStatsEntry;

// What MAW's classes keep between hits and casts: the character's own rules runtime.
using MawClassRuntime = CharacterRulesRuntime;

// An aura in effect: its holder's school skill (capped), mastery and level.
struct MawAuraSource
{
    double skill = 0;
    int mastery = 0;
    double level = 0;
    uint32_t holder = 0;
};

// The MAW ruleset of one game (devdocs/maw/HANDOFF.md phase 3): its options, its level banks and the rules objects
// the party plays by. The session owns it and installs gameRules() on the party.
class MawRules
{
public:
    MawRules(
        const RulesetOptions &options,
        const MawMapLevels &mapLevels,
        MawItemData itemData = {},
        MawPromotionData promotionData = {},
        MawCraftingData craftingData = {},
        MawTextData textData = {},
        MawDimensionData dimensionData = {});
    MawRules(const MawRules &) = delete;
    MawRules &operator=(const MawRules &) = delete;

    const GameRules &gameRules() const;
    const MawItemRules &itemRules() const;
    const MawSpellRules &spellRules() const;
    const MawClassRules &classRules() const;
    const RulesetOptions &options() const;
    // A difficulty change: every number sized by the balance model is resolved again.
    void setOptions(const RulesetOptions &options);
    MawGameState &state();
    const MawGameState &state() const;
    void setState(const MawGameState &state);
    const MawMapLevels &mapLevels() const;
    // The story bands' quest bits the party has reached (MawMapLevels::band); the map's monster levels follow.
    void updateStoryBands(const Party &party);
    const MawItemData &itemData() const;
    const MawCraftingData &craftingData() const;
    const MawTextData &textData() const;
    const MawDimensionData &dimensionData() const;
    // The map table, for the maps dimension maps open (the session's data).
    const MapStats *mapTable() const;
    void setMapTable(const MapStats *pMapTable);
    // The spell table, for what spells cost the caster in recovery (leech floors).
    const SpellTable *spellTable() const;
    void setSpellTable(const SpellTable *pSpellTable);
    // The item table, for what a sealed spellbook holds (its book's mastery and value).
    const ItemTable *itemTable() const;
    void setItemTable(const ItemTable *pItemTable);
    // The class table, for a class's SP per level in Enlightenment's base.
    const ClassMultiplierTable *classMultiplierTable() const;
    void setClassMultiplierTable(const ClassMultiplierTable *pClassMultiplierTable);
    // The enchantment tables, for an attacker's character sheet inside the damage pipeline (Legendary 14).
    const StandardItemEnchantTable *standardItemEnchantTable() const;
    const SpecialItemEnchantTable *specialItemEnchantTable() const;
    void setItemEnchantTables(const StandardItemEnchantTable *pStandard, const SpecialItemEnchantTable *pSpecial);
    // The map being played, lowercase: set when its load begins.
    const std::string &currentMap() const;
    void setCurrentMap(const std::string &mapFileName);
    // The last outdoor map set as the current one, lowercase (runtime only: empty after loading a save indoors).
    const std::string &lastOutdoorMap() const;
    // Whether MAW's outdoor rules hold on a map: an ODM, or a BLV its world declares open to the sky (MM9's regions
    // and cities, world.yml openAirMaps).
    bool outdoorMap(const std::string &mapFileName) const;
    // Where teachers teach, for the skill popups' trainer hints (the session's tables; empty without them).
    const MawTrainerHints &trainerHints() const;
    void setTrainerHints(MawTrainerHints hints);
    // The dimension run on a map, or null.
    const MawDimensionRun *dimensionRun(const std::string &mapFileName) const;
    // An affix's value where a dimension run puts it in force (the current map without a name), else nothing
    // (getMapAffixPower).
    std::optional<double> mapAffix(MawMapAffix affix) const;
    // Dimension affix 33 on the current map: buff strengths times 1 - X / 100 (MAW scales its buffPower table's base
    // and scaling; once, not again on every load as MAW does, DEVIATIONS 60). 1 elsewhere.
    double buffScale() const;
    std::optional<double> mapAffix(const std::string &mapFileName, MawMapAffix affix) const;
    // The maps a dimension map may open now: the completed ones among the data's dungeons (getDimensionMapPool).
    std::vector<uint16_t> dimensionMapPool() const;
    // A new dimension map from the stream: a target from the pool, the affixes of the chosen slots, `activeSlots`
    // active (0: all) and the power (at most 255). Nothing for an empty pool.
    MawDimensionMap rollDimensionMap(
        RandomStream &stream,
        const std::vector<uint16_t> &pool,
        const std::array<bool, 4> &slots,
        uint8_t activeSlots,
        int power) const;
    // The difficulty settings item rolls read.
    MawLootConfig lootConfig() const;
    // The drop level of loot without a monster (chests, the ground): the median monster level of the map whose levels
    // were resolved last, the current one.
    double mapDropLevel() const;
    // The level of the current map's own monsters: the lower middle of its B rows, when its levels were resolved
    // (MAW's mapMonsterLevel, MON:1930-1938).
    std::optional<double> mapMonsterLevel() const;
    // The game's random root seed, for MAW's seeded rolls (bosses). In Beyond Madness it is also the run of the death
    // ledger: setting it (new game or load) opens that run, and a run left pending counts a death.
    uint64_t randomRootSeed() const;
    void setRandomRootSeed(uint64_t rootSeed);

    // Beyond Madness's death ledger (P9.M8): idle in every other mode. The file defaults to saves/maw_madness_deaths.txt.
    const MawMadnessLedger &madnessLedger() const;
    void setMadnessLedgerFile(const std::filesystem::path &file);
    // A hit landed on a member: a monster's, a trap's, a fall (CHM-2).
    void markMadnessHit(double gameMinutes);
    // Each frame: the party's deaths (its NumDeaths event variable) and the ledger's wait.
    void updateMadnessLedger(const Party &party, double gameMinutes, bool enemiesNear);
    void leaveMadnessMap();

    // The auras in effect at the last update (holders conscious), by spell id; runtime only.
    std::optional<MawAuraSource> activeAura(uint32_t spellId) const;
    void setActiveAuras(std::unordered_map<uint32_t, MawAuraSource> auras);
    // Living hostile monsters within 512 of the party at the last update (legendaries 21 and 22); runtime only.
    int nearbyMonsters() const;
    void setNearbyMonsters(int count);
    // Whether a living Shadow (or Omnipotent) boss is within 2000 of the party, which keeps Wizard Eye off; runtime.
    bool shadowBossNearby() const;
    void setShadowBossNearby(bool nearby);
    // The levels a bounty hunt's map adds to its monsters' table levels when it holds the hunt's target
    // (mapvars.mawBounty, kept in the map's named variable MawBounty as levels + 1); runtime copy.
    std::optional<int> bountyLevel() const;
    void setBountyLevel(std::optional<int> levels);
    // Beyond Madness gives no experience, corpse loot or crafting drops on the arenas (zarena, d42), 7d05 and a
    // bounty's map (zzzMaw_Experience.lua:162-166, zzMaw-Monsters.lua:4421-4428, zzAlchemy.lua:1122-1126).
    bool madnessRewardlessMap(const std::string &mapFileName) const;
    // What the party's staffs add to every member's resistances at the last update (mawStaffPartyResistance);
    // runtime only.
    int partyStaffResistance() const;
    void setPartyStaffResistance(int resistance);
    // MAW's unstuck key (zzMAW-Skills.lua:2501-2510): whether it may lift the party at this game minute; taking it
    // starts its five-minute wait. Runtime only, so a load makes it ready (MAW saves vars.lastUnstuck).
    bool takeUnstuck(double gameMinutes);
    // Austerity's Identify Monster (zzAlchemy.lua:40-46, zzMAWRespec.lua:51-55): every member gets 10 Grandmaster on
    // each map load; a respec takes it from all of them until the next. Runtime only: a load counts as a map load.
    bool austerityIdentifyRespecced() const;
    void setAusterityIdentifyRespecced(bool respecced);
    // An aura as one member feels it: the party's, or the member's own potion copy when that is stronger
    // (getBuffSkill; they never add).
    std::optional<MawAuraSource> memberAura(uint32_t spellId, const Character &member) const;
    // The member's potion copy of an aura alone (Master, at the potion's power), while it lasts.
    static std::optional<MawAuraSource> potionAura(uint32_t spellId, const Character &member);
    // The caster skill an aura's effect reads: its holder's (or the member's potion's, when stronger), or, for Haste,
    // Shield, Stone Skin and Fate, Hour of Power's at skill / 1.5 when that is stronger (bestBuffSource); nothing
    // when it is not in effect.
    std::optional<double> auraSkill(uint32_t spellId, const Character *pMember = nullptr) const;
    // The Bless skill behind a member's hit bonus: the aura's, or 0 for Excalibur's own Bless without one
    // (blessHitBonus, Formulas.lua:98-110; zzzMaw_Artifacts.lua:743).
    std::optional<double> blessHitSkill(const Character &member) const;

    // A party member's class runtime state, kept with the character.
    MawClassRuntime &classRuntime(const Character &member) const;

    // How many worlds have completed the promotion of a class kind (0-3), from the promotion qbits.
    int promotionWorlds(uint32_t classKind) const;
    const std::map<uint32_t, int> &promotionWorldsByKind() const;
    void setPromotionWorlds(std::map<uint32_t, int> worlds);
    const MawPromotionData &promotionData() const;

    // The balance model for a party of this size.
    MawBalanceModel &model(int partyCount) const;
    // A crowd-control duration after diminishing returns (calcDebuffDuration, SP:1817-1852) for groups 2 (fear and
    // control) and 3 (paralysis): shortened by the share of the last 20 seconds the monster spent under the group's
    // control, 0 once it is immune, halved on a boss, and recorded. Spells and weapon stuns share the history.
    double diminishedCrowdControlSeconds(
        uint64_t targetKey,
        int group,
        double nowSeconds,
        double seconds,
        bool boss) const;
    // Every monster's level on a map at the current banks, by monster id (rebuilt when the map or the banks change).
    // The levels the map's monsters gain over their table level (mawMapBolster), as corpse gold reads it.
    double mapBolster(const MonsterTable &monsterTable, const MapStatsEntry &map) const;
    // The same without resolving the monsters' levels (chest gold).
    double mapBolster(const MapStatsEntry &map) const;
    const std::unordered_map<int, int> &monsterLevels(const MonsterTable &monsterTable, const MapStatsEntry &map) const;
    // A map's monster level as the Journal's Progress tab shows it: the mean level of its own B-tier families at the
    // current banks, and the part of it the map's resets add (0 for a map without native families).
    std::pair<int, int> mapLevelSummary(const MonsterTable &monsterTable, const MapStatsEntry &map) const;

    // MAW's map table with every world's maps (map_levels.yml and the worlds' balance files), each map's level as the
    // Progress tab counts it under each progression, whatever this game's options (`ruleset maplevels`): free with no
    // levels banked elsewhere and with `bankedLevels`, horizontal, Beyond Madness. Maps without native families are 0.
    struct MapLevelRow
    {
        std::string fileName;
        std::string name;
        uint32_t continentId = 0;
        std::array<double, 3> band = {};
        bool horizontalStarter = false;
        int madnessLevel = 0;
        int freeLevel = 0;
        int freeBankedLevel = 0;
        int horizontalLevel = 0;
        int madnessMapLevel = 0;
    };
    std::vector<MapLevelRow> mapLevelTable(const MonsterTable &monsterTable, double bankedLevels) const;

    // Each listed map's native families, A, B and C, as this game's options and banks make them (`ruleset
    // mapmonsters`): the numbers MAW gives a fresh spawn of each (level, hit points, armour, attack damage).
    struct MapMonsterRow
    {
        std::string fileName;
        uint32_t continentId = 0;
        std::string family;
        int monsterId = 0;
        std::string name;
        uint8_t tier = 0;
        int level = 0;
        int maxHp = 0;
        int armorClass = 0;
        float attackDamage = 0.0f;
    };
    std::vector<MapMonsterRow> mapMonsterTable(const MonsterTable &monsterTable, const Party *pParty) const;

private:
    MawMonsterLevelInputs monsterLevelInputs(const MapStatsEntry &map) const;

    struct MonsterLevelCache
    {
        std::string mapFileName;
        double partyLevel = -1;
        int resetCount = -1;
        int dimensionPower = -1;
        std::optional<int> bountyLevel;
        std::unordered_map<int, int> levels;
        double bolster = 0;
        // The levels of the map's own B rows (one per encounter slot naming them), ordered by table level.
        std::vector<int> nativeLevels;
    };

    RulesetOptions m_options;
    MawMapLevels m_mapLevels;
    MawItemData m_itemData;
    MawPromotionData m_promotionData;
    MawCraftingData m_craftingData;
    MawTextData m_textData;
    MawDimensionData m_dimensionData;
    const MapStats *m_pMapTable = nullptr;
    const SpellTable *m_pSpellTable = nullptr;
    const ItemTable *m_pItemTable = nullptr;
    const ClassMultiplierTable *m_pClassMultiplierTable = nullptr;
    const StandardItemEnchantTable *m_pStandardItemEnchantTable = nullptr;
    const SpecialItemEnchantTable *m_pSpecialItemEnchantTable = nullptr;
    std::string m_currentMap;
    std::string m_lastOutdoorMap;
    MawTrainerHints m_trainerHints;
    MawGameState m_state;
    uint64_t m_randomRootSeed = 0;
    MawMadnessLedger m_madnessLedger{std::filesystem::path("saves") / "maw_madness_deaths.txt"};
    // The party's NumDeaths at the last ledger update; none until the first update of a run.
    std::optional<int> m_madnessSeenDeaths;
    mutable std::map<int, MawBalanceModel> m_models;
    mutable MonsterLevelCache m_monsterLevels;
    std::unordered_map<uint32_t, MawAuraSource> m_activeAuras;
    int m_nearbyMonsters = 0;
    bool m_shadowBossNearby = false;
    std::optional<int> m_bountyLevel;
    int m_partyStaffResistance = 0;
    double m_unstuckReadyGameMinutes = 0;
    bool m_austerityIdentifyRespecced = false;
    std::map<uint32_t, int> m_promotionWorlds;
    // Runtime only: the crowd control each monster was under lately, per diminishing-returns group (2 and 3), as
    // intervals of the world clock.
    mutable std::unordered_map<uint64_t, std::array<std::vector<std::pair<double, double>>, 2>> m_crowdControlHistory;
    MawExperienceRules m_experience;
    MawCombatRules m_combat;
    MawMonsterRules m_monsters;
    MawItemRules m_items;
    MawSkillRules m_skills;
    MawSpellRules m_spells;
    MawClassRules m_classes;
    MawPotionRules m_potions;
    MawCraftingRules m_crafting;
    GameRules m_gameRules;
};
}
