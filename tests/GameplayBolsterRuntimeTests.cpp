#include "doctest/doctest.h"

#include "game/gameplay/GameplayBolsterRuntime.h"
#include "game/party/Party.h"
#include "game/tables/MapStats.h"
#include "game/tables/MergedBaseTables.h"

using namespace OpenYAMM::Game;

namespace
{
std::vector<std::string> monsterStatsRow(
    int id,
    const std::string &name,
    int level,
    int hp,
    int armorClass,
    const std::string &movement,
    int speed)
{
    std::vector<std::string> row(38);
    row[0] = std::to_string(id);
    row[1] = name;
    row[2] = name;
    row[3] = std::to_string(level);
    row[4] = std::to_string(hp);
    row[5] = std::to_string(armorClass);
    row[10] = movement;
    row[11] = "Normal";
    row[12] = "0";
    row[13] = std::to_string(speed);
    row[14] = "100";
    row[17] = "Phys";
    row[18] = "1d6";
    return row;
}

MonsterTable makeMonsterTable()
{
    MonsterTable table;
    REQUIRE(table.loadStatsFromRows({
        monsterStatsRow(451, "Tree A", 10, 100, 5, "Stationary", 120),
        monsterStatsRow(452, "Tree B", 10, 120, 7, "Stationary", 120),
        monsterStatsRow(453, "Tree C", 10, 140, 9, "Stationary", 120),
    }));
    return table;
}

MonsterTable makeGeneratedAbilityMonsterTable()
{
    std::vector<std::string> first = monsterStatsRow(16, "Regnan Sorcerer", 10, 100, 5, "Short", 120);
    first[18] = "2d5";
    MonsterTable table;
    REQUIRE(table.loadStatsFromRows({
        first,
        monsterStatsRow(17, "Regnan Battlemage", 10, 120, 7, "Short", 120),
        monsterStatsRow(18, "Regnan Archmage", 10, 140, 9, "Short", 120),
    }));
    return table;
}

MonsterTable makeElementalMonsterTable()
{
    MonsterTable table;
    REQUIRE(table.loadStatsFromRows({
        monsterStatsRow(76, "Lesser Water Elemental", 10, 100, 5, "Short", 120),
        monsterStatsRow(77, "Water Elemental", 10, 100, 5, "Short", 120),
        monsterStatsRow(78, "Greater Water Elemental", 10, 100, 5, "Short", 120),
    }));
    return table;
}

MergedBolsterMapTable makeBolsterMapTable(bool summons)
{
    MergedBolsterMapTable table;
    REQUIRE(table.loadFromRows({
        {"#", "Note", "Continent", "Bolster kind", "Spells", "Summons", "Weather", "Extra", "Rarity"},
        {"65", "The Tularean Forest", "2", "LowerToEqual", "x", summons ? "x" : "-", "x", "0", "30"},
    }));
    return table;
}

MergedBolsterMonsterTable makeBolsterMonsterTable()
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
        {"451", "Tree", "Immobile", "", "Neutral", "", "Endurance", "", "-", "-", "x", "-", "-", "x", "226", "", "300"},
        {"452", "Tree", "Immobile", "", "Neutral", "", "Endurance", "", "-", "-", "x", "-", "-", "x", "226", "", "300"},
        {"453", "Tree", "Immobile", "", "Neutral", "", "Endurance", "", "-", "-", "x", "-", "-", "x", "226", "", "300"},
    }));
    return table;
}

MergedBolsterMonsterTable makeGeneratedAbilityMonsterSettingsTable()
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
        {"16", "Regnan Sorcerer", "Human", "", "Dark", "M", "Magic", "Fire", "-", "x", "x",
         "-", "-", "-", "", "", "300"},
        {"17", "Regnan Battlemage", "Human", "", "Dark", "M", "Magic", "Fire", "-", "x", "x",
         "-", "-", "-", "", "", "300"},
        {"18", "Regnan Archmage", "Human", "", "Dark", "M", "Magic", "Fire", "-", "x", "x",
         "-", "-", "-", "", "", "300"},
    }));
    return table;
}

MergedBolsterMonsterTable makeElementalMonsterSettingsTable()
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
        {"76", "Lesser Water Elemental", "Elemental", "", "Neutral", "", "Magic", "Water", "-", "x",
         "-", "x", "-", "-", "", "", ""},
        {"77", "Water Elemental", "Elemental", "", "Neutral", "", "Magic", "Water", "-", "x",
         "-", "x", "-", "-", "", "", ""},
        {"78", "Greater Water Elemental", "Elemental", "", "Neutral", "", "Magic", "Water", "-", "x",
         "-", "x", "-", "-", "", "", ""},
    }));
    return table;
}

Party makeParty(uint32_t level)
{
    Character first;
    first.level = level;
    Character second;
    second.level = level;

    PartySeed seed = {};
    seed.members = {first, second};

    Party party;
    party.seed(seed);
    return party;
}
}

