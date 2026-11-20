#include "game/gameplay/MeleeContactEffects.h"

#include "game/gameplay/GameMechanics.h"

#include <algorithm>
#include <cmath>
#include <numbers>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
using Vector3 = std::array<float, 3>;

// The effects are authored for a target this tall.
constexpr float ReferenceTargetHeight = 160.0f;
constexpr float MinEffectScale = 0.6f;
constexpr float MaxEffectScale = 2.2f;
constexpr float TwoHandedEffectScale = 1.15f;
constexpr size_t MaxAccentElements = 3;
constexpr float MinParticleScale = 0.7f;
constexpr float MaxParticleScale = 1.8f;
// The effect is drawn at this fraction of the eye's distance to the contact point, but no nearer than the minimum.
constexpr float NearDistanceFraction = 0.45f;
constexpr float MinNearDistance = 60.0f;
constexpr float VariationTiltDegrees = 8.0f;
constexpr float DirectionEpsilon = 1.0e-4f;

struct TiltRange
{
    // Degrees below the horizontal for the outermost slots and for the middle of the party.
    float outer;
    float middle;
};

TiltRange tiltRangeFor(MeleeWeaponClass weaponClass)
{
    switch (weaponClass)
    {
        case MeleeWeaponClass::Thrust:
            return {8.0f, 30.0f};

        case MeleeWeaponClass::Crush:
            return {20.0f, 60.0f};

        case MeleeWeaponClass::Slash:
        default:
            return {25.0f, 80.0f};
    }
}

const char *classNameFor(MeleeWeaponClass weaponClass)
{
    switch (weaponClass)
    {
        case MeleeWeaponClass::Thrust:
            return "thrust";

        case MeleeWeaponClass::Crush:
            return "crush";

        case MeleeWeaponClass::Claw:
            return "claw";

        case MeleeWeaponClass::Slash:
        default:
            return "slash";
    }
}

const char *strengthSuffixFor(MeleeHitStrength strength)
{
    switch (strength)
    {
        case MeleeHitStrength::Glancing:
            return "_light";

        case MeleeHitStrength::Crushing:
            return "_heavy";

        case MeleeHitStrength::Normal:
        default:
            return "";
    }
}

const char *elementNameFor(MeleeWeaponElement element)
{
    switch (element)
    {
        case MeleeWeaponElement::Fire:
            return "fire";

        case MeleeWeaponElement::Air:
            return "air";

        case MeleeWeaponElement::Water:
            return "water";

        case MeleeWeaponElement::Body:
            return "body";

        case MeleeWeaponElement::Light:
            return "light";

        case MeleeWeaponElement::Dark:
            return "dark";

        case MeleeWeaponElement::None:
        default:
            return "";
    }
}

Vector3 add(const Vector3 &left, const Vector3 &right)
{
    return {left[0] + right[0], left[1] + right[1], left[2] + right[2]};
}

Vector3 scaled(const Vector3 &value, float factor)
{
    return {value[0] * factor, value[1] * factor, value[2] * factor};
}

Vector3 cross(const Vector3 &left, const Vector3 &right)
{
    return {
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    };
}

float length(const Vector3 &value)
{
    return std::sqrt(value[0] * value[0] + value[1] * value[1] + value[2] * value[2]);
}

// Quaternion (x, y, z, w) of the rotation whose matrix has the given orthonormal columns.
std::array<float, 4> rotationFromBasis(const Vector3 &axisX, const Vector3 &axisY, const Vector3 &axisZ)
{
    const float trace = axisX[0] + axisY[1] + axisZ[2];
    std::array<float, 4> rotation = {};

    if (trace > 0.0f)
    {
        const float s = std::sqrt(trace + 1.0f) * 2.0f;
        rotation = {(axisY[2] - axisZ[1]) / s, (axisZ[0] - axisX[2]) / s, (axisX[1] - axisY[0]) / s, 0.25f * s};
    }
    else if (axisX[0] > axisY[1] && axisX[0] > axisZ[2])
    {
        const float s = std::sqrt(1.0f + axisX[0] - axisY[1] - axisZ[2]) * 2.0f;
        rotation = {0.25f * s, (axisY[0] + axisX[1]) / s, (axisZ[0] + axisX[2]) / s, (axisY[2] - axisZ[1]) / s};
    }
    else if (axisY[1] > axisZ[2])
    {
        const float s = std::sqrt(1.0f + axisY[1] - axisX[0] - axisZ[2]) * 2.0f;
        rotation = {(axisY[0] + axisX[1]) / s, 0.25f * s, (axisZ[1] + axisY[2]) / s, (axisZ[0] - axisX[2]) / s};
    }
    else
    {
        const float s = std::sqrt(1.0f + axisZ[2] - axisX[0] - axisY[1]) * 2.0f;
        rotation = {(axisZ[0] + axisX[2]) / s, (axisZ[1] + axisY[2]) / s, 0.25f * s, (axisX[1] - axisY[0]) / s};
    }

    const float quaternionLength = std::sqrt(rotation[0] * rotation[0] + rotation[1] * rotation[1]
        + rotation[2] * rotation[2] + rotation[3] * rotation[3]);

    for (float &component : rotation)
    {
        component /= quaternionLength;
    }

    return rotation;
}
}

MeleeWeaponClass meleeWeaponClassForSkill(const std::string &canonicalSkillName)
{
    if (canonicalSkillName == "Sword" || canonicalSkillName == "Axe")
    {
        return MeleeWeaponClass::Slash;
    }

    if (canonicalSkillName == "Spear" || canonicalSkillName == "Dagger")
    {
        return MeleeWeaponClass::Thrust;
    }

    return MeleeWeaponClass::Crush;
}

