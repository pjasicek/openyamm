#include "doctest/doctest.h"

#include "game/events/EvtEnums.h"
#include "game/gameplay/BountyHuntRuntime.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/HouseInteraction.h"
#include "game/gameplay/HouseServiceRuntime.h"
#include "game/gameplay/NpcFollowerRuntime.h"
#include "game/gameplay/ReputationRuntime.h"
#include "game/gameplay/StealingRuntime.h"
#include "game/items/InventoryItemUseRuntime.h"
#include "game/items/ItemGenerator.h"
#include "game/items/ItemRuntime.h"
#include "game/items/PriceCalculator.h"
#include "game/party/Party.h"
#include "game/maps/SaveGame.h"
#include "game/party/SpellIds.h"
#include "game/party/PartySpellSystem.h"
#include "game/tables/MergedBaseTables.h"

#include "tests/RegressionGameData.h"
#include "tests/PartySpellTestHarness.h"

#include <algorithm>
#include <filesystem>
#include <random>

using namespace OpenYAMM::Game;

namespace
{
std::vector<std::string> monsterStatsRow(int id, const std::string &name, int level)
{
    std::vector<std::string> row(38);
    row[0] = std::to_string(id);
    row[1] = name;
    row[2] = name;
    row[3] = std::to_string(level);
    row[4] = "20";
    row[5] = "5";
    row[10] = "Short";
    row[11] = "Normal";
    row[12] = "0";
    row[13] = "100";
    row[14] = "100";
    row[17] = "Phys";
    row[18] = "1d6";
    return row;
}

MonsterTable makeBountyMonsterTable()
{
    MonsterTable table;
    REQUIRE(table.loadStatsFromRows({
        monsterStatsRow(10, "Allowed", 12),
        monsterStatsRow(11, "Excluded", 8),
        monsterStatsRow(12, "Too High", 80),
    }));
    return table;
}

MergedBolsterMonsterTable makeBountyBolsterMonsterTable()
{
    MergedBolsterMonsterTable table;
    REQUIRE(table.loadFromRows({
        {
            "#",
            "Note",
            "Type",
            "ExtraType",
            "Creed",
            "Gender",
            "Style",
            "PrefMagic",
            "NoBounty",
            "Ranged",
            "Spells",
            "HPBySize",
            "Replicate",
            "Summons",
            "SummonId",
            "Extra",
            "MaxHP",
        },
        {"10", "Allowed", "Human", "", "Neutral", "", "", "", "-", "-", "-", "-", "-", "-", "", "", ""},
        {"11", "Excluded", "Human", "", "Neutral", "", "", "", "x", "-", "-", "-", "-", "-", "", "", ""},
        {"12", "Too High", "Human", "", "Neutral", "", "", "", "-", "-", "-", "-", "-", "-", "", "", ""},
    }));
    return table;
}

Party makeOneMemberParty()
{
    Character member = {};
    member.name = "Tester";
    member.might = 10;
    member.intellect = 10;
    member.personality = 10;
    member.endurance = 10;
    member.accuracy = 10;
    member.speed = 10;
    member.luck = 10;
    member.maxHealth = 50;
    member.health = 50;
    member.maxSpellPoints = 30;
    member.spellPoints = 30;

    PartySeed seed = {};
    seed.members = {member};

    Party party = {};
    party.seed(seed);
    return party;
}

uint32_t findFirstItemIdByEquipStat(const ItemTable &itemTable, const std::string &equipStat, bool needsIdentify)
{
    for (const ItemDefinition &entry : itemTable.entries())
    {
        if (entry.itemId != 0
            && entry.equipStat == equipStat
            && (!needsIdentify || ItemRuntime::requiresIdentification(entry)))
        {
            return entry.itemId;
        }
    }

    return 0;
}
}

TEST_CASE("MM7 bounty hunt runtime filters no-bounty monsters and claims monthly reward")
{
    MonsterTable monsterTable = makeBountyMonsterTable();
    MergedBolsterMonsterTable bolsterTable = makeBountyBolsterMonsterTable();

    const std::vector<int16_t> ids = collectBountyHuntMonsterIds(monsterTable, &bolsterTable, 30);
    REQUIRE_EQ(ids.size(), 1u);
    CHECK_EQ(ids.front(), 10);

    BountyHuntEntry entry = {};
    entry.month = 3;
    entry.monsterId = 10;

    CHECK(markBountyHuntMonsterKilled(entry, 10, 3));
    CHECK(entry.done);

    const BountyHuntClaimResult claim = claimBountyHuntReward(entry, monsterTable, 3, true);
    CHECK(claim.claimed);
    CHECK_EQ(claim.goldReward, 1200u);
    CHECK_EQ(claim.bountyTotalDelta, 1200u);
    CHECK_EQ(claim.reputationDelta, -1);
    CHECK(entry.claimed);
}

TEST_CASE("MMerge bounty hunt reward applies gold total bounty award and reputation")
{
    BountyHuntClaimResult claim = {};
    claim.claimed = true;
    claim.goldReward = 1200;
    claim.bountyTotalDelta = 1200;
    claim.reputationDelta = -1;

    Party party = makeOneMemberParty();
    OpenYAMM::Tests::PartySpellTestWorldRuntime worldRuntime = {};
    worldRuntime.setCurrentLocationReputation(0);

    applyBountyHuntClaimResult(worldRuntime, &party, claim);

    CHECK_EQ(party.gold(), 1200);
    CHECK_EQ(party.eventVariableValue(static_cast<uint16_t>(EvtVariable::NumBounties)), 1200);
    CHECK_EQ(party.eventVariableValue(static_cast<uint16_t>(EvtVariable::ArenaWinsPage)), 0);
    CHECK(party.hasAward(44));
    CHECK_EQ(worldRuntime.currentLocationReputation(), -1);
}

