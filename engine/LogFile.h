#pragma once

#include <filesystem>
#include <fstream>
#include <memory>
#include <mutex>
#include <string>

namespace OpenYAMM::Engine
{
// Copies everything written to std::cout and std::cerr into a log file, so a player can report a failed start or a
// crash where no console shows them (Windows release builds, Android, desktop launchers). Output written before open()
// is held in memory and goes into the file when it opens. The streams are restored on destruction.
class LogFile
{
public:
    LogFile();
    ~LogFile();

    LogFile(const LogFile &) = delete;
    LogFile &operator=(const LogFile &) = delete;

    // Truncates the file, then writes a start line and the held output. Returns false when the file cannot be created.
    bool open(const std::filesystem::path &path);
    // Drops the held output and stops holding more, for runs that keep no log file.
    void discard();

private:
    struct Sink
    {
        std::mutex mutex;
        std::filebuf file;
        std::string held;
        bool holding = true;
    };

    class TeeBuffer;

    Sink m_sink;
    std::unique_ptr<TeeBuffer> m_pOutputBuffer;
    std::unique_ptr<TeeBuffer> m_pErrorBuffer;
};
}
