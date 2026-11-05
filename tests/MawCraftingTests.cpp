#include "doctest/doctest.h"
#include "game/items/AlchemyBenchRuntime.h"
#include "game/items/CraftingRuntime.h"
#include "game/items/InventoryBags.h"
#include "game/items/ItemGenerator.h"
#include "game/party/Party.h"
#include "game/rules/GameRules.h"
#include "game/rules/maw/MawCraftingRules.h"
#include "game/rules/maw/MawItemRules.h"
#include "game/rules/maw/MawRules.h"
#include "game/tables/HouseTable.h"
#include "game/tables/ItemTable.h"
#include "game/tables/MergedBaseTables.h"
#include "tests/RegressionGameData.h"

#include <array>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <memory>
#include <sstream>
#include <string>

using namespace OpenYAMM::Game;

// MAW's crafting (devdocs/maw/CRAFTING.md §3, rulesets/maw/data/crafting.yml) and the Workbench's batches.
namespace
{
std::string readSource(const std::string &relativePath)
{
    std::ifstream input(std::filesystem::path(OPENYAMM_SOURCE_DIR) / relativePath);
    std::ostringstream text;
    text << input.rdbuf();
    return text.str();
}

MawItemData installedItemData()
{
    MawItemData data;
    std::string error;
    REQUIRE_MESSAGE(data.loadFromYaml(readSource("assets_dev/engine/rulesets/maw/data/items.yml"), error), error);
    return data;
}

MawCraftingData installedCraftingData()
{
    MawCraftingData data;
    std::string error;
    REQUIRE_MESSAGE(data.loadFromYaml(readSource("assets_dev/engine/rulesets/maw/data/crafting.yml"), error), error);
    return data;
}

std::unique_ptr<MawRules> mawRules(RulesetOptions options = {})
{
    return std::make_unique<MawRules>(
        options, MawMapLevels{}, installedItemData(), MawPromotionData{}, installedCraftingData());
}

// The first MAW base item of a kind in the item table.
const ItemDefinition &baseItem(const MawRules &rules, const std::string &equipStat, bool twoHanded = false)
{
    for (const ItemDefinition &definition : OpenYAMM::Tests::regressionGameData().itemTable.entries())
    {
        const MawBaseItem *pBase = rules.itemData().baseItem(definition.itemId);

        if (pBase != nullptr && definition.equipStat == equipStat && pBase->twoHanded == twoHanded)
        {
            return definition;
        }
    }

    FAIL("no base item " << equipStat);
    static const ItemDefinition None;
    return None;
}

InventoryItem item(const ItemDefinition &definition, uint16_t enchant1, uint16_t power1, uint16_t enchant2 = 0,
    uint16_t power2 = 0)
{
    InventoryItem result;
    result.objectDescriptionId = definition.itemId;
    result.width = definition.inventoryWidth;
    result.height = definition.inventoryHeight;
    result.standardEnchantId = enchant1;
    result.standardEnchantPower = power1;
    result.rulesetFields.secondStandardEnchantId = enchant2;
    result.rulesetFields.secondStandardEnchantPower = power2;
    result.rulesetFields.lootRarity = uint8_t(enchant2 != 0 ? MawRarity::Rare : MawRarity::Uncommon);
    result.rulesetFields.dropLevel = 1;
    return result;
}

InventoryItem material(uint32_t itemId, uint16_t state = 0, uint16_t power = 0)
{
    const ItemDefinition *pDefinition = OpenYAMM::Tests::regressionGameData().itemTable.get(itemId);
    InventoryItem result;
    result.objectDescriptionId = itemId;
    result.width = pDefinition != nullptr ? pDefinition->inventoryWidth : 1;
    result.height = pDefinition != nullptr ? pDefinition->inventoryHeight : 1;
    result.rulesetFields.craftState = state;
    result.standardEnchantPower = power;
    return result;
}

CraftingContext context(int ownerLevel = 200)
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    CraftingContext result;
    result.pItemTable = &gameData.itemTable;
    result.pStandardEnchantTable = &gameData.standardItemEnchantTable;
    result.pSpecialEnchantTable = &gameData.specialItemEnchantTable;
    result.pPotionEffects = &gameData.mergedPotionSettingTable.effects();
    result.ownerLevel = ownerLevel;
    return result;
}
}

