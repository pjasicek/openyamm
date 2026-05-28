#include "game/mm9/Mm9ScriptedBillboardVisuals.h"

#include "engine/AssetFileSystem.h"
#include "game/maps/MapIdentity.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <exception>
#include <limits>
#include <unordered_set>
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
        [](unsigned char value)
        {
            return static_cast<char>(std::tolower(value));
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

std::string normalizeRef(const std::string &value)
{
    std::string output = trimCopy(value);
    std::replace(output.begin(), output.end(), '\\', '/');
    return toLowerCopy(output);
}

std::string normalizeModelRef(const std::string &value)
{
    std::string output = normalizeRef(value);
    if (!output.empty() && output.find('/') == std::string::npos)
    {
        output = "models/" + output;
    }
    return output;
}

std::string normalizeSkinRefs(const std::vector<std::string> &sourceSkins)
{
    std::vector<std::string> normalizedSkins;
    normalizedSkins.reserve(sourceSkins.size());

    for (const std::string &sourceSkin : sourceSkins)
    {
        std::string normalized = normalizeRef(sourceSkin);
        if (!normalized.empty() && normalized.find('/') == std::string::npos)
        {
            normalized = "skins/" + normalized;
        }

        if (!normalized.empty())
        {
            normalizedSkins.push_back(normalized);
        }
    }

    std::sort(normalizedSkins.begin(), normalizedSkins.end());

    std::ostringstream stream;
    for (size_t index = 0; index < normalizedSkins.size(); ++index)
    {
        if (index != 0)
        {
            stream << ';';
        }
        stream << normalizedSkins[index];
    }

    return stream.str();
}

std::vector<std::string> splitSkinRefs(const std::string &value)
{
    std::vector<std::string> output;
    std::string current;

    for (const char ch : value)
    {
        if (ch == ';')
        {
            const std::string normalized = normalizeRef(current);
            if (!normalized.empty())
            {
                output.push_back(normalized);
            }
            current.clear();
        }
        else
        {
            current.push_back(ch);
        }
    }

    const std::string normalized = normalizeRef(current);
    if (!normalized.empty())
    {
        output.push_back(normalized);
    }

    return output;
}

std::string mapObjectKey(const std::string &mapId, size_t sourceObjectIndex)
{
    return normalizeWorldId(mapId) + ":" + std::to_string(sourceObjectIndex);
}

std::string mapClassNameKey(const std::string &mapId, const std::string &sourceClass, const std::string &sourceName)
{
    return normalizeWorldId(mapId) + ":" + normalizeRef(sourceClass) + ":" + normalizeRef(sourceName);
}

std::string sourceModelSkinKey(const std::string &sourceModel, const std::vector<std::string> &sourceSkins)
{
    return normalizeModelRef(sourceModel) + ":" + normalizeSkinRefs(sourceSkins);
}

const Mm9ScriptedBillboardClip *findClipBySemantic(
    const Mm9ScriptedBillboardVisual &visual,
    const std::string &semantic)
{
    const std::string normalizedSemantic = normalizeRef(semantic);
    if (normalizedSemantic.empty())
    {
        return nullptr;
    }

    for (const Mm9ScriptedBillboardClip &clip : visual.clips)
    {
        if (normalizeRef(clip.semantic) == normalizedSemantic)
        {
            return &clip;
        }
    }

    return nullptr;
}

const Mm9ScriptedBillboardClip *findFirstClipWithFrames(const Mm9ScriptedBillboardVisual &visual)
{
    for (const Mm9ScriptedBillboardClip &clip : visual.clips)
    {
        if (!clip.frames.empty())
        {
            return &clip;
        }
    }

    return nullptr;
}

std::string readScalarString(const YAML::Node &node, const char *pKey, const std::string &fallback = "")
{
    const YAML::Node value = node[pKey];
    if (!value || !value.IsScalar())
    {
        return fallback;
    }

    return value.as<std::string>();
}

int readScalarInt(const YAML::Node &node, const char *pKey, int fallback)
{
    const YAML::Node value = node[pKey];
    if (!value || !value.IsScalar())
    {
        return fallback;
    }

    return value.as<int>();
}

float readScalarFloat(const YAML::Node &node, const char *pKey, float fallback)
{
    const YAML::Node value = node[pKey];
    if (!value || !value.IsScalar())
    {
        return fallback;
    }

    return value.as<float>();
}

uint32_t readScalarUInt32(const YAML::Node &node, const char *pKey, uint32_t fallback)
{
    const YAML::Node value = node[pKey];
    if (!value || !value.IsScalar())
    {
        return fallback;
    }

    const uint64_t parsed = value.as<uint64_t>();
    return static_cast<uint32_t>(std::min<uint64_t>(parsed, std::numeric_limits<uint32_t>::max()));
}

size_t readScalarSize(const YAML::Node &node, const char *pKey, size_t fallback)
{
    const YAML::Node value = node[pKey];
    if (!value || !value.IsScalar())
    {
        return fallback;
    }

    return value.as<size_t>();
}

bool hasYamlExtension(const std::string &entryName)
{
    const std::string normalized = toLowerCopy(entryName);
    return normalized.ends_with(".yml") || normalized.ends_with(".yaml");
}

bool startsWithMm9Prefix(const std::string &entryName)
{
    return toLowerCopy(entryName).starts_with("mm9_");
}

std::string joinVirtualPath(const std::string &rootPath, const std::string &relativePath)
{
    if (rootPath.empty())
    {
        return relativePath;
    }
    if (relativePath.empty())
    {
        return rootPath;
    }
    if (rootPath.ends_with("/"))
    {
        return rootPath + relativePath;
    }
    return rootPath + "/" + relativePath;
}

std::vector<std::string> readStringSequence(const YAML::Node &node)
{
    std::vector<std::string> output;
    if (!node || !node.IsSequence())
    {
        return output;
    }

    output.reserve(node.size());
    for (const YAML::Node &entry : node)
    {
        if (entry.IsScalar())
        {
            output.push_back(entry.as<std::string>());
        }
    }

    return output;
}

bool parseFrame(
    const YAML::Node &frameNode,
    Mm9ScriptedBillboardFrame &frame,
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &rootPath,
    bool verifyFrameAssets,
    std::string &errorMessage)
{
    if (!frameNode || !frameNode.IsMap())
    {
        errorMessage = "frame entry must be a map";
        return false;
    }

    frame.textureName = readScalarString(frameNode, "texture");
    frame.path = readScalarString(frameNode, "path");
    frame.angle = readScalarString(frameNode, "angle");
    frame.durationMs = readScalarUInt32(frameNode, "duration_ms", 0);
    frame.anchorX = readScalarFloat(frameNode, "anchor_x", -1.0f);
    frame.anchorY = readScalarFloat(frameNode, "anchor_y", -1.0f);

    if (frame.textureName.empty())
    {
        errorMessage = "frame entry is missing texture";
        return false;
    }
    if (frame.path.empty())
    {
        errorMessage = "frame " + frame.textureName + " is missing path";
        return false;
    }
    if (verifyFrameAssets && !assetFileSystem.exists(joinVirtualPath(rootPath, frame.path)))
    {
        errorMessage = "frame asset is missing: " + joinVirtualPath(rootPath, frame.path);
        return false;
    }

    return true;
}

bool parseClip(
    const std::string &clipName,
    const YAML::Node &clipNode,
    Mm9ScriptedBillboardClip &clip,
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &rootPath,
    bool verifyFrameAssets,
    std::string &errorMessage)
{
    if (!clipNode || !clipNode.IsMap())
    {
        errorMessage = "clip " + clipName + " must be a map";
        return false;
    }

    clip.name = clipName;
    clip.semantic = readScalarString(clipNode, "semantic");
    clip.fallback = readScalarString(clipNode, "fallback");
    clip.sourceClip = readScalarString(clipNode, "source_clip");
    clip.angleCount = readScalarUInt32(clipNode, "angles", 0);
    clip.durationMs = readScalarUInt32(clipNode, "duration_ms", 0);

    const YAML::Node framesNode = clipNode["frames"];
    if (!framesNode || !framesNode.IsSequence() || framesNode.size() == 0)
    {
        errorMessage = "clip " + clipName + " has no frames";
        return false;
    }

    clip.frames.reserve(framesNode.size());
    for (const YAML::Node &frameNode : framesNode)
    {
        Mm9ScriptedBillboardFrame frame = {};
        if (!parseFrame(frameNode, frame, assetFileSystem, rootPath, verifyFrameAssets, errorMessage))
        {
            errorMessage = "clip " + clipName + ": " + errorMessage;
            return false;
        }
        clip.frames.push_back(std::move(frame));
    }

    return true;
}

bool parseUsedBy(
    const YAML::Node &useNode,
    Mm9ScriptedBillboardUse &usedBy,
    std::string &errorMessage)
{
    if (!useNode || !useNode.IsMap())
    {
        errorMessage = "used_by entry must be a map";
        return false;
    }

    usedBy.mapId = readScalarString(useNode, "map");
    usedBy.objectId = readScalarString(useNode, "object_id");
    usedBy.sourceObjectIndex = readScalarSize(useNode, "source_object_index", 0);
    usedBy.sourceClass = readScalarString(useNode, "source_class");
    usedBy.sourceName = readScalarString(useNode, "source_name");
    usedBy.scriptName = readScalarString(useNode, "script_name");
    usedBy.scriptParams = readScalarString(useNode, "script_params");

    if (usedBy.mapId.empty())
    {
        errorMessage = "used_by entry is missing map";
        return false;
    }

    return true;
}

bool parseVisualYaml(
    const YAML::Node &rootNode,
    Mm9ScriptedBillboardVisual &visual,
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &rootPath,
    bool verifyFrameAssets,
    std::string &errorMessage)
{
    if (!rootNode || !rootNode.IsMap())
    {
        errorMessage = "visual file root must be a map";
        return false;
    }

    const std::string schema = readScalarString(rootNode, "schema");
    if (schema != Mm9ScriptedBillboardVisualSchema)
    {
        errorMessage = "unexpected schema: " + schema;
        return false;
    }

    visual.visualId = readScalarString(rootNode, "visual_id");
    if (!visual.visualId.starts_with("mm9_"))
    {
        errorMessage = "visual_id must use mm9_ prefix";
        return false;
    }

    visual.sourceModel = readScalarString(rootNode, "source_model");
    visual.sourceGlb = readScalarString(rootNode, "source_glb");
    visual.sourceSkins = readStringSequence(rootNode["source_skins"]);
    visual.variantId = readScalarString(rootNode, "variant_id");
    visual.modelId = readScalarString(rootNode, "model_id");
    visual.angleCount = readScalarUInt32(rootNode, "angle_count", 0);
    visual.angleNames = readStringSequence(rootNode["angle_names"]);

    const YAML::Node clipsNode = rootNode["clips"];
    if (!clipsNode || !clipsNode.IsMap() || clipsNode.size() == 0)
    {
        errorMessage = "visual " + visual.visualId + " has no clips";
        return false;
    }

    visual.clips.reserve(clipsNode.size());
    for (YAML::const_iterator iterator = clipsNode.begin(); iterator != clipsNode.end(); ++iterator)
    {
        const std::string clipName = iterator->first.as<std::string>();
        Mm9ScriptedBillboardClip clip = {};
        if (!parseClip(
                clipName,
                iterator->second,
                clip,
                assetFileSystem,
                rootPath,
                verifyFrameAssets,
                errorMessage))
        {
            errorMessage = "visual " + visual.visualId + ": " + errorMessage;
            return false;
        }
        visual.clips.push_back(std::move(clip));
    }

    const YAML::Node collisionNode = rootNode["collision"];
    if (collisionNode && collisionNode.IsMap())
    {
        visual.collision.radius = readScalarInt(collisionNode, "radius", visual.collision.radius);
        visual.collision.height = readScalarInt(collisionNode, "height", visual.collision.height);
        visual.collision.verticalOffset =
            readScalarInt(collisionNode, "vertical_offset", visual.collision.verticalOffset);
        visual.collision.anchor = readScalarString(collisionNode, "anchor", visual.collision.anchor);
        visual.collision.source = readScalarString(collisionNode, "source");
    }

    const YAML::Node usedByNode = rootNode["used_by"];
    if (usedByNode && usedByNode.IsSequence())
    {
        visual.usedBy.reserve(usedByNode.size());
        for (const YAML::Node &useNode : usedByNode)
        {
            Mm9ScriptedBillboardUse usedBy = {};
            if (!parseUsedBy(useNode, usedBy, errorMessage))
            {
                errorMessage = "visual " + visual.visualId + ": " + errorMessage;
                return false;
            }
            visual.usedBy.push_back(std::move(usedBy));
        }
    }

    return true;
}
}

