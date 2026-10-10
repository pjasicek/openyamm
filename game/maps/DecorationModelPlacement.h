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

// A camera-facing card corner (asset space p) in world space, turned about the vertical axis toward the viewer as
// modelStaticPosition (model_static.sh) turns it toward the camera: its offset across the model and its height stay.
std::array<float, 3> facingCardCorner(const Engine::ModelMatrix &placement, const std::array<float, 3> &p,
    const std::array<float, 3> &viewer);

// Yaw (radians, for Engine::gltfModelPlacement) that turns a model's front (asset +z) toward a horizontal direction.
float yawFacing(const std::array<float, 2> &direction);

// A wall-mounted placement: the model faces away from the wall (asset +z along the wall normal) with its back
// (the asset bounds' minimum z, scaled) on the wall face, at height z.
Engine::ModelMatrix wallMountedPlacement(const DecorationWallContact &wall, float backZ, float z, float scale);

// A placement swung by angleRadians about the asset x axis through the asset point pivot (a hanging chandelier or
// cage swinging from its top).
Engine::ModelMatrix swungPlacement(const Engine::ModelMatrix &placement, const std::array<float, 3> &pivot,
    float angleRadians);
}
