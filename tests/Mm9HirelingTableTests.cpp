#include "doctest/doctest.h"

#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "game/data/GameDataLoader.h"
#include "game/events/EventRuntime.h"
#include "game/gameplay/GameMechanics.h"
#include "game/maps/SaveGame.h"
#include "game/mm9/Mm9HirelingTable.h"
#include "game/party/Party.h"
#include "game/tables/ItemTable.h"

#include <algorithm>
#include <filesystem>
#include <string>
#include <vector>

namespace
{
using OpenYAMM::Game::CharacterCondition;
using OpenYAMM::Game::CombatDamageType;
using OpenYAMM::Game::Mm9Hireling;
using OpenYAMM::Game::Mm9HirelingKind;
using OpenYAMM::Game::Mm9HirelingService;
using OpenYAMM::Game::Mm9HirelingTable;
using OpenYAMM::Game::Party;
using OpenYAMM::Game::SkillMastery;

const std::vector<std::string> Header = {
    "rude_id", "name", "kind", "portrait", "monster_row", "hire_qbit", "hire_fee", "wage", "gold_share_percent",
    "service", "service_cooldown_hours", "cured_conditions", "passive",
    "level", "hp", "ac", "recovery_seconds",
    "attack1_type", "attack1_damage", "attack2_type", "attack2_damage", "attack2_missile",
    "spell1", "spell1_share_percent", "spell2",
    "res_fire", "res_air", "res_water", "res_earth", "res_spirit", "res_mind", "res_body", "res_light", "res_dark",
    "res_physical",
};

std::vector<std::string> archerRow()
{
    return {"42", "Hrolf Spearmaster", "paid", "9npc01-01", "279", "90450", "300", "300", "2", "none", "0", "", "",
        "34", "276", "21", "2.310", "Phys", "2d9+17", "Phys", "5d3+10", "Arrow", "", "0", "",
        "0", "0", "0", "0", "0", "0", "0", "0", "0", "Imm"};
}

std::vector<std::string> casterRow()
{
    return {"44", "Arienh A'Klindor", "paid", "9npc03-01", "281", "90452", "500", "500", "5", "none", "0", "", "",
        "20", "120", "14", "2.475", "Phys", "2d4+8", "0", "0", "0", "Fireball,E,6", "60", "Toxic Cloud,M,7",
        "20", "20", "20", "20", "20", "20", "20", "20", "20", "0"};
}

std::vector<std::string> healerRow()
{
    return {"308", "Florie", "paid", "9npc13-01", "291", "90462", "2000", "1000", "20", "heal_cure", "24",
        "Cursed|PoisonWeak|DiseaseSevere", "experience_percent:10|identify_always|skill:Merchant+6",
        "25", "169", "16", "2.310", "Phys", "4d4+13", "0", "0", "0", "", "0", "",
        "20", "20", "20", "20", "20", "20", "20", "20", "20", "20"};
}

std::vector<std::string> storyRow()
{
    return {"2", "Forad Darre", "story", "9npc15-01", "252", "90029", "0", "0", "0", "none", "0", "", "",
        "50", "525", "50", "1.485", "Phys", "9d3", "0", "0", "0", "", "0", "",
        "40", "40", "40", "40", "40", "40", "40", "30", "40", "30"};
}

bool loadsWith(const std::vector<std::string> &row)
{
    Mm9HirelingTable table;
    return table.loadFromRows({Header, row});
}

Mm9HirelingTable sampleTable()
{
    Mm9HirelingTable table;
    REQUIRE(table.loadFromRows({Header, archerRow(), casterRow(), healerRow(), storyRow()}));
    return table;
}
}

