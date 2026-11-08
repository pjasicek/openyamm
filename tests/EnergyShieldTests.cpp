#include "doctest/doctest.h"

#include "game/events/EventRuntime.h"
#include "game/gameplay/ActorBehaviorCatalog.h"
#include "game/gameplay/ActorBehaviorRuntime.h"
#include "game/gameplay/GameMechanics.h"
#include "game/gameplay/GameplayActorShields.h"
#include "game/gameplay/GameplayProjectileService.h"
#include "game/party/Party.h"
#include "game/tables/MonsterRelationAddOns.h"
#include "game/tables/MonsterShields.h"
#include "game/tables/MonsterTable.h"

#include <random>
#include <string>
#include <vector>

using namespace OpenYAMM::Game;

namespace
{
// Hesper's grades and two monsters: a Trooper (Light, 1 000) and a Drudge (no shield, exposed).
const char *ShieldsYaml = R"(schema: openyamm.shields.v1
rules:
  exposed_energy_multiplier: 1.5
  party: {regen_delay_seconds: 5, regen_seconds: 4, hardened_exposed_multiplier: 1.25, hit_sound: party_shield_hit}
sounds:
  shield_hit_light: {fallback: 15sparks01}
  shield_break: {fallback: 32iceblast03}
  shield_regen: {}
  party_shield_hit: {}
grades:
  Light:
    rates: {physical: 0.5, classic_blaster: 1.0, kreegan_energy: 1.0, spell: 0.0}
    color: [1.0, 0.4, 0.7]
    intensity: 0.7
    rest_intensity: 0.12
    regen_seconds: 2.0
    hit_sound: shield_hit_light
    break_sound: shield_break
    regen_sound: shield_regen
  Standard:
    rates: {physical: 0.25, classic_blaster: 0.25, kreegan_energy: 1.0, spell: 0.0}
  Noble:
    rates: {physical: 0.0, classic_blaster: 0.0, kreegan_energy: 1.0, spell: 0.0}
monsters:
  10010: {shield: 1000, grade: Light, regen_delay_seconds: 4}
  10040: {shield: 4000, grade: Noble, regen_delay_seconds: 5}
  10000: {}
)";

MonsterShieldTable loadShields()
{
    MonsterShieldTable table;
    std::string error;
    REQUIRE_MESSAGE(table.loadWorldYaml(ShieldsYaml, "hesper", 10000, 10999, error), error);
    return table;
}

const char *RelationsYaml = R"(schema: openyamm.monsterRelations.v1
factions:
  kreegans: {monsters: [10000-10062]}
  defenders: {monsters: [10065-10069], kin: [villagers]}
  villagers: {monsters: [10073-10078], kin: [defenders]}
  ashrunners: {monsters: [10070-10072]}
  wild: {monsters: [10080-10092]}
relations:
  - {from: [kreegans, wild], to: party, relation: long}
  - {from: [defenders, villagers], to: party, relation: friendly}
  - {from: ashrunners, to: party, relation: long, until_qbit: 100101}
  - {from: defenders, to: kreegans, relation: short}
  - {from: kreegans, to: [defenders, villagers], relation: close}
  - {from: wild, to: any, relation: short}
  - {from: wild, to: wild, relation: friendly}
)";

MonsterRelationAddOns loadRelations()
{
    MonsterRelationAddOns relations;
    std::string error;
    REQUIRE_MESSAGE(relations.loadWorldYaml(RelationsYaml, "hesper", 10000, 10999, error), error);
    return relations;
}

PartySeed singleMemberSeed()
{
    PartySeed seed = {};
    Character member = {};
    member.name = "Tester";
    member.className = "Knight";
    member.maxHealth = 500;
    member.health = 500;
    seed.members.push_back(member);
    return seed;
}
}

TEST_CASE("energy shield table loads grades, sounds and monsters within the world's id range")
{
    const MonsterShieldTable table = loadShields();
    const MonsterShieldProfile *pTrooper = table.find(10010);
    REQUIRE(pTrooper != nullptr);
    CHECK(pTrooper->pool == 1000);
    CHECK(table.grade(*pTrooper)->name == "Light");
    // A faint rim at rest; the full strength shows on a hit, the raise and the break. Unset: the intensity throughout.
    CHECK(table.grade(*pTrooper)->restIntensity.value_or(0.0f) == doctest::Approx(0.12f));
    CHECK_FALSE(table.grade(*table.find(10040))->restIntensity.has_value());
    CHECK(pTrooper->regenDelaySeconds == doctest::Approx(4.0f));
    CHECK(pTrooper->regenSeconds == doctest::Approx(2.0f));
    const MonsterShieldProfile *pDrudge = table.find(10000);
    REQUIRE(pDrudge != nullptr);
    CHECK(pDrudge->pool == 0);
    CHECK(table.grade(*pDrudge) == nullptr);
    CHECK(table.find(307) == nullptr);
    CHECK(table.findSound("shield_hit_light")->fallback == "15sparks01");
    CHECK(table.partyRules().regenDelaySeconds == doctest::Approx(5.0f));

    MonsterShieldTable outOfRange;
    std::string error;
    CHECK_FALSE(outOfRange.loadWorldYaml(
        "schema: openyamm.shields.v1\ngrades: {}\nmonsters: {307: {}}\n", "hesper", 10000, 10999, error));
    CHECK(error.find("outside the world's monster id range") != std::string::npos);

    MonsterShieldTable brighterAtRest;
    CHECK_FALSE(brighterAtRest.loadWorldYaml("schema: openyamm.shields.v1\ngrades: {Light: {rates: {physical: 1.0}, "
        "intensity: 0.3, rest_intensity: 0.5}}\n", "hesper", 10000, 10999, error));
    CHECK(error.find("rest_intensity") != std::string::npos);

    MonsterShieldTable unknownGrade;
    CHECK_FALSE(unknownGrade.loadWorldYaml(
        "schema: openyamm.shields.v1\nmonsters: {10010: {shield: 5, grade: Heavy}}\n", "hesper", 10000, 10999, error));
}

