#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <random>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class Party;
class ItemTable;
class StandardItemEnchantTable;
class SpecialItemEnchantTable;
struct Character;
struct HouseEntry;
struct EquippedItemRuntimeState;
struct InventoryItem;
struct ItemDefinition;
struct ItemGenerationRequest;
struct ItemRulesetFields;
enum class BagTag : uint8_t;
class RecentLootDrops;
struct LootFilterFacts;
struct RulesetLootFilter;

// The tables an item roll reads.
struct ItemRollTables
{
    const ItemTable &items;
    const StandardItemEnchantTable &standardEnchants;
    const SpecialItemEnchantTable &specialEnchants;
};

// How a character holds a weapon: in both hands, and whether it may go in the off hand.
struct ItemWield
{
    bool twoHanded = false;
    bool offHand = false;
};

// An equipped item's base numbers where a ruleset replaces the table's dice and armour (MAW: by item power).
struct ItemBaseStats
{
    int attackBonus = 0;
    int minimumDamage = 0;
    int maximumDamage = 0;
    int armorClass = 0;
};

// One extra line of an item's inspect popup, in its colour (0xRRGGBB).
struct ItemInspectLine
{
    std::string text;
    uint32_t color = 0xffffff;
};

// What the gather key brings to the party: at most this many corpses and ground items.
struct LootGathering
{
    size_t corpses = 0;
    size_t items = 0;
};

// How random items are rolled, what they give and what they are worth (devdocs/maw/HANDOFF.md §3.5). This class is the
// Standard MMMerge rules; a ruleset that handles items differently derives from it.
class ItemRules
{
public:
    virtual ~ItemRules() = default;

    // Whether a random drop is a rare item (artifact or relic) instead of a base item: Standard 5 % at treasure
    // level 6 outside shops.
    virtual bool rollsRareItem(const ItemGenerationRequest &request, Party *pParty, std::mt19937 &rng) const;
    // Whether a treasure-level-7 chest or ground slot gives a rare item: Standard yes; MAW reads level 7 as 6, so its
    // artifacts come only from its own roll (IT:26-28).
    virtual bool levelSevenGivesRareItem() const;
    // Rolls the enchantments of a freshly generated enchantable base item: Standard one standard or one special
    // enchantment, by treasure level. A ruleset may also turn the item into another one here (MAW: artifacts).
    virtual void rollEnchantments(
        InventoryItem &item,
        const ItemDefinition &itemDefinition,
        const ItemRollTables &tables,
        const ItemGenerationRequest &request,
        Party *pParty,
        std::mt19937 &rng) const;
    // Finishes a freshly generated item that takes no enchantments: Standard leaves it as the table has it; MAW
    // gives reagents an item level from where they dropped.
    virtual void rollPlainItem(
        InventoryItem &item,
        const ItemDefinition &itemDefinition,
        const ItemGenerationRequest &request) const;

    // An equipped item's damage and armour, or nothing for the table's dice and armour class (Standard). Items that
    // grow with their wearer read `wearerLevel`.
    virtual std::optional<ItemBaseStats> baseStats(
        const ItemDefinition &itemDefinition,
        const ItemRulesetFields &fields,
        int wearerLevel) const;
    // Adds what an equipped item gives its wearer (stats, skills, resistances) to `bonuses`.
    virtual void applyEquippedEnchantEffects(
        const ItemDefinition &itemDefinition,
        const EquippedItemRuntimeState &runtimeState,
        const StandardItemEnchantTable *pStandardTable,
        const SpecialItemEnchantTable *pSpecialTable,
        const Character &wearer,
        Character &bonuses) const;
    // How the character holds the weapon. Standard: two-handed weapons take both hands; one-handed daggers at Expert
    // and swords at Master may go in the off hand.
    virtual ItemWield wield(const Character &character, const ItemDefinition &itemDefinition) const;
    // Why a shop will not buy this item, or nothing; Standard refuses only items without a price (the house's own
    // checks come first).
    virtual std::optional<std::string> sellRefusal(const Party &party, const InventoryItem &item) const;
    // A shop bought the item (MAW remembers its unique items).
    virtual void itemSold(Party &party, const InventoryItem &item) const;
    // The character level needed to wear the item; 0 for none (Standard).
    virtual int levelRequirement(const ItemDefinition &itemDefinition, const ItemRulesetFields &fields) const;

