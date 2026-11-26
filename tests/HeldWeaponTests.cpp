#include "game/gameplay/GameMechanics.h"
#include "game/party/Party.h"
#include "game/render/FirstPersonViewModel.h"
#include "game/render/HeldWeapons.h"
#include "game/rules/ClassRules.h"
#include "game/rules/maw/MawClassRules.h"

#include <doctest/doctest.h>

#include <array>
#include <filesystem>
#include <fstream>
#include <sstream>

using namespace OpenYAMM;
using namespace OpenYAMM::Game;

namespace
{
std::array<float, 3> apply(const Engine::ModelMatrix &matrix, const std::array<float, 3> &point)
{
    return {matrix[0] * point[0] + matrix[4] * point[1] + matrix[8] * point[2] + matrix[12],
        matrix[1] * point[0] + matrix[5] * point[1] + matrix[9] * point[2] + matrix[13],
        matrix[2] * point[0] + matrix[6] * point[1] + matrix[10] * point[2] + matrix[14]};
}

float determinant(const Engine::ModelMatrix &m)
{
    return m[0] * (m[5] * m[10] - m[9] * m[6]) - m[4] * (m[1] * m[10] - m[9] * m[2])
        + m[8] * (m[1] * m[6] - m[5] * m[2]);
}

Engine::ModelBounds bounds(std::array<float, 3> min, std::array<float, 3> max)
{
    Engine::ModelBounds result;
    result.min = min;
    result.max = max;
    result.valid = true;
    return result;
}
}

TEST_CASE("held weapons: the table parses and rejects bad entries")
{
    HeldWeaponGrips grips;
    std::string error;
    const std::string good = "schema: openyamm.heldWeapons.v1\nheld:\n"
                             "  - {icon: sword1, kind: sword, long: z, head: -1, edge: 1, grip: 0.18, length: 79}\n"
                             "  - {icon: shield1, kind: shield, long: x, head: 1, grip: 0.5, length: 47}\n"
                             "  - {icon: bow1, kind: bow, long: z, head: 1, edge: -1, across: 0.7, grip: 0.5, length: 107}\n";
    REQUIRE(parseHeldWeaponGrips(good, "held.yml", grips, error));
    CHECK(grips.at("sword1").longAxis == 2);
    CHECK(grips.at("sword1").head == -1);
    CHECK(grips.at("shield1").mount == HeldWeaponMount::Shield);
    CHECK(grips.at("bow1").mount == HeldWeaponMount::Bow);
    CHECK(grips.at("bow1").across == doctest::Approx(0.7f));

    HeldWeaponGrips twice;
    CHECK_FALSE(parseHeldWeaponGrips(good + "  - {icon: sword1, kind: sword, long: x}\n", "held.yml", twice, error));
    HeldWeaponGrips badAxis;
    CHECK_FALSE(parseHeldWeaponGrips("schema: openyamm.heldWeapons.v1\nheld:\n  - {icon: a, kind: sword, long: y}\n",
        "held.yml", badAxis, error));
    HeldWeaponGrips badSchema;
    CHECK_FALSE(parseHeldWeaponGrips("schema: other\nheld: []\n", "held.yml", badSchema, error));
}

TEST_CASE("held weapons: a blade lying along -Z is held tip up, palm at the grip, without mirroring")
{
    HeldWeaponGrip grip;
    grip.longAxis = 2;
    grip.head = -1;
    grip.edge = 1;
    grip.grip = 0.2f;
    grip.length = 100.0f;
    const std::optional<Engine::ModelMatrix> matrix = heldWeaponMatrix(bounds({-2, -1, -50}, {2, 1, 50}), grip);
    REQUIRE(matrix.has_value());
    // The head is at the minimum Z, the butt at the maximum; the palm 20 % of the length up from the butt.
    const std::array<float, 3> palm = apply(*matrix, {0.0f, 0.0f, 30.0f});
    const std::array<float, 3> tip = apply(*matrix, {0.0f, 0.0f, -50.0f});
    const std::array<float, 3> butt = apply(*matrix, {0.0f, 0.0f, 50.0f});
    CHECK(palm[1] == doctest::Approx(0.0f).epsilon(1e-4));
    CHECK(tip[1] == doctest::Approx(80.0f));
    CHECK(butt[1] == doctest::Approx(-20.0f));
    // The edge axis (X) stays X, and the turn is a rotation (no inside-out faces).
    CHECK(apply(*matrix, {2.0f, 0.0f, 30.0f})[0] == doctest::Approx(2.0f));
    CHECK(determinant(*matrix) > 0.0f);
}

