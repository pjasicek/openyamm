#include "game/rules/maw/MawClassRules.h"

#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/gameplay/PartyHostileAlert.h"
#include "game/party/Party.h"
#include "game/party/SkillData.h"
#include "game/rules/CombatRules.h"
#include "game/rules/maw/MawClassSpells.h"
#include "game/rules/maw/MawCombatFormulas.h"
#include "game/rules/maw/MawItemRules.h"
#include "game/rules/maw/MawMonsterRules.h"
#include "game/rules/maw/MawPromotions.h"
#include "game/rules/maw/MawRules.h"
#include "game/rules/maw/MawSkillFormulas.h"
#include "game/tables/ClassMultiplierTable.h"
#include "game/tables/ClassSkillTable.h"

#include <functional>
#include <map>
#include <unordered_set>

#include <algorithm>
#include <array>
#include <cmath>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
std::pair<int, int> skillAndMastery(const Character &character, const char *pSkillName)
{
    const CharacterSkill *pSkill = character.findSkill(pSkillName);
    const int level = (pSkill != nullptr ? int(pSkill->level) : 0) + character.skillBonus(pSkillName);
    const int mastery = pSkill != nullptr ? int(pSkill->mastery) : 0;
    // Grandmaster counts as 5 for the flat HP and SP of Bodybuilding and Meditation.
    return {level, mastery >= 4 ? 5 : mastery};
}

// MAW's races (devdocs/maw/data/race_bonuses.yml); Dragon is mawIsDragon's.
enum Race : uint32_t
{
    Human = 0,
    Vampire = 1,
    DarkElf = 2,
    Minotaur = 3,
    Troll = 4,
    Dragon = 5,
    Undead = 6,
    Elf = 7,
    Goblin = 8,
    Dwarf = 9,
};

// The skills a race gets 3 levels in, and a tenth of the character's own level (S:2348-2400).
struct RaceSkills
{
    uint32_t race;
    std::array<const char *, 4> skills;
};

constexpr std::array<RaceSkills, 7> FlatSkillBonuses = {{
    {Human, {"LeatherArmor", "ChainArmor", "PlateArmor", "Shield"}},
    {DarkElf, {"Bow", "Spear", "Meditation", nullptr}},
    {Elf, {"Bow", "Spear", "Meditation", nullptr}},
    {Minotaur, {"Axe", nullptr, nullptr, nullptr}},
    {Troll, {"Regeneration", "Mace", "Staff", nullptr}},
    {Goblin, {"Sword", "Mace", "Dagger", "LeatherArmor"}},
    {Dwarf, {"Shield", "Bodybuilding", nullptr, nullptr}},
}};

struct RaceElement
{
    const char *pName;
    int CharacterResistanceSet::*pResistance;
};

constexpr RaceElement FireElement = {"Fire", &CharacterResistanceSet::fire};
constexpr RaceElement AirElement = {"Air", &CharacterResistanceSet::air};
constexpr RaceElement WaterElement = {"Water", &CharacterResistanceSet::water};
constexpr RaceElement EarthElement = {"Earth", &CharacterResistanceSet::earth};
constexpr RaceElement MindElement = {"Mind", &CharacterResistanceSet::mind};
constexpr RaceElement BodyElement = {"Body", &CharacterResistanceSet::body};

// What a race resists by base + perLevel x level; a base of 0 means immune. Elemental races resist their elements by
// 25 + level, dragons fire by 100 + 2 x level; undead are immune to Body and Mind, vampires to Mind. The immune rows
// only describe the race: ClassRules::applyClassBonuses grants those immunities in every ruleset.
struct RaceResistances
{
    uint32_t race;
    std::array<const RaceElement *, 4> elements;
    int base;
    int perLevel;
};

constexpr std::array<RaceResistances, 8> RaceResistanceTable = {{
    {DarkElf, {&FireElement, &AirElement, &WaterElement, &EarthElement}, 25, 1},
    {Elf, {&FireElement, &AirElement, &WaterElement, &EarthElement}, 25, 1},
    {Troll, {&WaterElement, &EarthElement, nullptr, nullptr}, 25, 1},
    {Goblin, {&AirElement, &EarthElement, nullptr, nullptr}, 25, 1},
    {Dwarf, {&MindElement, &EarthElement, nullptr, nullptr}, 25, 1},
    {Dragon, {&FireElement, nullptr, nullptr, nullptr}, 100, 2},
    {Undead, {&BodyElement, &MindElement, nullptr, nullptr}, 0, 0},
    {Vampire, {&MindElement, nullptr, nullptr, nullptr}, 0, 0},
}};

// "A, B and C".
std::string joinedList(const std::vector<std::string> &names)
{
    std::string text;

    for (size_t index = 0; index < names.size(); ++index)
    {
        text += (index == 0 ? "" : index + 1 == names.size() ? " and " : ", ") + names[index];
    }

    return text;
}
}