    // What the item is worth wherever its value counts (selling, chests, the inspect popup); at least
    // `minimumValue`.
    virtual int itemValue(
        const InventoryItem &item,
        const ItemDefinition &itemDefinition,
        const StandardItemEnchantTable *pStandardTable,
        const SpecialItemEnchantTable *pSpecialTable,
        int minimumValue) const;
    // The value a shop's buy screen starts its price from. Standard: the item value.
    virtual int shopBuyValue(
        const InventoryItem &item,
        const ItemDefinition &itemDefinition,
        const StandardItemEnchantTable *pStandardTable,
        const SpecialItemEnchantTable *pSpecialTable) const;

    // The name the item shows (Standard: the enchantment's suffix or prefix).
    virtual std::string displayName(
        const InventoryItem &item,
        const ItemDefinition &itemDefinition,
        const StandardItemEnchantTable *pStandardTable,
        const SpecialItemEnchantTable *pSpecialTable) const;
    // The "Special:" text of the inspect popup (Standard: the standard enchantment, else the special's description);
    // the viewer may be null.
    virtual std::string enchantDescription(
        const InventoryItem &item,
        const ItemDefinition &itemDefinition,
        const StandardItemEnchantTable *pStandardTable,
        const SpecialItemEnchantTable *pSpecialTable,
        const Character *pViewer) const;
    // The item's description in its inspect popup when the rules write their own (MAW: potions with their numbers at
    // the potion's power); nothing for the item table's notes.
    virtual std::optional<std::string> itemDescription(const InventoryItem &item, const Character *pViewer) const;
    // The colour of the item's name in its inspect popup (0xRRGGBB); nothing for the popup's own colour.
    virtual std::optional<uint32_t> nameColor(const InventoryItem &item) const;
    // Whether items are outlined in their rarity colour (the Item rarity glow setting); Standard has no rarities.
    virtual bool glowsItemRarity() const;
    // Whether the inventory has the item search field (MAW, for its many bags; user 2026-11-04).
    virtual bool inventorySearch() const;
    // Lines the rules add to the inspect popup below the item's type and stats (MAW: enchantments, level required).
    virtual std::vector<ItemInspectLine> inspectLines(
        const InventoryItem &item,
        const ItemDefinition &itemDefinition,
        const StandardItemEnchantTable *pStandardTable,
        const SpecialItemEnchantTable *pSpecialTable,
        const Character *pViewer) const;

    // A member's merchant value (the percent off house prices, up to 100) when the rules compute it themselves (MAW:
    // skill x mastery plus Glamour, no reputation); nothing for Standard's skill, bonus and reputation.
    virtual std::optional<int> merchantValue(const Character &member) const;
    // What rerolling a shop's stock costs, or nothing when its stock cannot be rerolled (Standard).
    virtual std::optional<int> shopRerollCost(const Party &party, const HouseEntry &house) const;
    // Changes a shop's freshly rolled stock (MAW: magic shops and alchemists sell crafting materials). Standard:
    // nothing.
    virtual void adjustShopStock(
        std::vector<InventoryItem> &stock,
        const HouseEntry &house,
        const Party &party,
        const ItemTable &itemTable,
        std::mt19937 &rng) const;

