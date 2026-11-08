#pragma once

#include <cstddef>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace OpenYAMM::Game
{
enum class CombatDamageType;
struct Mm9HirelingAttack;
struct Mm9HirelingSpell;

// The MM9 hireling rail's geometry and inspection text (devdocs/mm9/MM9_HIRELINGS_PLAN.md phase 6; the design study
// level_generation/ui/mm9_hirelings_20261106, revision 2). The rail itself is laid out in gameplay.yml
// (Mm9HirelingRail and its Mm9Hireling1-3 slots) and drawn by GameplayHirelingRail.
struct Mm9HirelingRailRect
{
    float x = 0.0f;
    float y = 0.0f;
    float width = 0.0f;
    float height = 0.0f;

    bool contains(float pointX, float pointY) const
    {
        return pointX >= x && pointX < x + width && pointY >= y && pointY < y + height;
    }
};

// The rail's panel around the live slots: the laid-out rail (sized for three), ending under the last live slot with
// the band the first slot has above it.
Mm9HirelingRailRect mm9HirelingRailPanel(
    const Mm9HirelingRailRect &rail,
    const Mm9HirelingRailRect &firstSlot,
    const Mm9HirelingRailRect &lastLiveSlot);
// The live slot (the hireling's index in Party::hirelings()) under a point.
std::optional<size_t> mm9HirelingRailSlotAt(const std::vector<Mm9HirelingRailRect> &liveSlots, float x, float y);

// "Physical", "Fire", ...: English, translated where shown.
std::string_view mm9HirelingDamageTypeName(CombatDamageType damageType);
// An attack for the inspection, in the interface language: "2d9+17 Physical", "5d3+10 Physical, Arrow"; empty
// without one.
std::string formatMm9HirelingAttack(const Mm9HirelingAttack &attack);
// A spell for the inspection: "Fireball, Expert 6" (displayName: the spell table's name of spell.name, already in the
// interface language).
std::string formatMm9HirelingSpell(const Mm9HirelingSpell &spell, const std::string &displayName);
}
