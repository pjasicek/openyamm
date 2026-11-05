#include <doctest/doctest.h>

#include "game/gameplay/ActorBehaviorCatalog.h"
#include "game/gameplay/GameplayActorModifiers.h"
#include "game/gameplay/GameplayActorService.h"
#include "game/gameplay/GameplayProjectileService.h"
#include "game/gameplay/GameplayRuntimeInterfaces.h"
#include "game/gameplay/MonsterSpellSupport.h"
#include "game/party/SpellIds.h"
#include "game/tables/MonsterModifiers.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <string>

using namespace OpenYAMM::Game;

namespace
{
constexpr float Pi = 3.14159265f;

bool loadModifiers(MonsterModifierTable &table, const std::string &body, std::string &error)
{
    return table.loadWorldYaml("schema: openyamm.monsterModifiers.v1\nmonsters:\n" + body, "hesper", 10000, 10999,
        error);
}

std::string modifierError(const std::string &body)
{
    MonsterModifierTable table;
    std::string error;
    CHECK_FALSE(loadModifiers(table, body, error));
    return error;
}

float headingDegreesBetween(float ax, float ay, float az, float bx, float by, float bz)
{
    const float dot = ax * bx + ay * by + az * bz;
    const float lengths = std::sqrt((ax * ax + ay * ay + az * az) * (bx * bx + by * by + bz * bz));
    return std::acos(std::clamp(dot / lengths, -1.0f, 1.0f)) * 180.0f / Pi;
}
}

TEST_CASE("monster modifiers load names, parameters with defaults and id ranges")
{
    MonsterModifierTable table;
    std::string error;
    REQUIRE_MESSAGE(loadModifiers(table,
        "  10065: [{true_aim: {turn_degrees_per_second: 90, max_seconds: 3}}, never_staggers]\n"
        "  10050-10052: [never_staggers]\n"
        "  10102: [{kites_party: {min_distance: 1024, max_distance: 3072}}]\n"
        "  10040: [{blink: {on_shield_break: true, cooldown_seconds: 8}}]\n"
        "  10066: [true_aim]\n"
        "  10120: [indoor_meteor_shower]\n", error), error);

    const MonsterModifierSet *pTurret = table.find(10065);
    REQUIRE(pTurret != nullptr);
    REQUIRE(pTurret->trueAim);
    CHECK(pTurret->trueAim->turnRadiansPerSecond == doctest::Approx(Pi / 2.0f));
    CHECK(pTurret->trueAim->maxSeconds == doctest::Approx(3.0f));
    CHECK_FALSE(pTurret->trueAim->expireAfter);
    CHECK(pTurret->neverStaggers);
    CHECK(pTurret->names == std::vector<std::string>{"true_aim", "never_staggers"});

    const MonsterModifierSet *pBastion = table.find(10066);
    REQUIRE(pBastion != nullptr);
    REQUIRE(pBastion->trueAim);
    CHECK(pBastion->trueAim->turnRadiansPerSecond == doctest::Approx(Pi));
    CHECK(pBastion->trueAim->maxSeconds == doctest::Approx(4.0f));
    CHECK_FALSE(pBastion->neverStaggers);
    CHECK_FALSE(pBastion->indoorMeteorShower);
    REQUIRE(table.find(10120) != nullptr);
    CHECK(table.find(10120)->indoorMeteorShower);

    for (int16_t id : {int16_t(10050), int16_t(10051), int16_t(10052)})
    {
        REQUIRE(table.find(id) != nullptr);
        CHECK(table.find(id)->neverStaggers);
        CHECK_FALSE(table.find(id)->trueAim);
    }

    REQUIRE(table.find(10102)->kitesParty);
    CHECK(table.find(10102)->kitesParty->maxDistance == doctest::Approx(3072.0f));
    const MonsterModifierSet *pNoble = table.find(10040);
    REQUIRE(pNoble->blink);
    CHECK(pNoble->blink->onShieldBreak);
    CHECK(pNoble->blink->cooldownSeconds == doctest::Approx(8.0f));
    CHECK(pNoble->blink->maxDistance == doctest::Approx(1024.0f));
    CHECK(pNoble->blink->sound == "monster_blink");
    CHECK(table.hasBlink());
    CHECK(table.find(10053) == nullptr);
    CHECK(table.find(307) == nullptr);
}

TEST_CASE("monster modifier errors name the file, the line and the problem")
{
    CHECK(modifierError("  10065: [tru_aim]\n").find("worlds/hesper/modifiers.yml:3: unknown modifier 'tru_aim'")
        != std::string::npos);
    CHECK(modifierError("  10065: [{true_aim: {turn_rate: 90}}]\n").find(":3: true_aim has no parameter 'turn_rate'")
        != std::string::npos);
    CHECK(modifierError("  10065: [{true_aim: {max_seconds: -1}}]\n").find("true_aim.max_seconds must be a number")
        != std::string::npos);
    CHECK(modifierError("  10065: [{true_aim: {then: bounce}}]\n").find("must be one of straight|expire")
        != std::string::npos);
    CHECK(modifierError("  10065: [{never_staggers: {seconds: 2}}]\n").find("(it takes none)") != std::string::npos);
    CHECK(modifierError("  10081: [energy_immune]\n").find("belongs to shields.yml") != std::string::npos);
    CHECK(modifierError("  10054: [stationary]\n").find("Movement column") != std::string::npos);
    CHECK(modifierError("  10065: [never_staggers, never_staggers]\n").find("listed twice") != std::string::npos);
    CHECK(modifierError("  10050-10052: [never_staggers]\n  10051: [true_aim]\n").find(":4: monster 10051 is listed")
        != std::string::npos);
    CHECK(modifierError("  307: [true_aim]\n").find("outside the world's monster id range") != std::string::npos);
    CHECK(modifierError("  10040: [blink]\n").find("blink needs a trigger") != std::string::npos);
    CHECK(modifierError("  10040: [{kites_party: {min_distance: 900, max_distance: 800}}]\n")
        .find("below max_distance") != std::string::npos);
    CHECK(modifierError("  ten: [true_aim]\n").find("is not a monster id") != std::string::npos);
    CHECK(modifierError("  10065: true_aim\n").find("must list its modifiers") != std::string::npos);

    MonsterModifierTable table;
    std::string error;
    CHECK_FALSE(table.loadWorldYaml("schema: openyamm.shields.v1\n", "hesper", 10000, 10999, error));
    CHECK(error.find("expected schema openyamm.monsterModifiers.v1") != std::string::npos);
}

TEST_CASE("the catalogue lists every modifier with its parameters and defaults")
{
    const MonsterModifierInfo *pTrueAim = findMonsterModifierInfo("true_aim");
    REQUIRE(pTrueAim != nullptr);
    REQUIRE(pTrueAim->parameters.size() == 3);
    CHECK(std::string(pTrueAim->parameters[0].pName) == "turn_degrees_per_second");
    CHECK(pTrueAim->parameters[0].defaultNumber == doctest::Approx(180.0f));
    CHECK(findMonsterModifierInfo("never_staggers") != nullptr);
    CHECK(findMonsterModifierInfo("indoor_meteor_shower") != nullptr);
    CHECK(findMonsterModifierInfo("kites_party") != nullptr);
    CHECK(findMonsterModifierInfo("blink") != nullptr);
    CHECK(findMonsterModifierInfo("charge") != nullptr);
    CHECK(findMonsterModifierInfo("frenzy") != nullptr);
    CHECK(findMonsterModifierInfo("energy_immune") == nullptr);
    CHECK(findMonsterModifierInfo("stagger") != nullptr);
    CHECK(findMonsterModifierInfo("telegraphed_attack") != nullptr);
    CHECK(findMonsterModifierInfo("sounds") != nullptr);
    CHECK(findMonsterModifierInfo("skirmisher") != nullptr);
    CHECK(findMonsterModifierInfo("mm9_ai") != nullptr);
    CHECK(findMonsterModifierInfo("spell_conditions") != nullptr);
    CHECK(findMonsterModifierInfo("reposition") != nullptr);
    CHECK(monsterModifierCatalogue().size() == 14);
}

