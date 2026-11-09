#pragma once

#include "game/gameplay/GameplayBolsterRuntime.h"
#include "game/rules/CorpseLoot.h"
#include "game/rules/MonsterInspect.h"
#include "game/rules/RulesetProgress.h"

#include <optional>
#include <utility>
#include <random>
#include <span>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class IGameplayWorldRuntime;
class Party;
struct ItemDefinition;
struct MapStatsEntry;
struct MonsterEntry;

// A monster as its map first places it, for the map-wide choices of a ruleset.
struct MapMonsterPlacement
{
    const MonsterTable::MonsterStatsEntry *pStats = nullptr;
    // Named NPCs and unique monsters never become bosses.
    bool named = false;
    bool hostile = false;
    ActorRulesetFacts *pFacts = nullptr;
    // The place_mon name of a unique monster (0 for none).
    int32_t uniqueNameId = 0;
    // The actor runs a Lua behaviour (MM9's Dragon King, Njam): never a boss either.
    bool scripted = false;
};

// A slain monster whose carried loot the rules size.
// What map scripts may ask of the rules (evt.RulesetInfo): MAW's difficulty (0 Easy to 5 Nightmare) and the bolster
// level of the current continent, which its scripts scale rewards by.
struct RulesetScriptInfo
{
    std::string rulesetId = "mmerge";
    int difficulty = 0;
    int bolsterLevel = 0;
    // A MAW dimension-map run is on the current map.
    bool dimensionRun = false;
    // The game's challenge mode id ("none", "doom", "road_to_insanity", "beyond_madness", "austerity"), for content
    // that only one mode has.
    std::string challengeMode = "none";
};

// A map's clearing progress as the HUD's progress bar shows it (MonsterRules::mapProgress,
// level_generation/ui/maw_map_progress_20261025 option A).
struct RulesetMapProgress
{
    enum class Kind : uint8_t
    {
        Map,
        // A dimension-map run on the map: its own hue, power and affix count.
        DimensionRun,
        // The Endless Arena: never completed, its wave level and progress instead.
        Arena,
    };

    Kind kind = Kind::Map;
    // How full the bar is, 0-100, as the rules round it (MAW: one decimal, 100 exactly when the map completes).
    double percent = 0;
    // Cleared since the last refill: the bar stays full and gold.
    bool complete = false;
    int slain = 0;
    int counted = 0;
    // The slain the map needs to complete and the share of the counted that is.
    int needed = 0;
    double requiredShare = 1;
    // Living hostiles the map hides, not counted.
    int hidden = 0;
    // Whether the slain rise again when the party leaves too early, the slain that stops it, where that is on the bar
    // (0-1) and whether it is passed.
    bool revival = false;
    int revivalSlain = 0;
    float revivalPosition = 0;
    bool revivalPassed = false;
    // What the first completion gives (empty: nothing), or that it was given.
    std::string reward;
    bool rewardPaid = false;
    int dimensionPower = 0;
    int dimensionAffixes = 0;
    int arenaLevel = 0;
};

// A town's bounty still open this month: the map that gave it and its monster.
struct OpenBounty
{
    std::string mapFileName;
    int16_t monsterId = 0;
    // The affix of the boss the rules spawned (0: none), which its name carries.
    uint8_t bossAffix = 0;
};

// A bounty target the rules placed: its monster id, its boss affix (0: none) and the journal map note marking where
// it was placed (empty: none).
struct BountyTarget
{
    int16_t monsterId = 0;
    uint8_t bossAffix = 0;
    std::string mapNote;
};

struct LootWithoutCorpse
{
    std::vector<CorpseLoot::ExtraItem> items;
    bool toParty = false;
};

