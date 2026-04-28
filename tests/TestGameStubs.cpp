#include "game/gameplay/GameMechanics.h"
#include "game/items/ItemEnchantRuntime.h"
#include "game/items/ItemGenerator.h"
#include "game/items/ItemRuntime.h"
#include "game/tables/CharacterDollTable.h"
#include "game/tables/ClassMultiplierTable.h"
#include "game/tables/ClassSkillTable.h"
#include "game/tables/ItemTable.h"

#include <algorithm>

namespace OpenYAMM::Game
{
void GameMechanics::bindClassMultiplierTable(const ClassMultiplierTable *pClassMultiplierTable)
{
    (void)pClassMultiplierTable;
}

bool GameMechanics::characterRangedAttackHitsArmorClass(
    int targetArmorClass,
    int attackBonus,
    float targetDistance,
    std::mt19937 &rng)
{
    (void)targetArmorClass;
    (void)attackBonus;
    (void)targetDistance;
    (void)rng;
    return true;
}

int GameMechanics::calculateBaseCharacterMaxHealth(
    const Character &character,
    const ClassMultiplierTable *pClassMultiplierTable)
{
    (void)pClassMultiplierTable;
    return std::max(1, character.maxHealth);
}

int GameMechanics::calculateBaseCharacterMaxSpellPoints(
    const Character &character,
    const ClassMultiplierTable *pClassMultiplierTable)
{
    (void)pClassMultiplierTable;
    return std::max(0, character.maxSpellPoints);
}

void GameMechanics::refreshCharacterBaseResources(
    Character &character,
    bool restoreCurrentToMaximum,
    const ClassMultiplierTable *pClassMultiplierTable)
{
    (void)pClassMultiplierTable;

    if (restoreCurrentToMaximum)
    {
        character.health = std::max(1, character.maxHealth);
        character.spellPoints = std::max(0, character.maxSpellPoints);
        return;
    }

    character.health = std::clamp(character.health, 0, std::max(1, character.maxHealth));
    character.spellPoints = std::clamp(character.spellPoints, 0, std::max(0, character.maxSpellPoints));
}

std::optional<CharacterEquipPlan> GameMechanics::resolveCharacterEquipPlan(
    const Character &character,
    const ItemDefinition &itemDefinition,
    const ItemTable *pItemTable,
    const CharacterDollTypeEntry *pCharacterDollType,
    std::optional<EquipmentSlot> explicitSlot,
    bool preferOffHand)
{
    (void)character;
    (void)itemDefinition;
    (void)pItemTable;
    (void)pCharacterDollType;
    (void)preferOffHand;

    if (!explicitSlot)
    {
        return std::nullopt;
    }

    CharacterEquipPlan plan = {};
    plan.targetSlot = *explicitSlot;
    return plan;
}

bool GameMechanics::canAct(const Character &character)
{
    return character.health > 0
        && !character.conditions.test(static_cast<size_t>(CharacterCondition::Asleep))
        && !character.conditions.test(static_cast<size_t>(CharacterCondition::Paralyzed))
        && !character.conditions.test(static_cast<size_t>(CharacterCondition::Dead))
        && !character.conditions.test(static_cast<size_t>(CharacterCondition::Unconscious))
        && !character.conditions.test(static_cast<size_t>(CharacterCondition::Petrified))
        && !character.conditions.test(static_cast<size_t>(CharacterCondition::Eradicated));
}

bool GameMechanics::canSelectInGameplay(const Character &character)
{
    return canAct(character);
}

bool GameMechanics::canTakeGameplayAction(const Character &character)
{
    return canAct(character) && character.recoverySecondsRemaining <= 0.0f;
}

int ItemEnchantRuntime::characterAttackDamageMultiplierAgainstMonster(
    const Character &character,
    CharacterAttackMode attackMode,
    const ItemTable *pItemTable,
    const SpecialItemEnchantTable *pSpecialTable,
    const std::string &monsterName,
    const std::string &monsterPictureName)
{
    (void)character;
    (void)attackMode;
    (void)pItemTable;
    (void)pSpecialTable;
    (void)monsterName;
    (void)monsterPictureName;
    return 1;
}

void ItemEnchantRuntime::applyEquippedEnchantEffects(
    const ItemDefinition &itemDefinition,
    const EquippedItemRuntimeState &runtimeState,
    const StandardItemEnchantTable *pStandardTable,
    const SpecialItemEnchantTable *pSpecialTable,
    Character &member)
{
    (void)itemDefinition;
    (void)runtimeState;
    (void)pStandardTable;
    (void)pSpecialTable;
    (void)member;
}

const ItemDefinition *ItemTable::get(uint32_t itemId) const
{
    (void)itemId;
    return nullptr;
}

const ItemDefinition *ItemTable::findBySpriteIndex(uint16_t spriteIndex) const
{
    (void)spriteIndex;
    return nullptr;
}

const std::vector<ItemDefinition> &ItemTable::entries() const
{
    static const std::vector<ItemDefinition> EmptyEntries;
    return EmptyEntries;
}

const CharacterDollEntry *CharacterDollTable::getCharacter(uint32_t characterId) const
{
    static CharacterDollEntry entry = {};
    entry = {};
    entry.id = characterId;
    entry.defaultSex = characterId == 2 ? 1u : 0u;
    entry.raceId = 0;
    return &entry;
}

const CharacterDollTypeEntry *CharacterDollTable::getDollType(uint32_t dollTypeId) const
{
    (void)dollTypeId;
    return nullptr;
}

SkillMastery ClassSkillTable::getClassCap(const std::string &className, const std::string &skillName) const
{
    (void)className;
    (void)skillName;
    return SkillMastery::None;
}

std::vector<CharacterSkill> ClassSkillTable::getDefaultSkillsForClass(const std::string &className) const
{
    (void)className;
    return {};
}

InventoryItem ItemGenerator::makeInventoryItem(
    uint32_t itemId,
    const ItemTable &itemTable,
    ItemGenerationMode mode)
{
    (void)itemTable;
    (void)mode;

    InventoryItem item = {};
    item.objectDescriptionId = itemId;
    item.quantity = 1;
    item.width = 1;
    item.height = 1;
    item.identified = true;
    return item;
}

bool ItemRuntime::requiresIdentification(const ItemDefinition &itemDefinition)
{
    (void)itemDefinition;
    return false;
}

bool ItemRuntime::isRareItem(const ItemDefinition &itemDefinition)
{
    return itemDefinition.rarity != ItemRarity::Common;
}

bool ItemRuntime::isUniquelyGeneratedRareItem(const ItemDefinition &itemDefinition)
{
    return isRareItem(itemDefinition);
}

bool ItemRuntime::characterMeetsClassRestriction(const Character &character, const ItemDefinition &itemDefinition)
{
    (void)character;
    (void)itemDefinition;
    return true;
}

bool ItemRuntime::characterMeetsRaceRestriction(const Character &character, const ItemDefinition &itemDefinition)
{
    (void)character;
    (void)itemDefinition;
    return true;
}

bool ItemRuntime::canCharacterIdentifyItem(const Character &character, const ItemDefinition &itemDefinition)
{
    (void)character;
    (void)itemDefinition;
    return true;
}

bool ItemRuntime::canCharacterRepairItem(const Character &character, const ItemDefinition &itemDefinition)
{
    (void)character;
    (void)itemDefinition;
    return true;
}

std::string ItemRuntime::displayName(const InventoryItem &item, const ItemDefinition &itemDefinition)
{
    (void)item;
    return itemDefinition.name;
}
}