TEST_CASE("homing steering turns at most the turn rate, keeps the speed and settles on the target")
{
    float vx = 1000.0f;
    float vy = 0.0f;
    float vz = 0.0f;
    // A target straight to the side: one step of 0.1 s at 180 degrees a second turns 18 degrees.
    REQUIRE(GameplayProjectileService::steerVelocityToward(
        vx, vy, vz, {0.0f, 0.0f, 0.0f}, {0.0f, 1000.0f, 0.0f}, 1000.0f, Pi * 0.1f));
    CHECK(headingDegreesBetween(vx, vy, vz, 1.0f, 0.0f, 0.0f) == doctest::Approx(18.0f).epsilon(0.001));
    CHECK(std::sqrt(vx * vx + vy * vy + vz * vz) == doctest::Approx(1000.0f));
    CHECK(vy > 0.0f);

    // Within the step's turn it points straight at the target.
    vx = 1000.0f;
    vy = 0.0f;
    vz = 0.0f;
    REQUIRE(GameplayProjectileService::steerVelocityToward(
        vx, vy, vz, {0.0f, 0.0f, 0.0f}, {1000.0f, 50.0f, 20.0f}, 800.0f, Pi * 0.1f));
    CHECK(headingDegreesBetween(vx, vy, vz, 1000.0f, 50.0f, 20.0f) == doctest::Approx(0.0f).epsilon(0.01));
    CHECK(std::sqrt(vx * vx + vy * vy + vz * vz) == doctest::Approx(800.0f));

    // Straight behind: it still turns (about any perpendicular axis), never flips at once.
    vx = 1000.0f;
    vy = 0.0f;
    vz = 0.0f;
    REQUIRE(GameplayProjectileService::steerVelocityToward(
        vx, vy, vz, {0.0f, 0.0f, 0.0f}, {-1000.0f, 0.0f, 0.0f}, 1000.0f, Pi * 0.1f));
    CHECK(headingDegreesBetween(vx, vy, vz, 1.0f, 0.0f, 0.0f) == doctest::Approx(18.0f).epsilon(0.001));
    CHECK_FALSE(GameplayProjectileService::steerVelocityToward(
        vx, vy, vz, {5.0f, 5.0f, 5.0f}, {5.0f, 5.0f, 5.0f}, 1000.0f, Pi));
}

TEST_CASE("a homing projectile follows a moving target, then flies straight or expires after its time")
{
    using ProjectileState = GameplayProjectileService::ProjectileState;
    ProjectileState projectile = {};
    projectile.velocityX = 1500.0f;
    GameplayProjectileService::ProjectileHoming homing = {};
    homing.turnRadiansPerSecond = Pi;
    homing.maxSeconds = 1.0f;
    homing.speed = 1500.0f;
    projectile.homing = homing;

    // The target walks sideways; the projectile ends up flying at it.
    constexpr float Step = 1.0f / 128.0f;
    GameplayWorldPoint target = {2000.0f, 0.0f, 0.0f};

    for (int step = 0; step < 96; ++step)
    {
        target.y += 600.0f * Step;
        REQUIRE_FALSE(GameplayProjectileService::steerHomingProjectile(projectile, &target, Step));
        projectile.x += projectile.velocityX * Step;
        projectile.y += projectile.velocityY * Step;
        projectile.z += projectile.velocityZ * Step;
    }

    CHECK(headingDegreesBetween(projectile.velocityX, projectile.velocityY, projectile.velocityZ,
        target.x - projectile.x, target.y - projectile.y, target.z - projectile.z) < 3.0f);
    CHECK(std::hypot(projectile.velocityX, projectile.velocityY) == doctest::Approx(1500.0f));

    // After max_seconds it keeps its heading.
    for (int step = 0; step < 40; ++step)
    {
        GameplayProjectileService::steerHomingProjectile(projectile, &target, Step);
    }

    REQUIRE(projectile.homing->lost);
    const float headingX = projectile.velocityX;
    const float headingY = projectile.velocityY;
    target = {-5000.0f, -5000.0f, 0.0f};
    CHECK_FALSE(GameplayProjectileService::steerHomingProjectile(projectile, &target, Step));
    CHECK(projectile.velocityX == headingX);
    CHECK(projectile.velocityY == headingY);

    // With `then: expire` the end of its time expires it; a lost target makes it fly straight.
    ProjectileState expiring = {};
    expiring.velocityX = 1000.0f;
    homing.expireAfter = true;
    homing.maxSeconds = 0.05f;
    homing.speed = 1000.0f;
    expiring.homing = homing;
    bool expired = false;

    for (int step = 0; step < 10 && !expired; ++step)
    {
        expired = GameplayProjectileService::steerHomingProjectile(expiring, &target, Step);
    }

    CHECK(expired);

    ProjectileState orphan = {};
    orphan.velocityX = 1000.0f;
    homing.expireAfter = false;
    homing.maxSeconds = 0.0f;
    orphan.homing = homing;
    CHECK_FALSE(GameplayProjectileService::steerHomingProjectile(orphan, nullptr, Step));
    CHECK(orphan.homing->lost);
    CHECK(orphan.velocityX == 1000.0f);
}

TEST_CASE("true aim is given only to the firing actor's new projectiles")
{
    GameplayProjectileService service;
    GameplayProjectileService::ProjectileSpawnRequest request = {};
    request.sourceKind = GameplayProjectileService::ProjectileState::SourceKind::Actor;
    request.sourceId = 7;
    request.definition.speed = 1200.0f;
    request.definition.lifetimeTicks = 512;
    request.targetX = 1000.0f;
    service.spawnProjectile(request);
    const uint32_t firstNew = service.nextProjectileId();
    service.spawnProjectile(request);
    request.sourceId = 8;
    service.spawnProjectile(request);
    request.sourceKind = GameplayProjectileService::ProjectileState::SourceKind::Party;
    request.sourceId = 7;
    service.spawnProjectile(request);

    MonsterModifierSet modifiers = {};
    modifiers.trueAim = TrueAimModifier{};
    const std::optional<GameplayProjectileService::ProjectileHoming> homing = trueAimProjectileHoming(
        &modifiers, GameplayProjectileService::ProjectileHoming::TargetKind::Party, static_cast<size_t>(-1), 0);
    REQUIRE(homing);
    CHECK(service.attachHoming(firstNew, 7, *homing) == 1);
    REQUIRE(service.projectiles().size() == 4);
    CHECK_FALSE(service.projectiles()[0].homing);
    REQUIRE(service.projectiles()[1].homing);
    CHECK(service.projectiles()[1].homing->speed == doctest::Approx(1200.0f));
    CHECK_FALSE(service.projectiles()[2].homing);
    CHECK_FALSE(service.projectiles()[3].homing);

    CHECK_FALSE(trueAimProjectileHoming(nullptr, GameplayProjectileService::ProjectileHoming::TargetKind::Party,
        static_cast<size_t>(-1), 0));
    CHECK_FALSE(trueAimProjectileHoming(&modifiers, GameplayProjectileService::ProjectileHoming::TargetKind::Actor,
        static_cast<size_t>(-1), 0));
}

