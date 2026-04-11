#pragma once

#include "game/tables/SurfaceAnimation.h"

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace OpenYAMM::Game
{
enum class SurfaceMaterialSemantic
{
    GenericAnimated,
    Water,
    Lava,
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
};

class SurfaceMaterialTable
{
public:
    bool loadFromYaml(const std::string &yamlText, std::string &errorMessage);
    const SurfaceMaterialDefinition *findMatch(
        std::string_view textureName,
        uint32_t faceAttributes,
        bool isTerrain) const;

private:
    std::vector<SurfaceMaterialDefinition> m_materials;
};
} // namespace OpenYAMM::Game
