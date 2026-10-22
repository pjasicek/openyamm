#pragma once

#include <vector>

namespace OpenYAMM::Game
{
// The command line of an app bundle launch, with --user-data <per-user folder> added unless it names one itself; the
// vector ends with a null pointer, as argv does.
std::vector<char *> appleBundleArguments(int argc, char **argv);
}
