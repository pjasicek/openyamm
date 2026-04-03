#include "game/gameplay/HouseInteraction.h"

#include "game/tables/ClassSkillTable.h"
#include "game/gameplay/HouseServiceRuntime.h"
#include "game/outdoor/OutdoorWorldRuntime.h"
#include "game/party/Party.h"
#include "game/items/PriceCalculator.h"
#include "game/party/SkillData.h"

#include <algorithm>
#include <cmath>
#include <unordered_set>

namespace OpenYAMM::Game
{
namespace
{
constexpr int RestTargetHour = 6;
constexpr int TavernFoodTarget = 14;
constexpr int MinutesPerDay = 24 * 60;

int minuteOfDayFromGameMinutes(float currentGameMinutes)
{
    int minuteOfDay = static_cast<int>(std::floor(currentGameMinutes));
    minuteOfDay %= MinutesPerDay;

    if (minuteOfDay < 0)
    {
        minuteOfDay += MinutesPerDay;
    }

    return minuteOfDay;
}

int dayOfWeekFromGameMinutes(float currentGameMinutes)
{
    int day = static_cast<int>(std::floor(currentGameMinutes / static_cast<float>(MinutesPerDay)));
    day %= 7;

    if (day < 0)
    {
        day += 7;
    }

    return day;
}

std::string amPmSuffixForHour(int hour24)
{
    const int normalizedHour = ((hour24 % 24) + 24) % 24;
    return normalizedHour >= 12 ? "PM" : "AM";
}

int displayHourAmPm(int hour24)
{
    const int normalizedHour = ((hour24 % 24) + 24) % 24;
    const int hour12 = normalizedHour % 12;
    return hour12 == 0 ? 12 : hour12;
}

bool isHouseType(const HouseEntry &houseEntry, const char *pTypeName)
{
    return houseEntry.type == pTypeName;
}

const Character *selectedMember(const Party *pParty)
{
    return pParty != nullptr ? pParty->activeMember() : nullptr;
}

bool isTransportHouseType(const HouseEntry &houseEntry)
{
    return isHouseType(houseEntry, "Stables") || isHouseType(houseEntry, "Boats");
}

bool isBoatHouse(const HouseEntry &houseEntry)
{
    return isHouseType(houseEntry, "Boats");
}

bool routeQBitSatisfied(
    const HouseEntry::TransportRoute &route,
    const OutdoorWorldRuntime *pOutdoorWorldRuntime)
{
    if (route.requiredQBit == 0)
    {
        return true;
    }

    if (pOutdoorWorldRuntime == nullptr)
    {
        return false;
    }

    const EventRuntimeState *pEventRuntimeState = pOutdoorWorldRuntime->eventRuntimeState();

    if (pEventRuntimeState == nullptr)
    {
        return false;
    }

    const auto it = pEventRuntimeState->variables.find(route.requiredQBit);
    return it != pEventRuntimeState->variables.end() && it->second != 0;
}

bool routeAvailableToday(const HouseEntry::TransportRoute &route, float currentGameMinutes)
{
    if (currentGameMinutes < 0.0f)
    {
        return true;
    }

    return route.daysAvailable[dayOfWeekFromGameMinutes(currentGameMinutes)];
}

const HouseEntry::TransportRoute *findTransportRoute(const HouseEntry &houseEntry, const std::string &argument)
{
    if (argument.empty())
    {
        return nullptr;
    }

    const uint32_t routeIndex = static_cast<uint32_t>(std::strtoul(argument.c_str(), nullptr, 10));

    for (const HouseEntry::TransportRoute &route : houseEntry.transportRoutes)
    {
        if (route.routeIndex == routeIndex)
        {
            return &route;
        }
    }

    return nullptr;
}

}

bool isHouseOpenAtGameMinute(const HouseEntry &houseEntry, float currentGameMinutes)
{
    if (currentGameMinutes < 0.0f || houseEntry.openHour == houseEntry.closeHour)
    {
        return true;
    }

    const int currentMinuteOfDay = minuteOfDayFromGameMinutes(currentGameMinutes);
    const int openMinuteOfDay = std::max(0, houseEntry.openHour) * 60;
    const int closeMinuteOfDay = std::max(0, houseEntry.closeHour) * 60;

    if (houseEntry.openHour < houseEntry.closeHour)
    {
        return currentMinuteOfDay >= openMinuteOfDay && currentMinuteOfDay <= closeMinuteOfDay;
    }

    return currentMinuteOfDay >= openMinuteOfDay || currentMinuteOfDay <= closeMinuteOfDay;
}

std::string buildClosedStatusText(const HouseEntry &houseEntry)
{
    return "This place is open from "
        + std::to_string(displayHourAmPm(houseEntry.openHour))
        + amPmSuffixForHour(houseEntry.openHour)
        + " to "
        + std::to_string(displayHourAmPm(houseEntry.closeHour))
        + amPmSuffixForHour(houseEntry.closeHour);
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

int skillLearningCost(const HouseEntry &houseEntry, bool isGuild)
{
    const float multiplier = isGuild ? houseEntry.priceMultiplier : houseEntry.skillPriceMultiplier;
    return roundPrice(multiplier, 500, 1);
}

int trainingCost(const HouseEntry &houseEntry, const Party &party)
{
    const Character *pMember = party.activeMember();
    const uint32_t level = pMember != nullptr ? pMember->level : 1;
    const int scaledCost = static_cast<int>(level) * roundPrice(houseEntry.priceMultiplier, 10, 5);
    return std::max(10, scaledCost);
}

uint64_t experienceRequiredForNextLevel(uint32_t currentLevel)
{
    return 1000ull * currentLevel * (currentLevel + 1) / 2;
}

std::optional<uint64_t> trainingExperienceShortfall(const Character &member)
{
    const uint64_t requiredExperience = experienceRequiredForNextLevel(member.level);

    if (member.experience >= requiredExperience)
    {
        return std::nullopt;
    }

    return requiredExperience - member.experience;
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

std::vector<std::string> collectLearnableSkills(
    const HouseEntry &houseEntry,
    const Party *pParty,
    const ClassSkillTable *pClassSkillTable
)
{
    std::vector<std::string> skills;

    if (pParty == nullptr || pClassSkillTable == nullptr)
    {
        return skills;
    }

    const Character *pMember = pParty->activeMember();

    if (pMember == nullptr)
    {
        return skills;
    }

    std::unordered_set<std::string> seenSkills;

    for (const std::string &offeredSkill : houseEntry.offeredSkills)
    {
        const std::string canonicalSkill = canonicalSkillName(offeredSkill);

        if (canonicalSkill.empty() || seenSkills.contains(canonicalSkill))
        {
            continue;
        }

        seenSkills.insert(canonicalSkill);

        if (pMember->hasSkill(canonicalSkill))
        {
            continue;
        }

        if (pClassSkillTable->getClassCap(pMember->className, canonicalSkill) == SkillMastery::None)
        {
            continue;
        }

        skills.push_back(canonicalSkill);
    }

    std::sort(skills.begin(), skills.end());
    return skills;
}

std::string selectedMemberLine(const Party *pParty)
{
    const Character *pMember = selectedMember(pParty);

    if (pMember == nullptr)
    {
        return "Selected: no character";
    }

    return "Selected: " + pMember->name + " the " + pMember->role;
}

std::string houseWelcomeLine(const HouseEntry &houseEntry)
{
    return "Welcome to " + houseEntry.name;
}

HouseServiceType resolveHouseServiceType(const HouseEntry &houseEntry)
{
    if (isHouseType(houseEntry, "Weapon Shop")
        || isHouseType(houseEntry, "Armor Shop")
        || isHouseType(houseEntry, "Magic Shop")
        || isHouseType(houseEntry, "Alchemist"))
    {
        return HouseServiceType::Shop;
    }

    if (isHouseType(houseEntry, "Temple"))
    {
        return HouseServiceType::Temple;
    }

    if (isHouseType(houseEntry, "Bank"))
    {
        return HouseServiceType::Bank;
    }

    if (isHouseType(houseEntry, "Tavern"))
    {
        return HouseServiceType::Tavern;
    }

    if (isHouseType(houseEntry, "Training"))
    {
        return HouseServiceType::TrainingHall;
    }

    if (isHouseType(houseEntry, "Elemental Guild")
        || isHouseType(houseEntry, "Light Guild")
        || isHouseType(houseEntry, "Dark Guild")
        || isHouseType(houseEntry, "Self Guild")
        || isHouseType(houseEntry, "Spell Shop"))
    {
        return HouseServiceType::Guild;
    }

    if (isTransportHouseType(houseEntry))
    {
        return HouseServiceType::Transport;
    }

    return HouseServiceType::None;
}

std::optional<uint32_t> deriveHouseSoundId(const HouseEntry &houseEntry, HouseSoundType soundType)
{
    if (houseEntry.roomSoundId == 0 || soundType == HouseSoundType::None)
    {
        return std::nullopt;
    }

    return static_cast<uint32_t>(soundType) + 100u * (houseEntry.roomSoundId + 300u);
}

std::vector<std::string> buildHouseServiceInfoLines(
    const HouseEntry &houseEntry,
    const Party *pParty,
    const ClassSkillTable *pClassSkillTable,
    DialogueMenuId menuId
)
{
    std::vector<std::string> lines;
    const HouseServiceType serviceType = resolveHouseServiceType(houseEntry);

    if (serviceType == HouseServiceType::Bank && menuId == DialogueMenuId::None)
    {
        lines.push_back("Balance: " + std::to_string(pParty != nullptr ? pParty->bankGold() : 0));
        return lines;
    }

    if (menuId == DialogueMenuId::LearnSkills)
    {
        if (collectLearnableSkills(houseEntry, pParty, pClassSkillTable).empty())
        {
            lines.push_back(std::string {});
            lines.push_back("No skills are available here for this character.");
        }
    }
    else if (menuId == DialogueMenuId::TavernArcomage)
    {
        lines.push_back(std::string {});
        lines.push_back("Choose an Arcomage option.");
    }

    return lines;
}

std::vector<HouseActionOption> buildHouseActionOptions(
    const HouseEntry &houseEntry,
    const Party *pParty,
    const ClassSkillTable *pClassSkillTable,
    const OutdoorWorldRuntime *pOutdoorWorldRuntime,
    float currentGameMinutes,
    DialogueMenuId menuId
)
{
    std::vector<HouseActionOption> options;
    const bool isHouseOpenNow = isHouseOpenAtGameMinute(houseEntry, currentGameMinutes);
    const std::string closedReason = buildClosedStatusText(houseEntry);
    const HouseServiceType serviceType = resolveHouseServiceType(houseEntry);

    if (menuId == DialogueMenuId::LearnSkills)
    {
        const int price = skillLearningCost(houseEntry, serviceType == HouseServiceType::Guild);
        const std::vector<std::string> learnableSkills = collectLearnableSkills(houseEntry, pParty, pClassSkillTable);

        for (const std::string &skillName : learnableSkills)
        {
            HouseActionOption learn = makeOption(
                HouseActionId::LearnSkill,
                "Learn " + displaySkillName(skillName) + " for " + std::to_string(price) + " gold",
                isHouseOpenNow,
                closedReason
            );
            learn.argument = skillName;
            options.push_back(std::move(learn));
        }

        if (learnableSkills.empty())
        {
            HouseActionOption noSkills = makeOption(
                HouseActionId::LearnSkill,
                "No skills are available here for this character.",
                true,
                std::string {}
            );
            noSkills.enabled = false;
            options.push_back(std::move(noSkills));
        }

        return options;
    }

    if (menuId == DialogueMenuId::ShopEquipment)
    {
        HouseActionOption sell = makeOption(HouseActionId::ShopSell, "Sell", isHouseOpenNow, closedReason);

        if (sell.enabled && !HouseServiceRuntime::supportsEquipmentSell(houseEntry))
        {
            sell.enabled = false;
            sell.disabledReason = "This house does not buy equipment.";
        }

        options.push_back(std::move(sell));

        HouseActionOption identify = makeOption(HouseActionId::ShopIdentify, "Identify", isHouseOpenNow, closedReason);

        if (identify.enabled && !HouseServiceRuntime::supportsIdentify(houseEntry))
        {
            identify.enabled = false;
            identify.disabledReason = "This house cannot identify items.";
        }

        options.push_back(std::move(identify));

        if (!isHouseType(houseEntry, "Alchemist"))
        {
            HouseActionOption repair = makeOption(HouseActionId::ShopRepair, "Repair", isHouseOpenNow, closedReason);

            if (repair.enabled && !HouseServiceRuntime::supportsRepair(houseEntry))
            {
                repair.enabled = false;
                repair.disabledReason = "This house cannot repair items.";
            }

            options.push_back(std::move(repair));
        }

        return options;
    }

    if (menuId == DialogueMenuId::TavernArcomage)
    {
        HouseActionOption rules = makeOption(
            HouseActionId::TavernArcomageRules,
            "Rules",
            isHouseOpenNow,
            closedReason
        );
        options.push_back(std::move(rules));

        HouseActionOption victory = makeOption(
            HouseActionId::TavernArcomageVictoryConditions,
            "Victory Conditions",
            isHouseOpenNow,
            closedReason
        );
        options.push_back(std::move(victory));

        HouseActionOption play = makeOption(
            HouseActionId::TavernArcomagePlay,
            "Play",
            isHouseOpenNow,
            closedReason
        );
        options.push_back(std::move(play));

        return options;
    }

    if (serviceType == HouseServiceType::Temple)
    {
        if (pParty == nullptr || pParty->activeMemberNeedsHealing())
        {
            options.push_back(makeOption(
                HouseActionId::TempleHeal,
                "Heal " + std::to_string(templeHealCost(houseEntry)) + " gold",
                isHouseOpenNow,
                closedReason
            ));
        }

        options.push_back(makeOption(
            HouseActionId::TempleDonate,
            "Donate " + std::to_string(templeDonationCost(houseEntry)) + " gold",
            isHouseOpenNow,
            closedReason
        ));
        options.push_back(makeOption(HouseActionId::OpenLearnSkillsMenu, "Learn Skills", isHouseOpenNow, closedReason));
        return options;
    }

    if (serviceType == HouseServiceType::Tavern)
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
        options.push_back(makeOption(HouseActionId::OpenLearnSkillsMenu, "Learn Skills", isHouseOpenNow, closedReason));
        options.push_back(makeOption(HouseActionId::OpenTavernArcomageMenu, "Play Arcomage", isHouseOpenNow, closedReason));
        return options;
    }

    if (serviceType == HouseServiceType::TrainingHall)
    {
        std::string label = "Train";
        bool trainingAvailable = true;
        std::string trainingUnavailableReason;

        if (pParty != nullptr && pParty->activeMember() != nullptr)
        {
            const Character &member = *pParty->activeMember();

            if (houseEntry.trainingMaxLevel > 0
                && member.level >= static_cast<uint32_t>(houseEntry.trainingMaxLevel))
            {
                label = "With your skills, you should be working here as a teacher\n\n"
                    "Sorry, but we are unable to train you.";
                trainingAvailable = false;
                trainingUnavailableReason = label;
            }
            else if (const std::optional<uint64_t> experienceShortfall = trainingExperienceShortfall(member))
            {
                label = "You need "
                    + std::to_string(*experienceShortfall)
                    + " more experience to train to level "
                    + std::to_string(member.level + 1);
                trainingAvailable = false;
                trainingUnavailableReason = label;
            }
            else
            {
                label = "Train to level "
                    + std::to_string(member.level + 1)
                    + " for "
                    + std::to_string(trainingCost(houseEntry, *pParty))
                    + " gold";
            }
        }

        HouseActionOption train = makeOption(
            HouseActionId::TrainingTrainActiveMember,
            label,
            isHouseOpenNow,
            closedReason
        );

        if (train.enabled && !trainingAvailable)
        {
            train.enabled = false;
            train.disabledReason = trainingUnavailableReason;
        }

        options.push_back(std::move(train));
        options.push_back(makeOption(HouseActionId::OpenLearnSkillsMenu, "Learn Skills", isHouseOpenNow, closedReason));
        return options;
    }

    if (serviceType == HouseServiceType::Bank)
    {
        HouseActionOption deposit = makeOption(HouseActionId::BankDepositAll, "Deposit", isHouseOpenNow, closedReason);
        HouseActionOption withdraw = makeOption(
            HouseActionId::BankWithdrawAll,
            "Withdraw",
            isHouseOpenNow,
            closedReason);

        options.push_back(std::move(deposit));
        options.push_back(std::move(withdraw));
        return options;
    }

    if (serviceType == HouseServiceType::Shop)
    {
        options.push_back(makeOption(HouseActionId::ShopBuyStandard, "Buy Standard", isHouseOpenNow, closedReason));
        options.push_back(makeOption(HouseActionId::ShopBuySpecial, "Buy Special", isHouseOpenNow, closedReason));

        options.push_back(makeOption(
            HouseActionId::OpenShopEquipmentMenu,
            "Display Equipment",
            isHouseOpenNow,
            closedReason
        ));
        options.push_back(makeOption(HouseActionId::OpenLearnSkillsMenu, "Learn Skills", isHouseOpenNow, closedReason));
        return options;
    }

    if (serviceType == HouseServiceType::Guild)
    {
        options.push_back(makeOption(
            HouseActionId::GuildBuySpellbooks,
            "Buy Spellbooks",
            isHouseOpenNow,
            closedReason
        ));

        options.push_back(makeOption(HouseActionId::OpenLearnSkillsMenu, "Learn Skills", isHouseOpenNow, closedReason));
        return options;
    }

    if (serviceType == HouseServiceType::Transport)
    {
        const Character *pMember = selectedMember(pParty);
        bool anyRouteVisible = false;
        bool anyRouteSkippedForDay = false;

        for (const HouseEntry::TransportRoute &route : houseEntry.transportRoutes)
        {
            if (!routeQBitSatisfied(route, pOutdoorWorldRuntime))
            {
                continue;
            }

            if (!routeAvailableToday(route, currentGameMinutes))
            {
                anyRouteSkippedForDay = true;
                continue;
            }

            anyRouteVisible = true;
            const int price = PriceCalculator::transportPrice(pMember, houseEntry, isBoatHouse(houseEntry));
            HouseActionOption transport = makeOption(
                HouseActionId::TransportRoute,
                "Travel to " + route.destinationName + " for " + std::to_string(price) + " gold",
                isHouseOpenNow,
                closedReason
            );
            transport.argument = std::to_string(route.routeIndex);
            options.push_back(std::move(transport));
        }

        if (!anyRouteVisible && anyRouteSkippedForDay)
        {
            HouseActionOption noRoute = {};
            noRoute.id = HouseActionId::TransportRoute;
            noRoute.label = "Sorry, come back another day";
            noRoute.enabled = false;
            noRoute.disabledReason = "Sorry, come back another day";
            options.push_back(std::move(noRoute));
        }
    }

    return options;
}

HouseActionResult performHouseAction(
    const HouseActionOption &action,
    const HouseEntry &houseEntry,
    Party &party,
    const ClassSkillTable *pClassSkillTable,
    OutdoorWorldRuntime *pOutdoorWorldRuntime
)
{
    HouseActionResult result = {};

    switch (action.id)
    {
        case HouseActionId::TempleHeal:
        {
            Character *pMember = party.activeMember();

            if (pMember == nullptr)
            {
                result.messages.push_back("No character is selected.");
                return result;
            }

            if (!party.activeMemberNeedsHealing())
            {
                result.messages.push_back("The temple staff says " + pMember->name + " is already well.");
                return result;
            }

            const int price = templeHealCost(houseEntry);

            if (party.gold() < price)
            {
                result.messages.push_back("You need " + std::to_string(price) + " gold for healing.");
                result.soundType = HouseSoundType::GeneralNotEnoughGold;
                return result;
            }

            party.addGold(-price);
            if (Character *pHealedMember = party.activeMember())
            {
                pHealedMember->health = pHealedMember->maxHealth;
                pHealedMember->spellPoints = pHealedMember->maxSpellPoints;
                pHealedMember->conditions.reset();
            }
            result.messages.push_back(
                "The temple restores " + pMember->name + " for " + std::to_string(price) + " gold.");
            result.succeeded = true;
            return result;
        }

        case HouseActionId::TempleDonate:
        {
            const int price = templeDonationCost(houseEntry);

            if (party.gold() < price)
            {
                result.messages.push_back("You need " + std::to_string(price) + " gold to donate here.");
                return result;
            }

            party.addGold(-price);
            result.messages.push_back("Thank You");
            result.succeeded = true;
            return result;
        }

        case HouseActionId::TavernRentRoom:
        {
            const int price = tavernRoomCost(houseEntry);

            if (party.gold() < price)
            {
                result.messages.push_back("You need " + std::to_string(price) + " gold to rent a room.");
                result.soundType = HouseSoundType::TavernNotEnoughGold;
                return result;
            }

            party.addGold(-price);
            party.restAndHealAll();

            if (pOutdoorWorldRuntime != nullptr)
            {
                pOutdoorWorldRuntime->advanceGameMinutes(restDurationMinutes(pOutdoorWorldRuntime->currentHour()));
            }

            result.messages.push_back("The party rents a room, rests, and wakes up refreshed.");
            result.succeeded = true;
            result.soundType = HouseSoundType::TavernRentRoom;
            return result;
        }

        case HouseActionId::TavernBuyFood:
        {
            if (party.food() >= TavernFoodTarget)
            {
                result.messages.push_back("Your packs are already full enough.");
                return result;
            }

            const int price = tavernFoodCost(houseEntry);

            if (party.gold() < price)
            {
                result.messages.push_back("You need " + std::to_string(price) + " gold for provisions.");
                result.soundType = HouseSoundType::TavernNotEnoughGold;
                return result;
            }

            party.addGold(-price);
            party.addFood(TavernFoodTarget - party.food());
            result.messages.push_back("The innkeeper fills your packs to " + std::to_string(TavernFoodTarget) + " days.");
            result.succeeded = true;
            result.soundType = HouseSoundType::TavernBuyFood;
            return result;
        }

        case HouseActionId::TrainingTrainActiveMember:
        {
            Character *pMember = party.activeMember();

            if (pMember == nullptr)
            {
                result.messages.push_back("No character is selected for training.");
                return result;
            }

            const int price = trainingCost(houseEntry, party);

            if (houseEntry.trainingMaxLevel > 0
                && pMember->level >= static_cast<uint32_t>(houseEntry.trainingMaxLevel))
            {
                result.messages.push_back(
                    "With your skills, you should be working here as a teacher\n\n"
                    "Sorry, but we are unable to train you."
                );
                result.soundType = HouseSoundType::TrainingCantTrain;
                return result;
            }

            if (const std::optional<uint64_t> experienceShortfall = trainingExperienceShortfall(*pMember))
            {
                result.messages.push_back(
                    "You need "
                    + std::to_string(*experienceShortfall)
                    + " more experience to train to level "
                    + std::to_string(pMember->level + 1)
                );
                result.soundType = HouseSoundType::TrainingCantTrain;
                return result;
            }

            if (party.gold() < price)
            {
                result.messages.push_back("You need " + std::to_string(price) + " gold for training.");
                result.soundType = HouseSoundType::TrainingNotEnoughGold;
                return result;
            }

            uint32_t newLevel = 0;
            uint32_t skillPointsEarned = 0;

            if (!party.trainActiveMember(
                    houseEntry.trainingMaxLevel > 0 ? static_cast<uint32_t>(houseEntry.trainingMaxLevel) : 0,
                    newLevel,
                    skillPointsEarned))
            {
                result.messages.push_back("Training is not available right now.");
                result.soundType = HouseSoundType::TrainingCantTrain;
                return result;
            }

            party.addGold(-price);
            result.messages.push_back(
                pMember->name
                + " is now level "
                + std::to_string(newLevel)
                + " and has earned "
                + std::to_string(skillPointsEarned)
                + " skill points!"
            );
            result.succeeded = true;
            result.soundType = HouseSoundType::TrainingTrain;
            return result;
        }

        case HouseActionId::LearnSkill:
        {
            if (action.argument.empty() || pClassSkillTable == nullptr)
            {
                result.messages.push_back("That lesson is not available.");
                return result;
            }

            Character *pMember = party.activeMember();

            if (pMember == nullptr)
            {
                result.messages.push_back("No character is selected.");
                return result;
            }

            if (!party.canActiveMemberLearnSkill(action.argument))
            {
                result.messages.push_back(
                    pMember->name + " cannot learn " + displaySkillName(action.argument) + " here.");
                return result;
            }

            const int price = skillLearningCost(
                houseEntry,
                resolveHouseServiceType(houseEntry) == HouseServiceType::Guild
            );

            if (party.gold() < price)
            {
                result.messages.push_back("You don't have enough gold.");
                result.soundType = HouseSoundType::GeneralNotEnoughGold;
                return result;
            }

            if (!party.learnActiveMemberSkill(action.argument))
            {
                result.messages.push_back("That lesson is not available.");
                return result;
            }

            party.addGold(-price);
            result.messages.push_back(
                pMember->name
                + " learns "
                + displaySkillName(action.argument)
                + " for "
                + std::to_string(price)
                + " gold."
            );
            result.succeeded = true;
            return result;
        }

        case HouseActionId::ShopBuyStandard:
        case HouseActionId::ShopBuySpecial:
        case HouseActionId::ShopSell:
        case HouseActionId::ShopIdentify:
        case HouseActionId::ShopRepair:
        case HouseActionId::GuildBuySpellbooks:
        {
            result.messages.push_back("This service is not implemented yet.");
            return result;
        }

        case HouseActionId::TransportRoute:
        {
            const HouseEntry::TransportRoute *pRoute = findTransportRoute(houseEntry, action.argument);

            if (pRoute == nullptr)
            {
                result.messages.push_back("That route is not available.");
                return result;
            }

            if (pOutdoorWorldRuntime == nullptr)
            {
                result.messages.push_back("Travel is unavailable right now.");
                return result;
            }

            if (!routeQBitSatisfied(*pRoute, pOutdoorWorldRuntime))
            {
                result.messages.push_back("That route is not available.");
                return result;
            }

            if (!routeAvailableToday(*pRoute, pOutdoorWorldRuntime->gameMinutes()))
            {
                result.messages.push_back("Sorry, come back another day");
                return result;
            }

            const Character *pMember = party.activeMember();
            const int price = PriceCalculator::transportPrice(pMember, houseEntry, isBoatHouse(houseEntry));

            if (party.gold() < price)
            {
                result.messages.push_back("You don't have enough gold.");
                result.soundType = HouseSoundType::TransportNotEnoughGold;
                return result;
            }

            EventRuntimeState *pEventRuntimeState = pOutdoorWorldRuntime->eventRuntimeState();

            if (pEventRuntimeState == nullptr)
            {
                result.messages.push_back("Travel is unavailable right now.");
                return result;
            }

            party.addGold(-price);
            party.restAndHealAll();
            pOutdoorWorldRuntime->advanceGameMinutes(static_cast<float>(pRoute->travelDays * MinutesPerDay));

            EventRuntimeState::PendingMapMove pendingMapMove = {};
            pendingMapMove.mapName = pRoute->mapFileName;
            pendingMapMove.x = pRoute->x;
            pendingMapMove.y = pRoute->y;
            pendingMapMove.z = pRoute->z;
            pendingMapMove.directionDegrees = pRoute->directionDegrees;
            pendingMapMove.useMapStartPosition = pRoute->useMapStartPosition;
            pEventRuntimeState->pendingMapMove = std::move(pendingMapMove);

            result.messages.push_back(
                "It will take "
                + std::to_string(pRoute->travelDays)
                + " days to travel to "
                + pRoute->destinationName
                + "."
            );
            result.succeeded = true;
            result.soundType = HouseSoundType::TransportTravel;
            return result;
        }

        case HouseActionId::TavernArcomageRules:
        {
            result.messages.push_back(
                "Arcomage uses the house deck. Build your tower, destroy theirs, or win on resources.");
            return result;
        }

        case HouseActionId::TavernArcomageVictoryConditions:
        {
            result.messages.push_back(
                "Arcomage victory conditions depend on the inn. This tavern flow is not implemented yet.");
            return result;
        }

        case HouseActionId::TavernArcomagePlay:
        {
            result.messages.push_back("Arcomage play is not implemented yet.");
            return result;
        }

        case HouseActionId::OpenLearnSkillsMenu:
        case HouseActionId::OpenShopEquipmentMenu:
        case HouseActionId::OpenTavernArcomageMenu:
        case HouseActionId::BackToRootMenu:
        {
            return result;
        }

        case HouseActionId::BankDepositAll:
        {
            const int depositedGold = party.depositAllGoldToBank();

            if (depositedGold <= 0)
            {
                result.messages.push_back("You are not carrying any gold.");
                return result;
            }

            result.messages.push_back("Deposited " + std::to_string(depositedGold) + " gold.");
            result.succeeded = true;
            return result;
        }

        case HouseActionId::BankWithdrawAll:
        {
            const int withdrawnGold = party.withdrawAllBankGold();

            if (withdrawnGold <= 0)
            {
                result.messages.push_back("You do not have any gold in the bank.");
                return result;
            }

            result.messages.push_back("Withdrew " + std::to_string(withdrawnGold) + " gold.");
            result.succeeded = true;
            return result;
        }
    }

    return result;
}
}