TEST_CASE("MAW gem caps match CRAFTING.md §3.3 for every tier and slot")
{
    const std::unique_ptr<MawRules> pRules = mawRules();
    const MawCraftingRules &crafting = static_cast<const MawCraftingRules &>(pRules->gameRules().crafting);
    CHECK_EQ(crafting.primordialMaxStrength(), 125);

    const std::array<std::array<int, 20>, 5> stat = {{
        {6, 13, 19, 25, 31, 38, 44, 50, 56, 63, 69, 75, 81, 88, 94, 100, 106, 113, 119, 125},
        {8, 17, 24, 32, 39, 48, 55, 63, 70, 79, 87, 94, 102, 110, 118, 125, 133, 142, 149, 157},
        {9, 20, 29, 38, 47, 57, 66, 75, 84, 95, 104, 113, 122, 132, 141, 150, 159, 170, 179, 188},
        {12, 26, 38, 50, 62, 76, 88, 100, 112, 126, 138, 150, 162, 176, 188, 200, 212, 226, 238, 250},
        {5, 10, 15, 19, 24, 29, 33, 38, 42, 48, 52, 57, 61, 66, 71, 75, 80, 85, 90, 94},
    }};
    const std::array<std::array<int, 20>, 5> skill = {{
        {3, 4, 5, 5, 6, 7, 7, 8, 8, 8, 9, 9, 9, 10, 10, 10, 11, 12, 12, 13},
        {4, 5, 7, 7, 8, 9, 9, 10, 10, 10, 12, 12, 12, 13, 13, 13, 14, 15, 15, 17},
        {5, 6, 8, 8, 9, 11, 11, 12, 12, 12, 14, 14, 14, 15, 15, 15, 17, 18, 18, 20},
        {6, 8, 10, 10, 12, 14, 14, 16, 16, 16, 18, 18, 18, 20, 20, 20, 22, 24, 24, 26},
        {3, 3, 4, 4, 5, 6, 6, 6, 6, 6, 7, 7, 7, 8, 8, 8, 9, 9, 9, 10},
    }};
    const std::array<double, 5> slots = {1, 1.25, 1.5, 2, 0.75};

    for (size_t slot = 0; slot < slots.size(); ++slot)
    {
        for (int tier = 1; tier <= 20; ++tier)
        {
            CAPTURE(slot);
            CAPTURE(tier);
            CHECK_EQ(crafting.gemCap(tier, slots[slot], false), stat[slot][size_t(tier - 1)]);
            CHECK_EQ(crafting.gemCap(tier, slots[slot], true), skill[slot][size_t(tier - 1)]);
        }
    }

    // Nightmare 131, Doom 138 (exact arithmetic, not MAW's 139), Road to Insanity 150.
    RulesetOptions nightmare;
    nightmare.difficulty = RulesetDifficulty::Nightmare;
    RulesetOptions doom;
    doom.challengeMode = RulesetChallengeMode::Doom;
    RulesetOptions insanity;
    insanity.challengeMode = RulesetChallengeMode::RoadToInsanity;
    CHECK_EQ(static_cast<const MawCraftingRules &>(mawRules(nightmare)->gameRules().crafting).primordialMaxStrength(),
        131);
    const std::unique_ptr<MawRules> pDoom = mawRules(doom);
    const MawCraftingRules &doomCrafting = static_cast<const MawCraftingRules &>(pDoom->gameRules().crafting);
    CHECK_EQ(doomCrafting.primordialMaxStrength(), 138);
    CHECK_EQ(doomCrafting.gemCap(20, 2, false), 276);
    CHECK_EQ(static_cast<const MawCraftingRules &>(mawRules(insanity)->gameRules().crafting).primordialMaxStrength(),
        150);
}

