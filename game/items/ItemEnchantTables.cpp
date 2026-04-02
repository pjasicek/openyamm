#include "game/items/ItemEnchantTables.h"

#include <algorithm>
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

}
