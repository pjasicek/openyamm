#pragma once

#include "game/tables/ItemTable.h"

#include <cstdint>

namespace OpenYAMM::Game
{
enum class ArpgModeLootImportance : uint8_t
{
    Common = 0,
    Fine,
    Valuable,
    Exceptional,
    Mythic,
    ArtifactRelic,
};

struct ArpgModeLootFacts
{
    bool isGold = false;
    uint32_t goldAmount = 0;
    int value = 0;
    int highestTreasureLevel = 0;
    int reagentPower = 0;
    bool hasStandardEnchant = false;
    bool hasSpecialEnchant = false;
    bool hasRareIdentity = false;
    bool hasArtifactOrRelicIdentity = false;
};

struct ArpgModeLootStyle
{
    uint32_t backgroundColorAbgr = 0;
    uint32_t borderColorAbgr = 0;
    uint32_t textColorAbgr = 0;
    uint32_t beamColorAbgr = 0;
    bool showBeam = false;
    bool showStar = false;
};

int arpgModeHighestTreasureLevel(const ItemDefinition &itemDefinition);
int arpgModeReagentPower(const ItemDefinition &itemDefinition);
ArpgModeLootImportance classifyArpgModeLoot(const ArpgModeLootFacts &facts);
ArpgModeLootStyle arpgModeLootStyle(ArpgModeLootImportance importance, bool isGold);
}
