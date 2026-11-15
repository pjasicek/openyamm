#include "game/items/InventoryBags.h"
#include "game/items/InventoryItemUseRuntime.h"
#include "game/items/QuickItemSlots.h"
#include "game/party/Party.h"
#include "tests/RegressionGameData.h"

#include <doctest/doctest.h>

using OpenYAMM::Game::Character;
using OpenYAMM::Game::InventoryItem;
using OpenYAMM::Game::QuickItemBottleRule;
using OpenYAMM::Game::QuickItemSlot;
namespace QuickItemSlots = OpenYAMM::Game::QuickItemSlots;

namespace
{
InventoryItem bottle(uint32_t itemId, uint16_t power, uint8_t gridX)
{
    InventoryItem item;
    item.objectDescriptionId = itemId;
    item.standardEnchantPower = power;
    item.gridX = gridX;
    return item;
}
}

TEST_CASE("a quick item slot uses the weakest bottle of its kind, or the strongest when asked")
{
    // The potion radial (GAPS.md H.6): a slot holds a kind; the weakest bottle by default saves the strong ones.
    Character member;
    member.inventory = {bottle(222, 40, 0), bottle(222, 12, 1), bottle(223, 5, 2), bottle(222, 60, 3)};
    QuickItemSlot slot;
    slot.itemId = 222;

    std::optional<QuickItemSlots::Location> found = QuickItemSlots::findItem(member, slot, 1);
    REQUIRE(found.has_value());
    CHECK_EQ(found->gridX, 1);

    slot.bottleRule = QuickItemBottleRule::Strongest;
    found = QuickItemSlots::findItem(member, slot, 1);
    REQUIRE(found.has_value());
    CHECK_EQ(found->gridX, 3);

    CHECK_EQ(QuickItemSlots::countItems(member, slot, 1), 3u);
    slot.itemId = 230;
    CHECK_FALSE(QuickItemSlots::findItem(member, slot, 1).has_value());
    CHECK_EQ(QuickItemSlots::countItems(member, slot, 1), 0u);
    CHECK_FALSE(QuickItemSlots::findItem(member, QuickItemSlot{}, 1).has_value());
}

TEST_CASE("a quick item slot uses the owner's bottle first, else another member's")
{
    // The slot draws on the whole party (user, 2026-10-25): the owner's bags first, then the others' in party order.
    OpenYAMM::Game::Party party;
    OpenYAMM::Game::Party::Snapshot snapshot = party.snapshot();
    snapshot.members.assign(3, Character{});
    snapshot.members[1].inventory = {bottle(222, 40, 0)};
    snapshot.members[2].inventory = {bottle(222, 10, 4), bottle(222, 20, 5)};
    party.restoreSnapshot(snapshot);
    QuickItemSlot slot;
    slot.itemId = 222;

    std::optional<QuickItemSlots::PartyLocation> found = QuickItemSlots::findPartyItem(party, 2, slot, 1);
    REQUIRE(found.has_value());
    CHECK_EQ(found->memberIndex, 2u);
    CHECK_EQ(found->location.gridX, 4);

    found = QuickItemSlots::findPartyItem(party, 0, slot, 1);
    REQUIRE(found.has_value());
    CHECK_EQ(found->memberIndex, 1u);
    CHECK_EQ(found->location.gridX, 0);

    CHECK_EQ(QuickItemSlots::countPartyItems(party, slot, 1), 3u);
    slot.itemId = 230;
    CHECK_FALSE(QuickItemSlots::findPartyItem(party, 0, slot, 1).has_value());
}

