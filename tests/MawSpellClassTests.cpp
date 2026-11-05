#include "doctest/doctest.h"
#include "engine/TextTable.h"
#include "game/content/ContentTableComposer.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayActorService.h"
#include "game/gameplay/GameplayCombatController.h"
#include "game/gameplay/TurnBasedCombatRuntime.h"
#include "game/party/EventSpellBuffs.h"
#include "game/party/Party.h"
#include "game/party/PartySpellSystem.h"
#include "game/party/SpellIds.h"
#include "game/rules/GameRules.h"
#include "game/rules/MonsterRules.h"
#include "game/rules/maw/MawAuras.h"
#include "game/rules/maw/MawCharacterSheet.h"
#include "game/rules/maw/MawClassRules.h"
#include "game/rules/maw/MawCombatFormulas.h"
#include "game/rules/maw/MawCombatRules.h"
#include "game/rules/maw/MawItemData.h"
#include "game/rules/maw/MawMonsterInspect.h"
#include "game/rules/maw/MawRules.h"
#include "game/rules/maw/MawSpellFormulas.h"
#include "game/tables/CharacterDollTable.h"
#include "game/tables/ClassMultiplierTable.h"
#include "game/tables/ItemTable.h"
#include "game/tables/SpellTable.h"
#include "tests/PartySpellTestHarness.h"
#include "tests/RegressionGameData.h"

#include <array>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <memory>
#include <optional>
#include <random>
#include <set>
#include <string>
#include <unordered_map>
#include <vector>

using namespace OpenYAMM::Game;

// devdocs/maw/GAPS.md §5 (spells and auras) and §6 (classes, races, creation).
namespace
{
MawItemData installedItemData()
{
    std::ifstream input(std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/rulesets/maw/data/items.yml");
    const std::string text((std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());
    MawItemData data;
    std::string error;
    REQUIRE_MESSAGE(data.loadFromYaml(text, error), error);
    return data;
}

Character member(const std::string &name, const std::string &className, uint32_t level)
{
    Character character;
    character.name = name;
    character.className = className;
    character.level = level;
    return character;
}

// An Assassin with Assassination 10 at Master and Sword 10 holding the Archangel Broadsword.
Character assassinWithSword()
{
    Character assassin = member("Ariel", "Assassin", 20);
    assassin.skills["EarthMagic"] = {"EarthMagic", 10, SkillMastery::Master};
    assassin.skills["Sword"] = {"Sword", 10, SkillMastery::Expert};
    assassin.equipment.mainHand = 15;
    assassin.equipmentRuntime.mainHand.rulesetFields.itemPower = 20;
    return assassin;
}
}

TEST_CASE("MAW Shared Life pools the living members' hit points and shares them evenly (A7.1)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const SpellRules &spells = rules.gameRules().spells;
    Character healthy = member("Ariel", "Knight", 10);
    healthy.maxHealth = 100;
    healthy.health = 100;
    Character wounded = member("Brom", "Cleric", 10);
    wounded.maxHealth = 80;
    wounded.health = 20;
    Character fallen = member("Cedric", "Druid", 10);
    fallen.maxHealth = 50;
    fallen.health = -10;
    fallen.conditions.set(size_t(CharacterCondition::Unconscious));
    Character dead = member("Daria", "Sorcerer", 10);
    dead.maxHealth = 60;
    dead.health = 0;
    dead.conditions.set(size_t(CharacterCondition::Dead));
    PartySeed seed;
    seed.members = {healthy, wounded, fallen, dead};
    Party party;
    party.seed(seed);
    party.setRules(&rules.gameRules());
    party.member(2)->health = -10;

    // 30 + 100 + 20 - 10 = 140 shared as 47, 47 and 46; the unconscious member wakes, the dead one stays out.
    REQUIRE(spells.shareLife(party, 30));
    CHECK_EQ(party.member(0)->health, 47);
    CHECK_EQ(party.member(1)->health, 47);
    CHECK_EQ(party.member(2)->health, 46);
    CHECK_FALSE(party.member(2)->conditions.test(size_t(CharacterCondition::Unconscious)));
    CHECK_EQ(party.member(3)->health, 0);

    // A member whose deficit would take the pool below zero stays out; the full member's overflow goes round.
    party.member(0)->health = 5;
    party.member(1)->health = 75;
    party.member(2)->health = -200;
    party.member(2)->conditions.set(size_t(CharacterCondition::Unconscious));
    REQUIRE(spells.shareLife(party, 100));
    CHECK_EQ(party.member(0)->health, 100);
    CHECK_EQ(party.member(1)->health, 80);
    CHECK_EQ(party.member(2)->health, -200);
    CHECK(party.member(2)->conditions.test(size_t(CharacterCondition::Unconscious)));

    CHECK_FALSE(standardGameRules().spells.shareLife(party, 10));
}

TEST_CASE("MAW aura holders follow their members when one is dismissed (A7.3)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    PartySeed seed;
    seed.members = {member("Ariel", "Knight", 10), member("Brom", "Cleric", 10), member("Cedric", "Druid", 10)};
    Party party;
    party.seed(seed);
    party.setRules(&rules.gameRules());
    rules.state().auraHolders = {{5, 0}, {17, 1}, {38, 2}};
    rules.classRuntime(*party.member(2)).comboPoints = 3;

    REQUIRE(party.dismissMemberToAdventurersInn(1));
    REQUIRE_EQ(party.members().size(), 2u);
    CHECK_EQ(party.member(1)->name, "Cedric");
    // Brom took Shield along; Cedric keeps Stone Skin and his combo points in his new slot.
    CHECK_EQ(rules.state().auraHolders, std::unordered_map<uint32_t, uint32_t>{{5, 0}, {38, 1}});
    CHECK_EQ(rules.classRuntime(*party.member(1)).comboPoints, 3);
}

TEST_CASE("MAW scroll, pedestal and temple buffs hold fixed auras until the map changes (L5.1)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const SpellRules &spells = rules.gameRules().spells;
    PartySeed seed;
    seed.members = {member("Ariel", "Knight", 10), member("Brom", "Cleric", 10)};
    Party party;
    party.seed(seed);
    party.setRules(&rules.gameRules());
    rules.setCurrentMap("oute3.odm");
    spells.updateAuras(party, 0.5f);

    // A pedestal's Fire Resistance holds at skill 7, Master, level 40 and reserves nobody's mana.
    REQUIRE(tryApplyEventSpellBuffs(party, 3, 10, 3));
    const PartyBuffState *pResistance = party.partyBuff(PartyBuffId::FireResistance);
    REQUIRE(pResistance != nullptr);
    CHECK_EQ(pResistance->power, int(std::round(mawAuraFlat(20, 2, 40, 7))));
    CHECK_EQ(spells.heldBuffText(party, 3), std::optional<std::string>("Blessing of this place"));
    CHECK_EQ(spells.reservedSpellPoints(party, 0), 0);

    // A temple's Bless; a hireling's Heroism is wiped as MAW's aura pass wipes it.
    REQUIRE(spells.castSourceBuff(party, 46, BuffSource::Temple));
    CHECK(party.characterBuff(1, CharacterBuffId::Bless) != nullptr);
    REQUIRE(tryApplyEventSpellBuffs(party, 51, 10, 3, 0.0f, BuffSource::Hireling));
    CHECK(party.partyBuff(PartyBuffId::Heroism) == nullptr);
    // Spells that are no aura stay the engine's.
    CHECK_FALSE(spells.castSourceBuff(party, 21, BuffSource::Scroll));

    // A dungeon ends the temple's blessing and keeps the pedestal's; another outdoor map ends that too.
    rules.setCurrentMap("d01.blv");
    spells.updateAuras(party, 0.5f);
    CHECK(party.characterBuff(1, CharacterBuffId::Bless) == nullptr);
    CHECK(party.partyBuff(PartyBuffId::FireResistance) != nullptr);
    rules.setCurrentMap("oute3.odm");
    spells.updateAuras(party, 0.5f);
    CHECK(party.partyBuff(PartyBuffId::FireResistance) != nullptr);
    rules.setCurrentMap("outd3.odm");
    spells.updateAuras(party, 0.5f);
    CHECK(party.partyBuff(PartyBuffId::FireResistance) == nullptr);
    CHECK(rules.state().auraHolders.empty());
    CHECK(rules.state().fixedAuraMaps.empty());

    // A member's own hold is not taken by a scroll, and a member takes a scroll's aura over by casting it.
    REQUIRE(spells.castSourceBuff(party, 3, BuffSource::Scroll));
    REQUIRE(spells.castAura(party, 0, 3) == AuraCastResult::Held);
    CHECK_EQ(rules.state().auraHolders.at(3), 0u);
    CHECK(rules.state().fixedAuraMaps.empty());
    REQUIRE(spells.castSourceBuff(party, 3, BuffSource::Scroll));
    CHECK_EQ(rules.state().auraHolders.at(3), 0u);

    CHECK_FALSE(standardGameRules().spells.castSourceBuff(party, 3, BuffSource::Scroll));
}

TEST_CASE("quick-cast heals go to the endangered, else where they heal the most, in both rulesets (A7.2)")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const auto partyOf = [](std::vector<std::pair<int, int>> pools)
    {
        PartySeed seed;
        seed.members.push_back(member("Healer", "Cleric", 10));

        for (size_t index = 0; index < pools.size(); ++index)
        {
            seed.members.push_back(member("Member" + std::to_string(index), "Knight", 10));
        }

        Party party;
        party.seed(seed);

        for (size_t index = 0; index < pools.size(); ++index)
        {
            Character &target = *party.member(index + 1);
            target.maxHealth = pools[index].second;
            target.health = pools[index].first;
        }

        // Standard's Grandmaster Heal at Body 399 heals 5 + 5 x 399 = 2000.
        party.member(0)->skills["BodyMagic"] = {"BodyMagic", 399, SkillMastery::Grandmaster};
        return party;
    };
    const auto target = [&gameData](const Party &party, uint32_t spellId)
    {
        return PartySpellSystem::quickCastCharacterTarget(party, 0, spellId, &gameData.spellTable);
    };

    // The user's example: 3000 of 20000 is in danger, 500 of 1000 is not.
    Party example = partyOf({{3000, 20000}, {500, 1000}});
    CHECK_EQ(PartySpellSystem::healAmount(example, *example.member(0), gameData.spellTable, 68),
        std::optional<int>(2000));
    CHECK_EQ(target(example, 68), std::optional<size_t>(1));
    // Nobody in danger: 2000 HP do the most for 18000 of 20000, not for 80 of 100.
    Party overheal = partyOf({{18000, 20000}, {80, 100}});
    CHECK_EQ(target(overheal, 68), std::optional<size_t>(1));
    // Several in danger: the lowest share first, however much each would gain.
    Party danger = partyOf({{30, 100}, {1000, 5000}, {10, 20}});
    CHECK_EQ(target(danger, 68), std::optional<size_t>(2));
    // The whole, the dead and the petrified are never healed; nobody to heal, no target.
    Party whole = partyOf({{100, 100}, {0, 50}});
    whole.member(2)->conditions.set(size_t(CharacterCondition::Dead));
    CHECK_FALSE(target(whole, 68));
    // Cures go to a member with the condition, revivals to the dead.
    Party poisoned = partyOf({{10, 100}, {90, 100}});
    poisoned.member(2)->conditions.set(size_t(CharacterCondition::PoisonWeak));
    poisoned.member(0)->skills["BodyMagic"] = {"BodyMagic", 10, SkillMastery::Grandmaster};
    CHECK_EQ(target(poisoned, uint32_t(SpellId::CurePoison)), std::optional<size_t>(2));
    CHECK_EQ(target(whole, uint32_t(SpellId::RaiseDead)), std::optional<size_t>(2));

    // MAW heals by its own table: the same rule with MAW's amount.
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Party mawParty = partyOf({{18000, 20000}, {80, 100}});
    mawParty.setRules(&rules.gameRules());
    mawParty.member(0)->skills["BodyMagic"] = {"BodyMagic", 20, SkillMastery::Grandmaster};
    const std::optional<int> mawHeal =
        PartySpellSystem::healAmount(mawParty, *mawParty.member(0), gameData.spellTable, 68);
    REQUIRE(mawHeal.has_value());
    CHECK_NE(*mawHeal, 105);
    CHECK_EQ(target(mawParty, 68), std::optional<size_t>(1));
}

TEST_CASE("quick-cast heals, cures and revivals pick their member; MAW's healing cures fall back to the condition")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());

    // The heals, cures and revivals on one member pick it; a buff on one member (Bless at Normal) asks.
    for (SpellId spell : {SpellId::Heal, SpellId::CureDisease, SpellId::RemoveCurse, SpellId::RemoveFear,
             SpellId::CureParalysis, SpellId::CureInsanity, SpellId::CureWeakness, SpellId::CurePoison,
             SpellId::RaiseDead, SpellId::Resurrection})
    {
        CHECK(PartySpellSystem::hasQuickCastCharacterTarget(spellIdValue(spell)));
        const std::optional<PartySpellDescriptor> descriptor = PartySpellSystem::describeSpell(spellIdValue(spell));
        REQUIRE(descriptor.has_value());
        CHECK(descriptor->targetKind == PartySpellCastTargetKind::Character);
    }

    CHECK_FALSE(PartySpellSystem::hasQuickCastCharacterTarget(spellIdValue(SpellId::Bless)));
    CHECK_FALSE(PartySpellSystem::hasQuickCastCharacterTarget(spellIdValue(SpellId::Preservation)));

    PartySeed seed;
    seed.members = {member("Healer", "Cleric", 10), member("Ariel", "Knight", 10), member("Brom", "Knight", 10)};
    Party party;
    party.seed(seed);
    party.member(0)->skills["BodyMagic"] = {"BodyMagic", 20, SkillMastery::Grandmaster};
    party.member(0)->skills["SpiritMagic"] = {"SpiritMagic", 20, SkillMastery::Grandmaster};
    // Brom is cursed and diseased at full health; Ariel is whole.
    party.member(2)->conditions.set(size_t(CharacterCondition::Cursed));
    party.member(2)->conditions.set(size_t(CharacterCondition::DiseaseWeak));
    const auto target = [&gameData](const Party &party, SpellId spell)
    {
        return PartySpellSystem::quickCastCharacterTarget(party, 0, spellIdValue(spell), &gameData.spellTable);
    };

    // Standard's Remove Curse and Cure Disease do not heal: they go to the condition.
    CHECK_EQ(target(party, SpellId::RemoveCurse), std::optional<size_t>(2));
    CHECK_EQ(target(party, SpellId::CureDisease), std::optional<size_t>(2));

    // MAW's Greater Heal and Remove Curse heal: nobody wounded, they still cure Brom.
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    party.setRules(&rules.gameRules());
    REQUIRE(PartySpellSystem::healAmount(party, *party.member(0), gameData.spellTable,
        spellIdValue(SpellId::CureDisease)).has_value());
    REQUIRE(PartySpellSystem::healAmount(party, *party.member(0), gameData.spellTable,
        spellIdValue(SpellId::RemoveCurse)).has_value());
    CHECK_EQ(target(party, SpellId::CureDisease), std::optional<size_t>(2));
    CHECK_EQ(target(party, SpellId::RemoveCurse), std::optional<size_t>(2));
    // A wounded member takes the heal first, as A7.2 rules.
    party.member(1)->health = 1;
    CHECK_EQ(target(party, SpellId::CureDisease), std::optional<size_t>(1));
    // Heal cures nothing: with nobody wounded it has no target.
    party.member(1)->health = Party::effectiveMaximumHealth(*party.member(1));
    CHECK_FALSE(target(party, SpellId::Heal));
}