TEST_CASE("MM9 hireling table parses typed rows")
{
    const Mm9HirelingTable table = sampleTable();
    REQUIRE_EQ(table.entries().size(), 4u);
    CHECK(table.find(999) == nullptr);

    const Mm9Hireling *pArcher = table.find(42);
    REQUIRE(pArcher != nullptr);
    CHECK_EQ(pArcher->name, "Hrolf Spearmaster");
    CHECK(pArcher->kind == Mm9HirelingKind::Paid);
    CHECK_EQ(pArcher->hireQBit, 90450u);
    CHECK_EQ(pArcher->hireFee, 300);
    CHECK_EQ(pArcher->wage, 300);
    CHECK_EQ(pArcher->goldSharePercent, 2);
    CHECK(pArcher->service == Mm9HirelingService::None);
    CHECK_EQ(pArcher->level, 34u);
    CHECK_EQ(pArcher->hitPoints, 276);
    CHECK_EQ(pArcher->armorClass, 21);
    CHECK(pArcher->recoverySeconds == doctest::Approx(2.31f));
    CHECK(pArcher->attack1.present);
    CHECK(pArcher->attack1.damageType == CombatDamageType::Physical);
    CHECK_EQ(pArcher->attack1.damage.diceRolls, 2);
    CHECK_EQ(pArcher->attack1.damage.diceSides, 9);
    CHECK_EQ(pArcher->attack1.damage.bonus, 17);
    CHECK(pArcher->attack1.missile.empty());
    CHECK(pArcher->attack2.present);
    CHECK_EQ(pArcher->attack2.missile, "Arrow");
    CHECK_EQ(pArcher->attack2.damage.diceRolls, 5);
    CHECK(pArcher->spells.empty());
    CHECK_EQ(pArcher->resistances.physical, 200);

    const Mm9Hireling *pCaster = table.find(44);
    REQUIRE(pCaster != nullptr);
    CHECK_FALSE(pCaster->attack2.present);
    REQUIRE_EQ(pCaster->spells.size(), 2u);
    CHECK_EQ(pCaster->spells[0].name, "fireball");
    CHECK(pCaster->spells[0].mastery == SkillMastery::Expert);
    CHECK_EQ(pCaster->spells[0].skillLevel, 6u);
    CHECK_EQ(pCaster->spells[1].name, "toxic cloud");
    CHECK(pCaster->spells[1].mastery == SkillMastery::Master);
    CHECK_EQ(pCaster->spells[1].skillLevel, 7u);
    CHECK_EQ(pCaster->spell1SharePercent, 60);
    CHECK_EQ(pCaster->resistances.fire, 20);

    const Mm9Hireling *pHealer = table.find(308);
    REQUIRE(pHealer != nullptr);
    CHECK(pHealer->service == Mm9HirelingService::HealCure);
    CHECK_EQ(pHealer->serviceCooldownHours, 24);
    CHECK(pHealer->curedConditions
        == std::vector<CharacterCondition>{
            CharacterCondition::Cursed, CharacterCondition::PoisonWeak, CharacterCondition::DiseaseSevere});
    CHECK_EQ(pHealer->passives.experiencePercent, 10);
    CHECK(pHealer->passives.identifyAlways);
    CHECK_FALSE(pHealer->passives.repairAlways);
    REQUIRE_EQ(pHealer->passives.skillBonuses.size(), 1u);
    CHECK_EQ(pHealer->passives.skillBonuses[0].skillName, "Merchant");
    CHECK_EQ(pHealer->passives.skillBonuses[0].amount, 6);

    const Mm9Hireling *pStory = table.find(2);
    REQUIRE(pStory != nullptr);
    CHECK(pStory->kind == Mm9HirelingKind::Story);
    CHECK_EQ(pStory->attack1.damage.bonus, 0);
}

