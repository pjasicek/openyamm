// MM9 balance probe (devdocs/mm9_rework/BALANCE_PLAN.md section 4): reference parties built through the engine fight
// the monster packs of each MM9 chapter and each MM7 stage, with the engine's own attack, spell, hit and resistance
// rules. Read-only; reads the pack mixes written by balance_prototypes/probe_input.py and writes one result row per
// group.
//
//   openyamm_balance_probe <input.tsv> <output.tsv> [--runs N] [--mm9-items] [--no-mm9-changes] [--no-profiles]
//                          [--area SHARE] [--sp SHARE] [--dump]
//
// Input rows: world, stage, party_level, shop_tier, pack_size, monster_id, weight (tab separated, '#' comments).

#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "game/data/GameDataLoader.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayBolsterRuntime.h"
#include "game/party/Party.h"
#include "game/party/SkillData.h"
#include "game/party/SpellSchool.h"
#include "game/rules/GameRules.h"
#include "game/tables/ClassSkillTable.h"
#include "game/tables/ItemTable.h"
#include "game/tables/MonsterTable.h"
#include "game/tables/SpellTable.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <fstream>
#include <iostream>
#include <map>
#include <optional>
#include <random>
#include <sstream>
#include <string>
#include <vector>

using namespace OpenYAMM;
using namespace OpenYAMM::Game;

