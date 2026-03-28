#include "game/Party.h"

#include "game/EventRuntime.h"
#include "game/GameMechanics.h"
#include "game/ItemTable.h"
#include "game/RosterTable.h"
#include "game/SpellIds.h"
#include "game/StringUtils.h"

#include <algorithm>
#include <array>
#include <cctype>

namespace OpenYAMM::Game
{
namespace
{
void grantSeedSkill(Character &character, const std::string &skillName, uint32_t level = 1)
{
    CharacterSkill skill = {};
    skill.name = canonicalSkillName(skillName);
    skill.level = level;
    skill.mastery = SkillMastery::Normal;
    character.skills[skill.name] = skill;
}

void grantSeedSkill(Character &character, const std::string &skillName, uint32_t level, SkillMastery mastery)
{
    CharacterSkill skill = {};
    skill.name = canonicalSkillName(skillName);
    skill.level = level;
    skill.mastery = mastery;
    character.skills[skill.name] = skill;
}

void grantAllMagicSchools(Character &character, uint32_t level, SkillMastery mastery)
{
    static const std::array<const char *, 9> skillNames = {
        "FireMagic",
        "AirMagic",
        "WaterMagic",
        "EarthMagic",
        "SpiritMagic",
        "MindMagic",
        "BodyMagic",
        "LightMagic",
        "DarkMagic"
    };

    for (const char *pSkillName : skillNames)
    {
        grantSeedSkill(character, pSkillName, level, mastery);
    }
}

void grantDefaultEquipmentSkills(Character &character)
{
    static const std::array<const char *, 11> skillNames = {
        "LeatherArmor",
        "ChainArmor",
        "PlateArmor",
        "Spear",
        "Sword",
        "Bow",
        "Dagger",
        "Mace",
        "Axe",
        "Staff",
        "Shield"
    };

    for (const char *pSkillName : skillNames)
    {
        grantSeedSkill(character, pSkillName);
    }
}

void grantSeedInventoryLoadout(Character &character)
{
    static const std::array<uint32_t, 29> itemIds = {
        84,
        89,
        94,
        41,
        1,
        56,
        21,
        66,
        31,
        79,
        99,
        109,
        117,
        132,
        124,
        137, 138, 139, 140, 141, 142, 143, 144, 145, 146,
        127, 129,
        147, 148
    };

    for (uint32_t itemId : itemIds)
    {
        character.inventory.push_back({itemId, 1, 0, 0, 0, 0});
    }
}

std::string normalizeRoleName(const std::string &className)
{
    const std::string canonicalName = canonicalClassName(className);

    if (canonicalName.empty())
    {
        return "Adventurer";
    }

    return displayClassName(canonicalName);
}

std::string portraitTextureNameFromPictureId(uint32_t pictureId)
{
    char buffer[16] = {};
    std::snprintf(buffer, sizeof(buffer), "PC%02u-01", pictureId + 1);
    return buffer;
}

std::optional<uint32_t> tryParsePictureIdFromPortraitTextureName(const std::string &portraitTextureName)
{
    if (portraitTextureName.size() < 6)
    {
        return std::nullopt;
    }

    const std::string normalized = toLowerCopy(portraitTextureName);

    if (normalized[0] != 'p' || normalized[1] != 'c'
        || !std::isdigit(static_cast<unsigned char>(normalized[2]))
        || !std::isdigit(static_cast<unsigned char>(normalized[3])))
    {
        return std::nullopt;
    }

    const uint32_t faceNumber = static_cast<uint32_t>((normalized[2] - '0') * 10 + (normalized[3] - '0'));

    if (faceNumber == 0)
    {
        return std::nullopt;
    }

    return faceNumber - 1;
}

void initializePortraitRuntimeState(Character &member)
{
    const std::optional<uint32_t> parsedPictureId = tryParsePictureIdFromPortraitTextureName(member.portraitTextureName);

    if (parsedPictureId)
    {
        member.portraitPictureId = *parsedPictureId;
    }
    else if (member.portraitTextureName.empty())
    {
        member.portraitTextureName = portraitTextureNameFromPictureId(member.portraitPictureId);
    }

    member.portraitState = PortraitId::Normal;
    member.portraitElapsedTicks = 0;
    member.portraitDurationTicks = 0;
    member.portraitSequenceCounter = 0;
    member.portraitImageIndex = 0;
}

std::optional<std::pair<uint8_t, uint8_t>> findFirstFreeInventorySlot(
    const std::vector<InventoryItem> &inventory,
    uint8_t width,
    uint8_t height)
{
    if (width == 0 || height == 0 || width > Character::InventoryWidth || height > Character::InventoryHeight)
    {
        return std::nullopt;
    }

    std::array<bool, Character::InventoryWidth * Character::InventoryHeight> occupied = {};

    for (const InventoryItem &item : inventory)
    {
        for (uint8_t y = 0; y < item.height; ++y)
        {
            for (uint8_t x = 0; x < item.width; ++x)
            {
                const uint8_t cellX = item.gridX + x;
                const uint8_t cellY = item.gridY + y;

                if (cellX >= Character::InventoryWidth || cellY >= Character::InventoryHeight)
                {
                    continue;
                }

                occupied[static_cast<size_t>(cellY) * Character::InventoryWidth + cellX] = true;
            }
        }
    }

    for (int x = 0; x <= Character::InventoryWidth - width; ++x)
    {
        for (int y = 0; y <= Character::InventoryHeight - height; ++y)
        {
            bool canPlace = true;

            for (uint8_t offsetY = 0; offsetY < height && canPlace; ++offsetY)
            {
                for (uint8_t offsetX = 0; offsetX < width; ++offsetX)
                {
                    const size_t index =
                        static_cast<size_t>(y + offsetY) * Character::InventoryWidth + static_cast<size_t>(x + offsetX);

                    if (occupied[index])
                    {
                        canPlace = false;
                        break;
                    }
                }
            }

            if (canPlace)
            {
                return std::pair<uint8_t, uint8_t>(static_cast<uint8_t>(x), static_cast<uint8_t>(y));
            }
        }
    }

    return std::nullopt;
}

bool inventoryItemContainsCell(const InventoryItem &item, uint8_t gridX, uint8_t gridY)
{
    return gridX >= item.gridX
        && gridX < item.gridX + item.width
        && gridY >= item.gridY
        && gridY < item.gridY + item.height;
}

constexpr uint32_t AttackPreferenceKnight = 0x0001;
constexpr uint32_t AttackPreferencePaladin = 0x0002;
constexpr uint32_t AttackPreferenceArcher = 0x0004;
constexpr uint32_t AttackPreferenceDruid = 0x0008;
constexpr uint32_t AttackPreferenceCleric = 0x0010;
constexpr uint32_t AttackPreferenceSorcerer = 0x0020;
constexpr uint32_t AttackPreferenceRanger = 0x0040;
constexpr uint32_t AttackPreferenceThief = 0x0080;
constexpr uint32_t AttackPreferenceMonk = 0x0100;
constexpr uint32_t AttackPreferenceMale = 0x0200;
constexpr uint32_t AttackPreferenceFemale = 0x0400;
constexpr uint32_t AttackPreferenceHuman = 0x0800;
constexpr uint32_t AttackPreferenceElf = 0x1000;
constexpr uint32_t AttackPreferenceDwarf = 0x2000;
constexpr uint32_t AttackPreferenceGoblin = 0x4000;

bool isValidMonsterAttackTarget(const Character &member)
{
    return member.health > 0
        && !member.conditions.test(static_cast<size_t>(CharacterCondition::Paralyzed))
        && !member.conditions.test(static_cast<size_t>(CharacterCondition::Unconscious))
        && !member.conditions.test(static_cast<size_t>(CharacterCondition::Dead))
        && !member.conditions.test(static_cast<size_t>(CharacterCondition::Petrified))
        && !member.conditions.test(static_cast<size_t>(CharacterCondition::Eradicated));
}

bool matchesMonsterAttackPreference(const Character &member, uint32_t preferenceFlag)
{
    const std::string className = canonicalClassName(member.className.empty() ? member.role : member.className);

    switch (preferenceFlag)
    {
        case AttackPreferenceKnight:
            return className == "Knight";

        case AttackPreferencePaladin:
            return className == "Paladin";

        case AttackPreferenceArcher:
            return className == "Archer";

        case AttackPreferenceDruid:
            return className == "Druid";

        case AttackPreferenceCleric:
            return className == "Cleric";

        case AttackPreferenceSorcerer:
            return className == "Sorcerer";

        case AttackPreferenceRanger:
            return className == "Ranger";

        case AttackPreferenceThief:
            return className == "Thief";

        case AttackPreferenceMonk:
            return className == "Monk";

        case AttackPreferenceHuman:
            return className == "Knight"
                || className == "Paladin"
                || className == "Archer"
                || className == "Druid"
                || className == "Cleric"
                || className == "Sorcerer"
                || className == "Ranger"
                || className == "Thief"
                || className == "Monk";

        case AttackPreferenceElf:
            return className == "DarkElf";

        case AttackPreferenceMale:
        case AttackPreferenceFemale:
        case AttackPreferenceDwarf:
        case AttackPreferenceGoblin:
        default:
            return false;
    }
}

void updateMemberIncapacitatedCondition(Character &member, bool preservationActive)
{
    if (member.health > 0)
    {
        member.conditions.reset(static_cast<size_t>(CharacterCondition::Unconscious));
        member.conditions.reset(static_cast<size_t>(CharacterCondition::Dead));
        return;
    }

    if (member.health + static_cast<int>(member.endurance) >= 1 || preservationActive)
    {
        member.conditions.set(static_cast<size_t>(CharacterCondition::Unconscious));
        member.conditions.reset(static_cast<size_t>(CharacterCondition::Dead));
    }
    else
    {
        member.conditions.set(static_cast<size_t>(CharacterCondition::Dead));
        member.conditions.reset(static_cast<size_t>(CharacterCondition::Unconscious));
    }
}

bool inventoryItemFitsAt(const InventoryItem &item, uint8_t gridX, uint8_t gridY)
{
    return item.width > 0
        && item.height > 0
        && gridX + item.width <= Character::InventoryWidth
        && gridY + item.height <= Character::InventoryHeight;
}

bool inventoryItemsOverlap(const InventoryItem &left, const InventoryItem &right)
{
    return left.gridX < right.gridX + right.width
        && left.gridX + left.width > right.gridX
        && left.gridY < right.gridY + right.height
        && left.gridY + left.height > right.gridY;
}

uint32_t &equippedItemId(CharacterEquipment &equipment, EquipmentSlot slot)
{
    switch (slot)
    {
        case EquipmentSlot::OffHand:
            return equipment.offHand;

        case EquipmentSlot::MainHand:
            return equipment.mainHand;

        case EquipmentSlot::Bow:
            return equipment.bow;

        case EquipmentSlot::Armor:
            return equipment.armor;

        case EquipmentSlot::Helm:
            return equipment.helm;

        case EquipmentSlot::Belt:
            return equipment.belt;

        case EquipmentSlot::Cloak:
            return equipment.cloak;

        case EquipmentSlot::Gauntlets:
            return equipment.gauntlets;

        case EquipmentSlot::Boots:
            return equipment.boots;

        case EquipmentSlot::Amulet:
            return equipment.amulet;

        case EquipmentSlot::Ring1:
            return equipment.ring1;

        case EquipmentSlot::Ring2:
            return equipment.ring2;

        case EquipmentSlot::Ring3:
            return equipment.ring3;

        case EquipmentSlot::Ring4:
            return equipment.ring4;

        case EquipmentSlot::Ring5:
            return equipment.ring5;

        case EquipmentSlot::Ring6:
            return equipment.ring6;
    }

    return equipment.mainHand;
}

uint32_t equippedItemId(const CharacterEquipment &equipment, EquipmentSlot slot)
{
    switch (slot)
    {
        case EquipmentSlot::OffHand:
            return equipment.offHand;

        case EquipmentSlot::MainHand:
            return equipment.mainHand;

        case EquipmentSlot::Bow:
            return equipment.bow;

        case EquipmentSlot::Armor:
            return equipment.armor;

        case EquipmentSlot::Helm:
            return equipment.helm;

        case EquipmentSlot::Belt:
            return equipment.belt;

        case EquipmentSlot::Cloak:
            return equipment.cloak;

        case EquipmentSlot::Gauntlets:
            return equipment.gauntlets;

        case EquipmentSlot::Boots:
            return equipment.boots;

        case EquipmentSlot::Amulet:
            return equipment.amulet;

        case EquipmentSlot::Ring1:
            return equipment.ring1;

        case EquipmentSlot::Ring2:
            return equipment.ring2;

        case EquipmentSlot::Ring3:
            return equipment.ring3;

        case EquipmentSlot::Ring4:
            return equipment.ring4;

        case EquipmentSlot::Ring5:
            return equipment.ring5;

        case EquipmentSlot::Ring6:
            return equipment.ring6;
    }

    return 0;
}
}

bool Character::addInventoryItem(const InventoryItem &item)
{
    InventoryItem placedItem = item;
    placedItem.width = std::max<uint8_t>(1, item.width);
    placedItem.height = std::max<uint8_t>(1, item.height);

    const std::optional<std::pair<uint8_t, uint8_t>> placement =
        findFirstFreeInventorySlot(inventory, placedItem.width, placedItem.height);

    if (!placement)
    {
        return false;
    }

    return addInventoryItemAt(placedItem, placement->first, placement->second);
}

bool Character::addInventoryItemAt(const InventoryItem &item, uint8_t gridX, uint8_t gridY)
{
    InventoryItem placedItem = item;
    placedItem.width = std::max<uint8_t>(1, item.width);
    placedItem.height = std::max<uint8_t>(1, item.height);
    placedItem.gridX = gridX;
    placedItem.gridY = gridY;

    if (!inventoryItemFitsAt(placedItem, placedItem.gridX, placedItem.gridY))
    {
        return false;
    }

    for (const InventoryItem &existingItem : inventory)
    {
        if (inventoryItemsOverlap(existingItem, placedItem))
        {
            return false;
        }
    }

    inventory.push_back(placedItem);
    return true;
}

bool Character::removeInventoryItem(uint32_t objectDescriptionId, uint32_t quantity)
{
    if (objectDescriptionId == 0 || quantity == 0)
    {
        return false;
    }

    for (size_t itemIndex = 0; itemIndex < inventory.size(); ++itemIndex)
    {
        InventoryItem &item = inventory[itemIndex];

        if (item.objectDescriptionId != objectDescriptionId)
        {
            continue;
        }

        if (item.quantity < quantity)
        {
            return false;
        }

        item.quantity -= quantity;

        if (item.quantity == 0)
        {
            inventory.erase(inventory.begin() + itemIndex);
        }

        return true;
    }

    return false;
}

const InventoryItem *Character::inventoryItemAt(uint8_t gridX, uint8_t gridY) const
{
    for (const InventoryItem &item : inventory)
    {
        if (inventoryItemContainsCell(item, gridX, gridY))
        {
            return &item;
        }
    }

    return nullptr;
}

bool Character::takeInventoryItemAt(uint8_t gridX, uint8_t gridY, InventoryItem &item)
{
    for (size_t itemIndex = 0; itemIndex < inventory.size(); ++itemIndex)
    {
        if (!inventoryItemContainsCell(inventory[itemIndex], gridX, gridY))
        {
            continue;
        }

        item = inventory[itemIndex];
        inventory.erase(inventory.begin() + itemIndex);
        return true;
    }

    return false;
}

bool Character::tryPlaceInventoryItemAt(
    const InventoryItem &item,
    uint8_t gridX,
    uint8_t gridY,
    std::optional<InventoryItem> &replacedItem)
{
    replacedItem.reset();

    InventoryItem placedItem = item;
    placedItem.width = std::max<uint8_t>(1, item.width);
    placedItem.height = std::max<uint8_t>(1, item.height);
    placedItem.gridX = gridX;
    placedItem.gridY = gridY;

    if (!inventoryItemFitsAt(placedItem, gridX, gridY))
    {
        return false;
    }

    std::vector<size_t> overlappingItemIndices;

    for (size_t itemIndex = 0; itemIndex < inventory.size(); ++itemIndex)
    {
        if (inventoryItemsOverlap(inventory[itemIndex], placedItem))
        {
            overlappingItemIndices.push_back(itemIndex);
        }
    }

    if (overlappingItemIndices.size() > 1)
    {
        return false;
    }

    if (overlappingItemIndices.size() == 1)
    {
        replacedItem = inventory[overlappingItemIndices.front()];
        inventory.erase(inventory.begin() + overlappingItemIndices.front());
    }

    inventory.push_back(placedItem);
    return true;
}

bool Character::hasSkill(const std::string &skillName) const
{
    const std::string canonicalName = canonicalSkillName(skillName);
    return !canonicalName.empty() && skills.contains(canonicalName);
}

const CharacterSkill *Character::findSkill(const std::string &skillName) const
{
    const std::string canonicalName = canonicalSkillName(skillName);

    if (canonicalName.empty())
    {
        return nullptr;
    }

    const std::unordered_map<std::string, CharacterSkill>::const_iterator it = skills.find(canonicalName);
    return it != skills.end() ? &it->second : nullptr;
}

CharacterSkill *Character::findSkill(const std::string &skillName)
{
    const std::string canonicalName = canonicalSkillName(skillName);

    if (canonicalName.empty())
    {
        return nullptr;
    }

    const std::unordered_map<std::string, CharacterSkill>::iterator it = skills.find(canonicalName);
    return it != skills.end() ? &it->second : nullptr;
}

bool Character::setSkillMastery(const std::string &skillName, SkillMastery mastery)
{
    CharacterSkill *pSkill = findSkill(skillName);

    if (pSkill == nullptr)
    {
        return false;
    }

    pSkill->mastery = mastery;
    return true;
}

size_t Character::inventoryItemCount() const
{
    return inventory.size();
}

size_t Character::usedInventoryCells() const
{
    size_t usedCells = 0;

    for (const InventoryItem &item : inventory)
    {
        usedCells += static_cast<size_t>(item.width) * item.height;
    }

    return usedCells;
}

size_t Character::inventoryCapacity() const
{
    return static_cast<size_t>(InventoryWidth) * InventoryHeight;
}

PartySeed Party::createDefaultSeed()
{
    PartySeed seed = {};
    seed.gold = 10000;
    seed.food = 7;

    Character cleric = {};
    cleric.name = "Ariel";
    cleric.className = "Cleric";
    cleric.role = "Cleric";
    cleric.portraitTextureName = "PC03-01";
    cleric.portraitPictureId = 2;
    cleric.characterDataId = 3;
    cleric.birthYear = 1148;
    cleric.experience = 10000;
    cleric.level = 5;
    cleric.skillPoints = 30;
    cleric.might = 12;
    cleric.intellect = 20;
    cleric.personality = 20;
    cleric.endurance = 15;
    cleric.speed = 12;
    cleric.accuracy = 12;
    cleric.luck = 14;
    cleric.maxHealth = 100;
    cleric.health = 100;
    cleric.maxSpellPoints = 120;
    cleric.spellPoints = 120;
    grantDefaultEquipmentSkills(cleric);
    grantAllMagicSchools(cleric, 10, SkillMastery::Grandmaster);
    grantSeedInventoryLoadout(cleric);
    seed.members.push_back(cleric);

    Character femaleKnight = {};
    femaleKnight.name = "Leane";
    femaleKnight.className = "Knight";
    femaleKnight.role = "Knight";
    femaleKnight.portraitTextureName = "PC02-01";
    femaleKnight.portraitPictureId = 1;
    femaleKnight.characterDataId = 2;
    femaleKnight.birthYear = 1144;
    femaleKnight.experience = 10000;
    femaleKnight.level = 5;
    femaleKnight.skillPoints = 30;
    femaleKnight.might = 16;
    femaleKnight.intellect = 9;
    femaleKnight.personality = 11;
    femaleKnight.endurance = 16;
    femaleKnight.speed = 13;
    femaleKnight.accuracy = 15;
    femaleKnight.luck = 12;
    femaleKnight.maxHealth = 115;
    femaleKnight.health = 115;
    grantDefaultEquipmentSkills(femaleKnight);
    grantSeedInventoryLoadout(femaleKnight);
    seed.members.push_back(femaleKnight);

    Character minotaur = {};
    minotaur.name = "Arius";
    minotaur.className = "Minotaur";
    minotaur.role = "Minotaur";
    minotaur.portraitTextureName = "PC21-01";
    minotaur.portraitPictureId = 20;
    minotaur.characterDataId = 21;
    minotaur.birthYear = 1155;
    minotaur.experience = 10000;
    minotaur.level = 5;
    minotaur.skillPoints = 30;
    minotaur.might = 21;
    minotaur.intellect = 11;
    minotaur.personality = 17;
    minotaur.endurance = 18;
    minotaur.speed = 10;
    minotaur.accuracy = 16;
    minotaur.luck = 12;
    minotaur.maxHealth = 130;
    minotaur.health = 130;
    grantDefaultEquipmentSkills(minotaur);
    grantSeedInventoryLoadout(minotaur);
    seed.members.push_back(minotaur);

    Character troll = {};
    troll.name = "Overdune";
    troll.className = "Troll";
    troll.role = "Troll";
    troll.portraitTextureName = "PC23-01";
    troll.portraitPictureId = 22;
    troll.characterDataId = 23;
    troll.birthYear = 1149;
    troll.experience = 10000;
    troll.level = 5;
    troll.skillPoints = 30;
    troll.might = 20;
    troll.intellect = 8;
    troll.personality = 8;
    troll.endurance = 20;
    troll.speed = 14;
    troll.accuracy = 16;
    troll.luck = 12;
    troll.maxHealth = 140;
    troll.health = 140;
    grantDefaultEquipmentSkills(troll);
    grantSeedInventoryLoadout(troll);
    seed.members.push_back(troll);

    Character dragon = {};
    dragon.name = "Ithilgore";
    dragon.className = "Dragon";
    dragon.role = "Dragon";
    dragon.portraitTextureName = "PC25-01";
    dragon.portraitPictureId = 24;
    dragon.characterDataId = 25;
    dragon.birthYear = 1129;
    dragon.experience = 10000;
    dragon.level = 5;
    dragon.skillPoints = 30;
    dragon.might = 30;
    dragon.intellect = 17;
    dragon.personality = 9;
    dragon.endurance = 21;
    dragon.speed = 11;
    dragon.accuracy = 13;
    dragon.luck = 7;
    dragon.maxHealth = 160;
    dragon.health = 160;
    dragon.maxSpellPoints = 20;
    dragon.spellPoints = 20;
    grantSeedInventoryLoadout(dragon);
    seed.members.push_back(dragon);

    return seed;
}

void Party::reset()
{
    seed(createDefaultSeed());
}

void Party::setItemTable(const ItemTable *pItemTable)
{
    m_pItemTable = pItemTable;
}

void Party::setClassSkillTable(const ClassSkillTable *pClassSkillTable)
{
    m_pClassSkillTable = pClassSkillTable;

    for (Character &member : m_members)
    {
        member.className = canonicalClassName(member.className.empty() ? member.role : member.className);

        if (member.skills.empty())
        {
            applyDefaultStartingSkills(member);
        }

        initializePortraitRuntimeState(member);
    }
}

void Party::seed(const PartySeed &seed)
{
    m_members = seed.members;
    m_activeMemberIndex = 0;
    m_partyBuffs = {};
    m_characterBuffs = {};
    m_gold = std::max(0, seed.gold);
    m_bankGold = 0;
    m_food = std::max(0, seed.food);
    m_monsterTargetSelectionCounter = 0;

    for (Character &member : m_members)
    {
        const std::vector<InventoryItem> seededInventory = member.inventory;
        member.className = canonicalClassName(member.className.empty() ? member.role : member.className);
        member.role = normalizeRoleName(member.className);
        member.level = std::max<uint32_t>(1, member.level);
        member.skillPoints = std::max<uint32_t>(0u, member.skillPoints);
        member.maxHealth = std::max(1, member.maxHealth);
        member.health = std::clamp(member.health, 0, member.maxHealth);
        member.maxSpellPoints = std::max(0, member.maxSpellPoints);
        member.spellPoints = std::clamp(member.spellPoints, 0, member.maxSpellPoints);
        member.inventory.clear();

        for (const InventoryItem &seededItem : seededInventory)
        {
            InventoryItem resolvedItem = seededItem;
            resolvedItem.width = resolveInventoryWidth(seededItem.objectDescriptionId);
            resolvedItem.height = resolveInventoryHeight(seededItem.objectDescriptionId);

            const bool placed = (seededItem.width > 0 && seededItem.height > 0)
                ? member.addInventoryItemAt(resolvedItem, seededItem.gridX, seededItem.gridY)
                : member.addInventoryItem(resolvedItem);

            if (!placed)
            {
                continue;
            }
        }

        if (member.skills.empty())
        {
            applyDefaultStartingSkills(member);
        }

        initializePortraitRuntimeState(member);
    }

    if (m_members.empty())
    {
        Character fallbackMember = {};
        fallbackMember.name = "Adventurer";
        fallbackMember.className = "Knight";
        fallbackMember.role = "Knight";
        fallbackMember.level = 1;
        fallbackMember.skillPoints = 0;
        fallbackMember.maxHealth = 100;
        fallbackMember.health = 100;
        m_members.push_back(fallbackMember);
    }

    for (const InventoryItem &item : seed.inventory)
    {
        grantItem(item.objectDescriptionId, std::max<uint32_t>(1, item.quantity));
    }

    m_waterDamageTicks = 0;
    m_burningDamageTicks = 0;
    m_splashCount = 0;
    m_landingSoundCount = 0;
    m_hardLandingSoundCount = 0;
    m_lastFallDamageDistance = 0.0f;
    m_lastStatus.clear();
    rebuildMagicalBonusesFromBuffs();
}

void Party::applyMovementEffects(const OutdoorMovementEffects &effects)
{
    for (uint32_t i = 0; i < effects.waterDamageTicks; ++i)
    {
        for (size_t memberIndex = 0; memberIndex < m_members.size(); ++memberIndex)
        {
            const int damage = std::max(1, m_members[memberIndex].maxHealth / 10);
            applyDamageToMember(memberIndex, damage, "");
        }

        m_waterDamageTicks += 1;
        m_lastStatus = "water damage";
    }

    for (uint32_t i = 0; i < effects.burningDamageTicks; ++i)
    {
        for (size_t memberIndex = 0; memberIndex < m_members.size(); ++memberIndex)
        {
            const int damage = std::max(1, m_members[memberIndex].maxHealth / 10);
            applyDamageToMember(memberIndex, damage, "");
        }

        m_burningDamageTicks += 1;
        m_lastStatus = "burning damage";
    }

    if (effects.maxFallDamageDistance > 0.0f)
    {
        m_lastFallDamageDistance = std::max(m_lastFallDamageDistance, effects.maxFallDamageDistance);

        for (size_t memberIndex = 0; memberIndex < m_members.size(); ++memberIndex)
        {
            const int damage =
                std::max(0, static_cast<int>(effects.maxFallDamageDistance * (m_members[memberIndex].maxHealth / 10.0f) / 256.0f));
            applyDamageToMember(memberIndex, damage, "");
        }

        m_lastStatus = "fall damage";
    }

    if (effects.playSplashSound)
    {
        m_splashCount += 1;
        m_lastStatus = "splash";
    }

    if (effects.playLandingSound)
    {
        m_landingSoundCount += 1;
        m_lastStatus = "landing";
    }

    if (effects.playHardLandingSound)
    {
        m_hardLandingSoundCount += 1;
        m_lastStatus = "hard landing";
    }
}

void Party::applyEventRuntimeState(const EventRuntimeState &runtimeState)
{
    for (uint32_t itemId : runtimeState.grantedItemIds)
    {
        grantItem(itemId);
        m_lastStatus = "item granted";
    }

    for (uint32_t itemId : runtimeState.removedItemIds)
    {
        if (removeItem(itemId))
        {
            m_lastStatus = "item removed";
        }
    }

    for (uint32_t awardId : runtimeState.grantedAwardIds)
    {
        addAward(awardId);
        m_lastStatus = "award granted";
    }

    for (uint32_t awardId : runtimeState.removedAwardIds)
    {
        removeAward(awardId);
        m_lastStatus = "award removed";
    }
}

bool Party::applyDamageToActiveMember(int damage, const std::string &status)
{
    if (damage <= 0 || m_members.empty())
    {
        return false;
    }

    size_t targetIndex = std::min(m_activeMemberIndex, m_members.size() - 1);

    if (m_members[targetIndex].health <= 0)
    {
        bool foundLivingMember = false;

        for (size_t memberIndex = 0; memberIndex < m_members.size(); ++memberIndex)
        {
            if (m_members[memberIndex].health > 0)
            {
                targetIndex = memberIndex;
                foundLivingMember = true;
                break;
            }
        }

        if (!foundLivingMember)
        {
            return false;
        }
    }

    return applyDamageToMember(targetIndex, damage, status);
}

bool Party::applyDamageToMember(size_t memberIndex, int damage, const std::string &status)
{
    if (damage <= 0 || memberIndex >= m_members.size())
    {
        return false;
    }

    Character &member = m_members[memberIndex];

    if (member.health <= 0)
    {
        return false;
    }

    member.health -= damage;
    const bool preservationActive =
        m_characterBuffs[memberIndex][static_cast<size_t>(CharacterBuffId::Preservation)].active();
    updateMemberIncapacitatedCondition(member, preservationActive);

    if (!status.empty())
    {
        m_lastStatus = status;
    }

    return true;
}

bool Party::applyDamageToAllLivingMembers(int damage, const std::string &status)
{
    if (damage <= 0 || m_members.empty())
    {
        return false;
    }

    bool applied = false;

    for (size_t memberIndex = 0; memberIndex < m_members.size(); ++memberIndex)
    {
        if (m_members[memberIndex].health <= 0)
        {
            continue;
        }

        applied = applyDamageToMember(memberIndex, damage, "") || applied;
    }

    if (applied && !status.empty())
    {
        m_lastStatus = status;
    }

    return applied;
}

std::optional<size_t> Party::chooseMonsterAttackTarget(uint32_t attackPreferences, uint32_t seedHint)
{
    std::vector<size_t> candidates;
    candidates.reserve(m_members.size());

    static constexpr std::array<uint32_t, 15> PreferenceFlags = {{
        AttackPreferenceKnight,
        AttackPreferencePaladin,
        AttackPreferenceArcher,
        AttackPreferenceDruid,
        AttackPreferenceCleric,
        AttackPreferenceSorcerer,
        AttackPreferenceRanger,
        AttackPreferenceThief,
        AttackPreferenceMonk,
        AttackPreferenceMale,
        AttackPreferenceFemale,
        AttackPreferenceHuman,
        AttackPreferenceElf,
        AttackPreferenceDwarf,
        AttackPreferenceGoblin,
    }};

    if (attackPreferences != 0)
    {
        for (uint32_t preferenceFlag : PreferenceFlags)
        {
            if ((attackPreferences & preferenceFlag) == 0)
            {
                continue;
            }

            for (size_t memberIndex = 0; memberIndex < m_members.size(); ++memberIndex)
            {
                const Character &member = m_members[memberIndex];

                if (!isValidMonsterAttackTarget(member) || !matchesMonsterAttackPreference(member, preferenceFlag))
                {
                    continue;
                }

                candidates.push_back(memberIndex);
            }
        }
    }

    if (candidates.empty())
    {
        for (size_t memberIndex = 0; memberIndex < m_members.size(); ++memberIndex)
        {
            if (isValidMonsterAttackTarget(m_members[memberIndex]))
            {
                candidates.push_back(memberIndex);
            }
        }
    }

    if (candidates.empty())
    {
        return std::nullopt;
    }

    const uint32_t selectionSeed =
        seedHint * 1103515245u + m_monsterTargetSelectionCounter * 2654435761u + 12345u;
    ++m_monsterTargetSelectionCounter;
    return candidates[selectionSeed % candidates.size()];
}

void Party::addGold(int amount)
{
    m_gold = std::max(0, m_gold + amount);
}

void Party::addFood(int amount)
{
    m_food = std::max(0, m_food + amount);
}

bool Party::tryGrantItem(uint32_t objectDescriptionId, uint32_t quantity)
{
    if (objectDescriptionId == 0 || quantity == 0)
    {
        return false;
    }

    std::vector<Character> testMembers = m_members;

    for (uint32_t itemCount = 0; itemCount < quantity; ++itemCount)
    {
        InventoryItem item = {};
        item.objectDescriptionId = objectDescriptionId;
        item.quantity = 1;
        item.width = resolveInventoryWidth(objectDescriptionId);
        item.height = resolveInventoryHeight(objectDescriptionId);

        bool added = false;

        for (Character &member : testMembers)
        {
            if (member.addInventoryItem(item))
            {
                added = true;
                break;
            }
        }

        if (!added)
        {
            m_lastStatus = "inventory full";
            return false;
        }
    }

    m_members = std::move(testMembers);
    return true;
}

void Party::grantItem(uint32_t objectDescriptionId, uint32_t quantity)
{
    if (!tryGrantItem(objectDescriptionId, quantity))
    {
        return;
    }
}

bool Party::removeItem(uint32_t objectDescriptionId, uint32_t quantity)
{
    if (objectDescriptionId == 0 || quantity == 0)
    {
        return false;
    }

    uint32_t availableCount = 0;

    for (const Character &member : m_members)
    {
        for (const InventoryItem &item : member.inventory)
        {
            if (item.objectDescriptionId == objectDescriptionId)
            {
                availableCount += item.quantity;
            }
        }
    }

    if (availableCount < quantity)
    {
        return false;
    }

    uint32_t removedCount = 0;

    for (Character &member : m_members)
    {
        while (removedCount < quantity && member.removeInventoryItem(objectDescriptionId))
        {
            removedCount += 1;
        }
    }

    return removedCount == quantity;
}

bool Party::needsHealing() const
{
    for (const Character &member : m_members)
    {
        if (member.health < member.maxHealth || member.spellPoints < member.maxSpellPoints)
        {
            return true;
        }
    }

    return false;
}

bool Party::activeMemberNeedsHealing() const
{
    const Character *pMember = activeMember();

    if (pMember == nullptr)
    {
        return false;
    }

    return pMember->health < pMember->maxHealth || pMember->spellPoints < pMember->maxSpellPoints;
}

void Party::restoreAll()
{
    for (Character &member : m_members)
    {
        member.health = member.maxHealth;
        member.spellPoints = member.maxSpellPoints;
        member.conditions.reset(static_cast<size_t>(CharacterCondition::Unconscious));
        member.conditions.reset(static_cast<size_t>(CharacterCondition::Dead));
    }
}

void Party::restoreActiveMember()
{
    Character *pMember = activeMember();

    if (pMember == nullptr)
    {
        return;
    }

    pMember->health = pMember->maxHealth;
    pMember->spellPoints = pMember->maxSpellPoints;
    pMember->conditions.reset(static_cast<size_t>(CharacterCondition::Unconscious));
    pMember->conditions.reset(static_cast<size_t>(CharacterCondition::Dead));
}

bool Party::trainLeader(uint32_t maxLevel, uint32_t &newLevel, uint32_t &skillPointsEarned)
{
    newLevel = 0;
    skillPointsEarned = 0;

    if (m_members.empty())
    {
        return false;
    }

    Character &leader = m_members.front();

    if (maxLevel > 0 && leader.level >= maxLevel)
    {
        return false;
    }

    leader.level += 1;
    skillPointsEarned = 5 + leader.level / 10;
    leader.skillPoints += skillPointsEarned;
    leader.health = leader.maxHealth;
    leader.spellPoints = leader.maxSpellPoints;
    newLevel = leader.level;
    return true;
}

bool Party::trainActiveMember(uint32_t maxLevel, uint32_t &newLevel, uint32_t &skillPointsEarned)
{
    newLevel = 0;
    skillPointsEarned = 0;

    Character *pMember = activeMember();

    if (pMember == nullptr)
    {
        return false;
    }

    if (maxLevel > 0 && pMember->level >= maxLevel)
    {
        return false;
    }

    pMember->level += 1;
    skillPointsEarned = 5 + pMember->level / 10;
    pMember->skillPoints += skillPointsEarned;
    pMember->health = pMember->maxHealth;
    pMember->spellPoints = pMember->maxSpellPoints;
    newLevel = pMember->level;
    return true;
}

bool Party::canActiveMemberLearnSkill(const std::string &skillName) const
{
    const Character *pMember = activeMember();
    const std::string canonicalSkill = canonicalSkillName(skillName);

    if (pMember == nullptr || canonicalSkill.empty() || m_pClassSkillTable == nullptr || pMember->hasSkill(canonicalSkill))
    {
        return false;
    }

    return m_pClassSkillTable->getClassCap(pMember->className, canonicalSkill) != SkillMastery::None;
}

bool Party::learnActiveMemberSkill(const std::string &skillName)
{
    if (!canActiveMemberLearnSkill(skillName))
    {
        return false;
    }

    Character *pMember = activeMember();

    if (pMember == nullptr)
    {
        return false;
    }

    CharacterSkill skill = {};
    skill.name = canonicalSkillName(skillName);
    skill.level = 1;
    skill.mastery = SkillMastery::Normal;
    pMember->skills[skill.name] = skill;
    return true;
}

bool Party::canIncreaseActiveMemberSkillLevel(const std::string &skillName) const
{
    const Character *pMember = activeMember();
    const std::string canonicalSkill = canonicalSkillName(skillName);

    if (pMember == nullptr || canonicalSkill.empty())
    {
        return false;
    }

    const CharacterSkill *pSkill = pMember->findSkill(canonicalSkill);

    if (pSkill == nullptr)
    {
        return false;
    }

    return pMember->skillPoints > pSkill->level;
}

bool Party::increaseActiveMemberSkillLevel(const std::string &skillName)
{
    if (!canIncreaseActiveMemberSkillLevel(skillName))
    {
        return false;
    }

    Character *pMember = activeMember();

    if (pMember == nullptr)
    {
        return false;
    }

    CharacterSkill *pSkill = pMember->findSkill(skillName);

    if (pSkill == nullptr)
    {
        return false;
    }

    const uint32_t newSkillLevel = pSkill->level + 1;
    pSkill->level = newSkillLevel;
    pMember->skillPoints -= newSkillLevel;
    return true;
}

int Party::depositAllGoldToBank()
{
    const int depositedGold = m_gold;
    m_bankGold += depositedGold;
    m_gold = 0;
    return depositedGold;
}

int Party::withdrawAllBankGold()
{
    const int withdrawnGold = m_bankGold;
    m_gold += withdrawnGold;
    m_bankGold = 0;
    return withdrawnGold;
}

bool Party::isFull() const
{
    return m_members.size() >= MaxMembers;
}

bool Party::recruitRosterMember(const RosterEntry &rosterEntry)
{
    if (isFull())
    {
        return false;
    }

    Character member = {};
    member.name = rosterEntry.name;
    member.className = canonicalClassName(rosterEntry.className);
    member.role = normalizeRoleName(member.className);
    member.portraitTextureName = portraitTextureNameFromPictureId(rosterEntry.pictureId);
    member.portraitPictureId = rosterEntry.pictureId;
    member.rosterId = rosterEntry.id;
    member.birthYear = rosterEntry.birthYear;
    member.experience = rosterEntry.experience;
    member.level = std::max<uint32_t>(1, rosterEntry.level);
    member.skillPoints = rosterEntry.skillPoints;
    member.might = rosterEntry.might;
    member.intellect = rosterEntry.intellect;
    member.personality = rosterEntry.personality;
    member.endurance = rosterEntry.endurance;
    member.speed = rosterEntry.speed;
    member.accuracy = rosterEntry.accuracy;
    member.luck = rosterEntry.luck;
    member.baseResistances = rosterEntry.baseResistances;
    member.skills = rosterEntry.skills;

    const int endurance = std::max(10, static_cast<int>(rosterEntry.endurance));
    const int intellect = std::max(0, static_cast<int>(rosterEntry.intellect));
    const int personality = std::max(0, static_cast<int>(rosterEntry.personality));

    member.maxHealth = std::max(1, 40 + endurance * 2 + static_cast<int>(member.level) * 5);
    member.health = member.maxHealth;

    const bool isCaster = intellect > 0 || personality > 0;
    member.maxSpellPoints = isCaster
        ? std::max(0, ((intellect + personality) / 2) + static_cast<int>(member.level) * 3)
        : 0;
    member.spellPoints = member.maxSpellPoints;

    m_members.push_back(std::move(member));

    const size_t memberIndex = m_members.size() - 1;

    for (uint32_t itemId : rosterEntry.startingInventoryItemIds)
    {
        grantItemToMember(memberIndex, itemId);
    }

    m_lastStatus = "party member recruited";
    return true;
}

bool Party::hasRosterMember(uint32_t rosterId) const
{
    if (rosterId == 0)
    {
        return false;
    }

    for (const Character &member : m_members)
    {
        if (member.rosterId == rosterId)
        {
            return true;
        }
    }

    return false;
}

bool Party::hasAward(uint32_t awardId) const
{
    if (awardId == 0)
    {
        return false;
    }

    for (const Character &member : m_members)
    {
        if (member.awards.contains(awardId))
        {
            return true;
        }
    }

    return false;
}

bool Party::hasAward(size_t memberIndex, uint32_t awardId) const
{
    const Character *pMember = member(memberIndex);
    return pMember != nullptr && awardId != 0 && pMember->awards.contains(awardId);
}

void Party::addAward(uint32_t awardId)
{
    if (awardId == 0)
    {
        return;
    }

    for (Character &member : m_members)
    {
        member.awards.insert(awardId);
    }
}

void Party::addAward(size_t memberIndex, uint32_t awardId)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr || awardId == 0)
    {
        return;
    }

    pMember->awards.insert(awardId);
}

