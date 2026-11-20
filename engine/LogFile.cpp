#include "engine/LogFile.h"

#include <cstring>
#include <ctime>
#include <iostream>
#include <streambuf>

namespace OpenYAMM::Engine
{
class LogFile::TeeBuffer final : public std::streambuf
{
public:
    TeeBuffer(std::streambuf *pConsole, Sink &sink)
        : m_pConsole(pConsole)
        , m_sink(sink)
    {
    }

    std::streambuf *console() const
    {
        return m_pConsole;
    }

protected:
    int overflow(int character) override
    {
        if (traits_type::eq_int_type(character, traits_type::eof()))
        {
            return traits_type::not_eof(character);
        }

        const char value = traits_type::to_char_type(character);
        write(&value, 1);
        return character;
    }

    std::streamsize xsputn(const char *pText, std::streamsize count) override
    {
        write(pText, count);
        return count;
    }

    int sync() override
    {
        const std::lock_guard<std::mutex> lock(m_sink.mutex);

        if (m_pConsole != nullptr)
        {
            m_pConsole->pubsync();
        }

        m_sink.file.pubsync();
        return 0;
    }

private:
    void write(const char *pText, std::streamsize count)
    {
        const std::lock_guard<std::mutex> lock(m_sink.mutex);

        // A Windows release build has no console; its writes fail and only the file keeps the text.
        if (m_pConsole != nullptr)
        {
            m_pConsole->sputn(pText, count);
        }

        if (m_sink.file.is_open())
        {
            m_sink.file.sputn(pText, count);

            // Flushed line by line, so the file holds everything written before a crash.
            if (std::memchr(pText, '\n', size_t(count)) != nullptr)
            {
                m_sink.file.pubsync();
            }
        }
        else if (m_sink.holding)
        {
            m_sink.held.append(pText, size_t(count));
        }
    }

    std::streambuf *m_pConsole;
    Sink &m_sink;
};

LogFile::LogFile()
    : m_pOutputBuffer(std::make_unique<TeeBuffer>(std::cout.rdbuf(), m_sink))
    , m_pErrorBuffer(std::make_unique<TeeBuffer>(std::cerr.rdbuf(), m_sink))
{
    std::cout.rdbuf(m_pOutputBuffer.get());
    std::cerr.rdbuf(m_pErrorBuffer.get());
}

LogFile::~LogFile()
{
    std::cout.flush();
    std::cerr.flush();
    std::cout.rdbuf(m_pOutputBuffer->console());
    std::cerr.rdbuf(m_pErrorBuffer->console());
}

bool LogFile::open(const std::filesystem::path &path)
{
    const std::lock_guard<std::mutex> lock(m_sink.mutex);
    const bool opened = m_sink.file.open(path, std::ios::out | std::ios::trunc) != nullptr;

    if (opened)
    {
        const std::time_t now = std::time(nullptr);
        char startTime[32] = {};
        std::strftime(startTime, sizeof(startTime), "%Y-%m-%d %H:%M:%S", std::localtime(&now));

        const std::string startLine = std::string("OpenYAMM log started ") + startTime + '\n';
        m_sink.file.sputn(startLine.data(), std::streamsize(startLine.size()));
        m_sink.file.sputn(m_sink.held.data(), std::streamsize(m_sink.held.size()));
        m_sink.file.pubsync();
    }

    m_sink.held.clear();
    m_sink.held.shrink_to_fit();
    m_sink.holding = false;
    return opened;
}

void LogFile::discard()
{
    const std::lock_guard<std::mutex> lock(m_sink.mutex);
    m_sink.held.clear();
    m_sink.held.shrink_to_fit();
    m_sink.holding = false;
}
}