TEST_CASE("held weapons: the length scales the model and the edge sign turns the blade")
{
    HeldWeaponGrip grip;
    grip.longAxis = 0;
    grip.head = 1;
    grip.edge = -1;
    grip.grip = 0.0f;
    grip.length = 50.0f;
    const std::optional<Engine::ModelMatrix> matrix = heldWeaponMatrix(bounds({0, 0, -10}, {200, 4, 10}), grip);
    REQUIRE(matrix.has_value());
    CHECK(apply(*matrix, {200.0f, 2.0f, 0.0f})[1] == doctest::Approx(50.0f));
    // The axe's blade at +Z (the edge axis for a model along X) turns to -X.
    CHECK(apply(*matrix, {0.0f, 2.0f, 10.0f})[0] == doctest::Approx(-2.5f));
    CHECK(determinant(*matrix) > 0.0f);
}

TEST_CASE("held weapons: a shield faces out from the forearm and a bow centres on its riser")
{
    HeldWeaponGrip shield;
    shield.kind = "shield";
    shield.mount = HeldWeaponMount::Shield;
    shield.longAxis = 0;
    shield.length = 47.0f;
    const std::optional<Engine::ModelMatrix> shieldMatrix = heldWeaponMatrix(bounds({-30, 0, -20}, {30, 6, 20}), shield);
    REQUIRE(shieldMatrix.has_value());
    const std::array<float, 3> centre = apply(*shieldMatrix, {0.0f, 3.0f, 0.0f});
    CHECK(centre[0] == doctest::Approx(21.8f));
    CHECK(centre[1] == doctest::Approx(-3.8f));
    CHECK(centre[2] == doctest::Approx(4.3f));
    // The face (the model's top) lies further toward -Y than its back.
    CHECK(apply(*shieldMatrix, {0.0f, 6.0f, 0.0f})[1] < apply(*shieldMatrix, {0.0f, 0.0f, 0.0f})[1]);
    CHECK(determinant(*shieldMatrix) > 0.0f);

    HeldWeaponGrip bow;
    bow.kind = "bow";
    bow.mount = HeldWeaponMount::Bow;
    bow.longAxis = 2;
    bow.grip = 0.5f;
    bow.across = 0.75f;
    bow.length = 100.0f;
    const std::optional<Engine::ModelMatrix> bowMatrix = heldWeaponMatrix(bounds({-8, -1, -50}, {8, 1, 50}), bow);
    REQUIRE(bowMatrix.has_value());
    const std::array<float, 3> riser = apply(*bowMatrix, {4.0f, 0.0f, 0.0f});
    CHECK(riser[0] == doctest::Approx(0.0f).epsilon(1e-4));
    CHECK(riser[1] == doctest::Approx(0.0f).epsilon(1e-4));
    CHECK(determinant(*bowMatrix) > 0.0f);
}

TEST_CASE("solo bow swap: with the bow drawn Attack shoots even in melee reach, only with a usable bow")
{
    Game::CharacterAttackProfile archer;
    archer.hasBow = true;
    archer.rangedAttackBonus = 10;
    CHECK(GameMechanics::soloBowShotMode(archer, false) == CharacterAttackMode::Bow);
    // Under water no bow is fired: the attack falls back to the weapon's blow.
    CHECK_FALSE(GameMechanics::soloBowShotMode(archer, true).has_value());

    Game::CharacterAttackProfile noBow;
    noBow.rangedAttackBonus = 10;
    CHECK_FALSE(GameMechanics::soloBowShotMode(noBow, false).has_value());

    // A blaster or wand in the main hand would shoot first in a party; with the bow drawn the bow shoots.
    Game::CharacterAttackProfile gunner = archer;
    gunner.hasBlaster = true;
    CHECK(GameMechanics::soloBowShotMode(gunner, false) == CharacterAttackMode::Bow);
}

TEST_CASE("held weapons: girth thins the cross-section and keeps the length")
{
    HeldWeaponGrip staff;
    staff.longAxis = 2;
    staff.head = 1;
    staff.grip = 0.5f;
    staff.length = 100.0f;
    staff.girth = 0.5f;
    const std::optional<Engine::ModelMatrix> matrix = heldWeaponMatrix(bounds({-4, -4, -50}, {4, 4, 50}), staff);
    REQUIRE(matrix.has_value());
    CHECK(apply(*matrix, {0.0f, 0.0f, 50.0f})[1] == doctest::Approx(50.0f));
    CHECK(apply(*matrix, {4.0f, 0.0f, 0.0f})[0] == doctest::Approx(2.0f));
    CHECK(determinant(*matrix) > 0.0f);
}

