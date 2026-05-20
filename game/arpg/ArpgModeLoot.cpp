#include "game/arpg/ArpgModeLoot.h"

#include <algorithm>
#include <cstdint>
#include <cstdlib>

namespace OpenYAMM::Game
{
namespace
{
uint32_t makeAbgr(uint8_t red, uint8_t green, uint8_t blue, uint8_t alpha)
{
    return (static_cast<uint32_t>(alpha) << 24)
        | (static_cast<uint32_t>(blue) << 16)
        | (static_cast<uint32_t>(green) << 8)
        | static_cast<uint32_t>(red);
}

int parsePositiveInt(const std::string &text)
{
    if (text.empty())
    {
        return 0;
    }

    char *pEnd = nullptr;
    const long value = std::strtol(text.c_str(), &pEnd, 10);

    if (pEnd == text.c_str() || value <= 0)
    {
        return 0;
    }

    return static_cast<int>(std::min<long>(value, 1000000));
}
}

int arpgModeHighestTreasureLevel(const ItemDefinition &itemDefinition)
{
    int highestTreasureLevel = 0;

    for (size_t index = 0; index < itemDefinition.randomTreasureWeights.size(); ++index)
    {
        if (itemDefinition.randomTreasureWeights[index] > 0)
        {
            highestTreasureLevel = static_cast<int>(index) + 1;
        }
    }

    return highestTreasureLevel;
}

int arpgModeReagentPower(const ItemDefinition &itemDefinition)
{
    if (itemDefinition.equipStat != "Reagent")
    {
        return 0;
    }

    return parsePositiveInt(itemDefinition.mod1);
}

ArpgModeLootImportance classifyArpgModeLoot(const ArpgModeLootFacts &facts)
{
    if (facts.isGold)
    {
        if (facts.goldAmount >= 1000)
        {
            return ArpgModeLootImportance::Exceptional;
        }

        if (facts.goldAmount >= 250)
        {
            return ArpgModeLootImportance::Valuable;
        }

        return ArpgModeLootImportance::Fine;
    }

    if (facts.hasArtifactOrRelicIdentity)
    {
        return ArpgModeLootImportance::ArtifactRelic;
    }

    if (facts.hasRareIdentity || facts.hasSpecialEnchant || facts.highestTreasureLevel >= 6 || facts.value >= 5000)
    {
        return ArpgModeLootImportance::Mythic;
    }

    if (facts.reagentPower >= 20 || facts.highestTreasureLevel >= 5 || facts.value >= 2000)
    {
        return ArpgModeLootImportance::Exceptional;
    }

    if (facts.hasStandardEnchant || facts.reagentPower >= 10 || facts.highestTreasureLevel >= 3 || facts.value >= 500)
    {
        return ArpgModeLootImportance::Valuable;
    }

    if (facts.highestTreasureLevel >= 2 || facts.value >= 100)
    {
        return ArpgModeLootImportance::Fine;
    }

    return ArpgModeLootImportance::Common;
}

ArpgModeLootStyle arpgModeLootStyle(ArpgModeLootImportance importance, bool isGold)
{
    if (isGold)
    {
        return ArpgModeLootStyle{
            .backgroundColorAbgr = makeAbgr(38, 27, 9, 232),
            .borderColorAbgr = makeAbgr(244, 185, 62, 255),
            .textColorAbgr = makeAbgr(255, 229, 132, 255),
            .beamColorAbgr = makeAbgr(255, 202, 77, 210),
            .showBeam = importance >= ArpgModeLootImportance::Valuable,
            .showStar = importance >= ArpgModeLootImportance::Exceptional,
        };
    }

    switch (importance)
    {
        case ArpgModeLootImportance::Mythic:
            return ArpgModeLootStyle{
                .backgroundColorAbgr = makeAbgr(175, 96, 37, 244),
                .borderColorAbgr = makeAbgr(255, 255, 255, 255),
                .textColorAbgr = makeAbgr(255, 255, 255, 255),
                .beamColorAbgr = makeAbgr(255, 68, 48, 220),
                .showBeam = true,
                .showStar = true,
            };

        case ArpgModeLootImportance::ArtifactRelic:
            return ArpgModeLootStyle{
                .backgroundColorAbgr = makeAbgr(252, 248, 238, 248),
                .borderColorAbgr = makeAbgr(255, 28, 26, 255),
                .textColorAbgr = makeAbgr(184, 10, 10, 255),
                .beamColorAbgr = makeAbgr(255, 255, 255, 235),
                .showBeam = true,
                .showStar = true,
            };

        case ArpgModeLootImportance::Exceptional:
            return ArpgModeLootStyle{
                .backgroundColorAbgr = makeAbgr(74, 41, 15, 238),
                .borderColorAbgr = makeAbgr(255, 143, 52, 255),
                .textColorAbgr = makeAbgr(255, 206, 116, 255),
                .beamColorAbgr = makeAbgr(255, 123, 42, 205),
                .showBeam = true,
                .showStar = false,
            };

        case ArpgModeLootImportance::Valuable:
            return ArpgModeLootStyle{
                .backgroundColorAbgr = makeAbgr(16, 22, 64, 232),
                .borderColorAbgr = makeAbgr(82, 110, 244, 255),
                .textColorAbgr = makeAbgr(185, 199, 255, 255),
                .beamColorAbgr = makeAbgr(101, 126, 255, 175),
                .showBeam = false,
                .showStar = false,
            };

        case ArpgModeLootImportance::Fine:
            return ArpgModeLootStyle{
                .backgroundColorAbgr = makeAbgr(42, 33, 19, 226),
                .borderColorAbgr = makeAbgr(203, 155, 78, 255),
                .textColorAbgr = makeAbgr(244, 222, 174, 255),
                .beamColorAbgr = makeAbgr(210, 168, 92, 145),
                .showBeam = false,
                .showStar = false,
            };

        case ArpgModeLootImportance::Common:
        default:
            return ArpgModeLootStyle{
                .backgroundColorAbgr = makeAbgr(22, 23, 25, 218),
                .borderColorAbgr = makeAbgr(92, 94, 98, 230),
                .textColorAbgr = makeAbgr(166, 169, 174, 255),
                .beamColorAbgr = makeAbgr(120, 124, 130, 100),
                .showBeam = false,
                .showStar = false,
            };
    }
}
}
