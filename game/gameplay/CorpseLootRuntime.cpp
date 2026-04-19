#include "game/gameplay/CorpseLootRuntime.h"

#include "game/items/ItemGenerator.h"
#include "game/party/Party.h"
#include "game/tables/ItemTable.h"

#include <algorithm>
#include <cstdint>
#include <random>

namespace OpenYAMM::Game
{
namespace
{
struct GoldHeapVisual
{
    uint8_t width = 1;
    uint8_t height = 1;
};

GoldHeapVisual classifyGoldHeapVisual(uint32_t goldAmount)
{
    if (goldAmount <= 200)
    {
        return {1, 1};
    }

    if (goldAmount <= 1000)
    {
        return {2, 1};
    }

    return {2, 1};
}

bool isWeaponLootItem(const ItemDefinition &item)
{
    return item.equipStat == "Weapon"
        || item.equipStat == "Weapon1or2"
        || item.equipStat == "Weapon2"
        || item.equipStat == "Missile";
}

bool isArmorLootItem(const ItemDefinition &item)
{
    return item.equipStat == "Armor";
}

bool isMiscLootItem(const ItemDefinition &item)
{
    return item.skillGroup == "Misc";
}

bool itemMatchesLootKind(const ItemDefinition &item, MonsterTable::LootItemKind kind)
{
    switch (kind)
    {
        case MonsterTable::LootItemKind::None:
            return false;

        case MonsterTable::LootItemKind::Any:
            return true;

        case MonsterTable::LootItemKind::Weapon:
            return isWeaponLootItem(item);

        case MonsterTable::LootItemKind::Armor:
            return isArmorLootItem(item);

        case MonsterTable::LootItemKind::Misc:
            return isMiscLootItem(item);

        case MonsterTable::LootItemKind::Gem:
            return item.equipStat == "Gem";

        case MonsterTable::LootItemKind::Ring:
            return item.equipStat == "Ring";

        case MonsterTable::LootItemKind::Amulet:
            return item.equipStat == "Amulet";

        case MonsterTable::LootItemKind::Boots:
            return item.equipStat == "Boots";

        case MonsterTable::LootItemKind::Helm:
            return item.equipStat == "Helm";

        case MonsterTable::LootItemKind::Belt:
            return item.equipStat == "Belt";

        case MonsterTable::LootItemKind::Cloak:
            return item.equipStat == "Cloak";

        case MonsterTable::LootItemKind::Gauntlets:
            return item.equipStat == "Gauntlets";

        case MonsterTable::LootItemKind::Shield:
            return item.equipStat == "Shield";

        case MonsterTable::LootItemKind::Wand:
            return item.equipStat == "WeaponW";

        case MonsterTable::LootItemKind::Ore:
            return item.equipStat == "Ore";

        case MonsterTable::LootItemKind::Scroll:
            return item.equipStat == "Sscroll";

        case MonsterTable::LootItemKind::Sword:
            return item.skillGroup == "Sword";

        case MonsterTable::LootItemKind::Dagger:
            return item.skillGroup == "Dagger";

        case MonsterTable::LootItemKind::Axe:
            return item.skillGroup == "Axe";

        case MonsterTable::LootItemKind::Spear:
            return item.skillGroup == "Spear";

        case MonsterTable::LootItemKind::Mace:
            return item.skillGroup == "Mace";

        case MonsterTable::LootItemKind::Club:
            return item.skillGroup == "Club";

        case MonsterTable::LootItemKind::Staff:
            return item.skillGroup == "Staff";

        case MonsterTable::LootItemKind::Bow:
            return item.skillGroup == "Bow";

        case MonsterTable::LootItemKind::Leather:
            return item.skillGroup == "Leather";

        case MonsterTable::LootItemKind::Chain:
            return item.skillGroup == "Chain";

        case MonsterTable::LootItemKind::Plate:
            return item.skillGroup == "Plate";
    }

    return false;
}
}

GameplayCorpseViewState buildMonsterCorpseView(
    const std::string &title,
    const MonsterTable::LootPrototype &loot,
    const ItemTable *pItemTable,
    Party *pParty)
{
    GameplayCorpseViewState view = {};
    view.title = title;

    static thread_local std::mt19937 rng(std::random_device{}());

    if (loot.goldDiceRolls > 0 && loot.goldDiceSides > 0)
    {
        GameplayChestItemState goldItem = {};
        goldItem.isGold = true;
        goldItem.goldRollCount = loot.goldDiceRolls;

        for (int roll = 0; roll < loot.goldDiceRolls; ++roll)
        {
            goldItem.goldAmount += uint32_t(std::uniform_int_distribution<int>(1, loot.goldDiceSides)(rng));
        }

        if (goldItem.goldAmount > 0)
        {
            const GoldHeapVisual goldVisual = classifyGoldHeapVisual(goldItem.goldAmount);
            goldItem.width = goldVisual.width;
            goldItem.height = goldVisual.height;
            view.items.push_back(goldItem);
        }
    }

    const StandardItemEnchantTable *pStandardItemEnchantTable =
        pParty != nullptr ? pParty->standardItemEnchantTable() : nullptr;
    const SpecialItemEnchantTable *pSpecialItemEnchantTable =
        pParty != nullptr ? pParty->specialItemEnchantTable() : nullptr;

    if (loot.itemChance > 0
        && loot.itemLevel > 0
        && std::uniform_int_distribution<int>(0, 99)(rng) < loot.itemChance)
    {
        const std::optional<InventoryItem> generatedItem =
            pItemTable != nullptr && pStandardItemEnchantTable != nullptr && pSpecialItemEnchantTable != nullptr
            ? ItemGenerator::generateRandomInventoryItem(
                *pItemTable,
                *pStandardItemEnchantTable,
                *pSpecialItemEnchantTable,
                ItemGenerationRequest{loot.itemLevel, ItemGenerationMode::MonsterLoot},
                pParty,
                rng,
                [kind = loot.itemKind](const ItemDefinition &entry)
                {
                    return itemMatchesLootKind(entry, kind);
                })
            : std::nullopt;

        if (generatedItem && generatedItem->objectDescriptionId != 0)
        {
            GameplayChestItemState item = {};
            item.item = *generatedItem;
            item.itemId = item.item.objectDescriptionId;
            item.quantity = item.item.quantity;
            view.items.push_back(item);
        }
    }

    return view;
}
}
