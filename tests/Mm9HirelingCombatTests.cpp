#include "doctest/doctest.h"

#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/TurnBasedCombatRuntime.h"
#include "game/mm9/Mm9HirelingCombat.h"
#include "game/mm9/Mm9HirelingTable.h"
#include "game/party/Party.h"
#include "game/party/PartySpellSystem.h"
#include "game/party/SpellIds.h"

#include "tests/PartySpellTestHarness.h"
#include "tests/RegressionGameData.h"

#include <array>
#include <optional>
#include <random>
#include <string>
#include <vector>

// MM9 hirelings in combat (devdocs/mm9/MM9_HIRELINGS_PLAN.md phases 3-5): shared rules, actions, monster targeting.
namespace
{
using OpenYAMM::Game::Character;
using OpenYAMM::Game::CharacterBuffId;
using OpenYAMM::Game::CharacterCondition;
using OpenYAMM::Game::CombatDamageType;
using OpenYAMM::Game::Mm9Hireling;
using OpenYAMM::Game::Mm9HirelingAction;
using OpenYAMM::Game::Mm9HirelingActionKind;
using OpenYAMM::Game::Mm9HirelingKind;
using OpenYAMM::Game::Mm9HirelingSpell;
using OpenYAMM::Game::Party;
using OpenYAMM::Game::PartyBuffId;
using OpenYAMM::Game::SkillMastery;

// Hrolf Spearmaster: a melee retainer with the Arrow as his attack 2.
Mm9Hireling meleeRow()
{
    Mm9Hireling row;
    row.rudeId = 42;
    row.name = "Hrolf Spearmaster";
    row.kind = Mm9HirelingKind::Paid;
    row.level = 34;
    row.hitPoints = 276;
    row.armorClass = 21;
    row.recoverySeconds = 2.31f;
    row.attack1 = {true, CombatDamageType::Physical, {2, 9, 17}, ""};
    row.attack2 = {true, CombatDamageType::Physical, {5, 3, 10}, "Arrow"};
    row.resistances.fire = 10;
    row.resistances.body = 15;
    return row;
}

// Beagan A'Ghrie: melee only.
Mm9Hireling meleeOnlyRow()
{
    Mm9Hireling row = meleeRow();
    row.rudeId = 125;
    row.name = "Beagan A'Ghrie";
    row.attack2 = {};
    return row;
}

// Arienh A'Klindor: the caster, Fireball 60 % of her casts, Toxic Cloud the rest.
Mm9Hireling casterRow()
{
    Mm9Hireling row;
    row.rudeId = 44;
    row.name = "Arienh A'Klindor";
    row.kind = Mm9HirelingKind::Paid;
    row.level = 20;
    row.hitPoints = 120;
    row.armorClass = 14;
    row.recoverySeconds = 2.475f;
    row.attack1 = {true, CombatDamageType::Physical, {2, 4, 8}, ""};
    row.spells = {Mm9HirelingSpell{"fireball", SkillMastery::Expert, 6},
        Mm9HirelingSpell{"toxic cloud", SkillMastery::Master, 7}};
    row.spell1SharePercent = 60;
    return row;
}

Party makeParty(size_t memberCount)
{
    OpenYAMM::Game::PartySeed seed = {};

    for (size_t memberIndex = 0; memberIndex < memberCount; ++memberIndex)
    {
        Character member = {};
        member.name = "Member " + std::to_string(memberIndex + 1);
        member.maxHealth = 100;
        member.health = 100;
        member.might = 15;
        member.speed = 15;
        member.luck = 15;
        member.endurance = 15;
        seed.members.push_back(member);
    }

    Party party = {};
    party.seed(seed);
    return party;
}

const OpenYAMM::Tests::RegressionGameData &requireRegressionGameData()
{
    REQUIRE_MESSAGE(
        OpenYAMM::Tests::regressionGameDataLoaded(),
        OpenYAMM::Tests::regressionGameDataFailure().c_str());
    return OpenYAMM::Tests::regressionGameData();
}
}

