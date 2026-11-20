#include "engine/UserDataPaths.h"

#include "engine/update/AppInstallation.h"

#include <system_error>
#include <vector>

namespace OpenYAMM::Engine
{
namespace
{
constexpr const char *SavesDirectoryName = "saves";

bool isRegularFile(const std::filesystem::path &path)
{
    std::error_code error;
    return std::filesystem::is_regular_file(path, error);
}

std::vector<std::filesystem::path> listSaveFiles(const std::filesystem::path &savesDirectory)
{
    std::vector<std::filesystem::path> saveFiles;
    std::error_code error;

    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(savesDirectory, error))
    {
        if (entry.is_regular_file(error) && entry.path().extension() == ".oysav")
        {
            saveFiles.push_back(entry.path());
        }
    }

    return saveFiles;
}

bool sameDirectory(const std::filesystem::path &left, const std::filesystem::path &right)
{
    std::error_code error;
    const bool equivalent = std::filesystem::equivalent(left, right, error);
    return !error ? equivalent : left.lexically_normal() == right.lexically_normal();
}
}

std::filesystem::path installationRoot(const std::filesystem::path &executableDirectory)
{
    const std::optional<AppInstallation> installation = AppInstallation::containing(executableDirectory);
    return installation ? installation->root() : executableDirectory;
}

bool isReleaseInstallation(const std::filesystem::path &installRoot)
{
    return isRegularFile(installRoot / "assets" / "index.json") || isRegularFile(installRoot / "app" / "current");
}

std::filesystem::path installedAssetRoot(const std::filesystem::path &executableDirectory)
{
    if (AppInstallation::containing(executableDirectory))
    {
        return executableDirectory;
    }

    return executableDirectory / "assets";
}

std::filesystem::path resolveUserDataRoot(
    const std::optional<std::filesystem::path> &explicitRoot,
    const std::filesystem::path &installRoot,
    const std::filesystem::path &workingDirectory)
{
    std::filesystem::path root = workingDirectory;

    if (explicitRoot)
    {
        root = explicitRoot->is_absolute() ? *explicitRoot : workingDirectory / *explicitRoot;
    }
    else if (isReleaseInstallation(installRoot))
    {
        root = installRoot;
    }

    return root.lexically_normal();
}

SaveImportResult importSaveFiles(const std::filesystem::path &sourceFolder, const std::filesystem::path &savesFolder)
{
    SaveImportResult result;
    std::vector<std::filesystem::path> saveFiles = listSaveFiles(sourceFolder);

    if (saveFiles.empty())
    {
        saveFiles = listSaveFiles(sourceFolder / SavesDirectoryName);
    }

    std::error_code error;
    std::filesystem::create_directories(savesFolder, error);

    for (const std::filesystem::path &saveFile : saveFiles)
    {
        const std::filesystem::path target = savesFolder / saveFile.filename();

        if (sameDirectory(saveFile.parent_path(), savesFolder) || std::filesystem::exists(target, error))
        {
            ++result.skipped;
            continue;
        }

        std::filesystem::copy_file(saveFile, target, std::filesystem::copy_options::skip_existing, error);

        if (error)
        {
            ++result.failed;
        }
        else
        {
            ++result.imported;
        }
    }

    return result;
}

std::string folderUrl(const std::filesystem::path &folder)
{
    const std::string path = std::filesystem::absolute(folder).generic_string();
    return std::string("file://") + (path.starts_with('/') ? "" : "/") + path;
}
}
