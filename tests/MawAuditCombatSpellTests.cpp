// The combat and spell fixes of the MAW audit of 2026-10-24 (devdocs/maw/AUDIT_20261024_PLAN.md, stream 2): one test
// per audit id.
#include "doctest/doctest.h"
#include "game/gameplay/GameplayProjectileService.h"
#include "game/items/ItemEnchantTables.h"
#include "game/maps/SaveGame.h"
#include "game/outdoor/OutdoorWorldRuntime.h"
#include "game/party/EventSpellBuffs.h"
#include "game/party/Party.h"
#include "game/party/PartySpellSystem.h"
#include "game/party/SpellIds.h"
#include "game/rules/GameRules.h"
#include "game/rules/SpellRules.h"
#include "game/rules/maw/MawClassRules.h"
#include "game/rules/maw/MawClassSpells.h"
#include "game/rules/maw/MawCharacterSheet.h"
#include "game/rules/maw/MawCombatFormulas.h"
#include "game/rules/maw/MawCombatRules.h"
#include "game/rules/maw/MawDimensionMaps.h"
#include "game/rules/maw/MawGameState.h"
#include "game/rules/maw/MawMonsterRules.h"
#include "game/rules/maw/MawItemRules.h"
#include "game/rules/maw/MawRules.h"
#include "game/rules/maw/MawSpellFormulas.h"
#include "game/rules/maw/MawTexts.h"
#include "game/tables/MergedBaseTables.h"
#include "game/tables/ItemTable.h"
#include "game/tables/MonsterTable.h"
#include "tests/PartySpellTestHarness.h"
#include "tests/RegressionGameData.h"

#include <cmath>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <random>
#include <string>
#include <vector>

using namespace OpenYAMM::Game;

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
}

TEST_CASE("A bow's x2 against a kind of monster: Standard doubles the arrow, indoors too; MAW does not (CMB-1, D8)")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    MawRules maw(RulesetOptions{}, MawMapLevels{});
    CHECK(standardGameRules().combat.weaponKindMultiplierApplies());
    CHECK_FALSE(maw.gameRules().combat.weaponKindMultiplierApplies());

    // A bow of Dragon Slaying doubles against dragons; the service is what both worlds now ask for an arrow.
    uint16_t dragonSlaying = 0;

    for (uint16_t id = 1; id < 200 && dragonSlaying == 0; ++id)
    {
        const SpecialItemEnchantEntry *pEntry = gameData.specialItemEnchantTable.get(id);
        dragonSlaying = pEntry != nullptr && pEntry->kind == SpecialItemEnchantKind::DragonSlaying ? id : 0;
    }

    REQUIRE(dragonSlaying != 0);
    Character archer;
    archer.equipment.bow = 61;
    archer.equipmentRuntime.bow.specialEnchantId = dragonSlaying;
    GameplayProjectileService service;
    GameplayProjectileService::ProjectileState arrow;
    arrow.sourceKind = GameplayProjectileService::ProjectileState::SourceKind::Party;
    arrow.damage = 10;
    const uint32_t dragon = monsterKindFlag(MonsterKind::Dragon);
    const auto multiplier = [&](uint32_t kinds, const CombatRules &rules)
    {
        return service.resolvePartyProjectileDamageMultiplier(
            arrow, &archer, &gameData.itemTable, &gameData.specialItemEnchantTable, kinds, rules);
    };
    CHECK_EQ(multiplier(dragon, standardGameRules().combat), 2);
    CHECK_EQ(multiplier(0, standardGameRules().combat), 1);
    CHECK_EQ(multiplier(dragon, maw.gameRules().combat), 1);
}

TEST_CASE("MAW's Meditation adds no spell points of its own, only to Enlightenment's base (CLS-1)")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    MawRules maw(RulesetOptions{}, MawMapLevels{});
    maw.setClassMultiplierTable(&gameData.classMultiplierTable);
    const ClassMultiplierEntry *pSorcerer = gameData.classMultiplierTable.get("Sorcerer");
    REQUIRE(pSorcerer != nullptr);

    Character sorcerer;
    sorcerer.className = "Sorcerer";
    sorcerer.level = 20;
    sorcerer.personality = 30;
    const int pool = maw.gameRules().classes.baseMaxSpellPoints(sorcerer, *pSorcerer).value_or(0);
    sorcerer.skills["Meditation"] = {"Meditation", 4, SkillMastery::Expert};
    CHECK_EQ(maw.gameRules().classes.baseMaxSpellPoints(sorcerer, *pSorcerer).value_or(0), pool);

    // Enlightenment 10 at Master (1.5 % a point) grows the pool plus SPFactor x Meditation 4 x Expert 2.
    const double meditation = maw.classRules().enlightenmentMeditationMana(sorcerer);
    CHECK_EQ(meditation, doctest::Approx(pSorcerer->manaPerLevel * 4 * 2));
    sorcerer.skills["Enlightenment"] = {"Enlightenment", 10, SkillMastery::Master};
    sorcerer.maxSpellPoints = pool;
    maw.gameRules().skills.applyResourceBonuses(sorcerer);
    CHECK_EQ(sorcerer.magicalBonuses.maxSpellPoints, int((pool + meditation) * 0.015 * 10));

    // A class without spell points gains nothing from Meditation.
    Character knight;
    knight.className = "Knight";
    knight.skills["Meditation"] = {"Meditation", 4, SkillMastery::Expert};
    CHECK_EQ(maw.classRules().enlightenmentMeditationMana(knight), 0);
}

TEST_CASE("A held Haste aura outlasts a five-day journey: nobody arrives Weak (SPL-4)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    PartySeed seed;
    Character knight;
    knight.name = "Ariel";
    knight.className = "Knight";
    knight.level = 10;
    seed.members = {knight};
    Party party;
    party.seed(seed);
    party.setRules(&rules.gameRules());
    rules.setCurrentMap("oute3.odm");
    rules.gameRules().spells.updateAuras(party, 0.5f);

    // A pedestal's Haste is a held aura (Haste is spell 5).
    REQUIRE(tryApplyEventSpellBuffs(party, 5, 10, 3));
    REQUIRE(party.partyBuff(PartyBuffId::Haste) != nullptr);
    rules.gameRules().spells.updateAuras(party, 0.5f);

    // Travel advances five days in one step, as TravelRuntime does.
    party.advanceTimedStates(5.0f * 24.0f * 60.0f * 60.0f);
    CHECK_FALSE(party.member(0)->conditions.test(static_cast<size_t>(CharacterCondition::Weak)));
    CHECK(party.partyBuff(PartyBuffId::Haste) != nullptr);
}

namespace
{
Character auditMember(const std::string &className, uint32_t level)
{
    Character character;
    character.name = "Member";
    character.className = className;
    character.level = level;
    character.maxHealth = 1000;
    character.health = 1000;
    return character;
}
}

TEST_CASE("An Assassin's Mass Distortion takes no difficulty scale, only Earth twice (CMB-4)")
{
    const auto landed = [](const MawRules &rules)
    {
        Character assassin = auditMember("Assassin", 20);
        std::mt19937 rng(1);
        MonsterDamageHit hit;
        hit.amount = 400;
        hit.type = CombatDamageType::Earth;
        hit.resistance = 50;
        hit.resistances.earth = 50;
        hit.pMissileAttacker = &assassin;
        hit.missileSpellId = 44;
        hit.pRng = &rng;
        return rules.gameRules().combat.damageToMonster(hit);
    };
    MawRules normal(RulesetOptions{}, MawMapLevels{});
    RulesetOptions hellOptions;
    hellOptions.difficulty = RulesetDifficulty::Hell;
    MawRules hell(hellOptions, MawMapLevels{});
    CHECK_EQ(landed(hell), landed(normal));
}

TEST_CASE("MAW class perks read the trained school skill, not item and follower bonuses (CLS-2)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Character assassin = auditMember("Assassin", 20);
    assassin.skills["EarthMagic"] = {"EarthMagic", 10, SkillMastery::Master};
    const double trained = mawClassMeleeFlatDamage(rules, assassin);
    CHECK_EQ(trained, doctest::Approx(10 * (1 + 3)));
    assassin.itemSkillBonuses["EarthMagic"] = 10;
    CHECK_EQ(mawClassMeleeFlatDamage(rules, assassin), doctest::Approx(trained));
}

TEST_CASE("An Assassin's class-spell kill pays energy and a combo point; a living target pays nothing (CLS-3)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    PartySeed seed;
    seed.members = {auditMember("Assassin", 20)};
    Party party;
    party.seed(seed);
    party.setRules(&rules.gameRules());
    Character &assassin = *party.member(0);
    assassin.skills["AirMagic"] = {"AirMagic", 10, SkillMastery::Expert};
    assassin.maxSpellPoints = 200;
    assassin.spellPoints = 0;
    const ActorRulesetFacts target;
    PartyHitOnMonster hit;
    hit.damage = 50;
    hit.pTarget = &target;
    hit.spellId = 44;
    REQUIRE(mawClassSpell("Assassin", 44) != nullptr);

    rules.gameRules().combat.applyPartyHitEffects(party, hit);
    CHECK_EQ(assassin.spellPoints, 0);
    CHECK_EQ(rules.classRuntime(assassin).comboPoints, doctest::Approx(0.0));

    // Expert Subtlety (Air): (1 + 2) x 5 energy.
    hit.killed = true;
    rules.gameRules().combat.applyPartyHitEffects(party, hit);
    CHECK_EQ(assassin.spellPoints, 15);
    CHECK_EQ(rules.classRuntime(assassin).comboPoints, doctest::Approx(1.0));
}

