#include "game/rules/maw/MawItemData.h"

#include <yaml-cpp/yaml.h>

#include <exception>

namespace OpenYAMM::Game
{
namespace
{
std::vector<std::pair<std::string, double>> readBudget(const YAML::Node &node)
{
    std::vector<std::pair<std::string, double>> budget;

    for (const auto &entry : node)
    {
        budget.emplace_back(entry.first.as<std::string>(), entry.second.as<double>());
    }

    return budget;
}
}

bool MawItemData::loadBases(const YAML::Node &bases, bool worldBases, std::string &errorMessage)
{
    for (const auto &entry : bases)
    {
        const YAML::Node &row = entry.second;
        const uint32_t itemId = entry.first.as<uint32_t>();

        if (!row.IsSequence() || row.size() < 5 || row.size() > (worldBases ? 6u : 5u))
        {
            errorMessage = "base item " + std::to_string(itemId) + " must be [rung, dice, two-handed, AC, reference AC"
                + (worldBases ? ", strength]" : "]");
            return false;
        }

        if (worldBases && m_baseItems.contains(itemId))
        {
            errorMessage = "base item " + std::to_string(itemId) + " is given twice";
            return false;
        }

        MawBaseItem item;
        item.rung = row[0].as<double>();
        item.diceCount = row[1].as<int>();
        item.twoHanded = row[2].as<int>() != 0;
        item.baseArmorClass = row[3].as<int>();
        item.referenceArmorClass = row[4].as<int>();
        item.strength = row.size() > 5 ? row[5].as<double>() : 1.0;

        if (item.strength < 1 || item.strength > 1.25)
        {
            errorMessage = "base item " + std::to_string(itemId) + " has a strength outside 1-1.25";
            return false;
        }

        m_baseItems[itemId] = item;
    }

    return true;
}

bool MawItemData::loadWorldBases(const std::string &text, std::string &errorMessage)
{
    try
    {
        return loadBases(YAML::Load(text)["bases"], true, errorMessage);
    }
    catch (const std::exception &exception)
    {
        errorMessage = std::string("item_bases.yml: ") + exception.what();
        return false;
    }
}

bool MawItemData::loadFromYaml(const std::string &text, std::string &errorMessage)
{
    try
    {
        const YAML::Node root = YAML::Load(text);

        for (const auto &entry : root["legendary_affixes"])
        {
            m_legendaryAffixTexts[entry.first.as<int>()] = entry.second.as<std::string>();
        }

        if (!loadBases(root["bases"], false, errorMessage))
        {
            return false;
        }

        for (const auto &entry : root["artifacts"])
        {
            const YAML::Node &node = entry.second;
            MawArtifact artifact;
            artifact.itemId = entry.first.as<uint32_t>();
            artifact.dropWeight = node["drop"].as<int>(1);
            const std::string base = node["base"].as<std::string>();

            if (base == "weapon")
            {
                artifact.base = MawArtifact::Base::Weapon;
            }
            else if (base == "armor")
            {
                artifact.base = MawArtifact::Base::Armor;
            }
            else if (base == "flat")
            {
                artifact.base = MawArtifact::Base::Flat;
            }
            else
            {
                errorMessage = "artifact " + std::to_string(artifact.itemId) + " has unknown base " + base;
                return false;
            }

            artifact.slotMultiplier = node["slot_mult"].as<double>(1);
            artifact.twoHanded = node["two_handed"].as<bool>(false);
            artifact.diceCount = node["dice"].as<int>(1);
            artifact.guardBase = node["guard"].as<int>(0);
            artifact.rung = node["rung"].as<double>(6);
            artifact.printedArmorClass = node["printed_ac"].as<int>(0);
            artifact.referenceArmorClass = node["reference_ac"].as<int>(0);
            artifact.stats = readBudget(node["stats"]);
            artifact.skills = readBudget(node["skills"]);
            artifact.flat = readBudget(node["flat"]);

            if (const YAML::Node onHit = node["on_hit"])
            {
                artifact.onHitType = onHit["kind"].as<std::string>();
                artifact.onHitDamage = onHit["damage"].as<double>(0);
                artifact.onHitVersus = readBudget(onHit["versus"]);
                artifact.onHitSlow = onHit["slow"].as<bool>(false);
            }

            artifact.spellBonus = node["spell_bonus"].as<std::vector<std::string>>(std::vector<std::string>{});
            artifact.attackDelayMultiplier = node["attack_delay"].as<double>(1);
            m_artifactIndex[artifact.itemId] = m_artifacts.size();
            m_artifacts.push_back(std::move(artifact));
        }
    }
    catch (const std::exception &exception)
    {
        errorMessage = exception.what();
        return false;
    }

    return true;
}

const std::vector<MawArtifact> &MawItemData::artifacts() const
{
    return m_artifacts;
}

const MawArtifact *MawItemData::artifact(uint32_t itemId) const
{
    const auto it = m_artifactIndex.find(itemId);
    return it != m_artifactIndex.end() ? &m_artifacts[it->second] : nullptr;
}

const MawBaseItem *MawItemData::baseItem(uint32_t itemId) const
{
    const auto it = m_baseItems.find(itemId);
    return it != m_baseItems.end() ? &it->second : nullptr;
}

const std::string &MawItemData::legendaryAffixText(int affixId) const
{
    static const std::string Empty;
    const auto it = m_legendaryAffixTexts.find(affixId);
    return it != m_legendaryAffixTexts.end() ? it->second : Empty;
}
}