TEST_CASE("MM9 hirelings are combatants after the members, never members")
{
    Party party = makeParty(4);
    CHECK_EQ(party.combatantCount(), 4u);
    REQUIRE(party.addHireling(meleeRow()));

    CHECK_EQ(party.members().size(), 4u);
    CHECK_EQ(party.combatantCount(), 5u);
    CHECK(party.member(4) == nullptr);
    REQUIRE(party.combatant(4) != nullptr);
    CHECK_EQ(party.combatant(4)->name, "Hrolf Spearmaster");
    CHECK(party.isHirelingCombatant(4));
    CHECK_FALSE(party.isHirelingCombatant(3));
    CHECK(party.hirelingCombatant(4) == party.findHireling(42));
    CHECK(party.combatant(5) == nullptr);
    // The shared formulas read neutral stats, so derived values are the row's alone.
    CHECK_EQ(party.combatant(4)->speed, Party::Mm9HirelingPrimaryStat);
    CHECK_EQ(OpenYAMM::Game::GameMechanics::primaryStatBonus(int(Party::Mm9HirelingPrimaryStat)), 0);
}

TEST_CASE("monster damage knocks an MM9 hireling out, never kills it, and any heal wakes it")
{
    Party party = makeParty(2);
    REQUIRE(party.addHireling(meleeRow()));
    const size_t hireling = 2;

    CHECK(party.applyDamageToMember(hireling, 100, ""));
    CHECK_EQ(party.combatant(hireling)->health, 176);
    CHECK(OpenYAMM::Game::GameMechanics::canAct(*party.combatant(hireling)));

    // Far past zero: Unconscious at 0 HP, never Dead and never below 0 (MM9_HIRELINGS.md 9.3).
    CHECK(party.applyDamageToMember(hireling, 5000, ""));
    const Character &knockedOut = *party.combatant(hireling);
    CHECK_EQ(knockedOut.health, 0);
    CHECK(knockedOut.conditions.test(size_t(CharacterCondition::Unconscious)));
    CHECK_FALSE(knockedOut.conditions.test(size_t(CharacterCondition::Dead)));
    CHECK_FALSE(OpenYAMM::Game::GameMechanics::canAct(knockedOut));
    CHECK_FALSE(party.applyDamageToMember(hireling, 10, "", true));
    // The members are untouched.
    CHECK_EQ(party.member(0)->health, 100);

    CHECK(party.healMember(hireling, 1));
    CHECK_EQ(party.combatant(hireling)->health, 1);
    CHECK_FALSE(party.combatant(hireling)->conditions.test(size_t(CharacterCondition::Unconscious)));
    CHECK(party.healMember(hireling, 1000));
    CHECK_EQ(party.combatant(hireling)->health, 276);

    // Dead set by an effect stays: no heal lifts it, a revival does.
    CHECK(party.applyMemberCondition(hireling, CharacterCondition::Dead));
    CHECK_FALSE(party.healMember(hireling, 50));
    CHECK(party.combatant(hireling)->conditions.test(size_t(CharacterCondition::Dead)));
    CHECK(party.reviveMember(hireling, 20, false));
    CHECK_FALSE(party.combatant(hireling)->conditions.test(size_t(CharacterCondition::Dead)));
    CHECK_EQ(party.combatant(hireling)->health, 20);

    // A rest wakes a knocked-out hireling and fills its HP.
    party.applyDamageToMember(hireling, 5000, "");
    party.restAndHealAll();
    CHECK_EQ(party.combatant(hireling)->health, 276);
    CHECK_FALSE(party.combatant(hireling)->conditions.test(size_t(CharacterCondition::Unconscious)));
}

TEST_CASE("an MM9 hireling's armour and resistances are its row's, with the party's buffs on top")
{
    Party party = makeParty(2);
    REQUIRE(party.addHireling(meleeRow()));
    const Character &hireling = *party.combatant(2);

    const auto armorClass = [&hireling]()
    {
        // As the monster hit check reads it (GameplayCombatController incomingAttackArmorClass).
        const OpenYAMM::Game::CharacterSheetSummary summary =
            OpenYAMM::Game::GameMechanics::buildCharacterSheetSummary(hireling, nullptr, nullptr, nullptr);
        return summary.armorClass.actual + hireling.armorClassModifier;
    };
    CHECK_EQ(armorClass(), 21);
    const OpenYAMM::Game::CharacterSheetSummary summary =
        OpenYAMM::Game::GameMechanics::buildCharacterSheetSummary(hireling, nullptr, nullptr, nullptr);
    CHECK_EQ(summary.fireResistance.actual, 10);
    CHECK_EQ(summary.bodyResistance.actual, 15);

    party.applyPartyBuff(PartyBuffId::Stoneskin, 600.0f, 8, 0, 4, SkillMastery::Expert, 0);
    party.applyPartyBuff(PartyBuffId::FireResistance, 600.0f, 12, 0, 4, SkillMastery::Expert, 0);
    CHECK_EQ(armorClass(), 29);
    CHECK_EQ(OpenYAMM::Game::GameMechanics::buildCharacterSheetSummary(hireling, nullptr, nullptr, nullptr)
                 .fireResistance.actual,
        22);
}