TEST_CASE("MAW auras need no target to quick-cast (A7.4)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const SpellRules &spells = rules.gameRules().spells;
    PartySeed seed;
    seed.members = {member("Ariel", "Knight", 10), member("Brom", "Cleric", 10)};
    Party party;
    party.seed(seed);
    party.setRules(&rules.gameRules());

    // Meditation (56, Telepathy's id) and Bless toggle as auras; a damage spell does not.
    CHECK(spells.castsAsAura(party, 0, 56));
    CHECK(spells.castsAsAura(party, 1, 46));
    CHECK_FALSE(spells.castsAsAura(party, 0, 11));
    CHECK_FALSE(standardGameRules().spells.castsAsAura(party, 0, 56));
}

TEST_CASE("MAW Shrinking Ray takes one more monster near its target per mastery (A7.5)")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    CHECK_EQ(rules.gameRules().spells.spellSplash(92, SkillMastery::Normal).extraTargets, 0u);
    CHECK_EQ(rules.gameRules().spells.spellSplash(92, SkillMastery::Grandmaster).extraTargets, 3u);
    CHECK_EQ(rules.gameRules().spells.spellSplash(11, SkillMastery::Grandmaster).extraTargets, 0u);
    CHECK_EQ(standardGameRules().spells.spellSplash(92, SkillMastery::Grandmaster).extraTargets, 0u);

    Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    party.setRules(&rules.gameRules());
    OpenYAMM::Tests::PartySpellTestWorldRuntime world;
    world.bindParty(&party);
    const auto monster = [](float x, bool hostile)
    {
        GameplayRuntimeActorState actor;
        actor.preciseX = x;
        actor.radius = 48;
        actor.height = 160;
        actor.currentHp = 50;
        actor.maxHp = 50;
        actor.hostileToParty = hostile;
        actor.hasDetectedParty = true;
        return actor;
    };
    const size_t target = world.addActor(monster(1024, true));
    world.addActor(monster(1324, true));
    world.addActor(monster(1124, false));
    world.addActor(monster(1224, true));
    world.addActor(monster(1424, true));
    world.addActor(monster(2048, true));

    Character *pCaster = party.member(0);
    REQUIRE(pCaster != nullptr);
    pCaster->skills["DarkMagic"] = {"DarkMagic", 10, SkillMastery::Master};
    pCaster->maxSpellPoints = 1000;
    pCaster->spellPoints = 1000;
    PartySpellCastRequest request;
    request.casterMemberIndex = 0;
    request.spellId = 92;
    request.targetActorIndex = target;
    const PartySpellCastResult result = PartySpellSystem::castSpell(party, world, gameData.spellTable, request);
    REQUIRE(result.status == PartySpellCastStatus::Succeeded);

    // Master: the target and the two nearest hostile monsters within 512, the peasant passed over.
    std::vector<size_t> struck;

    for (const auto &applied : world.appliedSpellRequests())
    {
        struck.push_back(applied.actorIndex);
    }

    CHECK_EQ(struck, std::vector<size_t>{target, 3, 1});
}

TEST_CASE("MAW Immolation burns as its holder's spell (L5.5)")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    rules.setSpellTable(&gameData.spellTable);
    Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    party.setRules(&rules.gameRules());
    party.member(3)->skills["FireMagic"] = {"FireMagic", 10, SkillMastery::Grandmaster};
    const SpellRules &spells = rules.gameRules().spells;

    CHECK_FALSE(spells.auraDamage(party, 8));
    REQUIRE(spells.castAura(party, 3, 8) == AuraCastResult::Held);
    spells.updateAuras(party, 0.5f);
    const std::optional<int> damage = spells.auraDamage(party, 8);
    REQUIRE(damage.has_value());
    CHECK(*damage > 0);
    CHECK_FALSE(standardGameRules().spells.auraDamage(party, 8));
}

TEST_CASE("MAW staffs resist for the whole party (L5.6)")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    party.setRules(&rules.gameRules());
    const auto armWithStaff = [&](size_t memberIndex, SkillMastery mastery)
    {
        Character &staffHolder = *party.member(memberIndex);
        staffHolder.equipment.mainHand = 81;
        staffHolder.equipmentRuntime.mainHand.rulesetFields.itemPower = 20;
        staffHolder.skills["Staff"] = {"Staff", 10, mastery};
    };

    // A Novice's staff gives nothing; a Master's 3 % of its attack per point of Staff + 10, a Grandmaster's 4 %.
    armWithStaff(1, SkillMastery::Normal);
    CHECK_EQ(mawStaffPartyResistance(rules, *party.member(1), gameData.itemTable), 0);
    armWithStaff(1, SkillMastery::Master);
    armWithStaff(2, SkillMastery::Grandmaster);
    const int master = mawStaffPartyResistance(rules, *party.member(1), gameData.itemTable);
    const int grandmaster = mawStaffPartyResistance(rules, *party.member(2), gameData.itemTable);
    CHECK(master > 0);
    CHECK(grandmaster > master);
    CHECK_EQ(mawStaffPartyResistance(rules, *party.member(0), gameData.itemTable), 0);

    rules.gameRules().spells.updateAuras(party, 0.5f);
    CHECK_EQ(rules.partyStaffResistance(), master + grandmaster);
}