void Party::removeAward(uint32_t awardId)
{
    if (awardId == 0)
    {
        return;
    }

    for (Character &member : m_members)
    {
        member.awards.erase(awardId);
    }
}

void Party::removeAward(size_t memberIndex, uint32_t awardId)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr || awardId == 0)
    {
        return;
    }

    pMember->awards.erase(awardId);
}

int Party::inventoryItemCount(uint32_t objectDescriptionId, std::optional<size_t> memberIndex) const
{
    if (objectDescriptionId == 0)
    {
        return 0;
    }

    int totalCount = 0;

    auto countMemberItems = [&](const Character &member)
    {
        for (const InventoryItem &item : member.inventory)
        {
            if (item.objectDescriptionId == objectDescriptionId)
            {
                totalCount += static_cast<int>(item.quantity);
            }
        }
    };

    if (memberIndex)
    {
        const Character *pMember = member(*memberIndex);

        if (pMember != nullptr)
        {
            countMemberItems(*pMember);
        }

        return totalCount;
    }

    for (const Character &member : m_members)
    {
        countMemberItems(member);
    }

    return totalCount;
}

bool Party::grantItemToMember(size_t memberIndex, uint32_t objectDescriptionId, uint32_t quantity)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr || objectDescriptionId == 0 || quantity == 0)
    {
        return false;
    }

    for (uint32_t itemIndex = 0; itemIndex < quantity; ++itemIndex)
    {
        InventoryItem item = {};
        item.objectDescriptionId = objectDescriptionId;
        item.quantity = 1;
        item.width = resolveInventoryWidth(objectDescriptionId);
        item.height = resolveInventoryHeight(objectDescriptionId);

        if (!pMember->addInventoryItem(item))
        {
            return false;
        }
    }

    m_lastStatus = "item granted";
    return true;
}

