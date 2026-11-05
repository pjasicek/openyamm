#include "game/rules/maw/MawItemRules.h"

#include "game/items/InventoryBags.h"
#include "game/items/InventoryItemMixingRuntime.h"
#include "game/items/ItemEnchantRuntime.h"
#include "game/items/ItemEnchantTables.h"
#include "game/items/ItemGenerator.h"
#include "game/items/ItemRuntime.h"
#include "game/party/Party.h"
#include "game/party/SkillData.h"
#include "game/rules/maw/MawAuras.h"
#include "game/rules/maw/MawBalanceModel.h"
#include "game/rules/maw/MawClassRules.h"
#include "game/rules/maw/MawCombatFormulas.h"
#include "game/rules/maw/MawCombatRules.h"
#include "game/rules/maw/MawPotionRules.h"
#include "game/rules/maw/MawRules.h"
#include "game/rules/maw/MawTexts.h"
#include "game/rules/RandomStreams.h"
#include "game/tables/PotionEffectTable.h"
#include "game/tables/HouseTable.h"
#include "game/tables/ItemTable.h"
#include "game/tables/MapStats.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdlib>
#include <limits>
#include <iomanip>
#include <sstream>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t PotionBottleItemId = 220;
constexpr int FirstSkillEnchant = 17;
constexpr int LastSkillEnchant = 24;
constexpr int ArmsmasterEnchant = 22;
constexpr int DodgeEnchant = 23;
constexpr int UnarmedEnchant = 24;
constexpr int HitPointsEnchant = 8;
constexpr int SpellPointsEnchant = 9;
constexpr int FirstResistanceEnchant = 11;
constexpr int LastResistanceEnchant = 16;
constexpr double ArtifactChance = 0.005;
constexpr double ShopLevelShare = 0.75;
constexpr double SellShare = 0.4;
constexpr int CelestialLevelCap = 600;
constexpr int MadnessCelestialLevelCap = 1000;

// The specials MAW swaps between a melee and a caster flavour (zzMaw-Items.lua:1267-1295).
constexpr uint16_t AscensionSpecial = 39;
constexpr uint16_t LichSpecial = 40;
constexpr uint16_t DarknessSpecial = 41;
constexpr uint16_t DragonSpecial = 46;

enum class LegendaryAffix : uint16_t
{
    EnchantEcho = 12,
    ResistanceEnchants = 16,
    EnchantDamage = 19,
    Ascension = 25,
    MeleeSkills = 33,
};

bool isSkillEnchant(int type)
{
    return type >= FirstSkillEnchant && type <= LastSkillEnchant;
}

bool isResistanceEnchant(int type)
{
    return type >= FirstResistanceEnchant && type <= LastResistanceEnchant;
}

int &resistanceField(CharacterResistanceSet &resistances, int type)
{
    switch (StandardItemEnchantKind(type))
    {
        case StandardItemEnchantKind::AirResistance:
            return resistances.air;
        case StandardItemEnchantKind::WaterResistance:
            return resistances.water;
        case StandardItemEnchantKind::EarthResistance:
            return resistances.earth;
        case StandardItemEnchantKind::MindResistance:
            return resistances.mind;
        case StandardItemEnchantKind::BodyResistance:
            return resistances.body;
        default:
            return resistances.fire;
    }
}

bool isWeapon(const ItemDefinition &itemDefinition)
{
    return itemDefinition.equipStat == "Weapon" || itemDefinition.equipStat == "Weapon2"
        || itemDefinition.equipStat == "Weapon1or2" || itemDefinition.equipStat == "Missile";
}

bool isTwoHanded(const ItemDefinition &itemDefinition)
{
    return itemDefinition.equipStat == "Weapon2";
}

// Hats and crowns read their enchantments 1.5 times stronger: MAW counts every helm without a flat armour bonus (Mod2),
// the Horned Helm's one die of armour included (IT:2728, 4421).
bool isHat(const ItemDefinition &itemDefinition, const MawBaseItem &)
{
    return itemDefinition.equipStat == "Helm" && std::atoi(itemDefinition.mod2.c_str()) == 0;
}

double readSlotMultiplier(const ItemDefinition &itemDefinition, const MawBaseItem &base)
{
    return mawEnchantSlotMultiplier(itemDefinition, base) * (isHat(itemDefinition, base) ? 1.5 : 1);
}

// A worn item's enchantment as MAW reads it (collectEnchant, IT:2722-2750): hit and spell points first grow with their
// power by the slot, then a hat reads it 1.5 times stronger (rounded up), then a resistance gains 10 as the first
// enchantment and is halved on a ring.
int readEnchantment(int type, int power, bool first, const ItemDefinition &itemDefinition, const MawBaseItem &base,
    bool ring)
{
    const double multiplier = readSlotMultiplier(itemDefinition, base);
    const bool vitality = type == HitPointsEnchant || type == SpellPointsEnchant;
    double value = vitality ? mawEnchantReadPower(type, power, first, multiplier, ring) : power;
    value = isHat(itemDefinition, base) ? std::ceil(value * 1.5) : value;
    return vitality ? int(value) : mawEnchantReadPower(type, int(value), first, multiplier, ring);
}

int uniform(std::mt19937 &rng, int low, int high)
{
    return std::uniform_int_distribution<int>(low, high)(rng);
}

double unitDraw(std::mt19937 &rng)
{
    return std::uniform_real_distribution<double>(0.0, 1.0)(rng);
}

// The base enchantment type (RollEnchantType): rings 1-16 (with the resistances), everything else 1-10.
int rollEnchantType(bool ring, std::mt19937 &rng)
{
    return uniform(rng, 1, ring ? LastResistanceEnchant : 10);
}

// get_affix: an entry is picked with weight / (times it was picked + 1), so the rarer ones are favoured.
template <typename Entry, typename Weight>
size_t pickLeastFound(const std::vector<Entry> &entries, Weight weight, std::mt19937 &rng)
{
    std::vector<double> weights;
    weights.reserve(entries.size());

    for (const Entry &entry : entries)
    {
        weights.push_back(weight(entry));
    }

    std::discrete_distribution<size_t> distribution(weights.begin(), weights.end());
    return distribution(rng);
}

struct EquippedSlot
{
    uint32_t itemId = 0;
    const EquippedItemRuntimeState *pState = nullptr;
};

std::array<EquippedSlot, 16> equippedSlots(const Character &character)
{
    const CharacterEquipment &items = character.equipment;
    const CharacterEquipmentRuntimeState &states = character.equipmentRuntime;
    return {{
        {items.offHand, &states.offHand},
        {items.mainHand, &states.mainHand},
        {items.bow, &states.bow},
        {items.armor, &states.armor},
        {items.helm, &states.helm},
        {items.belt, &states.belt},
        {items.cloak, &states.cloak},
        {items.gauntlets, &states.gauntlets},
        {items.boots, &states.boots},
        {items.amulet, &states.amulet},
        {items.ring1, &states.ring1},
        {items.ring2, &states.ring2},
        {items.ring3, &states.ring3},
        {items.ring4, &states.ring4},
        {items.ring5, &states.ring5},
        {items.ring6, &states.ring6},
    }};
}

// Legendary affixes work while equipped and do not stack: the first worn item with the affix carries it.
const EquippedItemRuntimeState *legendaryCarrier(const Character &wearer, LegendaryAffix affix)
{
    for (const EquippedSlot &slot : equippedSlots(wearer))
    {
        if (slot.itemId != 0 && !slot.pState->broken
            && slot.pState->rulesetFields.legendaryAffixId == uint16_t(affix))
        {
            return slot.pState;
        }
    }

    return nullptr;
}

bool wears(const Character &wearer, LegendaryAffix affix)
{
    return legendaryCarrier(wearer, affix) != nullptr;
}

struct MawSpecialStat
{
    int type = 0;
    double modifier = 0;
};

struct MawSpecialStats
{
    uint16_t specialId = 0;
    // A range of enchant types adds unrounded (and is floored here); listed types round each step (IT:2768-2782).
    bool range = false;
    std::vector<MawSpecialStat> stats;
};

MawSpecialStats statRange(uint16_t specialId, int first, int last, double modifier)
{
    MawSpecialStats special = {specialId, true, {}};

    for (int type = first; type <= last; ++type)
    {
        special.stats.push_back({type, modifier});
    }

    return special;
}

// bonusEffects (IT:1772-1799): the stats of each special, by standard enchant type (1-7 the seven stats, 8 HP, 9 SP,
// 10 armour, 11-16 the resistances), before the item-power scale.
const MawSpecialStats *mawSpecialStats(uint16_t specialId)
{
    static const std::vector<MawSpecialStats> Specials = {
        statRange(1, 11, 16, 10),
        statRange(2, 1, 7, 8),
        {39, false, {{2, 25}, {3, 25}}},
        statRange(42, 1, 16, 3),
        {43, false, {{4, 10}, {8, 10}, {10, 10}}},
        {44, false, {{8, 10}}},
        {45, false, {{5, 10}, {6, 10}}},
        {46, false, {{1, 25}}},
        {47, false, {{9, 10}}},
        {48, false, {{4, 15}, {10, 5}}},
        {49, false, {{2, 10}, {7, 10}}},
        {50, false, {{11, 30}}},
        {51, false, {{2, 10}, {6, 10}, {9, 10}}},
        {52, false, {{4, 10}, {5, 10}}},
        {53, false, {{1, 20}, {3, 20}}},
        {54, false, {{4, 15}}},
        {55, false, {{7, 15}}},
        {56, false, {{1, 10}, {4, 10}}},
        {57, false, {{2, 15}, {3, 15}}},
        {74, false, {{3, 20}, {5, 20}}},
        {75, false, {{1, 20}, {2, 20}}},
        {76, false, {{2, 20}, {5, 20}}},
        {77, false, {{1, 15}, {2, 15}, {3, 15}}},
        statRange(78, 11, 14, 20),
        {79, false, {{15, 20}, {16, 20}}},
        statRange(80, 1, 16, 5),
    };
    const auto it = std::find_if(Specials.begin(), Specials.end(),
        [specialId](const MawSpecialStats &special) { return special.specialId == specialId; });
    return it != Specials.end() ? &*it : nullptr;
}

// The amount the stat in place `index` of a special gives at an item power (as applyMawSpecial adds it).
int mawSpecialStatAmount(uint16_t specialId, size_t index, int itemPower)
{
    const MawSpecialStats *pStats = mawSpecialStats(specialId);

    if (pStats == nullptr || index >= pStats->stats.size())
    {
        return 0;
    }

    const double amount = pStats->stats[index].modifier * std::min(1 + itemPower / 25.0, 5.0);
    return int(pStats->range ? std::floor(amount) : mawRound(amount));
}

// MAW's text of a special at an item power (checktext, IT:1835-1890); nothing for the specials that keep the table's.
std::optional<std::string> mawSpecialText(uint16_t specialId, int itemPower)
{
    static const std::array<const char *, 9> Schools = {
        "Air", "Body", "Dark", "Earth", "Fire", "Light", "Mind", "Spirit", "Water",
    };
    const std::string school = std::to_string(itemPower / 4 + 5);
    const std::string meditation = std::to_string(itemPower * 3 / 20 + 3);
    const auto plus = [itemPower, specialId](const char *pText)
    {
        return " +" + std::to_string(mawSpecialStatAmount(specialId, 0, itemPower)) + pText;
    };

    if (specialId >= 26 && specialId <= 34)
    {
        return std::string(Schools[size_t(specialId - 26)]) + " Magic Skill +" + school;
    }

    switch (specialId)
    {
        case 1:
            return plus(" to all Resistances.");
        case 2:
            return plus(" to all Seven Statistics.");
        case 38:
            return "Meditation Skill +" + meditation;
        case 40:
            return std::string("Leech 10% of magical damage, increases cast speed (does not stack).");
        case 42:
        case 80:
            return plus(" to Seven Stats, HP, SP, Armor, Resistances.");
        case 43:
            return plus(" to Endurance, Armor, Hit points.");
        case 44:
            return plus(" Hit points and Regenerate Hit points over time.");
        case 45:
            return plus(" Speed and Accuracy.");
        case 47:
            return plus(" Spell points and Meditation Skill +") + meditation;
        case 48:
            return plus(" Endurance and +") + std::to_string(mawSpecialStatAmount(48, 1, itemPower)) + " Armor.";
        case 49:
            return plus(" Intellect and Luck.");
        case 50:
            return plus(" Fire Resistance and Regenerate Hit points over time.");
        case 51:
            return plus(" Spell points, Speed, Intellect.");
        case 52:
            return plus(" Endurance and Accuracy.");
        case 53:
            return plus(" Might and Personality.");
        case 54:
            return plus(" Endurance and Regenerate Hit points over time.");
        case 55:
            return plus(" Luck and Meditation Skill +") + meditation;
        case 56:
            return plus(" Might and Endurance.");
        case 57:
            return plus(" Intellect and Personality.");
        case 66:
            return "Regenerates Hit Points and Meditation Skill +" + meditation;
        case 74:
            return plus(" Personality and Accuracy.");
        case 75:
            return plus(" Intellect and Might.");
        case 76:
            return plus(" Intellect and Accuracy.");
        case 77:
            return plus(" Might, Intellect and Personality.");
        case 78:
            return plus(" Elemental Resistances.");
        case 79:
            return plus(" Body and mind Resistances.");
        default:
            return std::nullopt;
    }
}

// An item skill bonus as MAW's GetSkill counts it: at most up to twice the trained skill (S:205-213).
void addCappedSkillBonus(Character &bonuses, const Character &wearer, const std::string &skillName, int amount)
{
    const std::string skill = canonicalSkillName(skillName);
    const CharacterSkill *pSkill = wearer.findSkill(skill);
    const int learned = pSkill != nullptr && pSkill->mastery != SkillMastery::None ? int(pSkill->level) : 0;
    const int room = std::max(0, learned - bonuses.itemSkillBonuses[skill]);

    if (std::min(amount, room) > 0)
    {
        bonuses.itemSkillBonuses[skill] += std::min(amount, room);
    }
}

