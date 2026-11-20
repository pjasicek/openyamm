#pragma once

#include "engine/update/AppUpdater.h"

#include <memory>
#include <optional>
#include <ostream>
#include <string>

namespace OpenYAMM::Game
{
// The main menu's view of the self-updater (packaging/UPDATER_PLAN.md 8–10): the versioned Windows and Linux installations
// update in the game; Android hands over to its update screen. Development runs have none.
class GameUpdater
{
public:
    // Null where this build does not update itself. With keepModifiedPacks (settings.ini [updates]
    // keep_modified_packs), a check only reports that updates are off and nothing downloads, as an update would
    // replace the packs the player edited; the start counting of the rollback rule continues.
    // languageId: the interface language chosen in Settings; its optional packs (fonts, voices, cutscenes) download
    // and update with the game's, as do those of every language already installed (devdocs/LOCALIZATION.md).
    static std::unique_ptr<GameUpdater> create(const std::string &baseUrl, bool keepModifiedPacks = false,
                                               const std::string &languageId = {});

    virtual ~GameUpdater() = default;
    virtual std::string installedVersion() const = 0;
    virtual void check() = 0;
    virtual Engine::UpdateStatus status() const = 0;
    // After an update was found: the desktop downloads it while the menu waits; Android opens its update screen, and
    // the game should quit.
    virtual void startUpdate() = 0;
    virtual bool updatesInGame() const = 0;
    virtual void cancel() = 0;
    // A downloaded update becomes current and starts; the game should quit.
    virtual bool restartIntoUpdate(std::string &error) = 0;
    // The game reached its main menu or finished a headless run.
    virtual void markHealthy(std::ostream &log) = 0;
    // The version a failed update rolled back from, once.
    virtual std::optional<std::string> takeRollbackNotice() = 0;
};

// --headless-update: checks, downloads and installs an update without the menu. 0 when up to date or updated.
int runHeadlessUpdate(const std::string &baseUrl, bool keepModifiedPacks, std::ostream &log);
}
