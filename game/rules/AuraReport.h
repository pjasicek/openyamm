#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
// What the party's auras do, as the aura panel shows it (SpellRules::auraReport; MAW,
// level_generation/ui/maw_aura_panel_20261025 A). The rules compute it; the panel only formats it.

enum class AuraState : uint8_t
{
    // Every effect reaches every member.
    Active,
    // A stronger source covers some of its effects, or covers them for some members.
    PartlyUsed,
    // A stronger source covers all of it: it reserves for nothing.
    AddsNothing,
    // The holder is unconscious, dead or stoned: the effect is off, the reservation stays.
    Suspended,
    // A temple's, scroll's or pedestal's aura, reserving nothing.
    Blessing,
};

// How an effect's number reads: "+60", "+7 %", "-21 %", or words only (AuraEffect::text).
enum class AuraValueKind : uint8_t
{
    Text,
    Bonus,
    BonusPercent,
    ReductionPercent,
};

// A stronger source of an effect: another aura the party holds, or a member's own potion copy of one.
struct AuraRival
{
    uint32_t spellId = 0;
    // The aura's holder, or the potion's drinker; none for a blessing.
    std::optional<size_t> memberIndex;
    bool potion = false;
    double value = 0;
};

// One effect of an aura at its holder's strength.
struct AuraEffect
{
    std::string label;
    AuraValueKind kind = AuraValueKind::Text;
    double value = 0;
    // The effect in words for AuraValueKind::Text.
    std::string text;
    // The members this aura gives the effect to, of the party's.
    size_t membersUsing = 0;
    size_t members = 0;
    // The source that covers it where it gives way (for the first member it gives way for).
    std::optional<AuraRival> stronger;
};

// What one member gets from an aura.
struct AuraMemberBenefit
{
    // Indices into AuraReportEntry::effects.
    std::vector<size_t> effects;
    // With no effect: the source that covers its first effect for this member.
    std::optional<AuraRival> coveredBy;
};

// What holding an aura costs a member.
struct AuraReservationCost
{
    // The share of the member's maximum (0 for a flat one) and the points it holds.
    double percent = 0;
    int points = 0;
    // Torch Light, Wizard Eye, Water Walk: a flat number of points.
    bool flat = false;
    // Legendary 32: hit points instead of spell points.
    bool health = false;
    // Death Knights and the Thief line reserve nothing.
    bool free = false;
};

// A member the aura could move to: casting it as them.
struct AuraMoveOption
{
    size_t memberIndex = 0;
    bool knowsSpell = false;
    AuraReservationCost cost;
    // Whether the reservation fits in what the member's other auras leave of the pool, and how much that is.
    bool fits = false;
    int freePoints = 0;
    bool conscious = true;
};

struct AuraReportEntry
{
    uint32_t spellId = 0;
    // The holder; none for a blessing.
    std::optional<size_t> holder;
    // A blessing: a temple's (it ends on the next map) or this place's (a scroll or pedestal: it ends on another
    // outdoor map).
    bool templeBlessing = false;
    // A solo run's scroll blessing: the game seconds it has left, on any map.
    std::optional<float> scrollSecondsLeft;
    AuraReservationCost cost;
    // The strength it holds at: the school skill (counted up to its cap), mastery (1-4) and level.
    std::string schoolSkill;
    double skill = 0;
    bool skillCapped = false;
    int mastery = 0;
    int level = 0;
    AuraState state = AuraState::Active;
    std::vector<AuraEffect> effects;
    // By member index.
    std::vector<AuraMemberBenefit> members;
    std::vector<AuraMoveOption> moveTo;
};

// A member's pool and what the auras hold of it (hit points for a Legendary 32 wearer).
struct AuraMemberPool
{
    int maximum = 0;
    int current = 0;
    int reserved = 0;
    bool health = false;
    bool reservesNothing = false;
    bool conscious = true;
};

struct AuraReport
{
    // The held auras by holder in party order, the blessings last, each holder's by spell id.
    std::vector<AuraReportEntry> auras;
    // By member index.
    std::vector<AuraMemberPool> pools;
    int reservedSpellPoints = 0;
    int reservedHitPoints = 0;
};
}