TEST_CASE("a MAW gem raises the base enchantment furthest below its own cap")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const std::unique_ptr<MawRules> pRules = mawRules();
    const CraftingRules &crafting = pRules->gameRules().crafting;
    const ItemDefinition &sword = baseItem(*pRules, "Weapon");

    // Tier 8 on a one-handed weapon: caps 50 and skill 8. Might 40/50 is further below its cap than a skill 7/8.
    InventoryItem target = item(sword, 17, 7, 1, 40);
    CraftResult result = crafting.craft(target, material(1048), context());
    REQUIRE(result.possible);
    CHECK(result.materialConsumed);
    CHECK_EQ(result.target.rulesetFields.secondStandardEnchantPower, 43);
    CHECK_EQ(result.target.standardEnchantPower, 7);
    CHECK_EQ(result.target.rulesetFields.craftCount, 1);
    CHECK_NE(result.target.rulesetFields.craftSeed, 0u);

    // At both caps the gem is refused; a stat enchantment alone stops at the cap.
    target = item(sword, 1, 50, 2, 50);
    result = crafting.craft(target, material(1048), context());
    CHECK_FALSE(result.possible);
    target = item(sword, 1, 49);
    result = crafting.craft(target, material(1048), context());
    REQUIRE(result.possible);
    CHECK_EQ(result.target.standardEnchantPower, 50);

    // No enchantments, too low a level, unidentified.
    CHECK_FALSE(crafting.craft(item(sword, 0, 0), material(1048), context()).possible);
    InventoryItem unidentified = item(sword, 1, 10);
    unidentified.identified = false;
    CHECK_EQ(crafting.craft(unidentified, material(1048), context()).reason, "Identify the item first");
    InventoryItem demanding = item(sword, 1, 10);
    demanding.rulesetFields.dropLevel = 400;
    CHECK_FALSE(crafting.craft(demanding, material(1048), context(10)).possible);
}

TEST_CASE("MAW Enchant Item takes a whole fifth of the potion's power before the slot multiplier (audit ALC-14)")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const std::unique_ptr<MawRules> pRules = mawRules();
    const CraftingRules &crafting = pRules->gameRules().crafting;
    const ItemDefinition &armor = baseItem(*pRules, "Armor");
    const double multiplier = mawEnchantSlotMultiplier(armor, *pRules->itemData().baseItem(armor.itemId));
    // Power 33: floor(33 / 5) = 6 before the multiplier, not 6.6.
    const int expected = int(std::ceil(6 * multiplier - 1e-9));
    bool checked = false;

    for (uint32_t seed = 1; seed <= 40 && !checked; ++seed)
    {
        InventoryItem plain = item(armor, 0, 0);
        plain.rulesetFields.craftSeed = seed;
        const CraftResult result = crafting.craft(plain, material(238, 0, 33), context());
        REQUIRE(result.possible);

        if (result.target.standardEnchantId <= 16)
        {
            CHECK_EQ(int(result.target.standardEnchantPower), expected);
            checked = true;
        }
    }

    CHECK(checked);
}

TEST_CASE("MAW crafting is seeded: the preview is the result, and the next craft differs")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const std::unique_ptr<MawRules> pRules = mawRules();
    const CraftingRules &crafting = pRules->gameRules().crafting;
    const ItemDefinition &ring = baseItem(*pRules, "Ring");
    const InventoryItem target = item(ring, 3, 40);

    // Creator's Hourglass: a second enchantment of another kind, 40 to 50 strong (ring cap 75).
    const CraftResult first = crafting.craft(target, material(1062), context());
    const CraftResult again = crafting.craft(target, material(1062), context());
    REQUIRE(first.possible);
    CHECK(first.target == again.target);
    CHECK_NE(first.target.rulesetFields.secondStandardEnchantId, 3);
    CHECK_GE(first.target.rulesetFields.secondStandardEnchantPower, 40);
    CHECK_LE(first.target.rulesetFields.secondStandardEnchantPower, 50);
    CHECK(MawRarity(first.target.rulesetFields.lootRarity) == MawRarity::Rare);

}

