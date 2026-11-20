#include "engine/update/HttpTransport.h"

#if defined(_WIN32)
#include <windows.h>
#include <winhttp.h>

#include <algorithm>
#include <vector>
#elif (defined(__linux__) && !defined(__ANDROID__)) || (defined(__APPLE__) && !defined(OPENYAMM_IOS))
#include <dlfcn.h>

#include <algorithm>
#include <array>
#endif

namespace OpenYAMM::Engine
{
#if defined(_WIN32)
namespace
{
std::wstring widened(const std::string &text)
{
    if (text.empty())
    {
        return {};
    }

    const int length = MultiByteToWideChar(CP_UTF8, 0, text.data(), int(text.size()), nullptr, 0);
    std::wstring wide(size_t(length), L'\0');
    MultiByteToWideChar(CP_UTF8, 0, text.data(), int(text.size()), wide.data(), length);
    return wide;
}

std::string lastErrorText(const char *pWhat)
{
    return std::string(pWhat) + " failed (error " + std::to_string(GetLastError()) + ")";
}

class InternetHandle
{
public:
    explicit InternetHandle(HINTERNET handle)
        : m_handle(handle)
    {
    }

    ~InternetHandle()
    {
        if (m_handle != nullptr)
        {
            WinHttpCloseHandle(m_handle);
        }
    }

    InternetHandle(const InternetHandle &) = delete;
    InternetHandle &operator=(const InternetHandle &) = delete;

    HINTERNET get() const
    {
        return m_handle;
    }

private:
    HINTERNET m_handle;
};

class WinHttpTransport final : public HttpTransport
{
public:
    WinHttpTransport()
        : m_session(openSession())
    {
    }

    int get(const std::string &url, uint64_t offset, const Sink &sink, std::string &error) override
    {
        if (m_session.get() == nullptr)
        {
            error = lastErrorText("WinHttpOpen");
            return 0;
        }

        const std::wstring wideUrl = widened(url);
        URL_COMPONENTS components = {};
        components.dwStructSize = sizeof(components);
        components.dwHostNameLength = DWORD(-1);
        components.dwUrlPathLength = DWORD(-1);
        components.dwExtraInfoLength = DWORD(-1);

        if (!WinHttpCrackUrl(wideUrl.c_str(), 0, 0, &components))
        {
            error = "invalid URL " + url;
            return 0;
        }

        const std::wstring host(components.lpszHostName, components.dwHostNameLength);
        std::wstring path(components.lpszUrlPath, components.dwUrlPathLength);
        path.append(components.lpszExtraInfo, components.dwExtraInfoLength);
        const bool secure = components.nScheme == INTERNET_SCHEME_HTTPS;
        InternetHandle connection(WinHttpConnect(m_session.get(), host.c_str(), components.nPort, 0));

        if (connection.get() == nullptr)
        {
            error = lastErrorText("WinHttpConnect");
            return 0;
        }

        InternetHandle request(WinHttpOpenRequest(connection.get(), L"GET", path.c_str(), nullptr,
                                                  WINHTTP_NO_REFERER, WINHTTP_DEFAULT_ACCEPT_TYPES,
                                                  secure ? WINHTTP_FLAG_SECURE : 0));

        if (request.get() == nullptr)
        {
            error = lastErrorText("WinHttpOpenRequest");
            return 0;
        }

        std::wstring headers;

        if (offset > 0)
        {
            headers = L"Range: bytes=" + std::to_wstring(offset) + L"-\r\n";
        }

        if (!WinHttpSendRequest(request.get(), headers.empty() ? WINHTTP_NO_ADDITIONAL_HEADERS : headers.c_str(),
                                DWORD(-1L), WINHTTP_NO_REQUEST_DATA, 0, 0, 0)
            || !WinHttpReceiveResponse(request.get(), nullptr))
        {
            error = lastErrorText("WinHttpSendRequest") + " for " + url;
            return 0;
        }

        DWORD status = 0;
        DWORD statusSize = sizeof(status);

        if (!WinHttpQueryHeaders(request.get(), WINHTTP_QUERY_STATUS_CODE | WINHTTP_QUERY_FLAG_NUMBER,
                                 WINHTTP_HEADER_NAME_BY_INDEX, &status, &statusSize, WINHTTP_NO_HEADER_INDEX))
        {
            error = lastErrorText("WinHttpQueryHeaders");
            return 0;
        }

        if (status != 200 && status != 206)
        {
            error = "HTTP " + std::to_string(status) + " for " + url;
            return int(status);
        }

        std::vector<char> buffer(256 * 1024);
        // A server that ignores the range sends the whole file.
        uint64_t skip = status == 200 ? offset : 0;

        while (true)
        {
            DWORD read = 0;

            if (!WinHttpReadData(request.get(), buffer.data(), DWORD(buffer.size()), &read))
            {
                error = lastErrorText("WinHttpReadData");
                return 0;
            }

            if (read == 0)
            {
                break;
            }

            const DWORD skipped = DWORD(std::min<uint64_t>(skip, read));
            skip -= skipped;

            if (read > skipped && !sink(buffer.data() + skipped, read - skipped))
            {
                error = "cancelled";
                return 0;
            }
        }

        error.clear();
        return int(status);
    }

private:
    static HINTERNET openSession()
    {
        // Automatic proxy discovery needs Windows 8.1; the default proxy setting works everywhere.
        HINTERNET session = WinHttpOpen(L"OpenYAMM", WINHTTP_ACCESS_TYPE_AUTOMATIC_PROXY, WINHTTP_NO_PROXY_NAME,
                                        WINHTTP_NO_PROXY_BYPASS, 0);

        if (session == nullptr)
        {
            session = WinHttpOpen(L"OpenYAMM", WINHTTP_ACCESS_TYPE_DEFAULT_PROXY, WINHTTP_NO_PROXY_NAME,
                                  WINHTTP_NO_PROXY_BYPASS, 0);
        }

        if (session != nullptr)
        {
            WinHttpSetTimeouts(session, 15000, 15000, 30000, 30000);
        }

        return session;
    }

