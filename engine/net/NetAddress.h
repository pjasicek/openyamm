#pragma once

#include <cstdint>
#include <optional>
#include <string>

namespace OpenYAMM::Engine
{
// An IPv4 address and UDP port. The host is kept as ENet keeps it, in network byte order; the port in host order.
struct NetAddress
{
    uint32_t host = 0;
    uint16_t port = 0;

    bool operator==(const NetAddress &) const = default;

    bool valid() const
    {
        return host != 0 && port != 0;
    }
};

std::string toString(const NetAddress &address);

// The network library's start and stop, counted, so that every user may hold one.
class NetLibrary
{
public:
    NetLibrary();
    ~NetLibrary();

    NetLibrary(const NetLibrary &) = delete;
    NetLibrary &operator=(const NetLibrary &) = delete;
};

// Milliseconds on the network library's clock.
uint32_t netNowMilliseconds();
// The address this machine uses towards `remote` (its LAN address for a server on the internet), port 0.
NetAddress localAddressTowards(const NetAddress &remote);

// "host:port"; the host may be a name. None when it does not resolve or the port is missing.
std::optional<NetAddress> parseNetAddress(const std::string &text);
}
