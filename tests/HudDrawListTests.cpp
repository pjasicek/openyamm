#include "game/ui/HudDrawList.h"

#include <doctest/doctest.h>

#include <array>

using OpenYAMM::Game::HudDrawCommand;
using OpenYAMM::Game::HudDrawList;
using OpenYAMM::Game::HudDrawState;
using OpenYAMM::Game::HudVertex;

namespace
{
HudDrawState textureState(uint16_t texture)
{
    HudDrawState state;
    state.textureIndex = texture;
    return state;
}

std::array<HudVertex, 4> quadAt(float x)
{
    return {{{x, 0.0f}, {x + 1.0f, 0.0f}, {x + 1.0f, 1.0f}, {x, 1.0f}}};
}
}

TEST_CASE("HUD draw list merges neighbours of one state into one draw")
{
    HudDrawList list;
    list.addQuad(textureState(7), quadAt(0.0f));
    list.addQuad(textureState(7), quadAt(10.0f));
    list.addQuad(textureState(7), quadAt(20.0f));
    REQUIRE(list.commands().size() == 1);
    CHECK(list.commands()[0].vertexCount == 12);
    CHECK(list.commands()[0].indexCount == 18);
    CHECK(list.primitiveCount() == 3);
    // Indices count from the command's first vertex.
    CHECK(list.indices()[6] == 4);
    CHECK(list.indices()[17] == 11);
    CHECK(list.vertices()[8].x == 20.0f);
}

TEST_CASE("HUD draw list never reorders: a state between two equal ones keeps three draws")
{
    HudDrawList list;
    list.addQuad(textureState(1), quadAt(0.0f));
    list.addQuad(textureState(2), quadAt(1.0f));
    list.addQuad(textureState(1), quadAt(2.0f));
    REQUIRE(list.commands().size() == 3);
    CHECK(list.commands()[0].state.textureIndex == 1);
    CHECK(list.commands()[1].state.textureIndex == 2);
    CHECK(list.commands()[2].state.textureIndex == 1);
    CHECK(list.commands()[2].firstVertex == 8);
    CHECK(list.commands()[2].firstIndex == 12);
    // The third quad's indices start again from zero: they are relative to its own command.
    CHECK(list.indices()[12] == 0);
}

TEST_CASE("HUD draw list separates samplers and clip rectangles")
{
    HudDrawList list;
    HudDrawState state = textureState(3);
    list.addQuad(state, quadAt(0.0f));
    state.samplerFlags = 5;
    list.addQuad(state, quadAt(1.0f));
    state.clipped = true;
    state.scissorWidth = 10;
    state.scissorHeight = 10;
    list.addQuad(state, quadAt(2.0f));
    list.addQuad(state, quadAt(3.0f));
    state.scissorX = 1;
    list.addQuad(state, quadAt(4.0f));
    CHECK(list.commands().size() == 4);
}

TEST_CASE("HUD draw list starts a new draw when 16-bit indices run out")
{
    HudDrawList list;
    const HudDrawState state = textureState(1);

    for (uint32_t quad = 0; quad < HudDrawList::MaxCommandVertices / 4 + 1; ++quad)
    {
        list.addQuad(state, quadAt(0.0f));
    }

    REQUIRE(list.commands().size() == 2);
    CHECK(list.commands()[0].vertexCount == HudDrawList::MaxCommandVertices);
    CHECK(list.commands()[1].vertexCount == 4);
    CHECK(list.indices()[list.commands()[1].firstIndex] == 0);
    CHECK(list.indices()[list.commands()[1].firstIndex - 1] == 65535);
}

TEST_CASE("HUD draw list refuses empty and oversized primitives and clears to nothing")
{
    HudDrawList list;
    CHECK(list.add(textureState(1), 0, 3).pVertices == nullptr);
    CHECK(list.add(textureState(1), 3, 0).pVertices == nullptr);
    CHECK(list.add(textureState(1), HudDrawList::MaxCommandVertices + 1, 3).pVertices == nullptr);
    CHECK(list.empty());
    const HudDrawList::Primitive fan = list.add(textureState(1), 5, 9);
    REQUIRE(fan.pVertices != nullptr);
    CHECK(fan.firstVertex == 0);
    CHECK_FALSE(list.empty());
    list.clear();
    CHECK(list.empty());
    CHECK(list.vertices().empty());
    CHECK(list.indices().empty());
    CHECK(list.primitiveCount() == 0);
}