TEST_CASE("an MM9 hireling takes no armour or resistance from the party's stat buffs")
{
    Party party = makeParty(2);
    REQUIRE(party.addHireling(meleeRow()));
    const Character &hireling = *party.combatant(2);
    // Day of the Gods raises the members' speed and so their armour class; a hireling has no primary stats.
    party.applyPartyBuff(PartyBuffId::DayOfGods, 600.0f, 20, 0, 4, SkillMastery::Expert, 0);
    const OpenYAMM::Game::CharacterSheetSummary summary =
        OpenYAMM::Game::GameMechanics::buildCharacterSheetSummary(hireling, nullptr, nullptr, nullptr);
    CHECK_EQ(summary.armorClass.actual + hireling.armorClassModifier, 21);
    CHECK_EQ(summary.speed.actual, int(Party::Mm9HirelingPrimaryStat));
    CHECK_EQ(summary.fireResistance.actual, 10);
    CHECK_EQ(summary.airResistance.actual, 0);
    CHECK_GT(party.member(0)->magicalBonuses.speed, 0);
}

TEST_CASE("party and personal buffs reach MM9 hirelings; experience does not")
{
    Party party = makeParty(2);
    REQUIRE(party.addHireling(meleeRow()));
    const size_t hirelingIndex = 2;
    const Character &hireling = *party.combatant(hirelingIndex);
    const float baseRecovery = Party::hirelingRecoverySeconds(hireling, 2.31f);
    CHECK(baseRecovery == doctest::Approx(2.31f));

    party.applyPartyBuff(PartyBuffId::Heroism, 600.0f, 7, 0, 4, SkillMastery::Expert, 0);
    party.applyPartyBuff(PartyBuffId::Haste, 600.0f, 0, 0, 4, SkillMastery::Expert, 0);
    CHECK_EQ(hireling.magicalBonuses.meleeDamage, 7);
    CHECK_EQ(party.member(0)->magicalBonuses.meleeDamage, 7);
    CHECK_EQ(hireling.attackRecoveryReductionTicks, 25);
    CHECK(Party::hirelingRecoverySeconds(hireling, 2.31f) < baseRecovery);

    // A personal buff on the hireling alone, through the combatant index (a spell's character target).
    party.applyCharacterBuff(hirelingIndex, CharacterBuffId::Bless, 60.0f, 5, 0, 5, SkillMastery::Normal, 0);
    CHECK(party.characterBuff(hirelingIndex, CharacterBuffId::Bless) != nullptr);
    CHECK(party.characterBuff(0, CharacterBuffId::Bless) == nullptr);
    CHECK_EQ(hireling.magicalBonuses.meleeAttack, 5);
    party.advanceTimedStates(61.0f);
    CHECK(party.characterBuff(hirelingIndex, CharacterBuffId::Bless) == nullptr);
    CHECK_EQ(hireling.magicalBonuses.meleeAttack, 0);

    // Damage on the whole party reaches the hireling; experience is shared among the members only.
    CHECK(party.applyDamageToAllLivingMembers(10, ""));
    CHECK_EQ(hireling.health, 266);
    CHECK_EQ(party.member(1)->health, 90);
    party.grantSharedExperience(1000);
    CHECK_EQ(hireling.experience, 0u);
    CHECK(party.member(0)->experience > 0u);
}

