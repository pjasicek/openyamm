#include "game/rules/maw/MawExperienceRules.h"

#include "game/items/ItemGenerator.h"
#include "game/party/Party.h"
#include "game/party/SkillData.h"
#include "game/rules/RandomStreams.h"
#include "game/rules/maw/MawCombatFormulas.h"
#include "game/rules/maw/MawExperienceCurve.h"
#include "game/rules/maw/MawItemData.h"
#include "game/rules/maw/MawRules.h"
#include "game/rules/maw/MawSkillFormulas.h"
#include "game/tables/ItemTable.h"
#include "game/tables/MapStats.h"

#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
std::string lowercase(std::string text)
{
    for (char &character : text)
    {
        character = char(std::tolower(static_cast<unsigned char>(character)));
    }

    return text;
}

double unitDraw(RandomStream &stream)
{
    return double(stream() >> 11) / double(1ull << 53);
}

bool receivesKillExperience(const Character &member)
{
    return !member.conditions.test(size_t(CharacterCondition::Dead))
        && !member.conditions.test(size_t(CharacterCondition::Eradicated));
}

bool conscious(const Character &member)
{
    return receivesKillExperience(member) && !member.conditions.test(size_t(CharacterCondition::Unconscious))
        && !member.conditions.test(size_t(CharacterCondition::Petrified));
}
}

MawExperienceRules::MawExperienceRules(MawRules &rules)
    : m_rules(rules)
{
}

uint64_t MawExperienceRules::experienceForNextLevel(uint32_t level) const
{
    // MAW clamps the requirement below 2^31, which makes training free from level 863 (README §6); we do not.
    return uint64_t(mawRound(mawExperienceForLevel(double(level) + 1)));
}

int MawExperienceRules::questGoldBonus(int gold, uint32_t continentId) const
{
    const double partyLevel = m_rules.state().levelOutside(continentId);
    return gold > 0 ? int(std::floor(gold * partyLevel / 100 + 250 * partyLevel)) : 0;
}

int64_t MawExperienceRules::eventExperience(Party &party, int64_t value, uint32_t continentId) const
{
    if (value <= 0)
    {
        return value;
    }

    const double partyLevel = m_rules.options().challengeMode == RulesetChallengeMode::BeyondMadness
        ? m_rules.state().totalLevel()
        : m_rules.state().levelOutside(continentId);
    const double total = double(value) * (1 + partyLevel / 100) + 500 * partyLevel;
    const double partyCount = double(std::max<size_t>(1, party.members().size()));
    m_rules.state().addBankedExperience(total / partyCount, continentId);
    return int64_t(std::min(std::floor(total * 5 / partyCount), double(std::numeric_limits<int32_t>::max())));
}

