#include "game/maps/SaveGame.h"

#include "game/events/EvtEnums.h"
#include "game/tables/HouseTable.h"
#include "game/tables/ItemTable.h"

#include <algorithm>
#include <bitset>
#include <cctype>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <limits>
#include <type_traits>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
constexpr uint32_t SaveVersion = 85;
constexpr uint32_t SaveVersionAttackSpell = 19;
constexpr uint32_t SaveVersionIndoorCorpseViews = 21;
constexpr uint32_t SaveVersionIndoorChestViews = 22;
constexpr uint32_t SaveVersionIndoorActorSpellEffects = 23;
constexpr uint32_t SaveVersionIndoorActorAiStates = 24;
constexpr uint32_t SaveVersionWandCharges = 25;
constexpr uint32_t SaveVersionLloydBeaconPreview = 26;
constexpr uint32_t SaveVersionActorCarriedItem = 27;
constexpr uint32_t SaveVersionDungeonTransitionDialogue = 28;
constexpr uint32_t SaveVersionIndoorSaveLoadParity = 29;
constexpr uint32_t SaveVersionCombatEffectState = 30;
constexpr uint32_t SaveVersionGlobalNpcState = 31;
constexpr uint32_t SaveVersionInputPromptAnswers = 32;
constexpr uint32_t SaveVersionDialogueParticipantPicture = 33;
constexpr uint32_t SaveVersionOutdoorJournalRevealMask = 34;
constexpr uint32_t SaveVersionRuntimeMapNotes = 35;
constexpr uint32_t SaveVersionScopedHistory = 36;
constexpr uint32_t SaveVersionMapLuaRuntimeOverlays = 37;
constexpr uint32_t SaveVersionHiredNpcFollowers = 38;
constexpr uint32_t SaveVersionGeneratedNpcOverrides = 39;
constexpr uint32_t SaveVersionDialogueActorSource = 40;
constexpr uint32_t SaveVersionPartyHiredNpcFollowers = 41;
constexpr uint32_t SaveVersionRuntimeMapNoteMapFile = 42;
constexpr uint32_t SaveVersionPartyEverOwnedItems = 43;
constexpr uint32_t SaveVersionNamedLuaVars = 44;
constexpr uint32_t SaveVersionActorExtraItemOverrides = 45;
constexpr uint32_t SaveVersionInputPromptAnswerSteps = 46;
constexpr uint32_t SaveVersionPersistentLuaRuntimeState = 47;
constexpr uint32_t SaveVersionOutdoorModelMechanisms = 48;
constexpr uint32_t SaveVersionOutdoorActorBolsterCache = 49;
constexpr uint32_t SaveVersionGeneratedMercenaryRecruits = 50;
constexpr uint32_t SaveVersionSessionNamedGlobalVars = 51;
constexpr uint32_t SaveVersionGeneratedMercenaryNpcPicture = 52;
constexpr uint32_t SaveVersionPartyContinentReputations = 53;
constexpr uint32_t SaveVersionPartyFineGold = 54;
constexpr uint32_t SaveVersionOutdoorLocationInfo = 55;
constexpr uint32_t SaveVersionFullProjectileState = 56;
constexpr uint32_t SaveVersionCharacterConditionStartTimes = 57;
constexpr uint32_t SaveVersionHiredNpcFollowerAbilityUseDay = 58;
constexpr uint32_t SaveVersionMonsterBolsterRewards = 59;
constexpr uint32_t SaveVersionMonsterBolsterDamageDice = 60;
constexpr uint32_t SaveVersionPendingSoundNames = 61;
constexpr uint32_t SaveVersionOutdoorRuntimeSaveParity = 62;
constexpr uint32_t SaveVersionProjectileVisualMode = 63;
constexpr uint32_t SaveVersionIndoorFireSpikeTraps = 64;
constexpr uint32_t SaveVersionHeldCursorItem = 65;
constexpr uint32_t SaveVersionActorDiagnosticSource = 66;
constexpr uint32_t SaveVersionLegacyEvtTimers = 67;
constexpr uint32_t SaveVersionHiredNpcFollowerIdentity = 68;
constexpr uint32_t SaveVersionOutdoorFaceAttributes = 69;
constexpr uint32_t SaveVersionOutdoorMechanismRotationDirection = 70;
constexpr uint32_t SaveVersionMm9DialogueActors = 71;
constexpr uint32_t SaveVersionRequiredContentPackages = 72;
constexpr uint32_t SaveVersionItemWeeklyEffects = 73;
constexpr uint32_t SaveVersionMm9ActorReactions = 74;
constexpr uint32_t SaveVersionActorProceduralDeathLoot = 75;
constexpr uint32_t SaveVersionMm9ItemSourceState = 76;
constexpr uint32_t SaveVersionMm9SemanticWorldItems = 77;
constexpr uint32_t SaveVersionMm9IndoorSemanticWorldItems = 78;
constexpr uint32_t SaveVersionTimedPrimaryStatBonuses = 79;
constexpr uint32_t SaveVersionSuspendedMm9RudeVendor = 80;
constexpr uint32_t SaveVersionVendorStockGeneration = 80;
constexpr uint32_t SaveVersionOutdoorDestructibles = 81;
constexpr uint32_t SaveVersionMm9Barrels = 82;
constexpr uint32_t SaveVersionTemporaryEventBonuses = 83;
constexpr uint32_t SaveVersionConsumedCorpseMarkers = 83;
constexpr uint32_t SaveVersionIndoorCamera = 84;
// Weather comes from the game-time weather model; the outdoor rain-intensity override is no longer saved.
constexpr uint32_t SaveVersionWeatherModel = 85;
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
        if (size > remainingBytes())
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

    size_t remainingBytes() const
    {
        if (m_offset >= m_bytes.size())
        {
            return 0;
        }

        return m_bytes.size() - m_offset;
    }

    void setVersion(uint32_t version)
    {
        m_version = version;
    }

    uint32_t version() const
    {
        return m_version;
    }

private:
    const std::vector<uint8_t> &m_bytes;
    size_t m_offset = 0;
    bool m_failed = false;
    uint32_t m_version = SaveVersion;
};

void writeValue(BinaryWriter &writer, const HiredNpcFollower &value);
bool readValue(BinaryReader &reader, HiredNpcFollower &value);
void writeValue(BinaryWriter &writer, const GameplayProjectileService::Snapshot &value);
bool readValue(BinaryReader &reader, GameplayProjectileService::Snapshot &value);

bool canReadSerializedElementCount(const BinaryReader &reader, uint64_t count)
{
    if (count > std::numeric_limits<size_t>::max())
    {
        return false;
    }

    return count <= reader.remainingBytes();
}

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

    if (!canReadSerializedElementCount(reader, size))
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

    if (!canReadSerializedElementCount(reader, size))
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

    if (!canReadSerializedElementCount(reader, size))
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

    if (!canReadSerializedElementCount(reader, size))
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
    writeValue(writer, value.currentCharges);
    writeValue(writer, value.maxCharges);
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
        && (reader.version() < SaveVersionWandCharges || readValue(reader, value.currentCharges))
        && (reader.version() < SaveVersionWandCharges || readValue(reader, value.maxCharges))
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
    writeValue(writer, value.previewWidth);
    writeValue(writer, value.previewHeight);
    writeValue(writer, value.previewPixelsBgra);
}

bool readValue(BinaryReader &reader, LloydBeacon &value)
{
    return readValue(reader, value.mapName)
        && readValue(reader, value.locationName)
        && readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.z)
        && readValue(reader, value.directionDegrees)
        && readValue(reader, value.remainingSeconds)
        && (reader.version() < SaveVersionLloydBeaconPreview || readValue(reader, value.previewWidth))
        && (reader.version() < SaveVersionLloydBeaconPreview || readValue(reader, value.previewHeight))
        && (reader.version() < SaveVersionLloydBeaconPreview || readValue(reader, value.previewPixelsBgra));
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
    writeValue(writer, value.currentCharges);
    writeValue(writer, value.maxCharges);
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
        && (reader.version() < SaveVersionWandCharges || readValue(reader, value.currentCharges))
        && (reader.version() < SaveVersionWandCharges || readValue(reader, value.maxCharges))
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

void writeValue(BinaryWriter &writer, const TimedPrimaryStatBonus &value)
{
    writeValue(writer, value.power);
    writeValue(writer, value.remainingSeconds);
}

bool readValue(BinaryReader &reader, TimedPrimaryStatBonus &value)
{
    return readValue(reader, value.power)
        && readValue(reader, value.remainingSeconds);
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
    writeValue(writer, value.attackSpellName);
    writeValue(writer, value.knownSpellIds);
    writeValue(writer, value.baseResistances);
    writeValue(writer, value.permanentBonuses);
    writeValue(writer, value.temporaryEventBonuses);
    writeValue(writer, value.magicalBonuses);
    writeValue(writer, value.permanentImmunities);
    writeValue(writer, value.magicalImmunities);
    writeValue(writer, value.permanentConditionImmunities);
    writeValue(writer, value.magicalConditionImmunities);
    writeValue(writer, value.equipment);
    writeValue(writer, value.equipmentRuntime);
    writeValue(writer, value.conditions);
    writeValue(writer, value.conditionStartGameMinutes);
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
    writeValue(writer, value.timedPrimaryStatBonuses);
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
        && (reader.version() < SaveVersionAttackSpell || readValue(reader, value.attackSpellName))
        && readValue(reader, value.knownSpellIds)
        && readValue(reader, value.baseResistances)
        && readValue(reader, value.permanentBonuses)
        && (reader.version() < SaveVersionTemporaryEventBonuses
            || readValue(reader, value.temporaryEventBonuses))
        && readValue(reader, value.magicalBonuses)
        && readValue(reader, value.permanentImmunities)
        && readValue(reader, value.magicalImmunities)
        && readValue(reader, value.permanentConditionImmunities)
        && readValue(reader, value.magicalConditionImmunities)
        && readValue(reader, value.equipment)
        && readValue(reader, value.equipmentRuntime)
        && readValue(reader, value.conditions)
        && (reader.version() < SaveVersionCharacterConditionStartTimes
            || readValue(reader, value.conditionStartGameMinutes))
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
        && readValue(reader, value.inventory)
        && (reader.version() < SaveVersionTimedPrimaryStatBonuses
            || readValue(reader, value.timedPrimaryStatBonuses));
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
    writeValue(writer, value.generationVersion);
}