TEST_CASE("the active-member rotation runs over the members, then the MM9 hirelings")
{
    Party party = makeParty(2);
    REQUIRE(party.addHireling(meleeRow()));
    REQUIRE(party.addHireling(casterRow()));
    CHECK_EQ(party.activeCombatantIndex(), 0u);

    REQUIRE(party.switchToNextReadyMember());
    CHECK_EQ(party.activeCombatantIndex(), 1u);
    REQUIRE(party.switchToNextReadyMember());
    CHECK_EQ(party.activeCombatantIndex(), 2u);
    REQUIRE(party.activeHireling() != nullptr);
    CHECK_EQ(party.activeHireling()->rudeId, 42u);
    // The character screens keep the last active member.
    CHECK_EQ(party.activeMemberIndex(), 1u);
    CHECK_EQ(party.activeMember()->name, "Member 2");

    // A recovering or knocked-out hireling is passed over.
    party.applyRecoveryToMember(3, 5.0f);
    REQUIRE(party.switchToNextReadyMember());
    CHECK_EQ(party.activeCombatantIndex(), 0u);
    CHECK(party.activeHireling() == nullptr);
    party.updateRecovery(6.0f);
    party.applyDamageToMember(2, 5000, "");
    party.setActiveCombatantIndex(1);
    REQUIRE(party.switchToNextReadyMember());
    CHECK_EQ(party.activeCombatantIndex(), 3u);

    // Choosing a member's portrait leaves the hirelings' turn.
    CHECK(party.setActiveMemberIndex(0));
    CHECK(party.activeHireling() == nullptr);

    // Removing the active hireling hands the turn back to the members.
    party.setActiveCombatantIndex(3);
    CHECK(party.removeHireling(44));
    CHECK(party.activeHireling() == nullptr);
    CHECK_EQ(party.activeCombatantIndex(), 0u);
}

TEST_CASE("an MM9 hireling's recovery is its row's, and haste shortens it")
{
    Party party = makeParty(1);
    REQUIRE(party.addHireling(meleeRow()));
    Character &hireling = *party.combatant(1);
    CHECK(Party::hirelingRecoverySeconds(hireling, 2.31f) == doctest::Approx(2.31f));
    // Never below a blow's minimum.
    CHECK(Party::hirelingRecoverySeconds(hireling, 0.01f) > 0.0f);

    party.applyRecoveryToMember(1, 2.31f);
    CHECK_FALSE(OpenYAMM::Game::GameMechanics::canTakeGameplayAction(hireling));
    party.updateRecovery(1.0f);
    CHECK(hireling.recoverySecondsRemaining == doctest::Approx(1.31f));
    party.updateRecovery(2.0f);
    CHECK(OpenYAMM::Game::GameMechanics::canTakeGameplayAction(hireling));
}

TEST_CASE("an MM9 hireling attacks in reach with attack 1, beyond it with attack 2, and casters always cast")
{
    const Mm9Hireling melee = meleeRow();
    Mm9HirelingAction action = OpenYAMM::Game::chooseMm9HirelingAction(melee, true, true, 50);
    CHECK(action.kind == Mm9HirelingActionKind::Melee);
    CHECK(action.pAttack == &melee.attack1);
    action = OpenYAMM::Game::chooseMm9HirelingAction(melee, true, false, 50);
    CHECK(action.kind == Mm9HirelingActionKind::Ranged);
    CHECK(action.pAttack == &melee.attack2);
    // An unaimed attack does nothing.
    CHECK(OpenYAMM::Game::chooseMm9HirelingAction(melee, false, false, 50).kind == Mm9HirelingActionKind::None);

    const Mm9Hireling meleeOnly = meleeOnlyRow();
    CHECK(OpenYAMM::Game::chooseMm9HirelingAction(meleeOnly, true, true, 50).kind == Mm9HirelingActionKind::Melee);
    CHECK(OpenYAMM::Game::chooseMm9HirelingAction(meleeOnly, true, false, 50).kind == Mm9HirelingActionKind::None);

    // Turn-based, the command swings attack 1 at the air rather than leaving the turn unspent.
    action = OpenYAMM::Game::chooseMm9HirelingAction(melee, false, false, 50, true);
    CHECK(action.kind == Mm9HirelingActionKind::Melee);
    CHECK(action.pAttack == &melee.attack1);
    CHECK(OpenYAMM::Game::chooseMm9HirelingAction(meleeOnly, true, false, 50, true).kind
        == Mm9HirelingActionKind::Melee);
    CHECK(OpenYAMM::Game::chooseMm9HirelingAction(melee, true, false, 50, true).kind == Mm9HirelingActionKind::Ranged);

    // The first spell up to spell1_share_percent, then the second; in reach or not, aimed or not.
    const Mm9Hireling caster = casterRow();
    action = OpenYAMM::Game::chooseMm9HirelingAction(caster, true, true, 60);
    CHECK(action.kind == Mm9HirelingActionKind::Spell);
    REQUIRE(action.pSpell != nullptr);
    CHECK_EQ(action.pSpell->name, "fireball");
    action = OpenYAMM::Game::chooseMm9HirelingAction(caster, false, false, 61);
    CHECK(action.kind == Mm9HirelingActionKind::Spell);
    REQUIRE(action.pSpell != nullptr);
    CHECK_EQ(action.pSpell->name, "toxic cloud");
    CHECK(action.pSpell->mastery == SkillMastery::Master);
}