// A special enchantment's effect under MAW (IT:1458-1476, 1772-1799, 2758-2795). The specials MAW leaves alone keep
// Standard's effect; leech (16, 40, 41), swiftness (41, 59), Shielding (36) and the regeneration specials act where
// they are read (mawLeech, the attack delay, mitigation, regeneration).
void applyMawSpecial(
    Character &bonuses,
    const Character &wearer,
    uint16_t specialId,
    int itemPower,
    const SpecialItemEnchantTable *pSpecialTable)
{
    static const std::array<const char *, 9> Schools = {
        "AirMagic", "BodyMagic", "DarkMagic", "EarthMagic", "FireMagic", "LightMagic", "MindMagic", "SpiritMagic",
        "WaterMagic",
    };
    static const std::array<uint16_t, 4> MeditationSpecials = {38, 47, 55, 66};
    static const std::array<uint16_t, 10> EffectElsewhere = {16, 36, 37, 38, 40, 41, 44, 50, 54, 59};
    bool handled = false;

    if (const MawSpecialStats *pStats = mawSpecialStats(specialId))
    {
        // chargesStatMult: x min(1 + power / 25, 5).
        const double scale = std::min(1 + itemPower / 25.0, 5.0);

        for (const MawSpecialStat &stat : pStats->stats)
        {
            const double amount = stat.modifier * scale;
            ItemEnchantRuntime::applyStandardEnchantBonus(bonuses, StandardItemEnchantKind(stat.type),
                int(pStats->range ? std::floor(amount) : mawRound(amount)));
        }

        handled = true;
    }

    if (specialId >= 26 && specialId <= 34)
    {
        addCappedSkillBonus(bonuses, wearer, Schools[size_t(specialId - 26)], itemPower / 4 + 5);
        handled = true;
    }

    if (std::find(MeditationSpecials.begin(), MeditationSpecials.end(), specialId) != MeditationSpecials.end())
    {
        addCappedSkillBonus(bonuses, wearer, "Meditation", itemPower * 3 / 20 + 3);
        handled = true;
    }

    const auto immune = [&bonuses](std::initializer_list<CharacterCondition> conditions)
    {
        for (CharacterCondition condition : conditions)
        {
            bonuses.magicalConditionImmunities.set(size_t(condition));
        }
    };

    switch (specialId)
    {
        case 18:
            immune({CharacterCondition::DiseaseWeak, CharacterCondition::DiseaseMedium,
                CharacterCondition::DiseaseSevere, CharacterCondition::Cursed});
            return;
        case 19:
            immune({CharacterCondition::Insane});
            bonuses.manaDrainImmune = true;
            return;
        case 20:
            immune({CharacterCondition::Paralyzed, CharacterCondition::Fear});
            return;
        case 21:
            immune({CharacterCondition::PoisonWeak, CharacterCondition::PoisonMedium,
                CharacterCondition::PoisonSevere, CharacterCondition::Weak});
            return;
        case 22:
            immune({CharacterCondition::Asleep, CharacterCondition::Unconscious});
            return;
        case 23:
            immune({CharacterCondition::Petrified});
            bonuses.agingImmune = true;
            return;
        case 25:
            immune({CharacterCondition::Dead, CharacterCondition::Eradicated});
            return;
        case 62:
            addCappedSkillBonus(bonuses, wearer, "IdentifyItem", 3);
            addCappedSkillBonus(bonuses, wearer, "IdentifyMonster", 3);
            return;
        default:
            break;
    }

    if (handled || std::find(EffectElsewhere.begin(), EffectElsewhere.end(), specialId) != EffectElsewhere.end())
    {
        return;
    }

    // Any other special gives no stat or skill (MAW sets every item stat from its own table, IT:2566-2610); only the
    // engine powers MAW keeps still work.
    if (const SpecialItemEnchantEntry *pEntry = pSpecialTable != nullptr ? pSpecialTable->get(specialId) : nullptr;
        pEntry != nullptr
        && (pEntry->kind == SpecialItemEnchantKind::WaterWalking
            || pEntry->kind == SpecialItemEnchantKind::FeatherFalling || pEntry->kind == SpecialItemEnchantKind::Carnage))
    {
        ItemEnchantRuntime::applySpecialEnchantBonus(bonuses, pEntry->kind);
    }
}

// The item's own effects (rare-item powers, the table's effects) as Standard has them, without its enchantments and
// without the engine's vampiric heal and flat regeneration, which MAW turns off (IT:2462-2491, S:1358-1362).
void applyStandardItemEffects(
    const ItemDefinition &itemDefinition,
    const EquippedItemRuntimeState &runtimeState,
    const StandardItemEnchantTable *pStandardTable,
    const SpecialItemEnchantTable *pSpecialTable,
    Character &bonuses)
{
    EquippedItemRuntimeState plain = runtimeState;
    plain.standardEnchantId = 0;
    plain.standardEnchantPower = 0;
    plain.specialEnchantId = 0;
    const float vampiricHealFraction = bonuses.vampiricHealFraction;
    const float healthRegenPerSecond = bonuses.healthRegenPerSecond;
    const float spellRegenPerSecond = bonuses.spellRegenPerSecond;
    ItemEnchantRuntime::applyEquippedEnchantEffects(itemDefinition, plain, pStandardTable, pSpecialTable, bonuses);
    bonuses.vampiricHealFraction = vampiricHealFraction;
    bonuses.healthRegenPerSecond = healthRegenPerSecond;
    bonuses.spellRegenPerSecond = spellRegenPerSecond;
}

// The artifact powers a tooltip names: the permanent buffs and the immunities its Standard effects give.
std::vector<std::string> artifactPowerLines(
    const ItemDefinition &itemDefinition,
    const StandardItemEnchantTable *pStandardTable,
    const SpecialItemEnchantTable *pSpecialTable)
{
    Character worn;
    applyStandardItemEffects(itemDefinition, EquippedItemRuntimeState{}, pStandardTable, pSpecialTable, worn);
    std::vector<std::string> lines;

    if (worn.halfMissileDamage)
    {
        lines.push_back("Permanent Shield");
    }

    if (worn.waterWalking)
    {
        lines.push_back("Permanent Water Walk");
    }

    if (worn.featherFalling)
    {
        lines.push_back("Permanent Feather Fall for the party");
    }

    // Poison and disease are one word each to the player.
    struct Immunity
    {
        std::vector<CharacterCondition> conditions;
        const char *pName;
    };
    const std::array<Immunity, 9> immunities = {{
        {{CharacterCondition::Cursed}, "Curse"},
        {{CharacterCondition::Weak}, "Weakness"},
        {{CharacterCondition::Asleep}, "Sleep"},
        {{CharacterCondition::Fear}, "Fear"},
        {{CharacterCondition::Insane}, "Insanity"},
        {{CharacterCondition::PoisonWeak, CharacterCondition::PoisonMedium, CharacterCondition::PoisonSevere},
            "Poison"},
        {{CharacterCondition::DiseaseWeak, CharacterCondition::DiseaseMedium, CharacterCondition::DiseaseSevere},
            "Disease"},
        {{CharacterCondition::Paralyzed}, "Paralysis"},
        {{CharacterCondition::Petrified}, "Stone"},
    }};
    std::vector<std::string> names;

    for (const Immunity &immunity : immunities)
    {
        if (std::any_of(immunity.conditions.begin(), immunity.conditions.end(),
                [&worn](CharacterCondition condition)
                { return worn.magicalConditionImmunities.test(size_t(condition)); }))
        {
            names.push_back(immunity.pName);
        }
    }

    if (!names.empty())
    {
        std::sort(names.begin(), names.end());
        std::string text = "Immune to " + names.front();

        for (size_t index = 1; index < names.size(); ++index)
        {
            text += ", " + names[index];
        }

        lines.push_back(text);
    }

    return lines;
}
}

bool mawWearsLegendaryAffix(const Character &character, int affixId)
{
    return wears(character, LegendaryAffix(affixId));
}

int mawWornSpecialCount(const Character &character, std::initializer_list<uint16_t> specialIds)
{
    int count = 0;

    for (const EquippedSlot &slot : equippedSlots(character))
    {
        if (slot.itemId != 0 && !slot.pState->broken
            && std::find(specialIds.begin(), specialIds.end(), slot.pState->specialEnchantId) != specialIds.end())
        {
            ++count;
        }
    }

    return count;
}

double mawArtifactAttackDelayMultiplier(const MawRules &rules, const Character &character)
{
    double multiplier = 1;

    for (const EquippedSlot &slot : equippedSlots(character))
    {
        if (const MawArtifact *pArtifact = slot.itemId != 0 && !slot.pState->broken
                ? rules.itemData().artifact(slot.itemId)
                : nullptr)
        {
            multiplier *= pArtifact->attackDelayMultiplier;
        }
    }

    return multiplier;
}

int mawWornItemCount(const Character &character, std::initializer_list<uint32_t> itemIds)
{
    int count = 0;

    for (const EquippedSlot &slot : equippedSlots(character))
    {
        if (slot.itemId != 0 && !slot.pState->broken
            && std::find(itemIds.begin(), itemIds.end(), slot.itemId) != itemIds.end())
        {
            ++count;
        }
    }

    return count;
}

bool mawRegenerationArtifact(uint32_t itemId, bool spellPoints)
{
    static constexpr std::array<uint32_t, 6> HealthArtifacts = {509, 520, 1337, 1331, 1335, 2027};
    static constexpr std::array<uint32_t, 7> SpellArtifacts = {513, 1334, 1331, 2024, 2032, 2033, 2034};
    return spellPoints ? std::find(SpellArtifacts.begin(), SpellArtifacts.end(), itemId) != SpellArtifacts.end()
                       : std::find(HealthArtifacts.begin(), HealthArtifacts.end(), itemId) != HealthArtifacts.end();
}

int mawWornRegenerationArtifacts(const Character &character, bool spellPoints)
{
    int count = 0;

    for (const EquippedSlot &slot : equippedSlots(character))
    {
        if (slot.itemId != 0 && !slot.pState->broken && mawRegenerationArtifact(slot.itemId, spellPoints))
        {
            ++count;
        }
    }

    return count;
}

namespace
{

// The skill a skill enchantment raises; MAW reads enchant 18 as Repair (STDITEMS says Stealing).
std::string enchantSkillName(int type)
{
    static const std::array<const char *, 8> Skills = {
        "Alchemy", "RepairItem", "DisarmTraps", "IdentifyItem", "IdentifyMonster", "Armsmaster", "Dodging", "Unarmed",
    };
    return isSkillEnchant(type) ? Skills[size_t(type - FirstSkillEnchant)] : std::string();
}

int learnedSkillLevel(const Character &character, const std::string &skill)
{
    const CharacterSkill *pSkill = character.findSkill(skill);
    return pSkill != nullptr && pSkill->mastery != SkillMastery::None ? int(pSkill->level) : 0;
}

void addPrimaryStat(Character &bonuses, int type, int amount)
{
    switch (type)
    {
        case 1:
            bonuses.magicalBonuses.might += amount;
            break;
        case 2:
            bonuses.magicalBonuses.intellect += amount;
            break;
        case 3:
            bonuses.magicalBonuses.personality += amount;
            break;
        case 5:
            bonuses.magicalBonuses.accuracy += amount;
            break;
        default:
            break;
    }
}

// Adds a base enchantment of standard enchant id `type` to `bonuses`; skills only up to the wearer's own level
// (the total is capped at twice the trained skill, so an untrained skill gets nothing).
void addBaseEnchant(Character &bonuses, const Character &wearer, int type, int amount, bool echo)
{
    if (amount <= 0)
    {
        return;
    }

    if (isSkillEnchant(type))
    {
        const std::string skill = enchantSkillName(type);
        const int room = std::max(0, learnedSkillLevel(wearer, skill) - bonuses.itemSkillBonuses[skill]);

        if (std::min(amount, room) > 0)
        {
            bonuses.itemSkillBonuses[skill] += std::min(amount, room);
        }

        return;
    }

    ItemEnchantRuntime::applyStandardEnchantBonus(bonuses, StandardItemEnchantKind(type), amount);

    // Legendary 12: Might and Accuracy give 40 % of themselves to Intellect and Personality, and the other way round.
    if (echo)
    {
        const int share = int(mawRound(amount * 0.4));

        if (type == 1 || type == 5)
        {
            addPrimaryStat(bonuses, 2, share);
            addPrimaryStat(bonuses, 3, share);
        }
        else if (type == 2 || type == 3)
        {
            addPrimaryStat(bonuses, 1, share);
            addPrimaryStat(bonuses, 5, share);
        }
    }
}

std::string formatSpeed(int recovery)
{
    std::ostringstream stream;
    stream << std::fixed << std::setprecision(2) << recovery / 100.0;
    return stream.str();
}

// baseRecovery of zzMAW-Skills.lua by weapon skill; clubs and the rest stay at 100.
int weaponBaseRecovery(const std::string &skill)
{
    static const std::array<std::pair<const char *, int>, 8> Recoveries = {{
        {"Dagger", 60}, {"Sword", 80}, {"Mace", 100}, {"Bow", 100},
        {"Staff", 120}, {"Spear", 120}, {"Axe", 140}, {"Blaster", 40},
    }};

    for (const auto &[name, recovery] : Recoveries)
    {
        if (skill == name)
        {
            return recovery;
        }
    }

    return 100;
}
}

double mawEnchantSlotMultiplier(const ItemDefinition &itemDefinition, const MawBaseItem &base)
{
    const std::string &slot = itemDefinition.equipStat;

    if (slot == "Weapon" || slot == "Weapon2" || slot == "Weapon1or2")
    {
        return base.twoHanded ? 2 : 1;
    }

    if (slot == "Missile" || slot == "Helm" || slot == "Gauntlets" || slot == "Boots")
    {
        return 1.25;
    }

    if (slot == "Armor")
    {
        return 1.5;
    }

    if (slot == "Ring")
    {
        return 0.75;
    }

    return 1;
}

