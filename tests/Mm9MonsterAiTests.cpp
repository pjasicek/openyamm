#include <doctest/doctest.h>

#include "game/gameplay/ActorBehaviorCatalog.h"
#include "game/gameplay/ActorBehaviorRuntime.h"
#include "game/maps/SaveGame.h"
#include "game/tables/Mm9MonsterAi.h"
#include "game/tables/MonsterModifiers.h"

#include <yaml-cpp/yaml.h>

#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>

using namespace OpenYAMM::Game;

namespace
{
bool loadMm9(MonsterModifierTable &table, const std::string &body, std::string &error)
{
    return table.loadWorldYaml("schema: openyamm.monsterModifiers.v1\nmonsters:\n" + body, "mm9", 9000, 9999, error);
}

std::string mm9Error(const std::string &body)
{
    MonsterModifierTable table;
    std::string error;
    CHECK_FALSE(loadMm9(table, body, error));
    return error;
}

// The generated MM9 table (tools/mm9_import_discovery/generate_mm9_monster_modifiers.py).
const MonsterModifierTable &generatedMm9Modifiers()
{
    static const MonsterModifierTable table = []()
    {
        std::ifstream file(std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds/mm9/modifiers.yml");
        std::stringstream text;
        text << file.rdbuf();
        MonsterModifierTable loaded;
        std::string error;
        REQUIRE_MESSAGE(loaded.loadWorldYaml(text.str(), "mm9", 9000, 9999, error), error);
        return loaded;
    }();
    return table;
}

const Mm9AiProfile &generatedProfile(int16_t monsterId)
{
    const MonsterModifierSet *pSet = generatedMm9Modifiers().find(monsterId);
    REQUIRE(pSet != nullptr);
    REQUIRE(pSet->mm9Ai.has_value());
    return *pSet->mm9Ai;
}

Mm9AiPlacementRecord placement(const std::string &yaml)
{
    Mm9AiPlacementRecord record;
    std::string error;
    REQUIRE_MESSAGE(parseMm9AiPlacementNode(YAML::Load(yaml), record, error), error);
    return record;
}

std::string placementError(const std::string &yaml)
{
    Mm9AiPlacementRecord record;
    std::string error;
    CHECK_FALSE(parseMm9AiPlacementNode(YAML::Load(yaml), record, error));
    return error;
}
}

TEST_CASE("mm9_ai parses its archetype, numbers and hooks, with defaults and consistency checks")
{
    MonsterModifierTable table;
    std::string error;
    REQUIRE_MESSAGE(loadMm9(table,
        "  9086: [{mm9_ai: {archetype: turret, attack_reach: 20, melee_sweep: 154, pod_launch: 9084,\n"
        "      eye_below_top: 12}}]\n"
        "  9087: [{mm9_ai: {archetype: flier, movement: fly, ranged: flier, wince: never, fly_speed: 768,\n"
        "      dormant_until: disturbed, dormant_pose: hang, melee_window_seconds: 5}}]\n"
        "  9148: [skirmisher, {mm9_ai: {archetype: skirmisher, throttle: false, resurrecter: true}}]\n",
        error),
        error);

    const Mm9AiProfile &lobber = *table.find(9086)->mm9Ai;
    CHECK(lobber.archetype == Mm9AiArchetype::Turret);
    CHECK(lobber.movement == Mm9AiMovement::Walk);
    CHECK(lobber.ranged == Mm9AiRanged::None);
    CHECK(lobber.wince == Mm9AiWince::LowHealth);
    CHECK(lobber.attackReach == doctest::Approx(20.0f));
    CHECK(lobber.alertRadius == doctest::Approx(3072.0f));
    CHECK(lobber.podLaunchMonsterId == 9084);
    CHECK(lobber.podCooldownMinSeconds == doctest::Approx(5.0f));
    CHECK(lobber.podCooldownMaxSeconds == doctest::Approx(10.0f));
    CHECK(lobber.throttle);
    CHECK(lobber.dormantUntil == Mm9AiDormantUntil::None);
    CHECK(lobber.eyeBelowTop == doctest::Approx(12.0f));

    const Mm9AiProfile &icky = *table.find(9087)->mm9Ai;
    CHECK(icky.archetype == Mm9AiArchetype::Flier);
    CHECK(icky.movement == Mm9AiMovement::Fly);
    CHECK(icky.ranged == Mm9AiRanged::Flier);
    CHECK(icky.wince == Mm9AiWince::Never);
    CHECK(icky.dormantUntil == Mm9AiDormantUntil::Disturbed);
    CHECK(icky.dormantPose == Mm9AiDormantPose::Hang);
    CHECK(icky.meleeWindowSeconds == doctest::Approx(5.0f));
    // MM9's GetEyePos: 2 LT below the top.
    CHECK(icky.eyeBelowTop == doctest::Approx(5.12f));

    const MonsterModifierSet &dagrell = *table.find(9148);
    CHECK(dagrell.skirmisher.has_value());
    CHECK_FALSE(dagrell.mm9Ai->throttle);
    CHECK(dagrell.mm9Ai->resurrecter);
    CHECK(table.hasMm9Ai());

    CHECK(mm9Error("  9001: [{mm9_ai: {attack_reach: 10}}]\n").find("needs its archetype") != std::string::npos);
    CHECK(mm9Error("  9001: [{mm9_ai: {archetype: brawler}}]\n").find("must be one of") != std::string::npos);
    CHECK(mm9Error("  9001: [{mm9_ai: {archetype: flier}}]\n").find("needs movement fly") != std::string::npos);
    CHECK(mm9Error("  9001: [{mm9_ai: {archetype: swimmer, movement: fly}}]\n").find("needs movement swim")
        != std::string::npos);
    CHECK(mm9Error("  9001: [{mm9_ai: {archetype: crawler, pod_launch: 9084}}]\n").find("belongs to a turret")
        != std::string::npos);
    CHECK(mm9Error("  9001: [{mm9_ai: {archetype: crawler, dormant_pose: hang}}]\n").find("dormant_pose needs it")
        != std::string::npos);
    CHECK(mm9Error("  9001: [{mm9_ai: {archetype: crawler, attack_reach: -1}}]\n").find("must be a number")
        != std::string::npos);
}

TEST_CASE("the generated MM9 profiles map known rows to their archetypes")
{
    // Skeletoid (183, basemelee.scr): a skirmisher that raises its dead, never winces; keeps its footwork.
    const Mm9AiProfile &skeletoid = generatedProfile(9183);
    CHECK(skeletoid.archetype == Mm9AiArchetype::Skirmisher);
    CHECK(skeletoid.movement == Mm9AiMovement::Walk);
    CHECK(skeletoid.ranged == Mm9AiRanged::None);
    CHECK(skeletoid.resurrecter);
    CHECK(skeletoid.wince == Mm9AiWince::Never);
    CHECK(skeletoid.meleeSweep == doctest::Approx(54.0f));     // AttackRange 42 x Scale 0.5 x 2.56
    CHECK(generatedMm9Modifiers().find(9183)->skirmisher.has_value());

    // Evil Sorcerer (157, EvilSorcerer.scr): Range.inc type 2, never chases.
    const Mm9AiProfile &sorcerer = generatedProfile(9157);
    CHECK(sorcerer.archetype == Mm9AiArchetype::RangedHolder);
    CHECK(sorcerer.ranged == Mm9AiRanged::Walker);
    CHECK(sorcerer.alertRadius == doctest::Approx(4096.0f));    // AlertRadius 1600 x 2.56

    // Jellyspore (168, BaseSwim.scr, an AISwimFly class with Fly 1): swims.
    const Mm9AiProfile &jellyspore = generatedProfile(9168);
    CHECK(jellyspore.archetype == Mm9AiArchetype::Swimmer);
    CHECK(jellyspore.movement == Mm9AiMovement::Swim);

    // Lobber (86, lobber.scr): a rooted turret that launches Lobber Pods.
    const Mm9AiProfile &lobber = generatedProfile(9086);
    CHECK(lobber.archetype == Mm9AiArchetype::Turret);
    CHECK(lobber.podLaunchMonsterId == 9084);
    CHECK(lobber.runSpeed == 0.0f);
    CHECK(generatedProfile(9084).alwaysEvade);

    // Commoner (1, NPCbase.scr): a civilian with no ranged add-on.
    const Mm9AiProfile &commoner = generatedProfile(9001);
    CHECK(commoner.archetype == Mm9AiArchetype::Civilian);
    CHECK(commoner.ranged == Mm9AiRanged::None);
    CHECK_FALSE(generatedMm9Modifiers().find(9001)->skirmisher.has_value());

    // Hooks: the Flying Icky hangs, the Airborne Icky does not; Town Guards police; ghosts hover on the walker loop.
    CHECK(generatedProfile(9088).dormantPose == Mm9AiDormantPose::Hang);
    CHECK(generatedProfile(9087).dormantUntil == Mm9AiDormantUntil::None);
    CHECK(generatedProfile(9107).archetype == Mm9AiArchetype::Guard);
    CHECK(generatedProfile(9138).archetype == Mm9AiArchetype::Skirmisher);
    CHECK(generatedProfile(9138).movement == Mm9AiMovement::Fly);
    CHECK(generatedProfile(9212).boss);
    // A cast recovers by its spell's own recovery (SPELL.txt at its mastery, 33 ms per game second): the Dragon King's
    // Column of Fire at Grandmaster, 90 game seconds.
    CHECK_EQ(generatedProfile(9212).spell1RecoverySeconds, doctest::Approx(2.97f));
    CHECK(generatedProfile(9212).archetype == Mm9AiArchetype::Turret);

    // Lobber Pods and the Ice Lobbercicle (lobberpod.scr): melee only, a 1.8-2.2 s evade after every attack.
    for (const int16_t pod : {9084, 9085, 9105})
    {
        CHECK(generatedProfile(pod).ranged == Mm9AiRanged::None);
        CHECK(generatedProfile(pod).alwaysEvade);
        CHECK(generatedProfile(pod).evadeMinSeconds == doctest::Approx(1.8f));
        CHECK(generatedProfile(pod).evadeMaxSeconds == doctest::Approx(2.2f));
    }

    // No MM9 row holds a ranged weapon prop: every monster in reach strikes its blow.
    for (const auto &[monsterId, set] : generatedMm9Modifiers().sets())
    {
        const bool rangedWeapon = set.mm9Ai && set.mm9Ai->rangedWeapon;
        CHECK_MESSAGE(!rangedWeapon, monsterId);
    }
}

TEST_CASE("an MM9 scene placement parses its settings, markers and patterns")
{
    const Mm9AiPlacementRecord record = placement(R"({"sight": 1536, "hearing": 369, "runaway_chance": 0.05,
        "ranged_type": 2, "can_be_resurrected": true, "wander": "path", "path": [[1, 2, 3], [4, 5, 6]],
        "path_random": true, "wander_wait": [3, 10], "wander_time": [3, 6],
        "dormant": {"until": "trigger", "pose": "hang"}, "hostility": "hostile_after_event", "faction": "dook",
        "summon": {"class": "Skeletoid", "points": [[7, 8, 9]]}, "boss": true, "hiding_places": [[10, 11, 12]],
        "script": "ll_flyingcreature.scr", "script_params": "2ndLeftWMarker 0 6"})");
    const Mm9AiPlacement &settings = record.settings;
    CHECK(settings.sight == doctest::Approx(1536.0f));
    CHECK(settings.hearing == doctest::Approx(369.0f));
    CHECK(settings.runawayChance == doctest::Approx(0.05f));
    CHECK(settings.rangedType == 2);
    CHECK(settings.canBeResurrected);
    CHECK(settings.wander == Mm9AiWanderMode::Path);
    CHECK(settings.pathRandom);
    CHECK(settings.wanderWaitMaxSeconds == doctest::Approx(10.0f));
    CHECK(settings.wanderTimeMaxSeconds == doctest::Approx(6.0f));
    CHECK(settings.dormantUntil == Mm9AiDormantUntil::Trigger);
    CHECK(settings.dormantPose == Mm9AiDormantPose::Hang);
    CHECK(settings.hostility == Mm9AiHostility::HostileAfterEvent);
    CHECK(settings.faction == Mm9AiFaction::Dook);
    CHECK(settings.summoner);
    CHECK(settings.boss);
    CHECK_FALSE(settings.startsDead);
    REQUIRE(record.pathPoints.size() == 2);
    CHECK(record.pathPoints[1] == std::array<int32_t, 3>{4, 5, 6});
    REQUIRE(record.summonPoints.size() == 1);
    REQUIRE(record.hidingPlaces.size() == 1);
    CHECK(record.hidingPlaces[0] == std::array<int32_t, 3>{10, 11, 12});
    CHECK(record.summonClass == "Skeletoid");
    CHECK(record.script == "ll_flyingcreature.scr");
    CHECK(record.scriptParams == "2ndLeftWMarker 0 6");