TEST_CASE("energy shield hits follow the grade rate table, lose overflow and expose the body to energy")
{
    const MonsterShieldTable table = loadShields();
    const MonsterShieldProfile &trooper = *table.find(10010);
    const MonsterShieldProfile &noble = *table.find(10040);
    const MonsterShieldProfile &drudge = *table.find(10000);

    // Raised Light shield: physical at half, energy at full, spells do nothing; the body takes nothing.
    ShieldHitResolution hit = resolveMonsterShieldHit(table, trooper, 1000.0f, 100, ShieldAttackTier::Physical);
    CHECK(hit.absorbed);
    CHECK(hit.shieldDamage == doctest::Approx(50.0f));
    CHECK(hit.bodyDamage == 0);
    CHECK_FALSE(hit.broke);
    hit = resolveMonsterShieldHit(table, trooper, 1000.0f, 100, ShieldAttackTier::ClassicBlaster);
    CHECK(hit.shieldDamage == doctest::Approx(100.0f));
    hit = resolveMonsterShieldHit(table, trooper, 1000.0f, 250, ShieldAttackTier::Spell);
    CHECK(hit.absorbed);
    CHECK(hit.shieldDamage == doctest::Approx(0.0f));
    CHECK(hit.bodyDamage == 0);

    // A Noble shield ignores classic weapons and blasters; Kreegan energy wears it down.
    CHECK(resolveMonsterShieldHit(table, noble, 4000.0f, 300, ShieldAttackTier::ClassicBlaster).shieldDamage
        == doctest::Approx(0.0f));
    CHECK(resolveMonsterShieldHit(table, noble, 4000.0f, 300, ShieldAttackTier::KreeganEnergy).shieldDamage
        == doctest::Approx(300.0f));

    // Breaking: what is beyond the remaining pool is lost, the body still takes nothing.
    hit = resolveMonsterShieldHit(table, trooper, 40.0f, 500, ShieldAttackTier::KreeganEnergy);
    CHECK(hit.broke);
    CHECK(hit.shieldDamage == doctest::Approx(40.0f));
    CHECK(hit.bodyDamage == 0);

    // Down: energy x1.5 on the exposed body, physical and spells unchanged.
    CHECK(resolveMonsterShieldHit(table, trooper, 0.0f, 100, ShieldAttackTier::KreeganEnergy).bodyDamage == 150);
    CHECK(resolveMonsterShieldHit(table, trooper, 0.0f, 100, ShieldAttackTier::ClassicBlaster).bodyDamage == 150);
    CHECK(resolveMonsterShieldHit(table, trooper, 0.0f, 100, ShieldAttackTier::Physical).bodyDamage == 100);
    CHECK(resolveMonsterShieldHit(table, trooper, 0.0f, 100, ShieldAttackTier::Spell).bodyDamage == 100);
    // A monster without a shield is always exposed.
    hit = resolveMonsterShieldHit(table, drudge, 0.0f, 27, ShieldAttackTier::ClassicBlaster);
    CHECK_FALSE(hit.absorbed);
    CHECK(hit.bodyDamage == 41);
}