bool readValue(BinaryReader &reader, Party::HouseStockState &value)
{
    return readValue(reader, value.houseId)
        && readValue(reader, value.nextRefreshGameMinutes)
        && readValue(reader, value.refreshSequence)
        && readValue(reader, value.standardStock)
        && readValue(reader, value.specialStock)
        && readValue(reader, value.spellbookStock)
        && (reader.version() < SaveVersionVendorStockGeneration
            || readValue(reader, value.generationVersion));
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
    writeValue(writer, value.fineGold);
    writeValue(writer, value.waterDamageTicks);
    writeValue(writer, value.burningDamageTicks);
    writeValue(writer, value.splashCount);
    writeValue(writer, value.landingSoundCount);
    writeValue(writer, value.hardLandingSoundCount);
    writeValue(writer, value.monsterTargetSelectionCounter);
    writeValue(writer, value.houseStockSeed);
    writeValue(writer, value.itemEffectElapsedGameSeconds);
    writeValue(writer, value.itemWeeklyEffectSequence);
    writeValue(writer, value.lastFallDamageDistance);
    writeValue(writer, value.foundArtifactItems);
    writeValue(writer, value.arcomageWonHouseIds);
    writeValue(writer, value.arcomageWinCount);
    writeValue(writer, value.arcomageLossCount);
    writeValue(writer, value.houseStockStates);
    writeValue(writer, value.everOwnedItemIds);
    writeValue(writer, value.continentReputations);
    writeValue(writer, value.questBits);
    writeValue(writer, value.eventVariables);
    writeValue(writer, value.npcTopicOverrides);
    writeValue(writer, value.npcGroupNews);
    writeValue(writer, value.npcGreetingOverrides);
    writeValue(writer, value.npcGreetingDisplayCounts);
    writeValue(writer, value.npcHouseOverrides);
    writeValue(writer, value.npcItemOverrides);
    writeValue(writer, value.unavailableNpcIds);
    writeValue(writer, value.hiredNpcFollowers);
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
        && (reader.version() < SaveVersionPartyFineGold || readValue(reader, value.fineGold))
        && readValue(reader, value.waterDamageTicks)
        && readValue(reader, value.burningDamageTicks)
        && readValue(reader, value.splashCount)
        && readValue(reader, value.landingSoundCount)
        && readValue(reader, value.hardLandingSoundCount)
        && readValue(reader, value.monsterTargetSelectionCounter)
        && readValue(reader, value.houseStockSeed)
        && (reader.version() < SaveVersionItemWeeklyEffects
            || readValue(reader, value.itemEffectElapsedGameSeconds))
        && (reader.version() < SaveVersionItemWeeklyEffects
            || readValue(reader, value.itemWeeklyEffectSequence))
        && readValue(reader, value.lastFallDamageDistance)
        && readValue(reader, value.foundArtifactItems)
        && readValue(reader, value.arcomageWonHouseIds)
        && readValue(reader, value.arcomageWinCount)
        && readValue(reader, value.arcomageLossCount)
        && readValue(reader, value.houseStockStates)
        && (reader.version() < SaveVersionPartyEverOwnedItems || readValue(reader, value.everOwnedItemIds))
        && (reader.version() < SaveVersionPartyContinentReputations
            || readValue(reader, value.continentReputations))
        && readValue(reader, value.questBits)
        && readValue(reader, value.eventVariables)
        && (reader.version() < SaveVersionGlobalNpcState || readValue(reader, value.npcTopicOverrides))
        && (reader.version() < SaveVersionGlobalNpcState || readValue(reader, value.npcGroupNews))
        && (reader.version() < SaveVersionGlobalNpcState || readValue(reader, value.npcGreetingOverrides))
        && (reader.version() < SaveVersionGlobalNpcState || readValue(reader, value.npcGreetingDisplayCounts))
        && (reader.version() < SaveVersionGlobalNpcState || readValue(reader, value.npcHouseOverrides))
        && (reader.version() < SaveVersionGlobalNpcState || readValue(reader, value.npcItemOverrides))
        && (reader.version() < SaveVersionGlobalNpcState || readValue(reader, value.unavailableNpcIds))
        && (reader.version() < SaveVersionPartyHiredNpcFollowers || readValue(reader, value.hiredNpcFollowers));
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

void writeValue(BinaryWriter &writer, const IndoorMoveState &value)
{
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.footZ);
    writeValue(writer, value.eyeHeight);
    writeValue(writer, value.verticalVelocity);
    writeValue(writer, value.sectorId);
    writeValue(writer, value.eyeSectorId);
    writeValue(writer, value.supportFaceIndex);
    writeValue(writer, value.grounded);
}

bool readValue(BinaryReader &reader, IndoorMoveState &value)
{
    return readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.footZ)
        && readValue(reader, value.eyeHeight)
        && readValue(reader, value.verticalVelocity)
        && readValue(reader, value.sectorId)
        && readValue(reader, value.eyeSectorId)
        && readValue(reader, value.supportFaceIndex)
        && readValue(reader, value.grounded);
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
    value.activelyFlying = false;

    return readValue(reader, value.running)
        && readValue(reader, value.flying)
        && readValue(reader, value.featherFall)
        && readValue(reader, value.waterWalk);
}

void writeValue(BinaryWriter &writer, const IndoorPartyRuntime::Snapshot &value)
{
    writeValue(writer, value.movementState);
    writeValue(writer, value.movementAccumulatorSeconds);
    writeValue(writer, value.pendingJumpRequested);
}

bool readValue(BinaryReader &reader, IndoorPartyRuntime::Snapshot &value)
{
    return readValue(reader, value.movementState)
        && readValue(reader, value.movementAccumulatorSeconds)
        && readValue(reader, value.pendingJumpRequested);
}

void writeValue(BinaryWriter &writer, const GameplayActorSpellEffectState &value)
{
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
    writeValue(writer, value.armorClassHalvedRemainingSeconds);
    writeValue(writer, value.darkGraspRemainingSeconds);
    writeValue(writer, value.hostileToParty);
    writeValue(writer, value.hasDetectedParty);
    writeValue(writer, value.dayOfProtectionRemainingSeconds);
    writeValue(writer, value.dayOfProtectionPower);
    writeValue(writer, value.hourOfPowerRemainingSeconds);
    writeValue(writer, value.hourOfPowerPower);
    writeValue(writer, value.painReflectionRemainingSeconds);
    writeValue(writer, value.hammerhandsRemainingSeconds);
    writeValue(writer, value.hammerhandsPower);
    writeValue(writer, value.hasteRemainingSeconds);
    writeValue(writer, value.shieldRemainingSeconds);
    writeValue(writer, value.stoneskinRemainingSeconds);
    writeValue(writer, value.stoneskinPower);
    writeValue(writer, value.blessRemainingSeconds);
    writeValue(writer, value.blessPower);
    writeValue(writer, value.fateRemainingSeconds);
    writeValue(writer, value.fatePower);
    writeValue(writer, value.heroismRemainingSeconds);
    writeValue(writer, value.heroismPower);
}

bool readValue(BinaryReader &reader, GameplayActorSpellEffectState &value)
{
    return readValue(reader, value.slowRemainingSeconds)
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
        && (reader.version() < SaveVersionCombatEffectState
            || readValue(reader, value.armorClassHalvedRemainingSeconds))
        && readValue(reader, value.darkGraspRemainingSeconds)
        && readValue(reader, value.hostileToParty)
        && readValue(reader, value.hasDetectedParty)
        && (reader.version() < SaveVersionOutdoorRuntimeSaveParity
            || (readValue(reader, value.dayOfProtectionRemainingSeconds)
                && readValue(reader, value.dayOfProtectionPower)
                && readValue(reader, value.hourOfPowerRemainingSeconds)
                && readValue(reader, value.hourOfPowerPower)
                && readValue(reader, value.painReflectionRemainingSeconds)
                && readValue(reader, value.hammerhandsRemainingSeconds)
                && readValue(reader, value.hammerhandsPower)
                && readValue(reader, value.hasteRemainingSeconds)
                && readValue(reader, value.shieldRemainingSeconds)
                && readValue(reader, value.stoneskinRemainingSeconds)
                && readValue(reader, value.stoneskinPower)
                && readValue(reader, value.blessRemainingSeconds)
                && readValue(reader, value.blessPower)
                && readValue(reader, value.fateRemainingSeconds)
                && readValue(reader, value.fatePower)
                && readValue(reader, value.heroismRemainingSeconds)
                && readValue(reader, value.heroismPower)));
}

void writeValue(BinaryWriter &writer, const IndoorWorldRuntime::BloodSplatState::Vertex &value)
{
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.z);
    writeValue(writer, value.u);
    writeValue(writer, value.v);
}

bool readValue(BinaryReader &reader, IndoorWorldRuntime::BloodSplatState::Vertex &value)
{
    return readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.z)
        && readValue(reader, value.u)
        && readValue(reader, value.v);
}

void writeValue(BinaryWriter &writer, const IndoorWorldRuntime::BloodSplatState &value)
{
    writeValue(writer, value.sourceActorId);
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.z);
    writeValue(writer, value.radius);
    writeValue(writer, value.vertices);
}

bool readValue(BinaryReader &reader, IndoorWorldRuntime::BloodSplatState &value)
{
    return readValue(reader, value.sourceActorId)
        && readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.z)
        && readValue(reader, value.radius)
        && readValue(reader, value.vertices);
}

void writeValue(BinaryWriter &writer, const OutdoorWorldRuntime::BloodSplatState::Vertex &value)
{
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.z);
    writeValue(writer, value.u);
    writeValue(writer, value.v);
}

bool readValue(BinaryReader &reader, OutdoorWorldRuntime::BloodSplatState::Vertex &value)
{
    return readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.z)
        && readValue(reader, value.u)
        && readValue(reader, value.v);
}

void writeValue(BinaryWriter &writer, const OutdoorWorldRuntime::BloodSplatState &value)
{
    writeValue(writer, value.sourceActorId);
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.z);
    writeValue(writer, value.radius);
    writeValue(writer, value.vertices);
}

bool readValue(BinaryReader &reader, OutdoorWorldRuntime::BloodSplatState &value)
{
    return readValue(reader, value.sourceActorId)
        && readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.z)
        && readValue(reader, value.radius)
        && readValue(reader, value.vertices);
}

void writeValue(BinaryWriter &writer, const IndoorWorldRuntime::MapActorAiState &value)
{
    writeValue(writer, value.actorId);
    writeValue(writer, value.monsterId);
    writeValue(writer, value.displayName);
    writeValue(writer, value.hostileToParty);
    writeValue(writer, value.hasDetectedParty);
    writeValue(writer, value.bloodSplatSpawned);
    writeValue(writer, value.motionState);
    writeValue(writer, value.animationState);
    writeValue(writer, value.queuedAttackAbility);
    writeValue(writer, value.spellEffects);
    writeValue(writer, value.preciseX);
    writeValue(writer, value.preciseY);
    writeValue(writer, value.preciseZ);
    writeValue(writer, value.homePreciseX);
    writeValue(writer, value.homePreciseY);
    writeValue(writer, value.homePreciseZ);
    writeValue(writer, value.moveDirectionX);
    writeValue(writer, value.moveDirectionY);
    writeValue(writer, value.velocityX);
    writeValue(writer, value.velocityY);
    writeValue(writer, value.velocityZ);
    writeValue(writer, value.yawRadians);
    writeValue(writer, value.animationTimeTicks);
    writeValue(writer, value.recoverySeconds);
    writeValue(writer, value.attackAnimationSeconds);
    writeValue(writer, value.attackCooldownSeconds);
    writeValue(writer, value.idleDecisionSeconds);
    writeValue(writer, value.actionSeconds);
    writeValue(writer, value.idleDecisionCount);
    writeValue(writer, value.pursueDecisionCount);
    writeValue(writer, value.attackDecisionCount);
    writeValue(writer, value.attackImpactTriggered);
    writeValue(writer, value.spriteFrameIndex);
    writeValue(writer, value.actionSpriteFrameIndices);
    writeValue(writer, value.collisionRadius);
    writeValue(writer, value.collisionHeight);
    writeValue(writer, value.movementSpeed);
    writeValue(writer, value.bolsterRewardMultiplier);
    writeValue(writer, value.sectorId);
    writeValue(writer, value.eyeSectorId);
    writeValue(writer, value.supportFaceIndex);
    writeValue(writer, value.grounded);
    writeValue(writer, value.meleeAttackAnimationSeconds);
    writeValue(writer, value.rangedAttackAnimationSeconds);
    writeValue(writer, value.dyingAnimationSeconds);
    writeValue(writer, value.crowdSideLockRemainingSeconds);
    writeValue(writer, value.crowdNoProgressSeconds);
    writeValue(writer, value.crowdLastEdgeDistance);
    writeValue(writer, value.crowdRetreatRemainingSeconds);
    writeValue(writer, value.crowdStandRemainingSeconds);
    writeValue(writer, value.crowdProbeEdgeDistance);
    writeValue(writer, value.crowdProbeElapsedSeconds);
    writeValue(writer, value.crowdEscapeAttempts);
    writeValue(writer, value.crowdSideSign);
    writeValue(writer, value.suppressLowHealthFlee);
}

