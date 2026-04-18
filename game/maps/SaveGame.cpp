#include "game/maps/SaveGame.h"

#include <bitset>
#include <cctype>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <type_traits>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t SaveVersion = 18;
constexpr char SaveMagic[8] = {'O', 'Y', 'S', 'A', 'V', 'E', '1', '\0'};

std::string toLowerCopy(const std::string &value)
{
    std::string normalized = value;

    for (char &character : normalized)
    {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }

    return normalized;
}

int savePathDisplayPriority(const std::filesystem::path &path)
{
    const std::string stem = toLowerCopy(path.stem().string());

    if (stem == "autosave")
    {
        return 0;
    }

    if (stem == "quicksave")
    {
        return 1;
    }

    return 2;
}

class BinaryWriter
{
public:
    void writeBytes(const void *pData, size_t size)
    {
        const uint8_t *pBytes = static_cast<const uint8_t *>(pData);
        m_bytes.insert(m_bytes.end(), pBytes, pBytes + size);
    }

    template <typename T>
    void write(const T &value)
    {
        writeValue(*this, value);
    }

    const std::vector<uint8_t> &bytes() const
    {
        return m_bytes;
    }

private:
    std::vector<uint8_t> m_bytes;
};

class BinaryReader
{
public:
    explicit BinaryReader(const std::vector<uint8_t> &bytes)
        : m_bytes(bytes)
    {
    }

    bool readBytes(void *pData, size_t size)
    {
        if (m_offset + size > m_bytes.size())
        {
            m_failed = true;
            return false;
        }

        std::memcpy(pData, m_bytes.data() + m_offset, size);
        m_offset += size;
        return true;
    }

    template <typename T>
    bool read(T &value)
    {
        return readValue(*this, value);
    }

    bool failed() const
    {
        return m_failed;
    }

private:
    const std::vector<uint8_t> &m_bytes;
    size_t m_offset = 0;
    bool m_failed = false;
};

template <typename T>
requires(std::is_arithmetic_v<T>)
void writeValue(BinaryWriter &writer, const T &value)
{
    writer.writeBytes(&value, sizeof(value));
}

template <typename T>
requires(std::is_arithmetic_v<T>)
bool readValue(BinaryReader &reader, T &value)
{
    return reader.readBytes(&value, sizeof(value));
}

template <typename T>
requires(std::is_enum_v<T>)
void writeValue(BinaryWriter &writer, const T &value)
{
    const std::underlying_type_t<T> rawValue = static_cast<std::underlying_type_t<T>>(value);
    writeValue(writer, rawValue);
}

template <typename T>
requires(std::is_enum_v<T>)
bool readValue(BinaryReader &reader, T &value)
{
    std::underlying_type_t<T> rawValue = {};

    if (!readValue(reader, rawValue))
    {
        return false;
    }

    value = static_cast<T>(rawValue);
    return true;
}

void writeValue(BinaryWriter &writer, const std::string &value)
{
    const uint64_t size = static_cast<uint64_t>(value.size());
    writeValue(writer, size);

    if (!value.empty())
    {
        writer.writeBytes(value.data(), value.size());
    }
}

bool readValue(BinaryReader &reader, std::string &value)
{
    uint64_t size = 0;

    if (!readValue(reader, size))
    {
        return false;
    }

    value.resize(static_cast<size_t>(size));
    return value.empty() || reader.readBytes(value.data(), value.size());
}

template <size_t N>
void writeValue(BinaryWriter &writer, const std::bitset<N> &value)
{
    writeValue(writer, value.to_string());
}

template <size_t N>
bool readValue(BinaryReader &reader, std::bitset<N> &value)
{
    std::string encoded;

    if (!readValue(reader, encoded) || encoded.size() != N)
    {
        return false;
    }

    value = std::bitset<N>(encoded);
    return true;
}

template <typename T>
void writeValue(BinaryWriter &writer, const std::optional<T> &value)
{
    writeValue(writer, value.has_value());

    if (value.has_value())
    {
        writeValue(writer, *value);
    }
}

template <typename T>
bool readValue(BinaryReader &reader, std::optional<T> &value)
{
    bool hasValue = false;

    if (!readValue(reader, hasValue))
    {
        return false;
    }

    if (!hasValue)
    {
        value.reset();
        return true;
    }

    T decoded = {};

    if (!readValue(reader, decoded))
    {
        return false;
    }

    value = std::move(decoded);
    return true;
}

template <typename T>
void writeValue(BinaryWriter &writer, const std::vector<T> &value)
{
    const uint64_t size = static_cast<uint64_t>(value.size());
    writeValue(writer, size);

    for (const T &entry : value)
    {
        writeValue(writer, entry);
    }
}

template <typename T>
bool readValue(BinaryReader &reader, std::vector<T> &value)
{
    uint64_t size = 0;

    if (!readValue(reader, size))
    {
        return false;
    }

    value.clear();
    value.reserve(static_cast<size_t>(size));

    for (uint64_t index = 0; index < size; ++index)
    {
        T entry = {};

        if (!readValue(reader, entry))
        {
            return false;
        }

        value.push_back(std::move(entry));
    }

    return true;
}

template <typename T, size_t N>
void writeValue(BinaryWriter &writer, const std::array<T, N> &value)
{
    for (const T &entry : value)
    {
        writeValue(writer, entry);
    }
}

template <typename T, size_t N>
bool readValue(BinaryReader &reader, std::array<T, N> &value)
{
    for (T &entry : value)
    {
        if (!readValue(reader, entry))
        {
            return false;
        }
    }

    return true;
}

template <typename K, typename V>
void writeValue(BinaryWriter &writer, const std::unordered_map<K, V> &value)
{
    const uint64_t size = static_cast<uint64_t>(value.size());
    writeValue(writer, size);

    for (const auto &[key, entry] : value)
    {
        writeValue(writer, key);
        writeValue(writer, entry);
    }
}

template <typename K, typename V>
bool readValue(BinaryReader &reader, std::unordered_map<K, V> &value)
{
    uint64_t size = 0;

    if (!readValue(reader, size))
    {
        return false;
    }

    value.clear();
    value.reserve(static_cast<size_t>(size));

    for (uint64_t index = 0; index < size; ++index)
    {
        K key = {};
        V entry = {};

        if (!readValue(reader, key) || !readValue(reader, entry))
        {
            return false;
        }

        value.emplace(std::move(key), std::move(entry));
    }

    return true;
}

template <typename T>
void writeValue(BinaryWriter &writer, const std::unordered_set<T> &value)
{
    const uint64_t size = static_cast<uint64_t>(value.size());
    writeValue(writer, size);

    for (const T &entry : value)
    {
        writeValue(writer, entry);
    }
}

template <typename T>
bool readValue(BinaryReader &reader, std::unordered_set<T> &value)
{
    uint64_t size = 0;

    if (!readValue(reader, size))
    {
        return false;
    }

    value.clear();
    value.reserve(static_cast<size_t>(size));

    for (uint64_t index = 0; index < size; ++index)
    {
        T entry = {};

        if (!readValue(reader, entry))
        {
            return false;
        }

        value.insert(std::move(entry));
    }

    return true;
}

void writeValue(BinaryWriter &writer, const CharacterSkill &value)
{
    writeValue(writer, value.name);
    writeValue(writer, value.level);
    writeValue(writer, value.mastery);
}

bool readValue(BinaryReader &reader, CharacterSkill &value)
{
    return readValue(reader, value.name)
        && readValue(reader, value.level)
        && readValue(reader, value.mastery);
}

void writeValue(BinaryWriter &writer, const InventoryItem &value)
{
    writeValue(writer, value.objectDescriptionId);
    writeValue(writer, value.quantity);
    writeValue(writer, value.width);
    writeValue(writer, value.height);
    writeValue(writer, value.gridX);
    writeValue(writer, value.gridY);
    writeValue(writer, value.identified);
    writeValue(writer, value.broken);
    writeValue(writer, value.stolen);
    writeValue(writer, value.standardEnchantId);
    writeValue(writer, value.standardEnchantPower);
    writeValue(writer, value.specialEnchantId);
    writeValue(writer, value.artifactId);
    writeValue(writer, value.rarity);
    writeValue(writer, value.temporaryBonusRemainingSeconds);
}

bool readValue(BinaryReader &reader, InventoryItem &value)
{
    return readValue(reader, value.objectDescriptionId)
        && readValue(reader, value.quantity)
        && readValue(reader, value.width)
        && readValue(reader, value.height)
        && readValue(reader, value.gridX)
        && readValue(reader, value.gridY)
        && readValue(reader, value.identified)
        && readValue(reader, value.broken)
        && readValue(reader, value.stolen)
        && readValue(reader, value.standardEnchantId)
        && readValue(reader, value.standardEnchantPower)
        && readValue(reader, value.specialEnchantId)
        && readValue(reader, value.artifactId)
        && readValue(reader, value.rarity)
        && readValue(reader, value.temporaryBonusRemainingSeconds);
}

void writeValue(BinaryWriter &writer, const LloydBeacon &value)
{
    writeValue(writer, value.mapName);
    writeValue(writer, value.locationName);
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.z);
    writeValue(writer, value.directionDegrees);
    writeValue(writer, value.remainingSeconds);
}

