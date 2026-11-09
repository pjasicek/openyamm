#pragma once

#include "game/rules/MonsterRules.h"

#include <string>
#include <unordered_map>
#include <unordered_set>

namespace OpenYAMM::Game
{
class MawBalanceModel;
class MawRules;
struct MapKillProgress;
struct MawDimensionRun;

// MAW's monsters (devdocs/maw/data/monster_scaling.yml): MMMerge's bolster is off; a monster's level follows the map's
// band, the progression mode and the banks, and its HP, damage, armour and experience are sized by the balance model
// against a character of its family's B-tier level. Resolved per spawn into the actor's ruleset facts; the shared
// monster table is never rewritten.
class MawMonsterRules : public MonsterRules
{
public:
    explicit MawMonsterRules(MawRules &rules);

    GameplayMonsterBolsterResult resolveMonster(
        const GameplayBolsterRuntimeContext &context,
        const MonsterTable::MonsterStatsEntry &stats,
        const MonsterEntry *pMonsterEntry) const override;
    // Bosses (devdocs/maw/data/bosses.yml): from MAW difficulty up, ceil((monsters - 30) / 150) of the map's hostile,
    // unnamed C-tier monsters (/ 60 from Doom), each with an affix and its HP and damage multipliers; then the Doom
    // modes' special attacks.
    bool placeMapMonsters(
        const GameplayBolsterRuntimeContext &context,
        std::vector<MapMonsterPlacement> &monsters) const override;
    // Monster density (devdocs/maw/data/difficulty.yml density_rules), raised on a dimension map.
    void adjustMapEncounters(MapStatsEntry &map) const override;
    // A dimension map's families replace the map's own.
    void enterMap(MapStatsEntry &map, const MonsterTable &monsterTable) const override;
    // A dimension map's "higher tier" affix.
    char spawnTier(const MapStatsEntry &map, char tier, uint32_t seed) const override;
    // "dimensional_maps": the Dimensional Maps quest of the Oracle, Judge Grey and the Seer
    // (Global/zzMaw_DimensionalMapsQuest.lua).
    std::optional<std::string> rulesTopic(const std::string &topic, Party &party) const override;
    // A boss of the actor's own level: twice its level less its family's, a random affix, x 2.5-7.5 health and
    // x 1.2-1.4 damage (generateBoss, zzMaw-Monsters.lua:2866-3110).
    bool makeBoss(ActorRulesetFacts &facts, uint64_t seed, uint8_t affix) const override;
    std::string actorDisplayName(const ActorRulesetFacts &facts, const std::string &name) const override;
    // A boss shows the boss skull and its affix's badge (maw_boss_<affix>).
    std::vector<std::string> actorBadges(const ActorRulesetFacts &facts) const override;
    // Bosses are drawn x1.4 indoors and x2 outdoors, an Omnipotent one half as much again
    // (zzMaw-Monsters.lua:3641-3653).
    float actorDrawScale(const ActorRulesetFacts &facts, bool indoor) const override;
    // A completed dungeon can be reset at its entrance: +20 monster levels each time, no second completion reward
    // (zzMaw-Maps.lua:183-237); never in Road to Insanity and Beyond Madness.
    // Respawn on exit (zzMaw-Monsters.lua:2206-2263, 2785-2794): from Nightmare an indoor map left before 65 % of its
    // monsters fell raises the slain, worth a quarter of their experience (none in Road to Insanity and Beyond
    // Madness); once 65 % are slain the map is weakened for good, until it is reset.
    void leaveMap(IGameplayWorldRuntime &world) const override;
    // Remembers the barrel or cauldron; the map's next loads empty it again (zzMaw-Maps.lua:240-283).
    void decorationRaisedStats(const std::string &mapFileName, uint8_t decorVarIndex, uint8_t emptyState) const override;
    void decorationsRenumbered(const std::string &mapFileName, std::span<const int16_t> remap) const override;
    // checkMapCompletition's progress (zzMaw-Monsters.lua:2568-2796) for the HUD's bar: mawMapProgress on the map's
    // kills, revival state, reward and dimension run, or the Endless Arena's wave in d42.
    std::optional<RulesetMapProgress> mapProgress(const IGameplayWorldRuntime &world) const override;
    bool countsForMapCompletion(const MapStatsEntry &map, const MonsterTable::MonsterStatsEntry &stats) const override;
    double packDensityFactor(const MapStatsEntry &map) const override;
    bool keepsUsedBarrelsThroughRefill() const override;
    // The bolster level is getPartyLevel() - 4, never below 0 (zzMaw-Monsters.lua:418-422).
    RulesetScriptInfo scriptInfo(uint32_t continentId) const override;
    // BountyHunt.lua: round(level + the levels banked on the three continents) x 100.
    uint32_t bountyReward(const MonsterTable::MonsterStatsEntry &stats) const override;
    // "You need to clear the area COMPLETELY first."
    std::optional<std::string> bountyRefusal(const IGameplayWorldRuntime &world) const override;
    // The region must be cleared since it last refilled.
    std::optional<std::string> bountyRefusalForMap(
        const std::string &mapFileName, const std::string &mapName) const override;
    std::optional<int16_t> bountyTargetMonster(const MonsterTable &monsterTable, uint32_t seed) const override;
    // A C-tier boss of a random arena family, raised by the banked levels less 2/3 of its B level, with 5-15 of its
    // kin around it, marked "Bounty" on the map and named after its affix.
    std::optional<BountyTarget> spawnBountyTarget(
        IGameplayWorldRuntime &world,
        float x,
        float y,
        float z,
        uint32_t seed) const override;
    bool bountyKillCounts(const ActorRulesetFacts &facts) const override;
    // MAW keeps one bounty per map and only that map's kill counts (BountyHunt.lua:241-261).
    bool bountyKillCountsElsewhere() const override;
    // Only a party member's killing blow counts; any other death drops the bounty (BountyHunt.lua:247-250, where the
    // killer must be a player: their projectiles count, the party's summons do not).
    bool bountyCancelledByOtherKill() const override;
    void bountyClaimed() const override;
    // The continents' maps MAW lists, with their levels and how far each was cleared, the game's mode and its
    // dimension and bounty records (MawProgress.cpp).
    bool hasProgressTab() const override;
    std::optional<RulesetProgressSummary> progressSummary(const RulesetProgressQuery &query) const override;
    // monTbl (zzMaw-Maps.lua:750-789): the C-tier families that are not wimps, by their table level, less two.
    int16_t arenaWaveMonster(int wave, const MonsterTable &monsterTable) const override;
    size_t arenaMinimumTypes() const override;
    int arenaDrawLevel(const MonsterTable::MonsterStatsEntry &stats, const MonsterTable &monsterTable,
        const MapStatsEntry &map) const override;
    // The outdoor maps (and Celeste and the Pit) never refill (zzMaw-Maps.lua:73-85).
    int mapRespawnDays(const MapStatsEntry &map) const override;
    std::optional<std::string> mapResetOffer(const std::string &mapFileName) const override;
    void resetMap(const std::string &mapFileName) const override;
    bool mapRefillForced(const std::string &mapFileName) const override;
    // A refill ends the dimension run on the map, unless the run's own first load refills it.
    void mapLoaded(const std::string &mapFileName, bool refilled) const override;
    // MAW has no monster immunities: the resistance its damage uses (modulo 1000, at most 200).
    std::string monsterResistanceText(int resistance, const ActorRulesetFacts &facts) const override;
    // MAW's panel (mawMonsterInspectNumbers).
    std::optional<MonsterInspectNumbers> inspectNumbers(const MonsterInspectQuery &query) const override;
    // Road to Insanity and Beyond Madness: a town names the first other town's bounty still open this month
    // (BountyHunt.lua:150-156).
    std::optional<std::pair<OpenBounty, std::string>> bountyElsewhere(
        const std::vector<OpenBounty> &openBounties) const override;
    // Every monster may drop an item, more often with its level and tier; the grade follows the family's base level
    // and the map's band, bosses always drop one; gold grows with the level (devdocs/maw/ITEMS.md §1.2). Rolled from
    // a stream keyed by the map visit and the actor, so a kill always drops the same loot.
    CorpseLoot corpseLoot(const CorpseLootContext &context) const override;
    // Four in five death drops are cancelled (events.MonsterDropItem), and of those left four in five again for Wasp
    // Wings, the four trophies and unenchanted reagents (zzMaw-Monsters.lua:3784-3788, 4042-4061).
    bool keepsDeathDrop(const ItemDefinition &item, std::mt19937 &rng) const override;
    // A monster without a corpse drops its crafting materials, reagents and dimension maps (the corpse's rolls) on the
    // ground; a water monster's go to the party (zzAlchemy.lua:1117, 1199-1229).
    LootWithoutCorpse lootWithoutCorpse(const CorpseLootContext &context) const override;
    // Regenerating bosses heal once hit, ever slower with each hit; Leecher bosses drain the party nearby; a Shadow
    // boss nearby cancels Wizard Eye (zzMaw-Monsters.lua eliteRegen, leecher; zzMaw-Spells.lua buff refresh).
    void updateMonsters(IGameplayWorldRuntime &world, float deltaSeconds) const override;
    // From Nightmare (zzMaw-Monsters.lua CanCastLloyd, CanCastTownPortal, CanSaveGame).
    bool teleportBlockedNearEnemies() const override;
    // Beyond Madness's Town Portal: "Madness is not a place for cowards" (SP:3728-3735).
    std::string teleportBlockedText(bool townPortal) const override;
    // 2 indoors, 10 with enemies near; outdoors 0, or 3 with enemies near; free on a completed map.
    int saveFoodCost(const std::string &mapFileName, bool indoor, bool enemiesNear) const override;

private:
    // makeBoss from the boss's base level (MawBossLevel): known where the monster's row and the map's levels are.
    bool makeBoss(ActorRulesetFacts &facts, uint64_t seed, uint8_t affix, int baseLevel) const;
    // The bosses of placeMapMonsters.
    bool placeMapBosses(const GameplayBolsterRuntimeContext &context, std::vector<MapMonsterPlacement> &monsters) const;
    // The Doom modes: each monster but the map's unique ones has a chance of √level × 2 % of a special attack from a
    // pool that grows with its level, in place of its own (MON:3691-3740).
    bool rollDoomSpecialAttacks(
        const GameplayBolsterRuntimeContext &context,
        std::vector<MapMonsterPlacement> &monsters) const;
    // Road to Insanity and Beyond Madness, on entering a map: a dungeon caps the food at 15 + monsters / 25 and holds
    // the rest back; the next outdoor map returns it (zzMaw-Monsters.lua:2172-2187).
    void capInsanityFood(IGameplayWorldRuntime &world) const;
    // Runtime only: maps reset at their entrance, whose next load refills them.
    mutable std::unordered_set<std::string> m_forcedRefills;
    // Runtime only: a seed per map refilled this session, so its bosses are rolled again.
    mutable std::unordered_map<std::string, uint64_t> m_refillSeeds;
    // Runtime only: what MAW keeps in its map variables between ticks. A reload starts it afresh.
    struct BossTrack
    {
        double healCarry = 0;
    };