std::string mawArtifactDescription(const std::string &notes)
{
    std::string text = notes;

    if (const size_t special = text.find("(Special"); special != std::string::npos)
    {
        const size_t close = text.find(')', special);
        text.erase(special, close != std::string::npos ? close - special + 1 : std::string::npos);
    }

    const size_t first = text.find_first_not_of(" \t\n");

    if (first != std::string::npos && text[first] == '(')
    {
        const size_t close = text.find(')', first);
        text.erase(0, close != std::string::npos ? close + 1 : text.size());
    }

    const size_t begin = text.find_first_not_of(" \t\n");
    const size_t end = text.find_last_not_of(" \t\n");
    return begin == std::string::npos ? std::string() : text.substr(begin, end - begin + 1);
}

std::string mawEnchantStatName(const StandardItemEnchantTable *pTable, int type)
{
    if (isSkillEnchant(type))
    {
        return displaySkillName(enchantSkillName(type));
    }

    const StandardItemEnchantEntry *pEntry = pTable != nullptr ? pTable->get(uint16_t(type)) : nullptr;
    return pEntry != nullptr ? pEntry->statName : std::string();
}

int mawEnchantReadPower(int type, int power, bool first, double slotMultiplier, bool ring)
{
    double value = power;

    if (type == HitPointsEnchant || type == SpellPointsEnchant)
    {
        value = mawRound(value * (1 + std::min(value / 50 / slotMultiplier, 5.0)));
    }
    else if (isResistanceEnchant(type))
    {
        value += first ? 10 : 0;
        value = ring ? value * 100 / 200 : value;
    }

    return int(value);
}

MawItemRules::MawItemRules(MawRules &rules)
    : m_rules(rules)
{
}

bool MawItemRules::rollsRareItem(const ItemGenerationRequest &, Party *, std::mt19937 &) const
{
    // MAW's artifacts come from its own list, rolled on enchantable drops (rollEnchantments).
    return false;
}

namespace
{
constexpr uint32_t FirstSealedBookId = 971;
constexpr std::array<const char *, 9> SealedBookSchools = {
    "Fire", "Air", "Water", "Earth", "Spirit", "Mind", "Body", "Light", "Dark"};

// The school (1-9) of a spellbook that is sealed when found: the MM8 (400-498), MM7 (1202-1300) and MM6 (1902-2018)
// books, 11 a school (13 for MM6); 0 for any other item.
int sealableBookSchool(uint32_t itemId)
{
    if (itemId >= 400 && itemId <= 498)
    {
        return int(itemId - 399 + 10) / 11;
    }

    if (itemId >= 1202 && itemId <= 1300)
    {
        return int(itemId - 1201 + 10) / 11;
    }

    if (itemId >= 1902 && itemId <= 2018)
    {
        return int(itemId - 1901 + 12) / 13;
    }

    return 0;
}

// The school (1-9) of a sealed spellbook, or 0.
int sealedBookSchool(const InventoryItem &item)
{
    const bool sealed = item.objectDescriptionId >= FirstSealedBookId
        && item.objectDescriptionId < FirstSealedBookId + SealedBookSchools.size()
        && item.rulesetFields.craftState != 0;
    return sealed ? int(item.objectDescriptionId - FirstSealedBookId + 1) : 0;
}

// A spellbook's place in its school, 1 (the first spell) to 11; MM6's thirteen books per school share places with their
// neighbours (getBookTier). 0 for any other item.
int spellbookTier(uint32_t itemId)
{
    if (itemId >= 400 && itemId <= 498)
    {
        return int(itemId - 400) % 11 + 1;
    }

    if (itemId >= 1202 && itemId <= 1300)
    {
        return int(itemId - 1202) % 11 + 1;
    }

    if (itemId >= 1902 && itemId <= 2018)
    {
        const int tier = int(itemId - 1902) % 13 + 1;
        return tier > 5 ? tier - 2 : tier > 3 ? tier - 1 : tier;
    }

    return 0;
}

SkillMastery sealedBookMastery(const ItemDefinition &book)
{
    const int difficulty = std::atoi(book.idRepSt.c_str());
    return difficulty >= 15 ? SkillMastery::Grandmaster
        : difficulty >= 10  ? SkillMastery::Master
        : difficulty >= 5   ? SkillMastery::Expert
                            : SkillMastery::Normal;
}
}

void MawItemRules::rollPlainItem(
    InventoryItem &item,
    const ItemDefinition &itemDefinition,
    const ItemGenerationRequest &request) const
{
    if (const int school = sealableBookSchool(item.objectDescriptionId);
        school > 0 && request.mode != ItemGenerationMode::Shop)
    {
        item.rulesetFields.craftState = uint16_t(item.objectDescriptionId);
        item.objectDescriptionId = FirstSealedBookId + uint32_t(school - 1);
        return;
    }

    if (itemDefinition.equipStat != "Reagent")
    {
        return;
    }

    const MawGameState &state = m_rules.state();
    const double dropLevel = request.dropLevel ? double(*request.dropLevel)
        : request.mode == ItemGenerationMode::Shop ? ShopLevelShare * state.totalLevel()
                                                   : m_rules.mapDropLevel();
    const double divisor = m_rules.lootConfig().austerity ? 8 : 3;
    item.rulesetFields.dropLevel =
        uint16_t(std::clamp(int(mawRound(std::min(dropLevel, state.totalLevel()) / divisor)), 0, 2047));
}

namespace
{
struct MawQuestBoundItem
{
    uint32_t itemId = 0;
    // Any one of these quest bits or awards means its quest is done.
    std::vector<uint32_t> questBits;
    std::vector<uint32_t> awards;
};

const std::vector<MawQuestBoundItem> &mawQuestBoundItems()
{
    static const std::vector<MawQuestBoundItem> Items = {
        {516, {128}, {}},
        {539, {1540, 1541}, {}},
        {540, {1543, 1544}, {}},
        {541, {1545}, {29}},
        {1342, {1564, 1565}, {}},
        {1344, {1586, 1587, 1588, 1589}, {}},
        {2118, {}, {79}},
        {2119, {}, {57}},
    };
    return Items;
}

// The unique items that sell once a game, and the seer bit that would hand them out again (0 for none).
const std::vector<std::pair<uint32_t, uint32_t>> &mawSellOnceItems()
{
    static const std::vector<std::pair<uint32_t, uint32_t>> Items = {
        {516, 0}, {539, 199}, {540, 200}, {541, 201}, {1439, 0}, {2118, 0}, {2119, 0}, {2199, 0},
    };
    return Items;
}
}

std::optional<std::string> MawItemRules::sellRefusal(const Party &party, const InventoryItem &item) const
{
    const uint32_t itemId = item.objectDescriptionId;
    const auto once = std::find_if(mawSellOnceItems().begin(), mawSellOnceItems().end(),
        [itemId](const std::pair<uint32_t, uint32_t> &entry) { return entry.first == itemId; });

    if (once != mawSellOnceItems().end() && m_rules.state().soldUniqueItems.contains(itemId))
    {
        return std::string("I have already bought an item like that.");
    }

    const auto quest = std::find_if(mawQuestBoundItems().begin(), mawQuestBoundItems().end(),
        [itemId](const MawQuestBoundItem &entry) { return entry.itemId == itemId; });

    if (quest == mawQuestBoundItems().end())
    {
        return std::nullopt;
    }

    const bool done = std::any_of(quest->questBits.begin(), quest->questBits.end(),
                          [&party](uint32_t bit) { return party.hasQuestBit(bit); })
        || std::any_of(quest->awards.begin(), quest->awards.end(),
            [&party](uint32_t award) { return party.hasAward(award); });
    return done ? std::nullopt
                : std::optional<std::string>("No, no -- you will still need that item. Come back once the task it is "
                                             "for is done.");
}

void MawItemRules::itemSold(Party &party, const InventoryItem &item) const
{
    const uint32_t itemId = item.objectDescriptionId;
    const auto once = std::find_if(mawSellOnceItems().begin(), mawSellOnceItems().end(),
        [itemId](const std::pair<uint32_t, uint32_t> &entry) { return entry.first == itemId; });

    if (once == mawSellOnceItems().end())
    {
        return;
    }

    m_rules.state().soldUniqueItems[itemId] += 1;

    // The seer would hand it out again while this bit is set.
    if (once->second != 0)
    {
        party.setQuestBit(once->second, false);
    }
}

bool MawItemRules::levelSevenGivesRareItem() const
{
    return false;
}

void MawItemRules::rollEnchantments(
    InventoryItem &item,
    const ItemDefinition &itemDefinition,
    const ItemRollTables &tables,
    const ItemGenerationRequest &request,
    Party *pParty,
    std::mt19937 &rng) const
{
    const MawItemData &data = m_rules.itemData();
    const MawBaseItem *pBase = data.baseItem(itemDefinition.itemId);

    if (pBase == nullptr)
    {
        return;
    }

    MawGameState &state = m_rules.state();
    const MawLootConfig config = m_rules.lootConfig();
    const bool shop = request.mode == ItemGenerationMode::Shop;

    // 0.5 % of the enchantable drops outside shops become an artifact, with bad-luck protection.
    if (!shop && request.allowRareItems && !data.artifacts().empty())
    {
        if (unitDraw(rng) < mawPityChance(ArtifactChance, state.artifactPity))
        {
            const size_t index = pickLeastFound(
                data.artifacts(),
                [&state](const MawArtifact &artifact)
                {
                    const auto it = state.artifactDrops.find(artifact.itemId);
                    return artifact.dropWeight / double(1 + (it != state.artifactDrops.end() ? it->second : 0));
                },
                rng);
            const uint32_t artifactId = data.artifacts()[index].itemId;

            if (tables.items.get(artifactId) != nullptr)
            {
                state.artifactPity = 0;
                ++state.artifactDrops[artifactId];
                item = ItemGenerator::makeInventoryItem(artifactId, tables.items, request.mode);

                if (pParty != nullptr)
                {
                    pParty->markArtifactItemFound(artifactId);
                }

                return;
            }
        }

        state.artifactPity += 1;
    }

    const double dropLevel = request.dropLevel ? double(*request.dropLevel)
        : shop                                 ? ShopLevelShare * state.totalLevel()
                                               : m_rules.mapDropLevel();
    // A dimension map raises the enchant tier from power 28 and the upgrade chances by its affixes; the Arena raises
    // the tier by 20 (GetEnchantTierBonus, GetRarityMultiplier).
    const MawDimensionRun *pRun = m_rules.dimensionRun(m_rules.currentMap());
    const int tierBonus = (pRun != nullptr ? std::max((int(pRun->power) - 28) / 2, 0) : 0)
        + (m_rules.currentMap() == "d42.blv" ? 20 : 0);
    const int grade = std::clamp(request.treasureLevel, 1, 6);
    const int lootTier = mawLootTier(grade, dropLevel, request.boss, request.omnipotent, tierBonus, unitDraw(rng));

    MawRarityRollInputs rarityInputs;
    rarityInputs.lootTier = lootTier;
    rarityInputs.upgradeMultiplier =
        pRun != nullptr ? 1 + mawDimensionStrength(pRun->power, pRun->affixCount()) / 400 : 1;
    rarityInputs.difficulty = config.difficulty;
    rarityInputs.boss = request.boss;
    rarityInputs.shop = shop;
    rarityInputs.noLegendary = config.austerity;
    rarityInputs.omnipotent = request.omnipotent;
    MawRarityPity pity{state.celestialPity, state.legendaryPity, state.primordialPity};
    const MawRarity rarity = mawRollRarity(rarityInputs, pity, rng);

    // Gear nobody found (a mercenary's on offer) does not move the loot's bad-luck counters (audit ROB-2-7).
    if (!request.sparesLuck)
    {
        state.celestialPity = pity.celestial;
        state.legendaryPity = pity.legendary;
        state.primordialPity = pity.primordial;
    }

    rollRarityEnchantments(
        item, itemDefinition, tables, *pBase, lootTier, grade, request.boss, dropLevel, rarity, 0, true, rng);
}

void MawItemRules::rollEnchantmentsAtRarity(
    InventoryItem &item,
    const ItemDefinition &itemDefinition,
    const ItemRollTables &tables,
    int dropLevel,
    MawRarity rarity,
    int legendaryAffix,
    std::mt19937 &rng) const
{
    const MawBaseItem *pBase = m_rules.itemData().baseItem(itemDefinition.itemId);

    if (pBase == nullptr)
    {
        return;
    }

    constexpr int Grade = 6;
    const int lootTier = mawLootTier(Grade, double(dropLevel), true, false, 0, unitDraw(rng));
    rollRarityEnchantments(item, itemDefinition, tables, *pBase, lootTier, Grade, true, double(dropLevel), rarity,
        legendaryAffix, false, rng);
}

