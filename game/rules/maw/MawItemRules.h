#pragma once

#include "game/party/CharacterState.h"
#include "game/party/InventoryItem.h"
#include "game/rules/ItemRules.h"
#include "game/rules/LootFilter.h"
#include "game/rules/maw/MawItemFormulas.h"

#include <cstdint>
#include <initializer_list>
#include <string>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
class MawRules;
struct MapStatsEntry;
struct MawArtifact;
struct MawBaseItem;

// Whether the character wears a working item with this legendary affix (MAW id 11-35); affixes do not stack.
bool mawWearsLegendaryAffix(const Character &character, int affixId);
// How many working worn items carry one of these special enchantments, or are one of these items.
int mawWornSpecialCount(const Character &character, std::initializer_list<uint16_t> specialIds);
int mawWornItemCount(const Character &character, std::initializer_list<uint32_t> itemIds);
// The artifacts that regenerate hit points or spell points, 0.2 % of the pool a second (artifactHpRegen,
// artifactSpRegen, zzMaw-Items.lua:3844-3845), and how many of them the character wears.
bool mawRegenerationArtifact(uint32_t itemId, bool spellPoints);
int mawWornRegenerationArtifacts(const Character &character, bool spellPoints);
// The product of the attack delay multipliers of the artifacts the character wears (x0.9 each, GetAttackDelay).
double mawArtifactAttackDelayMultiplier(const MawRules &rules, const Character &character);
// MAW's halberds (halberdItems, IT:1410): two-handed spears that count as two-handed axes too.
bool mawIsHalberd(uint32_t itemId);
// The skill the character wields the weapon with: a halberd takes Axe when Axe is the higher skill (level, then
// mastery), else Spear; every other weapon its own skill (GetWeaponSkillFor, IT:4446-4456, MAW 8967ae88).
std::string mawWeaponSkill(const Character &character, const ItemDefinition &itemDefinition);

// An artifact's stats (standard enchantment types, read as worn) and skills from its budget at the party's level.
struct MawArtifactBonuses
{
    // The budget's stats (standard enchant type, amount) and its fixed amounts (power.Flat, e.g. a fire immunity).
    std::vector<std::pair<int, int>> stats;
    std::vector<std::pair<int, int>> flat;
    std::vector<std::pair<std::string, int>> skills;
};

// MAW's items (devdocs/maw/ITEMS.md §1, data/loot.yml): every enchantable drop rolls a rarity with bad-luck
// protection, an item power from its drop level, up to two base enchantments and a special, and Legendary and
// Celestial items a legendary affix; 0.5 % of drops become an artifact. Weapon damage and armour follow the item
// power, enchantments are read through MAW's transforms, and items need a character level.
class MawItemRules : public ItemRules
{
public:
    explicit MawItemRules(MawRules &rules);

    bool rollsRareItem(const ItemGenerationRequest &request, Party *pParty, std::mt19937 &rng) const override;
    bool levelSevenGivesRareItem() const override;
    // Quest items sell once their quest is done; unique ones once a game (MawCore/SpecialItems.lua).
    std::optional<std::string> sellRefusal(const Party &party, const InventoryItem &item) const override;
    void itemSold(Party &party, const InventoryItem &item) const override;
    void rollEnchantments(
        InventoryItem &item,
        const ItemDefinition &itemDefinition,
        const ItemRollTables &tables,
        const ItemGenerationRequest &request,
        Party *pParty,
        std::mt19937 &rng) const override;
    // A drop of this rarity at the level, rolled as rollEnchantments rolls a top-grade boss drop once its rarity is
    // drawn, for the debug console's test parties; a legendary affix of 0 is the least found one. The loot's
    // counters stay as they are. Nothing for an item MAW does not roll.
    void rollEnchantmentsAtRarity(
        InventoryItem &item,
        const ItemDefinition &itemDefinition,
        const ItemRollTables &tables,
        int dropLevel,
        MawRarity rarity,
        int legendaryAffix,
        std::mt19937 &rng) const;
    // A reagent's item level is a third of the lower of its drop level and the party's total level, an eighth in
    // Austerity (IT:1110-1123); the level raises its power in the mix. A spellbook found outside a shop is sealed: it
    // becomes its school's Magic Book (971-979) and keeps the book's id in craftState (SP:3708-3726).
    void rollPlainItem(
        InventoryItem &item,
        const ItemDefinition &itemDefinition,
        const ItemGenerationRequest &request) const override;

