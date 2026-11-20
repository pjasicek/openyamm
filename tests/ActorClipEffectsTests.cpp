#include "doctest/doctest.h"

#include "game/fx/ActorClipEffects.h"

#include <stdexcept>
#include <string>
#include <vector>

namespace
{
using OpenYAMM::Game::ActorClipEffect;

std::vector<ActorClipEffect> parse(const std::string &text, float clipSeconds = 1.5f)
{
    return OpenYAMM::Game::parseActorClipEffects(YAML::Load(text), clipSeconds,
        [](const std::string &socket) { return socket == "palm_left" || socket == "palm_right"; },
        [](const std::string &id) { return id == "mm9:redyeldots" || id == "mm9:bluedots"; }, "Test cast");
}
}

TEST_CASE("actor clip effects: one effect on a socket from a clip time")
{
    const std::vector<ActorClipEffect> effects =
        parse("{impact: 0.833, effect: {id: mm9:redyeldots, socket: palm_left, start: 0.13, end: 1.266}}");
    REQUIRE(effects.size() == 1);
    CHECK(effects[0].effectId == "mm9:redyeldots");
    CHECK(effects[0].sockets == std::vector<std::string>{"palm_left"});
    CHECK(effects[0].startSeconds == doctest::Approx(0.13f));
    CHECK(effects[0].endSeconds == doctest::Approx(1.266f));
    CHECK(effects[0].scale == doctest::Approx(1.0f));
    CHECK_FALSE(OpenYAMM::Game::actorClipEffectEmits(effects[0], 0.1f));
    CHECK(OpenYAMM::Game::actorClipEffectEmits(effects[0], 0.13f));
    CHECK(OpenYAMM::Game::actorClipEffectEmits(effects[0], 1.2f));
    CHECK_FALSE(OpenYAMM::Game::actorClipEffectEmits(effects[0], 1.266f));
}

TEST_CASE("actor clip effects: a list, both hands, defaults to the whole clip")
{
    const std::vector<ActorClipEffect> effects = parse(R"(
effects:
  - {id: mm9:bluedots, sockets: [palm_left, palm_right], scale: 0.5}
  - {id: mm9:redyeldots, socket: palm_right, start: 0.4}
)");
    REQUIRE(effects.size() == 2);
    CHECK(effects[0].sockets.size() == 2);
    CHECK(effects[0].startSeconds == doctest::Approx(0.0f));
    CHECK(effects[0].endSeconds < 0.0f);
    CHECK(effects[0].scale == doctest::Approx(0.5f));
    CHECK(OpenYAMM::Game::actorClipEffectEmits(effects[0], 1.49f));
    CHECK(effects[1].sockets == std::vector<std::string>{"palm_right"});
}

TEST_CASE("actor clip effects: the ranged attack's element map and a glow-only event carry none")
{
    CHECK(parse("{effects: {Fire: mm9:redyeldots}, glow: [palm_left]}").empty());
    CHECK(parse("{impact: 0.36, glow: [palm_left], color: [90, 140, 255]}").empty());
}

TEST_CASE("actor clip effects: authoring errors are rejected")
{
    CHECK_THROWS_AS(parse("{effect: {id: mm9:redyeldots, socket: staff_head}}"), std::runtime_error);
    CHECK_THROWS_AS(parse("{effect: {id: mm9:missing, socket: palm_left}}"), std::runtime_error);
    CHECK_THROWS_AS(parse("{effect: {socket: palm_left}}"), std::runtime_error);
    CHECK_THROWS_AS(parse("{effect: {id: mm9:bluedots}}"), std::runtime_error);
    CHECK_THROWS_AS(parse("{effect: {id: mm9:bluedots, socket: palm_left, sockets: [palm_right]}}"),
        std::runtime_error);
    CHECK_THROWS_AS(parse("{effect: {id: mm9:bluedots, socket: palm_left, colour: red}}"), std::runtime_error);
    CHECK_THROWS_AS(parse("{effect: {id: mm9:bluedots, socket: palm_left, start: 2.0}}"), std::runtime_error);
    CHECK_THROWS_AS(parse("{effect: {id: mm9:bluedots, socket: palm_left, start: 0.5, end: 0.4}}"),
        std::runtime_error);
    CHECK_THROWS_AS(parse("{effect: {id: mm9:bluedots, socket: palm_left, end: 1.6}}"), std::runtime_error);
    CHECK_THROWS_AS(parse("{effect: {id: mm9:bluedots, socket: palm_left, scale: 0}}"), std::runtime_error);
    CHECK_THROWS_AS(parse("{effect: {id: mm9:bluedots, socket: palm_left}, effects: [{id: mm9:bluedots, "
        "socket: palm_right}]}"), std::runtime_error);
    CHECK_THROWS_AS(parse("{effects: []}"), std::runtime_error);
    CHECK_THROWS_AS(parse("{effect: mm9:bluedots}"), std::runtime_error);
    CHECK_THROWS_AS(parse("{effect: {id: mm9:bluedots, sockets: [palm_left, palm_left, palm_left, palm_left, "
        "palm_left]}}"), std::runtime_error);
}

TEST_CASE("actor clip effects: a played clip's action role")
{
    // The Evil Sorcerer: melee AttackMelee (3), ranged and cast both AttackRanged (4).
    const std::array<uint32_t, 3> clips = {3, 4, 4};
    CHECK(OpenYAMM::Game::actorActionRoleForClip(clips, {true, true, true}, 3) == 0);
    CHECK(OpenYAMM::Game::actorActionRoleForClip(clips, {true, true, true}, 4) == 1);
    CHECK(OpenYAMM::Game::actorActionRoleForClip(clips, {true, false, true}, 4) == 2);
    CHECK(OpenYAMM::Game::actorActionRoleForClip(clips, {true, true, true}, 7) == -1);
    CHECK(OpenYAMM::Game::actorActionRoleForClip({3, 4, UINT32_MAX}, {true, true, true}, UINT32_MAX) == -1);
}

TEST_CASE("actor clip effects: a two-hand effect on two sockets gives each socket one hand's emitters")
{
    using namespace OpenYAMM::Game;
    EffectDefinition dots;
    dots.spriteEmitters.resize(2);
    dots.spriteEmitters[0].bodyAnchor = "left_hand";
    dots.spriteEmitters[1].bodyAnchor = "right_hand";
    CHECK(actorClipEffectSocketAnchor(dots, 2, 0) == "left_hand");
    CHECK(actorClipEffectSocketAnchor(dots, 2, 1) == "right_hand");
    // One socket, or a count that differs: the whole effect on each.
    CHECK(actorClipEffectSocketAnchor(dots, 1, 0).empty());
    CHECK(actorClipEffectSocketAnchor(dots, 3, 0).empty());
    EffectDefinition plain;
    plain.spriteEmitters.resize(2);
    CHECK(actorClipEffectSocketAnchor(plain, 2, 0).empty());
}
