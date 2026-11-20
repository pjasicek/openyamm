#pragma once

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
// One spell's text under MAW: each part replaces the spell table's; a mastery line set to "" is not shown.
struct MawSpellTextEntry
{
    std::optional<std::string> name;
    std::optional<std::string> description;
    // Novice to Grandmaster.
    std::array<std::optional<std::string>, 4> masteryLines;
};

// One skill's popup text under MAW: `append` adds a paragraph to the skill table's description, `description` replaces
// it; mastery lines replace the table's, where {table} stands for the table's own line.
struct MawSkillTextEntry
{
    std::optional<std::string> description;
    std::optional<std::string> append;
    std::array<std::optional<std::string>, 4> masteryLines;
};

// MAW's spell names, spellbook texts and skill popups (rulesets/maw/data/texts.yml), with placeholders such as {dice}
// that the rules fill with the character's numbers. A class line (death_knight, assassin, ...) may give its spells and
// school skills their own text, part by part over the ruleset's.
class MawTextData
{
public:
    bool loadFromYaml(const std::string &text, std::string &errorMessage);

    // The text of a spell for a class line: the line's parts first, then the ruleset's; nothing when neither has one.
    std::optional<MawSpellTextEntry> find(const std::string &classLine, uint32_t spellId) const;
    // Every spell the file describes, for checks.
    std::vector<uint32_t> spellIds() const;
    std::vector<uint32_t> classSpellIds(const std::string &classLine) const;
    // A skill's popup text for a class line, the line's parts over the ruleset's; nothing when neither has one.
    std::optional<MawSkillTextEntry> findSkill(const std::string &classLine, const std::string &canonicalSkill) const;
    // A character stat's popup text (Might, HitPoints, ArmorClass...), like a skill's without mastery lines.
    const MawSkillTextEntry *findStat(const std::string &statName) const;
    // An item's description by item id (potions, with placeholders for the numbers at their power), or of a kind of
    // item ("gem"); null for none.
    const std::string *findItemText(uint32_t itemId) const;
    const std::string *findItemKindText(const std::string &kind) const;

private:
    std::unordered_map<uint32_t, MawSpellTextEntry> m_spells;
    std::unordered_map<std::string, std::unordered_map<uint32_t, MawSpellTextEntry>> m_classSpells;
    std::unordered_map<std::string, MawSkillTextEntry> m_skills;
    std::unordered_map<std::string, std::unordered_map<std::string, MawSkillTextEntry>> m_classSkills;
    std::unordered_map<std::string, MawSkillTextEntry> m_stats;
    std::unordered_map<uint32_t, std::string> m_items;
    std::unordered_map<std::string, std::string> m_itemKinds;
};

// Fills {name}, {name*factor} and {name:1} (one decimal) from the values and {name} from the words; a name without a
// value stays as written. Colour tags become Might and Magic's inline colour codes: <good> green, <bad> red, <value>
// yellow, <mana> blue, </> back to the line's own colour.
std::string mawFillText(
    const std::string &text,
    const std::unordered_map<std::string, double> &values,
    const std::unordered_map<std::string, std::string> &words = {});
}