TEST_CASE("blink triggers on hits, shield breaks and while fighting, within its cooldown")
{
    MonsterModifierTable table;
    MonsterModifierSet always = {};
    always.monsterId = 10040;
    always.blink = BlinkModifier{};
    always.blink->onHitChance = 1.0f;
    always.blink->cooldownSeconds = 5.0f;
    table.set(always);
    MonsterModifierSet breaker = {};
    breaker.monsterId = 10041;
    breaker.blink = BlinkModifier{};
    breaker.blink->onShieldBreak = true;
    table.set(breaker);
    MonsterModifierSet periodic = {};
    periodic.monsterId = 10042;
    periodic.blink = BlinkModifier{};
    periodic.blink->everySeconds = 2.0f;
    periodic.blink->cooldownSeconds = 0.0f;
    table.set(periodic);

    GameplayActorModifiers modifiers;
    modifiers.bind(&table);
    REQUIRE(modifiers.active());
    const std::array<int16_t, 4> monsters = {10040, 10041, 10042, 307};
    const auto facts = [&](size_t actorIndex)
    {
        return GameplayActorModifiers::ActorFacts{
            .monsterId = monsters[actorIndex], .actorId = uint32_t(actorIndex + 100), .canAct = true,
            .position = {float(actorIndex) * 1000.0f, 0.0f, 0.0f}};
    };

    // Nothing asked: no blinks; an MM monster is never tracked.
    modifiers.observeHit(3, 307, 103, {0.0f, 0.0f, 0.0f}, true, false);
    CHECK(modifiers.update(0.1f, 4, facts).empty());

    modifiers.observeHit(0, 10040, 100, {0.0f, -500.0f, 0.0f}, true, false);
    modifiers.observeHit(1, 10041, 101, {0.0f, -500.0f, 0.0f}, true, false);
    std::vector<GameplayActorModifiers::BlinkRequest> requests = modifiers.update(0.1f, 4, facts);
    REQUIRE(requests.size() == 1);
    CHECK(requests[0].actorIndex == 0);
    REQUIRE(requests[0].threat);
    modifiers.finishBlink(requests[0], true);
    CHECK(modifiers.blinkCount() == 1);

    // Within the cooldown a new hit asks again but waits; the shield-break blinker answers its break.
    modifiers.observeHit(0, 10040, 100, {0.0f, -500.0f, 0.0f}, true, false);
    modifiers.observeHit(1, 10041, 101, {0.0f, -500.0f, 0.0f}, false, true);
    requests = modifiers.update(0.1f, 4, facts);
    REQUIRE(requests.size() == 1);
    CHECK(requests[0].actorIndex == 1);
    modifiers.finishBlink(requests[0], true);

    // A periodic blinker blinks every 2 s while it fights, and stops once the fight is 5 s old.
    modifiers.observeAttack(2, 10042, 102, {0.0f, 0.0f, 0.0f});
    int periodicBlinks = 0;

    for (int step = 0; step < 100; ++step)
    {
        for (const GameplayActorModifiers::BlinkRequest &request : modifiers.update(0.1f, 4, facts))
        {
            periodicBlinks += request.actorIndex == 2 ? 1 : 0;
            modifiers.finishBlink(request, true);
        }
    }

    CHECK(periodicBlinks == 2);
}

TEST_CASE("blink candidates lie within the jump range and turn away from the threat first")
{
    BlinkModifier blink = {};
    blink.minDistance = 400.0f;
    blink.maxDistance = 900.0f;
    GameplayActorModifiers::BlinkRequest request = {};
    request.pBlink = &blink;
    request.origin = {1000.0f, 2000.0f, 64.0f};
    request.threat = std::array<float, 3>{1000.0f, 0.0f, 64.0f};
    request.seed = 1234;
    const std::vector<std::array<float, 3>> candidates = GameplayActorModifiers::blinkCandidates(request, 16);
    REQUIRE(candidates.size() == 16);
    float firstHalfAway = 0.0f;
    float secondHalfAway = 0.0f;

    for (size_t index = 0; index < candidates.size(); ++index)
    {
        const float dx = candidates[index][0] - request.origin[0];
        const float dy = candidates[index][1] - request.origin[1];
        const float distance = std::hypot(dx, dy);
        CHECK(distance >= 399.0f);
        CHECK(distance <= 901.0f);
        CHECK(candidates[index][2] == 64.0f);
        (index < 8 ? firstHalfAway : secondHalfAway) += dy / distance;
    }

    CHECK(firstHalfAway > secondHalfAway);
    CHECK(GameplayActorModifiers::blinkCandidates(request, 16) == candidates);
}

TEST_CASE("skirmisher parses with its defaults and becomes the tactics footwork")
{
    MonsterModifierTable table;
    std::string error;
    REQUIRE_MESSAGE(table.loadWorldYaml("schema: openyamm.monsterModifiers.v1\nmonsters:\n"
        "  9111: [skirmisher]\n"
        "  9237: [{skirmisher: {strafe_attack_chance: 0.95, evade_chance: 0.25, taunt_seconds: 0.9}}]\n", "mm9",
        9000, 9999, error),
        error);
    REQUIRE(table.find(9111)->skirmisher);
    CHECK(table.find(9111)->skirmisher->strafeAttackChance == doctest::Approx(0.8f));
    CHECK(table.find(9111)->skirmisher->evadeChance == doctest::Approx(0.4f));
    CHECK(table.find(9237)->skirmisher->strafeAttackChance == doctest::Approx(0.95f));
    CHECK(table.find(9111)->skirmisher->tauntSeconds == 0.0f);
    CHECK(table.find(9237)->skirmisher->tauntChance == doctest::Approx(0.4f));

    ActorBehaviorCatalog catalog;
    REQUIRE(catalog.applyMonsterModifiers(table, error));
    const ActorTacticsFacts *pTactics = catalog.tacticsForMonster(9237);
    REQUIRE(pTactics != nullptr);
    CHECK(pTactics->skirmish);
    CHECK(pTactics->evadeChance == doctest::Approx(0.25f));
    CHECK(pTactics->evadeSeconds == doctest::Approx(2.0f));
    CHECK(pTactics->tauntSeconds == doctest::Approx(0.9f));
    CHECK_FALSE(pTactics->keepsRangedBand());
}

TEST_CASE("reposition parses with its defaults and errors and becomes tactics")
{
    MonsterModifierTable table;
    std::string error;
    REQUIRE_MESSAGE(table.loadWorldYaml("schema: openyamm.monsterModifiers.v1\nmonsters:\n"
        "  9157: [reposition]\n"
        "  9158: [{reposition: {leash_radius: 512, candidates: 4, back_off_distance: 256}}]\n", "mm9", 9000, 9999,
        error),
        error);
    REQUIRE(table.find(9157)->reposition);
    const RepositionModifier &defaults = *table.find(9157)->reposition;
    CHECK(defaults.lostSightSeconds == doctest::Approx(2.0f));
    CHECK(defaults.leashRadius == doctest::Approx(1024.0f));
    CHECK(defaults.searchDistance == doctest::Approx(640.0f));
    CHECK(defaults.candidates == 8);
    CHECK(defaults.maxSightChecks == 12);
    CHECK(defaults.retrySeconds == doctest::Approx(2.0f));
    CHECK(defaults.backOffTriggerDistance == doctest::Approx(640.0f));
    CHECK(defaults.backOffClosingSpeed == doctest::Approx(200.0f));
    CHECK(defaults.backOffDistance == doctest::Approx(384.0f));
    CHECK(defaults.backOffCooldownSeconds == doctest::Approx(5.0f));
    CHECK(table.find(9158)->reposition->leashRadius == doctest::Approx(512.0f));
    CHECK(table.find(9158)->reposition->candidates == 4);
    CHECK(table.find(9158)->reposition->backOffDistance == doctest::Approx(256.0f));

    const auto mm9Error = [](const std::string &body)
    {
        MonsterModifierTable errors;
        std::string message;
        CHECK_FALSE(errors.loadWorldYaml("schema: openyamm.monsterModifiers.v1\nmonsters:\n" + body, "mm9", 9000,
            9999, message));
        return message;
    };
    CHECK(mm9Error("  9157: [{reposition: {candidates: 2.5}}]\n").find("whole numbers") != std::string::npos);
    CHECK(mm9Error("  9157: [{reposition: {candidates: 17}}]\n").find("must be a number in") != std::string::npos);
    CHECK(mm9Error("  9157: [{reposition: {leash: 5}}]\n").find("no parameter") != std::string::npos);

    // Tactics of its own (a monster without the modifier has none).
    ActorBehaviorCatalog catalog;
    REQUIRE(catalog.applyMonsterModifiers(table, error));
    const ActorTacticsFacts *pTactics = catalog.tacticsForMonster(9158);
    REQUIRE(pTactics != nullptr);
    REQUIRE(pTactics->reposition);
    CHECK(pTactics->reposition->leashRadius == doctest::Approx(512.0f));
    CHECK_FALSE(pTactics->skirmish);
    CHECK(catalog.tacticsForMonster(9156) == nullptr);
}