    // MM9's defaults for what a placement leaves out.
    const Mm9AiPlacementRecord plain = placement("{sight: 1536}");
    CHECK(plain.settings.hearing == doctest::Approx(922.0f));
    CHECK(plain.settings.runawayChance == doctest::Approx(0.25f));
    CHECK(plain.settings.rangedType == 1);
    CHECK(plain.settings.wander == Mm9AiWanderMode::Off);
    CHECK(plain.settings.dormantUntil == Mm9AiDormantUntil::None);

    CHECK(placementError("{sights: 1}").find("no key 'sights'") != std::string::npos);
    CHECK(placementError("{ranged_type: 3}").find("ranged_type") != std::string::npos);
    CHECK(placementError("{runaway_chance: 2}").find("runaway_chance") != std::string::npos);
    CHECK(placementError("{wander: path, path: [[1, 2, 3]]}").find("two points") != std::string::npos);
    CHECK(placementError("{dormant: {pose: hang}}").find("dormant") != std::string::npos);
    CHECK(placementError("{wander_wait: [5, 3]}").find("wander_wait") != std::string::npos);
}

TEST_CASE("an MM9 placement parses the profile its own script decides")
{
    const Mm9AiPlacementRecord record = placement(R"({"profile": {"archetype": "skirmisher", "ranged": "none",
        "throttle": true, "guard_refuge": false, "evade_min_seconds": 1.8, "evade_max_seconds": 2.2,
        "skirmisher": {"evade_chance": 0.4, "strafe_attack_chance": 0.0, "taunt_seconds": 1.5}},
        "script": "kingkong.scr"})");
    const Mm9AiPlacementProfile &profile = record.settings.profile;
    CHECK(profile.archetype == std::optional<Mm9AiArchetype>(Mm9AiArchetype::Skirmisher));
    CHECK(profile.ranged == std::optional<Mm9AiRanged>(Mm9AiRanged::None));
    CHECK(profile.throttle == std::optional<bool>(true));
    CHECK(profile.guardRefuge == std::optional<bool>(false));
    REQUIRE(profile.evadeMinSeconds.has_value());
    CHECK(*profile.evadeMinSeconds == doctest::Approx(1.8f));
    CHECK_FALSE(profile.alwaysEvade.has_value());
    CHECK_FALSE(profile.passive);
    REQUIRE(profile.footwork.has_value());
    CHECK(profile.footwork->enabled);
    CHECK(profile.footwork->strafeAttackChance == doctest::Approx(0.0f));
    CHECK(profile.footwork->tauntSeconds == doctest::Approx(1.5f));

    const Mm9AiPlacementRecord inert = placement("{profile: {passive: true, skirmisher: false}}");
    CHECK(inert.settings.profile.passive);
    REQUIRE(inert.settings.profile.footwork.has_value());
    CHECK_FALSE(inert.settings.profile.footwork->enabled);
    CHECK(placement("{sight: 1}").settings.profile == Mm9AiPlacementProfile{});

    CHECK(placementError("{profile: {archetypes: crawler}}").find("no key 'archetypes'") != std::string::npos);
    CHECK(placementError("{profile: {ranged: bow}}").find("profile.ranged") != std::string::npos);
    CHECK(placementError("{profile: {skirmisher: true}}").find("skirmisher") != std::string::npos);
    CHECK(placementError("{profile: {skirmisher: {lunge: 1}}}").find("no key 'lunge'") != std::string::npos);
    CHECK(placementError("{profile: {evade_min_seconds: 3, evade_max_seconds: 2}}").find("evade_min_seconds")
        != std::string::npos);
}

