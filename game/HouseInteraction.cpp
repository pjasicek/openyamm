#include "game/HouseInteraction.h"

#include "game/ClassSkillTable.h"
#include "game/OutdoorWorldRuntime.h"
#include "game/Party.h"
#include "game/SkillData.h"

#include <algorithm>
#include <cmath>
#include <unordered_set>

namespace OpenYAMM::Game
{
namespace
{
constexpr int RestTargetHour = 6;
constexpr int TavernFoodTarget = 14;
constexpr char SkillsMenuId[] = "skills";
constexpr char ShopEquipmentMenuId[] = "shop_equipment";
constexpr char TavernArcomageMenuId[] = "tavern_arcomage";

bool isHouseType(const HouseEntry &houseEntry, const char *pTypeName)
{
    return houseEntry.type == pTypeName;
}

const Character *selectedMember(const Party *pParty)
{
    return pParty != nullptr ? pParty->activeMember() : nullptr;
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

    return HouseServiceType::None;
}

std::vector<std::string> buildHouseServiceInfoLines(
    const HouseEntry &houseEntry,
    const Party *pParty,
    const ClassSkillTable *pClassSkillTable,
    const std::string &menuId
)
{
    std::vector<std::string> lines;
    const HouseServiceType serviceType = resolveHouseServiceType(houseEntry);

    if (menuId == SkillsMenuId)
    {
        lines.push_back(selectedMemberLine(pParty));

        if (pParty != nullptr)
        {
            lines.push_back(
                "Skill Cost: "
                + std::to_string(skillLearningCost(houseEntry, serviceType == HouseServiceType::Guild))
                + " gold"
            );
        }

        if (collectLearnableSkills(houseEntry, pParty, pClassSkillTable).empty())
        {
            lines.push_back("No skills are available here for this character.");
        }
    }
    else if (menuId == ShopEquipmentMenuId)
    {
        lines.push_back("Choose an equipment service.");
    }
    else if (menuId == TavernArcomageMenuId)
    {
        lines.push_back("Choose an Arcomage option.");
    }

    return lines;
}

std::vector<HouseActionOption> buildHouseActionOptions(
    const HouseEntry &houseEntry,
    const Party *pParty,
    const ClassSkillTable *pClassSkillTable,
    int currentHour,
    const std::string &menuId
)
{
    std::vector<HouseActionOption> options;
    const bool isHouseOpenNow = isHouseOpen(houseEntry, currentHour);
    const std::string closedReason = buildClosedReason(houseEntry);
    const HouseServiceType serviceType = resolveHouseServiceType(houseEntry);

    if (menuId == SkillsMenuId)
    {
        const int price = skillLearningCost(houseEntry, serviceType == HouseServiceType::Guild);

        for (const std::string &skillName : collectLearnableSkills(houseEntry, pParty, pClassSkillTable))
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

        options.push_back(makeOption(HouseActionId::BackToRootMenu, "Back", true, std::string {}));
        return options;
    }

    if (menuId == ShopEquipmentMenuId)
    {
        HouseActionOption sell = makeOption(HouseActionId::ShopSell, "Sell", isHouseOpenNow, closedReason);
        sell.enabled = false;
        sell.disabledReason = "Item commerce is not implemented yet.";
        options.push_back(std::move(sell));

        HouseActionOption identify = makeOption(HouseActionId::ShopIdentify, "Identify", isHouseOpenNow, closedReason);
        identify.enabled = false;
        identify.disabledReason = "Item identification is not implemented yet.";
        options.push_back(std::move(identify));

        if (!isHouseType(houseEntry, "Alchemist"))
        {
            HouseActionOption repair = makeOption(HouseActionId::ShopRepair, "Repair", isHouseOpenNow, closedReason);
            repair.enabled = false;
            repair.disabledReason = "Item repair is not implemented yet.";
            options.push_back(std::move(repair));
        }

        options.push_back(makeOption(HouseActionId::BackToRootMenu, "Back", true, std::string {}));
        return options;
    }

    if (menuId == TavernArcomageMenuId)
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
        play.enabled = false;
        play.disabledReason = "Arcomage play is not implemented yet.";
        options.push_back(std::move(play));

        options.push_back(makeOption(HouseActionId::BackToRootMenu, "Back", true, std::string {}));
        return options;
    }

    if (serviceType == HouseServiceType::Temple)
    {
        const Character *pMember = selectedMember(pParty);
        const std::string healLabel = pMember != nullptr
            ? ("Heal " + pMember->name + " for " + std::to_string(templeHealCost(houseEntry)) + " gold")
            : ("Heal for " + std::to_string(templeHealCost(houseEntry)) + " gold");
        HouseActionOption heal = makeOption(
            HouseActionId::TempleHeal,
            healLabel,
            isHouseOpenNow,
            closedReason
        );

        if (heal.enabled && pParty != nullptr && !pParty->activeMemberNeedsHealing())
        {
            heal.enabled = false;
            heal.disabledReason = "That character is already fully restored.";
        }

        options.push_back(std::move(heal));
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

        if (pParty != nullptr && pParty->activeMember() != nullptr)
        {
            const Character &member = *pParty->activeMember();
            label = "Train " + member.name
                + " to level " + std::to_string(member.level + 1)
                + " for " + std::to_string(trainingCost(houseEntry, *pParty)) + " gold";
        }

        HouseActionOption train = makeOption(
            HouseActionId::TrainingTrainActiveMember,
            label,
            isHouseOpenNow,
            closedReason
        );

        if (train.enabled
            && pParty != nullptr
            && pParty->activeMember() != nullptr
            && houseEntry.trainingMaxLevel > 0
            && pParty->activeMember()->level >= static_cast<uint32_t>(houseEntry.trainingMaxLevel))
        {
            train.enabled = false;
            train.disabledReason = "This hall cannot train that character any further.";
        }

        options.push_back(std::move(train));
        options.push_back(makeOption(HouseActionId::OpenLearnSkillsMenu, "Learn Skills", isHouseOpenNow, closedReason));
        return options;
    }

