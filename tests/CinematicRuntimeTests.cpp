#include <doctest/doctest.h>

#include "game/events/EventRuntime.h"
#include "game/gameplay/CinematicRuntime.h"

#include <algorithm>
#include <cmath>
#include <map>
#include <string>
#include <vector>

using namespace OpenYAMM::Game;

namespace
{
constexpr float Pi = 3.14159265f;

class FakeCinematicWorld : public ICinematicWorld
{
public:
    std::optional<GameplayWorldPoint> actorFeet(size_t actorIndex) const override
    {
        const auto found = actors.find(actorIndex);
        return found != actors.end() ? std::optional<GameplayWorldPoint>(found->second) : std::nullopt;
    }

    float actorHeight(size_t actorIndex) const override
    {
        return actors.contains(actorIndex) ? 100.0f : 0.0f;
    }

    GameplayWorldPoint partyEye() const override
    {
        return party;
    }

    void runEvent(uint16_t eventId) override
    {
        events.push_back(eventId);
    }

    void playSound(const std::string &soundName) override
    {
        sounds.push_back(soundName);
    }

    void setActorHidden(size_t actorIndex, bool hidden) override
    {
        hiddenActors[actorIndex] = hidden;
    }

    void placeActor(size_t actorIndex, const GameplayWorldPoint &feet) override
    {
        actors[actorIndex] = feet;
    }

    void faceActor(size_t actorIndex, float yawRadians, float seconds) override
    {
        faces[actorIndex] = {yawRadians, seconds};
    }

    void playActorClip(size_t actorIndex, const std::string &clip, bool loop) override
    {
        clips[actorIndex] = {clip, loop};
    }

    void clearActorPresentation(size_t actorIndex) override
    {
        faces.erase(actorIndex);
        clips.erase(actorIndex);
        cleared.push_back(actorIndex);
    }

    void moveDecoration(uint32_t decorationKey, const GameplayWorldPoint &offset, float seconds) override
    {
        decorations[decorationKey] = {offset, seconds};
    }

    std::map<size_t, GameplayWorldPoint> actors;
    std::map<size_t, bool> hiddenActors;
    GameplayWorldPoint party = {0.0f, 0.0f, 100.0f};
    std::vector<uint16_t> events;
    std::vector<std::string> sounds;
    std::map<size_t, std::pair<float, float>> faces;
    std::map<size_t, std::pair<std::string, bool>> clips;
    std::vector<size_t> cleared;
    std::map<uint32_t, std::pair<GameplayWorldPoint, float>> decorations;
};

std::string file(const std::string &body)
{
    return "format_version: 1\nkind: openyamm_cinematics\ncinematics:\n" + body;
}

CinematicLibrary parse(const std::string &body)
{
    std::string error;
    const std::optional<CinematicLibrary> library = parseCinematicLibrary(file(body), error);
    INFO(error);
    REQUIRE(library.has_value());
    return *library;
}

std::string parseError(const std::string &body)
{
    std::string error;
    CHECK_FALSE(parseCinematicLibrary(file(body), error).has_value());
    return error;
}

// Two shots (a fixed camera looking at a point, then a camera moving east and turning from east to north) and cues.
const char *const TwoShots = R"(  intro:
    shots:
      - duration: 2
        position: [0, 0, 100]
        look_at: [100, 0, 100]
        fov: 50
      - duration: 4
        easing: linear
        keys:
          - {at: 0, position: [0, 0, 100], direction: [1, 0, 0]}
          - {at: 4, position: [400, 0, 100], direction: [0, 1, 0]}
    cues:
      - {at: 0, fade: in, seconds: 1}
      - {at: 1, event: 501}
      - {at: 1, sound: "sounds\\spells\\ebolt01.wav"}
      - {at: 3, actor: 7, action: move, to: [200, 0, 0], seconds: 2}
      - {at: 5, fade: out, seconds: 1}
      - {at: 6, event: 502}
)";
}

