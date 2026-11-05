#pragma once

#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
// What a MAW crafting material or item-target potion does to an item (devdocs/maw/CRAFTING.md §3-4).
enum class MawCraftOperation : uint8_t
{
    None,
    // Gems: +3 (+1 on a skill enchantment) to the base enchantment furthest below its cap.
    RaiseEnchant,
    // Eye of Void and the element potions: a special enchantment.
    AddSpecial,
    // Creator's Hourglass: a second base enchantment near the first one's strength.
    AddSecondEnchant,
    // Pandora's Cube: base damage or armour quality.
    RefineQuality,
    // Archibald's Mirror: becomes a copy of the item.
    DuplicateItem,
    // Emerald of Power: the next base item of the family.
    UpgradeBaseType,
    // Pearl of Memory: removes the enchantment the player picks.
    RemoveEnchant,
    // Orb of Creation: moves a legendary affix into the orb and out again.
    TransferLegendaryAffix,
    // Celestial Orb: moves Celestial status the same way.
    TransferCelestial,
    // Endless Potion: more drinks in a potion.
    AddPotionCharges,
    // Crafting Cube: item power up to a cap by the owner's level.
    AddItemPower,
    // Enchant Item potion: a first base enchantment from the potion's power.
    AddFirstEnchant,
};

struct MawCraftMaterial
{
    MawCraftOperation operation = MawCraftOperation::None;
    // 0: never sold.
    int shopPrice = 0;
    int shopWeight = 0;
    double dropChance = 0;
    // AddPotionCharges: the potions it refills. AddSpecial on a potion: the special enchantments it picks from (empty:
    // MAW's strongest special pool, as the Eye).
    std::vector<uint32_t> targets;
    std::vector<uint16_t> specialChoices;
};

// rulesets/maw/data/crafting.yml.
class MawCraftingData
{
public:
    bool loadFromYaml(const std::string &text, std::string &errorMessage);

    // The gem tier (1-20) of an item, or 0.
    int gemTier(uint32_t itemId) const;
    uint32_t gemItemId(int tier) const;
    int gemTiers() const;
    int gemDropMaxTier() const;
    int gemCombineCount() const;
    int gemShopPrice(int tier) const;
    // A crafting material other than a gem, or an item-target potion; null for anything else.
    const MawCraftMaterial *material(uint32_t itemId) const;
    const MawCraftMaterial *potion(uint32_t itemId) const;
    const std::unordered_map<uint32_t, MawCraftMaterial> &materials() const;

    double gemDropChance() const;
    double bossDropExtra() const;
    double pityExponent() const;
    double endlessPotionChance() const;
    // The reagents of each drop tier (1-5).
    const std::vector<std::vector<uint32_t>> &reagentTiers() const;
    double shopReplaceChance() const;
    double shopSpecialGold() const;
    const std::vector<double> &shopGemTierBonusWeights() const;
    const std::vector<uint32_t> &mapCompletionItems() const;
    int mapCompletionGems() const;

private:
    uint32_t m_firstGemItemId = 0;
    int m_gemTiers = 0;
    int m_gemDropMaxTier = 0;
    int m_gemCombineCount = 3;
    std::vector<int> m_gemShopPrices;
    std::unordered_map<uint32_t, MawCraftMaterial> m_materials;
    std::unordered_map<uint32_t, MawCraftMaterial> m_potions;
    double m_gemDropChance = 0;
    double m_bossDropExtra = 1;
    double m_pityExponent = 1.38;
    double m_endlessPotionChance = 0;
    std::vector<std::vector<uint32_t>> m_reagentTiers;
    double m_shopReplaceChance = 0;
    double m_shopSpecialGold = 1;
    std::vector<double> m_shopGemTierBonusWeights;
    std::vector<uint32_t> m_mapCompletionItems;
    int m_mapCompletionGems = 0;
};
}
