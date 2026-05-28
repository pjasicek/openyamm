#include "doctest/doctest.h"

#include "game/render/AnimatedModelRenderer.h"

#include <vector>

TEST_CASE("animated model renderer builds GPU skinned vertices from draw items")
{
    OpenYAMM::Game::AnimatedModelDrawItem drawItem = {};

    OpenYAMM::Game::AnimatedModelVertex first = {};
    first.position = {1.0f, 2.0f, 3.0f};
    first.normal = {0.0f, 0.0f, 1.0f};
    first.texcoord = {0.25f, 0.75f};
    first.joints = {0, 3, 5, 255};
    first.weights = {0.4f, 0.3f, 0.2f, 0.1f};
    drawItem.vertices.push_back(first);

    OpenYAMM::Game::AnimatedModelVertex second = {};
    second.position = {-1.0f, -2.0f, -3.0f};
    second.normal = {0.0f, 1.0f, 0.0f};
    second.texcoord = {1.0f, 0.0f};
    second.joints = {256, 4, 2, 1};
    second.weights = {1.0f, 0.0f, 0.0f, 0.0f};
    drawItem.vertices.push_back(second);

    const std::vector<OpenYAMM::Game::AnimatedModelSkinnedVertex> vertices =
        OpenYAMM::Game::AnimatedModelRenderer::buildSkinnedVertices(drawItem);

    REQUIRE(vertices.size() == 2);
    CHECK(vertices[0].x == doctest::Approx(1.0f));
    CHECK(vertices[0].y == doctest::Approx(2.0f));
    CHECK(vertices[0].z == doctest::Approx(3.0f));
    CHECK(vertices[0].normalZ == doctest::Approx(1.0f));
    CHECK(vertices[0].u == doctest::Approx(0.25f));
    CHECK(vertices[0].v == doctest::Approx(0.75f));
    CHECK(vertices[0].joints[0] == 0);
    CHECK(vertices[0].joints[1] == 3);
    CHECK(vertices[0].joints[2] == 5);
    CHECK(vertices[0].joints[3] == 255);
    CHECK(vertices[0].weights[0] == doctest::Approx(0.4f));
    CHECK(vertices[0].weights[1] == doctest::Approx(0.3f));
    CHECK(vertices[0].weights[2] == doctest::Approx(0.2f));
    CHECK(vertices[0].weights[3] == doctest::Approx(0.1f));
    CHECK(vertices[1].joints[0] == 255);
}

TEST_CASE("animated model renderer exposes expected bgfx skinned vertex layout")
{
    OpenYAMM::Game::AnimatedModelSkinnedVertex::init();

    const bgfx::VertexLayout &layout = OpenYAMM::Game::AnimatedModelSkinnedVertex::ms_layout;
    CHECK(layout.getStride() == sizeof(OpenYAMM::Game::AnimatedModelSkinnedVertex));
    CHECK(layout.has(bgfx::Attrib::Position));
    CHECK(layout.has(bgfx::Attrib::Normal));
    CHECK(layout.has(bgfx::Attrib::TexCoord0));
    CHECK(layout.has(bgfx::Attrib::Indices));
    CHECK(layout.has(bgfx::Attrib::Weight));
}

TEST_CASE("animated model renderer selects opaque, blended, and culling render states")
{
    OpenYAMM::Game::AnimatedModelDrawItem opaque = {};
    uint64_t state = OpenYAMM::Game::AnimatedModelRenderer::renderStateForDrawItem(opaque);
    CHECK((state & BGFX_STATE_WRITE_RGB) != 0);
    CHECK((state & BGFX_STATE_WRITE_Z) != 0);
    CHECK((state & BGFX_STATE_BLEND_ALPHA) == 0);
    CHECK((state & BGFX_STATE_CULL_CW) != 0);

    OpenYAMM::Game::AnimatedModelDrawItem alphaBlend = {};
    alphaBlend.alphaBlend = true;
    state = OpenYAMM::Game::AnimatedModelRenderer::renderStateForDrawItem(alphaBlend);
    CHECK((state & BGFX_STATE_BLEND_ALPHA) != 0);

    OpenYAMM::Game::AnimatedModelDrawItem doubleSided = {};
    doubleSided.doubleSided = true;
    state = OpenYAMM::Game::AnimatedModelRenderer::renderStateForDrawItem(doubleSided);
    CHECK((state & BGFX_STATE_CULL_CW) == 0);
}

TEST_CASE("animated model fog parameters default to disabled distance fog")
{
    const OpenYAMM::Game::AnimatedModelFogParameters fog = {};
    CHECK(fog.color[0] == doctest::Approx(0.0f));
    CHECK(fog.color[1] == doctest::Approx(0.0f));
    CHECK(fog.color[2] == doctest::Approx(0.0f));
    CHECK(fog.color[3] == doctest::Approx(1.0f));
    CHECK(fog.densities[0] == doctest::Approx(0.0f));
    CHECK(fog.densities[1] == doctest::Approx(0.0f));
    CHECK(fog.densities[2] == doctest::Approx(0.0f));
    CHECK(fog.distances[0] == doctest::Approx(1.0f));
    CHECK(fog.distances[1] == doctest::Approx(1.0f));
    CHECK(fog.distances[2] == doctest::Approx(2.0f));
}
