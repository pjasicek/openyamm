// MAW's later boss affixes (Unstoppable, Berserker, Cryptic, Skilled) and Dragon Fear's Dragon Ability durations
// (devdocs/maw/UPSTREAM_SYNC_8fbb48d1.md §2, S1).
#include "doctest/doctest.h"
#include "game/maps/SaveGame.h"
#include "game/outdoor/OutdoorWorldRuntime.h"
#include "game/party/Party.h"
#include "game/party/SpellIds.h"
#include "game/rules/CombatRules.h"
#include "game/rules/CorpseLoot.h"
#include "game/rules/GameRules.h"
#include "game/rules/MonsterRules.h"
#include "game/rules/SpellRules.h"
#include "game/rules/maw/MawMonsterRules.h"
#include "game/rules/maw/MawRules.h"
#include "game/rules/maw/MawSpellFormulas.h"
#include "game/tables/ItemTable.h"
#include "game/tables/MapStats.h"
#include "game/tables/MonsterTable.h"

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <random>
#include <set>
#include <string>
#include <vector>

using namespace OpenYAMM::Game;

namespace
{
std::string readSource(const std::string &path)
{
    std::ifstream input(std::filesystem::path(OPENYAMM_SOURCE_DIR) / path);
    return std::string((std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());
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

ActorRulesetFacts bossFacts(MawBossAffix affix, MawBossAffix hidden = MawBossAffix::None)
{
    ActorRulesetFacts facts;
    facts.level = 50;
    facts.familyLevel = 40;
    facts.tier = 2;
    facts.bossAffix = uint8_t(affix);
    facts.crypticAffix = uint8_t(hidden);
    return facts;
}

Character member(uint32_t level)
{
    Character character;
    character.name = "Member";
    character.className = "Knight";
    character.level = level;
    character.maxHealth = 1000;
    character.health = 1000;
    return character;
}
}

TEST_CASE("MAW's later affixes are rolled, named, and not part of an Omnipotent boss")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    const MonsterRules &monsters = rules.gameRules().monsters;
    std::set<uint8_t> rolled;

    for (uint64_t seed = 1; seed <= 4000; ++seed)
    {
        ActorRulesetFacts facts;
        facts.level = 50;
        facts.familyLevel = 40;
        REQUIRE(monsters.makeBoss(facts, seed * 7919, 0));
        rolled.insert(facts.bossAffix);
        // Only a Cryptic boss carries a hidden affix.
        CHECK_EQ(facts.crypticAffix != 0, facts.bossAffix == uint8_t(MawBossAffix::Cryptic));
    }

    for (const MawBossAffix affix : {MawBossAffix::Unstoppable, MawBossAffix::Berserker, MawBossAffix::Cryptic,
             MawBossAffix::Skilled, MawBossAffix::Summoner, MawBossAffix::Shadow})
    {
        CHECK(rolled.contains(uint8_t(affix)));
    }

    // The values are saved: appended after Omnipotent.
    CHECK_EQ(int(MawBossAffix::Omnipotent), 17);
    CHECK_EQ(int(MawBossAffix::Skilled), 21);
    CHECK_EQ(mawBossAffixName(MawBossAffix::Unstoppable), "Unstoppable");
    CHECK_EQ(mawBossAffixName(MawBossAffix::Skilled), "Skilled");
    CHECK_EQ(monsters.actorDisplayName(bossFacts(MawBossAffix::Berserker), "Ogre"), "Berserker Ogre");

    const ActorRulesetFacts omnipotent = bossFacts(MawBossAffix::Omnipotent);
    CHECK(mawHasBossAffix(omnipotent, MawBossAffix::Thorn));

    for (const MawBossAffix affix :
        {MawBossAffix::Unstoppable, MawBossAffix::Berserker, MawBossAffix::Cryptic, MawBossAffix::Skilled})
    {
        CHECK_FALSE(mawHasBossAffix(omnipotent, affix));
        CHECK(mawHasBossAffix(bossFacts(affix == MawBossAffix::Cryptic ? MawBossAffix::Cryptic : affix,
                                  affix == MawBossAffix::Cryptic ? MawBossAffix::Skilled : MawBossAffix::None),
                  affix == MawBossAffix::Cryptic ? MawBossAffix::Skilled : affix));
        // No badge art for these yet: the skull alone.
        CHECK_EQ(monsters.actorBadges(bossFacts(affix)), std::vector<std::string>{"maw_boss_skull"});
    }
}

TEST_CASE("MAW Cryptic bosses fight with a hidden other affix, kept by a save")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData());
    const MonsterRules &monsters = rules.gameRules().monsters;
    std::set<uint8_t> hidden;

    for (uint64_t seed = 1; seed <= 600; ++seed)
    {
        ActorRulesetFacts facts;
        facts.level = 50;
        facts.familyLevel = 40;
        REQUIRE(monsters.makeBoss(facts, seed, uint8_t(MawBossAffix::Cryptic)));
        CHECK_EQ(facts.bossAffix, uint8_t(MawBossAffix::Cryptic));
        const MawBossAffix effect = MawBossAffix(facts.crypticAffix);
        CHECK(effect != MawBossAffix::None);
        CHECK(effect != MawBossAffix::Cryptic);
        CHECK(effect != MawBossAffix::Broodlord);
        CHECK(effect != MawBossAffix::Broodling);
        CHECK(effect != MawBossAffix::Omnipotent);
        CHECK_EQ(mawBossEffectAffix(facts), effect);
        CHECK(mawHasBossAffix(facts, effect));
        hidden.insert(facts.crypticAffix);

        // The same seed draws the same hidden affix.
        ActorRulesetFacts again;
        again.level = 50;
        again.familyLevel = 40;
        REQUIRE(monsters.makeBoss(again, seed, uint8_t(MawBossAffix::Cryptic)));
        CHECK_EQ(again.crypticAffix, facts.crypticAffix);
    }

    // Every other rolled affix, the later ones included.
    CHECK_EQ(hidden.size(), 17u);

    // Named Cryptic, shown with the skull alone; its hidden affix acts.
    const ActorRulesetFacts thorn = bossFacts(MawBossAffix::Cryptic, MawBossAffix::Thorn);
    CHECK_EQ(monsters.actorDisplayName(thorn, "Ogre"), "Cryptic Ogre");
    CHECK_EQ(monsters.actorBadges(thorn), std::vector<std::string>{"maw_boss_skull"});
    CHECK(mawHasBossAffix(thorn, MawBossAffix::Thorn));
    CHECK_FALSE(mawHasBossAffix(thorn, MawBossAffix::Reflecting));

    // A save keeps the hidden affix.
    OutdoorWorldRuntime::MapActorState actor;
    actor.rulesetFacts = thorn;
    GameSaveData save;
    save.mapFileName = "oute3.odm";
    save.hasOutdoorRuntimeState = true;
    save.outdoorWorld.mapActors.push_back(actor);
    save.outdoorWorldStates[save.mapFileName] = save.outdoorWorld;
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "openyamm_cryptic_boss.oysav";
    std::string error;
    REQUIRE_MESSAGE(saveGameDataToPath(path, save, error), error.c_str());
    const std::optional<GameSaveData> restored = loadGameDataFromPath(path, error);
    std::filesystem::remove(path);
    REQUIRE_MESSAGE(restored.has_value(), error.c_str());
    REQUIRE_EQ(restored->outdoorWorldStates.at("oute3.odm").mapActors.size(), 1u);
    const ActorRulesetFacts &loaded = restored->outdoorWorldStates.at("oute3.odm").mapActors[0].rulesetFacts;
    CHECK_EQ(loaded.bossAffix, uint8_t(MawBossAffix::Cryptic));
    CHECK_EQ(loaded.crypticAffix, uint8_t(MawBossAffix::Thorn));
}

