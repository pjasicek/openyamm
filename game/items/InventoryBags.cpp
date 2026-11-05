#include "game/items/InventoryBags.h"

#include "game/party/Party.h"
#include "game/tables/ItemTable.h"

#include <algorithm>
#include <array>
#include <functional>
#include <optional>
#include <string>
#include <string_view>
#include <tuple>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
using BagGrid = std::array<bool, Character::InventoryWidth * Character::InventoryHeight>;

// The first free place for the item, column by column, as Character::addInventoryItem looks.
std::optional<std::pair<uint8_t, uint8_t>> firstFreePlace(const BagGrid &occupied, uint8_t width, uint8_t height)
{
    for (int x = 0; x + width <= Character::InventoryWidth; ++x)
    {
        for (int y = 0; y + height <= Character::InventoryHeight; ++y)
        {
            bool free = true;

            for (int offsetY = 0; offsetY < height && free; ++offsetY)
            {
                for (int offsetX = 0; offsetX < width && free; ++offsetX)
                {
                    free = !occupied[size_t(y + offsetY) * Character::InventoryWidth + size_t(x + offsetX)];
                }
            }

            if (free)
            {
                return std::pair(uint8_t(x), uint8_t(y));
            }
        }
    }

    return std::nullopt;
}

void occupy(BagGrid &occupied, const InventoryItem &item)
{
    for (int y = item.gridY; y < item.gridY + item.height; ++y)
    {
        for (int x = item.gridX; x < item.gridX + item.width; ++x)
        {
            occupied[size_t(y) * Character::InventoryWidth + size_t(x)] = true;
        }
    }
}

bool reachableBag(int bag, int bagCount)
{
    return bag >= 0 && bag < std::max(1, bagCount);
}

// The `bagCount` bags from `firstBag` that a sort of every bag covers: all of them, or with several tabs (a party of
// one) the open bag's tab.
struct BagRange
{
    int firstBag = 0;
    int bagCount = 1;

    bool contains(int bag) const
    {
        return bag >= firstBag && bag < firstBag + bagCount;
    }
};

BagRange sortedBagRange(const Character &character, int bagCount)
{
    const int count = std::max(1, bagCount);

    if (count <= InventoryBags::TabBags)
    {
        return {0, count};
    }

    const int first = InventoryBags::tabFirstBag(character.rulesetState.currentBag);
    return {first, std::clamp(count - first, 1, InventoryBags::TabBags)};
}

// The items of the open bag, or of every bag in the range.
std::vector<InventoryItem> bagItems(const Character &character, bool allBags, const BagRange &range)
{
    std::vector<InventoryItem> items = character.inventory;

    for (const auto &[bag, stored] : character.rulesetState.storedBags)
    {
        if (allBags && range.contains(bag))
        {
            items.insert(items.end(), stored.begin(), stored.end());
        }
    }

    return items;
}

// The cells the items of a bag cover.
BagGrid occupiedCells(const std::vector<InventoryItem> &items)
{
    BagGrid occupied = {};

    for (const InventoryItem &item : items)
    {
        occupy(occupied, item);
    }

    return occupied;
}

// MAW's sort order (zzMaw-Item-Sorter.lua): the tallest first (1.5 for a wide item one cell tall), then by skill and
// item id.
// An item's skill as the engine numbers it (const.Skills), which MAW's sort compares: the weapons and armour from Staff
// (0) to Plate (11), then Misc (12), then clubs (39); anything else after them.
int engineSkillNumber(const std::string &skillGroup)
{
    static constexpr std::array<std::string_view, 13> Skills = {
        "Staff", "Sword", "Dagger", "Axe", "Spear", "Bow", "Mace", "Blaster", "Shield", "Leather", "Chain", "Plate",
        "Misc"};
    const auto found = std::find(Skills.begin(), Skills.end(), skillGroup);

    if (found != Skills.end())
    {
        return int(found - Skills.begin());
    }

    return skillGroup == "Club" ? 39 : 40;
}

void sortByMawOrder(std::vector<InventoryItem> &items, const ItemTable *pItemTable)
{
    // Tallest first (a wide item one cell tall counts 1.5), then the skill's number, then the item id
    // (zzMaw-Item-Sorter.lua:155-167).
    const auto sortKey =
        [pItemTable](const InventoryItem &item)
        {
            const double size = item.height == 1 && item.width > 1 ? 1.5 : double(item.height);
            const ItemDefinition *pDefinition = pItemTable != nullptr ? pItemTable->get(item.objectDescriptionId)
                                                                      : nullptr;
            return std::tuple(-size, pDefinition != nullptr ? engineSkillNumber(pDefinition->skillGroup) : 40,
                item.objectDescriptionId);
        };
    std::stable_sort(items.begin(), items.end(),
        [&sortKey](const InventoryItem &left, const InventoryItem &right)
        {
            return sortKey(left) < sortKey(right);
        });
}

