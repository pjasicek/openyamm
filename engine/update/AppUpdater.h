#pragma once

#include "engine/update/AppInstallation.h"
#include "engine/update/HttpTransport.h"
#include "engine/update/ReleaseManifest.h"

#include <atomic>
#include <cstdint>
#include <filesystem>
#include <memory>
#include <mutex>
#include <ostream>
#include <string>
#include <thread>
#include <vector>

namespace OpenYAMM::Engine
{
// What an update needs beyond the installed files: packs whose file is not in the store yet (unchanged packs keep
// their file name, so they are never downloaded again) and the app archive.
struct UpdatePlan
{
    std::vector<size_t> packsToDownload;
    size_t reusedPacks = 0;
    uint64_t downloadBytes = 0;
};

// includeApp is false when only the installed version's content is missing. A language's optional packs are part of
// the plan only for the languages given (the installed ones and the one chosen in Settings).
UpdatePlan planUpdate(const ReleaseManifest &manifest, const std::filesystem::path &packStore, bool includeApp = true,
                      const std::vector<std::string> &languages = {});

enum class UpdateState
{
    Idle,
    Checking,
    UpToDate,
    Available,
    Downloading,
    Ready,
    Failed
};

struct UpdateStatus
{
    UpdateState state = UpdateState::Idle;
    std::string release;
    std::string notesUrl;
    std::string notes;
    // Player-facing reason for Failed, or what is being done.
    std::string message;
    uint64_t totalBytes = 0;
    uint64_t doneBytes = 0;
    size_t packCount = 0;
    // The installed version lacks its own content (a fresh installation from the small download package): the
    // download completes it instead of installing another version, and nothing needs to switch.
    bool contentOnly = false;
};

// The self-updater of a versioned installation (Windows and Linux, packaging/UPDATER_PLAN.md 8 and 9.1). check() and download()
// run on a worker thread; status() may be polled every frame. Nothing the running game uses is touched before
// activate(). It also installs the content of a fresh installation, whose small package carries no packs.
class AppUpdater
{
public:
    AppUpdater(AppInstallation installation, std::string installedVersion, std::string platform, std::string baseUrl,
               std::unique_ptr<HttpTransport> transport);
    ~AppUpdater();
    AppUpdater(const AppUpdater &) = delete;
    AppUpdater &operator=(const AppUpdater &) = delete;

    // The release keys by default; tests sign with their own.
    void setTrustedKeys(std::vector<ManifestPublicKey> keys);
    // The languages whose optional packs (sounds, voices, videos, fonts) are kept installed and updated; set before
    // check().
    void setLanguages(std::vector<std::string> languages);
    void check();
    // After check() found an update: downloads, verifies and stages it.
    void download();
    void cancel();
    UpdateStatus status() const;
    bool busy() const;
    // Waits for the running check or download.
    void wait();
    // Ready → the staged version becomes current; the next start (through the launcher) runs it.
    bool activate(std::string &error);

private:
    struct Job
    {
        std::string url;
        std::filesystem::path target;
        uint64_t size = 0;
        std::string sha256;
    };

    void start(void (AppUpdater::*pTask)());
    void runCheck();
    void runDownload();
    bool fetchText(const std::string &url, std::string &text, std::string &error);
    bool downloadJob(const Job &job, std::string &error);
    bool stageApp(const std::filesystem::path &archive, std::string &error);
    void setStatus(UpdateState state, const std::string &message);
    void fail(const std::string &message);

    AppInstallation m_installation;
    std::string m_installedVersion;
    std::string m_platform;
    std::string m_baseUrl;
    std::unique_ptr<HttpTransport> m_pTransport;
    std::vector<ManifestPublicKey> m_trustedKeys = releaseManifestPublicKeys();
    std::vector<std::string> m_languages;
    std::optional<ReleaseManifest> m_manifest;
    mutable std::mutex m_mutex;
    UpdateStatus m_status;
    std::atomic<uint64_t> m_doneBytes = 0;
    std::atomic<bool> m_cancel = false;
    std::atomic<bool> m_busy = false;
    std::thread m_worker;
};

// The manifest URL of a platform below a channel's base URL (".../openyamm/updates/").
std::string releaseManifestUrl(const std::string &baseUrl, const std::string &platform);
// The download URL of a manifest's store file: an absolute address as it is, otherwise below the channel.
std::string releaseFileUrl(const std::string &baseUrl, const std::string &url);
// The manifest platform of this build ("windows-x64", "linux-x64", "macos-arm64").
const char *releasePlatformName();

// Copies the files below `prefix` of a zip archive into targetDirectory.
bool extractZipFolder(const std::filesystem::path &archive, const std::string &prefix,
                      const std::filesystem::path &targetDirectory, std::string &error);

// After a version first reached its main menu: marks it healthy, then removes what no longer serves it (the other
// version folders, unreferenced packs, files of the old single-folder releases) and installs its launcher.
void finishHealthyStart(AppInstallation &installation, const std::string &version, std::ostream &log);
}
