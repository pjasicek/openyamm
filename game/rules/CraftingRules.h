#pragma once

#include "game/party/Party.h"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class ItemTable;
class PotionEffectTable;
class SpecialItemEnchantTable;
class StandardItemEnchantTable;

struct CraftingContext
{
    const ItemTable *pItemTable = nullptr;
    const StandardItemEnchantTable *pStandardEnchantTable = nullptr;
    const SpecialItemEnchantTable *pSpecialEnchantTable = nullptr;
    const PotionEffectTable *pPotionEffects = nullptr;
    // The level of the character who carries or wears the item.
    int ownerLevel = 1;
    // The option the player picked when the step offers several (CraftResult::choices); past the last, the last.
    size_t choice = 0;
};

// One crafting step worked out on copies (devdocs/maw/CRAFTING_BENCH_DESIGN.md §6): the preview shows it and applying
// commits the same result, since every random choice comes from the item's own craft stream.
struct CraftResult
{
    bool possible = false;
    // Why not, when it is not possible.
    std::string reason;
    // The item after the step.
    InventoryItem target;
    // The material: used up, or changed and kept (a charged orb), or turned into a new item (the Mirror's copy).
    bool materialConsumed = false;
    std::optional<InventoryItem> materialAfter;
    // Something the step destroys that the player may want; they confirm it first.
    std::string confirmation;
    // The step in a few words ("+3 Might, cap 106"); for a hidden outcome, what may happen.
    std::string summary;
    // The player picks what the step does (MAW's Pearl: which enchantment it removes): `choicePrompt` asks, `choices`
    // names each option and `choice` is the one this result made (CraftingContext::choice). Empty with nothing to pick.
    std::string choicePrompt;
    std::vector<std::string> choices;
    size_t choice = 0;
    // A gamble (MAW's element potions): the preview names the possible outcomes, not the one that will happen;
    // `outcome` says what happened, for after the step.
    bool hiddenOutcome = false;
    std::string outcome;
};

// Crafting materials worked on items (MAW's gems, orbs and cubes; devdocs/maw/CRAFTING.md). This class is the
// Standard rules, which have none; a ruleset with crafting derives from it.
class CraftingRules
{
public:
    virtual ~CraftingRules() = default;

    // Whether the Workbench has a Crafting tab.
    virtual bool hasCrafting() const;
    // Whether the item works on other items on the Workbench (a material or an item-target potion).
    virtual bool isMaterial(const InventoryItem &item) const;
    // Whether the Workbench lists the item as a target besides equipment and rechargeable potions (MAW: dimension
    // maps). Standard: no.
    virtual bool isExtraTarget(const InventoryItem &item) const;
    virtual CraftResult craft(
        const InventoryItem &target,
        const InventoryItem &material,
        const CraftingContext &context) const;
    // What a material does, in a few words ("Gem: raise the weaker enchantment"); empty for anything else.
    virtual std::string materialAction(uint32_t itemId) const;
    // A material's description in its inspect popup when the rules write one (MAW: a gem's tier and caps); nothing for
    // the item table's notes.
    virtual std::optional<std::string> materialDescription(const InventoryItem &item) const;

    // Gems: the tier of a gem (0 for anything else), how many of a tier make one of the next, and that next gem
    // (0 when there is none).
    virtual int gemTier(uint32_t itemId) const;
    virtual int gemCombineCount() const;
    virtual uint32_t combinedGem(uint32_t itemId) const;
    // What crafting can still do to an item, for the Workbench's item panel (MAW: its power against the Crafting
    // Cube's cap, how far gems raise each enchantment, what the Hourglass and the Eye of Void would add). Standard:
    // nothing.
    virtual std::vector<std::string> craftOutlook(const InventoryItem &target, const CraftingContext &context) const;
};

const CraftingRules &standardCraftingRules();
}
