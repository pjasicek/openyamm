#include "doctest/doctest.h"
#include "engine/TextTable.h"
#include "game/gameplay/GameMechanics.h"
#include "game/items/InventoryItemUseRuntime.h"
#include "game/party/Party.h"
#include "game/party/PartySpellSystem.h"
#include "game/party/SkillData.h"
#include "game/rules/GameRules.h"
#include "game/tables/MergedBaseTables.h"
#include "game/tables/SpellTable.h"
#include "tests/RegressionGameData.h"

#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <optional>
#include <random>
#include <sstream>
#include <string>
#include <vector>

using namespace OpenYAMM::Game;

// Golden checks that the Standard ruleset keeps its behaviour while its rules move from code into data
// (devdocs/maw/HANDOFF.md, phase 2).
namespace
{
std::string readSourceFile(const std::string &relativePath)
{
    std::ifstream input(std::filesystem::path(OPENYAMM_SOURCE_DIR) / relativePath);
    std::ostringstream contents;
    contents << input.rdbuf();
    return contents.str();
}

std::vector<std::vector<std::string>> readTable(const std::string &relativePath)
{
    const std::optional<OpenYAMM::Engine::TextTable> table =
        OpenYAMM::Engine::TextTable::parseTabSeparated(readSourceFile(relativePath));
    std::vector<std::vector<std::string>> rows;

    for (size_t rowIndex = 0; table && rowIndex < table->getRowCount(); ++rowIndex)
    {
        rows.push_back(table->getRow(rowIndex));
    }

    return rows;
}

// Set OPENYAMM_UPDATE_GOLDEN=1 to rewrite a golden file after an intended Standard change.
bool updatingGolden()
{
    const char *pValue = std::getenv("OPENYAMM_UPDATE_GOLDEN");
    return pValue != nullptr && std::string(pValue) == "1";
}

std::string potionFingerprint(const Party &party)
{
    const Character &m = party.members()[0];
    std::ostringstream out;
    out << m.might << ' ' << m.intellect << ' ' << m.personality << ' ' << m.endurance << ' ' << m.accuracy << ' '
        << m.speed << ' ' << m.luck << " | " << m.permanentBonuses.might << ' ' << m.permanentBonuses.intellect << ' '
        << m.permanentBonuses.personality << ' ' << m.permanentBonuses.endurance << ' ' << m.permanentBonuses.accuracy
        << ' ' << m.permanentBonuses.speed << ' ' << m.permanentBonuses.luck << " | " << m.baseResistances.fire << ' '
        << m.baseResistances.air << ' ' << m.baseResistances.water << ' ' << m.baseResistances.earth << ' '
        << m.baseResistances.mind << ' ' << m.baseResistances.body << " | age " << m.ageModifier << " level "
        << m.levelModifier << " cond " << m.conditions.to_string() << " hp " << m.health << " sp " << m.spellPoints
        << " bits " << m.playerBits.size();
    for (size_t id = 0; id < size_t(CharacterBuffId::Count); ++id)
    {
        const CharacterBuffState *pBuff = party.characterBuff(0, CharacterBuffId(id));
        if (pBuff != nullptr && pBuff->remainingSeconds > 0)
        {
            out << " cb" << id << '=' << pBuff->remainingSeconds << '/' << pBuff->power << '/' << int(pBuff->skillMastery);
        }
    }
    for (size_t id = 0; id < size_t(PartyBuffId::Count); ++id)
    {
        const PartyBuffState *pBuff = party.partyBuff(PartyBuffId(id));
        if (pBuff != nullptr && pBuff->remainingSeconds > 0)
        {
            out << " pb" << id << '=' << pBuff->remainingSeconds << '/' << pBuff->power << '/' << pBuff->skillLevel << '/'
                << int(pBuff->skillMastery);
        }
    }
    return out.str();
}

Party makeTestParty(bool weak, int ageModifier)
{
    Character member = {};
    member.name = "Tester";
    member.might = 3;
    member.intellect = 30;
    member.personality = 2;
    member.endurance = 40;
    member.accuracy = 4;
    member.speed = 25;
    member.luck = 1;
    member.maxHealth = 500;
    member.health = 20;
    member.maxSpellPoints = 300;
    member.spellPoints = 10;
    member.ageModifier = ageModifier;
    // A ready active member pays each drink's recovery, as in the original games; the tester cannot act.
    Character payer = {};
    payer.name = "Payer";
    payer.maxHealth = 100;
    payer.health = 100;
    PartySeed seed = {};
    seed.members = {member, payer};
    Party party = {};
    party.seed(seed);
    party.setActiveMemberIndex(1);
    for (CharacterCondition condition : {CharacterCondition::Cursed, CharacterCondition::Asleep, CharacterCondition::Fear,
             CharacterCondition::Insane, CharacterCondition::PoisonMedium, CharacterCondition::DiseaseWeak,
             CharacterCondition::Paralyzed, CharacterCondition::Petrified, CharacterCondition::Drunk})
    {
        party.applyMemberCondition(0, condition);
    }
    if (weak)
    {
        party.applyMemberCondition(0, CharacterCondition::Weak);
    }
    return party;
}

OpenYAMM::Game::SkillMastery masteryNamed(const std::string &name)
{
    return name == "Grandmaster" ? OpenYAMM::Game::SkillMastery::Grandmaster
        : name == "Master"       ? OpenYAMM::Game::SkillMastery::Master
        : name == "Expert"       ? OpenYAMM::Game::SkillMastery::Expert
                                 : OpenYAMM::Game::SkillMastery::Normal;
}
}