TEST_CASE("runtime bolster applies merged map and monster settings to MM7 tree-style actors")
{
    MonsterTable monsterTable = makeMonsterTable();
    MergedBolsterMapTable mapTable = makeBolsterMapTable(true);
    MergedBolsterMonsterTable monsterSettingsTable = makeBolsterMonsterTable();
    Party party = makeParty(35);
    MapStatsEntry map = {};
    map.id = 65;
    MonsterEntry monsterEntry = {};
    monsterEntry.height = 256;

    const MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(451);
    REQUIRE(pStats != nullptr);

    const GameplayMonsterBolsterResult bolster =
        resolveGameplayMonsterBolster(
            GameplayBolsterRuntimeContext{
                .pMap = &map,
                .pMonsterTable = &monsterTable,
                .pBolsterMapTable = &mapTable,
                .pBolsterMonsterTable = &monsterSettingsTable,
                .pParty = &party,
                .bolsterMonstersEnabled = true,
            },
            *pStats,
            &monsterEntry);

    CHECK(bolster.mapEnabled);
    CHECK(bolster.statsEnabled);
    CHECK(bolster.maxHp > pStats->hitPoints);
    CHECK_EQ(bolster.maxHp, 189);
    CHECK_EQ(bolster.armorClass, 8);
    CHECK_GT(bolster.attack1DamageBonus, pStats->attack1Damage.bonus);
    CHECK_EQ(bolster.attack2DamageBonus, pStats->attack2Damage.bonus);
    CHECK(bolster.monsterAllowsNewSpells);
    CHECK(bolster.monsterAllowsSummons);
    CHECK(bolster.immobile);
    CHECK(bolster.stationarySummonAsSpawnPoint);
    CHECK(bolster.summonMonsterId == 226);
    CHECK_EQ(bolster.rewardMultiplier, doctest::Approx(1.89f));
}

TEST_CASE("runtime bolster is disabled by default")
{
    MonsterTable monsterTable = makeMonsterTable();
    MergedBolsterMapTable mapTable = makeBolsterMapTable(true);
    MergedBolsterMonsterTable monsterSettingsTable = makeBolsterMonsterTable();
    Party party = makeParty(35);
    MapStatsEntry map = {};
    map.id = 65;

    const MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(451);
    REQUIRE(pStats != nullptr);

    const GameplayMonsterBolsterResult bolster =
        resolveGameplayMonsterBolster(
            GameplayBolsterRuntimeContext{
                .pMap = &map,
                .pMonsterTable = &monsterTable,
                .pBolsterMapTable = &mapTable,
                .pBolsterMonsterTable = &monsterSettingsTable,
                .pParty = &party,
            },
            *pStats,
            nullptr);

    CHECK_FALSE(bolster.mapEnabled);
    CHECK_FALSE(bolster.statsEnabled);
    CHECK_EQ(bolster.maxHp, pStats->hitPoints);
    CHECK_EQ(bolster.armorClass, pStats->armorClass);
    CHECK_FALSE(bolster.monsterAllowsNewSpells);
    CHECK_FALSE(bolster.monsterAllowsSummons);
}

TEST_CASE("a monster of the Immobile kind stays put with bolster off")
{
    MonsterTable monsterTable;
    REQUIRE(monsterTable.loadStatsFromRows({
        monsterStatsRow(142, "Malevolent Boulder A", 12, 50, 35, "Long", 250),
        monsterStatsRow(143, "Malevolent Boulder B", 20, 100, 50, "Med", 260),
    }));
    MergedBolsterMonsterTable monsterSettingsTable;
    REQUIRE(monsterSettingsTable.loadFromRows({
        {"#", "Note", "Type", "ExtraType", "Creed", "Gender", "Style", "PrefMagic", "NoBounty", "Ranged", "Spells",
         "HPBySize", "Replicate", "Summons", "SummonId", "Extra", "MaxHP"},
        {"142", "Boulder", "Construct", "Immobile,NoArena", "Neutral", "", "Endurance", "Earth", "-", "-", "-", "-",
         "-", "-", "", "", "300"},
        {"143", "Boulder", "Construct", "NoArena", "Neutral", "", "Endurance", "Earth", "-", "-", "-", "-", "-", "-",
         "", "", "300"},
    }));
    REQUIRE(monsterTable.applyKindFlagsFromBolsterMonsterTable(monsterSettingsTable));
    MapStatsEntry map = {};
    map.id = 52;

    for (const int monsterId : {142, 143})
    {
        CAPTURE(monsterId);
        const MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(monsterId);
        REQUIRE(pStats != nullptr);
        const GameplayMonsterBolsterResult bolster = resolveGameplayMonsterBolster(
            GameplayBolsterRuntimeContext{.pMap = &map, .pMonsterTable = &monsterTable}, *pStats, nullptr);
        CHECK_EQ(bolster.immobile, monsterId == 142);
    }
}

TEST_CASE("runtime bolster keeps summon behavior gated by the map row")
{
    MonsterTable monsterTable = makeMonsterTable();
    MergedBolsterMapTable mapTable = makeBolsterMapTable(false);
    MergedBolsterMonsterTable monsterSettingsTable = makeBolsterMonsterTable();
    Party party = makeParty(35);
    MapStatsEntry map = {};
    map.id = 65;

    const MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(451);
    REQUIRE(pStats != nullptr);

    const GameplayMonsterBolsterResult bolster =
        resolveGameplayMonsterBolster(
            GameplayBolsterRuntimeContext{
                .pMap = &map,
                .pMonsterTable = &monsterTable,
                .pBolsterMapTable = &mapTable,
                .pBolsterMonsterTable = &monsterSettingsTable,
                .pParty = &party,
                .bolsterMonstersEnabled = true,
            },
            *pStats,
            nullptr);

    CHECK(bolster.monsterAllowsNewSpells);
    CHECK_FALSE(bolster.monsterAllowsSummons);
    CHECK_FALSE(bolster.stationarySummonAsSpawnPoint);
}

