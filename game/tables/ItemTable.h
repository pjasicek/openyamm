#pragma once

#include "engine/AssetFileSystem.h"

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
enum class EquipmentSlot : uint8_t;

struct ItemEquipmentPlacement
{
    uint32_t dollType = 0;
    EquipmentSlot slot = {};
    int x = 0;
    int y = 0;
};

enum class ItemRarity : uint8_t
{
    Common = 0,
    Artifact,
    Relic,
    Special,
};

struct ItemContentEffect
{
    int might = 0;
    int intellect = 0;
    int personality = 0;
    int endurance = 0;
    int speed = 0;
    int accuracy = 0;
    int luck = 0;
    int maxHealth = 0;
    int maxSpellPoints = 0;
    int armorClass = 0;
    int meleeAttack = 0;
    int rangedAttack = 0;
    int meleeDamage = 0;
    int rangedDamage = 0;
    int allResistances = 0;
    int fireResistance = 0;
    int airResistance = 0;
    int waterResistance = 0;
    int earthResistance = 0;
    int mindResistance = 0;
    int bodyResistance = 0;
    int spiritResistance = 0;
    int weaponDamage = 0;
    int recoveryReductionTicks = 0;
    float healthRegenPerSecond = 0.0f;
    float spellRegenPerSecond = 0.0f;
    std::unordered_map<std::string, int> skillBonuses;
    std::vector<std::string> flags;
};

struct ItemSetBonusDefinition
{
    std::string setId;
    size_t requiredPieceCount = 0;
    std::string effectProfile;
    ItemContentEffect effect;
};

struct ItemDefinition
{
    uint32_t itemId = 0;
    std::string packageId = "engine";
    std::string canonicalId;
    uint32_t sourceItemId = 0;
    std::string iconName;
    std::string iconVirtualPath;
    std::string name;
    int value = 0;
    std::string equipStat;
    std::string skillGroup;
    std::string mod1;
    std::string mod2;
    int material = 0;
    std::string materialName;
    ItemRarity rarity = ItemRarity::Common;
    std::string idRepSt;
    int identifyRepairDifficulty = 0;
    std::string unidentifiedName;
    uint16_t spriteIndex = 0;
    int varA = 0;
    int varB = 0;
    int equipX = 0;
    int equipY = 0;
    std::string notes;
    std::vector<std::string> contentFlags;
    // Worlds whose maps generate this item at random and stock it (content flags "World:<id>"); empty: all.
    std::vector<std::string> worldIds;
    uint8_t normalizedTier = 0;
    std::string useAction;
    std::string useTarget;
    std::string setId;
    std::string effectProfile;
    std::vector<std::string> allowedClassRoots;
    int requiredMight = 0;
    int requiredAccuracy = 0;
    std::string visualStatus;
    ItemContentEffect contentEffect;
    float inventoryDrawScale = 1.0f;
    float jewelryDrawScale = 1.0f;
    std::vector<ItemEquipmentPlacement> equipmentPlacements;
    uint8_t inventoryWidth = 1;
    uint8_t inventoryHeight = 1;
    std::array<int, 6> randomTreasureWeights = {};
    std::string sourceEquipType;
    std::string sourceSkill;
    std::string sourceIconPath;
    std::string importStatus;
    std::string balanceProfile;

    bool isGold() const;
    bool hasContentFlag(const std::string &flag) const;
    bool availableInWorld(const std::string &worldId) const;
};

class ItemTable
{
public:
    bool load(
        const Engine::AssetFileSystem &assetFileSystem,
        const std::vector<std::vector<std::string>> &itemRows,
        const std::vector<std::vector<std::string>> &randomItemRows
    );
    bool loadVisualRows(const std::vector<std::vector<std::string>> &rows, std::string &errorMessage);
    bool loadContentEffectRows(const std::vector<std::vector<std::string>> &rows, std::string &errorMessage);
    bool loadItemSetRows(const std::vector<std::vector<std::string>> &rows, std::string &errorMessage);
    bool loadSourceAliasRows(const std::vector<std::vector<std::string>> &rows, std::string &errorMessage);
    const ItemDefinition *get(uint32_t itemId) const;
    const ItemDefinition *resolvePackageSourceItemId(const std::string &packageId, uint32_t sourceItemId) const;
    const ItemDefinition *findBySpriteIndex(uint16_t spriteIndex) const;
    // The first spellbook teaching the spell that the world may generate (its own MM6/MM7/MM8 book design).
    std::optional<uint32_t> spellbookItemIdForSpell(uint32_t spellId, const std::string &worldId) const;
    const std::vector<ItemDefinition> &entries() const;
    const std::vector<ItemSetBonusDefinition> &setBonuses() const;

private:
    std::vector<ItemDefinition> m_entries;
    std::vector<ItemSetBonusDefinition> m_setBonuses;
    std::unordered_map<std::string, uint32_t> m_sourceAliases;
};
}