bool readValue(BinaryReader &reader, IndoorWorldRuntime::MapActorAiState &value)
{
    return readValue(reader, value.actorId)
        && readValue(reader, value.monsterId)
        && readValue(reader, value.displayName)
        && readValue(reader, value.hostileToParty)
        && readValue(reader, value.hasDetectedParty)
        && readValue(reader, value.bloodSplatSpawned)
        && readValue(reader, value.motionState)
        && readValue(reader, value.animationState)
        && readValue(reader, value.queuedAttackAbility)
        && readValue(reader, value.spellEffects)
        && readValue(reader, value.preciseX)
        && readValue(reader, value.preciseY)
        && readValue(reader, value.preciseZ)
        && readValue(reader, value.homePreciseX)
        && readValue(reader, value.homePreciseY)
        && readValue(reader, value.homePreciseZ)
        && readValue(reader, value.moveDirectionX)
        && readValue(reader, value.moveDirectionY)
        && readValue(reader, value.velocityX)
        && readValue(reader, value.velocityY)
        && readValue(reader, value.velocityZ)
        && readValue(reader, value.yawRadians)
        && readValue(reader, value.animationTimeTicks)
        && readValue(reader, value.recoverySeconds)
        && readValue(reader, value.attackAnimationSeconds)
        && readValue(reader, value.attackCooldownSeconds)
        && readValue(reader, value.idleDecisionSeconds)
        && readValue(reader, value.actionSeconds)
        && readValue(reader, value.idleDecisionCount)
        && readValue(reader, value.pursueDecisionCount)
        && readValue(reader, value.attackDecisionCount)
        && readValue(reader, value.attackImpactTriggered)
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.spriteFrameIndex))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.actionSpriteFrameIndices))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.collisionRadius))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.collisionHeight))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.movementSpeed))
        && (reader.version() < SaveVersionMonsterBolsterRewards || readValue(reader, value.bolsterRewardMultiplier))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.sectorId))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.eyeSectorId))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.supportFaceIndex))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.grounded))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.meleeAttackAnimationSeconds))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.rangedAttackAnimationSeconds))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.dyingAnimationSeconds))
        && (reader.version() < SaveVersionIndoorSaveLoadParity
            || readValue(reader, value.crowdSideLockRemainingSeconds))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.crowdNoProgressSeconds))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.crowdLastEdgeDistance))
        && (reader.version() < SaveVersionIndoorSaveLoadParity
            || readValue(reader, value.crowdRetreatRemainingSeconds))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.crowdStandRemainingSeconds))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.crowdProbeEdgeDistance))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.crowdProbeElapsedSeconds))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.crowdEscapeAttempts))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.crowdSideSign))
        && (reader.version() < SaveVersionOutdoorRuntimeSaveParity || readValue(reader, value.suppressLowHealthFlee));
}

void writeValue(BinaryWriter &writer, const IndoorWorldRuntime::Snapshot &value)
{
    writeValue(writer, value.gameMinutes);
    writeValue(writer, value.currentLocationReputation);
    writeValue(writer, value.sessionChestSeed);
    writeValue(writer, value.materializedChestViews);
    writeValue(writer, value.activeChestView);
    writeValue(writer, value.mapActorCorpseViews);
    writeValue(writer, value.activeCorpseView);
    writeValue(writer, value.mapActorAiStates);
    writeValue(writer, value.bloodSplats);
    writeValue(writer, value.fireSpikeTraps);
    writeValue(writer, value.actorUpdateAccumulatorSeconds);
    writeValue(writer, value.projectileState);
    writeValue(writer, value.searchedLootPropSourceIds);
}

bool readValue(BinaryReader &reader, IndoorWorldRuntime::Snapshot &value)
{
    return readValue(reader, value.gameMinutes)
        && readValue(reader, value.currentLocationReputation)
        && (reader.version() < SaveVersionIndoorChestViews || readValue(reader, value.sessionChestSeed))
        && (reader.version() < SaveVersionIndoorChestViews || readValue(reader, value.materializedChestViews))
        && (reader.version() < SaveVersionIndoorChestViews || readValue(reader, value.activeChestView))
        && (reader.version() < SaveVersionIndoorCorpseViews || readValue(reader, value.mapActorCorpseViews))
        && (reader.version() < SaveVersionIndoorCorpseViews || readValue(reader, value.activeCorpseView))
        && (reader.version() < SaveVersionIndoorActorSpellEffects
            || reader.version() >= SaveVersionIndoorActorAiStates
            || readValue(reader, value.mapActorSpellEffectStates))
        && (reader.version() < SaveVersionIndoorActorAiStates || readValue(reader, value.mapActorAiStates))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.bloodSplats))
        && (reader.version() < SaveVersionIndoorFireSpikeTraps || readValue(reader, value.fireSpikeTraps))
        && (reader.version() < SaveVersionIndoorSaveLoadParity
            || readValue(reader, value.actorUpdateAccumulatorSeconds))
        && (reader.version() < SaveVersionFullProjectileState || readValue(reader, value.projectileState))
        && (reader.version() < SaveVersionMm9ItemSourceState
            || readValue(reader, value.searchedLootPropSourceIds));
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
    writeValue(writer, value.rotationDirection);
}

bool readValue(BinaryReader &reader, RuntimeMechanismState &value)
{
    return readValue(reader, value.state)
        && readValue(reader, value.timeSinceTriggeredMs)
        && readValue(reader, value.currentDistance)
        && readValue(reader, value.isMoving)
        && (reader.version() < SaveVersionOutdoorMechanismRotationDirection
            || readValue(reader, value.rotationDirection));
}

void writeValue(BinaryWriter &writer, const RuntimeDestructibleState &value)
{
    writeValue(writer, value.hp);
    writeValue(writer, value.damageEnabled);
    writeValue(writer, value.destroyed);
}

bool readValue(BinaryReader &reader, RuntimeDestructibleState &value)
{
    return readValue(reader, value.hp)
        && readValue(reader, value.damageEnabled)
        && readValue(reader, value.destroyed);
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::OutdoorModelMechanismDefinition &value)
{
    writeValue(writer, value.mechanismId);
    writeValue(writer, value.modelName);
    writeValue(writer, value.bmodelIndex);
    writeValue(writer, value.dx);
    writeValue(writer, value.dy);
    writeValue(writer, value.dz);
    writeValue(writer, value.moveTimeMs);
    writeValue(writer, value.closed);
    writeValue(writer, value.moveParty);
}

bool readValue(BinaryReader &reader, EventRuntimeState::OutdoorModelMechanismDefinition &value)
{
    return readValue(reader, value.mechanismId)
        && readValue(reader, value.modelName)
        && readValue(reader, value.bmodelIndex)
        && readValue(reader, value.dx)
        && readValue(reader, value.dy)
        && readValue(reader, value.dz)
        && readValue(reader, value.moveTimeMs)
        && readValue(reader, value.closed)
        && readValue(reader, value.moveParty);
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

void writeValue(BinaryWriter &writer, const EventRuntimeState::PendingDialogueContext &value)
{
    writeValue(writer, value.kind);
    writeValue(writer, value.sourceId);
    writeValue(writer, value.sourceActorIndex);
    writeValue(writer, value.hostHouseId);
    writeValue(writer, value.newsId);
    writeValue(writer, value.participantPictureId);
    writeValue(writer, value.titleOverride);
    writeValue(writer, value.transitionMapMove);
    writeValue(writer, value.transitionTextId);
    writeValue(writer, value.transitionImageId);
}

bool readValue(BinaryReader &reader, EventRuntimeState::PendingDialogueContext &value)
{
    return readValue(reader, value.kind)
        && readValue(reader, value.sourceId)
        && (reader.version() < SaveVersionDialogueActorSource || readValue(reader, value.sourceActorIndex))
        && readValue(reader, value.hostHouseId)
        && readValue(reader, value.newsId)
        && (reader.version() < SaveVersionDialogueParticipantPicture
            || readValue(reader, value.participantPictureId))
        && readValue(reader, value.titleOverride)
        && (reader.version() < SaveVersionDungeonTransitionDialogue || readValue(reader, value.transitionMapMove))
        && (reader.version() < SaveVersionDungeonTransitionDialogue || readValue(reader, value.transitionTextId))
        && (reader.version() < SaveVersionDungeonTransitionDialogue || readValue(reader, value.transitionImageId));
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
    writeValue(writer, value.correctStep);
    writeValue(writer, value.textId);
    writeValue(writer, value.answerTextIds);
    writeValue(writer, value.answers);
    writeValue(writer, value.answerContinueSteps);
    writeValue(writer, value.text);
}

bool readValue(BinaryReader &reader, EventRuntimeState::PendingInputPrompt &value)
{
    return readValue(reader, value.kind)
        && readValue(reader, value.eventId)
        && readValue(reader, value.continueStep)
        && (reader.version() < SaveVersionInputPromptAnswers || readValue(reader, value.correctStep))
        && readValue(reader, value.textId)
        && (reader.version() < SaveVersionInputPromptAnswers || readValue(reader, value.answerTextIds))
        && (reader.version() < SaveVersionInputPromptAnswers || readValue(reader, value.answers))
        && (reader.version() < SaveVersionInputPromptAnswerSteps || readValue(reader, value.answerContinueSteps))
        && readValue(reader, value.text);
}

void writePendingInputPromptForSave(BinaryWriter &writer, const EventRuntimeState &value)
{
    (void)value;
    const std::optional<EventRuntimeState::PendingInputPrompt> emptyPrompt = std::nullopt;
    writeValue(writer, emptyPrompt);
}

bool readPendingInputPromptForSave(BinaryReader &reader, EventRuntimeState &value)
{
    std::optional<EventRuntimeState::PendingInputPrompt> discardedPrompt;

    if (!readValue(reader, discardedPrompt))
    {
        return false;
    }

    value.pendingInputPrompt.reset();
    return true;
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::PendingSound &value)
{
    writeValue(writer, value.soundId);
    writeValue(writer, value.soundName);
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.z);
    writeValue(writer, value.positional);
    writeValue(writer, value.hasExplicitZ);
}

bool readValue(BinaryReader &reader, EventRuntimeState::PendingSound &value)
{
    return readValue(reader, value.soundId)
        && (reader.version() < SaveVersionPendingSoundNames || readValue(reader, value.soundName))
        && readValue(reader, value.x)
        && readValue(reader, value.y)
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.z))
        && readValue(reader, value.positional)
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readValue(reader, value.hasExplicitZ));
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
    writeValue(writer, value.sourceActorIndex);
}

bool readValue(BinaryReader &reader, EventRuntimeState::DialogueOfferState &value)
{
    return readValue(reader, value.kind)
        && readValue(reader, value.npcId)
        && readValue(reader, value.topicId)
        && readValue(reader, value.messageTextId)
        && readValue(reader, value.rosterId)
        && readValue(reader, value.partyFullTextId)
        && (reader.version() < SaveVersionDialogueActorSource || readValue(reader, value.sourceActorIndex));
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::SuspendedMm9RudeDialogue &value)
{
    writeValue(writer, value.rudeId);
    writeValue(writer, value.nodeId);
    writeValue(writer, value.sourceActorIndex);
    writeValue(writer, value.response);
    writeValue(writer, value.selectionIndex);
    writeValue(writer, value.exitCallbackExecuted);
}

bool readValue(BinaryReader &reader, EventRuntimeState::SuspendedMm9RudeDialogue &value)
{
    return readValue(reader, value.rudeId)
        && readValue(reader, value.nodeId)
        && readValue(reader, value.sourceActorIndex)
        && readValue(reader, value.response)
        && readValue(reader, value.selectionIndex)
        && readValue(reader, value.exitCallbackExecuted);
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::DialogueRuntimeState &value)
{
    writeValue(writer, value.hostHouseId);
    writeValue(writer, value.menuStack);
    writeValue(writer, value.currentOffer);
    writeValue(writer, value.suspendedMm9RudeDialogue);
}

bool readValue(BinaryReader &reader, EventRuntimeState::DialogueRuntimeState &value)
{
    return readValue(reader, value.hostHouseId)
        && readValue(reader, value.menuStack)
        && readValue(reader, value.currentOffer)
        && (reader.version() < SaveVersionSuspendedMm9RudeVendor
            || readValue(reader, value.suspendedMm9RudeDialogue));
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::GeneratedMercenaryRecruit &value)
{
    writeValue(writer, value.npcId);
    writeValue(writer, value.rosterId);
    writeValue(writer, value.houseId);
    writeValue(writer, value.portraitPictureId);
    writeValue(writer, value.npcPictureId);
    writeValue(writer, value.character);
}