uint32_t MawExperienceRules::grantKillExperience(Party &party, const MonsterKillReward &kill) const
{
    // The party's allies are worth nothing (zzMaw-Monsters.lua:4062-4065).
    if (kill.partyAlly)
    {
        return 0;
    }

    // A monster the ruleset never resolved (no facts) is worth what the table says.
    if (kill.facts.empty())
    {
        return ExperienceRules::grantKillExperience(party, kill);
    }

    // A kill by a monster fighting for the party (a wisp, the reanimated) gives each conscious member an equal share
    // of the monster's experience: no toughness ratio, cap or bank (zzMaw-Monsters.lua:4082-4095).
    if (kill.byPartyAlly)
    {
        const std::vector<Character> &members = party.members();
        const size_t consciousCount = size_t(std::count_if(members.begin(), members.end(), conscious));

        if (consciousCount == 0)
        {
            return 0;
        }

        const int64_t share = int64_t(std::floor(double(kill.facts.experience) / consciousCount));
        uint32_t grantedExperience = 0;

        for (size_t memberIndex = 0; memberIndex < members.size(); ++memberIndex)
        {
            if (conscious(members[memberIndex]))
            {
                const uint64_t experienceBefore = members[memberIndex].experience;
                party.addExperienceToMember(memberIndex, share);
                grantedExperience += uint32_t(members[memberIndex].experience - experienceBefore);
            }
        }

        return grantedExperience;
    }

    // Risen monsters give nothing in Road to Insanity and Beyond Madness (zzzMaw_Experience.lua:172-176); in
    // Nightmare and Doom their full experience, as MAW's kill hook resets it (DEVIATIONS 105).
    const RulesetChallengeMode mode = m_rules.options().challengeMode;

    if (m_rules.madnessRewardlessMap(m_rules.currentMap())
        || (kill.facts.risen
            && (mode == RulesetChallengeMode::RoadToInsanity || mode == RulesetChallengeMode::BeyondMadness)))
    {
        return 0;
    }

    const std::vector<Character> &members = party.members();
    const size_t receiverCount = std::max<size_t>(
        1, size_t(std::count_if(members.begin(), members.end(), receivesKillExperience)));
    const double experience = mawRound(double(kill.facts.experience) / receiverCount);
    double bankedExperience = 0;
    uint32_t grantedExperience = 0;

    for (size_t memberIndex = 0; memberIndex < members.size(); ++memberIndex)
    {
        const Character &member = members[memberIndex];

        if (!receivesKillExperience(member))
        {
            continue;
        }

        const MawMemberKillExperience share =
            mawMemberKillExperience(m_rules, member, int(members.size()), experience, kill.maxHp);
        const uint64_t experienceBefore = member.experience;
        party.addExperienceToMember(memberIndex, int64_t(share.award));
        grantedExperience += uint32_t(member.experience - experienceBefore);
        bankedExperience += share.award;
    }

    // The Endless Arena banks no levels (zzzMaw_Experience.lua:213-216).
    if (lowercase(m_rules.currentMap()) != "d42.blv")
    {
        m_rules.state().addBankedExperience(bankedExperience / 5, kill.continentId);
    }

    return grantedExperience;
}

MawMemberKillExperience mawMemberKillExperience(
    const MawRules &rules,
    const Character &member,
    int partySize,
    double experience,
    int monsterMaxHp)
{
    MawBalanceModel &model = rules.model(std::max(1, partySize));
    // How tough the monster is for this member: its HP over the HP of a monster of the member's level. The dimension
    // +HP affix stays out: MAW's ratio reads the health without it (zzzMaw_Experience.lua:191, DEVIATIONS 59).
    const double memberLevel =
        std::max(1.0, std::min(mawLevelForExperience(member.experience), rules.state().totalLevel()));
    const double healthAffix = rules.mapAffix(MawMapAffix::MonsterHealth).value_or(0);
    const double healthRatio = monsterMaxHp / (1 + healthAffix / 100) / model.monsterHealth(memberLevel);
    MawMemberKillExperience share;
    share.award = std::min(experience * healthRatio, (member.level + 1) * 1000.0);
    return share;
}