bool Mm9ScriptedBillboardVisualSet::loadFromAssetFileSystem(
    const Engine::AssetFileSystem &assetFileSystem,
    std::string &errorMessage,
    const std::string &rootPath,
    bool verifyFrameAssets)
{
    m_visuals.clear();
    m_visualIndexById.clear();
    m_visualIndexByMapObject.clear();
    m_visualIndexByMapClassName.clear();
    m_visualIndexBySourceModel.clear();
    m_visualIndexBySourceModelAndSkin.clear();
    errorMessage.clear();

    const std::vector<std::string> entries = assetFileSystem.enumerate(rootPath);
    for (const std::string &entry : entries)
    {
        if (!startsWithMm9Prefix(entry) || !hasYamlExtension(entry))
        {
            continue;
        }

        const std::string virtualPath = joinVirtualPath(rootPath, entry);
        const std::optional<std::string> yamlText = assetFileSystem.readTextFile(virtualPath);
        if (!yamlText)
        {
            errorMessage = "failed to read " + virtualPath;
            return false;
        }

        YAML::Node rootNode;
        try
        {
            rootNode = YAML::Load(*yamlText);
        }
        catch (const YAML::Exception &exception)
        {
            errorMessage = virtualPath + ": YAML parse failed: " + exception.what();
            return false;
        }

        Mm9ScriptedBillboardVisual visual = {};
        try
        {
            if (!parseVisualYaml(rootNode, visual, assetFileSystem, rootPath, verifyFrameAssets, errorMessage))
            {
                errorMessage = virtualPath + ": " + errorMessage;
                return false;
            }
        }
        catch (const std::exception &exception)
        {
            errorMessage = virtualPath + ": " + exception.what();
            return false;
        }

        m_visuals.push_back(std::move(visual));
    }

    rebuildIndexes();
    return true;
}