TEST_CASE("MAW's Lifedrain leeches by its own rules, without Standard's third (SPL-7)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    CHECK(standardGameRules().combat.lifedrainHealsCasterThird());
    CHECK_FALSE(rules.gameRules().combat.lifedrainHealsCasterThird());
}

TEST_CASE("A weapon's enchantment damage joins the hit after Adamantite, which cuts the base only (ITM-L2)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    MonsterDamageHit hit;
    hit.amount = 100;
    hit.type = CombatDamageType::Physical;
    ElementalDamageBonuses elements;
    elements.fire = 100;
    hit.weaponElements = elements;
    hit.targetFacts.level = 255;
    hit.targetFacts.bossAffix = uint8_t(MawBossAffix::Adamantite);
    std::mt19937 rng(1);
    hit.pRng = &rng;

    // Adamantite takes 4 x 255^1.15 off the base, down to a quarter (25); the 100 fire comes after it, uncut.
    CHECK_EQ(rules.gameRules().combat.damageToMonster(hit), 125);
}

TEST_CASE("A monster's Pain Reflection returns the hit at ^0.85 under MAW, whole in Standard (FCOR-2-1)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    PartySeed seed;
    seed.members = {auditMember("Knight", 20)};
    Party party;
    party.seed(seed);
    party.setRules(&rules.gameRules());

    CHECK_EQ(standardGameRules().combat.reflectedDamage(party, 0, 5000, CombatDamageType::Physical), 5000);
    // No armour or resistance: 5000^0.85.
    CHECK_EQ(rules.gameRules().combat.reflectedDamage(party, 0, 5000, CombatDamageType::Physical),
        int(std::pow(5000.0, 0.85)));
}

TEST_CASE("A heal keeps negative HP: a member below zero wakes only once the deficit is healed (SKL-1, FSPS-2-2)")
{
    for (const bool maw : {false, true})
    {
        CAPTURE(maw);
        MawRules rules(RulesetOptions{}, MawMapLevels{});
        PartySeed seed;
        seed.members = {auditMember("Knight", 20)};
        Party party;
        party.seed(seed);

        if (maw)
        {
            party.setRules(&rules.gameRules());
        }

        Character &knight = *party.member(0);
        knight.endurance = 50;
        knight.health = -30;
        knight.conditions.set(size_t(CharacterCondition::Unconscious));
        party.healMember(0, 20);
        CHECK_EQ(knight.health, -10);
        CHECK(knight.conditions.test(size_t(CharacterCondition::Unconscious)));

        // A rebuild of the derived stats leaves the deficit alone.
        party.refreshDerivedState();
        CHECK_EQ(knight.health, -10);

        party.healMember(0, 15);
        CHECK_EQ(knight.health, 5);
        CHECK_FALSE(knight.conditions.test(size_t(CharacterCondition::Unconscious)));
    }
}

TEST_CASE("Black-potion stats (permanent bonuses) raise HP and SP as the stats they add to (SKL-2)")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    rules.setClassMultiplierTable(&gameData.classMultiplierTable);
    PartySeed seed;
    Character cleric = auditMember("Cleric", 20);
    cleric.endurance = 20;
    cleric.personality = 20;
    seed.members = {cleric};
    Party party;
    party.setClassMultiplierTable(&gameData.classMultiplierTable);
    party.seed(seed);
    party.setRules(&rules.gameRules());
    party.refreshDerivedState();
    const int health = Party::effectiveMaximumHealth(*party.member(0));
    const int mana = Party::effectiveMaximumSpellPoints(*party.member(0));

    // Pure Resilience and Pure Wisdom store +20 Endurance and Personality as permanent bonuses.
    party.member(0)->permanentBonuses.endurance += 20;
    party.member(0)->permanentBonuses.personality += 20;
    party.refreshDerivedState();
    CHECK_GT(Party::effectiveMaximumHealth(*party.member(0)), health);
    CHECK_GT(Party::effectiveMaximumSpellPoints(*party.member(0)), mana);
}

TEST_CASE("Only rules with party hit effects pay for finding the struck actor (STD3-4)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    CHECK_FALSE(standardGameRules().combat.usesPartyHitEffects());
    CHECK(rules.gameRules().combat.usesPartyHitEffects());
}

TEST_CASE("A quick-cast cure passes the dead, eradicated and petrified by (STD2-4)")
{
    PartySeed seed;
    seed.members = {auditMember("Cleric", 20), auditMember("Knight", 20), auditMember("Archer", 20)};
    Party party;
    party.seed(seed);

    // The diseased knight is dead; the diseased archer lives and is the cure's target.
    party.member(1)->conditions.set(size_t(CharacterCondition::DiseaseWeak));
    party.member(1)->conditions.set(size_t(CharacterCondition::Dead));
    party.member(1)->health = -100;
    party.member(2)->conditions.set(size_t(CharacterCondition::DiseaseWeak));
    CHECK_EQ(PartySpellSystem::quickCastCharacterTarget(party, 0, spellIdValue(SpellId::CureDisease), nullptr),
        std::optional<size_t>(2));

    // With only the dead one diseased, the cure finds nobody; Raise Dead still finds the dead.
    party.member(2)->conditions.reset(size_t(CharacterCondition::DiseaseWeak));
    CHECK_FALSE(PartySpellSystem::quickCastCharacterTarget(party, 0, spellIdValue(SpellId::CureDisease), nullptr));
    CHECK_EQ(PartySpellSystem::quickCastCharacterTarget(party, 0, spellIdValue(SpellId::RaiseDead), nullptr),
        std::optional<size_t>(1));
}

TEST_CASE("MAW casts Sunray indoors at any hour; Standard and the night outdoors refuse it (FSPS-2-1)")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const auto cast = [&](bool maw, bool indoor, int hour)
    {
        Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);

        if (maw)
        {
            party.setRules(&rules.gameRules());
        }

        OpenYAMM::Tests::PartySpellTestWorldRuntime world;
        world.bindParty(&party);
        world.setIndoorMap(indoor);
        world.setCurrentHour(hour);
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
        pCaster->skills["LightMagic"] = {"LightMagic", 10, SkillMastery::Grandmaster};
        pCaster->maxSpellPoints = 100000;
        pCaster->spellPoints = 100000;
        PartySpellCastRequest request;
        request.casterMemberIndex = 0;
        request.spellId = spellIdValue(SpellId::Sunray);
        request.targetActorIndex = target;
        return PartySpellSystem::castSpell(party, world, gameData.spellTable, request).status
            == PartySpellCastStatus::Succeeded;
    };

    CHECK(cast(true, true, 23));
    CHECK(cast(true, false, 12));
    CHECK_FALSE(cast(true, false, 23));
    CHECK_FALSE(cast(false, true, 12));
    CHECK(cast(false, false, 12));
}

TEST_CASE("MAW's Protection from Magic holds 50 charges at Grandmaster and adds no resistance (SPL-3)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    PartySeed seed;
    seed.members = {auditMember("Cleric", 20), auditMember("Knight", 20)};
    Party party;
    party.seed(seed);
    party.setRules(&rules.gameRules());
    rules.setCurrentMap("oute3.odm");
    const SpellRules &spells = rules.gameRules().spells;
    spells.updateAuras(party, 0.5f);
    const int fireResistance = party.member(1)->magicalBonuses.resistances.fire;

    // A temple's Protection from Magic (skill 7, Master) is a fixed aura.
    REQUIRE(spells.castSourceBuff(party, 75, BuffSource::Temple));
    spells.updateAuras(party, 0.5f);
    const PartyBuffState *pBuff = party.partyBuff(PartyBuffId::ProtectionFromMagic);
    REQUIRE(pBuff != nullptr);
    CHECK_EQ(pBuff->power, 50);
    CHECK(pBuff->skillMastery == SkillMastery::Grandmaster);
    CHECK_EQ(party.member(1)->magicalBonuses.resistances.fire, fireResistance);

    // Death and Eradication need Grandmaster; several in one frame all pass.
    CHECK(party.blockConditionWithProtectionFromMagic(CharacterCondition::Dead));
    CHECK(party.blockConditionWithProtectionFromMagic(CharacterCondition::Eradicated));
    CHECK(party.blockConditionWithProtectionFromMagic(CharacterCondition::Dead));
}

TEST_CASE("A party Fire Spike trap rolls MAW's spell damage under MAW, its own dice in Standard (SPL-5)")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    const int fireSpike = int(spellIdValue(SpellId::FireSpike));
    constexpr int TrapRoll = -1;
    const auto damage = [&]()
    {
        return GameplayProjectileService::partyWorldSpellDamage(
            &party, &gameData.spellTable, 0, fireSpike, 10, uint32_t(SkillMastery::Grandmaster), TrapRoll);
    };

    CHECK_EQ(damage(), TrapRoll);
    party.setRules(&rules.gameRules());
    CHECK_GT(damage(), 0);
}

TEST_CASE("Armageddon rolls MAW's spell damage on monsters under MAW, 50 + skill in Standard (SPL-6)")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);
    const auto damage = [&]()
    {
        return GameplayProjectileService::partyWorldSpellDamage(&party, &gameData.spellTable, 0,
            int(spellIdValue(SpellId::Armageddon)), 20, uint32_t(SkillMastery::Grandmaster), 50 + 20);
    };

    CHECK_EQ(damage(), 70);
    party.setRules(&rules.gameRules());
    CHECK_GT(damage(), 0);
}