std::string MawExperienceRules::rewardMapProgress(Party &party, const MapKillProgress &progress) const
{
    MawGameState &state = m_rules.state();
    const std::string mapFileName = lowercase(progress.mapFileName);
    const auto run = state.dimensionRuns.find(mapFileName);
    const bool openRun = run != state.dimensionRuns.end() && !run->second.completed;
    const RulesetOptions &options = m_rules.options();
    const bool insanity = options.challengeMode == RulesetChallengeMode::RoadToInsanity
        || options.challengeMode == RulesetChallengeMode::BeyondMadness;
    const bool madness = options.challengeMode == RulesetChallengeMode::BeyondMadness;
    const bool doom = insanity || options.challengeMode == RulesetChallengeMode::Doom;

    if ((state.completedMaps.contains(mapFileName) && !openRun && state.clearedSinceRefill.contains(mapFileName))
        || !mawMapCompletion(progress, insanity).complete)
    {
        return {};
    }

    // Cleared since the last refill (MAW's mapvars.completed): every clear, a re-clear after a refill or a reset too.
    state.clearedSinceRefill.insert(mapFileName);

    if (state.completedMaps.contains(mapFileName) && !openRun)
    {
        return {};
    }

    // A dimension map's map was completed before: no second reward, but the quest counts it and, once the quest is
    // done, the next map drops (zzMaw-Monsters.lua:2646-2700). Beyond Madness never takes this branch: its runs pay
    // the full reward below and drop no next map.
    if (state.completedMaps.contains(mapFileName) && !madness)
    {
        return completeDimensionRun(party, run->second);
    }

    const std::array<double, 3> band = m_rules.mapLevels().band(mapFileName);
    double mapLevel = (band[0] + band[1] + band[2]) / 3;
    double bolster = options.progression == RulesetProgression::Horizontal ? mapLevel * 2 : 0;

    if (madness)
    {
        bolster = m_rules.mapLevels().madnessLevel(mapFileName);
    }

    // A dimension run's level is its power x 10 (zzMaw-Monsters.lua:2713-2715).
    if (openRun)
    {
        bolster = run->second.power * 10.0;
    }

    double slain = progress.slainMonsters;
    slain *= doom ? 0.5 : options.difficulty == RulesetDifficulty::Nightmare ? 0.67 : 1;
    slain *= insanity ? 0.8 : 1;
    mapLevel = std::clamp(mapLevel, 1.0, 100.0);
    double experience = std::ceil(std::pow(slain, 0.7) * (mapLevel * 20 + std::pow(mapLevel, 1.8)) / 3
                                  * (bolster + mapLevel) / mapLevel / 1000) * 1000;
    double gold = std::ceil(std::pow(experience, 0.9) / 1000) * 1000;

    if (madness)
    {
        // Twice on a plain map, half on a dimension run (zzMaw-Monsters.lua:2730-2736).
        experience = std::ceil(std::pow(slain, 0.7) * (bolster * 20 + std::pow(bolster, 1.8)) / 3 / 1000) * 1000
            * (openRun ? 0.5 : 2);
        gold = mawRound(experience / 3 / 1000) * 1000;
    }

    state.completedMaps.insert(mapFileName);

    if (openRun)
    {
        run->second.completed = true;
        ++state.dimensionRunsCleared;
    }

    state.addBankedExperience(experience, progress.continentId);
    party.addGold(int(gold));
    const size_t memberCount = std::max<size_t>(1, party.members().size());
    const double memberExperience = mawRound(experience * 5 / double(memberCount) / 1000) * 1000;

    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        party.addExperienceToMember(memberIndex, int64_t(memberExperience));
    }

    const std::string rewardText = "Map Completed! You gain " + std::to_string(int64_t(memberExperience)) + " Exp"
        + (options.challengeMode == RulesetChallengeMode::Austerity ? " and " : ", ") + std::to_string(int64_t(gold))
        + " Gold";

    if (party.itemTable() == nullptr)
    {
        return rewardText;
    }

    // A dimension run gives one crafting item by its affix count, in every mode (zzMaw-Monsters.lua:2743-2751).
    if (openRun)
    {
        static constexpr std::array<uint32_t, 5> RunRewards = {0, 1070, 1061, 1062, 1065};
        const uint32_t itemId = RunRewards[std::min<size_t>(run->second.affixCount(), RunRewards.size() - 1)];

        if (itemId != 0 && party.itemTable()->get(itemId) != nullptr)
        {
            party.tryGrantInventoryItem(
                ItemGenerator::makeInventoryItem(itemId, *party.itemTable(), ItemGenerationMode::Generic));
            return rewardText + " and Crafting Materials";
        }

        return rewardText;
    }

    if (options.challengeMode == RulesetChallengeMode::Austerity)
    {
        return rewardText;
    }

    // A Crafting Cube and two gems of tier min(ceil((map level + bolster) / 25 + 0.5), 16) (MON:2568-2797).
    const MawCraftingData &crafting = m_rules.craftingData();
    std::vector<uint32_t> rewards = crafting.mapCompletionItems();
    const int gemTier = std::min(int(std::ceil((mapLevel + bolster) / 25 + 0.5)), crafting.gemDropMaxTier());

    for (int gem = 0; gem < crafting.mapCompletionGems(); ++gem)
    {
        rewards.push_back(crafting.gemItemId(std::max(1, gemTier)));
    }

    for (uint32_t itemId : rewards)
    {
        if (itemId != 0 && party.itemTable()->get(itemId) != nullptr)
        {
            party.tryGrantInventoryItem(
                ItemGenerator::makeInventoryItem(itemId, *party.itemTable(), ItemGenerationMode::Generic));
        }
    }

    return rewardText + " and Crafting Materials";
}

