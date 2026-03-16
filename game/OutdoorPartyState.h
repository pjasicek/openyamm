#pragma once

#include "game/OutdoorMovementDriver.h"

#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct OutdoorPartyMemberState
{
    int maxHealth = 100;
    int health = 100;
};

class OutdoorPartyState
{
public:
    void reset(uint32_t memberCount = 4, int memberMaxHealth = 100);
    void applyMovementEffects(const OutdoorMovementEffects &effects);
    int totalHealth() const;
    int totalMaxHealth() const;
    uint32_t waterDamageTicks() const;
    uint32_t burningDamageTicks() const;
    uint32_t splashCount() const;
    uint32_t landingSoundCount() const;
    uint32_t hardLandingSoundCount() const;
    float lastFallDamageDistance() const;
    const std::string &lastStatus() const;

private:
    std::vector<OutdoorPartyMemberState> m_members;
    uint32_t m_waterDamageTicks = 0;
    uint32_t m_burningDamageTicks = 0;
    uint32_t m_splashCount = 0;
    uint32_t m_landingSoundCount = 0;
    uint32_t m_hardLandingSoundCount = 0;
    float m_lastFallDamageDistance = 0.0f;
    std::string m_lastStatus;
};
}