struct CorpseLootContext
{
    const MonsterTable::MonsterStatsEntry *pStats = nullptr;
    const MonsterTable *pMonsterTable = nullptr;
    const ActorRulesetFacts *pFacts = nullptr;
    // MMMerge's bolster reward multiplier of the actor.
    float bolsterRewardMultiplier = 1.0f;
    const MapStatsEntry *pMap = nullptr;
    // What keys the corpse's rolls: the map visit's seed (new when the map refills) and the actor's index on it.
    uint32_t visitSeed = 0;
    uint32_t actorIndex = 0;
    // The party that made the kill (its size and alchemists).
    const Party *pParty = nullptr;
    // The actor's place-monster name (1-219: a unique monster), 0 for none.
    uint32_t uniqueNameId = 0;
    CorpseLootPart part = CorpseLootPart::All;
};

// How a monster's numbers are set when it spawns or its map loads: level, hit points, armour, damage, speed, spells and
// rewards (devdocs/maw/HANDOFF.md §3.5). This class is the Standard rules (MMMerge's bolster); a ruleset that sizes
// monsters differently derives from it.
class MonsterRules
{
public:
    virtual ~MonsterRules() = default;

    virtual GameplayMonsterBolsterResult resolveMonster(
        const GameplayBolsterRuntimeContext &context,
        const MonsterTable::MonsterStatsEntry &stats,
        const MonsterEntry *pMonsterEntry) const;
    // Map-wide choices when a map's monsters are first placed (MAW: bosses), after each was resolved. True when facts
    // changed, so the world resolves those actors again. Standard changes nothing.
    virtual bool placeMapMonsters(
        const GameplayBolsterRuntimeContext &context,
        std::vector<MapMonsterPlacement> &monsters) const;
    // Turns a resolved monster into a boss with the rolls `seed` draws (MAW: an affix and stronger numbers), with the
    // given affix instead of a rolled one when it is not 0; the world resolves it again. Standard has no bosses: false.
    virtual bool makeBoss(ActorRulesetFacts &facts, uint64_t seed, uint8_t affix) const;
    // The encounter counts and tier mix a map spawns with (MAW: more and stronger monsters on harder difficulties).
    virtual void adjustMapEncounters(MapStatsEntry &map) const;
    // The map whose load begins, as its assets are about to be read (MAW: it becomes the rules' current map, and a
    // dimension map's monster families replace its own, so their art loads with it). Standard: nothing.
    virtual void enterMap(MapStatsEntry &map, const MonsterTable &monsterTable) const;
    // The tier ('A' to 'C') an encounter spawn takes after the map's rules (MAW: a dimension map's affix raises some);
    // `seed` keys the roll. Standard: the rolled tier.
    virtual char spawnTier(const MapStatsEntry &map, char tier, uint32_t seed) const;
    // An NPC topic the rules run (evt.RulesTopic): what the NPC says, or nothing when the rules have no such topic.
    virtual std::optional<std::string> rulesTopic(const std::string &topic, Party &party) const;
    virtual RulesetScriptInfo scriptInfo(uint32_t continentId) const;
    // Town bounties (BountyHuntRuntime). The reward for slaying the monster. Standard: its level x 100.
    virtual uint32_t bountyReward(const MonsterTable::MonsterStatsEntry &stats) const;
    // Why the town gives no new bounty yet (MAW: the town is not cleared); nothing when it may.
    virtual std::optional<std::string> bountyRefusal(const IGameplayWorldRuntime &world) const;
    // The same for a hunt posted on another map (an MM9 Jarl's region), by its file and name.
    virtual std::optional<std::string> bountyRefusalForMap(
        const std::string &mapFileName, const std::string &mapName) const;
    // The monster this month's target will be, by the hunt's seed, as spawnBountyTarget picks it; nothing leaves the
    // pick to the engine (Standard).
    virtual std::optional<int16_t> bountyTargetMonster(const MonsterTable &monsterTable, uint32_t seed) const;
    // Chooses and places this month's target near the point; nothing leaves both to the engine (Standard).
    virtual std::optional<BountyTarget> spawnBountyTarget(
        IGameplayWorldRuntime &world,
        float x,
        float y,
        float z,
        uint32_t seed) const;
    // Whether this slain monster of the bounty's kind fulfils it (MAW: only the boss). Standard: always.
    virtual bool bountyKillCounts(const ActorRulesetFacts &facts) const;
    // Whether such a kill also fulfils other towns' bounties on the same monster (MAW: only the current map's).
    // Standard: yes.
    virtual bool bountyKillCountsElsewhere() const;
    // Whether the target slain by anyone but a party member (an ally, another monster, a trap) calls the bounty off
    // (MAW). Standard: any death fulfils it.
    virtual bool bountyCancelledByOtherKill() const;
    // A town bounty's reward was claimed (MAW counts them for the Journal's Progress tab). Standard: nothing.
    virtual void bountyClaimed() const;
    // The Journal's Progress tab (MAW): whether the Journal has it, and its contents, built when the tab opens.
    // Standard: none, and the Journal keeps four tabs.
    virtual bool hasProgressTab() const;
    virtual std::optional<RulesetProgressSummary> progressSummary(const RulesetProgressQuery &query) const;
    // The monster family the Endless Arena brings in its wave (1-based; MAW: the C-tier families by level, cycling),
    // as its B monster id; 0 without an Endless Arena.
    virtual int16_t arenaWaveMonster(int wave, const MonsterTable &monsterTable) const;
    // The fewest monster types an Arena bout draws from: types nearest the bout's level range join when fewer lie in it
    // (MAW: 12, MawCore/Fixes.lua:87-107). Standard: none.
    virtual size_t arenaMinimumTypes() const;
    // The level an Arena bout draws a monster type by: the original engine reads the table's level after the ruleset
    // has set it for the map (MAW: d42's six-fold levels, at most 255). Standard: the table's.
    virtual int arenaDrawLevel(
        const MonsterTable::MonsterStatsEntry &stats, const MonsterTable &monsterTable, const MapStatsEntry &map) const;
    // Days after which a left map refills its monsters (0: never). Standard: the map table's.
    virtual int mapRespawnDays(const MapStatsEntry &map) const;
    // Whether the party may reset a map it is about to enter (MAW: a completed dungeon, except in Road to Insanity and
    // Beyond Madness), and what it says. Standard: no.
    virtual std::optional<std::string> mapResetOffer(const std::string &mapFileName) const;
    // Resets the map: its next load refills it as on the first visit, with the rules' harder numbers.
    virtual void resetMap(const std::string &mapFileName) const;
    // Whether the map's next load must refill it (MAW: a reset, a dimension map); the load clears it.
    virtual bool mapRefillForced(const std::string &mapFileName) const;
    // A gameplay load of the map is under way, and whether it refills the map; it clears a forced refill.
    virtual void mapLoaded(const std::string &mapFileName, bool refilled) const;
    // Whether nearby enemies stop Lloyd's Beacon and Town Portal (MAW from Nightmare). Standard: never.
    virtual bool teleportBlockedNearEnemies() const;
    // What a Town Portal or Lloyd's Beacon refused that way says. Standard: "Can't teleport now".
    virtual std::string teleportBlockedText(bool townPortal) const;
    // Food a manual save costs on this map (MAW from Nightmare). Standard: none.
    virtual int saveFoodCost(const std::string &mapFileName, bool indoor, bool enemiesNear) const;
    // What the rules do to the map's monsters and the party each frame of play (MAW: boss auras and regeneration).
    // Standard: nothing.
    virtual void updateMonsters(IGameplayWorldRuntime &world, float deltaSeconds) const;
    // The map's clearing progress the HUD's progress bar shows (MAW: the slain share against its threshold, the
    // revival mark, dimension runs and the Endless Arena). Standard: none, so no bar.
    virtual std::optional<RulesetMapProgress> mapProgress(const IGameplayWorldRuntime &world) const;
    // Whether a monster of the map counts toward its clearing (MAW: not those a world's balance file leaves out, as
    // MM9's sea monsters). Standard: every one.
    virtual bool countsForMapCompletion(const MapStatsEntry &map, const MonsterTable::MonsterStatsEntry &stats) const;
    // How much of a map's pack reserve joins it at a fill (MapDeltaData::packReserve: the entries whose fromFactor this
    // reaches; MAW: its difficulty's density in MM9). Standard: 1, none.
    virtual double packDensityFactor(const MapStatsEntry &map) const;
    // Whether a refill leaves the map's used MM9 barrels empty (MAW's used barrels, DEVIATIONS 57: what raised a stat
    // stays empty). Standard: a refill fills them again.
    virtual bool keepsUsedBarrelsThroughRefill() const;
    // Just before the party leaves the map (MAW's Nightmare: the slain of an indoor map rise again). Standard: nothing.
    virtual void leaveMap(IGameplayWorldRuntime &world) const;
    // A barrel or cauldron of the map (its decor var, left in `emptyState`) raised a party member's base stat or
    // resistance (MAW: it stays empty from now on, even through refills). Standard: nothing.
    virtual void decorationRaisedStats(const std::string &mapFileName, uint8_t decorVarIndex, uint8_t emptyState) const;
    // The map's decoration states were renumbered (a save from before MMerge's campfire list): `remap` gives each old
    // index its new one, or -1 (legacyCampFireDecorVarRemap). MAW: moves the decorations it remembers. Standard:
    // nothing.
    virtual void decorationsRenumbered(const std::string &mapFileName, std::span<const int16_t> remap) const;
    // What a slain monster carries (MAW: drop chance, item grade and gold by its level, rolls keyed by the kill).
    // Standard: the monster table's loot, scaled by MMMerge's bolster.
    virtual CorpseLoot corpseLoot(const CorpseLootContext &context) const;
    // Whether a monster's death drop (monster_death_drops.txt) that won its table roll still drops (MAW thins them
    // out). Standard: always, without a draw.
    virtual bool keepsDeathDrop(const ItemDefinition &item, std::mt19937 &rng) const;
    // What a slain monster that leaves no corpse still drops, rolled as its corpse's would be (MAW: its crafting
    // materials, reagents and dimension maps), and whether it goes straight to the party (MAW: the water monsters,
    // whose drops would sink). Standard: nothing, without a draw.
    virtual LootWithoutCorpse lootWithoutCorpse(const CorpseLootContext &context) const;
    // Icons beside the actor's floating health bar (MAW: a boss's skull, then its affix's badge); the first goes left
    // of the bar, the rest right. Standard: none.
    virtual std::vector<std::string> actorBadges(const ActorRulesetFacts &facts) const;
    // How much larger the actor is drawn (sprite and model; its collision stays). Standard: 1.
    virtual float actorDrawScale(const ActorRulesetFacts &facts, bool indoor) const;
    // The name an actor shows (MAW: a boss's affix before the monster's name).
    virtual std::string actorDisplayName(const ActorRulesetFacts &facts, const std::string &name) const;
    // A monster resistance as the inspect panel shows it. Standard: 200 and above is an immunity.
    virtual std::string monsterResistanceText(int resistance, const ActorRulesetFacts &facts) const;
    // The rules' own numbers for the monster inspect panel (MAW: level, damage after the viewer's defences,
    // experience). Standard: none, the panel shows the monster table's.
    virtual std::optional<MonsterInspectNumbers> inspectNumbers(const MonsterInspectQuery &query) const;
    // The open bounty of another town that a town names instead of giving a new one, with that town's map name
    // (MAW's Road to Insanity: one open bounty at a time). Standard: nothing, every town gives its own.
    virtual std::optional<std::pair<OpenBounty, std::string>> bountyElsewhere(
        const std::vector<OpenBounty> &openBounties) const;
};
}
