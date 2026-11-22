// The co-op lobby service as a program of its own (devdocs/plans/MULTIPLAYER_LISTEN_SERVER_ARCHITECTURE.md, "The lobby
// as built"): games that host register their session here, games that join ask for the list or name a session's
// code, and the service tells the two where each other is so that they open a path through their routers; where no
// path opens it relays between them. It runs wherever every game can reach it, and holds nothing of a game's state.
//   openyamm_lobby_server [--port 27910] [--relay-ports 16] [--quiet] [--relay-lan-with-internet]
#include "engine/net/RendezvousServer.h"

#include <csignal>
#include <cstdio>
#include <cstdlib>
#include <optional>
#include <string>

using namespace OpenYAMM::Engine;

namespace
{
volatile std::sig_atomic_t g_stop = 0;

void onSignal(int)
{
    g_stop = 1;
}

// A whole number from `low` to `high`, else nothing: a port typed wrong must not wrap around into another one.
std::optional<uint16_t> numberBetween(const char *pText, long low, long high)
{
    char *pEnd = nullptr;
    const long value = std::strtol(pText, &pEnd, 10);

    if (pEnd == pText || *pEnd != '\0' || value < low || value > high)
    {
        return std::nullopt;
    }

    return uint16_t(value);
}
}

int main(int argc, char **argv)
{
    RendezvousServerConfig config;
    config.verbose = true;

    for (int index = 1; index < argc; ++index)
    {
        const std::string argument = argv[index];
        const bool hasValue = index + 1 < argc;

        if (argument == "--port" && hasValue)
        {
            const std::optional<uint16_t> port = numberBetween(argv[++index], 1, 65535);

            if (!port)
            {
                std::fprintf(stderr, "--port takes a number from 1 to 65535\n");
                return 2;
            }

            config.port = *port;
        }
        else if (argument == "--relay-ports" && hasValue)
        {
            // The service waits on all its sockets at once, and the system's set for that has a fixed size.
            const long most = long(RendezvousServer::maxRelayPorts());
            const std::optional<uint16_t> count = numberBetween(argv[++index], 0, most);

            if (!count)
            {
                std::fprintf(stderr, "--relay-ports takes a number from 0 to %ld\n", most);
                return 2;
            }

            config.relayPortCount = *count;
        }
        else if (argument == "--quiet")
        {
            config.verbose = false;
        }
        else if (argument == "--relay-lan-with-internet")
        {
            // For a service that runs on its owner's home network: a game on that network is then relayed with
            // one on the internet. Off by default, so that the relay is no way from the internet into the network.
            config.relayBetweenLanAndInternet = true;
        }
        else
        {
            std::fprintf(stderr, "usage: openyamm_lobby_server [--port N] [--relay-ports N] [--quiet]"
                                 " [--relay-lan-with-internet]\n");
            return 2;
        }
    }

    if (config.port + config.relayPortCount > 65535)
    {
        std::fprintf(stderr, "port %u leaves no room for %u relay ports above it\n", config.port,
            config.relayPortCount);
        return 2;
    }

    RendezvousServer server;

    if (!server.start(config))
    {
        std::fprintf(stderr, "cannot bind UDP port %u and its %u relay ports\n", config.port, config.relayPortCount);
        return 1;
    }

    std::signal(SIGINT, onSignal);
    std::signal(SIGTERM, onSignal);
    std::printf("lobby on UDP %u, relay ports %u to %u\n", server.port(), server.port() + 1,
        server.port() + config.relayPortCount);
    std::fflush(stdout);

    // A line of numbers every ten minutes in which something happened, for the log.
    RendezvousServerStats told = server.stats();
    uint32_t sinceToldMs = 0;

    while (g_stop == 0)
    {
        server.service(250);
        sinceToldMs += 250;

        if (sinceToldMs >= 600000)
        {
            sinceToldMs = 0;
            const RendezvousServerStats now = server.stats();

            if (now.sessions != told.sessions || now.relayedBytes != told.relayedBytes
                || now.refusedRequests != told.refusedRequests)
            {
                std::printf("now: %zu sessions, %zu relay ports in use; in all %llu bytes relayed, %llu datagrams "
                            "dropped, %llu requests refused\n",
                    now.sessions, now.relaysInUse, static_cast<unsigned long long>(now.relayedBytes),
                    static_cast<unsigned long long>(now.droppedDatagrams),
                    static_cast<unsigned long long>(now.refusedRequests));
                told = now;
            }
        }

        std::fflush(stdout);
    }

    const RendezvousServerStats stats = server.stats();
    std::printf("stopped: %llu datagrams (%llu bytes) relayed, %llu dropped\n",
        static_cast<unsigned long long>(stats.relayedDatagrams), static_cast<unsigned long long>(stats.relayedBytes),
        static_cast<unsigned long long>(stats.droppedDatagrams));
    return 0;
}
