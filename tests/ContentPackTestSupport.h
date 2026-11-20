#pragma once

#include <filesystem>
#include <fstream>
#include <string>
#include <vector>

// Writes assets/index.json for one core pack per package; the test writes assets/packs/<package>.core.zip itself.
inline void writeCorePackIndex(const std::filesystem::path &assetRoot, const std::vector<std::string> &packages)
{
    std::string index = "{\"schema\": 1, \"release\": \"test\", \"build\": \"test\", \"profile\": \"desktop\", "
                        "\"content_format\": 1, \"store\": \"packs\", \"packs\": [";

    for (size_t packageIndex = 0; packageIndex < packages.size(); ++packageIndex)
    {
        const std::string &package = packages[packageIndex];
        const std::string file = package + ".core.zip";
        const std::string mount = package == "engine" ? "/engine" : "/worlds/" + package;
        index += std::string(packageIndex == 0 ? "" : ", ") + "{\"id\": \"" + package + ".core\", \"package\": \""
            + package + "\", \"mount\": \"" + mount + "\", \"file\": \"" + file + "\", \"size\": "
            + std::to_string(std::filesystem::file_size(assetRoot / "packs" / file))
            + ", \"content_id\": \"c\", \"sha256\": \"s\"}";
    }

    std::ofstream(assetRoot / "index.json", std::ios::binary) << index << "]}";
}