TEST_CASE("runtime bolster materializes generated ranged attacks and spells")
{
    MonsterTable monsterTable = makeGeneratedAbilityMonsterTable();
    MergedBolsterMapTable mapTable = makeBolsterMapTable(true);
    MergedBolsterMonsterTable monsterSettingsTable = makeGeneratedAbilityMonsterSettingsTable();
    Party party = makeParty(60);
    MapStatsEntry map = {};
    map.id = 65;

    const MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(16);
    REQUIRE(pStats != nullptr);

    const GameplayMonsterBolsterResult bolster =
        resolveGameplayMonsterBolster(
            GameplayBolsterRuntimeContext{
                .pMap = &map,
                .pMonsterTable = &monsterTable,
                .pBolsterMapTable = &mapTable,
                .pBolsterMonsterTable = &monsterSettingsTable,
                .pParty = &party,
                .bolsterMonstersEnabled = true,
            },
            *pStats,
            nullptr);

    CHECK(bolster.generatedAttack2);
    CHECK(bolster.generatedAttack2IsRanged);
    CHECK(bolster.copyAttack1DamageToAttack2);
    CHECK_EQ(bolster.generatedAttack2MissileType, "Fire");
    CHECK_EQ(bolster.generatedAttack2Chance, 35);
    CHECK_EQ(bolster.generatedSpell1Id, 11u);
    CHECK_EQ(bolster.generatedSpell2Id, 5u);
    CHECK_EQ(bolster.generatedSpell1UseChance, 60);
    CHECK_EQ(bolster.generatedSpell2UseChance, 35);
    CHECK_EQ(bolster.spell1SkillLevel, 4u);
    CHECK_EQ(bolster.spell1SkillMastery, SkillMastery::Expert);
}

TEST_CASE("runtime bolster scales existing spell rank from effective pseudo-level")
{
    std::vector<std::string> caster = monsterStatsRow(16, "Regnan Sorcerer", 10, 100, 5, "Short", 120);
    caster[24] = "100";
    caster[25] = "Lightning Bolt,B,3";

    MonsterTable monsterTable;
    REQUIRE(monsterTable.loadStatsFromRows({
        caster,
        monsterStatsRow(17, "Regnan Battlemage", 10, 120, 7, "Short", 120),
        monsterStatsRow(18, "Regnan Archmage", 10, 140, 9, "Short", 120),
    }));
    MergedBolsterMapTable mapTable = makeBolsterMapTable(true);
    MergedBolsterMonsterTable monsterSettingsTable = makeGeneratedAbilityMonsterSettingsTable();
    Party party = makeParty(35);
    MapStatsEntry map = {};
    map.id = 65;

    const MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(16);
    REQUIRE(pStats != nullptr);

    const GameplayMonsterBolsterResult bolster =
        resolveGameplayMonsterBolster(
            GameplayBolsterRuntimeContext{
                .pMap = &map,
                .pMonsterTable = &monsterTable,
                .pBolsterMapTable = &mapTable,
                .pBolsterMonsterTable = &monsterSettingsTable,
                .pParty = &party,
                .bolsterMonstersEnabled = true,
            },
            *pStats,
            nullptr);

    CHECK_EQ(bolster.maxHp, 189);
    CHECK_EQ(bolster.generatedSpell1Id, 0u);
    CHECK_EQ(bolster.spell1SkillLevel, 6u);
    CHECK_EQ(bolster.spell1SkillMastery, SkillMastery::Master);
}

TEST_CASE("runtime bolster applies pseudo-level HP formula to elementals")
{
    MonsterTable monsterTable = makeElementalMonsterTable();
    MergedBolsterMapTable mapTable = makeBolsterMapTable(true);
    MergedBolsterMonsterTable monsterSettingsTable = makeElementalMonsterSettingsTable();
    Party party = makeParty(30);
    MapStatsEntry map = {};
    map.id = 65;
    MonsterEntry monsterEntry = {};
    monsterEntry.height = 160;

    const MonsterTable::MonsterStatsEntry *pStats = monsterTable.findStatsById(76);
    REQUIRE(pStats != nullptr);

    const GameplayMonsterBolsterResult bolster =
        resolveGameplayMonsterBolster(
            GameplayBolsterRuntimeContext{
                .pMap = &map,
                .pMonsterTable = &monsterTable,
                .pBolsterMapTable = &mapTable,
                .pBolsterMonsterTable = &monsterSettingsTable,
                .pParty = &party,
                .bolsterMonstersEnabled = true,
            },
            *pStats,
            &monsterEntry);

    CHECK_EQ(bolster.maxHp, 153);
}

