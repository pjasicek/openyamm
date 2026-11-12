#include "engine/AssetPackIndex.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <fstream>
#include <iterator>
#include <system_error>
#include <unordered_set>

namespace OpenYAMM::Engine
{
namespace
{
constexpr int SupportedIndexSchema = 1;

bool isSimpleName(const std::string &name)
{
    if (name.empty() || name == "." || name == "..")
    {
        return false;
    }

    for (const char character : name)
    {
        const bool allowed = (character >= 'a' && character <= 'z') || (character >= 'A' && character <= 'Z')
            || (character >= '0' && character <= '9') || character == '_' || character == '-' || character == '.';

        if (!allowed)
        {
            return false;
        }
    }

    return true;
}

// The mount of a pack lies inside its package: "/engine" or "/worlds/<package>", optionally followed by folders.
// Releases up to 1.10 accept nothing else, so new content goes below one of these (the rulesets: /engine/rulesets).
bool isPackageMount(const std::string &mount, const std::string &package)
{
    const std::string root = package == "engine" ? "/engine" : "/worlds/" + package;

    if (mount == root)
    {
        return true;
    }

    if (!mount.starts_with(root + "/"))
    {
        return false;
    }

    size_t begin = root.size() + 1;

    while (begin <= mount.size())
    {
        const size_t end = mount.find('/', begin);
        const std::string part = mount.substr(begin, end == std::string::npos ? std::string::npos : end - begin);

        if (!isSimpleName(part))
        {
            return false;
        }

        if (end == std::string::npos)
        {
            break;
        }

        begin = end + 1;
    }

    return true;
}

std::string requiredString(const YAML::Node &node, const char *pKey)
{
    const YAML::Node value = node[pKey];

    if (!value || !value.IsScalar())
    {
        throw std::runtime_error(std::string("missing ") + pKey);
    }

    return value.as<std::string>();
}
}

bool validateAssetPackRecord(const AssetPackRecord &pack, std::string &error)
{
    if (!isSimpleName(pack.package) || !isPackageMount(pack.mount, pack.package))
    {
        error = "pack " + pack.id + " mounts outside its package: " + pack.mount;
        return false;
    }

    if (!isSimpleName(pack.file) || !pack.file.ends_with(".zip"))
    {
        error = "pack " + pack.id + " has an invalid file name: " + pack.file;
        return false;
    }

    if (!pack.language.empty() && (!isSimpleName(pack.language) || pack.language.find('.') != std::string::npos))
    {
        error = "pack " + pack.id + " has an invalid language: " + pack.language;
        return false;
    }

    return true;
}

std::optional<AssetPackIndex> parseAssetPackIndex(const std::string &text, std::string &error)
{
    try
    {
        const YAML::Node document = YAML::Load(text);

        if (!document.IsMap() || !document["schema"] || document["schema"].as<int>() != SupportedIndexSchema)
        {
            error = "unsupported pack index schema";
            return std::nullopt;
        }

        AssetPackIndex index;
        index.release = requiredString(document, "release");
        index.build = requiredString(document, "build");
        index.profile = requiredString(document, "profile");
        index.contentFormat = document["content_format"].as<uint32_t>();

        if (index.contentFormat != SupportedContentFormat)
        {
            error = "the content has format " + std::to_string(index.contentFormat) + ", this version reads format "
                + std::to_string(SupportedContentFormat);
            return std::nullopt;
        }

        index.store = requiredString(document, "store");
        const YAML::Node packs = document["packs"];

        if (!packs || !packs.IsSequence() || packs.size() == 0)
        {
            error = "pack index lists no packs";
            return std::nullopt;
        }

        // A release's index lists the languages' optional packs apart (language_packs): the updaters before 2.0
        // check every pack of a new version's index before switching to it, and never download a language's
        // (packaging/publish_release.py).
        const YAML::Node languagePacks = document["language_packs"];

        if (languagePacks && !languagePacks.IsSequence())
        {
            error = "pack index language_packs is not a list";
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

        for (size_t nodeIndex = 0; nodeIndex < packNodes.size(); ++nodeIndex)
        {
            const YAML::Node &packNode = packNodes[nodeIndex];
            AssetPackRecord pack;
            pack.id = requiredString(packNode, "id");
            pack.package = requiredString(packNode, "package");
            pack.mount = requiredString(packNode, "mount");
            pack.file = requiredString(packNode, "file");
            pack.size = packNode["size"].as<uint64_t>();
            pack.contentId = requiredString(packNode, "content_id");
            pack.sha256 = requiredString(packNode, "sha256");
            pack.language = packNode["language"] ? packNode["language"].as<std::string>() : std::string();

            if (!validateAssetPackRecord(pack, error))
            {
                return std::nullopt;
            }

            if (nodeIndex >= firstLanguagePack && pack.language.empty())
            {
                error = "pack index language pack " + pack.id + " names no language";
                return std::nullopt;
            }

            if (!ids.insert(pack.id).second || !files.insert(pack.file).second)
            {
                error = "pack index lists " + pack.id + " twice";
                return std::nullopt;
            }

            index.packs.push_back(std::move(pack));
        }

        error.clear();
        return index;
    }
    catch (const std::exception &exception)
    {
        error = std::string("invalid pack index: ") + exception.what();
        return std::nullopt;
    }
}

std::optional<AssetPackIndex> loadAssetPackIndex(const std::filesystem::path &path, std::string &error)
{
    std::ifstream input(path, std::ios::binary);

    if (!input)
    {
        error = "cannot open " + path.string();
        return std::nullopt;
    }

    const std::string text((std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());
    return parseAssetPackIndex(text, error);
}

bool validateAssetPackFiles(const AssetPackIndex &index, const std::filesystem::path &storeRoot, std::string &error)
{
    for (const AssetPackRecord &pack : index.packs)
    {
        std::error_code sizeError;
        const uintmax_t size = std::filesystem::file_size(storeRoot / pack.file, sizeError);

        if (sizeError && !pack.language.empty())
        {
            continue;
        }

        if (sizeError || size != pack.size)
        {
            error = sizeError ? "missing content pack " + pack.file
                              : "content pack " + pack.file + " has the wrong size; verify the game files";
            return false;
        }
    }

    error.clear();
    return true;
}

bool assetPackFilesExist(const AssetPackIndex &index, const std::filesystem::path &storeRoot, std::string &error)
{
    for (const AssetPackRecord &pack : index.packs)
    {
        std::error_code fileError;
        if (!std::filesystem::is_regular_file(storeRoot / pack.file, fileError) && pack.language.empty())
        {
            error = "missing content pack " + pack.file;
            return false;
        }
    }

    error.clear();
    return true;
}

std::vector<std::string> assetPackLanguages(const AssetPackIndex &index)
{
    std::vector<std::string> languages;

    for (const AssetPackRecord &pack : index.packs)
    {
        if (!pack.language.empty() && std::find(languages.begin(), languages.end(), pack.language) == languages.end())
        {
            languages.push_back(pack.language);
        }
    }

    std::sort(languages.begin(), languages.end());
    return languages;
}

uint64_t missingLanguagePackBytes(const AssetPackIndex &index, const std::filesystem::path &storeRoot,
                                  const std::string &language)
{
    uint64_t bytes = 0;

    for (const AssetPackRecord &pack : index.packs)
    {
        std::error_code sizeError;

        if (!language.empty() && pack.language == language
            && std::filesystem::file_size(storeRoot / pack.file, sizeError) != pack.size)
        {
            bytes += pack.size;
        }
    }

    return bytes;
}
}
