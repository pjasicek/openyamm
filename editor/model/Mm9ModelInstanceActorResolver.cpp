#include "editor/model/Mm9ModelInstanceActorResolver.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <array>
#include <cctype>
#include <deque>
#include <exception>
#include <filesystem>
#include <optional>
#include <sstream>
#include <string_view>
#include <utility>
#include <vector>

namespace OpenYAMM::Editor
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

std::string trimWhitespaceCopy(const std::string &value)
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

bool endsWithCaseInsensitive(const std::string &value, const std::string &suffix)
{
    if (suffix.size() > value.size())
    {
        return false;
    }

    const size_t offset = value.size() - suffix.size();
    for (size_t index = 0; index < suffix.size(); ++index)
    {
        const char lhs = static_cast<char>(std::tolower(static_cast<unsigned char>(value[offset + index])));
        const char rhs = static_cast<char>(std::tolower(static_cast<unsigned char>(suffix[index])));
        if (lhs != rhs)
        {
            return false;
        }
    }

    return true;
}

std::string stripTrailingDigits(std::string value)
{
    while (!value.empty() && std::isdigit(static_cast<unsigned char>(value.back())))
    {
        value.pop_back();
    }

    return value;
}

bool actorTokenMatches(const std::string &value, const std::string &key)
{
    return value == key || value.rfind(key, 0) == 0 || stripTrailingDigits(value) == key;
}

std::string normalizeActorKey(const std::string &value)
{
    std::string key;

    for (const char character : value)
    {
        if (std::isalnum(static_cast<unsigned char>(character)))
        {
            key.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(character))));
        }
    }

    return stripTrailingDigits(key);
}

void appendUnique(std::vector<std::string> &values, const std::string &value)
{
    if (!value.empty() && std::find(values.begin(), values.end(), value) == values.end())
    {
        values.push_back(value);
    }
}

bool startsWith(const std::string &value, const std::string &prefix)
{
    return value.rfind(prefix, 0) == 0;
}

std::string soundKey(std::string value)
{
    value = trimWhitespaceCopy(value);

    std::string key;
    for (const char character : value)
    {
        if (std::isalnum(static_cast<unsigned char>(character)))
        {
            key.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(character))));
        }
    }

    return key;
}

std::string lookupKey(const std::string &sourceModel, const std::string &actorKey)
{
    return sourceModel + "|" + actorKey;
}

std::vector<std::string> typePictureKeys(const std::string &value)
{
    const std::string key = normalizeActorKey(value);
    if (key.empty())
    {
        return {};
    }

    std::vector<std::string> keys;
    appendUnique(keys, key);

    if (startsWith(key, "peasant"))
    {
        appendUnique(keys, key.substr(7));
    }

    for (const std::string &prefix : std::array<std::string, 2>{{"peasant", ""}})
    {
        const bool hasPrefix = !prefix.empty() && startsWith(key, prefix);
        const std::string candidate = hasPrefix ? key.substr(prefix.size()) : key;
        if (candidate.empty())
        {
            continue;
        }

        const char suffix = candidate.back();
        if (suffix == 'a' || suffix == 'b' || suffix == 'c' || suffix == 'd')
        {
            appendUnique(keys, candidate.substr(0, candidate.size() - 1));
        }
    }

    return keys;
}

std::vector<std::string> sourceClassTypePictureKeys(const std::string &value)
{
    const std::string sourceKey = normalizeActorKey(value);
    if (sourceKey.empty())
    {
        return {};
    }

    static constexpr std::array<std::pair<std::string_view, std::string_view>, 4> RoleCodes = {{
        {"commoner", "a"},
        {"town", "b"},
        {"shopkeeper", "c"},
        {"prisoner", "d"},
    }};

    std::string roleCode;
    std::string remainder = sourceKey;
    for (const std::pair<std::string_view, std::string_view> &roleCodePair : RoleCodes)
    {
        const std::string role(roleCodePair.first);
        if (startsWith(sourceKey, role))
        {
            roleCode = std::string(roleCodePair.second);
            remainder = sourceKey.substr(role.size());
            break;
        }
    }

    static constexpr std::array<std::pair<std::string_view, std::string_view>, 5> RaceKeys = {{
        {"human2", "human2"},
        {"human", "human1"},
        {"elf", "elf"},
        {"dwarf", "dwarf"},
        {"halforc", "halforc"},
    }};

    std::string race;
    std::string raceRemainder = remainder;
    for (const std::pair<std::string_view, std::string_view> &raceKeyPair : RaceKeys)
    {
        const std::string racePrefix(raceKeyPair.first);
        if (startsWith(raceRemainder, racePrefix))
        {
            race = std::string(raceKeyPair.second);
            raceRemainder = raceRemainder.substr(racePrefix.size());
            break;
        }
    }

    std::string gender;
    std::string genderRemainder = raceRemainder;
    for (const std::string &genderPrefix : std::array<std::string, 2>{{"female", "male"}})
    {
        if (startsWith(genderRemainder, genderPrefix))
        {
            gender = genderPrefix;
            genderRemainder = genderRemainder.substr(genderPrefix.size());
            break;
        }
    }

    if (race.empty() || gender.empty() || genderRemainder.size() != 1
        || std::string("abcd").find(genderRemainder.front()) == std::string::npos)
    {
        return {};
    }

    const std::string variantCode = genderRemainder;
    std::vector<std::string> keys;

    if (race == "halforc")
    {
        appendUnique(keys, "peasant" + race + gender + variantCode);
    }

    if (!roleCode.empty())
    {
        appendUnique(keys, "peasant" + race + gender + roleCode + variantCode);
    }

    const size_t peasantKeyCount = keys.size();
    for (size_t keyIndex = 0; keyIndex < peasantKeyCount; ++keyIndex)
    {
        if (startsWith(keys[keyIndex], "peasant"))
        {
            appendUnique(keys, keys[keyIndex].substr(7));
        }
    }

    return keys;
}