bool readValue(BinaryReader &reader, LloydBeacon &value)
{
    return readValue(reader, value.mapName)
        && readValue(reader, value.locationName)
        && readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.z)
        && readValue(reader, value.directionDegrees)
        && readValue(reader, value.remainingSeconds);
}

void writeValue(BinaryWriter &writer, const CharacterResistanceSet &value)
{
    writeValue(writer, value.fire);
    writeValue(writer, value.air);
    writeValue(writer, value.water);
    writeValue(writer, value.earth);
    writeValue(writer, value.mind);
    writeValue(writer, value.body);
    writeValue(writer, value.spirit);
}

bool readValue(BinaryReader &reader, CharacterResistanceSet &value)
{
    return readValue(reader, value.fire)
        && readValue(reader, value.air)
        && readValue(reader, value.water)
        && readValue(reader, value.earth)
        && readValue(reader, value.mind)
        && readValue(reader, value.body)
        && readValue(reader, value.spirit);
}

void writeValue(BinaryWriter &writer, const CharacterResistanceImmunitySet &value)
{
    writeValue(writer, value.fire);
    writeValue(writer, value.air);
    writeValue(writer, value.water);
    writeValue(writer, value.earth);
    writeValue(writer, value.mind);
    writeValue(writer, value.body);
    writeValue(writer, value.spirit);
}

bool readValue(BinaryReader &reader, CharacterResistanceImmunitySet &value)
{
    return readValue(reader, value.fire)
        && readValue(reader, value.air)
        && readValue(reader, value.water)
        && readValue(reader, value.earth)
        && readValue(reader, value.mind)
        && readValue(reader, value.body)
        && readValue(reader, value.spirit);
}

void writeValue(BinaryWriter &writer, const CharacterStatBonuses &value)
{
    writeValue(writer, value.might);
    writeValue(writer, value.intellect);
    writeValue(writer, value.personality);
    writeValue(writer, value.endurance);
    writeValue(writer, value.speed);
    writeValue(writer, value.accuracy);
    writeValue(writer, value.luck);
    writeValue(writer, value.maxHealth);
    writeValue(writer, value.maxSpellPoints);
    writeValue(writer, value.armorClass);
    writeValue(writer, value.meleeAttack);
    writeValue(writer, value.rangedAttack);
    writeValue(writer, value.meleeDamage);
    writeValue(writer, value.rangedDamage);
    writeValue(writer, value.resistances);
}

bool readValue(BinaryReader &reader, CharacterStatBonuses &value)
{
    return readValue(reader, value.might)
        && readValue(reader, value.intellect)
        && readValue(reader, value.personality)
        && readValue(reader, value.endurance)
        && readValue(reader, value.speed)
        && readValue(reader, value.accuracy)
        && readValue(reader, value.luck)
        && readValue(reader, value.maxHealth)
        && readValue(reader, value.maxSpellPoints)
        && readValue(reader, value.armorClass)
        && readValue(reader, value.meleeAttack)
        && readValue(reader, value.rangedAttack)
        && readValue(reader, value.meleeDamage)
        && readValue(reader, value.rangedDamage)
        && readValue(reader, value.resistances);
}

void writeValue(BinaryWriter &writer, const CharacterEquipment &value)
{
    writeValue(writer, value.offHand);
    writeValue(writer, value.mainHand);
    writeValue(writer, value.bow);
    writeValue(writer, value.armor);
    writeValue(writer, value.helm);
    writeValue(writer, value.belt);
    writeValue(writer, value.cloak);
    writeValue(writer, value.gauntlets);
    writeValue(writer, value.boots);
    writeValue(writer, value.amulet);
    writeValue(writer, value.ring1);
    writeValue(writer, value.ring2);
    writeValue(writer, value.ring3);
    writeValue(writer, value.ring4);
    writeValue(writer, value.ring5);
    writeValue(writer, value.ring6);
}

bool readValue(BinaryReader &reader, CharacterEquipment &value)
{
    return readValue(reader, value.offHand)
        && readValue(reader, value.mainHand)
        && readValue(reader, value.bow)
        && readValue(reader, value.armor)
        && readValue(reader, value.helm)
        && readValue(reader, value.belt)
        && readValue(reader, value.cloak)
        && readValue(reader, value.gauntlets)
        && readValue(reader, value.boots)
        && readValue(reader, value.amulet)
        && readValue(reader, value.ring1)
        && readValue(reader, value.ring2)
        && readValue(reader, value.ring3)
        && readValue(reader, value.ring4)
        && readValue(reader, value.ring5)
        && readValue(reader, value.ring6);
}

void writeValue(BinaryWriter &writer, const EquippedItemRuntimeState &value)
{
    writeValue(writer, value.identified);
    writeValue(writer, value.broken);
    writeValue(writer, value.stolen);
    writeValue(writer, value.standardEnchantId);
    writeValue(writer, value.standardEnchantPower);
    writeValue(writer, value.specialEnchantId);
    writeValue(writer, value.artifactId);
    writeValue(writer, value.rarity);
    writeValue(writer, value.temporaryBonusRemainingSeconds);
}

bool readValue(BinaryReader &reader, EquippedItemRuntimeState &value)
{
    return readValue(reader, value.identified)
        && readValue(reader, value.broken)
        && readValue(reader, value.stolen)
        && readValue(reader, value.standardEnchantId)
        && readValue(reader, value.standardEnchantPower)
        && readValue(reader, value.specialEnchantId)
        && readValue(reader, value.artifactId)
        && readValue(reader, value.rarity)
        && readValue(reader, value.temporaryBonusRemainingSeconds);
}

void writeValue(BinaryWriter &writer, const CharacterEquipmentRuntimeState &value)
{
    writeValue(writer, value.offHand);
    writeValue(writer, value.mainHand);
    writeValue(writer, value.bow);
    writeValue(writer, value.armor);
    writeValue(writer, value.helm);
    writeValue(writer, value.belt);
    writeValue(writer, value.cloak);
    writeValue(writer, value.gauntlets);
    writeValue(writer, value.boots);
    writeValue(writer, value.amulet);
    writeValue(writer, value.ring1);
    writeValue(writer, value.ring2);
    writeValue(writer, value.ring3);
    writeValue(writer, value.ring4);
    writeValue(writer, value.ring5);
    writeValue(writer, value.ring6);
}

bool readValue(BinaryReader &reader, CharacterEquipmentRuntimeState &value)
{
    return readValue(reader, value.offHand)
        && readValue(reader, value.mainHand)
        && readValue(reader, value.bow)
        && readValue(reader, value.armor)
        && readValue(reader, value.helm)
        && readValue(reader, value.belt)
        && readValue(reader, value.cloak)
        && readValue(reader, value.gauntlets)
        && readValue(reader, value.boots)
        && readValue(reader, value.amulet)
        && readValue(reader, value.ring1)
        && readValue(reader, value.ring2)
        && readValue(reader, value.ring3)
        && readValue(reader, value.ring4)
        && readValue(reader, value.ring5)
        && readValue(reader, value.ring6);
}

void writeValue(BinaryWriter &writer, const Character &value)
{
    writeValue(writer, value.name);
    writeValue(writer, value.role);
    writeValue(writer, value.className);
    writeValue(writer, value.portraitTextureName);
    writeValue(writer, value.portraitPictureId);
    writeValue(writer, value.portraitState);
    writeValue(writer, value.portraitElapsedTicks);
    writeValue(writer, value.portraitDurationTicks);
    writeValue(writer, value.portraitSequenceCounter);
    writeValue(writer, value.portraitImageIndex);
    writeValue(writer, value.rosterId);
    writeValue(writer, value.characterDataId);
    writeValue(writer, value.voiceId);
    writeValue(writer, value.birthYear);
    writeValue(writer, value.sexId);
    writeValue(writer, value.raceId);
    writeValue(writer, value.experience);
    writeValue(writer, value.level);
    writeValue(writer, value.skillPoints);
    writeValue(writer, value.might);
    writeValue(writer, value.intellect);
    writeValue(writer, value.personality);
    writeValue(writer, value.endurance);
    writeValue(writer, value.speed);
    writeValue(writer, value.accuracy);
    writeValue(writer, value.luck);
    writeValue(writer, value.maxHealth);
    writeValue(writer, value.health);
    writeValue(writer, value.maxSpellPoints);
    writeValue(writer, value.spellPoints);
    writeValue(writer, value.quickSpellName);
    writeValue(writer, value.knownSpellIds);
    writeValue(writer, value.baseResistances);
    writeValue(writer, value.permanentBonuses);
    writeValue(writer, value.magicalBonuses);
    writeValue(writer, value.permanentImmunities);
    writeValue(writer, value.magicalImmunities);
    writeValue(writer, value.permanentConditionImmunities);
    writeValue(writer, value.magicalConditionImmunities);
    writeValue(writer, value.equipment);
    writeValue(writer, value.equipmentRuntime);
    writeValue(writer, value.conditions);
    writeValue(writer, value.skills);
    writeValue(writer, value.awards);
    writeValue(writer, value.eventVariables);
    writeValue(writer, value.recoverySecondsRemaining);
    writeValue(writer, value.armorClassModifier);
    writeValue(writer, value.levelModifier);
    writeValue(writer, value.ageModifier);
    writeValue(writer, value.playerBits);
    writeValue(writer, value.npcs2);
    writeValue(writer, value.healthRegenAccumulator);
    writeValue(writer, value.spellRegenAccumulator);
    writeValue(writer, value.lloydsBeacons);
    writeValue(writer, value.inventory);
}

