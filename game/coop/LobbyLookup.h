#pragma once

#include "engine/net/NetAddress.h"

#include <memory>
#include <mutex>
#include <optional>
#include <string>
#include <thread>

namespace OpenYAMM::Game
{
// Finds a lobby server's address from what names it ("host" or "host:port"), beside the game: looking a name up
// can take seconds, or as long again to fail without a network, and that must not hold a frame. An address written
// in numbers needs no looking up and is known at once.
class LobbyLookup
{
public:
    // Starts over with `text`; `defaultPort` is the port when the text names none. A lookup still under way is left
    // to end by itself.
    void start(const std::string &text, uint16_t defaultPort)
    {
        m_text = text;
        m_doneTaken = false;
        m_pShared = std::make_shared<Shared>();
        const std::string withPort = text.find(':') == std::string::npos ? text + ":" + std::to_string(defaultPort)
                                                                         : text;

        if (text.find_first_not_of("0123456789.:") == std::string::npos)
        {
            m_pShared->address = Engine::parseNetAddress(withPort);
            m_pShared->done = true;
            return;
        }

        std::thread([pShared = m_pShared, withPort]()
            {
                const std::optional<Engine::NetAddress> address = Engine::parseNetAddress(withPort);
                const std::lock_guard<std::mutex> lock(pShared->mutex);
                pShared->address = address;
                pShared->done = true;
            }).detach();
    }

    const std::string &text() const
    {
        return m_text;
    }

    bool pending() const
    {
        return m_pShared != nullptr && !done();
    }

    // Looked up and not found.
    bool failed() const
    {
        return m_pShared != nullptr && done() && !address();
    }

    std::optional<Engine::NetAddress> address() const
    {
        if (m_pShared == nullptr)
        {
            return std::nullopt;
        }

        const std::lock_guard<std::mutex> lock(m_pShared->mutex);
        return m_pShared->done ? m_pShared->address : std::nullopt;
    }

    // True once, when the lookup has ended (found or not).
    bool takeDone()
    {
        if (m_pShared == nullptr || m_doneTaken || !done())
        {
            return false;
        }

        m_doneTaken = true;
        return true;
    }

private:
    struct Shared
    {
        std::mutex mutex;
        bool done = false;
        std::optional<Engine::NetAddress> address;
    };

    bool done() const
    {
        const std::lock_guard<std::mutex> lock(m_pShared->mutex);
        return m_pShared->done;
    }

    std::shared_ptr<Shared> m_pShared;
    std::string m_text;
    bool m_doneTaken = true;
};
}
