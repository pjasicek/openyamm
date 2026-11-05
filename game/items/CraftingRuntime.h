#pragma once

#include "game/party/Party.h"
#include "game/rules/CraftingRules.h"

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class ItemTable;

// Where a party item is: in one of a member's bags (InventoryBags), or worn.
struct CraftItemRef
{
    size_t memberIndex = 0;
    bool worn = false;
    uint8_t gridX = 0;
    uint8_t gridY = 0;
    EquipmentSlot slot = EquipmentSlot::MainHand;
    uint8_t bag = 0;

    bool operator==(const CraftItemRef &) const = default;
};

// An item the Crafting tab lists (equipment, and potions an Endless Potion refills).
struct CraftTargetEntry
{
    CraftItemRef ref;
    InventoryItem item;
};

// Identical materials as one cell: the same item and state (a gem tier, a charged orb, a potion's power).
struct CraftMaterialKey
{
    uint32_t itemId = 0;
    uint16_t state = 0;
    uint16_t power = 0;

    bool operator==(const CraftMaterialKey &) const = default;
};

struct CraftMaterialEntry
{
    CraftMaterialKey key;
    InventoryItem item;
    std::vector<CraftItemRef> refs;
};

// A crafting step planned on copies: the preview shows it and applying commits it.
struct CraftPlan
{
    CraftItemRef target;
    // The first step's result (its reason when nothing is possible); with several applications, `item` is the end
    // state.
    CraftResult result;
    InventoryItem item;
    uint32_t applications = 0;
    std::vector<CraftItemRef> materialsUsed;
    // Gems used by tier, for a batch.
    std::vector<std::pair<uint32_t, uint32_t>> gemsUsed;
};

// Combining gems: `count` of a tier make one of the next; a cascade climbs from the lowest tier.
struct GemCombinePlan
{
    struct Step
    {
        uint32_t fromItemId = 0;
        uint32_t toItemId = 0;
        uint32_t merges = 0;
    };

    std::vector<Step> steps;
};

struct CraftingTables
{
    const ItemTable *pItemTable = nullptr;
    const StandardItemEnchantTable *pStandardEnchantTable = nullptr;
    const SpecialItemEnchantTable *pSpecialEnchantTable = nullptr;
    const PotionEffectTable *pPotionEffects = nullptr;
};

// The Workbench's crafting over the party's items (devdocs/maw/CRAFTING_BENCH_DESIGN.md §6): materials are counted
// across every member's bags, targets may be worn, and every step is the rules' CraftingRules::craft on copies.
class CraftingRuntime
{
public:
    static std::optional<InventoryItem> itemAt(const Party &party, const CraftItemRef &ref);
    static std::vector<CraftTargetEntry> collectTargets(const Party &party, const CraftingTables &tables);
    static std::vector<CraftMaterialEntry> collectMaterials(const Party &party, const CraftingRules &rules);
    static CraftMaterialKey materialKey(const InventoryItem &item);

    // Up to `maxApplications` steps of the material on the target while each is possible, using further identical
    // materials; with `cheapestGems` a gem step uses the lowest tier (up to the chosen one) that still raises the
    // item. Steps that need confirmation or change the material run once. `choice` is the player's pick when the step
    // offers several (CraftResult::choices).
    static CraftPlan plan(
        const Party &party,
        const CraftItemRef &target,
        const CraftMaterialKey &material,
        uint32_t maxApplications,
        bool cheapestGems,
        size_t choice,
        const CraftingRules &rules,
        const CraftingTables &tables);
    // Plans again and commits: materials used up, the target written back, a changed material or the Mirror's copy
    // returned to the party. False when nothing was possible. An item without room in any bag is returned in
    // `overflow` for the cursor.
    static bool apply(
        Party &party,
        const CraftItemRef &target,
        const CraftMaterialKey &material,
        uint32_t maxApplications,
        bool cheapestGems,
        size_t choice,
        const CraftingRules &rules,
        const CraftingTables &tables,
        CraftPlan &applied,
        std::optional<InventoryItem> &overflow);

    // How many merges of this gem the party can make now; with `cascade`, the whole climb from the lowest tier.
    static GemCombinePlan planCombine(const Party &party, uint32_t gemItemId, bool cascade, const CraftingRules &rules);
    static bool combine(
        Party &party,
        const GemCombinePlan &plan,
        const CraftingRules &rules,
        const ItemTable &itemTable);
};
}