void MawItemRules::rollRarityEnchantments(
    InventoryItem &item,
    const ItemDefinition &itemDefinition,
    const ItemRollTables &tables,
    const MawBaseItem &base,
    int lootTier,
    int grade,
    bool boss,
    double dropLevel,
    MawRarity rarity,
    int legendaryAffix,
    bool countFind,
    std::mt19937 &rng) const
{
    MawGameState &state = m_rules.state();
    const MawLootConfig config = m_rules.lootConfig();
    const MawStrengthRange powerRange = mawItemPowerRange(rarity);
    const int itemPower = mawItemPower(int(dropLevel), rarity, uniform(rng, powerRange.minimum, powerRange.maximum));
    ItemRulesetFields &fields = item.rulesetFields;
    fields.lootRarity = uint8_t(rarity);
    fields.ancientTier = rarity == MawRarity::Ancient ? 1
        : rarity == MawRarity::Primordial || rarity == MawRarity::Celestial ? 2
                                                                            : 0;
    fields.itemPower = uint16_t(itemPower);
    // The stored level is floored, as MAW's bit encoding does (zMaw_ItemBits.lua:160).
    fields.dropLevel = uint16_t(std::clamp(int(std::floor(dropLevel)), 0, 2047));

    const bool ring = itemDefinition.equipStat == "Ring";
    const MawStrengthRange strengthRange = mawEnchantStrengthRange(rarity);
    const auto rollStrength = [&]()
    {
        return mawEnchantStrength(
            lootTier, rarity, uniform(rng, strengthRange.minimum, strengthRange.maximum), config);
    };
    int type1 = 0;
    int strength1 = 0;
    int type2 = 0;
    int strength2 = 0;

    if (rarity >= MawRarity::Uncommon)
    {
        type1 = rollEnchantType(ring, rng);
        strength1 = rollStrength();

        // A tenth of first enchantments raise a skill instead; Dodge on chain or plate and Unarmed on a weapon other
        // than a staff or a club become Armsmaster (IT:1175-1182).
        if (uniform(rng, 1, 10) == 10)
        {
            type1 = uniform(rng, FirstSkillEnchant, LastSkillEnchant);
            const std::string skill = canonicalSkillName(itemDefinition.skillGroup);

            if (type1 == DodgeEnchant && itemDefinition.equipStat == "Armor"
                && (skill == "ChainArmor" || skill == "PlateArmor"))
            {
                type1 = ArmsmasterEnchant;
            }
            else if (type1 == UnarmedEnchant && isWeapon(itemDefinition) && skill != "Staff" && skill != "Club")
            {
                type1 = ArmsmasterEnchant;
            }
        }
    }

    if (rarity >= MawRarity::Rare)
    {
        type2 = uniform(rng, 1, 10);
        strength2 = rollStrength();

        // The two enchantments differ: the first is rolled again within its group.
        while (type1 == type2)
        {
            type1 = isResistanceEnchant(type1) ? uniform(rng, FirstResistanceEnchant, LastResistanceEnchant)
                                               : uniform(rng, 1, 10);
        }
    }

    const double multiplier = mawEnchantSlotMultiplier(itemDefinition, base);

    if (type1 != 0)
    {
        if (isSkillEnchant(type1))
        {
            strength1 = int(std::ceil(std::max(std::sqrt(double(strength1)), strength1 / 10.0)));
        }

        strength1 = int(std::ceil(strength1 * multiplier));
        item.standardEnchantId = uint16_t(type1);
        item.standardEnchantPower = uint16_t(std::min(strength1, 65535));
    }

    if (type2 != 0)
    {
        strength2 = std::min(int(std::floor(strength2 * multiplier)), 65535);

        // Within one of the first, also a skill enchantment's, it takes the first's strength (IT:1296-1299).
        if (std::abs(strength2 - strength1) <= 1)
        {
            strength2 = strength1;
        }

        fields.secondStandardEnchantId = uint16_t(type2);
        fields.secondStandardEnchantPower = uint16_t(strength2);
    }

    if (rarity >= MawRarity::Legendary && legendaryAffix != 0)
    {
        fields.legendaryAffixId = uint16_t(legendaryAffix);
    }
    else if (rarity >= MawRarity::Legendary)
    {
        std::vector<int> affixes;

        for (int affix = MawFirstLegendaryAffix; affix < MawFirstLegendaryAffix + MawLegendaryAffixCount; ++affix)
        {
            affixes.push_back(affix);
        }

        const size_t index = pickLeastFound(
            affixes,
            [&state](int affix)
            {
                const auto it = state.legendaryAffixDrops.find(uint32_t(affix));
                return 1.0 / (1 + (it != state.legendaryAffixDrops.end() ? it->second : 0));
            },
            rng);
        fields.legendaryAffixId = uint16_t(affixes[index]);

        if (countFind)
        {
            ++state.legendaryAffixDrops[uint32_t(affixes[index])];
        }
    }

    if (rarity >= MawRarity::Epic)
    {
        // The special comes from the pool of the drop's grade (MAW's SPCITEMS level groups); only bosses reach the
        // strongest one.
        const int pool = std::clamp(grade, 3, boss ? 6 : 5);
        const std::optional<uint16_t> special =
            ItemEnchantRuntime::chooseSpecialEnchantId(itemDefinition, tables.specialEnchants, pool, rng);
        uint16_t specialId = special.value_or(0);
        int melee = 0;
        int caster = 0;

        for (int type : {type1, type2})
        {
            melee += type == 1 || type == 5 ? 1 : 0;
            caster += type == 2 || type == 3 ? 1 : 0;
        }

        if (melee > caster)
        {
            specialId = specialId == AscensionSpecial ? DragonSpecial
                : specialId == LichSpecial            ? DarknessSpecial
                                                      : specialId;
        }
        else if (caster > melee)
        {
            specialId = specialId == DragonSpecial ? AscensionSpecial
                : specialId == DarknessSpecial     ? LichSpecial
                                                   : specialId;
        }

        // Legendary 19 strengthens enchantment damage, so its special is one that deals some.
        if (fields.legendaryAffixId == uint16_t(LegendaryAffix::EnchantDamage))
        {
            specialId = specialId == LichSpecial ? AscensionSpecial
                : specialId == DarknessSpecial   ? DragonSpecial
                                                 : specialId;
        }

        item.specialEnchantId = specialId;
    }
}

InventoryItem MawItemRules::celestialAtLevel(
    const InventoryItem &item,
    const ItemDefinition &itemDefinition,
    int wearerLevel) const
{
    const MawBaseItem *pBase = m_rules.itemData().baseItem(itemDefinition.itemId);

    if (pBase == nullptr || MawRarity(item.rulesetFields.lootRarity) != MawRarity::Celestial)
    {
        return item;
    }

    const MawLootConfig config = m_rules.lootConfig();
    const double level = celestialLevel(wearerLevel);
    const double tier = level / 11 + 5;
    const double strength = mawRound(std::ceil(mawEnchantStrengthCurve(tier, config.austerity) * config.enchantPower)
        * 1.25 * mawEnchantSlotMultiplier(itemDefinition, *pBase));
    InventoryItem scaled = item;
    scaled.rulesetFields.itemPower = uint16_t(mawItemPower(int(level), MawRarity::Celestial, 24));
    scaled.standardEnchantPower =
        uint16_t(isSkillEnchant(item.standardEnchantId) ? int(mawRound(strength / 10)) : int(strength));
    scaled.rulesetFields.secondStandardEnchantPower = uint16_t(std::min(strength, 65535.0));
    return scaled;
}

double MawItemRules::celestialLevel(int wearerLevel) const
{
    const bool madness = m_rules.options().challengeMode == RulesetChallengeMode::BeyondMadness;
    const double level = std::min(double(wearerLevel), 1.2 * m_rules.state().totalLevel());
    return std::clamp(level, 0.0, double(madness ? MadnessCelestialLevelCap : CelestialLevelCap));
}

std::optional<MawWeaponDamage> MawItemRules::weaponDamage(
    const ItemDefinition &itemDefinition,
    const ItemRulesetFields &fields,
    int wearerLevel) const
{
    const MawItemData &data = m_rules.itemData();
    const double quality = 1 + fields.qualityPercent / 100.0;

    if (const MawArtifact *pArtifact = data.artifact(itemDefinition.itemId))
    {
        // An artifact is a top-rung weapon of its kind at the party's level.
        return pArtifact->base == MawArtifact::Base::Weapon
            ? std::optional<MawWeaponDamage>(mawWeaponDamage(
                m_rules.state().totalLevel(), pArtifact->twoHanded, pArtifact->rung, pArtifact->diceCount, quality))
            : std::nullopt;
    }

    const MawBaseItem *pBase = data.baseItem(itemDefinition.itemId);

    if (pBase == nullptr || pBase->diceCount <= 0)
    {
        return std::nullopt;
    }

    int itemPower = fields.itemPower;

    if (MawRarity(fields.lootRarity) == MawRarity::Celestial)
    {
        // A Celestial item grows with its wearer: Primordial power at the wearer's level.
        itemPower = mawItemPower(int(celestialLevel(wearerLevel)), MawRarity::Celestial, 24);
    }

    return mawWeaponDamage(itemPower * 5.0, pBase->twoHanded, pBase->rung, pBase->diceCount, quality);
}

std::optional<int> MawItemRules::weaponGuardBase(
    const ItemDefinition &itemDefinition,
    const ItemRulesetFields &fields,
    int wearerLevel) const
{
    const MawItemData &data = m_rules.itemData();

    if (const MawArtifact *pArtifact = data.artifact(itemDefinition.itemId))
    {
        return pArtifact->base == MawArtifact::Base::Weapon ? std::optional<int>(pArtifact->guardBase) : std::nullopt;
    }

    const MawBaseItem *pBase = data.baseItem(itemDefinition.itemId);

    if (pBase == nullptr || pBase->diceCount <= 0)
    {
        return std::nullopt;
    }

    int itemPower = fields.itemPower;

    if (MawRarity(fields.lootRarity) == MawRarity::Celestial)
    {
        itemPower = mawItemPower(int(celestialLevel(wearerLevel)), MawRarity::Celestial, 24);
    }

    // The weapon upscaler's flat for the rung, halved for one-handers (IT:1416-1430); the top rung's is 16 or 8.
    const double half = pBase->twoHanded ? 1 : 0.5;
    const int flat = int(mawRound(16 * (pBase->rung - 1) / 5 * half));
    return flat + int(mawRound(16 * half * itemPower / 30));
}

std::optional<int> MawItemRules::armorClass(
    const ItemDefinition &itemDefinition,
    const ItemRulesetFields &fields,
    int wearerLevel) const
{
    const MawItemData &data = m_rules.itemData();
    const double quality = 1 + fields.qualityPercent / 100.0;

    if (const MawArtifact *pArtifact = data.artifact(itemDefinition.itemId))
    {
        if (pArtifact->base == MawArtifact::Base::Weapon)
        {
            return std::nullopt;
        }

        const int power = pArtifact->base == MawArtifact::Base::Armor
            ? mawItemPowerForLevel(m_rules.state().totalLevel())
            : 0;
        return mawArmorClass(pArtifact->printedArmorClass, pArtifact->referenceArmorClass, power, quality);
    }

    const MawBaseItem *pBase = data.baseItem(itemDefinition.itemId);

    if (pBase == nullptr || pBase->diceCount > 0)
    {
        return std::nullopt;
    }

    int itemPower = fields.itemPower;

    if (MawRarity(fields.lootRarity) == MawRarity::Celestial)
    {
        itemPower = mawItemPower(int(celestialLevel(wearerLevel)), MawRarity::Celestial, 24);
    }

    return mawArmorClass(pBase->baseArmorClass, pBase->referenceArmorClass, itemPower, quality);
}

std::optional<ItemBaseStats> MawItemRules::baseStats(
    const ItemDefinition &itemDefinition,
    const ItemRulesetFields &fields,
    int wearerLevel) const
{
    const MawItemData &data = m_rules.itemData();

    if (data.artifact(itemDefinition.itemId) == nullptr && data.baseItem(itemDefinition.itemId) == nullptr)
    {
        return std::nullopt;
    }

    ItemBaseStats stats;

    if (const std::optional<MawWeaponDamage> damage = weaponDamage(itemDefinition, fields, wearerLevel))
    {
        stats.attackBonus = damage->shownBonus;
        stats.minimumDamage = damage->minimum;
        stats.maximumDamage = damage->maximum;
    }

    stats.armorClass = armorClass(itemDefinition, fields, wearerLevel).value_or(0);
    return stats;
}

MawArtifactBonuses MawItemRules::artifactBonuses(const MawArtifact &artifact, const ItemDefinition &itemDefinition) const
{
    const MawLootConfig config = m_rules.lootConfig();
    const double level = m_rules.state().totalLevel();
    const double lootTier = level / 15 + std::min(1 + level / 15, 6.0);
    const double unit = mawEnchantStrengthCurve(lootTier, config.austerity) * config.enchantPower;
    const bool ring = itemDefinition.equipStat == "Ring";
    static const std::array<const char *, 16> StatNames = {
        "Might", "Intellect", "Personality", "Endurance", "Accuracy", "Speed", "Luck", "HP", "SP",
        "ArmorClass", "FireResistance", "AirResistance", "WaterResistance", "EarthResistance",
        "MindResistance", "BodyResistance",
    };
    const auto statType = [](const std::string &name)
    {
        const auto it = std::find(StatNames.begin(), StatNames.end(), name);
        return it != StatNames.end() ? int(it - StatNames.begin()) + 1 : 0;
    };
    MawArtifactBonuses bonuses;

    for (const auto &[name, coefficient] : artifact.stats)
    {
        const int type = statType(name);
        const int amount = int(mawRound(coefficient * unit * artifact.slotMultiplier));
        bonuses.stats.emplace_back(type, mawEnchantReadPower(type, amount, false, artifact.slotMultiplier, ring));
    }

    const double skillUnit = std::ceil(std::max(std::sqrt(unit), unit / 10)) * artifact.slotMultiplier;

    for (const auto &[name, coefficient] : artifact.skills)
    {
        bonuses.skills.emplace_back(name, int(mawRound(coefficient * skillUnit)));
    }

    for (const auto &[name, amount] : artifact.flat)
    {
        bonuses.flat.emplace_back(statType(name), int(mawRound(amount)));
    }

    return bonuses;
}

void MawItemRules::applyEquippedEnchantEffects(
    const ItemDefinition &itemDefinition,
    const EquippedItemRuntimeState &runtimeState,
    const StandardItemEnchantTable *pStandardTable,
    const SpecialItemEnchantTable *pSpecialTable,
    const Character &wearer,
    Character &bonuses) const
{
    const CharacterStatBonuses before = bonuses.magicalBonuses;
    const auto itemSkill = [&bonuses](const char *pName)
    {
        const auto it = bonuses.itemSkillBonuses.find(pName);
        return it != bonuses.itemSkillBonuses.end() ? it->second : 0;
    };
    const int dodgingBefore = itemSkill("Dodging");
    const int unarmedBefore = itemSkill("Unarmed");
    applyItemEffects(itemDefinition, runtimeState, pStandardTable, pSpecialTable, wearer, bonuses);

    if (!mawIsDragon(wearer))
    {
        return;
    }

    // Its Dodging and Unarmed additions too, the dragon's Scales and Fangs, still within twice the trained skill
    // (IT:3003-3015).
    for (const auto &[pName, old] : {std::pair{"Dodging", dodgingBefore}, std::pair{"Unarmed", unarmedBefore}})
    {
        const int added = itemSkill(pName) - old;
        const int room = std::max(0, learnedSkillLevel(wearer, pName) - itemSkill(pName));

        if (added > 0 && room > 0)
        {
            bonuses.itemSkillBonuses[pName] += std::min(2 * added, room);
        }
    }

    // A dragon-race wearer's items give their stats, hit points, armour and resistances three times over
    // (zzMaw-Items.lua:3002-3014).
    CharacterStatBonuses &after = bonuses.magicalBonuses;
    const auto triple = [](int &value, int old)
    {
        value += 2 * (value - old);
    };

    for (int CharacterStatBonuses::*pField : {&CharacterStatBonuses::might, &CharacterStatBonuses::intellect,
             &CharacterStatBonuses::personality, &CharacterStatBonuses::endurance, &CharacterStatBonuses::speed,
             &CharacterStatBonuses::accuracy, &CharacterStatBonuses::luck, &CharacterStatBonuses::maxHealth,
             &CharacterStatBonuses::maxSpellPoints, &CharacterStatBonuses::armorClass})
    {
        triple(after.*pField, before.*pField);
    }

    for (int CharacterResistanceSet::*pField : {&CharacterResistanceSet::fire, &CharacterResistanceSet::air,
             &CharacterResistanceSet::water, &CharacterResistanceSet::earth, &CharacterResistanceSet::mind,
             &CharacterResistanceSet::body})
    {
        triple(after.resistances.*pField, before.resistances.*pField);
    }
}

