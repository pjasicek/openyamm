#include "doctest/doctest.h"

#include "game/render/BillboardGeometry.h"
#include "game/render/SpriteAtlasCache.h"
#include "game/render/ViewFrustum.h"

#include <array>
#include <random>

using namespace OpenYAMM::Game;

namespace
{
template<size_t Count>
bool outsideClipPlane(const std::array<bx::Vec3, Count> &corners, const float *pMatrix, bool homogeneousDepth)
{
    std::array<bool, 6> allOutside = {true, true, true, true, true, true};
    for (const bx::Vec3 &point : corners)
    {
        std::array<float, 4> clip = {};
        for (size_t row = 0; row < 4; ++row)
        {
            clip[row] = point.x * pMatrix[row] + point.y * pMatrix[4 + row]
                + point.z * pMatrix[8 + row] + pMatrix[12 + row];
        }
        const std::array<bool, 6> outside = {
            clip[0] < -clip[3], clip[0] > clip[3], clip[1] < -clip[3], clip[1] > clip[3],
            clip[2] < (homogeneousDepth ? -clip[3] : 0.0f), clip[2] > clip[3]
        };
        for (size_t plane = 0; plane < 6; ++plane)
        {
            allOutside[plane] = allOutside[plane] && outside[plane];
        }
    }
    for (bool outside : allOutside)
    {
        if (outside)
        {
            return true;
        }
    }
    return false;
}
}

TEST_CASE("view frustum retains intersections and rejects all six outside regions")
{
    for (bool homogeneousDepth : {false, true})
    {
        float view[16];
        float projection[16];
        bx::mtxIdentity(view);
        bx::mtxProj(projection, 90.0f, 1.0f, 10.0f, 100.0f, homogeneousDepth, bx::Handedness::Right);
        const ViewFrustum frustum(view, projection, homogeneousDepth);
        CHECK(frustum.intersectsBounds({-1, -1, -21}, {1, 1, -19}));
        CHECK(frustum.intersectsBounds({-2, -2, -11}, {2, 2, 5})); // Crosses near plane/camera.
        CHECK(frustum.intersectsBounds({19, -1, -21}, {30, 1, -19})); // Center is outside.
        CHECK(frustum.intersectsBounds({-200, -200, -200}, {200, 200, 200})); // Encloses camera.
        CHECK(frustum.intersectsBounds({-1, -1, -10}, {1, 1, -9})); // Touches near plane.
        CHECK(frustum.intersectsBounds({-1, -1, -9.9f}, {1, 1, -9})); // Numeric margin.
        for (const bx::Vec3 &center : std::array<bx::Vec3, 6>{{
            {-40, 0, -20}, {40, 0, -20}, {0, -40, -20}, {0, 40, -20}, {0, 0, -5}, {0, 0, -110}}})
        {
            CHECK_FALSE(frustum.intersectsBounds(bx::sub(center, {1, 1, 1}), bx::add(center, {1, 1, 1})));
            CHECK_FALSE(frustum.intersectsQuad(center, {1, 0, 0}, {0, 1, 0}));
        }
    }
}

