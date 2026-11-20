#pragma once

#include "game/party/SkillData.h"

#include <cstdint>
#include <optional>
#include <string>

namespace OpenYAMM::Game
{
struct Character;
struct InventoryItem;
struct ItemDefinition;
enum class PotionPool : uint8_t;

// What potions are brewed from and how strong their effects are where that is code rather than potion_effects.yml
// (devdocs/maw/HANDOFF.md §3.5). This class is the Standard MMMerge rules; a ruleset that brews differently derives
// from it.
class PotionRules
{
public:
    virtual ~PotionRules() = default;

    // What a reagent adds to a bottle besides the alchemist's Alchemy level. Standard: the reagent table's power
    // (Mod1).
    virtual int reagentPower(
        const ItemDefinition &reagentDefinition,
        const InventoryItem &reagent,
        SkillMastery alchemyMastery,
        uint32_t alchemyLevel) const;
    // The HP or SP pool a character of this level is expected to have, for pool_share amounts. Standard: 0.
    virtual double estimatedPool(PotionPool pool, int level) const;
    // The Alchemy level the alchemist mixes with. Standard: the trained level plus item and follower bonuses.
    virtual uint32_t mixingAlchemyLevel(const Character &alchemist) const;
    // The power of a potion mixed with a catalyst, from the target's and the held item's power. Standard: the held
    // item's, the stronger of the two when both are catalysts.
    virtual int catalystMixPower(
        int targetPower,
        int heldPower,
        bool bothCatalysts,
        SkillMastery alchemyMastery,
        uint32_t alchemyLevel) const;
    // The status text when a potion can do nothing more for its drinker (a stat potion's limit reached). Standard:
    // none, the item's "can not be used that way".
    virtual std::optional<std::string> noBenefitText() const;
    // Whether a potion's copy of an aura (potion_effects.yml aura_buff) at this power would count, so an upkeep drink
    // is worth it. MAW: only the stronger of it and the party's aura counts. Standard has no aura potions: true.
    virtual bool potionAuraCounts(uint32_t spellId, int power) const;
};

const PotionRules &standardPotionRules();
}
