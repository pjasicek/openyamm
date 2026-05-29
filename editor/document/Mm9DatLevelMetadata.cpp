#include "editor/document/Mm9DatLevelMetadata.h"

#include "engine/ImageAssetLoader.h"
#include "game/mm9/Mm9DtxTexture.h"

#include <yaml-cpp/yaml.h>

#include <array>
#include <algorithm>
#include <cstdlib>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iterator>
#include <map>
#include <sstream>
#include <system_error>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Editor
{
namespace
{
std::string scalarString(const YAML::Node &node, const char *key, std::string &errorMessage)
{
    const YAML::Node valueNode = node[key];

    if (!valueNode || valueNode.IsNull())
    {
        errorMessage = std::string("missing required field: ") + key;
        return {};
    }

    if (!valueNode.IsScalar())
    {
        errorMessage = std::string("field must be scalar: ") + key;
        return {};
    }

    return valueNode.as<std::string>();
}

std::string optionalScalarString(const YAML::Node &node, const char *key)
{
    const YAML::Node valueNode = node[key];

    if (!valueNode || valueNode.IsNull())
    {
        return {};
    }

    if (!valueNode.IsScalar())
    {
        return {};
    }

    return valueNode.as<std::string>();
}

std::optional<std::string> optionalNullableString(const YAML::Node &node, const char *key)
{
    const YAML::Node valueNode = node[key];

    if (!valueNode || valueNode.IsNull())
    {
        return std::nullopt;
    }

    if (!valueNode.IsScalar())
    {
        return std::nullopt;
    }

    return valueNode.as<std::string>();
}

bool requireMap(const YAML::Node &node, const char *key, YAML::Node &result, std::string &errorMessage)
{
    result = node[key];

    if (!result || result.IsNull())
    {
        errorMessage = std::string("missing required section: ") + key;
        return false;
    }

    if (!result.IsMap())
    {
        errorMessage = std::string("section must be a map: ") + key;
        return false;
    }

    return true;
}

bool readRequiredString(const YAML::Node &node, const char *key, std::string &value, std::string &errorMessage)
{
    value = scalarString(node, key, errorMessage);
    return errorMessage.empty();
}

template <typename ValueType>
ValueType optionalScalarValue(const YAML::Node &node, const char *key, const ValueType &defaultValue)
{
    const YAML::Node valueNode = node[key];

    if (!valueNode || !valueNode.IsScalar())
    {
        return defaultValue;
    }

    return valueNode.as<ValueType>(defaultValue);
}

bool isHexString(const std::string &text)
{
    for (const char value : text)
    {
        if ((value >= '0' && value <= '9')
            || (value >= 'a' && value <= 'f')
            || (value >= 'A' && value <= 'F'))
        {
            continue;
        }

        return false;
    }

    return true;
}

std::filesystem::path developmentFallbackPath(const std::filesystem::path &path)
{
    std::filesystem::path result;
    bool replaced = false;

    for (const std::filesystem::path &part : path)
    {
        if (!replaced && part == "assets_editor_dev")
        {
            result /= "assets_dev";
            replaced = true;
        }
        else
        {
            result /= part;
        }
    }

    return replaced ? result.lexically_normal() : std::filesystem::path();
}

bool directPathExists(const std::filesystem::path &path)
{
    std::error_code existsError;
    return std::filesystem::exists(path, existsError) && !existsError;
}

bool pathExists(const std::filesystem::path &path)
{
    if (directPathExists(path))
    {
        return true;
    }

    const std::filesystem::path fallbackPath = developmentFallbackPath(path);
    return !fallbackPath.empty() && directPathExists(fallbackPath);
}

std::filesystem::path existingPathOrDevelopmentFallback(const std::filesystem::path &path)
{
    if (directPathExists(path))
    {
        return path;
    }

    const std::filesystem::path fallbackPath = developmentFallbackPath(path);

    if (!fallbackPath.empty() && directPathExists(fallbackPath))
    {
        return fallbackPath;
    }

    return path;
}

bool directoryExists(const std::filesystem::path &path)
{
    std::error_code statusError;
    return std::filesystem::is_directory(path, statusError) && !statusError;
}

size_t countRegularFilesRecursively(const std::filesystem::path &path)
{
    if (!directoryExists(path))
    {
        return 0;
    }

    size_t fileCount = 0;
    std::error_code iteratorError;
    std::filesystem::recursive_directory_iterator iterator(
        path,
        std::filesystem::directory_options::skip_permission_denied,
        iteratorError);
    const std::filesystem::recursive_directory_iterator endIterator;

    while (!iteratorError && iterator != endIterator)
    {
        std::error_code statusError;

        if (iterator->is_regular_file(statusError) && !statusError)
        {
            ++fileCount;
        }

        iterator.increment(iteratorError);
    }

    return fileCount;
}

bool readTextFile(const std::filesystem::path &path, std::string &text)
{
    std::ifstream input(path);

    if (!input)
    {
        return false;
    }

    text.assign(std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>());
    return true;
}

bool readBinaryFile(const std::filesystem::path &path, std::vector<uint8_t> &bytes)
{
    bytes.clear();
    std::ifstream input(path, std::ios::binary);

    if (!input)
    {
        return false;
    }

    input.seekg(0, std::ios::end);
    const std::streamsize size = input.tellg();

    if (size < 0)
    {
        return false;
    }

    input.seekg(0, std::ios::beg);
    bytes.resize(static_cast<size_t>(size));

    if (size == 0)
    {
        return true;
    }

    return input.read(reinterpret_cast<char *>(bytes.data()), size).good();
}

uintmax_t regularFileSizeOrZero(const std::filesystem::path &path)
{
    std::error_code sizeError;
    const uintmax_t size = std::filesystem::file_size(path, sizeError);

    if (sizeError)
    {
        return 0;
    }

    return size;
}

std::filesystem::file_time_type fileWriteTimeOrDefault(const std::filesystem::path &path)
{
    std::error_code timeError;
    const std::filesystem::file_time_type writeTime = std::filesystem::last_write_time(path, timeError);

    if (timeError)
    {
        return {};
    }

    return writeTime;
}

std::string sha256Hex(const std::vector<uint8_t> &bytes);

std::string toLowerAscii(std::string value);

std::unordered_map<std::string, std::vector<std::filesystem::path>> buildMm9SourceDtxIndex(
    const std::filesystem::path &sourceRoot);

std::unordered_map<std::string, std::vector<std::filesystem::path>> buildMm9SourceSpriteIndex(
    const std::filesystem::path &sourceRoot);

bool readFileSha256(const std::filesystem::path &path, std::string &hash)
{
    std::vector<uint8_t> bytes;

    if (!readBinaryFile(path, bytes))
    {
        hash.clear();
        return false;
    }

    hash = sha256Hex(bytes);
    return true;
}

std::string cachePathKey(const std::filesystem::path &path)
{
    std::error_code canonicalError;
    const std::filesystem::path canonicalPath = std::filesystem::weakly_canonical(path, canonicalError);

    if (!canonicalError)
    {
        return canonicalPath.generic_string();
    }

    return path.lexically_normal().generic_string();
}

EditorMm9FileInspectionCacheEntry inspectMm9File(
    const std::filesystem::path &path,
    bool requireHash,
    bool requireDtxHeader,
    EditorMm9MaterialInspectionCache *pCache)
{
    EditorMm9FileInspectionCacheEntry current = {};
    current.exists = pathExists(path);

    if (current.exists)
    {
        current.sizeBytes = regularFileSizeOrZero(path);
        current.lastWriteTime = fileWriteTimeOrDefault(path);
    }

    if (pCache != nullptr)
    {
        const std::string key = cachePathKey(path);
        const auto cachedIt = pCache->filesByPath.find(key);

        if (cachedIt != pCache->filesByPath.end()
            && cachedIt->second.exists == current.exists
            && cachedIt->second.sizeBytes == current.sizeBytes
            && cachedIt->second.lastWriteTime == current.lastWriteTime
            && (!requireHash || cachedIt->second.hashLoaded)
            && (!requireDtxHeader || cachedIt->second.dtxHeaderLoaded))
        {
            return cachedIt->second;
        }

        EditorMm9FileInspectionCacheEntry updated = current;

        if (updated.exists && requireHash)
        {
            updated.hashLoaded = readFileSha256(path, updated.sha256);
            ++pCache->fileHashReadCount;
        }

        if (updated.exists && requireDtxHeader)
        {
            std::string headerErrorMessage;
            updated.dtxHeader = readMm9DtxHeader(path, headerErrorMessage);
            updated.dtxHeaderLoaded = updated.dtxHeader.has_value();
            ++pCache->dtxHeaderReadCount;
        }

        pCache->filesByPath[key] = updated;
        return updated;
    }

    if (current.exists && requireHash)
    {
        current.hashLoaded = readFileSha256(path, current.sha256);
    }

    if (current.exists && requireDtxHeader)
    {
        std::string headerErrorMessage;
        current.dtxHeader = readMm9DtxHeader(path, headerErrorMessage);
        current.dtxHeaderLoaded = current.dtxHeader.has_value();
    }

    return current;
}

const std::unordered_map<std::string, std::vector<std::filesystem::path>> &mm9SourceDtxIndex(
    const std::filesystem::path &sourceRoot,
    EditorMm9MaterialInspectionCache *pCache,
    std::unordered_map<std::string, std::vector<std::filesystem::path>> &scratchIndex)
{
    const std::filesystem::path actualSourceRoot = existingPathOrDevelopmentFallback(sourceRoot);

    if (pCache == nullptr)
    {
        scratchIndex = buildMm9SourceDtxIndex(actualSourceRoot);
        return scratchIndex;
    }

    if (!pCache->sourceDtxIndexBuilt || pCache->sourceDtxIndexRoot != actualSourceRoot)
    {
        pCache->sourceDtxIndex = buildMm9SourceDtxIndex(actualSourceRoot);
        pCache->sourceDtxIndexRoot = actualSourceRoot;
        pCache->sourceDtxIndexBuilt = true;
        ++pCache->sourceDtxIndexBuildCount;
    }

    return pCache->sourceDtxIndex;
}

const std::vector<std::filesystem::path> *findMm9DtxSourceCandidates(
    const std::unordered_map<std::string, std::vector<std::filesystem::path>> &sourceDtxIndex,
    const std::string &sourceDtxKey)
{
    const auto exactIterator = sourceDtxIndex.find(sourceDtxKey);

    if (exactIterator != sourceDtxIndex.end())
    {
        return &exactIterator->second;
    }

    const std::string basenameKey =
        toLowerAscii(std::filesystem::path(sourceDtxKey).filename().generic_string());

    if (basenameKey.empty() || basenameKey == sourceDtxKey)
    {
        return nullptr;
    }

    const auto basenameIterator = sourceDtxIndex.find(basenameKey);

    if (basenameIterator == sourceDtxIndex.end())
    {
        return nullptr;
    }

    return &basenameIterator->second;
}

void compareFileFreshness(
    const std::filesystem::path &sourcePath,
    const std::filesystem::path &cachePath,
    bool &freshnessKnown,
    bool &cacheNewerThanSource,
    bool &cacheOlderThanSource)
{
    freshnessKnown = false;
    cacheNewerThanSource = false;
    cacheOlderThanSource = false;

    std::error_code sourceTimeError;
    std::error_code cacheTimeError;
    const std::filesystem::file_time_type sourceTime =
        std::filesystem::last_write_time(sourcePath, sourceTimeError);
    const std::filesystem::file_time_type cacheTime =
        std::filesystem::last_write_time(cachePath, cacheTimeError);

    if (sourceTimeError || cacheTimeError)
    {
        return;
    }

    freshnessKnown = true;
    cacheNewerThanSource = cacheTime >= sourceTime;
    cacheOlderThanSource = cacheTime < sourceTime;
}

uint32_t rotateRight(uint32_t value, uint32_t bits)
{
    return (value >> bits) | (value << (32 - bits));
}

std::string sha256Hex(const std::vector<uint8_t> &bytes)
{
    static constexpr std::array<uint32_t, 64> RoundConstants = {{
        0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
        0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
        0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
        0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
        0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
        0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
        0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
        0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
        0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
        0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
        0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
        0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
        0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
        0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
        0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
        0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
    }};

    std::array<uint32_t, 8> hash = {{
        0x6a09e667,
        0xbb67ae85,
        0x3c6ef372,
        0xa54ff53a,
        0x510e527f,
        0x9b05688c,
        0x1f83d9ab,
        0x5be0cd19,
    }};

    std::vector<uint8_t> padded = bytes;
    padded.push_back(0x80);

    while ((padded.size() % 64) != 56)
    {
        padded.push_back(0);
    }

    const uint64_t bitLength = static_cast<uint64_t>(bytes.size()) * 8;

    for (int shift = 56; shift >= 0; shift -= 8)
    {
        padded.push_back(static_cast<uint8_t>((bitLength >> shift) & 0xff));
    }

    for (size_t chunkOffset = 0; chunkOffset < padded.size(); chunkOffset += 64)
    {
        std::array<uint32_t, 64> words = {};

        for (size_t index = 0; index < 16; ++index)
        {
            const size_t byteOffset = chunkOffset + index * 4;
            words[index] =
                (uint32_t(padded[byteOffset]) << 24)
                | (uint32_t(padded[byteOffset + 1]) << 16)
                | (uint32_t(padded[byteOffset + 2]) << 8)
                | uint32_t(padded[byteOffset + 3]);
        }

        for (size_t index = 16; index < 64; ++index)
        {
            const uint32_t s0 =
                rotateRight(words[index - 15], 7) ^ rotateRight(words[index - 15], 18) ^ (words[index - 15] >> 3);
            const uint32_t s1 =
                rotateRight(words[index - 2], 17) ^ rotateRight(words[index - 2], 19) ^ (words[index - 2] >> 10);
            words[index] = words[index - 16] + s0 + words[index - 7] + s1;
        }

        uint32_t a = hash[0];
        uint32_t b = hash[1];
        uint32_t c = hash[2];
        uint32_t d = hash[3];
        uint32_t e = hash[4];
        uint32_t f = hash[5];
        uint32_t g = hash[6];
        uint32_t h = hash[7];

        for (size_t index = 0; index < 64; ++index)
        {
            const uint32_t s1 = rotateRight(e, 6) ^ rotateRight(e, 11) ^ rotateRight(e, 25);
            const uint32_t choice = (e & f) ^ ((~e) & g);
            const uint32_t temp1 = h + s1 + choice + RoundConstants[index] + words[index];
            const uint32_t s0 = rotateRight(a, 2) ^ rotateRight(a, 13) ^ rotateRight(a, 22);
            const uint32_t majority = (a & b) ^ (a & c) ^ (b & c);
            const uint32_t temp2 = s0 + majority;

            h = g;
            g = f;
            f = e;
            e = d + temp1;
            d = c;
            c = b;
            b = a;
            a = temp1 + temp2;
        }

        hash[0] += a;
        hash[1] += b;
        hash[2] += c;
        hash[3] += d;
        hash[4] += e;
        hash[5] += f;
        hash[6] += g;
        hash[7] += h;
    }

    std::ostringstream output;
    output << std::hex << std::setfill('0');

    for (uint32_t word : hash)
    {
        output << std::setw(8) << word;
    }

    return output.str();
}

void addSourceDatHashIssue(
    std::vector<std::string> &issues,
    const std::filesystem::path &levelPhysicalPath,
    const EditorMm9DatLevelMetadata &metadata)
{
    if (metadata.source.dat.empty())
    {
        return;
    }

    const std::filesystem::path resolvedPath =
        existingPathOrDevelopmentFallback(resolveMm9DatLevelRelativePath(levelPhysicalPath, metadata.source.dat));

    if (!pathExists(resolvedPath))
    {
        return;
    }

    std::vector<uint8_t> bytes;

    if (!readBinaryFile(resolvedPath, bytes))
    {
        issues.push_back("MM9 level source DAT could not be read for hashing: " + resolvedPath.generic_string());
        return;
    }

    const std::string actualHash = sha256Hex(bytes);

    if (actualHash != metadata.source.contentHash)
    {
        issues.push_back(
            "MM9 level source DAT hash mismatch: stored=" + metadata.source.contentHash
            + " actual=" + actualHash
            + " path=" + resolvedPath.generic_string());
    }
}

void addMissingPathIssue(
    std::vector<std::string> &issues,
    const std::string &label,
    const std::filesystem::path &levelPhysicalPath,
    const std::string &relativePath)
{
    if (relativePath.empty())
    {
        issues.push_back("MM9 level " + label + " path is empty.");
        return;
    }

    const std::filesystem::path resolvedPath =
        existingPathOrDevelopmentFallback(resolveMm9DatLevelRelativePath(levelPhysicalPath, relativePath));

    if (!pathExists(resolvedPath))
    {
        issues.push_back("MM9 level " + label + " is missing: " + resolvedPath.generic_string());
    }
}

bool pathHasSegment(const std::filesystem::path &path, const std::string &segment)
{
    const std::string lowerSegment = toLowerAscii(segment);

    for (const std::filesystem::path &pathPart : path.lexically_normal())
    {
        if (toLowerAscii(pathPart.generic_string()) == lowerSegment)
        {
            return true;
        }
    }

    return false;
}

EditorMm9DocumentPathStatus makeMm9DocumentPathStatus(
    const std::string &label,
    const std::string &role,
    const std::filesystem::path &levelPhysicalPath,
    const std::string &relativePath,
    bool sourceReadOnly,
    bool generated,
    bool authored,
    bool compatibilityDerived)
{
    EditorMm9DocumentPathStatus status = {};
    status.label = label;
    status.role = role;
    status.relativePath = relativePath;
    status.resolvedPath = resolveMm9DatLevelRelativePath(levelPhysicalPath, relativePath).generic_string();
    status.exists = pathExists(status.resolvedPath);
    status.sourceReadOnly = sourceReadOnly;
    status.generated = generated;
    status.authored = authored;
    status.compatibilityDerived = compatibilityDerived;
    return status;
}

EditorMm9DocumentPathStatus makeMm9DocumentAbsolutePathStatus(
    const std::string &label,
    const std::string &role,
    const std::filesystem::path &physicalPath,
    bool sourceReadOnly,
    bool generated,
    bool authored,
    bool compatibilityDerived)
{
    EditorMm9DocumentPathStatus status = {};
    status.label = label;
    status.role = role;
    status.relativePath = physicalPath.filename().generic_string();
    status.resolvedPath = physicalPath.lexically_normal().generic_string();
    status.exists = pathExists(physicalPath);
    status.sourceReadOnly = sourceReadOnly;
    status.generated = generated;
    status.authored = authored;
    status.compatibilityDerived = compatibilityDerived;
    return status;
}

void addSidecarKindIssue(
    std::vector<std::string> &issues,
    const std::string &label,
    const std::filesystem::path &levelPhysicalPath,
    const std::string &relativePath,
    const std::string &expectedKind)
{
    if (relativePath.empty())
    {
        return;
    }

    const std::filesystem::path resolvedPath =
        existingPathOrDevelopmentFallback(resolveMm9DatLevelRelativePath(levelPhysicalPath, relativePath));

    if (!pathExists(resolvedPath))
    {
        return;
    }

    std::string text;

    if (!readTextFile(resolvedPath, text))
    {
        issues.push_back("MM9 level " + label + " could not be read: " + resolvedPath.generic_string());
        return;
    }

    YAML::Node root;

    try
    {
        root = YAML::Load(text);
    }
    catch (const YAML::Exception &exception)
    {
        issues.push_back(
            "MM9 level " + label + " could not be parsed: " + resolvedPath.generic_string()
            + ": " + exception.what());
        return;
    }

    if (!root || !root.IsMap())
    {
        issues.push_back("MM9 level " + label + " root is not a map: " + resolvedPath.generic_string());
        return;
    }

    const std::string actualKind = root["kind"].as<std::string>(std::string());

    if (actualKind != expectedKind)
    {
        issues.push_back(
            "MM9 level " + label + " has kind '" + actualKind + "', expected '" + expectedKind
            + "': " + resolvedPath.generic_string());
    }
}

std::optional<YAML::Node> loadYamlMapFromText(
    const std::string &text,
    const std::string &label,
    std::string &errorMessage)
{
    YAML::Node root;

    try
    {
        root = YAML::Load(text);
    }
    catch (const YAML::Exception &exception)
    {
        errorMessage = "could not parse " + label + ": " + std::string(exception.what());
        return std::nullopt;
    }

    if (!root || !root.IsMap())
    {
        errorMessage = label + " root must be a map.";
        return std::nullopt;
    }

    return root;
}

bool validateSidecarKind(
    const YAML::Node &root,
    const std::string &expectedKind,
    const std::string &label,
    std::string &errorMessage)
{
    const std::string actualKind = root["kind"].as<std::string>(std::string());

    if (actualKind != expectedKind)
    {
        errorMessage = label + " kind must be " + expectedKind + ", got '" + actualKind + "'";
        return false;
    }

    return true;
}

EditorMm9DatWorldModelRoles parseDatWorldModelRoles(const YAML::Node &rolesNode)
{
    EditorMm9DatWorldModelRoles roles = {};

    if (!rolesNode || !rolesNode.IsMap())
    {
        return roles;
    }

    roles.visible = optionalScalarValue<bool>(rolesNode, "visible", false);
    roles.terrain = optionalScalarValue<bool>(rolesNode, "terrain", false);
    roles.physicsBsp = optionalScalarValue<bool>(rolesNode, "physics_bsp", false);
    roles.visBsp = optionalScalarValue<bool>(rolesNode, "vis_bsp", false);
    roles.sky = optionalScalarValue<bool>(rolesNode, "sky", false);
    roles.water = optionalScalarValue<bool>(rolesNode, "water", false);
    roles.triggerOrVolume = optionalScalarValue<bool>(rolesNode, "trigger_or_volume", false);
    roles.movable = optionalScalarValue<bool>(rolesNode, "movable", false);
    return roles;
}

EditorMm9Vec3 parseVec3Sequence(const YAML::Node &node)
{
    EditorMm9Vec3 value = {};

    if (!node || !node.IsSequence() || node.size() < 3)
    {
        return value;
    }

    value.x = node[0].as<float>(0.0f);
    value.y = node[1].as<float>(0.0f);
    value.z = node[2].as<float>(0.0f);
    return value;
}

std::optional<size_t> optionalNullableSize(const YAML::Node &node, const char *key)
{
    const YAML::Node valueNode = node[key];

    if (!valueNode || valueNode.IsNull() || !valueNode.IsScalar())
    {
        return std::nullopt;
    }

    return valueNode.as<size_t>();
}

std::string toLowerAscii(std::string value)
{
    for (char &character : value)
    {
        if (character >= 'A' && character <= 'Z')
        {
            character = static_cast<char>(character - 'A' + 'a');
        }
    }

    return value;
}

std::string normalizedTextureKey(const std::string &value)
{
    std::string normalized = value;

    for (char &character : normalized)
    {
        if (character == '\\')
        {
            character = '/';
        }
    }

    return toLowerAscii(normalized);
}

bool endsWithCaseInsensitive(const std::string &value, const std::string &suffix)
{
    if (value.size() < suffix.size())
    {
        return false;
    }

    return toLowerAscii(value.substr(value.size() - suffix.size())) == toLowerAscii(suffix);
}

bool startsWithCaseInsensitive(const std::string &value, const std::string &prefix)
{
    if (value.size() < prefix.size())
    {
        return false;
    }

    return toLowerAscii(value.substr(0, prefix.size())) == toLowerAscii(prefix);
}

std::string mm9DtxSourceKeyFromReference(const std::string &relativeOrSourcePath)
{
    std::string normalized = normalizedTextureKey(relativeOrSourcePath);

    while (!normalized.empty() && normalized.front() == '/')
    {
        normalized.erase(normalized.begin());
    }

    const std::array<std::pair<const char *, const char *>, 9> prefixes = {{
        {"mm9/extracted/textures/textures/", "textures/"},
        {"mm9/extracted/skins/skins/", "skins/"},
        {"mm9/extracted/spritetextures/spritetextures/", "sprite_textures/"},
        {"textures/textures/", "textures/"},
        {"skins/skins/", "skins/"},
        {"spritetextures/spritetextures/", "sprite_textures/"},
        {"textures/", "textures/"},
        {"skins/", "skins/"},
        {"spritetextures/", "sprite_textures/"}
    }};

    for (const std::pair<const char *, const char *> &prefix : prefixes)
    {
        const std::string sourcePrefix = prefix.first;

        if (normalized.rfind(sourcePrefix, 0) == 0)
        {
            return std::string(prefix.second) + normalized.substr(sourcePrefix.size());
        }
    }

    return normalized;
}

std::string mm9SpriteSourceKeyFromReference(const std::string &relativeOrSourcePath)
{
    std::string normalized = normalizedTextureKey(relativeOrSourcePath);

    while (!normalized.empty() && normalized.front() == '/')
    {
        normalized.erase(normalized.begin());
    }

    const std::array<std::pair<const char *, const char *>, 5> prefixes = {{
        {"mm9/extracted/sprites/sprites/", "sprites/"},
        {"sprites/sprites/", "sprites/"},
        {"sprites/", "sprites/"},
        {"mm9/extracted/skins/skins/", "skins/"},
        {"skins/", "skins/"}
    }};

    for (const std::pair<const char *, const char *> &prefix : prefixes)
    {
        const std::string sourcePrefix = prefix.first;

        if (normalized.rfind(sourcePrefix, 0) == 0)
        {
            return std::string(prefix.second) + normalized.substr(sourcePrefix.size());
        }
    }

    return normalized;
}

std::string mm9DtxSourceKeyFromSourceFile(
    const std::filesystem::path &sourceRoot,
    const std::filesystem::path &familyPath,
    const char *pFamilyId,
    const std::filesystem::path &sourcePath)
{
    std::error_code errorCode;
    std::filesystem::path relativePath = std::filesystem::relative(sourcePath, familyPath, errorCode);

    if (errorCode)
    {
        relativePath = sourcePath.lexically_relative(sourceRoot);
    }

    return normalizedTextureKey(std::string(pFamilyId) + "/" + relativePath.generic_string());
}

std::string mm9SpriteSourceKeyFromSourceFile(
    const std::filesystem::path &sourceRoot,
    const std::filesystem::path &familyPath,
    const std::filesystem::path &sourcePath)
{
    std::error_code errorCode;
    std::filesystem::path relativePath = std::filesystem::relative(sourcePath, familyPath, errorCode);

    if (errorCode)
    {
        relativePath = sourcePath.lexically_relative(sourceRoot);
    }

    return normalizedTextureKey("sprites/" + relativePath.generic_string());
}

bool isMm9SpriteReference(const std::string &sourceTexture)
{
    const std::string normalized = normalizedTextureKey(sourceTexture);
    return endsWithCaseInsensitive(normalized, ".spr")
        || normalized.rfind("sprites/", 0) == 0
        || normalized.rfind("mm9/extracted/sprites/sprites/", 0) == 0;
}

uint16_t readLittleUint16(const std::vector<uint8_t> &bytes, size_t offset)
{
    return static_cast<uint16_t>(bytes[offset])
        | static_cast<uint16_t>(static_cast<uint16_t>(bytes[offset + 1]) << 8);
}

uint32_t readLittleUint32(const std::vector<uint8_t> &bytes, size_t offset)
{
    return static_cast<uint32_t>(bytes[offset])
        | (static_cast<uint32_t>(bytes[offset + 1]) << 8)
        | (static_cast<uint32_t>(bytes[offset + 2]) << 16)
        | (static_cast<uint32_t>(bytes[offset + 3]) << 24);
}

bool readMm9SpriteTextureRefs(
    const std::filesystem::path &physicalPath,
    std::vector<std::string> &textureRefs)
{
    textureRefs.clear();

    std::vector<uint8_t> bytes;

    if (!readBinaryFile(physicalPath, bytes) || bytes.size() < 20)
    {
        return false;
    }

    const uint32_t textureCount = readLittleUint32(bytes, 0);
    size_t offset = 20;
    textureRefs.reserve(textureCount);

    for (uint32_t index = 0; index < textureCount; ++index)
    {
        if (offset + 2 > bytes.size())
        {
            textureRefs.clear();
            return false;
        }

        const uint16_t textLength = readLittleUint16(bytes, offset);
        offset += 2;

        if (offset + textLength > bytes.size())
        {
            textureRefs.clear();
            return false;
        }

        textureRefs.emplace_back(
            reinterpret_cast<const char *>(bytes.data() + offset),
            reinterpret_cast<const char *>(bytes.data() + offset + textLength));
        offset += textLength;
    }

    return offset == bytes.size();
}

std::string trimAsciiWhitespace(const std::string &value)
{
    size_t begin = 0;
    while (begin < value.size()
        && (value[begin] == ' ' || value[begin] == '\t' || value[begin] == '\r' || value[begin] == '\n'))
    {
        ++begin;
    }

    size_t end = value.size();
    while (end > begin
        && (value[end - 1] == ' ' || value[end - 1] == '\t' || value[end - 1] == '\r' || value[end - 1] == '\n'))
    {
        --end;
    }

    return value.substr(begin, end - begin);
}

std::optional<std::string> parseRawObjectJsonStringScalar(const std::string &valueJson)
{
    const std::string trimmed = trimAsciiWhitespace(valueJson);
    if (trimmed.size() < 2 || trimmed.front() != '"' || trimmed.back() != '"')
    {
        return std::nullopt;
    }

    std::string value;
    value.reserve(trimmed.size() - 2);
    for (size_t index = 1; index + 1 < trimmed.size(); ++index)
    {
        char character = trimmed[index];
        if (character != '\\')
        {
            value.push_back(character);
            continue;
        }

        if (index + 2 >= trimmed.size())
        {
            return std::nullopt;
        }

        const char escaped = trimmed[++index];
        switch (escaped)
        {
        case '"':
        case '\\':
        case '/':
            value.push_back(escaped);
            break;
        case 'b':
            value.push_back('\b');
            break;
        case 'f':
            value.push_back('\f');
            break;
        case 'n':
            value.push_back('\n');
            break;
        case 'r':
            value.push_back('\r');
            break;
        case 't':
            value.push_back('\t');
            break;
        default:
            return std::nullopt;
        }
    }

    return value;
}

std::optional<float> parseRawObjectJsonFloatScalar(const std::string &valueJson)
{
    const std::string trimmed = trimAsciiWhitespace(valueJson);
    if (trimmed.empty())
    {
        return std::nullopt;
    }

    char *pEnd = nullptr;
    const float value = std::strtof(trimmed.c_str(), &pEnd);
    if (pEnd == trimmed.c_str() || *pEnd != '\0')
    {
        return std::nullopt;
    }

    return value;
}

std::optional<int> parseRawObjectJsonIntScalar(const std::string &valueJson)
{
    const std::string trimmed = trimAsciiWhitespace(valueJson);
    if (trimmed.empty())
    {
        return std::nullopt;
    }

    char *pEnd = nullptr;
    const long value = std::strtol(trimmed.c_str(), &pEnd, 10);
    if (pEnd == trimmed.c_str() || *pEnd != '\0')
    {
        return std::nullopt;
    }

    return static_cast<int>(value);
}

std::vector<float> parseRawObjectJsonNumberList(const std::string &valueJson)
{
    const std::string trimmed = trimAsciiWhitespace(valueJson);
    std::vector<float> values;
    if (trimmed.size() < 2 || trimmed.front() != '[' || trimmed.back() != ']')
    {
        return values;
    }

    const char *pCursor = trimmed.c_str() + 1;
    const char *pEndList = trimmed.c_str() + trimmed.size() - 1;
    while (pCursor < pEndList)
    {
        while (pCursor < pEndList && (*pCursor == ' ' || *pCursor == '\t' || *pCursor == '\r' || *pCursor == '\n'))
        {
            ++pCursor;
        }

        if (pCursor >= pEndList)
        {
            break;
        }

        char *pEndNumber = nullptr;
        const float value = std::strtof(pCursor, &pEndNumber);
        if (pEndNumber == pCursor)
        {
            values.clear();
            return values;
        }

        values.push_back(value);
        pCursor = pEndNumber;

        while (pCursor < pEndList && (*pCursor == ' ' || *pCursor == '\t' || *pCursor == '\r' || *pCursor == '\n'))
        {
            ++pCursor;
        }

        if (pCursor < pEndList)
        {
            if (*pCursor != ',')
            {
                values.clear();
                return values;
            }
            ++pCursor;
        }
    }

    return values;
}

std::optional<std::string> decodedRawObjectStringValue(const EditorMm9RawObjectProperty &property)
{
    if (!property.decoded || property.code != 0 || property.valueJson.empty())
    {
        return std::nullopt;
    }

    if (const std::optional<std::string> value = parseRawObjectJsonStringScalar(property.valueJson))
    {
        return trimAsciiWhitespace(*value);
    }

    try
    {
        const YAML::Node node = YAML::Load(property.valueJson);

        if (!node || !node.IsScalar())
        {
            return std::nullopt;
        }

        return trimAsciiWhitespace(node.as<std::string>());
    }
    catch (const YAML::Exception &)
    {
        return std::nullopt;
    }
}

std::optional<float> yamlScalarFloatValue(const YAML::Node &node)
{
    if (!node || !node.IsScalar())
    {
        return std::nullopt;
    }

    try
    {
        return node.as<float>();
    }
    catch (const YAML::Exception &)
    {
        return std::nullopt;
    }
}

std::optional<int> yamlScalarIntValue(const YAML::Node &node)
{
    if (!node || !node.IsScalar())
    {
        return std::nullopt;
    }

    try
    {
        return node.as<int>();
    }
    catch (const YAML::Exception &)
    {
        return std::nullopt;
    }
}

std::optional<std::string> yamlScalarStringValue(const YAML::Node &node)
{
    if (!node || !node.IsScalar())
    {
        return std::nullopt;
    }

    try
    {
        return node.as<std::string>();
    }
    catch (const YAML::Exception &)
    {
        return std::nullopt;
    }
}

std::vector<float> yamlNumberListValue(const YAML::Node &node)
{
    std::vector<float> values;
    if (!node || !node.IsSequence())
    {
        return values;
    }

    values.reserve(node.size());
    for (const YAML::Node &entry : node)
    {
        const std::optional<float> value = yamlScalarFloatValue(entry);
        if (!value)
        {
            values.clear();
            return values;
        }

        values.push_back(*value);
    }

    return values;
}

std::vector<std::string> yamlStringListValue(const YAML::Node &node)
{
    std::vector<std::string> values;
    if (!node || !node.IsSequence())
    {
        return values;
    }

    values.reserve(node.size());
    for (const YAML::Node &entry : node)
    {
        const std::optional<std::string> value = yamlScalarStringValue(entry);
        if (!value)
        {
            values.clear();
            return values;
        }

        values.push_back(*value);
    }

    return values;
}

bool rawObjectPropertyNameLooksVec3(const std::string &name)
{
    return name == "Pos"
        || name == "Rotation"
        || name == "LightColor"
        || name == "InnerColor"
        || name == "OuterColor";
}

std::optional<Game::Mm9LightSourceProperty> buildMm9LightSourceProperty(
    const EditorMm9RawObjectProperty &property)
{
    if (!property.decoded || property.valueJson.empty())
    {
        return std::nullopt;
    }

    if (property.code == 0)
    {
        const std::optional<std::string> value = parseRawObjectJsonStringScalar(property.valueJson);
        if (value)
        {
            return Game::mm9LightStringProperty(property.name, trimAsciiWhitespace(*value));
        }
    }

    if (property.code == 5)
    {
        if (const std::optional<int> value = parseRawObjectJsonIntScalar(property.valueJson))
        {
            return Game::mm9LightBooleanProperty(property.name, *value != 0);
        }

        if (const std::optional<float> value = parseRawObjectJsonFloatScalar(property.valueJson))
        {
            return Game::mm9LightBooleanProperty(property.name, *value != 0.0f);
        }
    }

    if (property.code == 4)
    {
        if (const std::optional<int> value = parseRawObjectJsonIntScalar(property.valueJson))
        {
            return Game::mm9LightIntegerProperty(property.name, *value);
        }

        if (const std::optional<float> value = parseRawObjectJsonFloatScalar(property.valueJson))
        {
            return Game::mm9LightIntegerProperty(property.name, static_cast<int>(*value));
        }
    }

    if (const std::optional<float> numberValue = parseRawObjectJsonFloatScalar(property.valueJson))
    {
        return Game::mm9LightNumberProperty(property.name, *numberValue);
    }

    const std::vector<float> numberValues = parseRawObjectJsonNumberList(property.valueJson);
    if (!numberValues.empty())
    {
        if (numberValues.size() >= 3 && rawObjectPropertyNameLooksVec3(property.name))
        {
            return Game::mm9LightVec3Property(
                property.name,
                {numberValues[0], numberValues[1], numberValues[2]});
        }

        return Game::mm9LightNumberListProperty(property.name, numberValues);
    }

    YAML::Node node;
    try
    {
        node = YAML::Load(property.valueJson);
    }
    catch (const YAML::Exception &)
    {
        return std::nullopt;
    }

    if (!node)
    {
        return std::nullopt;
    }

    if (node.IsScalar())
    {
        if (property.code == 0)
        {
            const std::optional<std::string> value = yamlScalarStringValue(node);
            if (!value)
            {
                return std::nullopt;
            }

            return Game::mm9LightStringProperty(property.name, trimAsciiWhitespace(*value));
        }

        if (property.code == 5)
        {
            const std::optional<int> value = yamlScalarIntValue(node);
            if (!value)
            {
                return std::nullopt;
            }

            return Game::mm9LightBooleanProperty(property.name, *value != 0);
        }

        const std::optional<float> numberValue = yamlScalarFloatValue(node);
        if (!numberValue)
        {
            return std::nullopt;
        }

        if (property.code == 4)
        {
            return Game::mm9LightIntegerProperty(property.name, static_cast<int>(*numberValue));
        }

        return Game::mm9LightNumberProperty(property.name, *numberValue);
    }

    if (node.IsSequence())
    {
        const std::vector<float> numberValues = yamlNumberListValue(node);
        if (!numberValues.empty())
        {
            if (numberValues.size() >= 3 && rawObjectPropertyNameLooksVec3(property.name))
            {
                return Game::mm9LightVec3Property(
                    property.name,
                    {numberValues[0], numberValues[1], numberValues[2]});
            }

            return Game::mm9LightNumberListProperty(property.name, numberValues);
        }

        const std::vector<std::string> stringValues = yamlStringListValue(node);
        if (!stringValues.empty())
        {
            return Game::mm9LightStringListProperty(property.name, stringValues);
        }
    }

    return std::nullopt;
}

std::optional<YAML::Node> decodedRawObjectYamlValue(const EditorMm9RawObjectProperty &property)
{
    if (!property.decoded || property.valueJson.empty())
    {
        return std::nullopt;
    }

    try
    {
        return YAML::Load(property.valueJson);
    }
    catch (const YAML::Exception &)
    {
        return std::nullopt;
    }
}

std::optional<Game::Mm9DatVec3> decodedRawObjectVec3Value(const EditorMm9RawObjectProperty &property)
{
    const std::vector<float> fastValues = parseRawObjectJsonNumberList(property.valueJson);
    if (fastValues.size() >= 3)
    {
        return Game::Mm9DatVec3{fastValues[0], fastValues[1], fastValues[2]};
    }

    const std::optional<YAML::Node> node = decodedRawObjectYamlValue(property);
    if (!node || !node->IsSequence())
    {
        return std::nullopt;
    }

    const std::vector<float> values = yamlNumberListValue(*node);
    if (values.size() < 3)
    {
        return std::nullopt;
    }

    return Game::Mm9DatVec3{values[0], values[1], values[2]};
}

std::optional<float> decodedRawObjectFloatValue(const EditorMm9RawObjectProperty &property)
{
    if (const std::optional<float> value = parseRawObjectJsonFloatScalar(property.valueJson))
    {
        return value;
    }

    const std::optional<YAML::Node> node = decodedRawObjectYamlValue(property);
    if (!node || !node->IsScalar())
    {
        return std::nullopt;
    }

    return yamlScalarFloatValue(*node);
}

std::optional<int> decodedRawObjectIntValue(const EditorMm9RawObjectProperty &property)
{
    if (const std::optional<int> value = parseRawObjectJsonIntScalar(property.valueJson))
    {
        return value;
    }

    const std::optional<YAML::Node> node = decodedRawObjectYamlValue(property);
    if (!node || !node->IsScalar())
    {
        return std::nullopt;
    }

    return yamlScalarIntValue(*node);
}

std::optional<bool> decodedRawObjectBoolValue(const EditorMm9RawObjectProperty &property)
{
    const std::optional<int> value = decodedRawObjectIntValue(property);
    if (!value)
    {
        return std::nullopt;
    }

    return *value != 0;
}

std::string normalizedMm9SourceAssetKey(const std::string &sourceFamily, const std::string &sourceValue)
{
    std::string normalized = normalizedTextureKey(trimAsciiWhitespace(sourceValue));

    while (!normalized.empty() && normalized.front() == '/')
    {
        normalized.erase(normalized.begin());
    }

    const std::array<std::pair<const char *, const char *>, 17> prefixes = {{
        {"mm9/extracted/models/models/", "models"},
        {"mm9/extracted/skins/skins/", "skins"},
        {"mm9/extracted/textures/textures/", "textures"},
        {"mm9/extracted/spritetextures/spritetextures/", "sprite_textures"},
        {"mm9/extracted/sounds/sounds/", "sounds"},
        {"mm9/extracted/voices/voices/", "voices"},
        {"mm9/extracted/scripts/scripts/", "scripts"},
        {"mm9/extracted/sprites/sprites/", "sprites"},
        {"models/", "models"},
        {"skins/", "skins"},
        {"textures/", "textures"},
        {"spritetextures/", "sprite_textures"},
        {"sprite_textures/", "sprite_textures"},
        {"sounds/", "sounds"},
        {"voices/", "voices"},
        {"scripts/", "scripts"},
        {"sprites/", "sprites"}
    }};

    for (const std::pair<const char *, const char *> &prefix : prefixes)
    {
        if (sourceFamily == prefix.second && normalized.rfind(prefix.first, 0) == 0)
        {
            return normalized.substr(std::strlen(prefix.first));
        }
    }

    return normalized;
}

std::string inferMm9RawObjectAssetFamily(
    const std::string &propertyName,
    const std::string &sourceValue);

std::vector<std::string> splitMm9AssetReferenceList(const std::string &sourceValue)
{
    std::vector<std::string> values;
    size_t begin = 0;
    const std::array<std::string, 8> familyPrefixes = {{
        "models/",
        "skins/",
        "textures/",
        "spritetextures/",
        "sounds/",
        "voices/",
        "scripts/",
        "sprites/"
    }};
    const std::array<std::string, 9> extensions = {{
        ".abc",
        ".ltb",
        ".dtx",
        ".wav",
        ".mp3",
        ".scr",
        ".inc",
        ".spr",
        ".txt"
    }};

    const auto appendUnique =
        [&values](const std::string &candidate)
        {
            const std::string value = trimAsciiWhitespace(candidate);

            if (value.empty())
            {
                return;
            }

            if (std::find(values.begin(), values.end(), value) == values.end())
            {
                values.push_back(value);
            }
        };

    const auto appendEmbeddedReferences =
        [&appendUnique, &familyPrefixes, &extensions](const std::string &segment)
        {
            const std::string normalizedSegment = normalizedTextureKey(segment);
            size_t searchOffset = 0;

            while (searchOffset < normalizedSegment.size())
            {
                size_t bestPrefixPos = std::string::npos;

                for (const std::string &prefix : familyPrefixes)
                {
                    const size_t prefixPos = normalizedSegment.find(prefix, searchOffset);

                    if (prefixPos != std::string::npos
                        && (bestPrefixPos == std::string::npos || prefixPos < bestPrefixPos))
                    {
                        bestPrefixPos = prefixPos;
                    }
                }

                if (bestPrefixPos == std::string::npos)
                {
                    break;
                }

                size_t bestExtensionEnd = std::string::npos;

                for (const std::string &extension : extensions)
                {
                    const size_t extensionPos = normalizedSegment.find(extension, bestPrefixPos);

                    if (extensionPos != std::string::npos)
                    {
                        const size_t extensionEnd = extensionPos + extension.size();

                        if (bestExtensionEnd == std::string::npos || extensionEnd < bestExtensionEnd)
                        {
                            bestExtensionEnd = extensionEnd;
                        }
                    }
                }

                if (bestExtensionEnd == std::string::npos)
                {
                    break;
                }

                appendUnique(segment.substr(bestPrefixPos, bestExtensionEnd - bestPrefixPos));
                searchOffset = bestExtensionEnd;
            }
        };

    while (begin <= sourceValue.size())
    {
        const size_t end = sourceValue.find(';', begin);
        const std::string value =
            trimAsciiWhitespace(sourceValue.substr(begin, end == std::string::npos ? std::string::npos : end - begin));

        if (!value.empty())
        {
            if (!inferMm9RawObjectAssetFamily("", value).empty())
            {
                appendUnique(value);
            }
            else
            {
                appendEmbeddedReferences(value);
            }
        }

        if (end == std::string::npos)
        {
            break;
        }

        begin = end + 1;
    }

    return values;
}

std::string inferMm9RawObjectAssetFamily(
    const std::string &propertyName,
    const std::string &sourceValue)
{
    const std::string lowerProperty = toLowerAscii(propertyName);
    std::string normalizedValue = normalizedTextureKey(trimAsciiWhitespace(sourceValue));

    while (!normalizedValue.empty() && normalizedValue.front() == '/')
    {
        normalizedValue.erase(normalizedValue.begin());
    }

    const std::filesystem::path sourcePath(normalizedValue);
    const std::string extension = toLowerAscii(sourcePath.extension().generic_string());

    if (extension == ".abc" || extension == ".ltb")
    {
        return "models";
    }

    if (extension == ".dtx")
    {
        if (normalizedValue.rfind("textures/", 0) == 0)
        {
            return "textures";
        }

        if (normalizedValue.rfind("skins/", 0) == 0 || lowerProperty == "skin")
        {
            return "skins";
        }

        if (normalizedValue.rfind("spritetextures/", 0) == 0
            || normalizedValue.rfind("sprite_textures/", 0) == 0)
        {
            return "sprite_textures";
        }

        return "textures";
    }

    if (extension == ".wav" || extension == ".mp3")
    {
        if (normalizedValue.rfind("voices/", 0) == 0)
        {
            return "voices";
        }

        return "sounds";
    }

    if (extension == ".scr" || extension == ".inc" || lowerProperty == "scriptname")
    {
        return "scripts";
    }

    if (extension == ".spr")
    {
        return "sprites";
    }

    return {};
}

bool isMm9RawObjectAssetReferenceRequired(
    const std::string &sourceClass,
    const std::string &propertyName,
    const std::string &sourceFamily)
{
    const std::string lowerClass = toLowerAscii(sourceClass);
    const std::string lowerProperty = toLowerAscii(propertyName);

    if (lowerClass == "worldproperties" && sourceFamily == "textures")
    {
        return lowerProperty != "environmentmap"
            && lowerProperty != "softsky"
            && lowerProperty != "panskytexture";
    }

    return true;
}

bool isMm9WorldPropertiesBuiltinSkyTextureReference(
    const EditorMm9RawObjectAssetReferenceStatus &status)
{
    if (toLowerAscii(status.sourceClass) != "worldproperties" || status.sourceFamily != "textures")
    {
        return false;
    }

    const std::string lowerProperty = toLowerAscii(status.propertyName);
    return lowerProperty == "environmentmap"
        || lowerProperty == "softsky"
        || lowerProperty == "panskytexture";
}

std::unordered_map<std::string, std::vector<std::filesystem::path>> buildMm9SourceFamilyIndex(
    const std::filesystem::path &sourceRoot,
    const std::string &sourceFamily)
{
    std::unordered_map<std::string, std::vector<std::filesystem::path>> index;
    const std::filesystem::path familyPath = sourceRoot / sourceFamily;
    std::error_code errorCode;

    if (!std::filesystem::exists(familyPath, errorCode))
    {
        return index;
    }

    std::filesystem::recursive_directory_iterator iterator(
        familyPath,
        std::filesystem::directory_options::skip_permission_denied,
        errorCode);
    const std::filesystem::recursive_directory_iterator end;

    while (!errorCode && iterator != end)
    {
        const std::filesystem::directory_entry entry = *iterator;

        if (entry.is_regular_file(errorCode))
        {
            std::error_code relativeError;
            std::filesystem::path relativePath = std::filesystem::relative(entry.path(), familyPath, relativeError);

            if (relativeError)
            {
                relativePath = entry.path().lexically_relative(familyPath);
            }

            const std::filesystem::path normalizedPath = entry.path().lexically_normal();
            index[normalizedTextureKey(relativePath.generic_string())].push_back(normalizedPath);
            index[normalizedTextureKey(entry.path().filename().generic_string())].push_back(normalizedPath);
        }

        iterator.increment(errorCode);
    }

    for (std::pair<const std::string, std::vector<std::filesystem::path>> &entry : index)
    {
        std::sort(entry.second.begin(), entry.second.end());
        entry.second.erase(std::unique(entry.second.begin(), entry.second.end()), entry.second.end());
    }

    return index;
}

const std::vector<std::filesystem::path> *findMm9SourceFamilyCandidates(
    const std::unordered_map<std::string, std::vector<std::filesystem::path>> &familyIndex,
    const std::string &sourceFamily,
    const std::string &normalizedKey)
{
    const auto exact = familyIndex.find(normalizedKey);

    if (exact != familyIndex.end())
    {
        return &exact->second;
    }

    const std::string fileNameKey =
        normalizedTextureKey(std::filesystem::path(normalizedKey).filename().generic_string());

    if (fileNameKey.empty() || fileNameKey == normalizedKey)
    {
        return nullptr;
    }

    const auto byFileName = familyIndex.find(fileNameKey);

    if (byFileName == familyIndex.end())
    {
        if (sourceFamily == "sounds" && normalizedKey.rfind("ambient/bird", 0) == 0)
        {
            const std::string suffix = normalizedKey.substr(std::strlen("ambient/bird"));
            const std::string alternateKey = "ambient/birds/birds" + suffix;
            const auto alternate = familyIndex.find(alternateKey);

            if (alternate != familyIndex.end())
            {
                return &alternate->second;
            }
        }

        return nullptr;
    }

    return &byFileName->second;
}

struct Mm9SourceAssetAliasOverride
{
    std::string sourceFamily;
    std::string requestedKey;
    std::string targetKey;
    std::vector<std::string> mapIds;
    std::vector<size_t> objectIndexes;
    std::vector<std::string> properties;
};

std::vector<std::string> parseMm9StringSequence(const YAML::Node &node)
{
    std::vector<std::string> values;

    if (!node || !node.IsSequence())
    {
        return values;
    }

    values.reserve(node.size());

    for (const YAML::Node &entryNode : node)
    {
        if (entryNode.IsScalar())
        {
            values.push_back(entryNode.as<std::string>());
        }
    }

    return values;
}

std::vector<size_t> parseMm9SizeSequence(const YAML::Node &node)
{
    std::vector<size_t> values;

    if (!node || !node.IsSequence())
    {
        return values;
    }

    values.reserve(node.size());

    for (const YAML::Node &entryNode : node)
    {
        if (entryNode.IsScalar())
        {
            values.push_back(entryNode.as<size_t>(0));
        }
    }

    return values;
}

std::vector<Mm9SourceAssetAliasOverride> loadMm9SourceAssetAliasOverrides(
    const std::filesystem::path &levelPhysicalPath,
    const EditorMm9DatLevelMetadata *pMetadata)
{
    std::vector<Mm9SourceAssetAliasOverride> aliases;

    if (pMetadata == nullptr
        || !pMetadata->sidecars.sourceAssetAliases.has_value()
        || pMetadata->sidecars.sourceAssetAliases->empty())
    {
        return aliases;
    }

    const std::filesystem::path aliasesPath =
        existingPathOrDevelopmentFallback(
            resolveMm9DatLevelRelativePath(levelPhysicalPath, pMetadata->sidecars.sourceAssetAliases.value()));
    std::string aliasesText;

    if (!readTextFile(aliasesPath, aliasesText))
    {
        return aliases;
    }

    YAML::Node root;

    try
    {
        root = YAML::Load(aliasesText);
    }
    catch (const YAML::Exception &)
    {
        return aliases;
    }

    if (!root || !root.IsMap() || optionalScalarString(root, "kind") != "mm9_source_asset_aliases")
    {
        return aliases;
    }

    const YAML::Node aliasNodes = root["aliases"];

    if (!aliasNodes || !aliasNodes.IsSequence())
    {
        return aliases;
    }

    aliases.reserve(aliasNodes.size());

    for (const YAML::Node &aliasNode : aliasNodes)
    {
        if (!aliasNode.IsMap())
        {
            continue;
        }

        const std::string sourceFamily =
            optionalScalarValue<std::string>(aliasNode, "source_family", std::string());
        const std::string requested = optionalScalarValue<std::string>(aliasNode, "requested", std::string());
        const std::string resolved = optionalScalarValue<std::string>(aliasNode, "resolved", std::string());

        if (sourceFamily.empty() || requested.empty() || resolved.empty())
        {
            continue;
        }

        Mm9SourceAssetAliasOverride alias = {};
        alias.sourceFamily = sourceFamily;
        alias.requestedKey = normalizedMm9SourceAssetKey(sourceFamily, requested);
        alias.targetKey = normalizedMm9SourceAssetKey(sourceFamily, resolved);

        const YAML::Node scopeNode = aliasNode["scope"];

        if (scopeNode && scopeNode.IsMap())
        {
            alias.mapIds = parseMm9StringSequence(scopeNode["maps"]);
            alias.objectIndexes = parseMm9SizeSequence(scopeNode["object_indexes"]);
            alias.properties = parseMm9StringSequence(scopeNode["properties"]);

            for (std::string &property : alias.properties)
            {
                property = toLowerAscii(property);
            }
        }

        aliases.push_back(std::move(alias));
    }

    return aliases;
}

bool mm9SourceAssetAliasMatches(
    const Mm9SourceAssetAliasOverride &alias,
    const EditorMm9DatLevelMetadata *pMetadata,
    const EditorMm9RawObjectAssetReferenceStatus &status)
{
    if (alias.sourceFamily != status.sourceFamily || alias.requestedKey != status.normalizedKey)
    {
        return false;
    }

    if (!alias.mapIds.empty())
    {
        if (pMetadata == nullptr)
        {
            return false;
        }

        const auto mapId = std::find(alias.mapIds.begin(), alias.mapIds.end(), pMetadata->mapId);

        if (mapId == alias.mapIds.end())
        {
            return false;
        }
    }

    if (!alias.objectIndexes.empty())
    {
        const auto objectIndex =
            std::find(alias.objectIndexes.begin(), alias.objectIndexes.end(), status.sourceObjectIndex);

        if (objectIndex == alias.objectIndexes.end())
        {
            return false;
        }
    }

    if (!alias.properties.empty())
    {
        const std::string propertyName = toLowerAscii(status.propertyName);
        const auto property = std::find(alias.properties.begin(), alias.properties.end(), propertyName);

        if (property == alias.properties.end())
        {
            return false;
        }
    }

    return true;
}

bool mm9SourceAssetAliasMapScopeMatches(
    const Mm9SourceAssetAliasOverride &alias,
    const EditorMm9DatLevelMetadata *pMetadata)
{
    if (alias.mapIds.empty())
    {
        return true;
    }

    if (pMetadata == nullptr)
    {
        return false;
    }

    const auto mapId = std::find(alias.mapIds.begin(), alias.mapIds.end(), pMetadata->mapId);
    return mapId != alias.mapIds.end();
}

bool mm9MaterialSourceAssetAliasMatches(
    const Mm9SourceAssetAliasOverride &alias,
    const EditorMm9DatLevelMetadata *pMetadata,
    const std::string &sourceDtxKey)
{
    if (alias.sourceFamily != "textures"
        || alias.requestedKey != normalizedMm9SourceAssetKey("textures", sourceDtxKey))
    {
        return false;
    }

    if (!mm9SourceAssetAliasMapScopeMatches(alias, pMetadata))
    {
        return false;
    }

    return alias.objectIndexes.empty() && alias.properties.empty();
}

bool isMm9DefaultMaterialTextureKey(const std::string &textureKey)
{
    return textureKey == "default";
}

bool mm9DatWorldModelRendersInDefaultView(const EditorMm9DatWorldModelSummary &model)
{
    const bool visualCandidate =
        model.roles.visible
        || model.roles.terrain
        || model.roles.sky
        || model.roles.water
        || model.roles.physicsBsp
        || model.roles.movable;
    const bool hiddenHelper =
        model.roles.visBsp
        || model.roles.triggerOrVolume;

    return visualCandidate && !hiddenHelper;
}

std::string mm9DtxSourceKeyFromTextureAliasTarget(const std::string &targetKey)
{
    if (targetKey.empty())
    {
        return {};
    }

    if (targetKey.rfind("textures/", 0) == 0)
    {
        return targetKey;
    }

    return "textures/" + targetKey;
}

std::unordered_map<std::string, std::vector<std::filesystem::path>> buildMm9SourceDtxIndex(
    const std::filesystem::path &sourceRoot)
{
    std::unordered_map<std::string, std::vector<std::filesystem::path>> index;
    const std::array<std::pair<const char *, const char *>, 3> families = {{
        {"textures", "textures"},
        {"skins", "skins"},
        {"sprite_textures", "sprite_textures"}
    }};

    for (const std::pair<const char *, const char *> &family : families)
    {
        const std::filesystem::path familyPath = sourceRoot / family.first;
        std::error_code errorCode;

        if (!std::filesystem::exists(familyPath, errorCode))
        {
            continue;
        }

        std::filesystem::recursive_directory_iterator iterator(
            familyPath,
            std::filesystem::directory_options::skip_permission_denied,
            errorCode);
        const std::filesystem::recursive_directory_iterator end;

        while (!errorCode && iterator != end)
        {
            const std::filesystem::directory_entry entry = *iterator;

            if (entry.is_regular_file(errorCode)
                && endsWithCaseInsensitive(entry.path().filename().generic_string(), ".dtx"))
            {
                const std::string key =
                    mm9DtxSourceKeyFromSourceFile(sourceRoot, familyPath, family.second, entry.path());
                const std::filesystem::path normalizedPath = entry.path().lexically_normal();
                index[key].push_back(normalizedPath);
                index[normalizedTextureKey(entry.path().filename().generic_string())].push_back(normalizedPath);
            }

            iterator.increment(errorCode);
        }
    }

    for (std::pair<const std::string, std::vector<std::filesystem::path>> &entry : index)
    {
        std::sort(entry.second.begin(), entry.second.end());
    }

    return index;
}

std::unordered_map<std::string, std::vector<std::filesystem::path>> buildMm9SourceSpriteIndex(
    const std::filesystem::path &sourceRoot)
{
    std::unordered_map<std::string, std::vector<std::filesystem::path>> index;
    const std::filesystem::path spritesPath = sourceRoot / "sprites";
    std::error_code errorCode;

    if (!std::filesystem::exists(spritesPath, errorCode))
    {
        return index;
    }

    std::filesystem::recursive_directory_iterator iterator(
        spritesPath,
        std::filesystem::directory_options::skip_permission_denied,
        errorCode);
    const std::filesystem::recursive_directory_iterator end;

    while (!errorCode && iterator != end)
    {
        const std::filesystem::directory_entry entry = *iterator;

        if (entry.is_regular_file(errorCode)
            && endsWithCaseInsensitive(entry.path().filename().generic_string(), ".spr"))
        {
            const std::filesystem::path normalizedPath = entry.path().lexically_normal();
            const std::string key = mm9SpriteSourceKeyFromSourceFile(sourceRoot, spritesPath, normalizedPath);
            index[key].push_back(normalizedPath);
        }

        iterator.increment(errorCode);
    }

    for (std::pair<const std::string, std::vector<std::filesystem::path>> &entry : index)
    {
        std::sort(entry.second.begin(), entry.second.end());
    }

    return index;
}

std::filesystem::path resolveMm9MaterialPhysicalPath(
    const std::filesystem::path &levelPhysicalPath,
    const std::string &relativeOrSourcePath)
{
    if (relativeOrSourcePath.empty())
    {
        return {};
    }

    const std::filesystem::path rawPath(relativeOrSourcePath);

    if (rawPath.is_absolute())
    {
        return rawPath.lexically_normal();
    }

    const std::filesystem::path relativeToLevel =
        (levelPhysicalPath.parent_path() / rawPath).lexically_normal();
    const std::filesystem::path actualRelativeToLevel =
        existingPathOrDevelopmentFallback(relativeToLevel);

    if (directPathExists(actualRelativeToLevel))
    {
        return actualRelativeToLevel;
    }

    const std::filesystem::path sourceRoot =
        existingPathOrDevelopmentFallback((levelPhysicalPath.parent_path() / "../source").lexically_normal());
    const std::string normalized = relativeOrSourcePath;

    const std::string textureExtractedPrefix = "mm9/extracted/TEXTURES/TEXTURES/";
    const std::string skinExtractedPrefix = "mm9/extracted/SKINS/SKINS/";
    const std::string spriteExtractedPrefix = "mm9/extracted/SPRITES/SPRITES/";
    const std::string spriteTextureExtractedPrefix =
        "mm9/extracted/SPRITETEXTURES/SPRITETEXTURES/";

    if (startsWithCaseInsensitive(normalized, textureExtractedPrefix))
    {
        return (sourceRoot / "textures" / normalized.substr(textureExtractedPrefix.size())).lexically_normal();
    }

    if (startsWithCaseInsensitive(normalized, skinExtractedPrefix))
    {
        return (sourceRoot / "skins" / normalized.substr(skinExtractedPrefix.size())).lexically_normal();
    }

    if (startsWithCaseInsensitive(normalized, spriteExtractedPrefix))
    {
        return (sourceRoot / "sprites" / normalized.substr(spriteExtractedPrefix.size())).lexically_normal();
    }

    if (startsWithCaseInsensitive(normalized, spriteTextureExtractedPrefix))
    {
        return (
            sourceRoot
            / "sprite_textures"
            / normalized.substr(spriteTextureExtractedPrefix.size())).lexically_normal();
    }

    if (startsWithCaseInsensitive(normalized, "TEXTURES\\") || startsWithCaseInsensitive(normalized, "TEXTURES/"))
    {
        return (sourceRoot / "textures" / normalized.substr(9)).lexically_normal();
    }

    if (startsWithCaseInsensitive(normalized, "SKINS\\") || startsWithCaseInsensitive(normalized, "SKINS/"))
    {
        return (sourceRoot / "skins" / normalized.substr(6)).lexically_normal();
    }

    if (startsWithCaseInsensitive(normalized, "SPRITES\\") || startsWithCaseInsensitive(normalized, "SPRITES/"))
    {
        return (sourceRoot / "sprites" / normalized.substr(8)).lexically_normal();
    }

    return relativeToLevel;
}

std::filesystem::path resolveMm9MaterialCachePath(
    const std::filesystem::path &levelPhysicalPath,
    const std::string &relativePath)
{
    if (relativePath.empty())
    {
        return {};
    }

    const std::filesystem::path path(relativePath);

    if (path.is_absolute())
    {
        return path.lexically_normal();
    }

    return (levelPhysicalPath.parent_path() / path).lexically_normal();
}

std::filesystem::path resolveMm9EventScriptSourcePath(
    const std::filesystem::path &levelPhysicalPath,
    const std::string &sourcePath)
{
    if (sourcePath.empty())
    {
        return {};
    }

    const std::filesystem::path path(sourcePath);

    if (path.is_absolute())
    {
        return path.lexically_normal();
    }

    return existingPathOrDevelopmentFallback(
        (levelPhysicalPath.parent_path() / "../source/scripts" / path).lexically_normal());
}

template <typename ValueType>
ValueType readLittleEndianValue(const std::vector<uint8_t> &bytes, size_t offset)
{
    ValueType value = {};
    std::memcpy(&value, bytes.data() + offset, sizeof(ValueType));
    return value;
}

std::vector<EditorMm9DatWorldHistogramEntry> parseHistogramEntries(const YAML::Node &node)
{
    std::vector<EditorMm9DatWorldHistogramEntry> entries;

    if (!node || !node.IsMap())
    {
        return entries;
    }

    entries.reserve(node.size());

    for (YAML::const_iterator it = node.begin(); it != node.end(); ++it)
    {
        EditorMm9DatWorldHistogramEntry entry = {};
        entry.key = it->first.as<int>(0);
        entry.count = it->second.as<size_t>(0);
        entries.push_back(entry);
    }

    std::sort(
        entries.begin(),
        entries.end(),
        [](const EditorMm9DatWorldHistogramEntry &left, const EditorMm9DatWorldHistogramEntry &right)
        {
            return left.key < right.key;
        });

    return entries;
}

bool parseRawObjectProperties(
    const YAML::Node &objectNode,
    EditorMm9RawObject &rawObject,
    std::string &errorMessage)
{
    const YAML::Node propertiesNode = objectNode["properties"];

    if (!propertiesNode)
    {
        return true;
    }

    if (!propertiesNode.IsSequence())
    {
        errorMessage = "raw object properties must be a sequence";
        return false;
    }

    rawObject.properties.reserve(propertiesNode.size());

    for (const YAML::Node &propertyNode : propertiesNode)
    {
        if (!propertyNode.IsMap())
        {
            errorMessage = "raw object property entry must be a map";
            return false;
        }

        EditorMm9RawObjectProperty property = {};
        property.name = optionalScalarValue<std::string>(propertyNode, "name", std::string());
        property.code = optionalScalarValue<int>(propertyNode, "code", 0);
        property.flags = optionalScalarValue<int>(propertyNode, "flags", 0);
        property.declaredDataLength = optionalScalarValue<size_t>(propertyNode, "declared_data_length", 0);
        property.consumedDataLength = optionalScalarValue<size_t>(propertyNode, "consumed_data_length", 0);
        property.decoded = optionalScalarValue<bool>(propertyNode, "decoded", false);
        property.rawHex = optionalScalarValue<std::string>(propertyNode, "raw_hex", std::string());
        property.valueJson = optionalScalarValue<std::string>(propertyNode, "value_json", std::string());
        rawObject.properties.push_back(std::move(property));
    }

    return true;
}

const std::array<const char *, 14> &requiredSourceAssetFamilies()
{
    static const std::array<const char *, 14> Families = {{
        "worlds",
        "textures",
        "skins",
        "models",
        "scripts",
        "rude",
        "data",
        "sounds",
        "voices",
        "sprites",
        "sprite_textures",
        "art",
        "localart",
        "clientfx",
    }};

    return Families;
}

bool isRequiredSourceAssetFamily(const std::string &id)
{
    const std::array<const char *, 14> &families = requiredSourceAssetFamilies();
    const auto found = std::find_if(
        families.begin(),
        families.end(),
        [&id](const char *familyId)
        {
            return id == familyId;
        });

    return found != families.end();
}
}

std::optional<EditorMm9DatLevelMetadata> loadMm9DatLevelMetadataFromText(
    const std::string &text,
    std::string &errorMessage)
{
    errorMessage.clear();

    YAML::Node root;

    try
    {
        root = YAML::Load(text);
    }
    catch (const YAML::Exception &exception)
    {
        errorMessage = "could not parse MM9 DAT level YAML: " + std::string(exception.what());
        return std::nullopt;
    }

    if (!root || !root.IsMap())
    {
        errorMessage = "MM9 DAT level YAML root must be a map.";
        return std::nullopt;
    }

    EditorMm9DatLevelMetadata metadata = {};
    metadata.formatVersion = root["format_version"].as<int>(0);

    if (!readRequiredString(root, "kind", metadata.kind, errorMessage))
    {
        return std::nullopt;
    }

    if (metadata.kind != "mm9_level")
    {
        errorMessage = "unsupported level kind: " + metadata.kind;
        return std::nullopt;
    }

    if (!readRequiredString(root, "map_id", metadata.mapId, errorMessage)
        || !readRequiredString(root, "display_name", metadata.displayName, errorMessage))
    {
        return std::nullopt;
    }

    YAML::Node sourceNode;
    YAML::Node runtimeNode;
    YAML::Node sidecarsNode;
    YAML::Node scriptsNode;
    YAML::Node compatibilityNode;

    if (!requireMap(root, "source", sourceNode, errorMessage)
        || !requireMap(root, "runtime", runtimeNode, errorMessage)
        || !requireMap(root, "sidecars", sidecarsNode, errorMessage)
        || !requireMap(root, "scripts", scriptsNode, errorMessage)
        || !requireMap(root, "compatibility", compatibilityNode, errorMessage))
    {
        return std::nullopt;
    }

    if (!readRequiredString(sourceNode, "dat", metadata.source.dat, errorMessage)
        || !readRequiredString(sourceNode, "manifest", metadata.source.manifest, errorMessage)
        || !readRequiredString(sourceNode, "original_dat", metadata.source.originalDat, errorMessage)
        || !readRequiredString(sourceNode, "source_game", metadata.source.sourceGame, errorMessage)
        || !readRequiredString(sourceNode, "content_hash", metadata.source.contentHash, errorMessage))
    {
        return std::nullopt;
    }

    metadata.source.datVersion = sourceNode["dat_version"].as<int>(0);

    if (!readRequiredString(runtimeNode, "world_backend", metadata.runtime.worldBackend, errorMessage)
        || !readRequiredString(runtimeNode, "classification", metadata.runtime.classification, errorMessage)
        || !readRequiredString(
            runtimeNode,
            "classification_confidence",
            metadata.runtime.classificationConfidence,
            errorMessage)
        || !readRequiredString(runtimeNode, "visibility", metadata.runtime.visibility, errorMessage)
        || !readRequiredString(runtimeNode, "collision", metadata.runtime.collision, errorMessage)
        || !readRequiredString(runtimeNode, "render", metadata.runtime.render, errorMessage))
    {
        return std::nullopt;
    }

    metadata.runtime.sky = runtimeNode["sky"].as<bool>(false);

    if (!readRequiredString(sidecarsNode, "dat_world", metadata.sidecars.datWorld, errorMessage)
        || !readRequiredString(sidecarsNode, "raw_objects", metadata.sidecars.rawObjects, errorMessage)
        || !readRequiredString(sidecarsNode, "materials", metadata.sidecars.materials, errorMessage)
        || !readRequiredString(sidecarsNode, "events", metadata.sidecars.events, errorMessage))
    {
        return std::nullopt;
    }

    metadata.sidecars.sceneCompat = optionalNullableString(sidecarsNode, "scene_compat");
    metadata.sidecars.sourceMetadataCompat = optionalNullableString(sidecarsNode, "source_metadata_compat");
    metadata.sidecars.sourceAssetAliases = optionalNullableString(sidecarsNode, "source_asset_aliases");
    metadata.sidecars.bspCompat = optionalNullableString(sidecarsNode, "bsp_compat");
    metadata.sidecars.geometryCompat = optionalNullableString(sidecarsNode, "geometry_compat");
    metadata.sidecars.modelAssetsCompat = optionalNullableString(sidecarsNode, "model_assets_compat");
    metadata.sidecars.odmCompat = optionalNullableString(sidecarsNode, "odm_compat");
    metadata.sidecars.blvCompat = optionalNullableString(sidecarsNode, "blv_compat");

    if (!readRequiredString(scriptsNode, "level", metadata.scripts.level, errorMessage))
    {
        return std::nullopt;
    }

    metadata.scripts.scriptIr = optionalScalarString(scriptsNode, "script_ir");

    if (!readRequiredString(
            compatibilityNode,
            "legacy_target_format",
            metadata.compatibility.legacyTargetFormat,
            errorMessage))
    {
        return std::nullopt;
    }

    metadata.compatibility.generatedOdmBlvAreDerived =
        compatibilityNode["generated_odm_blv_are_derived"].as<bool>(false);

    if (metadata.formatVersion <= 0)
    {
        errorMessage = "MM9 DAT level format_version must be positive.";
        return std::nullopt;
    }

    if (metadata.source.datVersion != 66)
    {
        errorMessage = "MM9 DAT level source.dat_version must be 66.";
        return std::nullopt;
    }

    if (metadata.runtime.worldBackend != "dat_world")
    {
        errorMessage = "MM9 DAT level runtime.world_backend must be dat_world.";
        return std::nullopt;
    }

    if (!metadata.compatibility.generatedOdmBlvAreDerived)
    {
        errorMessage = "MM9 DAT level compatibility.generated_odm_blv_are_derived must be true.";
        return std::nullopt;
    }

    return metadata;
}

std::optional<EditorMm9DatWorldSidecar> loadMm9DatWorldSidecarFromText(
    const std::string &text,
    std::string &errorMessage)
{
    errorMessage.clear();
    const std::optional<YAML::Node> root = loadYamlMapFromText(text, "MM9 DAT world sidecar", errorMessage);

    if (!root || !validateSidecarKind(*root, "mm9_dat_world", "MM9 DAT world sidecar", errorMessage))
    {
        return std::nullopt;
    }

    EditorMm9DatWorldSidecar sidecar = {};
    sidecar.formatVersion = optionalScalarValue<int>(*root, "format_version", 0);
    sidecar.kind = optionalScalarValue<std::string>(*root, "kind", std::string());
    sidecar.mapId = optionalScalarValue<std::string>(*root, "map_id", std::string());
    sidecar.sourceDat = optionalScalarValue<std::string>(*root, "source_dat", std::string());
    sidecar.sourceHash = optionalScalarValue<std::string>(*root, "source_hash", std::string());
    sidecar.datVersion = optionalScalarValue<int>(*root, "dat_version", 0);

    const YAML::Node coordinateSystemNode = (*root)["coordinate_system"];
    if (coordinateSystemNode && coordinateSystemNode.IsMap())
    {
        sidecar.coordinateSystem.source =
            optionalScalarValue<std::string>(coordinateSystemNode, "source", std::string());
        sidecar.coordinateSystem.scale = optionalScalarValue<float>(coordinateSystemNode, "scale", 0.0f);

        const YAML::Node mappingNode = coordinateSystemNode["openyamm_mapping"];
        if (mappingNode && mappingNode.IsSequence())
        {
            sidecar.coordinateSystem.openYammMapping.reserve(mappingNode.size());

            for (const YAML::Node &mappingEntryNode : mappingNode)
            {
                sidecar.coordinateSystem.openYammMapping.push_back(mappingEntryNode.as<std::string>());
            }
        }
    }

    const YAML::Node worldInfoNode = (*root)["world_info"];
    if (worldInfoNode && worldInfoNode.IsMap())
    {
        sidecar.worldInfo.propertyString =
            optionalScalarValue<std::string>(worldInfoNode, "property_string", std::string());
        sidecar.worldInfo.lightMapGridSize =
            optionalScalarValue<float>(worldInfoNode, "light_map_grid_size", 0.0f);
        sidecar.worldInfo.extentsMinLt = parseVec3Sequence(worldInfoNode["extents_min_lt"]);
        sidecar.worldInfo.extentsMaxLt = parseVec3Sequence(worldInfoNode["extents_max_lt"]);
    }

    const YAML::Node classificationNode = (*root)["classification"];
    if (classificationNode && classificationNode.IsMap())
    {
        sidecar.classification =
            optionalScalarValue<std::string>(classificationNode, "recommendation", std::string());
        sidecar.classificationConfidence =
            optionalScalarValue<std::string>(classificationNode, "confidence", std::string());
        sidecar.classificationReason =
            optionalScalarValue<std::string>(classificationNode, "reason", std::string());
    }

    const YAML::Node totalsNode = (*root)["totals"];
    if (totalsNode && totalsNode.IsMap())
    {
        sidecar.totals.worldModelCount = optionalScalarValue<size_t>(totalsNode, "world_model_count", 0);
        sidecar.totals.objectCount = optionalScalarValue<size_t>(totalsNode, "object_count", 0);
        sidecar.totals.sourcePolyCount = optionalScalarValue<size_t>(totalsNode, "source_poly_count", 0);
        sidecar.totals.surfaceCount = optionalScalarValue<size_t>(totalsNode, "surface_count", 0);
        sidecar.totals.userPortalCount = optionalScalarValue<size_t>(totalsNode, "user_portal_count", 0);
        sidecar.totals.leafCount = optionalScalarValue<size_t>(totalsNode, "leaf_count", 0);
        sidecar.totals.leafReferenceCount = optionalScalarValue<size_t>(totalsNode, "leaf_reference_count", 0);
        sidecar.totals.invalidLeafReferenceCount =
            optionalScalarValue<size_t>(totalsNode, "invalid_leaf_reference_count", 0);
    }

    const YAML::Node worldModelsNode = (*root)["world_models"];
    if (!worldModelsNode || !worldModelsNode.IsSequence())
    {
        errorMessage = "MM9 DAT world sidecar world_models must be a sequence";
        return std::nullopt;
    }

    sidecar.worldModels.reserve(worldModelsNode.size());

    for (const YAML::Node &modelNode : worldModelsNode)
    {
        if (!modelNode.IsMap())
        {
            errorMessage = "MM9 DAT world model entry must be a map";
            return std::nullopt;
        }

        EditorMm9DatWorldModelSummary model = {};
        model.sourceModelIndex = optionalScalarValue<size_t>(modelNode, "source_model_index", 0);
        model.sourceName = optionalScalarValue<std::string>(modelNode, "source_name", std::string());
        model.kind = optionalScalarValue<std::string>(modelNode, "kind", std::string());
        model.worldInfoFlags = optionalScalarValue<uint32_t>(modelNode, "world_info_flags", 0);
        model.pointCount = optionalScalarValue<size_t>(modelNode, "point_count", 0);
        model.planeCount = optionalScalarValue<size_t>(modelNode, "plane_count", 0);
        model.surfaceCount = optionalScalarValue<size_t>(modelNode, "surface_count", 0);
        model.polyCount = optionalScalarValue<size_t>(modelNode, "poly_count", 0);
        model.leafCount = optionalScalarValue<size_t>(modelNode, "leaf_count", 0);
        model.nodeCount = optionalScalarValue<size_t>(modelNode, "node_count", 0);
        model.userPortalCount = optionalScalarValue<size_t>(modelNode, "user_portal_count", 0);
        model.rootNodeIndex = optionalScalarValue<size_t>(modelNode, "root_node_index", 0);
        model.sectionCount = optionalScalarValue<size_t>(modelNode, "section_count", 0);

        const YAML::Node bspCountsNode = modelNode["bsp_counts"];
        if (bspCountsNode && bspCountsNode.IsMap())
        {
            model.bspCounts.vertCount = optionalScalarValue<size_t>(bspCountsNode, "vert_count", 0);
            model.bspCounts.totalVisListSize =
                optionalScalarValue<size_t>(bspCountsNode, "total_vis_list_size", 0);
            model.bspCounts.leafListCount = optionalScalarValue<size_t>(bspCountsNode, "leaf_list_count", 0);
            model.bspCounts.textureNameLength =
                optionalScalarValue<size_t>(bspCountsNode, "texture_name_length", 0);
            model.bspCounts.textureCount = optionalScalarValue<size_t>(bspCountsNode, "texture_count", 0);
        }

        const YAML::Node unknownValuesNode = modelNode["unknown_values"];
        if (unknownValuesNode && unknownValuesNode.IsMap())
        {
            model.unknownValues.worldBspUnknownValue =
                optionalScalarValue<uint32_t>(unknownValuesNode, "world_bsp_unknown_value", 0);
            model.unknownValues.worldBspUnknownValue2 =
                optionalScalarValue<uint32_t>(unknownValuesNode, "world_bsp_unknown_value_2", 0);
            model.unknownValues.worldBspUnknownValue3 =
                optionalScalarValue<uint32_t>(unknownValuesNode, "world_bsp_unknown_value_3", 0);
        }

        const YAML::Node referenceValidationNode = modelNode["reference_validation"];
        if (referenceValidationNode && referenceValidationNode.IsMap())
        {
            model.referenceValidation.invalidSurfaceTextureRefs =
                optionalScalarValue<size_t>(referenceValidationNode, "invalid_surface_texture_refs", 0);
            model.referenceValidation.invalidPolySurfaceRefs =
                optionalScalarValue<size_t>(referenceValidationNode, "invalid_poly_surface_refs", 0);
            model.referenceValidation.invalidPolyPlaneRefs =
                optionalScalarValue<size_t>(referenceValidationNode, "invalid_poly_plane_refs", 0);
            model.referenceValidation.invalidPolyVertexRefs =
                optionalScalarValue<size_t>(referenceValidationNode, "invalid_poly_vertex_refs", 0);
            model.referenceValidation.invalidNodePolyRefs =
                optionalScalarValue<size_t>(referenceValidationNode, "invalid_node_poly_refs", 0);
            model.referenceValidation.invalidRootNodeRefs =
                optionalScalarValue<size_t>(referenceValidationNode, "invalid_root_node_refs", 0);
        }

        const YAML::Node pblockNode = modelNode["pblock_table"];
        if (pblockNode && pblockNode.IsMap())
        {
            model.pblockTable.preservedInSourceDat =
                optionalScalarValue<bool>(pblockNode, "preserved_in_source_dat", false);
            model.pblockTable.decodedSummary = optionalScalarValue<bool>(pblockNode, "decoded_summary", false);
            model.pblockTable.recordCount = optionalNullableSize(pblockNode, "record_count");

            const YAML::Node dimensionsNode = pblockNode["dimensions"];
            if (dimensionsNode && dimensionsNode.IsSequence() && dimensionsNode.size() >= 3)
            {
                model.pblockTable.dimA = dimensionsNode[0].as<size_t>(0);
                model.pblockTable.dimB = dimensionsNode[1].as<size_t>(0);
                model.pblockTable.dimC = dimensionsNode[2].as<size_t>(0);
            }

            const YAML::Node pblockBoundsNode = pblockNode["bounds_lt"];
            if (pblockBoundsNode && pblockBoundsNode.IsMap())
            {
                model.pblockTable.boundsMinLt = parseVec3Sequence(pblockBoundsNode["min"]);
                model.pblockTable.boundsMaxLt = parseVec3Sequence(pblockBoundsNode["max"]);
            }
        }

        const YAML::Node boundsNode = modelNode["bounds_lt"];
        if (boundsNode && boundsNode.IsMap())
        {
            model.boundsMinLt = parseVec3Sequence(boundsNode["min"]);
            model.boundsMaxLt = parseVec3Sequence(boundsNode["max"]);
        }

        model.worldTranslationLt = parseVec3Sequence(modelNode["world_translation_lt"]);

        const YAML::Node texturesNode = modelNode["textures"];
        if (texturesNode && texturesNode.IsSequence())
        {
            model.textureCount = texturesNode.size();

            for (const YAML::Node &textureNode : texturesNode)
            {
                if (!textureNode.IsMap())
                {
                    continue;
                }

                EditorMm9DatWorldModelTexture texture = {};
                texture.textureIndex = optionalScalarValue<size_t>(textureNode, "texture_index", 0);
                texture.sourceTexture = optionalScalarValue<std::string>(
                    textureNode,
                    "source_texture",
                    std::string());
                model.textures.push_back(std::move(texture));
            }
        }

        model.surfaceFlagHistogram = parseHistogramEntries(modelNode["surface_flag_histogram"]);
        model.textureUserFlagHistogram = parseHistogramEntries(modelNode["texture_user_flag_histogram"]);
        model.roles = parseDatWorldModelRoles(modelNode["roles"]);
        sidecar.worldModels.push_back(std::move(model));
    }

    if (sidecar.totals.worldModelCount != 0 && sidecar.totals.worldModelCount != sidecar.worldModels.size())
    {
        errorMessage = "MM9 DAT world sidecar world_model_count does not match world_models size";
        return std::nullopt;
    }

    const YAML::Node userPortalsNode = (*root)["user_portals"];
    if (userPortalsNode && userPortalsNode.IsSequence())
    {
        sidecar.userPortals.reserve(userPortalsNode.size());

        for (const YAML::Node &portalNode : userPortalsNode)
        {
            if (!portalNode.IsMap())
            {
                errorMessage = "MM9 DAT world sidecar user portal entry must be a map";
                return std::nullopt;
            }

            EditorMm9DatUserPortalSummary portal = {};
            portal.sourceModelIndex = optionalScalarValue<size_t>(portalNode, "source_model_index", 0);
            portal.sourceModelName =
                optionalScalarValue<std::string>(portalNode, "source_model_name", std::string());
            portal.portalIndex = optionalScalarValue<size_t>(portalNode, "portal_index", 0);
            portal.name = optionalScalarValue<std::string>(portalNode, "name", std::string());
            portal.centerLt = parseVec3Sequence(portalNode["center_lt"]);
            portal.dimsLt = parseVec3Sequence(portalNode["dims_lt"]);

            const YAML::Node rawUnknownsNode = portalNode["raw_unknowns"];
            if (rawUnknownsNode && rawUnknownsNode.IsMap())
            {
                portal.rawUnknowns.unknownInt1 =
                    optionalScalarValue<int>(rawUnknownsNode, "unknown_int_1", 0);
                portal.rawUnknowns.unknownShort =
                    optionalScalarValue<int>(rawUnknownsNode, "unknown_short", 0);
            }

            sidecar.userPortals.push_back(std::move(portal));
        }
    }

    const YAML::Node leafReferencesNode = (*root)["leaf_references"];
    if (leafReferencesNode && leafReferencesNode.IsMap())
    {
        sidecar.leafReferences.decode =
            optionalScalarValue<std::string>(leafReferencesNode, "decode", std::string());
        sidecar.leafReferences.totalRefs = optionalScalarValue<size_t>(leafReferencesNode, "total_refs", 0);
        sidecar.leafReferences.invalidRefs = optionalScalarValue<size_t>(leafReferencesNode, "invalid_refs", 0);
    }

    const YAML::Node validationNode = (*root)["validation"];
    if (validationNode && validationNode.IsMap())
    {
        sidecar.validation.parseStatus =
            optionalScalarValue<std::string>(validationNode, "parse_status", std::string());
        sidecar.validation.unknownFieldPolicy =
            optionalScalarValue<std::string>(validationNode, "unknown_field_policy", std::string());
        sidecar.validation.pblockSummaryStatus =
            optionalScalarValue<std::string>(validationNode, "pblock_summary_status", std::string());
    }

    return sidecar;
}

std::optional<EditorMm9MaterialAliasesSidecar> loadMm9MaterialAliasesSidecarFromText(
    const std::string &text,
    std::string &errorMessage)
{
    errorMessage.clear();
    const std::optional<YAML::Node> root = loadYamlMapFromText(text, "MM9 material aliases sidecar", errorMessage);

    if (!root || !validateSidecarKind(*root, "mm9_material_aliases", "MM9 material aliases sidecar", errorMessage))
    {
        return std::nullopt;
    }

    EditorMm9MaterialAliasesSidecar sidecar = {};
    sidecar.formatVersion = optionalScalarValue<int>(*root, "format_version", 0);
    sidecar.kind = optionalScalarValue<std::string>(*root, "kind", std::string());
    sidecar.sourceDat = optionalScalarValue<std::string>(*root, "source_dat", std::string());

    const YAML::Node statsNode = (*root)["stats"];
    if (statsNode && statsNode.IsMap())
    {
        sidecar.stats.sourceModels = optionalScalarValue<size_t>(statsNode, "source_models", 0);
        sidecar.stats.sourcePolies = optionalScalarValue<size_t>(statsNode, "source_polies", 0);
        sidecar.stats.emittedFaces = optionalScalarValue<size_t>(statsNode, "emitted_faces", 0);
        sidecar.stats.skippedPolies = optionalScalarValue<size_t>(statsNode, "skipped_polies", 0);
        sidecar.stats.triangulatedPolies = optionalScalarValue<size_t>(statsNode, "triangulated_polies", 0);
        sidecar.stats.skippedDegenerateTriangles =
            optionalScalarValue<size_t>(statsNode, "skipped_degenerate_triangles", 0);
        sidecar.stats.modelInstances = optionalScalarValue<size_t>(statsNode, "model_instances", 0);
        sidecar.stats.uniqueModelAssets = optionalScalarValue<size_t>(statsNode, "unique_model_assets", 0);
    }

    const YAML::Node texturesNode = (*root)["textures"];
    if (!texturesNode || !texturesNode.IsSequence())
    {
        errorMessage = "MM9 material aliases sidecar textures must be a sequence";
        return std::nullopt;
    }

    sidecar.textures.reserve(texturesNode.size());

    for (const YAML::Node &textureNode : texturesNode)
    {
        if (!textureNode.IsMap())
        {
            errorMessage = "MM9 material texture entry must be a map";
            return std::nullopt;
        }

        EditorMm9MaterialTexture texture = {};
        const YAML::Node aliasNode = textureNode["alias"];
        const YAML::Node sourceTextureNode = textureNode["source_texture"];
        const YAML::Node emittedBitmapNode = textureNode["emitted_bitmap"];
        const YAML::Node emittedBitmapModeNode = textureNode["emitted_bitmap_mode"];

        texture.alias = optionalScalarValue<std::string>(textureNode, "alias", std::string());
        texture.sourceTexture = optionalScalarValue<std::string>(textureNode, "source_texture", std::string());
        texture.physicalPath = optionalScalarValue<std::string>(textureNode, "physical_path", std::string());
        texture.emittedBitmap = optionalScalarValue<std::string>(textureNode, "emitted_bitmap", std::string());
        texture.emittedBitmapMode =
            optionalScalarValue<std::string>(textureNode, "emitted_bitmap_mode", std::string());
        texture.aliasFieldPresent = aliasNode && aliasNode.IsScalar();
        texture.sourceTextureFieldPresent = sourceTextureNode && sourceTextureNode.IsScalar();
        texture.emittedBitmapFieldPresent = emittedBitmapNode && emittedBitmapNode.IsScalar();
        texture.emittedBitmapModeFieldPresent = emittedBitmapModeNode && emittedBitmapModeNode.IsScalar();
        texture.width = optionalScalarValue<int>(textureNode, "width", 0);
        texture.height = optionalScalarValue<int>(textureNode, "height", 0);
        texture.dtxSurfaceFlag = optionalScalarValue<int>(textureNode, "dtx_surface_flag", 0);
        texture.dtxTextureGroup = optionalScalarValue<int>(textureNode, "dtx_texture_group", 0);
        texture.dtxBpp = optionalScalarValue<int>(textureNode, "dtx_bpp", 0);
        texture.dtxMipmapCount = optionalScalarValue<int>(textureNode, "dtx_mipmap_count", 0);
        texture.dtxMipmapsUsed = optionalScalarValue<int>(textureNode, "dtx_mipmaps_used", 0);
        texture.dtxFlags = optionalScalarValue<int>(textureNode, "dtx_flags", 0);
        texture.dtxDetailScale = optionalScalarValue<float>(textureNode, "dtx_detail_scale", 0.0f);
        texture.dtxDetailAngle = optionalScalarValue<int>(textureNode, "dtx_detail_angle", 0);
        texture.dtxCommandString =
            optionalScalarValue<std::string>(textureNode, "dtx_command_string", std::string());
        sidecar.textures.push_back(std::move(texture));
    }

    return sidecar;
}

std::optional<EditorMm9RawObjectsSidecar> loadMm9RawObjectsSidecarFromText(
    const std::string &text,
    std::string &errorMessage)
{
    errorMessage.clear();
    const std::optional<YAML::Node> root = loadYamlMapFromText(text, "MM9 raw objects sidecar", errorMessage);

    if (!root || !validateSidecarKind(*root, "mm9_raw_world_objects", "MM9 raw objects sidecar", errorMessage))
    {
        return std::nullopt;
    }

    EditorMm9RawObjectsSidecar sidecar = {};
    sidecar.formatVersion = optionalScalarValue<int>(*root, "format_version", 0);
    sidecar.kind = optionalScalarValue<std::string>(*root, "kind", std::string());
    sidecar.sourceDat = optionalScalarValue<std::string>(*root, "source_dat", std::string());
    sidecar.objectCount = optionalScalarValue<size_t>(*root, "object_count", 0);
    sidecar.unknownPropertyCount = optionalScalarValue<size_t>(*root, "unknown_property_count", 0);

    const YAML::Node unknownCodesNode = (*root)["unknown_property_codes"];
    if (unknownCodesNode && unknownCodesNode.IsSequence())
    {
        sidecar.unknownPropertyCodes.reserve(unknownCodesNode.size());
        for (const YAML::Node &codeNode : unknownCodesNode)
        {
            sidecar.unknownPropertyCodes.push_back(codeNode.as<int>(0));
        }
    }

    const YAML::Node objectsNode = (*root)["objects"];
    if (!objectsNode || !objectsNode.IsSequence())
    {
        errorMessage = "MM9 raw objects sidecar objects must be a sequence";
        return std::nullopt;
    }

    sidecar.objects.reserve(objectsNode.size());

    for (const YAML::Node &objectNode : objectsNode)
    {
        if (!objectNode.IsMap())
        {
            errorMessage = "MM9 raw object entry must be a map";
            return std::nullopt;
        }

        EditorMm9RawObject rawObject = {};
        rawObject.objectIndex = optionalScalarValue<size_t>(objectNode, "object_index", 0);
        rawObject.name = optionalScalarValue<std::string>(objectNode, "name", std::string());
        rawObject.propertyCount = optionalScalarValue<size_t>(objectNode, "property_count", 0);
        rawObject.dataLength = optionalScalarValue<size_t>(objectNode, "data_length", 0);
        rawObject.trailingHex = optionalScalarValue<std::string>(objectNode, "trailing_hex", std::string());

        if (!parseRawObjectProperties(objectNode, rawObject, errorMessage))
        {
            return std::nullopt;
        }

        sidecar.objects.push_back(std::move(rawObject));
    }

    if (sidecar.objectCount != 0 && sidecar.objectCount != sidecar.objects.size())
    {
        errorMessage = "MM9 raw objects sidecar object_count does not match objects size";
        return std::nullopt;
    }

    return sidecar;
}

std::vector<Game::Mm9LightSourceObject> buildMm9LightSourceObjects(
    const EditorMm9RawObjectsSidecar &rawObjects)
{
    std::vector<Game::Mm9LightSourceObject> lightSourceObjects;
    lightSourceObjects.reserve(rawObjects.objects.size());

    for (const EditorMm9RawObject &rawObject : rawObjects.objects)
    {
        Game::Mm9LightSourceObject lightSourceObject = {};
        lightSourceObject.sourceObjectIndex = rawObject.objectIndex;
        lightSourceObject.sourceClass = rawObject.name;
        lightSourceObject.sourceName = rawObject.name;
        lightSourceObject.properties.reserve(rawObject.properties.size());

        for (const EditorMm9RawObjectProperty &property : rawObject.properties)
        {
            const std::optional<Game::Mm9LightSourceProperty> lightProperty =
                buildMm9LightSourceProperty(property);
            if (lightProperty)
            {
                lightSourceObject.properties.push_back(*lightProperty);
            }
        }

        lightSourceObjects.push_back(std::move(lightSourceObject));
    }

    return lightSourceObjects;
}

std::vector<Game::Mm9SoundSourceObject> buildMm9SoundSourceObjects(
    const EditorMm9RawObjectsSidecar &rawObjects,
    const std::vector<EditorMm9RawObjectAssetReferenceStatus> &assetReferenceStatuses)
{
    std::unordered_map<size_t, std::vector<Game::Mm9SoundSourceReference>> referencesByObjectIndex;

    for (const EditorMm9RawObjectAssetReferenceStatus &status : assetReferenceStatuses)
    {
        if (status.sourceFamily != "sounds" && status.sourceFamily != "voices")
        {
            continue;
        }

        Game::Mm9SoundSourceReference reference = {};
        reference.propertyName = status.propertyName;
        reference.sourceFamily = status.sourceFamily;
        reference.sourceValue = status.sourceValue;
        reference.normalizedKey = status.normalizedKey;
        reference.resolvedSourcePath = status.resolvedSourcePath;
        reference.required = status.required;
        reference.resolved = status.resolved;
        reference.ambiguous = status.ambiguous;
        referencesByObjectIndex[status.sourceObjectIndex].push_back(std::move(reference));
    }

    std::vector<Game::Mm9SoundSourceObject> sourceObjects;
    sourceObjects.reserve(referencesByObjectIndex.size());

    for (const EditorMm9RawObject &rawObject : rawObjects.objects)
    {
        const auto referencesIterator = referencesByObjectIndex.find(rawObject.objectIndex);
        if (referencesIterator == referencesByObjectIndex.end())
        {
            continue;
        }

        Game::Mm9SoundSourceObject sourceObject = {};
        sourceObject.sourceObjectIndex = rawObject.objectIndex;
        sourceObject.sourceClass = rawObject.name;
        sourceObject.sourceName = rawObject.name;

        for (const EditorMm9RawObjectProperty &property : rawObject.properties)
        {
            if (property.name == "Name")
            {
                const std::optional<std::string> nameValue = decodedRawObjectStringValue(property);
                if (nameValue && !nameValue->empty())
                {
                    sourceObject.sourceName = *nameValue;
                }
            }
            else if (property.name == "Pos")
            {
                const std::optional<Game::Mm9DatVec3> position = decodedRawObjectVec3Value(property);
                if (position)
                {
                    sourceObject.positionLt = *position;
                    sourceObject.hasPosition = true;
                }
            }
            else if (property.name == "SoundPos")
            {
                const std::optional<Game::Mm9DatVec3> soundPosition = decodedRawObjectVec3Value(property);
                if (soundPosition)
                {
                    sourceObject.soundPositionLt = *soundPosition;
                    sourceObject.hasSoundPosition = true;
                }
            }
            else if (property.name == "SoundRadius")
            {
                const std::optional<float> soundRadius = decodedRawObjectFloatValue(property);
                if (soundRadius)
                {
                    sourceObject.soundRadius = *soundRadius;
                    sourceObject.hasSoundRadius = true;
                }
            }
        }

        sourceObject.references = referencesIterator->second;
        sourceObjects.push_back(std::move(sourceObject));
    }

    return sourceObjects;
}

std::vector<Game::Mm9ObjectSourceObject> buildMm9ObjectSourceObjects(
    const EditorMm9RawObjectsSidecar &rawObjects)
{
    std::vector<Game::Mm9ObjectSourceObject> sourceObjects;
    sourceObjects.reserve(rawObjects.objects.size());

    for (const EditorMm9RawObject &rawObject : rawObjects.objects)
    {
        Game::Mm9ObjectSourceObject sourceObject = {};
        sourceObject.sourceObjectIndex = rawObject.objectIndex;
        sourceObject.sourceClass = rawObject.name;
        sourceObject.sourceName = rawObject.name;

        for (const EditorMm9RawObjectProperty &property : rawObject.properties)
        {
            if (property.name == "Name")
            {
                const std::optional<std::string> nameValue = decodedRawObjectStringValue(property);
                if (nameValue && !nameValue->empty())
                {
                    sourceObject.sourceName = *nameValue;
                }
            }
            else if (property.name == "Pos")
            {
                const std::optional<Game::Mm9DatVec3> position = decodedRawObjectVec3Value(property);
                if (position)
                {
                    sourceObject.positionLt = *position;
                    sourceObject.hasPosition = true;
                }
            }
            else if (property.name == "Rotation")
            {
                const std::optional<Game::Mm9DatVec3> rotation = decodedRawObjectVec3Value(property);
                if (rotation)
                {
                    sourceObject.rotationLt = *rotation;
                    sourceObject.hasRotation = true;
                }
            }
            else if (property.name == "Scale")
            {
                const std::optional<float> scale = decodedRawObjectFloatValue(property);
                if (scale)
                {
                    sourceObject.scale = *scale;
                    sourceObject.hasScale = true;
                }
            }
            else if (property.name == "Dims")
            {
                const std::optional<Game::Mm9DatVec3> dims = decodedRawObjectVec3Value(property);
                if (dims)
                {
                    sourceObject.dimsLt = *dims;
                    sourceObject.hasDims = true;
                }
            }
            else if (property.name == "Radius")
            {
                const std::optional<float> radius = decodedRawObjectFloatValue(property);
                if (radius)
                {
                    sourceObject.radius = *radius;
                    sourceObject.hasRadius = true;
                }
            }
            else if (property.name == "Visible")
            {
                sourceObject.visible = decodedRawObjectBoolValue(property);
            }
            else if (property.name == "Solid")
            {
                sourceObject.solid = decodedRawObjectBoolValue(property);
            }
            else if (property.name == "Trigger")
            {
                sourceObject.trigger = decodedRawObjectBoolValue(property);
            }
        }

        sourceObjects.push_back(std::move(sourceObject));
    }

    return sourceObjects;
}

std::vector<Game::Mm9SpawnSourceObject> buildMm9SpawnSourceObjects(
    const EditorMm9RawObjectsSidecar &rawObjects)
{
    std::vector<Game::Mm9SpawnSourceObject> sourceObjects;
    sourceObjects.reserve(rawObjects.objects.size());

    for (const EditorMm9RawObject &rawObject : rawObjects.objects)
    {
        Game::Mm9SpawnSourceObject sourceObject = {};
        sourceObject.sourceObjectIndex = rawObject.objectIndex;
        sourceObject.sourceClass = rawObject.name;
        sourceObject.sourceName = rawObject.name;

        for (const EditorMm9RawObjectProperty &property : rawObject.properties)
        {
            if (property.name == "Name")
            {
                const std::optional<std::string> nameValue = decodedRawObjectStringValue(property);
                if (nameValue && !nameValue->empty())
                {
                    sourceObject.sourceName = *nameValue;
                }
            }
            else if (property.name == "Pos")
            {
                const std::optional<Game::Mm9DatVec3> position = decodedRawObjectVec3Value(property);
                if (position)
                {
                    sourceObject.positionLt = *position;
                    sourceObject.hasPosition = true;
                }
            }
            else if (property.name == "Rotation")
            {
                const std::optional<Game::Mm9DatVec3> rotation = decodedRawObjectVec3Value(property);
                if (rotation)
                {
                    sourceObject.rotationLt = *rotation;
                    sourceObject.hasRotation = true;
                }
            }
            else if (property.name == "SpawnLevel")
            {
                sourceObject.spawnLevel = decodedRawObjectIntValue(property);
            }
            else if (property.name == "SpawnObject")
            {
                sourceObject.spawnObject = decodedRawObjectStringValue(property);
            }
            else if (property.name == "SpawnObjectVel")
            {
                const std::optional<Game::Mm9DatVec3> velocity = decodedRawObjectVec3Value(property);
                if (velocity)
                {
                    sourceObject.spawnObjectVelocityLt = *velocity;
                    sourceObject.hasSpawnObjectVelocity = true;
                }
            }
            else if (property.name == "NPCProps")
            {
                sourceObject.npcProps = decodedRawObjectIntValue(property);
            }
            else if (property.name == "NPCNbr")
            {
                sourceObject.npcNumber = decodedRawObjectIntValue(property);
            }
        }

        if (sourceObject.spawnLevel
            || sourceObject.spawnObject
            || sourceObject.hasSpawnObjectVelocity
            || sourceObject.npcProps
            || sourceObject.npcNumber)
        {
            sourceObjects.push_back(std::move(sourceObject));
        }
    }

    return sourceObjects;
}

std::optional<EditorMm9SourceAssetManifest> loadMm9SourceAssetManifestFromText(
    const std::string &text,
    std::string &errorMessage)
{
    errorMessage.clear();
    const std::optional<YAML::Node> root = loadYamlMapFromText(text, "MM9 source asset manifest", errorMessage);

    if (!root || !validateSidecarKind(*root, "mm9_source_asset_manifest", "MM9 source asset manifest", errorMessage))
    {
        return std::nullopt;
    }

    EditorMm9SourceAssetManifest manifest = {};
    manifest.formatVersion = optionalScalarValue<int>(*root, "format_version", 0);
    manifest.kind = optionalScalarValue<std::string>(*root, "kind", std::string());
    manifest.sourceRoot = optionalScalarValue<std::string>(*root, "source_root", std::string());
    manifest.packageRoot = optionalScalarValue<std::string>(*root, "package_root", std::string());

    const YAML::Node policyNode = (*root)["policy"];
    if (policyNode && policyNode.IsMap())
    {
        manifest.policy.sourceTruth = optionalScalarValue<bool>(policyNode, "source_truth", false);
        manifest.policy.generatedCache = optionalScalarValue<bool>(policyNode, "generated_cache", false);
        manifest.policy.preserveRezRelativeNames =
            optionalScalarValue<bool>(policyNode, "preserve_rez_relative_names", false);
        manifest.policy.duplicateRezFamilyFolderRemoved =
            optionalScalarValue<bool>(policyNode, "duplicate_rez_family_folder_removed", false);
        manifest.policy.syncCommand = optionalScalarValue<std::string>(policyNode, "sync_command", std::string());
    }

    const YAML::Node familiesNode = (*root)["families"];
    if (!familiesNode || !familiesNode.IsSequence())
    {
        errorMessage = "MM9 source asset manifest families must be a sequence";
        return std::nullopt;
    }

    manifest.families.reserve(familiesNode.size());

    for (const YAML::Node &familyNode : familiesNode)
    {
        if (!familyNode.IsMap())
        {
            errorMessage = "MM9 source asset manifest family entry must be a map";
            return std::nullopt;
        }

        EditorMm9SourceAssetFamily family = {};
        family.id = optionalScalarValue<std::string>(familyNode, "id", std::string());
        family.source = optionalScalarValue<std::string>(familyNode, "source", std::string());
        family.package = optionalScalarValue<std::string>(familyNode, "package", std::string());
        family.fileCount = optionalScalarValue<size_t>(familyNode, "file_count", 0);

        if (family.id.empty())
        {
            errorMessage = "MM9 source asset manifest family id must not be empty";
            return std::nullopt;
        }

        if (family.package.empty())
        {
            errorMessage = "MM9 source asset manifest family package must not be empty";
            return std::nullopt;
        }

        manifest.families.push_back(std::move(family));
    }

    const YAML::Node notesNode = (*root)["notes"];
    if (notesNode && notesNode.IsSequence())
    {
        manifest.notes.reserve(notesNode.size());
        for (const YAML::Node &noteNode : notesNode)
        {
            if (noteNode.IsScalar())
            {
                manifest.notes.push_back(noteNode.as<std::string>());
            }
        }
    }

    if (manifest.formatVersion <= 0)
    {
        errorMessage = "MM9 source asset manifest format_version must be positive.";
        return std::nullopt;
    }

    return manifest;
}

bool isMm9DatLevelText(const std::string &text)
{
    try
    {
        const YAML::Node root = YAML::Load(text);
        return root && root.IsMap() && root["kind"].as<std::string>(std::string()) == "mm9_level";
    }
    catch (const YAML::Exception &)
    {
        return false;
    }
}

std::filesystem::path resolveMm9DatLevelRelativePath(
    const std::filesystem::path &levelPhysicalPath,
    const std::string &relativePath)
{
    const std::filesystem::path path(relativePath);

    if (path.is_absolute())
    {
        return path.lexically_normal();
    }

    return (levelPhysicalPath.parent_path() / path).lexically_normal();
}

std::filesystem::path resolveMm9SourceAssetManifestPath(const std::filesystem::path &levelPhysicalPath)
{
    return existingPathOrDevelopmentFallback(
        (levelPhysicalPath.parent_path() / "../source/manifest.yml").lexically_normal());
}

std::filesystem::path resolveMm9SourceAssetManifestPath(
    const std::filesystem::path &levelPhysicalPath,
    const EditorMm9DatLevelMetadata &metadata)
{
    return existingPathOrDevelopmentFallback(resolveMm9DatLevelRelativePath(levelPhysicalPath, metadata.source.manifest));
}

std::vector<std::string> validateMm9DatLevelMetadataFiles(
    const std::filesystem::path &levelPhysicalPath,
    const EditorMm9DatLevelMetadata &metadata)
{
    std::vector<std::string> issues;

    if (metadata.kind != "mm9_level")
    {
        issues.push_back("MM9 level kind is not mm9_level.");
    }

    if (metadata.runtime.worldBackend != "dat_world")
    {
        issues.push_back("MM9 level runtime.world_backend is not dat_world.");
    }

    addMissingPathIssue(issues, "source DAT", levelPhysicalPath, metadata.source.dat);
    addMissingPathIssue(issues, "source asset manifest", levelPhysicalPath, metadata.source.manifest);
    addMissingPathIssue(issues, "DAT world sidecar", levelPhysicalPath, metadata.sidecars.datWorld);
    addMissingPathIssue(issues, "raw objects sidecar", levelPhysicalPath, metadata.sidecars.rawObjects);
    addMissingPathIssue(issues, "material aliases sidecar", levelPhysicalPath, metadata.sidecars.materials);
    addMissingPathIssue(issues, "events sidecar", levelPhysicalPath, metadata.sidecars.events);
    if (metadata.sidecars.sourceAssetAliases.has_value() && !metadata.sidecars.sourceAssetAliases->empty())
    {
        addMissingPathIssue(
            issues,
            "source asset aliases sidecar",
            levelPhysicalPath,
            metadata.sidecars.sourceAssetAliases.value());
    }
    addMissingPathIssue(issues, "level Lua script", levelPhysicalPath, metadata.scripts.level);
    addSourceDatHashIssue(issues, levelPhysicalPath, metadata);

    addSidecarKindIssue(
        issues,
        "source asset manifest",
        levelPhysicalPath,
        metadata.source.manifest,
        "mm9_source_asset_manifest");

    addSidecarKindIssue(
        issues,
        "DAT world sidecar",
        levelPhysicalPath,
        metadata.sidecars.datWorld,
        "mm9_dat_world");
    addSidecarKindIssue(
        issues,
        "raw objects sidecar",
        levelPhysicalPath,
        metadata.sidecars.rawObjects,
        "mm9_raw_world_objects");
    addSidecarKindIssue(
        issues,
        "material aliases sidecar",
        levelPhysicalPath,
        metadata.sidecars.materials,
        "mm9_material_aliases");
    addSidecarKindIssue(
        issues,
        "events sidecar",
        levelPhysicalPath,
        metadata.sidecars.events,
        "mm9_events");
    if (metadata.sidecars.sourceAssetAliases.has_value() && !metadata.sidecars.sourceAssetAliases->empty())
    {
        addSidecarKindIssue(
            issues,
            "source asset aliases sidecar",
            levelPhysicalPath,
            metadata.sidecars.sourceAssetAliases.value(),
            "mm9_source_asset_aliases");
    }

    return issues;
}

std::vector<std::string> validateMm9DatWorldSidecarReferences(const EditorMm9DatWorldSidecar &sidecar)
{
    std::vector<std::string> issues;

    if (sidecar.totals.worldModelCount != sidecar.worldModels.size())
    {
        issues.push_back(
            "MM9 DAT world sidecar world_model_count mismatch: stored="
            + std::to_string(sidecar.totals.worldModelCount)
            + " actual=" + std::to_string(sidecar.worldModels.size()));
    }

    if (sidecar.totals.invalidLeafReferenceCount != 0)
    {
        issues.push_back(
            "MM9 DAT world sidecar has invalid leaf polygon references: "
            + std::to_string(sidecar.totals.invalidLeafReferenceCount));
    }

    if (sidecar.leafReferences.invalidRefs != 0)
    {
        issues.push_back(
            "MM9 DAT world sidecar leaf reference summary has invalid refs: "
            + std::to_string(sidecar.leafReferences.invalidRefs));
    }

    size_t surfaceTotal = 0;
    size_t polyTotal = 0;
    size_t leafTotal = 0;
    size_t userPortalTotal = 0;

    for (size_t modelIndex = 0; modelIndex < sidecar.worldModels.size(); ++modelIndex)
    {
        const EditorMm9DatWorldModelSummary &model = sidecar.worldModels[modelIndex];

        if (model.sourceModelIndex != modelIndex)
        {
            issues.push_back(
                "MM9 DAT world model sidecar index mismatch at row " + std::to_string(modelIndex)
                + ": source_model_index=" + std::to_string(model.sourceModelIndex));
        }

        if (model.textureCount != model.textures.size())
        {
            issues.push_back(
                "MM9 DAT world model " + std::to_string(model.sourceModelIndex)
                + " texture count mismatch: stored=" + std::to_string(model.textureCount)
                + " actual=" + std::to_string(model.textures.size()));
        }

        if (model.bspCounts.textureCount != 0 && model.bspCounts.textureCount != model.textures.size())
        {
            issues.push_back(
                "MM9 DAT world model " + std::to_string(model.sourceModelIndex)
                + " BSP texture count mismatch: stored=" + std::to_string(model.bspCounts.textureCount)
                + " actual=" + std::to_string(model.textures.size()));
        }

        if (model.pblockTable.decodedSummary && model.pblockTable.recordCount)
        {
            const size_t pblockRecordCount =
                model.pblockTable.dimA * model.pblockTable.dimB * model.pblockTable.dimC;

            if (pblockRecordCount != *model.pblockTable.recordCount)
            {
                issues.push_back(
                    "MM9 DAT world model " + std::to_string(model.sourceModelIndex)
                    + " PBlock record count mismatch: dimensions="
                    + std::to_string(pblockRecordCount)
                    + " stored=" + std::to_string(*model.pblockTable.recordCount));
            }
        }

        if (model.referenceValidation.invalidSurfaceTextureRefs != 0)
        {
            issues.push_back(
                "MM9 DAT world model " + std::to_string(model.sourceModelIndex)
                + " has invalid surface texture references: "
                + std::to_string(model.referenceValidation.invalidSurfaceTextureRefs));
        }

        if (model.referenceValidation.invalidPolySurfaceRefs != 0)
        {
            issues.push_back(
                "MM9 DAT world model " + std::to_string(model.sourceModelIndex)
                + " has invalid polygon surface references: "
                + std::to_string(model.referenceValidation.invalidPolySurfaceRefs));
        }

        if (model.referenceValidation.invalidPolyPlaneRefs != 0)
        {
            issues.push_back(
                "MM9 DAT world model " + std::to_string(model.sourceModelIndex)
                + " has invalid polygon plane references: "
                + std::to_string(model.referenceValidation.invalidPolyPlaneRefs));
        }

        if (model.referenceValidation.invalidPolyVertexRefs != 0)
        {
            issues.push_back(
                "MM9 DAT world model " + std::to_string(model.sourceModelIndex)
                + " has invalid polygon vertex references: "
                + std::to_string(model.referenceValidation.invalidPolyVertexRefs));
        }

        if (model.referenceValidation.invalidNodePolyRefs != 0)
        {
            issues.push_back(
                "MM9 DAT world model " + std::to_string(model.sourceModelIndex)
                + " has invalid node polygon references: "
                + std::to_string(model.referenceValidation.invalidNodePolyRefs));
        }

        if (model.referenceValidation.invalidRootNodeRefs != 0)
        {
            issues.push_back(
                "MM9 DAT world model " + std::to_string(model.sourceModelIndex)
                + " has invalid root node references: "
                + std::to_string(model.referenceValidation.invalidRootNodeRefs));
        }

        for (size_t textureRow = 0; textureRow < model.textures.size(); ++textureRow)
        {
            const EditorMm9DatWorldModelTexture &texture = model.textures[textureRow];

            if (texture.textureIndex != textureRow)
            {
                issues.push_back(
                    "MM9 DAT world model " + std::to_string(model.sourceModelIndex)
                    + " texture index mismatch at row " + std::to_string(textureRow)
                    + ": texture_index=" + std::to_string(texture.textureIndex));
            }

            if (texture.sourceTexture.empty())
            {
                issues.push_back(
                    "MM9 DAT world model " + std::to_string(model.sourceModelIndex)
                    + " texture " + std::to_string(texture.textureIndex)
                    + " source texture path is empty.");
            }
        }

        surfaceTotal += model.surfaceCount;
        polyTotal += model.polyCount;
        leafTotal += model.leafCount;
        userPortalTotal += model.userPortalCount;
    }

    if (surfaceTotal != sidecar.totals.surfaceCount)
    {
        issues.push_back(
            "MM9 DAT world sidecar surface total mismatch: stored="
            + std::to_string(sidecar.totals.surfaceCount)
            + " actual=" + std::to_string(surfaceTotal));
    }

    if (polyTotal != sidecar.totals.sourcePolyCount)
    {
        issues.push_back(
            "MM9 DAT world sidecar polygon total mismatch: stored="
            + std::to_string(sidecar.totals.sourcePolyCount)
            + " actual=" + std::to_string(polyTotal));
    }

    if (leafTotal != sidecar.totals.leafCount)
    {
        issues.push_back(
            "MM9 DAT world sidecar leaf total mismatch: stored="
            + std::to_string(sidecar.totals.leafCount)
            + " actual=" + std::to_string(leafTotal));
    }

    if (userPortalTotal != sidecar.totals.userPortalCount)
    {
        issues.push_back(
            "MM9 DAT world sidecar user portal total mismatch: stored="
            + std::to_string(sidecar.totals.userPortalCount)
            + " actual=" + std::to_string(userPortalTotal));
    }

    if (sidecar.leafReferences.totalRefs != 0
        && sidecar.leafReferences.totalRefs != sidecar.totals.leafReferenceCount)
    {
        issues.push_back(
            "MM9 DAT world sidecar leaf reference total mismatch: stored="
            + std::to_string(sidecar.totals.leafReferenceCount)
            + " summary=" + std::to_string(sidecar.leafReferences.totalRefs));
    }

    for (const EditorMm9DatUserPortalSummary &portal : sidecar.userPortals)
    {
        if (portal.sourceModelIndex >= sidecar.worldModels.size())
        {
            issues.push_back(
                "MM9 DAT user portal " + std::to_string(portal.portalIndex)
                + " references invalid source model " + std::to_string(portal.sourceModelIndex));
            continue;
        }

        const EditorMm9DatWorldModelSummary &model = sidecar.worldModels[portal.sourceModelIndex];

        if (portal.portalIndex >= model.userPortalCount)
        {
            issues.push_back(
                "MM9 DAT user portal " + std::to_string(portal.portalIndex)
                + " is out of range for source model " + std::to_string(portal.sourceModelIndex));
        }
    }

    return issues;
}

std::optional<EditorMm9DtxHeader> readMm9DtxHeader(
    const std::filesystem::path &physicalPath,
    std::string &errorMessage)
{
    errorMessage.clear();

    std::vector<uint8_t> bytes;

    if (!readBinaryFile(physicalPath, bytes))
    {
        errorMessage = "could not read DTX file: " + physicalPath.generic_string();
        return std::nullopt;
    }

    const std::optional<Game::Mm9DtxHeader> gameHeader = Game::parseMm9DtxHeader(bytes, errorMessage);

    if (!gameHeader)
    {
        errorMessage += ": " + physicalPath.generic_string();
        return std::nullopt;
    }

    if (bytes.size() < 36)
    {
        errorMessage = "DTX file is too small: " + physicalPath.generic_string();
        return std::nullopt;
    }

    EditorMm9DtxHeader header = {};
    header.fileType = gameHeader->resourceType;
    header.version = gameHeader->version;
    header.width = gameHeader->width;
    header.height = gameHeader->height;
    header.mipmapCount = gameHeader->mipmapCount;
    header.sectionCount = gameHeader->sectionCount;
    header.lightFlag = header.sectionCount;
    header.flags = gameHeader->flags;
    header.userFlags = gameHeader->userFlags;
    header.surfaceFlag = header.userFlags;
    header.textureGroup = gameHeader->textureGroup;
    header.mipmapsUsed = gameHeader->mipmapsUsed;
    header.bpp = gameHeader->bpp;
    header.nonS3tcOffset = gameHeader->nonS3tcOffset;
    header.uiMipmapOffset = gameHeader->uiMipmapOffset;
    header.texturePriority = gameHeader->texturePriority;
    header.detailScale = gameHeader->detailScale;
    header.detailAngle = gameHeader->detailAngle;
    header.commandString = gameHeader->commandString;

    for (size_t extraIndex = 0; extraIndex < header.extraBytes.size(); ++extraIndex)
    {
        header.extraBytes[extraIndex] = bytes[24 + extraIndex];
    }

    std::string layoutErrorMessage;
    const std::optional<Game::Mm9DtxLayout> layout = Game::parseMm9DtxLayout(bytes, layoutErrorMessage);

    if (layout)
    {
        header.mips.reserve(layout->mips.size());
        for (const Game::Mm9DtxMipLevel &gameMip : layout->mips)
        {
            EditorMm9DtxMipLevel mip = {};
            mip.level = gameMip.level;
            mip.width = gameMip.width;
            mip.height = gameMip.height;
            mip.payloadOffset = gameMip.payloadOffset;
            mip.payloadSize = gameMip.payloadSize;
            mip.payloadAvailable = gameMip.payloadAvailable;
            mip.decodedPreviewAvailable =
                gameMip.payloadAvailable
                && (gameHeader->bpp == Game::Mm9DtxBpp8P
                    || gameHeader->bpp == Game::Mm9DtxBpp32
                    || gameHeader->bpp == Game::Mm9DtxBppDxt1
                    || gameHeader->bpp == Game::Mm9DtxBppDxt3
                    || gameHeader->bpp == Game::Mm9DtxBppDxt5);
            header.mips.push_back(mip);
        }

        header.sections.reserve(layout->sections.size());
        for (const Game::Mm9DtxSection &gameSection : layout->sections)
        {
            EditorMm9DtxSection section = {};
            section.sectionIndex = gameSection.sectionIndex;
            section.type = gameSection.type;
            section.name = gameSection.name;
            section.payloadOffset = gameSection.payloadOffset;
            section.payloadSize = gameSection.payloadSize;
            section.payloadAvailable = gameSection.payloadAvailable;
            header.sections.push_back(section);
        }

        header.trailingBytes = layout->trailingBytes;
    }

    return header;
}

bool isMm9DecodedMaterialCacheMode(const std::string &mode)
{
    return mode == "dxt1"
        || mode == "dxt3"
        || mode == "dxt5"
        || mode == "bgra32"
        || mode == "bgra8p";
}

void inspectMm9DecodedMaterialCacheDeterminism(
    EditorMm9MaterialTextureStatus &status,
    const std::filesystem::path &sourcePath,
    const std::filesystem::path &cachePath)
{
    if (!isMm9DecodedMaterialCacheMode(status.emittedBitmapMode)
        || !status.sourceDtxResolved
        || !status.sourcePathExists
        || !status.cachePathExists)
    {
        return;
    }

    status.cacheDeterminismChecked = true;

    std::string dtxErrorMessage;
    const std::optional<Game::Mm9DtxTexture> sourceTexture =
        Game::loadMm9DtxTexture(sourcePath, dtxErrorMessage);

    if (!sourceTexture)
    {
        status.cacheDeterminismMessage = "source DTX decode failed: " + dtxErrorMessage;
        return;
    }

    status.sourceDtxDecodedForCache = true;

    if (sourceTexture->decodeMode != status.emittedBitmapMode)
    {
        status.cacheDeterminismMessage =
            "source DTX decode mode " + sourceTexture->decodeMode
            + " differs from emitted bitmap mode " + status.emittedBitmapMode;
        return;
    }

    std::vector<uint8_t> cacheBytes;

    if (!readBinaryFile(cachePath, cacheBytes))
    {
        status.cacheDeterminismMessage = "generated cache could not be read: " + cachePath.generic_string();
        return;
    }

    const std::optional<Engine::ImagePixelsBgra> cacheImage =
        Engine::decodeImagePixelsBgra(cacheBytes, cachePath.generic_string());

    if (!cacheImage)
    {
        status.cacheDeterminismMessage = "generated cache image could not be decoded: " + cachePath.generic_string();
        return;
    }

    status.cacheImageDecoded = true;

    if (cacheImage->width != static_cast<int>(sourceTexture->width)
        || cacheImage->height != static_cast<int>(sourceTexture->height))
    {
        status.cacheDeterminismMessage =
            "generated cache dimensions differ from decoded source DTX: cache="
            + std::to_string(cacheImage->width) + "x" + std::to_string(cacheImage->height)
            + " source=" + std::to_string(sourceTexture->width) + "x" + std::to_string(sourceTexture->height);
        return;
    }

    if (cacheImage->pixels != sourceTexture->pixelsBgra)
    {
        status.cacheDeterminismMessage =
            "generated cache pixels differ from decoded source DTX: " + status.sourceTexture;
        return;
    }

    status.cacheMatchesDecodedSource = true;
    status.cacheDeterminismMessage = "generated cache matches decoded source DTX";
}

std::vector<EditorMm9MaterialTextureStatus> inspectMm9MaterialTextureReferences(
    const std::filesystem::path &levelPhysicalPath,
    const EditorMm9DatWorldSidecar &datWorld,
    const EditorMm9MaterialAliasesSidecar &materialAliases,
    EditorMm9MaterialInspectionCache *pCache,
    const EditorMm9DatLevelMetadata *pMetadata)
{
    std::unordered_map<std::string, size_t> datReferenceCountByTexture;
    std::unordered_map<std::string, size_t> defaultRenderableDatReferenceCountByTexture;
    std::unordered_map<std::string, size_t> helperOnlyDatReferenceCountByTexture;
    std::unordered_map<std::string, size_t> materialAliasCountByTexture;
    const std::filesystem::path sourceRoot =
        existingPathOrDevelopmentFallback((levelPhysicalPath.parent_path() / "../source").lexically_normal());
    std::unordered_map<std::string, std::vector<std::filesystem::path>> scratchSourceDtxIndex;
    const std::unordered_map<std::string, std::vector<std::filesystem::path>> &sourceDtxIndex =
        mm9SourceDtxIndex(sourceRoot, pCache, scratchSourceDtxIndex);
    const std::unordered_map<std::string, std::vector<std::filesystem::path>> sourceSpriteIndex =
        buildMm9SourceSpriteIndex(sourceRoot);
    const std::vector<Mm9SourceAssetAliasOverride> sourceAssetAliases =
        loadMm9SourceAssetAliasOverrides(levelPhysicalPath, pMetadata);

    for (const EditorMm9DatWorldModelSummary &model : datWorld.worldModels)
    {
        const bool defaultRenderable = mm9DatWorldModelRendersInDefaultView(model);

        for (const EditorMm9DatWorldModelTexture &texture : model.textures)
        {
            const std::string textureKey = normalizedTextureKey(texture.sourceTexture);
            ++datReferenceCountByTexture[textureKey];

            if (defaultRenderable)
            {
                ++defaultRenderableDatReferenceCountByTexture[textureKey];
            }
            else
            {
                ++helperOnlyDatReferenceCountByTexture[textureKey];
            }
        }
    }

    for (const EditorMm9MaterialTexture &texture : materialAliases.textures)
    {
        ++materialAliasCountByTexture[normalizedTextureKey(texture.sourceTexture)];
    }

    std::vector<EditorMm9MaterialTextureStatus> statuses;
    statuses.reserve(materialAliases.textures.size());

    for (size_t textureIndex = 0; textureIndex < materialAliases.textures.size(); ++textureIndex)
    {
        const EditorMm9MaterialTexture &texture = materialAliases.textures[textureIndex];
        const std::string textureKey = normalizedTextureKey(texture.sourceTexture);
        const std::string sourceDtxKey = mm9DtxSourceKeyFromReference(
            texture.physicalPath.empty() ? texture.sourceTexture : texture.physicalPath);
        const bool spriteReference = isMm9SpriteReference(texture.sourceTexture);
        const std::filesystem::path sourcePath = existingPathOrDevelopmentFallback(
            resolveMm9MaterialPhysicalPath(levelPhysicalPath, texture.physicalPath.empty()
                ? texture.sourceTexture
                : texture.physicalPath));
        const std::filesystem::path cachePath =
            resolveMm9MaterialCachePath(levelPhysicalPath, texture.emittedBitmap);

        EditorMm9MaterialTextureStatus status = {};
        status.textureIndex = textureIndex;
        status.alias = texture.alias;
        status.sourceTexture = texture.sourceTexture;
        status.sourceAssetFamily = spriteReference ? "sprites" : "dtx";
        status.physicalPath = texture.physicalPath;
        status.resolvedSourcePath = sourcePath.generic_string();
        status.emittedBitmap = texture.emittedBitmap;
        status.resolvedCachePath = cachePath.generic_string();
        status.emittedBitmapMode = texture.emittedBitmapMode;
        status.materialAliasEntry = true;
        status.aliasFieldPresent = texture.aliasFieldPresent;
        status.sourceTextureFieldPresent = texture.sourceTextureFieldPresent;
        status.emittedBitmapFieldPresent = texture.emittedBitmapFieldPresent;
        status.emittedBitmapModeFieldPresent = texture.emittedBitmapModeFieldPresent;
        status.datReferenceCount = datReferenceCountByTexture[textureKey];
        status.defaultRenderableDatReferenceCount = defaultRenderableDatReferenceCountByTexture[textureKey];
        status.helperOnlyDatReferenceCount = helperOnlyDatReferenceCountByTexture[textureKey];
        status.materialAliasCountForSource = materialAliasCountByTexture[textureKey];
        status.placeholderMissingSource = texture.emittedBitmapMode == "placeholder_missing_source";
        status.defaultHelperMaterial =
            status.placeholderMissingSource
            && isMm9DefaultMaterialTextureKey(textureKey)
            && status.datReferenceCount > 0
            && status.defaultRenderableDatReferenceCount == 0;

        if (status.defaultHelperMaterial)
        {
            status.sourceAssetFamily = "builtin";
            status.resolutionSource = "lithtech_default_helper_material";
            status.resolvedSourcePath.clear();
        }

        status.cachePathExists = !cachePath.empty() && pathExists(cachePath);

        if (status.cachePathExists)
        {
            const EditorMm9FileInspectionCacheEntry cacheInspection =
                inspectMm9File(cachePath, true, false, pCache);
            status.cacheSizeBytes = cacheInspection.sizeBytes;
            status.cacheHashLoaded = cacheInspection.hashLoaded;
            status.cacheSha256 = cacheInspection.sha256;
        }

        if (status.defaultHelperMaterial)
        {
            statuses.push_back(std::move(status));
            continue;
        }

        if (spriteReference)
        {
            const std::string sourceSpriteKey = mm9SpriteSourceKeyFromReference(texture.sourceTexture);
            const auto sourceSpriteIterator = sourceSpriteIndex.find(sourceSpriteKey);

            if (sourceSpriteIterator != sourceSpriteIndex.end())
            {
                status.sourceSpriteCandidateCount = sourceSpriteIterator->second.size();
                status.sourceSpriteResolved = status.sourceSpriteCandidateCount == 1;
                status.sourceSpriteAmbiguous = status.sourceSpriteCandidateCount > 1;

                for (const std::filesystem::path &candidatePath : sourceSpriteIterator->second)
                {
                    status.sourceSpriteCandidates.push_back(candidatePath.generic_string());
                }

                if (status.sourceSpriteResolved)
                {
                    status.resolvedSpritePath = sourceSpriteIterator->second.front().generic_string();
                    status.sourceSpritePathExists = pathExists(sourceSpriteIterator->second.front());
                    status.resolvedSourcePath = status.resolvedSpritePath;
                }
            }

            if (status.sourceSpritePathExists)
            {
                std::vector<std::string> spriteFrameTextureRefs;
                status.sourceSpriteParsed =
                    readMm9SpriteTextureRefs(std::filesystem::path(status.resolvedSpritePath), spriteFrameTextureRefs);

                if (status.sourceSpriteParsed)
                {
                    status.spriteFrameTextureRefs = spriteFrameTextureRefs;
                    status.spriteFrameTextureCount = spriteFrameTextureRefs.size();

                    for (const std::string &spriteFrameTextureRef : spriteFrameTextureRefs)
                    {
                        const std::string spriteFrameDtxKey =
                            mm9DtxSourceKeyFromReference(spriteFrameTextureRef);
                        const std::vector<std::filesystem::path> *pSpriteFrameDtxCandidates =
                            findMm9DtxSourceCandidates(sourceDtxIndex, spriteFrameDtxKey);

                        if (pSpriteFrameDtxCandidates == nullptr)
                        {
                            ++status.unresolvedSpriteFrameTextureCount;
                            status.unresolvedSpriteFrameTextureRefs.push_back(spriteFrameTextureRef);
                        }
                        else if (pSpriteFrameDtxCandidates->size() > 1)
                        {
                            ++status.ambiguousSpriteFrameTextureCount;
                            status.ambiguousSpriteFrameTextureRefs.push_back(spriteFrameTextureRef);
                        }
                        else
                        {
                            ++status.resolvedSpriteFrameTextureCount;
                            status.resolvedSpriteFrameTexturePaths.push_back(
                                pSpriteFrameDtxCandidates->front().generic_string());
                        }
                    }
                }
            }
        }
        else
        {
            const std::vector<std::filesystem::path> *pSourceDtxCandidates =
                findMm9DtxSourceCandidates(sourceDtxIndex, sourceDtxKey);

            if (pSourceDtxCandidates == nullptr)
            {
                for (const Mm9SourceAssetAliasOverride &alias : sourceAssetAliases)
                {
                    if (!mm9MaterialSourceAssetAliasMatches(alias, pMetadata, sourceDtxKey))
                    {
                        continue;
                    }

                    status.aliasApplied = true;
                    status.aliasTargetKey = alias.targetKey;
                    status.resolutionSource = "source_asset_alias";
                    pSourceDtxCandidates =
                        findMm9DtxSourceCandidates(
                            sourceDtxIndex,
                            mm9DtxSourceKeyFromTextureAliasTarget(alias.targetKey));
                    break;
                }
            }

            if (pSourceDtxCandidates != nullptr)
            {
                status.sourceDtxCandidateCount = pSourceDtxCandidates->size();
                status.sourceDtxResolved = status.sourceDtxCandidateCount == 1;
                status.sourceDtxAmbiguous = status.sourceDtxCandidateCount > 1;

                for (const std::filesystem::path &candidatePath : *pSourceDtxCandidates)
                {
                    status.sourceDtxCandidates.push_back(candidatePath.generic_string());
                }

                if (status.sourceDtxResolved)
                {
                    status.resolvedSourcePath = pSourceDtxCandidates->front().generic_string();
                }

                if (status.resolutionSource.empty())
                {
                    status.resolutionSource = "source_index";
                }
            }
        }

        status.sourcePathExists = !status.resolvedSourcePath.empty()
            && pathExists(std::filesystem::path(status.resolvedSourcePath));

        if (status.sourceDtxResolved && status.sourcePathExists)
        {
            const std::filesystem::path resolvedSourcePath(status.resolvedSourcePath);
            const EditorMm9FileInspectionCacheEntry sourceInspection =
                inspectMm9File(resolvedSourcePath, true, true, pCache);
            status.sourceDtxSizeBytes = sourceInspection.sizeBytes;
            status.sourceDtxHashLoaded = sourceInspection.hashLoaded;
            status.sourceDtxSha256 = sourceInspection.sha256;

            if (status.cachePathExists)
            {
                compareFileFreshness(
                    resolvedSourcePath,
                    cachePath,
                    status.cacheFreshnessKnown,
                    status.cacheNewerThanSource,
                    status.cacheOlderThanSource);
            }

            status.dtxHeader = sourceInspection.dtxHeader;
            status.dtxHeaderLoaded = status.dtxHeader.has_value();

            if (status.dtxHeader)
            {
                const EditorMm9DtxHeader &header = *status.dtxHeader;
                status.dtxHeaderMatchesSidecar =
                    header.width == texture.width
                    && header.height == texture.height
                    && header.surfaceFlag == texture.dtxSurfaceFlag
                    && header.textureGroup == texture.dtxTextureGroup
                    && header.bpp == texture.dtxBpp
                    && header.mipmapCount == texture.dtxMipmapCount
                    && header.mipmapsUsed == texture.dtxMipmapsUsed
                    && header.flags == texture.dtxFlags
                    && header.detailAngle == texture.dtxDetailAngle
                    && header.commandString == texture.dtxCommandString;
            }

            inspectMm9DecodedMaterialCacheDeterminism(status, resolvedSourcePath, cachePath);
        }

        statuses.push_back(std::move(status));
    }

    for (const std::pair<const std::string, size_t> &datReference : datReferenceCountByTexture)
    {
        if (materialAliasCountByTexture[datReference.first] != 0)
        {
            continue;
        }

        EditorMm9MaterialTextureStatus status = {};
        status.textureIndex = statuses.size();
        status.sourceTexture = datReference.first;
        status.datReferenceCount = datReference.second;
        status.defaultRenderableDatReferenceCount = defaultRenderableDatReferenceCountByTexture[datReference.first];
        status.helperOnlyDatReferenceCount = helperOnlyDatReferenceCountByTexture[datReference.first];
        status.materialAliasCountForSource = 0;
        status.defaultHelperMaterial =
            isMm9DefaultMaterialTextureKey(datReference.first)
            && status.datReferenceCount > 0
            && status.defaultRenderableDatReferenceCount == 0;

        if (status.defaultHelperMaterial)
        {
            status.sourceAssetFamily = "builtin";
            status.resolutionSource = "lithtech_default_helper_material";
            statuses.push_back(std::move(status));
            continue;
        }

        const std::string sourceDtxKey = mm9DtxSourceKeyFromReference(datReference.first);
        const std::vector<std::filesystem::path> *pSourceDtxCandidates =
            findMm9DtxSourceCandidates(sourceDtxIndex, sourceDtxKey);

        if (pSourceDtxCandidates == nullptr)
        {
            for (const Mm9SourceAssetAliasOverride &alias : sourceAssetAliases)
            {
                if (!mm9MaterialSourceAssetAliasMatches(alias, pMetadata, sourceDtxKey))
                {
                    continue;
                }

                status.aliasApplied = true;
                status.aliasTargetKey = alias.targetKey;
                status.resolutionSource = "source_asset_alias";
                pSourceDtxCandidates =
                    findMm9DtxSourceCandidates(
                        sourceDtxIndex,
                        mm9DtxSourceKeyFromTextureAliasTarget(alias.targetKey));
                break;
            }
        }

        if (pSourceDtxCandidates != nullptr)
        {
            status.sourceDtxCandidateCount = pSourceDtxCandidates->size();
            status.sourceDtxResolved = status.sourceDtxCandidateCount == 1;
            status.sourceDtxAmbiguous = status.sourceDtxCandidateCount > 1;

            for (const std::filesystem::path &candidatePath : *pSourceDtxCandidates)
            {
                status.sourceDtxCandidates.push_back(candidatePath.generic_string());
            }

            if (status.sourceDtxResolved)
            {
                status.resolvedSourcePath = pSourceDtxCandidates->front().generic_string();
                status.sourcePathExists = pathExists(pSourceDtxCandidates->front());

                if (status.resolutionSource.empty())
                {
                    status.resolutionSource = "source_index";
                }

                if (status.sourcePathExists)
                {
                    const EditorMm9FileInspectionCacheEntry sourceInspection =
                        inspectMm9File(pSourceDtxCandidates->front(), true, false, pCache);
                    status.sourceDtxSizeBytes = sourceInspection.sizeBytes;
                    status.sourceDtxHashLoaded = sourceInspection.hashLoaded;
                    status.sourceDtxSha256 = sourceInspection.sha256;
                }
            }
        }

        statuses.push_back(std::move(status));
    }

    return statuses;
}

std::vector<std::string> validateMm9MaterialTextureReferences(
    const std::vector<EditorMm9MaterialTextureStatus> &statuses)
{
    std::vector<std::string> issues;

    for (const EditorMm9MaterialTextureStatus &status : statuses)
    {
        if (status.materialAliasEntry && (!status.aliasFieldPresent || status.alias.empty()))
        {
            issues.push_back(
                "MM9 material alias is missing DAT texture alias at row "
                + std::to_string(status.textureIndex));
        }

        if (status.materialAliasEntry && (!status.sourceTextureFieldPresent || status.sourceTexture.empty()))
        {
            issues.push_back(
                "MM9 material alias is missing source_texture: alias=" + status.alias);
        }

        if (status.materialAliasEntry && (!status.emittedBitmapFieldPresent || status.emittedBitmap.empty()))
        {
            issues.push_back(
                "MM9 material alias is missing emitted_bitmap: alias=" + status.alias);
        }

        if (status.materialAliasEntry && (!status.emittedBitmapModeFieldPresent || status.emittedBitmapMode.empty()))
        {
            issues.push_back(
                "MM9 material alias is missing emitted_bitmap_mode: alias=" + status.alias);
        }

        if (status.datReferenceCount > 0 && status.materialAliasCountForSource == 0)
        {
            issues.push_back(
                "MM9 DAT texture reference has no material alias: " + status.sourceTexture);
        }

        if (status.materialAliasCountForSource > 1)
        {
            issues.push_back(
                "MM9 DAT texture reference has ambiguous material aliases: " + status.sourceTexture);
        }

        if (status.defaultHelperMaterial)
        {
            continue;
        }

        if (status.sourceAssetFamily == "sprites")
        {
            if (status.placeholderMissingSource)
            {
                continue;
            }

            if (status.datReferenceCount > 0
                && status.sourceSpriteCandidateCount == 0)
            {
                issues.push_back(
                    "MM9 DAT sprite material reference resolves to no source SPR: " + status.sourceTexture
                    + " resolved=" + status.resolvedSourcePath);
            }

            if (status.datReferenceCount > 0 && status.sourceSpriteAmbiguous)
            {
                std::string issue =
                    "MM9 DAT sprite material reference resolves to ambiguous source SPR files: "
                    + status.sourceTexture;

                for (const std::string &candidate : status.sourceSpriteCandidates)
                {
                    issue += " candidate=" + candidate;
                }

                issues.push_back(issue);
            }

            if (status.datReferenceCount > 0
                && status.sourceSpriteResolved
                && !status.sourceSpritePathExists)
            {
                issues.push_back(
                    "MM9 DAT sprite material source SPR is missing: " + status.sourceTexture
                    + " resolved=" + status.resolvedSpritePath);
            }

            if (status.datReferenceCount > 0
                && status.sourceSpritePathExists
                && !status.sourceSpriteParsed)
            {
                issues.push_back(
                    "MM9 DAT sprite material source SPR could not be parsed: " + status.resolvedSpritePath);
            }

            if (status.datReferenceCount > 0
                && status.unresolvedSpriteFrameTextureCount != 0)
            {
                std::string issue =
                    "MM9 DAT sprite material frame texture resolves to no source DTX: "
                    + status.sourceTexture;

                for (const std::string &frameTexture : status.unresolvedSpriteFrameTextureRefs)
                {
                    issue += " frame=" + frameTexture;
                }

                issues.push_back(issue);
            }

            if (status.datReferenceCount > 0
                && status.ambiguousSpriteFrameTextureCount != 0)
            {
                std::string issue =
                    "MM9 DAT sprite material frame texture resolves to ambiguous source DTX: "
                    + status.sourceTexture;

                for (const std::string &frameTexture : status.ambiguousSpriteFrameTextureRefs)
                {
                    issue += " frame=" + frameTexture;
                }

                issues.push_back(issue);
            }

            continue;
        }

        if (status.datReferenceCount > 0
            && !status.placeholderMissingSource
            && status.sourceDtxCandidateCount == 0)
        {
            issues.push_back(
                "MM9 DAT texture reference resolves to no source DTX: " + status.sourceTexture
                + " resolved=" + status.resolvedSourcePath);
        }

        if (status.datReferenceCount > 0 && status.sourceDtxAmbiguous)
        {
            std::string issue =
                "MM9 DAT texture reference resolves to ambiguous source DTX files: " + status.sourceTexture;

            for (const std::string &candidate : status.sourceDtxCandidates)
            {
                issue += " candidate=" + candidate;
            }

            issues.push_back(issue);
        }

        if (status.datReferenceCount > 0
            && !status.placeholderMissingSource
            && status.sourceDtxResolved
            && !status.sourcePathExists)
        {
            issues.push_back(
                "MM9 DAT texture source DTX is missing: " + status.sourceTexture
                + " resolved=" + status.resolvedSourcePath);
        }

        if (status.sourcePathExists && !status.dtxHeaderLoaded && !status.placeholderMissingSource)
        {
            issues.push_back(
                "MM9 DAT texture source DTX header could not be loaded: " + status.resolvedSourcePath);
        }

        if (status.dtxHeaderLoaded && !status.dtxHeaderMatchesSidecar && !status.placeholderMissingSource)
        {
            issues.push_back(
                "MM9 DAT texture source DTX header differs from material sidecar: " + status.sourceTexture);
        }

        if (status.cacheDeterminismChecked && !status.cacheMatchesDecodedSource)
        {
            issues.push_back(
                "MM9 DAT texture generated cache is not deterministic from decoded source DTX: "
                + status.sourceTexture + " reason=" + status.cacheDeterminismMessage);
        }
    }

    return issues;
}

std::vector<std::string> validateMm9RawObjectsSidecarReferences(const EditorMm9RawObjectsSidecar &sidecar)
{
    std::vector<std::string> issues;

    if (sidecar.objectCount != sidecar.objects.size())
    {
        issues.push_back(
            "MM9 raw objects sidecar object_count mismatch: stored="
            + std::to_string(sidecar.objectCount)
            + " actual=" + std::to_string(sidecar.objects.size()));
    }

    size_t unknownPropertyCount = 0;

    for (size_t objectRow = 0; objectRow < sidecar.objects.size(); ++objectRow)
    {
        const EditorMm9RawObject &object = sidecar.objects[objectRow];

        if (object.objectIndex != objectRow)
        {
            issues.push_back(
                "MM9 raw object index mismatch at row " + std::to_string(objectRow)
                + ": object_index=" + std::to_string(object.objectIndex));
        }

        if (object.propertyCount != object.properties.size())
        {
            issues.push_back(
                "MM9 raw object " + std::to_string(object.objectIndex)
                + " property_count mismatch: stored=" + std::to_string(object.propertyCount)
                + " actual=" + std::to_string(object.properties.size()));
        }

        size_t consumedObjectPayloadBytes = 0;

        for (size_t propertyIndex = 0; propertyIndex < object.properties.size(); ++propertyIndex)
        {
            const EditorMm9RawObjectProperty &property = object.properties[propertyIndex];
            consumedObjectPayloadBytes += property.consumedDataLength;

            if (!property.decoded)
            {
                ++unknownPropertyCount;
            }

            if ((property.rawHex.size() % 2) != 0)
            {
                issues.push_back(
                    "MM9 raw object " + std::to_string(object.objectIndex)
                    + " property " + std::to_string(propertyIndex)
                    + " raw hex has an odd number of characters.");
            }

            if (!isHexString(property.rawHex))
            {
                issues.push_back(
                    "MM9 raw object " + std::to_string(object.objectIndex)
                    + " property " + std::to_string(propertyIndex)
                    + " raw hex contains non-hex characters.");
            }

            if (property.rawHex.size() != property.consumedDataLength * 2)
            {
                issues.push_back(
                    "MM9 raw object " + std::to_string(object.objectIndex)
                    + " property " + std::to_string(propertyIndex)
                    + " raw hex length does not match consumed length.");
            }

            if (property.name.empty())
            {
                issues.push_back(
                    "MM9 raw object " + std::to_string(object.objectIndex)
                    + " property " + std::to_string(propertyIndex)
                    + " name is empty.");
            }
        }

        if ((object.trailingHex.size() % 2) != 0)
        {
            issues.push_back(
                "MM9 raw object " + std::to_string(object.objectIndex)
                + " trailing hex has an odd number of characters.");
        }

        if (!isHexString(object.trailingHex))
        {
            issues.push_back(
                "MM9 raw object " + std::to_string(object.objectIndex)
                + " trailing hex contains non-hex characters.");
        }

        consumedObjectPayloadBytes += object.trailingHex.size() / 2;

        if (consumedObjectPayloadBytes > object.dataLength)
        {
            issues.push_back(
                "MM9 raw object " + std::to_string(object.objectIndex)
                + " decoded payload exceeds data_length: stored=" + std::to_string(object.dataLength)
                + " payload=" + std::to_string(consumedObjectPayloadBytes));
        }
    }

    if (unknownPropertyCount != sidecar.unknownPropertyCount)
    {
        issues.push_back(
            "MM9 raw objects sidecar unknown_property_count mismatch: stored="
            + std::to_string(sidecar.unknownPropertyCount)
            + " actual=" + std::to_string(unknownPropertyCount));
    }

    return issues;
}

std::vector<EditorMm9RawObjectAssetReferenceStatus> inspectMm9RawObjectAssetReferences(
    const std::filesystem::path &levelPhysicalPath,
    const EditorMm9RawObjectsSidecar &rawObjects,
    const EditorMm9DatLevelMetadata *pMetadata)
{
    std::vector<EditorMm9RawObjectAssetReferenceStatus> statuses;
    std::unordered_map<std::string, std::unordered_map<std::string, std::vector<std::filesystem::path>>> indexes;
    const std::filesystem::path sourceRoot =
        existingPathOrDevelopmentFallback((levelPhysicalPath.parent_path() / "../source").lexically_normal());
    const std::vector<Mm9SourceAssetAliasOverride> sourceAssetAliases =
        loadMm9SourceAssetAliasOverrides(levelPhysicalPath, pMetadata);

    for (const EditorMm9RawObject &object : rawObjects.objects)
    {
        for (size_t propertyIndex = 0; propertyIndex < object.properties.size(); ++propertyIndex)
        {
            const EditorMm9RawObjectProperty &property = object.properties[propertyIndex];
            const std::optional<std::string> decodedValue = decodedRawObjectStringValue(property);

            if (!decodedValue || decodedValue->empty())
            {
                continue;
            }

            const std::string objectName = [&object]()
            {
                for (const EditorMm9RawObjectProperty &candidate : object.properties)
                {
                    if (candidate.name != "Name")
                    {
                        continue;
                    }

                    const std::optional<std::string> nameValue = decodedRawObjectStringValue(candidate);
                    return nameValue ? *nameValue : std::string();
                }

                return std::string();
            }();

            for (const std::string &assetValue : splitMm9AssetReferenceList(*decodedValue))
            {
                const std::string sourceFamily =
                    inferMm9RawObjectAssetFamily(property.name, assetValue);

                if (sourceFamily.empty())
                {
                    continue;
                }

                if (indexes.find(sourceFamily) == indexes.end())
                {
                    indexes[sourceFamily] = buildMm9SourceFamilyIndex(sourceRoot, sourceFamily);
                }

                EditorMm9RawObjectAssetReferenceStatus status = {};
                status.sourceObjectIndex = object.objectIndex;
                status.sourceClass = object.name;
                status.objectName = objectName;
                status.propertyIndex = propertyIndex;
                status.propertyName = property.name;
                status.sourceFamily = sourceFamily;
                status.sourceValue = assetValue;
                status.normalizedKey = normalizedMm9SourceAssetKey(sourceFamily, assetValue);
                status.required =
                    isMm9RawObjectAssetReferenceRequired(object.name, property.name, sourceFamily);

                const std::unordered_map<std::string, std::vector<std::filesystem::path>> &familyIndex =
                    indexes[sourceFamily];
                const std::vector<std::filesystem::path> *pCandidates =
                    findMm9SourceFamilyCandidates(familyIndex, sourceFamily, status.normalizedKey);

                if (pCandidates == nullptr)
                {
                    for (const Mm9SourceAssetAliasOverride &alias : sourceAssetAliases)
                    {
                        if (!mm9SourceAssetAliasMatches(alias, pMetadata, status))
                        {
                            continue;
                        }

                        status.aliasApplied = true;
                        status.aliasTargetKey = alias.targetKey;
                        status.resolutionSource = "source_asset_alias";
                        pCandidates = findMm9SourceFamilyCandidates(familyIndex, sourceFamily, alias.targetKey);
                        break;
                    }
                }

                if (pCandidates == nullptr && isMm9WorldPropertiesBuiltinSkyTextureReference(status))
                {
                    status.resolved = true;
                    status.builtinReference = true;
                    status.resolutionSource = "lithtech_world_properties_sky_builtin";
                    statuses.push_back(std::move(status));
                    continue;
                }

                if (pCandidates != nullptr)
                {
                    status.resolved = pCandidates->size() == 1;
                    status.ambiguous = pCandidates->size() > 1;

                    for (const std::filesystem::path &candidatePath : *pCandidates)
                    {
                        status.sourceCandidates.push_back(candidatePath.generic_string());
                    }

                    if (status.resolved)
                    {
                        status.resolvedSourcePath = pCandidates->front().generic_string();
                    }

                    if (status.resolutionSource.empty())
                    {
                        status.resolutionSource = "source_index";
                    }
                }

                statuses.push_back(std::move(status));
            }
        }
    }

    return statuses;
}

std::vector<std::string> validateMm9RawObjectAssetReferences(
    const std::vector<EditorMm9RawObjectAssetReferenceStatus> &statuses)
{
    std::vector<std::string> issues;

    for (const EditorMm9RawObjectAssetReferenceStatus &status : statuses)
    {
        if (!status.required)
        {
            continue;
        }

        if (status.ambiguous)
        {
            std::string issue =
                "MM9 raw object asset reference is ambiguous: object="
                + std::to_string(status.sourceObjectIndex)
                + " property=" + status.propertyName
                + " family=" + status.sourceFamily
                + " value=" + status.sourceValue;

            for (const std::string &candidate : status.sourceCandidates)
            {
                issue += " candidate=" + candidate;
            }

            issues.push_back(issue);
            continue;
        }

        if (!status.resolved)
        {
            issues.push_back(
                "MM9 raw object asset reference is unresolved: object="
                + std::to_string(status.sourceObjectIndex)
                + " property=" + status.propertyName
                + " family=" + status.sourceFamily
                + " value=" + status.sourceValue
                + " key=" + status.normalizedKey);
        }
    }

    return issues;
}

EditorMm9AssetDependencyFamilySummary &findOrCreateAssetDependencyFamily(
    EditorMm9AssetDependencySummary &summary,
    const std::string &family)
{
    for (EditorMm9AssetDependencyFamilySummary &familySummary : summary.families)
    {
        if (familySummary.family == family)
        {
            return familySummary;
        }
    }

    EditorMm9AssetDependencyFamilySummary familySummary = {};
    familySummary.family = family;
    summary.families.push_back(std::move(familySummary));
    return summary.families.back();
}

void addAssetDependency(
    EditorMm9AssetDependencySummary &summary,
    const std::string &family,
    bool resolved,
    bool ambiguous,
    bool stale,
    bool required = true)
{
    EditorMm9AssetDependencyFamilySummary &familySummary =
        findOrCreateAssetDependencyFamily(summary, family);

    ++summary.total;
    ++familySummary.total;

    if (required)
    {
        ++summary.requiredTotal;
        ++familySummary.requiredTotal;
    }
    else
    {
        ++summary.optionalTotal;
        ++familySummary.optionalTotal;
    }

    if (ambiguous)
    {
        ++summary.ambiguous;
        ++familySummary.ambiguous;

        if (required)
        {
            ++summary.requiredAmbiguous;
            ++familySummary.requiredAmbiguous;
        }
        else
        {
            ++summary.optionalAmbiguous;
            ++familySummary.optionalAmbiguous;
        }
    }
    else if (resolved)
    {
        ++summary.resolved;
        ++familySummary.resolved;

        if (required)
        {
            ++summary.requiredResolved;
            ++familySummary.requiredResolved;
        }
        else
        {
            ++summary.optionalResolved;
            ++familySummary.optionalResolved;
        }
    }
    else
    {
        ++summary.unresolved;
        ++familySummary.unresolved;

        if (required)
        {
            ++summary.requiredUnresolved;
            ++familySummary.requiredUnresolved;
        }
        else
        {
            ++summary.optionalUnresolved;
            ++familySummary.optionalUnresolved;
        }
    }

    if (stale)
    {
        ++summary.stale;
        ++familySummary.stale;
    }
}

void addAssetSourceInventory(
    EditorMm9AssetDependencySummary &summary,
    const EditorMm9SourceAssetFamilyStatus &status)
{
    if (!status.declared || status.actualFileCount == 0)
    {
        return;
    }

    EditorMm9AssetDependencyFamilySummary &familySummary =
        findOrCreateAssetDependencyFamily(summary, status.id);
    const size_t referencedSourceCount = std::min(familySummary.total, status.actualFileCount);
    const size_t unusedSourceCount = status.actualFileCount - referencedSourceCount;

    summary.sourceOnly += status.actualFileCount;
    familySummary.sourceOnly += status.actualFileCount;
    summary.unusedSource += unusedSourceCount;
    familySummary.unusedSource += unusedSourceCount;
}

EditorMm9AssetDependencySummary summarizeMm9AssetDependencies(
    const std::filesystem::path &levelPhysicalPath,
    const EditorMm9DatLevelMetadata &metadata,
    const std::vector<EditorMm9MaterialTextureStatus> &materialStatuses,
    const std::vector<EditorMm9RawObjectAssetReferenceStatus> &rawObjectAssetStatuses,
    const std::vector<EditorMm9SourceAssetFamilyStatus> &sourceFamilyStatuses)
{
    EditorMm9AssetDependencySummary summary = {};

    const std::filesystem::path sourceDatPath =
        resolveMm9DatLevelRelativePath(levelPhysicalPath, metadata.source.dat);
    addAssetDependency(summary, "worlds", pathExists(sourceDatPath), false, false);

    const std::array<std::pair<const char *, std::string>, 4> sidecars = {{
        {"sidecars", metadata.sidecars.datWorld},
        {"sidecars", metadata.sidecars.rawObjects},
        {"sidecars", metadata.sidecars.materials},
        {"sidecars", metadata.sidecars.events}
    }};

    for (const std::pair<const char *, std::string> &sidecar : sidecars)
    {
        const std::filesystem::path sidecarPath =
            resolveMm9DatLevelRelativePath(levelPhysicalPath, sidecar.second);
        addAssetDependency(summary, sidecar.first, pathExists(sidecarPath), false, false);
    }

    if (metadata.sidecars.sourceAssetAliases.has_value() && !metadata.sidecars.sourceAssetAliases->empty())
    {
        const std::filesystem::path aliasesPath =
            resolveMm9DatLevelRelativePath(levelPhysicalPath, metadata.sidecars.sourceAssetAliases.value());
        addAssetDependency(summary, "authored_overrides", pathExists(aliasesPath), false, false);
    }

    const std::array<std::pair<const char *, std::string>, 2> generatedScripts = {{
        {"generated_events", metadata.scripts.level},
        {"generated_events", metadata.scripts.scriptIr}
    }};

    for (const std::pair<const char *, std::string> &script : generatedScripts)
    {
        const std::filesystem::path scriptPath =
            resolveMm9DatLevelRelativePath(levelPhysicalPath, script.second);
        addAssetDependency(summary, script.first, pathExists(scriptPath), false, false);
    }

    const std::filesystem::path sourceRoot =
        resolveMm9SourceAssetManifestPath(levelPhysicalPath, metadata).parent_path();
    const std::array<std::pair<const char *, const char *>, 2> sourceTableFamilies = {{
        {"data", "data"},
        {"rude", "rude"}
    }};

    for (const std::pair<const char *, const char *> &sourceFamily : sourceTableFamilies)
    {
        addAssetDependency(
            summary,
            sourceFamily.first,
            directoryExists(sourceRoot / sourceFamily.second),
            false,
            false);
    }

    for (const EditorMm9MaterialTextureStatus &status : materialStatuses)
    {
        if (status.defaultHelperMaterial)
        {
            if (!status.emittedBitmap.empty())
            {
                addAssetDependency(
                    summary,
                    "generated_caches",
                    status.cachePathExists,
                    false,
                    false,
                    false);
            }

            continue;
        }

        const bool requiredSource = status.datReferenceCount > 0 || !status.sourceTexture.empty();
        if (requiredSource)
        {
            bool resolved =
                status.sourceDtxResolved
                && status.sourcePathExists
                && status.dtxHeaderLoaded
                && status.dtxHeaderMatchesSidecar;

            if (status.placeholderMissingSource && !status.sourceDtxResolved)
            {
                resolved = false;
            }
            else if (status.placeholderMissingSource && status.sourceDtxResolved)
            {
                resolved = status.sourcePathExists && status.dtxHeaderLoaded;
            }

            if (status.sourceAssetFamily == "sprites")
            {
                resolved =
                    status.sourceSpriteResolved
                    && status.sourceSpritePathExists
                    && status.sourceSpriteParsed
                    && status.spriteFrameTextureCount != 0
                    && status.unresolvedSpriteFrameTextureCount == 0
                    && status.ambiguousSpriteFrameTextureCount == 0;
            }

            addAssetDependency(
                summary,
                status.sourceAssetFamily == "sprites" ? "sprites" : "textures",
                resolved,
                status.sourceDtxAmbiguous || status.sourceSpriteAmbiguous,
                false,
                !status.placeholderMissingSource);
        }

        if (!status.emittedBitmap.empty())
        {
            addAssetDependency(
                summary,
                "generated_caches",
                status.cachePathExists,
                false,
                status.cacheOlderThanSource,
                false);
        }
    }

    for (const EditorMm9RawObjectAssetReferenceStatus &status : rawObjectAssetStatuses)
    {
        addAssetDependency(
            summary,
            status.sourceFamily,
            status.resolved,
            status.ambiguous,
            false,
            status.required);
    }

    for (const EditorMm9SourceAssetFamilyStatus &status : sourceFamilyStatuses)
    {
        addAssetSourceInventory(summary, status);
    }

    std::sort(
        summary.families.begin(),
        summary.families.end(),
        [](const EditorMm9AssetDependencyFamilySummary &left,
           const EditorMm9AssetDependencyFamilySummary &right)
        {
            return left.family < right.family;
        });

    return summary;
}

std::vector<EditorMm9DocumentPathStatus> inspectMm9DatLevelDocumentPaths(
    const std::filesystem::path &levelPhysicalPath,
    const EditorMm9DatLevelMetadata &metadata,
    const std::vector<EditorMm9MaterialTextureStatus> &materialStatuses)
{
    std::vector<EditorMm9DocumentPathStatus> statuses;

    statuses.push_back(
        makeMm9DocumentAbsolutePathStatus(
            "level",
            "authored_or_generated_entrypoint",
            levelPhysicalPath,
            false,
            true,
            true,
            false));
    statuses.push_back(
        makeMm9DocumentPathStatus(
            "source_dat",
            "read_only_source",
            levelPhysicalPath,
            metadata.source.dat,
            true,
            false,
            false,
            false));
    statuses.push_back(
        makeMm9DocumentAbsolutePathStatus(
            "source_manifest",
            "read_only_source",
            resolveMm9SourceAssetManifestPath(levelPhysicalPath, metadata),
            true,
            false,
            false,
            false));

    const std::array<std::pair<const char *, std::string>, 4> sidecars = {{
        {"dat_world_sidecar", metadata.sidecars.datWorld},
        {"raw_objects_sidecar", metadata.sidecars.rawObjects},
        {"material_aliases_sidecar", metadata.sidecars.materials},
        {"events_sidecar", metadata.sidecars.events}
    }};

    for (const std::pair<const char *, std::string> &sidecar : sidecars)
    {
        statuses.push_back(
            makeMm9DocumentPathStatus(
                sidecar.first,
                "generated_sidecar",
                levelPhysicalPath,
                sidecar.second,
                false,
                true,
                false,
                false));
    }

    if (metadata.sidecars.sourceAssetAliases.has_value() && !metadata.sidecars.sourceAssetAliases->empty())
    {
        statuses.push_back(
            makeMm9DocumentPathStatus(
                "source_asset_aliases",
                "authored_override",
                levelPhysicalPath,
                metadata.sidecars.sourceAssetAliases.value(),
                false,
                false,
                true,
                false));
    }

    statuses.push_back(
        makeMm9DocumentPathStatus(
            "level_lua",
            "generated_event_script",
            levelPhysicalPath,
            metadata.scripts.level,
            false,
            true,
            false,
            false));
    statuses.push_back(
        makeMm9DocumentPathStatus(
            "script_ir",
            "generated_event_script",
            levelPhysicalPath,
            metadata.scripts.scriptIr,
            false,
            true,
            false,
            false));

    const std::array<std::pair<const char *, const std::optional<std::string> *>, 7> compatibilityPaths = {{
        {"scene_compat", &metadata.sidecars.sceneCompat},
        {"source_metadata_compat", &metadata.sidecars.sourceMetadataCompat},
        {"bsp_compat", &metadata.sidecars.bspCompat},
        {"geometry_compat", &metadata.sidecars.geometryCompat},
        {"model_assets_compat", &metadata.sidecars.modelAssetsCompat},
        {"odm_compat", &metadata.sidecars.odmCompat},
        {"blv_compat", &metadata.sidecars.blvCompat}
    }};

    for (const std::pair<const char *, const std::optional<std::string> *> &compatibilityPath : compatibilityPaths)
    {
        if (!compatibilityPath.second->has_value() || compatibilityPath.second->value().empty())
        {
            continue;
        }

        statuses.push_back(
            makeMm9DocumentPathStatus(
                compatibilityPath.first,
                "derived_compatibility_artifact",
                levelPhysicalPath,
                compatibilityPath.second->value(),
                false,
                true,
                false,
                true));
    }

    for (const EditorMm9MaterialTextureStatus &materialStatus : materialStatuses)
    {
        if (materialStatus.emittedBitmap.empty())
        {
            continue;
        }

        statuses.push_back(
            makeMm9DocumentPathStatus(
                "material_cache",
                "generated_cache",
                levelPhysicalPath,
                materialStatus.emittedBitmap,
                false,
                true,
                false,
                false));
    }

    return statuses;
}

bool isMm9DocumentPathRequired(const EditorMm9DocumentPathStatus &status)
{
    return status.role != "generated_cache" && !status.compatibilityDerived;
}

std::vector<std::string> validateMm9DatLevelDocumentPathRoles(
    const std::vector<EditorMm9DocumentPathStatus> &statuses)
{
    std::vector<std::string> issues;

    for (const EditorMm9DocumentPathStatus &status : statuses)
    {
        const std::filesystem::path resolvedPath(status.resolvedPath);

        if (status.sourceReadOnly && !pathHasSegment(resolvedPath, "source"))
        {
            issues.push_back(
                "MM9 document read-only source path is outside source/*: "
                + status.label + " path=" + status.resolvedPath);
        }

        if (!status.sourceReadOnly && pathHasSegment(resolvedPath, "source"))
        {
            issues.push_back(
                "MM9 document writable/generated path must not be under source/*: "
                + status.label + " path=" + status.resolvedPath);
        }

        if (status.compatibilityDerived && !status.generated)
        {
            issues.push_back(
                "MM9 document compatibility artifact must be generated: "
                + status.label + " path=" + status.resolvedPath);
        }
    }

    return issues;
}

const std::vector<EditorMm9DiagnosticSeverityRule> &mm9DiagnosticSeverityRules()
{
    static const std::vector<EditorMm9DiagnosticSeverityRule> rules = {
        {
            "error",
            "parse failure, invalid source index/reference, unresolved required asset or target, ambiguous required "
            "asset or target, generated sidecar data loss/cross-link drift, stale hash/cache mismatch, source mutation",
            true,
            "parser/source asset mirror/sidecar generator/authored override"
        },
        {
            "warning",
            "unused or source-only asset, unresolved optional asset or target, optional preview cache missing, "
            "placeholder preview material, unsupported preview-only metadata",
            false,
            "source asset mirror/sidecar generator"
        },
        {
            "info",
            "derived compatibility artifact missing, cache regenerated/refreshed, optional authored override absent",
            false,
            "sidecar generator/authored override"
        }
    };

    return rules;
}

const std::vector<std::filesystem::path> *findMm9EventScriptSourceCandidates(
    const std::unordered_map<std::string, std::vector<std::filesystem::path>> &scriptIndex,
    const std::string &sourcePath)
{
    const std::string normalizedKey = normalizedMm9SourceAssetKey("scripts", sourcePath);

    if (normalizedKey.empty())
    {
        return nullptr;
    }

    return findMm9SourceFamilyCandidates(scriptIndex, "scripts", normalizedKey);
}

std::unordered_map<std::string, std::vector<std::filesystem::path>> buildMm9EventScriptSourceIndex(
    const std::filesystem::path &levelPhysicalPath)
{
    const std::filesystem::path sourceRoot =
        existingPathOrDevelopmentFallback((levelPhysicalPath.parent_path() / "../source").lexically_normal());
    return buildMm9SourceFamilyIndex(sourceRoot, "scripts");
}

EditorMm9ScriptIncludeResolutionSummary summarizeMm9EventScriptIncludeResolution(
    const std::filesystem::path &levelPhysicalPath,
    const Game::Mm9EventsData &events)
{
    EditorMm9ScriptIncludeResolutionSummary summary = {};
    const std::unordered_map<std::string, std::vector<std::filesystem::path>> scriptIndex =
        buildMm9EventScriptSourceIndex(levelPhysicalPath);

    for (const Game::Mm9EventScript &script : events.scripts)
    {
        for (const Game::Mm9EventScript::Include &include : script.includes)
        {
            ++summary.references;

            const std::vector<std::filesystem::path> *pCandidates =
                findMm9EventScriptSourceCandidates(scriptIndex, include.path);

            if (pCandidates == nullptr || pCandidates->empty())
            {
                ++summary.unresolved;
            }
            else if (pCandidates->size() > 1)
            {
                ++summary.ambiguous;
            }
            else
            {
                ++summary.resolved;
            }
        }
    }

    return summary;
}

std::vector<std::string> validateMm9EventsReferences(
    const std::filesystem::path &levelPhysicalPath,
    const EditorMm9DatLevelMetadata &metadata,
    const EditorMm9DatWorldSidecar &datWorld,
    const EditorMm9RawObjectsSidecar &rawObjects,
    const Game::Mm9EventsData &events)
{
    std::vector<std::string> issues;
    std::unordered_map<std::string, int> sourceObjectIndexByObjectId;
    const std::unordered_map<std::string, std::vector<std::filesystem::path>> scriptIndex =
        buildMm9EventScriptSourceIndex(levelPhysicalPath);

    if (events.generatedLua.empty())
    {
        issues.push_back("MM9 events generated Lua path is empty.");
    }
    else if (!metadata.scripts.level.empty() && events.generatedLua != metadata.scripts.level)
    {
        issues.push_back(
            "MM9 events generated Lua path does not match level script path: events="
            + events.generatedLua + " level=" + metadata.scripts.level);
    }

    if (!events.generatedScriptIr.empty()
        && !metadata.scripts.scriptIr.empty()
        && events.generatedScriptIr != metadata.scripts.scriptIr)
    {
        issues.push_back(
            "MM9 events generated script IR path does not match level script IR path: events="
            + events.generatedScriptIr + " level=" + metadata.scripts.scriptIr);
    }

    if (!metadata.scripts.level.empty())
    {
        const std::filesystem::path levelLuaPath =
            resolveMm9DatLevelRelativePath(levelPhysicalPath, metadata.scripts.level);

        if (!pathExists(levelLuaPath))
        {
            issues.push_back("MM9 events generated Lua is missing: " + levelLuaPath.generic_string());
        }
    }

    if (!metadata.scripts.scriptIr.empty())
    {
        const std::filesystem::path scriptIrPath =
            resolveMm9DatLevelRelativePath(levelPhysicalPath, metadata.scripts.scriptIr);

        if (!pathExists(scriptIrPath))
        {
            issues.push_back("MM9 events generated script IR is missing: " + scriptIrPath.generic_string());
        }
    }

    if (!events.sourceRawObjects.empty() && events.sourceRawObjects != metadata.sidecars.rawObjects)
    {
        issues.push_back(
            "MM9 events source_raw_objects does not match level sidecar path: events="
            + events.sourceRawObjects + " level=" + metadata.sidecars.rawObjects);
    }

    for (size_t objectRow = 0; objectRow < events.objects.size(); ++objectRow)
    {
        const Game::Mm9EventObject &eventObject = events.objects[objectRow];
        sourceObjectIndexByObjectId[eventObject.objectId] = eventObject.sourceObjectIndex;

        if (eventObject.sourceObjectIndex < 0
            || static_cast<size_t>(eventObject.sourceObjectIndex) >= rawObjects.objects.size())
        {
            issues.push_back(
                "MM9 event object " + eventObject.objectId
                + " references invalid source_object_index "
                + std::to_string(eventObject.sourceObjectIndex));
            continue;
        }

        const EditorMm9RawObject &rawObject =
            rawObjects.objects[static_cast<size_t>(eventObject.sourceObjectIndex)];

        if (eventObject.rawPropertyCount != rawObject.properties.size())
        {
            issues.push_back(
                "MM9 event object " + eventObject.objectId
                + " raw_property_count mismatch: stored=" + std::to_string(eventObject.rawPropertyCount)
                + " raw_object=" + std::to_string(rawObject.properties.size()));
        }

        if (!eventObject.rawObjectRef.empty())
        {
            const std::string expectedRef =
                metadata.sidecars.rawObjects + "#objects[" + std::to_string(eventObject.sourceObjectIndex) + "]";

            if (eventObject.rawObjectRef != expectedRef)
            {
                issues.push_back(
                    "MM9 event object " + eventObject.objectId
                    + " raw_object_ref mismatch: stored=" + eventObject.rawObjectRef
                    + " expected=" + expectedRef);
            }
        }

        for (const Game::Mm9EventObject::RawPropertyRef &propertyRef : eventObject.rawProperties)
        {
            if (propertyRef.propertyIndex >= rawObject.properties.size())
            {
                issues.push_back(
                    "MM9 event object " + eventObject.objectId
                    + " raw property ref is out of range: "
                    + std::to_string(propertyRef.propertyIndex));
                continue;
            }

            const EditorMm9RawObjectProperty &rawProperty = rawObject.properties[propertyRef.propertyIndex];

            if (propertyRef.name != rawProperty.name
                || propertyRef.code != rawProperty.code
                || propertyRef.flags != rawProperty.flags
                || propertyRef.decoded != rawProperty.decoded)
            {
                issues.push_back(
                    "MM9 event object " + eventObject.objectId
                    + " raw property ref does not match raw object property "
                    + std::to_string(propertyRef.propertyIndex));
            }
        }

        if (eventObject.objectId.empty())
        {
            issues.push_back("MM9 event object at row " + std::to_string(objectRow) + " has an empty object_id.");
        }
    }

    for (const Game::Mm9EventMechanism &mechanism : events.mechanisms)
    {
        if (sourceObjectIndexByObjectId.find(mechanism.objectId) == sourceObjectIndexByObjectId.end())
        {
            issues.push_back(
                "MM9 mechanism " + mechanism.mechanismId
                + " references missing event object " + mechanism.objectId);
        }

        if (mechanism.sourceObjectIndex < 0
            || static_cast<size_t>(mechanism.sourceObjectIndex) >= rawObjects.objects.size())
        {
            issues.push_back(
                "MM9 mechanism " + mechanism.mechanismId
                + " references invalid source_object_index "
                + std::to_string(mechanism.sourceObjectIndex));
        }
    }

    for (const Game::Mm9EventBinding &binding : events.bindings)
    {
        if (sourceObjectIndexByObjectId.find(binding.objectId) == sourceObjectIndexByObjectId.end())
        {
            issues.push_back("MM9 binding references missing event object " + binding.objectId);
        }

        if (binding.sourceObjectIndex < 0
            || static_cast<size_t>(binding.sourceObjectIndex) >= rawObjects.objects.size())
        {
            issues.push_back(
                "MM9 binding " + binding.objectId
                + " references invalid source_object_index "
                + std::to_string(binding.sourceObjectIndex));
        }

        for (const Game::Mm9EventBindingTarget &target : binding.targets)
        {
            if (target.targetKind == "odm_bmodel" && target.bmodelIndex)
            {
                if (*target.bmodelIndex >= datWorld.worldModels.size())
                {
                    issues.push_back(
                        "MM9 binding " + binding.objectId
                        + " references invalid DAT world model target "
                        + std::to_string(*target.bmodelIndex));
                }
            }
        }
    }

    for (const Game::Mm9EventScript &script : events.scripts)
    {
        if (script.scriptId.empty())
        {
            issues.push_back("MM9 event script has an empty script_id.");
        }

        const std::filesystem::path scriptPath =
            resolveMm9EventScriptSourcePath(levelPhysicalPath, script.sourcePath);

        if (!pathExists(scriptPath))
        {
            issues.push_back("MM9 event source script is missing: " + scriptPath.generic_string());
        }

        for (const Game::Mm9EventScript::Include &include : script.includes)
        {
            const std::vector<std::filesystem::path> *pCandidates =
                findMm9EventScriptSourceCandidates(scriptIndex, include.path);

            if (pCandidates == nullptr || pCandidates->empty())
            {
                issues.push_back(
                    "MM9 event script include is missing: script="
                    + script.scriptId
                    + " line=" + std::to_string(include.line)
                    + " include=" + include.path);
            }
            else if (pCandidates->size() > 1)
            {
                issues.push_back(
                    "MM9 event script include is ambiguous: script="
                    + script.scriptId
                    + " line=" + std::to_string(include.line)
                    + " include=" + include.path);
            }
        }
    }

    return issues;
}

std::vector<EditorMm9SourceAssetFamilyStatus> inspectMm9SourceAssetManifestFiles(
    const std::filesystem::path &manifestPhysicalPath,
    const EditorMm9SourceAssetManifest &manifest)
{
    std::vector<EditorMm9SourceAssetFamilyStatus> statuses;
    statuses.reserve(manifest.families.size() + requiredSourceAssetFamilies().size());

    const std::filesystem::path packageRoot = manifestPhysicalPath.parent_path();

    for (const EditorMm9SourceAssetFamily &family : manifest.families)
    {
        const std::filesystem::path packagePath = packageRoot / family.package;
        EditorMm9SourceAssetFamilyStatus status = {};
        status.id = family.id;
        status.source = family.source;
        status.package = family.package;
        status.expectedFileCount = family.fileCount;
        status.actualFileCount = countRegularFilesRecursively(packagePath);
        status.required = isRequiredSourceAssetFamily(family.id);
        status.declared = true;
        status.packageDirectoryExists = directoryExists(packagePath);
        statuses.push_back(std::move(status));
    }

    for (const char *familyId : requiredSourceAssetFamilies())
    {
        const auto found = std::find_if(
            manifest.families.begin(),
            manifest.families.end(),
            [familyId](const EditorMm9SourceAssetFamily &family)
            {
                return family.id == familyId;
            });

        if (found == manifest.families.end())
        {
            EditorMm9SourceAssetFamilyStatus status = {};
            status.id = familyId;
            status.required = true;
            statuses.push_back(std::move(status));
        }
    }

    return statuses;
}

std::vector<std::string> validateMm9SourceAssetManifestFiles(
    const std::filesystem::path &manifestPhysicalPath,
    const EditorMm9SourceAssetManifest &manifest)
{
    std::vector<std::string> issues;

    if (manifest.kind != "mm9_source_asset_manifest")
    {
        issues.push_back("MM9 source asset manifest kind is not mm9_source_asset_manifest.");
    }

    if (manifest.formatVersion <= 0)
    {
        issues.push_back("MM9 source asset manifest format_version must be positive.");
    }

    if (!manifest.policy.sourceTruth)
    {
        issues.push_back("MM9 source asset manifest policy.source_truth must be true.");
    }

    if (manifest.policy.generatedCache)
    {
        issues.push_back("MM9 source asset manifest policy.generated_cache must be false.");
    }

    const std::vector<EditorMm9SourceAssetFamilyStatus> statuses =
        inspectMm9SourceAssetManifestFiles(manifestPhysicalPath, manifest);

    for (const EditorMm9SourceAssetFamilyStatus &status : statuses)
    {
        if (status.required && !status.declared)
        {
            issues.push_back("MM9 source asset manifest is missing required family: " + status.id);
            continue;
        }

        if (status.declared && !status.packageDirectoryExists)
        {
            issues.push_back(
                "MM9 source asset manifest package directory is missing for family " + status.id
                + ": " + (manifestPhysicalPath.parent_path() / status.package).generic_string());
            continue;
        }

        if (status.declared && status.actualFileCount != status.expectedFileCount)
        {
            issues.push_back(
                "MM9 source asset manifest file count mismatch for family " + status.id
                + ": expected=" + std::to_string(status.expectedFileCount)
                + " actual=" + std::to_string(status.actualFileCount));
        }
    }

    return issues;
}

bool loadMm9DatLevelSidecars(
    const std::filesystem::path &levelPhysicalPath,
    const EditorMm9DatLevelMetadata &metadata,
    EditorMm9LoadedSidecars &sidecars,
    std::string &errorMessage)
{
    errorMessage.clear();

    const auto readSidecarText =
        [&levelPhysicalPath, &errorMessage](const std::string &label, const std::string &relativePath)
            -> std::optional<std::string>
    {
        const std::filesystem::path path = resolveMm9DatLevelRelativePath(levelPhysicalPath, relativePath);
        std::string text;

        if (!readTextFile(path, text))
        {
            errorMessage = "could not read MM9 " + label + ": " + path.generic_string();
            return std::nullopt;
        }

        return text;
    };

    const std::optional<std::string> datWorldText = readSidecarText("DAT world sidecar", metadata.sidecars.datWorld);
    if (!datWorldText)
    {
        return false;
    }

    const std::optional<EditorMm9DatWorldSidecar> datWorld =
        loadMm9DatWorldSidecarFromText(*datWorldText, errorMessage);
    if (!datWorld)
    {
        errorMessage = "could not parse MM9 DAT world sidecar: " + errorMessage;
        return false;
    }

    const std::optional<std::string> materialText =
        readSidecarText("material aliases sidecar", metadata.sidecars.materials);
    if (!materialText)
    {
        return false;
    }

    const std::optional<EditorMm9MaterialAliasesSidecar> materialAliases =
        loadMm9MaterialAliasesSidecarFromText(*materialText, errorMessage);
    if (!materialAliases)
    {
        errorMessage = "could not parse MM9 material aliases sidecar: " + errorMessage;
        return false;
    }

    const std::optional<std::string> rawObjectsText =
        readSidecarText("raw objects sidecar", metadata.sidecars.rawObjects);
    if (!rawObjectsText)
    {
        return false;
    }

    const std::optional<EditorMm9RawObjectsSidecar> rawObjects =
        loadMm9RawObjectsSidecarFromText(*rawObjectsText, errorMessage);
    if (!rawObjects)
    {
        errorMessage = "could not parse MM9 raw objects sidecar: " + errorMessage;
        return false;
    }

    const std::optional<std::string> eventsText = readSidecarText("events sidecar", metadata.sidecars.events);
    if (!eventsText)
    {
        return false;
    }

    Game::Mm9EventsYmlLoader eventsLoader = {};
    const std::optional<Game::Mm9EventsData> events = eventsLoader.loadFromText(*eventsText, errorMessage);
    if (!events)
    {
        errorMessage = "could not parse MM9 events sidecar: " + errorMessage;
        return false;
    }

    sidecars.datWorld = *datWorld;
    sidecars.materialAliases = *materialAliases;
    sidecars.rawObjects = *rawObjects;
    sidecars.events = *events;
    return true;
}
}