TEST_CASE("a placement's own script decides its loop over its row's")
{
    // A Ghast (row 174, baserange.scr: Range.inc) placed with KingKong.scr: BaseMelee without Range.inc.
    Mm9AiProfile ghast;
    ghast.archetype = Mm9AiArchetype::Skirmisher;
    ghast.ranged = Mm9AiRanged::Walker;
    ghast.alertRadius = 4096.0f;
    Mm9AiPlacement kingKong;
    kingKong.profile.ranged = Mm9AiRanged::None;
    const Mm9AiProfile caged = placedMm9AiProfile(ghast, kingKong);
    CHECK(caged.ranged == Mm9AiRanged::None);
    CHECK(caged.archetype == Mm9AiArchetype::Skirmisher);
    CHECK(caged.alertRadius == doctest::Approx(4096.0f));

    // Range.inc's type 2 needs the placement's own Range.inc: KingKong.scr has none, so no holder.
    kingKong.rangedType = 2;
    CHECK(placedMm9AiProfile(ghast, kingKong).archetype == Mm9AiArchetype::Skirmisher);

    // A script that adds Range.inc (MonkGuardBasic.scr on a monk) makes a placed type 2 a holder.
    Mm9AiProfile monk;
    Mm9AiPlacement guardBasic;
    guardBasic.profile.ranged = Mm9AiRanged::Walker;
    guardBasic.rangedType = 2;
    CHECK(placedMm9AiProfile(monk, guardBasic).archetype == Mm9AiArchetype::RangedHolder);

    // A dialogue-only script (Sturmguard.scr): passive on its row's guard loop.
    Mm9AiProfile guard;
    guard.archetype = Mm9AiArchetype::Guard;
    Mm9AiPlacement sturmguard;
    sturmguard.profile.passive = true;
    const Mm9AiProfile prisonGuard = placedMm9AiProfile(guard, sturmguard);
    CHECK(prisonGuard.passive);
    CHECK(prisonGuard.archetype == Mm9AiArchetype::Guard);
    CHECK_FALSE(placedMm9AiProfile(guard, Mm9AiPlacement{}).passive);
}