    std::optional<ItemBaseStats> baseStats(
        const ItemDefinition &itemDefinition,
        const ItemRulesetFields &fields,
        int wearerLevel) const override;
    void applyEquippedEnchantEffects(
        const ItemDefinition &itemDefinition,
        const EquippedItemRuntimeState &runtimeState,
        const StandardItemEnchantTable *pStandardTable,
        const SpecialItemEnchantTable *pSpecialTable,
        const Character &wearer,
        Character &bonuses) const override;
    // Seraphim hold two-handed swords in one hand and never a sword in the off hand; Dwarves and Minotaurs take
    // one-handed axes in the off hand at Expert Axe, Minotaurs two-handed axes and halberds in one hand, and in the
    // off hand at Master Axe (CL:170-226, S:1787-1800, S:2655-2685).
    ItemWield wield(const Character &character, const ItemDefinition &itemDefinition) const override;
    // A halberd is wielded with Spear or Axe, whichever is higher, so Axe alone lets a character equip one.
    std::string weaponSkill(const Character &character, const ItemDefinition &itemDefinition) const override;
    int levelRequirement(const ItemDefinition &itemDefinition, const ItemRulesetFields &fields) const override;

    int itemValue(
        const InventoryItem &item,
        const ItemDefinition &itemDefinition,
        const StandardItemEnchantTable *pStandardTable,
        const SpecialItemEnchantTable *pSpecialTable,
        int minimumValue) const override;
    int shopBuyValue(
        const InventoryItem &item,
        const ItemDefinition &itemDefinition,
        const StandardItemEnchantTable *pStandardTable,
        const SpecialItemEnchantTable *pSpecialTable) const override;

    std::string displayName(
        const InventoryItem &item,
        const ItemDefinition &itemDefinition,
        const StandardItemEnchantTable *pStandardTable,
        const SpecialItemEnchantTable *pSpecialTable) const override;
    // A MAW item's base enchantments are inspect lines of their own; "Special:" is its special only.
    std::string enchantDescription(
        const InventoryItem &item,
        const ItemDefinition &itemDefinition,
        const StandardItemEnchantTable *pStandardTable,
        const SpecialItemEnchantTable *pSpecialTable,
        const Character *pViewer) const override;
    // MAW's potion texts (zzAlchemy.lua:429-541, Tooltip.lua:83-130): heal amounts and the aura percents at the
    // potion's power, the Meditation bonus, Transcendence's step.
    std::optional<std::string> itemDescription(const InventoryItem &item, const Character *pViewer) const override;
    std::optional<uint32_t> nameColor(const InventoryItem &item) const override;
    bool glowsItemRarity() const override;
    bool inventorySearch() const override;
    std::vector<ItemInspectLine> inspectLines(
        const InventoryItem &item,
        const ItemDefinition &itemDefinition,
        const StandardItemEnchantTable *pStandardTable,
        const SpecialItemEnchantTable *pSpecialTable,
        const Character *pViewer) const override;
    // One base enchantment as the inspect popup reads it ("Might +12" with the slot's read multipliers, a resistance as
    // the share of damage it stops with the viewer's Legendary 16 in it); `first` is the item's first slot.
    std::string enchantLine(
        int type,
        int power,
        bool first,
        const ItemDefinition &itemDefinition,
        const StandardItemEnchantTable *pStandardTable,
        const Character *pViewer) const;

