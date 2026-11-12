#include "engine/AssetPackIndex.h"

#include <doctest/doctest.h>

#include <string>

namespace
{
std::string indexWithPack(const std::string &pack)
{
    return "{\"schema\": 1, \"release\": \"0.8\", \"build\": \"0.8\", \"profile\": \"desktop\", \"content_format\": 1, "
           "\"store\": \"packs\", \"packs\": [" + pack + "]}";
}

std::string pack(const std::string &id, const std::string &package, const std::string &mount, const std::string &file)
{
    return "{\"id\": \"" + id + "\", \"package\": \"" + package + "\", \"mount\": \"" + mount + "\", \"file\": \""
        + file + "\", \"size\": 12, \"content_id\": \"aa\", \"sha256\": \"bb\"}";
}
}

TEST_CASE("pack indexes parse and keep every pack inside its package")
{
    std::string error;
    const std::optional<OpenYAMM::Engine::AssetPackIndex> index = OpenYAMM::Engine::parseAssetPackIndex(
        indexWithPack(pack("engine.core", "engine", "/engine", "engine.core-1.zip") + ", "
                      + pack("mm6.maps.lighting.0", "mm6", "/worlds/mm6/maps", "mm6.maps.lighting.0-2.zip")),
        error);
    REQUIRE_MESSAGE(index, error);
    CHECK(index->release == "0.8");
    CHECK(index->contentFormat == 1);
    CHECK(index->store == "packs");
    REQUIRE(index->packs.size() == 2);
    CHECK(index->packs[1].mount == "/worlds/mm6/maps");
    CHECK(index->packs[1].size == 12);

    for (const std::string &invalid : {
             pack("x", "mm6", "/worlds/mm7/maps", "x.zip"),
             pack("x", "engine", "/engine/../worlds", "x.zip"),
             pack("x", "engine", "/enginex", "x.zip"),
             pack("x", "engine", "/engine", "../x.zip"),
             pack("x", "engine", "/engine", "x.tar"),
             pack("x", "engine", "/engine", "x.zip") + ", " + pack("x", "engine", "/engine/ui", "y.zip"),
             pack("x", "engine", "/engine", "x.zip") + ", " + pack("y", "engine", "/engine/ui", "x.zip")})
    {
        CAPTURE(invalid);
        CHECK_FALSE(OpenYAMM::Engine::parseAssetPackIndex(indexWithPack(invalid), error));
    }

    CHECK_FALSE(OpenYAMM::Engine::parseAssetPackIndex("{\"schema\": 2}", error));
    CHECK_FALSE(OpenYAMM::Engine::parseAssetPackIndex("not json", error));
    CHECK_FALSE(OpenYAMM::Engine::parseAssetPackIndex(indexWithPack(""), error));
}

TEST_CASE("a release index's language packs, listed apart for older updaters, join the packs with their language")
{
    const std::string german = "{\"id\": \"lang-de.engine.audio\", \"package\": \"engine\", "
                               "\"mount\": \"/engine/audio\", \"file\": \"lang-de.engine.audio-1.zip\", "
                               "\"size\": 12, \"content_id\": \"aa\", \"sha256\": \"bb\", \"language\": \"de\"}";
    const std::string base = indexWithPack(pack("engine.core", "engine", "/engine", "engine.core-1.zip"));
    const std::string apart = base.substr(0, base.size() - 1) + ", \"language_packs\": [" + german + "]}";
    std::string error;
    const std::optional<OpenYAMM::Engine::AssetPackIndex> index = OpenYAMM::Engine::parseAssetPackIndex(apart, error);
    REQUIRE_MESSAGE(index, error);
    REQUIRE(index->packs.size() == 2);
    CHECK(index->packs[0].language.empty());
    CHECK(index->packs[1].id == "lang-de.engine.audio");
    CHECK(index->packs[1].language == "de");

    // A pack listed apart must name its language, and language_packs must be a list.
    const std::string nameless = base.substr(0, base.size() - 1) + ", \"language_packs\": ["
        + pack("lang-de.engine.ui", "engine", "/engine/ui", "lang-de.engine.ui-1.zip") + "]}";
    CHECK_FALSE(OpenYAMM::Engine::parseAssetPackIndex(nameless, error));
    CHECK_FALSE(OpenYAMM::Engine::parseAssetPackIndex(base.substr(0, base.size() - 1) + ", \"language_packs\": 3}",
                                                      error));
}