TEST_CASE("standard party spell numbers match the pinned golden table")
{
    OpenYAMM::Game::SpellTable spellTable;
    REQUIRE(spellTable.loadFromRows(readTable("assets_dev/engine/data_tables/spells.txt")));
    size_t checked = 0;

    for (const std::vector<std::string> &row : readTable("tests/data/standard_spell_numbers.tsv"))
    {
        if (row.size() != 9 || row[0].empty() || row[0][0] == '#' || row[0] == "spell_id")
        {
            continue;
        }

        CAPTURE(row[0]);
        CAPTURE(row[1]);
        const int spellId = std::stoi(row[0]);
        const OpenYAMM::Game::SpellEntry *pEntry = spellTable.findById(spellId);
        REQUIRE(pEntry != nullptr);
        CHECK(OpenYAMM::Game::PartySpellSystem::describeSpell(uint32_t(spellId)).has_value());
        const OpenYAMM::Game::SpellMasteryNumbers numbers =
            OpenYAMM::Game::spellNumbersAtMastery(*pEntry, masteryNamed(row[1]));
        CHECK(pEntry->requiredMastery == masteryNamed(row[2]));
        CHECK_EQ(numbers.manaCost, std::stoi(row[3]));
        CHECK_EQ(numbers.recoveryTicks, std::stoi(row[4]));
        CHECK_EQ(numbers.damageBase, std::stoi(row[5]));
        CHECK_EQ(numbers.damageDiceMin, std::stoi(row[6]));
        CHECK_EQ(numbers.damageDiceMax, std::stoi(row[7]));
        CHECK_EQ(numbers.projectileCount, uint32_t(std::stoi(row[8])));
        ++checked;
    }

    CHECK_EQ(checked, 444u);
}

TEST_CASE("a standard drink costs the active member 100 ticks of recovery, as in the original games")
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    Character member = {};
    member.maxHealth = 100;
    member.health = 10;
    PartySeed seed = {};
    seed.members = {member, member, member};
    Party party = {};
    party.seed(seed);
    party.setActiveMemberIndex(1);
    const auto drinkCureWounds = [&](size_t drinkerIndex)
    {
        InventoryItem potion = {};
        potion.objectDescriptionId = 222;
        potion.standardEnchantPower = 10;
        return InventoryItemUseRuntime::useItemOnMember(party, drinkerIndex, potion, gameData.itemTable,
            &gameData.readableScrollTable, &gameData.mergedPotionSettingTable);
    };

    // Out of combat too: the active member pays, not the drinker.
    CHECK(drinkCureWounds(0).consumed);
    CHECK_EQ(party.members()[0].health, 30);
    CHECK_EQ(party.members()[0].recoverySecondsRemaining, 0.0f);
    CHECK_EQ(party.members()[1].recoverySecondsRemaining, doctest::Approx(ticksToRecoverySeconds(100)));

    // A recovering active member: the first ready member pays.
    CHECK(drinkCureWounds(1).consumed);
    CHECK_EQ(party.members()[0].recoverySecondsRemaining, doctest::Approx(ticksToRecoverySeconds(100)));

    // Nobody ready: no drink.
    party.applyRecoveryToMember(2, 1.0f);
    const InventoryItemUseResult refused = drinkCureWounds(2);
    CHECK_FALSE(refused.consumed);
    CHECK_EQ(refused.statusText, "Player must be active to consume the potion");
}