TEST_CASE("MAW dragon rules follow the portrait's race (A6.1, A6.3)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    MawGameState state;
    state.continentLevels[0] = 19;
    rules.setState(state);
    ItemTable items;
    const auto withSkills = [](Character character)
    {
        character.skills["Unarmed"] = {"Unarmed", 20, SkillMastery::Expert};
        character.skills["DragonAbility"] = {"DragonAbility", 20, SkillMastery::Expert};
        character.skills["Dodging"] = {"Dodging", 20, SkillMastery::Grandmaster};
        return character;
    };
    Character dragonKnight = withSkills(member("Ariel", "Knight", 20));
    dragonKnight.raceId = 5;
    Character dragon = withSkills(member("Brom", "Dragon", 20));
    dragon.raceId = 5;
    Character humanDragon = withSkills(member("Cedric", "Dragon", 20));
    CHECK(mawIsDragon(dragonKnight));
    CHECK_FALSE(mawIsDragon(humanDragon));

    // Fangs and breath come with the race, whatever the class.
    const CharacterCombatRows knightRows = mawCombatRows(rules, dragonKnight, items, {13, 0, 0});
    const CharacterCombatRows dragonRows = mawCombatRows(rules, dragon, items, {13, 0, 0});
    CHECK_EQ(knightRows.meleeMinimumDamage, dragonRows.meleeMinimumDamage);
    CHECK_EQ(knightRows.rangedMaximumDamage, dragonRows.rangedMaximumDamage);
    CHECK(mawCombatRows(rules, humanDragon, items, {13, 0, 0}).meleeMinimumDamage
        != dragonRows.meleeMinimumDamage);

    // A dragon's bite has no Unarmed speed bonus and slows by 1.5 % per point of Fangs; its breath starts from 100
    // and slows by Dragon Ability the same way.
    Character bareKnight = member("Daria", "Knight", 20);
    const int bare = mawCharacterAttackDelay(rules, bareKnight, items, CharacterAttackMode::Melee, 0).delay;
    CHECK_EQ(mawCharacterAttackDelay(rules, dragon, items, CharacterAttackMode::Melee, 0).delay,
        int(std::round(bare * 1.3)));
    CHECK(mawCharacterAttackDelay(rules, humanDragon, items, CharacterAttackMode::Melee, 0).delay < bare);
    CHECK_EQ(mawCharacterAttackDelay(rules, dragon, items, CharacterAttackMode::DragonBreath, 0).delay,
        int(std::round(bare * 1.3)));
    // The Shoot tooltip and Ranged Power ask for a bow's delay; a dragon's ranged delay is its breath's.
    CHECK_EQ(mawCharacterAttackDelay(rules, dragon, items, CharacterAttackMode::Bow, 0).delay,
        int(std::round(bare * 1.3)));

    // Scales never dodge, Grandmaster Dodging or not.
    std::mt19937 rng(5);
    MonsterAttackOnCharacter attack;
    attack.pCharacter = &dragon;
    attack.pItemTable = &items;
    attack.monsterLevel = 20;
    attack.armorClass = 0;
    attack.attackBonus = 1000;
    attack.pRng = &rng;
    bool evaded = false;

    for (int roll = 0; roll < 200; ++roll)
    {
        evaded = evaded || rules.gameRules().combat.characterEvades(attack);
    }

    CHECK_FALSE(evaded);
}

TEST_CASE("MAW dragon breath crits, spreads and takes the lowest resistance (A6.2)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    ItemTable items;
    Character dragon = member("Ariel", "Dragon", 20);
    dragon.raceId = 5;
    dragon.skills["DragonAbility"] = {"DragonAbility", 10, SkillMastery::Expert};
    std::mt19937 rng(9);
    CharacterAttackOnMonster context;
    context.pCharacter = &dragon;
    context.pItemTable = &items;
    context.minimumDamage = 100;
    context.maximumDamage = 100;
    context.pRng = &rng;
    int lowest = 1000000;
    int highest = 0;

    for (int roll = 0; roll < 400; ++roll)
    {
        CharacterAttackResult attack;
        attack.mode = CharacterAttackMode::DragonBreath;
        attack.canAttack = true;
        rules.gameRules().combat.resolveCharacterAttack(attack, context);
        CHECK(attack.recoverySeconds > 0);
        lowest = std::min(lowest, attack.damage);
        highest = std::max(highest, attack.damage);
    }

    // 100 x (0.75 + 0.25 U + 0.25 U): 75 to 125 without a crit, more with one.
    CHECK(lowest >= 75);
    CHECK(lowest < 85);
    CHECK(highest > 115);

    // Fire-proof monsters take the breath through their weakest resistance; anyone else's fire is resisted as fire.
    const auto landed = [&](const Character &attacker)
    {
        MonsterDamageHit hit;
        hit.amount = 100;
        hit.type = CombatDamageType::Fire;
        hit.resistance = 200;
        hit.resistances.fire = 200;
        hit.resistances.air = 200;
        hit.resistances.water = 200;
        hit.resistances.earth = 200;
        hit.resistances.spirit = 200;
        hit.resistances.mind = 200;
        hit.resistances.body = 200;
        hit.resistances.light = 200;
        hit.resistances.dark = 200;
        hit.resistances.physical = 0;
        hit.pMissileAttacker = &attacker;
        hit.missileSpellId = 97;
        hit.pRng = &rng;
        return rules.gameRules().combat.damageToMonster(hit);
    };
    CHECK_EQ(landed(dragon), 100);
    CHECK(landed(member("Brom", "Knight", 20)) < 30);
}

TEST_CASE("MAW dragons learn their skills and refill faster out of combat (A6.4, A6.10)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    PartySeed seed;
    Character dragon = member("Ariel", "Dragon", 20);
    dragon.raceId = 5;
    dragon.maxSpellPoints = 200;
    dragon.spellPoints = 0;
    seed.members = {dragon, member("Brom", "Knight", 20)};
    Party party;
    party.seed(seed);
    party.setRules(&rules.gameRules());
    party.member(0)->spellPoints = 0;
    OpenYAMM::Tests::PartySpellTestWorldRuntime world;
    world.bindParty(&party);

    // No enemy near: 2 SP a second times four, doubled again once the pool has not fallen for 20 seconds.
    rules.gameRules().classes.update(party, world, 1.0f);
    CHECK_EQ(party.member(0)->spellPoints, 8);
    CHECK(party.member(0)->findSkill("Unarmed") != nullptr);
    CHECK(party.member(0)->findSkill("Dodging") != nullptr);
    CHECK(party.member(0)->findSkill("DragonAbility") != nullptr);
    CHECK(party.member(1)->findSkill("Unarmed") == nullptr);

    for (int second = 0; second < 20; ++second)
    {
        rules.gameRules().classes.update(party, world, 1.0f);
    }

    const int before = party.member(0)->spellPoints;
    rules.gameRules().classes.update(party, world, 1.0f);
    CHECK_EQ(party.member(0)->spellPoints - before, 16);
}

