#include "doctest/doctest.h"
#include "game/party/Party.h"
#include "game/rules/GameRules.h"
#include "game/rules/maw/MawBalanceModel.h"
#include "game/rules/maw/MawCharacterSheet.h"
#include "game/rules/maw/MawCombatFormulas.h"
#include "game/rules/maw/MawCombatRules.h"
#include "game/rules/maw/MawCraftingData.h"
#include "game/rules/maw/MawItemData.h"
#include "game/rules/maw/MawRules.h"
#include "game/tables/MapStats.h"
#include "game/tables/SpellTable.h"
#include "tests/RegressionGameData.h"

#include <cmath>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>

using namespace OpenYAMM::Game;

// The worked examples of devdocs/maw/COMBAT_SPEC.md §11 and CRAFTING.md §6.1 through the rules' real code: the
// character sheet, the spell, enchantment and aura paths and the kill drops (MawCombatFormulaTests.cpp checks the
// formulas alone).
namespace
{
// COMBAT_SPEC.md §11.1's gear on real items: a two-handed sword of 3 dice alone in its family (rung 3.5, item 6), a
// longbow of 5 dice (rung 3.5, item 845) and chain mail of AC 30 against a reference of 30 (item 91).
MawItemData specGear()
{
    MawItemData data;
    std::string error;
    REQUIRE_MESSAGE(data.loadFromYaml(
        "bases:\n  6: [3.5, 3, 1, 0, 0]\n  845: [3.5, 5, 0, 0, 0]\n  91: [3.5, 0, 0, 30, 30]\n", error), error);
    return data;
}

void bankLevel(MawRules &rules, double level)
{
    MawGameState state;
    state.continentLevels[0] = level;
    rules.setState(state);
}

// The Champion at level 50 (stats 89, weapon skills 17, the rest 11) or 150 (279, 40, 26), its gear at item power L / 5.
Character champion(int level)
{
    const bool high = level == 150;
    const uint32_t stat = high ? 279 : 89;
    const uint32_t weapon = high ? 40 : 17;
    const uint32_t other = high ? 26 : 11;
    Character character;
    character.name = "Champion";
    character.className = "Champion";
    character.level = uint32_t(level);
    character.might = character.intellect = character.personality = character.endurance = stat;
    character.speed = character.accuracy = character.luck = stat;
    character.skills["Sword"] = {"Sword", weapon, SkillMastery::Grandmaster};
    character.skills["Bow"] = {"Bow", weapon, SkillMastery::Grandmaster};
    character.skills["Armsmaster"] = {"Armsmaster", other, SkillMastery::Grandmaster};
    character.skills["ChainArmor"] = {"ChainArmor", other, SkillMastery::Grandmaster};
    character.skills["Bodybuilding"] = {"Bodybuilding", other, SkillMastery::Master};
    character.equipment.mainHand = 6;
    character.equipment.bow = 845;
    character.equipment.armor = 91;
    const uint16_t power = uint16_t(level / 5);
    character.equipmentRuntime.mainHand.rulesetFields.itemPower = power;
    character.equipmentRuntime.bow.rulesetFields.itemPower = power;
    character.equipmentRuntime.armor.rulesetFields.itemPower = power;
    return character;
}
}

TEST_CASE("MAW spec: the Champion's sheet rows and HP at levels 50 and 150 (COMBAT_SPEC §11.1)")
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());
    const ItemTable &items = OpenYAMM::Tests::regressionGameData().itemTable;
    struct Expected
    {
        int level;
        int meleeMinimum, meleeMaximum, meleeAttack;
        int bowMinimum, bowMaximum, bowAttack;
        int armorClass, resistance, health;
    };

    for (const Expected &expected : {Expected{50, 71, 120, 114, 36, 63, 111, 63, 34, 1059},
             Expected{150, 251, 424, 279, 166, 288, 274, 136, 110, 4087}})
    {
        CAPTURE(expected.level);
        MawRules rules(RulesetOptions{}, MawMapLevels{}, specGear());
        bankLevel(rules, expected.level);
        const Character character = champion(expected.level);
        const int stat = int(character.might);
        const CharacterCombatRows rows = mawCombatRows(rules, character, items, {stat, stat, stat});
        CHECK_EQ(rows.meleeMinimumDamage, expected.meleeMinimum);
        CHECK_EQ(rows.meleeMaximumDamage, expected.meleeMaximum);
        CHECK_EQ(rows.meleeAttack, expected.meleeAttack);
        CHECK_EQ(rows.rangedMinimumDamage, expected.bowMinimum);
        CHECK_EQ(rows.rangedMaximumDamage, expected.bowMaximum);
        CHECK_EQ(rows.rangedAttack, expected.bowAttack);
        CHECK_EQ(rows.resistances.fire, expected.resistance);
        CHECK_EQ(rows.resistances.body, expected.resistance);

        // The spec's sword has no attack bonus of its own, which MAW's Sword skill would turn into armour.
        Character withoutSword = character;
        withoutSword.equipment.mainHand = 0;
        CHECK_EQ(mawCombatRows(rules, withoutSword, items, {stat, stat, stat}).armorClass, expected.armorClass);

        // HP through the party: the class's base, then Endurance and Bodybuilding.
        PartySeed seed;
        seed.members = {character};
        Party party;
        party.seed(seed);
        party.setItemTable(&items);
        party.setClassMultiplierTable(&OpenYAMM::Tests::regressionGameData().classMultiplierTable);
        party.setRules(&rules.gameRules());
        bindGameRules(&rules.gameRules());
        party.refreshMemberResources(0);
        party.refreshDerivedState();
        CHECK_EQ(Party::effectiveMaximumHealth(*party.member(0)), expected.health);
        bindGameRules(nullptr);
    }
}