TEST_CASE("an MM9 hireling rolls its row's dice with the party's damage buffs")
{
    Party party = makeParty(1);
    REQUIRE(party.addHireling(meleeRow()));
    const Mm9Hireling row = meleeRow();
    std::mt19937 rng(1234);

    for (int roll = 0; roll < 200; ++roll)
    {
        const int damage = OpenYAMM::Game::rollMm9HirelingAttackDamage(row.attack1, *party.combatant(1), true, rng);
        CHECK(damage >= 2 + 17);
        CHECK(damage <= 18 + 17);
    }

    party.applyPartyBuff(PartyBuffId::Heroism, 600.0f, 10, 0, 4, SkillMastery::Expert, 0);
    const int buffed = OpenYAMM::Game::rollMm9HirelingAttackDamage(row.attack1, *party.combatant(1), true, rng);
    CHECK(buffed >= 2 + 17 + 10);

    // The monster hit roll at the hireling's level: level 34 lands on a low armour class most of the time.
    int hits = 0;

    for (int roll = 0; roll < 1000; ++roll)
    {
        hits += OpenYAMM::Game::mm9HirelingAttackHits(*party.combatant(1), true, 5, rng) ? 1 : 0;
    }

    CHECK(hits > 800);
}

TEST_CASE("a hireling caster casts its row's spell at its skill and mastery, without mana")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    REQUIRE(party.addHireling(casterRow()));
    const size_t casterIndex = party.members().size();
    OpenYAMM::Tests::PartySpellTestWorldRuntime worldRuntime = {};
    worldRuntime.bindParty(&party);
    OpenYAMM::Game::GameplayRuntimeActorState actor = {};
    actor.preciseX = 1024.0f;
    actor.height = 160;
    actor.radius = 48;
    actor.hostileToParty = true;
    actor.hasDetectedParty = true;
    const size_t targetActorIndex = worldRuntime.addActor(actor);
    const OpenYAMM::Game::SpellEntry *pFireball = gameData.spellTable.findByName("fireball");
    REQUIRE(pFireball != nullptr);

    OpenYAMM::Game::PartySpellCastRequest request = {};
    request.casterMemberIndex = casterIndex;
    request.spellId = uint32_t(pFireball->id);
    request.quickCast = true;
    request.targetActorIndex = targetActorIndex;
    request.skillLevelOverride = 6;
    request.skillMasteryOverride = SkillMastery::Expert;
    request.bypassRequiredMastery = true;
    request.spendMana = false;
    request.applyRecovery = false;
    const OpenYAMM::Game::PartySpellCastResult result =
        OpenYAMM::Game::PartySpellSystem::castSpell(party, worldRuntime, gameData.spellTable, request);

    CHECK(result.status == OpenYAMM::Game::PartySpellCastStatus::Succeeded);
    REQUIRE_EQ(worldRuntime.projectileRequests().size(), 1u);
    CHECK_EQ(worldRuntime.projectileRequests()[0].casterMemberIndex, uint32_t(casterIndex));
    CHECK_EQ(worldRuntime.projectileRequests()[0].skillLevel, 6u);
    CHECK(worldRuntime.projectileRequests()[0].skillMastery == SkillMastery::Expert);
    CHECK(worldRuntime.projectileRequests()[0].damage > 0);
    CHECK_EQ(party.combatant(casterIndex)->spellPoints, 0);
}