TEST_CASE("MMerge bounty hunt interaction creates map entry and hostile target")
{
    MonsterTable monsterTable = makeBountyMonsterTable();
    MergedBolsterMonsterTable bolsterTable = makeBountyBolsterMonsterTable();
    Party party = makeOneMemberParty();
    OpenYAMM::Tests::PartySpellTestWorldRuntime worldRuntime = {};
    EventRuntimeState state = {};
    worldRuntime.bindParty(&party);
    worldRuntime.bindEventRuntimeState(&state);
    worldRuntime.bindMonsterTable(&monsterTable);
    worldRuntime.bindMergedBolsterMonsterTable(&bolsterTable);
    worldRuntime.setMapName("new_sorpigal.odm");
    worldRuntime.setPartyPosition(100.0f, 200.0f, 300.0f);
    worldRuntime.setBountyHuntSpawnPoint(GameplayWorldPoint{444.0f, 555.0f, 666.0f});

    const BountyHuntInteractionResult result = performBountyHuntInteraction(worldRuntime, &party, true);

    REQUIRE(result.succeeded);
    REQUIRE_EQ(result.messages.size(), 1u);
    CHECK(result.messages.front().find("Allowed") != std::string::npos);
    CHECK_EQ(state.namedGlobalVars["MMerge.BountyHunt.new_sorpigal.odm.Month"], 0);
    CHECK_EQ(state.namedGlobalVars["MMerge.BountyHunt.new_sorpigal.odm.MonsterId"], 10);
    CHECK_EQ(state.namedGlobalVars["MMerge.BountyHunt.new_sorpigal.odm.Done"], 0);
    CHECK_EQ(state.namedGlobalVars["MMerge.BountyHunt.new_sorpigal.odm.Claimed"], 0);
    REQUIRE_EQ(worldRuntime.hostileSummonRequests().size(), 1u);
    CHECK_EQ(worldRuntime.hostileSummonRequests().front().monsterId, 10);
    CHECK_EQ(worldRuntime.hostileSummonRequests().front().group, 39u);
    CHECK_EQ(worldRuntime.hostileSummonRequests().front().x, 444.0f);
    CHECK_EQ(worldRuntime.hostileSummonRequests().front().y, 555.0f);
    CHECK_EQ(worldRuntime.hostileSummonRequests().front().z, 666.0f);
}

TEST_CASE("MMerge runtime bounty kill marker scans all active monthly entries")
{
    MonsterTable monsterTable = makeBountyMonsterTable();
    OpenYAMM::Tests::PartySpellTestWorldRuntime worldRuntime = {};
    EventRuntimeState state = {};
    worldRuntime.bindEventRuntimeState(&state);
    worldRuntime.setMapName("map_b.odm");
    worldRuntime.setCurrentLocationReputation(0);

    state.namedGlobalVars["MMerge.BountyHunt.map_a.odm.Month"] = 0;
    state.namedGlobalVars["MMerge.BountyHunt.map_a.odm.MonsterId"] = 10;
    state.namedGlobalVars["MMerge.BountyHunt.map_b.odm.Month"] = 0;
    state.namedGlobalVars["MMerge.BountyHunt.map_b.odm.MonsterId"] = 10;
    state.namedGlobalVars["MMerge.BountyHunt.claimed.odm.Month"] = 0;
    state.namedGlobalVars["MMerge.BountyHunt.claimed.odm.MonsterId"] = 10;
    state.namedGlobalVars["MMerge.BountyHunt.claimed.odm.Claimed"] = 1;
    state.namedGlobalVars["MMerge.BountyHunt.expired.odm.Month"] = 1;
    state.namedGlobalVars["MMerge.BountyHunt.expired.odm.MonsterId"] = 10;

    CHECK(markRuntimeBountyHuntMonsterKilled(worldRuntime, 10, &monsterTable));
    CHECK_EQ(state.namedGlobalVars["MMerge.BountyHunt.map_a.odm.Done"], 1);
    CHECK_EQ(state.namedGlobalVars["MMerge.BountyHunt.map_b.odm.Done"], 1);
    CHECK_EQ(state.namedGlobalVars["MMerge.BountyHunt.claimed.odm.Done"], 0);
    CHECK_EQ(state.namedGlobalVars["MMerge.BountyHunt.expired.odm.Done"], 0);
    CHECK_EQ(worldRuntime.currentLocationReputation(), -1);
}

TEST_CASE("MMerge extra potion drink effects apply and one-shot essence potions do not stack")
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();

    Party party = makeOneMemberParty();
    Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);

    InventoryItem essence = {};
    essence.objectDescriptionId = 272;
    essence.standardEnchantPower = 20;

    InventoryItemUseResult first = InventoryItemUseRuntime::useItemOnMember(
        party,
        0,
        essence,
        gameData.itemTable,
        &gameData.readableScrollTable,
        &gameData.mergedPotionSettingTable);
    CHECK(first.consumed);
    CHECK_EQ(pMember->might, 25u);
    CHECK_EQ(pMember->intellect, 5u);

    // Each drink costs the member recovery; the checks are about the potions, so recover before the next.
    pMember->recoverySecondsRemaining = 0.0f;
    InventoryItemUseResult second = InventoryItemUseRuntime::useItemOnMember(
        party,
        0,
        essence,
        gameData.itemTable,
        &gameData.readableScrollTable,
        &gameData.mergedPotionSettingTable);
    CHECK_FALSE(second.consumed);
    CHECK_EQ(pMember->might, 25u);

    InventoryItem protection = {};
    protection.objectDescriptionId = 290;
    protection.standardEnchantPower = 2;
    pMember->recoverySecondsRemaining = 0.0f;
    InventoryItemUseResult protectionResult = InventoryItemUseRuntime::useItemOnMember(
        party,
        0,
        protection,
        gameData.itemTable,
        &gameData.readableScrollTable,
        &gameData.mergedPotionSettingTable);
    CHECK(protectionResult.consumed);
    CHECK(party.hasPartyBuff(PartyBuffId::ProtectionFromMagic));
}