TEST_CASE("tech weapon perks: more damage to shields, more on exposed bodies, and a cleave through a breaking shield")
{
    const MonsterShieldTable table = loadShields();
    const MonsterShieldProfile &trooper = *table.find(10010);

    // +25 % to a raised shield.
    ShieldHitModifiers modifiers;
    modifiers.shieldDamageMultiplier = 1.25f;
    ShieldHitResolution hit = resolveMonsterShieldHit(table, trooper, 1000.0f, 100, ShieldAttackTier::KreeganEnergy,
        modifiers);
    CHECK(hit.shieldDamage == doctest::Approx(125.0f));
    CHECK(hit.bodyDamage == 0);

    // +20 % on an exposed body: x1.5 x1.2.
    modifiers = {};
    modifiers.exposedMultiplier = 1.2f;
    CHECK(resolveMonsterShieldHit(table, trooper, 0.0f, 100, ShieldAttackTier::KreeganEnergy, modifiers).bodyDamage
        == 180);
    CHECK(resolveMonsterShieldHit(table, trooper, 0.0f, 100, ShieldAttackTier::Physical, modifiers).bodyDamage == 100);

    // Cleave: a 500 Physical hit breaks a 40-point Light shield with 80 of it (half rate); half the other 420 reach the
    // body, which reacts. Without breaking, or without cleave, nothing reaches it.
    modifiers = {};
    modifiers.cleave = true;
    hit = resolveMonsterShieldHit(table, trooper, 40.0f, 500, ShieldAttackTier::Physical, modifiers);
    CHECK(hit.broke);
    CHECK(hit.cleaved);
    CHECK_FALSE(hit.absorbed);
    CHECK(hit.shieldDamage == doctest::Approx(40.0f));
    CHECK(hit.bodyDamage == 210);
    hit = resolveMonsterShieldHit(table, trooper, 1000.0f, 500, ShieldAttackTier::Physical, modifiers);
    CHECK_FALSE(hit.cleaved);
    CHECK(hit.bodyDamage == 0);
    CHECK(resolveMonsterShieldHit(table, trooper, 40.0f, 500, ShieldAttackTier::Physical).bodyDamage == 0);
}

TEST_CASE("energy shield regeneration waits for its delay without damage, then fills at its rate")
{
    const MonsterShieldTable table = loadShields();
    const MonsterShieldProfile &trooper = *table.find(10010);
    CHECK(regenerateMonsterShield(trooper, 0.0f, 1.0f, 1.0f) == doctest::Approx(0.0f));
    // 3.5 s since the damage plus a 1 s step: half a second past the 4 s delay at 500 points a second.
    CHECK(regenerateMonsterShield(trooper, 0.0f, 3.5f, 1.0f) == doctest::Approx(250.0f));
    CHECK(regenerateMonsterShield(trooper, 900.0f, 10.0f, 1.0f) == doctest::Approx(1000.0f));
    CHECK(regenerateMonsterShield(trooper, 200.0f, 10.0f, 0.5f) == doctest::Approx(450.0f));
}

TEST_CASE("actor energy shields absorb, break with a sound, stay down for the delay and rise again")
{
    const MonsterShieldTable table = loadShields();
    GameplayActorShields shields;
    shields.bind(&table);
    REQUIRE(shields.active());
    std::vector<int16_t> monsters = {10010, 307};
    const auto facts = [&](size_t actorIndex)
    {
        return GameplayActorShields::ActorFacts{monsters[actorIndex], true, {0.0f, 0.0f, 90.0f}};
    };
    shields.update(0.01f, monsters.size(), facts);

    // An MM monster passes the damage unchanged and has no shield view.
    GameplayActorShieldHit hit = shields.applyHit(1, 307, 40, ShieldAttackTier::KreeganEnergy);
    CHECK(hit.bodyDamage == 40);
    CHECK_FALSE(hit.absorbed);
    GameplayActorShieldView view;
    shields.view(1, view);
    CHECK_FALSE(view.present);

    shields.view(0, view);
    CHECK(view.present);
    CHECK(view.raised);
    CHECK(view.fraction == doctest::Approx(1.0f));

    const std::array<float, 3> impact = {10.0f, 0.0f, 100.0f};
    hit = shields.applyHit(0, 10010, 300, ShieldAttackTier::Physical, &impact);
    CHECK(hit.absorbed);
    CHECK(hit.bodyDamage == 0);
    CHECK(shields.shieldPoints(0) == doctest::Approx(850.0f));
    shields.view(0, view);
    CHECK(view.hitSerial == 1);
    CHECK(view.hits[0][3] == doctest::Approx(0.0f));
    CHECK(view.hits[0][0] == doctest::Approx(10.0f));

    hit = shields.applyHit(0, 10010, 2000, ShieldAttackTier::KreeganEnergy, &impact);
    CHECK(hit.absorbed);
    CHECK(hit.broke);
    CHECK(hit.bodyDamage == 0);
    shields.view(0, view);
    CHECK_FALSE(view.raised);
    CHECK(view.breakSerial == 1);
    CHECK(view.secondsSinceBreak == doctest::Approx(0.0f));

    // The next energy hit is on the exposed body.
    hit = shields.applyHit(0, 10010, 100, ShieldAttackTier::KreeganEnergy, &impact);
    CHECK_FALSE(hit.absorbed);
    CHECK(hit.bodyDamage == 150);

    std::vector<GameplayActorShieldSound> sounds = shields.drainSounds();
    REQUIRE(sounds.size() == 2);
    CHECK(sounds[0].name == "shield_hit_light");
    CHECK(sounds[0].fallback == "15sparks01");
    CHECK(sounds[1].name == "shield_break");

    // Down for the 4 s delay, then 2 s to full; the rise plays its sound once.
    for (int step = 0; step < 39; ++step)
    {
        shields.update(0.1f, monsters.size(), facts);
    }
    CHECK(shields.shieldPoints(0) == doctest::Approx(0.0f));
    for (int step = 0; step < 11; ++step)
    {
        shields.update(0.1f, monsters.size(), facts);
    }
    shields.view(0, view);
    CHECK(view.raised);
    CHECK(view.raiseSerial == 1);
    CHECK(view.fraction == doctest::Approx(0.5f).epsilon(0.06));
    for (int step = 0; step < 15; ++step)
    {
        shields.update(0.1f, monsters.size(), facts);
    }
    CHECK(shields.shieldPoints(0) == doctest::Approx(1000.0f));
    sounds = shields.drainSounds();
    REQUIRE(sounds.size() == 1);
    CHECK(sounds[0].name == "shield_regen");

    EventRuntimeState eventRuntimeState;
    shields.applyHit(0, 10010, 10, ShieldAttackTier::Physical, &impact);
    shields.queueSounds(eventRuntimeState);
    REQUIRE(eventRuntimeState.pendingSounds.size() == 1);
    CHECK(eventRuntimeState.pendingSounds[0].soundName == "shield_hit_light");
    CHECK(eventRuntimeState.pendingSounds[0].fallbackSoundName == "15sparks01");

    // A dead actor's shield does not regenerate.
    shields.applyHit(0, 10010, 5000, ShieldAttackTier::KreeganEnergy, &impact);
    for (int step = 0; step < 100; ++step)
    {
        shields.update(0.1f, monsters.size(), [&](size_t actorIndex)
        {
            return GameplayActorShields::ActorFacts{monsters[actorIndex], false, {}};
        });
    }
    CHECK(shields.shieldPoints(0) == doctest::Approx(0.0f));
}

