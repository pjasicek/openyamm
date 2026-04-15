#include "game/tables/SurfaceMaterialTable.h"

#include "game/FaceEnums.h"
#include "game/StringUtils.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cctype>
#include <exception>

namespace OpenYAMM::Game
{
namespace
{
std::optional<SurfaceMaterialSemantic> parseSemantic(const std::string &value)
{
    const std::string normalizedValue = toLowerCopy(value);

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
                for (const YAML::Node &frameNode : framesNode)
                {
                    if (!frameNode.IsScalar())
                    {
                        continue;
                    }

                    SurfaceAnimationFrame frame = {};
                    frame.textureName = frameNode.as<std::string>();
                    material.animation.frames.push_back(std::move(frame));
                }
            }

            const uint32_t animationLengthTicks = animationNode["animation_length_ticks"].as<uint32_t>(0);

            if (!material.animation.frames.empty())
            {
                distributeEvenFrameLengths(material.animation, animationLengthTicks);
            }
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
} // namespace OpenYAMM::Game
