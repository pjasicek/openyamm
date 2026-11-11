#include "doctest/doctest.h"

#include "engine/AssetFileSystem.h"
#include "engine/AssetScaleTier.h"
#include "engine/TextTable.h"
#include "engine/models/ModelAsset.h"
#include "game/audio/SoundCatalog.h"
#include "game/fx/ActorClipSounds.h"

#include <filesystem>
#include <stdexcept>
#include <string>
#include <vector>

namespace
{
using OpenYAMM::Game::ActorClipSoundCue;
using OpenYAMM::Game::ActorClipSoundState;

OpenYAMM::Engine::ModelAsset clipModel()
{
    OpenYAMM::Engine::ModelAsset asset;
    asset.clips.resize(3);
    asset.clips[0].name = "Walking";
    asset.clips[0].durationSeconds = 1.0f;
    asset.clips[1].name = "AttackMelee";
    asset.clips[1].durationSeconds = 1.2f;
    asset.clips[2].name = "Standing";
    asset.clips[2].durationSeconds = 2.0f;
    for (uint32_t clip = 0; clip < asset.clips.size(); ++clip)
    {
        asset.clipIndicesByName[asset.clips[clip].name] = clip;
    }
    return asset;
}

std::shared_ptr<const OpenYAMM::Game::ActorClipSounds> parse(const std::string &text)
{
    const OpenYAMM::Engine::ModelAsset asset = clipModel();
    return OpenYAMM::Game::parseActorClipSounds(YAML::Load(text), asset, "Test");
}

std::vector<std::string> advance(const OpenYAMM::Game::ActorClipSounds &sounds, ActorClipSoundState &state,
    uint32_t clip, float time, float duration, float delta)
{
    std::vector<ActorClipSoundCue> cues;
    state.clockSeconds += delta;
    OpenYAMM::Game::advanceActorClipSounds(sounds, state, 0, clip, time, duration, delta, cues);
    std::vector<std::string> names;
    for (const ActorClipSoundCue &cue : cues)
    {
        names.push_back(cue.sound + (cue.voice ? "!" : ""));
    }
    return names;
}

const char *NoblemanSounds = R"(
descriptor: Test
radius: 3686.4
footstep_radius: 896.0
footsteps: [steps/dirt1, steps/dirt2, steps/dirt3]
clips:
  Walking:
  - {at: 0.5, footstep: true}
  - {at: 1.0, footstep: true}
  AttackMelee:
  - {at: 0.333, sound: nobleman/hattack1, voice: true}
  - {at: 0.366, sound: nobleman/fx_hattack1}
  Standing:
  - {at: 0.2, sounds: [guard/stand1, guard/stand2], chance: 0.35, gate: 1.2, miss_gate: 50.0, radius: 2560.0,
     inner: 256.0}
)";
}

TEST_CASE("actor clip sounds play each event once as its clip passes it")
{
    const auto sounds = parse(NoblemanSounds);
    ActorClipSoundState state;

    // The attack starts: nothing before the grunt, then the grunt (a voice) and the swish in one long frame.
    CHECK(advance(*sounds, state, 1, 0.1f, 1.2f, 0.1f).empty());
    CHECK(advance(*sounds, state, 1, 0.34f, 1.2f, 0.24f) == std::vector<std::string>{"nobleman/hattack1!"});
    CHECK(advance(*sounds, state, 1, 0.5f, 1.2f, 0.16f) == std::vector<std::string>{"nobleman/fx_hattack1"});
    CHECK(advance(*sounds, state, 1, 1.0f, 1.2f, 0.5f).empty());
    // The attack restarts: its start plays again.
    CHECK(advance(*sounds, state, 1, 0.4f, 1.2f, 0.4f)
        == std::vector<std::string>{"nobleman/hattack1!", "nobleman/fx_hattack1"});
}

TEST_CASE("actor clip footsteps cycle through the step files across loops")
{
    const auto sounds = parse(NoblemanSounds);
    ActorClipSoundState state;

    CHECK(advance(*sounds, state, 0, 0.6f, 1.0f, 0.6f) == std::vector<std::string>{"steps/dirt1"});
    CHECK(advance(*sounds, state, 0, 0.99f, 1.0f, 0.39f).empty());
    // The loop wraps: the step at its end, then none until the next half.
    CHECK(advance(*sounds, state, 0, 0.1f, 1.0f, 0.11f) == std::vector<std::string>{"steps/dirt2"});
    CHECK(advance(*sounds, state, 0, 0.55f, 1.0f, 0.45f) == std::vector<std::string>{"steps/dirt3"});
    CHECK(advance(*sounds, state, 0, 1.0f, 1.0f, 0.45f) == std::vector<std::string>{"steps/dirt1"});

    // Another clip in between: entering the walk mid-stride plays only the frame's steps.
    CHECK(advance(*sounds, state, 2, 0.1f, 2.0f, 0.1f).empty());
    CHECK(advance(*sounds, state, 0, 0.7f, 1.0f, 0.1f).empty());
}

TEST_CASE("actor clip script sounds roll their chance and hold their gates")
{
    const auto sounds = parse(NoblemanSounds);
    ActorClipSoundState state;
    state.randomState = 12345u;
    size_t plays = 0;
    size_t passes = 0;
    for (int loop = 0; loop < 400; ++loop)
    {
        // Two seconds a loop: a miss holds the event 50 s (25 loops), a play 1.2 s (none).
        const std::vector<std::string> first = advance(*sounds, state, 2, 1.0f, 2.0f, 1.0f);
        const std::vector<std::string> second = advance(*sounds, state, 2, 1.99f, 2.0f, 0.99f);
        CHECK(second.empty());
        plays += first.size();
        passes += 1;
        advance(*sounds, state, 2, 0.01f, 2.0f, 0.02f);
    }
    CHECK(plays > 0);
    CHECK(plays < passes / 2);
}

