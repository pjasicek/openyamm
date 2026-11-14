#pragma once

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <optional>
#include <string_view>
#include <unordered_map>

namespace OpenYAMM::Game
{
constexpr size_t MaximumCombatActorHealthBars = 8;
constexpr float MaximumCombatActorHealthBarDistance = 5120.0f;
constexpr float MaximumCombatActorHealthBarDistanceSquared =
    MaximumCombatActorHealthBarDistance * MaximumCombatActorHealthBarDistance;
constexpr float MinimumCombatActorHealthBarScale = 0.22f;
constexpr float CombatActorHealthBarFullSizeDistance = 1000.0f;

inline bool validEnemyHealthBarMode(std::string_view value)
{
    return value == "off" || value == "target" || value == "combat" || value == "nearby";
}

inline bool validEnemyHealthBarValues(std::string_view value)
{
    return value == "off" || value == "target" || value == "all";
}

struct CombatActorHealthBarCandidate
{
    size_t drawItemIndex = 0;
    float distanceSquared = 0.0f;
    size_t actorIndex = 0;
    bool focused = false;
    bool inCombat = false;
};

struct CombatActorHealthBarSelection
{
    std::array<CombatActorHealthBarCandidate, MaximumCombatActorHealthBars> candidates = {};
    size_t count = 0;
};

inline bool healthBarCandidateBefore(
    const CombatActorHealthBarCandidate &left, const CombatActorHealthBarCandidate &right)
{
    if (left.focused != right.focused)
    {
        return left.focused;
    }
    if (left.inCombat != right.inCombat)
    {
        return left.inCombat;
    }
    return left.distanceSquared != right.distanceSquared
        ? left.distanceSquared < right.distanceSquared : left.actorIndex < right.actorIndex;
}

inline void considerCombatActorHealthBarCandidate(
    CombatActorHealthBarSelection &selection, CombatActorHealthBarCandidate candidate, std::string_view mode)
{
    if (mode == "off" || candidate.distanceSquared > MaximumCombatActorHealthBarDistanceSquared
        || (mode == "target" && !candidate.focused)
        || (mode == "combat" && !candidate.focused && !candidate.inCombat))
    {
        return;
    }
    size_t index = 0;
    while (index < selection.count && !healthBarCandidateBefore(candidate, selection.candidates[index]))
    {
        ++index;
    }
    if (index >= selection.candidates.size())
    {
        return;
    }
    selection.count = std::min(selection.count + 1, selection.candidates.size());
    for (size_t move = selection.count - 1; move > index; --move)
    {
        selection.candidates[move] = selection.candidates[move - 1];
    }
    selection.candidates[index] = candidate;
}

inline float combatActorHealthBarScale(float distanceSquared)
{
    const float distance = std::sqrt(std::clamp(distanceSquared, 0.0f, MaximumCombatActorHealthBarDistanceSquared));
    return std::clamp(CombatActorHealthBarFullSizeDistance / std::max(distance, 1.0f),
        MinimumCombatActorHealthBarScale, 1.0f);
}

inline float combatActorHealthBarDepthScale(float anchorDepth, float actorDepth)
{
    if (anchorDepth <= 1.0f || actorDepth <= 1.0f)
    {
        return 0.0f;
    }
    // A raised world anchor can sit behind its camera-facing owner when looking down.
    // Put the bar just ahead of that plane, with a bias capped at two world units.
    const float depth = std::min(anchorDepth, actorDepth);
    const float bias = std::min(2.0f, (depth - 1.0f) * 0.5f);
    return (depth - bias) / anchorDepth;
}

// Shared transient presentation history; never serialized with actors.
class CombatActorHealthBarRuntime
{
public:
    void clear()
    {
        m_actors.clear();
        m_focus.reset();
        m_hoverFocus.reset();
        m_time = 0;
        m_focusUntil = 0;
        m_hoverUntil = 0;
    }

    void advance(float seconds)
    {
        m_time += std::max(0.0f, seconds);
        std::erase_if(m_actors, [this](const auto &entry) { return m_time - entry.second.observed > 6.0; });
        if (m_time > m_focusUntil)
        {
            m_focus.reset();
        }
        if (m_time > m_hoverUntil)
        {
            m_hoverFocus.reset();
        }
    }