void MawItemRules::applyItemEffects(
    const ItemDefinition &itemDefinition,
    const EquippedItemRuntimeState &runtimeState,
    const StandardItemEnchantTable *pStandardTable,
    const SpecialItemEnchantTable *pSpecialTable,
    const Character &wearer,
    Character &bonuses) const
{
    if (runtimeState.broken)
    {
        return;
    }

    // Legendaries 25 and 33: Ascension +10, every melee weapon skill +10, past the item skill cap (S:2598-2628).
    if (legendaryCarrier(wearer, LegendaryAffix::Ascension) == &runtimeState)
    {
        bonuses.itemSkillBonuses["Learning"] += 10;
    }

    if (legendaryCarrier(wearer, LegendaryAffix::MeleeSkills) == &runtimeState)
    {
        for (const char *pSkill : {"Staff", "Sword", "Dagger", "Axe", "Spear", "Mace"})
        {
            bonuses.itemSkillBonuses[pSkill] += 10;
        }
    }

    const MawItemData &data = m_rules.itemData();
    const MawLootConfig config = m_rules.lootConfig();

    if (const MawArtifact *pArtifact = data.artifact(itemDefinition.itemId))
    {
        // The artifact keeps its powers but its stats and skills follow its budget at the party's level.
        const CharacterStatBonuses statsBefore = bonuses.magicalBonuses;
        const std::unordered_map<std::string, int> skillsBefore = bonuses.itemSkillBonuses;
        applyStandardItemEffects(itemDefinition, runtimeState, pStandardTable, pSpecialTable, bonuses);
        // MAW's buffs for these artifacts (artifactBuffs, zzzMaw_Artifacts.lua:735-749): Excalibur's Bless adds 3 attack,
        // not Standard's skill-scaled amount; Galahad's and Pellinore's Stoneskin 20 armour.
        constexpr uint32_t Excalibur = 2023;
        constexpr uint32_t Galahad = 2026;
        constexpr uint32_t Pellinore = 2027;
        const int attackCap = itemDefinition.itemId == Excalibur ? 3 : std::numeric_limits<int>::max();
        const int meleeAttack =
            statsBefore.meleeAttack + std::min(bonuses.magicalBonuses.meleeAttack - statsBefore.meleeAttack, attackCap);
        const int rangedAttack = statsBefore.rangedAttack
            + std::min(bonuses.magicalBonuses.rangedAttack - statsBefore.rangedAttack, attackCap);
        const int meleeDamage = bonuses.magicalBonuses.meleeDamage;
        const int rangedDamage = bonuses.magicalBonuses.rangedDamage;
        bonuses.magicalBonuses = statsBefore;
        bonuses.magicalBonuses.meleeAttack = meleeAttack;
        bonuses.magicalBonuses.rangedAttack = rangedAttack;
        bonuses.magicalBonuses.meleeDamage = meleeDamage;
        bonuses.magicalBonuses.rangedDamage = rangedDamage;
        bonuses.magicalBonuses.armorClass += itemDefinition.itemId == Galahad || itemDefinition.itemId == Pellinore ? 20 : 0;
        bonuses.itemSkillBonuses = skillsBefore;

        const MawArtifactBonuses budget = artifactBonuses(*pArtifact, itemDefinition);
        const double resistanceMultiplier = wears(wearer, LegendaryAffix::ResistanceEnchants) ? 1.5 : 1;

        for (const auto &[type, amount] : budget.stats)
        {
            // The budget's resistances count as resistance enchantments, the best per element, apart from the
            // resistances; only the fixed part stays a resistance (collectArtifactBonuses, MAW fc17d917).
            if (isResistanceEnchant(type))
            {
                int &best = resistanceField(bonuses.itemResistanceEnchants, type);
                best = std::max(best, int(mawRound(std::max(amount, 0) * resistanceMultiplier)));

                if (amount < 0)
                {
                    ItemEnchantRuntime::applyStandardEnchantBonus(bonuses, StandardItemEnchantKind(type), amount);
                }

                continue;
            }

            ItemEnchantRuntime::applyStandardEnchantBonus(bonuses, StandardItemEnchantKind(type), amount);
        }

        for (const auto &[type, amount] : budget.flat)
        {
            ItemEnchantRuntime::applyStandardEnchantBonus(bonuses, StandardItemEnchantKind(type), amount);
        }

        for (const auto &[skillName, amount] : budget.skills)
        {
            const std::string name = canonicalSkillName(skillName);
            const int room = std::max(0, learnedSkillLevel(wearer, name) - bonuses.itemSkillBonuses[name]);

            if (std::min(amount, room) > 0)
            {
                bonuses.itemSkillBonuses[name] += std::min(amount, room);
            }
        }

        // Its schools gain half the trained skill, up to twice the skill in all (zzMaw-Items.lua:2587-2611).
        for (const std::string &school : pArtifact->spellBonus)
        {
            addCappedSkillBonus(bonuses, wearer, school, learnedSkillLevel(wearer, school) / 2);
        }

        return;
    }

    const MawBaseItem *pBase = data.baseItem(itemDefinition.itemId);

    const ItemRulesetFields &fields = runtimeState.rulesetFields;
    applyStandardItemEffects(itemDefinition, runtimeState, pStandardTable, pSpecialTable, bonuses);

    if (pBase == nullptr)
    {
        if (const StandardItemEnchantEntry *pEntry = runtimeState.standardEnchantId != 0 && pStandardTable != nullptr
                ? pStandardTable->get(runtimeState.standardEnchantId)
                : nullptr)
        {
            ItemEnchantRuntime::applyStandardEnchantBonus(
                bonuses, pEntry->kind, std::max(1, int(runtimeState.standardEnchantPower)));
        }

        applyMawSpecial(bonuses, wearer, runtimeState.specialEnchantId, fields.itemPower, pSpecialTable);
        return;
    }

    // The item's own effects as Standard has them; the enchantments MAW's way.
    applyMawSpecial(bonuses, wearer, runtimeState.specialEnchantId,
        MawRarity(fields.lootRarity) == MawRarity::Celestial
            ? mawItemPower(int(celestialLevel(int(wearer.level))), MawRarity::Celestial, 24)
            : fields.itemPower,
        pSpecialTable);

    const bool ring = itemDefinition.equipStat == "Ring";
    const double multiplier = readSlotMultiplier(itemDefinition, *pBase);
    const bool echo = wears(wearer, LegendaryAffix::EnchantEcho);
    const double resistanceMultiplier = wears(wearer, LegendaryAffix::ResistanceEnchants) ? 1.5 : 1;
    int power1 = runtimeState.standardEnchantPower;
    int power2 = fields.secondStandardEnchantPower;

    if (MawRarity(fields.lootRarity) == MawRarity::Celestial)
    {
        // A Celestial item's enchantments are those of a Primordial one at its wearer's level.
        InventoryItem stored;
        stored.standardEnchantId = runtimeState.standardEnchantId;
        stored.rulesetFields = fields;
        const InventoryItem scaled = celestialAtLevel(stored, itemDefinition, int(wearer.level));
        power1 = scaled.standardEnchantPower;
        power2 = scaled.rulesetFields.secondStandardEnchantPower;
    }

    const auto applyEnchant = [&](int type, int power, bool first)
    {
        if (type == 0 || (isSkillEnchant(type) && !first))
        {
            return;
        }

        const double value = readEnchantment(type, power, first, itemDefinition, *pBase, ring);

        // Resistance enchantments stay apart from the resistances: the best per element cuts damage on its own
        // (IT:2740-2750, zzMaw-Stats.lua:1108-1131).
        if (isResistanceEnchant(type))
        {
            int &best = resistanceField(bonuses.itemResistanceEnchants, type);
            best = std::max(best, int(mawRound(value * resistanceMultiplier)));
            return;
        }

        addBaseEnchant(bonuses, wearer, type, int(mawRound(value)), echo);
    };

    applyEnchant(runtimeState.standardEnchantId, power1, true);
    applyEnchant(fields.secondStandardEnchantId, power2, false);
}

ItemWield MawItemRules::wield(const Character &character, const ItemDefinition &itemDefinition) const
{
    ItemWield wield = ItemRules::wield(character, itemDefinition);
    const std::string skill = canonicalSkillName(itemDefinition.skillGroup);
    const CharacterSkill *pAxe = character.findSkill("Axe");
    const SkillMastery axe = pAxe != nullptr ? pAxe->mastery : SkillMastery::None;
    constexpr uint32_t Minotaur = 3;
    constexpr uint32_t Dwarf = 9;

    if (skill == "Sword" && mawClassLine(character.className) == "seraphim")
    {
        wield.twoHanded = false;
        wield.offHand = false;
    }
    else if (skill == "Axe" && (character.raceId == Dwarf || character.raceId == Minotaur))
    {
        if (!wield.twoHanded)
        {
            wield.offHand = axe >= SkillMastery::Expert;
        }
        else if (character.raceId == Minotaur)
        {
            wield.twoHanded = false;
            wield.offHand = axe >= SkillMastery::Master;
        }
    }

    return wield;
}

int MawItemRules::levelRequirement(const ItemDefinition &itemDefinition, const ItemRulesetFields &fields) const
{
    const MawBaseItem *pBase = m_rules.itemData().baseItem(itemDefinition.itemId);

    if (pBase == nullptr)
    {
        return 0;
    }

    if (MawRarity(fields.lootRarity) == MawRarity::Celestial)
    {
        return 1;
    }

    const MawModelConfig config = mawModelConfig(m_rules.options(), 5);
    MawLevelRequirementRules rules;
    rules.nightmare = config.difficulty >= 6;
    rules.doom = config.doomMode;
    rules.insanity = config.insanityMode;
    return mawLevelRequirement(fields.dropLevel, pBase->rung, rules);
}

double MawItemRules::fullValue(
    const InventoryItem &item,
    const ItemDefinition &itemDefinition,
    const MawBaseItem &,
    const SpecialItemEnchantTable *pSpecialTable) const
{
    MawValueInputs inputs;
    inputs.baseValue = itemDefinition.value;
    inputs.itemPower = item.rulesetFields.itemPower;
    inputs.enchant1Type = item.standardEnchantId;
    inputs.enchant1Strength = item.standardEnchantPower;
    inputs.enchant2Type = item.rulesetFields.secondStandardEnchantId;
    inputs.enchant2Strength = item.rulesetFields.secondStandardEnchantPower;
    inputs.legendary = item.rulesetFields.legendaryAffixId != 0;

    if (item.specialEnchantId != 0 && pSpecialTable != nullptr)
    {
        if (const SpecialItemEnchantEntry *pEntry = pSpecialTable->get(item.specialEnchantId))
        {
            inputs.specialValue = pEntry->priceModifier.amount;
            inputs.specialScales = mawSpecialStats(item.specialEnchantId) != nullptr;
        }
    }

    return mawItemValue(inputs);
}

int MawItemRules::itemValue(
    const InventoryItem &item,
    const ItemDefinition &itemDefinition,
    const StandardItemEnchantTable *pStandardTable,
    const SpecialItemEnchantTable *pSpecialTable,
    int minimumValue) const
{
    const MawBaseItem *pBase = m_rules.itemData().baseItem(itemDefinition.itemId);

    // A sealed spellbook is worth its book.
    if (const ItemDefinition *pBook = sealedBookSchool(item) > 0 && m_rules.itemTable() != nullptr
                ? m_rules.itemTable()->get(item.rulesetFields.craftState)
                : nullptr;
        pBook != nullptr)
    {
        InventoryItem book = item;
        book.objectDescriptionId = pBook->itemId;
        book.rulesetFields.craftState = 0;
        return ItemRules::itemValue(book, *pBook, pStandardTable, pSpecialTable, minimumValue);
    }

    if (pBase == nullptr || item.temporaryBonusRemainingSeconds > 0.0f)
    {
        return ItemRules::itemValue(item, itemDefinition, pStandardTable, pSpecialTable, minimumValue);
    }

    return std::max(minimumValue, mawRoundPrice(fullValue(item, itemDefinition, *pBase, pSpecialTable) * SellShare));
}