TEST_CASE("energy shields cost nothing without profiles")
{
    MonsterShieldTable empty;
    GameplayActorShields shields;
    shields.bind(&empty);
    CHECK_FALSE(shields.active());
    size_t factsCalls = 0;
    shields.update(1.0f, 100, [&](size_t)
    {
        ++factsCalls;
        return GameplayActorShields::ActorFacts{};
    });
    CHECK(factsCalls == 0);
    CHECK(shields.applyHit(3, 10010, 77, ShieldAttackTier::KreeganEnergy).bodyDamage == 77);
}

TEST_CASE("energy shield attack tiers of damage types and projectiles")
{
    CHECK(shieldAttackTierForDamageType(CombatDamageType::Physical, true) == ShieldAttackTier::Physical);
    CHECK(shieldAttackTierForDamageType(CombatDamageType::Irresistible, true) == ShieldAttackTier::ClassicBlaster);
    CHECK(shieldAttackTierForDamageType(CombatDamageType::Energy, false) == ShieldAttackTier::KreeganEnergy);
    CHECK(shieldAttackTierForDamageType(CombatDamageType::Fire, false) == ShieldAttackTier::Spell);
    CHECK(parseShieldAttackTier("kreegan_energy") == ShieldAttackTier::KreeganEnergy);
    CHECK_FALSE(parseShieldAttackTier("plasma").has_value());

    GameplayProjectileService::ProjectileState projectile;
    projectile.sourceKind = GameplayProjectileService::ProjectileState::SourceKind::Party;
    projectile.damageType = CombatDamageType::Irresistible;
    CHECK(GameplayProjectileService::projectileShieldTier(projectile) == ShieldAttackTier::ClassicBlaster);
    projectile.shieldTier = ShieldAttackTier::KreeganEnergy;
    CHECK(GameplayProjectileService::projectileShieldTier(projectile) == ShieldAttackTier::KreeganEnergy);
    projectile.shieldTier.reset();
    projectile.spellId = 6;
    CHECK(GameplayProjectileService::projectileShieldTier(projectile) == ShieldAttackTier::Spell);
}

TEST_CASE("relation add-ons decide faction pairs and leave other monsters to the engine table")
{
    const MonsterRelationAddOns relations = loadRelations();
    CHECK(relations.factionName(relations.factionOf(10050)) == "kreegans");
    CHECK(relations.factionOf(307) == -1);
    CHECK(relations.relationToParty(10050) == 4);
    CHECK(relations.relationToParty(10067) == 0);
    CHECK_FALSE(relations.relationToParty(307).has_value());
    // Defenders engage Kreegans at the short range, drones answer only at close range.
    CHECK(relations.relationBetween(10065, 10050) == 2);
    CHECK(relations.relationBetween(10050, 10067) == 1);
    CHECK_FALSE(relations.relationBetween(10067, 10073).has_value());
    // Glassbacks attack anything (also MM monsters), never each other.
    CHECK(relations.relationBetween(10081, 10050) == 2);
    CHECK(relations.relationBetween(10081, 307) == 2);
    CHECK(relations.relationBetween(10081, 10082) == 0);
    // MM monsters keep their own relations.
    CHECK_FALSE(relations.relationBetween(307, 10081).has_value());
    CHECK(relations.sameFaction(10067, 10074) == true);
    CHECK(relations.sameFaction(10067, 10050) == false);
    CHECK(relations.sameFaction(10067, 307) == false);
    CHECK_FALSE(relations.sameFaction(306, 307).has_value());

    MonsterRelationAddOns bad;
    std::string error;
    CHECK_FALSE(bad.loadWorldYaml("schema: openyamm.monsterRelations.v1\nfactions: {a: {monsters: [12]}}\n",
        "hesper", 10000, 10999, error));
    CHECK_FALSE(bad.loadWorldYaml("schema: openyamm.monsterRelations.v1\nfactions: {b: {monsters: [10001]}}\n"
        "relations: [{from: b, to: c, relation: short}]\n", "hesper", 10000, 10999, error));
}

