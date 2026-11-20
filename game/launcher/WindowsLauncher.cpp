// OpenYAMM.exe: starts the current version of a versioned installation (app/<version>/openyamm.exe) with the same
// arguments and exits at once, so an update never replaces a running file (packaging/UPDATER_PLAN.md 9.1). A version that never
// reached its main menu and failed to start twice is rolled back to the previous one.
#include "engine/update/AppInstallation.h"

#include <windows.h>

#include <string>

namespace
{
std::wstring argumentsAfterProgramName(const wchar_t *pCommandLine)
{
    const wchar_t *pCursor = pCommandLine;

    if (*pCursor == L'"')
    {
        ++pCursor;

        while (*pCursor != L'\0' && *pCursor != L'"')
        {
            ++pCursor;
        }

        if (*pCursor == L'"')
        {
            ++pCursor;
        }
    }
    else
    {
        while (*pCursor != L'\0' && *pCursor != L' ' && *pCursor != L'\t')
        {
            ++pCursor;
        }
    }

    while (*pCursor == L' ' || *pCursor == L'\t')
    {
        ++pCursor;
    }

    return pCursor;
}

int showError(const std::wstring &message)
{
    MessageBoxW(nullptr, message.c_str(), L"OpenYAMM", MB_OK | MB_ICONERROR);
    return 1;
}
}

int WINAPI wWinMain(HINSTANCE, HINSTANCE, PWSTR, int)
{
    std::wstring modulePath(32768, L'\0');
    const DWORD length = GetModuleFileNameW(nullptr, modulePath.data(), DWORD(modulePath.size()));
    modulePath.resize(length);
    OpenYAMM::Engine::AppInstallation installation(std::filesystem::path(modulePath).parent_path());
    std::string rolledBackFrom;
    const std::optional<std::string> version = installation.chooseVersionToStart(rolledBackFrom);

    if (!version)
    {
        return showError(L"This OpenYAMM folder is incomplete: app\\current is missing.\n\n"
                         L"Download the complete package from the website and extract it again.");
    }

    const std::filesystem::path game = installation.gameExecutable(*version);
    std::wstring commandLine = L"\"" + game.wstring() + L"\" " + argumentsAfterProgramName(GetCommandLineW());
    STARTUPINFOW startup = {};
    startup.cb = sizeof(startup);
    PROCESS_INFORMATION process = {};

    if (!CreateProcessW(game.c_str(), commandLine.data(), nullptr, nullptr, FALSE, 0, nullptr, nullptr, &startup,
                        &process))
    {
        return showError(L"OpenYAMM could not start " + game.wstring() + L" (error "
                         + std::to_wstring(GetLastError()) + L").");
    }

    CloseHandle(process.hThread);
    CloseHandle(process.hProcess);
    return 0;
}
