#include "game/tables/LiquidTable.h"

#include "game/FaceEnums.h"
#include "game/StringUtils.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cmath>
#include <exception>
#include <limits>
#include <optional>

namespace OpenYAMM::Game
{
namespace
{
std::optional<LiquidKind> parseKind(const std::string &value)
{
    const std::string normalizedValue = toLowerCopy(value);
    if (normalizedValue == "water")
    {
        return LiquidKind::Water;
    }
    if (normalizedValue == "tar")
    {
        return LiquidKind::Tar;
    }
    if (normalizedValue == "lava")
    {
        return LiquidKind::Lava;
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
    return std::nullopt;
}

bool readStrings(const YAML::Node &node, std::vector<std::string> &values)
{
    values.clear();
    if (!node)
    {
        return true;
    }
    if (!node.IsSequence())
    {
        return false;
    }
    for (const YAML::Node &entry : node)
    {
        if (!entry.IsScalar())
        {
            return false;
        }
        values.push_back(toLowerCopy(entry.as<std::string>()));
    }
    return true;
}

std::optional<uint32_t> readColorAbgr(const YAML::Node &node)
{
    if (!node || !node.IsSequence() || node.size() != 3)
    {
        return std::nullopt;
    }
    uint32_t color = 0xff000000u;
    for (size_t channel = 0; channel < 3; ++channel)
    {
        const int value = node[channel].as<int>(-1);
        if (value < 0 || value > 255)
        {
            return std::nullopt;
        }
        color |= uint32_t(value) << (8 * channel);
    }
    return color;
}
}

bool LiquidTable::loadFromYaml(const std::string &yamlText, std::string &errorMessage)
{
    m_liquids.clear();
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

    const YAML::Node liquidsNode = root["liquids"];
    if (!liquidsNode || !liquidsNode.IsSequence())
    {
        errorMessage = "liquids must be a YAML sequence";
        return false;
    }

    for (const YAML::Node &liquidNode : liquidsNode)
    {
        LiquidDefinition liquid = {};
        liquid.id = liquidNode.IsMap() && liquidNode["id"].IsScalar()
            ? toLowerCopy(liquidNode["id"].as<std::string>()) : std::string();
        const std::string context = "liquid '" + liquid.id + "'";
        if (liquid.id.empty())
        {
            errorMessage = "every liquid needs an id";
            return false;
        }
        const std::optional<LiquidKind> kind = liquidNode["kind"].IsScalar()
            ? parseKind(liquidNode["kind"].as<std::string>()) : std::nullopt;
        if (!kind)
        {
            errorMessage = context + ": kind must be water, tar or lava";
            return false;
        }
        liquid.kind = *kind;
        const std::optional<uint32_t> color = readColorAbgr(liquidNode["color"]);
        if (!color)
        {
            errorMessage = context + ": color must be [red, green, blue] in 0-255";
            return false;
        }
        liquid.colorAbgr = *color;

        std::vector<std::string> scopes;
        if (!readStrings(liquidNode["applies_to"], scopes) || scopes.empty())
        {
            errorMessage = context + ": applies_to must list terrain and/or face";
            return false;
        }
        for (const std::string &scope : scopes)
        {
            if (scope == "terrain")
            {
                liquid.appliesToTerrain = true;
            }
            else if (scope == "face")
            {
                liquid.appliesToFaces = true;
            }
            else
            {
                errorMessage = context + ": unknown applies_to scope '" + scope + "'";
                return false;
            }
        }
        liquid.terrainTransitionOverlay = liquidNode["terrain_transition_overlay"].as<bool>(false);

        if (!readStrings(liquidNode["worlds"], liquid.worlds))
        {
            errorMessage = context + ": worlds must be a list of world ids";
            return false;
        }

        liquid.reflects = liquidNode["reflections"].as<bool>(true);

        if (const YAML::Node depthNode = liquidNode["depth"]; depthNode)
        {
            const std::string depth = depthNode.IsScalar() ? toLowerCopy(depthNode.as<std::string>()) : std::string();

            if (depth != "deep" && depth != "shallow")
            {
                errorMessage = context + ": depth must be deep or shallow";
                return false;
            }

            liquid.shallow = depth == "shallow";
        }

        liquid.wadeSpeed = liquidNode["wade_speed"].as<float>(1.0f);

        if (!(liquid.wadeSpeed > 0.0f && liquid.wadeSpeed <= 1.0f) || (liquid.wadeSpeed < 1.0f && !liquid.shallow))
        {
            errorMessage = context + ": wade_speed must lie in (0, 1] and needs depth: shallow";
            return false;
        }

        if (const YAML::Node opacityNode = liquidNode["opacity"]; opacityNode)
        {
            liquid.opacity = opacityNode.as<float>(std::numeric_limits<float>::quiet_NaN());
        }

        if (!(liquid.opacity > 0.0f && liquid.opacity <= 1.0f))
        {
            errorMessage = context + ": opacity must lie in (0, 1]";
            return false;
        }

        if (liquid.opacity < 1.0f && (liquid.kind == LiquidKind::Lava || liquid.appliesToTerrain))
        {
            errorMessage = context + ": opacity below 1 needs a water or tar liquid of faces only";
            return false;
        }

        const YAML::Node matchNode = liquidNode["match"];
        std::vector<std::string> attributes;
        if (!matchNode || !matchNode.IsMap()
            || !readStrings(matchNode["texture_names"], liquid.textureNames)
            || !readStrings(matchNode["texture_prefixes"], liquid.texturePrefixes)
            || !readStrings(matchNode["required_face_attributes"], attributes)
            || (liquid.textureNames.empty() && liquid.texturePrefixes.empty()))
        {
            errorMessage = context + ": match needs texture_names and/or texture_prefixes";
            return false;
        }
        for (const std::string &attribute : attributes)
        {
            const std::optional<uint32_t> bit = parseFaceAttributeName(attribute);
            if (!bit)
            {
                errorMessage = context + ": unknown face attribute '" + attribute + "'";
                return false;
            }
            liquid.requiredFaceAttributes |= *bit;
        }
        m_liquids.push_back(std::move(liquid));
    }
    return true;
}

uint32_t liquidFaceColorAbgr(const LiquidDefinition &liquid)
{
    // At least 1: a zero tint would read as no liquid at all.
    const uint32_t alpha = uint32_t(std::clamp(std::lround(liquid.opacity * 255.0f), 1L, 255L));
    return (liquid.colorAbgr & 0x00ffffffu) | (alpha << 24);
}

LiquidTable LiquidTable::forWorld(std::string_view worldId) const
{
    const std::string normalizedWorldId = toLowerCopy(std::string(worldId));
    LiquidTable table;

    for (const LiquidDefinition &liquid : m_liquids)
    {
        if (std::find(liquid.worlds.begin(), liquid.worlds.end(), normalizedWorldId) != liquid.worlds.end())
        {
            table.m_liquids.push_back(liquid);
        }
    }

    for (const LiquidDefinition &liquid : m_liquids)
    {
        if (liquid.worlds.empty())
        {
            table.m_liquids.push_back(liquid);
        }
    }

    return table;
}

bool LiquidTable::hasShallowLiquids() const
{
    return std::any_of(m_liquids.begin(), m_liquids.end(), [](const LiquidDefinition &liquid) { return liquid.shallow; });
}

const LiquidDefinition *LiquidTable::findMatch(std::string_view textureName, uint32_t faceAttributes,
    bool isTerrain) const
{
    const std::string normalizedTextureName = toLowerCopy(std::string(textureName));
    for (const LiquidDefinition &liquid : m_liquids)
    {
        if ((isTerrain ? !liquid.appliesToTerrain : !liquid.appliesToFaces)
            || (faceAttributes & liquid.requiredFaceAttributes) != liquid.requiredFaceAttributes)
        {
            continue;
        }
        if (std::find(liquid.textureNames.begin(), liquid.textureNames.end(), normalizedTextureName)
                != liquid.textureNames.end()
            || std::any_of(liquid.texturePrefixes.begin(), liquid.texturePrefixes.end(),
                [&](const std::string &prefix) { return normalizedTextureName.starts_with(prefix); }))
        {
            return &liquid;
        }
    }
    return nullptr;
}
}