TEST_CASE("held weapon tiers: value bands, two-handed scale, uniques and enchantments")
{
    HeldSkinRules rules;
    std::string error;
    const std::string text = "schema: openyamm.heldTiers.v1\n"
                             "template_kinds: [sword, mace, bow]\n"
                             "tiers: 3\nvalue_bands: [150, 600]\nvalue_scale: {Weapon2: 0.5}\n"
                             "unique_tier: 3\nenchanted_bonus: 1\n";
    REQUIRE(parseHeldSkinRules(text, "test", rules, error));
    CHECK(heldSkinTier(rules, {.value = 20, .equipStat = "Weapon"}) == 1);
    CHECK(heldSkinTier(rules, {.value = 149, .equipStat = "Weapon"}) == 1);
    CHECK(heldSkinTier(rules, {.value = 150, .equipStat = "Weapon"}) == 2);
    CHECK(heldSkinTier(rules, {.value = 600, .equipStat = "Weapon"}) == 3);
    CHECK(heldSkinTier(rules, {.value = 1100, .equipStat = "Weapon2"}) == 2);
    CHECK(heldSkinTier(rules, {.value = 1200, .equipStat = "Weapon2"}) == 3);
    CHECK(heldSkinTier(rules, {.value = 0, .equipStat = "Weapon", .unique = true}) == 3);
    CHECK(heldSkinTier(rules, {.value = 20, .equipStat = "Weapon", .enchanted = true}) == 2);
    CHECK(heldSkinTier(rules, {.value = 900, .equipStat = "Weapon", .enchanted = true}) == 3);
    CHECK(heldSkinUsesTemplate(rules, "sword"));
    CHECK_FALSE(heldSkinUsesTemplate(rules, "spear"));
    CHECK(heldSkinFile("w_longsword.glb", 2) == "w_longsword_t2.glb");
    CHECK(heldSkinFile("w_longsword.glb", 0) == "w_longsword.glb");

    // Four tiers with the enchantment raising at most to the third; uniques and the top band reach the fourth.
    HeldSkinRules four;
    REQUIRE(parseHeldSkinRules("schema: openyamm.heldTiers.v1\ntiers: 4\nvalue_bands: [150, 600, 5000]\n"
                               "value_scale: {Weapon2: 0.5}\nunique_tier: 4\nenchanted_bonus: 1\n"
                               "enchanted_max_tier: 3\n",
        "test", four, error));
    CHECK(heldSkinTier(four, {.value = 4999, .equipStat = "Weapon"}) == 3);
    CHECK(heldSkinTier(four, {.value = 5000, .equipStat = "Weapon"}) == 4);
    CHECK(heldSkinTier(four, {.value = 9998, .equipStat = "Weapon2"}) == 3);
    CHECK(heldSkinTier(four, {.value = 10000, .equipStat = "Weapon2"}) == 4);
    CHECK(heldSkinTier(four, {.value = 100, .equipStat = "Weapon", .enchanted = true}) == 2);
    CHECK(heldSkinTier(four, {.value = 700, .equipStat = "Weapon", .enchanted = true}) == 3);
    CHECK(heldSkinTier(four, {.value = 6000, .equipStat = "Weapon", .enchanted = true}) == 4);
    CHECK(heldSkinTier(four, {.value = 10, .equipStat = "Weapon", .unique = true}) == 4);

    // A loot rarity (MAW) lifts the tier to its own, never lowers it: a Legendary broadsword at base price is legendary.
    HeldSkinRules rarity;
    REQUIRE(parseHeldSkinRules("schema: openyamm.heldTiers.v1\ntiers: 4\nvalue_bands: [150, 600, 5000]\n"
                               "loot_rarity_tiers: [1, 2, 2, 3, 4, 4, 4, 4]\n",
        "test", rarity, error));
    CHECK(heldSkinTier(rarity, {.value = 400, .equipStat = "Weapon", .lootRarity = 7}) == 4);
    CHECK(heldSkinTier(rarity, {.value = 400, .equipStat = "Weapon", .lootRarity = 4}) == 3);
    CHECK(heldSkinTier(rarity, {.value = 700, .equipStat = "Weapon", .lootRarity = 1}) == 3);
    CHECK(heldSkinTier(rarity, {.value = 100, .equipStat = "Weapon", .lootRarity = 9}) == 1);
    CHECK_FALSE(parseHeldSkinRules("schema: openyamm.heldTiers.v1\ntiers: 4\nvalue_bands: [150, 600, 5000]\n"
                                   "loot_rarity_tiers: [1, 5]\n",
        "t", rarity, error));
    HeldSkinRules rejected;
    CHECK_FALSE(parseHeldSkinRules("schema: openyamm.heldTiers.v1\ntiers: 3\nvalue_bands: [150, 600]\n"
                                   "enchanted_max_tier: 4\n",
        "t", rejected, error));

    HeldSkinRules bad;
    CHECK_FALSE(parseHeldSkinRules("schema: openyamm.heldTiers.v1\ntiers: 3\nvalue_bands: [600, 150]\n", "t", bad,
        error));
    CHECK_FALSE(parseHeldSkinRules("schema: openyamm.heldTiers.v1\ntiers: 3\nvalue_bands: [150]\n", "t", bad,
        error));
    CHECK_FALSE(parseHeldSkinRules("schema: other\n", "t", bad, error));
}