bool readValue(BinaryReader &reader, Character &value)
{
    return readValue(reader, value.name)
        && readValue(reader, value.role)
        && readValue(reader, value.className)
        && readValue(reader, value.portraitTextureName)
        && readValue(reader, value.portraitPictureId)
        && readValue(reader, value.portraitState)
        && readValue(reader, value.portraitElapsedTicks)
        && readValue(reader, value.portraitDurationTicks)
        && readValue(reader, value.portraitSequenceCounter)
        && readValue(reader, value.portraitImageIndex)
        && readValue(reader, value.rosterId)
        && readValue(reader, value.characterDataId)
        && readValue(reader, value.voiceId)
        && readValue(reader, value.birthYear)
        && readValue(reader, value.sexId)
        && readValue(reader, value.raceId)
        && readValue(reader, value.experience)
        && readValue(reader, value.level)
        && readValue(reader, value.skillPoints)
        && readValue(reader, value.might)
        && readValue(reader, value.intellect)
        && readValue(reader, value.personality)
        && readValue(reader, value.endurance)
        && readValue(reader, value.speed)
        && readValue(reader, value.accuracy)
        && readValue(reader, value.luck)
        && readValue(reader, value.maxHealth)
        && readValue(reader, value.health)
        && readValue(reader, value.maxSpellPoints)
        && readValue(reader, value.spellPoints)
        && readValue(reader, value.quickSpellName)
        && readValue(reader, value.knownSpellIds)
        && readValue(reader, value.baseResistances)
        && readValue(reader, value.permanentBonuses)
        && readValue(reader, value.magicalBonuses)
        && readValue(reader, value.permanentImmunities)
        && readValue(reader, value.magicalImmunities)
        && readValue(reader, value.permanentConditionImmunities)
        && readValue(reader, value.magicalConditionImmunities)
        && readValue(reader, value.equipment)
        && readValue(reader, value.equipmentRuntime)
        && readValue(reader, value.conditions)
        && readValue(reader, value.skills)
        && readValue(reader, value.awards)
        && readValue(reader, value.eventVariables)
        && readValue(reader, value.recoverySecondsRemaining)
        && readValue(reader, value.armorClassModifier)
        && readValue(reader, value.levelModifier)
        && readValue(reader, value.ageModifier)
        && readValue(reader, value.playerBits)
        && readValue(reader, value.npcs2)
        && readValue(reader, value.healthRegenAccumulator)
        && readValue(reader, value.spellRegenAccumulator)
        && readValue(reader, value.lloydsBeacons)
        && readValue(reader, value.inventory);
}

void writeValue(BinaryWriter &writer, const PartyBuffState &value)
{
    writeValue(writer, value.remainingSeconds);
    writeValue(writer, value.spellId);
    writeValue(writer, value.skillLevel);
    writeValue(writer, value.skillMastery);
    writeValue(writer, value.power);
    writeValue(writer, value.casterMemberIndex);
}

bool readValue(BinaryReader &reader, PartyBuffState &value)
{
    return readValue(reader, value.remainingSeconds)
        && readValue(reader, value.spellId)
        && readValue(reader, value.skillLevel)
        && readValue(reader, value.skillMastery)
        && readValue(reader, value.power)
        && readValue(reader, value.casterMemberIndex);
}

void writeValue(BinaryWriter &writer, const CharacterBuffState &value)
{
    writeValue(writer, value.remainingSeconds);
    writeValue(writer, value.periodicAccumulatorSeconds);
    writeValue(writer, value.spellId);
    writeValue(writer, value.skillLevel);
    writeValue(writer, value.skillMastery);
    writeValue(writer, value.power);
    writeValue(writer, value.casterMemberIndex);
}

bool readValue(BinaryReader &reader, CharacterBuffState &value)
{
    return readValue(reader, value.remainingSeconds)
        && readValue(reader, value.periodicAccumulatorSeconds)
        && readValue(reader, value.spellId)
        && readValue(reader, value.skillLevel)
        && readValue(reader, value.skillMastery)
        && readValue(reader, value.power)
        && readValue(reader, value.casterMemberIndex);
}

void writeValue(BinaryWriter &writer, const Party::HouseStockState &value)
{
    writeValue(writer, value.houseId);
    writeValue(writer, value.nextRefreshGameMinutes);
    writeValue(writer, value.refreshSequence);
    writeValue(writer, value.standardStock);
    writeValue(writer, value.specialStock);
    writeValue(writer, value.spellbookStock);
}

bool readValue(BinaryReader &reader, Party::HouseStockState &value)
{
    return readValue(reader, value.houseId)
        && readValue(reader, value.nextRefreshGameMinutes)
        && readValue(reader, value.refreshSequence)
        && readValue(reader, value.standardStock)
        && readValue(reader, value.specialStock)
        && readValue(reader, value.spellbookStock);
}

void writeValue(BinaryWriter &writer, const AdventurersInnMember &value)
{
    writeValue(writer, value.character);
    writeValue(writer, value.portraitPictureId);
}

bool readValue(BinaryReader &reader, AdventurersInnMember &value)
{
    return readValue(reader, value.character)
        && readValue(reader, value.portraitPictureId);
}

void writeValue(BinaryWriter &writer, const Party::Snapshot &value)
{
    writeValue(writer, value.members);
    writeValue(writer, value.adventurersInnMembers);
    writeValue(writer, value.activeMemberIndex);
    writeValue(writer, value.partyBuffs);
    writeValue(writer, value.characterBuffs);
    writeValue(writer, value.gold);
    writeValue(writer, value.bankGold);
    writeValue(writer, value.food);
    writeValue(writer, value.waterDamageTicks);
    writeValue(writer, value.burningDamageTicks);
    writeValue(writer, value.splashCount);
    writeValue(writer, value.landingSoundCount);
    writeValue(writer, value.hardLandingSoundCount);
    writeValue(writer, value.monsterTargetSelectionCounter);
    writeValue(writer, value.houseStockSeed);
    writeValue(writer, value.lastFallDamageDistance);
    writeValue(writer, value.foundArtifactItems);
    writeValue(writer, value.arcomageWonHouseIds);
    writeValue(writer, value.arcomageWinCount);
    writeValue(writer, value.arcomageLossCount);
    writeValue(writer, value.houseStockStates);
    writeValue(writer, value.questBits);
    writeValue(writer, value.eventVariables);
}

bool readValue(BinaryReader &reader, Party::Snapshot &value)
{
    return readValue(reader, value.members)
        && readValue(reader, value.adventurersInnMembers)
        && readValue(reader, value.activeMemberIndex)
        && readValue(reader, value.partyBuffs)
        && readValue(reader, value.characterBuffs)
        && readValue(reader, value.gold)
        && readValue(reader, value.bankGold)
        && readValue(reader, value.food)
        && readValue(reader, value.waterDamageTicks)
        && readValue(reader, value.burningDamageTicks)
        && readValue(reader, value.splashCount)
        && readValue(reader, value.landingSoundCount)
        && readValue(reader, value.hardLandingSoundCount)
        && readValue(reader, value.monsterTargetSelectionCounter)
        && readValue(reader, value.houseStockSeed)
        && readValue(reader, value.lastFallDamageDistance)
        && readValue(reader, value.foundArtifactItems)
        && readValue(reader, value.arcomageWonHouseIds)
        && readValue(reader, value.arcomageWinCount)
        && readValue(reader, value.arcomageLossCount)
        && readValue(reader, value.houseStockStates)
        && readValue(reader, value.questBits)
        && readValue(reader, value.eventVariables);
}

void writeValue(BinaryWriter &writer, const OutdoorMoveState &value)
{
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.footZ);
    writeValue(writer, value.verticalVelocity);
    writeValue(writer, value.supportKind);
    writeValue(writer, value.supportBModelIndex);
    writeValue(writer, value.supportFaceIndex);
    writeValue(writer, value.supportIsFluid);
    writeValue(writer, value.supportOnWater);
    writeValue(writer, value.supportOnBurning);
    writeValue(writer, value.airborne);
    writeValue(writer, value.landedThisFrame);
    writeValue(writer, value.fallStartZ);
    writeValue(writer, value.fallDistance);
}

bool readValue(BinaryReader &reader, OutdoorMoveState &value)
{
    return readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.footZ)
        && readValue(reader, value.verticalVelocity)
        && readValue(reader, value.supportKind)
        && readValue(reader, value.supportBModelIndex)
        && readValue(reader, value.supportFaceIndex)
        && readValue(reader, value.supportIsFluid)
        && readValue(reader, value.supportOnWater)
        && readValue(reader, value.supportOnBurning)
        && readValue(reader, value.airborne)
        && readValue(reader, value.landedThisFrame)
        && readValue(reader, value.fallStartZ)
        && readValue(reader, value.fallDistance);
}

void writeValue(BinaryWriter &writer, const OutdoorPartyMovementState &value)
{
    writeValue(writer, value.running);
    writeValue(writer, value.flying);
    writeValue(writer, value.featherFall);
    writeValue(writer, value.waterWalk);
}

bool readValue(BinaryReader &reader, OutdoorPartyMovementState &value)
{
    return readValue(reader, value.running)
        && readValue(reader, value.flying)
        && readValue(reader, value.featherFall)
        && readValue(reader, value.waterWalk);
}

