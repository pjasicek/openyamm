#include "game/mm9/Mm9AnimatedModelResolver.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cctype>
#include <exception>
#include <sstream>

namespace OpenYAMM::Game
{
namespace
{
std::string toLowerCopy(const std::string &value)
{
    std::string output = value;
    std::transform(
        output.begin(),
        output.end(),
        output.begin(),
        [](unsigned char character)
        {
            return static_cast<char>(std::tolower(character));
        });
    return output;
}

std::string trimCopy(const std::string &value)
{
    size_t begin = 0;
    while (begin < value.size() && std::isspace(static_cast<unsigned char>(value[begin])) != 0)
    {
        ++begin;
    }

    size_t end = value.size();
    while (end > begin && std::isspace(static_cast<unsigned char>(value[end - 1])) != 0)
    {
        --end;
    }

    return value.substr(begin, end - begin);
}

bool pathLeafHasExtension(const std::string &value)
{
    const size_t slashIndex = value.find_last_of('/');
    const size_t dotIndex = value.find_last_of('.');
    return dotIndex != std::string::npos && (slashIndex == std::string::npos || dotIndex > slashIndex);
}

std::string normalizePathRef(const std::string &value)
{
    std::string output = trimCopy(value);
    std::replace(output.begin(), output.end(), '\\', '/');
    return toLowerCopy(output);
}

std::string normalizeSkinRef(const std::string &value)
{
    std::string output = normalizePathRef(value);
    if (output.empty())
    {
        return output;
    }

    if (output.find('/') == std::string::npos)
    {
        output = "skins/" + output;
    }

    if (!pathLeafHasExtension(output))
    {
        output += ".dtx";
    }

    return output;
}

std::vector<std::string> readStringSequence(const YAML::Node &node)
{
    std::vector<std::string> output;
    if (!node || !node.IsSequence())
    {
        return output;
    }

    for (const YAML::Node &entry : node)
    {
        if (entry && entry.IsScalar())
        {
            output.push_back(entry.as<std::string>());
        }
    }

    return output;
}

std::vector<std::string> normalizeSkinSequence(const YAML::Node &node)
{
    std::vector<std::string> output;
    for (const std::string &skin : readStringSequence(node))
    {
        const std::string normalized = normalizeSkinRef(skin);
        if (!normalized.empty())
        {
            output.push_back(normalized);
        }
    }
    return output;
}

void readAliasMap(
    const YAML::Node &node,
    std::unordered_map<std::string, std::string> &aliases,
    std::string (*normalize)(const std::string &))
{
    if (!node || !node.IsMap())
    {
        return;
    }

    for (YAML::const_iterator iterator = node.begin(); iterator != node.end(); ++iterator)
    {
        if (!iterator->first.IsScalar() || !iterator->second.IsScalar())
        {
            continue;
        }

        const std::string source = normalize(iterator->first.as<std::string>());
        const std::string target = normalize(iterator->second.as<std::string>());
        if (!source.empty() && !target.empty())
        {
            aliases[source] = target;
        }
    }
}

std::string aliasedRef(
    const std::unordered_map<std::string, std::string> &aliases,
    const std::string &value)
{
    const auto iterator = aliases.find(value);
    return iterator != aliases.end() ? iterator->second : value;
}

std::vector<std::string> aliasedRefs(
    const std::unordered_map<std::string, std::string> &aliases,
    const std::vector<std::string> &values)
{
    std::vector<std::string> result;
    result.reserve(values.size());
    for (const std::string &value : values)
    {
        result.push_back(aliasedRef(aliases, value));
    }
    return result;
}

std::string skinListKey(const std::vector<std::string> &skins)
{
    std::ostringstream stream;
    for (size_t index = 0; index < skins.size(); ++index)
    {
        if (index != 0)
        {
            stream << ';';
        }
        stream << skins[index];
    }
    return stream.str();
}

const Mm9AnimatedModelSkinBinding *findSkinBinding(
    const Mm9AnimatedModelRegistryEntry &entry,
    const std::vector<std::string> &normalizedSkins)
{
    for (const Mm9AnimatedModelSkinBinding &binding : entry.skinBindings)
    {
        if (binding.sourceSkins == normalizedSkins)
        {
            return &binding;
        }
    }
    return nullptr;
}

const Mm9AnimatedModelSkinBinding *findSkinBindingById(
    const Mm9AnimatedModelRegistryEntry &entry,
    const std::string &skinBindingId)
{
    for (const Mm9AnimatedModelSkinBinding &binding : entry.skinBindings)
    {
        if (binding.id == skinBindingId)
        {
            return &binding;
        }
    }
    return nullptr;
}

std::vector<Mm9AnimatedModelMaterialOverride> materialOverridesForSkins(const std::vector<std::string> &skins)
{
    std::vector<Mm9AnimatedModelMaterialOverride> output;
    output.reserve(skins.size());
    for (size_t index = 0; index < skins.size(); ++index)
    {
        output.push_back(Mm9AnimatedModelMaterialOverride{
            .materialIndex = index,
            .runtimeTexture = skins[index],
        });
    }
    return output;
}

Mm9AnimatedModelResolution makeResolution(
    const Mm9AnimatedModelRegistryEntry &entry,
    const std::filesystem::path &worldRoot,
    const std::string &requestedSourceModel,
    const std::string &requestedSourceSkin,
    const std::string &normalizedSourceModel,
    const std::vector<std::string> &normalizedSourceSkins,
    const Mm9AnimatedModelSkinBinding *pSkinBinding)
{
    Mm9AnimatedModelResolution resolution = {};
    resolution.requestedSourceModel = requestedSourceModel;
    resolution.requestedSourceSkin = requestedSourceSkin;
    resolution.normalizedSourceModel = normalizedSourceModel;
    resolution.normalizedSourceSkins = normalizedSourceSkins;
    resolution.modelId = entry.modelId;
    resolution.skinBindingId = pSkinBinding != nullptr ? pSkinBinding->id : "";
    resolution.modelAssetPath = worldRoot / entry.modelAsset;
    resolution.modelSidecarPath = worldRoot / entry.modelSidecar;
    resolution.materialOverrides = materialOverridesForSkins(normalizedSourceSkins);
    return resolution;
}

void addDiagnostic(
    std::vector<AnimatedModelDiagnostic> &diagnostics,
    const std::string &message,
    bool error)
{
    diagnostics.push_back(AnimatedModelDiagnostic{
        .message = message,
        .error = error,
    });
}
}

std::string normalizeMm9AnimatedModelSourceModelRef(const std::string &value)
{
    std::string output = normalizePathRef(value);
    if (output.empty())
    {
        return output;
    }

    if (output.find('/') == std::string::npos)
    {
        output = "models/" + output;
    }

    if (!pathLeafHasExtension(output))
    {
        output += ".abc";
    }

    return output;
}

std::vector<std::string> normalizeMm9AnimatedModelSourceSkinRefs(const std::string &value)
{
    std::vector<std::string> output;
    std::string current;

    for (const char character : value)
    {
        if (character == ';')
        {
            const std::string normalized = normalizeSkinRef(current);
            if (!normalized.empty())
            {
                output.push_back(normalized);
            }
            current.clear();
        }
        else
        {
            current.push_back(character);
        }
    }

    const std::string normalized = normalizeSkinRef(current);
    if (!normalized.empty())
    {
        output.push_back(normalized);
    }

    return output;
}

bool Mm9AnimatedModelResolver::loadRegistry(
    const std::filesystem::path &registryPath,
    std::string &errorMessage)
{
    m_entries.clear();
    m_sourceModelAliases.clear();
    m_sourceSkinAliases.clear();
    m_worldRoot.clear();

    try
    {
        const YAML::Node root = YAML::LoadFile(registryPath.string());
        const std::string schema = root["schema"] && root["schema"].IsScalar()
            ? root["schema"].as<std::string>()
            : "";
        if (schema != "openyamm.mm9.model_registry.v2")
        {
            errorMessage = "MM9 model registry has unsupported schema: " + schema;
            return false;
        }

        const YAML::Node models = root["models"];
        if (!models || !models.IsSequence())
        {
            errorMessage = "MM9 model registry is missing models sequence";
            return false;
        }

        m_worldRoot = registryPath.parent_path().parent_path();
        const YAML::Node aliases = root["aliases"];
        if (aliases && aliases.IsMap())
        {
            readAliasMap(aliases["source_models"], m_sourceModelAliases, normalizeMm9AnimatedModelSourceModelRef);
            readAliasMap(aliases["source_skins"], m_sourceSkinAliases, normalizeSkinRef);
        }

        for (const YAML::Node &modelNode : models)
        {
            if (!modelNode || !modelNode.IsMap())
            {
                continue;
            }

            Mm9AnimatedModelRegistryEntry entry = {};
            entry.modelId = modelNode["model_id"] && modelNode["model_id"].IsScalar()
                ? modelNode["model_id"].as<std::string>()
                : "";
            entry.roles = readStringSequence(modelNode["roles"]);
            entry.sourceModel = normalizeMm9AnimatedModelSourceModelRef(
                modelNode["source_model"] && modelNode["source_model"].IsScalar()
                    ? modelNode["source_model"].as<std::string>()
                    : "");
            entry.modelAsset = modelNode["model_asset"] && modelNode["model_asset"].IsScalar()
                ? normalizePathRef(modelNode["model_asset"].as<std::string>())
                : "";
            entry.modelSidecar = modelNode["model_sidecar"] && modelNode["model_sidecar"].IsScalar()
                ? normalizePathRef(modelNode["model_sidecar"].as<std::string>())
                : "";
            entry.sourceSkins = normalizeSkinSequence(modelNode["source_skins"]);

            const YAML::Node skinBindings = modelNode["skin_bindings"];
            if (skinBindings && skinBindings.IsSequence())
            {
                for (const YAML::Node &bindingNode : skinBindings)
                {
                    if (!bindingNode || !bindingNode.IsMap())
                    {
                        continue;
                    }

                    Mm9AnimatedModelSkinBinding binding = {};
                    binding.id = bindingNode["id"] && bindingNode["id"].IsScalar()
                        ? bindingNode["id"].as<std::string>()
                        : "";
                    binding.sourceSkins = normalizeSkinSequence(bindingNode["source_skins"]);
                    entry.skinBindings.push_back(binding);
                }
            }

            if (!entry.sourceModel.empty() && !entry.modelAsset.empty() && !entry.modelSidecar.empty())
            {
                m_entries.push_back(entry);
            }
        }
    }
    catch (const std::exception &exception)
    {
        errorMessage = "failed to load MM9 model registry " + registryPath.string() + ": " + exception.what();
        return false;
    }

    return true;
}

std::optional<Mm9AnimatedModelResolution> Mm9AnimatedModelResolver::resolve(
    const std::string &sourceModel,
    const std::string &sourceSkin,
    std::vector<AnimatedModelDiagnostic> &diagnostics) const
{
    const std::string normalizedModel = normalizeMm9AnimatedModelSourceModelRef(sourceModel);
    const std::string aliasedModel = aliasedRef(m_sourceModelAliases, normalizedModel);
    if (aliasedModel.empty())
    {
        addDiagnostic(diagnostics, "MM9 animated model resolution failed: empty source Filename", true);
        return std::nullopt;
    }

    const Mm9AnimatedModelRegistryEntry *pEntry = nullptr;
    for (const Mm9AnimatedModelRegistryEntry &entry : m_entries)
    {
        if (entry.sourceModel == aliasedModel)
        {
            pEntry = &entry;
            break;
        }
    }

    if (pEntry == nullptr)
    {
        addDiagnostic(
            diagnostics,
            "MM9 animated model resolution failed for Filename '" + sourceModel
                + "' normalized as '" + aliasedModel + "'",
            true);
        return std::nullopt;
    }

    std::vector<std::string> normalizedSkins =
        aliasedRefs(m_sourceSkinAliases, normalizeMm9AnimatedModelSourceSkinRefs(sourceSkin));
    const Mm9AnimatedModelSkinBinding *pSkinBinding = nullptr;

    if (normalizedSkins.empty())
    {
        normalizedSkins = pEntry->sourceSkins;
        pSkinBinding = findSkinBinding(*pEntry, normalizedSkins);
    }
    else
    {
        pSkinBinding = findSkinBinding(*pEntry, normalizedSkins);
        if (pSkinBinding == nullptr && pEntry->sourceSkins != normalizedSkins)
        {
            addDiagnostic(
                diagnostics,
                "MM9 animated model resolution uses object Skin override '" + sourceSkin
                    + "' normalized as '" + skinListKey(normalizedSkins)
                    + "' on Filename '" + sourceModel + "'",
                false);
        }
    }

    return makeResolution(
        *pEntry,
        m_worldRoot,
        sourceModel,
        sourceSkin,
        aliasedModel,
        normalizedSkins,
        pSkinBinding);
}

std::optional<Mm9AnimatedModelResolution> Mm9AnimatedModelResolver::resolveModelAsset(
    const std::string &modelAsset,
    const std::string &skinBindingId,
    const std::string &sourceModel,
    const std::string &sourceSkin,
    std::vector<AnimatedModelDiagnostic> &diagnostics) const
{
    const std::string normalizedModelAsset = normalizePathRef(modelAsset);
    if (normalizedModelAsset.empty())
    {
        addDiagnostic(diagnostics, "MM9 animated model resolution failed: empty model_asset", true);
        return std::nullopt;
    }

    const Mm9AnimatedModelRegistryEntry *pEntry = nullptr;
    for (const Mm9AnimatedModelRegistryEntry &entry : m_entries)
    {
        if (entry.modelAsset == normalizedModelAsset)
        {
            pEntry = &entry;
            break;
        }
    }

    if (pEntry == nullptr)
    {
        addDiagnostic(
            diagnostics,
            "MM9 animated model resolution failed for model_asset '" + modelAsset
                + "' normalized as '" + normalizedModelAsset + "'",
            true);
        return std::nullopt;
    }

    std::vector<std::string> normalizedSkins =
        aliasedRefs(m_sourceSkinAliases, normalizeMm9AnimatedModelSourceSkinRefs(sourceSkin));
    const Mm9AnimatedModelSkinBinding *pSkinBinding = nullptr;
    if (!skinBindingId.empty())
    {
        pSkinBinding = findSkinBindingById(*pEntry, skinBindingId);
        if (pSkinBinding == nullptr)
        {
            addDiagnostic(
                diagnostics,
                "MM9 animated model resolution failed for model_asset '" + modelAsset
                    + "': missing model_skin_binding '" + skinBindingId + "'",
                true);
            return std::nullopt;
        }
        normalizedSkins = pSkinBinding->sourceSkins;
    }
    else if (normalizedSkins.empty())
    {
        normalizedSkins = pEntry->sourceSkins;
        pSkinBinding = findSkinBinding(*pEntry, normalizedSkins);
    }
    else
    {
        pSkinBinding = findSkinBinding(*pEntry, normalizedSkins);
        if (pSkinBinding == nullptr && pEntry->sourceSkins != normalizedSkins)
        {
            addDiagnostic(
                diagnostics,
                "MM9 animated model resolution uses object Skin override '" + sourceSkin
                    + "' normalized as '" + skinListKey(normalizedSkins)
                    + "' on model_asset '" + modelAsset + "'",
                false);
        }
    }

    return makeResolution(
        *pEntry,
        m_worldRoot,
        sourceModel,
        sourceSkin,
        pEntry->sourceModel,
        normalizedSkins,
        pSkinBinding);
}

const std::vector<Mm9AnimatedModelRegistryEntry> &Mm9AnimatedModelResolver::entries() const
{
    return m_entries;
}
}