    void recordCombatEvent(size_t actorIndex, int hp, int maxHp, int damage)
    {
        m_focus = actorIndex;
        m_focusUntil = m_time + 6.0;
        if (damage <= 0 || maxHp <= 0)
        {
            return;
        }
        Actor &actor = m_actors[actorIndex];
        const float previousTrail = actor.maxHp == maxHp ? trailHp(actor) : 0.0f;
        actor.hp = hp;
        actor.maxHp = maxHp;
        actor.damageFrom = std::min(float(maxHp), std::max(previousTrail, float(hp) + float(damage)));
        actor.damageTime = m_time;
        actor.combatUntil = m_time + 6.0;
        actor.observed = m_time;
    }

    void observe(size_t actorIndex, int hp, int maxHp, bool attackingParty)
    {
        Actor &actor = m_actors[actorIndex];
        if (actor.maxHp == maxHp && hp < actor.hp)
        {
            actor.damageFrom = trailHp(actor);
            actor.damageTime = m_time;
            actor.combatUntil = m_time + 6.0;
        }
        else if (actor.maxHp != maxHp || hp > actor.hp)
        {
            actor.damageFrom = hp;
        }
        actor.hp = hp;
        actor.maxHp = maxHp;
        actor.observed = m_time;
        if (attackingParty)
        {
            actor.combatUntil = m_time + 6.0;
        }
    }

    std::optional<size_t> focus(std::optional<size_t> pointedActor)
    {
        if (pointedActor)
        {
            m_hoverFocus = pointedActor;
            // Only the label retains focus across short holes in an animated sprite's alpha mask.
            m_hoverUntil = m_time + 0.2;
        }
        return m_hoverFocus ? m_hoverFocus : m_focus;
    }

    void observeActivity(size_t actorIndex, bool attackingParty)
    {
        if (attackingParty)
        {
            Actor &actor = m_actors[actorIndex];
            actor.combatUntil = m_time + 6.0;
            actor.observed = m_time;
        }
    }

    bool inCombat(size_t actorIndex) const
    {
        const auto found = m_actors.find(actorIndex);
        return found != m_actors.end() && found->second.combatUntil > m_time;
    }

    float damageRatio(size_t actorIndex, float currentRatio) const
    {
        const auto found = m_actors.find(actorIndex);
        if (found == m_actors.end() || found->second.maxHp <= 0)
        {
            return currentRatio;
        }
        const Actor &actor = found->second;
        return std::clamp(trailHp(actor) / float(actor.maxHp), currentRatio, 1.0f);
    }

    // The share of an effect's duration already spent, for its icon's sweep. The actors keep only the time left, so
    // the duration is the most seen since the effect began; a recast that adds time starts it again. Called every
    // frame the bar is drawn for every slot, active or not, so an effect that ends is forgotten.
    static constexpr size_t EffectSlotCount = 24;
    float effectElapsed(size_t actorIndex, size_t slot, float remainingSeconds)
    {
        Actor &actor = m_actors[actorIndex];
        if (slot >= EffectSlotCount)
        {
            return 0.0f;
        }
        float &duration = actor.effectDurations[slot];
        float &last = actor.effectRemaining[slot];
        if (remainingSeconds <= 0.0f)
        {
            duration = 0.0f;
        }
        else if (duration <= 0.0f || remainingSeconds > last + 0.05f)
        {
            duration = remainingSeconds;
        }
        last = std::max(remainingSeconds, 0.0f);
        return duration > 0.0f ? std::clamp(1.0f - remainingSeconds / duration, 0.0f, 1.0f) : 0.0f;
    }

private:
    struct Actor
    {
        int hp = 0;
        int maxHp = 0;
        float damageFrom = 0;
        double observed = 0;
        double damageTime = 0;
        double combatUntil = 0;
        std::array<float, EffectSlotCount> effectDurations = {};
        std::array<float, EffectSlotCount> effectRemaining = {};
    };
    float trailHp(const Actor &actor) const
    {
        const float drain = std::clamp(float(m_time - actor.damageTime - 0.1) / 0.3f, 0.0f, 1.0f);
        return float(actor.hp) + std::max(0.0f, actor.damageFrom - float(actor.hp)) * (1.0f - drain);
    }

    std::unordered_map<size_t, Actor> m_actors;
    std::optional<size_t> m_focus;
    std::optional<size_t> m_hoverFocus;
    double m_time = 0;
    double m_focusUntil = 0;
    double m_hoverUntil = 0;
};
}
