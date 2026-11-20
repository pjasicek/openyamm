#include "game/app/GameUpdater.h"
#include "engine/Localization.h"

#if defined(__APPLE__)
#include "game/app/AppleBundlePaths.h"
#endif

#include <SDL3/SDL_filesystem.h>
#include <SDL3/SDL_process.h>
#include <SDL3/SDL_system.h>
#include <SDL3/SDL_timer.h>

#include <algorithm>
#include <filesystem>

#if defined(__ANDROID__)
#include <jni.h>

#include <sstream>
#include <vector>
#endif

namespace OpenYAMM::Game
{
namespace
{
constexpr std::string_view KeptPacksMessage = Engine::trNoop(
    "Updates are off while settings.ini has keep_modified_packs=on: an update would replace the content packs you "
    "changed.");

// The updater of a versioned installation: this executable runs from app/<version>/.
class InstallationUpdater final : public GameUpdater
{
public:
    InstallationUpdater(Engine::AppInstallation installation, std::string version, const std::string &baseUrl,
                        std::unique_ptr<Engine::HttpTransport> transport, bool keepModifiedPacks)
        : m_installation(installation)
        , m_version(version)
        , m_updater(installation, version, Engine::releasePlatformName(), baseUrl, std::move(transport))
        , m_keepModifiedPacks(keepModifiedPacks)
    {
    }

    // The languages whose optional packs stay installed and current: any with a pack in the store, and the chosen one.
    void keepLanguages(const std::string &chosenLanguage)
    {
        std::vector<std::string> languages;
        std::string error;
        const std::optional<Engine::AssetPackIndex> index = Engine::loadAssetPackIndex(
            m_installation.appDirectory(m_version) / Engine::AssetPackIndexFileName, error);

        for (const Engine::AssetPackRecord &pack : index ? index->packs : std::vector<Engine::AssetPackRecord>())
        {
            std::error_code fileError;

            if (!pack.language.empty() && std::find(languages.begin(), languages.end(), pack.language) == languages.end()
                && std::filesystem::is_regular_file(m_installation.packStore() / pack.file, fileError))
            {
                languages.push_back(pack.language);
            }
        }

        if (!chosenLanguage.empty() && chosenLanguage != "en"
            && std::find(languages.begin(), languages.end(), chosenLanguage) == languages.end())
        {
            languages.push_back(chosenLanguage);
        }

        m_updater.setLanguages(std::move(languages));
    }

    std::string installedVersion() const override
    {
        return m_version;
    }

    void check() override
    {
        if (m_keepModifiedPacks)
        {
            m_checkRefused = true;
            return;
        }

        m_updater.check();
    }

    Engine::UpdateStatus status() const override
    {
        if (m_checkRefused)
        {
            Engine::UpdateStatus status;
            status.state = Engine::UpdateState::Failed;
            // The main menu shows it.
            status.message = Engine::tr(KeptPacksMessage);
            return status;
        }

        return m_updater.status();
    }

    void startUpdate() override
    {
        // Only a check offers an update, and with kept packs none ran.
        if (!m_keepModifiedPacks)
        {
            m_updater.download();
        }
    }

    bool updatesInGame() const override
    {
        return true;
    }

    void cancel() override
    {
        m_updater.cancel();
    }

    bool restartIntoUpdate(std::string &error) override
    {
        if (!activate(error))
        {
            return false;
        }

        // The launcher starts the new version and counts its start for the rollback rule.
        const std::u8string launcherPath = m_installation.launcherPath().u8string();
        const std::string launcher(launcherPath.begin(), launcherPath.end());
        const char *arguments[] = {launcher.c_str(), nullptr};
        // No inherited standard handles: a Windows GUI program usually has none, and duplicating them fails.
        const SDL_PropertiesID properties = SDL_CreateProperties();
        SDL_SetPointerProperty(properties, SDL_PROP_PROCESS_CREATE_ARGS_POINTER, arguments);
        SDL_SetNumberProperty(properties, SDL_PROP_PROCESS_CREATE_STDIN_NUMBER, SDL_PROCESS_STDIO_NULL);
        SDL_SetNumberProperty(properties, SDL_PROP_PROCESS_CREATE_STDOUT_NUMBER, SDL_PROCESS_STDIO_NULL);
        SDL_SetNumberProperty(properties, SDL_PROP_PROCESS_CREATE_STDERR_NUMBER, SDL_PROCESS_STDIO_NULL);
        SDL_SetBooleanProperty(properties, SDL_PROP_PROCESS_CREATE_BACKGROUND_BOOLEAN, true);
        SDL_Process *pProcess = SDL_CreateProcessWithProperties(properties);
        SDL_DestroyProperties(properties);

        if (pProcess == nullptr)
        {
            error = std::string("cannot start ") + launcher + ": " + SDL_GetError();
            return false;
        }

        SDL_DestroyProcess(pProcess);
        return true;
    }

