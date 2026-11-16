#include "game/items/PotionUpkeep.h"

#include "game/items/InventoryBags.h"
#include "game/party/Party.h"
#include "game/rules/GameRules.h"
#include "game/rules/ItemRules.h"
#include "game/rules/PotionRules.h"
#include "game/tables/PotionEffectTable.h"

#include <algorithm>

namespace OpenYAMM::Game
{
namespace
{
bool isTimedEffect(PotionEffectKind kind)
{
    switch (kind)
    {
        case PotionEffectKind::Buff:
        case PotionEffectKind::PartyBuff:
        case PotionEffectKind::Immunity:
        case PotionEffectKind::AuraBuff:
        case PotionEffectKind::SkillBonus:
        case PotionEffectKind::Regeneration:
            return true;
        default:
            return false;
    }
}

int bagCount(const Party &party)
{
    return std::max(1, party.rules().items.bagCount(party));
}

// A timed potion effect on the member: the strongest in force and the time it has left (none when there is none).
struct RunningEffect
{
    int amount = 0;
    float remainingSeconds = 0;
};

std::optional<RunningEffect> runningPotionEffect(const Character &member, TimedPotionEffect::Kind kind, uint32_t key)
{
    std::optional<RunningEffect> running;

    for (const TimedPotionEffect &effect : member.rulesetState.potionEffects)
    {
        if (effect.kind == kind && effect.key == key && effect.remainingSeconds > 0
            && (!running || effect.amount > running->amount))
        {
            running = RunningEffect{effect.amount, effect.remainingSeconds};
        }
    }

    return running;
}

// One timed effect of a potion as it stands on the member: whether a drink would renew it (it would not when it runs
// stronger than the drink gives, or the party's own aura outdoes the drink's), and the time it has left.
struct EffectState
{
    bool counts = true;
    float remainingSeconds = 0;
};

std::vector<EffectState> effectStates(const Party &party, size_t memberIndex, const PotionDefinition &potion, int power)
{
    std::vector<EffectState> states;
    const Character &member = *party.member(memberIndex);
    const PotionRules &rules = gameRulesFor(&party).potions;

    for (const PotionEffect &effect : potion.effects)
    {
        if (!isTimedEffect(effect.kind))
        {
            continue;
        }

        const int amount = effect.amount.evaluate(power, rules.estimatedPool(effect.amount.pool, power));
        // The effect in force and the strength the drink would give it.
        const auto running = [&states](std::optional<RunningEffect> effectNow, int drinkAmount)
        {
            states.push_back(effectNow ? EffectState{effectNow->amount <= drinkAmount, effectNow->remainingSeconds}
                                       : EffectState{});
        };

        switch (effect.kind)
        {
            case PotionEffectKind::Buff:
            {
                const CharacterBuffState *pBuff = party.characterBuff(memberIndex, effect.buffId);
                running(pBuff != nullptr && pBuff->active()
                        ? std::optional<RunningEffect>(RunningEffect{pBuff->power, pBuff->remainingSeconds})
                        : std::nullopt,
                    amount);

                // A condition that stops the buff (Haste while weak): the drink would not give it.
                if (!effect.conditions.empty() && member.conditions.test(size_t(effect.conditions.front())))
                {
                    states.back().counts = false;
                }
                break;
            }
            case PotionEffectKind::PartyBuff:
            {
                const PartyBuffState *pBuff = party.partyBuff(effect.partyBuffId);
                running(pBuff != nullptr && pBuff->active()
                        ? std::optional<RunningEffect>(RunningEffect{pBuff->power, pBuff->remainingSeconds})
                        : std::nullopt,
                    amount);
                break;
            }
            case PotionEffectKind::Immunity:
                for (const CharacterCondition condition : effect.conditions)
                {
                    running(runningPotionEffect(member, TimedPotionEffect::Kind::Immunity, uint32_t(condition)), 1);
                }
                break;
            case PotionEffectKind::AuraBuff:
                running(runningPotionEffect(member, TimedPotionEffect::Kind::Aura, effect.spellId), power);

                if (!rules.potionAuraCounts(effect.spellId, power))
                {
                    states.back().counts = false;
                }
                break;
            case PotionEffectKind::SkillBonus:
                running(runningPotionEffect(member, TimedPotionEffect::Kind::SkillBonus,
                            skillIdForSkillName(effect.skillName).value_or(0)),
                    amount);
                break;
            case PotionEffectKind::Regeneration:
                running(runningPotionEffect(member, TimedPotionEffect::Kind::Regeneration, 0), amount);
                break;
            default:
                break;
        }
    }

    return states;
}

// The bottles of the potion the party carries that can be drunk and have at least `minimumPower`, and their drinks.
struct CarriedStock
{
    uint32_t drinks = 0;
    uint32_t bottles = 0;
};

CarriedStock carriedStock(
    const Party &party,
    const PotionDefinition &potion,
    const PotionEffectTable &effects,
    std::optional<uint16_t> minimumPower)
{
    CarriedStock stock;
    const int bags = bagCount(party);

    for (const Character &member : party.members())
    {
        for (int bag = 0; bag < bags; ++bag)
        {
            for (const InventoryItem &item : InventoryBags::itemsInBag(member, uint8_t(bag)))
            {
                const int power = PotionUpkeep::bottlePower(effects, item);

                if (item.objectDescriptionId == potion.itemId && power >= potion.minimumPower
                    && power >= int(minimumPower.value_or(0)))
                {
                    stock.drinks += PotionUpkeep::bottleDrinks(potion, item);
                    ++stock.bottles;
                }
            }
        }
    }

    return stock;
}
}

bool PotionUpkeep::isUpkeepPotion(const PotionDefinition &potion)
{
    return std::any_of(potion.effects.begin(), potion.effects.end(),
        [](const PotionEffect &effect) { return isTimedEffect(effect.kind); });
}

BattleOrder PotionUpkeep::newOrder(uint32_t itemId, const PotionEffectTable &effects)
{
    BattleOrder order;
    order.kind = BattleOrderKind::Potion;
    order.potionItemId = itemId;
    order.renewBelowMinutes = UpkeepRenewDefaultMinutes;
    const PotionDefinition *pPotion = effects.find(itemId);
    const int perBottle = std::max(1, pPotion != nullptr ? pPotion->charges : 1);
    order.stockDrinks = uint8_t(std::min<int>(UpkeepStockMaximumDrinks, 2 * perBottle));
    return order;
}

int PotionUpkeep::bottlePower(const PotionEffectTable &effects, const InventoryItem &item)
{
    const int power = std::max(1, int(item.standardEnchantPower));
    return effects.powerCap() > 0 ? std::min(power, effects.powerCap()) : power;
}

uint32_t PotionUpkeep::bottleDrinks(const PotionDefinition &potion, const InventoryItem &item)
{
    return potion.charges <= 1  ? 1u
        : item.currentCharges > 0 ? uint32_t(item.currentCharges)
                                  : uint32_t(potion.charges);
}

uint32_t PotionUpkeep::carriedDrinks(
    const Party &party,
    const PotionDefinition &potion,
    const PotionEffectTable &effects,
    std::optional<uint16_t> minimumPower)
{
    return carriedStock(party, potion, effects, minimumPower).drinks;
}

bool PotionUpkeep::potionDue(
    const Party &party,
    size_t memberIndex,
    const PotionDefinition &potion,
    int power,
    float drinkSeconds,
    std::optional<uint16_t> renewBelowMinutes)
{
    if (party.member(memberIndex) == nullptr)
    {
        return false;
    }

    for (const EffectState &state : effectStates(party, memberIndex, potion, power))
    {
        if (state.counts && upkeepBuffDue(state.remainingSeconds, drinkSeconds, renewBelowMinutes))
        {
            return true;
        }
    }

    return false;
}

std::optional<float> PotionUpkeep::secondsLeft(
    const Party &party,
    size_t memberIndex,
    const PotionDefinition &potion,
    int power)
{
    std::optional<float> least;

    if (party.member(memberIndex) == nullptr)
    {
        return least;
    }

    for (const EffectState &state : effectStates(party, memberIndex, potion, power))
    {
        if (state.counts)
        {
            least = std::min(least.value_or(state.remainingSeconds), state.remainingSeconds);
        }
    }

    return least;
}

PotionUpkeep::OrderBottle PotionUpkeep::orderBottle(
    const Party &party,
    size_t memberIndex,
    const BattleOrder &order,
    const PotionEffectTable &effects)
{
    OrderBottle bottle;
    bottle.location = QuickItemSlots::findPartyItem(
        party, memberIndex, QuickItemSlot{order.potionItemId, order.bottleRule}, bagCount(party));
    const Character *pCarrier = bottle.location ? party.member(bottle.location->memberIndex) : nullptr;
    const InventoryItem *pItem = pCarrier != nullptr
        ? InventoryBags::itemInBagAt(*pCarrier, bottle.location->location.bag, bottle.location->location.gridX,
            bottle.location->location.gridY)
        : nullptr;

    if (pItem == nullptr)
    {
        bottle.location.reset();
        bottle.power = std::max(1, int(order.brewPower.value_or(1)));
        return bottle;
    }

    bottle.power = bottlePower(effects, *pItem);
    return bottle;
}

std::vector<PotionUpkeep::StockTarget> PotionUpkeep::stockTargets(const Party &party)
{
    std::vector<StockTarget> targets;

    for (const Character &member : party.members())
    {
        for (const BattleOrder &order : member.upkeepOrders)
        {
            if (!order.enabled || order.kind != BattleOrderKind::Potion || order.potionItemId == 0
                || order.stockDrinks == 0)
            {
                continue;
            }

            const auto found = std::find_if(targets.begin(), targets.end(),
                [&order](const StockTarget &target) { return target.itemId == order.potionItemId; });

            if (found == targets.end())
            {
                targets.push_back({order.potionItemId, order.stockDrinks, order.brewPower});
                continue;
            }

            found->drinks += order.stockDrinks;

            if (order.brewPower)
            {
                found->power = std::max(found->power.value_or(0), *order.brewPower);
            }
        }
    }

    return targets;
}

bool PotionUpkeep::RestockOutcome::brewedAny() const
{
    return std::any_of(lines.begin(), lines.end(), [](const RestockLine &line) { return line.brewedBottles > 0; });
}

PotionUpkeep::RestockOutcome PotionUpkeep::restock(
    Party &party,
    const AlchemyBenchTables &tables,
    const PotionEffectTable &effects,
    const AlchemyBenchRuntime::AutonoteLookup &isAutonoteUnlocked,
    bool keepMixedPotions)
{
    RestockOutcome outcome;
    const std::vector<StockTarget> targets = stockTargets(party);
    const AlchemistInfo alchemist = AlchemyBenchRuntime::resolveAlchemist(party);
    const auto bottlesFor = [](const PotionDefinition &potion, uint32_t drinks)
    {
        const uint32_t perBottle = uint32_t(std::max(1, potion.charges));
        return (drinks + perBottle - 1) / perBottle;
    };

    for (const StockTarget &target : targets)
    {
        const PotionDefinition *pPotion = effects.find(target.itemId);

        if (pPotion == nullptr)
        {
            continue;
        }

        const uint32_t carried = carriedDrinks(party, *pPotion, effects, target.power);

        if (carried >= target.drinks)
        {
            continue;
        }

        RestockLine line;
        line.itemId = target.itemId;
        line.wantedDrinks = target.drinks;
        line.carriedDrinks = carried;

        // Kept out of the mixes: every stocked potion's bottles that count toward its stock, this one's too (a weaker
        // bottle is still an ingredient, and a catalyst may raise it).
        std::vector<AlchemyItemCount> reserved;

        for (const StockTarget &other : targets)
        {
            if (const PotionDefinition *pOther = effects.find(other.itemId))
            {
                reserved.push_back({other.itemId, carriedStock(party, *pOther, effects, other.power).bottles});
            }
        }

        const AlchemyBook book = AlchemyBenchRuntime::buildBook(tables,
            AlchemyBenchRuntime::collectIngredients(party, tables), alchemist.mastery, isAutonoteUnlocked,
            keepMixedPotions);
        const AlchemyChainPlanner planner(party, book, alchemist, tables, keepMixedPotions, reserved);
        const uint32_t missingBottles = bottlesFor(*pPotion, target.drinks - carried);
        const AlchemyChainPlan plan = planner.plan(target.itemId, missingBottles, target.power);

        if (plan.brewCount == 0)
        {
            line.block = plan.block;
            line.blockItemId = plan.blockItemId;
            // Without a block, the chain could brew it, only not at the power asked.
            line.powerUnreached = plan.block == AlchemyChainBlock::None && target.power.has_value();
            outcome.lines.push_back(line);
            continue;
        }

        const AlchemyChainOutcome brewed = AlchemyBenchRuntime::brewChain(party, plan, tables);
        line.brewedBottles = brewed.brewedCount;
        line.complete = carriedDrinks(party, *pPotion, effects, target.power) >= target.drinks;

        if (!line.complete && plan.brewCount < missingBottles)
        {
            // The ingredients ran out after some: what blocks the next one.
            const AlchemyChainPlan next = AlchemyChainPlanner(party,
                AlchemyBenchRuntime::buildBook(tables, AlchemyBenchRuntime::collectIngredients(party, tables),
                    alchemist.mastery, isAutonoteUnlocked, keepMixedPotions),
                alchemist, tables, keepMixedPotions, reserved)
                .plan(target.itemId, 1, target.power);
            line.block = next.block;
            line.blockItemId = next.blockItemId;
            line.powerUnreached = next.brewCount == 0 && next.block == AlchemyChainBlock::None
                && target.power.has_value();
        }

        if (brewed.brewedCount > 0)
        {
            outcome.lastBrewed = brewed.lastBrewed;
            outcome.lastMix = brewed.lastMix;
        }

        outcome.lines.push_back(line);

        if (brewed.lastMix.overflowItem)
        {
            outcome.overflowItem = brewed.lastMix.overflowItem;
            break;
        }
    }

    return outcome;
}
}
