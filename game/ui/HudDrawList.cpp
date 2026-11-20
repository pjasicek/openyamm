#include "game/ui/HudDrawList.h"

namespace OpenYAMM::Game
{
HudDrawList::Primitive HudDrawList::add(const HudDrawState &state, uint32_t vertexCount, uint32_t indexCount)
{
    if (vertexCount == 0 || indexCount == 0 || vertexCount > MaxCommandVertices)
    {
        return {};
    }

    if (m_commands.empty() || !(m_commands.back().state == state)
        || m_commands.back().vertexCount + vertexCount > MaxCommandVertices)
    {
        HudDrawCommand command;
        command.state = state;
        command.firstVertex = uint32_t(m_vertices.size());
        command.firstIndex = uint32_t(m_indices.size());
        m_commands.push_back(command);
    }

    HudDrawCommand &command = m_commands.back();
    Primitive primitive;
    primitive.firstVertex = uint16_t(command.vertexCount);
    m_vertices.resize(m_vertices.size() + vertexCount);
    m_indices.resize(m_indices.size() + indexCount);
    primitive.pVertices = m_vertices.data() + command.firstVertex + command.vertexCount;
    primitive.pIndices = m_indices.data() + command.firstIndex + command.indexCount;
    command.vertexCount += vertexCount;
    command.indexCount += indexCount;
    ++m_primitiveCount;
    return primitive;
}

void HudDrawList::addQuad(const HudDrawState &state, const std::array<HudVertex, 4> &corners)
{
    const Primitive primitive = add(state, 4, 6);

    if (primitive.pVertices == nullptr)
    {
        return;
    }

    for (size_t corner = 0; corner < corners.size(); ++corner)
    {
        primitive.pVertices[corner] = corners[corner];
    }

    constexpr std::array<uint16_t, 6> Corners = {{0, 1, 2, 0, 2, 3}};

    for (size_t index = 0; index < Corners.size(); ++index)
    {
        primitive.pIndices[index] = uint16_t(primitive.firstVertex + Corners[index]);
    }
}

void HudDrawList::clear()
{
    m_vertices.clear();
    m_indices.clear();
    m_commands.clear();
    m_primitiveCount = 0;
}
}