bool Party::removeItemFromMember(size_t memberIndex, uint32_t objectDescriptionId, uint32_t quantity)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr || objectDescriptionId == 0 || quantity == 0)
    {
        return false;
    }

    for (uint32_t itemIndex = 0; itemIndex < quantity; ++itemIndex)
    {
        if (!pMember->removeInventoryItem(objectDescriptionId))
        {
            return false;
        }
    }

    m_lastStatus = "item removed";
    return true;
}

bool Party::takeItemFromMemberInventoryCell(size_t memberIndex, uint8_t gridX, uint8_t gridY, InventoryItem &item)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    if (!pMember->takeInventoryItemAt(gridX, gridY, item))
    {
        return false;
    }

    m_lastStatus = "item picked up";
    return true;
}

bool Party::tryAutoPlaceItemInMemberInventory(size_t memberIndex, const InventoryItem &item)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    if (!pMember->addInventoryItem(item))
    {
        m_lastStatus = "inventory full";
        return false;
    }

    m_lastStatus = "item moved";
    return true;
}

bool Party::tryPlaceItemInMemberInventoryCell(
    size_t memberIndex,
    const InventoryItem &item,
    uint8_t gridX,
    uint8_t gridY,
    std::optional<InventoryItem> &replacedItem)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        replacedItem.reset();
        return false;
    }

    if (!pMember->tryPlaceInventoryItemAt(item, gridX, gridY, replacedItem))
    {
        return false;
    }

    m_lastStatus = replacedItem.has_value() ? "item swapped" : "item moved";
    return true;
}