std::string joinSourceSkins(const YAML::Node &sourceSkinsNode)
{
    if (!sourceSkinsNode || !sourceSkinsNode.IsSequence())
    {
        return {};
    }

    std::string sourceSkin;
    for (const YAML::Node &skinNode : sourceSkinsNode)
    {
        if (!skinNode.IsScalar())
        {
            continue;
        }

        const std::string skinPath = normalizeMm9ModelInstanceVirtualPath(skinNode.as<std::string>());
        if (skinPath.empty())
        {
            continue;
        }

        if (!sourceSkin.empty())
        {
            sourceSkin += ";";
        }
        sourceSkin += skinPath;
    }

    return sourceSkin;
}

std::vector<std::string> splitTsvLine(const std::string &line)
{
    std::vector<std::string> cells;
    size_t begin = 0;

    while (begin <= line.size())
    {
        const size_t separator = line.find('\t', begin);
        const size_t end = separator == std::string::npos ? line.size() : separator;
        std::string cell = line.substr(begin, end - begin);

        if (cell.size() >= 2 && cell.front() == '"' && cell.back() == '"')
        {
            cell = cell.substr(1, cell.size() - 2);
        }

        cells.push_back(cell);

        if (separator == std::string::npos)
        {
            break;
        }

        begin = separator + 1;
    }

    return cells;
}

void assignActorRowField(
    std::string &target,
    const std::vector<std::string> &row,
    const std::unordered_map<std::string, size_t> &columnByName,
    const std::string &columnName)
{
    const auto found = columnByName.find(columnName);
    if (found == columnByName.end() || found->second >= row.size())
    {
        return;
    }

    target = row[found->second];
}

Mm9ResolvedModelInstanceActorSource::ActorRow actorRowIdentityFromTableRow(
    const std::string &table,
    size_t rowIndex,
    const std::vector<std::string> &row,
    const std::unordered_map<std::string, size_t> &columnByName)
{
    Mm9ResolvedModelInstanceActorSource::ActorRow actorRow = {};
    actorRow.table = table;
    actorRow.row = std::to_string(rowIndex);
    assignActorRowField(actorRow.number, row, columnByName, "Number");
    assignActorRowField(actorRow.monsterName, row, columnByName, "Monster Name");
    assignActorRowField(actorRow.typePicture, row, columnByName, "Type/Picture");
    assignActorRowField(actorRow.baseName, row, columnByName, "BaseName");
    assignActorRowField(actorRow.level, row, columnByName, "LVL");
    assignActorRowField(actorRow.hitPoints, row, columnByName, "HP");
    assignActorRowField(actorRow.armorClass, row, columnByName, "AC");
    assignActorRowField(actorRow.experience, row, columnByName, "EXP");
    assignActorRowField(actorRow.speed, row, columnByName, "SPD");
    assignActorRowField(actorRow.treasureType, row, columnByName, "TreasureType");
    assignActorRowField(actorRow.quest, row, columnByName, "Quest");
    assignActorRowField(actorRow.fly, row, columnByName, "Fly");
    assignActorRowField(actorRow.move, row, columnByName, "Move");
    assignActorRowField(actorRow.walkVelocity, row, columnByName, "WalkVelocity");
    assignActorRowField(actorRow.runVelocity, row, columnByName, "RunVelocity");
    assignActorRowField(actorRow.flyVelocity, row, columnByName, "FlyVelocity");
    assignActorRowField(actorRow.lungeVelocity, row, columnByName, "LungeVelocity");
    assignActorRowField(actorRow.attackReach, row, columnByName, "AttackReach");
    assignActorRowField(actorRow.attackRange, row, columnByName, "AttackRange");
    assignActorRowField(actorRow.recovery, row, columnByName, "Recovery");
    assignActorRowField(actorRow.targetPreference, row, columnByName, "Target Pref");
    assignActorRowField(actorRow.bonus, row, columnByName, "Bonus");
    assignActorRowField(actorRow.alertRadius, row, columnByName, "AlertRadius");
    assignActorRowField(actorRow.accuracy, row, columnByName, "Accuracy");
    assignActorRowField(actorRow.scriptName, row, columnByName, "ScriptName");
    assignActorRowField(actorRow.footSound, row, columnByName, "FootSound");
    assignActorRowField(actorRow.footRadius, row, columnByName, "FootRadius");
    assignActorRowField(actorRow.transparent, row, columnByName, "Transparent");
    assignActorRowField(actorRow.headTurn, row, columnByName, "HeadTurn");
    assignActorRowField(actorRow.special, row, columnByName, "Special");
    assignActorRowField(actorRow.scale, row, columnByName, "Scale");
    assignActorRowField(actorRow.evadeChance, row, columnByName, "Evade Chance");
    assignActorRowField(actorRow.strafeAttackPct, row, columnByName, "Strafe Attack Pct");
    assignActorRowField(actorRow.isMonster, row, columnByName, "IsMonster");
    assignActorRowField(actorRow.hostilityGroup, row, columnByName, "Hostility Group");
    assignActorRowField(actorRow.treasureLevel, row, columnByName, "Treasure Level");
    assignActorRowField(actorRow.voiceRadius, row, columnByName, "Voice Radius");
    return actorRow;
}