TEST_CASE("the basebar popups list each potion and scroll kind the party carries once, by power")
{
    // level_generation/ui/potion_scroll_popups_20261102: one entry per kind and strength, with who carries it.
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    OpenYAMM::Game::Party party;
    OpenYAMM::Game::Party::Snapshot snapshot = party.snapshot();
    snapshot.members.assign(3, Character{});
    // 222 Cure Wounds, 233 Recharge Item (poured on wands, nothing to drink), 301 a Fire Bolt scroll, 1 a sword.
    snapshot.members[0].inventory = {bottle(222, 10, 0), bottle(301, 0, 1), bottle(1, 0, 2)};
    snapshot.members[2].inventory = {bottle(222, 10, 0), bottle(222, 30, 1), bottle(233, 20, 2)};
    party.restoreSnapshot(snapshot);

    const std::vector<QuickItemSlots::PartyItemKind> kinds = QuickItemSlots::partyItemKinds(
        party, gameData.itemTable, &gameData.mergedPotionSettingTable, nullptr, 1);
    REQUIRE_EQ(kinds.size(), 3u);
    CHECK_EQ(kinds[0].itemId, 222u);
    CHECK_EQ(kinds[0].power, 10);
    CHECK_EQ(kinds[0].count, 2u);
    CHECK_EQ(kinds[0].carriers, std::vector<size_t>{0, 2});
    CHECK_FALSE(kinds[0].scroll);
    CHECK_EQ(kinds[1].itemId, 301u);
    CHECK(kinds[1].scroll);
    CHECK_EQ(kinds[2].power, 30);
    CHECK_EQ(kinds[2].carriers, std::vector<size_t>{2});

    // The chosen member's own bottle first, else the first carrier's in party order.
    std::optional<QuickItemSlots::PartyLocation> found = QuickItemSlots::findPartyItemOfPower(party, 2, 222, 10, 1);
    REQUIRE(found.has_value());
    CHECK_EQ(found->memberIndex, 2u);
    found = QuickItemSlots::findPartyItemOfPower(party, 1, 222, 30, 1);
    REQUIRE(found.has_value());
    CHECK_EQ(found->memberIndex, 2u);
    CHECK_EQ(found->location.gridX, 1);
    CHECK_FALSE(QuickItemSlots::findPartyItemOfPower(party, 0, 222, 20, 1).has_value());
}

TEST_CASE("a potion preview says what a drink would restore and cure without drinking it")
{
    using OpenYAMM::Game::CharacterCondition;
    using OpenYAMM::Game::InventoryItemUseRuntime;
    using OpenYAMM::Game::PotionPreview;

    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    Character member;
    member.maxHealth = 100;
    member.health = 60;
    member.maxSpellPoints = 0;
    OpenYAMM::Game::PartySeed seed;
    seed.members = {member};
    OpenYAMM::Game::Party party;
    party.seed(seed);
    const int maximum = OpenYAMM::Game::Party::effectiveMaximumHealth(*party.member(0));
    party.member(0)->health = maximum - 40;

    // Standard Cure Wounds heals 10 + power, up to the maximum.
    PotionPreview preview =
        InventoryItemUseRuntime::previewPotion(party, 0, bottle(222, 20, 0), gameData.mergedPotionSettingTable);
    CHECK(preview.known);
    CHECK_EQ(preview.healthGain, 30);
    CHECK_EQ(preview.healthBefore, maximum - 40);
    CHECK_FALSE(preview.noEffectNow());
    preview = InventoryItemUseRuntime::previewPotion(party, 0, bottle(222, 50, 0), gameData.mergedPotionSettingTable);
    CHECK_EQ(preview.healthGain, 40);
    CHECK_EQ(party.member(0)->health, maximum - 40);

    // Cure Poison does nothing for a member who is not poisoned; Magic Potion nothing without spell points; Haste is
    // a buff, never "no effect".
    CHECK(InventoryItemUseRuntime::previewPotion(party, 0, bottle(226, 20, 0), gameData.mergedPotionSettingTable)
              .noEffectNow());
    CHECK(InventoryItemUseRuntime::previewPotion(party, 0, bottle(223, 20, 0), gameData.mergedPotionSettingTable)
              .noEffectNow());
    CHECK_FALSE(InventoryItemUseRuntime::previewPotion(party, 0, bottle(228, 20, 0), gameData.mergedPotionSettingTable)
                    .noEffectNow());
    party.member(0)->conditions.set(static_cast<size_t>(CharacterCondition::PoisonMedium));
    preview = InventoryItemUseRuntime::previewPotion(party, 0, bottle(226, 20, 0), gameData.mergedPotionSettingTable);
    CHECK_EQ(preview.cures, std::vector<CharacterCondition>{CharacterCondition::PoisonMedium});
}