bool Party::takeEquippedItemFromMember(size_t memberIndex, EquipmentSlot slot, InventoryItem &item)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    const uint32_t itemId = equippedItemId(pMember->equipment, slot);

    if (itemId == 0)
    {
        return false;
    }

    item = {};
    item.objectDescriptionId = itemId;
    item.quantity = 1;
    item.width = resolveInventoryWidth(itemId);
    item.height = resolveInventoryHeight(itemId);
    equippedItemId(pMember->equipment, slot) = 0;
    m_lastStatus = "item unequipped";
    return true;
}

bool Party::tryEquipItemOnMember(
    size_t memberIndex,
    EquipmentSlot targetSlot,
    const InventoryItem &item,
    std::optional<EquipmentSlot> displacedSlot,
    bool autoStoreDisplacedItem,
    std::optional<InventoryItem> &heldReplacement)
{
    heldReplacement.reset();

    Character *pMember = member(memberIndex);

    if (pMember == nullptr || item.objectDescriptionId == 0)
    {
        return false;
    }

    if (displacedSlot && *displacedSlot != targetSlot && equippedItemId(pMember->equipment, targetSlot) != 0)
    {
        return false;
    }

    if (!displacedSlot && equippedItemId(pMember->equipment, targetSlot) != 0)
    {
        displacedSlot = targetSlot;
    }

    const uint32_t displacedItemId =
        displacedSlot ? equippedItemId(pMember->equipment, *displacedSlot) : 0;

    if (autoStoreDisplacedItem && displacedItemId != 0)
    {
        InventoryItem displacedInventoryItem = {};
        displacedInventoryItem.objectDescriptionId = displacedItemId;
        displacedInventoryItem.quantity = 1;
        displacedInventoryItem.width = resolveInventoryWidth(displacedItemId);
        displacedInventoryItem.height = resolveInventoryHeight(displacedItemId);

        if (!pMember->addInventoryItem(displacedInventoryItem))
        {
            m_lastStatus = "inventory full";
            return false;
        }
    }

    if (displacedSlot)
    {
        equippedItemId(pMember->equipment, *displacedSlot) = 0;
    }

    equippedItemId(pMember->equipment, targetSlot) = item.objectDescriptionId;

    if (!autoStoreDisplacedItem && displacedItemId != 0)
    {
        InventoryItem displacedInventoryItem = {};
        displacedInventoryItem.objectDescriptionId = displacedItemId;
        displacedInventoryItem.quantity = 1;
        displacedInventoryItem.width = resolveInventoryWidth(displacedItemId);
        displacedInventoryItem.height = resolveInventoryHeight(displacedItemId);
        heldReplacement = displacedInventoryItem;
        m_lastStatus = "item swapped";
    }
    else
    {
        m_lastStatus = "item equipped";
    }

    return true;
}