TEST_CASE("MAW's Summon Wisp adds permanent Grandmaster wisps past the limit: Grandmaster up to ten (SPL-8)")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    CHECK_EQ(rules.gameRules().spells.extraPermanentWisps(SkillMastery::Normal), 0u);
    CHECK_EQ(rules.gameRules().spells.extraPermanentWisps(SkillMastery::Expert), 1u);
    CHECK_EQ(rules.gameRules().spells.extraPermanentWisps(SkillMastery::Master), 3u);
    CHECK_EQ(rules.gameRules().spells.extraPermanentWisps(SkillMastery::Grandmaster), 5u);
    CHECK_EQ(standardGameRules().spells.extraPermanentWisps(SkillMastery::Grandmaster), 0u);

    const auto summonedCount = [&](bool maw)
    {
        Party party = OpenYAMM::Tests::makeSpellRegressionParty(gameData);

        if (maw)
        {
            party.setRules(&rules.gameRules());
        }

        OpenYAMM::Tests::PartySpellTestWorldRuntime world;
        world.bindParty(&party);
        Character *pCaster = party.member(0);
        pCaster->skills["LightMagic"] = {"LightMagic", 10, SkillMastery::Grandmaster};
        size_t summoned = 0;

        for (int cast = 0; cast < 12; ++cast)
        {
            pCaster->maxSpellPoints = 100000;
            pCaster->spellPoints = 100000;
            pCaster->recoverySecondsRemaining = 0;
            PartySpellCastRequest request;
            request.casterMemberIndex = 0;
            request.spellId = spellIdValue(SpellId::SummonWisp);
            summoned += PartySpellSystem::castSpell(party, world, gameData.spellTable, request).status
                    == PartySpellCastStatus::Succeeded
                ? 1
                : 0;
        }

        return summoned;
    };

    CHECK_EQ(summonedCount(false), 5u);
    CHECK_EQ(summonedCount(true), 10u);
}

TEST_CASE("MAW's M&M6 projectiles: elemental missiles carry nothing extra, arrows take two Speed rolls (D2)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const CombatRules &maw = rules.gameRules().combat;
    const MonsterMissileRules fire = maw.monsterMissileRules("Fire");
    CHECK(fire.noSpecialAttack);
    CHECK(fire.noPainReflection);
    CHECK(fire.randomTarget);
    CHECK_FALSE(fire.secondSpeedRoll);
    CHECK(maw.monsterMissileRules("Arrow").secondSpeedRoll);
    CHECK(maw.monsterMissileRules("Spirit").secondSpeedRoll);
    CHECK_FALSE(maw.monsterMissileRules("ArrowF").secondSpeedRoll);
    CHECK_FALSE(maw.monsterMissileRules("Rock").randomTarget);
    CHECK_FALSE(standardGameRules().combat.monsterMissileRules("Fire").randomTarget);
    CHECK_FALSE(standardGameRules().combat.monsterMissileRules("Arrow").secondSpeedRoll);

    // An arrow lands about p x p of the time where a blow lands p.
    Character archer = auditMember("Archer", 20);
    archer.speed = 200;
    std::mt19937 rng(7);
    const auto hitShare = [&](const std::string &token)
    {
        int hits = 0;

        for (int trial = 0; trial < 4000; ++trial)
        {
            MonsterAttackOnCharacter attack;
            attack.pCharacter = &archer;
            attack.monsterLevel = 20;
            attack.missileToken = token;
            attack.pRng = &rng;
            hits += maw.characterEvades(attack) ? 0 : 1;
        }

        return hits / 4000.0;
    };
    const double blow = hitShare("");
    CHECK_LT(blow, 0.99);
    CHECK(hitShare("Arrow") == doctest::Approx(blow * blow).epsilon(0.1));
}

namespace
{
Party auditParty(MawRules &rules, std::vector<Character> members)
{
    PartySeed seed;
    seed.members = std::move(members);
    Party party;
    party.seed(seed);
    party.setRules(&rules.gameRules());
    return party;
}
}

TEST_CASE("Elementalist stacks fade after max(4 x delay, 128) ticks, halved at once and then each second (CLS-4)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Party party = auditParty(rules, {auditMember("Elementalist", 20)});
    OpenYAMM::Tests::PartySpellTestWorldRuntime world;
    world.bindParty(&party);
    MawClassRuntime &runtime = rules.classRuntime(*party.member(0));
    runtime.elementalStacks = 8;
    runtime.elementalLastDelayTicks = 100;
    // The class pass runs every quarter second.
    const auto advance = [&](int quarters)
    {
        for (int quarter = 0; quarter < quarters; ++quarter)
        {
            rules.gameRules().classes.update(party, world, 0.25f);
        }
    };

    // The window is 400 ticks, 3.125 seconds: still whole at 3, halved at 3.25, again a second later.
    advance(12);
    CHECK_EQ(runtime.elementalStacks, 8);
    advance(1);
    CHECK_EQ(runtime.elementalStacks, 4);
    advance(3);
    CHECK_EQ(runtime.elementalStacks, 4);
    advance(1);
    CHECK_EQ(runtime.elementalStacks, 2);
}

TEST_CASE("A vampire's night Preservation starts at 21:00 (CLS-6)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Character vampire = auditMember("Vampire", 20);
    vampire.raceId = 1;
    Party party = auditParty(rules, {vampire});
    OpenYAMM::Tests::PartySpellTestWorldRuntime world;
    world.bindParty(&party);
    world.setCurrentHour(20);
    rules.gameRules().classes.update(party, world, 0.5f);
    CHECK(party.characterBuff(0, CharacterBuffId::Preservation) == nullptr);
    world.setCurrentHour(21);
    rules.gameRules().classes.update(party, world, 0.5f);
    CHECK(party.characterBuff(0, CharacterBuffId::Preservation) != nullptr);
}

TEST_CASE("A Death Knight's arrows refill SP like blows (CLS-8, CMB-5)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Party party = auditParty(rules, {auditMember("DeathKnight", 20)});
    Character &knight = *party.member(0);
    knight.maxSpellPoints = 100;
    knight.spellPoints = 0;
    const ActorRulesetFacts target;
    PartyHitOnMonster arrow;
    arrow.damage = 50;
    arrow.pTarget = &target;
    rules.gameRules().combat.applyPartyHitEffects(party, arrow);
    CHECK_EQ(knight.spellPoints, 10);
}

TEST_CASE("Dragons refill no spell points while dead (CLS-9, SKL-6)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Character dragon = auditMember("Dragon", 20);
    dragon.raceId = 5;
    Party party = auditParty(rules, {dragon});
    OpenYAMM::Tests::PartySpellTestWorldRuntime world;
    world.bindParty(&party);
    Character &member = *party.member(0);
    member.maxSpellPoints = 60;
    member.spellPoints = 0;
    member.conditions.set(size_t(CharacterCondition::Dead));
    rules.gameRules().classes.update(party, world, 5.0f);
    CHECK_EQ(member.spellPoints, 0);
    member.conditions.reset(size_t(CharacterCondition::Dead));
    rules.gameRules().classes.update(party, world, 5.0f);
    CHECK_GT(member.spellPoints, 0);
}

TEST_CASE("The rules' runtime state moves with its character, not its address or slot (CLS-11, CMB-23, SKL-8)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Character first = auditMember("Assassin", 20);
    first.name = "First";
    Character second = auditMember("Elementalist", 20);
    second.name = "Second";
    Party party = auditParty(rules, {first, second});
    rules.classRuntime(*party.member(0)).comboPoints = 3;
    rules.classRuntime(*party.member(1)).elementalStacks = 5;
    party.member(1)->rulesetState.runtime.retaliationStacks = 2;

    // A copy (a load, a reallocation) carries the state; a fresh character has none.
    const Character copy = *party.member(1);
    CHECK_EQ(rules.classRuntime(copy).elementalStacks, 5);
    CHECK_EQ(copy.rulesetState.runtime.retaliationStacks, 2);
    CHECK_EQ(rules.classRuntime(auditMember("Knight", 20)).comboPoints, doctest::Approx(0.0));
}

TEST_CASE("An Assassin without energy can regain 15 by hitting: the refund is rolled before the payment (CLS-7)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Party party = auditParty(rules, {auditMember("Assassin", 20)});
    Character &assassin = *party.member(0);
    assassin.maxSpellPoints = 200;
    const ActorRulesetFacts target;
    PartyHitOnMonster blow;
    blow.damage = 50;
    blow.pTarget = &target;
    blow.melee = true;
    int refunds = 0;

    for (int trial = 0; trial < 300; ++trial)
    {
        assassin.spellPoints = 0;
        rules.gameRules().combat.applyPartyHitEffects(party, blow);
        refunds += assassin.spellPoints == 15 ? 1 : 0;
    }

    // At least the base 10 % chance.
    CHECK_GT(refunds, 10);
}

TEST_CASE("An Elementalist's Grandmaster Mass Distortion costs by level as anyone's (SPL-12)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    SpellEntry massDistortion;
    massDistortion.id = 44;
    const auto cost = [&](const std::string &className)
    {
        Character caster = auditMember(className, 100);
        caster.personality = 50;
        CharacterSpellCast cast;
        cast.pCaster = &caster;
        cast.pSpell = &massDistortion;
        cast.mastery = SkillMastery::Grandmaster;
        cast.skillLevel = 20;
        return rules.gameRules().spells.manaCost(cast, 20);
    };
    CHECK_EQ(cost("Elementalist"), cost("Sorcerer"));
}

TEST_CASE("An Elementalist's crowd control recovers against the four elements' average, not Learning (SPL-11)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    SpellEntry slow;
    slow.id = 35;
    Character elementalist = auditMember("Elementalist", 50);

    for (const char *pSchool : {"FireMagic", "AirMagic", "WaterMagic", "EarthMagic"})
    {
        elementalist.skills[pSchool] = {pSchool, 20, SkillMastery::Grandmaster};
    }

    CharacterSpellCast cast;
    cast.pCaster = &elementalist;
    cast.pSpell = &slow;
    cast.mastery = SkillMastery::Grandmaster;
    cast.skillLevel = 20;
    // Ascension 20 against the school's 20: the table's delay.
    CHECK_EQ(rules.gameRules().spells.recoveryTicks(cast, 200), 200);
}

