#pragma once

#include <doctest/doctest.h>

#include <filesystem>

namespace OpenYAMM::Tests
{
// MM9's imported content is an optional, untracked package. A present but incomplete package must still fail.
inline doctest::skip requiresMm9Assets()
{
    return doctest::skip(!std::filesystem::is_directory(
        std::filesystem::path(OPENYAMM_SOURCE_DIR) / "assets_dev/worlds/mm9"));
}

inline bool hasExactFileName(const std::filesystem::path &path)
{
    for (const std::filesystem::directory_entry &entry : std::filesystem::directory_iterator(path.parent_path()))
    {
        if (entry.path().filename() == path.filename())
        {
            return true;
        }
    }
    return false;
}

inline bool hasAssetFilePermissions(const std::filesystem::path &path)
{
    const std::filesystem::perms permissions = std::filesystem::status(path).permissions();
#if defined(_WIN32)
    // Windows exposes the read-only attribute, not POSIX group/other write bits.
    const std::filesystem::perms required = std::filesystem::perms::owner_read | std::filesystem::perms::owner_write;
    return (permissions & required) == required;
#else
    return (permissions & std::filesystem::perms::all) == (std::filesystem::perms::owner_read
        | std::filesystem::perms::owner_write | std::filesystem::perms::group_read | std::filesystem::perms::others_read);
#endif
}
}