const Mm9ScriptedBillboardVisual *Mm9ScriptedBillboardVisualSet::findVisual(const std::string &visualId) const
{
    const std::unordered_map<std::string, size_t>::const_iterator iterator =
        m_visualIndexById.find(normalizeRef(visualId));
    if (iterator == m_visualIndexById.end() || iterator->second >= m_visuals.size())
    {
        return nullptr;
    }

    return &m_visuals[iterator->second];
}

const Mm9ScriptedBillboardClip *Mm9ScriptedBillboardVisualSet::findClip(
    const Mm9ScriptedBillboardVisual &visual,
    const std::string &clipName) const
{
    const std::string normalizedClipName = normalizeRef(clipName);
    for (const Mm9ScriptedBillboardClip &clip : visual.clips)
    {
        if (normalizeRef(clip.name) == normalizedClipName)
        {
            return &clip;
        }
    }

    return nullptr;
}

const Mm9ScriptedBillboardClip *Mm9ScriptedBillboardVisualSet::findIdleClip(
    const Mm9ScriptedBillboardVisual &visual) const
{
    const Mm9ScriptedBillboardClip *pClip = findClip(visual, "idle");
    if (pClip != nullptr)
    {
        return pClip;
    }

    for (const Mm9ScriptedBillboardClip &clip : visual.clips)
    {
        if (normalizeRef(clip.semantic) == "idle" || normalizeRef(clip.semantic) == "stand")
        {
            return &clip;
        }
    }

    if (!visual.clips.empty())
    {
        return &visual.clips.front();
    }

    return nullptr;
}