TEST_CASE("MM9 hireling table rejects malformed rows")
{
    CHECK(loadsWith(archerRow()));

    Mm9HirelingTable table;
    std::vector<std::string> wrongHeader = Header;
    wrongHeader[1] = "display_name";
    CHECK_FALSE(table.loadFromRows({wrongHeader, archerRow()}));
    CHECK_FALSE(table.errors().empty());
    CHECK_FALSE(table.loadFromRows({Header}));
    CHECK_FALSE(table.loadFromRows({Header, archerRow(), archerRow()}));

    const auto changed = [](std::vector<std::string> row, size_t column, const std::string &value)
    {
        row[column] = value;
        return row;
    };
    std::vector<std::string> shortRow = archerRow();
    shortRow.pop_back();
    CHECK_FALSE(loadsWith(shortRow));
    CHECK_FALSE(loadsWith(changed(archerRow(), 0, "0")));
    CHECK_FALSE(loadsWith(changed(archerRow(), 2, "mercenary")));
    CHECK_FALSE(loadsWith(changed(archerRow(), 5, "x")));
    CHECK_FALSE(loadsWith(changed(storyRow(), 6, "100")));
    CHECK_FALSE(loadsWith(changed(archerRow(), 9, "resurrect")));
    // A service needs a cooldown, and only heal_cure cures conditions.
    CHECK_FALSE(loadsWith(changed(archerRow(), 9, "heal")));
    CHECK_FALSE(loadsWith(changed(archerRow(), 11, "Cursed")));
    CHECK_FALSE(loadsWith(changed(healerRow(), 11, "Cursed|Poisoned")));
    CHECK_FALSE(loadsWith(changed(healerRow(), 11, "")));
    CHECK_FALSE(loadsWith(changed(archerRow(), 12, "skill:Lockpicking+4")));
    CHECK_FALSE(loadsWith(changed(archerRow(), 12, "skill:merchant+4")));
    CHECK_FALSE(loadsWith(changed(archerRow(), 12, "skill:Merchant")));
    CHECK_FALSE(loadsWith(changed(archerRow(), 12, "gold_percent:0")));
    CHECK_FALSE(loadsWith(changed(archerRow(), 12, "fly_always")));
    CHECK_FALSE(loadsWith(changed(archerRow(), 14, "0")));
    CHECK_FALSE(loadsWith(changed(archerRow(), 16, "fast")));
    CHECK_FALSE(loadsWith(changed(archerRow(), 18, "lots")));
    CHECK_FALSE(loadsWith(changed(archerRow(), 17, "0")));
    // A second attack needs its missile, and no missile without one.
    CHECK_FALSE(loadsWith(changed(archerRow(), 21, "0")));
    CHECK_FALSE(loadsWith(changed(casterRow(), 21, "Arrow")));
    CHECK_FALSE(loadsWith(changed(casterRow(), 22, "Fireball,X,6")));
    CHECK_FALSE(loadsWith(changed(casterRow(), 22, "Fireball,E,0")));
    CHECK_FALSE(loadsWith(changed(casterRow(), 22, "")));
    CHECK_FALSE(loadsWith(changed(casterRow(), 23, "0")));
    CHECK_FALSE(loadsWith(changed(casterRow(), 23, "101")));
    CHECK_FALSE(loadsWith(changed(changed(casterRow(), 24, ""), 23, "60")));
    CHECK(loadsWith(changed(changed(casterRow(), 24, ""), 23, "100")));
    CHECK_FALSE(loadsWith(changed(archerRow(), 30, "high")));
}

TEST_CASE("MM9 world data loads the hireling table")
{
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assetFileSystem.initialize(
        sourceRoot,
        sourceRoot / "assets_dev",
        OpenYAMM::Engine::AssetScaleTier::X1,
        "mm9"));

    OpenYAMM::Game::GameDataLoader dataLoader = {};
    REQUIRE(dataLoader.loadCommonForGameplay(assetFileSystem));
    const Mm9HirelingTable &table = dataLoader.getMm9HirelingTable();
    REQUIRE_EQ(table.entries().size(), 15u);
    CHECK_EQ(std::count_if(table.entries().begin(), table.entries().end(),
                 [](const Mm9Hireling &entry) { return entry.kind == Mm9HirelingKind::Paid; }),
        13);

    const Mm9Hireling *pArienh = table.find(44);
    REQUIRE(pArienh != nullptr);
    REQUIRE_EQ(pArienh->spells.size(), 2u);
    CHECK_EQ(pArienh->spells[0].name, "fireball");
    CHECK_EQ(pArienh->spells[1].name, "toxic cloud");
    const Mm9Hireling *pAke = table.find(86);
    REQUIRE(pAke != nullptr);
    REQUIRE_EQ(pAke->spells.size(), 2u);
    CHECK_EQ(pAke->spells[0].name, "sparks");
    CHECK_EQ(pAke->spells[1].name, "lightning bolt");
    CHECK(pAke->spells[1].mastery == SkillMastery::Normal);
    for (uint32_t rudeId : {42u, 43u, 85u})
    {
        const Mm9Hireling *pArcher = table.find(rudeId);
        REQUIRE(pArcher != nullptr);
        CHECK_EQ(pArcher->attack2.missile, "Arrow");
    }
    const Mm9Hireling *pFlorie = table.find(308);
    REQUIRE(pFlorie != nullptr);
    CHECK(pFlorie->service == Mm9HirelingService::HealCure);
    CHECK_EQ(pFlorie->curedConditions.size(), 8u);
    const Mm9Hireling *pTamur = table.find(309);
    REQUIRE(pTamur != nullptr);
    CHECK(pTamur->kind == Mm9HirelingKind::Story);
    CHECK_EQ(pTamur->hireQBit, 90190u);
}