TEST_CASE("sorting every bag sends crafting and alchemy items to the bags tagged for them")
{
    using OpenYAMM::Game::BagTag;
    using OpenYAMM::Game::Party;
    using OpenYAMM::Game::PartySeed;
    namespace InventoryBags = OpenYAMM::Game::InventoryBags;

    const auto item = [](uint32_t itemId, uint8_t gridX)
    {
        InventoryItem result;
        result.objectDescriptionId = itemId;
        result.width = 1;
        result.height = 1;
        result.gridX = gridX;
        return result;
    };
    // 1050 a crafting material, 222 a reagent, 1 a sword (the rules' bagTag, by id here).
    const auto bagTagOf = [](const InventoryItem &stored) -> std::optional<BagTag>
    {
        return stored.objectDescriptionId == 1050 ? std::optional<BagTag>(BagTag::Crafting)
            : stored.objectDescriptionId == 222   ? std::optional<BagTag>(BagTag::Alchemy)
                                                  : std::nullopt;
    };

    PartySeed seed;
    seed.members = {Character{}};
    Party party;
    party.seed(seed);
    Character &member = *party.member(0);
    member.inventory = {item(1050, 0), item(222, 1), item(1, 2)};
    InventoryBags::toggleTag(member, 2, BagTag::Alchemy);
    InventoryBags::toggleTag(member, 3, BagTag::Crafting);

    // The open bag alone keeps everything: it has nowhere else to put an item.
    REQUIRE(InventoryBags::sortPartyBags(party, {0}, false, 4, bagTagOf));
    CHECK_EQ(InventoryBags::itemsInBag(member, 0).size(), 3u);

    REQUIRE(InventoryBags::sortPartyBags(party, {0}, true, 4, bagTagOf));
    REQUIRE_EQ(InventoryBags::itemsInBag(member, 0).size(), 1u);
    CHECK_EQ(InventoryBags::itemsInBag(member, 0)[0].objectDescriptionId, 1u);
    REQUIRE_EQ(InventoryBags::itemsInBag(member, 2).size(), 1u);
    CHECK_EQ(InventoryBags::itemsInBag(member, 2)[0].objectDescriptionId, 222u);
    REQUIRE_EQ(InventoryBags::itemsInBag(member, 3).size(), 1u);
    CHECK_EQ(InventoryBags::itemsInBag(member, 3)[0].objectDescriptionId, 1050u);
}

