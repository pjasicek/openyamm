#include "game/tables/SurfaceMaterialTable.h"

#include "game/FaceEnums.h"
#include "game/StringUtils.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cctype>
#include <cmath>
#include <exception>
#include <unordered_set>

namespace OpenYAMM::Game
{
namespace
{
std::optional<SurfaceMaterialSemantic> parseSemantic(const std::string &value)
{
    const std::string normalizedValue = toLowerCopy(value);

    if (normalizedValue == "generic")
    {
        return SurfaceMaterialSemantic::Generic;
    }

    if (normalizedValue == "generic_animated")
    {
        return SurfaceMaterialSemantic::GenericAnimated;
    }

    if (normalizedValue == "water")
    {
        return SurfaceMaterialSemantic::Water;
    }

    if (normalizedValue == "lava")
    {
        return SurfaceMaterialSemantic::Lava;
    }

    return std::nullopt;
}

std::optional<uint32_t> parseFaceAttributeName(const std::string &value)
{
    const std::string normalizedValue = toLowerCopy(value);

    if (normalizedValue == "fluid")
    {
        return faceAttributeBit(FaceAttribute::Fluid);
    }

    if (normalizedValue == "lava")
    {
        return faceAttributeBit(FaceAttribute::Lava);
    }

    if (normalizedValue == "flow_down")
    {
        return faceAttributeBit(FaceAttribute::FlowDown);
    }

    if (normalizedValue == "flow_up")
    {
        return faceAttributeBit(FaceAttribute::FlowUp);
    }

    if (normalizedValue == "flow_left")
    {
        return faceAttributeBit(FaceAttribute::FlowLeft);
    }

    if (normalizedValue == "flow_right")
    {
        return faceAttributeBit(FaceAttribute::FlowRight);
    }

    return std::nullopt;
}

bool nodeAsStringSequence(const YAML::Node &node, std::vector<std::string> &values)
{
    values.clear();

    if (!node || !node.IsSequence())
    {
        return false;
    }

    for (const YAML::Node &entryNode : node)
    {
        if (!entryNode.IsScalar())
        {
            return false;
        }

        values.push_back(toLowerCopy(entryNode.as<std::string>()));
    }

    return true;
}

void distributeEvenFrameLengths(SurfaceAnimationSequence &animation, uint32_t animationLengthTicks)
{
    if (animation.frames.empty())
    {
        animation.animationLengthTicks = 0;
        return;
    }

    animation.animationLengthTicks = animationLengthTicks;

    if (animation.frames.size() == 1)
    {
        animation.frames.front().frameLengthTicks = animationLengthTicks;
        return;
    }

    const uint32_t frameCount = static_cast<uint32_t>(animation.frames.size());
    const uint32_t baseFrameLength = frameCount == 0 ? 0 : animationLengthTicks / frameCount;
    uint32_t remainder = frameCount == 0 ? 0 : animationLengthTicks % frameCount;

    for (SurfaceAnimationFrame &frame : animation.frames)
    {
        frame.frameLengthTicks = baseFrameLength + (remainder > 0 ? 1U : 0U);

        if (remainder > 0)
        {
            --remainder;
        }
    }
}

std::optional<uint32_t> frameLengthTicksFromNode(const YAML::Node &frameNode)
{
    if (const YAML::Node ticksNode = frameNode["ticks"]; ticksNode && ticksNode.IsScalar())
    {
        return ticksNode.as<uint32_t>();
    }

    if (const YAML::Node ticksNode = frameNode["frame_length_ticks"]; ticksNode && ticksNode.IsScalar())
    {
        return ticksNode.as<uint32_t>();
    }

    if (const YAML::Node ticksNode = frameNode["length_ticks"]; ticksNode && ticksNode.IsScalar())
    {
        return ticksNode.as<uint32_t>();
    }

    return std::nullopt;
}

std::string frameTextureNameFromNode(const YAML::Node &frameNode)
{
    if (const YAML::Node textureNode = frameNode["texture"]; textureNode && textureNode.IsScalar())
    {
        return textureNode.as<std::string>();
    }

    if (const YAML::Node textureNode = frameNode["texture_name"]; textureNode && textureNode.IsScalar())
    {
        return textureNode.as<std::string>();
    }

    if (const YAML::Node nameNode = frameNode["name"]; nameNode && nameNode.IsScalar())
    {
        return nameNode.as<std::string>();
    }

    return {};
}

void normalizeExplicitFrameLengths(SurfaceAnimationSequence &animation)
{
    uint32_t animationLengthTicks = 0;

    for (SurfaceAnimationFrame &frame : animation.frames)
    {
        frame.frameLengthTicks = std::max(1u, frame.frameLengthTicks);
        animationLengthTicks += frame.frameLengthTicks;
    }

    animation.animationLengthTicks = animationLengthTicks;
}

bool shadingFloatInRange(
    const YAML::Node &node,
    const char *propertyName,
    const std::string &materialId,
    float minValue,
    float maxValue,
    float &outValue,
    std::string &errorMessage)
{
    float value = 0.0f;

    try
    {
        value = node.as<float>();
    }
    catch (const std::exception &)
    {
        errorMessage = "surface material '" + materialId + "': shading." + propertyName
            + " must be a number";
        return false;
    }

    if (!std::isfinite(value))
    {
        errorMessage = "surface material '" + materialId + "': shading." + propertyName
            + " must be a finite number";
        return false;
    }

    if (value < minValue || value > maxValue)
    {
        errorMessage = "surface material '" + materialId + "': shading." + propertyName + "="
            + std::to_string(value) + " is outside the allowed range ["
            + std::to_string(minValue) + ", " + std::to_string(maxValue) + "]";
        return false;
    }

    outValue = value;
    return true;
}

bool shadingBoolValue(
    const YAML::Node &node,
    const char *propertyName,
    const std::string &materialId,
    bool &outValue,
    std::string &errorMessage)
{
    try
    {
        outValue = node.as<bool>();
        return true;
    }
    catch (const std::exception &)
    {
        errorMessage = "surface material '" + materialId + "': shading." + propertyName
            + " must be a boolean";
        return false;
    }
}

std::optional<SurfaceMaterialShading> parseShadingNode(
    const YAML::Node &shadingNode,
    const std::string &materialId,
    bool appliesToTerrain,
    bool appliesToFaces,
    std::string &errorMessage)
{
    if (!shadingNode.IsMap())
    {
        errorMessage = "surface material '" + materialId + "': shading must be a YAML map";
        return std::nullopt;
    }

    SurfaceMaterialShading shading = {};

    for (const auto &entry : shadingNode)
    {
        const std::string propertyName = entry.first.as<std::string>("");

        if (propertyName.empty())
        {
            errorMessage = "surface material '" + materialId + "': shading has an empty property name";
            return std::nullopt;
        }

        const YAML::Node valueNode = entry.second;

        if (propertyName == "roughness")
        {
            if (!shadingFloatInRange(
                    valueNode, "roughness", materialId, 0.05f, 1.0f, shading.roughness, errorMessage))
            {
                return std::nullopt;
            }
        }
        else if (propertyName == "specular")
        {
            if (!shadingFloatInRange(
                    valueNode, "specular", materialId, 0.0f, 1.0f, shading.specular, errorMessage))
            {
                return std::nullopt;
            }
        }
        else if (propertyName == "receives_wetness")
        {
            if (!shadingBoolValue(
                    valueNode, "receives_wetness", materialId, shading.receivesWetness, errorMessage))
            {
                return std::nullopt;
            }
        }
        else if (propertyName == "wetness_response")
        {
            if (!shadingFloatInRange(
                    valueNode,
                    "wetness_response",
                    materialId,
                    0.0f,
                    1.0f,
                    shading.wetnessResponse,
                    errorMessage))
            {
                return std::nullopt;
            }
        }
        else if (propertyName == "wet_roughness")
        {
            if (!shadingFloatInRange(
                    valueNode, "wet_roughness", materialId, 0.05f, 1.0f, shading.wetRoughness, errorMessage))
            {
                return std::nullopt;
            }
        }
        else if (propertyName == "wet_darkening")
        {
            if (!shadingFloatInRange(
                    valueNode, "wet_darkening", materialId, 0.0f, 1.0f, shading.wetDarkening, errorMessage))
            {
                return std::nullopt;
            }
        }
        else if (propertyName == "receives_puddles")
        {
            if (!shadingBoolValue(
                    valueNode, "receives_puddles", materialId, shading.receivesPuddles, errorMessage))
            {
                return std::nullopt;
            }
        }
        else if (propertyName == "fresnel_strength")
        {
            if (!shadingFloatInRange(
                    valueNode,
                    "fresnel_strength",
                    materialId,
                    0.0f,
                    1.0f,
                    shading.fresnelStrength,
                    errorMessage))
            {
                return std::nullopt;
            }
        }
        else if (propertyName == "emissive_strength")
        {
            if (!shadingFloatInRange(
                    valueNode,
                    "emissive_strength",
                    materialId,
                    0.0f,
                    4.0f,
                    shading.emissiveStrength,
                    errorMessage))
            {
                return std::nullopt;
            }
        }
        else if (propertyName == "emissive_color")
        {
            if (!valueNode.IsSequence() || valueNode.size() != 3)
            {
                errorMessage = "surface material '" + materialId
                    + "': shading.emissive_color must be a sequence of three numbers";
                return std::nullopt;
            }

            std::array<float, 3> color = {};

            for (size_t componentIndex = 0; componentIndex < 3; ++componentIndex)
            {
                const std::string colorPropertyName =
                    "emissive_color[" + std::to_string(componentIndex) + "]";

                if (!shadingFloatInRange(
                        valueNode[componentIndex],
                        colorPropertyName.c_str(),
                        materialId,
                        0.0f,
                        1.0f,
                        color[componentIndex],
                        errorMessage))
                {
                    return std::nullopt;
                }
            }

            shading.emissiveColor = color;
        }
        else
        {
            errorMessage = "surface material '" + materialId + "': unknown shading property '"
                + propertyName + "'";
            return std::nullopt;
        }
    }

    if (shading.receivesPuddles && !shading.receivesWetness)
    {
        errorMessage = "surface material '" + materialId
            + "': shading.receives_puddles requires receives_wetness";
        return std::nullopt;
    }

    if (shading.receivesPuddles && appliesToFaces && !appliesToTerrain)
    {
        errorMessage = "surface material '" + materialId
            + "': shading.receives_puddles is terrain-only and cannot be set on face-only materials";
        return std::nullopt;
    }

    return shading;
}
}

bool SurfaceMaterialTable::loadFromYaml(const std::string &yamlText, std::string &errorMessage)
{
    m_materials.clear();

    YAML::Node root;

    try
    {
        root = YAML::Load(yamlText);
    }
    catch (const std::exception &exception)
    {
        errorMessage = exception.what();
        return false;
    }

    const YAML::Node materialsNode = root["materials"];

    if (!materialsNode || !materialsNode.IsSequence())
    {
        errorMessage = "materials must be a YAML sequence";
        return false;
    }

    std::unordered_set<std::string> seenMaterialIds;

    for (const YAML::Node &materialNode : materialsNode)
    {
        if (!materialNode.IsMap())
        {
            continue;
        }

        SurfaceMaterialDefinition material = {};

        if (const YAML::Node idNode = materialNode["id"]; idNode && idNode.IsScalar())
        {
            material.id = toLowerCopy(idNode.as<std::string>());
        }

        if (material.id.empty())
        {
            continue;
        }

        if (!seenMaterialIds.insert(material.id).second)
        {
            errorMessage = "duplicate surface material id '" + material.id + "'";
            return false;
        }

        const YAML::Node semanticNode = materialNode["semantic"];

        if (!semanticNode || !semanticNode.IsScalar())
        {
            continue;
        }

        const std::optional<SurfaceMaterialSemantic> semantic = parseSemantic(semanticNode.as<std::string>());

        if (!semantic)
        {
            continue;
        }

        material.semantic = *semantic;

        const YAML::Node appliesToNode = materialNode["applies_to"];

        if (!appliesToNode || !appliesToNode.IsSequence())
        {
            continue;
        }

        for (const YAML::Node &entryNode : appliesToNode)
        {
            if (!entryNode.IsScalar())
            {
                continue;
            }

            const std::string scopeName = toLowerCopy(entryNode.as<std::string>());

            if (scopeName == "terrain")
            {
                material.appliesToTerrain = true;
            }
            else if (scopeName == "face")
            {
                material.appliesToFaces = true;
            }
        }

        material.terrainTransitionOverlay = materialNode["terrain_transition_overlay"].as<bool>(false);

        const YAML::Node matchNode = materialNode["match"];

        if (matchNode && matchNode.IsMap())
        {
            nodeAsStringSequence(matchNode["texture_names"], material.textureNames);
            nodeAsStringSequence(matchNode["texture_prefixes"], material.texturePrefixes);

            const YAML::Node faceAttributesNode = matchNode["required_face_attributes"];

            if (faceAttributesNode && faceAttributesNode.IsSequence())
            {
                for (const YAML::Node &attributeNode : faceAttributesNode)
                {
                    if (!attributeNode.IsScalar())
                    {
                        continue;
                    }

                    const std::optional<uint32_t> attributeBit =
                        parseFaceAttributeName(attributeNode.as<std::string>());

                    if (attributeBit)
                    {
                        material.requiredFaceAttributes |= *attributeBit;
                    }
                }
            }
        }

        const YAML::Node animationNode = materialNode["animation"];

        if (animationNode && animationNode.IsMap())
        {
            const YAML::Node framesNode = animationNode["frames"];

            if (framesNode && framesNode.IsSequence())
            {
                bool explicitFrameLengths = false;

                for (const YAML::Node &frameNode : framesNode)
                {
                    SurfaceAnimationFrame frame = {};

                    if (frameNode.IsScalar())
                    {
                        frame.textureName = frameNode.as<std::string>();
                    }
                    else if (frameNode.IsMap())
                    {
                        frame.textureName = frameTextureNameFromNode(frameNode);

                        if (const std::optional<uint32_t> frameLengthTicks = frameLengthTicksFromNode(frameNode))
                        {
                            frame.frameLengthTicks = *frameLengthTicks;
                            explicitFrameLengths = true;
                        }
                    }
                    else
                    {
                        continue;
                    }

                    if (!frame.textureName.empty())
                    {
                        material.animation.frames.push_back(std::move(frame));
                    }
                }

                const uint32_t animationLengthTicks = animationNode["animation_length_ticks"].as<uint32_t>(0);

                if (!material.animation.frames.empty())
                {
                    if (explicitFrameLengths)
                    {
                        normalizeExplicitFrameLengths(material.animation);
                    }
                    else
                    {
                        distributeEvenFrameLengths(material.animation, animationLengthTicks);
                    }
                }
            }
        }

        const YAML::Node shadingNode = materialNode["shading"];

        if (shadingNode)
        {
            std::optional<SurfaceMaterialShading> shading = parseShadingNode(
                shadingNode, material.id, material.appliesToTerrain, material.appliesToFaces, errorMessage);

            if (!shading)
            {
                return false;
            }

            material.shading = *shading;
        }

        m_materials.push_back(std::move(material));
    }

    return !m_materials.empty();
}

const SurfaceMaterialDefinition *SurfaceMaterialTable::findMatch(
    std::string_view textureName,
    uint32_t faceAttributes,
    bool isTerrain
) const
{
    const std::string normalizedTextureName = toLowerCopy(std::string(textureName));

    for (const SurfaceMaterialDefinition &material : m_materials)
    {
        if (isTerrain && !material.appliesToTerrain)
        {
            continue;
        }

        if (!isTerrain && !material.appliesToFaces)
        {
            continue;
        }

        if ((faceAttributes & material.requiredFaceAttributes) != material.requiredFaceAttributes)
        {
            continue;
        }

        bool hasTextureMatch = material.textureNames.empty() && material.texturePrefixes.empty();

        if (!hasTextureMatch)
        {
            hasTextureMatch = std::find(
                material.textureNames.begin(),
                material.textureNames.end(),
                normalizedTextureName) != material.textureNames.end();

            if (!hasTextureMatch)
            {
                for (const std::string &prefix : material.texturePrefixes)
                {
                    if (normalizedTextureName.starts_with(prefix))
                    {
                        hasTextureMatch = true;
                        break;
                    }
                }
            }
        }

        if (!hasTextureMatch)
        {
            continue;
        }

        return &material;
    }

    return nullptr;
}

size_t SurfaceMaterialTable::definitionCount() const
{
    return m_materials.size();
}

const SurfaceMaterialDefinition *SurfaceMaterialTable::definitionAt(size_t index) const
{
    if (index >= m_materials.size())
    {
        return nullptr;
    }

    return &m_materials[index];
}
} // namespace OpenYAMM::Game