TEST_CASE("MAW Pearl of Memory removes the enchantment the player picks")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const std::unique_ptr<MawRules> pRules = mawRules();
    const CraftingRules &crafting = pRules->gameRules().crafting;
    // A ring with Might +40, a second enchantment (Intellect +30) and a special.
    InventoryItem ring = item(baseItem(*pRules, "Ring"), 1, 40, 2, 30);
    ring.specialEnchantId = 1;
    const auto pick = [&](size_t choice)
    {
        CraftingContext picked = context();
        picked.choice = choice;
        return crafting.craft(ring, material(1066), picked);
    };

    // Three options, the first by default, each named in the preview and the confirmation; nothing is hidden.
    const CraftResult first = crafting.craft(ring, material(1066), context());
    REQUIRE(first.possible);
    REQUIRE_EQ(first.choices.size(), 3);
    CHECK_FALSE(first.choicePrompt.empty());
    CHECK_EQ(first.choice, 0);
    CHECK_FALSE(first.hiddenOutcome);
    CHECK_EQ(first.summary, "Removes " + first.choices[0]);
    CHECK_EQ(first.confirmation, "Remove " + first.choices[0] + "?");

    // Losing the first moves the second up.
    CHECK_EQ(first.target.standardEnchantId, 2);
    CHECK_EQ(int(first.target.standardEnchantPower), 30);
    CHECK_EQ(first.target.rulesetFields.secondStandardEnchantId, 0);
    CHECK_EQ(first.target.specialEnchantId, 1);

    const CraftResult second = pick(1);
    CHECK_EQ(second.choice, 1);
    CHECK_EQ(second.target.standardEnchantId, 1);
    CHECK_EQ(second.target.rulesetFields.secondStandardEnchantId, 0);
    CHECK_EQ(second.target.specialEnchantId, 1);

    const CraftResult special = pick(2);
    CHECK_EQ(special.target.standardEnchantId, 1);
    CHECK_EQ(special.target.rulesetFields.secondStandardEnchantId, 2);
    CHECK_EQ(special.target.specialEnchantId, 0);
    CHECK_EQ(special.summary, "Removes " + first.choices[2]);

    // A pick past the last is the last, and the same pick is the same result.
    CHECK(pick(7).target == special.target);
    CHECK(pick(1).target == second.target);

    // Two left, two options; with one there is nothing to pick, and with none the Pearl refuses.
    CHECK_EQ(crafting.craft(second.target, material(1066), context()).choices.size(), 2);
    const InventoryItem single = item(baseItem(*pRules, "Ring"), 1, 40);
    const CraftResult last = crafting.craft(single, material(1066), context());
    REQUIRE(last.possible);
    CHECK(last.choices.empty());
    CHECK_EQ(last.target.standardEnchantId, 0);
    CHECK_FALSE(crafting.craft(last.target, material(1066), context()).possible);
}