TEST_CASE("MAW portraits: races, the Troll Death Knight and a second Lich Troll (A6.7)")
{
    const auto readRows = [](const std::string &path)
    {
        std::ifstream input(std::filesystem::path(OPENYAMM_SOURCE_DIR) / path, std::ios::binary);
        const std::string text{std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
        const std::optional<OpenYAMM::Engine::TextTable> table = OpenYAMM::Engine::TextTable::parseTabSeparated(text);
        REQUIRE_MESSAGE(table.has_value(), path);
        std::vector<std::vector<std::string>> rows;

        for (size_t rowIndex = 0; rowIndex < table->getRowCount(); ++rowIndex)
        {
            rows.push_back(table->getRow(rowIndex));
        }

        return rows;
    };
    std::vector<std::vector<std::string>> rows = readRows("assets_dev/engine/data_tables/character_data.txt");
    std::string error;
    REQUIRE_MESSAGE(applyTableCellOverrides(
                        rows, readRows("assets_dev/engine/rulesets/maw/content/character_data_patch.txt"), 0, 0, error),
        error);
    REQUIRE_MESSAGE(
        appendTableRows(rows, readRows("assets_dev/engine/rulesets/maw/content/character_data.append.txt"), 0, 0, error),
        error);
    CharacterDollTable dolls;
    REQUIRE(dolls.loadCharacterRows(rows));

    for (const auto &[id, race] : std::vector<std::pair<uint32_t, int32_t>>{{68, 5}, {69, 5}, {70, 3}, {71, 3}})
    {
        CAPTURE(id);
        REQUIRE(dolls.getCharacter(id) != nullptr);
        CHECK_EQ(dolls.getCharacter(id)->raceId, race);
    }

    const CharacterDollEntry *pTroll = dolls.getCharacter(77);
    REQUIRE(pTroll != nullptr);
    CHECK_EQ(pTroll->raceId, 4);
    CHECK_EQ(pTroll->defaultClassId, 56u);
    CHECK(pTroll->availableAtStart);
    const CharacterDollEntry *pLich = dolls.getCharacter(78);
    REQUIRE(pLich != nullptr);
    CHECK_EQ(pLich->raceId, 6);
    CHECK_EQ(pLich->facePicturesPrefix, "pc41-");
}

TEST_CASE("MAW Invisibility lasts longer and Resurrection only heals the living (A7.8, A7.10)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const SpellRules &spells = rules.gameRules().spells;
    PartySeed soloSeed;
    soloSeed.members = {member("Ariel", "Knight", 10)};
    Party solo;
    solo.seed(soloSeed);
    CHECK(*spells.partyBuffSeconds(solo, 19, 10, SkillMastery::Master, false) == doctest::Approx(25 * 1.5 * 60));
    CHECK(*spells.partyBuffSeconds(solo, 19, 10, SkillMastery::Grandmaster, false) == doctest::Approx(50 * 1.5 * 60));
    CHECK_FALSE(spells.partyBuffSeconds(solo, 19, 10, SkillMastery::Expert, false));
    CHECK_FALSE(spells.partyBuffSeconds(solo, 5, 10, SkillMastery::Grandmaster, false));
    CHECK_FALSE(standardGameRules().spells.partyBuffSeconds(solo, 19, 10, SkillMastery::Grandmaster, false));
    // A solo party's Fly scroll lasts seven hours (A7.12); a cast or a bigger party's scroll keeps the engine's.
    CHECK(*spells.partyBuffSeconds(solo, 21, 5, SkillMastery::Expert, true) == doctest::Approx(7 * 3600));
    CHECK_FALSE(spells.partyBuffSeconds(solo, 21, 5, SkillMastery::Expert, false));

    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    rules.setSpellTable(&gameData.spellTable);
    Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    party.setRules(&rules.gameRules());
    OpenYAMM::Tests::PartySpellTestWorldRuntime world;
    world.bindParty(&party);
    Character &caster = *party.member(1);
    caster.skills["SpiritMagic"] = {"SpiritMagic", 10, SkillMastery::Grandmaster};
    caster.maxSpellPoints = 5000;
    caster.spellPoints = 5000;
    party.member(2)->health = 5;

    PartySpellCastRequest request;
    request.casterMemberIndex = 1;
    request.spellId = 55;
    request.targetCharacterIndex = 2;
    const PartySpellCastResult result = PartySpellSystem::castSpell(party, world, gameData.spellTable, request);
    REQUIRE(result.status == PartySpellCastStatus::Succeeded);
    CHECK_EQ(party.member(2)->health, Party::effectiveMaximumHealth(*party.member(2)));
    CHECK_FALSE(party.member(2)->conditions.test(size_t(CharacterCondition::Weak)));

    // Remove Curse heals as well, but a heal never raises the dead: the target is uncursed and stays dead.
    Character &dead = *party.member(2);
    dead.health = -50;
    dead.conditions.set(size_t(CharacterCondition::Dead));
    dead.conditions.set(size_t(CharacterCondition::Cursed));
    request.spellId = spellIdValue(SpellId::RemoveCurse);
    caster.recoverySecondsRemaining = 0.0f;
    REQUIRE(PartySpellSystem::castSpell(party, world, gameData.spellTable, request).status
        == PartySpellCastStatus::Succeeded);
    CHECK(dead.conditions.test(size_t(CharacterCondition::Dead)));
    CHECK_FALSE(dead.conditions.test(size_t(CharacterCondition::Cursed)));
    CHECK_EQ(dead.health, -50);
}

TEST_CASE("MAW solo parties keep their travel scrolls and see by Wizard Eye and torchlight (A7.12)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const SpellRules &spells = rules.gameRules().spells;
    PartySeed seed;
    seed.members = {member("Ariel", "Knight", 10)};
    Party party;
    party.seed(seed);
    party.setRules(&rules.gameRules());

    CHECK(spells.keepsScroll(party, 31));
    CHECK(spells.keepsScroll(party, 21));
    CHECK_FALSE(spells.keepsScroll(party, 2));
    CHECK_FALSE(standardGameRules().spells.keepsScroll(party, 31));
    spells.updateAuras(party, 0.5f);
    CHECK(party.partyBuff(PartyBuffId::WizardEye) != nullptr);
    REQUIRE(party.partyBuff(PartyBuffId::TorchLight) != nullptr);
    CHECK_EQ(party.partyBuff(PartyBuffId::TorchLight)->power, 3);

    // Two members: no freebies.
    PartySeed pair;
    pair.members = {member("Ariel", "Knight", 10), member("Brom", "Cleric", 10)};
    Party duo;
    duo.seed(pair);
    duo.setRules(&rules.gameRules());
    CHECK_FALSE(spells.keepsScroll(duo, 31));
    spells.updateAuras(duo, 0.5f);
    CHECK(duo.partyBuff(PartyBuffId::WizardEye) == nullptr);
}

TEST_CASE("MAW Assassins lose their Assassination bonus to a crowd and without energy (L6.2)")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    const ItemTable &items = gameData.itemTable;
    Character assassin = assassinWithSword();
    assassin.maxSpellPoints = 100;
    assassin.spellPoints = 100;
    // Assassination's 10 x (1 + Master) = 40 flat damage at Sword 10's x1.2; bare hands carry none.
    CHECK(mawAssassinationBonus(rules, assassin, items) == doctest::Approx(48));
    Character bare = assassin;
    bare.equipment.mainHand = 0;
    CHECK(mawAssassinationBonus(rules, bare, items) == doctest::Approx(0));
    CHECK(mawAssassinationBonus(rules, member("Brom", "Knight", 20), items) == doctest::Approx(0));

    const auto blow = [&](int near, int spellPoints)
    {
        assassin.spellPoints = spellPoints;
        std::mt19937 rng(3);
        CharacterAttackOnMonster context;
        context.pCharacter = &assassin;
        context.pItemTable = &items;
        context.minimumDamage = 200;
        context.maximumDamage = 200;
        context.monstersNearTarget = near;
        context.pRng = &rng;
        CharacterAttackResult attack;
        attack.mode = CharacterAttackMode::Melee;
        attack.canAttack = true;
        rules.gameRules().combat.resolveCharacterAttack(attack, context);
        return attack.damage;
    };

    // Alone it keeps the bonus; two more monsters take 40 % of it back, five or more 80 %; no energy, all of it.
    const int alone = blow(1, 100);
    CHECK(blow(0, 100) == alone);
    CHECK(double(blow(3, 100)) == doctest::Approx(alone * (200.0 - 19.2) / 200).epsilon(0.02));
    CHECK(double(blow(6, 100)) == doctest::Approx(alone * (200.0 - 38.4) / 200).epsilon(0.02));
    CHECK(double(blow(1, 0)) == doctest::Approx(alone * (200.0 - 48) / 200).epsilon(0.02));
}

TEST_CASE("MAW names final classes promoted on two or three worlds Elder and Ultimate (L6.5)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    ClassMultiplierTable multipliers;
    REQUIRE(multipliers.loadFromRows({{"Class", "HP base", "HP", "SP base", "SP", "Mode"},
        {"Cleric", "25", "2", "0", "2", "Personality"}, {"Priest of the Light", "25", "4", "0", "4", "Personality"}}));
    REQUIRE(multipliers.applyClassExtraRows({{"#", "Kind", "Step", "Note"}, {"0", "2", "0", "Cleric"},
        {"1", "2", "2", "Priest of the Light"}}));
    PartySeed seed;
    seed.members = {member("Ariel", "Cleric", 30), member("Brom", "PriestLight", 30)};
    Party party;
    party.seed(seed);
    party.setClassMultiplierTable(&multipliers);
    const ClassRules &classes = rules.gameRules().classes;

    CHECK_EQ(classes.displayName(party, party.members()[1]), "Priest of the Light");
    rules.setPromotionWorlds({{2, 2}});
    CHECK_EQ(classes.displayName(party, party.members()[1]), "Elder Priest of the Light");
    CHECK_EQ(classes.displayName(party, party.members()[0]), "Cleric");
    rules.setPromotionWorlds({{2, 3}});
    CHECK_EQ(classes.displayName(party, party.members()[1]), "Ultimate Priest of the Light");
    CHECK_EQ(standardClassRules().displayName(party, party.members()[1]), "Priest of the Light");
}

TEST_CASE("MAW stats page values shorten numbers of 10000 or more (H.9)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const SkillRules &skills = rules.gameRules().skills;
    CHECK_EQ(skills.statValueText("13381 / 13381"),
        mawShortNumber(13381, false) + " / " + mawShortNumber(13381, false));
    CHECK_EQ(skills.statValueText("1417 - 1496"), "1417 - 1496");
    CHECK_EQ(skills.statValueText("9999 - 250000"), "9999 - " + mawShortNumber(250000, false));
    CHECK_EQ(skills.statValueText("N/A"), "N/A");
    CHECK_EQ(standardGameRules().skills.statValueText("13381 / 13381"), "13381 / 13381");
}

TEST_CASE("MAW's Unstuck lifts the party 100 units once per five game minutes (D.12)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const ClassRules &classes = rules.gameRules().classes;
    CHECK_EQ(classes.unstuckLift(600), std::optional<float>(100.0f));
    CHECK_FALSE(classes.unstuckLift(602));
    CHECK_EQ(classes.unstuckLift(605), std::optional<float>(100.0f));
    // An earlier save's clock makes it ready at once.
    CHECK_EQ(classes.unstuckLift(30), std::optional<float>(100.0f));
    CHECK_FALSE(standardClassRules().unstuckLift(600));
}

TEST_CASE("MAW class spells crit against their target and lose the Assassination bonus to a crowd (A1.12, L6.2)")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    const ItemTable &items = gameData.itemTable;
    Character assassin = assassinWithSword();
    const SpellEntry *pBlades = gameData.spellTable.findById(39);
    REQUIRE(pBlades != nullptr);
    const auto average = [&](int targetLevel, int near)
    {
        CharacterSpellCast cast;
        cast.pCaster = &assassin;
        cast.pItemTable = &items;
        cast.pSpell = pBlades;
        cast.mastery = SkillMastery::Master;
        cast.skillLevel = 10;
        cast.targetLevel = targetLevel;
        cast.monstersNearTarget = near;
        double total = 0;

        for (int roll = 0; roll < 4000; ++roll)
        {
            total += rules.gameRules().combat.rollSpellDamage(cast);
        }

        return total / 4000;
    };

    // Blades is three blows; a crowd of six takes back four fifths of half the 48-point bonus from each: 57.6, at
    // the sword's speed multiplier.
    const MawAttackDelay delay = mawCharacterAttackDelay(rules, assassin, items, CharacterAttackMode::Melee, 0);
    const double alone = average(20, 1);
    CHECK(alone - average(20, 6) == doctest::Approx(57.6 * delay.damageMultiplier).epsilon(0.15));
    // A target far above the attacker is crit far less often than one far below: at 500 Luck, always against level 1
    // and about a fifth of the time against level 100000.
    assassin.luck = 500;
    CHECK(average(1, 1) > average(100000, 1) * 1.2);
}

TEST_CASE("MAW Assassins' Mass Distortion takes Earth twice; the vampires' drains leech a tenth (L6.3, A1.15)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Character assassin = member("Ariel", "Assassin", 20);
    Character mage = member("Brom", "Sorcerer", 20);
    std::mt19937 rng(1);
    const auto landed = [&](const Character &attacker)
    {
        MonsterDamageHit hit;
        hit.amount = 400;
        hit.type = CombatDamageType::Earth;
        hit.resistance = 100;
        hit.resistances.earth = 100;
        hit.pMissileAttacker = &attacker;
        hit.missileSpellId = 44;
        hit.pRng = &rng;
        return rules.gameRules().combat.damageToMonster(hit);
    };
    const int once = landed(mage);
    CHECK(double(landed(assassin)) == doctest::Approx(once / mawMonsterResistanceDivisor(100)).epsilon(0.02));
    // An Assassin's Mass Distortion is its blow, not a share of the target's hit points.
    CharacterSpellCast cast;
    SpellEntry massDistortion;
    massDistortion.id = 44;
    cast.pCaster = &assassin;
    cast.pSpell = &massDistortion;
    CHECK_FALSE(rules.gameRules().combat.spellDamageOnTarget(cast, {1000, 1000, nullptr}));
    cast.pCaster = &mage;
    CHECK(rules.gameRules().combat.spellDamageOnTarget(cast, {1000, 1000, nullptr}).has_value());

    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    party.setRules(&rules.gameRules());
    Character &vampire = *party.member(0);
    vampire.className = "Vampire";
    vampire.raceId = 1;
    vampire.maxHealth = 1000;
    vampire.health = 100;
    ActorRulesetFacts target;
    target.level = 20;
    target.familyLevel = 20;
    target.maxHp = 1000;
    const auto healedBy = [&](uint32_t spellId)
    {
        vampire.health = 100;
        PartyHitOnMonster hit;
        hit.memberIndex = 0;
        hit.damage = 500;
        hit.pTarget = &target;
        hit.spellId = spellId;
        rules.gameRules().combat.applyPartyHitEffects(party, hit);
        return vampire.health - 100;
    };

    // The race's spell leech heals any spell; the drains add a tenth of the bar share on top.
    CHECK(healedBy(111) > healedBy(2));
    CHECK(healedBy(99) > healedBy(2));

    // A Dark mage's Souldrinker is no vampire's: no tenth on top (CMB-22).
    vampire.className = "Sorcerer";
    vampire.raceId = 0;
    CHECK_EQ(healedBy(99), 0);
}