std::string actorIdentityLookupKey(
    const std::string &table,
    const std::string &keyKind,
    const std::string &keyValue)
{
    return toLowerCopy(table) + "|" + keyKind + "|" + trimWhitespaceCopy(keyValue);
}

using ActorIdentityByKey =
    std::unordered_map<std::string, Mm9ResolvedModelInstanceActorSource::ActorRow>;

void addActorIdentityTable(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &table,
    ActorIdentityByKey &identityByKey)
{
    const std::optional<std::string> tableText =
        assetFileSystem.readTextFile("source/data/" + table + ".txt");
    if (!tableText)
    {
        return;
    }

    std::istringstream stream(*tableText);
    std::string line;
    if (!std::getline(stream, line))
    {
        return;
    }

    if (!line.empty() && line.back() == '\r')
    {
        line.pop_back();
    }

    const std::vector<std::string> headers = splitTsvLine(line);
    std::unordered_map<std::string, size_t> columnByName;
    for (size_t columnIndex = 0; columnIndex < headers.size(); ++columnIndex)
    {
        columnByName.emplace(headers[columnIndex], columnIndex);
    }

    size_t rowIndex = 0;
    while (std::getline(stream, line))
    {
        if (!line.empty() && line.back() == '\r')
        {
            line.pop_back();
        }

        if (trimWhitespaceCopy(line).empty())
        {
            continue;
        }

        const std::vector<std::string> row = splitTsvLine(line);
        Mm9ResolvedModelInstanceActorSource::ActorRow actorRow =
            actorRowIdentityFromTableRow(table, rowIndex, row, columnByName);

        if (!actorRow.number.empty())
        {
            identityByKey[actorIdentityLookupKey(table, "number", actorRow.number)] = actorRow;
        }

        identityByKey[actorIdentityLookupKey(table, "row", actorRow.row)] = actorRow;
        identityByKey[actorIdentityLookupKey(table, "row", std::to_string(rowIndex + 1))] = actorRow;
        ++rowIndex;
    }
}

ActorIdentityByKey loadActorIdentityRows(const Engine::AssetFileSystem &assetFileSystem)
{
    ActorIdentityByKey identityByKey;
    addActorIdentityTable(assetFileSystem, "ACTOR", identityByKey);
    addActorIdentityTable(assetFileSystem, "MONSTERS", identityByKey);
    return identityByKey;
}

