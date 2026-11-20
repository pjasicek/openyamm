#pragma once

#include "engine/models/ModelAsset.h"

#include <array>

namespace OpenYAMM::Game
{
// The wall a wall-mounted decoration hangs on: the nearest point of the wall face (map x, y) and the face's
// horizontal unit normal pointing from the wall toward the decoration.
struct DecorationWallContact
{
    std::array<float, 2> point = {};
    std::array<float, 2> normal = {};
};

// A camera-facing card corner (asset space p) in world space, turned toward the viewer about the vertical axis through
// pivot (asset space: the model origin, or a "card" billboard's own centre) as modelStaticPosition (model_static.sh)
// turns it toward the camera: its offset across the model and its height stay.
std::array<float, 3> facingCardCorner(const Engine::ModelMatrix &placement, const std::array<float, 3> &p,
    const std::array<float, 3> &viewer, const std::array<float, 3> &pivot = {});

// Yaw (radians, for Engine::gltfModelPlacement) that turns a model's front (asset +z) toward a horizontal direction.
float yawFacing(const std::array<float, 2> &direction);

// A wall-mounted placement: the model faces away from the wall (asset +z along the wall normal) with its back
// (the asset bounds' minimum z, scaled) on the wall face, at height z.
Engine::ModelMatrix wallMountedPlacement(const DecorationWallContact &wall, float backZ, float z, float scale);

// A placement swung by angleRadians about the asset x axis through the asset point pivot (a hanging chandelier or
// cage swinging from its top).
Engine::ModelMatrix swungPlacement(const Engine::ModelMatrix &placement, const std::array<float, 3> &pivot,
    float angleRadians);

// A placement turned by angleRadians about the asset z axis (the model's front axis: a wheel's axle) through the asset
// point pivot (its x and y).
Engine::ModelMatrix turnedPlacement(const Engine::ModelMatrix &placement, const std::array<float, 3> &pivot,
    float angleRadians);

// The angle a one-shot turn of turnRadians over durationSeconds still has to go, elapsedSeconds after it began: it
// eases in and out and reaches 0 at the end, where the model rests in its own pose.
float turnRemaining(float turnRadians, float durationSeconds, float elapsedSeconds);
}
