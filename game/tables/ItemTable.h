#pragma once

#include "engine/AssetFileSystem.h"
#include "game/tables/ItemModelBindings.h"

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Game
{
enum class EquipmentSlot : uint8_t;
class MergedPotionSettingTable;

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
    // Energy resistance (item_effects energy_resistance) and personal energy shield points (personal_shield).
    int energyResistance = 0;
    int personalShield = 0;
    // Hesper's columns after them (design/kreegan_world/ITEMS.md): seconds added to the personal shield's
    // regeneration delay (negative shortens it), points against the Hum, per-cent ranged (bows, blasters, guns), melee
    // and spell damage, per-cent Energy damage taken (negative takes less), and ticks off gun and melee recovery.
    float shieldRegenDelaySeconds = 0.0f;
    int humPoints = 0;
    int rangedDamagePercent = 0;
    int meleeDamagePercent = 0;
    int spellDamagePercent = 0;
    int energyDamageTakenPercent = 0;
    int gunRecoveryReductionTicks = 0;
    int meleeRecoveryReductionTicks = 0;
};

struct ItemSetBonusDefinition
{
    std::string setId;
    size_t requiredPieceCount = 0;
    std::string effectProfile;
    ItemContentEffect effect;
};

// A Workshop mod (a world's workshop_mods row): fitted to one item (InventoryItem::workshopModId), it gives its wearer
// its effect columns (as item_effects) while worn; a ShieldDamage<percent> flag in them adds to that weapon's damage to
// shields. It fits the equip stats in fits; never a relic or a quest item.
struct WorkshopModDefinition
{
    uint16_t id = 0;
    std::string name;
    std::vector<std::string> fits;
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
    // An MM6-MM8 potion (not the empty bottle): its strength is the item's standard enchant power.
    bool hasPotionPower = false;

    bool hasContentFlag(const std::string &flag) const;
    bool availableInWorld(const std::string &worldId) const;
    // A gold heap (equip stat "Gold"): picking it up adds its amount to the party purse.
    bool isGold() const;
};

// A world's own random loot (worlds/<id>/loot.yml): weighted item lists per loot class, and the class each treasure
// level rolls from. A world with one generates its random items only from it, so other worlds' items stay out.
struct WorldLootTable
{
    struct Entry
    {
        uint32_t itemId = 0;
        int weight = 0;
    };

    // Treasure levels 1-6 (level 7 rolls as 6): the class name.
    std::array<std::string, 6> classByTreasureLevel;
    std::unordered_map<std::string, std::vector<Entry>> classes;
    // Every item some class lists: a rare item rolls there only when listed.
    std::unordered_set<uint32_t> listedItemIds;
    // The curated enchantment pool (loot.yml enchantments), by the enchantments' table names ("of Health",
    // "Swift"), lower case: the standard bonuses its items may roll, and the special ones per class. Not curated: any.
    bool curatesEnchantments = false;
    std::unordered_set<std::string> standardEnchantments;
    std::unordered_map<std::string, std::unordered_set<std::string>> specialEnchantmentsByClass;

    const std::vector<Entry> *entriesForTreasureLevel(int treasureLevel) const;
    // The loot class of a treasure level (level 7 rolls as 6).
    const std::string &classForTreasureLevel(int treasureLevel) const;
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
    // workshop_mods rows: mod_id, name, fits (equip stats, | separated), then the item_effects columns.
    bool loadWorkshopModRows(const std::vector<std::vector<std::string>> &rows, std::string &errorMessage);
    const WorkshopModDefinition *workshopMod(uint16_t modId) const;
    // The mod fits the item: its equip stat is one the mod lists, and it is no relic or quest item.
    bool workshopModFits(const WorkshopModDefinition &mod, const ItemDefinition &item) const;
    bool loadSourceAliasRows(const std::vector<std::vector<std::string>> &rows, std::string &errorMessage);
    // A world's loot.yml, after the item rows are loaded: its items must exist.
    bool loadWorldLootYaml(const std::string &text, const std::string &worldId, std::string &errorMessage);
    // The world's own random loot, or null when it rolls from the shared tables.
    const WorldLootTable *worldLoot(const std::string &worldId) const;
    // The item pool a world's shops stock equipment from (ItemGenerator::shopPoolAllows): its own package when it has
    // items, else the merged MM6-MM8 base, "engine". An empty world id has no pool.
    std::string lootPoolForWorld(const std::string &worldId) const;
    // Worlds whose random artifacts come only from level-7 chest slots (world.yml chestArtifactsOnly).
    void setChestArtifactsOnlyWorlds(std::unordered_set<std::string> worldIds);
    bool chestArtifactsOnly(const std::string &worldId) const;
    // Worlds whose treasure markers always give an item (world.yml treasureMarkersItemsOnly).
    void setTreasureMarkersItemsOnlyWorlds(std::unordered_set<std::string> worldIds);
    bool treasureMarkersItemsOnly(const std::string &worldId) const;
    const ItemDefinition *get(uint32_t itemId) const;
    const ItemDefinition *resolvePackageSourceItemId(const std::string &packageId, uint32_t sourceItemId) const;
    const ItemDefinition *findBySpriteIndex(uint16_t spriteIndex) const;
    // The first spellbook teaching the spell that the world may generate (its own MM6/MM7/MM8 book design).
    std::optional<uint32_t> spellbookItemIdForSpell(uint32_t spellId, const std::string &worldId) const;
    const std::vector<ItemDefinition> &entries() const;
    const std::vector<ItemSetBonusDefinition> &setBonuses() const;
    // Binds every item to its icon's ground model (engine/world_items/items.yml), after the item rows are loaded.
    void setGroundModels(const ItemModelBindings &bindings);
    // Marks the potions listed in the potion settings, after the item rows are loaded.
    void applyPotionSettings(const MergedPotionSettingTable &potionSettingTable);
    // The model an item draws lying on the ground: its icon's binding, or the missing-model placeholder.
    const ItemModelBinding &groundModel(uint32_t itemId) const;
    // Whether the item's icon has a ground model of its own (false: it draws the placeholder).
    bool hasGroundModel(uint32_t itemId) const;

private:
    std::vector<ItemDefinition> m_entries;
    std::vector<ItemSetBonusDefinition> m_setBonuses;
    std::unordered_map<uint16_t, WorkshopModDefinition> m_workshopMods;
    std::unordered_map<std::string, uint32_t> m_sourceAliases;
    std::unordered_map<std::string, WorldLootTable> m_worldLoot;
    // Lower-case package ids that own at least one item.
    std::unordered_set<std::string> m_itemPackageIds;
    // Lower-case world ids.
    std::unordered_set<std::string> m_chestArtifactsOnlyWorlds;
    std::unordered_set<std::string> m_treasureMarkersItemsOnlyWorlds;
    std::vector<ItemModelBinding> m_groundModels;
    // By item id: index into m_groundModels, or -1 for the placeholder.
    std::vector<int32_t> m_groundModelIndexByItemId;
};
}
