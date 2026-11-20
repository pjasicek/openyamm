#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct ElementalDamageBonuses;

// How hard a landed melee blow struck: indexes MonsterTable::MeleeHitMaterial::impactSoundPaths and picks the contact
// effect variant.
enum class MeleeHitStrength : uint8_t
{
    Glancing = 0,
    Normal = 1,
    Crushing = 2,
};

// The shape of the contact effect: an arc for edged weapons, a streak for pointed ones, a burst for blunt ones, and a
// rake of three streaks for a dragon's claws and bite (tilted like a slash).
enum class MeleeWeaponClass : uint8_t
{
    Slash,
    Thrust,
    Crush,
    Claw,
};

// An element whose colour accents a blow.
enum class MeleeWeaponElement : uint8_t
{
    None,
    Fire,
    Air,
    Water,
    Body,
    Light,
    Dark,
};

MeleeWeaponClass meleeWeaponClassForSkill(const std::string &canonicalSkillName);
// The attacker's melee elements, strongest first and at most three: both hands of a dual wielder, or a weapon with
// several elements.
std::vector<MeleeWeaponElement> meleeWeaponElementsFor(const ElementalDamageBonuses &bonuses);
// Size of a material's contact particles on a target of this height.
float meleeContactParticleScale(float targetHeight);
// A material's contact effect for a blow of this strength: the base id with _light or _heavy appended (every contact
// effect named in melee_hit_materials.txt has all three).
std::string meleeContactEffectVariant(const std::string &baseEffectId, MeleeHitStrength strength);

struct MeleeContactEffectInput
{
    MeleeWeaponClass weaponClass = MeleeWeaponClass::Slash;
    MeleeHitStrength strength = MeleeHitStrength::Normal;
    std::array<float, 3> contact = {};
    // The camera eye and its screen axes; the axes are derived from the eye and world up when zero.
    std::array<float, 3> viewer = {};
    std::array<float, 3> screenRight = {};
    std::array<float, 3> screenUp = {};
    size_t memberIndex = 0;
    size_t memberCount = 1;
    float targetHeight = 160.0f;
    bool twoHanded = false;
    // A miss passes beside the contact point, faintly, and ignores strength and element.
    bool missed = false;
    std::vector<MeleeWeaponElement> elements;
    // Uniform in [-1, 1]: a small tilt of the blow, and its side for a member in the middle of the party.
    float variation = 0.0f;
    // The blow's direction on screen (right, up) from the first-person view model's blade; replaces the slot's side
    // and tilt when set.
    std::optional<std::array<float, 2>> blowDirection;
};

struct MeleeContactEffectPlacement
{
    std::string effectId;
    // An accent per element, spawned with the same transform.
    std::vector<std::string> accentEffectIds;
    // The blow's direction on screen (right, up), unit length.
    std::array<float, 2> blowScreenDirection = {};
    std::array<float, 3> position = {};
    // Local +X along the blow's direction on screen, local +Y towards the outer side of its arc, local +Z = X x Y.
    std::array<float, 4> rotation = {0.0f, 0.0f, 0.0f, 1.0f};
    float scale = 1.0f;
};

// Places one of the openyamm:fx/melee/* effects (tools/fx/generate_melee_effects.py) over the contact point. Each party
// slot swings from its own side of the portrait row: the leftmost member cuts from the left, the rightmost from the
// right, the middle nearly straight down. The effect lies in a plane parallel to the screen, moved towards the eye
// and shrunk by the same factor: it covers the same part of the screen, but the creature's body and the ground in
// front of the contact point no longer cut it. Empty when the viewer and the contact point coincide.
std::optional<MeleeContactEffectPlacement> buildMeleeContactEffect(const MeleeContactEffectInput &input);
}