TEST_CASE("runtime bolster derives monster power from catch-up effective level")
{
    MonsterTable monsterTable;
    std::vector<std::string> youngBehemoth = monsterStatsRow(208, "Young Behemoth", 45, 337, 35, "Long", 250);
    youngBehemoth[7] = "50D10";
    youngBehemoth[18] = "3D10+20";
    std::vector<std::string> behemoth = monsterStatsRow(209, "Behemoth", 60, 540, 50, "Med", 260);
    behemoth[7] = "100D10";
    behemoth[18] = "4D10+30";
    std::vector<std::string> ancientBehemoth = monsterStatsRow(210, "Ancient Behemoth", 85, 977, 80, "Short", 300);
    ancientBehemoth[6] = "8075";
    ancientBehemoth[7] = "200D10";
    ancientBehemoth[18] = "5D10+40";
    std::vector<std::string> emeraldDragon = monsterStatsRow(112, "Emerald Dragon", 75, 787, 60, "Long", 240);
    std::vector<std::string> sapphireDragon = monsterStatsRow(113, "Sapphire Dragon", 100, 1300, 80, "Med", 260);
    sapphireDragon[6] = "11000";
    sapphireDragon[18] = "14D8";
    std::vector<std::string> rubyDragon = monsterStatsRow(114, "Ruby Dragon", 125, 1937, 100, "Short", 300);
    std::vector<std::string> fireLizard = monsterStatsRow(505, "Fire Lizard", 40, 280, 40, "Med", 200);
    fireLizard[6] = "2000";
    fireLizard[7] = "100D10+L4";
    std::vector<std::string> lightningLizard =
        monsterStatsRow(506, "Lightning Lizard", 50, 400, 50, "Short", 220);
    lightningLizard[6] = "3000";
    lightningLizard[7] = "150D10+L5";
    std::vector<std::string> thunderLizard = monsterStatsRow(507, "Thunder Lizard", 60, 540, 60, "Short", 240);
    thunderLizard[6] = "4200";
    thunderLizard[7] = "200D10+L5";
    std::vector<std::string> wyrm = monsterStatsRow(511, "Wyrm", 50, 400, 40, "Med", 180);
    std::vector<std::string> giantWyrm = monsterStatsRow(512, "Giant Wyrm", 60, 540, 50, "Med", 160);
    std::vector<std::string> greatWyrm = monsterStatsRow(513, "Great Wyrm", 70, 700, 60, "Short", 140);
    std::vector<std::string> redDragon = monsterStatsRow(514, "Red Dragon", 80, 880, 60, "Long", 240);
    std::vector<std::string> blueDragon = monsterStatsRow(515, "Blue Dragon", 90, 1080, 80, "Med", 260);
    std::vector<std::string> goldDragon = monsterStatsRow(516, "Gold Dragon", 100, 1300, 100, "Short", 300);
    goldDragon[6] = "11000";
    goldDragon[18] = "16D8";

    REQUIRE(monsterTable.loadStatsFromRows({
        emeraldDragon,
        sapphireDragon,
        rubyDragon,
        youngBehemoth,
        behemoth,
        ancientBehemoth,
        fireLizard,
        lightningLizard,
        thunderLizard,
        wyrm,
        giantWyrm,
        greatWyrm,
        redDragon,
        blueDragon,
        goldDragon,
    }));

    MergedBolsterMapTable mapTable = makeBolsterMapTable(true);
    MergedBolsterMonsterTable monsterSettingsTable;
    REQUIRE(monsterSettingsTable.loadFromRows({
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
        {"112", "Emerald Dragon", "Construct", "Dragon", "Neutral", "", "Strength", "0", "-", "-", "-", "-", "-", "-",
         "", "", "300"},
        {"113", "Sapphire Dragon", "Construct", "Dragon", "Neutral", "", "Strength", "0", "-", "-", "-", "-", "-",
         "-", "", "", "300"},
        {"114", "Ruby Dragon", "Construct", "Dragon", "Neutral", "", "Strength", "0", "-", "-", "-", "-", "-", "-",
         "", "", "300"},
        {"208", "Young Behemoth", "Creature", "", "Neutral", "", "Strength", "0", "-", "-", "-", "x", "-", "-",
         "", "", "300"},
        {"209", "Behemoth", "Creature", "", "Neutral", "", "Strength", "0", "-", "-", "-", "x", "-", "-",
         "", "", "300"},
        {"210", "Ancient Behemoth", "Creature", "", "Neutral", "", "Strength", "0", "-", "-", "-", "x", "-", "-",
         "", "", "300"},
        {"505", "Fire Lizard", "Creature", "", "Neutral", "", "Strength", "0", "-", "x", "-", "x", "-", "-",
         "", "", "300"},
        {"506", "Lightning Lizard", "Creature", "", "Neutral", "", "Strength", "0", "-", "x", "-", "x", "-", "-",
         "", "", "300"},
        {"507", "Thunder Lizard", "Creature", "", "Neutral", "", "Strength", "0", "-", "x", "-", "x", "-", "-",
         "", "", "300"},
        {"511", "Wyrm", "Dragon", "", "Neutral", "", "Strength", "0", "-", "-", "-", "x", "-", "-",
         "", "", "300"},
        {"512", "Giant Wyrm", "Dragon", "", "Neutral", "", "Strength", "0", "-", "-", "-", "x", "-", "-",
         "", "", "300"},
        {"513", "Great Wyrm", "Dragon", "", "Neutral", "", "Strength", "0", "-", "-", "-", "x", "-", "-",
         "", "", "300"},
        {"514", "Red Dragon", "Dragon", "", "Neutral", "", "Strength", "0", "-", "x", "-", "x", "-", "-",
         "", "", "300"},
        {"515", "Blue Dragon", "Dragon", "", "Neutral", "", "Strength", "0", "-", "x", "-", "x", "-", "-",
         "", "", "300"},
        {"516", "Gold Dragon", "Dragon", "", "Neutral", "", "Strength", "0", "-", "x", "-", "x", "-", "-",
         "", "", "300"},
    }));

    Party party = makeParty(90);
    MapStatsEntry map = {};
    map.id = 65;
    MonsterEntry largeMonsterEntry = {};
    largeMonsterEntry.height = 256;

    const MonsterTable::MonsterStatsEntry *pBehemoth = monsterTable.findStatsById(210);
    const MonsterTable::MonsterStatsEntry *pFireLizard = monsterTable.findStatsById(505);
    const MonsterTable::MonsterStatsEntry *pLightningLizard = monsterTable.findStatsById(506);
    const MonsterTable::MonsterStatsEntry *pThunderLizard = monsterTable.findStatsById(507);
    const MonsterTable::MonsterStatsEntry *pGreatWyrm = monsterTable.findStatsById(513);
    const MonsterTable::MonsterStatsEntry *pRedDragon = monsterTable.findStatsById(514);
    const MonsterTable::MonsterStatsEntry *pBlueDragon = monsterTable.findStatsById(515);
    const MonsterTable::MonsterStatsEntry *pGoldDragon = monsterTable.findStatsById(516);
    const MonsterTable::MonsterStatsEntry *pSapphireDragon = monsterTable.findStatsById(113);
    REQUIRE(pBehemoth != nullptr);
    REQUIRE(pFireLizard != nullptr);
    REQUIRE(pLightningLizard != nullptr);
    REQUIRE(pThunderLizard != nullptr);
    REQUIRE(pGreatWyrm != nullptr);
    REQUIRE(pRedDragon != nullptr);
    REQUIRE(pBlueDragon != nullptr);
    REQUIRE(pGoldDragon != nullptr);
    REQUIRE(pSapphireDragon != nullptr);

    const GameplayMonsterBolsterResult behemothBolster =
        resolveGameplayMonsterBolster(
            GameplayBolsterRuntimeContext{
                .pMap = &map,
                .pMonsterTable = &monsterTable,
                .pBolsterMapTable = &mapTable,
                .pBolsterMonsterTable = &monsterSettingsTable,
                .pParty = &party,
                .bolsterMonstersEnabled = true,
            },
            *pBehemoth,
            &largeMonsterEntry);
    const GameplayMonsterBolsterResult goldBolster =
        resolveGameplayMonsterBolster(
            GameplayBolsterRuntimeContext{
                .pMap = &map,
                .pMonsterTable = &monsterTable,
                .pBolsterMapTable = &mapTable,
                .pBolsterMonsterTable = &monsterSettingsTable,
                .pParty = &party,
                .bolsterMonstersEnabled = true,
            },
            *pGoldDragon,
            &largeMonsterEntry);
    const GameplayMonsterBolsterResult sapphireBolster =
        resolveGameplayMonsterBolster(
            GameplayBolsterRuntimeContext{
                .pMap = &map,
                .pMonsterTable = &monsterTable,
                .pBolsterMapTable = &mapTable,
                .pBolsterMonsterTable = &monsterSettingsTable,
                .pParty = &party,
                .bolsterMonstersEnabled = true,
            },
            *pSapphireDragon,
            &largeMonsterEntry);

    CHECK_EQ(behemothBolster.maxHp, 1059);
    CHECK_EQ(behemothBolster.armorClass, 84);
    CHECK_EQ(behemothBolster.moveSpeed, 314);
    CHECK_EQ(behemothBolster.attack1DamageDiceRolls, 5);
    CHECK_EQ(behemothBolster.attack1DamageDiceSides, 10);
    CHECK_EQ(behemothBolster.attack1DamageBonus, 43);
    CHECK_EQ(
        gameplayBolsterExperienceReward(
            pBehemoth->experience,
            pBehemoth->hitPoints,
            behemothBolster.rewardMultiplier),
        8811u);
    CHECK_EQ(
        gameplayBolsterLootPrototype(
            pBehemoth->loot,
            pBehemoth->hitPoints,
            behemothBolster.rewardMultiplier).goldDiceSides,
        10);

    CHECK_FALSE(goldBolster.statsEnabled);
    CHECK_EQ(goldBolster.maxHp, 1300);
    CHECK_EQ(goldBolster.rewardMultiplier, doctest::Approx(1.0f));
    CHECK_FALSE(sapphireBolster.statsEnabled);
    CHECK_EQ(sapphireBolster.maxHp, 1300);
    CHECK_EQ(sapphireBolster.rewardMultiplier, doctest::Approx(1.0f));

    Party peerLevelParty = makeParty(100);
    MonsterEntry greatWyrmEntry = {};
    greatWyrmEntry.height = 140;
    MonsterEntry redDragonEntry = {};
    redDragonEntry.height = 240;
    MonsterEntry blueDragonEntry = {};
    blueDragonEntry.height = 260;
    MonsterEntry standardGoldDragonEntry = {};
    standardGoldDragonEntry.height = 300;
    MonsterEntry fireLizardEntry = {};
    fireLizardEntry.height = 200;
    MonsterEntry lightningLizardEntry = {};
    lightningLizardEntry.height = 220;
    MonsterEntry thunderLizardEntry = {};
    thunderLizardEntry.height = 240;
    const GameplayMonsterBolsterResult peerFireLizardBolster =
        resolveGameplayMonsterBolster(
            GameplayBolsterRuntimeContext{
                .pMap = &map,
                .pMonsterTable = &monsterTable,
                .pBolsterMapTable = &mapTable,
                .pBolsterMonsterTable = &monsterSettingsTable,
                .pParty = &peerLevelParty,
                .bolsterMonstersEnabled = true,
            },
            *pFireLizard,
            &fireLizardEntry);
    const GameplayMonsterBolsterResult peerLightningLizardBolster =
        resolveGameplayMonsterBolster(
            GameplayBolsterRuntimeContext{
                .pMap = &map,
                .pMonsterTable = &monsterTable,
                .pBolsterMapTable = &mapTable,
                .pBolsterMonsterTable = &monsterSettingsTable,
                .pParty = &peerLevelParty,
                .bolsterMonstersEnabled = true,
            },
            *pLightningLizard,
            &lightningLizardEntry);
    const GameplayMonsterBolsterResult peerThunderLizardBolster =
        resolveGameplayMonsterBolster(
            GameplayBolsterRuntimeContext{
                .pMap = &map,
                .pMonsterTable = &monsterTable,
                .pBolsterMapTable = &mapTable,
                .pBolsterMonsterTable = &monsterSettingsTable,
                .pParty = &peerLevelParty,
                .bolsterMonstersEnabled = true,
            },
            *pThunderLizard,
            &thunderLizardEntry);
    const GameplayMonsterBolsterResult peerGreatWyrmBolster =
        resolveGameplayMonsterBolster(
            GameplayBolsterRuntimeContext{
                .pMap = &map,
                .pMonsterTable = &monsterTable,
                .pBolsterMapTable = &mapTable,
                .pBolsterMonsterTable = &monsterSettingsTable,
                .pParty = &peerLevelParty,
                .bolsterMonstersEnabled = true,
            },
            *pGreatWyrm,
            &greatWyrmEntry);
    const GameplayMonsterBolsterResult peerRedDragonBolster =
        resolveGameplayMonsterBolster(
            GameplayBolsterRuntimeContext{
                .pMap = &map,
                .pMonsterTable = &monsterTable,
                .pBolsterMapTable = &mapTable,
                .pBolsterMonsterTable = &monsterSettingsTable,
                .pParty = &peerLevelParty,
                .bolsterMonstersEnabled = true,
            },
            *pRedDragon,
            &redDragonEntry);
    const GameplayMonsterBolsterResult peerBlueDragonBolster =
        resolveGameplayMonsterBolster(
            GameplayBolsterRuntimeContext{
                .pMap = &map,
                .pMonsterTable = &monsterTable,
                .pBolsterMapTable = &mapTable,
                .pBolsterMonsterTable = &monsterSettingsTable,
                .pParty = &peerLevelParty,
                .bolsterMonstersEnabled = true,
            },
            *pBlueDragon,
            &blueDragonEntry);
    const GameplayMonsterBolsterResult peerGoldDragonBolster =
        resolveGameplayMonsterBolster(
            GameplayBolsterRuntimeContext{
                .pMap = &map,
                .pMonsterTable = &monsterTable,
                .pBolsterMapTable = &mapTable,
                .pBolsterMonsterTable = &monsterSettingsTable,
                .pParty = &peerLevelParty,
                .bolsterMonstersEnabled = true,
            },
            *pGoldDragon,
            &standardGoldDragonEntry);

    CHECK_EQ(peerFireLizardBolster.maxHp, 840);
    CHECK_EQ(peerLightningLizardBolster.maxHp, 977);
    CHECK_EQ(peerThunderLizardBolster.maxHp, 1038);
    CHECK_EQ(
        gameplayBolsterExperienceReward(
            pThunderLizard->experience,
            pThunderLizard->hitPoints,
            peerThunderLizardBolster.rewardMultiplier),
        8624u);
    CHECK_EQ(
        gameplayBolsterLootPrototype(
            pThunderLizard->loot,
            pThunderLizard->hitPoints,
            peerThunderLizardBolster.rewardMultiplier).goldDiceSides,
        15);
    CHECK_EQ(peerGreatWyrmBolster.maxHp, 1101);
    CHECK_EQ(peerRedDragonBolster.maxHp, 1165);
    CHECK_EQ(peerBlueDragonBolster.maxHp, 1231);
    CHECK_EQ(peerGoldDragonBolster.maxHp, 1300);

    Party highLevelParty = makeParty(150);
    MonsterEntry goldDragonEntry = {};
    goldDragonEntry.height = 487;
    const GameplayMonsterBolsterResult highLevelBehemothBolster =
        resolveGameplayMonsterBolster(
            GameplayBolsterRuntimeContext{
                .pMap = &map,
                .pMonsterTable = &monsterTable,
                .pBolsterMapTable = &mapTable,
                .pBolsterMonsterTable = &monsterSettingsTable,
                .pParty = &highLevelParty,
                .bolsterMonstersEnabled = true,
            },
            *pBehemoth,
            &largeMonsterEntry);
    const GameplayMonsterBolsterResult highLevelGoldBolster =
        resolveGameplayMonsterBolster(
            GameplayBolsterRuntimeContext{
                .pMap = &map,
                .pMonsterTable = &monsterTable,
                .pBolsterMapTable = &mapTable,
                .pBolsterMonsterTable = &monsterSettingsTable,
                .pParty = &highLevelParty,
                .bolsterMonstersEnabled = true,
            },
            *pGoldDragon,
            &goldDragonEntry);
    const GameplayMonsterBolsterResult highLevelSapphireBolster =
        resolveGameplayMonsterBolster(
            GameplayBolsterRuntimeContext{
                .pMap = &map,
                .pMonsterTable = &monsterTable,
                .pBolsterMapTable = &mapTable,
                .pBolsterMonsterTable = &monsterSettingsTable,
                .pParty = &highLevelParty,
                .bolsterMonstersEnabled = true,
            },
            *pSapphireDragon,
            &largeMonsterEntry);

    CHECK_EQ(highLevelBehemothBolster.maxHp, 1937);
    CHECK_EQ(highLevelBehemothBolster.attack1DamageDiceRolls, 6);
    CHECK_EQ(highLevelBehemothBolster.attack1DamageDiceSides, 12);
    CHECK_EQ(highLevelBehemothBolster.attack1DamageBonus, 60);
    CHECK_EQ(
        gameplayBolsterExperienceReward(
            pBehemoth->experience,
            pBehemoth->hitPoints,
            highLevelBehemothBolster.rewardMultiplier),
        16875u);
    CHECK_EQ(
        highLevelBehemothBolster.rewardMultiplier,
        static_cast<float>(highLevelBehemothBolster.maxHp) / static_cast<float>(pBehemoth->hitPoints));

    CHECK_EQ(highLevelGoldBolster.maxHp, 2051);
    CHECK_EQ(highLevelGoldBolster.attack1DamageDiceRolls, 18);
    CHECK_EQ(highLevelGoldBolster.attack1DamageDiceSides, 9);
    CHECK_EQ(highLevelGoldBolster.attack1DamageBonus, 3);
    CHECK_EQ(
        gameplayBolsterExperienceReward(
            pGoldDragon->experience,
            pGoldDragon->hitPoints,
            highLevelGoldBolster.rewardMultiplier),
        17931u);
    CHECK_EQ(
        highLevelGoldBolster.rewardMultiplier,
        static_cast<float>(highLevelGoldBolster.maxHp) / static_cast<float>(pGoldDragon->hitPoints));

    CHECK_EQ(highLevelSapphireBolster.maxHp, 2051);
    CHECK_EQ(highLevelSapphireBolster.rewardMultiplier, doctest::Approx(1.5776923f));
}