std::string MawExperienceRules::completeDimensionRun(Party &party, MawDimensionRun &run) const
{
    MawGameState &state = m_rules.state();
    MawDimensionQuest &quest = state.dimensionQuest;
    const MawDimensionData &data = m_rules.dimensionData();
    const MapStatsEntry *pMap =
        m_rules.mapTable() != nullptr ? m_rules.mapTable()->findByFileName(m_rules.currentMap()) : nullptr;
    run.completed = true;
    ++state.dimensionRunsCleared;

    if (quest.mapGiven && !quest.cleared && run.questTier == quest.tierLevel && pMap != nullptr)
    {
        quest.cleared = true;
        quest.clearedLevel = mawDimensionMapLevel(run.power, m_rules.mapLevels().band(pMap->fileName));
        quest.clearedMapName = pMap->name;
    }

    std::string text = "Dungeon Completed!";

    if (!quest.done || party.itemTable() == nullptr || party.itemTable()->get(data.mapItemId()) == nullptr)
    {
        return text;
    }

    // The next map: the second affix always, the third at 60 %, the fourth at 50 % and the first at 40 %, all
    // active, one power more.
    const std::string mapFileName = pMap != nullptr ? lowercase(pMap->fileName) : m_rules.currentMap();
    RandomStream stream(randomStreamKey(m_rules.randomRootSeed(), RandomDomain::DimensionCompletion,
        randomNameKey(mapFileName), uint64_t(state.mapsDropped[mapFileName]), run.power));
    const std::array<bool, 4> slots = {
        unitDraw(stream) < 0.4, true, unitDraw(stream) < 0.6, unitDraw(stream) < 0.5};
    const MawDimensionMap map =
        m_rules.rollDimensionMap(stream, m_rules.dimensionMapPool(), slots, 0, run.power + 1);
    InventoryItem item =
        ItemGenerator::makeInventoryItem(data.mapItemId(), *party.itemTable(), ItemGenerationMode::Generic);
    map.writeFields(item.rulesetFields);

    if (map.mapId != 0 && party.tryGrantInventoryItem(item))
    {
        ++state.mapsDropped[mapFileName];
        text += " You find a new Dimension Map.";
    }

    return text;
}

int MawExperienceRules::trainingLevelCap(int tableCap) const
{
    return tableCap > 0
        ? mawTrainingHallCap(tableCap, m_rules.options().challengeMode == RulesetChallengeMode::BeyondMadness)
        : tableCap;
}

float MawExperienceRules::trainingDurationMinutes(float) const
{
    return 2.0f * 24.0f * 60.0f;
}

// MAW's characters train far past level 1063, whose 4 billion experience Standard's cap stops (audit ROB-2-1).
uint64_t MawExperienceRules::maximumExperience() const
{
    return 1000000000000000000ull;
}

bool MawExperienceRules::learningGrantsExperience() const
{
    return false;
}

std::optional<int> MawExperienceRules::runDeaths() const
{
    return m_rules.options().challengeMode == RulesetChallengeMode::BeyondMadness
        ? std::optional<int>(m_rules.madnessLedger().deaths())
        : std::nullopt;
}

std::optional<int> MawExperienceRules::deathPendingSeconds(double gameMinutes) const
{
    // Two real seconds a game minute.
    constexpr double RealSecondsPerGameMinute = 2;
    const std::optional<double> minutes = m_rules.options().challengeMode == RulesetChallengeMode::BeyondMadness
        ? m_rules.madnessLedger().pendingMinutesLeft(gameMinutes)
        : std::nullopt;
    return minutes ? std::optional<int>(int(std::ceil(*minutes * RealSecondsPerGameMinute))) : std::nullopt;
}

std::optional<std::string> MawExperienceRules::loadWarning() const
{
    return m_rules.options().challengeMode == RulesetChallengeMode::BeyondMadness && m_rules.madnessLedger().pending()
        ? std::optional<std::string>("Loading now will count as death, are you sure to proceed?")
        : std::nullopt;
}