bool readValue(BinaryReader &reader, EventRuntimeState::GeneratedMercenaryRecruit &value)
{
    const bool loaded = readValue(reader, value.npcId)
        && readValue(reader, value.rosterId)
        && readValue(reader, value.houseId)
        && readValue(reader, value.portraitPictureId)
        && (reader.version() < SaveVersionGeneratedMercenaryNpcPicture
            || readValue(reader, value.npcPictureId))
        && readValue(reader, value.character);

    if (loaded && reader.version() < SaveVersionGeneratedMercenaryNpcPicture)
    {
        value.npcPictureId = value.portraitPictureId;
    }

    return loaded;
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

void writeValue(BinaryWriter &writer, const EventRuntimeState::RuntimeMapNote &value)
{
    writeValue(writer, value.id);
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.mapFileName);
    writeValue(writer, value.text);
    writeValue(writer, value.active);
}

bool readValue(BinaryReader &reader, EventRuntimeState::RuntimeMapNote &value)
{
    if (!readValue(reader, value.id)
        || !readValue(reader, value.x)
        || !readValue(reader, value.y))
    {
        return false;
    }

    if (reader.version() >= SaveVersionRuntimeMapNoteMapFile)
    {
        if (!readValue(reader, value.mapFileName))
        {
            return false;
        }
    }
    else
    {
        value.mapFileName.clear();
    }

    return readValue(reader, value.text)
        && readValue(reader, value.active);
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::ChestItemRequest &value)
{
    writeValue(writer, value.itemId);
    writeValue(writer, value.gridX);
    writeValue(writer, value.gridY);
}

bool readValue(BinaryReader &reader, EventRuntimeState::ChestItemRequest &value)
{
    return readValue(reader, value.itemId)
        && readValue(reader, value.gridX)
        && readValue(reader, value.gridY);
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::HiredNpcFollower &value)
{
    writeValue(writer, value.npcId);
    writeValue(writer, value.professionId);
    writeValue(writer, value.weeklyCost);
    writeValue(writer, value.abilityUsedDay);
    writeValue(writer, value.name);
    writeValue(writer, value.pictureId);
}

bool readValue(BinaryReader &reader, EventRuntimeState::HiredNpcFollower &value)
{
    return readValue(reader, value.npcId)
        && readValue(reader, value.professionId)
        && readValue(reader, value.weeklyCost)
        && (reader.version() < SaveVersionHiredNpcFollowerAbilityUseDay || readValue(reader, value.abilityUsedDay))
        && (reader.version() < SaveVersionHiredNpcFollowerIdentity || readValue(reader, value.name))
        && (reader.version() < SaveVersionHiredNpcFollowerIdentity || readValue(reader, value.pictureId));
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::SavedLocation &value)
{
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.z);
    writeValue(writer, value.continentId);
    writeValue(writer, value.mapName);
}

bool readValue(BinaryReader &reader, EventRuntimeState::SavedLocation &value)
{
    return readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.z)
        && readValue(reader, value.continentId)
        && readValue(reader, value.mapName);
}

void writeValue(BinaryWriter &writer, const EventRuntimeState::TransportRouteOverride &value)
{
    writeValue(writer, value.houseId);
    writeValue(writer, value.routeIndex);
    writeValue(writer, value.destinationName);
    writeValue(writer, value.mapFileName);
    writeValue(writer, value.daysAvailable);
    writeValue(writer, value.travelDays);
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.z);
    writeValue(writer, value.directionDegrees);
    writeValue(writer, value.requiredQBit);
    writeValue(writer, value.useMapStartPosition);
}

bool readValue(BinaryReader &reader, EventRuntimeState::TransportRouteOverride &value)
{
    return readValue(reader, value.houseId)
        && readValue(reader, value.routeIndex)
        && readValue(reader, value.destinationName)
        && readValue(reader, value.mapFileName)
        && readValue(reader, value.daysAvailable)
        && readValue(reader, value.travelDays)
        && readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.z)
        && readValue(reader, value.directionDegrees)
        && readValue(reader, value.requiredQBit)
        && readValue(reader, value.useMapStartPosition);
}

void writeValue(BinaryWriter &writer, const EventRuntimeState &value)
{
    writeValue(writer, value.variables);
    writeValue(writer, value.namedMapVars);
    writeValue(writer, value.namedGlobalVars);
    writeValue(writer, value.runtimeMapNotes);
    writeValue(writer, value.savedLocations);
    writeValue(writer, value.transportRouteOverrides);
    writeValue(writer, value.activeHistoryContinentId);
    writeValue(writer, value.historyEventTimes);
    writeValue(writer, value.historyEventTimesByContinent);
    writeValue(writer, value.mapVars);
    writeValue(writer, value.currentLocationReputation);
    writeValue(writer, value.facetSetMasks);
    writeValue(writer, value.facetClearMasks);
    writeValue(writer, value.mechanisms);
    writeValue(writer, value.destructibles);
    writeValue(writer, value.outdoorModelMechanisms);
    writeValue(writer, value.textureOverrides);
    writeValue(writer, value.outdoorModelFacetTextureOverrides);
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
    writeValue(writer, value.npcNameOverrides);
    writeValue(writer, value.npcPictureOverrides);
    writeValue(writer, value.npcProfessionOverrides);
    writeValue(writer, value.generatedNpcIdsByActorKey);
    writeValue(writer, value.generatedMercenaryRecruitsByNpcId);
    writeValue(writer, value.npcItemOverrides);
    writeValue(writer, value.actorItemOverrides);
    writeValue(writer, value.actorExtraItemOverrides);
    writeValue(writer, value.monsterRelationOverrides);
    writeValue(writer, value.chestItemRequests);
    writeValue(writer, value.unavailableNpcIds);
    writeValue(writer, value.hiredNpcFollowers);
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
    writePendingInputPromptForSave(writer, value);
    writeValue(writer, value.pendingArcomageGame);
    writeValue(writer, value.pendingSounds);
    writeValue(writer, value.lastAffectedMechanismIds);
    writeValue(writer, value.lastActivationResult);
    writeValue(writer, value.localOnLoadEventsExecuted);
    writeValue(writer, value.globalOnLoadEventsExecuted);
    writeValue(writer, value.processedMapRespawnCount);
}

bool readValue(BinaryReader &reader, EventRuntimeState &value)
{
    const bool ok = readValue(reader, value.variables)
        && (reader.version() < SaveVersionNamedLuaVars || readValue(reader, value.namedMapVars))
        && (reader.version() < SaveVersionNamedLuaVars || readValue(reader, value.namedGlobalVars))
        && (reader.version() < SaveVersionRuntimeMapNotes || readValue(reader, value.runtimeMapNotes))
        && (reader.version() < SaveVersionPersistentLuaRuntimeState || readValue(reader, value.savedLocations))
        && (reader.version() < SaveVersionPersistentLuaRuntimeState || readValue(reader, value.transportRouteOverrides))
        && (reader.version() < SaveVersionScopedHistory || readValue(reader, value.activeHistoryContinentId))
        && readValue(reader, value.historyEventTimes)
        && (reader.version() < SaveVersionScopedHistory || readValue(reader, value.historyEventTimesByContinent))
        && readValue(reader, value.mapVars)
        && (reader.version() < SaveVersionPartyContinentReputations
            || readValue(reader, value.currentLocationReputation))
        && readValue(reader, value.facetSetMasks)
        && readValue(reader, value.facetClearMasks)
        && readValue(reader, value.mechanisms)
        && (reader.version() < SaveVersionOutdoorDestructibles
            || readValue(reader, value.destructibles))
        && (reader.version() < SaveVersionOutdoorModelMechanisms
            || readValue(reader, value.outdoorModelMechanisms))
        && readValue(reader, value.textureOverrides)
        && (reader.version() < SaveVersionMapLuaRuntimeOverlays
            || readValue(reader, value.outdoorModelFacetTextureOverrides))
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
        && (reader.version() < SaveVersionGeneratedNpcOverrides || readValue(reader, value.npcNameOverrides))
        && (reader.version() < SaveVersionGeneratedNpcOverrides || readValue(reader, value.npcPictureOverrides))
        && (reader.version() < SaveVersionGeneratedNpcOverrides || readValue(reader, value.npcProfessionOverrides))
        && (reader.version() < SaveVersionGeneratedNpcOverrides || readValue(reader, value.generatedNpcIdsByActorKey))
        && (reader.version() < SaveVersionGeneratedMercenaryRecruits
            || readValue(reader, value.generatedMercenaryRecruitsByNpcId))
        && readValue(reader, value.npcItemOverrides)
        && readValue(reader, value.actorItemOverrides)
        && (reader.version() < SaveVersionActorExtraItemOverrides
            || readValue(reader, value.actorExtraItemOverrides))
        && (reader.version() < SaveVersionMapLuaRuntimeOverlays || readValue(reader, value.monsterRelationOverrides))
        && (reader.version() < SaveVersionMapLuaRuntimeOverlays || readValue(reader, value.chestItemRequests))
        && readValue(reader, value.unavailableNpcIds)
        && (reader.version() < SaveVersionHiredNpcFollowers || readValue(reader, value.hiredNpcFollowers))
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
        && readPendingInputPromptForSave(reader, value)
        && readValue(reader, value.pendingArcomageGame)
        && readValue(reader, value.pendingSounds)
        && readValue(reader, value.lastAffectedMechanismIds)
        && readValue(reader, value.lastActivationResult)
        && readValue(reader, value.localOnLoadEventsExecuted)
        && readValue(reader, value.globalOnLoadEventsExecuted)
        && (reader.version() < SaveVersionActorExtraItemOverrides
            || readValue(reader, value.processedMapRespawnCount));

    if (!ok)
    {
        return false;
    }

    value.activeHistoryContinentId = normalizedHistoryContinentId(value.activeHistoryContinentId);

    if (value.historyEventTimesByContinent.empty() && !value.historyEventTimes.empty())
    {
        value.historyEventTimesByContinent[1u] = value.historyEventTimes;
    }

    return true;
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
    writeValue(writer, value.carriedItemId);
    writeValue(writer, value.group);
    writeValue(writer, value.ally);
    writeValue(writer, value.uniqueNameIndex);
    writeValue(writer, value.bolsterRewardMultiplier);
    const uint64_t diagnosticSourceActorIndex =
        value.diagnosticSourceActorIndex != static_cast<size_t>(-1)
            ? static_cast<uint64_t>(value.diagnosticSourceActorIndex)
            : std::numeric_limits<uint64_t>::max();
    writeValue(writer, diagnosticSourceActorIndex);
    writeValue(writer, value.mm9RudeId);
    writeValue(writer, value.mm9SourceObjectIndex);
    writeValue(writer, value.initialYawUnits);
    writeValue(writer, value.immobile);
    writeValue(writer, value.mm9CanReceiveDamage);
    writeValue(writer, value.mm9Civilian);
    writeValue(writer, value.mm9Guard);
    writeValue(writer, value.proceduralDeathLoot);
}