MawClassRules::MawClassRules(MawRules &rules)
    : m_rules(rules)
{
}

std::string mawClassLine(const std::string &className)
{
    static const std::array<std::pair<const char *, const char *>, 17> Lines = {{
        {"Seraphim", "seraphim"},
        {"Angel", "seraphim"},
        {"Archangel", "seraphim"},
        {"DeathKnight", "death_knight"},
        {"DeathLord", "death_knight"},
        {"LichKing", "death_knight"},
        {"Shaman", "shaman"},
        {"Sekhem", "shaman"},
        {"Marabou", "shaman"},
        {"Elementalist", "elementalist"},
        {"ElementalAdept", "elementalist"},
        {"MasterOfElements", "elementalist"},
        {"Thief", "assassin"},
        {"Rogue", "assassin"},
        {"Assassin", "assassin"},
        {"Spy", "assassin"},
        {"Dragon", "dragon"},
    }};
    const std::string canonical = canonicalClassName(className);

    if (canonical == "GreatWyrm")
    {
        return "dragon";
    }

    for (const auto &[name, line] : Lines)
    {
        if (canonical == name)
        {
            return line;
        }
    }

    return {};
}

double MawClassRules::promotionFactor(const ClassMultiplierEntry &entry) const
{
    // Two or three worlds' promotions completed make the kind's final classes Elder or Ultimate (CL:62-108).
    const int worlds = entry.promotionStep == 2 ? m_rules.promotionWorlds(entry.classKind) : 0;
    return worlds >= 2 ? 0.75 + 0.25 * worlds : 1.0;
}

// The engine keeps HP and SP per level in bytes: Lua's 2.5 for the Elemental Adept (CL:606) stores 2, and an Elder or
// Ultimate factor (x1.25, x1.5) truncates to a whole number (CL:97-98, RemoveClassLimits.lua:140-147; CLS-5).
double MawClassRules::healthPerLevel(const ClassMultiplierEntry &entry) const
{
    return std::floor(double(entry.healthPerLevel) * promotionFactor(entry));
}

double MawClassRules::manaPerLevel(const ClassMultiplierEntry &entry) const
{
    return std::floor(double(entry.manaPerLevel) * promotionFactor(entry));
}

std::optional<int> MawClassRules::baseMaxHealth(const Character &character, const ClassMultiplierEntry &entry) const
{
    // The party adds what items and buffs do to the stat effects on top, as with Standard's formula.
    const int endurance = int(character.endurance);
    const auto [bodybuilding, mastery] = skillAndMastery(character, "Bodybuilding");
    const double health = entry.baseHealth
        + healthPerLevel(entry)
            * (std::max(int(character.level), 1) + mawStatEffect(endurance) + bodybuilding * mastery);
    return std::max(0, int(health));
}

std::optional<int> MawClassRules::baseMaxSpellPoints(
    const Character &character,
    const ClassMultiplierEntry &entry) const
{
    // MAW makes Personality every caster's SP stat (zzMaw-Items.lua:4427-4433: SPStats 2), and addMana adds its effect
    // once more (:3131-3146), so the pool counts Personality twice and Intellect not at all; classes without SP keep 0.
    const int personalityEffect =
        entry.manaMode == ClassManaMode::None ? 0 : 2 * mawStatEffect(int(character.personality));

    // Dragons' pools are set in Lua: 60 for the Dragon (CL:320-325). Meditation adds no SP of its own: MAW zeroes
    // the engine's skill bonuses (zzMAW-Skills.lua:402-404) and counts it only in Enlightenment's base.
    const int baseMana = entry.className == "Dragon" ? 60 : entry.baseMana;
    const double mana = baseMana + manaPerLevel(entry) * (std::max(int(character.level), 1) + personalityEffect);
    return std::max(0, int(mana));
}

double MawClassRules::enlightenmentMeditationMana(const Character &character) const
{
    const ClassMultiplierTable *pTable = m_rules.classMultiplierTable();
    const ClassMultiplierEntry *pEntry =
        pTable != nullptr ? pTable->get(canonicalClassName(character.className)) : nullptr;

    if (pEntry == nullptr || pEntry->manaMode == ClassManaMode::None)
    {
        return 0;
    }

    const auto [meditation, mastery] = skillAndMastery(character, "Meditation");
    return manaPerLevel(*pEntry) * meditation * mastery;
}

bool mawIsDragon(const Character &character)
{
    return character.raceId == Dragon;
}