int MawItemRules::shopBuyValue(
    const InventoryItem &item,
    const ItemDefinition &itemDefinition,
    const StandardItemEnchantTable *pStandardTable,
    const SpecialItemEnchantTable *pSpecialTable) const
{
    const MawBaseItem *pBase = m_rules.itemData().baseItem(itemDefinition.itemId);
    const MawCraftingData &crafting = m_rules.craftingData();

    // Road to Insanity: spellbooks cost 5, 10 or 20 times as much in shops from the 5th, 8th and 11th of their school
    // (zzMaw-Items.lua:2306-2324).
    if (const int tier = spellbookTier(itemDefinition.itemId);
        tier > 0 && mawModelConfig(m_rules.options(), 5).insanityMode)
    {
        const int multiplier = tier == 11 ? 20 : tier >= 8 ? 10 : tier >= 5 ? 5 : 1;
        return ItemRules::shopBuyValue(item, itemDefinition, pStandardTable, pSpecialTable) * multiplier;
    }

    // Crafting materials have buy prices of their own (reagentPrices).
    if (const int tier = crafting.gemTier(itemDefinition.itemId); tier > 0)
    {
        return crafting.gemShopPrice(tier);
    }

    if (const MawCraftMaterial *pMaterial = crafting.material(itemDefinition.itemId);
        pMaterial != nullptr && pMaterial->shopPrice > 0)
    {
        return pMaterial->shopPrice;
    }

    if (pBase == nullptr)
    {
        return ItemRules::shopBuyValue(item, itemDefinition, pStandardTable, pSpecialTable);
    }

    const int enchantCount = (item.standardEnchantId != 0 ? 1 : 0)
        + (item.rulesetFields.secondStandardEnchantId != 0 ? 1 : 0) + (item.specialEnchantId != 0 ? 1 : 0);
    const MawRarity rarity = MawRarity(item.rulesetFields.lootRarity);
    const bool ancientTier = rarity == MawRarity::Ancient || rarity == MawRarity::Primordial;
    return std::max(1, mawRoundPrice(mawShopBuyValue(
        fullValue(item, itemDefinition, *pBase, pSpecialTable), enchantCount, ancientTier)));
}

std::string MawItemRules::displayName(
    const InventoryItem &item,
    const ItemDefinition &itemDefinition,
    const StandardItemEnchantTable *pStandardTable,
    const SpecialItemEnchantTable *pSpecialTable) const
{
    // Austerity renames the potions it takes out of the recipes, without blocking them (zzAlchemy.lua:22-36).
    const uint32_t itemId = itemDefinition.itemId;

    if (m_rules.options().challengeMode == RulesetChallengeMode::Austerity
        && ((itemId >= 232 && itemId <= 237) || (itemId >= 252 && itemId <= 256) || (itemId >= 261 && itemId <= 263)))
    {
        return "Potion Deleted in Austerity";
    }

    // A dimension map is named after its map (Tooltip.lua tooltipMapLevel).
    if (const MapStatsEntry *pMap = dimensionMapTarget(item))
    {
        return pMap->name + " Map";
    }

    if (m_rules.itemData().baseItem(itemDefinition.itemId) == nullptr)
    {
        return ItemRules::displayName(item, itemDefinition, pStandardTable, pSpecialTable);
    }

    // The special's name wins over the base enchantment's suffix.
    InventoryItem named = item;

    if (named.specialEnchantId != 0)
    {
        named.standardEnchantId = 0;
    }

    std::string name = ItemRuntime::identifiedDisplayName(named, itemDefinition, pStandardTable, pSpecialTable);
    const MawRarity rarity = MawRarity(item.rulesetFields.lootRarity);

    if (rarity >= MawRarity::Ancient)
    {
        name = std::string(mawRarityName(rarity)) + " " + name;
    }

    return name;
}

std::string MawItemRules::enchantDescription(
    const InventoryItem &storedItem,
    const ItemDefinition &itemDefinition,
    const StandardItemEnchantTable *pStandardTable,
    const SpecialItemEnchantTable *pSpecialTable,
    const Character *pViewer) const
{
    const InventoryItem item =
        pViewer != nullptr ? celestialAtLevel(storedItem, itemDefinition, int(pViewer->level)) : storedItem;

    if (m_rules.itemData().baseItem(itemDefinition.itemId) == nullptr)
    {
        return ItemRules::enchantDescription(item, itemDefinition, pStandardTable, pSpecialTable, pViewer);
    }

    // A damage enchantment shows the range it rolls at the item's level; stat, school and Meditation specials their
    // numbers at the item's power (checktext, IT:1801-1890).
    const int itemPower = item.rulesetFields.itemPower;

    if (const MawDamageEnchant *pEnchant = mawDamageEnchant(item.specialEnchantId))
    {
        const MawEnchantRange range = mawEnchantDamageRange(
            m_rules.model(1).weaponLevelDamage(itemPower * 5.0, isTwoHanded(itemDefinition), 0),
            pEnchant->minimum, pEnchant->maximum, pEnchant->coefficient, isTwoHanded(itemDefinition));
        // The viewer's Legendary 19 is in the range (GetLegendary19Mult, IT:1817-1826).
        const double legendary = pViewer != nullptr && mawWearsLegendaryAffix(*pViewer, 19) ? 1.5 : 1;
        const int low = int(std::floor(range.minimum * legendary));
        const int high = int(std::floor(range.maximum * legendary));
        const std::string amount = std::to_string(low) + (high != low ? "-" + std::to_string(high) : std::string());
        const char *pKind = pEnchant->type == CombatDamageType::Water ? "Cold"
            : pEnchant->type == CombatDamageType::Air                ? "Electrical"
            : pEnchant->type == CombatDamageType::Body               ? "Body"
                                                                      : "Fire";

        if (pEnchant->spellOnly)
        {
            return "Adds " + amount + " to spell damage and +" + std::to_string(mawSpecialStatAmount(39, 0, itemPower))
                + " Intellect and personality.";
        }

        if (pEnchant->weaponOnly)
        {
            return "Adds " + amount + " points of Fire damage to "
                + (itemDefinition.equipStat == "Missile" ? "Bow" : "Melee") + " attacks and +"
                + std::to_string(mawSpecialStatAmount(46, 0, itemPower)) + " Might.";
        }

        return "Adds " + amount + " points of " + pKind + " damage.";
    }

    if (const std::optional<std::string> text = mawSpecialText(item.specialEnchantId, itemPower))
    {
        return *text;
    }

    InventoryItem special = item;
    special.standardEnchantId = 0;
    return ItemEnchantRuntime::buildEnchantDescription(special, pStandardTable, pSpecialTable);
}

bool MawItemRules::glowsItemRarity() const
{
    return true;
}

bool MawItemRules::inventorySearch() const
{
    return true;
}

std::optional<uint32_t> MawItemRules::nameColor(const InventoryItem &item) const
{
    switch (MawRarity(item.rulesetFields.lootRarity))
    {
        case MawRarity::Uncommon:
            return 0x1eff00;
        case MawRarity::Rare:
            return 0x0096ff;
        case MawRarity::Epic:
            return 0xa335ee;
        case MawRarity::Ancient:
            return 0xff8000;
        case MawRarity::Primordial:
            return 0xff3232;
        case MawRarity::Legendary:
            return 0xffff1e;
        case MawRarity::Celestial:
            return 0x78f0ff;
        default:
            return std::nullopt;
    }
}

std::string MawItemRules::enchantLine(
    int type,
    int power,
    bool first,
    const ItemDefinition &itemDefinition,
    const StandardItemEnchantTable *pStandardTable,
    const Character *pViewer) const
{
    const MawBaseItem *pBase = m_rules.itemData().baseItem(itemDefinition.itemId);

    if (pBase == nullptr)
    {
        return mawEnchantStatName(pStandardTable, type) + " +" + std::to_string(power);
    }

    const bool ring = itemDefinition.equipStat == "Ring";

    // A resistance shows the share of damage it stops: (roll + 10, half on rings) as 1 - 1 / (1 + p / 100), the
    // viewer's Legendary 16 in it (resistancePercent, Tooltip.lua:20-22, 262-293).
    if (isResistanceEnchant(type))
    {
        double points = isHat(itemDefinition, *pBase) ? std::ceil(power * 1.5) : power;
        points *= pViewer != nullptr && mawWearsLegendaryAffix(*pViewer, 16) ? 1.5 : 1;
        points = (points + 10) * (ring ? 0.5 : 1);
        const double percent = mawRound((1 - 1 / (points / 100 + 1)) * 1000) / 10;
        std::ostringstream text;
        text << mawEnchantStatName(pStandardTable, type) << " +" << percent << "%";
        return text.str();
    }

    const int shown = readEnchantment(type, power, first, itemDefinition, *pBase, ring);
    return mawEnchantStatName(pStandardTable, type) + " +" + std::to_string(shown);
}

std::vector<ItemInspectLine> MawItemRules::inspectLines(
    const InventoryItem &storedItem,
    const ItemDefinition &itemDefinition,
    const StandardItemEnchantTable *pStandardTable,
    const SpecialItemEnchantTable *pSpecialTable,
    const Character *pViewer) const
{
    // A Celestial item reads at the viewer's level (Tooltip.lua:205).
    const InventoryItem item =
        pViewer != nullptr ? celestialAtLevel(storedItem, itemDefinition, int(pViewer->level)) : storedItem;
    std::vector<ItemInspectLine> lines;
    const MawItemData &data = m_rules.itemData();
    const MawBaseItem *pBase = data.baseItem(itemDefinition.itemId);
    const ItemRulesetFields &fields = item.rulesetFields;

    // A dimension map: its level, what its affixes add to loot and density, then the affixes, the locked ones grey.
    if (const MapStatsEntry *pMap = dimensionMapTarget(item))
    {
        const MawDimensionData &dimension = m_rules.dimensionData();
        const MawDimensionMap map = MawDimensionMap::fromFields(fields);
        const double strength = mawDimensionStrength(map.power, map.activeAffixCount());
        lines.push_back({"Map Level: "
                + std::to_string(mawDimensionMapLevel(map.power, m_rules.mapLevels().band(pMap->fileName))),
            0xffffff});
        lines.push_back({"+" + std::to_string(int(mawRound(strength / 8 * 1.5))) + "% craft items drop chances",
            0x007fff});
        lines.push_back({"+" + std::to_string(int(mawRound(strength / 4))) + "% item quality", 0x007fff});
        lines.push_back({"+" + std::to_string(int(mawRound(strength / 3))) + "% monster density", 0x007fff});
        const std::array<uint8_t, 4> active = map.activeAffixes();

        for (size_t slot = 0; slot < map.affixes.size(); ++slot)
        {
            if (map.affixes[slot] != 0)
            {
                lines.push_back({"- " + dimension.affixLine(map.affixes[slot], map.power),
                    active[slot] != 0 ? 0xffff99u : 0x646464u});
            }
        }

        return lines;
    }

    // A reagent's power from its item level (Tooltip.lua:135-138).
    if (itemDefinition.equipStat == "Reagent" && fields.dropLevel > 0)
    {
        const int power =
            mawReagentBasePower(InventoryItemMixingRuntime::reagentPower(itemDefinition), fields.dropLevel);
        lines.push_back({"Power: " + std::to_string(power), 0xffffff});
        return lines;
    }

    // An artifact shows what it gives at the party's level, then its powers (Tooltip.lua:495-534, Artifacts.lua
    // BonusesOf, zzzMaw_Artifacts.lua MawArtifactOnHitText; audit FITM-2-5).
    if (const MawArtifact *pArtifact = data.artifact(itemDefinition.itemId))
    {
        const MawArtifactBonuses bonuses = artifactBonuses(*pArtifact, itemDefinition);

        for (const std::vector<std::pair<int, int>> *pStats : {&bonuses.stats, &bonuses.flat})
        {
            for (const auto &[type, amount] : *pStats)
            {
                // MAW's immunity value reads as such (Tooltip.lua tooltipArtifactScaling).
                if (amount >= 65000)
                {
                    lines.push_back({mawEnchantStatName(pStandardTable, type) + ": Immune", 0x96c8ffu});
                }
                else if (amount != 0)
                {
                    lines.push_back({mawEnchantStatName(pStandardTable, type) + (amount > 0 ? " +" : " ")
                            + std::to_string(amount),
                        amount > 0 ? 0x96c8ffu : 0xff6464u});
                }
            }
        }

        for (const auto &[skill, amount] : bonuses.skills)
        {
            if (amount != 0)
            {
                lines.push_back({displaySkillName(skill) + (amount > 0 ? " +" : " ") + std::to_string(amount),
                    amount > 0 ? 0x96c8ffu : 0xff6464u});
            }
        }

        if (!pArtifact->onHitType.empty())
        {
            lines.push_back({pArtifact->onHitType + " damage on hit" + (pArtifact->onHitSlow ? ", slows" : ""),
                0xffbe5a});
        }

        for (const auto &[kind, factor] : pArtifact->onHitVersus)
        {
            std::ostringstream text;
            text << "x" << factor << " damage vs " << kind;
            lines.push_back({text.str(), 0xffbe5a});
        }

        for (const std::string &school : pArtifact->spellBonus)
        {
            lines.push_back({"+50% skill in " + displaySkillName(school), 0x96c8ff});
        }

        // Its lasting powers (MawArtifactOnHitText, zzzMaw_Artifacts.lua:410-460): read off what wearing it does.
        for (const std::string &power : artifactPowerLines(itemDefinition, pStandardTable, pSpecialTable))
        {
            lines.push_back({power, 0x96c8ff});
        }

        if (mawRegenerationArtifact(itemDefinition.itemId, false))
        {
            lines.push_back({"Regenerates Hit Points", 0x96c8ff});
        }

        if (mawRegenerationArtifact(itemDefinition.itemId, true))
        {
            lines.push_back({"Regenerates Spell Points", 0x96c8ff});
        }

        if (pArtifact->attackDelayMultiplier < 1)
        {
            lines.push_back({"Swift", 0x96c8ff});
        }

        // Who may wear it (artifactWearReq), red when the viewer may not.
        if (const std::optional<std::string> requirement = ItemRuntime::wearRequirementText(itemDefinition))
        {
            const bool barred = pViewer != nullptr
                && (!ItemRuntime::characterMeetsClassRestriction(*pViewer, itemDefinition)
                    || !ItemRuntime::characterMeetsRaceRestriction(*pViewer, itemDefinition));
            lines.push_back({*requirement, barred ? 0xff3232u : 0xffbe5au});
        }

        lines.push_back({"Artifact level: " + std::to_string(int(mawRound(m_rules.state().totalLevel()))), 0x78f0ff});
        return lines;
    }

    if (pBase == nullptr)
    {
        return lines;
    }

    if (item.identified)
    {
        const auto addEnchant = [&](int type, int power, bool first)
        {
            if (type != 0)
            {
                lines.push_back(
                    {enchantLine(type, power, first, itemDefinition, pStandardTable, pViewer), 0x96c8ff});
            }
        };

        addEnchant(fields.secondStandardEnchantId, fields.secondStandardEnchantPower, false);
        addEnchant(item.standardEnchantId, item.standardEnchantPower, true);

        if (fields.legendaryAffixId != 0)
        {
            lines.push_back({data.legendaryAffixText(fields.legendaryAffixId), 0xffff1e});
            const int nearby = m_rules.nearbyMonsters();

            // Legendaries 21 and 22 with the monsters near the party now (Tooltip.lua:399-422).
            if (fields.legendaryAffixId == 21)
            {
                lines.push_back({"Current bonus Damage: " + std::to_string(std::min(nearby * 5, 100)) + "%", 0xffff1e});
            }
            else if (fields.legendaryAffixId == 22)
            {
                std::ostringstream text;
                text << "Current Reduction: " << mawRound(std::min(1 - std::pow(0.97, nearby), 0.5) * 10000) / 100
                     << "%";
                lines.push_back({text.str(), 0xffff1e});
            }
        }

        if (MawRarity(fields.lootRarity) == MawRarity::Celestial)
        {
            const bool madness = m_rules.options().challengeMode == RulesetChallengeMode::BeyondMadness;
            lines.push_back({"Grows with its wearer up to level "
                    + std::to_string(madness ? MadnessCelestialLevelCap : CelestialLevelCap),
                0x78f0ff});
        }
    }

    if (isWeapon(itemDefinition))
    {
        const std::string skill = canonicalSkillName(itemDefinition.skillGroup);
        const bool twoHanded = pBase->twoHanded;
        lines.push_back({"Attack speed: " + formatSpeed(mawItemRecovery(weaponBaseRecovery(skill),
                    fields.itemPower * 5, twoHanded)),
            0xffffff});
    }

    if (fields.qualityPercent > 0)
    {
        lines.push_back({"Quality bonus: +" + std::to_string(fields.qualityPercent) + "%", 0xffbe5a});
    }

    // The held auras on a weapon in the viewer's hands (tooltipFireAura).
    if (isWeapon(itemDefinition) && pViewer != nullptr)
    {
        if (const std::optional<MawAuraSource> fire = m_rules.memberAura(4, *pViewer))
        {
            static const std::array<const char *, 5> Names = {"", "Fire", "Flame", "Inferno", "Hell"};
            const int damage = mawFireAuraOnWeapon(m_rules, *pViewer, itemDefinition, item);
            lines.push_back({std::string(Names[size_t(std::clamp(int(fire->mastery), 0, 4))]) + " Aura: adds "
                    + std::to_string(damage) + " Fire Damage to any attack",
                0xffff99});
        }

        if (m_rules.memberAura(91, *pViewer))
        {
            lines.push_back({"Vampiric Aura: damage done will restore player HP.", 0xffff99});
        }
    }

    lines.push_back({"Item level: " + std::to_string(fields.itemPower * 5), 0xc8c8c8});
    const int requiredLevel = levelRequirement(itemDefinition, fields);

    if (requiredLevel > 1)
    {
        const bool tooLow = pViewer != nullptr && int(pViewer->level) < requiredLevel;
        lines.push_back({"Level required: " + std::to_string(requiredLevel), tooLow ? 0xff3232u : 0xffffffu});
    }

    return lines;
}

