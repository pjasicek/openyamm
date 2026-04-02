#pragma once

#include "game/events/EventRuntime.h"
#include "game/tables/HouseTable.h"

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
    Transport,
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
    TransportRoute,
};

enum class HouseSoundType : uint32_t
{
    None = 0,
    GeneralGreeting = 1,
    GeneralNotEnoughGold = 2,
    MagicGuildMembersOnly = 3,
    ShopGoodbyeRude = 3,
    ShopGoodbyePolite = 4,
    AlchemyShopGoodbyeRegular = 3,
    AlchemyShopGoodbyeBought = 4,
    TempleGoodbye = 3,
    BankGoodbye = 3,
    TavernRentRoom = 2,
    TavernBuyFood = 3,
    TavernNotEnoughGold = 4,
    TrainingTrain = 2,
    TrainingCantTrain = 3,
    TrainingNotEnoughGold = 4,
    TransportTravel = 2,
    TransportNotEnoughGold = 3,
};

struct HouseActionOption
{
    HouseActionId id = HouseActionId::TempleHeal;
    std::string label;
    std::string argument;
    bool enabled = true;
    std::string disabledReason;
};

struct HouseActionResult
{
    bool succeeded = false;
    std::optional<HouseSoundType> soundType;
    std::vector<std::string> messages;
};

HouseServiceType resolveHouseServiceType(const HouseEntry &houseEntry);
std::optional<uint32_t> deriveHouseSoundId(const HouseEntry &houseEntry, HouseSoundType soundType);
bool isHouseOpenAtGameMinute(const HouseEntry &houseEntry, float currentGameMinutes);
std::string buildClosedStatusText(const HouseEntry &houseEntry);

std::vector<std::string> buildHouseServiceInfoLines(
    const HouseEntry &houseEntry,
    const Party *pParty,
    const ClassSkillTable *pClassSkillTable,
    DialogueMenuId menuId
);

std::vector<HouseActionOption> buildHouseActionOptions(
    const HouseEntry &houseEntry,
    const Party *pParty,
    const ClassSkillTable *pClassSkillTable,
    const OutdoorWorldRuntime *pOutdoorWorldRuntime,
    float currentGameMinutes,
    DialogueMenuId menuId
);

HouseActionResult performHouseAction(
    const HouseActionOption &action,
    const HouseEntry &houseEntry,
    Party &party,
    const ClassSkillTable *pClassSkillTable,
    OutdoorWorldRuntime *pOutdoorWorldRuntime
);
}
