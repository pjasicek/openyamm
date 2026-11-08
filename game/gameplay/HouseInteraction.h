#pragma once

#include "game/events/EventRuntime.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/party/SpeechIds.h"
#include "game/tables/HouseTable.h"

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class Mm9TransportRouteTable;
struct Mm9TransportRoute;
class Party;
class ClassSkillTable;
class NpcDialogTable;

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
    TownHall,
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
    ExtraExit,
    LorettaPriceFixing,
    TavernDrink,
    TavernTip,
    TownHallCurrentFine,
    TownHallPayFine,
    TownHallBountyHunt,
    ThroneServeSentence,
    // A stable's or boat's week of departures (the Schedule topic).
    TransportSchedule,
    // A trip chosen in the schedule: wait for its departure day, then travel. Argument "route:day" (day 0 Monday).
    TransportScheduledTrip,
    // A tavern's Ledger of Teachers topic (TrainerDirectory.h): its description and the purchase.
    OpenTeacherLedgerMenu,
    BuyTeacherLedger,
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

struct InnRestRequest
{
    uint32_t houseId = 0;
};

struct HouseActionResult
{
    bool succeeded = false;
    std::optional<HouseSoundType> soundType;
    SpeechId speechId = SpeechId::None;
    std::vector<SpeechId> additionalSpeechIds;
    std::vector<std::string> messages;
    std::optional<InnRestRequest> pendingInnRest;
};

// The continent whose Ledger of Teachers the tavern sells while the party has not bought it, or nothing.
std::optional<uint32_t> tavernTeacherLedgerContinent(const HouseEntry &houseEntry, const Party *pParty);

// A stable's or boat's week of departures, for its Schedule popup: the routes the party may take, with event
// overrides, quest bits and hireling day reductions applied, in route order.
struct TransportScheduleRoute
{
    uint32_t routeIndex = 0;
    std::string destinationName;
    std::array<bool, 7> daysAvailable = {};
    int travelDays = 0;
};

struct TransportSchedule
{
    std::vector<TransportScheduleRoute> routes;
    // The weekday now, 0 Monday.
    int today = 0;
    int fare = 0;
    // Food the party eats for each day it waits for a departure.
    int foodPerWaitDay = 0;
};

struct HouseShopGoodbyeResult
{
    std::optional<HouseSoundType> soundType;
    bool queueRudeSpeech = false;
};

HouseServiceType resolveHouseServiceType(const HouseEntry &houseEntry);
// The sound played on entering: the greeting, or a magic guild's members-only line for a non-member.
HouseSoundType houseEntrySoundType(
    const HouseEntry &houseEntry,
    const Party *pParty,
    const IGameplayWorldRuntime *pWorldRuntime);
std::optional<uint32_t> deriveHouseSoundId(const HouseEntry &houseEntry, HouseSoundType soundType);
bool isAlchemyShop(const HouseEntry &houseEntry);
bool houseRefusesShopServiceForReputation(
    const HouseEntry &houseEntry,
    const IGameplayWorldRuntime *pWorldRuntime,
    float currentGameMinutes);
HouseShopGoodbyeResult resolveHouseShopGoodbyeResult(
    const HouseEntry &houseEntry,
    bool transactionPerformed,
    bool shopBanned,
    int partyGold);
bool isHouseOpenAtGameMinute(const HouseEntry &houseEntry, float currentGameMinutes);
float innRestDurationMinutes(uint32_t houseId, float currentGameMinutes);
std::string buildClosedStatusText(const HouseEntry &houseEntry);
bool isBoatHouse(const HouseEntry &houseEntry);
uint32_t arcomageDeckItemId();
std::string arcomageDeckRequiredMessage();
bool partyHasArcomageDeck(const Party *pParty);
bool houseRequiresArcomageDeck(const HouseEntry &houseEntry);
bool partyCanPlayArcomageInHouse(const HouseEntry &houseEntry, const Party *pParty);
TransportSchedule buildTransportSchedule(
    const HouseEntry &houseEntry,
    const Party *pParty,
    const IGameplayWorldRuntime *pWorldRuntime);
// An MM9 dock's fare for a route: its base price and multiplier with the party's best merchant and reputation.
int mm9TransportFare(const Mm9TransportRoute &route, const Party &party, const IGameplayWorldRuntime *pWorldRuntime);
// An MM9 dock's week for the talk's Schedule: its one boat a weekday that the party may take (routeIndex is the
// route's MM9 day index); the dock's routes share one fare.
TransportSchedule buildMm9TransportSchedule(
    const Mm9TransportRouteTable &routeTable,
    uint32_t dockId,
    const Party *pParty,
    const IGameplayWorldRuntime *pWorldRuntime);
// Food the party eats for each day it waits for a departure.
int transportWaitFoodPerDay();
// Days from today until a departure on the given weekday (0 Monday): 0 for today, up to 6.
int transportWaitDays(int today, int departureDay);
std::string transportScheduledTripArgument(uint32_t routeIndex, int departureDay);

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
    const IGameplayWorldRuntime *pWorldRuntime,
    float currentGameMinutes,
    DialogueMenuId menuId
);

HouseActionResult performHouseAction(
    const HouseActionOption &action,
    const HouseEntry &houseEntry,
    Party &party,
    const ClassSkillTable *pClassSkillTable,
    IGameplayWorldRuntime *pWorldRuntime,
    const NpcDialogTable *pNpcDialogTable = nullptr
);
}
