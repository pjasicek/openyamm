#include "game/rules/maw/MawClassSpells.h"
#include "engine/Localization.h"

#include "game/party/Party.h"
#include "game/rules/maw/MawClassRules.h"

#include <algorithm>
#include <cmath>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
// The names stay English, as the spell table's do; trNoop marks them for the screens that show them translated.
const std::vector<MawClassSpell> DeathKnightSpells = {
    // Frost (MCC:24-36, 108-122; DM:695-818).
    {26, Engine::trNoop("Icy Touch").data(), "WaterMagic", 1, 15, 0, {1, 1, 1.2, 1.2}},
    {27, Engine::trNoop("Water Walk").data(), "WaterMagic", 2, 0},
    {29, Engine::trNoop("Frostbite").data(), "WaterMagic", 3, 30, 0, {1.5, 1.5, 1.5, 2}},
    {32, Engine::trNoop("Ice Bomb").data(), "WaterMagic", 4, 50, 0, {0.75, 0.75, 0.75, 0.75}},
    // Blood.
    {68, Engine::trNoop("Blood Leech").data(), "BodyMagic", 1, 6, 0, {}, true},
    {71, Engine::trNoop("Regeneration").data(), "BodyMagic", 2, 0},
    {76, Engine::trNoop("Asphyxiate").data(), "BodyMagic", 3, 70, 0, {1.1, 1.1, 1.1, 1.4}},
    {74, Engine::trNoop("Superior Blood Leech").data(), "BodyMagic", 4, 12, 0, {}, true},
    // Unholy.
    {91, Engine::trNoop("Vampiric Aura").data(), "DarkMagic", 1, 0},
    {90, Engine::trNoop("Death Coil").data(), "DarkMagic", 2, 30, 0, {1, 1, 1, 1.2}},
    {96, Engine::trNoop("Death Grasp").data(), "DarkMagic", 3, 15, 0, {}, true},
    {97, Engine::trNoop("Death Breath").data(), "DarkMagic", 4, 100, 0, {0.6, 0.6, 0.6, 0.6}},
};

const std::vector<MawClassSpell> AssassinSpells = {
    // Combat: the first entry unskilled, one more per mastery (MCC:69-101, 595-625).
    {1, Engine::trNoop("Torch Light").data(), "FireMagic", 0, 1},
    {4, Engine::trNoop("Fire Aura").data(), "FireMagic", 1, 0},
    {5, Engine::trNoop("Haste").data(), "FireMagic", 2, 0},
    {6, Engine::trNoop("Fireball").data(), "FireMagic", 3, 0, 5, {1, 1, 1, 1}},
    {7, Engine::trNoop("Fire Spike").data(), "FireMagic", 4, 0, 3, {2.5, 2.5, 2.5, 2.5}},
    // Subtlety: two entries unskilled.
    {12, Engine::trNoop("Wizard Eye").data(), "AirMagic", 0, 1},
    {17, Engine::trNoop("Shield").data(), "AirMagic", 0, 0},
    {16, Engine::trNoop("Jump").data(), "AirMagic", 1, 5},
    {18, Engine::trNoop("Chain Lightning").data(), "AirMagic", 2, 0, 5, {1.5, 1.5, 1.5, 1.5}},
    {21, Engine::trNoop("Fly").data(), "AirMagic", 3, 25},
    {19, Engine::trNoop("Invisibility").data(), "AirMagic", 4, 15},
    // Poisons.
    {24, Engine::trNoop("Poison Spray").data(), "WaterMagic", 0, 0, 3, {0.75, 0.75, 0.75, 0.75}},
    {27, Engine::trNoop("Water Walk").data(), "WaterMagic", 1, 0},
    {29, Engine::trNoop("Acid Burst").data(), "WaterMagic", 2, 0, 3, {3, 3, 3, 3}},
    {31, Engine::trNoop("Town Portal").data(), "WaterMagic", 3, 20},
    {33, Engine::trNoop("Lloyd's Beacon").data(), "WaterMagic", 4, 30},
    // Assassination.
    {34, Engine::trNoop("Stun").data(), "EarthMagic", 0, 0, 3, {1.5, 1.5, 1.5, 1.5}},
    {38, Engine::trNoop("Stone Skin").data(), "EarthMagic", 1, 0},
    {39, Engine::trNoop("Blades").data(), "EarthMagic", 2, 0, 3, {3, 3, 3, 3}},
    {42, Engine::trNoop("Telekinesis").data(), "EarthMagic", 3, 0},
    {44, Engine::trNoop("Mass Distortion").data(), "EarthMagic", 4, 0, 4, {4, 4, 4, 4}},
};