TEST_CASE("Cinematic files parse with their durations and implicit letterbox")
{
    const CinematicLibrary library = parse(TwoShots);
    const CinematicDefinition *pIntro = library.find("intro");
    REQUIRE(pIntro != nullptr);
    CHECK(pIntro->skippable);
    CHECK(pIntro->shots.size() == 2);
    CHECK(pIntro->durationSeconds == doctest::Approx(6.0f));
    // Six cues plus the letterbox in at the start and out half a second before the end.
    REQUIRE(pIntro->cues.size() == 8);
    CHECK(pIntro->cues.front().kind == CinematicCueKind::FadeIn);
    CHECK(pIntro->cues.back().kind == CinematicCueKind::Event);
    bool letterboxOut = false;

    for (const CinematicCue &cue : pIntro->cues)
    {
        letterboxOut = letterboxOut
            || (cue.kind == CinematicCueKind::Letterbox && cue.amount == 0.0f && cue.atSeconds == 5.5f);
    }

    CHECK(letterboxOut);
    CHECK(pIntro->shots[0].keys[0].verticalFovDegrees == doctest::Approx(50.0f));
    CHECK(library.find("missing") == nullptr);
}

TEST_CASE("Cinematic files reject unknown keys, bad aims and bad timing")
{
    CHECK(parseError("  a:\n    shots:\n      - {duration: 1, position: [0, 0, 0], look_at: [1, 0, 0], zoom: 2}\n")
        .find("unknown key 'zoom'") != std::string::npos);
    CHECK(parseError("  a:\n    shots:\n      - {duration: 1, position: [0, 0, 0]}\n").find("exactly one aim")
        != std::string::npos);
    CHECK(parseError("  a:\n    shots:\n      - {duration: 1, position: [0, 0, 0], look_at: [1, 0, 0], "
        "look_at_party: true}\n").find("exactly one aim") != std::string::npos);
    CHECK(parseError("  a:\n    shots:\n      - duration: 2\n        keys:\n"
        "          - {at: 0, position: [0, 0, 0], yaw: 0, pitch: 0}\n"
        "          - {at: 0, position: [1, 0, 0], yaw: 0, pitch: 0}\n").find("increasing time") != std::string::npos);
    CHECK(parseError("  a:\n    shots:\n      - duration: 2\n        keys:\n"
        "          - {at: 0, position: [0, 0, 0], yaw: 0, pitch: 0}\n"
        "          - {at: 3, position: [1, 0, 0], yaw: 0, pitch: 0}\n").find("at") != std::string::npos);
    CHECK(parseError("  a:\n    cues:\n      - {at: 0, event: 0}\n").find("event") != std::string::npos);
    CHECK(parseError("  a:\n    cues:\n      - {at: 0, event: 5, sound: x}\n").find("exactly one of")
        != std::string::npos);
    CHECK(parseError("  a:\n    cues:\n      - {at: 0, actor: 3, action: move, to: [0, 0, 0]}\n")
        .find("needs seconds") != std::string::npos);
    CHECK(parseError("  a:\n    cues:\n      - {at: 0, subtitle: Hello}\n").find("needs seconds")
        != std::string::npos);
    CHECK(parseError("  a: {}\n").find("needs shots or cues") != std::string::npos);

    std::string error;
    CHECK_FALSE(parseCinematicLibrary("format_version: 2\nkind: openyamm_cinematics\ncinematics: {}\n", error));
    CHECK_FALSE(parseCinematicLibrary("format_version: 1\nkind: something\ncinematics: {}\n", error));
}

