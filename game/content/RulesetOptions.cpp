#include "game/content/RulesetOptions.h"

#include "engine/Localization.h"

#include <algorithm>
#include <array>
#include <cstddef>

namespace OpenYAMM::Game
{
namespace
{
struct OptionNames
{
    std::string_view id;
    std::string_view name;
};

constexpr std::array<OptionNames, 6> DifficultyNames = {{
    {"easy", Engine::trNoop("Easy")},
    {"normal", Engine::trNoop("Normal")},
    {"maw", Engine::trNoop("MAW")},
    {"hard", Engine::trNoop("Hard")},
    {"hell", Engine::trNoop("Hell")},
    {"nightmare", Engine::trNoop("Nightmare")},
}};

constexpr std::array<OptionNames, 2> ProgressionNames = {{
    {"free", Engine::trNoop("Free")},
    {"horizontal", Engine::trNoop("Horizontal")},
}};

constexpr std::array<OptionNames, 5> ChallengeModeNames = {{
    {"none", Engine::trNoop("None")},
    {"doom", Engine::trNoop("Doom")},
    {"road_to_insanity", Engine::trNoop("Road to Insanity")},
    {"beyond_madness", Engine::trNoop("Beyond Madness")},
    {"austerity", Engine::trNoop("Austerity")},
}};

constexpr std::array<OptionNames, 6> LootFilterPresetNames = {{
    {"off", Engine::trNoop("Off")},
    {"soft", Engine::trNoop("Soft")},
    {"regular", Engine::trNoop("Regular")},
    {"strict", Engine::trNoop("Strict")},
    {"very_strict", Engine::trNoop("Very strict")},
    {"custom", Engine::trNoop("Custom")},
}};
template <typename Enum, size_t Count>
std::optional<Enum> parseOption(const std::array<OptionNames, Count> &names, std::string_view id)
{
    for (size_t index = 0; index < names.size(); ++index)
    {
        if (names[index].id == id)
        {
            return Enum(index);
        }
    }

    return std::nullopt;
}

template <typename Enum, size_t Count>
const OptionNames &optionNames(const std::array<OptionNames, Count> &names, Enum value)
{
    const size_t index = static_cast<size_t>(value);
    return names[index < names.size() ? index : 0];
}
}

bool RulesetOptions::difficultyLocked() const
{
    return difficulty == RulesetDifficulty::Nightmare || rulesetChallengeModeDifficulty(challengeMode).has_value();
}

bool RulesetSelection::isStandard() const
{
    return id == StandardRulesetId;
}

std::string_view rulesetDifficultyId(RulesetDifficulty difficulty)
{
    return optionNames(DifficultyNames, difficulty).id;
}

std::string_view rulesetDifficultyName(RulesetDifficulty difficulty)
{
    return optionNames(DifficultyNames, difficulty).name;
}

std::optional<RulesetDifficulty> parseRulesetDifficulty(std::string_view id)
{
    return parseOption<RulesetDifficulty>(DifficultyNames, id);
}

std::string_view rulesetProgressionId(RulesetProgression progression)
{
    return optionNames(ProgressionNames, progression).id;
}

std::string_view rulesetProgressionName(RulesetProgression progression)
{
    return optionNames(ProgressionNames, progression).name;
}

std::optional<RulesetProgression> parseRulesetProgression(std::string_view id)
{
    return parseOption<RulesetProgression>(ProgressionNames, id);
}

std::string_view rulesetChallengeModeId(RulesetChallengeMode challengeMode)
{
    return optionNames(ChallengeModeNames, challengeMode).id;
}

std::string_view rulesetChallengeModeName(RulesetChallengeMode challengeMode)
{
    return optionNames(ChallengeModeNames, challengeMode).name;
}

std::optional<RulesetChallengeMode> parseRulesetChallengeMode(std::string_view id)
{
    return parseOption<RulesetChallengeMode>(ChallengeModeNames, id);
}

std::optional<RulesetProgression> rulesetChallengeModeProgression(RulesetChallengeMode challengeMode)
{
    if (challengeMode == RulesetChallengeMode::BeyondMadness)
    {
        return RulesetProgression::Horizontal;
    }

    return std::nullopt;
}

std::optional<RulesetDifficulty> rulesetChallengeModeDifficulty(RulesetChallengeMode challengeMode)
{
    if (challengeMode == RulesetChallengeMode::Doom || challengeMode == RulesetChallengeMode::RoadToInsanity
        || challengeMode == RulesetChallengeMode::BeyondMadness)
    {
        return RulesetDifficulty::Nightmare;
    }

    return std::nullopt;
}

std::string_view rulesetLootFilterPresetId(RulesetLootFilterPreset preset)
{
    return optionNames(LootFilterPresetNames, preset).id;
}

std::string_view rulesetLootFilterPresetName(RulesetLootFilterPreset preset)
{
    return optionNames(LootFilterPresetNames, preset).name;
}

std::optional<RulesetLootFilterPreset> parseRulesetLootFilterPreset(std::string_view id)
{
    return parseOption<RulesetLootFilterPreset>(LootFilterPresetNames, id);
}

RulesetLootFilter rulesetLootFilterWithPreset(RulesetLootFilterPreset preset, bool leaveOnGround)
{
    // Strict turns scrolls into gold as well, Very strict wands and scrolls.
    const auto bit = [](RulesetLootKind kind) { return uint8_t(1u << unsigned(kind)); };
    RulesetLootFilter filter;
    filter.preset = preset;
    filter.leaveOnGround = leaveOnGround;

    if (preset == RulesetLootFilterPreset::Strict || preset == RulesetLootFilterPreset::VeryStrict)
    {
        filter.goldKinds = bit(RulesetLootKind::Scrolls);
    }

    if (preset == RulesetLootFilterPreset::VeryStrict)
    {
        filter.goldKinds |= bit(RulesetLootKind::Wands);
    }

    return filter;
}

RulesetLootFilter rulesetLootFilterFromLegacyRarity(uint8_t rarity)
{
    // Off; Common: Soft; Uncommon: Regular; Rare: Strict; Epic and above: Very strict.
    constexpr std::array<RulesetLootFilterPreset, 7> Nearest = {RulesetLootFilterPreset::Off,
        RulesetLootFilterPreset::Soft, RulesetLootFilterPreset::Regular, RulesetLootFilterPreset::Strict,
        RulesetLootFilterPreset::VeryStrict, RulesetLootFilterPreset::VeryStrict, RulesetLootFilterPreset::VeryStrict};
    return rulesetLootFilterWithPreset(Nearest[std::min<size_t>(rarity, Nearest.size() - 1)]);
}

bool applyRulesetOptionIds(std::string_view ids, RulesetOptions &options)
{
    while (!ids.empty())
    {
        const size_t separator = ids.find(':');
        const std::string_view id = ids.substr(0, separator);
        ids = separator == std::string_view::npos ? std::string_view() : ids.substr(separator + 1);

        if (const std::optional<RulesetDifficulty> difficulty = parseRulesetDifficulty(id))
        {
            options.difficulty = *difficulty;
        }
        else if (const std::optional<RulesetProgression> progression = parseRulesetProgression(id))
        {
            options.progression = *progression;
        }
        else if (const std::optional<RulesetChallengeMode> challengeMode = parseRulesetChallengeMode(id))
        {
            options.challengeMode = *challengeMode;
        }
        else if (id == "randomizer")
        {
            options.randomizer = true;
        }
        else if (id == "friendlyfire")
        {
            options.preferences.friendlyFire = true;
        }
        else if (id == "nobow" || id == "bow")
        {
            options.preferences.bowDisabled = id == "nobow";
        }
        else
        {
            return false;
        }
    }

    // A challenge mode's own difficulty and progression win over the ids given beside it.
    options.difficulty = rulesetChallengeModeDifficulty(options.challengeMode).value_or(options.difficulty);
    options.progression = rulesetChallengeModeProgression(options.challengeMode).value_or(options.progression);
    return true;
}

bool rulesetOptionsValid(const RulesetOptions &options)
{
    return static_cast<size_t>(options.difficulty) < DifficultyNames.size()
        && static_cast<size_t>(options.progression) < ProgressionNames.size()
        && static_cast<size_t>(options.challengeMode) < ChallengeModeNames.size()
        && static_cast<size_t>(options.preferences.lootFilter.preset) < LootFilterPresetNames.size()
        && options.preferences.lootFilter.goldKinds < (1u << RulesetLootKindCount);
}

std::string describeRulesetSelection(const RulesetSelection &selection, const std::string &rulesetName)
{
    if (selection.isStandard())
    {
        return {};
    }

    // The ruleset's name (ruleset.yml English, or already shown text from the save list) and its options, each in
    // the interface language.
    std::string badge = rulesetName.empty() ? selection.id : Engine::localizeKnown(rulesetName);
    badge += " · ";
    badge += Engine::tr("{difficulty} difficulty",
        {{"difficulty", Engine::tr(rulesetDifficultyName(selection.options.difficulty))}});
    badge += " · ";
    badge += Engine::tr("{progression} progression",
        {{"progression", Engine::tr(rulesetProgressionName(selection.options.progression))}});

    if (selection.options.challengeMode != RulesetChallengeMode::None)
    {
        badge += " · ";
        badge += Engine::tr(rulesetChallengeModeName(selection.options.challengeMode));
    }

    if (selection.options.randomizer)
    {
        badge += " · ";
        badge += Engine::tr("Randomizer");
    }

    return badge;
}
}