TEST_CASE("potion strength scales drink effects as in MM8")
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();

    Party party = makeOneMemberParty();
    Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);

    const auto drink =
        [&](uint32_t itemId, uint16_t power)
        {
            InventoryItem potion = {};
            potion.objectDescriptionId = itemId;
            potion.standardEnchantPower = power;
            // Each drink costs the member recovery; these checks are about strength, so recover before each.
            pMember->recoverySecondsRemaining = 0.0f;
            return InventoryItemUseRuntime::useItemOnMember(
                party,
                0,
                potion,
                gameData.itemTable,
                &gameData.readableScrollTable,
                &gameData.mergedPotionSettingTable);
        };
    constexpr float SecondsPerPower = 30.0f * 60.0f;

    pMember->health = 10;
    REQUIRE(drink(222, 7).consumed);
    CHECK_EQ(pMember->health, 27);
    pMember->spellPoints = 0;
    REQUIRE(drink(223, 4).consumed);
    CHECK_EQ(pMember->spellPoints, 14);
    pMember->health = 10;
    REQUIRE(drink(253, 4).consumed);
    CHECK_EQ(pMember->health, 30);

    REQUIRE(drink(240, 4).consumed);
    const CharacterBuffState *pMight = party.characterBuff(0, CharacterBuffId::TempMight);
    REQUIRE(pMight != nullptr);
    CHECK_EQ(pMight->power, 12);
    CHECK_EQ(pMight->remainingSeconds, doctest::Approx(4.0f * SecondsPerPower));
    party.clearPartyBuff(PartyBuffId::TorchLight);
    CHECK_EQ(pMember->magicalBonuses.might, 12);
    REQUIRE(drink(240, 1).consumed);
    CHECK_EQ(party.characterBuff(0, CharacterBuffId::TempMight)->power, 12);

    REQUIRE(drink(256, 2).consumed);
    CHECK_EQ(pMember->magicalBonuses.resistances.fire, 6);

    REQUIRE(drink(230, 3).consumed);
    const CharacterBuffState *pBless = party.characterBuff(0, CharacterBuffId::Bless);
    REQUIRE(pBless != nullptr);
    CHECK_EQ(pBless->power, 5);
    CHECK_EQ(pBless->remainingSeconds, doctest::Approx(3.0f * SecondsPerPower));

    REQUIRE(drink(235, 2).consumed);
    CHECK_FALSE(party.hasPartyBuff(PartyBuffId::WaterWalk));
    CHECK(pMember->waterWalking);

    REQUIRE(drink(228, 1).consumed);
    CHECK_FALSE(party.hasPartyBuff(PartyBuffId::Haste));
    REQUIRE(party.hasCharacterBuff(0, CharacterBuffId::Haste));
    CHECK_EQ(pMember->attackRecoveryReductionTicks, 25);
    party.advanceTimedStates(SecondsPerPower + 1.0f);
    CHECK_FALSE(party.hasCharacterBuff(0, CharacterBuffId::Haste));
    CHECK(pMember->conditions.test(static_cast<size_t>(CharacterCondition::Weak)));
    REQUIRE(drink(228, 1).consumed);
    CHECK_FALSE(party.hasCharacterBuff(0, CharacterBuffId::Haste));
}

TEST_CASE("potion buffs survive a save and older saves still load")
{
    Party party = makeOneMemberParty();
    party.applyCharacterBuff(0, CharacterBuffId::BodyResistance, 600.0f, 9, 0, 0, SkillMastery::Master, 0);
    party.applyCharacterBuff(0, CharacterBuffId::Glamour, 600.0f, 4, 0, 0, SkillMastery::Master, 0);
    GameSaveData save;
    save.mapFileName = "out02.odm";
    save.party = party.snapshot();
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "openyamm_potion_buffs.oysav";
    std::string error;
    REQUIRE(saveGameDataToPath(path, save, error));
    const std::optional<GameSaveData> loaded = loadGameDataFromPath(path, error);
    std::filesystem::remove(path);
    REQUIRE(loaded.has_value());
    Party restored;
    restored.restoreSnapshot(loaded->party);
    REQUIRE(restored.hasCharacterBuff(0, CharacterBuffId::BodyResistance));
    CHECK_EQ(restored.member(0)->magicalBonuses.resistances.body, 9);
    CHECK_EQ(restored.characterBuff(0, CharacterBuffId::Glamour)->power, 4);
}

TEST_CASE("potions get their power from where they come from")
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());
    const ItemTable &itemTable = OpenYAMM::Tests::regressionGameData().itemTable;
    std::mt19937 rng(1234);

    for (int attempt = 0; attempt < 50; ++attempt)
    {
        InventoryItem treasure = ItemGenerator::makeInventoryItem(222, itemTable, ItemGenerationMode::ChestLoot);
        ItemGenerator::assignTreasurePotionPower(treasure, itemTable, 3, rng);
        CHECK(treasure.standardEnchantPower >= 6);
        CHECK(treasure.standardEnchantPower <= 24);
        CHECK_EQ(treasure.standardEnchantPower % 3, 0);

        InventoryItem placed = ItemGenerator::makeInventoryItem(240, itemTable, ItemGenerationMode::Generic);
        ItemGenerator::assignPlacedPotionPower(placed, itemTable, rng);
        CHECK(placed.standardEnchantPower >= 5);
        CHECK(placed.standardEnchantPower <= 19);

        InventoryItem carried = ItemGenerator::makeInventoryItem(221, itemTable, ItemGenerationMode::MonsterLoot);
        ItemGenerator::assignMonsterPotionPower(carried, itemTable, rng);
        CHECK(carried.standardEnchantPower >= 2);
        CHECK(carried.standardEnchantPower <= 8);
        CHECK_EQ(carried.standardEnchantPower % 2, 0);
    }

    InventoryItem bottle = ItemGenerator::makeInventoryItem(220, itemTable, ItemGenerationMode::Shop);
    ItemGenerator::assignTreasurePotionPower(bottle, itemTable, 6, rng);
    CHECK_EQ(bottle.standardEnchantPower, 0);

    InventoryItem brewed = ItemGenerator::makeInventoryItem(222, itemTable, ItemGenerationMode::Generic);
    brewed.standardEnchantPower = 40;
    ItemGenerator::assignPlacedPotionPower(brewed, itemTable, rng);
    CHECK_EQ(brewed.standardEnchantPower, 40);

    const ItemDefinition *pMm9Potion = itemTable.get(1766);
    REQUIRE(pMm9Potion != nullptr);
    CHECK_FALSE(pMm9Potion->hasPotionPower);

    const std::optional<InventoryItem> generated = ItemGenerator::generateRandomInventoryItem(
        itemTable,
        OpenYAMM::Tests::regressionGameData().standardItemEnchantTable,
        OpenYAMM::Tests::regressionGameData().specialItemEnchantTable,
        ItemGenerationRequest{.treasureLevel = 1, .mode = ItemGenerationMode::ChestLoot},
        nullptr,
        rng,
        [](const ItemDefinition &entry)
        {
            return entry.itemId == 222;
        });
    REQUIRE(generated.has_value());
    CHECK(generated->standardEnchantPower >= 2);
    CHECK(generated->standardEnchantPower <= 8);
}

