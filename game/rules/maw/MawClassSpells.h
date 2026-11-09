#pragma once

#include "game/party/SkillData.h"
#include "game/rules/SpellbookSkin.h"

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct Character;

// A spell of a class that has its own spell list (devdocs/maw/data/spells.yml class_variants): Death Knights and the
// reworked Thief line know these by school mastery instead of from spell books, at fixed costs.
struct MawClassSpell
{
    uint32_t spellId = 0;
    const char *pName = "";
    // The school skill that teaches it, and the mastery it takes (0: known even without the skill).
    const char *pSchool = "";
    int mastery = 0;
    // Spell points (energy for Assassins) and combo points a cast costs.
    int cost = 0;
    int comboCost = 0;
    // A damage spell's share of a weapon blow by the school's mastery, Novice to Grandmaster; 0 for none.
    std::array<double, 4> damage = {};
    // A switch the caster turns on and off, paying its cost on every melee hit instead.
    bool toggle = false;
};

// The class's own spells, or nothing for a class that learns from spell books.
const std::vector<MawClassSpell> &mawClassSpells(const std::string &className);
const MawClassSpell *mawClassSpell(const std::string &className, uint32_t spellId);
// The spells the character's school masteries give, for a class with its own list.
std::vector<uint32_t> mawKnownClassSpells(const Character &character);
// The Elementalist's offensive spells (Fire, Air, Water and Earth damage spells, MCC:45-61), and the progress a hit
// of one adds to its school: tier^1.5 x monster level^0.5 x party size^0.5, a third for area spells but Sparks and
// Poison Spray (DM:152-195). Insanity drops the party term.
bool mawElementalistOffensiveSpell(uint32_t spellId);
double mawElementalistProgress(uint32_t spellId, int monsterLevel, int partyCount, bool insanity);
// The Elementalist's spells of the four elements: Fire Bolt, Sparks, Poison Spray and Deadly Swarm always, every other
// tier once its school's progress and mastery reach it (MCC:43, DM:155).
std::vector<uint32_t> mawElementalistKnownSpells(const Character &character, bool insanity);
// How far a school's casting progress is from its last spell threshold to the next, in percent; 100 past the last.
double mawElementalistNextSpellPercent(double progress);
// The spell a school's casting progress reaches next (school 0-3: Fire, Air, Water, Earth); none past the last.
std::optional<uint32_t> mawElementalistNextSpell(size_t school, double progress);

// The class's own spellbook look (Death Knight Frost, Blood and Unholy pages; Assassin Combat, Subtlety, Poisons and
// Assassination pages), or null for a class with the standard book. Art: level_generation/ui/
// maw_class_spellbooks_20261108 (devdocs/maw/CLASS_SPELLBOOKS.md).
const SpellbookSkin *mawClassSpellbookSkin(const std::string &className);

// A class school's own name (Death Knight Frost, Blood, Unholy; Assassin Combat, Subtlety, Poisons,
// Assassination; a dragon-race character's Fangs and Scales), or nothing.
const char *mawClassSchoolName(const Character &character, const std::string &skillName);
}
