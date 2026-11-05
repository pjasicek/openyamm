#pragma once

#include "game/party/CharacterState.h"
#include "game/party/SkillData.h"

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
class ClassSkillTable;
class IGameplayWorldRuntime;
class ItemTable;
class Party;
struct Character;
struct IdentifyMonsterReveal;

// A skill's right-click popup: its description and its Novice to Grandmaster lines (an empty line is not shown).
struct SkillTooltipText
{
    std::string description;
    std::array<std::string, 4> masteryLines;
    // A paragraph after the mastery lines and the skill bonus (MAW's trainer hint); may carry colour codes.
    std::string footer;
};

// A character's attack, damage, armour class and resistance as rules that compute them from items and skills
// themselves see them (MAW's itemStats, devdocs/maw/COMBAT_SPEC.md §3). Attacks and damage are final; the armour class
// is the items' and skills' part (buffs and enchantments add theirs); resistances add to the items'.
struct CharacterCombatRows
{
    int meleeAttack = 0;
    int meleeMinimumDamage = 0;
    int meleeMaximumDamage = 0;
    int rangedAttack = 0;
    int rangedMinimumDamage = 0;
    int rangedMaximumDamage = 0;
    // A blaster shot's range when the rules set one (MAW fires blasters with the melee rows); else the engine's.
    std::optional<std::pair<int, int>> blasterDamage;
    int armorClass = 0;
    CharacterResistanceSet resistances;
};

// A row of the character's stats page as the rules relabel it (MAW: Condition shows the powers, Quick Spell Vitality).
struct CharacterStatRowText
{
    std::string label;
    std::string value;
    // The title of the row's popup (empty: the stat's own).
    std::string popupTitle;
};

// What a resistance row of the stats page adds before its value (MAW: the share of hits it takes off).
struct CharacterResistanceCut
{
    double percent = 0;
    // An item's resistance enchantment raises it (MAW shows the row green).
    bool raisedByItem = false;
    // The row label's colour as 0xRRGGBB (MAW: the element's); 0 keeps the page's.
    uint32_t labelRgb = 0;
};

// The character's actual statistics the rows read.
struct CharacterStatValues
{
    int might = 0;
    int accuracy = 0;
    int luck = 0;
};

// What raising a skill costs, as the skills page shows it.
struct SkillRaiseCost
{
    uint32_t cost = 0;
    // The raise's cost without sharing: the new level.
    uint32_t fullCost = 0;
    // The other skills that share the raise and lower its cost (display names).
    std::vector<std::string> sharedWith;
};

// How skills are raised and taught (devdocs/maw/HANDOFF.md §3.5): the point cost of a raise, masteries granted without
// a teacher, and a teacher's requirement and price. This class is the Standard MMMerge rules; a ruleset that handles
// skills differently derives from it.
class SkillRules
{
public:
    virtual ~SkillRules() = default;

    // The skill's name on the character's skill sheet (MAW: Death Knights and Assassins rename their schools).
    virtual std::string skillDisplayName(const Character &character, const std::string &canonicalSkill) const;
    // The skill points raising the skill by one costs. Standard: the new level.
    virtual uint32_t skillRaiseCost(const Character &character, const std::string &canonicalSkill) const;
    // The highest base level the skill can be raised to, or nothing for no limit (Standard).
    virtual std::optional<uint32_t> skillLevelCap(const std::string &canonicalSkill) const;
    // Whether the character has the skill below its cap and the points for its next raise.
    bool canRaiseSkill(const Character &character, const std::string &canonicalSkill) const;
    // After a raise: masteries the rules grant without a teacher. Returns a status text, or nothing. Standard: none.
    virtual std::string afterSkillRaised(
        Character &character,
        const std::string &canonicalSkill,
        const ClassSkillTable *pClassSkillTable) const;
    // Skills a house teaches besides its own list (MAW: Cover at training halls, Mana Shield and Enlightenment at
    // magic shops). Standard: none.
    virtual std::vector<std::string> extraHouseSkills(const std::string &houseType) const;
    // Skills that become Expert, Master and Grandmaster at these base levels with no teacher (MAW: Cover, Mana
    // Shield, Enlightenment and Retaliation), for the journal's trainer finder. Standard: none.
    virtual std::vector<std::pair<std::string, std::array<uint32_t, 3>>> teacherlessMasteryLadders() const;
    // The base skill level a teacher wants for a mastery. Standard: 4, 7 and 10.
    virtual uint32_t masteryRequiredLevel(const std::string &canonicalSkill, SkillMastery mastery) const;
    // What a teacher asks for a mastery. Standard: the topic's or the default price, `standardCost`.
    virtual int masteryTeacherCost(
        const Character &character,
        const std::string &canonicalSkill,
        SkillMastery mastery,
        int standardCost) const;

    // What resetting the character's skills costs, or nothing when the rules have no reset (Standard).
    virtual std::optional<int> skillResetCost(const Character &character) const;
    // Lowers the character's skills and gives their points back (MAW's respec); false when the rules have no reset.
    virtual bool resetSkills(Character &character) const;

