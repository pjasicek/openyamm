#include "game/render/SurfaceMaterialRuntime.h"

#include "game/StringUtils.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
bool resolvedMaterialMatches(
    const ResolvedSurfaceMaterial &material,
    const std::string &normalizedTextureName,
    uint32_t faceAttributes,
    bool isTerrain)
{
    if (isTerrain && !material.appliesToTerrain)
    {
        return false;
    }

    if (!isTerrain && !material.appliesToFaces)
    {
        return false;
    }

    if ((faceAttributes & material.requiredFaceAttributes) != material.requiredFaceAttributes)
    {
        return false;
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

    return hasTextureMatch;
}
}

bool SurfaceMaterialRuntimeSet::buildFromTable(const SurfaceMaterialTable &table, std::string &errorMessage)
{
    m_materials.clear();
    m_bindingCache.clear();

    ResolvedSurfaceMaterial neutralMaterial = {};
    neutralMaterial.sourceId = "";
    m_materials.push_back(neutralMaterial);

    const size_t definitionCount = table.definitionCount();

    if (definitionCount + 1 > MaxMaterialCount)
    {
        errorMessage = "surface material table has "
            + std::to_string(definitionCount)
            + " definitions, exceeding the resolved material capacity of "
            + std::to_string(MaxMaterialCount - 1);
        return false;
    }

    for (size_t definitionIndex = 0; definitionIndex < definitionCount; ++definitionIndex)
    {
        const SurfaceMaterialDefinition *pDefinition = table.definitionAt(definitionIndex);

        if (pDefinition == nullptr)
        {
            errorMessage = "surface material table definition "
                + std::to_string(definitionIndex)
                + " is unavailable";
            return false;
        }

        ResolvedSurfaceMaterial resolvedMaterial = {};
        resolvedMaterial.sourceId = pDefinition->id;
        resolvedMaterial.semantic = pDefinition->semantic;
        resolvedMaterial.appliesToTerrain = pDefinition->appliesToTerrain;
        resolvedMaterial.appliesToFaces = pDefinition->appliesToFaces;
        resolvedMaterial.requiredFaceAttributes = pDefinition->requiredFaceAttributes;
        resolvedMaterial.textureNames = pDefinition->textureNames;
        resolvedMaterial.texturePrefixes = pDefinition->texturePrefixes;

        if (pDefinition->shading)
        {
            const SurfaceMaterialShading &shading = *pDefinition->shading;
            resolvedMaterial.roughness = shading.roughness;
            resolvedMaterial.specular = shading.specular;
            resolvedMaterial.effectiveWetnessResponse =
                shading.receivesWetness ? shading.wetnessResponse : 0.0f;
            resolvedMaterial.wetRoughness = shading.wetRoughness;
            resolvedMaterial.wetDarkening = shading.wetDarkening;
            resolvedMaterial.receivesPuddles = shading.receivesPuddles;
            resolvedMaterial.fresnelStrength = shading.fresnelStrength;
            resolvedMaterial.emissiveStrength = shading.emissiveStrength;
            resolvedMaterial.emissiveColor = shading.emissiveColor;
            resolvedMaterial.materialMaskTexture = shading.materialMaskTexture;
        }

        m_materials.push_back(std::move(resolvedMaterial));
    }

    return true;
}

uint16_t SurfaceMaterialRuntimeSet::resolveMaterialId(
    std::string_view textureName,
    uint32_t faceAttributes,
    bool isTerrain) const
{
    if (m_materials.size() <= 1)
    {
        return NeutralMaterialId;
    }

    const std::string normalizedTextureName = toLowerCopy(std::string(textureName));
    const BindingKey bindingKey = {normalizedTextureName, faceAttributes, isTerrain};
    const auto cachedIterator = m_bindingCache.find(bindingKey);

    if (cachedIterator != m_bindingCache.end())
    {
        return cachedIterator->second;
    }

    const uint16_t materialId = resolveUncached(normalizedTextureName, faceAttributes, isTerrain);
    m_bindingCache.emplace(bindingKey, materialId);
    return materialId;
}

uint16_t SurfaceMaterialRuntimeSet::resolveUncached(
    const std::string &normalizedTextureName,
    uint32_t faceAttributes,
    bool isTerrain) const
{
    for (size_t materialIndex = 1; materialIndex < m_materials.size(); ++materialIndex)
    {
        if (resolvedMaterialMatches(
                m_materials[materialIndex], normalizedTextureName, faceAttributes, isTerrain))
        {
            return static_cast<uint16_t>(materialIndex);
        }
    }

    return NeutralMaterialId;
}