namespace
{
// Records the pushes the combat rules ask of the world.
class PushTestWorld : public OpenYAMM::Tests::PartySpellTestWorldRuntime
{
public:
    bool pushActor(size_t actorIndex, float directionX, float directionY, float distance) override
    {
        pushes.push_back({float(actorIndex), directionX, directionY, distance});
        return true;
    }

    size_t revealActorsAround(size_t actorIndex, float radius) override
    {
        reveals.emplace_back(actorIndex, radius);
        return 0;
    }

    bool isIndoorMap() const override
    {
        return indoor;
    }

    std::vector<std::array<float, 4>> pushes;
    std::vector<std::pair<size_t, float>> reveals;
    bool indoor = false;
};
}

TEST_CASE("MAW dragons' bites throw their target once Dragon Ability reaches Fangs (L6.4)")
{
    CHECK(mawDragonPushDistance(10, 1) == doctest::Approx(2048.0));
    CHECK(mawDragonPushDistance(16, 16) == doctest::Approx(400.0 * std::pow(16.0 / 8.0, 1.5)));
    CHECK(mawDragonPushDistance(4, 100) < 30.0);

    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    party.setRules(&rules.gameRules());
    Character &dragon = *party.member(0);
    dragon.raceId = 5;
    dragon.skills["Unarmed"] = {"Unarmed", 16, SkillMastery::Expert};
    dragon.skills["DragonAbility"] = {"DragonAbility", 16, SkillMastery::Expert};
    PushTestWorld world;
    world.bindParty(&party);
    GameplayRuntimeActorState actor = {};
    actor.preciseY = 300.0f;
    actor.hostileToParty = true;
    const size_t actorIndex = world.addActor(actor);
    ActorRulesetFacts target;
    target.level = 16;
    target.familyLevel = 16;
    target.maxHp = 1000;
    PartyHitOnMonster hit;
    hit.memberIndex = 0;
    hit.damage = 50;
    hit.pTarget = &target;
    hit.melee = true;
    hit.pWorld = &world;
    hit.targetActorIndex = actorIndex;
    rules.gameRules().combat.applyPartyHitEffects(party, hit);
    REQUIRE_EQ(world.pushes.size(), 1u);
    CHECK(world.pushes[0][1] == doctest::Approx(0.0f));
    CHECK(world.pushes[0][2] == doctest::Approx(1.0f));
    CHECK(world.pushes[0][3] == doctest::Approx(mawDragonPushDistance(16, 16)));

    // Fangs above Dragon Ability, a kill, or a breath (not a bite) throw nothing; nor does a dragon-classed human.
    dragon.skills["Unarmed"].level = 17;
    rules.gameRules().combat.applyPartyHitEffects(party, hit);
    dragon.skills["Unarmed"].level = 16;
    hit.killed = true;
    rules.gameRules().combat.applyPartyHitEffects(party, hit);
    hit.killed = false;
    hit.melee = false;
    rules.gameRules().combat.applyPartyHitEffects(party, hit);
    hit.melee = true;
    dragon.raceId = 0;
    rules.gameRules().combat.applyPartyHitEffects(party, hit);
    CHECK_EQ(world.pushes.size(), 1u);
}

TEST_CASE("MAW's Doom modes kill, eradicate and, from Road to Insanity, disintegrate deep overkills (P9.D11, P9.I3)")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const auto run = [&](RulesetChallengeMode mode, bool preference, int healthInFulls)
    {
        RulesetOptions options;
        options.difficulty = RulesetDifficulty::Nightmare;
        options.challengeMode = mode;
        options.preferences.disintegration = preference;
        MawRules rules(options, MawMapLevels{});
        Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
        party.setRules(&rules.gameRules());
        const size_t before = party.members().size();
        Character &victim = *party.member(1);
        victim.health = healthInFulls * Party::effectiveMaximumHealth(victim) - 1;
        rules.gameRules().combat.characterDamaged(party, 1);
        OpenYAMM::Tests::PartySpellTestWorldRuntime world;
        world.bindParty(&party);
        rules.gameRules().combat.updateCombat(party, world, 0.016f);
        const std::vector<std::string> &messages = world.eventRuntimeState()->statusMessages;
        const bool disintegrated = party.members().size() == before - 1;
        CHECK_EQ(disintegrated, std::find(messages.begin(), messages.end(), "Disintegrated") != messages.end());
        return disintegrated ? std::string("disintegrated")
            : party.member(1)->conditions.test(size_t(CharacterCondition::Eradicated)) ? "eradicated"
            : party.member(1)->conditions.test(size_t(CharacterCondition::Dead)) ? "dead"
            : "alive";
    };

    CHECK_EQ(run(RulesetChallengeMode::Doom, true, -1), "dead");
    CHECK_EQ(run(RulesetChallengeMode::Doom, true, -2), "eradicated");
    CHECK_EQ(run(RulesetChallengeMode::Doom, true, -10), "eradicated");
    CHECK_EQ(run(RulesetChallengeMode::RoadToInsanity, true, -9), "eradicated");
    CHECK_EQ(run(RulesetChallengeMode::RoadToInsanity, true, -10), "disintegrated");
    CHECK_EQ(run(RulesetChallengeMode::BeyondMadness, true, -10), "disintegrated");
    CHECK_EQ(run(RulesetChallengeMode::RoadToInsanity, false, -10), "eradicated");
}

TEST_CASE("MAW's Doom modes wake the monsters near a struck one indoors (P9.D8)")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const auto reveals = [&](RulesetChallengeMode mode, bool indoor)
    {
        RulesetOptions options;
        options.challengeMode = mode;
        MawRules rules(options, MawMapLevels{});
        Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
        party.setRules(&rules.gameRules());
        PushTestWorld world;
        world.indoor = indoor;
        world.bindParty(&party);
        const size_t actorIndex = world.addActor(GameplayRuntimeActorState{});
        ActorRulesetFacts target;
        target.level = 10;
        target.maxHp = 1000;
        PartyHitOnMonster hit;
        hit.damage = 10;
        hit.pTarget = &target;
        hit.melee = true;
        hit.pWorld = &world;
        hit.targetActorIndex = actorIndex;
        rules.gameRules().combat.applyPartyHitEffects(party, hit);
        return world.reveals;
    };

    const std::vector<std::pair<size_t, float>> doom = reveals(RulesetChallengeMode::Doom, true);
    REQUIRE_EQ(doom.size(), 1u);
    CHECK(doom[0].second == doctest::Approx(256.0f));
    CHECK_EQ(reveals(RulesetChallengeMode::BeyondMadness, true).size(), 1u);
    CHECK(reveals(RulesetChallengeMode::Doom, false).empty());
    CHECK(reveals(RulesetChallengeMode::None, true).empty());
    CHECK(reveals(RulesetChallengeMode::Austerity, true).empty());
}

TEST_CASE("MAW's Doom modes and Austerity end a turn-based walk 370 units from where it began (P9.D9)")
{
    const auto walkEndsAt = [](RulesetChallengeMode mode, float distance)
    {
        RulesetOptions options;
        options.challengeMode = mode;
        MawRules rules(options, MawMapLevels{});
        PartySeed seed;
        seed.members.resize(1);
        seed.members[0].name = "Ariel";
        seed.members[0].health = 100;
        seed.members[0].maxHealth = 100;
        Party party;
        party.seed(seed);
        party.setRules(&rules.gameRules());
        TurnBasedCombatRuntime runtime;
        REQUIRE(runtime.begin(party, nullptr));
        runtime.update(&party, nullptr, 0.6f);
        REQUIRE(runtime.applyPlayerAction(party, 0, 5.0f));
        runtime.update(&party, nullptr, 0.016f);
        REQUIRE(runtime.stage() == TurnBasedCombatStage::Movement);
        OpenYAMM::Tests::PartySpellTestWorldRuntime world;
        world.bindParty(&party);
        world.setPartyPosition(1000.0f, 0.0f, 0.0f);
        runtime.update(&party, &world, 0.016f);
        world.setPartyPosition(1000.0f, distance, 0.0f);
        runtime.update(&party, &world, 0.016f);
        runtime.update(&party, &world, 0.016f);
        return runtime.stage() != TurnBasedCombatStage::Movement;
    };

    CHECK(walkEndsAt(RulesetChallengeMode::Doom, 371.0f));
    CHECK_FALSE(walkEndsAt(RulesetChallengeMode::Doom, 369.0f));
    CHECK(walkEndsAt(RulesetChallengeMode::Austerity, 371.0f));
    CHECK(walkEndsAt(RulesetChallengeMode::BeyondMadness, 371.0f));
    CHECK_FALSE(walkEndsAt(RulesetChallengeMode::None, 2000.0f));
}

TEST_CASE("MAW's Austerity gives body armour and shields at least round(skill x mastery) x 2 AC and resistance (P9.A2)")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const auto breakdown = [&](RulesetChallengeMode mode)
    {
        RulesetOptions options;
        options.challengeMode = mode;
        MawRules rules(options, MawMapLevels{}, installedItemData());
        Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
        party.setRules(&rules.gameRules());
        Character &member = *party.member(0);
        member.equipment = {};
        member.skills["LeatherArmor"] = {"LeatherArmor", 10, SkillMastery::Expert};
        member.skills["Shield"] = {"Shield", 6, SkillMastery::Master};
        member.equipment.armor = 84;

        for (uint32_t itemId = 1; itemId < 800 && member.equipment.offHand == 0; ++itemId)
        {
            const ItemDefinition *pItem = party.itemTable()->get(itemId);
            member.equipment.offHand =
                pItem != nullptr && canonicalSkillName(pItem->skillGroup) == "Shield" ? itemId : 0;
        }

        REQUIRE(member.equipment.offHand != 0);
        return mawArmorBreakdown(rules, member, *party.itemTable());
    };

    const MawArmorBreakdown normal = breakdown(RulesetChallengeMode::None);
    const MawArmorBreakdown austerity = breakdown(RulesetChallengeMode::Austerity);
    REQUIRE(normal.pieces >= 1);
    REQUIRE(normal.shield >= 1);
    REQUIRE(normal.bodySkillArmor < 40);
    CHECK_EQ(austerity.bodySkillArmor, 40);
    CHECK_EQ(austerity.bodySkillResistance, std::max(40, normal.bodySkillResistance));
    CHECK_EQ(austerity.shieldSkillArmor, std::max(36, normal.shieldSkillArmor));
    CHECK_EQ(austerity.shieldSkillResistance, std::max(36, normal.shieldSkillResistance));
}

