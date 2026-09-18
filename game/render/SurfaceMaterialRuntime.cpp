#include "game/render/SurfaceMaterialRuntime.h"

#include "game/StringUtils.h"

#include <algorithm>

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
} // namespace OpenYAMM::Game