void MawClassRules::applyClassBonuses(Character &member) const
{
    ClassRules::applyClassBonuses(member);

    for (const RaceSkills &entry : FlatSkillBonuses)
    {
        if (entry.race != member.raceId)
        {
            continue;
        }

        for (const char *pSkill : entry.skills)
        {
            if (pSkill != nullptr)
            {
                const CharacterSkill *pLearned = member.findSkill(pSkill);
                member.itemSkillBonuses[canonicalSkillName(pSkill)] +=
                    3 + (pLearned != nullptr ? int(pLearned->level) / 10 : 0);
            }
        }
    }

    for (const RaceResistances &entry : RaceResistanceTable)
    {
        for (const RaceElement *pElement : entry.elements)
        {
            if (entry.race != member.raceId || pElement == nullptr || entry.base == 0)
            {
                continue;
            }

            member.magicalBonuses.resistances.*(pElement->pResistance) +=
                entry.base + entry.perLevel * int(member.level);
        }
    }

    // Supreme Armsmaster adds a tenth of Armsmaster, items included, to every melee weapon skill, at most doubling it
    // (S:2605-2620).
    if (mawSupremeArmsmaster(m_rules, member))
    {
        const int armsmaster = int(member.findSkill("Armsmaster")->level) + member.skillBonus("Armsmaster");

        for (const char *pWeapon : {"Staff", "Sword", "Dagger", "Axe", "Spear", "Mace"})
        {
            if (const CharacterSkill *pSkill = member.findSkill(pWeapon))
            {
                int &bonus = member.itemSkillBonuses[pWeapon];
                bonus += std::clamp(int(pSkill->level) - bonus, 0, armsmaster / 10);
            }
        }
    }

    const std::string line = mawClassLine(member.className);

    // Items give a Death Knight and a dragon-race character no spell points (CL:793-796).
    if (line == "death_knight" || mawIsDragon(member))
    {
        member.magicalBonuses.maxSpellPoints = 0;
    }
    else if (line == "assassin")
    {
        const CharacterSkill *pAssassination = member.findSkill("EarthMagic");
        member.magicalBonuses.maxSpellPoints = 10 * (pAssassination != nullptr ? int(pAssassination->mastery) : 0);
    }
}

bool MawClassRules::learnsSpellsFromBooks(const Character &character) const
{
    const std::string line = mawClassLine(character.className);
    return line != "death_knight" && line != "elementalist" && line != "assassin";
}

bool MawClassRules::isDragon(const Character &character) const
{
    return mawIsDragon(character);
}

std::string MawClassRules::displayName(const Party &party, const Character &member) const
{
    const std::string name = ClassRules::displayName(party, member);
    const ClassMultiplierEntry *pEntry = party.classMultiplierTable() != nullptr
        ? party.classMultiplierTable()->get(canonicalClassName(member.className))
        : nullptr;
    const int worlds = pEntry != nullptr && pEntry->promotionStep == 2 ? m_rules.promotionWorlds(pEntry->classKind) : 0;
    return worlds >= 3 ? "Ultimate " + name : worlds == 2 ? "Elder " + name : name;
}

PortraitCounter MawClassRules::portraitCounter(const Character &member) const
{
    const std::string line = mawClassLine(member.className);
    PortraitCounter counter;

    if (line == "assassin")
    {
        // Points come in halves (an arrow); the popup names what they buy (MawClassSpells comboCost).
        const double points = m_rules.classRuntime(member).comboPoints;
        const int halves = int(std::floor(points * 2 + 1e-6));
        counter.kind = PortraitCounterKind::ComboPoints;
        counter.amount = halves / 2.0;
        counter.pips = 5;
        counter.title = member.name + " - Combo points";
        counter.notes.push_back(
            std::to_string(halves / 2) + (halves % 2 != 0 ? ".5" : "") + " of 5 combo points");
        std::map<int, std::string> spellsByCost;

        for (const MawClassSpell &spell : mawClassSpells(member.className))
        {
            if (spell.comboCost > 0 && member.knownSpellIds.contains(spell.spellId))
            {
                std::string &names = spellsByCost[spell.comboCost];
                names += (names.empty() ? "" : ", ") + std::string(spell.pName);
            }
        }

        for (const auto &[cost, names] : spellsByCost)
        {
            counter.notes.push_back(std::to_string(cost) + (counter.amount >= cost ? " (ready): " : ": ") + names);
        }

        counter.notes.push_back("+1 per paying blow or kill, +0.5 per arrow");
    }
    else if (line == "elementalist")
    {
        // At 10 the cast delay is back to normal and the damage doubled (CLASSES_SPELLS_SPEC 5.5).
        const int stacks = m_rules.classRuntime(member).elementalStacks;
        const auto percent = [](double value)
        {
            return std::to_string(int(std::lround(value * 100))) + "%";
        };
        counter.kind = PortraitCounterKind::Stacks;
        counter.amount = stacks;
        counter.pips = 10;
        counter.title = member.name + " - Elemental stacks";
        counter.notes.push_back(std::to_string(stacks) + (stacks == 1 ? " stack" : " stacks"));
        counter.notes.push_back("Damage " + percent(1 + 0.1 * stacks) + ", cast delay "
            + percent(1.5 / (1 + 0.05 * stacks)));
        counter.notes.push_back("+1 per offensive cast; halves when idle");
    }

    return counter;
}