TEST_CASE("runtime bolster caps low level monster rewards and damage at capped HP pseudo-level")
{
    MonsterTable monsterTable;
    std::vector<std::string> apprenticeMage =
        monsterStatsRow(610, "Apprentice Mage", 2, 6, 4, "Med", 140);
    apprenticeMage[6] = "24";
    apprenticeMage[7] = "5%2D6+L1Staff";
    apprenticeMage[18] = "2D4";
    apprenticeMage[25] = "Fire Bolt,N,1";
    std::vector<std::string> goblin = monsterStatsRow(271, "Goblin", 4, 13, 6, "Med", 160);
    goblin[6] = "56";
    goblin[7] = "4D4";
    goblin[18] = "1D9";
    std::vector<std::string> hobgoblin = monsterStatsRow(272, "Hobgoblin", 6, 21, 10, "Med", 170);
    hobgoblin[6] = "96";
    hobgoblin[7] = "8D4";
    hobgoblin[18] = "1D9+2";
    std::vector<std::string> goblinLord = monsterStatsRow(273, "Goblin Lord", 10, 40, 14, "Short", 180);
    goblinLord[6] = "200";
    goblinLord[7] = "10%15D4+L1";
    goblinLord[18] = "1D9+4";

    REQUIRE(monsterTable.loadStatsFromRows({apprenticeMage, goblin, hobgoblin, goblinLord}));

    MergedBolsterMapTable mapTable = makeBolsterMapTable(true);
    MergedBolsterMonsterTable monsterSettingsTable;
    REQUIRE(monsterSettingsTable.loadFromRows({
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
        {"271", "Goblin", "Goblin", "", "Neutral", "", "Strength", "0", "-", "-", "-", "-", "-", "-", "", "", "500"},
        {"272", "Hobgoblin", "Goblin", "", "Neutral", "", "Strength", "0", "-", "-", "-", "-", "-", "-",
         "", "", "400"},
        {"273", "Goblin Lord", "Goblin", "", "Neutral", "", "Strength", "0", "-", "x", "-", "-", "-", "-",
         "", "", "300"},
        {"610", "Apprentice Mage", "Human", "", "Neutral", "M", "Magic", "Fire", "-", "x", "x", "-", "-", "-",
         "", "", "300"},
    }));

    Party party = makeParty(100);
    MapStatsEntry map = {};
    map.id = 65;

    const MonsterTable::MonsterStatsEntry *pApprenticeMage = monsterTable.findStatsById(610);
    const MonsterTable::MonsterStatsEntry *pGoblin = monsterTable.findStatsById(271);
    REQUIRE(pApprenticeMage != nullptr);
    REQUIRE(pGoblin != nullptr);

    const GameplayMonsterBolsterResult mageBolster =
        resolveGameplayMonsterBolster(
            GameplayBolsterRuntimeContext{
                .pMap = &map,
                .pMonsterTable = &monsterTable,
                .pBolsterMapTable = &mapTable,
                .pBolsterMonsterTable = &monsterSettingsTable,
                .pParty = &party,
                .bolsterMonstersEnabled = true,
            },
            *pApprenticeMage,
            nullptr);

    CHECK_EQ(mageBolster.maxHp, 18);
    CHECK_EQ(mageBolster.spell1SkillLevel, 1u);
    CHECK_EQ(mageBolster.spell1SkillMastery, SkillMastery::Normal);
    CHECK_EQ(mageBolster.rewardMultiplier, doctest::Approx(3.0f));
    CHECK_EQ(
        gameplayBolsterExperienceReward(
            pApprenticeMage->experience,
            pApprenticeMage->hitPoints,
            mageBolster.rewardMultiplier),
        75u);
    CHECK_EQ(
        gameplayBolsterLootPrototype(
            pApprenticeMage->loot,
            pApprenticeMage->hitPoints,
            mageBolster.rewardMultiplier).goldDiceRolls,
        2);
    CHECK_EQ(
        gameplayBolsterLootPrototype(
            pApprenticeMage->loot,
            pApprenticeMage->hitPoints,
            mageBolster.rewardMultiplier).goldDiceSides,
        15);

    Party highLevelParty = makeParty(150);
    const GameplayMonsterBolsterResult bolster =
        resolveGameplayMonsterBolster(
            GameplayBolsterRuntimeContext{
                .pMap = &map,
                .pMonsterTable = &monsterTable,
                .pBolsterMapTable = &mapTable,
                .pBolsterMonsterTable = &monsterSettingsTable,
                .pParty = &highLevelParty,
                .bolsterMonstersEnabled = true,
            },
            *pGoblin,
            nullptr);

    CHECK_EQ(bolster.maxHp, 65);
    CHECK_EQ(bolster.attack1DamageDiceRolls, 2);
    CHECK_EQ(bolster.attack1DamageDiceSides, 17);
    CHECK_EQ(bolster.attack1DamageBonus, 1);
    CHECK_EQ(gameplayBolsterExperienceReward(pGoblin->experience, pGoblin->hitPoints, bolster.rewardMultiplier), 375u);
    CHECK_EQ(
        gameplayBolsterLootPrototype(
            pGoblin->loot,
            pGoblin->hitPoints,
            bolster.rewardMultiplier).goldDiceSides,
        15);
}

