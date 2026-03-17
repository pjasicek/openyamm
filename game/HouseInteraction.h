#pragma once

#include "game/HouseTable.h"

#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class OutdoorWorldRuntime;
class Party;

enum class HouseActionId : uint32_t
{
    TempleHeal = 1,
    TempleDonate,
    TavernRentRoom,
    TavernBuyFood,
    TrainingTrainLeader,
    BankDepositAll,
    BankWithdrawAll,
};

struct HouseActionOption
{
    HouseActionId id = HouseActionId::TempleHeal;
    std::string label;
    bool enabled = true;
    std::string disabledReason;
};

std::vector<HouseActionOption> buildHouseActionOptions(
    const HouseEntry &houseEntry,
    const Party *pParty,
    int currentHour
);

bool performHouseAction(
    HouseActionId actionId,
    const HouseEntry &houseEntry,
    Party &party,
    OutdoorWorldRuntime *pOutdoorWorldRuntime,
    std::vector<std::string> &messages
);
}