    InternetHandle m_session;
};
}

std::unique_ptr<HttpTransport> createPlatformHttpTransport()
{
    return std::make_unique<WinHttpTransport>();
}
#elif (defined(__linux__) && !defined(__ANDROID__)) || (defined(__APPLE__) && !defined(OPENYAMM_IOS))
namespace
{
// libcurl is loaded when the updater first runs, not linked: the game starts without it, uses the system's TLS,
// certificates and proxy settings, and ships no TLS library to patch. Every desktop distribution carries libcurl
// (Debian and Ubuntu also as the GnuTLS build), and so does macOS. The option numbers are libcurl's stable ABI
// (curl/curl.h).
constexpr int CurlOptionWriteData = 10001;
constexpr int CurlOptionUrl = 10002;
constexpr int CurlOptionRange = 10007;
constexpr int CurlOptionErrorBuffer = 10010;
constexpr int CurlOptionUserAgent = 10018;
constexpr int CurlOptionWriteFunction = 20011;
constexpr int CurlOptionLowSpeedLimit = 19;
constexpr int CurlOptionLowSpeedTime = 20;
constexpr int CurlOptionFollowLocation = 52;
constexpr int CurlOptionMaxRedirects = 68;
constexpr int CurlOptionConnectTimeout = 78;
constexpr int CurlOptionNoSignal = 99;
constexpr int CurlInfoResponseCode = 0x200002;
constexpr long CurlGlobalDefault = 3;
constexpr size_t CurlErrorSize = 256;

struct CurlLibrary
{
    void *(*pEasyInit)() = nullptr;
    int (*pEasySetopt)(void *, int, ...) = nullptr;
    int (*pEasyPerform)(void *) = nullptr;
    int (*pEasyGetinfo)(void *, int, ...) = nullptr;
    void (*pEasyCleanup)(void *) = nullptr;
    const char *(*pEasyStrerror)(int) = nullptr;
    std::string loadError;

