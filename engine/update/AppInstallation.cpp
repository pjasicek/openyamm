#include "engine/update/AppInstallation.h"

#include <algorithm>
#include <fstream>
#include <sstream>
#include <system_error>

namespace OpenYAMM::Engine
{
namespace
{
constexpr const char *CurrentFileName = "current";
constexpr const char *PreviousFileName = "previous";
constexpr const char *StartsFileName = "starts";
constexpr const char *HealthyFileName = "healthy";
constexpr const char *RollbackFileName = "rolled-back";
// A version that never reached its main menu is given up after this many starts.
constexpr int MaximumUnhealthyStarts = 2;

std::string trimmed(const std::string &text)
{
    const size_t begin = text.find_first_not_of(" \t\r\n");

    if (begin == std::string::npos)
    {
        return {};
    }

    return text.substr(begin, text.find_last_not_of(" \t\r\n") - begin + 1);
}

std::optional<std::string> readVersionFile(const std::filesystem::path &path)
{
    const std::optional<std::string> text = readSmallTextFile(path);

    if (!text)
    {
        return std::nullopt;
    }

    const std::string version = trimmed(*text);
    return isValidAppVersionName(version) ? std::optional<std::string>(version) : std::nullopt;
}
}

AppInstallation::AppInstallation(std::filesystem::path root)
    : m_root(std::move(root))
{
}

std::optional<AppInstallation> AppInstallation::containing(const std::filesystem::path &executableDirectory)
{
    const std::filesystem::path directory = executableDirectory.lexically_normal();
    const std::filesystem::path folder = directory.has_filename() ? directory : directory.parent_path();

    if (folder.parent_path().filename() != "app" || !isValidAppVersionName(folder.filename().string()))
    {
        return std::nullopt;
    }

    std::error_code error;

    if (!std::filesystem::is_regular_file(folder.parent_path() / CurrentFileName, error))
    {
        return std::nullopt;
    }

    return AppInstallation(folder.parent_path().parent_path());
}

const std::filesystem::path &AppInstallation::root() const
{
    return m_root;
}

std::filesystem::path AppInstallation::appDirectory(const std::string &version) const
{
    return m_root / "app" / version;
}

std::filesystem::path AppInstallation::gameExecutable(const std::string &version) const
{
    return appDirectory(version) / GameExecutableName;
}

std::filesystem::path AppInstallation::packStore() const
{
    return m_root / "assets" / "packs";
}

std::filesystem::path AppInstallation::updateDirectory() const
{
    return m_root / "update";
}

std::filesystem::path AppInstallation::launcherPath() const
{
    return m_root / LauncherExecutableName;
}

std::optional<std::string> AppInstallation::currentVersion() const
{
    return readVersionFile(m_root / "app" / CurrentFileName);
}

std::optional<std::string> AppInstallation::previousVersion() const
{
    return readVersionFile(m_root / "app" / PreviousFileName);
}

bool AppInstallation::isHealthy(const std::string &version) const
{
    std::error_code error;
    return std::filesystem::is_regular_file(appDirectory(version) / HealthyFileName, error);
}

std::optional<std::string> AppInstallation::chooseVersionToStart(std::string &rolledBackFrom)
{
    rolledBackFrom.clear();
    const std::optional<std::string> current = currentVersion();

    if (!current || isHealthy(*current))
    {
        return current;
    }

    const std::filesystem::path startsPath = appDirectory(*current) / StartsFileName;
    int starts = 0;

    if (const std::optional<std::string> text = readSmallTextFile(startsPath))
    {
        std::istringstream(*text) >> starts;
    }

    const std::optional<std::string> previous = previousVersion();
    std::error_code error;

    if (starts >= MaximumUnhealthyStarts && previous && *previous != *current
        && std::filesystem::is_directory(appDirectory(*previous), error)
        && writeTextFileAtomically(m_root / "app" / CurrentFileName, *previous + "\n"))
    {
        std::filesystem::remove(m_root / "app" / PreviousFileName, error);
        writeTextFileAtomically(m_root / "app" / RollbackFileName, *current + "\n");
        rolledBackFrom = *current;
        return previous;
    }

    writeTextFileAtomically(startsPath, std::to_string(starts + 1) + "\n");
    return current;
}

bool AppInstallation::switchTo(const std::string &version, std::string &error)
{
    std::error_code fileError;

    if (!isValidAppVersionName(version) || !std::filesystem::is_directory(appDirectory(version), fileError))
    {
        error = "version " + version + " is not staged";
        return false;
    }

    std::filesystem::remove(appDirectory(version) / StartsFileName, fileError);
    std::filesystem::remove(appDirectory(version) / HealthyFileName, fileError);
    const std::optional<std::string> current = currentVersion();

    if (current && *current != version && !writeTextFileAtomically(m_root / "app" / PreviousFileName, *current + "\n"))
    {
        error = "cannot record the previous version";
        return false;
    }

    if (!writeTextFileAtomically(m_root / "app" / CurrentFileName, version + "\n"))
    {
        error = "cannot switch to version " + version;
        return false;
    }

    return true;
}

bool AppInstallation::markHealthy(const std::string &version)
{
    if (isHealthy(version))
    {
        return true;
    }

    std::error_code error;
    std::filesystem::remove(appDirectory(version) / StartsFileName, error);
    return writeTextFileAtomically(appDirectory(version) / HealthyFileName, "");
}

void AppInstallation::forgetPreviousVersion()
{
    std::error_code error;
    std::filesystem::remove(m_root / "app" / PreviousFileName, error);
}

std::optional<std::string> AppInstallation::takeRollbackNotice()
{
    const std::filesystem::path path = m_root / "app" / RollbackFileName;
    const std::optional<std::string> version = readVersionFile(path);
    std::error_code error;
    std::filesystem::remove(path, error);
    return version;
}

std::vector<std::string> AppInstallation::otherVersions() const
{
    std::vector<std::string> versions;
    const std::optional<std::string> current = currentVersion();
    std::error_code error;

    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(m_root / "app", error))
    {
        const std::string name = entry.path().filename().string();

        if (entry.is_directory(error) && isValidAppVersionName(name) && name != current)
        {
            versions.push_back(name);
        }
    }