TEST_CASE("A cinematic moves its camera, runs its cues in time and ends one update after its end")
{
    const CinematicLibrary library = parse(TwoShots);
    FakeCinematicWorld world;
    world.actors[7] = {0.0f, 0.0f, 0.0f};
    CinematicRuntime runtime;
    runtime.start(*library.find("intro"), 900, world);
    REQUIRE(runtime.active());
    CHECK(runtime.fadeAmount() == doctest::Approx(1.0f));
    REQUIRE(runtime.cameraView().has_value());
    CHECK(runtime.cameraView()->yawRadians == doctest::Approx(0.0f));
    CHECK(runtime.cameraView()->pitchRadians == doctest::Approx(0.0f));
    CHECK(runtime.cameraView()->verticalFovDegrees.value_or(0.0f) == doctest::Approx(50.0f));
    CHECK(*runtime.activeShotIndex() == 0);

    runtime.update(0.5f, world);
    CHECK(runtime.fadeAmount() == doctest::Approx(0.5f));
    CHECK(runtime.letterboxAmount() == doctest::Approx(1.0f));
    CHECK(world.events.empty());

    runtime.update(0.5f, world);
    CHECK(world.events == std::vector<uint16_t>{501});
    CHECK(world.sounds.size() == 1);

    // Halfway through the moving shot: halfway along and halfway turned (45 degrees).
    runtime.update(3.0f, world);
    REQUIRE(runtime.cameraView().has_value());
    CHECK(*runtime.activeShotIndex() == 1);
    CHECK(runtime.cameraView()->eye.x == doctest::Approx(200.0f));
    CHECK(runtime.cameraView()->yawRadians == doctest::Approx(Pi / 4.0f));
    CHECK_FALSE(runtime.cameraView()->verticalFovDegrees.has_value());
    // The actor's two-second move began at 3 s: halfway at 4 s.
    CHECK(world.actors[7].x == doctest::Approx(100.0f));

    runtime.update(1.5f, world);
    CHECK(world.actors[7].x == doctest::Approx(200.0f));
    CHECK(runtime.fadeAmount() == doctest::Approx(0.5f));

    runtime.update(0.5f, world);
    CHECK(world.events == std::vector<uint16_t>{501, 502});
    // The end frame still draws the cinematic; the next update finishes it and runs its done event.
    CHECK(runtime.active());
    CHECK(runtime.fadeAmount() == doctest::Approx(1.0f));
    runtime.update(0.016f, world);
    CHECK_FALSE(runtime.active());
    CHECK_FALSE(runtime.cameraView().has_value());
    CHECK(world.events == std::vector<uint16_t>{501, 502, 900});
}

TEST_CASE("Skipping a cinematic runs its remaining events and places its actors, but drops its presentation")
{
    const CinematicLibrary library = parse(TwoShots);
    FakeCinematicWorld world;
    world.actors[7] = {0.0f, 0.0f, 0.0f};
    CinematicRuntime runtime;
    runtime.start(*library.find("intro"), 900, world);
    runtime.update(0.5f, world);
    REQUIRE(runtime.skip(world));
    CHECK(world.events == std::vector<uint16_t>{501, 502});
    CHECK(world.sounds.empty());
    CHECK(world.actors[7].x == doctest::Approx(200.0f));
    CHECK(runtime.active());
    runtime.update(0.016f, world);
    CHECK_FALSE(runtime.active());
    CHECK(world.events == std::vector<uint16_t>{501, 502, 900});

    // Unskippable: only a forced skip ends it (evt.SkipCinematic).
    const CinematicLibrary locked = parse("  locked:\n    skippable: false\n    letterbox: false\n"
        "    shots:\n      - {duration: 3, position: [0, 0, 0], look_at_party: true}\n");
    runtime.start(*locked.find("locked"), 0, world);
    CHECK_FALSE(runtime.skippable());
    CHECK_FALSE(runtime.skip(world));
    CHECK(runtime.skip(world, true));
    runtime.update(0.0f, world);
    CHECK_FALSE(runtime.active());
}

TEST_CASE("A cinematic camera follows the actor it looks at, and actor cues show, hide and place")
{
    const CinematicLibrary library = parse("  follow:\n    letterbox: false\n    shots:\n"
        "      - {duration: 2, position: [0, 0, 75], look_at_actor: 3}\n    cues:\n"
        "      - {at: 0, actor: 3, action: show}\n      - {at: 0.5, actor: 4, action: hide}\n"
        "      - {at: 1, actor: 3, action: place, to: [0, 100, 0]}\n");
    FakeCinematicWorld world;
    world.actors[3] = {100.0f, 0.0f, 0.0f};
    CinematicRuntime runtime;
    runtime.start(*library.find("follow"), 0, world);
    CHECK(world.hiddenActors[3] == false);
    // Its aim is three quarters up its 100-unit body: level with the camera.
    CHECK(runtime.cameraView()->yawRadians == doctest::Approx(0.0f));
    CHECK(runtime.cameraView()->pitchRadians == doctest::Approx(0.0f));
    runtime.update(1.0f, world);
    CHECK(world.hiddenActors[4] == true);
    CHECK(runtime.cameraView()->yawRadians == doctest::Approx(Pi / 2.0f));
    runtime.update(1.0f, world);
    runtime.update(0.0f, world);
    CHECK_FALSE(runtime.active());
}