TEST_CASE("spell_conditions parse with their defaults and errors")
{
    MonsterModifierTable table;
    std::string error;
    REQUIRE_MESSAGE(table.loadWorldYaml("schema: openyamm.monsterModifiers.v1\nmonsters:\n"
        "  9209: [{spell_conditions: {spell1: weak, spell2: cursed}}]\n"
        "  9162: [{spell_conditions: {spell1: afraid, chance: 0.5}}]\n", "mm9", 9000, 9999, error),
        error);
    REQUIRE(table.find(9209)->spellConditions);
    CHECK(table.find(9209)->spellConditions->spell1 == MonsterSpecialAttackKind::Weak);
    CHECK(table.find(9209)->spellConditions->spell2 == MonsterSpecialAttackKind::Curse);
    CHECK(table.find(9209)->spellConditions->chance == doctest::Approx(1.0f));
    CHECK(table.find(9162)->spellConditions->spell1 == MonsterSpecialAttackKind::Fear);
    CHECK(table.find(9162)->spellConditions->spell2 == MonsterSpecialAttackKind::None);
    CHECK(table.find(9162)->spellConditions->chance == doctest::Approx(0.5f));

    const auto mm9Error = [](const std::string &body)
    {
        MonsterModifierTable errors;
        std::string message;
        CHECK_FALSE(errors.loadWorldYaml("schema: openyamm.monsterModifiers.v1\nmonsters:\n" + body, "mm9", 9000,
            9999, message));
        return message;
    };
    CHECK(mm9Error("  9162: [spell_conditions]\n").find("needs a condition") != std::string::npos);
    CHECK(mm9Error("  9162: [{spell_conditions: {spell1: frozen}}]\n").find("must be one of") != std::string::npos);
    CHECK(mm9Error("  9116: [special_attack_chance]\n").find("unknown") != std::string::npos);

    // A monster's combat info: the modifiers, a slot a ruleset replaced, a monster without them.
    GameplayCombatActorInfo info;
    applyHitConditionModifiers(table.find(9209), false, true, info);
    CHECK(info.spell1Condition == MonsterSpecialAttackKind::Weak);
    CHECK(info.spell2Condition == MonsterSpecialAttackKind::None);
    GameplayCombatActorInfo plain;
    applyHitConditionModifiers(nullptr, false, false, plain);
    CHECK(plain.spell1Condition == MonsterSpecialAttackKind::None);
}

TEST_CASE("Paralyze and Fear are castable monster spells only with a condition for their slot")
{
    MonsterModifierTable table;
    std::string error;
    REQUIRE_MESSAGE(table.loadWorldYaml("schema: openyamm.monsterModifiers.v1\nmonsters:\n"
        "  9230: [{spell_conditions: {spell1: paralyzed}}]\n", "mm9", 9000, 9999, error),
        error);
    const MonsterModifierSet *pOculus = table.find(9230);
    CHECK(monsterConditionSpellCastSupported("paralyze", pOculus, 1));
    CHECK_FALSE(monsterConditionSpellCastSupported("paralyze", pOculus, 2));
    CHECK_FALSE(monsterConditionSpellCastSupported("paralyze", nullptr, 1));
    CHECK_FALSE(monsterConditionSpellCastSupported("dark grasp", pOculus, 1));
    CHECK(isKnownUnsupportedMonsterSpellName("Paralyze"));
    CHECK(isKnownUnsupportedMonsterSpellName("Fear"));
    CHECK_FALSE(isMonsterProjectileSpellName("paralyze"));

    // The cast carries only the condition: no damage.
    GameplayProjectileService service;
    GameplayProjectileService::ProjectilePartyImpactDamageInput input;
    input.sourceKind = GameplayProjectileService::ProjectileState::SourceKind::Actor;
    input.hasMonsterFacts = true;
    input.monsterAbility = GameplayProjectileService::MonsterAttackAbility::Spell1;
    input.spellId = int(spellIdValue(SpellId::Paralyze));
    input.spell1Damage.skillLevel = 10;
    input.spell1Damage.skillMastery = SkillMastery::Expert;
    CHECK(service.resolveProjectilePartyImpactDamage(input) == 0);
    input.spellId = int(spellIdValue(SpellId::DarkGrasp));
    CHECK(service.resolveProjectilePartyImpactDamage(input) >= 1);
}

TEST_CASE("a monster's Sparks fires a volley by mastery over a 60 degree fan")
{
    const uint32_t sparks = spellIdValue(SpellId::Sparks);
    CHECK(monsterSpellProjectileCount(sparks, SkillMastery::None) == 3);
    CHECK(monsterSpellProjectileCount(sparks, SkillMastery::Normal) == 3);
    CHECK(monsterSpellProjectileCount(sparks, SkillMastery::Expert) == 5);
    CHECK(monsterSpellProjectileCount(sparks, SkillMastery::Master) == 7);
    CHECK(monsterSpellProjectileCount(sparks, SkillMastery::Grandmaster) == 9);
    CHECK(monsterSpellProjectileCount(spellIdValue(SpellId::FireBolt), SkillMastery::Grandmaster) == 1);
    CHECK(monsterSpellProjectileCount(spellIdValue(SpellId::PoisonSpray), SkillMastery::Grandmaster) == 1);

    // A single shot flies at the target; a volley spreads evenly from -30 to +30 degrees off the line to it.
    const std::array<float, 3> source = {0.0f, 0.0f, 50.0f};
    const std::array<float, 3> target = {1000.0f, 0.0f, 80.0f};
    CHECK(monsterSpellVolleyTarget(source, target, 1, 0) == target);
    const auto bearing = [&](uint32_t index)
    {
        const std::array<float, 3> shot = monsterSpellVolleyTarget(source, target, 5, index);
        CHECK(shot[2] == doctest::Approx(80.0f));
        CHECK(std::hypot(shot[0], shot[1]) == doctest::Approx(1000.0f));
        return std::atan2(shot[1], shot[0]) * 180.0f / Pi;
    };
    CHECK(bearing(0) == doctest::Approx(-30.0f));
    CHECK(bearing(1) == doctest::Approx(-15.0f));
    CHECK(std::abs(bearing(2)) < 0.01f);
    CHECK(bearing(4) == doctest::Approx(30.0f));
}