TEST_CASE("MAW crafting materials: cubes, mirror, orbs and the Endless Potion")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const std::unique_ptr<MawRules> pRules = mawRules();
    const CraftingRules &crafting = pRules->gameRules().crafting;
    const ItemDefinition &armour = baseItem(*pRules, "Armor");
    const ItemDefinition &ring = baseItem(*pRules, "Ring");

    // Pandora's Cube: +10 % quality on a Rare item, refused on rings, stops at 20 %.
    InventoryItem plate = item(armour, 1, 10, 2, 10);
    CraftResult cube = crafting.craft(plate, material(1063), context());
    REQUIRE(cube.possible);
    CHECK_EQ(cube.target.rulesetFields.qualityPercent, 10);
    cube = crafting.craft(cube.target, material(1063), context());
    CHECK_EQ(cube.target.rulesetFields.qualityPercent, 20);
    CHECK_FALSE(crafting.craft(cube.target, material(1063), context()).possible);
    CHECK_EQ(crafting.craft(item(ring, 1, 5), material(1063), context()).reason,
        "Only weapons and armour can be refined");

    // Crafting Cube: +2 power on body armour, capped at a fifth of the owner's level.
    InventoryItem powered = crafting.craft(plate, material(1070), context(21)).target;
    CHECK_EQ(powered.rulesetFields.itemPower, 2);
    powered.rulesetFields.itemPower = 4;
    CHECK_FALSE(crafting.craft(powered, material(1070), context(21)).possible);

    // Archibald's Mirror: becomes an identified copy with its own craft stream; the original is unchanged.
    const CraftResult mirror = crafting.craft(plate, material(1064), context());
    REQUIRE(mirror.possible);
    REQUIRE(mirror.materialAfter.has_value());
    CHECK_FALSE(mirror.materialConsumed);
    CHECK_EQ(mirror.materialAfter->objectDescriptionId, plate.objectDescriptionId);
    CHECK_EQ(mirror.materialAfter->rulesetFields.secondStandardEnchantPower, 10);
    CHECK(mirror.materialAfter->identified);

    // Orb of Creation: an empty orb draws the affix out (and becomes charged), a charged one gives it.
    InventoryItem legendary = plate;
    legendary.rulesetFields.legendaryAffixId = 19;
    legendary.rulesetFields.lootRarity = uint8_t(MawRarity::Legendary);
    const CraftResult draw = crafting.craft(legendary, material(1067), context());
    REQUIRE(draw.possible);
    CHECK_EQ(draw.target.rulesetFields.legendaryAffixId, 0);
    CHECK(MawRarity(draw.target.rulesetFields.lootRarity) == MawRarity::Rare);
    REQUIRE(draw.materialAfter.has_value());
    CHECK_EQ(draw.materialAfter->rulesetFields.craftState, 19);
    const CraftResult give = crafting.craft(plate, *draw.materialAfter, context());
    REQUIRE(give.possible);
    CHECK(give.materialConsumed);
    CHECK_EQ(give.target.rulesetFields.legendaryAffixId, 19);
    CHECK(MawRarity(give.target.rulesetFields.lootRarity) == MawRarity::Legendary);

    // Celestial Orb: a charged orb makes an item Celestial; an empty one takes it back.
    const CraftResult celestial = crafting.craft(plate, material(1068, 1), context());
    REQUIRE(celestial.possible);
    CHECK(MawRarity(celestial.target.rulesetFields.lootRarity) == MawRarity::Celestial);
    CHECK_FALSE(crafting.craft(celestial.target, material(1048), context()).possible);
    const CraftResult back = crafting.craft(celestial.target, material(1068), context());
    REQUIRE(back.possible);
    // Without the status the item is what it was: a Rare plate here, as MAW reads rarity back (audit ALC-8).
    CHECK(MawRarity(back.target.rulesetFields.lootRarity) == MawRarity::Rare);
    CHECK_EQ(back.materialAfter->rulesetFields.craftState, 1);

    // A Primordial item keeps its tier through an affix given and taken away.
    InventoryItem primordial = plate;
    primordial.rulesetFields.lootRarity = uint8_t(MawRarity::Primordial);
    primordial.rulesetFields.ancientTier = 2;
    const CraftResult affixed = crafting.craft(primordial, *draw.materialAfter, context());
    REQUIRE(affixed.possible);
    CHECK(MawRarity(affixed.target.rulesetFields.lootRarity) == MawRarity::Legendary);
    const CraftResult stripped = crafting.craft(affixed.target, material(1067), context());
    REQUIRE(stripped.possible);
    CHECK(MawRarity(stripped.target.rulesetFields.lootRarity) == MawRarity::Primordial);
}