TEST_CASE("relation add-ons switch by QBit and advance their revision only on a change")
{
    const MonsterRelationAddOns relations = loadRelations();
    REQUIRE(relations.hasConditions());
    CHECK(relations.partyRelationIsConditional(10071));
    CHECK_FALSE(relations.partyRelationIsConditional(10050));
    bool s1Done = false;
    const auto isQBitSet = [&](uint32_t questBitId)
    {
        return questBitId == 100101 && s1Done;
    };
    CHECK(relations.refreshConditions(isQBitSet));
    const uint64_t revision = relations.revision();
    CHECK(relations.relationToParty(10071) == 4);
    CHECK_FALSE(relations.refreshConditions(isQBitSet));
    CHECK(relations.revision() == revision);
    s1Done = true;
    CHECK(relations.refreshConditions(isQBitSet));
    CHECK(relations.revision() == revision + 1);
    // No rule left for the Ashrunners and the party: the engine table's relation (none for these ids) applies.
    CHECK_FALSE(relations.relationToParty(10071).has_value());
}

TEST_CASE("monster table relations take the add-on first and the engine table otherwise")
{
    MonsterTable table;
    // A two-faction engine table: row and column 1 are monsters 1-3; they hate the party (row 0) at long range.
    REQUIRE(table.loadRelationsFromRows({{"", "Party", "Goblin"}, {"Party", "0", "4"}, {"Goblin", "4", "0"}}));
    CHECK(table.getRelationToParty(1) == 4);
    CHECK(table.getRelationToParty(10050) == 0);
    std::string error;
    REQUIRE(table.relationAddOns().loadWorldYaml(RelationsYaml, "hesper", 10000, 10999, error));
    CHECK(table.getRelationToParty(1) == 4);
    CHECK(table.getRelationToParty(10050) == 4);
    CHECK(table.isHostileToParty(10081));
    CHECK_FALSE(table.isHostileToParty(10067));
    CHECK(table.getRelationBetweenMonsters(10066, 10051) == 2);
    CHECK(table.getRelationBetweenMonsters(1, 1) == 0);
    CHECK(table.isLikelySameFaction(10069, 10078));
}

TEST_CASE("a map's own faction relations replace hostile.txt cells until the next map clears them")
{
    MonsterTable table;
    // Factions 1 (monsters 1-3) and 2 (monsters 4-6) both hate the party (row 0) and are neutral to each other.
    REQUIRE(table.loadRelationsFromRows({{"", "Party", "Goblin", "Guard"},
        {"Party", "0", "3", "3"},
        {"Goblin", "0", "0", "0"},
        {"Guard", "0", "0", "0"}}));
    REQUIRE(table.isHostileToParty(2));
    REQUIRE(table.isHostileToParty(5));

    // MMMerge's Game.HostileTxt[2][0] = 0 and Game.HostileTxt[2][1] = 2: guards are peaceful toward the party and
    // attack goblins on this map; the goblins keep their table relations.
    table.setMapFactionRelation(2, 0, 0);
    table.setMapFactionRelation(2, 1, 2);
    CHECK_FALSE(table.isHostileToParty(4));
    CHECK_FALSE(table.isHostileToParty(6));
    CHECK(table.isHostileToParty(1));
    CHECK(table.getRelationBetweenMonsters(5, 2) == 2);
    CHECK(table.getRelationBetweenMonsters(2, 5) == 0);

    table.clearMapFactionRelations();
    CHECK(table.isHostileToParty(5));
    CHECK(table.getRelationBetweenMonsters(5, 2) == 0);
}