TEST_CASE("view frustum rejection agrees with clip-space corners at outdoor coordinates and camera rotations")
{
    std::mt19937 random(821);
    std::uniform_real_distribution<float> offset(-20000.0f, 20000.0f);
    std::uniform_real_distribution<float> extent(1.0f, 2000.0f);
    for (bool homogeneousDepth : {false, true})
    {
        for (float aspect : {0.6f, 1.7777778f})
        {
            for (float yaw : {0.0f, 1.57f, 2.6529f, 4.7f})
            {
                const bx::Vec3 eye = {-9728, -11319, 161};
                const bx::Vec3 forward = {std::cos(yaw) * 0.8f, std::sin(yaw) * 0.8f, -0.6f};
                float view[16];
                float projection[16];
                float matrix[16];
                bx::mtxLookAt(view, eye, bx::add(eye, forward), {0, 0, 1}, bx::Handedness::Right);
                bx::mtxProj(projection, 65.0f, aspect, 10.0f, 18000.0f, homogeneousDepth, bx::Handedness::Right);
                bx::mtxMul(matrix, view, projection);
                const ViewFrustum frustum(view, projection, homogeneousDepth);
                const bx::Vec3 cameraRight = {view[0], view[4], view[8]};
                const bx::Vec3 cameraUp = {view[1], view[5], view[9]};
                int rejectedBoxes = 0;
                int rejectedQuads = 0;
                for (size_t sample = 0; sample < 1000; ++sample)
                {
                    const bx::Vec3 center = bx::add(eye, {offset(random), offset(random), offset(random)});
                    const bx::Vec3 halfSize = {extent(random), extent(random), extent(random)};
                    const bx::Vec3 min = bx::sub(center, halfSize);
                    const bx::Vec3 max = bx::add(center, halfSize);
                    std::array<bx::Vec3, 8> corners = {min, min, min, min, min, min, min, min};
                    for (size_t corner = 0; corner < corners.size(); ++corner)
                    {
                        corners[corner] = {corner & 1 ? max.x : min.x, corner & 2 ? max.y : min.y,
                            corner & 4 ? max.z : min.z};
                    }
                    if (!frustum.intersectsBounds(min, max))
                    {
                        ++rejectedBoxes;
                        CHECK(outsideClipPlane(corners, matrix, homogeneousDepth));
                    }
                    const BillboardQuad quad = billboardQuad(center, cameraRight, cameraUp, halfSize.x, halfSize.y);
                    std::array<bx::Vec3, 4> quadCorners = {center, center, center, center};
                    for (size_t corner = 0; corner < quadCorners.size(); ++corner)
                    {
                        quadCorners[corner] = bx::add(center, bx::add(
                            bx::mul(quad.right, corner & 1 ? 1.0f : -1.0f),
                            bx::mul(quad.up, corner & 2 ? 1.0f : -1.0f)));
                    }
                    if (!frustum.intersectsQuad(quad.center, quad.right, quad.up))
                    {
                        ++rejectedQuads;
                        CHECK(outsideClipPlane(quadCorners, matrix, homogeneousDepth));
                    }
                }
                CHECK(rejectedBoxes > 500);
                CHECK(rejectedQuads > 500);
            }
        }
    }
}

TEST_CASE("view frustum uses cropped sprite placement and mirroring with a tilted camera")
{
    const bx::Vec3 eye = {-9728, -11319, 161};
    const bx::Vec3 forward = {0, 0.8f, -0.6f};
    float view[16];
    float projection[16];
    bx::mtxLookAt(view, eye, bx::add(eye, forward), {0, 0, 1}, bx::Handedness::Right);
    bx::mtxProj(projection, 90.0f, 1.0f, 10.0f, 1000.0f, true, bx::Handedness::Right);
    const ViewFrustum frustum(view, projection, true);
    const bx::Vec3 cameraRight = {view[0], view[4], view[8]};
    const bx::Vec3 cameraUp = {view[1], view[5], view[9]};
    const bx::Vec3 anchor = bx::add(eye, bx::add(bx::mul(forward, 100.0f), bx::mul(cameraRight, 125.0f)));
    SpriteBillboardTexture texture;
    texture.width = 20;
    texture.height = 40;
    texture.offsetX = -20;
    texture.offsetY = -10;
    for (bool mirrored : {false, true})
    {
        const float scale = 2.0f;
        const bx::Vec3 center = spriteBillboardCenter(
            anchor.x, anchor.y, anchor.z, cameraRight, cameraUp, texture, scale, mirrored);
        const BillboardQuad quad = billboardQuad(
            center, cameraRight, cameraUp, texture.width * scale, texture.height * scale);
        CHECK(frustum.intersectsQuad(quad.center, quad.right, quad.up) == !mirrored);
        CHECK(bx::dot(bx::sub(center, anchor), cameraRight) == doctest::Approx(mirrored ? 40 : -40));
        CHECK(bx::dot(bx::sub(center, anchor), cameraUp) == doctest::Approx(20).epsilon(0.001));
    }
}