TEST_CASE("party heals and party-wide buffs reach MM9 hirelings; a heal on a hireling wakes it")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = requireRegressionGameData();
    Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    REQUIRE(party.addHireling(meleeRow()));
    const size_t hirelingIndex = party.members().size();
    OpenYAMM::Tests::PartySpellTestWorldRuntime worldRuntime = {};
    worldRuntime.bindParty(&party);
    Character *pCaster = party.member(0);
    REQUIRE(pCaster != nullptr);
    pCaster->skills["BodyMagic"] = {"BodyMagic", 10, SkillMastery::Grandmaster};
    pCaster->skills["SpiritMagic"] = {"SpiritMagic", 10, SkillMastery::Expert};
    pCaster->maxSpellPoints = 500;
    pCaster->spellPoints = 500;
    party.applyDamageToMember(hirelingIndex, 5000, "");
    REQUIRE(party.combatant(hirelingIndex)->conditions.test(size_t(CharacterCondition::Unconscious)));

    OpenYAMM::Game::PartySpellCastRequest request = {};
    request.casterMemberIndex = 0;
    request.spellId = OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::PowerCure);
    OpenYAMM::Game::PartySpellCastResult result =
        OpenYAMM::Game::PartySpellSystem::castSpell(party, worldRuntime, gameData.spellTable, request);
    CHECK(result.status == OpenYAMM::Game::PartySpellCastStatus::Succeeded);
    CHECK(party.combatant(hirelingIndex)->health > 0);
    CHECK_FALSE(party.combatant(hirelingIndex)->conditions.test(size_t(CharacterCondition::Unconscious)));

    // Bless at Expert covers the party, the hireling too.
    party.updateRecovery(30.0f);
    request = {};
    request.casterMemberIndex = 0;
    request.spellId = OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::Bless);
    result = OpenYAMM::Game::PartySpellSystem::castSpell(party, worldRuntime, gameData.spellTable, request);
    CHECK(result.status == OpenYAMM::Game::PartySpellCastStatus::Succeeded);
    CHECK(party.characterBuff(hirelingIndex, CharacterBuffId::Bless) != nullptr);

    // Heal aimed at the hireling (a character target by combatant index).
    party.applyDamageToMember(hirelingIndex, 5000, "");
    party.updateRecovery(30.0f);
    request = {};
    request.casterMemberIndex = 0;
    request.spellId = OpenYAMM::Game::spellIdValue(OpenYAMM::Game::SpellId::Heal);
    request.targetCharacterIndex = hirelingIndex;
    result = OpenYAMM::Game::PartySpellSystem::castSpell(party, worldRuntime, gameData.spellTable, request);
    CHECK(result.status == OpenYAMM::Game::PartySpellCastStatus::Succeeded);
    CHECK(party.combatant(hirelingIndex)->health > 0);
    CHECK_FALSE(party.combatant(hirelingIndex)->conditions.test(size_t(CharacterCondition::Unconscious)));
}

TEST_CASE("MM9 formation: members and hirelings take the lowest free cell")
{
    Party party = makeParty(4);
    CHECK_EQ(party.formationCell(0), 0);
    CHECK_EQ(party.formationCell(1), 1);
    CHECK_EQ(party.formationCell(2), 2);
    CHECK_EQ(party.formationCell(3), 3);
    REQUIRE(party.addHireling(meleeRow()));
    REQUIRE(party.addHireling(casterRow()));
    CHECK_EQ(party.formationCell(4), 4);
    CHECK_EQ(party.formationCell(5), 5);

    // Five members: the front rank, then middle left and middle centre; the hireling joins at middle right.
    Party five = makeParty(5);
    CHECK_EQ(five.formationCell(3), 3);
    CHECK_EQ(five.formationCell(4), 4);
    REQUIRE(five.addHireling(meleeRow()));
    CHECK_EQ(five.formationCell(5), 5);

    // One member per cell; a freed cell is the next joiner's.
    CHECK_FALSE(party.setFormationCell(4, 0));
    CHECK(party.setFormationCell(4, 8));
    CHECK_EQ(party.formationCell(4), 8);
    CHECK(party.removeHireling(44));
    REQUIRE(party.addHireling(casterRow()));
    CHECK_EQ(party.formationCell(5), 4);

    // The cells survive a snapshot.
    Party restored = {};
    restored.restoreSnapshot(party.snapshot());
    CHECK_EQ(restored.formationCell(0), 0);
    CHECK_EQ(restored.formationCell(4), 8);
    CHECK_EQ(restored.formationCell(5), 4);
}

