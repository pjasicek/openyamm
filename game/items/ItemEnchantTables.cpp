#include "game/items/ItemEnchantTables.h"
#include "engine/Localization.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <array>
#include <cctype>

namespace OpenYAMM::Game
{
namespace
{
std::string toLowerCopy(const std::string &value)
{
    std::string result = value;

    for (char &character : result)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return result;
}

std::string trimCopy(const std::string &value)
{
    size_t begin = 0;

    while (begin < value.size() && std::isspace(static_cast<unsigned char>(value[begin])))
    {
        ++begin;
    }

    size_t end = value.size();

    while (end > begin && std::isspace(static_cast<unsigned char>(value[end - 1])))
    {
        --end;
    }

    return value.substr(begin, end - begin);
}

std::string getCell(const std::vector<std::string> &row, size_t index)
{
    if (index >= row.size())
    {
        return {};
    }

    return trimCopy(row[index]);
}

int parseInt(const std::string &value)
{
    if (value.empty())
    {
        return 0;
    }

    try
    {
        return std::stoi(value);
    }
    catch (...)
    {
        return 0;
    }
}

StandardItemEnchantKind parseStandardEnchantKind(const std::string &value)
{
    const std::string normalized = toLowerCopy(trimCopy(value));

    if (normalized == "might")
    {
        return StandardItemEnchantKind::Might;
    }

    if (normalized == "intellect")
    {
        return StandardItemEnchantKind::Intellect;
    }

    if (normalized == "personality")
    {
        return StandardItemEnchantKind::Personality;
    }

    if (normalized == "endurance")
    {
        return StandardItemEnchantKind::Endurance;
    }

    if (normalized == "accuracy")
    {
        return StandardItemEnchantKind::Accuracy;
    }

    if (normalized == "speed")
    {
        return StandardItemEnchantKind::Speed;
    }

    if (normalized == "luck")
    {
        return StandardItemEnchantKind::Luck;
    }

    if (normalized == "hit points")
    {
        return StandardItemEnchantKind::HitPoints;
    }

    if (normalized == "spell points")
    {
        return StandardItemEnchantKind::SpellPoints;
    }

    if (normalized == "armor class")
    {
        return StandardItemEnchantKind::ArmorClass;
    }

    if (normalized == "fire resistance")
    {
        return StandardItemEnchantKind::FireResistance;
    }

    if (normalized == "air resistance")
    {
        return StandardItemEnchantKind::AirResistance;
    }

    if (normalized == "water resistance")
    {
        return StandardItemEnchantKind::WaterResistance;
    }

    if (normalized == "earth resistance")
    {
        return StandardItemEnchantKind::EarthResistance;
    }

    if (normalized == "mind resistance")
    {
        return StandardItemEnchantKind::MindResistance;
    }

    if (normalized == "body resistance")
    {
        return StandardItemEnchantKind::BodyResistance;
    }

    if (normalized == "alchemy skill")
    {
        return StandardItemEnchantKind::Alchemy;
    }

    if (normalized == "stealing skill")
    {
        return StandardItemEnchantKind::Stealing;
    }

    if (normalized == "disarm skill")
    {
        return StandardItemEnchantKind::Disarm;
    }

    if (normalized == "id item skill")
    {
        return StandardItemEnchantKind::IdentifyItem;
    }

    if (normalized == "id monster skill")
    {
        return StandardItemEnchantKind::IdentifyMonster;
    }

    if (normalized == "armsmaster skill")
    {
        return StandardItemEnchantKind::Armsmaster;
    }

    if (normalized == "dodge skill")
    {
        return StandardItemEnchantKind::Dodge;
    }

    if (normalized == "unarmed skill")
    {
        return StandardItemEnchantKind::Unarmed;
    }

    return StandardItemEnchantKind::None;
}

SpecialItemEnchantKind parseSpecialEnchantKind(const std::string &value)
{
    const std::string normalized = toLowerCopy(trimCopy(value));

    if (normalized == "of protection")
    {
        return SpecialItemEnchantKind::Protection;
    }

    if (normalized == "of the gods")
    {
        return SpecialItemEnchantKind::Gods;
    }

    if (normalized == "of carnage")
    {
        return SpecialItemEnchantKind::Carnage;
    }

    if (normalized == "of cold")
    {
        return SpecialItemEnchantKind::Cold;
    }

    if (normalized == "of frost")
    {
        return SpecialItemEnchantKind::Frost;
    }

    if (normalized == "of ice")
    {
        return SpecialItemEnchantKind::Ice;
    }

    if (normalized == "of sparks")
    {
        return SpecialItemEnchantKind::Sparks;
    }

    if (normalized == "of lightning")
    {
        return SpecialItemEnchantKind::Lightning;
    }

    if (normalized == "of thunderbolts")
    {
        return SpecialItemEnchantKind::Thunderbolts;
    }

    if (normalized == "of fire")
    {
        return SpecialItemEnchantKind::Fire;
    }

    if (normalized == "of flame")
    {
        return SpecialItemEnchantKind::Flame;
    }

    if (normalized == "of infernos")
    {
        return SpecialItemEnchantKind::Infernos;
    }

    if (normalized == "of poison")
    {
        return SpecialItemEnchantKind::Poison;
    }

    if (normalized == "of venom")
    {
        return SpecialItemEnchantKind::Venom;
    }

    if (normalized == "of acid")
    {
        return SpecialItemEnchantKind::Acid;
    }

    if (normalized == "vampiric")
    {
        return SpecialItemEnchantKind::Vampiric;
    }

    if (normalized == "of recovery")
    {
        return SpecialItemEnchantKind::Recovery;
    }

    if (normalized == "of immunity")
    {
        return SpecialItemEnchantKind::Immunity;
    }

    if (normalized == "of sanity")
    {
        return SpecialItemEnchantKind::Sanity;
    }

    if (normalized == "of freedom")
    {
        return SpecialItemEnchantKind::Freedom;
    }

    if (normalized == "of antidotes")
    {
        return SpecialItemEnchantKind::Antidotes;
    }

    if (normalized == "of alarms")
    {
        return SpecialItemEnchantKind::Alarms;
    }

    if (normalized == "of the medusa")
    {
        return SpecialItemEnchantKind::Medusa;
    }

    if (normalized == "of force")
    {
        return SpecialItemEnchantKind::Force;
    }

    if (normalized == "of power")
    {
        return SpecialItemEnchantKind::Power;
    }

    if (normalized == "of air magic")
    {
        return SpecialItemEnchantKind::AirMagic;
    }

    if (normalized == "of body magic")
    {
        return SpecialItemEnchantKind::BodyMagic;
    }

    if (normalized == "of dark magic")
    {
        return SpecialItemEnchantKind::DarkMagic;
    }

    if (normalized == "of earth magic")
    {
        return SpecialItemEnchantKind::EarthMagic;
    }

    if (normalized == "of fire magic")
    {
        return SpecialItemEnchantKind::FireMagic;
    }

    if (normalized == "of light magic")
    {
        return SpecialItemEnchantKind::LightMagic;
    }

    if (normalized == "of mind magic")
    {
        return SpecialItemEnchantKind::MindMagic;
    }

    if (normalized == "of spirit magic")
    {
        return SpecialItemEnchantKind::SpiritMagic;
    }

    if (normalized == "of water magic")
    {
        return SpecialItemEnchantKind::WaterMagic;
    }

    if (normalized == "of thievery")
    {
        return SpecialItemEnchantKind::Thievery;
    }

    if (normalized == "of shielding")
    {
        return SpecialItemEnchantKind::Shielding;
    }

    if (normalized == "of regeneration")
    {
        return SpecialItemEnchantKind::Regeneration;
    }

    if (normalized == "of mana")
    {
        return SpecialItemEnchantKind::Mana;
    }

    if (normalized == "ogre slaying")
    {
        return SpecialItemEnchantKind::OgreSlaying;
    }

    if (normalized == "dragon slaying")
    {
        return SpecialItemEnchantKind::DragonSlaying;
    }

    if (normalized == "of darkness")
    {
        return SpecialItemEnchantKind::Darkness;
    }

    if (normalized == "of doom")
    {
        return SpecialItemEnchantKind::Doom;
    }

    if (normalized == "of earth")
    {
        return SpecialItemEnchantKind::Earth;
    }

    if (normalized == "of life")
    {
        return SpecialItemEnchantKind::Life;
    }

    if (normalized == "rogues'")
    {
        return SpecialItemEnchantKind::Rogues;
    }

    if (normalized == "of the dragon")
    {
        return SpecialItemEnchantKind::TheDragon;
    }

    if (normalized == "of the eclipse")
    {
        return SpecialItemEnchantKind::TheEclipse;
    }

    if (normalized == "of the golem")
    {
        return SpecialItemEnchantKind::TheGolem;
    }

    if (normalized == "of the moon")
    {
        return SpecialItemEnchantKind::TheMoon;
    }

    if (normalized == "of the phoenix")
    {
        return SpecialItemEnchantKind::ThePhoenix;
    }

    if (normalized == "of the sky")
    {
        return SpecialItemEnchantKind::TheSky;
    }

    if (normalized == "of the stars")
    {
        return SpecialItemEnchantKind::TheStars;
    }

    if (normalized == "of the sun")
    {
        return SpecialItemEnchantKind::TheSun;
    }

    if (normalized == "of the troll")
    {
        return SpecialItemEnchantKind::TheTroll;
    }

    if (normalized == "of the unicorn")
    {
        return SpecialItemEnchantKind::TheUnicorn;
    }

    if (normalized == "warriors'")
    {
        return SpecialItemEnchantKind::Warriors;
    }

    if (normalized == "wizards'")
    {
        return SpecialItemEnchantKind::Wizards;
    }

    if (normalized == "antique")
    {
        return SpecialItemEnchantKind::Antique;
    }

    if (normalized == "swift")
    {
        return SpecialItemEnchantKind::Swift;
    }

    if (normalized == "monks'")
    {
        return SpecialItemEnchantKind::Monks;
    }

    if (normalized == "thieves'")
    {
        return SpecialItemEnchantKind::Thieves;
    }

    if (normalized == "of identifying")
    {
        return SpecialItemEnchantKind::Identifying;
    }

    if (normalized == "elemental slaying")
    {
        return SpecialItemEnchantKind::ElementalSlaying;
    }

    if (normalized == "undead slaying")
    {
        return SpecialItemEnchantKind::UndeadSlaying;
    }

    if (normalized == "of david")
    {
        return SpecialItemEnchantKind::David;
    }

    if (normalized == "of plenty")
    {
        return SpecialItemEnchantKind::Plenty;
    }

    if (normalized == "assassins'")
    {
        return SpecialItemEnchantKind::Assassins;
    }

    if (normalized == "barbarians'")
    {
        return SpecialItemEnchantKind::Barbarians;
    }

    if (normalized == "of the storm")
    {
        return SpecialItemEnchantKind::TheStorm;
    }

    if (normalized == "of the ocean")
    {
        return SpecialItemEnchantKind::TheOcean;
    }

    if (normalized == "of water walking")
    {
        return SpecialItemEnchantKind::WaterWalking;
    }

    if (normalized == "of feather falling")
    {
        return SpecialItemEnchantKind::FeatherFalling;
    }

    static const std::array<const char *, 9> RulesetSpecials = {
        "of ascension", "lichs'", "paladins'", "warriormage'", "shadows'", "rangers'", "elementals'", "selfs'",
        "divines'",
    };

    if (std::find(RulesetSpecials.begin(), RulesetSpecials.end(), normalized) != RulesetSpecials.end())
    {
        return SpecialItemEnchantKind::RulesetSpecial;
    }

    return SpecialItemEnchantKind::None;
}

ItemEnchantPriceModifier parsePriceModifier(const std::string &value)
{
    ItemEnchantPriceModifier modifier = {};
    const std::string normalized = toLowerCopy(trimCopy(value));

    if (normalized.empty())
    {
        return modifier;
    }

    if (normalized[0] == 'x')
    {
        modifier.multiplicative = true;
        modifier.amount = parseInt(normalized.substr(1));
        return modifier;
    }

    modifier.amount = parseInt(normalized);
    return modifier;
}
}

bool StandardItemEnchantTable::load(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();

    for (const std::vector<std::string> &row : rows)
    {
        const std::string statName = getCell(row, 0);
        const std::string suffix = getCell(row, 1);

        if (statName.empty() || suffix.empty() || statName == "Bonus Stat")
        {
            continue;
        }

        StandardItemEnchantEntry entry = {};
        entry.kind = parseStandardEnchantKind(statName);
        entry.statName = statName;
        entry.suffix = suffix;

        for (size_t index = 0; index < entry.slotValues.size(); ++index)
        {
            entry.slotValues[index] = parseInt(getCell(row, 2 + index));
        }

        m_entries.push_back(std::move(entry));
    }

    return !m_entries.empty();
}

bool StandardItemEnchantTable::addAt(uint16_t enchantId, StandardItemEnchantEntry entry)
{
    if (enchantId == 0 || (enchantId <= m_entries.size() && m_entries[enchantId - 1].kind != StandardItemEnchantKind::None))
    {
        return false;
    }

    if (m_entries.size() < enchantId)
    {
        m_entries.resize(enchantId);
    }

    m_entries[enchantId - 1] = std::move(entry);
    return true;
}

const std::vector<StandardItemEnchantEntry> &StandardItemEnchantTable::entries() const
{
    return m_entries;
}

const StandardItemEnchantEntry *StandardItemEnchantTable::get(uint16_t enchantId) const
{
    if (enchantId == 0)
    {
        return nullptr;
    }

    const size_t index = static_cast<size_t>(enchantId - 1);
    return index < m_entries.size() ? &m_entries[index] : nullptr;
}

bool SpecialItemEnchantTable::load(const std::vector<std::vector<std::string>> &rows)
{
    m_entries.clear();

    for (const std::vector<std::string> &row : rows)
    {
        const std::string name = getCell(row, 0);
        const std::string suffix = getCell(row, 1);

        // The enchantments end at the first blank row; the notes below it are not enchantments, so a ruleset can
        // add ids after the last one.
        if (name.empty() && suffix.empty() && !m_entries.empty())
        {
            break;
        }

        if (name.empty() || suffix.empty() || name == "Bonus Stat")
        {
            continue;
        }

        SpecialItemEnchantEntry entry = {};
        entry.kind = parseSpecialEnchantKind(suffix);
        entry.name = name;
        entry.suffix = suffix;

        for (size_t index = 0; index < entry.slotWeights.size(); ++index)
        {
            entry.slotWeights[index] = parseInt(getCell(row, 2 + index));
        }

        entry.priceModifier = parsePriceModifier(getCell(row, 14));
        const std::string rarityText = getCell(row, 15);
        entry.rarityLevel = rarityText.empty() ? 0 : rarityText[0];
        entry.description = getCell(row, 16);
        entry.displayAsPrefix = !toLowerCopy(entry.suffix).starts_with("of ");
        m_entries.push_back(std::move(entry));
    }

    return !m_entries.empty();
}

bool SpecialItemEnchantTable::addAt(uint16_t enchantId, SpecialItemEnchantEntry entry)
{
    if (enchantId == 0 || (enchantId <= m_entries.size() && m_entries[enchantId - 1].kind != SpecialItemEnchantKind::None))
    {
        return false;
    }

    if (m_entries.size() < enchantId)
    {
        m_entries.resize(enchantId);
    }

    m_entries[enchantId - 1] = std::move(entry);
    return true;
}

bool loadWorldEnchantments(const std::string &text, const std::string &worldId, StandardItemEnchantTable &standard,
    SpecialItemEnchantTable &special, std::string &errorMessage)
{
    const std::string where = "worlds/" + worldId + "/enchantments.yml: ";

    try
    {
        const YAML::Node root = YAML::Load(text);

        if (!root.IsMap() || root["schema"].as<std::string>("") != "openyamm.worldEnchantments.v1")
        {
            errorMessage = where + "expected schema openyamm.worldEnchantments.v1";
            return false;
        }

        const auto readId = [&where, &errorMessage](const YAML::Node &node, uint16_t &id)
        {
            id = node["id"].as<uint16_t>(0);

            if (id < 100 || id > 999)
            {
                errorMessage = where + "enchantment ids must lie in 100-999";
                return false;
            }

            return true;
        };

        for (const YAML::Node &node : root["standard"])
        {
            StandardItemEnchantEntry entry = {};
            uint16_t id = 0;
            const YAML::Node slots = node["slots"];

            if (!readId(node, id) || node["stat"].as<std::string>("") != "energy_resistance" || !slots.IsSequence()
                || slots.size() != entry.slotValues.size())
            {
                errorMessage = errorMessage.empty()
                    ? where + "a standard enchantment needs stat: energy_resistance and nine slot weights"
                    : errorMessage;
                return false;
            }

            entry.kind = StandardItemEnchantKind::EnergyResistance;
            entry.statName = Engine::trNoop("Energy Resistance");
            entry.suffix = node["name"].as<std::string>();
            entry.worlds = {worldId};

            for (size_t slot = 0; slot < entry.slotValues.size(); ++slot)
            {
                entry.slotValues[slot] = slots[slot].as<int>();
            }

            if (!standard.addAt(id, std::move(entry)))
            {
                errorMessage = where + "standard enchantment id " + std::to_string(id) + " is taken";
                return false;
            }
        }

        for (const YAML::Node &node : root["special"])
        {
            SpecialItemEnchantEntry entry = {};
            uint16_t id = 0;
            const YAML::Node slots = node["slots"];
            const std::string rarity = node["rarity"].as<std::string>("");

            if (!readId(node, id) || !slots.IsSequence() || slots.size() != entry.slotWeights.size()
                || rarity.size() != 1 || rarity[0] < 'A' || rarity[0] > 'D')
            {
                errorMessage = errorMessage.empty()
                    ? where + "a special enchantment needs a rarity A-D and twelve slot weights"
                    : errorMessage;
                return false;
            }

            entry.kind = SpecialItemEnchantKind::World;
            entry.suffix = node["name"].as<std::string>();
            entry.name = node["description"].as<std::string>(entry.suffix);
            entry.description = entry.name;
            entry.rarityLevel = rarity[0];
            entry.priceModifier.amount = node["value"].as<int>(0);
            entry.displayAsPrefix = !toLowerCopy(entry.suffix).starts_with("of ");
            entry.requiredContentFlag = node["requires_flag"].as<std::string>("");
            entry.worlds = {worldId};

            for (size_t slot = 0; slot < entry.slotWeights.size(); ++slot)
            {
                entry.slotWeights[slot] = slots[slot].as<int>();
            }

            WorldEnchantEffect &effect = entry.worldEffect;
            const YAML::Node effectNode = node["effect"];
            effect.shieldDamagePercent = effectNode["shield_damage"].as<int>(0);
            effect.exposedDamagePercent = effectNode["exposed_damage"].as<int>(0);
            effect.overloadChancePercent = effectNode["overload_chance"].as<int>(0);
            effect.bonusDamagePercent = effectNode["bonus_damage"].as<int>(0);
            effect.personalShield = effectNode["personal_shield"].as<int>(0);
            effect.energyDamageTakenPercent = effectNode["energy_damage_taken"].as<int>(0);

            if (const YAML::Node energy = effectNode["energy_damage"])
            {
                effect.energyDamageMinimum = energy[0].as<int>();
                effect.energyDamageMaximum = energy[1].as<int>();
            }

            for (const YAML::Node &range : effectNode["against"])
            {
                effect.bonusMonsterIds.emplace_back(range[0].as<int>(), range[1].as<int>());
            }

            if (effect.energyDamageMaximum < effect.energyDamageMinimum
                || (effect.bonusDamagePercent != 0) != !effect.bonusMonsterIds.empty())
            {
                errorMessage = where + entry.suffix + ": energy_damage is [min, max]; bonus_damage needs against";
                return false;
            }

            if (!special.addAt(id, std::move(entry)))
            {
                errorMessage = where + "special enchantment id " + std::to_string(id) + " is taken";
                return false;
            }
        }
    }
    catch (const YAML::Exception &exception)
    {
        errorMessage = where + exception.what();
        return false;
    }

    return true;
}

const std::vector<SpecialItemEnchantEntry> &SpecialItemEnchantTable::entries() const
{
    return m_entries;
}

const SpecialItemEnchantEntry *SpecialItemEnchantTable::get(uint16_t enchantId) const
{
    if (enchantId == 0)
    {
        return nullptr;
    }

    const size_t index = static_cast<size_t>(enchantId - 1);
    return index < m_entries.size() ? &m_entries[index] : nullptr;
}

uint16_t SpecialItemEnchantTable::findId(SpecialItemEnchantKind kind) const
{
    for (size_t index = 0; index < m_entries.size(); ++index)
    {
        if (m_entries[index].kind == kind)
        {
            return static_cast<uint16_t>(index + 1);
        }
    }

    return 0;
}

}