TEST_CASE("party keeps MM9 hirelings apart from its members, within MM9's limits")
{
    const Mm9HirelingTable table = sampleTable();
    Party party = {};
    party.seed(Party::createDefaultSeed());
    const size_t memberCount = party.members().size();
    party.setGameMinutes(3.0f * 1440.0f + 600.0f);

    REQUIRE(party.addHireling(*table.find(42)));
    CHECK_FALSE(party.addHireling(*table.find(42)));
    CHECK_EQ(party.members().size(), memberCount);
    REQUIRE_EQ(party.hirelings().size(), 1u);

    const OpenYAMM::Game::Mm9PartyHireling *pHrolf = party.findHireling(42);
    REQUIRE(pHrolf != nullptr);
    CHECK_EQ(pHrolf->character.name, "Hrolf Spearmaster");
    CHECK_EQ(pHrolf->character.portraitTextureName, "9npc01-01");
    CHECK_EQ(pHrolf->character.level, 34u);
    CHECK_EQ(pHrolf->character.maxHealth, 276);
    CHECK_EQ(pHrolf->character.health, 276);
    CHECK_EQ(pHrolf->character.armorClassModifier, 21);
    CHECK_EQ(pHrolf->character.baseResistances.physical, 200);
    CHECK(pHrolf->character.inventory.empty());
    CHECK(pHrolf->character.knownSpellIds.empty());
    CHECK_EQ(pHrolf->hireDay, 3u);
    CHECK(pHrolf->nextWageGameMinutes == doctest::Approx(3.0f * 1440.0f + 600.0f + 28.0f * 1440.0f));
    // MM9's lowest free formation cell, after the members' (Party::formationCell).
    CHECK_EQ(pHrolf->formationCell, int32_t(memberCount));

    REQUIRE(party.addHireling(*table.find(44)));
    CHECK_EQ(party.paidHirelingCount(), 2u);
    // A third paid retainer does not fit; the third slot is a story companion's.
    CHECK_FALSE(party.canAddHireling(*table.find(308)));
    CHECK_FALSE(party.addHireling(*table.find(308)));
    REQUIRE(party.canAddHireling(*table.find(2)));
    REQUIRE(party.addHireling(*table.find(2)));
    CHECK_EQ(party.findHireling(2)->nextWageGameMinutes, 0.0f);
    CHECK_EQ(party.hirelings().size(), 3u);

    CHECK(party.removeHireling(44));
    CHECK_FALSE(party.removeHireling(44));
    CHECK_EQ(party.paidHirelingCount(), 1u);
    CHECK(party.canAddHireling(*table.find(308)));

    party.reset();
    CHECK(party.hirelings().empty());
}

TEST_CASE("MM9 hirelings survive a save round trip")
{
    const Mm9HirelingTable table = sampleTable();
    Party party = {};
    party.seed(Party::createDefaultSeed());
    REQUIRE(party.addHireling(*table.find(44)));
    REQUIRE(party.addHireling(*table.find(2)));
    OpenYAMM::Game::Mm9PartyHireling *pArienh = party.findHireling(44);
    pArienh->character.health = 37;
    pArienh->character.conditions.set(size_t(CharacterCondition::PoisonMedium));
    pArienh->character.recoverySecondsRemaining = 1.25f;
    pArienh->buffs[size_t(OpenYAMM::Game::CharacterBuffId::Bless)].remainingSeconds = 90.0f;
    pArienh->buffs[size_t(OpenYAMM::Game::CharacterBuffId::Bless)].power = 5;
    pArienh->serviceReadyGameMinutes = 4321.0f;
    pArienh->formationCell = 4;

    OpenYAMM::Game::GameSaveData saveData = {};
    saveData.mapFileName = "mm9_hireling_roundtrip.odm";
    saveData.party = party.snapshot();
    const std::filesystem::path savePath =
        std::filesystem::temp_directory_path() / "openyamm_mm9_hireling_roundtrip.oysav";
    std::string error;
    REQUIRE(OpenYAMM::Game::saveGameDataToPath(savePath, saveData, error));
    const std::optional<OpenYAMM::Game::GameSaveData> loaded = OpenYAMM::Game::loadGameDataFromPath(savePath, error);
    std::filesystem::remove(savePath);
    REQUIRE_MESSAGE(loaded.has_value(), error.c_str());

    Party restored = {};
    restored.restoreSnapshot(loaded->party);
    CHECK_EQ(restored.members().size(), party.members().size());
    REQUIRE_EQ(restored.hirelings().size(), 2u);
    const OpenYAMM::Game::Mm9PartyHireling *pLoaded = restored.findHireling(44);
    REQUIRE(pLoaded != nullptr);
    CHECK(pLoaded->kind == Mm9HirelingKind::Paid);
    CHECK_EQ(pLoaded->character.name, "Arienh A'Klindor");
    CHECK_EQ(pLoaded->character.health, 37);
    CHECK_EQ(pLoaded->character.maxHealth, 120);
    CHECK(pLoaded->character.conditions.test(size_t(CharacterCondition::PoisonMedium)));
    CHECK(pLoaded->character.recoverySecondsRemaining == doctest::Approx(1.25f));
    CHECK_EQ(pLoaded->buffs[size_t(OpenYAMM::Game::CharacterBuffId::Bless)].power, 5);
    CHECK(pLoaded->nextWageGameMinutes == doctest::Approx(pArienh->nextWageGameMinutes));
    CHECK(pLoaded->serviceReadyGameMinutes == doctest::Approx(4321.0f));
    CHECK_EQ(pLoaded->formationCell, 4);
    CHECK(restored.findHireling(2)->kind == Mm9HirelingKind::Story);
    CHECK(restored.paidHirelingCount() == 1u);
}

