#pragma once

#include "engine/update/AppInstallation.h"

#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
// The command line of an app bundle launch, with --user-data <per-user folder> added unless it names one itself; the
// vector ends with a null pointer, as argv does.
std::vector<char *> appleBundleArguments(int argc, char **argv);

// The downloaded OpenYAMM.app of a release runs from wherever the player put it, often a read-only copy that macOS
// made (App Translocation). It never plays from there: it installs its release into the per-user folder, a versioned
// installation, and starts the version installed there (packaging/UPDATER_PLAN.md 9.4).
//
// That installation when this process is such a downloaded app (a release bundle outside an installation).
std::optional<Engine::AppInstallation> applePackageInstallation();
// The release the downloaded app installs.
std::string applePackageVersion();
// When the downloaded app finds an installed version, it starts it in place of this process and does not return; when
// that fails, the exit code of this process. Nothing when there is nothing to start.
std::optional<int> startInstalledApplePackage(int argc, char **argv);
}
