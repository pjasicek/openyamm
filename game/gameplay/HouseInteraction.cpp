#include "game/gameplay/HouseInteraction.h"

#include "game/debug/GameplayDebugTrace.h"
#include "game/gameplay/BountyHuntRuntime.h"
#include "game/gameplay/GameMechanics.h"
#include "game/events/EvtEnums.h"
#include "game/tables/ClassSkillTable.h"
#include "game/gameplay/HouseServiceRuntime.h"
#include "game/gameplay/NpcFollowerRuntime.h"
#include "game/gameplay/ReputationRuntime.h"
#include "game/gameplay/TrainerDirectory.h"
#include "game/party/SpellIds.h"
#include "game/rules/GameRules.h"
#include "game/rules/SpellRules.h"
#include "game/party/Party.h"
#include "game/items/PriceCalculator.h"
#include "game/party/SkillData.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <functional>
#include <random>
#include <unordered_set>

namespace OpenYAMM::Game
{
namespace
{
constexpr int MinutesPerDay = 24 * 60;
// Waiting for a stable's or boat's departure eats one food a day, about what waiting until morning and resting
// costs (user, 2026-11-04).
constexpr int TransportWaitFoodPerDay = 1;
constexpr uint32_t LorettaPriceQuestBit = 1140;
constexpr uint32_t LorettaPriceCompleteBit = 1141;
constexpr uint32_t LorettaFirstStableBit = 1515;
constexpr uint32_t LorettaLastStableBit = 1523;
constexpr uint32_t FreeHavenHighCouncilHouseId = 209;
constexpr int MMergeBadReputationShopBanThreshold = 25;
constexpr int ShopTheftBanDays = 336;
constexpr float PrisonSentenceMinutes = 365.0f * 24.0f * 60.0f;
constexpr uint32_t ArcomageDeckItemId = 1453;
constexpr uint32_t FirstAntagarichArcomageTavernHouseId = 239;
constexpr uint32_t LastAntagarichArcomageTavernHouseId = 252;
constexpr uint32_t Mm7PitTrainingHouseId = 1575;
constexpr uint32_t Mm7MountNighonTrainingHouseId = 1576;
constexpr uint32_t OeMm7PitTrainingHouseId = 94;
constexpr uint32_t OeMm7MountNighonTrainingHouseId = 95;
constexpr uint32_t PrisonTermsAwardId = 87;
constexpr uint32_t DeyjaTavernHouseId = 243;
constexpr uint32_t PitTavernHouseId = 246;
constexpr uint32_t MountNighonTavernHouseId = 248;
constexpr const char *pArcomageDeckRequiredMessage = "You must have your own card deck to play here.";
constexpr const char *pLorettaPriceFixingLabel = "Price Fixing";
constexpr const char *pLorettaPriceFixingMessage =
    "Well, If Loretta's got a new scheme, count me in!\n"
    "But you better get all the other companies to sign up!";

int effectiveReputationForWorld(const IGameplayWorldRuntime *pWorldRuntime);

// A tavern fills the packs to the house's Val in days, the same value that scales its prices.
int tavernFoodTarget(const HouseEntry &houseEntry)
{
    return static_cast<int>(houseEntry.priceMultiplier);
}

bool tavernDrinkMakesPartyDrunk()
{
    static thread_local std::mt19937 rng(std::random_device{}());
    return std::uniform_int_distribution<int>(1, 4)(rng) == 1;
}

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

float minutesUntilNextDawn(float currentGameMinutes)
{
    constexpr int DawnMinuteOfDay = 5 * 60;

    int minutesUntilDawn = DawnMinuteOfDay - minuteOfDayFromGameMinutes(currentGameMinutes);

    if (minutesUntilDawn <= 0)
    {
        minutesUntilDawn += MinutesPerDay;
    }

    return static_cast<float>(minutesUntilDawn);
}

bool trainingHouseUsesExtendedOeTrainingTime(const HouseEntry &houseEntry)
{
    return houseEntry.id == Mm7PitTrainingHouseId
        || houseEntry.id == Mm7MountNighonTrainingHouseId
        || houseEntry.id == OeMm7PitTrainingHouseId
        || houseEntry.id == OeMm7MountNighonTrainingHouseId
        || houseEntry.name == "Perdition's Flame"
        || houseEntry.name == "Applied Instruction";
}

float oeTrainingDurationMinutes(const HouseEntry &houseEntry, float currentGameMinutes)
{
    float durationMinutes = 7.0f * static_cast<float>(MinutesPerDay)
        + minutesUntilNextDawn(currentGameMinutes)
        + 4.0f * 60.0f;

    if (trainingHouseUsesExtendedOeTrainingTime(houseEntry))
    {
        durationMinutes += 12.0f * 60.0f;
    }

    return durationMinutes;
}

bool recordOeTrainingLevel(
    EventRuntimeState::DialogueRuntimeState &dialogueState,
    uint32_t houseId,
    size_t activeMemberIndex,
    size_t memberCount)
{
    if (dialogueState.trainingHouseId != houseId)
    {
        dialogueState.trainingHouseId = houseId;
        dialogueState.trainingLevelsByMember.assign(memberCount, 0);
    }
    else if (dialogueState.trainingLevelsByMember.size() != memberCount)
    {
        dialogueState.trainingLevelsByMember.resize(memberCount, 0);
    }

    const uint32_t maximumBefore = dialogueState.trainingLevelsByMember.empty()
        ? 0
        : *std::max_element(
            dialogueState.trainingLevelsByMember.begin(),
            dialogueState.trainingLevelsByMember.end());
    ++dialogueState.trainingLevelsByMember[activeMemberIndex];
    const uint32_t maximumAfter = *std::max_element(
        dialogueState.trainingLevelsByMember.begin(),
        dialogueState.trainingLevelsByMember.end());
    return maximumAfter > maximumBefore;
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

int dayOfMonthFromGameMinutes(float currentGameMinutes)
{
    const int totalMinutes = std::max(0, static_cast<int>(std::floor(currentGameMinutes)));
    const int totalDays = totalMinutes / MinutesPerDay;
    return 1 + totalDays % 28;
}

uint32_t templeSpellLevelFromGameMinutes(float currentGameMinutes)
{
    return static_cast<uint32_t>(dayOfMonthFromGameMinutes(currentGameMinutes) % 7 + 1);
}

std::string shopBanUntilVar(uint32_t houseId)
{
    return "MMerge.ShopBanUntil." + std::to_string(houseId);
}

bool isFreeHavenHighCouncil(const HouseEntry &houseEntry)
{
    return houseEntry.id == FreeHavenHighCouncilHouseId;
}

bool houseServiceSubjectToReputationBan(HouseServiceType serviceType)
{
    return serviceType == HouseServiceType::Shop
        || serviceType == HouseServiceType::Guild
        || serviceType == HouseServiceType::TrainingHall
        || serviceType == HouseServiceType::Tavern
        || serviceType == HouseServiceType::Bank;
}

bool houseHasActiveTheftBan(
    const HouseEntry &houseEntry,
    const IGameplayWorldRuntime *pWorldRuntime,
    float currentGameMinutes)
{
    const EventRuntimeState *pEventRuntimeState =
        pWorldRuntime != nullptr ? pWorldRuntime->eventRuntimeState() : nullptr;

    if (pEventRuntimeState == nullptr)
    {
        return false;
    }

    const auto iterator = pEventRuntimeState->namedGlobalVars.find(shopBanUntilVar(houseEntry.id));
    return iterator != pEventRuntimeState->namedGlobalVars.end()
        && iterator->second > static_cast<int32_t>(std::floor(currentGameMinutes));
}

bool houseRefusesServiceForReputation(
    const HouseEntry &houseEntry,
    HouseServiceType serviceType,
    const IGameplayWorldRuntime *pWorldRuntime,
    float currentGameMinutes)
{
    if (!houseServiceSubjectToReputationBan(serviceType))
    {
        return false;
    }

    return houseHasActiveTheftBan(houseEntry, pWorldRuntime, currentGameMinutes)
        || effectiveReputationForWorld(pWorldRuntime) >= MMergeBadReputationShopBanThreshold;
}

void disableHouseOptionsForReputation(std::vector<HouseActionOption> &options, const std::string &reason)
{
    for (HouseActionOption &option : options)
    {
        option.enabled = false;
        option.disabledReason = reason;
    }
}

// A dead, stoned, unconscious, asleep or paralysed character cannot train or take lessons (OE
// GUIWindow_House::checkIfPlayerCanInteract).
std::string noConditionToActText(const Character &member)
{
    return member.name + " is in no condition to do anything";
}

int templeDonationTriggerIndexFromGameMinutes(float currentGameMinutes)
{
    return dayOfMonthFromGameMinutes(currentGameMinutes) % 7;
}

void castTempleDonationSpell(
    IGameplayWorldRuntime &worldRuntime,
    Party &party,
    uint32_t spellId,
    uint32_t spellLevel)
{
    // The party's rules may hold the blessing as the temple's (MAW); the event cast still shows it.
    party.rules().spells.castSourceBuff(party, spellId, BuffSource::Temple);
    worldRuntime.castEventSpell(
        spellId,
        spellLevel,
        static_cast<uint32_t>(SkillMastery::Master),
        0,
        0,
        0,
        0,
        0,
        0);
}

void tryApplyTempleDonationBuffs(
    IGameplayWorldRuntime &worldRuntime,
    Party &party,
    EventRuntimeState::DialogueRuntimeState &dialogueState,
    size_t activeMemberIndex)
{
    if (activeMemberIndex >= dialogueState.templeDonationCounters.size())
    {
        return;
    }

    const uint8_t counter = dialogueState.templeDonationCounters[activeMemberIndex] % 7;

    if (counter != templeDonationTriggerIndexFromGameMinutes(worldRuntime.gameMinutes()))
    {
        return;
    }

    const uint32_t spellLevel = templeSpellLevelFromGameMinutes(worldRuntime.gameMinutes());
    const int reputation = worldRuntime.currentLocationReputation();

    if (reputation <= -5)
    {
        castTempleDonationSpell(worldRuntime, party, spellIdValue(SpellId::Bless), spellLevel);
    }

    if (reputation <= -10)
    {
        castTempleDonationSpell(worldRuntime, party, spellIdValue(SpellId::Preservation), spellLevel);
    }

    if (reputation <= -15)
    {
        castTempleDonationSpell(worldRuntime, party, spellIdValue(SpellId::ProtectionFromMagic), spellLevel);
    }

    if (reputation <= -20)
    {
        castTempleDonationSpell(worldRuntime, party, spellIdValue(SpellId::HourOfPower), spellLevel);
    }

    if (reputation <= -25)
    {
        castTempleDonationSpell(worldRuntime, party, spellIdValue(SpellId::DayOfProtection), spellLevel);
    }
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

uint16_t guildMembershipPartyVariableId(uint32_t guildType)
{
    constexpr uint16_t GuildMembershipPartyVariableBase = 0x8000u;
    return static_cast<uint16_t>(GuildMembershipPartyVariableBase | static_cast<uint16_t>(guildType));
}

uint32_t guildMembershipRuntimeVariableKey(uint32_t guildType)
{
    constexpr uint32_t GuildMembershipVariableBase = 0x80000000u;
    return GuildMembershipVariableBase | guildType;
}

std::optional<uint32_t> skillGuildMembershipType(const HouseEntry &houseEntry)
{
    if (houseEntry.name == "Buccaneers' Lair")
    {
        return 16;
    }

    if (houseEntry.name == "Protection Services")
    {
        return 17;
    }

    if (houseEntry.name == "Smugglers' Guild")
    {
        return 18;
    }

    if (houseEntry.name == "Blades' End")
    {
        return 19;
    }

    if (houseEntry.name == "Duelists' Edge")
    {
        return 20;
    }

    if (houseEntry.name == "Berserkers' Fury")
    {
        return 21;
    }

    return std::nullopt;
}

// MMerge StdQuestsFunctions.lua (DrawLearnTopics, DrawShopTopics): magic guild house types 5-15 need membership on
// Enroth and Antagarich, except Antagarich's Light and Dark guilds, which its light/dark path gates instead. Jadame's
// guilds are always open.
std::optional<uint32_t> magicGuildMembershipType(const HouseEntry &houseEntry)
{
    struct Mapping
    {
        const char *pType;
        uint32_t guildType;
    };

    constexpr std::array<Mapping, 11> mappings = {{
        {"Fire Guild", 5},
        {"Air Guild", 6},
        {"Water Guild", 7},
        {"Earth Guild", 8},
        {"Spirit Guild", 9},
        {"Mind Guild", 10},
        {"Body Guild", 11},
        {"Light Guild", 12},
        {"Dark Guild", 13},
        {"Elemental Guild", 14},
        {"Self Guild", 15},
    }};
    constexpr uint32_t LightGuildType = 12;
    constexpr uint32_t DarkGuildType = 13;
    const bool antagarich = houseEntry.worldId == "mm7";
    const bool enroth = houseEntry.worldId == "mm6";

    if (!antagarich && !enroth)
    {
        return std::nullopt;
    }

    for (const Mapping &mapping : mappings)
    {
        if (houseEntry.type != mapping.pType)
        {
            continue;
        }

        if (antagarich && (mapping.guildType == LightGuildType || mapping.guildType == DarkGuildType))
        {
            return std::nullopt;
        }

        return mapping.guildType;
    }

    return std::nullopt;
}

std::optional<uint32_t> requiredGuildMembershipType(const HouseEntry &houseEntry)
{
    const std::optional<uint32_t> skillGuildType = skillGuildMembershipType(houseEntry);
    return skillGuildType.has_value() ? skillGuildType : magicGuildMembershipType(houseEntry);
}

bool isSkillGuildHouse(const HouseEntry &houseEntry)
{
    return skillGuildMembershipType(houseEntry).has_value();
}

bool requiresGuildMembership(const HouseEntry &houseEntry)
{
    return requiredGuildMembershipType(houseEntry).has_value();
}

bool hasGuildMembership(
    const HouseEntry &houseEntry,
    const Party *pParty,
    const IGameplayWorldRuntime *pWorldRuntime)
{
    const std::optional<uint32_t> guildType = requiredGuildMembershipType(houseEntry);

    if (!guildType.has_value())
    {
        return true;
    }

    if (pParty != nullptr && pParty->eventVariableValue(guildMembershipPartyVariableId(*guildType)) != 0)
    {
        return true;
    }

    const EventRuntimeState *pEventRuntimeState =
        pWorldRuntime != nullptr ? pWorldRuntime->eventRuntimeState() : nullptr;

    if (pEventRuntimeState == nullptr)
    {
        return false;
    }

    const auto membershipIt = pEventRuntimeState->variables.find(guildMembershipRuntimeVariableKey(*guildType));
    return membershipIt != pEventRuntimeState->variables.end() && membershipIt->second != 0;
}

const Character *selectedMember(const Party *pParty)
{
    return pParty != nullptr ? pParty->activeMember() : nullptr;
}

const Character *partyMerchantMember(const Party *pParty)
{
    if (const Character *pRulesMerchant = pParty != nullptr ? PriceCalculator::rulesMerchantMember(*pParty) : nullptr)
    {
        return pRulesMerchant;
    }

    const Character *pMerchant = pParty != nullptr ? pParty->bestPartyWideUtilitySkillMember("Merchant") : nullptr;
    return pMerchant != nullptr ? pMerchant : selectedMember(pParty);
}

bool isTransportHouseType(const HouseEntry &houseEntry)
{
    return isHouseType(houseEntry, "Stables") || isHouseType(houseEntry, "Boats");
}

int effectiveReputationForWorld(const IGameplayWorldRuntime *pWorldRuntime)
{
    return pWorldRuntime != nullptr
        ? effectivePartyReputation(pWorldRuntime->currentLocationReputation(), pWorldRuntime->eventRuntimeState())
        : 0;
}

bool isTempleOfBaa(const HouseEntry &houseEntry)
{
    return isHouseType(houseEntry, "Temple") && houseEntry.name.find("Baa") != std::string::npos;
}

}

bool isBoatHouse(const HouseEntry &houseEntry)
{
    return isHouseType(houseEntry, "Boats");
}

bool isAlchemyShop(const HouseEntry &houseEntry)
{
    return isHouseType(houseEntry, "Alchemist");
}

bool houseRefusesShopServiceForReputation(
    const HouseEntry &houseEntry,
    const IGameplayWorldRuntime *pWorldRuntime,
    float currentGameMinutes)
{
    return resolveHouseServiceType(houseEntry) == HouseServiceType::Shop
        && houseRefusesServiceForReputation(
            houseEntry,
            HouseServiceType::Shop,
            pWorldRuntime,
            currentGameMinutes);
}

HouseShopGoodbyeResult resolveHouseShopGoodbyeResult(
    const HouseEntry &houseEntry,
    bool transactionPerformed,
    bool shopBanned,
    int partyGold)
{
    HouseShopGoodbyeResult result = {};

    if (resolveHouseServiceType(houseEntry) != HouseServiceType::Shop)
    {
        return result;
    }

    if (isAlchemyShop(houseEntry))
    {
        if (shopBanned)
        {
            result.queueRudeSpeech = true;
            return result;
        }

        result.soundType = transactionPerformed
            ? HouseSoundType::AlchemyShopGoodbyeBought
            : HouseSoundType::AlchemyShopGoodbyeRegular;
        return result;
    }

    if (shopBanned)
    {
        result.queueRudeSpeech = true;
        return result;
    }

    if (partyGold <= 10000)
    {
        if (transactionPerformed)
        {
            result.soundType = HouseSoundType::ShopGoodbyePolite;
        }

        return result;
    }

    if (transactionPerformed)
    {
        result.soundType = HouseSoundType::ShopGoodbyePolite;
    }
    else
    {
        result.soundType = HouseSoundType::ShopGoodbyeRude;
        result.queueRudeSpeech = true;
    }

    return result;
}

uint32_t arcomageDeckItemId()
{
    return ArcomageDeckItemId;
}

const char *arcomageDeckRequiredMessage()
{
    return pArcomageDeckRequiredMessage;
}

bool partyHasArcomageDeck(const Party *pParty)
{
    return pParty != nullptr && pParty->hasItemAnywhere(ArcomageDeckItemId);
}

bool houseRequiresArcomageDeck(const HouseEntry &houseEntry)
{
    return houseEntry.id >= FirstAntagarichArcomageTavernHouseId
        && houseEntry.id <= LastAntagarichArcomageTavernHouseId;
}

bool partyCanPlayArcomageInHouse(const HouseEntry &houseEntry, const Party *pParty)
{
    return !houseRequiresArcomageDeck(houseEntry) || partyHasArcomageDeck(pParty);
}

bool routeQBitSatisfied(
    const HouseEntry::TransportRoute &route,
    const IGameplayWorldRuntime *pWorldRuntime)
{
    if (route.requiredQBit == 0)
    {
        return true;
    }

    if (pWorldRuntime == nullptr)
    {
        return false;
    }

    const Party *pParty = pWorldRuntime->party();
    return pParty != nullptr && pParty->hasQuestBit(route.requiredQBit);
}

bool routeAvailableToday(const HouseEntry::TransportRoute &route, float currentGameMinutes)
{
    if (currentGameMinutes < 0.0f)
    {
        return true;
    }

    return route.daysAvailable[dayOfWeekFromGameMinutes(currentGameMinutes)];
}

int adjustedTransportTravelDays(
    const HouseEntry::TransportRoute &route,
    const EventRuntimeState *pEventRuntimeState,
    bool stable)
{
    const int baseDays = route.travelDays == 0 ? 1 : static_cast<int>(route.travelDays);
    const int reduction = pEventRuntimeState != nullptr
        ? hiredNpcTransportDayReduction(*pEventRuntimeState, stable)
        : 0;

    return std::max(1, baseDays - reduction);
}

std::string transportTravelDaysText(int travelDays)
{
    return std::to_string(travelDays) + (travelDays == 1 ? " day" : " days");
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

HouseEntry::TransportRoute effectiveTransportRoute(
    const HouseEntry &houseEntry,
    const HouseEntry::TransportRoute &baseRoute,
    const EventRuntimeState *pEventRuntimeState)
{
    if (pEventRuntimeState == nullptr)
    {
        return baseRoute;
    }

    const uint64_t key = EventRuntime::transportRouteOverrideKey(houseEntry.id, baseRoute.routeIndex);
    const auto iterator = pEventRuntimeState->transportRouteOverrides.find(key);

    if (iterator == pEventRuntimeState->transportRouteOverrides.end())
    {
        return baseRoute;
    }

    const EventRuntimeState::TransportRouteOverride &overrideRoute = iterator->second;
    HouseEntry::TransportRoute route = baseRoute;
    route.destinationName = overrideRoute.destinationName.empty()
        ? baseRoute.destinationName
        : overrideRoute.destinationName;
    route.mapFileName = overrideRoute.mapFileName.empty() ? baseRoute.mapFileName : overrideRoute.mapFileName;
    route.daysAvailable = overrideRoute.daysAvailable;
    route.travelDays = overrideRoute.travelDays == 0 ? baseRoute.travelDays : overrideRoute.travelDays;
    route.x = overrideRoute.x;
    route.y = overrideRoute.y;
    route.z = overrideRoute.z;
    route.directionDegrees = overrideRoute.directionDegrees;
    route.requiredQBit = overrideRoute.requiredQBit;
    route.useMapStartPosition = overrideRoute.useMapStartPosition;
    return route;
}

float innRestDurationMinutes(uint32_t houseId, float currentGameMinutes)
{
    // An inn room lasts until an hour after dawn; the Deyja, Pit and Mount Nighon inns add twelve hours.
    float durationMinutes = minutesUntilNextDawn(currentGameMinutes) + 60.0f;

    if (houseId == DeyjaTavernHouseId || houseId == PitTavernHouseId || houseId == MountNighonTavernHouseId)
    {
        durationMinutes += 12.0f * 60.0f;
    }

    return durationMinutes;
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

std::optional<uint32_t> lorettaStableQuestBitForHouse(uint32_t houseId)
{
    switch (houseId)
    {
        case 477:
            return 1515;
        case 478:
            return 1516;
        case 476:
            return 1517;
        case 472:
            return 1518;
        case 473:
            return 1519;
        case 474:
            return 1520;
        case 475:
            return 1521;
        case 471:
            return 1522;
        case 470:
            return 1523;
        default:
            return std::nullopt;
    }
}

bool shouldShowLorettaPriceFixing(const HouseEntry &houseEntry, const Party *pParty)
{
    if (pParty == nullptr || houseEntry.type != "Stables")
    {
        return false;
    }

    const std::optional<uint32_t> stableQuestBit = lorettaStableQuestBitForHouse(houseEntry.id);

    return stableQuestBit.has_value()
        && pParty->hasQuestBit(LorettaPriceQuestBit)
        && !pParty->hasQuestBit(*stableQuestBit);
}

int roundPrice(float multiplier, int scale, int minimumPrice)
{
    const int scaledPrice = static_cast<int>(std::round(multiplier * static_cast<float>(scale)));
    return std::max(minimumPrice, scaledPrice);
}

float templeConditionHealingTier(CharacterCondition condition)
{
    switch (condition)
    {
        case CharacterCondition::Eradicated:
        case CharacterCondition::Zombie:
            return 2.5f;

        case CharacterCondition::Dead:
        case CharacterCondition::Petrified:
            return 2.0f;

        case CharacterCondition::Asleep:
        case CharacterCondition::PoisonMedium:
        case CharacterCondition::DiseaseMedium:
        case CharacterCondition::PoisonSevere:
        case CharacterCondition::DiseaseSevere:
        case CharacterCondition::Paralyzed:
        case CharacterCondition::Unconscious:
            return 1.5f;

        case CharacterCondition::Cursed:
        case CharacterCondition::Weak:
        case CharacterCondition::Fear:
        case CharacterCondition::Drunk:
        case CharacterCondition::Insane:
        case CharacterCondition::PoisonWeak:
        case CharacterCondition::DiseaseWeak:
        default:
            return 1.0f;
    }
}

bool templeCanTreatCondition(const HouseEntry &houseEntry, CharacterCondition condition)
{
    if (houseEntry.templeHealingTier <= 0.0f)
    {
        return true;
    }

    return houseEntry.templeHealingTier + 0.001f >= templeConditionHealingTier(condition);
}

bool templeCanTreatActiveMemberNeed(const HouseEntry &houseEntry, const Character &member)
{
    bool hasCondition = false;

    for (size_t conditionIndex = 0; conditionIndex < CharacterConditionCount; ++conditionIndex)
    {
        if (!member.conditions.test(conditionIndex))
        {
            continue;
        }

        hasCondition = true;
        if (!templeCanTreatCondition(houseEntry, static_cast<CharacterCondition>(conditionIndex)))
        {
            return false;
        }
    }

    return hasCondition
        || member.health < Party::effectiveMaximumHealth(member)
        || member.spellPoints < Party::effectiveMaximumSpellPoints(member);
}

bool activeMemberNeedsTempleHealing(const Party &party, const HouseEntry &houseEntry)
{
    const Character *pMember = party.activeMember();
    return pMember != nullptr && templeCanTreatActiveMemberNeed(houseEntry, *pMember);
}

int templeHealCost(const HouseEntry &houseEntry, const Character *pMember)
{
    return PriceCalculator::templeHealPrice(pMember, houseEntry);
}

int templeDonationCost(const HouseEntry &houseEntry)
{
    return roundPrice(houseEntry.priceMultiplier, 1, 1);
}

int skillLearningCost(
    const HouseEntry &houseEntry,
    const Party *pParty,
    bool isGuild,
    int effectiveReputation = 0)
{
    return PriceCalculator::skillLearningPrice(
        partyMerchantMember(pParty),
        houseEntry,
        isGuild,
        effectiveReputation);
}

int trainingCost(const HouseEntry &houseEntry, const Party &party, int effectiveReputation = 0)
{
    // The rules may price the hall by the trainee (MAW's Insanity).
    HouseEntry pricedHouse = houseEntry;
    const Character *pTrainee = party.activeMember();

    if (pTrainee != nullptr)
    {
        pricedHouse.priceMultiplier =
            party.rules().skills.trainingPriceMultiplier(*pTrainee, houseEntry.priceMultiplier);
    }

    return PriceCalculator::trainingPrice(pTrainee, partyMerchantMember(&party), pricedHouse, effectiveReputation);
}

std::optional<uint64_t> trainingExperienceShortfall(const Party &party, const Character &member)
{
    const uint64_t requiredExperience = party.rules().experience.experienceForNextLevel(member.level);

    if (member.experience >= requiredExperience)
    {
        return std::nullopt;
    }

    return requiredExperience - member.experience;
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
    std::vector<std::string> offeredSkills = houseEntry.offeredSkills;
    const std::vector<std::string> extraSkills = pParty->rules().skills.extraHouseSkills(houseEntry.type);
    offeredSkills.insert(offeredSkills.end(), extraSkills.begin(), extraSkills.end());

    for (const std::string &offeredSkill : offeredSkills)
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

        if (pClassSkillTable->getEffectiveCap(pMember->className, pMember->raceId, canonicalSkill)
            == SkillMastery::None)
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

    return "Selected: " + pMember->name + " the " + pParty->rules().classes.displayName(*pParty, *pMember);
}

std::string houseWelcomeLine(const HouseEntry &houseEntry)
{
    return "Welcome to " + houseEntry.name;
}

HouseServiceType resolveHouseServiceType(const HouseEntry &houseEntry)
{
    if (houseEntry.vendorStockProfile != VendorStockProfile::None)
    {
        return HouseServiceType::Shop;
    }

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
        || isHouseType(houseEntry, "Fire Guild")
        || isHouseType(houseEntry, "Air Guild")
        || isHouseType(houseEntry, "Water Guild")
        || isHouseType(houseEntry, "Earth Guild")
        || isHouseType(houseEntry, "Spirit Guild")
        || isHouseType(houseEntry, "Mind Guild")
        || isHouseType(houseEntry, "Body Guild")
        || isHouseType(houseEntry, "Spell Shop")
        || isHouseType(houseEntry, "Thieves guild")
        || isHouseType(houseEntry, "Merc Guild"))
    {
        return HouseServiceType::Guild;
    }

    if (isTransportHouseType(houseEntry))
    {
        return HouseServiceType::Transport;
    }

    if (isHouseType(houseEntry, "Town Hall"))
    {
        return HouseServiceType::TownHall;
    }

    return HouseServiceType::None;
}

HouseSoundType houseEntrySoundType(
    const HouseEntry &houseEntry,
    const Party *pParty,
    const IGameplayWorldRuntime *pWorldRuntime)
{
    // Only magic guilds greet a non-member with their members-only line (OpenEnroth UIHouses.cpp).
    if (magicGuildMembershipType(houseEntry).has_value() && !hasGuildMembership(houseEntry, pParty, pWorldRuntime))
    {
        return HouseSoundType::MagicGuildMembersOnly;
    }

    return HouseSoundType::GeneralGreeting;
}

std::optional<uint32_t> deriveHouseSoundId(const HouseEntry &houseEntry, HouseSoundType soundType)
{
    if (soundType == HouseSoundType::None)
    {
        return std::nullopt;
    }

    if (houseEntry.houseSoundBaseId != 0)
    {
        return houseEntry.houseSoundBaseId + static_cast<uint32_t>(soundType);
    }

    if (houseEntry.roomSoundId == 0)
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

    if (requiresGuildMembership(houseEntry)
        && menuId == DialogueMenuId::None
        && !hasGuildMembership(houseEntry, pParty, nullptr))
    {
        lines.push_back("You must be a member of this guild to study here.");
        return lines;
    }

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
    else if (menuId == DialogueMenuId::TeacherLedger)
    {
        const std::optional<uint32_t> continent = tavernTeacherLedgerContinent(houseEntry, pParty);

        if (continent)
        {
            const TeacherLedgerSettings &ledger = pParty->trainerDirectory()->ledger();
            lines.push_back(ledger.fill(ledger.description, trainerContinentName(*continent)));
        }
    }
    else if (menuId == DialogueMenuId::TavernArcomage)
    {
        lines.push_back(std::string {});

        if (partyCanPlayArcomageInHouse(houseEntry, pParty))
        {
            lines.push_back("Choose an Arcomage option.");
        }
        else
        {
            lines.push_back(arcomageDeckRequiredMessage());
        }
    }

    return lines;
}

std::vector<HouseActionOption> finalizeHouseActionOptions(
    const HouseEntry &houseEntry,
    HouseServiceType serviceType,
    DialogueMenuId menuId,
    const Party *pParty,
    const IGameplayWorldRuntime *pWorldRuntime,
    float currentGameMinutes,
    std::vector<HouseActionOption> options);

TransportSchedule buildTransportSchedule(
    const HouseEntry &houseEntry,
    const Party *pParty,
    const IGameplayWorldRuntime *pWorldRuntime)
{
    TransportSchedule schedule;
    const EventRuntimeState *pEventRuntimeState =
        pWorldRuntime != nullptr ? pWorldRuntime->eventRuntimeState() : nullptr;
    const bool boat = isBoatHouse(houseEntry);
    schedule.today = pWorldRuntime != nullptr ? dayOfWeekFromGameMinutes(pWorldRuntime->gameMinutes()) : 0;
    schedule.fare = PriceCalculator::transportPrice(
        partyMerchantMember(pParty),
        houseEntry,
        boat,
        effectiveReputationForWorld(pWorldRuntime));
    schedule.foodPerWaitDay = TransportWaitFoodPerDay;

    for (const HouseEntry::TransportRoute &baseRoute : houseEntry.transportRoutes)
    {
        const HouseEntry::TransportRoute route = effectiveTransportRoute(houseEntry, baseRoute, pEventRuntimeState);

        if (!routeQBitSatisfied(route, pWorldRuntime))
        {
            continue;
        }

        TransportScheduleRoute entry;
        entry.routeIndex = route.routeIndex;
        entry.destinationName = route.destinationName;
        entry.daysAvailable = route.daysAvailable;
        entry.travelDays = adjustedTransportTravelDays(route, pEventRuntimeState, !boat);
        schedule.routes.push_back(std::move(entry));
    }

    return schedule;
}

std::optional<uint32_t> tavernTeacherLedgerContinent(const HouseEntry &houseEntry, const Party *pParty)
{
    if (pParty == nullptr || pParty->trainerDirectory() == nullptr
        || resolveHouseServiceType(houseEntry) != HouseServiceType::Tavern)
    {
        return std::nullopt;
    }

    const std::optional<uint32_t> continent = pParty->trainerDirectory()->mapContinent(houseEntry.mapId);

    if (!continent || trainerContinentName(*continent).empty() || pParty->hasTeacherLedger(*continent))
    {
        return std::nullopt;
    }

    return continent;
}

int transportWaitDays(int today, int departureDay)
{
    return ((departureDay - today) % 7 + 7) % 7;
}

std::string transportScheduledTripArgument(uint32_t routeIndex, int departureDay)
{
    return std::to_string(routeIndex) + ":" + std::to_string(departureDay);
}

std::vector<HouseActionOption> buildHouseActionOptions(
    const HouseEntry &houseEntry,
    const Party *pParty,
    const ClassSkillTable *pClassSkillTable,
    const IGameplayWorldRuntime *pWorldRuntime,
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
        const int price = skillLearningCost(
            houseEntry,
            pParty,
            serviceType == HouseServiceType::Guild,
            effectiveReputationForWorld(pWorldRuntime));
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

        return finalizeHouseActionOptions(houseEntry, serviceType, menuId, pParty, pWorldRuntime, currentGameMinutes, std::move(options));
    }

    if (menuId == DialogueMenuId::ShopEquipment)
    {
        const bool isExplicitVendor = houseEntry.vendorStockProfile != VendorStockProfile::None;
        if (!isExplicitVendor || HouseServiceRuntime::supportsEquipmentSell(houseEntry))
        {
            HouseActionOption sell = makeOption(HouseActionId::ShopSell, "Sell", isHouseOpenNow, closedReason);

            if (sell.enabled && !HouseServiceRuntime::supportsEquipmentSell(houseEntry))
            {
                sell.enabled = false;
                sell.disabledReason = "This house does not buy equipment.";
            }

            options.push_back(std::move(sell));
        }

        if (!isExplicitVendor || HouseServiceRuntime::supportsIdentify(houseEntry))
        {
            HouseActionOption identify = makeOption(
                HouseActionId::ShopIdentify,
                "Identify",
                isHouseOpenNow,
                closedReason);

            if (identify.enabled && !HouseServiceRuntime::supportsIdentify(houseEntry))
            {
                identify.enabled = false;
                identify.disabledReason = "This house cannot identify items.";
            }

            options.push_back(std::move(identify));
        }

        if ((!isExplicitVendor && !isHouseType(houseEntry, "Alchemist"))
            || (isExplicitVendor && HouseServiceRuntime::supportsRepair(houseEntry)))
        {
            HouseActionOption repair = makeOption(HouseActionId::ShopRepair, "Repair", isHouseOpenNow, closedReason);

            if (repair.enabled && !HouseServiceRuntime::supportsRepair(houseEntry))
            {
                repair.enabled = false;
                repair.disabledReason = "This house cannot repair items.";
            }

            options.push_back(std::move(repair));
        }

        return finalizeHouseActionOptions(houseEntry, serviceType, menuId, pParty, pWorldRuntime, currentGameMinutes, std::move(options));
    }

    if (menuId == DialogueMenuId::TeacherLedger)
    {
        if (const std::optional<uint32_t> continent = tavernTeacherLedgerContinent(houseEntry, pParty))
        {
            const TeacherLedgerSettings &ledger = pParty->trainerDirectory()->ledger();
            HouseActionOption buy = makeOption(HouseActionId::BuyTeacherLedger,
                ledger.fill(ledger.buy, trainerContinentName(*continent)), isHouseOpenNow, closedReason);
            buy.argument = std::to_string(*continent);
            options.push_back(std::move(buy));
        }

        return finalizeHouseActionOptions(
            houseEntry, serviceType, menuId, pParty, pWorldRuntime, currentGameMinutes, std::move(options));
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

        if (partyCanPlayArcomageInHouse(houseEntry, pParty))
        {
            HouseActionOption play = makeOption(
                HouseActionId::TavernArcomagePlay,
                "Play",
                isHouseOpenNow,
                closedReason
            );
            options.push_back(std::move(play));
        }

        return finalizeHouseActionOptions(houseEntry, serviceType, menuId, pParty, pWorldRuntime, currentGameMinutes, std::move(options));
    }

    if (houseEntry.extraExit.has_value()
        && (houseEntry.extraExit->requiredQuestBit == 0
            || (pParty != nullptr && pParty->hasQuestBit(houseEntry.extraExit->requiredQuestBit))))
    {
        options.push_back(makeOption(
            HouseActionId::ExtraExit,
            houseEntry.extraExit->label,
            true,
            std::string {}
        ));
    }

    if (serviceType == HouseServiceType::Temple)
    {
        const Character *pMember = pParty != nullptr ? pParty->activeMember() : nullptr;

        if (houseEntry.templeCanHeal
            && (pParty == nullptr || activeMemberNeedsTempleHealing(*pParty, houseEntry)))
        {
            options.push_back(makeOption(
                HouseActionId::TempleHeal,
                "Heal " + std::to_string(templeHealCost(houseEntry, pMember)) + " gold",
                isHouseOpenNow,
                closedReason
            ));
        }

        if (houseEntry.templeCanDonate)
        {
            options.push_back(makeOption(
                HouseActionId::TempleDonate,
                "Donate " + std::to_string(templeDonationCost(houseEntry)) + " gold",
                isHouseOpenNow,
                closedReason
            ));
        }
        if (houseEntry.serviceCanLearnSkills)
        {
            options.push_back(makeOption(
                HouseActionId::OpenLearnSkillsMenu,
                "Learn Skills",
                isHouseOpenNow,
                closedReason));
        }
        return finalizeHouseActionOptions(houseEntry, serviceType, menuId, pParty, pWorldRuntime, currentGameMinutes, std::move(options));
    }

    if (serviceType == HouseServiceType::Tavern)
    {
        const Character *pMember = partyMerchantMember(pParty);

        options.push_back(makeOption(
            HouseActionId::TavernRentRoom,
            "Rent room for "
                + std::to_string(PriceCalculator::tavernRoomPrice(
                    pMember,
                    houseEntry,
                    effectiveReputationForWorld(pWorldRuntime)))
                + " gold",
            isHouseOpenNow,
            closedReason
        ));

        const int foodTarget = tavernFoodTarget(houseEntry);
        HouseActionOption food = makeOption(
            HouseActionId::TavernBuyFood,
            "Fill packs to " + std::to_string(foodTarget) + " days for "
                + std::to_string(PriceCalculator::tavernFoodPrice(
                    pMember,
                    houseEntry,
                    effectiveReputationForWorld(pWorldRuntime))) + " gold",
            isHouseOpenNow,
            closedReason
        );

        if (food.enabled && pParty != nullptr && pParty->food() >= foodTarget)
        {
            food.enabled = false;
            food.disabledReason = "Your packs are already full enough.";
        }

        options.push_back(std::move(food));

        // A tavern whose skill cell says none (HouseEntry::teachesNothing) has no lessons to offer.
        if (!houseEntry.teachesNothing)
        {
            options.push_back(
                makeOption(HouseActionId::OpenLearnSkillsMenu, "Learn Skills", isHouseOpenNow, closedReason));
        }

        if (houseEntry.arcomageRule.has_value())
        {
            options.push_back(makeOption(
                HouseActionId::OpenTavernArcomageMenu,
                "Play Arcomage",
                isHouseOpenNow,
                closedReason));
        }

        // The continent's Ledger of Teachers, until the party has it.
        if (tavernTeacherLedgerContinent(houseEntry, pParty))
        {
            options.push_back(makeOption(HouseActionId::OpenTeacherLedgerMenu,
                pParty->trainerDirectory()->ledger().topic, isHouseOpenNow, closedReason));
        }

        return finalizeHouseActionOptions(houseEntry, serviceType, menuId, pParty, pWorldRuntime, currentGameMinutes, std::move(options));
    }

    if (serviceType == HouseServiceType::TrainingHall)
    {
        std::string label = "Train";
        bool trainingAvailable = true;
        std::string trainingUnavailableReason;

        if (pParty != nullptr && pParty->activeMember() != nullptr)
        {
            const Character &member = *pParty->activeMember();
            const int trainingCap = pParty->rules().experience.trainingLevelCap(houseEntry.trainingMaxLevel);

            if (!GameMechanics::canAct(member))
            {
                label = noConditionToActText(member);
                trainingAvailable = false;
                trainingUnavailableReason = label;
            }
            else if (trainingCap > 0 && member.level >= static_cast<uint32_t>(trainingCap))
            {
                label = "With your skills, you should be working here as a teacher\n\n"
                    "Sorry, but we are unable to train you.";
                trainingAvailable = false;
                trainingUnavailableReason = label;
            }
            else if (const std::optional<uint64_t> experienceShortfall = trainingExperienceShortfall(*pParty, member))
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
                    + std::to_string(trainingCost(
                        houseEntry,
                        *pParty,
                        effectiveReputationForWorld(pWorldRuntime)))
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
        if (houseEntry.serviceCanLearnSkills)
        {
            options.push_back(makeOption(
                HouseActionId::OpenLearnSkillsMenu,
                "Learn Skills",
                isHouseOpenNow,
                closedReason));
        }
        return finalizeHouseActionOptions(houseEntry, serviceType, menuId, pParty, pWorldRuntime, currentGameMinutes, std::move(options));
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
        return finalizeHouseActionOptions(houseEntry, serviceType, menuId, pParty, pWorldRuntime, currentGameMinutes, std::move(options));
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
        if (houseEntry.vendorStockProfile == VendorStockProfile::None)
        {
            options.push_back(makeOption(
                HouseActionId::OpenLearnSkillsMenu,
                "Learn Skills",
                isHouseOpenNow,
                closedReason));
        }
        return finalizeHouseActionOptions(houseEntry, serviceType, menuId, pParty, pWorldRuntime, currentGameMinutes, std::move(options));
    }

    if (serviceType == HouseServiceType::Guild)
    {
        if (requiresGuildMembership(houseEntry)
            && !hasGuildMembership(houseEntry, pParty, pWorldRuntime))
        {
            HouseActionOption learnSkills =
                makeOption(HouseActionId::OpenLearnSkillsMenu, "Learn Skills", isHouseOpenNow, closedReason);
            learnSkills.enabled = false;
            learnSkills.disabledReason = "You must be a member of this guild to study here.";
            options.push_back(std::move(learnSkills));
            return finalizeHouseActionOptions(
                houseEntry,
                serviceType,
                menuId,
                pParty,
                pWorldRuntime,
                currentGameMinutes,
                std::move(options));
        }

        if (!isSkillGuildHouse(houseEntry))
        {
            // A guild of several schools sells each from a shelf of its own, as MM8 does: "Buy Fire Spells" and so on.
            static constexpr std::array<const char *, 9> SchoolNames = {
                "Fire", "Air", "Water", "Earth", "Spirit", "Mind", "Body", "Light", "Dark",
            };
            const std::vector<uint32_t> schools = HouseServiceRuntime::spellbookShelfSchools(houseEntry);

            if (schools.size() > 1)
            {
                for (size_t shelf = 0; shelf < schools.size(); ++shelf)
                {
                    HouseActionOption buy = makeOption(
                        HouseActionId::GuildBuySpellbooks,
                        std::string("Buy ") + SchoolNames[schools[shelf]] + " Spells",
                        isHouseOpenNow,
                        closedReason);
                    buy.argument = std::to_string(shelf);
                    options.push_back(std::move(buy));
                }
            }
            else
            {
                options.push_back(makeOption(
                    HouseActionId::GuildBuySpellbooks,
                    "Buy Spellbooks",
                    isHouseOpenNow,
                    closedReason
                ));
            }
        }

        if (!houseEntry.teachesNothing)
        {
            options.push_back(
                makeOption(HouseActionId::OpenLearnSkillsMenu, "Learn Skills", isHouseOpenNow, closedReason));
        }
        return finalizeHouseActionOptions(houseEntry, serviceType, menuId, pParty, pWorldRuntime, currentGameMinutes, std::move(options));
    }

    if (isFreeHavenHighCouncil(houseEntry))
    {
        return finalizeHouseActionOptions(
            houseEntry,
            serviceType,
            menuId,
            pParty,
            pWorldRuntime,
            currentGameMinutes,
            std::move(options));
    }

    if (serviceType == HouseServiceType::TownHall)
    {
        const int currentFine = pParty != nullptr ? pParty->fineGold() : 0;
        HouseActionOption fine = makeOption(
            HouseActionId::TownHallCurrentFine,
            "Current Fine: " + std::to_string(currentFine) + " gold",
            true,
            std::string {});
        fine.enabled = false;
        options.push_back(std::move(fine));

        HouseActionOption payFine = makeOption(
            HouseActionId::TownHallPayFine,
            "Pay Fine",
            isHouseOpenNow,
            closedReason);

        if (payFine.enabled && currentFine <= 0)
        {
            payFine.enabled = false;
            payFine.disabledReason = "You do not owe a fine.";
        }

        options.push_back(std::move(payFine));
        options.push_back(makeOption(HouseActionId::TownHallBountyHunt, "Bounty Hunt", isHouseOpenNow, closedReason));
        return finalizeHouseActionOptions(houseEntry, serviceType, menuId, pParty, pWorldRuntime, currentGameMinutes, std::move(options));
    }

    if (serviceType == HouseServiceType::Transport)
    {
        if (shouldShowLorettaPriceFixing(houseEntry, pParty))
        {
            options.push_back(makeOption(
                HouseActionId::LorettaPriceFixing,
                pLorettaPriceFixingLabel,
                isHouseOpenNow,
                closedReason));
        }

        options.push_back(makeOption(HouseActionId::TransportSchedule, "Schedule", isHouseOpenNow, closedReason));
        const Character *pMember = selectedMember(pParty);
        bool anyRouteVisible = false;
        bool anyRouteHidden = false;
        const EventRuntimeState *pEventRuntimeState =
            pWorldRuntime != nullptr ? pWorldRuntime->eventRuntimeState() : nullptr;

        for (const HouseEntry::TransportRoute &baseRoute : houseEntry.transportRoutes)
        {
            const HouseEntry::TransportRoute route =
                effectiveTransportRoute(houseEntry, baseRoute, pEventRuntimeState);

            if (!routeQBitSatisfied(route, pWorldRuntime))
            {
                anyRouteHidden = true;
                continue;
            }

            if (!routeAvailableToday(route, currentGameMinutes))
            {
                anyRouteHidden = true;
                continue;
            }

            anyRouteVisible = true;
            const int price = PriceCalculator::transportPrice(
                partyMerchantMember(pParty),
                houseEntry,
                isBoatHouse(houseEntry),
                effectiveReputationForWorld(pWorldRuntime));
            const int travelDays =
                adjustedTransportTravelDays(route, pEventRuntimeState, !isBoatHouse(houseEntry));
            HouseActionOption transport = makeOption(
                HouseActionId::TransportRoute,
                transportTravelDaysText(travelDays)
                    + " to "
                    + route.destinationName
                    + " for "
                    + std::to_string(price)
                    + " gold",
                isHouseOpenNow,
                closedReason
            );
            transport.argument = std::to_string(route.routeIndex);
            options.push_back(std::move(transport));
        }

        if (!anyRouteVisible && anyRouteHidden)
        {
            HouseActionOption noRoute = {};
            noRoute.id = HouseActionId::TransportRoute;
            noRoute.label = "Sorry, come back another day";
            noRoute.enabled = false;
            noRoute.disabledReason = "Sorry, come back another day";
            options.push_back(std::move(noRoute));
        }
    }

    // A house of no MM service type whose row lists offered skills (house_data's last column, unused by MM data)
    // teaches their Novice for gold, like a guild without membership: Hesper's service houses.
    if (serviceType == HouseServiceType::None && !houseEntry.offeredSkills.empty())
    {
        options.push_back(makeOption(HouseActionId::OpenLearnSkillsMenu, "Learn Skills", isHouseOpenNow, closedReason));
    }

    return finalizeHouseActionOptions(houseEntry, serviceType, menuId, pParty, pWorldRuntime, currentGameMinutes, std::move(options));
}

void applyHouseTopicFilterHook(
    const HouseEntry &houseEntry,
    HouseServiceType serviceType,
    DialogueMenuId menuId,
    const Party *pParty,
    const IGameplayWorldRuntime *pWorldRuntime,
    std::vector<HouseActionOption> &options)
{
    if (pWorldRuntime == nullptr || options.empty())
    {
        return;
    }

    IGameplayWorldRuntime *pMutableWorldRuntime = const_cast<IGameplayWorldRuntime *>(pWorldRuntime);
    EventRuntimeState *pEventRuntimeState = pMutableWorldRuntime->eventRuntimeState();

    if (pEventRuntimeState == nullptr)
    {
        return;
    }

    EventRuntimeState::ActiveHookContext hookContext = {};
    hookContext.kind = EventRuntimeHookKind::HouseTopicFilter;
    hookContext.houseId = houseEntry.id;
    hookContext.houseServiceType = static_cast<uint32_t>(serviceType);
    hookContext.menuId = static_cast<uint32_t>(menuId);
    hookContext.heldItemId = pParty != nullptr ? pParty->heldItemIdForQueries() : 0;
    pEventRuntimeState->activeHookContext = std::move(hookContext);
    pMutableWorldRuntime->executeEventHooks(EventRuntimeHookKind::HouseTopicFilter);

    const std::vector<uint32_t> actionIds = pEventRuntimeState->activeHookContext
        ? pEventRuntimeState->activeHookContext->houseTopicActionIds
        : std::vector<uint32_t>{};
    pEventRuntimeState->activeHookContext.reset();

    if (actionIds.empty())
    {
        return;
    }

    std::vector<HouseActionOption> filteredOptions;

    for (uint32_t actionId : actionIds)
    {
        const auto iterator = std::find_if(
            options.begin(),
            options.end(),
            [actionId](const HouseActionOption &option)
            {
                return static_cast<uint32_t>(option.id) == actionId;
            });

        if (iterator != options.end())
        {
            filteredOptions.push_back(*iterator);
        }
    }

    options = std::move(filteredOptions);
}

std::vector<HouseActionOption> finalizeHouseActionOptions(
    const HouseEntry &houseEntry,
    HouseServiceType serviceType,
    DialogueMenuId menuId,
    const Party *pParty,
    const IGameplayWorldRuntime *pWorldRuntime,
    float currentGameMinutes,
    std::vector<HouseActionOption> options)
{
    applyHouseTopicFilterHook(houseEntry, serviceType, menuId, pParty, pWorldRuntime, options);

    if (houseRefusesServiceForReputation(houseEntry, serviceType, pWorldRuntime, currentGameMinutes))
    {
        const std::string reason = houseHasActiveTheftBan(houseEntry, pWorldRuntime, currentGameMinutes)
            ? "This house refuses service after the theft."
            : "This house refuses service because of your reputation.";
        disableHouseOptionsForReputation(options, reason);
    }

    return options;
}

namespace
{
// A route's trip (TransportRoute today, TransportScheduledTrip after waiting for its day): the fare, the waiting
// food, the days on the road with the party resting, and the map move.
void travelByTransport(
    const HouseActionOption &action,
    const HouseEntry &houseEntry,
    Party &party,
    IGameplayWorldRuntime *pWorldRuntime,
    HouseActionResult &result)
{
    // The route's index leads the argument; a scheduled trip adds its departure day after a colon.
    const HouseEntry::TransportRoute *pRoute = findTransportRoute(houseEntry, action.argument);
    const bool scheduled = action.id == HouseActionId::TransportScheduledTrip;
    const size_t daySeparator = action.argument.find(':');
    const int departureDay = scheduled && daySeparator != std::string::npos
        ? std::atoi(action.argument.c_str() + daySeparator + 1)
        : -1;

    if (pRoute == nullptr || (scheduled && (departureDay < 0 || departureDay > 6)))
    {
        result.messages.push_back("That route is not available.");
        return;
    }

    if (pWorldRuntime == nullptr)
    {
        result.messages.push_back("Travel is unavailable right now.");
        return;
    }

    EventRuntimeState *pEventRuntimeState = pWorldRuntime->eventRuntimeState();

    if (pEventRuntimeState == nullptr)
    {
        result.messages.push_back("Travel is unavailable right now.");
        return;
    }

    const HouseEntry::TransportRoute route =
        effectiveTransportRoute(houseEntry, *pRoute, pEventRuntimeState);

    if (!routeQBitSatisfied(route, pWorldRuntime))
    {
        result.messages.push_back("That route is not available.");
        return;
    }

    int waitDays = 0;

    if (scheduled)
    {
        if (!route.daysAvailable[size_t(departureDay)])
        {
            result.messages.push_back("That route is not available.");
            return;
        }

        waitDays = transportWaitDays(dayOfWeekFromGameMinutes(pWorldRuntime->gameMinutes()), departureDay);
    }
    else if (!routeAvailableToday(route, pWorldRuntime->gameMinutes()))
    {
        result.messages.push_back("Sorry, come back another day");
        return;
    }

    const int price = PriceCalculator::transportPrice(
        partyMerchantMember(&party),
        houseEntry,
        isBoatHouse(houseEntry),
        effectiveReputationForWorld(pWorldRuntime));

    if (party.gold() < price)
    {
        result.messages.push_back("You don't have enough gold.");
        result.soundType = HouseSoundType::TransportNotEnoughGold;
        result.speechId = SpeechId::NotEnoughGold;
        return;
    }

    // The party eats while it waits for the departure; the trip itself is free.
    const int waitFood = waitDays * TransportWaitFoodPerDay;

    if (party.food() < waitFood)
    {
        result.messages.push_back(
            "You don't have enough food to wait " + transportTravelDaysText(waitDays) + ".");
        return;
    }

    party.addGold(-price);

    if (waitDays > 0)
    {
        party.addFood(-waitFood);
        const float waitMinutes = float(waitDays * MinutesPerDay);
        pWorldRuntime->advanceGameMinutes(waitMinutes);
        party.advanceTimedStates(waitMinutes * 60.0f);
    }

    party.restAndHealAll();
    const int travelDays =
        adjustedTransportTravelDays(route, pEventRuntimeState, !isBoatHouse(houseEntry));
    const float beforeGameMinutes = pWorldRuntime->gameMinutes();
    const float travelMinutes = static_cast<float>(travelDays * MinutesPerDay);
    pWorldRuntime->advanceGameMinutes(travelMinutes);
    party.advanceTimedStates(travelMinutes * 60.0f);
    const float afterGameMinutes = pWorldRuntime->gameMinutes();

    EventRuntimeState::PendingMapMove pendingMapMove = {};
    pendingMapMove.travelTimeApplied = true;
    pendingMapMove.mapName = route.mapFileName;
    pendingMapMove.x = route.x;
    pendingMapMove.y = route.y;
    pendingMapMove.z = route.z;
    pendingMapMove.directionDegrees = route.directionDegrees;
    pendingMapMove.useMapStartPosition = route.useMapStartPosition;
    pendingMapMove.traceSourceKind = isBoatHouse(houseEntry) ? "boat_route" : "horse_route";
    pendingMapMove.traceSourceId = houseEntry.id;
    pendingMapMove.traceActionId = static_cast<uint32_t>(action.id);
    pendingMapMove.traceDestinationName = route.destinationName;
    pEventRuntimeState->lastMapTransitionRequested = EventRuntimeState::MapTransitionTrace{
        .sourceKind = pendingMapMove.traceSourceKind,
        .sourceId = houseEntry.id,
        .actionId = static_cast<uint32_t>(action.id),
        .routeIndex = route.routeIndex,
        .confirmationRequired = false,
        .destinationMap = route.mapFileName,
        .destinationName = route.destinationName,
        .travelDays = static_cast<uint32_t>(travelDays),
        .useStartPosition = route.useMapStartPosition,
        .x = route.x,
        .y = route.y,
        .z = route.z,
        .directionDegrees = route.directionDegrees,
    };
    GAMEPLAY_DEBUG_TRACE(
        "game_time_advanced source=\"" + pendingMapMove.traceSourceKind + "\""
        + " source_id=" + std::to_string(houseEntry.id)
        + " action_id=" + std::to_string(static_cast<uint32_t>(action.id))
        + " minutes=" + std::to_string(travelMinutes)
        + " before_game_minutes=" + std::to_string(beforeGameMinutes)
        + " after_game_minutes=" + std::to_string(afterGameMinutes)
        + " game_minutes=" + std::to_string(afterGameMinutes));
    GAMEPLAY_DEBUG_TRACE(
        "map_transition_requested source_kind=\"" + pendingMapMove.traceSourceKind + "\""
        + " source_id=" + std::to_string(houseEntry.id)
        + " action_id=" + std::to_string(static_cast<uint32_t>(action.id))
        + " route_index=" + std::to_string(route.routeIndex)
        + " confirmation_required=false"
        + " destination_map=\"" + route.mapFileName + "\""
        + " destination_name=\"" + route.destinationName + "\""
        + " travel_days=" + std::to_string(travelDays)
        + " before_game_minutes=" + std::to_string(beforeGameMinutes)
        + " game_minutes=" + std::to_string(afterGameMinutes)
        + " use_start_position=" + (route.useMapStartPosition ? "true" : "false")
        + " pos=(" + std::to_string(route.x)
        + "," + std::to_string(route.y)
        + "," + std::to_string(route.z) + ")"
        + " direction_degrees=" + std::to_string(route.directionDegrees));
    pEventRuntimeState->pendingMapMove = std::move(pendingMapMove);

    result.messages.push_back(
        (waitDays > 0
                ? "You wait " + transportTravelDaysText(waitDays) + " for the "
                    + (isBoatHouse(houseEntry) ? "ship" : "coach") + ". "
                : std::string())
        + "It will take "
        + transportTravelDaysText(travelDays)
        + " to travel to "
        + route.destinationName
        + "."
    );
    result.succeeded = true;
    result.soundType = HouseSoundType::TransportTravel;
    return;
}
}

HouseActionResult performHouseAction(
    const HouseActionOption &action,
    const HouseEntry &houseEntry,
    Party &party,
    const ClassSkillTable *pClassSkillTable,
    IGameplayWorldRuntime *pWorldRuntime,
    const NpcDialogTable *pNpcDialogTable
)
{
    HouseActionResult result = {};

    if (pWorldRuntime != nullptr)
    {
        EventRuntimeState *pEventRuntimeState = pWorldRuntime->eventRuntimeState();

        if (pEventRuntimeState != nullptr)
        {
            EventRuntimeState::ActiveHookContext hookContext = {};
            hookContext.kind = EventRuntimeHookKind::HouseTopicClick;
            hookContext.houseId = houseEntry.id;
            hookContext.houseServiceType = static_cast<uint32_t>(resolveHouseServiceType(houseEntry));
            hookContext.houseActionId = static_cast<uint32_t>(action.id);
            hookContext.heldItemId = party.heldItemIdForQueries();
            pEventRuntimeState->activeHookContext = std::move(hookContext);
            pWorldRuntime->executeEventHooks(EventRuntimeHookKind::HouseTopicClick);

            const bool blocked = pEventRuntimeState->activeHookContext
                && pEventRuntimeState->activeHookContext->blocked;
            const std::optional<std::string> statusText = pEventRuntimeState->activeHookContext
                ? pEventRuntimeState->activeHookContext->statusText
                : std::nullopt;
            pEventRuntimeState->activeHookContext.reset();

            if (blocked)
            {
                if (statusText)
                {
                    result.messages.push_back(*statusText);
                }

                return result;
            }
        }
    }

    switch (action.id)
    {
        case HouseActionId::TempleHeal:
        {
            if (!houseEntry.templeCanHeal)
            {
                result.messages.push_back("Healing is not offered here.");
                return result;
            }

            Character *pMember = party.activeMember();

            if (pMember == nullptr)
            {
                result.messages.push_back("No character is selected.");
                return result;
            }

            if (!activeMemberNeedsTempleHealing(party, houseEntry))
            {
                if (party.activeMemberNeedsHealing())
                {
                    result.messages.push_back("The temple staff cannot treat " + pMember->name + "'s condition.");
                }
                else
                {
                    result.messages.push_back("The temple staff says " + pMember->name + " is already well.");
                }
                return result;
            }

            const int price = templeHealCost(houseEntry, pMember);

            if (party.gold() < price)
            {
                result.messages.push_back("You need " + std::to_string(price) + " gold for healing.");
                result.soundType = HouseSoundType::GeneralNotEnoughGold;
                result.speechId = SpeechId::NotEnoughGold;
                return result;
            }

            party.addGold(-price);
            if (Character *pHealedMember = party.activeMember())
            {
                pHealedMember->health = Party::effectiveMaximumHealth(*pHealedMember);
                pHealedMember->spellPoints = Party::effectiveMaximumSpellPoints(*pHealedMember);
                pHealedMember->conditions.reset();
                pHealedMember->conditionStartGameMinutes.fill(0.0f);
            }
            result.messages.push_back(
                "The temple restores " + pMember->name + " for " + std::to_string(price) + " gold.");
            result.succeeded = true;
            return result;
        }

        case HouseActionId::TempleDonate:
        {
            if (!houseEntry.templeCanDonate)
            {
                result.messages.push_back("Donations are not accepted here.");
                return result;
            }

            const int price = templeDonationCost(houseEntry);

            if (party.gold() < price)
            {
                result.messages.push_back("You need " + std::to_string(price) + " gold to donate here.");
                result.soundType = HouseSoundType::GeneralNotEnoughGold;
                result.speechId = SpeechId::NotEnoughGold;
                return result;
            }

            party.addGold(-price);

            if (pWorldRuntime != nullptr)
            {
                if (isTempleOfBaa(houseEntry)
                    && effectiveReputationForWorld(pWorldRuntime) < 9)
                {
                    addStoredCurrentLocationReputation(*pWorldRuntime, 2);
                }
                else if (pWorldRuntime->currentLocationReputation() > -5)
                {
                    addStoredCurrentLocationReputation(*pWorldRuntime, -1);
                }

                if (EventRuntimeState *pEventRuntimeState = pWorldRuntime->eventRuntimeState())
                {
                    const size_t activeMemberIndex = party.activeMemberIndex();
                    tryApplyTempleDonationBuffs(
                        *pWorldRuntime,
                        party,
                        pEventRuntimeState->dialogueState,
                        activeMemberIndex);

                    if (activeMemberIndex < pEventRuntimeState->dialogueState.templeDonationCounters.size())
                    {
                        ++pEventRuntimeState->dialogueState.templeDonationCounters[activeMemberIndex];
                    }
                }
            }

            result.messages.push_back("Thank You");
            result.succeeded = true;
            return result;
        }

        case HouseActionId::TavernRentRoom:
        {
            const int price = PriceCalculator::tavernRoomPrice(
                partyMerchantMember(&party),
                houseEntry,
                effectiveReputationForWorld(pWorldRuntime));

            if (party.gold() < price)
            {
                result.messages.push_back("You need " + std::to_string(price) + " gold to rent a room.");
                result.soundType = HouseSoundType::TavernNotEnoughGold;
                result.speechId = SpeechId::NotEnoughGold;
                return result;
            }

            party.addGold(-price);
            result.succeeded = true;
            result.soundType = HouseSoundType::TavernRentRoom;
            result.pendingInnRest = InnRestRequest{houseEntry.id};
            return result;
        }

        case HouseActionId::TavernBuyFood:
        {
            const int foodTarget = tavernFoodTarget(houseEntry);

            if (party.food() >= foodTarget)
            {
                result.messages.push_back("Your packs are already full enough.");
                result.speechId = SpeechId::TavernPacksFull;
                return result;
            }

            const int price = PriceCalculator::tavernFoodPrice(
                partyMerchantMember(&party),
                houseEntry,
                effectiveReputationForWorld(pWorldRuntime));

            if (party.gold() < price)
            {
                result.messages.push_back("You need " + std::to_string(price) + " gold for provisions.");
                result.soundType = HouseSoundType::TavernNotEnoughGold;
                result.speechId = SpeechId::NotEnoughGold;
                return result;
            }

            party.addGold(-price);
            party.addFood(foodTarget - party.food());
            result.messages.push_back("The innkeeper fills your packs to " + std::to_string(foodTarget) + " days.");
            result.succeeded = true;
            result.soundType = HouseSoundType::TavernBuyFood;
            return result;
        }

        case HouseActionId::TavernDrink:
        {
            constexpr int DrinkPrice = 1;

            if (party.gold() < DrinkPrice)
            {
                result.messages.push_back("You need " + std::to_string(DrinkPrice) + " gold for a drink.");
                result.soundType = HouseSoundType::TavernNotEnoughGold;
                result.speechId = SpeechId::NotEnoughGold;
                return result;
            }

            party.addGold(-DrinkPrice);
            result.messages.push_back("Refreshing!");
            result.succeeded = true;
            result.speechId = SpeechId::TavernDrink;

            if (tavernDrinkMakesPartyDrunk())
            {
                const float gameMinutes = pWorldRuntime != nullptr ? pWorldRuntime->gameMinutes() : 0.0f;
                party.applyMemberCondition(party.activeMemberIndex(), CharacterCondition::Drunk, gameMinutes);
                result.additionalSpeechIds.push_back(SpeechId::TavernGotDrunk);
            }

            return result;
        }

        case HouseActionId::TavernTip:
        {
            constexpr int TipPrice = 1;

            if (party.gold() < TipPrice)
            {
                result.messages.push_back("You need " + std::to_string(TipPrice) + " gold for a tip.");
                result.soundType = HouseSoundType::TavernNotEnoughGold;
                result.speechId = SpeechId::NotEnoughGold;
                return result;
            }

            party.addGold(-TipPrice);
            result.messages.push_back("Thank You");
            result.succeeded = true;
            result.speechId = SpeechId::TavernTip;
            result.additionalSpeechIds.push_back(SpeechId::ThankYou);
            return result;
        }

        case HouseActionId::LorettaPriceFixing:
        {
            const std::optional<uint32_t> stableQuestBit = lorettaStableQuestBitForHouse(houseEntry.id);

            if (!stableQuestBit.has_value()
                || !party.hasQuestBit(LorettaPriceQuestBit)
                || party.hasQuestBit(*stableQuestBit))
            {
                return result;
            }

            party.setQuestBit(*stableQuestBit, true);
            result.messages.push_back(pLorettaPriceFixingMessage);
            result.succeeded = true;

            bool allStablesFixed = true;

            for (uint32_t questBit = LorettaFirstStableBit; questBit <= LorettaLastStableBit; ++questBit)
            {
                if (!party.hasQuestBit(questBit))
                {
                    allStablesFixed = false;
                    break;
                }
            }

            if (allStablesFixed)
            {
                party.addExperienceToMember(party.activeMemberIndex(), 1);
                party.setQuestBit(LorettaPriceCompleteBit, true);
            }

            return result;
        }

        case HouseActionId::TownHallCurrentFine:
        {
            result.messages.push_back("Your current fine is " + std::to_string(party.fineGold()) + " gold.");
            return result;
        }

        case HouseActionId::TownHallPayFine:
        {
            const int fine = party.fineGold();

            if (fine <= 0)
            {
                result.messages.push_back("You do not owe a fine.");
                return result;
            }

            if (party.gold() < fine)
            {
                result.messages.push_back("You need " + std::to_string(fine) + " gold to pay your fine.");
                result.soundType = HouseSoundType::GeneralNotEnoughGold;
                result.speechId = SpeechId::NotEnoughGold;
                return result;
            }

            party.addGold(-fine);
            party.clearFineGold();
            result.messages.push_back("Your fine has been paid.");
            result.succeeded = true;
            return result;
        }

        case HouseActionId::TownHallBountyHunt:
        {
            if (pWorldRuntime == nullptr)
            {
                result.messages.push_back("The bounty office is unavailable right now.");
                return result;
            }

            const BountyHuntInteractionResult bountyResult =
                performBountyHuntInteraction(*pWorldRuntime, &party, true, pNpcDialogTable);
            result.succeeded = bountyResult.succeeded;
            result.messages = bountyResult.messages;
            return result;
        }

        case HouseActionId::ThroneServeSentence:
        {
            if (party.fineGold() <= 0)
            {
                result.messages.push_back("You do not owe a fine.");
                return result;
            }

            party.clearFineGold();
            party.addEventVariableValue(static_cast<uint16_t>(EvtVariable::PrisonTerms), 1);
            party.addAward(PrisonTermsAwardId);
            party.restAndHealAll();

            if (pWorldRuntime != nullptr)
            {
                pWorldRuntime->advanceGameMinutes(PrisonSentenceMinutes);
                party.advanceTimedStates(PrisonSentenceMinutes * 60.0f);
            }

            result.messages.push_back("You have served one year in prison.");
            result.succeeded = true;
            result.speechId = SpeechId::InPrison;
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

            if (!GameMechanics::canAct(*pMember))
            {
                result.messages.push_back(noConditionToActText(*pMember));
                return result;
            }

            const int price = trainingCost(
                houseEntry,
                party,
                effectiveReputationForWorld(pWorldRuntime));

            const int trainingCap = party.rules().experience.trainingLevelCap(houseEntry.trainingMaxLevel);

            if (trainingCap > 0 && pMember->level >= static_cast<uint32_t>(trainingCap))
            {
                result.messages.push_back(
                    "With your skills, you should be working here as a teacher\n\n"
                    "Sorry, but we are unable to train you."
                );
                result.soundType = HouseSoundType::TrainingCantTrain;
                return result;
            }

            if (const std::optional<uint64_t> experienceShortfall = trainingExperienceShortfall(party, *pMember))
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
                result.speechId = SpeechId::NotEnoughGold;
                return result;
            }

            uint32_t newLevel = 0;
            uint32_t skillPointsEarned = 0;

            if (!party.trainActiveMember(
                    trainingCap > 0 ? static_cast<uint32_t>(trainingCap) : 0,
                    newLevel,
                    skillPointsEarned))
            {
                result.messages.push_back("Training is not available right now.");
                result.soundType = HouseSoundType::TrainingCantTrain;
                return result;
            }

            party.addGold(-price);
            bool trainingRoundAdvanced = true;

            if (pWorldRuntime != nullptr)
            {
                EventRuntimeState *pEventRuntimeState = pWorldRuntime->eventRuntimeState();

                if (pEventRuntimeState != nullptr)
                {
                    trainingRoundAdvanced = recordOeTrainingLevel(
                        pEventRuntimeState->dialogueState,
                        houseEntry.id,
                        party.activeMemberIndex(),
                        party.memberCount());
                }
            }

            if (trainingRoundAdvanced)
            {
                party.restAndHealAll();

                if (pWorldRuntime != nullptr)
                {
                    const float trainingMinutes = party.rules().experience.trainingDurationMinutes(
                        oeTrainingDurationMinutes(houseEntry, pWorldRuntime->gameMinutes()));
                    pWorldRuntime->advanceGameMinutes(trainingMinutes);
                    party.advanceTimedStates(trainingMinutes * 60.0f);
                }
            }

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

            if (!GameMechanics::canAct(*pMember))
            {
                result.messages.push_back(noConditionToActText(*pMember));
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
                &party,
                resolveHouseServiceType(houseEntry) == HouseServiceType::Guild,
                effectiveReputationForWorld(pWorldRuntime));

            if (party.gold() < price)
            {
                result.messages.push_back("You don't have enough gold.");
                result.soundType = HouseSoundType::GeneralNotEnoughGold;
                result.speechId = SpeechId::NotEnoughGold;
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
            result.speechId = SpeechId::SkillLearned;
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
        case HouseActionId::TransportScheduledTrip:
        {
            travelByTransport(action, houseEntry, party, pWorldRuntime, result);
            return result;
        }

        case HouseActionId::BuyTeacherLedger:
        {
            const std::optional<uint32_t> continent = tavernTeacherLedgerContinent(houseEntry, &party);

            if (!continent)
            {
                result.messages.push_back("The ledger is not sold here.");
                return result;
            }

            const TrainerDirectory &directory = *party.trainerDirectory();
            const std::string continentName = trainerContinentName(*continent);

            if (!buyTeacherLedger(party, directory, *continent))
            {
                result.messages.push_back(directory.ledger().fill(directory.ledger().tooPoor, continentName));
                result.soundType = HouseSoundType::TavernNotEnoughGold;
                return result;
            }

            result.messages.push_back(directory.ledger().fill(directory.ledger().bought, continentName));
            result.succeeded = true;
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
        case HouseActionId::OpenTeacherLedgerMenu:
        case HouseActionId::BackToRootMenu:
        case HouseActionId::ExtraExit:
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
