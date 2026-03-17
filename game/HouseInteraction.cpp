#include "game/HouseInteraction.h"

#include "game/OutdoorWorldRuntime.h"
#include "game/Party.h"

#include <algorithm>
#include <cmath>

namespace OpenYAMM::Game
{
namespace
{
constexpr int RestTargetHour = 6;
constexpr int TavernFoodTarget = 14;

bool isHouseType(const HouseEntry &houseEntry, const char *pTypeName)
{
    return houseEntry.type == pTypeName;
}

bool isInnLikeHouse(const HouseEntry &houseEntry)
{
    return houseEntry.type == "Tavern"
        || houseEntry.type == "The Adventurer's Inn"
        || houseEntry.name.find("Inn") != std::string::npos;
}

bool isHouseOpen(const HouseEntry &houseEntry, int currentHour)
{
    if (currentHour < 0 || houseEntry.openHour == houseEntry.closeHour)
    {
        return true;
    }

    if (houseEntry.openHour < houseEntry.closeHour)
    {
        return currentHour >= houseEntry.openHour && currentHour < houseEntry.closeHour;
    }

    return currentHour >= houseEntry.openHour || currentHour < houseEntry.closeHour;
}

std::string buildClosedReason(const HouseEntry &houseEntry)
{
    return "Closed. Hours: "
        + std::to_string(houseEntry.openHour)
        + ":00 - "
        + std::to_string(houseEntry.closeHour)
        + ":00";
}

int roundPrice(float multiplier, int scale, int minimumPrice)
{
    const int scaledPrice = static_cast<int>(std::round(multiplier * static_cast<float>(scale)));
    return std::max(minimumPrice, scaledPrice);
}

int templeHealCost(const HouseEntry &houseEntry)
{
    return roundPrice(houseEntry.priceMultiplier, 20, 10);
}

int templeDonationCost(const HouseEntry &houseEntry)
{
    return roundPrice(houseEntry.priceMultiplier, 1, 1);
}

int tavernRoomCost(const HouseEntry &houseEntry)
{
    return roundPrice(houseEntry.priceMultiplier, 8, 4);
}

int tavernFoodCost(const HouseEntry &houseEntry)
{
    return roundPrice(houseEntry.priceMultiplier, 3, 2);
}

int trainingCost(const HouseEntry &houseEntry, const Party &party)
{
    const std::vector<Character> &members = party.members();
    const uint32_t level = members.empty() ? 1 : members.front().level;
    const int scaledCost = static_cast<int>(level) * roundPrice(houseEntry.priceMultiplier, 10, 5);
    return std::max(10, scaledCost);
}

float restDurationMinutes(int currentHour)
{
    if (currentHour < 0)
    {
        return 8.0f * 60.0f;
    }

    int hoursUntilMorning = RestTargetHour - currentHour;

    if (hoursUntilMorning <= 0)
    {
        hoursUntilMorning += 24;
    }

    return static_cast<float>(hoursUntilMorning * 60);
}

HouseActionOption makeOption(
    HouseActionId actionId,
    const std::string &label,
    bool isHouseOpenNow,
    const std::string &closedReason
)
{
    HouseActionOption option = {};
    option.id = actionId;
    option.label = label;
    option.enabled = isHouseOpenNow;
    option.disabledReason = isHouseOpenNow ? std::string {} : closedReason;
    return option;
}
}

std::vector<HouseActionOption> buildHouseActionOptions(
    const HouseEntry &houseEntry,
    const Party *pParty,
    int currentHour
)
{
    std::vector<HouseActionOption> options;
    const bool isHouseOpenNow = isHouseOpen(houseEntry, currentHour);
    const std::string closedReason = buildClosedReason(houseEntry);

    if (isHouseType(houseEntry, "Temple"))
    {
        HouseActionOption heal = makeOption(
            HouseActionId::TempleHeal,
            "Heal party for " + std::to_string(templeHealCost(houseEntry)) + " gold",
            isHouseOpenNow,
            closedReason
        );

        if (heal.enabled && pParty != nullptr && !pParty->needsHealing())
        {
            heal.enabled = false;
            heal.disabledReason = "Your party is already fully restored.";
        }

        options.push_back(std::move(heal));
        options.push_back(makeOption(
            HouseActionId::TempleDonate,
            "Donate " + std::to_string(templeDonationCost(houseEntry)) + " gold",
            isHouseOpenNow,
            closedReason
        ));
        return options;
    }

    if (isInnLikeHouse(houseEntry))
    {
        options.push_back(makeOption(
            HouseActionId::TavernRentRoom,
            "Rent room for " + std::to_string(tavernRoomCost(houseEntry)) + " gold",
            isHouseOpenNow,
            closedReason
        ));

        HouseActionOption food = makeOption(
            HouseActionId::TavernBuyFood,
            "Fill packs to " + std::to_string(TavernFoodTarget) + " days for "
                + std::to_string(tavernFoodCost(houseEntry)) + " gold",
            isHouseOpenNow,
            closedReason
        );

        if (food.enabled && pParty != nullptr && pParty->food() >= TavernFoodTarget)
        {
            food.enabled = false;
            food.disabledReason = "Your packs are already full enough.";
        }

        options.push_back(std::move(food));
        return options;
    }

    if (isHouseType(houseEntry, "Training"))
    {
        std::string label = "Train leader";

        if (pParty != nullptr && !pParty->members().empty())
        {
            const Character &leader = pParty->members().front();
            label = "Train " + leader.name
                + " to level " + std::to_string(leader.level + 1)
                + " for " + std::to_string(trainingCost(houseEntry, *pParty)) + " gold";
        }

        HouseActionOption train = makeOption(
            HouseActionId::TrainingTrainLeader,
            label,
            isHouseOpenNow,
            closedReason
        );

        if (train.enabled
            && pParty != nullptr
            && !pParty->members().empty()
            && houseEntry.trainingMaxLevel > 0
            && pParty->members().front().level >= static_cast<uint32_t>(houseEntry.trainingMaxLevel))
        {
            train.enabled = false;
            train.disabledReason = "This hall cannot train your leader any further.";
        }

        options.push_back(std::move(train));
        return options;
    }

    if (isHouseType(houseEntry, "Bank"))
    {
        HouseActionOption deposit = makeOption(
            HouseActionId::BankDepositAll,
            "Deposit all carried gold",
            isHouseOpenNow,
            closedReason
        );

        if (deposit.enabled && pParty != nullptr && pParty->gold() <= 0)
        {
            deposit.enabled = false;
            deposit.disabledReason = "You are not carrying any gold.";
        }

        HouseActionOption withdraw = makeOption(
            HouseActionId::BankWithdrawAll,
            "Withdraw all banked gold (" + std::to_string(pParty != nullptr ? pParty->bankGold() : 0) + ")",
            isHouseOpenNow,
            closedReason
        );

        if (withdraw.enabled && pParty != nullptr && pParty->bankGold() <= 0)
        {
            withdraw.enabled = false;
            withdraw.disabledReason = "You do not have any gold in the bank.";
        }

        options.push_back(std::move(deposit));
        options.push_back(std::move(withdraw));
    }

    return options;
}

bool performHouseAction(
    HouseActionId actionId,
    const HouseEntry &houseEntry,
    Party &party,
    OutdoorWorldRuntime *pOutdoorWorldRuntime,
    std::vector<std::string> &messages
)
{
    switch (actionId)
    {
        case HouseActionId::TempleHeal:
        {
            if (!party.needsHealing())
            {
                messages.push_back("The temple staff says your party is already well.");
                return false;
            }

            const int price = templeHealCost(houseEntry);

            if (party.gold() < price)
            {
                messages.push_back("You need " + std::to_string(price) + " gold for healing.");
                return false;
            }

            party.addGold(-price);
            party.restoreAll();
            messages.push_back("The temple restores the party for " + std::to_string(price) + " gold.");
            return true;
        }

        case HouseActionId::TempleDonate:
        {
            const int price = templeDonationCost(houseEntry);

            if (party.gold() < price)
            {
                messages.push_back("You need " + std::to_string(price) + " gold to donate here.");
                return false;
            }

            party.addGold(-price);
            messages.push_back("You donate " + std::to_string(price) + " gold at the temple.");
            return true;
        }

        case HouseActionId::TavernRentRoom:
        {
            const int price = tavernRoomCost(houseEntry);

            if (party.gold() < price)
            {
                messages.push_back("You need " + std::to_string(price) + " gold to rent a room.");
                return false;
            }

            party.addGold(-price);
            party.restoreAll();

            if (pOutdoorWorldRuntime != nullptr)
            {
                pOutdoorWorldRuntime->advanceGameMinutes(restDurationMinutes(pOutdoorWorldRuntime->currentHour()));
            }

            messages.push_back("The party rents a room, rests, and wakes up refreshed.");
            return true;
        }

        case HouseActionId::TavernBuyFood:
        {
            if (party.food() >= TavernFoodTarget)
            {
                messages.push_back("Your packs are already full enough.");
                return false;
            }

            const int price = tavernFoodCost(houseEntry);

            if (party.gold() < price)
            {
                messages.push_back("You need " + std::to_string(price) + " gold for provisions.");
                return false;
            }

            party.addGold(-price);
            party.addFood(TavernFoodTarget - party.food());
            messages.push_back("The innkeeper fills your packs to " + std::to_string(TavernFoodTarget) + " days.");
            return true;
        }

        case HouseActionId::TrainingTrainLeader:
        {
            if (party.members().empty())
            {
                messages.push_back("No party leader is available for training.");
                return false;
            }

            const int price = trainingCost(houseEntry, party);

            if (party.gold() < price)
            {
                messages.push_back("You need " + std::to_string(price) + " gold for training.");
                return false;
            }

            uint32_t newLevel = 0;
            uint32_t skillPointsEarned = 0;

            if (!party.trainLeader(
                    houseEntry.trainingMaxLevel > 0 ? static_cast<uint32_t>(houseEntry.trainingMaxLevel) : 0,
                    newLevel,
                    skillPointsEarned))
            {
                messages.push_back("This hall cannot train your leader any further.");
                return false;
            }

            party.addGold(-price);
            messages.push_back(
                party.members().front().name
                + " reaches level "
                + std::to_string(newLevel)
                + " and gains "
                + std::to_string(skillPointsEarned)
                + " skill points."
            );
            return true;
        }

        case HouseActionId::BankDepositAll:
        {
            const int depositedGold = party.depositAllGoldToBank();

            if (depositedGold <= 0)
            {
                messages.push_back("You are not carrying any gold.");
                return false;
            }

            messages.push_back("Deposited " + std::to_string(depositedGold) + " gold.");
            return true;
        }

        case HouseActionId::BankWithdrawAll:
        {
            const int withdrawnGold = party.withdrawAllBankGold();

            if (withdrawnGold <= 0)
            {
                messages.push_back("You do not have any gold in the bank.");
                return false;
            }

            messages.push_back("Withdrew " + std::to_string(withdrawnGold) + " gold.");
            return true;
        }
    }

    return false;
}
}