    // Weapon, armour and magic shops reroll for (floor(P / 15) + S)^2 x 250 gold, P being the levels banked on the
    // three continents less half the shop's own (at most 54), S = min(floor(own / 18) + 2, 5) (refreshItems).
    // Skill x mastery plus Glamour's mastery x power; Grandmaster Merchant or Glamour, or a total of 45, trades at
    // cost; 7 more, no reputation term
    // (GetMerchantTotalSkill, zzMAW-Skills.lua).
    std::optional<int> merchantValue(const Character &member) const override;
    std::optional<int> shopRerollCost(const Party &party, const HouseEntry &house) const override;
    // Magic shops and alchemists (CRAFTING.md §6.2, all alchemists by decision): every gem and three in ten other
    // non-equipment items become a crafting material: a special with chance min((gold / 20,000,000)^0.7, 1), else a
    // gem of tier 1 + min(floor(banked levels / 25) + 0, 1 or 2, 15).
    void adjustShopStock(
        std::vector<InventoryItem> &stock,
        const HouseEntry &house,
        const Party &party,
        const ItemTable &itemTable,
        std::mt19937 &rng) const override;
    // MM9's shops sell their own items at MAW's power and rarity.
    bool rollsFixedShopStock() const override;
    // A dimension map (zzMaw-Maps.lua UseMouseItem): its map refills on the next visit with three random families,
    // denser by its affixes and at its power's level, and the party goes to its entrance.
    std::optional<std::string> useTravelItem(Party &party, const InventoryItem &item) const override;
    // MAW's loot filter, as the player set it; the drop's facts: its group or kind by Equip Stat, its MAW rarity (a
    // placed item MAW never rolled ranks as Common plus one per enchantment, IT:933-944) and its drop level.
    const RulesetLootFilter *lootFilter() const override;
    std::optional<LootFilterFacts> lootFilterFacts(
        const InventoryItem &item,
        const ItemDefinition &itemDefinition) const override;
    RecentLootDrops *recentLootDrops() const override;
    int filteredLootGold(
        const InventoryItem &item,
        const ItemDefinition &itemDefinition,
        const StandardItemEnchantTable *pStandardTable,
        const SpecialItemEnchantTable *pSpecialTable) const override;
    std::optional<uint32_t> chestGoldAmount(int pileSize, std::mt19937 &rng) const override;
    uint32_t placedItemId(uint32_t itemId, std::mt19937 &rng) const override;
    // NPCMercenaries.lua:349-356.
    void trimMercenaryItem(InventoryItem &item, std::mt19937 &rng) const override;
    // Four bags a member, a party of one too (zzMaw-MultiBag.lua has five and 25; DEVIATIONS 141).
    int bagCount(const Party &party) const override;
    // A sealed spellbook opens for a reader with the mastery its book's identify difficulty asks: 15 Grandmaster, 10
    // Master, 5 Expert, else Novice (SP:3685-3705).
    bool openSealedItem(InventoryItem &item, const Character &reader) const override;
    // Beyond Madness: a dimension map cannot be dropped on the ground (zzMaw-Maps.lua:1166-1197).
    bool canDropToWorld(const InventoryItem &item, const ItemDefinition &definition) const override;
    // K pulls 30 corpses and 30 crafting items (1041-1070) or dimension maps (290) to the party
    // (zzMaw-Monsters.lua:4563-4596).
    std::optional<LootGathering> lootGathering() const override;
    bool gathersItem(const InventoryItem &item) const override;
    // Crafting items (1041-1070, zzzMaw_CraftingBag.lua:1-6) go to a crafting bag; potions, bottles and reagents to
    // an alchemy bag (ours).
    std::optional<BagTag> bagTag(const ItemDefinition &definition) const override;
    // The alchemist key (MAW's E) picks the member who takes alchemy items when sorting (zzMaw-Item-Sorter.lua:47-56);
    // the potions 220-299 go first, highest id first, then MAW's reagent and crafting order (alchemyItemsOrder,
    // :751-758).
    std::optional<size_t> alchemist(const Party &party) const override;
    std::optional<std::string> pickAlchemist(Party &party, size_t memberIndex) const override;
    std::optional<int> alchemySortRank(const InventoryItem &item) const override;
    // Doom and the modes after it (IT:4129-4201): chests open only for a member whose Disarm Traps skill x mastery
    // reaches the map's lock (twice a lock of 4 or more), or a Grandmaster, trapped or not (PHASE9_SCOPE Q1);
    // unidentified items cannot be worn; identifying costs the identify difficulty squared and repairs take the
    // multiplier 5 (the item's value).
    std::optional<std::string> chestOpenRefusal(const Party &party, int mapLock) const override;
    std::optional<std::string> wearRefusal(const InventoryItem &item) const override;
    float shopServiceMultiplier(const ItemDefinition &itemDefinition, bool identify, float houseMultiplier) const override;
    // "Power: +x %" and "Vitality: -y %" when the member wears the item in place of what they wear in its slot; nothing
    // for an empty slot or no change (Tooltip.lua:589-665). Power is the best of melee, ranged and spell power.
    std::vector<ItemInspectLine> comparisonLines(
        const Party &party,
        size_t memberIndex,
        const InventoryItem &item,
        const ItemDefinition &itemDefinition) const override;