std::optional<int> MawItemRules::merchantValue(const Character &member) const
{
    const CharacterSkill *pSkill = member.findSkill("Merchant");
    const int mastery = pSkill != nullptr ? int(pSkill->mastery) : 0;
    const int level = pSkill != nullptr ? int(pSkill->level) + member.skillBonus("Merchant") : 0;
    // The member's Glamour adds mastery x power; a Grandmaster Glamour trades at cost.
    const int glamour = member.glamourMastery == SkillMastery::Grandmaster
        ? 100
        : int(member.glamourMastery) * member.glamourPower;
    const int total = level * mastery + std::max(0, member.merchantBonus - member.glamourPower) + glamour;
    const int value = total > 0 && (mastery == int(SkillMastery::Grandmaster) || total >= 45) ? 100 : total;
    return std::min(7 + value, 100);
}

std::optional<int> MawItemRules::shopRerollCost(const Party &, const HouseEntry &house) const
{
    if (house.type != "Weapon Shop" && house.type != "Armor Shop" && house.type != "Magic Shop")
    {
        return std::nullopt;
    }

    // MMMerge's continents: Jadame (MM8) 1, Antagarich (MM7) 2, Enroth (MM6) 3.
    const uint32_t continent = house.worldId == "mm7" ? 2 : house.worldId == "mm6" ? 3 : 1;
    const MawGameState &state = m_rules.state();
    const double ownLevel = state.continentLevels[MawGameState::continentIndex(continent)];
    const double partyLevel = state.levelOutside(4) - std::min(ownLevel / 2, 54.0);
    const int strength = std::min(int(ownLevel / 18) + 2, 5);
    const int tier = int(std::floor(std::max(0.0, partyLevel) / 15)) + strength;
    return tier * tier * 250;
}

void MawItemRules::adjustShopStock(
    std::vector<InventoryItem> &stock,
    const HouseEntry &house,
    const Party &party,
    const ItemTable &itemTable,
    std::mt19937 &rng) const
{
    const MawCraftingData &crafting = m_rules.craftingData();

    if ((house.type != "Magic Shop" && house.type != "Alchemist") || crafting.gemTiers() <= 0
        || m_rules.lootConfig().austerity)
    {
        return;
    }

    std::vector<uint32_t> specials;
    std::vector<int> weights;

    for (const auto &[itemId, material] : crafting.materials())
    {
        if (material.shopWeight > 0)
        {
            specials.push_back(itemId);
        }
    }

    std::sort(specials.begin(), specials.end());

    for (uint32_t itemId : specials)
    {
        weights.push_back(crafting.material(itemId)->shopWeight);
    }

    const double specialChance =
        std::min(std::pow(std::max(0, party.gold()) / crafting.shopSpecialGold(), 0.7), 1.0);
    const std::vector<double> &bonusWeights = crafting.shopGemTierBonusWeights();
    const double bankedLevel = m_rules.state().levelOutside(4);

    for (InventoryItem &item : stock)
    {
        const ItemDefinition *pDefinition = itemTable.get(item.objectDescriptionId);

        // The alchemist's row of empty bottles is the guaranteed native stock; only the random slots are swapped.
        if (pDefinition == nullptr || ItemEnchantRuntime::categoryForItem(*pDefinition) != ItemEnchantCategory::None
            || (house.type == "Alchemist" && item.objectDescriptionId == PotionBottleItemId))
        {
            continue;
        }

        if (pDefinition->equipStat != "Gem" && unitDraw(rng) >= crafting.shopReplaceChance())
        {
            continue;
        }

        uint32_t replacement = 0;

        if (!specials.empty() && unitDraw(rng) < specialChance)
        {
            std::discrete_distribution<size_t> pick(weights.begin(), weights.end());
            replacement = specials[pick(rng)];
        }
        else
        {
            std::discrete_distribution<size_t> bonus(bonusWeights.begin(), bonusWeights.end());
            const int tier = 1 + std::min(int(std::floor(bankedLevel / 25)) + int(bonus(rng)),
                crafting.gemDropMaxTier() - 1);
            replacement = crafting.gemItemId(tier);
        }

        if (itemTable.get(replacement) != nullptr)
        {
            item = ItemGenerator::makeInventoryItem(replacement, itemTable, ItemGenerationMode::Shop);
        }
    }
}

const MapStatsEntry *MawItemRules::dimensionMapTarget(const InventoryItem &item) const
{
    const uint32_t mapItemId = m_rules.dimensionData().mapItemId();

    if (mapItemId == 0 || item.objectDescriptionId != mapItemId || m_rules.mapTable() == nullptr)
    {
        return nullptr;
    }

    return m_rules.mapTable()->findById(item.rulesetFields.dimensionMapId);
}

std::optional<std::string> MawItemRules::useTravelItem(Party &, const InventoryItem &item) const
{
    const MapStatsEntry *pMap = dimensionMapTarget(item);

    if (pMap == nullptr)
    {
        return std::nullopt;
    }

    // Seeded by the map's own fields, so the same map always brings the same families (UseMouseItem).
    const MawDimensionData &data = m_rules.dimensionData();
    const MawDimensionMap map = MawDimensionMap::fromFields(item.rulesetFields);
    const ItemRulesetFields &fields = item.rulesetFields;
    RandomStream stream(randomStreamKey(m_rules.randomRootSeed(), RandomDomain::Dimension, map.mapId,
        uint64_t(fields.dimensionAffixes[0]) | uint64_t(fields.dimensionAffixes[1]) << 8
            | uint64_t(fields.dimensionAffixes[2]) << 16 | uint64_t(fields.dimensionAffixes[3]) << 24,
        uint64_t(map.power) | uint64_t(map.activeSlots) << 8));
    std::string mapFileName = pMap->fileName;
    std::transform(mapFileName.begin(), mapFileName.end(), mapFileName.begin(),
        [](unsigned char character) { return char(std::tolower(character)); });
    const std::vector<int16_t> &families = data.families(mapFileName.ends_with(".blv"));
    MawDimensionRun run;
    run.affixes = map.activeAffixes();
    run.power = map.power;
    run.entering = true;

    for (int16_t &family : run.families)
    {
        family = families[stream.uniform(0, uint32_t(families.size() - 1))];
    }

    const MawDimensionQuest &quest = m_rules.state().dimensionQuest;

    if (quest.mapGiven && !quest.cleared)
    {
        run.questTier = quest.tierLevel;
    }

    m_rules.state().dimensionRuns[mapFileName] = run;
    return pMap->fileName;
}

const RulesetLootFilter *MawItemRules::lootFilter() const
{
    return &m_rules.options().preferences.lootFilter;
}

std::optional<LootFilterFacts> MawItemRules::lootFilterFacts(
    const InventoryItem &item,
    const ItemDefinition &itemDefinition) const
{
    // Items without a price (the blasters, Wetsuit, quest artifacts) are never filtered; MAW's chest filter sold the
    // Control Center's blasters for nothing (DEVIATIONS 182).
    if (itemDefinition.value <= 0)
    {
        return std::nullopt;
    }

    const std::string &stat = itemDefinition.equipStat;
    LootFilterFacts facts;

    if (stat == "Weapon" || stat == "Weapon2" || stat == "Weapon1or2" || stat == "Missile")
    {
        facts.group = LootFilterGroup::Weapons;
    }
    else if (stat == "Armor" || stat == "Shield" || stat == "Helm" || stat == "Belt" || stat == "Cloak"
        || stat == "Gauntlets" || stat == "Boots")
    {
        facts.group = LootFilterGroup::Armour;
    }
    else if (stat == "Ring" || stat == "Amulet")
    {
        facts.group = LootFilterGroup::Jewellery;
    }
    else if (stat == "WeaponW")
    {
        facts.kind = RulesetLootKind::Wands;
    }
    else if (stat == "Sscroll")
    {
        facts.kind = RulesetLootKind::Scrolls;
    }
    else if (stat == "Bottle")
    {
        facts.kind = RulesetLootKind::Potions;
    }
    else if (stat == "Reagent" || stat == "Herb")
    {
        facts.kind = RulesetLootKind::Reagents;
    }
    else if (stat == "Gem")
    {
        facts.kind = RulesetLootKind::Gems;
    }
    else
    {
        // Spellbooks, quest items, letters and the rest are never filtered.
        return std::nullopt;
    }

    MawRarity rarity = MawRarity(item.rulesetFields.lootRarity);
    const uint32_t id = item.objectDescriptionId;
    const bool baseItem = (id >= 1 && id <= 151) || (id >= 803 && id <= 936) || (id >= 1603 && id <= 1736);

    // An equipment item MAW never rolled (placed in a chest) ranks as Common plus one tier per enchantment (IT:933-944).
    if (rarity == MawRarity::None && baseItem)
    {
        rarity = MawRarity(1 + (item.standardEnchantId != 0 ? 1 : 0) + (item.specialEnchantId != 0 ? 1 : 0)
            + (item.rulesetFields.secondStandardEnchantId != 0 ? 1 : 0));
    }

    facts.rarity = std::min(int(rarity), LootFilterRarityCount);
    facts.itemLevel = item.rulesetFields.dropLevel;
    facts.alwaysKept = rarity >= MawRarity::Legendary || item.rulesetFields.legendaryAffixId != 0
        || itemDefinition.rarity == ItemRarity::Artifact || itemDefinition.rarity == ItemRarity::Relic;
    return facts;
}

RecentLootDrops *MawItemRules::recentLootDrops() const
{
    return &m_recentLootDrops;
}

int MawItemRules::filteredLootGold(
    const InventoryItem &item,
    const ItemDefinition &itemDefinition,
    const StandardItemEnchantTable *pStandardTable,
    const SpecialItemEnchantTable *pSpecialTable) const
{
    return itemValue(item, itemDefinition, pStandardTable, pSpecialTable, 0);
}

std::optional<uint32_t> MawItemRules::chestGoldAmount(int pileSize, std::mt19937 &rng) const
{
    const MapStats *pMapTable = m_rules.mapTable();
    const MapStatsEntry *pMap = pMapTable != nullptr ? pMapTable->findByFileName(m_rules.currentMap()) : nullptr;

    if (pMap == nullptr)
    {
        return std::nullopt;
    }

    // 10 x (the band's mean + the map's bolster) x 1, 2 or 4 by the pile's size x 0.66-1.32 (IT:903-927).
    const std::array<double, 3> band = m_rules.mapLevels().band(m_rules.currentMap());
    const double mapLevel = (band[0] + band[1] + band[2]) / 3;
    const double sizeFactor = pileSize <= 0 ? 1 : pileSize == 1 ? 2 : 4;
    const double draw = std::uniform_real_distribution<double>(0.66, 1.32)(rng);
    return uint32_t(std::max(1.0, 10 * (mapLevel + m_rules.mapBolster(*pMap)) * sizeFactor * draw));
}