bool Party::setMemberClassName(size_t memberIndex, const std::string &className)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    pMember->className = canonicalClassName(className);
    pMember->role = normalizeRoleName(pMember->className);
    m_lastStatus = "class changed";
    return true;
}

const Character *Party::member(size_t memberIndex) const
{
    if (memberIndex >= m_members.size())
    {
        return nullptr;
    }

    return &m_members[memberIndex];
}

Character *Party::member(size_t memberIndex)
{
    if (memberIndex >= m_members.size())
    {
        return nullptr;
    }

    return &m_members[memberIndex];
}

bool Party::canSelectMemberInGameplay(size_t memberIndex) const
{
    const Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    return GameMechanics::canSelectInGameplay(*pMember);
}

bool Party::hasSelectableMemberInGameplay() const
{
    for (size_t memberIndex = 0; memberIndex < m_members.size(); ++memberIndex)
    {
        if (canSelectMemberInGameplay(memberIndex))
        {
            return true;
        }
    }

    return false;
}

uint8_t Party::resolveInventoryWidth(uint32_t objectDescriptionId) const
{
    if (m_pItemTable == nullptr)
    {
        return 1;
    }

    const ItemDefinition *pItemDefinition = m_pItemTable->get(objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        return 1;
    }

    return std::max<uint8_t>(1, pItemDefinition->inventoryWidth);
}