    // A Broodlord, Broodling or Omnipotent boss seen alive, where it last stood.
    struct HatchingBoss
    {
        int16_t monsterId = 0;
        uint8_t affix = 0;
        float x = 0;
        float y = 0;
        float z = 0;
    };

    // What a special boss leaves when it dies (zzMaw-Monsters.lua:4098-4122): three Broodlings of the next tier
    // down (a Broodlord's of its own), and from an Omnipotent boss one boss per affix besides.
    void hatchBoss(IGameplayWorldRuntime &world, uint32_t actorId, const HatchingBoss &boss) const;

    MawRules &m_rules;
    // The map the boss tracks belong to.
    mutable std::string m_trackedMap;
    // The game day the current map was loaded on (its refill timer's start).
    mutable int32_t m_loadDay = 0;
    // The map just loaded whose used barrels and cauldrons the first update empties again.
    mutable std::string m_usedDecorationsMap;
    mutable std::unordered_map<uint32_t, HatchingBoss> m_hatchingBosses;
    mutable std::string m_hatchingMap;
    // The monsters seen alive on a summon-on-death dimension map, by actor id (their monster id).
    mutable std::unordered_map<uint32_t, int16_t> m_livingMonsters;
    // Runtime: the map Road to Insanity's food cap last ran on.
    mutable std::string m_foodCapMap;
    mutable std::unordered_map<uint32_t, BossTrack> m_bossTracks;
    mutable float m_regenerationSeconds = 0;
    mutable float m_auraSeconds = 0;
    mutable float m_weakenSeconds = 0;
    mutable float m_mapRegenerationSeconds = 0;
    mutable float m_completionSeconds = 0;
    // The Leecher drain each member owes below one point, hit points then spell points (amountHP/amountSP).
    mutable std::vector<std::pair<double, double>> m_leechCarry;
    // The map whose arrival was last announced (flight maps from Hard up).
    mutable std::string m_announcedMap;
};

// A monster's damage before the attack's own ratio (getMonsterDamage): the model's damage at its family level for the
// damage kind, scaled by its tier and boss multiplier. Physical attacks are sized against armour, every other kind
// against resistances.
double mawMonsterBaseDamage(
    const MawRules &rules, const ActorRulesetFacts &facts, int partyCount, CombatDamageType type);

// How far a map is cleared (checkMapCompletition, zzMaw-Monsters.lua:2568-2640): the slain share of its counted
// monsters (mdt15 counts one fewer) against 0.99^floor(n / 100), every one in Road to Insanity and Beyond Madness
// outdoors. A map whose remaining hostiles are all hidden counts as cleared; one without any has no share. The Arena
// is never cleared.
struct MawMapCompletion
{
    bool counts = false;
    double share = 0;
    double required = 1;
    // MAW's display: min(round(share x 1000 / required) / 10, 100).
    double percent = 0;
    bool complete = false;
    // The counted monsters the share is of (mdt15 one fewer).
    int counted = 0;
};

MawMapCompletion mawMapCompletion(const MapKillProgress &progress, bool insanityRules);

// What the HUD's map progress needs beside the kills (MawMonsterRules::mapProgress).
struct MawMapProgressFacts
{
    // Road to Insanity and Beyond Madness: an outdoor map needs every monster.
    bool insanityRules = false;
    // The slain of a dungeon rise again when the party leaves before 65 % (Nightmare and the challenge modes), and
    // whether this map is already safe from it (weakened).
    bool revivalRules = false;
    bool weakened = false;
    // Cleared since the last refill; completed (paid) before.
    bool cleared = false;
    bool completedBefore = false;
    // Austerity pays no crafting materials; Beyond Madness pays dimension runs the full reward.
    bool austerity = false;
    bool beyondMadness = false;
    // The map's dimension run (null: none).
    const MawDimensionRun *pDimensionRun = nullptr;
    // The Endless Arena's wave level (0: no bout) and its progress in percent (d42).
    int arenaLevel = 0;
    int arenaPercent = 0;
};

// The bar's numbers: MAW's normalised percent (100 at completion, kept full until the refill), slain of needed
// (ceil(required x n)), the revival mark at 65 % of the counted (raw share) in dungeons while it matters, and what the
// first completion pays. None for a map without counted monsters, or the Arena between bouts.
std::optional<RulesetMapProgress> mawMapProgress(const MapKillProgress &progress, const MawMapProgressFacts &facts);

// MAW's boss affixes in its SkillList order (zzMaw-Monsters.lua); stored on the actor as ActorRulesetFacts::bossAffix.
enum class MawBossAffix : uint8_t
{
    None = 0,
    Summoner,
    Venomous,
    Plagueborn,
    Fixator,
    Exploding,
    Thorn,
    Reflecting,
    Adamantite,
    Swapper,
    Regenerating,
    Puller,
    Leecher,
    Swift,
    Shadow,
    // MAW's special bosses (bosses.yml `special`): a Broodlord and its Broodlings, which hatch from each other as they
    // die, have no affix of their own; an Omnipotent boss has all fourteen above.
    Broodlord,
    Broodling,
    Omnipotent,
    // The affixes added later (MAW 8fbb48d1), rolled like the first fourteen but not part of an Omnipotent boss
    // (OmnipotentExcluded): immune to crowd control; up to twice the damage as its health runs out; named Cryptic
    // but fighting with a hidden other affix (ActorRulesetFacts::crypticAffix); 40 % of the party's weapon hits
    // miss it and its own hits cannot be dodged, and it drops four Horseshoes.
    Unstoppable,
    Berserker,
    Cryptic,
    Skilled,
};

std::string mawBossAffixName(MawBossAffix affix);
// The affix a boss fights with: a Cryptic boss's hidden one, otherwise its own (MAW's getBossSkill).
MawBossAffix mawBossEffectAffix(const ActorRulesetFacts &facts);
// Whether a monster's boss affix includes this one: the affix it fights with, and for an Omnipotent boss each of the
// first fourteen.
bool mawHasBossAffix(const ActorRulesetFacts &facts, MawBossAffix affix);
// Whether no crowd control holds the monster (an Unstoppable boss): spells, weapon stuns, Retaliation and the class
// abilities that stun, slow or hold.
bool mawIgnoresCrowdControl(const ActorRulesetFacts &facts);
// A Berserker boss's damage multiplier at its health: 2 - HP / max HP, from 1 at full health to 2 near death
// (getMonsterDamage, Estimates.lua:491-493).
double mawBerserkerDamageMultiplier(int currentHp, int maxHp);
}