bool readValue(BinaryReader &reader, MapDeltaActor &value)
{
    if (!(readValue(reader, value.name)
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
        && (reader.version() < SaveVersionActorCarriedItem || readValue(reader, value.carriedItemId))
        && readValue(reader, value.group)
        && readValue(reader, value.ally)
        && readValue(reader, value.uniqueNameIndex)
        && (reader.version() < SaveVersionMonsterBolsterRewards || readValue(reader, value.bolsterRewardMultiplier))))
    {
        return false;
    }

    if (reader.version() >= SaveVersionActorDiagnosticSource)
    {
        uint64_t diagnosticSourceActorIndex = std::numeric_limits<uint64_t>::max();

        if (!readValue(reader, diagnosticSourceActorIndex))
        {
            return false;
        }

        value.diagnosticSourceActorIndex = static_cast<size_t>(-1);

        if (diagnosticSourceActorIndex != std::numeric_limits<uint64_t>::max()
            && diagnosticSourceActorIndex <= static_cast<uint64_t>(std::numeric_limits<size_t>::max()))
        {
            value.diagnosticSourceActorIndex = static_cast<size_t>(diagnosticSourceActorIndex);
        }
    }

    if (reader.version() >= SaveVersionMm9DialogueActors
        && (!readValue(reader, value.mm9RudeId)
            || !readValue(reader, value.mm9SourceObjectIndex)
            || !readValue(reader, value.initialYawUnits)
            || !readValue(reader, value.immobile)))
    {
        return false;
    }

    if (reader.version() >= SaveVersionMm9ActorReactions
        && (!readValue(reader, value.mm9CanReceiveDamage)
            || !readValue(reader, value.mm9Civilian)
            || !readValue(reader, value.mm9Guard)))
    {
        return false;
    }

    if (reader.version() >= SaveVersionActorProceduralDeathLoot
        && !readValue(reader, value.proceduralDeathLoot))
    {
        return false;
    }

    return true;
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
    writeValue(writer, value.semanticSourceId);
    writeValue(writer, value.semanticLootContainerId);
    writeValue(writer, value.semanticPlacedPickup);
    writeValue(writer, value.semanticLootContainer);
    writeValue(writer, value.semanticPolicyHidden);
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
        && readValue(reader, value.rawContainingItem)
        && (reader.version() < SaveVersionMm9IndoorSemanticWorldItems
            || (readValue(reader, value.semanticSourceId)
                && readValue(reader, value.semanticLootContainerId)
                && readValue(reader, value.semanticPlacedPickup)
                && readValue(reader, value.semanticLootContainer)
                && readValue(reader, value.semanticPolicyHidden)));
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

void writeValue(BinaryWriter &writer, const MapDeltaMm9BarrelState &value)
{
    writeValue(writer, value.sourceObjectIndex);
    writeValue(writer, value.type);
    writeValue(writer, value.used);
}

bool readValue(BinaryReader &reader, MapDeltaMm9BarrelState &value)
{
    uint8_t rawType = 0;
    if (!readValue(reader, value.sourceObjectIndex)
        || !readValue(reader, rawType)
        || !readValue(reader, value.used)
        || rawType < static_cast<uint8_t>(Mm9BarrelType::RedMight)
        || rawType > static_cast<uint8_t>(Mm9BarrelType::Water))
    {
        return false;
    }
    value.type = static_cast<Mm9BarrelType>(rawType);
    return true;
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
    writeValue(writer, value.mm9Barrels);
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
        && readValue(reader, value.locationTime)
        && (reader.version() < SaveVersionMm9Barrels || readValue(reader, value.mm9Barrels));
}

void writeValue(BinaryWriter &writer, const ScriptedEventTimerDefinition &value)
{
    writeValue(writer, value.scope);
    writeValue(writer, value.origin);
    writeValue(writer, value.triggerKind);
    writeValue(writer, value.scheduleKind);
    writeValue(writer, value.eventId);
    writeValue(writer, value.sourceEventId);
    writeValue(writer, value.triggerStep);
    writeValue(writer, value.registrationIndex);
    writeValue(writer, value.repeating);
    writeValue(writer, value.intervalHalfMinutes);
    writeValue(writer, value.startHour);
    writeValue(writer, value.startMinute);
    writeValue(writer, value.startSecond);
    writeValue(writer, value.intervalGameMinutes);
    writeValue(writer, value.initialDelayGameMinutes);
}

bool readValue(BinaryReader &reader, ScriptedEventTimerDefinition &value)
{
    return readValue(reader, value.scope)
        && readValue(reader, value.origin)
        && readValue(reader, value.triggerKind)
        && readValue(reader, value.scheduleKind)
        && readValue(reader, value.eventId)
        && readValue(reader, value.sourceEventId)
        && readValue(reader, value.triggerStep)
        && readValue(reader, value.registrationIndex)
        && readValue(reader, value.repeating)
        && readValue(reader, value.intervalHalfMinutes)
        && readValue(reader, value.startHour)
        && readValue(reader, value.startMinute)
        && readValue(reader, value.startSecond)
        && readValue(reader, value.intervalGameMinutes)
        && readValue(reader, value.initialDelayGameMinutes);
}

void writeValue(BinaryWriter &writer, const ScriptedEventTimerState &value)
{
    writeValue(writer, value.definition);
    writeValue(writer, value.nextAlarmGameMinutes);
    writeValue(writer, value.eligibleGameMinutes);
    writeValue(writer, value.hasFired);
    writeValue(writer, value.initialCalendarFirePending);
    writeValue(writer, value.migratedFromLegacySave);
    writeValue(writer, value.migratedRemainingGameMinutes);
}

bool readValue(BinaryReader &reader, ScriptedEventTimerState &value)
{
    return readValue(reader, value.definition)
        && readValue(reader, value.nextAlarmGameMinutes)
        && readValue(reader, value.eligibleGameMinutes)
        && readValue(reader, value.hasFired)
        && readValue(reader, value.initialCalendarFirePending)
        && readValue(reader, value.migratedFromLegacySave)
        && readValue(reader, value.migratedRemainingGameMinutes);
}

struct LegacyOutdoorTimerState
{
    uint16_t eventId = 0;
    bool repeating = false;
    float intervalGameMinutes = 0.0f;
    float remainingGameMinutes = 0.0f;
    std::optional<int> targetHour;
    bool hasFired = false;
};

bool readValue(BinaryReader &reader, LegacyOutdoorTimerState &value)
{
    return readValue(reader, value.eventId)
        && readValue(reader, value.repeating)
        && readValue(reader, value.intervalGameMinutes)
        && readValue(reader, value.remainingGameMinutes)
        && readValue(reader, value.targetHour)
        && readValue(reader, value.hasFired);
}

struct LegacyIndoorTimerState
{
    uint16_t eventId = 0;
    bool repeating = false;
    int targetHour = 0;
    float intervalGameMinutes = 0.0f;
    float remainingGameMinutes = 0.0f;
    bool hasFired = false;
};

bool readValue(BinaryReader &reader, LegacyIndoorTimerState &value)
{
    return readValue(reader, value.eventId)
        && readValue(reader, value.repeating)
        && readValue(reader, value.targetHour)
        && readValue(reader, value.intervalGameMinutes)
        && readValue(reader, value.remainingGameMinutes)
        && readValue(reader, value.hasFired);
}

ScriptedEventTimerState migrateLegacyTimerState(
    uint16_t eventId,
    bool repeating,
    float intervalGameMinutes,
    float remainingGameMinutes,
    bool hasFired,
    uint32_t registrationIndex)
{
    ScriptedEventTimerState state = {};
    state.definition.scope = ScriptedEventScope::Map;
    state.definition.origin = ScriptedEventTimerOrigin::Native;
    state.definition.scheduleKind = ScriptedEventTimerScheduleKind::Relative;
    state.definition.eventId = eventId;
    state.definition.sourceEventId = eventId;
    state.definition.registrationIndex = registrationIndex;
    state.definition.repeating = repeating;
    state.definition.intervalGameMinutes = intervalGameMinutes;
    state.hasFired = hasFired;
    state.migratedFromLegacySave = true;
    state.migratedRemainingGameMinutes = remainingGameMinutes;
    return state;
}

bool readOutdoorTimerStates(BinaryReader &reader, std::vector<ScriptedEventTimerState> &values)
{
    if (reader.version() >= SaveVersionLegacyEvtTimers)
    {
        return readValue(reader, values);
    }

    std::vector<LegacyOutdoorTimerState> legacyValues;
    if (!readValue(reader, legacyValues))
    {
        return false;
    }

    values.clear();
    values.reserve(legacyValues.size());

    for (size_t index = 0; index < legacyValues.size(); ++index)
    {
        const LegacyOutdoorTimerState &legacyValue = legacyValues[index];
        values.push_back(migrateLegacyTimerState(
            legacyValue.eventId,
            legacyValue.repeating,
            legacyValue.intervalGameMinutes,
            legacyValue.remainingGameMinutes,
            legacyValue.hasFired,
            static_cast<uint32_t>(index + 1)));
    }

    return true;
}

bool readIndoorTimerStates(BinaryReader &reader, std::vector<ScriptedEventTimerState> &values)
{
    if (reader.version() >= SaveVersionLegacyEvtTimers)
    {
        return readValue(reader, values);
    }

    std::vector<LegacyIndoorTimerState> legacyValues;
    if (!readValue(reader, legacyValues))
    {
        return false;
    }

    values.clear();
    values.reserve(legacyValues.size());

    for (size_t index = 0; index < legacyValues.size(); ++index)
    {
        const LegacyIndoorTimerState &legacyValue = legacyValues[index];
        values.push_back(migrateLegacyTimerState(
            legacyValue.eventId,
            legacyValue.repeating,
            legacyValue.intervalGameMinutes,
            legacyValue.remainingGameMinutes,
            legacyValue.hasFired,
            static_cast<uint32_t>(index + 1)));
    }

    return true;
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
    writeValue(writer, value.bolsterRewardMultiplier);
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
    writeValue(writer, value.armorClass);
    writeValue(writer, value.immobile);
    writeValue(writer, value.attack1DamageDiceRolls);
    writeValue(writer, value.attack1DamageDiceSides);
    writeValue(writer, value.attack1DamageBonus);
    writeValue(writer, value.attack2DamageDiceRolls);
    writeValue(writer, value.attack2DamageDiceSides);
    writeValue(writer, value.attack2DamageBonus);
    writeValue(writer, value.spell1SkillLevel);
    writeValue(writer, value.spell1SkillMastery);
    writeValue(writer, value.spell2SkillLevel);
    writeValue(writer, value.spell2SkillMastery);
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
    writeValue(writer, value.armorClassHalvedRemainingSeconds);
    writeValue(writer, value.darkGraspRemainingSeconds);
    writeValue(writer, value.idleDecisionCount);
    writeValue(writer, value.pursueDecisionCount);
    writeValue(writer, value.attackDecisionCount);
    writeValue(writer, value.attackImpactTriggered);
    writeValue(writer, value.queuedAttackAbility);
    writeValue(writer, value.movementState);
    writeValue(writer, value.movementStateInitialized);
    writeValue(writer, value.npcId);
    writeValue(writer, value.aiType);
    writeValue(writer, value.canFly);
    writeValue(writer, value.attack1DamageType);
    writeValue(writer, value.attack2DamageType);
    writeValue(writer, value.spell1Id);
    writeValue(writer, value.spell1DamageType);
    writeValue(writer, value.spell1CastSupported);
    writeValue(writer, value.spell2Id);
    writeValue(writer, value.spell2DamageType);
    writeValue(writer, value.spell2CastSupported);
    writeValue(writer, value.wanderRadius);
    writeValue(writer, value.generatedAttack2);
    writeValue(writer, value.generatedAttack2IsRanged);
    writeValue(writer, value.copyAttack1DamageToAttack2);
    writeValue(writer, value.generatedAttack2MissileType);
    writeValue(writer, value.generatedAttack2Chance);
    writeValue(writer, value.generatedSpell1UseChance);
    writeValue(writer, value.generatedSpell2UseChance);
    writeValue(writer, value.alertStatusBit);
    writeValue(writer, value.bloodSplatSpawned);
    writeValue(writer, value.dayOfProtectionRemainingSeconds);
    writeValue(writer, value.dayOfProtectionPower);
    writeValue(writer, value.hourOfPowerRemainingSeconds);
    writeValue(writer, value.hourOfPowerPower);
    writeValue(writer, value.painReflectionRemainingSeconds);
    writeValue(writer, value.hammerhandsRemainingSeconds);
    writeValue(writer, value.hammerhandsPower);
    writeValue(writer, value.hasteRemainingSeconds);
    writeValue(writer, value.shieldRemainingSeconds);
    writeValue(writer, value.stoneskinRemainingSeconds);
    writeValue(writer, value.stoneskinPower);
    writeValue(writer, value.blessRemainingSeconds);
    writeValue(writer, value.blessPower);
    writeValue(writer, value.fateRemainingSeconds);
    writeValue(writer, value.fatePower);
    writeValue(writer, value.heroismRemainingSeconds);
    writeValue(writer, value.heroismPower);
    writeValue(writer, value.crowdSideLockRemainingSeconds);
    writeValue(writer, value.crowdNoProgressSeconds);
    writeValue(writer, value.crowdLastEdgeDistance);
    writeValue(writer, value.crowdRetreatRemainingSeconds);
    writeValue(writer, value.crowdStandRemainingSeconds);
    writeValue(writer, value.crowdProbeX);
    writeValue(writer, value.crowdProbeY);
    writeValue(writer, value.crowdProbeEdgeDistance);
    writeValue(writer, value.crowdProbeElapsedSeconds);
    writeValue(writer, value.crowdEscapeAttempts);
    writeValue(writer, value.crowdSideSign);
    writeValue(writer, value.suppressLowHealthFlee);
    writeValue(writer, value.mm9RudeId);
    writeValue(writer, value.usesMm9ActorRules);
    writeValue(writer, value.canReceiveDamage);
    writeValue(writer, value.mm9Civilian);
    writeValue(writer, value.mm9Guard);
    writeValue(writer, value.mm9FleeingFromParty);
    writeValue(writer, value.mm9FleeRemainingSeconds);
    writeValue(writer, value.mm9HelpCooldownSeconds);
    writeValue(writer, value.mm9PlayerHitCount);
    writeValue(writer, value.proceduralDeathLoot);
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
        && (reader.version() < SaveVersionMonsterBolsterRewards || readValue(reader, value.bolsterRewardMultiplier))
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
        && (reader.version() < SaveVersionOutdoorActorBolsterCache
            || (readValue(reader, value.armorClass)
                && readValue(reader, value.immobile)
                && (reader.version() < SaveVersionMonsterBolsterDamageDice
                    || (readValue(reader, value.attack1DamageDiceRolls)
                        && readValue(reader, value.attack1DamageDiceSides)))
                && readValue(reader, value.attack1DamageBonus)
                && (reader.version() < SaveVersionMonsterBolsterDamageDice
                    || (readValue(reader, value.attack2DamageDiceRolls)
                        && readValue(reader, value.attack2DamageDiceSides)))
                && readValue(reader, value.attack2DamageBonus)
                && readValue(reader, value.spell1SkillLevel)
                && readValue(reader, value.spell1SkillMastery)
                && readValue(reader, value.spell2SkillLevel)
                && readValue(reader, value.spell2SkillMastery)))
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
        && (reader.version() < SaveVersionCombatEffectState
            || readValue(reader, value.armorClassHalvedRemainingSeconds))
        && readValue(reader, value.darkGraspRemainingSeconds)
        && readValue(reader, value.idleDecisionCount)
        && readValue(reader, value.pursueDecisionCount)
        && readValue(reader, value.attackDecisionCount)
        && readValue(reader, value.attackImpactTriggered)
        && readValue(reader, value.queuedAttackAbility)
        && readValue(reader, value.movementState)
        && readValue(reader, value.movementStateInitialized)
        && (reader.version() < SaveVersionOutdoorRuntimeSaveParity
            || (readValue(reader, value.npcId)
                && readValue(reader, value.aiType)
                && readValue(reader, value.canFly)
                && readValue(reader, value.attack1DamageType)
                && readValue(reader, value.attack2DamageType)
                && readValue(reader, value.spell1Id)
                && readValue(reader, value.spell1DamageType)
                && readValue(reader, value.spell1CastSupported)
                && readValue(reader, value.spell2Id)
                && readValue(reader, value.spell2DamageType)
                && readValue(reader, value.spell2CastSupported)
                && readValue(reader, value.wanderRadius)
                && readValue(reader, value.generatedAttack2)
                && readValue(reader, value.generatedAttack2IsRanged)
                && readValue(reader, value.copyAttack1DamageToAttack2)
                && readValue(reader, value.generatedAttack2MissileType)
                && readValue(reader, value.generatedAttack2Chance)
                && readValue(reader, value.generatedSpell1UseChance)
                && readValue(reader, value.generatedSpell2UseChance)
                && readValue(reader, value.alertStatusBit)
                && readValue(reader, value.bloodSplatSpawned)
                && readValue(reader, value.dayOfProtectionRemainingSeconds)
                && readValue(reader, value.dayOfProtectionPower)
                && readValue(reader, value.hourOfPowerRemainingSeconds)
                && readValue(reader, value.hourOfPowerPower)
                && readValue(reader, value.painReflectionRemainingSeconds)
                && readValue(reader, value.hammerhandsRemainingSeconds)
                && readValue(reader, value.hammerhandsPower)
                && readValue(reader, value.hasteRemainingSeconds)
                && readValue(reader, value.shieldRemainingSeconds)
                && readValue(reader, value.stoneskinRemainingSeconds)
                && readValue(reader, value.stoneskinPower)
                && readValue(reader, value.blessRemainingSeconds)
                && readValue(reader, value.blessPower)
                && readValue(reader, value.fateRemainingSeconds)
                && readValue(reader, value.fatePower)
                && readValue(reader, value.heroismRemainingSeconds)
                && readValue(reader, value.heroismPower)
                && readValue(reader, value.crowdSideLockRemainingSeconds)
                && readValue(reader, value.crowdNoProgressSeconds)
                && readValue(reader, value.crowdLastEdgeDistance)
                && readValue(reader, value.crowdRetreatRemainingSeconds)
                && readValue(reader, value.crowdStandRemainingSeconds)
                && readValue(reader, value.crowdProbeX)
                && readValue(reader, value.crowdProbeY)
                && readValue(reader, value.crowdProbeEdgeDistance)
                && readValue(reader, value.crowdProbeElapsedSeconds)
                && readValue(reader, value.crowdEscapeAttempts)
                && readValue(reader, value.crowdSideSign)
                && readValue(reader, value.suppressLowHealthFlee)))
        && (reader.version() < SaveVersionMm9DialogueActors || readValue(reader, value.mm9RudeId))
        && (reader.version() < SaveVersionMm9ActorReactions
            || (readValue(reader, value.usesMm9ActorRules)
                && readValue(reader, value.canReceiveDamage)
                && readValue(reader, value.mm9Civilian)
                && readValue(reader, value.mm9Guard)
                && readValue(reader, value.mm9FleeingFromParty)
                && readValue(reader, value.mm9FleeRemainingSeconds)
                && readValue(reader, value.mm9HelpCooldownSeconds)
                && readValue(reader, value.mm9PlayerHitCount)))
        && (reader.version() < SaveVersionActorProceduralDeathLoot
            || readValue(reader, value.proceduralDeathLoot));
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
    writeValue(writer, value.hiddenItems);
}

bool readValue(BinaryReader &reader, OutdoorWorldRuntime::ChestViewState &value)
{
    return readValue(reader, value.chestId)
        && readValue(reader, value.chestTypeId)
        && readValue(reader, value.flags)
        && readValue(reader, value.gridWidth)
        && readValue(reader, value.gridHeight)
        && readValue(reader, value.items)
        && readValue(reader, value.hiddenItems);
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
    writeValue(writer, value.semanticSourceId);
    writeValue(writer, value.semanticPlacedPickup);
    writeValue(writer, value.semanticLootContainerId);
    writeValue(writer, value.semanticLootContainer);
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
        && readValue(reader, value.isExpired)
        && (reader.version() < SaveVersionMm9SemanticWorldItems
            || (readValue(reader, value.semanticSourceId)
                && readValue(reader, value.semanticPlacedPickup)
                && readValue(reader, value.semanticLootContainerId)
                && readValue(reader, value.semanticLootContainer)));
}

void writeValue(BinaryWriter &writer, const OutdoorWorldRuntime::ArmageddonState &value)
{
    writeValue(writer, value.remainingSeconds);
    writeValue(writer, value.skillLevel);
    writeValue(writer, value.skillMastery);
    writeValue(writer, value.casterMemberIndex);
    writeValue(writer, value.shakeStepsRemaining);
    writeValue(writer, value.shakeSequence);
    writeValue(writer, value.cameraShakeYawRadians);
    writeValue(writer, value.cameraShakePitchRadians);
}

bool readValue(BinaryReader &reader, OutdoorWorldRuntime::ArmageddonState &value)
{
    return readValue(reader, value.remainingSeconds)
        && readValue(reader, value.skillLevel)
        && readValue(reader, value.skillMastery)
        && readValue(reader, value.casterMemberIndex)
        && readValue(reader, value.shakeStepsRemaining)
        && readValue(reader, value.shakeSequence)
        && readValue(reader, value.cameraShakeYawRadians)
        && readValue(reader, value.cameraShakePitchRadians);
}

void writeValue(BinaryWriter &writer, const GameplayProjectileService::ProjectileState &value)
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
    writeValue(writer, value.visualMode);
    writeValue(writer, value.radius);
    writeValue(writer, value.height);
    writeValue(writer, value.spellId);
    writeValue(writer, value.effectSoundId);
    writeValue(writer, value.impactSoundIdOverride);
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
    writeValue(writer, value.damageType);
    writeValue(writer, value.useActorHitChance);
    writeValue(writer, value.timeSinceCreatedTicks);
    writeValue(writer, value.lifetimeTickAccumulator);
    writeValue(writer, value.lifetimeTicks);
    writeValue(writer, value.sectorId);
    writeValue(writer, value.isSettled);
    writeValue(writer, value.isExpired);
}

