#include "doctest/doctest.h"

#include "game/scenario/ScenarioYamlLoader.h"

#include <filesystem>
#include <fstream>
#include <string>

using namespace OpenYAMM::Game;

namespace
{
ScenarioLoadResult loadScenarioText(const std::string &text)
{
    const std::filesystem::path path = std::filesystem::temp_directory_path() / "openyamm-scenario-loader-test.yml";
    {
        std::ofstream output(path);
        output << "id: loader.test\nworld: mm8\nsteps:\n" << text;
    }
    ScenarioYamlLoader loader;
    ScenarioLoadResult result = loader.load(path);
    std::filesystem::remove(path);
    return result;
}

bool anyErrorContains(const ScenarioLoadResult &result, const std::string &text)
{
    for (const std::string &error : result.errors)
    {
        if (error.find(text) != std::string::npos)
        {
            return true;
        }
    }

    return false;
}
}

TEST_CASE("scenario loader accepts the keys the runner reads and recorded annotations")
{
    const ScenarioLoadResult result = loadScenarioText(
        "- new_game_flow: {start_map: d01.blv, continent_name: Jadame}\n"
        "- set_pose: {map: d01.blv, x: 1, y: 2, z: 3, yaw: 0, pitch: 0}\n"
        "- assert: {gold: 100, mechanism: {kind: indoor_door, id: 1, state: open}, scene_kind: indoor}\n"
        "- assert: {homing_ends: {source_monster_id: 10065, hit: party, min_count: 1}}\n"
        "- wait_until: {timeout_runtime_seconds: 2, assert: {mechanism: {id: 1, state: open}}}\n"
        "- setup_shortcut: {kind: set_qbit, id: 5, reason: a note}\n"
        "- press_action: {action: cancel_dialog, expect: {dialogue_canceled: {kind: house}}}\n"
        "- note: free text\n"
        "- trace_observation: {event: anything, fields: {whatever: 1}}\n");
    CHECK(result.errors.empty());
    CHECK(result.document.steps.size() == 9);
}

TEST_CASE("scenario loader rejects an unknown step, step key or assert key, naming the file, step and key")
{
    const ScenarioLoadResult unknownStep = loadScenarioText("- assert: {map: d01.blv}\n- teleport_party: {x: 1}\n");
    REQUIRE(unknownStep.errors.size() == 1);
    CHECK(anyErrorContains(unknownStep, "openyamm-scenario-loader-test.yml:5 step 2"));
    CHECK(anyErrorContains(unknownStep, "unknown scenario step 'teleport_party'"));

    const ScenarioLoadResult unknownAssert = loadScenarioText("- assert: {homing_endz: {hit: party}}\n");
    REQUIRE(unknownAssert.errors.size() == 1);
    CHECK(anyErrorContains(unknownAssert, "step 1 (assert)"));
    CHECK(anyErrorContains(unknownAssert, "unknown assert key 'homing_endz'"));

    const ScenarioLoadResult unknownNested =
        loadScenarioText("- assert: {projectiles: {min_count: 1, homing_ends: 2}}\n");
    REQUIRE(unknownNested.errors.size() == 1);
    CHECK(anyErrorContains(unknownNested, "unknown assert projectiles key 'homing_ends'"));

    const ScenarioLoadResult unknownStepKey = loadScenarioText("- spawn_actor: {monster_id: 1, x: 0, y: 0, z: 0, "
        "hostile: true}\n");
    REQUIRE(unknownStepKey.errors.size() == 1);
    CHECK(anyErrorContains(unknownStepKey, "unknown spawn_actor key 'hostile'"));

    const ScenarioLoadResult unknownWaitAssert =
        loadScenarioText("- wait_until: {seconds: 1, assert: {qbit_set: [5]}}\n");
    REQUIRE(unknownWaitAssert.errors.size() == 1);
    CHECK(anyErrorContains(unknownWaitAssert, "unknown wait_until assert key 'qbit_set'"));
}