const ResolvedSurfaceMaterial &SurfaceMaterialRuntimeSet::material(uint16_t materialId) const
{
    if (materialId == NeutralMaterialId || materialId >= m_materials.size())
    {
        return m_materials[NeutralMaterialId];
    }

    return m_materials[materialId];
}

bool SurfaceMaterialRuntimeSet::empty() const
{
    return m_materials.size() <= 1;
}

size_t SurfaceMaterialRuntimeSet::size() const
{
    return m_materials.size();
}

bool SurfaceMaterialRuntimeSet::hasDirectionalShading() const
{
    for (size_t materialIndex = 1; materialIndex < m_materials.size(); ++materialIndex)
    {
        if (m_materials[materialIndex].specular > 0.0f || m_materials[materialIndex].fresnelStrength > 0.0f)
        {
            return true;
        }
    }

    return false;
}

namespace
{
uint8_t lutByte(float value, float scale)
{
    const float clamped = std::clamp(value * scale, 0.0f, 1.0f);
    return static_cast<uint8_t>(std::lround(clamped * 255.0f));
}

bool hasEffectiveTerrainShading(const ResolvedSurfaceMaterial &material)
{
    const bool hasEmissive = material.emissiveStrength > 0.0f
        && (material.emissiveColor[0] > 0.0f
            || material.emissiveColor[1] > 0.0f
            || material.emissiveColor[2] > 0.0f);
    const bool hasWetResponse = material.effectiveWetnessResponse > 0.0f
        && (material.wetDarkening > 0.0f || material.receivesPuddles);
    return material.specular > 0.0f || hasWetResponse || hasEmissive;
}
}

TerrainMaterialLookup buildTerrainMaterialLookup(
    const SurfaceMaterialRuntimeSet &surfaceMaterials,
    const std::array<uint16_t, TerrainMaterialLookup::LayerCount> &layerMaterialIds,
    const std::array<uint8_t, TerrainMaterialLookup::LayerCount> &layerTransitionFlags)
{
    TerrainMaterialLookup lookup = {};

    for (size_t layer = 0; layer < TerrainMaterialLookup::LayerCount; ++layer)
    {
        const bool transition = layerTransitionFlags[layer] != 0;
        const uint16_t materialId = transition ? SurfaceMaterialRuntimeSet::NeutralMaterialId : layerMaterialIds[layer];
        const ResolvedSurfaceMaterial &material = surfaceMaterials.material(materialId);
        const bool hasMaterial = materialId != SurfaceMaterialRuntimeSet::NeutralMaterialId
            && hasEffectiveTerrainShading(material);

        const auto setByte = [&](size_t row, size_t channel, uint8_t value)
        {
            lookup.bytes[TerrainMaterialLookup::texelByteOffset(layer, row, channel)] = value;
        };

        // Row 0: roughness, specular, effective wetness response, wet roughness.
        setByte(0, 0, lutByte(material.roughness, 1.0f));
        setByte(0, 1, lutByte(material.specular, 1.0f));
        setByte(0, 2, lutByte(material.effectiveWetnessResponse, 1.0f));
        setByte(0, 3, lutByte(material.wetRoughness, 1.0f));

        // Row 1: wet darkening, fresnel strength, puddles allowed, emissive strength / 4.
        setByte(1, 0, lutByte(material.wetDarkening, 1.0f));
        setByte(1, 1, lutByte(material.fresnelStrength, 1.0f));
        setByte(1, 2, material.receivesPuddles ? 255 : 0);
        setByte(1, 3, lutByte(material.emissiveStrength, 0.25f));

        // Row 2: emissive RGB, reserved zero.
        setByte(2, 0, lutByte(material.emissiveColor[0], 1.0f));
        setByte(2, 1, lutByte(material.emissiveColor[1], 1.0f));
        setByte(2, 2, lutByte(material.emissiveColor[2], 1.0f));
        setByte(2, 3, 0);

        if (hasMaterial)
        {
            lookup.anyMaterialLayer = true;

            if (material.emissiveStrength > 0.0f
                && (material.emissiveColor[0] > 0.0f
                    || material.emissiveColor[1] > 0.0f
                    || material.emissiveColor[2] > 0.0f))
            {
                lookup.anyEmissiveLayer = true;
            }
        }
    }

    return lookup;
}
} // namespace OpenYAMM::Game