void MawClassRules::update(Party &party, const IGameplayWorldRuntime &world, float frameSeconds) const
{
    // Four times a second is often enough for promotions, known spells and pools.
    m_pendingSeconds += frameSeconds;

    if (m_pendingSeconds < 0.25f)
    {
        return;
    }

    const float deltaSeconds = m_pendingSeconds;
    m_pendingSeconds = 0;
    updatePromotions(party);

    // Austerity: Identify Monster 10 Grandmaster for everyone on each map, none after a respec until the next.
    if (m_rules.options().challengeMode == RulesetChallengeMode::Austerity)
    {
        const bool newMap = m_rules.currentMap() != m_identifyMonsterMap;
        m_identifyMonsterMap = m_rules.currentMap();
        m_rules.setAusterityIdentifyRespecced(m_rules.austerityIdentifyRespecced() && !newMap);

        for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
        {
            std::unordered_map<std::string, CharacterSkill> &skills = party.member(memberIndex)->skills;

            if (m_rules.austerityIdentifyRespecced())
            {
                skills.erase("IdentifyMonster");
            }
            else if (newMap)
            {
                skills["IdentifyMonster"] = {"IdentifyMonster", 10, SkillMastery::Grandmaster};
            }
        }
    }

    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        Character &member = *party.member(memberIndex);
        const std::string line = mawClassLine(member.className);
        MawClassRuntime &runtime = m_rules.classRuntime(member);

        // Death Knights and Assassins know the spells their school masteries give, and only those (MCC:458-480).
        if (line == "death_knight" || line == "assassin")
        {
            const std::vector<uint32_t> known = mawKnownClassSpells(member);
            std::unordered_set<uint32_t> spells;

            for (const uint32_t spellId : member.knownSpellIds)
            {
                if (spellId >= 100)
                {
                    spells.insert(spellId);
                }
            }

            spells.insert(known.begin(), known.end());

            if (spells != member.knownSpellIds)
            {
                member.knownSpellIds = std::move(spells);
            }
        }

        if (line == "elementalist")
        {
            // The four elements' spells come from casting; stacks halve every second once the caster has not cast
            // for four of their casts (at least 128 ticks; MCC:300-315).
            const bool insanity = m_rules.options().challengeMode == RulesetChallengeMode::RoadToInsanity
                || m_rules.options().challengeMode == RulesetChallengeMode::BeyondMadness;
            std::unordered_set<uint32_t> spells;

            for (const uint32_t spellId : member.knownSpellIds)
            {
                if (spellId > 44)
                {
                    spells.insert(spellId);
                }
            }

            const std::vector<uint32_t> known = mawElementalistKnownSpells(member, insanity);
            spells.insert(known.begin(), known.end());

            if (spells != member.knownSpellIds)
            {
                member.knownSpellIds = std::move(spells);
            }

            // The window is max(4 x the cast's recovery, 128) game ticks, 128 a second; once it passes the stacks
            // halve at once, then once a second (Classes.lua:300-315, 533; CLS-4).
            runtime.elementalIdleSeconds += deltaSeconds;
            const float idleLimit = std::max(4 * runtime.elementalLastDelayTicks, 128) / 128.0f;

            if (runtime.elementalStacks > 0 && runtime.elementalIdleSeconds > idleLimit)
            {
                // A cast sets the countdown to 0, so the first halving comes as the window passes.
                if (runtime.elementalDecaySeconds > 0)
                {
                    runtime.elementalDecaySeconds -= deltaSeconds;
                }

                while (runtime.elementalDecaySeconds <= 0 && runtime.elementalStacks > 0)
                {
                    runtime.elementalDecaySeconds += 1;
                    runtime.elementalStacks /= 2;
                }
            }
        }

        if (mawIsDragon(member))
        {
            bool learned = false;

            for (const char *pSkill : {"Unarmed", "Dodging", "DragonAbility"})
            {
                if (member.findSkill(pSkill) == nullptr)
                {
                    member.skills[pSkill] = {pSkill, 1, SkillMastery::Normal};
                    learned = true;
                }
            }

            // Dragon Ability's Novice spell (Fear) comes with the skill.
            if (learned)
            {
                member.synchronizeInnateAbilitySpells();
            }
        }

        // The refills below run in MAW's SP loop: not for the dead, stoned, eradicated or insane, at the dimension
        // map's slower regeneration, up to the pool the auras leave (S:1433-1481; CLS-9, SKL-6).
        const bool refills = !member.conditions.test(size_t(CharacterCondition::Dead))
            && !member.conditions.test(size_t(CharacterCondition::Petrified))
            && !member.conditions.test(size_t(CharacterCondition::Eradicated))
            && !member.conditions.test(size_t(CharacterCondition::Insane));
        const double mapRegeneration = 1 - m_rules.mapAffix(MawMapAffix::PlayerRegeneration).value_or(0) / 100;
        const int refillCap = std::max(0, member.maxSpellPoints + member.permanentBonuses.maxSpellPoints
            + member.magicalBonuses.maxSpellPoints - m_rules.gameRules().spells.reservedSpellPoints(party, memberIndex));

        if (line == "dragon" && refills)
        {
            runtime.dragonSecondsSinceLoss =
                runtime.dragonLastSpellPoints > member.spellPoints ? 0 : runtime.dragonSecondsSinceLoss + deltaSeconds;
            const double multiplier = mawRegenerationMultiplier(runtime.dragonSecondsSinceLoss < 20,
                partyHasYellowAlert(world)) * mapRegeneration;
            const int maximum = refillCap;
            runtime.energyCarry +=
                (canonicalClassName(member.className) == "GreatWyrm" ? 5 : 2) * multiplier * deltaSeconds;
            const int whole = int(runtime.energyCarry);
            runtime.energyCarry -= whole;
            member.spellPoints = std::max(member.spellPoints, std::min(maximum, member.spellPoints + whole));
            runtime.dragonLastSpellPoints = member.spellPoints;
        }

        if (line == "assassin")
        {
            // Poisons regenerates (0.6 + 0.2 m) x 10 energy a second; Subtlety stacks lapse after their eight
            // seconds (S:1478-1481, MCC:388-413).
            const CharacterSkill *pPoisons = member.findSkill("WaterMagic");
            const double perSecond = (0.6 + 0.2 * (pPoisons != nullptr ? int(pPoisons->mastery) : 0)) * 10;

            if (refills)
            {
                runtime.energyCarry += perSecond * mapRegeneration * deltaSeconds;
                const int whole = int(runtime.energyCarry);
                runtime.energyCarry -= whole;
                member.spellPoints = std::max(member.spellPoints, std::min(refillCap, member.spellPoints + whole));
            }
            runtime.subtletySeconds = std::max(0.0f, runtime.subtletySeconds - deltaSeconds);

            if (runtime.subtletySeconds <= 0)
            {
                runtime.subtletyStacks = 0;
            }
        }
    }

    const int hour = world.currentHour();
    // MAW's hour is fractional, so its `hour > 21` starts the night at 21:00 (CLS-6).
    const bool vampireNight = (hour >= 21 || hour < 5 || world.isIndoorMap()) && world.mapName() != "7d25.blv";

    for (size_t memberIndex = 0; memberIndex < party.members().size() && vampireNight; ++memberIndex)
    {
        const CharacterBuffState *pBuff = party.characterBuff(memberIndex, CharacterBuffId::Preservation);

        // Five game minutes, refreshed.
        if (party.members()[memberIndex].raceId == Vampire && (pBuff == nullptr || pBuff->remainingSeconds < 5))
        {
            party.applyCharacterBuff(
                memberIndex, CharacterBuffId::Preservation, 10, 0, 0, 0, SkillMastery::None, uint32_t(memberIndex));
        }
    }
}