TEST_CASE("held weapon tiers: the engine's table parses and gives the starting swords the low tier")
{
    std::ifstream file(std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/world_items/held_tiers.yml");
    REQUIRE(file);
    std::stringstream text;
    text << file.rdbuf();
    HeldSkinRules rules;
    std::string error;
    REQUIRE_MESSAGE(parseHeldSkinRules(text.str(), "held_tiers.yml", rules, error), error);
    CHECK(rules.tierCount == 4);
    // Iron Longsword (a new knight's), Steel Broadsword, Champion's Sword, Iron Two-Handed Sword, Headsman's Reaver.
    CHECK(heldSkinTier(rules, {.value = 20, .equipStat = "Weapon"}) == 1);
    CHECK(heldSkinTier(rules, {.value = 300, .equipStat = "Weapon"}) == 2);
    CHECK(heldSkinTier(rules, {.value = 700, .equipStat = "Weapon"}) == 3);
    CHECK(heldSkinTier(rules, {.value = 200, .equipStat = "Weapon2"}) == 1);
    CHECK(heldSkinTier(rules, {.value = 2000, .equipStat = "Weapon2"}) == 3);
    // Legendary: artifacts and relics, and the most valuable bases; an enchantment stops at high.
    CHECK(heldSkinTier(rules, {.value = 0, .equipStat = "Weapon", .unique = true}) == 4);
    CHECK(heldSkinTier(rules, {.value = 5000, .equipStat = "Weapon"}) == 4);
    CHECK(heldSkinTier(rules, {.value = 2000, .equipStat = "Weapon", .enchanted = true}) == 3);
    for (const char *pKind : {"sword", "shortsword", "greatsword", "mace", "bow", "spear", "trident", "polearm",
             "poleaxe", "club", "crossbow", "wand", "blaster"})
    {
        CHECK(heldSkinUsesTemplate(rules, pKind));
    }
    // Cutlasses, scimitars, sabres and falchions hold the short sword; other one-handed swords the longsword.
    const HeldKindTemplate *pShort = heldKindTemplate(rules, "shortsword");
    REQUIRE(pShort != nullptr);
    CHECK(pShort->file == "w_shortsword.glb");
    CHECK(pShort->maxTier == 0);
    CHECK(heldKindTemplate(rules, "sword") == nullptr);
}

TEST_CASE("held weapon tiers: kinds with a template of their own, clubs capped at the mid tier")
{
    HeldSkinRules rules;
    std::string error;
    REQUIRE(parseHeldSkinRules("schema: openyamm.heldTiers.v1\ntiers: 4\nvalue_bands: [150, 600, 5000]\n"
                               "kind_templates:\n  spear: {file: w_spear.glb}\n"
                               "  club: {file: w_club.glb, max_tier: 2}\n",
        "t", rules, error));
    const HeldKindTemplate *pSpear = heldKindTemplate(rules, "spear");
    REQUIRE(pSpear != nullptr);
    CHECK(pSpear->file == "w_spear.glb");
    CHECK(pSpear->maxTier == 0);
    const HeldKindTemplate *pClub = heldKindTemplate(rules, "club");
    REQUIRE(pClub != nullptr);
    CHECK(pClub->maxTier == 2);
    CHECK(heldKindTemplate(rules, "sword") == nullptr);
    HeldSkinRules bad;
    CHECK_FALSE(parseHeldSkinRules("schema: openyamm.heldTiers.v1\ntiers: 4\nvalue_bands: [150, 600, 5000]\n"
                                   "kind_templates:\n  spear: {max_tier: 1}\n",
        "t", bad, error));
    CHECK_FALSE(parseHeldSkinRules("schema: openyamm.heldTiers.v1\ntiers: 4\nvalue_bands: [150, 600, 5000]\n"
                                   "kind_templates:\n  club: {file: w_club.glb, max_tier: 5}\n",
        "t", bad, error));

    // The engine's table: every new template and its skins up to its max_tier (all four without one) are installed
    // (devdocs/solo_action/WEAPONS.md "New templates (2026-11-14)").
    std::ifstream file(std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/world_items/held_tiers.yml");
    REQUIRE(file);
    std::stringstream text;
    text << file.rdbuf();
    HeldSkinRules engine;
    REQUIRE_MESSAGE(parseHeldSkinRules(text.str(), "held_tiers.yml", engine, error), error);
    const std::filesystem::path viewModel = std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/view_model";
    for (const char *pKind : {"spear", "trident", "polearm", "poleaxe", "crossbow", "wand", "blaster", "club"})
    {
        const HeldKindTemplate *pOwn = heldKindTemplate(engine, pKind);
        REQUIRE_MESSAGE(pOwn != nullptr, pKind);
        CHECK(std::filesystem::exists(viewModel / pOwn->file));
        const uint8_t topTier = pOwn->maxTier > 0 ? pOwn->maxTier : engine.tierCount;
        for (uint8_t tier = 1; tier <= topTier; ++tier)
        {
            CHECK_MESSAGE(std::filesystem::exists(viewModel / heldSkinFile(pOwn->file, tier)),
                heldSkinFile(pOwn->file, tier));
        }
    }
    const HeldKindTemplate *pEngineClub = heldKindTemplate(engine, "club");
    REQUIRE(pEngineClub != nullptr);
    CHECK(pEngineClub->file == "w_club.glb");
    CHECK(pEngineClub->maxTier == 2);
}

TEST_CASE("held weapon tiers: template_scales draws a template smaller, the battle axe at 80 percent")
{
    HeldSkinRules rules;
    std::string error;
    REQUIRE(parseHeldSkinRules("schema: openyamm.heldTiers.v1\ntiers: 4\nvalue_bands: [150, 600, 5000]\n"
                               "template_scales: {w_battleaxe.glb: 0.8}\n",
        "t", rules, error));
    CHECK(heldTemplateScale(rules, "w_battleaxe.glb") == doctest::Approx(0.8f));
    CHECK(heldTemplateScale(rules, "w_waraxe.glb") == 1.0f);
    HeldSkinRules bad;
    CHECK_FALSE(parseHeldSkinRules("schema: openyamm.heldTiers.v1\ntiers: 4\nvalue_bands: [150, 600, 5000]\n"
                                   "template_scales: {w_battleaxe.glb: 0}\n",
        "t", bad, error));

    std::ifstream file(std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/world_items/held_tiers.yml");
    REQUIRE(file);
    std::stringstream text;
    text << file.rdbuf();
    HeldSkinRules engine;
    REQUIRE_MESSAGE(parseHeldSkinRules(text.str(), "held_tiers.yml", engine, error), error);
    CHECK(heldTemplateScale(engine, "w_battleaxe.glb") == doctest::Approx(0.8f));
    CHECK(heldTemplateScale(engine, "w_claymore.glb") == 1.0f);
}

TEST_CASE("dual wielding: a melee weapon in each hand is the dual kit, anything else keeps the main hand's")
{
    using ViewModel = FirstPersonViewModel;
    const ViewModel::Kit swords = ViewModel::kitForHands("Sword", false, false, "Sword", false);
    CHECK(swords.set == ViewModel::WeaponSet::Dual);
    CHECK(swords.weapon == "w_longsword.glb");
    CHECK(swords.offWeapon == "w_longsword.glb");
    CHECK_FALSE(swords.heavy);

    const ViewModel::Kit daggerSword = ViewModel::kitForHands("Sword", false, false, "Dagger", false);
    CHECK(daggerSword.set == ViewModel::WeaponSet::Dual);
    CHECK(daggerSword.weapon == "w_longsword.glb");
    CHECK(daggerSword.offWeapon == "w_dagger.glb");
    CHECK(ViewModel::kitForHands("Axe", false, false, "Axe", false).offWeapon == "w_waraxe.glb");
    CHECK(ViewModel::kitForHands("Mace", false, false, "Club", false).set == ViewModel::WeaponSet::Dual);

    // A MAW Minotaur's two-handed axes, one in each hand: the larger template and the heavier swing.
    const ViewModel::Kit minotaur = ViewModel::kitForHands("Axe", false, true, "Axe", true);
    CHECK(minotaur.set == ViewModel::WeaponSet::Dual);
    CHECK(minotaur.weapon == "w_battleaxe.glb");
    CHECK(minotaur.offWeapon == "w_battleaxe.glb");
    CHECK(minotaur.heavy);

    // A shield (never shown), an empty off hand, a weapon wielded two-handed or a staff, spear or bow: the main hand's
    // kit as before.
    CHECK(ViewModel::kitForHands("Sword", false, false, "Shield", false) == ViewModel::kitFor("Sword", false));
    CHECK(ViewModel::kitForHands("Sword", false, false, "", false) == ViewModel::kitFor("Sword", false));
    CHECK(ViewModel::kitForHands("Sword", true, true, "Dagger", false) == ViewModel::kitFor("Sword", true));
    CHECK(ViewModel::kitForHands("Spear", false, false, "Sword", false).set == ViewModel::WeaponSet::TwoHand);
    CHECK(ViewModel::kitForHands("", false, false, "Dagger", false).set == ViewModel::WeaponSet::HandToHand);
    CHECK_FALSE(ViewModel::dualWieldable("Bow"));
    CHECK_FALSE(ViewModel::dualWieldable("Staff"));
    CHECK_FALSE(ViewModel::dualWieldable("Shield"));
}

TEST_CASE("dual wielding: the combo alternates the leading hand and closes each round with a power blow")
{
    using ViewModel = FirstPersonViewModel;
    // The side each blow hands on to comes from the clip's chain key: dualattackright chains to the left, the left
    // back to the right, as the one-handed cuts do. Standing, the fifth blow is the cross slash (dualattackpower).
    std::vector<std::string> actions;
    char side = 'R';
    for (uint32_t step = 0; step < 10; ++step)
    {
        const std::string action = ViewModel::comboAction(step, side, 0.0f, 0.0f);
        actions.push_back(action);
        side = action.starts_with("attackright") ? 'L' : 'R';
    }
    const std::vector<std::string> expected = {"attackright", "attackleft", "attackright_chop", "attackleft_chop",
        "attackpower", "attackright", "attackleft", "attackright_chop", "attackleft_chop", "attackpower"};
    CHECK(actions == expected);
    // Moving, the power blow follows the direction: a lunge forward, a sweep sideways, a step-back cut.
    CHECK(ViewModel::comboAction(4, 'R', 300.0f, 0.0f) == "attackforwardpower");
    CHECK(ViewModel::comboAction(4, 'R', -300.0f, 0.0f) == "attackbackpower");
    CHECK(ViewModel::comboAction(4, 'R', 0.0f, 300.0f) == "attackleftpower");
    CHECK(ViewModel::comboAction(4, 'R', 0.0f, -300.0f) == "attackrightpower");
}

TEST_CASE("crossbows: the drawn bow's held kind picks the crossbow set, any other bow keeps the bow set")
{
    using ViewModel = FirstPersonViewModel;
    const ViewModel::Kit crossbow = ViewModel::kitForBow("crossbow");
    CHECK(crossbow.set == ViewModel::WeaponSet::Crossbow);
    CHECK(crossbow.weapon == "w_crossbow.glb");
    CHECK(ViewModel::kitForBow("bow") == ViewModel::kitFor("Bow", false));
    // An icon without a held.yml row has no kind: the bow set as before.
    CHECK(ViewModel::kitForBow("") == ViewModel::kitFor("Bow", false));
    CHECK(ViewModel::kitForBow("bow").set == ViewModel::WeaponSet::Bow);

    // The engine's table: every crossbow icon is of the crossbow kind, so the bow slot draws the crossbow set.
    std::ifstream file(std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/world_items/held.yml");
    REQUIRE(file);
    std::stringstream text;
    text << file.rdbuf();
    HeldWeaponGrips grips;
    std::string error;
    REQUIRE_MESSAGE(parseHeldWeaponGrips(text.str(), "held.yml", grips, error), error);
    for (const char *pIcon : {"crsbow1", "crsbow2", "crsbow3", "item061", "7item047"})
    {
        REQUIRE_MESSAGE(grips.contains(pIcon), pIcon);
        CHECK(ViewModel::kitForBow(grips.at(pIcon).kind).set == ViewModel::WeaponSet::Crossbow);
    }
}

TEST_CASE("pole weapons: spears, tridents, polearms and poleaxes get the pole set, staves keep the two-handed one")
{
    using ViewModel = FirstPersonViewModel;
    // A spear in two hands, and a Spear Master's spear with a shield: both hands on the shaft, no shield.
    const ViewModel::Kit spear = ViewModel::kitForHeldKind(ViewModel::kitForHands("Spear", true, false, "", false),
        "spear");
    CHECK(spear.set == ViewModel::WeaponSet::Pole);
    CHECK(spear.weapon == "w_spear.glb");
    const ViewModel::Kit master = ViewModel::kitForHeldKind(
        ViewModel::kitForHands("Spear", false, false, "Shield", false), "trident");
    CHECK(master.set == ViewModel::WeaponSet::Pole);
    // A poleaxe is an Axe item (the battle axe's kit before), a halberd a Spear one: both the pole set.
    CHECK(ViewModel::kitForHeldKind(ViewModel::kitForHands("Axe", true, true, "", false), "poleaxe").set
        == ViewModel::WeaponSet::Pole);
    CHECK(ViewModel::kitForHeldKind(ViewModel::kitForHands("Spear", true, true, "", false), "polearm").set
        == ViewModel::WeaponSet::Pole);
    // Our ground model and its skin tier ride along.
    ViewModel::Kit held = ViewModel::kitForHands("Spear", true, false, "", false);
    held.heldModel = "engine/world_items/models/item_item042.glb";
    held.heldIcon = "item042";
    held.weaponTier = 2;
    const ViewModel::Kit heldPole = ViewModel::kitForHeldKind(held, "spear");
    CHECK(heldPole.heldModel == held.heldModel);
    CHECK(heldPole.heldIcon == "item042");
    CHECK(heldPole.weaponTier == 2);

    // Anything else is unchanged: a staff, a sword, an icon without a held.yml row, and a MAW Minotaur's poleaxe
    // dual wielded with an axe.
    const ViewModel::Kit staff = ViewModel::kitForHands("Staff", true, false, "", false);
    CHECK(ViewModel::kitForHeldKind(staff, "staff") == staff);
    CHECK(ViewModel::kitForHeldKind(staff, "staff").set == ViewModel::WeaponSet::TwoHand);
    const ViewModel::Kit sword = ViewModel::kitForHands("Sword", false, false, "Shield", false);
    CHECK(ViewModel::kitForHeldKind(sword, "sword") == sword);
    const ViewModel::Kit unknown = ViewModel::kitForHands("Spear", true, false, "", false);
    CHECK(ViewModel::kitForHeldKind(unknown, "") == unknown);
    const ViewModel::Kit minotaur = ViewModel::kitForHands("Axe", false, true, "Axe", true);
    CHECK(ViewModel::kitForHeldKind(minotaur, "poleaxe") == minotaur);
    CHECK_FALSE(ViewModel::poleKind("staff"));
    CHECK_FALSE(ViewModel::poleKind("greataxe"));

    // The engine's table: every row of a pole kind gets the pole set, every staff keeps the two-handed set.
    std::ifstream file(std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/world_items/held.yml");
    REQUIRE(file);
    std::stringstream text;
    text << file.rdbuf();
    HeldWeaponGrips grips;
    std::string error;
    REQUIRE_MESSAGE(parseHeldWeaponGrips(text.str(), "held.yml", grips, error), error);
    for (const char *pIcon : {"item042", "2haxe1", "6trident5", "7item036", "halberd1"})
    {
        REQUIRE_MESSAGE(grips.contains(pIcon), pIcon);
        CHECK_MESSAGE(ViewModel::poleKind(grips.at(pIcon).kind), pIcon);
    }
    size_t poles = 0;
    for (const auto &[icon, grip] : grips)
    {
        if (grip.kind == "staff")
        {
            CHECK_MESSAGE(ViewModel::kitForHeldKind(staff, grip.kind).set == ViewModel::WeaponSet::TwoHand, icon);
        }
        poles += ViewModel::poleKind(grip.kind) ? 1 : 0;
    }
    CHECK(poles >= 40);
}

TEST_CASE("dragon view model: a dragon gets the clawed forelegs, everyone else the arms")
{
    using ViewModel = FirstPersonViewModel;
    // The choice GameApplication makes: ClassRules::isDragon (Standard: the Dragon and Great Wyrm classes; MAW: the
    // portrait's race), then the claws kit on the forelegs model, else the weapon kit on the arms.
    const auto kitOf = [](bool dragon)
    {
        return dragon ? ViewModel::dragonKit() : ViewModel::kitFor("Sword", false);
    };
    Character dragon;
    dragon.className = "Dragon";
    Character wyrm;
    wyrm.className = "GreatWyrm";
    Character knight;
    knight.className = "Knight";
    const ClassRules standard;
    CHECK(standard.isDragon(dragon));
    CHECK(standard.isDragon(wyrm));
    CHECK_FALSE(standard.isDragon(knight));

    const ViewModel::Kit claws = kitOf(standard.isDragon(dragon));
    CHECK(claws.set == ViewModel::WeaponSet::Claws);
    CHECK(claws.weapon.empty());
    CHECK(claws.offWeapon.empty());
    CHECK(ViewModel::packagedModelPath(claws) == "engine/view_model/dragon_forelegs.glb");

    const ViewModel::Kit arms = kitOf(standard.isDragon(knight));
    CHECK(arms.set == ViewModel::WeaponSet::OneHand);
    CHECK(ViewModel::packagedModelPath(arms) == "engine/view_model/arms.glb");
    CHECK(ViewModel::packagedModelPath(ViewModel::Kit{}) == "engine/view_model/arms.glb");
    CHECK(ViewModel::packagedModelPath(ViewModel::kitForBow("crossbow")) == "engine/view_model/arms.glb");

    // MAW: a Knight with the Dragon portrait (race 5) is a dragon; a Dragon-class human is not.
    Character dragonKnight = knight;
    dragonKnight.raceId = 5;
    Character humanDragon = dragon;
    humanDragon.raceId = 0;
    CHECK(mawIsDragon(dragonKnight));
    CHECK_FALSE(mawIsDragon(humanDragon));
    CHECK(kitOf(mawIsDragon(dragonKnight)).set == ViewModel::WeaponSet::Claws);
    CHECK(kitOf(mawIsDragon(humanDragon)).set == ViewModel::WeaponSet::OneHand);
}

TEST_CASE("dragon view model: the claws rake right and left and bite on the fifth blow")
{
    using ViewModel = FirstPersonViewModel;
    std::vector<std::string> actions;
    char side = 'R';
    for (uint32_t step = 0; step < 10; ++step)
    {
        const std::string action = ViewModel::clawsAction(step, side);
        actions.push_back(action);
        // The rakes' chain keys hand on to the other side; the bite has none, so the next round starts from the right.
        side = action == "attackright" ? 'L' : 'R';
    }
    const std::vector<std::string> expected = {"attackright", "attackleft", "attackright", "attackleft", "bite",
        "attackright", "attackleft", "attackright", "attackleft", "bite"};
    CHECK(actions == expected);
}

TEST_CASE("dragon view model: the installed forelegs carry the claws clips, text keys and contact nodes")
{
    const std::filesystem::path directory = std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/engine/view_model";
    std::ifstream keysFile(directory / "dragon_forelegs.textkeys.json");
    REQUIRE(keysFile);
    std::stringstream keysText;
    keysText << keysFile.rdbuf();
    const std::string keys = keysText.str();
    for (const char *pClip : {"clawsidle", "clawsattackright", "clawsattackleft", "clawsbite", "clawsbreath",
             "clawsblockidle", "clawsequip", "clawsforward", "clawsfastforward"})
    {
        CHECK_MESSAGE(keys.find(std::string("\"") + pClip + "\"") != std::string::npos, pClip);
    }
    std::ifstream model(directory / "dragon_forelegs.glb", std::ios::binary);
    REQUIRE(model);
    std::string header(20, '\0');
    model.read(header.data(), 20);
    const uint32_t jsonLength = uint32_t(uint8_t(header[12])) | uint32_t(uint8_t(header[13])) << 8
        | uint32_t(uint8_t(header[14])) << 16 | uint32_t(uint8_t(header[15])) << 24;
    std::string json(jsonLength, '\0');
    model.read(json.data(), jsonLength);
    for (const char *pNode : {"Camera01", "Weapon", "ClawTipR", "ClawTipL", "Mouth"})
    {
        CHECK_MESSAGE(json.find(std::string("\"name\":\"") + pNode + "\"") != std::string::npos, pNode);
    }
}
