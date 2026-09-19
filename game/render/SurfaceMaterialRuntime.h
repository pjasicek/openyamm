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
    // Face-only packed facade mask (mount-relative image path); empty on neutral/terrain rows.
    std::string materialMaskTexture;
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

// Packs the per-layer terrain material contract into a 256x3 RGBA8 lookup table plus the
// map-level flags the shader needs to skip work. Rows: 0 = roughness, specular, effective
// wetness response, wet roughness; 1 = wet darkening, fresnel strength, puddles allowed,
// emissive strength / 4; 2 = emissive RGB, reserved zero. Values are linear data, not color.
struct TerrainMaterialLookup
{
    static constexpr size_t LayerCount = 256;
    static constexpr size_t RowCount = 3;
    static constexpr size_t BytesPerTexel = 4;
    static constexpr size_t ByteCount = LayerCount * RowCount * BytesPerTexel;

    static constexpr size_t texelByteOffset(size_t layer, size_t row, size_t channel = 0)
    {
        return (row * LayerCount + layer) * BytesPerTexel + channel;
    }

    // bgfx texture uploads use row-major storage: all 256 layer texels for row 0,
    // followed by all layer texels for rows 1 and 2.
    std::array<uint8_t, ByteCount> bytes = {};
    bool anyMaterialLayer = false;
    bool anyEmissiveLayer = false;
};

// Composited shore/transition layers stay neutral: their land and water pixels cannot be
// separated by a scalar per-layer entry.
TerrainMaterialLookup buildTerrainMaterialLookup(
    const SurfaceMaterialRuntimeSet &surfaceMaterials,
    const std::array<uint16_t, TerrainMaterialLookup::LayerCount> &layerMaterialIds,
    const std::array<uint8_t, TerrainMaterialLookup::LayerCount> &layerTransitionFlags);
} // namespace OpenYAMM::Game
