#pragma once

#include "game/HouseTable.h"

#include <cstdint>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class OutdoorWorldRuntime;
class Party;
class ClassSkillTable;

enum class HouseServiceType : uint32_t
{
    None = 0,
    Shop,
    Temple,
    Bank,
    Tavern,
    TrainingHall,
    Guild,
};

enum class HouseActionId : uint32_t
{
    TempleHeal = 1,
    TempleDonate,
    TavernRentRoom,
    TavernBuyFood,
    TrainingTrainActiveMember,
    BankDepositAll,
    BankWithdrawAll,
    OpenLearnSkillsMenu,
    OpenShopEquipmentMenu,
    OpenTavernArcomageMenu,
    BackToRootMenu,
    LearnSkill,
    ShopBuyStandard,
    ShopBuySpecial,
    ShopSell,
    ShopIdentify,
    ShopRepair,
    GuildBuySpellbooks,
    TavernArcomageRules,
    TavernArcomageVictoryConditions,
    TavernArcomagePlay,
};

struct HouseActionOption
{
    HouseActionId id = HouseActionId::TempleHeal;
    std::string label;
    std::string argument;
    bool enabled = true;
    std::string disabledReason;
};

HouseServiceType resolveHouseServiceType(const HouseEntry &houseEntry);

std::vector<std::string> buildHouseServiceInfoLines(
    const HouseEntry &houseEntry,
    const Party *pParty,
    const ClassSkillTable *pClassSkillTable,
    const std::string &menuId
);

std::vector<HouseActionOption> buildHouseActionOptions(
    const HouseEntry &houseEntry,
    const Party *pParty,
    const ClassSkillTable *pClassSkillTable,
    int currentHour,
    const std::string &menuId
);

bool performHouseAction(
    const HouseActionOption &action,
    const HouseEntry &houseEntry,
    Party &party,
    const ClassSkillTable *pClassSkillTable,
    OutdoorWorldRuntime *pOutdoorWorldRuntime,
    std::vector<std::string> &messages
);
}