TEST_CASE("the Workbench batches gems from the cheapest tier and combines three into one")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    const std::unique_ptr<MawRules> pRules = mawRules();
    const CraftingRules &crafting = pRules->gameRules().crafting;
    const ItemDefinition &sword = baseItem(*pRules, "Weapon");

    Character member;
    member.name = "Smith";
    member.level = 100;
    PartySeed seed;
    seed.members = {member};
    Party party;
    party.setItemTable(&gameData.itemTable);
    party.seed(seed);
    party.setRules(&pRules->gameRules());
    REQUIRE(party.tryAutoPlaceItemInMemberInventory(0, item(sword, 1, 0)));

    for (int index = 0; index < 4; ++index)
    {
        REQUIRE(party.tryAutoPlaceItemInMemberInventory(0, material(1041)));
    }

    for (int index = 0; index < 10; ++index)
    {
        REQUIRE(party.tryAutoPlaceItemInMemberInventory(0, material(1048)));
    }

    CraftingTables tables;
    tables.pItemTable = &gameData.itemTable;
    tables.pStandardEnchantTable = &gameData.standardItemEnchantTable;
    tables.pSpecialEnchantTable = &gameData.specialItemEnchantTable;
    tables.pPotionEffects = &gameData.mergedPotionSettingTable.effects();
    const std::vector<CraftTargetEntry> targets = CraftingRuntime::collectTargets(party, tables);
    REQUIRE_EQ(targets.size(), 1u);
    const std::vector<CraftMaterialEntry> materials = CraftingRuntime::collectMaterials(party, crafting);
    REQUIRE_EQ(materials.size(), 2u);
    CHECK_EQ(materials[0].key.itemId, 1041u);
    CHECK_EQ(materials[0].refs.size(), 4u);

    // Cheapest first: two tier-1 gems take Might 0 -> 6 (cap 6), then tier 8 gems 6 -> 50 in 15 steps (10 left: 36).
    const CraftPlan plan =
        CraftingRuntime::plan(party, targets[0].ref, materials[1].key, 100, true, 0, crafting, tables);
    CHECK_EQ(plan.applications, 12u);
    CHECK_EQ(plan.item.standardEnchantPower, 36);
    REQUIRE_EQ(plan.gemsUsed.size(), 2u);
    CHECK_EQ(plan.gemsUsed[0].second, 2u);
    CHECK_EQ(plan.gemsUsed[1].second, 10u);

    CraftPlan applied;
    std::optional<InventoryItem> overflow;
    REQUIRE(CraftingRuntime::apply(party, targets[0].ref, materials[1].key, 100, true, 0, crafting, tables, applied,
        overflow));
    CHECK_EQ(CraftingRuntime::itemAt(party, targets[0].ref)->standardEnchantPower, 36);
    CHECK_EQ(CraftingRuntime::collectMaterials(party, crafting).size(), 1u);

    // Two tier-1 gems are left: no merge. Four more make two merges.
    CHECK(CraftingRuntime::planCombine(party, 1041, false, crafting).steps.empty());

    for (int index = 0; index < 4; ++index)
    {
        REQUIRE(party.tryAutoPlaceItemInMemberInventory(0, material(1041)));
    }

    const GemCombinePlan combine = CraftingRuntime::planCombine(party, 1041, true, crafting);
    REQUIRE_EQ(combine.steps.size(), 1u);
    CHECK_EQ(combine.steps[0].merges, 2u);
    REQUIRE(CraftingRuntime::combine(party, combine, crafting, gameData.itemTable));
    const std::vector<CraftMaterialEntry> after = CraftingRuntime::collectMaterials(party, crafting);
    REQUIRE_EQ(after.size(), 1u);
    CHECK_EQ(after[0].key.itemId, 1042u);
    CHECK_EQ(after[0].refs.size(), 2u);
}