void writeValue(BinaryWriter &writer, const OutdoorPartyRuntime::Snapshot &value)
{
    writeValue(writer, value.movementState);
    writeValue(writer, value.partyMovementState);
}

bool readValue(BinaryReader &reader, OutdoorPartyRuntime::Snapshot &value)
{
    return readValue(reader, value.movementState)
        && readValue(reader, value.partyMovementState);
}

void writeValue(BinaryWriter &writer, const RuntimeMechanismState &value)
{
    writeValue(writer, value.state);
    writeValue(writer, value.timeSinceTriggeredMs);
    writeValue(writer, value.currentDistance);
    writeValue(writer, value.isMoving);
}

bool readValue(BinaryReader &reader, RuntimeMechanismState &value)
{
    return readValue(reader, value.state)
        && readValue(reader, value.timeSinceTriggeredMs)
        && readValue(reader, value.currentDistance)
        && readValue(reader, value.isMoving);
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::PendingDialogueContext &value)
{
    writeValue(writer, value.kind);
    writeValue(writer, value.sourceId);
    writeValue(writer, value.hostHouseId);
    writeValue(writer, value.newsId);
    writeValue(writer, value.titleOverride);
}

bool readValue(BinaryReader &reader, EventRuntimeState::PendingDialogueContext &value)
{
    return readValue(reader, value.kind)
        && readValue(reader, value.sourceId)
        && readValue(reader, value.hostHouseId)
        && readValue(reader, value.newsId)
        && readValue(reader, value.titleOverride);
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::PendingMapMove &value)
{
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.z);
    writeValue(writer, value.mapName);
    writeValue(writer, value.directionDegrees);
    writeValue(writer, value.useMapStartPosition);
}

bool readValue(BinaryReader &reader, EventRuntimeState::PendingMapMove &value)
{
    return readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.z)
        && readValue(reader, value.mapName)
        && readValue(reader, value.directionDegrees)
        && readValue(reader, value.useMapStartPosition);
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::PendingMovie &value)
{
    writeValue(writer, value.movieName);
    writeValue(writer, value.restoreAfterPlayback);
}

bool readValue(BinaryReader &reader, EventRuntimeState::PendingMovie &value)
{
    return readValue(reader, value.movieName)
        && readValue(reader, value.restoreAfterPlayback);
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::PendingInputPrompt &value)
{
    writeValue(writer, value.kind);
    writeValue(writer, value.eventId);
    writeValue(writer, value.continueStep);
    writeValue(writer, value.textId);
    writeValue(writer, value.text);
}

bool readValue(BinaryReader &reader, EventRuntimeState::PendingInputPrompt &value)
{
    return readValue(reader, value.kind)
        && readValue(reader, value.eventId)
        && readValue(reader, value.continueStep)
        && readValue(reader, value.textId)
        && readValue(reader, value.text);
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::PendingSound &value)
{
    writeValue(writer, value.soundId);
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.positional);
}

bool readValue(BinaryReader &reader, EventRuntimeState::PendingSound &value)
{
    return readValue(reader, value.soundId)
        && readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.positional);
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::SpriteOverride &value)
{
    writeValue(writer, value.hidden);
    writeValue(writer, value.textureName);
}

bool readValue(BinaryReader &reader, EventRuntimeState::SpriteOverride &value)
{
    return readValue(reader, value.hidden)
        && readValue(reader, value.textureName);
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::PendingArcomageGame &value)
{
    writeValue(writer, value.houseId);
}

bool readValue(BinaryReader &reader, EventRuntimeState::PendingArcomageGame &value)
{
    return readValue(reader, value.houseId);
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::DialogueOfferState &value)
{
    writeValue(writer, value.kind);
    writeValue(writer, value.npcId);
    writeValue(writer, value.topicId);
    writeValue(writer, value.messageTextId);
    writeValue(writer, value.rosterId);
    writeValue(writer, value.partyFullTextId);
}

bool readValue(BinaryReader &reader, EventRuntimeState::DialogueOfferState &value)
{
    return readValue(reader, value.kind)
        && readValue(reader, value.npcId)
        && readValue(reader, value.topicId)
        && readValue(reader, value.messageTextId)
        && readValue(reader, value.rosterId)
        && readValue(reader, value.partyFullTextId);
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::DialogueRuntimeState &value)
{
    writeValue(writer, value.hostHouseId);
    writeValue(writer, value.menuStack);
    writeValue(writer, value.currentOffer);
}

bool readValue(BinaryReader &reader, EventRuntimeState::DialogueRuntimeState &value)
{
    return readValue(reader, value.hostHouseId)
        && readValue(reader, value.menuStack)
        && readValue(reader, value.currentOffer);
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::ActiveDecorationContext &value)
{
    writeValue(writer, value.decorVarIndex);
    writeValue(writer, value.baseEventId);
    writeValue(writer, value.currentEventId);
    writeValue(writer, value.eventCount);
    writeValue(writer, value.hideWhenCleared);
}

bool readValue(BinaryReader &reader, EventRuntimeState::ActiveDecorationContext &value)
{
    return readValue(reader, value.decorVarIndex)
        && readValue(reader, value.baseEventId)
        && readValue(reader, value.currentEventId)
        && readValue(reader, value.eventCount)
        && readValue(reader, value.hideWhenCleared);
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::PortraitFxRequest &value)
{
    writeValue(writer, value.kind);
    writeValue(writer, value.memberIndices);
}

bool readValue(BinaryReader &reader, EventRuntimeState::PortraitFxRequest &value)
{
    return readValue(reader, value.kind)
        && readValue(reader, value.memberIndices);
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::SpellFxRequest &value)
{
    writeValue(writer, value.spellId);
    writeValue(writer, value.memberIndices);
}

bool readValue(BinaryReader &reader, EventRuntimeState::SpellFxRequest &value)
{
    return readValue(reader, value.spellId)
        && readValue(reader, value.memberIndices);
}

void writeValue(BinaryWriter &writer, const EventRuntimeState &value)
{
    writeValue(writer, value.variables);
    writeValue(writer, value.historyEventTimes);
    writeValue(writer, value.mapVars);
    writeValue(writer, value.facetSetMasks);
    writeValue(writer, value.facetClearMasks);
    writeValue(writer, value.mechanisms);
    writeValue(writer, value.textureOverrides);
    writeValue(writer, value.spriteOverrides);
    writeValue(writer, value.indoorLightsEnabled);
    writeValue(writer, value.snowEnabled);
    writeValue(writer, value.rainEnabled);
    writeValue(writer, value.actorSetMasks);
    writeValue(writer, value.actorClearMasks);
    writeValue(writer, value.actorGroupSetMasks);
    writeValue(writer, value.actorGroupClearMasks);
    writeValue(writer, value.actorIdGroupOverrides);
    writeValue(writer, value.actorGroupOverrides);
    writeValue(writer, value.actorGroupAllyOverrides);
    writeValue(writer, value.chestSetMasks);
    writeValue(writer, value.chestClearMasks);
    writeValue(writer, value.npcTopicOverrides);
    writeValue(writer, value.npcGroupNews);
    writeValue(writer, value.npcGreetingOverrides);
    writeValue(writer, value.npcGreetingDisplayCounts);
    writeValue(writer, value.npcHouseOverrides);
    writeValue(writer, value.npcItemOverrides);
    writeValue(writer, value.actorItemOverrides);
    writeValue(writer, value.unavailableNpcIds);
    writeValue(writer, value.dialogueState);
    writeValue(writer, value.decorVars);
    writeValue(writer, value.activeDecorationContext);
    writeValue(writer, value.messages);
    writeValue(writer, value.statusMessages);
    writeValue(writer, value.openedChestIds);
    writeValue(writer, value.grantedItems);
    writeValue(writer, value.grantedItemIds);
    writeValue(writer, value.removedItemIds);
    writeValue(writer, value.grantedAwardIds);
    writeValue(writer, value.removedAwardIds);
    writeValue(writer, value.portraitFxRequests);
    writeValue(writer, value.spellFxRequests);
    writeValue(writer, value.pendingDialogueContext);
    writeValue(writer, value.pendingMapMove);
    writeValue(writer, value.pendingMovie);
    writeValue(writer, value.pendingInputPrompt);
    writeValue(writer, value.pendingArcomageGame);
    writeValue(writer, value.pendingSounds);
    writeValue(writer, value.lastAffectedMechanismIds);
    writeValue(writer, value.lastActivationResult);
    writeValue(writer, value.localOnLoadEventsExecuted);
    writeValue(writer, value.globalOnLoadEventsExecuted);
}