namespace
{
struct GroupRow
{
    std::string world;
    int stage = 0;
    int partyLevel = 1;
    int shopTier = 1;
    float packSize = 1.0f;
    int monsterId = 0;
    float weight = 0.0f;
};

struct Options
{
    int runs = 300;
    bool mm9Items = false;      // the party wears today's MM9 items instead of the tier's MM6-MM8 items
    bool mm9Changes = true;     // BALANCE_PLAN.md 3.2 on MM9 monsters (recovery, low-level damage, HP trim, spells)
    bool profiles = true;       // MM6-MM8-style resistance profiles on MM9 monsters (one weak school)
    float casterStartingSpellPoints = 0.5f;   // casters are part-way through a dungeon
    float areaShare = 0.7f;     // share of a pack an area spell catches
    bool dump = false;          // print each group's party to stderr
    bool bolster = false;       // monsters below the party rise toward it (bolster_maps.txt rows), as in play
};

// The reference party (same in both worlds): class lines, the skills each spends its points on (main first), the
// slots it wears and whether it fights at range.
struct MemberPlan
{
    std::array<const char *, 3> classLine;
    std::vector<const char *> skills;
    const char *weaponSkill;
    bool shield;
    const char *armorSkill;
    bool ranged;
    const char *primaryStat;
};

const std::array<MemberPlan, 5> PartyPlan = {{
    {{"Knight", "Cavalier", "Champion"}, {"Sword", "Armsmaster", "PlateArmor", "Shield", "Bodybuilding"}, "Sword",
        true, "PlateArmor", false, "Might"},
    {{"Paladin", "Crusader", "Hero"}, {"Mace", "PlateArmor", "Shield", "SpiritMagic", "BodyMagic"}, "Mace", true,
        "PlateArmor", false, "Might"},
    {{"Archer", "WarriorMage", "MasterArcher"}, {"Bow", "FireMagic", "AirMagic", "ChainArmor", "Sword"}, "Bow", false,
        "ChainArmor", true, "Intellect"},
    {{"Cleric", "Priest", "PriestLight"}, {"SpiritMagic", "BodyMagic", "MindMagic", "Mace", "ChainArmor",
        "Meditation"}, "Mace", true, "ChainArmor", false, "Personality"},
    {{"Sorcerer", "Wizard", "ArchMage"}, {"FireMagic", "AirMagic", "WaterMagic", "EarthMagic", "Staff",
        "LeatherArmor", "Meditation"}, "Staff", false, "LeatherArmor", true, "Intellect"},
}};

const std::array<const char *, 9> AreaSpells = {
    "Fireball", "Meteor Shower", "Inferno", "Starburst", "Ring of Fire", "Death Blossom", "Prismatic Light",
    "Ice Blast", "Armageddon"};

std::string lower(std::string text)
{
    std::transform(text.begin(), text.end(), text.begin(), [](unsigned char c) { return char(std::tolower(c)); });
    return text;
}

bool isAreaSpell(const SpellEntry &spell)
{
    return std::any_of(AreaSpells.begin(), AreaSpells.end(),
        [&spell](const char *pName) { return lower(spell.name) == lower(pName); });
}

// Skill points a member has spent by `level`: 5 a level plus one more per ten levels (MM6-MM8), from a start of 10.
int skillPointsAtLevel(int level)
{
    int points = 10;

    for (int l = 1; l < level; ++l)
    {
        points += 5 + l / 10;
    }

    return points;
}

// The tier of an ordinary item: its random-treasure weights' strongest tier, else its normalised tier.
int itemTier(const ItemDefinition &item)
{
    int best = 0;
    int bestWeight = 0;

    for (size_t tier = 0; tier < item.randomTreasureWeights.size(); ++tier)
    {
        if (item.randomTreasureWeights[tier] > bestWeight)
        {
            bestWeight = item.randomTreasureWeights[tier];
            best = int(tier) + 1;
        }
    }

    return best > 0 ? best : int(item.normalizedTier);
}

float diceAverage(const std::string &dice)
{
    int rolls = 0;
    int sides = 0;
    char d = 0;
    std::istringstream stream(dice);

    if (stream >> rolls >> d >> sides && (d == 'd' || d == 'D'))
    {
        return rolls * (sides + 1) / 2.0f;
    }

    try
    {
        return std::stof(dice);
    }
    catch (...)
    {
        return 0.0f;
    }
}

float itemPower(const ItemDefinition &item)
{
    float mod2 = 0.0f;

    try
    {
        mod2 = item.mod2.empty() ? 0.0f : std::stof(item.mod2);
    }
    catch (...)
    {
    }

    return diceAverage(item.mod1) + mod2;
}

// The median ordinary item of a slot kind and skill at a tier, from one world's items.
const ItemDefinition *pickItem(
    const ItemTable &items,
    const std::vector<std::string> &equipStats,
    const std::string &skillGroup,
    int tier,
    bool mm9)
{
    for (int tryTier = tier; tryTier >= 1; --tryTier)
    {
        std::vector<const ItemDefinition *> candidates;

        for (const ItemDefinition &item : items.entries())
        {
            const bool fromMm9 = lower(item.packageId) == "mm9";

            if (fromMm9 != mm9 || item.rarity != ItemRarity::Common || itemTier(item) != tryTier)
            {
                continue;
            }

            if (std::find(equipStats.begin(), equipStats.end(), item.equipStat) == equipStats.end())
            {
                continue;
            }

            if (!skillGroup.empty() && lower(item.skillGroup) != lower(skillGroup))
            {
                continue;
            }

            candidates.push_back(&item);
        }

        if (!candidates.empty())
        {
            std::sort(candidates.begin(), candidates.end(),
                [](const ItemDefinition *pA, const ItemDefinition *pB) { return itemPower(*pA) < itemPower(*pB); });
            return candidates[candidates.size() / 2];
        }
    }

    return nullptr;
}

std::string armorSkillGroup(const std::string &skill)
{
    if (skill == "PlateArmor")
    {
        return "Plate";
    }

    if (skill == "ChainArmor")
    {
        return "Chain";
    }

    return "Leather";
}

Character buildMember(const MemberPlan &plan, int level, const GameDataLoader &data, const GameRules &rules)
{
    Character member = {};
    const int classStage = level >= 40 ? 2 : level >= 20 ? 1 : 0;
    member.className = plan.classLine[classStage];
    member.name = member.className;
    member.role = member.className;
    member.level = uint32_t(level);
    member.experience = level > 1 ? rules.experience.experienceForNextLevel(uint32_t(level - 1)) : 0;

    // Stats: 15 at the start, the primary and Endurance growing with potions, fountains and items (the same in both
    // worlds).
    const uint32_t primary = uint32_t(18 + level * 0.8);
    const uint32_t secondary = uint32_t(14 + level * 0.4);
    member.might = secondary;
    member.intellect = secondary;
    member.personality = secondary;
    member.endurance = uint32_t(16 + level * 0.6);
    member.accuracy = secondary;
    member.speed = secondary;
    member.luck = secondary;

    if (std::string(plan.primaryStat) == "Might")
    {
        member.might = primary;
        member.accuracy = uint32_t(16 + level * 0.6);
    }
    else if (std::string(plan.primaryStat) == "Intellect")
    {
        member.intellect = primary;
    }
    else
    {
        member.personality = primary;
    }

    // Skill ranks: spend the level's points on the plan's skills, the first two at twice the weight of the rest,
    // raising whichever is furthest behind its share.
    std::map<std::string, int> ranks;
    int points = skillPointsAtLevel(level);

    for (const char *pSkill : plan.skills)
    {
        ranks[pSkill] = 1;
    }

    while (true)
    {
        const char *pNext = nullptr;
        float bestShare = 1e9f;

        for (size_t index = 0; index < plan.skills.size(); ++index)
        {
            const float weight = index < 2 ? 2.0f : 1.0f;
            const float share = ranks[plan.skills[index]] / weight;
            const int cost = ranks[plan.skills[index]] + 1;

            if (cost <= points && share < bestShare)
            {
                bestShare = share;
                pNext = plan.skills[index];
            }
        }

        if (pNext == nullptr)
        {
            break;
        }

        points -= ranks[pNext] + 1;
        ++ranks[pNext];
    }

    const ClassSkillTable &classSkills = data.getClassSkillTable();
    constexpr std::array<SkillMastery, 4> Masteries = {
        SkillMastery::Normal, SkillMastery::Expert, SkillMastery::Master, SkillMastery::Grandmaster};

    for (const auto &[skill, rank] : ranks)
    {
        const SkillMastery cap = classSkills.getEffectiveCap(member.className, member.raceId, skill);

        if (cap == SkillMastery::None)
        {
            continue;
        }

        SkillMastery mastery = SkillMastery::Normal;

        for (SkillMastery candidate : Masteries)
        {
            if (candidate <= cap && uint32_t(rank) >= rules.skills.masteryRequiredLevel(skill, candidate))
            {
                mastery = candidate;
            }
        }

        member.skills[skill] = {skill, uint32_t(rank), mastery};
    }

    for (const SpellEntry &spell : data.getSpellTable().entries())
    {
        const std::optional<std::string> school =
            spell.id > 0 ? resolveMagicSkillName(uint32_t(spell.id)) : std::nullopt;
        const CharacterSkill *pSkill = school ? member.findSkill(*school) : nullptr;

        if (pSkill != nullptr && pSkill->mastery != SkillMastery::None && pSkill->mastery >= spell.requiredMastery)
        {
            member.learnSpell(uint32_t(spell.id));
        }
    }

    GameMechanics::refreshCharacterBaseResources(member, true, &data.getClassMultiplierTable());
    return member;
}

Party buildParty(int level, int tier, bool mm9Items, const GameDataLoader &data)
{
    Party party = {};
    party.setItemTable(&data.getItemTable());
    party.setCharacterDollTable(&data.getCharacterDollTable());
    party.setItemEnchantTables(&data.getStandardItemEnchantTable(), &data.getSpecialItemEnchantTable());
    party.setClassMultiplierTable(&data.getClassMultiplierTable());
    party.setClassSkillTable(&data.getClassSkillTable());
    PartySeed seed = {};

    for (const MemberPlan &plan : PartyPlan)
    {
        seed.members.push_back(buildMember(plan, level, data, party.rules()));
    }

    party.seed(seed);
    const ItemTable &items = data.getItemTable();

    for (size_t index = 0; index < PartyPlan.size(); ++index)
    {
        const MemberPlan &plan = PartyPlan[index];
        std::vector<std::pair<EquipmentSlot, const ItemDefinition *>> gear;
        const std::string weapon = plan.weaponSkill;

        if (weapon == "Bow")
        {
            gear.push_back({EquipmentSlot::Bow, pickItem(items, {"Missile"}, "Bow", tier, mm9Items)});
            gear.push_back({EquipmentSlot::MainHand, pickItem(items, {"Weapon"}, "Sword", tier, mm9Items)});
        }
        else if (weapon == "Staff")
        {
            gear.push_back({EquipmentSlot::MainHand, pickItem(items, {"Weapon2"}, "Staff", tier, mm9Items)});
        }
        else
        {
            gear.push_back({EquipmentSlot::MainHand, pickItem(items, {"Weapon", "Weapon1or2"}, weapon, tier,
                mm9Items)});
        }

        if (plan.shield)
        {
            gear.push_back({EquipmentSlot::OffHand, pickItem(items, {"Shield"}, "Shield", tier, mm9Items)});
        }

        gear.push_back({EquipmentSlot::Armor, pickItem(items, {"Armor"}, armorSkillGroup(plan.armorSkill), tier,
            mm9Items)});
        gear.push_back({EquipmentSlot::Helm, pickItem(items, {"Helm"}, "", tier, mm9Items)});
        gear.push_back({EquipmentSlot::Boots, pickItem(items, {"Boots"}, "", tier, mm9Items)});
        gear.push_back({EquipmentSlot::Gauntlets, pickItem(items, {"Gauntlets"}, "", tier, mm9Items)});

        for (const auto &[slot, pItem] : gear)
        {
            if (pItem == nullptr)
            {
                continue;
            }

            InventoryItem item = {};
            item.objectDescriptionId = pItem->itemId;
            item.identified = true;
            std::optional<InventoryItem> held;
            party.tryEquipItemOnMember(index, slot, item, std::nullopt, false, held);
        }
    }

    return party;
}

// A monster in a fight: its stats as the world plays them.
struct FightMonster
{
    const MonsterTable::MonsterStatsEntry *pStats = nullptr;
    int hp = 0;
    int maxHp = 0;
    float nextAction = 0.0f;
    float recoverySeconds = 1.0f;
    float damageScale = 1.0f;
    int spell1Use = 0;
    int spell2Use = 0;
    uint32_t spell1Skill = 0;
    uint32_t spell2Skill = 0;
    std::array<int, 7> schools = {};   // fire air water earth mind spirit body
    int physical = 0;
    int armorClass = 0;
    MonsterTable::MonsterStatsEntry::DamageProfile attack1 = {};
    MonsterTable::MonsterStatsEntry::DamageProfile attack2 = {};
    bool lowersPartyArmorClass = false;   // a bolstered monster meets the party's AC scaled by its level
};

int monsterSchoolResistance(const FightMonster &monster, CombatDamageType type)
{
    switch (type)
    {
        case CombatDamageType::Fire: return monster.schools[0];
        case CombatDamageType::Air: return monster.schools[1];
        case CombatDamageType::Water: return monster.schools[2];
        case CombatDamageType::Earth: return monster.schools[3];
        case CombatDamageType::Mind: return monster.schools[4];
        case CombatDamageType::Spirit: return monster.schools[5];
        case CombatDamageType::Body: return monster.schools[6];
        case CombatDamageType::Physical: return monster.physical;
        default: return 0;
    }
}

float expectedResistMultiplier(int resistance)
{
    if (resistance >= 200)
    {
        return 0.0f;
    }

    const float p = 30.0f / (std::max(0, resistance) + 30.0f);
    float multiplier = 0.0f;

    for (int k = 0; k < 4; ++k)
    {
        multiplier += p * std::pow(1.0f - p, float(k)) / std::pow(2.0f, float(k));
    }

    return multiplier + std::pow(1.0f - p, 4.0f) / 16.0f;
}

// A spread of several projectiles (Sparks, Poison Spray, Shrapmetal) mostly misses a single target: the first hits,
// about a third of the rest do.
float projectileHitsOnOneTarget(uint32_t projectiles)
{
    return 1.0f + 0.3f * float(std::max<uint32_t>(1, projectiles) - 1);
}

bool isConditionSpell(const std::string &name)
{
    const std::string n = lower(name);
    return n.find("fear") != std::string::npos || n.find("paralyze") != std::string::npos
        || n.find("slow") != std::string::npos || n.find("charm") != std::string::npos
        || n.find("turn undead") != std::string::npos;
}

// MM9's monster table as BALANCE_PLAN.md 3.2 plays it.
FightMonster makeMonster(const MonsterTable::MonsterStatsEntry &stats, bool mm9, const Options &options,
    const std::map<int, uint32_t> &mm7SpellSkillCap, const GameplayBolsterRuntimeContext *pBolster)
{
    FightMonster monster = {};
    monster.pStats = &stats;
    monster.maxHp = stats.hitPoints;
    monster.armorClass = stats.armorClass;
    monster.attack1 = stats.attack1Damage;
    monster.attack2 = stats.attack2Damage;
    monster.recoverySeconds = std::max(0.3f, stats.recovery / 60.0f);
    monster.spell1Use = stats.hasSpell1 ? stats.spell1UseChance : 0;
    monster.spell2Use = stats.hasSpell2 ? stats.spell2UseChance : 0;
    monster.spell1Skill = stats.spell1SkillLevel;
    monster.spell2Skill = stats.spell2SkillLevel;
    monster.schools = {stats.fireResistance, stats.airResistance, stats.waterResistance, stats.earthResistance,
        stats.mindResistance, stats.spiritResistance, stats.bodyResistance};
    monster.physical = stats.physicalResistance;

    if (mm9 && options.mm9Changes)
    {
        const int level = stats.level;
        monster.maxHp = int(stats.hitPoints * (level > 60 ? 0.90f : level >= 41 ? 0.95f : 1.0f));
        monster.recoverySeconds = level <= 20 ? std::max(monster.recoverySeconds, 75 / 60.0f) : monster.recoverySeconds;
        monster.damageScale = level <= 5 ? 0.75f : 1.0f;
        const auto scaledUse = [](int use, const std::string &name)
        {
            return std::min(int(std::lround(use * 0.4f)), isConditionSpell(name) ? 25 : 40);
        };
        monster.spell1Use = scaledUse(monster.spell1Use, stats.spell1Name);
        monster.spell2Use = scaledUse(monster.spell2Use, stats.spell2Name);
        const int band = std::min(level / 10, 12);
        const auto cap = mm7SpellSkillCap.find(band);

        if (cap != mm7SpellSkillCap.end())
        {
            monster.spell1Skill = std::min(monster.spell1Skill, cap->second);
            monster.spell2Skill = std::min(monster.spell2Skill, cap->second);
        }
    }

    if (mm9 && options.profiles)
    {
        int *pWeakest = &*std::min_element(monster.schools.begin(), monster.schools.end());
        *pWeakest /= 4;
    }

    if (pBolster != nullptr)
    {
        const GameplayMonsterBolsterResult bolster = resolveGameplayMonsterBolster(*pBolster, stats, nullptr);

        if (bolster.statsEnabled)
        {
            monster.maxHp = int(monster.maxHp * float(bolster.maxHp) / float(std::max(1, stats.hitPoints)));
            monster.armorClass = bolster.armorClass;
            monster.attack1 = {bolster.attack1DamageDiceRolls, bolster.attack1DamageDiceSides, bolster.attack1DamageBonus};
            monster.attack2 = {bolster.attack2DamageDiceRolls, bolster.attack2DamageDiceSides, bolster.attack2DamageBonus};
            monster.spell1Skill = std::max(monster.spell1Skill, bolster.spell1SkillLevel);
            monster.spell2Skill = std::max(monster.spell2Skill, bolster.spell2SkillLevel);
            monster.lowersPartyArmorClass = true;
        }
    }

    monster.hp = monster.maxHp;
    return monster;
}

struct FightResult
{
    float seconds = 0.0f;
    float damageTaken = 0.0f;
    int deaths = 0;
    bool won = false;
};

struct CasterSpell
{
    const SpellEntry *pSpell = nullptr;
    SkillMastery mastery = SkillMastery::None;
    uint32_t skillLevel = 0;
    int manaCost = 0;
    float recoverySeconds = 1.0f;
    float averageDamage = 0.0f;
    CombatDamageType type = CombatDamageType::Fire;
    bool area = false;
};

std::vector<CasterSpell> casterSpells(const Character &member, const GameDataLoader &data)
{
    std::vector<CasterSpell> spells;

    for (const SpellEntry &spell : data.getSpellTable().entries())
    {
        if (spell.id <= 0 || !member.knowsSpell(uint32_t(spell.id)) || (spell.damageBase <= 0 && spell.damageDiceSides <= 0))
        {
            continue;
        }

        const std::optional<std::string> school = resolveMagicSkillName(uint32_t(spell.id));
        const CharacterSkill *pSkill = school ? member.findSkill(*school) : nullptr;

        if (pSkill == nullptr)
        {
            continue;
        }

        CasterSpell cast = {};
        cast.pSpell = &spell;
        cast.mastery = pSkill->mastery;
        cast.skillLevel = pSkill->level;
        const SpellMasteryNumbers numbers = spellNumbersAtMastery(spell, pSkill->mastery);
        cast.manaCost = numbers.manaCost;
        cast.recoverySeconds = std::max(0.3f, ticksToRecoverySeconds(numbers.recoveryTicks));
        cast.averageDamage = (numbers.damageBase + (numbers.damageDiceMin + numbers.damageDiceMax) / 2.0f
            * pSkill->level) * projectileHitsOnOneTarget(numbers.projectileCount);
        cast.type = GameMechanics::parseCombatDamageType(spell.schoolName);
        cast.area = isAreaSpell(spell);
        spells.push_back(cast);
    }

    return spells;
}

FightResult fight(
    Party &party,
    std::vector<FightMonster> monsters,
    const GameDataLoader &data,
    const Options &options,
    std::mt19937 &rng)
{
    const ItemTable *pItems = &data.getItemTable();
    const SpellTable *pSpells = &data.getSpellTable();
    const GameRules &rules = party.rules();
    const size_t count = party.memberCount();
    std::vector<int> hp(count);
    std::vector<int> sp(count);
    std::vector<int> armorClass(count);
    std::vector<float> nextAction(count, 0.0f);
    std::vector<std::vector<CasterSpell>> spells(count);

    for (size_t index = 0; index < count; ++index)
    {
        const Character &member = *party.member(index);
        const CharacterSheetSummary summary = GameMechanics::buildCharacterSheetSummary(
            member, pItems, &data.getStandardItemEnchantTable(), &data.getSpecialItemEnchantTable());
        hp[index] = summary.health.maximum;
        sp[index] = int(summary.spellPoints.maximum * options.casterStartingSpellPoints);
        armorClass[index] = summary.armorClass.actual;
        spells[index] = casterSpells(member, data);
        nextAction[index] = std::uniform_real_distribution<float>(0.0f, 0.5f)(rng);
    }

    for (FightMonster &monster : monsters)
    {
        monster.nextAction = std::uniform_real_distribution<float>(0.0f, monster.recoverySeconds)(rng);
    }

    FightResult result = {};
    float now = 0.0f;
    const auto alive = [&monsters]() { return std::count_if(monsters.begin(), monsters.end(),
        [](const FightMonster &m) { return m.hp > 0; }); };

    while (now < 600.0f)
    {
        if (alive() == 0)
        {
            result.won = true;
            break;
        }

        if (std::none_of(hp.begin(), hp.end(), [](int h) { return h > 0; }))
        {
            break;
        }

        // The next actor: the earliest party member or monster.
        float next = 1e9f;
        int memberTurn = -1;
        int monsterTurn = -1;

        for (size_t index = 0; index < count; ++index)
        {
            if (hp[index] > 0 && nextAction[index] < next)
            {
                next = nextAction[index];
                memberTurn = int(index);
                monsterTurn = -1;
            }
        }

        for (size_t index = 0; index < monsters.size(); ++index)
        {
            if (monsters[index].hp > 0 && monsters[index].nextAction < next)
            {
                next = monsters[index].nextAction;
                monsterTurn = int(index);
                memberTurn = -1;
            }
        }

        now = next;

        if (memberTurn >= 0)
        {
            const size_t index = size_t(memberTurn);
            const Character &member = *party.member(index);
            // Focus fire on the first living monster.
            FightMonster *pTarget = nullptr;

            for (FightMonster &monster : monsters)
            {
                if (monster.hp > 0)
                {
                    pTarget = &monster;
                    break;
                }
            }

            // A caster takes the affordable spell with the best expected damage per second on this pack.
            const CasterSpell *pBest = nullptr;
            float bestRate = 0.0f;
            const int living = int(alive());

            for (const CasterSpell &cast : spells[index])
            {
                if (cast.manaCost > sp[index])
                {
                    continue;
                }

                const float targets = cast.area ? std::max(1.0f, living * options.areaShare) : 1.0f;
                const float rate = cast.averageDamage * targets
                    * expectedResistMultiplier(monsterSchoolResistance(*pTarget, cast.type)) / cast.recoverySeconds;

                if (rate > bestRate)
                {
                    bestRate = rate;
                    pBest = &cast;
                }
            }

            const bool ranged = PartyPlan[index].ranged;
            const CharacterAttackResult attack = GameMechanics::resolveCharacterAttackAgainstArmorClass(
                member, pItems, pSpells, pTarget->armorClass, ranged ? 1500.0f : 100.0f, rng);
            const CharacterAttackProfile profile = GameMechanics::buildCharacterAttackProfile(member, pItems, pSpells);
            const bool shoots = ranged && profile.canShoot;
            const float weaponRate = shoots
                ? 0.5f * (profile.rangedMinDamage + profile.rangedMaxDamage) * profile.rangedProjectileCount
                    / std::max(0.3f, profile.rangedRecoverySeconds)
                : 0.5f * (profile.meleeMinDamage + profile.meleeMaxDamage) / std::max(0.3f, profile.meleeRecoverySeconds);

            if (pBest != nullptr && bestRate > weaponRate)
            {
                CharacterSpellCast cast = {};
                cast.pCaster = &member;
                cast.pItemTable = pItems;
                cast.pSpell = pBest->pSpell;
                cast.mastery = pBest->mastery;
                cast.skillLevel = pBest->skillLevel;
                sp[index] -= pBest->manaCost;

                for (FightMonster &monster : monsters)
                {
                    const bool struck = &monster == pTarget
                        || (pBest->area && monster.hp > 0
                            && std::uniform_real_distribution<float>(0.0f, 1.0f)(rng) < options.areaShare);

                    if (!struck || monster.hp <= 0)
                    {
                        continue;
                    }

                    const float hits = projectileHitsOnOneTarget(
                        spellNumbersAtMastery(*pBest->pSpell, pBest->mastery).projectileCount);
                    const int projectiles = int(hits) + (std::uniform_real_distribution<float>(0.0f, 1.0f)(rng)
                        < hits - std::floor(hits) ? 1 : 0);

                    for (int shot = 0; shot < projectiles; ++shot)
                    {
                        monster.hp -= GameMechanics::resolveMonsterIncomingDamage(rules.combat.rollSpellDamage(cast),
                            pBest->type, monsterSchoolResistance(monster, pBest->type), 0, rng);
                    }
                }

                nextAction[index] = now + pBest->recoverySeconds;
            }
            else
            {
                if (attack.canAttack && attack.hit)
                {
                    for (int shot = 0; shot < std::max<int>(1, attack.projectileCount); ++shot)
                    {
                        const int damage = shot == 0 ? attack.damage
                            : std::uniform_int_distribution<int>(attack.minimumDamage,
                                std::max(attack.minimumDamage, attack.maximumDamage))(rng);
                        pTarget->hp -= GameMechanics::resolveMonsterIncomingDamage(damage, attack.damageType,
                            monsterSchoolResistance(*pTarget, attack.damageType), 0, rng);
                    }
                }

                nextAction[index] = now + std::max(0.3f, attack.recoverySeconds > 0.0f ? attack.recoverySeconds : 1.0f);
            }

            continue;
        }

        // A monster acts: a spell by its use chance, else attack 2 by its chance, else attack 1, at a random living
        // member.
        FightMonster &monster = monsters[size_t(monsterTurn)];
        const MonsterTable::MonsterStatsEntry &stats = *monster.pStats;
        std::vector<size_t> targets;

        for (size_t index = 0; index < count; ++index)
        {
            if (hp[index] > 0)
            {
                targets.push_back(index);
            }
        }

        const size_t target = targets[std::uniform_int_distribution<size_t>(0, targets.size() - 1)(rng)];
        const Character &victim = *party.member(target);
        const int roll = std::uniform_int_distribution<int>(0, 99)(rng);
        int damage = 0;
        CombatDamageType type = CombatDamageType::Physical;
        const auto spellHit = [&](const std::string &name, uint32_t skill, SkillMastery mastery)
        {
            const SpellEntry *pSpell = data.getSpellTable().findByName(name);

            if (pSpell == nullptr || isConditionSpell(name))
            {
                return 0;
            }

            type = GameMechanics::parseCombatDamageType(pSpell->schoolName);
            int value = pSpell->damageBase;

            for (uint32_t r = 0; r < skill; ++r)
            {
                value += std::uniform_int_distribution<int>(1, std::max(1, pSpell->damageDiceSides))(rng);
            }

            (void)mastery;
            return value;
        };

        if (roll < monster.spell1Use)
        {
            damage = spellHit(stats.spell1Name, monster.spell1Skill, stats.spell1SkillMastery);
        }
        else if (roll < monster.spell1Use + monster.spell2Use)
        {
            damage = spellHit(stats.spell2Name, monster.spell2Skill, stats.spell2SkillMastery);
        }
        else
        {
            const bool second = std::uniform_int_distribution<int>(0, 99)(rng) < stats.attack2Chance;
            const auto &profile = second ? monster.attack2 : monster.attack1;
            type = GameMechanics::parseCombatDamageType(second ? stats.attack2Type : stats.attack1Type);

            const int victimArmorClass = gameplayBolsterPlayerArmorClass(armorClass[target], stats.level,
                int(std::max<uint32_t>(1, victim.level)), monster.lowersPartyArmorClass);

            if (GameMechanics::monsterAttackHitsArmorClass(victimArmorClass, stats.level, 0, rng))
            {
                damage = GameMechanics::rollMonsterAttackDamage(profile.diceRolls, profile.diceSides, profile.bonus,
                    rng);
                damage = int(std::lround(damage * monster.damageScale));
            }
        }

        if (damage > 0)
        {
            damage = GameMechanics::resolveCharacterIncomingDamage(victim, pItems, &data.getStandardItemEnchantTable(),
                &data.getSpecialItemEnchantTable(), damage, type, rng);
            const int dealt = std::min(damage, std::max(0, hp[target]));
            result.damageTaken += float(dealt);
            hp[target] -= damage;

            if (hp[target] <= 0)
            {
                ++result.deaths;
            }
        }

        monster.nextAction = now + monster.recoverySeconds;
    }

    result.seconds = now;
    return result;
}

void dumpParty(const Party &party, const GameDataLoader &data)
{
    for (size_t index = 0; index < party.memberCount(); ++index)
    {
        const Character &member = *party.member(index);
        const CharacterSheetSummary summary = GameMechanics::buildCharacterSheetSummary(member, &data.getItemTable(),
            &data.getStandardItemEnchantTable(), &data.getSpecialItemEnchantTable());
        const CharacterAttackProfile profile =
            GameMechanics::buildCharacterAttackProfile(member, &data.getItemTable(), &data.getSpellTable());
        std::cerr << "  " << member.className << " L" << member.level << ": HP " << summary.health.maximum << " SP "
                  << summary.spellPoints.maximum << " AC " << summary.armorClass.actual << " | melee "
                  << profile.meleeMinDamage << "-" << profile.meleeMaxDamage << " +" << profile.meleeAttackBonus << " /"
                  << profile.meleeRecoverySeconds << "s | ranged " << (profile.canShoot
                  ? std::to_string(profile.rangedMinDamage) + "-" + std::to_string(profile.rangedMaxDamage) + " x"
                  + std::to_string(profile.rangedProjectileCount) + " /" + std::to_string(profile.rangedRecoverySeconds)
                  + "s" : std::string("-")) << "\n    skills:";

        for (const auto &[name, skill] : member.skills)
        {
            std::cerr << ' ' << name << ' ' << skill.level << "/" << int(skill.mastery);
        }

        std::cerr << "\n    gear:";

        for (int slot = 0; slot <= int(EquipmentSlot::Boots); ++slot)
        {
            if (const std::optional<InventoryItem> item = party.equippedItem(index, EquipmentSlot(slot)))
            {
                const ItemDefinition *pItem = data.getItemTable().get(item->objectDescriptionId);
                std::cerr << ' ' << (pItem ? pItem->name + " (" + pItem->mod1 + "+" + pItem->mod2 + ")" : "?") << ';';
            }
        }

        const std::vector<CasterSpell> spells = casterSpells(member, data);
        std::cerr << "\n    damage spells:";

        for (const CasterSpell &cast : spells)
        {
            std::cerr << ' ' << cast.pSpell->name << " " << cast.averageDamage << "/" << cast.recoverySeconds << "s "
                      << cast.manaCost << "sp" << (cast.area ? " area" : "") << ';';
        }

        std::cerr << '\n';
    }
}

int partyMaxHealth(const Party &party, const GameDataLoader &data)
{
    int total = 0;

    for (size_t index = 0; index < party.memberCount(); ++index)
    {
        total += GameMechanics::buildCharacterSheetSummary(*party.member(index), &data.getItemTable(),
            &data.getStandardItemEnchantTable(), &data.getSpecialItemEnchantTable()).health.maximum;
    }

    return total;
}
}

