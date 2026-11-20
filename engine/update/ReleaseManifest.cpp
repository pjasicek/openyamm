#include "engine/update/ReleaseManifest.h"

#include <monocypher-ed25519.h>
#include <yaml-cpp/yaml.h>

#include <charconv>
#include <unordered_set>

namespace OpenYAMM::Engine
{
namespace
{
std::string requiredString(const YAML::Node &node, const char *pKey)
{
    const YAML::Node value = node[pKey];

    if (!value || !value.IsScalar())
    {
        throw std::runtime_error(std::string("missing ") + pKey);
    }

    return value.as<std::string>();
}

bool isLowerHex(const std::string &text, size_t length)
{
    if (text.size() != length)
    {
        return false;
    }

    for (const char character : text)
    {
        if (!((character >= '0' && character <= '9') || (character >= 'a' && character <= 'f')))
        {
            return false;
        }
    }

    return true;
}

// Store files are addressed by their own hash: "<folder>/<sha256><suffix>" below the channel, or an absolute https URL
// whose last path segment is "<sha256><suffix>" (a mirror).
bool isStoreUrl(const std::string &url, const std::string &folder, const std::string &sha256)
{
    for (const char *pSuffix : {".zip", ".apk"})
    {
        const std::string name = sha256 + pSuffix;

        if (url == folder + "/" + name || (url.starts_with("https://") && url.ends_with("/" + name)))
        {
            return true;
        }
    }

    return false;
}

ReleaseFile parseFile(const YAML::Node &node, const std::string &folder)
{
    ReleaseFile file;
    file.file = requiredString(node, "file");
    file.url = requiredString(node, "url");
    file.size = node["size"].as<uint64_t>();
    file.sha256 = requiredString(node, "sha256");

    if (!isLowerHex(file.sha256, 64) || !isStoreUrl(file.url, folder, file.sha256))
    {
        throw std::runtime_error("invalid store address for " + file.file);
    }

    return file;
}

std::optional<std::vector<uint8_t>> decodeBase64(const std::string &text)
{
    std::vector<uint8_t> bytes;
    uint32_t accumulator = 0;
    int bits = 0;
    size_t padding = 0;

    for (const char character : text)
    {
        int value = -1;

        if (character >= 'A' && character <= 'Z')
        {
            value = character - 'A';
        }
        else if (character >= 'a' && character <= 'z')
        {
            value = character - 'a' + 26;
        }
        else if (character >= '0' && character <= '9')
        {
            value = character - '0' + 52;
        }
        else if (character == '+')
        {
            value = 62;
        }
        else if (character == '/')
        {
            value = 63;
        }
        else if (character == '=')
        {
            ++padding;
            continue;
        }
        else
        {
            return std::nullopt;
        }

        if (padding > 0)
        {
            return std::nullopt;
        }

        accumulator = (accumulator << 6) | uint32_t(value);
        bits += 6;

        if (bits >= 8)
        {
            bits -= 8;
            bytes.push_back(uint8_t(accumulator >> bits));
        }
    }

    if (padding > 2)
    {
        return std::nullopt;
    }

    return bytes;
}

std::array<uint8_t, 32> hexKey(const char *pHex)
{
    std::array<uint8_t, 32> key = {};

    for (size_t index = 0; index < key.size(); ++index)
    {
        std::from_chars(pHex + index * 2, pHex + index * 2 + 2, key[index], 16);
    }

    return key;
}

std::optional<std::pair<int, int>> parseReleaseVersion(const std::string &version)
{
    const size_t dot = version.find('.');

    if (dot == std::string::npos || dot == 0 || dot + 1 == version.size())
    {
        return std::nullopt;
    }

    std::pair<int, int> parsed;
    const char *pBegin = version.data();
    const char *pEnd = pBegin + version.size();
    const std::from_chars_result major = std::from_chars(pBegin, pBegin + dot, parsed.first);
    const std::from_chars_result minor = std::from_chars(pBegin + dot + 1, pEnd, parsed.second);

    if (major.ec != std::errc() || major.ptr != pBegin + dot || minor.ec != std::errc() || minor.ptr != pEnd
        || (version[0] == '0' && dot > 1) || (version[dot + 1] == '0' && dot + 2 < version.size()))
    {
        return std::nullopt;
    }

    return parsed;
}
}

std::optional<ReleaseManifest> parseReleaseManifest(const std::string &text, std::string &error)
{
    try
    {
        const YAML::Node document = YAML::Load(text);

        if (!document.IsMap() || !document["schema"] || document["schema"].as<uint32_t>() != ReleaseManifestSchema)
        {
            error = "unsupported manifest schema";
            return std::nullopt;
        }

        ReleaseManifest manifest;
        manifest.channel = requiredString(document, "channel");
        manifest.platform = requiredString(document, "platform");
        manifest.release = requiredString(document, "release");
        manifest.build = requiredString(document, "build");
        manifest.published = requiredString(document, "published");
        manifest.contentFormat = document["content_format"].as<uint32_t>();
        manifest.minUpdaterSchema = document["min_updater_schema"].as<uint32_t>();

        // Optional texts; JSON null is not a scalar.
        const auto optionalString = [&document](const char *pKey)
        {
            const YAML::Node value = document[pKey];
            return value && value.IsScalar() ? value.as<std::string>() : std::string();
        };
        manifest.notesUrl = optionalString("notes_url");
        manifest.notes = optionalString("notes");

        const YAML::Node app = document["app"];

        if (!app || !app.IsMap())
        {
            error = "manifest has no app";
            return std::nullopt;
        }

        manifest.app = parseFile(app, "apps");

        if (app["android_version_code"] && app["android_version_code"].IsScalar()
            && app["android_version_code"].as<std::string>() != "null")
        {
            manifest.androidVersionCode = app["android_version_code"].as<int64_t>();
        }

        const YAML::Node packs = document["packs"];

        if (!packs || !packs.IsSequence() || packs.size() == 0)
        {
            error = "manifest lists no packs";
            return std::nullopt;
        }

        // A desktop manifest lists the languages' optional packs apart (language_packs), which updaters before 2.0
        // do not read: they know no language field and would download every language's (packaging/publish_release.py).
        const YAML::Node languagePacks = document["language_packs"];

        if (languagePacks && !languagePacks.IsSequence())
        {
            error = "manifest language_packs is not a list";
            return std::nullopt;
        }

        std::vector<YAML::Node> packNodes;

        for (const YAML::Node &packNode : packs)
        {
            packNodes.push_back(packNode);
        }

        const size_t firstLanguagePack = packNodes.size();

        if (languagePacks)
        {
            for (const YAML::Node &packNode : languagePacks)
            {
                packNodes.push_back(packNode);
            }
        }

        std::unordered_set<std::string> ids;
        std::unordered_set<std::string> files;

        for (size_t index = 0; index < packNodes.size(); ++index)
        {
            const YAML::Node &packNode = packNodes[index];
            const ReleaseFile file = parseFile(packNode, "packs");
            AssetPackRecord pack;
            pack.id = requiredString(packNode, "id");
            pack.package = requiredString(packNode, "package");
            pack.mount = requiredString(packNode, "mount");
            pack.file = file.file;
            pack.size = file.size;
            pack.contentId = requiredString(packNode, "content_id");
            pack.sha256 = file.sha256;
            pack.language = packNode["language"] ? packNode["language"].as<std::string>() : std::string();

            if (index >= firstLanguagePack && pack.language.empty())
            {
                error = "manifest language pack " + pack.id + " names no language";
                return std::nullopt;
            }

            if (!validateAssetPackRecord(pack, error))
            {
                return std::nullopt;
            }

            if (!ids.insert(pack.id).second || !files.insert(pack.file).second)
            {
                error = "manifest lists " + pack.id + " twice";
                return std::nullopt;
            }

            manifest.packs.push_back(std::move(pack));
            manifest.packUrls.push_back(file.url);
        }

        error.clear();
        return manifest;
    }
    catch (const std::exception &exception)
    {
        error = std::string("invalid manifest: ") + exception.what();
        return std::nullopt;
    }
}

const std::vector<ManifestPublicKey> &releaseManifestPublicKeys()
{
    // Must match packaging/keys/manifest-ed25519-<slot>.pub (checked by the unit tests).
    static const std::vector<ManifestPublicKey> keys = {
        {1, hexKey("7e2aa970dd08244309145ea9d505d700b89fee3bf3d183403dab5d252f12f6f6")},
        {2, hexKey("4bbe2fc5c51949ae537bba047e01d207061c447710304ef96b842c961a1d9d1b")},
    };
    return keys;
}

std::optional<int> verifyManifestSignature(const std::string &manifestBytes, const std::string &signatureJson,
                                           const std::vector<ManifestPublicKey> &keys, std::string &error)
{
    try
    {
        const YAML::Node document = YAML::Load(signatureJson);

        if (!document.IsMap() || requiredString(document, "algorithm") != "ed25519")
        {
            error = "unsupported manifest signature";
            return std::nullopt;
        }

        const int slot = document["key"].as<int>();
        const std::optional<std::vector<uint8_t>> signature = decodeBase64(requiredString(document, "signature"));

        if (!signature || signature->size() != 64)
        {
            error = "malformed manifest signature";
            return std::nullopt;
        }

        for (const ManifestPublicKey &key : keys)
        {
            if (key.slot != slot)
            {
                continue;
            }

            if (crypto_ed25519_check(signature->data(), key.key.data(),
                                     reinterpret_cast<const uint8_t *>(manifestBytes.data()), manifestBytes.size())
                == 0)
            {
                error.clear();
                return slot;
            }

            error = "the manifest signature is invalid";
            return std::nullopt;
        }

        error = "the manifest is signed with an unknown key";
        return std::nullopt;
    }
    catch (const std::exception &exception)
    {
        error = std::string("invalid manifest signature: ") + exception.what();
        return std::nullopt;
    }
}

std::optional<int> compareReleaseVersions(const std::string &left, const std::string &right)
{
    const std::optional<std::pair<int, int>> leftVersion = parseReleaseVersion(left);
    const std::optional<std::pair<int, int>> rightVersion = parseReleaseVersion(right);

    if (!leftVersion || !rightVersion)
    {
        return std::nullopt;
    }

    return *leftVersion < *rightVersion ? -1 : (*leftVersion == *rightVersion ? 0 : 1);
}
}
