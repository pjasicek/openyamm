#include "tests/RegressionMapLoader.h"

#include "engine/AssetScaleTier.h"

#include <doctest/doctest.h>

#include <cstring>
#include <filesystem>
#include <memory>
#include <string>

namespace OpenYAMM::Tests
{
namespace
{
struct RegressionMapLoaderState
{
    bool loaded = false;
    RegressionMapLoader loader = {};
    std::string failure;
};

bool loadRegressionMapLoader(RegressionMapLoader &loader, std::string &failure)
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::filesystem::path assetsRoot = sourceRoot / "assets_dev";

    if (!loader.assetFileSystem.initialize(sourceRoot, assetsRoot, Engine::AssetScaleTier::X1))
    {
        failure = "could not initialize asset file system for regression map tests";
        return false;
    }

    if (!loader.gameDataLoader.loadForHeadlessGameplay(loader.assetFileSystem))
    {
        failure = "could not load gameplay data for regression map tests";
        return false;
    }

    return true;
}

std::unique_ptr<RegressionMapLoaderState> &sharedState()
{
    static std::unique_ptr<RegressionMapLoaderState> state;
    return state;
}

const RegressionMapLoaderState &regressionMapLoaderState()
{
    std::unique_ptr<RegressionMapLoaderState> &state = sharedState();
    if (state == nullptr)
    {
        state = std::make_unique<RegressionMapLoaderState>();
        state->loaded = loadRegressionMapLoader(state->loader, state->failure);
    }

    return *state;
}

// Releases the shared loader before each test outside SharedRegressionMapSuite, and at the end of the run.
class SharedRegressionMapListener : public doctest::IReporter
{
public:
    explicit SharedRegressionMapListener(const doctest::ContextOptions &)
    {
    }

    void report_query(const doctest::QueryData &) override
    {
    }
    void test_run_start() override
    {
    }
    void test_run_end(const doctest::TestRunStats &) override
    {
        releaseRegressionMapLoader();
    }
    void test_case_start(const doctest::TestCaseData &testCase) override
    {
        if (testCase.m_test_suite == nullptr || std::strcmp(testCase.m_test_suite, SharedRegressionMapSuite) != 0)
        {
            releaseRegressionMapLoader();
        }
    }
    void test_case_reenter(const doctest::TestCaseData &) override
    {
    }
    void test_case_end(const doctest::CurrentTestCaseStats &) override
    {
    }
    void test_case_exception(const doctest::TestCaseException &) override
    {
    }
    void subcase_start(const doctest::SubcaseSignature &) override
    {
    }
    void subcase_end() override
    {
    }
    void log_assert(const doctest::AssertData &) override
    {
    }
    void log_message(const doctest::MessageData &) override
    {
    }
    void test_case_skipped(const doctest::TestCaseData &) override
    {
    }
};

REGISTER_LISTENER("shared_regression_map", 1, SharedRegressionMapListener);
}

bool regressionMapLoaderLoaded()
{
    return regressionMapLoaderState().loaded;
}

const std::string &regressionMapLoaderFailure()
{
    return regressionMapLoaderState().failure;
}

const RegressionMapLoader &regressionMapLoader()
{
    return regressionMapLoaderState().loader;
}

void releaseRegressionMapLoader()
{
    sharedState().reset();
}
}
