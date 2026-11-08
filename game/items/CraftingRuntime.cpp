#include "game/items/CraftingRuntime.h"
#include "engine/Localization.h"

#include "game/items/InventoryBags.h"
#include "game/items/ItemEnchantRuntime.h"
#include "game/items/ItemGenerator.h"
#include "game/rules/CraftingRules.h"
#include "game/rules/GameRules.h"
#include "game/tables/ItemTable.h"
#include "game/tables/PotionEffectTable.h"

#include <algorithm>
#include <array>
#include <functional>

namespace OpenYAMM::Game
{
namespace
{
constexpr std::array<EquipmentSlot, 16> WornSlots = {
    EquipmentSlot::MainHand, EquipmentSlot::OffHand, EquipmentSlot::Bow, EquipmentSlot::Armor, EquipmentSlot::Helm,
    EquipmentSlot::Belt, EquipmentSlot::Cloak, EquipmentSlot::Gauntlets, EquipmentSlot::Boots, EquipmentSlot::Amulet,
    EquipmentSlot::Ring1, EquipmentSlot::Ring2, EquipmentSlot::Ring3, EquipmentSlot::Ring4, EquipmentSlot::Ring5,
    EquipmentSlot::Ring6,
};

CraftItemRef packRef(size_t memberIndex, uint8_t bag, const InventoryItem &item)
{
    CraftItemRef ref;
    ref.memberIndex = memberIndex;
    ref.gridX = item.gridX;
    ref.gridY = item.gridY;
    ref.bag = bag;
    return ref;
}

int bagCountOf(const Party &party)
{
    return std::max(1, party.rules().items.bagCount(party));
}

// Every item in the members' bags, member by member and bag by bag, with its reference.
void forEachPackItem(const Party &party, const std::function<void(const CraftItemRef &, const InventoryItem &)> &visit)
{
    const int bagCount = bagCountOf(party);

    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        for (int bag = 0; bag < bagCount; ++bag)
        {
            for (const InventoryItem &item : InventoryBags::itemsInBag(party.members()[memberIndex], uint8_t(bag)))
            {
                visit(packRef(memberIndex, uint8_t(bag), item), item);
            }
        }
    }
}

CraftingContext craftingContext(const Party &party, const CraftItemRef &target, const CraftingTables &tables)
{
    CraftingContext context;
    context.pItemTable = tables.pItemTable;
    context.pStandardEnchantTable = tables.pStandardEnchantTable;
    context.pSpecialEnchantTable = tables.pSpecialEnchantTable;
    context.pPotionEffects = tables.pPotionEffects;
    const Character *pOwner = party.member(target.memberIndex);
    context.ownerLevel = pOwner != nullptr ? int(pOwner->level) : 1;
    return context;
}

// The bag instances of a material, in bag order.
std::vector<CraftItemRef> materialRefs(const Party &party, const CraftMaterialKey &key)
{
    std::vector<CraftItemRef> refs;
    forEachPackItem(party,
        [&refs, &key](const CraftItemRef &ref, const InventoryItem &item)
        {
            if (CraftingRuntime::materialKey(item) == key)
            {
                refs.push_back(ref);
            }
        });
    return refs;
}

// Whether an item of this size fits at a cell of the bag without covering another item.
bool fitsAt(const Character &member, uint8_t bag, const InventoryItem &item, uint8_t gridX, uint8_t gridY)
{
    if (gridX + item.width > Character::InventoryWidth || gridY + item.height > Character::InventoryHeight)
    {
        return false;
    }

    for (uint8_t y = gridY; y < gridY + item.height; ++y)
    {
        for (uint8_t x = gridX; x < gridX + item.width; ++x)
        {
            if (InventoryBags::itemInBagAt(member, bag, x, y) != nullptr)
            {
                return false;
            }
        }
    }

    return true;
}

// Puts an item back into the party: at the cell it came from when it fits, else in its owner's bags, else anyone's;
// false when no bag has room.
bool returnToParty(Party &party, const CraftItemRef &from, const InventoryItem &item)
{
    const Character *pMember = party.member(from.memberIndex);
    std::optional<InventoryItem> replaced;

    if (pMember != nullptr && fitsAt(*pMember, from.bag, item, from.gridX, from.gridY)
        && InventoryBags::placeInBag(
            party, from.memberIndex, from.bag, bagCountOf(party), item, from.gridX, from.gridY, replaced))
    {
        return true;
    }

    return party.tryGrantInventoryItemStartingAt(from.memberIndex, item);
}
}