TEST_CASE("kites_party becomes the tactics ranged band and conflicts with one set there")
{
    MonsterModifierTable table;
    MonsterModifierSet kiter = {};
    kiter.monsterId = 10102;
    kiter.kitesParty = KitesPartyModifier{1024.0f, 3072.0f};
    table.set(kiter);

    ActorBehaviorCatalog catalog;
    std::string error;
    REQUIRE(catalog.applyMonsterModifiers(table, error));
    const ActorTacticsFacts *pTactics = catalog.tacticsForMonster(10102);
    REQUIRE(pTactics != nullptr);
    CHECK(pTactics->rangedMinDistance == doctest::Approx(1024.0f));
    CHECK(pTactics->rangedMaxDistance == doctest::Approx(3072.0f));
    CHECK(pTactics->traverseRadiansPerSecond == 0.0f);

    ActorBehaviorCatalog conflicting;
    ActorTacticsFacts band = {};
    band.rangedMinDistance = 768.0f;
    band.rangedMaxDistance = 2304.0f;
    conflicting.setMonsterTactics(10102, band);
    CHECK_FALSE(conflicting.applyMonsterModifiers(table, error));
    CHECK(error.find("kites_party") != std::string::npos);
}

namespace
{
// A straight corridor along +x for a charge: the party at partyX, a wall at wallX (0: none).
struct ChargeTestWorld
{
    float actorX = 0.0f;
    float actorY = 0.0f;
    float partyX = 1000.0f;
    float wallX = 0.0f;
    // A post's leash around x = 0 (0: none).
    float leashRadius = 0.0f;
    bool sight = true;
    std::vector<GameplayActorModifiers::ChargeEventKind> events;

    GameplayActorModifiers::ChargeWorld world()
    {
        GameplayActorModifiers::ChargeWorld chargeWorld = {};
        chargeWorld.hasLineOfSightToParty = [this](size_t) { return sight; };
        chargeWorld.step = [this](size_t, float x, float y, float, float)
        {
            if (std::abs(x - partyX) < 40.0f + 37.0f + 16.0f)
            {
                return GameplayActorModifiers::ChargeStepResult::Contact;
            }
            if (wallX != 0.0f && x + 40.0f > wallX)
            {
                return GameplayActorModifiers::ChargeStepResult::Blocked;
            }
            actorX = x;
            actorY = y;
            return GameplayActorModifiers::ChargeStepResult::Moved;
        };
        chargeWorld.handle = [this](const GameplayActorModifiers::ChargeEvent &event) { events.push_back(event.kind); };
        return chargeWorld;
    }

    GameplayActorModifiers::ChargeActorFacts facts(bool canAct = true) const
    {
        GameplayActorModifiers::ChargeActorFacts actorFacts = {};
        actorFacts.monsterId = 10082;
        actorFacts.actorId = 7;
        actorFacts.canAct = canAct;
        actorFacts.engagesParty = true;
        actorFacts.position = {actorX, actorY, 0.0f};
        actorFacts.partyPosition = {partyX, 0.0f, 0.0f};
        actorFacts.partyEdgeDistance = std::max(0.0f, std::abs(partyX - actorX) - 40.0f - 37.0f);
        actorFacts.leashRadius = leashRadius;
        return actorFacts;
    }
};

MonsterModifierTable chargeTable(const std::string &parameters)
{
    MonsterModifierTable table;
    std::string error;
    REQUIRE_MESSAGE(loadModifiers(table, "  10082: [{charge: {" + parameters + "}}]\n", error), error);
    return table;
}

void stepCharge(GameplayActorModifiers &modifiers, ChargeTestWorld &test, float seconds, bool canAct = true)
{
    const GameplayActorModifiers::ChargeWorld world = test.world();
    for (float elapsed = 0.0f; elapsed < seconds - 0.0001f; elapsed += 1.0f / 30.0f)
    {
        modifiers.updateCharges(1.0f / 30.0f, 1, [&](size_t) { return test.facts(canAct); }, world);
    }
}
}

TEST_CASE("charge modifier loads its parameters, defaults and errors")
{
    const MonsterModifierTable defaults = chargeTable("");
    REQUIRE(defaults.find(10082)->charge);
    const ChargeModifier &charge = *defaults.find(10082)->charge;
    CHECK(defaults.hasCharge());
    CHECK_FALSE(defaults.hasBlink());
    CHECK(charge.triggerMinDistance == doctest::Approx(384.0f));
    CHECK(charge.triggerMaxDistance == doctest::Approx(1280.0f));
    CHECK(charge.windupSeconds == doctest::Approx(0.6f));
    CHECK(charge.speed == doctest::Approx(1400.0f));
    CHECK(charge.maxDistance == doctest::Approx(1536.0f));
    CHECK(charge.useMelee);
    CHECK(charge.knockback == doctest::Approx(256.0f));
    CHECK(charge.cooldownSeconds == doctest::Approx(8.0f));
    CHECK(charge.stumbleSeconds == doctest::Approx(1.2f));
    CHECK(charge.windupSound == "monster_charge_windup");
    CHECK(charge.hitSound == "monster_charge_hit");

    // A damage given without use_melee replaces the melee attack.
    const MonsterModifierTable fixed = chargeTable("damage: 30, speed: 2000, windup_seconds: 0.4");
    CHECK_FALSE(fixed.find(10082)->charge->useMelee);
    CHECK(fixed.find(10082)->charge->damage == doctest::Approx(30.0f));
    CHECK(fixed.find(10082)->charge->speed == doctest::Approx(2000.0f));

    CHECK(modifierError("  10082: [{charge: {trigger_min_distance: 900, trigger_max_distance: 800}}]\n")
        .find("trigger_min_distance must be below trigger_max_distance") != std::string::npos);
    CHECK(modifierError("  10082: [{charge: {use_melee: true, damage: 10}}]\n").find("melee attack")
        != std::string::npos);
    CHECK(modifierError("  10082: [{charge: {use_melee: false}}]\n").find("fixed damage") != std::string::npos);
    CHECK(modifierError("  10082: [{charge: {speed: 50}}]\n").find("charge.speed must be a number in 100-8000")
        != std::string::npos);
    CHECK(modifierError("  10082: [{charge: {sped: 900}}]\n").find("charge has no parameter 'sped'")
        != std::string::npos);
}

TEST_CASE("charge winds up, dashes onto the party, hits and cools down")
{
    const MonsterModifierTable table = chargeTable("windup_seconds: 0.5, speed: 1500, cooldown_seconds: 4");
    GameplayActorModifiers modifiers;
    modifiers.bind(&table);
    ChargeTestWorld test;
    test.partyX = 900.0f;

    // In the band and in sight: the wind-up starts and holds the actor in place.
    stepCharge(modifiers, test, 1.0f / 30.0f);
    CHECK(modifiers.chargePhase(0) == GameplayActorModifiers::ChargePhase::Windup);
    CHECK(modifiers.chargeCount() == 1);
    REQUIRE(test.events.size() == 1);
    CHECK(test.events[0] == GameplayActorModifiers::ChargeEventKind::WindupStarted);
    stepCharge(modifiers, test, 0.4f);
    CHECK(modifiers.chargePhase(0) == GameplayActorModifiers::ChargePhase::Windup);
    CHECK(test.actorX == doctest::Approx(0.0f));

    ActorAiFrameFacts frame = {};
    ActorAiFacts actorFacts = {};
    actorFacts.actorIndex = 0;
    actorFacts.actorId = 7;
    frame.activeActors.push_back(actorFacts);
    modifiers.applyChargeHolds(frame);
    CHECK(frame.activeActors[0].behavior.holdActive);

    // The dash covers 1500 units a second and stops at the party with the hit.
    stepCharge(modifiers, test, 0.2f);
    CHECK(modifiers.chargePhase(0) == GameplayActorModifiers::ChargePhase::Dash);
    CHECK(test.actorX > 50.0f);
    stepCharge(modifiers, test, 0.6f);
    CHECK(modifiers.chargeHitCount() == 1);
    CHECK(modifiers.chargeMissCount() == 0);
    CHECK(std::find(test.events.begin(), test.events.end(), GameplayActorModifiers::ChargeEventKind::Hit)
        != test.events.end());
    CHECK(test.actorX < test.partyX - 40.0f);

    // Recovery, then the cooldown: no second charge before it ends, one after.
    stepCharge(modifiers, test, 1.0f);
    CHECK(modifiers.chargePhase(0) == GameplayActorModifiers::ChargePhase::Ready);
    test.partyX = test.actorX + 800.0f;
    stepCharge(modifiers, test, 3.0f);
    CHECK(modifiers.chargeCount() == 1);
    stepCharge(modifiers, test, 1.0f);
    CHECK(modifiers.chargeCount() == 2);
}