TEST_CASE("Camera shake trembles and fades out over its seconds")
{
    CameraShake shake;
    shake.start(1.0f, 2.0f);
    CHECK(shake.active());
    float strongest = 0.0f;

    for (int step = 0; step < 30; ++step)
    {
        shake.update(1.0f / 60.0f);
        strongest = std::max(strongest, std::abs(shake.yawRadians()));
    }

    CHECK(strongest > 0.005f);
    CHECK(strongest < 0.02f);
    for (int step = 0; step < 60; ++step)
    {
        shake.update(1.0f / 60.0f);
    }

    // The last quarter of its two seconds: at most a sixteenth of its first strength.
    float late = 0.0f;

    for (int step = 0; step < 20; ++step)
    {
        shake.update(1.0f / 60.0f);
        late = std::max(late, std::abs(shake.yawRadians()));
    }

    CHECK(late < strongest * 0.3f);
    shake.update(1.0f);
    CHECK_FALSE(shake.active());
    CHECK(shake.yawRadians() == 0.0f);
    shake.start(0.0f, 1.0f);
    CHECK_FALSE(shake.active());
}

TEST_CASE("Cinematic actors face and play clips until it ends, and decorations glide (at once on a skip)")
{
    const CinematicLibrary library = parse("  scene:\n    letterbox: false\n    shots:\n"
        "      - {duration: 4, position: [0, 0, 75], look_at_party: true}\n    cues:\n"
        "      - {at: 0, actor: 3, action: face, look_at_actor: 4, seconds: 1}\n"
        "      - {at: 0, actor: 4, action: face, look_at_party: true}\n"
        "      - {at: 1, actor: 3, action: clip, clip: Applause, loop: true}\n"
        "      - {at: 1, decoration: 493, offset: [0, 0, -2560], seconds: 20}\n"
        "      - {at: 3, decoration: 77, offset: [100, 0, 0]}\n");
    const CinematicDefinition *pScene = library.find("scene");
    REQUIRE(pScene != nullptr);
    // A decoration's glide goes on by itself: it does not lengthen the cinematic.
    CHECK(pScene->durationSeconds == doctest::Approx(4.0f));
    FakeCinematicWorld world;
    world.actors[3] = {0.0f, 0.0f, 0.0f};
    world.actors[4] = {0.0f, 100.0f, 0.0f};
    world.party = {-100.0f, 100.0f, 150.0f};
    CinematicRuntime runtime;
    runtime.start(*pScene, 0, world);
    CHECK(world.faces[3].first == doctest::Approx(Pi / 2.0f));
    CHECK(world.faces[3].second == doctest::Approx(1.0f));
    CHECK(world.faces[4].first == doctest::Approx(Pi));
    runtime.update(1.0f, world);
    CHECK(world.clips[3] == std::pair<std::string, bool>{"Applause", true});
    CHECK(world.decorations[493].second == doctest::Approx(20.0f));
    REQUIRE(runtime.skip(world));
    // Both glides at their ends at once, the one to come included.
    CHECK(world.decorations[493].first.z == doctest::Approx(-2560.0f));
    CHECK(world.decorations[493].second == 0.0f);
    CHECK(world.decorations[77].first.x == doctest::Approx(100.0f));
    runtime.update(0.0f, world);
    CHECK_FALSE(runtime.active());
    CHECK(world.faces.empty());
    CHECK(world.clips.empty());
    CHECK(world.cleared.size() == 2);

    CHECK(parseError("  a:\n    cues:\n      - {at: 0, actor: 1, action: clip}\n").find("needs clip")
        != std::string::npos);
    CHECK(parseError("  a:\n    cues:\n      - {at: 0, actor: 1, action: face}\n").find("exactly one of")
        != std::string::npos);
    CHECK(parseError("  a:\n    cues:\n      - {at: 0, actor: 1, action: hide, loop: true}\n")
        .find("actor clip cue") != std::string::npos);
    CHECK(parseError("  a:\n    cues:\n      - {at: 0, decoration: 5}\n").find("needs offset") != std::string::npos);
    CHECK(parseError("  a:\n    cues:\n      - {at: 0, event: 5, clip: x}\n").find("does not belong")
        != std::string::npos);
}

