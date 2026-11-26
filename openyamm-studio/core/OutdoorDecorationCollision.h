#pragma once

#include "core/OutdoorPlaces.h"
#include "game/outdoor/OutdoorMapData.h"

#include <array>
#include <filesystem>
#include <map>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Studio
{
// A binding and the same native-space triangles feed the indoor and outdoor compilers.
class DecorationCollisionModels
{
public:
    struct Binding
    {
        std::string model;
        std::string collisionModel;
        double height = 0.0;
        double heightJitter = 0.0;
        bool randomYaw = true;
        bool scatter = false;
        double yawOffset = 0.0;
        double zOffset = 0.0;
    };
    struct Shape
    {
        std::vector<std::array<double, 3>> triangles;
        double low = 0.0;
        double high = 0.0;
    };

    DecorationCollisionModels(const std::filesystem::path &assets, const std::string &world,
        const std::string &mapStem, bool indoors);
    std::vector<std::array<double, 3>> place(const std::string &name, double x, double y, double z,
        double facing, bool scattered, std::vector<std::string> &warnings);

private:
    std::filesystem::path m_assets;
    std::map<std::string, Binding> m_bindings;
    std::map<std::string, std::optional<Shape>> m_shapes;
};

// How far each named outdoor decoration bound to a 3D model on the ground (engine/models/decorations.yml, the world's
// replacing an entry of its name) reaches from its middle as the game draws it: the farthest of the model's base-mesh
// points across x or z, at the binding's height over the model's. Names without a readable model are left out.
std::map<std::string, double> decorationDrawnReach(const std::filesystem::path &assetRoot, const std::string &world,
    const std::string &mapStem, const std::vector<std::string> &names);

// Collision for outdoor decorations the game draws as 3D models. The game keeps a decoration's native collision, an
// upright cylinder of its decoration_data.txt radius and height (none at radius 0), so a long or hollow model (Xeen's
// world hull, a ship) is walked and flown through. A binding in engine/models/decorations.yml or the world's
// models/decorations.yml with `collision: model` makes the build raise, under each such decoration of the sketch's
// structures, an invisible model of the 3D model's own triangles (its base mesh, not its _lodN ones), placed as the
// game places the model (DecorationModelSet::placementFor: the binding's height over the model's height, its
// height_jitter, yaw by the decoration's facing or at random, yaw_offset, z_offset). Its faces are not drawn but are
// walked on and stop the party, monsters and missiles as any model's do. `collision_model:` names a simpler proxy
// glTF in the visible model's coordinates, or `lod` for the visible model's coarsest LOD (the last of its
// `openyamm_lods`; the base mesh when it has none); either is placed by the visible model's base-mesh height.
// Scattered decorations keep their cylinder unless the binding explicitly requests collision_scatter (permanent solid
// rock or structures). Wall-mounted bindings keep their cylinder; a decoration that starts hidden gets none (it would
// block where nothing shows).
//
// The models are named `collision:<structure id>`. `warnings` gets a binding whose model cannot be read.
std::vector<Game::OutdoorBModel> raiseDecorationCollision(const std::filesystem::path &assetRoot,
    const std::string &world, const std::string &mapStem, const std::vector<OutdoorPlacedDecoration> &decorations,
    const std::vector<std::string> &ids, const std::vector<bool> &hidden, std::vector<std::string> &warnings,
    const std::vector<OutdoorPlacedDecoration> &scatter = {});
}