TEST_CASE("personal shields absorb first, pass the overflow, start full and regenerate after their delay")
{
    Party party;
    party.seed(singleMemberSeed());
    Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);

    // No shield: the damage passes untouched.
    Party::PersonalShieldHit hit = party.absorbPersonalShieldHit(0, 80);
    CHECK(hit.passedDamage == 80);
    CHECK_FALSE(hit.absorbed);

    pMember->personalShieldCapacity = 300;
    pMember->personalShieldInitialized = false;
    party.updatePersonalShields(0.1f);
    CHECK(pMember->personalShield == doctest::Approx(300.0f));

    hit = party.absorbPersonalShieldHit(0, 120);
    CHECK(hit.absorbed);
    CHECK(hit.passedDamage == 0);
    CHECK(pMember->personalShield == doctest::Approx(180.0f));
    hit = party.absorbPersonalShieldHit(0, 500);
    CHECK(hit.broke);
    CHECK(hit.passedDamage == 320);
    CHECK(pMember->personalShield == doctest::Approx(0.0f));

    // 5 s delay (the defaults), then 4 s to full.
    for (int step = 0; step < 49; ++step)
    {
        party.updatePersonalShields(0.1f);
    }
    CHECK(pMember->personalShield == doctest::Approx(0.0f));
    for (int step = 0; step < 21; ++step)
    {
        party.updatePersonalShields(0.1f);
    }
    CHECK(pMember->personalShield == doctest::Approx(150.0f).epsilon(0.05));
}

namespace
{
// The follow-ups: an Overseer (Standard, links its squad), a Trooper, a Glassback (energy immune), a turret (machine),
// and the overload, EMP and party consumable rules.
const char *FollowUpShieldsYaml = R"(schema: openyamm.shields.v1
rules:
  overload: {chance: 0.25, remaining_fraction: 0.5}
  emp_grenade: {radius: 700, remaining_fraction: 0.4, machine_stun_seconds: 3}
  party: {shield_cell: {points: 250, seconds: 30}, shield_burst: {refill_fraction: 0.5}}
sounds:
  shield_break: {}
grades:
  Light:
    rates: {physical: 0.5, classic_blaster: 1.0, kreegan_energy: 1.0, spell: 0.0}
    regen_seconds: 2.0
    break_sound: shield_break
  Standard:
    rates: {physical: 0.25, classic_blaster: 0.25, kreegan_energy: 1.0, spell: 0.0}
monsters:
  10030: {shield: 1800, grade: Standard, regen_delay_seconds: 4, link: {radius: 2000, regen_multiplier: 2,
          drop_on_death: true}}
  10010: {shield: 1000, grade: Light, regen_delay_seconds: 4}
  10054: {shield: 400, grade: Light, regen_delay_seconds: 4, machine: true}
  10081: {energy_immune: true}
)";

MonsterShieldTable loadFollowUpShields()
{
    MonsterShieldTable table;
    std::string error;
    REQUIRE_MESSAGE(table.loadWorldYaml(FollowUpShieldsYaml, "hesper", 10000, 10999, error), error);
    return table;
}
}

TEST_CASE("energy shield table reads links, energy immunity, machines and the overload, EMP and cell rules")
{
    const MonsterShieldTable table = loadFollowUpShields();
    CHECK(table.hasLinks());
    const MonsterShieldProfile *pOverseer = table.find(10030);
    REQUIRE(pOverseer != nullptr);
    CHECK(pOverseer->linkRadius == doctest::Approx(2000.0f));
    CHECK(pOverseer->linkRegenMultiplier == doctest::Approx(2.0f));
    CHECK(pOverseer->linkDropsOnDeath);
    CHECK(table.find(10010)->linkRadius == 0.0f);
    CHECK(table.find(10054)->machine);
    CHECK(table.find(10081)->energyImmune);
    CHECK(table.overloadRules().chance == doctest::Approx(0.25f));
    CHECK(table.empGrenadeRules().radius == doctest::Approx(700.0f));
    CHECK(table.empGrenadeRules().remainingFraction == doctest::Approx(0.4f));
    CHECK(table.empGrenadeRules().machineStunSeconds == doctest::Approx(3.0f));
    CHECK(table.partyRules().shieldCellPoints == 250);
    CHECK(table.partyRules().shieldCellSeconds == doctest::Approx(30.0f));

    // Without the blocks the defaults are COMBAT.md's and ITEMS.md's numbers.
    const MonsterShieldTable defaults = loadShields();
    CHECK_FALSE(defaults.hasLinks());
    CHECK(defaults.overloadRules().chance == doctest::Approx(0.1f));
    CHECK(defaults.overloadRules().remainingFraction == doctest::Approx(0.5f));
    CHECK(defaults.empGrenadeRules().radius == doctest::Approx(600.0f));
    CHECK(defaults.partyRules().shieldCellPoints == 200);
    CHECK(defaults.partyRules().shieldCellSeconds == doctest::Approx(60.0f));
    CHECK(defaults.partyRules().shieldBurstFraction == doctest::Approx(0.5f));

    MonsterShieldTable badLink;
    std::string error;
    CHECK_FALSE(badLink.loadWorldYaml("schema: openyamm.shields.v1\ngrades: {Light: {rates: {physical: 1}}}\n"
        "monsters: {10030: {shield: 5, grade: Light, link: {radius: -3}}}\n", "hesper", 10000, 10999, error));
    CHECK(error.find("link") != std::string::npos);
}

