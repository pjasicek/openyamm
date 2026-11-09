#pragma once

#include <cstdint>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

namespace YAML
{
class Node;
}

namespace OpenYAMM::Game
{
// One artifact a MAW drop can turn into (rulesets/maw/data/items.yml, devdocs/maw/data/artifacts.yml).
struct MawArtifact
{
    enum class Base : uint8_t
    {
        // A top-rung weapon of its kind at the party's level.
        Weapon,
        // Printed armour class plus the reference armour class x power / 40.
        Armor,
        // The printed armour class only.
        Flat,
    };

    uint32_t itemId = 0;
    // Slots in MAW's drop list (the pick favours artifacts found less often per slot).
    int dropWeight = 1;
    Base base = Base::Weapon;
    double slotMultiplier = 1;
    bool twoHanded = false;
    // The weapon ladder rung it counts as (6, the top, but for a few ladder artifacts).
    double rung = 6;
    int diceCount = 1;
    // A weapon's flat damage as Staff, Sword and Spear guard by it: its printed one after MAW's artifact upscaler.
    int guardBase = 0;
    int printedArmorClass = 0;
    int referenceArmorClass = 0;
    // Stat and skill budgets in units of one perfect Epic enchant at the party's level; flat numbers outside it.
    std::vector<std::pair<std::string, double>> stats;
    std::vector<std::pair<std::string, double>> skills;
    std::vector<std::pair<std::string, double>> flat;
    // On a hit (artifactOnHit, zzzMaw_Artifacts.lua): extra damage of `onHitType` worth `onHitDamage` times the
    // range of the reference enchantment at the artifact's level, doubled (or more) against the listed monster kinds;
    // Slow on the target.
    std::string onHitType;
    double onHitDamage = 0;
    std::vector<std::pair<std::string, double>> onHitVersus;
    bool onHitSlow = false;
    // Schools whose skill it raises by half the trained level (artifactSpellBonus); its attack delay multiplier.
    std::vector<std::string> spellBonus;
    double attackDelayMultiplier = 1;
};

// A base item MAW rolls (the enchantable equipment of the three games): its rung in its family (1-6), the weapon dice
// count and hands, and the armour class at item power 0 and of the family's top rung.
struct MawBaseItem
{
    double rung = 3.5;
    int diceCount = 0;
    bool twoHanded = false;
    int baseArmorClass = 0;
    int referenceArmorClass = 0;
    // A world's item a step stronger than its MM6-MM8 peers (MM9's: up to 1.15): its weapon damage and armour.
    double strength = 1;
};

// The MAW ruleset's item data: base items, legendary affix texts and the artifacts.
class MawItemData
{
public:
    bool loadFromYaml(const std::string &text, std::string &errorMessage);
    // A world's base items (rulesets/maw/worlds/<world>/item_bases.yml, written by tools/maw/mm9_balance.py from
    // its balance.yml), after items.yml: `bases` as there, with an optional sixth value, the strength. An id items.yml
    // or another world already gives is an error.
    bool loadWorldBases(const std::string &text, std::string &errorMessage);
    const std::vector<MawArtifact> &artifacts() const;
    const MawArtifact *artifact(uint32_t itemId) const;
    // Null for anything but a base item MAW rolls.
    const MawBaseItem *baseItem(uint32_t itemId) const;
    // The tooltip text of a legendary affix (MAW id 11-35); empty for an unknown id.
    const std::string &legendaryAffixText(int affixId) const;

private:
    bool loadBases(const YAML::Node &bases, bool worldBases, std::string &errorMessage);

    std::vector<MawArtifact> m_artifacts;
    std::unordered_map<uint32_t, size_t> m_artifactIndex;
    std::unordered_map<int, std::string> m_legendaryAffixTexts;
    std::unordered_map<uint32_t, MawBaseItem> m_baseItems;
};

inline constexpr int MawFirstLegendaryAffix = 11;
inline constexpr int MawLegendaryAffixCount = 25;
}