    // A weapon's damage rows under MAW (bonus, die sides and count before skills), or nothing for anything that is
    // not one of MAW's weapons.
    std::optional<MawWeaponDamage> weaponDamage(
        const ItemDefinition &itemDefinition,
        const ItemRulesetFields &fields,
        int wearerLevel) const;
    // The flat damage Staff, Sword and Spear guard by (addWeaponACRes, IT:3226-3247): the base's ladder flat plus
    // the top rung's x item power / 30, no quality and no cap; an artifact's upscaled printed flat. Nothing for
    // anything that is not one of MAW's weapons.
    std::optional<int> weaponGuardBase(
        const ItemDefinition &itemDefinition,
        const ItemRulesetFields &fields,
        int wearerLevel) const;
    // The armour class of an armour piece under MAW, or nothing for anything that is not MAW's armour.
    std::optional<int> armorClass(
        const ItemDefinition &itemDefinition,
        const ItemRulesetFields &fields,
        int wearerLevel) const;

    // The level a Celestial item scales to on a wearer of `wearerLevel`.
    double celestialLevel(int wearerLevel) const;
    // A Celestial item as it is at its wearer's level: the item power and the enchantment strengths of a Primordial
    // one there (updateCelestialItem, IT:1622-1661). Other items come back as they are.
    InventoryItem celestialAtLevel(const InventoryItem &item, const ItemDefinition &itemDefinition, int wearerLevel) const;
    // What an artifact gives at the party's level (MawCore/Artifacts.lua BonusesOf, budget unit at the total level).
    MawArtifactBonuses artifactBonuses(const MawArtifact &artifact, const ItemDefinition &itemDefinition) const;

private:
    // applyEquippedEnchantEffects before a dragon's triple share.
    void applyItemEffects(
        const ItemDefinition &itemDefinition,
        const EquippedItemRuntimeState &runtimeState,
        const StandardItemEnchantTable *pStandardTable,
        const SpecialItemEnchantTable *pSpecialTable,
        const Character &wearer,
        Character &bonuses) const;
    // The map a dimension map opens, or null for any other item.
    const MapStatsEntry *dimensionMapTarget(const InventoryItem &item) const;
    // The MAW value of a base item before the selling (0.4) and buy-screen multipliers.
    double fullValue(
        const InventoryItem &item,
        const ItemDefinition &itemDefinition,
        const MawBaseItem &base,
        const SpecialItemEnchantTable *pSpecialTable) const;
    // What a drop of its rarity gets: item power, base enchantments, the legendary affix (0: the least found,
    // counted when countFind) and the special.
    void rollRarityEnchantments(
        InventoryItem &item,
        const ItemDefinition &itemDefinition,
        const ItemRollTables &tables,
        const MawBaseItem &base,
        int lootTier,
        int grade,
        bool boss,
        double dropLevel,
        MawRarity rarity,
        int legendaryAffix,
        bool countFind,
        std::mt19937 &rng) const;

    // The last comparison, kept while the popup shows the same item to the same member wearing the same things.
    struct Comparison
    {
        InventoryItem item;
        size_t memberIndex = 0;
        CharacterEquipment equipment;
        CharacterEquipmentRuntimeState equipmentRuntime;
        std::vector<ItemInspectLine> lines;
    };

    MawRules &m_rules;
    mutable std::optional<Comparison> m_lastComparison;
    // This session's drops the loot filter saw (not saved).
    mutable RecentLootDrops m_recentLootDrops;
};

// slotMult (zzMaw-Items.lua:1405): what both base enchantments of this kind of item are multiplied by when rolled
// (two-handed weapons 2, bows, helms, gauntlets and boots 1.25, body armour 1.5, rings 0.75, the rest 1).
double mawEnchantSlotMultiplier(const ItemDefinition &itemDefinition, const MawBaseItem &base);
// The stat or skill a base enchantment (standard enchant id 1-24) raises, as the player reads it (translated).
std::string mawEnchantStatName(const StandardItemEnchantTable *pTable, int type);
// An artifact's item text without MMMerge's "(Special ...)" part and a leading "(...)" summary.
std::string mawArtifactDescription(const std::string &notes);

// The read-time strength of a base enchantment (Formulas.vitalityEnchantPower, the resistance +10 and ring halving):
// `type` is the standard enchant id 1-24, `first` whether it sits in the first slot.
int mawEnchantReadPower(int type, int power, bool first, double slotMultiplier, bool ring);
}