std::string meleeContactEffectVariant(const std::string &baseEffectId, MeleeHitStrength strength)
{
    return baseEffectId + strengthSuffixFor(strength);
}

float meleeContactParticleScale(float targetHeight)
{
    return std::clamp(targetHeight / ReferenceTargetHeight, MinParticleScale, MaxParticleScale);
}

std::vector<MeleeWeaponElement> meleeWeaponElementsFor(const ElementalDamageBonuses &bonuses)
{
    std::array<std::pair<int, MeleeWeaponElement>, 6> candidates = {{
        {bonuses.fire, MeleeWeaponElement::Fire},
        {bonuses.air, MeleeWeaponElement::Air},
        {bonuses.water, MeleeWeaponElement::Water},
        {bonuses.body, MeleeWeaponElement::Body},
        {bonuses.light, MeleeWeaponElement::Light},
        {bonuses.dark, MeleeWeaponElement::Dark},
    }};
    std::stable_sort(candidates.begin(), candidates.end(),
        [](const std::pair<int, MeleeWeaponElement> &left, const std::pair<int, MeleeWeaponElement> &right)
        {
            return left.first > right.first;
        });
    std::vector<MeleeWeaponElement> elements;

    for (const std::pair<int, MeleeWeaponElement> &candidate : candidates)
    {
        if (candidate.first > 0 && elements.size() < MaxAccentElements)
        {
            elements.push_back(candidate.second);
        }
    }

    return elements;
}

std::optional<MeleeContactEffectPlacement> buildMeleeContactEffect(const MeleeContactEffectInput &input)
{
    const Vector3 toViewer = {
        input.viewer[0] - input.contact[0],
        input.viewer[1] - input.contact[1],
        input.viewer[2] - input.contact[2],
    };
    const float viewerDistance = length(toViewer);

    if (!std::isfinite(viewerDistance) || viewerDistance <= DirectionEpsilon)
    {
        return std::nullopt;
    }

    // Without the camera's axes, the screen as seen from the eye: right = forward x up, up = right x forward (as the
    // renderer's right-handed view).
    Vector3 screenRight = input.screenRight;
    Vector3 screenUp = input.screenUp;

    if (length(screenRight) <= DirectionEpsilon || length(screenUp) <= DirectionEpsilon)
    {
        const Vector3 forward = scaled(toViewer, -1.0f / viewerDistance);
        screenRight = cross(forward, {0.0f, 0.0f, 1.0f});
        const float rightLength = length(screenRight);
        screenRight =
            rightLength > DirectionEpsilon ? scaled(screenRight, 1.0f / rightLength) : Vector3{1.0f, 0.0f, 0.0f};
        screenUp = cross(screenRight, forward);
    }

    // Slot position from -1 (leftmost portrait) to 1 (rightmost); a member in the middle takes a side by chance.
    const float halfSpan = input.memberCount > 1 ? (static_cast<float>(input.memberCount) - 1.0f) * 0.5f : 0.0f;
    const float slot = halfSpan > 0.0f
        ? std::clamp((static_cast<float>(input.memberIndex) - halfSpan) / halfSpan, -1.0f, 1.0f) : 0.0f;
    float side = slot < 0.0f ? 1.0f : (slot > 0.0f ? -1.0f : (input.variation < 0.0f ? 1.0f : -1.0f));
    const TiltRange tiltRange = tiltRangeFor(input.weaponClass);
    const float tiltDegrees = tiltRange.outer + (tiltRange.middle - tiltRange.outer) * (1.0f - std::abs(slot))
        + VariationTiltDegrees * input.variation;
    const float tilt = tiltDegrees * std::numbers::pi_v<float> / 180.0f;

    // On screen the blow travels across towards the other side and downwards; the arc bulges up and outwards. A view
    // model's blade gives the direction itself.
    float blowRight = side * std::cos(tilt);
    float blowUp = -std::sin(tilt);
    if (input.blowDirection)
    {
        const float directionLength = std::hypot((*input.blowDirection)[0], (*input.blowDirection)[1]);
        if (directionLength > DirectionEpsilon)
        {
            blowRight = (*input.blowDirection)[0] / directionLength;
            blowUp = (*input.blowDirection)[1] / directionLength;
            side = blowRight < 0.0f ? -1.0f : 1.0f;
        }
    }
    const Vector3 axisX = add(scaled(screenRight, blowRight), scaled(screenUp, blowUp));
    const Vector3 axisY = scaled(add(scaled(screenRight, -blowUp), scaled(screenUp, blowRight)), side);
    const Vector3 axisZ = cross(axisX, axisY);

    const float nearDistance =
        std::min(viewerDistance, std::max(MinNearDistance, viewerDistance * NearDistanceFraction));
    const float nearFactor = nearDistance / viewerDistance;
    float scale = std::clamp(input.targetHeight / ReferenceTargetHeight, MinEffectScale, MaxEffectScale);

    if (input.twoHanded)
    {
        scale *= TwoHandedEffectScale;
    }

    MeleeContactEffectPlacement placement;
    const std::string classEffectId = std::string("openyamm:fx/melee/") + classNameFor(input.weaponClass);
    placement.effectId = classEffectId + (input.missed ? "_miss" : strengthSuffixFor(input.strength));

    if (!input.missed)
    {
        for (MeleeWeaponElement element : input.elements)
        {
            if (element != MeleeWeaponElement::None)
            {
                placement.accentEffectIds.push_back(classEffectId + "_element_" + elementNameFor(element));
            }
        }
    }

    placement.blowScreenDirection = {blowRight, blowUp};
    placement.position = add(input.viewer, scaled(toViewer, -nearFactor));
    placement.rotation = rotationFromBasis(axisX, axisY, axisZ);
    placement.scale = scale * nearFactor;
    return placement;
}
}