TEST_CASE("MAW's Austerity gives everyone Identify Monster 10 Grandmaster on each map, none after a respec (P9.A3)")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    RulesetOptions options;
    options.challengeMode = RulesetChallengeMode::Austerity;
    MawRules rules(options, MawMapLevels{});
    Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    party.setRules(&rules.gameRules());
    OpenYAMM::Tests::PartySpellTestWorldRuntime world;
    world.bindParty(&party);
    const auto identify = [&](size_t memberIndex)
    {
        const CharacterSkill *pSkill = party.member(memberIndex)->findSkill("IdentifyMonster");
        return pSkill != nullptr ? std::pair(int(pSkill->level), pSkill->mastery) : std::pair(0, SkillMastery::None);
    };

    rules.setCurrentMap("oute3.odm");
    rules.gameRules().classes.update(party, world, 0.5f);
    CHECK(identify(0) == std::pair(10, SkillMastery::Grandmaster));
    CHECK(identify(3) == std::pair(10, SkillMastery::Grandmaster));

    // A respec refunds nothing for it and takes it from everyone until the next map.
    const uint32_t pointsBefore = party.member(1)->skillPoints;
    REQUIRE(rules.gameRules().skills.resetSkills(*party.member(1)));
    CHECK(party.member(1)->skillPoints >= pointsBefore);
    rules.gameRules().classes.update(party, world, 0.5f);
    CHECK_EQ(identify(0).first, 0);
    CHECK_EQ(identify(1).first, 0);
    rules.setCurrentMap("oute3.odm");
    rules.gameRules().classes.update(party, world, 0.5f);
    CHECK_EQ(identify(0).first, 0);
    rules.setCurrentMap("6d01.blv");
    rules.gameRules().classes.update(party, world, 0.5f);
    CHECK(identify(2) == std::pair(10, SkillMastery::Grandmaster));

    // Outside Austerity nothing is handed out.
    MawRules normalRules(RulesetOptions{}, MawMapLevels{});
    Party normal = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    normal.setRules(&normalRules.gameRules());
    normalRules.setCurrentMap("oute3.odm");
    normalRules.gameRules().classes.update(normal, world, 0.5f);
    CHECK(normal.member(0)->findSkill("IdentifyMonster") == nullptr);
}

TEST_CASE("MAW's Doom modes give monsters a special attack by level once per map fill (P9.D2)")
{
    // An A-tier row, which never becomes a boss.
    MonsterTable::MonsterStatsEntry stats;
    stats.id = 193;
    MapStatsEntry map = {};
    map.fileName = "out02.odm";
    GameplayBolsterRuntimeContext context = {};
    context.pMap = &map;
    const auto place = [&](RulesetChallengeMode mode, int level, std::vector<ActorRulesetFacts> &facts)
    {
        RulesetOptions options;
        options.challengeMode = mode;
        MawRules rules(options, MawMapLevels{});
        rules.setRandomRootSeed(1234);
        std::vector<MapMonsterPlacement> placements;

        for (size_t index = 0; index < facts.size(); ++index)
        {
            facts[index] = {.level = level, .familyLevel = level, .tier = 1};
            // Every tenth is one of the map's unique monsters (place_mon names 1-219).
            placements.push_back({&stats, false, true, &facts[index], index % 10 == 0 ? 5 : 0});
        }

        rules.gameRules().monsters.placeMapMonsters(context, placements);
    };
    using Kind = MonsterSpecialAttackKind;

    std::vector<ActorRulesetFacts> facts(4000);
    place(RulesetChallengeMode::Doom, 400, facts);
    size_t rolled = 0;
    std::set<Kind> kinds;

    for (size_t index = 0; index < facts.size(); ++index)
    {
        CHECK((index % 10 != 0 || facts[index].doomSpecialAttack == 0));
        rolled += facts[index].doomSpecialAttack != 0 ? 1 : 0;
        kinds.insert(Kind(facts[index].doomSpecialAttack));
    }

    // Level 400 is stored as 255: √255 × 2 % of the 3600 others; all 18 kinds open from level 100.
    CHECK(double(rolled) / 3600 == doctest::Approx(std::sqrt(255.0) * 0.02).epsilon(0.1));
    CHECK_EQ(kinds.size(), 19u);

    // At level 16 only the poisons, Weakness, Fear and Curse.
    place(RulesetChallengeMode::RoadToInsanity, 16, facts);
    kinds.clear();

    for (const ActorRulesetFacts &fact : facts)
    {
        kinds.insert(Kind(fact.doomSpecialAttack));
    }

    CHECK(kinds == std::set<Kind>{Kind::None, Kind::PoisonWeak, Kind::PoisonMedium, Kind::PoisonSevere, Kind::Weak,
        Kind::Fear, Kind::Curse});

    // The same map and seed roll the same; outside the Doom modes nothing.
    std::vector<ActorRulesetFacts> again(4000);
    place(RulesetChallengeMode::RoadToInsanity, 16, again);
    CHECK(again == facts);
    place(RulesetChallengeMode::Austerity, 400, facts);
    CHECK(std::all_of(facts.begin(), facts.end(), [](const ActorRulesetFacts &fact)
        { return fact.doomSpecialAttack == 0; }));
}

TEST_CASE("MAW's Road to Insanity heals dearer and ends Invisibility when an enemy is in melee range (P9.I4)")
{
    // getBaseHealingSpells: Heal costs 40 at Grandmaster and heals 48 + 15 per point; Resurrection 300.
    const std::optional<MawHealSpell> heal = mawHealSpell(68, SkillMastery::Grandmaster, true);
    REQUIRE(heal);
    CHECK_EQ(heal->cost, 40);
    CHECK(heal->base == doctest::Approx(48));
    CHECK(heal->perPoint == doctest::Approx(15));
    CHECK_EQ(mawHealSpell(55, SkillMastery::Grandmaster, true)->cost, 300);
    CHECK_EQ(mawHealSpell(68, SkillMastery::Grandmaster, false)->cost, 8);
    CHECK_FALSE(mawHealSpell(74, SkillMastery::Expert, true));

    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const auto invisibleAfter = [&](RulesetChallengeMode mode, float enemyDistance)
    {
        RulesetOptions options;
        options.challengeMode = mode;
        MawRules rules(options, MawMapLevels{});
        Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
        party.setRules(&rules.gameRules());
        party.applyPartyBuff(PartyBuffId::Invisibility, 600.0f, 1, 19, 10, SkillMastery::Master, 0);
        OpenYAMM::Tests::PartySpellTestWorldRuntime world;
        world.bindParty(&party);
        GameplayRuntimeActorState enemy = {};
        enemy.preciseX = enemyDistance;
        enemy.radius = 32;
        enemy.hostileToParty = true;
        enemy.hasDetectedParty = true;
        world.addActor(enemy);
        rules.gameRules().combat.updateCombat(party, world, 0.016f);
        return party.hasPartyBuff(PartyBuffId::Invisibility);
    };

    CHECK_FALSE(invisibleAfter(RulesetChallengeMode::RoadToInsanity, 200.0f));
    CHECK_FALSE(invisibleAfter(RulesetChallengeMode::BeyondMadness, 200.0f));
    CHECK(invisibleAfter(RulesetChallengeMode::RoadToInsanity, 1000.0f));
    CHECK(invisibleAfter(RulesetChallengeMode::Doom, 200.0f));
}

TEST_CASE("MAW's Beyond Madness offers no mercenaries and calls Town Portal near enemies cowardice (P9.M7)")
{
    const auto rules = [](RulesetChallengeMode mode)
    {
        RulesetOptions options;
        options.challengeMode = mode;
        return std::make_unique<MawRules>(options, MawMapLevels{});
    };
    const std::unique_ptr<MawRules> madness = rules(RulesetChallengeMode::BeyondMadness);
    const std::unique_ptr<MawRules> insanity = rules(RulesetChallengeMode::RoadToInsanity);

    CHECK_FALSE(madness->gameRules().classes.offersMercenaries());
    CHECK(insanity->gameRules().classes.offersMercenaries());
    CHECK(standardGameRules().classes.offersMercenaries());

    const MonsterRules &madnessMonsters = madness->gameRules().monsters;
    CHECK(madnessMonsters.teleportBlockedNearEnemies());
    CHECK_EQ(madnessMonsters.teleportBlockedText(true), "Madness is not a place for cowards");
    CHECK_EQ(madnessMonsters.teleportBlockedText(false), "Can't teleport now");
    CHECK_EQ(insanity->gameRules().monsters.teleportBlockedText(true), "Can't teleport now");
}

namespace
{
// Records the charge's dash and stun.
class ChargeTestWorld : public OpenYAMM::Tests::PartySpellTestWorldRuntime
{
public:
    bool dashParty(float directionX, float directionY, float distance) override
    {
        dashes.push_back({directionX, directionY, distance});
        return true;
    }

    bool stunActor(size_t actorIndex, float seconds) override
    {
        stuns.emplace_back(actorIndex, seconds);
        return true;
    }

    std::vector<std::array<float, 3>> dashes;
    std::vector<std::pair<size_t, float>> stuns;
};
}