TEST_CASE("Turn Undead on a living monster records no diminishing returns (SPL-10)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Party party = auditParty(rules, {auditMember("Cleric", 20)});
    ActorRulesetFacts facts;
    facts.level = 20;
    const uint32_t turnUndead = spellIdValue(SpellId::TurnUndead);
    const auto seconds = [&](bool undead)
    {
        return partyCrowdControlSeconds(&party, 0, turnUndead, 10, SkillMastery::Master, 0, facts, 20, undead,
            "oute3.odm", 3, 100.0);
    };

    CHECK_FALSE(seconds(false).has_value());
    // The living one left no history: the undead one's first cast takes the full time, as does a repeat on a
    // fresh target.
    const std::optional<float> first = seconds(true);
    REQUIRE(first.has_value());
    CHECK_GT(*first, 0.0f);
}

TEST_CASE("MAW's Master Spirit Lash reaches 384; Grandmaster and Standard keep 768 (SPL-13)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    CHECK_EQ(rules.gameRules().spells.spiritLashRadius(SkillMastery::Master), doctest::Approx(384.0f));
    CHECK_EQ(rules.gameRules().spells.spiritLashRadius(SkillMastery::Grandmaster), doctest::Approx(768.0f));
    CHECK_EQ(standardGameRules().spells.spiritLashRadius(SkillMastery::Master), doctest::Approx(768.0f));
}

TEST_CASE("MAW's Raise Dead lifts Eradication at Grandmaster only; Standard at any mastery (SPL-15)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    CHECK_FALSE(rules.gameRules().spells.raiseDeadLiftsEradication(SkillMastery::Master));
    CHECK(rules.gameRules().spells.raiseDeadLiftsEradication(SkillMastery::Grandmaster));
    CHECK(standardGameRules().spells.raiseDeadLiftsEradication(SkillMastery::Normal));
}

TEST_CASE("A weak potion's aura shows skill 0, not its negative skill wrapped round (SPL-17)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Character drinker = auditMember("Knight", 20);
    drinker.rulesetState.potionEffects.push_back({TimedPotionEffect::Kind::Aura, 50, 30, 600});
    Party party = auditParty(rules, {drinker});
    rules.gameRules().spells.updateAuras(party, 0.5f);
    const CharacterBuffState *pBuff = party.characterBuff(0, CharacterBuffId::Preservation);
    REQUIRE(pBuff != nullptr);
    CHECK_EQ(pBuff->skillLevel, 0u);
}

TEST_CASE("MAW's armour breakdown counts the printed AC of worn rings and amulets (ITM-A3)")
{
    REQUIRE_MESSAGE(OpenYAMM::Tests::regressionGameDataLoaded(), OpenYAMM::Tests::regressionGameDataFailure().c_str());
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    Party party = OpenYAMM::Tests::makeSpellRegressionParty(OpenYAMM::Tests::regressionGameData());
    party.setRules(&rules.gameRules());
    REQUIRE(party.itemTable() != nullptr);
    Character &member = *party.member(0);
    member.equipment = {};
    // Guinevere (AC 2) as the amulet and Hera (AC 6) on a ring finger.
    member.equipment.amulet = 2032;
    member.equipment.ring3 = 2049;
    CHECK_EQ(mawArmorBreakdown(rules, member, *party.itemTable()).pieces, 8);
    member.equipmentRuntime.ring3.broken = true;
    CHECK_EQ(mawArmorBreakdown(rules, member, *party.itemTable()).pieces, 2);
}

TEST_CASE("MAW's quick-cast crowd control takes the hostile whose debuff ends soonest; Standard the closest (SPL-18)")
{
    // Monster 1 is a living Human, 2 an Undead.
    const auto statsRow = [](int id)
    {
        std::vector<std::string> row(38);
        row[0] = std::to_string(id);
        row[1] = row[2] = "Monster " + std::to_string(id);
        row[3] = "10";
        row[4] = "100";
        row[5] = "5";
        row[10] = "Short";
        row[11] = "Normal";
        row[12] = "0";
        row[13] = "120";
        row[14] = "100";
        row[17] = "Phys";
        row[18] = "1d6";
        return row;
    };
    MonsterTable monsters;
    REQUIRE(monsters.loadStatsFromRows({statsRow(1), statsRow(2)}));
    MergedBolsterMonsterTable kinds;
    REQUIRE(kinds.loadFromRows({
        {"#", "Note", "Type", "ExtraType", "Creed", "Gender", "Style", "PrefMagic", "NoBounty", "Ranged", "Spells",
            "HPBySize", "Replicate", "Summons", "SummonId", "Extra", "MaxHP"},
        {"1", "Living", "Human", "", "Neutral", "", "Might", "", "-", "-", "-", "-", "-", "-", "", "", "300"},
        {"2", "Dead", "Undead", "", "Neutral", "", "Might", "", "-", "-", "-", "-", "-", "-", "", "", "300"},
    }));
    REQUIRE(monsters.applyKindFlagsFromBolsterMonsterTable(kinds));
    const int16_t living = 1;
    const int16_t undead = 2;
    REQUIRE(monsters.findStatsById(undead)->hasKind(MonsterKind::Undead));
    REQUIRE_FALSE(monsters.findStatsById(living)->hasKind(MonsterKind::Undead));
    MawRules maw(RulesetOptions{}, MawMapLevels{});
    OpenYAMM::Tests::PartySpellTestWorldRuntime world;
    world.bindMonsterTable(&monsters);
    world.setPartyPosition(0, 0, 0);

    // Four hostiles, closest first; the last is out of MAW's 4800 reach.
    const auto addHostile = [&world](float x, int16_t monsterId)
    {
        GameplayRuntimeActorState actor;
        actor.preciseX = x;
        actor.hostileToParty = true;
        actor.monsterId = monsterId;
        actor.currentHp = actor.maxHp = 10;
        return world.addActor(actor);
    };
    const size_t near = addHostile(100, living);
    const size_t middle = addHostile(200, living);
    const size_t far = addHostile(300, undead);
    addHostile(6000, living);

    GameplayActorInspectState nearState;
    nearState.slowRemainingSeconds = 30;
    nearState.controlMode = GameplayActorControlMode::Charm;
    nearState.controlRemainingSeconds = 20;
    world.setActorInspectState(near, nearState);
    GameplayActorInspectState middleState;
    middleState.slowRemainingSeconds = 5;
    middleState.controlMode = GameplayActorControlMode::Berserk;
    middleState.controlRemainingSeconds = 50;
    world.setActorInspectState(middle, middleState);
    GameplayActorInspectState farState;
    farState.slowRemainingSeconds = 10;
    world.setActorInspectState(far, farState);

    const auto target = [&world](const SpellRules &rules, SpellId spell)
    {
        return PartySpellSystem::quickCastActorTarget(world, rules, spellIdValue(spell));
    };
    const SpellRules &standard = standardSpellRules();
    const SpellRules &rules = maw.gameRules().spells;
    CHECK_EQ(target(standard, SpellId::Slow), std::optional<size_t>(near));
    CHECK_EQ(target(rules, SpellId::Slow), std::optional<size_t>(middle));
    // A Berserk debuff is no Charm: the middle one is charmed for 0 s, and it is closer than the uncharmed far one.
    CHECK_EQ(target(rules, SpellId::Charm), std::optional<size_t>(middle));
    CHECK_EQ(target(rules, SpellId::Berserk), std::optional<size_t>(near));
    CHECK_EQ(target(rules, SpellId::ControlUndead), std::optional<size_t>(far));
    // Spells MAW does not spread keep the closest.
    CHECK_EQ(target(rules, SpellId::FireBolt), std::optional<size_t>(near));
}

TEST_CASE("Under MAW a heal scroll heals the engine's amount; a Shared Life scroll MAW's table at its skill (FSPS-2-3)")
{
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Character reader = auditMember("Cleric", 40);
    reader.personality = 500;
    CharacterSpellCast cast;
    cast.pCaster = &reader;
    cast.mastery = SkillMastery::Master;
    cast.skillLevel = 7;
    const SpellRules &spells = rules.gameRules().spells;

    cast.pSpell = gameData.spellTable.findById(spellIdValue(SpellId::Heal));
    REQUIRE(cast.pSpell != nullptr);
    CHECK(spells.healAmount(cast).has_value());
    cast.fromScroll = true;
    CHECK_FALSE(spells.healAmount(cast).has_value());

    // Shared Life at Master 7: base + per point x 7 / 2 - 3 x 7, nothing of the reader's Personality.
    cast.pSpell = gameData.spellTable.findById(spellIdValue(SpellId::SharedLife));
    REQUIRE(cast.pSpell != nullptr);
    const std::optional<MawHealSpell> table =
        mawHealSpell(spellIdValue(SpellId::SharedLife), SkillMastery::Master, false);
    REQUIRE(table.has_value());
    const std::optional<int> scrollHeal = int(mawRound(std::max(table->base + table->perPoint * 3.5 - 21, 0.0)));
    CHECK_EQ(spells.healAmount(cast), scrollHeal);
    cast.fromScroll = false;
    CHECK_NE(spells.healAmount(cast), scrollHeal);
}