TEST_CASE("MMerge stealing runtime resolves success, caught failure, and monster distance")
{
    Character thief = {};
    thief.speed = 50;
    thief.luck = 10;
    thief.skills["Stealing"] = {"Stealing", 10, SkillMastery::Master};

    CHECK_EQ(stealingTotalSkill(thief), 30);
    CHECK_EQ(stealingRecoveryTicks(thief), 95);

    StealingAttemptInput shop = {};
    shop.targetKind = StealingTargetKind::Shop;
    shop.itemValue = 500;
    shop.successRoll = 25;
    const StealingAttemptResult success = resolveStealingAttempt(thief, shop);
    CHECK(success.handled);
    CHECK(success.outcome == StealingOutcomeKind::Success);
    CHECK(success.stoleItem);

    shop.successRoll = 1;
    shop.caughtRoll = 0;
    const StealingAttemptResult caught = resolveStealingAttempt(thief, shop);
    CHECK(caught.outcome == StealingOutcomeKind::FailedCaught);
    CHECK(caught.breakInvisibility);
    CHECK_GT(caught.fineDelta, 0);

    StealingAttemptInput monster = {};
    monster.targetKind = StealingTargetKind::Monster;
    monster.monsterLevel = 20;
    monster.distanceSquared = 20000 * 9 + 1;
    const StealingAttemptResult tooFar = resolveStealingAttempt(thief, monster);
    CHECK(tooFar.outcome == StealingOutcomeKind::TooFar);

    monster.distanceSquared = 0;
    monster.successRoll = 20;
    monster.reputationSensitiveTarget = false;
    const StealingAttemptResult neutralMonster = resolveStealingAttempt(thief, monster);
    CHECK(neutralMonster.outcome == StealingOutcomeKind::Success);
    CHECK_EQ(neutralMonster.reputationDelta, 0);
}

TEST_CASE("MMerge runtime bounty kill marker persists to named globals")
{
    MonsterTable monsterTable = makeBountyMonsterTable();
    OpenYAMM::Tests::PartySpellTestWorldRuntime worldRuntime = {};
    EventRuntimeState state = {};
    worldRuntime.bindEventRuntimeState(&state);

    state.namedGlobalVars["MMerge.BountyHunt.spell_test.odm.Month"] = 0;
    state.namedGlobalVars["MMerge.BountyHunt.spell_test.odm.MonsterId"] = 10;
    worldRuntime.setCurrentLocationReputation(0);

    CHECK(markRuntimeBountyHuntMonsterKilled(worldRuntime, 10, &monsterTable));
    CHECK_EQ(state.namedGlobalVars["MMerge.BountyHunt.spell_test.odm.Done"], 1);
    CHECK_EQ(worldRuntime.currentLocationReputation(), -1);
}

TEST_CASE("MMerge town hall fine payment clears party fines")
{
    Party party = makeOneMemberParty();
    party.addGold(200);
    party.addFineGold(150);

    HouseEntry townHall = {};
    townHall.type = "Town Hall";
    townHall.name = "Test Town Hall";

    const std::vector<HouseActionOption> options =
        buildHouseActionOptions(townHall, &party, nullptr, nullptr, 0.0f, DialogueMenuId::None);
    CHECK(std::any_of(options.begin(), options.end(), [](const HouseActionOption &option)
    {
        return option.id == HouseActionId::TownHallPayFine && option.enabled;
    }));

    HouseActionOption payFine = {};
    payFine.id = HouseActionId::TownHallPayFine;
    const HouseActionResult result = performHouseAction(payFine, townHall, party, nullptr, nullptr);
    CHECK(result.succeeded);
    CHECK_EQ(party.fineGold(), 0);
    CHECK_EQ(party.gold(), 50);
}

TEST_CASE("MMerge bad reputation toggles guard hostility requests")
{
    OpenYAMM::Tests::PartySpellTestWorldRuntime worldRuntime = {};
    EventRuntimeState state = {};
    worldRuntime.bindEventRuntimeState(&state);
    worldRuntime.setCurrentLocationReputation(19);

    addStoredCurrentLocationReputation(worldRuntime, 1);
    CHECK_EQ(state.actorGroupHostilityRequests[38], true);
    CHECK_EQ(state.actorGroupHostilityRequests[55], true);

    addStoredCurrentLocationReputation(worldRuntime, -1);
    CHECK_EQ(state.actorGroupHostilityRequests[38], false);
    CHECK_EQ(state.actorGroupHostilityRequests[55], false);
}

TEST_CASE("MMerge terrible reputation and theft bans disable shop service")
{
    Party party = makeOneMemberParty();
    OpenYAMM::Tests::PartySpellTestWorldRuntime worldRuntime = {};
    EventRuntimeState state = {};
    worldRuntime.bindEventRuntimeState(&state);
    worldRuntime.setCurrentLocationReputation(25);

    HouseEntry shop = {};
    shop.id = 1234;
    shop.type = "Weapon Shop";
    shop.name = "Test Weapon Shop";

    std::vector<HouseActionOption> options =
        buildHouseActionOptions(shop, &party, nullptr, &worldRuntime, 0.0f, DialogueMenuId::None);
    REQUIRE_FALSE(options.empty());
    CHECK(std::all_of(options.begin(), options.end(), [](const HouseActionOption &option)
    {
        return !option.enabled;
    }));

    worldRuntime.setCurrentLocationReputation(0);
    state.namedGlobalVars["MMerge.ShopBanUntil.1234"] = 1000;
    options = buildHouseActionOptions(shop, &party, nullptr, &worldRuntime, 10.0f, DialogueMenuId::None);
    REQUIRE_FALSE(options.empty());
    CHECK(std::all_of(options.begin(), options.end(), [](const HouseActionOption &option)
    {
        return !option.enabled;
    }));
}