bool readValue(BinaryReader &reader, GameplayProjectileService::ProjectileState &value)
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
        && (reader.version() < SaveVersionProjectileVisualMode || readValue(reader, value.visualMode))
        && readValue(reader, value.radius)
        && readValue(reader, value.height)
        && readValue(reader, value.spellId)
        && readValue(reader, value.effectSoundId)
        && (reader.version() < SaveVersionFullProjectileState || readValue(reader, value.impactSoundIdOverride))
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
        && (reader.version() < SaveVersionFullProjectileState || readValue(reader, value.damageType))
        && readValue(reader, value.useActorHitChance)
        && readValue(reader, value.timeSinceCreatedTicks)
        && (reader.version() < SaveVersionFullProjectileState || readValue(reader, value.lifetimeTickAccumulator))
        && readValue(reader, value.lifetimeTicks)
        && (reader.version() < SaveVersionFullProjectileState || readValue(reader, value.sectorId))
        && (reader.version() < SaveVersionFullProjectileState || readValue(reader, value.isSettled))
        && readValue(reader, value.isExpired);
}

void writeValue(BinaryWriter &writer, const GameplayProjectileService::ProjectileImpactState &value)
{
    writeValue(writer, value.effectId);
    writeValue(writer, value.objectDescriptionId);
    writeValue(writer, value.objectSpriteId);
    writeValue(writer, value.objectSpriteFrameIndex);
    writeValue(writer, value.sourceObjectFlags);
    writeValue(writer, value.sourceSpellId);
    writeValue(writer, value.objectName);
    writeValue(writer, value.objectSpriteName);
    writeValue(writer, value.sourceObjectName);
    writeValue(writer, value.sourceObjectSpriteName);
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.z);
    writeValue(writer, value.timeSinceCreatedTicks);
    writeValue(writer, value.lifetimeTickAccumulator);
    writeValue(writer, value.lifetimeTicks);
    writeValue(writer, value.sectorId);
    writeValue(writer, value.freezeAnimation);
    writeValue(writer, value.isExpired);
}

bool readValue(BinaryReader &reader, GameplayProjectileService::ProjectileImpactState &value)
{
    return readValue(reader, value.effectId)
        && readValue(reader, value.objectDescriptionId)
        && readValue(reader, value.objectSpriteId)
        && readValue(reader, value.objectSpriteFrameIndex)
        && (reader.version() < SaveVersionFullProjectileState || readValue(reader, value.sourceObjectFlags))
        && (reader.version() < SaveVersionFullProjectileState || readValue(reader, value.sourceSpellId))
        && readValue(reader, value.objectName)
        && readValue(reader, value.objectSpriteName)
        && (reader.version() < SaveVersionFullProjectileState || readValue(reader, value.sourceObjectName))
        && (reader.version() < SaveVersionFullProjectileState || readValue(reader, value.sourceObjectSpriteName))
        && readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.z)
        && readValue(reader, value.timeSinceCreatedTicks)
        && (reader.version() < SaveVersionFullProjectileState || readValue(reader, value.lifetimeTickAccumulator))
        && readValue(reader, value.lifetimeTicks)
        && (reader.version() < SaveVersionFullProjectileState || readValue(reader, value.sectorId))
        && (reader.version() < SaveVersionFullProjectileState || readValue(reader, value.freezeAnimation))
        && readValue(reader, value.isExpired);
}