TEST_CASE("MAW's Knight Charge throws a lone Knight at a monster 500-3000 units away and stuns it (L6.1)")
{
    const auto solo = [](const std::string &className)
    {
        PartySeed seed;
        seed.members.resize(1);
        seed.members[0].name = "Ariel";
        seed.members[0].className = className;
        seed.members[0].health = 100;
        seed.members[0].maxHealth = 100;
        return seed;
    };
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Party party;
    party.seed(solo("Cavalier"));
    party.setRules(&rules.gameRules());
    ChargeTestWorld world;
    world.bindParty(&party);
    GameplayRuntimeActorState near = {};
    near.preciseX = 400.0f;
    GameplayRuntimeActorState target = {};
    target.preciseY = 1100.0f;
    const size_t nearIndex = world.addActor(near);
    const size_t targetIndex = world.addActor(target);
    const ClassRules &classes = rules.gameRules().classes;

    CHECK_EQ(classes.partyCharge(party, world, std::nullopt).value_or("?"), "");
    CHECK_EQ(classes.partyCharge(party, world, nearIndex).value_or("?"), "Out of range");
    CHECK_EQ(classes.partyCharge(party, world, targetIndex).value_or("?"), "Ariel casts Charge stunning the enemy");
    REQUIRE_EQ(world.dashes.size(), 1u);
    CHECK(world.dashes[0][0] == doctest::Approx(0.0f));
    CHECK(world.dashes[0][1] == doctest::Approx(1.0f));
    CHECK(world.dashes[0][2] == doctest::Approx(1000.0f));
    // A Cavalier holds it two game minutes: 4 seconds.
    REQUIRE_EQ(world.stuns.size(), 1u);
    CHECK_EQ(world.stuns[0].first, targetIndex);
    CHECK(world.stuns[0].second == doctest::Approx(4.0f));

    // 25 seconds of cooldown: 12.5 game minutes.
    CHECK_EQ(classes.partyCharge(party, world, targetIndex).value_or("?"), "Charge has 25 seconds of cooldown");
    world.advanceGameMinutes(12.5f);
    CHECK_EQ(classes.partyCharge(party, world, targetIndex).value_or("?"), "Ariel casts Charge stunning the enemy");
    CHECK_EQ(world.dashes.size(), 2u);

    // Other classes, larger parties and Standard have no charge.
    Party sorcerer;
    sorcerer.seed(solo("Sorcerer"));
    sorcerer.setRules(&rules.gameRules());
    CHECK_FALSE(classes.partyCharge(sorcerer, world, targetIndex));
    Party pair;
    PartySeed two = solo("Knight");
    two.members.push_back(two.members[0]);
    pair.seed(two);
    pair.setRules(&rules.gameRules());
    CHECK_FALSE(classes.partyCharge(pair, world, targetIndex));
    CHECK_FALSE(standardGameRules().classes.partyCharge(party, world, targetIndex));
}

TEST_CASE("MAW's Austerity names the potions it removed \"Potion Deleted in Austerity\" (P9.A4)")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const auto name = [&](RulesetChallengeMode mode, uint32_t itemId)
    {
        RulesetOptions options;
        options.challengeMode = mode;
        MawRules rules(options, MawMapLevels{}, installedItemData());
        const ItemDefinition *pItem = gameData.itemTable.get(itemId);
        REQUIRE(pItem != nullptr);
        InventoryItem item;
        item.objectDescriptionId = itemId;
        item.identified = true;
        return rules.gameRules().items.displayName(item, *pItem, nullptr, nullptr);
    };

    for (const uint32_t itemId : {232u, 237u, 252u, 256u, 261u, 263u})
    {
        CHECK_EQ(name(RulesetChallengeMode::Austerity, itemId), "Potion Deleted in Austerity");
        CHECK_NE(name(RulesetChallengeMode::None, itemId), "Potion Deleted in Austerity");
    }

    CHECK_NE(name(RulesetChallengeMode::Austerity, 238), "Potion Deleted in Austerity");
    CHECK_NE(name(RulesetChallengeMode::Austerity, 260), "Potion Deleted in Austerity");
}

TEST_CASE("MAW's stat rows Melee, Ranged and Spell Power and Vitality have popups of their own")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    party.setRules(&rules.gameRules());
    const SkillRules &skills = rules.gameRules().skills;
    const Character &member = *party.member(0);
    const auto title = [&](const char *pStat)
    {
        const std::optional<CharacterStatRowText> row = skills.statRowText(party, member, pStat);
        return row ? row->popupTitle : std::string();
    };

    CHECK_EQ(title("Condition"), "Melee Power");
    CHECK_EQ(title("QuickSpell"), "Ranged Power");
    CHECK_EQ(title("SpellPower"), "Spell Power");
    CHECK_EQ(title("Vitality"), "Vitality");

    const std::string melee = skills.statTooltip(party, member, "Condition", "The table's Condition text.");
    CHECK(melee.find("Melee Power:") != std::string::npos);
    CHECK(melee.find("Condition text") == std::string::npos);
    const std::string ranged = skills.statTooltip(party, member, "QuickSpell", "The table's Quick Spell text.");
    CHECK(ranged.find("Ranged Power:") != std::string::npos);
    CHECK(ranged.find("Quick Spell text") == std::string::npos);
    CHECK(skills.statTooltip(party, member, "SpellPower", "").find("attack or quick spell") != std::string::npos);
    const std::string vitality = skills.statTooltip(party, member, "Vitality", "");
    CHECK(vitality.find("Vitality:") != std::string::npos);
    CHECK(vitality.find("Currently Active Legendary effects: none") != std::string::npos);

    // Standard keeps its rows and adds none.
    CHECK_FALSE(standardGameRules().skills.statRowText(party, member, "QuickSpell").has_value());
    CHECK_FALSE(standardGameRules().skills.statRowText(party, member, "Vitality").has_value());
}

TEST_CASE("MAW's Spell Power row counts a healing quick spell, as MAW's calcPowerVitality does")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    rules.setSpellTable(&gameData.spellTable);
    Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    party.setRules(&rules.gameRules());
    Character &healer = *party.member(1);
    healer.skills["BodyMagic"] = {"BodyMagic", 10, SkillMastery::Expert};
    healer.attackSpellName.clear();
    healer.quickSpellName = "Heal";
    const SkillRules &skills = rules.gameRules().skills;

    const std::optional<CharacterStatRowText> row = skills.statRowText(party, healer, "SpellPower");
    REQUIRE(row.has_value());
    CHECK_EQ(row->label, "Spell Power:");
    CHECK_EQ(row->popupTitle, "Spell Power");
    CHECK_NE(row->value, "-");
    // Ranged Power keeps its own row whatever the spell.
    CHECK_EQ(skills.statRowText(party, healer, "QuickSpell")->label, "Ranged Power:");
    const MawPowerReport report = mawPowerReport(rules, healer, *party.itemTable(), nullptr, nullptr, 4);
    // Expert Heal: 8 + 10 x 3 = 38 a cast before Personality.
    CHECK_GT(report.spell, 0);

    healer.quickSpellName.clear();
    CHECK_EQ(skills.statRowText(party, healer, "SpellPower")->value, "-");
}

TEST_CASE("Mass Distortion hits a monster for the ruleset's share of its hit points, through the world (SPL-1)")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    GameplayActorService actorService;
    actorService.bindTables(&gameData.monsterTable, &gameData.spellTable);
    MawRules rules(RulesetOptions{}, MawMapLevels{});

    for (const bool maw : {false, true})
    {
        CAPTURE(maw);
        Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);

        if (maw)
        {
            party.setRules(&rules.gameRules());
        }

        OpenYAMM::Tests::PartySpellTestWorldRuntime world;
        world.bindParty(&party);
        GameplayRuntimeActorState monster;
        monster.preciseX = 1024;
        monster.radius = 48;
        monster.height = 160;
        monster.currentHp = 1000;
        monster.maxHp = 1000;
        monster.hostileToParty = true;
        monster.hasDetectedParty = true;
        const size_t target = world.addActor(monster);
        Character *pCaster = party.member(0);
        REQUIRE(pCaster != nullptr);
        pCaster->className = "Sorcerer";
        pCaster->skills["EarthMagic"] = {"EarthMagic", 10, SkillMastery::Grandmaster};
        pCaster->maxSpellPoints = 100000;
        pCaster->spellPoints = 100000;
        PartySpellCastRequest request;
        request.casterMemberIndex = 0;
        request.spellId = spellIdValue(SpellId::MassDistortion);
        request.targetActorIndex = target;
        const PartySpellCastResult result = PartySpellSystem::castSpell(party, world, gameData.spellTable, request);
        REQUIRE(result.status == PartySpellCastStatus::Succeeded);
        REQUIRE_EQ(world.appliedSpellRequests().size(), 1u);

        // Standard: 25 % + 2 % per point of the current 1000; MAW: its own 15 % + 0.5 % per point.
        const int damage = world.appliedSpellRequests().front().damage;
        CHECK_EQ(damage, maw ? 200 : 450);
        // The world applies what it is given, not Standard's share again.
        const GameplayActorService::DirectSpellImpactResult impact =
            actorService.resolveDirectSpellImpact(request.spellId, 10, damage, false);
        CHECK_EQ(impact.damage, damage);
    }
}

TEST_CASE("MAW class spells cast at their class mastery step, as the original engine casts any known spell")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    party.setRules(&rules.gameRules());
    OpenYAMM::Tests::PartySpellTestWorldRuntime world;
    world.bindParty(&party);
    GameplayRuntimeActorState actor;
    actor.preciseX = 1024;
    actor.radius = 48;
    actor.height = 160;
    actor.currentHp = 50;
    actor.maxHp = 50;
    actor.hostileToParty = true;
    actor.hasDetectedParty = true;
    const size_t target = world.addActor(actor);

    Character *pCaster = party.member(0);
    REQUIRE(pCaster != nullptr);
    pCaster->maxSpellPoints = 1000;
    pCaster->spellPoints = 1000;
    const auto cast = [&](uint32_t spellId)
    {
        PartySpellCastRequest request;
        request.casterMemberIndex = 0;
        request.spellId = spellId;
        request.targetActorIndex = target;
        return PartySpellSystem::castSpell(party, world, gameData.spellTable, request).status;
    };

    // A Thief knows Stone Skin and Water Walk at Novice and Shield without Air (the table wants Expert for all three).
    pCaster->className = "Thief";
    pCaster->skills.clear();
    pCaster->skills["EarthMagic"] = {"EarthMagic", 3, SkillMastery::Normal};
    pCaster->knownSpellIds = {38, 17};
    CHECK(rules.gameRules().spells.classSpellMastery(*pCaster, 38) == SkillMastery::Normal);
    CHECK(rules.gameRules().spells.classSpellMastery(*pCaster, 17) == SkillMastery::None);
    CHECK(cast(38) == PartySpellCastStatus::Succeeded);
    CHECK(cast(17) == PartySpellCastStatus::Succeeded);

    // An Elementalist's rotation casts its known Deadly Swarm without Earth.
    pCaster->className = "Elementalist";
    pCaster->skills.clear();
    pCaster->skills["FireMagic"] = {"FireMagic", 3, SkillMastery::Normal};
    pCaster->knownSpellIds = {2, 15, 24, 37};
    pCaster->recoverySecondsRemaining = 0.0f;
    CHECK(cast(37) == PartySpellCastStatus::Succeeded);

    // Standard keeps the table's masteries.
    pCaster->className = "Thief";
    pCaster->skills.clear();
    pCaster->skills["EarthMagic"] = {"EarthMagic", 3, SkillMastery::Normal};
    pCaster->knownSpellIds = {38};
    party.setRules(&standardGameRules());
    CHECK(cast(38) == PartySpellCastStatus::NotSkilledEnough);
}