// Places the items in order into `bagCount` bags, filled column by column from the first bag on; a full bag is not
// looked at again (MAW moves on to the next bag for good). Returns what did not fit.
std::vector<InventoryItem> packIntoBags(
    const std::vector<InventoryItem> &items,
    int bagCount,
    std::vector<std::vector<InventoryItem>> &bags)
{
    bags.assign(size_t(std::max(1, bagCount)), {});
    std::vector<BagGrid> grids(bags.size());
    std::vector<InventoryItem> leftovers;
    size_t firstOpenBag = 0;

    for (InventoryItem item : items)
    {
        item.width = std::max<uint8_t>(1, item.width);
        item.height = std::max<uint8_t>(1, item.height);
        bool placed = false;

        for (size_t bag = firstOpenBag; bag < bags.size() && !placed; ++bag)
        {
            const std::optional<std::pair<uint8_t, uint8_t>> place =
                firstFreePlace(grids[bag], item.width, item.height);

            if (!place)
            {
                firstOpenBag = bag + 1;
                continue;
            }

            item.gridX = place->first;
            item.gridY = place->second;
            occupy(grids[bag], item);
            bags[bag].push_back(item);
            placed = true;
        }

        if (!placed)
        {
            leftovers.push_back(item);
        }
    }

    return leftovers;
}

// packIntoBags for a member whose bags carry tags: an item with a tag goes to the bags with that tag first, then to the
// untagged bags, then to the bags of the other tag; an item without one to the untagged bags first. Each item takes the
// first bag of its order with room (pickups route by the tags the same way, placeInTaggedBag).
std::vector<InventoryItem> packIntoTaggedBags(
    const std::vector<InventoryItem> &items,
    const BagRange &range,
    const Character &character,
    const std::function<std::optional<BagTag>(const InventoryItem &)> &bagTagOf,
    std::vector<std::vector<InventoryItem>> &bags)
{
    const int count = std::max(1, range.bagCount);
    // Packed bag `bag` is the range's bag firstBag + bag.
    const auto tagOfBag = [&character, &range](int bag) -> std::optional<BagTag>
    {
        for (const BagTag tag : {BagTag::Crafting, BagTag::Alchemy})
        {
            if (InventoryBags::hasTag(character, uint8_t(range.firstBag + bag), tag))
            {
                return tag;
            }
        }

        return std::nullopt;
    };
    bool tagged = false;

    for (int bag = 0; bag < count; ++bag)
    {
        tagged = tagged || tagOfBag(bag).has_value();
    }

    if (!tagged || !bagTagOf)
    {
        return packIntoBags(items, count, bags);
    }

    bags.assign(size_t(count), {});
    std::vector<BagGrid> grids(bags.size());
    std::vector<InventoryItem> leftovers;

    for (InventoryItem item : items)
    {
        item.width = std::max<uint8_t>(1, item.width);
        item.height = std::max<uint8_t>(1, item.height);
        const std::optional<BagTag> itemTag = bagTagOf(item);
        std::vector<int> order;

        for (const int pass : {0, 1, 2})
        {
            for (int bag = 0; bag < count; ++bag)
            {
                const std::optional<BagTag> bagTag = tagOfBag(bag);
                const int rank = itemTag && bagTag == itemTag ? 0 : !bagTag ? 1 : 2;

                if (rank == pass)
                {
                    order.push_back(bag);
                }
            }
        }

        bool placed = false;

        for (const int bag : order)
        {
            const std::optional<std::pair<uint8_t, uint8_t>> place =
                firstFreePlace(grids[size_t(bag)], item.width, item.height);

            if (place)
            {
                item.gridX = place->first;
                item.gridY = place->second;
                occupy(grids[size_t(bag)], item);
                bags[size_t(bag)].push_back(item);
                placed = true;
                break;
            }
        }

        if (!placed)
        {
            leftovers.push_back(item);
        }
    }

    return leftovers;
}