const std::vector<MawClassSpell> NoSpells;

// The class spellbooks: per page the school's first spell id, the page and tab art, then each spell's pictures and
// place in the 640 x 480 book. Written by level_generation/ui/maw_class_spellbooks_20261108/scripts/
// install_runtime.py from the study's layout; the art is in engine/icons_x2 (maw_sbdk*, maw_sbas*, maw_stdk*,
// maw_stas*), and the Assassin's ordinary spells keep their original pictures.
const SpellbookSkin DeathKnightSpellbook = {{
    {23, "maw_sbdk_frost", "maw_stdk_frost_d", "maw_stdk_frost_u", {
        {26, "maw_sbdk26b", "maw_sbdk26a", {129.5f, 124.2f, 165.0f, 111.5f}},
        {27, "maw_sbdk27b", "maw_sbdk27a", {57.5f, 279.2f, 215.0f, 145.5f}},
        {29, "maw_sbdk29b", "maw_sbdk29a", {360.0f, 64.5f, 220.0f, 171.0f}},
        {32, "maw_sbdk32b", "maw_sbdk32a", {360.0f, 267.0f, 220.0f, 170.0f}},
    }},
    {67, "maw_sbdk_blood", "maw_stdk_blood_d", "maw_stdk_blood_u", {
        {68, "maw_sbdk68b", "maw_sbdk68a", {129.5f, 124.2f, 165.0f, 111.5f}},
        {71, "maw_sbdk71b", "maw_sbdk71a", {57.5f, 270.8f, 215.0f, 162.5f}},
        {76, "maw_sbdk76b", "maw_sbdk76a", {360.0f, 71.5f, 220.0f, 157.0f}},
        {74, "maw_sbdk74b", "maw_sbdk74a", {372.8f, 262.0f, 194.5f, 180.0f}},
    }},
    {89, "maw_sbdk_unholy", "maw_stdk_unholy_d", "maw_stdk_unholy_u", {
        {91, "maw_sbdk91b", "maw_sbdk91a", {129.5f, 115.0f, 165.0f, 130.0f}},
        {90, "maw_sbdk90b", "maw_sbdk90a", {57.5f, 274.0f, 215.0f, 156.0f}},
        {96, "maw_sbdk96b", "maw_sbdk96a", {360.0f, 66.8f, 220.0f, 166.5f}},
        {97, "maw_sbdk97b", "maw_sbdk97a", {360.0f, 277.8f, 220.0f, 148.5f}},
    }},
}};

