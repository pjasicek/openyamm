#include "game/gameplay/GameplayLootFilter.h"

#include "game/gameplay/CombatLog.h"
#include "game/party/Party.h"
#include "game/rules/GameRules.h"
#include "game/rules/ItemRules.h"
#include "game/tables/ItemTable.h"

#include <algorithm>

namespace OpenYAMM::Game
{
int meanPartyLevel(const Party *pParty)
{
    if (pParty == nullptr || pParty->members().empty())
    {
        return 0;
    }

    int total = 0;

    for (const Character &member : pParty->members())
    {
        total += int(member.level);
    }

    return total / int(pParty->members().size());
}

FilteredLoot filterDroppedLoot(
    InventoryItem &item,
    const ItemDefinition &definition,
    const Party *pParty,
    const StandardItemEnchantTable *pStandardTable,
    const SpecialItemEnchantTable *pSpecialTable)
{
    const ItemRules &rules = gameRulesFor(pParty).items;
    const RulesetLootFilter *pFilter = rules.lootFilter();
    const std::optional<LootFilterFacts> facts =
        pFilter != nullptr ? rules.lootFilterFacts(item, definition) : std::nullopt;

    if (!facts)
    {
        return {};
    }

    const int partyLevel = meanPartyLevel(pParty);
    const int gold = std::max(1, rules.filteredLootGold(item, definition, pStandardTable, pSpecialTable));

    if (RecentLootDrops *pRecent = rules.recentLootDrops())
    {
        pRecent->add({*facts, partyLevel, gold});
    }

    FilteredLoot result;
    result.verdict = evaluateLootFilter(*pFilter, *facts, partyLevel);

    if (result.verdict == LootFilterVerdict::Ground)
    {
        item.rulesetFields.lootFiltered = 1;
    }
    else if (result.verdict == LootFilterVerdict::Gold)
    {
        result.gold = uint32_t(gold);

        if (CombatLog *pLog = boundCombatLog())
        {
            CombatLogEntry entry;
            entry.kind = CombatLogKind::Loot;
            entry.target = definition.name;
            entry.rarity = lootFilterRarityName(facts->rarity);
            entry.amount = gold;

            // nameColor is 0xRRGGBB; the panel's colours are ABGR.
            if (const std::optional<uint32_t> color = rules.nameColor(item))
            {
                entry.rarityColor =
                    0xff000000u | ((*color & 0xffu) << 16) | (*color & 0xff00u) | ((*color >> 16) & 0xffu);
            }

            pLog->add(std::move(entry), false);
        }
    }

    return result;
}
}