    bool activate(std::string &error)
    {
        return m_updater.activate(error);
    }

    void wait()
    {
        m_updater.wait();
    }

    void markHealthy(std::ostream &log) override
    {
        Engine::finishHealthyStart(m_installation, m_version, log);
    }

    std::optional<std::string> takeRollbackNotice() override
    {
        return m_installation.takeRollbackNotice();
    }

private:
    Engine::AppInstallation m_installation;
    std::string m_version;
    Engine::AppUpdater m_updater;
    bool m_keepModifiedPacks = false;
    bool m_checkRefused = false;
};

std::unique_ptr<InstallationUpdater> createInstallationUpdater(const std::string &baseUrl, bool keepModifiedPacks,
                                                               const std::string &languageId = {})
{
    const char *pBasePath = SDL_GetBasePath();

    if (pBasePath == nullptr)
    {
        return nullptr;
    }

    const std::filesystem::path executableDirectory = Engine::programDirectory(pBasePath);
    std::optional<Engine::AppInstallation> installation = Engine::AppInstallation::containing(executableDirectory);
    std::string version = executableDirectory.filename().string();
#if defined(__APPLE__)
    // The downloaded app installs its release into the per-user installation.
    if (!installation)
    {
        installation = applePackageInstallation();
        version = applePackageVersion();
    }
#endif
    std::unique_ptr<Engine::HttpTransport> transport = Engine::createPlatformHttpTransport();

    if (!installation || !transport)
    {
        return nullptr;
    }

    std::unique_ptr<InstallationUpdater> updater = std::make_unique<InstallationUpdater>(
        *installation, version, baseUrl, std::move(transport), keepModifiedPacks);
    updater->keepLanguages(languageId);
    return updater;
}

#if defined(__ANDROID__)
// The Android updater lives in Java (OpenYammActivity's updater* methods and OpenYammUpdateActivity): the APK and
// its content packs are installed outside the running game.
class AndroidUpdater final : public GameUpdater
{
public:
    explicit AndroidUpdater(std::string baseUrl)
        : m_baseUrl(std::move(baseUrl))
    {
    }

    std::string installedVersion() const override
    {
        return callString("updaterInstalledVersion", "()Ljava/lang/String;");
    }

    void check() override
    {
        callWithUrl("updaterStartCheck");
    }

    Engine::UpdateStatus status() const override
    {
        // "state|release|bytes|message", see OpenYammActivity.updaterCheckResult.
        std::vector<std::string> fields;
        std::stringstream stream(callString("updaterCheckResult", "()Ljava/lang/String;"));
        std::string field;

        while (std::getline(stream, field, '|'))
        {
            fields.push_back(field);
        }

        fields.resize(4);
        Engine::UpdateStatus status;
        status.release = fields[1];
        status.totalBytes = fields[2].empty() ? 0 : std::stoull(fields[2]);
        status.message = fields[3];
        // An available update's last field is its release notes.
        status.notes = fields[0] == "available" ? fields[3] : std::string();
        status.state = fields[0] == "checking"    ? Engine::UpdateState::Checking
            : fields[0] == "available"            ? Engine::UpdateState::Available
            : fields[0] == "uptodate"             ? Engine::UpdateState::UpToDate
            : fields[0] == "failed"               ? Engine::UpdateState::Failed
                                                  : Engine::UpdateState::Idle;
        return status;
    }

    void startUpdate() override
    {
        callWithUrl("updaterOpen");
    }

    bool updatesInGame() const override
    {
        return false;
    }

    void cancel() override
    {
    }

    bool restartIntoUpdate(std::string &error) override
    {
        error = "Android installs updates in its update screen";
        return false;
    }

    void markHealthy(std::ostream &) override
    {
    }