TEST_CASE("MMerge follower bonuses expose skill, gold, food, and item-service effects")
{
    EventRuntimeState state = {};
    state.hiredNpcFollowers.push_back({1001, 14, 150});
    state.hiredNpcFollowers.push_back({1002, 30, 250});
    state.hiredNpcFollowers.push_back({1003, 32, 300});
    state.hiredNpcFollowers.push_back({1004, 4, 100});

    CHECK_EQ(hiredNpcSkillBonus(state.hiredNpcFollowers, "Learning"), 20);
    CHECK_EQ(hiredNpcRestFoodReduction(state), 2);
    // The Banker raises 1000 to 1200; costs of 800 take 8% of that.
    const FoundGold foundGold = resolveFoundGold(1000, &state);
    CHECK_EQ(foundGold.amount, 1200u);
    CHECK_EQ(foundGold.followerShare, 96u);
    CHECK_EQ(foundGold.partyAmount, 1104u);
    CHECK_EQ(foundGoldStatusText(foundGold), "You found 1200 gold (followers take 96)!");

    // Any fee takes at least one coin, and cheap followers still count.
    EventRuntimeState cheapState = {};
    cheapState.hiredNpcFollowers.push_back({1005, 1, 1});
    const FoundGold smallFind = resolveFoundGold(20, &cheapState);
    CHECK_EQ(smallFind.followerShare, 1u);
    CHECK_EQ(smallFind.partyAmount, 19u);

    const FoundGold noFollowers = resolveFoundGold(20, nullptr);
    CHECK_EQ(noFollowers.partyAmount, 20u);
    CHECK_EQ(foundGoldStatusText(noFollowers), "You found 20 gold!");
    CHECK(hiredNpcHasProfession(state.hiredNpcFollowers, 4));
    CHECK_FALSE(hiredNpcCanRepairItemKind(state.hiredNpcFollowers, "Armor"));
}

TEST_CASE("MMerge follower luck and resistance bonuses are visible in character summaries")
{
    Character member = {};
    member.luck = 10;
    member.baseResistances.fire = 5;
    member.baseResistances.air = 6;
    member.baseResistances.water = 7;
    member.baseResistances.earth = 8;

    PartySeed seed = {};
    seed.members.push_back(member);
    Party party;
    party.seed(seed);
    party.addHiredNpcFollower({1001, 27, 100});
    party.addHiredNpcFollower({1002, 37, 100});

    const CharacterSheetSummary summary = GameMechanics::buildCharacterSheetSummary(*party.member(0), nullptr);
    CHECK_EQ(summary.luck.actual, 15);
    CHECK_EQ(summary.luck.base, 10);
    CHECK_EQ(summary.fireResistance.actual, 25);
    CHECK_EQ(summary.airResistance.actual, 26);
    CHECK_EQ(summary.waterResistance.actual, 27);
    CHECK_EQ(summary.earthResistance.actual, 28);
}

TEST_CASE("MMerge shop stealing integrates with stock and reputation")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    const HouseEntry *pHouseEntry = gameData.houseTable.get(1);
    REQUIRE(pHouseEntry != nullptr);

    Party party = makeOneMemberParty();
    party.setItemTable(&gameData.itemTable);
    party.setItemEnchantTables(&gameData.standardItemEnchantTable, &gameData.specialItemEnchantTable);
    party.addGold(1000);

    Character *pThief = party.activeMember();
    REQUIRE(pThief != nullptr);
    pThief->skills["Stealing"] = {"Stealing", 30, SkillMastery::Grandmaster};

    OpenYAMM::Tests::PartySpellTestWorldRuntime worldRuntime = {};
    worldRuntime.bindParty(&party);

    const std::vector<InventoryItem> &stock = HouseServiceRuntime::ensureStock(
        party,
        gameData.itemTable,
        gameData.standardItemEnchantTable,
        gameData.specialItemEnchantTable,
        *pHouseEntry,
        worldRuntime.gameMinutes(),
        HouseStockMode::ShopStandard);
    const auto stockIt = std::find_if(stock.begin(), stock.end(), [](const InventoryItem &item)
    {
        return item.objectDescriptionId != 0;
    });
    REQUIRE(stockIt != stock.end());

    const size_t slotIndex = static_cast<size_t>(std::distance(stock.begin(), stockIt));
    const size_t initialInventoryCount = party.inventoryItemCount();
    std::string statusText;
    HouseServiceRuntime::ShopItemServiceResult serviceResult = HouseServiceRuntime::ShopItemServiceResult::None;

    const bool stoleItem = HouseServiceRuntime::tryStealStockItem(
        party,
        worldRuntime,
        gameData.itemTable,
        gameData.standardItemEnchantTable,
        gameData.specialItemEnchantTable,
        *pHouseEntry,
        worldRuntime.gameMinutes(),
        HouseStockMode::ShopStandard,
        slotIndex,
        150u,
        1000000u,
        statusText,
        &serviceResult);

    INFO(statusText);
    INFO(static_cast<int>(serviceResult));
    REQUIRE(stoleItem);

    CHECK(serviceResult == HouseServiceRuntime::ShopItemServiceResult::Stolen);
    CHECK_EQ(party.inventoryItemCount(), initialInventoryCount + 1u);
    CHECK_EQ(worldRuntime.currentLocationReputation(), 1);

    // The stolen item leaves the shelf, so the slot cannot be stolen from again.
    const Party::HouseStockState *pStockState = party.houseStockState(pHouseEntry->id);
    REQUIRE(pStockState != nullptr);
    REQUIRE(slotIndex < pStockState->standardStock.size());
    CHECK_EQ(pStockState->standardStock[slotIndex].objectDescriptionId, 0u);

    CHECK_FALSE(HouseServiceRuntime::tryStealStockItem(
        party,
        worldRuntime,
        gameData.itemTable,
        gameData.standardItemEnchantTable,
        gameData.specialItemEnchantTable,
        *pHouseEntry,
        worldRuntime.gameMinutes(),
        HouseStockMode::ShopStandard,
        slotIndex,
        150u,
        1000000u,
        statusText,
        &serviceResult));
    CHECK(serviceResult == HouseServiceRuntime::ShopItemServiceResult::NoItem);
    CHECK_EQ(party.inventoryItemCount(), initialInventoryCount + 1u);
}

