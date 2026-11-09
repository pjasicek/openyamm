#pragma once

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <unordered_set>

namespace OpenYAMM::Game
{
// A dimension map used on its target map (zzMaw-Maps.lua mapvars.mapAffixes): its affixes stay in force there until
// the map refills again.
struct MawDimensionRun
{
    // The active affixes (0 empty) and the power.
    std::array<uint8_t, 4> affixes = {};
    uint16_t power = 0;
    // The three monster families that replace the map's own (their A-tier monster ids).
    std::array<int16_t, 3> families = {};
    // The map item was used and the run's first load, which refills the map, is still to come.
    bool entering = false;
    // The run's map was cleared: its next dimension map was given.
    bool completed = false;
    // The Dimensional Maps quest tier the run counts for when cleared (0: none).
    int questTier = 0;

    int affixCount() const;
    bool operator==(const MawDimensionRun &) const = default;
};

// The Dimensional Maps topic (Global/zzMaw_DimensionalMapsQuest.lua vars.dimensionalMapsQuest).
struct MawDimensionQuest
{
    // The party level the next map is for; 0 until the topic is first asked.
    int tierLevel = 0;
    // The tier's map was given and not yet rewarded.
    bool mapGiven = false;
    bool cleared = false;
    // The cleared run's map level and map name, for the reward.
    int clearedLevel = 0;
    std::string clearedMapName;
    // A tier at the unlock level was rewarded: monsters may drop dimension maps.
    bool done = false;

    bool operator==(const MawDimensionQuest &) const = default;
};

// What the party last saw of a map it left (the Journal's Progress tab): its slain and counted monsters as the map's
// completion counts them, and the game day its monsters last refilled.
struct MawMapVisit
{
    int32_t slain = 0;
    int32_t counted = 0;
    int32_t lastRefillDay = 0;

    bool operator==(const MawMapVisit &) const = default;
};

// What a MAW game remembers besides the party and the maps (devdocs/maw/data/exp_curve.yml banked_levels,
// monster_scaling.yml level): the levels banked on each continent, which drive monster levels, and the dungeons that
// were completed or reset. Saved with MAW games only.
struct MawGameState
{
    // MAW's four continents: Jadame (MM8), Antagarich (MM7), Enroth (MM6) and Chedian (MM9), map table continents 1,
    // 2, 3 and 5. Levels are fractional.
    static constexpr size_t ContinentCount = 4;

    std::array<double, ContinentCount> continentLevels = {};
    // All bank experience so far and the MAW-curve level it amounts to; a gain moves the difference into the bank of
    // the continent where it was earned.
    double bankedExperience = 0;
    double bankedLevel = 0;
    // Lowercase map file name: times the dungeon was reset for harder monsters (+20 levels each).
    std::unordered_map<std::string, int> mapResetCounts;
    // Lowercase map file names whose completion reward was paid: once per game, and the dimension maps' pool.
    std::unordered_set<std::string> completedMaps;
    // Lowercase map file names cleared since their monsters last refilled (MAW's mapvars.completed): the HUD's 100 %,
    // the free Nightmare save, the bounty gate, the reset offer and Beyond Madness's boss chances read it; a refill or
    // a reset takes the map out.
    std::unordered_set<std::string> clearedSinceRefill;
    // Loot bad-luck protection (devdocs/maw/RANDOMS.md §4.2): what the Celestial, Legendary and Primordial upgrades and
    // the artifact roll have failed since they last succeeded, and how often each artifact (by item id) and each
    // legendary affix has dropped, so the rarer ones are favoured.
    double celestialPity = 0;
    double legendaryPity = 0;
    double primordialPity = 0;
    double artifactPity = 0;
    std::unordered_map<uint32_t, int> artifactDrops;
    std::unordered_map<uint32_t, int> legendaryAffixDrops;
    // What each crafting material's drop roll (by item id) has failed since it last succeeded (craftPityCounters).
    std::unordered_map<uint32_t, double> craftingPity;
    // The buff auras the party holds (CLASSES_SPELLS_SPEC.md §3): spell id to the holding member's index, or
    // FixedAuraHolder for an aura from a scroll, a pedestal or a temple.
    std::unordered_map<uint32_t, uint32_t> auraHolders;
    // Where each fixed aura came from: the lowercase map file of its scroll or pedestal, which entering another
    // outdoor map ends, or empty for a temple's, which leaving the map ends (SP:2693-2730).
    std::unordered_map<uint32_t, std::string> fixedAuraMaps;
    // Dimension maps by lowercase target map file name, the quest, and what the map kill drop has failed since it last
    // dropped (vars.mapDropFailures).
    std::unordered_map<std::string, MawDimensionRun> dimensionRuns;
    MawDimensionQuest dimensionQuest;
    double mapDropPity = 0;
    // Dimension maps dropped on each map since it last refilled (mapvars.mapsDropped).
    std::unordered_map<std::string, int> mapsDropped;
    // The unique items a shop bought, by item id: each sells once a game (SpecialItems.SellOnce).
    std::unordered_map<uint32_t, int> soldUniqueItems;
    // The party member (slot index) who takes the alchemy items when the party sorts (vars.alchemyPlayer), or -1.
    int32_t alchemistMember = -1;
    // Road to Insanity: the food a dungeon's cap held back, returned on the next outdoor map (vars.refundFood).
    int32_t heldFood = 0;
    // Beyond Madness: bosses rolled since the last Broodlord and Omnipotent one (vars.broodlordPityCounter,
    // vars.omnipotentPityCounter).
    double broodlordPity = 0;
    double omnipotentPity = 0;
    // The maps the party has left, by lowercase map file name (the Progress tab; saves before it list none), the
    // dimension runs cleared and the town bounties claimed in this game.
    std::unordered_map<std::string, MawMapVisit> mapVisits;
    int32_t dimensionRunsCleared = 0;
    int32_t bountiesClaimed = 0;
    // The barrels and cauldrons that raised a stat, by lowercase map file name: decor var index to the state they were
    // left in (empty). They stay so through refills and resets (vars.usedBarrels, zzMaw-Maps.lua:240-283).
    std::unordered_map<std::string, std::unordered_map<uint8_t, uint8_t>> usedStatDecorations;
    // Beyond Madness's death count as of the save, so a save moved to another installation (whose death ledger has no
    // line for the run) keeps its count (vars.MadnessDeathCounter, zzMaw-Monsters.lua:2385-2400).
    int32_t madnessDeaths = 0;

    // The holder of an aura no party member holds (MAW's string holders: Temple, scroll or pedestal).
    static constexpr uint32_t FixedAuraHolder = 0xFFFFFFFFu;

    // The bank index of a continent id from the map table (1, 2, 3 or 5); none for any other id.
    static std::optional<size_t> continentIndex(uint32_t continentId);

    void addBankedExperience(double experience, uint32_t continentId);
    double totalLevel() const;
    // The levels banked on this continent (0 for an id that is none of the four).
    double levelOn(uint32_t continentId) const;
    // The levels banked on every continent except this one (MAW getPartyLevel).
    double levelOutside(uint32_t continentId) const;
    int resetCount(const std::string &mapFileName) const;

    bool operator==(const MawGameState &) const = default;
};
}