void MawClassRules::updatePromotions(Party &party) const
{
    const ClassSkillTable *pClasses = party.classSkillTable();

    if (pClasses == nullptr)
    {
        return;
    }

    const auto hasQuestBit = [&party](uint32_t bit)
    {
        return party.hasQuestBit(bit);
    };
    const auto hasAward = [&party](uint32_t award)
    {
        return party.hasAward(award);
    };
    std::map<uint32_t, int> worlds;

    for (const auto &[kind, promotion] : m_rules.promotionData().kinds)
    {
        if (const int count = mawPromotionWorlds(promotion, hasQuestBit, hasAward); count > 0)
        {
            worlds[kind] = count;
        }
    }

    const bool worldsChanged = worlds != m_rules.promotionWorldsByKind();
    m_rules.setPromotionWorlds(worlds);

    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        const Character &member = party.members()[memberIndex];
        const ClassMetadataEntry *pClass = pClasses->classMetadata(member.className);

        if (pClass == nullptr)
        {
            continue;
        }

        const auto promotion = m_rules.promotionData().kinds.find(pClass->classKind);
        uint32_t step = pClass->promotionStep;

        if (worlds.contains(pClass->classKind) && step < 2)
        {
            step = 2;
        }
        else if (step == 0 && promotion != m_rules.promotionData().kinds.end()
            && std::any_of(promotion->second.mid.begin(), promotion->second.mid.end(), hasQuestBit))
        {
            step = 1;
        }

        const std::vector<std::string> classes = pClasses->classNamesOfKind(pClass->classKind, step);

        if (step == pClass->promotionStep || classes.empty())
        {
            if (worldsChanged && step == 2)
            {
                party.refreshMemberResources(memberIndex);
            }

            continue;
        }

        // MAW draws one of several final classes at random; the draw is fixed per character so a reload agrees.
        const uint64_t draw = m_rules.randomRootSeed() ^ std::hash<std::string> {}(member.name)
            ^ (uint64_t(member.characterDataId) << 32) ^ pClass->classKind;
        // The class alone: a promotion to Lich keeps the member's race and portrait (CL:123-126).
        party.setMemberClassName(memberIndex, classes[size_t(draw % classes.size())], true);
    }
}