TEST_CASE("energy-immune bodies take nothing from energy weapons and the usual from everything else")
{
    const MonsterShieldTable table = loadFollowUpShields();
    const MonsterShieldProfile &glassback = *table.find(10081);
    CHECK(resolveMonsterShieldHit(table, glassback, 0.0f, 100, ShieldAttackTier::KreeganEnergy).bodyDamage == 0);
    CHECK(resolveMonsterShieldHit(table, glassback, 0.0f, 100, ShieldAttackTier::ClassicBlaster).bodyDamage == 0);
    CHECK(resolveMonsterShieldHit(table, glassback, 0.0f, 100, ShieldAttackTier::Physical).bodyDamage == 100);
    CHECK(resolveMonsterShieldHit(table, glassback, 0.0f, 100, ShieldAttackTier::Spell).bodyDamage == 100);
    CHECK_FALSE(resolveMonsterShieldHit(table, glassback, 0.0f, 100, ShieldAttackTier::KreeganEnergy).absorbed);
}

TEST_CASE("a living shield link doubles its allies' regeneration and its death drops their raised shields")
{
    const MonsterShieldTable table = loadFollowUpShields();
    GameplayActorShields shields;
    shields.bind(&table);
    // 0 the Overseer, 1 a Trooper beside it, 2 a Trooper out of reach, 3 a Trooper beside it on the party's side.
    std::vector<int16_t> monsters = {10030, 10010, 10010, 10010};
    std::vector<bool> alive = {true, true, true, true};
    const std::vector<std::array<float, 3>> centers = {
        {0.0f, 0.0f, 90.0f}, {500.0f, 0.0f, 90.0f}, {5000.0f, 0.0f, 90.0f}, {0.0f, 500.0f, 90.0f}};
    const auto facts = [&](size_t actorIndex)
    {
        return GameplayActorShields::ActorFacts{monsters[actorIndex], alive[actorIndex], centers[actorIndex],
            actorIndex != 3};
    };
    shields.update(0.01f, monsters.size(), facts);
    for (size_t actorIndex = 1; actorIndex < 4; ++actorIndex)
    {
        shields.applyHit(actorIndex, 10010, 5000, ShieldAttackTier::KreeganEnergy);
    }
    // 4 s delay, then 1 s: the linked Trooper is at 2 x 1000 / 2 s x 1 s = full, the others at half.
    for (int step = 0; step < 50; ++step)
    {
        shields.update(0.1f, monsters.size(), facts);
    }
    CHECK(shields.shieldPoints(1) == doctest::Approx(1000.0f));
    CHECK(shields.shieldPoints(2) == doctest::Approx(500.0f).epsilon(0.05));
    CHECK(shields.shieldPoints(3) == doctest::Approx(500.0f).epsilon(0.05));

    // The Overseer dies: the allied Trooper's raised shield breaks with it, the others keep theirs.
    alive[0] = false;
    shields.drainSounds();
    shields.update(0.1f, monsters.size(), facts);
    CHECK(shields.shieldPoints(1) == doctest::Approx(0.0f));
    CHECK(shields.secondsDownSinceBreak(1) == doctest::Approx(0.0f));
    CHECK(shields.shieldPoints(2) > 500.0f);
    CHECK(shields.shieldPoints(3) > 500.0f);
    CHECK(shields.drainSounds().size() == 1);
    // A dead link speeds nothing: back to the plain 4 s delay and 2 s fill (the break's update counted 0.1 s).
    for (int step = 0; step < 49; ++step)
    {
        shields.update(0.1f, monsters.size(), facts);
    }
    CHECK(shields.shieldPoints(1) == doctest::Approx(500.0f).epsilon(0.05));
}

TEST_CASE("cutting a raised shield keeps a share, ripples, and reports how long a broken shield stays down")
{
    const MonsterShieldTable table = loadFollowUpShields();
    GameplayActorShields shields;
    shields.bind(&table);
    std::vector<int16_t> monsters = {10010, 10081};
    const auto facts = [&](size_t actorIndex)
    {
        return GameplayActorShields::ActorFacts{monsters[actorIndex], true, {0.0f, 0.0f, 90.0f}, true};
    };
    shields.update(0.01f, monsters.size(), facts);
    CHECK(shields.secondsDownSinceBreak(0) == doctest::Approx(-1.0f));
    REQUIRE(shields.cutRaisedShield(0, 0.5f));
    CHECK(shields.shieldPoints(0) == doctest::Approx(500.0f));
    GameplayActorShieldView view;
    shields.view(0, view);
    CHECK(view.hitSerial == 1);
    CHECK_FALSE(shields.cutRaisedShield(1, 0.5f));   // no shield
    CHECK(shields.profile(1) == table.find(10081));
    CHECK(shields.profile(5) == nullptr);

    const GameplayActorShieldHit hit = shields.applyHit(0, 10010, 2000, ShieldAttackTier::KreeganEnergy);
    CHECK(hit.shieldDamage == doctest::Approx(500.0f));
    CHECK(hit.broke);
    CHECK_FALSE(shields.cutRaisedShield(0, 0.5f));   // already down
    shields.update(1.5f, monsters.size(), facts);
    CHECK(shields.secondsDownSinceBreak(0) == doctest::Approx(1.5f));
    CHECK(shields.secondsDownSinceBreak(1) == doctest::Approx(-1.0f));
}