TEST_CASE("charge stops at a wall, at its longest dash and outside its band")
{
    const MonsterModifierTable table = chargeTable("windup_seconds: 0.2, max_distance: 500, stumble_seconds: 1");
    {
        GameplayActorModifiers modifiers;
        modifiers.bind(&table);
        ChargeTestWorld test;
        test.wallX = 300.0f;
        stepCharge(modifiers, test, 1.0f);
        CHECK(modifiers.chargeMissCount() == 1);
        CHECK(modifiers.chargePhase(0) == GameplayActorModifiers::ChargePhase::Recover);
        CHECK(test.actorX <= 260.0f + 0.01f);

        ActorAiFrameFacts frame = {};
        ActorAiFacts actorFacts = {};
        actorFacts.actorId = 7;
        actorFacts.actorIndex = 0;
        frame.activeActors.push_back(actorFacts);
        modifiers.applyChargeHolds(frame);
        CHECK(frame.activeActors[0].behavior.holdAnimation == ActorAiAnimationState::GotHit);
    }
    {
        GameplayActorModifiers modifiers;
        modifiers.bind(&table);
        ChargeTestWorld test;
        test.partyX = 1200.0f;
        stepCharge(modifiers, test, 1.5f);
        CHECK(modifiers.chargeMissCount() == 1);
        CHECK(test.actorX == doctest::Approx(500.0f).epsilon(0.01));
    }
    {
        // Too close, too far, out of sight, or not fighting the party: no charge.
        GameplayActorModifiers modifiers;
        modifiers.bind(&table);
        ChargeTestWorld test;
        test.partyX = 200.0f;
        stepCharge(modifiers, test, 0.5f);
        test.partyX = 3000.0f;
        stepCharge(modifiers, test, 0.5f);
        test.partyX = 900.0f;
        test.sight = false;
        stepCharge(modifiers, test, 0.5f);
        CHECK(modifiers.chargeCount() == 0);
    }
    {
        // A stun mid-dash ends it in place.
        GameplayActorModifiers modifiers;
        modifiers.bind(&table);
        ChargeTestWorld test;
        test.partyX = 1200.0f;
        stepCharge(modifiers, test, 0.3f);
        stepCharge(modifiers, test, 1.0f / 30.0f, false);
        CHECK(modifiers.chargePhase(0) == GameplayActorModifiers::ChargePhase::Ready);
        CHECK(modifiers.chargeHitCount() + modifiers.chargeMissCount() == 0);
    }
}

TEST_CASE("a posted charger's dash stops at its leash, and it never charges a party beyond it")
{
    const MonsterModifierTable table = chargeTable("windup_seconds: 0.2, max_distance: 1500, stumble_seconds: 1");
    {
        GameplayActorModifiers modifiers;
        modifiers.bind(&table);
        ChargeTestWorld test;
        test.leashRadius = 600.0f;
        test.partyX = 500.0f;
        // The party steps away during the wind-up: the dash runs on and stops at the leash like at a wall.
        stepCharge(modifiers, test, 1.0f / 30.0f);
        CHECK(modifiers.chargePhase(0) == GameplayActorModifiers::ChargePhase::Windup);
        test.partyX = 2000.0f;
        stepCharge(modifiers, test, 1.5f);
        CHECK(modifiers.chargeCount() == 1);
        CHECK(modifiers.chargeHitCount() == 0);
        CHECK(modifiers.chargeMissCount() == 1);
        CHECK(test.actorX <= 600.0f + 0.01f);
        CHECK(test.actorX > 560.0f);
    }
    {
        GameplayActorModifiers modifiers;
        modifiers.bind(&table);
        ChargeTestWorld test;
        test.leashRadius = 600.0f;
        test.partyX = 900.0f;
        stepCharge(modifiers, test, 1.0f);
        CHECK(modifiers.chargeCount() == 0);
    }
}

TEST_CASE("a charge with strike_seconds plays its strike clip from the impact after a hit")
{
    const MonsterModifierTable table =
        chargeTable("windup_seconds: 0.2, speed: 1500, strike_seconds: 0.6, strike_impact_seconds: 0.25");
    CHECK(table.find(10082)->charge->strikeSeconds == doctest::Approx(0.6f));
    CHECK(table.find(10082)->charge->strikeImpactSeconds == doctest::Approx(0.25f));
    GameplayActorModifiers modifiers;
    modifiers.bind(&table);
    ChargeTestWorld test;
    test.partyX = 900.0f;
    float clipSeconds = 0.0f;

    for (int frame = 0; frame < 60 && modifiers.chargeHitCount() == 0; ++frame)
    {
        stepCharge(modifiers, test, 1.0f / 30.0f);
        CHECK((modifiers.chargeHitCount() > 0) == modifiers.chargeStrikeClip(0, 7, clipSeconds));
    }

    REQUIRE(modifiers.chargeHitCount() == 1);
    REQUIRE(modifiers.chargeStrikeClip(0, 7, clipSeconds));
    CHECK(clipSeconds == doctest::Approx(0.25f));
    CHECK_FALSE(modifiers.chargeStrikeClip(0, 8, clipSeconds));
    stepCharge(modifiers, test, 0.3f);
    REQUIRE(modifiers.chargeStrikeClip(0, 7, clipSeconds));
    CHECK(clipSeconds == doctest::Approx(0.55f).epsilon(0.02));
    CHECK(modifiers.chargePhase(0) == GameplayActorModifiers::ChargePhase::Recover);
    stepCharge(modifiers, test, 0.35f);
    CHECK_FALSE(modifiers.chargeStrikeClip(0, 7, clipSeconds));
    CHECK(modifiers.chargePhase(0) == GameplayActorModifiers::ChargePhase::Ready);
}

namespace
{
// One actor with a frenzy (and optionally a charge) at x = 0, the party at x = 900 in sight.
struct FrenzyTestActor
{
    float healthShare = 1.0f;
    bool canAct = true;
    bool alive = true;
    bool engagesParty = true;
    uint32_t roars = 0;

    GameplayActorModifiers::ChargeActorFacts facts() const
    {
        GameplayActorModifiers::ChargeActorFacts actorFacts = {};
        actorFacts.monsterId = 10082;
        actorFacts.actorId = 7;
        actorFacts.canAct = canAct;
        actorFacts.alive = alive;
        actorFacts.healthShare = healthShare;
        actorFacts.engagesParty = engagesParty;
        actorFacts.hostileToParty = true;
        actorFacts.partyPosition = {900.0f, 0.0f, 0.0f};
        actorFacts.partyEdgeDistance = 900.0f - 77.0f;
        return actorFacts;
    }