const SpellbookSkin AssassinSpellbook = {{
    {1, "maw_sbas_combat", "maw_stas_combat_d", "maw_stas_combat_u", {
        {1, "sbf01b", "sbf01a", {150.0f, 110.0f, 124.0f, 140.0f}},
        {4, "sbf02b", "sbf02a", {109.0f, 277.5f, 112.0f, 155.0f}},
        {5, "sbf05b", "sbf05a", {399.5f, 44.5f, 141.0f, 121.0f}},
        {6, "maw_sbas06b", "maw_sbas06a", {375.0f, 179.0f, 174.0f, 132.0f}},
        {7, "maw_sbas07b", "maw_sbas07a", {382.8f, 319.0f, 174.5f, 132.0f}},
    }},
    {12, "maw_sbas_subtlety", "maw_stas_subtlety_d", "maw_stas_subtlety_u", {
        {12, "sba01b", "sba01a", {151.0f, 117.5f, 128.0f, 115.0f}},
        {17, "sba06b", "sba06a", {54.2f, 243.0f, 111.5f, 118.0f}},
        {16, "sba05b", "sba05a", {161.2f, 346.2f, 107.5f, 117.5f}},
        {18, "maw_sbas18b", "maw_sbas18a", {373.8f, 39.0f, 192.5f, 132.0f}},
        {21, "sba10b", "sba10a", {395.8f, 179.0f, 132.5f, 132.0f}},
        {19, "sba08b", "sba08a", {403.0f, 319.5f, 134.0f, 131.0f}},
    }},
    {23, "maw_sbas_poisons", "maw_stas_poisons_d", "maw_stas_poisons_u", {
        {24, "maw_sbas24b", "maw_sbas24a", {129.5f, 124.8f, 165.0f, 110.5f}},
        {27, "sbw05b", "sbw05a", {87.0f, 306.5f, 156.0f, 97.0f}},
        {29, "maw_sbas29b", "maw_sbas29a", {372.0f, 39.0f, 196.0f, 132.0f}},
        {31, "sbw09b", "sbw09a", {395.0f, 198.5f, 134.0f, 93.0f}},
        {33, "sbw11b", "sbw11a", {423.5f, 319.0f, 93.0f, 132.0f}},
    }},
    {34, "maw_sbas_assassination", "maw_stas_assassination_d", "maw_stas_assassination_u", {
        {34, "maw_sbas34b", "maw_sbas34a", {129.5f, 124.8f, 165.0f, 110.5f}},
        {38, "sbe05b", "sbe05a", {93.5f, 290.5f, 143.0f, 129.0f}},
        {39, "maw_sbas39b", "maw_sbas39a", {372.0f, 39.0f, 196.0f, 132.0f}},
        {42, "sbe09b", "sbe09a", {380.5f, 211.0f, 163.0f, 68.0f}},
        {44, "maw_sbas44b", "maw_sbas44a", {372.0f, 319.0f, 196.0f, 132.0f}},
    }},
}};
}

const std::vector<MawClassSpell> &mawClassSpells(const std::string &className)
{
    const std::string line = mawClassLine(className);
    return line == "death_knight" ? DeathKnightSpells : line == "assassin" ? AssassinSpells : NoSpells;
}

const SpellbookSkin *mawClassSpellbookSkin(const std::string &className)
{
    const std::string line = mawClassLine(className);
    return line == "death_knight" ? &DeathKnightSpellbook : line == "assassin" ? &AssassinSpellbook : nullptr;
}

const MawClassSpell *mawClassSpell(const std::string &className, uint32_t spellId)
{
    const std::vector<MawClassSpell> &spells = mawClassSpells(className);
    const auto found = std::find_if(spells.begin(), spells.end(),
        [spellId](const MawClassSpell &spell) { return spell.spellId == spellId; });
    return found != spells.end() ? &*found : nullptr;
}

std::vector<uint32_t> mawKnownClassSpells(const Character &character)
{
    std::vector<uint32_t> known;

    for (const MawClassSpell &spell : mawClassSpells(character.className))
    {
        const CharacterSkill *pSchool = character.findSkill(spell.pSchool);
        const int mastery = pSchool != nullptr ? int(pSchool->mastery) : 0;

        if (mastery >= spell.mastery)
        {
            known.push_back(spell.spellId);
        }
    }

    return known;
}

const char *mawClassSchoolName(const Character &character, const std::string &skillName)
{
    static const std::array<std::pair<const char *, const char *>, 3> DeathKnight = {{
        {"WaterMagic", Engine::trNoop("Frost").data()},
        {"BodyMagic", Engine::trNoop("Blood").data()},
        {"DarkMagic", Engine::trNoop("Unholy").data()},
    }};
    static const std::array<std::pair<const char *, const char *>, 4> Assassin = {{
        {"FireMagic", Engine::trNoop("Combat").data()},
        {"AirMagic", Engine::trNoop("Subtlety").data()},
        {"WaterMagic", Engine::trNoop("Poisons").data()},
        {"EarthMagic", Engine::trNoop("Assassination").data()},
    }};
    // Dragons fight with Fangs and wear Scales (zzClasses.lua dragonSkill).
    static const std::array<std::pair<const char *, const char *>, 2> Dragon = {{
        {"Unarmed", Engine::trNoop("Fangs").data()}, {"Dodging", Engine::trNoop("Scales").data()},
    }};
    const std::string line = mawClassLine(character.className);
    const std::string canonical = canonicalSkillName(skillName);

    if (line == "death_knight")
    {
        for (const auto &[skill, name] : DeathKnight)
        {
            if (canonical == skill)
            {
                return name;
            }
        }
    }
    else if (line == "assassin")
    {
        for (const auto &[skill, name] : Assassin)
        {
            if (canonical == skill)
            {
                return name;
            }
        }
    }
    else if (mawIsDragon(character))
    {
        for (const auto &[skill, name] : Dragon)
        {
            if (canonical == skill)
            {
                return name;
            }
        }
    }

    return nullptr;
}

