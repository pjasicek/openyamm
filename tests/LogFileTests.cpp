#include "engine/LogFile.h"

#include <doctest/doctest.h>

#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <sstream>
#include <string>

namespace
{
std::filesystem::path makeTemporaryLogPath()
{
    const uint64_t tickCount = static_cast<uint64_t>(
        std::chrono::steady_clock::now().time_since_epoch().count());
    return std::filesystem::temp_directory_path() / ("openyamm_log_" + std::to_string(tickCount) + ".log");
}

std::string readTextFile(const std::filesystem::path &path)
{
    std::ifstream file(path);
    return std::string(std::istreambuf_iterator<char>(file), std::istreambuf_iterator<char>());
}

// Points std::cout and std::cerr at string buffers for the test's lifetime.
class ConsoleCapture
{
public:
    ConsoleCapture()
        : m_pOutput(std::cout.rdbuf(m_output.rdbuf()))
        , m_pError(std::cerr.rdbuf(m_error.rdbuf()))
    {
    }

    ~ConsoleCapture()
    {
        std::cout.rdbuf(m_pOutput);
        std::cerr.rdbuf(m_pError);
    }

    std::ostringstream m_output;
    std::ostringstream m_error;

private:
    std::streambuf *m_pOutput;
    std::streambuf *m_pError;
};
}

TEST_CASE("log file keeps console output and the output written before it opened")
{
    const std::filesystem::path logPath = makeTemporaryLogPath();
    ConsoleCapture console;
    std::streambuf *pCapturedOutput = std::cout.rdbuf();

    {
        OpenYAMM::Engine::LogFile logFile;
        std::cout << "before open\n";
        REQUIRE(logFile.open(logPath));
        std::cerr << "error after open\n";
        std::cout << "output after open\n";

        const std::string contents = readTextFile(logPath);
        CHECK(contents.rfind("OpenYAMM log started ", 0) == 0);
        CHECK(contents.find("before open\nerror after open\noutput after open\n") != std::string::npos);
    }

    CHECK(std::cout.rdbuf() == pCapturedOutput);
    CHECK(console.m_output.str() == "before open\noutput after open\n");
    CHECK(console.m_error.str() == "error after open\n");

    std::error_code error;
    std::filesystem::remove(logPath, error);
}

TEST_CASE("discarded log file still writes to the console")
{
    ConsoleCapture console;

    {
        OpenYAMM::Engine::LogFile logFile;
        std::cout << "held\n";
        logFile.discard();
        std::cout << "console only\n";
    }

    CHECK(console.m_output.str() == "held\nconsole only\n");
}