bool readValue(BinaryReader &reader, EventRuntimeState &value)
{
    return readValue(reader, value.variables)
        && readValue(reader, value.historyEventTimes)
        && readValue(reader, value.mapVars)
        && readValue(reader, value.facetSetMasks)
        && readValue(reader, value.facetClearMasks)
        && readValue(reader, value.mechanisms)
        && readValue(reader, value.textureOverrides)
        && readValue(reader, value.spriteOverrides)
        && readValue(reader, value.indoorLightsEnabled)
        && readValue(reader, value.snowEnabled)
        && readValue(reader, value.rainEnabled)
        && readValue(reader, value.actorSetMasks)
        && readValue(reader, value.actorClearMasks)
        && readValue(reader, value.actorGroupSetMasks)
        && readValue(reader, value.actorGroupClearMasks)
        && readValue(reader, value.actorIdGroupOverrides)
        && readValue(reader, value.actorGroupOverrides)
        && readValue(reader, value.actorGroupAllyOverrides)
        && readValue(reader, value.chestSetMasks)
        && readValue(reader, value.chestClearMasks)
        && readValue(reader, value.npcTopicOverrides)
        && readValue(reader, value.npcGroupNews)
        && readValue(reader, value.npcGreetingOverrides)
        && readValue(reader, value.npcGreetingDisplayCounts)
        && readValue(reader, value.npcHouseOverrides)
        && readValue(reader, value.npcItemOverrides)
        && readValue(reader, value.actorItemOverrides)
        && readValue(reader, value.unavailableNpcIds)
        && readValue(reader, value.dialogueState)
        && readValue(reader, value.decorVars)
        && readValue(reader, value.activeDecorationContext)
        && readValue(reader, value.messages)
        && readValue(reader, value.statusMessages)
        && readValue(reader, value.openedChestIds)
        && readValue(reader, value.grantedItems)
        && readValue(reader, value.grantedItemIds)
        && readValue(reader, value.removedItemIds)
        && readValue(reader, value.grantedAwardIds)
        && readValue(reader, value.removedAwardIds)
        && readValue(reader, value.portraitFxRequests)
        && readValue(reader, value.spellFxRequests)
        && readValue(reader, value.pendingDialogueContext)
        && readValue(reader, value.pendingMapMove)
        && readValue(reader, value.pendingMovie)
        && readValue(reader, value.pendingInputPrompt)
        && readValue(reader, value.pendingArcomageGame)
        && readValue(reader, value.pendingSounds)
        && readValue(reader, value.lastAffectedMechanismIds)
        && readValue(reader, value.lastActivationResult)
        && readValue(reader, value.localOnLoadEventsExecuted)
        && readValue(reader, value.globalOnLoadEventsExecuted);
}

void writeValue(BinaryWriter &writer, const MapDeltaChest &value)
{
    writeValue(writer, value.chestTypeId);
    writeValue(writer, value.flags);
    writeValue(writer, value.rawItems);
    writeValue(writer, value.inventoryMatrix);
}

bool readValue(BinaryReader &reader, MapDeltaChest &value)
{
    return readValue(reader, value.chestTypeId)
        && readValue(reader, value.flags)
        && readValue(reader, value.rawItems)
        && readValue(reader, value.inventoryMatrix);
}

void writeValue(BinaryWriter &writer, const MapDeltaLocationInfo &value)
{
    writeValue(writer, value.respawnCount);
    writeValue(writer, value.lastRespawnDay);
    writeValue(writer, value.reputation);
    writeValue(writer, value.alertStatus);
    writeValue(writer, value.totalFacesCount);
    writeValue(writer, value.decorationCount);
    writeValue(writer, value.bmodelCount);
}

bool readValue(BinaryReader &reader, MapDeltaLocationInfo &value)
{
    return readValue(reader, value.respawnCount)
        && readValue(reader, value.lastRespawnDay)
        && readValue(reader, value.reputation)
        && readValue(reader, value.alertStatus)
        && readValue(reader, value.totalFacesCount)
        && readValue(reader, value.decorationCount)
        && readValue(reader, value.bmodelCount);
}

void writeValue(BinaryWriter &writer, const MapDeltaPersistentVariables &value)
{
    writeValue(writer, value.mapVars);
    writeValue(writer, value.decorVars);
}

bool readValue(BinaryReader &reader, MapDeltaPersistentVariables &value)
{
    return readValue(reader, value.mapVars)
        && readValue(reader, value.decorVars);
}

void writeValue(BinaryWriter &writer, const MapDeltaLocationTime &value)
{
    writeValue(writer, value.lastVisitTime);
    writeValue(writer, value.skyTextureName);
    writeValue(writer, value.weatherFlags);
    writeValue(writer, value.fogWeakDistance);
    writeValue(writer, value.fogStrongDistance);
    writeValue(writer, value.reserved);
}

bool readValue(BinaryReader &reader, MapDeltaLocationTime &value)
{
    return readValue(reader, value.lastVisitTime)
        && readValue(reader, value.skyTextureName)
        && readValue(reader, value.weatherFlags)
        && readValue(reader, value.fogWeakDistance)
        && readValue(reader, value.fogStrongDistance)
        && readValue(reader, value.reserved);
}

void writeValue(BinaryWriter &writer, const MapDeltaActor &value)
{
    writeValue(writer, value.name);
    writeValue(writer, value.npcId);
    writeValue(writer, value.attributes);
    writeValue(writer, value.hp);
    writeValue(writer, value.hostilityType);
    writeValue(writer, value.monsterInfoId);
    writeValue(writer, value.monsterId);
    writeValue(writer, value.radius);
    writeValue(writer, value.height);
    writeValue(writer, value.moveSpeed);
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.z);
    writeValue(writer, value.spriteIds);
    writeValue(writer, value.sectorId);
    writeValue(writer, value.currentActionAnimation);
    writeValue(writer, value.group);
    writeValue(writer, value.ally);
    writeValue(writer, value.uniqueNameIndex);
}

bool readValue(BinaryReader &reader, MapDeltaActor &value)
{
    return readValue(reader, value.name)
        && readValue(reader, value.npcId)
        && readValue(reader, value.attributes)
        && readValue(reader, value.hp)
        && readValue(reader, value.hostilityType)
        && readValue(reader, value.monsterInfoId)
        && readValue(reader, value.monsterId)
        && readValue(reader, value.radius)
        && readValue(reader, value.height)
        && readValue(reader, value.moveSpeed)
        && readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.z)
        && readValue(reader, value.spriteIds)
        && readValue(reader, value.sectorId)
        && readValue(reader, value.currentActionAnimation)
        && readValue(reader, value.group)
        && readValue(reader, value.ally)
        && readValue(reader, value.uniqueNameIndex);
}

void writeValue(BinaryWriter &writer, const MapDeltaSpriteObject &value)
{
    writeValue(writer, value.spriteId);
    writeValue(writer, value.objectDescriptionId);
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.z);
    writeValue(writer, value.velocityX);
    writeValue(writer, value.velocityY);
    writeValue(writer, value.velocityZ);
    writeValue(writer, value.yawAngle);
    writeValue(writer, value.soundId);
    writeValue(writer, value.attributes);
    writeValue(writer, value.sectorId);
    writeValue(writer, value.timeSinceCreated);
    writeValue(writer, value.temporaryLifetime);
    writeValue(writer, value.glowRadiusMultiplier);
    writeValue(writer, value.spellId);
    writeValue(writer, value.spellLevel);
    writeValue(writer, value.spellSkill);
    writeValue(writer, value.field54);
    writeValue(writer, value.spellCasterPid);
    writeValue(writer, value.spellTargetPid);
    writeValue(writer, value.lodDistance);
    writeValue(writer, value.spellCasterAbility);
    writeValue(writer, value.initialX);
    writeValue(writer, value.initialY);
    writeValue(writer, value.initialZ);
    writeValue(writer, value.rawContainingItem);
}

bool readValue(BinaryReader &reader, MapDeltaSpriteObject &value)
{
    return readValue(reader, value.spriteId)
        && readValue(reader, value.objectDescriptionId)
        && readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.z)
        && readValue(reader, value.velocityX)
        && readValue(reader, value.velocityY)
        && readValue(reader, value.velocityZ)
        && readValue(reader, value.yawAngle)
        && readValue(reader, value.soundId)
        && readValue(reader, value.attributes)
        && readValue(reader, value.sectorId)
        && readValue(reader, value.timeSinceCreated)
        && readValue(reader, value.temporaryLifetime)
        && readValue(reader, value.glowRadiusMultiplier)
        && readValue(reader, value.spellId)
        && readValue(reader, value.spellLevel)
        && readValue(reader, value.spellSkill)
        && readValue(reader, value.field54)
        && readValue(reader, value.spellCasterPid)
        && readValue(reader, value.spellTargetPid)
        && readValue(reader, value.lodDistance)
        && readValue(reader, value.spellCasterAbility)
        && readValue(reader, value.initialX)
        && readValue(reader, value.initialY)
        && readValue(reader, value.initialZ)
        && readValue(reader, value.rawContainingItem);
}

void writeValue(BinaryWriter &writer, const MapDeltaDoor &value)
{
    writeValue(writer, value.slotIndex);
    writeValue(writer, value.attributes);
    writeValue(writer, value.doorId);
    writeValue(writer, value.timeSinceTriggered);
    writeValue(writer, value.directionX);
    writeValue(writer, value.directionY);
    writeValue(writer, value.directionZ);
    writeValue(writer, value.moveLength);
    writeValue(writer, value.openSpeed);
    writeValue(writer, value.closeSpeed);
    writeValue(writer, value.numVertices);
    writeValue(writer, value.numFaces);
    writeValue(writer, value.numSectors);
    writeValue(writer, value.numOffsets);
    writeValue(writer, value.state);
    writeValue(writer, value.vertexIds);
    writeValue(writer, value.faceIds);
    writeValue(writer, value.sectorIds);
    writeValue(writer, value.deltaUs);
    writeValue(writer, value.deltaVs);
    writeValue(writer, value.xOffsets);
    writeValue(writer, value.yOffsets);
    writeValue(writer, value.zOffsets);
}