TEST_CASE("MMerge caught shop stealing records a house ban")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    const HouseEntry *pHouseEntry = gameData.houseTable.get(1);
    REQUIRE(pHouseEntry != nullptr);

    Party party = makeOneMemberParty();
    party.setItemTable(&gameData.itemTable);
    party.setItemEnchantTables(&gameData.standardItemEnchantTable, &gameData.specialItemEnchantTable);

    Character *pThief = party.activeMember();
    REQUIRE(pThief != nullptr);
    pThief->skills["Stealing"] = {"Stealing", 1, SkillMastery::Normal};

    EventRuntimeState runtimeState = {};
    OpenYAMM::Tests::PartySpellTestWorldRuntime worldRuntime = {};
    worldRuntime.bindParty(&party);
    worldRuntime.bindEventRuntimeState(&runtimeState);

    const std::vector<InventoryItem> &stock = HouseServiceRuntime::ensureStock(
        party,
        gameData.itemTable,
        gameData.standardItemEnchantTable,
        gameData.specialItemEnchantTable,
        *pHouseEntry,
        worldRuntime.gameMinutes(),
        HouseStockMode::ShopStandard);
    const auto stockIt = std::find_if(stock.begin(), stock.end(), [](const InventoryItem &item)
    {
        return item.objectDescriptionId != 0;
    });
    REQUIRE(stockIt != stock.end());

    const size_t slotIndex = static_cast<size_t>(std::distance(stock.begin(), stockIt));
    std::string statusText;
    HouseServiceRuntime::ShopItemServiceResult serviceResult = HouseServiceRuntime::ShopItemServiceResult::None;

    CHECK_FALSE(HouseServiceRuntime::tryStealStockItem(
        party,
        worldRuntime,
        gameData.itemTable,
        gameData.standardItemEnchantTable,
        gameData.specialItemEnchantTable,
        *pHouseEntry,
        worldRuntime.gameMinutes(),
        HouseStockMode::ShopStandard,
        slotIndex,
        0u,
        0u,
        statusText,
        &serviceResult));

    CHECK(serviceResult == HouseServiceRuntime::ShopItemServiceResult::TheftCaught);
    const std::string banVar = "MMerge.ShopBanUntil." + std::to_string(pHouseEntry->id);
    REQUIRE(runtimeState.namedGlobalVars.contains(banVar));
    CHECK_GT(runtimeState.namedGlobalVars[banVar], 0);
}

TEST_CASE("MMerge follower identify and repair helpers are shop service consumers")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    const uint32_t ringId = findFirstItemIdByEquipStat(gameData.itemTable, "Ring", true);
    const uint32_t armorId = findFirstItemIdByEquipStat(gameData.itemTable, "Armor", false);
    REQUIRE(ringId != 0);
    REQUIRE(armorId != 0);

    HouseEntry houseEntry = {};
    houseEntry.type = "Weapon Shop";
    houseEntry.priceMultiplier = 1.0f;

    Party party = makeOneMemberParty();
    party.setItemTable(&gameData.itemTable);
    party.setItemEnchantTables(&gameData.standardItemEnchantTable, &gameData.specialItemEnchantTable);
    party.addGold(10000);

    InventoryItem ring = {};
    ring.objectDescriptionId = ringId;
    ring.width = 1;
    ring.height = 1;
    ring.identified = false;
    REQUIRE(party.member(0)->addInventoryItemAt(ring, 0, 0));

    InventoryItem armor = {};
    armor.objectDescriptionId = armorId;
    armor.width = 2;
    armor.height = 3;
    armor.broken = true;
    REQUIRE(party.member(0)->addInventoryItemAt(armor, 2, 0));

    EventRuntimeState runtimeState = {};
    runtimeState.hiredNpcFollowers.push_back({1001, 4, 100});
    runtimeState.hiredNpcFollowers.push_back({1002, 2, 100});

    const int initialGold = party.gold();
    std::string statusText;
    HouseServiceRuntime::ShopItemServiceResult serviceResult = HouseServiceRuntime::ShopItemServiceResult::None;

    CHECK(HouseServiceRuntime::tryIdentifyInventoryItem(
        party,
        gameData.itemTable,
        gameData.standardItemEnchantTable,
        gameData.specialItemEnchantTable,
        houseEntry,
        0,
        0,
        0,
        statusText,
        &serviceResult,
        0,
        &runtimeState));
    CHECK(serviceResult == HouseServiceRuntime::ShopItemServiceResult::Success);
    CHECK_EQ(party.gold(), initialGold);

    CHECK(HouseServiceRuntime::tryRepairInventoryItem(
        party,
        gameData.itemTable,
        gameData.standardItemEnchantTable,
        gameData.specialItemEnchantTable,
        houseEntry,
        0,
        2,
        0,
        statusText,
        &serviceResult,
        0,
        &runtimeState));
    CHECK(serviceResult == HouseServiceRuntime::ShopItemServiceResult::Success);
    CHECK_EQ(party.gold(), initialGold);
}

TEST_CASE("hireling skill bonuses reach character gameplay values and disappear on dismissal")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const OpenYAMM::Tests::RegressionGameData &data = OpenYAMM::Tests::regressionGameData();
    Party party = makeOneMemberParty();
    party.setItemTable(&data.itemTable);
    Character *pMember = party.member(0);
    pMember->skills["Merchant"] = {"Merchant", 1, SkillMastery::Expert};
    pMember->skills["Perception"] = {"Perception", 1, SkillMastery::Expert};
    pMember->skills["DisarmTraps"] = {"DisarmTraps", 1, SkillMastery::Expert};
    pMember->skills["Sword"] = {"Sword", 1, SkillMastery::Normal};
    pMember->skills["PlateArmor"] = {"PlateArmor", 1, SkillMastery::Normal};
    pMember->equipment.mainHand = findFirstItemIdByEquipStat(data.itemTable, "Weapon", false);
    REQUIRE(pMember->equipment.mainHand != 0);
    const std::string weaponSkill = data.itemTable.get(pMember->equipment.mainHand)->skillGroup;
    pMember->skills[weaponSkill] = {weaponSkill, 1, SkillMastery::Normal};
    const CharacterSheetSummary before = GameMechanics::buildCharacterSheetSummary(*pMember, &data.itemTable);
    const int merchantBefore = PriceCalculator::playerMerchant(pMember, 0);

    party.addHiredNpcFollower({1001, 21, 200});
    party.addHiredNpcFollower({1002, 22, 300});
    party.addHiredNpcFollower({1003, 26, 300});
    party.addHiredNpcFollower({1004, 46, 600});
    CHECK_EQ(PriceCalculator::playerMerchant(pMember, 0), merchantBefore + 12);
    CHECK_EQ(party.bestPartyWideUtilitySkillValue("Perception"), 14);
    CHECK_EQ(party.bestPartyWideUtilitySkillValue("DisarmTraps"), 14);
    CHECK_EQ(pMember->skillBonus("PlateArmor"), 2);
    CHECK_EQ(pMember->skillBonus("Sword"), 2);
    const CharacterSheetSummary after = GameMechanics::buildCharacterSheetSummary(*pMember, &data.itemTable);
    CHECK(after.combat.attack > before.combat.attack);

    Party restored;
    restored.setItemTable(&data.itemTable);
    restored.restoreSnapshot(party.snapshot());
    CHECK_EQ(restored.member(0)->skillBonus("Sword"), 2);
    for (uint32_t npcId = 1001; npcId <= 1004; ++npcId)
    {
        party.removeHiredNpcFollower(npcId);
        restored.removeHiredNpcFollower(npcId);
    }
    CHECK_EQ(PriceCalculator::playerMerchant(pMember, 0), merchantBefore);
    CHECK_EQ(party.bestPartyWideUtilitySkillValue("DisarmTraps"), 2);
    CHECK_EQ(pMember->skillBonus("Sword"), 0);
    CHECK_EQ(restored.member(0)->skillBonus("Sword"), 0);
}

