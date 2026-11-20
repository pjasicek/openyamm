#pragma once

#include "game/fx/ParticleRecipes.h"

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace OpenYAMM::Engine
{
class AssetFileSystem;
}

namespace OpenYAMM::Game
{
class EffectLibrary;

struct ProjectileEffectLight
{
    std::array<uint8_t, 3> rgb = {255, 255, 255};
    float radius = 0.0f;
};

// How one projectile recipe, or one monster's variant of it, looks in the enhanced projectile style. Empty effect ids
// keep the recipe's classic presentation for that phase.
struct ProjectileEffectBinding
{
    // Flies with the projectile in place of the recipe's trail particles or beam. For a spell applied to an actor at
    // once (Shrinking Ray), a visual-only bolt that flies from the party to the actor before the impact plays.
    std::string flight;
    // Plays while the projectile lies settled on the ground (an armed Fire Spike).
    std::string settled;
    // Replaces the recipe's impact particles and native impact sprite; the recipe's impact light stays.
    std::string impact;
    // The impact effect sits on the struck actor's centre and follows it.
    bool impactFollowsTarget = false;
    // Flies from each impact back to the casting party (a drain spell's stolen life); party casts only.
    std::string returnFlight;
    // Draw the native projectile sprite under the effects; unset follows the recipe.
    std::optional<bool> nativeSprite;
    // The flight light; unset follows the recipe.
    std::optional<ProjectileEffectLight> light;
    // The impact light; unset follows the recipe.
    std::optional<ProjectileEffectLight> impactLight;
};

class ProjectileEffectBindings
{
public:
    // The binding for a projectile of this recipe thrown by a monster with this picture name (monster_data.txt
    // "Picture"; empty when no monster threw it) as this object (object_list.txt "Name"; empty when unknown). An
    // object's own binding wins, then a monster variant, then the recipe's own binding.
    const ProjectileEffectBinding *find(FxRecipes::ProjectileRecipe recipe, const std::string &monsterPicture,
        const std::string &objectName = std::string()) const;
    bool contains(FxRecipes::ProjectileRecipe recipe) const;
    bool empty() const;
    // Every monster picture name a variant names, normalised, for validation against the monster table.
    std::vector<std::string> variantMonsterPictures() const;
    // Every object name an object binding names, normalised, for validation against the object table.
    std::vector<std::string> objectNames() const;
    // Every effect id any binding or variant names, once each.
    std::vector<std::string> effectIds() const;

    // The impact effect of a projectile falling into water (the splash object), empty when none is bound.
    const std::string &waterSplash() const
    {
        return m_waterSplash;
    }

    void setRecipe(FxRecipes::ProjectileRecipe recipe, ProjectileEffectBinding binding);
    void setWaterSplash(std::string effectId)
    {
        m_waterSplash = std::move(effectId);
    }
    void setVariant(FxRecipes::ProjectileRecipe recipe, const std::string &monsterPicture,
        ProjectileEffectBinding binding);
    void setObject(const std::string &objectName, ProjectileEffectBinding binding);

    static std::string normalizeMonsterPicture(const std::string &monsterPicture);

private:
    std::unordered_map<FxRecipes::ProjectileRecipe, ProjectileEffectBinding> m_recipes;
    std::unordered_map<FxRecipes::ProjectileRecipe, std::unordered_map<std::string, ProjectileEffectBinding>>
        m_variants;
    // By normalised object name: a world's own missiles (monster_projectiles.yml), whatever their recipe.
    std::unordered_map<std::string, ProjectileEffectBinding> m_objects;
    std::string m_waterSplash;
};

// Reads engine/effects/projectiles.yml (schema openyamm.projectileEffects.v1). Each recipe entry may name flight,
// settled, impact and return_flight effects, impact_follows_target, sprite (native|hidden), light {rgb, radius}, and
// variants: a list of {monsters: [picture names], ...} whose fields override the recipe's for projectiles those
// monsters throw. A top-level water_splash names the impact effect of a projectile falling into water. A top-level
// objects map binds projectiles by object name (a world's own missiles) with the same keys plus impact_light
// {rgb, radius}; it wins over the recipe and its variants. Each object binding names a flight and an impact.
// A missing file binds nothing; an unknown recipe, key or effect id fails the load.
bool loadProjectileEffectBindings(
    const Engine::AssetFileSystem &assetFileSystem,
    const std::string &path,
    const EffectLibrary &library,
    ProjectileEffectBindings &bindings,
    std::string &error);
// The same from YAML text; path names the source in errors.
bool parseProjectileEffectBindings(
    const std::string &text,
    const std::string &path,
    const EffectLibrary &library,
    ProjectileEffectBindings &bindings,
    std::string &error);
}