TEST_CASE("MM9 hirelings wait behind in a world without them, and rejoin")
{
    const Mm9HirelingTable table = sampleTable();
    Party party = {};
    party.seed(Party::createDefaultSeed());
    REQUIRE(party.addHireling(*table.find(44)));
    REQUIRE(party.addHireling(*table.find(2)));
    party.findHireling(44)->character.health = 37;
    const size_t memberCount = party.members().size();
    REQUIRE_EQ(party.combatantCount(), memberCount + 2);

    party.setMm9HirelingsAlong(false);
    CHECK_FALSE(party.mm9HirelingsAlong());
    CHECK(party.hirelings().empty());
    CHECK_EQ(party.combatantCount(), memberCount);
    CHECK(party.findHireling(44) == nullptr);
    CHECK_EQ(party.paidHirelingCount(), 0u);
    // A save made there keeps them, and a party loaded there still has none along.
    const Party::Snapshot away = party.snapshot();
    CHECK_EQ(away.mm9Hirelings.size(), 2u);
    Party restored = {};
    restored.setMm9HirelingsAlong(false);
    restored.restoreSnapshot(away);
    CHECK(restored.hirelings().empty());
    CHECK_EQ(restored.snapshot().mm9Hirelings.size(), 2u);

    restored.setMm9HirelingsAlong(true);
    REQUIRE_EQ(restored.hirelings().size(), 2u);
    CHECK_EQ(restored.combatantCount(), memberCount + 2);
    REQUIRE(restored.findHireling(44) != nullptr);
    CHECK_EQ(restored.findHireling(44)->character.health, 37);
    CHECK(restored.findHireling(2)->kind == Mm9HirelingKind::Story);
}

TEST_CASE("MM6-MM8 followers are off in a world without them, and kept for other worlds")
{
    Party party = {};
    OpenYAMM::Game::PartySeed seed = {};
    OpenYAMM::Game::Character member = {};
    member.name = "Ada";
    member.maxHealth = 50;
    member.health = 50;
    seed.members = {member};
    party.seed(seed);

    OpenYAMM::Game::HiredNpcFollower follower = {};
    follower.npcId = 501;
    follower.professionId = 4; // Scholar: every item identifies.
    follower.weeklyCost = 300;
    party.addHiredNpcFollower(follower);

    OpenYAMM::Game::ItemDefinition item = {};
    item.equipStat = "Armor";
    CHECK(party.canIdentifyItem(item));
    OpenYAMM::Game::EventRuntimeState runtimeState = {};
    party.applyGlobalNpcStateTo(runtimeState);
    CHECK_EQ(runtimeState.hiredNpcFollowers.size(), 1u);

    party.setNpcFollowersActive(false);
    CHECK_FALSE(party.npcFollowersActive());
    CHECK_FALSE(party.canIdentifyItem(item));
    party.applyGlobalNpcStateTo(runtimeState);
    CHECK(runtimeState.hiredNpcFollowers.empty());
    // The map's own events cannot add followers there either.
    OpenYAMM::Game::EventRuntimeState eventState = {};
    OpenYAMM::Game::HiredNpcFollower scripted = {};
    scripted.npcId = 777;
    eventState.hiredNpcFollowers.push_back(scripted);
    party.applyEventRuntimeState(eventState, false);

    party.setNpcFollowersActive(true);
    CHECK(party.canIdentifyItem(item));
    party.applyGlobalNpcStateTo(runtimeState);
    REQUIRE_EQ(runtimeState.hiredNpcFollowers.size(), 1u);
    CHECK_EQ(runtimeState.hiredNpcFollowers[0].npcId, 501u);
    CHECK_EQ(party.snapshot().hiredNpcFollowers.size(), 1u);
}