void copyActorIdentityFields(
    Mm9ResolvedModelInstanceActorSource::ActorRow &target,
    const Mm9ResolvedModelInstanceActorSource::ActorRow &source)
{
    if (target.table.empty())
    {
        target.table = source.table;
    }
    if (target.row.empty())
    {
        target.row = source.row;
    }
    if (target.number.empty())
    {
        target.number = source.number;
    }
    if (target.monsterName.empty())
    {
        target.monsterName = source.monsterName;
    }
    if (target.typePicture.empty())
    {
        target.typePicture = source.typePicture;
    }
    if (target.baseName.empty())
    {
        target.baseName = source.baseName;
    }

    target.level = source.level;
    target.hitPoints = source.hitPoints;
    target.armorClass = source.armorClass;
    target.experience = source.experience;
    target.speed = source.speed;
    target.treasureType = source.treasureType;
    target.quest = source.quest;
    target.fly = source.fly;
    target.move = source.move;
    target.walkVelocity = source.walkVelocity;
    target.runVelocity = source.runVelocity;
    target.flyVelocity = source.flyVelocity;
    target.lungeVelocity = source.lungeVelocity;
    target.attackReach = source.attackReach;
    target.attackRange = source.attackRange;
    target.recovery = source.recovery;
    target.targetPreference = source.targetPreference;
    target.bonus = source.bonus;
    target.alertRadius = source.alertRadius;
    target.accuracy = source.accuracy;
    target.scriptName = source.scriptName;
    target.footSound = source.footSound;
    target.footRadius = source.footRadius;
    target.transparent = source.transparent;
    target.headTurn = source.headTurn;
    target.special = source.special;
    target.scale = source.scale;
    target.evadeChance = source.evadeChance;
    target.strafeAttackPct = source.strafeAttackPct;
    target.isMonster = source.isMonster;
    target.hostilityGroup = source.hostilityGroup;
    target.treasureLevel = source.treasureLevel;
    target.voiceRadius = source.voiceRadius;
    target.footSoundReferences = source.footSoundReferences;
}

void enrichActorRowFromIdentityTable(
    Mm9ResolvedModelInstanceActorSource::ActorRow &actorRow,
    const ActorIdentityByKey &identityByKey)
{
    if (actorRow.table.empty())
    {
        return;
    }

    const std::string table = actorRow.table;
    if (!actorRow.number.empty())
    {
        const auto found = identityByKey.find(actorIdentityLookupKey(table, "number", actorRow.number));
        if (found != identityByKey.end())
        {
            copyActorIdentityFields(actorRow, found->second);
            return;
        }
    }

    if (!actorRow.row.empty())
    {
        const auto found = identityByKey.find(actorIdentityLookupKey(table, "row", actorRow.row));
        if (found != identityByKey.end())
        {
            copyActorIdentityFields(actorRow, found->second);
        }
    }
}

void appendCandidates(
    std::vector<const Mm9ModelInstanceActorSourceLookup::Candidate *> &candidates,
    const std::unordered_map<std::string, std::vector<Mm9ModelInstanceActorSourceLookup::Candidate>> &sourceByKey,
    const std::string &key)
{
    const auto found = sourceByKey.find(key);
    if (found == sourceByKey.end())
    {
        return;
    }

    for (const Mm9ModelInstanceActorSourceLookup::Candidate &candidate : found->second)
    {
        candidates.push_back(&candidate);
    }
}

std::optional<Mm9ResolvedModelInstanceActorSource> uniqueResolvedSource(
    const std::vector<const Mm9ModelInstanceActorSourceLookup::Candidate *> &candidates)
{
    const Mm9ModelInstanceActorSourceLookup::Candidate *pUniqueCandidate = nullptr;
    for (const Mm9ModelInstanceActorSourceLookup::Candidate *pCandidate : candidates)
    {
        if (pCandidate == nullptr)
        {
            continue;
        }

        if (pUniqueCandidate == nullptr)
        {
            pUniqueCandidate = pCandidate;
            continue;
        }

        if (pCandidate->id != pUniqueCandidate->id)
        {
            return std::nullopt;
        }
    }

    if (pUniqueCandidate != nullptr)
    {
        return pUniqueCandidate->source;
    }

    return std::nullopt;
}