bool readValue(BinaryReader &reader, MapDeltaDoor &value)
{
    return readValue(reader, value.slotIndex)
        && readValue(reader, value.attributes)
        && readValue(reader, value.doorId)
        && readValue(reader, value.timeSinceTriggered)
        && readValue(reader, value.directionX)
        && readValue(reader, value.directionY)
        && readValue(reader, value.directionZ)
        && readValue(reader, value.moveLength)
        && readValue(reader, value.openSpeed)
        && readValue(reader, value.closeSpeed)
        && readValue(reader, value.numVertices)
        && readValue(reader, value.numFaces)
        && readValue(reader, value.numSectors)
        && readValue(reader, value.numOffsets)
        && readValue(reader, value.state)
        && readValue(reader, value.vertexIds)
        && readValue(reader, value.faceIds)
        && readValue(reader, value.sectorIds)
        && readValue(reader, value.deltaUs)
        && readValue(reader, value.deltaVs)
        && readValue(reader, value.xOffsets)
        && readValue(reader, value.yOffsets)
        && readValue(reader, value.zOffsets);
}

void writeValue(BinaryWriter &writer, const MapDeltaData &value)
{
    writeValue(writer, value.locationInfo);
    writeValue(writer, value.fullyRevealedCells);
    writeValue(writer, value.partiallyRevealedCells);
    writeValue(writer, value.visibleOutlines);
    writeValue(writer, value.faceAttributes);
    writeValue(writer, value.decorationFlags);
    writeValue(writer, value.actors);
    writeValue(writer, value.spriteObjects);
    writeValue(writer, value.chests);
    writeValue(writer, value.doorSlotCount);
    writeValue(writer, value.doors);
    writeValue(writer, value.doorsData);
    writeValue(writer, value.eventVariables);
    writeValue(writer, value.locationTime);
}

bool readValue(BinaryReader &reader, MapDeltaData &value)
{
    return readValue(reader, value.locationInfo)
        && readValue(reader, value.fullyRevealedCells)
        && readValue(reader, value.partiallyRevealedCells)
        && readValue(reader, value.visibleOutlines)
        && readValue(reader, value.faceAttributes)
        && readValue(reader, value.decorationFlags)
        && readValue(reader, value.actors)
        && readValue(reader, value.spriteObjects)
        && readValue(reader, value.chests)
        && readValue(reader, value.doorSlotCount)
        && readValue(reader, value.doors)
        && readValue(reader, value.doorsData)
        && readValue(reader, value.eventVariables)
        && readValue(reader, value.locationTime);
}

void writeValue(BinaryWriter &writer, const OutdoorWorldRuntime::TimerState &value)
{
    writeValue(writer, value.eventId);
    writeValue(writer, value.repeating);
    writeValue(writer, value.intervalGameMinutes);
    writeValue(writer, value.remainingGameMinutes);
    writeValue(writer, value.targetHour);
    writeValue(writer, value.hasFired);
}

bool readValue(BinaryReader &reader, OutdoorWorldRuntime::TimerState &value)
{
    return readValue(reader, value.eventId)
        && readValue(reader, value.repeating)
        && readValue(reader, value.intervalGameMinutes)
        && readValue(reader, value.remainingGameMinutes)
        && readValue(reader, value.targetHour)
        && readValue(reader, value.hasFired);
}

void writeValue(BinaryWriter &writer, const OutdoorWorldRuntime::MapActorState &value)
{
    writeValue(writer, value.actorId);
    writeValue(writer, value.monsterId);
    writeValue(writer, value.displayName);
    writeValue(writer, value.uniqueNameId);
    writeValue(writer, value.spawnedAtRuntime);
    writeValue(writer, value.fromSpawnPoint);
    writeValue(writer, value.spawnPointIndex);
    writeValue(writer, value.group);
    writeValue(writer, value.ally);
    writeValue(writer, value.hostilityType);
    writeValue(writer, value.specialItemId);
    writeValue(writer, value.currentHp);
    writeValue(writer, value.maxHp);
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.z);
    writeValue(writer, value.preciseX);
    writeValue(writer, value.preciseY);
    writeValue(writer, value.preciseZ);
    writeValue(writer, value.homeX);
    writeValue(writer, value.homeY);
    writeValue(writer, value.homeZ);
    writeValue(writer, value.homePreciseX);
    writeValue(writer, value.homePreciseY);
    writeValue(writer, value.homePreciseZ);
    writeValue(writer, value.radius);
    writeValue(writer, value.height);
    writeValue(writer, value.moveSpeed);
    writeValue(writer, value.spriteFrameIndex);
    writeValue(writer, value.actionSpriteFrameIndices);
    writeValue(writer, value.useStaticSpriteFrame);
    writeValue(writer, value.hostileToParty);
    writeValue(writer, value.isDead);
    writeValue(writer, value.isInvisible);
    writeValue(writer, value.hasDetectedParty);
    writeValue(writer, value.aiState);
    writeValue(writer, value.animation);
    writeValue(writer, value.animationTimeTicks);
    writeValue(writer, value.recoverySeconds);
    writeValue(writer, value.attackAnimationSeconds);
    writeValue(writer, value.attackCooldownSeconds);
    writeValue(writer, value.idleDecisionSeconds);
    writeValue(writer, value.actionSeconds);
    writeValue(writer, value.moveDirectionX);
    writeValue(writer, value.moveDirectionY);
    writeValue(writer, value.velocityX);
    writeValue(writer, value.velocityY);
    writeValue(writer, value.velocityZ);
    writeValue(writer, value.yawRadians);
    writeValue(writer, value.slowRemainingSeconds);
    writeValue(writer, value.slowMoveMultiplier);
    writeValue(writer, value.slowRecoveryMultiplier);
    writeValue(writer, value.stunRemainingSeconds);
    writeValue(writer, value.paralyzeRemainingSeconds);
    writeValue(writer, value.fearRemainingSeconds);
    writeValue(writer, value.blindRemainingSeconds);
    writeValue(writer, value.controlRemainingSeconds);
    writeValue(writer, value.controlMode);
    writeValue(writer, value.shrinkRemainingSeconds);
    writeValue(writer, value.shrinkDamageMultiplier);
    writeValue(writer, value.shrinkArmorClassMultiplier);
    writeValue(writer, value.darkGraspRemainingSeconds);
    writeValue(writer, value.idleDecisionCount);
    writeValue(writer, value.pursueDecisionCount);
    writeValue(writer, value.attackDecisionCount);
    writeValue(writer, value.attackImpactTriggered);
    writeValue(writer, value.queuedAttackAbility);
    writeValue(writer, value.movementState);
    writeValue(writer, value.movementStateInitialized);
}

bool readValue(BinaryReader &reader, OutdoorWorldRuntime::MapActorState &value)
{
    return readValue(reader, value.actorId)
        && readValue(reader, value.monsterId)
        && readValue(reader, value.displayName)
        && readValue(reader, value.uniqueNameId)
        && readValue(reader, value.spawnedAtRuntime)
        && readValue(reader, value.fromSpawnPoint)
        && readValue(reader, value.spawnPointIndex)
        && readValue(reader, value.group)
        && readValue(reader, value.ally)
        && readValue(reader, value.hostilityType)
        && readValue(reader, value.specialItemId)
        && readValue(reader, value.currentHp)
        && readValue(reader, value.maxHp)
        && readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.z)
        && readValue(reader, value.preciseX)
        && readValue(reader, value.preciseY)
        && readValue(reader, value.preciseZ)
        && readValue(reader, value.homeX)
        && readValue(reader, value.homeY)
        && readValue(reader, value.homeZ)
        && readValue(reader, value.homePreciseX)
        && readValue(reader, value.homePreciseY)
        && readValue(reader, value.homePreciseZ)
        && readValue(reader, value.radius)
        && readValue(reader, value.height)
        && readValue(reader, value.moveSpeed)
        && readValue(reader, value.spriteFrameIndex)
        && readValue(reader, value.actionSpriteFrameIndices)
        && readValue(reader, value.useStaticSpriteFrame)
        && readValue(reader, value.hostileToParty)
        && readValue(reader, value.isDead)
        && readValue(reader, value.isInvisible)
        && readValue(reader, value.hasDetectedParty)
        && readValue(reader, value.aiState)
        && readValue(reader, value.animation)
        && readValue(reader, value.animationTimeTicks)
        && readValue(reader, value.recoverySeconds)
        && readValue(reader, value.attackAnimationSeconds)
        && readValue(reader, value.attackCooldownSeconds)
        && readValue(reader, value.idleDecisionSeconds)
        && readValue(reader, value.actionSeconds)
        && readValue(reader, value.moveDirectionX)
        && readValue(reader, value.moveDirectionY)
        && readValue(reader, value.velocityX)
        && readValue(reader, value.velocityY)
        && readValue(reader, value.velocityZ)
        && readValue(reader, value.yawRadians)
        && readValue(reader, value.slowRemainingSeconds)
        && readValue(reader, value.slowMoveMultiplier)
        && readValue(reader, value.slowRecoveryMultiplier)
        && readValue(reader, value.stunRemainingSeconds)
        && readValue(reader, value.paralyzeRemainingSeconds)
        && readValue(reader, value.fearRemainingSeconds)
        && readValue(reader, value.blindRemainingSeconds)
        && readValue(reader, value.controlRemainingSeconds)
        && readValue(reader, value.controlMode)
        && readValue(reader, value.shrinkRemainingSeconds)
        && readValue(reader, value.shrinkDamageMultiplier)
        && readValue(reader, value.shrinkArmorClassMultiplier)
        && readValue(reader, value.darkGraspRemainingSeconds)
        && readValue(reader, value.idleDecisionCount)
        && readValue(reader, value.pursueDecisionCount)
        && readValue(reader, value.attackDecisionCount)
        && readValue(reader, value.attackImpactTriggered)
        && readValue(reader, value.queuedAttackAbility)
        && readValue(reader, value.movementState)
        && readValue(reader, value.movementStateInitialized);
}