    // After items and buffs: the rules' own bonuses to the primary stats (MAW: the aura stat percents, and what a
    // potion's copy of a flat aura adds over the party's). Standard: none.
    virtual void applyStatBonuses(Character &member) const;
    // After the stats: the rules' own bonuses to maximum HP and SP (MAW: Endurance and Bodybuilding percents,
    // Enlightenment). Standard: none.
    virtual void applyResourceBonuses(Character &member) const;
    // The character's combat rows, or nothing for Standard's sum of item and skill bonuses.
    virtual std::optional<CharacterCombatRows> combatRows(
        const Character &character,
        const ItemTable *pItemTable,
        const CharacterStatValues &stats) const;

    // HP per real second the Regeneration skill gives. Standard: level x mastery per five game minutes.
    virtual float regenerationHealthPerSecond(const Character &member) const;
    // SP the Meditation skill gives on each five-minute tick. Standard: mastery + skill / 10.
    virtual int meditationSpellPointsPerTick(const Character &member) const;
    // Each frame of play: a ruleset's own regeneration (MAW's, faster out of combat). Standard: none.
    // Whether the skill bonuses of hired NPC followers add up (Standard, MMerge) or only the strongest counts (MAW,
    // NPCFollowersSkills.lua:40-48).
    virtual bool followerSkillBonusesStack() const;
    // A hired follower's bonus to a skill, given the MMerge table's amount (Standard: the table's), and whether a
    // member gains it only once they have learned the skill (Standard: no).
    virtual int followerSkillBonus(uint32_t professionId, const std::string &canonicalSkill, int tableBonus) const;
    virtual bool followerSkillBonusNeedsSkill(const std::string &canonicalSkill) const;
    virtual void updateRegeneration(Party &party, const IGameplayWorldRuntime &world, float deltaSeconds) const;
    // What Identify Monster tells the party about a monster of this level (its ruleset level, else its table level).
    // Standard: the best able member's skill and mastery against the level.
    virtual IdentifyMonsterReveal identifyMonsterReveal(const Party &party, int monsterLevel) const;
    // A skill's popup for a character in the party, from the skill table's own text (MAW: its texts with the
    // character's numbers). Standard: the table's text.
    virtual SkillTooltipText skillTooltip(
        const Party &party,
        const Character &character,
        const std::string &canonicalSkill,
        const SkillTooltipText &table) const;
    // A character stat's popup (Might, HitPoints, ArmorClass...) from the stat table's text (MAW: its live numbers).
    // Standard: the table's text, and for a primary stat or a resistance what its value gives in plain numbers.
    virtual std::string statTooltip(
        const Party &party,
        const Character &character,
        const std::string &statName,
        const std::string &table) const;
    // A stats page row's label and value when the rules show something else there (MAW: Melee Power in the Condition
    // row, Ranged Power in the Quick Spell row), or for the two rows they may add ("SpellPower" and "Vitality": MAW's
    // Spell Power and Vitality; "Bow off" in "Shoot" and "RangedDamage" with its Bow preference off). Standard: none.
    virtual std::optional<CharacterStatRowText> statRowText(
        const Party &party,
        const Character &character,
        const std::string &statName) const;
    // statRowText for the four rows at once: "Condition", "QuickSpell", "SpellPower" and "Vitality" (MAW works them
    // all out from one report). Standard: statRowText for each.
    virtual std::array<std::optional<CharacterStatRowText>, 4> statRows(
        const Party &party,
        const Character &character) const;
    // Whether the stats page's Condition box shows statRowText's four rows ("Condition", "QuickSpell", "SpellPower",
    // "Vitality") in tighter rows (MAW). Standard: false, its two rows.
    virtual bool compactStatPowerRows() const;
    // The share of hits a resistance row ("FireResistance" ... "BodyResistance") takes off, shown inline (MAW,
    // zzMaw-Stats.lua:870-897). Standard: none.
    virtual std::optional<CharacterResistanceCut> resistanceCut(
        const Party &party,
        const Character &character,
        const std::string &statName) const;
    // resistanceCut for the six rows at once, Fire, Air, Water, Earth, Mind and Body (MAW: from one character sheet).
    // Standard: resistanceCut for each.
    virtual std::array<std::optional<CharacterResistanceCut>, 6> resistanceCuts(
        const Party &party,
        const Character &character) const;
    // The colour (0xRRGGBB) of a stats page label (Might .. Luck, HitPoints, SpellPoints, ArmorClass); none keeps the
    // layout's. Standard: none.
    virtual std::optional<uint32_t> statLabelRgb(const std::string &statName) const;
    // A stats page value as the rules print it (MAW shortens every number of 10000 or more to 3 digits and K/M/B).
    // Standard: the text as it is.
    virtual std::string statValueText(const std::string &text) const;
    // A mastery teacher's speech with the requirement and price the rules ask (MAW rewrites the speech's numbers).
    // Standard: the speech as written.
    virtual std::string teacherSpeech(
        const std::string &text,
        const std::string &canonicalSkill,
        SkillMastery mastery,
        uint32_t requiredLevel,
        int price) const;
    // The training hall's price multiplier for this character's next level (PriceCalculator::trainingPrice), the
    // hall's own otherwise. Standard: the hall's.
    virtual float trainingPriceMultiplier(const Character &trainee, float houseMultiplier) const;
    // The next raise's cost shown beside the skill on the skills page and on hover (MAW, whose shared schools make it
    // differ from the level: every skill below its cap). Standard: none, the level says it.
    virtual std::optional<SkillRaiseCost> skillRaiseCostDetail(
        const Character &character,
        const std::string &canonicalSkill) const;
};

const SkillRules &standardSkillRules();
}