TEST_CASE("the Workbench sees every bag: a target and gems in closed bags craft there (players, 2026-10-27)")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    const std::unique_ptr<MawRules> pRules = mawRules();
    const CraftingRules &crafting = pRules->gameRules().crafting;
    const ItemDefinition &sword = baseItem(*pRules, "Weapon");

    Character member;
    member.name = "Smith";
    member.level = 100;
    PartySeed seed;
    seed.members = {member, member};
    Party party;
    party.setItemTable(&gameData.itemTable);
    party.seed(seed);
    party.setRules(&pRules->gameRules());
    Character &smith = *party.member(0);
    Character &helper = *party.member(1);
    REQUIRE(InventoryBags::openBag(smith, 3, 4));
    REQUIRE(smith.addInventoryItem(item(sword, 1, 0)));
    REQUIRE(smith.addInventoryItem(material(1041)));
    REQUIRE(InventoryBags::openBag(smith, 0, 4));
    REQUIRE(InventoryBags::openBag(helper, 2, 4));
    REQUIRE(helper.addInventoryItem(material(1041)));
    REQUIRE(helper.addInventoryItem(material(1041)));
    REQUIRE(InventoryBags::openBag(helper, 0, 4));
    REQUIRE(smith.inventory.empty());
    REQUIRE(helper.inventory.empty());

    CraftingTables tables;
    tables.pItemTable = &gameData.itemTable;
    tables.pStandardEnchantTable = &gameData.standardItemEnchantTable;
    tables.pSpecialEnchantTable = &gameData.specialItemEnchantTable;
    tables.pPotionEffects = &gameData.mergedPotionSettingTable.effects();
    const std::vector<CraftTargetEntry> targets = CraftingRuntime::collectTargets(party, tables);
    REQUIRE_EQ(targets.size(), 1u);
    CHECK_EQ(targets[0].ref.bag, 3);
    const std::vector<CraftMaterialEntry> materials = CraftingRuntime::collectMaterials(party, crafting);
    REQUIRE_EQ(materials.size(), 1u);
    CHECK_EQ(materials[0].refs.size(), 3u);

    // Tier-1 gems take Might 0 -> 6 (cap 6) in two steps; the third has nothing left to raise.
    CraftPlan applied;
    std::optional<InventoryItem> overflow;
    REQUIRE(CraftingRuntime::apply(party, targets[0].ref, materials[0].key, 100, false, 0, crafting, tables, applied,
        overflow));
    CHECK_EQ(applied.applications, 2u);
    CHECK_EQ(CraftingRuntime::itemAt(party, targets[0].ref)->standardEnchantPower, 6);
    CHECK_EQ(CraftingRuntime::collectMaterials(party, crafting)[0].refs.size(), 1u);
    CHECK_EQ(smith.rulesetState.currentBag, 0);
    CHECK_EQ(helper.rulesetState.currentBag, 0);
    CHECK(smith.inventory.empty());
    CHECK(helper.inventory.empty());
    CHECK_EQ(InventoryBags::itemsInBag(smith, 3).size() + InventoryBags::itemsInBag(helper, 2).size(), 2u);

    // Gem merges count and take the gems of every bag too.
    REQUIRE(InventoryBags::openBag(helper, 1, 4));
    REQUIRE(helper.addInventoryItem(material(1041)));
    REQUIRE(helper.addInventoryItem(material(1041)));
    REQUIRE(InventoryBags::openBag(helper, 0, 4));
    const GemCombinePlan combine = CraftingRuntime::planCombine(party, 1041, false, crafting);
    REQUIRE_EQ(combine.steps.size(), 1u);
    CHECK_EQ(combine.steps[0].merges, 1u);
    REQUIRE(CraftingRuntime::combine(party, combine, crafting, gameData.itemTable));
    const std::vector<CraftMaterialEntry> after = CraftingRuntime::collectMaterials(party, crafting);
    REQUIRE_EQ(after.size(), 1u);
    CHECK_EQ(after[0].key.itemId, 1042u);
}

TEST_CASE("the Workbench's Alchemy tab mixes the ingredients of closed bags (players, 2026-10-27)")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    const std::unique_ptr<MawRules> pRules = mawRules();
    constexpr uint32_t BottleItemId = 220;
    constexpr uint32_t WidowsweepBerriesItemId = 200;

    Character member;
    member.name = "Alchemist";
    member.level = 10;
    member.skills["Alchemy"] = {"Alchemy", 4, SkillMastery::Expert};
    PartySeed seed;
    seed.members = {member};
    Party party;
    party.setItemTable(&gameData.itemTable);
    party.seed(seed);
    party.setRules(&pRules->gameRules());
    Character &alchemist = *party.member(0);
    REQUIRE(InventoryBags::openBag(alchemist, 3, 4));
    REQUIRE(alchemist.addInventoryItem(material(BottleItemId)));
    REQUIRE(InventoryBags::openBag(alchemist, 1, 4));
    REQUIRE(alchemist.addInventoryItem(material(WidowsweepBerriesItemId)));
    REQUIRE(InventoryBags::openBag(alchemist, 0, 4));
    REQUIRE(alchemist.inventory.empty());

    const AlchemyBenchTables tables{
        gameData.itemTable,
        gameData.potionMixingTable,
        gameData.potionNoteTable,
        gameData.mergedPotionSettingTable,
        gameData.mergedReagentSettingTable};
    const std::vector<AlchemyIngredient> ingredients = AlchemyBenchRuntime::collectIngredients(party, tables);
    REQUIRE_EQ(ingredients.size(), 2u);
    const AlchemyRecipe recipe{BottleItemId, WidowsweepBerriesItemId};
    CHECK_EQ(AlchemyBenchRuntime::brewableCount(recipe, ingredients), 1u);

    const AlchemyMixOutcome outcome = AlchemyBenchRuntime::mix(party, recipe, tables);
    REQUIRE(outcome.result.success);
    CHECK_EQ(alchemist.rulesetState.currentBag, 0);
    CHECK(alchemist.inventory.empty());
    CHECK(InventoryBags::itemsInBag(alchemist, 1).empty());
    REQUIRE_EQ(InventoryBags::itemsInBag(alchemist, 3).size(), 1u);
    CHECK_EQ(InventoryBags::itemsInBag(alchemist, 3)[0].objectDescriptionId, outcome.resultItem.objectDescriptionId);
    CHECK_NE(outcome.resultItem.objectDescriptionId, BottleItemId);
}