TEST_CASE("hireling profession bonuses match the merged descriptions")
{
    struct SkillBonusCase
    {
        uint32_t professionId;
        const char *pSkill;
        int bonus;
    };
    const SkillBonusCase cases[] = {
        {4, "Learning", 5}, {13, "Learning", 10}, {14, "Learning", 15},
        {15, "Sword", 2}, {16, "Sword", 3}, {17, "FireMagic", 2}, {18, "BodyMagic", 3},
        {19, "DarkMagic", 4}, {20, "Merchant", 4}, {21, "Merchant", 6}, {22, "Perception", 6},
        {25, "DisarmTraps", 4}, {26, "DisarmTraps", 6}, {46, "PlateArmor", 2},
        {47, "Perception", 5}, {48, "Merchant", 3}, {49, "Merchant", 4},
        {50, "Merchant", 8}, {51, "DisarmTraps", 8},
    };
    for (const SkillBonusCase &entry : cases)
    {
        CAPTURE(entry.professionId);
        Party party = makeOneMemberParty();
        party.addHiredNpcFollower({1001, entry.professionId, 100});
        CHECK_EQ(party.member(0)->skillBonus(entry.pSkill), entry.bonus);
        party.refreshDerivedState();
        CHECK_EQ(party.member(0)->skillBonus(entry.pSkill), entry.bonus);
        party.removeHiredNpcFollower(1001);
        CHECK_EQ(party.member(0)->skillBonus(entry.pSkill), 0);
    }
    for (uint32_t professionId : {4u, 13u, 14u})
    {
        Party party = makeOneMemberParty();
        party.member(0)->skills["Learning"] = {"Learning", 1, SkillMastery::Grandmaster};
        party.addHiredNpcFollower({1001, professionId, 100});
        const int bonus = professionId == 4 ? 5 : professionId == 13 ? 10 : 15;
        CHECK_EQ(party.grantSharedExperience(100), 114u + bonus);
        CHECK_EQ(party.member(0)->experience, 114u + bonus);
    }
    for (uint32_t professionId : {4u, 13u, 14u})
    {
        Party party = makeOneMemberParty();
        party.member(0)->skills.erase("Learning");
        party.addHiredNpcFollower({1001, professionId, 100});
        const int bonus = professionId == 4 ? 5 : professionId == 13 ? 10 : 15;
        CHECK_EQ(party.grantSharedExperience(100), 109u + bonus);
    }
}

TEST_CASE("hireling luck and elemental resistance reduce actual incoming damage")
{
    Party party = makeOneMemberParty();
    auto totalDamage = [&party](CombatDamageType type)
    {
        std::mt19937 rng(91);
        int damage = 0;
        for (int roll = 0; roll < 1000; ++roll)
        {
            damage += GameMechanics::resolveCharacterIncomingDamage(
                *party.member(0), nullptr, nullptr, nullptr, 100, type, rng);
        }
        return damage;
    };
    const int baselineFire = totalDamage(CombatDamageType::Fire);
    const int baselinePhysical = totalDamage(CombatDamageType::Physical);
    party.addHiredNpcFollower({1001, 37, 1000});
    CHECK(totalDamage(CombatDamageType::Fire) < baselineFire);
    CHECK_EQ(totalDamage(CombatDamageType::Physical), baselinePhysical);
    party.addHiredNpcFollower({1002, 28, 200});
    CHECK(totalDamage(CombatDamageType::Physical) < baselinePhysical);
    party.removeHiredNpcFollower(1001);
    party.removeHiredNpcFollower(1002);
    CHECK_EQ(totalDamage(CombatDamageType::Fire), baselineFire);
    CHECK_EQ(totalDamage(CombatDamageType::Physical), baselinePhysical);
    party.addHiredNpcFollower({1003, 47, 400});
    CHECK_EQ(GameMechanics::buildCharacterSheetSummary(*party.member(0), nullptr).luck.actual, 20);
}

TEST_CASE("Cartographer maintains expert Wizard Eye without overwriting real spell buffs")
{
    Party party = makeOneMemberParty();
    party.addHiredNpcFollower({1001, 38, 200});
    REQUIRE(party.hasPartyBuff(PartyBuffId::WizardEye));
    CHECK_EQ(party.partyBuff(PartyBuffId::WizardEye)->skillMastery, SkillMastery::Expert);
    party.advanceTimedStates(24.0f * 3600.0f);
    CHECK(party.hasPartyBuff(PartyBuffId::WizardEye));
    party.applyPartyBuff(PartyBuffId::WizardEye, 3600, 0, 19, 10, SkillMastery::Master, 0);
    CHECK_EQ(party.partyBuff(PartyBuffId::WizardEye)->skillMastery, SkillMastery::Master);
    party.removeHiredNpcFollower(1001);
    CHECK_EQ(party.partyBuff(PartyBuffId::WizardEye)->skillMastery, SkillMastery::Master);
    party.clearPartyBuff(PartyBuffId::WizardEye);
    CHECK_FALSE(party.hasPartyBuff(PartyBuffId::WizardEye));
    party.addHiredNpcFollower({1001, 38, 200});
    party.clearDispellableBuffs();
    CHECK(party.hasPartyBuff(PartyBuffId::WizardEye));
    Party restored;
    restored.restoreSnapshot(party.snapshot());
    CHECK(restored.hasPartyBuff(PartyBuffId::WizardEye));
    restored.removeHiredNpcFollower(1001);
    CHECK_FALSE(restored.hasPartyBuff(PartyBuffId::WizardEye));
}

