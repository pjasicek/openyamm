#pragma once

#include "game/rules/CraftingRules.h"
#include "game/rules/maw/MawCraftingData.h"
#include "game/rules/maw/MawItemFormulas.h"

#include <random>

namespace OpenYAMM::Game
{
class MawRules;
struct ItemDefinition;

// MAW's crafting (devdocs/maw/CRAFTING.md §3-4, rulesets/maw/data/crafting.yml) with the Workbench's fixes
// (CRAFTING_BENCH_DESIGN.md §12): every random choice comes from the item's craft stream, so a preview is exact;
// failures say why; levels are checked against the item's owner.
class MawCraftingRules : public CraftingRules
{
public:
    explicit MawCraftingRules(MawRules &rules);

    bool hasCrafting() const override;
    bool isMaterial(const InventoryItem &item) const override;
    // Dimension maps (CRAFTING.md §5).
    bool isExtraTarget(const InventoryItem &item) const override;
    CraftResult craft(
        const InventoryItem &target,
        const InventoryItem &material,
        const CraftingContext &context) const override;
    std::string materialAction(uint32_t itemId) const override;
    // A gem's tier, its caps on each class of item and how gems combine (Tooltip.lua:141-163).
    std::optional<std::string> materialDescription(const InventoryItem &item) const override;

    int gemTier(uint32_t itemId) const override;
    int gemCombineCount() const override;
    uint32_t combinedGem(uint32_t itemId) const override;
    // MAW's Alt view (Tooltip.lua:295-340, 471-474), here where it is used: "Item Bonus Power: x/cap", each base
    // enchantment's reach with the strongest gem, and the exact step the Hourglass and the Eye of Void would make
    // (from the item's own craft stream, as their preview does).
    std::vector<std::string> craftOutlook(const InventoryItem &target, const CraftingContext &context) const override;

    // The strongest enchantment of a Primordial drop at this difficulty, the gems' cap at tier 20 on a x1 item:
    // round(ceil(100 x difficulty power) x 1.25), 125 up to Hell, 131 Nightmare, 138 Doom, 150 Insanity and Madness.
    int primordialMaxStrength() const;
    // GetGemCap: r = round(tier / 20 x primordialMax); a skill enchantment ceil(max(sqrt(r), r / 10)); times the slot
    // multiplier, rounded up.
    int gemCap(int tier, double slotMultiplier, bool skillEnchant) const;

private:
    // The Eye and the Hourglass activate a map's next affix, the Emerald adds 5 power, the Crafting Cube moves it to
    // another cleared place of the same kind.
    CraftResult craftDimensionMap(CraftResult result, const InventoryItem &material, MawCraftOperation operation) const;
    CraftResult raiseEnchant(CraftResult result, const ItemDefinition &definition, int tier,
        const CraftingContext &context) const;
    CraftResult addSpecial(CraftResult result, const ItemDefinition &definition, const InventoryItem &material,
        const CraftingContext &context, std::mt19937 &rng) const;
    CraftResult addSecondEnchant(CraftResult result, const ItemDefinition &definition,
        const CraftingContext &context, std::mt19937 &rng) const;
    CraftResult refineQuality(CraftResult result, const ItemDefinition &definition,
        const CraftingContext &context) const;
    CraftResult duplicateItem(CraftResult result, const ItemDefinition &definition, uint32_t streamSeed) const;
    CraftResult upgradeBaseType(CraftResult result, const ItemDefinition &definition,
        const CraftingContext &context) const;
    // Removes the enchantment the player picks (context.choice), each named as the inspect popup reads it.
    CraftResult removeEnchant(
        CraftResult result,
        const ItemDefinition &definition,
        const CraftingContext &context) const;
    CraftResult transferLegendaryAffix(CraftResult result, const InventoryItem &material) const;
    CraftResult transferCelestial(CraftResult result, const InventoryItem &material) const;
    CraftResult addPotionCharges(CraftResult result, const InventoryItem &material,
        const CraftingContext &context) const;
    CraftResult addItemPower(CraftResult result, const ItemDefinition &definition,
        const CraftingContext &context) const;
    CraftResult addFirstEnchant(CraftResult result, const ItemDefinition &definition, const InventoryItem &material,
        const CraftingContext &context, std::mt19937 &rng) const;

    // The base enchantment slot multiplier of a MAW base item (1 for anything else).
    double slotMultiplier(const ItemDefinition &definition) const;
    // Whether the owner may use the item: its level requirement against the owner's level.
    std::string levelRefusal(const InventoryItem &item, const ItemDefinition &definition,
        const CraftingContext &context) const;

    MawRules &m_rules;
};

// What a crafted MAW item is (MawItemRarity): Celestial, else Legendary with an affix, else the Ancient or Primordial
// tier it dropped at, else by its enchantment count (Uncommon one, Rare two, Epic with a special).
MawRarity mawCraftedRarity(const InventoryItem &item, MawRarity droppedRarity);
}
