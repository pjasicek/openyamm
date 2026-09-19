#pragma once

#include "game/tables/SurfaceAnimation.h"

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace OpenYAMM::Game
{
enum class SurfaceMaterialSemantic
{
    Generic,
    GenericAnimated,
    Water,
    Lava,
};

struct SurfaceMaterialShading
{
    float roughness = 0.90f;
    float specular = 0.0f;
    bool receivesWetness = false;
    float wetnessResponse = 0.0f;
    float wetRoughness = 0.12f;
    float wetDarkening = 0.08f;
    bool receivesPuddles = false;
    float fresnelStrength = 0.0f;
    float emissiveStrength = 0.0f;
    std::array<float, 3> emissiveColor = {1.0f, 1.0f, 1.0f};
    // Optional packed facade mask: mount-relative image path sampled with the diffuse UV.
    // R selects shine, G multiplies wetness response, B multiplies emissive; empty = unmasked.
    std::string materialMaskTexture;
};

struct SurfaceMaterialDefinition
{
    std::string id;
    SurfaceMaterialSemantic semantic = SurfaceMaterialSemantic::GenericAnimated;
    bool appliesToTerrain = false;
    bool appliesToFaces = false;
    bool terrainTransitionOverlay = false;
    std::vector<std::string> textureNames;
    std::vector<std::string> texturePrefixes;
    uint32_t requiredFaceAttributes = 0;
    SurfaceAnimationSequence animation;
    std::optional<SurfaceMaterialShading> shading;
};

class SurfaceMaterialTable
{
public:
    bool loadFromYaml(const std::string &yamlText, std::string &errorMessage);
    const SurfaceMaterialDefinition *findMatch(
        std::string_view textureName,
        uint32_t faceAttributes,
        bool isTerrain) const;

    size_t definitionCount() const;
    const SurfaceMaterialDefinition *definitionAt(size_t index) const;

private:
    std::vector<SurfaceMaterialDefinition> m_materials;
};
} // namespace OpenYAMM::Game