TEST_CASE("MAW's crowd-control and Elementalist mana costs stop at 65000 (FSPS-2-5)")
{
    CHECK_EQ(mawSpellManaCost(MawSpellCategory::CrowdControl, 50, 160, SkillMastery::Grandmaster, 1), 65000);
    CHECK_EQ(mawSpellManaCost(MawSpellCategory::CrowdControl, 50, 500, SkillMastery::Grandmaster, 1), 65000);
    CHECK_LT(mawSpellManaCost(MawSpellCategory::CrowdControl, 50, 20, SkillMastery::Grandmaster, 1), 65000);

    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Character elementalist = auditMember("Elementalist", 100);
    // An Elementalist's Ascension is the four elements' average.
    for (const char *pSchool : {"FireMagic", "AirMagic", "WaterMagic", "EarthMagic"})
    {
        elementalist.skills[pSchool] = {pSchool, 300, SkillMastery::Grandmaster};
    }

    Party party = auditParty(rules, {elementalist});
    rules.classRuntime(*party.member(0)).elementalStacks = 20;
    CharacterSpellCast cast;
    cast.pCaster = party.member(0);
    cast.pSpell = gameData.spellTable.findById(spellIdValue(SpellId::FireBolt));
    cast.mastery = SkillMastery::Grandmaster;
    cast.skillLevel = 60;
    REQUIRE(cast.pSpell != nullptr);
    CHECK_EQ(rules.gameRules().spells.manaCost(cast, 2), 65000);
}

TEST_CASE("A released Preservation aura ends for every member but one whose own potion keeps it (FSPS-2-7)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Character cleric = auditMember("Cleric", 20);
    cleric.skills["SpiritMagic"] = {"SpiritMagic", 10, SkillMastery::Master};
    Character drinker = auditMember("Knight", 20);
    drinker.rulesetState.potionEffects.push_back({TimedPotionEffect::Kind::Aura, 50, 100, 600});
    Party party = auditParty(rules, {cleric, drinker, auditMember("Knight", 20)});
    const SpellRules &spells = rules.gameRules().spells;

    rules.state().auraHolders[50] = 0;
    spells.updateAuras(party, 0.5f);

    for (size_t memberIndex = 0; memberIndex < 3; ++memberIndex)
    {
        CHECK(party.characterBuff(memberIndex, CharacterBuffId::Preservation) != nullptr);
    }

    rules.state().auraHolders.erase(50);
    spells.updateAuras(party, 0.5f);
    CHECK(party.characterBuff(0, CharacterBuffId::Preservation) == nullptr);
    CHECK(party.characterBuff(1, CharacterBuffId::Preservation) != nullptr);
    CHECK(party.characterBuff(2, CharacterBuffId::Preservation) == nullptr);
}