void writeValue(BinaryWriter &writer, const OutdoorWorldRuntime::FireSpikeTrapState &value)
{
    writeValue(writer, value.trapId);
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
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.z);
    writeValue(writer, value.timeSinceCreatedTicks);
    writeValue(writer, value.isExpired);
}

bool readValue(BinaryReader &reader, OutdoorWorldRuntime::FireSpikeTrapState &value)
{
    return readValue(reader, value.trapId)
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
        && readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.z)
        && readValue(reader, value.timeSinceCreatedTicks)
        && readValue(reader, value.isExpired);
}

void writeValue(BinaryWriter &writer, const IndoorWorldRuntime::FireSpikeTrapState &value)
{
    writeValue(writer, value.trapId);
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
    writeValue(writer, value.x);
    writeValue(writer, value.y);
    writeValue(writer, value.z);
    writeValue(writer, value.sectorId);
    writeValue(writer, value.timeSinceCreatedTicks);
    writeValue(writer, value.isExpired);
}

bool readValue(BinaryReader &reader, IndoorWorldRuntime::FireSpikeTrapState &value)
{
    return readValue(reader, value.trapId)
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
        && readValue(reader, value.x)
        && readValue(reader, value.y)
        && readValue(reader, value.z)
        && readValue(reader, value.sectorId)
        && readValue(reader, value.timeSinceCreatedTicks)
        && readValue(reader, value.isExpired);
}

void writeValue(BinaryWriter &writer, const GameplayProjectileService::Snapshot &value)
{
    writeValue(writer, value.nextProjectileId);
    writeValue(writer, value.nextProjectileImpactId);
    writeValue(writer, value.nextFireSpikeTrapId);
    writeValue(writer, value.projectiles);
    writeValue(writer, value.projectileImpacts);
}

bool readValue(BinaryReader &reader, GameplayProjectileService::Snapshot &value)
{
    return readValue(reader, value.nextProjectileId)
        && readValue(reader, value.nextProjectileImpactId)
        && (reader.version() < SaveVersionFullProjectileState || readValue(reader, value.nextFireSpikeTrapId))
        && readValue(reader, value.projectiles)
        && readValue(reader, value.projectileImpacts);
}

// Saves before SaveVersionWeatherModel stored a debug rain-intensity override (flag and preset byte); the weather
// model replaces it, so older saves read and drop it.
bool skipRetiredRainIntensityOverride(BinaryReader &reader)
{
    bool hasOverride = false;
    uint8_t preset = 0;
    return readValue(reader, hasOverride) && readValue(reader, preset);
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
    writeValue(writer, value.locationInfo);
    writeValue(writer, value.locationTime);
    writeValue(writer, value.hasLocationTime);
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
    writeValue(writer, value.nextFireSpikeTrapId);
    writeValue(writer, value.projectiles);
    writeValue(writer, value.projectileImpacts);
    writeValue(writer, value.fireSpikeTraps);
    writeValue(writer, value.fullyRevealedCells);
    writeValue(writer, value.partiallyRevealedCells);
    writeValue(writer, value.gameplayOverlayRemainingSeconds);
    writeValue(writer, value.gameplayOverlayDurationSeconds);
    writeValue(writer, value.gameplayOverlayPeakAlpha);
    writeValue(writer, value.gameplayOverlayColorAbgr);
    writeValue(writer, value.armageddon);
    writeValue(writer, value.bloodSplats);
    writeValue(writer, value.faceAttributes);
    writeValue(writer, value.searchedLootPropSourceIds);
}

bool readValue(BinaryReader &reader, OutdoorWorldRuntime::Snapshot &value)
{
    const bool loaded = readValue(reader, value.gameMinutes)
        && (reader.version() < SaveVersionOutdoorLocationInfo || readValue(reader, value.locationInfo))
        && (reader.version() < SaveVersionLegacyEvtTimers || readValue(reader, value.locationTime))
        && (reader.version() < SaveVersionLegacyEvtTimers || readValue(reader, value.hasLocationTime))
        && readValue(reader, value.atmosphere)
        && readOutdoorTimerStates(reader, value.timers)
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
        && (reader.version() < SaveVersionFullProjectileState || readValue(reader, value.nextFireSpikeTrapId))
        && readValue(reader, value.projectiles)
        && readValue(reader, value.projectileImpacts)
        && (reader.version() < SaveVersionFullProjectileState || readValue(reader, value.fireSpikeTraps))
        && (reader.version() < SaveVersionOutdoorJournalRevealMask
            || readValue(reader, value.fullyRevealedCells))
        && (reader.version() < SaveVersionOutdoorJournalRevealMask
            || readValue(reader, value.partiallyRevealedCells))
        && (reader.version() < SaveVersionOutdoorRuntimeSaveParity
            || (readValue(reader, value.gameplayOverlayRemainingSeconds)
                && readValue(reader, value.gameplayOverlayDurationSeconds)
                && readValue(reader, value.gameplayOverlayPeakAlpha)
                && readValue(reader, value.gameplayOverlayColorAbgr)
                && readValue(reader, value.armageddon)
                && (reader.version() >= SaveVersionWeatherModel || skipRetiredRainIntensityOverride(reader))
                && readValue(reader, value.bloodSplats)))
        && (reader.version() < SaveVersionOutdoorFaceAttributes
            || readValue(reader, value.faceAttributes))
        && (reader.version() < SaveVersionMm9ItemSourceState
            || readValue(reader, value.searchedLootPropSourceIds));

    if (loaded && reader.version() >= SaveVersionOutdoorRuntimeSaveParity)
    {
        value.hasOutdoorRuntimeSaveParityFields = true;
    }

    return loaded;
}

void writeValue(BinaryWriter &writer, const IndoorSceneRuntime::Snapshot &value)
{
    writeValue(writer, value.mapDeltaData);
    writeValue(writer, value.eventRuntimeState);
    writeValue(writer, value.worldRuntime);
    writeValue(writer, value.partyRuntime);
    writeValue(writer, value.timers);
    writeValue(writer, value.lastProcessedPartyMoveStateForFaceTriggers);
    writeValue(writer, value.mechanismAccumulatorMilliseconds);
}

bool readValue(BinaryReader &reader, IndoorSceneRuntime::Snapshot &value)
{
    return readValue(reader, value.mapDeltaData)
        && readValue(reader, value.eventRuntimeState)
        && (reader.version() < 20 || readValue(reader, value.worldRuntime))
        && (reader.version() < 20 || readValue(reader, value.partyRuntime))
        && (reader.version() < SaveVersionIndoorSaveLoadParity || readIndoorTimerStates(reader, value.timers))
        && (reader.version() < SaveVersionIndoorSaveLoadParity
            || readValue(reader, value.lastProcessedPartyMoveStateForFaceTriggers))
        && readValue(reader, value.mechanismAccumulatorMilliseconds);
}

void writeValue(BinaryWriter &writer, const GameSaveData &value)
{
    writeValue(writer, value.currentSceneKind);
    writeValue(writer, value.mapFileName);
    writeValue(writer, value.party);
    writeValue(writer, value.namedGlobalVars);
    writeValue(writer, value.hasOutdoorRuntimeState);
    writeValue(writer, value.outdoorParty);
    writeValue(writer, value.outdoorWorld);
    writeValue(writer, value.outdoorWorldStates);
    writeValue(writer, value.hasIndoorSceneState);
    writeValue(writer, value.indoorScene);
    writeValue(writer, value.indoorSceneStates);
    writeValue(writer, value.savedGameMinutes);
    writeValue(writer, value.cameraYawRadians);
    writeValue(writer, value.cameraPitchRadians);
    writeValue(writer, value.heldInventoryItemActive);
    writeValue(writer, value.heldInventoryItem);
    writeValue(writer, value.heldInventoryItemGrabCellOffsetX);
    writeValue(writer, value.heldInventoryItemGrabCellOffsetY);
    writeValue(writer, value.heldInventoryItemGrabOffsetX);
    writeValue(writer, value.heldInventoryItemGrabOffsetY);
    writeValue(writer, value.requiredContentPackages);
    writeValue(writer, value.saveName);
    writeValue(writer, value.previewBmp);
}

bool readValue(BinaryReader &reader, GameSaveData &value)
{
    const bool read = readValue(reader, value.currentSceneKind)
        && readValue(reader, value.mapFileName)
        && readValue(reader, value.party)
        && (reader.version() < SaveVersionSessionNamedGlobalVars || readValue(reader, value.namedGlobalVars))
        && readValue(reader, value.hasOutdoorRuntimeState)
        && readValue(reader, value.outdoorParty)
        && readValue(reader, value.outdoorWorld)
        && readValue(reader, value.outdoorWorldStates)
        && readValue(reader, value.hasIndoorSceneState)
        && readValue(reader, value.indoorScene)
        && readValue(reader, value.indoorSceneStates)
        && readValue(reader, value.savedGameMinutes)
        && readValue(reader, value.cameraYawRadians)
        && readValue(reader, value.cameraPitchRadians)
        && (reader.version() < SaveVersionHeldCursorItem || readValue(reader, value.heldInventoryItemActive))
        && (reader.version() < SaveVersionHeldCursorItem || readValue(reader, value.heldInventoryItem))
        && (reader.version() < SaveVersionHeldCursorItem
            || readValue(reader, value.heldInventoryItemGrabCellOffsetX))
        && (reader.version() < SaveVersionHeldCursorItem
            || readValue(reader, value.heldInventoryItemGrabCellOffsetY))
        && (reader.version() < SaveVersionHeldCursorItem || readValue(reader, value.heldInventoryItemGrabOffsetX))
        && (reader.version() < SaveVersionHeldCursorItem || readValue(reader, value.heldInventoryItemGrabOffsetY))
        && (reader.version() < SaveVersionRequiredContentPackages
            || readValue(reader, value.requiredContentPackages))
        && readValue(reader, value.saveName)
        && readValue(reader, value.previewBmp);
    value.cameraAnglesValid = reader.version() >= SaveVersionIndoorCamera || value.currentSceneKind == SceneKind::Outdoor;
    return read;
}
}