namespace
{
// A class perk's school: the trained level, without item, follower or race bonuses, as MAW's perks read
// `pl.Skills[...]` (CLS-2).
std::pair<double, int> schoolSkill(const Character &character, const char *pSkillName)
{
    const CharacterSkill *pSkill = character.findSkill(pSkillName);
    return {pSkill != nullptr ? double(pSkill->level) : 0.0, pSkill != nullptr ? std::min(int(pSkill->mastery), 4) : 0};
}
}

double mawClassMeleeFlatDamage(const MawRules &rules, const Character &character)
{
    const std::string line = mawClassLine(character.className);

    if (line == "seraphim")
    {
        const auto [mind, mastery] = schoolSkill(character, "MindMagic");
        return mind * (mastery + 1) / 2;
    }

    if (line == "shaman")
    {
        const auto [earth, mastery] = schoolSkill(character, "EarthMagic");
        return earth * mastery / 2;
    }

    if (line == "death_knight")
    {
        static constexpr std::array<double, 4> PerPoint = {0.5, 0.75, 1, 1};
        const MawBalanceModel &model = rules.model(1);
        double flat = 0;

        for (const char *pSchool : {"WaterMagic", "DarkMagic"})
        {
            const auto [level, mastery] = schoolSkill(character, pSchool);
            flat += model.gradualSkillValue(PerPoint, level, mastery) * level;
        }

        return flat;
    }

    if (line == "assassin")
    {
        const auto [assassination, mastery] = schoolSkill(character, "EarthMagic");
        return assassination * (1 + mastery);
    }

    return 0;
}

double mawClassMeleeMultiplier(const Character &character)
{
    if (mawClassLine(character.className) == "shaman")
    {
        return 1 + schoolSkill(character, "SpiritMagic").first / 100;
    }

    return 1;
}

double mawClassAttackSpeedPercent(const Character &character)
{
    const std::string line = mawClassLine(character.className);

    if (line == "seraphim")
    {
        const auto [light, mastery] = schoolSkill(character, "LightMagic");
        return light * mastery / 2;
    }

    if (line == "death_knight")
    {
        return schoolSkill(character, "WaterMagic").first;
    }

    return 0;
}

MawClassDefense mawClassDefense(const MawRules &rules, const Character &character, int partyCount)
{
    const std::string line = mawClassLine(character.className);
    MawClassDefense defense;

    if (line == "shaman")
    {
        defense.physicalCutSkill = defense.magicCutSkill = schoolSkill(character, "AirMagic").first;
    }
    else if (line == "death_knight")
    {
        defense.physicalCutSkill = schoolSkill(character, "BodyMagic").first;
        defense.magicCutSkill = schoolSkill(character, "DarkMagic").first;
    }

    const double flatSkill = line == "seraphim" ? schoolSkill(character, "SpiritMagic").first
        : line == "shaman"                     ? schoolSkill(character, "WaterMagic").first
                                               : 0;

    if (flatSkill > 0 && character.health > 0)
    {
        const double level = std::max(1.0, rules.state().totalLevel());
        MawBalanceModel &model = rules.model(std::max(partyCount, 1));
        const double expectedSkill = std::max(model.skill(level), 1.0);
        const double averageTaken = (model.physicalDamageTaken(level + 1) + model.magicDamageTaken(level + 1)) / 2;
        defense.flatReduction = mawRound(model.monsterDamage(level + 1) * flatSkill / expectedSkill * averageTaken
            / 2 * std::pow(0.99, expectedSkill));
    }

    return defense;
}

MawLeech mawLeech(const MawRules &rules, const Character &character, const ItemTable *)
{
    constexpr uint16_t Vampiric = 16;
    constexpr uint16_t Lichs = 40;
    constexpr uint16_t Darkness = 41;
    constexpr uint32_t Hades = 2035;
    static constexpr std::array<uint32_t, 3> VampiricArtifacts = {508, 527, 2020};
    const std::array<const EquippedItemRuntimeState *, 3> weapons = {
        &character.equipmentRuntime.offHand, &character.equipmentRuntime.mainHand, &character.equipmentRuntime.bow};
    const auto holds = [&weapons](uint16_t special)
    {
        return std::any_of(weapons.begin(), weapons.end(),
            [special](const EquippedItemRuntimeState *pState) { return pState->specialEnchantId == special; });
    };
    MawLeech leech;

    // The vampiric artifacts (Foulfang 508, 527, 2020) leech like "of Darkness"; MAW never reads their flag
    // (COMBAT_SPEC §13 item 6).
    const bool vampiricArtifact = std::any_of(VampiricArtifacts.begin(), VampiricArtifacts.end(),
        [&character](uint32_t itemId)
        {
            return character.equipment.mainHand == itemId || character.equipment.offHand == itemId
                || character.equipment.bow == itemId;
        });

    if (holds(Vampiric) || holds(Darkness) || vampiricArtifact)
    {
        leech.melee += 0.10;
        leech.ranged += 0.05;
    }

    if (holds(Vampiric) || holds(Lichs))
    {
        leech.spell += 0.10;
    }

    if (character.equipment.mainHand == Hades || character.equipment.offHand == Hades)
    {
        leech.melee -= 0.10;
    }

    const auto add = [&leech](double factor)
    {
        leech.melee += 0.05 * factor;
        leech.ranged += 0.025 * factor;
        leech.spell += 0.025 * factor;
    };

    if (rules.auraSkill(91))
    {
        add(1);
    }

    if (character.raceId == 1)
    {
        const std::string className = canonicalClassName(character.className);
        add(className == "Vampire" || className == "Nosferatu" ? 2 : 1);
    }

    if (mawClassLine(character.className) == "death_knight")
    {
        leech.melee += 0.10;
        leech.ranged += 0.05;
    }

    return leech;
}