const Mm9ScriptedBillboardFrame *Mm9ScriptedBillboardVisualSet::findFirstIdleFrame(
    const Mm9ScriptedBillboardVisual &visual) const
{
    const Mm9ScriptedBillboardClip *pClip = findIdleClip(visual);
    if (pClip == nullptr || pClip->frames.empty())
    {
        return nullptr;
    }

    return &pClip->frames.front();
}

const Mm9ScriptedBillboardClip *Mm9ScriptedBillboardVisualSet::resolveClip(
    const Mm9ScriptedBillboardVisual &visual,
    const std::string &clipName,
    const std::string &semanticFallback) const
{
    std::unordered_set<std::string> visitedClips;
    const Mm9ScriptedBillboardClip *pClip = findClip(visual, clipName);

    while (pClip != nullptr)
    {
        if (!pClip->frames.empty())
        {
            return pClip;
        }

        const std::string fallbackClipName = normalizeRef(pClip->fallback);
        if (fallbackClipName.empty() || visitedClips.contains(fallbackClipName))
        {
            break;
        }

        visitedClips.insert(fallbackClipName);
        pClip = findClip(visual, pClip->fallback);
    }

    pClip = findClipBySemantic(visual, semanticFallback);
    if (pClip != nullptr && !pClip->frames.empty())
    {
        return pClip;
    }

    pClip = findIdleClip(visual);
    if (pClip != nullptr && !pClip->frames.empty())
    {
        return pClip;
    }

    return findFirstClipWithFrames(visual);
}