    std::sort(versions.begin(), versions.end());
    return versions;
}

std::filesystem::path programDirectory(const std::filesystem::path &basePath)
{
    std::filesystem::path directory = basePath.lexically_normal();

    if (!directory.has_filename())
    {
        directory = directory.parent_path();
    }

    const std::filesystem::path contents = directory.parent_path();
    const std::filesystem::path bundle = contents.parent_path();

    if (directory.filename() == "Resources" && contents.filename() == "Contents" && bundle.extension() == ".app")
    {
        return bundle.parent_path();
    }

    return directory;
}

bool isValidAppVersionName(const std::string &version)
{
    if (version.empty() || version.size() > 32 || version.front() == '.' || version == "..")
    {
        return false;
    }

    return std::all_of(version.begin(), version.end(),
                       [](char character)
                       {
                           return (character >= '0' && character <= '9') || (character >= 'a' && character <= 'z')
                               || (character >= 'A' && character <= 'Z') || character == '.' || character == '-';
                       });
}

std::optional<std::string> readSmallTextFile(const std::filesystem::path &path)
{
    std::ifstream input(path, std::ios::binary);

    if (!input)
    {
        return std::nullopt;
    }

    std::string text(4096, '\0');
    input.read(text.data(), std::streamsize(text.size()));
    text.resize(size_t(input.gcount()));
    return text;
}

bool writeTextFileAtomically(const std::filesystem::path &path, const std::string &text)
{
    std::filesystem::path temporary = path;
    temporary += ".tmp";

    {
        std::ofstream output(temporary, std::ios::binary | std::ios::trunc);
        output << text;

        if (!output.flush())
        {
            return false;
        }
    }

    std::error_code error;
    std::filesystem::rename(temporary, path, error);

    if (error)
    {
        std::filesystem::remove(temporary, error);
        return false;
    }

    return true;
}
}
