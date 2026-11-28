#pragma once

#include "engine/AssetFileSystem.h"
#include "game/party/ImplantSocket.h"
#include "game/tables/ItemModelBindings.h"

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Game
{
enum class EquipmentSlot : uint8_t;
class MergedPotionSettingTable;
class SpecialItemEnchantTable;
class StandardItemEnchantTable;

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

// Hesper's implants (DECISIONS H-91): what one part of an implant does, as a share (per cent) of its wearer's totals.
// An implant has one or more parts (Adrenaline Gland: Recovery and a negative AllStats sparing Speed, in Standard also
// a negative MaxHealth).
enum class ImplantEffect : uint8_t
{
    // Neural Loom: more of total Intellect and Personality.
    IntellectPersonality,
    // Berserker's Seed: more damage dealt while a hostile is in melee reach, which drains HP and SP.
    BerserkDamage,
    // Converter: a share of the other six primary stats moved into the highest.
    Converter,
    // Kreegan Heart, Mana Gland (positive) and Adrenaline Gland's cost (negative): maximum HP and SP.
    MaxHealth,
    MaxSpellPoints,
    // All seven primary stats (Adrenaline Gland's cost: negative).
    AllStats,
    // Siphoner: a share of all damage dealt back as HP and as SP over ImplantSiphonSeconds.
    Siphon,
    // Reflex Mesh, Adrenaline Gland: recovery time cut by the share (several parts multiply).
    Recovery,
    // Ember Lattice, Chitin Graft: more of total fire resistance and armour class.
    FireResistance,
    ArmorClass,
    // Mirror Carapace: the chance to send a physical missile back at its shooter.
    Reflect,
    // Kinetic Coil: faster missiles and spells.
    ProjectileSpeed,
    // Hunter's Eye: more of total Accuracy.
    Accuracy,
};
constexpr size_t ImplantEffectCount = size_t(ImplantEffect::Accuracy) + 1;

// The implants table's effect names ("intellect_personality", "berserk", ...), by ImplantEffect.
std::optional<ImplantEffect> parseImplantEffect(std::string_view name);
// Only these parts may be negative (a cost).
bool implantEffectMayBeNegative(ImplantEffect effect);
// Stages I and II (H-91): II at the implant's kills, times the rules' evolve factor (MAW 3: 250 -> 750).
constexpr uint32_t ImplantStageCount = 2;
// The Implants level an implant's per-level share counts at most, in every ruleset (H-91).
constexpr int ImplantEffectLevelCap = 50;
// Siphoner pays its share out evenly over this time; Berserker's Seed drains this per cent of maximum HP and SP per
// second.
constexpr float ImplantSiphonSeconds = 2.0f;
constexpr float ImplantBerserkDrainPercentPerSecond = 5.0f;

struct ImplantDefinition;

// One ruleset's values of an implant part: per stage (I, II) the per cent at Implants 0 and per level.
struct ImplantShare
{
    std::array<float, ImplantStageCount> basePercent = {};
    std::array<float, ImplantStageCount> perLevelPercent = {};
};

// An implant's stage (1 or 2) at its kill count, its threshold multiplied by the rules' evolve factor, and the kills a
// stage needs (0 for stage 1).
uint32_t implantStage(const ImplantDefinition &implant, uint32_t kills, float evolveFactor);
uint32_t implantStageKills(const ImplantDefinition &implant, uint32_t stage, float evolveFactor);
// The stage's name shown after an implant's name ("{item} {stage}"): "I" or "II".
std::string implantStageName(uint32_t stage);
// A part's per cent at a stage and effect level: base + per level x min(level, ImplantEffectLevelCap).
float implantEffectPercent(const ImplantShare &share, uint32_t stage, int effectLevel);
// The part as the player reads it at that per cent ("+12.5 % of total Intellect and Personality"), translated; an
// AllStats part names the stats it spares (exceptStats, ImplantComponent).
std::string implantEffectText(ImplantEffect effect, float percent, uint8_t exceptStats = 0);
// A per cent as the inspect lines print it: a value with one decimal at most ("14.6", "12"), a rate (a base or a
// per-level share) with three significant digits at most ("0.415", "4.15", "10"); no trailing zeros.
std::string implantPercentText(float percent);
std::string implantRateText(float percent);
// The share of a total an implant adds (a positive per cent) or takes (a negative one), its size rounded down;
// nothing of a total of 0 or less.
int implantShareOf(int total, float percent);
// The factor a wearer's recovery times are multiplied by, the 30-tick floor included: the product of (1 - share) over
// its Recovery parts (implantRecoveryCut, from 1), then implantRecoveryFactor keeps it at ImplantMinimumRecoveryFactor
// or more, so that floor keeps at least one tick.
constexpr float ImplantMinimumRecoveryFactor = 1.0f / 30.0f;
float implantRecoveryCut(float factor, float recoveryPercent);
float implantRecoveryFactor(float product);
// The seven primary stats' data names in the order implants count them (Converter's ties, AllStats' except column).
constexpr std::array<std::string_view, 7> ImplantStatNames = {"might", "intellect", "personality", "endurance",
    "accuracy", "speed", "luck"};
// Converter: the changes to the seven primary stats' totals (Might, Intellect, Personality, Endurance, Accuracy,
// Speed, Luck) when the share of each of the other six (rounded down) moves into the highest, picked before the move
// (ties: the first in that order).
std::array<int, 7> implantConverterChanges(const std::array<int, 7> &totals, float percent);

// An effect flag Slaying<Kind> (SlayingDemon, SlayingUndead, SlayingDragon, SlayingOgre, SlayingElemental, SlayingElf,
// SlayingTitan): the weapon does double damage to monsters of that kind (MonsterKind bits), as the slaying
// enchantments. 0 for any other flag.
uint32_t itemSlayingKindFlag(const std::string &flag);
// The kinds an effect's Slaying flags name.
uint32_t itemSlayingKindFlags(const ItemContentEffect &effect);

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

// A world's implant (DECISIONS H-91): the socket an implant item (equip stat Implant) fits and its parts, each with its
// Standard values and MAW's (the table's maw_ columns; Standard's where empty), base + per level x min(Implants
// level, 50) per cent at each stage; stage II from its kill threshold on.
struct ImplantComponent
{
    ImplantEffect effect = ImplantEffect::IntellectPersonality;
    ImplantShare standard;
    ImplantShare maw;
    // AllStats only: the stats it leaves alone (the table's except column, "speed|luck"), bit i for stat i in
    // ImplantStatNames' order (Standard's Adrenaline Gland spares Speed).
    uint8_t exceptStats = 0;
};

struct ImplantDefinition
{
    ImplantSocket socket = ImplantSocket::Cranial;
    std::vector<ImplantComponent> components;
    uint32_t stageTwoKills = 250;
    // The sound an evolution to stage II plays (a sound id of the world's; 0: the engine's chime).
    uint32_t evolveSoundId = 0;
    // The sounds of fitting it into its socket and of taking it out (sound ids of the world's; 0: silent, as before).
    uint32_t fitSoundId = 0;
    uint32_t removeSoundId = 0;
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
    // The VarA column as written: a Special item's own enchantment by name (VarB: a standard one's power).
    std::string varAText;
    // That enchantment, resolved once the enchantment tables load (ItemTable::resolveSpecialItemEnchants); every copy
    // of the item carries it (ItemGenerator::assignSpecialItemEnchants).
    uint16_t specialItemStandardEnchantId = 0;
    uint16_t specialItemStandardEnchantPower = 0;
    uint16_t specialItemSpecialEnchantId = 0;
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
    // A world's implants rows, one per part (columns found by the header: item_id, socket, effect, base_i,
    // per_level_i, base_ii, per_level_ii, maw_base_i, maw_per_level_i, maw_base_ii, maw_per_level_ii, evolve_ii,
    // evolve_sound, fit_sound, remove_sound; the sound columns may be left out), after the items: every row names an
    // Implant item, every Implant item of a package with rows has one, an item's rows agree on socket, evolution and
    // sounds, and no implant item's own effects raise Implants.
    bool loadImplantRows(const std::vector<std::vector<std::string>> &rows, std::string &errorMessage);
    const ImplantDefinition *implant(uint32_t itemId) const;
    // A mounted world provides implants rows (Hesper): the Implants skill and its sockets exist (setImplantsAvailable).
    bool implantsAvailable() const;
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
    // Every pool the world draws equipment from: its own, then those of the worlds it names as dependencies in
    // world.yml (Xeen's MM6-MM8: the merged base). Its shops always keep to them, and so does the random loot of a
    // world with more than one (Xeen, whatever "MM9 loot in MM6-MM8" says); that setting is only for the worlds whose
    // own pool is the merged base, MM6-MM8 (ItemGenerator::generateRandomInventoryItem). Empty for an empty world id.
    std::vector<std::string> lootPoolsForWorld(const std::string &worldId) const;
    // The mounted worlds' world.yml dependencies that are worlds (not the engine package), by world id.
    void setWorldDependencies(std::unordered_map<std::string, std::vector<std::string>> dependenciesByWorld);
    // The mounted worlds' world.yml lootPool, by world id: the pool their own items join instead of one of their own.
    void setWorldLootPools(std::unordered_map<std::string, std::string> lootPoolsByWorld);
    // Worlds whose random artifacts come only from level-7 chest slots (world.yml chestArtifactsOnly).
    void setChestArtifactsOnlyWorlds(std::unordered_set<std::string> worldIds);
    bool chestArtifactsOnly(const std::string &worldId) const;
    // Worlds whose treasure markers roll gold by their item tier (world.yml groundGoldByItemTier).
    void setGroundGoldByItemTierWorlds(std::unordered_set<std::string> worldIds);
    bool groundGoldByItemTier(const std::string &worldId) const;
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
    // Gives each Special item the enchantment its VarA column names: a standard one (at VarB's power, else 1) when a
    // standard suffix matches, else a special one, as MM7 does for its special items. Returns the Special items whose
    // VarA names no enchantment.
    std::vector<uint32_t> resolveSpecialItemEnchants(
        const StandardItemEnchantTable &standardTable,
        const SpecialItemEnchantTable &specialTable);
    // The model an item draws lying on the ground: its icon's binding, or the missing-model placeholder.
    const ItemModelBinding &groundModel(uint32_t itemId) const;
    // Whether the item's icon has a ground model of its own (false: it draws the placeholder).
    bool hasGroundModel(uint32_t itemId) const;

private:
    std::vector<ItemDefinition> m_entries;
    std::vector<ItemSetBonusDefinition> m_setBonuses;
    std::unordered_map<uint16_t, WorkshopModDefinition> m_workshopMods;
    std::unordered_map<uint32_t, ImplantDefinition> m_implants;
    std::unordered_map<std::string, uint32_t> m_sourceAliases;
    std::unordered_map<std::string, WorldLootTable> m_worldLoot;
    // Lower-case package ids that own at least one item.
    std::unordered_set<std::string> m_itemPackageIds;
    // Lower-case world ids.
    std::unordered_set<std::string> m_chestArtifactsOnlyWorlds;
    std::unordered_set<std::string> m_groundGoldByItemTierWorlds;
    // Lower-case world id: the lower-case world ids it depends on.
    std::unordered_map<std::string, std::vector<std::string>> m_worldDependencies;
    std::unordered_map<std::string, std::string> m_worldLootPools;
    std::vector<ItemModelBinding> m_groundModels;
    // By item id: index into m_groundModels, or -1 for the placeholder.
    std::vector<int32_t> m_groundModelIndexByItemId;
};
}