TEST_CASE("Armsmaster's mastery lines: speed from Master, 1.5 damage at Grandmaster (FSPS-2-8)")
{
    std::ifstream input(std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/rulesets/maw/data/texts.yml");
    const std::string yaml((std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());
    MawTextData texts;
    std::string error;
    REQUIRE_MESSAGE(texts.loadFromYaml(yaml, error), error);
    MawRules rules(RulesetOptions{}, MawMapLevels{}, {}, {}, {}, texts);
    Character knight = auditMember("Knight", 20);
    knight.skills["Armsmaster"] = {"Armsmaster", 10, SkillMastery::Expert};
    Party party = auditParty(rules, {knight});
    const SkillTooltipText text = rules.gameRules().skills.skillTooltip(party, *party.member(0), "Armsmaster", {});
    CHECK_EQ(text.masteryLines[1], "Each point adds 1 damage, 1 attack");
    CHECK_EQ(text.masteryLines[2], "Each point adds 1 damage, 1 attack, 1 % speed");
    CHECK_EQ(text.masteryLines[3], "Each point adds 1.5 damage, 1 attack, 1 % speed");
}

TEST_CASE("Dimension affix 26 slows the attack itself, not only the HUD's number, and only once (CMB-6)")
{
    std::ifstream input(
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/rulesets/maw/data/dimension_maps.yml");
    const std::string yaml{std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
    MawDimensionData dimensions;
    std::string error;
    REQUIRE_MESSAGE(dimensions.loadFromYaml(yaml, error), error);
    MawRules rules(RulesetOptions{}, MawMapLevels{}, MawItemData{}, MawPromotionData{}, MawCraftingData{},
        MawTextData{}, dimensions);
    const ItemTable items;
    const Character fighter = auditMember("Knight", 20);
    const auto delay = [&]()
    {
        return mawCharacterAttackDelay(rules, fighter, items, CharacterAttackMode::Melee, 0).delay;
    };
    const int plain = delay();

    MawDimensionRun run;
    run.affixes = {int(MawMapAffix::PlayerAttackSpeed), 0, 0, 0};
    run.power = 10;
    rules.state().dimensionRuns["6d02.blv"] = run;
    rules.setCurrentMap("6d02.blv");
    const std::optional<double> slower = rules.mapAffix(MawMapAffix::PlayerAttackSpeed);
    REQUIRE(slower.has_value());
    REQUIRE(*slower > 0);
    const int slowed = int(mawRound(plain / (1 - *slower / 100)));
    CHECK_GT(slowed, plain);
    CHECK_EQ(delay(), slowed);
    CHECK_EQ(rules.gameRules().combat.characterAttackRecoveryTicks(fighter, CharacterAttackMode::Melee, items,
                 nullptr, nullptr),
        std::optional<int>(slowed));
}

TEST_CASE("Beyond Madness's death ledger counts every hit that lands, not only monsters' (CHM-2)")
{
    RulesetOptions options;
    options.challengeMode = RulesetChallengeMode::BeyondMadness;
    MawRules madness(options, MawMapLevels{});
    const std::filesystem::path ledger =
        std::filesystem::temp_directory_path() / ("maw_ledger_chm2_" + std::to_string(std::random_device{}()) + ".txt");
    madness.setMadnessLedgerFile(ledger);
    madness.setRandomRootSeed(77);
    Party party = auditParty(madness, {auditMember("Knight", 20)});
    const ExperienceRules &experience = madness.gameRules().experience;
    CHECK_FALSE(experience.deathPendingSeconds(0).has_value());

    // A fall or a trap: no monster in it.
    REQUIRE(party.applyDamageToMember(0, 10, "Fall"));
    CHECK(experience.deathPendingSeconds(0).has_value());
    std::error_code error;
    std::filesystem::remove(ledger, error);
}

TEST_CASE("The Seraphim's flat damage cut reads the balance model of the party's size (CMB-8)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    rules.state().addBankedExperience(3.0e5, 1);
    Character seraphim = auditMember("Seraphim", 200);
    seraphim.skills["SpiritMagic"] = {"SpiritMagic", 40, SkillMastery::Master};
    // The model's only party-size term is cover: a covering tank survives twice as long, and since MAW 249b00da a solo
    // character's halved cover damage is worth the same, so both sizes read the same cut.
    REQUIRE(rules.state().totalLevel() > 15);
    REQUIRE(rules.state().totalLevel() < 40);
    const double solo = mawClassDefense(rules, seraphim, 1).flatReduction;
    const double party = mawClassDefense(rules, seraphim, 5).flatReduction;
    CHECK_GT(solo, 0);
    CHECK_GT(party, 0);
    CHECK_EQ(solo, doctest::Approx(party));
}

TEST_CASE("A dragon's breath takes the mean of two rolls, so very low breaths are rare (CMB-11)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    ItemTable items;
    Character dragon = auditMember("Dragon", 20);
    dragon.raceId = 5;
    dragon.skills["DragonAbility"] = {"DragonAbility", 10, SkillMastery::Expert};
    std::mt19937 rng(11);
    CharacterAttackOnMonster context;
    context.pCharacter = &dragon;
    context.pItemTable = &items;
    context.minimumDamage = 0;
    context.maximumDamage = 1000;
    context.pRng = &rng;
    constexpr int Breaths = 4000;
    int low = 0;

    for (int breath = 0; breath < Breaths; ++breath)
    {
        CharacterAttackResult attack;
        attack.mode = CharacterAttackMode::DragonBreath;
        attack.canAttack = true;
        rules.gameRules().combat.resolveCharacterAttack(attack, context);
        low += attack.damage < 75 ? 1 : 0;
    }

    // One roll lands below 75 at least 6 % of the time (a roll under 60, x 1.25 at most); the mean of two under 100 at
    // most 2 % (x 0.75 at least).
    CHECK_LT(low, Breaths * 4 / 100);
}

TEST_CASE("The leech floor reads the full Speed and keeps whole under dimension affix 32 (CMB-13, CMB-15)")
{
    REQUIRE_MESSAGE(OpenYAMM::Tests::regressionGameDataLoaded(), OpenYAMM::Tests::regressionGameDataFailure().c_str());
    std::ifstream input(
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/rulesets/maw/data/dimension_maps.yml");
    const std::string yaml{std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
    MawDimensionData dimensions;
    std::string error;
    REQUIRE_MESSAGE(dimensions.loadFromYaml(yaml, error), error);
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData(), MawPromotionData{}, MawCraftingData{},
        MawTextData{}, dimensions);
    Party party = OpenYAMM::Tests::makeSpellRegressionParty(OpenYAMM::Tests::regressionGameData());
    party.setRules(&rules.gameRules());
    Character &vampire = *party.member(0);
    vampire.className = "Knight";
    vampire.equipment = {};
    // Foulfang leeches 10 % of melee.
    vampire.equipment.mainHand = 508;
    vampire.maxHealth = 5000;
    ActorRulesetFacts target;
    target.level = 20;
    target.maxHp = 1000;
    PartyHitOnMonster hit;
    hit.memberIndex = 0;
    hit.pTarget = &target;
    hit.damage = 1;
    hit.melee = true;
    // A one-point hit: the floor, a fifth of the share per 100 recovery, is the whole heal.
    const auto healed = [&]()
    {
        vampire.health = 100;
        rules.gameRules().combat.applyPartyHitEffects(party, hit);
        return vampire.health - 100;
    };
    const int plain = healed();
    REQUIRE_GT(plain, 0);

    // A faster attacker's floor is smaller: Speed from items and black potions counts (CMB-13).
    vampire.permanentBonuses.speed = 400;
    const int fast = healed();
    CHECK_LT(fast, plain);
    vampire.permanentBonuses.speed = 0;

    // Affix 32 cuts the heal, not the floor (CMB-15).
    MawDimensionRun run;
    run.affixes = {int(MawMapAffix::Leech), 0, 0, 0};
    run.power = 10;
    rules.state().dimensionRuns["6d02.blv"] = run;
    rules.setCurrentMap("6d02.blv");
    REQUIRE(rules.mapAffix(MawMapAffix::Leech).has_value());
    CHECK_EQ(healed(), plain);
}

TEST_CASE("An Assassin's Subtlety stacks speed their spells too (CMB-19)")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Character assassin = auditMember("Assassin", 30);
    assassin.skills["AirMagic"] = {"AirMagic", 20, SkillMastery::Master};
    Party party = auditParty(rules, {assassin});
    CharacterSpellCast cast;
    cast.pCaster = party.member(0);
    cast.pItemTable = &gameData.itemTable;
    cast.pSpell = gameData.spellTable.findById(spellIdValue(SpellId::FireBolt));
    cast.mastery = SkillMastery::Master;
    cast.skillLevel = 20;
    REQUIRE(cast.pSpell != nullptr);
    const SpellRules &spells = rules.gameRules().spells;
    const int calm = spells.recoveryTicks(cast, 100);
    rules.classRuntime(*party.member(0)).subtletyStacks = 5;
    CHECK_LT(spells.recoveryTicks(cast, 100), calm);
}

TEST_CASE("Hazards take legendaries 18 and 22's cut and dimension affix 2's crits as traps do (CMB-14)")
{
    std::ifstream input(
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/rulesets/maw/data/dimension_maps.yml");
    const std::string yaml{std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
    MawDimensionData dimensions;
    std::string error;
    REQUIRE_MESSAGE(dimensions.loadFromYaml(yaml, error), error);
    MawRules rules(RulesetOptions{}, MawMapLevels{}, MawItemData{}, MawPromotionData{}, MawCraftingData{},
        MawTextData{}, dimensions);
    rules.state().addBankedExperience(3.0e6, 1);
    Party party = auditParty(rules, {auditMember("Knight", 50)});
    const CombatRules &combat = rules.gameRules().combat;
    const int plain = combat.environmentDamage(party, 0, 7, CombatDamageType::Fire, true);
    REQUIRE_GT(plain, 20);

    // Legendary 18: x 0.9.
    Character &wearer = *party.member(0);
    wearer.equipment.amulet = 1;
    wearer.equipmentRuntime.amulet.rulesetFields.legendaryAffixId = 18;
    // The cut comes before the mitigation's rounding, so the result may sit one point off plain x 0.9.
    CHECK(std::abs(combat.environmentDamage(party, 0, 7, CombatDamageType::Fire, true) - plain * 0.9) <= 1);
    wearer.equipment.amulet = 0;
    wearer.equipmentRuntime.amulet.rulesetFields.legendaryAffixId = 0;

    // Affix 2 doubles some hits; an outdoor fall's own number too.
    MawDimensionRun run;
    run.affixes = {int(MawMapAffix::MonsterCritical), 0, 0, 0};
    run.power = 10;
    rules.state().dimensionRuns["6d02.blv"] = run;
    rules.setCurrentMap("6d02.blv");
    REQUIRE(rules.mapAffix(MawMapAffix::MonsterCritical).has_value());
    bool doubled = false;

    for (int fall = 0; fall < 400 && !doubled; ++fall)
    {
        const int damage = combat.environmentDamage(party, 0, 7, CombatDamageType::Physical, false);
        CHECK((damage == 7 || damage == 14));
        doubled = damage == 14;
    }

    CHECK(doubled);
}

TEST_CASE("Weak halves a MAW arrow's own roll, not the bow's enchantment; Standard's caller halves it all (CMB-16)")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Character archer = auditMember("Archer", 20);
    archer.skills["Bow"] = {"Bow", 10, SkillMastery::Expert};
    archer.equipment.bow = 61;
    const auto shot = [&](bool weak, uint16_t special)
    {
        archer.conditions.set(size_t(CharacterCondition::Weak), weak);
        archer.equipmentRuntime.bow.specialEnchantId = special;
        std::mt19937 rng(5);
        CharacterAttackOnMonster context;
        context.pCharacter = &archer;
        context.pItemTable = &gameData.itemTable;
        context.minimumDamage = 100;
        context.maximumDamage = 100;
        context.pRng = &rng;
        CharacterAttackResult attack;
        attack.mode = CharacterAttackMode::Bow;
        attack.canAttack = true;
        rules.gameRules().combat.resolveCharacterAttack(attack, context);
        return attack.damage;
    };
    // Special 15 adds a flat Body enchantment to every arrow.
    const int plain = shot(false, 0);
    const int enchanted = shot(false, 15);
    REQUIRE_GT(enchanted, plain);
    CHECK_EQ(shot(true, 15), int(mawRound(plain * 0.5)) + enchanted - plain);
    CHECK_FALSE(rules.gameRules().combat.callerHalvesWeakMissile(CharacterAttackMode::Bow));
    CHECK(rules.gameRules().combat.callerHalvesWeakMissile(CharacterAttackMode::Wand));
    CHECK(standardGameRules().combat.callerHalvesWeakMissile(CharacterAttackMode::Bow));
}

TEST_CASE("A weapon artifact's on-hit damage joins after Adamantite, resisted by its own kind (ITM-A7)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    std::mt19937 rng(3);
    Character attacker = auditMember("Knight", 50);
    const auto landed = [&](int fireResistance, int lateFire)
    {
        MonsterDamageHit hit;
        hit.amount = 1000;
        hit.type = CombatDamageType::Physical;
        hit.weaponElements = ElementalDamageBonuses{};
        hit.resistances.fire = fireResistance;
        hit.targetFacts.level = 100;
        hit.targetFacts.bossAffix = uint8_t(MawBossAffix::Adamantite);
        hit.pMeleeAttacker = &attacker;
        hit.targetCurrentHp = 100000;
        hit.pRng = &rng;
        hit.lateDamage[size_t(CombatDamageType::Fire)] = lateFire;
        return rules.gameRules().combat.damageToMonster(hit);
    };
    const int blow = landed(0, 0);
    // Adamantite cut the blow, not the artifact's 100 fire.
    CHECK_LT(blow, 1000);
    CHECK_EQ(landed(0, 100), blow + 100);
    // Fire resistance takes its share of the artifact's damage only.
    const int resisted = landed(100, 100) - blow;
    CHECK_GT(resisted, 0);
    CHECK_LT(resisted, 100);
}

TEST_CASE("Ethric's Staff spares the Lich class only; Horn of Ros and Ghost Ring buffs never lapse (ITM-A8, ITM-A9)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    Character lich = auditMember("Lich", 30);
    lich.equipment.mainHand = 1317;
    Character lichKing = auditMember("LichKing", 30);
    lichKing.equipment.mainHand = 1317;
    Character ringBearer = auditMember("Knight", 30);
    ringBearer.equipment.ring1 = 1347;
    InventoryItem horn;
    horn.objectDescriptionId = 2055;
    ringBearer.inventory.push_back(horn);
    Party party = auditParty(rules, {lich, lichKing, ringBearer});
    OpenYAMM::Tests::PartySpellTestWorldRuntime world;
    world.bindParty(&party);
    const CombatRules &combat = rules.gameRules().combat;
    combat.updateCombat(party, world, 0.016f);
    world.advanceGameMinutes(5);
    combat.updateCombat(party, world, 0.016f);
    CHECK_EQ(party.members()[0].health, 1000);
    CHECK_EQ(party.members()[1].health, 997);

    // Master power 3, renewed every game minute to at least three more: it never runs out while held.
    const PartyBuffState *pDetectLife = party.partyBuff(PartyBuffId::DetectLife);
    REQUIRE(pDetectLife != nullptr);
    CHECK_EQ(pDetectLife->skillMastery, SkillMastery::Master);

    for (int minute = 0; minute < 6; ++minute)
    {
        party.advanceTimedStates(1.9f);
        world.advanceGameMinutes(1);
        combat.updateCombat(party, world, 0.016f);
        CHECK(party.hasPartyBuff(PartyBuffId::DetectLife));
        CHECK(party.hasCharacterBuff(2, CharacterBuffId::Preservation));
        CHECK_GT(party.partyBuff(PartyBuffId::DetectLife)->remainingSeconds, 5.9f);
    }
}

TEST_CASE("The alchemist's slot follows a leaving member; a broken Lichs' weapon is no faster (ROB-2-3, FITM-2-7)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Party party = auditParty(rules, {auditMember("Knight", 20), auditMember("Knight", 20), auditMember("Knight", 20)});
    const SpellRules &spells = rules.gameRules().spells;
    rules.state().alchemistMember = 2;
    spells.memberLeaving(party, 0);
    CHECK_EQ(rules.state().alchemistMember, 1);
    spells.memberLeaving(party, 1);
    CHECK_EQ(rules.state().alchemistMember, -1);

    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    Character sorcerer = auditMember("Sorcerer", 20);
    sorcerer.skills["FireMagic"] = {"FireMagic", 10, SkillMastery::Expert};
    CharacterSpellCast cast;
    cast.pCaster = &sorcerer;
    cast.pItemTable = &gameData.itemTable;
    cast.pSpell = gameData.spellTable.findById(spellIdValue(SpellId::FireBolt));
    cast.mastery = SkillMastery::Expert;
    cast.skillLevel = 10;
    REQUIRE(cast.pSpell != nullptr);
    const int plain = spells.recoveryTicks(cast, 100);
    sorcerer.equipment.mainHand = 1;
    sorcerer.equipmentRuntime.mainHand.specialEnchantId = 40;
    CHECK_LT(spells.recoveryTicks(cast, 100), plain);
    sorcerer.equipmentRuntime.mainHand.broken = true;
    CHECK_EQ(spells.recoveryTicks(cast, 100), plain);
}

TEST_CASE("A Shielded monster halves MAW spells but not MAW arrows; Standard halves both (CMB-21)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    GameplayProjectileService service;
    const auto impact = [&](const CombatRules &combat, int spellId)
    {
        GameplayProjectileService::ProjectileState projectile = {};
        projectile.projectileId = 42;
        projectile.sourceKind = GameplayProjectileService::ProjectileState::SourceKind::Party;
        projectile.damage = 20;
        projectile.spellId = spellId;
        GameplayProjectileService::ProjectileDirectActorImpactInput input = {};
        input.damageMultiplier = 1;
        input.pCombatRules = &combat;
        input.halfIncomingMissileDamage = true;
        return service.buildProjectileDirectActorImpact(projectile, input).damage;
    };
    CHECK_EQ(impact(standardGameRules().combat, 0), 10);
    CHECK_EQ(impact(standardGameRules().combat, 2), 10);
    CHECK_EQ(impact(rules.gameRules().combat, 0), 20);
    CHECK_EQ(impact(rules.gameRules().combat, 2), 10);
}

TEST_CASE("An Elementalist learns from any element spell on a hostile monster, not from a friendly one (FCOR-2-5)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Party party = auditParty(rules, {auditMember("Elementalist", 20)});
    OpenYAMM::Tests::PartySpellTestWorldRuntime world;
    world.bindParty(&party);
    GameplayRuntimeActorState friendly;
    friendly.currentHp = friendly.maxHp = 100;
    const size_t friendlyIndex = world.addActor(friendly);
    GameplayRuntimeActorState hostile = friendly;
    hostile.hostileToParty = true;
    const size_t hostileIndex = world.addActor(hostile);
    ActorRulesetFacts target;
    target.level = 20;
    target.maxHp = 100;
    const auto progress = [&](uint32_t spellId, size_t actorIndex)
    {
        party.member(0)->rulesetState.elementalProgress = {};
        PartyHitOnMonster hit;
        hit.memberIndex = 0;
        hit.pTarget = &target;
        hit.damage = 10;
        hit.spellId = spellId;
        hit.pWorld = &world;
        hit.targetActorIndex = actorIndex;
        rules.gameRules().combat.applyPartyHitEffects(party, hit);
        return party.members()[0].rulesetState.elementalProgress;
    };
    // Fire Aura (4) is no offensive spell; it still teaches Fire on a hostile monster.
    CHECK_GT(progress(4, hostileIndex)[0], 0);
    CHECK_EQ(progress(4, friendlyIndex)[0], 0);
    CHECK_GT(progress(2, hostileIndex)[0], 0);
    CHECK_EQ(progress(2, friendlyIndex)[0], 0);
}

TEST_CASE("The Elementalist's idle window comes from the last offensive cast, not any delay read since (FCOR-2-20)")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Character elementalist = auditMember("Elementalist", 20);
    elementalist.skills["FireMagic"] = {"FireMagic", 10, SkillMastery::Expert};
    Party party = auditParty(rules, {elementalist});
    party.setItemTable(&gameData.itemTable);
    const SpellRules &spells = rules.gameRules().spells;
    const MawClassRuntime &runtime = rules.classRuntime(*party.member(0));

    // Reading a spell's delay (the stats page, the leech floor) sets nothing.
    CharacterSpellCast cast;
    cast.pCaster = party.member(0);
    cast.pItemTable = &gameData.itemTable;
    cast.pSpell = gameData.spellTable.findById(spellIdValue(SpellId::FireBolt));
    cast.mastery = SkillMastery::Expert;
    cast.skillLevel = 10;
    REQUIRE(cast.pSpell != nullptr);
    spells.recoveryTicks(cast, 100);
    CHECK_EQ(runtime.elementalLastDelayTicks, 0);

    // An offensive cast records its own delay; a utility cast after it changes nothing.
    spells.afterCast(party, 0, spellIdValue(SpellId::FireBolt), gameData.spellTable, false, true);
    const int window = runtime.elementalLastDelayTicks;
    CHECK_GT(window, 0);
    spells.afterCast(party, 0, spellIdValue(SpellId::TorchLight), gameData.spellTable, false, true);
    cast.pSpell = gameData.spellTable.findById(spellIdValue(SpellId::TorchLight));
    spells.recoveryTicks(cast, 500);
    CHECK_EQ(runtime.elementalLastDelayTicks, window);
}

TEST_CASE("A Regenerating boss counts the party's hits with itself, and a save keeps them (FCOR-2-6)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Party party = auditParty(rules, {auditMember("Knight", 20)});
    OpenYAMM::Tests::PartySpellTestWorldRuntime world;
    world.bindParty(&party);
    GameplayRuntimeActorState boss;
    boss.currentHp = boss.maxHp = 1000;
    boss.hostileToParty = true;
    boss.rulesetFacts.level = 50;
    boss.rulesetFacts.bossAffix = uint8_t(MawBossAffix::Regenerating);
    const size_t bossIndex = world.addActor(boss);
    PartyHitOnMonster hit;
    hit.memberIndex = 0;
    hit.pTarget = &world.actor(bossIndex).rulesetFacts;
    hit.damage = 10;
    hit.melee = true;
    hit.pWorld = &world;
    hit.targetActorIndex = bossIndex;
    rules.gameRules().combat.applyPartyHitEffects(party, hit);
    rules.gameRules().combat.applyPartyHitEffects(party, hit);
    CHECK_EQ(world.actor(bossIndex).rulesetFacts.regeneratingHits, 2);

    OutdoorWorldRuntime::MapActorState actor;
    actor.rulesetFacts = world.actor(bossIndex).rulesetFacts;
    GameSaveData save;
    save.mapFileName = "oute3.odm";
    save.hasOutdoorRuntimeState = true;
    save.outdoorWorld.mapActors.push_back(actor);
    save.outdoorWorldStates[save.mapFileName] = save.outdoorWorld;
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "openyamm_regenerating_hits.oysav";
    std::string error;
    REQUIRE_MESSAGE(saveGameDataToPath(path, save, error), error.c_str());
    const std::optional<GameSaveData> restored = loadGameDataFromPath(path, error);
    std::filesystem::remove(path);
    REQUIRE_MESSAGE(restored.has_value(), error.c_str());
    REQUIRE_EQ(restored->outdoorWorldStates.at("oute3.odm").mapActors.size(), 1u);
    CHECK_EQ(restored->outdoorWorldStates.at("oute3.odm").mapActors[0].rulesetFacts.regeneratingHits, 2);
}

TEST_CASE("An Assassin's blow on a monster that is not hostile pays no energy and builds nothing (FCOR-2-21)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Character assassin = auditMember("Assassin", 20);
    assassin.maxSpellPoints = 200;
    assassin.spellPoints = 200;
    Party party = auditParty(rules, {assassin});
    OpenYAMM::Tests::PartySpellTestWorldRuntime world;
    world.bindParty(&party);
    GameplayRuntimeActorState peasant;
    peasant.currentHp = peasant.maxHp = 100;
    const size_t peasantIndex = world.addActor(peasant);
    GameplayRuntimeActorState hostile = peasant;
    hostile.hostileToParty = true;
    const size_t hostileIndex = world.addActor(hostile);
    ActorRulesetFacts target;
    target.level = 20;
    target.maxHp = 100;
    const MawClassRuntime &runtime = rules.classRuntime(*party.member(0));
    const auto blow = [&](size_t actorIndex)
    {
        party.member(0)->spellPoints = 200;
        PartyHitOnMonster hit;
        hit.memberIndex = 0;
        hit.pTarget = &target;
        hit.damage = 10;
        hit.melee = true;
        hit.pWorld = &world;
        hit.targetActorIndex = actorIndex;
        rules.gameRules().combat.applyPartyHitEffects(party, hit);
        return party.members()[0].spellPoints;
    };
    // The 15-energy refund cannot lift a full pool, so what is left shows the payment.
    CHECK_EQ(blow(peasantIndex), 200);
    CHECK_EQ(runtime.comboPoints, doctest::Approx(0));
    CHECK_LT(blow(hostileIndex), 200);
    CHECK_EQ(runtime.comboPoints, doctest::Approx(1));
}

TEST_CASE("Worn regeneration specials add about 1 % of the bar on each 5-minute tick (FCOR-2-60)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Character wearer = auditMember("Knight", 30);
    wearer.maxHealth = 1000;
    wearer.health = 500;
    wearer.maxSpellPoints = 1000;
    wearer.spellPoints = 500;
    // "of Regeneration" (37) on the ring, "of Mana" (38) on the amulet.
    wearer.equipment.ring1 = 1;
    wearer.equipmentRuntime.ring1.specialEnchantId = 37;
    wearer.equipment.amulet = 1;
    wearer.equipmentRuntime.amulet.specialEnchantId = 38;
    Party party = auditParty(rules, {wearer});
    OpenYAMM::Tests::PartySpellTestWorldRuntime world;
    world.bindParty(&party);
    const CombatRules &combat = rules.gameRules().combat;
    combat.updateCombat(party, world, 0.016f);
    const int health = party.members()[0].health;
    const int mana = party.members()[0].spellPoints;
    world.advanceGameMinutes(5);
    combat.updateCombat(party, world, 0.016f);
    // 1 % of 1000 less the engine's own point: 9.
    CHECK_EQ(party.members()[0].health, health + 9);
    CHECK_EQ(party.members()[0].spellPoints, mana + 9);
}

TEST_CASE("Supreme Armsmaster's damage counts item bonuses; the weapon-skill bonus the trained level (SKL-3)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Character knight = auditMember("Knight", 50);
    knight.skills["Armsmaster"] = {"Armsmaster", 25, SkillMastery::Grandmaster};
    CHECK_FALSE(mawSupremeArmsmaster(rules, knight, true));
    knight.itemSkillBonuses["Armsmaster"] = 5;
    CHECK(mawSupremeArmsmaster(rules, knight, true));
    CHECK_FALSE(mawSupremeArmsmaster(rules, knight));
}

TEST_CASE("A mercenary's gear loses its rarity, legendary affix, drop level and quality (SKL-4)")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    InventoryItem item;
    item.objectDescriptionId = 1;
    item.rulesetFields.lootRarity = 4;
    item.rulesetFields.ancientTier = 2;
    item.rulesetFields.legendaryAffixId = 18;
    item.rulesetFields.dropLevel = 120;
    item.rulesetFields.qualityPercent = 40;
    std::mt19937 rng(1);
    rules.gameRules().items.trimMercenaryItem(item, rng);
    CHECK_EQ(item.rulesetFields.lootRarity, 0);
    CHECK_EQ(item.rulesetFields.ancientTier, 0);
    CHECK_EQ(item.rulesetFields.legendaryAffixId, 0);
    CHECK_EQ(item.rulesetFields.dropLevel, 0);
    CHECK_EQ(item.rulesetFields.qualityPercent, 0);
}

TEST_CASE("A broken weapon attacks at bare-hand pace and broken armour slows nothing (SKL-7)")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const ItemTable &items = OpenYAMM::Tests::regressionGameData().itemTable;
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Character knight = auditMember("Knight", 20);
    knight.skills["Sword"] = {"Sword", 10, SkillMastery::Expert};
    const int bare = mawCharacterAttackDelay(rules, knight, items, CharacterAttackMode::Melee, 0).delay;
    knight.equipment.mainHand = 1;
    const int armed = mawCharacterAttackDelay(rules, knight, items, CharacterAttackMode::Melee, 0).delay;
    REQUIRE_NE(armed, bare);
    knight.equipmentRuntime.mainHand.broken = true;
    CHECK_EQ(mawCharacterAttackDelay(rules, knight, items, CharacterAttackMode::Melee, 0).delay, bare);

    // A plate armour slows by its impairment; broken, not at all.
    uint32_t plate = 0;

    for (uint32_t id = 1; id < 600 && plate == 0; ++id)
    {
        const ItemDefinition *pItem = items.get(id);
        plate = pItem != nullptr && canonicalSkillName(pItem->skillGroup) == "PlateArmor" ? id : 0;
    }

    REQUIRE(plate != 0);
    knight.equipment.armor = plate;
    REQUIRE_GT(mawCharacterArmorImpairment(knight, items), 0);
    knight.equipmentRuntime.armor.broken = true;
    CHECK_EQ(mawCharacterArmorImpairment(knight, items), doctest::Approx(0));
}

namespace
{
std::string plainText(std::string text)
{
    for (size_t found = text.find('\f'); found != std::string::npos; found = text.find('\f'))
    {
        text.erase(found, 6);
    }

    return text;
}
}

TEST_CASE("Skill popups show the numbers the rules use (TXT-2-5, TXT-2-6, TXT-2-7, TXT-2-11)")
{
    REQUIRE(OpenYAMM::Tests::regressionGameDataLoaded());
    const OpenYAMM::Tests::RegressionGameData &gameData = OpenYAMM::Tests::regressionGameData();
    std::ifstream input(std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/rulesets/maw/data/texts.yml");
    const std::string yaml((std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());
    MawTextData texts;
    std::string error;
    REQUIRE_MESSAGE(texts.loadFromYaml(yaml, error), error);
    MawRules rules(RulesetOptions{}, MawMapLevels{}, {}, {}, {}, texts);
    Character shaman = auditMember("Shaman", 40);
    shaman.skills["MindMagic"] = {"MindMagic", 20, SkillMastery::Grandmaster};
    shaman.skills["Mace"] = {"Mace", 20, SkillMastery::Grandmaster};
    shaman.skills["Staff"] = {"Staff", 20, SkillMastery::Grandmaster};
    Character assassin = auditMember("Assassin", 40);
    Character knight = auditMember("DeathKnight", 40);
    knight.skills["Learning"] = {"Learning", 10, SkillMastery::Expert};
    Party party = auditParty(rules, {shaman, assassin, knight});
    party.setItemTable(&gameData.itemTable);
    const SkillRules &skills = rules.gameRules().skills;
    const auto popup = [&](size_t member, const char *pSkill)
    {
        return skills.skillTooltip(party, *party.member(member), pSkill, {});
    };

    // A Shaman's Mind returns round(20^1.25) = 42 spell points a blow; an Assassin's Poisons rows give the energy.
    CHECK(plainText(popup(0, "MindMagic").description).find("restore 42 spell points") != std::string::npos);
    CHECK_EQ(popup(1, "WaterMagic").masteryLines[3], "You regenerate 14 energy per second");
    // A Death Knight has no Ascension: no mana cut for a trained Learning.
    CHECK(plainText(popup(2, "Learning").description).find("mana cost +0 %") != std::string::npos);

    // Holding a staff, only the Staff popup names a paralyse chance.
    uint32_t staff = 0;

    for (uint32_t id = 1; id < 600 && staff == 0; ++id)
    {
        const ItemDefinition *pItem = gameData.itemTable.get(id);
        staff = pItem != nullptr && canonicalSkillName(pItem->skillGroup) == "Staff" ? id : 0;
    }

    REQUIRE(staff != 0);
    party.member(0)->equipment.mainHand = staff;
    CHECK(popup(0, "Staff").description.find("Chance to paralyse") != std::string::npos);
    CHECK(popup(0, "Mace").description.find("Chance to paralyse") == std::string::npos);

    // Meditation fills what the auras leave: a held aura's reservation lowers the rate shown.
    Character &cleric = *party.member(0);
    cleric.skills["Meditation"] = {"Meditation", 20, SkillMastery::Master};
    cleric.skills["SpiritMagic"] = {"SpiritMagic", 20, SkillMastery::Master};
    cleric.maxSpellPoints = 1000;
    const std::string free = plainText(popup(0, "Meditation").description);
    rules.state().auraHolders[46] = 0;
    REQUIRE_GT(rules.gameRules().spells.reservedSpellPoints(party, 0), 0);
    CHECK_NE(plainText(popup(0, "Meditation").description), free);
}

TEST_CASE("The balance model caches whole levels only, so fractional levels do not grow it (ROB-2-6)")
{
    MawBalanceModel model(mawModelConfig(RulesetOptions{}, 5));
    const double whole = model.health(40);
    const size_t cached = model.cachedLevelCount();
    CHECK_GT(cached, 0u);

    for (int kill = 1; kill <= 100; ++kill)
    {
        model.health(40 + kill / 1000.0);
    }

    CHECK_EQ(model.cachedLevelCount(), cached);
    CHECK_EQ(model.health(40), doctest::Approx(whole));
}

TEST_CASE("A malformed placeholder in a MAW text stays as written instead of throwing (ROB-2-10)")
{
    const std::unordered_map<std::string, double> values = {{"x", 1.3}};
    CHECK_EQ(mawFillText("{x:1} {x:} {x*} {x*a} {x:2b}", values), "1.3 {x:} {x*} {x*a} {x:2b}");
    CHECK_EQ(mawFillText("{x*2}", values), "3");
}

TEST_CASE("A summoned actor keeps its summoner across a save, indoors and outdoors (Summon Wisp, MM8-Rel)")
{
    OutdoorWorldRuntime::MapActorState outdoorActor;
    outdoorActor.summonerMemberIndex = 2;
    MapDeltaActor indoorActor;
    indoorActor.summonerMemberIndex = 1;
    GameSaveData save;
    save.mapFileName = "oute3.odm";
    save.hasOutdoorRuntimeState = true;
    save.outdoorWorld.mapActors.push_back(outdoorActor);
    save.outdoorWorldStates[save.mapFileName] = save.outdoorWorld;
    save.indoorSceneStates["6d19.blv"].mapDeltaData.emplace();
    save.indoorSceneStates["6d19.blv"].mapDeltaData->actors.push_back(indoorActor);
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "openyamm_summoner.oysav";
    std::string error;
    REQUIRE_MESSAGE(saveGameDataToPath(path, save, error), error.c_str());
    const std::optional<GameSaveData> restored = loadGameDataFromPath(path, error);
    std::filesystem::remove(path);
    REQUIRE_MESSAGE(restored.has_value(), error.c_str());
    CHECK_EQ(restored->outdoorWorldStates.at("oute3.odm").mapActors.at(0).summonerMemberIndex, 2);
    const std::optional<MapDeltaData> &delta = restored->indoorSceneStates.at("6d19.blv").mapDeltaData;
    REQUIRE(delta.has_value());
    REQUIRE_EQ(delta->actors.size(), 1u);
    CHECK_EQ(delta->actors[0].summonerMemberIndex, 1);
}