TEST_CASE("actor clip sounds refuse a clip the model does not have or an event past its clip")
{
    CHECK_THROWS_AS(parse("radius: 10\nclips:\n  Running:\n  - {at: 0.1, sound: a}\n"), std::runtime_error);
    CHECK_THROWS_AS(parse("radius: 10\nclips:\n  Walking:\n  - {at: 1.5, sound: a}\n"), std::runtime_error);
    CHECK_THROWS_AS(parse("radius: 10\nclips:\n  Walking:\n  - {at: 0.5, footstep: true}\n"), std::runtime_error);
    CHECK_THROWS_AS(parse("radius: 10\nloud: true\nclips: {}\n"), std::runtime_error);
}

TEST_CASE("actor clip shakes cue alone or with a sound and refuse bad strengths")
{
    const std::shared_ptr<const OpenYAMM::Game::ActorClipSounds> sounds = parse(R"(
radius: 10
clips:
  Walking:
  - {at: 0.4, shake: {near: 0.333, edge: 0.083, seconds: 0.6, radius: 3072}}
  - {at: 0.4, sound: step}
)");
    ActorClipSoundState state;
    std::vector<ActorClipSoundCue> cues;
    OpenYAMM::Game::advanceActorClipSounds(*sounds, state, 0, 0, 0.0f, 1.0f, 0.0f, cues);
    OpenYAMM::Game::advanceActorClipSounds(*sounds, state, 0, 0, 0.5f, 1.0f, 0.5f, cues);
    REQUIRE(cues.size() == 2);
    CHECK(cues[0].sound.empty());
    CHECK(cues[0].shake.intensity == doctest::Approx(0.333f));
    CHECK(cues[0].shake.edgeIntensity == doctest::Approx(0.083f));
    CHECK(cues[0].shake.radius == doctest::Approx(3072.0f));
    CHECK(cues[1].sound == "step");
    CHECK(cues[1].shake.radius == 0.0f);
    CHECK_THROWS_AS(parse("radius: 10\nclips:\n  Walking:\n  - {at: 0.4, shake: {near: 0.1, edge: 0.2, seconds: 1, "
        "radius: 5}}\n"), std::runtime_error);
    CHECK_THROWS_AS(parse("radius: 10\nclips:\n  Walking:\n  - {at: 0.4, shake: {near: 0.1, seconds: 1}}\n"),
        std::runtime_error);
}

TEST_CASE("the MM9 world's monster sounds load into the world scope clear of the engine ids")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    OpenYAMM::Engine::AssetFileSystem assetFileSystem;
    REQUIRE(assetFileSystem.initialize(sourceRoot, sourceRoot / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1));
    if (!assetFileSystem.exists("worlds/mm9/data_tables/sounds.txt"))
    {
        return;
    }
    const std::optional<std::string> engineText = assetFileSystem.readTextFile("engine/data_tables/sounds.txt");
    REQUIRE(engineText.has_value());
    const std::optional<OpenYAMM::Engine::TextTable> engineTable =
        OpenYAMM::Engine::TextTable::parseTabSeparated(*engineText);
    REQUIRE(engineTable.has_value());
    std::vector<std::vector<std::string>> engineRows;
    for (size_t row = 0; row < engineTable->getRowCount(); ++row)
    {
        engineRows.push_back(engineTable->getRow(row));
    }

    std::vector<std::vector<std::string>> worldRows;
    std::string error;
    REQUIRE_MESSAGE(OpenYAMM::Game::loadWorldSoundRows(assetFileSystem, engineRows, worldRows, error), error);
    CHECK(worldRows.size() > 900);

    OpenYAMM::Game::SoundCatalog catalog;
    REQUIRE_MESSAGE(catalog.loadFromScopedRows(engineRows, worldRows, error), error);
    catalog.initializeVirtualPathIndex(assetFileSystem);
    for (const std::vector<std::string> &row : worldRows)
    {
        const uint32_t soundId = uint32_t(std::stoul(row[1]));
        CHECK(soundId >= 50000);
        CHECK(soundId <= 59999);
        const std::optional<std::string> path = catalog.buildVirtualPath(OpenYAMM::Game::worldSound(soundId));
        REQUIRE_MESSAGE(path.has_value(), row[0]);
        CHECK_MESSAGE(assetFileSystem.exists(*path), *path);
    }
    // The Count (Kluso) grunts with MM9's Nobleman attack, not MM6-MM8's 112noblemana_attack.
    const std::optional<std::string> grunt =
        catalog.buildVirtualPathByName(OpenYAMM::Game::SoundScope::World, "animsounds/nobleman/hattack1");
    REQUIRE(grunt.has_value());
    CHECK(assetFileSystem.exists(*grunt));
    // An engine id still resolves to the engine's sound in the world scope.
    const std::optional<std::string> engineSound = catalog.buildVirtualPath(OpenYAMM::Game::worldSound(2900));
    REQUIRE(engineSound.has_value());
    CHECK(engineSound->find("112noblemana_attack") != std::string::npos);
}