namespace
{
void migrateLegacyIndoorCorpseMarkers(IndoorSceneRuntime::Snapshot &snapshot)
{
    if (!snapshot.mapDeltaData)
    {
        return;
    }

    const std::vector<MapDeltaActor> &actors = snapshot.mapDeltaData->actors;
    std::vector<std::optional<GameplayCorpseViewState>> &corpseViews =
        snapshot.worldRuntime.mapActorCorpseViews;
    corpseViews.resize(std::max(corpseViews.size(), actors.size()));
    const uint32_t invisibleMask = static_cast<uint32_t>(EvtActorAttribute::Invisible);

    for (size_t actorIndex = 0; actorIndex < actors.size(); ++actorIndex)
    {
        const MapDeltaActor &actor = actors[actorIndex];

        if (actor.hp <= 0 && (actor.attributes & invisibleMask) != 0 && !corpseViews[actorIndex].has_value())
        {
            GameplayCorpseViewState consumedCorpse = {};
            consumedCorpse.sourceIndex = static_cast<uint32_t>(actorIndex);
            corpseViews[actorIndex] = std::move(consumedCorpse);
        }
    }
}

void migrateLegacyOutdoorCorpseMarkers(OutdoorWorldRuntime::Snapshot &snapshot)
{
    std::vector<std::optional<GameplayCorpseViewState>> &corpseViews = snapshot.mapActorCorpseViews;
    corpseViews.resize(std::max(corpseViews.size(), snapshot.mapActors.size()));

    for (size_t actorIndex = 0; actorIndex < snapshot.mapActors.size(); ++actorIndex)
    {
        const OutdoorWorldRuntime::MapActorState &actor = snapshot.mapActors[actorIndex];
        const bool terminalCorpse = actor.isDead
            || actor.currentHp <= 0
            || actor.aiState == OutdoorWorldRuntime::ActorAiState::Dying
            || actor.aiState == OutdoorWorldRuntime::ActorAiState::Dead;

        if (terminalCorpse && actor.isInvisible && !corpseViews[actorIndex].has_value())
        {
            GameplayCorpseViewState consumedCorpse = {};
            consumedCorpse.sourceIndex = static_cast<uint32_t>(actorIndex);
            corpseViews[actorIndex] = std::move(consumedCorpse);
        }
    }
}

std::vector<uint32_t> persistentSaveItemIds(const GameSaveData &data)
{
    std::vector<uint32_t> itemIds;
    const auto appendInventoryItem = [&itemIds](const InventoryItem &item)
    {
        if (item.objectDescriptionId != 0)
        {
            itemIds.push_back(item.objectDescriptionId);
        }
    };
    const auto appendChestView = [&appendInventoryItem](const GameplayChestViewState &view)
    {
        for (const GameplayChestItemState &item : view.items)
        {
            appendInventoryItem(item.item);
        }
        for (const GameplayChestItemState &item : view.hiddenItems)
        {
            appendInventoryItem(item.item);
        }
    };
    const auto appendCorpseView = [&appendInventoryItem](const GameplayCorpseViewState &view)
    {
        for (const GameplayChestItemState &item : view.items)
        {
            appendInventoryItem(item.item);
        }
    };
    const auto appendCharacterItems = [&itemIds](const Character &member)
    {
        for (const InventoryItem &item : member.inventory)
        {
            if (item.objectDescriptionId != 0)
            {
                itemIds.push_back(item.objectDescriptionId);
            }
        }

        const CharacterEquipment &equipment = member.equipment;
        for (uint32_t itemId : {
                 equipment.offHand,
                 equipment.mainHand,
                 equipment.bow,
                 equipment.armor,
                 equipment.helm,
                 equipment.belt,
                 equipment.cloak,
                 equipment.gauntlets,
                 equipment.boots,
                 equipment.amulet,
                 equipment.ring1,
                 equipment.ring2,
                 equipment.ring3,
                 equipment.ring4,
                 equipment.ring5,
                 equipment.ring6})
        {
            if (itemId != 0)
            {
                itemIds.push_back(itemId);
            }
        }
    };

    for (const Character &member : data.party.members)
    {
        appendCharacterItems(member);
    }

    for (const AdventurersInnMember &member : data.party.adventurersInnMembers)
    {
        appendCharacterItems(member.character);
    }

    for (const Party::HouseStockState &state : data.party.houseStockStates)
    {
        for (const InventoryItem &item : state.standardStock)
        {
            appendInventoryItem(item);
        }
        for (const InventoryItem &item : state.specialStock)
        {
            appendInventoryItem(item);
        }
        for (const InventoryItem &item : state.spellbookStock)
        {
            appendInventoryItem(item);
        }
    }

    if (data.heldInventoryItemActive && data.heldInventoryItem.objectDescriptionId != 0)
    {
        itemIds.push_back(data.heldInventoryItem.objectDescriptionId);
    }

    const auto appendOutdoorWorld = [&](const OutdoorWorldRuntime::Snapshot &snapshot)
    {
        for (const std::optional<GameplayChestViewState> &view : snapshot.materializedChestViews)
        {
            if (view)
            {
                appendChestView(*view);
            }
        }
        if (snapshot.activeChestView)
        {
            appendChestView(*snapshot.activeChestView);
        }
        for (const std::optional<GameplayCorpseViewState> &view : snapshot.mapActorCorpseViews)
        {
            if (view)
            {
                appendCorpseView(*view);
            }
        }
        if (snapshot.activeCorpseView)
        {
            appendCorpseView(*snapshot.activeCorpseView);
        }
        for (const OutdoorWorldRuntime::WorldItemState &item : snapshot.worldItems)
        {
            appendInventoryItem(item.item);
        }
    };
    const auto appendIndoorWorld = [&](const IndoorWorldRuntime::Snapshot &snapshot)
    {
        for (const std::optional<GameplayChestViewState> &view : snapshot.materializedChestViews)
        {
            if (view)
            {
                appendChestView(*view);
            }
        }
        if (snapshot.activeChestView)
        {
            appendChestView(*snapshot.activeChestView);
        }
        for (const std::optional<GameplayCorpseViewState> &view : snapshot.mapActorCorpseViews)
        {
            if (view)
            {
                appendCorpseView(*view);
            }
        }
        if (snapshot.activeCorpseView)
        {
            appendCorpseView(*snapshot.activeCorpseView);
        }
    };

    if (data.hasOutdoorRuntimeState)
    {
        appendOutdoorWorld(data.outdoorWorld);
    }
    for (const auto &[mapName, snapshot] : data.outdoorWorldStates)
    {
        (void)mapName;
        appendOutdoorWorld(snapshot);
    }
    if (data.hasIndoorSceneState)
    {
        appendIndoorWorld(data.indoorScene.worldRuntime);
    }
    for (const auto &[mapName, snapshot] : data.indoorSceneStates)
    {
        (void)mapName;
        appendIndoorWorld(snapshot.worldRuntime);
    }

    std::sort(itemIds.begin(), itemIds.end());
    itemIds.erase(std::unique(itemIds.begin(), itemIds.end()), itemIds.end());
    return itemIds;
}
}

void migrateLegacyNpcRosters(GameSaveData &data)
{
    const float gameMinutes = data.savedGameMinutes > 0.0f ? data.savedGameMinutes
        : (data.currentSceneKind == SceneKind::Outdoor ? data.outdoorWorld.gameMinutes
                                                     : data.indoorScene.worldRuntime.gameMinutes);
    const int32_t currentMinute = std::max(0, int32_t(std::floor(gameMinutes)));
    const auto migrate = [currentMinute](std::optional<EventRuntimeState> &state)
    {
        if (!state)
        {
            return;
        }
        // Legacy map hashes are seed zero; keep the whole saved roster until its next monthly refill.
        if (state->namedMapVars.try_emplace("MMerge.RandomNPC.Seed", 0).second)
        {
            state->namedMapVars["MMerge.RandomNPC.RefillMinutes"] = currentMinute;
        }
        if (!state->generatedMercenaryRecruitsByNpcId.empty())
        {
            state->namedMapVars.try_emplace("MMerge.Mercenaries.RefillMonth", currentMinute / (28 * 24 * 60));
        }
    };
    migrate(data.outdoorWorld.eventRuntimeState);
    migrate(data.indoorScene.eventRuntimeState);
    for (auto &[mapFileName, snapshot] : data.outdoorWorldStates)
    {
        migrate(snapshot.eventRuntimeState);
    }
    for (auto &[mapFileName, snapshot] : data.indoorSceneStates)
    {
        migrate(snapshot.eventRuntimeState);
    }
}

void migrateLegacyConsumedCorpseMarkers(GameSaveData &data, uint32_t sourceSaveVersion)
{
    if (sourceSaveVersion >= SaveVersionConsumedCorpseMarkers)
    {
        return;
    }

    if (data.hasOutdoorRuntimeState)
    {
        migrateLegacyOutdoorCorpseMarkers(data.outdoorWorld);
    }

    for (auto &[mapName, snapshot] : data.outdoorWorldStates)
    {
        (void)mapName;
        migrateLegacyOutdoorCorpseMarkers(snapshot);
    }

    if (data.hasIndoorSceneState)
    {
        migrateLegacyIndoorCorpseMarkers(data.indoorScene);
    }

    for (auto &[mapName, snapshot] : data.indoorSceneStates)
    {
        (void)mapName;
        migrateLegacyIndoorCorpseMarkers(snapshot);
    }
}

std::unordered_map<std::string, uint32_t> collectRequiredContentPackages(
    const GameSaveData &data,
    const ItemTable &itemTable,
    const HouseTable &houseTable,
    const std::unordered_map<std::string, uint32_t> &loadedPackageSchemas)
{
    std::unordered_map<std::string, uint32_t> result;

    for (uint32_t itemId : persistentSaveItemIds(data))
    {
        const ItemDefinition *pDefinition = itemTable.get(itemId);

        if (pDefinition == nullptr || pDefinition->packageId.empty() || pDefinition->packageId == "engine")
        {
            continue;
        }

        const auto foundSchema = loadedPackageSchemas.find(pDefinition->packageId);
        result[pDefinition->packageId] = foundSchema != loadedPackageSchemas.end() ? foundSchema->second : 0;
    }

    for (const Party::HouseStockState &state : data.party.houseStockStates)
    {
        const HouseEntry *pHouseEntry = houseTable.get(state.houseId);
        if (state.generationVersion == 0
            || pHouseEntry == nullptr
            || pHouseEntry->packageId.empty()
            || pHouseEntry->packageId == "engine")
        {
            continue;
        }
        const auto foundSchema = loadedPackageSchemas.find(pHouseEntry->packageId);
        result[pHouseEntry->packageId] = foundSchema != loadedPackageSchemas.end() ? foundSchema->second : 0;
    }

    return result;
}

bool validateRequiredContentPackages(
    const GameSaveData &data,
    const ItemTable &itemTable,
    const HouseTable &houseTable,
    const std::unordered_map<std::string, uint32_t> &loadedPackageSchemas,
    std::string &error)
{
    error.clear();

    for (const auto &[packageId, requiredSchema] : data.requiredContentPackages)
    {
        const auto foundPackage = loadedPackageSchemas.find(packageId);

        if (foundPackage == loadedPackageSchemas.end())
        {
            error = "save requires missing content package '" + packageId + "'";
            return false;
        }

        if (requiredSchema == 0 || foundPackage->second != requiredSchema)
        {
            error = "save requires content package '" + packageId + "' schema "
                + std::to_string(requiredSchema) + ", loaded schema is " + std::to_string(foundPackage->second);
            return false;
        }
    }

    for (uint32_t itemId : persistentSaveItemIds(data))
    {
        const ItemDefinition *pDefinition = itemTable.get(itemId);

        if (pDefinition == nullptr)
        {
            error = "save references missing item definition " + std::to_string(itemId);
            return false;
        }

        if (pDefinition->packageId != "engine"
            && !data.requiredContentPackages.contains(pDefinition->packageId))
        {
            error = "save item " + std::to_string(itemId) + " is missing required package metadata for '"
                + pDefinition->packageId + "'";
            return false;
        }
    }

    for (const Party::HouseStockState &state : data.party.houseStockStates)
    {
        if (state.generationVersion == 0)
        {
            continue;
        }
        const HouseEntry *pHouseEntry = houseTable.get(state.houseId);
        if (pHouseEntry == nullptr || pHouseEntry->vendorStockProfile == VendorStockProfile::None)
        {
            error = "save references missing vendor definition " + std::to_string(state.houseId);
            return false;
        }
        if (pHouseEntry->packageId != "engine"
            && !data.requiredContentPackages.contains(pHouseEntry->packageId))
        {
            error = "save vendor " + std::to_string(state.houseId)
                + " is missing required package metadata for '" + pHouseEntry->packageId + "'";
            return false;
        }
    }

    return true;
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

    if (version > SaveVersion)
    {
        error = "unsupported save version";
        return std::nullopt;
    }

    reader.setVersion(version);

    GameSaveData data = {};
    bool decoded = false;

    try
    {
        decoded = reader.read(data);
    }
    catch (const std::exception &exception)
    {
        error = std::string("save data is corrupted: ") + exception.what();
        return std::nullopt;
    }

    if (!decoded || reader.failed())
    {
        error = "save data is corrupted";
        return std::nullopt;
    }

    migrateLegacyConsumedCorpseMarkers(data, version);
    migrateLegacyNpcRosters(data);

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