TEST_CASE("standard potion drinks match the pinned golden results")
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    std::ostringstream results;
    results << "# Character state after drinking each potion item at several powers, twice, from four starting states\n"
            << "# (weak or not, magically aged or not). Pinned when potion effects moved from code into\n"
            << "# potion_effects.yml (MAW phase 2, 2026-10-23), after checking every line against the old code.\n";

    for (uint32_t itemId = 220; itemId <= 291; ++itemId)
    {
        for (uint16_t power : {0, 1, 7, 40, 133})
        {
            for (int variant = 0; variant < 4; ++variant)
            {
                Party party = makeTestParty((variant & 1) != 0, (variant & 2) != 0 ? 6 : 0);
                InventoryItem potion = {};
                potion.objectDescriptionId = itemId;
                potion.standardEnchantPower = power;

                if (InventoryItemUseRuntime::classifyItemUse(potion, gameData.itemTable)
                    != InventoryItemUseAction::ConsumePotion)
                {
                    continue;
                }

                for (int drink = 0; drink < 2; ++drink)
                {
                    party.member(1)->recoverySecondsRemaining = 0.0f;
                    const InventoryItemUseResult result = InventoryItemUseRuntime::useItemOnMember(
                        party,
                        0,
                        potion,
                        gameData.itemTable,
                        &gameData.readableScrollTable,
                        &gameData.mergedPotionSettingTable);
                    results << itemId << '\t' << power << '\t' << variant << '\t' << drink << '\t'
                            << (result.consumed ? "consumed" : "refused") << '\t' << potionFingerprint(party) << '\n';
                }
            }
        }
    }

    const std::filesystem::path goldenPath =
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "tests/data/standard_potion_drinks.tsv";

    if (updatingGolden())
    {
        std::ofstream(goldenPath) << results.str();
    }

    CHECK(results.str() == readSourceFile("tests/data/standard_potion_drinks.tsv"));
}

TEST_CASE("standard damage resolution matches the pinned golden results")
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    const CombatRules &combat = standardGameRules().combat;
    std::ostringstream results;
    results << "# Damage after the Standard damage stages for fixed inputs and random seeds. Pinned when damage moved\n"
            << "# into the rules' stage pipeline (MAW phase 2, 2026-10-23), which calls the same formulas as before.\n";
    uint32_t seed = 1;

    for (const CombatDamageType type :
         {CombatDamageType::Physical, CombatDamageType::Fire, CombatDamageType::Mind, CombatDamageType::Light,
          CombatDamageType::Energy, CombatDamageType::Irresistible})
    {
        for (const int resistance : {0, 10, 50, 150, 199, 200})
        {
            for (const int damage : {1, 10, 100})
            {
                for (const int hourOfPower : {0, 20})
                {
                    std::mt19937 rng(++seed);
                    results << "monster\t" << int(type) << '\t' << resistance << '\t' << damage << '\t'
                            << hourOfPower << '\t'
                            << resolveDamageToMonster(combat, damage, type, resistance, hourOfPower, rng, {}) << '\n';

                    std::mt19937 weaponRng(seed);
                    MonsterDamageHit weapon = {};
                    weapon.amount = damage;
                    weapon.type = type;
                    weapon.weaponElements = ElementalDamageBonuses{.fire = damage / 2, .body = 3};
                    weapon.resistances = MonsterDamageResistances{
                        .fire = resistance, .body = resistance / 2, .physical = resistance};
                    weapon.hourOfPowerResistanceBonus = hourOfPower;
                    weapon.pRng = &weaponRng;
                    results << "weapon\t" << int(type) << '\t' << resistance << '\t' << damage << '\t' << hourOfPower
                            << '\t' << combat.damageToMonster(weapon) << '\n';
                }
            }
        }
    }

    for (const CombatDamageType type :
         {CombatDamageType::Physical, CombatDamageType::Fire, CombatDamageType::Spirit, CombatDamageType::Energy})
    {
        for (const int resistance : {0, 25, 120})
        {
            for (const bool shielded : {false, true})
            {
                for (const bool monsterAttack : {false, true})
                {
                    Character character = {};
                    character.luck = 30;
                    character.baseResistances.fire = resistance;
                    character.baseResistances.spirit = resistance;
                    character.energyResistance = resistance;
                    character.halfMissileDamage = shielded;
                    character.physicalDamageTakenMultiplier = 0.75f;
                    std::mt19937 rng(++seed);
                    CharacterDamageHit hit = {};
                    hit.amount = 60;
                    hit.type = type;
                    hit.pCharacter = &character;
                    hit.pItemTable = &gameData.itemTable;
                    hit.pStandardItemEnchantTable = &gameData.standardItemEnchantTable;
                    hit.pSpecialItemEnchantTable = &gameData.specialItemEnchantTable;
                    hit.monsterAttack = monsterAttack;
                    hit.physicalProjectile = true;
                    hit.pRng = &rng;
                    results << "character\t" << int(type) << '\t' << resistance << '\t' << shielded << '\t'
                            << monsterAttack << '\t' << combat.damageToCharacter(hit) << '\n';
                }
            }
        }
    }

    const std::filesystem::path goldenPath =
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "tests/data/standard_damage.tsv";

    if (updatingGolden())
    {
        std::ofstream(goldenPath) << results.str();
    }

    CHECK(results.str() == readSourceFile("tests/data/standard_damage.tsv"));
}
