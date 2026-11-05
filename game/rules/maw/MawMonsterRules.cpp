#include "game/rules/maw/MawMonsterRules.h"

#include "game/gameplay/GameplayMonsterSpawn.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/gameplay/PartyHostileAlert.h"
#include "game/items/ItemGenerator.h"
#include "game/party/Party.h"
#include "game/rules/RandomStreams.h"
#include "game/rules/maw/MawCombatFormulas.h"
#include "game/rules/maw/MawCombatRules.h"
#include "game/rules/maw/MawExperienceCurve.h"
#include "game/rules/maw/MawItemFormulas.h"
#include "game/rules/maw/MawMonsterInspect.h"
#include "game/rules/maw/MawRules.h"
#include "game/tables/ItemTable.h"
#include "game/tables/MapStats.h"

#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <sstream>
#include <tuple>

namespace OpenYAMM::Game
{
namespace
{
constexpr std::array<double, 4> TierDamageMultipliers = {1, 0.66, 1, 1.5};
constexpr int MawDifficultyIndex = 3;
// The named map variable that marks a bounty hunt's map.
constexpr const char *BountyMapVariable = "MawBounty";
constexpr int BossLevelCap = 255;
// The affixes a boss rolls from (SkillList, zzMaw-Monsters.lua:3122): the fourteen an Omnipotent boss has, then the
// four it has not.
constexpr std::array<MawBossAffix, 18> RolledBossAffixes = {
    MawBossAffix::Summoner,
    MawBossAffix::Venomous,
    MawBossAffix::Plagueborn,
    MawBossAffix::Fixator,
    MawBossAffix::Exploding,
    MawBossAffix::Thorn,
    MawBossAffix::Reflecting,
    MawBossAffix::Adamantite,
    MawBossAffix::Swapper,
    MawBossAffix::Regenerating,
    MawBossAffix::Puller,
    MawBossAffix::Leecher,
    MawBossAffix::Swift,
    MawBossAffix::Shadow,
    MawBossAffix::Unstoppable,
    MawBossAffix::Berserker,
    MawBossAffix::Cryptic,
    MawBossAffix::Skilled,
};

// Whether an Omnipotent boss has this affix (and spawns a boss of it on death): the first fourteen.
bool omnipotentCovers(MawBossAffix affix)
{
    return affix != MawBossAffix::None && affix < MawBossAffix::Broodlord;
}

// MAW's special bosses, which hatch or spawn others on death.
bool specialBoss(uint8_t affix)
{
    return affix == uint8_t(MawBossAffix::Broodlord) || affix == uint8_t(MawBossAffix::Broodling)
        || affix == uint8_t(MawBossAffix::Omnipotent);
}

std::string lowerFileName(const std::string &fileName)
{
    std::string lower = fileName;
    std::transform(lower.begin(), lower.end(), lower.begin(), [](unsigned char c) { return char(std::tolower(c)); });
    return lower;
}

double unitDraw(RandomStream &stream)
{
    return double(stream() >> 11) / double(1ull << 53);
}

// The party's best Alchemy mastery and, perhaps from another member, its best Alchemy skill.
std::pair<int, int> bestAlchemy(const Party *pParty)
{
    int mastery = 0;
    int skill = 0;

    if (pParty == nullptr)
    {
        return {mastery, skill};
    }

    for (const Character &member : pParty->members())
    {
        if (const CharacterSkill *pAlchemy = member.findSkill("Alchemy"))
        {
            mastery = std::max(mastery, int(pAlchemy->mastery));
            skill = std::max(skill, int(pAlchemy->level) + member.skillBonus("Alchemy"));
        }
    }

    return {mastery, skill};
}

// Crafting materials and reagents a kill drops besides its loot (CRAFTING.md §6.1, §9.2): a gem, each special by its
// bad-luck counter, an Endless Potion for a Grandmaster alchemist's party, and reagents from Master Alchemy.
// The share of a boss's extra drops a Broodling gets: 1 / (5 - tier) (zzMaw-Items.lua:270-279); 1 for other bosses.
double bossDropShare(const CorpseLootContext &context)
{
    if (context.pFacts == nullptr || context.pFacts->bossAffix != uint8_t(MawBossAffix::Broodling))
    {
        return 1;
    }

    const int tier = context.pFacts->tier > 0 ? context.pFacts->tier : mawMonsterTier(context.pStats->id);
    return 1.0 / (5 - tier);
}

void rollCraftingDrops(MawRules &rules, const CorpseLootContext &context, int level, bool boss, CorpseLoot &result)
{
    // The monsters that leave no corpse (MAW's noCorpseMonsters) drop three times as much.
    static constexpr std::array<int16_t, 24> NoCorpseMonsters = {
        82, 83, 84, 97, 98, 99, 241, 242, 243, 523, 524, 525, 529, 530, 531, 532, 533, 534, 622, 623, 624, 625,
        626, 627,
    };
    const MawCraftingData &data = rules.craftingData();
    const MawModelConfig config = mawModelConfig(rules.options(), 5);

    if (data.gemTiers() <= 0)
    {
        return;
    }

    // Risen monsters and Beyond Madness's rewardless maps drop no gems or specials; reagents and Endless Potions
    // still come, from MAW's other handler (zzAlchemy.lua:654-698, 1118-1126).
    const bool gemsAndSpecials = !context.pFacts->risen && !rules.madnessRewardlessMap(context.pMap->fileName);

    RandomStream stream(randomStreamKey(rules.randomRootSeed(), RandomDomain::CraftDrop,
        randomNameKey(context.pMap->fileName), context.visitSeed, context.actorIndex));
    const MawDimensionRun *pRun = rules.dimensionRun(context.pMap->fileName);
    const double dimension =
        pRun != nullptr ? 1 + mawDimensionStrength(pRun->power, pRun->affixCount()) / 800 * 1.5 : 1;
    const bool noCorpse =
        std::find(NoCorpseMonsters.begin(), NoCorpseMonsters.end(), context.pStats->id) != NoCorpseMonsters.end();
    // Austerity drops no gems or specials; reagents and Endless Potions still come (zzAlchemy.lua:1181-1183).
    const double bonus = config.austerity
        ? 0
        : std::sqrt(level / 10.0) * (boss ? data.bossDropExtra() * bossDropShare(context) : 1) * dimension
            * (noCorpse ? 3 : 1);
    const double gemChance = data.gemDropChance() * bonus * (config.insanityMode ? 1.5 : 1);

    if (gemsAndSpecials && unitDraw(stream) < gemChance)
    {
        // Box-Muller: a normal draw around max(level^0.6 / 4 + 1, level / 40), deviation 2.
        const double mean = std::max(std::pow(level, 0.6) / 4 + 1, level / 40.0);
        const double radius = std::sqrt(-2 * std::log(std::max(unitDraw(stream), 1e-12)));
        const double normal = mean + 2 * radius * std::cos(2 * 3.14159265358979323846 * unitDraw(stream));
        const int tier = std::clamp(int(std::floor(normal)), 1, data.gemDropMaxTier());
        result.extraItems.push_back({data.gemItemId(tier)});
    }

    // The specials in id order, each with its own counter: base^(1.38 - base x counter / 2) x bonus.
    std::vector<uint32_t> specials;

    for (const auto &[itemId, material] : data.materials())
    {
        if (material.dropChance > 0)
        {
            specials.push_back(itemId);
        }
    }

    std::sort(specials.begin(), specials.end());
    MawGameState &state = rules.state();

    for (uint32_t itemId : gemsAndSpecials ? specials : std::vector<uint32_t>{})
    {
        const double base = data.material(itemId)->dropChance;
        double &counter = state.craftingPity[itemId];
        const double chance = base >= 1 ? 1 : std::pow(base, data.pityExponent() - base * counter * 0.5) * bonus;

        if (unitDraw(stream) < chance)
        {
            result.extraItems.push_back({itemId});
            counter = 0;
        }
        else
        {
            counter += mawRound(bonus);
        }
    }

    const auto [alchemyMastery, alchemySkill] = bestAlchemy(context.pParty);

    // Endless Potion: adds the best Alchemy skill + 10 drinks, at most 100.
    if (alchemyMastery >= int(SkillMastery::Grandmaster) && unitDraw(stream) < data.endlessPotionChance())
    {
        for (const auto &[itemId, material] : data.materials())
        {
            if (material.operation == MawCraftOperation::AddPotionCharges)
            {
                result.extraItems.push_back({itemId, uint16_t(std::min(alchemySkill + 10, 100))});
            }
        }
    }

    // Reagents: (mastery - 2) % from Master; tier by the monster's table level, the item level half the levels banked
    // on the other continents. Far too strong a reagent comes as a ready potion of that power instead.
    if (alchemyMastery >= int(SkillMastery::Master) && !data.reagentTiers().empty()
        && unitDraw(stream) < (alchemyMastery - 2) / 100.0)
    {
        const double baseLevel = context.pStats->level;
        const int reagentTier = std::clamp(int(mawRound(baseLevel / 20 * (1.75 + unitDraw(stream) / 2))), 1,
            int(data.reagentTiers().size()));
        const std::vector<uint32_t> &reagents = data.reagentTiers()[size_t(reagentTier - 1)];
        const uint32_t reagentId = reagents[stream.uniform(0, uint32_t(reagents.size() - 1))];
        const int itemLevel = int(mawRound(state.levelOutside(context.pMap->mergedContinentId) / 2));
        // The skill's share is a float (zzAlchemy.lua:679-688): 200.5 makes a potion.
        const double potionPower = itemLevel + alchemySkill * alchemyMastery / 2.0;

        if (potionPower > 200)
        {
            result.extraItems.push_back(
                {221 + stream.uniform(0, 3), 0, uint16_t(std::min(int(mawRound(potionPower)), 65535))});
        }
        else
        {
            result.extraItems.push_back({reagentId, 0, 0, uint16_t(std::clamp(itemLevel, 0, 2047))});
        }
    }

    // A Skilled boss drops four Horseshoes (zzAlchemy.lua:1132-1136); a risen one, which dropped them already, none.
    constexpr uint32_t Horseshoe = 656;

    if (gemsAndSpecials && mawHasBossAffix(*context.pFacts, MawBossAffix::Skilled))
    {
        result.extraItems.insert(result.extraItems.end(), 4, {Horseshoe});
    }
}

// A dimension map from a kill once the Dimensional Maps quest is done (zzMaw-Maps.lua:826-939): from monsters of
// level 100, by the completed share of the dungeons with bad-luck protection, x level / 100, less with every map
// already dropped on the map, x10 from bosses. Two to four affixes; MAW's roll never gives two (DEVIATIONS.md).
void rollDimensionMapDrop(MawRules &rules, const CorpseLootContext &context, int level, bool boss, CorpseLoot &result)
{
    const MawDimensionData &data = rules.dimensionData();
    MawGameState &state = rules.state();
    const RulesetChallengeMode mode = rules.options().challengeMode;
    const bool madness = mode == RulesetChallengeMode::BeyondMadness;
    // Beyond Madness: maps drop from level 70, but only on maps of level 950 and up (the band's mean + 20, + 10 per
    // power of a dimension run), with no failure counted elsewhere (zzMaw-Maps.lua:822-858).
    constexpr int MadnessDropLevel = 70;
    constexpr double MadnessMapLevel = 950;

    if (!state.dimensionQuest.done || data.mapItemId() == 0 || context.pFacts->risen
        || level < (madness ? MadnessDropLevel : data.dropLevelRequired()))
    {
        return;
    }

    if (madness)
    {
        const std::array<double, 3> band = rules.mapLevels().band(context.pMap->fileName);
        const MawDimensionRun *pMapRun = rules.dimensionRun(context.pMap->fileName);
        const double mapLevel =
            mawRound((band[0] + band[1] + band[2]) / 3) + 20 + (pMapRun != nullptr ? pMapRun->power * 10 : 0);

        if (mapLevel < MadnessMapLevel)
        {
            return;
        }
    }

    const std::vector<uint16_t> pool = rules.dimensionMapPool();

    if (pool.empty())
    {
        return;
    }

    RandomStream stream(randomStreamKey(rules.randomRootSeed(), RandomDomain::Dimension,
        randomNameKey(context.pMap->fileName), context.visitSeed, context.actorIndex));
    const std::string mapFileName = lowerFileName(context.pMap->fileName);
    const int dropped = state.mapsDropped[mapFileName];
    const double multiplier = boss ? data.bossDropMultiplier() * bossDropShare(context) : 1;
    // The chance reads the monster's table level, a byte capped at 255 (zzMaw-Maps.lua:885); the gate above and the
    // map's power below use the full level.
    const double chance = mawPityChance(data.dropChance() * double(pool.size()) / double(data.dungeons().size()),
                              state.mapDropPity)
        * std::min(level, 255) / 100.0 / (dropped + 1) * multiplier;

    if (unitDraw(stream) >= chance)
    {
        state.mapDropPity += multiplier;
        return;
    }

    const double activeRoll = unitDraw(stream);
    const uint8_t activeSlots = activeRoll <= 0.1 ? 4 : activeRoll < 0.3 ? 3 : 2;
    int power = int(mawRound(level / 10.0 - stream.uniform(0, 3)));

    // Road to Insanity (not Beyond Madness): a dropped map has power 30 at least (zzMaw-Maps.lua:928-930).
    if (mode == RulesetChallengeMode::RoadToInsanity)
    {
        power = std::max(power, 30);
    }

    const MawDimensionMap map = rules.rollDimensionMap(stream, pool, {true, true, true, true}, activeSlots, power);
    CorpseLoot::ExtraItem item;
    item.itemId = data.mapItemId();
    item.rulesetFields = ItemRulesetFields{};
    map.writeFields(*item.rulesetFields);
    result.extraItems.push_back(item);
    state.mapDropPity = 0;
    ++state.mapsDropped[mapFileName];
}

int levelOf(const std::unordered_map<int, int> &levels, int monsterId, int fallback)
{
    const auto it = levels.find(monsterId);
    return it != levels.end() ? it->second : fallback;
}

bool gainsHellRangedAttack(
    const RulesetOptions &options,
    const std::string &mapFileName,
    const MonsterTable::MonsterStatsEntry &stats,
    bool bountyMap)
{
    static const std::array<const char *, 6> StartingMaps = {
        "out01.odm", "out02.odm", "7out01.odm", "7out02.odm", "oute3.odm", "outd3.odm",
    };
    const std::string map = lowerFileName(mapFileName);
    const bool hellOutdoors = options.difficulty >= RulesetDifficulty::Hell && map.ends_with(".odm")
        && std::find(StartingMaps.begin(), StartingMaps.end(), map) == StartingMaps.end();
    return (hellOutdoors || bountyMap) && !stats.attack1HasMissile && stats.attack2Chance <= 0 && !stats.hasSpell1
        && !stats.canFly;
}

// A boss is its own level plus the gap to its family's B level, drawn again inside [1.1 L, 1.3 L] (below level 100)
// or [L + 10, L + 30] when that falls outside (MON:311-335).
// The level a boss starts from (MawBossLevel, MON:31-40): a C row its level plus the C - B gap, an A or B row the next
// tier's level.
int bossBaseLevel(int level, int familyLevel, uint8_t tier, int nextTierLevel)
{
    return tier == 3 ? std::max(1, int(mawRound(2.0 * level - familyLevel))) : std::max(1, nextTierLevel);
}

// The boss's level: its base level, drawn again inside [1.1, 1.3] x its row's level (below 100) or [+10, +30] when it
// lies outside (MON:321-327).
bool bossLevelRedrawn(int level, int candidate)
{
    return level < 100 ? candidate < 1.1 * level || candidate > 1.3 * level
                       : candidate < level + 10 || candidate > level + 30;
}

int bossLevel(int level, int candidate, double draw)
{
    if (!bossLevelRedrawn(level, candidate))
    {
        return candidate;
    }

    return level < 100 ? std::max(1, int(mawRound(level * (1.1 + 0.2 * draw)))) : int(mawRound(level + 10 + 20 * draw));
}


// The monster's share of its family's HP: A and C rows keep their table ratio to the B row, within 0.6-1.8.
double tierHealthRatio(const MonsterTable &monsterTable, const MonsterTable::MonsterStatsEntry &stats, uint8_t tier)
{
    const MonsterTable::MonsterStatsEntry *pFamilyB = monsterTable.findStatsById(int16_t(mawFamilyBId(stats.id)));

    if (tier == 2 || pFamilyB == nullptr || pFamilyB->hitPoints <= 0)
    {
        return 1;
    }

    return std::clamp(double(stats.hitPoints) / pFamilyB->hitPoints, 0.6, 1.8);
}

// MAW keeps the table's dice only as a ratio; the actor's dice show the model damage with its ±25 % spread.
void setDisplayedDamage(int &diceRolls, int &diceSides, int &bonus, double damage)
{
    diceRolls = 1;
    diceSides = std::max(1, int(mawRound(damage * 0.5)));
    bonus = std::max(0, int(mawRound(damage * 0.75)) - 1);
}
}

std::string mawBossAffixName(MawBossAffix affix)
{
    static constexpr std::array<const char *, 22> Names = {
        "", "Summoner", "Venomous", "Plagueborn", "Fixator", "Exploding", "Thorn", "Reflecting", "Adamantite",
        "Swapper", "Regenerating", "Puller", "Leecher", "Swift", "Shadow", "Broodlord", "Broodling", "Omnipotent",
        "Unstoppable", "Berserker", "Cryptic", "Skilled",
    };
    return size_t(affix) < Names.size() ? Names[size_t(affix)] : "";
}

MawBossAffix mawBossEffectAffix(const ActorRulesetFacts &facts)
{
    return facts.bossAffix == uint8_t(MawBossAffix::Cryptic) ? MawBossAffix(facts.crypticAffix)
                                                              : MawBossAffix(facts.bossAffix);
}

bool mawHasBossAffix(const ActorRulesetFacts &facts, MawBossAffix affix)
{
    const MawBossAffix effect = mawBossEffectAffix(facts);
    return (affix != MawBossAffix::None && effect == affix)
        || (omnipotentCovers(affix) && effect == MawBossAffix::Omnipotent);
}

bool mawIgnoresCrowdControl(const ActorRulesetFacts &facts)
{
    return mawHasBossAffix(facts, MawBossAffix::Unstoppable);
}

double mawBerserkerDamageMultiplier(int currentHp, int maxHp)
{
    return 2 - std::clamp(double(currentHp) / std::max(maxHp, 1), 0.0, 1.0);
}

MawMapCompletion mawMapCompletion(const MapKillProgress &progress, bool insanityRules)
{
    MawMapCompletion completion;
    const std::string mapFileName = lowerFileName(progress.mapFileName);
    const int counted = progress.countedMonsters - (mapFileName == "mdt15.blv" ? 1 : 0);

    if (mapFileName == "d42.blv" || (counted <= 0 && progress.hiddenMonsters <= 0))
    {
        return completion;
    }

    completion.counts = true;
    completion.counted = std::max(counted, 0);
    completion.share = counted > 0 ? std::min(1.0, double(progress.slainMonsters) / counted) : 1.0;
    completion.required = insanityRules && !progress.indoor ? 1 : std::pow(0.99, std::floor(std::max(counted, 0) / 100));
    completion.percent = std::min(mawRound(completion.share * 1000 / completion.required) / 10, 100.0);
    completion.complete = completion.share >= completion.required;
    return completion;
}

std::optional<RulesetMapProgress> mawMapProgress(const MapKillProgress &progress, const MawMapProgressFacts &facts)
{
    RulesetMapProgress result;

    // The Arena shows the Endless Arena's level and progress instead (d42_maw.lua).
    if (lowerFileName(progress.mapFileName) == "d42.blv")
    {
        if (facts.arenaLevel <= 0)
        {
            return std::nullopt;
        }

        result.kind = RulesetMapProgress::Kind::Arena;
        result.arenaLevel = facts.arenaLevel;
        result.percent = std::clamp(facts.arenaPercent, 0, 100);
        return result;
    }

    const MawMapCompletion completion = mawMapCompletion(progress, facts.insanityRules);

    if (!completion.counts)
    {
        return std::nullopt;
    }

    result.complete = completion.complete || facts.cleared;
    result.percent = result.complete ? 100.0 : completion.percent;
    result.slain = std::min(progress.slainMonsters, completion.counted);
    result.counted = completion.counted;
    result.requiredShare = completion.required;
    result.needed = int(std::ceil(completion.required * completion.counted - 1e-9));
    result.hidden = progress.hiddenMonsters;

    // The revival line is the raw share of the counted, placed on the bar's normalised scale.
    constexpr double RevivalShare = 0.65;
    result.revival = facts.revivalRules && progress.indoor && !result.complete;
    result.revivalSlain = int(std::ceil(RevivalShare * completion.counted - 1e-9));
    result.revivalPosition = float(std::min(1.0, RevivalShare / completion.required));
    result.revivalPassed = facts.weakened || completion.share >= RevivalShare;

    const MawDimensionRun *pRun = facts.pDimensionRun;

    if (pRun != nullptr)
    {
        result.kind = RulesetMapProgress::Kind::DimensionRun;
        result.dimensionPower = pRun->power;
        result.dimensionAffixes = pRun->affixCount();
    }

    // A dimension run on a completed map pays no second reward but counts for the quest (rewardMapProgress); Beyond
    // Madness pays its runs the full reward.
    const bool openRun = pRun != nullptr && !pRun->completed;

    if (openRun && facts.completedBefore && !facts.beyondMadness)
    {
        result.reward = "counts for the Dimensional Maps quest";
    }
    else if (facts.completedBefore && !openRun)
    {
        result.rewardPaid = true;
    }
    else
    {
        result.reward = facts.austerity ? "experience and gold" : "experience, gold, materials";
    }

    return result;
}

uint8_t mawMonsterTier(int monsterId)
{
    const int remainder = monsterId % 3;
    return remainder == 1 ? 1 : remainder == 2 ? 2 : 3;
}

double mawMonsterBaseDamage(
    const MawRules &rules, const ActorRulesetFacts &facts, int partyCount, CombatDamageType type)
{
    const MawDamageClass damageClass =
        type == CombatDamageType::Physical ? MawDamageClass::Physical : MawDamageClass::Magic;
    const double familyLevel = std::max(1, facts.familyLevel);
    return rules.model(std::max(1, partyCount)).monsterDamage(familyLevel, damageClass)
        * TierDamageMultipliers[std::min<size_t>(facts.tier, TierDamageMultipliers.size() - 1)]
        * facts.bossDamageMultiplier;
}

MawMonsterRules::MawMonsterRules(MawRules &rules)
    : m_rules(rules)
{
}

GameplayMonsterBolsterResult MawMonsterRules::resolveMonster(
    const GameplayBolsterRuntimeContext &context,
    const MonsterTable::MonsterStatsEntry &stats,
    const MonsterEntry *pMonsterEntry) const
{
    // MMMerge's bolster is off under MAW: start from the table row.
    GameplayBolsterRuntimeContext tableContext = context;
    tableContext.bolsterMonstersEnabled = false;
    GameplayMonsterBolsterResult result = MonsterRules::resolveMonster(tableContext, stats, pMonsterEntry);

    if (context.pMap == nullptr || context.pMonsterTable == nullptr || stats.id <= 0)
    {
        return result;
    }

    ActorRulesetFacts facts =
        context.pExistingFacts != nullptr ? *context.pExistingFacts : ActorRulesetFacts{};

    // Every resolve takes the level the map gives now, so survivors follow banked levels, a progression change or a
    // reset when the map loads or the rules change (MON:383-665); a boss keeps its affix and rolls.
    const std::unordered_map<int, int> &levels = m_rules.monsterLevels(*context.pMonsterTable, *context.pMap);
    const int baseLevel = levelOf(levels, stats.id, stats.level);
    facts.familyLevel = levelOf(levels, mawFamilyBId(stats.id), baseLevel);
    facts.tier = mawMonsterTier(stats.id);
    facts.level = facts.bossAffix != 0
        ? bossLevel(baseLevel,
              bossBaseLevel(baseLevel, facts.familyLevel, facts.tier, levelOf(levels, stats.id + 1, baseLevel)),
              facts.bossLevelDraw)
        : baseLevel;

    // A unique monster climbs from its own level by the party's banked levels (no -4), as the starting maps do in
    // horizontal progression; elsewhere there it is 2.5 x its level (MON:273-310). Beyond Madness: the map's fixed
    // level plus twice its band's spread above the middle, or 3 x its own level on a starting map or a map without
    // one (MON:290-305). Its health and damage stay the family's.
    if (facts.unique)
    {
        const std::string mapFile = lowerFileName(context.pMap->fileName);
        const MawMapLevels &mapLevels = m_rules.mapLevels();

        if (m_rules.options().challengeMode == RulesetChallengeMode::BeyondMadness)
        {
            const int madnessLevel = mapLevels.madnessLevel(mapFile);
            const std::array<double, 3> band = mapLevels.band(mapFile);
            facts.level = madnessLevel > 0 && !mapLevels.isMadnessStartingMap(mapFile)
                ? int(mawRound(madnessLevel + (band[2] - band[1]) * 2))
                : stats.level * 3;
        }
        else
        {
            const bool horizontalElsewhere = m_rules.options().progression == RulesetProgression::Horizontal
                && !mapLevels.isHorizontalStarterMap(mapFile);
            facts.level = int(mawRound(horizontalElsewhere
                    ? stats.level * 2.5
                    : mawBolsteredLevel(m_rules.state().levelOutside(context.pMap->mergedContinentId), stats.level)));
        }
    }

    const int partyCount = context.pParty != nullptr ? int(std::max<size_t>(1, context.pParty->members().size())) : 5;
    MawBalanceModel &model = m_rules.model(partyCount);
    const double level = facts.level;
    const double familyLevel = std::max(1, facts.familyLevel);
    const std::string &mapFileName = context.pMap->fileName;
    const std::optional<double> healthAffix = m_rules.mapAffix(mapFileName, MawMapAffix::MonsterHealth);
    // MAW's +HP affix never reaches live HP (dimension_affixes.yml 15); here it does (DEVIATIONS.md).
    const double health = model.monsterHealth(familyLevel) * tierHealthRatio(*context.pMonsterTable, stats, facts.tier)
        * facts.bossHealthMultiplier * (1 + healthAffix.value_or(0) / 100);
    const double roundedHealth = health > 1000 ? mawRound(health / 10) * 10 : mawRound(health);
    result.maxHp = std::max(1, int(roundedHealth));
    // Armour grows from the table's B level to the row's level on the map (MON:751); a boss or unique monster keeps its
    // row's armour, not its own level's. Poisons replace diseases below level 20 (MON:3741-3747).
    const MonsterTable::MonsterStatsEntry *pTableB = context.pMonsterTable->findStatsById(int16_t(mawFamilyBId(stats.id)));
    const double tableFamilyLevel = pTableB != nullptr ? std::max(1, pTableB->level) : familyLevel;
    result.armorClass = int(mawRound(stats.armorClass * (baseLevel + 10.0) / (tableFamilyLevel + 10)));

    // The Doom modes' special attack replaces the monster's own (its strength stays the monster's).
    if (facts.doomSpecialAttack != 0)
    {
        result.specialAttackKind = MonsterSpecialAttackKind(facts.doomSpecialAttack);
    }

    if (level < 20)
    {
        switch (result.specialAttackKind.value_or(stats.specialAttackKind))
        {
            case MonsterSpecialAttackKind::DiseaseWeak:
                result.specialAttackKind = MonsterSpecialAttackKind::PoisonWeak;
                break;
            case MonsterSpecialAttackKind::DiseaseMedium:
                result.specialAttackKind = MonsterSpecialAttackKind::PoisonMedium;
                break;
            case MonsterSpecialAttackKind::DiseaseSevere:
                result.specialAttackKind = MonsterSpecialAttackKind::PoisonSevere;
                break;
            default:
                break;
        }
    }

    // Each attack is sized against the defence its damage kind meets (getMonsterDamage's damageKind, MAW 249b00da).
    const double damage = mawMonsterBaseDamage(
        m_rules, facts, partyCount, GameMechanics::parseCombatDamageType(stats.attack1Type));
    const double attack2BaseDamage = mawMonsterBaseDamage(
        m_rules, facts, partyCount, GameMechanics::parseCombatDamageType(stats.attack2Type));
    const double attack1Average =
        mawDiceAverage(stats.attack1Damage.diceRolls, stats.attack1Damage.diceSides, stats.attack1Damage.bonus);
    double attack2Average =
        mawDiceAverage(stats.attack2Damage.diceRolls, stats.attack2Damage.diceSides, stats.attack2Damage.bonus);

    // From Hell up, outdoors outside the six starting maps, and on a bounty hunt's map on any difficulty, a walking
    // melee-only monster also shoots: chance 10, 20 or 30 % by tier, its dice and bonus cut from attack 1's
    // (MON:632-658).
    if (gainsHellRangedAttack(m_rules.options(), mapFileName, stats, m_rules.bountyLevel().has_value()))
    {
        result.generatedAttack2 = true;
        result.generatedAttack2IsRanged = true;
        result.generatedAttack2MissileType = "Arrow";
        result.generatedAttack2Chance = 10 * std::max<int>(1, facts.tier);
        attack2Average = mawDiceAverage(int(std::ceil(stats.attack1Damage.diceRolls / 1.4)),
            int(std::ceil(stats.attack1Damage.diceSides / 1.4)), int(std::ceil(stats.attack1Damage.bonus / 2.0)));
    }
    facts.attack1Damage = float(damage);
    facts.attack2Damage =
        float(attack1Average > 0 ? attack2BaseDamage * attack2Average / attack1Average : attack2BaseDamage);
    setDisplayedDamage(
        result.attack1DamageDiceRolls, result.attack1DamageDiceSides, result.attack1DamageBonus, facts.attack1Damage);
    setDisplayedDamage(
        result.attack2DamageDiceRolls, result.attack2DamageDiceSides, result.attack2DamageBonus, facts.attack2Damage);

    // Experience follows the row's level on the map, also for bosses and uniques (their own level only enters through
    // the health share, zzMaw-Monsters.lua:4071-4080).
    const double ownLevel = baseLevel;
    const double experienceLevel = std::min(std::max(double(stats.level), ownLevel / 3), 100.0);
    const double experience = experienceLevel > 0
        ? mawRound((experienceLevel * 20 + std::pow(experienceLevel, 1.8)) * ownLevel / experienceLevel)
        : 0;
    // Antagarich's monsters give twice as much, at most 1000 more (MON:612-614; MAW reads a stale world global there,
    // DEVIATIONS.md 75).
    const double continentExperience =
        context.pMap->mergedContinentId == 2 ? std::min(experience * 2, experience + 1000) : experience;
    facts.experience =
        uint32_t(std::max(0.0, mawRound(continentExperience * model.monsterExperienceMultiplier())));

    // Fast melee monsters close in quicker: v -> v / 2 + 300; not while they are calm (MON:94-152).
    if (stats.speed > 150 && !stats.attack1HasMissile)
    {
        result.calmMoveSpeed = result.moveSpeed;
        result.moveSpeed = uint16_t(stats.speed + (400 - stats.speed) / 2 + 100);
    }

    // MAW moves a Swift boss twice as far each frame while it walks.
    if (mawHasBossAffix(facts, MawBossAffix::Swift))
    {
        result.moveSpeed = uint16_t(std::min(2 * int(result.moveSpeed), 65535));
    }

    // A boss's first spell is cast at its skill times the boss's damage multiplier (generateBoss, MON:3074-3075).
    if (facts.bossAffix != 0 && result.spell1SkillLevel > 0)
    {
        result.spell1SkillLevel = uint32_t(std::floor(result.spell1SkillLevel * facts.bossDamageMultiplier));
    }

    // A dimension map's movement speed and spells (zzMaw-Monsters.lua:340-350, 3469-3490): Fireball at skill 10, or
    // Dragon Breath at skill 5, in place of the monster's first spell.
    if (const std::optional<double> speed = m_rules.mapAffix(mapFileName, MawMapAffix::MonsterSpeed))
    {
        result.moveSpeed = uint16_t(std::min(mawRound(result.moveSpeed * (1 + *speed / 100)), 65535.0));
    }

    for (const auto &[affix, spellId, skill] : {std::tuple{MawMapAffix::Fireball, 6u, 10u},
             std::tuple{MawMapAffix::DragonBreath, 97u, 5u}})
    {
        if (const std::optional<double> chance = m_rules.mapAffix(mapFileName, affix))
        {
            result.generatedSpell1Id = spellId;
            result.generatedSpell1UseChance = std::max(1, int(mawRound(*chance)));
            result.spell1SkillLevel = skill;
            result.spell1SkillMastery = SkillMastery::Normal;
        }
    }

    facts.maxHp = result.maxHp;
    result.partyLevel = int(m_rules.state().levelOutside(context.pMap->mergedContinentId));
    result.monsterFamilyLevel = facts.familyLevel;
    result.rulesetFacts = facts;
    return result;
}

bool MawMonsterRules::placeMapMonsters(
    const GameplayBolsterRuntimeContext &context,
    std::vector<MapMonsterPlacement> &monsters) const
{
    // MAW makes the bosses first, so the conditions see their levels.
    const bool bosses = placeMapBosses(context, monsters);
    return rollDoomSpecialAttacks(context, monsters) || bosses;
}

bool MawMonsterRules::rollDoomSpecialAttacks(
    const GameplayBolsterRuntimeContext &context,
    std::vector<MapMonsterPlacement> &monsters) const
{
    using Kind = MonsterSpecialAttackKind;
    // The pool opens up with the monster's level: MAW's Bonus ids 6, 7, 8, 2, 23, then 1 at 15, 9-11 at 20, 12 at 30, 5
    // at 40, 15 at 50, 3 and 13 at 60, 21 at 70, 22 at 80, 14 at 90 and 16 at 100.
    static const std::array<std::pair<int, Kind>, 18> Pool = {{
        {0, Kind::PoisonWeak}, {0, Kind::PoisonMedium}, {0, Kind::PoisonSevere}, {0, Kind::Weak}, {0, Kind::Fear},
        {15, Kind::Curse}, {20, Kind::DiseaseWeak}, {20, Kind::DiseaseMedium}, {20, Kind::DiseaseSevere},
        {30, Kind::Paralyze}, {40, Kind::Insane}, {50, Kind::Petrify}, {60, Kind::Sleep}, {60, Kind::Unconscious},
        {70, Kind::Aging}, {80, Kind::ManaDrain}, {90, Kind::Dead}, {100, Kind::Eradicate},
    }};

    if (context.pMap == nullptr || !mawModelConfig(m_rules.options(), 5).doomMode)
    {
        return false;
    }

    const std::string &mapFileName = context.pMap->fileName;
    const auto refill = m_refillSeeds.find(lowerFileName(mapFileName));
    const uint64_t resets = uint64_t(m_rules.state().resetCount(mapFileName))
        ^ (refill != m_refillSeeds.end() ? refill->second : 0);
    RandomStream roll(randomStreamKey(m_rules.randomRootSeed(), RandomDomain::DoomSpecialAttack,
        randomNameKey(mapFileName), resets));
    bool changed = false;

    for (MapMonsterPlacement &monster : monsters)
    {
        if (monster.pStats == nullptr || monster.pFacts == nullptr || monster.pFacts->level <= 0
            || (monster.uniqueNameId >= 1 && monster.uniqueNameId < 220))
        {
            continue;
        }

        // The game's stored level stops at 255.
        const int level = std::min(monster.pFacts->level, 255);

        if (std::sqrt(double(level)) * 2 / 100 <= unitDraw(roll))
        {
            continue;
        }

        size_t open = 0;

        while (open < Pool.size() && Pool[open].first <= level)
        {
            ++open;
        }

        monster.pFacts->doomSpecialAttack = uint8_t(Pool[roll.uniform(0, uint32_t(open - 1))].second);
        changed = true;
    }

    return changed;
}

bool MawMonsterRules::placeMapBosses(
    const GameplayBolsterRuntimeContext &context,
    std::vector<MapMonsterPlacement> &monsters) const
{
    const MawModelConfig config = mawModelConfig(m_rules.options(), 5);
    bool changed = false;

    // The map's unique monsters level with the party on every difficulty (zzMaw-Monsters.lua:273-310).
    for (MapMonsterPlacement &monster : monsters)
    {
        if (monster.pFacts != nullptr && monster.pFacts->level > 0 && !monster.pFacts->unique
            && monster.uniqueNameId >= 1 && monster.uniqueNameId < 220)
        {
            monster.pFacts->unique = true;
            changed = true;
        }
    }

    if (context.pMap == nullptr || config.difficulty < MawDifficultyIndex)
    {
        return changed;
    }

    // The next tier's level on this map, which an A or B row's boss starts from.
    const auto baseLevelOf = [this, &context](const MapMonsterPlacement &monster)
    {
        const ActorRulesetFacts &facts = *monster.pFacts;
        const int nextTierLevel = context.pMonsterTable != nullptr
            ? levelOf(m_rules.monsterLevels(*context.pMonsterTable, *context.pMap), monster.pStats->id + 1, facts.level)
            : facts.level;
        return bossBaseLevel(facts.level, facts.familyLevel, mawMonsterTier(monster.pStats->id), nextTierLevel);
    };
    const double divisor = config.doomMode ? 60 : 150;
    int bossCount = int(std::ceil((double(monsters.size()) - 30) / divisor));
    const std::string &mapFileName = context.pMap->fileName;
    const uint64_t rootSeed = m_rules.randomRootSeed();
    const uint64_t map = randomNameKey(mapFileName);
    // A refill rolls the bosses afresh (MAW: fresh map variables); the first visit's stay keyed by the map.
    const auto refill = m_refillSeeds.find(lowerFileName(mapFileName));
    const uint64_t resets = uint64_t(m_rules.state().resetCount(mapFileName))
        ^ (refill != m_refillSeeds.end() ? refill->second : 0);

    if (const std::optional<double> density = m_rules.mapAffix(mapFileName, MawMapAffix::BossDensity))
    {
        bossCount = int(std::ceil(bossCount * (1 + *density / 100)));
    }

    // A dimension map may make any unnamed A or B monster a boss before the usual C-tier picks.
    if (const std::optional<double> chance = m_rules.mapAffix(mapFileName, MawMapAffix::BecomeBoss))
    {
        RandomStream roll(
            randomStreamKey(rootSeed, RandomDomain::DimensionBecomeBoss, map, resets, int(MawMapAffix::BecomeBoss)));

        for (size_t index = 0; index < monsters.size(); ++index)
        {
            const MapMonsterPlacement &monster = monsters[index];

            if (monster.pStats != nullptr && monster.pFacts != nullptr && monster.pFacts->level > 0 && !monster.named
                && mawMonsterTier(monster.pStats->id) != 3
                && monster.pStats->aiType != MonsterTable::MonsterAiType::Wimp && unitDraw(roll) < *chance / 100)
            {
                changed = makeBoss(*monster.pFacts, randomStreamKey(rootSeed, RandomDomain::BossStats, map, resets,
                    index), 0, baseLevelOf(monster)) || changed;
            }
        }
    }

    std::vector<size_t> candidates;

    for (size_t index = 0; index < monsters.size(); ++index)
    {
        const MapMonsterPlacement &monster = monsters[index];

        // MAW does not ask whether the monster is hostile (zzMaw-Monsters.lua:2880-2890).
        if (monster.pStats != nullptr && monster.pFacts != nullptr && monster.pFacts->level > 0 && !monster.named
            && mawMonsterTier(monster.pStats->id) == 3
            && monster.pStats->aiType != MonsterTable::MonsterAiType::Wimp && monster.pFacts->bossAffix == 0)
        {
            candidates.push_back(index);
        }
    }

    if (bossCount <= 0 || candidates.empty())
    {
        return changed;
    }

    RandomStream selection(randomStreamKey(rootSeed, RandomDomain::BossSelect, map, resets));
    const size_t chosenCount = std::min(candidates.size(), size_t(bossCount));

    for (size_t chosen = 0; chosen < chosenCount; ++chosen)
    {
        const size_t pick = chosen + selection.uniform(0, uint32_t(candidates.size() - chosen - 1));
        std::swap(candidates[chosen], candidates[pick]);
        const size_t monsterIndex = candidates[chosen];
        makeBoss(*monsters[monsterIndex].pFacts, randomStreamKey(rootSeed, RandomDomain::BossStats, map, resets,
            monsterIndex), 0, baseLevelOf(monsters[monsterIndex]));
    }

    return true;
}

bool MawMonsterRules::makeBoss(ActorRulesetFacts &facts, uint64_t seed, uint8_t forcedAffix) const
{
    // Without the row a B boss starts from its own level (spawned bosses are C or A rows).
    return makeBoss(facts, seed, forcedAffix, bossBaseLevel(facts.level, facts.familyLevel, facts.tier,
        facts.tier == 1 ? facts.familyLevel : facts.level));
}

bool MawMonsterRules::makeBoss(ActorRulesetFacts &facts, uint64_t seed, uint8_t forcedAffix, int baseLevel) const
{
    if (facts.level <= 0)
    {
        return false;
    }

    const MawModelConfig config = mawModelConfig(m_rules.options(), 5);
    RandomStream stats(randomStreamKey(seed, RandomDomain::BossStats));
    RandomStream affix(randomStreamKey(seed, RandomDomain::BossAffix));
    const double healthDraw = unitDraw(stats);
    const double damageDraw = unitDraw(stats);
    facts.bossLevelDraw = float(unitDraw(stats));
    // The health multiplier reads the base level, before the band draw (generateBoss, MON:2999-3008).
    const double cappedLevel = std::min(baseLevel, BossLevelCap);
    const double flatten = config.austerity ? 4 : 1;
    facts.level = bossLevel(facts.level, baseLevel, facts.bossLevelDraw);
    facts.bossAffix = forcedAffix != 0
        ? forcedAffix
        : uint8_t(RolledBossAffixes[affix.uniform(0, uint32_t(RolledBossAffixes.size() - 1))]);
    // A script's health scale stays on top of the boss's.
    facts.bossHealthMultiplier *=
        float(2.5 * (1 + cappedLevel / BossLevelCap / flatten) * (1 + 0.5 * healthDraw / flatten));
    facts.bossDamageMultiplier = float(1.2 + 0.2 * damageDraw);

    // A rolled boss may be a Broodlord (1 %) and then an Omnipotent one (0.1 %, over a Broodlord's numbers too); x2
    // in Doom, x3 from Insanity (zzMaw-Monsters.lua:3030-3060).
    const double chances = config.insanityMode || config.madnessMode ? 3 : config.doomMode ? 2 : 1;

    if (forcedAffix == 0 && config.madnessMode)
    {
        // Beyond Madness: the two chances carry bad-luck protection, a Broodlord has twice the health and half again
        // the damage, an Omnipotent boss four and two times, one or the other; none in the Arena or on a completed
        // map (zzMaw-Monsters.lua:3028-3047, 3189-3235).
        MawGameState &state = m_rules.state();
        const std::string mapFileName = lowerFileName(m_rules.currentMap());

        if (mapFileName != "d42.blv" && !state.clearedSinceRefill.contains(mapFileName))
        {
            const double broodlordRoll = unitDraw(affix);
            const double omnipotentRoll = unitDraw(affix);

            if (broodlordRoll < mawPityChance(0.01 * chances, state.broodlordPity))
            {
                facts.bossAffix = uint8_t(MawBossAffix::Broodlord);
                facts.bossHealthMultiplier *= 2.0f;
                facts.bossDamageMultiplier *= 1.5f;
                state.broodlordPity = 0;
            }
            else
            {
                ++state.broodlordPity;

                if (omnipotentRoll < mawPityChance(0.001 * chances, state.omnipotentPity))
                {
                    facts.bossAffix = uint8_t(MawBossAffix::Omnipotent);
                    facts.bossHealthMultiplier *= 4.0f;
                    facts.bossDamageMultiplier *= 2.0f;
                    state.omnipotentPity = 0;
                }
                else
                {
                    ++state.omnipotentPity;
                }
            }
        }
    }
    else if (forcedAffix == 0)
    {
        if (unitDraw(affix) < 0.01 * chances)
        {
            facts.bossAffix = uint8_t(MawBossAffix::Broodlord);
            facts.bossHealthMultiplier *= 1.5f;
            facts.bossDamageMultiplier = float(1.5 + 0.3 * unitDraw(stats));
        }

        if (unitDraw(affix) < 0.001 * chances)
        {
            facts.bossAffix = uint8_t(MawBossAffix::Omnipotent);
            facts.bossHealthMultiplier *= 4.0f;
            facts.bossDamageMultiplier = float(2 + 0.5 * unitDraw(stats));
        }
    }

    // A dimension map's stronger bosses (zzMaw-Monsters.lua:3009-3011, 3070-3072).
    if (const std::optional<double> strength = m_rules.mapAffix(MawMapAffix::BossStrength))
    {
        facts.bossHealthMultiplier *= float(1 + *strength / 100);
        facts.bossDamageMultiplier *= float(1 + *strength / 100);
    }

    // A Cryptic boss fights with one of the other rolled affixes, drawn from its own stream so the rolls above stay
    // as they were (getCrypticSkill, zzMaw-Monsters.lua:3074-3077, 3192-3209).
    facts.crypticAffix = 0;

    if (facts.bossAffix == uint8_t(MawBossAffix::Cryptic))
    {
        std::vector<MawBossAffix> pool;

        for (const MawBossAffix candidate : RolledBossAffixes)
        {
            if (candidate != MawBossAffix::Cryptic)
            {
                pool.push_back(candidate);
            }
        }

        RandomStream hidden(randomStreamKey(seed, RandomDomain::BossAffix, uint64_t(MawBossAffix::Cryptic)));
        facts.crypticAffix = uint8_t(pool[hidden.uniform(0, uint32_t(pool.size() - 1))]);
    }

    return true;
}

bool MawMonsterRules::keepsDeathDrop(const ItemDefinition &item, std::mt19937 &rng) const
{
    static constexpr std::array<uint32_t, 5> Thinned = {217, 632, 633, 640, 654};
    std::uniform_real_distribution<double> unit(0.0, 1.0);

    if (unit(rng) < 0.8)
    {
        return false;
    }

    const bool thinned = std::find(Thinned.begin(), Thinned.end(), item.itemId) != Thinned.end()
        || item.equipStat == "Reagent";
    return !thinned || unit(rng) < 0.2;
}

LootWithoutCorpse MawMonsterRules::lootWithoutCorpse(const CorpseLootContext &context) const
{
    static constexpr std::array<int16_t, 9> WaterMonsters = {244, 245, 246, 532, 533, 534, 625, 626, 627};
    const ActorRulesetFacts *pFacts = context.pFacts;

    if (pFacts == nullptr || pFacts->level <= 0 || context.pStats == nullptr || context.pMap == nullptr)
    {
        return {};
    }

    CorpseLoot loot;
    const bool boss = pFacts->bossAffix != 0;
    rollCraftingDrops(m_rules, context, pFacts->level, boss, loot);
    rollDimensionMapDrop(m_rules, context, pFacts->level, boss, loot);
    LootWithoutCorpse result;
    result.items = std::move(loot.extraItems);
    result.toParty =
        std::find(WaterMonsters.begin(), WaterMonsters.end(), context.pStats->id) != WaterMonsters.end();
    return result;
}

CorpseLoot MawMonsterRules::corpseLoot(const CorpseLootContext &context) const
{
    const ActorRulesetFacts *pFacts = context.pFacts;

    if (pFacts == nullptr || pFacts->level <= 0 || context.pStats == nullptr || context.pMap == nullptr)
    {
        return MonsterRules::corpseLoot(context);
    }

    const MonsterTable::MonsterStatsEntry &stats = *context.pStats;
    const MawModelConfig config = mawModelConfig(m_rules.options(), 5);

    // Road to Insanity and Beyond Madness: a resurrected monster's corpse holds no gold and no item
    // (zzMaw-Monsters.lua:4139-4145); risen monsters never drop gems or specials in any mode. Beyond Madness's arenas,
    // 7d05 and bounty maps neither.
    if ((pFacts->risen && config.insanityMode) || m_rules.madnessRewardlessMap(context.pMap->fileName))
    {
        CorpseLoot empty;
        empty.loot = stats.loot;
        empty.loot.goldDiceRolls = 0;
        empty.loot.goldDiceSides = 0;
        empty.loot.itemChance = 0;
        // Reagents and Endless Potions still come (audit ALC-12).
        if (context.part != CorpseLootPart::Table)
        {
            rollCraftingDrops(m_rules, context, pFacts->level, pFacts->bossAffix != 0, empty);
        }

        return empty;
    }

    RandomStream stream(randomStreamKey(m_rules.randomRootSeed(), RandomDomain::CorpseLoot,
        randomNameKey(context.pMap->fileName), context.visitSeed, context.actorIndex));
    CorpseLoot result;
    result.loot = stats.loot;
    result.seed = stream();
    result.dropLevel = pFacts->level;
    // Morcarack (place name 160) drops an item as a boss does, without a boss's gold (IT:268-293).
    constexpr uint32_t Morcarack = 160;
    const bool affixBoss = pFacts->bossAffix != 0;
    result.boss = affixBoss || context.uniqueNameId == Morcarack;
    MonsterTable::LootPrototype &loot = result.loot;
    const int level = pFacts->level;
    const int tier = pFacts->tier > 0 ? pFacts->tier : mawMonsterTier(stats.id);

    const MonsterTable::MonsterStatsEntry *pFamilyB = context.pMonsterTable != nullptr
        ? context.pMonsterTable->findStatsById(int16_t(mawFamilyBId(stats.id)))
        : nullptr;
    const double familyBaseLevel = pFamilyB != nullptr ? pFamilyB->level : stats.level;
    // The table caps a monster's level at 255 where MAW reads it for loot.
    const double tableLevel = std::min(level, 255);

    // Gold: (the map's bolster + the family's B level) x 7.5, half for the weak and twice for the strong variant,
    // when that beats the table's dice (IT:207-226); a boss always carries sqrt(100 L)d sqrt(100 L) (MON:3013-3014).
    if (affixBoss)
    {
        loot.goldDiceRolls = loot.goldDiceSides = std::max(1, int(std::sqrt(100 * tableLevel)));
    }
    else if (loot.goldDiceRolls > 0 && loot.goldDiceSides > 0 && context.pMonsterTable != nullptr)
    {
        const double target = (m_rules.mapBolster(*context.pMonsterTable, *context.pMap) + familyBaseLevel) * 7.5
            * (tier == 1 ? 0.5 : tier == 3 ? 2 : 1);

        if (target > loot.goldDiceRolls * (loot.goldDiceSides + 1) / 2.0)
        {
            loot.goldDiceRolls = loot.goldDiceSides = std::max(1, int(std::min(std::sqrt(target), 255.0)));
        }
    }
    const double mapLow = m_rules.mapLevels().band(context.pMap->fileName)[0];
    const auto rolledGrade = [&stream](double grade)
    {
        // The fraction of a grade is rolled as a chance to round up.
        return int(std::floor(grade)) + (unitDraw(stream) < grade - std::floor(grade) ? 1 : 0);
    };

    if (result.boss)
    {
        // A Broodling drops an item 30 %, 10 % or 4 % of the time by its tier (zzMaw-Items.lua:270-279).
        const bool broodling = pFacts->bossAffix == uint8_t(MawBossAffix::Broodling);
        loot.itemChance = !broodling ? 100 : tier == 3 ? 30 : tier == 2 ? 10 : 4;
        // The grade reads a unique monster's level, and a boss's when its level was drawn again in its band; other
        // bosses read their row's level, at least the map's low one (IT:283-293).
        double gradeLevel = std::max<double>(stats.level, mapLow);

        if (pFacts->unique)
        {
            gradeLevel = level;
        }
        else if (affixBoss && context.pMonsterTable != nullptr)
        {
            const std::unordered_map<int, int> &levels = m_rules.monsterLevels(*context.pMonsterTable, *context.pMap);
            const int baseLevel = levelOf(levels, stats.id, stats.level);
            const int familyLevel = levelOf(levels, mawFamilyBId(stats.id), baseLevel);
            const int candidate = bossBaseLevel(
                baseLevel, familyLevel, uint8_t(tier), levelOf(levels, stats.id + 1, baseLevel));

            if (bossLevelRedrawn(baseLevel, candidate))
            {
                gradeLevel = level;
            }
        }

        loot.itemLevel = std::clamp(rolledGrade(gradeLevel / 20 + 2), 2, 6);
    }
    else
    {
        double chance = std::ceil(std::sqrt(tableLevel) * (1 + tier) * 0.5 + std::min(loot.itemChance, 50) * 0.3);
        chance = config.doomMode ? mawRound(chance * 0.5) : config.difficulty >= 6 ? mawRound(chance * 0.75) : chance;
        int grade = rolledGrade((std::max(familyBaseLevel, mapLow) + 10 * tier) / 20);

        if (grade <= 0)
        {
            chance *= std::pow(2.0, grade - 1);
        }

        loot.itemChance = std::clamp(int(mawRound(chance)), 0, 100);
        loot.itemLevel = std::clamp(grade, 1, 6);

        // A risen monster's corpse holds a quarter of the item chance and of the gold dice sides (IT:265-267).
        if (pFacts->risen)
        {
            loot.itemChance = int(mawRound(loot.itemChance / 4.0));
            loot.goldDiceSides = std::max(int(mawRound(loot.goldDiceSides / 4.0)), 1);
        }
    }

    // A boss drops one of the twelve kinds of equipment, each as often (MON:3016; the three weapon kinds are our
    // weapons, twice, and bows). Seven other drops in ten may be any kind of item.
    using LootKind = MonsterTable::LootItemKind;
    static constexpr std::array<LootKind, 12> BossKinds = {LootKind::Weapon, LootKind::Weapon, LootKind::Bow,
        LootKind::Armor, LootKind::Shield, LootKind::Helm, LootKind::Belt, LootKind::Cloak, LootKind::Gauntlets,
        LootKind::Boots, LootKind::Ring, LootKind::Amulet};

    if (result.boss)
    {
        loot.itemKind = BossKinds[stream.uniform(0, uint32_t(BossKinds.size() - 1))];
    }
    else if (loot.itemKind == LootKind::None || unitDraw(stream) < 0.7)
    {
        loot.itemKind = LootKind::Any;
    }

    // The crafting and map drops are rolled at the kill only, never by Telepathy, as their bad-luck counters move
    // (audit ALC-13).
    if (context.part != CorpseLootPart::Table)
    {
        rollCraftingDrops(m_rules, context, level, affixBoss, result);
        rollDimensionMapDrop(m_rules, context, level, affixBoss, result);
    }

    if (context.part == CorpseLootPart::Extras)
    {
        loot.goldDiceRolls = 0;
        loot.goldDiceSides = 0;
        loot.itemChance = 0;
    }

    // The Endless Arena's wave monsters carry no gold or item; its boss keeps its loot, and every kill still rolls
    // the crafting and dimension map drops (Global/zzMaw_Arena.lua:293-299).
    if (lowerFileName(context.pMap->fileName) == "d42.blv" && !result.boss)
    {
        loot.goldDiceRolls = 0;
        loot.goldDiceSides = 0;
        loot.itemChance = 0;
    }

    return result;
}

std::string MawMonsterRules::actorDisplayName(const ActorRulesetFacts &facts, const std::string &name) const
{
    const std::string named =
        facts.bossAffix != 0 ? mawBossAffixName(MawBossAffix(facts.bossAffix)) + " " + name : name;
    return facts.risen ? "Resurrected " + named : named;
}

float MawMonsterRules::actorDrawScale(const ActorRulesetFacts &facts, bool indoor) const
{
    if (facts.bossAffix == 0)
    {
        return 1.0f;
    }

    const float scale = indoor ? 1.4f : 2.0f;
    return facts.bossAffix == uint8_t(MawBossAffix::Omnipotent) ? scale + (scale - 1) * 0.5f : scale;
}

std::vector<std::string> MawMonsterRules::actorBadges(const ActorRulesetFacts &facts) const
{
    if (facts.bossAffix == 0)
    {
        return {};
    }

    // The special bosses show the skull alone, and so do the later affixes, which have no badge art yet.
    if (!omnipotentCovers(MawBossAffix(facts.bossAffix)))
    {
        return {"maw_boss_skull"};
    }

    std::string affix = mawBossAffixName(MawBossAffix(facts.bossAffix));
    std::transform(affix.begin(), affix.end(), affix.begin(), [](unsigned char c) { return char(std::tolower(c)); });
    return {"maw_boss_skull", "maw_boss_" + affix};
}

namespace
{
constexpr const char *WeakenedVariable = "MawMonstersWeakened";

// Nightmare and the Doom modes (MAW's bolster 300 or Mode 2); Austerity only at Nightmare.
bool revivalRules(const RulesetOptions &options)
{
    return options.difficulty == RulesetDifficulty::Nightmare
        || rulesetChallengeModeDifficulty(options.challengeMode).has_value();
}

// The weakened mark carries the map's reset count, so a reset map can raise its dead again.
int weakenedMark(const MawRules &rules, const std::string &mapFileName)
{
    return rules.state().resetCount(lowerFileName(mapFileName)) + 1;
}
}

void MawMonsterRules::leaveMap(IGameplayWorldRuntime &world) const
{
    m_rules.leaveMadnessMap();
    MapKillProgress progress;
    const EventRuntimeState *pRuntimeState = world.eventRuntimeState();

    if (!world.mapKillProgress(progress))
    {
        return;
    }

    if (revivalRules(m_rules.options()) && progress.indoor && pRuntimeState != nullptr)
    {
        const auto weakened = pRuntimeState->namedMapVars.find(WeakenedVariable);

        // Their experience is settled at the kill (MawExperienceRules::grantKillExperience): full in Nightmare and
        // Doom, none in Road to Insanity and Beyond Madness (DEVIATIONS 105).
        if (weakened == pRuntimeState->namedMapVars.end()
            || weakened->second != weakenedMark(m_rules, progress.mapFileName))
        {
            world.reviveSlainMonsters(1.0f);
            world.mapKillProgress(progress);
        }
    }

    // What the party leaves behind, for the Journal's Progress tab.
    MawMapVisit &visit = m_rules.state().mapVisits[lowerFileName(progress.mapFileName)];
    visit.slain = progress.slainMonsters;
    visit.counted = progress.countedMonsters;
    visit.lastRefillDay = m_loadDay;
}

std::optional<RulesetMapProgress> MawMonsterRules::mapProgress(const IGameplayWorldRuntime &world) const
{
    MapKillProgress progress;

    if (!world.mapKillProgress(progress))
    {
        return std::nullopt;
    }

    const std::string mapFileName = lowerFileName(progress.mapFileName);
    const RulesetOptions &options = m_rules.options();
    const RulesetChallengeMode mode = options.challengeMode;
    const MawGameState &state = m_rules.state();
    const EventRuntimeState *pRuntimeState = world.eventRuntimeState();
    MawMapProgressFacts facts;
    facts.insanityRules = mode == RulesetChallengeMode::RoadToInsanity || mode == RulesetChallengeMode::BeyondMadness;
    facts.revivalRules = revivalRules(options);
    facts.cleared = state.clearedSinceRefill.contains(mapFileName);
    facts.completedBefore = state.completedMaps.contains(mapFileName);
    facts.austerity = mode == RulesetChallengeMode::Austerity;
    facts.beyondMadness = mode == RulesetChallengeMode::BeyondMadness;
    facts.pDimensionRun = m_rules.dimensionRun(mapFileName);

    if (pRuntimeState != nullptr)
    {
        const auto weakened = pRuntimeState->namedMapVars.find(WeakenedVariable);
        facts.weakened = weakened != pRuntimeState->namedMapVars.end()
            && weakened->second == weakenedMark(m_rules, progress.mapFileName);
        const auto level = pRuntimeState->namedGlobalVars.find("MawArenaLevel");
        const auto percent = pRuntimeState->namedGlobalVars.find("MawArenaProgress");
        facts.arenaLevel = level != pRuntimeState->namedGlobalVars.end() ? level->second : 0;
        facts.arenaPercent = percent != pRuntimeState->namedGlobalVars.end() ? percent->second : 0;
    }

    return mawMapProgress(progress, facts);
}

namespace
{
// monTbl: the C-tier monsters that are not wimps (less 462 and 579), by their table level.
std::vector<const MonsterTable::MonsterStatsEntry *> mawArenaFamilies(const MonsterTable &monsterTable)
{
    std::vector<const MonsterTable::MonsterStatsEntry *> families;

    for (int monsterId = 3; monsterId <= 651; monsterId += 3)
    {
        const MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(int16_t(monsterId));

        if (pStats != nullptr && pStats->aiType != MonsterTable::MonsterAiType::Wimp && monsterId != 462
            && monsterId != 579)
        {
            families.push_back(pStats);
        }
    }

    std::stable_sort(families.begin(), families.end(),
        [](const MonsterTable::MonsterStatsEntry *pLeft, const MonsterTable::MonsterStatsEntry *pRight)
        {
            return pLeft->level < pRight->level;
        });
    return families;
}
}

int16_t MawMonsterRules::arenaWaveMonster(int wave, const MonsterTable &monsterTable) const
{
    const std::vector<const MonsterTable::MonsterStatsEntry *> families = mawArenaFamilies(monsterTable);

    if (families.empty() || wave <= 0)
    {
        return 0;
    }

    // The wave's family, its B variant (the arena rolls the tier).
    return int16_t(families[size_t(wave - 1) % families.size()]->id - 1);
}

uint32_t MawMonsterRules::bountyReward(const MonsterTable::MonsterStatsEntry &stats) const
{
    // getPartyLevel(4): every continent's bank but the "other" one.
    return uint32_t(std::max(0.0, mawRound(stats.level + m_rules.state().levelOutside(0))) * 100);
}

std::optional<std::string> MawMonsterRules::bountyRefusal(const IGameplayWorldRuntime &world) const
{
    MapKillProgress progress;

    if (world.mapKillProgress(progress)
        && !m_rules.state().clearedSinceRefill.contains(lowerFileName(progress.mapFileName)))
    {
        return "You need to clear the area COMPLETELY first.";
    }

    return std::nullopt;
}

std::optional<BountyTarget> MawMonsterRules::spawnBountyTarget(
    IGameplayWorldRuntime &world,
    float x,
    float y,
    float z,
    uint32_t seed) const
{
    const MonsterTable *pMonsterTable = world.monsterTable();
    if (pMonsterTable == nullptr)
    {
        return std::nullopt;
    }

    const std::vector<const MonsterTable::MonsterStatsEntry *> families = mawArenaFamilies(*pMonsterTable);

    if (families.empty())
    {
        return std::nullopt;
    }

    std::mt19937 rng(seed);
    const MonsterTable::MonsterStatsEntry &target =
        *families[std::uniform_int_distribution<size_t>(0, families.size() - 1)(rng)];
    const MonsterTable::MonsterStatsEntry *pFamilyB = pMonsterTable->findStatsById(int16_t(target.id - 1));
    GameplayMonsterSpawnRequest request;
    request.monsterId = int16_t(target.id);
    request.x = x;
    request.y = y;
    request.z = z;
    request.radius = 256;
    request.group = 2;
    request.moveSpeed = 350;
    // The map becomes a bounty map (mapvars.mawBounty): every monster on it, the hunt's included, sits at its table
    // level plus the party's banked levels less 2/3 of the target family's B level, and its walkers shoot too
    // (BountyHunt.lua:214, MON:591-593, 634).
    const int bounty = int(mawRound(std::max(
        0.0, m_rules.state().levelOutside(0) - (pFamilyB != nullptr ? pFamilyB->level : target.level) / 1.5)));

    if (EventRuntimeState *pRuntimeState = world.eventRuntimeState())
    {
        pRuntimeState->namedMapVars[BountyMapVariable] = bounty + 1;
    }

    m_rules.setBountyLevel(bounty);
    world.refreshRulesetMonsters();
    request.boss = true;
    request.seed = rng();
    const std::vector<size_t> hunted = world.spawnMonsters(request);
    request.boss = false;
    request.tierWeights = {55, 30, 15};

    // The bounty texts name the boss as spawned and a "Bounty" note marks its spot (BountyHunt.lua:216-231).
    BountyTarget result;
    result.monsterId = int16_t(target.id);
    result.mapNote = "Bounty";
    GameplayRuntimeActorState huntedState = {};

    if (!hunted.empty() && world.actorRuntimeState(hunted.front(), huntedState))
    {
        result.bossAffix = huntedState.rulesetFacts.bossAffix;
    }

    // An Omnipotent target brings 100-200 of its kin across the map (BountyHunt.lua:220-224).
    if (result.bossAffix == uint8_t(MawBossAffix::Omnipotent))
    {
        request.count = std::uniform_int_distribution<uint32_t>(100, 200)(rng);
        request.radius = 2048;
        request.seed = rng();
        world.spawnMonsters(request);
    }

    request.count = std::uniform_int_distribution<uint32_t>(5, 15)(rng);
    request.radius = 1024;
    request.seed = rng();
    world.spawnMonsters(request);
    return result;
}

bool MawMonsterRules::bountyKillCounts(const ActorRulesetFacts &facts) const
{
    return facts.bossAffix != 0;
}

bool MawMonsterRules::bountyKillCountsElsewhere() const
{
    return false;
}

bool MawMonsterRules::bountyCancelledByOtherKill() const
{
    return true;
}

void MawMonsterRules::bountyClaimed() const
{
    ++m_rules.state().bountiesClaimed;
}

size_t MawMonsterRules::arenaMinimumTypes() const
{
    return 12;
}

int MawMonsterRules::arenaDrawLevel(
    const MonsterTable::MonsterStatsEntry &stats, const MonsterTable &monsterTable, const MapStatsEntry &map) const
{
    // The engine's draw reads MonstersTxt levels after recalculateMonsterTable, in the byte field (MawCore/Fixes.lua:87,
    // Engine.lua setArenaPoolFallback), so a Squire bout brings the types whose arena level suits the party.
    return std::min(levelOf(m_rules.monsterLevels(monsterTable, map), stats.id, stats.level), 255);
}

RulesetScriptInfo MawMonsterRules::scriptInfo(uint32_t continentId) const
{
    RulesetScriptInfo info;
    info.rulesetId = "maw";
    info.difficulty = int(m_rules.options().difficulty);
    // MAW's bolsterLevel as the map scripts read it (recalculateMonsterTable, MON:416-441): the bank less 4 (^1.015
    // in Austerity), Beyond Madness's fixed map level, +20 per reset; a dimension run's power x 10 + 20 instead.
    const std::string mapFile = lowerFileName(m_rules.currentMap());
    const MawMapLevels &mapLevels = m_rules.mapLevels();
    double level = std::max(0.0, m_rules.state().levelOutside(continentId) - 4);
    level = mawModelConfig(m_rules.options(), 5).austerity ? std::pow(level, 1.015) : level;

    if (m_rules.options().challengeMode == RulesetChallengeMode::BeyondMadness && mapLevels.madnessLevel(mapFile) > 0
        && !mapLevels.isMadnessStartingMap(mapFile))
    {
        level = mapLevels.madnessLevel(mapFile);
    }

    level += 20.0 * m_rules.state().resetCount(mapFile);
    const MawDimensionRun *pRun = m_rules.dimensionRun(mapFile);
    info.bolsterLevel = int(pRun != nullptr ? pRun->power * 10 + 20 : level);
    info.dimensionRun = pRun != nullptr;
    info.challengeMode = std::string(rulesetChallengeModeId(m_rules.options().challengeMode));
    return info;
}

int MawMonsterRules::mapRespawnDays(const MapStatsEntry &map) const
{
    // Road to Insanity and Beyond Madness: no map ever refills (zzMaw-Maps.lua:80-86, 166-168); a dimension map run
    // still refills its target through mapRefillForced.
    const RulesetChallengeMode mode = m_rules.options().challengeMode;

    if (mode == RulesetChallengeMode::RoadToInsanity || mode == RulesetChallengeMode::BeyondMadness)
    {
        return 0;
    }

    static constexpr std::array<std::pair<int, int>, 7> NeverRefill = {{
        {1, 8}, {13, 13}, {62, 70}, {72, 74}, {99, 100}, {140, 141}, {143, 151},
    }};

    for (const auto &[first, last] : NeverRefill)
    {
        if (map.id >= first && map.id <= last)
        {
            return 0;
        }
    }

    return map.respawnIntervalDays;
}

std::optional<std::string> MawMonsterRules::mapResetOffer(const std::string &mapFileName) const
{
    const std::string fileName = lowerFileName(mapFileName);
    const RulesetChallengeMode mode = m_rules.options().challengeMode;

    // Only a dungeon cleared since it last refilled: a reset refills it, so resets cannot be chained without a re-clear
    // (zzMaw-Maps.lua:166-188).
    if (!fileName.ends_with(".blv") || !m_rules.state().clearedSinceRefill.contains(fileName)
        || mode == RulesetChallengeMode::RoadToInsanity || mode == RulesetChallengeMode::BeyondMadness)
    {
        return std::nullopt;
    }

    const int resets = m_rules.state().resetCount(fileName);
    return "You have cleared this dungeon. Resetting it brings every monster back "
        + std::to_string(20 * (resets + 1)) + " levels stronger than at first, with no second completion reward.";
}

void MawMonsterRules::resetMap(const std::string &mapFileName) const
{
    const std::string fileName = lowerFileName(mapFileName);
    ++m_rules.state().mapResetCounts[fileName];
    m_forcedRefills.insert(fileName);
}

bool MawMonsterRules::mapRefillForced(const std::string &mapFileName) const
{
    const MawDimensionRun *pRun = m_rules.dimensionRun(mapFileName);
    return m_forcedRefills.contains(lowerFileName(mapFileName)) || (pRun != nullptr && pRun->entering);
}

void MawMonsterRules::decorationRaisedStats(
    const std::string &mapFileName, uint8_t decorVarIndex, uint8_t emptyState) const
{
    m_rules.state().usedStatDecorations[lowerFileName(mapFileName)][decorVarIndex] = emptyState;
}

void MawMonsterRules::decorationsRenumbered(const std::string &mapFileName, std::span<const int16_t> remap) const
{
    const auto used = m_rules.state().usedStatDecorations.find(lowerFileName(mapFileName));

    if (used == m_rules.state().usedStatDecorations.end())
    {
        return;
    }

    std::unordered_map<uint8_t, uint8_t> renumbered;

    for (const auto &[decorVarIndex, emptyState] : used->second)
    {
        if (decorVarIndex < remap.size() && remap[decorVarIndex] >= 0)
        {
            renumbered[uint8_t(remap[decorVarIndex])] = emptyState;
        }
    }

    used->second = std::move(renumbered);
}

void MawMonsterRules::mapLoaded(const std::string &mapFileName, bool refilled) const
{
    const std::string fileName = lowerFileName(mapFileName);
    MawGameState &state = m_rules.state();
    m_forcedRefills.erase(fileName);
    m_usedDecorationsMap = fileName;

    if (refilled)
    {
        // Its monsters are back: it has to be cleared again (MAW: fresh map variables, zzMaw-Maps.lua:166-188).
        state.clearedSinceRefill.erase(fileName);
        state.mapsDropped.erase(fileName);
        std::random_device device;
        m_refillSeeds[fileName] = (uint64_t(device()) << 32) | device();
    }

    const auto run = state.dimensionRuns.find(fileName);

    if (run == state.dimensionRuns.end())
    {
        return;
    }

    if (run->second.entering)
    {
        run->second.entering = false;
    }
    else if (refilled)
    {
        state.dimensionRuns.erase(run);
    }
}

void MawMonsterRules::enterMap(MapStatsEntry &map, const MonsterTable &monsterTable) const
{
    m_rules.setCurrentMap(map.fileName);
    const MawDimensionRun *pRun = m_rules.dimensionRun(map.fileName);

    // The map's monster levels now, so its chests and ground items drop at its own level even when no monster is
    // left to resolve (audit ROB-2-2).
    if (pRun == nullptr)
    {
        m_rules.monsterLevels(monsterTable, map);
        return;
    }

    // The run's families take the place of the map's own (zzMaw-Maps.lua BeforeLoadMap): their picture without the
    // tier letter.
    const std::array<MapEncounterInfo *, 3> encounters = {&map.encounter1, &map.encounter2, &map.encounter3};

    for (size_t slot = 0; slot < encounters.size(); ++slot)
    {
        const MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(pRun->families[slot]);

        if (pStats != nullptr && pStats->pictureName.size() > 2)
        {
            encounters[slot]->pictureName = pStats->pictureName.substr(0, pStats->pictureName.size() - 2);
            encounters[slot]->monsterName = encounters[slot]->pictureName;
        }
    }

    m_rules.monsterLevels(monsterTable, map);
}

char MawMonsterRules::spawnTier(const MapStatsEntry &map, char tier, uint32_t seed) const
{
    const std::optional<double> chance = m_rules.mapAffix(map.fileName, MawMapAffix::HigherTier);

    if (!chance || tier >= 'C' || mawModelConfig(m_rules.options(), 5).difficulty < MawDifficultyIndex)
    {
        return tier;
    }

    RandomStream roll(randomStreamKey(m_rules.randomRootSeed(), RandomDomain::DimensionHigherTier,
        randomNameKey(map.fileName), seed, int(MawMapAffix::HigherTier)));
    return unitDraw(roll) < *chance / 100 ? char(tier + 1) : tier;
}

std::string MawMonsterRules::monsterResistanceText(int resistance, const ActorRulesetFacts &facts) const
{
    return std::to_string(mawCappedMonsterResistance(resistance, mawMonsterResistanceBonus(m_rules, facts)));
}

std::optional<std::pair<OpenBounty, std::string>> MawMonsterRules::bountyElsewhere(
    const std::vector<OpenBounty> &openBounties) const
{
    if (!mawModelConfig(m_rules.options(), 5).insanityMode || openBounties.empty())
    {
        return std::nullopt;
    }

    const OpenBounty &bounty = openBounties.front();
    const MapStatsEntry *pMap =
        m_rules.mapTable() != nullptr ? m_rules.mapTable()->findByFileName(bounty.mapFileName) : nullptr;
    return std::pair(bounty, pMap != nullptr ? pMap->name : bounty.mapFileName);
}

std::optional<MonsterInspectNumbers> MawMonsterRules::inspectNumbers(const MonsterInspectQuery &query) const
{
    return mawMonsterInspectNumbers(m_rules, query);
}

void MawMonsterRules::adjustMapEncounters(MapStatsEntry &map) const
{
    const RulesetOptions &options = m_rules.options();
    const bool doom = options.challengeMode == RulesetChallengeMode::Doom
        || options.challengeMode == RulesetChallengeMode::RoadToInsanity
        || options.challengeMode == RulesetChallengeMode::BeyondMadness;
    const bool insanity = options.challengeMode == RulesetChallengeMode::RoadToInsanity
        || options.challengeMode == RulesetChallengeMode::BeyondMadness;
    const bool madness = options.challengeMode == RulesetChallengeMode::BeyondMadness;
    const std::array<MapEncounterInfo, 3> table = {map.encounter1, map.encounter2, map.encounter3};
    std::array<MapEncounterInfo *, 3> slots = {&map.encounter1, &map.encounter2, &map.encounter3};

    // Each rule starts from the table's counts; a later rule overwrites an earlier one (zzMaw-Monsters.lua
    // AdjustMonsterDensity). Doom and up never use the Hard to Nightmare rules: they play at bolster 600.
    for (size_t slot = 0; slot < slots.size(); ++slot)
    {
        MapEncounterInfo &encounter = *slots[slot];
        const MapEncounterInfo &base = table[slot];

        if (!doom
            && (options.difficulty == RulesetDifficulty::Hard || options.difficulty == RulesetDifficulty::Hell)
            && encounter.maxCount <= 3)
        {
            encounter.minCount = std::max(base.minCount, 1);
            encounter.maxCount = base.maxCount + 1;
        }

        if (!doom && options.difficulty == RulesetDifficulty::Nightmare)
        {
            if (base.maxCount > 1)
            {
                encounter.minCount = std::max(base.minCount, 2);
                encounter.maxCount = base.maxCount + 1;
            }

            encounter.difficulty = std::min(base.difficulty + 1, 5);
        }

        if (doom)
        {
            if (base.maxCount > 1)
            {
                encounter.minCount = std::max(base.minCount, 2);
                encounter.maxCount = base.maxCount + 2;
            }

            encounter.difficulty = std::min(base.difficulty + 1, 5);
        }

        if (insanity && table[0].maxCount > 1)
        {
            encounter.minCount = std::max(base.minCount, 3);
        }

        if (madness && base.maxCount > 1)
        {
            encounter.minCount = std::max(base.minCount, 3);
            encounter.maxCount = base.maxCount + 3;
        }

        encounter.minCount = std::min(encounter.minCount, encounter.maxCount);
    }

    // The Hall under the Hill's unicorns stay 1-3 on every difficulty (MON:903-908).
    constexpr int HallUnderTheHill = 96;

    if (map.id == HallUnderTheHill)
    {
        map.encounter3.minCount = 1;
        map.encounter3.maxCount = 3;
    }

    // A dimension map: every group's upper count x (1 + (power + 20) x affixes / 300), rounded.
    if (const MawDimensionRun *pRun = m_rules.dimensionRun(map.fileName))
    {
        const double multiplier = 1 + mawDimensionStrength(pRun->power, pRun->affixCount()) / 300;

        for (MapEncounterInfo *pEncounter : slots)
        {
            pEncounter->maxCount = int(mawRound(pEncounter->maxCount * multiplier));
        }
    }
}

void MawMonsterRules::hatchBoss(IGameplayWorldRuntime &world, uint32_t actorId, const HatchingBoss &boss) const
{
    std::mt19937_64 rng(m_rules.randomRootSeed() ^ (uint64_t(actorId) * 0x9e3779b97f4a7c15ull));
    GameplayMonsterSpawnRequest request;
    request.x = boss.x;
    request.y = boss.y;
    request.z = boss.z;
    request.radius = 256;
    request.boss = true;
    request.moveSpeed = 350;
    const uint8_t tier = mawMonsterTier(boss.monsterId);
    const int16_t familyC = int16_t((boss.monsterId - 1) / 3 * 3 + 3);

    if (boss.affix == uint8_t(MawBossAffix::Omnipotent))
    {
        for (const MawBossAffix affix : RolledBossAffixes)
        {
            // Not the later four (OmnipotentExcluded, zzMaw-Monsters.lua:4149-4154).
            if (!omnipotentCovers(affix))
            {
                continue;
            }

            request.monsterId = familyC;
            request.bossAffix = uint8_t(affix);
            request.seed = rng();
            world.spawnMonsters(request);
        }
    }

    // A Broodling hatches the tier below its own; an A-tier one nothing.
    if (boss.affix == uint8_t(MawBossAffix::Broodling) && tier == 1)
    {
        return;
    }

    request.monsterId = boss.affix == uint8_t(MawBossAffix::Broodling) ? int16_t(boss.monsterId - 1) : familyC;
    request.count = 3;
    request.bossAffix = uint8_t(MawBossAffix::Broodling);
    request.seed = rng();
    world.spawnMonsters(request);
}

void MawMonsterRules::capInsanityFood(IGameplayWorldRuntime &world) const
{
    const RulesetChallengeMode mode = m_rules.options().challengeMode;
    Party *pParty = world.party();

    if ((mode != RulesetChallengeMode::RoadToInsanity && mode != RulesetChallengeMode::BeyondMadness)
        || pParty == nullptr)
    {
        return;
    }

    MawGameState &state = m_rules.state();

    if (!world.isIndoorMap())
    {
        pParty->addFood(state.heldFood);
        state.heldFood = 0;
        return;
    }

    // Map.Monsters.High is the last monster's index. A held amount adds up across dungeons (MAW overwrites it).
    const int cap = 15 + std::max(0, int(world.mapActorCount()) - 1) / 25;

    if (pParty->food() > cap)
    {
        state.heldFood += pParty->food() - cap;
        pParty->addFood(cap - pParty->food());
    }
}

void MawMonsterRules::updateMonsters(IGameplayWorldRuntime &world, float deltaSeconds) const
{
    constexpr float RegenerationTickSeconds = 0.1f;
    constexpr float AuraTickSeconds = 0.5f;
    constexpr float LeecherRange = 1500.0f;
    constexpr float ShadowRange = 2000.0f;
    constexpr double LevelCap = 255;

    // The barrels and cauldrons that raised a stat stay empty, also after a refill rolled them again (MAW's
    // AfterLoadMap turns their events into the empty barrel).
    if (EventRuntimeState *pRuntimeState = world.eventRuntimeState();
        !m_usedDecorationsMap.empty() && pRuntimeState != nullptr)
    {
        const auto used = m_rules.state().usedStatDecorations.find(m_usedDecorationsMap);

        if (used != m_rules.state().usedStatDecorations.end()
            && lowerFileName(pRuntimeState->mapFileName) == m_usedDecorationsMap)
        {
            bool changed = false;

            for (const auto &[decorVarIndex, emptyState] : used->second)
            {
                if (decorVarIndex < pRuntimeState->decorVars.size()
                    && pRuntimeState->decorVars[decorVarIndex] != emptyState)
                {
                    pRuntimeState->decorVars[decorVarIndex] = emptyState;
                    changed = true;
                }
            }

            if (changed)
            {
                world.applyEventRuntimeState();
            }
        }

        m_usedDecorationsMap.clear();
    }

    // Dimension affix 25 slows the party by X % while enemies are near (yellow or red): MAW takes that share of each
    // tick's movement back (zzMaw_Mapping.lua:7-18); we scale its speed instead (DEVIATIONS 60).
    if (Party *pParty = world.party(); pParty != nullptr)
    {
        const std::optional<double> slow = m_rules.mapAffix(MawMapAffix::PlayerMovement);
        pParty->setRulesMovementMultiplier(
            slow && partyHasYellowAlert(world) ? float(1 - std::clamp(*slow, 0.0, 100.0) / 100) : 1.0f);
    }

    // Beyond Madness's death ledger, with enemies near as the detector shows them (yellow or red).
    if (const Party *pParty = world.party();
        pParty != nullptr && m_rules.options().challengeMode == RulesetChallengeMode::BeyondMadness)
    {
        m_rules.updateMadnessLedger(*pParty, world.gameMinutes(), partyHasYellowAlert(world));
    }

    // A new map starts its boss tracks afresh: actor ids restart per map, and the next map's runtime may take the old
    // one's address (audit ROB-2-4).
    if (m_trackedMap != m_rules.currentMap())
    {
        m_trackedMap = m_rules.currentMap();
        // The map's refill timer runs from the day it was loaded (GameApplication's lastRespawnDay).
        m_loadDay = int32_t(std::floor(std::max(0.0f, world.gameMinutes()) / (24.0f * 60.0f))) + 1;
        m_bossTracks.clear();
        m_regenerationSeconds = 0;
        m_auraSeconds = 0;
    }

    if (m_foodCapMap != m_rules.currentMap())
    {
        m_foodCapMap = m_rules.currentMap();
        capInsanityFood(world);
    }

    if (m_hatchingMap != m_rules.currentMap())
    {
        m_hatchingMap = m_rules.currentMap();
        m_hatchingBosses.clear();
        m_livingMonsters.clear();
        std::optional<int> levels;

        if (const EventRuntimeState *pRuntimeState = world.eventRuntimeState())
        {
            if (const auto bounty = pRuntimeState->namedMapVars.find(BountyMapVariable);
                bounty != pRuntimeState->namedMapVars.end())
            {
                levels = std::max(0, bounty->second - 1);
            }
        }

        if (levels != m_rules.bountyLevel())
        {
            m_rules.setBountyLevel(levels);
            world.refreshRulesetMonsters();
        }
    }

    // The special bosses seen alive hatch when they are found dead.
    for (size_t actorIndex = 0; actorIndex < world.mapActorCount(); ++actorIndex)
    {
        GameplayActorRulesView state = {};

        if (!world.actorRulesView(actorIndex, state)
            || !specialBoss(state.rulesetFacts.bossAffix))
        {
            continue;
        }

        if (!state.isDead && state.currentHp > 0)
        {
            m_hatchingBosses[state.actorId] = HatchingBoss{
                state.monsterId, state.rulesetFacts.bossAffix, state.preciseX, state.preciseY, state.preciseZ};
            continue;
        }

        const auto hatching = m_hatchingBosses.find(state.actorId);

        if (hatching != m_hatchingBosses.end() && hatching->second.monsterId == state.monsterId)
        {
            const HatchingBoss boss = hatching->second;
            m_hatchingBosses.erase(hatching);
            hatchBoss(world, state.actorId, boss);
        }
    }

    // A dimension map's monsters may call one of their family as they die, however they die (zzAlchemy.lua:1118-1148):
    // not the risen, the party's allies, nor Beyond Madness's arenas and bounty maps.
    if (const std::optional<double> summon = m_rules.mapAffix(MawMapAffix::SummonOnDeath))
    {
        const bool rewardless = m_rules.madnessRewardlessMap(m_rules.currentMap());

        for (size_t actorIndex = 0; actorIndex < world.mapActorCount(); ++actorIndex)
        {
            GameplayActorRulesView state = {};

            if (!world.actorRulesView(actorIndex, state))
            {
                continue;
            }

            if (!state.isDead && state.currentHp > 0)
            {
                m_livingMonsters[state.actorId] = state.monsterId;
                continue;
            }

            const auto living = m_livingMonsters.find(state.actorId);

            if (living == m_livingMonsters.end() || living->second != state.monsterId)
            {
                continue;
            }

            m_livingMonsters.erase(living);
            std::mt19937_64 rng(m_rules.randomRootSeed() ^ (uint64_t(state.actorId) * 0xc2b2ae3d27d4eb4full)
                ^ randomNameKey(m_rules.currentMap()));

            if (state.rulesetFacts.risen || state.partyAlly || rewardless
                || std::uniform_real_distribution<double>(0, 1)(rng) >= *summon / 100)
            {
                continue;
            }

            GameplayMonsterSpawnRequest request;
            request.monsterId = int16_t(mawFamilyBId(state.monsterId));
            request.tierWeights = {55, 30, 15};
            request.x = state.preciseX;
            request.y = state.preciseY;
            request.z = state.preciseZ;
            request.radius = 128;
            request.moveSpeed = 350;
            request.seed = rng();
            world.spawnMonsters(request);
        }
    }

    // MAW checks the map's completion on a timer, so a kill by anyone counts (zzMaw-Timers.lua:92).
    m_completionSeconds += deltaSeconds;

    if (m_completionSeconds >= 1.0f)
    {
        m_completionSeconds = 0;
        MapKillProgress progress;
        Party *pCompletingParty = world.party();

        if (pCompletingParty != nullptr && world.mapKillProgress(progress))
        {
            const std::string message = pCompletingParty->rules().experience.rewardMapProgress(*pCompletingParty,
                progress);
            EventRuntimeState *pRuntimeState = world.eventRuntimeState();

            if (!message.empty() && pRuntimeState != nullptr)
            {
                pRuntimeState->statusMessages.push_back(message);
            }
        }
    }

    // From Hard up, the maps made for flying say so on arrival (zzMaw-Spells.lua:1020-1027).
    if (m_rules.currentMap() != m_announcedMap)
    {
        m_announcedMap = m_rules.currentMap();
        EventRuntimeState *pRuntimeState = world.eventRuntimeState();

        if (pRuntimeState != nullptr && m_rules.options().difficulty >= RulesetDifficulty::Hard
            && mawFlightMap(m_announcedMap))
        {
            pRuntimeState->statusMessages.push_back("Fly is allowed without restrictions here");
        }
    }

    // Nightmare's dead stop rising once 65 % of an indoor map's monsters are slain (checked each second).
    m_weakenSeconds += deltaSeconds;

    if (m_weakenSeconds >= 1.0f && revivalRules(m_rules.options()))
    {
        m_weakenSeconds = 0;
        MapKillProgress progress;
        EventRuntimeState *pRuntimeState = world.eventRuntimeState();

        if (pRuntimeState != nullptr && world.mapKillProgress(progress) && progress.indoor
            && progress.countedMonsters > 0 && double(progress.slainMonsters) / progress.countedMonsters >= 0.65)
        {
            int &mark = pRuntimeState->namedMapVars[WeakenedVariable];

            if (mark != weakenedMark(m_rules, progress.mapFileName))
            {
                mark = weakenedMark(m_rules, progress.mapFileName);
                pRuntimeState->statusMessages.push_back("Monsters are weakened and can no longer resurrect");
            }
        }
    }

    // A dimension map's regeneration: X % of full HP each second for every wounded monster (MAW heals only whichever
    // monster its script touched last; DEVIATIONS.md).
    const std::optional<double> mapRegeneration = m_rules.mapAffix(MawMapAffix::MonsterRegeneration);
    m_mapRegenerationSeconds = mapRegeneration ? m_mapRegenerationSeconds + deltaSeconds : 0;

    for (; m_mapRegenerationSeconds >= 1.0f; m_mapRegenerationSeconds -= 1.0f)
    {
        for (size_t actorIndex = 0; actorIndex < world.mapActorCount(); ++actorIndex)
        {
            GameplayActorRulesView state = {};

            if (world.actorRulesView(actorIndex, state) && !state.isDead && state.currentHp > 0
                && state.currentHp < state.maxHp)
            {
                world.healMapActor(actorIndex, std::max(1, int(mawRound(state.maxHp * *mapRegeneration / 100))));
            }
        }
    }

    Party *pParty = world.party();
    m_regenerationSeconds += deltaSeconds;
    m_auraSeconds += deltaSeconds;
    const int regenerationTicks = int(m_regenerationSeconds / RegenerationTickSeconds);
    const bool auraTick = m_auraSeconds >= AuraTickSeconds;
    m_regenerationSeconds -= float(regenerationTicks) * RegenerationTickSeconds;
    m_auraSeconds = auraTick ? 0.0f : m_auraSeconds;
    // Every Leecher (and Omnipotent) boss in range drains on its own (leecher, MON:3390-3428).
    std::vector<double> leechStrengths;
    bool shadowNearby = false;

    for (size_t actorIndex = 0; actorIndex < world.mapActorCount(); ++actorIndex)
    {
        GameplayActorRulesView state = {};

        if (!world.actorRulesView(actorIndex, state) || state.rulesetFacts.bossAffix == 0 || state.isDead
            || state.currentHp <= 0)
        {
            continue;
        }

        const ActorRulesetFacts &facts = state.rulesetFacts;

        if (mawHasBossAffix(facts, MawBossAffix::Regenerating))
        {
            BossTrack &track = m_bossTracks[state.actorId];
            // It regenerates once the party hit it, slower with each hit, counted with the actor (FCOR-2-6).
            const int hits = facts.regeneratingHits;

            if (hits > 0 && regenerationTicks > 0)
            {
                const double level = std::min(double(state.rulesetFacts.level), LevelCap);
                track.healCarry += regenerationTicks * state.maxHp * 0.01 * std::pow(0.99, hits)
                    / (1 + level / 50);
                const int heal = int(track.healCarry);
                track.healCarry -= heal;

                if (heal > 0 && world.healMapActor(actorIndex, heal))
                {
                    state.currentHp = std::min(state.maxHp, state.currentHp + heal);
                }
            }
        }

        if (!auraTick || pParty == nullptr)
        {
            continue;
        }

        const float dx = state.preciseX - world.partyX();
        const float dy = state.preciseY - world.partyY();
        const float dz = state.preciseZ - world.partyFootZ();
        const float distance = std::sqrt(dx * dx + dy * dy + dz * dz);

        if (mawHasBossAffix(facts, MawBossAffix::Leecher) && distance < LeecherRange)
        {
            const double closeness = (LeecherRange - distance) / LeecherRange;
            leechStrengths.push_back(closeness * closeness * 0.05);
        }

        shadowNearby = shadowNearby || (mawHasBossAffix(facts, MawBossAffix::Shadow) && distance < ShadowRange);
    }

    if (pParty == nullptr || !auraTick)
    {
        return;
    }

    m_leechCarry.resize(pParty->members().size());

    for (const double strength : leechStrengths)
    {
        for (size_t memberIndex = 0; memberIndex < pParty->members().size(); ++memberIndex)
        {
            Character *pMember = pParty->member(memberIndex);
            auto &[healthCarry, manaCarry] = m_leechCarry[memberIndex];

            if (pMember == nullptr)
            {
                continue;
            }

            // Fractions carry to the next tick; spell points drain even from a member below one hit point.
            if (pMember->health >= 1)
            {
                healthCarry += pMember->maxHealth * strength;
                const int taken = int(std::floor(healthCarry));
                pMember->health = std::max(1, pMember->health - taken);
                healthCarry -= taken;
            }

            manaCarry += pMember->spellPoints * strength;
            const int drained = int(std::floor(manaCarry));
            pMember->spellPoints = std::max(0, pMember->spellPoints - drained);
            manaCarry -= drained;
        }
    }

    // The aura pass leaves Wizard Eye off while the Shadow is near.
    m_rules.setShadowBossNearby(shadowNearby);

    if (shadowNearby && pParty->hasPartyBuff(PartyBuffId::WizardEye))
    {
        pParty->clearPartyBuff(PartyBuffId::WizardEye);
    }
}

namespace
{
// Nightmare and the Doom family of challenge modes (MAW's BolsterAmount 300 or Mode 2).
bool nightmareRules(const RulesetOptions &options)
{
    return options.difficulty == RulesetDifficulty::Nightmare
        || options.challengeMode == RulesetChallengeMode::Doom
        || options.challengeMode == RulesetChallengeMode::RoadToInsanity
        || options.challengeMode == RulesetChallengeMode::BeyondMadness;
}
}

bool MawMonsterRules::teleportBlockedNearEnemies() const
{
    return nightmareRules(m_rules.options());
}

std::string MawMonsterRules::teleportBlockedText(bool townPortal) const
{
    return townPortal && m_rules.options().challengeMode == RulesetChallengeMode::BeyondMadness
        ? "Madness is not a place for cowards"
        : MonsterRules::teleportBlockedText(townPortal);
}

int MawMonsterRules::saveFoodCost(const std::string &mapFileName, bool indoor, bool enemiesNear) const
{
    std::string lowercaseMap = mapFileName;
    std::transform(lowercaseMap.begin(), lowercaseMap.end(), lowercaseMap.begin(),
                   [](unsigned char character) { return char(std::tolower(character)); });

    if (!nightmareRules(m_rules.options()) || m_rules.state().clearedSinceRefill.contains(lowercaseMap))
    {
        return 0;
    }

    return indoor ? (enemiesNear ? 10 : 2) : (enemiesNear ? 3 : 0);
}

namespace
{
std::string formatQuestText(const std::string &format, const std::string &name, int number)
{
    std::string text;

    for (size_t index = 0; index < format.size(); ++index)
    {
        if (format[index] == '%' && index + 1 < format.size() && (format[index + 1] == 's' || format[index + 1] == 'd'))
        {
            text += format[index + 1] == 's' ? name : std::to_string(number);
            ++index;
        }
        else
        {
            text += format[index];
        }
    }

    return text;
}
}

std::optional<std::string> MawMonsterRules::rulesTopic(const std::string &topic, Party &party) const
{
    if (topic != "dimensional_maps")
    {
        return std::nullopt;
    }

    const MawDimensionData &data = m_rules.dimensionData();
    const MawDimensionQuestRules &questRules = data.quest();
    MawDimensionQuest &quest = m_rules.state().dimensionQuest;
    quest.tierLevel = quest.tierLevel > 0 ? quest.tierLevel : questRules.firstTier;
    const int tier = quest.tierLevel;

    if (!quest.mapGiven)
    {
        uint32_t highest = 0;

        for (const Character &member : party.members())
        {
            highest = std::max(highest, member.level);
        }

        if (int(highest) < tier)
        {
            return formatQuestText(questRules.textTooLow, {}, tier);
        }

        // Keyed by the tier, so asking again after a reload gives the same map (rollQuestMap).
        RandomStream stream(randomStreamKey(m_rules.randomRootSeed(), RandomDomain::DimensionQuest, uint64_t(tier)));
        std::vector<uint16_t> pool = m_rules.dimensionMapPool();

        if (pool.empty())
        {
            pool = data.dungeons();
        }

        const double activeRoll = unitDraw(stream);
        const uint8_t activeSlots = activeRoll <= 0.1 ? 4 : activeRoll < 0.3 ? 3 : 2;
        const MawDimensionMap map = m_rules.rollDimensionMap(stream, pool, {true, true, true, true}, activeSlots,
            (tier - 20) / 10);
        const MapStatsEntry *pTarget =
            m_rules.mapTable() != nullptr ? m_rules.mapTable()->findById(map.mapId) : nullptr;
        const ItemTable *pItemTable = party.itemTable();

        if (pTarget == nullptr || pItemTable == nullptr || pItemTable->get(data.mapItemId()) == nullptr)
        {
            return std::nullopt;
        }

        InventoryItem item =
            ItemGenerator::makeInventoryItem(data.mapItemId(), *pItemTable, ItemGenerationMode::Generic);
        map.writeFields(item.rulesetFields);

        if (!party.tryGrantInventoryItem(item))
        {
            return std::string("Your packs are too full to take the map.");
        }

        quest.mapGiven = true;
        quest.cleared = false;
        return formatQuestText(questRules.textGive, pTarget->name,
            mawDimensionMapLevel(map.power, m_rules.mapLevels().band(pTarget->fileName)));
    }

    if (!quest.cleared)
    {
        return questRules.textNotCleared;
    }

    // AddGoldExp: the gold, and the same in experience to everyone as an event gives it.
    const int reward = quest.clearedLevel * 1000;
    const MapStatsEntry *pCurrentMap =
        m_rules.mapTable() != nullptr ? m_rules.mapTable()->findByFileName(m_rules.currentMap()) : nullptr;
    const uint32_t continentId = pCurrentMap != nullptr ? pCurrentMap->mergedContinentId : 0;
    party.addGold(reward);

    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        party.addExperienceToMember(memberIndex, m_rules.gameRules().experience.eventExperience(party, reward,
            continentId));
    }

    const std::string text = formatQuestText(questRules.textReward, quest.clearedMapName, reward);
    quest.done = quest.done || tier >= questRules.unlockTier;
    quest.tierLevel = data.nextQuestTier(tier);
    quest.mapGiven = false;
    quest.cleared = false;
    quest.clearedLevel = 0;
    quest.clearedMapName.clear();
    return text;
}
}