    // Where using the item takes the party (MAW: a dimension map, to the map it opens), once the rules set the visit
    // up; the item is used up. Nothing for an item that does not travel (Standard: every item).
    virtual std::optional<std::string> useTravelItem(Party &party, const InventoryItem &item) const;
    // The loot filter in force (MAW's, a player preference; it also reads items placed in chests). Standard: none.
    virtual const RulesetLootFilter *lootFilter() const;
    // What the loot filter needs to know of a drop (LootFilter.h); none for an item it never takes.
    virtual std::optional<LootFilterFacts> lootFilterFacts(
        const InventoryItem &item,
        const ItemDefinition &itemDefinition) const;
    // The drops the filter saw this session, for its window's trial of another preset; none without a filter.
    virtual RecentLootDrops *recentLootDrops() const;
    // The gold a filtered item turns into.
    virtual int filteredLootGold(
        const InventoryItem &item,
        const ItemDefinition &itemDefinition,
        const StandardItemEnchantTable *pStandardTable,
        const SpecialItemEnchantTable *pSpecialTable) const;
    // The gold of a pile in a chest of the current map, by its size (0 small, 1 medium, 2 large), when the rules set
    // it (MAW: from the map's level). Standard: nothing, the pile keeps its amount.
    virtual std::optional<uint32_t> chestGoldAmount(int pileSize, std::mt19937 &rng) const;
    // The item placed where a map's data (its ground and its chests) has `itemId`, each time the map loads (MAW: a
    // removed potion, 264-289, becomes one of 252-263). Standard: the same item.
    virtual uint32_t placedItemId(uint32_t itemId, std::mt19937 &rng) const;
    // Lines comparing the member with the item worn instead of what they wear in its slot (MAW: Power and Vitality).
    // Standard: none.
    virtual std::vector<ItemInspectLine> comparisonLines(
        const Party &party,
        size_t memberIndex,
        const InventoryItem &item,
        const ItemDefinition &itemDefinition) const;
    // A hired mercenary's generated gear (MAW: an item with a special and a second base enchantment loses one of them,
    // even odds). Standard: unchanged, without a draw.
    virtual void trimMercenaryItem(InventoryItem &item, std::mt19937 &rng) const;
    // How many bags each member carries (MAW's multibag: 4); the inventory is the open one.
    // Standard: 1.
    virtual int bagCount(const Party &party) const;
    // Opens an item for the member who inspects it, true when it changed (MAW: a sealed spellbook becomes its book once
    // the reader's mastery in its school is high enough). Standard: nothing is sealed.
    virtual bool openSealedItem(InventoryItem &item, const Character &reader) const;
    // Whether the party may drop the held item on the ground (MAW: Beyond Madness keeps dimension maps in the packs).
    // Standard: every item but the ones the item table forbids.
    virtual bool canDropToWorld(const InventoryItem &item, const ItemDefinition &definition) const;
    // What the gather key brings to the party (MAW: 30 corpses and 30 ground items). Standard: nothing, the key does
    // nothing.
    virtual std::optional<LootGathering> lootGathering() const;
    // Whether the gather key brings this ground item (MAW: crafting items and dimension maps).
    virtual bool gathersItem(const InventoryItem &item) const;
    // The tagged bag a ground item goes to when the party picks it up (MAW: crafting items to a crafting bag, potions
    // and reagents to an alchemy bag). Standard: none, bags are not tagged.
    virtual std::optional<BagTag> bagTag(const ItemDefinition &definition) const;
    // The member who takes the alchemy items when the party sorts, if the rules have one and someone was picked.
    // Standard: nobody.
    virtual std::optional<size_t> alchemist(const Party &party) const;
    // The alchemist key on a member's inventory: picks the member, or drops the pick when it is theirs already; the
    // status line. Standard: nothing, the key does nothing.
    virtual std::optional<std::string> pickAlchemist(Party &party, size_t memberIndex) const;
    // Where an alchemy item goes in its alchemist's bags, lowest first; nothing for any other item (Standard: all).
    virtual std::optional<int> alchemySortRank(const InventoryItem &item) const;
    // Why the party cannot open a chest on a map of this lock rating (MapStatsEntry::disarmDifficulty), or nothing
    // (Standard: chests always open, their traps aside).
    virtual std::optional<std::string> chestOpenRefusal(const Party &party, int mapLock) const;
    // Why a member cannot wear the item, before the class, race and level checks (MAW's Doom: unidentified items);
    // nothing when they can.
    virtual std::optional<std::string> wearRefusal(const InventoryItem &item) const;
    // The shop's price multiplier for identifying or repairing the item (PriceCalculator, its house's multiplier
    // otherwise). Standard: the house's.
    virtual float shopServiceMultiplier(const ItemDefinition &itemDefinition, bool identify, float houseMultiplier) const;
};

const ItemRules &standardItemRules();
}