TEST_CASE("repair hirelings repair their item families without skills or gold")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const ItemTable &items = OpenYAMM::Tests::regressionGameData().itemTable;
    struct RepairCase
    {
        uint32_t professionId;
        const char *pKind;
        EquipmentSlot slot;
    };
    const RepairCase cases[] = {
        {1, "Weapon", EquipmentSlot::MainHand}, {2, "Armor", EquipmentSlot::Armor},
        {3, "Ring", EquipmentSlot::Ring1},
    };
    for (const RepairCase &entry : cases)
    {
        CAPTURE(entry.professionId);
        Party party = makeOneMemberParty();
        party.setItemTable(&items);
        party.member(0)->skills.clear();
        const uint32_t itemId = findFirstItemIdByEquipStat(items, entry.pKind, false);
        REQUIRE(itemId != 0);
        const ItemDefinition *pDefinition = items.get(itemId);
        InventoryItem item = {};
        item.objectDescriptionId = itemId;
        item.width = std::max<uint8_t>(1, pDefinition->inventoryWidth);
        item.height = std::max<uint8_t>(1, pDefinition->inventoryHeight);
        item.broken = true;
        REQUIRE(party.member(0)->addInventoryItemAt(item, 0, 0));
        std::string status;
        CHECK_FALSE(party.tryRepairMemberInventoryItem(0, 0, 0, 0, status));
        party.addHiredNpcFollower({1001, entry.professionId, 200});
        const int gold = party.gold();
        CHECK(party.tryRepairMemberInventoryItem(0, 0, 0, 0, status));
        CHECK_FALSE(party.memberInventoryItem(0, 0, 0)->broken);
        CHECK_EQ(party.gold(), gold);
        if (entry.slot == EquipmentSlot::MainHand)
        {
            party.member(0)->equipment.mainHand = itemId;
        }
        if (entry.slot == EquipmentSlot::Armor)
        {
            party.member(0)->equipment.armor = itemId;
        }
        if (entry.slot == EquipmentSlot::Ring1)
        {
            party.member(0)->equipment.ring1 = itemId;
        }
        party.equippedItemRuntimeMutable(0, entry.slot)->broken = true;
        CHECK(party.tryRepairEquippedItem(0, entry.slot, 0, status));
        party.removeHiredNpcFollower(1001);
        CHECK_FALSE(party.canRepairItem(*pDefinition));
    }
}

TEST_CASE("hireling camping and walking reductions keep their advertised minimum")
{
    EventRuntimeState state;
    state.hiredNpcFollowers = {{1001, 29, 100}, {1002, 30, 200}, {1003, 48, 100}};
    CHECK_EQ(hiredNpcCampingFoodCost(5, state), 1);
    CHECK_EQ(hiredNpcCampingFoodCost(2, state), 1);
    CHECK_EQ(hiredNpcCampingFoodCost(0, state), 0);
    state.hiredNpcFollowers = {{1001, 5, 100}, {1002, 6, 200}, {1003, 7, 300}, {1004, 44, 100}};
    CHECK_EQ(hiredNpcWalkingTravelDays(10, state), 3);
    CHECK_EQ(hiredNpcWalkingTravelDays(5, state), 1);
    CHECK_EQ(hiredNpcWalkingTravelDays(0, state), 0);
}

TEST_CASE("hireling magic bonus increases real spell power")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const OpenYAMM::Tests::RegressionGameData &data = OpenYAMM::Tests::regressionGameData();
    Party party = makeOneMemberParty();
    party.member(0)->skills["SpiritMagic"] = {"SpiritMagic", 5, SkillMastery::Master};
    OpenYAMM::Tests::PartySpellTestWorldRuntime world;
    world.bindParty(&party);
    PartySpellCastRequest request;
    request.casterMemberIndex = 0;
    request.spellId = spellIdValue(SpellId::Bless);
    request.spendMana = false;
    request.applyRecovery = false;
    request.bypassGameplayCasterValidation = true;
    REQUIRE(PartySpellSystem::castSpell(party, world, data.spellTable, request).succeeded());
    const int originalPower = party.characterBuff(0, CharacterBuffId::Bless)->power;
    party.addHiredNpcFollower({1001, 19, 2000});
    REQUIRE(PartySpellSystem::castSpell(party, world, data.spellTable, request).succeeded());
    CHECK_EQ(party.characterBuff(0, CharacterBuffId::Bless)->skillLevel, 9u);
    CHECK(party.characterBuff(0, CharacterBuffId::Bless)->power > originalPower);
}

TEST_CASE("hireling bonuses are rebuilt after a disk save and never applied twice")
{
    Party party = makeOneMemberParty();
    party.addHiredNpcFollower({1001, 37, 1000});
    party.addHiredNpcFollower({1002, 38, 200});
    party.addHiredNpcFollower({1003, 46, 600});
    GameSaveData save;
    save.mapFileName = "out02.odm";
    save.party = party.snapshot();
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "openyamm_hireling_bonuses.oysav";
    std::string error;
    REQUIRE(saveGameDataToPath(path, save, error));
    const std::optional<GameSaveData> loaded = loadGameDataFromPath(path, error);
    std::filesystem::remove(path);
    REQUIRE(loaded.has_value());
    Party restored;
    restored.restoreSnapshot(loaded->party);
    CHECK_EQ(restored.member(0)->magicalBonuses.resistances.fire, 20);
    CHECK_EQ(restored.member(0)->skillBonus("Sword"), 2);
    CHECK(restored.hasPartyBuff(PartyBuffId::WizardEye));
    restored.refreshDerivedState();
    CHECK_EQ(restored.member(0)->magicalBonuses.resistances.fire, 20);
    restored.removeHiredNpcFollower(1001);
    CHECK_EQ(restored.member(0)->magicalBonuses.resistances.fire, 0);
}