std::optional<InventoryItem> CraftingRuntime::itemAt(const Party &party, const CraftItemRef &ref)
{
    if (ref.worn)
    {
        return party.equippedItem(ref.memberIndex, ref.slot);
    }

    const Character *pMember = party.member(ref.memberIndex);
    const InventoryItem *pItem =
        pMember != nullptr ? InventoryBags::itemInBagAt(*pMember, ref.bag, ref.gridX, ref.gridY) : nullptr;
    return pItem != nullptr ? std::optional<InventoryItem>(*pItem) : std::nullopt;
}

CraftMaterialKey CraftingRuntime::materialKey(const InventoryItem &item)
{
    return {item.objectDescriptionId, item.rulesetFields.craftState, item.standardEnchantPower};
}

std::vector<CraftTargetEntry> CraftingRuntime::collectTargets(const Party &party, const CraftingTables &tables)
{
    std::vector<CraftTargetEntry> targets;

    if (tables.pItemTable == nullptr)
    {
        return targets;
    }

    const auto isTarget = [&tables, &party](const InventoryItem &item)
    {
        const ItemDefinition *pDefinition = tables.pItemTable->get(item.objectDescriptionId);

        if (pDefinition == nullptr)
        {
            return false;
        }

        if (party.rules().crafting.isExtraTarget(item))
        {
            return true;
        }

        const PotionDefinition *pPotion =
            tables.pPotionEffects != nullptr ? tables.pPotionEffects->find(item.objectDescriptionId) : nullptr;
        return ItemEnchantRuntime::categoryForItem(*pDefinition) != ItemEnchantCategory::None
            || (pPotion != nullptr && pPotion->rechargeable);
    };

    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        for (EquipmentSlot slot : WornSlots)
        {
            const std::optional<InventoryItem> item = party.equippedItem(memberIndex, slot);

            if (item && isTarget(*item))
            {
                CraftItemRef ref;
                ref.memberIndex = memberIndex;
                ref.worn = true;
                ref.slot = slot;
                targets.push_back({ref, *item});
            }
        }
    }

    forEachPackItem(party,
        [&targets, &isTarget](const CraftItemRef &ref, const InventoryItem &item)
        {
            if (isTarget(item))
            {
                targets.push_back({ref, item});
            }
        });
    return targets;
}

std::vector<CraftMaterialEntry> CraftingRuntime::collectMaterials(const Party &party, const CraftingRules &rules)
{
    std::vector<CraftMaterialEntry> materials;

    forEachPackItem(party,
        [&materials, &rules](const CraftItemRef &ref, const InventoryItem &item)
        {
            if (!rules.isMaterial(item))
            {
                return;
            }

            const CraftMaterialKey key = materialKey(item);
            const auto found = std::find_if(
                materials.begin(),
                materials.end(),
                [&key](const CraftMaterialEntry &entry)
                {
                    return entry.key == key;
                });

            if (found != materials.end())
            {
                found->refs.push_back(ref);
            }
            else
            {
                materials.push_back({key, item, {ref}});
            }
        });

    // Gems first by tier, then the rest by item id.
    std::stable_sort(
        materials.begin(),
        materials.end(),
        [&rules](const CraftMaterialEntry &left, const CraftMaterialEntry &right)
        {
            const int leftTier = rules.gemTier(left.key.itemId);
            const int rightTier = rules.gemTier(right.key.itemId);

            if ((leftTier > 0) != (rightTier > 0))
            {
                return leftTier > 0;
            }

            return left.key.itemId < right.key.itemId;
        });
    return materials;
}