TEST_CASE("MAW spec: Mass Distortion takes its share of the target's HP, less from Hell up (COMBAT_SPEC §11.2)")
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());
    const SpellEntry *pSpell = OpenYAMM::Tests::regressionGameData().spellTable.findById(44);
    REQUIRE(pSpell != nullptr);
    struct Expected
    {
        RulesetDifficulty difficulty;
        int level;
        uint32_t earth;
        int health;
        int damage;
    };

    for (const Expected &expected : {Expected{RulesetDifficulty::Maw, 50, 17, 552, 130},
             Expected{RulesetDifficulty::Maw, 150, 40, 3859, 1351},
             Expected{RulesetDifficulty::Hell, 50, 17, 861, 151},
             Expected{RulesetDifficulty::Hell, 150, 40, 6162, 1608}})
    {
        RulesetOptions options;
        options.difficulty = expected.difficulty;
        MawRules rules(options, MawMapLevels{});
        Character caster;
        CharacterSpellCast cast;
        cast.pCaster = &caster;
        cast.pSpell = pSpell;
        cast.mastery = SkillMastery::Grandmaster;
        cast.skillLevel = expected.earth;
        ActorRulesetFacts facts;
        facts.level = expected.level;
        SpellTargetState target;
        target.currentHp = expected.health;
        target.maxHp = expected.health;
        target.pFacts = &facts;
        CHECK_EQ(rules.gameRules().combat.spellDamageOnTarget(cast, target).value_or(-1), expected.damage);
    }
}

TEST_CASE("MAW spec: a sword's fire enchantment and Fire Aura by the weapon's level damage (COMBAT_SPEC §11.2)")
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());
    const ItemTable &items = OpenYAMM::Tests::regressionGameData().itemTable;
    const MawDamageEnchant *pFire = mawDamageEnchant(12);
    REQUIRE(pFire != nullptr);
    struct Expected
    {
        int level;
        double levelDamage, enchantMinimum, enchantMaximum;
        int aura;
    };

    // MAW 8fbb48d1's getWeaponLevelDamage (the stat share fell to 0.2): 76.644615 and 282.3103 from MAW's own Lua.
    for (const Expected &expected : {Expected{50, 76.644615, 8.75938, 52.5563, 48},
             Expected{150, 282.3103, 32.264, 193.584, 71}})
    {
        CAPTURE(expected.level);
        MawRules rules(RulesetOptions{}, MawMapLevels{}, specGear());
        bankLevel(rules, expected.level);
        const double levelDamage = rules.model(1).weaponLevelDamage(expected.level, true, 0);
        CHECK(levelDamage == doctest::Approx(expected.levelDamage).epsilon(1e-5));
        const MawEnchantRange range =
            mawEnchantDamageRange(levelDamage, pFire->minimum, pFire->maximum, pFire->coefficient, true);
        CHECK(range.minimum == doctest::Approx(expected.enchantMinimum).epsilon(1e-4));
        CHECK(range.maximum == doctest::Approx(expected.enchantMaximum).epsilon(1e-4));

        // Fire Aura held at Grandmaster: max(0.25 x the level damage, 48) on the sword the Champion wields.
        const double skill = expected.level == 150 ? 40 : 17;
        rules.setActiveAuras({{4, MawAuraSource{skill, int(SkillMastery::Grandmaster), double(expected.level), 0}}});
        InventoryItem sword;
        sword.objectDescriptionId = 6;
        sword.rulesetFields.itemPower = uint16_t(expected.level / 5);
        CHECK_EQ(mawFireAuraOnWeapon(rules, champion(expected.level), *items.get(6), sword), expected.aura);
    }
}