TEST_CASE("a dragon bites a target in melee range and breathes at one further away")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    Character dragon;
    dragon.name = "Ariel";
    dragon.className = "Dragon";
    dragon.level = 10;
    dragon.skills["DragonAbility"] = {"DragonAbility", 5, SkillMastery::Normal};
    const CharacterAttackProfile profile =
        GameMechanics::buildCharacterAttackProfile(dragon, &gameData.itemTable, &gameData.spellTable);
    REQUIRE(profile.hasDragonBreath);
    std::mt19937 rng(7);
    const auto modeAt = [&](float distance)
    {
        return GameMechanics::resolveCharacterAttackAgainstArmorClass(
            dragon, &gameData.itemTable, &gameData.spellTable, 10, distance, rng).mode;
    };
    // MAW's dragon damage has a bite branch (fang knockback, SP gain; Damage.lua:592-610) that breath alone never
    // reached.
    CHECK(modeAt(200.0f) == CharacterAttackMode::Melee);
    CHECK(modeAt(1024.0f) == CharacterAttackMode::DragonBreath);
}

TEST_CASE("a MAW dragon breathes by its race, whatever its class")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    Character knight;
    knight.name = "Ariel";
    knight.className = "Knight";
    knight.raceId = 5;
    knight.level = 10;
    knight.skills["DragonAbility"] = {"DragonAbility", 5, SkillMastery::Normal};
    Character human = knight;
    human.className = "Dragon";
    human.raceId = 0;
    const auto breathes = [&](const Character &character)
    {
        return GameMechanics::buildCharacterAttackProfile(character, &gameData.itemTable, &gameData.spellTable)
            .hasDragonBreath;
    };

    // Standard: the Dragon class breathes.
    CHECK_FALSE(breathes(knight));
    CHECK(breathes(human));

    MawRules rules(RulesetOptions{}, MawMapLevels{});
    bindGameRules(&rules.gameRules());
    CHECK(breathes(knight));
    CHECK_FALSE(breathes(human));
    bindGameRules(nullptr);
}

TEST_CASE("MAW's Bow preference off: no arrow or breath, the melee attack at its pace, Bow off on the stats page")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const ItemTable &items = gameData.itemTable;
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    party.setRules(&rules.gameRules());
    bindGameRules(&rules.gameRules());
    const SkillRules &skills = rules.gameRules().skills;

    // An archer with a Hunting Bow and a longsword, and a dragon.
    Character archer;
    archer.name = "Ariel";
    archer.className = "Archer";
    archer.level = 20;
    archer.equipment.mainHand = 1;
    archer.equipment.bow = 56;
    archer.skills["Sword"] = {"Sword", 10, SkillMastery::Expert};
    archer.skills["Bow"] = {"Bow", 10, SkillMastery::Expert};
    Character dragon;
    dragon.name = "Duroth";
    dragon.className = "Dragon";
    dragon.raceId = 5;
    dragon.level = 20;
    dragon.skills["DragonAbility"] = {"DragonAbility", 5, SkillMastery::Normal};
    std::mt19937 rng(7);
    const auto attackAt = [&](const Character &character, float distance)
    {
        return GameMechanics::resolveCharacterAttackAgainstArmorClass(
            character, &items, &gameData.spellTable, 10, distance, rng);
    };
    const auto delay = [&](const Character &character, CharacterAttackMode mode)
    {
        return mawCharacterAttackDelay(rules, character, items, mode, 50).delay;
    };

    // Off by default: the archer shoots, the dragon breathes, and the stats page shows the bow's own rows.
    CHECK_FALSE(RulesetOptions{}.preferences.bowDisabled);
    CHECK_FALSE(rules.gameRules().combat.bowDisabled());
    CHECK(attackAt(archer, 1024.0f).mode == CharacterAttackMode::Bow);
    CHECK(attackAt(dragon, 1024.0f).mode == CharacterAttackMode::DragonBreath);
    CHECK_NE(delay(archer, CharacterAttackMode::Bow), delay(archer, CharacterAttackMode::Melee));
    CHECK_FALSE(skills.statRowText(party, archer, "Shoot").has_value());
    CHECK_FALSE(skills.statRowText(party, archer, "RangedDamage").has_value());

    RulesetOptions options;
    options.preferences.bowDisabled = true;
    rules.setOptions(options);
    CHECK(rules.gameRules().combat.bowDisabled());

    // Nothing leaves the bow: the attack at range is the melee one, which reaches nothing, at the melee pace.
    const CharacterAttackProfile archerProfile =
        GameMechanics::buildCharacterAttackProfile(archer, &items, &gameData.spellTable);
    CHECK_FALSE(archerProfile.hasBow);
    CHECK_FALSE(archerProfile.canShoot);
    const CharacterAttackResult shot = attackAt(archer, 1024.0f);
    CHECK(shot.mode == CharacterAttackMode::Melee);
    CHECK_FALSE(shot.canAttack);
    CHECK_FALSE(shot.resolvesOnImpact);
    CHECK(shot.recoverySeconds == doctest::Approx(archerProfile.meleeRecoverySeconds));
    CHECK(attackAt(archer, 200.0f).mode == CharacterAttackMode::Melee);
    // MAW gives a ranged attack the melee delay (zzMAW-Skills.lua:614-616), Flame Blast's breath too.
    CHECK_EQ(delay(archer, CharacterAttackMode::Bow), delay(archer, CharacterAttackMode::Melee));
    CHECK_EQ(delay(dragon, CharacterAttackMode::DragonBreath), delay(dragon, CharacterAttackMode::Melee));

    // The dragon bites, near or far.
    CHECK_FALSE(GameMechanics::buildCharacterAttackProfile(dragon, &items, &gameData.spellTable).hasDragonBreath);
    CHECK(attackAt(dragon, 1024.0f).mode == CharacterAttackMode::Melee);
    CHECK(attackAt(dragon, 200.0f).mode == CharacterAttackMode::Melee);

    // The stats page's Shoot rows say so, for the dragon too.
    const std::optional<CharacterStatRowText> shoot = skills.statRowText(party, archer, "Shoot");
    REQUIRE(shoot.has_value());
    CHECK_EQ(shoot->value, "Bow off");
    CHECK(shoot->popupTitle.empty());
    REQUIRE(skills.statRowText(party, archer, "RangedDamage").has_value());
    CHECK_EQ(skills.statRowText(party, archer, "RangedDamage")->value, "-");
    REQUIRE(skills.statRowText(party, dragon, "Shoot").has_value());
    CHECK_EQ(skills.statRowText(party, dragon, "Shoot")->value, "Bow off");

    // Standard has no such preference.
    CHECK_FALSE(standardGameRules().combat.bowDisabled());
    CHECK_FALSE(standardGameRules().skills.statRowText(party, archer, "Shoot").has_value());
    bindGameRules(nullptr);
}

TEST_CASE("MAW missile and spell crits reach the status line: breath's Flame Blast, Fireball; Standard none (user)")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    const SpellEntry *pFlameBlast = gameData.spellTable.findById(123);
    const SpellEntry *pFireball = gameData.spellTable.findById(spellIdValue(SpellId::Fireball));
    REQUIRE(pFlameBlast != nullptr);
    REQUIRE(pFireball != nullptr);

    Character dragon;
    dragon.name = "Dragon";
    dragon.className = "Dragon";
    dragon.raceId = 5;
    dragon.level = 50;
    dragon.might = dragon.accuracy = dragon.speed = 89;
    dragon.skills["DragonAbility"] = {"DragonAbility", 17, SkillMastery::Grandmaster};
    Character sorcerer;
    sorcerer.name = "Sorcerer";
    sorcerer.className = "Sorcerer";
    sorcerer.level = 50;
    sorcerer.skills["FireMagic"] = {"FireMagic", 17, SkillMastery::Grandmaster};

    const auto criticalShare = [&](Character &caster, const SpellEntry &spell, const GameRules &gameRules)
    {
        CharacterSpellCast cast;
        cast.pCaster = &caster;
        cast.pItemTable = &gameData.itemTable;
        cast.pSpell = &spell;
        cast.mastery = SkillMastery::Grandmaster;
        cast.skillLevel = 17;
        int criticals = 0;

        for (int roll = 0; roll < 200; ++roll)
        {
            bool critical = true;
            gameRules.combat.rollSpellDamage(cast, &critical);
            criticals += critical ? 1 : 0;
        }

        return criticals;
    };

    // Luck far past the crit cap crits every roll; no Luck crits about one roll in twenty.
    dragon.luck = sorcerer.luck = 100000;
    CHECK_EQ(criticalShare(dragon, *pFlameBlast, rules.gameRules()), 200);
    CHECK_EQ(criticalShare(sorcerer, *pFireball, rules.gameRules()), 200);
    dragon.luck = sorcerer.luck = 0;
    CHECK(criticalShare(dragon, *pFlameBlast, rules.gameRules()) < 100);
    CHECK(criticalShare(sorcerer, *pFireball, rules.gameRules()) < 100);
    sorcerer.luck = 100000;
    CHECK_EQ(criticalShare(sorcerer, *pFireball, standardGameRules()), 0);

    // A missile's crit rides its impact event to MAW's status line, and only when it hits.
    GameplayCombatController combat;
    combat.recordPartyProjectileActorImpact(1, 0, 7, 120, 123, true, false, true);
    combat.recordPartyProjectileActorImpact(1, 0, 7, 120, 123, true, false, false);
    combat.recordPartyProjectileActorImpact(1, 0, 7, 0, 123, false, false, true);
    const std::vector<GameplayCombatController::CombatEvent> &events = combat.pendingCombatEvents();
    REQUIRE_EQ(events.size(), 3u);
    CHECK(events[0].critical);
    CHECK(GameplayCombatController::formatPartyProjectileActorImpactStatusText("Dragon", "Ogre", events[0],
        &rules.gameRules().combat).find("(CRIT!)") != std::string::npos);
    CHECK(GameplayCombatController::formatPartyProjectileActorImpactStatusText("Dragon", "Ogre", events[1],
        &rules.gameRules().combat).find("(CRIT!)") == std::string::npos);
    CHECK_FALSE(events[2].critical);
}