namespace
{
// Fire 1-11, Air 12-22, Water 23-33, Earth 34-44: a spell's school and its tier 1-11 in it.
std::pair<size_t, int> elementalSchoolAndTier(uint32_t spellId)
{
    return {(spellId - 1) / 11, int((spellId - 1) % 11) + 1};
}
}

bool mawElementalistOffensiveSpell(uint32_t spellId)
{
    static constexpr std::array<uint32_t, 19> Offensive = {
        2, 6, 7, 9, 10, 11, 15, 18, 20, 22, 24, 26, 29, 32, 37, 39, 41, 43, 44,
    };
    return std::find(Offensive.begin(), Offensive.end(), spellId) != Offensive.end();
}

double mawElementalistProgress(uint32_t spellId, int monsterLevel, int partyCount, bool insanity)
{
    // MAW's area spells of the four elements (aoespells, SP:2094) but Sparks and Poison Spray.
    static constexpr std::array<uint32_t, 9> AreaSpells = {6, 7, 8, 9, 10, 22, 32, 41, 43};

    if (spellId < 1 || spellId > 44)
    {
        return 0;
    }

    const int tier = elementalSchoolAndTier(spellId).second;
    double progress = std::pow(tier, 1.5) * std::sqrt(std::max(1, monsterLevel))
        * (insanity ? 1.0 : std::sqrt(std::max(1, partyCount)));

    if (std::find(AreaSpells.begin(), AreaSpells.end(), spellId) != AreaSpells.end())
    {
        progress /= 3;
    }

    return progress;
}

namespace
{
// The casting progress each tier of a school needs (SP:1650-1660).
constexpr std::array<double, 11> ElementalistThresholds = {
    0, 0, 500, 1500, 5000, 10000, 20000, 40000, 80000, 160000, 320000,
};
}

double mawElementalistNextSpellPercent(double progress)
{
    for (size_t tier = 1; tier < ElementalistThresholds.size(); ++tier)
    {
        if (progress < ElementalistThresholds[tier])
        {
            const double low = ElementalistThresholds[tier - 1];
            return 100 * (progress - low) / (ElementalistThresholds[tier] - low);
        }
    }

    return 100;
}

std::optional<uint32_t> mawElementalistNextSpell(size_t school, double progress)
{
    // A spell of tier t needs the threshold t - 1, so the first threshold not reached opens tier index + 1.
    for (size_t tier = 1; tier < ElementalistThresholds.size(); ++tier)
    {
        if (progress < ElementalistThresholds[tier])
        {
            return uint32_t(school * 11 + tier + 1);
        }
    }

    return std::nullopt;
}

std::vector<uint32_t> mawElementalistKnownSpells(const Character &character, bool insanity)
{
    const std::array<double, 11> &Thresholds = ElementalistThresholds;
    static constexpr std::array<int, 11> Masteries = {1, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4};
    static constexpr std::array<const char *, 4> Schools = {"FireMagic", "AirMagic", "WaterMagic", "EarthMagic"};
    static constexpr std::array<uint32_t, 4> AlwaysKnown = {2, 15, 24, 37};
    std::vector<uint32_t> known(AlwaysKnown.begin(), AlwaysKnown.end());

    for (uint32_t spellId = 1; spellId <= 44; ++spellId)
    {
        const auto [school, tier] = elementalSchoolAndTier(spellId);
        const CharacterSkill *pSkill = character.findSkill(Schools[school]);
        const int mastery = pSkill != nullptr ? int(pSkill->mastery) : 0;
        const int required = insanity && spellId == 19 ? 4 : Masteries[size_t(tier - 1)];

        if (mastery >= required && character.rulesetState.elementalProgress[school] >= Thresholds[size_t(tier - 1)]
            && std::find(known.begin(), known.end(), spellId) == known.end())
        {
            known.push_back(spellId);
        }
    }

    return known;
}
}