TEST_CASE("a placement overrides its row's dormant start and turns a ranged walker into a holder")
{
    Mm9AiProfile row;
    row.archetype = Mm9AiArchetype::Skirmisher;
    row.ranged = Mm9AiRanged::Walker;
    row.dormantUntil = Mm9AiDormantUntil::Disturbed;
    row.dormantPose = Mm9AiDormantPose::Hang;

    Mm9AiPlacement placed;
    CHECK(placedMm9AiProfile(row, placed).archetype == Mm9AiArchetype::Skirmisher);
    CHECK(placedMm9AiProfile(row, placed).dormantPose == Mm9AiDormantPose::Hang);

    placed.rangedType = 2;
    placed.dormantUntil = Mm9AiDormantUntil::Trigger;
    placed.dormantPose = Mm9AiDormantPose::Underground;
    const Mm9AiProfile profile = placedMm9AiProfile(row, placed);
    CHECK(profile.archetype == Mm9AiArchetype::RangedHolder);
    CHECK(profile.dormantUntil == Mm9AiDormantUntil::Trigger);
    CHECK(profile.dormantPose == Mm9AiDormantPose::Underground);

    // Type 2 needs Range.inc: a pure melee skirmisher, a flier or a civilian keeps its loop.
    row.ranged = Mm9AiRanged::None;
    CHECK(placedMm9AiProfile(row, placed).archetype == Mm9AiArchetype::Skirmisher);
    row.archetype = Mm9AiArchetype::Flier;
    row.ranged = Mm9AiRanged::Flier;
    CHECK(placedMm9AiProfile(row, placed).archetype == Mm9AiArchetype::Flier);
}

