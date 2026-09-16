#include "game/app/ProfilingControl.h"

#include <charconv>
#include <chrono>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <stdexcept>

#if defined(__linux__) && !defined(__ANDROID__)
#include <cerrno>
#include <fcntl.h>
#include <poll.h>
#include <unistd.h>
#endif

#if defined(__GNUC__) && !defined(__ANDROID__) && !defined(_WIN32)
extern "C" void __gmon_start__(void) __attribute__((weak));
extern "C" void moncontrol(int mode) __attribute__((weak));
#endif

namespace OpenYAMM::Game
{
namespace
{
#if defined(__linux__) && !defined(__ANDROID__)
class PerfControl
{
public:
    PerfControl()
    {
        const char *pControlPath = std::getenv("OPENYAMM_PERF_CONTROL_FIFO");
        if (pControlPath == nullptr)
        {
            return;
        }

        const char *pAckPath = std::getenv("OPENYAMM_PERF_ACK_FIFO");
        if (pAckPath == nullptr)
        {
            throw std::runtime_error("Perf control requires OPENYAMM_PERF_ACK_FIFO");
        }

        if (const char *pWarmup = std::getenv("OPENYAMM_PERF_WARMUP_MS"))
        {
            const char *pEnd = pWarmup + std::strlen(pWarmup);
            const std::from_chars_result result = std::from_chars(pWarmup, pEnd, m_warmupMilliseconds);
            if (result.ec != std::errc() || result.ptr != pEnd || m_warmupMilliseconds < 0)
            {
                throw std::runtime_error("Invalid OPENYAMM_PERF_WARMUP_MS");
            }
        }

        // O_RDWR keeps a closed recorder from delivering SIGPIPE to the game. The acknowledgement timeout
        // detects recorder failure instead. These descriptors must not leak to subprocesses.
        m_controlFd = open(pControlPath, O_RDWR | O_NONBLOCK | O_CLOEXEC);
        m_ackFd = open(pAckPath, O_RDONLY | O_NONBLOCK | O_CLOEXEC);
        if (m_controlFd < 0 || m_ackFd < 0)
        {
            closeDescriptors();
            throw std::runtime_error("Could not open perf control FIFOs");
        }

        std::cerr << "[Perf] waiting for loaded gameplay and " << m_warmupMilliseconds << " ms warmup\n";
    }

    ~PerfControl()
    {
        closeDescriptors();
    }

    void setGameplayReady(bool ready)
    {
        if (m_controlFd < 0)
        {
            return;
        }

        if (!ready)
        {
            m_gameplayReady = false;
            if (m_enabled)
            {
                sendCommand(false);
            }
            return;
        }

        if (m_enabled)
        {
            return;
        }

        const std::chrono::steady_clock::time_point now = std::chrono::steady_clock::now();
        if (!m_gameplayReady)
        {
            m_readySince = now;
            m_gameplayReady = true;
        }
        if (now - m_readySince >= std::chrono::milliseconds(m_warmupMilliseconds))
        {
            sendCommand(true);
        }
    }

private:
    void sendCommand(bool enabled)
    {
        const char *pCommand = enabled ? "enable\n" : "disable\n";
        const size_t length = std::strlen(pCommand);
        ssize_t written;
        do
        {
            written = write(m_controlFd, pCommand, length);
        }
        while (written < 0 && errno == EINTR);
        if (written < 0 || size_t(written) != length)
        {
            throw std::runtime_error("Failed to send perf collection command");
        }

        pollfd acknowledgement = {m_ackFd, POLLIN, 0};
        int pollResult;
        do
        {
            pollResult = poll(&acknowledgement, 1, 5000);
        }
        while (pollResult < 0 && errno == EINTR);

        // perf writes sizeof("ack\n"), including the terminating NUL.
        char response[sizeof("ack\n")] = {};
        if (pollResult <= 0 || (acknowledgement.revents & POLLIN) == 0
            || read(m_ackFd, response, sizeof(response)) != sizeof(response)
            || std::memcmp(response, "ack\n", sizeof(response)) != 0)
        {
            throw std::runtime_error("Perf recorder did not acknowledge collection command");
        }

        m_enabled = enabled;
        std::cerr << "[Perf] collection " << (enabled ? "enabled" : "disabled") << '\n';
    }

    void closeDescriptors()
    {
        if (m_controlFd >= 0)
        {
            close(m_controlFd);
        }
        if (m_ackFd >= 0)
        {
            close(m_ackFd);
        }
    }

    int m_controlFd = -1;
    int m_ackFd = -1;
    int m_warmupMilliseconds = 3000;
    bool m_gameplayReady = false;
    bool m_enabled = false;
    std::chrono::steady_clock::time_point m_readySince;
};
#endif

void setGprofProfilingEnabled(bool enabled)
{
#if defined(__GNUC__) && !defined(__ANDROID__) && !defined(_WIN32)
    static bool profilingEnabled = true;

    if (__gmon_start__ != nullptr && moncontrol != nullptr && profilingEnabled != enabled)
    {
        moncontrol(enabled ? 1 : 0);
        profilingEnabled = enabled;
        std::cerr << "[Gprof] collection " << (enabled ? "enabled" : "disabled") << '\n';
    }
#else
    (void)enabled;
#endif
}
}

void setGameplayProfilingEnabled(bool enabled)
{
    setGprofProfilingEnabled(enabled);
#if defined(__linux__) && !defined(__ANDROID__)
    static PerfControl perfControl;
    perfControl.setGameplayReady(enabled);
#endif
}

GprofProfilingScope::GprofProfilingScope()
{
    setGprofProfilingEnabled(true);
}

GprofProfilingScope::~GprofProfilingScope()
{
    setGprofProfilingEnabled(false);
}
}