void writeValue(BinaryWriter &writer, const OutdoorWorldRuntime::ChestItemState &value)
{
    writeValue(writer, value.item);
    writeValue(writer, value.itemId);
    writeValue(writer, value.quantity);
    writeValue(writer, value.goldAmount);
    writeValue(writer, value.goldRollCount);
    writeValue(writer, value.isGold);
    writeValue(writer, value.width);
    writeValue(writer, value.height);
    writeValue(writer, value.gridX);
    writeValue(writer, value.gridY);
}

bool readValue(BinaryReader &reader, OutdoorWorldRuntime::ChestItemState &value)
{
    return readValue(reader, value.item)
        && readValue(reader, value.itemId)
        && readValue(reader, value.quantity)
        && readValue(reader, value.goldAmount)
        && readValue(reader, value.goldRollCount)
        && readValue(reader, value.isGold)
        && readValue(reader, value.width)
        && readValue(reader, value.height)
        && readValue(reader, value.gridX)
        && readValue(reader, value.gridY);
}

void writeValue(BinaryWriter &writer, const OutdoorWorldRuntime::ChestViewState &value)
{
    writeValue(writer, value.chestId);
    writeValue(writer, value.chestTypeId);
    writeValue(writer, value.flags);
    writeValue(writer, value.gridWidth);
    writeValue(writer, value.gridHeight);
    writeValue(writer, value.items);
}

bool readValue(BinaryReader &reader, OutdoorWorldRuntime::ChestViewState &value)
{
    return readValue(reader, value.chestId)
        && readValue(reader, value.chestTypeId)
        && readValue(reader, value.flags)
        && readValue(reader, value.gridWidth)
        && readValue(reader, value.gridHeight)
        && readValue(reader, value.items);
}

void writeValue(BinaryWriter &writer, const OutdoorWorldRuntime::CorpseViewState &value)
{
    writeValue(writer, value.fromSummonedMonster);
    writeValue(writer, value.sourceIndex);
    writeValue(writer, value.title);
    writeValue(writer, value.items);
}

bool readValue(BinaryReader &reader, OutdoorWorldRuntime::CorpseViewState &value)
{
    return readValue(reader, value.fromSummonedMonster)
        && readValue(reader, value.sourceIndex)
        && readValue(reader, value.title)
        && readValue(reader, value.items);
}

void writeValue(BinaryWriter &writer, const OutdoorWorldRuntime::WorldItemState &value)
{
    writeValue(writer, value.worldItemId);
    writeValue(writer, value.item);
    writeValue(writer, value.goldAmount);
    writeValue(writer, value.isGold);
    writeValue(writer, value.objectDescriptionId);
    writeValue(writer, value.objectSpriteId);
    writeValue(writer, value.objectSpriteFrameIndex);
    writeValue(writer, value.objectFlags);
    writeValue(writer, value.radius);
    writeValue(writer, value.height);
    writeValue(writer, value.soundId);
    writeValue(writer, value.attributes);
    writeValue(writer, value.sectorId);
    writeValue(writer, value.objectName);
    writeValue(writer, value.objectSpriteName);
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.z);
    writeValue(writer, value.velocityX);
    writeValue(writer, value.velocityY);
    writeValue(writer, value.velocityZ);
    writeValue(writer, value.initialX);
    writeValue(writer, value.initialY);
    writeValue(writer, value.initialZ);
    writeValue(writer, value.timeSinceCreatedTicks);
    writeValue(writer, value.lifetimeTicks);
    writeValue(writer, value.spawnedByPlayer);
    writeValue(writer, value.isExpired);
}

bool readValue(BinaryReader &reader, OutdoorWorldRuntime::WorldItemState &value)
{
    return readValue(reader, value.worldItemId)
        && readValue(reader, value.item)
        && readValue(reader, value.goldAmount)
        && readValue(reader, value.isGold)
        && readValue(reader, value.objectDescriptionId)
        && readValue(reader, value.objectSpriteId)
        && readValue(reader, value.objectSpriteFrameIndex)
        && readValue(reader, value.objectFlags)
        && readValue(reader, value.radius)
        && readValue(reader, value.height)
        && readValue(reader, value.soundId)
        && readValue(reader, value.attributes)
        && readValue(reader, value.sectorId)
        && readValue(reader, value.objectName)
        && readValue(reader, value.objectSpriteName)
        && readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.z)
        && readValue(reader, value.velocityX)
        && readValue(reader, value.velocityY)
        && readValue(reader, value.velocityZ)
        && readValue(reader, value.initialX)
        && readValue(reader, value.initialY)
        && readValue(reader, value.initialZ)
        && readValue(reader, value.timeSinceCreatedTicks)
        && readValue(reader, value.lifetimeTicks)
        && readValue(reader, value.spawnedByPlayer)
        && readValue(reader, value.isExpired);
}

void writeValue(BinaryWriter &writer, const OutdoorWorldRuntime::ProjectileState &value)
{
    writeValue(writer, value.projectileId);
    writeValue(writer, value.sourceKind);
    writeValue(writer, value.sourceId);
    writeValue(writer, value.sourcePartyMemberIndex);
    writeValue(writer, value.sourceMonsterId);
    writeValue(writer, value.fromSummonedMonster);
    writeValue(writer, value.ability);
    writeValue(writer, value.objectDescriptionId);
    writeValue(writer, value.objectSpriteId);
    writeValue(writer, value.objectSpriteFrameIndex);
    writeValue(writer, value.impactObjectDescriptionId);
    writeValue(writer, value.objectFlags);
    writeValue(writer, value.radius);
    writeValue(writer, value.height);
    writeValue(writer, value.spellId);
    writeValue(writer, value.effectSoundId);
    writeValue(writer, value.skillLevel);
    writeValue(writer, value.skillMastery);
    writeValue(writer, value.objectName);
    writeValue(writer, value.objectSpriteName);
    writeValue(writer, value.sourceX);
    writeValue(writer, value.sourceY);
    writeValue(writer, value.sourceZ);
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.z);
    writeValue(writer, value.velocityX);
    writeValue(writer, value.velocityY);
    writeValue(writer, value.velocityZ);
    writeValue(writer, value.damage);
    writeValue(writer, value.attackBonus);
    writeValue(writer, value.useActorHitChance);
    writeValue(writer, value.timeSinceCreatedTicks);
    writeValue(writer, value.lifetimeTicks);
    writeValue(writer, value.isExpired);
}

bool readValue(BinaryReader &reader, OutdoorWorldRuntime::ProjectileState &value)
{
    return readValue(reader, value.projectileId)
        && readValue(reader, value.sourceKind)
        && readValue(reader, value.sourceId)
        && readValue(reader, value.sourcePartyMemberIndex)
        && readValue(reader, value.sourceMonsterId)
        && readValue(reader, value.fromSummonedMonster)
        && readValue(reader, value.ability)
        && readValue(reader, value.objectDescriptionId)
        && readValue(reader, value.objectSpriteId)
        && readValue(reader, value.objectSpriteFrameIndex)
        && readValue(reader, value.impactObjectDescriptionId)
        && readValue(reader, value.objectFlags)
        && readValue(reader, value.radius)
        && readValue(reader, value.height)
        && readValue(reader, value.spellId)
        && readValue(reader, value.effectSoundId)
        && readValue(reader, value.skillLevel)
        && readValue(reader, value.skillMastery)
        && readValue(reader, value.objectName)
        && readValue(reader, value.objectSpriteName)
        && readValue(reader, value.sourceX)
        && readValue(reader, value.sourceY)
        && readValue(reader, value.sourceZ)
        && readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.z)
        && readValue(reader, value.velocityX)
        && readValue(reader, value.velocityY)
        && readValue(reader, value.velocityZ)
        && readValue(reader, value.damage)
        && readValue(reader, value.attackBonus)
        && readValue(reader, value.useActorHitChance)
        && readValue(reader, value.timeSinceCreatedTicks)
        && readValue(reader, value.lifetimeTicks)
        && readValue(reader, value.isExpired);
}

void writeValue(BinaryWriter &writer, const OutdoorWorldRuntime::ProjectileImpactState &value)
{
    writeValue(writer, value.effectId);
    writeValue(writer, value.objectDescriptionId);
    writeValue(writer, value.objectSpriteId);
    writeValue(writer, value.objectSpriteFrameIndex);
    writeValue(writer, value.objectName);
    writeValue(writer, value.objectSpriteName);
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.z);
    writeValue(writer, value.timeSinceCreatedTicks);
    writeValue(writer, value.lifetimeTicks);
    writeValue(writer, value.isExpired);
}