    GameplayActorModifiers::ChargeWorld world()
    {
        GameplayActorModifiers::ChargeWorld chargeWorld = {};
        chargeWorld.hasLineOfSightToParty = [](size_t) { return true; };
        chargeWorld.step = [](size_t, float, float, float, float)
        {
            return GameplayActorModifiers::ChargeStepResult::Moved;
        };
        chargeWorld.frenzyRoared = [this](size_t, const FrenzyModifier &) { ++roars; };
        return chargeWorld;
    }
};

MonsterModifierTable frenzyTable(const std::string &modifiers)
{
    MonsterModifierTable table;
    std::string error;
    REQUIRE_MESSAGE(loadModifiers(table, "  10082: [" + modifiers + "]\n", error), error);
    return table;
}

void stepFrenzy(GameplayActorModifiers &modifiers, FrenzyTestActor &actor, float seconds)
{
    const GameplayActorModifiers::ChargeWorld world = actor.world();
    for (float elapsed = 0.0f; elapsed < seconds - 0.0001f; elapsed += 1.0f / 30.0f)
    {
        const auto facts = [&](size_t) { return actor.facts(); };
        modifiers.updateFrenzies(1.0f / 30.0f, 1, facts, world);
        modifiers.updateCharges(1.0f / 30.0f, 1, facts, world);
    }
}

ActorAiFacts frenzyAiFacts(const GameplayActorModifiers &modifiers)
{
    ActorAiFrameFacts frame = {};
    ActorAiFacts actorFacts = {};
    actorFacts.actorIndex = 0;
    actorFacts.actorId = 7;
    actorFacts.movement.effectiveMoveSpeed = 200.0f;
    frame.activeActors.push_back(actorFacts);
    modifiers.applyFrenzies(frame);
    return frame.activeActors[0];
}
}

TEST_CASE("frenzy modifier loads its parameters, defaults and errors")
{
    const MonsterModifierTable table = frenzyTable("{frenzy: {health_below: 0.5}}");
    REQUIRE(table.find(10082)->frenzy);
    const FrenzyModifier &frenzy = *table.find(10082)->frenzy;
    CHECK(table.hasFrenzy());
    CHECK_FALSE(table.hasCharge());
    CHECK(frenzy.healthBelow == doctest::Approx(0.5f));
    CHECK(frenzy.everySeconds == 0.0f);
    CHECK_FALSE(frenzy.onShieldBreak);
    CHECK(frenzy.windupSeconds == doctest::Approx(0.8f));
    CHECK(frenzy.seconds == doctest::Approx(6.0f));
    CHECK(frenzy.speedMultiplier == doctest::Approx(1.4f));
    CHECK(frenzy.attackRateMultiplier == doctest::Approx(1.5f));
    CHECK(frenzy.spentSeconds == 0.0f);
    CHECK(frenzy.cooldownSeconds == doctest::Approx(20.0f));
    CHECK(frenzy.glowMultiplier == doctest::Approx(2.0f));
    CHECK(frenzy.sound == "monster_frenzy");
    CHECK(frenzy.fallbackSound == "roar 1");

    CHECK(modifierError("  10082: [{frenzy: {seconds: 4}}]\n").find("frenzy needs a trigger") != std::string::npos);
    CHECK(modifierError("  10082: [{frenzy: {health_below: 0.99}}]\n").find("health_below must be a number")
        != std::string::npos);
    CHECK(modifierError("  10082: [{frenzy: {every_seconds: 5, speed_multiplier: 4}}]\n")
        .find("speed_multiplier must be a number") != std::string::npos);
}

TEST_CASE("frenzy roars below its health share once, then speeds the actor up and holds it spent")
{
    const MonsterModifierTable table = frenzyTable("{frenzy: {health_below: 0.5, windup_seconds: 0.5, seconds: 2, "
        "speed_multiplier: 1.5, attack_rate_multiplier: 2, spent_seconds: 1, glow_multiplier: 3, "
        "cooldown_seconds: 0}}");
    GameplayActorModifiers modifiers;
    modifiers.bind(&table);
    FrenzyTestActor actor;

    stepFrenzy(modifiers, actor, 1.0f);
    CHECK(modifiers.frenzyCount() == 0);
    CHECK(frenzyAiFacts(modifiers).movement.effectiveMoveSpeed == doctest::Approx(200.0f));

    // Below half health: the roar holds it and plays the frenzy clip.
    actor.healthShare = 0.4f;
    stepFrenzy(modifiers, actor, 1.0f / 30.0f);
    CHECK(modifiers.frenzyCount() == 1);
    CHECK(actor.roars == 1);
    CHECK(modifiers.frenzyPhase(0) == GameplayActorModifiers::FrenzyPhase::Roar);
    CHECK(frenzyAiFacts(modifiers).behavior.holdActive);
    const char *pRole = nullptr;
    float clipSeconds = -1.0f;
    REQUIRE(modifiers.scriptedClip(0, 7, pRole, clipSeconds));
    CHECK(std::string(pRole) == "frenzy");
    CHECK(clipSeconds == doctest::Approx(1.0f / 30.0f).epsilon(0.05));
    CHECK(modifiers.emissionMultiplier(0, 7) == doctest::Approx(1.0f));

    // The frenzy: faster moves and recovery, the glow.
    stepFrenzy(modifiers, actor, 0.6f);
    CHECK(modifiers.frenzyPhase(0) == GameplayActorModifiers::FrenzyPhase::Active);
    const ActorAiFacts frenzied = frenzyAiFacts(modifiers);
    CHECK_FALSE(frenzied.behavior.holdActive);
    CHECK(frenzied.movement.effectiveMoveSpeed == doctest::Approx(300.0f));
    CHECK(frenzied.behavior.attackRateMultiplier == doctest::Approx(2.0f));
    CHECK(modifiers.emissionMultiplier(0, 7) == doctest::Approx(3.0f));
    CHECK(modifiers.emissionMultiplier(0, 8) == doctest::Approx(1.0f));
    CHECK_FALSE(modifiers.scriptedClip(0, 7, pRole, clipSeconds));

    // Spent, then ready; the health trigger fired once, so no second frenzy.
    stepFrenzy(modifiers, actor, 2.0f);
    CHECK(modifiers.frenzyPhase(0) == GameplayActorModifiers::FrenzyPhase::Spent);
    CHECK(frenzyAiFacts(modifiers).behavior.holdActive);
    REQUIRE(modifiers.scriptedClip(0, 7, pRole, clipSeconds));
    CHECK(std::string(pRole) == "spent");
    stepFrenzy(modifiers, actor, 5.0f);
    CHECK(modifiers.frenzyPhase(0) == GameplayActorModifiers::FrenzyPhase::Ready);
    CHECK(modifiers.frenzyCount() == 1);
}

TEST_CASE("frenzy repeats every_seconds below its health share, and a stun in the roar cancels it")
{
    const MonsterModifierTable table = frenzyTable("{frenzy: {health_below: 0.5, every_seconds: 5, "
        "windup_seconds: 1, seconds: 1, cooldown_seconds: 3}}");
    {
        GameplayActorModifiers modifiers;
        modifiers.bind(&table);
        FrenzyTestActor actor;
        // Above the share the period does not run.
        stepFrenzy(modifiers, actor, 6.0f);
        CHECK(modifiers.frenzyCount() == 0);
        actor.healthShare = 0.3f;
        stepFrenzy(modifiers, actor, 0.1f);
        CHECK(modifiers.frenzyCount() == 1);
        // Roar 1 s, frenzy 1 s, cooldown 3 s; the period runs from the roar: the next one 5 s after it.
        stepFrenzy(modifiers, actor, 4.7f);
        CHECK(modifiers.frenzyCount() == 1);
        stepFrenzy(modifiers, actor, 0.4f);
        CHECK(modifiers.frenzyCount() == 2);
    }
    {
        GameplayActorModifiers modifiers;
        modifiers.bind(&table);
        FrenzyTestActor actor;
        actor.healthShare = 0.3f;
        stepFrenzy(modifiers, actor, 0.1f);
        REQUIRE(modifiers.frenzyPhase(0) == GameplayActorModifiers::FrenzyPhase::Roar);
        actor.canAct = false;
        stepFrenzy(modifiers, actor, 1.0f / 30.0f);
        CHECK(modifiers.frenzyPhase(0) == GameplayActorModifiers::FrenzyPhase::Ready);
        actor.canAct = true;
        stepFrenzy(modifiers, actor, 2.0f);
        CHECK(modifiers.frenzyCount() == 1);
    }
}

