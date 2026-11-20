// OpenYAMM on Linux and macOS: starts the current version of a versioned installation (app/<version>/openyamm, on
// macOS app/<version>/OpenYAMM.app) with the same arguments in place of this process, so an update never replaces a
// running file (packaging/UPDATER_PLAN.md 9.1). A version that never reached its main menu and failed to start twice
// is rolled back to the previous one.
#include "engine/update/AppInstallation.h"

#if defined(__APPLE__)
#include <mach-o/dyld.h>
#endif
#include <unistd.h>

#include <cerrno>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <string>
#include <vector>

namespace
{
std::filesystem::path ownExecutable(std::error_code &error)
{
#if defined(__APPLE__)
    uint32_t size = 0;
    _NSGetExecutablePath(nullptr, &size);
    std::string path(size, '\0');

    if (_NSGetExecutablePath(path.data(), &size) != 0)
    {
        error = std::make_error_code(std::errc::filename_too_long);
        return {};
    }

    path.resize(std::strlen(path.c_str()));
    return std::filesystem::canonical(path, error);
#else
    return std::filesystem::read_symlink("/proc/self/exe", error);
#endif
}
}

int main(int argc, char **argv)
{
    std::error_code error;
    const std::filesystem::path self = ownExecutable(error);

    if (error)
    {
        std::cerr << "OpenYAMM cannot find its own folder: " << error.message() << '\n';
        return 1;
    }

    OpenYAMM::Engine::AppInstallation installation(self.parent_path());
    std::string rolledBackFrom;
    const std::optional<std::string> version = installation.chooseVersionToStart(rolledBackFrom);

    if (!version)
    {
        std::cerr << "This OpenYAMM folder is incomplete: app/current is missing.\n"
                     "Download the package from the website and extract it again.\n";
        return 1;
    }

    const std::string game = installation.gameExecutable(*version).string();
    std::vector<char *> arguments = {const_cast<char *>(game.c_str())};
    arguments.insert(arguments.end(), argv + 1, argv + argc);
    arguments.push_back(nullptr);
    execv(game.c_str(), arguments.data());

    std::cerr << "OpenYAMM could not start " << game << ": " << std::strerror(errno) << '\n';
    return 1;
}