TEST_CASE("MAW spec: a dragon's fang and breath rows and its delays (COMBAT_SPEC §11.2)")
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());
    const ItemTable &items = OpenYAMM::Tests::regressionGameData().itemTable;
    struct Expected
    {
        int level;
        uint32_t stat, skill;
        int fangMinimum, fangMaximum, breathMinimum, breathMaximum, delay;
    };

    for (const Expected &expected : {Expected{50, 89, 17, 378, 619, 266, 443, 117},
             Expected{150, 279, 40, 2606, 4306, 1754, 2924, 126}})
    {
        CAPTURE(expected.level);
        MawRules rules(RulesetOptions{}, MawMapLevels{});
        bankLevel(rules, expected.level);
        Character dragon;
        dragon.className = "Dragon";
        dragon.raceId = 5;
        dragon.level = uint32_t(expected.level);
        dragon.might = dragon.intellect = dragon.personality = dragon.endurance = expected.stat;
        dragon.speed = dragon.accuracy = dragon.luck = expected.stat;
        dragon.skills["Unarmed"] = {"Unarmed", expected.skill, SkillMastery::Grandmaster};
        dragon.skills["DragonAbility"] = {"DragonAbility", expected.skill, SkillMastery::Grandmaster};
        const int stat = int(expected.stat);
        const CharacterCombatRows rows = mawCombatRows(rules, dragon, items, {stat, stat, stat});
        // Fangs: the rows plus Might's effect, as the engine adds to every melee range.
        CHECK_EQ(rows.meleeMinimumDamage, expected.fangMinimum);
        CHECK_EQ(rows.meleeMaximumDamage, expected.fangMaximum);
        CHECK_EQ(rows.rangedMinimumDamage, expected.breathMinimum);
        CHECK_EQ(rows.rangedMaximumDamage, expected.breathMaximum);
        // The spec's 116.715 and 126.4 before the engine's whole ticks; bite and breath share it.
        CHECK_EQ(mawCharacterAttackDelay(rules, dragon, items, CharacterAttackMode::Melee, stat).delay, expected.delay);
        CHECK_EQ(mawCharacterAttackDelay(rules, dragon, items, CharacterAttackMode::DragonBreath, stat).delay,
            expected.delay);
    }
}

TEST_CASE("MAW spec: crafting drops per 1000 kills of level-50 monsters (CRAFTING.md §6.1)")
{
    std::ifstream input(std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/rulesets/maw/data/crafting.yml");
    std::ostringstream text;
    text << input.rdbuf();
    MawCraftingData crafting;
    std::string error;
    REQUIRE_MESSAGE(crafting.loadFromYaml(text.str(), error), error);
    MawRules rules(RulesetOptions{}, MawMapLevels{}, MawItemData{}, MawPromotionData{}, std::move(crafting));
    std::vector<std::string> row(38);
    row[0] = "194";
    row[1] = row[2] = "Human Mercenary B";
    row[3] = "50";
    row[4] = "100";
    row[10] = "Short";
    row[11] = "Normal";
    row[17] = "Phys";
    row[18] = "1d6";
    MonsterTable monsters;
    REQUIRE(monsters.loadStatsFromRows({row}));
    MapStatsEntry map = {};
    map.fileName = "out01.odm";
    ActorRulesetFacts facts;
    facts.level = 50;
    facts.tier = 2;
    CorpseLootContext context;
    context.pStats = monsters.findStatsById(194);
    context.pMonsterTable = &monsters;
    context.pFacts = &facts;
    context.pMap = &map;

    // The bad-luck counters carry from kill to kill, so this is the renewal rate the spec tabulates.
    constexpr uint32_t Kills = 400000;
    std::unordered_map<uint32_t, int> drops;

    for (uint32_t kill = 0; kill < Kills; ++kill)
    {
        context.actorIndex = kill;

        for (const CorpseLoot::ExtraItem &item : rules.gameRules().monsters.lootWithoutCorpse(context).items)
        {
            drops[item.itemId >= 1041 && item.itemId <= 1060 ? 1041 : item.itemId] += 1;
        }
    }

    const auto perThousand = [&drops](uint32_t itemId) { return drops[itemId] * 1000.0 / Kills; };
    CHECK(perThousand(1041) == doctest::Approx(13.4).epsilon(0.05));
    CHECK(perThousand(1063) == doctest::Approx(2.11).epsilon(0.1));
    CHECK(perThousand(1070) == doctest::Approx(2.11).epsilon(0.1));
    CHECK(perThousand(1061) == doctest::Approx(0.42).epsilon(0.2));
    CHECK(perThousand(1065) == doctest::Approx(0.53).epsilon(0.2));
}