TEST_CASE("MAW Unstoppable bosses shrug off crowd control")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const SpellRules &spells = rules.gameRules().spells;
    Character caster = member(20);
    caster.className = "Cleric";
    const ActorRulesetFacts plain = bossFacts(MawBossAffix::Thorn);
    const ActorRulesetFacts unstoppable = bossFacts(MawBossAffix::Unstoppable);
    const ActorRulesetFacts cryptic = bossFacts(MawBossAffix::Cryptic, MawBossAffix::Unstoppable);
    uint64_t key = 1;

    const auto cast = [&](uint32_t spellId, const ActorRulesetFacts &target)
    {
        CrowdControlCast spell;
        spell.spellId = spellId;
        spell.mastery = SkillMastery::Grandmaster;
        spell.skillLevel = 10;
        spell.pCaster = &caster;
        spell.boss = true;
        spell.targetLevel = 1;
        spell.pTargetFacts = &target;
        spell.targetKey = key++;
        spell.partySize = 4;
        return spells.crowdControlSeconds(spell);
    };

    // Slow, Charm, Mass Fear, Paralyze, Dark Grasp, Turn Undead and Dragon Fear hold any other boss.
    for (const uint32_t spellId : {35u, 60u, 63u, 81u, 96u, 48u, 122u})
    {
        CAPTURE(spellId);
        CHECK(cast(spellId, plain).value_or(0) > 0);
        CHECK_EQ(cast(spellId, unstoppable).value_or(-1), 0.0f);
        CHECK_EQ(cast(spellId, cryptic).value_or(-1), 0.0f);
    }

    // Stun (34) always fails on one.
    for (int trial = 0; trial < 50; ++trial)
    {
        CHECK_EQ(cast(34, unstoppable).value_or(-1), 0.0f);
    }

    // Spells that are not crowd control keep the engine's own handling.
    CHECK_FALSE(cast(spellIdValue(SpellId::DispelMagic), unstoppable).has_value());

    // CC targeting and splash pass it over.
    CHECK(spells.ignoresCrowdControl(unstoppable));
    CHECK(spells.ignoresCrowdControl(cryptic));
    CHECK_FALSE(spells.ignoresCrowdControl(plain));
    CHECK_FALSE(spells.ignoresCrowdControl(bossFacts(MawBossAffix::Omnipotent)));
    CHECK_FALSE(standardGameRules().spells.ignoresCrowdControl(unstoppable));

    // Retaliation's stun: a Grandmaster's three stacks stun 75 % of blows, never an Unstoppable boss.
    ItemTable items;
    Character knight = member(20);
    knight.skills["Retaliation"] = {"Retaliation", 10, SkillMastery::Grandmaster};
    std::mt19937 rng(5);
    const auto paralyses = [&](const ActorRulesetFacts &target)
    {
        int count = 0;

        for (int blow = 0; blow < 200; ++blow)
        {
            knight.rulesetState.runtime.retaliationStacks = 3;
            CharacterAttackOnMonster context;
            context.pCharacter = &knight;
            context.pItemTable = &items;
            context.pTargetFacts = &target;
            context.minimumDamage = 10;
            context.maximumDamage = 20;
            context.pRng = &rng;
            CharacterAttackResult attack;
            attack.mode = CharacterAttackMode::Melee;
            attack.canAttack = true;
            attack.attackBonus = 100000;
            rules.gameRules().combat.resolveCharacterAttack(attack, context);
            count += attack.hit && attack.paralyzeTarget ? 1 : 0;
        }

        return count;
    };
    CHECK_GT(paralyses(plain), 100);
    CHECK_EQ(paralyses(unstoppable), 0);
}

