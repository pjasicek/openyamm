#pragma once

#include <cstdint>
#include <functional>
#include <memory>
#include <string>

namespace OpenYAMM::Engine
{
// Blocking HTTP(S) GET for the updater. Implementations are thread-safe; the downloader runs several at once.
class HttpTransport
{
public:
    using Sink = std::function<bool(const char *pData, size_t size)>;

    virtual ~HttpTransport() = default;

    // Requests url from byte offset onward (a Range request when offset > 0) and passes the body from that offset to
    // sink, which returns false to cancel; when a server ignores the range, the bytes before offset are skipped.
    // Returns the HTTP status (200 or 206), another status for an HTTP error, or 0 when the request failed or was
    // cancelled; error says why.
    virtual int get(const std::string &url, uint64_t offset, const Sink &sink, std::string &error) = 0;
};

// The platform's transport (WinHTTP on Windows, the system's libcurl on Linux); null where the game does not update
// itself.
std::unique_ptr<HttpTransport> createPlatformHttpTransport();
}
