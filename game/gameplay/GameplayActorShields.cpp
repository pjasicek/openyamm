#include "game/gameplay/GameplayActorShields.h"

#include "game/events/EventRuntime.h"
#include "game/tables/MonsterTable.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
// Presentation ages stop counting here (a break or raise long ago is "none").
constexpr float PresentationAgeLimitSeconds = 30.0f;
constexpr float HitLifetimeSeconds = 0.8f;
}

ShieldAttackTier shieldAttackTierForDamageType(CombatDamageType damageType, bool fromParty)
{
    switch (damageType)
    {
        case CombatDamageType::Physical:
            return ShieldAttackTier::Physical;
        case CombatDamageType::Energy:
            return fromParty ? ShieldAttackTier::ClassicBlaster : ShieldAttackTier::KreeganEnergy;
        case CombatDamageType::Irresistible:
            return fromParty ? ShieldAttackTier::ClassicBlaster : ShieldAttackTier::Spell;
        default:
            return ShieldAttackTier::Spell;
    }
}

std::array<float, 3> actorShieldImpactPoint(const std::array<float, 3> &foot, float radius, float height,
    const std::array<float, 3> &source)
{
    const float deltaX = source[0] - foot[0];
    const float deltaY = source[1] - foot[1];
    const float distance = std::sqrt(deltaX * deltaX + deltaY * deltaY);
    const float scale = distance > 0.001f ? radius / distance : 0.0f;
    const float z = std::clamp(source[2], foot[2] + height * 0.2f, foot[2] + height * 0.85f);
    return {foot[0] + deltaX * scale, foot[1] + deltaY * scale, z};
}

void GameplayActorShields::bind(const MonsterShieldTable *pTable, const MonsterTable *pRelations)
{
    m_pTable = pTable;
    m_pRelations = pRelations;
    clear();
}

void GameplayActorShields::clear()
{
    m_entries.clear();
    m_sounds.clear();
    m_regenMultipliers.clear();
    m_deadLinkers.clear();
}

GameplayActorShields::Entry *GameplayActorShields::ensure(size_t actorIndex, int16_t monsterId)
{
    if (!active())
    {
        return nullptr;
    }
    const MonsterShieldProfile *pProfile = m_pTable->find(monsterId);
    if (pProfile == nullptr)
    {
        if (actorIndex < m_entries.size())
        {
            m_entries[actorIndex] = {};
        }
        return nullptr;
    }
    if (actorIndex >= m_entries.size())
    {
        m_entries.resize(actorIndex + 1);
    }
    Entry &entry = m_entries[actorIndex];
    if (!entry.used || entry.monsterId != monsterId)
    {
        // A new actor (or a reused index): its shield starts full.
        entry = {};
        entry.used = true;
        entry.monsterId = monsterId;
        entry.current = float(pProfile->pool);
        entry.secondsSinceDamage = pProfile->regenDelaySeconds;
        for (std::array<float, 4> &hit : entry.hits)
        {
            hit[3] = -1.0f;
        }
    }
    entry.pProfile = pProfile;
    return &entry;
}

void GameplayActorShields::queueSound(const std::string &name, const std::array<float, 3> &position)
{
    if (name.empty() || m_pTable == nullptr)
    {
        return;
    }
    const ShieldSoundDefinition *pSound = m_pTable->findSound(name);
    m_sounds.push_back({name, pSound != nullptr ? pSound->fallback : std::string(), position});
}

