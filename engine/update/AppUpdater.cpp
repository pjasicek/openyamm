#include "engine/update/AppUpdater.h"

#include "engine/AssetPackIndex.h"
#include "engine/update/Sha256.h"

#include <algorithm>
#include <physfs.h>

#include <array>
#include <chrono>
#include <fstream>
#include <unordered_set>

namespace OpenYAMM::Engine
{
namespace
{
constexpr const char *ChannelName = "stable";
constexpr size_t ParallelDownloads = 3;
// The pauses before each further attempt at a file after a broken connection or a busy server (HTTP 408, 429, 5xx;
// nginx answers 503 above its connections per address, which a household or a mobile carrier's shared address
// reaches). Each attempt resumes the partial file.
constexpr std::array<int, 5> RetryDelaySeconds = {0, 2, 5, 10, 20};
// Free space required beyond the download, so a nearly full disk is refused before it fills up.
constexpr double FreeSpaceMargin = 1.1;
constexpr const char *ArchiveMountPoint = "/.openyamm-update-archive";

std::string utf8(const std::filesystem::path &path)
{
    const std::u8string text = path.u8string();
    return std::string(text.begin(), text.end());
}

std::filesystem::path pathFromUtf8(const std::string &text)
{
    return std::filesystem::path(std::u8string(text.begin(), text.end()));
}

std::string megabytes(uint64_t bytes)
{
    return std::to_string((bytes + 999999) / 1000000) + " MB";
}

bool sameFileContent(const std::filesystem::path &left, const std::filesystem::path &right)
{
    std::error_code error;

    if (std::filesystem::file_size(left, error) != std::filesystem::file_size(right, error) || error)
    {
        return false;
    }

    return sha256File(left) == sha256File(right);
}

bool copyPhysFsFile(const std::string &source, const std::filesystem::path &target, std::string &error)
{
    PHYSFS_File *pInput = PHYSFS_openRead(source.c_str());

    if (pInput == nullptr)
    {
        error = "cannot read " + source + " from the update archive";
        return false;
    }

    std::error_code fileError;
    std::filesystem::create_directories(target.parent_path(), fileError);
    std::ofstream output(target, std::ios::binary | std::ios::trunc);
    std::vector<char> buffer(1 << 20);
    bool succeeded = bool(output);

    while (succeeded)
    {
        const PHYSFS_sint64 read = PHYSFS_readBytes(pInput, buffer.data(), buffer.size());

        if (read < 0)
        {
            succeeded = false;
            break;
        }

        if (read == 0)
        {
            break;
        }

        output.write(buffer.data(), std::streamsize(read));
        succeeded = bool(output);
    }

    PHYSFS_close(pInput);

    if (!succeeded || !output.flush())
    {
        error = "cannot write " + utf8(target);
        return false;
    }

    return true;
}

bool copyPhysFsFolder(const std::string &source, const std::filesystem::path &target, size_t &fileCount,
                      std::string &error)
{
    char **ppEntries = PHYSFS_enumerateFiles(source.c_str());

    if (ppEntries == nullptr)
    {
        error = "cannot list " + source + " in the update archive";
        return false;
    }

    bool succeeded = true;

    for (char **ppEntry = ppEntries; *ppEntry != nullptr && succeeded; ++ppEntry)
    {
        const std::string name = *ppEntry;
        const std::string path = source + "/" + name;
        PHYSFS_Stat stat = {};

        if (name == "." || name == ".." || !PHYSFS_stat(path.c_str(), &stat))
        {
            continue;
        }

        if (stat.filetype == PHYSFS_FILETYPE_DIRECTORY)
        {
            succeeded = copyPhysFsFolder(path, target / pathFromUtf8(name), fileCount, error);
        }
        else
        {
            succeeded = copyPhysFsFile(path, target / pathFromUtf8(name), error);
            fileCount += succeeded ? 1 : 0;
        }
    }

    PHYSFS_freeList(ppEntries);
    return succeeded;
}

// Zip archives carry no permissions PhysicsFS reads, so the extracted executables are made executable again.
void makeExecutable(const std::filesystem::path &path)
{
#if !defined(_WIN32)
    std::error_code error;

    if (std::filesystem::is_regular_file(path, error))
    {
        std::filesystem::permissions(path,
                                     std::filesystem::perms::owner_exec | std::filesystem::perms::group_exec
                                         | std::filesystem::perms::others_exec,
                                     std::filesystem::perm_options::add, error);
    }
#else
    (void)path;
#endif
}

void removeLegacyRelease(const AppInstallation &installation, std::ostream &log)
{
    // Releases up to 1.5 kept the whole game in one folder: two packages in assets/ and the shaders in runtime/.
    // Players extract the new package over such a folder; the saves and settings.ini there stay where they are.
    const std::filesystem::path root = installation.root();
    std::vector<std::filesystem::path> leftovers = {root / "assets" / "engine.zip", root / "runtime"};
    std::error_code error;

    for (const std::filesystem::directory_entry &entry :
         std::filesystem::directory_iterator(root / "assets" / "worlds", error))
    {
        if (entry.path().extension() == ".zip")
        {
            leftovers.push_back(entry.path());
        }
    }

    for (const std::filesystem::path &path : leftovers)
    {
        if (std::filesystem::exists(path, error) && std::filesystem::remove_all(path, error) > 0)
        {
            log << "Update: removed " << utf8(path) << " of an earlier release\n";
        }
    }

    std::filesystem::remove(root / "assets" / "worlds", error);
}
}

UpdatePlan planUpdate(const ReleaseManifest &manifest, const std::filesystem::path &packStore, bool includeApp,
                      const std::vector<std::string> &languages)
{
    UpdatePlan plan;

    for (size_t index = 0; index < manifest.packs.size(); ++index)
    {
        const AssetPackRecord &pack = manifest.packs[index];

        if (!pack.language.empty() && std::find(languages.begin(), languages.end(), pack.language) == languages.end())
        {
            continue;
        }

        std::error_code error;
        const uintmax_t size = std::filesystem::file_size(packStore / pack.file, error);

        // A file name carries its content id, and files are only renamed into the store once verified.
        if (!error && size == pack.size)
        {
            ++plan.reusedPacks;
            continue;
        }

        plan.packsToDownload.push_back(index);
        plan.downloadBytes += pack.size;
    }

    plan.downloadBytes += includeApp ? manifest.app.size : 0;
    return plan;
}

std::string releaseManifestUrl(const std::string &baseUrl, const std::string &platform)
{
    const std::string base = baseUrl.empty() || baseUrl.back() == '/' ? baseUrl : baseUrl + "/";
    return base + "channels/" + ChannelName + "/" + platform + ".json";
}

std::string releaseFileUrl(const std::string &baseUrl, const std::string &url)
{
    return url.starts_with("https://") || url.starts_with("http://") ? url : baseUrl + url;
}

const char *releasePlatformName()
{
#if defined(_WIN32)
    return "windows-x64";
#elif defined(__APPLE__)
    return "macos-arm64";
#else
    return "linux-x64";
#endif
}

AppUpdater::AppUpdater(AppInstallation installation, std::string installedVersion, std::string platform,
                       std::string baseUrl, std::unique_ptr<HttpTransport> transport)
    : m_installation(std::move(installation))
    , m_installedVersion(std::move(installedVersion))
    , m_platform(std::move(platform))
    , m_baseUrl(baseUrl.empty() || baseUrl.back() == '/' ? baseUrl : baseUrl + "/")
    , m_pTransport(std::move(transport))
{
}

AppUpdater::~AppUpdater()
{
    cancel();
    wait();
}

void AppUpdater::setTrustedKeys(std::vector<ManifestPublicKey> keys)
{
    m_trustedKeys = std::move(keys);
}

void AppUpdater::setLanguages(std::vector<std::string> languages)
{
    m_languages = std::move(languages);
}

void AppUpdater::check()
{
    start(&AppUpdater::runCheck);
}

void AppUpdater::download()
{
    start(&AppUpdater::runDownload);
}

void AppUpdater::cancel()
{
    m_cancel = true;
}

UpdateStatus AppUpdater::status() const
{
    std::lock_guard<std::mutex> lock(m_mutex);
    UpdateStatus status = m_status;
    status.doneBytes = std::min(m_doneBytes.load(), status.totalBytes);
    return status;
}

bool AppUpdater::busy() const
{
    return m_busy;
}

void AppUpdater::wait()
{
    if (m_worker.joinable())
    {
        m_worker.join();
    }
}

void AppUpdater::start(void (AppUpdater::*pTask)())
{
    if (m_busy)
    {
        return;
    }

    wait();
    m_cancel = false;
    m_busy = true;
    m_worker = std::thread(
        [this, pTask]()
        {
            (this->*pTask)();
            m_busy = false;
        });
}

void AppUpdater::setStatus(UpdateState state, const std::string &message)
{
    std::lock_guard<std::mutex> lock(m_mutex);
    m_status.state = state;
    m_status.message = message;
}

void AppUpdater::fail(const std::string &message)
{
    setStatus(UpdateState::Failed, m_cancel ? "The update was cancelled." : message);
}

bool AppUpdater::fetchText(const std::string &url, std::string &text, std::string &error)
{
    text.clear();
    const int status = m_pTransport->get(
        url, 0,
        [this, &text](const char *pData, size_t size)
        {
            // Manifests are small; anything larger is not one.
            text.append(pData, size);
            return !m_cancel && text.size() < 16 * 1024 * 1024;
        },
        error);
    return status == 200;
}

void AppUpdater::runCheck()
{
    {
        std::lock_guard<std::mutex> lock(m_mutex);
        m_status = UpdateStatus();
        m_status.state = UpdateState::Checking;
        m_status.message = "Checking for updates...";
    }

    if (!m_pTransport)
    {
        fail("This version of OpenYAMM cannot update itself.");
        return;
    }

    const std::string manifestUrl = releaseManifestUrl(m_baseUrl, m_platform);
    std::string manifestText;
    std::string signatureText;
    std::string error;

    if (!fetchText(manifestUrl, manifestText, error) || !fetchText(manifestUrl + ".sig", signatureText, error))
    {
        fail("The update server is unreachable; try again later. (" + error + ")");
        return;
    }

    if (!verifyManifestSignature(manifestText, signatureText, m_trustedKeys, error))
    {
        fail("The update's signature is invalid; download the complete package from the website. (" + error + ")");
        return;
    }

    std::optional<ReleaseManifest> manifest = parseReleaseManifest(manifestText, error);

    if (!manifest || manifest->platform != m_platform)
    {
        fail("The update server sent an unexpected release (" + (manifest ? manifest->platform : error) + ").");
        return;
    }

    if (manifest->minUpdaterSchema > UpdaterSchema)
    {
        fail("OpenYAMM " + manifest->release + " needs the complete package from the website.");
        return;
    }

    const std::optional<int> comparison = compareReleaseVersions(manifest->release, m_installedVersion);

    if (!comparison)
    {
        fail("This build of OpenYAMM (" + m_installedVersion + ") does not take updates.");
        return;
    }

    bool contentOnly = false;
    // The per-user installation that the downloaded macOS app creates holds no version yet: it installs the published
    // release, the app's own or a newer one (packaging/UPDATER_PLAN.md 9.4).
    const bool emptyInstallation = !m_installation.currentVersion();

    if (*comparison == 0 && !emptyInstallation)
    {
        // The installed version itself: complete when all of its packs are there, else a fresh installation whose
        // small package carries no packs. Its index must name exactly the published packs.
        if (planUpdate(*manifest, m_installation.packStore(), false, m_languages).packsToDownload.empty())
        {
            std::lock_guard<std::mutex> lock(m_mutex);
            m_status.release = manifest->release;
            m_status.state = UpdateState::UpToDate;
            m_status.message = "OpenYAMM " + m_installedVersion + " is up to date.";
            return;
        }

        std::string indexError;
        const std::optional<AssetPackIndex> installed = loadAssetPackIndex(
            m_installation.appDirectory(m_installedVersion) / AssetPackIndexFileName, indexError);
        std::unordered_set<std::string> installedFiles;
        std::unordered_set<std::string> publishedFiles;

        for (const AssetPackRecord &pack : installed ? installed->packs : std::vector<AssetPackRecord>())
        {
            installedFiles.insert(pack.file);
        }

        for (const AssetPackRecord &pack : manifest->packs)
        {
            publishedFiles.insert(pack.file);
        }

        if (!installed || installedFiles != publishedFiles)
        {
            fail("This OpenYAMM " + m_installedVersion
                 + " package does not match the published release; download it again from the website.");
            return;
        }

        contentOnly = true;
    }

    std::lock_guard<std::mutex> lock(m_mutex);
    m_status.release = manifest->release;
    m_status.notesUrl = manifest->notesUrl;
    m_status.notes = manifest->notes;

    // An older manifest is refused too, so a replayed one cannot downgrade the game.
    if (*comparison < 0)
    {
        m_status.state = UpdateState::UpToDate;
        m_status.message = "OpenYAMM " + m_installedVersion + " is up to date.";
        return;
    }

    const UpdatePlan plan = planUpdate(*manifest, m_installation.packStore(), !contentOnly, m_languages);
    m_status.state = UpdateState::Available;
    m_status.contentOnly = contentOnly;
    m_status.totalBytes = plan.downloadBytes;
    m_status.packCount = plan.packsToDownload.size();
    m_status.message = contentOnly
        ? "OpenYAMM " + manifest->release + " needs its game content (" + megabytes(plan.downloadBytes) + ")."
        : "OpenYAMM " + manifest->release + " is available (" + megabytes(plan.downloadBytes) + ").";
    m_manifest = std::move(manifest);
}

bool AppUpdater::downloadJob(const Job &job, std::string &error)
{
    std::error_code fileError;

    // The app archive of an earlier, interrupted attempt.
    if (std::filesystem::file_size(job.target, fileError) == job.size && !fileError
        && sha256File(job.target) == job.sha256)
    {
        m_doneBytes += job.size;
        return true;
    }

    const std::filesystem::path part = m_installation.updateDirectory() / (job.target.filename().string() + ".part");
    bool verificationFailed = false;

    for (size_t attempt = 0;; ++attempt)
    {
        uint64_t offset = std::filesystem::exists(part, fileError) ? std::filesystem::file_size(part, fileError) : 0;

        if (fileError || offset > job.size)
        {
            std::filesystem::remove(part, fileError);
            offset = 0;
        }

        m_doneBytes += offset;
        uint64_t received = offset;
        std::ofstream output(part, std::ios::binary | (offset > 0 ? std::ios::app : std::ios::trunc));

        if (!output)
        {
            error = "cannot write " + utf8(part);
            return false;
        }

        const int status = m_pTransport->get(
            releaseFileUrl(m_baseUrl, job.url), offset,
            [this, &output, &received, &job](const char *pData, size_t size)
            {
                received += size;
                m_doneBytes += size;
                output.write(pData, std::streamsize(size));
                return bool(output) && !m_cancel && received <= job.size;
            },
            error);
        output.close();

        if (m_cancel)
        {
            error = "cancelled";
            return false;
        }

        if ((status == 200 || status == 206) && received == job.size && sha256File(part) == job.sha256)
        {
            std::filesystem::remove(job.target, fileError);
            std::filesystem::rename(part, job.target, fileError);

            if (fileError)
            {
                error = "cannot move " + utf8(part) + " into place: " + fileError.message();
                return false;
            }

            return true;
        }

        m_doneBytes.fetch_sub(std::min(m_doneBytes.load(), received));

        // A complete answer with the wrong bytes is downloaded once more from scratch.
        if (status == 200 || status == 206)
        {
            error = job.target.filename().string() + " failed verification";
            std::filesystem::remove(part, fileError);

            if (verificationFailed)
            {
                return false;
            }

            verificationFailed = true;
            continue;
        }

        if (error.empty())
        {
            error = "HTTP " + std::to_string(status);
        }

        const bool transient = status == 0 || status == 408 || status == 429 || status >= 500;

        if (!transient || attempt >= RetryDelaySeconds.size())
        {
            return false;
        }

        const auto resume = std::chrono::steady_clock::now() + std::chrono::seconds(RetryDelaySeconds[attempt]);

        while (std::chrono::steady_clock::now() < resume && !m_cancel)
        {
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }

        if (m_cancel)
        {
            error = "cancelled";
            return false;
        }

        error.clear();
    }
}

void AppUpdater::runDownload()
{
    if (!m_manifest)
    {
        fail("Check for updates first.");
        return;
    }

    const ReleaseManifest &manifest = *m_manifest;
    const bool contentOnly = status().contentOnly;
    const UpdatePlan plan = planUpdate(manifest, m_installation.packStore(), !contentOnly, m_languages);
    std::error_code fileError;
    std::filesystem::create_directories(m_installation.updateDirectory(), fileError);
    std::filesystem::create_directories(m_installation.packStore(), fileError);

    if (fileError || !writeTextFileAtomically(m_installation.updateDirectory() / "writable", ""))
    {
        fail("OpenYAMM cannot write to its folder " + utf8(m_installation.root())
             + ". Move it to a folder you can write to, or download the complete package.");
        return;
    }

    const std::filesystem::space_info space = std::filesystem::space(m_installation.root(), fileError);

    if (!fileError && double(space.available) < double(plan.downloadBytes) * FreeSpaceMargin)
    {
        fail("Not enough disk space: " + megabytes(uint64_t(double(plan.downloadBytes) * FreeSpaceMargin))
             + " needed.");
        return;
    }

    {
        std::lock_guard<std::mutex> lock(m_mutex);
        m_status.state = UpdateState::Downloading;
        m_status.message = contentOnly ? "Downloading the game content..."
                                       : "Downloading OpenYAMM " + manifest.release + "...";
        m_status.totalBytes = plan.downloadBytes;
        m_status.packCount = plan.packsToDownload.size();
    }

    m_doneBytes = 0;
    std::vector<Job> jobs;
    const std::filesystem::path archive = m_installation.updateDirectory() / ("app-" + manifest.release + ".zip");

    if (!contentOnly)
    {
        jobs.push_back({manifest.app.url, archive, manifest.app.size, manifest.app.sha256});
    }

    for (const size_t index : plan.packsToDownload)
    {
        const AssetPackRecord &pack = manifest.packs[index];
        jobs.push_back({manifest.packUrls[index], m_installation.packStore() / pack.file, pack.size, pack.sha256});
    }

    std::atomic<size_t> nextJob = 0;
    std::mutex errorMutex;
    std::string firstError;
    std::vector<std::thread> workers;

    for (size_t worker = 0; worker < std::min(ParallelDownloads, jobs.size()); ++worker)
    {
        workers.emplace_back(
            [this, &jobs, &nextJob, &errorMutex, &firstError]()
            {
                for (size_t index = nextJob++; index < jobs.size() && !m_cancel; index = nextJob++)
                {
                    std::string error;

                    if (!downloadJob(jobs[index], error))
                    {
                        std::lock_guard<std::mutex> lock(errorMutex);
                        firstError = firstError.empty() ? error : firstError;
                        m_cancel = true;
                    }
                }
            });
    }

    for (std::thread &worker : workers)
    {
        worker.join();
    }

    if (!firstError.empty() || m_cancel)
    {
        const bool cancelledByPlayer = firstError.empty() || firstError == "cancelled";
        m_cancel = cancelledByPlayer;
        fail(cancelledByPlayer ? "The update was cancelled."
                               : "The download failed; try again later. (" + firstError + ")");
        return;
    }

    if (contentOnly)
    {
        setStatus(UpdateState::Ready, "The game content of OpenYAMM " + manifest.release + " is installed.");
        return;
    }

    setStatus(UpdateState::Downloading, "Installing OpenYAMM " + manifest.release + "...");
    std::string error;

    if (!stageApp(archive, error))
    {
        fail("The update could not be installed: " + error);
        return;
    }

    setStatus(UpdateState::Ready, "OpenYAMM " + manifest.release + " is ready. Restart to play it.");
}

bool AppUpdater::stageApp(const std::filesystem::path &archive, std::string &error)
{
    const std::string &release = m_manifest->release;

    if (!isValidAppVersionName(release))
    {
        error = "invalid release name " + release;
        return false;
    }

    const std::filesystem::path target = m_installation.appDirectory(release);
    std::filesystem::path staging = target;
    staging += ".staging";
    std::error_code fileError;
    std::filesystem::remove_all(staging, fileError);

    if (!extractZipFolder(archive, "OpenYAMM/app/" + release, staging, error))
    {
        return false;
    }

    std::optional<AssetPackIndex> index = loadAssetPackIndex(staging / AssetPackIndexFileName, error);

    if (!index || !validateAssetPackFiles(*index, staging / index->store, error))
    {
        error = "the new version's content is incomplete: " + error;
        return false;
    }

    if (index->release != release)
    {
        error = "the app archive holds " + index->release + ", not " + release;
        return false;
    }

    makeExecutable(staging / GameExecutableName);
    makeExecutable(staging / LauncherCopyName);

    if (m_installation.currentVersion() == release)
    {
        error = release + " is already installed";
        return false;
    }

    std::filesystem::remove_all(target, fileError);
    std::filesystem::rename(staging, target, fileError);

    if (fileError)
    {
        error = "cannot move the new version into place: " + fileError.message();
        return false;
    }

    return true;
}

bool AppUpdater::activate(std::string &error)
{
    const UpdateStatus current = status();

    if (current.state != UpdateState::Ready || !m_manifest)
    {
        error = "no update is ready";
        return false;
    }

    // Completed content belongs to the running version: nothing switches.
    if (!current.contentOnly && !m_installation.switchTo(m_manifest->release, error))
    {
        return false;
    }

    // The first version of an empty installation brings the launcher that starts it.
    const std::filesystem::path launcher = m_installation.appDirectory(m_manifest->release) / LauncherCopyName;
    std::error_code launcherError;

    if (!std::filesystem::exists(m_installation.launcherPath(), launcherError)
        && std::filesystem::is_regular_file(launcher, launcherError))
    {
        std::filesystem::copy_file(launcher, m_installation.launcherPath(), launcherError);

        if (launcherError)
        {
            error = "cannot install the launcher: " + launcherError.message();
            return false;
        }

        makeExecutable(m_installation.launcherPath());
    }

    std::error_code fileError;
    std::filesystem::remove_all(m_installation.updateDirectory(), fileError);
    return true;
}

bool extractZipFolder(const std::filesystem::path &archive, const std::string &prefix,
                      const std::filesystem::path &targetDirectory, std::string &error)
{
    const bool initializedHere = PHYSFS_isInit() == 0;

    if (initializedHere && PHYSFS_init(nullptr) == 0)
    {
        error = std::string("PhysicsFS: ") + PHYSFS_getErrorByCode(PHYSFS_getLastErrorCode());
        return false;
    }

    const std::string archivePath = utf8(archive);
    bool succeeded = false;

    if (PHYSFS_mount(archivePath.c_str(), ArchiveMountPoint, 0) == 0)
    {
        error = "cannot open the update archive: " + std::string(PHYSFS_getErrorByCode(PHYSFS_getLastErrorCode()));
    }
    else
    {
        size_t fileCount = 0;
        succeeded = copyPhysFsFolder(std::string(ArchiveMountPoint) + "/" + prefix, targetDirectory, fileCount, error);

        if (succeeded && fileCount == 0)
        {
            error = "the update archive has no " + prefix;
            succeeded = false;
        }

        PHYSFS_unmount(archivePath.c_str());
    }

    if (initializedHere)
    {
        PHYSFS_deinit();
    }

    return succeeded;
}

void finishHealthyStart(AppInstallation &installation, const std::string &version, std::ostream &log)
{
    if (installation.isHealthy(version))
    {
        return;
    }

    if (!installation.markHealthy(version))
    {
        log << "Update: cannot mark " << version << " healthy\n";
        return;
    }

    log << "Update: OpenYAMM " << version << " started successfully\n";

    // A version started directly from its folder while another is current cleans up nothing.
    if (installation.currentVersion() != version)
    {
        return;
    }

    installation.forgetPreviousVersion();
    std::error_code error;

    for (const std::string &other : installation.otherVersions())
    {
        std::filesystem::remove_all(installation.appDirectory(other), error);
        log << "Update: removed version " << other << '\n';
    }

    std::string indexError;
    const std::optional<AssetPackIndex> index =
        loadAssetPackIndex(installation.appDirectory(version) / AssetPackIndexFileName, indexError);

    if (index)
    {
        std::unordered_set<std::string> referenced;

        for (const AssetPackRecord &pack : index->packs)
        {
            referenced.insert(pack.file);
        }

        size_t removed = 0;

        for (const std::filesystem::directory_entry &entry :
             std::filesystem::directory_iterator(installation.packStore(), error))
        {
            const std::string name = entry.path().filename().string();

            if (entry.is_regular_file(error) && entry.path().extension() == ".zip" && !referenced.contains(name))
            {
                removed += std::filesystem::remove(entry.path(), error) ? 1 : 0;
            }
        }

        if (removed > 0)
        {
            log << "Update: removed " << removed << " content packs no version uses\n";
        }
    }

    const std::filesystem::path launcher = installation.appDirectory(version) / LauncherCopyName;

    if (std::filesystem::is_regular_file(launcher, error) && !sameFileContent(launcher, installation.launcherPath()))
    {
        // The launcher exits as soon as it started the game, so it can be replaced now.
        std::filesystem::path replacement = installation.launcherPath();
        replacement += ".new";
        std::filesystem::copy_file(launcher, replacement, std::filesystem::copy_options::overwrite_existing, error);

        if (!error)
        {
            makeExecutable(replacement);
            std::filesystem::rename(replacement, installation.launcherPath(), error);
        }

        log << (error ? "Update: cannot replace the launcher: " + error.message() : "Update: launcher updated")
            << '\n';
    }

    removeLegacyRelease(installation, log);
}
}