    if (serviceType == HouseServiceType::Bank)
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
        return options;
    }

    if (serviceType == HouseServiceType::Shop)
    {
        HouseActionOption buyStandard = makeOption(
            HouseActionId::ShopBuyStandard,
            "Buy Standard",
            isHouseOpenNow,
            closedReason
        );
        buyStandard.enabled = false;
        buyStandard.disabledReason = "Shop inventory is not implemented yet.";
        options.push_back(std::move(buyStandard));

        HouseActionOption buySpecial = makeOption(
            HouseActionId::ShopBuySpecial,
            "Buy Special",
            isHouseOpenNow,
            closedReason
        );
        buySpecial.enabled = false;
        buySpecial.disabledReason = "Special shop inventory is not implemented yet.";
        options.push_back(std::move(buySpecial));

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
        HouseActionOption spellbooks = makeOption(
            HouseActionId::GuildBuySpellbooks,
            "Buy Spellbooks",
            isHouseOpenNow,
            closedReason
        );
        spellbooks.enabled = false;
        spellbooks.disabledReason = "Spellbook buying is not implemented yet.";
        options.push_back(std::move(spellbooks));

        options.push_back(makeOption(HouseActionId::OpenLearnSkillsMenu, "Learn Skills", isHouseOpenNow, closedReason));
    }

    return options;
}

bool performHouseAction(
    const HouseActionOption &action,
    const HouseEntry &houseEntry,
    Party &party,
    const ClassSkillTable *pClassSkillTable,
    OutdoorWorldRuntime *pOutdoorWorldRuntime,
    std::vector<std::string> &messages
)
{
    switch (action.id)
    {
        case HouseActionId::TempleHeal:
        {
            Character *pMember = party.activeMember();

            if (pMember == nullptr)
            {
                messages.push_back("No character is selected.");
                return false;
            }

            if (!party.activeMemberNeedsHealing())
            {
                messages.push_back("The temple staff says " + pMember->name + " is already well.");
                return false;
            }

            const int price = templeHealCost(houseEntry);

            if (party.gold() < price)
            {
                messages.push_back("You need " + std::to_string(price) + " gold for healing.");
                return false;
            }

            party.addGold(-price);
            party.restoreActiveMember();
            messages.push_back("The temple restores " + pMember->name + " for " + std::to_string(price) + " gold.");
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

        case HouseActionId::TrainingTrainActiveMember:
        {
            Character *pMember = party.activeMember();

            if (pMember == nullptr)
            {
                messages.push_back("No character is selected for training.");
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

            if (!party.trainActiveMember(
                    houseEntry.trainingMaxLevel > 0 ? static_cast<uint32_t>(houseEntry.trainingMaxLevel) : 0,
                    newLevel,
                    skillPointsEarned))
            {
                messages.push_back("This hall cannot train that character any further.");
                return false;
            }

            party.addGold(-price);
            messages.push_back(
                pMember->name
                + " reaches level "
                + std::to_string(newLevel)
                + " and gains "
                + std::to_string(skillPointsEarned)
                + " skill points."
            );
            return true;
        }

        case HouseActionId::LearnSkill:
        {
            if (action.argument.empty() || pClassSkillTable == nullptr)
            {
                messages.push_back("That lesson is not available.");
                return false;
            }

            Character *pMember = party.activeMember();

            if (pMember == nullptr)
            {
                messages.push_back("No character is selected.");
                return false;
            }

            if (!party.canActiveMemberLearnSkill(action.argument))
            {
                messages.push_back(pMember->name + " cannot learn " + displaySkillName(action.argument) + " here.");
                return false;
            }

            const int price = skillLearningCost(
                houseEntry,
                resolveHouseServiceType(houseEntry) == HouseServiceType::Guild
            );

            if (party.gold() < price)
            {
                messages.push_back("You need " + std::to_string(price) + " gold for that lesson.");
                return false;
            }

            if (!party.learnActiveMemberSkill(action.argument))
            {
                messages.push_back("That lesson is not available.");
                return false;
            }

            party.addGold(-price);
            messages.push_back(
                pMember->name
                + " learns "
                + displaySkillName(action.argument)
                + " for "
                + std::to_string(price)
                + " gold."
            );
            return true;
        }

        case HouseActionId::ShopBuyStandard:
        case HouseActionId::ShopBuySpecial:
        case HouseActionId::ShopSell:
        case HouseActionId::ShopIdentify:
        case HouseActionId::ShopRepair:
        case HouseActionId::GuildBuySpellbooks:
        {
            messages.push_back("This service is not implemented yet.");
            return false;
        }

        case HouseActionId::TavernArcomageRules:
        {
            messages.push_back("Arcomage uses the house deck. Build your tower, destroy theirs, or win on resources.");
            return false;
        }

        case HouseActionId::TavernArcomageVictoryConditions:
        {
            messages.push_back("Arcomage victory conditions depend on the inn. This tavern flow is not implemented yet.");
            return false;
        }

        case HouseActionId::TavernArcomagePlay:
        {
            messages.push_back("Arcomage play is not implemented yet.");
            return false;
        }

        case HouseActionId::OpenLearnSkillsMenu:
        case HouseActionId::OpenShopEquipmentMenu:
        case HouseActionId::OpenTavernArcomageMenu:
        case HouseActionId::BackToRootMenu:
        {
            return false;
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