TEST_CASE("sorting a tab sends what finds no bag of its kind there to the next tab's bags of its kind (OY-651)")
{
    using OpenYAMM::Game::BagTag;
    using OpenYAMM::Game::Party;
    using OpenYAMM::Game::PartySeed;
    namespace InventoryBags = OpenYAMM::Game::InventoryBags;

    // A reagent (222) as large as a whole bag, so each takes one bag; a sword (1) of one cell.
    const auto item = [](uint32_t itemId, bool wholeBag)
    {
        InventoryItem result;
        result.objectDescriptionId = itemId;
        result.width = wholeBag ? uint8_t(Character::InventoryWidth) : 1;
        result.height = wholeBag ? uint8_t(Character::InventoryHeight) : 1;
        return result;
    };
    const auto bagTagOf = [](const InventoryItem &stored) -> std::optional<BagTag>
    {
        return stored.objectDescriptionId == 222 ? std::optional<BagTag>(BagTag::Alchemy) : std::nullopt;
    };

    PartySeed seed;
    seed.members = {Character{}};
    Party party;
    party.seed(seed);
    Character &member = *party.member(0);
    constexpr int BagCount = 8;

    // Tab I (bags 0-3) all alchemy bags, holding five bag-sized reagents and a sword (more than fits: the sort reads
    // a bag's items as a list); tab II has an untagged bag 4 with a shield in it and the alchemy bag 5.
    for (uint8_t bag = 0; bag < 4; ++bag)
    {
        InventoryBags::toggleTag(member, bag, BagTag::Alchemy);
    }

    InventoryBags::toggleTag(member, 5, BagTag::Alchemy);
    member.inventory = {item(222, true)};
    member.rulesetState.storedBags[1] = {item(222, true)};
    member.rulesetState.storedBags[2] = {item(222, true)};
    member.rulesetState.storedBags[3] = {item(222, true)};
    InventoryItem shield = item(2, false);
    member.rulesetState.storedBags[4] = {shield};
    // A fifth reagent and the sword in bag 3 too: a sort takes every item of the tab's bags as one list.
    member.rulesetState.storedBags[3].push_back(item(222, true));
    member.rulesetState.storedBags[3].push_back(item(1, false));

    REQUIRE(InventoryBags::sortPartyBags(party, {0}, true, BagCount, bagTagOf));

    // Tab I's four alchemy bags take four reagents; the fifth goes to tab II's alchemy bag, not its untagged one, and
    // the sword to tab II's untagged bag beside the shield.
    for (uint8_t bag = 0; bag < 4; ++bag)
    {
        REQUIRE_EQ(InventoryBags::itemsInBag(member, bag).size(), 1u);
        CHECK_EQ(InventoryBags::itemsInBag(member, bag)[0].objectDescriptionId, 222u);
    }

    REQUIRE_EQ(InventoryBags::itemsInBag(member, 5).size(), 1u);
    CHECK_EQ(InventoryBags::itemsInBag(member, 5)[0].objectDescriptionId, 222u);
    REQUIRE_EQ(InventoryBags::itemsInBag(member, 4).size(), 2u);
    CHECK_EQ(InventoryBags::itemsInBag(member, 4)[0].objectDescriptionId, 2u);
    CHECK_EQ(InventoryBags::itemsInBag(member, 4)[1].objectDescriptionId, 1u);
    CHECK_EQ(member.rulesetState.currentBag, 0);

    // Without the next tab (four bags) the same items no longer fit: nothing changes.
    Party small;
    small.seed(seed);
    Character &alone = *small.member(0);

    for (uint8_t bag = 0; bag < 4; ++bag)
    {
        InventoryBags::toggleTag(alone, bag, BagTag::Alchemy);
    }

    alone.inventory = {item(222, true), item(222, true), item(222, true), item(222, true), item(222, true)};
    CHECK_FALSE(InventoryBags::sortPartyBags(small, {0}, true, 4, bagTagOf));
}

TEST_CASE("giving the party an item keeps every pointer to its members valid")
{
    using OpenYAMM::Game::Party;
    using OpenYAMM::Game::PartySeed;

    // An attack holds its attacker while the kill's reward (MAW's map completion) gives the party items; replacing
    // the member list there freed the attacker and crashed the attack.
    PartySeed seed;
    seed.members = {Character{}, Character{}};
    Party party;
    party.seed(seed);
    const Character *pFirst = party.member(0);
    const Character *pSecond = party.member(1);
    InventoryItem gem;
    gem.objectDescriptionId = 1050;
    gem.width = 1;
    gem.height = 1;

    size_t recipient = 99;
    REQUIRE(party.tryGrantInventoryItemStartingAt(1, gem, &recipient));
    CHECK_EQ(recipient, 1u);
    CHECK_EQ(party.member(0), pFirst);
    CHECK_EQ(party.member(1), pSecond);
    CHECK_EQ(pSecond->inventory.size(), 1u);
    CHECK(pFirst->inventory.empty());
}
