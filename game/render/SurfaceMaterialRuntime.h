#pragma once

#include "game/tables/SurfaceMaterialTable.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Game
{
struct ResolvedSurfaceMaterial
{
    std::string sourceId;
    SurfaceMaterialSemantic semantic = SurfaceMaterialSemantic::Generic;
    bool appliesToTerrain = false;
    bool appliesToFaces = false;
    uint32_t requiredFaceAttributes = 0;
    std::vector<std::string> textureNames;
    std::vector<std::string> texturePrefixes;
    float roughness = 0.90f;
    float specular = 0.0f;
    float effectiveWetnessResponse = 0.0f;
    float wetRoughness = 0.12f;
    float wetDarkening = 0.08f;
    bool receivesPuddles = false;
    float fresnelStrength = 0.0f;
    float emissiveStrength = 0.0f;
    std::array<float, 3> emissiveColor = {1.0f, 1.0f, 1.0f};
};

class SurfaceMaterialRuntimeSet
{
public:
    static constexpr uint16_t NeutralMaterialId = 0;
    static constexpr size_t MaxMaterialCount = 65535;

    bool buildFromTable(const SurfaceMaterialTable &table, std::string &errorMessage);
    uint16_t resolveMaterialId(std::string_view textureName, uint32_t faceAttributes, bool isTerrain) const;
    const ResolvedSurfaceMaterial &material(uint16_t materialId) const;

    bool empty() const;
    size_t size() const;
    bool hasDirectionalShading() const;

private:
    struct BindingKey
    {
        std::string textureName;
        uint32_t faceAttributes = 0;
        bool isTerrain = false;

        bool operator==(const BindingKey &other) const
        {
            return textureName == other.textureName
                && faceAttributes == other.faceAttributes
                && isTerrain == other.isTerrain;
        }
    };

    struct BindingKeyHash
    {
        size_t operator()(const BindingKey &key) const
        {
            const size_t textureHash = std::hash<std::string>{}(key.textureName);
            return textureHash ^ (std::hash<uint32_t>{}(key.faceAttributes) << 1)
                ^ (std::hash<bool>{}(key.isTerrain) << 2);
        }
    };

    uint16_t resolveUncached(
        const std::string &normalizedTextureName,
        uint32_t faceAttributes,
        bool isTerrain) const;

    // A default-constructed set is valid when the optional authoring table is absent.
    // Keep ID 0 materialized so every renderer can bind neutral state safely.
    std::vector<ResolvedSurfaceMaterial> m_materials = {ResolvedSurfaceMaterial{}};
    mutable std::unordered_map<BindingKey, uint16_t, BindingKeyHash> m_bindingCache;
};
} // namespace OpenYAMM::Game