bool readValue(BinaryReader &reader, OutdoorWorldRuntime::ProjectileImpactState &value)
{
    return readValue(reader, value.effectId)
        && readValue(reader, value.objectDescriptionId)
        && readValue(reader, value.objectSpriteId)
        && readValue(reader, value.objectSpriteFrameIndex)
        && readValue(reader, value.objectName)
        && readValue(reader, value.objectSpriteName)
        && readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.z)
        && readValue(reader, value.timeSinceCreatedTicks)
        && readValue(reader, value.lifetimeTicks)
        && readValue(reader, value.isExpired);
}

void writeValue(BinaryWriter &writer, const OutdoorWorldRuntime::AtmosphereState &value)
{
    writeValue(writer, value.sourceSkyTextureName);
    writeValue(writer, value.skyTextureName);
    writeValue(writer, value.weatherFlags);
    writeValue(writer, value.fogWeakDistance);
    writeValue(writer, value.fogStrongDistance);
    writeValue(writer, value.redFog);
    writeValue(writer, value.isNight);
    writeValue(writer, value.fogDensity);
    writeValue(writer, value.ambientBrightness);
    writeValue(writer, value.visibilityDistance);
    writeValue(writer, value.darknessOverlayAlpha);
    writeValue(writer, value.darknessOverlayColorAbgr);
    writeValue(writer, value.sunDirectionX);
    writeValue(writer, value.sunDirectionY);
    writeValue(writer, value.sunDirectionZ);
    writeValue(writer, value.clearColorAbgr);
}

bool readValue(BinaryReader &reader, OutdoorWorldRuntime::AtmosphereState &value)
{
    return readValue(reader, value.sourceSkyTextureName)
        && readValue(reader, value.skyTextureName)
        && readValue(reader, value.weatherFlags)
        && readValue(reader, value.fogWeakDistance)
        && readValue(reader, value.fogStrongDistance)
        && readValue(reader, value.redFog)
        && readValue(reader, value.isNight)
        && readValue(reader, value.fogDensity)
        && readValue(reader, value.ambientBrightness)
        && readValue(reader, value.visibilityDistance)
        && readValue(reader, value.darknessOverlayAlpha)
        && readValue(reader, value.darknessOverlayColorAbgr)
        && readValue(reader, value.sunDirectionX)
        && readValue(reader, value.sunDirectionY)
        && readValue(reader, value.sunDirectionZ)
        && readValue(reader, value.clearColorAbgr);
}

void writeValue(BinaryWriter &writer, const OutdoorWorldRuntime::Snapshot &value)
{
    writeValue(writer, value.gameMinutes);
    writeValue(writer, value.atmosphere);
    writeValue(writer, value.timers);
    writeValue(writer, value.mapActors);
    writeValue(writer, value.chests);
    writeValue(writer, value.openedChestFlags);
    writeValue(writer, value.materializedChestViews);
    writeValue(writer, value.activeChestView);
    writeValue(writer, value.eventRuntimeState);
    writeValue(writer, value.actorUpdateAccumulatorSeconds);
    writeValue(writer, value.sessionChestSeed);
    writeValue(writer, value.nextActorId);
    writeValue(writer, value.mapActorCorpseViews);
    writeValue(writer, value.activeCorpseView);
    writeValue(writer, value.worldItems);
    writeValue(writer, value.nextWorldItemId);
    writeValue(writer, value.nextProjectileId);
    writeValue(writer, value.nextProjectileImpactId);
    writeValue(writer, value.projectiles);
    writeValue(writer, value.projectileImpacts);
}

bool readValue(BinaryReader &reader, OutdoorWorldRuntime::Snapshot &value)
{
    return readValue(reader, value.gameMinutes)
        && readValue(reader, value.atmosphere)
        && readValue(reader, value.timers)
        && readValue(reader, value.mapActors)
        && readValue(reader, value.chests)
        && readValue(reader, value.openedChestFlags)
        && readValue(reader, value.materializedChestViews)
        && readValue(reader, value.activeChestView)
        && readValue(reader, value.eventRuntimeState)
        && readValue(reader, value.actorUpdateAccumulatorSeconds)
        && readValue(reader, value.sessionChestSeed)
        && readValue(reader, value.nextActorId)
        && readValue(reader, value.mapActorCorpseViews)
        && readValue(reader, value.activeCorpseView)
        && readValue(reader, value.worldItems)
        && readValue(reader, value.nextWorldItemId)
        && readValue(reader, value.nextProjectileId)
        && readValue(reader, value.nextProjectileImpactId)
        && readValue(reader, value.projectiles)
        && readValue(reader, value.projectileImpacts);
}

void writeValue(BinaryWriter &writer, const IndoorSceneRuntime::Snapshot &value)
{
    writeValue(writer, value.mapDeltaData);
    writeValue(writer, value.eventRuntimeState);
    writeValue(writer, value.mechanismAccumulatorMilliseconds);
}

bool readValue(BinaryReader &reader, IndoorSceneRuntime::Snapshot &value)
{
    return readValue(reader, value.mapDeltaData)
        && readValue(reader, value.eventRuntimeState)
        && readValue(reader, value.mechanismAccumulatorMilliseconds);
}

void writeValue(BinaryWriter &writer, const GameSaveData &value)
{
    writeValue(writer, value.currentSceneKind);
    writeValue(writer, value.mapFileName);
    writeValue(writer, value.party);
    writeValue(writer, value.hasOutdoorRuntimeState);
    writeValue(writer, value.outdoorParty);
    writeValue(writer, value.outdoorWorld);
    writeValue(writer, value.outdoorWorldStates);
    writeValue(writer, value.hasIndoorSceneState);
    writeValue(writer, value.indoorScene);
    writeValue(writer, value.indoorSceneStates);
    writeValue(writer, value.savedGameMinutes);
    writeValue(writer, value.outdoorCameraYawRadians);
    writeValue(writer, value.outdoorCameraPitchRadians);
    writeValue(writer, value.saveName);
    writeValue(writer, value.previewBmp);
}

bool readValue(BinaryReader &reader, GameSaveData &value)
{
    return readValue(reader, value.currentSceneKind)
        && readValue(reader, value.mapFileName)
        && readValue(reader, value.party)
        && readValue(reader, value.hasOutdoorRuntimeState)
        && readValue(reader, value.outdoorParty)
        && readValue(reader, value.outdoorWorld)
        && readValue(reader, value.outdoorWorldStates)
        && readValue(reader, value.hasIndoorSceneState)
        && readValue(reader, value.indoorScene)
        && readValue(reader, value.indoorSceneStates)
        && readValue(reader, value.savedGameMinutes)
        && readValue(reader, value.outdoorCameraYawRadians)
        && readValue(reader, value.outdoorCameraPitchRadians)
        && readValue(reader, value.saveName)
        && readValue(reader, value.previewBmp);
}
}

bool saveGameDataToPath(const std::filesystem::path &path, const GameSaveData &data, std::string &error)
{
    BinaryWriter writer;
    writer.writeBytes(SaveMagic, sizeof(SaveMagic));
    writer.write(SaveVersion);
    writer.write(data);

    std::filesystem::create_directories(path.parent_path());
    std::ofstream output(path, std::ios::binary);

    if (!output)
    {
        error = "could not open save file for writing";
        return false;
    }

    const std::vector<uint8_t> &bytes = writer.bytes();
    output.write(reinterpret_cast<const char *>(bytes.data()), static_cast<std::streamsize>(bytes.size()));

    if (!output.good())
    {
        error = "could not write save file";
        return false;
    }

    return true;
}

std::optional<GameSaveData> loadGameDataFromPath(const std::filesystem::path &path, std::string &error)
{
    std::ifstream input(path, std::ios::binary);

    if (!input)
    {
        error = "save file not found";
        return std::nullopt;
    }

    input.seekg(0, std::ios::end);
    const std::streamoff size = input.tellg();
    input.seekg(0, std::ios::beg);

    if (size <= 0)
    {
        error = "save file is empty";
        return std::nullopt;
    }

    std::vector<uint8_t> bytes(static_cast<size_t>(size));
    input.read(reinterpret_cast<char *>(bytes.data()), size);

    if (!input.good() && !input.eof())
    {
        error = "could not read save file";
        return std::nullopt;
    }

    BinaryReader reader(bytes);
    char magic[sizeof(SaveMagic)] = {};
    uint32_t version = 0;

    if (!reader.readBytes(magic, sizeof(magic))
        || std::memcmp(magic, SaveMagic, sizeof(SaveMagic)) != 0
        || !reader.read(version))
    {
        error = "invalid save header";
        return std::nullopt;
    }

    if (version != SaveVersion)
    {
        error = "unsupported save version";
        return std::nullopt;
    }

    GameSaveData data = {};
    const bool decoded = reader.read(data);

    if (!decoded || reader.failed())
    {
        error = "save data is corrupted";
        return std::nullopt;
    }

    return data;
}

bool compareSavePathsForDisplay(const std::filesystem::path &left, const std::filesystem::path &right)
{
    const int leftPriority = savePathDisplayPriority(left);
    const int rightPriority = savePathDisplayPriority(right);

    if (leftPriority != rightPriority)
    {
        return leftPriority < rightPriority;
    }

    return toLowerCopy(left.filename().string()) < toLowerCopy(right.filename().string());
}
}