TEST_CASE("MAW magic shops and alchemists stock crafting materials in place of gems")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    const std::unique_ptr<MawRules> pRules = mawRules();
    Party party;
    party.setItemTable(&gameData.itemTable);
    std::mt19937 rng(7);
    const auto stock = [&](const char *pHouseType)
    {
        HouseEntry house;
        house.type = pHouseType;
        std::vector<InventoryItem> items(6);

        for (InventoryItem &item : items)
        {
            item = ItemGenerator::makeInventoryItem(177, gameData.itemTable, ItemGenerationMode::Shop);
        }

        pRules->itemRules().adjustShopStock(items, house, party, gameData.itemTable, rng);
        return items;
    };

    // A poor party gets gems (tier 1-3 with nothing banked); every valuable gem slot is replaced.
    for (const char *pType : {"Magic Shop", "Alchemist"})
    {
        for (const InventoryItem &item : stock(pType))
        {
            CHECK_GE(item.objectDescriptionId, 1041u);
            CHECK_LE(item.objectDescriptionId, 1043u);
        }
    }

    // A weapon shop keeps its stock; gems sell at MAW's prices.
    for (const InventoryItem &item : stock("Weapon Shop"))
    {
        CHECK_EQ(item.objectDescriptionId, 177u);
    }

    // The alchemist's guaranteed row of empty bottles is never swapped.
    HouseEntry alchemist;
    alchemist.type = "Alchemist";
    std::vector<InventoryItem> bottles(40, ItemGenerator::makeInventoryItem(220, gameData.itemTable,
        ItemGenerationMode::Shop));
    pRules->itemRules().adjustShopStock(bottles, alchemist, party, gameData.itemTable, rng);

    for (const InventoryItem &item : bottles)
    {
        CHECK_EQ(item.objectDescriptionId, 220u);
    }

    const ItemDefinition *pGem = gameData.itemTable.get(1043);
    REQUIRE(pGem != nullptr);
    CHECK_EQ(pRules->itemRules().shopBuyValue(InventoryItem{}, *pGem, nullptr, nullptr), 4000);
}

TEST_CASE("the Workbench outlook: item power, the gems' reach and what the Hourglass and the Eye would add (D.17)")
{
    const std::unique_ptr<MawRules> pRules = mawRules();
    const MawCraftingRules &crafting = static_cast<const MawCraftingRules &>(pRules->gameRules().crafting);
    const ItemDefinition &armor = baseItem(*pRules, "Armor");
    InventoryItem target = item(armor, 1, 10);
    target.rulesetFields.itemPower = 12;
    const CraftingContext craftingContext = context(200);

    const std::vector<std::string> lines = crafting.craftOutlook(target, craftingContext);
    REQUIRE_EQ(lines.size(), 4u);
    CHECK_EQ(lines[0], "Item Bonus Power: 12/40");
    CHECK_NE(lines[1].find(" +10, gems raise it to "), std::string::npos);
    CHECK_GT(std::stoi(lines[1].substr(lines[1].rfind(' ') + 1)), 100);

    // The same step the Hourglass (1062) and the Eye of Void (1061) would make on the Workbench.
    const CraftResult hourglass = crafting.craft(target, material(1062), craftingContext);
    const CraftResult eye = crafting.craft(target, material(1061), craftingContext);
    REQUIRE(hourglass.possible);
    REQUIRE(eye.possible);
    CHECK_NE(lines[2].find(hourglass.summary), std::string::npos);
    CHECK_NE(lines[3].find(eye.summary), std::string::npos);

    CHECK(standardCraftingRules().craftOutlook(target, craftingContext).empty());
}
