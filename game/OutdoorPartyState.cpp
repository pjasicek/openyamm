#include "game/OutdoorPartyState.h"

#include <algorithm>

namespace OpenYAMM::Game
{
void OutdoorPartyState::reset(uint32_t memberCount, int memberMaxHealth)
{
    m_members.clear();
    m_members.resize(memberCount);

    for (OutdoorPartyMemberState &member : m_members)
    {
        member.maxHealth = memberMaxHealth;
        member.health = memberMaxHealth;
    }

    m_waterDamageTicks = 0;
    m_burningDamageTicks = 0;
    m_splashCount = 0;
    m_landingSoundCount = 0;
    m_hardLandingSoundCount = 0;
    m_lastFallDamageDistance = 0.0f;
    m_lastStatus.clear();
}

void OutdoorPartyState::applyMovementEffects(const OutdoorMovementEffects &effects)
{
    for (uint32_t i = 0; i < effects.waterDamageTicks; ++i)
    {
        for (OutdoorPartyMemberState &member : m_members)
        {
            const int damage = std::max(1, member.maxHealth / 10);
            member.health = std::max(0, member.health - damage);
        }

        m_waterDamageTicks += 1;
        m_lastStatus = "water damage";
    }

    for (uint32_t i = 0; i < effects.burningDamageTicks; ++i)
    {
        for (OutdoorPartyMemberState &member : m_members)
        {
            const int damage = std::max(1, member.maxHealth / 10);
            member.health = std::max(0, member.health - damage);
        }

        m_burningDamageTicks += 1;
        m_lastStatus = "burning damage";
    }

    if (effects.maxFallDamageDistance > 0.0f)
    {
        m_lastFallDamageDistance = std::max(m_lastFallDamageDistance, effects.maxFallDamageDistance);

        for (OutdoorPartyMemberState &member : m_members)
        {
            const int damage =
                std::max(0, static_cast<int>(effects.maxFallDamageDistance * (member.maxHealth / 10.0f) / 256.0f));
            member.health = std::max(0, member.health - damage);
        }

        m_lastStatus = "fall damage";
    }

    if (effects.playSplashSound)
    {
        m_splashCount += 1;
        m_lastStatus = "splash";
    }

    if (effects.playLandingSound)
    {
        m_landingSoundCount += 1;
        m_lastStatus = "landing";
    }

    if (effects.playHardLandingSound)
    {
        m_hardLandingSoundCount += 1;
        m_lastStatus = "hard landing";
    }
}

int OutdoorPartyState::totalHealth() const
{
    int totalHealth = 0;

    for (const OutdoorPartyMemberState &member : m_members)
    {
        totalHealth += member.health;
    }

    return totalHealth;
}

int OutdoorPartyState::totalMaxHealth() const
{
    int totalMaxHealth = 0;

    for (const OutdoorPartyMemberState &member : m_members)
    {
        totalMaxHealth += member.maxHealth;
    }

    return totalMaxHealth;
}

uint32_t OutdoorPartyState::waterDamageTicks() const
{
    return m_waterDamageTicks;
}

uint32_t OutdoorPartyState::burningDamageTicks() const
{
    return m_burningDamageTicks;
}

uint32_t OutdoorPartyState::splashCount() const
{
    return m_splashCount;
}

uint32_t OutdoorPartyState::landingSoundCount() const
{
    return m_landingSoundCount;
}

uint32_t OutdoorPartyState::hardLandingSoundCount() const
{
    return m_hardLandingSoundCount;
}

float OutdoorPartyState::lastFallDamageDistance() const
{
    return m_lastFallDamageDistance;
}

const std::string &OutdoorPartyState::lastStatus() const
{
    return m_lastStatus;
}
}