MawAscension mawAscension(const Character &caster, MawAscensionUse use)
{
    const std::string line = mawClassLine(caster.className);
    const auto baseSum = [&caster](std::initializer_list<const char *> schools)
    {
        double sum = 0;

        for (const char *pSchool : schools)
        {
            const CharacterSkill *pSkill = caster.findSkill(pSchool);
            sum += pSkill != nullptr ? pSkill->level : 0;
        }

        return sum;
    };

    if (line == "death_knight" || line == "assassin")
    {
        return {};
    }

    if (line == "elementalist" && use != MawAscensionUse::CrowdControl)
    {
        const double sum = baseSum({"FireMagic", "AirMagic", "WaterMagic", "EarthMagic"}) / 4;
        const bool floored = use == MawAscensionUse::CastTime || use == MawAscensionUse::CrowdControlCastTime;
        return {floored ? std::floor(sum) : sum, SkillMastery::Grandmaster};
    }

    if (line == "shaman" && (use == MawAscensionUse::Cost || use == MawAscensionUse::Heal))
    {
        const double sum = baseSum({"FireMagic", "AirMagic", "WaterMagic", "EarthMagic", "SpiritMagic", "MindMagic",
                               "BodyMagic"})
            / 7;
        return {sum, SkillMastery::Grandmaster};
    }

    const CharacterSkill *pLearning = caster.findSkill("Learning");
    return {(pLearning != nullptr ? double(pLearning->level) : 0.0) + caster.skillBonus("Learning"),
        pLearning != nullptr ? pLearning->mastery : SkillMastery::None};
}

double mawShamanSchoolSum(const Character &caster)
{
    if (mawClassLine(caster.className) != "shaman")
    {
        return 0;
    }

    double sum = 0;

    for (const char *pSchool :
         {"FireMagic", "AirMagic", "WaterMagic", "EarthMagic", "SpiritMagic", "MindMagic", "BodyMagic"})
    {
        sum += schoolSkill(caster, pSchool).first;
    }

    return sum;
}

bool mawSupremeArmsmaster(const MawRules &rules, const Character &character, bool effectiveLevel)
{
    const CharacterSkill *pSkill = character.findSkill("Armsmaster");
    const std::string className = canonicalClassName(character.className);
    const RulesetChallengeMode mode = rules.options().challengeMode;
    const uint32_t supremeLevel = mode == RulesetChallengeMode::BeyondMadness ? 70
        : mode == RulesetChallengeMode::RoadToInsanity                       ? 50
                                                                              : 30;
    const int level = pSkill == nullptr ? 0
        : effectiveLevel                ? int(pSkill->level) + character.skillBonus("Armsmaster")
                                        : int(pSkill->level);
    return pSkill != nullptr && pSkill->mastery >= SkillMastery::Grandmaster && level >= int(supremeLevel)
        && (className == "Knight" || className == "Cavalier" || className == "BlackKnight" || className == "Champion");
}

bool MawClassRules::offersMercenaries() const
{
    return m_rules.options().challengeMode != RulesetChallengeMode::BeyondMadness;
}

uint32_t MawClassRules::mercenarySkillPoints(uint32_t level) const
{
    uint32_t points = 0;

    for (uint32_t step = 2; step <= level; ++step)
    {
        points += 4 + step / 10 + 1;
    }

    return points;
}

std::vector<std::string> MawClassRules::raceNotes(const Character &character) const
{
    std::vector<std::string> notes;

    for (const RaceSkills &entry : FlatSkillBonuses)
    {
        std::vector<std::string> skills;

        for (const char *pSkill : entry.skills)
        {
            if (entry.race == character.raceId && pSkill != nullptr)
            {
                skills.push_back(displaySkillName(pSkill));
            }
        }

        if (!skills.empty())
        {
            notes.push_back("+3 to " + joinedList(skills) + ", and +1 more per 10 skill levels.");
        }
    }

    for (const RaceResistances &entry : RaceResistanceTable)
    {
        std::vector<std::string> elements;

        for (const RaceElement *pElement : entry.elements)
        {
            if (entry.race == character.raceId && pElement != nullptr)
            {
                elements.push_back(pElement->pName);
            }
        }

        if (elements.empty())
        {
            continue;
        }

        notes.push_back(entry.base == 0
                ? "Immune to " + joinedList(elements) + " magic."
                : joinedList(elements) + " resistance +" + std::to_string(entry.base) + ", and +"
                    + std::to_string(entry.perLevel) + " per level.");
    }

    if (character.raceId == Vampire)
    {
        notes.push_back("Preservation at night and in dungeons.");
    }

    return notes;
}