TEST_CASE("MAW Berserker bosses hit up to twice as hard as their health runs out")
{
    CHECK(mawBerserkerDamageMultiplier(100, 100) == doctest::Approx(1));
    CHECK(mawBerserkerDamageMultiplier(25, 100) == doctest::Approx(1.75));
    CHECK(mawBerserkerDamageMultiplier(0, 100) == doctest::Approx(2));

    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const CombatRules &combat = rules.gameRules().combat;
    const Character target = member(20);
    const auto taken = [&](MawBossAffix affix, int currentHp)
    {
        CharacterDamageHit hit;
        hit.amount = 100;
        hit.pCharacter = &target;
        hit.monsterAttack = true;
        hit.attackerLevel = 20;
        hit.attackerFacts = bossFacts(affix);
        hit.attackerFacts.level = 20;
        hit.attackerFacts.familyLevel = 20;
        hit.attackerFacts.attack1Damage = 200;
        hit.attackerCurrentHp = currentHp;
        hit.attackerMaxHp = 1000;
        std::mt19937 rng(9);
        hit.pRng = &rng;
        return combat.damageToCharacter(hit);
    };
    const int full = taken(MawBossAffix::Berserker, 1000);
    REQUIRE(full > 20);
    CHECK(taken(MawBossAffix::Berserker, 500) == doctest::Approx(full * 1.5).epsilon(0.03));
    CHECK(taken(MawBossAffix::Berserker, 0) == doctest::Approx(full * 2).epsilon(0.03));
    CHECK_EQ(taken(MawBossAffix::Thorn, 0), taken(MawBossAffix::Thorn, 1000));
    CHECK_EQ(taken(MawBossAffix::Thorn, 1000), full);
}

