#pragma once

#include <cstdint>
#include <string>
#include <unordered_map>

namespace OpenYAMM::Engine
{
class AssetFileSystem;
}

namespace OpenYAMM::Game
{
// The model's own axis a projectile model spins about while it flies (a tumbling rock, a whirling blade).
enum class ProjectileModelSpinAxis : uint8_t
{
    None,
    // Along the flight (roll).
    Forward,
    // The model's up (glTF +Y): a flat blade whirling in its own plane.
    Up,
    // Across the flight, sideways (glTF +X): end over end.
    Side,
};

// The 3D model a flying projectile draws in place of its native sprite, in both projectile styles. Its effects
// (trail, light, impact) stay as they are.
struct ProjectileModelBinding
{
    // Engine model path. The model points along glTF +Z (Blender -Y) with its origin at the projectile's centre.
    std::string model;
    // World units from tail to tip along the flight; the model is scaled uniformly to it.
    float length = 0.0f;
    ProjectileModelSpinAxis spinAxis = ProjectileModelSpinAxis::None;
    float spinDegreesPerSecond = 0.0f;
    // The file that bound it, for errors.
    std::string sourcePath;
};

// Object id (object_list.txt ObjectId) -> binding.
using ProjectileModelBindings = std::unordered_map<int16_t, ProjectileModelBinding>;

// Reads engine/models/projectiles.yml (schema openyamm.projectileModels.v1): a projectiles list of
// {object, model, length, spin: {axis: forward|up|side, degrees_per_second}} (spin optional). A missing file binds
// nothing; an unknown key, a repeated object, a bad length or a bad spin fails.
bool loadProjectileModelBindings(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &path,
    ProjectileModelBindings &bindings,
    std::string &error);
// The same from YAML text; path names the source in errors.
bool parseProjectileModelBindings(
    const std::string &text,
    const std::string &path,
    ProjectileModelBindings &bindings,
    std::string &error);
// Adds a world's own rows (worlds/<world>/models/projectiles.yml, same schema) to bindings: each object must lie in
// the world's objects id range [objectBegin, objectEnd] and must not be bound yet. A failing file adds nothing.
bool mergeWorldProjectileModelBindings(
    const std::string &text,
    const std::string &path,
    uint32_t objectBegin,
    uint32_t objectEnd,
    ProjectileModelBindings &bindings,
    std::string &error);
// engine/models/projectiles.yml, then every mounted world's models/projectiles.yml through
// mergeWorldProjectileModelBindings. Missing files bind nothing.
bool loadAllProjectileModelBindings(
    const Engine::AssetFileSystem &assetFileSystem,
    ProjectileModelBindings &bindings,
    std::string &error);
}