// Puts packed bags back: the first is the open bag when only it was sorted; else packed bag i is the range's bag
// firstBag + i, the same one open.
void storeBags(Character &character, std::vector<std::vector<InventoryItem>> bags, bool allBags, const BagRange &range)
{
    CharacterRulesetState &state = character.rulesetState;

    if (!allBags)
    {
        character.inventory = std::move(bags.front());
        return;
    }

    std::erase_if(state.storedBags,
        [&range](const auto &entry)
        {
            return range.contains(entry.first);
        });
    character.inventory.clear();

    for (size_t index = 0; index < bags.size(); ++index)
    {
        const uint8_t bag = uint8_t(range.firstBag + int(index));

        if (bag == state.currentBag)
        {
            character.inventory = std::move(bags[index]);
        }
        else if (!bags[index].empty())
        {
            state.storedBags[bag] = std::move(bags[index]);
        }
    }
}
}

namespace InventoryBags
{
bool openBag(Character &character, uint8_t bag, int bagCount)
{
    CharacterRulesetState &state = character.rulesetState;

    if (bag == state.currentBag || !reachableBag(int(bag), bagCount))
    {
        return false;
    }

    if (!character.inventory.empty())
    {
        state.storedBags[state.currentBag] = std::move(character.inventory);
    }

    character.inventory.clear();
    const auto stored = state.storedBags.find(bag);

    if (stored != state.storedBags.end())
    {
        character.inventory = std::move(stored->second);
        state.storedBags.erase(stored);
    }

    state.currentBag = bag;
    return true;
}

bool sortAllBags(Character &character, int bagCount, const ItemTable *pItemTable)
{
    const BagRange range = {0, std::max(1, bagCount)};
    std::vector<InventoryItem> items = bagItems(character, true, range);
    sortByMawOrder(items, pItemTable);
    std::vector<std::vector<InventoryItem>> bags;

    if (!packIntoBags(items, range.bagCount, bags).empty())
    {
        return false;
    }

    storeBags(character, std::move(bags), true, range);
    return true;
}

bool sortPartyBags(
    Party &party,
    const std::vector<size_t> &members,
    bool allBags,
    int bagCount,
    std::optional<size_t> alchemist,
    const std::function<std::optional<int>(const InventoryItem &)> &alchemyRank,
    const std::function<std::optional<BagTag>(const InventoryItem &)> &bagTagOf)
{
    const ItemTable *pItemTable = party.itemTable();
    std::vector<size_t> sorted = members;

    if (alchemist && std::find(sorted.begin(), sorted.end(), *alchemist) == sorted.end())
    {
        sorted.push_back(*alchemist);
    }

    // What each member keeps, and the alchemy items that go to the alchemist with their owners.
    std::vector<std::vector<InventoryItem>> kept(party.members().size());
    std::vector<std::pair<InventoryItem, size_t>> alchemyItems;

    for (const size_t memberIndex : sorted)
    {
        const Character *pMember = party.member(memberIndex);

        if (pMember == nullptr)
        {
            return false;
        }

        for (const InventoryItem &item : bagItems(*pMember, allBags, sortedBagRange(*pMember, bagCount)))
        {
            if (alchemist && alchemyRank(item))
            {
                alchemyItems.emplace_back(item, memberIndex);
            }
            else
            {
                kept[memberIndex].push_back(item);
            }
        }
    }

    std::stable_sort(alchemyItems.begin(), alchemyItems.end(),
        [&alchemyRank](const auto &left, const auto &right)
        {
            return *alchemyRank(left.first) < *alchemyRank(right.first);
        });
    std::vector<std::vector<std::vector<InventoryItem>>> packed(party.members().size());
    // Sorting every bag honours the member's bag tags; the open bag alone has nowhere else to send an item.
    const auto packMember = [&](size_t memberIndex, const std::vector<InventoryItem> &items)
    {
        const Character &member = *party.member(memberIndex);
        return allBags
            ? packIntoTaggedBags(items, sortedBagRange(member, bagCount), member, bagTagOf, packed[memberIndex])
            : packIntoBags(items, 1, packed[memberIndex]);
    };

    if (alchemist)
    {
        // The alchemist takes what fits after their own items; the other members' alchemy items that do not, the
        // last first, stay with their owners.
        sortByMawOrder(kept[*alchemist], pItemTable);

        while (true)
        {
            std::vector<InventoryItem> items;

            for (const auto &[item, owner] : alchemyItems)
            {
                items.push_back(item);
            }

            items.insert(items.end(), kept[*alchemist].begin(), kept[*alchemist].end());

            if (packMember(*alchemist, items).empty())
            {
                break;
            }

            const auto lastForeign = std::find_if(alchemyItems.rbegin(), alchemyItems.rend(),
                [&alchemist](const auto &entry)
                {
                    return entry.second != *alchemist;
                });

            if (lastForeign == alchemyItems.rend())
            {
                return false;
            }

            kept[lastForeign->second].push_back(lastForeign->first);
            alchemyItems.erase(std::next(lastForeign).base());
        }
    }

    for (const size_t memberIndex : sorted)
    {
        if (alchemist && memberIndex == *alchemist)
        {
            continue;
        }

        sortByMawOrder(kept[memberIndex], pItemTable);

        if (!packMember(memberIndex, kept[memberIndex]).empty())
        {
            return false;
        }
    }

    for (const size_t memberIndex : sorted)
    {
        Character &member = *party.member(memberIndex);
        storeBags(member, std::move(packed[memberIndex]), allBags, sortedBagRange(member, bagCount));
    }

    return true;
}

size_t fitIntoBagCount(Party &party, int bagCount)
{
    const int bags = std::max(1, bagCount);
    // The items of the bags past the count, with their owners.
    std::vector<std::pair<InventoryItem, size_t>> overflow;

    for (size_t memberIndex = 0; memberIndex < party.members().size(); ++memberIndex)
    {
        Character &member = *party.member(memberIndex);
        CharacterRulesetState &state = member.rulesetState;

        // A member whose open bag is gone opens the first.
        if (state.currentBag >= bags)
        {
            if (!member.inventory.empty())
            {
                state.storedBags[state.currentBag] = std::move(member.inventory);
            }

            member.inventory.clear();
            const auto first = state.storedBags.find(0);

            if (first != state.storedBags.end())
            {
                member.inventory = std::move(first->second);
                state.storedBags.erase(first);
            }

            state.currentBag = 0;
        }

        for (auto entry = state.storedBags.begin(); entry != state.storedBags.end();)
        {
            if (reachableBag(entry->first, bags))
            {
                ++entry;
                continue;
            }

            for (const InventoryItem &item : entry->second)
            {
                overflow.emplace_back(item, memberIndex);
            }

            entry = state.storedBags.erase(entry);
        }
    }

    // Into the owner's first free place, bag by bag, then any other member's.
    const auto place = [&party, bags](size_t memberIndex, InventoryItem item)
    {
        Character &member = *party.member(memberIndex);

        for (int bag = 0; bag < bags; ++bag)
        {
            const uint8_t bagIndex = uint8_t(bag);
            const std::optional<std::pair<uint8_t, uint8_t>> free = firstFreePlace(
                occupiedCells(itemsInBag(member, bagIndex)), std::max<uint8_t>(1, item.width),
                std::max<uint8_t>(1, item.height));

            if (!free)
            {
                continue;
            }

            item.gridX = free->first;
            item.gridY = free->second;
            (bagIndex == member.rulesetState.currentBag ? member.inventory : member.rulesetState.storedBags[bagIndex])
                .push_back(item);
            return true;
        }

        return false;
    };
    size_t left = 0;

    for (const auto &[item, owner] : overflow)
    {
        bool placed = place(owner, item);

        for (size_t memberIndex = 0; memberIndex < party.members().size() && !placed; ++memberIndex)
        {
            placed = memberIndex != owner && place(memberIndex, item);
        }

        // What fits nowhere waits for takeOverflow.
        if (!placed)
        {
            party.member(owner)->rulesetState.storedBags[InventoryBags::OverflowBag].push_back(item);
            ++left;
        }
    }

    return left;
}

std::vector<InventoryItem> takeOverflow(Character &character)
{
    std::vector<InventoryItem> items;
    const auto overflow = character.rulesetState.storedBags.find(OverflowBag);

    if (overflow != character.rulesetState.storedBags.end())
    {
        items = std::move(overflow->second);
        character.rulesetState.storedBags.erase(overflow);
    }

    return items;
}

size_t storedItemCount(const Character &character)
{
    size_t count = 0;

    for (const auto &[bag, items] : character.rulesetState.storedBags)
    {
        count += items.size();
    }

    return count;
}

const std::vector<InventoryItem> &itemsInBag(const Character &character, uint8_t bag)
{
    static const std::vector<InventoryItem> NoItems;

    if (bag == character.rulesetState.currentBag)
    {
        return character.inventory;
    }

    const auto stored = character.rulesetState.storedBags.find(bag);
    return stored != character.rulesetState.storedBags.end() ? stored->second : NoItems;
}

const InventoryItem *itemInBagAt(const Character &character, uint8_t bag, uint8_t gridX, uint8_t gridY)
{
    for (const InventoryItem &item : itemsInBag(character, bag))
    {
        if (gridX >= item.gridX && gridX < item.gridX + std::max<uint8_t>(1, item.width)
            && gridY >= item.gridY && gridY < item.gridY + std::max<uint8_t>(1, item.height))
        {
            return &item;
        }
    }

    return nullptr;
}

InventoryItem *itemInBagAt(Character &character, uint8_t bag, uint8_t gridX, uint8_t gridY)
{
    return const_cast<InventoryItem *>(itemInBagAt(std::as_const(character), bag, gridX, gridY));
}

bool withBagOpen(Party &party, size_t memberIndex, uint8_t bag, int bagCount, const std::function<bool()> &operation)
{
    Character *pMember = party.member(memberIndex);

    if (pMember == nullptr || !reachableBag(int(bag), bagCount))
    {
        return false;
    }

    const uint8_t openBagIndex = pMember->rulesetState.currentBag;

    if (bag == openBagIndex)
    {
        return operation();
    }

    openBag(*pMember, bag, bagCount);
    const bool done = operation();
    openBag(*pMember, openBagIndex, bagCount);
    return done;
}

bool placeInBag(
    Party &party,
    size_t memberIndex,
    uint8_t bag,
    int bagCount,
    const InventoryItem &item,
    uint8_t gridX,
    uint8_t gridY,
    std::optional<InventoryItem> &replacedItem)
{
    replacedItem.reset();
    return withBagOpen(party, memberIndex, bag, bagCount,
        [&]() { return party.tryPlaceItemInMemberInventoryCell(memberIndex, item, gridX, gridY, replacedItem); });
}

PlacementPreview previewPlaceInBag(
    const Character &character,
    uint8_t bag,
    const InventoryItem &item,
    uint8_t gridX,
    uint8_t gridY)
{
    // The real placement on a copy of the bag's items.
    Character probe;
    probe.inventory = itemsInBag(character, bag);
    PlacementPreview preview;
    preview.fits = probe.tryPlaceInventoryItemAt(item, gridX, gridY, preview.replacedItem);

    if (preview.fits && !probe.inventory.empty())
    {
        preview.gridX = probe.inventory.back().gridX;
        preview.gridY = probe.inventory.back().gridY;
    }
    else
    {
        preview.gridX = gridX;
        preview.gridY = gridY;
        preview.replacedItem.reset();
    }

    return preview;
}

bool hasTag(const Character &character, uint8_t bag, BagTag tag)
{
    const uint8_t tags =
        tag == BagTag::Crafting ? character.rulesetState.craftingBags : character.rulesetState.alchemyBags;
    return bag < 8 && (tags & (1u << bag)) != 0;
}

bool toggleTag(Character &character, uint8_t bag, BagTag tag)
{
    if (bag >= 8)
    {
        return false;
    }

    uint8_t &tags = tag == BagTag::Crafting ? character.rulesetState.craftingBags : character.rulesetState.alchemyBags;
    tags ^= uint8_t(1u << bag);
    return (tags & (1u << bag)) != 0;
}

std::optional<size_t> placeInTaggedBag(
    Party &party,
    size_t pickerIndex,
    const InventoryItem &item,
    BagTag tag,
    int bagCount)
{
    const size_t memberCount = party.members().size();

    for (size_t offset = 0; offset < memberCount; ++offset)
    {
        const size_t memberIndex = offset == 0 ? pickerIndex : (offset <= pickerIndex ? offset - 1 : offset);

        if (memberIndex >= memberCount)
        {
            continue;
        }

        for (int bag = 0; bag < bagCount; ++bag)
        {
            if (hasTag(*party.member(memberIndex), uint8_t(bag), tag)
                && withBagOpen(party, memberIndex, uint8_t(bag), bagCount,
                    [&]() { return party.tryGrantInventoryItemToMember(memberIndex, item); }))
            {
                return memberIndex;
            }
        }
    }

    return std::nullopt;
}

bool takeFromBag(
    Party &party,
    size_t memberIndex,
    uint8_t bag,
    int bagCount,
    uint8_t gridX,
    uint8_t gridY,
    InventoryItem &item)
{
    return withBagOpen(party, memberIndex, bag, bagCount,
        [&]() { return party.takeItemFromMemberInventoryCell(memberIndex, gridX, gridY, item); });
}
}
}