void GameplayActorShields::update(
    float deltaSeconds,
    size_t actorCount,
    const std::function<ActorFacts(size_t)> &actorFacts)
{
    if (!active() || deltaSeconds <= 0.0f)
    {
        return;
    }
    if (m_entries.size() > actorCount)
    {
        m_entries.resize(actorCount);
    }
    const int16_t minimumId = m_pTable->minimumMonsterId();
    const int16_t maximumId = m_pTable->maximumMonsterId();
    m_deadLinkers.clear();
    for (size_t actorIndex = 0; actorIndex < actorCount; ++actorIndex)
    {
        const ActorFacts facts = actorFacts(actorIndex);
        if (facts.monsterId < minimumId || facts.monsterId > maximumId)
        {
            if (actorIndex < m_entries.size() && m_entries[actorIndex].used)
            {
                m_entries[actorIndex] = {};
            }
            continue;
        }
        Entry *pEntry = ensure(actorIndex, facts.monsterId);
        if (pEntry == nullptr)
        {
            continue;
        }
        Entry &entry = *pEntry;
        entry.center = facts.center;
        entry.hostileToParty = facts.hostileToParty;
        if (entry.alive && !facts.alive && entry.pProfile->linkRadius > 0.0f && entry.pProfile->linkDropsOnDeath)
        {
            m_deadLinkers.push_back(actorIndex);
        }
        entry.alive = facts.alive;
        for (std::array<float, 4> &hit : entry.hits)
        {
            if (hit[3] >= 0.0f)
            {
                hit[3] += deltaSeconds;
                hit[3] = hit[3] > HitLifetimeSeconds ? -1.0f : hit[3];
            }
        }
        for (float *pAge : {&entry.secondsSinceBreak, &entry.secondsSinceRaise})
        {
            if (*pAge >= 0.0f)
            {
                *pAge += deltaSeconds;
                *pAge = *pAge > PresentationAgeLimitSeconds ? -1.0f : *pAge;
            }
        }
    }

    if (m_pTable->hasLinks())
    {
        updateLinks();
    }

    for (size_t actorIndex = 0; actorIndex < m_entries.size(); ++actorIndex)
    {
        Entry &entry = m_entries[actorIndex];
        if (!entry.used || !entry.alive || entry.pProfile == nullptr)
        {
            continue;
        }
        if (entry.suspendedSeconds != 0.0f)
        {
            entry.suspendedSeconds = entry.suspendedSeconds > 0.0f
                ? std::max(0.0f, entry.suspendedSeconds - deltaSeconds) : entry.suspendedSeconds;
            entry.current = 0.0f;
            continue;
        }
        const MonsterShieldProfile &profile = *entry.pProfile;
        const float before = entry.current;
        const float multiplier = actorIndex < m_regenMultipliers.size() ? m_regenMultipliers[actorIndex] : 1.0f;
        entry.current =
            regenerateMonsterShield(profile, entry.current, entry.secondsSinceDamage, deltaSeconds, multiplier);
        entry.secondsSinceDamage = std::min(entry.secondsSinceDamage + deltaSeconds, 3600.0f);
        if (before <= 0.0f && entry.current > 0.0f && profile.pool > 0)
        {
            // Back up: the shell rises over the body.
            entry.secondsSinceRaise = 0.0f;
            ++entry.raiseSerial;
            if (const ShieldGradeDefinition *pGrade = m_pTable->grade(profile))
            {
                queueSound(pGrade->regenSound, entry.center);
            }
        }
    }
}

bool GameplayActorShields::allied(const Entry &linker, const Entry &other) const
{
    return linker.hostileToParty == other.hostileToParty
        && (m_pRelations == nullptr
            || m_pRelations->getRelationBetweenMonsters(linker.monsterId, other.monsterId) <= 0);
}

void GameplayActorShields::updateLinks()
{
    m_regenMultipliers.assign(m_entries.size(), 1.0f);
    const auto inReach = [](const Entry &linker, const Entry &other)
    {
        const float deltaX = other.center[0] - linker.center[0];
        const float deltaY = other.center[1] - linker.center[1];
        const float deltaZ = other.center[2] - linker.center[2];
        const float radius = linker.pProfile->linkRadius;
        return deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ <= radius * radius;
    };
    for (const Entry &linker : m_entries)
    {
        if (!linker.used || !linker.alive || linker.pProfile == nullptr || linker.pProfile->linkRadius <= 0.0f)
        {
            continue;
        }
        for (size_t otherIndex = 0; otherIndex < m_entries.size(); ++otherIndex)
        {
            const Entry &other = m_entries[otherIndex];
            if (other.used && other.alive && other.pProfile != nullptr && other.pProfile->pool > 0
                && allied(linker, other) && inReach(linker, other))
            {
                m_regenMultipliers[otherIndex] =
                    std::max(m_regenMultipliers[otherIndex], linker.pProfile->linkRegenMultiplier);
            }
        }
    }
    // A linker that just died takes its allies' raised shields down with it.
    for (const size_t linkerIndex : m_deadLinkers)
    {
        const Entry &linker = m_entries[linkerIndex];
        for (size_t otherIndex = 0; otherIndex < m_entries.size(); ++otherIndex)
        {
            Entry &other = m_entries[otherIndex];
            if (otherIndex != linkerIndex && other.used && other.alive && other.pProfile != nullptr
                && other.pProfile->pool > 0 && other.current > 0.0f && allied(linker, other) && inReach(linker, other))
            {
                breakShield(other, other.center);
                other.secondsSinceDamage = 0.0f;
            }
        }
    }
}