CraftPlan CraftingRuntime::plan(
    const Party &party,
    const CraftItemRef &target,
    const CraftMaterialKey &material,
    uint32_t maxApplications,
    bool cheapestGems,
    size_t choice,
    const CraftingRules &rules,
    const CraftingTables &tables)
{
    CraftPlan plan;
    plan.target = target;
    const std::optional<InventoryItem> targetItem = itemAt(party, target);

    if (!targetItem)
    {
        plan.result.reason = Engine::tr("The item is gone");
        return plan;
    }

    plan.item = *targetItem;
    plan.result.target = *targetItem;
    CraftingContext context = craftingContext(party, target, tables);
    context.choice = choice;
    const int chosenTier = rules.gemTier(material.itemId);

    // The material instances still unused, by key; gem batches may draw on the lower tiers.
    std::vector<std::pair<CraftMaterialKey, std::vector<CraftItemRef>>> pools;

    if (cheapestGems && chosenTier > 0)
    {
        for (int tier = 1; tier <= chosenTier; ++tier)
        {
            const uint32_t gemId = material.itemId - uint32_t(chosenTier - tier);
            const CraftMaterialKey key{gemId, 0, 0};
            pools.push_back({key, materialRefs(party, key)});
        }
    }
    else
    {
        pools.push_back({material, materialRefs(party, material)});
    }

    for (uint32_t step = 0; step < std::max(1u, maxApplications); ++step)
    {
        bool applied = false;

        for (auto &[key, refs] : pools)
        {
            if (refs.empty())
            {
                continue;
            }

            const std::optional<InventoryItem> materialItem = itemAt(party, refs.front());
            CraftResult result = rules.craft(plan.item, *materialItem, context);

            if (step == 0)
            {
                plan.result = result;
            }

            if (!result.possible)
            {
                continue;
            }

            // A step that changes the material or wants confirming runs alone.
            if (step > 0 && (!result.confirmation.empty() || result.materialAfter || !result.materialConsumed))
            {
                break;
            }

            plan.item = result.target;
            plan.materialsUsed.push_back(refs.front());
            refs.erase(refs.begin());
            ++plan.applications;
            applied = true;

            if (rules.gemTier(key.itemId) > 0)
            {
                const auto used = std::find_if(
                    plan.gemsUsed.begin(),
                    plan.gemsUsed.end(),
                    [&key](const std::pair<uint32_t, uint32_t> &entry)
                    {
                        return entry.first == key.itemId;
                    });

                if (used != plan.gemsUsed.end())
                {
                    ++used->second;
                }
                else
                {
                    plan.gemsUsed.push_back({key.itemId, 1});
                }
            }

            break;
        }

        if (!applied || !plan.result.confirmation.empty() || plan.result.materialAfter
            || !plan.result.materialConsumed)
        {
            break;
        }
    }

    // The first step's reason stands when nothing ran; otherwise the plan succeeded.
    if (plan.applications > 0)
    {
        plan.result.possible = true;
    }

    return plan;
}

bool CraftingRuntime::apply(
    Party &party,
    const CraftItemRef &target,
    const CraftMaterialKey &material,
    uint32_t maxApplications,
    bool cheapestGems,
    size_t choice,
    const CraftingRules &rules,
    const CraftingTables &tables,
    CraftPlan &applied,
    std::optional<InventoryItem> &overflow)
{
    applied = plan(party, target, material, maxApplications, cheapestGems, choice, rules, tables);
    overflow.reset();

    if (applied.applications == 0)
    {
        return false;
    }

    // A material that stays (a charged orb, the Mirror's copy) goes back where it was.
    const CraftItemRef firstMaterial = applied.materialsUsed.front();

    const int bagCount = bagCountOf(party);

    for (const CraftItemRef &ref : applied.materialsUsed)
    {
        InventoryItem removed;
        InventoryBags::takeFromBag(party, ref.memberIndex, ref.bag, bagCount, ref.gridX, ref.gridY, removed);
    }

    if (target.worn)
    {
        party.replaceEquippedItem(target.memberIndex, target.slot, applied.item);
    }
    else
    {
        Character *pOwner = party.member(target.memberIndex);
        InventoryItem *pItem =
            pOwner != nullptr ? InventoryBags::itemInBagAt(*pOwner, target.bag, target.gridX, target.gridY) : nullptr;
        const bool sameSize = pItem != nullptr && pItem->width == applied.item.width
            && pItem->height == applied.item.height;

        if (sameSize)
        {
            const uint8_t gridX = pItem->gridX;
            const uint8_t gridY = pItem->gridY;
            *pItem = applied.item;
            pItem->gridX = gridX;
            pItem->gridY = gridY;
        }
        else if (pItem != nullptr)
        {
            // A new base item of another size (the Emerald) is placed again.
            InventoryItem old;
            InventoryBags::takeFromBag(
                party, target.memberIndex, target.bag, bagCount, target.gridX, target.gridY, old);

            if (!returnToParty(party, target, applied.item))
            {
                overflow = applied.item;
            }
        }
    }

    if (applied.result.materialAfter && !returnToParty(party, firstMaterial, *applied.result.materialAfter))
    {
        overflow = *applied.result.materialAfter;
    }

    party.refreshDerivedState();
    return true;
}

