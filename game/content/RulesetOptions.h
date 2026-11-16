#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace OpenYAMM::Game
{
// The rules a game is played by: the Standard MMerge rules or an optional ruleset package such as MAW
// (devdocs/maw/HANDOFF.md §3.1). Chosen at new game and carried by the save.
inline constexpr const char *StandardRulesetId = "mmerge";
inline constexpr const char *MawRulesetId = "maw";

// The enum values are stored in saves; never renumber them.
enum class RulesetDifficulty : uint8_t
{
    Easy = 0,
    Normal = 1,
    Maw = 2,
    Hard = 3,
    Hell = 4,
    Nightmare = 5,
};

enum class RulesetProgression : uint8_t
{
    Free = 0,
    Horizontal = 1,
};

enum class RulesetChallengeMode : uint8_t
{
    None = 0,
    Doom = 1,
    RoadToInsanity = 2,
    BeyondMadness = 3,
    Austerity = 4,
};

// MAW's loot filter (level_generation/ui/maw_loot_progress_20261025, view A): a preset says which weapons, armour and
// jewellery turn into gold by rarity, the rarity above that once the item is far enough below the party's level.
enum class RulesetLootFilterPreset : uint8_t
{
    Off = 0,
    Soft = 1,
    Regular = 2,
    Strict = 3,
    VeryStrict = 4,
    Custom = 5,
};

// The kinds of item without a rarity, each turned into gold or not (RulesetLootFilter::goldKinds, a bit each).
enum class RulesetLootKind : uint8_t
{
    Wands = 0,
    Scrolls = 1,
    Potions = 2,
    Reagents = 3,
    Gems = 4,
};
inline constexpr size_t RulesetLootKindCount = 5;

// The item types a custom rule names (RulesetLootFilterRule::types, a bit each): weapons by skill, body armour by skill,
// the other armour slots, the two jewellery slots and the kinds without rarity. Stored in saves; never renumber.
enum class LootItemType : uint8_t
{
    Sword = 0,
    Dagger = 1,
    Axe = 2,
    Spear = 3,
    Mace = 4,
    Club = 5,
    Staff = 6,
    Bow = 7,
    Throwing = 8,
    Leather = 9,
    Chain = 10,
    Plate = 11,
    Shield = 12,
    Helm = 13,
    Belt = 14,
    Cloak = 15,
    Gauntlets = 16,
    Boots = 17,
    Ring = 18,
    Amulet = 19,
    Wands = 20,
    Scrolls = 21,
    Potions = 22,
    Reagents = 23,
    Gems = 24,
};
inline constexpr size_t LootItemTypeCount = 25;

// What becomes of a drop: kept, turned into gold, or left on the ground greyed. Stored in saves.
enum class LootFilterAction : uint8_t
{
    Keep = 0,
    Gold = 1,
    Ground = 2,
};

// A Custom filter's rule: the item types it names, the highest rarity it takes (1 Common .. 6 Primordial; the kinds
// without rarity ignore it) and, when not 0, how many levels below the party's the item must be.
struct RulesetLootFilterRule
{
    uint32_t types = 0;
    uint8_t rarityAtMost = 2;
    uint8_t levelsBelow = 0;
    LootFilterAction action = LootFilterAction::Gold;

    bool operator==(const RulesetLootFilterRule &) const = default;
};
inline constexpr size_t RulesetLootFilterMaxRules = 8;

struct RulesetLootFilter
{
    // Off until the player picks a preset: nothing a new game drops turns into gold unasked (OY-216).
    RulesetLootFilterPreset preset = RulesetLootFilterPreset::Off;
    uint8_t goldKinds = 0;
    // A filtered drop stays an item, greyed (no rarity glow), instead of turning into gold.
    bool leaveOnGround = false;
    // Custom only: the rules checked from the top, the first that fits deciding, and what becomes of a drop none fits.
    // Each rule carries its own action; goldKinds and leaveOnGround are the presets'.
    std::vector<RulesetLootFilterRule> rules;
    LootFilterAction otherwise = LootFilterAction::Keep;

    bool turnsKindIntoGold(RulesetLootKind kind) const
    {
        return (goldKinds & (1u << unsigned(kind))) != 0;
    }

    bool operator==(const RulesetLootFilter &) const = default;
};

// Player preferences rather than rules: they can change at any time.
struct RulesetPreferences
{
    bool homingProjectiles = true;
    bool friendlyFire = false;
    // Road to Insanity and Beyond Madness: a deep overkill dismisses the member (MAW's enableDisintegrate).
    bool disintegration = true;
    // The skill popup names the nearest teacher of the next mastery (MAW's Trainer Hints, off by default).
    bool trainerHints = false;
    // Bows, crossbows, thrown weapons and a dragon's breath do not shoot: the attack is the melee one, at its pace
    // (MAW's disableBow, a melee-only challenge; off by default).
    bool bowDisabled = false;
    RulesetLootFilter lootFilter;

    bool operator==(const RulesetPreferences &) const = default;
};

struct RulesetOptions
{
    RulesetDifficulty difficulty = RulesetDifficulty::Maw;
    RulesetProgression progression = RulesetProgression::Free;
    // Fixed at new game, like the randomizer.
    RulesetChallengeMode challengeMode = RulesetChallengeMode::None;
    bool randomizer = false;
    // The augmented solo run (devdocs/solo_action/README.md): a party of one played in first person with the solo HUD
    // and, under MAW, the talents. Chosen at new game, fixed for the adventure. It changes no rule of the ruleset:
    // presentation and the solo-only additions read it. Standard games keep it too (the options' other fields are
    // ignored there).
    bool soloRun = false;
    RulesetPreferences preferences;

    // Nightmare and the Doom modes cannot be left once chosen; Austerity keeps a changeable difficulty.
    bool difficultyLocked() const;
    bool operator==(const RulesetOptions &) const = default;
};

// The ruleset of one game. Standard games ignore the options.
// The key of a ruleset's package among a save's required content packages: "rulesets/<id>".
inline const std::string RulesetContentPackagePrefix = "rulesets/";

struct RulesetSelection
{
    std::string id = StandardRulesetId;
    RulesetOptions options;

    bool isStandard() const;
    bool operator==(const RulesetSelection &) const = default;
};

std::string_view rulesetDifficultyId(RulesetDifficulty difficulty);
std::string_view rulesetDifficultyName(RulesetDifficulty difficulty);
std::optional<RulesetDifficulty> parseRulesetDifficulty(std::string_view id);
std::string_view rulesetProgressionId(RulesetProgression progression);
std::string_view rulesetProgressionName(RulesetProgression progression);
std::optional<RulesetProgression> parseRulesetProgression(std::string_view id);
std::string_view rulesetChallengeModeId(RulesetChallengeMode challengeMode);
std::string_view rulesetChallengeModeName(RulesetChallengeMode challengeMode);
std::optional<RulesetChallengeMode> parseRulesetChallengeMode(std::string_view id);
// The progression a challenge mode plays with, when it fixes one (Beyond Madness is horizontal only).
std::optional<RulesetProgression> rulesetChallengeModeProgression(RulesetChallengeMode challengeMode);
// The difficulty a challenge mode sets: Doom, Road to Insanity and Beyond Madness play at Nightmare (MAW's bolster 600,
// above Nightmare's 300, so every rule of the harder difficulties applies); Austerity keeps the chosen one.
std::optional<RulesetDifficulty> rulesetChallengeModeDifficulty(RulesetChallengeMode challengeMode);
std::string_view rulesetLootFilterPresetId(RulesetLootFilterPreset preset);
std::string_view rulesetLootFilterPresetName(RulesetLootFilterPreset preset);
std::optional<RulesetLootFilterPreset> parseRulesetLootFilterPreset(std::string_view id);
// A preset with the kinds without rarity it turns into gold, keeping what becomes of a filtered drop.
RulesetLootFilter rulesetLootFilterWithPreset(RulesetLootFilterPreset preset, bool leaveOnGround = false);
// The settings row's value for the whole filter, so any change to it counts: "regular:2:gold", and a Custom filter's
// rules after a '|'.
std::string rulesetLootFilterValue(const RulesetLootFilter &filter);
// Saves before version 126 stored MAW's own filter, a rarity (0 off, 1 Common .. 6 Primordial) at or below which every
// drop turned into gold: the nearest preset.
RulesetLootFilter rulesetLootFilterFromLegacyRarity(uint8_t rarity);
// Applies colon-separated option ids in any order: difficulties, progressions, challenge modes, "randomizer",
// "friendlyfire" and "nobow" or "bow" (the preferences) ("hell:horizontal"). False on an unknown id.
bool applyRulesetOptionIds(std::string_view ids, RulesetOptions &options);
// False when a stored value is outside its enum, as in a damaged save.
bool rulesetOptionsValid(const RulesetOptions &options);

// The Load-screen badge, such as "MAW · Hell difficulty · Horizontal progression" or
// "MAW · Nightmare difficulty · Free progression · Doom"; empty for Standard.
std::string describeRulesetSelection(const RulesetSelection &selection, const std::string &rulesetName);
}