    CurlLibrary()
    {
        void *pLibrary = nullptr;

#if defined(__APPLE__)
        for (const char *pName : {"/usr/lib/libcurl.4.dylib"})
#else
        for (const char *pName : {"libcurl.so.4", "libcurl-gnutls.so.4"})
#endif
        {
            pLibrary = pLibrary != nullptr ? pLibrary : dlopen(pName, RTLD_NOW | RTLD_LOCAL);
        }

        if (pLibrary == nullptr)
        {
            loadError = "libcurl is not installed (install the libcurl package of your distribution)";
            return;
        }

        int (*pGlobalInit)(long) = reinterpret_cast<int (*)(long)>(dlsym(pLibrary, "curl_global_init"));
        pEasyInit = reinterpret_cast<void *(*)()>(dlsym(pLibrary, "curl_easy_init"));
        pEasySetopt = reinterpret_cast<int (*)(void *, int, ...)>(dlsym(pLibrary, "curl_easy_setopt"));
        pEasyPerform = reinterpret_cast<int (*)(void *)>(dlsym(pLibrary, "curl_easy_perform"));
        pEasyGetinfo = reinterpret_cast<int (*)(void *, int, ...)>(dlsym(pLibrary, "curl_easy_getinfo"));
        pEasyCleanup = reinterpret_cast<void (*)(void *)>(dlsym(pLibrary, "curl_easy_cleanup"));
        pEasyStrerror = reinterpret_cast<const char *(*)(int)>(dlsym(pLibrary, "curl_easy_strerror"));

        // curl_global_init is not thread-safe; this constructor runs once, before any transfer.
        if (pGlobalInit == nullptr || pEasyInit == nullptr || pEasySetopt == nullptr || pEasyPerform == nullptr
            || pEasyGetinfo == nullptr || pEasyCleanup == nullptr || pEasyStrerror == nullptr
            || pGlobalInit(CurlGlobalDefault) != 0)
        {
            loadError = "the installed libcurl cannot be used";
            pEasyInit = nullptr;
        }
    }
};

const CurlLibrary &curlLibrary()
{
    static const CurlLibrary library;
    return library;
}

struct CurlTransfer
{
    const CurlLibrary *pLibrary = nullptr;
    void *pHandle = nullptr;
    const HttpTransport::Sink *pSink = nullptr;
    uint64_t offset = 0;
    uint64_t skip = 0;
    long status = 0;
    bool cancelled = false;
};

size_t receiveCurlData(char *pData, size_t size, size_t count, void *pUserData)
{
    CurlTransfer &transfer = *static_cast<CurlTransfer *>(pUserData);
    const size_t bytes = size * count;

    if (transfer.status == 0)
    {
        transfer.pLibrary->pEasyGetinfo(transfer.pHandle, CurlInfoResponseCode, &transfer.status);
        // A server that ignores the range sends the whole file.
        transfer.skip = transfer.status == 200 ? transfer.offset : 0;
    }

    // An error page is not the file; stopping here makes libcurl end the transfer.
    if (transfer.status != 200 && transfer.status != 206)
    {
        return 0;
    }

    const size_t skipped = size_t(std::min<uint64_t>(transfer.skip, bytes));
    transfer.skip -= skipped;

    if (bytes > skipped && !(*transfer.pSink)(pData + skipped, bytes - skipped))
    {
        transfer.cancelled = true;
        return 0;
    }

    return bytes;
}

class CurlTransport final : public HttpTransport
{
public:
    int get(const std::string &url, uint64_t offset, const Sink &sink, std::string &error) override
    {
        const CurlLibrary &library = curlLibrary();

        if (library.pEasyInit == nullptr)
        {
            error = library.loadError;
            return 0;
        }

        void *pHandle = library.pEasyInit();

        if (pHandle == nullptr)
        {
            error = "curl_easy_init failed";
            return 0;
        }

        CurlTransfer transfer;
        transfer.pLibrary = &library;
        transfer.pHandle = pHandle;
        transfer.pSink = &sink;
        transfer.offset = offset;
        std::array<char, CurlErrorSize> errorBuffer = {};
        const std::string range = std::to_string(offset) + "-";
        size_t (*pReceive)(char *, size_t, size_t, void *) = &receiveCurlData;
        library.pEasySetopt(pHandle, CurlOptionUrl, url.c_str());
        library.pEasySetopt(pHandle, CurlOptionWriteFunction, pReceive);
        library.pEasySetopt(pHandle, CurlOptionWriteData, &transfer);
        library.pEasySetopt(pHandle, CurlOptionErrorBuffer, errorBuffer.data());
        library.pEasySetopt(pHandle, CurlOptionUserAgent, "OpenYAMM");
        library.pEasySetopt(pHandle, CurlOptionFollowLocation, 1L);
        library.pEasySetopt(pHandle, CurlOptionMaxRedirects, 5L);
        library.pEasySetopt(pHandle, CurlOptionNoSignal, 1L);
        library.pEasySetopt(pHandle, CurlOptionConnectTimeout, 15L);
        // A stalled connection (under one byte per second for 30 seconds) fails, as the WinHTTP timeouts do.
        library.pEasySetopt(pHandle, CurlOptionLowSpeedLimit, 1L);
        library.pEasySetopt(pHandle, CurlOptionLowSpeedTime, 30L);

        if (offset > 0)
        {
            library.pEasySetopt(pHandle, CurlOptionRange, range.c_str());
        }

        const int result = library.pEasyPerform(pHandle);

        if (transfer.status == 0)
        {
            library.pEasyGetinfo(pHandle, CurlInfoResponseCode, &transfer.status);
        }

        library.pEasyCleanup(pHandle);

        if (transfer.cancelled)
        {
            error = "cancelled";
            return 0;
        }

        if (transfer.status != 0 && transfer.status != 200 && transfer.status != 206)
        {
            error = "HTTP " + std::to_string(transfer.status) + " for " + url;
            return int(transfer.status);
        }

        if (result != 0)
        {
            error = (errorBuffer[0] != '\0' ? std::string(errorBuffer.data()) : library.pEasyStrerror(result))
                + " for " + url;
            return 0;
        }

        error.clear();
        return int(transfer.status);
    }
};
}

std::unique_ptr<HttpTransport> createPlatformHttpTransport()
{
    return std::make_unique<CurlTransport>();
}
#else
std::unique_ptr<HttpTransport> createPlatformHttpTransport()
{
    return nullptr;
}
#endif
}