TEST_CASE("MM9 formation targeting strikes the front rank 70 %, the middle 20 %, the rear 10 %")
{
    Party party = makeParty(4);
    REQUIRE(party.addHireling(meleeRow()));
    // Front: members 0-2; middle: member 3; rear: the hireling.
    REQUIRE(party.setFormationCell(4, 7));
    party.setFormationTargetingActive(true);

    std::array<int, 5> picks = {};
    constexpr int Trials = 20000;

    for (int trial = 0; trial < Trials; ++trial)
    {
        const std::optional<size_t> target = party.chooseMonsterAttackTarget(0, uint32_t(trial) * 7919u + 3u);
        REQUIRE(target.has_value());
        ++picks[*target];
    }

    const auto share = [](int count)
    {
        return double(count) / double(Trials);
    };
    CHECK(share(picks[0] + picks[1] + picks[2]) == doctest::Approx(0.70).epsilon(0.05));
    CHECK(share(picks[3]) == doctest::Approx(0.20).epsilon(0.1));
    CHECK(share(picks[4]) == doctest::Approx(0.10).epsilon(0.15));

    // A knocked-out front member is passed over: the rank's share goes to the others in it.
    party.applyDamageToMember(0, 5000, "");
    party.applyMemberCondition(0, CharacterCondition::Unconscious);

    for (int trial = 0; trial < 200; ++trial)
    {
        const std::optional<size_t> target = party.chooseMonsterAttackTarget(0, uint32_t(trial));
        REQUIRE(target.has_value());
        CHECK_NE(*target, 0u);
    }

    // Once every member is down nobody is chosen, the hireling standing or not (MM9 9.3).
    for (size_t memberIndex = 1; memberIndex < 4; ++memberIndex)
    {
        party.applyDamageToMember(memberIndex, 5000, "");
        party.applyMemberCondition(memberIndex, CharacterCondition::Unconscious);
    }

    CHECK_FALSE(party.chooseMonsterAttackTarget(0, 17u).has_value());
}

TEST_CASE("MM6-MM8 monster targeting is unchanged without formation targeting")
{
    Party plain = makeParty(4);
    Party withCells = makeParty(4);
    REQUIRE(withCells.addHireling(meleeRow()));
    CHECK_FALSE(withCells.formationTargetingActive());

    for (uint32_t trial = 0; trial < 500; ++trial)
    {
        const std::optional<size_t> left = plain.chooseMonsterAttackTarget(0, trial * 31u);
        const std::optional<size_t> right = withCells.chooseMonsterAttackTarget(0, trial * 31u);
        REQUIRE(left.has_value());
        REQUIRE(right.has_value());
        // The members only, exactly as without a hireling.
        CHECK_EQ(*left, *right);
    }
}

TEST_CASE("turn-based combat queues MM9 hirelings after the members and waits for their command")
{
    Party party = makeParty(2);
    REQUIRE(party.addHireling(meleeRow()));
    OpenYAMM::Game::TurnBasedCombatRuntime runtime = {};
    REQUIRE(runtime.begin(party, nullptr));

    std::vector<size_t> characters;

    for (const OpenYAMM::Game::TurnBasedCombatRuntime::QueueEntry &entry : runtime.queue())
    {
        if (entry.kind == OpenYAMM::Game::TurnBasedCombatRuntime::QueueEntry::Kind::Character)
        {
            characters.push_back(entry.id);
        }
    }

    CHECK_EQ(characters, std::vector<size_t>{0, 1, 2});
    runtime.update(&party, nullptr, 0.6f);
    REQUIRE(runtime.canBeginPlayerAction(party));
    CHECK_EQ(party.activeCombatantIndex(), 0u);
    REQUIRE(runtime.applyPlayerAction(party, 0, 2.0f));
    REQUIRE(runtime.canBeginPlayerAction(party));
    CHECK_EQ(party.activeCombatantIndex(), 1u);
    REQUIRE(runtime.applyPlayerAction(party, 1, 2.0f));
    REQUIRE(runtime.canBeginPlayerAction(party));
    CHECK_EQ(party.activeCombatantIndex(), 2u);
    CHECK(party.activeHireling() != nullptr);
    runtime.storeMemberTurnRecovery(2, 2.31f);
    CHECK(runtime.applyPlayerAction(party, 2, 2.31f));
}