TEST_CASE("MM9 profiles reach the AI facts without giving their monsters tactics")
{
    MonsterModifierTable table;
    std::string error;
    REQUIRE_MESSAGE(loadMm9(table,
        "  9168: [{mm9_ai: {archetype: swimmer, movement: swim, attack_reach: 113}}]\n"
        "  9183: [skirmisher, {mm9_ai: {archetype: skirmisher, ranged: walker}}]\n",
        error),
        error);

    ActorBehaviorCatalog catalog;
    REQUIRE(catalog.applyMonsterModifiers(table, error));
    CHECK(catalog.tacticsForMonster(9168) == nullptr);
    REQUIRE(catalog.tacticsForMonster(9183) != nullptr);
    CHECK(catalog.hasMm9AiProfiles());
    REQUIRE(catalog.mm9AiProfileForMonster(9168) != nullptr);
    CHECK(catalog.mm9AiProfileForMonster(10001) == nullptr);

    ActorBehaviorRuntime runtime;
    runtime.bind(&catalog, nullptr);
    ActorAiFrameFacts facts = {};
    facts.fixedStepSeconds = 1.0f / 128.0f;
    ActorAiFacts swimmer = {};
    swimmer.actorIndex = 0;
    swimmer.identity.monsterId = 9168;
    ActorAiFacts skirmisher = {};
    skirmisher.actorIndex = 1;
    skirmisher.identity.monsterId = 9183;
    Mm9AiPlacement holder;
    holder.rangedType = 2;
    holder.sight = 1536.0f;
    skirmisher.movement.mm9Placement = holder;
    ActorAiFacts other = {};
    other.actorIndex = 2;
    other.identity.monsterId = 77;
    facts.activeActors = {swimmer, skirmisher, other};
    runtime.applyAiFacts(facts);

    const ActorAiFacts &swimmerFacts = facts.activeActors[0];
    REQUIRE(swimmerFacts.tactics.mm9Profile.has_value());
    CHECK(swimmerFacts.tactics.mm9Profile->archetype == Mm9AiArchetype::Swimmer);
    CHECK_FALSE(swimmerFacts.tactics.skirmish);
    // No placement record (a summon, an old save): MM9's defaults.
    REQUIRE(swimmerFacts.movement.mm9Placement.has_value());
    CHECK(swimmerFacts.movement.mm9Placement->sight == doctest::Approx(3379.0f));

    const ActorAiFacts &skirmisherFacts = facts.activeActors[1];
    CHECK(skirmisherFacts.tactics.skirmish);
    REQUIRE(skirmisherFacts.tactics.mm9Profile.has_value());
    CHECK(skirmisherFacts.tactics.mm9Profile->archetype == Mm9AiArchetype::RangedHolder);
    CHECK(skirmisherFacts.movement.mm9Placement->sight == doctest::Approx(1536.0f));

    // Other worlds' monsters never carry either.
    CHECK_FALSE(facts.activeActors[2].tactics.mm9Profile.has_value());
    CHECK_FALSE(facts.activeActors[2].movement.mm9Placement.has_value());
}