std::optional<Mm9ResolvedModelInstanceActorSource> findActorSource(
    const Game::OutdoorSceneModelInstance &modelInstance,
    const Mm9ModelInstanceActorSourceLookup *pActorSourceLookup)
{
    if (pActorSourceLookup == nullptr)
    {
        return std::nullopt;
    }

    std::vector<const Mm9ModelInstanceActorSourceLookup::Candidate *> candidates;

    const std::string sourceModel = normalizeMm9ModelInstanceVirtualPath(modelInstance.sourceModel);
    const std::string classKey = normalizeActorKey(modelInstance.sourceClass);
    if (!classKey.empty())
    {
        appendCandidates(candidates, pActorSourceLookup->sourceByActorKey, classKey);
        if (const std::optional<Mm9ResolvedModelInstanceActorSource> source = uniqueResolvedSource(candidates))
        {
            return source;
        }

        candidates.clear();
        for (const std::string &typePictureKey : sourceClassTypePictureKeys(modelInstance.sourceClass))
        {
            appendCandidates(candidates, pActorSourceLookup->sourceByTypePictureKey, typePictureKey);
        }

        if (const std::optional<Mm9ResolvedModelInstanceActorSource> source = uniqueResolvedSource(candidates))
        {
            return source;
        }

        candidates.clear();
        appendCandidates(
            candidates,
            pActorSourceLookup->sourceBySourceModelAndActorKey,
            lookupKey(sourceModel, classKey));
        if (const std::optional<Mm9ResolvedModelInstanceActorSource> source = uniqueResolvedSource(candidates))
        {
            return source;
        }
    }

    const std::string nameKey = normalizeActorKey(modelInstance.sourceName);
    if (!nameKey.empty())
    {
        candidates.clear();
        appendCandidates(candidates, pActorSourceLookup->sourceByActorKey, nameKey);
        if (const std::optional<Mm9ResolvedModelInstanceActorSource> source = uniqueResolvedSource(candidates))
        {
            return source;
        }

        candidates.clear();
        for (const auto &entry : pActorSourceLookup->sourceByActorKey)
        {
            if (actorTokenMatches(nameKey, entry.first))
            {
                for (const Mm9ModelInstanceActorSourceLookup::Candidate &candidate : entry.second)
                {
                    candidates.push_back(&candidate);
                }
            }
        }

        if (const std::optional<Mm9ResolvedModelInstanceActorSource> source = uniqueResolvedSource(candidates))
        {
            return source;
        }
    }

    return std::nullopt;
}

std::string sourceModelAssetPath(const std::string &sourceModel)
{
    std::string value = normalizeMm9ModelInstanceVirtualPath(sourceModel);
    const size_t extension = value.find_last_of('.');
    if (extension != std::string::npos)
    {
        value = value.substr(0, extension);
    }

    if (!value.empty())
    {
        value += ".glb";
    }

    return value;
}

YAML::Node yamlMapValue(const YAML::Node &node, const char *pKey)
{
    if (!node.IsDefined() || !node.IsMap())
    {
        return {};
    }

    for (YAML::const_iterator iterator = node.begin(); iterator != node.end(); ++iterator)
    {
        if (iterator->first.IsScalar() && iterator->first.as<std::string>() == pKey)
        {
            return iterator->second;
        }
    }

    return {};
}

std::string yamlScalarString(const YAML::Node &node)
{
    if (!node.IsDefined() || !node.IsScalar())
    {
        return {};
    }

    try
    {
        return node.as<std::string>();
    }
    catch (const YAML::Exception &)
    {
        return {};
    }
}

struct Mm9ActorSourceLookupCacheEntry
{
    std::string activeWorldId;
    std::filesystem::path registryPhysicalPath;
    std::string actorIdentityMetadataToken;
    std::filesystem::file_time_type lastWriteTime = {};
    uintmax_t fileSize = 0;
    Mm9ModelInstanceActorSourceLookup lookup;
};

std::string actorIdentityTableMetadataToken(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &table)
{
    const std::string virtualPath = "source/data/" + table + ".txt";
    const std::optional<std::filesystem::path> physicalPath =
        assetFileSystem.resolvePhysicalPath(virtualPath);
    if (!physicalPath)
    {
        return virtualPath + ":missing";
    }

    std::error_code metadataError;
    const std::filesystem::file_time_type lastWriteTime =
        std::filesystem::last_write_time(*physicalPath, metadataError);
    const auto writeTimeCount = metadataError
        ? std::filesystem::file_time_type::duration::rep{}
        : lastWriteTime.time_since_epoch().count();

    const uintmax_t fileSize = std::filesystem::file_size(*physicalPath, metadataError);
    return physicalPath->generic_string()
        + ":"
        + std::to_string(writeTimeCount)
        + ":"
        + std::to_string(metadataError ? 0 : fileSize);
}

std::string actorIdentityMetadataToken(const Engine::AssetFileSystem &assetFileSystem)
{
    return actorIdentityTableMetadataToken(assetFileSystem, "ACTOR")
        + "|"
        + actorIdentityTableMetadataToken(assetFileSystem, "MONSTERS");
}

bool actorSourceLookupCacheEntryMatches(
    const Mm9ActorSourceLookupCacheEntry &entry,
    const std::string &activeWorldId,
    const std::filesystem::path &registryPhysicalPath,
    const std::string &actorIdentityMetadataToken,
    const std::filesystem::file_time_type &lastWriteTime,
    uintmax_t fileSize)
{
    return entry.activeWorldId == activeWorldId
        && entry.registryPhysicalPath == registryPhysicalPath
        && entry.actorIdentityMetadataToken == actorIdentityMetadataToken
        && entry.lastWriteTime == lastWriteTime
        && entry.fileSize == fileSize;
}
}