void MawExperienceRules::prepareNewParty(Party &party) const
{
    const RulesetChallengeMode mode = m_rules.options().challengeMode;

    if (!rulesetChallengeModeDifficulty(mode))
    {
        return;
    }

    const uint32_t experience = 10000 / uint32_t(std::max<size_t>(1, party.members().size()));

    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        Character &member = *party.member(memberIndex);

        if (mode == RulesetChallengeMode::BeyondMadness)
        {
            resetForMadness(member);
        }

        member.experience += experience;
        giveStartingItemPower(member);
    }

    party.addGold(5000 - party.gold());
}

void MawExperienceRules::prepareRosterCharacter(Character &character) const
{
    const RulesetChallengeMode mode = m_rules.options().challengeMode;

    if (mode == RulesetChallengeMode::BeyondMadness)
    {
        resetForMadness(character);
    }

    // Nobody starts with Learning (Ascension): its points come back, s + (s - 1) + ... + 2 (zzMAW-Skills.lua:1543-1560).
    if (const auto learning = character.skills.find("Learning"); learning != character.skills.end())
    {
        for (uint32_t level = learning->second.level; level > 1; --level)
        {
            character.skillPoints += level;
        }

        character.skills.erase(learning);
    }

    if (rulesetChallengeModeDifficulty(mode))
    {
        giveStartingItemPower(character);
    }
}

void MawExperienceRules::resetForMadness(Character &character) const
{
    character.level = 1;
    character.experience = 0;
    character.skillPoints = 0;

    // MAW resets its skills 0-38, not the four it adds.
    for (auto &[name, skill] : character.skills)
    {
        if (skill.level > 0 && !isRulesetSkill(name))
        {
            skill.level = 1;
            skill.mastery = SkillMastery::Normal;
        }
    }
}

void MawExperienceRules::giveStartingItemPower(Character &character) const
{
    const RulesetChallengeMode mode = m_rules.options().challengeMode;
    const bool insanity = mode == RulesetChallengeMode::RoadToInsanity || mode == RulesetChallengeMode::BeyondMadness;
    // MAW leaves the artifact Mordred (2020) out (zzMaw-Items.lua:4547).
    constexpr uint32_t ExcludedItem = 2020;
    const auto givePower = [this, insanity](uint32_t itemId, ItemRulesetFields &fields)
    {
        if (itemId != 0 && itemId != ExcludedItem && fields.itemPower == 0
            && m_rules.itemData().baseItem(itemId) != nullptr)
        {
            fields.itemPower = insanity ? 4 : 2;
        }
    };

    for (InventoryItem &item : character.inventory)
    {
        givePower(item.objectDescriptionId, item.rulesetFields);
    }

    const std::array<std::pair<uint32_t, EquippedItemRuntimeState *>, 16> worn = {{
        {character.equipment.offHand, &character.equipmentRuntime.offHand},
        {character.equipment.mainHand, &character.equipmentRuntime.mainHand},
        {character.equipment.bow, &character.equipmentRuntime.bow},
        {character.equipment.armor, &character.equipmentRuntime.armor},
        {character.equipment.helm, &character.equipmentRuntime.helm},
        {character.equipment.belt, &character.equipmentRuntime.belt},
        {character.equipment.cloak, &character.equipmentRuntime.cloak},
        {character.equipment.gauntlets, &character.equipmentRuntime.gauntlets},
        {character.equipment.boots, &character.equipmentRuntime.boots},
        {character.equipment.amulet, &character.equipmentRuntime.amulet},
        {character.equipment.ring1, &character.equipmentRuntime.ring1},
        {character.equipment.ring2, &character.equipmentRuntime.ring2},
        {character.equipment.ring3, &character.equipmentRuntime.ring3},
        {character.equipment.ring4, &character.equipmentRuntime.ring4},
        {character.equipment.ring5, &character.equipmentRuntime.ring5},
        {character.equipment.ring6, &character.equipmentRuntime.ring6},
    }};

    for (const auto &[itemId, pState] : worn)
    {
        givePower(itemId, pState->rulesetFields);
    }
}
}