const Mm9ScriptedBillboardFrame *Mm9ScriptedBillboardVisualSet::resolveFrame(
    const Mm9ScriptedBillboardVisual &visual,
    const std::string &clipName,
    const std::string &semanticFallback,
    const std::string &angleName,
    uint32_t elapsedMs) const
{
    const Mm9ScriptedBillboardClip *pClip = resolveClip(visual, clipName, semanticFallback);
    if (pClip == nullptr || pClip->frames.empty())
    {
        return nullptr;
    }

    const std::string normalizedAngleName = normalizeRef(angleName);
    std::vector<const Mm9ScriptedBillboardFrame *> angleFrames;
    angleFrames.reserve(pClip->frames.size());

    if (!normalizedAngleName.empty())
    {
        for (const Mm9ScriptedBillboardFrame &frame : pClip->frames)
        {
            if (normalizeRef(frame.angle) == normalizedAngleName)
            {
                angleFrames.push_back(&frame);
            }
        }
    }

    if (angleFrames.empty())
    {
        for (const Mm9ScriptedBillboardFrame &frame : pClip->frames)
        {
            angleFrames.push_back(&frame);
        }
    }

    uint32_t totalDurationMs = 0;
    for (const Mm9ScriptedBillboardFrame *pFrame : angleFrames)
    {
        totalDurationMs += std::max(pFrame->durationMs, uint32_t(1));
    }

    if (totalDurationMs == 0)
    {
        return angleFrames.front();
    }

    uint32_t frameTimeMs = elapsedMs % totalDurationMs;
    for (const Mm9ScriptedBillboardFrame *pFrame : angleFrames)
    {
        const uint32_t durationMs = std::max(pFrame->durationMs, uint32_t(1));
        if (frameTimeMs < durationMs)
        {
            return pFrame;
        }
        frameTimeMs -= durationMs;
    }

    return angleFrames.back();
}

