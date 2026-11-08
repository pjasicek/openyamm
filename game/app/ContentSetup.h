#pragma once

#include <filesystem>
#include <string>

namespace OpenYAMM::Game
{
enum class ContentSetupResult
{
    // The content is installed; the game starts.
    Ready,
    // A newer release was installed and its launcher started; this process ends.
    Restarted,
    // The player closed the window or the content cannot be installed.
    Quit
};

// Whether the index in assetRoot names packs that are not in its store: a fresh installation from the small download
// package, which carries the game but none of its content (packaging/UPDATER_PLAN.md 9.1).
bool installedContentMissing(const std::filesystem::path &assetRoot);
// Whether the optional packs (voices, sounds, videos, fonts) of the language chosen in Settings are not downloaded yet.
bool languageContentMissing(const std::filesystem::path &assetRoot, const std::string &languageId);
// With [updates] keep_modified_packs the packs are not checked or restored (packaging/MODDING.md); when one is missing,
// a message box says what to do and the game does not start.
bool modifiedContentComplete(const std::filesystem::path &assetRoot);

// The first start of such an installation: a window that needs no game content downloads it through the updater, or a
// newer release when one is published. It also restores the packs of an installation that lost or changed some.
// With languageId it also downloads that language's packs; when only those are missing and nothing can download them,
// it returns Quit without a message, and the game plays in English.
ContentSetupResult runContentSetup(const std::string &updateChannelUrl, const std::filesystem::path &assetRoot,
                                   const std::string &languageId = {});
}