    std::optional<std::string> takeRollbackNotice() override
    {
        return std::nullopt;
    }

private:
    template <typename Call>
    static void withActivity(const char *pName, const char *pSignature, Call call)
    {
        JNIEnv *pEnvironment = static_cast<JNIEnv *>(SDL_GetAndroidJNIEnv());
        jobject activity = static_cast<jobject>(SDL_GetAndroidActivity());

        if (pEnvironment == nullptr || activity == nullptr)
        {
            return;
        }

        jclass activityClass = pEnvironment->GetObjectClass(activity);
        jmethodID method = pEnvironment->GetStaticMethodID(activityClass, pName, pSignature);

        if (method != nullptr)
        {
            call(pEnvironment, activityClass, method);
        }

        if (pEnvironment->ExceptionCheck())
        {
            pEnvironment->ExceptionClear();
        }

        pEnvironment->DeleteLocalRef(activityClass);
        pEnvironment->DeleteLocalRef(activity);
    }

    static std::string callString(const char *pName, const char *pSignature)
    {
        std::string result;
        withActivity(pName, pSignature,
                     [&result](JNIEnv *pEnvironment, jclass activityClass, jmethodID method)
                     {
                         jstring value = static_cast<jstring>(pEnvironment->CallStaticObjectMethod(activityClass, method));

                         if (value != nullptr)
                         {
                             const char *pChars = pEnvironment->GetStringUTFChars(value, nullptr);
                             result = pChars != nullptr ? pChars : "";
                             pEnvironment->ReleaseStringUTFChars(value, pChars);
                             pEnvironment->DeleteLocalRef(value);
                         }
                     });
        return result;
    }

    void callWithUrl(const char *pName) const
    {
        withActivity(pName, "(Ljava/lang/String;)V",
                     [this](JNIEnv *pEnvironment, jclass activityClass, jmethodID method)
                     {
                         jstring url = pEnvironment->NewStringUTF(m_baseUrl.c_str());
                         pEnvironment->CallStaticVoidMethod(activityClass, method, url);
                         pEnvironment->DeleteLocalRef(url);
                     });
    }

    std::string m_baseUrl;
};
#endif
}

std::unique_ptr<GameUpdater> GameUpdater::create(const std::string &baseUrl, bool keepModifiedPacks,
                                                 const std::string &languageId)
{
#if defined(__ANDROID__)
    // Development APKs bundle their content and take no updates; an APK installs its packs itself.
    (void)keepModifiedPacks;
    (void)languageId;
    std::unique_ptr<GameUpdater> updater = std::make_unique<AndroidUpdater>(baseUrl);
    return updater->installedVersion().empty() ? nullptr : std::move(updater);
#else
    return createInstallationUpdater(baseUrl, keepModifiedPacks, languageId);
#endif
}

int runHeadlessUpdate(const std::string &baseUrl, bool keepModifiedPacks, std::ostream &log)
{
    std::unique_ptr<InstallationUpdater> updater = createInstallationUpdater(baseUrl, keepModifiedPacks);

    if (!updater)
    {
        log << "Update: this installation does not update itself\n";
        return 2;
    }

    if (keepModifiedPacks)
    {
        log << "Update: " << KeptPacksMessage << '\n';
        return 2;
    }

    log << "Update: OpenYAMM " << updater->installedVersion() << ", checking " << baseUrl << '\n';
    updater->check();
    updater->wait();
    Engine::UpdateStatus status = updater->status();
    log << "Update: " << status.message << '\n';

    if (status.state == Engine::UpdateState::UpToDate)
    {
        return 0;
    }

    if (status.state != Engine::UpdateState::Available)
    {
        return 1;
    }

    log << "Update: downloading " << status.packCount << " content packs" << (status.contentOnly ? "" : " and the app")
        << ", " << status.totalBytes << " bytes\n";
    updater->startUpdate();
    updater->wait();
    status = updater->status();
    log << "Update: " << status.message << " (" << status.doneBytes << " of " << status.totalBytes << " bytes)\n";
    std::string error;

    if (status.state != Engine::UpdateState::Ready || !updater->activate(error))
    {
        log << "Update: failed " << error << '\n';
        return 1;
    }

    log << (status.contentOnly ? "Update: the content of OpenYAMM " + status.release + " is installed\n"
                               : "Update: OpenYAMM " + status.release + " is now current\n");
    return 0;
}
}