uint8_t Party::resolveInventoryHeight(uint32_t objectDescriptionId) const
{
    if (m_pItemTable == nullptr)
    {
        return 1;
    }

    const ItemDefinition *pItemDefinition = m_pItemTable->get(objectDescriptionId);

    if (pItemDefinition == nullptr)
    {
        return 1;
    }

    return std::max<uint8_t>(1, pItemDefinition->inventoryHeight);
}

const std::vector<Character> &Party::members() const
{
    return m_members;
}

bool Party::setActiveMemberIndex(size_t memberIndex)
{
    if (memberIndex >= m_members.size())
    {
        return false;
    }

    m_activeMemberIndex = memberIndex;
    return true;
}

bool Party::canSpendSpellPoints(size_t memberIndex, int amount) const
{
    const Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    return amount <= 0 || pMember->spellPoints >= amount;
}

bool Party::spendSpellPoints(size_t memberIndex, int amount)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    if (amount <= 0)
    {
        return true;
    }

    if (pMember->spellPoints < amount)
    {
        return false;
    }

    pMember->spellPoints -= amount;
    return true;
}

bool Party::spendSpellPointsOnActiveMember(int amount)
{
    return spendSpellPoints(activeMemberIndex(), amount);
}

void Party::updateRecovery(float deltaSeconds)
{
    if (deltaSeconds <= 0.0f)
    {
        return;
    }

    for (Character &member : m_members)
    {
        member.recoverySecondsRemaining = std::max(0.0f, member.recoverySecondsRemaining - deltaSeconds);
    }

    bool buffsChanged = false;

    for (PartyBuffState &buff : m_partyBuffs)
    {
        if (!buff.active())
        {
            continue;
        }

        const float previousRemainingSeconds = buff.remainingSeconds;
        buff.remainingSeconds = std::max(0.0f, buff.remainingSeconds - deltaSeconds);

        if (previousRemainingSeconds > 0.0f && buff.remainingSeconds <= 0.0f)
        {
            buffsChanged = true;

            if (isSpellId(buff.spellId, SpellId::Haste))
            {
                for (Character &member : m_members)
                {
                    member.conditions.set(static_cast<size_t>(CharacterCondition::Weak));
                }
            }
        }
    }

    for (size_t memberIndex = 0; memberIndex < m_members.size() && memberIndex < m_characterBuffs.size(); ++memberIndex)
    {
        for (CharacterBuffState &buff : m_characterBuffs[memberIndex])
        {
            if (!buff.active())
            {
                continue;
            }

            const float previousRemainingSeconds = buff.remainingSeconds;
            buff.remainingSeconds = std::max(0.0f, buff.remainingSeconds - deltaSeconds);

            if (isSpellId(buff.spellId, SpellId::Regeneration))
            {
                buff.periodicAccumulatorSeconds += deltaSeconds;
                const float tickIntervalSeconds = buff.skillMastery == SkillMastery::Grandmaster
                    ? 0.5f
                    : buff.skillMastery == SkillMastery::Master
                    ? 0.75f
                    : 1.0f;
                const int healPerTick = std::max(1, buff.power);

                while (buff.periodicAccumulatorSeconds >= tickIntervalSeconds)
                {
                    buff.periodicAccumulatorSeconds -= tickIntervalSeconds;
                    healMember(memberIndex, healPerTick);
                }
            }

            if (previousRemainingSeconds > 0.0f && buff.remainingSeconds <= 0.0f)
            {
                buffsChanged = true;
                buff.periodicAccumulatorSeconds = 0.0f;
            }
        }
    }

    if (buffsChanged)
    {
        rebuildMagicalBonusesFromBuffs();
    }

    if (!canSelectMemberInGameplay(m_activeMemberIndex))
    {
        switchToNextReadyMember();
    }
}

