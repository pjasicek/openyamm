#include "game/rules/maw/MawCraftingData.h"

#include <yaml-cpp/yaml.h>

#include <exception>
#include <stdexcept>

namespace OpenYAMM::Game
{
namespace
{
MawCraftOperation operationNamed(const std::string &name)
{
    static const std::unordered_map<std::string, MawCraftOperation> Operations = {
        {"add_special", MawCraftOperation::AddSpecial},
        {"add_second_enchant", MawCraftOperation::AddSecondEnchant},
        {"refine_quality", MawCraftOperation::RefineQuality},
        {"duplicate_item", MawCraftOperation::DuplicateItem},
        {"upgrade_base_type", MawCraftOperation::UpgradeBaseType},
        {"remove_enchant", MawCraftOperation::RemoveEnchant},
        {"transfer_legendary_affix", MawCraftOperation::TransferLegendaryAffix},
        {"transfer_celestial", MawCraftOperation::TransferCelestial},
        {"add_potion_charges", MawCraftOperation::AddPotionCharges},
        {"add_item_power", MawCraftOperation::AddItemPower},
        {"add_first_enchant", MawCraftOperation::AddFirstEnchant},
    };
    const auto it = Operations.find(name);

    if (it == Operations.end())
    {
        throw std::runtime_error("unknown crafting operation '" + name + "'");
    }

    return it->second;
}

MawCraftMaterial parseMaterial(const YAML::Node &node)
{
    MawCraftMaterial material;
    material.operation = operationNamed(node["operation"].as<std::string>());
    material.shopPrice = node["shop_price"] ? node["shop_price"].as<int>() : 0;
    material.shopWeight = node["shop_weight"] ? node["shop_weight"].as<int>() : 0;
    material.dropChance = node["drop_chance"] ? node["drop_chance"].as<double>() : 0;
    material.targets = node["targets"] ? node["targets"].as<std::vector<uint32_t>>() : std::vector<uint32_t> {};
    material.specialChoices =
        node["choices"] ? node["choices"].as<std::vector<uint16_t>>() : std::vector<uint16_t> {};
    return material;
}
}

bool MawCraftingData::loadFromYaml(const std::string &text, std::string &errorMessage)
{
    try
    {
        const YAML::Node root = YAML::Load(text);
        const YAML::Node gems = root["gems"];
        m_firstGemItemId = gems["first_item"].as<uint32_t>();
        m_gemTiers = gems["tiers"].as<int>();
        m_gemDropMaxTier = gems["drop_max_tier"].as<int>();
        m_gemCombineCount = gems["combine"].as<int>();
        m_gemShopPrices = gems["shop_prices"].as<std::vector<int>>();

        if (int(m_gemShopPrices.size()) != m_gemTiers)
        {
            throw std::runtime_error("gems.shop_prices needs one price per tier");
        }

        for (const auto &entry : root["materials"])
        {
            m_materials[entry.first.as<uint32_t>()] = parseMaterial(entry.second);
        }

        for (const auto &entry : root["potions"])
        {
            m_potions[entry.first.as<uint32_t>()] = parseMaterial(entry.second);
        }

        const YAML::Node drops = root["drops"];
        m_gemDropChance = drops["gem_chance"].as<double>();
        m_bossDropExtra = drops["boss_extra"].as<double>();
        m_pityExponent = drops["pity_exponent"].as<double>();
        m_endlessPotionChance = drops["endless_potion_chance"].as<double>();
        m_reagentTiers = drops["reagent_tiers"].as<std::vector<std::vector<uint32_t>>>();

        const YAML::Node shops = root["shops"];
        m_shopReplaceChance = shops["replace_chance"].as<double>();
        m_shopSpecialGold = shops["special_gold"].as<double>();
        m_shopGemTierBonusWeights = shops["gem_tier_bonus_weights"].as<std::vector<double>>();

        const YAML::Node completion = root["map_completion"];
        m_mapCompletionItems = completion["items"].as<std::vector<uint32_t>>();
        m_mapCompletionGems = completion["gems"].as<int>();
    }
    catch (const std::exception &exception)
    {
        errorMessage = exception.what();
        return false;
    }

    return true;
}

int MawCraftingData::gemTier(uint32_t itemId) const
{
    return itemId >= m_firstGemItemId && itemId < m_firstGemItemId + uint32_t(m_gemTiers)
        ? int(itemId - m_firstGemItemId) + 1
        : 0;
}

uint32_t MawCraftingData::gemItemId(int tier) const
{
    return tier >= 1 && tier <= m_gemTiers ? m_firstGemItemId + uint32_t(tier - 1) : 0;
}

int MawCraftingData::gemTiers() const
{
    return m_gemTiers;
}

int MawCraftingData::gemDropMaxTier() const
{
    return m_gemDropMaxTier;
}

int MawCraftingData::gemCombineCount() const
{
    return m_gemCombineCount;
}

int MawCraftingData::gemShopPrice(int tier) const
{
    return tier >= 1 && tier <= m_gemTiers ? m_gemShopPrices[size_t(tier - 1)] : 0;
}

const MawCraftMaterial *MawCraftingData::material(uint32_t itemId) const
{
    const auto it = m_materials.find(itemId);
    return it != m_materials.end() ? &it->second : nullptr;
}

const MawCraftMaterial *MawCraftingData::potion(uint32_t itemId) const
{
    const auto it = m_potions.find(itemId);
    return it != m_potions.end() ? &it->second : nullptr;
}

const std::unordered_map<uint32_t, MawCraftMaterial> &MawCraftingData::materials() const
{
    return m_materials;
}

double MawCraftingData::gemDropChance() const
{
    return m_gemDropChance;
}

double MawCraftingData::bossDropExtra() const
{
    return m_bossDropExtra;
}

double MawCraftingData::pityExponent() const
{
    return m_pityExponent;
}

double MawCraftingData::endlessPotionChance() const
{
    return m_endlessPotionChance;
}

const std::vector<std::vector<uint32_t>> &MawCraftingData::reagentTiers() const
{
    return m_reagentTiers;
}

double MawCraftingData::shopReplaceChance() const
{
    return m_shopReplaceChance;
}

double MawCraftingData::shopSpecialGold() const
{
    return m_shopSpecialGold;
}

const std::vector<double> &MawCraftingData::shopGemTierBonusWeights() const
{
    return m_shopGemTierBonusWeights;
}

const std::vector<uint32_t> &MawCraftingData::mapCompletionItems() const
{
    return m_mapCompletionItems;
}

int MawCraftingData::mapCompletionGems() const
{
    return m_mapCompletionGems;
}
}