std::string normalizeMm9ModelInstanceVirtualPath(std::string value)
{
    value = trimWhitespaceCopy(value);
    std::replace(value.begin(), value.end(), '\\', '/');

    while (!value.empty() && value.front() == '/')
    {
        value.erase(value.begin());
    }

    value = toLowerCopy(value);

    const std::string extractedModelsPrefix = "mm9/extracted/models/models/";
    const std::string extractedSkinsPrefix = "mm9/extracted/skins/skins/";
    const std::string modelsPrefix = "models/models/";
    const std::string skinsPrefix = "skins/skins/";

    if (value.rfind(extractedModelsPrefix, 0) == 0)
    {
        value = "models/" + value.substr(extractedModelsPrefix.size());
    }
    else if (value.rfind(extractedSkinsPrefix, 0) == 0)
    {
        value = "skins/" + value.substr(extractedSkinsPrefix.size());
    }
    else if (value.rfind(modelsPrefix, 0) == 0)
    {
        value = "models/" + value.substr(modelsPrefix.size());
    }
    else if (value.rfind(skinsPrefix, 0) == 0)
    {
        value = "skins/" + value.substr(skinsPrefix.size());
    }

    if (endsWithCaseInsensitive(value, ".png"))
    {
        value.resize(value.size() - 4);
        value += ".dtx";
    }

    return value;
}

std::string normalizeMm9ModelInstanceImagePath(std::string value)
{
    value = trimWhitespaceCopy(value);
    std::replace(value.begin(), value.end(), '\\', '/');

    while (!value.empty() && value.front() == '/')
    {
        value.erase(value.begin());
    }

    value = toLowerCopy(value);

    const std::string extractedSkinsPrefix = "mm9/extracted/skins/skins/";
    const std::string extractedTexturesPrefix = "mm9/extracted/textures/textures/";
    const std::string skinsPrefix = "skins/skins/";
    const std::string texturesPrefix = "textures/textures/";

    if (value.rfind(extractedSkinsPrefix, 0) == 0)
    {
        value = "skins/" + value.substr(extractedSkinsPrefix.size());
    }
    else if (value.rfind(extractedTexturesPrefix, 0) == 0)
    {
        value = "textures/" + value.substr(extractedTexturesPrefix.size());
    }
    else if (value.rfind(skinsPrefix, 0) == 0)
    {
        value = "skins/" + value.substr(skinsPrefix.size());
    }
    else if (value.rfind(texturesPrefix, 0) == 0)
    {
        value = "textures/" + value.substr(texturesPrefix.size());
    }

    return value;
}

bool mm9ActorFootSoundRequiresResolution(const std::string &footSound)
{
    const std::string key = soundKey(footSound);
    return !key.empty() && key != "0" && key != "none";
}

std::vector<Mm9ResolvedModelInstanceActorSource::ActorSoundReference> resolveMm9ActorFootSoundReferences(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &footSound)
{
    std::vector<Mm9ResolvedModelInstanceActorSource::ActorSoundReference> references;
    const std::string requiredKey = soundKey(footSound);
    if (!mm9ActorFootSoundRequiresResolution(requiredKey))
    {
        return references;
    }

    const std::string footstepDirectory = "source/sounds/ANIMSOUNDS/FOOTSTEPS";
    const std::vector<std::string> entries = assetFileSystem.enumerate(footstepDirectory);
    for (const std::string &entry : entries)
    {
        const std::string entryKey = soundKey(std::filesystem::path(entry).stem().string());
        const bool matches = entryKey == requiredKey || entryKey.rfind(requiredKey, 0) == 0;
        if (!matches)
        {
            continue;
        }

        const std::string sourcePath =
            (std::filesystem::path(footstepDirectory) / entry).generic_string();
        if (!assetFileSystem.resolvePhysicalPath(sourcePath))
        {
            continue;
        }

        Mm9ResolvedModelInstanceActorSource::ActorSoundReference reference = {};
        reference.sourcePath = sourcePath;
        references.push_back(std::move(reference));
    }

    std::sort(
        references.begin(),
        references.end(),
        [](const Mm9ResolvedModelInstanceActorSource::ActorSoundReference &left,
            const Mm9ResolvedModelInstanceActorSource::ActorSoundReference &right)
        {
            return left.sourcePath < right.sourcePath;
        });

    return references;
}

std::vector<std::string> splitMm9ModelInstanceSourceSkins(const std::string &sourceSkin)
{
    std::vector<std::string> skinPaths;
    size_t begin = 0;

    while (begin <= sourceSkin.size())
    {
        const size_t separator = sourceSkin.find(';', begin);
        const size_t end = separator == std::string::npos ? sourceSkin.size() : separator;
        const std::string skinPath = normalizeMm9ModelInstanceVirtualPath(sourceSkin.substr(begin, end - begin));
        if (!skinPath.empty())
        {
            skinPaths.push_back(skinPath);
        }

        if (separator == std::string::npos)
        {
            break;
        }

        begin = separator + 1;
    }

    return skinPaths;
}