GemCombinePlan CraftingRuntime::planCombine(
    const Party &party,
    uint32_t gemItemId,
    bool cascade,
    const CraftingRules &rules)
{
    GemCombinePlan plan;
    const int count = rules.gemCombineCount();

    if (rules.gemTier(gemItemId) <= 0 || count <= 1)
    {
        return plan;
    }

    // Gems in bags, plain (a stored state is not a plain gem).
    const auto gemsOf = [&party](uint32_t itemId)
    {
        return uint32_t(materialRefs(party, {itemId, 0, 0}).size());
    };

    uint32_t itemId = gemItemId;

    if (cascade)
    {
        // The climb starts at the lowest tier.
        while (rules.gemTier(itemId) > 1)
        {
            --itemId;
        }
    }

    uint32_t carried = 0;

    while (rules.combinedGem(itemId) != 0)
    {
        const uint32_t available = gemsOf(itemId) + carried;
        const uint32_t merges = available / uint32_t(count);

        if (merges > 0)
        {
            plan.steps.push_back({itemId, rules.combinedGem(itemId), merges});
        }

        if (!cascade)
        {
            break;
        }

        carried = merges;
        itemId = rules.combinedGem(itemId);
    }

    return plan;
}

bool CraftingRuntime::combine(
    Party &party,
    const GemCombinePlan &plan,
    const CraftingRules &rules,
    const ItemTable &itemTable)
{
    if (plan.steps.empty())
    {
        return false;
    }

    const uint32_t count = uint32_t(rules.gemCombineCount());
    const int bagCount = bagCountOf(party);
    // Gems made by an earlier step are used before the party's own (they are not in a bag yet).
    uint32_t made = 0;
    uint32_t madeItemId = 0;
    std::vector<InventoryItem> results;

    for (const GemCombinePlan::Step &step : plan.steps)
    {
        uint32_t needed = step.merges * count;
        const uint32_t fromMade = step.fromItemId == madeItemId ? std::min(made, needed) : 0;
        needed -= fromMade;
        made -= fromMade;

        for (const CraftItemRef &ref : materialRefs(party, {step.fromItemId, 0, 0}))
        {
            if (needed == 0)
            {
                break;
            }

            InventoryItem removed;
            InventoryBags::takeFromBag(party, ref.memberIndex, ref.bag, bagCount, ref.gridX, ref.gridY, removed);
            --needed;
        }

        // Gems of the previous step left unused stay with the party.
        for (uint32_t index = 0; index < made; ++index)
        {
            results.push_back(ItemGenerator::makeInventoryItem(madeItemId, itemTable, ItemGenerationMode::Generic));
        }

        made = step.merges;
        madeItemId = step.toItemId;
    }

    for (uint32_t index = 0; index < made; ++index)
    {
        results.push_back(ItemGenerator::makeInventoryItem(madeItemId, itemTable, ItemGenerationMode::Generic));
    }

    for (const InventoryItem &gem : results)
    {
        party.tryGrantInventoryItem(gem);
    }

    return true;
}
}