uint32_t MawItemRules::placedItemId(uint32_t itemId, std::mt19937 &rng) const
{
    // MAW removed these potions; a map that places one gets a random black potion (IT:4449-4465).
    if (itemId >= 264 && itemId <= 289)
    {
        return uint32_t(std::uniform_int_distribution<int>(252, 263)(rng));
    }

    return itemId;
}

int MawItemRules::bagCount(const Party &party) const
{
    // Four bags a character (the user's inventory design of 2026-10-25), and five tabs of four for a party of one
    // (user, 2026-11-04; MAW has five bags, and five tabs of five alone: DEVIATIONS 141). A member who joins someone
    // keeps the other tabs' items until alone again.
    return party.members().size() == 1 ? 5 * InventoryBags::TabBags : InventoryBags::TabBags;
}

std::optional<LootGathering> MawItemRules::lootGathering() const
{
    return LootGathering{30, 30};
}

bool MawItemRules::gathersItem(const InventoryItem &item) const
{
    constexpr uint32_t DimensionMapItemId = 290;
    return (item.objectDescriptionId >= 1041 && item.objectDescriptionId <= 1070)
        || item.objectDescriptionId == DimensionMapItemId;
}

std::optional<BagTag> MawItemRules::bagTag(const ItemDefinition &definition) const
{
    if (definition.itemId >= 1041 && definition.itemId <= 1070)
    {
        return BagTag::Crafting;
    }

    // MM6's reagents are herbs (1762-1764).
    if (definition.equipStat == "Bottle" || definition.equipStat == "Reagent" || definition.equipStat == "Herb")
    {
        return BagTag::Alchemy;
    }

    return std::nullopt;
}

std::optional<std::string> MawItemRules::chestOpenRefusal(const Party &party, int mapLock) const
{
    if (!mawModelConfig(m_rules.options(), 5).doomMode)
    {
        return std::nullopt;
    }

    const int required = mapLock >= 4 ? mapLock * 2 : mapLock;

    for (const Character &member : party.members())
    {
        const CharacterSkill *pSkill = member.findSkill("DisarmTraps");
        const int mastery = pSkill != nullptr ? int(pSkill->mastery) : 0;
        const int level = (pSkill != nullptr ? int(pSkill->level) : 0) + member.skillBonus("DisarmTraps");

        if (mastery >= int(SkillMastery::Grandmaster) || level * mastery >= required)
        {
            return std::nullopt;
        }
    }

    return "Not enough disarm skill";
}

std::optional<std::string> MawItemRules::wearRefusal(const InventoryItem &item) const
{
    return mawModelConfig(m_rules.options(), 5).doomMode && !item.identified
        ? std::optional<std::string>("Identify the item first")
        : std::nullopt;
}

float MawItemRules::shopServiceMultiplier(const ItemDefinition &itemDefinition, bool identify, float houseMultiplier) const
{
    if (!mawModelConfig(m_rules.options(), 5).doomMode)
    {
        return houseMultiplier;
    }

    const int difficulty = std::atoi(itemDefinition.idRepSt.c_str());
    return identify ? float(difficulty * difficulty) : 5.0f;
}

std::optional<size_t> MawItemRules::alchemist(const Party &party) const
{
    const int32_t member = m_rules.state().alchemistMember;
    return member >= 0 && size_t(member) < party.members().size() ? std::optional<size_t>(size_t(member))
                                                                   : std::nullopt;
}

std::optional<std::string> MawItemRules::pickAlchemist(Party &party, size_t memberIndex) const
{
    const Character *pMember = party.member(memberIndex);

    if (pMember == nullptr)
    {
        return std::nullopt;
    }

    int32_t &alchemistMember = m_rules.state().alchemistMember;

    if (alchemist(party) == memberIndex)
    {
        alchemistMember = -1;
        return "No alchemy preference when sorting";
    }

    alchemistMember = int32_t(memberIndex);
    return pMember->name + " will now take alchemy items when sorting";
}

std::optional<int> MawItemRules::alchemySortRank(const InventoryItem &item) const
{
    // MAW's alchemyItemsOrder: reagents of each potion tier beside their MM7 copies, then the crafting items.
    static constexpr std::array<uint16_t, 73> AlchemyItemsOrder = {
        200, 1002, 1764, 201, 1003, 202, 1004, 203, 1005, 204, 1006,
        205, 1007, 1763, 206, 1008, 207, 1009, 208, 1010, 209, 1011,
        210, 1012, 1762, 211, 1013, 212, 1014, 213, 1015, 214, 1016,
        215, 1017, 216, 1018, 217, 1019, 218, 1020, 219, 1021,
        1069, 1068, 1064, 1067, 1065, 1063, 1070, 1066, 1061, 1062, 1060, 1059, 1058, 1057, 1056, 1055, 1054, 1053,
        1052, 1051, 1050, 1049, 1048, 1047, 1046, 1045, 1044, 1043, 1042, 1041};
    const uint32_t itemId = item.objectDescriptionId;

    // The potions lead, the highest id first.
    if (itemId >= 220 && itemId < 300)
    {
        return int(299 - itemId);
    }

    const auto found = std::find(AlchemyItemsOrder.begin(), AlchemyItemsOrder.end(), itemId);

    if (found == AlchemyItemsOrder.end())
    {
        return std::nullopt;
    }

    // An empty stateful material (1051-1060 with nothing stored) goes ten places later.
    int rank = 100 + int(found - AlchemyItemsOrder.begin());

    if (itemId > 1050 && itemId <= 1060 && item.rulesetFields.craftState == 0)
    {
        rank += 10;
    }

    return rank;
}

bool MawItemRules::openSealedItem(InventoryItem &item, const Character &reader) const
{
    const int school = sealedBookSchool(item);
    const ItemTable *pItemTable = m_rules.itemTable();
    const ItemDefinition *pBook =
        school > 0 && pItemTable != nullptr ? pItemTable->get(item.rulesetFields.craftState) : nullptr;

    if (pBook == nullptr)
    {
        return false;
    }

    const CharacterSkill *pSkill = reader.findSkill(std::string(SealedBookSchools[school - 1]) + "Magic");

    if (pSkill == nullptr || pSkill->mastery < sealedBookMastery(*pBook))
    {
        return false;
    }

    item.objectDescriptionId = pBook->itemId;
    item.rulesetFields.craftState = 0;
    return true;
}

std::vector<ItemInspectLine> MawItemRules::comparisonLines(
    const Party &party,
    size_t memberIndex,
    const InventoryItem &item,
    const ItemDefinition &itemDefinition) const
{
    static constexpr std::array<const char *, 12> Wearable = {
        "Weapon", "Weapon2", "Weapon1or2", "Missile", "Armor", "Shield", "Helm", "Belt", "Cloak", "Gauntlets", "Boots",
        "Ring"};
    const Character *pMember = party.member(memberIndex);

    if (pMember == nullptr || party.itemTable() == nullptr
        || std::find(Wearable.begin(), Wearable.end(), itemDefinition.equipStat) == Wearable.end())
    {
        return {};
    }

    if (m_lastComparison && m_lastComparison->item == item && m_lastComparison->memberIndex == memberIndex
        && m_lastComparison->equipment == pMember->equipment
        && m_lastComparison->equipmentRuntime == pMember->equipmentRuntime)
    {
        return m_lastComparison->lines;
    }

    m_lastComparison = Comparison{item, memberIndex, pMember->equipment, pMember->equipmentRuntime, {}};
    const std::optional<CharacterEquipPlan> plan = GameMechanics::resolveCharacterEquipPlan(
        *pMember, itemDefinition, party.itemTable(), nullptr, std::nullopt, false);

    // The party's numbers as worn and with the item worn instead: two copies of it, rebuilt alike.
    Party baseline = party;
    Party trial = party;

    if (!plan || !trial.replaceEquippedItem(memberIndex, plan->targetSlot, item))
    {
        return {};
    }

    baseline.refreshDerivedState();
    baseline.refreshMemberResources(memberIndex);
    trial.refreshMemberResources(memberIndex);
    const int partyCount = int(party.members().size());
    const auto report = [&](const Party &source)
    {
        return mawPowerReport(m_rules, *source.member(memberIndex), *source.itemTable(),
            source.standardItemEnchantTable(), source.specialItemEnchantTable(), partyCount);
    };
    const MawPowerReport before = report(baseline);
    const MawPowerReport after = report(trial);
    const double powerBefore = std::max({before.melee, before.ranged, before.spell});
    const double powerAfter = std::max({after.melee, after.ranged, after.spell});
    std::vector<ItemInspectLine> &lines = m_lastComparison->lines;
    const auto addLine = [&lines](const char *pName, double before, double after)
    {
        const double change = before > 0 ? mawRound((after / before - 1) * 10000) / 100 : 0;

        if (change == 0)
        {
            return;
        }

        std::ostringstream text;
        text << pName << ": " << (change > 0 ? "+" : "") << change << "%";
        lines.push_back({text.str(), change > 0 ? 0x00ff00u : 0xff0000u});
    };
    addLine("Power", powerBefore, powerAfter);
    addLine("Vitality", before.vitality, after.vitality);
    return lines;
}

std::optional<std::string> MawItemRules::itemDescription(const InventoryItem &item, const Character *pViewer) const
{
    const ItemTable *pItemTable = m_rules.itemTable();

    if (const int school = sealedBookSchool(item); school > 0 && pItemTable != nullptr)
    {
        const ItemDefinition *pSealed = pItemTable->get(item.objectDescriptionId);
        const ItemDefinition *pBook = pItemTable->get(item.rulesetFields.craftState);

        if (pSealed != nullptr && pBook != nullptr)
        {
            static constexpr std::array<const char *, 5> MasteryNames = {
                "", "Novice", "Expert", "Master", "Grandmaster"};
            return pSealed->notes + "\n\n\f63488You need at least "
                + MasteryNames[size_t(sealedBookMastery(*pBook))] + " skill in " + SealedBookSchools[school - 1]
                + " Magic to open the book\f00000";
        }
    }

    // An artifact's description without MMMerge's "(Special Powers: ...)" numbers and leading "(...)" summary, which
    // MAW's popup replaces with its own lines (Tooltip.lua:495-534, audit FITM-2-5).
    if (pItemTable != nullptr && m_rules.itemData().artifact(item.objectDescriptionId) != nullptr)
    {
        if (const ItemDefinition *pDefinition = pItemTable->get(item.objectDescriptionId))
        {
            return mawArtifactDescription(pDefinition->notes);
        }
    }

    const std::string *pText = m_rules.textData().findItemText(item.objectDescriptionId);

    if (pText == nullptr)
    {
        return m_rules.gameRules().crafting.materialDescription(item);
    }

    constexpr int PowerCap = 500;
    const int power = std::min(int(item.standardEnchantPower), PowerCap);
    const PotionRules &potions = m_rules.gameRules().potions;
    // A potion's copy of an aura: the buff's percent, the stat percent (Day of the Gods' wider one), the flat value.
    const auto auraPercent = [power](uint32_t spellId)
    {
        return mawRound(mawBuffMultiplier(int(spellId), mawPotionAuraSkill(spellId, power)) * 1000) / 10;
    };
    const int step = power / 50;
    const int bestStep = pViewer != nullptr && pViewer->rulesetState.potionSteps.contains(item.objectDescriptionId)
        ? pViewer->rulesetState.potionSteps.at(item.objectDescriptionId)
        : 0;
    const std::unordered_map<std::string, double> values = {
        {"heal_small", mawRound(20 + potions.estimatedPool(PotionPool::HitPoints, power) * 0.25)},
        {"mana_small", mawRound(10 + potions.estimatedPool(PotionPool::SpellPoints, power) * 0.25)},
        {"heal_large", mawRound(50 + potions.estimatedPool(PotionPool::HitPoints, power) * 0.35)},
        {"mana_large", mawRound(50 + potions.estimatedPool(PotionPool::SpellPoints, power) * 0.35)},
        {"haste", auraPercent(5)},
        {"heroism", auraPercent(51)},
        {"shield", auraPercent(17)},
        {"stat", mawRound(mawAuraStatPercent(mawPotionAuraSkill(46, power), false))},
        {"stat_light", mawRound(mawAuraStatPercent(mawPotionAuraSkill(83, power), true))},
        {"protection", mawRound(mawAuraFlat(20, 2, mawPotionAuraLevel(power), mawPotionAuraSkill(85, power) / 1.4))},
        {"meditation", std::ceil(std::sqrt(power) / 1.5) + 1},
        {"step", step},
        {"skill_points", 5 * step * step + 15 * step},
        {"best_step", bestStep},
        {"best_skill_points", 5 * bestStep * bestStep + 15 * bestStep},
    };
    return mawFillText(*pText, values);
}

void MawItemRules::trimMercenaryItem(InventoryItem &item, std::mt19937 &rng) const
{
    // A mercenary's gear is plain: MAW clears the bits that hold its rarity, legendary affix, Celestial status, drop
    // level and quality (BonusExpireTime = 0, NPCMercenaries.lua:348; SKL-4).
    item.rulesetFields.lootRarity = 0;
    item.rulesetFields.ancientTier = 0;
    item.rulesetFields.legendaryAffixId = 0;
    item.rulesetFields.dropLevel = 0;
    item.rulesetFields.qualityPercent = 0;

    if (item.specialEnchantId == 0 || item.rulesetFields.secondStandardEnchantId == 0)
    {
        return;
    }

    if (std::uniform_real_distribution<double>(0.0, 1.0)(rng) < 0.5)
    {
        item.specialEnchantId = 0;
    }
    else
    {
        item.rulesetFields.secondStandardEnchantId = 0;
        item.rulesetFields.secondStandardEnchantPower = 0;
    }
}

bool MawItemRules::canDropToWorld(const InventoryItem &item, const ItemDefinition &definition) const
{
    if (m_rules.options().challengeMode == RulesetChallengeMode::BeyondMadness
        && m_rules.dimensionData().mapItemId() != 0 && item.objectDescriptionId == m_rules.dimensionData().mapItemId())
    {
        return false;
    }

    return ItemRules::canDropToWorld(item, definition);
}
}