std::vector<std::string> splitMm9ModelInstanceSourceSkinImages(const std::string &sourceSkin)
{
    std::vector<std::string> imagePaths;
    size_t begin = 0;

    while (begin <= sourceSkin.size())
    {
        const size_t separator = sourceSkin.find(';', begin);
        const size_t end = separator == std::string::npos ? sourceSkin.size() : separator;
        const std::string imagePath = normalizeMm9ModelInstanceImagePath(sourceSkin.substr(begin, end - begin));
        if (!imagePath.empty())
        {
            imagePaths.push_back(imagePath);
        }

        if (separator == std::string::npos)
        {
            break;
        }

        begin = separator + 1;
    }

    return imagePaths;
}

const Mm9ModelInstanceActorSourceLookup *cachedMm9ModelInstanceActorSourceLookup(
    const Engine::AssetFileSystem &assetFileSystem)
{
    static std::deque<Mm9ActorSourceLookupCacheEntry> cachedLookups;

    const std::optional<std::filesystem::path> registryPhysicalPath =
        assetFileSystem.resolvePhysicalPath("models/model_registry.yml");
    const std::string actorIdentityToken = actorIdentityMetadataToken(assetFileSystem);
    std::filesystem::file_time_type registryLastWriteTime = {};
    uintmax_t registryFileSize = 0;

    if (registryPhysicalPath)
    {
        std::error_code metadataError;
        registryLastWriteTime = std::filesystem::last_write_time(*registryPhysicalPath, metadataError);
        if (metadataError)
        {
            registryLastWriteTime = {};
        }

        registryFileSize = std::filesystem::file_size(*registryPhysicalPath, metadataError);
        if (metadataError)
        {
            registryFileSize = 0;
        }

        for (const Mm9ActorSourceLookupCacheEntry &entry : cachedLookups)
        {
            if (actorSourceLookupCacheEntryMatches(
                    entry,
                    assetFileSystem.getActiveWorldId(),
                    *registryPhysicalPath,
                    actorIdentityToken,
                    registryLastWriteTime,
                    registryFileSize))
            {
                return &entry.lookup;
            }
        }
    }

    const std::optional<std::string> registryText = assetFileSystem.readTextFile("models/model_registry.yml");
    if (!registryText)
    {
        return nullptr;
    }

    YAML::Node rootNode;
    try
    {
        rootNode = YAML::Load(*registryText);
    }
    catch (const std::exception &)
    {
        return nullptr;
    }

    const YAML::Node modelsNode = yamlMapValue(rootNode, "models");
    if (!modelsNode.IsDefined() || !modelsNode.IsSequence())
    {
        return nullptr;
    }

    Mm9ModelInstanceActorSourceLookup lookup = {};
    const ActorIdentityByKey actorIdentityByKey = loadActorIdentityRows(assetFileSystem);

    for (const YAML::Node &modelNode : modelsNode)
    {
        if (!modelNode.IsDefined() || !modelNode.IsMap())
        {
            continue;
        }

        const YAML::Node sourceModelNode = yamlMapValue(modelNode, "source_model");
        YAML::Node bindingsNode = yamlMapValue(modelNode, "skin_bindings");
        if (!bindingsNode.IsDefined() || !bindingsNode.IsSequence())
        {
            bindingsNode = yamlMapValue(modelNode, "variants");
        }

        if (!sourceModelNode.IsDefined()
            || !sourceModelNode.IsScalar()
            || !bindingsNode.IsDefined()
            || !bindingsNode.IsSequence())
        {
            continue;
        }

        const std::string sourceModel = normalizeMm9ModelInstanceVirtualPath(sourceModelNode.as<std::string>());
        if (sourceModel.empty())
        {
            continue;
        }

        for (const YAML::Node &variantNode : bindingsNode)
        {
            if (!variantNode.IsDefined() || !variantNode.IsMap())
            {
                continue;
            }

            const YAML::Node variantIdNode = yamlMapValue(variantNode, "id");
            if (!variantIdNode.IsDefined() || !variantIdNode.IsScalar())
            {
                continue;
            }

            const std::string sourceSkin = joinSourceSkins(yamlMapValue(variantNode, "source_skins"));
            if (sourceSkin.empty())
            {
                continue;
            }

            const YAML::Node actorRowsNode = yamlMapValue(variantNode, "actor_rows");
            if (!actorRowsNode.IsDefined() || !actorRowsNode.IsSequence())
            {
                continue;
            }

            for (const YAML::Node &actorRowNode : actorRowsNode)
            {
                if (!actorRowNode.IsDefined() || !actorRowNode.IsMap())
                {
                    continue;
                }

                const YAML::Node monsterNameNode = yamlMapValue(actorRowNode, "monster_name");
                const YAML::Node typePictureNode = yamlMapValue(actorRowNode, "type_picture");
                if (!monsterNameNode.IsDefined() || !monsterNameNode.IsScalar()
                    || !typePictureNode.IsDefined() || !typePictureNode.IsScalar())
                {
                    continue;
                }

                Mm9ModelInstanceActorSourceLookup::Candidate candidate = {};
                candidate.id = variantIdNode.as<std::string>();
                candidate.source.variantId = candidate.id;
                candidate.source.sourceModel = sourceModel;
                candidate.source.sourceSkin = sourceSkin;
                candidate.source.inferredFromActorClass = true;
                candidate.source.actorRow.table = yamlScalarString(yamlMapValue(actorRowNode, "table"));
                candidate.source.actorRow.row = yamlScalarString(yamlMapValue(actorRowNode, "row"));
                candidate.source.actorRow.number = yamlScalarString(yamlMapValue(actorRowNode, "number"));
                candidate.source.actorRow.monsterName = yamlScalarString(monsterNameNode);
                candidate.source.actorRow.typePicture = yamlScalarString(typePictureNode);
                candidate.source.actorRow.baseName = yamlScalarString(yamlMapValue(actorRowNode, "base_name"));
                enrichActorRowFromIdentityTable(candidate.source.actorRow, actorIdentityByKey);
                candidate.source.actorRow.footSoundReferences =
                    resolveMm9ActorFootSoundReferences(
                        assetFileSystem,
                        candidate.source.actorRow.footSound);

                const std::string actorKey = normalizeActorKey(monsterNameNode.as<std::string>());
                if (!actorKey.empty())
                {
                    lookup.sourceByActorKey[actorKey].push_back(candidate);
                    lookup.sourceBySourceModelAndActorKey[lookupKey(sourceModel, actorKey)].push_back(candidate);
                }

                for (const std::string &typePictureKey : typePictureKeys(typePictureNode.as<std::string>()))
                {
                    lookup.sourceByTypePictureKey[typePictureKey].push_back(candidate);
                }
            }
        }
    }

    if (registryPhysicalPath)
    {
        Mm9ActorSourceLookupCacheEntry entry = {};
        entry.activeWorldId = assetFileSystem.getActiveWorldId();
        entry.registryPhysicalPath = *registryPhysicalPath;
        entry.actorIdentityMetadataToken = actorIdentityToken;
        entry.lastWriteTime = registryLastWriteTime;
        entry.fileSize = registryFileSize;
        entry.lookup = std::move(lookup);
        cachedLookups.push_back(std::move(entry));
        return &cachedLookups.back().lookup;
    }

    cachedLookups.push_back(
        Mm9ActorSourceLookupCacheEntry{
            assetFileSystem.getActiveWorldId(),
            {},
            actorIdentityToken,
            {},
            0,
            std::move(lookup)});
    return &cachedLookups.back().lookup;
}