int main(int argc, char **argv)
{
    if (argc < 3)
    {
        std::cerr << "usage: openyamm_balance_probe <input.tsv> <output.tsv> [--runs N] [--mm9-items] "
                     "[--no-mm9-changes] [--no-profiles]\n";
        return 2;
    }

    Options options = {};

    for (int index = 3; index < argc; ++index)
    {
        const std::string argument = argv[index];

        if (argument == "--runs" && index + 1 < argc)
        {
            options.runs = std::stoi(argv[++index]);
        }
        else if (argument == "--mm9-items")
        {
            options.mm9Items = true;
        }
        else if (argument == "--no-mm9-changes")
        {
            options.mm9Changes = false;
        }
        else if (argument == "--no-profiles")
        {
            options.profiles = false;
        }
        else if (argument == "--dump")
        {
            options.dump = true;
        }
        else if (argument == "--bolster")
        {
            options.bolster = true;
        }
        else if (argument == "--area" && index + 1 < argc)
        {
            options.areaShare = std::stof(argv[++index]);
        }
        else if (argument == "--sp" && index + 1 < argc)
        {
            options.casterStartingSpellPoints = std::stof(argv[++index]);
        }
    }

    Engine::AssetFileSystem assets;
    const std::filesystem::path root = std::filesystem::current_path();

    if (!assets.initialize(root, root / "assets_dev", Engine::AssetScaleTier::X1, "mm9"))
    {
        std::cerr << "cannot mount assets_dev with the mm9 world\n";
        return 1;
    }

    GameDataLoader data = {};

    if (!data.loadForHeadlessGameplay(assets))
    {
        std::cerr << "cannot load the game data\n";
        return 1;
    }

    std::map<std::pair<std::string, int>, std::vector<GroupRow>> groups;
    std::ifstream input(argv[1]);
    std::string line;

    while (std::getline(input, line))
    {
        if (line.empty() || line[0] == '#')
        {
            continue;
        }

        std::istringstream fields(line);
        GroupRow row = {};

        if (fields >> row.world >> row.stage >> row.partyLevel >> row.shopTier >> row.packSize >> row.monsterId
            >> row.weight)
        {
            groups[{row.world, row.stage}].push_back(row);
        }
    }

    // MM7's highest monster spell skill per ten levels: the cap BALANCE_PLAN.md 3.2 puts on MM9's.
    std::map<int, uint32_t> mm7SpellSkillCap;

    for (const auto &[id, stats] : data.getMonsterTable().statsEntries())
    {
        if (id < 9000 && stats.level > 0)
        {
            uint32_t &cap = mm7SpellSkillCap[std::min(stats.level / 10, 12)];
            cap = std::max({cap, stats.spell1SkillLevel, stats.spell2SkillLevel});
        }
    }

    std::ofstream output(argv[2]);
    output << "world\tstage\tparty_level\tshop_tier\tpack\tparty_hp\tclear_seconds\tdamage_share\tdeaths\twins\n";
    std::mt19937 rng(20261106u);

    for (const auto &[key, rows] : groups)
    {
        const GroupRow &first = rows.front();
        const bool mm9 = key.first == "mm9";
        Party party = buildParty(first.partyLevel, first.shopTier, mm9 && options.mm9Items, data);
        const int partyHp = partyMaxHealth(party, data);

        if (options.dump)
        {
            std::cerr << key.first << " stage " << key.second << ":\n";
            dumpParty(party, data);
        }
        std::vector<float> weights;

        for (const GroupRow &row : rows)
        {
            weights.push_back(row.weight);
        }

        std::discrete_distribution<size_t> pickRow(weights.begin(), weights.end());
        // Bolster as play has it: a map of the world with a LowerToEqual row (MM9: Sturmford's; MM7: its first).
        const MapStatsEntry *pBolsterMap = nullptr;

        for (const MapStatsEntry &map : data.getMapStats().getEntries())
        {
            const MergedBolsterMapEntry *pRow = data.getMergedBolsterMapTable().findById(uint32_t(map.id));

            if (pRow != nullptr && lower(map.worldId) == key.first && lower(pRow->bolsterKind) == "lowertoequal")
            {
                pBolsterMap = &map;
                break;
            }
        }

        GameplayBolsterRuntimeContext bolsterContext = {};
        bolsterContext.pMap = pBolsterMap;
        bolsterContext.pMonsterTable = &data.getMonsterTable();
        bolsterContext.pBolsterMapTable = &data.getMergedBolsterMapTable();
        bolsterContext.pBolsterMonsterTable = &data.getMergedBolsterMonsterTable();
        bolsterContext.pParty = &party;
        bolsterContext.bolsterMonstersEnabled = true;

        if (options.bolster && pBolsterMap == nullptr)
        {
            std::cerr << key.first << ": no map with a LowerToEqual bolster row\n";
        }
        double seconds = 0.0;
        double damage = 0.0;
        double deaths = 0.0;
        double wins = 0.0;
        double packs = 0.0;
        int fights = 0;

        for (int run = 0; run < options.runs; ++run)
        {
            const GroupRow &row = rows[pickRow(rng)];
            const MonsterTable::MonsterStatsEntry *pStats = data.getMonsterTable().findStatsById(int16_t(row.monsterId));

            if (pStats == nullptr)
            {
                continue;
            }

            // One family per pack, its size around the group's mean.
            const int base = int(std::floor(row.packSize));
            const int size = std::max(1, base + (std::uniform_real_distribution<float>(0.0f, 1.0f)(rng)
                < row.packSize - base ? 1 : 0));
            std::vector<FightMonster> pack;

            for (int m = 0; m < size; ++m)
            {
                pack.push_back(makeMonster(*pStats, mm9, options, mm7SpellSkillCap,
                    options.bolster && pBolsterMap != nullptr ? &bolsterContext : nullptr));
            }

            const FightResult result = fight(party, pack, data, options, rng);
            seconds += result.seconds;
            damage += result.damageTaken / std::max(1, partyHp);
            deaths += result.deaths;
            wins += result.won ? 1.0 : 0.0;
            packs += size;
            ++fights;
        }

        const double n = std::max(1, fights);
        output << key.first << '\t' << key.second << '\t' << first.partyLevel << '\t' << first.shopTier << '\t'
               << packs / n << '\t' << partyHp << '\t' << seconds / n << '\t' << damage / n << '\t' << deaths / n
               << '\t' << wins / n << '\n';
        std::cerr << key.first << " stage " << key.second << ": party level " << first.partyLevel << ", "
                  << fights << " fights\n";
    }

    return 0;
}
