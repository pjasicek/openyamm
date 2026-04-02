#pragma once

#include "game/party/CharacterState.h"
#include "game/items/ItemEnchantTables.h"
#include "game/party/Party.h"

#include <optional>
#include <random>
#include <string>

namespace OpenYAMM::Game
{
struct Character;
class ItemTable;
struct ItemDefinition;
enum class CharacterAttackMode;

enum class ItemEnchantCategory : uint8_t
{
    None = 0,
    OneHandedWeapon,
    TwoHandedWeapon,
    Missile,
    Armor,
    Shield,
    Helm,
    Belt,
    Cloak,
    Gauntlets,
    Boots,
    Ring,
    Amulet,
};

class ItemEnchantRuntime
{
public:
    static bool isEnchantable(const ItemDefinition &itemDefinition);
    static bool canHaveStandardEnchant(const ItemDefinition &itemDefinition);
    static bool canHaveSpecialEnchant(const ItemDefinition &itemDefinition);
    static ItemEnchantCategory categoryForItem(const ItemDefinition &itemDefinition);
    static int standardEnchantChance(int treasureLevel);
    static int specialEnchantChance(const ItemDefinition &itemDefinition, int treasureLevel);
    static bool isSpecialRarityAllowed(char rarityLevel, int treasureLevel);
    static std::optional<uint16_t> chooseStandardEnchantId(
        const ItemDefinition &itemDefinition,
        const StandardItemEnchantTable &table,
        std::mt19937 &rng);
    static std::optional<uint16_t> chooseSpecialEnchantId(
        const ItemDefinition &itemDefinition,
        const SpecialItemEnchantTable &table,
        int treasureLevel,
        std::mt19937 &rng);
    static int generateStandardEnchantPower(StandardItemEnchantKind kind, int treasureLevel, std::mt19937 &rng);
    static std::string displayName(
        const InventoryItem &item,
        const ItemDefinition &itemDefinition,
        const StandardItemEnchantTable *pStandardTable,
        const SpecialItemEnchantTable *pSpecialTable);
    static int itemValue(
        const InventoryItem &item,
        const ItemDefinition &itemDefinition,
        const StandardItemEnchantTable *pStandardTable,
        const SpecialItemEnchantTable *pSpecialTable);
    static std::string buildEnchantDescription(
        const InventoryItem &item,
        const StandardItemEnchantTable *pStandardTable,
        const SpecialItemEnchantTable *pSpecialTable);
    static void applyEquippedEnchantEffects(
        const ItemDefinition &itemDefinition,
        const EquippedItemRuntimeState &runtimeState,
        const StandardItemEnchantTable *pStandardTable,
        const SpecialItemEnchantTable *pSpecialTable,
        Character &member);
    static int characterAttackDamageMultiplierAgainstMonster(
        const Character &character,
        CharacterAttackMode attackMode,
        const ItemTable *pItemTable,
        const SpecialItemEnchantTable *pSpecialTable,
        const std::string &monsterName,
        const std::string &monsterPictureName);
    static int elementalDamageBonus(
        const InventoryItem &item,
        const SpecialItemEnchantTable *pSpecialTable);
};
}