void GameplayActorShields::addRipple(Entry &entry, const std::array<float, 3> &impact)
{
    // The oldest slot takes the new ripple.
    std::array<float, 4> *pSlot = &entry.hits[0];
    for (std::array<float, 4> &hit : entry.hits)
    {
        if (hit[3] < 0.0f)
        {
            pSlot = &hit;
            break;
        }
        pSlot = hit[3] > (*pSlot)[3] ? &hit : pSlot;
    }
    *pSlot = {impact[0], impact[1], impact[2], 0.0f};
    ++entry.hitSerial;
}

void GameplayActorShields::breakShield(Entry &entry, const std::array<float, 3> &impact)
{
    entry.current = 0.0f;
    entry.secondsSinceBreak = 0.0f;
    ++entry.breakSerial;
    if (const ShieldGradeDefinition *pGrade = entry.pProfile != nullptr ? m_pTable->grade(*entry.pProfile) : nullptr)
    {
        queueSound(pGrade->breakSound, impact);
    }
}

GameplayActorShieldHit GameplayActorShields::applyHit(
    size_t actorIndex,
    int16_t monsterId,
    int damage,
    ShieldAttackTier tier,
    const std::array<float, 3> *pImpactPoint,
    const ShieldHitModifiers &modifiers)
{
    GameplayActorShieldHit result;
    result.bodyDamage = damage;
    if (!active() || damage <= 0)
    {
        return result;
    }
    Entry *pEntry = ensure(actorIndex, monsterId);
    if (pEntry == nullptr)
    {
        return result;
    }
    Entry &entry = *pEntry;
    const MonsterShieldProfile &profile = *entry.pProfile;
    const ShieldHitResolution resolution =
        resolveMonsterShieldHit(*m_pTable, profile, entry.current, damage, tier, modifiers);
    result.bodyDamage = resolution.bodyDamage;
    result.absorbed = resolution.absorbed;
    result.broke = resolution.broke;
    if (resolution.shieldDamage > 0.0f || resolution.bodyDamage > 0)
    {
        entry.secondsSinceDamage = 0.0f;
    }
    if (!resolution.absorbed && !resolution.cleaved)
    {
        return result;
    }
    result.shieldDamage = resolution.shieldDamage;
    const std::array<float, 3> impact = pImpactPoint != nullptr ? *pImpactPoint : entry.center;
    addRipple(entry, impact);
    entry.current = std::max(0.0f, entry.current - resolution.shieldDamage);
    if (resolution.broke)
    {
        breakShield(entry, impact);
    }
    else if (const ShieldGradeDefinition *pGrade = m_pTable->grade(profile))
    {
        queueSound(pGrade->hitSound, impact);
    }
    return result;
}

bool GameplayActorShields::suspend(size_t actorIndex, int16_t monsterId, float seconds)
{
    Entry *pEntry = active() ? ensure(actorIndex, monsterId) : nullptr;
    if (pEntry == nullptr || pEntry->pProfile == nullptr || pEntry->pProfile->pool <= 0)
    {
        return false;
    }
    if (pEntry->current > 0.0f)
    {
        breakShield(*pEntry, pEntry->center);
    }
    pEntry->suspendedSeconds = seconds > 0.0f ? seconds : -1.0f;
    return true;
}

bool GameplayActorShields::restore(size_t actorIndex)
{
    if (actorIndex >= m_entries.size() || !m_entries[actorIndex].used)
    {
        return false;
    }
    m_entries[actorIndex].suspendedSeconds = 0.0f;
    m_entries[actorIndex].secondsSinceDamage = 3600.0f;
    return true;
}