std::optional<std::string> Mm9ScriptedBillboardVisualSet::resolveVisualIdForModelInstance(
    const std::string &mapId,
    const OutdoorSceneModelInstance &modelInstance) const
{
    const std::string normalizedMapId = normalizeWorldId(mapId);

    const std::unordered_map<std::string, size_t>::const_iterator objectIterator =
        m_visualIndexByMapObject.find(mapObjectKey(normalizedMapId, modelInstance.sourceObjectIndex));
    if (objectIterator != m_visualIndexByMapObject.end() && objectIterator->second < m_visuals.size())
    {
        return m_visuals[objectIterator->second].visualId;
    }

    const std::unordered_map<std::string, size_t>::const_iterator classNameIterator =
        m_visualIndexByMapClassName.find(
            mapClassNameKey(normalizedMapId, modelInstance.sourceClass, modelInstance.sourceName));
    if (classNameIterator != m_visualIndexByMapClassName.end() && classNameIterator->second < m_visuals.size())
    {
        return m_visuals[classNameIterator->second].visualId;
    }

    const std::vector<std::string> instanceSkins = splitSkinRefs(modelInstance.sourceSkin);
    const std::string exactModelSkinKey = sourceModelSkinKey(modelInstance.sourceModel, instanceSkins);
    const std::unordered_map<std::string, size_t>::const_iterator exactIterator =
        m_visualIndexBySourceModelAndSkin.find(exactModelSkinKey);
    if (exactIterator != m_visualIndexBySourceModelAndSkin.end() && exactIterator->second < m_visuals.size())
    {
        return m_visuals[exactIterator->second].visualId;
    }

    const std::unordered_map<std::string, size_t>::const_iterator sourceModelIterator =
        m_visualIndexBySourceModel.find(normalizeModelRef(modelInstance.sourceModel));
    if (sourceModelIterator != m_visualIndexBySourceModel.end() && sourceModelIterator->second < m_visuals.size())
    {
        return m_visuals[sourceModelIterator->second].visualId;
    }

    return std::nullopt;
}

const std::vector<Mm9ScriptedBillboardVisual> &Mm9ScriptedBillboardVisualSet::visuals() const
{
    return m_visuals;
}

void Mm9ScriptedBillboardVisualSet::rebuildIndexes()
{
    for (size_t visualIndex = 0; visualIndex < m_visuals.size(); ++visualIndex)
    {
        const Mm9ScriptedBillboardVisual &visual = m_visuals[visualIndex];
        m_visualIndexById.emplace(normalizeRef(visual.visualId), visualIndex);

        const std::string normalizedSourceModel = normalizeModelRef(visual.sourceModel);
        if (!normalizedSourceModel.empty())
        {
            m_visualIndexBySourceModel.emplace(normalizedSourceModel, visualIndex);
            m_visualIndexBySourceModelAndSkin.emplace(
                sourceModelSkinKey(visual.sourceModel, visual.sourceSkins),
                visualIndex);
        }

        for (const Mm9ScriptedBillboardUse &usedBy : visual.usedBy)
        {
            m_visualIndexByMapObject.emplace(mapObjectKey(usedBy.mapId, usedBy.sourceObjectIndex), visualIndex);

            if (!usedBy.sourceClass.empty() || !usedBy.sourceName.empty())
            {
                m_visualIndexByMapClassName.emplace(
                    mapClassNameKey(usedBy.mapId, usedBy.sourceClass, usedBy.sourceName),
                    visualIndex);
            }
        }
    }
}
}