TEST_CASE("MAW Skilled bosses dodge the party's weapons and cannot be dodged")
{
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    const CombatRules &combat = rules.gameRules().combat;
    ItemTable items;
    Character knight = member(20);
    std::mt19937 rng(3);
    const ActorRulesetFacts plain = bossFacts(MawBossAffix::Thorn);
    const ActorRulesetFacts skilled = bossFacts(MawBossAffix::Skilled);
    const ActorRulesetFacts cryptic = bossFacts(MawBossAffix::Cryptic, MawBossAffix::Skilled);
    constexpr int Trials = 4000;

    const auto meleeHitShare = [&](const ActorRulesetFacts &target)
    {
        int hits = 0;

        for (int trial = 0; trial < Trials; ++trial)
        {
            CharacterAttackOnMonster context;
            context.pCharacter = &knight;
            context.pItemTable = &items;
            context.pTargetFacts = &target;
            context.minimumDamage = 10;
            context.maximumDamage = 20;
            context.pRng = &rng;
            CharacterAttackResult attack;
            attack.mode = CharacterAttackMode::Melee;
            attack.canAttack = true;
            attack.attackBonus = 100000;
            combat.resolveCharacterAttack(attack, context);
            hits += attack.hit ? 1 : 0;
        }

        return double(hits) / Trials;
    };
    const double plainShare = meleeHitShare(plain);
    REQUIRE(plainShare > 0.9);
    CHECK(meleeHitShare(skilled) == doctest::Approx(plainShare * 0.6).epsilon(0.05));
    CHECK(meleeHitShare(cryptic) == doctest::Approx(plainShare * 0.6).epsilon(0.05));

    const auto missileHitShare = [&](const ActorRulesetFacts &target)
    {
        int hits = 0;

        for (int trial = 0; trial < Trials; ++trial)
        {
            CharacterMissileOnMonster missile;
            missile.attackBonus = 100000;
            missile.targetFacts = target;
            missile.pRng = &rng;
            hits += combat.characterMissileHits(missile) ? 1 : 0;
        }

        return double(hits) / Trials;
    };
    const double plainMissiles = missileHitShare(plain);
    REQUIRE(plainMissiles > 0.9);
    CHECK(missileHitShare(skilled) == doctest::Approx(plainMissiles * 0.6).epsilon(0.05));

    // A fast Grandmaster dodger evades other monsters now and then, a Skilled boss never.
    Character dodger = member(20);
    dodger.speed = 500;
    dodger.skills["Dodging"] = {"Dodging", 60, SkillMastery::Grandmaster};
    const auto evasions = [&](const ActorRulesetFacts &attacker)
    {
        int evaded = 0;

        for (int trial = 0; trial < 1000; ++trial)
        {
            MonsterAttackOnCharacter attack;
            attack.pCharacter = &dodger;
            attack.monsterLevel = 5;
            attack.missileToken = "Arrow";
            attack.pAttackerFacts = &attacker;
            attack.pRng = &rng;
            evaded += combat.characterEvades(attack) ? 1 : 0;
        }

        return evaded;
    };
    CHECK_GT(evasions(plain), 100);
    CHECK_EQ(evasions(skilled), 0);
    CHECK_EQ(evasions(cryptic), 0);
}