bool GameplayActorShields::cutRaisedShield(
    size_t actorIndex,
    float remainingFraction,
    const std::array<float, 3> *pImpactPoint)
{
    if (actorIndex >= m_entries.size() || !m_entries[actorIndex].used || m_entries[actorIndex].pProfile == nullptr
        || m_entries[actorIndex].current <= 0.0f)
    {
        return false;
    }
    Entry &entry = m_entries[actorIndex];
    entry.current *= std::clamp(remainingFraction, 0.0f, 1.0f);
    entry.secondsSinceDamage = 0.0f;
    const std::array<float, 3> impact = pImpactPoint != nullptr ? *pImpactPoint : entry.center;
    addRipple(entry, impact);
    if (entry.current < 0.5f)
    {
        breakShield(entry, impact);
    }
    else if (const ShieldGradeDefinition *pGrade = m_pTable->grade(*entry.pProfile))
    {
        queueSound(pGrade->hitSound, impact);
    }
    return true;
}

float GameplayActorShields::secondsDownSinceBreak(size_t actorIndex) const
{
    if (actorIndex >= m_entries.size() || !m_entries[actorIndex].used || m_entries[actorIndex].current > 0.0f)
    {
        return -1.0f;
    }
    return m_entries[actorIndex].secondsSinceBreak;
}

const MonsterShieldProfile *GameplayActorShields::profile(size_t actorIndex) const
{
    return actorIndex < m_entries.size() && m_entries[actorIndex].used ? m_entries[actorIndex].pProfile : nullptr;
}

void GameplayActorShields::view(size_t actorIndex, GameplayActorShieldView &view) const
{
    view = {};
    if (actorIndex >= m_entries.size() || !m_entries[actorIndex].used || m_entries[actorIndex].pProfile == nullptr
        || m_entries[actorIndex].pProfile->pool <= 0)
    {
        return;
    }
    const Entry &entry = m_entries[actorIndex];
    const MonsterShieldProfile &profile = *entry.pProfile;
    view.present = true;
    view.raised = entry.current > 0.0f;
    view.fraction = std::clamp(entry.current / float(profile.pool), 0.0f, 1.0f);
    if (const ShieldGradeDefinition *pGrade = m_pTable->grade(profile))
    {
        view.color = pGrade->color;
        view.intensity = pGrade->intensity;
        view.restIntensity = pGrade->restIntensity.value_or(-1.0f);
    }
    view.secondsSinceBreak = entry.secondsSinceBreak;
    view.secondsSinceRaise = entry.secondsSinceRaise;
    view.hits = entry.hits;
    view.hitSerial = entry.hitSerial;
    view.breakSerial = entry.breakSerial;
    view.raiseSerial = entry.raiseSerial;
}

float GameplayActorShields::shieldPoints(size_t actorIndex) const
{
    return actorIndex < m_entries.size() && m_entries[actorIndex].used ? m_entries[actorIndex].current : 0.0f;
}

bool GameplayActorShields::setShieldPoints(size_t actorIndex, float points)
{
    if (actorIndex >= m_entries.size() || !m_entries[actorIndex].used || m_entries[actorIndex].pProfile == nullptr)
    {
        return false;
    }
    Entry &entry = m_entries[actorIndex];
    entry.current = std::clamp(points, 0.0f, float(entry.pProfile->pool));
    return true;
}

void GameplayActorShields::queueSounds(EventRuntimeState &eventRuntimeState)
{
    for (const GameplayActorShieldSound &sound : m_sounds)
    {
        EventRuntimeState::PendingSound request = {};
        request.soundScope = SoundScope::World;
        request.soundName = sound.name;
        request.fallbackSoundName = sound.fallback;
        request.x = int32_t(std::lround(sound.position[0]));
        request.y = int32_t(std::lround(sound.position[1]));
        request.z = int32_t(std::lround(sound.position[2]));
        request.positional = true;
        request.hasExplicitZ = true;
        eventRuntimeState.pendingSounds.push_back(std::move(request));
    }
    m_sounds.clear();
}

std::vector<GameplayActorShieldSound> GameplayActorShields::drainSounds()
{
    std::vector<GameplayActorShieldSound> sounds;
    sounds.swap(m_sounds);
    return sounds;
}
}