TEST_CASE("automatic heals and upkeep buffs reach MM9 hirelings (OY-583, OY-487)")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    Party party = makeParty(2);
    REQUIRE(party.addHireling(meleeRow()));
    const size_t hirelingIndex = 2;
    Character *pCleric = party.member(0);
    REQUIRE(pCleric != nullptr);
    pCleric->skills["BodyMagic"] = OpenYAMM::Game::CharacterSkill{"BodyMagic", 10, SkillMastery::Expert};
    pCleric->skills["SpiritMagic"] = OpenYAMM::Game::CharacterSkill{"SpiritMagic", 10, SkillMastery::Expert};
    pCleric->spellPoints = 100;
    const uint32_t heal = uint32_t(OpenYAMM::Game::SpellId::Heal);
    const uint32_t bless = uint32_t(OpenYAMM::Game::SpellId::Bless);

    // The members are whole and the hireling is wounded: a quick-cast Heal goes to the hireling.
    party.combatant(hirelingIndex)->health = 100;
    CHECK(OpenYAMM::Game::PartySpellSystem::quickCastCharacterTarget(party, 0, heal, &gameData.spellTable)
        == std::optional<size_t>(hirelingIndex));

    // Bless is a buff an attack order waits for: due while someone lacks it, the hireling included.
    CHECK(OpenYAMM::Game::PartySpellSystem::isUpkeepBuffSpell(bless));
    CHECK_FALSE(OpenYAMM::Game::PartySpellSystem::isUpkeepBuffSpell(heal));
    party.applyCharacterBuff(0, CharacterBuffId::Bless, 600.0f, 5, 0, 5, SkillMastery::Expert, 0);
    party.applyCharacterBuff(1, CharacterBuffId::Bless, 600.0f, 5, 0, 5, SkillMastery::Expert, 0);
    const std::optional<OpenYAMM::Game::PartySpellSystem::UpkeepNeed> need =
        OpenYAMM::Game::PartySpellSystem::upkeepNeed(party, 0, bless, &gameData.spellTable, std::nullopt);
    REQUIRE(need.has_value());
    CHECK(need->targetCharacterIndex == std::optional<size_t>(hirelingIndex));

    party.applyCharacterBuff(hirelingIndex, CharacterBuffId::Bless, 600.0f, 5, 0, 5, SkillMastery::Expert, 0);
    CHECK_FALSE(OpenYAMM::Game::PartySpellSystem::upkeepNeed(party, 0, bless, &gameData.spellTable, std::nullopt)
        .has_value());
}

TEST_CASE("an older save's party in the default formation stands by health, an arranged one keeps its cells")
{
    Party party = makeParty(5);
    const std::array<int, 5> maximumHealth = {60, 140, 90, 200, 75};

    for (size_t memberIndex = 0; memberIndex < 5; ++memberIndex)
    {
        party.member(memberIndex)->maxHealth = maximumHealth[memberIndex];
    }

    REQUIRE(party.addHireling(meleeRow()));
    CHECK_EQ(party.formationCell(5), 5);
    party.arrangeDefaultFormationByHealth();
    // Front rank (cells 0-2): 200, 140, 90; middle: 75, 60. The hireling keeps its cell.
    CHECK_EQ(party.formationCell(3), 0);
    CHECK_EQ(party.formationCell(1), 1);
    CHECK_EQ(party.formationCell(2), 2);
    CHECK_EQ(party.formationCell(4), 3);
    CHECK_EQ(party.formationCell(0), 4);
    CHECK_EQ(party.formationCell(5), 5);

    // A formation the player arranged stays as it is.
    Party arranged = makeParty(3);
    arranged.member(2)->maxHealth = 500;
    REQUIRE(arranged.setFormationCell(0, 6));
    arranged.arrangeDefaultFormationByHealth();
    CHECK_EQ(arranged.formationCell(0), 6);
    CHECK_EQ(arranged.formationCell(2), 2);
}
