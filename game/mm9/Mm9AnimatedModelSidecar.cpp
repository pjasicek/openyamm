#include "game/mm9/Mm9AnimatedModelSidecar.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cmath>
#include <cctype>
#include <cstdint>
#include <exception>
#include <fstream>
#include <limits>

namespace OpenYAMM::Game
{
namespace
{
std::string readString(const YAML::Node &node, const char *pKey)
{
    const YAML::Node value = node[pKey];
    if (!value || !value.IsScalar())
    {
        return {};
    }
    return value.as<std::string>();
}

int readInt(const YAML::Node &node, const char *pKey, int fallback = 0)
{
    const YAML::Node value = node[pKey];
    if (!value || !value.IsScalar())
    {
        return fallback;
    }
    return value.as<int>();
}

uint32_t readUInt32(const YAML::Node &node, const char *pKey, uint32_t fallback = 0)
{
    const YAML::Node value = node[pKey];
    if (!value || !value.IsScalar())
    {
        return fallback;
    }
    return value.as<uint32_t>();
}

float readFloat(const YAML::Node &node, const char *pKey, float fallback = 0.0f)
{
    const YAML::Node value = node[pKey];
    if (!value || !value.IsScalar())
    {
        return fallback;
    }
    return value.as<float>();
}

bool readBool(const YAML::Node &node, const char *pKey, bool fallback = false)
{
    const YAML::Node value = node[pKey];
    if (!value || !value.IsScalar())
    {
        return fallback;
    }
    return value.as<bool>();
}

std::vector<float> readFloatSequence(const YAML::Node &node)
{
    std::vector<float> values;
    if (!node || !node.IsSequence())
    {
        return values;
    }

    values.reserve(node.size());
    for (const YAML::Node &value : node)
    {
        values.push_back(value.as<float>());
    }
    return values;
}

std::vector<size_t> readSizeSequence(const YAML::Node &node)
{
    std::vector<size_t> values;
    if (!node || !node.IsSequence())
    {
        return values;
    }

    values.reserve(node.size());
    for (const YAML::Node &value : node)
    {
        values.push_back(value.as<size_t>());
    }
    return values;
}

AnimatedModelVec3 readVec3(const YAML::Node &node)
{
    if (!node || !node.IsSequence() || node.size() < 3)
    {
        return {};
    }

    return {node[0].as<float>(), node[1].as<float>(), node[2].as<float>()};
}

AnimatedModelQuat readQuat(const YAML::Node &node)
{
    if (!node || !node.IsSequence() || node.size() < 4)
    {
        return {};
    }

    return {node[0].as<float>(), node[1].as<float>(), node[2].as<float>(), node[3].as<float>()};
}

std::string lowerCopy(std::string value)
{
    std::transform(value.begin(), value.end(), value.begin(), [](unsigned char character)
    {
        return static_cast<char>(std::tolower(character));
    });
    return value;
}

std::optional<size_t> findMaterialByIndex(const std::vector<Mm9AnimatedModelMaterialRef> &materials, size_t index)
{
    for (size_t materialIndex = 0; materialIndex < materials.size(); ++materialIndex)
    {
        if (materials[materialIndex].index == index)
        {
            return materialIndex;
        }
    }
    return std::nullopt;
}
}

std::optional<Mm9AnimatedModelSidecar> loadMm9AnimatedModelSidecar(
    const std::filesystem::path &path,
    std::string &errorMessage)
{
    YAML::Node rootNode;
    try
    {
        rootNode = YAML::LoadFile(path.string());
    }
    catch (const std::exception &exception)
    {
        errorMessage = path.string() + ": YAML load failed: " + exception.what();
        return std::nullopt;
    }

    if (!rootNode || !rootNode.IsMap())
    {
        errorMessage = path.string() + ": sidecar root must be a map";
        return std::nullopt;
    }

    Mm9AnimatedModelSidecar sidecar = {};
    sidecar.schema = readString(rootNode, "schema");
    if (sidecar.schema != "openyamm.model3d.v1")
    {
        errorMessage = path.string() + ": unexpected model sidecar schema: " + sidecar.schema;
        return std::nullopt;
    }

    sidecar.id = readString(rootNode, "id");
    sidecar.model = readString(rootNode, "model");

    const YAML::Node sourceNode = rootNode["source"];
    if (sourceNode && sourceNode.IsMap())
    {
        sidecar.sourceFormat = readString(sourceNode, "format");
        sidecar.sourcePath = readString(sourceNode, "path");
        sidecar.sourceCommandString = readString(sourceNode, "commandString");
        sidecar.sourceVersion = readInt(sourceNode, "version");
    }

    const YAML::Node lodNode = rootNode["lod"];
    if (lodNode && lodNode.IsMap())
    {
        sidecar.exportedLodIndex = readInt(lodNode, "exportedIndex");
        sidecar.lodDistances = readFloatSequence(lodNode["distances"]);
    }

    const YAML::Node materialsNode = rootNode["materials"];
    if (materialsNode && materialsNode.IsSequence())
    {
        sidecar.materials.reserve(materialsNode.size());
        for (const YAML::Node &materialNode : materialsNode)
        {
            if (!materialNode || !materialNode.IsMap())
            {
                continue;
            }

            Mm9AnimatedModelMaterialRef material = {};
            material.index = static_cast<size_t>(readInt(materialNode, "index"));
            material.texture = readString(materialNode, "texture");
            material.runtimeTexture = readString(materialNode, "runtime_texture");
            material.previewTexture = readString(materialNode, "preview_texture");
            const std::string alphaMode = lowerCopy(readString(materialNode, "alphaMode"));
            material.alphaMask = alphaMode == "mask";
            material.alphaCutoff = readFloat(materialNode, "alphaCutoff", 0.5f);
            material.doubleSided = readBool(materialNode, "doubleSided", false);
            sidecar.materials.push_back(std::move(material));
        }
    }

    const YAML::Node skeletonNode = rootNode["skeleton"];
    if (skeletonNode && skeletonNode.IsMap())
    {
        const YAML::Node nodesNode = skeletonNode["nodes"];
        if (nodesNode && nodesNode.IsSequence())
        {
            sidecar.skeleton.nodes.reserve(nodesNode.size());
            for (const YAML::Node &node : nodesNode)
            {
                if (!node || !node.IsMap())
                {
                    continue;
                }

                Mm9AnimatedModelSkeletonNode skeletonNodeInfo = {};
                skeletonNodeInfo.index = static_cast<size_t>(readInt(node, "index"));
                skeletonNodeInfo.name = readString(node, "name");
                skeletonNodeInfo.parentIndex = readInt(node, "parent", -1);
                skeletonNodeInfo.flags = readUInt32(node, "flags");
                skeletonNodeInfo.childIndices = readSizeSequence(node["children"]);
                sidecar.skeleton.nodes.push_back(std::move(skeletonNodeInfo));
            }
        }
    }

    const YAML::Node socketsNode = rootNode["sockets"];
    if (socketsNode && socketsNode.IsSequence())
    {
        sidecar.sockets.reserve(socketsNode.size());
        for (const YAML::Node &socketNode : socketsNode)
        {
            if (!socketNode || !socketNode.IsMap())
            {
                continue;
            }

            AnimatedModelSocket socket = {};
            socket.name = readString(socketNode, "name");
            socket.nodeIndex = static_cast<size_t>(readInt(socketNode, "node"));
            socket.localTransform.translation = readVec3(socketNode["translation"]);
            socket.localTransform.rotation = readQuat(socketNode["rotation"]);
            sidecar.sockets.push_back(std::move(socket));
        }
    }

    const YAML::Node animationsNode = rootNode["animations"];
    if (animationsNode && animationsNode.IsSequence())
    {
        sidecar.animations.reserve(animationsNode.size());
        for (const YAML::Node &animationNode : animationsNode)
        {
            if (!animationNode || !animationNode.IsMap())
            {
                continue;
            }

            Mm9AnimatedModelAnimationInfo animation = {};
            animation.name = readString(animationNode, "name");
            animation.durationMs = readUInt32(animationNode, "durationMs");
            animation.keyframes = readUInt32(animationNode, "keyframes");
            animation.interpolationTimeMs = readUInt32(animationNode, "interpolationTimeMs");
            const YAML::Node eventsNode = animationNode["events"];
            if (eventsNode && eventsNode.IsSequence())
            {
                animation.events.reserve(eventsNode.size());
                for (const YAML::Node &eventNode : eventsNode)
                {
                    if (!eventNode || !eventNode.IsMap())
                    {
                        continue;
                    }

                    animation.events.push_back(Mm9AnimatedModelAnimationEvent{
                        readUInt32(eventNode, "timeMs"),
                        readString(eventNode, "event")});
                }
            }
            sidecar.animations.push_back(std::move(animation));
        }
    }

    return sidecar;
}

void mergeMm9AnimatedModelSidecar(
    const Mm9AnimatedModelSidecar &sidecar,
    AnimatedModelAsset &asset)
{
    asset.lod.exportedIndex = sidecar.exportedLodIndex;
    asset.lod.distances = sidecar.lodDistances;
    asset.lod.valid = !sidecar.lodDistances.empty();
    if (asset.lod.valid)
    {
        if (asset.lod.exportedIndex < 0)
        {
            asset.diagnostics.push_back(AnimatedModelDiagnostic{
                "MM9 sidecar LOD exported index is negative",
                true});
        }
        for (const float distance : asset.lod.distances)
        {
            if (!std::isfinite(distance) || distance < 0.0f)
            {
                asset.diagnostics.push_back(AnimatedModelDiagnostic{
                    "MM9 sidecar LOD distance is invalid",
                    true});
            }
        }
    }

    for (const Mm9AnimatedModelSkeletonNode &node : sidecar.skeleton.nodes)
    {
        if (node.index >= asset.nodes.size())
        {
            asset.diagnostics.push_back(AnimatedModelDiagnostic{
                "MM9 sidecar skeleton node " + node.name + " references invalid node index",
                true});
        }

        if (node.parentIndex >= 0 && static_cast<size_t>(node.parentIndex) >= asset.nodes.size())
        {
            asset.diagnostics.push_back(AnimatedModelDiagnostic{
                "MM9 sidecar skeleton node " + node.name + " references invalid parent node",
                true});
        }

        for (const size_t childIndex : node.childIndices)
        {
            if (childIndex >= asset.nodes.size())
            {
                asset.diagnostics.push_back(AnimatedModelDiagnostic{
                    "MM9 sidecar skeleton node " + node.name + " references invalid child node",
                    true});
            }
        }
    }

    asset.sockets = sidecar.sockets;

    for (AnimatedModelSocket &socket : asset.sockets)
    {
        if (socket.nodeIndex >= asset.nodes.size())
        {
            asset.diagnostics.push_back(AnimatedModelDiagnostic{
                "MM9 sidecar socket " + socket.name + " references invalid node",
                true});
        }
    }

    for (AnimatedModelClip &clip : asset.clips)
    {
        for (const Mm9AnimatedModelAnimationInfo &animation : sidecar.animations)
        {
            if (lowerCopy(animation.name) != lowerCopy(clip.name))
            {
                continue;
            }

            clip.events.clear();
            clip.events.reserve(animation.events.size());
            for (const Mm9AnimatedModelAnimationEvent &event : animation.events)
            {
                clip.events.push_back(AnimatedModelEvent{
                    .timeSeconds = static_cast<float>(event.timeMs) / 1000.0f,
                    .key = event.event,
                });
            }
            break;
        }
    }

    for (const Mm9AnimatedModelMaterialRef &materialRef : sidecar.materials)
    {
        if (materialRef.index >= asset.materials.size())
        {
            asset.diagnostics.push_back(AnimatedModelDiagnostic{
                "MM9 sidecar material index is outside GLB material list",
                true});
            continue;
        }

        AnimatedModelMaterial &material = asset.materials[materialRef.index];
        if (!materialRef.runtimeTexture.empty())
        {
            material.baseColorTextureUri = materialRef.runtimeTexture;
        }
        material.alphaMask = material.alphaMask || materialRef.alphaMask;
        material.alphaCutoff = materialRef.alphaCutoff;
        material.doubleSided = material.doubleSided || materialRef.doubleSided;
    }

    for (const AnimatedModelPrimitive &primitive : asset.primitives)
    {
        if (primitive.materialIndex == std::numeric_limits<size_t>::max())
        {
            continue;
        }
        if (!findMaterialByIndex(sidecar.materials, primitive.materialIndex))
        {
            asset.diagnostics.push_back(AnimatedModelDiagnostic{
                "GLB primitive material has no MM9 sidecar material entry",
                false});
        }
    }
}
}