TEST_CASE("a placement script gives or takes the skirmisher footwork, and a pod's evade window reaches its tactics")
{
    MonsterModifierTable table;
    std::string error;
    REQUIRE_MESSAGE(loadMm9(table,
        "  9145: [{mm9_ai: {archetype: crawler}}]\n"
        "  9174: [{skirmisher: {strafe_attack_chance: 0.6}}, {mm9_ai: {archetype: skirmisher, ranged: walker}}]\n"
        "  9084: [{mm9_ai: {archetype: crawler, always_evade: true, evade_min_seconds: 1.8, "
        "evade_max_seconds: 2.2}}]\n",
        error),
        error);
    ActorBehaviorCatalog catalog;
    REQUIRE(catalog.applyMonsterModifiers(table, error));
    ActorBehaviorRuntime runtime;
    runtime.bind(&catalog, nullptr);

    ActorAiFrameFacts facts = {};
    facts.fixedStepSeconds = 1.0f / 128.0f;
    // An Embalmed Mummy on MummyAwaken.scr gains BaseMelee's footwork; a Ghast on Honkies-like wander loses it.
    ActorAiFacts mummy = {};
    mummy.actorIndex = 0;
    mummy.identity.monsterId = 9145;
    Mm9AiPlacement awaken;
    awaken.profile.archetype = Mm9AiArchetype::Skirmisher;
    awaken.profile.footwork = Mm9AiFootwork{true, 0.8f, 0.4f, 4.0f};
    mummy.movement.mm9Placement = awaken;
    ActorAiFacts ghast = {};
    ghast.actorIndex = 1;
    ghast.identity.monsterId = 9174;
    Mm9AiPlacement wander;
    wander.profile.archetype = Mm9AiArchetype::Civilian;
    wander.profile.footwork = Mm9AiFootwork{};
    ghast.movement.mm9Placement = wander;
    ActorAiFacts pod = {};
    pod.actorIndex = 2;
    pod.identity.monsterId = 9084;
    facts.activeActors = {mummy, ghast, pod};
    runtime.applyAiFacts(facts);

    const ActorTacticsFacts &mummyTactics = facts.activeActors[0].tactics;
    CHECK(mummyTactics.skirmish);
    CHECK(mummyTactics.strafeAttackChance == doctest::Approx(0.8f));
    CHECK(mummyTactics.tauntSeconds == doctest::Approx(4.0f));
    CHECK(mummyTactics.tauntChance == doctest::Approx(0.4f));
    CHECK(mummyTactics.mm9Profile->archetype == Mm9AiArchetype::Skirmisher);

    const ActorTacticsFacts &ghastTactics = facts.activeActors[1].tactics;
    CHECK_FALSE(ghastTactics.skirmish);
    CHECK(ghastTactics.mm9Profile->archetype == Mm9AiArchetype::Civilian);

    const ActorTacticsFacts &podTactics = facts.activeActors[2].tactics;
    CHECK(podTactics.skirmish);
    CHECK(podTactics.evadeChance == doctest::Approx(1.0f));
    CHECK(podTactics.strafeAttackChance == doctest::Approx(0.0f));
    CHECK(podTactics.evadeSeconds == doctest::Approx(1.8f));
    CHECK(podTactics.evadeSecondsMax == doctest::Approx(2.2f));
}