TEST_CASE("Actor presentations turn and play over the actor's own state")
{
    EventRuntimeState events;
    EventRuntimeState::ActorPresentation &presentation = events.actorPresentations[2];
    presentation.clip = "conv";
    presentation.yawFromRadians = 0.0f;
    presentation.yawToRadians = Pi / 2.0f;
    presentation.turnSeconds = 1.0f;
    presentation.yawRadians = 0.0f;
    advanceActorPresentations(events, 0.5f);
    GameplayRuntimeActorState state = {};
    state.yawRadians = 3.0f;
    applyActorPresentation(&events, 2, state);
    CHECK(state.scriptedClip == "conv");
    CHECK(state.scriptedClipSeconds == doctest::Approx(0.5f));
    CHECK(state.scriptedClipEnd == GameplayRuntimeActorState::ScriptedClipEnd::Release);
    CHECK(state.yawRadians == doctest::Approx(Pi / 4.0f));
    GameplayRuntimeActorState other = {};
    applyActorPresentation(&events, 5, other);
    CHECK(other.scriptedClip.empty());

    // A clip sequence (evt.PlayActorClip with a list: a posed MM9 prop's moment ending in a held pose) reaches the
    // model presentation whole; the loop applies to its last clip.
    EventRuntimeState::ActorPresentation &sequence = events.actorPresentations[4];
    sequence.clip = "ercc01a";
    sequence.then = {"ercc01b", "ercc02"};
    sequence.loop = true;
    GameplayRuntimeActorState posed = {};
    applyActorPresentation(&events, 4, posed);
    CHECK(posed.scriptedClip == "ercc01a");
    CHECK(posed.scriptedClipThen == std::vector<std::string>{"ercc01b", "ercc02"});
    CHECK(posed.scriptedClipEnd == GameplayRuntimeActorState::ScriptedClipEnd::Loop);

    moveDecoration(events, 9, {0.0f, 0.0f, -100.0f}, 2.0f);
    advanceDecorationAims(events, 1.0f);
    CHECK(events.decorationAims[9].offset[2] == doctest::Approx(-50.0f));
    advanceDecorationAims(events, 5.0f);
    CHECK(events.decorationAims[9].offset[2] == doctest::Approx(-100.0f));
}

TEST_CASE("Ambient cinematics keep the view, and a key may sit at its shot's end")
{
    const CinematicLibrary library = parse("  talk:\n    ambient: true\n    cues:\n"
        "      - {at: 0, sound: \"voices\\\\cinema\\\\bobanddoug\\\\01.wav\"}\n"
        "      - {at: 0, subtitle: Hello, seconds: 2}\n"
        "  pan:\n    shots:\n      - duration: 16.3\n        keys:\n"
        "          - {at: 0, position: [0, 0, 0], yaw: 0, pitch: 0}\n"
        "          - {at: 16.3, position: [1, 0, 0], yaw: 10, pitch: 0}\n");
    const CinematicDefinition *pTalk = library.find("talk");
    REQUIRE(pTalk != nullptr);
    CHECK(pTalk->ambient);
    CHECK_FALSE(pTalk->letterbox);
    FakeCinematicWorld world;
    CinematicRuntime runtime;
    runtime.start(*pTalk, 0, world);
    CHECK(runtime.active());
    CHECK_FALSE(runtime.takesOverView());
    CHECK_FALSE(runtime.cameraView().has_value());
    CHECK(runtime.subtitle() == "Hello");
    CHECK(library.find("pan") != nullptr);
    CHECK(parseError("  a:\n    ambient: true\n    shots:\n      - {duration: 1, position: [0, 0, 0], look_at_party: true}\n")
        .find("ambient") != std::string::npos);
    CHECK(parseError("  a:\n    ambient: true\n    cues:\n      - {at: 0, fade: in}\n").find("no fades")
        != std::string::npos);
}
