#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace OpenYAMM::Game
{
// The HUD's draw list (devdocs/HUD_RENDERING.md): everything the HUD draws in a frame, as vertices in the order it
// was drawn. Neighbours that share a texture, a sampler and a clip rectangle become one draw; nothing is reordered
// and nothing is kept between frames.

// Texels with alpha at or below a vertex's cut are dropped.
inline constexpr float HudAlphaCutNone = -1.0f;
// Untinted images drop their faintest texels, as the textured program the HUD used before did; its art is tuned to it.
inline constexpr float HudAlphaCutUntinted = 0.1f;

struct HudVertex
{
    float x = 0.0f;
    float y = 0.0f;
    float alphaCut = HudAlphaCutNone;
    float u = 0.0f;
    float v = 0.0f;
    // Multiplies the texture.
    uint32_t colorAbgr = 0xffffffffu;
};

// What has to be equal for two primitives to share a draw.
struct HudDrawState
{
    uint16_t textureIndex = UINT16_MAX;
    uint32_t samplerFlags = 0;
    bool clipped = false;
    uint16_t scissorX = 0;
    uint16_t scissorY = 0;
    uint16_t scissorWidth = 0;
    uint16_t scissorHeight = 0;

    bool operator==(const HudDrawState &other) const = default;
};

struct HudDrawCommand
{
    HudDrawState state;
    uint32_t firstVertex = 0;
    uint32_t vertexCount = 0;
    uint32_t firstIndex = 0;
    uint32_t indexCount = 0;
};

class HudDrawList
{
public:
    // A command's vertices are addressed by 16-bit indices.
    static constexpr uint32_t MaxCommandVertices = 65536;

    // Room for one primitive. Its indices count from the command's first vertex: add firstVertex to each.
    struct Primitive
    {
        HudVertex *pVertices = nullptr;
        uint16_t *pIndices = nullptr;
        uint16_t firstVertex = 0;
    };

    // The pointers hold until the next add. A primitive larger than a command can address is refused (null pointers).
    Primitive add(const HudDrawState &state, uint32_t vertexCount, uint32_t indexCount);

    // Two triangles over four corners given in order round the quad.
    void addQuad(const HudDrawState &state, const std::array<HudVertex, 4> &corners);

    void clear();

    bool empty() const
    {
        return m_commands.empty();
    }

    const std::vector<HudVertex> &vertices() const
    {
        return m_vertices;
    }

    const std::vector<uint16_t> &indices() const
    {
        return m_indices;
    }

    const std::vector<HudDrawCommand> &commands() const
    {
        return m_commands;
    }

    // Primitives added since the last clear.
    size_t primitiveCount() const
    {
        return m_primitiveCount;
    }

private:
    std::vector<HudVertex> m_vertices;
    std::vector<uint16_t> m_indices;
    std::vector<HudDrawCommand> m_commands;
    size_t m_primitiveCount = 0;
};
}