TEST_CASE("shield cells refill a shield or lend a fading one, and burst cells refill every shield by a share")
{
    MonsterShieldTable table = loadFollowUpShields();
    Party party;
    party.seed(singleMemberSeed());
    party.setPersonalShieldRules(&table.partyRules());
    Character *pMember = party.member(0);
    REQUIRE(pMember != nullptr);

    // Nobody has a shield: a burst cell does nothing, a shield cell lends 250 points for 30 s.
    CHECK_FALSE(party.burstPersonalShields());
    REQUIRE(party.chargePersonalShield(0));
    CHECK(pMember->personalShieldCapacity == 250);
    CHECK(pMember->personalShield == doctest::Approx(250.0f));
    CHECK(party.absorbPersonalShieldHit(0, 100).passedDamage == 0);
    party.rebuildMagicalBonusesFromBuffs();
    CHECK(pMember->personalShieldCapacity == 250);   // the equipment rebuild keeps it
    CHECK(party.burstPersonalShields());
    CHECK(pMember->personalShield == doctest::Approx(250.0f));
    for (int step = 0; step < 301; ++step)
    {
        party.updatePersonalShields(0.1f);
    }
    CHECK(pMember->temporaryShieldPoints == 0);
    CHECK(pMember->personalShieldCapacity == 0);
    CHECK(pMember->personalShield == doctest::Approx(0.0f));

    // With a shield of its own a cell refills it, and a burst adds half the pool.
    pMember->armorShieldPoints = 400;
    pMember->personalShieldCapacity = 400;
    pMember->personalShieldInitialized = true;
    pMember->personalShield = 50.0f;
    REQUIRE(party.burstPersonalShields());
    CHECK(pMember->personalShield == doctest::Approx(250.0f));
    REQUIRE(party.chargePersonalShield(0));
    CHECK(pMember->personalShield == doctest::Approx(400.0f));
    CHECK(pMember->temporaryShieldPoints == 0);
}

TEST_CASE("party energy resistance from items halves Energy damage like the other schools")
{
    // Without it (every home-world character) Energy is unresisted.
    Character member = {};
    std::mt19937 rng(7);
    CHECK(GameMechanics::resolveCharacterIncomingDamage(
        member, nullptr, nullptr, nullptr, 160, CombatDamageType::Energy, rng) == 160);
    member.energyResistance = 100000;
    std::mt19937 resistantRng(7);
    CHECK(GameMechanics::resolveCharacterIncomingDamage(
        member, nullptr, nullptr, nullptr, 160, CombatDamageType::Energy, resistantRng) == 10);
}

TEST_CASE("tactic shield_break falls back while a hostile actor's shield is down, within its time")
{
    ActorBehaviorCatalog catalog;
    ActorTacticsFacts tactics = {};
    tactics.shieldBreakReaction = ActorShieldBreakReaction::FallBack;
    tactics.shieldBreakSeconds = 4.0f;
    catalog.setMonsterTactics(10010, tactics);
    ActorBehaviorRuntime runtime;
    runtime.bind(&catalog, nullptr);

    const auto makeFacts = [](size_t index, int16_t monsterId, float shieldDown, bool hostile)
    {
        ActorAiFacts facts = {};
        facts.actorIndex = index;
        facts.actorId = uint32_t(200 + index);
        facts.identity.monsterId = monsterId;
        facts.status.hostileToParty = hostile;
        facts.status.shieldDownSinceBreakSeconds = shieldDown;
        facts.target.currentKind = ActorAiTargetKind::Party;
        facts.target.currentCanSense = true;
        return facts;
    };
    ActorAiFrameFacts frame = {};
    frame.activeActors.push_back(makeFacts(0, 10010, 1.0f, true));    // just broke: falls back
    frame.activeActors.push_back(makeFacts(1, 10010, -1.0f, true));   // shield up
    frame.activeActors.push_back(makeFacts(2, 10010, 5.0f, true));    // down longer than its 4 s
    frame.activeActors.push_back(makeFacts(3, 10010, 1.0f, false));   // a friendly guard holds
    frame.activeActors.push_back(makeFacts(4, 10020, 1.0f, true));    // no reaction in its tactics
    runtime.applyAiFacts(frame);
    CHECK(frame.activeActors[0].status.forceFleeFromParty);
    CHECK_FALSE(frame.activeActors[1].status.forceFleeFromParty);
    CHECK_FALSE(frame.activeActors[2].status.forceFleeFromParty);
    CHECK_FALSE(frame.activeActors[3].status.forceFleeFromParty);
    CHECK_FALSE(frame.activeActors[4].status.forceFleeFromParty);
}