bool Party::applyRecoveryToMember(size_t memberIndex, float recoverySeconds)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    pMember->recoverySecondsRemaining = std::max(pMember->recoverySecondsRemaining, std::max(0.0f, recoverySeconds));
    return true;
}

bool Party::applyRecoveryToActiveMember(float recoverySeconds)
{
    return applyRecoveryToMember(m_activeMemberIndex, recoverySeconds);
}

bool Party::switchToNextReadyMember()
{
    if (m_members.empty())
    {
        return false;
    }

    const size_t currentIndex = std::min(m_activeMemberIndex, m_members.size() - 1);

    for (size_t offset = 1; offset <= m_members.size(); ++offset)
    {
        const size_t candidateIndex = (currentIndex + offset) % m_members.size();

        if (canSelectMemberInGameplay(candidateIndex))
        {
            m_activeMemberIndex = candidateIndex;
            return true;
        }
    }

    return false;
}

void Party::applyPartyBuff(
    PartyBuffId buffId,
    float durationSeconds,
    int power,
    uint32_t spellId,
    uint32_t skillLevel,
    SkillMastery skillMastery,
    uint32_t casterMemberIndex)
{
    PartyBuffState &buff = m_partyBuffs[static_cast<size_t>(buffId)];
    buff.remainingSeconds = std::max(buff.remainingSeconds, std::max(0.0f, durationSeconds));
    buff.spellId = spellId;
    buff.skillLevel = skillLevel;
    buff.skillMastery = skillMastery;
    buff.power = power;
    buff.casterMemberIndex = casterMemberIndex;
    rebuildMagicalBonusesFromBuffs();
}

void Party::applyCharacterBuff(
    size_t memberIndex,
    CharacterBuffId buffId,
    float durationSeconds,
    int power,
    uint32_t spellId,
    uint32_t skillLevel,
    SkillMastery skillMastery,
    uint32_t casterMemberIndex)
{
    if (memberIndex >= m_members.size() || memberIndex >= m_characterBuffs.size())
    {
        return;
    }

    CharacterBuffState &buff = m_characterBuffs[memberIndex][static_cast<size_t>(buffId)];
    buff.remainingSeconds = std::max(buff.remainingSeconds, std::max(0.0f, durationSeconds));
    buff.spellId = spellId;
    buff.skillLevel = skillLevel;
    buff.skillMastery = skillMastery;
    buff.power = power;
    buff.casterMemberIndex = casterMemberIndex;
    rebuildMagicalBonusesFromBuffs();
}

void Party::clearPartyBuff(PartyBuffId buffId)
{
    m_partyBuffs[static_cast<size_t>(buffId)] = {};
    rebuildMagicalBonusesFromBuffs();
}

void Party::clearCharacterBuff(size_t memberIndex, CharacterBuffId buffId)
{
    if (memberIndex >= m_members.size() || memberIndex >= m_characterBuffs.size())
    {
        return;
    }

    m_characterBuffs[memberIndex][static_cast<size_t>(buffId)] = {};
    rebuildMagicalBonusesFromBuffs();
}

bool Party::hasPartyBuff(PartyBuffId buffId) const
{
    return m_partyBuffs[static_cast<size_t>(buffId)].active();
}

bool Party::hasCharacterBuff(size_t memberIndex, CharacterBuffId buffId) const
{
    return characterBuff(memberIndex, buffId) != nullptr;
}

const PartyBuffState *Party::partyBuff(PartyBuffId buffId) const
{
    const PartyBuffState &buff = m_partyBuffs[static_cast<size_t>(buffId)];
    return buff.active() ? &buff : nullptr;
}

const CharacterBuffState *Party::characterBuff(size_t memberIndex, CharacterBuffId buffId) const
{
    if (memberIndex >= m_members.size() || memberIndex >= m_characterBuffs.size())
    {
        return nullptr;
    }

    const CharacterBuffState &buff = m_characterBuffs[memberIndex][static_cast<size_t>(buffId)];
    return buff.active() ? &buff : nullptr;
}

bool Party::clearMemberCondition(size_t memberIndex, CharacterCondition condition)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    pMember->conditions.reset(static_cast<size_t>(condition));
    return true;
}

bool Party::healMember(size_t memberIndex, int amount)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr || amount <= 0)
    {
        return false;
    }

    const int maxHealth =
        std::max(1, pMember->maxHealth + pMember->permanentBonuses.maxHealth + pMember->magicalBonuses.maxHealth);
    const int previousHealth = pMember->health;
    pMember->health = std::clamp(pMember->health + amount, 0, maxHealth);
    updateMemberIncapacitatedCondition(
        *pMember,
        m_characterBuffs[memberIndex][static_cast<size_t>(CharacterBuffId::Preservation)].active());
    return pMember->health > previousHealth;
}

