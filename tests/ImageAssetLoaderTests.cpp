#include "engine/ImageAssetLoader.h"

#include <doctest/doctest.h>

#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <optional>
#include <vector>

namespace
{
std::vector<uint8_t> readBinaryFile(const std::filesystem::path &path)
{
    std::ifstream file(path, std::ios::binary);

    if (!file)
    {
        return {};
    }

    return std::vector<uint8_t>(std::istreambuf_iterator<char>(file), std::istreambuf_iterator<char>());
}
}

TEST_CASE("ImageAssetLoader decodes PNG pixels through shared loader")
{
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    const std::filesystem::path pngPath =
        sourceRoot / "editor" / "assets" / "editor_ux_work" / "mockups" / "Level editor UI redesign mockup.png";
    const std::vector<uint8_t> bytes = readBinaryFile(pngPath);

    REQUIRE_FALSE(bytes.empty());

    const std::optional<OpenYAMM::Engine::ImagePixelsBgra> image =
        OpenYAMM::Engine::decodeImagePixelsBgra(bytes, pngPath.generic_string());

    REQUIRE(image.has_value());
    CHECK(image->width > 0);
    CHECK(image->height > 0);
    CHECK(image->pixels.size() == static_cast<size_t>(image->width) * static_cast<size_t>(image->height) * 4);
}