TEST_CASE("frenzy on a shield break, and frenzies and charges never overlap")
{
    {
        const MonsterModifierTable table = frenzyTable("{frenzy: {on_shield_break: true}}");
        GameplayActorModifiers modifiers;
        modifiers.bind(&table);
        FrenzyTestActor actor;
        stepFrenzy(modifiers, actor, 1.0f);
        CHECK(modifiers.frenzyCount() == 0);
        modifiers.observeHit(0, 10082, 7, {900.0f, 0.0f, 0.0f}, true, false);
        stepFrenzy(modifiers, actor, 1.0f / 30.0f);
        CHECK(modifiers.frenzyCount() == 0);
        modifiers.observeHit(0, 10082, 7, {900.0f, 0.0f, 0.0f}, false, true);
        stepFrenzy(modifiers, actor, 1.0f / 30.0f);
        CHECK(modifiers.frenzyCount() == 1);
    }
    {
        const MonsterModifierTable table = frenzyTable(
            "{charge: {windup_seconds: 0.5}}, {frenzy: {every_seconds: 1, windup_seconds: 1, spent_seconds: 1}}");
        GameplayActorModifiers modifiers;
        modifiers.bind(&table);
        FrenzyTestActor actor;
        // The party in the charge band: the charge starts first and the frenzy waits for it.
        stepFrenzy(modifiers, actor, 1.0f / 30.0f);
        CHECK(modifiers.chargePhase(0) == GameplayActorModifiers::ChargePhase::Windup);
        REQUIRE(modifiers.startFrenzy(0, 10082, 7, actor.world()) == false);
        CHECK(modifiers.frenzyCount() == 0);
    }
    {
        const MonsterModifierTable table = frenzyTable(
            "{charge: {windup_seconds: 0.5}}, {frenzy: {every_seconds: 1, windup_seconds: 1, spent_seconds: 1}}");
        GameplayActorModifiers modifiers;
        modifiers.bind(&table);
        FrenzyTestActor actor;
        // In the roar no charge starts.
        REQUIRE(modifiers.startFrenzy(0, 10082, 7, actor.world()));
        stepFrenzy(modifiers, actor, 0.5f);
        CHECK(modifiers.chargeCount() == 0);
        CHECK_FALSE(modifiers.startCharge(0, 10082, 7, {0.0f, 0.0f, 0.0f}, {900.0f, 0.0f, 0.0f}, actor.world()));
    }
}

TEST_CASE("charge hit damage and knock-back")
{
    MonsterTable::MonsterStatsEntry brute = {};
    brute.attack1Type = "Phys";
    brute.attack1Damage = {2, 6, 3};
    ChargeModifier fixed;
    fixed.useMelee = false;
    fixed.damage = 30.0f;
    CHECK(GameplayActorModifiers::chargeHit(fixed, &brute, 1).damage == 30);
    ChargeModifier melee;
    for (uint32_t seed = 0; seed < 50; ++seed)
    {
        const GameplayActorModifiers::ChargeHit hit = GameplayActorModifiers::chargeHit(melee, &brute, seed);
        CHECK(hit.damage >= 5);
        CHECK(hit.damage <= 15);
        CHECK(hit.ability == GameplayActorAttackAbility::Attack1);
    }

    // A Lancer's Attack1 is its beam: the charge thrusts with Attack2.
    MonsterTable::MonsterStatsEntry lancer = brute;
    lancer.attack1HasMissile = true;
    lancer.attack1Type = "Ener";
    lancer.attack1Damage = {10, 10, 0};
    lancer.attack2Type = "Phys";
    lancer.attack2Damage = {1, 4, 100};
    const GameplayActorModifiers::ChargeHit thrust = GameplayActorModifiers::chargeHit(melee, &lancer, 3);
    CHECK(thrust.ability == GameplayActorAttackAbility::Attack2);
    CHECK(thrust.damage >= 101);
    CHECK(thrust.damage <= 104);
    CHECK(thrust.damageType == CombatDamageType::Physical);
    const std::array<float, 3> impulse = GameplayActorModifiers::chargeKnockbackImpulse(0.0f, 1.0f, 256.0f, 1280.0f);
    CHECK(impulse[0] == doctest::Approx(0.0f));
    CHECK(impulse[2] > 0.0f);
    // Up and down under gravity: 2 * vz / g seconds at the horizontal speed covers the distance.
    CHECK(impulse[1] * 2.0f * impulse[2] / 1280.0f == doctest::Approx(256.0f));
}

TEST_CASE("melee vertical reach: a ledge above half the lower body's height stops a blow, a step never does")
{
    // No reach set (MM6-MM8): height never matters.
    CHECK(GameplayActorService::meleeReachesVertically(0.0f, 0.0f, 179.0f, 500.0f, 192.0f));
    // Half of a 179-high Drudge: it cannot strike a party 96 above it, can strike one 80 above it.
    CHECK_FALSE(GameplayActorService::meleeReachesVertically(0.5f, 0.0f, 179.0f, 96.0f, 192.0f));
    CHECK(GameplayActorService::meleeReachesVertically(0.5f, 0.0f, 179.0f, 80.0f, 192.0f));
    // A tall monster reaches higher.
    CHECK(GameplayActorService::meleeReachesVertically(0.5f, 0.0f, 400.0f, 180.0f, 192.0f));
    // Down onto a party below: half the party's 192.
    CHECK(GameplayActorService::meleeReachesVertically(0.5f, 96.0f, 179.0f, 0.0f, 192.0f));
    CHECK_FALSE(GameplayActorService::meleeReachesVertically(0.5f, 128.0f, 179.0f, 0.0f, 192.0f));
    // A small body still reaches across a step.
    CHECK(GameplayActorService::meleeReachesVertically(0.5f, 0.0f, 40.0f, 48.0f, 192.0f));
    CHECK_FALSE(GameplayActorService::meleeReachesVertically(0.5f, 0.0f, 40.0f, 49.0f, 192.0f));
}

TEST_CASE("stagger rules: only heavy damage within the window flinches, then not again within the cooldown")
{
    MonsterModifierTable table;
    std::string error;
    REQUIRE_MESSAGE(loadModifiers(table,
        "  10010: [{stagger: {threshold_percent: 8, cooldown_seconds: 2}}]\n", error), error);
    REQUIRE(table.find(10010) != nullptr);
    REQUIRE(table.find(10010)->stagger);
    CHECK(table.find(10010)->stagger->windowSeconds == doctest::Approx(2.0f));

    GameplayActorModifiers modifiers;
    modifiers.bind(&table);
    // A trooper of 1 000 health: 8 % is 80 within 2 s.
    modifiers.recordDamage(0, 10010, 7, 50);
    CHECK_FALSE(modifiers.allowsStagger(0, 10010, 7, 1000));
    modifiers.tickStagger(1.0f);
    modifiers.recordDamage(0, 10010, 7, 40);
    CHECK(modifiers.allowsStagger(0, 10010, 7, 1000));
    // The cooldown: a heavy hit at once does nothing.
    modifiers.recordDamage(0, 10010, 7, 500);
    CHECK_FALSE(modifiers.allowsStagger(0, 10010, 7, 1000));
    // Old chip damage leaves the window.
    modifiers.tickStagger(2.5f);
    modifiers.recordDamage(0, 10010, 7, 50);
    CHECK_FALSE(modifiers.allowsStagger(0, 10010, 7, 1000));
    // A monster without the rules always may.
    CHECK(modifiers.allowsStagger(1, 10011, 8, 1000));

    CHECK(modifierError("  10010: [never_staggers, stagger]\n").find("contradict") != std::string::npos);
}