std::optional<Mm9ModelInstanceActorSourceLookup> loadMm9ModelInstanceActorSourceLookup(
    const Engine::AssetFileSystem &assetFileSystem)
{
    const Mm9ModelInstanceActorSourceLookup *pLookup = cachedMm9ModelInstanceActorSourceLookup(assetFileSystem);
    if (pLookup == nullptr)
    {
        return std::nullopt;
    }

    return *pLookup;
}

Mm9ResolvedModelInstanceActorSource resolveMm9ModelInstanceActorSource(
    const Game::OutdoorSceneModelInstance &modelInstance,
    const Mm9ModelInstanceActorSourceLookup *pActorSourceLookup)
{
    Mm9ResolvedModelInstanceActorSource resolvedSource = {};
    resolvedSource.sourceModel = modelInstance.sourceModel;
    resolvedSource.sourceSkin = modelInstance.sourceSkin;

    if (!splitMm9ModelInstanceSourceSkins(modelInstance.sourceSkin).empty())
    {
        return resolvedSource;
    }

    return findActorSource(modelInstance, pActorSourceLookup).value_or(resolvedSource);
}

bool canResolveMm9ModelInstanceActorSource(
    const Game::OutdoorSceneModelInstance &modelInstance,
    const Mm9ModelInstanceActorSourceLookup *pActorSourceLookup)
{
    if (!splitMm9ModelInstanceSourceSkins(modelInstance.sourceSkin).empty())
    {
        return false;
    }

    return findActorSource(modelInstance, pActorSourceLookup).has_value();
}

std::string mm9ModelInstanceActorVariantAssetPath(
    const std::string &sourceModel,
    const std::string &sourceSkin)
{
    (void)sourceSkin;
    const std::string modelAsset = sourceModelAssetPath(sourceModel);
    if (modelAsset.empty())
    {
        return {};
    }

    return modelAsset;
}
}