TEST_CASE("MAW Skilled bosses drop four Horseshoes")
{
    constexpr uint32_t Horseshoe = 656;
    MonsterTable monsterTable;
    std::vector<std::string> row(38);
    row[0] = "195";
    row[1] = row[2] = "Human Mercenary C";
    row[3] = "24";
    row[4] = "100";
    row[10] = "Short";
    row[11] = "Normal";
    row[17] = "Phys";
    row[18] = "1d6";
    REQUIRE(monsterTable.loadStatsFromRows({row}));
    MapStatsEntry map = {};
    map.fileName = "out05.odm";
    MawRules rules(RulesetOptions{}, MawMapLevels{}, installedItemData(), MawPromotionData{}, installedCraftingData());
    const MonsterRules &monsters = rules.gameRules().monsters;
    const auto horseshoes = [&](const ActorRulesetFacts &facts, CorpseLootPart part)
    {
        CorpseLootContext context;
        context.pStats = monsterTable.findStatsById(195);
        context.pMonsterTable = &monsterTable;
        context.pFacts = &facts;
        context.pMap = &map;
        context.part = part;
        const CorpseLoot loot = monsters.corpseLoot(context);
        return std::count_if(loot.extraItems.begin(), loot.extraItems.end(),
            [](const CorpseLoot::ExtraItem &item) { return item.itemId == Horseshoe; });
    };

    CHECK_EQ(horseshoes(bossFacts(MawBossAffix::Skilled), CorpseLootPart::Extras), 4);
    CHECK_EQ(horseshoes(bossFacts(MawBossAffix::Cryptic, MawBossAffix::Skilled), CorpseLootPart::Extras), 4);
    CHECK_EQ(horseshoes(bossFacts(MawBossAffix::Thorn), CorpseLootPart::Extras), 0);
    // Not at Telepathy's look, nor from a risen one.
    CHECK_EQ(horseshoes(bossFacts(MawBossAffix::Skilled), CorpseLootPart::Table), 0);
    ActorRulesetFacts risen = bossFacts(MawBossAffix::Skilled);
    risen.risen = true;
    CHECK_EQ(horseshoes(risen, CorpseLootPart::Extras), 0);
}

TEST_CASE("MAW Dragon Fear lasts by its Dragon Ability mastery, without Ascension or resistance (S1)")
{
    const MawCrowdControlSpell *pFear = mawCrowdControlSpell(122);
    REQUIRE(pFear != nullptr);
    // Real seconds: 4 x {0.5, 0.65, 0.8, 1} x 2.
    CHECK(2 * mawCrowdControlMinutes(*pFear, SkillMastery::Normal, 0, 0, false) == doctest::Approx(4));
    CHECK(2 * mawCrowdControlMinutes(*pFear, SkillMastery::Expert, 0, 0, false) == doctest::Approx(5.2));
    CHECK(2 * mawCrowdControlMinutes(*pFear, SkillMastery::Master, 50, 100, false) == doctest::Approx(6.4));
    CHECK(2 * mawCrowdControlMinutes(*pFear, SkillMastery::Grandmaster, 50, 100, false) == doctest::Approx(8));
    CHECK(2 * mawCrowdControlMinutes(*pFear, SkillMastery::Grandmaster, 0, 0, true) == doctest::Approx(16));

    // Through the rules: the cast's mastery is its Dragon Ability's; diminishing returns still apply.
    MawRules rules(RulesetOptions{}, MawMapLevels{});
    Character dragon = member(20);
    dragon.className = "Dragon";
    dragon.raceId = 5;
    CrowdControlCast cast;
    cast.spellId = 122;
    cast.mastery = SkillMastery::Grandmaster;
    cast.skillLevel = 20;
    cast.pCaster = &dragon;
    cast.resistance = 50;
    cast.targetKey = 9;
    cast.partySize = 4;
    CHECK(rules.gameRules().spells.crowdControlSeconds(cast).value_or(0) == doctest::Approx(8));
    cast.nowSeconds = 8;
    CHECK(rules.gameRules().spells.crowdControlSeconds(cast).value_or(0) == doctest::Approx(4));
}