bool Party::reviveMember(size_t memberIndex, int health, bool applyWeak)
{
    Character *pMember = member(memberIndex);

    if (pMember == nullptr)
    {
        return false;
    }

    pMember->conditions.reset(static_cast<size_t>(CharacterCondition::Unconscious));
    pMember->conditions.reset(static_cast<size_t>(CharacterCondition::Dead));
    pMember->conditions.reset(static_cast<size_t>(CharacterCondition::Petrified));
    pMember->conditions.reset(static_cast<size_t>(CharacterCondition::Eradicated));
    pMember->conditions.reset(static_cast<size_t>(CharacterCondition::Zombie));
    pMember->health = std::max(1, health);

    if (applyWeak)
    {
        pMember->conditions.set(static_cast<size_t>(CharacterCondition::Weak));
    }

    return true;
}

const Character *Party::activeMember() const
{
    if (m_members.empty())
    {
        return nullptr;
    }

    return &m_members[std::min(m_activeMemberIndex, m_members.size() - 1)];
}

Character *Party::activeMember()
{
    if (m_members.empty())
    {
        return nullptr;
    }

    return &m_members[std::min(m_activeMemberIndex, m_members.size() - 1)];
}

size_t Party::activeMemberIndex() const
{
    return m_members.empty() ? 0 : std::min(m_activeMemberIndex, m_members.size() - 1);
}

int Party::totalHealth() const
{
    int totalHealth = 0;

    for (const Character &member : m_members)
    {
        totalHealth += member.health;
    }

    return totalHealth;
}

int Party::totalMaxHealth() const
{
    int totalMaxHealth = 0;

    for (const Character &member : m_members)
    {
        totalMaxHealth += member.maxHealth;
    }

    return totalMaxHealth;
}

int Party::gold() const
{
    return m_gold;
}

int Party::bankGold() const
{
    return m_bankGold;
}

int Party::food() const
{
    return m_food;
}

size_t Party::inventoryItemCount() const
{
    size_t itemCount = 0;

    for (const Character &member : m_members)
    {
        itemCount += member.inventoryItemCount();
    }

    return itemCount;
}

size_t Party::usedInventoryCells() const
{
    size_t usedCells = 0;

    for (const Character &member : m_members)
    {
        usedCells += member.usedInventoryCells();
    }

    return usedCells;
}

size_t Party::inventoryCapacity() const
{
    size_t capacity = 0;

    for (const Character &member : m_members)
    {
        capacity += member.inventoryCapacity();
    }

    return capacity;
}

uint32_t Party::waterDamageTicks() const
{
    return m_waterDamageTicks;
}

uint32_t Party::burningDamageTicks() const
{
    return m_burningDamageTicks;
}

uint32_t Party::splashCount() const
{
    return m_splashCount;
}

uint32_t Party::landingSoundCount() const
{
    return m_landingSoundCount;
}

uint32_t Party::hardLandingSoundCount() const
{
    return m_hardLandingSoundCount;
}

float Party::lastFallDamageDistance() const
{
    return m_lastFallDamageDistance;
}

const std::string &Party::lastStatus() const
{
    return m_lastStatus;
}

void Party::rebuildMagicalBonusesFromBuffs()
{
    for (Character &member : m_members)
    {
        member.magicalBonuses = {};
        member.magicalImmunities = {};
        member.merchantBonus = 0;
        member.weaponEnchantmentDamageBonus = 0;
        member.vampiricHealFraction = 0.0f;
        member.physicalAttackDisabled = false;
        member.physicalDamageImmune = false;
    }

    const auto applyResistanceBonus =
        [this](PartyBuffId buffId, auto CharacterResistanceSet::*field)
        {
            const PartyBuffState &buff = m_partyBuffs[static_cast<size_t>(buffId)];

            if (!buff.active())
            {
                return;
            }

            for (Character &member : m_members)
            {
                member.magicalBonuses.resistances.*field += buff.power;
            }
        };

    applyResistanceBonus(PartyBuffId::FireResistance, &CharacterResistanceSet::fire);
    applyResistanceBonus(PartyBuffId::WaterResistance, &CharacterResistanceSet::water);
    applyResistanceBonus(PartyBuffId::AirResistance, &CharacterResistanceSet::air);
    applyResistanceBonus(PartyBuffId::EarthResistance, &CharacterResistanceSet::earth);
    applyResistanceBonus(PartyBuffId::MindResistance, &CharacterResistanceSet::mind);
    applyResistanceBonus(PartyBuffId::BodyResistance, &CharacterResistanceSet::body);

    if (const PartyBuffState *pBuff = partyBuff(PartyBuffId::Stoneskin))
    {
        for (Character &member : m_members)
        {
            member.magicalBonuses.armorClass += pBuff->power;
        }
    }

    if (const PartyBuffState *pBuff = partyBuff(PartyBuffId::Heroism))
    {
        for (Character &member : m_members)
        {
            member.magicalBonuses.meleeDamage += pBuff->power;
            member.magicalBonuses.rangedDamage += pBuff->power;
        }
    }

    if (const PartyBuffState *pBuff = partyBuff(PartyBuffId::DayOfGods))
    {
        for (Character &member : m_members)
        {
            member.magicalBonuses.might += pBuff->power;
            member.magicalBonuses.intellect += pBuff->power;
            member.magicalBonuses.personality += pBuff->power;
            member.magicalBonuses.endurance += pBuff->power;
            member.magicalBonuses.speed += pBuff->power;
            member.magicalBonuses.accuracy += pBuff->power;
            member.magicalBonuses.luck += pBuff->power;
        }
    }

    if (const PartyBuffState *pBuff = partyBuff(PartyBuffId::ProtectionFromMagic))
    {
        for (Character &member : m_members)
        {
            member.magicalBonuses.resistances.fire += pBuff->power;
            member.magicalBonuses.resistances.air += pBuff->power;
            member.magicalBonuses.resistances.water += pBuff->power;
            member.magicalBonuses.resistances.earth += pBuff->power;
            member.magicalBonuses.resistances.mind += pBuff->power;
            member.magicalBonuses.resistances.body += pBuff->power;
            member.magicalBonuses.resistances.spirit += pBuff->power;
        }
    }

    if (const PartyBuffState *pBuff = partyBuff(PartyBuffId::Glamour))
    {
        for (Character &member : m_members)
        {
            member.merchantBonus += pBuff->power;
        }
    }

    for (size_t memberIndex = 0; memberIndex < m_members.size() && memberIndex < m_characterBuffs.size(); ++memberIndex)
    {
        Character &member = m_members[memberIndex];

        if (const CharacterBuffState *pBuff = characterBuff(memberIndex, CharacterBuffId::Bless))
        {
            member.magicalBonuses.meleeAttack += pBuff->power;
            member.magicalBonuses.rangedAttack += pBuff->power;
        }

        if (const CharacterBuffState *pBuff = characterBuff(memberIndex, CharacterBuffId::Fate))
        {
            member.magicalBonuses.meleeAttack += pBuff->power;
            member.magicalBonuses.rangedAttack += pBuff->power;
        }

        if (const CharacterBuffState *pBuff = characterBuff(memberIndex, CharacterBuffId::Hammerhands))
        {
            member.magicalBonuses.meleeDamage += pBuff->power;
        }

        if (const CharacterBuffState *pBuff = characterBuff(memberIndex, CharacterBuffId::FireAura))
        {
            member.weaponEnchantmentDamageBonus += pBuff->power;
            member.magicalBonuses.meleeDamage += pBuff->power;
            member.magicalBonuses.rangedDamage += pBuff->power;
        }

        if (const CharacterBuffState *pBuff = characterBuff(memberIndex, CharacterBuffId::VampiricWeapon))
        {
            member.vampiricHealFraction = std::max(member.vampiricHealFraction, static_cast<float>(pBuff->power) / 100.0f);
        }

        if (const CharacterBuffState *pBuff = characterBuff(memberIndex, CharacterBuffId::Mistform))
        {
            static_cast<void>(pBuff);
            member.physicalAttackDisabled = true;
            member.physicalDamageImmune = true;
        }

        if (const CharacterBuffState *pBuff = characterBuff(memberIndex, CharacterBuffId::Glamour))
        {
            member.merchantBonus += pBuff->power;
        }
    }
}

void Party::applyDefaultStartingSkills(Character &member) const
{
    if (m_pClassSkillTable == nullptr)
    {
        return;
    }

    const std::vector<CharacterSkill> defaultSkills = m_pClassSkillTable->getDefaultSkillsForClass(member.className);

    for (const CharacterSkill &skill : defaultSkills)
    {
        member.skills[skill.name] = skill;
    }
}
}