TEST_CASE("saves keep a placed actor's MM9 AI settings")
{
    MapDeltaActor actor = {};
    actor.name = "Flying Icky";
    actor.monsterId = 9088;
    Mm9AiPlacementRecord record;
    record.settings.sight = 1536.0f;
    record.settings.rangedType = 2;
    record.settings.wander = Mm9AiWanderMode::Path;
    record.settings.dormantUntil = Mm9AiDormantUntil::Trigger;
    record.settings.dormantPose = Mm9AiDormantPose::Hang;
    record.settings.faction = Mm9AiFaction::Monk;
    record.pathPoints = {{1, 2, 3}, {4, 5, 6}};
    record.summonPoints = {{7, 8, 9}};
    record.hidingPlaces = {{10, 11, 12}};
    record.summonClass = "Skeletoid";
    record.script = "ll_flyingcreature.scr";
    record.scriptParams = "1stRightWMarker 0 7";
    record.settings.profile.archetype = Mm9AiArchetype::Crawler;
    record.settings.profile.ranged = Mm9AiRanged::None;
    record.settings.profile.evadeMaxSeconds = 2.2f;
    record.settings.profile.passive = true;
    record.settings.profile.footwork = Mm9AiFootwork{true, 0.5f, 0.3f, 1.25f};
    actor.mm9Ai = record;
    MapDeltaActor plain = {};
    plain.name = "Goblin";

    GameSaveData save;
    save.mapFileName = "thearena.blv";
    MapDeltaData delta = {};
    delta.actors = {actor, plain};
    save.indoorSceneStates["thearena.blv"].mapDeltaData = delta;

    const std::filesystem::path path = std::filesystem::temp_directory_path() / "openyamm_mm9_ai_placement.oysav";
    std::string error;
    REQUIRE_MESSAGE(saveGameDataToPath(path, save, error), error.c_str());
    const std::optional<GameSaveData> restored = loadGameDataFromPath(path, error);
    std::filesystem::remove(path);
    REQUIRE_MESSAGE(restored.has_value(), error.c_str());

    const std::optional<MapDeltaData> &loaded = restored->indoorSceneStates.at("thearena.blv").mapDeltaData;
    REQUIRE(loaded.has_value());
    REQUIRE(loaded->actors.size() == 2);
    REQUIRE(loaded->actors[0].mm9Ai.has_value());
    CHECK(*loaded->actors[0].mm9Ai == record);
    CHECK_FALSE(loaded->actors[1].mm9Ai.has_value());
}