TEST_CASE("runtime bolster player armor class formula only applies to bolstered monsters")
{
    CHECK_EQ(gameplayBolsterPlayerArmorClass(50, 10, 20, false), 50);
    CHECK_EQ(gameplayBolsterPlayerArmorClass(50, 10, 20, true), 25);
    CHECK_EQ(gameplayBolsterPlayerArmorClass(50, 30, 20, true), 50);
}

TEST_CASE("runtime bolster scales experience and corpse loot rewards")
{
    CHECK_EQ(gameplayBolsterRewardMultiplier(100, 300, true), doctest::Approx(3.0f));
    CHECK_EQ(gameplayBolsterRewardMultiplier(100, 3000, true), doctest::Approx(10.0f));
    CHECK_EQ(gameplayBolsterRewardMultiplier(100, 300, false), doctest::Approx(1.0f));
    CHECK_EQ(gameplayBolsterExperienceReward(56, 13, 10.0f), 816u);
    CHECK_EQ(gameplayBolsterExperienceReward(50, 280, 10.0f), 623u);

    MonsterTable::LootPrototype loot = {};
    loot.goldDiceRolls = 2;
    loot.goldDiceSides = 6;
    loot.itemChance = 25;
    loot.itemLevel = 2;
    loot.itemKind = MonsterTable::LootItemKind::Weapon;

    const MonsterTable::LootPrototype scaledLoot = gameplayBolsterLootPrototype(loot, 100, 4.0f);

    CHECK_EQ(scaledLoot.goldDiceRolls, 2);
    CHECK_EQ(scaledLoot.goldDiceSides, 15);
    CHECK_EQ(scaledLoot.itemChance, 75);
    CHECK_EQ(scaledLoot.itemLevel, 5);
    CHECK_EQ(scaledLoot.itemKind, MonsterTable::LootItemKind::Weapon);
}