bool MawClassRules::showsCreationSkillMatrix() const
{
    return true;
}

std::optional<std::string> MawClassRules::partyCharge(
    Party &party,
    IGameplayWorldRuntime &world,
    std::optional<size_t> targetActorIndex) const
{
    // 25 seconds of cooldown, MAW's half game minutes.
    constexpr double CooldownGameMinutes = 12.5;
    constexpr int ParalyzeGroup = 3;
    const Character *pKnight = party.member(0);
    const std::string className = pKnight != nullptr ? canonicalClassName(pKnight->className) : std::string();
    const bool knightLine =
        className == "Knight" || className == "Cavalier" || className == "BlackKnight" || className == "Champion";

    if (party.members().size() != 1 || !knightLine)
    {
        return std::nullopt;
    }

    const double now = world.gameMinutes();

    // A clock that went back (a load) makes it ready.
    if (m_chargeReadyGameMinutes - now > CooldownGameMinutes)
    {
        m_chargeReadyGameMinutes = 0;
    }

    if (now < m_chargeReadyGameMinutes)
    {
        return "Charge has " + std::to_string(int(std::ceil((m_chargeReadyGameMinutes - now) * 2)))
            + " seconds of cooldown";
    }

    GameplayRuntimeActorState target = {};

    if (!targetActorIndex || !world.actorRuntimeState(*targetActorIndex, target) || target.isDead)
    {
        return std::string();
    }

    const float deltaX = target.preciseX - world.partyX();
    const float deltaY = target.preciseY - world.partyY();
    const float distance = std::sqrt(deltaX * deltaX + deltaY * deltaY
        + (target.preciseZ - world.partyFootZ()) * (target.preciseZ - world.partyFootZ()));

    if (distance <= 500 || distance >= 3000)
    {
        return std::string("Out of range");
    }

    // Twenty steps of a 22nd of the way.
    const float horizontal = std::hypot(deltaX, deltaY);

    if (horizontal > 0.01f)
    {
        world.dashParty(deltaX / horizontal, deltaY / horizontal, horizontal * 20 / 22);
    }

    m_chargeReadyGameMinutes = now + CooldownGameMinutes;
    const double minutes = className == "Knight" ? 1.5 : className == "Cavalier" ? 2 : 2.5;
    // An Unstoppable boss is not stunned (calcDebuffDuration, zzMAW-Skills.lua:999).
    const double seconds = mawIgnoresCrowdControl(target.rulesetFacts)
        ? 0
        : m_rules.diminishedCrowdControlSeconds(mapActorKey(world.mapName(), *targetActorIndex), ParalyzeGroup,
              now * 2, minutes * 2, target.rulesetFacts.bossAffix != 0);

    if (seconds > 0)
    {
        world.stunActor(*targetActorIndex, float(seconds));
    }

    return pKnight->name + " casts Charge stunning the enemy";
}

std::optional<float> MawClassRules::unstuckLift(double gameMinutes) const
{
    constexpr float UnstuckLift = 100.0f;
    return m_rules.takeUnstuck(gameMinutes) ? std::optional<float>(UnstuckLift) : std::nullopt;
}

std::optional<FollowerHireRefusal> MawClassRules::followerHireRefusal(uint32_t houseId) const
{
    constexpr std::array<uint32_t, 2> HiringHouses = {1466, 1486};

    if (!mawModelConfig(m_rules.options(), 5).doomMode
        || std::find(HiringHouses.begin(), HiringHouses.end(), houseId) != HiringHouses.end())
    {
        return std::nullopt;
    }

    return FollowerHireRefusal{"Following you would be foolish",
        "I wouldn't join in your reckless adventure, not even for all the wealth in the world."};
}

std::vector<uint32_t> MawClassRules::mercenaryClassKinds(uint32_t continentId, std::vector<uint32_t>) const
{
    // Class kinds of class_extra.txt: 16 Peasant, 17 Seraphim, 18 Death Knight, 19 Shaman, 20 Elementalist.
    switch (continentId)
    {
        case 1:
            return {2, 3, 4, 6, 7, 12, 13, 15, 16};
        case 2:
            return {1, 2, 5, 6, 8, 9, 10, 11, 14, 16};
        default:
            return {1, 2, 5, 6, 9, 14, 16, 17, 18, 19, 20};
    }
}
}
