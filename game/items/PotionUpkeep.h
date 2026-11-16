#pragma once

#include "game/items/AlchemyBenchRuntime.h"
#include "game/items/QuickItemSlots.h"
#include "game/party/BattleOrders.h"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace OpenYAMM::Game
{
class Party;
class PotionEffectTable;
struct PotionDefinition;

// Potions in the upkeep list (devdocs/BATTLE_ORDERS.md "Potions"): a potion order (BattleOrderKind::Potion) is drunk
// by its member while one of the potion's timed effects is gone or running out, as an upkeep buff is cast; and the
// party keeps a stock of it, which the Upkeep key's auto-brew brews from what the party carries.
namespace PotionUpkeep
{
// A potion the upkeep list takes: one with a timed effect (a buff, an aura, an immunity, a skill bonus,
// regeneration), so it has a time left to renew at.
bool isUpkeepPotion(const PotionDefinition &potion);

// A new upkeep order for the potion: renewed from the default time left on, keeping two bottles' drinks in stock.
BattleOrder newOrder(uint32_t itemId, const PotionEffectTable &effects);

// A carried bottle's power as a drink uses it: at least 1, at most the table's cap.
int bottlePower(const PotionEffectTable &effects, const InventoryItem &item);
// The drinks a carried bottle has left.
uint32_t bottleDrinks(const PotionDefinition &potion, const InventoryItem &item);
// The drinks of the potion the party carries in its bags, counting only bottles that can be drunk and have at least
// `minimumPower`.
uint32_t carriedDrinks(
    const Party &party,
    const PotionDefinition &potion,
    const PotionEffectTable &effects,
    std::optional<uint16_t> minimumPower);

// Whether the member should drink a bottle of this power now, whose timed effects last `drinkSeconds`: one of them
// is gone, or less is left than the order's renew time and half of what the drink gives (upkeepBuffDue). An effect
// still running stronger than the bottle gives, or an aura the party's own outdoes (MAW), counts as kept: the drink
// would add nothing to it.
bool potionDue(
    const Party &party,
    size_t memberIndex,
    const PotionDefinition &potion,
    int power,
    float drinkSeconds,
    std::optional<uint16_t> renewBelowMinutes);

// The least time a drink's timed effects have left on the member, among those a drink of this power would renew: 0
// when one is gone. None when none would be renewed (all kept by something stronger).
std::optional<float> secondsLeft(const Party &party, size_t memberIndex, const PotionDefinition &potion, int power);

// The bottle a potion order drinks (its rule's pick, from the member's bags first, then the others') and its power;
// without one, the power the stock is brewed at, for whether it would be due.
struct OrderBottle
{
    std::optional<QuickItemSlots::PartyLocation> location;
    int power = 1;
};
OrderBottle orderBottle(
    const Party &party,
    size_t memberIndex,
    const BattleOrder &order,
    const PotionEffectTable &effects);

// What auto-brew keeps: each potion the members' upkeep lists stock (enabled potion orders with stock), with the sum
// of their drinks and the highest power any of them asks; in the order the lists first name them, which is the
// order they are brewed in.
struct StockTarget
{
    uint32_t itemId = 0;
    uint32_t drinks = 0;
    std::optional<uint16_t> power;
};
std::vector<StockTarget> stockTargets(const Party &party);

// One stocked potion that was short: how much was wanted and carried, what was brewed, and why not more.
struct RestockLine
{
    uint32_t itemId = 0;
    uint32_t wantedDrinks = 0;
    uint32_t carriedDrinks = 0;
    uint32_t brewedBottles = 0;
    // Why the missing drinks were not all brewed; None with `powerUnreached` when only the aimed power could not be.
    AlchemyChainBlock block = AlchemyChainBlock::None;
    uint32_t blockItemId = 0;
    bool powerUnreached = false;
    bool complete = false;
};

struct RestockOutcome
{
    std::vector<RestockLine> lines;
    // The last potion brewed, and the mix that brewed it (its sound and the alchemist's speech).
    InventoryItem lastBrewed;
    AlchemyMixOutcome lastMix;
    // An empty bottle no pack had room for: brewing stopped there.
    std::optional<InventoryItem> overflowItem;

    bool brewedAny() const;
};

// Brews what the stock lacks, potion by potion in stockTargets' order: each from the weakest ingredients that reach
// its power, never mixing the drinks the other stocked potions keep into it. Only known recipes the party's alchemist
// mixes safely are used (AlchemyChainPlanner), so nothing explodes.
RestockOutcome restock(
    Party &party,
    const AlchemyBenchTables &tables,
    const PotionEffectTable &effects,
    const AlchemyBenchRuntime::AutonoteLookup &isAutonoteUnlocked,
    bool keepMixedPotions);
}
}
